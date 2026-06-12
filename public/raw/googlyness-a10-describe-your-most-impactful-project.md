# 🟡 G10 · Describe your most impactful project.

> **信号**: Ownership · 规模化 impact · **hellointerview 报告数**: 1
> ⚠️ 标 [✏️] 的数字是占位, 背诵前换成你的真实数据.

## 🧠 这题在测什么

选 impact 最大且 ownership 最清晰的. 与 Q20 (most proud) 必须用不同项目.

## 📋 English Answer (背诵稿, ~60-90 秒)

The debt-collection voice agent — a real-time, multilingual production voice AI deployed across 7 markets in Asia, and the largest end-to-end scope I've owned.
The problem: human collection calls are expensive, inconsistent, and hard to scale across languages and compliance regimes. I led algorithm design and delivery across the full stack — streaming ASR, TTS and VAD on the speech side; an LLM dialogue policy with tool orchestration in the middle; and underneath it, the foundation-model post-training pipeline: data construction, multilingual domain adaptation, SFT, DPO-style alignment, evaluation-driven iteration. I applied RL-style optimization over multi-step workflows for long-horizon decision quality, and led the streaming-architecture upgrades for latency and interruption handling.
Impact landed in three layers. Business: automation rate and repayment conversion improved across markets [✏️ 填真实数字]. Technical: the post-training and vLLM/SGLang serving pipeline became reusable infrastructure. Organizational: the patterns we proved — eval harnesses, agent orchestration — seeded the internal Agent Platform other teams now build on.
It's the project where I ran the whole spectrum: GPU serving optimization one day, weekly syncs with regional business teams the next.

## 🇨🇳 中文完整版 (口播稿, ~60-90 秒)

催收 voice agent — 一个实时、多语种的生产语音 AI, 部署在亚洲 7 个市场, 也是我 own 过的最大端到端 scope.
问题本身: 人工催收电话贵、不一致、跨语言跨合规难规模化. 我主导了全栈的算法设计和交付 — 语音侧的流式 ASR、TTS、VAD; 中间的 LLM 对话策略和工具编排; 底层的基础模型 post-training pipeline: 数据构建、多语种领域适配、SFT、DPO 风格对齐、评估驱动迭代. 我还在多步 workflow 上做了 RL 式优化 (长程 credit assignment 提升决策质量), 并主导了延迟和打断处理的 streaming 架构升级.
Impact 在三层: 业务 — 各市场自动化率和回款转化提升 [✏️ 填真实数字]; 技术 — post-training 和 vLLM/SGLang serving pipeline 变成了可复用基础设施; 组织 — 我们验证过的模式 (eval harness、agent 编排) 孵化了内部 Agent Platform, 其他团队现在在上面构建.
这是我真正跑完全谱的项目: 这天在调 GPU serving, 第二天在和区域业务团队开周会.

## 🇨🇳 中文速记 (结构记忆)

7 市场实时多语种 voice agent, 最大全栈 ownership: 语音层+LLM策略+工具编排+post-training (SFT/DPO/RL)+streaming+serving. 三层 impact: 业务(自动化/回款) / 技术(可复用 pipeline) / 组织(孵化 Agent Platform).

## 🔁 高概率追问

**Q: What was the hardest part?**

Not the models — the latency-quality-compliance triangle in production. Each market pulled it differently, which is why per-market config and the eval harness mattered more than any single model gain.
