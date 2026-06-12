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

## 🇨🇳 中文完整版 (口播稿, ~60-90 秒)

早期做 voice agent 的时候, 我和一位 senior 工程师在部署架构上有真实的分歧. 他主张 7 个市场共用一个 service — 一套代码, 运维简单. 我认为必须按市场分开部署: 各市场监管约束不同, 印尼的紧急修复不应该排在别的市场的 QA 后面等发版.
我没有升级给老板, 而是提了一个一周的 time-boxed 实验: 影子环境跑分市场部署, 量化跨市场发版互相阻塞的情况. 我刻意把话术定为「让数据决定」, 而不是「我是对的」.
影子数据显示跨市场耦合确实在制造发版摩擦 [✏️ 次数核实]. 他认了 — 关键是我请他来共同设计迁移方案, 让这次重构是「我们的」, 不是「我赢了」. 最后保留共享库、拆分部署.
我反复复用的心得: 把架构分歧转化成便宜的实验, 并把方案的所有权分给对方. 这次冲突之后我们的合作反而比之前更好.

## 🇨🇳 中文速记 (结构记忆)

单体 vs 分市场部署; 提 1 周影子实验, '让数据决定'; 请对方共建迁移; 分歧→可验证实验 + 共同所有权.

## 🔁 高概率追问

**Q: Would you do anything differently?**

Surface it earlier — I let friction become visible before raising it. Now architecture concerns go into design review on day one.
