# 🟡 G16 · Tell me about a time you had to pivot mid-project.

> **信号**: 适应性 · 抗沉没成本 · **hellointerview 报告数**: 2
> ⚠️ 标 [✏️] 的数字是占位, 背诵前换成你的真实数据.

## 🧠 这题在测什么

看你靠什么信号识别'方向错了', 以及 pivot 时怎么保住已有投入.

## 📋 English Answer (背诵稿, ~60-90 秒)

The first BNPL chatbot prototype was a free-form agent loop — one capable LLM with tools, reasoning through any request end-to-end. Demos looked fantastic. Then we built the evaluation harness, and it told a different story: on high-frequency transactional intents like refunds and order lookups, the free-form agent's correct-action rate was nowhere near what money-touching operations demand, and its failures were unpredictable — different wrong answers to the same input [✏️ 数字核实].
The pivot signal for me wasn't one bad demo — it was the eval distribution: unbounded variance on bounded tasks. So mid-project, I restructured the architecture: an intent classifier routing recognized intents to *dedicated workflow sub-agents* — deterministic, auditable state machines for refunds, disputes, order lookup — while genuinely open-ended questions flowed through a FAQ RAG path. The free-form loop didn't die; it got demoted from "the system" to one mode within it.
Crucially, the pivot preserved most prior investment: tool integrations, prompts and eval cases all carried over — we changed the control plane, not the parts.
My takeaway: build the eval harness early precisely so a pivot is a data decision, not a confidence crisis — and pivot the architecture, not the team's morale.

## 🇨🇳 中文完整版 (口播稿, ~60-90 秒)

BNPL chatbot 第一版原型是一个自由 agent loop — 一个强模型带工具, 端到端推理任何请求. Demo 非常惊艳. 然后我们建了 eval harness, 它讲了另一个故事: 在退款、订单查询这类高频交易型意图上, 自由 agent 的 correct-action rate 远达不到动钱操作的要求, 而且失败是不可预测的 — 同样输入给出不同的错误答案 [✏️ 数字核实].
对我来说 pivot 的信号不是某次糟糕的 demo, 而是 eval 的分布: 有界任务上的无界方差. 所以项目中途我重构了架构: intent 分类器把已识别意图路由到「专用 workflow 子 agent」— 退款、争议、订单查询走确定性、可审计的状态机 — 真正开放式的问题走 FAQ RAG 路径. 自由 loop 没有死, 它从「整个系统」降级成了系统里的一种模式.
关键是这次 pivot 保住了大部分已有投入: 工具集成、prompt、eval case 全部沿用 — 我们换的是控制面, 不是零件.
我的心得: 尽早建 eval harness, 正是为了让 pivot 成为一个数据决策, 而不是一场信心危机 — 并且 pivot 架构, 不 pivot 团队士气.

## 🇨🇳 中文速记 (结构记忆)

自由 agent loop demo 惊艳但 eval 揭示: 交易类意图 correct-action 不达动钱标准+失败不可预测. 信号=有界任务上的无界方差. Pivot 到 intent router+workflow 子agent+RAG 路径; 自由 loop 降级为一种模式. 工具/prompt/eval 全保留 — 换控制面不换零件.

## 🔁 高概率追问

**Q: How did you sell the pivot to stakeholders?**

With the eval data and a cost frame: two weeks of rearchitecting versus an unbounded stream of money-touching incidents. The harness made it an obvious call.
