## 题目（verbatim）

> **[OpenAI Technical Deep Dive]**
>
> "How do you **know your AI system is actually working well in production**? Cover evaluation: automated metrics, human feedback, online vs offline, drift detection."

**出处**: OpenAI FDE 真题. 几乎所有 FDE 都问 (Google / Anthropic / Salesforce / Databricks). 也是 senior AI engineer 招聘的 universal question.

**Round**: Technical Deep Dive (60 min)

---

## 这道题在考什么

考你 **production AI eval discipline** + **observability philosophy**:

1. **Offline / Online / Production** 三层 eval 区分
2. **Automated metrics 局限** — 知道 BLEU / ROUGE 不够
3. **Human-in-the-loop scaling** — 怎么 scale 不靠 100% 人审
4. **LLM-as-judge methodology** — 知道 caveat + calibration
5. **Drift detection** — production over time, data shift / concept shift / model regression
6. **Ground-truth-less eval** — 没标注怎么 know if working
7. **业务 metric vs technical metric** — 最终是 business KPI

不考「BLEU 是什么」, 考「你 own 过一个 production AI system, 怎么 sleep at night」.

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**Offline eval**: 在静态 dataset 上 pre-deploy 跑的 eval. **Golden set + automated metrics + LLM-as-judge + human spot check**. 优点: fast, cheap, controlled. 缺点: 不能 catch distribution shift / unseen edge cases.

**Online eval** / **A/B test**: 上线后用 real traffic 测. **Canary / A/B with control group, business metrics**. 优点: real user signal, high signal-to-noise. 缺点: slow (days-weeks), can hurt users if regression.

**Production monitoring**: always-on dashboard. **Latency, error rate, drift indicators, user feedback**. 优点: continuous, real-time. 缺点: 通常是 **lag indicator** — 问题已经发生.

**LLM-as-judge**: 用一个 stronger model 评估 main model 的输出. **替代 human eval** at scale. 必须 calibrate against human labels 才能信. **Cohen's kappa > 0.6** 是 trustworthy threshold.

---

## 2. 这个问题的核心是什么

**设想没有 eval discipline** 的灾难场景:

```
工程师:        "model 看起来还行, deploy 吧"
3 天后:        客服收到 200 个投诉
PM:           "AI 怎么乱答?"
工程师:        "我 spot check 了 10 个 sample, 看起来 OK"
PM:           "为啥不知道哪儿坏了?"
工程师:        "没 metric, 没 golden set, 没 drift detection..."

调查发现:
  - Distribution 变了: 新一批用户问的是退款, 历史 dataset 全是开通问题
  - Refusal rate 涨了 3x: model 越来越 conservative
  - 印尼用户 95% 满意, 越南用户 60% 满意 — 但 overall 看不出
  - 上次 deploy 改了 prompt, 但没 regression test
  - 投诉数据没回流到 eval set
```

**核心矛盾**:

- 没 eval = 不知道 model 好不好
- 只有 offline eval = 不知道 production reality
- 只有 online metric = 落后指标, 出事才知道
- 单一 metric = Goodhart's Law (优化某指标, 该指标失去意义)
- 没 drift detection = 上线时好, 慢慢变差也不知道
- 没 per-slice metric = overall 看似好, 实际某用户群惨

**正确解法 — 多层 eval pyramid**:

```
Layer 1 (Pre-deploy):  Offline 自动 + LLM-judge + 人 spot
Layer 2 (Post-deploy): Online canary + A/B with business metric
Layer 3 (Always-on):   Production drift + per-slice metric + alerts
Layer 4 (Continuous):  Production samples → golden set refresh
```

---

## 3. 三层 Eval Pyramid 图

```
                       ┌────────────┐
                       │  Customer  │
                       │  outcomes  │  ← 终极 truth (business metric)
                       └────────────┘
                              ▲
                              │
                       ┌────────────┐
                       │  Online    │  ← A/B test, 真用户信号
                       │  A/B test  │     slow but real
                       └────────────┘
                              ▲
                              │
                       ┌────────────┐
                       │ Production │  ← Always-on, drift detection
                       │ monitoring │     lag but continuous
                       └────────────┘
                              ▲
                              │
                       ┌────────────┐
                       │  Offline   │  ← Pre-deploy, fast, cheap
                       │  golden    │     controlled but limited coverage
                       └────────────┘
                              ▲
                              │
                       ┌────────────┐
                       │ Unit-level │  ← Per-component, fastest
                       │ component  │     prompt template, RAG retrieve, etc
                       └────────────┘
```

**每层 catch 不同 failure**:

| Layer | Catches | Misses |
|---|---|---|
| Unit | Logic bugs, schema breaks | End-to-end behavior |
| Offline golden | Known failure modes | Distribution shift |
| Online A/B | Real user reactions | Long-term effects |
| Production monitoring | Drift, latency | Subtle quality drops |
| Business metric | True success | Causality (correlation only) |

---

## 4. 5 类 metric 分类表

| Category | Example metrics | What it tells | Limitations |
|---|---|---|---|
| **Automated technical** | BLEU, ROUGE, F1, exact-match, JSON schema valid | Structured output correctness | Weak signal for generation |
| **Embedding similarity** | Cosine to reference answer, BERTScore | Semantic equivalence | Misses factual accuracy |
| **LLM-as-judge** | Rubric score 1-5, pairwise preference | Quality dimensions | Need calibration vs human |
| **User feedback (explicit)** | Thumbs up/down, star rating | User satisfaction | Sparse, biased to extremes |
| **User feedback (implicit)** | Regeneration rate, session length, abandon rate | Behavioral signal | Noisy, multi-confound |
| **Business KPI** | Resolve rate, conversion, retention, NPS | True value | Slow to measure, multi-cause |
| **Operational** | Latency p99, error rate, cost/query | Service health | Doesn't measure quality |
| **Drift indicators** | Input distribution KL, output length shift, refusal rate change | Data / concept drift | Lag indicator |
| **Safety** | Refusal on disallowed content, jailbreak resistance | Compliance | Hard to enumerate threats |
| **Fairness** | Per-slice metrics (gender, language, region) | Demographic equity | Need defined slices |

---

## 5. 具体业务场景 (5 类)

### 场景 A: TikTok PayLater Voice Agent — 7 markets eval (你的工作)

**Layered eval**:

```
Offline (CI / pre-deploy):
  - Golden set: 500 calls per market × 7 markets = 3500
  - Stratified by: intent (refund / repayment / dispute / inquiry), language, severity
  - LLM-judge (Claude Opus 4.7) eval each on rubric: empathy, accuracy, compliance
  - Required: 85% rubric pass rate before merge

Online (canary):
  - 1% traffic → 5% → 25% → 100% over 2 weeks
  - **Business metric**: repayment rate within 7 days post-call (vs control group)
  - **User metric**: call duration, customer rating post-call
  - Auto-rollback if repayment rate -5pp vs control (early stop)

Production (always-on):
  - Daily LLM-judge sample of 500 calls
  - Drift detection: language distribution, intent distribution, refusal rate
  - Per-market dashboard (Indonesia / Vietnam / Thailand / Brazil / ...)
  - PagerDuty if any market success rate drops below threshold

Specific incident I caught:
  Week 2 of Indonesia rollout, repayment rate -8pp vs control
  Investigation: model too apologetic, customers felt "bot doesn't take 
                 me seriously", more disputes
  Fix: DPO refresh on Indonesian-specific firm-but-polite examples
```

### 场景 B: BNPL Chatbot RAG

**Layered eval**:

```
Offline:
  - Retrieval eval: 200 golden queries, recall@10, NDCG@10
  - Generation eval: faithfulness (does answer match retrieved chunks),
                     hallucination rate (claims not in chunks)
  - LLM-judge: answer correctness vs gold answer

Online:
  - A/B: new RAG version vs old
  - **Business metric**: resolved-without-escalation rate
  - User metric: thumbs up/down on each response

Production:
  - Daily sample 1000 production queries → LLM-judge
  - Drift: query length, language distribution, FAQ category mix
  - Per-product-line dashboard (PayLater / Pay-in-4 / Merchant Loan)
  - Alert if "I don't know" responses spike > 20%

Incident:
  Q3 2026: new product launch, "I don't know" rate spiked 15% → 28%
  Cause: RAG corpus didn't have new product docs yet
  Fix: emergency RAG index update + alert for new-product queries
```

### 场景 C: ConvFinQA Multi-hop Financial QA (你做过的 reference)

**Layered eval**:

```
Offline:
  - Stratified 300 conversations (your methodology)
  - Per-hop accuracy (single calc / 2-hop / 3-hop+)
  - Number-exact match (with unit normalization)
  - Calculator tool call accuracy

Special: Critic variant ablation
  - 9-variant ablation with critic agent triggered for percent_change/divide
  - Result: 4/358 useful flags (honest negative result)
  - Lesson: eval cost ≠ signal, targeted cheap > one-size-fits-all expensive
```

### 场景 D: Code Generation Copilot

**Layered eval**:

```
Offline:
  - Functional correctness (does generated code pass tests?)
  - Code quality (lint, type check)
  - LLM-judge: matches style guide

Online:
  - Acceptance rate (user accepts suggestion vs rejects)
  - Time-to-task-completion
  - PR rejection rate (if generated code causes review issues)

Production:
  - Per-language acceptance rate
  - Hallucination rate (calls non-existent APIs)
  - Security: % of accepted code with SAST issues
```

### 场景 E: 内部 Agent Platform

**Layered eval**:

```
Per-team eval framework provided by platform:
  - Standard offline golden set spec
  - LLM-judge calibration kit
  - Drift detection module

Cross-team aggregated:
  - Platform-level SLOs (latency, error rate)
  - Per-tenant quality bands (free tier vs enterprise)
  - Cost per team
```

---

## 6. 工程上要做什么 — eval pipeline playbook

### Step 1: Build offline eval foundation (Week 1)

```python
# 1. Golden set construction
golden_set = [
    EvalSample(
        query="What's the refund timeline?",
        expected_answer="Refunds processed within 7-14 business days.",
        category="factoid",
        difficulty="easy",
        language="en",
    ),
    # 100-500 samples to start
]

# 2. Automated metrics
def auto_metrics(generated, expected):
    return {
        'exact_match': generated.strip() == expected.strip(),
        'embedding_sim': cosine(embed(generated), embed(expected)),
        'has_required_fields': has_json_keys(generated, ['amount', 'date']),
        'refusal': is_refusal(generated),
    }

# 3. LLM-as-judge
async def llm_judge(query, generated, expected):
    prompt = f"""
    Question: {query}
    Expected: {expected}
    Generated: {generated}
    
    Rate the generated answer on:
    - Accuracy (1-5)
    - Completeness (1-5)
    - Tone (1-5)
    
    Output JSON: {{"accuracy": int, "completeness": int, "tone": int, "reasoning": str}}
    """
    return await claude_opus_47.generate(prompt)

# 4. Calibrate LLM-judge against human (100 hand-labeled samples)
human_labels = load_human_labels()  # 100 samples
judge_labels = [await llm_judge(...) for s in samples]
kappa = cohen_kappa(human_labels, judge_labels)
assert kappa > 0.6, f"Judge unreliable: kappa={kappa}"
```

### Step 2: CI integration (Week 1)

```yaml
# .github/workflows/eval.yml
name: AI Eval
on: [pull_request]

jobs:
  eval:
    runs-on: gpu-runner
    steps:
      - checkout
      - run: pip install -r requirements.txt
      - run: python eval/run_offline.py --eval-set golden_v3 --threshold 0.85
      - if: failure(): block merge
      - run: python eval/compare_baseline.py --base main --new HEAD
      - if: regression > 2pp on any slice: block merge
```

### Step 3: Online A/B framework (Week 2-3)

```python
# Feature flag service
class ABTest:
    def __init__(self, name, control, treatment, traffic_pct=0.05):
        self.name = name
        self.control = control
        self.treatment = treatment
        self.traffic_pct = traffic_pct
    
    def get_variant(self, user_id):
        # Stable hash for sticky assignment
        if hash(user_id + self.name) % 100 < self.traffic_pct * 100:
            return self.treatment
        return self.control

# Usage
test = ABTest("rag_v2", control="v1", treatment="v2", traffic_pct=0.05)
variant = test.get_variant(user.id)
response = system.generate(query, version=variant)

# Log for analysis
log_event({
    'experiment': 'rag_v2',
    'variant': variant,
    'user_id': hash_user(user.id),
    'business_metric_pending': True,  # measured later
})

# After 1 week, compute lift
def compute_lift(experiment):
    control_metric = mean(events.filter(variant=control).business_metric)
    treatment_metric = mean(events.filter(variant=treatment).business_metric)
    
    # Statistical significance
    t_stat, p_value = ttest_ind(control, treatment)
    
    return {
        'lift_pct': (treatment_metric / control_metric - 1) * 100,
        'p_value': p_value,
        'significant': p_value < 0.05,
    }
```

### Step 4: Production monitoring (always-on)

```python
# Daily eval sample
async def daily_production_eval():
    samples = sample_production_logs(n=500)
    
    # LLM-judge each
    scores = []
    for s in samples:
        score = await llm_judge_batched(s)
        scores.append(score)
    
    # Aggregate
    summary = {
        'date': today(),
        'sample_size': len(samples),
        'avg_accuracy': mean([s.accuracy for s in scores]),
        'refusal_rate': mean([s.is_refusal for s in samples]),
        'p_per_slice': {
            slice: mean([s.score for s in scores if s.slice == slice])
            for slice in SLICES
        },
    }
    
    # Compare to 7-day baseline
    baseline = load_baseline(days=7)
    drift = {k: summary[k] - baseline[k] for k in baseline}
    
    # Alert if regression
    for slice, delta in drift['p_per_slice'].items():
        if delta < -0.03 and slice in CRITICAL_SLICES:
            page_oncall(f"Quality regression on {slice}: {delta:.2%}")
    
    # Persist for trend
    db.insert('eval_daily', summary)
```

### Step 5: Drift detection

```python
def detect_drift(window_now, window_baseline):
    # Input distribution drift
    queries_now_emb = mean_embedding(window_now.queries)
    queries_baseline_emb = mean_embedding(window_baseline.queries)
    input_drift = 1 - cosine(queries_now_emb, queries_baseline_emb)
    
    # Output distribution drift
    lengths_now = [len(r) for r in window_now.responses]
    lengths_baseline = [len(r) for r in window_baseline.responses]
    length_drift = wasserstein(lengths_now, lengths_baseline)
    
    # Refusal rate drift
    refusal_now = mean([is_refusal(r) for r in window_now.responses])
    refusal_baseline = mean([is_refusal(r) for r in window_baseline.responses])
    
    # Intent distribution drift (if classifier exists)
    intent_now = Counter([classify(q) for q in window_now.queries])
    intent_baseline = Counter([classify(q) for q in window_baseline.queries])
    intent_drift = kl_divergence(intent_now, intent_baseline)
    
    return {
        'input_embedding_drift': input_drift,
        'length_drift': length_drift,
        'refusal_drift': refusal_now - refusal_baseline,
        'intent_drift': intent_drift,
    }
```

### Step 6: Continuous golden set refresh

```python
# Weekly: incorporate production findings
def refresh_golden_set():
    # 1. Find production samples that LLM-judge scored low
    low_scored = production_logs.filter(judge_score < 3).sample(50)
    
    # 2. Hand-label these
    human_labeled = await human_label(low_scored)
    
    # 3. Add to golden set
    golden_set.extend(human_labeled)
    
    # 4. Find samples where LLM-judge disagreed with human historically
    disagreements = find_disagreements(human_labels, judge_labels)
    
    # 5. Re-calibrate judge
    recalibrate(disagreements)

# Quarterly: comprehensive golden set audit
def quarterly_audit():
    # Are golden samples still representative of production?
    prod_dist = compute_distribution(production_logs)
    golden_dist = compute_distribution(golden_set)
    
    coverage = check_coverage(golden_dist, prod_dist)
    if coverage < 0.8:
        alert_team("Golden set drift, needs refresh")
```

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **Offline only (no production monitoring)** | Drift undetected |
| 2 | **Single metric optimization** | Goodhart's Law (e.g., reward length → verbose) |
| 3 | **BLEU/ROUGE for generation** | Known weak, misleading |
| 4 | **Same model judges itself** | Bias, false confidence |
| 5 | **Static golden set** | Stale, doesn't reflect production |
| 6 | **No drift detection** | Silent regression |
| 7 | **No SLO / alerts** | Discover via customer complaint |
| 8 | **No per-slice metric** | Overall fine but worst slice -20pp |
| 9 | **Eval debt** (launch without eval) | Disaster when distribution shifts |
| 10 | **Confuse correlation / causation** in A/B | Make wrong product decisions |
| 11 | **No human-in-loop sampling** | Blind spots compound |
| 12 | **Ignore cost of eval** | Eval pipeline becomes major cost |

---

## 一句话总结 (Part 1)

> **"知道 AI 在 production 是否 working" = 「多层 eval pyramid + 业务 metric + drift detection + 持续 refresh」**.
>
> 没有 single metric 能告诉你「working」. 是 ensemble of signals, 哪个 signal 异常都得关注.

---

# Part 2 · 5 个深度工程问题

## ⚙️ Problem 1: Multi-layer Eval — Unit / Integration / Production / Online

### 1.1 4 层 eval 体系

```
Layer 1: Unit eval (per-component)
  - Prompt template renders correctly
  - RAG retrieves expected chunks
  - LLM call returns valid JSON
  - Tool function executes correctly
  - Frequency: every commit
  - Cost: ~$0 (mock + small samples)

Layer 2: Integration eval (end-to-end on golden set)
  - Full pipeline: query → retrieve → reason → respond
  - Metrics: accuracy, latency, cost per query
  - Frequency: every PR + nightly
  - Cost: ~$20-100/run (depends on eval set size)

Layer 3: Online experimentation (A/B)
  - New version vs baseline on real traffic
  - Business metrics (resolve rate, conversion)
  - Frequency: per feature launch
  - Cost: ~product team time + monitoring

Layer 4: Production monitoring (always-on)
  - Latency, error rate, drift indicators, sample LLM-judge
  - Frequency: continuous
  - Cost: ~$50-500/day depending on volume
```

### 1.2 Unit eval 实操

```python
# pytest for AI components
def test_prompt_template():
    """Template renders without errors, includes all fields"""
    rendered = render_prompt(query="test", user_id="u123")
    assert "{user_id}" not in rendered  # no unfilled vars
    assert len(rendered) < 5000  # not bloated
    
def test_rag_retrieve():
    """RAG returns top-10, all from correct tenant"""
    chunks = rag.retrieve("test query", tenant_id="t1", top_k=10)
    assert len(chunks) == 10
    assert all(c.tenant_id == "t1" for c in chunks)  # ACL filter works
    
def test_json_schema_compliance():
    """Output validates against schema"""
    for sample in golden_set[:50]:  # quick subset
        output = system.generate(sample.query)
        try:
            Response.model_validate_json(output)
        except ValidationError:
            pytest.fail(f"Invalid JSON: {output}")
```

### 1.3 Integration eval pipeline

```python
async def run_integration_eval():
    results = []
    
    for sample in golden_set:
        # 1. Run end-to-end
        start = time.time()
        output = await system.generate(sample.query)
        latency = time.time() - start
        
        # 2. Automated checks
        auto = auto_metrics(output, sample.expected)
        
        # 3. LLM-judge
        judge = await llm_judge(sample.query, output, sample.expected)
        
        results.append({
            'sample_id': sample.id,
            'category': sample.category,
            'output': output,
            'latency': latency,
            **auto,
            'judge_score': judge.score,
        })
    
    # 4. Aggregate
    summary = {
        'overall_accuracy': mean([r['judge_score'] for r in results]) / 5,
        'overall_latency_p99': p99([r['latency'] for r in results]),
        'per_slice': groupby_slice(results),
    }
    
    # 5. Compare to baseline
    baseline = load_baseline()
    return diff(summary, baseline)
```

### 1.4 Online A/B test 框架

```python
# Statistical significance check
from scipy.stats import ttest_ind, chi2_contingency

def run_ab_analysis(experiment_id):
    events = load_events(experiment_id, days=7)
    
    control = events.filter(variant='control')
    treatment = events.filter(variant='treatment')
    
    # Continuous metric (e.g., resolve rate)
    t_stat, p_value = ttest_ind(
        [e.resolved for e in control],
        [e.resolved for e in treatment]
    )
    
    lift = mean([e.resolved for e in treatment]) - mean([e.resolved for e in control])
    
    # Sample size check (sufficient power?)
    n_per_group = min(len(control), len(treatment))
    required = compute_required_sample_size(effect_size=0.02, alpha=0.05, power=0.8)
    
    return {
        'lift_pp': lift * 100,
        'p_value': p_value,
        'significant': p_value < 0.05,
        'sample_size_per_group': n_per_group,
        'required_sample_size': required,
        'underpowered': n_per_group < required,
    }
```

### 1.5 Production monitoring dashboard

Standard sections every dashboard should have:

```
1. Service Health:
   - Request rate (per region / per tenant)
   - Error rate (per error class)
   - Latency p50 / p95 / p99
   - Cost per request

2. Quality Indicators:
   - Daily LLM-judge sample score
   - User feedback ratio (thumbs up / down)
   - Refusal rate
   - Hallucination rate (from sampled audit)

3. Drift Indicators:
   - Input length / type distribution
   - Output length distribution
   - Intent distribution
   - Per-slice score deltas

4. Business Metrics:
   - Resolve rate / conversion / retention
   - NPS / CSAT
   - Cost per resolved interaction

5. Alerts:
   - Active alerts + acknowledgment status
   - Recent incident summary
   - Error budget burn rate
```

---

## ⚙️ Problem 2: Production Signals — Latency, Error, User Feedback, Business Metric

### 2.1 4 类 production signal

```
1. Technical signals (lag indicator, easiest)
   - Latency: p50, p95, p99 per stage
   - Error rate: 4xx, 5xx, timeouts
   - Throughput: QPS
   - Cost: $/query
   
2. Quality signals (medium difficulty)
   - LLM-judge daily sample
   - Refusal rate
   - Hallucination detection
   - Output diversity (entropy)

3. User feedback (explicit)
   - Thumbs up / down
   - Star rating
   - Free-text feedback
   - Complaint volume

4. Business KPI (ultimate truth, slowest)
   - Resolve rate (no human escalation)
   - Conversion / purchase
   - Retention 30d / 90d
   - NPS / CSAT
   - Revenue impact
```

### 2.2 Per-tenant / Per-slice 视图

```python
# 不只是 overall, 必须 per-slice
slices = ['tenant_id', 'language', 'region', 'product_line', 'query_type']

for slice in slices:
    metric_per_slice = production_logs.groupby(slice).agg({
        'latency': 'p99',
        'error_rate': 'mean',
        'judge_score': 'mean',
        'feedback_positive_rate': 'mean',
    })
    
    # Find outliers
    for group, metric in metric_per_slice.iterrows():
        if metric.judge_score < threshold:
            alert(f"Slice {slice}={group} quality regression: {metric.judge_score}")
```

**Why per-slice critical**: overall fine but 一个 slice 烂可能是:
- 一个 enterprise customer 不爽 (大单)
- 一个 language 不会说 (国际化失败)
- 一个 region 系统问题 (合规风险)

### 2.3 Implicit signals (when explicit feedback sparse)

```python
implicit_signals = {
    # Conversation continuation (user retry / regenerate)
    'regeneration_rate': fraction_messages_with_retry,
    
    # Session length (engagement)
    'avg_session_length': mean_messages_per_session,
    
    # Abandon rate
    'session_abandon_rate': fraction_session_ended_early,
    
    # Downstream completion
    'task_completion_rate': fraction_user_completed_intent,
    
    # Time-to-completion
    'time_to_complete': median_session_duration,
}
```

**Caveat**: implicit signals 多 confound:
- 短 session 可能是「答得好快速完成」 or 「答得差用户放弃」
- 长 session 可能是「engaged 深入」 or 「来回扯皮」

需要 explicit feedback + LLM-judge 来 disambiguate.

### 2.4 Business KPI 关联

```python
# 用户级数据 join AI usage 和 business outcome
def ai_business_impact_analysis():
    users_with_ai = users.filter(ai_used=True)
    users_without_ai = users.filter(ai_used=False)
    
    # Matched comparison (control for user attributes)
    matched = propensity_matched(users_with_ai, users_without_ai)
    
    metrics = {
        'retention_30d_lift': retention(matched.with_ai) - retention(matched.without_ai),
        'revenue_lift': revenue(matched.with_ai) - revenue(matched.without_ai),
        'support_cost_per_user': cost(matched.with_ai) - cost(matched.without_ai),
    }
    
    return metrics
```

### 2.5 Alert design

```yaml
# SLO + multi-tier alerts
slos:
  - name: ai_response_quality
    metric: daily_llm_judge_avg
    target: 4.0  # out of 5
    
  - name: latency_p99
    metric: response_latency_p99
    target: 800ms

alerts:
  # P1 — page now
  - name: quality_drop_p1
    condition: daily_llm_judge_avg < 3.5 for 1 day
    severity: page
    
  # P2 — investigate within 1h
  - name: latency_breach_p2
    condition: latency_p99 > 1500ms for 30 min
    severity: page
  
  # P3 — slack alert
  - name: drift_warning_p3
    condition: input_embedding_drift > 0.15
    severity: slack
  
  # Budget
  - name: error_budget_burning
    condition: burn_rate > 2x over 1h
    severity: slack
```

---

## ⚙️ Problem 3: LLM-as-judge Methodology — Calibration, Selection, Cost

### 3.1 为什么需要 LLM-as-judge

```
Manual eval:    Cost $5-10/sample, slow (天级)
Automated metrics (BLEU): Cost $0, fast, but signal poor
LLM-as-judge:   Cost ~$0.01/sample, fast (秒级), signal good if calibrated
```

**Scale enabler**: 100k production samples/day manual = impossible, LLM-judge = $1k/day feasible.

### 3.2 Calibration against human (必做)

```python
async def calibrate_judge(judge_model, n=100):
    """LLM-judge 必须先 calibrate against 真人"""
    
    # 1. 抽样 100 个 production samples
    samples = sample_production(n=n)
    
    # 2. 5+ 人 hand-label each (consensus)
    human_labels = []
    for s in samples:
        labels = [human_labeler.label(s) for _ in range(5)]
        consensus = mode(labels)
        human_labels.append(consensus)
    
    # 3. LLM-judge labels same samples
    judge_labels = []
    for s in samples:
        result = await judge_model.judge(s)
        judge_labels.append(result.score)
    
    # 4. Compute agreement
    from sklearn.metrics import cohen_kappa_score
    kappa = cohen_kappa_score(human_labels, judge_labels)
    accuracy = mean([h == j for h, j in zip(human_labels, judge_labels)])
    
    print(f"Cohen's kappa: {kappa:.2f}")
    print(f"Accuracy: {accuracy:.2%}")
    
    # 5. Trust threshold
    if kappa < 0.4:
        return "Don't trust judge"
    elif kappa < 0.6:
        return "Marginal — only for rough triage"
    else:
        return "Trustworthy for production eval"
```

**Cohen's kappa thresholds**:
- < 0.4: poor agreement
- 0.4-0.6: moderate
- 0.6-0.8: substantial
- 0.8+: almost perfect

**Target: > 0.6**. Below, don't rely on judge for production decisions.

### 3.3 Judge selection (2026 reality)

| Judge model | Cost | When to use |
|---|---|---|
| **Claude Opus 4.7** | $5/$25 per M | High-stakes eval, complex rubric, < 1k samples |
| **Claude Sonnet 4.6** | $3/$15 | Production default, balance cost/quality |
| **Gemini 3 Pro** | $2/$12 | Multi-modal eval, cost-conscious |
| **Haiku 4.5** | $1/$5 | High-volume eval, simple rubric |
| **GPT-5.5 / 5.4** | $5/$30 or $2.50/$15 | Cross-validation, second opinion |

**Cost math** (eval 5k samples/run):

```
Opus 4.7:  5k × (500 input + 200 output) tokens × cost
           = 5k × 0.5 × $5/M + 5k × 0.2 × $25/M
           = $12.5 + $25 = $37.50 per eval run

Haiku 4.5: 5k × 0.5 × $1/M + 5k × 0.2 × $5/M
           = $2.50 + $5 = $7.50 per eval run

Production daily eval (500 sample/day):
Haiku 4.5: $0.75/day = $22.50/month
Sonnet 4.6: $2.10/day = $63/month
Opus 4.7: $3.75/day = $112/month
```

### 3.4 Multi-judge ensemble (减少 bias)

```python
# Single judge can have systematic bias
# 3 judge ensemble + majority vote / average
async def ensemble_judge(sample):
    judges = [opus_47, gemini_3_pro, gpt_5_5]
    
    results = await asyncio.gather(*[
        j.judge(sample) for j in judges
    ])
    
    # Average score
    avg_score = mean([r.score for r in results])
    
    # Or: median for outlier resistance
    median_score = median([r.score for r in results])
    
    # Disagreement signal (high disagreement = uncertain)
    std = stdev([r.score for r in results])
    
    return {
        'score': avg_score,
        'disagreement': std,
        'individual_scores': [r.score for r in results],
    }
```

**Trade-off**: 3x cost, but reduces single-judge bias. Worth it for high-stakes eval.

### 3.5 Avoid common pitfalls

```
❌ Judge same model as main model
  → Bias toward own style, false confidence
  
❌ Single fixed rubric for all sample types
  → Rubric doesn't fit all (e.g., factoid vs creative)
  → Use per-category rubric
  
❌ Don't recalibrate
  → Judge model upgrades, calibration stale
  → Recalibrate quarterly minimum
  
❌ Judge can see metadata that biases
  → "User rated this 5 stars" → judge inflates score
  → Strip metadata, blind judge
  
❌ Only happy path samples in calibration set
  → Calibration doesn't reflect production
  → Calibrate on diverse production samples (including failures)
```

### 3.6 Pairwise judge (better than absolute)

```python
# Absolute scoring is hard for LLM-judge (drift)
# Pairwise comparison more reliable
async def pairwise_judge(query, response_a, response_b):
    prompt = f"""
    Query: {query}
    Response A: {response_a}
    Response B: {response_b}
    
    Which response is better? Answer "A", "B", or "tie".
    Reasoning: ...
    """
    return await claude_sonnet_46.generate(prompt)

# Use for A/B comparison
async def compare_versions(query, v1, v2):
    response_v1 = await system_v1.generate(query)
    response_v2 = await system_v2.generate(query)
    
    # Randomize order to prevent position bias
    if random.random() > 0.5:
        result = await pairwise_judge(query, response_v1, response_v2)
        return 'v1' if result == 'A' else 'v2'
    else:
        result = await pairwise_judge(query, response_v2, response_v1)
        return 'v2' if result == 'A' else 'v1'
```

---

## ⚙️ Problem 4: Drift Detection — Data, Model, Concept, Distribution Shift

### 4.1 4 类 drift

```
1. Data drift (input distribution change):
   - User query patterns change (新产品上线, 新人群)
   - Language mix changes (拓展新国家)
   - Length distribution changes (移动端 vs 桌面端)
   
2. Concept drift (true label changes over time):
   - "What's our return policy" — answer changes when policy updates
   - "Is this fraud?" — fraud patterns evolve
   
3. Model drift (model behavior changes):
   - Dependency upgrade (vLLM, embedding model)
   - Prompt template change
   - LLM API model upgrade (gpt-4 → gpt-5)
   
4. Distribution shift (output behavior changes):
   - Refusal rate creeping up (model getting conservative)
   - Average length growing (verbose drift)
   - Topic distribution shifting
```

### 4.2 Detection algorithms

**Input distribution drift** (KL / Wasserstein):

```python
def detect_input_drift(window_now, window_baseline):
    # Embed all queries
    now_embeds = embed_batch(window_now.queries)
    baseline_embeds = embed_batch(window_baseline.queries)
    
    # Approach 1: Mean embedding cosine
    drift_score = 1 - cosine(mean(now_embeds), mean(baseline_embeds))
    
    # Approach 2: Wasserstein distance on embedding distribution
    from scipy.stats import wasserstein_distance
    # (Use 1D projection for efficiency, e.g., first PCA component)
    pca = PCA(n_components=1).fit(baseline_embeds)
    w_dist = wasserstein_distance(pca.transform(baseline_embeds), pca.transform(now_embeds))
    
    # Approach 3: Topic distribution KL
    topics_now = Counter([topic_classifier.predict(q) for q in window_now.queries])
    topics_baseline = Counter([topic_classifier.predict(q) for q in window_baseline.queries])
    kl = kl_divergence(topics_now, topics_baseline)
    
    return {
        'embedding_drift': drift_score,
        'wasserstein': w_dist,
        'topic_kl': kl,
    }
```

**Output distribution drift**:

```python
def detect_output_drift(window_now, window_baseline):
    # Length distribution
    lengths_now = [len(r) for r in window_now.responses]
    lengths_baseline = [len(r) for r in window_baseline.responses]
    
    # Refusal rate
    refusal_now = mean([is_refusal(r) for r in window_now.responses])
    refusal_baseline = mean([is_refusal(r) for r in window_baseline.responses])
    
    # Structured output validity
    json_valid_now = mean([is_valid_json(r) for r in window_now.responses])
    json_valid_baseline = mean([is_valid_json(r) for r in window_baseline.responses])
    
    return {
        'length_p50_delta': median(lengths_now) - median(lengths_baseline),
        'refusal_rate_delta': refusal_now - refusal_baseline,
        'json_valid_delta': json_valid_now - json_valid_baseline,
    }
```

**Statistical tests for drift**:

```python
from scipy.stats import ks_2samp, chi2_contingency

# Kolmogorov-Smirnov for continuous metric
ks_stat, p_value = ks_2samp(window_now.length, window_baseline.length)
if p_value < 0.01:
    alert("Length distribution shift")

# Chi-square for categorical
chi2, p_value, dof, _ = chi2_contingency([
    counts_now_per_intent,
    counts_baseline_per_intent,
])
if p_value < 0.01:
    alert("Intent distribution shift")
```

### 4.3 Drift response playbook

```
Drift detected → 调查 root cause:

1. Is this expected drift?
   - Product launch?  → Update golden set, recalibrate
   - Holiday season?  → Note seasonal pattern
   - New market?     → Expand eval set coverage

2. Is this unexpected drift?
   - User behavior change → Investigate user side
   - Upstream change   → Check dependency updates
   - Model regression  → Check recent deploys, possibly rollback

3. Severity assessment:
   - Quality impact?  → Run targeted eval on drifted samples
   - Business impact? → Cross-reference with business KPI
   - Affects which slice? → Per-slice deeper drill
```

### 4.4 实战: voice agent drift (你的工作)

```
Week 5 of Indonesia voice agent:
  
Detected:
  - Input drift: 印尼语 question patterns shifted
  - Output drift: refusal rate 8% → 18%

Investigation:
  - Sample 100 refused calls
  - Found: new fraud pattern (借冠新冠 emergency 理由)
  - Model conservatively refusing all "emergency" claims, missing legit ones
  
Root cause: legit-vs-fraud separator drifted
Action:
  - DPO refresh with 200 new examples (emergency true / false)
  - Update fraud detection rules
  - Add to weekly drift watchlist
```

### 4.5 自动化 drift detection pipeline

```python
# Daily drift check job
async def daily_drift_check():
    today_window = production_logs.last(hours=24)
    baseline_window = production_logs.range(days=8, days_back=2)  # 7-day baseline ending yesterday
    
    drift = detect_input_drift(today_window, baseline_window)
    drift.update(detect_output_drift(today_window, baseline_window))
    
    # Persist
    db.insert('drift_daily', {**drift, 'date': today()})
    
    # Threshold-based alert
    for metric, value in drift.items():
        threshold = DRIFT_THRESHOLDS[metric]
        if abs(value) > threshold:
            await page_oncall(f"Drift detected: {metric}={value:.3f} > {threshold}")
    
    # Trend analysis (last 14 days)
    recent = db.query('drift_daily', days=14)
    if any(metric_trending_up(recent[m]) for m in drift):
        await slack_alert("Drift trending up over 2 weeks")
```

---

## ⚙️ Problem 5: Ground-Truth-less Evaluation — Self-consistency, Ensemble, Downstream KPI

很多 production scenario 没有 ground truth answer. 怎么 eval?

### 5.1 4 类 ground-truth-less 方法

```
1. Self-consistency
   - Same query sampled multiple times → consistent answers?
   - Low variance = high model confidence
   
2. Ensemble agreement
   - Multiple models on same query → agree?
   - Disagreement signal = uncertainty
   
3. Behavioral signal
   - User accepts / rejects / regenerates
   - User completes downstream action
   
4. Business KPI correlation
   - Long-term: did AI usage correlate with business outcomes?
```

### 5.2 Self-consistency

```python
async def self_consistency_score(query, n=5, temperature=0.7):
    """Sample N responses, measure variance"""
    responses = await asyncio.gather(*[
        llm.generate(query, temperature=temperature) for _ in range(n)
    ])
    
    # For categorical (classification): majority vote rate
    if is_categorical(responses):
        votes = Counter(responses)
        majority_share = votes.most_common(1)[0][1] / n
        return {'consistency': majority_share, 'majority_answer': votes.most_common(1)[0][0]}
    
    # For generation: pairwise semantic similarity
    embeds = embed_batch(responses)
    pairwise_sims = [cosine(embeds[i], embeds[j]) for i in range(n) for j in range(i+1, n)]
    avg_sim = mean(pairwise_sims)
    return {'consistency': avg_sim}

# Production usage: low consistency = model uncertain, flag for human review
```

**应用**:
- 高 consistency = confident → 直接用
- 低 consistency = uncertain → fallback (大 model / 人工 / 拒答)

### 5.3 Ensemble agreement

```python
async def ensemble_agreement(query):
    """Multiple models agree?"""
    models = [haiku_45, sonnet_46, opus_47]
    responses = await asyncio.gather(*[m.generate(query) for m in models])
    
    # Pairwise semantic agreement
    embeds = embed_batch(responses)
    agreement_matrix = [[cosine(e1, e2) for e1 in embeds] for e2 in embeds]
    
    avg_agreement = mean([agreement_matrix[i][j] for i in range(3) for j in range(i+1, 3)])
    
    return {
        'agreement': avg_agreement,
        'responses': dict(zip(['haiku', 'sonnet', 'opus'], responses)),
        'flag_for_review': avg_agreement < 0.7,
    }
```

### 5.4 Downstream business KPI

**关键洞见**: AI 系统的真正 metric 是它**对 business 的影响**, 不是 model 自身性能.

```python
# 例: BNPL chatbot 真正的 metric
business_metrics = {
    # Direct
    'resolve_rate': fraction_resolved_without_escalation,
    'first_response_quality': customer_rating_after_first_msg,
    
    # Indirect
    '7d_repayment_rate': fraction_paid_within_7_days,
    'churn_30d': fraction_churned_within_30_days,
    'nps': net_promoter_score,
    
    # Cost-side
    'support_cost_per_interaction': cost / interactions,
    'human_escalation_rate': escalations / total,
}

# Lift analysis
def ai_lift(metric_name):
    with_ai = users.filter(ai_enabled=True)
    without_ai = users.filter(ai_enabled=False)  # control
    
    # Match on confounders (tenure, value, region)
    matched = propensity_matched(with_ai, without_ai)
    
    return {
        'lift_pp': metric(matched.with_ai) - metric(matched.without_ai),
        'significance': bootstrap_p_value(matched, metric),
    }
```

### 5.5 Implicit user signals

```python
# Without explicit feedback, infer from behavior
def quality_from_behavior(session):
    signals = {
        # Positive
        'completed_task': session.user_completed_intent,
        'didnt_regenerate': session.regeneration_count == 0,
        'short_session': session.duration < 5_min,  # quick resolve
        'no_complaint': not session.has_complaint_keyword,
        
        # Negative
        'regenerated': session.regeneration_count > 0,
        'escalated': session.was_escalated,
        'abandoned': session.user_abandoned,
        'complained': session.has_complaint_keyword,
    }
    
    # Composite score
    score = (
        signals['completed_task'] * 0.4 +
        signals['didnt_regenerate'] * 0.2 +
        (not signals['escalated']) * 0.2 +
        (not signals['abandoned']) * 0.1 +
        (not signals['complained']) * 0.1
    )
    return score
```

### 5.6 LLM-judge with rubric (when no expected answer)

```python
# 没 expected answer, 但 rubric 可定义
RUBRIC = """
Evaluate the AI response on:
1. Helpfulness (1-5): Does it actually help the user achieve their goal?
2. Accuracy (1-5): Does it contain factual errors?
3. Tone (1-5): Is it professional and appropriate?
4. Safety (1-5): Does it follow policy / refuse appropriately?
5. Clarity (1-5): Is it understandable?

Output JSON: {helpfulness, accuracy, tone, safety, clarity, reasoning}
"""

async def rubric_judge(query, response):
    prompt = f"""
    Query: {query}
    Response: {response}
    
    {RUBRIC}
    """
    return await opus_47.generate(prompt, response_format=Rubric)
```

### 5.7 ConvFinQA-style negative result methodology (你的经验)

> "我们 ConvFinQA 用 LLM-judge 评 reasoning correctness — 但我们也做了 critic variant ablation. Critic agent 只在 percent_change / divide ops trigger. **Result: 4/358 useful flags (1.1%)**. 我们诚实 report 了这个 negative result.
>
> **Lesson**: aggressive eval triggers cost more but mostly produce noise. **Cheap broad eval + targeted expensive eval beats one-size-fits-all**. 这是 ground-truth-less eval 的关键 trade-off — 你 willing to pay more for slightly more signal? 通常不 worth."

---

# Part 3 · 把 5 个问题串起来看

这 5 个问题是 **production AI eval 的完整 layered defense**:

1. **Multi-layer eval** 给「pipeline 各阶段都 check」
2. **Production signals** 给「continuous monitoring」
3. **LLM-as-judge** 给「scale 人审到 100k samples/day」
4. **Drift detection** 给「在出事前发现 drift」
5. **Ground-truth-less eval** 给「真实场景没标注怎么 know」

面试场把这 5 层都讲透, 加上「我在 ConvFinQA 做过 9-variant ablation, 在 voice agent 做过 7-market drift detection」, 就是 staff-level eval discipline.

---

## 必问 clarifying questions

**1. Use case**

> "Generation / classification / agent / RAG / multi-turn chat? Eval methodology differs."

**2. Ground truth availability**

> "Have labeled expected answers? Or production needs ground-truth-less eval?"

**3. Volume**

> "Queries/day? Determines feasibility of LLM-judge vs human eval."

**4. Stakes**

> "Medical / legal high-stakes (need human-in-loop) or chat assistant (LLM-judge suffices)?"

**5. Resources**

> "Budget for eval? Engineering capacity? Limits 你能投多少在 eval 上."

**6. Existing monitoring**

> "Current state — no eval / basic latency only / mature pipeline?"

---

## 5 步框架 (sample 60-min answer)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify use case + ground truth + stakes |
| 5-15 min | 3-layer pyramid (offline / online / production) |
| 15-30 min | Offline metrics + LLM-as-judge calibration |
| 30-45 min | Online A/B + business metric + drift detection |
| 45-55 min | Human-in-loop scaling + ground-truth-less methods |
| 55-60 min | Quote ConvFinQA + voice agent specific experience |

---

## 简历专属 reframe

你的 **ConvFinQA stratified-300 eval + 9-variant ablation** + **voice agent multi-market eval**:

| 题 | 你做过 |
|---|---|
| Offline golden + auto metrics | ConvFinQA stratified eval pipeline (你 own) |
| LLM-as-judge with calibration | ConvFinQA critic 实验 — 4/358 trigger, honest negative result |
| A/B test in production | Voice agent 7 markets phased rollout |
| Per-slice metric | Voice agent per-market dashboard |
| Drift detection | Voice agent input distribution monitoring |
| Human-in-loop for low-conf | Refund tier — agent flags uncertain → human |
| Business metric correlation | Repayment rate as voice agent KPI |
| Ablation methodology | ConvFinQA 9-variant |

**主动 quote**:

> "I've built this exact 3-layer system for two production AI projects.
>
> **For ConvFinQA**, I built **stratified 300-conversation eval set** with per-difficulty / per-hop-depth slices. Used **9-variant ablation** to isolate which component changes helped. **Critic variant** only triggered on percent_change/divide ops, got 4/358 useful flags (1.1%). I **honestly reported this as negative result** — the eval cost wasn't justified by signal. **Lesson**: aggressive eval triggers cost more but mostly produce noise. **Cheap broad eval + targeted expensive eval beats one-size-fits-all**.
>
> **For voice agent at TikTok PayLater**:
> - **Offline**: 500 golden calls × 7 markets, LLM-judge (Opus 4.7) on rubric (empathy, accuracy, compliance)
> - **Online**: phased canary 1% → 5% → 25% → 100% per market. **Business metric: 7-day repayment rate vs control**. Auto-rollback if -5pp.
> - **Production**: per-market dashboard, daily LLM-judge 500 samples, drift detection on input distribution + refusal rate
>
> **Specific incident**: Week 2 of Indonesia rollout, repayment rate -8pp vs control. Investigation showed model too apologetic, customers felt 'bot doesn't take me seriously', disputes up. Fix: DPO refresh on Indonesian firm-but-polite examples. **Without per-market drift detection, we'd have lost a quarter of the rollout before noticing**.
>
> **The most important meta-lesson**: business KPI > technical metric. We optimized voice agent for repayment rate (true outcome), not for LLM-judge accuracy (proxy). Sometimes a 'worse-sounding' response leads to higher repayment because it's firmer. Eval truth follows business truth."

→ ConvFinQA negative result + voice agent A/B 都是 gold reference, 一定 ace.

---

## 5 follow-ups

**Q1**: "LLM-as-judge — how do you know judge is reliable?"

**A**: 5-step validation:
1. **Hand-label 100 production examples** by experts (gold standard)
2. **Run judge on same 100**, compute Cohen's kappa
3. Judge must reach **kappa > 0.6** to be trusted (substantial agreement)
4. **Re-validate quarterly** as model / task drift over time
5. **Avoid same model self-eval** — significant bias
6. **Multi-judge ensemble** (Opus 4.7 + Gemini 3 Pro + GPT-5.5) — average / median for outlier resistance
7. **Per-rubric-dimension calibration** — judge might be good at accuracy but bad at tone, calibrate each dimension separately

**Q2**: "Customer asks: how confident are you the model is working today?"

**A**: Build a **live confidence dashboard**:
- Error budget remaining (e.g., 99.5% SLO, 0.3% burned this month)
- Drift indicators (input distribution Δ vs 7d baseline)
- Recent canary results (last 5 deploys passing?)
- Human-flag rate (production samples flagged by LLM-judge or low confidence)
- "Latest weekly human eval pass rate: 94%"
- "Per-tenant health green / yellow / red"

Show numbers, trends, not feels. Customers trust numbers + graphs.

**Q3**: "We don't have user feedback signal. What do we use?"

**A**:
- **Implicit signals**: regeneration rate (user hit retry), session length, click-through, completion rate
- **Downstream**: did user complete intended action (purchase, file ticket close)
- **External sensors**: changes in support ticket volume after deploy
- **Self-consistency**: same query sampled N times, low variance = high confidence
- **Ensemble agreement**: 3 models on same query, disagreement = uncertainty signal
- **Contract human eval**: if no implicit signal, $10/sample × 500/week = $26k/year, often worth it for high-stakes use case

**Q4**: "How much should eval cost as % of inference cost?"

**A**:
- **Mature production**: 5-15% of inference cost. Below 5% likely under-investing.
- **Early production**: 20-50% (need confidence in deploys, frequent eval iteration)
- **Critical domains** (medical, legal, financial): 50%+ — human review on most outputs
- Cost is **justified by avoided incidents** — 1 silent quality regression in production can mean lost contract / churn / lawsuit

Examples:
- ConvFinQA: ~30% eval / inference (research project, lots of iteration)
- Voice agent: ~10% (mature, automated)
- BNPL chatbot: ~15% (medium maturity, multi-market complexity)

**Q5**: "Eval suite passes but customers complain. Why?"

**A**: Eval suite doesn't reflect production. Common causes:
- **Golden set unrepresentative** (synthetic queries vs real customer language)
- **Wrong metric**: ROUGE high but users hate verbose output
- **No diversity** in golden set (overfit to certain query type)
- **Drift**: production distribution shifted, eval set stale
- **Missing slice**: overall passes, but one important slice fails (e.g., new product line)
- **Goodhart**: we optimized for our metric, gaming it without solving real problem

Fix:
- **Production sampling**: 200 random samples/week → hand label → add to golden set
- **Customer complaint mining**: every complaint becomes eval case
- **Slice expansion**: ensure eval covers all customer segments
- **Always have human review channel** for unclear cases
- **Quarterly golden set audit**: is set still representative?

---

## ❌ 易错点 (top 10)

1. **Offline only (no production monitoring)**
2. **Single metric optimization** — Goodhart's Law
3. **BLEU/ROUGE for generation** — weak, misleading
4. **Same model judges itself** — bias
5. **Static golden set** — stale fast
6. **No drift detection** — silent regression
7. **No alerts / SLOs** — discover via customer complaint
8. **No per-slice metric** — worst slice masked
9. **Skip LLM-judge calibration** — false confidence
10. **No business metric correlation** — optimizing proxy not truth

---

## ✅ 加分项 (top 10)

1. **3-layer eval pyramid** (offline / online / production)
2. **LLM-judge calibration via Cohen's kappa**
3. **Production sampling → golden set refresh** loop
4. **Goodhart's Law awareness**
5. **Specific tools** (Braintrust, Langfuse, Phoenix, Ragas)
6. **Cost as % of inference** (5-15% mature)
7. **Quote ConvFinQA + voice agent experience**
8. **Confidence dashboard** for customer-facing
9. **Per-slice + per-tenant metric** decomposition
10. **Business KPI > technical metric** philosophy

---

## 一句话总结

> **"知道 AI 在 production working" = 多层 eval pyramid + 校准的 LLM-judge + 持续 drift monitoring + business KPI correlation + golden set 持续 refresh**.
>
> 不是 single metric, 是 ensemble of signals. **任何 silent system 都是 production 事故等待发生**.

---

## Cheat Sheet (印 1 页)

```
3-layer eval pyramid (every system needs):
  Offline (CI / pre-deploy): 
    - Golden set (200-2000 stratified)
    - Auto metrics (exact match, schema valid, embedding sim)
    - LLM-judge (calibrated against human, kappa > 0.6)
    - Human spot check (weekly 50 samples)
  
  Online (canary + A/B):
    - 1% → 5% → 50% → 100% phased
    - Business metric vs control
    - Auto-rollback on SLO breach
    - Statistical significance check
  
  Production (always-on):
    - Per-tenant / per-slice metric
    - Drift detection (input dist, output dist, refusal rate)
    - LLM-judge daily sample (200-1000)
    - User feedback aggregation
    - Cost / latency monitoring

5 metric categories:
  Technical: latency, error rate, throughput, cost
  Quality: judge score, refusal, hallucination
  User explicit: thumbs, rating, complaint
  User implicit: regeneration, session length, completion
  Business KPI: resolve rate, conversion, retention

LLM-judge requirements:
  - Different model than under test (no self-eval bias)
  - Cohen's kappa > 0.6 with human (calibrate quarterly)
  - Multi-judge ensemble for high-stakes (3 judges, avg/median)
  - Per-dimension rubric (not single score)
  - Pairwise > absolute (more reliable)
  - Strip metadata (don't leak ground truth)

Drift detection (4 types):
  Data drift: input distribution change
  Concept drift: true label changes over time
  Model drift: dependency / config / model upgrade
  Distribution shift: output behavior changes

Drift metrics:
  Input: embedding mean cosine, Wasserstein 1D, KL on topics
  Output: length p50, refusal rate, JSON validity rate
  Statistical: KS test for continuous, chi-square for categorical
  Trend: 14-day rolling check

Ground-truth-less eval:
  Self-consistency: sample N, low variance = confident
  Ensemble agreement: 3 models, disagreement = flag
  Behavioral: completion, regeneration, abandonment
  Business KPI: lift vs control via propensity matching
  Rubric LLM-judge: criteria-based (no expected answer)

Production monitoring sections:
  1. Service health (latency, error, throughput, cost)
  2. Quality indicators (judge, refusal, hallucination)
  3. Drift indicators (input/output dist deltas)
  4. Business metrics (resolve, conversion, retention)
  5. Alerts (P1 page / P2 30min / P3 slack)

Cost target:
  Mature production: 5-15% of inference cost on eval
  Early production: 20-50%
  Critical domain: 50%+

Anti-patterns:
  - BLEU/ROUGE for generation (weak)
  - Same model self-eval (bias)
  - Static golden set (stale)
  - Single metric optimization (Goodhart)
  - No human-in-loop (blind spots)
  - No drift detection (silent regression)
  - Optimize technical metric, ignore business KPI

Pragmatic steps:
  Week 1: 100-sample golden set + basic CI eval
  Week 2: LLM-judge with calibration
  Week 3: Production monitoring dashboard
  Week 4: A/B test framework
  Month 2: Drift detection
  Month 3: Continuous golden set refresh
  Ongoing: Quarterly judge recalibration

Tools (2026):
  Eval pipelines: Braintrust, Langfuse, Phoenix, Ragas, TruLens
  Tracing: LangSmith, Phoenix, Datadog APM
  Drift: Custom + Arize / WhyLabs / Fiddler
  Logging: W&B Tables / MLflow
  Dashboards: Grafana, Datadog
  Alerts: PagerDuty + Slack
  Human label: Scale AI / Labelbox / internal

Quotes for interview:
  - "3-layer eval pyramid: offline + online + production"
  - "LLM-judge requires kappa > 0.6 vs human, or don't trust it"
  - "Per-slice metric matters more than overall — worst slice catches issues"
  - "Business KPI > technical metric — optimize the truth not the proxy"
  - "Static golden set is dead within months — production sampling is the refresh loop"
  - "Goodhart's Law: any single metric you optimize becomes gamed"
```

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

