# ⚡ T1.1 · Idempotent Tool 设计 — 冲刺版

> 完整版: [gfde-t1-idempotency.html](gfde-t1-idempotency.html). 这页是 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: bank API 不原生支持 idempotency_key, dedup window 24h, worst-case double charge = compliance event, agent runtime owns the key, multi-tenant SaaS."

**3-layer 架构**:

### Layer 1: Idempotency key generation (at agent runtime)

- **Runtime 生成, 不是 LLM**. LLM sampling 非确定, 同 intent 可能给不同 key.
- 组成: `blake2b(tenant_id + session_id + tool_name + canonical(args))`
- `canonical(args)` = sort_keys + Decimal precision + str normalize.
- **必带 tenant_id** — 跨 tenant 碰撞 = SaaS 安全事故.

### Layer 2: 3-state dedup (Redis hot + DB warm)

```
GET idem:{key}
  in_flight    → poll 200ms (or Pub/Sub wait), max 10s, 否则 409 Retry-After
  completed    → 返回 cached result (deterministic replay)
  not_exist    → SETNX with TTL 24h, execute
  failed       → 同 not_exist (允许重试)
  failed_perm  → tombstone, 拒绝重试
```

Pub/Sub 通知 in_flight 完成, 比 dumb-poll 省 latency. DB tier (Postgres / Cloud SQL) 兜底 >24h.

### Layer 3: Cross-vendor wrapper

Bank 不支持 idempotency? 模式:
- **A. Native passthrough** (Stripe-style): pass `Idempotency-Key` header to vendor ⭐ 最稳
- **B. Wrapper full ownership**: 我们 own dedup + 单点责任
- **C. Check-then-execute via query API**: distributed lock → `query_by_external_ref(ref)` → if exists return → else execute
- **D. Best-effort + nightly reconciliation**: 跑对账, 业务 accept 微小 dup rate

### Edge cases (按问到的顺序背)

- **EC1 网络超时**: bank 可能 commit 可能没 → 返回 `state='unknown'`, agent 调 `get_transfer_status(ref)` 确认. 不盲重试.
- **EC2 LLM 调整 args 重试**: 新 args → 新 key → 新 transaction. Prompt 层指令 "Always retry SAME args first". Audit log 标记 "LLM-initiated adjusted retry".
- **EC3 Redis 挂**: destructive tool **fail closed** (拒绝执行). Read tool fail open (跳 dedup OK).
- **EC4 24h 后同 args 合法新 intent**: UI 提供 `force_new=True` flag 显式 bypass.
- **EC5 Worker 中途 crash**: in_flight 带 heartbeat. Stale >30s → re-query vendor by external_ref → 已 commit 标 completed, 否则重执行.

### Production hardening (1 min wrap)

- **Monitor**: dedup hit rate (~2% expected, alert >10% = upstream 异常); in_flight p99 wait; key cardinality
- **Audit log**: every hit 标 reason (retry / dup / collision suspect)
- **Reconciliation**: nightly 对比 our log vs bank ledger
- **Property test**: hypothesis 跑并发, 不变式 `count(distinct execution) <= count(distinct key)`
- **No SPOF**: Redis cluster + DB replica

### 🪝 Resume hook

"我在 TikTok PayLater 7 国 voice agent 跑过这套. 5 个 market 走 Pattern A (vendor 支持), 2 个 legacy (墨西哥 + 印尼) 走 Pattern C 加 distributed lock + transaction lookup. 6 个月后 double-charge incident 从 ~3/月 → 0."

---

## 🔥 5 Follow-ups (面试官会问)

**Q1: Redis 挂了, fail-open 还是 fail-closed?**
按 tool 分类: read = open (跳 dedup); write-idempotent = fall back DB tier; **destructive (transfer/charge/delete) = 永远 closed**. 宁可不执行不要双花.

**Q2: Vendor 自带 idempotency_key 但只 5 分钟 TTL, 你要 24h?**
2 层: Bank 5min handle transient retry; 我们 24h handle cross-session retry (用户关电脑); >24h 走 vendor 永久 ledger + `external_ref` lookup. 三个 window 写进 client doc.

**Q3: Agent 出错后调整 args 重试 (例如 +$10), 新 key, 但原 transaction 可能还在执行?**
这是 LLM 的责任, runtime 抓不到. 防御:
1. Prompt: "On error, retry SAME args first; only adjust after `get_transaction_status` 确认原 didn't execute"
2. 每个 destructive tool 必带 `get_transaction(ref)` companion tool
3. 提供 `cancel_transfer(ref)` 紧急补偿
4. Audit log 标 "LLM adjusted-args retry" 供人工 review

**Q4: 怎么测?**
4 层: Unit (并发 2 call 同 key → 1 execution); Integration (mid-call kill network); Property-based (hypothesis 随机 args 序列, 不变式 distinct_exec ≤ distinct_key); Chaos (Redis kill mid-flight 验 graceful); Production shadow (历史流量关 idem 跑, 数 would-be doubles).

**Q5: 3rd-party API 完全不支持 idempotency?**
走 Pattern B/C/D:
- B Wrapper own dedup (我们单点责任)
- C Distributed lock (Redis Redlock / ZK) + vendor `query_by_external_ref` API
- D Best-effort + nightly reconciliation + manual compensation flow
- 最次也要 reconciliation, 否则 ledger 永远不一致

---

## ❌ 易错点 (10 条红线)

1. 让 **LLM 生成 idempotency_key** — non-deterministic, key 不稳
2. Key 不含 `tenant_id` — 跨租户撞车, 安全事故
3. 没考虑 **in-flight race** (SETNX atomic 是关键)
4. TTL 太长 → logical collision risk; 太短 → 跨 session 重试漏
5. Redis 挂时 destructive tool **fail-open** — 可能双花, 灾难
6. 没 audit log — dedup hit 不可观察
7. Args 不 canonical 化 (e.g., `{a:1, b:2}` vs `{b:2, a:1}`) — hash 不同, dedup 失效
8. 跨 vendor 没 wrapper — vendor 不支持就裸奔
9. 没 reconciliation — 我们 log 与 vendor ledger 最终不一致
10. Tool 内部本身不 idempotent — wrapper 也救不了 (e.g., `SELECT ... FOR UPDATE` 没拿到锁)

---

## ✅ 加分项 (13 条)

1. Agent runtime 生成 key + BLAKE2b-128 hash
2. 3-state state machine (in_flight / completed / failed)
3. SETNX atomic + 短 poll handle race
4. Pub/Sub 通知 in_flight done (vs dumb poll)
5. Stripe-style key passthrough to vendor
6. Multi-tier storage (Redis 24h + DB 30d + ledger permanent)
7. Fail-closed on destructive + fail-open on read
8. Nightly reconciliation job
9. Cardinality math (50M keys/day → Redis cluster 单集群 ok)
10. Audit hit log with reason
11. Cross-vendor decision tree (A/B/C/D)
12. Property-based test (hypothesis 并发不变式)
13. Voice agent 7-market 实战 story + double-charge 数字

---

## 一句话总结

Idempotent tool = **runtime 生成确定性 key + 3 态机协调并发 + 短长 TTL 双 tier + destructive fail-closed + 跨 vendor wrapper + 持续对账**. LLM 比 human 更易触发 retry, idempotency 是最后防线.

---

## 🃏 Cheat Sheet (印 1 页随身)

```
Idempotency key:
  Source: agent runtime (NOT LLM, NOT server)
  Composition: tenant_id + session_id + tool_name + canonical(args)
  Hash: BLAKE2b-128 (16 bytes / 32 hex)
  Canonical: sort_keys + Decimal precision + str normalize

State machine:
  none → in_flight → completed
              ↓
            failed (retryable) → none
              ↓
        failed_permanent (tombstone)

In-flight race:
  redis.set(key, in_flight, nx=True, ex=ttl)  # atomic
  If exists in_flight: poll 200ms or Pub/Sub wait, max 10s, else 409

TTL multi-tier:
  Redis hot:    24h
  DB warm:      30d
  Bank ledger:  permanent
  + nightly reconciliation

Failure policy:
  Tool safety  | Redis down  | DB down
  read         | skip dedup  | skip dedup
  write-idem   | use DB      | local 5m
  destructive  | FAIL CLOSED | FAIL CLOSED

Cross-vendor patterns:
  A. Native idem header (Stripe) → pass-through ⭐
  B. Wrapper full ownership
  C. Check-then-execute via query API + lock
  D. Best-effort + reconciliation (legacy)

Worker crash:
  in_flight entry: worker_id + last_heartbeat
  Stale > 30s → re-query vendor by external_ref
              → committed: mark completed
              → not: re-execute

Cost / cardinality:
  1M users × 50 calls/day = 50M keys
  Redis: 5GB, single cluster ok
  Hit rate: ~2% normal, alert > 10%

Monitor:
  - dedup hit rate
  - in_flight wait p99
  - key cardinality growth
  - reconciliation mismatch count

Test:
  - concurrent same-key invocation property
  - chaos kill Redis mid-flight
  - production shadow with idem disabled

红线:
  - LLM-generated key
  - Fail-open on infra failure for destructive
  - No reconciliation
  - No audit
```
