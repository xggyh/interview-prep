# 🍎 HM Q12 · In a multi-turn conversation, how do you manage context as it grows?

> **类别**: BNPL & Agent Platform · **考点**: rolling summary / token budget / 受保护状态 / structured-vs-prose,直接对上 JD "multi-turn" · ⚠️ [✏️] 数字背前替换成真实值

## 🧠 这题在测什么 / 面试官想看到

JD 反复强调 "multi-turn, conversational" —— 核心能力题。面试官想看你懂**上下文不能无限堆**,以及你怎么在 token 预算内**不丢关键信息**。强答区分两类信息:**结构化状态** (订单号、已确认意图、金额 —— 必须精确保留) 和 **对话历史** (可摘要压缩),还会讲 token budget 怎么分配、什么绝不能丢。弱答会说"我把整段历史塞进 prompt"或"用个滑动窗口"然后没了。陷阱:把关键事实 (金额、确认过的动作) 当普通历史一起摘要掉 —— money flow 里这是灾难。

## 📋 English Answer (背诵稿, 主答 ~60-90 秒 + 可延伸)

"The core principle is: not all context is equal, so I don't manage it as one blob. I split it into structured state and conversational history, and treat them completely differently.

**Structured state — protected, never summarized.**
- Things like the order ID, the confirmed intent, the refund amount, what the user has already agreed to — facts the agent must carry *exactly*.
- I hold them as structured slots in the orchestration layer, *outside* the prompt's free-text history, and inject them verbatim every turn.
- You never want a summarizer to paraphrase '$200 refund' into 'a refund' — in a money-touching flow that's a real failure.

**Conversational history — compressed under a token budget.**
- I keep the last few turns verbatim — recency matters most for coherence.
- Everything older folds into a *rolling summary* that I update as the conversation moves.
- So the prompt is: system instructions, protected state, a running summary of the early conversation, and the last N turns in full.

**The token budget is explicit.**
- System and state get a reserved floor; recent turns get the bulk; the rolling summary is capped.
- As we approach the limit, the summary *absorbs* older turns rather than the prompt growing unboundedly.
- That keeps latency and cost flat as the conversation gets long — which matters because long conversations are exactly when users are frustrated and latency hurts most.

So: protect the facts as structured state, summarize the prose, and hold a hard token budget."

*(可延伸:)* "On the voice agent this discipline was even tighter — every extra token is latency the user *hears* as a pause. So the strict context budget came directly from that latency pressure, not from theory. And honestly, that's the same constraint I'd expect moving to on-device, where the budget is bounded by device memory rather than cost."

## 🇨🇳 中文完整版 (口播稿, 与英文对应)

"核心原则是：不是所有 context 都等价，所以我不会把它当成一坨整体来管。我把它拆成 structured state 和 conversational history，然后用完全不同的方式对待这两者。

**Structured state —— 受保护，绝不摘要。**
- 像 order ID、确认过的意图、refund 金额、用户已经同意了什么 —— 这些是 agent 必须*精确*携带的事实。
- 我把它们作为 structured slots 放在 orchestration 层，*在* prompt 那段自由文本历史*之外*，每一轮都原样注入。
- 你绝不希望一个 summarizer 把 '$200 refund' 改写成 'a refund' —— 在一个碰钱的流程里，这是一个真实的事故。

**Conversational history —— 在 token budget 下压缩。**
- 我把最近几轮原样保留 —— 对连贯性来说，recency 最重要。
- 再往前的全都折进一个 *rolling summary*，随着对话推进我不断更新它。
- 所以这个 prompt 就是：system instructions、protected state、早期对话的一份 running summary、以及最近 N 轮的完整原文。

**token budget 是显式的。**
- system 和 state 有一个保留的底线；最近几轮拿大头；rolling summary 有上限封顶。
- 当我们逼近上限时，是让 summary 去*吸收*更旧的轮次，而不是让 prompt 无限制地涨。
- 这让 latency 和 cost 在对话变长时保持平稳 —— 这很重要，因为长对话恰恰是用户最烦躁、延迟最伤人的时候。

所以：把事实作为 structured state 保护起来，把那些散文（prose）摘要掉，再守住一个硬的 token budget。"

*(可延伸:)* "在 voice agent 上这个纪律还要更严 —— 每多一个 token 就是用户能*听见*的延迟、是一个停顿。所以这个严格的 context budget 是直接来自那种延迟压力，不是来自理论。而且老实说，这跟我搬到端侧时会遇到的约束是一样的 —— 在端上 budget 是被设备内存框住的，而不是被 cost 框住。"

## 🇨🇳 中文要点 (理解 + 记忆骨架)

核心原则:**不是所有 context 都等价 —— 分成 structured state 和 conversational history,分开管。**

- **Structured state (受保护,绝不摘要)**: order ID、确认的意图、退款金额、用户已同意的事 —— 必须精确携带。存成 orchestration 层的 structured slots,在 prompt 自由文本历史**之外**,每轮原样注入。**绝不能让 summarizer 把 "$200 refund" 摘成 "a refund"** —— money flow 里是真事故。
- **Conversational history (token 预算下压缩)**: 最近几轮原样保留 (recency 对连贯最关键),更早的折进 **rolling summary**,随对话推进更新。
- **prompt 结构** = system instructions + protected state + 早期对话的 running summary + 最近 N 轮原文。
- **token budget 显式分配**: system/state 有保底,recent turns 占大头,summary 封顶。逼近上限时让 summary 吸收旧轮,而不是 prompt 无限涨 → **长对话也保持 latency/cost 平稳**。长对话恰恰是用户烦躁、延迟最伤的时候。

**判定法则 (放 state 还是放 summary):** 问一句 "如果这条被改写或丢了,会不会导致错误的*动作*?" —— 会,就是 protected state;不会 (只是语气/措辞),就进 summary。

骨架一句话:**"protect facts (structured state) / summarize prose (rolling summary) / 硬 token budget —— 让长对话延迟和成本不爆,关键事实绝不被摘掉。"**

讲述节奏:
1. 先抛原则:"not all context is equal — I split state from history"。
2. 三块:protected state → rolling summary → token budget,各一句。
3. 用 **"$200 refund 不能被摘成 a refund"** 这个具体例子坐实 —— 极有说服力,务必讲。
4. 收尾桥到 voice (token = 听得见的延迟) + 端侧 (budget 受设备内存约束)。

强答 vs 弱答对照 (面试官心里的评分表):
- 弱答:"我把对话历史塞进 prompt" → 不 scale,显得没在生产里跑过长对话。
- 弱答:"我用滑动窗口保留最近 K 轮" → 会丢早期关键事实 (订单号被滑出去),money flow 致命。
- 中等:"我用 rolling summary 压缩历史" → 对,但没区分 state vs prose,关键事实可能被摘掉。
- **强答 (你要给的):"state 和 history 分开 —— 事实进 protected slots 原样注入、prose 进 rolling summary、硬 token budget 兜底"** → 这才是 senior 信号:你知道哪些**绝不能**被压缩。

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: How do you build the rolling summary without it drifting or dropping facts?**
- Two safeguards. First, the summary only ever covers *prose* — the facts live in structured state, so even a lossy summary can't drop the order ID or amount.
- Second, I summarize *incrementally* — update the prior summary with the new turn rather than re-summarizing from scratch, which is cheaper and drifts less.
- I'd validate summary quality on an eval set, because a bad summarizer silently degrades every long conversation. [✏️ 核实 是否真上了 LLM summarizer vs 规则抽取]

**Q: What exactly goes into structured state vs the summary?**
- Anything that, if paraphrased or lost, changes the *outcome* → state: IDs, amounts, resolved intent, confirmations, tool results.
- Anything that's just rapport or phrasing → summary.
- The test: "would a wrong paraphrase of this cause a wrong action?" If yes, it's protected state.

**Q: How do you pick N — how many recent turns to keep verbatim?**
- It's a budget decision tuned against the eval, not a fixed number.
- Enough turns to preserve local coherence — pronouns, "the second one", follow-ups — but no more, because every verbatim turn is tokens I could spend elsewhere.
- In voice, where latency is audible, N was tighter than in text chat. [✏️ 核实 实际 N]

**Q: User references something from way back that got summarized away — now what?**
- That's why the summary is *lossy on prose but lossless on facts*. If they reference a fact, it's in structured state.
- If they reference earlier phrasing or a nuance, the summary should carry the gist.
- And if it genuinely fell out, the agent asks a one-line clarifier rather than guess. I'd rather re-confirm than confabulate.

**Q: Does this differ between the chatbot and the voice agent?**
- Same architecture, different pressure. In text I have more budget headroom.
- In voice, context length is a *latency* knob the user literally hears — so the budget is stricter and I lean harder on structured state plus a tight recent window.
- The principle is identical; the constraint surface changes — same kind of shift I'd expect moving to on-device.

**Q: Why not just use a long-context model and keep everything?**
- Cost and latency scale with context length every single turn, and quality doesn't — models lose recall in the middle of very long contexts.
- So a 100-turn conversation in full context is expensive *and* less reliable than state + summary + recent window.
- Long context is a tool, not a substitute for managing what the model actually needs to see.

**Q: How does the agent confirm a critical action when state and the user's words disagree?**
- Structured state is the source of truth for facts, but before a money-touching action I read the relevant slot back to the user for explicit confirmation — "to confirm, a $200 refund on order 12345?"
- If their reply contradicts state, I don't silently overwrite — I re-confirm, because in a money flow a wrong write is worse than an extra question.
- That confirmed value then updates the slot. State is authoritative, but a high-stakes change is always user-confirmed.

**Q: What happens to all this state when the session ends or the user comes back later?**
- Within a session it lives in the orchestration layer. Across sessions, whether I persist it depends on the use case [✏️ 核实 是否做了跨 session 持久化].
- If I persist, it's the structured slots — resolved intents, account context — not raw transcript, and it's subject to retention and privacy rules, which in a finance context are strict.
- I'd be explicit that long-term per-user memory raises privacy questions, so I'd only keep what's needed and govern it — which is exactly the mindset Apple cares about.

**Q: How would this run on-device with a small model and a hard memory ceiling?**
- The architecture barely changes — it's *built* around a token budget, which is just tighter on-device.
- Structured state stays cheap because it's compact slots, not prose; the rolling summary and recent window shrink to fit device memory.
- That's the cloud→device bridge: same discipline, the constraint flips from cost/HBM to unified memory and power.

## ⚠️ 边界 & 红线 (honest limits + what NOT to say)

- **绝不**说"把整段历史全塞进 prompt"或"只用固定滑动窗口" —— 前者不 scale,后者会丢关键事实。
- 诚实区分 summarizer 实现:如果当时是 LLM 摘要就说 LLM;如果是规则/槽位抽取为主、摘要为辅,就如实说,别吹成精巧的分层 memory。用 [✏️ 核实] 兜。
- 不要把 structured state 和 history 混为一谈 —— 这个区分是全题的 senior 信号,丢了就平庸。
- 不要声称做了向量化长期记忆 (per-user episodic memory) 除非真做了。如果只是 session 内 state + summary,就说 session 内。
- 不要声称精确测过"摘要丢信息率"之类的指标除非真测过;说"我在 eval set 上验证摘要质量",别编一个百分比。

## ✅ 加分钩子 (主动抛, steer 到强项)

- 主动抛 **"$200 refund 不能被摘成 a refund"** 这个具体例子 —— 一句话证明你懂 money-touching 的精确性红线,极有说服力。
- 把 **"长对话 = 用户最烦躁 + 延迟最伤"** 点出来 —— 命中 JD 的 latency + customer experience。
- 顺势桥到端侧:**"context budget 受设备内存约束,跟我在 voice 里把 context 当 latency 旋钮是同构问题"** —— 自然衔接 Apple on-device 的 cloud→device reframe (引到 Q26)。
- 提一句 **"这套 state + summary 后来做成了平台的 memory 服务"** —— 把单点能力升级成平台抽象 (引到 Q13)。
