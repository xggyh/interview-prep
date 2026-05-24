## AI Deep Dive #5 · How Know AI Working — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/how-know-ai-working.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`how-know-ai-working.html`](questions/how-know-ai-working.html)

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

> **"AI working well" = 3-layer pyramid (offline golden + online A/B + production always-on) + 5 metric class (technical / quality / user explicit / user implicit / business KPI) + LLM-judge calibrated (kappa > 0.6) + drift detection (data / concept / model / distribution) + per-slice not aggregate + ground-truth-less methods**. Mature production 5-15% inference cost on eval; critical domain 50%+.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Offline eval | 静态 dataset pre-deploy | CI 阶段 |
| Online eval | 上线 real traffic A/B | canary 阶段 |
| Production monitoring | always-on dashboard | drift detection |
| Golden set | 200-2000 stratified labeled | offline 必备 |
| LLM-as-judge | stronger model 评估 | scale human eval |
| Cohen's kappa | 校准 metric, > 0.6 trustworthy | LLM-judge 必校 |
| BLEU / ROUGE | n-gram overlap | structured output OK, generation weak |
| BERTScore | embedding similarity | semantic equivalence |
| Faithfulness | answer grounded in context | RAG 核心 metric |
| Hallucination rate | 编造率 | RAG critical |
| Refusal rate | model 拒答 % | safety + drift signal |
| Goodhart's Law | optimize metric → gamed | single metric 危险 |
| Data drift | input distribution 变 | KS / Wasserstein |
| Concept drift | feature→label 关系变 | recent model perf check |
| Model drift | dep / config / model upgrade | regression test |
| Distribution shift | output 分布变 | KL divergence |
| Propensity matching | 给非实验组配对 | ground-truth-less |
| Self-consistency | sample N vote majority | confidence signal |
| Pairwise preference | A vs B 偏好 | 比 absolute score 可靠 |
| Per-slice metric | by tenant / language / region | aggregate 必掩盖 |

### 🎯 5 个核心 framework

**Framework 1**: 3-Layer Eval Pyramid
- When: 任何 production AI system
- Algorithm:
  - Offline (CI / pre-deploy): golden set 200-2000 stratified + auto metrics + LLM-judge + human spot check 50/wk
  - Online (canary 1% → 5% → 50% → 100% phased): business metric vs control, auto-rollback SLO breach, stat significance
  - Production (always-on): per-tenant / per-slice metric + drift detection + LLM-judge daily 200-1000 sample + user feedback + cost/latency
- Trade-off: 每层 catch 不同 failure, 缺哪层就漏哪类
- Tools: Braintrust / Langfuse / Phoenix, Datadog APM, statistical test framework

**Framework 2**: 5-Metric Categories
- When: 设计 metric matrix
- Algorithm:
  - Technical: latency p50/p99, error rate, throughput, cost
  - Quality: LLM-judge score, refusal rate, hallucination rate, faithfulness
  - User explicit: thumbs up/down, star rating, complaint
  - User implicit: regeneration rate, session length, abandonment, completion
  - Business KPI: resolve rate, conversion, retention, NPS, repayment rate (BNPL)
- Trade-off: 单一 metric Goodhart's Law, multi-metric 复杂
- Tools: Grafana per-category dashboard, Looker business KPI

**Framework 3**: LLM-as-Judge Methodology
- When: scale human eval at 100k+ queries/day
- Algorithm:
  - Different model than under test (Gemini-judges-Claude or vice versa, no self-preference)
  - Cohen's kappa > 0.6 with human (calibrate quarterly)
  - Multi-judge ensemble for high-stakes (3 judges, avg/median)
  - Per-dimension rubric (not single score: empathy / accuracy / compliance)
  - Pairwise > absolute (more reliable, less noise)
  - Strip metadata (don't leak ground truth)
- Trade-off: 单 judge bias risk, multi-judge cost 3x
- Tools: Claude Opus 4.7 + Gemini 3 Pro dual-judge, kappa calculator quarterly

**Framework 4**: 4-Type Drift Detection
- When: production always-on
- Algorithm:
  - Data drift: input distribution change → KS test continuous, chi-square categorical, Wasserstein 1D, embedding mean cosine
  - Concept drift: true label changes over time → train quick recent model vs baseline
  - Model drift: dependency / config / model upgrade → regression test
  - Distribution shift: output behavior changes → KL divergence on output dist, refusal rate, length p50
- Trade-off: 灵敏度 vs 假警报频率
- Tools: scipy.stats, Evidently, Whylogs, Arize, Fiddler, custom alerts

**Framework 5**: Ground-Truth-Less Eval
- When: 没标注但要 know if working
- Algorithm:
  - Self-consistency: sample N times, low variance = confident
  - Ensemble agreement: 3 different models, disagreement = flag for human
  - Behavioral signals: completion rate, regeneration rate, abandonment, session length
  - Business KPI: lift vs control via propensity matching (no random assignment OK)
  - Rubric LLM-judge: criteria-based score without expected answer
- Trade-off: 没 ground truth, signal weaker, 多 method 三角化
- Tools: temperature sampling, multi-model ensemble, behavior log analysis

### 🌳 关键决策树

```
Where to invest eval?
├── Pre-deploy: build offline pipeline first (golden set + LLM-judge)
├── Deploy: canary 1% → A/B → 100% with rollback
├── Live: production monitoring (drift + per-slice)
└── Ongoing: refresh golden from production sample 每 month

Which metric to alert on?
├── Latency p99 → page (P1)
├── Error rate > 1% → page (P1)
├── Refusal rate > 20% → 30min (P2)
├── Per-tenant LLM-judge < 0.8 → 30min (P2)
├── Drift KL > 0.5 → slack (P3)
└── Business KPI -5% → escalation

LLM-judge trustworthy?
├── kappa > 0.6 vs human? → use
├── kappa 0.4-0.6? → use with human spot check
└── kappa < 0.4? → don't trust, recalibrate

Drift root cause?
├── Input distribution KS pval < 0.01 (multiple features)? → data drift, retrain
├── Recent model > +3% on test? → concept drift, retrain
├── Output dist KL > 0.5? → behavior drift, check upstream / injection
└── Refusal rate spike? → safety policy or model regression
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: Multi-Layer Eval (Unit / Integration / Production / Online)**
- 核心解法:
  ```
  Unit (component): prompt template, RAG retrieve, post-process
    - Fastest, run per PR
    - Test: schema validity, edge case input
  
  Integration (end-to-end offline):
    - Golden set 200-2000 stratified
    - LLM-judge + auto metric
    - Block merge if regression
  
  Production (always-on):
    - Per-tenant / per-slice dashboard
    - Drift detection
    - Daily LLM-judge sample
  
  Online (A/B canary):
    - 1% → 5% → 50% → 100% phased
    - Business KPI vs control
    - Auto-rollback SLO breach
  ```
- Top 3 gotchas: 跳 unit (上 integration 调试昂贵) / static golden set (3 月后 stale) / 没 auto-rollback
- Tools: pytest CI, Braintrust / Langfuse, LaunchDarkly feature flag

**Problem 2: Production Signals (Latency, Error, User Feedback, Business)**
- 核心解法:
  ```
  Latency: p50 / p99, per-stage breakdown (OTel span)
  Error: 4xx / 5xx rate, retry count, timeout %
  User explicit: thumbs / rating / complaint (sparse, biased to extremes)
  User implicit: regeneration rate (用户重发 = 不满意), session length, abandon
  Business KPI: resolve_rate / conversion / repayment_rate (BNPL)
  
  Alert hierarchy:
    P1 page: latency p99 > 2x baseline, error > 1%, business KPI -10%
    P2 30min: refusal > 20%, judge score per-tenant < 0.8
    P3 slack: drift KL > 0.5
  ```
- Top 3 gotchas: 只看 technical 不看 business / 没 implicit signal (用户不点 thumb 但 regenerate 5 次) / 单 metric Goodhart
- Tools: Datadog APM, Grafana, Looker business, PagerDuty escalation

**Problem 3: LLM-as-Judge Methodology**
- 核心解法:
  ```python
  # Per-dimension rubric (not single score)
  prompt = """
  Rate this response on:
  1. Empathy (0-10)
  2. Accuracy vs source (0-10)
  3. Compliance with policy (0-10)
  4. Format correctness (0-10)
  Return JSON.
  """
  
  # Pairwise > absolute
  prompt_pairwise = """
  Which response is better: A or B?
  Consider empathy, accuracy, compliance.
  Output: A | B | tie
  """
  
  # Calibration
  kappa = cohen_kappa(human_scores, judge_scores)
  if kappa < 0.6: recalibrate prompt / 换 judge model
  
  # Multi-judge ensemble for high-stakes
  scores = [gemini_pro.judge(x), claude_opus.judge(x), gpt55.judge(x)]
  final = median(scores)
  ```
- Top 3 gotchas: same model self-judge / single score (rubric better) / 不 quarterly recalibrate
- Tools/tactics: Cohen kappa calculator, 3 model ensemble (Gemini + Claude + OpenAI 不同 family), prompt strip metadata

**Problem 4: Drift Detection (4 types)**
- 核心解法:
  ```python
  # 1. Data drift (KS + Wasserstein per feature)
  for col in input_features:
      stat, pval = scipy.stats.ks_2samp(today[col], baseline[col])
      if pval < 0.01: flag(col)
  
  # 2. Concept drift (recent model perf)
  recent_model = train(last_30_day_data)
  if recent_model.eval(test) - baseline_perf > 0.03: flag
  
  # 3. Model drift (dep / config diff)
  diff_check(deployed_config, last_known_good)
  
  # 4. Distribution shift (output)
  kl = scipy.stats.entropy(today_output_dist, baseline_output_dist)
  if kl > 0.5: flag (could be injection, model regression, upstream)
  
  # Behavioral drift (don't conflate with model)
  KL(today_decisions || last_7d_decisions) > 0.5 → investigate
  Could be prompt injection, NOT just retrain trigger
  ```
- Top 3 gotchas: 看 aggregate 不 stratify (某 slice drift 掩盖) / drift 当 retrain trigger 但实际是 prompt injection / 没 14-day rolling
- Tools/tactics: scipy.stats, Evidently AI, Whylogs, custom alerts, 14-day rolling

**Problem 5: Ground-Truth-Less Eval**
- 核心解法:
  ```python
  # Self-consistency (low variance = confident)
  answers = [llm.complete(query) for _ in range(5)]
  variance = compute_variance(answers)
  if variance > threshold: flag uncertain
  
  # Ensemble agreement
  results = [model_a(x), model_b(x), model_c(x)]
  if not all_agree(results): flag for human
  
  # Behavioral signals
  signals = {
    'completion_rate': 0.85,
    'regeneration_rate': 0.05,  # 用户 regenerate = dissatisfied
    'session_length_p50': 320,  # seconds
    'abandonment_at_step': step_dist
  }
  
  # Propensity matching for business KPI lift
  # (no random A/B OK, match by observable confounders)
  matched_control = propensity_score_match(treated, untreated, confounders)
  lift = treated.outcome.mean() - matched_control.outcome.mean()
  
  # Rubric LLM-judge (no gold answer)
  rubric = "Score on empathy / accuracy / compliance, output JSON"
  ```
- Top 3 gotchas: 没 ground truth 当借口不做 eval / self-consistency 当 accuracy / propensity matching 没 confound control
- Tools/tactics: temperature 多采样, multi-model ensemble, causalinference Python library

### 🔥 Production gotchas (top 15)

1. BLEU / ROUGE for generation → weak signal
2. Same model self-eval → bias (no self-preference)
3. Static golden set → 3 月后 stale
4. Single metric optimization → Goodhart's Law gamed
5. No human-in-loop → blind spots
6. No drift detection → silent regression
7. 看 aggregate 不 per-slice → 某 tenant / language 退步掩盖
8. 优化 technical metric 忽略 business KPI → 假阳性
9. LLM-judge 不 calibrate kappa → 不可信
10. 没 implicit user signal → 用户 regenerate 5x 但不点 thumb
11. 没 auto-rollback → 上线后 P99 爆 自己重启
12. 跳 unit test 直接 integration → 调试成本高 10x
13. 没 cost monitoring → bill shock
14. Refusal rate spike 不 alert → policy 误 expand 漏检
15. 没 quarterly judge recalibrate → kappa 滑落

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| 3-layer eval | Voice agent 7 markets | offline + canary + production |
| Stratified golden | ConvFinQA 9-variant ablation | 300 stratified by topic |
| LLM-as-judge calibration | ConvFinQA | kappa > 0.6 vs human |
| Drift detection production | Voice agent Indonesia | repayment rate -8pp 抓到 |
| Per-slice metric | Voice agent 7 markets | per-market dashboard |
| Auto-rollback | Voice agent canary | SLO breach 自动 rollback |
| Business KPI vs technical | Voice agent repayment rate | technical 好但 business 差案例 |
| Ground-truth-less | Internal Agent Platform | self-consistency + ensemble |
| Continuous golden refresh | ConvFinQA | production sample → golden |

### 🎤 面试现场 quotables (top 8)

1. "3-layer eval pyramid — offline pre-deploy + online canary A/B + production always-on. Each catches different failure"
2. "LLM-judge requires kappa > 0.6 vs human, or don't trust it. Recalibrate quarterly"
3. "Per-slice metric matters more than overall — worst slice catches issues that aggregate hides"
4. "Goodhart's Law — any single metric you optimize becomes gamed. Multi-metric or you'll over-fit"
5. "Static golden set is dead within months — production sampling is the refresh loop"
6. "Voice agent Indonesia — caught repayment rate -8pp via per-market dashboard, fixed via DPO refresh on Indonesian-specific firm-but-polite examples"
7. "ConvFinQA — 9-variant ablation on stratified 300 set, critic agent gave 4/358 useful flags. Honest negative result"
8. "Mature production allocates 5-15% inference cost on eval. Critical domain like healthcare or finance, 50%+"

### 🚨 红线 (top 10 anti-patterns)

1. BLEU / ROUGE for generation
2. Same model self-eval
3. Static golden set (no refresh)
4. Single metric optimization
5. No human-in-loop
6. No drift detection
7. Optimize technical metric ignore business KPI
8. LLM-judge 不 kappa-calibrate
9. 看 aggregate 不 per-slice
10. 没 auto-rollback on SLO breach
