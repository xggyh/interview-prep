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

## 🇨🇳 中文完整版 (口播稿, ~60-90 秒)

BNPL chatbot 要自动化退款时, 我夹在两个团队的对峙中间. 支付后端团队拒绝把退款 API 的写权限开给一个 LLM 驱动的系统 — 从他们的位置看完全理性: 账本是他们的, 一次幻觉退款就是他们的事故. 而 product 背着自动化指标, 没有这个权限指标毫无意义. 几周的会都在重复立场; 两边都是对的, 这正是僵住的原因.
我的判断: 这不是说服问题, 是机制缺失问题 —「给不给权限」本身就是错的问题. 我设计了一个中间产物: 分层执行. Agent 拿不到裸 API; 取而代之是一个受约束的执行层 — 小额、规则校验通过的退款自动执行, 带幂等键和完整审计; 中等金额由 agent 备好、人来确认; 大额或异常的直接转人工, case 已经预组装好 [✏️ 阈值核实]. 校验规则由后端共同设计 — 他们的否决权从会议立场变成了可执行的代码.
两个团队都拿到了真正想要的: 后端保住了对账本的确定性控制; product 拿到了主体流量的自动化.
我对团队间冲突的心得: 当双方都对的时候, 停止仲裁, 去设计那个让两个约束同时为真的机制.

## 🇨🇳 中文速记 (结构记忆)

后端拒绝给 LLM 退款写权限 (幻觉退款=他们的事故) vs product 自动化指标. 判断: 不是说服问题是机制缺失. 设计分层执行: 小额规则校验自动执行(幂等+审计) / 中额 agent 备好人确认 / 大额异常转人工; 后端共建校验规则 — 否决权变成可执行代码. 金句: 双方都对时, 停止仲裁, 设计让两个约束同时为真的机制.

## 🔁 高概率追问

**Q: Why did backend trust the mechanism?**

Because they wrote its rules — the validation layer was their code, their thresholds, their kill switch. Trust came from control, not promises.
