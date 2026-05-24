## 题目（verbatim）

> "After deployment, the **model performs worse than the previous manual process** the customer was using. How do you investigate and what do you do?"

**出处**: fde.academy 列出的「AI deployment 失败诊断」经典题. OpenAI / Google FDE 都常问.

**Round**: Case Study / Deployment Scenario (45 min)

---

## 这道题在考什么

考你**面对 AI deployment 失败时的工程冷静**. AI deployment 失败比成功多. 考点:

1. **Don't panic, don't blame** — 立刻 reach for 「model is bad」或「customer integrated wrong」都是 ego
2. **First measure, then hypothesize** — 你拿什么数据来比较 model vs manual?
3. **5 个 hypothesis class** — 你能拆出来吗
4. **De-risk vs Roll back** — 知道 partial 退回 / kill switch
5. **Don't avoid「maybe model is wrong for this task」** — 这是有可能的, 你愿不愿意诚实说

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**Manual process baseline**: 客户之前的「人工流程」. 通常是:
- 一个 expert 凭 20 年经验做决策 (e.g., dispatcher 选车)
- 一个 process 跑 N 步 + N 个 form (e.g., 客服 ticket 流转)
- 一个 algorithm + 人工 review (e.g., 信用评分 + manager approve)

**关键**: manual baseline 通常**不是同等任务**. 人在做 X 的 subset, 模型在做 X 的全集. 这就是 H1 (Apple-to-orange).

**Model performance**: 一个充满歧义的词. 必须细分:
- **Accuracy / F1**: traditional ML
- **Latency**: speed
- **User satisfaction**: 主观
- **Business KPI**: 跟实际收入 / 成本挂钩
- **Cost**: serving + compute
- **Coverage**: 处理 case 的比例

哪个 metric "worse"? 不同 metric 不同 root cause.

**Diagnostic framework**: 5 类 hypothesis 框架 (H1-H5), 这是这道题的核心. **未先 diagnose 就 retrain 是典型新手错误**.

**Graceful retreat**: 当 H5 (产品真不行) 时, 不要硬撑. 重新 scope: model 只服务 X% 它擅长的 case, 剩下还是 manual. 这比死磕全量好.

---

## 2. 这个问题的核心是什么

设想没有 diagnostic framework 的灾难:

```
Day 1:  客户怒: "你们 model 不如我们人."
Day 2:  你: "我们 retrain 一下."
Day 7:  Retrain v2, performance 跟 v1 一样.
Day 14: 客户更怒. 你: "再 retrain, 加数据."
Day 21: v3, 还一样.
Day 30: 客户提合同终止.
Day 35: 你回去复盘, 才发现:
         真问题: feature pipeline 有个 bug, prod 缺一个关键 feature.
         Retrain 永远解决不了, 因为 feature 都是错的.
```

**问题**:
- 没诊断就 retrain — 烧 GPU 烧 cycle 烧客户耐心
- Blame model — 把 H4 (integration) 当 H5 (model)
- Blame customer — 政治灾难
- 没 immediate safeguard — 诊断期间客户的真业务每天在死

**Diagnostic framework 解法**:

```
Day 1: Acknowledge + immediate safeguard (high-stake roll back to manual)
Day 2-3: 5 hypothesis classes, rank by likelihood
Day 4-7: H1+H3 first (最常见), 5 天验证
Day 8-10: 若不是 H1/H3, 验 H4 (2 天)
Day 11-14: 若都不是, 验 H2/H5

Day 14: 诊断完毕 + 具体 remediation + 跟客户对齐
```

---

## 3. 5 Hypothesis Decision Tree

```
                        ┌────────────────────────────┐
                        │ Model 表现 "worse than manual"│
                        └─────────────┬──────────────┘
                                      ↓
                        ┌────────────────────────────┐
                        │  H1: Apple-to-orange?      │
                        │  Model 处理的 case 跟 manual│
                        │  处理的不一样?              │
                        └────────────┬───────────────┘
                          YES → fix scope  ↓ NO
                                          ↓
                        ┌────────────────────────────┐
                        │  H3: Edge case dominance?  │
                        │  Manual 是 20 yr expert 处理 │
                        │  罕见 case. Model 只学 bulk. │
                        └────────────┬───────────────┘
                          YES → triage route ↓ NO
                                            ↓
                        ┌────────────────────────────┐
                        │  H4: Integration/feature   │
                        │  pipeline 失败?             │
                        │  Prod 缺 feature / null / 错。│
                        └────────────┬───────────────┘
                          YES → fix pipeline ↓ NO
                                            ↓
                        ┌────────────────────────────┐
                        │  H2: Distribution shift?   │
                        │  Live data ≠ training data │
                        └────────────┬───────────────┘
                          YES → retrain on recent ↓ NO
                                                  ↓
                        ┌────────────────────────────┐
                        │  H5: Model genuinely wrong │
                        │  Task may need different ML │
                        └────────────────────────────┘
                          YES → graceful retreat
```

诊断顺序: H1 → H3 → H4 → H2 → H5 (rough 优先级 by likelihood).

---

## 4. 5 个 Hypothesis 详细分类表

| Hypothesis | What's wrong | Investigation | Fix | Likelihood |
|---|---|---|---|---|
| **H1: Apple-to-orange** | Model 处理更广 case (manual 只挑容易) | Stratify by case difficulty, see if model wins on easy + same on hard | Triage routing | 40% |
| **H2: Distribution shift** | Live data ≠ training data | Compare train / test / live distributions (KS, PSI) | Retrain on recent | 15% |
| **H3: Edge case dominance** | Expert intuition on 5% rare case | Stratify error rate by case rarity | Specialist sub-model + escalate rare | 25% |
| **H4: Integration / feature pipeline failure** | Model OK offline, prod 缺 feature | Trace 10 live errors end-to-end | Fix pipeline + add tests | 15% |
| **H5: Model genuinely wrong** | Task fundamentally hard for ML | Error analysis 100 errors, structural | Graceful retreat | 5% |

**总数 100%**, H1 + H3 占 65% — 优先诊断这两个.

---

## 5. 具体业务场景

### 场景 A: 你的 ConvFinQA negative result — 直接对应

你做 ConvFinQA 9-variant ablation, **所有 9 个 variant 都没超 baseline**. 这就是这道题的精确实验:

- 你 v0 baseline = "no agent pattern, just LLM"
- 你 v1-v9 = 9 种 agent pattern (typed lookup, critic, plan tags, etc.)
- 结果: v1-v9 全部 <= baseline

**诊断**:
- **H1 (apple-to-orange)**: 没 detect; conditional acc on non-None preds — 一样
- **H4 (integration)**: 你 tested; pipeline OK
- **H3 (edge case)**: 你 stratify by topic — 同样 distribution
- **H5 (model wrong)**: variants 增加 prompt budget, 模型不能 attention 关键信息

你的 **negative result 论文 + 公开承认 H5** 就是这道题答案的精髓.

### 场景 B: 信用评分模型替代人工 — 经典 H1 案例

**Setup**: 客户 (银行) 让你的 model 替代信用审核员. Model auto-decision, manual baseline 是 senior credit officer.

**初表现**: Model accuracy 91%, manual 是 94%. 看起来 model worse 3%.

**真相 (H1)**: 
- Manual: 看 100 个 app, 35 个 obvious approve, 35 个 obvious reject, 30 个 borderline → 30 个借给 senior officer 看 (他 94% accuracy)
- Model: 看 100 个 app, 全部 auto-decision (91% accuracy)

**Apple-to-orange**: 
- Manual 实际处理 30%, accuracy 94%
- Model 处理 100%, accuracy 91%
- Manual on the same 30%? **80% accuracy** (太难, senior officer 也犯错)
- Model on the same 30%? **84% accuracy**

**Model 实际更强**. 只是看 aggregate 不知道.

**Fix**: Triage routing — 70% easy 给 model, 30% hard 给 senior officer. Throughput +70%, accuracy 不变. 客户喜欢.

### 场景 C: 你的 voice agent ASR 在 1 个市场 degraded — 类似 H3

**Setup**: Voice agent 跨 7 markets, Brazil market 上线后客户投诉「人听不懂客户」.

**初表现**: ASR overall accuracy 88%, Brazil market 76%.

**诊断 (H3 + H2)**:
- H3: Brazil 用 Portuguese, 你 model 训练数据 95% 是 English + Spanish
- H2: Brazil 客户口音地区差异大, 你训练数据来自 Rio (1 个 metro)

**Fix**: 
- H3 fix: 额外 fine-tune on Portuguese, +800K hours from public corpus
- H2 fix: 收集 6 个 metro 的样本, balanced training data
- 联合: accuracy 76% → 86%, 接近 overall

### 场景 D: AI 工具表现差因为 prod 缺 feature — H4 经典

**Setup**: 你给 logistics 客户上 rerouting agent. Offline accuracy 92%, online 67%.

**诊断 (H4)**:
- 你 trace 10 个 prod 失败 case
- 发现 weather_condition feature 永远是 null in prod
- 因为 weather API 集成有 bug, weather service 在 prod env 没 deploy

**Fix**: Deploy weather service to prod. Accuracy 67% → 91%. 30 min 工作量解决了 3 周 retraining 都没解决的「model 问题」.

### 场景 E: Model 真的不适合 task — H5 honest

**Setup**: 客户希望 ML 做「医疗诊断 free-text 分类到 200 ICD-10 codes」.

**Symptom**: Accuracy 65%. Manual coder (human) 92%.

**深度 error analysis**: 60% 错误是「nuanced cases」 — 需要 inferring patient history + cross-reference 多份历史 record. LLM context window 太小, 不能装下所有 context.

**Honest 诊断**: 这不是 retrain 能 fix. ICD coding 真的需要 narrative reasoning + 完整患者历史, 比当前 LLM context 大.

**Graceful retreat**:
- "We were wrong about scope. Model best-suited for **simple ICD coding** (60% of cases). For complex multi-pathology, **manual coder retains**."
- 客户 satisfied: 60% throughput up, 40% manual workload stay
- 不再硬卖「全自动」

---

## 6. 工程上要做什么 / 诊断 checklist

**Day 1 — Immediate response (4 hours)**:

1. Acknowledge customer's concern. **Never defensive**.
2. **Immediate safeguard**: 高 stake 类目 (safety-critical / 大客户) **立刻 fallback to manual**. 写 1 个 feature flag toggle.
3. 给客户**14 天 diagnosis plan** (具体时间表).
4. 设立 daily standup (15 min) 跟 customer counterpart.

**Day 2-5 — H1 + H3 investigation**:

5. 拉 last 30 day prod data, stratify by case difficulty
6. 跑 manual baseline on same set (历史数据 + sampling)
7. 比较 model vs manual on 同 distribution
8. 看 model error 在 case rarity 分布: 是 bulk error 还是 tail error?

**Day 6-7 — H4 investigation**:

9. Trace 20 个 prod 错误 end-to-end
10. 比较 feature values: prod vs training
11. Check pipeline: nulls / defaults / encoding bugs
12. Compare model offline eval on prod-mimicked data

**Day 8-10 — H2 investigation**:

13. KS test on every feature: train vs live
14. PSI (Population Stability Index) calculation
15. Check for new categories / values / volume shift

**Day 11-12 — H5 investigation (if needed)**:

16. 100 errors random sample, manual error analysis
17. 是 random error (model variance) 还是 structural (model 系统性盲点)?
18. Compare to SOTA: 该 task 行业最佳 accuracy 是多少?

**Day 13-14 — Synthesis + customer comm**:

19. 写 1-pager: root cause + remediation plan + timeline
20. Present to customer leadership
21. 跟客户 jointly own action items

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **立刻 blame model** | 没诊断 jumping to "我们 model 有问题" |
| 2 | **立刻 blame customer** | "你们 integrate 错了" 出口 |
| 3 | **没 5 hypothesis 框架** | 没结构化 |
| 4 | **跳过 H1 apple-to-orange** | 最常见原因 |
| 5 | **没 immediate safeguard** | Diagnose 期间不保护 customer |
| 6 | **不敢说 H5** | 永远不承认 model 是错选 |
| 7 | **直接 retrain** | 没诊断就 retrain, 大概率没解决根因 |
| 8 | **跳过 daily standup** | 客户每天怒一点直到爆 |
| 9 | **没 stratification** | Aggregate metric 掩盖真 root cause |
| 10 | **rules-on-top death spiral** | 加 rule 永无止境, 不如 retrain |

---

## 一句话总结 (Part 1)

> **Model worse than manual = 「不 panic 不 blame, 立 immediate safeguard, 5 hypothesis decomposition (H1 apple-to-orange first), daily standup 跟客户透明, retrain 永远是最后选项」**.
>
> 这道题考的是「production AI deployment 失败时你不慌, 你诊断, 你诚实」. 慌 = 失分. 诊断不全 = 失分. 不诚实承认 H5 = 失分.

---

# Part 2 · 5 个深度工程问题

## ⚙️ Problem 1: Diagnostic Framework — Data Drift vs Model Issue vs Metric Mismatch vs Scope Mismatch

**核心**: 不要把 5 个 hypothesis 当 checklist, 当 decision tree. 不同症状指向不同 hypothesis.

### 1.1 Symptom-to-Hypothesis 映射

```python
class SymptomDiagnosis:
    def __init__(self, model_perf, manual_perf, prod_data, train_data):
        self.model = model_perf
        self.manual = manual_perf
        self.prod = prod_data
        self.train = train_data

    def hypothesize(self):
        hypotheses = []

        # H1 signal: 处理 case 不同
        if self.manual.case_count < self.model.case_count * 0.7:
            hypotheses.append({
                'name': 'H1_apple_to_orange',
                'confidence': 0.8,
                'evidence': f'manual handled {self.manual.case_count}, model {self.model.case_count}'
            })

        # H2 signal: 训练 vs prod 分布漂
        psi = compute_psi(self.train, self.prod)
        if psi > 0.2:
            hypotheses.append({
                'name': 'H2_distribution_shift',
                'confidence': min(psi, 1.0),
                'evidence': f'PSI = {psi:.2f}'
            })

        # H3 signal: 错误集中在 rare cases
        rare_case_err = error_rate_in_rare_buckets(self.model)
        common_case_err = error_rate_in_common_buckets(self.model)
        if rare_case_err > common_case_err * 2:
            hypotheses.append({
                'name': 'H3_edge_case_dominance',
                'confidence': 0.7,
                'evidence': f'rare-case err {rare_case_err}, common {common_case_err}'
            })

        # H4 signal: offline eval >> online perf
        offline_perf = self.model.offline_eval
        online_perf = self.model.online_perf
        if offline_perf - online_perf > 0.1:
            hypotheses.append({
                'name': 'H4_integration_failure',
                'confidence': 0.9,
                'evidence': f'offline {offline_perf}, online {online_perf}'
            })

        # H5 signal: 全维度都查过仍 worse
        # 这个是 last resort, 只有其他 4 个排除后才说

        return sorted(hypotheses, key=lambda h: -h['confidence'])
```

### 1.2 H1 Apple-to-orange 详细诊断

```python
def diagnose_h1(model_records, manual_records):
    """对比 model 和 manual 处理的 case distribution"""

    # 1. Case difficulty stratify
    def difficulty(case):
        return case.feature_completeness_score * case.signal_strength

    model_diff_dist = np.histogram([difficulty(c) for c in model_records], bins=10)
    manual_diff_dist = np.histogram([difficulty(c) for c in manual_records], bins=10)

    # 2. 检测分布差异
    from scipy.stats import ks_2samp
    stat, pval = ks_2samp(model_diff_dist, manual_diff_dist)

    if pval < 0.01:
        return {
            'h1_confirmed': True,
            'reason': f'distributions differ significantly (KS p={pval})',
            'model_handles_harder_cases': model_diff_dist.mean() < manual_diff_dist.mean()
        }

    # 3. Performance on overlapping distribution
    overlap_distribution = get_overlap(model_diff_dist, manual_diff_dist)
    model_on_overlap = model_perf_in_range(overlap_distribution)
    manual_on_overlap = manual_perf_in_range(overlap_distribution)

    return {
        'h1_confirmed': False,
        'model_on_overlap': model_on_overlap,
        'manual_on_overlap': manual_on_overlap,
        'true_comparison': model_on_overlap >= manual_on_overlap
    }
```

### 1.3 H2 Distribution shift 详细诊断

```python
def diagnose_h2(train_df, prod_df):
    """对每个 feature 检验分布漂移"""

    drift_report = {}
    for col in train_df.columns:
        if train_df[col].dtype in ['int', 'float']:
            # Continuous: KS test + PSI
            psi = compute_psi(train_df[col], prod_df[col])
            ks_stat, ks_pval = ks_2samp(train_df[col], prod_df[col])
            drift_report[col] = {
                'psi': psi,
                'ks_stat': ks_stat,
                'ks_pval': ks_pval,
                'drifted': psi > 0.2 or ks_pval < 0.01
            }
        else:
            # Categorical: chi-square + new values
            new_values = set(prod_df[col].unique()) - set(train_df[col].unique())
            chi2, chi2_pval = chi_square_test(train_df[col], prod_df[col])
            drift_report[col] = {
                'new_values': new_values,
                'chi2_pval': chi2_pval,
                'drifted': len(new_values) > 0 or chi2_pval < 0.01
            }

    drifted_features = [k for k, v in drift_report.items() if v['drifted']]

    return {
        'h2_confirmed': len(drifted_features) > 0,
        'drifted_features': drifted_features,
        'severity': 'critical' if len(drifted_features) > 5 else 'moderate'
    }
```

### 1.4 H4 Integration failure 诊断

```python
def diagnose_h4(prod_failures):
    """End-to-end trace 失败 cases"""

    issues = []
    for case in prod_failures[:20]:
        # 1. Reconstruct features at decision time
        features = reconstruct_features(case.id)

        # 2. Check for nulls
        nulls = [k for k, v in features.items() if v is None]
        if nulls:
            issues.append({
                'case_id': case.id,
                'issue': 'missing_features',
                'detail': nulls
            })
            continue

        # 3. Check for outliers
        outliers = []
        for k, v in features.items():
            if is_outlier(v, training_distribution=k):
                outliers.append({'feature': k, 'value': v})
        if outliers:
            issues.append({
                'case_id': case.id,
                'issue': 'feature_outliers',
                'detail': outliers
            })

        # 4. Replay model with prod features → confirm same output
        replay_output = model.predict(features)
        prod_output = case.decision
        if replay_output != prod_output:
            issues.append({
                'case_id': case.id,
                'issue': 'replay_mismatch',
                'detail': {'replay': replay_output, 'prod': prod_output}
            })

    common_issues = Counter(i['issue'] for i in issues)
    return {
        'h4_confirmed': len(issues) > len(prod_failures) * 0.3,
        'common_issues': common_issues
    }
```

### 1.5 Investigation priority matrix

```
       Cost to investigate  |  Likelihood
H1     Low (2 days)         |  40%       ← Start here
H3     Low (2 days)         |  25%       ← And here in parallel
H4     Low (1-2 days)       |  15%       ← Quick to rule out
H2     Mid (3 days)         |  15%
H5     High (5+ days)       |  5%        ← Only if all else fails
```

并行 H1 + H3 (5 天), 然后 H4 (1-2 天), H2 (3 天), 最后 H5.

---

## ⚙️ Problem 2: Sliced Eval — Find Which Segment Regressed

**核心**: Aggregate metric 是个 lie. 真正发生什么必须 stratify by 多个 axis.

### 2.1 Multi-axis stratification

```python
def sliced_eval(records, axes):
    """对每个 axis × 每个 value 计算 metric"""
    results = {}
    for axis in axes:
        for value in records[axis].unique():
            subset = records[records[axis] == value]
            results[f'{axis}={value}'] = {
                'count': len(subset),
                'accuracy': accuracy(subset),
                'precision': precision(subset),
                'recall': recall(subset),
                'f1': f1(subset),
            }
    return results

# 用法
axes = ['customer_type', 'product_category', 'region', 'time_of_day', 'difficulty_bucket']
sliced = sliced_eval(prod_records, axes)
```

### 2.2 Regression detection

```python
def detect_regression(current_slice, baseline_slice, threshold=0.02):
    """对每个 slice 检测是否退步"""
    regressions = []
    for slice_name in current_slice:
        if slice_name not in baseline_slice:
            continue
        cur = current_slice[slice_name]
        base = baseline_slice[slice_name]
        if base['count'] < 100:
            continue  # 样本太小, 不可靠
        delta_f1 = cur['f1'] - base['f1']
        if delta_f1 < -threshold:
            regressions.append({
                'slice': slice_name,
                'delta_f1': delta_f1,
                'cur_f1': cur['f1'],
                'baseline_f1': base['f1'],
                'count': cur['count']
            })

    return sorted(regressions, key=lambda r: r['delta_f1'])

# Output 样例:
# [
#   {'slice': 'region=Brazil', 'delta_f1': -0.18, ...}
#   {'slice': 'product_category=hazmat', 'delta_f1': -0.12, ...}
#   {'slice': 'time_of_day=night', 'delta_f1': -0.05, ...}
# ]
```

### 2.3 Concentration analysis

```python
def concentration_analysis(error_records, axes):
    """如果 90% 错误集中在 5% slice, 那就是 concentrated failure"""
    for axis in axes:
        value_counts = error_records[axis].value_counts(normalize=True)
        for value, pct in value_counts.head(5).items():
            if pct > 0.3:
                # Disproportionate concentration
                yield {
                    'axis': axis,
                    'value': value,
                    'error_share': pct,
                    'population_share': population_share(axis, value)
                }
```

Example output: "region=Brazil 占 8% 流量, 但产生 47% 错误" → 强信号 H3 (edge case for that region).

### 2.4 Visual dashboard

```
[Sliced Eval - last 30 days]

By region:
   US East   ████████████████████ 0.91  (baseline 0.92)  -0.01 ✓
   US West   ███████████████████  0.89  (baseline 0.89)   0.00 ✓
   EU        ██████████████████   0.87  (baseline 0.90)  -0.03 ⚠️
   Brazil    █████████            0.72  (baseline 0.89)  -0.17 ✗

By product:
   Standard  ████████████████████ 0.91  ✓
   Hazmat    ███████              0.65  (baseline 0.88) -0.23 ✗
   Oversized ████████████████     0.85  ⚠️

By customer tier:
   Enterprise ████████████████████ 0.92  ✓
   SMB        ███████████████████  0.89  ✓
   Trial      ████████████         0.78  (baseline 0.85) -0.07 ⚠️
```

立即可见: Brazil region 和 Hazmat 产品是 regression hotspot. 进一步 cross-tab 看是不是 "Brazil hazmat" 双重边缘.

### 2.5 你的 ConvFinQA stratified 300 经验

你做 ConvFinQA stratified by 9 topic, 这就是 sliced eval. 直接 quote:

```
ConvFinQA 9-variant ablation 结果:

Baseline (no agent):  72% accuracy overall
Variant 1 (typed):    71% — within noise
Variant 2 (critic):   68% — REGRESSION

Sliced by topic:
  Financial reporting  baseline 75% → variant 2 60% (-15%)  ✗
  Date arithmetic       baseline 60% → variant 2 64% (+4%)  ✓ 
  Multi-step ratio      baseline 80% → variant 2 78% (-2%)  ✓

诊断: critic variant 在 financial reporting 引入 over-correction.
     不是「critic 不好」, 是「critic 在某 task type 错」.
```

这就是真实的 sliced eval methodology.

---

## ⚙️ Problem 3: Hidden Cost of Automation — Errors at Scale, Lack of Human Judgment

**核心**: 即使 model accuracy 等于 manual, 部署 model 仍可能让客户**总成本上升**. 这是 FDE 必须知道的 deployment trap.

### 3.1 错误的 cost asymmetry

```python
# 不是所有 error 等价
def error_cost(error_type):
    cost = {
        'false_positive_credit_approve': 5000,    # 坏账损失
        'false_negative_credit_approve': 50,      # 失去一笔小贷利息
        'false_positive_fraud_block': 100,        # 误伤客户
        'false_negative_fraud_block': 10000,      # 真欺诈
        'false_positive_medical_diagnose': 200,    # 多做一项 test
        'false_negative_medical_diagnose': 100000  # 漏诊死人
    }
    return cost[error_type]
```

Manual 倾向 conservative (false negative): 模糊 case → 升级. Model 倾向 confident (false positive). **错误类型分布不同**, 总成本可能 model 更高.

### 3.2 Scale amplification

```python
# Manual 错误: 每天 100 case × 5% error × $5000 = $25K/day
# Model 错误: 每天 10000 case × 5% error × $5000 = $2.5M/day

# 即使 accuracy 一样, scale 让小 error rate 变成大金额
# Manual 不会跑 100x scale, 因为人不够; model 跑全量

# 客户没意识到: "model accuracy 跟 manual 一样, 怎么 cost 涨了 100x?"
```

### 3.3 Loss of human safety net

```python
# Manual case:
def manual_process(case):
    decision = expert_judge(case)
    if expert_uncertain(case):
        consult_colleague(case)         # Built-in second opinion
    if decision_high_stake(case):
        manager_approve(case)             # Built-in oversight
    return decision

# Model case (naive):
def model_process(case):
    decision = model.predict(case)
    return decision                       # No oversight, no escalation
```

Manual process 有**多层 safety net** (peer review, manager approve). Model 一上线把这些都拆了, hidden cost 是「之前你不知道有的 safety event」.

### 3.4 Confidence-based hybrid

```python
def hybrid_process(case):
    model_decision = model.predict(case)
    confidence = model.confidence(case)

    if confidence > 0.9 and stake(case) < 'high':
        # Auto-execute
        return model_decision

    elif confidence > 0.7:
        # Recommend to human, who decides
        return human_with_recommendation(case, model_decision)

    elif confidence < 0.5:
        # Escalate, model output is noise
        return escalate_to_specialist(case)

    elif stake(case) == 'high':
        # Always human for high-stake
        return human_with_recommendation(case, model_decision)
```

**关键**: 即使 model accuracy 91%, 把 9% error 都路由到人就 cost 几乎 zero. **混合 > 全自动** in 90% deployment 场景.

### 3.5 Long-tail learning loss

```python
# Manual process: senior expert 处理 5% rare cases 积累经验
# Model deployment: rare cases 也走 model
# 结果: 1 年后 senior expert 没新经验, 知识 plateau or atrophy

# 5 年后, 模型坏了, 客户回 manual: senior 已经不会处理了

# 这就是 "skill atrophy through automation"
```

**Mitigation**: 永远把 X% (5-10%) case route to expert + model 学习他们的决策.

### 3.6 跟你 Indonesia refund tier 类比

你做 Indonesia refund tier 设计就是 hybrid:
- Tier 1: model auto-decision (70% volume, 0 cost)
- Tier 2: model recommend + collection rep confirm (25% volume, low cost)
- Tier 3: full human review (5% volume, normal cost)

总 throughput +70%, accuracy 没退步, 实际错误成本 < manual baseline. **这是 hidden-cost-aware design**.

---

## ⚙️ Problem 4: Rollback Strategy + Parallel Run

**核心**: 不能完全 rollback (浪费 deploy effort + 客户已经 used). 也不能不 rollback (客户每天受伤). 中间方案是 **parallel run + canary rollback**.

### 4.1 Rollback 模式

```python
class RollbackController:
    """Feature flag 控制每类 case 的 model 启用"""

    def __init__(self):
        self.routing_config = {
            'high_stake': 'manual',
            'medium_stake': 'model_with_human_review',
            'low_stake': 'model'
        }

    def route(self, case):
        category = self.categorize(case)
        return self.routing_config[category]

    def emergency_rollback(self, category):
        """1 行 config change 切回 manual"""
        self.routing_config[category] = 'manual'

    def gradual_rollback(self, category, percent):
        """10% case 走 manual, 90% 仍 model"""
        if random() < percent:
            return 'manual'
        return self.routing_config[category]
```

### 4.2 Parallel run pattern

```python
# Phase 1: 100% manual + 0% model (rollback完成态)
# Phase 2: 90% manual + 10% model (shadow + comparing)
# Phase 3: 50% manual + 50% model (A/B真比较)
# Phase 4: 10% manual + 90% model (verify scale stable)
# Phase 5: 0% manual + 100% model (full deploy)

def parallel_run(case):
    # Real path: manual
    actual_decision = manual_process(case)

    # Shadow path: model (no commit)
    shadow_decision = model.predict(case)

    # Log both for comparison
    log({
        'case_id': case.id,
        'manual': actual_decision,
        'model': shadow_decision,
        'agreement': actual_decision == shadow_decision
    })

    return actual_decision  # Manual wins
```

### 4.3 Canary deployment

```python
class CanaryRouter:
    def __init__(self, canary_percent=5):
        self.canary_percent = canary_percent

    def route(self, case):
        # 5% 流量走新 model, 95% 走 stable
        if hash(case.id) % 100 < self.canary_percent:
            return new_model
        return stable_model

    def health_check(self, window_hours=1):
        canary_perf = perf_metrics(new_model, window=window_hours)
        stable_perf = perf_metrics(stable_model, window=window_hours)

        if canary_perf['f1'] < stable_perf['f1'] - 0.02:
            self.canary_percent = 0  # 立即停 canary
            alert('canary regression, rolling back')
            return 'rollback'

        if canary_perf['f1'] >= stable_perf['f1']:
            self.canary_percent = min(self.canary_percent * 2, 100)
            return 'continue_expanding'
```

### 4.4 Communicating rollback to customer

```
Wrong way:
  "Sorry, we're rolling back the AI model."
  → Customer: 这是失败. 续约危险.

Right way:
  "We've identified a specific issue affecting category X.
   For X, we've reverted to manual for safety while we fix.
   For categories Y and Z (75% of volume), model continues
   to outperform manual by Δ%. We expect to re-enable X
   in 4 weeks with a fix."
   → Customer: 这是 controlled response, 你们在管.
```

### 4.5 Keep-model-running 的价值

```python
# 即使 rollback, 让 model 继续 shadow:
# 1. 收集 prod data
# 2. 比较 model vs manual decisions
# 3. 训练数据自动生成 (manual decision = label)
# 4. 不浪费 deploy capacity

def shadow_after_rollback(case):
    manual_decision = manual_process(case)

    # Model shadow
    model_decision = model.predict(case)

    if manual_decision != model_decision:
        # Disagreement → training signal
        training_data.append({
            'features': case.features,
            'human_label': manual_decision,
            'model_predicted': model_decision,
            'disagreement': True
        })

    return manual_decision
```

3 个月后 retrain on 这些 disagreement, model 重新 onboard 时表现大概率好得多.

---

## ⚙️ Problem 5: Trust Rebuilding with Customer

**核心**: 一次 model failure 客户对你信任降 50%. 不主动 rebuilds, 续约死. 4 个 lever 重建信任.

### 5.1 Communication cadence

```
Week 1: Daily 15-min standup with customer counterpart
  - Today's diagnosis findings
  - Tomorrow's investigation step
  - Customer questions / pressure

Week 2-4: Daily 15-min during active investigation
  - Standdown to weekly once root cause confirmed

Month 2-3: Weekly 30-min review
  - Remediation progress
  - Metric trends
  - New issues

Month 4+: Bi-weekly 30-min
  - Long-term health
  - Roadmap

Quarterly: 90-min QBR with leadership
```

### 5.2 Transparency through dashboard

```
Customer Dashboard (read-only access):

[Daily]
  Model decisions today:     12,841
  Auto-executed:              9,832 (77%)
  Routed to human:           2,587 (20%)
  Escalated:                   422 (3%)

  Accuracy vs manual:        +3.2%
  Cost per decision:         -67%
  Latency p99:                4.2s

[Drift indicators]
  Data drift detected:        2 features (mild)
  Model behavior drift:       none
  Outcome drift:              improving

[Last 7 days incidents]
  - Mar 15: 1h elevated error rate on EU region
            Root cause: weather feed delay
            Resolved: 14:30
  - Mar 18: Brief latency spike, no impact
            Resolved: 09:15
```

客户随时可见 → 不需要找你问 → 信任建立.

### 5.3 Joint ownership of action items

```
Wrong way: "We will fix it."
  → Vendor-customer dynamic, customer passive.

Right way: 
  "We've identified these 3 issues and 5 action items.
   3 are owned by us:
     - Re-train model on recent data (us, by week 2)
     - Add weather feature pipeline (us, by week 1)
     - Add monitoring for drift (us, by week 3)
   2 require your team:
     - Provide updated feature catalog for SKU classification (you, by week 1)
     - Approve the canary 10% rollout (your CMIO, by week 2)
   Joint review: end of week 4."
```

客户成为 partner, 不是 victim.

### 5.4 Overdeliver on first remediation

```
Customer expected:  "fix accuracy in 4 weeks"
You delivered:      "fix accuracy in 3 weeks + added 2 new features they asked for + 
                     wrote a runbook for them"

→ 信任度上升超 baseline. 续约几乎 sure.
```

### 5.5 Honest about uncertainty

```
Wrong: "We're 100% sure the fix works."

Right: "Based on diagnosis, we're 85% confident H1 + H3 is root cause.
        Fix should improve accuracy by 5-8 points within 2 weeks.
        We've set up 4 monitoring metrics — if any regress, we'll
        catch within 24 hours.
        Worst case (15% probability), we'll need 4 more weeks for 
        deeper investigation. Here's that contingency plan."
```

Honesty about uncertainty → customer trust 实际更高. False confidence → 一旦事情不顺信任崩.

### 5.6 跟你 voice agent rollout 类比

你 voice agent 上线时遇到 Brazil ASR issue, **你 daily standup + transparency dashboard + joint action items + honest H3 admission** — 这就是 trust rebuild 经验.

```
"Actually we went through this with Brazil market on voice agent.
 Initial accuracy was 76% vs 88% other markets. Customer (local
 ops director) was upset. We did:
 - Daily 15-min standup for 4 weeks
 - Built a dashboard showing accuracy by sub-region
 - Joint action: we'd retrain, they'd help collect 6-metro samples
 - Honest about H3: 'this isn't a model bug, our training data didn't
   represent your variation. We need 800K hours of Brazilian Portuguese
   from outside Rio.'
 - 6 weeks later: 86% accuracy
 - That ops director is now our biggest internal champion."
```

---

# Part 3 · 把 5 个问题串起来看

这 5 个 layer 拼起来就是 model-worse-than-manual 的全栈应对:

1. **Diagnostic framework** (Problem 1) — 5 hypothesis, H1 + H3 first
2. **Sliced eval** (Problem 2) — Aggregate 是 lie, slice 才是真相
3. **Hidden cost** (Problem 3) — Scale × error × stake. Hybrid > full auto.
4. **Rollback strategy** (Problem 4) — Canary + parallel run + selective rollback
5. **Trust rebuilding** (Problem 5) — Daily standup + dashboard + joint ownership + honest

面试场把这 5 个 layer 系统讲明 + quote 你 ConvFinQA negative result 经验 = **真 FDE deployment 觉悟**.

---

## 必问 clarifying questions

**1. Define "worse"**

> "What metric is worse — accuracy? Speed? User satisfaction? **Worse for the customer's KPI or for some technical metric we set**?"

**2. Worse by how much**

> "5% worse or 50% worse? In a controlled comparison or anecdotal?"

**3. Population overlap**

> "Is the model handling the **same cases** the manual process did? Or is it triggering on different inputs?"

**4. Time since deployment**

> "How long has it been live? 1 week (still ramping) vs 3 months (stable comparison)?"

**5. Customer's actual complaint**

> "What did the customer **specifically say**? 'Numbers are bad' vs 'one user yelled at me' is very different signal."

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-10 min | Clarify metric + magnitude + time + customer言语 |
| 10-25 min | 5 hypothesis classes, propose diagnosis order (H1+H3 first) |
| 25-40 min | Pick most likely hypothesis (usually H1 or H3), deep dive investigation |
| 40-50 min | Remediation by hypothesis + safeguard + parallel run |
| 50-60 min | Communicate to customer + trust rebuild plan |

---

## 简历专属 reframe

你的 **voice agent deployment** + **ConvFinQA ablation** 直接 reframe:

| 题里的情况 | 你做过 |
|---|---|
| Model worse than manual diagnosis | ConvFinQA 你做过 9 variant ablation — 都比 control 差! 这就是这道题的精确等价 |
| Apple-to-orange comparison | ConvFinQA "conditional acc on non-None preds" — 你已经做过这种 trick |
| Edge case dominance | Voice agent ASR 在 Brazil 方言上 degrade — 你处理过 |
| H4: feature pipeline failure | Voice agent 上线后 latency 漂移 / context window 漏 features 你 debug 过 |
| Roll back to manual safety | Voice agent fallback to human agent 你设计过 |
| Triage routing (model + human) | Indonesia refund tier 经典 case |
| Sliced eval by topic | ConvFinQA stratified 300 by 9 topic |
| Daily standup with customer | 7-market regional ops weekly sync |
| Honest H5 acknowledgment | Negative result paper 你公开发表 |

**主动说**:

> "Funnily this is exactly what happened with my ConvFinQA ablation experiment. I tried 9 variants of common agent patterns — typed lookup, critic, plan tags, all combinations — and **none beat the simple baseline**. I documented it as a negative result paper. The lesson I took: **before assigning model performance loss to 'model is bad', exhaustively rule out apples-to-orange and integration issues**.
>
> When that happens in customer-facing deployment, the response sequence I'd run:
> Day 1: Acknowledge + immediate safeguard for high-stake category — switch to manual for those, keep model on low-stake.
> Day 2-5: H1 + H3 in parallel — stratify by case difficulty, see if model is winning on easy + losing on rare. Brazil ASR case for voice agent was H3 + H2 combined; we needed Portuguese-specific training data, not 'better model'.
> Day 6-7: H4 if not H1/H3 — trace 20 prod errors end-to-end, check feature pipeline.
> Throughout: Daily 15-min standup with customer counterpart. Joint dashboard. Honest about uncertainty.
>
> The Brazil voice agent case is a complete worked example — 76% accuracy → 86% in 6 weeks, no retrain magic, just **honest H3 diagnosis + targeted data + transparency with customer**."

---

## 5 个 follow-ups

**Q1**: "Customer demands full rollback today. CFO threatening contract cancellation."

**A**: 谈判, 不投降:
- "We hear you. **Stake-1 / safety-critical category rolls back to manual today** (1 day to set up). Lower-stake stays on model so we can keep telemetry to diagnose."
- "If after 2 weeks we can't show concrete improvement plan, we agree to discuss broader rollback. But pulling all 6 months of work in 24 hours is in your interest to avoid too."
- Get this in writing.

**Q2**: "H5 turns out true. Model genuinely worse. Now what?"

**A**: **Graceful retreat**, not denial:
- "We were wrong about scope. The model **assists not replaces** the manual process. New goal: 50% volume reduction on bulk cases, 100% volume kept on critical."
- Renegotiate contract terms (consulting fees for ongoing optimization, not SaaS for replacement)
- Add specialist human review tier for cases model is bad at
- Track new KPI: total cost per case, not pure accuracy.

**Q3**: "Model is right but customer hates it because output looks different from human's. Cosmetic problem."

**A**: 这是 H4 变种 — UX integration issue, not model issue. 解:
- **Format normalization layer**: make model output **look like** human output (rounding, terminology, structure)
- **Side-by-side display** in UI for first month so customer can build trust
- **Confidence indicators** — show "model 88% sure" so user can intuit when to verify
- 通常 2-4 周 fix. **Don't retrain the model**.

**Q4**: "Manual process operator quit. Now there's no 'better' baseline to fall back to."

**A**: 紧急但好机会:
- **Hire interim contractor for 6 weeks** as fallback while we fix model
- Document operator's decision logic from their case history → **enrich training data**
- 紧急 retrain on operator's specific decisions
- **Don't let "they quit" become "model gets blamed" by default** — establish the model has known issues, set realistic expectations

**Q5**: "Customer wants you to add lots of 'rules' on top of model to fix specific cases."

**A**: 危险路. Rules-on-top spreads infinitely + becomes unmaintainable. Better:
- **Whitelist concrete failure modes**: 5-10 specific case patterns where manual rule overrides model. Document them. Cap at 20.
- **Track override rate**: if > 30% of decisions overridden by rules, the model itself needs retraining, not more rules.
- **Sunset rules**: each rule has expiry, retrain model to absorb the rule's intent.

---

## ❌ 易错点

1. **立刻 blame model** — 没诊断 jumping to "我们 model 有问题"
2. **立刻 blame customer** — "你们 integrate 错了" 出口
3. **没 5 hypothesis 框架** — 没结构化
4. **跳过 H1 apple-to-orange** — 最常见原因
5. **没 immediate safeguard** — diagnose 期间不保护 customer
6. **不敢说 H5** — 永远不承认 model 是错选
7. **直接 retrain** — 没诊断就 retrain, 大概率没解决根因
8. **跳过 sliced eval** — 看 aggregate 不看 segment
9. **过早 promise** — "2 周 fix" 没诊断前别说
10. **Rules-on-top death spiral** — 短期止血, 长期不可维护

---

## ✅ 加分项

1. **5-hypothesis decomposition** 完整说出来
2. **Apple-to-orange first** — 最常 root cause
3. **Triage routing (model + human)** 作为 H1/H3 standard fix
4. **Daily standup with customer** 期间
5. **Graceful retreat plan** for H5
6. **Negotiate rollback scope** 不全 yield
7. **Quote ConvFinQA negative result experience**
8. **Sunset rules** — 防 rules-on-top death spiral
9. **Sliced eval by 5+ axes** stratification
10. **Canary + parallel run** rollback pattern
11. **Joint ownership of action items** — customer partnership
12. **Honest about uncertainty** in remediation timeline

---

## 一句话总结

> **Model worse than manual diagnosis = 「不 panic 不 blame, 立 immediate safeguard, 5 hypothesis (H1 apple-to-orange + H3 edge case first), sliced eval by 5 axis, daily standup + transparency dashboard with customer, parallel run + canary rollback, honest H5 acknowledgment if true」**.
>
> 这道题考的是 deployment 真实经验. 真做过 production AI 的人会答, 没做过的人会 retrain 烧钱.

---

## Cheat Sheet

```
5 Hypotheses (diagnose 顺序 by likelihood):
  H1 Apple-to-orange (manual on easy cases only) — 40%
  H3 Edge case dominance (expert intuition rare) — 25%
  H4 Integration / feature pipeline fail — 15%
  H2 Distribution shift — 15%
  H5 Model genuinely wrong for task — 5%

Priority diagnose:
  H1 + H3 first (5 days, parallel)
  H4 fast (1-2 days)
  H2 medium (3 days)
  H5 last (only if others rule out)

Symptom → Hypothesis mapping:
  Different case distribution → H1
  Offline >> Online perf → H4
  Errors concentrated in rare → H3
  Recent features look weird → H2
  100 random errors structural → H5

Standard fix if H1 + H3 (65% cases):
  - Triage routing (90% common to model, 10% rare to human)
  - Specialist sub-model on rare cases
  - Confidence threshold escalation
  - Indonesia refund tier 是这个模式

Sliced eval axes:
  - customer_type
  - product_category
  - region
  - difficulty bucket
  - time_of_day
  - feature_completeness

Hidden cost considerations:
  - Error cost asymmetry (FP vs FN)
  - Scale amplification (100x volume × small error)
  - Loss of human safety net
  - Long-tail skill atrophy

Rollback strategy:
  - Selective by category (high-stake first)
  - Canary deployment (5% → 100%)
  - Parallel run during transition
  - Keep model shadow for retraining data

Customer comms cadence:
  Day 1: acknowledge + plan + safeguard
  Day 2-14: daily 15min standup
  Week 2-4: daily during fix
  Month 2+: weekly review
  Quarterly: leadership QBR

Trust rebuild 4 lever:
  - Communication cadence (daily standup)
  - Transparency dashboard (customer read access)
  - Joint ownership of action items
  - Overdeliver on first remediation
  - Honest about uncertainty

红线 (don't):
  - Blame customer
  - Blame model without diagnosis
  - Retrain blindly
  - Rules-on-top death spiral
  - Refuse H5 even if true
  - Promise timeline before diagnosis

Quote opportunities:
  - ConvFinQA 9-variant negative result
  - Voice agent Brazil ASR H3 + H2
  - Indonesia refund tier triage routing
```

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

> **Model worse than manual = 不 panic 不 blame, 立 immediate safeguard, 5-hypothesis diagnostic (H1 apple-to-orange first 40% / H3 edge case 25% / H4 integration 15% / H2 drift 15% / H5 真错 5%), retrain 永远是最后选项, 不敢承认 H5 = 死磕等死**. 你 ConvFinQA 9-variant 全输的负面 result 就是这道题精髓.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| H1 Apple-to-orange | manual 只处理 30% 易 case, model 全量 | 最常见 root cause (40%) |
| H2 Distribution shift | live data ≠ training, KS / PSI 检测 | 15% case |
| H3 Edge case dominance | expert 在 5% rare 表现强, model 学 bulk | 25% case |
| H4 Integration failure | offline OK, prod 缺 feature / null / wrong | 15% case, 修最快 |
| H5 Model genuinely wrong | structural 错误, task 不适合 ML | 5% case, 最难承认 |
| PSI | Population Stability Index, > 0.2 = drift | H2 检测主要指标 |
| KS test | Kolmogorov-Smirnov, 分布差异 | feature drift |
| Triage routing | confidence 高 auto, 中等 recommend, 低 escalate | H1+H3 标准 fix |
| Graceful retreat | 不硬卖全自动, 重新 scope 60% throughput | H5 承认时 |
| Canary deployment | 5% 流量新 model 监控, 健康自动扩 | rollback strategy |
| Parallel run | shadow model + manual 真路径并行 | 比较 + 训练数据 |
| Concentration analysis | 90% 错误集中在 5% slice → H3 | error distribution |
| Skill atrophy | 自动化后 senior 失去经验 | hidden cost long-term |
| Cost asymmetry | FP $5K vs FN $50K, 不对称 | hidden cost 设计 |
| Scale amplification | 100x volume × 同 error rate = 100x 总成本 | hidden cost #1 |
| Shadow log | rollback 后 model 仍跑 log, 当训练数据 | retraining 后续 |

### 🎯 5 个核心 framework

**Framework 1**: 5-Hypothesis Diagnostic Tree (H1→H3→H4→H2→H5)
- When: customer 投诉 "worse than manual"
- Algorithm: H1 apple-to-orange (Q: model 跟 manual 处理同 case 吗) → H3 edge case (Q: 错误集中 rare 吗) → H4 integration (Q: offline >> online?) → H2 drift (KS / PSI > 0.2?) → H5 structural (100 错误 sample, random or systematic?)
- Trade-off: H1+H3 cheap 2 天 / H5 expensive 5+ 天, 不轻易判 H5
- Tools: scipy.stats.ks_2samp, PSI = sum((actual%-expected%) * ln(actual%/expected%)), feature replay debugger

**Framework 2**: Sliced Eval (Multi-axis stratification)
- When: aggregate metric 是 lie 时
- Algorithm: axes = [customer_type, product_category, region, time_of_day, difficulty_bucket, feature_completeness] → 每 slice 计算 f1 / accuracy / precision / recall → regression detect delta < -0.02 + count > 100 → concentration analysis (90% err 在 5% slice = H3 信号)
- Trade-off: 太多 slice 小样本噪声大, count > 100 阈值
- Tools: Pandas groupby, scipy chi2, visual dashboard with █ bars

**Framework 3**: Hidden Cost of Automation
- When: 即使 accuracy 等于 manual, model 仍可能更贵
- Algorithm:
  - Error cost asymmetry: FP credit $5K vs FN $50, FN fraud $10K vs FP $100
  - Scale amplification: manual 100 case/day × 5% = $25K vs model 10000 × 5% = $2.5M
  - Loss of safety net: manual 有 peer review / manager approve, model 一上线全拆
  - Skill atrophy: senior 5 年后处理 rare case 也不会了
- Trade-off: 全自动 vs hybrid, 90% case hybrid 更稳
- Tools: confidence-based hybrid (> 0.9 + low-stake auto / > 0.7 recommend / < 0.5 escalate / high-stake always human)

**Framework 4**: Rollback + Parallel Run + Canary
- When: 不能全 rollback (浪费) 不能不动 (客户痛)
- Algorithm:
  - Selective rollback by category (high-stake first, low-stake last)
  - Canary 5% → health_check 1h → if regress 立停 / if equal 扩 2x
  - Parallel run: manual 是 real path, model shadow log, 不 commit
  - Keep model shadow even after rollback → 训练数据 (manual decision = label)
- Trade-off: parallel 双倍 compute, canary 慢
- Tools: feature flag (LaunchDarkly), routing_config dict, hash(case_id) % 100 < canary%

**Framework 5**: Trust Rebuilding 4-Lever
- When: model failure 后客户信任 -50%
- Algorithm:
  - Communication cadence: daily 15min standup wk1-4 → weekly month 2-3 → bi-weekly → quarterly QBR
  - Transparency dashboard: customer read-only access, daily decision count / accuracy / cost / latency / drift / incident log
  - Joint ownership: "3 actions on us, 2 on you" with timeline
  - Overdeliver first remediation: customer expects 4w, you deliver 3w + bonus
  - Honest uncertainty: "85% confident H1+H3 is root cause, contingency for 15%"
- Trade-off: high comm cost, but lower trust 完爆 续约
- Tools: dashboard Looker, weekly slide template, runbook

### 🌳 关键决策树

```
Symptom: "model worse than manual"
├── 立刻 acknowledge + immediate safeguard (high-stake → fallback feature flag)
├── Different case distribution? → H1 (40%) → triage routing
├── Errors in rare 5% case? → H3 (25%) → specialist sub-model
├── Offline >> online? → H4 (15%) → trace 20 errors, fix pipeline (30 min 修)
├── PSI > 0.2 on features? → H2 (15%) → retrain on recent
└── 100 sample structural? → H5 (5%) → graceful retreat, scope to 60% throughput

Rollback decision?
├── Safety-critical? → 立刻 fallback to manual (feature flag)
├── Selective by category? → high-stake manual, low-stake model 继续
├── Canary 5%? → 1h health check, auto-扩 or 退
└── Parallel shadow? → model 不 commit, log for retraining
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: Diagnostic Framework**
- 核心解法:
  ```python
  # H1: case count manual vs model
  manual.case_count < model.case_count * 0.7 → H1 confirmed
  # H2: PSI per feature
  compute_psi(train, prod) > 0.2 OR KS pval < 0.01 → H2
  # H3: error rate by rarity bucket
  rare_case_err > common_case_err * 2 → H3
  # H4: offline vs online gap
  offline - online > 0.1 → H4, trace 20 failures end-to-end (nulls, outliers, replay)
  # H5: 100 error structural sample
  ```
- Top 3 gotchas: 跳 H1 直接 retrain / 不 trace 20 prod errors / 不敢说 H5
- Tools: scipy.stats.ks_2samp, PSI = Σ (a-e)*ln(a/e), feature replay

**Problem 2: Sliced Eval**
- 核心解法:
  ```python
  axes = [customer_type, product_category, region, time_of_day, difficulty]
  for axis × value: compute f1 / accuracy / count
  detect_regression: delta_f1 < -0.02 AND count > 100
  concentration: if axis × value error_share > 0.3 → H3 signal
  ```
- Top 3 gotchas: 看 aggregate / 小样本 < 100 噪声 / 不 cross-tab "region × product"
- Tools: Pandas groupby, scipy chi2, visual dashboard with bar chart, Looker

**Problem 3: Hidden Cost**
- 核心解法:
  ```
  Asymmetry: FP credit $5K, FN $50 / FN fraud $10K, FP $100
  Scale: 100x volume × 5% err × $5K = $2.5M vs manual $25K
  Safety net: manual peer/manager review built-in, model 上线全拆
  Hybrid (Indonesia refund tier):
    Tier 1 (70%): conf > 0.9 + low-stake → auto
    Tier 2 (25%): 0.7-0.9 → recommend + human confirm
    Tier 3 (5%): conf < 0.5 OR high-stake → full human
  ```
- Top 3 gotchas: 全自动 vs hybrid 不考虑 / 不看 error cost / 忽略 skill atrophy
- Tools: cost matrix table, confidence calibration probe model

**Problem 4: Rollback Strategy**
- 核心解法:
  ```python
  routing_config = {high_stake: manual, mid: model_with_review, low: model}
  emergency_rollback(category): routing_config[cat] = 'manual'  # 1 line
  gradual_rollback(cat, 0.1): 10% case 走 manual
  CanaryRouter: hash(case_id) % 100 < 5; health_check 1h, regress → 0%, equal → 2x
  shadow_after_rollback: model 仍跑, disagreement → training_data
  ```
- Top 3 gotchas: 全 rollback (浪费) / 没 canary 直接 100% (爆雷) / rollback 不留 shadow
- Tools: LaunchDarkly feature flag, hash routing, perf_metrics windowed

**Problem 5: Trust Rebuilding**
- 核心解法:
  ```
  Cadence: daily 15min wk1-4 → weekly month 2-3 → bi-weekly → quarterly QBR
  Dashboard: customer read-only, daily decisions / accuracy / cost / drift / incident log
  Joint: "3 on us, 2 on you" with deadline
  Overdeliver: 4w expectation, deliver 3w + bonus
  Honest: "85% confident, 15% contingency plan"
  Voice agent Brazil quote: daily standup 4w + dashboard + joint 800K hr collection
  ```
- Top 3 gotchas: vendor-customer dynamic (我们 fix, 你 passive) / 100% confident promise / 跳 daily standup
- Tools: Looker dashboard, weekly slide template, runbook for customer

### 🔥 Production gotchas (top 15)

1. 立刻 blame model 没诊断 → 烧 GPU 烧 cycle 烧客户耐心
2. 立刻 blame customer → 政治灾难
3. 跳过 H1 apple-to-orange (40% case) → 错过最常见原因
4. 没 immediate safeguard → diagnose 期间客户每天受伤
5. 不敢说 H5 → 死磕 retrain 6 月不解
6. 直接 retrain 没诊断 → 大概率没解决根因
7. 没 daily standup → 客户每天怒一点
8. 没 stratification → aggregate 掩盖
9. Rules-on-top death spiral → 加 rule 永无止境
10. 全自动 vs hybrid 不考虑 → hidden cost 爆
11. 看 accuracy 等于 manual 就上线 → scale × cost 爆
12. Rollback 后 model 完全停 → 浪费 shadow 训练数据机会
13. 100% confidence promise → 一旦不顺 trust 崩
14. Skill atrophy 忽略 → 5 年后 senior 也不会
15. 不 cross-tab "region × product" → 双重边缘漏诊

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Negative result honesty | ConvFinQA 9-variant | 全 9 个 variant <= baseline, 公开论文 |
| Sliced eval methodology | ConvFinQA stratified 300 | by topic, financial reporting drop -15% |
| H1 apple-to-orange | Voice agent 跨 7 markets | manual 接 30% 易 case |
| H3 edge case | Voice agent Brazil ASR | rare 口音 H3 + H2 mix |
| H4 integration | Pipeline bug fix | offline 92% online 67% feature null |
| Hybrid (triage) | Indonesia refund tier 1/2/3 | 70/25/5 split |
| Trust rebuilding | Voice agent Brazil | daily standup + dashboard + joint |
| Graceful retreat | Refund tier 3 manual | 5% case 不勉强 auto |
| Parallel run shadow | Voice agent RL alignment | shadow before 切量 |

### 🎤 面试现场 quotables (top 8)

1. "Before I do anything, I'd put an immediate safeguard on safety-critical categories — feature flag back to manual within 4 hours"
2. "I'd diagnose H1 + H3 first in parallel — they cover 65% of real cases, and they're 2-day investigations"
3. "Don't retrain until you've done H4 — 30 minutes of pipeline tracing can save 3 weeks of GPU"
4. "I just published a negative result on ConvFinQA — 9 agent variants, all worse than baseline. I know what it feels like to honestly call H5"
5. "Aggregate metric is a lie — sliced eval by region × product × difficulty is the real diagnosis"
6. "Indonesia refund tier 1/2/3 is hidden-cost-aware design — 70% auto, 25% recommend, 5% full human. Accuracy didn't move, but error cost dropped"
7. "Rollback ≠ failure. We're rolling back category X for safety while we fix; Y and Z still beat manual by Δ%"
8. "Brazil ASR 76% vs 88% other markets. Daily standup 4 weeks, joint 800K-hour collection, honest H3 admission. That ops director is now our biggest champion"

### 🚨 红线 (top 10 anti-patterns)

1. Blame model without diagnosis
2. Blame customer
3. Retrain blindly
4. Rules-on-top death spiral
5. Refuse H5 even if true
6. Promise timeline before diagnosis
7. No immediate safeguard
8. No daily standup
9. No stratification (看 aggregate)
10. 100% confidence promise

### 📊 数字 anchors (面试必记)

| Metric | Value | Source |
|---|---|---|
| Hypothesis class likelihood | H1 40% / H3 25% / H4 15% / H2 15% / H5 5% | real-world distribution |
| H1+H3 cover | 65% cases | 优先 diagnose 平行 |
| Diagnose cost | H1 2d / H3 2d parallel / H4 1-2d / H2 3d / H5 5+ d | priority matrix |
| PSI threshold | > 0.2 = drift confirmed | scipy.stats |
| KS pval threshold | < 0.01 per feature = drift | continuous |
| OOM offline vs online | > 0.1 gap → H4 confirmed | feature pipeline bug |
| Hybrid tier split | Tier 1 70% auto / Tier 2 25% recommend / Tier 3 5% human | Indonesia refund |
| Confidence routing | > 0.9 auto / 0.7-0.9 recommend / < 0.5 escalate | hybrid decision |
| Daily standup | 15 min same time wk 1-4 | trust rebuilding |
| Canary | 5% → 1h health check → 2x or rollback | safety |
| Trust rebuild realistic | 3-6 months consistent professionalism | not 30 days |
| Stratified eval slice count | tenant / language / region / customer_tier / difficulty | 5 axes minimum |
| Sample size per slice | > 100 for reliability | statistical power |
| Error cost asymmetry | FP credit $5K vs FN $50 / FN fraud $10K vs FP $100 | hidden cost |
| Scale amplification | 100 case × 5% = $25K (manual) vs 10K × 5% = $2.5M (model) | 100x volume |
| Override outcome window | 7 days for resolution | training signal |
| Service credit | 3-month free + PE pro bono | post-failure offer |
| Auto-rollback regression | outcome -5pp vs control sustained 24h | safety circuit |

### ⚠️ 必避坑 (interview-specific)

| 坑 | 解法 | Quote |
|---|---|---|
| Blame model 没诊断 | 5-hypothesis first | "Before retrain, diagnose. H1+H3 cover 65% in 5 days parallel" |
| Blame customer | joint own | "Joint diagnosis, never blame" |
| 直接 retrain | H4 trace first | "30 min pipeline tracing can save 3 weeks of GPU" |
| 跳 H1 apple-to-orange | distribution stratify | "Manual 30% 易 case vs model 100%, must compare overlap" |
| 没 immediate safeguard | feature flag fallback | "High-stake categories get manual within 4 hours" |
| 不敢说 H5 | honest H5 ack | "I just published 9-variant ablation, all worse than baseline. ConvFinQA H5" |
| Aggregate metric | sliced eval | "Region × product × difficulty — concentration analysis reveals H3" |
| 全自动 vs hybrid | tier 1/2/3 | "Indonesia refund tier — 70/25/5 split, hidden cost down" |
| 100% confidence promise | honest uncertainty | "85% confident H1+H3, contingency for 15%" |
| Skill atrophy 忽略 | route 5-10% to expert | "Senior 5 年后 rare case 也会处理" |

