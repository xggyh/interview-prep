## 题目（verbatim）

> **[OpenAI / Anthropic Solution Design Round — 60 min, opener]**
>
> "Design a **complete AI solution** for a company's business problem. But first — **what questions would you ask the customer before designing anything?**
>
> Variant: 'A bank wants an AI agent for retail customer support. Where do you start?' / 'A pharma company wants AI for drug discovery workflow. Walk us through your first conversation with them.'"

**出处**: OpenAI FDE 真题. Palantir / Google Cloud / Databricks FDE 都问这类. **Skip clarifying = immediate fail** for FDE.

**Round**: Solution Design (60 min, 通常作为 round 开场或第一阶段)

---

## 这道题在考什么

这道题考的是 **FDE 灵魂**:

不 clarify 就 design = **vendor 思维**, 不是 **FDE 思维**.

**HM 在筛 5 件事**:

1. **Customer-first instinct** —— 你是否**本能**上 want to understand before solving
2. **Question structure** —— 你 ask 的 order 体现 prioritization 能力
3. **What you ask for** —— stakeholder / KPI / data / constraint / failure tolerance
4. **Pattern recognition** —— 你见过 enough deployment, 知道 what to verify
5. **Boundary** —— 不要 fish forever, eventually commit to solve

**没说出口的 anti-signal**:
- 上来就 design — 立刻 fail
- 问 20 个问题 — 显得不会 prioritize, customer 感觉被 interrogate
- 问没 "why" 的问题 — 显得问 checklist
- 把 KPI 当 nice-to-have — 显示不懂 FDE 工作
- 没 acceptable boundary — 一直 fish, 永远不 design

**这道题是 differentiator**: 通过率不到 30%, 因为大部分候选第一反应是 design.

---

# Part 1 · 教学讲解

## 1. 几个术语 / 概念先讲清

**Clarifying questions**: 在 design 之前向客户提的问题, 目的是把 ambiguous 的 ask 转化为可执行的 design.

**Discovery**: Clarifying 的延伸, 不只是问问题, 还包括 listening / observing / 跟 customer 的 user 接触.

**KPI lock**: 把客户的 vague success criteria 锁定到 specific measurable metric.

**Stakeholder map**: 列出所有 stakeholder + 他们的诉求 + 红线 + veto power.

**Failure tolerance**: 客户能承受多大的 wrong-answer rate / downtime / cost.

**Why this matters**: 每个 question 都要绑定 "为什么问这个" — 否则 customer 觉得 interrogate.

---

## 2. 这道题在考你什么 (深入)

### 表面 vs 深层

**表面**: 问 5-7 个 question

**深层** (HM 真正在筛):

| 信号 | 权重 | 怎么 demonstrate |
|---|---|---|
| **"我每次都先 clarify"** | ★★★★★ | 自然 reflex, 不是面试技巧 |
| **Question 顺序** | ★★★★★ | KPI 一定先, 不是 random list |
| **"Why I'm asking"** | ★★★★ | 每个问题绑定 reasoning |
| **5-7 question limit** | ★★★★ | 不 interrogate, 知道节制 |
| **Specific question wording** | ★★★★ | 不是 "what's the budget" 而是 "envelope for first 12 months" |
| **Listen for hidden ask** | ★★★ | 客户说 efficiency, 你 push 到 specific metric |
| **Strawman ready** | ★★★ | 如果客户嫌 ask 多, 你能立刻 sketch + flag 3 assumptions |
| **Commit to next step** | ★★ | 1-page proposal in 1 week, not 4 weeks |

### 5 类 question (FDE 必问)

| 类型 | 解锁的 design dimension | 通常问几个 |
|---|---|---|
| 1. **Business / KPI** | 设计目标 / 优化对象 | 2-3 |
| 2. **Stakeholders / Politics** | 谁批 / 谁 veto / 政治风险 | 2 |
| 3. **Constraints** | 部署环境 / 合规 / 时间预算 | 2-3 |
| 4. **Failure mode** | 错的容忍度 / fallback | 2 |
| 5. **Success criteria** | 时间窗 / demo / milestone | 2 |

Total: 10-12 questions across 5 categories. 但**第一次 conversation 只问 5-7**, 其他在 follow up 里 ask.

---

## 3. 问题顺序框架: BSCFS

**Order**: Business → Stakeholders → Constraints → Failure → Success

| 顺序 | 类型 | 为什么是这个顺序 |
|---|---|---|
| 1st | **B**usiness / KPI | 一切其他设计 optimize for 这个 metric. 没 lock KPI 就 design = wrong direction. |
| 2nd | **S**takeholders | 谁批 / 谁 veto / 谁是 funder, 决定 architecture 政治可行性. |
| 3rd | **C**onstraints | Deployment env / compliance / 数据 residency, 决定技术 stack. |
| 4th | **F**ailure | Wrong-answer 容忍度, 决定 architecture safety layer. |
| 5th | **S**uccess | Week-1 / month-1 / quarter-1 milestone, 决定 phased rollout. |

**关键 insight**: 顺序错 = waste. 比如先问 constraints, 你设计了完美的 on-prem solution, 然后发现 KPI 是 "low latency" 而 on-prem 高 latency, 全部白做.

---

## 4. 不同情境下的 question 偏重

| 情境 | 重点 question 类别 | Why |
|---|---|---|
| **Customer 第一次见你** | KPI + Stakeholder (前 2) | 不熟, 先 anchor 商业目标 + 政治环境 |
| **POC 已 done, design phase** | Constraints + Failure (3, 4) | 商业 already aligned, 现在落地细节 |
| **复购 / renewal** | Success + 上一阶段 retro | 看上一期 KPI 表现 + 决定下期方向 |
| **客户已有 vendor** | Stakeholder + Constraints | 谁是 incumbent + 为什么换 |
| **新行业 / 不熟客户** | KPI + 全部 5 类 (long discovery) | 你需要更多 context |
| **熟客户, similar use case** | 1-2 question + 直接 design | 不要 over-clarify |

---

## 5. 4-5 个真实场景演示

### 场景 A: TikTok PayLater Voice Agent (你的当前)

**Customer**: Indonesia ops team (内部, 但形态等同 external customer)
**Initial ask**: "我们想要 voice agent 做债务催收."

**5 类 question 走一遍**:

**B (Business / KPI)**:
> "如果 6 个月后 review 项目, 一个 metric 告诉你 '成功了', 你看什么 number?"
>
> Ops 答: "Repayment rate."
>
> 你 push: "Total repayment? 还是 outbound-call-led repayment? 还是 30-day cohort?"
>
> Ops: "Outbound-led repayment, 30-day cohort."
>
> 你: "Baseline 是 X%, target Y%?"
>
> Ops: "Baseline 12%, target 18% (1.5×)."
>
> **KPI lock**: 30-day cohort outbound-led repayment rate, baseline 12%, target 18%, measured monthly.

**S (Stakeholder)**:
> "谁是 sponsor? 谁能 veto deployment?"
>
> Ops: "Sponsor 是 Head of Credit Operations. Veto: Compliance team (OJK 合规) + IT (data residency)."
>
> 你: "Compliance 红线?"
>
> Ops: "不能 promise 减免, 不能 imply 法律行动, 不能在非 working hour 拨打."
>
> **设计影响**: Persona 必须按 OJK 文档过, working hour validator hard-coded, escalation 到人工不能自动 promise 减免.

**C (Constraints)**:
> "Deployment 必须在 Indonesia 数据中心吗?"
>
> Ops: "是. OJK 要求 customer data 不出印尼."
>
> 你: "目前 telephony provider?"
>
> Ops: "Twilio + 印尼本地 SIP."
>
> 你: "Inbound API 限制?"
>
> Ops: "100 concurrent calls peak, dial rate 必须 < 50/min."
>
> **设计影响**: Self-host model on Jakarta region, 不能用 OpenAI API. Telephony abstraction 必须支持本地 SIP fallback.

**F (Failure)**:
> "Worst case 是什么? 比如 voice agent 给错信息."
>
> Ops: "给错还款金额, 客户照交了, customer 投诉. 比 silent fail 更糟."
>
> 你: "可接受 wrong-info rate?"
>
> Ops: "< 0.5%."
>
> 你: "如果 ASR 不确定, 选项?"
>
> Ops: "宁愿 'please repeat' 5 次, 也不要 hallucinate."
>
> **设计影响**: Confidence threshold high, low confidence → re-prompt or escalate human, hallucination eval is gate.

**S (Success)**:
> "Week-1 launch 你看 dashboard 想看什么?"
>
> Ops: "Daily call volume, AHT (average handle time), customer hang-up rate."
>
> 你: "Month-1 success?"
>
> Ops: "Voice agent 处理 ≥ 30% volume, AHT < 4 min, hang-up < 15%."
>
> 你: "Quarter-1?"
>
> Ops: "Repayment rate measurable improvement, 至少 +2 percentage points vs baseline."
>
> **设计影响**: Phased rollout — week 1 shadow mode + manual review, week 2-4 ramp to 10/30/50% traffic.

**Outcome**: 这次 conversation 后我能立刻写 1-page design proposal. 因为 5 类 question 都 locked.

### 场景 B: BNPL Chatbot — 内部 product team

**Customer**: BNPL product team
**Initial ask**: "客服 chatbot, like ChatGPT 但 for our finance."

**Quick 5-question**:

> "(B) 6-month success metric?" → "Deflection rate (% inbound 不需 human)"
> "(B) Baseline + target?" → "0% (无 chatbot), target 50%"
> "(S) Decision maker? Veto power?" → "Product VP sponsor; Compliance + Risk veto; CS manager 怕替代"
> "(C) Deployment + integration?" → "Self-host, integrate with our customer service platform"
> "(F) Wrong-answer cost?" → "Compliance breach (promise 错额度) > customer 略不满意"

**Outcome**: 决定 tier-based design (1: FAQ no PII, 2: account-specific limited surface, 3: human escalation).

### 场景 C: 想象一个 OpenAI FDE 面试场景 — 银行客服 AI

**Interviewer scenario**: "A regional US bank wants an AI agent for retail customer support. Walk through your first 30 minutes with them."

**你 monologue**:

> "我会问 5 类 question, 在 5-7 个问题以内. 不会 interrogate.
>
> **(B) KPI**: 'If we review in 6 months and call it a success, what's the ONE metric we look at? Deflection rate, CSAT, AHT, or something else?'
>
> 我 expect 客户答 'efficiency / cost'. 我 push 到 specific — 'Tickets per hour or cost per ticket?' 通常客户会选 deflection (无 human 解决比例).
>
> **(B) Baseline**: 'Current deflection? My guess is 10-20% (industry typical with traditional FAQ chatbots). Right?'
>
> Anchor industry data 帮客户回答.
>
> **(S) Veto**: 'Beyond your team, who needs to approve this? Compliance, IT security, legal — usually all three for banks.'
>
> Banks always have 3 veto holders. 我 explicitly raise 让客户 confirm.
>
> **(C) Data**: 'What customer data can the AI access — account balance? Transactions? Profile? Are there fields like SSN / DOB the AI must NOT see?'
>
> 银行 data sensitivity 是 top-3 design driver.
>
> **(F) Failure tolerance**: 'What's worse — wrong info given to customer (and we audit later) or AI saying I dont know too often (escalation overhead)? Both have cost.'
>
> 银行通常选 'wrong info 更糟' — fines + reputation. 这驱动 confidence threshold high.
>
> **(S) Week-1 milestone**: 'What do you want to see in dashboards week 1? If we hit it, what becomes ambitious in month 3?'
>
> 把 success criteria phasing 出来.
>
> 5-7 questions, 30 min. 然后我会 commit 'I'll send a 1-page design proposal within 1 week, with 3 architecture options ranked by what we discussed.'"

### 场景 D: 假设一个 Anthropic FDE 面试场景 — 法律科技 AI

**Scenario**: "Law firm wants Claude to draft contracts. Walk us through."

**Tweaked 5-question** (法律行业特殊):

> "(B) Success metric: 'Drafting time reduction? Or accuracy of clauses? Or attorney satisfaction? Pick one as North Star.'
>
> (S) Veto: 'Partner-level sign-off for AI tool use? Bar association compliance?'
>
> (C) Confidentiality: 'Client data — never leave on-prem? Or can use AWS GovCloud / Anthropic Trust portal?'
>
> (F) Worst-case: 'AI drafts clause that exposes firm to malpractice. How do you want it gated — mandatory attorney review every draft, or risk-tier?'
>
> (S) Week-1: 'First use case — does AI draft from scratch or edit existing? Most firms start with edit (lower risk).'"

**核心**: 不同行业 question wording 不一样, 但 5 类 framework 一样.

### 场景 E: 假设一个 Palantir FDE 面试场景 — 制造业 ops

**Scenario**: "Manufacturing client wants AI to predict equipment failure."

**Tweaked 5-question** (Palantir 风格 — data + ontology):

> "(B) Success: 'Reduction in unplanned downtime? Or maintenance cost? Or specific equipment uptime %?'
>
> (S) Owners: 'Who owns the SCADA data? Who owns the maintenance ticket system? They usually aren't the same team — alignment needed.'
>
> (C) Data: 'Sensor data — historical depth? Frequency? Format (OPC UA / MQTT / SQL)? Maintenance log — structured or free text?'
>
> (F) False alarm cost: 'Predict failure that doesnt happen — wasted truck roll. Predict no failure but it happens — line down. Which is worse?'
>
> (S) Week-1: 'Top 5 equipment types covered? Pilot site selection?'"

**核心**: Palantir 不是 LLM-first, question 偏 data + ops, 跟 OpenAI / Anthropic 不同.

---

## 6. 回答 playbook (回答这道题的 60 秒结构)

**Step 1**: Frame 你的 approach (15 秒)
> "Before designing, I'd ask 5 categories of question in 5-7 questions total. Each question unlocks a different design dimension."

**Step 2**: 列 5 categories (20 秒)
> "Business / KPI first, then Stakeholders / politics, then Constraints (deployment + compliance), then Failure tolerance, then Success criteria phasing."

**Step 3**: 给一个 specific example category (15 秒)
> "Take KPI as example — I'd ask 'What's the ONE metric in 6 months that would tell you this worked?' If they say 'efficiency', I push to specific — 'Tickets per hour or cost per ticket?' I anchor to industry baseline if they're new."

**Step 4**: Pragmatic limit (10 秒)
> "5-7 questions max first session. More feels like interrogation. Remaining questions come up in follow-ups as we go."

**Step 5**: Commit next step (10 秒)
> "Then commit to 1-page design proposal within 1 week, not 4. Customer hates slow vendors."

Total: ~70 秒. HM 通常会 follow up 让你具体 demo.

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **上来直接 design** | Immediate fail for FDE |
| 2 | **问 20 个 question** | Customer 感觉 interrogate, 信任下降 |
| 3 | **问没 "why"** | 显得问 checklist, 不是 customer-first |
| 4 | **No prioritization** | 顺序混乱, 显示没经验 |
| 5 | **Accept vague KPI** | "Efficiency" 不 push 到 specific = waste |
| 6 | **不 acknowledge customer 不耐烦** | 显示 inflexible |
| 7 | **No commit to next step** | Questions 不 lead anywhere |
| 8 | **Generic question wording** | 不显示 pattern recognition |
| 9 | **没 reference points** | 客户不会答 "acceptable error rate", 你得给 anchor |
| 10 | **Treat question as one-way** | Should be conversation, listen + react |

---

## 一句话总结 (Part 1)

> **"What questions would you ask the customer first?" 真正的考点不是 question list, 是 "你能不能 instinct 上 prioritize, 用 5-7 个 high-leverage question 解锁所有 design dimension, 不 interrogate, 然后 commit to 1-page proposal in 1 week"**.
>
> 5 categories (BSCFS) + ordered + with "why" + pragmatic limit + commit next step = senior FDE clarifying.

---

# Part 2 · 5 个深度子问题

## ⚙️ Problem 1: Business / KPI Questions — The 6-month North Star

### 1.1 为什么 KPI 必须第一个问

每个 design decision optimize for 一个 metric. 不知道 metric = 设计 for the wrong thing.

具体例子:
- 客户说 "want AI customer support". 你 design CSAT-optimized → 复杂多步骤 dialog. 实际客户 KPI 是 deflection rate (越少人工越好) → 应该 design simple-then-escalate.
- 错 KPI 的 design 上线后 6 个月才发现, redo cost = 整个项目.

### 1.2 5-10 个 specific KPI question scripts

**Q1: The ONE metric**

> "If we review this project in 6 months and call it a success, what's the **ONE metric** we would look at?"

**为什么**: ONE forces prioritization. 客户经常说 "improve everything", 这是 anti-pattern. ONE 强迫 lock.

**Push back if vague**:
> "I hear 'improve everything'. Let me phrase differently — if the **only** dashboard change after 6 months is one number going up, **which number**?"

**Q2: Baseline**

> "What's the **current baseline** without our system? Do you have a number, or estimate?"

**为什么**: Without baseline, can't measure improvement. Customer 经常不知道, 这是 actionable next step.

**Handle "I don't know"**:
> "OK, baseline 是 step 1. 我可以下周帮你 instrument current process, 1 周后我们 lock baseline 数字. 这帮 future measurement."

**Q3: Threshold for success**

> "What number — at the 6-month mark — would you call **clear success**? What would be **stretch goal**? What would be **disappointment**?"

**为什么**: 3-tier (target / stretch / disappointment) 比单 number 更 robust. 客户更容易回答 range 不是 single point.

**Q4: The loser**

> "If this project succeeds, **who's the loser**? Whose job description changes? Whose budget gets reallocated?"

**为什么**: Successful AI deployment always reallocates someone's work. 不 acknowledge = 政治阻力 backfire.

**Sample dialog**:
> Customer: "Customer support team — they'd handle fewer tickets."
> 你: "Got it. CS team should be in design from day 1, not surprise them on launch. 我提议下周 1 hour workshop 跟 CS lead 一起 design tier escalation."

**Q5: Budget envelope**

> "What's the **budget envelope** for first 12 months — annual run rate, including deployment + infrastructure + iteration?"

**为什么**: 设计必须 fit budget. $50k vs $500k vs $5M 完全不同 architecture.

**Avoid awkward**: 不要直接说 "what's your budget" — sounds salesy. 用 "annual run rate" framing 显得 mature.

**Q6: ROI horizon**

> "When does this project need to **show positive ROI**? End of year 1? Year 2? Or is this exploration with longer horizon?"

**为什么**: Short horizon → conservative design, low risk. Long horizon → bet on bigger reframe.

**Q7: Comparison anchor**

> "Have you tried this with **other vendors / internal teams**? If yes, what worked / didn't work?"

**为什么**: Previous attempts contain lessons. 不问 = 重蹈覆辙.

**Q8: User vs Buyer**

> "Who's the **buyer** (signs the contract / approves budget)? Who's the **end-user** (uses daily)? Are they the same person?"

**为什么**: Buyer 和 user 经常不同. Design 必须 satisfy 两者. 否则 buyer signs, user sabotages.

**Q9: Adjacent metrics**

> "Beyond your North Star metric, what **secondary metrics** would worry you if they regress? E.g., if deflection goes up but CSAT drops?"

**为什么**: 单 metric 优化经常 gaming. Guard rail metrics 防止 gaming.

**Q10: Counter-example**

> "Walk me through a **specific recent case** where current process failed. What would you want the AI to do **differently**?"

**为什么**: Abstract KPI 不够, specific case 让你看到真实失败模式.

### 1.3 KPI lock STAR (Indonesia voice agent)

**S**: Ops "想用 voice agent 做催收"

**T**: Lock specific KPI before designing

**A**:
1. "ONE metric in 6 months?" → "Repayment rate"
2. "Total or outbound-led?" → Push to "outbound-led 30-day cohort"
3. "Baseline?" → 12% (after ops checked)
4. "Target / stretch / disappointment?" → 18% target, 22% stretch, 14% disappoint
5. "Loser?" → Manual call agents — reorg to higher-tier case
6. "Budget envelope?" → Single-market $X/year, scale to $X×7 if 7-market
7. "Counter-example?" → Recent case where customer hung up after 30 sec on manual agent

**R**: KPI locked, 后续 6 个月设计每周决定都 reference 这 7 个 anchor. 上线后 KPI 准确达成 target.

**FDE framing**: "KPI lock 不是 contract, 是 alignment tool. Without it, 6 月后双方对成功定义不一致 = 失败."

---

## ⚙️ Problem 2: Stakeholder Questions — Who Decides, Funds, Vetos, Uses, Blocks

### 2.1 Why stakeholder questions 第二个问

90% AI deployment 失败 on **integration / political**, 不是 technical. 不 map stakeholder = architecture 设计完 IT 不批 / Legal 不签 / Finance 不付 = 项目死.

### 2.2 5-10 specific question scripts

**Q1: Sponsor + incentive**

> "Who's the **executive sponsor**? What's their **incentive** — promotion / cost saving / strategic bet?"

**为什么**: Sponsor 的 incentive 决定项目优先级. 如果 sponsor 是 promotion driven, 项目 timeline 跟他升职窗口 align. 如果 cost saving, 你要 prove ROI 快.

**Sample dialog**:
> Customer: "VP of Operations."
> 你: "VP 的 OKR 这个季度是?"
> Customer: "Reduce cost per ticket 20%."
> 你: "OK, 这是 anchor. Design 必须 demonstrate cost reduction within 1 quarter, 不能 'long term improvement'."

**Q2: Veto holders**

> "Who could **veto** deployment — IT, Legal, Compliance, Security, Finance? Have they been engaged?"

**为什么**: Vetoers 经常在最后才出现, killing project. Engage early.

**Sample push**:
> "I notice Compliance not in the room. Can we get 30 min with Compliance head before next session? Their red lines drive 30% of architecture."

**Q3: Funder vs Decider**

> "Who **funds** this (which budget line)? Are they the same as the **decider** for architecture?"

**为什么**: 资金来源决定 reporting / accountability. 经常 funder 是 CFO/CTO, decider 是 product team, gap 需要 bridge.

**Q4: Previous failures**

> "Has the company **tried this before** — internal team or vendor? What happened?"

**为什么**: Previous failures 带 institutional scar. 你必须 explicitly address 为什么 this time different.

**Sample dialog**:
> Customer: "Tried 2 years ago with [vendor], failed."
> 你: "What's the failure mode — model didn't work? Integration didn't ship? Adoption failed?"
> Customer: "Integration. IT didn't cooperate."
> 你: "Got it. 我会 first conversation with IT 之前 even start technical design. 上一次 lesson."

**Q5: Other vendors in space**

> "Are there **other vendors** / internal teams already in this space? Any overlapping mandate?"

**为什么**: 政治冲突. 如果有 incumbent vendor, 你要 understand why 客户 looking 新方案.

**Q6: User involvement**

> "Will the **end-users** (e.g., support agents using AI) be involved in design / testing? How much weight do they carry vs. management?"

**为什么**: User sabotage 是 silent project killer. Bottom-up adoption 比 top-down mandate 持久.

**Q7: Trust evaluator**

> "Who **technically evaluates** our solution on your side? Who do **you trust** for the technical call?"

**为什么**: Customer-side technical evaluator 是你的 ally. Identify them early.

**Q8: Champion**

> "Who's our **champion** inside the org — someone who actively wants this to work, willing to advocate for resources?"

**为什么**: Without champion, project drifts. Champion ≠ sponsor (sponsor signs check, champion makes things happen daily).

**Q9: Implementation team**

> "Will your team **implement alongside** us, or is this fully us delivering and you accepting? What's your team's bandwidth?"

**为什么**: 决定 we own how much. 客户 0 bandwidth = we do all integration. 客户 high bandwidth = pair programming model.

**Q10: Renewal decider**

> "Who decides if we **renew the contract** in 12 months? Same person, or different?"

**为什么**: 你的 long-term success metric 由 renewal decider 决定. Engage them from start.

### 2.3 Stakeholder map STAR (BNPL 4-stakeholder)

**S**: BNPL chatbot, 4 个 stakeholder (Product / Compliance / CS / Risk)

**T**: Map + reconcile

**A**:
1. Sponsor question → Product VP (incentive: launch this quarter for promotion)
2. Veto question → Compliance (regulatory) + Risk (data leak)
3. User question → CS team (worried about replacement)
4. Champion question → Product PM 是 day-to-day champion
5. Funder question → Product budget, but cost goes to CS budget post-launch (政治!)

**Stakeholder map** (5 col), decisions tier-based per red lines.

**R**: 0 compliance incident, CS happier (high-value cases), Product VP renews.

**FDE framing**: "Stakeholder map ≠ org chart. 5 questions per stakeholder makes the real org visible."

---

## ⚙️ Problem 3: Constraints Questions — Deployment, Compliance, Timeline, Data

### 3.1 Why constraints 第三个问

KPI + Stakeholder locked, now reality check. Constraints 决定 technical stack — 经常 "must run on-prem" 或 "must integrate with this 15-year-old ERP" 比所有其他 design decision 影响大.

### 3.2 5-10 specific question scripts

**Q1: Deployment environment**

> "Where does the system **run** — your cloud, our cloud, on-prem, edge devices, hybrid? Any hard constraints?"

**为什么**: 决定 90% architecture. On-prem 没法用 OpenAI API; cloud 要选 AWS / GCP / Azure.

**Q2: Data residency**

> "**Customer data** — where can it physically reside? GDPR, data sovereignty, industry regulation?"

**为什么**: 国家级 constraint. 欧洲 / 中国 / 印度 / 印尼都有 residency 法律.

**Sample dialog**:
> Customer: "EU customer data must stay in EU."
> 你: "OK, this means: (a) Model serving must be EU region, (b) Logs / observability must be EU region, (c) Cross-border API calls (e.g., OpenAI us-east) are blocked. This eliminates ~50% of off-the-shelf solutions."

**Q3: Integration systems**

> "**What existing systems** must integrate? CRM, ERP, ticketing, identity, data warehouse?"

**为什么**: Integration 是 deployment 慢的最大原因. 6-month delay 经常来自 integration, 不是 model.

**Push for specificity**:
> "Specifically — Salesforce / SAP / ServiceNow versions? Auth model (OAuth 2.0 / SAML / mTLS)? API throughput limits?"

**Q4: Timeline**

> "What's the **target timeline** — MVP, POC, production launch?"

**为什么**: 6 weeks vs 6 months 完全不同 architecture choice.

**Sample push**:
> Customer: "Production by end of year."
> 你: "Today is May. 7 months. 给我 split: 6 weeks POC, 8 weeks MVP, 14 weeks production hardening. OK?"

**Q5: Budget / cost ceiling**

> "**Cost ceiling** — monthly run rate, including inference cost, infrastructure, headcount?"

**为什么**: Cheap LLM (Haiku) vs expensive (Opus) 经常 10×. 客户经常没意识到 inference cost 累计.

**Sample education**:
> "GPT-4 调用 average $0.02 per request. 1M req/month = $20k. 我估算你的 use case ~500k req/month = $10k. Sound right? Or are we looking at 10×?"

**Q6: Latency tolerance**

> "**Latency requirements** — < 200ms, < 1s, < 5s, eventual?"

**为什么**: Voice agent < 500ms vs document analysis < 30s 完全不同 architecture.

**Q7: Scale today + 12 months**

> "**Current scale** — req/day, MAU, ticket volume? **Expected 12-month scale** — 2×, 10×, 100×?"

**为什么**: 单 region vs multi-region, single-tenant vs multi-tenant, dictate by scale.

**Q8: Compliance / audit**

> "Compliance regime — SOC2 / HIPAA / GDPR / SOX / PCI? Audit requirements — every decision logged?"

**为什么**: 决定 logging architecture, retention, encryption.

**Q9: What CAN'T change**

> "What in your current stack **can't change** — existing ERP, regulatory framework, customer-facing API?"

**为什么**: 客户经常说 "we want AI", 但有 silent constraint "but don't change ServiceNow workflow". 不问 = 后期 surprise.

**Q10: Security review process**

> "Security review process — who, how long, what blockers typically?"

**为什么**: 银行 / 政府 客户 security review 经常 8-12 weeks, 必须 build into timeline.

### 3.3 Constraints STAR (Indonesia data residency)

**S**: Indonesia voice agent, OJK regulation

**T**: Discover constraints before designing

**A**:
1. "Deployment env?" → "Must be in Indonesia data center"
2. "Data residency?" → "Customer phone, dialog, recording — never leave Indonesia"
3. "Integration?" → "Existing repayment system, COBOL-based, batch API only"
4. "Timeline?" → "8 weeks pilot, 6 months full rollout"
5. "Compliance?" → "OJK 2017 fintech reg, customer consent + opt-out + recording disclosure"

**Discovered**: OpenAI API 不能用 (data 不能出印尼). Must self-host. COBOL integration 需要 batch API adapter.

**R**: Architecture decisions 锁住. 没在 month 3 才发现 "OpenAI API 不能用" 这种事故.

**FDE framing**: "Constraints questions saved 4 weeks of re-architecture. 关键是 ask before design."

---

## ⚙️ Problem 4: Failure Mode Questions — Worst Case, Recovery, Fallback

### 4.1 Why failure mode questions 第四个问

KPI + Stakeholder + Constraints locked, now ask: **what's worst case?**

不同 use case wrong-answer cost 差 1000×. 客服 chatbot 给错回答 $1 cost; medical diagnosis 给错答案 lawsuit + life. 不问 = 设计 wrong safety layer.

### 4.2 5-10 specific question scripts

**Q1: Cost of wrong answer**

> "**Cost of a wrong answer** — trivial (customer re-asks), moderate (refund / lost trust), severe (financial loss / regulatory), catastrophic (life-threatening)?"

**Reference 3-tier framing if customer 不知道**:

> "Let me give 3 reference points:
> (a) **Consumer search** — wrong result annoying, retry free. ~5% error OK.
> (b) **Credit decision** — wrong call has financial + regulatory impact. < 1% error.
> (c) **Medical diagnosis** — wrong call life-threatening. < 0.01% error.
>
> Where on this spectrum are your use cases?"

**Q2: Acceptable error rate**

> "**Acceptable error rate** at launch? Year 1 target?"

**为什么**: 0% is impossible. Force customer to commit to realistic number.

**Push if "0%"**:
> "Zero is impossible for any AI. Let's discuss: (a) what error rate is **detectable** by your team and **reversible**? (b) what triggers **catastrophic** loss vs **annoying** loss? (c) what error rate does your **current manual process** have? Usually 2-5%. We'll be < 1% in most domains."

**Q3: Fallback path**

> "**Fallback when AI fails** — human review, alternate system, manual process, simply 'I don't know'?"

**为什么**: Fallback design dictates UX + cost. "I don't know" 是免费 fallback, human review 是贵 fallback.

**Q4: Edge case review**

> "**Edge case review** — who looks at AI outputs that look wrong? How quickly?"

**为什么**: Without review loop, errors compound silently.

**Sample setup**:
> "I'd propose: random 5% sampling for daily review, anomaly-triggered 100% review, customer-flagged 100% review. Sound right for your scale?"

**Q5: Silent failure mode**

> "What's the **silent failure mode** that worries you — AI gives plausible-looking wrong answer that humans don't catch?"

**为什么**: Silent failure 是 LLM 最危险 mode. Customer 必须 acknowledge.

**Q6: Recovery / rollback**

> "If we deploy and something goes wrong, **how do we roll back**? Feature flag, kill switch, redirect to human?"

**为什么**: 客户经常没想 rollback. FDE 必须 raise.

**Q7: Public visibility**

> "**If AI output goes wrong publicly** — Twitter screenshot, news article — what's the company response plan?"

**为什么**: PR 风险 = brand. 客户必须 commit response plan.

**Q8: Worst customer-cohort**

> "What **customer cohort** is most fragile — would be hit hardest if AI gives wrong answer? High-net-worth? Vulnerable population? Regulators?"

**为什么**: 不同 cohort 接受 different risk. 设计可能要 tier 处理.

**Q9: Acceptable downtime**

> "**Acceptable downtime** — 99%, 99.9%, 99.99% uptime SLA?"

**为什么**: 99.99% needs multi-region failover. 99% can be single region. 10× cost difference.

**Q10: Audit trail**

> "Audit trail — for **every wrong answer**, what investigation evidence do you need to keep?"

**为什么**: 合规 + post-mortem. Audit log design 决定 by this answer.

### 4.3 Failure mode STAR (Indonesia tier 3 refund design)

**S**: Indonesia ops "auto refund"

**T**: Define failure tolerance before designing

**A**:
1. "Cost of wrong refund?" → "Customer 投诉 to OJK = monetary fine + reputation"
2. "Acceptable error rate?" → "Tier 3 must be < 0.1%, basically zero"
3. "Fallback?" → "Human approves before refund (tier 3); 自动 (tier 1)"
4. "Silent failure?" → "Wrong amount calculated → customer happy short-term, accounting catches later"
5. "Rollback?" → "Daily reconciliation cron, anomaly → freeze auto-refunds"

**Outcome**: Tier 3 设计 with mandatory human in loop, daily reconciliation, freeze trigger.

**Result**: 90 days 0 wrong refund. Customer trust intact.

**FDE framing**: "Failure mode questions force customer to confront reality. 0% is unrealistic. 0.5% might be acceptable. Design around the real number."

---

## ⚙️ Problem 5: Success Criteria Questions — Week 1, Month 1, Quarter 1, Demo

### 5.1 Why success criteria 第五个问

KPI + Stakeholder + Constraints + Failure locked. Now: **phasing**. Customer wants result fast. 你 design phased rollout 让客户 see progress 早.

### 5.2 5-10 specific question scripts

**Q1: Week 1 look-like**

> "**Week 1 of launch** — what do you want to see on dashboard?"

**为什么**: 强制 customer 想象 launch day. Reveal 真实 priorities.

**Sample dialog**:
> Customer: "Volume served + customer satisfaction."
> 你: "OK. Week 1 dashboard: daily volume + CSAT. Anything else? Latency? Error rate?"
> Customer: "Yeah, error rate."
> 你: "Threshold for week-1 pass — volume ≥ X, CSAT ≥ Y, error ≤ Z?"

**Q2: Month 1 milestone**

> "**Month 1** — what becomes 'project still healthy' vs 'we need to course correct'?"

**为什么**: Month 1 是 customer 第一个 escalation point. Threshold lock 早.

**Q3: Quarter 1 ROI**

> "**Quarter 1** — does the project need to show ROI? What number?"

**为什么**: Quarter 1 ROI 决定 renewal probability.

**Q4: Year 1 vision**

> "**Year 1** — if everything goes right, where is this project? Replaced X% of manual process? Generated Y revenue? Reduced Z cost?"

**为什么**: 长期 vision 决定 architecture extensibility. Locked-in for 1 year horizon vs 5 year horizon.

**Q5: Demo for stakeholder**

> "What's the **demo** that would impress your sponsor / CFO?"

**为什么**: Sponsor 的 mental model 是 demo. Build demo first, generalize later.

**Sample**:
> Customer: "Show 3 customer dialogs end-to-end, with metrics."
> 你: "OK. Week 2 we record 3 real (or realistic) dialogs, embed metrics overlay, ready for VP demo."

**Q6: Champion's win**

> "What's the **win our champion can claim** in next quarterly review?"

**为什么**: Champion needs ammo for internal advocacy. Design specific wins for them.

**Q7: Failure-to-launch criteria**

> "What would make you **kill** this project — what evidence by what date?"

**为什么**: Force customer to commit kill criteria. Otherwise project drags zombie.

**Q8: Renewal milestone**

> "**12 months** — what makes renewal a yes? What makes it a no?"

**为什么**: Long-term success criteria. 你的 design 必须 optimize for renewal yes.

**Q9: Phased rollout preference**

> "**Rollout style** — shadow mode → 10% → 50% → 100%, or big bang launch?"

**为什么**: 客户的 risk tolerance + technical maturity 决定.

**Q10: Comparison plan**

> "How do we **compare** AI performance vs. status quo? A/B test? Shadow mode? Historic baseline?"

**为什么**: Without comparison, can't prove value. Lock measurement method.

### 5.3 Success criteria STAR (Voice agent multi-market phased)

**S**: Voice agent expand 6 markets, customer wants "production in 6 months"

**T**: Define phased success per market

**A**:
1. "Week 1 per market?" → Shadow mode, 0 customer impact, observe metrics
2. "Month 1?" → 10% traffic, ≥ 20% repayment improvement vs control
3. "Quarter 1?" → 50% traffic, repayment + 1.5pp absolute
4. "Year 1?" → Full traffic, repayment hit target, 5 lessons documented per market
5. "Demo?" → Per-market 30-min playback with metrics overlay for ops VP
6. "Kill criteria?" → Month 1 repayment < baseline, freeze + re-design

**Outcome**: Per-market phased rollout 文档. 6 markets 6 months, 0 markets stalled.

**FDE framing**: "Success criteria not for customer — for me. Forces honesty about phased delivery. Customer hates surprise."

---

# Part 3 · 串起来看

5 类 questions 是 design 的 5 个 dimension:

1. **Business / KPI** — 设计 optimize 什么
2. **Stakeholder** — 设计 satisfy 谁
3. **Constraints** — 设计 stack 选什么
4. **Failure** — 设计 safety layer 在哪
5. **Success** — 设计 phasing 怎么 roll out

**5 类完整 ask = design 解锁**. Skip 任一类 = design 有 blind spot.

**Pragmatic limit**: 第一次 conversation 5-7 questions. 不是 5 类各问 2 个 = 10 个 (too many). 是 5 类总共 5-7 个 (1-2 per category).

---

## 必问 clarifying questions (面试官给场景时反问)

如果 interviewer 给 vague scenario, 你反问 clarifying:

**1. Customer 类型**
> "What industry? Bank / health / retail / SaaS / government? Each has different default constraints."

**2. Customer 已有 AI 经验?**
> "First AI deployment, or sophisticated user? Design conversation depth different."

**3. Time constraint of this conversation**
> "Is this a 30-min discovery call or full-day workshop? Affects how many questions I ask."

**4. Sponsor seniority**
> "VP / Director / Manager level? Each prefers different framing — VP wants strategic, Director wants concrete, Manager wants daily ops."

**5. Have they hired vendor before?**
> "Past vendor experience — positive or negative? Shapes trust level and how I open."

---

## 5 步框架 (回答 60-90 秒 monologue)

| 段 | 时长 | 内容 |
|---|---|---|
| Frame | 15s | "5 categories of question, 5-7 questions total, with why each matters" |
| List categories | 20s | BSCFS (Business / Stakeholder / Constraints / Failure / Success) |
| One example | 20s | Demo 1 question with push-back if vague |
| Pragmatic limit | 10s | "5-7 max first session" |
| Commit next step | 10s | "1-page proposal in 1 week" |

Then if HM follow-up, demo specific question wording per category.

---

## 简历专属 reframe — MANY STAR stories

### STAR 1: Indonesia Voice Agent Discovery (★ PRIMARY)

**Use for**: "What questions would you ask"

**S**: Ops "want voice agent for debt collection"
**T**: 5-category discovery in 30 min
**A**: B (repayment rate KPI lock) → S (compliance veto, ops champion) → C (Indonesia residency, COBOL integration) → F (wrong-info < 0.5%) → S (week-1 shadow, month-1 10% traffic)
**R**: Architecture decisions locked, no late-stage surprises, on-time launch

**Quote ready**:
> "I started Indonesia voice agent with 30-min discovery. 7 specific questions. Locked KPI as outbound-led 30-day cohort repayment (not total). Found OJK data residency = no OpenAI API. Found ops champion early. Without that 30 min, we'd have wasted 4 weeks re-architecting."

### STAR 2: BNPL Chatbot 4-Stakeholder Discovery

**Use for**: "Stakeholder mapping"

**S**: BNPL product team "want chatbot"
**T**: Map 4 stakeholders before designing
**A**: 1v1 with Product / Compliance / CS / Risk (1 hour each), stakeholder map 5-col, find red lines + spaces
**R**: Tier-based design satisfies all 4, 0 incident, CS happier, renewal yes

**Quote ready**:
> "BNPL chatbot — 4 stakeholders sponsor / compliance / CS / risk. I did 1v1 1-hour discovery with each. Compliance red line: no specific 额度 promise. Risk red line: no PII surface. Tier design lets each red line stay. Without stakeholder discovery, single architecture would fail one of them."

### STAR 3: Internal Agent Platform — 5 Team Interview

**Use for**: "Multi-customer discovery"

**S**: Build internal agent platform for N teams
**T**: Discover commonality + diff before abstract
**A**: 5 seed teams 1-hour interview each, abstract 3-layer (workflow / tool / memory), escape hatches per team
**R**: 5 → 14 teams adoption, Risk team self-onboard later as use case grew

**Quote ready**:
> "Internal Agent Platform — 5 seed teams 1-hour interview each. Discovered Risk team didn't need workflow layer, just tool layer. 我没 force it. 6 months later they grew into needing workflow. Discovery-driven abstraction让 platform scale to 14 teams."

### STAR 4: Pakistan Launch Failure Mode Discovery

**Use for**: "Failure tolerance questions"

**S**: Pakistan ASR provider selection
**T**: Failure tolerance discovery
**A**: "Worst case?" → "silent fail > garbage", "wrong-info rate?" → "< 0.5%", "recovery?" → "fall to local Whisper"
**R**: Cascade design (Azure → Google → Whisper), 0 calls lost during Azure 40-min outage

**Quote ready**:
> "Pakistan launch — I asked ops 'silent fail vs garbage response, which worse?'. They said silent fail OK, garbage 不可. 这 30-second conversation 决定整个 fallback architecture — cascade not single provider, ops preference > technical convenience."

### STAR 5: ConvFinQA Data Discovery

**Use for**: "Data questions"

**S**: Multi-hop financial QA project
**T**: Discover data shape before designing pipeline
**A**: "Data depth?" → "5 years filings", "labels?" → "annotator pairs", "noise?" → "5% annotation disagreement", "freshness?" → "annual"
**R**: Pipeline 设计 specifically for noisy + multi-hop. Ablation discovered which stage matters.

**Quote ready**:
> "ConvFinQA — before designing pipeline, I asked data team 5 questions: depth, label format, noise rate, freshness, distribution. Noise rate (5% disagree) drove me to add verification stage. Without that discovery, pipeline 设计 wrong, paper would fail review."

---

## 5 follow-ups

**Q1**: "Customer is impatient — wants design NOW, not questions."

**A**: 不投降, frame strawman + flagged assumptions:
> "I hear you. I can sketch a strawman design in 10 minutes — but I want to **flag 3 assumptions** I'm making, any of which if wrong invalidates the design.
>
> Want me to ask the 3 questions first (5 minutes), or sketch then ask (10 + 5 minutes)?
>
> Either way, **questions save time, not waste it**."

90% impatient customer chooses "ask first" after framing.

**Q2**: "Customer's answer to 'what's the KPI' is 'increase efficiency'. Now what?"

**A**: Push deeper, give options:
> "Efficiency means different things. Let me give 3 specific:
> (a) **Tickets per hour** (volume KPI)
> (b) **Cost per ticket** (cost KPI)
> (c) **First-call resolution rate** (quality KPI)
>
> If I came back in 6 months with 30% improvement in [one of these], would your VP renew this contract?
>
> The one that triggers renewal is your real KPI."

**Q3**: "Customer doesn't know failure tolerance — first time deploying AI."

**A**: Reference 3-tier framing:
> "Let me give 3 reference points:
> (a) **Consumer search engine** — wrong result annoying, retry free. ~5% error OK.
> (b) **Credit decision** — wrong call financial + regulatory impact. < 1% error.
> (c) **Medical diagnosis** — wrong call life-threatening. < 0.01% error.
>
> Where on this spectrum is your use case?"
>
> Help them think it through, don't make them know in advance.

**Q4**: "Customer's 'must-have' constraints are unrealistic (e.g., 0% error rate, 100ms latency, $100/month)."

**A**: Reset with their current process anchor:
> "Zero error impossible for any AI. Let's frame:
> (a) What error rate is **detectable + reversible** by your team?
> (b) What error rate triggers **catastrophic** loss vs **annoying** loss?
> (c) What error rate does your **current manual process** have?
>
> Your manual is usually 2-5%. AI will be < 1% in most domains. Frame relative to manual."

**Q5**: "Do you ever skip questions and just design?"

**A**: Honest, scoped:
> "Yes, but only:
> (a) Small / well-scoped problem where I've solved exactly this 3+ times before
> (b) Customer is sophisticated, they preempted with detailed RFP
> (c) MVP exploration where speed > rigor
>
> First deployment of new domain — **never** skip. Cost of designing wrong thing is always higher than 1 hour of clarification."

---

## ❌ 易错点 (top 10)

1. **Start designing without asking** — fastest fail
2. **Ask 20 questions** — interrogation
3. **Ask without "why this matters"** — checklist mode
4. **No prioritization** — random order
5. **Accept "efficiency" as KPI** — not pushing for specificity
6. **Don't acknowledge customer's frustration** — inflexible
7. **No commit to next step** — questions go nowhere
8. **Generic question wording** — no pattern recognition
9. **Don't give reference points** — customer can't anchor
10. **One-way questioning** — not conversational

---

## ✅ 加分项 (top 10)

1. **5 category framework explicit** (BSCFS)
2. **Why each matters** — pattern recognition demonstrated
3. **Order matters** (KPI first)
4. **5-7 question limit** — pragmatic
5. **Strawman + flag assumptions** for impatient customer
6. **Reference points** for unrealistic constraint
7. **Specific question wording** (not generic)
8. **Push for specificity** (efficiency → tickets per hour)
9. **Commit 1-page proposal in 1 week**
10. **Quote real discovery story** (Indonesia / BNPL)

---

## 一句话总结

> **"What questions would you ask the customer first?" 真正的考点是 "你能不能用 5-7 个 high-leverage question 在 30 min 内 unlock 5 个 design dimension (BSCFS), 每个 question 带 why, 不 interrogate, 然后 commit 1-page proposal in 1 week"**.
>
> 5 categories (BSCFS) + ordered + with "why" + pragmatic limit (5-7 max) + commit next step.

---

## Cheat Sheet (印 1 页)

```
5 question categories (BSCFS, in order):
  Business / KPI      — 优化目标
  Stakeholders        — 谁批 / 谁 veto / 政治
  Constraints         — 部署 / 合规 / 数据
  Failure             — 错的容忍 / fallback
  Success             — 时间窗 / phasing / demo

5-7 questions limit first conversation
1-2 questions per category, the rest in follow-ups

Business / KPI scripts (4-5 essential):
  1. "The ONE metric in 6 months — what number?"
  2. "Current baseline?"
  3. "Threshold: success / stretch / disappointment?"
  4. "Who's the loser if we succeed?"
  5. "Counter-example — recent case where current failed?"

Stakeholder scripts:
  1. "Executive sponsor + incentive?"
  2. "Veto holders — IT / Legal / Compliance / Security?"
  3. "Previous failed attempt?"
  4. "Champion + funder + decider + user (5 different hats?)"

Constraints scripts:
  1. "Deployment env — your cloud / our cloud / on-prem?"
  2. "Data residency — GDPR / industry reg?"
  3. "Integration systems — versions + APIs?"
  4. "Timeline + budget envelope?"
  5. "What CAN'T change?"

Failure scripts:
  1. "Cost of wrong answer — trivial / moderate / severe / catastrophic?"
  2. "Acceptable error rate?"
  3. "Fallback path?"
  4. "Silent failure mode worry?"
  5. "Rollback / kill switch?"

Success scripts:
  1. "Week 1 dashboard — what's on it?"
  2. "Month 1 — healthy vs course-correct threshold?"
  3. "Quarter 1 — ROI required?"
  4. "Demo for sponsor?"
  5. "Kill criteria + by-when?"

Push-back templates:
  Vague KPI ("efficiency") → 3-option (volume / cost / quality)
  Unrealistic constraint (0% error) → 3-tier reference (search / credit / medical)
  Impatient customer → "Sketch + flag 3 assumptions, or confirm first?"
  Don't know failure → "Spectrum: search 5% / credit < 1% / medical < 0.01%"
  Don't want to lock metric → "Strawman + you push back"

Pragmatic rules:
  - 5-7 max first conversation
  - Each question paired with "why this matters"
  - KPI first, always
  - Push for specificity ("efficiency" → "tickets per hour")
  - 1-page proposal within 1 week
  - Listen + react, not lecture

Red lines:
  - Designing without asking (immediate fail)
  - 20+ questions (interrogation)
  - Accept vague KPI without push
  - No follow-up commitment
  - No reference points for unknown answers
  - Generic question wording

5 ready STAR stories:
  1. Indonesia voice agent discovery (★ comprehensive)
  2. BNPL chatbot 4-stakeholder map
  3. Internal Platform 5-team interview
  4. Pakistan failure tolerance discovery
  5. ConvFinQA data discovery

Phrases to use:
  "Each question unlocks a design dimension"
  "If I asked 20 questions you'd feel interrogated"
  "Customer hates slow vendors"
  "1-page proposal within 1 week"
  "Questions save time, not waste it"
```
