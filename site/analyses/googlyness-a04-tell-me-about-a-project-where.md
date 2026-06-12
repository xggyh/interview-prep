# 🟡 G4 · Tell me about a project where the requirements were not clear or kept changing.

> **信号**: 模糊容忍 · 结构化能力 · **hellointerview 报告数**: 3
> ⚠️ 标 [✏️] 的数字是占位, 背诵前换成你的真实数据.

## 🧠 这题在测什么

Googlyness 核心信号 thrive-in-ambiguity: 你是抱怨需求变, 还是让架构吸收变化.

## 📋 English Answer (背诵稿, ~60-90 秒)

The BNPL chatbot began as a one-line ask: "make customer support smarter." Every stakeholder meant something different — ops wanted fewer tickets, product wanted self-service refunds, compliance wanted zero policy violations. And the requirements genuinely kept moving, because each market had different refund rules and regulatory expectations.
I did two things. Where clarity was cheap, I forced it: I pulled real ticket data, showed that a small set of intents covered most volume [✏️ 比例核实], and got all three stakeholders to agree on three launch intents plus explicit success metrics — task completion and correct-action rate, not just deflection.
Where clarity was impossible, I made the architecture absorb change instead: an intent router in front of swappable workflow sub-agents, with every per-market policy living in config and RAG knowledge bases — never in code, never in model weights. When a market changed its refund window, that was a config-and-document edit, not a retrain or redeploy.
Requirements never stopped changing. The system stopped caring. That's my general approach: clarify what's cheap to clarify, architect for what isn't.

## 🇨🇳 中文速记 (结构记忆)

'更智能客服'一句话需求; ticket 数据收敛 3 意图+对齐指标; 架构吸收变化: router+子agent, 政策进 config/RAG 不进权重. 金句: 需求一直变, 系统不在乎.

## 🔁 高概率追问

**Q: How did you keep stakeholders aligned through changes?**

A standing weekly review against the agreed metric set — changes were welcome but entered through the metrics conversation, not side channels.
