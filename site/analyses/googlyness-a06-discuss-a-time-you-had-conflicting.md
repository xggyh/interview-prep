# 🟡 G6 · Discuss a time you had conflicting perspectives with teammates and how you handled it.

> **信号**: 多方合成 · 指标思维 · **hellointerview 报告数**: 3
> ⚠️ 标 [✏️] 的数字是占位, 背诵前换成你的真实数据.

## 🧠 这题在测什么

与 Q1 区分: 多方观点 (不止两人对立), 看合成能力而非裁决能力.

## 📋 English Answer (背诵稿, ~60-90 秒)

Defining success metrics for the BNPL chatbot split the room three ways. Product pushed containment — fewer human transfers. Ops pushed safety — a wrong automated action creates a dispute that costs more than the ticket it saved. Engineering pushed automation coverage — more intents handled end-to-end.
Each metric alone was gameable: maximize containment and the bot refuses to escalate when it should; maximize safety and it escalates everything; maximize coverage and long-tail quality collapses.
Instead of arbitrating whose number wins, I reframed the question: what does one *successful conversation* require? The task completed, the action taken was correct, no policy violated, the user didn't bounce back. So I proposed a metric system — task completion and correct-action rate as primary, containment and violation rate as guardrails — and built the evaluation harness so every release reports all four together.
The conflict dissolved because nobody lost: each team's concern became a tracked dimension rather than a competing goal. My reusable lesson: when smart people fight over metrics, the answer is usually a vector, not a scalar.

## 🇨🇳 中文速记 (结构记忆)

指标三方之争 (containment/安全/覆盖率), 单指标皆可 game; 重构为'一次成功对话需要什么' → 指标系统: completion+correct-action 主, containment+violation 护栏; eval harness 同屏出. 金句: 吵指标的答案是向量不是标量.

## 🔁 高概率追问

**Q: Who owned the final definition?**

I drove the framework but had product own the primary-metric wording — people defend what they co-author.
