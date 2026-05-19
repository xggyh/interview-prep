## 题目（verbatim）

> "Design **reliable webhook integration** when client systems **frequently go offline**. Cover retry, idempotency, dead-letter handling, backpressure."

**出处**：fde.academy 技术 round 经典. Stripe-style webhook problem 适用所有 enterprise.

**Round**：Technical Integration (45 min)

---

## 这道题在考什么

考你做过 **producer-side webhook delivery** —— Stripe/Twilio/Shopify 都解过的标准问题：

1. **At-least-once vs exactly-once** —— 哪个 realistic
2. **Idempotency model** —— 客户端 dedup 还是服务端
3. **Retry strategy** —— exponential backoff + jitter + cap
4. **DLQ (dead letter queue)** —— 永远失败的事件怎么 handle
5. **Backpressure** —— 客户端 slow，我方 queue 不能爆

---

## 必问 clarifying questions

**1. Direction**

> "We send to client (we're webhook producer) or client sends to us (we're webhook consumer)? Usually 前者 for SaaS."

**2. Volume**

> "Events/sec sustained + peak? 100/s? 10k/s?"

**3. Order matter?**

> "Strict ordering required (e.g., `created → updated → deleted` for same entity), or events independent?"

**4. Acceptable delay**

> "How fresh? Real-time (<1s), seconds-fresh (<10s), or eventual (<1min)?"

**5. Client patterns**

> "All clients behave similar, or 1% are slow + 1% always down + 98% fine? Long-tail behavior changes design."

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify direction + volume + ordering |
| 5-15 min | Core delivery model (queue → worker → HTTP POST) |
| 15-25 min | Retry strategy (backoff + jitter + cap + DLQ) |
| 25-35 min | Idempotency (event_id) + ordering |
| 35-45 min | Backpressure + per-client rate limit + monitoring |

---

## 我会这样答（sample monologue）

> "Clarify — *[假设：we're producer, 1k events/sec sustained 10k peak, ordering matters per-entity not globally, real-time aim <5s p99, 5% of clients are flaky]*.
>
> **Architecture**:
>
> ```
> Event source → Kafka topic (partition by client_id × entity_id for per-entity order)
>                    ↓
>              Webhook Worker Pool (consumers per client_id partition)
>                    ↓
>              HTTP POST to client URL
>                    ↓ (on failure)
>              Retry Queue (Kafka with delay) → Worker
>                    ↓ (after N retries)
>              DLQ (cold storage, S3 + dashboard)
> ```
>
> **Delivery model**: at-least-once with idempotent receiver. **Exactly-once is fiction across network**, force client to dedup by `event_id`.
>
> **Retry strategy**:
> ```
> Attempt 1: immediate
> Attempt 2: 30s
> Attempt 3: 2min
> Attempt 4: 10min
> Attempt 5: 1h
> Attempt 6: 6h
> Attempt 7: 24h
> Attempt 8: DLQ
> ```
> Each with **±20% jitter** to prevent retry stampede.
>
> Total retry window ~36 hours. After DLQ, **manual + alert customer**.
>
> **What status codes to retry**:
> - **5xx**: retry (server-side temporary)
> - **429**: retry with `Retry-After` header
> - **408, 503**: retry
> - **Connection errors, timeouts**: retry
> - **4xx other than 408/429**: NO retry (permanent error like 401 = bad creds, 422 = bad data)
>
> **Idempotency**:
> - Every webhook includes `X-Event-Id` header (UUID)
> - Client is expected to dedup by this ID
> - Documented in our spec
> - Provide a **dedup-cache library** for top languages
>
> **Ordering per-entity**:
> - Partition Kafka topic by `client_id × entity_id`
> - Single consumer per partition guarantees ordered delivery
> - If `order_123.updated` retries 30s, all subsequent `order_123` events wait. Deadline:
>   - After max wait (5 min), **skip** the stuck event into DLQ, send next
>   - Customer notified: "order_123 events out-of-order, oldest in DLQ"
>
> **Backpressure**:
> - Per-client max in-flight requests (e.g., 50 concurrent POSTs)
> - If client returns 429 / consistently slow → **dynamic backoff per client** (their queue depth grows, we slow more)
> - Kafka topic-level retention 14 days — even if client is down 13 days, replay works
> - **If client's queue grows > 1M events**, **page customer** + auto-suspend webhook with alert
>
> **Signing for security**:
> - Every webhook signed with HMAC-SHA256 + client secret
> - Header: `X-Signature: t=<timestamp>,v1=<hash>`
> - Client verifies → guards against forged webhooks from attackers
> - Secret rotation: support 2 active secrets (current + previous) for 30-day cutover
>
> **Monitoring**:
> - **Per-client delivery rate** (over 5 min): alert if drops to 0
> - **Queue depth** per client
> - **DLQ size** per event type
> - **p99 delivery latency** end-to-end
>
> **Failure modes**:
> - **Stampede on retry**: jitter solves
> - **Client URL changes**: provide self-serve config update
> - **Client returns 200 but didn't process**: that's their bug, we're done at HTTP layer
> - **DLQ explodes**: alert, then **bulk-retry option** for ops once client recovers
> - **DDoS via webhook**: if attacker injects events → we'd flood client. **Rate limit at event source**
>
> **Customer experience**:
> - **Real-time dashboard**: per-event status (delivered / retrying / DLQ)
> - **Self-serve retry**: customer can manually replay specific events
> - **Audit log**: every attempt + response code logged 90 days
> - **Webhook testing tool**: simulate POSTs to validate client's endpoint
>
> **Phasing 30 days**:
> - Wk 1: Core delivery + simple retry
> - Wk 2: Idempotency + signing
> - Wk 3: DLQ + monitoring dashboard
> - Wk 4: Self-serve retry tool + ordering"

---

## 简历专属 reframe

你的 **voice agent multi-region** + **BNPL chatbot retry logic** 都涉及类似：

| 题 | 你做过 |
|---|---|
| At-least-once + dedup | ConvFinQA agent retry with idempotency key (`client_msg_id`) |
| Exponential backoff + jitter | Voice agent ASR/TTS retry pipeline |
| DLQ pattern | Voice agent failed calls 上报系统 |
| HMAC signing | Voice agent multi-tenant auth (类似) |
| Per-client backpressure | 7 markets traffic asymmetry handling |

**主动说**：

> "On the voice agent retry pipeline I built, we used **exponential backoff with jitter + 7 retry attempts capped at 36h** with DLQ to S3. The thing that surprised me was **per-client behavioral fingerprinting** — 5% of customer phones were on bad networks; we auto-detected and shifted those to lower-frequency retries to avoid wasting compute. I'd apply the same lesson to webhook delivery: **don't retry the same way for all clients**, adapt to their pattern."

---

## 5 follow-ups

**Q1**: "Customer says they need 99.99% delivery. Possible?"
**A**: 跟 99.99% **eventual** delivery 是可行的 (we always retry until DLQ), 但 **99.99% within real-time** 是 unsupportable if client is down. Frame:
- "99.99% eventual delivery via 36h retry window — yes"
- "99.99% delivered within 5s — requires client to maintain 99.99% uptime, which is **on them**"
- **Customer Tier upgrade**: dedicated worker pool for Gold (more aggressive retry, lower queue depth)

**Q2**: "Client only accepts 1 webhook at a time (no concurrency). 10k events/sec arrives. Stuck?"
**A**:
- Per-client concurrency = 1 → queue grows
- After queue depth > threshold → page customer with options:
  1. Customer's URL handler must process faster (their problem)
  2. We **batch deliver** N events per call (negotiate API change)
  3. Customer accepts increased latency / DLQ growth

**Q3**: "Client misses 3-day event burst, asks us to replay everything 'newest first'."
**A**:
- DLQ retention 30 days → can replay
- **Replay UI**: customer picks time range, replay starts
- **Newest-first** for catching up: emit events in reverse-time order
- Standard pattern for migration-back-online scenarios

**Q4**: "Race: client sends 'updated' before we deliver 'created'. State mismatch."
**A**: 不可能 from our side if same-entity events partitioned to same Kafka partition (FIFO).
But race CAN happen if **client** does parallel processing internally → that's their architecture. We help by including:
- `event_sequence_number` per entity (we own)
- `created_at` server-side timestamp
- Client should buffer + process in order if their handler is async

**Q5**: "We need to deliver to webhook URL behind firewall (corporate). They can't expose endpoint."
**A**: 3 options:
1. **Polling reverse**: client polls us instead of us pushing. Less real-time but firewall-friendly
2. **Long polling / SSE**: server-sent events client opens
3. **Customer-hosted gateway**: we push to their cloud broker (e.g., AWS EventBridge), they consume from inside firewall

---

## ❌ 易错点

1. **Promise exactly-once** — 不存在
2. **No DLQ** — events 永远 stuck in retry
3. **没 jitter** — retry stampede
4. **Retry on 4xx** — wastes resources on permanent errors
5. **没 ordering 处理** — multi-event entities race
6. **没 backpressure** — slow client cause queue OOM
7. **没 HMAC signing** — replay attacks / forged webhooks

---

## ✅ 加分项

1. **at-least-once + client-side idempotency** standard pattern
2. **Per-entity Kafka partition** for ordering
3. **Exponential backoff + jitter + 7 attempts + DLQ**
4. **HMAC-SHA256 signing** + 2-secret rotation
5. **Self-serve retry UI** for customer
6. **Per-client adaptive backoff** based on history
7. **Webhook testing tool** for onboarding
8. **Polling fallback** for firewall'd clients

---

## Cheat Sheet

```
Delivery model:
  at-least-once + receiver dedup by event_id

Retry schedule (with ±20% jitter):
  immediate / 30s / 2m / 10m / 1h / 6h / 24h / DLQ
  Total ~36h window

What to retry:
  5xx, 408, 429 (with Retry-After), conn errors
  NEVER 4xx (other than 408/429)

Ordering:
  Kafka partition by client × entity
  Single consumer per partition
  Skip stuck events to DLQ after 5min

Backpressure:
  Per-client max concurrency
  Queue depth alert > threshold
  Auto-suspend at extreme depth
  Tenant tier dedicated workers for Gold

Security:
  HMAC-SHA256 signing
  2 active secrets for rotation
  Replay protection via timestamp
  TLS 1.3 transit

Customer tools:
  Dashboard: per-event status
  Self-serve retry by time range
  Audit log 90 days
  Test endpoint validator

红线:
  - Exactly-once promise (fiction)
  - No DLQ
  - No jitter
  - Retry on 4xx
```
