## Q42 · How do you evaluate an LLM beyond "it looks right"?

> "Your model 'looks right' in dev. **How do you actually know it works** when you ship it to a customer's production environment? Walk me through your eval methodology — automated metrics, LLM-as-judge, human review, business KPI. Be specific about what you'd build in week 1 vs month 3."

**中文翻译**:

> "你的模型在开发环境里 '看起来对'. **你到底怎么知道它真的能 work** — 当你把它 ship 到客户的 production 环境之后? 跟我讲讲你的 eval (评估) 方法论 — automated metrics (自动化指标), LLM-as-judge (用大模型当评审), 人工 review, 业务 KPI 这些. 要具体说清楚第 1 周做什么 vs 第 3 个月做什么."

**Round**: AI Specialty (45 min)
**出处**: Exponent 2026 FDE Guide · 公司: OpenAI / Anthropic / Cohere / Scale AI — 分水岭 question. "你怎么知道它真的 работает"

---

## 📖 术语速查 (本题用到的)

> Eval 是 FDE 第二常考题, 术语堆叠. 5 min 扫完再读详解.

### Eval 总论 ⭐

| 术语 | 解释 |
|---|---|
| **3-layer eval pyramid** ⭐ | **Offline (CI 前跑) / Online A/B (canary 比) / Production monitoring (always-on)**. 三层各抓不同 failure, 缺一层 = 有盲区. |
| **Golden set / Eval set** ⭐ | 200-2000 个手标的 (query, expected answer) 对. **每 3 月不 refresh 就 stale**. |
| **Eval debt** | 上线时没 eval set, 6 周后 model 退化也发现不了 — 没 baseline 可比. 早期 FDE 最常踩坑. |
| **Stratified sample** | 按 intent / language / difficulty 分层取样, 确保 eval set 各 slice 都覆盖. |

### Metrics — 知道选哪个

| 术语 | 解释 |
|---|---|
| **BLEU / ROUGE** | 旧式 n-gram 重叠分数 — 翻译/摘要时代用的. **对 LLM generation 几乎无用** (有多种正确答案, BLEU 鼓励冗长). |
| **Recall@10 / NDCG@10 / MRR** | RAG 检索指标. Recall@10 = 正确文档在前 10 个的比例; NDCG = 加权排名好坏; MRR = 第一个正确答案的倒数排名. |
| **F1 / Precision / Recall** | 分类任务标配. F1 = precision/recall 调和均. |
| **Cosine similarity** | 两向量夹角余弦 — semantic 相似度的标准度量, -1 到 1. |
| **Pass@k** | 采样 k 次, 至少一次对就算对. Coding eval 用. |
| **Faithfulness** | RAG 输出有没有 grounding 在 retrieved chunks — hallucination 反指标. |

### LLM-as-Judge ⭐

| 术语 | 解释 |
|---|---|
| **LLM-as-judge** ⭐ | **用一个 LLM 给另一个 LLM 输出打分**. Scale 关键 — 100k 输出人审不起, LLM-judge 0.001/sample. **但必须校准**. |
| **Cohen's kappa** ⭐ | **Inter-rater agreement 系数**. 跟纯靠运气比的 agreement. < 0.4 别信; 0.4-0.6 凑合; **> 0.6 production-ready**; > 0.8 几乎完美 (常说明 overfit). |
| **Inter-rater reliability** | 多个评审之间是否一致. 量化用 Cohen's kappa / Fleiss' kappa (3+ raters). |
| **Pairwise judging** | 给 judge 看 A / B 两个答案问"哪个好". 比 1-5 absolute scoring 更稳 (绝对分会 drift). |
| **Position bias** | Judge 倾向选第一个出现的 — pairwise 必须 randomize 顺序. |
| **Self-eval bias** | Model 给自己输出打高分. **FT'd Sonnet 系统不能用 Sonnet 当 judge**. |
| **Rubric** | 评分标准 (accuracy / completeness / tone / clarity 各一档). 比单分更可解释. |
| **ELO** | 国际象棋评分系统迁移过来 — pairwise battle 多了, 自动给 model 排名. Chatbot Arena 用这个. |

### Online A/B / Canary

| 术语 | 解释 |
|---|---|
| **Canary rollout** ⭐ | 1% → 5% → 25% → 100% 阶梯式. 每阶段观察 metrics, 出 SLO breach 自动 rollback. |
| **A/A test** | 把同一 version 分成两组对比 — 应该没 difference. 校准 A/B 测试系统本身有没有 bias. |
| **Shadow mode** | 新 model 跟旧 model 并跑, 新 model 决策**只记录不生效**. 收数据零风险. |
| **Statistical significance** | p-value < 0.05 才能说 difference 不是偶然. 但**实际 effect 太小 (lift < 1pp) 没业务意义也别 ship**. |
| **Power / MDE** | Power = 测出真 effect 的概率 (target 0.8). MDE = 最小可探测 effect (typical 2pp). Sample size 不够 = underpowered, 测不出真 effect. |
| **Business KPI** | 真业务指标 — resolved rate, conversion, repayment. LLM-judge 是 proxy, business KPI 是 truth. |

### Drift / 持续监控 ⭐

| 术语 | 解释 |
|---|---|
| **Data drift** ⭐ | **输入分布变了** — 用户问的东西变了 (新 product line 上线, 季节性, 营销活动). Embedding cosine / KL divergence 量化. |
| **Concept drift** | **输入 → 输出的 mapping 变了** — 同样的 query 现在该有不同答案 (法规更新, 退款政策改). 更难抓, 因为 input 看起来一样. |
| **Model drift** | Model 行为变化 — 因为 dependency upgrade / config change / vendor model 升级. |
| **Distribution shift** | 总称 — covers data drift + concept drift. |
| **KL divergence** | 两个分布的"距离" — drift 量化常用. |
| **Wasserstein distance** | 类似 KL 但对 sparse 分布更稳. |
| **Per-slice metric** ⭐ | 不只看整体 89%, 看 Indonesia 60% vs 美国 92%. **Worst-slice 是真的 production 风险**. |
| **Goodhart's Law** | "When a measure becomes a target, it ceases to be a good measure" — 优化 ROUGE → model 变冗长, ROUGE 升 user 不爽. |

### 生产 Eval 工具 (2026)

| 术语 | 解释 |
|---|---|
| **Braintrust** | 商业 eval pipeline. 标 ground truth + 跑 eval 套件. |
| **Langfuse** | 开源 LLM 监控 + eval, self-host friendly. |
| **Arize Phoenix** | 开源 LLM observability. Tracing + eval. |
| **LangSmith** | LangChain 的 eval + tracing. |
| **Ragas** | 专门 RAG eval — faithfulness, context relevance, answer correctness. |
| **TruLens** | RAG triad eval (context relevance / groundedness / answer relevance). |
| **PagerDuty** | On-call 告警 routing. Production AI 告警走这个. |

---

## 这道题在考什么

表面是 eval 题, 底下藏着 **8 个 FDE evaluation signal**:

1. **Offline / Online / Production 三层 eval pyramid** — 知道 single metric 不够
2. **Automated metrics 局限** — 知道 BLEU / ROUGE 对 generation 几乎无用
3. **LLM-as-judge methodology** — 知道 calibration (Cohen's kappa > 0.6) + bias risks
4. **Human-in-the-loop scaling** — 怎么 scale 不靠 100% 人审
5. **Drift detection** — 不只是 launch-day metric, 是持续 monitoring
6. **Per-slice metric** — overall fine 但 worst slice 暴雷
7. **Business KPI vs technical metric** — proxy vs truth
8. **Production sampling → golden set refresh** loop — eval set 不是 static

不考「BLEU 是什么」, 考「你 own 过 production AI, sleep at night 靠什么」.

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|---|---|---|
| 1 | **Clarify 5 things** | 3 min | Use case / ground truth / volume / stakes / existing monitoring | "Before I prescribe — what's the use case? Is there ground truth? What's the volume? Stakes?" |
| 2 | **3-layer pyramid** | 5 min | Offline / Online A/B / Production monitoring | "I think about it as a pyramid — 3 layers, each catches different failures." |
| 3 | **Why 'looks right' fails** | 3 min | 5 failure modes (Goodhart, drift, slice, biz proxy mismatch, eval debt) | "Let me show 5 ways 'looks right' lies — Goodhart, distribution shift, masked slice failure, proxy/truth mismatch, eval debt." |
| 4 | **Offline: golden set + auto + LLM-judge + spot** | 7 min | Stratified set, auto metrics, LLM-judge calibration | "Week 1 deliverable: 200-sample golden set stratified by intent / language / difficulty, with LLM-judge calibrated to kappa > 0.6." |
| 5 | **LLM-as-judge methodology** | 5 min | Calibration, ensemble, pairwise, anti-patterns | "Judge methodology has 5 non-negotiables — different model, kappa validated, ensemble for high-stakes, pairwise > absolute, recalibrate quarterly." |
| 6 | **Online A/B + business metric** | 5 min | Canary, phased rollout, statistical significance | "Online: 1% → 5% → 25% → 100% phased. Business metric is the real truth. Auto-rollback on SLO breach." |
| 7 | **Production monitoring + drift** | 5 min | Always-on dashboard, per-slice, drift detection | "Always-on: latency / error / quality / drift / business — 5 sections. Per-tenant per-language per-region slicing." |
| 8 | **Continuous refresh** | 3 min | Production sampling → golden set updates | "Golden set is dead within 3 months without refresh. Weekly production sampling + quarterly comprehensive audit." |
| 9 | **Quote ConvFinQA + voice agent** | 4 min | Specific shipped numbers + negative result | "I shipped this exact system at TikTok. ConvFinQA 9-variant ablation including honest negative result. Voice agent 7-market per-slice dashboard caught Indonesia regression in week 2." |
| 10 | **Cost as % of inference** | 2 min | 5-15% mature, 20-50% early, 50%+ critical | "Mature production runs eval at 5-15% of inference cost. Early or critical domains more. Justified by avoided incidents." |

---

## 详细回答

### Step 1: Why "looks right" fails — 5 failure modes

```
Failure 1: Goodhart's Law
  You optimize for ROUGE → model becomes more verbose (matches reference longer)
  → ROUGE up, user satisfaction down
  
Failure 2: Distribution shift
  Eval set is queries from Q1 / dev team
  Production users from Q3, ask different things
  → eval passes, customers complain

Failure 3: Masked slice failure
  Overall 89% accuracy looks fine
  But Indonesian users 60%, brings everyone else's 92% down
  → 重要 customer 不爽, 但 dashboard 不显示

Failure 4: Proxy/truth mismatch
  LLM-judge says response is "polite and accurate" → 4.5/5
  But user didn't actually take action (didn't pay, didn't convert)
  → 优化了 proxy, 没 move business needle

Failure 5: Eval debt
  Launched without eval set
  6 weeks later: model regression
  No way to know if THIS regression or always was
  No baseline to compare
```

**Conclusion**: "Looks right" 是 single point. 真 reliable eval 是 **layered ensemble of signals**.

### Step 2: The 3-Layer Eval Pyramid

```
                       ┌────────────┐
                       │  Customer  │
                       │  outcomes  │  ← Ultimate truth (business KPI)
                       └────────────┘
                              ▲
                              │
                       ┌────────────┐
                       │  Online    │  ← A/B, real user signal
                       │  A/B test  │     Slow but real
                       └────────────┘
                              ▲
                              │
                       ┌────────────┐
                       │ Production │  ← Always-on, drift, sampled judge
                       │ monitoring │     Lag indicator but continuous
                       └────────────┘
                              ▲
                              │
                       ┌────────────┐
                       │  Offline   │  ← Pre-deploy CI, fast cheap
                       │  golden    │     Controlled but limited coverage
                       └────────────┘
                              ▲
                              │
                       ┌────────────┐
                       │ Unit-level │  ← Per-component, fastest
                       │ component  │     Prompt template, RAG, schema
                       └────────────┘
```

**Each layer catches different failures**:

| Layer | Catches | Misses | Frequency | Cost |
|---|---|---|---|---|
| Unit | Logic bugs, schema breaks | End-to-end behavior | Every commit | $0 |
| Offline golden | Known failure modes | Distribution shift | Every PR | $20-100/run |
| Online A/B | Real user reactions | Long-term effects | Per feature | Time + monitoring |
| Production monitoring | Drift, latency | Subtle quality drops | Continuous | $50-500/day |
| Business KPI | True success | Causality, slow | Weekly | Data analyst time |

### Step 3: Offline eval foundation (Week 1 deliverable)

**Component 1: Stratified golden set**

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class EvalSample:
    id: str
    query: str
    expected: str  # or expected_schema for structured
    category: Literal['factoid', 'reasoning', 'creative', 'classification']
    difficulty: Literal['easy', 'medium', 'hard']
    language: str  # 'en', 'id', 'vi', 'th', 'pt', 'es', 'fr'
    tenant_segment: str  # 'enterprise', 'smb', 'consumer'
    contains_pii: bool
    edge_case: bool

# Stratified construction
def build_golden_set(production_samples, n=200):
    """
    Sample stratified by intent, difficulty, language.
    Include happy path + edge cases proportionally.
    """
    stratify_keys = ['category', 'difficulty', 'language']
    samples_per_stratum = max(5, n // (len(intents) * len(difficulties) * len(languages)))
    
    golden = []
    for cat in CATEGORIES:
        for diff in DIFFICULTIES:
            for lang in LANGUAGES:
                stratum = production_samples.filter(category=cat, difficulty=diff, language=lang)
                sampled = stratum.sample(min(samples_per_stratum, len(stratum)))
                golden.extend(sampled)
    
    # Ensure 20% edge cases
    edge_count = int(n * 0.2)
    edge_samples = production_samples.filter(edge_case=True).sample(edge_count)
    golden.extend(edge_samples)
    
    # Human-label expected outputs (gold standard)
    return [annotate_with_human(s) for s in golden]
```

**Component 2: Automated metrics (limited but cheap)**

```python
def auto_metrics(generated: str, expected: str, sample: EvalSample) -> dict:
    """
    Cheap automated metrics. Useful for structured tasks, weak for generation.
    """
    metrics = {}
    
    # Structured output
    metrics['valid_json'] = is_valid_json(generated)
    metrics['has_required_fields'] = has_required_fields(generated, sample.schema)
    metrics['schema_compliance'] = validate_schema(generated, sample.schema)
    
    # Exact match (only for factoid / classification)
    if sample.category in ('factoid', 'classification'):
        metrics['exact_match'] = generated.strip() == expected.strip()
    
    # Embedding similarity (semantic — better than BLEU)
    metrics['cosine_to_expected'] = cosine(embed(generated), embed(expected))
    
    # Refusal detection
    metrics['is_refusal'] = is_refusal(generated)
    
    # Length sanity
    metrics['length_ratio'] = len(generated) / max(len(expected), 1)
    
    # PII leak check
    metrics['contains_pii'] = detect_pii(generated)
    
    # Citation presence (for RAG)
    metrics['has_citations'] = has_citations(generated)
    
    return metrics
```

**Why not BLEU / ROUGE for generation**:
- Designed for translation / summarization where reference is "the" correct answer
- LLM generation has many valid answers — penalty for not matching exact reference is wrong signal
- High BLEU ≠ user satisfaction (often inverse: BLEU rewards verbose padding)
- **Use for narrow structured tasks only**

**Component 3: LLM-as-judge (the scale enabler)**

```python
async def llm_judge(query, generated, expected=None, rubric=None) -> dict:
    """
    LLM-judge with rubric. Calibrated against human, kappa > 0.6.
    """
    if rubric is None:
        rubric = DEFAULT_RUBRIC
    
    if expected:
        # Reference-based judging
        prompt = f"""
        Query: {query}
        Reference answer: {expected}
        Generated answer: {generated}
        
        Rate the generated answer:
        1. Accuracy (1-5): Does it convey the same factual content?
        2. Completeness (1-5): Does it cover what reference covers?
        3. Tone (1-5): Is it appropriate?
        4. Clarity (1-5): Is it understandable?
        
        Output strict JSON: {{"accuracy": int, "completeness": int, "tone": int, "clarity": int, "reasoning": str}}
        """
    else:
        # Reference-free (rubric-only)
        prompt = f"""
        Query: {query}
        Generated answer: {generated}
        
        {rubric}
        
        Output strict JSON with each dimension score and reasoning.
        """
    
    # CRITICAL: judge must be DIFFERENT model from system under test
    result = await claude_opus_47.generate(prompt, response_format=JudgeResult)
    return result
```

**Component 4: LLM-judge calibration (non-negotiable)**

```python
async def calibrate_judge(judge_model, n=100):
    """
    Validate LLM-judge against human labels. Required before trusting.
    """
    # 1. Sample 100 production examples
    samples = sample_production(n=n)
    
    # 2. 5 human labelers per sample, take consensus (mode)
    human_labels = []
    for s in samples:
        labels = [human_labeler.label(s) for _ in range(5)]
        consensus = mode(labels)
        human_labels.append(consensus)
    
    # 3. LLM-judge labels same samples
    judge_labels = []
    for s in samples:
        result = await judge_model.judge(s)
        judge_labels.append(result.overall_score_bucket)  # discretize for kappa
    
    # 4. Compute agreement
    from sklearn.metrics import cohen_kappa_score, classification_report
    kappa = cohen_kappa_score(human_labels, judge_labels)
    accuracy = mean([h == j for h, j in zip(human_labels, judge_labels)])
    
    # 5. Per-dimension calibration
    per_dim_kappa = {}
    for dim in ['accuracy', 'completeness', 'tone', 'clarity']:
        per_dim_kappa[dim] = cohen_kappa_score(
            [h[dim] for h in human_labels_detailed],
            [j[dim] for j in judge_labels_detailed]
        )
    
    return {
        'overall_kappa': kappa,
        'accuracy': accuracy,
        'per_dim_kappa': per_dim_kappa,
        'trustworthy': kappa > 0.6,
        'recommendations': diagnose_disagreements(human_labels, judge_labels)
    }
```

**Cohen's kappa thresholds**:
- < 0.4: poor agreement, **don't trust judge**
- 0.4-0.6: moderate, **only for rough triage**
- 0.6-0.8: substantial, **production-ready**
- 0.8+: almost perfect (rare, suspect overfitting)

**Target: > 0.6**. Below, don't rely on judge for production decisions. **Recalibrate quarterly** (judge model upgrades, task drift).

### Step 4: LLM-judge methodology — 5 non-negotiables

**1. Different model from system under test (no self-eval bias)**

```
❌ FT'd Sonnet 4.6 system → Sonnet 4.6 judge
   Bias toward own style, false confidence
   
✓ FT'd Sonnet 4.6 system → Opus 4.7 judge OR Gemini 3 Pro judge
```

**2. Calibrated against human (kappa > 0.6)** — covered above.

**3. Multi-judge ensemble for high-stakes**

```python
async def ensemble_judge(sample):
    judges = [opus_47, gemini_3_pro, gpt_5_5]
    
    results = await asyncio.gather(*[j.judge(sample) for j in judges])
    
    avg_score = mean([r.score for r in results])
    median_score = median([r.score for r in results])  # outlier-resistant
    std = stdev([r.score for r in results])
    
    return {
        'score': avg_score,
        'disagreement': std,
        'individual_scores': [r.score for r in results],
        'flag_for_human': std > 1.0,  # high disagreement
    }
```

**Trade-off**: 3x cost. Worth it for high-stakes domains (medical, legal, financial).

**4. Pairwise > absolute scoring**

```python
# Absolute scoring (1-5) drifts over time, hard to calibrate
# Pairwise comparison more reliable

async def pairwise_judge(query, response_a, response_b):
    prompt = f"""
    Query: {query}
    Response A: {response_a}
    Response B: {response_b}
    
    Which response is better? Answer "A", "B", or "tie".
    Reasoning: ...
    """
    return await sonnet_46.generate(prompt)

# For A/B testing model versions
async def compare_versions(query, v1, v2):
    response_v1 = await system_v1.generate(query)
    response_v2 = await system_v2.generate(query)
    
    # CRITICAL: randomize order to prevent position bias
    if random.random() > 0.5:
        result = await pairwise_judge(query, response_v1, response_v2)
        return 'v1' if result == 'A' else 'v2'
    else:
        result = await pairwise_judge(query, response_v2, response_v1)
        return 'v2' if result == 'A' else 'v1'
```

**5. Recalibrate quarterly** + strip metadata that could bias (user ratings, model name, version tags).

### Step 5: Online A/B framework

```python
# Phased canary rollout
class CanaryRollout:
    PHASES = [
        ('canary', 0.01, hours=4),     # 1% for 4 hours
        ('small', 0.05, hours=24),     # 5% for 1 day
        ('medium', 0.25, days=3),      # 25% for 3 days
        ('full', 1.0, None),           # 100%
    ]
    
    async def run(self, experiment_id, control_version, treatment_version):
        for phase_name, traffic_pct, duration in self.PHASES:
            await self.shift_traffic(treatment_version, traffic_pct)
            
            start = now()
            while now() - start < duration:
                metrics = await self.collect_metrics(experiment_id, last_5_min=True)
                
                # Auto-rollback triggers
                if metrics['error_rate'] > 0.05:
                    await self.rollback(experiment_id, reason='error_rate spike')
                    return 'rolled_back'
                
                if metrics['business_kpi_delta'] < -0.05:  # 5pp regression
                    await self.rollback(experiment_id, reason='business KPI regression')
                    return 'rolled_back'
                
                if metrics['latency_p99'] > 2000:
                    await self.rollback(experiment_id, reason='latency breach')
                    return 'rolled_back'
                
                await asyncio.sleep(60)
            
            print(f"Phase {phase_name} complete, advancing")
        
        return 'fully_deployed'

# Statistical significance check
from scipy.stats import ttest_ind

def ab_analysis(experiment_id, days=7):
    events = load_events(experiment_id, days=days)
    
    control = events.filter(variant='control')
    treatment = events.filter(variant='treatment')
    
    # Continuous metric (e.g., resolve rate)
    t_stat, p_value = ttest_ind(
        [e.resolved for e in control],
        [e.resolved for e in treatment]
    )
    
    lift_pp = mean([e.resolved for e in treatment]) - mean([e.resolved for e in control])
    
    # Sample size sufficiency (power 0.8, alpha 0.05, MDE 2pp)
    n_per_group = min(len(control), len(treatment))
    required = compute_required_sample_size(effect_size=0.02, alpha=0.05, power=0.8)
    
    return {
        'lift_pp': lift_pp * 100,
        'p_value': p_value,
        'significant': p_value < 0.05,
        'sample_size_per_group': n_per_group,
        'required_sample_size': required,
        'underpowered': n_per_group < required,
        'recommendation': 'ship' if (p_value < 0.05 and lift_pp > 0) else 'iterate'
    }
```

**Business metric > technical metric** principle:
- Voice agent: 7-day repayment rate > LLM-judge accuracy
- BNPL chatbot: resolved-without-escalation > intent classification F1
- ConvFinQA: financial decision quality > BLEU on answer

### Step 6: Production monitoring + drift detection

**Dashboard sections** (every production AI system needs):

```
1. Service Health:
   - Request rate (per region / per tenant)
   - Error rate (per error class)
   - Latency p50 / p95 / p99 per stage
   - Cost per request

2. Quality Indicators:
   - Daily LLM-judge sample score (500 samples)
   - User feedback ratio (thumbs up / down)
   - Refusal rate trend
   - Hallucination rate (from sampled audit)

3. Drift Indicators:
   - Input length / type distribution Δ vs baseline
   - Output length distribution Δ
   - Intent distribution Δ
   - Per-slice score delta

4. Business Metrics:
   - Resolve rate / conversion / retention
   - NPS / CSAT
   - Cost per resolved interaction

5. Alerts:
   - Active alerts + acknowledgment status
   - Recent incident summary
   - Error budget burn rate
```

**Drift detection (4 types)**:

```python
def detect_drift(window_now, window_baseline):
    # 1. Data drift (input distribution)
    queries_now_emb = mean_embedding(window_now.queries)
    queries_baseline_emb = mean_embedding(window_baseline.queries)
    input_drift = 1 - cosine(queries_now_emb, queries_baseline_emb)
    
    # 2. Output drift
    lengths_now = [len(r) for r in window_now.responses]
    lengths_baseline = [len(r) for r in window_baseline.responses]
    length_drift_pp = (median(lengths_now) - median(lengths_baseline)) / median(lengths_baseline)
    
    # 3. Refusal rate drift (model getting conservative?)
    refusal_delta = mean([is_refusal(r) for r in window_now.responses]) - \
                    mean([is_refusal(r) for r in window_baseline.responses])
    
    # 4. Intent distribution KL
    intent_now = Counter([classify(q) for q in window_now.queries])
    intent_baseline = Counter([classify(q) for q in window_baseline.queries])
    intent_kl = kl_divergence(intent_now, intent_baseline)
    
    return {
        'input_embedding_drift': input_drift,
        'length_drift_pp': length_drift_pp,
        'refusal_delta': refusal_delta,
        'intent_kl': intent_kl,
    }

# Daily job
async def daily_drift_check():
    today = production_logs.last(hours=24)
    baseline = production_logs.range(days=8, days_back=2)  # 7-day baseline
    
    drift = detect_drift(today, baseline)
    db.insert('drift_daily', {**drift, 'date': today_date()})
    
    for metric, value in drift.items():
        threshold = DRIFT_THRESHOLDS[metric]
        if abs(value) > threshold:
            await page_oncall(f"Drift: {metric}={value:.3f} > {threshold}")
```

**Per-slice drift** (overall fine, slice broken):

```python
SLICES = ['language', 'tenant_segment', 'region', 'product_line', 'query_type']

for slice in SLICES:
    metric_per_group = production_logs.groupby(slice).agg({
        'judge_score': 'mean',
        'error_rate': 'mean',
        'business_kpi': 'mean',
    })
    
    for group, metric in metric_per_group.iterrows():
        if metric.judge_score < THRESHOLD:
            alert(f"Slice {slice}={group} quality drop: {metric.judge_score}")
```

### Step 7: Continuous golden set refresh

**Golden set is dead within 3 months** without active refresh.

```python
# Weekly: incorporate production findings
def refresh_golden_set():
    # 1. Find production samples that LLM-judge scored low
    low_scored = production_logs.filter(judge_score < 3).sample(50)
    
    # 2. Hand-label these
    human_labeled = await human_label(low_scored)
    
    # 3. Add to golden set
    golden_set.extend(human_labeled)
    
    # 4. Find LLM-judge / human disagreements
    disagreements = find_disagreements(human_labels, judge_labels)
    
    # 5. Re-calibrate judge on disagreements
    if len(disagreements) > 10:
        recalibrate(disagreements)

# Quarterly: comprehensive audit
def quarterly_audit():
    # Are golden samples still representative?
    prod_dist = compute_distribution(production_logs)
    golden_dist = compute_distribution(golden_set)
    
    coverage = check_coverage(golden_dist, prod_dist)
    if coverage < 0.8:
        alert_team("Golden set drift, needs refresh")
    
    # Are we still measuring the right things?
    review_metrics_alignment_with_business()
```

### Step 8: Eval cost — how much should you spend?

```
Mature production:  5-15% of inference cost on eval
Early production:   20-50%
Critical domain:    50%+ (medical, legal, regulated)

ConvFinQA:         ~30% (research project, lots of iteration)
Voice agent:       ~10% (mature, automated)
BNPL chatbot:      ~15% (multi-market complexity)
```

**Cost is justified by avoided incidents**. 1 silent quality regression = lost contract / churn / lawsuit.

---

## 关键决策 / 框架

### What to eval (5 layers)

```
Layer 1: Per-component unit tests
  - Prompt template renders correctly (no unfilled vars)
  - RAG retrieves expected chunks (ACL respected)
  - JSON schema validates
  - Tool function executes correctly
  - Run: every commit, ~$0

Layer 2: Integration / Offline eval
  - End-to-end on golden set
  - Auto metrics + LLM-judge + spot check
  - Per-slice breakdowns
  - Run: every PR + nightly, ~$20-100

Layer 3: Online A/B
  - Phased canary 1% → 5% → 25% → 100%
  - Business metric vs control
  - Statistical significance + power check
  - Auto-rollback on SLO breach

Layer 4: Production monitoring
  - 5 sections: health, quality, drift, business, alerts
  - Per-slice + per-tenant
  - Continuous, ~$50-500/day

Layer 5: Continuous improvement
  - Weekly golden set refresh
  - Quarterly judge recalibration
  - Quarterly audit (representativeness)
```

### Metric selection by use case

```
Classification (intent routing):
  - Accuracy, F1, confusion matrix
  - Per-class precision/recall
  - Calibration (predicted prob vs actual)

Generation (chat response):
  - LLM-judge on rubric (accuracy, helpfulness, tone)
  - User feedback (thumbs / rating)
  - Behavioral (regeneration, abandonment)
  - Business KPI (resolve rate, conversion)

RAG:
  - Retrieval: recall@10, NDCG@10, MRR
  - Generation: faithfulness, hallucination rate
  - End-to-end: answer correctness, citation accuracy

Agent (tool-using):
  - Per-step success rate
  - End-to-end task completion
  - Tool call accuracy
  - Latency p99, cost per task

Safety / Compliance:
  - Refusal rate on disallowed content
  - PII leak detection
  - Per-jurisdiction policy adherence
```

---

## 完整代码 / 架构图

### Full eval pipeline

```python
# eval/pipeline.py

import asyncio
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class EvalConfig:
    golden_set_path: str
    judge_model: str = 'claude-opus-4-7'
    threshold_overall: float = 0.85
    threshold_per_slice: float = 0.80
    judge_calibration_kappa: float = 0.60

class EvalPipeline:
    def __init__(self, config: EvalConfig):
        self.config = config
        self.golden_set = self._load_golden_set()
        self.judge = init_judge(config.judge_model)
    
    async def run(self, system) -> Dict:
        """Full eval run."""
        # 1. Per-component unit tests
        unit_results = await self._unit_tests(system)
        if not unit_results['all_pass']:
            return {'status': 'fail', 'stage': 'unit', 'details': unit_results}
        
        # 2. Integration eval on golden set
        integration_results = await self._integration_eval(system)
        
        # 3. Per-slice analysis
        slice_results = self._per_slice_analysis(integration_results)
        
        # 4. Compare to baseline
        baseline = self._load_baseline()
        regression_check = self._regression_check(integration_results, baseline)
        
        # 5. Decide pass/fail
        passed = (
            integration_results['overall'] >= self.config.threshold_overall and
            all(s >= self.config.threshold_per_slice for s in slice_results.values()) and
            not regression_check['has_regression']
        )
        
        return {
            'status': 'pass' if passed else 'fail',
            'overall': integration_results['overall'],
            'per_slice': slice_results,
            'regression': regression_check,
            'baseline_delta': integration_results['overall'] - baseline['overall'],
            'samples_evaluated': len(self.golden_set),
        }
    
    async def _integration_eval(self, system) -> Dict:
        results = []
        
        # Parallel evaluation
        async def eval_one(sample):
            start = time.time()
            output = await system.generate(sample.query, context=sample.context)
            latency = time.time() - start
            
            auto = auto_metrics(output, sample.expected, sample)
            judge = await self.judge.judge(sample.query, output, sample.expected)
            
            return {
                'sample_id': sample.id,
                'category': sample.category,
                'language': sample.language,
                'output': output,
                'latency': latency,
                **auto,
                'judge_score': judge.overall,
                'judge_per_dim': judge.per_dim,
            }
        
        # Batch with concurrency control
        sem = asyncio.Semaphore(20)
        async def bounded(sample):
            async with sem:
                return await eval_one(sample)
        
        results = await asyncio.gather(*[bounded(s) for s in self.golden_set])
        
        # Aggregate
        return {
            'overall': mean([r['judge_score'] for r in results]) / 5,
            'latency_p50': p50([r['latency'] for r in results]),
            'latency_p99': p99([r['latency'] for r in results]),
            'auto_metric_summary': aggregate_auto(results),
            'samples': results,
        }
    
    def _per_slice_analysis(self, results) -> Dict:
        slice_dims = ['category', 'language', 'difficulty', 'tenant_segment']
        per_slice = {}
        
        for dim in slice_dims:
            for value in set(s[dim] for s in results['samples']):
                slice_samples = [s for s in results['samples'] if s[dim] == value]
                per_slice[f"{dim}={value}"] = mean([s['judge_score'] for s in slice_samples]) / 5
        
        return per_slice
    
    def _regression_check(self, current, baseline) -> Dict:
        # Per-slice regression check
        regressions = []
        for slice_key, current_score in current['per_slice'].items():
            baseline_score = baseline['per_slice'].get(slice_key, current_score)
            if current_score < baseline_score - 0.02:  # 2pp regression
                regressions.append({
                    'slice': slice_key,
                    'baseline': baseline_score,
                    'current': current_score,
                    'delta_pp': (current_score - baseline_score) * 100
                })
        
        return {
            'has_regression': len(regressions) > 0,
            'regressions': regressions,
        }


# Usage in CI
async def main():
    config = EvalConfig(
        golden_set_path='eval/golden_v3.jsonl',
        threshold_overall=0.85,
        threshold_per_slice=0.80,
    )
    
    pipeline = EvalPipeline(config)
    results = await pipeline.run(system)
    
    if results['status'] == 'fail':
        print(f"FAIL: {results}")
        sys.exit(1)
    
    print(f"PASS: overall={results['overall']:.2%}")
```

### Architecture diagram

```
                    ┌──────────────────────────────────────┐
                    │      Eval Pyramid (Production)       │
                    └──────────────────────────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
        ▼                              ▼                              ▼
┌───────────────┐            ┌───────────────┐            ┌───────────────┐
│   OFFLINE     │            │    ONLINE     │            │  PRODUCTION   │
│   (Pre-PR)    │            │  (A/B test)   │            │  (Always-on)  │
└───────┬───────┘            └───────┬───────┘            └───────┬───────┘
        │                            │                            │
        ▼                            ▼                            ▼
┌───────────────┐            ┌───────────────┐            ┌───────────────┐
│ Golden set    │            │ Canary rollout│            │ Daily judge   │
│ 200 stratified│            │ 1→5→25→100%   │            │ sample 500    │
└───────┬───────┘            └───────┬───────┘            └───────┬───────┘
        │                            │                            │
        ▼                            ▼                            ▼
┌───────────────┐            ┌───────────────┐            ┌───────────────┐
│ Auto metrics  │            │ Business KPI  │            │ Drift detect  │
│ (schema, sim) │            │ vs control    │            │ (4 types)     │
└───────┬───────┘            └───────┬───────┘            └───────┬───────┘
        │                            │                            │
        ▼                            ▼                            ▼
┌───────────────┐            ┌───────────────┐            ┌───────────────┐
│ LLM-judge     │            │ Stat signifi  │            │ Per-slice     │
│ (kappa>0.6)   │            │ + power check │            │ + per-tenant  │
└───────┬───────┘            └───────┬───────┘            └───────┬───────┘
        │                            │                            │
        ▼                            ▼                            ▼
┌───────────────┐            ┌───────────────┐            ┌───────────────┐
│ Human spot    │            │ Auto-rollback │            │ Alerts        │
│ check (50/wk) │            │ on SLO breach │            │ P1/P2/P3      │
└───────────────┘            └───────────────┘            └───────────────┘
        │                            │                            │
        └────────────────────────────┴────────────────────────────┘
                                     │
                                     ▼
                            ┌───────────────────┐
                            │ Weekly refresh    │
                            │ Quarterly audit   │
                            └───────────────────┘
```

---

## Gao Xin 简历专属 reframe

### ConvFinQA — 9-variant ablation + honest negative result

**S**: ConvFinQA multi-hop financial QA. 多 component (RAG + reasoning + tool + critic), 不知道每个 helps how much.

**T**: 设计 eval methodology 能 isolate 每个 component 的 contribution.

**A**: 我设计了 **9-variant ablation**:
- Variant 1: base model only (PE baseline)
- Variant 2: + RAG (knowledge retrieval)
- Variant 3: + tool (calculator)
- Variant 4: + CoT prompt
- Variant 5-7: combinations
- Variant 8: + critic agent (always trigger)
- Variant 9: + critic agent (selectively trigger on percent_change / divide ops only)

Stratified 300-conversation eval set, per-hop-depth slices, per-difficulty slices.

**R**: 
- Variant 9 (selective critic) triggered on 358 reasoning steps
- Caught useful errors on **4/358** (1.1%)
- **Honest negative result**: critic eval cost wasn't justified by signal

**Lesson**: aggressive eval triggers cost more but mostly produce noise. **Cheap broad eval + targeted expensive eval beats one-size-fits-all expensive eval**.

### Voice agent — 7-market per-slice dashboard caught Indonesia regression

**S**: Voice agent deployed across 7 markets (印尼 / 越南 / 泰国 / 菲律宾 / 巴西 / 墨西哥 / 巴基斯坦).

**T**: Continuous quality monitoring without 100% human review.

**A**: 
- **Offline**: 500 golden calls per market × 7 = 3500 stratified
- **LLM-judge**: Opus 4.7 on rubric (empathy, accuracy, compliance), calibrated kappa = 0.72
- **Online**: phased canary 1% → 5% → 25% → 100% per market
- **Business metric**: 7-day repayment rate vs control (auto-rollback if -5pp)
- **Production**: per-market dashboard, daily 500 judge samples, drift on input dist + refusal rate

**R**: Week 2 of Indonesia rollout, **repayment rate -8pp vs control** caught by canary monitoring. Investigation: model too apologetic, customers felt "bot doesn't take me seriously", disputes up. Fix: DPO refresh on Indonesian firm-but-polite examples. **Without per-slice monitoring, would have lost a quarter before noticing**.

### BNPL chatbot — composite confidence + 4-signal escalation

**S**: BNPL chatbot 70% intent routing accuracy. PM wanted 90%+.

**T**: Get routing to 90% without retraining (too expensive).

**A**: Built **4-signal composite confidence**:
1. LLM-reported confidence (calibrated against historical accuracy)
2. Top-1 vs top-2 probability margin
3. RAG retrieval score (NDCG@5)
4. Self-consistency (sample 3, agreement rate)

Composite = weighted sum, threshold tuned on held-out set.

**R**: Accuracy 70 → 92% by escalating bottom 8% to human. **Composite confidence outperformed any single signal**. Calibration story (Brier score) showed predicted probabilities matched actual accuracy within 2pp across deciles.

### Pakistan ASR cascade — 40-minute outage incident eval

**S**: Voice agent in Pakistan. ASR API (third-party) had intermittent 40-min outage during peak hours.

**T**: Detect and respond fast.

**A**:
- **Detection**: drift dashboard caught ASR confidence drop in 3 minutes
- **Triage**: per-region dashboard isolated to Pakistan only
- **Mitigation**: failover to backup ASR provider (latency 1.5x but functional)
- **Comm**: status update to Pakistan ops team within 8 minutes
- **Postmortem**: action items — multi-vendor fallback policy, faster detection threshold

**R**: 40-min outage with only ~12% calls affected (vs 100% if no failover). MTTR 8 min vs typical 30+ min.

---

## 5 个 Follow-ups

**Q1**: "LLM-as-judge — how do you know judge is reliable?"

**A**: 6-step validation:
1. **Hand-label 100 production examples** by experts (gold standard, 5 labelers per sample, take consensus)
2. **Run judge on same 100**, compute Cohen's kappa
3. Judge must reach **kappa > 0.6** to be trusted (substantial agreement)
4. **Re-validate quarterly** as model / task drift over time
5. **Avoid same model self-eval** — significant bias toward own style
6. **Multi-judge ensemble** (Opus 4.7 + Gemini 3 Pro + GPT-5.5) for high-stakes — average / median for outlier resistance
7. **Per-rubric-dimension calibration** — judge might be good at accuracy but bad at tone

**Q2**: "Customer asks: how confident are you the model is working today?"

**A**: Build a **live confidence dashboard**:
- Error budget remaining (e.g., 99.5% SLO, 0.3% burned this month)
- Drift indicators (input distribution Δ vs 7d baseline — currently +0.04, below 0.10 threshold)
- Recent canary results (last 5 deploys passing? Latest deploy 3 days ago, +1.2pp on judge)
- Human-flag rate (production samples flagged by LLM-judge or low confidence — 2% this week, baseline 2.1%)
- "Latest weekly human eval pass rate: 94%, baseline 93%"
- "Per-tenant health: 18 green / 2 yellow / 0 red"

Show numbers, trends, not feels. Customers trust numbers + graphs.

**Q3**: "We don't have user feedback signal. What do we use?"

**A**:
- **Implicit signals**: regeneration rate (user hit retry), session length, click-through, completion rate
- **Downstream**: did user complete intended action (purchase, file ticket close)
- **External sensors**: changes in support ticket volume after deploy
- **Self-consistency**: same query sampled N times, low variance = high confidence
- **Ensemble agreement**: 3 models on same query, disagreement = uncertainty signal
- **Contract human eval**: if no implicit signal, $10/sample × 500/week = $26k/year, often worth it for high-stakes use case
- **LLM-judge rubric**: criteria-based (helpfulness, accuracy, tone, safety, clarity) without expected answer

**Q4**: "How much should eval cost as % of inference cost?"

**A**:
- **Mature production**: 5-15% of inference cost. Below 5% likely under-investing.
- **Early production**: 20-50% (need confidence in deploys, frequent eval iteration)
- **Critical domains** (medical, legal, financial): 50%+ — human review on most outputs
- Cost is **justified by avoided incidents** — 1 silent quality regression in production can mean lost contract / churn / lawsuit

**Cost math example** (BNPL chatbot, 100k queries/day):
- Inference: ~$15k/month (Sonnet 4.6 + RAG)
- Eval: ~$2k/month (daily 500 judge samples at Opus 4.7 × $4 + 10% human spot check)
- Eval / inference = ~13% ✓ healthy range

**Q5**: "Eval suite passes but customers complain. Why?"

**A**: Eval suite doesn't reflect production. Common causes:
- **Golden set unrepresentative** (synthetic queries vs real customer language)
- **Wrong metric**: ROUGE high but users hate verbose output
- **No diversity** in golden set (overfit to certain query type)
- **Drift**: production distribution shifted, eval set stale
- **Missing slice**: overall passes, but one important slice fails (e.g., new product line, new tenant)
- **Goodhart**: we optimized for our metric, gaming it without solving real problem

**Fix**:
- **Production sampling**: 200 random samples/week → hand label → add to golden set
- **Customer complaint mining**: every complaint becomes eval case
- **Slice expansion**: ensure eval covers all customer segments
- **Always have human review channel** for unclear cases
- **Quarterly golden set audit**: is set still representative?

---

## ❌ 死路答法

1. **BLEU / ROUGE only** — weak for generation, misleading
2. **Same model judges itself** — bias toward own style, false confidence
3. **Single overall metric** — masks per-slice failures
4. **Static golden set** — stale within 3 months
5. **Offline only, no production monitoring** — drift undetected
6. **No business KPI correlation** — optimizing proxy, not truth
7. **No alerts / SLOs** — discover via customer complaint
8. **Skip LLM-judge calibration** — judge may be biased / unreliable
9. **No human-in-loop** — blind spots compound
10. **Optimize technical metric, ignore business outcome** — Goodhart's Law

---

## ✅ 加分项

1. **3-layer eval pyramid** (offline / online / production) with concrete tools
2. **LLM-judge calibration via Cohen's kappa > 0.6** — quantitative trust threshold
3. **Production sampling → golden set refresh** loop — keeps eval honest
4. **Goodhart's Law awareness** — explicit anti-pattern
5. **Specific tools** (Braintrust, Langfuse, Phoenix, Ragas, TruLens, LangSmith) — 2026 specificity
6. **Cost as % of inference** (5-15% mature) — budget framing
7. **Quote ConvFinQA negative result + voice agent A/B + BNPL composite confidence**
8. **Confidence dashboard for customer-facing** — trust transparency
9. **Per-slice + per-tenant decomposition** — overall fine ≠ all slices fine
10. **Business KPI > technical metric** philosophy

---

## 一句话总结

> **"知道 AI 在 production working" = 多层 eval pyramid + 校准的 LLM-judge (kappa > 0.6) + 持续 drift monitoring + business KPI correlation + golden set 持续 refresh. 不是 single metric, 是 ensemble of signals. Any silent system 都是 production 事故等待发生.**

---

## Cheat Sheet

```
3-layer eval pyramid:
  Offline (CI / pre-deploy): 
    - Stratified golden set 200-2000
    - Auto metrics (schema, sim, refusal)
    - LLM-judge (kappa > 0.6 vs human)
    - Human spot check 50/week
  
  Online (canary + A/B):
    - 1% → 5% → 25% → 100% phased
    - Business metric vs control
    - Auto-rollback on SLO breach
    - Statistical significance + power check
  
  Production (always-on):
    - Per-tenant / per-slice metric
    - Drift detection (input/output/refusal/intent)
    - LLM-judge daily 500 samples
    - User feedback aggregation
    - Cost / latency monitoring

5 metric categories:
  Technical: latency, error rate, throughput, cost
  Quality: judge score, refusal, hallucination
  User explicit: thumbs, rating, complaint
  User implicit: regeneration, session length, completion
  Business KPI: resolve rate, conversion, retention, NPS

LLM-judge methodology:
  - Different model from system under test
  - Cohen's kappa > 0.6 with human (calibrate quarterly)
  - Multi-judge ensemble for high-stakes (3 judges)
  - Pairwise > absolute (more reliable)
  - Strip metadata (no ground truth leak)
  - Per-dimension rubric not single score

Drift detection (4 types):
  Data drift: input distribution change
  Concept drift: true label changes over time
  Model drift: dependency / config / model upgrade
  Distribution shift: output behavior changes

Drift metrics:
  Input: embedding mean cosine, Wasserstein 1D, KL on topics
  Output: length p50, refusal rate, JSON validity rate
  Statistical: KS test continuous, chi-square categorical
  Trend: 14-day rolling check

Production monitoring (5 sections):
  1. Service health
  2. Quality indicators
  3. Drift indicators
  4. Business metrics
  5. Alerts (P1 page / P2 30min / P3 slack)

Cost target:
  Mature production: 5-15% of inference cost
  Early production: 20-50%
  Critical domain: 50%+

Tools 2026:
  Eval pipelines: Braintrust, Langfuse, Phoenix, Ragas, TruLens
  Tracing: LangSmith, Phoenix, Datadog APM
  Drift: Custom + Arize / WhyLabs / Fiddler
  Logging: W&B Tables / MLflow
  Dashboards: Grafana, Datadog
  Alerts: PagerDuty + Slack
  Human label: Scale AI / Labelbox / internal

Pragmatic timeline:
  Week 1: 100-sample golden set + basic CI eval
  Week 2: LLM-judge with calibration (kappa > 0.6)
  Week 3: Production monitoring dashboard
  Week 4: A/B test framework
  Month 2: Drift detection
  Month 3: Continuous golden set refresh
  Ongoing: Quarterly judge recalibration

Anti-patterns:
  - BLEU/ROUGE for generation
  - Same model self-eval
  - Static golden set
  - Single metric optimization (Goodhart)
  - No human-in-loop
  - No drift detection
  - Optimize proxy not truth

Case studies:
  - ConvFinQA: 9-variant ablation + 4/358 honest negative result
  - Voice agent: 7-market per-slice dashboard, Indonesia week-2 catch
  - BNPL: 4-signal composite confidence, 70→92% via escalation
  - Pakistan ASR: 40-min outage, MTTR 8 min via drift detection

Quotes for interview:
  - "3-layer pyramid: offline + online + production"
  - "LLM-judge needs kappa > 0.6 vs human, or don't trust it"
  - "Per-slice > overall — worst slice catches issues"
  - "Business KPI > technical metric — optimize truth not proxy"
  - "Static golden set is dead within 3 months — production sampling is refresh loop"
  - "Goodhart's Law: any single metric you optimize becomes gamed"
  - "Eval cost 5-15% of inference is healthy"
```
