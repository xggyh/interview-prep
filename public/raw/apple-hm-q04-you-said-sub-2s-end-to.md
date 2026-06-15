# 🍎 HM Q4 · "You said sub-2s end-to-end. How did you allocate that budget across ASR/LLM/TTS, and where was the hardest millisecond?"

> **类别**: Project deep-dive / 延迟工程 · **考点**: 给出具体预算切分（数字全标 [✏️]）+ 指出最难的那一毫秒 + 怎么省下来的 · ⚠️ [✏️] 数字背前替换成真实值

## 🧠 这题在测什么 / 面试官想看到

JD 第一句就是 latency / cost / customer experience。HM 想看你**有没有真的拿延迟预算当工程对象在管**——能不能把一个总目标拆到每一跳、知道哪一跳最贵、并讲出你具体动了什么把它压下来。强答案 = 一张 budget 表（每跳 ms + 占比）+ 明确指认瓶颈（几乎一定是 LLM TTFT，因为 TTS 要等它）+ 2-3 个真实优化手段。弱答案 = "我们优化了很多，大概 2 秒"——没有拆分、没有瓶颈、没有手段。陷阱：(1) 报一堆精确数字却说不出怎么测的（Apple 会问"how did you measure that"）；(2) 把所有数字当事实背——**全部口头说 approximately 并在稿里标 [✏️]**。这一题数字密度最高，最容易翻车，务必先和真实数据对齐。

## 📋 English Answer (背诵稿, 主答 ~60-90 秒 + 可延伸)

"Right — and to be precise, the number that matters to a caller isn't total round-trip, it's **time-to-first-audio**: how long after they stop talking until they hear us start. That's the perceived latency. Let me give you the budget that way. *(数字全部 [✏️ 核实]，口头说 'roughly')*

Out of a sub-2-second budget, roughly:
- **ASR endpointing + final**: ~[✏️ 300ms]. Most of that is the endpointer waiting to be confident the user actually stopped — not compute. That wait is a tunable: too short and we cut people off, too long and we feel slow.
- **Retrieval + context assembly**: ~[✏️ 100ms]. Pulling account state and dialogue history into the prompt.
- **LLM time-to-first-token**: ~[✏️ 500ms] — and this is the hardest millisecond. TTS literally cannot start until the first tokens exist, so TTFT sits on the critical path with nothing able to hide behind it.
- **TTS time-to-first-audio**: ~[✏️ 200ms] from first tokens to first synthesized frame.
- **Network / telephony overhead**: ~[✏️ 150ms] round trip.

So perceived latency lands around [✏️ 1.2s] of first-audio, under the 2-second bar.

The hardest part, clearly, was **LLM TTFT**, for a structural reason: everything else can overlap, but TTS is strictly downstream of the first token. So I attacked it three ways. One — **prefill optimization and KV-cache reuse** on the serving side with vLLM/SGLang, so the static parts of the prompt — system instructions, tool schema — aren't recomputed every turn. Two — **streaming the LLM output and starting TTS on the first clause**, not the full sentence, so TTFT and synthesis overlap. Three — **shrinking the prompt** by retrieving only the account fields the policy needs, because prefill cost scales with input length. The endpointer was the other tuning knob — I traded a little latency for not interrupting people, because cutting a caller off is worse than being 100ms slower."

*(可延伸)*: "The honest caveat: these are the shapes from our dashboards — I'd want to pull the exact current percentiles before quoting them as hard numbers, and I track p95, not just the mean, because the tail is what callers actually feel."

## 🇨🇳 中文要点 (理解 + 记忆骨架)

**第一步重新定义指标（关键，显专业）**：用户感知的不是 total round-trip，是 **time-to-first-audio**（用户停说 → 听到我们开口）。按这个口径给预算。

预算表（数字全 [✏️]，口头 "roughly"）：
| 跳 | ~ms | 备注 |
|---|---|---|
| ASR endpointing + final | [✏️ 300] | 大头是 endpointer 等"确认停了"，不是算力 |
| Retrieval + context 拼装 | [✏️ 100] | 拉账户 state + 历史 |
| **LLM TTFT** | [✏️ 500] | **最难**，TTS 必须等它，挡在关键路径上 |
| TTS time-to-first-audio | [✏️ 200] | 第一 token → 第一帧 |
| Network / telephony | [✏️ 150] | round trip |
| **感知延迟** | **~[✏️ 1.2s]** | 在 2s 内 |

**最难的一毫秒 = LLM TTFT**，结构性原因：别的都能 overlap，**TTS 严格在第一个 token 之后**，没东西能藏在它后面。三招砍它：
1. **Prefill 优化 + KV-cache 复用**（vLLM/SGLang）——system prompt / tool schema 这种静态部分不每轮重算。
2. **LLM 流式 + 第一个分句就开 TTS**——让 TTFT 和合成 overlap。
3. **缩短 prompt**——只检索 policy 需要的账户字段，prefill 成本随输入长度涨。
+ endpointer 是另一个旋钮：宁可慢 100ms 也不打断用户（**打断比慢更伤体验**）。

**诚实收口**：这些是 dashboard 的"形状"，背前要拉真实 p95（不是均值，**尾延迟才是用户真感受**）。

记忆口诀：**先改口径(first-audio)→给表→点瓶颈(TTFT 因为 TTS 在它下游)→三招(KV-cache复用/分句开TTS/缩prompt)→认尾延迟**。

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: How did you actually measure these numbers?**
"Per-hop timestamps logged in the observability layer — every stage emits enter/exit timestamps tied to a turn ID, so I can attribute milliseconds to ASR vs LLM vs TTS for every real call, not a synthetic test. I look at distributions, mostly p50 and p95. I'd pull the live numbers before quoting exact figures — what I'm giving you is the shape."

**Q: You optimized TTFT with KV-cache reuse — what exactly is cached and what's the win?**
"The prefix of the prompt that's stable across turns — system instructions and the tool schema — gets its KV computed once and reused, so per-turn prefill only processes the new user turn plus retrieved context. The win scales with how much of your prompt is static; for us the system+tools prefix is a large fixed block, so it's meaningful. On Apple's side this is the same idea as the published KV-cache sharing that cuts prefill memory — about 37.5% in their report — just applied on-device." *(接 on-device 桥)*

**Q: Could you have used a smaller/faster model to cut TTFT instead?**
"Yes, and that's the real trade. A smaller model lowers TTFT but can drop task accuracy and compliance adherence, which in debt collection is unacceptable. My approach was: keep the model capable enough to be safe, and buy latency back through serving optimizations and overlap rather than by shrinking the brain. If I were forced smaller, I'd compensate with tighter post-training on the specific task — which is exactly the on-device adapter story."

**Q: What's your p95, not your average? The tail is what hurts.**
"Agreed — that's the right question. The mean is comfortably under budget; the tail is where occasional slow tool calls or a long generation push it up. I monitor p95 explicitly and the biggest tail contributors are tool latency and unusually long completions. I'd give you the live p95 rather than guess — but I track it precisely because, as you say, callers feel the tail, not the average."

**Q: Where would on-device change this budget?**
"TTFT changes character — no network round trip to a GPU, but you're prefilling on a phone's compute and memory budget, so the quantization and KV-cache decisions become the whole game. Network overhead largely disappears for on-device turns; PCC turns reintroduce a round trip but with privacy guarantees. The budgeting discipline is identical — the line items move."

## ⚠️ 边界 & 红线 (honest limits + what NOT to say)

- **最大红线**：把 [✏️] 数字当确定事实背出来。每个数字口头加 "roughly / approximately / on the order of"，并在面试前**务必和真实 dashboard 对齐**。报错一个被追问"how'd you measure" 会连锁崩。
- 别报你说不出测量方法的数字——HM 一定追"how did you measure that"。答案永远是"per-hop timestamps tied to a turn ID"。
- 别只给均值。主动说 p95 / tail，否则被追问 p95 时显得没真在 monitor。
- 别声称"我把延迟从 X 降到 Y"除非有真数据；可以说"我把 TTFT 当主攻方向，用了这三招"，过程比结果数字更安全。
- KV-cache 37.5% 是 Apple 公开报告数字，可引用；别把它说成你做的——明确说"Apple's published number / on their side"。

## ✅ 加分钩子 (主动抛, steer 到强项)

- 开场重定义"perceived latency = time-to-first-audio, not round-trip" —— 立刻显示你是从 customer experience 倒推工程，Apple 的 latency/UX 关切直接命中。
- "TTS is strictly downstream of the first token, so TTFT has nothing to hide behind" —— 一句话证明你真的理解 pipeline 的关键路径，不是背名词。
- KV-cache 复用 → 主动桥到 Apple 公开的 37.5% prefill 节省 —— 把你的 vLLM 经验和 Apple on-device 技术精确对接。
- "cutting a caller off is worse than being 100ms slower" —— 把一个纯工程旋钮上升到产品判断，展示 senior 的 trade-off sense。
- 主动认 p95 / tail —— 不等对方问就暴露你 monitor 尾延迟，这是区分"做过生产系统"和"做过 demo"的信号。
