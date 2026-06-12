# 🟡 G19 · Tell me about a time you uncovered a significant problem in your team.

> **信号**: 洞察 · 测量怀疑精神 · **hellointerview 报告数**: 1
> ⚠️ 标 [✏️] 的数字是占位, 背诵前换成你的真实数据.

## 🧠 这题在测什么

测你对'看起来很好'的怀疑能力 — 最好是发现指标本身在说谎.

## 📋 English Answer (背诵稿, ~60-90 秒)

Our BNPL chatbot dashboard looked great — containment rate trending up, meaning fewer conversations escalated to humans. The team read it as success. Something felt off to me: complaints weren't falling in proportion.
So I did the unglamorous thing — sampled raw transcripts from "contained" conversations, the supposedly successful pile, and read them. A non-trivial share were conversations the bot *should* have escalated but didn't: it answered confidently, the user gave up and left, and the metric recorded a win [✏️ 比例核实]. Containment was counting silent failures as successes — our north-star metric had a blind spot exactly where the product hurt most.
I brought transcripts, not just numbers, to the metric review — three verbatim conversations are more persuasive than any chart. We then added correct-action rate as a primary metric, scored by sampled human review plus automated checks against backend state, and re-baselined the targets. Containment stayed as a guardrail, no longer the goal.
The general principle I took: any single success metric will eventually learn to lie. The antidote is regularly reading raw reality — transcripts, tickets, calls — behind your best-looking number.

## 🇨🇳 中文速记 (结构记忆)

Containment 上升像成功, 但投诉没同步降; 抽读'成功'对话 transcript → 相当比例是该转人工而没转、用户放弃离开被记为 win; 北极星指标在产品最痛处有盲区. 带 3 段原文 (比图表有说服力) 进 metric review → 加 correct-action 主指标, containment 降级护栏. 原则: 任何单一成功指标终将学会撒谎, 解药是定期读最好看数字背后的原始现实.

## 🔁 高概率追问

**Q: Why did you doubt a rising metric?**

Conservation check — if containment was truly up, complaint volume should fall roughly in step. When two numbers that should move together don't, one of them is lying.
