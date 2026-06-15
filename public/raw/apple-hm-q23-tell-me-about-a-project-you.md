# 🍎 HM Q23 · "Tell me about a project you owned end to end with little guidance."

> **类别**: Behavioral / Ownership (STAR) · **考点**: 能不能从 0→1 独立扛下一个有真实业务影响的系统, 且 ownership 横跨 ASR→LLM→TTS + post-training + serving · ⚠️ [✏️] 数字背前替换成真实值

## 🧠 这题在测什么 / 面试官想看到

Apple 的 ownership 信号是头等大事 — 他们想听到 "I", 不是 "we"; 想听到你在**没人给详细方向**时自己定义问题、定义指标、做取舍。强答案 = 一个有清晰商业目标的 0→1 项目, 你展示了**端到端的技术广度**(数据→模型→serving→上线), 并用具体数字收尾。弱答案 = 泛泛说 "我负责了一个大项目", 全程 "我们", 没有个人决策点, 没有取舍。陷阱: 把团队成果说成自己的 → Apple 会顺着钻 "那部分具体是谁做的", 所以要诚实区分 "我亲手做的" vs "我带团队做的"。

## 📋 English Answer (背诵稿, 主答 ~75 秒 + 可延伸)

"The clearest example is the multilingual voice agent I led from zero to production at TikTok Global Payment, starting mid-2025. The mandate was deliberately vague — leadership said 'we want a voice AI that can handle outbound conversations across our markets,' and that was it. No design, no metrics, no reference system. I owned the whole thing end to end with a team of three.

I broke it into three layers and owned all of them. **Layer one, the voice pipeline** — ASR, TTS, VAD streaming, packetization, and interruption handling. **Layer two, the brain** — the LLM dialogue policy plus tool orchestration, so the agent could actually look things up and take actions, not just talk. **Layer three, the model itself** — I owned foundation-model post-training: data construction, multilingual adaptation, SFT, then DPO-style alignment, all driven by an eval harness I built so we iterated on numbers, not vibes.

The hardest part was that it had to work across seven markets — Chinese, English, Japanese, Korean, Malay, Indonesian, Thai — each with different speech patterns and a different bar for what 'natural' sounds like. So I didn't just train one model and ship; I built a market-by-market eval loop and a shadow-mode rollout so we caught regressions before any real customer heard them.

The outcome: we shipped to production across all seven markets, and we moved the three metrics that mattered — latency down, automation rate up, and repayment conversion up [✏️ 核实 具体数字]. The thing I'm proudest of isn't any single number — it's that there was no template for this, and I had to define what 'good' even meant before I could build it."

延伸 (若给时间): "If I zoom into one decision — early on I had to choose whether to chase the lowest possible latency or protect conversation quality. I'll come back to that if it's useful, because the tradeoff there is the core of the whole system."

## 🇨🇳 中文完整版 (口播稿, 与英文对应)

"最清楚的一个例子, 是我在 TikTok Global Payment 从 0 到 1 带起来的那个多语言 voice agent, 大概 2025 年中开始做的。这个事情的 mandate 是故意很模糊的 — leadership 就一句话, '我们想要一个能跨市场打 outbound 对话的 voice AI', 就这么多。没有设计, 没有指标, 没有可参考的系统。这整个东西是我端到端扛下来的, 带了一个三个人的小团队。

我把它拆成三层, 三层我都 own。**第一层, voice pipeline** — ASR、TTS、VAD streaming、打包、还有打断处理 (interruption)。**第二层, 大脑** — LLM 的对话策略加上 tool orchestration, 让这个 agent 真的能去查东西、能执行动作, 而不只是会说话。**第三层, 模型本身** — 我 own 了 foundation model 的 post-training: 数据构造、多语适配、SFT, 然后 DPO-style 的 alignment, 这一整套全都是跑在我自己搭的 eval harness 上的, 所以我们是拿数字在迭代, 不是凭感觉。

最难的部分是, 它得在七个市场都能跑 — 中文、英文、日文、韩文、马来语、印尼语、泰语 — 每个市场的说话习惯都不一样, 对 '自然' 的标准也不一样。所以我没有训一个模型就直接 ship; 我搭了一个 market-by-market 的 eval loop, 加上 shadow-mode 上线, 这样我们能在任何真实客户听到之前就把 regression 抓出来。

结果是: 我们在全部七个市场都上了线, 而且把三个真正重要的指标都推动了 — latency 降下来、automation rate 升上去、还有还款 conversion 也涨了 [✏️ 核实 具体数字]。我最自豪的其实不是某一个数字 — 而是这件事根本没有模板, 我得先定义清楚 '什么叫好', 才谈得上去把它做出来。"

延伸 (若给时间): "如果让我钻进某一个决策 — 一开始我就得选, 到底是去追极致的 latency, 还是保住对话质量。如果有用我可以回头展开讲这个, 因为那个取舍其实是整个系统的核心。"

## 🇨🇳 中文要点 (理解 + 记忆骨架)

- **开场一句锁定**: 0→1 voice agent, mandate 故意模糊 ("就一句话: 做个能打电话的语音 AI"), 没设计没指标没参考 → 这就是 "little guidance" 的证据。
- **三层骨架** (背熟这个三段式, 体现广度):
  1. Voice pipeline: ASR / TTS / VAD / streaming / 打断处理
  2. Brain: LLM dialogue + tool orchestration (能查能做, 不只是会说)
  3. Model: post-training 全链路 — 数据构造 / 多语适配 / SFT / DPO-style alignment, 全部 eval-driven
- **难点 = 7 markets**: 每个市场语音习惯不同、"自然" 的标准不同 → 我做了 per-market eval loop + shadow-mode rollout (上线前抓回归)。
- **结尾**: 三个核心指标都动了 (latency↓ / automation↑ / conversion↑ [✏️ 核实]); 最自豪的是 **"没有模板, 我得先定义什么叫好"** — 这句直接命中 ownership。
- 记忆钩子: **"三层 + 七市场 + 先定义好"**。

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: With a team of three, what did YOU personally build versus delegate?**
"I personally owned the post-training stack and the eval harness — data pipeline, SFT/DPO runs, and the metric definitions. I led, but didn't solo, the voice streaming work; one engineer drove the ASR/TTS integration while I owned the latency-quality tradeoff decisions and the interruption logic. I made the architecture calls; they owned execution on their slices. I'm happy to go deep on the post-training part since that's the piece that was fully mine."

**Q: What was the hardest single decision you had to make alone?**
"Whether to ship one shared multilingual model or per-market models. Shared is cheaper to maintain and serve; per-market is higher quality but multiplies the post-training and serving cost. I went with a shared backbone plus lightweight per-market adaptation — best quality-per-dollar, and it kept serving simple. That's a bet I owned, and I'd defend the reasoning even though it cost me more eval work upfront."

**Q: How did you know it was actually working, not just looking good in a demo?**
"That's exactly why I refused to ship on demos. I built an offline eval harness with market-specific test sets, plus shadow mode in production where the agent ran without affecting the real customer, and I compared its decisions against the live outcome. A demo passing means nothing; a stable shadow-mode number across a week means something."

## ⚠️ 边界 & 红线 (honest limits + what NOT to say)

- 诚实区分 "我亲手做" vs "带团队做"。Apple 一定会问 "你具体做了哪块" — 把 post-training + eval harness + 取舍决策划成自己的, voice streaming 划成 "led, one engineer executed"。不要把 3 个人的活全揽成 "我"。
- 不要把所有数字说死。latency / automation / conversion 的具体值用 [✏️ 核实] 占位, 背前换成真实数据 — 说不准的数字被钻会很难看。
- 不要说 "毫无指导所以全靠我天才"。框成 "mandate 模糊 → 我主动把模糊翻译成可执行的指标和架构", 这是成熟度, 不是邀功。
- 别炫技术名词堆砌。每个名词后面要能接 "为什么这么选"。

## ✅ 加分钩子 (主动抛, steer 到强项)

- **"先定义什么叫好"** — 这句是这题的灵魂, 主动强调, 直击 Apple 的 ownership + quality bar。
- **横跨 ASR→LLM→TTS→serving 的全栈广度** — 主动点出 "很少有人同时碰 voice pipeline 和 post-training", 这是你区别于纯模型工程师/纯 infra 工程师的差异点。
- **eval-driven, not vibes-driven** — 主动抛 eval harness + shadow mode, 正好命中 JD 的 "LLM eval" 和 "monitoring", 也呼应 Apple "上线前不让真实用户踩坑" 的质量观。
- 埋钩子: 提一句 latency-quality 取舍, 引导面试官顺着问到你的 streaming / TTFA 强项 (可衔接 Q26 on-device 那条线)。
