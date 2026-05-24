## Recruiter #2 · Handle Ambiguity — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/handle-ambiguity.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`handle-ambiguity.html`](questions/handle-ambiguity.html)

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

> **Ambiguity 不是 "需要更多信息", 是「先 classify 5 种 type, 再选对应 framework, 用 reversibility 决定 speed」**. D·D·D·V (Diagnose / Decompose / Decide / Validate). FDE 90% 时间在 ambiguity 里, Junior 把所有 ambiguity 当 "需要更多信息", Senior 区分 one-way 慢 + two-way 快.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| D·D·D·V | Diagnose / Decompose / Decide / Validate | 黄金 framework |
| Goal ambiguity | 客户不知道想要什么 | discovery 帮拆 |
| Technical ambiguity | 多个 viable 架构 | trade-off matrix |
| Data ambiguity | 稀疏 / 矛盾 / 噪声 | hypothesis-driven |
| Organizational ambiguity | 多 stakeholder 优先级冲突 | stakeholder map + escalate |
| Outcome ambiguity | 成功标准没定义 | KPI lock |
| One-way door | 错了不能撤 (Bezos Type 1) | slow + investigate |
| Two-way door | 错了易撤 (Bezos Type 2) | fast + measure |
| Blast radius | 影响范围 (单客户 vs 多市场) | reversibility 维度 |
| Time to detect | 错了多久看到 | reversibility 维度 |
| Recovery cost | $100k vs < 1 wk eng | reversibility 维度 |
| KPI lock | 跟 stakeholder 签字 metric | outcome ambiguity 应对 |
| Reference point | 5-10% / 1% / 0.01% error 行业 anchor | outcome ambiguity 用 |
| Stakeholder map | 5 col table (诉求/红线/妥协/veto) | org ambiguity tool |
| Strawman proposal | 你出初稿让 stakeholder push back | 解 paralysis 工具 |
| Hypothesis order | 按 cost-to-verify 升序 | data ambiguity 不烧钱 |
| Decomposition hypothesis | "已知/未知/假设" 分解 | Decompose 步骤 |

### 🎯 5 个核心 framework

**Framework 1**: D·D·D·V (黄金 framework, 这道题核心 quote)
- When: 任何 ambiguous situation
- Algorithm:
  - D Diagnose: 哪种 ambiguity (goal / technical / data / organizational / outcome)
  - D Decompose: 已知 / 未知 / 假设 分清
  - D Decide: by reversibility (one-way slow, two-way fast)
  - V Validate: stakeholder + pilot data 不 silo
- Trade-off: framework vs flexibility
- Tools: 5 ambiguity types table, reversibility matrix, stakeholder map

**Framework 2**: Reversibility Decision Matrix (Bezos + FDE 改造)
- When: Decide 步骤
- Algorithm:
  - Axis: Reversibility / Blast radius / Time to detect / Recovery cost
  - One-way + high blast (Indonesia tier 3 refund) → 8-12 wk scoping
  - One-way + low blast (production single-customer change) → 2-4 wk scoping
  - Two-way + high blast (multi-market rollout) → 1-2 wk pilot then scale
  - Two-way + low blast (prompt tuning) → ship + measure same day
- Trade-off: 错估 reversibility = 速度错位 (one-way 上太快炸, two-way 上太慢错过)
- Tools: 4-axis evaluation, blast radius estimator

**Framework 3**: 5-Type Ambiguity Classification + Role
- When: 拿到 ambiguity 第一步
- Algorithm:
  - Goal ambiguity: 你帮 articulate, 客户 commit
  - Technical: 你主导决策, stakeholder ratify
  - Data: 你 investigate, stakeholder consume
  - Organizational: 你 map, exec resolve
  - Outcome: 你 propose, 客户 lock
- Trade-off: role 错配 (replace decision vs facilitate decision)
- Tools: ambiguity type → role table

**Framework 4**: 5-Question Discovery (Goal Ambiguity)
- When: 客户说 "I want AI" / "make it better"
- Algorithm:
  1. The ONE metric in 6 months? (强制 prioritize)
  2. Current baseline? (no baseline = no eval)
  3. Who's the loser if we succeed? (政治信号)
  4. What outcome makes us look stupid? (negative space)
  5. What does week-1 success look like? (quick win MVP)
- Trade-off: 5 questions take 30 min, 但 save weeks
- Tools: discovery question template, kickoff agenda

**Framework 5**: Hypothesis Order (Data Ambiguity)
- When: data 稀疏 / 矛盾时
- Algorithm:
  - List 5-10 hypotheses INCLUDING "boring" ones (data missing / source mis-aligned)
  - Order by cost-to-verify (ascending)
  - Run cheapest first
  - Stop when explanation found
  - ❌ Don't start with "let's retrain" (most expensive usually)
- Trade-off: 烧 GPU 烧时间 vs cheap investigation
- Tools: hypothesis list template, cost-to-verify ranking, "boring first" rule

### 🌳 关键决策树

```
Ambiguity 第一动作?
├── 先 classify 5 type (Diagnose)
│   ├── Goal → 5-question discovery
│   ├── Technical → trade-off matrix + reversibility
│   ├── Data → hypothesis-driven cheap first
│   ├── Organizational → stakeholder map + escalate
│   └── Outcome → KPI lock + industry reference points
├── 再 Decompose (已知 / 未知 / 假设)
├── 再 Decide by reversibility
└── 再 Validate (stakeholder + pilot)

Reversibility judgment?
├── 错了能撤? → two-way (fast + measure)
├── 多少 blast radius? (单客户 vs 多市场)
├── 多久 detect? (下周 vs 6 月后)
├── Recovery cost? ($100k vs 1wk eng)
└── 综合 → one-way+high blast 8-12w / one-way+low 2-4w / two-way+high 1-2w pilot / two-way+low ship same day

被问 push back 怎么应对?
├── Customer impatient → "Sketch + flag 3 assumptions, or confirm first?"
├── Vague KPI → "Reference 3 industry anchors"
├── Solo lock metric 客户 refuse → "I propose strawman, you push back"
└── Stakeholder conflict → "Give option A/B/C with trade-offs"
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: Goal Ambiguity (客户不知道想要什么)**
- 核心解法:
  ```
  5-question discovery kickoff:
    1. What's the ONE metric you want moved in 6 months?
    2. Current baseline?
    3. Who's the loser if we succeed (politically)?
    4. What outcome makes us look stupid?
    5. What does week-1 success look like?
  
  Don't accept "AI" / "make it better" / "automate":
    Push: "Of [refund / dispute / inquiry / KYC], which ONE?"
    Push: "$10 limit auto, $100 review, $1000 manual — does that shape match?"
  
  Indonesia refund tier outcome:
    Tier 1 auto (70% volume, $50 limit, 0% error)
    Tier 2 recommend + human (25%, $500 limit)
    Tier 3 full human (5%, $5000+)
  ```
- Top 3 gotchas: accept vague ask / 没量化 "automate" / 没 baseline
- Tools/tactics: 5-question discovery, tier 1/2/3 scoping language

**Problem 2: Technical Ambiguity (多 viable 架构)**
- 核心解法:
  ```
  Trade-off matrix (cost / latency / dev-time / vendor-lock / extensibility):
    Pinecone:  managed, fast, $$, vendor-lock
    Qdrant:    self-host, customizable, $, ops-burden
    pgvector:  in-existing-DB, cheapest, slow at 1M+
  
  Reversibility check:
    Vector DB choice: two-way (migrate later)
    Embedding model choice: more one-way (need re-embed 全量)
    System prompt: pure two-way (ship same day)
  
  Decide: 2 days time-boxed, ship, measure
  ```
- Top 3 gotchas: analysis paralysis (太多 alternative) / 没 reversibility 一刀切 slow / vendor lock 没 ack
- Tools/tactics: 2-day time-box, trade-off matrix template, ADR (Architecture Decision Record)

**Problem 3: Data Ambiguity (稀疏 / 矛盾 / 噪声)**
- 核心解法:
  ```
  Hypothesis order (cost ascending):
    H1: Data source mis-aligned (boring, $0) ← start here
    H2: Cohort definition different ($0)
    H3: Time window mismatch ($0)
    H4: Feature missing in prod ($100 eng)
    H5: Distribution shift (KS test, $50 compute)
    H6: Model regression ($500)
    H7: Retrain ($25k+, last resort)
  
  ConvFinQA negative result: tested critic agent on 358 cases, 4 useful flags.
    Honest reporting: "ablation showed assumption wrong"
  ```
- Top 3 gotchas: start with "retrain" (最贵) / 不写 boring hypotheses / 不 honest report negative
- Tools/tactics: hypothesis list template, cost-to-verify ranking, ablation methodology

**Problem 4: Organizational Ambiguity (Stakeholder 冲突)**
- 核心解法:
  ```
  Stakeholder map (5-col):
    | Stakeholder | 真实诉求 | 红线 | 妥协空间 | Veto power |
    | Ops | 自动化效率 | 不能让 customer 暴怒 | $限额可调 | low |
    | Legal | 监管合规 | OJK 罚款风险 | tier-3 manual 可接受 | HIGH |
    | Product | 速度 | 不能 6 月 | 30 天 MVP | mid |
  
  3-way working session agenda:
    1. Restate goals (both legitimate)
    2. Identify constraints (both 角度)
    3. Propose phased
    4. Define exit criteria
    5. Agree on cadence
    6. Action items
  ```
- Top 3 gotchas: 站任何一边 / 不 map veto power / 不 escalate when needed
- Tools/tactics: stakeholder map template, 3-way session facilitator hat

**Problem 5: Outcome / Metric Ambiguity**
- 核心解法:
  ```
  Industry reference points (你不能空提):
    Consumer search (Google): 5-10% error rate OK
    Credit decision: < 1% error rate
    Medical diagnosis: < 0.01% error rate
    Fraud detection: F1 > 0.85 production-grade
  
  KPI lock workflow:
    1. Propose strawman ("8% error OK, $500 limit, 30-day SLA")
    2. Stakeholder push back ("8% too high, want 3%")
    3. Iterate until signed
    4. Written: design doc with signed metric
  
  Don't accept "increase efficiency":
    Push: "By what %? On which workflow? Measured how?"
  ```
- Top 3 gotchas: accept vague "efficiency" / 没 reference points / 不 lock written
- Tools/tactics: reference points table, strawman proposal, written sign-off

### 🔥 Production gotchas (top 15)

1. "I just ship" → no thoughtfulness, HM 担心乱来
2. "I align with my manager" → 显示没 judgment
3. "I do a lot of research first" → analysis paralysis 字面
4. "It depends" 无 follow-through → wishy-washy
5. 故事没 metric → 显得不真实
6. 不区分 5 种 ambiguity → Junior signal
7. 不知 reversibility → senior signal 缺失
8. Solo silo decision → 不 validate stakeholder
9. 起 hypothesis 从 "retrain" 最贵开始 → 烧钱
10. 没 wrong call story (vulnerability) → 显得不诚实
11. 没 stakeholder map → org ambiguity 处理不专业
12. 替客户 decide goal → role 错位 (你应 facilitate)
13. 没 KPI lock written → 后续 goal-post shift
14. 没 industry reference point → "8% error" 凭空说
15. Two-way 决策上得太慢 / one-way 决策上得太快 → reversibility 误判

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Goal + outcome | Indonesia refund tier | scope from "automate refund" to tier 1/2/3 |
| Technical | Pakistan ASR cascade | 3 模型选型 trade-off + reversibility |
| Data | BNPL routing 70→92% | hypothesis order 找 data source mis-align |
| Organizational | BNPL 4-stakeholder | ops / legal / product / compliance 平衡 |
| Honest reporting | ConvFinQA 9-variant | negative result 公开论文 |
| Voice agent 7-market | per-market workshop | 6h workshop unify metrics |
| Internal Platform KPI | Internal Agent Platform | 14 teams 不同 metric lock |
| Wrong call vulnerability | multi-region launch | 文化误判, 重新 scope |
| Two-way decision speed | Voice agent prompt tune | ship same day, measure next-day |

### 🎤 面试现场 quotables (top 8)

1. "I have a framework for ambiguity called D·D·D·V — Diagnose, Decompose, Decide, Validate"
2. "Decomposition is hypothesis, not commandment — must validate with stakeholders + pilot data"
3. "Right answer faster, not wrong answer on time — scoping discipline"
4. "Two-way door — ship and measure same day. One-way door — invest 8-12 weeks scoping"
5. "Cheap hypothesis first — 'retrain' is most expensive usually, start with boring like data source mis-aligned"
6. "Indonesia refund tier 1/2/3 — scoped from 'full automation' to tier-based confirm. 70% throughput up, 0% error increase"
7. "I make ambiguity explicit and help stakeholders reach consensus — I don't replace their decision"
8. "ConvFinQA — 9-variant ablation, all worse than baseline. Honest negative result published. Eval > model"

### 🚨 红线 (top 10 anti-patterns)

1. "I just ship and iterate" (no framework)
2. "I align with my manager and ask them" (no judgment)
3. "I do a lot of research first" (analysis paralysis)
4. "It depends" no follow-through (wishy-washy)
5. No metrics in story (unreliable)
6. No wrong call acknowledged (no vulnerability)
7. No reversibility distinction (junior signal)
8. Solo silo decision
9. Start hypothesis from "retrain" (most expensive)
10. 替客户 decide goal (role 错位)
