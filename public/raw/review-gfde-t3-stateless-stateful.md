## T3.1 · stateless vs stateful — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/gfde-t3-stateless-stateful.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t3-stateless-stateful.html`](questions/gfde-t3-stateless-stateful.html)

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页 4-axis / 5 Problem / 全部 production 数字. 比 Cheat Sheet 详细 3x, 是面试前一晚的 last-look 版本.

### 🧠 核心心智模型 (1 sentence)

**默认 stateless + client 带 conv_id + Redis hybrid + KV cache hint**, voice / 强延迟才用 stateful WebSocket; "stateless" 是 API 语义而非 backend 实现, 真实生产里 stateful 优化 (KV cache, prefix tree) 是隐藏第 4 层.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Stateless API | Server 不存 session, client 带 conv_id, 每次 rebuild from DB | 默认 95% LLM 场景 |
| Stateful single | Sticky session, in-process state, pod 死则丢部分 | voice 单节点 |
| Stateful Active-Active | Replicated state, < 1s failover, cost 3x | < 500ms 强延迟 + multi-region |
| KV cache | GPU 显存里 attention key/value, 决定 TTFT | vLLM PagedAttention 自动 |
| Prefix cache | Conv 前缀 reuse, 同 conv_id 命中 60-85% | vLLM enable-prefix-caching |
| WebSocket session | 长连接 server 持 ASR/TTS pipeline | voice 强 latency |
| conv_id hint | Request 带 conv_id, vLLM extra_body 提示 prefix lookup | 多轮对话提速 50% |
| Sticky LB | Hash by conv_id 路由到固定 pod (Envoy / Linkerd) | KV cache locality |
| Idempotency key | client_msg_id UUID, DB unique constraint | 重试不双发 |
| Write-ahead | DB write before LLM call (state durable then call) | failover 0 loss |
| Checkpoint lag | Stateful pod backup interval (5-30s 典型) | 决定 failover 数据丢失 |
| TTFT | Time-to-first-token, 用户感知首字延迟 | voice < 300ms, chat < 1s |
| TPOT | Time-per-output-token, 后续 token 平均延迟 | 30-100ms 典型 |
| Hybrid backend | API 层 stateless + Redis L1 + Postgres L3 + vLLM KV L4 | 你的 BNPL chatbot |
| RadixAttention | SGLang 的 prefix tree, multi-turn cache hit 更佳 | 多轮 chatbot |

### 🎯 4 个核心 framework

**Framework 1: 4-Axis 对比 (Latency / Scale / Cost / Failover)**
- When: 面试官问 "stateless vs stateful 怎么选"
- Algorithm: 列 4 维度, 对比 stateless vs stateful single vs AA
- Trade-off: 没有银弹, 不同维度 winner 不同
- Tools: 量化数字 — TTFT, QPS/pod, $/M token, failover RTO

**Framework 2: Hybrid 4-Tier Cache**
- When: production LLM serving any scale
- Algorithm: L1 in-process LRU (1K conv 95% hit) → L2 Redis warm (10K 1h TTL) → L3 Postgres cold → L4 vLLM KV
- Trade-off: 更多层 = 更复杂 invalidation
- Tools: Caffeine / Guava (L1), Redis Cluster (L2), Postgres (L3), vLLM (L4)

**Framework 3: DB Write-Ahead Idempotency Protocol**
- When: 任何 mutation + retry
- Algorithm: load → append user_msg → DB write → LLM call → append response → DB write (双写)
- Trade-off: 2 DB write/req, 但 0 loss on crash
- Tools: Postgres + Redis SETNX (lock), client_msg_id UUID

**Framework 4: KV Cache + Conv_id Hint + Sticky Routing**
- When: 多轮对话 + self-host vLLM
- Algorithm: client 带 conv_id → Envoy sticky hash → vLLM extra_body={"conversation_id": id} → prefix cache 命中
- Trade-off: sticky pod 死 → re-warm 200-500ms (small loss)
- Tools: Envoy hash-based, vLLM 0.6, SGLang RadixAttn

### 🌳 关键决策树 (ASCII)

```
Stateful or Stateless?
  ├─ Latency < 500ms 必需? (voice / gaming)
  │   └─ yes ── Stateful WebSocket single OR AA
  ├─ Multi-region failover < 1s required?
  │   └─ yes ── AA (3x cost)
  ├─ Long-running workflow (hours/days)?
  │   └─ yes ── Stateful via Temporal workflow
  └─ default ── Stateless + hybrid backend (95% 场景) ⭐

KV cache hit rate optimization?
  ├─ No hint, random LB         30-50%
  ├─ Auto prefix cache (vLLM)   50-70%
  ├─ + conv_id hint              70-80%
  └─ + sticky routing            80-85% ⭐
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: 4-axis 深度对比 — Latency / Scale / Cost / Failover**

```
Stateless API:    p99 200-1200ms, infinite scale, wire 10x, < 1s failover 0 loss
Stateful single:  p99 150-350ms, 100K+ pods ok, wire 1x, 5-30s failover lose checkpoint
Stateful AA:      p99 150-350ms, 100K+, wire 1x, < 1s failover 3x cost
```
- 核心: 没有银弹, latency 想要 stateful, scale 想要 stateless, cost 看流量, failover 看 SLA
- Top 3 gotchas: (1) 算 wire cost 时忘 LLM token 等价 (2) failover RTO ≠ RPO (3) AA 复制冲突 last-write-wins 数据丢
- Tools: Locust / k6 latency benchmark, AWS CloudWatch RTO/RPO, Envoy active-active

**Problem 2: Hybrid Pattern — Logically Stateless + 4-Tier Cache**

```python
def serve(req):
    conv_id = req.conv_id
    # L1 in-process LRU
    msgs = local_lru.get(conv_id)
    if not msgs:
        # L2 Redis warm
        msgs = redis.get(f"conv:{conv_id}")
        if not msgs:
            # L3 Postgres cold source of truth
            msgs = pg.fetch_history(conv_id)
            redis.setex(f"conv:{conv_id}", 3600, msgs)
        local_lru.put(conv_id, msgs)
    # L4 vLLM KV cache via hint
    resp = vllm.complete(msgs + [req.user_msg],
                         extra_body={"conversation_id": conv_id})
    # write-ahead pattern
    pg.append(conv_id, req.user_msg)  # before LLM call ideally
    pg.append(conv_id, resp.text)
    return resp
```
- Top 3 gotchas: (1) L1 stale on pod different (2) Redis evict 用 LRU not random (3) DB write 必须 before LLM 不 after
- Tools: Caffeine/Guava, Redis Cluster + DragonFly, Postgres logical replication, vLLM 0.6

**Problem 3: KV Cache Reuse Engineering**

```
KV cache 原理: attention 的 K/V 矩阵 = past token 计算结果, GPU 显存
vLLM PagedAttention: block 16 token 切分, 类似 OS 页表, 多 req 共享 page
命中条件: 完全相同 prefix token 序列 (system prompt + history)
hint 协议: extra_body={"conversation_id": "c123"} → vLLM lookup block table
sticky routing: hash(conv_id) % N → 固定 pod, KV 在该 GPU 显存
失效: KV evict (LRU when full), pod 死 (lost), prompt 改 (cache invalid)
```
- Top 3 gotchas: (1) 不传 conv_id → 0 hit (2) sticky pod 死 → re-warm 200ms (3) prompt 微改 → all cache invalid
- Tools: vLLM `--enable-prefix-caching --max-num-batched-tokens`, SGLang RadixAttn, Envoy hash-based

**Problem 4: Per-Use-Case Decisions**

| Use case | 选 | 关键参数 |
|---|---|---|
| Chat REST (SaaS chatbot) | Stateless + hybrid | TTL 1h Redis, sticky optional |
| Voice WSS (telephony) | Strict stateful single | WebSocket sticky, checkpoint 5s, TTFT < 300ms |
| Coding agent (Cursor) | Sticky hybrid + checkpoint | session 30min, file context in L2 |
| Workflow (Temporal) | Stateful via engine | activity timeout, retry policy |
| Multi-user collab | Document-bound + CRDT | Y.js / Automerge |

- Top 3 gotchas: (1) Voice 用 stateless → TTFT 800ms 客户砸单 (2) Chat 用 stateful → scale 100K+ 难 (3) Coding agent 没 sticky → file context 重读 GB/min
- Tools: Envoy WebSocket, Temporal SDK, Y.js CRDT, vLLM extra_body

**Problem 5: Failover Mechanics**

```
Stateless full flow:
  1. Client retry with same client_msg_id
  2. New pod fetch DB state
  3. Redis SETNX in-flight lock
  4. DB unique constraint backup
  5. Return cached response if duplicate
  → 0 message loss

Stateful single:
  - Checkpoint 5-30s interval (snapshot to S3)
  - Pod die → spare pod load snapshot + replay WAL
  - Lose 5-30s data + 200-500ms TTFT cold start

Active-Active:
  - Replicate delta (operation log) cross-region < 1s
  - Conflict: last-write-wins or vector clock CRDT
  - 3x cost for replicas
```
- Top 3 gotchas: (1) checkpoint 太长 lose data (2) replay WAL slow (3) AA split-brain 时双写
- Tools: AWS S3 for checkpoint, Postgres logical replication, Redis Streams for replay, chaos-monkey

### 🔥 Production gotchas (top 15)

1. **Stateless API 强制 sticky**: 违反 stateless 假设, 单 pod 挂全体 user 受影响
2. **Stateful 无 failover plan**: 死一个 pod 丢一晚 session
3. **不传 conv_id 给 LLM**: KV cache 0 hit, TTFT 翻倍
4. **每 turn 重传 50K token (no cache hint)**: cost 5x, latency 大
5. **In-memory only state (无 DB backup)**: pod 死 = data gone
6. **DB write 在 LLM call 之后**: crash 时 LLM 已 mutate downstream 但 state 没存
7. **Idempotency key 缺失**: retry 双发 SMS / 双扣款
8. **State 无 size cap**: 100MB session blob, GC 拖死
9. **Conv > 100 turn 不 summarize**: token cost 线性涨
10. **Active-Active conflict resolution 没设计**: split-brain 时数据 corrupt
11. **Voice 用 REST polling 不 WebSocket**: TTFT 1.5s, 客户体验糟
12. **Sticky LB 没 hash by conv_id**: pod 平均分配 cache 但 same conv 跨 pod
13. **Checkpoint 30s + RPO 0 矛盾**: 选 SLA 时不算 RPO
14. **Prompt 微改 → cache 全失效**: 没意识到 cache key 是 token 序列
15. **Cross-region replication lag > 5s**: AA 失效但仍 routes traffic

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Stateful WebSocket voice | Voice agent 7 markets | "WSS sticky, TTFT 280ms, single-pod failover 200ms re-warm" |
| Stateless hybrid 4-tier | BNPL chatbot | "Stateless API + Redis 1h + Postgres source + vLLM KV hint, 80% prefix hit" |
| Idempotency + write-ahead | TikTok PayLater | "client_msg_id UUID + Redis SETNX + Postgres unique, 0 double charge in 6M txn" |
| KV cache locality | Voice agent | "Envoy sticky hash(conv_id), vLLM RadixAttn, TTFT 800ms→280ms 65% drop" |
| Active-Active failover | Voice agent multi-region | "ID region down → KL takeover, < 1s failover, 3x replica cost justified by SLA" |
| Workflow as state | Indonesia refund | "Temporal workflow_id durable state, 5-step refund 任意 step crash auto-resume" |
| State size cap | Internal Agent Platform | "Conv > 100 turn → summarize older 用 Haiku, blob < 5MB hard cap" |

### 🎤 面试现场 quotables (top 8)

1. "Default stateless + hybrid backend; voice / 强延迟才考虑 stateful"
2. "Stateless 是 API 语义, 不是 backend 实现; vLLM prefix cache + sticky 是隐藏第 4 层 stateful 优化"
3. "DB write-ahead before LLM call — 否则 crash 时 LLM 已 mutate 但 state 没存"
4. "Idempotency 3 层: Redis SETNX (fast) + DB unique (durable) + vendor key (Stripe)"
5. "conv_id hint + sticky routing → KV cache hit 50% → 80-85%, TTFT 减半"
6. "Voice agent TTFT 280ms 不是 LLM 优化, 是 WSS sticky + KV 持久 + ASR/TTS pipeline 协同"
7. "Active-Active 3x cost, 只有 < 1s failover SLA 才值得"
8. "Conv 100+ turn 不 summarize → token cost 线性涨, blob > 100MB GC 拖死"

### 🚨 红线 (top 10 anti-patterns)

1. Stateless API 强制 sticky (自相矛盾)
2. Stateful 无 failover plan (单点)
3. 不传 conv_id (KV cache 0 hit)
4. 每 turn 重传 50K token without cache hint (cost 5x)
5. In-memory only state (pod die = lost)
6. DB write 在 LLM call 之后 (crash 时 inconsistent)
7. Idempotency key 缺失 (retry 双发)
8. State 无 size cap (100MB blob)
9. Voice 用 REST polling (TTFT 1.5s)
10. AA split-brain 没 conflict resolution

### 📊 KV cache 数学 + 关键数字

```
模型 KV cache size per token:
  Llama 7B  FP16: 0.5 MB/token
  Llama 70B FP16: 5 MB/token
  Llama 7B  FP8:  0.25 MB/token
  Llama 70B FP8:  2.5 MB/token

GPU mem budget (A100 80GB FP8):
  Model weight 70B FP8: 70GB (single GPU 不够, 必须 TP)
  TP=8 H100: each GPU 持 ~9GB weight, 剩 71GB for KV
  KV budget: 71GB / 2.5MB = 28K token concurrent (across all sessions)
  → 100 active sessions × 280 token avg

vLLM prefix cache hit rate (production 实测):
  No hint, random LB:       30-50%
  Auto prefix cache only:   50-70%
  + conv_id hint:            70-80%
  + sticky routing (Envoy hash conv_id): 80-85% ⭐
```

### 🧰 2026 工具栈 quick lookup

| 类别 | 默认 | Alt | 你简历 |
|---|---|---|---|
| Stateless API framework | FastAPI / Express | Go Gin, Rust Axum | FastAPI |
| L1 in-process cache | Caffeine / Guava | LRU dict | Caffeine |
| L2 warm cache | Redis Cluster | DragonFly, KeyDB | Redis |
| L3 cold store | Postgres | DynamoDB, Cassandra | Postgres |
| L4 KV cache (LLM) | vLLM PagedAttn | SGLang RadixAttn, TensorRT-LLM | vLLM + SGLang ✅ |
| Sticky LB | Envoy hash | HAProxy, NGINX consistent hash | Envoy |
| WebSocket | Envoy WS / Socket.io | uWebSockets | Envoy |
| Workflow engine | Temporal | DBOS, Inngest | Temporal ✅ |
| Idempotency | Redis SETNX + DB unique | Vendor Idempotency-Key | Redis + Postgres |
| CRDT | Y.js / Automerge | Loro | — |

### 🎬 45-min 节奏 (T3.1 专属)

```
0-5    Clarify    "voice or chat? p99 latency? failover RTO/RPO?
                  Multi-region? Tenant isolation? Compliance?"
5-10   Mental     "Default stateless + hybrid; voice 例外"; 画 ASCII
10-25  4-axis     Latency/Scale/Cost/Failover 表展开 + 数字
25-35  Hybrid impl  4-tier cache + write-ahead + idempotency code
35-42  Failover    Stateless 0 loss vs Stateful 5-30s vs AA < 1s
42-45  Resume      "Voice agent TTFT 280ms; BNPL 80% prefix hit"
```

### 🔢 关键 production 数字 (你的简历项目)

- Voice agent TTFT: 800ms → 280ms (65% drop via WSS + KV sticky)
- BNPL chatbot prefix cache hit: 80% (conv_id hint + Envoy sticky hash)
- Indonesia refund workflow: 156K processed, Temporal durable state
- TikTok PayLater idempotency: 0 double-charge in 6M transactions
- Voice agent failover: < 1s (AA setup multi-region, 3x cost justified)
- BNPL session blob avg: 12KB (Redis 1h TTL, 95% L1 hit, 5% L2)
- Conv > 100 turn summarize threshold: Haiku $1/$5 召叫 1 次省 90%

### 🧠 mental model anchors

- "Stateless API 是 API 语义, backend hidden 优化 stateful (KV cache)"
- "Default stateless, voice 例外, < 500ms latency 才考虑 sticky stateful"
- "Hybrid 4-tier cache is 95% scenarios"
- "Write-ahead DB before LLM call, idempotency 3 层"
- "conv_id hint + Envoy sticky hash → KV cache 50% → 85%"
- "AA 3x cost, 只有 < 1s failover SLA 才合理"
