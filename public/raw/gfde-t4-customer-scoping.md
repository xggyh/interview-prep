## 题目

> "Customer says: 'We want to use AI to make our sales team more efficient.' That's all you got. **First customer meeting next week**. Walk through how you'd **scope this into a 3-week MVP demo**."

或追问形态:

> "Walk through how you'd handle a customer who keeps changing their mind every meeting."

**Round**: FDE Scoping / Discovery (45-60 min)

---

## 这道题在考什么

最 FDE-flavor 题. 考你**ambiguity navigation + delivery speed**:

1. **Discovery framework** —— 不要立即写代码
2. **Stakeholder mapping** —— customer 不是单一 entity
3. **KPI 锁定** —— 1 个 number
4. **Decomposition** —— MVP 必须 ship 3 周
5. **Customer 心理** —— manage expectation + scope creep

---

## 必问 clarifying

需要你 **主动 ask 客户**:

**1. KPI**

> "If this works perfectly, what business metric improves and by how much? Quarterly revenue / win rate / time saved per rep?"

**2. Who uses**

> "Sales reps (front-line) or managers (oversight) or both? Different workflow."

**3. Current pain**

> "Walk me through a sales rep's day — where's the 30% of time that hurts most?"

**4. Existing stack**

> "Salesforce / HubSpot / Outlook? Calendar? Database? Need to integrate or build from scratch?"

**5. Success window**

> "When is the buying decision (i.e., budget approval) — 3 weeks / 3 months / next year? Affects scope."

---

## 5 步框架 (D·K·D·M·P)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Frame the FDE delivery framework |
| 5-15 min | Discovery (stakeholder interviews) |
| 15-25 min | KPI lock + decomposition |
| 25-35 min | MVP design (week 1-3 plan) |
| 35-45 min | Customer management (scope creep, change of mind) |

---

## 我会这样答（sample）

> "Before designing anything, I'd resist the urge to scope from my side. The ask is **vague on purpose** — customer hasn't done the thinking. My job week 0 is discovery, not code.
>
> **D·K·D·M·P framework**:
>
> **D — Discovery (Week 0, day 1-3)**:
>
> Stakeholder interviews — typically 5 people across roles:
>
> | Role | What I ask |
> |---|---|
> | **Sales VP** (sponsor / buyer) | Business goal: revenue / win rate / cost? Quarterly target? |
> | **Sales ops** | Current process: tools, manual steps, common pain |
> | **2 sales reps** | Day in life: where's 30% time wasted? Top 3 frustrations? |
> | **IT / security** | Constraints: data isolation, perms, deployment |
> | **CFO / budget owner** | What ROI threshold for approval? |
>
> 30-min each. Notes synthesized into **1-page stakeholder map**.
>
> **K — KPI lock**:
>
> Most likely 1 of:
> - **Time saved per rep per week** (e.g., 5 hr → 8 hr)
> - **Win rate increase** (e.g., 22% → 25%)
> - **Deal cycle time** (e.g., 90d → 60d)
> - **Lead quality** (e.g., qualified-to-meeting ratio)
>
> Pick **ONE primary KPI**. Document baseline + target + measurement method.
>
> Counter-example fail: 'improve sales efficiency' — too vague to demo, too hard to measure.
>
> **D — Decomposition**:
>
> Sales workflow has ~10 sub-steps:
>
> ```
> 1. Lead receives (email / inbound)
> 2. Lead qualification (research)
> 3. First outreach
> 4. Discovery call
> 5. Demo / pitch
> 6. Proposal
> 7. Negotiate
> 8. Close
> 9. Handoff to CS
> 10. Renew / expand
> ```
>
> Pick **smallest slice that demos value**. Hypothesis: top time-waste is steps 1-3 (lead qualification + outreach drafting).
>
> Phase plan:
> - **MVP (Week 1-3)**: agent helps qualify leads + draft first outreach
> - **Phase 2 (Week 4-8)**: discovery call notes + auto-CRM update
> - **Phase 3 (Week 9-12)**: full sales conversation analysis
> - **Phase 4+ (future)**: forecasting / pipeline reasoning
>
> **M — MVP demo (Week 1-3)**:
>
> Goal: **show 1 rep doing 1 lead qualification in 5 min instead of 30 min**.
>
> Architecture:
>
> ```
> Lead arrives
>   ↓
> Agent loads CRM context, recent emails, company news (RAG)
>   ↓
> Agent generates qualification summary + suggested next action
>   ↓
> Rep reviews (UI: edit / accept / reject)
>   ↓
> Agent drafts first outreach email
>   ↓
> Rep edits + sends
> ```
>
> Tech stack (deliberately minimal):
> - LLM: Gemini 3 Pro for reasoning ($2/$12 per 1M), Gemini 3 Flash for cheap operations ($0.50/$3) — skip self-hosted for MVP
> - Vector DB: Pinecone (cloud, fast)
> - Frontend: simple web form (Streamlit / Next.js)
> - Integration: read-only Salesforce API + Outlook
> - Deployment: GCP / AWS, single tenant for MVP
>
> Anti-perfection rules:
> - Hardcoded company list OK
> - No multi-tenancy yet
> - No proper auth (basic password)
> - No fancy UI
> - **Single happy path works end-to-end** — that's the MVP
>
> **P — Pilot (Week 4-12)**:
>
> - Deploy to 3 pilot reps
> - Weekly review (what worked, what didn't)
> - Iterate on prompts + UI
> - Quantify KPI delta vs baseline (control reps comparison)
> - Expand to 20 reps based on results
>
> **Customer management tactics**:
>
> **When customer changes mind**:
>
> ```
> Customer (week 2): "Actually, can it also do forecasting?"
> 
> FDE response: "Yes, that's a great Phase 3 idea. To not delay your week-3 demo,
> let's keep MVP focused on lead qualification. I'll write up a forecasting
> phase doc for our week-4 review — we can decide then to bump it to next."
> ```
>
> **When customer demands faster**:
>
> ```
> "We need this in 1 week, not 3."
>
> Response: "1 week is possible if we strip even further. I'd propose:
> - Week 1: hardcoded for 5 leads, manual run
> - Week 2-3: integrate properly + automate
> The week-1 version is a proof you can show your CEO, not production."
> ```
>
> **When customer says 'we want full automation'**:
>
> ```
> Response: "We can get there incrementally. Phase 1 = agent suggests, rep approves.
> Phase 2 = agent auto-acts on approved patterns. Phase 3 = autonomous within bounds.
> Going straight to autonomous = high risk + low trust = fail.
> Confidence + audit data builds trust over weeks."
> ```
>
> **Week 1-3 timeline**:
>
> Week 1 (days 1-5):
> - Stakeholder interviews (days 1-2)
> - KPI lock + 1-page design (day 3)
> - Architecture sketch + LLM prompt iteration (days 4-5)
> - Setup: cloud accounts, Salesforce API access, vector DB
>
> Week 2 (days 6-10):
> - Build core agent loop (days 6-8)
> - RAG over CRM + emails (days 8-9)
> - UI (day 10)
>
> Week 3 (days 11-15):
> - Integration testing (days 11-12)
> - Demo prep (day 13)
> - **Customer demo (day 14)**
> - Same-day feedback synthesis (day 15)
>
> **Anti-patterns I'd avoid**:
> - Spending weeks 1-2 on perfect architecture
> - Building multi-tenancy / scalability features pre-validation
> - Promising 100% automation
> - Skipping stakeholder interviews
> - Doing it in isolation (not showing customer until week 3 = no early feedback)"

---

## 多场景变体 + 解法

### 变体 1: Customer support automation

> "客户说: 'AI 接管我们的客服, 70% 自动'"

**解法**:
- **Discovery**: 看 top-N intent (probably 80% 是 5-10 intents)
- **KPI**: deflection rate (% 不转人工) / CSAT / handle time
- **MVP**: 1 个最常 intent (e.g., 'where is my order') 端到端
- **Trust ladder**: 先 suggest-only (人 review), 再渐 auto, 再 fully autonomous
- **Anti-pattern**: 一上来就 100% 自动, 砸品牌

### 变体 2: 内部 IT helpdesk agent

> "员工 IT 问题 (Wi-Fi / VPN / 密码 reset), 用 AI 接"

**解法**:
- **Discovery**: ticket 历史 mining, top intents
- **KPI**: avg resolution time (人 30 min → 目标 5 min)
- **MVP**: 密码 reset (high volume, automatable) 一键解决
- **Integration**: SSO / AD / MDM 接口
- **Risk lower than customer-facing**: 内部 user 更容忍 试错
- **Self-serve docs**: agent 先 retrieve KB, 答 + 提供 link

### 变体 3: Marketing content gen

> "1 marketing team 想用 AI 加速 content (blog / social / ad copy)"

**解法**:
- **KPI**: time per post (8h → 2h), quality (engagement metric)
- **MVP**: 1 个 channel (e.g., LinkedIn post) 端到端 — brief → draft → human edit
- **Brand voice**: brand guide → system prompt + few-shot 例子
- **Workflow**: agent 出 3 个 variant, human 选 + 改
- **不是 full auto**: 创意 / brand voice 难全自动, 人在 loop
- **Reuse mechanism**: 高效 prompt template 沉淀成组织资产

### 变体 4: Data analyst assistant

> "Non-tech 业务想 ask data question in English"

**解法**:
- **KPI**: questions answered / day, accuracy on labeled set
- **MVP**: 1 个 specific dashboard / schema (不是 'all data')
- **Text2SQL**: agent 出 SQL + run + plot
- **Confirm-required for expensive query**: 'this will scan 10TB, confirm?'
- **Verifier**: SQL result 给 LLM 校验语义合理 (sanity check)
- **Iterative**: user 改问题, agent 改 SQL, 不是 1-shot

### 变体 5: Engineer code assistant

> "Internal dev tooling — 帮 engineer 写 code"

**解法**:
- **KPI**: tickets closed / day, code review iteration count, dev satisfaction
- **MVP**: 1 specific task (test generation? boilerplate refactor?)
- **Trust ladder**: PR suggestion → PR auto-create-review-required → ...
- **Repo-aware**: AST + symbol graph + recent commits 作 context
- **Eval**: 历史 PR replay 看 agent 解法对不对

---

## 简历专属 reframe

| 题 | 你做过 |
|---|---|
| Customer scoping | Voice agent 7 markets — every market needed scoping |
| Stakeholder map | TikTok payment — multi-stakeholder (ops / finance / engineering) |
| KPI lock | Indonesia refund tier — refund rate / approval time / accuracy 单一 KPI |
| MVP in 3 weeks | Voice agent expansion — each market 3-4 week MVP |
| Scope creep mgmt | Internal Agent Platform — customer requests filtered into roadmap |

**Quote**:

> "Voice agent expansion to Indonesia — exactly this shape. Week 0 = stakeholder map (operations head, compliance, finance, IT). KPI = **collection effectiveness rate** (single number, baseline 18%, target 25%). MVP week 1-3 = 1 use case (overdue payment reminder), Bahasa Indonesia voice, hardcoded customer list of 100. Demo to ops head week 3. Iterate to broader product in week 4-8. Same playbook for Vietnam / Thailand / Philippines."

---

## 5 follow-ups

**Q1**: "Customer is non-technical. How present design?"
**A**:
- **No architecture diagrams in first meeting**
- Show: **before / after rep workflow** (storyboard)
- Show: **estimated time saved** with concrete numbers
- Architecture only in tech-stakeholder meeting
- Use customer's vocabulary, not 'embedding / vector / agent'

**Q2**: "What if I can't get stakeholder interviews booked?"
**A**:
- **Async via doc**: send 5-question one-pager, ask buyer to fill or forward
- **Observe**: shadow a rep for a day (huge info gain)
- **Public data**: customer's job posts / press releases reveal priorities
- **Reduce to fewer interviews** + caveat the design with assumptions

**Q3**: "Customer wants 'agentic' as buzzword but actual need is simpler?"
**A**: Build what's needed:
- "We're delivering an agent-architecture solution that may not need full autonomy in v1. v1 = suggest + approve. v2 = expand autonomy as trust builds."
- They keep the marketing language, you build the right thing.
- **Don't add complexity to satisfy buzzword**

**Q4**: "MVP demo fails — customer underwhelmed."
**A**:
- **Diagnosis**: what did they expect vs what you showed?
- **Common cause**: KPI not visible in demo (showed feature, didn't measure)
- **Recovery**: 'I heard X — let me regroup, here's revised plan for next week'
- **Better than hiding**: face it head-on, ship revised demo fast

**Q5**: "Scope creep — customer keeps adding 'small' requests."
**A**:
- **Roadmap document** maintained: every request goes in, dated
- **Trade-off framing**: "Adding X means delaying Y by 1 week. Which?"
- **Quarterly re-prioritize**: not every meeting, prevent thrashing
- **Buyer enforces** scope on internal stakeholders (not you)

---

## ❌ 易错点

1. **Write code week 1** — no scoping
2. **No stakeholder interviews** — design wrong thing
3. **Multiple KPIs** — confusion
4. **Try to automate all 10 steps** — no MVP
5. **No demo until production-ready** — no feedback loop
6. **Build for perfection** week 1 — slow ship
7. **Say yes to every scope add** — never ship

---

## ✅ 加分项

1. **D·K·D·M·P framework** named explicitly
2. **5 stakeholder roles** to interview
3. **1 KPI** lock with baseline / target / measure
4. **Smallest vertical slice** for MVP
5. **3-week timeline** with daily breakdown
6. **Scope creep** management tactics
7. **Customer change-of-mind** handling
8. **Quote Indonesia refund tier scoping**

---

## Cheat Sheet

```
D·K·D·M·P framework:
  Discovery (week 0, day 1-3): 5 stakeholder interviews
  KPI lock: 1 number, baseline + target + measure
  Decomposition: workflow → MVP / phase 2 / phase 3
  MVP demo: week 1-3, vertical slice
  Pilot rollout: week 4-12, feedback loop

5 stakeholder roles:
  Sales VP (sponsor / buyer)
  Sales ops (process owner)
  2 reps (daily user)
  IT / security (constraints)
  CFO (ROI threshold)

KPI examples:
  Time saved per rep
  Win rate
  Deal cycle time
  Lead quality
  Pick ONE primary

Decomposition heuristic:
  10 sales steps → top 1-3 by time spent
  MVP = smallest demo of value

MVP design rules:
  Hardcoded list OK
  Single happy path
  No multi-tenancy
  No fancy UI
  No proper auth
  Just core workflow

3-week timeline:
  Wk1: discovery + design + setup
  Wk2: build core
  Wk3: integrate + demo

Customer management:
  Change of mind → roadmap, defer to next phase
  'Faster please' → strip further, multi-stage
  '100% automation' → incremental autonomy
  Non-technical → storyboard, not architecture
  Buzzword 'agentic' → build right, keep their language

Scope creep:
  Roadmap doc, dated
  Trade-off framing (X delays Y)
  Quarterly re-prioritize
  Buyer enforces scope

Anti-patterns:
  - Write code week 1
  - No stakeholder map
  - Multiple KPIs
  - Try automate all steps
  - No demo til ready
  - Build for perfection
  - Say yes to all scope

红线 (Anti-pattern):
  - Spec before demo
  - 100% automation promise
  - Skip clarifying
  - Vendor-style narrative
  - Ignore IT/Security
  - No observability
  - Heroics culture
```
