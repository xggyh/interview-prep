## 题目（verbatim）

> "Client **demands a 6-week feature delivered in 3 days**. Manage expectations without losing the relationship."

**出处**：fde.academy 客户模拟. 几乎所有 enterprise SaaS FDE 都遇到.

**Round**：Client Simulation (45 min)

---

## 这道题在考什么

考你**scope negotiation + 拒绝艺术**：

1. **不能直接说 no** —— 杀关系
2. **不能直接说 yes** —— 杀团队
3. **Decompose** the ask 找 what they really need
4. **Tradeoff transparency** —— 给客户做选择, 不替他们做
5. **Counter-offer** with phased delivery

---

## 黄金 framework：D·D·O·C

| Step | What | Sample line |
|---|---|---|
| **D** | **Deeper why** | "Help me understand the urgency — what happens on day 4 if this isn't ready?" |
| **D** | **Decompose** | "Of the 6-week scope, what's the **must-have-on-day-3** vs nice-to-have?" |
| **O** | **Offer phased** | "Here's what I think is feasible: Tier 1 in 3 days (covers your urgent need), Tier 2 in 2 weeks, Tier 3 in 6 weeks." |
| **C** | **Commit specifically** | "By Thursday 5pm I'll have Tier 1 demoed. Want my CTO to send written commitment?" |

---

## 5 个 "do say"

✅ "Help me understand what happens on day 4" → reveals real driver
✅ "If we shipped only 30% in 3 days, would that cover the critical use case?" → opens decomposition
✅ "Here are 3 options with tradeoffs..." → put choice on them
✅ "I want to be honest — if we promise 6w in 3d, we'll ship buggy work that we'll spend the next 3 weeks fixing" → transparent risk
✅ "Can we get your team to do X part, so my team can focus on Y?" → joint ownership

---

## 5 个 "do not say"

❌ "That's not possible" → relationship-ender, doesn't open dialog
❌ "Let me check with engineering" → punt, slow, looks weak
❌ "We'll try our best" → commitment by ambiguity, sets up failure
❌ "If we work weekends..." → heroics promise, sets unsustainable precedent
❌ "Your timeline is unreasonable" → blames customer

---

## Sample script

> *[Client: "I need the multi-tenant analytics dashboard by Thursday — 3 days from now."]*
>
> "OK, I hear you on the urgency. Two quick questions before I propose something:
>
> 1. Help me understand what's driving Thursday — is there a specific meeting / customer commitment / board deadline?
>
> *[Client: "I'm presenting Q3 wins to the CFO Thursday. I need to show analytics."]*
>
> 2. Of the full analytics dashboard (multi-tenant, drill-down, exports, alerts, scheduled reports), **what's the absolute minimum that gets you through Thursday's CFO meeting**?
>
> *[Client: "Just showing total volume + revenue per customer for top 10 customers, in a chart."]*
>
> Got it. So the **must-have-for-CFO** is a clean visualization of 10 numbers, not the full feature. Let me propose 3 options:
>
> **Option A (3 days)**: Single-tenant view of top-10 customer volume + revenue, exported to a Looker dashboard. Not the full multi-tenant analytics, but **CFO won't know the difference for Thursday**. Estimated cost: 2 engineer-days.
>
> **Option B (2 weeks)**: Above + per-customer drill-down + 1-month historical. Better, but not Thursday-feasible.
>
> **Option C (6 weeks)**: Full original scope. The right long-term answer.
>
> **My recommendation**: Option A for Thursday, then we de-prioritize a less urgent feature on our roadmap to start B+C immediately. CFO gets her meeting, we don't ship rushed multi-tenant code that haunts us.
>
> One ask back: **can your data team provide a CSV of the 10 customer aggregates by tomorrow EOD**? That lets us focus on visualization, not data plumbing.
>
> If you go with Option A, I'll have it demoed by Thursday morning, plenty of buffer for CFO afternoon. **Want my CTO to send written commitment by EOD today?**"

⏱️ ~5 min conversation.

---

## 简历专属 reframe

你的 **Indonesia refund tier scoping** HR 用过的故事 —— **直接套**。

| 题 | 你的故事 |
|---|---|
| Client wants 6w in 3d | Indonesia ops wanted full auto-refund |
| Decompose into tiers | Tier 1 (info lookup) / Tier 2 (structured) / Tier 3 (refund) |
| Offer phased | Tier 1 first → measure → expand |
| Save relationship | Got 70% throughput at 0% risk |

**主动说**：

> "This is **exactly** the move I made with Indonesia ops 6 months ago. They wanted full autonomous refund decisions on day 1. I decomposed into 3 tiers — lookup, structured tasks, refund decisions. Shipped tier 1 in 2 weeks, ran 2 weeks of data, then graduated. **They got 70% of the value in 4 weeks with 0% accuracy risk**, vs the alternative which would've been an 8% wrong-call rate.
>
> The lesson I'd apply here: **what they ask for is rarely what they actually need**. The honest question is 'what's the smallest thing that gets you through Thursday', then build that with a roadmap to bigger."

---

## 5 个 follow-ups

**Q1**: "Client refuses tiering — wants everything Thursday."
**A**: 升级 transparency:
- "I want to be honest with you. We can ship **a version** in 3 days, but it will have known bugs and we'll spend the next 4 weeks fixing them. The total time-to-stable will be **longer** than tiering. **The CFO meeting is the wrong use case to risk a bad demo on.**"
- Bring in your manager / their account manager if needed — peer-level conversation often unblocks

**Q2**: "Client agrees to tier 1, but on Thursday demands tier 3 ready 'soon'."
**A**: This is **goal-post shifting**, common pattern. Counter:
- "Glad tier 1 works for CFO. Let me put tier 2 + 3 on the official roadmap with dates. **Tier 2 by week 5, Tier 3 by week 10**. I'll send a tracking doc with weekly updates so you have visibility."
- **Concrete dates with written commitment** > vague urgency.

**Q3**: "Your engineering manager says even tier 1 in 3 days is impossible."
**A**: Don't 1-sidedly promise customer:
- Acknowledge engineering's constraint: "If tier 1 can't be done in 3 days, what can?"
- Find the **smallest possible 3-day deliverable** — maybe a hardcoded mockup, manual data pull, single-customer view
- Re-propose to customer with the actually-feasible version

**Q4**: "Customer says other vendor promised 6w-in-3d."
**A**: Don't take the bait:
- "If they can really do that with quality, they should win this. Honestly — I'd rather lose this deal than ship something that hurts both our reputations. **But in my experience, promises like that mean the work continues for weeks past the demo**. I'd ask them: what happens day 4-30?"
- This converts to **due diligence**: if you're confident in your team's craft, exposing it as superior is the move.

**Q5**: "Sales manager pressures you to commit to 6w-in-3d to close the deal."
**A**: Hardest. Internal alignment first:
- "If we commit, here are the 3 ways this fails — buggy demo + 4-week recovery / can't actually demo + lost trust / team burnout + attrition."
- Offer: "I can commit to tier-1 in 3 days, full scope by week 10. **If sales needs 6w-in-3d, that's a different deal with caveats** — let's get legal to write 'demo readiness' rather than 'production-ready'."
- Worst case, **document your concerns in writing** to sales / leadership before agreeing.

---

## ❌ 易错点

1. **直接 no** — kills relationship
2. **直接 yes** — kills team
3. **没 ask why now** — miss real driver
4. **没 decompose** — treat ask as monolithic
5. **没 written commitment** — verbal forgotten
6. **Heroics promise** — sets unsustainable
7. **Internal misalignment** with sales/eng before negotiating

---

## ✅ 加分项

1. **D·D·O·C framework** explicit
2. **"What happens on day 4"** discovery move
3. **3-option presentation** puts choice on client
4. **Smallest viable scope** + roadmap with dates
5. **Joint ownership** (ask their team to do X)
6. **Written CTO commit** for confidence
7. **Quote Indonesia refund tier scoping**
8. **Reframe vendor comparison as DD opportunity**

---

## Cheat Sheet

```
D·D·O·C:
  Deeper why (what happens day 4?)
  Decompose ask (must-have vs nice)
  Offer phased (3 options, tradeoffs)
  Commit specifically (date + written)

Standard 3 options:
  A: 1-day urgent minimum
  B: 2-week medium
  C: 6-week original

Phrases:
  - "What's driving the timeline?"
  - "Of the full scope, what's the must-have-today?"
  - "Here are 3 options with tradeoffs..."
  - "Want written commitment by EOD?"
  - "If we promise that, here's how it fails..."

Anti-patterns:
  - "Not possible"
  - "We'll try"
  - "Engineering needs to check"
  - "If we work weekends"

Internal alignment first:
  - Sales: get commitment language right
  - Eng: confirm smallest viable
  - Manager: peer-level escalation if needed

红线:
  - Promise without alignment
  - Verbal-only commitments
  - Heroics culture
```
