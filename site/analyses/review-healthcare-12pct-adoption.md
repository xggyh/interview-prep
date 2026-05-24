## Case #3 · Healthcare Adoption — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/healthcare-12pct-adoption.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`healthcare-12pct-adoption.html`](questions/healthcare-12pct-adoption.html)

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

> **12% adoption 是 aggregate 症状, funnel 才是诊断**. 永远先拉 funnel telemetry, 4-5 hypothesis 对应每段 drop, on-site shadow 5 active + 10 non-user 验证, jointly own action items, 区分 product fit vs deployment fit. 80% 真实 case 是 A+B+D 混合, 10% C, 10% E.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Funnel | Awareness→Consider→Provision→Activate→First Value→Recurring→Habitual 7 阶 | 永远先拉 |
| TTV | Time-to-Value, activation 到 first_value | within 1 session 是关键, 否则 80% 不回来 |
| Stickiness | DAU/MAU, > 0.5 = 习惯化 | 其他 metric 可骗这个骗不了 |
| Cohort retention | 按 onboarding 周分组看衰减 | retention 在某 cohort 突崩 → 那周什么事 |
| CMIO | Chief Medical Information Officer, 决策购买 | top sponsor 离职 = 危险信号 |
| CMO | Chief Medical Officer, 决策 outcome | 临床信誉 |
| CFO | 决策续约 | 必须 ROI 语言 |
| Champion 3-tier | Executive / Functional / Floor (top 5% user) | 任一缺位 = stall |
| EHR | Electronic Health Record, Epic/Cerner/Athena/AllScripts | 深集成是 must, 否则死刑 |
| SMART on FHIR | EHR app 集成标准 | Level 2 集成方式 |
| ECE | Expected Calibration Error, < 0.05 是部署门槛 | LLM confidence 是否可信 |
| Diffusion of innovation | 5 类用户 (innovator/early adopter/early majority/late majority/laggard) | champion 找 early adopter |
| Hypothesis A-E | A 配 B UX C workflow D change mgmt E product fit | adoption 失败 5 分类 |
| Stratify | 多轴 (role × site × demographic) 拆数据 | aggregate 必掩盖 |
| HCAHPS | 患者满意度评分 | lagging outcome metric |
| Rage clicks | 同按钮 3 次 < 1s, friction 信号 | UI / 响应慢 |

### 🎯 5 个核心 framework

**Framework 1**: 7-stage Adoption Funnel
- When: 任何 adoption 诊断
- Algorithm: Awareness→Consideration→Provisioning→Activation→First Value→Recurring→Habitual, 算每段 conversion rate vs benchmark (Activation→First Value 50-70% healthy)
- Trade-off: 太多 stage 难以 instrument, 太少看不到 root cause
- Tools: Amplitude / Mixpanel funnel, dbt for transformation, Looker dashboard

**Framework 2**: 5-Hypothesis 分类 (A/B/C/D/E)
- When: funnel 看到大 drop 后
- Algorithm:
  - A. Provisioning failure (IT/SSO) → 2-4w bulk action
  - B. UX/training gap → 4-8w in-app onboarding + 现场培训
  - C. Workflow fit (EHR) → 3-6mo 深度集成
  - D. Change management (champion loss) → 6-12w sponsor 重启
  - E. Product fit → 6+mo graceful retreat / 重新 scope
- Trade-off: E 是最难承认的, 但死磕 E = 项目自杀
- Tools: Pearson likelihood × impact 矩阵, weekly hypothesis re-rank

**Framework 3**: 5-Friction 分类
- When: deep dive 单层 drop 时
- Algorithm: Access (SSO IT) / Discovery (找不到入口) / Cognitive (UI 复杂) / Workflow (打断主流程, 需 EHR 深集成) / Trust (AI confidence 不明)
- Trade-off: Access/Discovery low cost, Workflow/Trust high cost
- Tools: FrictionAudit session log (time_to_first_click, rage_clicks, context_switches, abandonment_points)

**Framework 4**: Trust Building 3-Lever
- When: AI clinical deployment
- Algorithm:
  - Calibrated confidence (self-consistency + logprob + probe model → ECE < 0.05)
  - Explainability 4 层 (sources / CoT / what-if counterfactual / limitation 自报)
  - Peer endorsement (early adopter 30-min lunch session > vendor pitch 10x)
- Trade-off: 透明 failure (AI 主动认 "我不确定") 反而建立信任
- Tools: token-level logprob, RAG citations, 训 confidence probe model

**Framework 5**: 3-Tier Champion + 双层 Metric
- When: change management
- Algorithm: Executive (CMIO 月 30min) / Functional (Chief Resident 周 sync) / Floor (top 5% user 月 1on1) + 永远培养 next sponsor (CMIO 2-3yr, chief resident 1yr) + Leading (DAU/funnel daily) + Lagging (time saved/outcome/ROI monthly)
- Trade-off: 失任一 tier 都 stall, 必须冗余
- Tools: sponsor_succession_plan, "AI Champion" 社会认可, 时间节省 personal dashboard

### 🌳 关键决策树

```
Funnel drop 在哪?
├── Target → Provisioned (大 drop)? → Hyp A (IT/SSO), 2-4w fix
├── Provisioned → Activation? → Onboarding bottleneck
├── Activation → First Task (大 drop)? → Hyp B (UX/discovery), 4-8w fix
├── First Task → Recurring (大 drop)? → Hyp C (workflow fit, EHR), 3-6mo
└── 任何阶段 + champion 离职? → Hyp D (change mgmt), 6-12w
   └── 数据 + 反馈都差? → Hyp E (product fit) → 诚实 retreat

Trust building 阶段?
├── ECE > 0.05? → calibration 不够, 别上线
├── Explainability 缺哪层? → sources/CoT/what-if/limitation 补全
└── Peer endorsement 没 champion? → 找 top 10% seniority + open-to-tech
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: Adoption Funnel**
- 核心解法:
  ```python
  stages = [awareness, consideration, provisioning, activation, first_value, recurring, habitual]
  benchmarks: provision→activation 80-95%, activation→first_value 50-70%, first_value→recurring 40-60%
  ttv_p50, within_1_session_pct (< 1hr 关键)
  cohort_retention (wk1, wk4, wk12)
  stickiness = DAU/MAU > 0.5
  ```
- Top 3 gotchas: 看 aggregate / 单 metric (DAU 骗局) / 没 cohort 看 release 影响
- Tools: Amplitude funnel, dbt, Looker, Pearson 训练→adoption correlation

**Problem 2: Friction Analysis**
- 核心解法:
  ```
  5 类: Access / Discovery / Cognitive / Workflow / Trust
  EHR 集成 Level 1 (standalone) → 90s; Level 4 (embedded widget) → 12s
  FrictionAudit: rage_clicks / context_switches / abandonment_points
  ```
- Top 3 gotchas: 误判 cognitive 实际是 workflow / 没集成 EHR / 没 rage_clicks tracking
- Tools: FullStory / LogRocket session replay, SMART on FHIR, FHIR REST API

**Problem 3: Trust Building**
- 核心解法:
  ```python
  # calibration: self-consistency (5x) + logprob + probe model → ECE < 0.05
  display: confidence > 90% 绿 / 70-90% 黄 / < 70% 红
  explainability: sources (RAG) / CoT / counterfactual / limitation
  peer: 5 early adopter (chief resident, ICU director) 30min lunch demo
  transparent_failure: conf < 0.6 → "low confidence, consult specialist"
  ```
- Top 3 gotchas: uncalibrated confidence (88% acc 报 99%) / 同 model self-judge / 一直自信 1 错 trust 崩
- Tools: RAG sources, Chain-of-Thought log, confidence probe model

**Problem 4: Change Management**
- 核心解法:
  ```
  3-tier sponsor: Executive CMIO / Functional Chief Resident / Floor top user
  Succession plan: CMIO 2-3yr tenure, 永远培养 next
  Training 3-level: self-serve 10min / cohort 30min / 1-on-1 monthly
  Incentive 医院 ≠ 钱: 社会认可 / 时间节省 dashboard / 学术 credit / IT support 优先
  ```
- Top 3 gotchas: 失 1 tier 就 stall / 没 succession plan / 上钱激励 (医生收入高, 无效)
- Tools: monthly CMIO update slide, "AI Champion" newsletter, 时间节省 personal dashboard

**Problem 5: Measurement (Leading + Lagging + ROI)**
- 核心解法:
  ```python
  Leading daily: funnel, DAU, stickiness, session
  Lagging monthly: time saved, readmission, HCAHPS, FTE-hours saved
  ROI: active × hours_saved × work_days × loaded_rate - subscription - integration
  Equity stratify: by role, demographic, race - 防 AI bias 加剧
  pre/post + confounder control (acuity, season, staff, covid)
  ```
- Top 3 gotchas: 只讲 adoption % 给 CFO (听不懂) / 没 confounder 控制 / 不 stratify 看 equity
- Tools: ttest, scipy adjust_for_confounders, HCAHPS data, Equity dashboard

### 🔥 Production gotchas (top 15)

1. 预设 root cause (UI/model) → 砸错地方
2. 跳过 funnel 直接救火 → fix 对空气挥拳
3. 甩锅 customer → FDE joint own, 失分
4. 不上 customer site → 远程看 dashboard 误判
5. 不区分 product fit vs deployment fit → 当 H5 死磕 = 自杀
6. 承诺 "90 天回到 80%" → 没数据不能 commit
7. 当 training problem → training 是局部 fix, 不万能
8. 忽略 EHR 深集成 → healthcare 死刑
9. 看 7-day active 不看 DAU/MAU → 误判 stickiness
10. 没 CFO-language → 续约只讲 adoption % CFO 听不懂
11. 上 uncalibrated LLM clinical → 1 次错 trust 崩
12. 跳 stratify 看 aggregate → equity bias 加剧不平等
13. CMIO 离职没 succession → adoption 30% → 12% 滑铁卢
14. 钱激励医生 → 收入已高, 无效, 用时间节省
15. AI 一直自信 → 比"我不确定"更危险

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Funnel diagnosis | Voice agent 7 markets | Indonesia 15% adoption, 70% provisioning failure |
| Cross-market adoption | Voice agent 7 markets | 不同 cultural 不同 rollout 路径 |
| Champion network | Voice agent regional ops | 7 个 regional champion |
| Cultural difference | Voice agent | Indonesia top-down / Brazil grass-root / Mexico balance |
| Product fit vs deployment | Refund tier 1/2/3 scoping | tier 3 manual 是 product 不适合 auto |
| Stickiness | BNPL chatbot | DAU/MAU 量化 |
| Embedded floor training | Voice agent | weekly regional ops sync |
| Calibrated confidence | Voice agent | confidence routing 转人工 |
| Deep integration | BNPL 跨 internal system | EHR 类似挑战 |

### 🎤 面试现场 quotables (top 8)

1. "Before I propose anything, can we look at the funnel breakdown? Adoption is aggregate, funnel is actionable"
2. "Indonesia voice agent had same shape — 15% adoption, funnel showed 70% provisioning failure, not product"
3. "I'd shadow 5 active users + 10 non-users on-site in week 1 — qualitative + quantitative triangulation"
4. "Joint action items: 3 are on us, 2 on you — can floor managers commit to 15-min adoption huddles every shift for 4 weeks?"
5. "Healthcare AI without deep EHR integration is dead on arrival — the difference is 90s vs 12s per query"
6. "Calibrated confidence beats high accuracy uncalibrated — ECE < 0.05 is my deployment gate"
7. "Champion-led peer demo > vendor pitch 10x. Find 5 early adopters by seniority × open-to-tech"
8. "ROI for CFO: 280 active × 0.85 hr × 220 days × $80 = $4.19M annual value vs $600K cost = 597% ROI"

### 🚨 红线 (top 10 anti-patterns)

1. 预设 root cause (UI/model)
2. 跳 funnel 直接救火
3. 当 training problem (cop-out)
4. 不区分 product fit vs deployment fit
5. 不去 customer site
6. 承诺数字 (90 天 80%)
7. 甩锅 customer
8. 忽略 EHR 集成 in healthcare
9. 没 calibrated confidence 上 clinical
10. 没 ROI math 给 CFO

### 📊 数字 anchors (面试必记)

| Metric | Value | Source |
|---|---|---|
| Funnel benchmark | Awareness→Consider 60-80% / Consider→Provision 70-90% / Provision→Activation 80-95% / Activation→FirstValue 50-70% / FirstValue→Recurring 40-60% / Recurring→Habitual 30-50% | 健康 funnel |
| Total Awareness→Habitual | 5-15% | 健康范围 |
| TTV within session | < 1hr critical, otherwise 80% never return | 研究表明 |
| Stickiness DAU/MAU > 0.5 | 工具进入日常工作流标志 | 其他 metric 可骗 |
| ECE | < 0.05 | LLM clinical 部署门槛 |
| EHR integration latency | Level 1 standalone 90s / Level 4 embedded widget 12s | 75% time saving |
| Hypothesis A-E breakdown | A 40% / B 25% / C 10% / D 15% / E 10% | 真实 case 分布 |
| Hypothesis fix duration | A 2-4w / B 4-8w / C 3-6mo / D 6-12w / E 6+ mo | 应对 schedule |
| ROI math template | 280 active × 0.85 hr × 220 days × $80 = $4.19M / yr vs $600K cost = 597% | CFO language |
| Champion 3-tier engagement | CMIO monthly 30min / Chief Resident weekly / Top user monthly 1-on-1 | sponsor cadence |
| CMIO tenure | 2-3 years (must groom next) | succession plan |
| Chief Resident tenure | 1 year (rotate) | succession plan |
| 90-day target | 40% adoption | realistic vs 80% pipe dream |
| 6-month target | 70% adoption | sustained growth |
| On-site interview budget | 5 active + 10 non-user | qualitative triangulation |
| Survey reach | 200 responses, 5 questions, 2 min | scale qualitative |
| Per-tenant ACL | hard pre-search filter | 不能事后过滤 |
| ROI breakeven | < 2 months (typical AI healthcare) | CFO expectation |

### ⚠️ 必避坑 (interview-specific)

| 坑 | 解法 | Quote |
|---|---|---|
| 预设 root cause | funnel 先 | "Adoption is aggregate, funnel is actionable" |
| 跳过 funnel | 5-stage telemetry first | "Before fix, pull every stage conversion rate" |
| 甩锅 customer | joint own | "3 actions on us, 2 on you with timeline" |
| 不去 customer site | on-site 5 active + 10 non-user | "Remote dashboards miss workflow" |
| 不区分 product vs deployment | H5 ack | "I won't fake H1 if data shows H5 — graceful retreat preserves relationship" |
| 承诺 90 天 80% | realistic 40% | "40% in 90d, 70% in 6mo" |
| 当 training problem | training 是 H2 局部 fix | "Training alone is cop-out" |
| 忽略 EHR 深集成 | Level 4 widget | "Without deep EHR, 90s vs 12s — dead on arrival" |
| 没 calibrated confidence | ECE < 0.05 | "Calibrated > Accuracy" |
| 没 ROI math 给 CFO | $/hr × hr × days | "CFO cares FTE-hours-saved, not adoption %" |

### 💡 4-Layer Explainability cheat (背诵)

| Layer | Content | Tool |
|---|---|---|
| L1 Sources (RAG) | doc_id, snippet, similarity | retrieve metadata |
| L2 Chain of thought | "Patient presents X / Lab Y / Differential A 40% B 30% / Recommend Z" | reasoning trace |
| L3 What-if counterfactual | "If temp higher → shift A; if no history X → consider D" | sensitivity |
| L4 Limitation 自报 | "Trained adult data, pediatric lower; not validated Y demographic" | transparency |

### 💡 EHR Integration Level cheat (背诵)

| Level | Pattern | UX latency |
|---|---|---|
| 1 Standalone web | switch tab + paste + wait + copy + paste back | 90s, "no second use" |
| 2 SMART on FHIR app | EHR-launched iframe | 30-45s |
| 3 Deep SDK | widget in patient chart pane | 20s |
| 4 Embedded workflow | AI suggests next note line, native UX | 12s ⭐ |
