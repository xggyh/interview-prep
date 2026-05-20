## 题目（verbatim）

> "Design **multi-tenant SaaS monitoring** with **varying client SLA requirements**. Per-tenant quotas, noisy-neighbor isolation, billable signal aggregation."

**出处**：fde.academy 技术 round. Databricks / Snowflake / Datadog 都问过.

**Round**：Technical Integration (45-60 min)

---

## 这道题在考什么

考你做过 **multi-tenant SaaS infrastructure**:

1. **不同 SLA tier 怎么 enforce** —— Bronze vs Gold 怎么物理 / 逻辑区分
2. **Noisy neighbor isolation** —— 大客户不能影响小客户
3. **Billable signal** —— 哪些 metric 算 billable (latency 5xx 等)
4. **Aggregation at scale** —— 1B+ events/day 怎么 store + query 每 tenant 不会爆

---

## 必问 clarifying questions

**1. SLA tiers**

> "How many tiers — Bronze/Silver/Gold? What does each promise (availability %, latency p99, throughput)?"

**2. Tenant count + size distribution**

> "100 tenants or 100k? Long-tail (5 huge, many tiny) or evenly distributed?"

**3. Multi-tenancy model**

> "Pooled (shared infra) or siloed (dedicated)? Hybrid common — small tenants share, large dedicated?"

**4. Billing granularity**

> "Per-API-call billing? Per-resource-hour? Tiered subscription with overage?"

**5. Existing observability**

> "Are we building on Datadog / Prometheus + Grafana? Or greenfield?"

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify tier model + size dist + multi-tenancy model |
| 5-20 min | **Storage + ingestion** architecture (Kafka/TSDB sharded by tenant) |
| 20-30 min | **Noisy neighbor isolation** (quota + WFQ + tiered placement) |
| 30-40 min | **SLA computation** + per-tenant alert |
| 40-50 min | Billable signal aggregation + audit |
| 50-60 min | Failure modes + onboarding |

---

## 我会这样答（sample monologue）

> "Clarify — *[假设：3 tiers (Bronze 99.5%, Silver 99.9%, Gold 99.99%), 10k tenants long-tail (top 100 = 80% traffic), pooled with dedicated for Gold, per-API-call billing + overage]*.
>
> **High-level architecture**:
>
> ```
> Tenant requests → API Gateway (auth + rate limit per tenant)
>                         ↓
>                  App Layer (multi-tenant DB queries, etc.)
>                         ↓
>                  Telemetry emit (every request: tenant_id, latency, status)
>                         ↓
>                  Kafka (partition by tenant_id)
>                         ↓
>                  Stream Processor (Flink): per-tenant 1-min rollups
>                         ↓
>                  TSDB (sharded by tenant_id)
>                         ↓
>                  Per-tenant dashboard + SLA computer + alerts + billing
> ```
>
> **Storage**: ClickHouse with `(tenant_id, timestamp)` primary key. Per-tenant query naturally hits 1 shard.
>
> **Noisy-neighbor isolation**: 3 layers
>
> **L1: Rate limit at API Gateway**
> - Token bucket per tenant: Bronze 100 QPS, Silver 1000, Gold 10000 (configurable)
> - Burst allowance: 2x for 60s
> - Beyond → 429 with `Retry-After`
>
> **L2: Resource quota at app layer**
> - Per-tenant DB connection pool max (Bronze 5, Silver 50, Gold 500)
> - Per-tenant memory budget for query result sets
> - Background worker pool fair-share (WFQ — Weighted Fair Queueing)
>
> **L3: Physical isolation for Gold**
> - Gold tenants run on dedicated replica set
> - Bronze/Silver share pooled infra
> - **Tier upgrade**: deploy fresh dedicated infra in N minutes, drain pooled traffic
>
> **SLA computation**:
>
> Per-tenant SLOs:
> - Availability = (successful_requests / total_requests) over 5min sliding window
> - Latency p99 over 5min window
> - **Error budget**: monthly, draws down on each 5xx / breach
>
> Daily SLO digest auto-sent to customer + their account manager.
> Real-time alerts when error budget burn rate > N% per hour.
>
> **Billable signal aggregation**:
>
> Bill components:
> - API calls (counter)
> - Storage GB-hours (gauge)
> - Compute milliseconds (counter)
>
> Stream processor outputs:
> ```
> {
>   tenant_id, hour, total_calls, total_4xx, total_5xx,
>   storage_gb_hours, compute_ms, sla_minutes_breached
> }
> ```
> Persist hourly aggregates in **billing DB** (separate from telemetry DB).
> Monthly rollup → invoice.
>
> **Audit**: every billable event has provenance (request ID + tenant + timestamp).
> Tenant can self-serve **usage report** + **dispute window** (60 days).
>
> **Failure modes**:
> - **Quota exhaustion under burst**: gold burst can starve silver if shared pool. Mitigate: separate gold pool.
> - **Telemetry pipeline lag** at peak: degrade to **sampled telemetry** (1/10) to keep up
> - **Misattribution**: shared services (rate limiter itself) — attribute by tenant_id in trace
> - **DDoS via legit tier**: high-tier customer compromise → flood. Per-tenant max QPS hard ceiling even within tier.
>
> **Onboarding new tenant**: provisioning script creates per-tenant quota config + dashboard + alerting rules. <10 min.
>
> **Cost optimization for telemetry**:
> - 1-minute rollups for hot store (30 days)
> - 1-hour rollups for warm (1 year)
> - Daily rollups for cold (3+ years)
> - Saves 90%+ storage cost on long tail"

---

## 简历专属 reframe

你的 **voice agent 7 markets** 是天然 multi-tenant：

| 题 | 你的经验 |
|---|---|
| Per-tenant SLA tiers | 7 markets 不同 latency / accuracy SLA |
| Noisy neighbor isolation | Indonesia 流量 burst 不影响 Thailand |
| Token bucket rate limit | API gateway 自然有 |
| Per-tenant dashboard | 你 weekly 跟 regional ops review |
| Billing signal | ByteDance 内部 chargeback 通常按 region |

**主动说**：

> "We treated 7 markets as 7 tenants in our voice agent. Each had a different SLA — Indonesia high-volume tolerance for 200ms, Thailand stricter at 150ms. We isolated via **per-market Kafka partitions + dedicated inference replicas for the top-3 markets**. Indonesia burst once during a payday spike — 5x normal traffic. **Because the top-3 were dedicated, Thailand and Korea were unaffected**. That isolation was worth its hardware cost."

---

## 5 follow-ups

**Q1**: "Gold tenant suddenly spikes 20x, burns through capacity. What now?"
**A**: Tier-protected:
- Hard ceiling per tenant even in tier (e.g., 100k QPS max regardless of Gold)
- Auto-scale dedicated infra (+20% capacity for 1h)
- Customer-facing alert: "you're approaching capacity, do you need a tier upgrade?"
- Bill overage 1.5x normal rate (motivation to upgrade)

**Q2**: "Bronze tenant DDoS attempt — how protect Silver/Gold?"
**A**:
- Pooled Bronze infra completely separate physical from Silver/Gold
- Cross-tier blast radius zero by design
- Automated anomaly detection on Bronze: 100x normal → temporary throttle + alert customer

**Q3**: "1B events/day storage cost — how reduce?"
**A**:
- 90% to cold tier after 30 days (1/30 the cost)
- **Aggregate-first storage**: raw events for 7d, 1-min rollups for 90d, 1-hour for year+
- **Sampling** for non-critical metrics (debug traces)
- **Per-tenant retention** (Bronze 30d, Gold 1y)

**Q4**: "Customer disputes a billing line. How do we prove?"
**A**:
- **Per-request audit log** retained 13 months (1 year + buffer)
- Tenant can self-serve usage report (CSV download)
- Dispute window 60 days
- **Cryptographic signature** on monthly invoice (tamper-proof)
- Internal "billing replay" tool: ops can reconstruct billing from raw logs

**Q5**: "Multi-region deployment. SLA computed in which region?"
**A**:
- SLO **per region** (each region has its own availability score)
- Customer sees **per-region** dashboard
- Overall SLA = min(regions used) OR weighted by traffic distribution (negotiated)
- Cross-region failover may pause SLO computation briefly (5-10 min)

---

## ❌ 易错点

1. **Single shared infra** for all tiers — no isolation
2. **没 rate limit at gateway** — app layer overloaded
3. **没 quota per-tenant DB connections** — single tenant 杀全 DB
4. **Billing 跟 telemetry 同 DB** — billing 精度受 telemetry retention 影响
5. **Aggregate at query time** — query 慢 + 贵
6. **没 dispute window / audit** — billing 不可挑战, customer 怒
7. **Sampling for everything** — billing 数据不能 sample

---

## ✅ 加分项

1. **3-layer isolation** (gateway / app / physical)
2. **Tier-based dedicated infra** for Gold
3. **Error budget burn rate** alerts (modern SRE)
4. **Aggregate-first storage** (rollups > raw)
5. **Billing 独立 DB** + cryptographic invoice
6. **Per-region SLO** computation
7. **Hard ceiling even in tier** anti-DDoS
8. **Tenant self-serve usage report**

---

## Cheat Sheet

```
3 isolation layers:
  L1 API Gateway: token bucket per tenant by tier
  L2 App: DB pool, memory quota, WFQ
  L3 Physical: dedicated replicas for Gold

SLA computation:
  Availability % over sliding window
  Latency p99 over window
  Error budget monthly, alert on burn rate

Tier 标准:
  Bronze 99.5% / 100 QPS / pooled
  Silver 99.9% / 1k QPS / pooled
  Gold 99.99% / 10k QPS / dedicated

Storage (cost optim):
  Raw 7d in hot
  1-min rollups 30-90d in warm
  1-hour 1-year+ in cold
  Daily 3+ years compliance

Billing:
  Separate DB from telemetry
  Per-request audit 13 months
  Tenant self-serve report
  Crypto-signed invoice
  60-day dispute window

Noisy neighbor:
  Hard ceiling even in tier
  Auto-scale on Gold burst
  Bronze完全 isolated from Silver/Gold
```
