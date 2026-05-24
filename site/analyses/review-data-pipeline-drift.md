## Tech #4 · Data Pipeline Drift Detection — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/data-pipeline-drift.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`data-pipeline-drift.html`](questions/data-pipeline-drift.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"你 ML pipeline 跑 3 个月, accuracy 慢慢掉, 客户没投诉但你看出来了 — 怎么 detect drift 早, 怎么修?"** 我按这 8 层回答, 不跳序.

### 📐 Drift Detection + Remediation — 8 层 framework

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 |
|---|---|---|---|---|
| 1 | Frame: silent failure 才是真敌人 | 30s | "Silent failure 不是 'model died', 是 'model still returns plausible answer, but wrong distribution'. 客户 6 个月后才发现. 第一原则: detection > anything" | "First — silent failure beats loud failure. Plausible-but-wrong is the enemy…" |
| 2 | 4 类 drift 区分 | 1.5 min | (a) **Covariate drift** P(X) — feature distribution change, e.g., user demographic shift; (b) **Concept drift** P(Y\|X) — relationship change, e.g., what defines "good loan" changed; (c) **Label drift** P(Y) — outcome distribution change; (d) **Schema drift** — field type / new field / missing field. 4 类 root cause + remediation 完全不同 | "Four drift classes — covariate / concept / label / schema — different root cause + fix per class…" |
| 3 | 检测方法 per class | 2 min | Covariate: **PSI** (Population Stability Index) > 0.25 alert, KS test p < 0.001. Categorical: chi-square. High-dim: **embedding centroid** distance + MMD. Concept: **accuracy monitor with ADWIN** (Adaptive Windowing) — concept drift only detectable via outcome. Label: chi-square on label dist. Schema: schema registry + Great Expectations / dbt test | "Per class — PSI for covariate, ADWIN for concept, chi-square for label, schema registry for schema…" |
| 4 | 3 层架构 (input / output / feedback) | 1.5 min | Deploy detection 3 places: (a) **Input layer** — feature dist 监控 (covariate / schema fast detect); (b) **Output layer** — prediction dist 监控 (label drift + early concept signal); (c) **Feedback layer** — ground truth comparison (true concept drift, lags weeks-months). 3 层 缺一不可 | "Three layers — input PSI / output prediction dist / feedback ground truth — covers fast → slow signal…" |
| 5 | Per-dim routing to owner | 1.5 min | Drift alert routing matrix: schema drift → integration team P0 (block pipeline, fix mapping); covariate drift on key feature → data eng P1 (investigate source); concept drift → ML team P1 (retrain); volume drift → source team P1 (check upstream); label drift on rare class → product team P2. 每个 alert 必须有 owner | "Routing — schema P0 integration, covariate P1 data eng, concept P1 ML team, label P2 product…" |
| 6 | Remediation playbook 闭环 | 1.5 min | Schema → block pipeline + fix mapping + replay; Covariate → quantify segment, decide subset retrain vs full retrain; Concept → retrain with recent data, validate on holdout, A/B canary; Label → check source upstream + verify labeling team consistency; 每个 playbook 含 success criteria + escalate criteria | "Remediation — schema block+replay / covariate quantify+retrain / concept retrain+A/B / label upstream check…" |
| 7 | Observability + dashboard | 1 min | Per-feature PSI weekly. Per-prediction-class freq dashboard. Feedback latency tracker (how stale is truth label). Alert on rate of change not absolute (drift accelerating > drift baseline). Tools: Whylogs / Evidently / custom Grafana | "Observability — PSI dashboard / prediction freq / feedback lag / alert on rate-of-change not threshold…" |
| 8 | Resume hook | 1 min | "Concrete: Indonesia voice agent 3-month run. PSI alert on call-duration feature (covariate drift, +18% mean). Investigation: new carrier acquired, longer ring time. Retrained with last-30-day data + carrier flag feature. CER 25%→26% maintained. Without detection would have silently dropped to ~22%. Internal Agent Platform shared drift framework across 200+ agent" | "Real example — Indonesia voice agent PSI alert on call duration, retrain prevented silent drop…" |

### 🎯 为啥按这个序

Silent failure framing 在第 1 因为面试官想知道你懂 drift 的本质不是 "model crashed". 4 类 区分 是核心 — 大部分人混淆 covariate vs concept. Detection method per class 是 technical depth. 3 层架构 是 "你真的部署过 detection 还是只读过论文" 的 signal. Routing + remediation 是 production-only knowledge. Observability + resume hook 收尾.

### 🔥 哪一层最容易被追问 deeper

**Layer 2-3 (drift class + detection)** — 必被追 "Concept drift 怎么 detect without feedback delay?" → 答: 只能间接 — proxy signal (prediction distribution shift in input-stable segment), uncertainty / margin distribution shift, prediction-prediction correlation drift. True concept drift confirmation 永远 lag (need ground truth). ADWIN is for accuracy-tracked online learning, traditional ML pipelines monitor weekly batch feedback.

**Layer 4 (3 layer)** — 追 "Why all 3, not just feedback?" → 答: feedback layer is lagging indicator — 6 week stale labels means 6 weeks of silent damage. Input layer detects in hours (covariate). Output layer detects in days (label / prediction shift). Feedback is ground truth confirmation. Use input → output → feedback as defense-in-depth timeline.

### ⏱ 时间压缩版 (30 min round)

- 0-3 min: Layer 1+2 (silent failure framing + 4 drift class)
- 3-10 min: Layer 3+4 (per-class detection + 3 layer arch)
- 10-17 min: Layer 5+6 (routing + remediation)
- 17-22 min: Layer 7 (PSI dashboard + Whylogs / Evidently)
- 22-27 min: Layer 8 Indonesia voice agent PSI case
- 27-30 min: Q&A buffer

### 🆘 卡壳兜底 (针对这题)

- 忘 PSI 公式 → "PSI = Σ (actual% - expected%) × ln(actual%/expected%); thresholds 0.1 minor / 0.25 alert / 0.5 critical; standard industry baseline"
- 被问 "feedback lag — what if no ground truth ever" → "use weak labels (heuristic / rule-based proxy), or sample 1% for human-label monthly, or use related metric (NPS / retention) as concept-drift proxy"
- 不熟 ADWIN → "online concept-drift detector for streaming — Adaptive Windowing maintains 2 sub-windows, statistically tests if means differ, drops old window on detection; alternative DDM / EDDM"

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 核心心智模型 (1 sentence)

Data pipeline drift detection = "区分 4 类 drift (covariate P(X) / concept P(Y|X) / label P(Y) / schema 字段类型) → 用合适统计 / model-based 方法 (PSI > 0.25 alert / KS test p<0.001 / chi-square categorical / embedding centroid / accuracy monitor with ADWIN) → 在 input / output / feedback 3 层架构部署 → per-dim routing 给 owner (schema → integration team P0 / concept → ml team P1 / volume → source team P1) → remediation playbook 闭环 (block + fix mapping / quantify + retrain / check source + alert)", 90% 失败是 silent failure 没监控.

### 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Covariate shift | P(X) 变, 模型仍成立 | 通常不 retrain |
| Concept drift | P(Y\|X) 变, 模型跟不上现实 | **必须 retrain** |
| Label drift | P(Y) 变, 业务环境变化 | alert business + threshold |
| Schema drift | 字段名 / 类型 / 顺序变 | block downstream + fix mapping |
| PSI | Population Stability Index, 0.25+ alert | 业务化 distribution metric |
| KS test | Kolmogorov-Smirnov 累积分布最大差 | hypothesis test |
| Chi-square | 期望 vs 实际频次, categorical | category drift |
| ADWIN | Adaptive Windowing, concept drift detector | online accuracy 跟踪 |
| Embedding centroid | text/image drift, mean distance from baseline | non-numeric drift |
| 3 层 monitor | Input + Output + Feedback | 架构必备 |
| Feedback loop | 从下游 label 回采, 见 concept drift | 否则不可见 |
| Per-segment baseline | per (market, tier, dow) 单独 baseline | aggregate 隐 |
| Dynamic threshold | 滚动 30d mean ± 3 SD | 业务变化时自动校准 |
| Alert dedup | (source × dim × 1h) 同窗口聚合 | 防 storm |
| Calendar suppression | 黑五 / 春节 已知大流量日 不报 | 防节假 false positive |
| Remediation playbook | per-drift-type 闭环动作 | block / retrain / fix mapping |

### 5 个核心 framework / pattern

**Framework 1**: 4 类 drift 分类
- When: 出现 quality 问题前
- Algorithm: covariate (P(X)) / concept (P(Y|X)) / label (P(Y)) / schema (字段/类型); 真实分布 schema 40% / covariate 30% / concept 20% / label 10%
- Trade-off: 每类不同检测方法, 不能一刀切
- Tools: PSI for covariate, accuracy monitor for concept, label histogram, schema hash diff

**Framework 2**: Detection methods 矩阵
- When: 量化 drift
- Algorithm: 连续 numeric → KS test + PSI / categorical → chi-square / text-image → embedding centroid / 模型表现 → accuracy 滚动窗口 + ADWIN/DDM
- Trade-off: statistical first, ML-based 3 months 后 layer
- Tools: scipy.stats.ks_2samp, sklearn.metrics, sentence-transformers, alibi-detect ADWIN

**Framework 3**: 3 层 monitor 架构
- When: pipeline design
- Algorithm: Input monitor (schema / volume / null / freshness / KS) + Output monitor (+ business invariants + referential) + Feedback loop (online accuracy + 用户 complaints + A/B holdout)
- Trade-off: 3 层缺一不可, feedback loop 是 concept drift 唯一可见途径
- Tools: Great Expectations input, dbt tests output, custom feedback collector

**Framework 4**: Alert 减少疲劳 4 手段
- When: 监控部署
- Algorithm: stratification (P0/P1/P2) + dedup (1h window source × dim) + auto-resolve (30min stable) + calendar suppression (already-known surge days)
- Trade-off: 每加一层减疲劳, 加 1 false negative 风险
- Tools: Alertmanager dedup, PagerDuty / Slack tier, calendar JSON list

**Framework 5**: Remediation routing per dim
- When: alert fires
- Algorithm: schema → data-integration team P0 / volume → source team P1 / null spike → data-eng P1 / PSI → product-analytics P2 / concept → ml team P1 / constraint → data-eng P0
- Trade-off: routing 表 maintain 成本 vs 找对人 cost
- Tools: ROUTING_TABLE dict + alert manager rule

### 关键决策树 (ASCII)

```
出现 ML / agent quality 问题
   |
   v
Symptom 分类:
   - 上游字段变 → Schema drift
   - 模型输入分布变 → Covariate shift
   - 同 X 出 Y 概率变 → Concept drift (最难)
   - Y 分布变 → Label drift

Detection method:
   Numeric continuous → KS test (p<0.001) + PSI (>0.25)
   Categorical → chi-square
   Text/image → embedding centroid distance > 2× baseline radius
   Model performance → accuracy + ADWIN/DDM
   Schema → hash diff + Great Expectations

3 层部署:
   Input monitor (schema/volume/null/freshness/KS) — 80% RC catch
   Output monitor (+ business invariants + referential) — 15% RC
   Feedback loop (online accuracy + complaints + A/B) — 5% RC concept drift

Alert routing:
   Schema drift → integration team P0 (block + fix mapping)
   Volume drop → source team P1 (check upstream)
   Null spike → data-eng P1 (check nullable change)
   PSI drift → product-analytics P2 (business event)
   Concept drift → ml team P1 (trigger retrain)
   Constraint break → data-eng P0 (investigate)

Remediation playbook:
   Schema → 1.block 2.compare schema 3.contact upstream 4.update mapping 5.unblock 6.backfill
   Concept → 1.confirm 2.quantify per segment 3.decide (< 5% monitor / 5-10% retrain / > 10% rollback) 4.canary
   Volume → check source / ingestion / business event
```

### Part 2 五个深度问题速查

**Problem 1: 4 类 drift 各自检测**
- 核心解法: schema (hash diff Great Expectations) / covariate (PSI > 0.25 + KS) / concept (accuracy monitor + ADWIN) / label (histogram per class)
- Top 3 gotchas: PSI > 0.1 watch, > 0.25 alert / concept drift 需 label (delayed feedback / A/B holdout / surrogate signal) / 同 ts grant + revoke tie-break
- Tools: scipy KS test, sklearn isotonic, alibi-detect ADWIN, sentence-transformers embedding

**Problem 2: Detection methods 选型**
- 核心解法: numeric → PSI + KS / categorical → chi-square / text → embedding centroid distance > 2× baseline radius / 多 feature → model-based (binary classifier baseline vs current, AUC > 0.7 = drift)
- Top 3 gotchas: PSI / KS 单 feature, model-based 联合分布 / Wasserstein distance for general / embedding 75th percentile = normal radius
- Tools: scipy.stats, sklearn RandomForestClassifier, fastdtw

**Problem 3: 3 层 monitor 架构**
- 核心解法: Input (schema / volume / null / freshness / dist) + Output (business invariants / referential) + Feedback (accuracy / complaints / A/B); 80% catch from input, 15% output, 5% feedback (concept drift 唯一可见)
- Top 3 gotchas: 没 feedback loop concept drift 完全不见 / output 必含 cross-table 业务 invariants 不只 sum / freshness assert MAX(updated_at)
- Tools: Great Expectations input, dbt tests output, custom feedback ETL

**Problem 4: Alerting 阈值 + per-segment + 减疲劳**
- 核心解法: dynamic threshold (滚动 30d mean ± 3 SD) + per-segment baseline (market × tier × dow) + dedup (source × dim × 1h) + P0/P1/P2 stratification + calendar suppression
- Top 3 gotchas: 全局 mean 隐 per-segment 失败 / dedup 同窗口聚合不消失 / quarterly review tune low-precision alerts
- Tools: SegmentedBaseline class, AlertDedup, Prophet for seasonality

**Problem 5: Remediation pipeline (routing + playbook + audit)**
- 核心解法: routing per dim (schema → integration / volume → source / concept → ml / etc.) + per-playbook (schema = block + fix mapping + backfill / concept = quantify + retrain / volume = check 3 layers) + audit log 1y
- Top 3 gotchas: auto OK (scale / retrain-small / fillna-known) vs manual (schema / large concept / constraint) / dispute window 60d / SOC 2 audit chain of custody
- Tools: ROUTING_TABLE dict, RemediationOrchestrator, audit immutable log

### Production gotchas (top 15)

1. ML-based anomaly day 1 (black-box, no RCA)
2. Single threshold for all tables
3. 没 per-segment baseline (aggregate 隐)
4. 没 dedup (alert storm on single RC)
5. 没 P0/P1/P2 stratification (page on everything)
6. 没 routing (alert → #general, no owner)
7. 没 dashboard (only alerting, no situational awareness)
8. 过 aggregate (miss per-segment drift)
9. 没 calendar suppression (Black Friday 误报)
10. 没 audit log (customer dispute 无据可查)
11. 没 feedback loop (concept drift 完全不见)
12. 没分 4 类 drift, 同套阈值 cover schema + concept
13. Embedding centroid 没 baseline radius
14. Schema drift 没 severity (added column 不该 P0)
15. ML model retrain on biased label (human override 直接 fine-tune)

### 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Schema drift detection | Voice agent CRM 7 markets | phone_country_code 类型变, 没监控 → 95% join fail |
| Volume / freshness monitor | ConvFinQA eval pipeline | per quarter report freshness SLA |
| PSI for covariate | ConvFinQA stratified eval | 4 length buckets 类似分类思路 |
| Concept drift detected | Voice agent Indonesia | 春节经济压力 promise→fulfill rate 35% → 12% |
| Alert fatigue tuning | Voice agent 7 markets | per-market threshold, quarterly review precision < 30% remove |
| Per-segment baseline | Voice agent per-market | aggregate 隐 Indonesia 50% drop |
| Routing by dim | Voice agent failure | ASR team / LLM team / TTS team |
| Statistical first ML later | ConvFinQA RL alignment | z-score → PSI → Prophet seasonality, 3 mo 后才 ML detector |
| Audit log compliance | TikTok payment 7y retention | SOC2 / SOX immutable + hash-chained |

### 面试现场 quotables (top 8)

1. "4 类 drift: covariate P(X) / concept P(Y|X) / label P(Y) / schema. 真实分布 schema 40% / covariate 30% / concept 20% / label 10%."
2. "Statistical first, ML-based after 3 months stable. ML day 1 is a trap — black-box alerts no engineer can RCA."
3. "Concept drift 没 feedback loop 完全看不见. Input + Output monitor 抓 80%, feedback loop 抓 20% concept drift."
4. "PSI > 0.25 alert, > 0.1 watch. KS test p < 0.001 reject null. Chi-square for categorical."
5. "Per-segment baseline (market × tier × dow). Aggregate hides Indonesia 50% drop when Singapore +60% offsets it."
6. "ConvFinQA: aggregate metric hides 90% drift. Stratified per-length-bucket caught cascade where T0 errors compound."
7. "Voice agent monitoring: 6 dims (volume / freshness / schema / null / distribution / referential) → MTTR < 1h from 15-day silent corruption."
8. "Remediation per dim: schema → integration team block + fix mapping. Concept → ml team retrain. Volume drop → source team check upstream."

### 红线 (top 10 anti-patterns)

1. ML anomaly day 1 (black-box)
2. Single threshold for all tables
3. No dedup (alert storm)
4. No feedback loop (concept drift invisible)
5. No per-segment baseline
6. No routing (alert → #general)
7. Aggregate metric only
8. No calendar suppression
9. Mutable audit log (compliance fail)
10. Retrain on biased human label (amplify bias)

### 4 drift types vs detection method

| Drift type | Definition | Detection | Action |
|---|---|---|---|
| Covariate | P(X) 变, P(Y\|X) 不变 | PSI > 0.25 / KS p < 0.001 / chi-square cat | 通常不 retrain, watch |
| Concept | P(Y\|X) 变, model 跟不上 | Online accuracy + ADWIN / DDM | **必须 retrain** |
| Label | P(Y) 变 | Label histogram Δ > 5pp | Alert business + threshold |
| Schema | Field name / type 变 | Hash diff (Great Expectations) | Block downstream + fix mapping |

### Statistical test 选型表

| Data type | Method | Threshold | Tool |
|---|---|---|---|
| 连续 numeric | PSI | > 0.25 alert, > 0.1 watch | numpy + percentile bins |
| 连续 numeric | KS test | p < 0.001 reject null | scipy.stats.ks_2samp |
| Categorical | Chi-square | p < 0.001 reject null | scipy.stats.chi2_contingency |
| Text / image | Embedding centroid distance | > 2× baseline radius | sentence-transformers |
| Multi-feature | Model-based (binary classifier) | AUC > 0.7 | sklearn RandomForestClassifier |
| Universal | Wasserstein distance | application-specific | scipy.stats.wasserstein_distance |

### Routing per detected dim → owner

| Dim | Owner | Severity | Playbook |
|---|---|---|---|
| Schema drift | data-integration | P0 | block + diff + contact upstream + fix mapping + unblock + backfill |
| Volume drop | source-system team | P1 | check source / ingestion / business event |
| Volume surge | data-eng | P2 | check duplicate / scale pipeline |
| Null spike | data-eng | P1 | check upstream nullable change |
| PSI drift | product-analytics | P2 | investigate business event |
| Concept drift | ml-team | P1 | quantify + decide retrain / rollback |
| Constraint violation | data-eng | P0 | investigate data quality bug |

### 工具栈 (production)

| Tool | Use |
|---|---|
| Great Expectations | declarative assertions on ingest |
| Evidently AI | drift dashboards |
| Whylogs | profiling |
| Monte Carlo | data observability platform (SaaS) |
| Prophet | seasonality decomposition (interpretable) |
| Alibi-Detect | concept drift algorithms (ADWIN / DDM) |
| dbt tests | downstream output invariants |
| Pandera | schema enforcement Python |
| Soda Core | open-source data quality |

### 60-day phasing

| Week | Stage | Deliverable |
|---|---|---|
| 1-2 | Foundation: Volume / Freshness / Schema | Great Expectations setup |
| 3-4 | Null rate | per-column null % alert |
| 5-6 | Distribution drift | PSI / KS test on top 20 columns |
| 7-8 | Concept drift + feedback loop | accuracy monitor + A/B holdout |
| 9-10 | Routing + remediation playbooks | per-dim playbook + auto-remediation |

### 5 业务场景变体 (anchor stories)

| Variant | Drift type | Detection signal | Remediation |
|---|---|---|---|
| Voice agent Indonesia 春节 | Label drift (P(Y)) | promise_to_pay 35% → 12% | adjust prompt strategy + retrain classifier |
| ConvFinQA Q3 PDF template | Schema drift | column header hash diff | parser schema 自适应 + alert |
| BNPL chatbot recommender | Covariate (P(X)) | user_tenure_days 分布左移 (new user 5% → 30%) | retrain on recent 7d + segment model |
| Indonesia refund tier | Covariate (amount distribution shift) | mean refund +40% | dynamic threshold (滚动 30d 中位数) per-market |
| Risk model 通胀 | Concept (P(Y\|X)) | prediction vs realized 违约率差 | continuous weekly retrain |

### Alert fatigue reduction 4 mechanisms

| Mechanism | Effect | Implementation |
|---|---|---|
| Stratification P0/P1/P2 | page only critical | severity = (check_name, magnitude) → pager / slack / email |
| Dedup 1h | single RC → 1 alert not 50 | (source × dim) → 1 fire per hour, count累计 |
| Auto-resolve 30min stable | close auto when metric back | metric_history(last 30min) all OK → close |
| Calendar suppression | Black Friday / 春节 不报 | KNOWN_SURGE_DAYS list, volume alert suppressed |

### Audit log fields (data quality)

| Field | Type | Purpose |
|---|---|---|
| alert_id | uuid | unique identifier |
| fired_at | datetime | when |
| type | str | "schema_drift" / "volume_drop" / etc. |
| source | str | which pipeline / table |
| severity | "P0/P1/P2/P3" | priority |
| diff | dict | what changed |
| remediation | dict | playbook + actions + actors |
| resolved_at | datetime | when closed |
| mttr_minutes | int | mean time to resolution |
| owner | str | team responsible |
| audit_chain | list | each action with actor + ts + reason |

### Per-table baseline storage strategy

| Table importance | Threshold tightness | Sample rate | Retention |
|---|---|---|---|
| Critical (billing, regulatory) | strict (z > 2) | 100% | 1y |
| Important (model training) | medium (z > 3) | 100% | 90d |
| General (analytics) | lax (z > 5) | 10% | 30d |
| Toy / experiment | none | 1% | 7d |
