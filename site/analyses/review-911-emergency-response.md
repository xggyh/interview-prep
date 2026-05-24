## Case #1 · 911 Emergency Response — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/911-emergency-response.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`911-emergency-response.html`](questions/911-emergency-response.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"How would you reduce 911 response time using AI?"**, 我按这 8 层回答, 不跳序. 这题是 life-safety domain, 第一动作不是画 ML 架构, 是 **frame the funnel**.

### 📐 911 Response Time — 8 层结构

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 (literal) |
|---|---|---|---|---|
| 1 | Clarify before solving | 1 min | "Before I propose anything, 5 questions: PSAP scope? CAD vendor? Current P50/P90? Which 4 funnel segments? Existing ML?" — 拒绝立刻画图 | "Life-safety means I want to make sure I'm not optimizing the wrong segment. Five quick clarifying questions..." |
| 2 | Time-breakdown anchor | 2 min | 把 total response time 拆成 4 段: **call-taking (45s) → dispatch decision (60s) → turnout (90s) → travel (4-7 min)**. 强调 travel 占 70% 但 dispatch decision 是 ML 最高 leverage | "911 response time is not one number — it's a 4-stage funnel. Let me draw the timestamps..." |
| 3 | 12 data points to instrument | 3 min | 列 12 个 timestamp event: ring_received, call_picked_up, address_confirmed, priority_assigned, unit_recommended, unit_dispatched, ack_received, turnout_complete, arrival_scene, patient_contact, transport_start, hospital_arrival. **这是 Day-1 dashboard, 不是 ML** | "Before I touch a model, I need 12 timestamps. Day 1 of this engagement is dashboards, not models..." |
| 4 | Root cause hypothesis (sliced) | 3 min | 按 segment slice: urban vs rural, time-of-day, priority class, dispatcher seniority, call type (cardiac vs fire vs non-emergency). **每段独立 root cause, 不要 average** | "Averages lie in 911. P50 might be fine but P95 cardiac at 2am could be killing people. Let me slice..." |
| 5 | ML intervention points (ranked) | 4 min | 3 个干预: **(a) Dispatch recommendation (highest leverage, dispatcher-in-loop)** → (b) Pre-positioning (demand prediction + static opt) → (c) ETA estimation (Graph-NN + traffic). 排序按 **lives-saved per $1M** | "I'd rank interventions by lives-saved-per-dollar, not by ML novelty. Top of stack: dispatch recommendation..." |
| 6 | Eval methodology — NO A/B | 4 min | **不能 A/B 因 ethics**. Use **stepped-wedge by district** + **counterfactual replay** + **shadow→opt-in→default rollout**. Ground truth lags 30-90 days → use leading indicators (override rate, time-to-dispatch) | "I can't randomize between AI-dispatch and human-dispatch — ethics review will reject. Three alternatives: stepped wedge, counterfactual replay, shadow mode..." |
| 7 | Failure modes + HITL | 2 min | 5 failure modes: address geocoding error, priority misclassification, ETA underestimate, recommendation bias, network partition. **HITL 三层**: AI suggests + dispatcher confirms + supervisor audit. **Override 是数据不是失败** | "Override rate is my favorite leading metric. If dispatchers override 40% I have a model problem. If 2% I might have a trust problem..." |
| 8 | Resume reframe | 1 min | "这跟我 TikTok PayLater Voice Agent 一样 — 7 markets, 6 languages. **2024 Q3 Pakistan ASR provider 40-min outage**, 我们 fallback to recorded TTS + queue, lost 12% transactions but zero compliance breach. **911 应用同思路: graceful degradation matters more than peak accuracy**" | "I lived this in voice agents. We had a Pakistan ASR provider 40-min outage..." |

### 🎯 为啥按这个序

**先 frame the funnel, 再 propose ML** — 因为 90% candidates 跳过 instrumentation 直接讲 LLM dispatch, 这是错的. **Travel time 是 70% bottleneck 但 ML 不能让车开更快**, ML 的 leverage 在 dispatch decision 和 pre-positioning. 先把这个 frame 立住, 后面 6 层都是支撑.

Eval methodology (Layer 6) 是这题的 **核心区分项** — 一般 candidate 说 "我做个 A/B", FDE 必须立刻 push back "no A/B in life-safety", 然后给出 stepped-wedge + counterfactual replay 替代方案.

### 🔥 哪一层最容易被追问 deeper

- **Layer 5 (ML intervention)**: 面试官会问 "为啥 dispatch recommendation 比 pre-positioning leverage 高?" → 答 "因为 dispatch 是 per-call decision (10万次/天), pre-positioning 是 shift-level decision (3次/天). Leverage = decision_count × delta_per_decision"
- **Layer 6 (eval methodology)**: 面试官会问 "counterfactual replay 怎么算 lift?" → 答 "Pair matching on call type + time + district, compare actual outcome vs replayed AI recommendation. Use propensity score for confounders. Limitation: can't replay traffic dynamics, so we add synthetic traffic noise"

### ⏱ 时间压缩版 (30 min round)

- 5 min: clarify + funnel breakdown (Layer 1-2 合并)
- 10 min: 12 data points + root cause slicing (Layer 3-4)
- 10 min: ML intervention + eval methodology (Layer 5-6, 重点)
- 3 min: HITL + failure modes (Layer 7)
- 2 min: resume hook (Layer 8)

### 🆘 卡壳兜底 (针对这题)

- 卡 ML 部分 → pivot to **"我先讲 instrumentation, ML 是 Phase 2"** — 这是 FDE Diagnose-First 框架
- 卡 eval → pivot to **"我做过的 ConvFinQA 9-variant ablation"**, 借 negative result 故事讲 eval 严谨性
- 卡 production → pivot to **"Pakistan ASR 40-min outage"** voice agent 故事, 讲 graceful degradation

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

> **911 不是「炫 ML 模型」, 是「把 funnel 每段 instrument + ML 推荐人决策 + shadow→opt-in→default 渐进 + ground truth lag 用 counterfactual + leading indicators 补位」**. FDE 拿到题目第一动作: 问 5 个 clarifying, 拒绝立刻画图.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| PSAP | Public Safety Answering Point, 接警中心 | 描述 911 入口节点 |
| CAD | Computer-Aided Dispatch, 接警调度中枢 | 集成对象 + 数据源 |
| Call-taker | 接电话录入 incident | 区分采集者 vs dispatcher |
| Dispatcher | 看 CAD 屏决定派谁 / 怎么走 | 决策环用户, override 的人 |
| ALI | Automatic Location Identification (E911) | 地址自动定位 |
| ALS | Advanced Life Support, 高级救护 | 高优先级 cardiac 派车 |
| NFPA 1710 | 火灾响应 P90 6.5 min 行业标准 | 当 baseline 引用 |
| Turnout | 接到通知 → 车启动的时间 | 4 优化点之一 (C) |
| Stepped wedge | 分区分阶段上线, 内部对照 | 替代 A/B 因 ethics |
| Counterfactual replay | 用历史 incident 让 AI 重新决策对比 | ground truth lag 时用 |
| Dead reckoning | 上次位置 + 朝向 × 时间, GPS stale 兜底 | GPS 数据 5-15% stale 时 |
| Override rate | dispatcher 推翻 AI 推荐的比例 | North Star: 20-30% 健康 |
| Stratified eval | 按 category (cardiac/fire/...) 分桶看指标 | 防止 aggregate 掩盖退步 |
| OPTICOM/RKE | 城市信号灯优先放行协议 | travel 优化, 需 city DOT |
| 26-D-1 | EMS 调度代码 (cardiac arrest) | 描述 dispatch code 时使用 |

### 🎯 5 个核心 framework

**Framework 1**: Funnel decomposition (12 时间戳)
- When: 任何 multi-stage 响应类问题
- Algorithm: call_received→connected→pickup→location→classified→cad_submit→dispatcher→unit_select→notified→ack→enroute→arrived
- Trade-off: 12 时间戳工程量大, 但没量化就没诊断
- Tools: OpenTelemetry trace, P50/P90/P99 Postgres percentile_cont, Grafana / Datadog dashboard

**Framework 2**: ML + LLM 分工
- When: 既有数值 (ETA) 又有非结构化 (call audio) 时
- Algorithm: GBDT 做 ETA + demand预测 (数值, MAE<60s) / LLM 做 ASR + symptom抽取 + 多语 + dispatch code 建议 (非结构化) / 优化器 (CBC / OR-Tools) 做 pre-position (NP-hard)
- Trade-off: LLM 慢且不擅数值, GBDT 不学非结构化
- Tools: Gemini 3 Flash $0.50/$3 (LLM), XGBoost / LightGBM (GBDT), Google OR-Tools / SciPy linprog

**Framework 3**: HITL 三层 + Override 数据化
- When: safety-critical 系统
- Algorithm: Layer 1 AI assist (1 键 confirm) / Layer 2 AI blind (junior train mode) / Layer 3 kill switch (全市退手动) / log every override + 一周后 outcome 对比
- Trade-off: junior 全 accept (over-rely) vs senior 全 ignore (信任不足)
- Tools: 强制 train mode 1 个月, override rate dashboard, "AI Assist: ON Layer X" UI 角标

**Framework 4**: 5-stage rollout (shadow→opt-in→default→kill)
- When: 任何 ML 系统部署 to safety-critical
- Algorithm: Phase 0 discovery 1w / Phase 1 instrument 2-4w / Phase 2 shadow 4-12w / Phase 3 opt-in 5 top dispatcher / Phase 4 default-on + kill switch
- Trade-off: 太慢, 但 911 一条命就是一条命, 不快
- Tools: feature flag (LaunchDarkly), shadow log table, weekly retro, 2w outcome regression auto-pause

**Framework 5**: Eval ladder (leading / mid / lagging)
- When: ground truth (生存率) 延迟 weeks-months
- Algorithm: Leading (response time, override rate, uptime 实时) → Mid (assessment scores 1-7d) → Lagging (survival, damage months) + stepped wedge + counterfactual replay
- Trade-off: counterfactual 是估计不是真相; A/B 不伦理
- Tools: stepped wedge by zone, synthetic control, DiD vs 邻市, replay simulator

### 🌳 关键决策树

```
Q: 60 min 内怎么 scope?
├─ Mayor's KPI? → P99 / category-specific / average → 锁 KPI
├─ Integration? → realtime stream / 5-min sampled / batch overnight → 锁架构
└─ Sub-problem? → routing / dispatch / pre-position → 选一个
   └─ Pick: 通常 funnel diagnose + dispatch recommend (最大 ROI)

Q: 决策时 confidence 多少 trigger 什么?
├─ conf > 0.85 + P1 → auto-confirm in 3s (但仍可 1 键 override)
├─ conf 0.7-0.85 → recommend, dispatcher 必须 confirm
├─ conf < 0.7 → show raw list, no recommend
└─ Override > 50% / 1 day → auto-pause + page FDE
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: Funnel 拆解 + Instrumentation**
- 核心解法:
  ```python
  # 12 时间戳 → SQL percentile_cont → stacked bar per category
  # outlier 自动归因: classify_slow / dispatch_slow / travel_slow
  # 第一周交付: PSAP dashboard "Worst bottleneck × volume = save 133h"
  ```
- Top 3 gotchas: 假设 timestamp 都有 (实际缺 30%) / 不分 category 看 aggregate / 没把 ROI 估出来
- Tools: OpenTelemetry, Datadog APM, Grafana, percentile_cont SQL, Mimir 长期存储

**Problem 2: Real-Time Dispatch Agent (ETA + Recommendation)**
- 核心解法:
  ```python
  rank = -eta - conf_penalty + skill_match + equipment - workload - depot_imbalance + redundancy
  return top_3 with reasoning  # dispatcher 一键 confirm
  # LLM (Gemini Flash) 解析 ASR → dispatch code 建议; GBDT MAE < 60s
  ```
- Top 3 gotchas: 只看 ETA 忽略 skill/equipment / 不给 reasoning (黑盒 dispatcher 不信) / LLM 跑数值
- Tools: Gemini 3 Flash $9300/yr/city, LightGBM, GraphQL UI, streaming ASR

**Problem 3: Failure Modes + HITL**
- 核心解法:
  ```
  GPS stale > 60s → dead reckoning
  Traffic > 5min lag → shortest path no-traffic
  conf < 0.4 → show raw list
  CAD down → manual mode + alarm
  Override > 50% → auto-pause + page FDE
  ```
- Top 3 gotchas: junior 全 accept (不动脑) / 没 kill switch / override 只算数不分析为什么
- Tools: 心跳 metric, OOD embedding distance, feature flag kill switch, weekly override retro

**Problem 4: Resource Pre-Positioning**
- 核心解法:
  ```python
  # demand: GBDT Poisson per 8x8km cell × 30min, MAPE < 25%
  # optim: CBC IntVar x[u,c], constraint 每车一位置, min Σ demand × travel
  # trigger: demand drift > 1.3 OR event dispersal in 15min OR coverage gap > 0.8
  ```
- Top 3 gotchas: 司机 silent sabotage (假装就位) / 没参与设计 / 没看到改进数据
- Tools: Google OR-Tools CBC, scipy.optimize, Poisson regression, event_calendar API

**Problem 5: Eval Methodology (ground truth lag)**
- 核心解法:
  ```
  Layer 1 leading (实时): response time, override, uptime, latency
  Layer 2 mid (1-7d): assessment scores, utilization
  Layer 3 lagging (weeks): survival, damage, cost
  Method: stepped wedge by zone + counterfactual replay (directional)
  Stratified: cardiac / fire / trauma / violence / mental_health 分桶看
  ```
- Top 3 gotchas: 直接 A/B 半个城市 (伦理) / 只看 aggregate 掩盖某 category 退步 / counterfactual 当 ground truth
- Tools: synthetic control, DiD vs 邻市, replay simulator, OpenTelemetry, Looker / Tableau

### 🔥 Production gotchas (top 15)

1. GPS 5-15% stale / drift → dead reckoning
2. Traffic feed > 5min lag → fallback no-traffic shortest path
3. CAD vendor (Motorola/Tyler/Hexagon/RapidDeploy) 拒绝集成 → side-car pattern
4. PSAP 工会触饭碗 → 早期 sponsor + 数据透明
5. Junior dispatcher rubber stamp → 1 个月 train mode
6. Senior dispatcher 全 override → 信任失败信号, retrain on their choices
7. Mass casualty (50 calls/秒) → 自动 cluster 合并防重复派警
8. Cluster mis-merge → 不同事件被合并 → 漏派, P1 必须 cluster + 单独 verify
9. Ambulance silent sabotage (假装就位) → GPS 校验 + 参与设计
10. Override rate noise → 30% 健康, < 10% 警惕, > 60% AI 模型差
11. A/B 切半个城市 → 伦理灾难, stepped wedge / DiD 替代
12. Counterfactual replay 当 ground truth → 只是 directional
13. 只看 aggregate → 某 strata (mental health) 退步被掩盖
14. Address 识别失败 ("我们这栋楼") → cross-ref 来电号码
15. HIPAA + CJIS 合规 → 911 涉及 PHI + 刑事数据, 加密 / 审计 / 数据驻留

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Funnel instrument | Voice agent 7 markets | ASR/LLM/TTS/tool-call latency day-1 instrument, dashboard 不吵架 |
| Multi-source data | Voice agent | customer / call history / repayment / blacklist 4 源 |
| Real-time decision | Voice agent | streaming p99 < 800ms |
| Safety-critical fallback | Voice agent | trust-critical, 转人工 fallback |
| Stepped wedge rollout | Voice agent | RL alignment 跨市分阶段 |
| LLM + ML 分工 | BNPL chatbot | agentic + RAG intent routing, sub-agent |
| Override / HITL | Indonesia refund tier 1/2/3 | tier 1 auto, tier 2 dual confirm, tier 3 manual |
| Override rate North Star | Voice agent | week-1 数据 |
| Counterfactual replay | ConvFinQA ablation | multi-hop reasoning ablation methodology |

### 🎤 面试现场 quotables (top 8)

1. "Let me ask 5 clarifying questions before I draw anything"
2. "I'd narrow this to dispatcher decision support — that's the highest leverage with lowest political risk"
3. "Before being asked, I want to flag 5 failure modes I'd plan for from day 1"
4. "This mirrors my voice agent at TikTok — multi-source, real-time, safety-critical, hard to A/B"
5. "I'd phase this shadow → opt-in → default-on, with override rate as the North Star"
6. "Override is not failure — it's training data. After 7 days of outcome we know if human or AI was right"
7. "A/B test on half the city is ethically off the table. Stepped wedge by zone + counterfactual replay"
8. "The first week deliverable is not a model — it's a funnel dashboard so we stop arguing about feelings"

### 🚨 红线 (top 10 anti-patterns)

1. 上来画 architecture / 算 QPS — 没 clarify = 失分
2. 当 system design 做 (DB shard / QPS) — 不是这题考的
3. 把人 cut out of decision loop — safety-critical 红旗
4. 承诺 6 个月一次性 GA — 没 phasing = 没部署过
5. 假设 GPS / traffic 完美 — 真实 5-15% stale
6. 忽略 dispatcher override — 模型再准, 不信任也白搭
7. A/B 切半个城市 — 伦理灾难
8. 承诺 "30% 改进" 没 buffer — 现实 5-15% 已 huge
9. 忽略 PSAP 工会和政治 — 接警员是工会代表的工种
10. 遗忘 HIPAA / CJIS 合规 — 涉 PHI + 刑事数据

### 📊 数字 anchors (面试必记)

| Metric | Value | Source / Rationale |
|---|---|---|
| NFPA 1710 fire response | 6.5 min P90 (90s pickup + 60s turnout + 240s travel) | 行业标准 |
| Cardiac arrest golden | 4 min, < 10% survival > 10 min | 医学共识 |
| Total response P50 / P90 / P99 (target) | 5:21 / 6:42 / 14:32 | dashboard 关键 3 数字 |
| ETA MAE target | < 60s P90 | GBDT 模型 KPI |
| Demand 预测 MAPE | < 25% on cell-30min granularity | Poisson regression |
| Confidence threshold | > 0.85 + P1 → auto-confirm in 3s | rank decision |
| Override rate healthy | 20-30% | < 10% over-rely warning, > 60% AI bad |
| LLM cost per city | $9300/year (30K calls/day × $0.85 / 1K) | Gemini 3 Flash $0.50/$3 |
| Shadow mode duration | 4-12 weeks | phase 2 |
| Phase 0/1/2/3 | 1w discovery / 2-4w instrument / 4-12w shadow / 5 dispatcher opt-in 3-6m | rollout schema |
| Outcome regression auto-pause | 2-week window | kill switch trigger |
| Mass casualty cluster | 50 calls/sec same location/similar desc | auto-merge logic |
| GPS stale threshold | > 60s | dead reckoning trigger |
| Traffic feed stale | > 5min | no-traffic fallback trigger |
| LLM model | Gemini 3 Flash $0.50/$3 | per 911 call ASR + symptom + code suggest |
| Pre-position model | GBDT 2yr training, MAPE < 25% | Poisson per 8km² cell |
| Optimization horizon | 30min next-period demand | facility location problem |

### 🎯 面试时机分配 (60-min budget)

| 阶段 | 时长 | 必做 |
|---|---|---|
| 0-10 min | Clarify + scope | 5 questions, narrow to 1 sub-problem |
| 10-25 min | Architecture | 3 components: ingest / decision / integration |
| 25-40 min | Deep dive 1 | 通常 decision engine + 实时 traffic |
| 40-50 min | Failure + measurement | 5 failure modes, KPI, dispatcher trust |
| 50-60 min | Phasing | 90-day MVP, phase 2/3

### ⚠️ 必避坑 (interview-specific)

| 坑 | 解法 | Quote |
|---|---|---|
| 一上来画 architecture | 先 5 clarify | "Let me ask 5 things before designing" |
| 当 system design 做 | 别算 QPS | "This isn't about QPS, it's about decomposition + tractable MVP" |
| 把 dispatcher cut out | HITL 3-layer | "Recommendation, not decision — dispatcher always has final call" |
| 承诺 6 个月 GA | phasing | "Shadow 4-12w → opt-in 5 dispatcher → default-on with kill switch" |
| 假设 GPS 完美 | dead reckoning | "Real-world 5-15% stale. Dead reckoning fallback" |
| A/B 切半个城市 | stepped wedge | "Ethically off the table. Stepped wedge by zone + counterfactual replay" |
| 承诺 30% 改进 | 5-15% 已 huge | "Realistic 5-15%, anything more 需要 buffer" |
| 忽略 PSAP 工会 | 早期 sponsor | "Union dispatcher is a real political constraint" |
| 遗忘 HIPAA / CJIS | 加密 + 审计 | "PHI + criminal data, need full compliance stack" |
| 单一 lagging outcome | leading + lagging | "Response time (leading) → assessment (mid) → survival (lagging months)" |

### 💡 ML + LLM 分工 cheat (背诵)

| Component | Tool | KPI |
|---|---|---|
| ASR streaming | Gemini 3 Flash $0.50/$3 | < 800ms p99 |
| Symptom抽取 + dispatch code | Gemini Flash w/ structured output | accuracy > 90% on 26-D-1 type codes |
| ETA estimator | GBDT (LightGBM) | MAE < 60s P90 |
| Demand 预测 | GBDT Poisson regression | MAPE < 25% per cell-30min |
| Pre-position optimization | Google OR-Tools CBC IntVar | facility location seconds-级 solve |
| Confidence calibration | self-consistency + logprob + probe | ECE < 0.05 |
| Override logging | structured table (incident, ai_unit, ai_eta, human_unit, reason, ts) | weekly outcome compare |
| Failure detector | TS heartbeat, OOD embedding distance | per-failure-mode runbook |

### 💡 5 Clarifying Questions cheat (背诵 verbatim)

| Q | 你问什么 | 为啥重要 |
|---|---|---|
| 1 | "Who's the buyer — mayor's office, police, fire? Single KPI?" | 不同 stakeholder metric 完全不同 |
| 2 | "Real-time GPS, or 5-min sampled? On-prem or cloud OK?" | data freshness + integration mode 决定 architecture |
| 3 | "Current baseline response time? Target — 10% or 50%?" | no baseline = no eval |
| 4 | "Dispatch software, predictive routing, or pre-positioning?" | 60min 做不完全部, force scope |
| 5 | "Cost of wrong prediction — fallback?" | safety-critical risk appetite 决定 model 类型 |
