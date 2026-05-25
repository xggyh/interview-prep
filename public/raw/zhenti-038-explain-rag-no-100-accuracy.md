## Q38 · 向非技术 VP 解释为什么 RAG 系统无法保证 100% 准确

> "You're meeting with the customer's **VP of Customer Operations** (non-technical, ex-MBA, never coded). They want a guarantee that the **RAG-powered AI assistant will be 100% accurate** before they roll it out to their 2,000-person support team. Explain why **no AI system can give that guarantee**, without losing the deal."

**Round**: Client Simulation (30 min)
**出处**: Exponent 2026 FDE · OpenAI Enterprise / Anthropic enterprise sales · 每次 GenAI 企业级部署必踩
**场景**: VP wants 100% guarantee. You can't give it. You must redirect without rejection.

---

## 📖 术语速查 (本题用到的)

> 这题最大坑: **non-技术 VP** 听不懂术语. 表里**前 4 节是你可以说的, 第 5 节是你绝不能说的**.

### 沟通 / 解释技巧

| 术语 | 解释 |
|---|---|
| **Reframe (重新定义问题)** ⭐ | 不直接回答 "100% 能不能", 重塑问题为 "right standard for your use case is what?". 这题核心动作. |
| **Business analogy** ⭐ | 业务类比 — 用 VP 已经懂的概念解释技术. "Citation = agent 说 'per policy 4.2'", "Confidence = junior agent 不确定时 escalate". |
| **Anchor to current baseline** | 锚定当前基线 — "你的人工 team 现在多准? 88-92%". 让 VP 意识到她对比的不是 100% 而是当前. |
| **Variance vs human baseline** | LLM 变异 vs 人变异 — 关键 framing. 人也不是 100%. |
| **Help them sell upward** ⭐ | 帮对方向上推销 — 给 VP 一个**给 CEO 的 3 句话 script** + 1-pager. 不只是说服 VP, 是 arm her. |
| **CEO-script (3 sentences)** | 给 CEO 的 3 句话: (1) 比现在好 4-10x, (2) 每个答案有 citation + audit + escalation, (3) 1 小时可 rollback. |
| **Phased rollout proposal** | 阶段性上线提议 — 200 agents 先, 30 天 eval, 再全量. 给对方控制感. |
| **Name worst case honestly** | 诚实说最差情况 — "前 30 天预期 3-5 个 incident". 比 hand-wave reassurance 更可信. |
| **Don't patronize** | 不要 condescending — VP 是聪明人, 只是不懂技术. 用类比, 不用 baby talk. |
| **"Right question to ask"** | 开场认可对方问题 — "you're asking the right question before rollout". 验证 VP 的关切. |

### AI / 系统术语 (你可以解释, 但不直接用)

| 术语 | 解释 |
|---|---|
| **RAG (Retrieval-Augmented Generation)** ⭐ | 检索增强生成 — LLM 先检索文档再答, 是这题的系统类型. **不要直接说 "RAG"**, 说 "the system reasons rather than retrieves" 或 "it cites the source". |
| **Citation** ⭐ | 引用 — 每个答案附带源文档. 类比: "agent says 'per policy 4.2'". 4 guards 之一. |
| **Confidence score / Calibration** ⭐ | 置信度 / 校准 — AI 报告自己多确定. 类比: "junior agent 不确定时 escalate". |
| **Eval / Evaluation set** | 评估集 — 5000 题已知答案的测试. 每周跑, 监控 drift. 类比: "每周客户满意度调查, 但是给 AI". |
| **Audit log** | 审计日志 — 每个 AI 答案 + 引用 + confidence 记录. 类比: "call recording for legal review". |
| **Escalation** | 升级 — confidence 低就转人工. 类比: junior agent 转 senior. |
| **Hallucination** | 幻觉 — AI 编造源文档没的事实. **不直接说**, 说 "wrong answer". |
| **Drift** | 漂移 — 准确率随时间下滑 (新问题 / 新文档). |
| **Retroactive correction** | 事后纠正 — 找到错答后联系客户 + credit + 喂回系统. |
| **Rollback (回滚)** | 1 小时内禁用 AI 回到人工. Reversibility 关键卖点. |

### 业务 / 客服行业

| 术语 | 解释 |
|---|---|
| **VP of Customer Operations** ⭐ | 客户运营副总 — 这题对方. 非技术 (ex-MBA), 有 budget authority. |
| **First-response accuracy** | 首次响应准确率 — 客服行业标准指标. 行业 baseline 85-92%. |
| **Support team / Support agent** | 客服团队 — 这题 2000 人. |
| **Ticket** | 客服工单 — 这题 2000 tickets / day. |
| **Escalation rate** | 升级率 — 多少 case 转人工. |
| **NPS (Net Promoter Score)** | 净推荐值 — 客户满意度核心指标. |
| **LTV (Lifetime Value)** | 客户终生价值 — 算 wrong answer cost 时用. |
| **Churn** | 客户流失. |
| **QA (Quality Assurance)** | 质量审核 — 客户中心通常已经 QA 5% calls. 类比 AI eval. |
| **Incident response / Incident playbook** | 事件响应流程 — 客户投诉怎么处理. AI 套用同一 playbook + 多一步 audit log review. |
| **Override rate** | 覆盖率 — agent 推翻 AI 推荐的比例. 早期高, 后期降. 是 trust 指标. |

### 数据 / ML 概念 (非术语表达)

| 术语 | 解释 |
|---|---|
| **Fine-tuning** | 微调 — 用客户数据再训练 model. **不直接说**, 说 "tailored to your data". |
| **Re-ranker** | 重排序 — 提升 retrieval 质量的二阶段. **不直接说**. |
| **2-model consensus** | 两模型共识 — 高精度要求时用. **可以用**, 类比 second opinion. |
| **SLA (Service Level Agreement)** | 服务等级协议 — uptime 99.9%, 不是 accuracy 100%. |
| **Doc freshness** | 文档新鲜度 — 检测过期文档. 类比 "policy doc updated when". |

### 禁词清单 ❌ (不要在 VP 前说)

| 术语 | 为啥不能说 |
|---|---|
| **Embedding** | VP 听不懂, 听到就 tune out. |
| **Vector** | 同上. |
| **Chunking** | 同上. |
| **Temperature / Top-p** | 同上. |
| **Stochastic / Deterministic** | 听起来像炫技. |
| **Token** | 太底层. |
| **Context window** | 太底层. |
| **"Model"** (单用) | 太抽象, 说 "the system" 或 "the AI". |

### Gao Xin 简历相关

| 术语 | 解释 |
|---|---|
| **OJK** | 印尼金融监管 — Gao Xin 给 OJK 做过类似 "reframe + analogy + 帮 GM 上推" 的 methodology doc, 6 周 pre-approved. |
| **ConvFinQA negative-result ablation** | 用消融实验测准确率, 不 hand-wave. 这题精神. |

---

## 这道题在考什么

**不是**: 考你能否 explain RAG technically.

**是**: 考你能否在 30 分钟内**重塑 VP 的 mental model**, 让她从 "I want 100% accuracy" 走到 "I want measured accuracy + guards I can defend to my CEO". 加上避免 condescension.

5 个 signal:

1. **No tech jargon** — "embedding", "vector", "chunking", "temperature" — banned
2. **Analogies from VP's world** — call center, customer service, escalation processes
3. **Show what you DO offer** — citation, confidence, eval, escalation. Not just "we can't guarantee"
4. **Reframe variance as feature** — human agents aren't 100% either. Variance vs human baseline matters.
5. **Don't patronize** — VP is smart, just not in this domain. Concrete numbers + business analogies, not baby talk

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 该说什么 | 开口句 (literal) |
|---|---|---|---|---|
| 1 | **Validate the question** | 0:00 - 0:30 | "Smart to ask before rollout" | "Janet — you're asking the right question. Before we roll this out to 2000 people, we need a real answer." |
| 2 | **Reframe the question** | 0:30 - 2:00 | From "100%" to "right standard" | "Let me reframe — '100% accurate' isn't a standard that exists for ANY decision system. Let me show you what is." |
| 3 | **Business analogy** | 2:00 - 5:00 | Call center current state | "Your current support team — what's their first-response accuracy?" *(usually 85-92%)* |
| 4 | **What we do offer** | 5:00 - 12:00 | Citation + confidence + escalation | "Here are 4 specific guards we ship..." |
| 5 | **Variance vs human baseline** | 12:00 - 17:00 | LLM 95-99%, human 85-92% | "Your current team is 85-92%. Our system is 95-99% with eval. Net: you're better off." |
| 6 | **Show the worst case** | 17:00 - 21:00 | What if the 1% wrong slips through | "Here's what happens when wrong answer slips: escalation, audit log, retroactive correction." |
| 7 | **Defensible to her CEO** | 21:00 - 25:00 | Help her sell it upward | "Here's how you frame this for your CEO: 'we measured X, guards Y, escalation Z'." |
| 8 | **Final ask + commit** | 25:00 - 30:00 | Approval to ship + specific eval | "Specifically I'd recommend: ship to 200 agents for 30 days, eval shows X, then full rollout." |

---

## 30-second 开场脚本 (Verbatim)

> "Janet — you're asking the right question, and I want to give you a real answer.
>
> Here's what I'm going to do in our 30 minutes: I'm going to **reframe what '100% accurate' means**, because the truth is **no decision system in your business is 100%** — not your support team, not your underwriters, not even your billing system. So we need to find the **right standard for your use case**.
>
> Then I'll show you **what we actually guarantee**, the **specific numbers we've measured for your data**, **what happens when the system is wrong** (because it will be, just like your humans are), and **how you frame this for your CEO** when she asks.
>
> Sound good? Walk me through what success looks like to you on day 30 of rollout."

→ Note: you don't say "we can't guarantee 100%" up front. You **reframe the question**.

---

## 完整对话流 (15-min back-and-forth)

> **VP Janet**: "Look, my CEO told me 'no AI mistakes touching customers'. If even 1% of answers are wrong, that's 20 customers a day getting misinformation."

> **You**: "I hear that. And **20 customers a day getting wrong information is a real number** — let's make sure we're not creating that.
>
> But let me ask: **what's your current accuracy rate?**
>
> Your support team today, handling those 2000 tickets a day. Of those, what % give the customer **exactly correct information**? Not 'helpful' — but actually correct, factually, with policy citation?
>
> *(Listen. Most VPs say 'I'd guess 90%')*
>
> So **roughly 200 customers a day** get information from your support team that's not factually perfect. Not because your agents are bad — because **call centers run at 85-92% first-response accuracy in our industry data**. That's the baseline.
>
> **What we ship runs at 95-99% on the queries we measured for your data**. So you'd actually go from 200 wrong answers a day to **20-100 wrong answers a day**. That's a 50-90% improvement over your current state.
>
> **The frame your CEO probably wants** isn't '100% accuracy' — it's '**measurably better than today + a way to catch the mistakes we do make**'. Want me to show you the guards we have?"

→ The reframe: **your current state isn't 100% either**. LLM vs **realistic human baseline**, not LLM vs **fantasy 100% baseline**.

---

> **Janet**: "OK, I never thought about it that way. So how do you catch the mistakes?"

> **You**: "**Four layers of guards**. Let me walk through them with an analogy.
>
> **Layer 1 — Citation**. Every answer the AI gives **cites the source document** it pulled from. Just like a good support agent would say 'according to policy 4.2, here's the answer'. The customer-facing agent sees the citation and can verify before sending.
>
> Think of it like: when you ask **your assistant** a question, you want her to say 'I checked the policy doc, page 47, and here's what it says'. **Not 'I'm pretty sure'**. Our system does that automatically.
>
> **Layer 2 — Confidence**. The AI **reports how confident it is**. If it's 95%+ confident, your agent can send the answer with light review. If it's 70-95%, the agent should verify before sending. **Below 70%, it doesn't even surface the answer** — agent goes to human escalation.
>
> Think of it like: **a junior agent who has self-awareness**. Junior says 'I'm sure about this one, ship it' vs 'I'm not sure, let me ask a senior'. Our system has that self-awareness built in.
>
> **Layer 3 — Eval set**. We **constantly test the system** against a set of 5000 sample customer questions that we know the correct answers to. **Every week we re-run and report**. If accuracy drops below your agreed threshold, we get alerted and fix.
>
> Think of it like: **a monthly customer-satisfaction survey**, but for AI accuracy specifically, and weekly not monthly.
>
> **Layer 4 — Audit log + retroactive review**. **Every single AI answer is logged** with the question, the citation, the confidence, the agent who used it. If a wrong answer slips through, **your team can find it later, correct the customer, and we feed that back into the system**.
>
> Think of it like: **call recording for legal review**. You have a record, you can find issues, you can fix the system.
>
> **Combined**: citation makes wrong answers obvious, confidence routes uncertain cases to humans, eval catches systemic drift, audit log catches what slipped through. **No single guarantee — but a system of layered guards**, exactly like how your current support quality process works."

---

> **Janet**: "What if even with all that, a customer gets bad info and goes to social media?"

> **You**: "That's a real scenario, and it happens with **human support teams too**. The question is: **what's your incident response process?**
>
> Today, when a customer goes to social media with a wrong answer from a human agent, you have a playbook: **escalate, customer-care direct contact, retroactive credit if needed, training for the agent**. Right?
>
> Our system fits into that same playbook with one extra step: **the AI's response is logged with citation**. So when investigating, you can see exactly:
>
> - **What the AI said**
> - **What document it pulled from**
> - **What the agent reviewed before sending**
> - **The confidence score at the time**
>
> Often this makes resolution **faster** than human-only support, because you have the full trace. With human-only, you have a vague 'agent said X' and have to dig.
>
> **My recommendation for your incident response**: add one new step — '**if AI was involved, pull the audit log first, see if it was a content issue, confidence issue, or agent override issue**'. Then you know if it's an isolated event or a systemic one.
>
> **Want me to draft the playbook update for you?**"

→ Show you've thought about THEIR operations, not just the tech.

---

> **Janet**: "What's the worst case scenario you've seen?"

> **You**: "Honest answer: I've seen 3 categories of issues in deployments I've shipped.
>
> **Category 1 — The simple miss**: AI gave a policy answer that was correct in the doc but the doc was outdated. The fix: **doc freshness pipeline + 'this answer is from doc last updated X days ago' shown to agent**. Caught in 24 hours.
>
> **Category 2 — The confidence miscalibration**: AI was 95% confident on a question where the right answer required cross-referencing 2 policies. **Fix: better retrieval + 'multi-document answers required confidence threshold higher'**. Caught in a week.
>
> **Category 3 — The novel question**: customer asked something the AI had no good data for. **Fix: confidence threshold + escalation worked, AI didn't give answer, escalated to human. No customer impact.**
>
> Worst case I've seen turn into a real customer-facing problem: about **5 cases per million queries** before our guards caught it. After guards: **less than 1 per million**.
>
> Your current human-only support — **5 per million** is probably better than your current baseline, but I want to be honest: it's not zero. **If your CEO needs absolute zero, no system gives that. But layered guards reduce it to a level where your incident response handles each case.**"

→ Honest specificity beats vague reassurance. Don't hide the worst case.

---

> **Janet**: "How do I justify this to my CEO?"

> **You**: "**Here's the script I'd give her**, and you can adapt:
>
> *'We evaluated the AI system across [3000 historical questions from our support corpus]. It achieved [97%] accuracy with [4] independent layers of guards: citation showing source, confidence routing, weekly eval, audit log review. Our current human team operates at [88%] accuracy on the same questions. We're rolling out to [200] agents first for [30 days], measuring [these 5 KPIs], with weekly reviews. If the eval shows degradation, we have [rollback in 1 hour]. Full rollout depends on phase-1 results.'*
>
> **Three things this CEO-script does**:
>
> 1. **It gives her concrete numbers** (97%, 88%, 200, 30, 5)
> 2. **It shows phased deployment**, not big bang
> 3. **It shows rollback capability**, so if anything goes wrong, you control the situation
>
> **What CEO will actually want to ask** (anticipate her questions):
>
> - *'What happens to the 3% wrong?'* → 'Audit log + retroactive customer correction + system improvement'
> - *'How do you know it won't get worse over time?'* → 'Weekly eval + alerting if drops below threshold'
> - *'Can we turn it off in an emergency?'* → 'Yes, in 1 hour, no agent retraining needed'
>
> **I'll send you a 1-pager with this framing by Monday.** You can edit and send to your CEO. **Want me to do that?**"

→ Help VP sell internally. Don't just deliver to them, **arm them**.

---

> **Janet**: "Yes, send the 1-pager. Anything else I need to know?"

> **You**: "**Two things to flag honestly**:
>
> **(a) The first 30 days will have surprises**. Even with strong eval, real production traffic surfaces edge cases we didn't anticipate. **Expect 3-5 incidents in the first month that we'll need to learn from**. Plan for it, don't be surprised by it.
>
> **(b) Your agents will be skeptical at first**. They'll feel watched, they'll override the AI even when AI is right, override rate will be high in week 1. **That's healthy** — but by week 4, override should drop as they trust it. We track that.
>
> **What I need from you**:
>
> 1. **Phase-1 sign-off**: roll to 200 agents on [date], measure for 30 days
> 2. **Incident escalation contact**: who do we reach in 30 minutes if something goes wrong?
> 3. **Eval threshold approval**: I'll send you my recommended threshold (e.g., 'accuracy never drops below 94% / week'), you approve or modify
>
> **By Monday**: 1-pager for your CEO. **By Friday**: phase-1 launch plan with the 5 KPIs. **30 days from launch**: eval review.
>
> **Sound good?**"

> **Janet**: "Yeah. Thank you for not just saying 'AI is fine'."

> **You**: "I appreciate you not letting me get away with that. **Your job is to protect customers; mine is to ship something you can defend. That's the goal.**"

---

## Gao Xin 简历专属 reframe

> "I had this exact conversation with Indonesia OJK + TikTok PayLater compliance team. They wanted **'guarantee no AI errors will impact customers'**.
>
> What worked:
>
> 1. **I led with their current baseline**. Indonesia call center had **8-15% inconsistency** across agents — same customer + different agent = different decision sometimes. Once OJK saw their baseline, the LLM at 1% was clearly improvement.
>
> 2. **I explained guards as analogies they already understood**:
>    - **Citation** = our agents already cite policy when explaining a decision
>    - **Confidence** = junior agents already escalate when unsure
>    - **Eval** = QA team already audits 5% of calls
>    - **Audit log** = call recording for dispute resolution
>    These were already their processes. AI just systematizes them.
>
> 3. **I helped them sell upward to regulator**. OJK was the 'CEO' of this conversation. I drafted a 2-page methodology doc the GM took to OJK that framed: 'Existing human variance baseline 8-15%, AI achieves 1% with 4 measured guards, weekly eval, audit-log + retroactive correction in 24 hours'. **OJK pre-approved in 6 weeks**.
>
> 4. **I named worst-case scenarios honestly**. I told the GM: 'In the first 30 days, expect 3-5 incidents where AI was wrong. Here's the plan for each.' That **transparency** earned more credibility than reassurance would.
>
> 5. **I didn't use jargon**. No 'temperature' or 'top-p' or 'context window'. **'The system reasons rather than retrieves' was as technical as I got.** Even with a sophisticated regulator.
>
> The pattern that transfers: **'100% accuracy' isn't a real standard for any decision system. The right standard is 'measurably better than current + measured + guarded + reversible'. Frame the conversation that way, not 'we can't promise 100%'.**"

**Other resume hooks**:

- **ConvFinQA negative-result ablation** — when communicating LLM accuracy to non-ML stakeholders, the framing of 'measured agreement rate' translates. ConvFinQA is exactly this — measured accuracy with named tradeoffs, vs hand-wave reassurance.
- **Internal Agent Platform onboarding multiple teams** — every onboarding had this 'how do I know it won't break' moment.

---

## 5 个 Follow-ups

**Q1**: "What if Janet says 'OK if you can't give 100%, what about 99.99%?'"

**A**: Treat as good-faith engagement, not pushback. Specifics matter.

> "99.99% is **better than the system can deliver out of the box**. Here's what I can commit to:
>
> Based on our eval on your data, **97% baseline**. With targeted improvements over 3 months, I can commit to **98%** with monitoring. **99% requires investing in domain-specific fine-tuning** which we can scope if you want.
>
> **99.99% means 1 wrong per 10,000 queries**. To get there I'd need: (a) a fine-tuned model on your data, (b) a re-ranker, (c) consensus from 2 independent models. **Cost goes up 5x. Latency goes up 3x.**
>
> **Is 99.99% the actual business requirement, or 'feel safer'?** If the former, here's the cost. If the latter, **'97% with strong guards' might be better trade-off**. Let's quantify your team's bandwidth to handle escalations — that's the constraint."

**Q2**: "What if she asks 'what's the cost of a wrong answer'?"

**A**: Help her think through it.

> "Good question. Three categories:
>
> **(a) Cost of customer churn**: if a customer gets wrong info and leaves, you lose [LTV $X]. Multiplied by error rate × % who churn from a wrong answer (typically 5-20%).
>
> **(b) Cost of escalation handling**: when a wrong answer becomes a complaint, your team handles it. [Cost per complaint $Y] × error rate × % that escalate (typically 30-50%).
>
> **(c) Cost of brand / press**: rare but high-cost (social media incident).
>
> For your business: at 2000 tickets/day, 3% error = 60 wrongs/day. Let's say 20% escalate = 12 escalations/day. **Cost?** That should drive your accuracy investment.
>
> Compare to **today's manual support**: 88% accuracy on same questions = **240 wrongs/day**. So AI even at 97% is **4x improvement on absolute error count**. The math usually favors AI."

**Q3**: "What if she asks 'have you ever had a deployment go badly wrong'?"

**A**: Be honest. Don't pretend you've never failed.

> "Yes. In one customer deployment 18 months ago, **we had a bias in retrieval where the AI consistently pulled an outdated FAQ entry**. For 3 days, ~50 customers got wrong info before we caught it via eval. **Fix took 2 weeks** (re-indexed corpus + added doc-freshness signal).
>
> **What we changed afterward**:
>
> - **Doc freshness in eval**: every doc has an updated-date check
> - **Stricter alert threshold**: catch within 12 hours of accuracy drop
> - **Better escalation playbook**: customer-care direct contact procedure
>
> **Customer didn't churn**. We did retroactive customer outreach + credit. Project continued, has been clean since.
>
> Why I share this: **deployments WILL have issues**. The question is how fast you catch them. **Plan for 1-2 incidents in your first 6 months, with each one resolved < 24 hours.** That's the realistic baseline."

**Q4**: "What if Janet says 'OK, but my CEO is non-technical too. How do I explain this?'"

**A**: Already partially covered above. Add:

> "The CEO-tier conversation is shorter than ours. Three sentences:
>
> 1. **'AI is better than our current support team by 4-10x on accuracy.'** (number quantified)
> 2. **'Every answer is cited, audited, and escalable.'** (guards)
> 3. **'We can roll back in 1 hour if anything goes wrong.'** (reversibility)
>
> Most CEOs need exactly these 3 sentences. They don't want to know HOW the system works. They want to know **how to defend the decision** if challenged.
>
> The 1-pager I'm sending you Monday is designed for that — 1 page, 3 sections, no jargon. **Email forwardable.**"

**Q5**: "What if she asks 'why doesn't OpenAI or your competitor offer a 100% accuracy guarantee?'"

**A**: Honest market context.

> "Honest answer: **no vendor offers it because it's not possible**. Any vendor who promises 100% is either:
>
> - Defining 'accuracy' so narrowly it's meaningless ('we never crash')
> - Going to walk back the promise when issues arise
> - Going to put crippling guards in place that make the system unusable
>
> **What real vendors offer**: SLA on **availability** (99.9% uptime), **measured accuracy on your data** (specific number, weekly review), **rollback within X hours**, **incident response within Y minutes**.
>
> If a competitor verbally promises 100% accuracy, **ask for it in writing**. They won't sign it. That's the test.
>
> Our differentiation isn't 'we promise more'. It's '**we measure honestly + we have stronger guards + we partner on the deployment**'. The vendor who's transparent about limitations is the one you can trust in 18 months."

---

## ❌ 死路答法 (top 7)

1. **Lead with "we can't guarantee 100%"** — sounds defensive
2. **Use jargon** (embeddings, RAG, temperature) — VP tunes out
3. **Promise 99.99%** to dodge — sets impossible standard
4. **Patronize** ("you don't need to understand the tech") — explosive
5. **Don't quote current human baseline** — miss the reframe
6. **No concrete guards** — vague "we have safety measures"
7. **Don't help her sell to CEO** — leave her stranded

---

## ✅ 加分项 (top 7)

1. **Reframe from "100%" to "right standard"**
2. **Quote current human baseline** (88-92% typical)
3. **4-layer guards explained as business analogies**
4. **Worst-case named honestly** with resolution path
5. **CEO-script drafted for them**
6. **Phase rollout** (200 agents, 30 days, eval, full)
7. **Quote Indonesia OJK pre-approval experience**

---

## 一句话总结

> **向非技术 VP 解释 RAG 没有 100% 保证 = "reframe to right-standard + business analogy for current baseline + 4 layers of guards as business analogies + help her sell to CEO + name worst case honestly"**.
>
> 真正的 win 不是说服 VP 接受 "AI 不完美", 是让她**有 ammunition 跟 CEO 说: '我们比现在好 4-10 倍, 有 4 层 guard, 1 小时可 rollback'**.

---

## Cheat Sheet

```
不要用:
  - "embedding" / "vector"
  - "RAG" / "retrieval"
  - "temperature" / "top-p"
  - "stochastic" / "deterministic"
  - "model" alone
  - "we can't guarantee" (defensive)
  - Patronizing tone

要用:
  - "the system reasons rather than retrieves"
  - "citation" (it cites the source)
  - "confidence" (it knows when unsure)
  - "eval" (we measure weekly)
  - "audit log" (every answer is recorded)
  - "escalation" (routes to human)
  - "measurably better than today"

8-layer response:
  1. Validate (0:00-0:30) "right question"
  2. Reframe (0:30-2:00) "100% isn't a real standard"
  3. Business analogy (2:00-5:00) current baseline
  4. 4 guards (5:00-12:00) citation/conf/eval/audit
  5. Variance vs human (12:00-17:00)
  6. Worst case (17:00-21:00)
  7. Defensible to CEO (21:00-25:00)
  8. Commit + phased (25:00-30:00)

Reframe sentence:
  "'100% accurate' isn't a standard that exists
   for ANY decision system. Let me show you what is."

Current baseline anchor:
  "Your support team — what's their accuracy today?
   Call center industry baseline is 85-92%.
   Our system is 95-99% on your data.
   You're already 4-10x better."

4 guards (business analogies):
  1. Citation = "agent says 'per policy 4.2, here's the answer'"
  2. Confidence = "junior agent who escalates when unsure"
  3. Eval = "weekly customer-satisfaction survey but for accuracy"
  4. Audit log = "call recording for legal review"

Worst-case framing:
  "In first 30 days, expect 3-5 incidents.
   Plan for them, don't be surprised.
   Each resolved < 24 hours."

CEO-script (3 sentences):
  1. "AI 4-10x better than current support on accuracy"
  2. "Every answer cited, audited, escalable"
  3. "Rollback in 1 hour"

Phased rollout (always propose):
  200 agents → 30 days eval → full rollout
  KPIs: accuracy, escalation rate, agent satisfaction, customer NPS, override rate

What to commit (specific):
  - 1-pager for CEO by Monday
  - Phase-1 launch plan by Friday
  - 30-day eval review
  - Rollback ability in 1 hour

What you need from VP:
  - Phase-1 sign-off
  - Incident escalation contact
  - Eval threshold approval

When she says 99.99%:
  - Honest: "out-of-box: 97%. With fine-tune + rerank + 2-model consensus: 99%+"
  - "5x cost, 3x latency. Worth it?"
  - "Is 99.99% real need or feel-safer?"

When she asks about worst case:
  - Don't pretend never failed
  - Share specific past incident
  - Show what changed afterward

When she asks about competitors:
  - "No vendor offers 100%. Any who does won't sign it."
  - "Test: ask for it in writing"

Resume quote:
  "TikTok PayLater Indonesia + OJK regulator:
   wanted 'no AI errors'. Reframed via current
   8-15% human variance baseline, 4 guards as
   existing processes (citation/escalation/QA/calls).
   OJK pre-approved in 6 weeks via 2-page methodology.
   Pattern: reframe + analogy + help them sell upward."

Close line:
  "Your job is to protect customers; mine is to ship
   something you can defend. That's the goal."
```
