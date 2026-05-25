## Q09 · 描述你入职新 FDE 岗位的前 30/60/90 天计划

> "Walk me through your 30/60/90-day plan for this FDE role. What would you focus on in your first 30 days, then 60, then 90? How would you measure success at each milestone?"

**中文翻译**:

> "讲一下你来这个 FDE 岗位的前 30/60/90 天计划. 头 30 天你打算 focus 什么, 然后 60 天、90 天怎么递进? 每个 milestone 你怎么衡量成败?"

**Round**: Behavioral (30-45 min, hiring manager 或 cross-functional, 通常在 round 后期)
**出处**: Exponent 2026 FDE Guide · 公司: OpenAI / Anthropic / Palantir / Databricks / Scale AI 高频. 变体: "if hired, how would you spend your first 90 days?" / "describe your onboarding plan" / "what would your first project look like"

---

## 📖 术语速查 (本题用到的)

> 这题是 onboarding plan + 公司 specific 研究 + ramp-up 方法论 综合. 涉及大量公司专属产品 / paper / 框架术语.

### Plan 方法论 ⭐ 这题的核心

| 术语 | 解释 |
|---|---|
| **Escalating ambition** ⭐ | 递增式野心. 30 天 = learn (low output), 60 天 = contribute (small ship), 90 天 = own + propose. 不是均匀切分. |
| **Calibration with hiring manager** ⭐ | 跟招聘经理对齐. Day 1 1-hour 问 "what does success look like for YOU?". Plan 是 hypothesis, manager 答案 updates plan. |
| **Under-promise day 1, over-deliver day 90** | 起步少承诺, 收尾多交付. FDE rookie 反 pattern 是 over-promise. |
| **Exit criteria per milestone** | 每个 milestone 的退出标准. Measurable, not aspirational. |
| **30/60/90 ratio shift** | 时间分配比例随阶段变. Day 1-30 = 70% customer 30% internal. Day 31-60 = 50/30/20. Day 61-90 = 40/30/30. |
| **Low-hanging fruit (LHF)** | 容易摘的果子. Pod 已经想要但没时间做的小项目. |
| **Mid-size deliverable** | 中等规模交付. 不是 greenfield, 不是 high-stakes-renewal. 1 month scope. |
| **Contained 2-week first project** | 受限 2 周首个项目. Bounded, customer-facing, two-way door. |

### 公司专属 — OpenAI

| 术语 | 解释 |
|---|---|
| **Operator** ⭐ | OpenAI 的浏览器 + computer use agent. 能在网页上点按钮 / 填表. |
| **GPT-5** | OpenAI 的下一代 frontier model. |
| **Codex** | OpenAI 的 code agent / code 生成. |
| **ChatGPT Enterprise** | OpenAI 的企业版 ChatGPT. |
| **Custom GPTs / GPT Store** | 用户自定义 GPT + 共享市场. |
| **Realtime API** | OpenAI 的实时 voice + multimodal API. |
| **Stargate** | OpenAI + Microsoft 等的 $100B+ 数据中心 / 算力 投资项目. |
| **Eval & Deployment team** | OpenAI 内部专注 eval + 部署的团队. |
| **Tomoro acquisition** | OpenAI 2025 收购 Tomoro (Singapore agent company). |

### 公司专属 — Anthropic

| 术语 | 解释 |
|---|---|
| **Claude (3.7 / Opus / Sonnet / Haiku)** | Anthropic 的模型系列. |
| **Claude Code** | Anthropic 的 code agent / CLI. |
| **Constitutional AI** ⭐ | Anthropic 用 AI 反馈替代部分人类反馈做 alignment (RLAIF). |
| **Tool Use API** | Anthropic 的工具调用 API. |
| **Computer Use API** | Anthropic 的版本的 Operator (computer use). |
| **Core Views (on AI Safety)** | Anthropic 公开的 mission alignment 文档. |
| **RSP (Responsible Scaling Policy)** | 模型能力到某 threshold 才解锁部署的政策. |
| **Applied Solutions** | Anthropic 的 FDE-equivalent 团队名. |

### 公司专属 — Palantir

| 术语 | 解释 |
|---|---|
| **Foundry** ⭐ | Palantir 的数据 + ontology 平台. |
| **AIP (Palantir AI Platform)** | Palantir 把 LLM 接到 Foundry 上. |
| **Apollo** | Palantir 的 deployment 管理工具. |
| **Workshop** | Palantir 的 low-code app builder. |
| **Ontology** | Palantir 核心方法论 — 上层业务概念词典. |
| **Karp's letters** | Palantir CEO 每年的 shareholder letter, 哲学 + 战略. |

### 公司专属 — Databricks

| 术语 | 解释 |
|---|---|
| **Lakehouse** | Databricks 核心概念 — data lake + data warehouse 合一. |
| **MLflow** | Databricks 的 ML lifecycle 工具 (track / version / deploy). |
| **Mosaic AI** | Databricks 收购 Mosaic ML 后的 LLM stack. |
| **DBRX** | Databricks 开源的 MoE (Mixture of Experts) 模型. |
| **Unity Catalog** | Databricks 的数据治理工具. |
| **Genie** | Databricks 的 text-to-SQL AI. |
| **Spark / PySpark** | Apache Spark 大数据处理框架, Databricks 创始团队的核心技术. |
| **Notebook** | Databricks Notebook — Jupyter-like 协作环境. |

### Source of truth / Ramp 术语

| 术语 | 解释 |
|---|---|
| **Shadow (existing FDE on customer calls)** | 旁听老 FDE 客户会议. 不 contribute, only listen. |
| **Pod meetings** | 小组会议. Pod = FDE 团队的 sub-unit, 通常服务 1-2 个 customer. |
| **Cross-functional coffee** | 跨职能咖啡聊天. Sales / customer success / product 各人 30 min. |
| **Deployment retrospective** | 部署复盘. 老项目的 post-mortem 文档. |
| **Customer pod** | 客户小组. 服务特定客户的 FDE 团队. |
| **Internal tooling docs** | 内部工具文档. |
| **Stakeholder map** | 利益相关方地图. 谁决定 / 谁阻拦 / 谁付钱 / 谁用. |
| **Pattern recognition** | 模式识别. 60-day pattern notes 是 90-day proposal 的原材料. |

### 业务 / 评估术语

| 术语 | 解释 |
|---|---|
| **Customer renewal** | 客户续约. FDE 的 ultimate metric. |
| **Standard performance review trajectory** | 标准绩效评估轨迹. Hit plan = 标准 promotion track. |
| **Pilot scope (low-risk validation)** | 试点范围 — 低风险验证. |
| **Customer demonstrably better off** | 客户可证明地变好. "Ship 了" 不够, 客户实际有改善才算 outcome. |
| **'Go-to person' for 1 small dimension** | 某小方向的 go-to 人. RAG-based tool discovery / multi-market cultural review. |

### 反 pattern / 红线

| 术语 | 解释 |
|---|---|
| **Greenfield project** | 从 0 启动的项目. 90 天不该接, 风险高. |
| **High-stakes-renewal project** | 高风险续约项目. 90 天不该接. |
| **Tattling** | 打小报告. 升级太早给的感觉. |
| **Anti-rookie pattern** | 反新人 pattern. Don't ship code day 1, don't disagree publicly, don't propose major changes, don't over-promise. |

---

## 这道题在考什么

这是 **FDE 题里 most calibrated-thinking-required 的题**. 表面问 plan, 实际筛 6 件事:

- **Self-awareness about ramp** —— 你 know FDE 不是 day-1 contributing role, 还是 expect day-1 ship
- **Customer-first orientation** —— 30 天 你 prioritize 听 customer 还是 hack on tech
- **Output cadence (small first, big later)** —— 30/60/90 escalating ambition, 不是均匀
- **Calibration with hiring manager** —— 你 commit 之前 ask hiring manager 'what do you want'
- **Risk awareness** —— 你 know 90 天 ship 大东西 = under-deliver risk, 还是 over-promise
- **Org politics navigation** —— FDE 在 customer + product + research 之间, 30/60/90 你怎么 build relationship 在这 3 个 dimension

**没说出口的红线**:

- "Day 1 I'll start writing code" → 太 early, FDE ramp 必须 customer first
- "30 days learn, 60 days design, 90 days ship" → too rigid, 没 milestone signal
- "By 90 days I'll have shipped major project" → over-promise
- "I'll ask my manager what to do" → no agency
- "Same plan for any company" → no company-specific calibration
- 没有 "I'll calibrate this with hiring manager day 1" → no humility

---

## 完美答案架构 (Layered Response)

8 段结构, total ~5 分钟:

| # | 层 | 时间 | 这层该说什么 | 开口句 |
|---|---|---|---|---|
| 1 | **Frame — what 30/60/90 should be (心智模型: 30/60/90 应该是什么)** | 20s | Set up the mental model | "I think of 30/60/90 as escalating ambition: learn → contribute → own..." |
| 2 | **Calibration upfront (先跟 hiring manager 对齐)** | 20s | 你 day-1 跟 hiring manager align | "Day 1 I'd schedule 1-hour with hiring manager: what does success look like at each milestone for YOU?..." |
| 3 | **30-day plan — Learn / Listen (30 天 — 学习 / 倾听)** | 60s | Customer + team + product + tech ramp | "Days 1-30: I'd shadow 2-3 existing FDE on customer calls, sit in pod meetings, read 5 deployment docs..." |
| 4 | **30-day exit criteria (30 天退出标准)** | 20s | 具体 by day 30 you can articulate X | "By day 30: I can articulate top-3 customer pain patterns + team's 2 biggest blockers + 1 'low-hanging fruit' candidate..." |
| 5 | **60-day plan — Contribute (60 天 — 开始贡献)** | 60s | First small ship + relationship build | "Days 31-60: Take a contained 2-week first project — something the pod already wanted but hadn't gotten to..." |
| 6 | **60-day exit criteria (60 天退出标准)** | 20s | By day 60 ship + relationships | "By day 60: 1 shipped contained project + 3 customer relationships established + 1 cross-team relationship..." |
| 7 | **90-day plan — Own + propose (90 天 — own + 主动提案)** | 60s | Bigger ship + own bigger thing + propose | "Days 61-90: Take ownership of a medium customer deployment OR propose a small platform improvement based on patterns I've seen..." |
| 8 | **90-day exit criteria + how I measure (90 天退出标准 + 衡量方式)** | 30s | Success metric + Risk-of-over-promise ack | "By day 90: I'd want to have 1 mid-size deliverable, but I'll calibrate with hiring manager — over-promise day-1 is FDE rookie mistake..." |

Total: ~5 min. 8 段 必须均衡, 60-day + 90-day = real ship, 30-day = setup.

---

## 详细回答 (Sample Monologue) — 可以照背

> "我先 frame 一下 mental model, 然后 walk through each milestone.
>
> **Frame**:
>
> 30/60/90 不是均匀切分. 我看作 **escalating ambition**: 30 days = learn / listen (low output, high input), 60 days = contribute (small contained ship), 90 days = own + propose (medium scope + 1 strategic proposal).
>
> 反过来 anti-pattern: 'day 1 ship code' = ramp 不够 → 易 wrong scope. 'day 90 ship major project' = over-promise → 易 under-deliver. Calibrated escalation 是 sustainable.
>
> **Calibration upfront — Day 1 with hiring manager**:
>
> 我 day-1 schedule 1 hour with hiring manager 问 4 个 question:
>
> 1. What does success look like at 30 / 60 / 90 days **for you specifically**? (你 boss 怎么 judge me)
> 2. Who are top 3 customer accounts I should focus on?
> 3. What are top 2 blockers your existing FDE team faces?
> 4. What's 1 'I'd love this but haven't had time' project I could pick up?
>
> 我 plan 是 hypothesis. Hiring manager 答案 updates plan. 没 calibration upfront = 你 ship 一个 plan 服务自己想象的 role, 不服务 actual role.
>
> Day 1 calibration 之后, plan 可能 30/40/50 比 30/60/90 更适合. Adapt.
>
> 假设 hiring manager 答 'standard FDE onboarding', 我 default plan 如下.
>
> **Days 1-30: Learn / Listen / Build Relationships**:
>
> **Customer dimension (50% of 30-day time)**:
> - Shadow 2-3 existing FDE on customer calls. Listen, not contribute. **Goal**: understand customer interaction style at this company specifically.
> - Read 5 deployment retrospectives or post-mortems. **Goal**: pattern recognition before joining customer calls.
> - Sit in 2-3 internal customer pod meetings. **Goal**: understand pod dynamics.
> - Schedule 30-min coffee with 3-5 customer-facing teammate (sales / customer success / product). **Goal**: cross-functional relationship.
>
> **Product dimension (30% of 30-day time)**:
> - Read product changelog last 6 months. **Goal**: understand recent customer-facing feature/change.
> - Read top-5 most-used internal tooling docs. **Goal**: usable on common tasks.
> - Cold-DM 2-3 product team member (model team / API team / agent team), 30 min chat. **Goal**: how product team thinks vs FDE thinks.
>
> **Tech / domain dimension (20% of 30-day time)**:
> - Read codebase architecture overview + 1 reference deployment end-to-end.
> - Local set-up + run basic deployment locally.
> - Read 2-3 white papers / blog post on company-specific tech (if e.g. OpenAI: Operator paper + agent guide; if Anthropic: tool use paper; if Palantir: Foundry ontology paper).
>
> **What I DON'T do day 1-30**:
> - Write production code (except local exploration)
> - Propose major changes (I haven't earned context yet)
> - Disagree publicly (I haven't earned trust yet)
>
> **30-day exit criteria**:
>
> By day 30 I can articulate:
> - Top 3 customer pain patterns (across multiple customer accounts)
> - Team's 2 biggest internal blockers (e.g., deployment time, customer access)
> - 1 'low-hanging fruit' candidate project (something existing pod wants but hasn't done)
> - Map of 8-10 internal stakeholders (who decides, who blocks, who funds, who uses)
>
> Day 30 check-in with hiring manager: 'here's what I learned, here's my 60-day proposal'.
>
> **Days 31-60: Contribute (small contained ship)**:
>
> **First Project (40% of 60-day time)**:
> Take a **contained 2-week first project**. Criteria:
> - Pod already wanted it but hadn't gotten to
> - Bounded scope (no major architectural decision)
> - Customer-facing (so I learn customer interaction)
> - Failure mode is recoverable (two-way door)
>
> Examples (depends on company):
> - OpenAI: small enterprise customer onboarding (1 customer end-to-end, low complexity)
> - Anthropic: improve internal eval framework for 1 customer use case
> - Palantir: add 1 ontology dimension for existing customer
> - Databricks: 1 customer notebook deployment optimization
>
> **Relationship deepening (30% of 60-day time)**:
> - 3 customer relationships I'm now primary or secondary contact on
> - 1 cross-functional relationship that's now 'I'd Slack you for X' level
> - 30-min monthly with my manager: progress + obstacles + ask
>
> **Continued learning (20% of 60-day time)**:
> - Domain knowledge gap I identified in 30-day map
> - Tech / framework gap I identified
>
> **Pattern recognition (10% of 60-day time)**:
> - Across 4-5 customer interactions, what pattern emerges?
> - Bank in notes for 90-day proposal
>
> **60-day exit criteria**:
>
> - **1 shipped contained project** (real customer impact, not toy)
> - **3 customer relationships** at 'they Slack me directly' level
> - **1 cross-team relationship** at 'we'd grab coffee' level
> - **Mid-progress notes** for pattern recognition (raw material for 90-day proposal)
>
> Day 60 check-in: 'shipped X, learning Y, want to propose Z at 90 days'.
>
> **Days 61-90: Own + Propose**:
>
> **Medium Ownership Project (50% of 90-day time)**:
> Take a **medium customer deployment** — not greenfield, not high-stakes-renewal. Something with:
> - 1 month scope realistic
> - 3-5 stakeholders to navigate
> - 1 architectural decision required (so I demonstrate FDE judgment)
> - Failure mode: customer can survive, my reputation can survive
>
> **Pattern Proposal (20% of 90-day time)**:
> Based on 60 days of pattern recognition, propose **1 small platform / process improvement**:
> - Quantified pattern (e.g., "5 of last 10 customer onboardings hit X issue")
> - Specific proposal (not abstract)
> - Pilot scope (low-risk validation)
> - Champion identified (someone influential to convert)
>
> Examples:
> - Workshop + skeleton replacing spec doc (from my voice agent experience)
> - RAG-based tool discovery (from BNPL experience)
> - Cultural workshop mandatory in multi-market scoping
>
> **Cross-team engagement (15% of 90-day time)**:
> - Now I have enough context to interact with research / model team — ask 1 specific technical question, give 1 specific customer feedback
> - Volunteer for 1 cross-team initiative (don't lead, contribute)
>
> **Reflection / Calibration (15% of 90-day time)**:
> - Self-reflect: what did I get right? wrong? slow on?
> - Schedule 1-hour with hiring manager: 90-day review + 6-month plan calibration
>
> **90-day exit criteria + how I measure**:
>
> - **1 mid-size delivered project** (not just shipped, but **customer demonstrably better off**)
> - **1 proposed improvement** with pilot plan + champion lined up
> - **6-10 customer-facing relationships** at functional level
> - **2-3 internal cross-team relationships** at collaborator level
> - **1 documented pattern** I can teach next FDE onboarding
>
> **Risk-of-over-promise acknowledgment**:
>
> 90 days 是 hiring manager 用来 evaluate '是否 keep me' 的 timeframe. Over-promise day 1 = under-deliver day 90 = renewal at risk.
>
> 我 explicit calibrate: 'shipping 1 mid-size project + 1 proposal pilot' 是 ambitious-but-safe. 不 commit '90 days ship major customer-renewal project' because 它 over-promise.
>
> Better: under-promise day 1, over-deliver day 90.
>
> **How I'd measure success**:
>
> 3 dimension:
>
> 1. **Customer**: 1-2 customer told my manager 'good with you' unprompted
> 2. **Team**: I'm 'go-to person' for 1 small dimension (e.g., RAG-based tool discovery, multi-market cultural review)
> 3. **Personal**: I can articulate company-specific FDE flavor 比 day 1 deep 10×
>
> **Company-specific calibration (example: OpenAI)**:
>
> 如果 OpenAI:
> - 30 days: shadow 2 FDE on Fortune 500 customer call, read GPT-5 + Operator + Codex internal docs, sit in Eval & Deployment team meeting
> - 60 days: small enterprise customer end-to-end onboarding (1 customer)
> - 90 days: take medium customer deployment + propose 1 pattern improvement based on what I've seen at OpenAI specifically
>
> 不 generic. Specific to OpenAI FDE flavor."

---

## Gao Xin 简历专属 STAR 模板

这道题主要是 plan, 但需要 1 STAR demonstrating 我已经做过 30/60/90 ramp 在 unfamiliar context (proving plan is grounded in experience).

### ★ STAR 1: ConvFinQA Financial Reasoning Ramp (★ PROOF that I can execute 30/60/90)

**S** (Situation):
> "加入 ConvFinQA 项目时 unfamiliar domain. 4 month deadline. Lead engineer + methodology designer. 我 effectively executed a 30/60/90 ramp."

**T** (Task):
> "Ramp + ship parallel. By month 4 ship paper.

**A** (Action, mapped to 30/60/90 thinking):

**First 30 days** (week 1-4):
- Domain learning: book intro, 3 真实 10-K filings, 2 grad student lunch chat
- Source of truth: identified 4 specific expert
- First small delivery: data preprocessing pipeline (week 2)
- Outcome: domain map + 4 experts on speed dial + 1 deliverable

**Days 31-60** (week 5-8):
- Contained ship: retrieval module (week 4-6), numeric reasoning v1 (week 7-8)
- Relationship: finance grad student weekly review (paid honoraria)
- Calibrated confidence: confident on retrieval, partial on numeric, low on domain reasoning
- Outcome: 2 modules shipped + 1 weekly review cycle

**Days 61-90** (week 9-12):
- Ownership: own methodology design + 9-variant ablation
- Pattern: 'evidence-based pipeline design' team principle
- Cross-team: present at internal NLP forum
- Outcome: paper draft ready + methodology principle documented

**Days 91-120** (week 13-16): paper polish + submission

**R** (Result):
- Paper shipped on deadline
- Top-tier venue accepted
- Reviewer cited methodology design as paper strength
- I now use 30/60/90 framework for any new domain ramp

**Vulnerability line**:
> "我 ConvFinQA 30 days 我 spent too much time on 'breadth domain reading'. Hindsight: should have done 'one specific question per day' instead of 'general accounting overview'. Now my 30-day default: 'specific question per day with specific human, not breadth reading'. ConvFinQA paid 1 week tax for this lesson."

### STAR 2 (Alternate): Voice Agent Pakistan Market Onboarding 30/60/90

**S**: 巴基斯坦 voice agent onboarding, market #7 (after 6 markets experience). Effectively 90-day onboarding plan.

**T**: Onboard plus launch faster than prior markets (印尼 took 6 months, Vietnam 3 months, target 6 weeks for Pakistan).

**A**:
- **Days 1-30**: Workshop + skeleton with 巴基斯坦 ops (3 days), cultural review (1 week), persona design, ASR vendor selection per dialect
- **Days 31-60**: Pilot 100 users → 1000 users → full launch by day 50
- **Days 61-90**: Stabilization + cascade fallback per-language tune + handover to local on-call

**R**:
- **Pakistan launch in 6 weeks (vs 6 months Indonesia)**
- 0 cultural redo needed (cultural workshop default working)
- Cascade fallback caught Azure outage day 42

### STAR 3 (Alternate): Internal Agent Platform Bootstrap 30/60/90

**S**: Internal Agent Platform 从 0 启动. Effectively 90-day platform bootstrap.

**T**: 5 seed teams onboard within 90 days.

**A**:
- **Days 1-30**: Customer interview 5 seed teams (1 hour each), abstract commonality
- **Days 31-60**: 3-layer abstraction designed + 2 seed teams onboard (Risk + Marketing)
- **Days 61-90**: 5 seed teams onboard + first cross-team adoption pattern documented

**R**:
- 5 teams onboard 90 days
- 14 teams by month 6
- Pattern adopted as ByteDance internal agent infra standard

---

## 5 个 Follow-ups (interviewer 追问 + 准备答案)

### Follow-up 1: "What's the biggest risk in your 30-day plan?"

**Answer**:
> "Biggest risk: **spending too much time learning, not enough listening to customer**.
>
> Day 30 retrospective trigger: 我 explicit check 'how many hours did I spend on technical docs vs customer interaction?'. If technical > 50%, I'm in wrong mode.
>
> FDE ramp 90% 是 customer signal absorption, 10% 是 codebase familiarity. Reverse the typical SWE ramp.
>
> Real example: ConvFinQA 30 days 我 spent too much on technical literature (multi-hop NLP papers), 40% of time. Should have been 60% talking to grad students + 40% technical. 我 1 week tax 学到这个.
>
> 现在我 30-day default: customer interaction time ≥ 50%, technical reading ≤ 30%, internal team meeting 20%."

### Follow-up 2: "What if your first 30-day project is harder than expected?"

**Answer**:
> "**Two checkpoints**:
>
> **Checkpoint 1 — Day 7**: am I making progress proportional to plan? If 'I'm stuck' at day 7 on a 14-day project, raise flag immediately. Don't 'try harder for 7 more days'.
>
> **Checkpoint 2 — Day 14**: am I on track to deliver? If projecting > 21 days, that's > 50% slip — escalate to manager.
>
> Real example: Voice agent Pakistan ASR cascade per-language tuning — I projected 2 weeks, hit week 1 'I don't have eval framework', flagged. Manager pointed me to existing eval framework I missed. Saved 1 week.
>
> **Anti-pattern**: 'I'll figure it out solo' for new hire. Day-30 new hire asking for help is **expected**, not weakness. Day-90 me asking for help is harder. Use the new-hire privilege when it counts."

### Follow-up 3: "How do you balance customer needs vs internal team needs in 30/60/90?"

**Answer**:
> "**Different ratio per milestone**:
>
> **Days 1-30**: 70% customer signal absorption, 30% internal team. 我 onboarding, customer-facing 是 primary.
>
> **Days 31-60**: 50% customer (first project), 30% internal team (relationships), 20% pattern recognition. Balance.
>
> **Days 61-90**: 40% customer (medium project), 30% internal team (cross-team initiative), 20% propose pattern, 10% personal calibration.
>
> Notice 30-day 高 customer ratio, 90-day 更平衡. 因为 30 days customer is 你 source of truth. 90 days you have enough context to also serve internal team.
>
> **Anti-pattern**: 30 days 50% internal politics. 你 没 listened to customer yet, politics 没 ground."

### Follow-up 4: "What about salary expectations during 30/60/90?"

**Answer**:
> "Comp discussion is separate from plan, but related — manager 的 90-day evaluation 决定我 future comp.
>
> My implicit calibration: ambition during 90 days should support 'positive 90-day review = standard performance review trajectory'. Not 'rockstar' (over-promise), not 'mediocre' (under-promise).
>
> Concretely:
> - Hit 90-day plan = positive review = standard 1-year promotion track
> - Exceed (e.g., propose successfully pilot'd) = stretch review = accelerated
> - Under-deliver = honest about what happened, learn for next quarter
>
> 不 stress about comp 90 days. Stress about being **good 90-day FDE**. 后者 take care of前者."

### Follow-up 5: "What if hiring manager gives you a project on day 1 that contradicts your plan?"

**Answer**:
> "**I adapt**. 我的 plan 是 hypothesis. Manager 的 actual ask 是 fact.
>
> Example: 假设 manager day 1 say 'we have a critical customer escalation, jump in week 1'. 我 plan说 30-day shadow, 但 manager 的 ask 优先.
>
> 我 adapt:
> - Week 1-2: jump on escalation with senior FDE pair (I learn by doing)
> - Week 3-4: catch up on standard onboarding (shadow + read)
> - Day 30: same exit criteria, different sequencing
>
> 但 — 我 explicit say back to manager: 'I'll jump on escalation. I want to flag — I'm in ramp mode so I'll need senior pair for first 2 weeks to avoid silent mistakes. That OK?'
>
> Manager rather know I'm aware of ramp risk than have me silently ramp.
>
> **核心**: plan 是 default. Manager direction overrides plan. But I communicate trade-off explicitly."

---

## ❌ 死路答法 (碰了就挂)

### 死路 1: "Day 1 I'll start writing code."

**为什么挂**: FDE ramp 必须 customer first. Day 1 code = ramp failure mode.

**怎么改**: "Day 1-30 I'd shadow 2-3 FDE on customer calls + read deployment retros + cross-functional coffee. Code starts week 4-5 with contained scope."

---

### 死路 2: "I'll learn for 30 days, design for 60 days, ship for 90 days."

**为什么挂**: Too rigid. 没 milestone signal. FDE 实际 30/60/90 是 overlapping not sequential.

**怎么改**: Each milestone has its own learn / contribute / own ratio. 30-day = 70% learn 30% contribute. 60-day = 30% learn 50% contribute 20% propose. Overlapping.

---

### 死路 3: "By 90 days I'll have shipped a major project."

**为什么挂**: Over-promise. Major project 90 days = under-deliver risk. Hiring manager 听完 raise concern.

**怎么改**: "1 mid-size delivered project + 1 proposed improvement". Calibrated ambition.

---

### 死路 4: "I'll ask my manager what to do."

**为什么挂**: No agency. Hiring manager 想看 你 有 plan, 不是 wait for instructions.

**怎么改**: Plan 是 hypothesis, calibration with manager 是 update mechanism. "My default plan is X. I'd day-1 calibrate with you: does this fit your specific success criteria?"

---

### 死路 5: Same plan for any company

**为什么挂**: Generic = no research done. Each company FDE flavor different.

**怎么改**: 显式 company-specific calibration. OpenAI = enterprise + agent stack. Anthropic = safety + tool use. Palantir = ops + ontology. Each different 30-day reading + 60-day project type.

---

### 死路 6: 没有 risk-of-over-promise acknowledgment

**为什么挂**: Hiring manager 听完想 'great plan, but realistic?'. Without explicit risk acknowledgment, plan feels naive.

**怎么改**: "90-day plan over-promise is FDE rookie mistake. Better: under-promise day 1, over-deliver day 90". 显式 acknowledge.

---

### 死路 7: No exit criteria per milestone

**为什么挂**: Plan 没 measure mechanism = aspiration not plan.

**怎么改**: 30-day exit: I can articulate top-3 customer pain + 1 low-hanging-fruit candidate. 60-day exit: 1 shipped + 3 relationships. 90-day exit: 1 mid-size + 1 proposal pilot.

---

## ✅ 加分项 (top 5)

### 加分 1: 显式 "calibration with hiring manager day 1"

"Day 1 I'd schedule 1-hour with hiring manager: what does success look like for YOU?". 4 specific question to ask. 这种 humility + agency 是 senior signal.

### 加分 2: 30-day ratio 70% customer 30% internal

具体 ratio. Not abstract "I'll learn". "Customer signal absorption 70%, technical reading 30%". 这种 specificity 让 plan feel real.

### 加分 3: Company-specific examples

OpenAI = agent stack reading + Fortune 500 customer shadow. Anthropic = safety paper + customer use case eval. Palantir = ontology + customer ops sit-in. 显式 company-specific = research done.

### 加分 4: Risk-of-over-promise explicit acknowledgment

"90-day major project = under-deliver risk. Better under-promise over-deliver." 这种 senior-level risk awareness 让 manager 信你 not naive.

### 加分 5: Exit criteria specific + measurable

Each milestone "I can articulate top-3 X + ship Y + relationship Z". Measurable, not aspirational.

---

## 一句话总结

> **"30/60/90 plan" 的 winning answer 不是讲 ambition 多大, 是用 'calibration with hiring manager day 1 + 30-day = 70% customer 30% internal + 60-day = 1 contained ship + 90-day = 1 mid-size + 1 proposal + explicit exit criteria + risk-of-over-promise ack' 证明 "我 know FDE ramp 不是 day-1 code, 我有 escalating ambition framework, 我 day-1 calibrate plan with manager"**.
>
> Customer first 30-day, contained ship 60-day, mid-size + proposal 90-day. Under-promise day 1, over-deliver day 90.

---

## Cheat Sheet (面试前 30s 扫一眼)

```
Question type:
  Behavioral / Plan / Calibration (5 min monologue)
Key skill being tested:
  Ramp self-awareness + customer-first orientation + calibration with manager + escalating ambition + risk acknowledgment + measurable exit criteria

Answer arc (8 段):
  1. Frame mental model (20s)        — Escalating ambition, not uniform
  2. Calibration upfront (20s)       — Day 1 hiring manager 4 questions
  3. 30-day plan (60s)               — Learn / Listen / Build relationships
  4. 30-day exit criteria (20s)      — Articulate top 3 customer pain + 1 LHF
  5. 60-day plan (60s)               — 1 contained ship + relationships + pattern
  6. 60-day exit criteria (20s)      — 1 shipped + 3 customer + 1 cross-team
  7. 90-day plan (60s)               — 1 mid-size own + 1 pattern proposal
  8. 90-day exit + risk ack (30s)    — Under-promise over-deliver + measure 3 dim

Day-1 hiring manager 4 questions:
  1. Success at 30/60/90 days for YOU specifically?
  2. Top 3 customer accounts to focus?
  3. Top 2 blockers existing FDE team faces?
  4. 1 "I'd love this" project I could pick up?

30-day time allocation:
  Customer (50%): shadow FDE / pod meetings / cross-functional coffee
  Product (30%): changelog / tooling docs / product team chat
  Tech / Domain (20%): codebase / reference deployment / company-specific paper

What I DON'T do in 30 days:
  - Write production code
  - Propose major changes
  - Disagree publicly

30-day exit criteria:
  - Top 3 customer pain patterns
  - Team's 2 biggest internal blockers
  - 1 low-hanging fruit candidate
  - Map of 8-10 internal stakeholders

60-day plan:
  First Project (40%):  Contained 2-week, bounded, customer-facing, two-way door
  Relationships (30%):  3 customer + 1 cross-team
  Continued learning (20%): identified gaps
  Pattern recognition (10%): bank notes for 90-day proposal

60-day exit criteria:
  - 1 shipped contained project
  - 3 customer relationships "they Slack me directly"
  - 1 cross-team relationship "we'd grab coffee"
  - Mid-progress pattern notes

90-day plan:
  Medium Ownership (50%): 1 month scope, 3-5 stakeholders, 1 architectural decision
  Pattern Proposal (20%): quantified pattern + specific + pilot scope + champion
  Cross-team (15%): 1 specific technical question + 1 customer feedback to research
  Reflection (15%): 90-day review with manager + 6-month plan

90-day exit criteria:
  - 1 mid-size delivered (customer demonstrably better off)
  - 1 proposed improvement with pilot plan + champion
  - 6-10 customer relationships
  - 2-3 internal cross-team relationships
  - 1 documented pattern teachable to next FDE

How I measure success (3 dimension):
  Customer: 1-2 customer said "good with you" unprompted to manager
  Team: "go-to person" for 1 small dimension
  Personal: company-specific FDE flavor articulated 10× deeper than day 1

Company-specific calibration examples:
  OpenAI:    enterprise + agent stack + Fortune 500 customer shadow + Operator/Codex docs
  Anthropic: safety + tool use + customer compliance use case + Constitutional AI
  Palantir:  ops + ontology + Foundry + customer ops sit-in
  Databricks: data + Notebook + customer data team + Spark/Mosaic

Red lines:
  - "Day 1 write code" (ramp failure mode)
  - "Learn 30 / design 60 / ship 90" (too rigid sequential)
  - "Major project 90 days" (over-promise)
  - "Ask manager what to do" (no agency)
  - Same plan any company (no research)
  - No risk-of-over-promise (naive)
  - No exit criteria (aspiration not plan)

3 STAR (proving I can execute 30/60/90):
  STAR 1: ConvFinQA financial domain ramp (★ primary, paper deadline 4 months)
  STAR 2: Voice agent Pakistan 6-week launch (vs 6 month Indonesia)
  STAR 3: Internal Agent Platform 5 teams onboard 90 days

5 follow-ups ready:
  Q1: Biggest 30-day risk? → "Spending too much time learning, not enough listening"
  Q2: First project harder than expected? → "Day 7 / Day 14 checkpoints, escalate at >50% slip"
  Q3: Customer vs internal balance? → 70/30 day 1-30, 50/30/20 day 31-60, 40/30/30 day 61-90
  Q4: Comp expectations? → "Hit plan = standard track, exceed = accelerated, separate conversation"
  Q5: Manager gives day-1 project contradicting plan? → "Adapt, but flag ramp risk explicitly"

Anti-rookie patterns:
  - Don't ship code day 1 (customer first)
  - Don't disagree publicly day 1 (no trust earned)
  - Don't propose major changes day 1 (no context earned)
  - Don't over-promise (under-promise over-deliver instead)
  - Don't generic plan (company-specific calibration)
```
