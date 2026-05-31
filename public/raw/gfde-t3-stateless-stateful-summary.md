# 🔄 T3.1 · Stateless vs Stateful Agent 架构 — 冲刺版

> 完整版: [gfde-t3-stateless-stateful.html](gfde-t3-stateless-stateful.html). 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: multi-surface (chat REST 10K concurrent + voice WSS 1K + code agent 500), p99 chat <1s / voice <300ms / code <1s, multi-device for chat 单 device for voice+code, 失败可容忍 voice drop call / code 30s loss / chat 0 loss."

**核心 framing**: 不是二选一. "API 表面 stateless, server 内部 hybrid stateful" 是 2026 LLM 平台事实标准.

### Layer 1: 4-tier hybrid cache (default architecture)

```
L1 In-process LRU   1K 热对话    95% hit, ~10us
L2 Redis warm       10K, TTL 1h   4-15% hit, ~1ms
L3 Postgres cold    source truth  1-5% hit, ~10ms
L4 KV cache (vLLM)  GPU 显存      80-85% prefix hit if conv_id hint
```

Client 传 `conversation_id`, server LB round-robin (软 sticky 优化), 任意 node 都能 serve. KV cache 是隐藏 stateful 层 — 同 conv_id 让 vLLM 自动 prefix-share.

### Layer 2: Per-use-case 选 sticky 模式

```
Chat REST    : Stateless API + 4-tier hybrid    (p99 1s, multi-device)
Voice WSS    : Strict stateful single-actor      (TTFT 300ms, drop call OK)
Coding agent : Sticky hybrid + 30s checkpoint    (50MB state, 30s loss OK)
Workflow     : Stateful via Temporal             (workflow_id = state)
Multi-user   : Document-bound + CRDT             (Notion AI / Figma)
```

### Layer 3: Request lifecycle (chat REST hybrid)

```python
POST /chat { conv_id, user_msg }
1. LB → any node (stateless)
2. cache.get(conv_id)  # L1→L2→L3 fallthrough
3. state.append(user_msg)
4. db.write(user_msg)  # write-ahead BEFORE LLM call
5. vllm.generate(messages, conversation_id=conv_id)  # KV cache hint
6. state.append(response)
7. L1 sync + L2/L3 async write
```

**Write-ahead**: user_msg 先 durable, LLM call 后才回写 response. Node crash 时 user_msg 不丢, retry 通过 client_msg_id idempotency.

### Edge cases

- **EC1 Node crash mid-LLM-call**: user_msg 已 write-ahead → durable. Client SDK retry 带 client_msg_id → new node load state, idempotency check → 重执行或返 cached. <1s recovery.
- **EC2 Multi-device 同 conv**: Postgres source of truth, device A 写 → invalidate Redis + WebSocket push device B. 冲突走 last-writer-wins or CRDT.
- **EC3 100-turn 50K token history**: client 只传 conv_id (不传 history), server 从 DB load. 超过 100 turn → summarize 老 turn + sliding window 保最近 20.
- **EC4 Voice node crash 中通话**: drop call (UX 可接受), 用户重拨 = new session. 通话结束 final transcript + summary 写 DB audit.
- **EC5 Latency-sensitive 要 failover**: active-active 复制状态 (Raft / Redis streams), <1s recovery, 3x cost. 仅用于 trader / 法庭 / 关键 voice.

### Production hardening

- **KV cache hit rate**: 无 hint 30-50%, auto prefix 50-70%, conv_id hint + 软 sticky 80-85%. 这是 latency 最大 lever.
- **Idempotency**: client_msg_id → Redis SETNX in-flight + DB unique constraint backup. 同 key 重发 → 返 cached response.
- **State size cap**: 单 session <100MB hard cap, 长对话 summarize, file >10MB 存 reference 不存内容.
- **Chaos test**: weekly random node kill mid-LLM-call → 期望 retry succeed no double-process.

### 🪝 Resume hook

"在 TikTok Global Payment 我建过 3 种 statefulness pattern: voice agent 7 markets 是 strict stateful WSS (in-process actor 持 ASR/LLM/TTS pipeline, p99 TTFT 280ms); BNPL chatbot 是 hybrid stateless API + 4-tier cache (vLLM conv_id hint, prefix reuse 80%, p99 1.2s → 450ms); Indonesia refund 是 stateful via Temporal (workflow_id = state). 教训: 'stateless API' 是 fiction at serious scale — 真正的产品都有隐藏 stateful 层 (LRU/Redis/KV cache), 显式设计这些 layer."

---

## 🔥 5 Follow-ups

**Q1: KV cache 命中率真实增益?**
10 turn × 1K token/turn 对话: naive prefill 100K compute, prefix cache 后只需 10K (10x reduction). 实测: vLLM 0.6 70B model TTFT 800ms → 220ms, throughput 3-4x. Anthropic 官方 prompt caching 90% off cached input, $3 → $0.30 per 1M.

**Q2: 100 turn 50K token, stateless 每次重传浪费吗?**
网络层浪费 (50KB × 100 = 5MB bandwidth/conv). LLM cost: KV cache 隐藏这个 — server 不重 prefill. 优化: client 只传 conv_id, server 从 DB 重建. Cap 100 turn → summarize 老的.

**Q3: Multi-device 同时操作冲突怎么办?**
DB source of truth (Postgres/Spanner), device A 写 → Redis invalidate + WebSocket push 所有订阅 device. Real-time race 默认 last-writer-wins (chat UX 很少真冲突). 严格场景 per-conversation lock 或 CRDT. Notion-style 协作走 document-bound actor + CRDT.

**Q4: Failover 中 voice agent latency-sensitive 又要不丢?**
Active-active replication: 状态 Raft / Redis streams 复制 2-3 node, per-turn delta sync <1KB. Primary 挂 → replica promote <1s. 音频 gap 200-500ms (voice 可接受). 成本: 3x 网络 + 3x 内存 + 复杂协调. 仅 trader / 法庭 / 关键 voice 用.

**Q5: 你见过的最糟 stateless/stateful mismatch?**
真实案例: 团队声称 REST API stateless 但 in-process feature flag cache 每 node 不同 → multi-device 用户路由不同 node 看到不同行为. Fix: flag 移 Redis 共享, API 真 stateless. 教训: 隐式 statefulness 最危险, 显式 declare 或彻底消除.

---

## ❌ 易错点 (10 条红线)

1. "**Stateless = no state anywhere**" — 错. Server cache / KV cache / LRU 都是 state
2. "**Stateful = single-node**" — 错. Active-active replication 可以
3. **Stateless API 强制 sticky session** — 反模式, 牺牲优势没拿到 stateful 收益
4. **Stateful 无 failover plan** — node crash 用户数据丢
5. **不传 conversation_id 给 LLM** — KV cache 命中率 50% → 30% 暴跌
6. **每 turn 重传 50K token** — 网络浪费 + 序列化 CPU
7. **In-memory only state** — 没 checkpoint, crash 全丢
8. **Mix 但无 contract** — SDK 用户不知道哪些 endpoint sticky, 混淆 multi-device 行为
9. **State 无限增长** — 100+ turn → OOM, 必须 summarize / sliding window
10. **LLM call 前不写 DB** — write-ahead 没做, crash 时 user_msg 丢

---

## ✅ 加分项 (12 条)

1. **4-axis 对比** (latency / scale / cost / failover) with 数字
2. **Hybrid pattern + 4-tier cache** as default
3. **KV cache hint via conversation_id** for prefix reuse 80%+
4. **Per-use-case sticky 模式** (chat / voice / code 三种不同)
5. **DB write-ahead user_msg** before LLM call + idempotency key
6. **软 sticky routing** for KV cache locality (不强制但优先)
7. **Anthropic prompt caching** 90% input discount, OpenAI 50%, Google 75%
8. **Active-active replication** for mission-critical
9. **State size cap + summarize** for long conv (>100 turn)
10. **Chaos testing** (weekly node kill / monthly AZ failure / quarterly region)
11. **Quote voice / BNPL / refund** 三个 production case with 数字
12. **2026 pricing math** (Gemini Pro $2/$12, Flash $0.50/$3, Opus $5/$25)

---

## 一句话总结

Stateless vs Stateful **不是二选一**, 而是 **per-surface 选 sticky 模式 + 内部统一 hybrid 4-tier cache + KV cache hint 利用 LLM serving 隐藏 stateful 层 + 设计 failover**. 2026 production LLM 平台都是「API 表面 stateless, server 内部 hybrid stateful」, conv_id 把客户端 hint 串通到 vLLM prefix KV cache. 这是 staff-level 答案.

---

## 🃏 Cheat Sheet (印 1 页随身)

```
Statefulness 三类 + 1 隐藏层:
  Stateless API     LB round-robin, DB truth
  Stateful single   sticky session, checkpoint
  Stateful A-A      replicated, <1s failover 3x cost
  KV cache (hidden) GPU vLLM auto, conv_id hash

4-axis 对比 (production 数字):
  Latency   stateless 200-1200ms / stateful 150-350ms
  Scale     stateless 1M trivial / stateful 100K ok
  Cost wire stateless 10x re-send / stateful 1x delta
  Failover  stateless <1s 0 loss / stateful 5-30s

Per-use-case:
  Chat REST   stateless + hybrid backend
  Voice WSS   strict stateful single
  Coding      sticky hybrid + 30s checkpoint
  Workflow    stateful via Temporal
  Multi-user  document-bound + CRDT

Hybrid 4-tier cache:
  L1 in-proc LRU   1K conv  95% hit
  L2 Redis warm    10K TTL 1h
  L3 Postgres cold source of truth
  L4 KV cache vLLM hash by conv_id

DB write-ahead protocol:
  1. Load state
  2. Append user_msg
  3. WRITE state to DB (before LLM)
  4. Call LLM
  5. Append response
  6. Write state again

Idempotency:
  client_msg_id (UUID per send)
  Server: Redis SETNX → in-flight lock
  DB unique constraint backup
  Same key retry → cached response

KV cache hit rate:
  No hint            30-50%
  Auto prefix        50-70%
  conv_id + sticky   80-85% ⭐

vLLM hint:
  extra_body={"conversation_id": conv_id}
  Anthropic cache_control={"type":"ephemeral"} 90% off
  OpenAI 50% off / Google 75% off

Failover patterns:
  Stateless     write-ahead + idem → 0 loss <1s
  Stateful      30s checkpoint → <30s loss
  Active-active replicate delta → <1s loss 3x cost

State size caps:
  Conv >100 turn → summarize older
  File >10MB → store reference not content
  Per-session memory <100MB hard cap

Observability:
  Cache hit rate by tier (L1/L2/L3/L4-kv)
  Per-conv TTFT, total latency
  Checkpoint lag (stateful)
  Failover event + recovery time
  KV cache hit rate (vLLM /metrics)

2026 pricing for cost math:
  Gemini 3 Flash $0.50/$3 (cache $0.10)
  Gemini 3 Pro   $2/$12   (cache $0.40)
  Haiku 4.5      $1/$5    (cache $0.10)
  Sonnet 4.6     $3/$15   (cache $0.30)
  Opus 4.7       $5/$25   (cache $0.50)
  GPT-5.5        $5/$30   (cache $1)

红线:
  - Stateless API 强制 sticky
  - Stateful 无 failover plan
  - 不传 conv_id 给 LLM
  - 每 turn 重传 50K token (no cache hint)
  - In-memory only state
  - DB write 在 LLM call 之后
  - Idempotency key 缺失
  - State 无 size cap

Resume quotes:
  "Voice agent strict stateful, p99 TTFT 280ms"
  "BNPL chatbot hybrid + KV hint, 80% prefix reuse"
  "Indonesia refund stateful via Temporal"
  "TikTok 3 statefulness pattern 同一平台"
```
