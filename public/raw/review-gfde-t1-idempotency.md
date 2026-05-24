## T1.1 · idempotent tool 接口 — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/gfde-t1-idempotency.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t1-idempotency.html`](questions/gfde-t1-idempotency.html)

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.
> 不含 prose, 全是 compressed structure (tables / code / one-liners).

### 核心心智模型 (1 sentence)

Idempotency = 「runtime 生成 deterministic key (tenant+session+tool+canonical_args hash) → 3-state machine (in_flight/completed/failed) + atomic SETNX → 多 tier TTL (Redis 24h + DB 30d + bank 永久) + cross-vendor wrapper + 持续 reconciliation」. 没这层, destructive tool 必双花.

### 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Idempotency | f(f(x))=f(x), 多次执行 = 单次 side-effect | 任何 write tool |
| Idempotency key | unique 字符串标识 1 次业务意图 | runtime 生成 |
| At-most-once | 最多 1 次, 可能 0 次 | 不允许丢的场景 不可用 |
| At-least-once | 至少 1 次, 可能多 | 网络默认 |
| Exactly-once | 严格不可达 (Two Generals); 用 at-least-once + idem 模拟 | 业务层目标 |
| Dedup window | server 记 key 的 TTL | Stripe 24h, bank 永久 |
| Canonical args | sorted keys + 固定精度 + str norm | hash 前必做 |
| SETNX | Redis atomic 拿锁原语 | in_flight 状态 |
| Fencing token | 单调递增 token, storage 拒 stale | Redlock 不安全场景 |
| In-flight | 上次还在执行 (3-state 中间态) | 防 race |
| TOCTOU | check-then-use 之间有 race window | 用 atomic SETNX 防 |
| Outbox | DB 同事务写 intent + 执行 | atomicity |
| Reconciliation | 我方 log vs 下游 ledger 对账 | 夜间 job |
| Worker heartbeat | in_flight 含 last_heartbeat + worker_id | crash recovery |
| Compensating | reverse_transfer / cancel_transfer | undo path |
| External ref | bank-side 自带的 key 字段 | 即使无 idem header 也能 dedup |

### N 个核心 framework / pattern

**Framework 1: Key Generation Layered**
- When: 每个 tool call 必备
- Algorithm: `key = blake2b-128(tenant + session + tool + canonical(args))`; canonical = sort_keys + Decimal precision + str.strip().lower()
- Trade-off: 包字段多 → 失误率高; 包少 → cross-tenant 撞
- Tools: hashlib.blake2b, json.dumps(sort_keys=True), pydantic strict types

**Framework 2: 3-State Machine**
- When: 所有 idempotent tool wrapper
- Algorithm: `SET key in_flight NX EX ttl` → execute → SET completed OR SET failed (短 TTL retryable, 长 TTL permanent tombstone)
- Trade-off: in_flight wait poll vs 409 immediate
- Tools: Redis SET NX, Redis Pub/Sub for wake, Lua DEL with token check

**Framework 3: Multi-Tier Storage**
- When: 高吞吐 + 跨 session retry
- Algorithm: Redis (24h hot) → Postgres (30d warm) → bank ledger (permanent)
- Trade-off: TTL 长安全但 logical collision risk; TTL 短安全但跨 session miss
- Tools: Redis ElastiCache, Postgres UNIQUE(idem_key), DynamoDB conditional writes

**Framework 4: Failure Policy Matrix**
- When: Redis / DB 挂时
- Algorithm: read tool skip dedup, write idem fall back to DB, destructive fail closed
- Trade-off: availability vs correctness
- Tools: Redis Sentinel, Postgres read replica, OpenTelemetry alert

**Framework 5: Cross-Vendor Wrapper Patterns**
- When: 下游 vendor 不一致
- Algorithm: A pass-through (Stripe) / B wrapper-owned / C check-then-execute / D best-effort + reconciliation
- Trade-off: vendor TTL 短 → wrapper 长 TTL 兜底
- Tools: Stripe Idempotency-Key header, PayPal-Request-Id, MessageDeduplicationId (SQS FIFO)

### 关键决策树 (ASCII)

```
谁生成 idempotency key?
├─ LLM emit key      → ❌ non-deterministic
├─ Client UI         → 用户层 (button click UUID)
├─ Agent runtime ⭐  → hash(tenant+session+tool+args)
└─ Server tool side  → ❌ 生成时已执行
```

```
Vendor 支持 idempotency header?
├─ YES (Stripe / Square / PayPal) → Pattern A: pass-through
└─ NO
    ├─ Vendor 有 query-by-ref API?
    │   ├─ YES (legacy bank with txn lookup) → Pattern C: check-then-execute + lock
    │   └─ NO
    │       ├─ Vendor idempotent at storage? (set-style) → 直接调
    │       └─ NO (legacy SMS) → Pattern D: best-effort + reconciliation
    └─ Vendor 是自家 service? → 改造支持 idem-key
```

```
Redis 挂时 destructive tool 如何?
├─ Fall back DB (warm tier)
│   ├─ DB 也挂 → FAIL CLOSED (refuse)
│   └─ DB OK → execute via DB lookup
└─ Tool safety = read → skip dedup (allow)
```

### Part 2 五个深度问题速查

**Problem 1: Key Generation — 谁生成, hash 啥, 包含什么**
- 核心解法:
```python
def make_key(tenant, session, tool, args):
    canonical = {'tenant':tenant, 'session':session, 'tool':tool,
                 'args': canonicalize(args)}  # sort_keys + Decimal + str norm
    return hashlib.blake2b(
        json.dumps(canonical, sort_keys=True).encode(),
        digest_size=16
    ).hexdigest()
```
- Top 3 gotchas:
  1. Float `100.00 != 100.000` JSON encode 不同 → 强制 Decimal + `f"{v:.6f}"`
  2. dict key 顺序变 → 不同 hash → `sort_keys=True`
  3. 多空格 / 大小写 → `' '.join(v.strip().lower().split())`
- Tools: hashlib.blake2b (16 bytes, 32 hex, 10^-19 prob for 1B keys), pydantic strict types

**Problem 2: State Machine + Race**
- 核心解法:
```python
ok = redis.set(key, 'in_flight', nx=True, ex=86400)  # atomic SETNX
if ok:
    try: result = execute(); redis.set(key, completed_with_result)
    except RetryableErr: redis.set(key, 'failed', ex=300)  # short TTL retry
    except FatalErr: redis.set(key, 'failed_permanent', ex=86400)  # tombstone
else:
    existing = redis.get(key)
    if existing.state == 'completed': return existing.result
    if existing.state == 'in_flight': poll/pubsub_wait/409
```
- Top 3 gotchas:
  1. `if redis.get is None: redis.set` 不 atomic → TOCTOU → 用 SETNX
  2. Worker crash mid-execute → in_flight 滞留 → 加 heartbeat + worker_id
  3. Lua DEL 不 check token → TTL 过期后误删别人的锁
- Tools: Redis SET NX EX, Lua scripts, Redlock library, ZooKeeper (CP > AP), fencing token

**Problem 3: TTL + Storage Tier**
- 核心解法:
```
Redis 24h (hot, <1ms) → Postgres 30d (warm, <50ms) → bank ledger permanent
Cardinality math: 1M users × 50 calls/day = 50M keys/day → 5GB Redis, single cluster OK
Hit rate: ~2% (real retry); alert if > 10% (upstream broken)
```
- Top 3 gotchas:
  1. TTL > 30d → logical collision (用户合法重发同 args)
  2. TTL < 1min → 跨 session retry 失效
  3. Wrapper TTL 24h vs Stripe 24h → 跨 24h dedup 丢 → bank ledger 兜底
- Tools: Redis ElastiCache (managed HA), DragonflyDB/KeyDB (Redis-compatible faster), Postgres UNIQUE, S3 Parquet cold archive

**Problem 4: Failure Modes**
- 核心解法:
```
Tool safety  | Redis down  | DB down
read         | skip dedup  | skip dedup
write idem   | use DB      | local 5m
destructive  | FAIL CLOSED | FAIL CLOSED
```
- Top 3 gotchas:
  1. Network timeout → tool 返 `state='unknown'`, agent 必须 `get_status` 再决定
  2. LLM retry with adjusted args (+$10) → 新 key 新执行 → prompt-level guidance + companion `get_transaction_status` tool
  3. Worker crash → in_flight 滞留 24h → heartbeat + `bank.lookup_by_external_ref` 恢复
- Tools: Redis Sentinel/Cluster, OpenTelemetry trace, Hypothesis property test, Sentry alert

**Problem 5: Cross-Vendor**
- 核心解法:
```
Pattern A (Stripe / Square / PayPal native): idempotency_key header pass-through
Pattern B (no support, wrapper-owned): distributed lock + Redis cache
Pattern C (query API exists): bank.search(external_ref) → if exists return; else create + cache
Pattern D (legacy SMS no API): best-effort + nightly reconciliation alert duplicates
```
- Top 3 gotchas:
  1. Pattern C race: 2 thread 都 search miss → 都 create → 双花 → wrapper lock 串行
  2. Vendor TTL 5min vs wrapper 24h → 24h-1d 之间 wrapper miss → bank external_ref 永久 truth
  3. Voice agent 7 markets 不同 vendor → 统一 wrapper 抽象, agent 不感知差异
- Tools: Stripe / PayPal SDK native idem, AWS SQS FIFO MessageDeduplicationId, Temporal workflow_id auto-idem, Saga compensating, Outbox + Debezium CDC

### Production gotchas (top 15)

1. LLM-generated key — non-deterministic, sampling 变
2. Key 不含 tenant_id — SaaS 跨租户撞 → 安全事故
3. Key 含 timestamp / nonce — 等于没 dedup
4. TTL 太长 (> 30d) — logical collision
5. TTL 太短 (< 1min) — 跨 session retry 漏
6. 无 in_flight 态 — concurrent race 双执行
7. Fail-open Redis down for destructive — 双花风险
8. No reconciliation — wrapper 和下游 ledger 永久不一致
9. Args 不 canonical (Float / case / 空格) — 同意图不同 hash
10. Worker crash 无 heartbeat — in_flight 滞留
11. Idem key 进 URL — log 泄漏 → 攻击者 replay (用 header)
12. 同 key 不同 result (下游 mutate) — 矛盾
13. TOCTOU race — `if redis.get is None: redis.set` 不 atomic
14. Cross-tenant key collision — `tenant_id` 显式入 key 不信任 args
15. Vendor 不 dedup 也不 query — Pattern D 必须 reconcile + business 接受小概率重复

### 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Key 生成 | Voice agent 7 markets | "tenant+session+tool+canonical_args hash. ASR retry boundary 不一致 → hash 不同 → fixed by normalize audio chunk boundary 前 hash" |
| 3-state machine | BNPL chatbot retry | "SET NX in_flight + Pub/Sub wake. 一次 incident: 单 Redis 无 Sentinel → 锁失效 → 改 cluster" |
| Multi-tier TTL | TikTok payment | "Redis 24h + Postgres 30d + bank ledger 永久. 30 天对账作 fallback truth" |
| Cross-vendor | 7 markets pattern matrix | "Indonesia GoPay no native idem → Pattern C lock + search; Brazil Mercado Pago native → Pattern A; Mexico SPEI legacy → Pattern D + nightly reconcile" |
| Failure modes | Voice agent 6 month run | "网络抖动 30% Indonesia 14:00. Layered dedup 后 double-charge 3/month → 0" |
| Compliance audit | Debt collection multi-market | "每次 hit/miss/collision audit log + reconciliation 跟 bank 对账, regulator 可查" |

### 面试现场 quotables (top 8)

> "Idempotency 不是 ML 问题, 是 distributed system 问题. Agent 时代比 traditional system 更需要, 因为 LLM 比 human 更容易触发 retry."

> "Exactly-once 不存在, 工程上是 at-least-once + idempotent consumer. Two Generals 问题在 network 层永远 unsolvable."

> "Runtime 生成 key 而不是 LLM. LLM sampling 不确定, 同 prompt 调 2 次可能不同 key, 同 retry 也可能不同 key — 等于没 dedup."

> "TTL 不只一个值, 是 multi-tier. Redis 24h hot + DB 30d warm + bank ledger 永久 cold. 反向 reconciliation."

> "Fail-closed on destructive tool when Redis down. 宁可不可用, 不可双花. 这是 staff-level 的判断."

> "Args canonical 是隐形大坑. `100.00` vs `100.000` JSON encode 不同 → 同意图不同 hash → 失效. 强制 Decimal + 固定精度."

> "Cross-vendor 必须有 wrapper 抽象. Voice agent 7 markets, 5 个有 native idem, 2 个没有 — wrapper 统一 `transfer(args, idem_key)` 接口, agent 不感知差异."

> "Network timeout 不该 silent retry. Tool 必须返 `state='unknown'`, 让 agent 调 `get_status` 查 — 这是 idempotency 教科书最常被忽略的 corner case."

### 红线 (top 10 anti-patterns)

1. Let LLM generate idempotency_key
2. Key 不含 tenant_id (SaaS 跨租户撞)
3. Key 含 timestamp / nonce (等于没 dedup)
4. TTL 单层 (没多 tier 兜底)
5. Fail-open on Redis down for destructive
6. 同意图 args 不 canonical (Float / case / 空格)
7. 无 reconciliation (wrapper 和 ledger 长期不一致)
8. 无 in_flight 态 (concurrent race)
9. Idem key 进 URL (log 泄漏 + replay)
10. 下游 idem-unaware 时无 wrapper-side 兜底 (裸奔)
