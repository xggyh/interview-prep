## 题目（verbatim）

> "Build a **detection system for data pipeline quality degradation** on specific days. Cover metrics, thresholds, alerting, and root-cause routing."

**出处**：fde.academy 技术 round 经典。Databricks / Salesforce / Snowflake FDE 都问过。

**Round**：Technical Integration (45-60 min)

---

## 这道题在考什么

考你 **production data ops** —— 数据 pipeline 半挂掉是 enterprise 最常见 silent failure。

1. **Data quality 6 个维度** —— 你知道几个？
2. **Detection 灵敏度 vs 噪声 trade-off** —— 太 sensitive 警报疲劳, 太 loose 漏 bug
3. **Drift 类型区分** —— schema / distribution / volume / freshness / null-rate
4. **Root-cause routing** —— 不是只 alert, 是路由给对的人

---

## 必问 clarifying questions

**1. Pipeline structure**

> "Single pipeline or many? Batch (daily) or streaming? Source → sink 几跳？"

**2. Downstream consumers**

> "What breaks downstream if pipeline goes bad — model training? dashboard? customer-facing feature?"

**3. Existing**

> "Any current monitoring (Datadog / Airflow / Great Expectations)? Or greenfield?"

**4. Acceptable false positive rate**

> "Pager fatigue cost: how many false alerts per week are we willing to tolerate? 1? 5? 20?"

**5. Recent incident**

> "Was there a specific incident that drove this ask? Often the customer wants to detect 'the next time X happens'."

---

## 6 个 data quality 维度

| 维度 | What | 怎么 detect |
|---|---|---|
| **1. Volume** | Row count drops / surges | Time-series anomaly (z-score / Prophet) |
| **2. Freshness** | Data not arriving on time | SLA on `MAX(updated_at)` |
| **3. Schema** | Column added/removed/typed-different | Schema diff at each ingest |
| **4. Null rate** | % null per column shifts | Track per-column null %, alert on Δ > 5% |
| **5. Distribution** | Statistical drift on values (KS test, PSI) | Compare today vs 7d avg |
| **6. Referential integrity** | FK violations / orphan rows | Constraint checks |

**STAFF 答**：每个维度独立 detector, 各有 threshold + escalation。

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify pipeline + downstream stakes |
| 5-20 min | 6 维度 detection system 设计 |
| 20-30 min | Alert routing + de-duplication + on-call rotation |
| 30-45 min | Root cause routing (data team vs upstream vs infra) |
| 45-60 min | Failure modes (alert fatigue) + dashboard |

---

## 我会这样答（sample monologue）

> "Clarify — *[假设：daily batch pipeline, customer order data → analytics warehouse, downstream = sales dashboard + ML training, no existing monitoring beyond Airflow task success, customer was bit by a 2-week data corruption that went undetected]*.
>
> **6-维度 detection 系统**：
>
> **1. Volume**
> - Daily row count per table
> - Compare today vs **7d trailing mean ± 3 SD**
> - Alert if drop > 20% or surge > 50%
> - Use Prophet for seasonality (Black Friday surges normal)
>
> **2. Freshness**
> - `MAX(updated_at)` per source table polled every 30 min
> - Alert if older than expected SLA + 1h grace
> - Mean-time-to-fresh tracked as SLI
>
> **3. Schema**
> - Snapshot schema at every ingest start
> - `git-diff` style: column added/removed/type changed
> - **Breaking changes alert immediately**; non-breaking (e.g., new nullable column) info-only
> - Use Great Expectations or dbt schema tests
>
> **4. Null rate per column**
> - Top-20 important columns, track null %
> - Daily compute; alert if jumps > 5pp from 7d mean
> - **Critical columns** (customer_id, order_id) zero-tolerance: any null alerts immediately
>
> **5. Distribution drift**
> - Key numeric columns: today's mean / std / quantiles vs 7d
> - Categorical: PSI (Population Stability Index) per category
> - PSI > 0.25 alert, > 0.1 watch
> - **KS test** for continuous
>
> **6. Referential integrity**
> - Foreign keys: orphan rows count per day
> - Constraint violations (e.g., `quantity < 0`)
> - Alert any rise
>
> **Alert routing + dedup**:
>
> Routes by failure pattern:
> - Volume spike + freshness OK → likely **upstream data flood**, ping data engineering
> - Volume drop + freshness fail → **upstream system down**, ping source-system team
> - Schema change → **upstream API change**, ping integration team
> - Null spike on single column → **upstream nullable field change**, ping data engineering
> - PSI drift no schema change → **business event** (campaign / seasonal), ping product analytics
> - Constraint violations → **data quality bug**, ping data eng
>
> Each route has SLO + on-call rotation. Pager dedup: same root-cause alerts within 1h grouped into single incident.
>
> **Alert fatigue prevention** (the actual hard part):
> - **Stratify alerts**: P0 (broke customer flow) / P1 (broke internal flow) / P2 (info)
> - Only P0/P1 page; P2 to Slack
> - **Auto-resolve** when condition clears for 30 min
> - **Suppression rules**: known-bad day windows (e.g., Black Friday) suppressed
> - **Quarterly review**: alerts that have never paged in 90 days → tune up; alerts paging 5x/wk → tune down or auto-resolve
>
> **Root-cause routing flow**:
> ```
> Alert fires →
>   1. Tag with detected dimension (volume / schema / etc.)
>   2. Tag with table + column + source
>   3. Match against known patterns (table from this source has had X-type drift before)
>   4. Route to default owner of that source / table
>   5. Include in alert: link to data lineage graph showing upstream
> ```
>
> **Dashboard**:
> - Per-table health: green/yellow/red across 6 dims
> - Time-series of each metric, last 30 days
> - Recent alerts with status
> - SLO compliance (data freshness 99%)
>
> **Phasing 60 days**:
> - Wk 1-2: Volume + Freshness + Schema (foundational, low false positive)
> - Wk 3-4: Null rate
> - Wk 5-6: Distribution drift
> - Wk 7-8: Referential integrity + routing automation
>
> **Failure mode**: pager fatigue. Quote real number: pager noise > 5/week causes engineer to ignore. **Tune aggressively for first month**, expect 70% suppression rate.
>
> **What to NOT do**: ML-based anomaly detection day 1. Black-box ML alerts → can't debug → trust collapses. Use **simple statistical rules** until volume justifies ML."

---

## 简历专属 reframe

你的 **ConvFinQA eval pipeline** + **voice agent monitoring** 直接 reframe：

| 题 | 你做过 |
|---|---|
| 6-dim data quality monitoring | ConvFinQA stratified eval — distribution check across 4 length buckets |
| Distribution drift PSI | ConvFinQA classify_failure 类似分类思路 |
| Alert fatigue tuning | Voice agent 监控 7 markets, you 必经过 alert tuning |
| Per-table health dashboard | Voice agent latency dashboard 同款 |
| Root cause routing | Voice agent failure routing to LLM / ASR / TTS team |

**主动说**：

> "When I built the eval pipeline for ConvFinQA, I learned that even **stratified sampling by 4 length buckets** wasn't enough to catch distribution drift — I had to add a **per-turn-index breakdown** to spot a cascade where T0 errors propagate. For pipeline data quality, I'd apply the same lesson: **not aggregate metric, but **per-segment** — by table, by source, by column. Aggregate hides 90% of drift."

---

## 5 follow-ups

**Q1**: "Customer wants ML-based anomaly detection. Auto-magic."
**A**: 推回去：
- "Day 1 ML detection is a trap — black-box alerts, no engineer can RCA, trust collapses"
- "Statistical rules first (z-score / quantile). Once stable for 3 months, **then** layer ML on top of statistical, with **explainable output**"
- Use Prophet for seasonality (interpretable), not deep models

**Q2**: "Volume drops 50% on a Sunday — false positive (weekend)?"
**A**: Seasonality:
- **Prophet** decomposes weekly seasonality automatically
- Or **per-day-of-week baselines** (Sunday compared to last 4 Sundays)
- Or **calendar-aware suppression** (holidays, regional events)

**Q3**: "How fast can you detect a corruption that affects 0.1% of rows?"
**A**: Hard. 0.1% is below natural variance. Mitigations:
- **Sampling**: stratified row-level checks on 10k random rows / day, run referential / constraint checks
- **Domain rules**: if customer has business rules (e.g., "order_total = sum(line_items)"), assert these
- Catch downstream: model accuracy or dashboard ratio drift detects 0.1% if it accumulates

**Q4**: "Customer's source system makes schema changes daily. How not to alert every time?"
**A**:
- **Schema-change allow-list**: customer maintains list of "expected upcoming changes"
- **Non-breaking auto-accept**: add nullable column = info-only
- **Breaking changes still alert**: column drop / type change / required field rename

**Q5**: "We need to be auditable for SOC 2. How does monitoring help?"
**A**:
- Every alert + resolution logged immutable for 1 year
- Compliance dashboard: % SLOs met, MTTR, alert backlog
- **Pipeline health** is increasingly a SOC 2 / SOX item

---

## ❌ 易错点

1. **ML anomaly day 1** — black-box, untrustable
2. **Single threshold for all tables** — important tables need tighter
3. **没 dedup** — alert storm on single root cause
4. **没 P0/P1/P2 stratification** — page on everything = page on nothing
5. **没 routing** — alert lands in #general, nobody owns
6. **没 dashboard** — only alerting = no daily situational awareness
7. **过 aggregate** — miss per-segment drift

---

## ✅ 加分项

1. **6 distinct dims** with separate detectors
2. **PSI for categorical drift** specific metric
3. **Prophet for seasonality** (interpretable)
4. **Alert routing by detected dim** + lineage
5. **Auto-resolve + suppression** for fatigue
6. **Phasing 60 days** from foundational to advanced
7. **Statistical first, ML later**

---

## Cheat Sheet

```
6 dims of data quality:
  Volume / Freshness / Schema / Null / Distribution / Referential

Detection methods:
  Volume: z-score + Prophet (seasonality)
  Freshness: SLA on MAX(updated_at)
  Schema: snapshot + diff (Great Expectations)
  Null rate: per-column %, Δ>5pp alert
  Distribution: PSI > 0.25 alert
  Referential: FK constraint check

Alert structure:
  P0/P1/P2 stratification (page on P0/P1)
  Auto-resolve when stable
  Dedup within 1h
  Calendar suppression

Routing by detected dim:
  Volume drop → source system team
  Schema change → integration team
  PSI drift → product analytics
  Null spike → data engineering

Phasing 60 days:
  Wk 1-2: Volume / Freshness / Schema
  Wk 3-4: Null
  Wk 5-6: Distribution
  Wk 7-8: Referential + routing automation

红线:
  - ML day 1
  - Single threshold
  - 没 dedup
  - 没 dashboard for daily review
```
