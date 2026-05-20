## 题目（verbatim）

> "Deployed fix fails; the **same problem recurs**; client is **losing confidence** in your team. How do you communicate, what do you change in your process?"

**出处**：fde.academy 客户模拟. Palantir / OpenAI / Salesforce 都问. 真实 deployment 最难的 moment 之一.

**Round**：Client Simulation (45 min)

---

## 这道题在考什么

你能不能 **professionally own a streak of failures**：

1. **Stop digging the hole** —— 别再 promise quick fix
2. **Process-level admission** —— 不是"this bug specific", 是"我们的诊断方法有问题"
3. **Bring in fresh eyes** —— 你已经 stuck in same hypothesis
4. **Compensation** —— offer something they didn't ask for
5. **Plan to rebuild trust** —— rebuild trust is **months**, not 1 fix

---

## 黄金 framework：A·R·R·R

| Step | What | Why |
|---|---|---|
| **A** | **Admit process-level fault** | "Our diagnosis wasn't deep enough" — not blaming bug |
| **R** | **Reset approach** | "I'm bringing in [senior eng / new lead / pair-debug with your team]" |
| **R** | **Reduce blast radius** | "While we fix, here's what we're doing to prevent customer impact" |
| **R** | **Re-earn over time** | "Trust gets rebuilt by N weeks of stability, not by next sprint's deliverable" |

---

## Sample script

> *[Client (CTO): "This is the 3rd time. I'm seriously considering canceling. What's your team doing?"]*
>
> "I hear you. **You're right to be frustrated** — and your reaction is justified. I'm not going to argue or list mitigations until I address what really matters here.
>
> **Three things I want to commit to right now:**
>
> **1. Process change, not 'we'll try harder':**
> Our previous fixes treated this as a 'specific bug to patch'. The pattern of recurrence tells me **our diagnostic approach is wrong**, not just our code. So I'm changing how we approach this entirely.
>
> Specifically:
> - I'm bringing in our principal engineer [name] who hasn't been touching this code — fresh eyes
> - We're spending 1 week on **just root cause analysis, no patches** — I'm explicitly not promising a fix in the next sprint
> - We'll pair-debug with your team — your engineer sits with mine. You see what we're trying.
>
> **2. Reduce blast radius immediately:**
> We're not waiting for the fix. Within 24h, I'll have a **feature flag system** so we can disable the problem code path on your environment without taking down the whole feature. If issue recurs, we kill the path within minutes, not hours.
>
> **3. Earn trust back — not by promises, by stability:**
> I'm not going to tell you 'this fix will work for sure'. I've said that twice already, you don't believe me, and you shouldn't. What I will tell you:
> - **30 days of stability** before I claim it's fixed
> - **Daily 10-min syncs for first 2 weeks** so you have visibility
> - **A post-mortem write-up** for past failures shared with you, internal-grade, not sanitized
>
> **One ask back:** I know you're considering canceling. **Would you give us 30 days under this plan** before deciding? If we miss any milestone, the cancellation is your call without penalty discussions.
>
> What I'm offering is **work and accountability, not excuses**. Is that something you can accept?"

⏱️ 5-7 min. Then listen to their response carefully.

---

## 简历专属 reframe

你的 **ConvFinQA 9-variant ablation** + **Indonesia voice agent debugging** :

| 题 | 你做过 |
|---|---|
| Recurring fix doesn't work | ConvFinQA — 8 个 variant 都失败, 你 honestly reported negative result |
| Process-level admission | ConvFinQA 你写了 "all 8 variants regressed, here's why" 不 hide |
| Fresh eyes / bring in others | Voice agent 跨 7 markets — 每个市场带 fresh perspective |
| Feature flag for blast radius | Voice agent multi-market gradual rollout |
| Daily syncs + post-mortem | 你做过 |

**主动说**：

> "Funnily this exact shape happened in my ConvFinQA work. I tried 9 variants of agent improvements. The first 3 made it worse. I had a choice: keep patching, or admit 'my hypothesis is wrong, let me try something fundamentally different'. I picked admission, documented the negative result openly. **Customers in this situation prefer honest reset over the 4th 'this time will work'**. So I'd offer them the equivalent: a fresh-eyes RCA week, no patches, and let them watch us think."

→ 真实 honest 经验, FDE 级别 signal.

---

## 5 follow-ups

**Q1**: "Client refuses 30-day grace. Wants exit clause activated."
**A**: 别 fight contract. Move to relationship preservation:
- "I respect that decision. Before any contract action, can I propose: **2-week reset**, no charges during that period, you get the post-mortem + fix attempt. If still bad on day 14, you decide."
- This buys time + shows good faith. Most CTOs say yes to "free 2 weeks".

**Q2**: "Senior engineer you bring in finds it's a deeper architectural issue. 6-month fix."
**A**: This is where most FDE fail — they hide. Don't:
- "We've identified the root issue. It's a **6-month architectural change** to truly fix. Here are 3 paths: (1) workaround that buys you 6 months at known limitations, (2) commit to the rewrite jointly, (3) we de-scope the affected feature."
- Let customer choose. They might pick #3 — that's fine, **graceful degradation > 6 more months of denial**.

**Q3**: "Customer's CFO involved now, talking about damages."
**A**: 上 lawyer 之前一定 try:
- Escalate to your CEO + your account manager
- Joint call with their CFO + your CEO
- Offer **specific service credits / discount** (e.g., 3 months free) as good-faith
- Don't unilaterally promise damages — but **acknowledge real cost** to their business
- Document everything from this point forward

**Q4**: "Your manager wants you to spin the situation 'we've made great progress'."
**A**: Disagree internally:
- "If we tell them 'great progress' and the next fix fails, we lose the customer permanently."
- "Honest reset is more likely to save the relationship than spin."
- If manager insists, **escalate to senior leadership** — this is a career-defining choice for you. Spin and you become part of the failure pattern.

**Q5**: "How long does trust take to rebuild?"
**A**: Realistic: **3-6 months of stability** before customer's trust returns. Specifically:
- 30 days zero incidents on the previous bug class
- 60 days delivery of committed features on time
- 90 days no surprise — proactive comms on potential issues
- 6 months — relationship moves from "watching us fail" to "trusting us by default"

**Don't promise faster recovery**. People rebuild trust slower than they lose it.

---

## ❌ 易错点

1. **"This time we got it"** — credibility-burning
2. **Argue or defend** when customer is frustrated
3. **No process-level admission** — treating it as bug-specific
4. **No blast radius reduction** — fix is sole strategy
5. **Spin progress** — disaster long-term
6. **Promise rapid trust rebuild** — 30-day trust = lie
7. **Hide deeper architectural issue** if discovered

---

## ✅ 加分项

1. **A·R·R·R** process-level framework
2. **Fresh principal engineer** to break stuck thinking
3. **Pair-debug with customer's team** — radical transparency
4. **Feature flag for blast radius** immediate mitigation
5. **30-day grace period offer** before contract action
6. **Daily syncs first 2 weeks** for visibility
7. **Honest 6-month timeline** if architectural
8. **Service credits** as good-faith
9. **Quote ConvFinQA negative result honesty**

---

## Cheat Sheet

```
A·R·R·R:
  Admit process-level fault (not just bug)
  Reset approach (fresh eyes, RCA week, pair-debug)
  Reduce blast radius (feature flag, kill switch)
  Re-earn over time (30/60/90 day stability)

Phrases:
  - "You're right to be frustrated"
  - "Our diagnostic approach was wrong, not just our code"
  - "I'm bringing in fresh eyes"
  - "30 days of stability before I claim it's fixed"
  - "Daily 10-min syncs first 2 weeks"
  - "Pair-debug with your team"
  - "Service credit / 3 months free"

What customers want:
  - Honest reset > 4th "this will work"
  - Visibility into our thinking
  - Reduced blast radius FIRST
  - Time to evaluate (30 days)
  - Don't argue

What kills relationship:
  - Spin / "great progress" message
  - Another quick-fix promise
  - Hide deeper issue
  - Argue when frustrated
  - Internal misalignment in front of them
```
