## Tech #5 · Multi-tenant SLA Monitoring — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](multitenant-monitoring-slas.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`multitenant-monitoring-slas.html`](multitenant-monitoring-slas.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"你 SaaS 服务 500 个 tenant, 1 个 Bronze tenant 突然 100x traffic, 怎么不让它拖垮 Gold tenant SLA, 怎么监控, 怎么 bill?"** 我按这 8 层回答, 不跳序.

### 📐 Multi-tenant SLA Monitoring — 8 层 isolation + observability + billing

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 |
|---|---|---|---|---|
| 1 | Frame: noisy neighbor 是 multi-tenant 第一敌人 | 30s | 不是 "monitor everything", 是 "isolate first, then observe". 1 个 Bronze 不能拖 Gold — 这是 multi-tenant SaaS 第一原则 | "First — isolation before observation. Noisy neighbor is the primary failure mode…" |
| 2 | 3 层 isolation | 2 min | (a) **Gateway** token bucket per-tenant (10/s Bronze, 100/s Silver, 1000/s Gold) — fast cheap; (b) **App layer** DB pool partition + Weighted Fair Queue (WFQ) — fair share under contention; (c) **Physical** — Gold gets dedicated infra (cluster / VPC / shard), Bronze shared pool. 3 层 分而治之 | "Three isolation layers — gateway token bucket / app WFQ / physical dedicated for Gold…" |
| 3 | Tier-based SLA + threshold | 1.5 min | Gold 99.99% availability + p99 200ms latency, Silver 99.9% + 500ms, Bronze 99% + 1s. Error budget per tier (Gold 4 min/month, Silver 43 min/month, Bronze 7h/month). 客户 contract 显式声明 | "Tier SLA — Gold 99.99/200ms / Silver 99.9/500ms / Bronze 99/1s with error budget per tier…" |
| 4 | Per-tenant SLI + cardinality control | 2 min | Cardinality 是 multi-tenant monitoring 第一陷阱. 500 tenant × 50 metric × 10 label = 250k series Prometheus 顶不住. 我用: (a) top-N tenant 全量 SLI (Gold + Silver + top 20 Bronze by spend), (b) 长尾 Bronze aggregated to bucket ('bronze_low'/'bronze_med'), (c) Mimir / Cortex 横扩 storage, (d) per-tenant only on dimensions that matter (availability + latency + error rate, not 50 random labels) | "Cardinality — top-N tenant full + tail aggregated + Mimir horizontal, never label-explode…" |
| 5 | Multi-window burn rate alert | 1.5 min | Google SRE multi-window: 1h@14x burn (2% budget in 1h → page), 6h@7x burn (5% in 6h → page), 1d@3x burn (10% in 1d → ticket), 3d@1x burn (10% in 3d → review). 4 window 避免 alert fatigue + 抓 slow leak | "Multi-window burn rate — 1h@14x page / 6h@7x page / 1d@3x ticket / 3d@1x review…" |
| 6 | Customer self-serve dashboard + auto-credit | 1 min | Per-tenant dashboard (Grafana panel filtered by tenant_id) showing their SLI vs SLA + error budget remaining. SLA breach auto-detect + auto-credit (no manual review for credit < $X) — customer trust signal | "Customer-facing — Grafana per-tenant dashboard + auto-credit on SLA breach for trust…" |
| 7 | Billing audit 独立 | 1 min | Billing metering 用独立 DB (从可观测 metric 抽), WORM storage 13 month, HMAC-signed event log, monthly reconciliation. 不要用可观测 metric 直接算 bill (compactor 会 drop / sample). 独立 audit trail is regulatory necessity (finance) | "Billing — independent DB + WORM 13 month + HMAC + monthly reconcile, separate from observability metric…" |
| 8 | Resume hook | 1 min | "Concrete: BNPL platform multi-tenant — 50+ merchant. 3-layer isolation, per-tenant burn rate alert, monthly auto-credit on breach. One Black Friday Bronze merchant 100x traffic, Gold merchant p99 unchanged (gateway tier bucket triggered + WFQ kicked in). Billing audit passed annual financial regulator review" | "Real example — BNPL 50+ merchant, Black Friday 100x Bronze spike no Gold impact, regulator-passed billing audit…" |

### 🎯 为啥按这个序

Frame "isolation before observation" 第一 because 90% 候选人 jump 到 "Prometheus per-tenant label" → cardinality 死. 3 层 isolation 是核心 mechanism. Tier SLA 给 isolation 量化目标. Cardinality 控制是 production-only deep — 没踩过坑的人不会讲. Multi-window burn rate 是 Google SRE 现代 alerting. Self-serve dashboard + auto-credit 是 customer-facing UX. Billing audit 是 finance / compliance gotcha. Resume hook 用 Black Friday + regulator pass 双 land.

### 🔥 哪一层最容易被追问 deeper

**Layer 4 (cardinality)** — 必被追 "How do you bound cardinality at 500 tenants?" → 答: hard cap per metric = top 50 + 5 aggregated bucket. Top 50 by spend (Gold + Silver + top Bronze). Bucket criteria: per-region × per-plan-tier × per-volume-tier (low/med/high) = ~12 buckets covering 450 long-tail. Mimir / Cortex / Thanos 横扩 storage as last resort. Never 500 individual tenant label.

**Layer 5 (multi-window burn rate)** — 追 "Why 14x / 7x / 3x / 1x?" → 答: Google SRE workbook math — error budget = 1 - SLO. Burn rate X means consuming budget X times faster than nominal. 14x in 1h burns 2% of monthly budget (page-worthy). 7x in 6h burns 5% (page). 3x in 1d burns 10% (ticket). 1x in 3d burns 10% (review). Mathematically prevents both fast outage missed + slow leak missed.

### ⏱ 时间压缩版 (30 min round)

- 0-3 min: Layer 1+2 (frame + 3 isolation layer)
- 3-10 min: Layer 3+4 (tier SLA + cardinality control)
- 10-15 min: Layer 5 (multi-window burn rate)
- 15-20 min: Layer 6+7 (self-serve dashboard + billing audit)
- 20-26 min: Layer 8 BNPL Black Friday case + regulator audit
- 26-30 min: Q&A buffer

### 🆘 卡壳兜底 (针对这题)

- 不熟 Mimir/Cortex → "Prometheus 单 instance 死, 用 horizontal-scale TSDB; Mimir / Cortex / Thanos / VictoriaMetrics 都行, 选 cluster vs object-store backend"
- 被问 "what if customer demands per-tenant metric on all dimensions" → "explain cardinality + cost; offer top-N + bucket aggregation as default; full per-tenant only for Gold tier as paid feature"
- 不熟 WFQ → "Weighted Fair Queue — each tenant has weight (= tier multiplier), queue scheduler picks next request by deficit round-robin so no tenant starves; alternative = stochastic fair queue"

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 核心心智模型 (1 sentence)

Multi-tenant SaaS monitoring = "3 层 isolation (gateway token bucket / app DB pool & WFQ / physical dedicated for Gold) + per-tenant SLI 但严控 cardinality (top-N tenant 全量 + 长尾 aggregated bucket + Mimir/Cortex 横扩) + tier-based threshold (Gold 99.99%/200ms / Silver 99.9%/500ms / Bronze 99%/1s) + multi-window burn rate alert (1h@14x / 6h@7x / 1d@3x / 3d@1x) + 自助 dashboard + 自动 credit + 严格 billing audit (独立 DB / WORM / HMAC-signed / 13 month)", 1 个 noisy bronze 不能拖 Gold.

### 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| SLI | Service Level Indicator, 一个测量值 | 事实 |
| SLO | Service Level Objective, 内部目标 (99.9%) | aspirational |
| SLA | Service Level Agreement, 合同承诺 (99.5%) + breach credit | 法律 |
| Error budget | 1 - SLO, 月预算 | 43min/month for 99.9% |
| Burn rate | EB 消耗速率, 10x = 4天烧光 | multi-window alert |
| Cardinality | metric label 组合总数 | 10K tenant × 100 metric = 危险 |
| Noisy neighbor | 1 个 tenant 占光资源拖死全场 | 隔离的对象 |
| Token bucket | per-tenant rate limit (refill + capacity) | API Gateway L1 |
| WFQ | Weighted Fair Queueing, priority class | App L2 |
| Dedicated replica | Gold tier 独享 Kubernetes node pool (taint+toleration) | L3 物理隔离 |
| Tier threshold | 同 metric 不同 tier 不同 threshold | per-tier monitoring |
| Streaming aggregation | Flink 1-min rollup per tenant per metric | cardinality 控制 |
| Mimir / Cortex / Thanos | Prometheus 横扩 multi-tenant | > 10M ts 需要 |
| WORM | Write Once Read Many, billing 不可改 | compliance |
| HMAC-signed invoice | 防篡改 | billing audit |
| Self-serve dashboard | customer 看 SLO compliance + EB + usage | transparency |
| Auto-credit | SLA breach 自动 trigger compensation | 不手动 ask |

### 5 个核心 framework / pattern

**Framework 1**: SLI / SLO / SLA / Error Budget Taxonomy
- When: 定义 "好坏" 标准
- Algorithm: SLI (event-based 计算) → SLO (内部 99.9%) → SLA (合同 99.5% + credit) → EB (1-SLO × total in window); SLA < SLO 留 20-50% buffer
- Trade-off: SLO 严但 buffer 大 vs 紧但 breach 概率高
- Tools: Prometheus recording rules, Grafana SLO panel, custom EB tracker

**Framework 2**: Multi-window multi-burn-rate alert (Google SRE)
- When: catch fast burn + slow burn
- Algorithm: 1h@14x → critical / 6h@7x → critical / 1d@3x → warning / 3d@1x → warning; 1h 14x 意味 4 天烧光全月 budget
- Trade-off: 单 window 错过 slow burn 或 sudden burst
- Tools: Alertmanager multi-rule, Grafana SLO module, PrometheusRule with burn_rate expression

**Framework 3**: 3 isolation layers (gateway / app / physical)
- When: multi-tenant infra
- Algorithm: L1 Gateway (Envoy per-tenant token bucket by tier) / L2 App (per-tenant DB pool + memory + WFQ scheduler) / L3 Physical (Gold dedicated node pool, taint+toleration, autoscale 独立)
- Trade-off: 3 层完全 isolation 贵, 但 1 个 noisy 拖死全场代价更大
- Tools: Envoy / Kong, defaultdict(Semaphore), Kubernetes taint+toleration, separate autoscale group

**Framework 4**: Cardinality control 5 策略
- When: 10K+ tenant scale
- Algorithm: 1) label limit (max 10 per metric) / 2) per-tenant only top-N metrics / 3) top-100 tenant full, 长尾 aggregated bucket / 4) endpoint bucket (not raw URL) / 5) streaming aggregation (Flink 1-min pre-rollup)
- Trade-off: aggregated 失去细粒度 vs 系统能跑
- Tools: Prometheus relabeling, Mimir/Cortex, Flink 1-min window aggregator

**Framework 5**: Auto-credit on SLA breach
- When: SLA breach detected
- Algorithm: compute_credit (gap < 0.01% → 10% / < 0.1% → 25% / < 1% → 50% / > 1% → 100%); auto-issue credit note for next invoice; notify customer; record audit
- Trade-off: 主动 credit 关系好 vs 不主动客户来 ask 关系崩
- Tools: SLACreditEngine, billing DB separate, Stripe/Chargebee credit API

### 关键决策树 (ASCII)

```
Tier definition:
Gold:   99.99% / 200ms / dedicated / 10K QPS / 24x7 support / 100% telemetry
Silver: 99.9%  / 500ms / pooled priority A / 1K QPS / business hours / 50% telemetry
Bronze: 99%    / 1s    / pooled priority B / 100 QPS / email digest / 10% telemetry

Burn rate alert window:
1h burn rate 14x → critical page (4天烧光)
6h burn rate 7x  → critical
1d burn rate 3x  → warning (10天烧光)
3d burn rate 1x  → warning

Cardinality strategy:
< 1K tenant + < 1M ts → single Prometheus + recording rules
> 1K tenant → Mimir / Cortex (horizontal scale)
Large SaaS, $$ → Datadog (less ops, more $$$)

Storage tier:
Hot: raw 7d, 1-min rollups 30d (Postgres/Vertex AI Vector Search)
Warm: 1-min 30-90d in SSD (GCS Parquet)
Cold: 1-hour 1y, daily 3y+ (GCS Glacier)
Per-tier retention: Bronze 30d, Silver 90d, Gold 1y

Routing per severity:
P0 (Gold SLA) → PagerDuty 24x7
P1 (Silver / Gold non-SLA) → business hours
P2 (Bronze) → Slack
P3 (info) → daily digest
Dedup 1h per (tenant × metric)
```

### Part 2 五个深度问题速查

**Problem 1: SLI / SLO / SLA + Error Budget**
- 核心解法: SLI 测量 → SLO 内部 → SLA 合同; SLA < SLO 留 buffer; EB = (1-SLO)×total; multi-window burn (1h@14x / 6h@7x / 1d@3x / 3d@1x)
- Top 3 gotchas: SLA=SLO 没 buffer / 单 window 错过 slow burn / 月跨期 EB 重置规则
- Tools: Prometheus, Alertmanager, Grafana, custom EB tracker

**Problem 2: Per-tenant metrics + cardinality**
- 核心解法: 5 策略 (label limit / per-tenant top-N metric / 头长尾分 / endpoint bucket / streaming aggregation Flink); 10K tenant × 100 metric × 10 label = 10M ts 直接超 Prometheus 极限
- Top 3 gotchas: Sampling 不可用于 billing / Mimir/Cortex 必要 > 10M ts / endpoint raw URL 不可 bucket 必要
- Tools: Flink 1-min rollup, Mimir, Datadog SaaS (省运维但 $$$)

**Problem 3: Tier-based monitoring**
- 核心解法: tier 定义价格 + 资源 + 监控 + alert; physical for Gold (taint + toleration K8s node pool); WFQ for shared Silver/Bronze
- Top 3 gotchas: tier 物理 isolation 贵但 Gold 看 dedicated 心安 / 共享 pool 必有 priority class / per-tier threshold 不能 one-size-fits-all
- Tools: K8s node pool, Envoy per-tenant rate limit, defaultdict priority queue

**Problem 4: Alert routing per-tenant**
- 核心解法: 3 strategy (aggregate / per-tier / per-tenant); 4 severity (P0 page 24x7 / P1 page business / P2 slack / P3 digest); dedup 1h per (tenant × metric); quarterly precision review
- Top 3 gotchas: alert → #general no owner / 单 channel 全 fire / quarterly tune low-precision dead alerts
- Tools: PagerDuty + Opsgenie + Slack + Alertmanager routing rules

**Problem 5: Customer dashboard + auto-credit + billing audit**
- 核心解法: self-serve dashboard (uptime + EB remaining + incidents + usage + recommendations + bill estimate); auto-credit ladder (gap < 0.01% → 10%, < 0.1% → 25%, etc.); billing 独立 DB + WORM + HMAC-signed + 13mo retention; 60d dispute window
- Top 3 gotchas: telemetry + billing 同 DB → billing 受 retention 影响 / billing 永不 sample / dispute 必有 audit chain of custody
- Tools: Stripe/Chargebee credit API, statuspage.io, BigQuery 独立 billing dataset, HMAC sign

### Production gotchas (top 15)

1. Cardinality 失控 (10k × 100 × 10 = 10M ts)
2. Single shared infra for all tiers
3. 没 rate limit at gateway (app 层被打爆)
4. 没 quota per-tenant DB connections
5. Billing 跟 telemetry 同 DB
6. Aggregate at query time (slow + expensive)
7. 没 dispute window / audit (customer 怒)
8. Sampling for billing (不可接受)
9. SLA = SLO (no buffer)
10. Burn rate alert 单 window (错过 fast 或 slow)
11. Tier 不可升级 (客户成长无 path)
12. Bronze tenant 受 DDoS 没 protect
13. 没 hard ceiling within tier (Gold 也能爆)
14. Public status page 缺失 (客户 Twitter 发飙才知道)
15. Storage 一刀切 retention (Bronze 1y 浪费 / Gold 30d 不够)

### 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Per-tenant SLA tiers | Voice agent 7 markets | 不同 latency/accuracy SLA per market |
| Noisy neighbor isolation | Voice agent Indonesia payday 5x burst | Top-3 markets dedicated → 不影响 Thailand/Korea |
| Token bucket rate limit | API gateway 自然 per-market | Envoy per-market refill rate |
| Per-tenant dashboard | Regional ops weekly review | 自助看 SLO + usage + cost |
| Billing signal | ByteDance internal chargeback | per-region cost attribution |
| Cardinality control | Voice agent metric per market | top markets full, 长尾 aggregated |
| Burn rate alert multi-window | Voice agent 7 markets on-call | 1h / 6h / 1d / 3d for fast + slow burn |
| Auto-credit | Indonesia SLA breach commission adjust | 自动算 + 通知 |
| Tier upgrade path | Bronze → Silver 自助升级 | dashboard 内一键 |

### 面试现场 quotables (top 8)

1. "SLO > SLA — 留 20-50% buffer. Burn rate alert multi-window: 1h@14x / 6h@7x / 1d@3x / 3d@1x. Catches fast burn + slow burn."
2. "3 isolation layers: L1 Gateway per-tenant token bucket + L2 App per-tenant DB pool & WFQ + L3 Physical Gold dedicated node pool (K8s taint+toleration)."
3. "Cardinality control: top-100 tenant full per-tenant metric, 长尾 aggregated. Endpoint bucket (not raw URL). Streaming aggregation Flink 1-min pre-rollup. Mimir/Cortex when > 10M ts."
4. "Billing 独立 DB. Never sample for billing. WORM + HMAC-signed. 13 month retention. 60d dispute window with self-serve CSV export."
5. "Voice agent 7 markets — Indonesia payday 5x traffic burst. Because top-3 markets had dedicated inference replicas, Thailand/Korea/Vietnam unaffected. Tier-based isolation = insurance not luxury."
6. "Per-market burn rate multi-window caught a slow degradation in Vietnam gradient over 48h that would have missed aggregate alert."
7. "Auto-credit ladder on SLA breach: gap < 0.01% → 10% / < 0.1% → 25% / < 1% → 50% / > 1% → 100%. Notify customer + audit log."
8. "Gold tenant 20x spike: hard ceiling within tier + autoscale dedicated infra + customer-facing alert + bill overage 1.5x. Even Gold has ceiling."

### 红线 (top 10 anti-patterns)

1. Cardinality 失控 (10M+ ts no control)
2. Single shared infra for all tiers
3. No per-tenant rate limit at gateway
4. Sampling for billing
5. SLA = SLO (no buffer)
6. 单 window burn rate alert
7. Telemetry + billing 同 DB
8. No hard ceiling within tier
9. No dispute window / no audit chain
10. Public status page 缺失 (客户 Twitter 才知道)

### Tier definition (full table)

| Aspect | Bronze | Silver | Gold |
|---|---|---|---|
| Uptime SLA | 99% | 99.9% | 99.99% |
| Latency p99 | 1000 ms | 500 ms | 200 ms |
| Rate limit | 100 QPS | 1000 QPS | 10000 QPS |
| Burst | 200 QPS / 60s | 2000 QPS / 60s | 20000 QPS / 60s |
| Isolation | Pooled (priority B) | Pooled (priority A) | Dedicated K8s node pool |
| DB pool | 5 connections | 50 connections | 500 connections |
| Telemetry sample | 10% | 50% | 100% |
| Alert routing | Email daily digest | Slack business hours | PagerDuty 24x7 |
| Support response | 24h | 1h | 15 min |
| Storage retention | 30d | 90d | 1y |
| Credit ladder | 5/15/30/60 % | 10/25/50/100 % | 10/25/50/100 % |

### Multi-window burn rate alerts (Google SRE)

| Window | Burn rate threshold | Time to exhaust budget | Severity |
|---|---|---|---|
| 1 h | 14× | ~ 2 days | Critical (page 24x7) |
| 6 h | 7× | ~ 4 days | Critical |
| 1 d | 3× | ~ 10 days | Warning |
| 3 d | 1× | ~ 30 days (whole month) | Warning |

### Cardinality control 5 strategies

| Strategy | Implementation | Cardinality reduction |
|---|---|---|
| Label limit | Prometheus max_label_names_per_series = 10 | hard cap |
| Per-tenant only top-N metrics | PER_TENANT_METRICS list (billing + SLA only) | 10x |
| Head + tail bucket | Top-100 tenant full, 长尾 aggregated_small | 100x for long-tail |
| Endpoint bucket | /api/v1/agent/* → "agent" | 50x |
| Streaming aggregation | Flink 1-min rollup per tenant | 60x (raw event/min → 1/min) |

### Routing + severity matrix

| Tenant tier | Severity | Route | Escalation |
|---|---|---|---|
| Gold | P0 SLA breach | PagerDuty oncall + CSM | 15 min |
| Silver | P1 SLA breach | PagerDuty business hours | 1h |
| Bronze | P2 SLA breach | Slack #tenant-alerts | none |
| Gold | P1 non-SLA | Slack #gold-watch | none |
| Any | P3 info | Email daily digest | none |

### Auto-credit ladder (SLA breach)

| Uptime gap | Credit % |
|---|---|
| 0 - 0.01% (99.9 → 99.89%) | 10% |
| 0.01 - 0.1% | 25% |
| 0.1 - 1% | 50% |
| > 1% | 100% (基本免费一个月) |

### 工具栈

| Component | Tools |
|---|---|
| API Gateway | Envoy / Kong / Cloudflare Workers |
| Metric storage | Prometheus / Mimir / Cortex / Datadog (SaaS) |
| Visualization | Grafana / Datadog dashboard |
| Alert routing | Alertmanager / PagerDuty / Opsgenie |
| Streaming aggregation | Flink / Spark Streaming / Materialize |
| Time-series DB | ClickHouse / TimescaleDB / Druid |
| Status page | statuspage.io / Cachet self-hosted |
| Billing | Stripe / Chargebee / Metronome (usage-based) |

### 5 业务场景变体 (anchor stories)

| Variant | Tenant model | Key challenge |
|---|---|---|
| TikTok voice agent 7 markets | 7 markets = 7 tenants | Indonesia / Vietnam Gold, Thailand / Philippines Silver, SG / MY Bronze, Korea pilot |
| BNPL chatbot merchant tenants | 1000+ 商户, top 10% = 80% 流量 | Top 商户 dedicated LLM endpoint, 长尾 shared |
| Internal Agent Platform | ByteDance team-as-tenant | cost chargeback per team, internal SLA |
| ConvFinQA fair share | researcher-as-tenant | WFQ instead of tiered |
| Cloudflare-style 10K+ SaaS | 长尾极端 | top 1% = 50% resources, Bronze 80% tenant only 5% 流量 |

### Storage tier strategy

| Tier | Retention | Storage | Use |
|---|---|---|---|
| Hot | 7d raw + 30d 1-min rollups | Postgres / Vertex AI Vector Search | real-time query, alert |
| Warm | 30-90d 1-min in SSD | GCS Parquet | slow query 调查 |
| Cold | 1y 1-hour, 3y+ daily | GCS Glacier | compliance retention |
| Per-tier retention | Bronze 30d / Silver 90d / Gold 1y | varies | tier-scaled |

### Per-tier physical isolation (K8s)

| Tier | Isolation | Method |
|---|---|---|
| Gold | Dedicated node pool | K8s taint=tier:gold + toleration on Gold pods + nodeSelector |
| Silver | Pooled priority A | PriorityClass A + 80% slot quota |
| Bronze | Pooled priority B | PriorityClass B + 20% slot quota |
| All | Hard ceiling per tenant | even within tier, cap absolute QPS |

### Billing requirements (合规)

| Requirement | Implementation |
|---|---|
| Independent DB | NOT same as telemetry (retention 不同) |
| WORM (Write Once Read Many) | append-only table, no UPDATE/DELETE |
| HMAC-signed events | hmac_sign(event, BILLING_KEY) on insert |
| 13-month retention | 1y for audit + 1 month buffer |
| Self-serve report | CSV export from customer dashboard |
| Crypto-signed invoice | monthly invoice HMAC for tamper |
| Double-entry consistency | telemetry vs billing 可对账 |
| 60-day dispute window | customer 可 challenge billing line |

### Burn rate calculation example

| Window | Window error rate | SLO target | Burn rate | Threshold |
|---|---|---|---|---|
| 1h | 0.014 | 0.999 | 0.014 / 0.001 = 14× | critical |
| 6h | 0.007 | 0.999 | 7× | critical |
| 1d | 0.003 | 0.999 | 3× | warning |
| 3d | 0.001 | 0.999 | 1× | warning (sustained slow burn) |
