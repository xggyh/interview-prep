## Case #2 · Logistics AI Rerouting — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/logistics-ai-rerouting.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`logistics-ai-rerouting.html`](questions/logistics-ai-rerouting.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"How do you evaluate a re-routing AI agent (no historical labels, no A/B)?"**, 我按这 8 层回答, 不跳序. 这题考的不是 "ML 模型怎么训", 是 **eval methodology when labels lag 90 days**.

### 📐 Logistics Re-routing Eval — 8 层结构

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 (literal) |
|---|---|---|---|---|
| 1 | Clarify before solving | 1 min | 5 questions: agent decision space? (reroute/hold/split) \| warehouse count? \| SLA tier? \| current baseline (rule-based?)? \| data delay (SAP 30min)? | "Before I propose eval, I need to scope decision space. Five questions..." |
| 2 | Metric anchor — CADR | 2 min | **CADR = Cost-Adjusted Delivery Rate** = (on-time deliveries) / (cost per package). 单一 metric 不行 — 必须 **stratified by**: SLA tier × region × decision type × package volume bucket | "Aggregate on-time-rate lies. I'd anchor on CADR but stratify on 4 axes — let me draw..." |
| 3 | 3 counterfactual estimators | 4 min | 因为没 ground truth, 我用 3 个 estimators: **(a) Direct method (predict counterfactual outcome with regression)** → **(b) IPS (inverse propensity scoring, re-weight observed)** → **(c) Doubly robust (combine both, hedge bias)**. 三个一起跑, 看 agreement | "No labels means 3 counterfactual estimators, not 1. Direct + IPS + DR. If they agree I trust. If they diverge I dig..." |
| 4 | LLM-as-judge for novel decisions | 3 min | 当 agent 做出 historical baseline 没做过的决策 (e.g. "split shipment to 3 warehouses"), 用 **LLM-as-judge with structured rubric**: (i) safety, (ii) cost, (iii) SLA compliance, (iv) operational feasibility. **不是给分**, 是给 4 个 binary flags | "For novel decisions counterfactuals fail. I'd use LLM-as-judge but not for scoring — for structured flagging on 4 axes..." |
| 5 | 3-layer eval pipeline | 4 min | **Offline (replay 90 days) → Shadow (run agent in parallel, don't execute) → Production (10% canary)**. Gate: shadow 必须 agreement >80% with current rule + LLM-judge flags <5% before canary | "Three-layer pipeline. Offline replay gates shadow, shadow gates canary, canary gates rollout. Each layer has explicit go/no-go..." |
| 6 | Boundary tests (hand-crafted) | 2 min | 30-50 hand-crafted scenarios: **blizzard, port strike, warehouse fire, SAP outage (30-min delay), inventory mismatch, customs hold**. 每个 scenario 有 expected behavior. 这是 **regression test**, agent 改了必跑 | "I lived this in TikTok PayLater. Indonesia refund tier CER jumped 18→25% after a daily-cap incident. After that I built 47 hand-crafted boundary tests..." |
| 7 | Tail metrics + monitoring | 2 min | **P99 latency, P95 cost, worst-case SLA breach** — 监控 4 维度: (i) decision distribution drift, (ii) override rate by warehouse manager, (iii) downstream cost, (iv) anomaly cluster (>2σ). 500 warehouse manager 每个都不一样 → **per-manager calibration** | "Average is for managers who don't care. P99 is for keeping your job. Four monitoring axes..." |
| 8 | Resume reframe | 1 min | "我在 TikTok 做 BNPL chatbot, agentic + RAG, intent routing 70→92%. **Multi-tenant** 跟 500 warehouse 一样, 每个 tenant rule 不同. Eval methodology 我复用过 ConvFinQA 的 9-variant ablation, 一个 negative result 让我学会 stratification before aggregation" | "I've done this — BNPL chatbot, multi-tenant, routing 70→92%. The eval methodology is portable..." |

### 🎯 为啥按这个序

**先 metric (CADR), 再 estimator (counterfactual), 再 pipeline (3-layer), 再 boundary (hand-crafted)** — 这是 FDE eval-when-no-labels 标准 stack. 跳序会被打断: 如果直接讲 shadow 但没讲 stratification, 面试官会问 "shadow 怎么判断 agent 比 baseline 好?" 你答不上.

LLM-as-judge (Layer 4) 是这题的 **加分项** — 一般 candidate 不知道 novel decision 不能用 counterfactual, FDE 必须意识到这层 gap.

### 🔥 哪一层最容易被追问 deeper

- **Layer 3 (counterfactual)**: 面试官会问 "IPS 怎么处理 extreme propensity?" → 答 "clip propensity at [0.05, 0.95] and report sensitivity to clip threshold. If lift is sensitive to clip we don't trust IPS"
- **Layer 5 (pipeline)**: 面试官会问 "shadow agreement <80% 你怎么办?" → 答 "first slice agreement by decision type — usually 1-2 decision classes drive disagreement. Then root cause: model issue vs label noise vs rule baseline being wrong. We assume rule baseline is right but it's often wrong"

### ⏱ 时间压缩版 (30 min round)

- 4 min: clarify + CADR (Layer 1-2)
- 8 min: counterfactual estimators + LLM-as-judge (Layer 3-4, 重点)
- 8 min: 3-layer pipeline + boundary tests (Layer 5-6)
- 3 min: tail metrics (Layer 7)
- 2 min: resume hook (Layer 8)

### 🆘 卡壳兜底 (针对这题)

- 卡 estimator → pivot to **"我先讲 hand-crafted boundary tests, 因为 counterfactual 在 novel decisions 上 break"**
- 卡 metric → pivot to **ConvFinQA 9-variant ablation 故事**, 讲一个 metric 怎么误导
- 卡 production → pivot to **Indonesia refund tier CER 18→25%** daily-cap incident, 讲 monitoring 缺失代价

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

> **Logistics AI eval = "offline replay (CADR + 9-axis strata + counterfactual + boundary) + shadow (recommend not execute) + production 14-metric monitor + 4 类 drift 自动 retrain + 5 类 failure mode mitigation"**. Question 在考 eval, 不在考 agent. **Eval > Model**.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| CADR | Cost-Adjusted Delivery Rate = delivery_rate - λ × cost_over_baseline | 单一可优化 scalar (RL reward) |
| λ (lambda) | trade-off coefficient, 0.3-0.8 per stakeholder | 跟 customer 谈调 |
| Counterfactual | "agent 不选这条路 outcome 会怎样" 估计 | novel decision grading |
| IPW | Inverse Propensity Weighting, 罕见 decision 加权 | 反事实 estimator #2 |
| Pessimistic bound | 假设最差情形, 只有 outcome 远超才给 credit | 反事实 estimator #3 |
| LLM-as-judge | 用另一个 LLM 评 agent novel 决策 | NN 找不到匹配时 |
| Self-preference bias | 同 model 既当 agent 又当 judge → 偏好自己 | 必须不同 model family |
| Boundary tests | 50-200 domain expert 手工标 critical case | hazmat / 高值 compliance |
| Data drift | 输入分布变 (KS test) | 新地区上线 / 季节变化 |
| Concept drift | feature→label 关系变 (recent vs baseline perf) | 燃油涨价后 cost 决策不再最优 |
| Behavior drift | agent 输出分布变 (KL divergence) | 突然 5x 选 air freight |
| Outcome drift | 业务结果趋势 (Mann-Kendall) | CADR 缓慢下跌 |
| DLQ | Dead Letter Queue, 失败决策落库 | growth > 100/min alert |
| Manager gaming | 假装 accept 后台手动改 | accept rate metric 危险 |
| Stratified eval | 多轴分桶 (carrier × region × tier × value × class × weather × season) | 防 aggregate 掩盖 |
| Time-based split | train/dev/test 按时间切, 不 random | 避免 temporal leakage |

### 🎯 5 个核心 framework

**Framework 1**: 单一 scalar metric (CADR + tunable λ)
- When: 多 trade-off (delivery vs cost) 需要 single optimization signal
- Algorithm: `CADR = delivery_rate - λ × max(0, cost - baseline) / baseline`
- Trade-off: 单 scalar 易 RL 训练, 但丢失 stratification 洞察, 必须配 multi-axis dashboard
- Tools: Numpy percentile, Pandas groupby, Looker dashboard

**Framework 2**: 3-Estimator counterfactual + LLM judge
- When: novel decision human 没做过, 无 ground truth
- Algorithm: NN (历史最像) / IPW (倒概率加权) / Pessimistic (最差假设) → 3 个 agreement → > 20% 分歧 = low confidence flag for human
- Trade-off: 都是估计不是真值; LLM judge 自偏好风险
- Tools: scikit FAISS NN, Gemini 3 Pro $2/$12 + Claude Opus 4.7 $5/$25 dual-judge, kappa > 0.85 校准

**Framework 3**: 3-Layer eval pipeline (offline → shadow → production)
- When: 任何 production AI agent
- Algorithm: Offline (CI replay 2yr, block if CADR worse / strata regression / boundary critical fail) → Shadow (4w, recommend not execute, weekly retro accept rate + outcome) → Production (canary + 14 metric daily alert + kill switch)
- Trade-off: 慢, 但跳一层 = 早期 bug 打到客户
- Tools: GitHub Actions CI, LaunchDarkly feature flag, Datadog APM, Mimir 长期, dbt + Airflow

**Framework 4**: 4-Drift detection + retraining pipeline
- When: 上线后自动监测环境变化
- Algorithm:
  - Data drift: KS test per feature, pval < 0.01 → flag
  - Concept drift: train quick model on recent 30d, if > +3% baseline → retrain
  - Behavior drift: KL(today || last_7d) > 0.5 → investigate (could be prompt injection)
  - Outcome drift: Mann-Kendall tau < -0.3 + pval < 0.01 → urgent retrain
- Trade-off: 检测灵敏度 vs 假警报频率
- Tools: scipy.stats.ks_2samp / kendalltau, Evidently, Whylogs, Great Expectations

**Framework 5**: 5-Class production failure mitigation
- When: 永远生效, 5 个独立 detector
- Algorithm:
  - Upstream stale: SAP 60min lag → disable inventory decisions; weather 30min stale → no_weather_signal
  - Edge case: > $5K value / hazmat / VIP / single trigger > 100 / cost > $1000 / novel pattern → escalate
  - Prompt injection: sanitize (truncate, structured input) / system prompt 强化 / output validate (cost > 1.5x baseline → escalate)
  - Correlated failure: 60min 窗口任何 decision type > 5x baseline OR single trigger > 100 affected → pause + oncall
  - Manager gaming: 对比 accept vs actual action, > 20% mismatch → alert; outcome metric 主导, 不是 accept rate
- Trade-off: 5 个 guard 会增加 manual escalation 量
- Tools: feature_flag.set('agent_enabled', False) kill switch, DLQ growth alert

### 🌳 关键决策树

```
新 PR 提交 → CI offline eval
├── CADR < human - 0.005? → FAIL block
├── Strata regression (any > -0.02)? → FAIL block
├── Boundary critical fail rate > 0? → FAIL block
└── Else → Stage to shadow

Shadow 4w
├── Agreement < 85%? → review, possibly block
├── Manager accept rate per manager > 70%? → continue
└── Else → Pilot 3 warehouse

Pilot 4w
├── Outcome worse than control? → kill, debug
└── Else → Production canary

Production daily
├── Delivery rate < 99% / 24h? → page + kill switch eval
├── Cost > 110% baseline / 6h? → page
├── KL(today || baseline) > 0.5? → page (injection?)
├── DLQ growth > 100/h? → page
├── Novel decision > 20% / 1h? → warn
└── Latency p99 > 2s? → warn
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: CADR + Stratification**
- 核心解法:
  ```python
  cadr = delivery_rate - 0.5 * max(0, cost - baseline)/baseline
  strata = carrier × region × tier × class × value × weather × season  # 7 axes
  alert if any stratum drops > 0.02 vs last_week
  also: P50/P99/P999 tail metrics, spike_analysis above_p99
  ```
- Top 3 gotchas: 多 metric 选不出 Pareto / aggregate 改善某 strata 退步 / 忽略 P99 tail
- Tools: numpy.percentile, scipy, Pandas groupby

**Problem 2: Counterfactual Eval**
- 核心解法:
  ```python
  # 3 estimator agreement
  nn = nearest_neighbor_outcome(decision, context, k=20)
  ipw = ipw_outcome(decision, context)  # 1/propensity weight
  pess = max_historical_outcome(context)
  if max-min > 0.2 * mean: confidence=low, flag_human
  # LLM judge for truly novel
  judge: gemini_pro_complete(prompt), inter-judge with Claude Opus 4.7
  ```
- Top 3 gotchas: self-preference bias (same model) / IPW propensity < 0.05 不可靠 / novel decision 当当然给 credit
- Tools: scikit FAISS, Gemini 3 Pro $2/$12 + Claude Opus 4.7 $5/$25 dual-judge

**Problem 3: 3-Layer Pipeline**
- 核心解法:
  ```python
  offline_eval(agent) → PASS gate
    └── time_split / CADR / strata / boundary / novel rate
  ShadowAgent.on_shipment_delay → log decision, human still decides
  ProductionMonitor: 14 alerts (4 维度) + kill switch
  ```
- Top 3 gotchas: random split temporal leakage / 跳 shadow 直 pilot / production 没 kill switch
- Tools: GitHub Actions, LaunchDarkly, Datadog, OpenTelemetry, Mimir, dbt + Airflow

**Problem 4: Drift + Retraining**
- 核心解法:
  ```python
  # 4 类 drift detection daily
  data_drift: scipy.stats.ks_2samp(today, baseline) pval < 0.01
  concept_drift: quick_model_perf - baseline_perf > 0.03
  behavior_drift: kl_divergence(today_dec, last_7d_dec) > 0.5
  outcome_drift: scipy.stats.kendalltau(days, cadr) tau < -0.3 pval < 0.01
  # retraining pipeline auto:
  pull 6mo → time_split → fine_tune → offline_eval gate → boundary gate → shadow 14d → pilot 14d → canary
  ```
- Top 3 gotchas: 检测到 drift 但没 trigger pipeline / 行为 drift 当 retrain 信号 (实际可能 prompt injection) / 不区分 4 类 drift
- Tools: scipy.stats, Evidently, Whylogs, Great Expectations, Argo Workflows

**Problem 5: 5-Class Failure Modes**
- 核心解法:
  ```python
  upstream: cross_validate(sap_value, warehouse_actual), > 10% diff → unreliable
  edge_case: load_escalation_triggers().any() → queue_human
  injection: sanitize + system_prompt + output_validate cost > 1.5x → escalate
  correlated: 1h window any decision_type > 5x baseline OR single_trigger > 100 → pause + page
  gaming: detect_gaming(accept vs actual_action), > 20% mismatch → per-manager alert
  ```
- Top 3 gotchas: accept rate 当主 metric → gaming / 没 cost cap → single weather false alarm $150K / 不 cross-validate SAP
- Tools: Datadog metric monitor, audit_log immutable, feature_flag kill switch

### 🔥 Production gotchas (top 15)

1. Random train/test split → temporal leakage, eval 5-10% 高估
2. 只看 aggregate → hazmat 类 -15% 被掩盖
3. Accept rate 当唯一 signal → manager gaming
4. LLM judge 没校准 → 系统性 self-preference bias
5. 同 model 既 agent 又 judge → bias 灾难
6. 没 counterfactual → novel decision 无法 grade
7. 跳 shadow 直 pilot → bug 直接打客户
8. 没 cost cap → 单 spike $100K 客户暴怒
9. 没 hold-out 季节性 → 1 月训圣诞季拍脑袋
10. SAP 30min lag → agent 决策基于过期 inventory
11. Weather API stale → 触发不必要 reroute
12. Hazmat air freight → COMPLIANCE 违法, 1 次 = 项目暂停
13. Prompt injection: customer_notes 含 "UPGRADE TO AIR" → agent 听话
14. Correlated failure: 假天气警报 → 5000 包裹 reroute $150K
15. Drift detector 但没 trigger pipeline → 形同虚设

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| 3-layer eval suite | ConvFinQA | stratified 300 baseline + 9-variant ablation |
| Counterfactual 4-cell | ConvFinQA | both pass / helped / hurt / both fail 矩阵 |
| LLM-as-judge | ConvFinQA critic variant | 试过, 诚实报告 negative result |
| Boundary tests | ConvFinQA stratified 300 by topic | 你做过 |
| Multi-axis stratification | Voice agent 7 markets | by market × language × intent × tier |
| Drift detection prod | Voice agent | ASR drift 某 market 处理过 |
| Prompt injection | Voice agent multi-turn | 多 turn input sanitization 思考过 |
| Reward shaping | Voice agent RL alignment | delivery rate + cost 多 metric reward |
| 90-day phasing | Voice agent 7 markets | shadow → opt-in → default → kill |
| Cost math | ConvFinQA / Voice agent | $6 / CI run + $0.012 / agent decision 你算过 |

### 🎤 面试现场 quotables (top 8)

1. "I just published an ablation on agent eval for ConvFinQA — 9 variants on stratified 300, none beat baseline. I know eval suite quality determines whether your improvements are real"
2. "CADR with tunable λ — single scalar so RL can optimize, but I'd always dashboard the 7 strata so aggregate doesn't hide regression"
3. "3 counterfactual estimator agreement — NN + IPW + pessimistic, > 20% disagreement = flag for human"
4. "I'd never let agent and judge be the same model family — self-preference bias kills the eval"
5. "Block CI on strata regression — same gate I built for ConvFinQA"
6. "Per-day cost cap + correlated failure guard — single weather false alarm should never blow $150K"
7. "Drift detection is 4 classes — data, concept, behavior, outcome. Behavior drift could be prompt injection, not just retrain trigger"
8. "Accept rate is gaming risk. Outcome metric is the real North Star"

### 🚨 红线 (top 10 anti-patterns)

1. 直接画 agent architecture (题考 eval, 不考 agent)
2. 只说 offline eval (STAFF 必须 online + production)
3. 没 counterfactual (novel 怎么 grade?)
4. 忽略 prompt injection (agentic #1 attack)
5. 没 cost cap / kill switch (跑飞了怎么停)
6. Accept-rate 当唯一 metric (manager gaming)
7. 跳 phasing (零部署经验)
8. Random split (temporal leakage)
9. 不 stratify (aggregate 掩盖)
10. Drift 检测但没 retraining pipeline

### 📊 数字 anchors (面试必记)

| Metric | Value | Source |
|---|---|---|
| CADR λ | 0.3-0.8 per stakeholder | 跟 customer 谈 |
| 9-axis stratification | carrier × region × tier × value × class × weather × season + 自定义 | 防 aggregate 掩盖 |
| Strata regression threshold | -0.02 vs last week → alert | 2% drop monitor |
| Sample size | minimum 100 per strata for reliability | 噪声防 |
| Counterfactual estimator | 3 (NN / IPW / Pessimistic), 分歧 > 20% mean = low conf | flag human |
| IPW propensity floor | < 0.05 不可靠 | 罕见 decision |
| Boundary tests | 50-200 hand-crafted by domain expert | critical class 100% pass |
| LLM-judge kappa | > 0.85 必须 (logistics 强 stake) | inter-judge calibrate |
| Daily monitor cost | $25-50 LLM-as-judge | 100-1000 sample/day |
| Agent decision cost | $0.012 each (500 in + 200 out, Gemini 3 Pro $2/$12) | per-query cost |
| CI run judge cost | $5 (500 cases × 800 tokens, Pro) | block on regression |
| Shadow duration | 4 weeks | recommend not execute |
| Pilot scope | 3 warehouses opt-in × 4 weeks | limited rollout |
| Phasing | D0-30 offline / D30-60 shadow / D60-90 opt-in / D90+ gradual | 90-day rollout |
| Drift retraining trigger | data > 5 features OR concept > 0.03 OR behavior KL > 0.5 OR outcome tau < -0.3 | auto-mark |
| Cost cap | per-day Σ reroute cost ≤ $X / customer approval | correlated failure guard |
| Single trigger | > 100 affected → pause + page | mass weather event |
| Gaming detection | accept vs actual_action > 20% mismatch | manager flag |
| Cost spike threshold | > 110% baseline / 6h sustained → page | financial gate |
| Delivery rate floor | < 99% / 24h sustained → page | SLA breach |

### 💡 Counterfactual Estimator cheat (背诵)

| Estimator | 公式 / 思路 | 限制 |
|---|---|---|
| Nearest-neighbor | k_nearest_historical (k=20), filter same decision, mean outcome | k 太小或匹配少 → None novel flag |
| Inverse Propensity Weighting | propensity = historical_count(decision) / total; if < 0.05 None; else weighted outcome / propensity | 罕见 decision 不可靠 |
| Pessimistic bound | max historical outcome for similar context, conservative | 过保守, 只 good case 给 credit |
| Agreement check | range(estimates) > 0.2 × mean → low confidence, flag human | 3 estimator 必跑 |
| LLM-as-judge | Gemini 3 Pro $2/$12 evaluate plausibility/cost/delivery/compliance | novel decision 用, kappa > 0.85 必须 |
| Dual-judge | Gemini 3 Pro + Claude Opus 4.7, inter-judge agreement alert | self-preference bias 防 |

### 💡 Production Alert cheat (背诵)

| Alert | Condition | Severity |
|---|---|---|
| delivery_rate_drop | < 0.99 sustained 24h | page, kill-switch eval |
| cost_spike | > 1.10 baseline sustained 6h | page |
| decision_distribution_shift | KL(today, last_7d) > 0.5 | page, prompt injection? |
| dlq_growth | > 100 entries/hour | page |
| novel_decision_burst | > 20% in 1h window | warn, state shift? |
| latency_p99 | > 2000ms | warn |
