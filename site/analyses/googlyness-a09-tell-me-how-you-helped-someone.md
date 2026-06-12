# 🟡 G9 · Tell me how you helped someone in your team get better at some task.

> **信号**: 教练能力 · scaling others · **hellointerview 报告数**: 1
> ⚠️ 标 [✏️] 的数字是占位, 背诵前换成你的真实数据.

## 🧠 这题在测什么

与 Q21 区分: 这题是『一项具体技能』的提升过程 — 给教学机制, 不是泛指导.

## 📋 English Answer (背诵稿, ~60-90 秒)

A junior engineer on the team was iterating prompts by feel — tweak, eyeball three outputs, ship. His changes sometimes regressed cases we'd already fixed, and he couldn't tell which edits genuinely helped.
I skipped the lecture on evaluation best practices. Instead we rebuilt his workflow around one of his real tasks: we took a recent regression and wrote a couple dozen test cases together from production transcripts [✏️ 数量核实] — including the edge cases that had burned us — then set up a small eval harness so every prompt change produced a before/after score instead of an impression.
The teaching move that mattered: I had him *predict* the score before each run. Whenever prediction and result diverged, that gap was the lesson — it calibrated his intuition instead of replacing it with my rules.
Within a couple of months he was the one demanding eval coverage in design reviews, and he built the regression suite for his own market's workflows. My principle: don't hand people conclusions, hand them a feedback loop — the loop keeps teaching when you're not in the room.

## 🇨🇳 中文完整版 (口播稿, ~60-90 秒)

团队里一个 junior 工程师调 prompt 全凭感觉 — 改一下, 肉眼看三个输出, 上线. 他的改动时不时把我们已经修好的 case 打回退, 而且他说不清哪些改动真的有效.
我没有给他上「评估最佳实践」课, 而是围绕他手头的真实任务重建工作流: 我们拿一个最近的回归, 一起从生产 transcript 里写了二十多条测试 case [✏️ 数量核实] — 包括烫过我们的边角 case — 然后搭了个小 eval harness, 让每次 prompt 改动都产出前后分数, 而不是一个印象.
真正起作用的教学动作: 我让他每次跑之前先「预测」分数. 预测和结果出现偏差的时刻, 就是学习时刻 — 这把他的直觉校准了, 而不是用我的规则替换掉.
两个月左右, 他成了 design review 里主动要求 eval 覆盖的人, 还给他自己市场的 workflow 建了回归套件. 我的原则: 不要递给别人结论, 递给他一个反馈回路 — 你不在场的时候, 回路还在教他.

## 🇨🇳 中文速记 (结构记忆)

Junior 凭感觉调 prompt 反复回归; 用他的真实任务共建 20+ 条 production case 小 eval; 关键: 每次先预测分数, 预测≠结果就是学习时刻; 2 个月后他主动在 review 要 eval. 原则: 给回路不给结论.

## 🔁 高概率追问

**Q: How would you coach someone senior to you?**

Same loop, inverted framing: I bring the harness and ask them to help me interpret the results. Senior people adopt tools faster than they adopt advice.
