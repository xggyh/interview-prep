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

## 🇨🇳 中文完整版 (口播稿, 与英文对应)

"我把这个 classifier 当成一个分层系统来做，而不是单个模型，因为路由的成本是高度非对称的。

**第一层 —— 一个又小又便宜的 fine-tuned classifier。**
- 它在低延迟下扛掉大多数轮次。
- 对那些清晰、高频的意图 —— order lookup、refund —— 你根本不需要一个大模型就能知道该往哪路由。
- 它输出的是一个 confidence score，不只是一个 label。整个自愈设计都挂在这个分数上。

**第二层 —— 一个 LLM fallback，专门接那些模糊的 case。**
- 当小模型的置信度低于一个 threshold 时，我把*路由决策本身*升级给一个 LLM，让它在完整的对话上下文上做推理。
- 所以贵的模型我只花在它值得花的地方 —— 那难的 10–20% [✏️ 核实 占比]，而不是每一轮。

**关于 accuracy** —— 我会报我们 eval set 上的真实数字，而不是一个凑整的数 [✏️ 核实 实际 intent accuracy]。而且我会主动指出，top-line accuracy 会掩盖真正要紧的东西：*相邻的、碰钱的意图*之间的混淆，比如 refund 和 dispute。混淆矩阵里那一格，才是我真正盯的。

**现在是重点 —— 它错了会怎样。** 我从不假设 router 是对的。三个机制：
1. **低置信 → 反问，不要瞎猜。** 低于 threshold 时，agent 会问一个澄清问题，而不是盲目路由。
2. **检测到 misroute → 重新路由。** 如果 refund sub-agent 收到一轮、却找不到任何可退的订单，它不会幻觉出一个动作 —— 它会回信号给 orchestrator，这一轮被 re-route。
3. **反复失败或敏感意图 → 升级人工。** 在一个合规敏感、碰钱的流程里，不确定时正确的做法是优雅地 handoff，而不是自信地做一个错的动作。

所以这个设计的前提假设就是：classifier *一定*会有某个比例是错的，而系统在它错的时候依然是安全的。"

*(可延伸:)* "而且那些被误路由、又被澄清的轮次并没有白费 —— 它们是 gold-standard 的 label，直接回流进小模型的训练集。classifier 恰恰在它原本做错的那些 case 上变得更好。"

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

强答 vs 弱答对照 (面试官心里的评分表):
- 弱答:"我们用了个分类模型,准确率 99%" → 然后没了。报漂亮数字 + 没有错分处理 = 正中陷阱,显得没在生产里运营过。
- 弱答:"用 LLM 做意图识别,很准" → 没成本意识 (每轮都上大模型),也没讲错了怎么办。
- 中等:"小模型分类 + 置信度门限" → 方向对,但停在"门限",没讲门限触发后**怎么自愈**。
- **强答 (你要给的):分层选型 (cost 非对称) + 报真实数且主动揭示相邻意图混淆 + 三步自愈闭环 (反问/回弹/升级) + 错例回流再训练** → 这才是"我知道它会错,而且系统在它错时依然安全"。

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: Why not just use the LLM for routing everywhere — it's more accurate?**
**中**: 为什么不干脆全程用 LLM 来路由 —— 它更准啊？
- Latency and cost. Routing is on the critical path of *every* turn — a large model there taxes every interaction, even trivial ones.
- The tiered approach gives me the LLM's judgment on the hard 10–20% [✏️ 核实] while keeping median latency and cost down.
- That latency/cost/quality trade-off is exactly what this role cares about.
> 🇨🇳 latency 和 cost。routing 在*每一轮*的关键路径上 —— 在那放一个大模型，会给每一次交互都加税，哪怕是最 trivial 的那种。分层的做法让我在难的那 10–20% [✏️ 核实] 上拿到 LLM 的判断，同时把 median 的延迟和成本压下来。这个 latency/cost/quality 的权衡，恰恰是这个岗位关心的东西。

**Q: How do you set the confidence threshold?**
**中**: confidence 阈值你是怎么定的？
- It's a precision/recall trade-off I tune on the eval set against the *cost of a misroute*.
- Benign intents → route more aggressively. Money-touching intents (refund, dispute) → raise the bar; a wrong action there is expensive, so I'd rather ask or escalate.
- So it's not one global number — it's *per-intent, risk-weighted*.
> 🇨🇳 这是一个 precision/recall 的权衡，我在 eval set 上对着*一次 misroute 的代价*来调。无害的意图 → 路由得更激进一点。碰钱的意图（refund、dispute）→ 把门槛抬高；那里做错一个动作代价很大，所以我宁愿先问一句或者升级。所以它不是一个全局的数 —— 它是*按 intent、按风险加权*的。

**Q: How do you even know a misroute happened — that's the hard part?**
**中**: 你怎么知道发生了一次 misroute —— 这才是难的地方？
- Two signals. *In-band*: the sub-agent detects domain mismatch — refund agent queries for a refundable order, finds none → strong misroute signal.
- *Out-of-band*: instrumentation — user re-asks, expresses frustration, or the conversation stalls without resolution.
- Those feed both the live escalation path and the offline retraining set.
> 🇨🇳 两个信号。*In-band*：sub-agent 自己检测到域不匹配 —— refund agent 去查一个可退款的订单，结果一个都没找到 → 这是一个很强的 misroute 信号。*Out-of-band*：靠 instrumentation —— 用户反复追问、表现出 frustration，或者对话卡住一直没 resolve。这两类信号同时喂给线上的 escalation 路径和离线的 retraining 集。

**Q: How does the classifier improve over time?**
**中**: 这个 classifier 随时间怎么变好？
- Misrouted-and-clarified turns are gold-standard labels — they flow back into the small model's training set.
- I review the confusion matrix each iteration, especially the adjacent-intent cells.
- Same eval-driven loop I ran on the voice agent: ship → measure → find failures → retrain on those failures.
> 🇨🇳 那些先路由错、然后被澄清纠正的 turn，是 gold-standard 的标签 —— 它们回流进小模型的训练集。我每一轮迭代都看 confusion matrix，尤其是相邻意图那几格。跟我在 voice agent 上跑的是同一个 eval-driven 闭环：上线 → 度量 → 找失败 → 在这些失败上 retrain。

**Q: Rules — did you use any at all?**
**中**: 规则 —— 你到底用没用？
- Yes, narrowly — as deterministic *guardrails*, not the classifier.
- E.g. hard triggers for high-risk phrases that must *always* escalate — a regulatory complaint, fraud language — regardless of what the model thinks.
- Rules are great at "never miss this," bad at general coverage. So I use them only where a miss is unacceptable.
> 🇨🇳 用了，但很窄 —— 是作为确定性的 *guardrails*，不是作为 classifier。比如对一些高风险措辞设硬触发，这些必须*永远*升级 —— 监管投诉、涉欺诈的话术 —— 不管模型怎么想。规则擅长"绝不漏掉这个"，但不擅长泛化覆盖。所以我只在"漏掉就不可接受"的地方用它。

**Q: What latency does the classifier add per turn?**
**中**: 这个 classifier 每一轮加多少延迟？
- The small model is cheap — a few milliseconds of overhead [✏️ 核实 实际延迟] — which is the whole reason it's tier one.
- The LLM fallback is slower, but it only fires on the ambiguous minority, so it doesn't move the median.
- This is a deliberate latency-budget decision, not an afterthought.
> 🇨🇳 小模型很便宜 —— 就几毫秒的开销 [✏️ 核实 实际延迟] —— 这正是它能当 tier one 的全部原因。LLM 的 fallback 更慢，但它只在那一小撮 ambiguous 的情况上触发，所以它不会动 median。这是一个刻意的 latency-budget 决策，不是事后补的。

**Q: New intents appear over time — how does the taxonomy not go stale?**
**中**: 新意图会随时间冒出来 —— taxonomy 怎么不会过时？
- I monitor the *general* / fallback bucket and the low-confidence cluster — a rising mass there is the signal that a new intent is emerging.
- When a cluster is big and automatable enough, it graduates into its own labeled intent with a sub-agent.
- So the taxonomy is data-driven and evolving, not frozen at launch. [✏️ 核实 实际有没有做这个 cluster 监控]
> 🇨🇳 我会监控 *general* / fallback 那个桶，还有 low-confidence 的那一簇 —— 那里的量在涨，就是一个新意图正在浮现的信号。当某一簇足够大、又足够可自动化时，它就"毕业"成自己一个有标签的意图，配一个 sub-agent。所以这个 taxonomy 是数据驱动、不断演化的，不是上线那一刻就冻住的。[✏️ 核实 实际有没有做这个 cluster 监控]

**Q: Could you skip the classifier and let an orchestrator LLM decide routing as part of generation?**
**中**: 能不能干脆不要 classifier，让一个 orchestrator LLM 在生成的同时顺便决定路由？
- You can — that's the "single agent decides its own next action" pattern. The trade-off is you lose the cheap, fast, separately-measurable routing decision.
- A standalone classifier gives me a confidence score to gate on, a confusion matrix to debug, and a place to enforce risk-weighted thresholds — all harder to isolate inside one big generation call.
- For a compliance-sensitive flow I value that observability and control over the elegance of one model doing everything.
> 🇨🇳 可以 —— 那就是"单个 agent 自己决定下一步动作"的那种 pattern。代价是你失去了那个便宜、快、又能单独度量的 routing 决策。一个独立的 classifier 给我一个 confidence score 去 gate、一个 confusion matrix 去 debug、还有一个能强制施加风险加权阈值的地方 —— 这些塞进一个大的 generation 调用里都更难隔离出来。对一个合规敏感的流程，比起"一个模型干所有事"那种优雅，我更看重这种可观测性和控制力。

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
