# 🟡 G1 · Tell me about a conflict you had at work.

> **信号**: 协作 · 谦逊 · 数据 > 层级 · **hellointerview 报告数**: 6
> ⚠️ 标 [✏️] 的数字是占位, 背诵前换成你的真实数据.

## 🧠 这题在测什么

页面思路: 面试官关注的是『执行方式上的观点冲突』(不是人际矛盾). 评分点: 你怎么把对立降级成可验证实验, 以及事后关系.

## 📋 English Answer (背诵稿, ~60-90 秒)

Early in the voice-agent project I disagreed with a senior engineer about deployment architecture. He wanted one shared service for all 7 markets — one codebase, simpler ops. I believed per-market deployments were necessary: markets had different regulatory constraints, and an urgent fix for Indonesia shouldn't queue behind another market's QA.
Instead of escalating, I proposed a one-week, time-boxed experiment: run the per-market setup in shadow and measure release-blocking interference between markets. I framed it deliberately as "let the data decide," not "I'm right."
The shadow run showed cross-market coupling was creating real release friction [✏️ 次数核实]. He agreed — and I asked him to co-design the migration, so the refactor was ours, not my win. We kept shared libraries, split the deployments.
The takeaway I reuse constantly: convert architecture disagreements into cheap experiments, and hand the other person co-ownership of the outcome. We worked better together after that than before the conflict.

## 🇨🇳 中文速记 (结构记忆)

单体 vs 分市场部署; 提 1 周影子实验, '让数据决定'; 请对方共建迁移; 分歧→可验证实验 + 共同所有权.

## 🔁 高概率追问

**Q: Would you do anything differently?**

Surface it earlier — I let friction become visible before raising it. Now architecture concerns go into design review on day one.
