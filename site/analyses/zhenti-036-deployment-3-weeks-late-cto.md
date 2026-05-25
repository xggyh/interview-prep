## Q36 · 告诉客户 CTO 部署延期 3 周

> "You're on a live video call with the customer's **CTO**. The deployment is **3 weeks behind schedule**. Tell him."

**Round**: Client Simulation (30 min)
**出处**: Exponent 2026 FDE · OpenAI / Palantir / Anthropic 高频
**场景**: 客户 CTO 一对一. 你在 1 分钟内要说完 cause + impact + new date + mitigation, 然后接 5 分钟 grilling.

---

## 📖 术语速查 (本题用到的)

> Client Sim 题 = **communication + ownership + 政治术语**. 5 min 速查.

### 沟通 / 谈判核心

| 术语 | 解释 |
|---|---|
| **Ownership language** ⭐ | 主动归责的语言 — "I" / "we" / "I should have flagged earlier" 替代 "the team" / "engineering said". 把延期归到自己, 不是别人. |
| **Blame language** | 推卸语言 — "Engineering said X" / "The team didn't tell me" / "The customer's slow". CTO 一听就 lose trust. |
| **Frame the call** | 开场定调 — "I'll be direct" / "I called specifically to deliver bad news". 让对方知道接下来是 hard news. |
| **Headline first / Bury the lead** ⭐ | 先讲核心结论, 再讲 context. "We're slipping 3 weeks. New target [date]." 然后才讲原因. 反过来 = bury the lead = 失分. |
| **Hard news delivery** | 坏消息传递技巧 — 直接 + 结构化 + own it. CTO/VP 这级别人**讨厌委婉**, 喜欢 specific. |
| **Push back / Disagree-and-commit** | 推回 / 反对但执行 — 你可以反对 CTO 的某个 framing, 但用 evidence 不情绪. |
| **Emotional regulation** | 情绪管理 — 对方激动你不能跟着激动. 沉默 + 听 > 反驳. |
| **Don't over-promise** ⭐ | 不要超额承诺 — "I'll fix it this weekend" / "We'll add 5 extra features to make up" = dig your own hole. **超额承诺 = 下次再 miss**. |
| **Promise the process, not the outcome** ⭐ | 承诺流程不承诺结果 — "I'll have written answer by Wednesday" 而非 "you'll get credit". 你不能控制结果, 但能控制流程. |
| **Specific vs vague** | 具体 vs 模糊 — "June 15th" 不是 "soon". "80% confident" 不是 "pretty confident". |
| **Confidence level (置信度)** | 给具体百分比 — "80% confident in June 15. Remaining risk is X". 量化你的不确定性. |
| **Behavioral commitment / Behavioral change** | 行为承诺 — 不是道歉, 是 "我以后这样做": "anything that risks >5 business day slip, I call you within 24 hours". |
| **Escalation path** ⭐ | 升级路径 — 客户要找你 director 或更高级别. **不要 fight escalation**, 主动配合: "I'll text her in 30 seconds". |
| **Hand mic to them** | 把话筒给对方 — 讲完你的 3 min headline 后**闭嘴**, 听对方反应. 大多数候选人继续讲 = 输. |

### 角色 / 头衔

| 术语 | 解释 |
|---|---|
| **CTO (Chief Technology Officer)** ⭐ | 首席技术官 — 客户技术决策最高人. 这题对方. 技术人, 直接 + 结构化沟通最有效. |
| **Director / VP** | 你公司里的中层 / 高层 — escalation 可能涉及. |
| **AE (Account Executive)** | 客户大客户经理 — 这题里负责商业 + 合同的人 (credit 谈判 owner). |
| **CEO** | 客户 CEO — 如果 CTO 要升级到他这级别, 你要 prep 不同的话术. |
| **GM (General Manager)** | 业务负责人 — Gao Xin 简历里 Indonesia GM 是这种角色. |

### 项目 / 部署术语

| 术语 | 解释 |
|---|---|
| **Soft-launch vs Hard-launch** ⭐ | 软发布 vs 硬发布 — Soft = 内部 / 受限用户先用 (ramp-up); Hard = 全量 / 对外发布 (board commit 通常对此). **这题里 soft-launch 滑了 3 周, hard-launch 不动**. |
| **Slip (滑期)** | 项目延期. "3-week slip". |
| **ETA (Estimated Time of Arrival)** | 预计完成时间. |
| **Board commit** | 向董事会承诺 — CTO 的 board commit 是这题敏感点. |
| **Phased rollout / Phased launch** | 分批上线 — 不全量发, 先 20% 用户, 再 ramp 到 100%. 这题 fallback 选项. |
| **Scope reduction** | 减小范围 — 不要全功能上, 砍掉 [feature B] 先上 [feature A]. |
| **Internal milestone vs External commit** | 内部里程碑 vs 对外承诺 — 这题关键 framing: 把 soft-launch 表述为 internal 不让 board 看到. |

### 流程 / 工具

| 术语 | 解释 |
|---|---|
| **Daily standup** | 每日站会 — "I'm the new daily owner of [bottleneck]" 是 mitigation. |
| **Daily 5-line status update** | 每日 5 行状态更新 — 这题具体的 behavioral commitment. |
| **Hard internal checkpoint** | 硬性内部检查点 — "if not on-track by June 1st, I'll call you that afternoon". 自我设的 trigger. |
| **Post-mortem** | 事后复盘 — 出问题后系统性总结. 这题没明说但隐含. |
| **Cc list** | 抄送列表 — 你的 daily status 抄给谁是 CTO 决定. |

### 客户具体场景

| 术语 | 解释 |
|---|---|
| **Snowflake cluster** | Snowflake 云数仓 — 这题集成对象, 出权限问题. |
| **Data governance committee** | 数据治理委员会 — 客户内部审批组织, biweekly meeting 是 bottleneck. |
| **Inference latency** | 推理延迟 — LLM 部署的关键性能指标. 这题超 spec 3x. |
| **Prompt strategy / Routing model** | 提示策略 / 路由模型 — mitigation 提到的技术手段, 用小模型先 route 减少大模型调用. |

### Gao Xin 简历相关

| 术语 | 解释 |
|---|---|
| **OJK (Otoritas Jasa Keuangan)** | 印尼金融监管局 — Gao Xin 的 Indonesia 项目监管. 类比这题的 governance committee. |
| **BNPL (Buy Now Pay Later)** | 先买后付 — TikTok PayLater 产品类别. |

---

## 这道题在考什么

**不是**: 考你能不能找借口.

**是**: 考 **ownership language**、**clear hard news delivery**、**emotional regulation under pushback**, 以及**避免 6 个具体反面 trap**.

具体看 5 个 signal:

1. **Open with the bad news in 60 seconds** — Mealy-mouthed opening = lose CTO immediately. CTO 是技术人, 直接 + 结构化 > 委婉
2. **Ownership language not blame language** — "I" / "we" 不是 "the team" / "engineering said". 把延期归到自己
3. **Specific new date with confidence level** — 不是 "soon" 或 "ASAP". 具体日期 + 你为啥相信
4. **Mitigation already in motion** — "starting today we are doing X" 不是 "we'll figure it out"
5. **Don't over-promise to make the news softer** — "we'll make it up by adding 5 features" = dig your own hole

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 该说什么 | 开口句 (literal) |
|---|---|---|---|---|
| 1 | **Frame the call** | 0:00 - 0:15 | "I want to be direct because your time is valuable" | "Mark, I'll be direct. I called specifically to deliver bad news." |
| 2 | **Headline** | 0:15 - 0:30 | New ETA + magnitude | "We're slipping the deployment by 3 weeks. New target is [date]." |
| 3 | **Cause (one breath)** | 0:30 - 1:00 | What blocked, no blame | "Two reasons. First, [tech issue]. Second, [integration issue]. I should have flagged earlier." |
| 4 | **Impact** | 1:00 - 1:30 | What it means for them | "This impacts your [Q3 launch / board commit / X user team] in these specific ways..." |
| 5 | **Mitigation in motion** | 1:30 - 2:30 | Already-started actions | "Starting today: (a) X, (b) Y, (c) Z. Specifically I will [personal commit]." |
| 6 | **Confidence in new date** | 2:30 - 3:00 | Why this date holds | "I'm 80% confident in [date]. The risk to that is [Z]. Here's the dependency..." |
| 7 | **Their decision points** | 3:00 - 3:30 | What you need from them | "Two things I need from you: (a) ..., (b) ..." |
| 8 | **Hand mic to them** | 3:30 + | Stop talking, let them react | "What's your reaction? What questions?" |
| 9 | **Listen + take notes** | 3:30 - 8:00 | Don't defend, just take it | (Silent + notes) |
| 10 | **Confirm follow-up** | 8:00 - 10:00 | Specific deliverables, dates | "By Friday, I'll send: [doc]. Next call: [date]. Sound good?" |

**Total**: < 3 min talking up front. Rest is them. **The shorter your opener, the more respect you signal**.

---

## 30-second 开场脚本 (Verbatim)

> "Mark, I'll be direct because I know your time is valuable. I called specifically to deliver bad news.
>
> **We're slipping the deployment by 3 weeks. New target is June 15th, was May 25th.**
>
> Two reasons. First, the data integration with your **Snowflake cluster ran into a permissions issue** that took us 9 business days to resolve — we hit it 2 weeks in, your team and ours were aligned on root cause within 48 hours but **the actual unblock required your data governance committee's approval** which has biweekly meetings. Second, we discovered the **inference latency was 3x our spec** on your particular query mix and we rebuilt the prompt strategy and added a smaller routing model — that took another 6 business days.
>
> **The impact on your Q3 product launch**: 3 weeks slips your soft-launch from May 30th to June 22nd. Your hard-launch on July 15th is still on track. I want to be honest — **the soft-launch slip is real and I won't pretend it's minor**.
>
> **What's in motion starting today**:
>
> 1. **I am the new daily standup driver** with your data governance team, no more biweekly bottleneck. We've already gotten verbal yes for an expedited approval session this Friday.
>
> 2. We added one senior engineer (Sarah, our infra lead) on for the next 3 weeks dedicated to your account. Started yesterday.
>
> 3. **I'm sending you a written daily 5-line status update** every 4pm Pacific until launch, so you don't have to ask.
>
> **I'm 80% confident in June 15th.** The remaining risk is your data governance approval — if Friday doesn't yield, that's another 2 weeks. I'll flag day-of either way.
>
> **Two things I need from you**:
>
> 1. **Friday's data governance session** — your sponsor needs to push for our slot. Can you make a call this afternoon?
>
> 2. If we need to escalate within your org, who's the right name?
>
> What's your reaction? What questions do you have? I'd rather hear them now than later."

→ **3 minutes flat**. Then shut up.

---

## 完整对话流 (15-min back-and-forth simulation)

> **Customer (CTO Mark)**: "So basically you missed your commit. Why should I trust the new date?"

> **You**: "Fair question. Two things changed in our process: **(a) I'm now the single owner of escalations to your data governance team — that's the path that lost us the most time, and I won't delegate it again, (b) we added a senior engineer with margin in her quarter.** Plus I'm setting a hard internal checkpoint: if we're not on-track by **June 1st** for the **inference quality eval**, I'll call you and propose a phased launch — not pretend we'll catch up. **You won't be surprised again.**"

---

> **Mark**: "This affects my board commit. They've been told end of Q2."

> **You**: "I hear you, and I want to address the board commit specifically.
>
> **The hard-launch on July 15 is still on track.** That's the date you committed to the board, if I understand correctly. **The soft-launch with internal users is the date that slips** — and that's used for ramp-up before hard-launch.
>
> **What I'd propose**: I'll send you a 1-pager you can adapt for the board update. **Two framings**:
>
> **Option A** (preferred by me): board sees only the hard-launch date. Soft-launch is internal milestone. **They never knew about it. No change to board commit.**
>
> **Option B**: If you've already shared soft-launch with the board, here's my proposed update: 'Soft-launch internally moves from May 30 → June 22. Hard-launch July 15 unchanged. Reason: integration with our data governance.'
>
> Which framing fits how you've set expectations with them?"

→ Notice you're helping him manage HIS political situation, not yours.

---

> **Mark**: "I shouldn't be hearing about this 3 weeks late. Why didn't you flag this when the permissions issue came up?"

> **You**: "**You're right and I'm not going to dodge that.**
>
> The truth is: when we hit the permissions issue 2 weeks in, my read was 'we'll resolve in a few days, it's not worth alarming Mark'. **That read was wrong.** When it became clear it needed governance committee approval, **I should have called you that day**. I waited 4 more business days hoping we'd find a workaround.
>
> **What I'm changing**: the 5-line daily status starting today is partly so you have early signals. **Plus an explicit rule: anything that risks >5 business days slip, I call you within 24 hours.** That's the standard I'm holding myself to.
>
> I won't make excuses for the late notification — that was a judgment error on my part. **I want to earn back the trust.**"

→ Don't dodge. Don't defend. **Own** + **commit to a behavioral change with a measurable threshold**.

---

> **Mark**: "How do I know your team isn't oversold? Maybe you took on too much."

> **You**: "Honest answer: we may have been optimistic on the data integration timeline. We assumed your governance committee approval would be 3-5 days based on a comparable engagement with a peer — it ended up being 9 days because the committee's schedule didn't align. **That was my misread, not your team's slowness.**
>
> **In terms of capacity**: my own team is 4 engineers + me on this account. The senior engineer we added isn't borrowed from elsewhere — she had bench time in her quarter and your account is now her top priority through July. **We are not short on people. We are short on a clean integration path with your governance, and that's solved by me owning escalations.**
>
> If after the next 2 weeks you don't see daily progress, **you should escalate to my director (cc'd on the daily) — and I'll support that, not block it.**"

---

> **Mark**: "Are we paying for the 3 weeks? My CFO will ask."

> **You**: "**Good question, and I want to handle this transparently.**
>
> **My commit**: I won't ship a commercial proposal here, but I'm going to recommend to my account team that **we credit the 3 weeks of professional services time** since that's where the slip is. **You'll have something in writing by Wednesday** with my AE's name attached.
>
> If my recommendation isn't approved internally, I'll come back and tell you that directly, and we'll figure out an alternative. **I'm not promising you a credit before I check, but I'm promising you a written answer by Wednesday.**"

→ Don't make commercial commitments you can't keep. **Promise the process**, not the outcome.

---

> **Mark**: "And what if the June 15 date slips too?"

> **You**: "**I will tell you on June 1st, not June 14th.** The June 1st checkpoint is the inference-quality eval — if that's not on track, I call you that afternoon and we discuss options.
>
> **The options if June 15 looks at risk**:
>
> 1. **Phased launch**: ship to 20% of users on June 15, ramp to 100% by June 22. **Reduces risk, gives data team time to absorb feedback before full rollout**.
>
> 2. **Delay to June 22 with full launch**: cleaner, but loses the 7-day ramp.
>
> 3. **Reduce scope**: launch with [specific feature subset], add [other feature] in July. **Requires us to agree what's truly v1**.
>
> **I will not unilaterally pick.** I'll bring the data and the options on June 1st and we decide together. **No surprises.**"

---

> **Mark**: "OK. What do you need from me right now?"

> **You**: "**Three things**:
>
> 1. **Friday's data governance session** — please make a call to your sponsor today. Even a 2-line note works: 'I want this on the agenda Friday'.
>
> 2. **Cc list for daily status**: who else on your team should be on the 5-line daily? I default to you only, but if there's a deputy or PM you want looped in, let me know.
>
> 3. **The escalation contact** — if I need to go above the data governance committee, who do I go to? I want to know in advance so I don't fumble it under pressure.
>
> I'll send you those daily emails starting today at 4pm Pacific. Friday's session, I'll let you know how it went by 5pm Friday. **Anything else you need from me right now?**"

> **Mark**: "No, that's it. Let's see how Friday goes."

> **You**: "Thank you. **And Mark — I appreciate you not letting me off the hook on the late notification. I'd rather have this conversation than the comfortable version of it.** Talk Friday."

→ Close with: acknowledge them being a good customer + show you appreciated honest pushback. Don't grovel.

---

## Gao Xin 简历专属 reframe

> "I had this exact conversation with our Indonesia voice agent rollout. We were 4 weeks behind our committed soft-launch because of:
> - **OJK regulatory clarification** that we hadn't anticipated would take 2 cycles of submission (3 weeks)
> - **One particular dialog edge case** that kept failing for a high-volume customer segment (1 week)
>
> The decision: tell the **Indonesia GM and the regional product VP** in a Friday afternoon meeting. **I owned that delivery.**
>
> What I learned and would apply directly here:
>
> 1. **Don't dilute the headline with context first**. I led with: 'We're 4 weeks behind. New date is [X]. I want to walk you through cause + mitigation + what I need from you.' Three sentences. Then context.
>
> 2. **Own the late notification specifically**. I'd known about the OJK timing risk for 2 weeks before telling them, hoping we'd find a workaround. The GM called me on that — 'why didn't you call when you first suspected it?' Same trap as this scenario. **I won't repeat that mistake.**
>
> 3. **Help them manage THEIR political situation**. The GM's concern wasn't the slip per se — it was that he'd told the regional VP about the soft-launch. I drafted a 1-paragraph note he could send to the VP. **That's where I added value beyond just delivering bad news.**
>
> 4. **Don't over-promise to make the bad news softer**. I almost said 'I'll personally code the dialog edge case fix this weekend'. Caught myself. **That commitment would have created another miss.** Instead: 'I'll have the dedicated dialog engineer pair with one of your team's lead. We'll have a working solution in 5 business days, not a 2-day commitment I can't keep.'
>
> 5. **End with appreciation, not grovel**. The GM had been respectful even when frustrated. I closed: 'I appreciate you holding this conversation directly with me, not escalating around me. I'll earn that.'
>
> The pattern that transfers: **CTO/GM/VP-tier respects directness + ownership + behavioral commitments more than apology + reassurance.**"

**Other resume hooks**:

- **BNPL chatbot CTO escalation** — when our chatbot's intent classifier degraded for one customer segment, I had a similar conversation with their CTO. Same template worked.
- **ConvFinQA stakeholder presentations** — when ablation showed a negative result, framing 'this is what we learned' vs 'this is bad news' was a craft I practiced.

---

## 5 个 Follow-ups

**Q1**: "What if Mark wants to bring his CEO into the next call?"

**A**: Treat it as their org's decision, not a punishment.

> "Of course. Two things:
>
> **(a)** I want to make sure my director is on that call too — so it's CEO-to-Director-level, not asymmetric.
>
> **(b)** Can you tell me what specific outcome your CEO is looking for from the call? If it's 'see we're serious', we'll come with the daily status + the mitigation actions. If it's 'see commercial accommodation', we'll bring my AE. Different prep.
>
> I'll align with my director by EOD today on the call format. **When works for the CEO?**"

Don't get defensive. CEOs being on calls is normal escalation.

**Q2**: "What if Mark says 'forget the new date, just cancel the project'?"

**A**: Don't take it personally. Diagnose first.

> "I hear you, and that's your call. **Before you make it, can I ask one thing**: is the cancellation about (a) the slip itself, (b) loss of confidence in my team specifically, (c) my company more broadly, or (d) the business case changed?
>
> Because each of those has a different path forward. If it's (a), I want a chance to recover. If it's (b) or (c), I'd rather have an honest exit conversation. If it's (d), let's talk about what the project should be instead.
>
> **No pressure to answer today**. I'd rather you take a week with your team and come back. **Want to schedule for next Friday?**"

Show you respect their decision. Cancellation is their right.

**Q3**: "What if Mark gets emotional or aggressive on the call?"

**A**: Match calmness. Don't match emotion.

- **Don't argue back** when frustration is being vented
- **Take notes** while they talk — visible to them (helps them feel heard)
- **Don't say "I understand"** — say "I hear you" or summarize what they said
- **If they swear or insult you personally**: don't say anything immediate. Wait. If continues, "Mark, I'm hearing you're frustrated. I'd rather we have this call when we can be specific about next steps. Can we resume in an hour?"
- **After the call**: send a short follow-up confirming what you agreed. **No editorial about the emotional moment.**

The CTO who got emotional usually appreciates you didn't escalate it.

**Q4**: "What if Mark says 'you're not the right person, give me your director'?"

**A**: Don't take offense. Help him.

> "That's reasonable, and I'd rather you have direct access to my director than us pretend everything's fine. **Let me text her right now**.
>
> **One ask**: can I be on that call too? Not to defend, but so I can hear what you say to her directly — that way I learn what to do differently and can execute on whatever she commits.
>
> I'll text her in 30 seconds. **What time works in the next 48 hours?**"

Don't fight the escalation. Make it efficient.

**Q5**: "What if the 3-week slip is actually because YOUR company de-prioritized this account for a bigger customer?"

**A**: Honesty is the only play. **Don't lie to the customer about resourcing.**

> "Honestly — yes, that's part of what happened. **Two weeks ago, my company committed to an emergency engagement with another customer, and we lost 1.5 engineers from your team for 8 business days.** I should have called you when that resource decision was made internally — that was a judgment failure on my part.
>
> **What I changed**: the senior engineer we added (Sarah) is in writing as your dedicated until July 15. **She can't be borrowed without explicit re-discussion with you.** I've cc'd my director on the email establishing that.
>
> I won't pretend the resource shift didn't happen. **I will commit to you that it won't happen again on this engagement without your explicit yes.**"

→ Lying about this 100% explodes when CTO finds out. Better to admit + show what changed.

---

## ❌ 死路答法 (top 7)

1. **"The team is working hard"** — passive, no ownership
2. **"Engineering said..."** — blame the team, not yourself
3. **"It's been a tough sprint"** — emotional, not informative
4. **"We'll catch up by..."** with unspecified plan — make-belief
5. **Open with apology before headline** — buries the lead
6. **Promise extra features to soften slip** — dig deeper hole
7. **Lie about resourcing** — explodes when discovered

---

## ✅ 加分项 (top 7)

1. **Headline in 30 seconds**: new date + cause + impact + mitigation + need-from-you
2. **80% confidence stated explicitly** with named risk
3. **"I should have called you sooner"** without prompt
4. **5-line daily email** as concrete behavioral change
5. **Help them with THEIR political situation** (board commit framing)
6. **Promise process not outcome** on commercial (no fake credit commit)
7. **Close with appreciation for their directness**

---

## 一句话总结

> **延期通知 CTO = "60-second headline + ownership language + specific new date with confidence + mitigation in motion + 'what I need from you' + shut up + listen"**.
>
> 真正的 win 不是把延期讲得不像延期, 是让 CTO 觉得**"this person owns the situation and I get clean information from them"**. 长期 trust > 这次延期感受.

---

## Cheat Sheet

```
不要说:
  - "The team is working hard"
  - "Engineering said..."
  - "It's been tough"
  - "We'll catch up"
  - "I'm so sorry" before headline
  - "We'll throw in extra features"
  - "Don't worry"

要说:
  - "I'll be direct"
  - "We're slipping 3 weeks. New target [date]."
  - "Two reasons. First [X]. Second [Y]."
  - "I should have flagged earlier"
  - "Starting today: [action 1], [action 2]"
  - "I'm 80% confident in [date]"
  - "What I need from you: [Q]"

10-layer response:
  1. Frame call (0:00-0:15) "I'll be direct"
  2. Headline (0:15-0:30) new date
  3. Cause (0:30-1:00) one breath
  4. Impact (1:00-1:30) for them specifically
  5. Mitigation (1:30-2:30) already in motion
  6. Confidence (2:30-3:00) 80% + named risk
  7. Their decision (3:00-3:30) what you need
  8. Hand mic (3:30+) stop talking
  9. Listen + notes (3:30-8:00) no defense
  10. Confirm follow-up (8:00-10:00) specific

Total time talking: < 3 min upfront

Headline structure:
  "Slipping X weeks. New target [date]. Two reasons.
   Impact on your [thing]. Mitigation in motion.
   I'm [N]% confident. Need [thing] from you."

Mitigation actions to mention:
  - "I'm the new daily owner of [the bottleneck]"
  - "Added [specific named engineer], dedicated"
  - "5-line daily email at 4pm Pacific"
  - "Hard internal checkpoint [date] — if at risk, I call you that day"
  - "Phased rollout option as fallback"

Confidence quantification:
  "80% confident in June 15. Remaining risk is X.
   If Friday doesn't yield, that's another 2 weeks
   and I'll flag day-of."

When asked "why so late to flag":
  - "You're right and I won't dodge"
  - "I waited hoping we'd find workaround. Judgment error."
  - "New rule: >5 business day slip = call you within 24 hours"

When asked about money:
  - "Promise the process, not outcome"
  - "I'll recommend credit, written answer Wednesday"
  - "If not approved, I'll tell you that directly"

When CTO escalates to your director:
  - "I'd rather you have direct access than us pretend"
  - Don't fight escalation
  - Ask to be on call (learn, don't defend)

When CTO threatens cancellation:
  - "Take a week with your team, come back"
  - Diagnose (slip / team / company / business case)
  - Respect the decision

When CTO emotional:
  - Don't match emotion
  - Take visible notes
  - "I hear you" not "I understand"
  - If insulting: "let's resume in an hour"

When asked about resourcing shift:
  - Don't lie
  - Admit + show what changed
  - "Sarah is dedicated until July 15 in writing, cc'd director"

Resume quote:
  "Indonesia voice agent 4-week slip:
   - OJK timing + dialog edge case
   - Owned delivery to GM
   - Helped him manage VP politically
   - 5-line daily until launch
   - Pattern: CTO respects directness + ownership"

Close line:
  "Mark, I appreciate you not letting me off the hook
   on the late notification. I'd rather have this
   conversation than the comfortable version. Talk Friday."
```
