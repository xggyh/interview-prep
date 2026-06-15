# 🍎 HM Q10 · How does the intent classifier work — rules, small model, or LLM? What accuracy, and what happens when it's wrong?

> **类别**: BNPL & Agent Platform · **考点**: 分类器选型 + 准确率 + 错分自愈 (re-route / escalate),绝不假设 100% 准 · ⚠️ [✏️] 数字背前替换成真实值

## 🧠 这题在测什么 / 面试官想看到

两层意图:(1) 你对 classifier 选型有没有**工程判断** (rules vs small model vs LLM 各自取舍),(2) —— 这才是真考点 —— **你假不假设它 100% 准**。Apple 在做 customer-facing agent,misroute 直接伤体验,所以"它错了怎么办"比"它有多准"更重要。强答会给一个**自愈闭环**:置信度门限 → 澄清 / re-route / 升级人工。弱答会甩一个 99% 准确率然后没有下文。陷阱:报一个漂亮的 accuracy 却说不出错分时发生什么。

## 📋 English Answer (背诵稿, 主答 ~60-90 秒 + 可延伸)

"I treat the classifier as a tiered system, not one model, because routing has very asymmetric cost.

**Tier one — a small, cheap fine-tuned classifier.**
- It handles the bulk of turns at low latency.
- For clear, high-frequency intents — order lookup, refund — you don't need a large model to know where to route.
- It emits a confidence score, not just a label. That score is what the whole self-healing design hangs on.

**Tier two — an LLM fallback for the ambiguous cases.**
- When the small model's confidence is below a threshold, I escalate the *routing decision itself* to an LLM that reasons over the full conversational context.
- So I spend the expensive model only where it earns its keep — the hard 10–20% [✏️ 核实 占比], not every turn.

**On accuracy** — I'd quote the real number from our eval set, not a round figure [✏️ 核实 实际 intent accuracy]. And I'd flag that top-line accuracy hides the thing that matters: the confusion between *adjacent money-touching intents*, like refund versus dispute. That specific cell in the confusion matrix is what I actually watched.

**Now the important part — what happens when it's wrong.** I never assume the router is correct. Three mechanisms:
1. **Low confidence → ask, don't guess.** Below threshold, the agent asks one clarifying question instead of routing blindly.
2. **Detected misroute → re-route.** If the refund sub-agent gets a turn with no refundable order, it doesn't hallucinate an action — it signals back to the orchestrator and the turn is re-routed.
3. **Repeated failure or sensitive intent → escalate to a human.** In a compliance-sensitive, money-touching flow, the right move under uncertainty is a graceful handoff, not a confident wrong action.

So the design assumption is: the classifier *will* be wrong some percent of the time, and the system stays safe anyway."

*(可延伸:)* "And those misrouted-then-clarified turns aren't wasted — they're gold-standard labels that flow straight back into the small model's training set. The classifier gets better at exactly the cases it was getting wrong."

## 🇨🇳 中文要点 (理解 + 记忆骨架)

**选型 = 分层 (cost 非对称):**
- **小模型 (主力)**: fine-tuned 轻量分类器,扛大多数清晰高频意图,低延迟。**输出 confidence 分数**,不只是 label —— 整个自愈设计都挂在这个分数上。
- **LLM (fallback)**: 小模型置信度低时,把"路由决策本身"升级给 LLM,让它读全上下文推理。贵模型只用在刀刃上 (难的 10–20% [✏️ 核实])。
- (备选话术:rules 适合极少数硬规则,但维护成本高、不泛化,所以只做兜底/护栏,不做主分类。)

**准确率:** 报真实 eval 数字 [✏️ 核实],并主动说 top-line accuracy 会掩盖关键问题 —— **相邻 money-touching 意图的混淆** (refund vs dispute) 才是我盯的那一格混淆矩阵。

**错了怎么办 (真考点,记三步自愈):**
1. **低置信 → 反问澄清**,不盲路由。
2. **检测到 misroute → re-route**:sub-agent 发现不属于自己域 (refund agent 找不到可退订单) → 不幻觉动作,回信号给 orchestrator 重路由。
3. **反复失败 / 敏感意图 → 升级人工**:money flow 里不确定时,优雅 handoff > 自信地做错。

**闭环:** 误路由 + 澄清后的轮次 = gold-standard label,回流再训练 → 分类器在它原本错的地方变好。

骨架一句话:**"我从不假设 router 100% 准 —— 小模型扛主流、LLM 接难例、低置信反问、错分回弹、敏感升级,系统在分类器出错时依然安全,且错例回流让它越来越准。"**

讲述节奏:
1. 先定调:"tiered system, not one model, because routing cost is asymmetric"。
2. 小模型 → LLM fallback 两层讲完。
3. accuracy:**主动**说"我盯的是相邻意图混淆,不是 top-line"。
4. **重头戏**:三步自愈,慢讲、讲透 —— 这是这题的 senior 信号。
5. 收尾:错例回流闭环。

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: Why not just use the LLM for routing everywhere — it's more accurate?**
- Latency and cost. Routing is on the critical path of *every* turn — a large model there taxes every interaction, even trivial ones.
- The tiered approach gives me the LLM's judgment on the hard 10–20% [✏️ 核实] while keeping median latency and cost down.
- That latency/cost/quality trade-off is exactly what this role cares about.

**Q: How do you set the confidence threshold?**
- It's a precision/recall trade-off I tune on the eval set against the *cost of a misroute*.
- Benign intents → route more aggressively. Money-touching intents (refund, dispute) → raise the bar; a wrong action there is expensive, so I'd rather ask or escalate.
- So it's not one global number — it's *per-intent, risk-weighted*.

**Q: How do you even know a misroute happened — that's the hard part?**
- Two signals. *In-band*: the sub-agent detects domain mismatch — refund agent queries for a refundable order, finds none → strong misroute signal.
- *Out-of-band*: instrumentation — user re-asks, expresses frustration, or the conversation stalls without resolution.
- Those feed both the live escalation path and the offline retraining set.

**Q: How does the classifier improve over time?**
- Misrouted-and-clarified turns are gold-standard labels — they flow back into the small model's training set.
- I review the confusion matrix each iteration, especially the adjacent-intent cells.
- Same eval-driven loop I ran on the voice agent: ship → measure → find failures → retrain on those failures.

**Q: Rules — did you use any at all?**
- Yes, narrowly — as deterministic *guardrails*, not the classifier.
- E.g. hard triggers for high-risk phrases that must *always* escalate — a regulatory complaint, fraud language — regardless of what the model thinks.
- Rules are great at "never miss this," bad at general coverage. So I use them only where a miss is unacceptable.

**Q: What latency does the classifier add per turn?**
- The small model is cheap — a few milliseconds of overhead [✏️ 核实 实际延迟] — which is the whole reason it's tier one.
- The LLM fallback is slower, but it only fires on the ambiguous minority, so it doesn't move the median.
- This is a deliberate latency-budget decision, not an afterthought.

## ⚠️ 边界 & 红线 (honest limits + what NOT to say)

- **绝不报 100% 或一个没核实的漂亮数字。** 报真实 eval 数 [✏️ 核实];如果当时没系统量过 per-intent accuracy,就老实说"我们主要盯 resolution rate 和相邻意图混淆矩阵",别硬编一个。
- 不要把 classifier 讲成单一模型就完事 —— 必须带出"错了怎么办"的闭环,否则正中陷阱。
- 如果被追"misroute 检测当时是不是真做到自动",诚实区分:in-band 域不匹配检测是有的;out-of-band 的 frustration 检测如果当时偏人工抽样,就说成"抽样 + 逐步自动化",别说成全自动。
- 不要声称 rules 能扛主分类 —— 会显得不懂泛化问题。Rules 只做"绝不能漏"的护栏。
- 如果你当时其实是 **LLM 直接做分类** (没有专门的小模型),诚实说 —— 然后把答案重心放在"置信度 + 自愈"上,那部分照样成立,别硬编一个不存在的小模型。

## ✅ 加分钩子 (主动抛, steer 到强项)

- 主动把它框成 **latency/cost/quality 三角的路由层取舍** —— 直接命中 JD 的 "improve latency, cost, customer experience"。
- 强调 **per-intent risk-weighted threshold** (money-touching 意图门限更高) —— 体现你懂 compliance-sensitive 场景,对上 Apple customer systems。
- 提 **"误路由样本回流再训练 + 看相邻意图混淆矩阵"** 的 eval-driven 闭环 —— 跟你 voice agent 的 eval-driven iteration 同一套方法论,可顺势引到 RL/eval 强项 (Q14/Q19)。
- 主动说 **"confidence 分数是整个自愈设计的支点"** —— 一句话把分类器从"黑盒打标签"提升到"带不确定性的决策组件",非常 senior。
