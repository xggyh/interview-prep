## Case #5 · Model Worse Than Manual — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/model-worse-than-manual.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`model-worse-than-manual.html`](questions/model-worse-than-manual.html)

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
