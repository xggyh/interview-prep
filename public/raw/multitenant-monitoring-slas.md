## 题目（verbatim）

> "Design **multi-tenant SaaS monitoring** with **varying client SLA requirements**. Per-tenant quotas, noisy-neighbor isolation, billable signal aggregation."

**出处**: fde.academy 技术 round. Databricks / BigQuery / Datadog / Cloudflare 都问过.

**Round**: Technical Integration (45-60 min)

---

## 这道题在考什么

考你做过 **multi-tenant SaaS infrastructure** 的真实痛点:

1. **SLA / SLO / SLI 区分得清吗** — Error budget 怎么算
2. **Per-tenant metrics 怎么不爆 cardinality** — 这是 monitoring 真正的难题
3. **Tier-based 怎么 enforce** — Gold vs Bronze 怎么物理 / 逻辑区分
4. **Alert routing per-tenant** — 不能所有 tenant 一个 channel
5. **Customer-facing dashboard + credit** — SLA breach 要 compensate
6. **熟不熟工具** — Prometheus / Mimir / Datadog / Grafana / Cortex / Thanos

考的不是 "你知道 P99", 是 "你跑过 10k+ tenant 的 SaaS, 处理过 noisy neighbor 和 cardinality 爆炸".

---

# 这道题在考什么

考你做过 **multi-tenant SaaS infrastructure**:

1. **不同 SLA tier 怎么 enforce** — Bronze vs Gold 怎么物理 / 逻辑区分
2. **Noisy neighbor isolation** — 大客户不能影响小客户
3. **Cardinality 爆炸** — 10k tenant × 100 metric × 10 label = 10M time series
4. **Billable signal aggregation** — 哪些 metric 算 billable, 怎么 audit
5. **Customer-facing SLA dashboard** — 客户能自助看, 出问题能 credit

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**Multi-tenant SaaS**: 一套**软件 + 基础设施**, 同时服务多个**租户** (tenant). 每个租户 (一家企业客户) 看到的像是独享, 实际上多个租户共享物理资源 (pooled) 或部分专用 (siloed) 或混合 (hybrid). 你做的 voice agent 7 markets 就是天然的 multi-tenant — 每个 market 一个 tenant.

**SLA / SLO / SLI**: 三个术语 SRE 圈天天用, 经常混:

- **SLI** (Service Level **Indicator**): **一个可测量的数字**. 例如: 过去 5 分钟的 successful_requests / total_requests. 是事实.
- **SLO** (Service Level **Objective**): **内部目标**. 例如: 99.9% requests succeed. 是 aspirational target, 团队的承诺.
- **SLA** (Service Level **Agreement**): **合同条款**. 例如: 我们保证 99.5% uptime, 不满足赔 10% 月费. 是法律约束, 跟客户签的.

公式: `SLA < SLO`. 内部目标永远比对客户的承诺更严格, 留 buffer.

**Error budget** (错误预算): `1 - SLO`. 比如 SLO 99.9% 意味着每月可以有 0.1% × 30d = 43 分钟 unavailable. 这 43 分钟是你的「预算」, 用完了, 就 freeze release, 优先稳定性.

**Cardinality** (基数): 一个 metric 的 label 组合总数. 例如 `http_requests_total{tenant_id, endpoint, status_code, region}`, 1000 tenant × 50 endpoint × 5 status × 5 region = 1.25M unique time series. **这是 multi-tenant monitoring 的头号杀手**.

**Noisy neighbor**: 一个 tenant 异常行为 (流量飙升 / 大查询 / 死循环) 把共享资源吃光, 影响其他 tenant. SaaS 经典问题.

---

## 2. 这个问题的核心是什么

设想一个**没 isolation / 没 per-tenant quota / 没 cardinality control** 的 SaaS 灾难:

```
2026-05-21 03:00  Bronze tier 客户 acme-corp 部署了一个 buggy script
                  对你的 API 每秒发 50k 请求 (正常 100 QPS)
                  
03:01  你的 API gateway 没 per-tenant rate limit, 全部通过
03:02  Database connection pool 被 acme 吃满 (500 conn)
03:03  Gold tier 客户 bigcorp 的关键报表 query 等不到 conn, 超时
03:05  Bigcorp CEO 在 Twitter 发: "your SaaS is down, terrible service"
03:10  你的 PagerDuty 一片红, 但你看 monitoring "CPU 60%, 一切正常"
       (因为 monitoring metric 没 per-tenant breakdown, aggregate 看不到 acme spike)
03:30  你手忙脚乱猜原因, 期间所有 tenant 都受影响
04:00  你终于发现是 acme, 手动 ban 它 IP
04:30  恢复. Bigcorp 取消合同. SLA 赔付一个月免单
```

**问题**:

- 没 per-tenant rate limit → 1 个 noisy tenant 拖垮全场
- 没 per-tenant metric → 看不到谁是元凶
- 没 tiered isolation → Gold 客户和 Bronze 共享同一资源池
- 没 SLA dashboard → 客户在 Twitter 发飙才知道
- 没 auto-credit → 客户人工要 compensation, 关系崩

**Production-grade 解法**:

```
1. API Gateway: per-tenant token bucket (按 tier QPS)
2. App layer: per-tenant DB pool, memory quota, WFQ scheduler
3. Physical: Gold tenant 走 dedicated replica
4. Monitoring: per-tenant SLI, 但用 streaming aggregation 避免 cardinality 爆
5. Alert: per-tenant routing, by severity tier
6. Customer dashboard: 自助看 SLO compliance + error budget
7. Auto-credit: SLA breach 自动 trigger compensation
```

---

## 3. 典型架构图

```
                      ┌───────────────────────────┐
                      │   Tenant Onboarding       │
                      │  (tier, quota config)     │
                      └─────────┬─────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────┐
│  API Gateway (Envoy / Kong)                                  │
│    L1: Per-tenant token bucket rate limit (by tier)          │
│    Authentication, tenant_id 注入 trace                       │
└─────────────────┬───────────────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Application Layer                                           │
│    L2: Per-tenant DB pool, memory quota, WFQ scheduler       │
│    Tier-aware request routing:                               │
│      Gold tenants  → dedicated replica set                   │
│      Silver/Bronze → pooled replica set                      │
└─────────────────┬───────────────────────────────────────────┘
                  ▼
        Telemetry emit per request:
          tenant_id, tier, endpoint, status, latency_ms, ...
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Telemetry Pipeline                                          │
│    Kafka (partition by tenant_id)                            │
│    Flink: 1-min rollups per tenant per metric                │
│    Sampling (head + tail biased for slow)                    │
└─────────────────┬───────────────────────────────────────────┘
                  ▼
        ┌─────────────────────────────┐
        │ TSDB / Mimir / Datadog      │
        │  Hot:  1-min rollups, 30d   │
        │  Warm: 1-hour rollups, 1y   │
        │  Cold: 1-day rollups, 3y+   │
        └─────────┬───────────────────┘
                  ▼
        ┌────────────────────────────────────────────────┐
        │  Per-tenant Dashboard + SLA Computer            │
        │  Auto-credit Logic                              │
        │  Alert Routing (PagerDuty / Slack)              │
        │  Billing System (separate DB!)                  │
        └─────────────────────────────────────────────────┘
```

---

## 4. SLI / SLO / SLA / Error Budget 关系表

| 概念 | 是什么 | 例子 (voice agent) | 谁负责 |
|---|---|---|---|
| **SLI** | 一个测量值 | "过去 5 min 通话成功率" | 系统 自动算 |
| **SLO** | 内部目标 | "99.9% calls succeed" | SRE / Eng owner |
| **SLA** | 对客户的承诺 | "99.5% uptime, 不达赔 10%" | 销售 / Legal |
| **Error budget** | 允许失败的额度 | 99.9% SLO → 43 min/月可用 | 共同 |
| **Burn rate** | 当前消耗 EB 的速率 | 1h 内消耗 10% EB = 10x burn | Alert |

**经验**:

- SLO 永远比 SLA 严 (留 20-50% buffer)
- Error budget 跑完 → freeze release, 直到下个 window
- Burn rate alert 比 SLO breach alert 更 actionable (前者预防, 后者已经晚了)

---

## 5. 具体业务场景

### 场景 A: 你的 TikTok Voice Agent 7 markets (你工作背景)

**7 markets = 7 tenants**, 不同 SLA:

| Market | Tier | SLA (uptime) | Latency p99 SLO | Daily call volume |
|---|---|---|---|---|
| Indonesia | Gold (high revenue) | 99.95% | 200ms | 500k |
| Vietnam | Gold | 99.95% | 200ms | 300k |
| Thailand | Silver | 99.9% | 250ms | 100k |
| Philippines | Silver | 99.9% | 250ms | 80k |
| Singapore | Bronze (small market) | 99.5% | 500ms | 10k |
| Malaysia | Bronze | 99.5% | 500ms | 8k |
| Korea | Pilot | best-effort | best-effort | 1k |

**Noisy neighbor 真实事故**:

- 印尼发薪日 (15 号), 流量 burst 5x
- 印尼用 dedicated inference replica → 不影响其他 market
- 如果共享, 越南 Gold 客户也会受影响

### 场景 B: BNPL Chatbot — 商户租户

- 每个接入的电商商户 = 1 tenant
- Top 10% 商户占 80% 流量 (长尾)
- Gold 商户 (年 GMV > 10M USD): 独享 LLM endpoint, 99.99% SLA
- Silver / Bronze 共享 LLM endpoint, 99.9% / 99% SLA
- Cardinality: 1000 tenant × 20 endpoint × 5 region = 100k time series

### 场景 C: Internal Agent Platform — Team 当 tenant

- ByteDance 内部多个 team 用你的 Agent Platform
- 每个 team = 1 tenant
- 内部 SLA 不那么严, 但 cost attribution 必须准 (chargeback)
- Billing 维度: tokens consumed, GPU-hours, storage GB-hours

### 场景 D: ConvFinQA 内部用户

- 每个 researcher = 1 tenant
- "Fair share" 而不是 tiered: 没人付费, 大家公平
- WFQ (Weighted Fair Queueing) 保证小用户不被大 batch 用户饿死

### 场景 E: Cloudflare / Datadog 这种纯 SaaS

- 10万+ tenant, 长尾极端
- 头部 1% tenant 占 50% 资源
- Bronze 占 80% tenant 但只 5% 流量
- Cardinality 是头号挑战 — 不能为所有 tenant 维护所有 metric

---

## 6. 工程上要做什么 — 实现 checklist

**Stage 0: Tier Definition (Week 1)**

1. 定义 3 个 tier: Bronze / Silver / Gold (or 4 with Platinum)
2. 每个 tier 写清:
   - Promised uptime SLA
   - Promised latency p99
   - Rate limit (QPS)
   - Throughput cap (req/day)
   - Isolation level (pooled / dedicated)
   - Support response time
3. 价格分级, tier 升级 path 清晰

**Stage 1: Isolation (Week 2-4)**

4. **L1 API Gateway**: token bucket per tenant, configurable by tier
5. **L2 App layer**: per-tenant DB connection pool, query timeout, memory quota
6. **L3 Physical**: Gold tenants 独立 replica set (Kubernetes node taint + tolerations)
7. WFQ scheduler 对 background job (避免 1 tenant 占满 worker pool)

**Stage 2: Telemetry (Week 4-6)**

8. 每个 request emit metric: tenant_id, tier, endpoint, status, latency_ms
9. Cardinality control: per-tenant only top-N important metrics, rest aggregated
10. Streaming aggregation (Flink / Spark Streaming): 1-min rollup per tenant
11. Storage tier: hot 30d, warm 1y, cold 3y+ (different retention by tier)

**Stage 3: SLO Computation + Alert (Week 6-8)**

12. SLI calc per 5-min sliding window per tenant
13. Error budget tracker: monthly rolling, 30-day window
14. Burn rate alert: 多 fast / multi-window (e.g., 1h burn at 10x = page, 6h at 5x = page)
15. Per-tenant alert routing (PagerDuty per-tenant integration / Slack channel)

**Stage 4: Customer-facing + Billing (Week 8-10)**

16. Customer self-serve dashboard: SLO compliance, error budget remaining, recent incidents
17. SLA credit auto-calculation: breach → automatic credit on next invoice
18. Billing system (separate DB!): metered usage, audit trail 13 months
19. Dispute window (60 days), self-serve usage report (CSV export)

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **Cardinality 爆炸** | 10k tenant × 100 metric × 10 label = 10M ts → Prometheus 内存爆 |
| 2 | **Single shared infra for all tiers** | 1 tenant 影响所有 |
| 3 | **没 rate limit at gateway** | App 层被打爆 |
| 4 | **Billing 跟 telemetry 同 DB** | Billing 受 telemetry retention 影响, 不能 audit |
| 5 | **Aggregate at query time** | 慢 + 贵 |
| 6 | **没 dispute window** | Billing 不可挑战, customer 怒 |
| 7 | **Sampling for billing** | 计费数据**绝不能** sample |
| 8 | **没 per-tenant DB pool** | 1 tenant 拿光 conn, 全员 stall |
| 9 | **SLA = SLO** | 没 buffer, breach 概率高 |
| 10 | **Burn rate alert 单 window** | 要 multi-window (fast + slow) |
| 11 | **Tier 不可升级** | 客户成长后没自助 path |
| 12 | **Bronze tenant 受 DDoS** | 没 anomaly detection / 自动 throttle |

---

## 一句话总结 (Part 1)

> **Multi-tenant SaaS monitoring + SLA = "3 层 isolation (gateway / app / physical) + per-tenant SLI 但控 cardinality + tier-based threshold + 自助 dashboard + 自动 credit + 严格 billing audit"**.
>
> 这道题考的不是 "你会用 Prometheus", 是 "你跑过 10k+ tenant 的 SaaS, 处理过 noisy neighbor + cardinality 爆炸".

---

# Part 2 · 5 个深度工程问题

## ⚙️ Problem 1: SLA / SLO / SLI Taxonomy + Error Budget

### 1.1 区分三者

```python
# SLI (Service Level Indicator) — 一个数字
def compute_availability_sli(window_sec=300):
    """5 分钟滑动窗口的可用性."""
    total = metric_store.sum('requests_total', last_seconds=window_sec)
    failed = metric_store.sum('requests_failed', last_seconds=window_sec)
    return (total - failed) / total if total > 0 else 1.0

# SLO (Service Level Objective) — 目标
class SLO:
    name = "api_availability"
    target = 0.999  # 99.9%
    window = "30d_rolling"

    def check(self):
        sli = compute_availability_sli()
        return sli >= self.target

# SLA (Service Level Agreement) — 法律
class SLA:
    name = "Gold tier api_availability"
    target = 0.995  # 99.5% (lower than SLO! 留 buffer)
    breach_credit_pct = 10  # 不达成 → 10% 月费 credit
```

### 1.2 Error Budget 计算

```python
class ErrorBudget:
    """
    Error budget = (1 - SLO target) × total_requests_in_window.
    """
    def __init__(self, slo_target=0.999, window_days=30):
        self.target = slo_target
        self.window_days = window_days

    def total_budget(self, tenant_id):
        total = metric_store.sum(
            'requests_total',
            tenant_id=tenant_id,
            last_days=self.window_days,
        )
        return total * (1 - self.target)

    def consumed(self, tenant_id):
        return metric_store.sum(
            'requests_failed',
            tenant_id=tenant_id,
            last_days=self.window_days,
        )

    def remaining(self, tenant_id):
        return self.total_budget(tenant_id) - self.consumed(tenant_id)

    def remaining_pct(self, tenant_id):
        total = self.total_budget(tenant_id)
        if total == 0:
            return 1.0
        return self.remaining(tenant_id) / total
```

### 1.3 Burn Rate Alerts (Multi-window Multi-burn-rate)

**Google SRE book** 推荐的多窗口多 burn rate alert:

```python
# 防止 fast burn (灾难) + slow burn (温水煮青蛙) 都能 catch
BURN_RATE_ALERTS = [
    # (window, burn_rate_threshold, severity)
    ('1h',  14,  'critical'),  # 1h 烧光全月 budget 的 1/14 → critical
    ('6h',  7,   'critical'),  # 6h 烧光全月 budget 的 1/7  → critical
    ('1d',  3,   'warning'),   # 24h 烧光全月 budget 的 1/3 → warning
    ('3d',  1,   'warning'),   # 3d 烧光所有 budget → warning
]

def check_burn_rate(tenant_id, slo):
    alerts = []
    for window, threshold, sev in BURN_RATE_ALERTS:
        sli_in_window = compute_availability_sli_for_window(tenant_id, window)
        error_rate = 1 - sli_in_window
        budget_burn_rate = error_rate / (1 - slo.target)
        if budget_burn_rate > threshold:
            alerts.append({
                'window': window,
                'burn_rate': budget_burn_rate,
                'severity': sev,
            })
    return alerts
```

**关键直觉**:

- 1h 内消耗 10x 预期 burn → 这速度 4 天烧光全月 → critical
- 1d 内消耗 3x → 10 天烧光 → warning
- 多窗口配合: 短窗口 catch sudden, 长窗口 catch gradual

### 1.4 Per-Tier SLO

```python
TIER_SLOS = {
    'gold': {
        'availability': 0.9999,  # 99.99%
        'latency_p99_ms': 200,
        'sla_promise': 0.999,    # 比 SLO 低 0.09%
    },
    'silver': {
        'availability': 0.999,
        'latency_p99_ms': 500,
        'sla_promise': 0.995,
    },
    'bronze': {
        'availability': 0.99,
        'latency_p99_ms': 1000,
        'sla_promise': 0.97,
    },
}
```

---

## ⚙️ Problem 2: Per-Tenant Metrics — Cardinality Explosion

**这是 multi-tenant monitoring 的核心难题**. 不解决直接死.

### 2.1 Cardinality 数学

```
Naive 设计:
  Metric: http_requests_total
  Labels: tenant_id, endpoint, status_code, region, method, version
  
  10,000 tenants × 50 endpoints × 5 status × 5 region × 6 method × 3 version
  = 22,500,000 unique time series

Prometheus 内存: 每个 ts ~3 KB
  → 22.5M × 3 KB = 67.5 GB 内存
  → 一个 Prometheus 进程承受不住 (典型 10M ts 极限)
```

### 2.2 Cardinality Control 策略

#### (a) Label Limit (硬性)

```python
# Prometheus / Mimir / Datadog 都有这种限制
# 配置: max_label_names_per_series = 10
#       max_label_value_length = 256
```

#### (b) 重要 Metric Only Per-tenant

```python
# 不是所有 metric 都 per-tenant
PER_TENANT_METRICS = [
    'http_requests_total',  # 计费用
    'http_request_duration_seconds',  # SLA 用
    'http_requests_failed_total',  # SLO 用
]

# 其他 metric (内部 debug 类) — 不带 tenant_id
INTERNAL_METRICS = [
    'gc_duration_seconds',
    'goroutines_count',
    'db_connection_pool_size',
]
```

#### (c) 头部 vs 长尾 — 不同 strategy

```python
# 头部 100 tenant: 全量 per-tenant metric
# 长尾 9900 tenant: 聚合成 "small_tenant" bucket
def tag_tenant_for_metric(tenant_id):
    if tenant_id in TOP_100_TENANTS:
        return tenant_id
    return 'aggregated_small'
```

#### (d) Endpoint Bucket

```python
# 50 endpoint 直接用很 high cardinality, 用 bucket
def bucket_endpoint(endpoint):
    if endpoint.startswith('/api/v1/agent'):
        return 'agent'
    if endpoint.startswith('/api/v1/billing'):
        return 'billing'
    if endpoint.startswith('/api/v1/admin'):
        return 'admin'
    return 'other'
```

#### (e) Streaming Aggregation (Flink / Spark)

```python
# 不直接 push raw event 到 Prometheus
# 用 Flink 流式聚合, 输出 pre-aggregated metric

# Pseudocode for Flink job
stream
    .keyBy(event -> event.tenant_id + ":" + event.endpoint_bucket)
    .window(TumblingProcessingTimeWindows.of(Time.minutes(1)))
    .aggregate(new RequestAggregator())
    .map(agg -> Metric.builder()
        .name("http_requests_per_minute")
        .label("tenant_id", agg.tenant)
        .label("endpoint_bucket", agg.bucket)
        .value(agg.count)
        .build())
    .addSink(prometheusSink)
```

**结果**: 10M raw event/min → 50k aggregated metric/min, cardinality 可控.

### 2.3 Sampling for Non-billable

```python
# 计费 metric (api_calls_total) — **100% 不能 sample**
# Debug metric (db_query_duration) — 1/100 sampling OK

class SamplingStrategy:
    BILLABLE_METRICS = {'api_calls_total', 'compute_seconds_total', 'storage_gb_hours'}

    def should_record(self, metric_name):
        if metric_name in self.BILLABLE_METRICS:
            return True  # 永远 record
        return random.random() < 0.01  # 1% sample
```

### 2.4 Mimir / Cortex / Thanos (Prometheus 横向扩展)

```
Single Prometheus:    上限 ~10M ts, ~500K samples/sec
                      ↓
Mimir / Cortex:       horizontally scalable, 跨多 instance
                      支持 multi-tenant 隔离 (per-tenant retention, RBAC)
                      cost: 比 Datadog 便宜很多 (self-host)

Datadog (SaaS):       cardinality $-cost, $0.05/host/hr + per-metric pricing
                      cardinality 失控 = bill 失控
```

**选型**:

- < 1000 tenant, < 1M ts → single Prometheus + recording rules
- > 1000 tenant → Mimir / Cortex
- 大型 SaaS, 钱多 → Datadog (省运维)

---

## ⚙️ Problem 3: Tier-Based Monitoring (Gold / Silver / Bronze)

### 3.1 Tier 定义 — 不只是价格, 是**资源 + 监控 + alert**

```yaml
tiers:
  gold:
    isolation: dedicated_replica
    rate_limit: 10000 qps
    burst: 20000 qps for 60s
    db_pool: 500 connections
    sla_uptime: 0.9995
    sla_latency_p99_ms: 200
    monitor_sample_rate: 1.0   # 100% telemetry
    alert_routing: pagerduty_oncall_24x7
    support_response: 15min
    storage_retention: 1y_hot

  silver:
    isolation: pooled (priority class A)
    rate_limit: 1000 qps
    burst: 2000 qps for 60s
    db_pool: 50 connections
    sla_uptime: 0.999
    sla_latency_p99_ms: 500
    monitor_sample_rate: 0.5   # 50% telemetry
    alert_routing: slack_business_hours
    support_response: 1h
    storage_retention: 90d_warm

  bronze:
    isolation: pooled (priority class B)
    rate_limit: 100 qps
    burst: 200 qps for 60s
    db_pool: 5 connections
    sla_uptime: 0.99
    sla_latency_p99_ms: 1000
    monitor_sample_rate: 0.1   # 10% telemetry
    alert_routing: email_daily_digest
    support_response: 24h
    storage_retention: 30d_cold
```

### 3.2 Physical Isolation for Gold

```python
# Kubernetes: Gold pods 走专用 node pool
# 用 taints + tolerations 强制隔离

# Node pool config (Terraform / GKE)
resource "google_container_node_pool" "gold" {
  name       = "gold-tier-pool"
  node_count = 5

  node_config {
    taint {
      key    = "tier"
      value  = "gold"
      effect = "NO_SCHEDULE"
    }
    labels = {
      tier = "gold"
    }
  }
}

# Pod spec
spec:
  tolerations:
  - key: "tier"
    operator: "Equal"
    value: "gold"
    effect: "NoSchedule"
  nodeSelector:
    tier: "gold"
```

**好处**:

- Gold 流量永远不和 Bronze 共享 node
- Gold 可以用更好的硬件 (GPU / 高 IO)
- Auto-scale Gold pool 独立, 不被 Bronze 流量 burst 影响

### 3.3 Pooled with Priority Class

Silver / Bronze 共享 pool, 但有优先级:

```python
class PriorityScheduler:
    """Silver 优先于 Bronze 在 pooled infra."""

    def __init__(self):
        self.queues = {
            'silver': PriorityQueue(),
            'bronze': PriorityQueue(),
        }

    def enqueue(self, request):
        tier = get_tenant_tier(request.tenant_id)
        self.queues[tier].put(request)

    def dequeue(self):
        # WFQ: Silver 80% slot, Bronze 20%
        if random.random() < 0.8 and not self.queues['silver'].empty():
            return self.queues['silver'].get()
        if not self.queues['bronze'].empty():
            return self.queues['bronze'].get()
        return self.queues['silver'].get()  # fallback
```

### 3.4 Per-Tier Threshold

```python
# 同一 metric 不同 tier 不同 threshold
LATENCY_P99_THRESHOLD = {
    'gold': 200,    # ms
    'silver': 500,
    'bronze': 1000,
}

def check_latency_slo(tenant_id):
    tier = get_tenant_tier(tenant_id)
    p99 = metric_store.percentile(99, 'latency_ms', tenant_id=tenant_id)
    threshold = LATENCY_P99_THRESHOLD[tier]
    if p99 > threshold:
        alert(f"Tenant {tenant_id} ({tier}) p99 {p99}ms > threshold {threshold}ms")
```

---

## ⚙️ Problem 4: Alerting — Per-Tenant vs Aggregate, Routing, Severity

### 4.1 Three Alert Strategies

```
1. Aggregate alerts (整体异常):
   "P99 latency on all api endpoints > 1s"
   → SRE on-call

2. Per-tier alerts (某 tier 整体异常):
   "Gold tier error rate > 0.1%"
   → SRE + Gold customer success team

3. Per-tenant alerts (具体 tenant):
   "Tenant acme-corp error rate > 5%"
   → tenant's account manager + tech lead
```

### 4.2 Severity Tier

```python
class AlertSeverity:
    P0 = 'critical'      # page 24x7
    P1 = 'high'          # page business hours
    P2 = 'medium'        # slack
    P3 = 'low'           # email daily digest

def determine_severity(alert):
    tier = alert.tenant_tier
    metric = alert.metric

    # Gold tenant: 任何 SLA breach 都 P0
    if tier == 'gold' and metric in SLA_METRICS:
        return AlertSeverity.P0

    # Silver: SLA breach P1, internal P2
    if tier == 'silver':
        return AlertSeverity.P1 if metric in SLA_METRICS else AlertSeverity.P2

    # Bronze: 基本不 page
    if tier == 'bronze':
        return AlertSeverity.P2 if metric in SLA_METRICS else AlertSeverity.P3

    return AlertSeverity.P2
```

### 4.3 Routing Rules

```yaml
routing_rules:
  - match: {severity: P0, tier: gold}
    route: pagerduty/oncall_engineer + pagerduty/gold_csm
    escalate_after: 15min

  - match: {severity: P1, tier: silver}
    route: pagerduty/oncall_engineer (business hours only)
    escalate_after: 1h
    fallback_route: slack/#silver-incidents

  - match: {severity: P2}
    route: slack/#tenant-alerts
    
  - match: {severity: P3}
    route: email/daily-digest@example.com
```

### 4.4 Dedup + Suppression

```python
class TenantAlertManager:
    """
    Per-tenant 范围内 dedup.
    同一 tenant + 同一 metric + 1h 窗口只 fire 一次.
    """
    def __init__(self):
        self.recent = {}  # (tenant_id, metric) → last_fire_ts

    def fire_or_suppress(self, alert):
        key = (alert.tenant_id, alert.metric_name)
        last = self.recent.get(key, 0)
        if time.time() - last < 3600:
            # 1h dedup window, 累计 count
            self._increment_count(key)
            return False
        self.recent[key] = time.time()
        return True
```

### 4.5 Alert Quality — Quarterly Tune

```python
# 看每个 alert 类型的 actionability
def alert_quality_report(quarter):
    report = {}
    for alert_type in alert_types:
        ats = db.get_alerts(quarter, type=alert_type)
        resolved_real = sum(1 for a in ats if a.outcome == 'real_issue_fixed')
        false_positive = sum(1 for a in ats if a.outcome == 'auto_resolved')
        precision = resolved_real / len(ats) if ats else 0
        report[alert_type] = {
            'fired_count': len(ats),
            'precision': precision,
            'avg_mttr_min': sum(a.mttr_min for a in ats) / len(ats),
        }
    return report
```

---

## ⚙️ Problem 5: Customer-Facing SLA Dashboard + Credit Logic

### 5.1 Customer Self-serve Dashboard

```python
class CustomerDashboard:
    """每个客户能看自己的 SLA / 用量."""

    def render(self, tenant_id):
        return {
            'current_month': {
                'uptime': self.compute_uptime(tenant_id, 'this_month'),
                'sla_target': self.get_sla(tenant_id).uptime,
                'sla_met': self.compute_uptime(tenant_id, 'this_month') >= self.get_sla(tenant_id).uptime,
                'error_budget_remaining_pct': self.error_budget(tenant_id).remaining_pct(),
                'incidents': self.list_incidents(tenant_id, 'this_month'),
            },
            'usage': {
                'api_calls': self.usage_count(tenant_id, 'api_calls'),
                'compute_seconds': self.usage_count(tenant_id, 'compute_seconds'),
                'storage_gb_hours': self.usage_count(tenant_id, 'storage_gb_hours'),
                'rate_limit_hits': self.count_429s(tenant_id),
            },
            'recommendations': self.recommendations(tenant_id),  # tier upgrade等
            'next_invoice_estimate': self.estimate_bill(tenant_id),
        }
```

### 5.2 Auto-credit on SLA Breach

```python
class SLACreditEngine:
    """SLA breach → 自动算 credit."""

    def __init__(self, db):
        self.db = db

    def compute_credit(self, tenant_id, month):
        sla = self.db.get_sla(tenant_id)
        actual_uptime = self.compute_uptime(tenant_id, month)

        if actual_uptime >= sla.uptime:
            return 0  # 没 breach, 没 credit

        # 标准 credit ladder (典型 SaaS)
        gap = sla.uptime - actual_uptime
        if gap < 0.0001:    # 99.9% → 99.89%
            credit_pct = 0.10  # 10% off
        elif gap < 0.001:   # 99.9% → 99.8%
            credit_pct = 0.25
        elif gap < 0.01:    # 99.9% → 98.9%
            credit_pct = 0.50
        else:
            credit_pct = 1.0   # 100% credit (基本免费)

        monthly_bill = self.estimate_bill(tenant_id, month)
        return monthly_bill * credit_pct

    def issue_credit(self, tenant_id, month):
        credit = self.compute_credit(tenant_id, month)
        if credit > 0:
            self.db.create_credit_note(
                tenant_id=tenant_id,
                amount=credit,
                reason=f"SLA breach in {month}",
                applies_to_invoice='next',
            )
            self.notify_customer(tenant_id, credit)
```

### 5.3 Billing Audit Trail

**Billing 必须独立 DB, 高 retention, 不可改**:

```python
class BillingDB:
    """
    Billing 存储要求:
      1. 独立于 telemetry DB (telemetry 7d 保留, billing 13 months)
      2. 不能 sample (every event recorded)
      3. 写入后不可修改 (append-only / WORM)
      4. 加密 + 签名 (防篡改)
      5. 跟 telemetry double-entry bookkeeping (可对账)
    """

    def record_billable_event(self, event):
        # 写入前 sign
        event.signature = hmac_sign(event, secret=BILLING_KEY)
        # WORM table
        self.db.insert_immutable('billable_events', event)
        # 审计 log
        audit.log({
            'action': 'billable_event_recorded',
            'event_id': event.id,
            'tenant_id': event.tenant_id,
            'amount': event.amount,
            'ts': now(),
        })
```

### 5.4 Dispute Window + Self-serve Report

```python
def export_usage_report(tenant_id, start_date, end_date, format='csv'):
    """客户自助导出 usage report 用于对账."""
    events = billing_db.query(
        tenant_id=tenant_id,
        start=start_date,
        end=end_date,
    )
    if format == 'csv':
        return to_csv(events, columns=['ts', 'event_id', 'metric', 'value', 'request_id'])
    if format == 'json':
        return to_json(events)

def file_dispute(tenant_id, invoice_id, reason, evidence):
    """客户提 dispute (60d window)."""
    invoice = db.get_invoice(invoice_id)
    if (now() - invoice.issued_at).days > 60:
        return {'error': 'Outside 60-day dispute window'}

    db.create_dispute(
        tenant_id=tenant_id,
        invoice_id=invoice_id,
        reason=reason,
        evidence=evidence,
        status='pending_review',
    )
    notify_billing_team(invoice_id)
    return {'ok': True, 'dispute_id': ...}
```

### 5.5 Public Status Page

```python
# 跟客户透明 — 比客户先发现自己的 incident
# 用 statuspage.io / 自建

@app.route('/status')
def public_status():
    return {
        'overall': overall_health(),
        'services': {
            'api': service_health('api'),
            'inference': service_health('inference'),
            'webhooks': service_health('webhooks'),
        },
        'incidents': list_active_incidents(),
        'recent_incidents': list_incidents(last_days=30),
        'sla_history': sla_compliance_history(months=12),
    }
```

---

# Part 3 · 把 5 个问题串起来看

这 5 个问题是**同一件事的不同 layer**:

1. **SLI / SLO / SLA / Error Budget** = 「**度量框架**」 — 你怎么定义"好坏"
2. **Per-tenant metrics + cardinality control** = 「**测量工具**」 — 你怎么测出 1 万 tenant 的"好坏"
3. **Tier-based isolation** = 「**资源分配**」 — 你怎么让不同 tier 的"好坏"目标可达
4. **Alert routing + severity** = 「**信号过滤**」 — 测出 "坏" 时怎么找对人
5. **Customer-facing + credit** = 「**对客户兑现**」 — 真的 "坏" 时怎么 honor 承诺

面试场或架构评审上, 能从这 5 层系统讲清楚, 就是**做过大型 SaaS infra 的水准**. 如果只会答 "我用 Prometheus + Grafana", 那是初级.

---

## 必问 clarifying questions

**1. SLA tiers**

> "How many tiers — Bronze/Silver/Gold? What does each promise (availability %, latency p99, throughput, support response)?"

**2. Tenant count + size distribution**

> "100 tenants or 100k? Long-tail (5 huge, many tiny) or evenly distributed? Top 10% = X% traffic?"

**3. Multi-tenancy model**

> "Pooled (shared infra) or siloed (dedicated)? Hybrid common — small tenants share, large dedicated? Acceptable cross-tier bleed?"

**4. Billing granularity**

> "Per-API-call billing? Per-resource-hour? Tiered subscription with overage? Determines whether sampling is OK."

**5. Existing observability**

> "Are we building on Datadog / Prometheus + Grafana / Mimir? Or greenfield? Cost ceiling for telemetry?"

**6. Customer expectations**

> "Do customers expect self-serve dashboard + credit auto-issue? Or manual ticket-based? Determines product surface."

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify tier model + size dist + existing tools |
| 5-15 min | SLI/SLO/SLA + error budget + burn rate alerting |
| 15-25 min | Per-tenant metrics + cardinality control + storage tiers |
| 25-35 min | Tier-based isolation (gateway + app + physical) |
| 35-45 min | Alert routing + per-tier severity + dedup |
| 45-55 min | Customer dashboard + credit logic + billing audit |
| 55-60 min | Failure modes + onboarding + cost optimization |

---

## 简历专属 reframe

你的 **voice agent 7 markets** + **BNPL chatbot multi-tenant** 都是天然 SaaS:

| 题 | 你的经验 |
|---|---|
| Per-tenant SLA tiers | 7 markets 不同 latency / accuracy SLA |
| Noisy neighbor isolation | Indonesia payday burst 不影响 Thailand |
| Token bucket rate limit | API gateway 自然有 |
| Per-tenant dashboard | 你 weekly 跟 regional ops review |
| Billing signal | ByteDance 内部 chargeback 按 region |
| Cardinality control | Voice agent metric per market — top markets full, long-tail aggregate |
| Burn rate alert | Voice agent on-call multi-window |
| Auto-credit | Indonesia SLA breach → adjust commission |
| Tier upgrade path | Bronze → Silver 怎么提升 |

**主动 quote**:

> "We treated 7 markets as 7 tenants in our voice agent. Each had a different SLA — Indonesia high-volume tolerance for 200ms p99, Thailand stricter at 150ms because of stricter compliance regime. We isolated via **per-market Kafka partitions + dedicated inference replicas for top-3 markets**. Indonesia had a payday burst event — 5x normal traffic. **Because top-3 were dedicated, Thailand and Korea were unaffected**. That isolation cost extra hardware but saved us a major SLA breach across 6 other markets. The lesson I'd transfer: **tier-based physical isolation is worth its hardware cost** when you have any sufficiently high-value tenant — it's insurance, not luxury. We also instituted **per-market burn rate alerts (1h, 6h, 1d, 3d windows)** — caught a slow degradation in Vietnam that gradient-shifted over 48h and would have missed a simple aggregate alert."

---

## 5 follow-ups

**Q1**: "Gold tenant suddenly spikes 20x, burns through capacity. What now?"

**A**: Tier-protected response:
- **Hard ceiling** per tenant even within tier (e.g., 100k QPS max regardless of Gold)
- **Auto-scale dedicated infra** (+20% capacity for 1h)
- **Customer-facing alert**: "you're approaching capacity, do you need a tier upgrade?"
- **Bill overage 1.5x normal rate** (motivation to upgrade properly)
- If sustained for > 4h: emergency capacity review, possibly negotiate dedicated cluster

**Q2**: "Bronze tenant DDoS attempt — how protect Silver/Gold?"

**A**:
- Pooled Bronze infra **completely separate physical** from Silver/Gold
- Cross-tier blast radius **zero by design**
- Automated anomaly detection on Bronze: 100x normal → temporary throttle + alert customer
- WAF rules on Bronze tier IP ranges (if applicable)
- If proven malicious: terminate tenant per ToS

**Q3**: "1B events/day storage cost — how reduce?"

**A**:
- **Tiered storage**: hot 7d in RAM/SSD, warm 30-90d in SSD, cold 1y+ in GCS
- **Aggregate-first**: raw events 7d, 1-min rollups 90d, 1-hour 1y, daily 3y
- **Sampling** for non-critical metrics (debug traces 1/100), but **never for billing**
- **Per-tenant retention**: Bronze 30d, Silver 90d, Gold 1y
- **Compression**: Prometheus block compression / Mimir blocks → 10x storage saving

**Q4**: "Customer disputes a billing line. How do we prove?"

**A**:
- **Per-request audit log** retained 13 months (1 year + buffer for legal)
- Tenant can **self-serve usage report** (CSV download)
- Dispute window **60 days**
- **Cryptographic signature** on monthly invoice (tamper-proof, HMAC)
- Internal "**billing replay**" tool: ops can reconstruct billing from raw logs to verify
- Match against telemetry DB (double-entry bookkeeping consistency)

**Q5**: "Multi-region deployment. SLA computed in which region?"

**A**:
- **SLO per region** (each region has own availability score)
- Customer sees **per-region dashboard**
- Overall SLA = `min(regions used)` OR `weighted by traffic distribution` (negotiated)
- Cross-region **failover** may pause SLO computation briefly (5-10 min)
- Multi-region active-active 是 "max" available, active-passive 是 region 1 own

**Q6**: "How do you handle latency SLA across global users when our service is in Singapore only?"

**A**:
- **Be honest in SLA**: "p99 < 200ms from APAC region, < 500ms from EU/US"
- Or **regional deployment**: spin up EU/US replica (cost ↑)
- Or **CDN-front for cacheable**: latency-sensitive read-only endpoints on CDN
- **Per-region SLI**: 不是单个 SLA 数字, 而是 per-customer-region 算
- 给客户透明的 latency map dashboard

---

## ❌ 易错点

1. **Cardinality 失控** — 10k tenant × 100 metric × 10 label
2. **Single shared infra for all tiers** — no isolation
3. **没 rate limit at gateway** — app 层被打爆
4. **没 quota per-tenant DB connections** — 1 tenant 杀全 DB
5. **Billing 跟 telemetry 同 DB** — billing 受 telemetry retention 影响
6. **Aggregate at query time** — query 慢 + 贵
7. **没 dispute window / audit** — billing 不可挑战, customer 怒
8. **Sampling for billing** — billing 数据**绝不能** sample
9. **SLA = SLO** (没 buffer) — breach 概率高
10. **Burn rate alert 单 window** — 要 multi-window
11. **Tier 不可升级** — 客户成长后没 path
12. **Bronze 受 DDoS 没 protect** — anomaly detection 缺失

---

## ✅ 加分项

1. **3-layer isolation** (gateway / app / physical)
2. **Tier-based dedicated infra** for Gold
3. **Multi-window burn rate alerts** (modern SRE)
4. **Aggregate-first storage** (rollups > raw)
5. **Billing 独立 DB** + cryptographic invoice
6. **Per-region SLO** computation
7. **Hard ceiling even within tier** (anti-DDoS)
8. **Tenant self-serve usage report** (60d dispute)
9. **Cardinality control** (top-N + bucket + sampling)
10. **Auto-credit on SLA breach** (no manual asking)
11. **Streaming aggregation** (Flink for pre-rollup)
12. **Public status page** (transparency)
13. **Per-tenant alert routing** (not just one channel)

---

## 一句话总结

> **Multi-tenant SaaS monitoring + SLA = "3 层 isolation (gateway / app / physical) + per-tenant SLI 但严控 cardinality + tier-based threshold + multi-window burn rate alert + 自助 dashboard + 自动 credit + 严格 billing audit"**.
>
> 这道题考的不是 "你会用 Prometheus", 是 "你跑过 10k+ tenant 的 SaaS, 处理过 noisy neighbor + cardinality 爆炸 + customer-facing SLA disputes".

---

## Cheat Sheet (印 1 页)

```
SLI / SLO / SLA / Error Budget:
  SLI  - measurement (e.g., success rate)
  SLO  - internal target (99.9%)
  SLA  - contractual promise (99.5%, with credit)
  EB   - 1 - SLO, monthly window
  Burn rate: how fast EB is consumed
  SLO > SLA (留 buffer)

Burn rate alerts (Google SRE 推荐):
  1h  @ 14x burn → critical (page)
  6h  @ 7x burn  → critical
  1d  @ 3x burn  → warning
  3d  @ 1x burn  → warning

3 isolation layers:
  L1 API Gateway: per-tenant token bucket (by tier)
  L2 App: DB pool, memory quota, WFQ
  L3 Physical: dedicated replicas for Gold

Tier 标准 (示例):
  Gold:   99.99% / 10k QPS / dedicated / 24x7
  Silver: 99.9%  / 1k QPS  / pooled    / business h
  Bronze: 99%    / 100 QPS / pooled    / email

Cardinality 控制 (multi-tenant 关键):
  Per-tenant only top-N metrics
  Top-100 tenant full, long-tail aggregated
  Endpoint bucketing (not raw URL)
  Streaming aggregation (Flink pre-rollup)
  Sampling for non-billable (1% OK)
  Billing NEVER sampled
  Mimir/Cortex for > 10M ts
  Datadog for $$ + low-ops

Storage tiers:
  Hot:  raw 7d, 1-min rollups 30d
  Warm: 1-min 30-90d in SSD
  Cold: 1-hour 1y, daily 3y+
  Per-tier retention (Bronze 30d, Gold 1y)

Alert routing:
  P0 (Gold SLA) → PagerDuty 24x7
  P1 (Silver / non-SLA Gold) → business hours
  P2 (Bronze) → Slack
  P3 (info) → daily digest
  Dedup 1h per (tenant × metric)
  Per-tier severity

Customer-facing:
  Self-serve SLO dashboard
  Error budget remaining %
  Usage CSV export
  Public status page
  60d dispute window
  Auto-credit on SLA breach

Billing:
  Separate DB from telemetry
  100% recorded (no sampling)
  WORM (immutable)
  HMAC-signed events
  13-month retention
  Self-serve report
  Crypto-signed invoice
  Double-entry consistency check

Noisy neighbor protection:
  Hard ceiling even in tier
  Auto-scale on Gold burst
  Bronze完全 isolated from Silver/Gold
  Per-tenant DB pool
  Per-tenant memory budget
  WFQ scheduler

工具栈:
  API Gateway:  Envoy / Kong / Cloudflare
  Metric:       Prometheus / Mimir / Cortex / Datadog
  Visualization: Grafana / DD dashboard
  Alert:        Alertmanager / PagerDuty / Opsgenie
  Streaming:    Flink / Spark Streaming / Materialize
  Storage:      ClickHouse / TimescaleDB / Druid

红线:
  - Cardinality 失控
  - Single shared infra
  - 没 per-tenant rate limit
  - Sampling for billing
  - SLA = SLO (no buffer)
  - 单 window burn rate alert
  - Telemetry + billing 同 DB
```
