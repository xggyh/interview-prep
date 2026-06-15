# 🍎 HM Q10 · How does the intent classifier work — rules, small model, or LLM? What accuracy, and what happens when it's wrong?

> **类别**: BNPL & Agent Platform · **考点**: 分类器选型 + 准确率 + 错分自愈 (re-route / escalate),绝不假设 100% 准 · ⚠️ [✏️] 数字背前替换成真实值

## 🧠 这题在测什么 / 面试官想看到

两层意图:(1) 你对 classifier 选型有没有**工程判断** (rules vs small model vs LLM 各自的取舍),(2) —— 这才是真考点 —— **你假不假设它 100% 准**。Apple 在做 customer-facing agent,misroute 会直接伤体验,所以"它错了怎么办"比"它有多准"更重要。强答会给一个**自愈闭环**:置信度门限 → 澄清 / re-route / 升级人工。弱答会甩一个 99% 准确率然后没有下文。陷阱:报一个漂亮的 accuracy 却说不出错分时发生什么。

## 📋 English Answer (背诵稿, 主答 ~60-90 秒 + 可延伸)

"I treat the classifier as a tiered system, not one model, because routing has very asymmetric cost.

**Tier one is a small, cheap model** — a fine-tuned lightweight classifier — that handles the bulk of turns at low latency. For the clear, high-frequency intents like order lookup or refund, you don't need a large model to know where to route.

**Tier two is an LLM fallback** for the ambiguous cases — when the small model's confidence is below a threshold, I escalate the *routing decision itself* to an LLM that can reason over the full conversational context. So I spend the expensive model only where it earns its keep.

I'd be honest about accuracy — I'd quote the real number from our eval set rather than a round figure [✏️ 核实 实际 intent accuracy],and I'd point out top-line accuracy hides the thing that matters: the confusion between *adjacent money-touching intents*, like refund versus dispute. That specific confusion is what I watched.

Now — **the important part — what happens when it's wrong.** I never assume the router is correct. Three mechanisms:

1. **Low confidence → ask, don't guess.** If confidence is below threshold, the agent asks one clarifying question instead of routing blindly.
2. **Detected misroute → re-route.** If a sub-agent receives a turn that doesn't fit its domain — say the refund agent sees no refundable order — it doesn't hallucinate an action; it signals back to the orchestrator and the turn is re-routed.
3. **Repeated failure or sensitive intent → escalate to a human.** In a compliance-sensitive, money-touching flow, the right move when the system is uncertain is a graceful handoff, not a confident wrong action.

So the design assumption is: the classifier *will* be wrong some percent of the time, and the system stays safe anyway."

## 🇨🇳 中文要点 (理解 + 记忆骨架)

**选型 = 分层 (cost 非对称):**
- **小模型 (主力)**: fine-tuned 轻量分类器,扛大多数清晰高频意图,低延迟。
- **LLM (fallback)**: 小模型置信度低时,把"路由决策本身"升级给 LLM,让它读全上下文推理。贵模型只用在刀刃上。
- (备选话术:rules 适合极少数硬规则,但维护成本高、不泛化,所以只做兜底/护栏,不做主分类。)

**准确率:** 报真实 eval 数字 [✏️ 核实],并主动说 top-line accuracy 会掩盖关键问题 —— **相邻 money-touching 意图的混淆** (refund vs dispute) 才是我盯的。

**错了怎么办 (真考点,记三步自愈):**
1. **低置信 → 反问澄清**,不盲路由。
2. **检测到 misroute → re-route**:sub-agent 发现不属于自己域 (refund agent 找不到可退订单) → 不幻觉动作,回信号给 orchestrator 重路由。
3. **反复失败 / 敏感意图 → 升级人工**:money flow 里不确定时,优雅 handoff > 自信地做错。

骨架一句话:**"我从不假设 router 100% 准 —— 低置信反问、错分回弹、敏感升级,系统在分类器出错时依然安全。"**

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: Why not just use the LLM for routing everywhere — it's more accurate?**
Latency and cost. Routing is on the critical path of every single turn — putting a large model there taxes every interaction, even the trivial ones. The tiered approach gives me the LLM's judgment on the hard 10–20% [✏️ 核实 占比] while keeping median latency and cost down. That latency/cost/quality trade-off is exactly the kind of thing this role cares about.

**Q: How do you set the confidence threshold?**
It's a precision/recall trade-off I tune on the eval set against the *cost of a misroute*. For benign intents I can route more aggressively. For money-touching intents — refund, dispute — I raise the bar, because a wrong action there is expensive, so I'd rather ask a clarifying question or escalate. The threshold isn't one global number; it's per-intent risk-weighted.

**Q: How do you know a misroute even happened — that's the hard part?**
Two signals. First, *in-band*: the sub-agent itself can detect domain mismatch — the refund agent queries for a refundable order and finds none, that's a strong misroute signal. Second, *out-of-band*: I instrument it — user re-asks, user expresses frustration, or the conversation stalls without resolution. Those feed both the live escalation path and the offline retraining set.

**Q: How does the classifier improve over time?**
Misrouted and clarified turns are gold-standard labels. They flow back into the training set for the small model, and I review the confusion matrix — especially the adjacent-intent cells — each iteration. That's the eval-driven loop I ran on the voice agent too.

**Q: Rules — did you use any at all?**
Yes, narrowly — as deterministic guardrails, not as the classifier. E.g. hard keyword triggers for high-risk phrases that must always escalate (a regulatory complaint, fraud language) regardless of what the model thinks. Rules are good at "never miss this", bad at general coverage — so I use them only where a miss is unacceptable.

## ⚠️ 边界 & 红线 (honest limits + what NOT to say)

- **绝不报 100% 或一个没核实的漂亮数字。** 报真实 eval 数 [✏️ 核实];如果当时没系统量过 per-intent accuracy,就老实说"我们主要盯 resolution rate 和混淆矩阵的相邻格",别硬编一个。
- 不要把 classifier 讲成单一模型就完事 —— 必须带出"错了怎么办"的闭环,否则正中陷阱。
- 如果被追"misroute 检测当时是不是真做到了自动",诚实区分:in-band 域不匹配检测是有的;out-of-band 的 frustration 检测如果当时偏人工抽样,就说成"抽样 + 逐步自动化",别说成全自动。
- 不要声称 rules 能扛主分类 —— 会显得不懂泛化问题。Rules 只做"绝不能漏"的护栏。

## ✅ 加分钩子 (主动抛, steer 到强项)

- 主动把它框成 **latency/cost/quality 三角的路由层取舍** —— 直接命中 JD 的 "improve latency, cost, customer experience"。
- 强调 **per-intent risk-weighted threshold** (money-touching 意图门限更高) —— 体现你懂 compliance-sensitive 场景,对上 Apple customer systems。
- 提 **"误路由样本回流再训练 + 看相邻意图混淆矩阵"** 的 eval-driven 闭环 —— 跟你 voice agent 的 eval-driven iteration 是同一套方法论,可顺势引到 RL/eval 的强项。
