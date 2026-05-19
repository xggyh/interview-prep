## 题目（verbatim）

> **[OpenAI Solution Design Round - 60 min]**
>
> Open-ended: "**Design a complete AI solution for a company's business problem.** But first — **what questions would you ask the customer before designing anything?**"

**出处**：OpenAI FDE 真题. Palantir / Google Cloud FDE 都问类似. **Skip this question = immediate fail** for FDE.

**Round**：Solution Design (60 min)

---

## 这道题在考什么

考 FDE 灵魂 —— **不 clarify 就 design = vendor 思维不是 FDE 思维**:

1. **Customer-first instinct** —— 你是否本能上 want to understand before solving
2. **Question structure** —— 你 ask 的 order 体现 prioritization
3. **What you ask for** —— stakeholder / KPI / data / constraint / failure tolerance
4. **Pattern recognition** —— 你见过 enough deployment 知道 what to verify
5. **Boundary** —— 不要 fish forever, eventually commit to solve

---

## 必问的 5 个 question categories

### 1. Business / KPI (必)

> - **What's the ONE metric** that would tell you in 6 months 'this worked'?
> - **What's the current baseline** without our system?
> - **Who's the buyer**? Who's the user? Who's the loser if we succeed?
> - **Budget envelope** for this initiative?
> - **What happens to people whose jobs are partially automated** by this?

### 2. Stakeholders / Politics

> - **Who's the executive sponsor** + their incentive?
> - **Who could veto** deployment? (IT, legal, compliance, finance)
> - **What other vendors / internal teams** are in the space?
> - **Is there a previous failed attempt** at this problem?
> - **Who do you trust** on the technical evaluation side?

### 3. Data / Integration

> - **What data exists** and where? Quality?
> - **How fresh** does it need to be?
> - **What systems need to integrate**? Their owners?
> - **What's the auth / security model**?
> - **Privacy / compliance constraints** (GDPR, HIPAA, regulatory)?

### 4. Constraints / Reality

> - **What's the deployment environment** — your cloud, our cloud, on-premise, edge?
> - **Network / latency** requirements?
> - **Scale** today and in 12 months?
> - **What CAN'T change** (e.g., existing ERP, regulatory framework)?
> - **Compliance / audit requirements**?

### 5. Failure tolerance

> - **What's the cost of a wrong answer**? Trivial (re-prompt) vs catastrophic (financial loss)
> - **Acceptable error rate**? 1%? 0.01%? Zero (impossible — adjust expectations)
> - **What's the fallback** when AI fails?
> - **Who reviews edge cases**?
> - **Acceptable latency** for the user?

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-2 min | 框架 introduction — what categories of question I'll cover |
| 2-15 min | Ask categories 1-5 (above), with **why each matters** |
| 15-25 min | Based on assumed answers, **scope to a sub-problem** |
| 25-40 min | Solution design at high level |
| 40-50 min | Deep dive on a chosen component |
| 50-60 min | Failure modes + phasing |

---

## 我会这样答（sample monologue）

> "Before designing anything, I'd ask 5 categories of question — each unblocks a different design dimension.
>
> **Category 1: Business KPI** — what does success look like?
> Specifically: 'What's the ONE metric that would tell you in 6 months this worked? What's the current baseline? Who's the executive sponsor and their incentive?'
>
> Why first: every other design decision optimizes for this metric. If I don't know it, I'll design for the wrong thing.
>
> **Category 2: Stakeholders / Politics**:
> 'Who could veto deployment — IT, legal, compliance, finance? Is there a previous failed attempt at this problem?'
>
> Why: 90% of AI deployments fail on **integration / political**, not technical. If IT is opposed, my architecture has to be different.
>
> **Category 3: Data & Integration**:
> 'What data exists, where, and what quality? What systems need to integrate? Their owners? Privacy / compliance constraints?'
>
> Why: AI without data is impossible, and integration without IT cooperation takes 6 months.
>
> **Category 4: Constraints**:
> 'Deployment environment? Scale today vs 12 months? What CAN'T change?'
>
> Why: 'must run on-prem' or 'must integrate with this 15-year-old ERP' dictates entirely different architecture.
>
> **Category 5: Failure tolerance**:
> 'What's the cost of a wrong answer? Acceptable error rate? Fallback when AI fails?'
>
> Why: if it's $0.10 per wrong answer, we move fast. If it's medical decision, completely different rigor.
>
> **My order of asking**: KPI first, stakeholders second, then data/constraints/failure together.
>
> **Pragmatic limit**: I ask 5-7 questions max in first conversation. If I ask 20 questions, customer thinks I'm not listening. **The remaining questions come up during follow-up sessions as we go**.
>
> **Then I'd commit to a 1-page design proposal within 1 week**, not 4 weeks. Customer hates slow vendors.
>
> Now, assuming you've answered the questions, let me design for [example: customer service Co-pilot for our finance product, KPI=ticket resolution time, sponsor=customer ops lead, must integrate with their existing ServiceNow, on-prem allowed, < 1% wrong answers, fallback = human agent]:
>
> *[Continue with actual solution design...]*"

---

## 简历专属 reframe

你的 **Indonesia refund tier scoping** + **voice agent 7 markets** + **BNPL chatbot** all involve customer-first clarification:

| 题 | 你做过 |
|---|---|
| KPI-first scoping | Refund tier — you measured 70% throughput at 0% risk |
| Stakeholder mapping | 7 markets each has unique regulator + ops + product |
| Integration constraint discovery | Voice agent legacy repayment systems |
| Failure tolerance triage | Refund tier — different per category |

**主动说**:

> "I do this every time I scope a new initiative. For the voice agent's Indonesia rollout, I started with 30 minutes of 'questions before designing': KPI was repayment rate (not collection volume — they were different); sponsor was head of credit operations (not the CTO who reached out); deployment had to run **inside Indonesia data residency**, no exception. **Half my design decisions were determined by these 3 facts before I drew a single architecture diagram**. Without that conversation I would have designed something the customer couldn't deploy."

---

## 5 follow-ups

**Q1**: "Customer is impatient — wants design now, not questions."
**A**: 不投降:
- "I hear you. I can sketch a strawman design in 10 minutes — but I want to flag **3 assumptions I'm making, any of which if wrong invalidates the design**. Want me to ask those 3 questions first, or sketch then ask?"
- **Frame as: questions save time, not waste it**

**Q2**: "Customer's answer to 'what's the KPI' is 'increase efficiency'. Now what?"
**A**: Push deeper:
- "What does 'efficiency' look like to your VP? Tickets per hour? Cost per ticket? Average handle time?"
- "If I came back in 6 months with a 30% improvement in ticket resolution time, would your VP renew this contract?"
- **Forcing the metric specific is part of the FDE value**.

**Q3**: "Customer doesn't know failure tolerance — first time deploying AI."
**A**: Frame it:
- "Let me give you 3 reference points: (a) consumer search engine — wrong result is annoying, retry is free; (b) credit decision — wrong call has financial + regulatory impact; (c) medical diagnosis — wrong call is life-threatening. Where on this spectrum are your use cases?"
- **Help them think it through**, don't make them know in advance.

**Q4**: "Customer's 'must-have' constraints are unrealistic (e.g., 0% error rate)."
**A**: Reset expectations:
- "Zero error is impossible for any AI system. Let's talk about: (a) what error rate is **detectable** by your team and **reversible**, (b) what error rate triggers **catastrophic** loss vs **annoying** loss, (c) what error rate the **current manual process** has."
- Use **current process error rate** as anchor — usually their manual is 2-5%, our AI will be < 1% in most domains.

**Q5**: "Do you ever skip questions and just design?"
**A**: Honest:
- "Yes, but only on small / well-scoped problems where I've solved exactly this 3+ times before. **First deployment of new domain — never skip**. The cost of designing wrong thing is always higher than 1 hour of clarification."

---

## ❌ 易错点

1. **Start designing without asking** — fastest fail
2. **Ask 20 questions** — customer feels interrogated
3. **Ask without "why this matters"** — questions seem arbitrary
4. **No prioritization** — KPI before integration before failure
5. **Take answers at face value** — customer's stated KPI ≠ real KPI sometimes
6. **Don't push for specificity** — accept "increase efficiency" as answer
7. **Don't commit to next step** — questions go nowhere

---

## ✅ 加分项

1. **5 category framework** explicit
2. **Why each matters** — show pattern recognition
3. **Order matters** (KPI first)
4. **5-7 questions limit** — pragmatic
5. **Strawman + flag assumptions** — for impatient customer
6. **Frame impossible constraints** with reference points
7. **Quote Indonesia voice agent scoping**
8. **1-page design in 1 week** commitment

---

## Cheat Sheet

```
5 question categories (ask in order):
  1. Business / KPI (the single metric)
  2. Stakeholders / Politics (sponsor + veto power)
  3. Data / Integration (where + quality + owners)
  4. Constraints / Reality (deployment + scale + can't change)
  5. Failure tolerance (cost of wrong + fallback)

Specific questions:
  KPI:
    - One metric, success at 6 months
    - Current baseline
    - Executive sponsor + their incentive
  
  Stakeholders:
    - Who could veto
    - Previous failed attempts
    - Other vendors / internal teams
  
  Data:
    - What exists + quality + freshness
    - Integration systems + owners
    - Privacy / compliance
  
  Constraints:
    - Deployment env
    - Scale (now + 12mo)
    - What can't change
  
  Failure:
    - Cost of wrong answer
    - Acceptable error rate
    - Fallback path

Rules:
  - 5-7 questions max in first conversation
  - Each question paired with "why"
  - KPI first, always
  - Push for specificity ("efficiency" → "tickets per hour")
  - 1-page proposal within 1 week

For impatient customer:
  "I can sketch + flag 3 assumptions, or ask first"
  Frame: questions save time, not waste

For unrealistic constraints:
  Use 3-tier reference (consumer / financial / medical)
  Anchor to customer's current manual process error rate

红线:
  - Designing without asking
  - 20+ questions (interrogation)
  - Accept vague KPI
  - No follow-up commitment
```
