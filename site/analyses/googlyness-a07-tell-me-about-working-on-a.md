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

## 🇨🇳 中文速记 (结构记忆)

做第 2 市场发现重写同构代码 → 看见所有团队将重复造轮子 → Agent Platform 提案 (编排/工具/记忆/可观测/eval); 先拉 2 个共建团队再 pitch; 成为 Global Payment 共享底座. 习惯: 第二次写同样代码就问该不该做平台.

## 🔁 高概率追问

**Q: How did you justify the extra scope?**

I didn't ask permission to explore — time-boxed the design doc, proved demand with co-sponsors, then brought a de-risked proposal. Leaders fund demand, not dreams.
