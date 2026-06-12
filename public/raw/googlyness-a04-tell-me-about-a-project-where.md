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

## 🇨🇳 中文完整版 (口播稿, ~60-90 秒)

BNPL chatbot 立项时需求只有一句话:「让客服更智能」. 每个 stakeholder 的理解都不一样 — ops 要减工单, product 要自助退款, 合规要零违规. 而且需求是真的在持续变, 因为各市场退款规则和监管预期都不同.
我做了两件事. 第一, 便宜的地方强制澄清: 我拉了真实工单数据, 证明少数几个意图覆盖了大部分流量 [✏️ 比例核实], 然后让三方对齐了三个首发意图和明确的成功指标 — task completion 和 correct-action rate, 而不是只看挡了多少工单.
第二, 让架构去吸收变化而不是对抗变化: intent router 在前, 后面挂可替换的 workflow 子 agent, 所有市场政策放在 config 和 RAG 知识库里 — 不进代码, 不进模型权重. 某市场改退款窗口, 就是改配置和文档, 不用重训不用重新部署.
需求一直在变, 但系统不在乎了. 这就是我对模糊性的通用打法: 便宜的就澄清, 澄清不了的就用架构吸收.

## 🇨🇳 中文速记 (结构记忆)

'更智能客服'一句话需求; ticket 数据收敛 3 意图+对齐指标; 架构吸收变化: router+子agent, 政策进 config/RAG 不进权重. 金句: 需求一直变, 系统不在乎.

## 🔁 高概率追问

**Q: How did you keep stakeholders aligned through changes?**

A standing weekly review against the agreed metric set — changes were welcome but entered through the metrics conversation, not side channels.
