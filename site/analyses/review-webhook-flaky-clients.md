## Tech #2 · Reliable Webhook — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/webhook-flaky-clients.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`webhook-flaky-clients.html`](questions/webhook-flaky-clients.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"你 platform 给客户发 webhook, 客户 endpoint flaky (timeout / 5xx / slow), 你怎么保证 eventual delivery 且不 hammer 客户?"** 我按这 8 层回答, 不跳序.

### 📐 Reliable Webhook — 8 层 delivery + protection

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 |
|---|---|---|---|---|
| 1 | At-least-once 哲学声明 | 30s | 不 promise exactly-once (lie). Promise at-least-once + 客户端 idempotent. Provider responsibility = deliver eventually, consumer responsibility = idempotent | "First — exactly-once is fiction at network boundaries. I do at-least-once + idempotent consumer…" |
| 2 | Idempotency key 双层 | 1.5 min | 每 webhook 带 event_id (UUID v4 or composite tenant_id+resource_id+version). 客户端 dedup 双层: (a) Redis NX SET event_id with TTL 24h (hot path fast O(1)), (b) DB unique index on event_id (cold path durable). Provider also stamp X-Webhook-Id header | "Idempotency key — event_id in body + X-Webhook-Id header, Redis NX + DB unique index dual-layer…" |
| 3 | Retry policy: exp backoff + jitter | 1.5 min | Exponential backoff base 2s, ±20% jitter (avoid thundering herd), max 7 attempts, 36h window. Attempt schedule: 2s, 4s, 8s, 30s, 5min, 1h, 6h, 24h. After 7 fails → DLQ | "Retry — exponential backoff 2^n with ±20% jitter, 7 attempts, 36h window…" |
| 4 | Retry budget + per-client backpressure | 2 min | Global retry budget = 20% of new event rate (不让 retry 把 fresh event 挤掉). Per-client backpressure: (a) per-client queue cap 10k events (overflow → DLQ + alert), (b) per-client concurrency cap 10 in-flight, (c) EMA error rate 5xx > 30% over 1 min → circuit breaker half-open, (d) full circuit breaker if 5xx > 70% for 5 min — pause delivery 5 min, notify customer | "Backpressure — retry budget 20% + per-client queue/concurrency/EMA/circuit breaker…" |
| 5 | DLQ + replay UI | 1.5 min | After 7 fail → DLQ to S3 cold storage 30 day retention. Self-serve replay UI per customer: filter by event_id / date / type, replay single or bulk. Replay re-enters queue, preserves event_id (consumer dedup catches re-replays). Operator audit on bulk replay | "DLQ — S3 cold 30 day, self-serve replay UI per customer, audited bulk replay…" |
| 6 | Ordering: Kafka per-entity partition | 1.5 min | Within same entity (same user_id / order_id), order matters. Use Kafka partition key = entity_id, single consumer per partition, FIFO within partition. Cross-entity ordering NOT guaranteed — explicit in customer-facing doc | "Ordering — per-entity Kafka partition + single consumer, cross-entity not guaranteed by design…" |
| 7 | Security: HMAC-SHA256 + replay window | 1 min | X-Signature header = HMAC-SHA256(body, secret). Consumer recompute + constant-time compare. X-Timestamp + reject if > 5 min skew (replay protection). Rotate signing secret quarterly, support 2 active simultaneously during rotation | "Security — HMAC-SHA256 with 5min timestamp window + dual-secret rotation…" |
| 8 | Resume hook | 1 min | "Concrete: BNPL platform → 50+ merchant webhook for payment events. At-least-once + per-merchant idempotency + Kafka partition by merchant+order. 1 merchant endpoint down 48h, queue 80k event, no loss, automatic replay on recovery. 5 layer 缺一不可 — 之前少 backpressure 一次 cascade 把整个 fleet 拖慢" | "Real example — BNPL 50+ merchant webhook, 48h merchant outage zero loss…" |

### 🎯 为啥按这个序

At-least-once 在第 1 层 set expectation — 不 over-promise. Idempotency key 紧跟是 consumer 责任的合约. Retry policy → backpressure 是 provider 自我保护的 2 层. DLQ + replay 是 "fail visible + customer self-recover" 给客户 dignity. Ordering 单独一层因为 80% 工程师忘了. Security 必须有 (没 HMAC 任何人能 fake). Resume hook 用真实 48h outage 数字 land.

### 🔥 哪一层最容易被追问 deeper

**Layer 4 (backpressure)** — 必被追 "Why both retry budget AND per-client backpressure?" → 答: retry budget 防 retry 总量 starve fresh delivery (global health). Per-client backpressure 防 1 个 client 把整个 fleet 拖死 (noisy neighbor). 两者 attack 不同 failure mode — global congestion vs single-tenant noise. EMA decay 0.9 让 transient spike 不立刻 circuit-break.

**Layer 6 (ordering)** — 追 "What if customer needs cross-entity order?" → 答: hard problem. 3 选 1: (a) global single-partition (low throughput, easy order), (b) vector clock + reorder buffer on consumer (complex), (c) document as "best effort" and recommend customer reconcile via periodic snapshot API. 大多数 case (c) is right answer — webhook is event stream, not ordered log.

### ⏱ 时间压缩版 (30 min round)

- 0-3 min: Layer 1+2 (at-least-once + idempotency dual-layer)
- 3-10 min: Layer 3+4 (retry exp+jitter + backpressure)
- 10-17 min: Layer 5+6 (DLQ replay + Kafka ordering)
- 17-22 min: Layer 7 (HMAC + replay window)
- 22-27 min: Layer 8 BNPL 50-merchant 48h outage
- 27-30 min: Q&A buffer

### 🆘 卡壳兜底 (针对这题)

- 不熟 HMAC code → "constant-time compare via hmac.compare_digest() in Python, never == on bytes (timing attack); SHA256 not MD5"
- 被问 "what if Redis dies during dedup" → "DB unique constraint is the floor; Redis is fast path. Worst case is duplicate processing if both layers fail, but consumer logic should still be idempotent (final unique key insert)"
- 客户 endpoint 5 min latency → "we don't block our queue worker, we async fire-and-monitor with 30s connect + 60s read timeout; long-poll endpoint is anti-pattern, reject in customer onboarding doc"

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 核心心智模型 (1 sentence)

Reliable webhook = "at-least-once delivery (exactly-once is fiction) + 客户端 idempotent by event_id (Redis NX + DB unique 双层) + retry exponential backoff with ±20% jitter 7 attempts 36h window + retry budget 20% cap + DLQ S3 cold 30 day + per-client backpressure (queue cap / concurrency / EMA error rate / circuit breaker) + per-entity Kafka partition ordering + HMAC-SHA256 + self-serve replay UI", 5 layer 缺一不可.

### 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Webhook | 反向 API, producer 主动 HTTP POST 到 consumer URL | 事件驱动 |
| Flaky clients | 间歇性不可用 (30s up / 30s down), 5-10% production | retry 必须 |
| At-least-once | 保证最少 1 次, 可能多次 | 标准选择 |
| Exactly-once | 数学上不可能 (Two Generals) | 别承诺 |
| Idempotency | 同 event_id 重复 noop, by Redis NX + DB unique | consumer 必备 |
| Event ID | UUID 永久, X-Event-Id header | dedup key |
| HMAC-SHA256 | webhook 签名 with client_secret | 防伪造 |
| Timestamp | X-Timestamp header, 5 min 容差 | 防 replay attack |
| DLQ (Dead Letter Queue) | retry N 次失败的 event, S3 cold 30d | tier 兜底 |
| Backoff with jitter | base × 2^attempt × (1 + random(-0.2, 0.2)) | 防 thundering herd retry |
| Retry budget | retry 占 < 20% 总流量 | 防 retry storm |
| Per-entity partition | Kafka hash(client_id, entity_id) | per-entity FIFO |
| Head-of-line block | partition 中 1 个失败 block 后续 | DLQ + skip 5min |
| Circuit breaker | 10 fail → open 5min → half-open 试探 | per-client |
| Adaptive backoff | EMA error rate → per-client 调 concurrency | 慢客户端自动降速 |
| Self-serve replay | customer UI 选 time range + event-type + 重发 | DLQ 救援 |

### 5 个核心 framework / pattern

**Framework 1**: At-least-once + 客户端 idempotency (双层 dedup)
- When: 所有 webhook
- Algorithm: producer at-least-once + consumer Layer 1 Redis SET NX 1h TTL + Layer 2 DB unique constraint
- Trade-off: 不能承诺 exactly-once (网络 + restart + race), 接受重复 + dedup
- Tools: Redis SETNX, Postgres UNIQUE index on event_id, async business logic after ACK 200

**Framework 2**: Retry schedule (exponential backoff + jitter + cap + budget)
- When: 5xx / 408 / 429 / 连接失败
- Algorithm: immediate → 30s → 2m → 10m → 1h → 6h → 24h → DLQ (Stripe 风格, 36h window); jitter ±20%; budget 20% 上限; 4xx (除 408/429) NOT retry
- Trade-off: 太短 retry 错过故障窗, 太长用户等; 36h 是 sweet spot
- Tools: Retry-After header respect, retry budget per client, Cancellation on entity deleted

**Framework 3**: Ordering — Per-entity Kafka partition (推荐)
- When: 业务有顺序要求 (created → updated → deleted)
- Algorithm: Kafka partition by hash(client_id, entity_id), 单 consumer per partition (FIFO 保证)
- Trade-off: per-entity 顺序保, global 不可扩展, no-order 最简单但客户端必须 tolerate
- Tools: Kafka partition strategy, head-of-line block → skip + DLQ after 5min, sub-partition by event-type (high-volume)

**Framework 4**: Backpressure 4-layer
- When: client slow / down
- Algorithm: 1) Per-client queue cap 10K → DLQ / 2) Per-client concurrency cap (Semaphore 10 in-flight) / 3) Adaptive EMA error rate → per-client concurrency / 4) Circuit breaker (10 fail → 5min open → half-open)
- Trade-off: 4 层都加 latency, 但慢客户端会拖死 producer
- Tools: Per-client semaphore, EMA tracker, defaultdict CircuitBreaker

**Framework 5**: DLQ + Observability + Self-serve replay
- When: 真正挂掉的 event
- Algorithm: S3 cold + Postgres index (DLQEntry metadata), customer UI 选 (client, time-range, event-type, status), dry-run 预估, audit log, 保留原 event_id (still dedup-able)
- Trade-off: DLQ 30d 存储成本 vs 客户撑腰
- Tools: S3 Glacier cold, customer dashboard, replay rate-limited respect downstream

### 关键决策树 (ASCII)

```
Webhook 投递语义:
At-least-once + 客户端 dedup ⭐ (95% case)
Exactly-once: 数学不可能 别承诺

HTTP response:
2xx → ACK
4xx (除 408/429) → DLQ (permanent)
408 / 429 / 5xx / conn refused / timeout → Retry

Retry decision per status:
408 timeout → YES
429 rate limit → YES (respect Retry-After)
500 / 502 / 503 / 504 → YES
Connection refused → YES
SSL/TLS error → NO (alert humans)
4xx (其他) → NO (permanent)

Ordering choice:
No ordering → 最简单, client 必 tolerate
Per-entity (Kafka hash) ⭐ → 多数场景够
Global single partition → 不可扩展, 几乎不选

Failure escalation:
< 1h → retry quietly
1-6h → log + dashboard
> 24h → DLQ + customer alert
> 7d in DLQ → customer abandons or escalate sales

Customer 不能 expose endpoint?
Option 1: Polling reverse (client polls us)
Option 2: SSE long polling
Option 3: Customer-hosted gateway (AWS EventBridge in their VPC)
```

### Part 2 五个深度问题速查

**Problem 1: At-least-once vs Exactly-once**
- 核心解法: at-least-once + consumer idempotent (Redis NX layer 1 + DB unique layer 2), 接受重复
- Top 3 gotchas: 不能承诺 exactly-once (Two Generals Problem) / consumer 必加 idempotency / 快速 ACK 200 + async business logic
- Tools: Redis SETNX, Postgres ON CONFLICT DO NOTHING, msg.canonical_form() for dedup

**Problem 2: Retry exponential + jitter + cap + budget**
- 核心解法: immediate → 30s → 2m → 10m → 1h → 6h → 24h → DLQ (8 attempts, 36h), ±20% jitter, 4xx NOT retry except 408/429, budget 20% 总流量
- Top 3 gotchas: 没 jitter = retry storm 同秒 / 4xx retry 浪费 / cancellation on entity deleted
- Tools: Retry-After header parser, RetryBudget class, retry_queue.cancel on entity delete

**Problem 3: Ordering — Per-entity vs Global vs None**
- 核心解法: per-entity Kafka partition (hash(client_id, entity_id)) — 同 entity 单 consumer FIFO; head-of-line block 5min → skip + DLQ + notify; sub-partition by event-type for high-volume entity
- Top 3 gotchas: global ordering 不可扩展 / head-of-line block 必有 timeout / 不破坏 entity order without explicit trade-off
- Tools: Kafka partition strategy, side-queue for retry break ordering trade-off

**Problem 4: Backpressure + Per-client adaptive**
- 核心解法: 4-layer (queue cap / concurrency cap / adaptive EMA / circuit breaker); EMA error_rate update 0.95×old + 0.05×delta; per-client semaphore 10 in-flight
- Top 3 gotchas: 没 queue cap → OOM / 没 concurrency cap → 慢 client 独占 worker / circuit breaker half-open 试探, 不一直 closed
- Tools: defaultdict(Semaphore), AdaptiveDelivery EMA tracker, CircuitBreaker

**Problem 5: DLQ + observability + replay**
- 核心解法: DLQEntry (event_id, client, payload, reason, response, attempts, ts), S3 cold + Postgres index, customer self-serve UI (time range + event-type + status), dry-run, audit
- Top 3 gotchas: DLQ retention 30d 不够 customer 抱怨 / replay 保留原 event_id 让 client 仍 dedup / audit log redact PII
- Tools: customer dashboard, dispute window 60d, rate-limited replay

### Production gotchas (top 15)

1. Promise exactly-once (don't, fiction)
2. No DLQ (events 永循环 retry)
3. No jitter (thundering herd retry)
4. Retry on 4xx (wastes resources)
5. No ordering 处理 (multi-event entities race)
6. No backpressure (slow client → OOM)
7. No HMAC signing (forged webhook attack)
8. Sync business logic in handler (slow → producer 重试风暴)
9. 明文 webhook body in log (PII leak)
10. No retry budget (retry 长期占主流量)
11. Same ts events 没 tie-break (订单 created/updated 同 ts 顺序乱)
12. Customer URL hardcoded 改了就废 (self-serve config)
13. No replay UI customer 不能自救
14. Webhook signing 2 secret rotation 没 cutover 设计
15. Per-client SLA 没分级 (Gold 应有 dedicated worker pool + lower queue depth)

### 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| At-least-once + dedup | ConvFinQA agent retry | client_msg_id idempotency key |
| Exponential backoff + jitter | Voice agent ASR/TTS retry pipeline | 7 attempts capped 36h with DLQ to S3 |
| DLQ pattern | Voice agent failed calls 上报 | S3 cold + ops review |
| HMAC signing | Voice agent multi-tenant auth | per-customer secret + rotation |
| Per-client backpressure | 7 markets traffic asymmetry | per-market concurrency cap |
| Adaptive per-client | Voice agent 5% bad-network | 自动降低 retry frequency |
| Self-serve replay | Voice agent ops dashboard | time-range + event-type filter |
| Polling fallback | Voice agent firewall'd merchant | reverse polling for behind-firewall |

### 面试现场 quotables (top 8)

1. "At-least-once + client idempotent is standard. Exactly-once is fiction — Two Generals Problem mathematically prevents 100% consensus over network."
2. "Retry schedule Stripe-style: immediate / 30s / 2m / 10m / 1h / 6h / 24h / DLQ. 36h window, ±20% jitter."
3. "Retry budget 20% prevents retry-becomes-main-traffic — a long-down client doesn't starve healthy clients."
4. "Per-entity Kafka partition (hash client_id + entity_id) preserves order per entity, parallelizable across entities."
5. "Head-of-line block 5 min → skip + DLQ + customer notify. Ordering relaxed under sustained failure with explicit tag."
6. "Per-client adaptive: EMA error rate → adjust concurrency (50/20/5/1 healthy → near-death)."
7. "Customer self-serve replay UI: time range + event-type + status. Preserves event_id so client still dedup. Customers love rescuing events themselves."
8. "Voice agent: 5% bad-network customers auto-detected and shifted to lower-frequency retries. Don't retry same way for all clients."

### 红线 (top 10 anti-patterns)

1. Promise exactly-once (impossible)
2. No DLQ
3. No jitter (thundering herd)
4. Retry on 4xx (permanent errors waste)
5. No ordering 处理 multi-event entities
6. No backpressure (slow client OOM)
7. No HMAC signing
8. Sync handler (producer 超时风暴)
9. Webhook body in log unredacted
10. No retry budget cap

### Retry decision table (per HTTP status)

| Status | Retry? | Reason |
|---|---|---|
| 200, 201, 202, 204 | NO | Success |
| 301, 302, 303 | follow redirect | 不算 retry |
| 400 | NO | Client permanent error |
| 401 | NO* | Signature problem, alert humans |
| 403 | NO | Permission denied |
| 404 | NO | URL not exist |
| 408 Timeout | YES | Network layer timeout |
| 422 Unprocessable | NO | Client data format |
| 429 Rate Limit | YES (with Retry-After) | Respect 对方限流 |
| 500, 502, 503, 504 | YES | Server transient |
| Connection refused | YES | Temporarily unavailable |
| Connection timeout | YES | Network issue |
| SSL/TLS error | NO* | Cert / handshake, alert humans |

### Retry schedule with jitter (Stripe-style)

| Attempt | Base delay | With jitter ±20% |
|---|---|---|
| 1 | immediate | 0 |
| 2 | 30 s | 24-36 s |
| 3 | 2 min | 96-144 s |
| 4 | 10 min | 8-12 min |
| 5 | 1 h | 48-72 min |
| 6 | 6 h | 4.8-7.2 h |
| 7 | 24 h | 19-29 h |
| 8 | → DLQ | n/a |

Total window ≈ 36h, retry budget 20% of total traffic per client.

### Headers checklist

| Header | Lifetime | Purpose | Set by | Consumed by |
|---|---|---|---|---|
| X-Event-Id | Permanent (UUID) | Dedup | Producer | Consumer |
| X-Signature | Per request | HMAC-SHA256 verify | Producer signs | Consumer verifies |
| X-Timestamp | 5 min tolerance | Replay attack defense | Producer current ts | Consumer rejects too old |
| Content-Type | per request | application/json | Producer | Consumer |
| X-Retry-Count | per request | dedup hint + observability | Producer | Consumer (optional) |
| Idempotency-Key | per request | client-side dedup (Stripe-style) | Producer | Consumer |

### Backpressure 4-layer detail

| Layer | Mechanism | Threshold |
|---|---|---|
| 1 Per-client queue cap | max_depth_per_client | 10K → DLQ overflow |
| 2 Per-client concurrency | Semaphore in-flight | 10 max parallel HTTP |
| 3 Adaptive EMA | error_rate = 0.95×old + 0.05×delta | 0-5% → 50 conc / 5-20% → 20 / 20-50% → 5 / > 50% → 1 |
| 4 Circuit breaker | 10 consecutive fail → open 5 min | half-open 试探 1 req → close on success |

### Observability 4 维度

| Dim | Metric | Alert |
|---|---|---|
| Per-client delivery rate | Success/min by client | < 50% for > 10 min → alert |
| DLQ growth rate | DLQ entries/min | > 100/min sustained → page |
| Queue depth | Per-client in-flight | > 80% of max → warn |
| Latency p99 | First-attempt to ACK | > 5s → investigate |

### DLQ entry schema

| Field | Type | Purpose |
|---|---|---|
| event_id | str (UUID) | dedup |
| client_id | str | tenant |
| original_payload | dict | replay |
| failure_reason | str | "max_retries_exceeded", "4xx_permanent", etc. |
| last_attempted_at | datetime | when last try |
| last_response_code | int | HTTP status |
| last_response_body | str | reason from client |
| attempt_count | int | total retries |
| sent_to_dlq_at | datetime | when entered DLQ |
| can_replay | bool | self-serve allowed |

### 5 业务场景变体 (anchor stories)

| Variant | Producer | Consumer | Key concern |
|---|---|---|---|
| TikTok PayLater → merchant CRM | PayLater | merchant CRM | merchant 半夜 maintenance → retry 兜底 |
| Stripe → SaaS | Stripe | your SaaS | at-least-once → idempotency 必须 |
| GitHub → CI/CD | GitHub | CI system | ordering (created→updated→closed) |
| IoT platform → customer alarm | IoT system | customer alarm | volume 1M+ events/sec, short outage = 几十万事件丢失风险 |
| Twilio SMS → marketing | Twilio | marketing system | ordering 重要 ("STOP" 后 "OK" vs 反过来) |

### Self-serve replay UI

| Component | Example |
|---|---|
| Client filter | acme-corp dropdown |
| Time range | [2026-05-19 14:00] – [2026-05-19 16:00] |
| Event types | [payment.succeeded ✓] [call.completed ✓] |
| Status filter | [Failed ✓] [DLQ ✓] |
| Dry-run output | "Found 142 events. Estimated 5 minutes. Will respect rate limits." |
| Actions | [Replay Now] [Export CSV] [Cancel] |
| Replay tracking | event_id preserved → client still dedup |
