## Tech #2 · Reliable Webhook — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/webhook-flaky-clients.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`webhook-flaky-clients.html`](questions/webhook-flaky-clients.html)

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
