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

## 🇨🇳 中文速记 (结构记忆)

Junior 凭感觉调 prompt 反复回归; 用他的真实任务共建 20+ 条 production case 小 eval; 关键: 每次先预测分数, 预测≠结果就是学习时刻; 2 个月后他主动在 review 要 eval. 原则: 给回路不给结论.

## 🔁 高概率追问

**Q: How would you coach someone senior to you?**

Same loop, inverted framing: I bring the harness and ask them to help me interpret the results. Senior people adopt tools faster than they adopt advice.
