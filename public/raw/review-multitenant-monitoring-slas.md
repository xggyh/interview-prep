## Tech #5 · Multi-tenant SLA Monitoring — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/multitenant-monitoring-slas.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`multitenant-monitoring-slas.html`](questions/multitenant-monitoring-slas.html)

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
Hot: raw 7d, 1-min rollups 30d (Postgres/OpenSearch)
Warm: 1-min 30-90d in SSD (S3 Parquet)
Cold: 1-hour 1y, daily 3y+ (S3 Glacier)
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
| Hot | 7d raw + 30d 1-min rollups | Postgres / OpenSearch | real-time query, alert |
| Warm | 30-90d 1-min in SSD | S3 Parquet | slow query 调查 |
| Cold | 1y 1-hour, 3y+ daily | S3 Glacier | compliance retention |
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
