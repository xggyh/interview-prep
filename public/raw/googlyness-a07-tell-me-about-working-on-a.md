# 🟡 G7 · Tell me about working on a goal and seeing an opportunity to deliver beyond it.

> **信号**: Think bigger · 平台思维 · **hellointerview 报告数**: 1
> ⚠️ 标 [✏️] 的数字是占位, 背诵前换成你的真实数据.

## 🧠 这题在测什么

测平台思维: 做 N 时看见 10N, 且推进方式是 de-risked 的 (不是擅自扩 scope).

## 📋 English Answer (背诵稿, ~60-90 秒)

While shipping the BNPL chatbot's second market, I caught myself writing nearly the same orchestration and policy code I'd written for the first — different thresholds, same structure. The assigned goal was "launch market two." But the pattern was obvious: every future market, and every agent any team in Global Payment would build, was going to re-solve workflow orchestration, tool integration, memory, observability and evaluation from scratch.
So beyond the launch, I drafted a proposal for an internal Agent Platform: extract those five concerns into shared infrastructure with per-team configuration on top. Before pitching leadership, I recruited two other teams with concrete use cases as co-sponsors — so it landed as proven demand, not a solo vision doc.
I co-designed the platform as algorithm POC, and it became the shared foundation for cross-team GenAI rollouts across Global Payment [✏️ 接入团队数核实].
The habit behind it: the second time I write structurally identical code for different stakeholders, I stop and ask whether the real deliverable is a platform. And I de-risk the bigger bet before asking anyone to fund it.

## 🇨🇳 中文完整版 (口播稿, ~60-90 秒)

做 BNPL chatbot 第二个市场的时候, 我发现自己在写和第一个市场结构几乎一样的编排和政策代码 — 阈值不同, 骨架相同. 分配给我的目标是「上线第二个市场」, 但模式已经很明显: 未来每个市场、以及 Global Payment 任何团队要做 agent, 都会从头解一遍同样的问题 — workflow 编排、工具集成、记忆、可观测、评估.
所以在交付市场之外, 我起草了内部 Agent Platform 的提案: 把这五件事抽成共享基础设施, 每个团队在上面只做配置. Pitch 给 leadership 之前, 我先找了两个有具体用例的团队做 co-sponsor — 所以提案落地时是「已验证的需求」, 不是一个人的愿景文档.
我以算法 POC 身份共同设计了这个平台, 它后来成了 Global Payment 跨团队 GenAI 落地的共享底座 [✏️ 接入团队数核实].
背后的习惯: 第二次为不同 stakeholder 写结构相同的代码时, 我就停下来问 — 真正的交付物是不是一个平台? 并且在要任何资源之前, 先把更大的赌注去风险化.

## 🇨🇳 中文速记 (结构记忆)

做第 2 市场发现重写同构代码 → 看见所有团队将重复造轮子 → Agent Platform 提案 (编排/工具/记忆/可观测/eval); 先拉 2 个共建团队再 pitch; 成为 Global Payment 共享底座. 习惯: 第二次写同样代码就问该不该做平台.

## 🔁 高概率追问

**Q: How did you justify the extra scope?**

I didn't ask permission to explore — time-boxed the design doc, proved demand with co-sponsors, then brought a de-risked proposal. Leaders fund demand, not dreams.
