# 🟡 G17 · Tell me about a conflict with your manager where you were wrong.

> **信号**: 谦逊 (Googlyness 核心) · 可被说服 · **hellointerview 报告数**: 1
> ⚠️ 标 [✏️] 的数字是占位, 背诵前换成你的真实数据.

## 🧠 这题在测什么

真正的谦逊题: 必须是你确实错了 + 错误如何更新了你的判断框架. 别选伪错误.

## 📋 English Answer (背诵稿, ~60-90 秒)

Early in the BNPL chatbot, my manager pushed for shipping rule-based handling for the top intents first, with the LLM handling only the long tail. I pushed back hard — I argued rules were legacy thinking, the LLM could cover everything, and maintaining two stacks was waste. We went back and forth across a couple of design reviews; he eventually let me try it my way with a deadline.
He was right. The LLM-everything path burned weeks on edge-case whack-a-mole for intents that a deterministic flow would have handled trivially, and our launch risk grew instead of shrinking. The moment I conceded was seeing the incident projection for money-touching flows: the variance was simply not acceptable for refunds, whatever the demo looked like.
I told him directly: "You were right, I optimized for elegance over reliability." We shipped the hybrid — and the irony is that the architecture I now advocate everywhere, deterministic workflows for known intents with the LLM scoped to the open-ended residue, is essentially his position from that argument, refined.
What it changed in me: when I feel strong technical conviction, I now ask "what would have to be true for the other side to be right" — and try to get that evidence *before* spending the team's weeks on my elegance.

## 🇨🇳 中文速记 (结构记忆)

经理主张规则先行+LLM 兜长尾, 我坚持 LLM 全覆盖; 试了我的方案→edge case 打地鼠+发版风险上升; 动钱流的方差预测让我认输. 当面认错; 如今到处倡导的 hybrid 架构本质是他当年立场的精炼. 改变: 有强烈技术信念时先找'对方正确需要什么证据'.

## 🔁 高概率追问

**Q: Why did you resist initially?**

Identity, honestly — I'd joined as the GenAI person and read 'rules first' as a vote against the new stack. Separating my craft identity from architecture decisions was the real lesson.
