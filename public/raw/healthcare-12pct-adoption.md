## 题目（verbatim）

> "Healthcare client shows **12% adoption after 90 days**. **Diagnose root cause** and propose remediation."

**出处**：fde.academy 列出的 deployment scenario 经典款。Salesforce / Palantir / Google Cloud FDE 都见过。

**Round**：Case Study / Deployment Scenario (45 min)

---

## 这道题在考什么

**不是技术题** —— 是**deployment 失败诊断**题。考你能不能：

1. **不预设原因** —— "肯定是 UI 难用"、"肯定是 model 不准"都是失分。一上来就有 hypothesis = 你没见过真实部署
2. **结构化拆 funnel** —— 12% adoption 是个 aggregate metric。它在 funnel 的哪一段崩？
3. **区分 product issue vs adoption issue vs change-management issue** —— 这三种是完全不同的 fix
4. **跟 customer co-investigate** —— FDE 不是 vendor on site，是 customer's extended team

---

## 5 个 clarifying questions

**1. Define "adoption"**

> "What's the **denominator** — total employees? Specific role (nurse / doctor / admin)? Active users / month? And what counts as 'adopted' — one login, weekly use, daily use?"

**2. The baseline / target**

> "12% is bad **vs what**? Was the target 50% / 80% / 100%? Did the contract include adoption SLA?"

**3. Funnel stage breakdown**

> "Of all eligible users, what % were **provisioned access**? Of those, what % **logged in once**? Of those, what % **completed first task**? Of those, what % **used in past 7 days**?"

→ 这一个问题暴露 root cause 80% 时间。

**4. Customer's previous workflow**

> "What did clinicians use **before** us? Was it a competing product, manual paper, nothing? How disruptive is the switch?"

**5. Internal sponsor / champion**

> "Who's our **champion** at the client? Did they leave / get reassigned? Is the CMIO still personally backing this?"

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-10 min | Define adoption + ask for funnel breakdown |
| 10-20 min | Hypothesize 3-5 root causes from funnel data, **rank by likelihood + impact** |
| 20-30 min | Pick top 1-2 hypotheses, propose **investigation plan** (not solution yet) |
| 30-40 min | Based on hypothesis, propose **remediation** with phasing |
| 40-45 min | Failure modes + how to know it worked |

---

## 我会这样答（sample monologue）

> "First, let me make sure I understand 'adoption' — *[问 clarifying]*. Assume **denominator = 1000 nurses across 3 hospitals, 'adopted' = used in past 7 days, 12% = 120 nurses, target was 80%**.
>
> Before hypothesizing, I want to see the **funnel**:
>
> - Provisioned access: ?
> - Logged in at least once: ?
> - Completed first task: ?
> - Used in past 7 days: 12% (the reported number)
>
> Each drop tells different story. Let me hypothesize what I'd see in each scenario:
>
> **Hypothesis A: Provisioning failure** (only 30% provisioned)
>   → IT integration with their HR system is broken. Fix: triage with their IT team, get bulk SSO setup.
>
> **Hypothesis B: Login but no first-task** (90% provisioned, 80% logged in, 20% completed task)
>   → UX / training gap. Fix: in-app onboarding flow, 30-min coach session at each shift handoff.
>
> **Hypothesis C: First-task but not retained** (80% logged in, 60% completed task, 12% in past 7d)
>   → Our product loses to incumbent workflow. **This is the worst case** because it's product-market fit, not deployment. Fix: hard product conversation with their CMIO.
>
> **Hypothesis D: Change management failure** (any stage)
>   → Champion left / political pushback / floor manager not enforcing. Fix: re-engage executive sponsor.
>
> **Investigation plan, week 1-2**:
> 1. Pull funnel data from telemetry (1 day)
> 2. **Shadow 5 nurses for a shift** — actually see what they do (2 days). FDE 必须 to the customer site.
> 3. Interview 10 non-adopters: "Walk me through your day, when would you use this?" (3 days)
> 4. Interview 5 active adopters: "What made you stick?" (1 day)
> 5. Talk to CMIO + 2 floor managers (2 days)
>
> Output: a **1-pager** with root cause + concrete remediation.
>
> **Most likely outcome (based on FDE experience)**: it's **Hypothesis B mixed with D** — the product is OK but training was rushed + champion lost focus. That's actually **good news** because both are fixable in 60 days.
>
> **Remediation if B+D**:
> - Week 1-4: **embedded floor training** — FDE physically sits with 3 nurses per shift, 2 hospitals, rotate
> - Week 4-8: **champion re-engagement** — weekly review with CMIO showing micro-improvements
> - Week 8-12: **adoption challenge** — internal leaderboard, recognition, gamification (works in healthcare)
>
> **Target**: 40% in 90 days, 70% in 6 months. Honest, not 80% in 30 days fantasy.
>
> **How we know it worked**:
> - Funnel improves stage-by-stage (not just top number)
> - **Stickiness ratio (DAU/MAU)** grows above 0.5
> - Drop in support tickets per active user (people aren't fighting the tool)
>
> **Two risks to flag**:
> - If after 4 weeks of embedded training adoption is still flat, it's actually **Hypothesis C** (product-fit), and we have to have the hard conversation. Don't avoid it.
> - **Don't blame the customer**. Even if it's their change management, the FDE owns the joint outcome."

---

## 简历专属 reframe

你的 **voice agent 7 markets** 项目 + **BNPL chatbot adoption** 都有 deployment ramp 经验：

| Healthcare 题 | 你的经验 |
|---|---|
| Funnel diagnosis | 你跨 7 markets 不同 adoption rate，肯定 diagnose 过 |
| Embedded floor training | Voice agent 你 weekly 跟 regional ops 跑 |
| Champion management | 7 markets 每个有 regional champion |
| Product fit vs deployment fit 区分 | 你做过的 refund tier scoping 就是这个判断 |
| Stickiness ratio | BNPL chatbot 你 measure 过 |

**主动说**：

> "Actually one of my 7 markets, Indonesia, had this exact shape — initial adoption around 15% after 60 days. We did the funnel diagnostic and it turned out the issue was 70% provisioning failure (their HR feed wasn't syncing), not product fit at all. Once we fixed the SSO integration, adoption jumped to 60% in 4 weeks. The general lesson: **always diagnose the funnel first, never assume product issue**."

→ 真实经验, 巨加分.

---

## 5 个常见 follow-ups

**Q1**: "What if the CMIO says it's all our fault?"
**A**: Don't defensive. Three moves:
1. **Acknowledge**: "I hear you, you're frustrated, and we owe you a turnaround plan."
2. **Diagnose together**: "Can we spend 30 min on the funnel data? I want to make sure we're fixing the right thing, not just adding training."
3. **Joint action items**: "Of these 5 actions, 3 are on us, 2 require your team's help — can your floor managers commit to 15-min adoption huddles every shift for 4 weeks?"

Don't unilaterally promise outcomes you can't control.

**Q2**: "Active users say tool is great. Non-users won't try. How to convert?"
**A**: This is classic **diffusion of innovation** problem. Active users = your early-adopters / champions. Two levers:
1. **Champion-led conversion**: have active users do **30-min lunch sessions** for their peers. Way more credible than vendor training.
2. **Friction removal**: interview 5 non-users specifically. Often it's a single dumb thing (e.g., they have to log in twice, app is on wrong screen of their workstation). Fix that, **conversion is free**.

**Q3**: "Adoption is OK but renewal at risk because CFO says no measurable outcome."
**A**: This is **business case re-anchoring**. The CFO sees cost but no value. 2-step:
1. **Find existing internal metric you can move** — e.g., "we noticed your charting time decreased 18% for active users. At $80/hr × 3000 nurses, that's $X/year."
2. **Convert to language CFO uses** — they don't care about adoption, they care about cost-per-encounter, FTE-hours-saved, readmission-rate.

You can't make a CFO care about adoption. You can make them care about adoption's economic equivalent.

**Q4**: "Hypothesis C is the case (product-market fit). What now?"
**A**: Have the **honest conversation up the chain at our side first**:
- If the product is wrong for healthcare nursing, escalate to product leadership: "We need workflow X added or we won't win healthcare. Roadmap commitment?"
- Don't promise client we'll fix in 60 days when product team can't ship in 12 months.
- Worst case: **negotiate a graceful exit / scope reduction** — only serve admin staff (where adoption is fine), not bedside nurses. Save the relationship.

**Q5**: "Customer wants you to interview EVERY nurse to find the issue. Time impossible."
**A**: 推回去得 surgical：
- "I can talk to 15 non-users in 5 days. That's statistically meaningful and 80% of the signal."
- Offer **survey for the rest**: 5-question 2-min survey, target 200 responses.
- Don't waste 6 weeks on 1000 interviews.

---

## ❌ 易错点

1. **预设 root cause** — 一上来"肯定是 UI 难用" = 失分
2. **跳过 funnel** — adoption 是 aggregate, funnel 才是 actionable
3. **当 "training problem"** — 用 training 解决一切是 cop-out
4. **不区分 product 和 deployment 问题** — 这是 FDE 是否成熟的关键判断
5. **不去 customer site** — FDE 必须 on-site shadow
6. **承诺数字** — 80% 30 天不可能
7. **甩锅给 customer** — 即使是他们的 change mgmt, FDE 拥有 joint outcome

---

## ✅ 加分项

1. **Funnel-based diagnosis** 主动列出 4 个 hypothesis 对应每段 funnel
2. **On-site shadow + 15 interviews** 具体行动
3. **Stickiness ratio (DAU/MAU)** 作为 leading indicator
4. **CFO-language re-anchoring** 应对 renewal 风险
5. **Champion-led peer training** > vendor training
6. **诚实区分 hypothesis C** (product fit) 不回避
7. **Joint action items** 让 customer 也有 commitment

---

## Cheat Sheet

```
绝不预设根因, 永远先看 funnel:
  Provisioned → Login → First-task → Past 7d active
  
4 hypothesis 对应 4 段 drop:
  A: Provisioning broken (IT)
  B: UX / training gap
  C: Product-market fit (worst)
  D: Change management / champion loss

Investigation tools:
  - Funnel telemetry
  - On-site shadow 5 users
  - 10 non-user interviews
  - 5 adopter interviews
  - CMIO + manager talks

Remediation if B+D (most common):
  Wk 1-4: embedded floor training
  Wk 4-8: champion re-engagement
  Wk 8-12: gamified rollout
  Target: 40% in 90d, 70% in 6mo

Success metrics:
  - Funnel improves stage-by-stage
  - Stickiness (DAU/MAU) > 0.5
  - Support tickets / active user ↓

红线:
  - Don't blame customer
  - Don't promise unilateral
  - Don't avoid Hypothesis C if data shows it
```
