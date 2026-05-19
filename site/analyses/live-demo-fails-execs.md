## 题目（verbatim）

> "Your **live demo fails** in front of the client's executive team. What do you communicate, **in what order**, and how do you recover the deployment timeline?"

**出处**：fde.academy 客户模拟经典. Palantir / Salesforce / OpenAI 都问.

**Round**：Client Simulation / Role-play (45 min)

---

## 这道题在考什么

**不**考你 "怎么 fix the bug"。考**沟通顺序 + 心态稳定 + business 思维**：

1. **Acknowledge before explaining** —— 不要立刻 jump to "let me explain why this happened"
2. **Buy time without sounding evasive**
3. **Reframe the meeting** —— 把 demo-failure 转成 "live debugging value-demo"
4. **Save the deal**, not your ego
5. **Follow-up commitment 实在**

---

## 黄金 framework：A·D·O·R

| Step | Stand for | What you say |
|---|---|---|
| **A** | **Acknowledge** | "OK, the demo is hitting an issue. I appreciate you all making time for this — let me handle it directly." |
| **D** | **Diagnose live (or fake diagnose)** | "Looks like [hypothesis]. Let me try [action]." If it doesn't work in 2 min, move on. |
| **O** | **Offer alternative** | "Rather than debug live and burn your time, let me [walk you through the working flow on staging / show the recent data we generated / share the slide explanation of what would have happened]." |
| **R** | **Recommit** | "I'll have a 1-page incident report by EOD tomorrow + a re-demo invitation. Does Thursday 10am work?" |

整套大约 **3-5 分钟**, 然后转 meeting agenda。

---

## 4 个 critical "do not say"

❌ **"This works fine in our demo environment."** → blames customer's environment, sounds defensive
❌ **"This is a known issue we're going to fix."** → admit ongoing bug, executives lose confidence
❌ **"Let me debug this real quick."** + 15min silence → kills the room
❌ **"Engineering will look into it."** → punt to absent party, makes you look like middleman not owner

---

## 4 个 critical "do say"

✅ **"I'm going to handle this directly. Give me 2 minutes."** → ownership
✅ **"Rather than burn your time on the debugging, let me show you [working scenario]"** → time-respect + still convey value
✅ **"This is exactly the kind of failure mode we'd want to catch in pre-deploy testing — let me walk you through how we'd build that monitoring."** → turn the failure into a feature demo
✅ **"Here's my commitment: 1-pager by EOD tomorrow, re-demo Thursday."** → concrete next step

---

## Sample script (full role play)

> *[Demo screen freezes / returns error]*
>
> "Looks like the demo is hitting an issue. Let me handle that directly — give me 2 minutes to check what's going on."
>
> *[20 seconds of looking at terminal, trying obvious fix]*
>
> "OK, I see what it is — looks like the integration with your test environment is throwing a permission error. **This is fixable on our side**, but I don't want to burn your meeting time debugging in front of you.
>
> **What I'd like to do instead**: I have a screen recording from yesterday's working demo on the same data shape. Let me share it — *[2 min recording]* — then we walk through the questions you came with, and I take an action item to get the live environment fixed by tomorrow.
>
> *[After the recording]*
>
> Actually, this issue here is a useful conversation. **One of the things you'll want from us is exactly this kind of failure detection in production** — we want to demonstrate not just that the system works, but how it fails. So let me also share the **observability layer we'd build** so issues like this surface in seconds, not in customer demos.
>
> *[Spend 10 min on observability — substantive value]*
>
> **My commitments**:
> 1. Root cause + fix by EOD tomorrow (I'll send 1-page incident analysis)
> 2. Re-demo on the same scenarios Thursday 10am — does that work for everyone's calendar?
> 3. We'll add the failure-detection monitoring I just described to the rollout plan
>
> Sorry again for the timing. What other questions do you have?"

⏱️ 3 min from failure → recovered agenda.

---

## 简历专属 reframe

你的 **voice agent 7 markets** 一定经历过 live failure：

- **A**: "I appreciate you all making time — let me handle this directly"
- **D**: 你已经在 prod debug 7 markets 多次, 知道哪些 hypothesis fastest to验证
- **O**: 你的 Voice agent 有 staging 录屏 (production deployment 标配)
- **R**: 你的 RCA writeup quality + re-demo 频率你做过

**主动说**：

> "I've actually been on this side of a failed demo. We were demoing the voice agent to the Indonesia regulatory body, the model started outputting English mid-call because a Thai prompt config leaked into the Indonesia model checkpoint. I did exactly the **acknowledge → buy 2 min → switch to recorded showcase → commit RCA by EOD** flow. We re-demoed 48h later with the fix + a new observability layer that would have caught the leak. **They actually signed faster** after that — they saw we handle failure professionally. The demo failure became a sales asset."

→ 这是 STAFF/FDE level signal。

---

## 5 个 follow-ups

**Q1**: "What if you genuinely don't know what's wrong?"
**A**: Don't lie. Say: "I have 2-3 hypotheses I'd need to verify. Rather than guess in front of you, let me commit to a 1-pager by EOD tomorrow with root cause and fix timeline." Customers respect honesty more than fake competence.

**Q2**: "Customer's CEO is annoyed and pressing for explanation."
**A**: Don't argue back. **Lower their stress first**:
- "I hear you. This shouldn't have happened in front of you. I'm going to own it."
- "What I can commit to right now: detailed incident report by EOD tomorrow, dedicated re-demo within 5 days. Anything else you need from me in the next 24h?"
- **Send a follow-up email 30 min after the meeting** with written commitments. Reduces "did they really say that?" doubt.

**Q3**: "Customer wants to cancel the contract on the spot."
**A**: 
- "I hear that. I'd be frustrated too. Before we discuss contract action, can I propose: I'll fix the issue by tomorrow, run a re-demo by Friday at no cost, and we revisit your decision then?"
- Get **time + concrete deliverables** before they pull the trigger. People rarely cancel after they get a clean follow-up.

**Q4**: "Your manager joins the call and contradicts you mid-recovery."
**A**:
- Don't contradict back in front of customer. Politely sync: "Let me clarify — I was committing to EOD tomorrow for the incident report. Maybe we can align after the call on the broader timeline."
- After the call: **explicit alignment with manager** about who owns customer commitment.
- Never let customer see internal disagreement during incident — confidence erosion.

**Q5**: "Re-demo also fails."
**A**: Worst case. 3 moves:
- **Don't re-demo a 3rd time without confidence**. Move to async: "let me record + share, you provide feedback, we iterate without burning your time"
- **Engage their technical lead 1:1**: have them in our staging env, debug together — converts adversary to ally
- **Escalate at our side**: this customer relationship is in jeopardy. CEO/CRO involvement needed.

---

## ❌ 易错点

1. **Long silence while debugging** — kills the room
2. **Blame infrastructure / customer environment** — defensive
3. **Punt to engineering** — looks like middleman
4. **Promise speedy fix without checking** — sets up second failure
5. **Don't write follow-up email** — let memory drift
6. **Defensive body language** — pacing, sighing, looking away
7. **Re-demo too soon** — same risk

---

## ✅ 加分项

1. **A·D·O·R framework** in real time
2. **Turn failure into feature demo** (observability layer)
3. **Written commitments** within 30 min of meeting
4. **Specific re-demo date** (not "next week")
5. **Quote a real prior experience** — Indonesia voice agent
6. **Pre-emptive internal alignment** if manager joins
7. **Move to async** if re-demo fails

---

## Cheat Sheet

```
A·D·O·R:
  A - Acknowledge ownership immediately
  D - Diagnose live (cap at 2 min)
  O - Offer alternative value (recorded demo / observability talk)
  R - Recommit specific date

Time budget:
  0-30s: acknowledge
  30s-2m: try diagnose live
  2m-3m: pivot to alternative
  3m-end: substantive content + agenda
  +30 min after: follow-up email

DO say:
  "Give me 2 minutes"
  "Rather than burn your time"
  "This failure mode is exactly what we'd monitor for"
  "1-pager by EOD tomorrow"

DON'T say:
  "Works in our env"
  "Known issue"
  "Engineering will look"
  "Real quick"

Severity escalation:
  Failed re-demo → async sharing
  Customer threatens cancel → buy time + commitments
  CEO angry → don't defend, ower
  Manager contradicts → resync after, never publicly
```
