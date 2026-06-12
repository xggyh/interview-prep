# 🟡 G25 · Share an example where you resolved a significant conflict between different teams.

> **信号**: 跨团队调解 · 机制设计 · **hellointerview 报告数**: 1
> ⚠️ 标 [✏️] 的数字是占位, 背诵前换成你的真实数据.

## 🧠 这题在测什么

与 Q11 区分: 你不是冲突方而是调解者/架构者 — 解法应是机制而非说服.

## 📋 English Answer (背诵稿, ~60-90 秒)

Automating refunds in the BNPL chatbot triggered a standoff between two teams I sat between. The payments backend team refused to expose write-access to refund APIs for an LLM-driven system — from their seat, entirely rational: they own the ledger, and a hallucinated refund is their incident. Product, meanwhile, had automation targets that were meaningless without exactly that access. Weeks of meetings restated positions; both sides were right, which is what made it stuck.
My read: this wasn't a persuasion problem, it was a missing-mechanism problem — "access yes or no" was the wrong question. I designed a middle artifact: tiered execution. The agent gets no raw API access; instead, a constrained execution layer where small, rule-validated refunds auto-execute with idempotency keys and full audit trails; mid-tier amounts run agent-prepared but human-confirmed; anything large or anomalous routes to humans with the case pre-assembled [✏️ 阈值核实]. Backend co-designed the validation rules — their veto became executable code instead of a meeting position.
Both teams got their real need: backend kept deterministic control of the ledger; product got automation on the volume that mattered.
My takeaway for team conflicts: when both sides are right, stop arbitrating and design the mechanism that makes both constraints simultaneously true.

## 🇨🇳 中文速记 (结构记忆)

后端拒绝给 LLM 退款写权限 (幻觉退款=他们的事故) vs product 自动化指标. 判断: 不是说服问题是机制缺失. 设计分层执行: 小额规则校验自动执行(幂等+审计) / 中额 agent 备好人确认 / 大额异常转人工; 后端共建校验规则 — 否决权变成可执行代码. 金句: 双方都对时, 停止仲裁, 设计让两个约束同时为真的机制.

## 🔁 高概率追问

**Q: Why did backend trust the mechanism?**

Because they wrote its rules — the validation layer was their code, their thresholds, their kill switch. Trust came from control, not promises.
