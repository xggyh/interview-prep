# 🟡 G26 · Tell me about an important decision between two strong options.

> **信号**: 决策框架 · 可逆性思维 · **hellointerview 报告数**: 1
> ⚠️ 标 [✏️] 的数字是占位, 背诵前换成你的真实数据.

## 🧠 这题在测什么

两个选项必须都真有吸引力; 评分点在决策框架 (准则+可逆性+触发器) 而非结论.

## 📋 English Answer (背诵稿, ~60-90 秒)

For the voice agent's dialogue model we faced a genuine fork: self-host a fine-tuned model on our own GPUs with vLLM, or build on a vendor LLM API. Both were strong. Self-hosting gave us domain-adapted quality from our post-training pipeline, full data control for sensitive payment conversations, and a better cost curve at our call volume. The API gave faster iteration, zero serving ops, and automatic model upgrades.
Rather than debating taste, I scored both against weighted criteria: latency floor — a real-time voice call has a hard conversational budget, and an extra network hop plus queueing risk eats it; data sensitivity — collection conversations are regulated and market-specific; volume economics at our scale; and team capability — we already ran GPU inference infrastructure, so ops cost was marginal, not new.
We chose self-hosted serving for the core dialogue policy — latency and data control were the two criteria that were *irreversible* at runtime — while keeping API access for low-volume internal tooling where iteration speed dominates. I also defined exit triggers upfront: if our model's quality gap versus frontier APIs widened past our eval threshold, we'd revisit rather than ride sunk costs.
That's my decision pattern: weighted criteria, decide by what's irreversible, and pre-commit the conditions for changing your mind. I later turned this analysis into an internal talk on GPU/TPU/LPU inference tradeoffs.

## 🇨🇳 中文速记 (结构记忆)

自托管 fine-tuned (vLLM) vs vendor API, 两边都强. 加权准则: latency 硬预算 (实时语音) / 数据敏感 (催收对话受监管) / 量级经济性 / 团队已有 GPU 能力. 选自托管做核心对话 (latency+数据控制是运行时不可逆项), API 留给低量内部工具; 预设退出触发器 (质量差距过 eval 阈值就重审). 模式: 加权准则+按不可逆性决策+预先承诺改变心意的条件. 衍生成 GPU/TPU/LPU talk.

## 🔁 高概率追问

**Q: Has the decision held up?**

The exit trigger is the real answer — we re-evaluate against frontier APIs on our eval set periodically, so it keeps re-earning its place instead of surviving on sunk cost.
