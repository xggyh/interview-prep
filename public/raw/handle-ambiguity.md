## 题目（verbatim）

> **[OpenAI Hiring Manager Round]**
>
> "How do you **handle ambiguity**? Tell me a story where requirements were unclear and you had to make calls without complete information."

**出处**：OpenAI / Google FDE hiring manager 必问. Palantir/Salesforce 也问.

**Round**：Hiring Manager (60 min)

---

## 这道题在考什么

FDE 工作 90% 时间在 ambiguity 里:

1. **Process** —— 有 framework 处理还是 panic
2. **Decision-making** —— 在不完整信息下 commit
3. **Reversibility awareness** —— 知道 one-way vs two-way doors
4. **Communication** —— 用 stakeholder 验证 vs 自己 silo
5. **Story quality** —— STAR + 具体 metrics

---

## 黄金 framework：D·D·D·V

| Step | What |
|---|---|
| **D** | **Diagnose ambiguity type** (info-missing vs decision-required vs unknown-unknown) |
| **D** | **Decompose** into known + unknown + assumption |
| **D** | **Decide** by reversibility (one-way: slow + investigate; two-way: ship + measure) |
| **V** | **Validate** with stakeholder + ship + learn |

---

## 你专属 STAR story（用 Indonesia refund tier）

**Situation**:
> "On the voice agent project, the Indonesia regional ops team asked us to **automate refund decisions** — agent could approve or deny refunds without a human. The ask came as a Friday Slack message: 'we want full automation by next quarter, can you do it?'
>
> There was huge ambiguity: what kinds of refunds, what amount limits, who's accountable for wrong calls, what's the cost of a wrong call, what does 'next quarter' mean."

**Task**:
> "I had to either commit to a timeline I couldn't actually verify, or push back without scope information, or **find a way to commit conditionally** with information learned along the way."

**Action**:
> "I did 3 things:
>
> **1. Diagnose** the ambiguity. This was 'decision-required without enough info' — not 'unknown unknown'. The right move was **structured discovery, not pause**.
>
> **2. Decompose**: I broke 'automate refunds' into 3 tiers:
> - Tier 1: info lookup (look up policy, balance — agent says read-only facts)
> - Tier 2: structured tasks (calculate fees, look up case status)
> - Tier 3: refund decisions (approve / deny — the real ask)
>
> Each tier has different **risk profile** and **decision reversibility**.
>
> **3. Decide by reversibility**:
> - Tier 1: **two-way door** (wrong info bot says easy to correct, low cost). Ship in 2 weeks, measure.
> - Tier 2: **mostly two-way** (some financial calc, but human reviews). Ship in 4 weeks.
> - Tier 3: **one-way door** (wrong refund = direct financial loss, customer trust impact, regulatory). Need 12+ weeks investigation before committing.
>
> **4. Validate**: I went back to ops team with 'here are 3 things I can commit to and timelines, here's why tier 3 needs more time'. They initially pushed for full tier 3 in 8 weeks. **I ran a 2-week pilot showing tier 1 + 2 covered 70% of volume at 0% wrong-call rate, vs full automation projected at 8% wrong-call rate**.
>
> Data made the call obvious. We shipped tier 1+2 first."

**Result**:
> "Ops got 70% of throughput at 0% risk in 6 weeks. Tier 3 came online 6 months later **after we had policy + monitoring + human-in-loop infrastructure**. **Zero wrong refunds in production for tier 3 in first 90 days**.
>
> What I learned: **scope ambiguity is rarely about timeline — it's about the asker not having decomposed the problem yet**. When you decompose for them with reversibility analysis, they often realize their own ask was too broad. Then they thank you."

⏱️ ~3 min spoken. HM can ask deep follow-ups for another 10 min.

---

## 5 个 "what to NOT say"

❌ "I just ship and iterate" → no thoughtfulness, scares hiring manager
❌ "I align with my manager and ask them to decide" → no judgment
❌ "I do a lot of research first" → if literal, can mean analysis paralysis
❌ "It depends" without follow-through → wishy-washy
❌ Generic story without metrics → not memorable

---

## 5 个 "do say" formulas

✅ **"I diagnose what kind of ambiguity it is"** → process signal
✅ **"I decompose into known / unknown / assumption"** → clarity
✅ **"For reversible decisions, I ship fast and measure"** → bias to action
✅ **"For irreversible decisions, I invest in investigation"** → judgment
✅ **"I validate with the stakeholder before final commit"** → collaboration

---

## 简历专属 reframe

Indonesia refund tier story 是 **黄金叙事** for this question. 但你可以扩展：

| Question variant | Best story |
|---|---|
| "Handle ambiguity" | Indonesia refund tier (decompose + reversibility) |
| "Make decision without info" | Voice agent multi-region rollout (phased + measured) |
| "Push back on stakeholder" | Same — refund tier |
| "Bias to action vs caution" | ConvFinQA — bias to ship, measured, found negative result, **published it honestly** |

---

## 5 follow-ups (recruiter / HM 会追问)

**Q1**: "What if your decomposition is wrong — turn out tier 3 actually fine to automate quickly?"
**A**: "Then I learn and reshape. The 2-week pilot was specifically designed to **stress-test my assumption**. If pilot showed 0% wrong-call on tier 3 difficult cases, I'd accelerate. **Decomposition is a hypothesis, not a commandment** — the eval is the truth."

**Q2**: "What if the ops team got angry at the pushback?"
**A**: "They were initially frustrated — 'we asked for 8 weeks, why 12 weeks for tier 3'. The reframe that worked: **'I want to give you the right answer faster, not the wrong answer on time'**. Showed them the cost-of-wrong-call analysis (estimated 8% wrong rate × $X per refund = $Y monthly liability). Numbers diffused the emotional ask."

**Q3**: "How do you know when 'decompose more' becomes procrastination?"
**A**: "Pragmatic rule: **decomposition that takes longer than 10% of the implementation timeline is over-decomposition**. For a 12-week project, > 1 week of scoping is procrastination. **At some point, ship a small piece and learn from data**. I'd rather over-decompose by 1 day than under-ship for 4 weeks."

**Q4**: "Have you ever made a wrong call under ambiguity?"
**A**: Have a real one ready:
> "Yes. On the voice agent, I initially scoped the multi-region rollout as 'translate prompts per language, ship'. Turns out **debt-collection cultural norms differ wildly** — what's polite in Thailand is rude in Korea. We had to redo the persona + escalation logic per market. **Cost: 4 extra weeks**. **Lesson: 'localization' for AI means more than translation; I now scope cultural review as part of multi-market projects**."

**Q5**: "How do you balance speed and quality under ambiguity?"
**A**: "By **reversibility classification**: two-way doors → speed. One-way doors → quality. I explicitly tag every decision when scoping. **Most decisions are two-way and can be reversed cheaply** — over-optimizing for quality on those is waste."

---

## ❌ 易错点

1. **No structured framework** — just narrative
2. **Pure speed/pure caution** — no nuance
3. **Story without metrics** (70% / 0% / 6 weeks)
4. **Blame stakeholder** for ambiguity
5. **Solo decision** without stakeholder validation
6. **Generic story** — sounds rehearsed
7. **Doesn't tie to what FDE does** (deployment ambiguity)

---

## ✅ 加分项

1. **D·D·D·V framework** explicit
2. **Reversibility classification** (one-way vs two-way doors)
3. **"Decomposition is hypothesis" awareness**
4. **Specific metrics in story** (70% / 0% / 8 weeks)
5. **Acknowledge wrong call you made** in follow-up
6. **Tie to FDE day-to-day** (customer deployment ambiguity is universal)
7. **Quote business-language framing** ("right answer faster vs wrong answer on time")

---

## Cheat Sheet

```
D·D·D·V framework:
  Diagnose ambiguity type
  Decompose into known / unknown / assumption
  Decide by reversibility (one-way slow, two-way fast)
  Validate with stakeholder

Reversibility classifier:
  Two-way doors → ship + measure (most decisions)
  One-way doors → investigate first
  ID at scoping time, not after

Indonesia refund tier story:
  S: ops wants auto refund "next quarter"
  T: scope + timeline conflict
  A: 3-tier decomposition by reversibility,
     pilot 2 weeks, data-driven reframe
  R: 70% throughput, 0% risk, 6 weeks

Phrases:
  "I diagnose what kind of ambiguity"
  "Reversibility classification"
  "Two-way doors → ship + measure"
  "Decomposition is hypothesis"
  "Right answer faster, not wrong on time"

Anti-patterns:
  "I just ship"
  "I ask manager"
  "I research first"
  "It depends" without follow-up
  No metrics
```
