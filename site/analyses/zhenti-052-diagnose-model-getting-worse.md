## Q52 · Model is getting worse over time — diagnose

> "Customer reports their AI feature 'feels worse' than 2 months ago. **Same model, same prompts, but quality has degraded.** Walk me through your diagnosis methodology — hypotheses with priors, stratified eval, common causes, and how you isolate variables."

**中文翻译**:

> "客户反馈说他们的 AI feature '感觉比 2 个月前差了'. **模型没换, prompt 没改, 但质量明显下降了.** 跟我讲讲你的诊断方法论 — 几个假设各自的 prior (先验概率) 是多少, 怎么做 stratified eval (分层评估), 常见原因, 还有怎么 isolate variables (隔离变量)."

**Round**: Production / Reliability (45 min)
**出处**: Exponent 2026 FDE Guide · 公司: OpenAI / Anthropic / Cohere / Scale AI — production AI drift 必问

---

## 📖 术语速查 (本题用到的)

> Model drift 题. 涉及 ML 监控 + 统计 + Bayesian 思维.

### Drift 类型 ⭐

| 术语 | 解释 |
|---|---|
| **Model drift** ⭐ | **Vendor 偷偷更新了 underlying model**. GPT-5.3 → 5.4 没说. 同 API call 行为变了. **2026 最常见的"突然变差"原因**. |
| **Data drift** ⭐ | **输入分布变了** — 用户问题类型变了. 新 product line / 季节 / 营销活动. |
| **Concept drift** ⭐ | **输入 → 输出的 mapping 变了**. 同 query 现在该有不同答案 (法规更新). 比 data drift 难抓. |
| **Distribution shift** | 总称 — 包 data + concept drift. |
| **Covariate shift** | 输入分布变, 但 conditional p(y|x) 不变. = pure data drift. |
| **Label shift / Prior shift** | 类别比例变了 (e.g. fraud rate 涨了). |
| **Prompt drift** ⭐ | **有人改了 prompt** 没走 review. Git log 能查. |
| **Eval drift** | Rubric / judge model 升级 → 同输出新分不同. |
| **Baseline shift** | 用户期望变高了 — model 没变差, 但 "feels worse" 是 expectation up. |
| **Silent drift** | 没 alert 触发的 drift — 渐进式. 最危险. |

### Drift 检测指标 ⭐

| 术语 | 解释 |
|---|---|
| **KL divergence** ⭐ | **两分布的"距离"**. Drift 量化常用. 0 = 一样, 大 = 偏离多. |
| **Wasserstein / KS test / Chi-square** | 类似 KL 不同场景 — 连续 / sparse / categorical 分布. |
| **Embedding mean cosine** | 输入 embedding 平均的 cosine drift. Semantic shift 抓手. |
| **Population Stability Index (PSI)** | 金融常用. > 0.25 = 严重 drift. |
| **Refusal rate drift** | Model 越来越保守? Refusal % 涨 = 信号. |

### Bayesian / Prior 思维 ⭐

| 术语 | 解释 |
|---|---|
| **Prior probability** ⭐ | **某假设的先验概率** — "model drift 是因, 40% prior". 没数据前的 belief. |
| **Posterior probability** | 收了 evidence 后的概率. Posterior = prior × likelihood / normalize. |
| **Bayesian thinking** | 用 prior + evidence 更新 belief. 不是 binary. |
| **Likelihood** | 假设 H 为真时, 看到这个 evidence 的概率. |
| **Hypothesis-driven debug** | 列假设 + 测每个 — 比 trial-and-error 高效. |
| **Ablation** | 单变量改, 看影响. |
| **Variable isolation** | 一次只动一个 variable, 其他固定. |
| **Confounding variable** | 跟原因混淆的变量. e.g. deploy 跟 query growth 同时发生 → 哪个是因? |

### Eval / 测量 ⭐

| 术语 | 解释 |
|---|---|
| **Vintage golden set** ⭐ | **2 月前的 eval set, 现在重跑**. 如果分掉了 → model 真变差. |
| **Regression eval** | 改动后跑老 eval, 看 metric 退化没. |
| **Stratified eval** ⭐ | 按 slice (language / intent / tenant) 拆开看. 整体 OK 但某 slice 挂. |
| **Per-segment metric** | 跟 stratified eval 同义. |
| **A/A test** | 同 version 分两组 — 应该无差异. 校准 A/B 系统. |
| **Vintage queries vs new queries** | 老 query 重跑 vs 新 query 测 — 隔离 data drift vs model drift. |
| **Time-of-day pattern** | Drift 跟时段相关? Peak hour traffic 不同? |

### 监控 / Observability ⭐

| 术语 | 解释 |
|---|---|
| **Continuous monitoring** | 一直 monitoring, 不是点状测. |
| **Drift detection** | 自动检测 drift 的 alert system. |
| **Golden set refresh** | Eval set 持续更新. 不 refresh 3 月就 stale. |
| **Per-slice dashboard** ⭐ | **按 language / region / tenant 拆的 dashboard**. Worst slice catch issue. |
| **Canary monitoring** | 1-5% 流量先 ship, 看 metric. |
| **A/B against old version** | 跟之前 stable version 实时比. |
| **Shadow mode** | 新 version 跟旧并跑, 新只记录. |

### Vendor 升级 / API ⭐

| 术语 | 解释 |
|---|---|
| **API model version pinning** ⭐ | **指定 model version (gpt-5.5-2025-12)** 而不是 alias (gpt-5.5). Vendor 升级不影响你. |
| **Model alias / Latest tag** | "gpt-4o" 这种, 跟着 vendor 自动升. 危险. |
| **Deprecation notice** | Vendor 通知某 model 要废. 通常 30-90 天 notice. |
| **Silent model update** | Vendor 没说就改了. Anthropic / OpenAI 一般会说, 但 minor patch 可能没说. |
| **Vendor changelog** | Vendor 的 model 更新记录. Production 必 subscribe. |

### 质量 metric + Prevention ⭐

| 术语 | 解释 |
|---|---|
| **Hallucination rate / Faithfulness** | 编造比例 / 输出是否 grounded. RAG 重点 track. |
| **Refusal rate** | 拒答比例. 涨 = 太保守了 — vendor 升级常见症状. |
| **Verbosity / Tone drift** | 输出长度 / 风格变了 — model 升级最 visible. |
| **Regression eval on every change** | CI 跑 golden set. |
| **Pin model version** ⭐ | 不用 latest alias. 防 silent upgrade. |
| **Drift alert** | KL > 0.1 时 page. |
| **Customer perception survey** | 季度问客户 "feels worse?" — baseline shift 唯一抓手. |

---

## 这道题在考什么

表面是 model drift 题, 底下藏着 **8 个 FDE evaluation signal**:

1. **Hypothesis-driven debug** — 不是改一堆 things, 是 isolating 一个 variable
2. **5 hypothesis categories** — data / prompt / model / eval / baseline drift
3. **Bayesian prior thinking** — 知道哪个原因最常见 (prior)
4. **Stratified eval methodology** — 不只是 overall, 是 by-segment
5. **Variable isolation** — A/B with vintage queries vs new queries, etc.
6. **2026 reality** — vendor silently updates underlying model
7. **Customer perception vs reality** — "feels worse" may be users got better
8. **Specific shipped diagnoses** — voice agent Indonesia, BNPL Anthropic model upgrade

不考「model drift 是什么」, 考「customer 说 it's worse, 你 30 分钟内 diagnose 出 5 个可能原因, 各 prior 多少」.

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|---|---|---|
| 1 | **Validate "feels worse"** | 3 min | Subjective vs measured | "First — is this measured or anecdotal? 'Feels worse' could mean different things. Let me ask 5 questions." |
| 2 | **5 hypothesis categories with priors** | 5 min | Data / prompt / model / eval / baseline drift | "5 hypotheses, ranked by my priors — model drift (40%, vendor sneaky), data drift (25%), prompt drift (20%), eval drift (10%), baseline shift (5%)." |
| 3 | **Diagnosis methodology** | 5 min | Stratified eval by date / segment / variable | "Methodology: stratified eval — current vs historical baselines, by segment, isolate which variable changed." |
| 4 | **Hypothesis 1: Model drift** | 5 min | Vendor silently updated underlying | "Most common — vendor updated model. API users hit silent quality changes. Test: regression suite on vintage golden set." |
| 5 | **Hypothesis 2: Data drift** | 4 min | Query distribution shifted | "User questions changed. Test: compare query distribution today vs 2 months ago. Embedding mean cosine drift." |
| 6 | **Hypothesis 3: Prompt drift** | 4 min | Someone edited prompt | "Someone edited prompt (often without ticket). Test: diff system prompt vs 2 months ago. Audit git log." |
| 7 | **Hypothesis 4: Eval drift** | 3 min | Rubric / judge changed | "Eval methodology changed. Test: re-score 2-month-old samples with current rubric." |
| 8 | **Hypothesis 5: Baseline shift** | 3 min | Users / customers got better, "worse than expected" | "Users learned the system, expectations raised. Test: customer survey, compare to 2-month perception." |
| 9 | **Quote BNPL Anthropic model upgrade + voice agent fraud drift** | 5 min | Real stories | "BNPL: Anthropic upgraded GPT-5.3 → 5.4 silently, response style changed. Voice agent: Indonesia fraud patterns shifted, refusal rate creeped up." |
| 10 | **Prevention going forward** | 2 min | Continuous monitoring + golden set + change detection | "Prevention — continuous monitoring, regression eval on every change, vendor change notifications, drift detection." |

---

## 详细回答

### Step 1: Validate "feels worse"

```
Before debugging, validate:

1. Is it measured or anecdotal?
   - Specific metric drop? By how much?
   - User feedback? How many users?
   - Customer complaint? Specific examples?

2. When did it start?
   - Specific date? Gradual decline?
   - Coincides with deploys? Vendor updates?
   - Today only? 2 weeks ago? 2 months ago?

3. What "worse" means?
   - Accuracy drop?
   - Tone change?
   - Slower / latency?
   - Refusal rate up?
   - Hallucination rate up?

4. Who's affected?
   - All users? Subset?
   - Specific language?
   - Specific use case?
   - Specific tenant?

5. Has anything else changed?
   - Our deploys?
   - Model versions?
   - Vendor announcements?
   - User base growth?
```

**Common mistake**: jumping to "we need to retrain" before validating it's actually worse + identifying which dimension.

### Step 2: 5 Hypothesis Categories with Priors

```
Hypothesis 1: MODEL DRIFT (vendor updated)
  Prior: 40% (highest)
  Why: vendors update API models without notice (sometimes), or with announcement
       that customers miss. 2026 reality.
  Evidence: 
    - Started right after vendor announcement
    - Affects all queries equally (not just specific subset)
    - Output style / tone / verbosity changed
  
Hypothesis 2: DATA DRIFT (query distribution shifted)
  Prior: 25%
  Why: customer's user base changed. New product launched, new feature, 
       new market. Queries today are different from queries 2 months ago.
  Evidence:
    - Query distribution KL divergence high
    - New query types (intents) appearing
    - Per-old-intent metrics still good, overall down
  
Hypothesis 3: PROMPT DRIFT (someone edited prompt)
  Prior: 20%
  Why: prompt was edited, often by someone not on your team, without 
       regression test.
  Evidence:
    - Git log shows prompt change
    - Decline correlates with prompt change date
    - Specific use cases affected (changed prompt subsection)
  
Hypothesis 4: EVAL DRIFT (rubric / judge changed)
  Prior: 10%
  Why: eval methodology evolved, new rubric is stricter or different.
  Evidence:
    - Same outputs scored differently on old vs new rubric
    - Eval set changed (samples added that shift distribution)
    - LLM-judge upgraded (different model, different bias)
  
Hypothesis 5: BASELINE SHIFT (users got better)
  Prior: 5%
  Why: users learned the system, expectations raised. Actually no quality 
       drop, just relative perception.
  Evidence:
    - Measured metrics flat
    - User satisfaction down despite quality flat
    - "It used to wow me, now feels normal"
```

**Priors based on 2026 production reality** — model drift biggest because API users hit it without notice.

### Step 3: Diagnosis methodology — stratified eval

**Don't just run "overall accuracy now vs 2 months ago"** — stratify by every possible variable.

```python
async def stratified_eval_compare(current_date, baseline_date):
    """Compare current vs 2-month baseline, stratified by every dimension."""
    
    results = {}
    
    # 1. Overall comparison
    current_metric = await eval_on_period(current_date)
    baseline_metric = await eval_on_period(baseline_date)
    results['overall_delta'] = current_metric - baseline_metric
    
    # 2. By segment
    for dim in ['language', 'tenant', 'product_line', 'query_type', 'difficulty']:
        for value in get_values(dim):
            current_filtered = await eval_on_period(current_date, **{dim: value})
            baseline_filtered = await eval_on_period(baseline_date, **{dim: value})
            results[f'{dim}_{value}_delta'] = current_filtered - baseline_filtered
    
    # 3. By query vintage
    # Use 2-month-old queries on current model
    old_queries = await load_queries(date_range=baseline_date - timedelta(days=7), date_range_end=baseline_date)
    current_on_old = await eval_current_model(old_queries)
    
    # Use today's queries on current model
    new_queries = await load_queries(date_range=current_date - timedelta(days=7), date_range_end=current_date)
    current_on_new = await eval_current_model(new_queries)
    
    results['old_queries_now'] = current_on_old
    results['new_queries_now'] = current_on_new
    
    # If old_queries_now is also down → model drift (not data drift)
    # If old_queries_now is fine but new_queries_now is down → data drift
    
    # 4. By prompt version (if multi-version A/B)
    # Compare current prompt vs prompt from 2 months ago
    
    return results
```

**Variable isolation pattern**:

```
To test Model drift:
  Take 2-month-old queries
  Run them on current model
  Compare to 2-month-old scores
  If lower → model changed

To test Data drift:
  Take 2-month-old queries
  Run on current model
  Compare to today's queries on current model
  If old queries score higher → user data changed

To test Prompt drift:
  Take same query
  Run on current prompt vs old prompt (same model)
  Compare outputs
  If different style → prompt changed

To test Eval drift:
  Take 2-month-old outputs
  Score with current eval / current rubric
  Compare to 2-month-old scores
  If lower → eval changed (output unchanged)

To test Baseline shift:
  Survey users on satisfaction now vs perceptions 2 months ago
  Compare measured metrics vs survey
  If metrics flat but survey down → baseline shifted
```

### Step 4: Hypothesis 1 — Model drift (most common)

**Vendor silently updates underlying model**. 2026 reality.

```
Examples of model drift I've seen:

1. OpenAI updates GPT-5.3 → 5.4 with same API endpoint name
   - Old: terse, factual responses
   - New: verbose, includes caveats
   - Same prompt, different output style
   - Users complain "AI is being chatty"

2. Anthropic updates Claude Sonnet 4.5 → 4.6
   - Subtle reasoning improvement
   - But refusal rate up 2pp
   - Some queries previously answered now refused
   - Affects guardrails — broader refusal

3. Vendor changes tokenizer
   - Prompts that were 4000 tokens now 4200 tokens
   - Hit context window limits
   - Truncation behavior changes

4. Vendor changes default temperature / safety filters
   - Output diversity changes
   - More "I cannot answer" responses
```

**Detection**:

```python
async def detect_model_drift(api_provider, model_name):
    """Run regression suite on vintage golden set."""
    # 1. Vintage golden set (frozen 2 months ago)
    golden = load_golden_set('v3_dated_2026_03_20')
    
    # 2. Current responses
    current_results = []
    for sample in golden:
        response = await api_provider.generate(
            model=model_name,
            prompt=sample.prompt,
            **sample.params
        )
        current_results.append(response)
    
    # 3. Compare to frozen baseline responses (saved 2 months ago)
    drift_metrics = {}
    for sample, current_resp in zip(golden, current_results):
        baseline_resp = sample.frozen_response_2_months_ago
        
        # Embedding similarity (semantic)
        emb_sim = cosine(embed(current_resp), embed(baseline_resp))
        
        # Length ratio
        len_ratio = len(current_resp) / max(len(baseline_resp), 1)
        
        # Refusal flag
        is_refusal = is_refusal_response(current_resp)
        was_refusal = is_refusal_response(baseline_resp)
        
        drift_metrics[sample.id] = {
            'emb_sim': emb_sim,
            'len_ratio': len_ratio,
            'refusal_change': is_refusal and not was_refusal,
        }
    
    # 4. Aggregate
    return {
        'avg_emb_sim': mean([m['emb_sim'] for m in drift_metrics.values()]),
        'avg_len_ratio': mean([m['len_ratio'] for m in drift_metrics.values()]),
        'refusal_drift_pp': mean([m['refusal_change'] for m in drift_metrics.values()]) * 100,
        'recommendation': interpret(drift_metrics)
    }

def interpret(drift_metrics):
    avg_emb = mean([m['emb_sim'] for m in drift_metrics.values()])
    if avg_emb < 0.85:
        return "Strong model drift — different semantic outputs"
    if mean([m['len_ratio'] for m in drift_metrics.values()]) > 1.5:
        return "Model becoming more verbose"
    if mean([m['refusal_change'] for m in drift_metrics.values()]) > 0.05:
        return "Refusal rate increased — model getting conservative"
    return "Minor drift, within normal variance"
```

**Mitigation if model drift confirmed**:

1. **Roll back to previous version** (if vendor offers — Anthropic version pinning)
2. **Pin model version explicitly** going forward (e.g., `claude-3-5-sonnet-20241022` vs latest)
3. **Subscribe to vendor change announcements** (Discord, mailing list)
4. **Multi-vendor for diversification** (cushion against single-vendor drift)
5. **Re-tune prompt** for new model (sometimes prompts need updating per version)

### Step 5: Hypothesis 2 — Data drift

```python
async def detect_data_drift(current_date, baseline_date):
    """Has user query distribution changed?"""
    
    # 1. Sample queries from both periods
    current_queries = await sample_queries(date_range=current_date)
    baseline_queries = await sample_queries(date_range=baseline_date)
    
    # 2. Embedding-based drift
    current_embeds = await embed_batch(current_queries)
    baseline_embeds = await embed_batch(baseline_queries)
    
    drift_score = 1 - cosine(mean(current_embeds), mean(baseline_embeds))
    
    # 3. Topic distribution drift
    current_intents = await classify_batch(current_queries)
    baseline_intents = await classify_batch(baseline_queries)
    
    current_dist = Counter(current_intents)
    baseline_dist = Counter(baseline_intents)
    intent_kl = kl_divergence(current_dist, baseline_dist)
    
    # 4. Length distribution
    current_lengths = [len(q) for q in current_queries]
    baseline_lengths = [len(q) for q in baseline_queries]
    length_shift = median(current_lengths) - median(baseline_lengths)
    
    # 5. New intents emerging
    new_intents = set(current_intents) - set(baseline_intents)
    
    # 6. Old intents disappearing
    disappeared_intents = set(baseline_intents) - set(current_intents)
    
    return {
        'embedding_drift': drift_score,
        'intent_distribution_kl': intent_kl,
        'length_shift': length_shift,
        'new_intents': list(new_intents),
        'disappeared_intents': list(disappeared_intents),
        'recommendation': interpret_data_drift(drift_score, intent_kl, new_intents)
    }
```

**Per-intent breakdown**:

```python
# Even if overall metrics down, check per-intent
async def per_intent_quality(period):
    queries_by_intent = group_queries_by_intent(await sample_queries(period))
    
    quality_per_intent = {}
    for intent, queries in queries_by_intent.items():
        responses = await eval_responses(queries)
        quality_per_intent[intent] = {
            'sample_size': len(queries),
            'avg_score': mean([r.score for r in responses]),
            'pct_of_total_volume': len(queries) / sum(len(q) for q in queries_by_intent.values())
        }
    
    return quality_per_intent
```

**Interpretation patterns**:

```
If per-old-intent metrics still good, but overall down:
  → Data drift confirmed
  → New intents poorly handled
  → Action: extend FT / RAG corpus to cover new intents

If per-old-intent metrics also down:
  → Not data drift alone, likely model drift or prompt drift
  → Need other tests
```

### Step 6: Hypothesis 3 — Prompt drift

```python
# Audit prompt changes
def audit_prompt_changes(prompt_repo, period_start, period_end):
    """Git log analysis."""
    changes = git_log(prompt_repo, 
                      since=period_start, 
                      until=period_end,
                      paths=['prompts/'])
    
    return [{
        'commit': c.sha,
        'date': c.date,
        'author': c.author,
        'files_changed': c.files,
        'lines_added': c.lines_added,
        'lines_removed': c.lines_removed,
        'commit_msg': c.message,
    } for c in changes]

# Comparison test
async def compare_prompts(query, prompt_v1, prompt_v2, model):
    """Same query on both prompts, compare outputs."""
    response_v1 = await model.generate(prompt_v1.format(query=query))
    response_v2 = await model.generate(prompt_v2.format(query=query))
    
    return {
        'response_v1': response_v1,
        'response_v2': response_v2,
        'semantic_similarity': cosine(embed(response_v1), embed(response_v2)),
        'length_ratio': len(response_v1) / max(len(response_v2), 1),
    }
```

**Common prompt drift patterns**:

```
Pattern 1: PM added new instruction without test
  "Add 'be more concise' to system prompt"
  → Model truncates responses
  → User complaints "AI is curt"

Pattern 2: New team member rewrote prompt for "clarity"
  → Different output style
  → Tests don't cover all use cases

Pattern 3: Prompt template variable broke
  → Variable not filled (e.g., {user_name} → literally "{user_name}")
  → Model confused by literal placeholder

Pattern 4: System prompt got too long
  → Added 5 new instructions over 2 months
  → Model loses focus on original task
  → "Prompt creep"
```

### Step 7: Hypothesis 4 — Eval drift

```python
# Did the eval methodology change?
async def re_eval_old_samples_with_current_rubric(old_samples, current_rubric):
    """Re-score 2-month-old samples with current rubric."""
    results = []
    for sample in old_samples:
        # Use the OLD output (saved 2 months ago)
        old_output = sample.frozen_output_2_months_ago
        
        # Score with CURRENT rubric / judge
        new_score = await judge_current.judge(sample.query, old_output, rubric=current_rubric)
        
        # Compare to score it got 2 months ago with OLD rubric / judge
        old_score = sample.frozen_score_2_months_ago
        
        results.append({
            'sample_id': sample.id,
            'old_score': old_score,
            'new_score': new_score,
            'delta': new_score - old_score,
        })
    
    avg_delta = mean([r['delta'] for r in results])
    
    if abs(avg_delta) > 0.1:
        return f"Eval drift confirmed — same output scored differently. Avg delta: {avg_delta:+.2f}"
    return "Eval rubric stable, drift not from eval"
```

**Common eval drift patterns**:

```
- LLM-judge model upgraded (Sonnet 4.5 → 4.6 → 4.7)
  - Different bias, scores shifted
- Rubric refined (added new dimensions, weights changed)
- Eval set added new edge cases (overall distribution shifted)
- Human labelers changed (different consistency)
```

### Step 8: Hypothesis 5 — Baseline shift

```python
# Customer / user perception drift
async def survey_user_satisfaction(period):
    surveys = await fetch_surveys(period)
    
    return {
        'avg_csat': mean([s.csat for s in surveys]),
        'avg_nps': mean([s.nps for s in surveys]),
        'common_complaints': top_complaints(surveys),
    }

# Compare measured metrics vs perceived
def metric_vs_perception_gap():
    measured_now = quality_metric_now  # e.g., 88%
    measured_baseline = quality_metric_2mo_ago  # e.g., 87%
    
    perceived_now = user_satisfaction_now  # e.g., 3.8/5
    perceived_baseline = user_satisfaction_2mo_ago  # e.g., 4.4/5
    
    if abs(measured_now - measured_baseline) < 0.02:
        # Quality flat
        if abs(perceived_now - perceived_baseline) > 0.3:
            # Perception dropped
            return "Baseline shift — users got better, expectations raised"
```

**Baseline shift management**:
- It's a real form of drift (relative to user expectations)
- Mitigation: communicate progress vs absolute
- Or: actually improve to match new expectations (treat as legitimate signal)

---

## 关键决策 / 框架

### 5-hypothesis priors (memorize)

```
Most likely first:
  1. Model drift (40%) — vendor sneaky updates
  2. Data drift (25%) — user queries changed
  3. Prompt drift (20%) — someone edited
  4. Eval drift (10%) — rubric / judge changed
  5. Baseline shift (5%) — users got better
```

### Variable isolation pattern (the key technique)

```
To diagnose what changed, hold one variable constant:

Test 1: Vintage queries on current model
  - Same queries as 2 months ago
  - Current model
  - If quality drops: MODEL changed
  - If quality fine: model didn't change

Test 2: Current queries on vintage model (if vendor allows version pinning)
  - Current queries
  - Old model version
  - If quality drops: model improvements gone
  - If quality fine: model is fine, something else

Test 3: Same query on old prompt vs new prompt
  - Same query
  - Compare outputs from prompts
  - If different: PROMPT drift

Test 4: Old outputs on new eval
  - Use saved outputs from 2 months ago
  - Score with current rubric/judge
  - If score lower: EVAL drift (output unchanged but scoring changed)

Test 5: User survey
  - Direct user satisfaction now vs 2 months
  - vs measured metrics
  - If perception down but metrics flat: BASELINE shift
```

### Decision tree

```
"Feels worse" report
   │
   ▼
Validate: measured or anecdotal?
   │
   ▼
Run stratified eval (overall + segments)
   │
   ▼
Vintage queries on current model
   ├── Drops → Hypothesis 1: Model drift
   └── Fine → Continue
   │
   ▼
Compare query distribution vs 2 months ago
   ├── KL > threshold → Hypothesis 2: Data drift
   └── Same → Continue
   │
   ▼
Git log on prompts
   ├── Changes correlate with decline → Hypothesis 3: Prompt drift
   └── No changes → Continue
   │
   ▼
Re-eval old outputs with current rubric
   ├── Different scores → Hypothesis 4: Eval drift
   └── Same scores → Continue
   │
   ▼
User survey
   ├── Satisfaction down despite metrics flat → Hypothesis 5: Baseline shift
   └── Both metrics + satisfaction in sync → mysterious
```

---

## 完整代码 / 架构图

### Full diagnosis pipeline

```python
# diagnosis/pipeline.py

from datetime import datetime, timedelta
from typing import List

class DriftDiagnosisRunner:
    def __init__(self, system, eval_set, baseline_period_days=60):
        self.system = system
        self.eval_set = eval_set
        self.baseline_period_days = baseline_period_days
    
    async def diagnose(self):
        """Run 5-hypothesis diagnosis."""
        baseline_date = datetime.now() - timedelta(days=self.baseline_period_days)
        current_date = datetime.now()
        
        results = {}
        
        # ============================================
        # Hypothesis 1: Model drift
        # ============================================
        print("Running Hypothesis 1: Model drift...")
        vintage_golden = self._load_vintage_golden_set(date=baseline_date)
        current_responses = await self._run_current_model_on(vintage_golden)
        baseline_responses = [s.frozen_response_at(baseline_date) for s in vintage_golden]
        
        results['hypothesis_1_model_drift'] = await self._compare_responses(
            current_responses, baseline_responses, vintage_golden
        )
        
        # ============================================
        # Hypothesis 2: Data drift
        # ============================================
        print("Running Hypothesis 2: Data drift...")
        current_queries = await self._sample_queries(period=current_date)
        baseline_queries = await self._sample_queries(period=baseline_date)
        
        results['hypothesis_2_data_drift'] = await self._compare_query_distributions(
            current_queries, baseline_queries
        )
        
        # ============================================
        # Hypothesis 3: Prompt drift
        # ============================================
        print("Running Hypothesis 3: Prompt drift...")
        prompt_changes = self._audit_prompt_repo(baseline_date, current_date)
        prompt_comparison = await self._compare_prompts(prompt_changes)
        
        results['hypothesis_3_prompt_drift'] = {
            'prompt_changes': prompt_changes,
            'comparison': prompt_comparison,
        }
        
        # ============================================
        # Hypothesis 4: Eval drift
        # ============================================
        print("Running Hypothesis 4: Eval drift...")
        old_outputs = self._load_outputs_at(baseline_date)
        results['hypothesis_4_eval_drift'] = await self._re_eval_old_outputs(old_outputs)
        
        # ============================================
        # Hypothesis 5: Baseline shift
        # ============================================
        print("Running Hypothesis 5: Baseline shift...")
        results['hypothesis_5_baseline_shift'] = await self._compare_satisfaction(
            baseline_date, current_date
        )
        
        # ============================================
        # Rank hypotheses
        # ============================================
        ranked = self._rank_hypotheses(results)
        results['recommendation'] = ranked
        
        return results
    
    async def _compare_responses(self, current, baseline, samples):
        emb_sims = [cosine(embed(c), embed(b)) for c, b in zip(current, baseline)]
        len_ratios = [len(c) / max(len(b), 1) for c, b in zip(current, baseline)]
        
        return {
            'avg_emb_similarity': mean(emb_sims),
            'avg_length_ratio': mean(len_ratios),
            'verdict': 'MODEL_DRIFT_CONFIRMED' if mean(emb_sims) < 0.85 else 'no_evidence',
            'samples_compared': len(samples),
        }
    
    async def _compare_query_distributions(self, current, baseline):
        current_embs = await embed_batch(current)
        baseline_embs = await embed_batch(baseline)
        
        emb_drift = 1 - cosine(mean(current_embs), mean(baseline_embs))
        
        current_intents = await classify_batch(current)
        baseline_intents = await classify_batch(baseline)
        
        intent_kl = kl_divergence(Counter(current_intents), Counter(baseline_intents))
        
        new_intents = set(current_intents) - set(baseline_intents)
        
        return {
            'embedding_drift': emb_drift,
            'intent_kl': intent_kl,
            'new_intents': list(new_intents),
            'verdict': 'DATA_DRIFT_CONFIRMED' if emb_drift > 0.15 or intent_kl > 0.3 else 'no_evidence',
        }
    
    def _rank_hypotheses(self, results):
        """Rank hypotheses by evidence strength."""
        confirmed = []
        for k, v in results.items():
            if isinstance(v, dict) and v.get('verdict', '').endswith('_CONFIRMED'):
                confirmed.append(k)
        
        return {
            'confirmed_hypotheses': confirmed,
            'next_steps': self._recommend_next_steps(confirmed)
        }
    
    def _recommend_next_steps(self, confirmed):
        if 'hypothesis_1_model_drift' in confirmed:
            return [
                "Pin model version explicitly (e.g., claude-3-5-sonnet-20241022)",
                "Subscribe to vendor change announcements",
                "Re-tune prompt for new model version",
                "Consider multi-vendor diversification"
            ]
        if 'hypothesis_2_data_drift' in confirmed:
            return [
                "Extend FT / RAG corpus to cover new intents",
                "Update eval set with current data distribution",
                "Investigate why query distribution shifted (new product? new market?)",
            ]
        # ... etc
        return ["Mystery — need deeper investigation"]
```

### Architecture: drift diagnosis system

```
                  ┌──────────────────────────────────────┐
                  │  Customer Report: "Feels worse"      │
                  └────────────────┬─────────────────────┘
                                   │
                                   ▼
                  ┌──────────────────────────────────────┐
                  │  Validate: measured or anecdotal?    │
                  └────────────────┬─────────────────────┘
                                   │
                                   ▼
                  ┌──────────────────────────────────────┐
                  │  Stratified Eval                     │
                  │  - Overall current vs baseline       │
                  │  - By language / tenant / product    │
                  │  - By query type / difficulty        │
                  └────────────────┬─────────────────────┘
                                   │
        ┌──────────────────────────┴──────────────────────┐
        │           5-Hypothesis Diagnosis                │
        └─┬────────┬────────┬────────┬────────┬───────────┘
          │        │        │        │        │
          ▼        ▼        ▼        ▼        ▼
      ┌────────┐┌─────────┐┌────────┐┌────────┐┌──────────┐
      │ H1     ││ H2      ││ H3     ││ H4     ││ H5       │
      │ Model  ││ Data    ││ Prompt ││ Eval   ││ Baseline │
      │ drift  ││ drift   ││ drift  ││ drift  ││ shift    │
      │ 40%    ││ 25%     ││ 20%    ││ 10%    ││ 5%       │
      └────┬───┘└────┬────┘└───┬────┘└───┬────┘└────┬─────┘
           │         │         │         │          │
           ▼         ▼         ▼         ▼          ▼
      Vintage queries  Query     Git log    Re-eval   User
      on current        distrib   on        old       survey
      model             KL        prompt    outputs   compare
                                  files     with     measured
                                            current   vs perceived
                                            rubric
           │         │         │         │          │
           └─────────┴────┬────┴─────────┴──────────┘
                          │
                          ▼
              ┌──────────────────────────────────────┐
              │  Confirmed Hypotheses                │
              │  + Recommended Actions               │
              └──────────────────────────────────────┘
```

---

## Gao Xin 简历专属 reframe

### BNPL Anthropic model upgrade (PRIMARY STAR)

**S** (Situation):
> "December 2025, BNPL chatbot users reported responses 'feeling different' — more verbose, more caveats, more 'I should note that...'. Quality metrics on our eval set flat at 92%, but user satisfaction (CSAT) dropped from 4.4 to 3.9. Customer's PM was frustrated."

**T** (Task):
> "Diagnose if quality actually degraded or if perception was off."

**A** (Action — 5-hypothesis diagnosis):

```
Hypothesis 1 — Model drift (prior 40%):
  Test: ran vintage golden set (frozen August 2025) on current API
  Result: outputs semantically different from frozen Aug responses
          (avg emb sim 0.72 vs target > 0.85)
          Length 40% longer
          Refusal rate +1pp
  → MODEL DRIFT CONFIRMED

Verification: checked Anthropic changelog
  Found: Sonnet 4.5 → 4.6 silent upgrade on shared API endpoint
  (we used `claude-3-5-sonnet-latest` not version-pinned)

Hypothesis 2 — Data drift: KL stable, ruled out
Hypothesis 3 — Prompt drift: no recent changes, ruled out
Hypothesis 4 — Eval drift: same rubric/judge, ruled out
Hypothesis 5 — Baseline shift: minor (users got slightly used to it),
              but not primary
```

**Specific mitigation**:
1. Pinned model version: `claude-3-5-sonnet-20241022` (specific date)
2. Re-tuned system prompt for new model version (5 prompt iterations)
3. Subscribed to Anthropic changelog mailing list
4. Built model version comparison tool (compare current pinned vs latest, monthly)
5. Multi-vendor canary started (5% on Gemini 3 Pro for diversification)

**R** (Result with concrete numbers):
- **CSAT recovered**: 3.9 → 4.3 within 2 weeks
- **Quality metric improved**: 92% → 94% (after prompt re-tuning, better than baseline)
- **Multi-vendor**: never been bitten by model drift again
- **Customer trust restored**: shared the diagnosis methodology with customer, now they use similar approach

### Voice agent Indonesia fraud drift (SECONDARY STAR)

**S**: Voice agent Indonesia. Week 5 production, refusal rate creeping up 8% → 18%.

**T**: Diagnose.

**A**:
- H1 Model drift: vendor (Mistral) stable, ruled out
- H2 Data drift: input distribution shifted (more emergency claims). New fraud pattern: people claiming emergency to get refund.
- H3 Prompt drift: no changes
- H4 Eval drift: stable
- H5 Baseline: stable

**DATA DRIFT CONFIRMED**. Model conservatively refusing all "emergency" claims (legit + fraud).

**Mitigation**: DPO refresh on 200 new examples (emergency true vs false), updated fraud rules.

**R**: Refusal rate normalized 18% → 9%, fraud detection improved.

### ConvFinQA financial knowledge update (TERTIARY STAR)

**S**: ConvFinQA accuracy dropped after Q4 earnings season.

**T**: Diagnose.

**A**:
- Data drift: new financial language in Q4 earnings reports (new accounting standards, new product mentions)
- RAG corpus not updated yet

**Mitigation**: Incremental RAG re-indexing on Q4 docs.

**R**: Accuracy recovered within 1 week of re-indexing.

---

## 5 个 Follow-ups

**Q1**: "Vendor doesn't allow version pinning. What do you do?"

**A**: Multi-layer defense:
1. **Multi-vendor diversification**: split traffic across 2-3 vendors. If one drifts, fall back to others.
2. **Continuous regression eval**: daily/weekly check vintage golden set on current model. Detect drift quickly.
3. **Self-host as backup**: open weights (Llama 4 70B) self-hosted as failover if managed quality degrades.
4. **Vendor pressure**: if multiple customers complain, vendor may add version pinning.
5. **Prompt versioning**: maintain prompts per model version, switch as vendor switches.

**Q2**: "How often should you re-tune prompts for new model versions?"

**A**:
- **On detected drift**: if regression eval shows quality drop, prompt re-tune is the cheapest first step.
- **On vendor announcement**: when vendor pre-announces new version, schedule prompt eval + tune.
- **Default quarterly**: even if no obvious issue, re-eval quarterly. Subtle drift may be undetected.
- **Per workload**: high-volume workloads worth more tuning effort. Low-volume can ride.

Typical re-tune: 2-5 prompt iterations, 1-2 weeks of eval. Costs ~$5-10k engineering time.

**Q3**: "User survey vs measured metrics — which to trust?"

**A**: Both, but understand they measure different things:
- **Measured metrics** (LLM-judge, accuracy): objective but proxy. May miss what users care about.
- **User survey** (CSAT, NPS): subjective but truth. Reflects actual user experience.

**Common gaps**:
- Metrics improve, survey flat: optimizing wrong proxy (Goodhart)
- Survey drops, metrics flat: baseline shift or unmeasured dimension
- Both move together: aligned, easy to interpret

**Action**: triangulate. If survey + metric agree → high confidence. If diverge → investigate (often baseline shift or proxy mismatch).

**Q4**: "How do you prevent silent drift in the first place?"

**A**: 5 practices:
1. **Continuous regression eval**: daily/weekly on vintage golden set
2. **Version pinning where possible** (Anthropic, OpenAI both offer)
3. **Vendor change subscriptions** (Discord, mailing list, changelog)
4. **Multi-vendor diversification** (5-10% canary on alternative)
5. **Drift detection in production** (input distribution + output behavior monitoring)
6. **Quarterly golden set refresh** to capture new patterns
7. **User satisfaction trending** (catch perception drift independent of metrics)

**Q5**: "Customer doesn't believe you when you say 'it's vendor drift, not us.' How handle?"

**A**:
1. **Show the data**: "Here's our regression eval. Same queries, same prompts, different responses now. Started [date] which coincides with [vendor announcement / silent change]."
2. **Vendor changelog**: cite specific evidence ("Anthropic announced Sonnet 4.6 upgrade")
3. **Reproduce live**: in meeting, run a sample query showing different output now vs 2 months ago
4. **Customer's data residency**: "We can use a version-pinned model for your tenant specifically. Costs ~5% more, locks at this version."
5. **Trust building**: be transparent that vendor drift is a real risk. We mitigate but can't eliminate. Multi-vendor + version pinning is our defense.

If they still don't believe: they're frustrated, not factual. Acknowledge frustration, focus on what we'll do (specific action items) more than what happened.

---

## ❌ 死路答法

1. **"Probably model drift"** — without methodology, no diagnosis
2. **Jumping to retrain** without isolating variable
3. **Only check overall metrics** (per-segment hides issues)
4. **No vintage golden set** (can't compare like-for-like)
5. **Forget vendor silent updates** (model drift is biggest cause 2026)
6. **Don't audit prompt changes** (often the surprise)
7. **No user survey** (perception drift missed)
8. **Single hypothesis** (often 2-3 causes overlap)
9. **No isolation pattern** (can't tell which variable changed)
10. **No prevention plan** going forward

---

## ✅ 加分项

1. **5 hypothesis categories with priors** — Bayesian thinking
2. **Variable isolation pattern** — hold one constant, test others
3. **Vintage golden set** practice — frozen reference
4. **Stratified eval by segment** — overall hides per-segment
5. **Vendor silent updates** awareness — 2026 reality
6. **Prompt audit via git log** — often the surprise cause
7. **Eval drift recognition** — re-score old outputs with new rubric
8. **Baseline shift** — users got better, expectations raised
9. **Specific examples** (BNPL Anthropic upgrade, voice agent fraud, ConvFinQA)
10. **Prevention plan** (version pin + multi-vendor + continuous regression)

---

## 一句话总结

> **Model drift diagnosis = 5 hypotheses with priors: model drift (40%, vendor sneaky) / data drift (25%, query shift) / prompt drift (20%, someone edited) / eval drift (10%, rubric changed) / baseline shift (5%, users learned). Variable isolation: vintage queries on current model isolates model drift. Stratified eval by segment reveals per-segment failures hidden by overall. Prevention: version pinning + continuous regression + multi-vendor canary + quarterly golden set refresh. BNPL Anthropic Sonnet 4.5→4.6 silent upgrade is the canonical 2026 story.**

---

## Cheat Sheet

```
5 hypothesis categories (with priors):
  1. MODEL drift (40%)   — vendor updated silently
  2. DATA drift (25%)    — user queries shifted
  3. PROMPT drift (20%)  — someone edited
  4. EVAL drift (10%)    — rubric / judge changed
  5. BASELINE shift (5%) — users got better

Diagnosis methodology:
  Step 1: Validate "feels worse" — measured or anecdotal?
  Step 2: Stratified eval (overall + segments)
  Step 3: Variable isolation (vintage queries on current model, etc.)
  Step 4: Audit git log on prompts
  Step 5: Re-eval old outputs with current rubric
  Step 6: User survey
  Step 7: Rank confirmed hypotheses
  Step 8: Mitigation specific to confirmed cause

Variable isolation pattern:
  - Vintage queries + current model: tests MODEL drift
  - Current queries + vintage model: tests if model improvements gone
  - Same query + old vs new prompt: tests PROMPT drift
  - Old outputs + current rubric: tests EVAL drift
  - Survey vs metrics: tests BASELINE shift

Model drift detection:
  - Vintage golden set (frozen 2 months ago)
  - Same queries on current model
  - Compare: embedding similarity, length, refusal rate
  - Drift if: emb_sim < 0.85, length ratio > 1.5, refusal +5%+

Data drift detection:
  - Query distribution KL divergence
  - Embedding mean cosine
  - New intents emerging
  - Per-old-intent metrics still good?

Prompt drift detection:
  - Git log on prompts/ directory
  - Comparison test (same query, both prompts)
  - "Prompt creep" (length growth)

Eval drift detection:
  - Re-score frozen outputs with current rubric
  - Judge model version changes
  - Rubric weight changes

Baseline shift detection:
  - User survey trend (CSAT, NPS)
  - Compare measured vs perceived
  - Gap = baseline shift

Mitigation by hypothesis:
  Model drift:
    - Pin model version explicitly
    - Subscribe vendor changelog
    - Re-tune prompt for new version
    - Multi-vendor diversification
  
  Data drift:
    - Extend FT / RAG corpus
    - Update eval set
    - Investigate why query shifted
  
  Prompt drift:
    - Audit git log
    - Regression test before merge
    - Version control prompts like code
  
  Eval drift:
    - Document rubric changes
    - Recalibrate judge
  
  Baseline shift:
    - Improve to match new expectations
    - Communicate progress

Prevention (continuous):
  - Daily/weekly regression eval on vintage golden set
  - Version pinning where vendor allows
  - Vendor change subscriptions
  - Multi-vendor canary (5-10%)
  - Drift detection in production
  - Quarterly golden set refresh
  - User satisfaction trending

Production reality:
  - Anthropic Sonnet 4.5→4.6 silent (December 2025 example)
  - OpenAI GPT-5.3→5.4 with same endpoint name
  - 2026 reality: API users always at risk of model drift

Case studies:
  - BNPL Anthropic upgrade: CSAT 4.4→3.9, recovered via version pin + prompt re-tune
  - Voice agent Indonesia fraud: refusal 8%→18%, DPO refresh on new patterns
  - ConvFinQA Q4 earnings: RAG re-index for new financial language

Anti-patterns:
  - "Just retrain" without diagnosis
  - Only check overall metrics
  - No vintage golden set
  - Single hypothesis
  - No variable isolation
  - Don't audit prompt git log
  - No prevention plan

Quotes for interview:
  - "5 hypotheses with priors — model drift is highest (40%) in 2026"
  - "Vintage queries on current model isolates model drift"
  - "Stratified eval — overall hides per-segment failure"
  - "Version pinning is your #1 defense against vendor drift"
  - "Continuous regression eval catches drift in days not months"
  - "BNPL Anthropic Sonnet 4.5→4.6 silent upgrade is canonical 2026 story"
```
