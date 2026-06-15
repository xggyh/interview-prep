# 🍎 HM Q28 · "How do you stay current with the GenAI field?"

> **类别**: Fit / Learning & curiosity · **考点**: 是否有真实、具体、可验证的学习习惯, 而非泛泛 "我看论文"; 学到的东西能否落地 · ⚠️ [✏️] 数字背前替换成真实值

## 🧠 这题在测什么 / 面试官想看到

GenAI 半年就换一代, 团队 JD 明确说要 "incorporate the latest models"。面试官想确认: 你不是停在某个时间点的工程师, 你有**主动、持续、且能落地**的学习闭环。强答案 = 具体来源 (point 得出名字) + 输入如何变成输出 (内部分享/落地/竞赛) + 一个最近真学到并用上的例子。弱答案 = "我看 Twitter / 关注 arXiv" 这种谁都能说的空话。陷阱: 只说 "输入" (读了什么) 不说 "输出" (做了什么) → 显得是被动消费者, 不是 practitioner。Apple 想要的是 "学了就用" 的人。

## 📋 English Answer (背诵稿, 主答 ~70 秒 + 可延伸)

"I keep it concrete and I make sure learning turns into output, not just reading. Three channels.

**First, primary sources over hot takes.** I read the actual technical reports and papers — the model cards and tech reports from the major labs, including Apple's own 2025 on-device foundation-model report, which is part of why I can talk specifically about rank-16 adapters and 2-bit quantization. I'd rather read the real report than someone's thread about it, because the details that matter — the tradeoffs, the ablations — only live in the source.

**Second, I teach it, which forces me to actually understand it.** I've given three internal talks: 'LLM Strategy and Roadmap for Payments,' 'Agent Harness and Long-Horizon RL,' and one on 'GPU, TPU, and LPU Tradeoffs for GenAI Inference.' Preparing a talk is the highest-bandwidth way I learn — you can't give a talk on inference hardware tradeoffs while being vague about it, so it forces the knowledge to be real and structured.

**Third, I keep my hands dirty competitively.** I'm in the global top 1% on Kaggle — seven silvers and six bronzes across NLP, CV, multimodal, and matching. Competitions keep me honest because there's no hiding behind a slide; either your approach scores or it doesn't, and you're forced to adopt whatever's actually state of the art that month.

And the loop closes at work — when post-training tooling moved, I went hands-on with the current stack: Megatron-LM, DeepSpeed ZeRO, FSDP, and the vLLM/SGLang serving side. So my learning isn't passive; it's read the source, teach it, prove it, ship it."

延伸: "A recent concrete example: reading the on-device quantization literature is exactly what let me reason about the cloud-to-device shift for this role instead of hand-waving — that's the loop working in real time."

## 🇨🇳 中文要点 (理解 + 记忆骨架)

- **总纲一句**: 具体来源 + **学了就变成输出** (不只是读)。三个 channel。
- **Channel 1 — 一手来源 > 热评**: 读真正的 tech report / 论文 / model card, 包括 **Apple 自己 2025 的 on-device 报告** (所以我能具体讲 rank-16 adapter / 2-bit 量化)。读源不读 thread, 因为关键的 tradeoff/ablation 只在原文里。
- **Channel 2 — 教 = 逼自己真懂**: 三个内部 talk — "LLM Strategy & Roadmap for Payments" / "Agent Harness & Long-Horizon RL" / "GPU/TPU/LPU Tradeoffs for GenAI Inference"。备课是我最高带宽的学习方式 (讲 inference 硬件取舍没法含糊, 逼知识变得真实且结构化)。
- **Channel 3 — 竞赛保持手感**: Kaggle global **top 1%, 7 银 6 铜** (NLP/CV/multimodal/matching)。竞赛不能靠 slide 糊弄, 要么 score 要么不 score, 逼你用当月真正 SOTA 的方法。
- **闭环落到工作**: post-training 工具链变了 → 我上手当前 stack (Megatron-LM / DeepSpeed ZeRO / FSDP / vLLM / SGLang)。
- **杀手句**: **"read the source, teach it, prove it, ship it"** (读源→教→验证→落地)。
- 延伸: 最近的例子 = 读 on-device 量化文献正是我能为这个岗位 reason cloud→device 而非空谈的原因 (loop 实时在转, 自然衔接 Q26)。
- 记忆钩子: **"一手源 / 三个talk / Kaggle 7银6铜 / 读-教-验-用"**。

## 🔬 深挖追问 + 答法 (面试官会顺着钻)

**Q: What's a recent paper or development that changed how you do something?**
"The on-device efficiency line of work — quantization-aware training at very low bit-widths and KV-cache sharing. It reframed how I think about the latency-quality-memory triangle: I used to treat memory as a given and optimize latency and quality against it, and that literature pushed me to treat memory itself as something you attack with QAT and cache reuse. Concretely, it's what let me map my time-to-first-audio work onto the on-device prefill problem instead of seeing them as unrelated. [✏️ 核实 — 可换成你最近真读、真改变做法的一篇]"

**Q: The field moves fast — how do you decide what's worth learning versus hype?**
"I filter by whether it changes a decision I actually make. A lot of releases are incremental and I just note them. I go deep when something shifts a real tradeoff — a serving technique that changes my cost-latency curve, or a post-training method that changes my data strategy. Competitions and shipping are the filter: if a technique doesn't help me score or ship, the hype doesn't survive contact. I'd rather be deep on the ten things that move my work than shallow on a hundred headlines."

**Q: How do you keep a team current, not just yourself?**
"That's what the internal talks are for — I don't keep learning to myself. When I dig into something that matters for our roadmap, I write it up and present it, so the team levels up together and we make decisions from shared, current understanding. Knowledge that stays in one head is fragile; a talk plus a doc makes it the team's."

## ⚠️ 边界 & 红线 (honest limits + what NOT to say)

- **绝不说空话**。"我看 arXiv / 刷 Twitter / 听播客" 这种谁都能讲的, 单独说毫无信号。必须配具体名字 (talk 标题 / Kaggle 战绩 / 具体 stack)。
- "最近一篇 paper" 那个追问大概率会被问 — **提前准备一个你真读过、真改变做法的具体例子**, 别临场编。可以是 on-device 量化, 也可以换成你近期真读的。编一篇会被钻到穿帮。
- 别把学习说成纯输入。Apple 要 practitioner 不要 consumer → 一定要有 "输出" (教/赛/落地) 这一半。
- 提 Apple 自己的报告时, 只引公开内容, 姿态是 "我认真读过你们的工作" (加分), 不是 "我比你们懂"。
- 别让三个 talk 听起来像 "为了简历刷的"。框成 "备课是我的学习方式", 动机是学不是秀。

## ✅ 加分钩子 (主动抛, steer 到强项)

- **读过 Apple 自己的 2025 报告** — 这是全场最高性价比钩子: 既证明 "我读一手源" 的习惯真实, 又证明 "我为这次面试做了功课、真的想来", 还天然接到 Q26 的 on-device 技术细节。务必主动抛。
- **"教 = 学" + 三个 talk 标题** — 主动报标题, 尤其 "Agent Harness & Long-Horizon RL" 和 "GPU/TPU/LPU Tradeoffs", 直接展示 agent + inference 双重深度, 命中 JD 的 multi-agent orchestration 和 latency/cost 重点。
- **Kaggle top 1% (7S6B)** — 这是 resume-real 的硬数字, 大方报。它独立证明了 "持续保持 SOTA 手感" 且跨 NLP/CV/multimodal, 是很难造假的可信信号。
- **"read-teach-prove-ship" 闭环** — 主动抛这句框架, 把自己定位成 "学了就落地" 的人, 正好呼应 Apple 这个 research↔product 中间带岗位 (衔接 Q29)。
