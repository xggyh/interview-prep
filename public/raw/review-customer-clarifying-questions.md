## Solution Design #1 · Customer Clarifying Q — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/customer-clarifying-questions.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`customer-clarifying-questions.html`](questions/customer-clarifying-questions.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"customer 上来给 vague brief 你问什么 / first meeting clarifying questions"**, 我按这 7 层回答, 不跳序. **核心心法: BSCFS taxonomy → scripted question banks → push-back tactics → STAR examples → vulnerability close. Vendor 上来 design, FDE 上来 ask**.

### 📐 Customer Clarifying Q — 7 层结构

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 (literal) |
|---|---|---|---|---|
| 1 | Posture (vendor vs FDE) | 15s | Vendor 听到 brief 就 design demo. FDE 第一反应是问 5-7 question. Skip clarifying = immediate fail. Why-binding 每 question | "First principle — vendor hears a brief and goes to demo. FDE hears a brief and asks 5 to 7 questions. Skipping clarifying is an immediate fail in this role. And every question I ask is bound to a 'why I'm asking'" |
| 2 | BSCFS taxonomy (5 类) | 30s | Business (KPI / 业务 driver) / Stakeholders (decider / blocker / sponsor) / Constraints (latency / compliance / cost / data) / Failure (acceptable error mode / red lines) / Success (measurable definition + 时间窗) | "Five categories — Business, Stakeholders, Constraints, Failure, Success. BSCFS. Business first because if I don't know the KPI no answer is right. Failure second-last because 'what's the worst that can happen' is the question vendors skip" |
| 3 | Scripted question banks (per-bucket) | 45s | **Business**: "if this works in 6 months what business metric moves? Whose budget?" **Stakeholders**: "who signs off? Who blocks? Who I never meet but matters?" **Constraints**: "P99 latency / regulator / cost ceiling / data residency / on-prem?" **Failure**: "what's the worst case if AI is wrong — financial / regulatory / brand?" **Success**: "what does 'done' look like at 30/60/90 days?" | "Concrete scripts — Business: 'if this works in six months what metric moved and whose budget did it justify?' Stakeholders: 'who signs off, who blocks, who I never meet but matters?' Constraints: latency, regulator, cost ceiling, data residency. Failure: 'what's the worst case if the AI is wrong?' Success: 30/60/90-day measurable" |
| 4 | Push-back tactics | 30s | 客户给 vague answer 三招: (1) "what would change if 80% / 90% / 95%?" (push 数字 specificity), (2) "tell me a recent example where this happened" (push concreteness), (3) "if I gave you a demo tomorrow what would make you say no?" (push failure mode) | "When the answer is vague I push three ways. One — 'what would change if accuracy were 80 vs 95?' to force a number. Two — 'walk me through a recent example' to force concreteness. Three — 'if I demo tomorrow what makes you say no' to surface real failure mode" |
| 5 | KPI-first + 1-page proposal | 20s | 永远 KPI 第一. 1-page proposal within 1 week — restate problem, KPI, 3 options with cost/risk, recommendation, success criteria, 30/60/90 plan. 客户 sign-off baseline | "KPI is always first. And I follow first meeting with a one-page proposal within a week — restated problem, KPI, three options with cost-risk, my recommendation, success criteria, and a 30/60/90 plan. Customer signs that off as the baseline" |
| 6 | STAR (clarifying win) | 25s | BNPL "make chatbot smarter": 我没接受 brief. Week 1 200 conversation interview + BSCFS 5 question 全跑. Output: "smarter" = intent routing 70→90% on top-5 intents. Sign-off 1-pager. Result: 70→92%, 客户给了 follow-on engagement | "Concrete — BNPL customer asked to 'make the chatbot smarter'. I refused to design until I'd run BSCFS. Five questions surfaced the real KPI: intent routing 70 to 90 percent on top-5 intents. One-page proposal, signed. Shipped 70 to 92" |
| 7 | Vulnerability + close | 20s | Acknowledge failure mode: 早期我 ConvFinQA 跳过 clarifying 直接做 — 结果 spec 错, 浪费 2 week. 学到 "clarifying time 不是 cost, 是 risk reduction". Close: 我能给你 demo 我的 BSCFS 实操 | "Failure I learned from — early in my career on ConvFinQA I skipped clarifying and dove into design. Spec was wrong, two weeks wasted. The lesson — clarifying time isn't cost, it's risk reduction. Happy to walk through my BSCFS sheet on a real brief if you want" |

### 🎯 为啥按这个序

**先 posture 再 taxonomy 再 scripts 再 push-back 再 STAR 再 vulnerability**: 面试官筛的是 "你会不会 demo-first". Posture 句直接化解, BSCFS taxonomy 证明你有结构, scripted questions 证明你 ready (不是 made-up on spot), push-back tactics 证明你能处理 vague customer (常见现实), STAR 闭环, vulnerability (ConvFinQA spec 错 2 week 浪费) 化解 "你只讲赢的故事". **Why-binding 每个 question 是 differentiator**.

### 🔥 哪一层最容易被追问 deeper

- **Layer 3 (Scripted questions)**: "客户不知道 KPI 你怎么办?" → 三步: (1) 提供 menu 选项 (containment rate / CSAT / handle time) 让客户挑, (2) 借鉴行业 benchmark (BNPL 25-40% containment), (3) propose 一个先 sign-off 跑 1 week 调
- **Layer 4 (Push-back)**: "客户 push 回来说 just build the demo? 你怎么 hold line?" → "Happy to demo — but my demo only matters if I demo against your KPI. Give me one number and I'll demo against that, otherwise we're both guessing"

### ⏱ 时间压缩版 (30 min round)

- 30s: "Vendor designs, FDE asks. BSCFS taxonomy — Business / Stakeholders / Constraints / Failure / Success. 5-7 questions first meeting. 1-page proposal within 1 week"
- 1 min: + scripted question per bucket + BNPL "smarter" example
- 2 min: + push-back tactics + ConvFinQA vulnerability + close offer

### 🆘 卡壳兜底 (针对这题)

1. **被问到 customer 不配合**: "Customer who won't answer is a signal — usually means they don't know the answer or the sponsor is missing. I'd escalate to ask 'who's the decider' and route the question there. Never just guess and proceed"
2. **被问到具体 sample question 我没准备**: "Honestly the exact question depends on the domain — for an enterprise SaaS I'd ask differently than for a consumer app. The framework is BSCFS, the wording is per-domain. If you give me the domain I'll show you the per-bucket script"
3. **被问到 "too many questions 客户烦"**: "Real risk — I cap at 5 to 7 in first meeting, prioritize by decision-blocking. The rest go into a follow-up email or the 1-pager proposal. And I lead each with 'why I'm asking' so it doesn't feel like an interrogation"

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

> **Skip clarifying = immediate fail for FDE**. 5-7 question first conversation, BSCFS order (Business / Stakeholders / Constraints / Failure / Success), 每个 question 绑定 "why I'm asking", push specificity, KPI first 永远, 1-page proposal within 1 week. **Vendor 上来 design, FDE 上来 ask**.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| BSCFS | Business / Stakeholders / Constraints / Failure / Success 5 类 | 永远这个 order |
| Clarifying question | design 前问的问题 | 第一动作 |
| Discovery | listening / observing / customer's user 接触 | extension of clarifying |
| KPI lock | vague success → specific measurable metric | 第一类必锁 |
| Stakeholder map | 5-col (诉求/红线/妥协/veto/incentive) | Stakeholder 类工具 |
| Failure tolerance | wrong-answer rate / downtime / cost 容忍 | Failure 类 |
| Strawman | 你出初稿让 stakeholder push back | metric lock 推动器 |
| Why this matters | 每个 question 绑定 reasoning | 不显得 interrogate |
| Push for specificity | "efficiency" → "tickets/hour" | 避免 vague accept |
| 5-7 limit | first conversation question 上限 | 不 interrogate 节制 |
| 1-page proposal 1 wk | 后续 commit | 快 vendor signal |
| Reference points | 5-10% / 1% / 0.01% error | failure tolerance anchor |
| Veto holder | IT / Legal / Compliance / Security | architecture 政治可行 |
| Champion vs Sponsor | 推动 vs 决策 | stakeholder 层 |
| Funder | 出钱 | 第三 hat |
| User vs Buyer | 用户 ≠ 买单 | 5 hat 区分 |
| Goal-post shifting | Tier 1 ship 后 ask Tier 2 ASAP | success criteria 锁防 |

### 🎯 5 个核心 framework

**Framework 1**: BSCFS Question Order (永远先 KPI)
- When: 任何 solution design 第一步
- Algorithm:
  1. Business / KPI (2-3 questions, 优化目标)
  2. Stakeholders / Politics (2, 谁批 / 谁 veto)
  3. Constraints (2-3, deployment / 合规 / 数据)
  4. Failure mode (2, 错的容忍)
  5. Success criteria (2, time window / milestone / demo)
- Trade-off: 顺序错 = 白做 (先问 constraints 设计 on-prem, KPI 是 low latency 全废)
- Tools: BSCFS mnemonic, 5-7 question limit, 1-2 per category

**Framework 2**: KPI Lock (永远第一类)
- When: 客户说 "efficiency" / "better" / "AI"
- Algorithm:
  - "The ONE metric in 6 months — what number?" (force prioritize)
  - "Current baseline?" (no baseline = no eval)
  - "Threshold: success / stretch / disappointment?" (3-level)
  - "Who's the loser if we succeed?" (政治信号)
  - "Counter-example — recent case where current failed?" (negative space)
- Trade-off: 客户讨厌过多 push back, 但 vague KPI = wrong design
- Tools: strawman propose, 3-option (volume / cost / quality), industry reference

**Framework 3**: Stakeholder Map (5 hats)
- When: 政治可行性 check
- Algorithm:
  - Champion (推动): 内部 push
  - Funder (出钱): budget
  - Decider (决策): 签字
  - User (用户): 真用
  - Buyer (买单): 续约
  - + Veto holders (IT / Legal / Compliance / Security): 一票否决
  - 5-col map: 真实诉求 / 红线 / 妥协空间 / Veto power / Incentive
- Trade-off: 5 hat 可能同一人, 大企业可能 5 人
- Tools: stakeholder spreadsheet, RACI matrix variant

**Framework 4**: Failure Tolerance Spectrum
- When: 客户说 "we need it to work well"
- Algorithm:
  - Industry reference points (你不能空提):
    - Consumer search (Google): 5-10% error OK
    - Credit decision: < 1% error
    - Medical diagnosis: < 0.01% error
    - Fraud F1: > 0.85
  - 4-tier cost of wrong answer: trivial (< $1) / moderate ($100) / severe ($10K) / catastrophic ($1M+)
  - Silent failure 担心? rollback / kill switch?
- Trade-off: 过度保守 = 设计 over-engineer, 不够保守 = 上线 explode
- Tools: failure tolerance table, reference point library

**Framework 5**: 5-7 Question Limit + "Why This Matters"
- When: 节制 vs interrogate
- Algorithm:
  - First conversation: 5-7 max
  - 1-2 per BSCFS category
  - Each question paired with "why I'm asking this"
  - Remaining questions in follow-up email / next call
  - 1-page proposal within 1 week (fast vendor signal)
- Trade-off: 太少 missing critical, 太多 interrogate
- Tools: question script with "why" reasoning, follow-up email template

### 🌳 关键决策树

```
拿到 customer 问题, 第一步?
├── 上来 design → IMMEDIATE FAIL (vendor 思维)
├── 问 20 questions → 客户被 interrogate
├── 问 random list → 显示不会 prioritize
└── BSCFS 5-7 with reasoning → ⭐ FDE 思维

每类 question 何时多问?
├── Business 多问 → 第一次见, 不熟 customer
├── Stakeholders 多问 → 已有 vendor / 政治复杂
├── Constraints 多问 → 监管行业 (financial / healthcare)
├── Failure 多问 → 高 stake (safety-critical)
└── Success 多问 → renewal / complex phasing

客户 vague KPI ("efficiency")?
├── 3-option push (volume / cost / quality)
├── Industry reference points
├── Strawman propose: "8% error OK, $500 limit, 30-day SLA"
└── Lock written sign-off

不知道客户 failure tolerance?
├── Industry spectrum: search 5% / credit 1% / medical 0.01%
├── Cost of wrong: trivial $1 / moderate $100 / severe $10K / catastrophic $1M
└── Counter-example: "recent case current process failed, what happened?"
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: Business / KPI Questions (永远第一)**
- 核心解法:
  ```
  5 essential questions:
    Q1: "The ONE metric in 6 months — what number?"
        Why: force prioritize, single optimization target
    Q2: "Current baseline?"
        Why: no baseline = no eval
    Q3: "Threshold: success (X) / stretch (Y) / disappointment (Z)?"
        Why: 3-level helps phasing
    Q4: "Who's the loser if we succeed?"
        Why: 政治信号, downstream impact
    Q5: "Counter-example — recent case where current process failed?"
        Why: negative space, real pain
  
  Push if vague:
    "efficiency" → "tickets/hour or cost-per-ticket?"
    "better" → "what specific behavior to change?"
    "AI" → "AI for what specific workflow?"
  ```
- Top 3 gotchas: accept "efficiency" / 没 baseline / 没 3-level threshold
- Tools/tactics: 3-option push template, industry KPI reference, strawman propose

**Problem 2: Stakeholder Questions (谁批 / 谁 veto)**
- 核心解法:
  ```
  Q1: "Executive sponsor + their incentive?"
      Who pushes top-down, what gets them promoted
  Q2: "Veto holders — IT / Legal / Compliance / Security?"
      One-vote-no blockers
  Q3: "Previous failed attempt?"
      Politics history, scar tissue
  Q4: "5 hats — champion / sponsor / funder / decider / user?"
      Same person or 5 different (large enterprise)
  
  Indonesia BNPL example:
    Champion: Head of Credit Ops (Maria)
    Sponsor: VP Engineering
    Funder: Regional GM
    Decider: Country Head
    User: Collection reps
    Veto: Compliance (OJK), IT (data residency)
  ```
- Top 3 gotchas: 假设单一 decider / 忽略 veto holder / 不查 previous failed
- Tools/tactics: 5-hat stakeholder map, RACI matrix, political history check

**Problem 3: Constraints Questions (技术 / 合规 / 时间)**
- 核心解法:
  ```
  Q1: "Deployment env — your cloud / our cloud / on-prem?"
      决定 architecture
  Q2: "Data residency — GDPR / industry reg / in-country?"
      决定 region serving
  Q3: "Integration systems — versions + APIs?"
      legacy ERP / CRM 集成挑战
  Q4: "Timeline + budget envelope first 12 months?"
      Scope reality check
  Q5: "What CAN'T change?"
      Org-mandated constraint
  
  Indonesia voice agent constraints found:
    Deployment: in-country DC (OJK)
    Integration: legacy collection system + telephony Twilio
    Timeline: 30-day MVP (board commit)
    Budget: $250k Y1
    Can't change: 无法 promise 减免 (legal)
  ```
- Top 3 gotchas: 不问 deployment 早 / 假设 data 自由跨境 / 没 budget envelope
- Tools/tactics: deployment matrix, compliance industry mapping, contract review

**Problem 4: Failure Mode Questions**
- 核心解法:
  ```
  Q1: "Cost of wrong answer — trivial / moderate / severe / catastrophic?"
      $1 / $100 / $10K / $1M+ tiers
  Q2: "Acceptable error rate? Industry reference:
       Consumer 5-10%, Credit < 1%, Medical < 0.01%"
  Q3: "Fallback path when AI fails?"
      Human escalation, scripted template, retry
  Q4: "Silent failure mode worry? (wrong answer looks right)"
      hallucination, drift, format break
  Q5: "Rollback / kill switch single command?"
      feature flag, customer credential
  
  Indonesia voice agent:
    Cost wrong: moderate ($100 customer ire, $0 financial)
    Error rate: < 3% acceptable
    Fallback: 转人工 agent
    Silent: model 越来越 apologetic 谁也不知道
    Kill switch: feature flag customer-held
  ```
- Top 3 gotchas: 不区分 trivial vs catastrophic / 没 industry reference / silent failure 忽略
- Tools/tactics: failure tolerance spectrum, kill switch design, silent failure detection plan

**Problem 5: Success Criteria Questions**
- 核心解法:
  ```
  Q1: "Week 1 dashboard — what number's on it?"
      Leading indicator, daily visibility
  Q2: "Month 1 — healthy vs course-correct threshold?"
      Mid checkpoint
  Q3: "Quarter 1 — ROI required for continued investment?"
      Lagging financial
  Q4: "Demo for sponsor — what artifact?"
      Visible value moment
  Q5: "Kill criteria + by-when?"
      Explicit exit, prevent goal-post shifting
  
  Indonesia voice agent:
    Week 1: # calls / day, repayment rate, customer complaint count
    Month 1: 12% → 14% mid-target
    Quarter 1: 12% → 16% on track for 18% target
    Demo: 10 sample calls with full audit log
    Kill: < 10% improvement by Q1 + complaint spike
  ```
- Top 3 gotchas: 没 leading indicator (lagging 才显结果, 太慢) / 没 kill criteria (goal-post shift) / 没 demo artifact
- Tools/tactics: dashboard template, weekly review cadence, exit criteria written

### 🔥 Production gotchas (top 15)

1. 上来 design 没 clarify → immediate fail FDE
2. 问 20 questions → interrogate
3. 问 random order → 不 prioritize signal
4. 没 "why I'm asking" → checklist 感
5. Accept vague KPI → wrong direction
6. 假设 single decider → 漏 veto holder
7. 不问 deployment env early → 后续返工
8. 没 industry reference for failure tolerance → 凭空说
9. 没 strawman ready → paralysis
10. 没 1-page proposal commit → slow vendor signal
11. 没 kill criteria → goal-post shift Q2
12. 没 5-hat 区分 (champion / sponsor / funder / decider / user)
13. 没 counter-example "current process failed when"
14. 不 push for specificity ("efficiency" → "tickets/hour")
15. follow-up email 没发 → 客户记忆漂移

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Indonesia voice agent discovery | TikTok PayLater Indonesia | 5 类 question 走过 KPI lock 18% |
| BNPL 4-stakeholder | BNPL chatbot | ops/legal/product/compliance map |
| Internal Platform 5-team | Internal Agent Platform | 14 teams 不同 KPI lock |
| Pakistan failure tolerance | Pakistan ASR cascade | < 3% acceptable, fallback human |
| ConvFinQA data discovery | ConvFinQA reference | data definition + topic stratify |
| 5-hat stakeholder | 7 markets voice agent | champion + sponsor + funder + decider + user 区分 |
| 1-page proposal 1 wk | Indonesia kickoff | fast vendor signal |
| Strawman propose | refund tier 1/2/3 | "8% error, $500 limit, 30d SLA" |
| Industry reference | financial < 1% | failure tolerance anchor |

### 🎤 面试现场 quotables (top 8)

1. "Before I design anything, I'd ask 5-7 questions in BSCFS order — Business, Stakeholders, Constraints, Failure, Success"
2. "Each question unlocks a design dimension — every question paired with why I'm asking"
3. "If I asked 20 questions you'd feel interrogated. Customer hates slow vendors. 5-7 is the sweet spot"
4. "KPI first, always. 'The ONE metric in 6 months — what number?' Without this, everything downstream is wrong direction"
5. "I never accept 'efficiency' — push to 'tickets per hour' or 'cost per ticket'. Specificity unlocks design"
6. "Industry reference for failure tolerance: consumer search 5-10%, credit < 1%, medical < 0.01%. I anchor unknown ranges"
7. "1-page proposal within 1 week — fast vendor signal. Customer hates slow vendors more than they hate questions"
8. "Indonesia voice agent — I locked KPI to '30-day cohort outbound-led repayment rate, 12% baseline, 18% target'. Took 30 min upfront, saved 8 weeks downstream"

### 🚨 红线 (top 10 anti-patterns)

1. Designing without asking (immediate fail)
2. 20+ questions (interrogation)
3. Accept vague KPI without push
4. No follow-up commitment (1-page proposal 1 wk)
5. No reference points for unknown answers
6. Generic question wording ("what's the budget")
7. 上来 random order (KPI 不先)
8. 没 "why I'm asking" 绑定
9. 假设 single decider, 漏 veto holder
10. 没 kill criteria → goal-post shift
