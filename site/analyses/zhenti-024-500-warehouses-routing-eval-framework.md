## Q24 · 500 仓库经理 + 99% 送达率 AI agent 评估框架

> "We're deploying an **AI agent that suggests delivery rerouting** to **500 warehouse managers**. Customer's existing rate is **97% on-time, target 99%**. **Design the evaluation framework** — how do you know the agent actually helps before / during / after rollout? What's your North Star metric?"

**中文翻译**:

> "我们要部署一个 **AI agent, 给 500 个仓库经理建议送货改派**. 客户现在 **on-time 送达率 97%, 目标 99%**. **设计评估 (evaluation) 框架** — 上线前 / 中 / 后, 你怎么知道 agent 真的有用? 你的 North Star (北极星) 指标是什么?"

**Round**: System Design (60 min)
**出处**: Exponent 2026 FDE · 公司: Palantir Foundry / Anduril / o9 / Anthropic Enterprise · 行业: logistics / supply chain
**约束**: 500 warehouse heterogeneity (西雅图 vs 拉斯维加斯) / 97% baseline 已经高, 边际收益难证明 / agent suggests, manager decides (HITL) / counterfactual hard (反事实评估) / drift over time (天气/促销/staff turnover) / regulatory none but operational SLA

---

## 📖 术语速查 (本题用到的)

> 这题考的不是 ML 模型, 是 causal inference + A/B 设计. 名词不懂会答错方向. 5 min 看完.

### 业务 / 行业

| 术语 | 解释 |
|---|---|
| **On-time delivery rate** ⭐ | 在承诺时间窗内送达的比例. 这题 97% → 99% target. |
| **Promised window** | 承诺时间窗 (e.g. 2-4pm). 超出 = miss. |
| **Last-mile** | 最后一公里 — 从仓库到客户的最终配送段, 成本最大. |
| **Hub** | 物流枢纽 — 仓库 / 中转站. |
| **Expedite** | 加急配送 — 用更贵的方式 (UPS Next Day) 保证准时. Agent 容易 game 这个. |
| **NPS (Net Promoter Score)** | 客户推荐净值 — 业务体验指标. |
| **Driver attrition** | 司机流失率 — agent 不能压榨 driver 导致离职. |
| **Hyperspace UI** | Palantir 的前端 platform — warehouse manager 操作界面. |

### Eval / A/B 设计 (核心)

| 术语 | 解释 |
|---|---|
| **Baseline-relative metrics** ⭐ | 每个 warehouse 跟自己历史比, 不跟 fleet 平均比. 异质性大时必备. |
| **North star metric** | 唯一最重要的业务目标指标 (这题: 加权 on-time rate). |
| **Leading indicator** | 早于 outcome 出现的信号 (e.g. acceptance rate 早 outcome 14-30 天). |
| **Guardrail metric** | 防 agent 作弊的反向指标 (e.g. cost / driver hours / 投诉). |
| **Counter metric** | 防 dashboard 偏的指标 (e.g. bottom-quartile, worst-day). |
| **A/B test (RCT)** ⭐ | Randomized Controlled Trial — 因果推断金标准. |
| **Cluster random** ⭐ | 按 cluster (这题 = warehouse) 分组随机, 不按 request 随机. 防 spillover. |
| **Stratified random** | 分层随机抽样 — 在每个 stratum 内做 random. |
| **Stratification** | 分层 — 按 baseline / region / volume 把 warehouse 分组. |
| **Spillover effect** | 溢出效应 — treat 组影响 control 组 (e.g. 共享 driver pool). |
| **MDE (Minimum Detectable Effect)** | 能检测到的最小效应大小. Power 越高 MDE 越小. |
| **Statistical power** | 检验功效 (1 - β), 通常要求 0.8 或 0.9. |
| **α / β** | α = 假阳率 (通常 0.05); β = 假阴率 (通常 0.1-0.2). |

### Causal Inference (深度)

| 术语 | 解释 |
|---|---|
| **Counterfactual** ⭐ | 反事实 — "如果 agent 决定, outcome 是什么?" |
| **Confounder / confounding** | 混淆变量 — 同时影响 treatment 和 outcome 的因素. |
| **Doubly-Robust (DR)** ⭐ | 双重稳健估计器 — outcome model + IPW 结合, 任一对即一致. |
| **IPW (Inverse Propensity Weighting)** | 用 propensity 倒数加权, 校正 selection bias. |
| **Propensity score** | 倾向得分 — P(treatment | context), 用模型估. |
| **Synthetic control** | 合成对照 — 用 control 加权组合构造 treated 的反事实. |
| **DiD (Difference-in-Differences)** ⭐ | 双重差分 — (treat_post - treat_pre) - (control_post - control_pre). 业务友好. |
| **Parallel trends assumption** | DiD 的核心假设 — treat 和 control 无 treatment 时趋势平行. |
| **ITT (Intent-to-Treat)** | 按分配分析 (不按实际接受 / 拒绝). manager 拒绝 agent 仍算 treated. |
| **ATE (Average Treatment Effect)** | 平均处置效应. |
| **HTE (Heterogeneous Treatment Effect)** | 异质处置效应 — 不同 subgroup 反应不同. |
| **Causal forest / X-learner** | 估计 HTE 的现代方法. |
| **RLHF** | Reinforcement Learning from Human Feedback — 用 override 数据反向训 agent. |

### Rollout / 阶段

| 术语 | 解释 |
|---|---|
| **Offline replay** ⭐ | 用历史数据跑 agent, 看建议 vs 实际决定. |
| **Shadow mode** ⭐ | 影子模式 — agent 在线但建议不显示, 收集真实数据. |
| **Concordance** | 一致率 — agent 建议 == manager 实际的比例. |
| **Gradual / cohort rollout** | 分批 rollout (100 → 250 → 500). |
| **Halt criteria** | 触发暂停 / 回滚的红线指标. |
| **Holdout / preserved control** | 永远不上 agent 的 10% 用作长期对照. |
| **Cohort** | 队列 — 一批 warehouse 一起 rollout. |
| **Power calculation** | 计算 sample 多大才能 detect 效应. |

### Drift / 监控

| 术语 | 解释 |
|---|---|
| **Feature drift** | 输入数据分布漂移. |
| **Outcome drift** | 输出 / outcome 分布漂移. |
| **Concept drift** | input → output 的映射关系变了. |
| **PSI (Population Stability Index)** ⭐ | 群体稳定指数 — 监控数据分布漂移. PSI > 0.2 = 明显漂移. |
| **KS-statistic** | Kolmogorov-Smirnov 检验 — 分布差异度量. |

### HITL / Engagement

| 术语 | 解释 |
|---|---|
| **HITL (Human-In-The-Loop)** ⭐ | 人在循环 — agent 建议, 人决定. 这题 manager 是 HITL. |
| **Acceptance rate** | 接受率 — manager 接受 agent 建议的比例. 60-80% 健康. |
| **Override / Override reason** | 推翻 / 推翻原因 — manager 拒绝 agent 时的原因 (UI dropdown). |
| **Rubber stamping** | 橡皮图章 — manager 不思考全接受, agent 错了也照办. 危险信号. |
| **Time-to-decide** | 决策时长 — manager 看 suggestion 后多久点接受 / 拒绝. |
| **Manager segmentation** | 用户分群 — heavy / selective / rejector / rubber-stamper. |

### 数据 / 基础设施

| 术语 | 解释 |
|---|---|
| **Iceberg** | 数据湖表格式. |
| **Decision log / Outcome log** | 决策 / 结果日志, 用于 eval. |
| **Databricks** | 数据 + ML 平台. |
| **PagerDuty** | 告警 + on-call 调度. |
| **Datadog** | 监控 / observability 平台. |

---

## 这道题在考什么

不是考你 LLM eval, 是考你**在已经 97% baseline 上证明 agent 有用**, 哪些反直觉:

1. **Baseline-relative metrics** — 不能只看 absolute 99%, 要 per-warehouse baseline (西雅图 historical 98% vs 拉斯维加斯 92% — 给到 99% 难度天差地远)
2. **Counterfactual evaluation** — 500 manager 不一定听 agent, 即使送达率涨了, 是 agent 还是 manager 直觉?
3. **A/B by warehouse, not by request** — 同一 warehouse 用 / 不用 agent 会造成 manager 困惑, 必须 cluster random
4. **Shadow mode** before live — agent 在背后跑, 不显示 suggestion, 对比 agent 建议 vs manager 实际决定的 outcome
5. **Engagement signal** — manager 是否接受 agent 建议 是 leading indicator (信不信)
6. **Drift detection** — 旺季 (Q4 promo) / 异常天气 / staffing crisis 时 agent 表现怎样, 不只看 average
7. **HITL eval** — manager 最终拍板, 你的 eval 要 attribute 决策, 不能 confound
8. **菜鸟答案失败点**: "我用 accuracy / F1 score, 跑 holdout test set" — 完全错. 这是 sequential decision-making with delayed outcome, 不是分类问题. 需要 causal inference + A/B + counterfactual simulation.

---

## 必问 clarifying questions

1. **Decision authority**: agent 直接 reroute 还是只建议给 manager? 99% case 是后者 (HITL)
2. **Outcome definition**: "送达" = on-time? in-condition? customer-rated? 不同 outcome metric 完全不同的 eval
3. **Time horizon**: rollout 想多久看到 99%? 3 个月 vs 1 年, 影响 sampling power
4. **Cost dimension**: 是不是单纯 send 更多 driver / 更贵 expedite 就能 99%? agent 必须不增加 cost
5. **Existing data**: 多少历史 routing decisions + outcomes? 决定 counterfactual 可行性
6. **Baseline mechanism**: manager 现在用什么决策? 系统 default + 直觉? 是否有 "current manual" 数据
7. **External shocks**: 旺季 (Q4) / 天气 / labor 是 noise 还是要在 eval 里 stratify
8. **Approval power**: 升级到 99% 是 board-level 还是 ops-team level? 影响 eval rigor

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|------|------|------|
| 1 | Clarify + outcome def | 5 min | 锁 outcome metric + HITL 程度 + time horizon | "三件事先锁: outcome 是 on-time only 还是综合 cost? agent 是 advise 还是 act? horizon 3 月 还是 1 年?" |
| 2 | Metric hierarchy | 8 min | North star + leading + guardrail | "North star: per-warehouse outcome rate. Leading: engagement + recommendation quality. Guardrail: cost, driver hours, customer complaint" |
| 3 | Per-warehouse baseline | 7 min | Stratify by warehouse, baseline 历史 | "每个 warehouse 自己跟自己比, 不跟 fleet average 比" |
| 4 | Eval framework stages | 12 min | Offline → shadow → A/B → full rollout | "4-stage gate: offline (历史 replay), shadow (在线但不显示), A/B (cluster random), full rollout" |
| 5 | Counterfactual + causal | 10 min | Doubly-robust estimation, synthetic control | "Counterfactual 关键. 我用 doubly-robust + synthetic control 估反事实" |
| 6 | Engagement / HITL signals | 5 min | Acceptance rate, override rate, time-to-decide | "Manager 接受率是 leading indicator, override rate 是 negative signal" |
| 7 | Drift + monitoring | 7 min | Concept drift, distribution shift, alert | "Drift detection: feature drift + outcome drift + per-warehouse cohort" |
| 8 | Trade-offs + close | 6 min | 学术 rigor vs business speed | "Doubly-robust 是 gold standard, business 可能接受 difference-in-differences as 80% solution" |

---

## 端到端架构图 (ASCII)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│   Production: 500 warehouses, manager-facing AI agent                                  │
│                                                                                        │
│   Manager (Hyperspace UI)                                                              │
│      ▼                                                                                 │
│   Agent recommends reroute → Manager accepts / overrides → Execute → Outcome later     │
│      │                                  │                                              │
│      │ log: (warehouse, ts,             │ log: (decision, ts, override_reason)        │
│      │       suggestion, context,       │                                              │
│      │       confidence)                ▼                                              │
│      └─────────────────────────────► Decision Log (Kafka → Iceberg)                    │
│                                                                                        │
│   Driver dispatch system → Delivery completion → Outcome:                              │
│   (on_time, in_condition, cost, customer_rating, driver_miles)                         │
│                                              │                                         │
│                                              ▼                                         │
│                                       Outcome Log (Iceberg)                            │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│   Eval Framework  (Databricks notebooks + airflow scheduled + custom Python)            │
│                                                                                        │
│   Stage 1: OFFLINE EVAL (historical replay)                                            │
│   ┌──────────────────────────────────────────────────────────────────────┐             │
│   │ Replay 6 month historical decisions                                  │             │
│   │ For each (warehouse, day):                                           │             │
│   │   ▸ agent_suggestion = agent.predict(historical_context)             │             │
│   │   ▸ actual_manager_decision = log[warehouse, day]                    │             │
│   │   ▸ actual_outcome = outcome[warehouse, day]                         │             │
│   │   ▸ counterfactual_outcome = doubly_robust_estimate(...)             │             │
│   │ Metric: % of warehouse-days where agent ≥ manager (paired comparison) │             │
│   └──────────────────────────────────────────────────────────────────────┘             │
│                                                                                        │
│   Stage 2: SHADOW MODE (3 weeks)                                                       │
│   ┌──────────────────────────────────────────────────────────────────────┐             │
│   │ Agent runs LIVE on real context but suggestion NOT shown to manager  │             │
│   │ Logs: (agent_suggestion, manager_actual_decision, outcome)           │             │
│   │ Allow comparison: agent ≈ manager (concordance)                      │             │
│   │ Gate: if agent disagrees badly + outcome would be worse, halt rollout │             │
│   └──────────────────────────────────────────────────────────────────────┘             │
│                                                                                        │
│   Stage 3: A/B BY WAREHOUSE (cluster random)  (8 weeks)                                │
│   ┌──────────────────────────────────────────────────────────────────────┐             │
│   │ Stratified random:                                                   │             │
│   │   - Control: 50 warehouses, no agent (manager only)                  │             │
│   │   - Treat:   50 warehouses, agent suggestion shown                   │             │
│   │   - Strata: warehouse size, region, baseline ontime                  │             │
│   │ Outcome: on-time rate diff (treat - control), per-strata             │             │
│   │ Power: with 50 warehouses × 8 weeks × ~500 deliveries/day            │             │
│   │   → detect 0.5pp lift with 90% power                                 │             │
│   └──────────────────────────────────────────────────────────────────────┘             │
│                                                                                        │
│   Stage 4: GRADUAL ROLLOUT (4 weeks → 100%)                                            │
│   ┌──────────────────────────────────────────────────────────────────────┐             │
│   │ Cohort rollout: 100 → 250 → all 500                                  │             │
│   │ Per-cohort: 2-week observation, regression detection                 │             │
│   │ Halt criteria: any guardrail breach (cost +5%, complaint +20%)       │             │
│   └──────────────────────────────────────────────────────────────────────┘             │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│   Post-launch monitoring (continuous)                                                  │
│                                                                                        │
│   ▸ Per-warehouse outcome dashboard (rolling 30d, 7d, 1d)                              │
│   ▸ Drift detection:                                                                   │
│       - Feature drift (PSI on agent inputs)                                            │
│       - Outcome drift (per-warehouse cohort vs historical)                             │
│       - Acceptance rate drift (manager 拒绝率 trend)                                   │
│   ▸ Alert routing:                                                                     │
│       - Per-warehouse outcome regression > 2pp → PagerDuty (P2)                        │
│       - Fleet-wide acceptance < 50% sudden → ML team (P3)                              │
│   ▸ Quarterly causal analysis:                                                         │
│       - Synthetic control reconstruction                                               │
│       - Difference-in-differences vs preserved control 10% (10 永远 not get agent)     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 详细设计 (60-min walkthrough)

### Phase 1: Clarify + outcome definition (澄清 + 结果定义) (5 min)

开口锁:
- "Outcome metric: 'on-time' 是 promised window 内吗? 比如 promised 2pm 实际 3pm 算 fail?"
- "Agent advises or acts? 99% case 是 advise + manager 决定. 影响 attribution"
- "Time horizon: 3 个月看到 99% 还是 12 个月? 影响 sample size + 是否能 isolate seasonal"
- "Cost guardrail: 如果送达 99% 但 cost +20%, business 接受吗?"

我假设: outcome = on-time within promised window AND not-damaged, agent advise (manager decide), horizon = 6 months to reach 99% sustained, cost guardrail < 105% baseline.

KPI clarity:
- **North star**: per-warehouse on-time rate (delivery in window + intact), weighted by delivery volume
- **Leading**: manager acceptance rate of agent suggestions
- **Guardrail**: cost per delivery, driver hours/delivery, customer complaint rate, manager override reasons

### Phase 2: Metric hierarchy (指标层级) (8 min)

不要只一个 metric, 三层:

**North star (1 个)**:
- Weighted on-time rate (delivery in promised window AND intact AND received) — 衡量真正业务目标 99%

**Leading indicators (3-5 个)** — 早于 outcome 现的信号:
- Manager acceptance rate (% suggestion accepted by manager): leading signal of agent trust
- Recommendation quality (% suggestion that *would have* improved outcome based on counterfactual)
- Time-to-decide (manager 看 suggestion 后多快做决定): proxy for cognitive load
- Suggestion coverage (% of routing decisions where agent had non-trivial recommendation)
- Override reasons distribution (taxonomy: "agent missed weather", "manager local knowledge", etc.)

**Guardrails (5-7 个)** — 防 agent 拿"作弊"方式刷指标:
- Cost per delivery (US$): agent 不能让人都用 expedite 来 99%
- Driver hours per delivery: 不能压榨 driver
- Customer complaint rate (per 1000 deliveries)
- Customer NPS (sampled survey)
- Damaged-in-transit rate
- Driver attrition rate (per quarter): 不能让 driver 因为不合理 routing 跳槽
- Hub utilization variance: 不能 over-route 某 hub 累瘫

**Counter metrics** — 防 dashboard 偏:
- Bottom-quartile warehouse outcome (不只看 average, 看最差的 25%)
- Worst-day outcome (最差一天)

为什么三层 + counter:
- North star 滞后: 看 outcome 要 1-3 天 delivery cycle
- Leading 让你早知道 trouble (acceptance 跌等于将来 outcome 跌)
- Guardrail 防 game (不能为 99% 牺牲 cost)
- Counter 防 average-shifting hide variance

### Phase 3: Per-warehouse baseline (按仓库定基线) (7 min)

**关键洞察**: 500 warehouse heterogeneity 巨大. 西雅图 hub 处理 5000/day deliveries 经验老到 baseline 98%; 拉斯维加斯小 hub 800/day baseline 92%; 鳳凰城 大 promo season 一时间 85%.

**统一目标 99% 是错的**. 正确:
- 每 warehouse 自己 baseline (rolling 6-month pre-agent)
- Target = baseline + Δ, Δ 大小因 warehouse 而异 (低 baseline 提升空间大, 高 baseline 提升难)

**分层 (stratification)**:
```python
warehouse_strata = stratify(warehouses, dims=[
    'baseline_ontime_quartile',  # Q1/Q2/Q3/Q4
    'region',                    # 5 region
    'volume_decile',             # daily delivery volume
])
# 500 warehouse → ~20 strata, each ~25 warehouse
```

**目标 redefinition**:
- 不是 "99% by Dec 2026"
- 而是 "every warehouse +1pp on baseline by Q4, weighted-average reaches 99% by Q1 2027"

**Per-warehouse leaderboard** (操作意义):
- 不公开排名 (避免压力 distort manager 行为)
- 内部 leadership see: top mover, bottom mover, agent contribution % to mover
- Bottom-quartile manager 1:1 from regional director

### Phase 4: 4-stage eval pipeline (四阶段评估流水线) (12 min)

**Stage 1: Offline historical replay (week 1-2)**

```python
historical_data = load('2024-09 to 2025-08, 500 warehouse, all routing decisions')
# ~500 warehouse × 365 day × ~50 decisions/day = ~9M decision-rows

for warehouse, day in warehouses × days:
    context = historical_data[warehouse, day].context  # weather, inventory, demand
    actual_decision = historical_data[warehouse, day].manager_decision
    actual_outcome  = historical_data[warehouse, day].outcome
    
    agent_decision  = agent.predict(context)
    
    # Concordance: does agent agree with manager on 80%+?
    concordance = (agent_decision == actual_decision)
    
    # Counterfactual: what would have happened if agent's decision?
    counterfactual_outcome = doubly_robust(
        context=context,
        treatment=agent_decision,
        observed_outcome=actual_outcome,
        observed_decision=actual_decision,
        propensity_model=...,
        outcome_model=...,
    )
    
    # Metric: did agent's decision >= manager's decision (paired)?
    win_loss = compare(counterfactual_outcome, actual_outcome)

# Aggregate
metrics = {
    'concordance_rate': mean(concordance),  # 0.78
    'agent_wins_pct': mean(win_loss == 'win'),  # 0.32
    'agent_loses_pct': mean(win_loss == 'lose'),  # 0.15
    'tied_pct': 0.53,
}
```

Gate: agent_wins > agent_loses by 5pp, concordance > 70%, no warehouse has catastrophic counterfactual

**Stage 2: Shadow mode (week 3-5)**

Agent runs live on real-time data. 但 **suggestion 不显示给 manager** (manager 还是按自己经验决定). 我们 log:
- Real-time agent_suggestion
- Actual manager_decision
- Outcome (24-72h delayed)

为什么 shadow:
- Offline replay 假设 historical context = future context, 但 distribution drift 可能
- Live shadow 验证 in-production data pipeline, model deploy correct
- 收集 "if you had shown this suggestion to manager, would they have changed?" — virtual A/B

3 weeks × 500 warehouse × 50 decisions/day = 5M decisions of shadow data. Stat power 强.

Gate: shadow vs offline concordance 接近 (< 5pp drift), no live infra issue

**Stage 3: Cluster random A/B (week 6-13)**

不能 per-decision random (同一 warehouse 一时给 agent 一时不给 → manager 困惑 / spillover). **必须 cluster-by-warehouse**.

设计:
```python
# Stratified random sampling
strata = stratify(500_warehouses, by=[baseline_quartile, region, volume_decile])
control = random_sample(strata, n_per_stratum=2)  # ~40 warehouse
treat   = random_sample(strata, n_per_stratum=2)  # ~40 warehouse
# Remaining 420 stay on current process

# Run for 8 weeks
for week in 8_weeks:
    for w in control: # no agent
    for w in treat:   # agent suggestion shown
    for w in rest:    # no change (still part of pre-rollout baseline)

# Analysis
treat_ontime = ...
control_ontime = ...
diff_in_diff = (treat_post - treat_pre) - (control_post - control_pre)
```

**Power calculation**:
- Baseline 97%, target lift 2pp to 99%
- σ across warehouse-week ≈ 1.5pp (variance)
- 40 warehouse × 8 weeks × 500 deliveries = 160K deliveries treat
- Detectable effect (α=0.05, β=0.1): 0.4pp lift detectable

→ 40 warehouse × 8 weeks 够 detect 0.5pp lift (我们想看 2pp). 富余.

**Spillover risk**: 邻近 warehouse share driver pool, agent reroute 1 个可能影响邻居. Mitigation: cluster random by region (集中 control/treat 在 region 内, 减少 spill).

**Stage 4: Gradual rollout (week 14-17)**

Cohort 1: top 100 + bottom 100 = 200 (mixed performance for diversity)
Cohort 2: + middle 250 = 450
Cohort 3: + remaining 50 = 500

每 cohort 2 weeks observation, regression test 通过才下一 cohort.

Halt criteria:
- Per-warehouse on-time regression > 2pp (P0)
- Cost +5% (P1)
- Customer complaint +20% (P1)
- Manager acceptance < 30% (P2)

### Phase 5: Counterfactual + causal inference (反事实 + 因果推断) (10 min)

这是 staff-level 的标志. 99% of candidates 不会答这层.

**Why counterfactual is hard here**:
- We observe (decision, outcome). 我们想知道 "如果 agent 决定, outcome 是什么".
- Naive: train regression on (decision, context) → outcome. But manager_decision is itself a function of context, confounded.
- Need to break confound: doubly-robust, IPW, or A/B.

**Methods (in order of rigor)**:

**1. RCT (gold standard)** — Stage 3 A/B 是这个.

**2. Doubly-Robust estimator** — when no A/B:

```
DR(x) = E[Y | T=t, X=x] (outcome model)
      + I(T=t)/π(t|x) * (Y - E[Y|T=t, X=x])  (IPW correction)

where π(t|x) = propensity score = P(manager_decision=t | context=x)
```

DR is consistent if EITHER outcome model OR propensity model is correct. Robust.

**3. Synthetic control** — for ongoing post-launch eval:
- Pick 50 warehouse 永远 not get agent (preserved control)
- For each treated warehouse, construct synthetic counterfactual = weighted combo of control warehouses
- Diff = treated - synthetic

**4. Difference-in-differences (DiD)** — simpler, business-friendly:
```
ATE = (treat_post - treat_pre) - (control_post - control_pre)
```
Assumes parallel trends. Easier to communicate to business.

**Implementation**: 主用 DR 给 ML team, DiD 给 business stakeholder ("简单减一减").

**Edge cases**:
- Manager rejects agent suggestion → still counts as "treated" (intent-to-treat ITT)
- Warehouse 部分 manager 接受 部分不接受 → cluster-level 仍 random, ITT 仍 valid

### Phase 6: Engagement + HITL signals (参与度 + 人在循环信号) (5 min)

Agent advises, manager decides. **Engagement is leading indicator**.

**Acceptance rate**:
- 100% acceptance: manager 没在思考 (rubber stamp), agent 错了也接受 — bad
- 0%: manager 不信任 — bad
- 60-80%: healthy disagreement, agent adds value 但 manager 用 local knowledge override 部分

**Override reasons taxonomy**:
- "Agent missed local context" (weather, road closure unknown)
- "Cost too high" (agent picked expedite, manager 用 cheaper)
- "Manager intuition" (5+ year veteran, knows specific customer)
- "Agent error" (real bug, log to ML team)

每 override 强制要求 manager 选 reason (UI dropdown, < 3 sec interaction).

**Engagement signals dashboard**:
- Per-warehouse acceptance rate trend
- Per-manager acceptance rate (some manager 60%, some 90% — different trust)
- Override reason distribution shifts (mix 偏 "agent error" 意味着真的 quality 下降)
- Time-to-decide (manager 看 suggestion 后多久点接受/拒绝)

**Manager-level segmentation**:
- "Heavy adopter": > 80% accept, < 30s decide → 给他们 advanced features
- "Selective adopter": 50-80% accept, > 60s decide → 健康
- "Rejector": < 30% accept → 1:1 training, understand barrier
- "Rubber stamper": > 95% accept, < 5s decide → concerning, agent 错了也照办, 加 friction (要求注释)

### Phase 7: Drift detection + monitoring (漂移检测 + 监控) (7 min)

Long-tail problem: agent 在 Q3 表现好, Q4 promo + winter weather 不一定.

**3 类 drift**:

**(a) Feature drift** — agent input distribution 变
- PSI (Population Stability Index) on key features: order_volume, weather_severity, staff_count, inventory
- PSI > 0.2 = significant shift → alert ML team
- Per-warehouse PSI (locality 重要)

**(b) Outcome drift** — outcome distribution 变 (与 agent 无关 / 与 agent 有关)
- Per-warehouse cohort outcome rolling 7d / 30d
- Pre-launch baseline as reference
- Drift > 1pp → investigate

**(c) Concept drift** — relationship (context → outcome) 变
- Train shadow model on recent 30d, compare predictions to original agent
- High divergence = concept changed (e.g., new last-mile vendor 改了 dynamics)

**Alert routing**:
| Signal | Severity | Channel |
|---|---|---|
| Per-warehouse outcome -2pp 7d trailing | P2 | PagerDuty → ops oncall + regional director |
| Fleet outcome -1pp 30d trailing | P2 | PagerDuty → ML team + ops VP |
| Acceptance rate -10pp 7d trailing | P3 | Slack → ML team |
| Feature PSI > 0.2 | P3 | Slack → ML team |
| Cost / driver hour > +5% | P1 | PagerDuty → ops VP |
| Customer complaint > +20% | P1 | PagerDuty → CX VP + ops VP |

**Quarterly causal re-eval**:
- Synthetic control reconstruction (using preserved 10% never-treated)
- DiD on rolling quarter
- Per-strata effect heterogeneity (does agent help low-baseline warehouses more? expected yes)

### Phase 8: Trade-offs + alternatives (权衡 + 备选方案) (6 min)

**Decision 8.1 — Rigor vs business speed**

| 选项 | Pros | Cons |
|---|---|---|
| RCT 8 weeks before any rollout | Causal certainty | Slow, business 急 |
| Shadow + DiD only | Fast | Causal weaker |
| Offline replay only | Fastest | Distribution drift risk |

我推: 4-stage gate (offline → shadow → A/B → rollout). 8 weeks A/B 不能砍, 这是 99%-target 的 board-defensible.

**Decision 8.2 — Centralized eval team vs federated**

| 选项 | Pros | Cons |
|---|---|---|
| Centralized (我们 ML team 全管) | Consistency, expertise | Slow, doesn't scale to 50 customers |
| Federated (我们提供 framework, customer ops 跑) | Scale, customer ownership | Less rigor |

我推: hybrid — 我们提供 eval framework (code + dashboard template) + 培训 customer ops team, 关键 RCT 由我们 ML team operate, ongoing monitoring 给 customer.

**Decision 8.3 — Stratification dimensions**

Pick wisely, 太多 stratum 每 stratum sample 小. 我选 3:
- baseline quartile (Q1/Q2/Q3/Q4) — 关键, 因为效果 heterogeneity
- region (5) — 季节性 + driver pool
- volume decile (D1-D10) — small vs large warehouse 动态不同

500 / (4×5×10) = 仍只 2.5 warehouse/stratum, 太少. 折中: 4×5×3 = 60 stratum, 8 warehouse 平均. Match 8 weeks × 500 deliveries 够 power.

**Decision 8.4 — Pricing of agent suggestion based on cost**

Agent 可能为 99% 推 expedite (rush delivery, +50% cost). Guardrail 防止. 还可以让 agent 直接 see cost in reward function:

```
agent.optimize(
    objective = on_time_rate - λ * cost - μ * driver_hours,
    λ = $5 per delivery cost,
    μ = $20 per driver hour,
)
```

让 agent 自带 cost-awareness 而不是只靠 guardrail kill.

---

## 关键决策点 (with rationale)

1. **Per-warehouse baseline 而不是 fleet average target** — 西雅图 vs 拉斯维加斯 起点不同, 一刀切 99% 不可能 / 不公平.

2. **4-stage gated eval (offline → shadow → A/B → rollout)** — 跳任何 stage 都是 risk. Shadow 验 prod pipeline, A/B 给 causal.

3. **Cluster random by warehouse, not by request** — 避免 manager 困惑 + 减少 spillover.

4. **Doubly-robust + DiD parallel** — DR 给 ML rigor, DiD 给 business 简单证据.

5. **Engagement (acceptance rate) 为 leading indicator** — 早 outcome 14-30 天 看到 trouble.

6. **Override reason taxonomy 强制** — manager 拒绝时给 reason, 这是 product feedback data, 比任何 ML metric 都 actionable.

7. **Counter metrics (bottom-quartile, worst-day)** — 防止 average lift hide variance. 99% sustained 比 99% average 难.

8. **Preserved 10% never-treated control** — quarterly causal re-eval, long-term agent health check.

---

## 数字 (capacity sizing, cost math)

**Volumes**:
- 500 warehouse × 50 routing decisions/day × 365 = 9.1M decisions/year
- Each decision: context ~5KB JSON → 45GB/year
- Outcome data: ~1KB per delivery × 200M deliveries/year = 200GB/year

**A/B power**:
- Treat 40 warehouse × 8 weeks × ~500 deliveries/warehouse-day = 1.1M deliveries
- Baseline σ across warehouse-week ≈ 1.5pp
- Minimum detectable effect: 0.4pp at α=0.05, β=0.1
- Target lift: 2pp → 5× over MDE → easily detected

**Compute (eval pipeline)**:
- Daily eval batch: ~$50/day (Databricks 4-node 1hr)
- Quarterly causal analysis: ~$2K (Databricks ML cluster 2 days)
- Real-time monitoring (Datadog dashboards, alert engine): ~$1K/month
- **Total**: ~$3K/month eval cost

**Timeline**:
- Stage 1 (offline replay): 2 weeks
- Stage 2 (shadow): 3 weeks
- Stage 3 (A/B): 8 weeks
- Stage 4 (rollout): 4 weeks
- **Total**: 17 weeks to full rollout (~4 months)

**Quarterly causal eval cost**: 1 ML team-week × 4 quarters = 4 weeks/year = $40K labor cost

**Business value**:
- 500 warehouse × 500 deliveries/day × avg $5 cost/delivery × 2pp on-time improvement
  → 2pp better SLA = ~$50/warehouse/day saved (avoid expedite + customer refund)
  → 500 × $50 × 365 = $9.1M/year value
- Net: $9M+ vs eval cost ~$50K + agent infra ~$200K = strong ROI

---

## Gao Xin 简历专属 reframe

1. **TikTok PayLater A/B framework** — 你做过 BNPL approval A/B, 同样 cluster random (by user cohort), counterfactual approval, guardrail (default rate). 直接套.

2. **Voice agent 7 markets** — 多 market 表现差异巨大, 你做过 per-market baseline + stratified rollout, 跟 500 warehouse heterogeneity 同思路.

3. **Indonesia refund tier A/B** — 你做过 monitored rollout with regulator-tracked metric, halt criteria 你定过, 跟这道题 99% target 思路同源.

4. **ConvFinQA eval** — multi-step task eval 经验, agent-decision eval framework 你跑过.

5. **Risk model drift monitoring** — 你做过 production model drift dashboard, PSI / KS-statistic 监控, 直接用在 agent 监控.

reframe: "我在字节做 PayLater 时 A/B framework 跟这道题 80% 重叠: cluster random + stratified + guardrail + DiD/DR. 增量是 (1) HITL — manager 在循环里, 我加 engagement signal; (2) 500 warehouse heterogeneity 比 user cohort 更复杂, per-warehouse baseline 而不是 fleet average; (3) outcome 延迟 (delivery 1-3 天) 比 default (30 天) 短, 反馈快."

---

## 5 个 Follow-ups

1. **"如果 RCT 8 weeks 太慢, business 要 4 weeks 就 rollout, 怎么办?"** — 答: 砍 sample size 到 60 warehouse (30+30), power 仍 detect 0.6pp, 但精度降. 跟 business 摆清楚 — 我们 might miss subtle 但 catch big issues. 同时 shadow + offline 已 paid 7 weeks, A/B 4 weeks 是最少 acceptable. Business 想再砍, 我会 push back + 给 risk memo.

2. **"manager 拒绝 agent 但 outcome 反而好, 怎么解释?"** — 答: manager 有 local knowledge agent 不知 (specific customer relationship, road closure not in feed, driver 出 sick). 这是 healthy disagreement. 把 override 当 product feedback, 把高质量 override 的 case 反向 train agent (RLHF-like). 同时把 manager local knowledge 改成 feature (e.g., let manager flag "VIP customer", agent 输入).

3. **"如何区分 agent contribution vs 旺季外部因素?"** — 答: synthetic control + DiD. 用 preserved 10% never-treated 作 control, treated vs synthetic control diff 是 net effect, 把 seasonal common shock 滤掉.

4. **"客户高管问'2 个月内你能给我 99% 数字吗', 你怎么答?"** — 答: 诚实. 4-stage 17 周 sequence, 想 2 个月只能砍到 offline + shadow + 小 A/B. 在 month 2 可以给 directional evidence (shadow data + small A/B 趋势), 但 board-defensible 99% sustained 需要至少 6 个月. Push back: "急可以, 但风险是 false positive — A/B 没 powered to detect cost regression. 我建议 hybrid: month 2 directional sign-off + month 4 full validation".

5. **"如果 agent 让 99% 仓但坏 bottom-quartile 怎么办?"** — 答: heterogeneous treatment effect 分析. 用 causal forest 或 X-learner 找 subgroup. 可能 agent 适合 large warehouse 不适合 small. 应对: (a) 不给 small warehouse 用 agent; (b) 训 small-specific agent; (c) 给 small manager 不同 UI (advise but never auto-action).

---

## ❌ 死路答法

1. **"用 accuracy / F1"** — 这是 sequential decision, 不是分类. 错.
2. **"per-decision random A/B"** — manager 困惑 + spillover. 必须 cluster random.
3. **"全部 500 一起 rollout 看 outcome"** — 没 control, 没 causal, 旺季影响混入.
4. **"只看 average on-time"** — variance hide, bottom-quartile 仍可能差.
5. **"agent 直接 act 不要 manager"** — 99% case 是 HITL, 直接 act 业务 + legal 不接受.
6. **"offline replay 通过就 rollout"** — distribution drift 风险.
7. **"acceptance rate = engagement = success"** — rubber-stamping 也能 100% acceptance, 需要 nuance.
8. **"causal? 太复杂, 业务不要"** — staff 答案必须有 causal, 不然 99% claim 不 defensible.
9. **"agent cost 不管, business 自己看"** — agent 可能 game 指标 (推 expedite), guardrail 必须有.
10. **"drift detection? 上线后 1 年再说"** — Day 1 dashboard 就要有, agent drift 可能 week 4 就出现.

---

## ✅ 加分项

1. **Per-warehouse baseline 而不是 fleet 99% target** — 立刻 signal 你懂 heterogeneous treatment
2. **4-stage gate (offline + shadow + A/B + rollout)** — 完整 eval lifecycle, 不跳步
3. **Cluster random by warehouse + stratification by baseline-quartile/region/volume** — 真懂 A/B 设计
4. **Doubly-robust + DiD 并行** — rigor + business-friendly
5. **Engagement signals (acceptance / override reason taxonomy)** — HITL 设计深度
6. **Counter metrics (bottom-quartile, worst-day)** — 防 average hide
7. **Preserved 10% never-treated 做 long-term control** — 真懂 causal hygiene
8. **Halt criteria 明确 + 多级 alert routing** — production sense
9. **Heterogeneous treatment effect (causal forest 找 subgroup)** — analytics 深度
10. **Numbers 给得出来** (40 warehouse × 8 weeks 够 0.4pp MDE, $9M business value)

---

## 一句话总结

99% 目标不是 ML problem, 是 **eval framework problem** — per-warehouse baseline + 4-stage gate (offline replay → shadow → cluster random A/B → cohort rollout) + counterfactual estimation (DR + DiD) + engagement leading indicator + drift monitoring + counter metric, 一整套 causal-rigorous + HITL-aware 评估系统.

---

## Cheat Sheet

```
Metric Hierarchy:
  North star (1):     per-warehouse on-time rate, weighted by volume
  Leading (3-5):      acceptance, recommendation quality, time-to-decide, coverage, override reason
  Guardrail (5-7):    cost, driver hr, complaint, NPS, damage, attrition, hub variance
  Counter (2):        bottom-quartile, worst-day

Per-warehouse baseline:
  Strata: baseline_quartile × region × volume_decile = ~60 stratum
  Target: baseline + Δ (not uniform 99%)
  Leaderboard: internal only, not manager-facing

4-stage Eval:
  Stage 1 (2w):  offline replay, doubly-robust counterfactual, concordance ≥ 70%, agent_wins > losses + 5pp
  Stage 2 (3w):  shadow, agent live but hidden, validate prod pipeline
  Stage 3 (8w):  cluster A/B, 40 control + 40 treat, MDE 0.4pp, DiD analysis
  Stage 4 (4w):  cohort rollout 100 → 250 → 500, halt criteria active

Counterfactual:
  RCT:           gold standard (Stage 3)
  Doubly-Robust: outcome model + propensity weight, consistent if either correct
  Synthetic ctrl:treated vs weighted-control combo, post-launch
  DiD:           business-friendly, parallel trends assumed

Engagement Signals:
  Acceptance rate (60-80% healthy)
  Override reason taxonomy (manager picks dropdown)
  Time-to-decide (proxy for cognitive load)
  Manager segmentation: heavy / selective / rejector / rubber-stamper

Drift Detection:
  Feature drift: PSI per-warehouse, > 0.2 alert
  Outcome drift: rolling 7d / 30d vs baseline
  Concept drift: shadow model recent 30d vs original agent

Alert Routing:
  P0 (page on-call): per-warehouse -2pp, customer complaint +20%, cost +5%
  P1 (page leader):  fleet outcome -1pp 30d
  P2 (Slack ML):     acceptance -10pp, feature PSI > 0.2

Preserved Controls:
  10% warehouse (50) never get agent → quarterly causal re-eval

Numbers:
  9.1M decisions/year, 200M deliveries
  Stage 3: 40+40 warehouse × 8 weeks → 1.1M deliveries treat
  MDE: 0.4pp; target lift 2pp easy detect
  Total timeline: 17 weeks (4 months) to full rollout
  Eval cost: ~$3K/month
  Business value: ~$9M/year on $200K infra + $50K eval
```
