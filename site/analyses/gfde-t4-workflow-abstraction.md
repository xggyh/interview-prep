## 题目

> "Customer's loan-approval team has a **manual 12-step workflow**: receive application → KYC check → credit check → income verify → property appraisal → ... → approve / decline. Each step takes minutes-to-days, human-mediated. Convert this into an **agent workflow**. Which steps go to agent, which stay human, which are hybrid?"

或追问形态:

> "Walk through how you decide what's automatable vs what stays human, and how the agent and humans collaborate."

**出处**: Google FDE T4 (Forward Deployed Engineer Scenario Delivery), HR-tipped — 是测试 "business workflow → agent workflow 抽象能力" 的经典题. Palantir / 字节 Lark / Salesforce 都问过类似变体.

**Round**: FDE Workflow Design (45-60 min)

---

## 这道题在考什么

考你 **workflow → agent abstraction** + 产品 + 工程一起的功底:

1. **3-question framework per step** (Deterministic / Reversible / Latency-sensitive) — 不是 "我觉得这步可以"
2. **Hybrid 是常态, 不是异常** — 90% real workflow 都是混合
3. **Human handoff** smooth design — 不能让人重新读所有 context
4. **State persistence** across human-mediated pauses — workflow 暂停几天后能 resume
5. **Trust ladder** — agent autonomy 不是 day 1 全开, 4-phase 渐进

**不考**: "你 agent 框架用 LangChain 还是 LangGraph". 考 **"你能不能把 12 步业务流程拆给 agent 跑得对"**.

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**Business Workflow**: 一个**业务流程**, 由 N 个 sequential / parallel 步骤组成, 由人 (或多人) 手工 / 半手工执行. 贷款审批就是典型 — 12 步, 不同人在不同时间做不同事.

**Agent Workflow**: 把上面的流程**至少部分**交给 agent (LLM-driven 自动化模块) 执行. **关键**: agent ≠ pure LLM, agent = LLM + tools + state + decision logic.

**Hybrid Workflow**: agent 和人在 same workflow 里**协作**完成. 不是 "agent 跑完, 人审", 也不是 "人跑完, agent 看", 而是**穿插**: 第 1 步 agent, 第 2 步人 (但看了 agent 的 prep), 第 3 步 agent, 等等. **90% 真实 enterprise workflow 是 hybrid**.

**Trust Ladder**: agent autonomy 的渐进过程. Phase 1 = agent 只 suggest, 人审; Phase 2 = agent 自动跑 deterministic 步骤, 人审 judgment; Phase 3 = agent 自动 + 异常 escalate; Phase 4 = agent autonomous on routine, 人审 exception. 每 phase 4-8 周 stable 后再 advance.

---

## 2. 核心问题 / 矛盾

**设想没有 3-question framework 的灾难场景**:

```
客户: "我们 12 步 loan approval 流程, 用 AI 自动化."
你想: 都用 AI 跑应该最 efficient.
你写: 12 步全 agent (KYC + credit + appraisal + ... + final approve).

部署 1 周:
  - KYC 步: agent 接 ID 文档 OCR + 自动 verify → 合规人员看不爽 "这不合规, 法规要求人眼"
  - Credit 步: agent 调 bureau API + 解读 → OK
  - 最终 approve 步: agent 自动 deny 1 个客户 → 客户告公司 → "AI 自动拒贷是 discrimination"
  - 还款追踪步: agent auto 调 collection vendor → vendor 接错电话 → 客户投诉
  - 每个步骤出问题就回滚, 没 audit log, 不知道哪个 agent 干了啥

结果: 客户砍项目, 你被 fire, 公司被罚.
```

**问题根源**:

- **没分类 step** → 把 deterministic 和 judgment 步骤混在一起
- **没识别 regulatory** → 某些步骤法律要求人
- **没设计 hybrid handoff** → 人接 agent 的活, 没 context, 慢
- **没 trust ladder** → 直接全自动, 没 staging
- **没 audit + rollback** → 出事不知道哪步, 不能回滚

**3-question framework + Hybrid + Trust ladder 解法**:

```
Step-by-step:
1. 问 3 问题: Deterministic? Reversible? Latency-sensitive?
2. 分类: Agent auto / Confirm-required / Hybrid / Human only
3. 设计 handoff (agent → human 时人看到什么)
4. 用 workflow engine (Temporal / DBOS) 持久化 state
5. Trust ladder Phase 1-4, 每 phase 4-8 周 monitor

每步独立判断, 不是 "全部 auto" 也不是 "全部人".
```

---

## 3. 决策树 — 3-question framework

```
每个 step, 问 3 问题:

┌─────────────────────────────────────────────────┐
│  Q1: Deterministic? 同 input → 同 output?       │
│       (e.g., credit score 公式 = deterministic)  │
│       (e.g., "他能不能还" = judgment)            │
└────────┬─────────────────────────────────┬──────┘
         │ YES                              │ NO (judgment-heavy)
         ▼                                  ▼
┌────────────────┐                  ┌──────────────────┐
│ Q2: Reversible?│                  │ Q2': Reversible? │
│ 出错能不能 undo?│                  │                  │
└────────┬───────┘                  └────────┬─────────┘
         │ YES                                │
         ▼                                    │
┌────────────────┐                            │
│ Q3: Latency?   │                            │
│ Real-time / Async                          │
└────────┬───────┘                            │
         │                                    │
   ┌─────┴─────┐                              │
   │ Real-time │ Async                        │
   ▼           ▼                              │
┌──────┐  ┌──────────────────┐                │
│Agent │  │ Agent auto        │       ┌──────┴─────────┐
│realtime│ │ (background)    │       │ 高风险 / irreversible │
└──────┘  └──────────────────┘       ▼                │
                                  ┌─────────────┐    │
                                  │ Confirm-    │    │
                                  │ required    │    │
                                  │ (agent draft│    │
                                  │  + human    │    │
                                  │  approve)   │    │
                                  └─────────────┘    │
                                                     ▼
                                            ┌────────────────┐
                                            │ Agent assist,  │
                                            │ human decide   │
                                            │ (or pure human)│
                                            └────────────────┘
```

**分类规则**:

| Det? | Rev? | Latency? | 分类 |
|---|---|---|---|
| YES | YES | Async OK | **Agent automate** (full auto, background) |
| YES | YES | Real-time | **Agent automate** (real-time, with fallback) |
| YES | NO | any | **Confirm-required agent** (draft + human approve) |
| NO (judgment) | YES | any | **Agent assist** (draft + human decide) |
| NO (judgment) | NO | any | **Human + agent provides context** |

---

## 4. 12-step 贷款审批 — 分类矩阵

把 3-question framework 套到这道题的 12 步:

| # | Step | Determ? | Revers? | Latency? | Owner | Why |
|---|---|---|---|---|---|---|
| 1 | Receive application | Yes | Yes | Real-time | **Agent**: parse + acknowledge | 解析表单, 确认收件 |
| 2 | KYC check | Mixed | No | Async | **Hybrid**: agent gather docs + scoring, human verify | 法规要求人眼 |
| 3 | Credit bureau pull | Yes | Yes | Real-time | **Agent**: API call | API 死板, deterministic |
| 4 | Credit score interpret | Mostly | Yes | Async | **Agent + escalate outlier** | 大多 routine, 异常人审 |
| 5 | Income verify (payslips / W2) | Mixed | Yes | Async | **Agent assist**: OCR + extract, human spot-check | OCR + 数字对比 |
| 6 | Employer verify (phone call) | No | Yes | Async | **Human** (voice agent draft script) | 关系 + 判断, 人主导 |
| 7 | Property appraisal request | Yes | Yes | Async | **Agent**: schedule + track | 流程性 |
| 8 | Appraisal review | Judgment | Yes | Async | **Hybrid**: agent extract numbers + flag anomalies, human validate | 数字 deterministic, 判断 human |
| 9 | Debt-to-income calc | Yes | Yes | Real-time | **Agent**: deterministic formula | 公式 |
| 10 | Risk assessment | Judgment | Yes | Async | **Agent assist**: ML model score + reasoning, human review | 模型 + 解读 |
| 11 | Final decision | Judgment | No | Async | **Human**: underwriter | 法律责任 + 不可逆 |
| 12 | Communicate decision | Yes | Mostly | Async | **Confirm-required agent**: draft email/letter, underwriter sign | 模板化 + 不可逆 |

**4 类 outcome 分布**:

- **Agent automate** (Step 1, 3, 9): 3 步 — 节省 days
- **Hybrid** (Step 2, 8): 2 步 — agent prep, 人 verify
- **Agent assist + human decide** (Step 5, 6, 10): 3 步 — agent draft, 人定
- **Confirm-required agent** (Step 12): 1 步 — 模板出, 人签
- **Human only** (Step 11): 1 步 — 法律责任
- **Hybrid escalate** (Step 4): 1 步 — agent auto + outlier 人

总: **8/12 步至少有 agent 参与, 4/12 步纯人**.

---

## 5. 具体业务场景 (5 个变体)

### 场景 A: 保险理赔 workflow (12 步类似)

```
1. 报案 (claim 接收)
2. Triage (大小事故分级)
3. 资料收集 (车主上传 / 维修单)
4. 损失评估 (车辆 / 健康)
5. 责任判定 (谁的错)
6. 欺诈检测
7. 维修 / 治疗合作方
8. 估价
9. 决定金额
10. 客户确认
11. 支付
12. Closure 跟踪
```

| Step | Owner | Why |
|---|---|---|
| 1 报案 | Agent (multi-channel intake) | 解析、acknowledge |
| 2 Triage | Agent (rule + ML model) | Routine |
| 3 资料收集 | Hybrid (agent draft list, 客户上传, agent OCR) | 人审复杂上传 |
| 4 损失评估 | Hybrid (照片识别 + 人验) | Vision + judgment |
| 5 责任判定 | Human + agent context | 法律 + 判断 |
| 6 欺诈检测 | Agent assist (ML + 异常 flag) | 模型擅长, 人审 high-risk |
| 7 合作方 | Agent (调度) | Deterministic |
| 8 估价 | Agent (公式 + 市场 query) | Deterministic with exception |
| 9 决定金额 | Confirm-required agent (< $X auto, > 人 sign) | Tier by amount |
| 10 客户确认 | Agent (notify + collect ack) | 流程 |
| 11 支付 | Confirm-required (大额必人审) | Irreversible |
| 12 Closure | Agent | 跟踪 + reminders |

### 场景 B: HR Onboarding (新员工)

```
1. Offer letter draft
2. Offer letter sent
3. 入职手续 (form filling, ID upload)
4. 设备申请 (laptop / phone)
5. Access provisioning (SSO / 系统权限)
6. Training assignments
7. Buddy assignment
8. First-day welcome
9. Week 1 check-in
10. 30-day review
11. Probation eval
12. Promotion to regular
```

| Step | Owner |
|---|---|
| 1 Offer draft | Confirm-required agent (HR signs) |
| 2 Send | Agent |
| 3 Self-serve forms | Agent guide, 异常 → 人 |
| 4 Equipment | Agent ticket, IT fulfill |
| 5 Access | Agent provision based on role template, 人审 sensitive 系统 |
| 6 Training | Agent assign + track |
| 7 Buddy | Manager pick (human), agent 推荐 |
| 8 Welcome | Agent + HR (script) |
| 9 Week 1 | Agent reminder + 反馈 form |
| 10 30-day | Agent prep + manager 1-on-1 |
| 11 Probation | Human (HR + manager) |
| 12 Conversion | Confirm-required agent (template + 签) |

### 场景 C: Software Release Pipeline

```
1. Commit
2. CI build
3. Unit tests
4. Integration tests
5. Code review
6. Security scan
7. Deploy to staging
8. Smoke test staging
9. Canary deploy (5% traffic)
10. Monitor metrics
11. Full ramp
12. Post-release review
```

| Step | Owner |
|---|---|
| 1 Commit | Human (dev) |
| 2 CI | Agent (auto-run) |
| 3 Unit test | Agent |
| 4 Integration | Agent + flake retry |
| 5 Review | Hybrid (agent prep diff summary + suggested reviewers, human approve) |
| 6 Security scan | Agent + human triage CVE |
| 7 Staging deploy | Agent |
| 8 Smoke test | Agent |
| 9 Canary | Agent (auto-rollback on metric drop) |
| 10 Monitor | Agent (alert) |
| 11 Full ramp | Confirm-required (high-traffic, human OK) |
| 12 Postmortem | Hybrid (agent compile metrics, human write learnings) |

### 场景 D: 客户投诉 处理 workflow

```
1. 接收 (email / chat / phone / social)
2. 分类 + priority
3. 客户 verify
4. 调查 / 内部查
5. 责任 + 影响评估
6. 解决方案 propose
7. 客户沟通
8. 执行 (refund / 补偿 / 道歉 / 升级)
9. Follow-up
10. CSAT 调查
11. 内部 learnings
12. Process improvement
```

| Step | Owner |
|---|---|
| 1 接收 | Agent (multi-channel intake) |
| 2 分类 | Agent (intent + priority) |
| 3 Verify | Agent (ID + account lookup) |
| 4 调查 | Hybrid (agent pull data, 复杂 case 人) |
| 5 评估 | Agent assist + 人 (sensitive case) |
| 6 Propose | Confirm-required (refund < $X auto draft, > 人) |
| 7 沟通 | Confirm-required (agent draft, 人 send) |
| 8 执行 | Tier by amount (auto / confirm / human) |
| 9 Follow-up | Agent (timed reminder) |
| 10 CSAT | Agent |
| 11 Learnings | Hybrid (agent aggregate, 人 write) |
| 12 Process imp | Human (with agent data) |

### 场景 E: B2B SaaS Customer Onboarding (你的实际经验背景)

```
1. Signup verify (company / email)
2. Account provisioning
3. Initial config wizard
4. Data import
5. Schema mapping
6. Integration setup (SSO / API)
7. Sample data load
8. User invite (team members)
9. Training (videos + walkthrough)
10. First success milestone
11. Go-live decision
12. Track adoption / churn risk
```

| Step | Owner |
|---|---|
| 1 Signup | Agent (auto-verify domain) |
| 2 Account | Agent |
| 3 Config | Agent guide, complex → CSM |
| 4 Data import | Hybrid (agent map fields, CSM 协助 complex schema) |
| 5 Schema map | Hybrid |
| 6 Integration | Hybrid (agent + IT) |
| 7 Sample data | Agent |
| 8 Invite | Agent |
| 9 Training | Agent (personalized) + CSM (live session if asked) |
| 10 Milestone | Agent track + celebrate |
| 11 Go-live | CSM (human) — relationship moment |
| 12 Adoption | Agent monitor + alert CSM |

---

## 6. 实施 Playbook

**3-step delivery for workflow abstraction project**:

**Step 1: Workflow Mapping (week 0-1)**

- 跟客户的 ops / SME 一起列出真实 workflow 每一步 (interview + shadow + 文档)
- 每步标注: 谁做、用什么 tool、耗时、错误率
- 输出: **1-page workflow map** + matrix (每步 3-question 评分)

**Step 2: Categorization (week 1-2)**

- 应用 3-question framework
- 每步分配 owner (agent / hybrid / confirm-required / human)
- 与客户 review + sign-off
- 输出: **per-step owner doc** + **handoff design** (agent → human 时人看到什么)

**Step 3: Trust Ladder Plan (week 2-3)**

- Phase 1: agent **suggest only** (人审所有)
- Phase 2: agent **auto** on deterministic + reversible
- Phase 3: agent **auto + escalate outlier**
- Phase 4: agent **autonomous** on routine (< 阈值)
- 每 phase 4-8 周, advance 看 override-rate < 5% & 客户 sign-off

**Workflow Engine 选型** (持久化 state):

| 工具 | 适用 | 优点 |
|---|---|---|
| **Temporal** | 大型 / 关键流程 / 多语言 | 工业标准, replay, durable activity, signal |
| **DBOS** | Python-heavy, 数据库优先 | DB-native, 比 Temporal 轻 |
| **AWS Step Functions** | AWS-native, 简单流程 | 不需运维, 但 vendor-lock |
| **Cadence** (Temporal 前身) | 旧 Uber 系统 | 还在用但建议迁 Temporal |
| **自建 + Postgres FOR UPDATE SKIP LOCKED** | 简单 workflow, 小 team | 极简但缺 retry / signal / replay |

**90% 选 Temporal** for enterprise FDE 项目.

---

## 7. 易错坑表

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **Automate everything** | 法规违规 (KYC) + 不可逆错 (final approve) + 信任崩 |
| 2 | **No 3-question framework** | Gut-feel 决定哪步 auto, 错的步自动 |
| 3 | **Agent + human duplicate work** | 没 handoff 协议, 人重新读所有 context |
| 4 | **No state persistence** | Workflow 暂停几天后 lose state, 重做 |
| 5 | **No trust ladder** | 直接 phase 4, 第 1 个 incident → 全 rollback |
| 6 | **Human task UI shows everything** | 信息过载, 人花 30 min 不是 2 min |
| 7 | **No override metric** | Agent 错的看不见, 客户投诉了才发现 |
| 8 | **Sub-step 不拆** | Judgment 步骤里其实有 deterministic 子步骤, 浪费 |
| 9 | **No escalation path** | Agent stuck 时人不知道接, workflow 卡住 |
| 10 | **No timeout / SLA** | 人没在 SLA 内 ack, workflow 永远 pending |

---

## 一句话总结 (Part 1)

> **Workflow → Agent abstraction = "用 3-question framework 把每步分类成 4 个 owner (agent / confirm / hybrid / human), 用 workflow engine 持久化 state, 用 trust ladder 4-phase 渐进开放 autonomy"**.
>
> 90% real workflow 是 hybrid, 不是 "全 auto 或全人". 工程上**绝大多数难点不在 LLM, 在 handoff + state + trust**.

---

# Part 2 · 5 个深度问题

## ⚙️ Problem 1: 3-Question Framework 深度拆解

**这是这道题的 backbone**. 面试场把这 3 问讲清楚, 加 12 步矩阵 demo, 拿一半分.

### 1.1 Q1 — Deterministic? (Same input → same output?)

**测试方法**: 给同一个 expert 同一个 input, 他每次结果**字节级**一样吗?

**Deterministic 例子**:
- Credit bureau API call (input: SSN, output: score)
- Debt-to-income ratio calculation (公式)
- Email parsing (extract from / subject / body)
- Date formatting / unit conversion
- Tax calculation (公式 + 表)

**Judgment 例子** (NOT deterministic):
- "Should we approve this loan?"
- "Is this fraud?"
- "How urgent is this complaint?"
- "Is the employer call going well?"
- "Does this customer fit our ICP?"

**Mixed 例子** (often the case):
- KYC verify: identity matching = deterministic, but "is this likely a fraud attempt" = judgment
- Income verify: extract numbers from payslip = deterministic, "is this income sufficient + stable" = judgment

**Sub-step decomposition** (重要技巧):

很多 step 看似 judgment, 实际可拆成:
1. **Deterministic sub-step** (extract / normalize / lookup)
2. **Judgment sub-step** (small kernel)

例: "Income verify" =
- (a) OCR payslip → extract amount, period (deterministic)
- (b) Sum up 12-month income (deterministic)
- (c) Compare to debt threshold (deterministic)
- (d) "Is the income stable?" (judgment — single year vs multiple)
- (e) "Should we ask for additional docs?" (judgment, edge case)

(a)-(c) agent automates. (d)-(e) 给 human (or low-stakes auto + escalate). **80% 时间是 (a)-(c), 人只花 20% 时间在 (d)-(e)** — 这是巨大的 efficiency gain.

### 1.2 Q2 — Reversible? (Can we undo if wrong?)

**测试方法**: 如果 agent 这步做错了, 1 小时内能不能 100% undo, 无副作用?

**Reversible 例子**:
- Draft email (没发, 还能改)
- Database write to internal table (可 update / delete)
- Soft-delete a record (有 trash bin)
- Schedule a meeting (可 cancel)
- Internal note (可改)

**Irreversible 例子**:
- Send email to customer (发了就发了, recall 有 60s 窗口而且不可靠)
- Send money / transfer / refund (有 chargeback 但慢)
- Sign legal document
- Public post (可删但有截图)
- Delete data without backup
- Call customer phone (说出去的话覆水难收)
- Send SMS

**Reversible-but-painful**:
- Update CRM record (能 revert 但 audit 留痕)
- Reject loan application (能再 invite, 但客户体验受损)

**Rule of thumb**:

- **Reversible + Deterministic** → agent automate, 不需 confirm
- **Irreversible + Deterministic** → confirm-required (agent draft, 人审)
- **Reversible + Judgment** → agent assist (draft + human decide)
- **Irreversible + Judgment** → human only (agent provides context)

### 1.3 Q3 — Latency-Sensitive? (Real-time vs Async OK?)

**Real-time 必备**:
- User chat (秒级响应)
- Phone IVR
- Payment auth (商家等)
- Search query
- Form submit ack

**Async OK** (minutes-hours-days):
- Document processing
- Background scoring
- Batch job
- Email reply
- KYC verification
- Approval workflow

**Why this matters**:

| Latency | Architecture |
|---|---|
| < 100ms | Pre-computed cache / single-process |
| < 1s | LLM call + cached retrieval |
| < 10s | Multi-step agent (sequential tool calls) |
| < 1min | Multi-agent / longer chains |
| < 1hr | Background queue, batch |
| Days | Workflow engine (Temporal), human in loop |

**Real-time + Judgment** 是最难的组合 (e.g., live chat with agent, 必须 sub-second 决定 escalate). 通常的解法: 
- Pre-classify intent (low-latency)
- Defer judgment 给 background OR human
- Use cached / pre-trained classifier (vs full LLM)

---

## ⚙️ Problem 2: Hybrid Handoff UI Design — Smooth Transitions

**真正决定 hybrid 工作流体验的, 不是 agent 多 smart, 而是 handoff UI**.

### 2.1 Bad Handoff vs Good Handoff

**Bad** (常见):

```
[Slack DM to underwriter Alice]

"Loan #4283 needs your review. Click here: [link]"

Alice 点 link → 看到原始 application form (PDF), 没 agent prep 痕迹. 
Alice 重新读 30 页 PDF, 自己 cross-check Excel.
20 min 后做出决定.
```

**Good**:

```
[Underwriter dashboard: Loan #4283 — KYC review needed]

Agent's preparation:
✓ Driver's license: name + DOB match application
✓ Address: utility bill matches
✓ SSN: bureau confirmed identity
✓ Bank statement: 6 months reviewed

Agent flags 2 concerns (please verify):
⚠ Name on bank statement: "J. Smith" — application says "John Smith"
   (likely same person, but worth confirming)
⚠ Address changed in last 6 months
   (from CA to NY — verify intent)

Agent's preliminary recommendation: APPROVE with note

[Approve KYC]   [Request more info]   [Decline]   [Escalate to supervisor]

SLA: respond by Friday 5pm (you have 8 hours)
```

Alice 2 min 决定. **从 20 min → 2 min = 10x 时间节省**.

### 2.2 Handoff UI Checklist

每个 hybrid 步骤的 human UI 必须包含:

| 元素 | 为什么 |
|---|---|
| **Agent's preliminary work** | 别让人重做 |
| **Specific question to answer** | "Approve KYC" 比 "Review everything" 清楚 |
| **Flagged concerns** | Agent 不确定的, 人聚焦 |
| **Quick actions** (1-click) | Approve / Decline / Kick-back / Escalate |
| **Time SLA** | 人知道 deadline |
| **Context links** | 原始文档 (按需查) |
| **Audit log** | 之前 agent 步骤 |
| **Notes field** | 人加备注, 后续 audit |
| **Disagree path** | "I think agent's wrong about X" → training signal |

### 2.3 Anti-patterns (常见错误)

| Anti-pattern | 后果 |
|---|---|
| 给人看原始 raw data, 让人自己重 derive | 浪费时间, 人易出错 |
| Agent 隐藏不确定性 (假装 confident) | 人盲信 / 信任崩 |
| 没 quick action | 人需打字写 long answer, 慢 |
| 没 SLA | Workflow 卡死 |
| 没 escalate option | 人 stuck, 没法 punt up |
| 没 audit log | 后来 audit 不出 |

### 2.4 Dialog 示例 — Agent escalates to underwriter

> **Agent (background)**: Working on Loan #4283. Step 2 (KYC) — found concerns.
>
> **Agent → Underwriter UI**: 
> *"I've completed KYC document gathering. 2 concerns I'm 60% confident about (vs 95% threshold). Please verify before I proceed to Step 3."*
>
> **Underwriter Alice**: Opens UI, sees pre-filled summary + 2 flags. Spends 90 seconds. Clicks "Approve KYC, both flags noted as acceptable."
>
> **Agent**: Marks Step 2 complete with Alice's signature, proceeds to Step 3.

**关键点**: agent 不假装 confident. **60% confidence → escalate at 95% threshold** = 自动 flag.

---

## ⚙️ Problem 3: State Persistence with Workflow Engine

**Workflow 跨越 days/weeks, 必须 durable**. 不能用 in-memory state — restart 就丢.

### 3.1 Why Workflow Engine

朴素实现:

```python
def loan_workflow(application):
    step1 = receive_application(application)
    step2 = run_kyc(step1)        # 等人审 — 几小时到几天
    step3 = get_credit_score(step2)
    # ...
```

**问题**: Python process 重启 → 全丢 state.

**Workflow engine** 把每步**持久化到 DB**, restart 后从中断处 resume:

```python
@workflow.defn
class LoanWorkflow:
    @workflow.run
    async def run(self, application):
        # Step 1: Agent parse + acknowledge
        parsed = await workflow.execute_activity(
            parse_application,
            application,
            start_to_close_timeout=timedelta(minutes=5),
        )
        
        # Step 2: Hybrid KYC (agent prep + human verify)
        agent_kyc = await workflow.execute_activity(
            agent_kyc_prep,
            parsed,
            start_to_close_timeout=timedelta(minutes=30),
        )
        
        # 等人 (signal-based, 可等 days)
        human_kyc = await workflow.wait_for_signal(
            'kyc_verified',
            timeout=timedelta(days=3),
        )
        
        if not human_kyc.passed:
            return await workflow.execute_activity(
                send_kyc_failure_notice,
                application,
            )
        
        # Step 3-4: Agent automate
        credit = await workflow.execute_activity(
            get_credit_score,
            parsed.identity,
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
        interpretation = await workflow.execute_activity(
            agent_interpret_credit,
            credit,
        )
        
        # Step 5-10: ... (略)
        
        # Step 11: Human final decision
        decision = await workflow.wait_for_signal(
            'underwriter_decision',
            timeout=timedelta(days=7),
        )
        
        # Step 12: Confirm-required agent communicate
        draft = await workflow.execute_activity(
            agent_draft_communication,
            decision,
        )
        approved = await workflow.wait_for_signal(
            'comms_approved',
            timeout=timedelta(hours=4),
        )
        
        await workflow.execute_activity(
            send_communication,
            approved.draft,
        )
        
        return decision
```

**Key features**:

| Feature | 用途 |
|---|---|
| **Durable activities** | 每 activity 跑完写 DB, restart 续跑 |
| **Signals** | 等外部事件 (e.g., human verify done) |
| **Timeouts** | SLA, 防止永远 pending |
| **Retry policies** | 自动重试 transient failure |
| **Replay** | 同一 workflow 可重放 (debugging) |
| **Versioning** | 老的 workflow 继续跑老逻辑, 新的跑新 |
| **Saga / Compensation** | 失败时按相反顺序 undo |

### 3.2 State Schema

每个 workflow instance 持久化:

```python
{
  'workflow_id': 'loan-4283',
  'state': 'awaiting_kyc_verify',  # current step
  'history': [
    {'step': 'receive_application', 'status': 'done', 'ts': ..., 'output': {...}},
    {'step': 'kyc_agent_prep', 'status': 'done', 'ts': ..., 'output': {...}},
    {'step': 'kyc_human_verify', 'status': 'pending', 'assigned': 'alice@bank.com', 'sla': ...},
  ],
  'context': {
    'application': {...},
    'agent_findings': {...},
  },
  'pending_signals': ['kyc_verified', 'kyc_rejected'],
  'created_at': ...,
  'updated_at': ...,
}
```

### 3.3 Replay & Time-travel Debug

**Debug 工具**:

- "Show me what workflow #4283 did at 14:30 yesterday" — replay 到时间点
- "Why did the agent decline step 4?" — 看 activity input/output history
- "Time-travel: rerun step 4 with new input" — 改 input 看结果 (sandbox)

**Audit value**: 监管要求 7 年保留, workflow engine 自带 history.

### 3.4 Signal-driven Human Wait

**Signal pattern**:

```python
# Workflow 中等 signal
human_kyc = await workflow.wait_for_signal('kyc_verified', timeout=timedelta(days=3))

# 外部系统 (人审 UI) 发 signal
client.signal_workflow_execution(
    workflow_id='loan-4283',
    signal_name='kyc_verified',
    args=[{'passed': True, 'notes': '...', 'reviewer': 'alice@bank.com'}],
)
```

**Timeout 处理**:

```python
try:
    human_kyc = await workflow.wait_for_signal(
        'kyc_verified',
        timeout=timedelta(days=3),
    )
except TimeoutError:
    # SLA breach — escalate to supervisor
    await workflow.execute_activity(escalate_to_supervisor, ...)
    human_kyc = await workflow.wait_for_signal(
        'kyc_verified',
        timeout=timedelta(days=1),
    )
```

---

## ⚙️ Problem 4: Trust Ladder Rollout — 4-Phase Plan

**最常见 FDE 失败**: 直接全自动 → 第 1 个 incident → 客户失信 → 项目砍.

**正确做法**: 4 phase, 每 phase 4-8 周 stable 后再 advance.

### 4.1 4 Phases Detail

**Phase 0 (Baseline)**: 现状, 全人工.

**Phase 1 — Suggest Mode (Week 1-8)**:

- Agent 跑所有可自动化步骤, 但**不执行**, 只生成 suggestion
- 人审每个 suggestion, accept / edit / reject
- 数据收集: agent suggestion 准确率, 人 override 率, 时间节省

**Advancement criteria (Phase 1 → 2)**:
- Override rate < 10% on deterministic steps (e.g., Step 1, 3, 9)
- Time saved > 20% (vs Phase 0)
- 客户 sign-off

**Phase 2 — Auto-Execute Deterministic (Week 8-16)**:

- Step 1, 3, 9 (deterministic + reversible) → auto-execute
- Step 4, 5, 8, 10, 12 → still suggest mode
- Step 2, 6, 11 → still human

**Advancement criteria (Phase 2 → 3)**:
- Auto-executed steps: error rate < 1%
- Time saved > 40%
- 客户 sign-off

**Phase 3 — Auto + Escalate Outliers (Week 16-32)**:

- Step 4, 5, 8, 10 → auto-execute on routine cases, escalate outliers
- "Routine" = confidence > 95%, within historical norm
- "Outlier" = anomaly detected, edge case, large amount

**Advancement criteria (Phase 3 → 4)**:
- Escalation rate < 5% (i.e., 95% truly routine)
- Customer trust signals (e.g., positive feedback)
- 客户 sign-off

**Phase 4 — Autonomous on Routine (Week 32+)**:

- Routine cases (e.g., loan < $100K, credit > 700, DTI < 35%) → fully autonomous
- Non-routine → still hybrid
- Audit + sample review (10% sampled by human)

**Stays human regardless of phase**:
- Step 11 (Final decision) — legal liability
- Step 6 (Employer call) — relationship + judgment

### 4.2 Phase Advancement Decision

不是日历驱动, 是**指标驱动**. 每 phase 都有明确的 KPI:

| Phase | Primary metric | Threshold |
|---|---|---|
| 1 | Suggestion accuracy | > 90% |
| 1 | Override rate | < 10% |
| 2 | Auto-step error rate | < 1% |
| 2 | Time saved % | > 40% |
| 3 | Escalation rate | < 5% |
| 3 | Customer complaint rate | < baseline |
| 4 | Autonomous decision error | < 0.5% |

**Advancement gate**: 4 周 stable + 客户 sign-off + postmortem learnings 整合.

**Rollback criteria**: 任何 phase 指标 > 2x threshold → rollback to previous phase + investigate.

### 4.3 Trust Ladder Dialog (with customer)

> **客户 (Week 2)**: *"Looks great! Can we go straight to Phase 4? We want autonomous."*
>
> **You**: "I understand the appeal — but going straight to Phase 4 has higher failure probability than Phase 1-2-3-4 sequenced. Here's why:
>
> 1. **We don't yet know agent's failure modes**. Phase 1 reveals them safely.
> 2. **Org change takes weeks**. Underwriters need to learn the new workflow. Phase 1-2 builds their comfort.
> 3. **Trust takes time**. Customer's customers (loan applicants) need to see the system works.
> 4. **Recovery**: Phase 1 mistake = $0 (rep catches). Phase 4 mistake = $$$$ + audit.
>
> **Concretely**: 
> - Phase 1-2 = 16 weeks. By week 16, you have data showing 40% time saved + 1% error.
> - Phase 4 attempt without 1-2 = 4-12 weeks until major incident → 2-month rollback → restart at Phase 1.
> 
> **Net**: 1-2-3-4 = 32 weeks to autonomous. Direct-4 = 50+ weeks. Plus reputation cost.
> 
> Recommend phased. We can compress if data is great (Phase 1 stable after 4 weeks → skip ahead). OK?"

### 4.4 Customer-Visible Phases

让客户看到当前 phase + 进度:

```
Loan AI Project — Phase Tracker

Phase 1 (Suggest Mode):     ████████ DONE Week 1-8
Phase 2 (Auto Deterministic): ████░░░░ IN PROGRESS Week 8-12 (50%)
Phase 3 (Auto + Escalate):  ░░░░░░░░ Week 16-32
Phase 4 (Autonomous Routine): ░░░░░░░░ Week 32+

Current metrics:
- Time saved: 32% (target > 40% to advance)
- Auto-step error rate: 0.7% (target < 1%)
- Customer satisfaction: 4.2 / 5 (baseline 3.8)
```

让客户看到**纪律**, 不是黑盒.

---

## ⚙️ Problem 5: Sub-step Decomposition — When Judgment Steps Aren't Atomic

**最反直觉的发现**: 大多数 "judgment step" 其实可以拆成 **(deterministic 抽取 + 小 judgment kernel)**.

### 5.1 Decomposition Pattern

**Example: Step 5 (Income verify)**

朴素分类:
- "Verify income" = judgment-heavy → 人

精细拆解:
1. (Det) OCR payslip → extract gross, net, period, employer
2. (Det) Look up applicant's claimed annual income
3. (Det) Compute: 12-month sum vs claimed
4. (Det) Compare to debt threshold (DTI ratio)
5. (Judgment) Is income stable? (1 year vs 5 year history)
6. (Judgment) Any red flags? (gaps, abrupt changes)
7. (Judgment) Should we ask for more docs?

**Owner reassignment**:
- 1-4: Agent (deterministic, automatable)
- 5-7: Human, but agent provides context

**Time**: 90% time was in 1-4 (人手工), now agent does. 人只花 10% time on 5-7.

### 5.2 Example: Step 8 (Appraisal Review)

朴素: "Review appraisal" = judgment → 人.

精细:
1. (Det) Extract appraised value from PDF
2. (Det) Compare to listing price
3. (Det) Look up comparable sales in last 6 months (zillow / MLS)
4. (Det) Compute % deviation from comparable
5. (Judgment) Is the appraisal reasonable given comparables?
6. (Judgment) Any anomalies (e.g., much higher than comparables)?
7. (Judgment) Should we order second appraisal?

**Agent**: 1-4 + flag any > 10% deviation. **Human**: 5-7 (with agent's flag).

### 5.3 Example: Step 4 (Credit Score Interpret)

朴素: "Interpret credit" = judgment.

精细:
1. (Det) Score: 720
2. (Det) Category: "Good" (660-749 range)
3. (Det) Recent late payments: 0
4. (Det) Credit utilization: 22% (< 30% healthy)
5. (Det) Account length: 8 years (> 5 = stable)
6. (Det) Recent inquiries: 1 (< 3 = stable)
7. (Judgment) Any concerning patterns in detail?
8. (Judgment) Approve based on this profile?

**Agent**: 1-6 (full profile). **Escalate to human** only if any sub-step shows outlier (e.g., score < 580, utilization > 80%, etc.).

### 5.4 Decomposition Mental Model

```
                    Step (judgment-looking)
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
  Extract data       Look up data      Compute (formula)
  (deterministic)    (deterministic)   (deterministic)
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                Aggregate context
                          │
                          ▼
                Judgment kernel (small)
                  ↓ (binary or small)
                  Decision
```

**Rule**: 大多数 step 的 80% 时间在 "extract + look up + compute", 20% 在 "judgment kernel". Agent 接管 80%, 人专注 20%. **80% efficiency gain without giving up judgment**.

### 5.5 Anti-pattern: Atomic Step Assumption

错: "This step is judgment, so human only."

对: "What sub-parts of this step are deterministic? Agent does those. Judgment kernel only stays human."

**Test**: 让 SME 完成一次该 step, 录像. 看视频, list 每个动作. 大部分动作是 "look up X" / "compute Y" / "format Z" — deterministic. Only 1-2 actions 是 "decide whether..." — judgment. **可量化的 80/20**.

---

# Part 3 · 把 5 个问题串起来看

这 5 个 problem 是**实施一个 workflow abstraction 项目的完整 lifecycle**:

1. **3-question framework** = 工具 (per-step 分类)
2. **Hybrid handoff** = 工程 (agent ↔ human 接口)
3. **State persistence** = 基础设施 (workflow engine)
4. **Trust ladder** = 节奏 (4-phase 渐进)
5. **Sub-step decomposition** = 技巧 (从 step 拆出更多 automation 机会)

**FDE T4 面试场**, 这 5 个讲下来 + 12-step 矩阵 demo + Indonesia refund tier 故事, 是 senior FDE 水准.

---

## 必问 clarifying questions

**1. Current pain**

> "Which step has longest delay / most errors today? Where do customers complain?"

**2. Regulatory**

> "KYC / credit check legally require human eyes-on, or AI-allowed in this jurisdiction? Same for final decision?"

**3. Data systems**

> "Which steps already have APIs (credit bureau)? Which manual / paper? Salesforce / proprietary?"

**4. Decision authority**

> "Final approval — committee / single underwriter / role-based? Agent assists or decides?"

**5. Volume**

> "10 applications/day or 1000? Affects automation ROI."

**6. Failure tolerance**

> "What's the worst-case error you can absorb? 1 wrong approve / month / 100k volume?"

---

## 5 步框架 (sample 45-min answer)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify pain / regulatory / volume / authority |
| 5-15 min | 3-question framework + 12-step categorization matrix |
| 15-25 min | Hybrid handoff UI design |
| 25-35 min | State persistence (Temporal) + sub-step decomposition |
| 35-45 min | Trust ladder 4-phase rollout |

---

## 我会这样答 (sample 完整应答)

> "Clarify — *[假设: longest delay = appraisal (3-5 days), KYC must be human-verified per regulator, credit bureau has API, single underwriter decides final, 100 apps/day]*.
>
> **3-question framework per step**:
>
> 1. Deterministic? Same input → same output?
> 2. Reversible? Easy undo?
> 3. Latency-sensitive? Real-time or async OK?
>
> **4 outcome categories**:
> - Det + Rev + Async → Agent automate
> - Det + Irrev → Confirm-required agent
> - Judgment + Reversible → Agent assist, human decide
> - Judgment + Irreversible → Human (with agent context)
>
> **Apply to 12 steps**: [12-step matrix from Section 4]
>
> 8/12 steps have agent involvement, 4 stay pure human (KYC verify, employer call, final decision, judgment-heavy approval comm).
>
> **Hybrid handoff**: when agent escalates to underwriter, UI shows agent's prep + flagged concerns + 1-click actions + SLA. Underwriter spends 2 min, not 20.
>
> **State persistence**: Temporal workflow engine. Each step is a durable activity. Human waits use signals with timeouts. Workflow can pause days/weeks then resume.
>
> **Trust ladder 4 phases**:
> - Phase 1 (week 1-8): suggest mode, human approves all
> - Phase 2 (week 8-16): auto-execute deterministic steps
> - Phase 3 (week 16-32): auto + escalate outliers
> - Phase 4 (week 32+): autonomous on routine (e.g., loans < $100K)
> - Stays human regardless: Step 11 final decision
>
> **Sub-step decomposition**: most 'judgment' steps split into (deterministic extraction × 80%) + (judgment kernel × 20%). Agent does 80%, human does 20% — 80% efficiency without giving up judgment.
>
> **What I'd avoid**: full automation day 1, no handoff design, in-memory state, no trust ladder, atomic step assumption.
>
> **My resume anchor**: Indonesia refund tier was exactly this 3-question framework applied. Tier 1 (small, common) = fully auto. Tier 2 (moderate) = confirm-required (agent draft + human 1-click). Tier 3 (high-value / suspicious) = full human (agent provides summary). Phase rollout: Phase 1 (agent suggests all tiers, human reviews), 6 weeks later Phase 2 (auto on tier 1), 12 weeks Phase 3 (auto on tier 1+2). Each phase only advanced when human-override rate stable < 5%."

---

## 多场景变体 + 解法

### 变体 1: Insurance claims (12 步)

前面 Section 5 场景 A 已展开. 关键: 欺诈检测 + 高金额需 human, 小额 + routine 可 auto.

### 变体 2: HR Onboarding (12 步)

前面 Section 5 场景 B 已展开. 关键: agent 减 HR 30% 时间, 但 buddy / 1-on-1 / probation 永远 human.

### 变体 3: Software Release (12 步)

前面 Section 5 场景 C 已展开. 关键: canary auto-rollback 是 Phase 4 的招牌, 但 critical release 需 human gate.

### 变体 4: Customer complaint (12 步)

前面 Section 5 场景 D 已展开. 关键: refund amount tier, 高 priority + 法律风险 → human.

### 变体 5: B2B SaaS onboarding (12 步)

前面 Section 5 场景 E 已展开. 关键: go-live 是 CSM 的 relationship moment, 不可 auto.

---

## 简历专属 reframe

| 题点 | 你做过的具体动作 |
|---|---|
| Workflow → agent abstraction | BNPL chatbot — collection workflow 1 步一步 map (intent classification → ack / dispute / promise / hostile / escalate) |
| 3-question framework | Refund tier — tier 1 (det + rev + async) auto, tier 2 (det + irrev) confirm, tier 3 (judgment) human |
| Hybrid handoff | Voice agent escalation — 当 escalate to human agent, transcript + agent's prep + 标记 concern 全部 transfer |
| State persistence | TikTok payment workflow — Temporal-like durable workflows for refund / dispute / chargeback |
| Trust ladder | Voice agent 7 markets — Phase 1 (script-only) → Phase 2 (LLM-augmented) → Phase 3 (LLM-led with human review) → Phase 4 (autonomous on routine) |
| Sub-step decomposition | BNPL chatbot — "decide if user 在 dispute" 拆成 (det: pattern match) + (judgment: nuance) |

**主动 quote** (面试 30-sec):

> "Indonesia refund tier was exactly this 3-question framework. Tier 1 (small refund < IDR 50K, routine reason like 'wrong item') = fully auto, agent decides + executes. Tier 2 (moderate IDR 50K-500K, or moderate suspicion) = confirm-required, agent draft + ops 1-click sign. Tier 3 (high-value > IDR 500K, fraud signal, VIP) = full human, agent provides summary + history. Phase rollout: started Phase 1 (agent suggests all tiers, human reviews all), 6 weeks later Phase 2 (auto on tier 1, ops review only tier 2-3), 12 weeks Phase 3 (auto on tier 1 + 2, human only tier 3). Each phase advanced only when human-override rate stable < 5% over 2-week window. We had ONE incident in Phase 2 — agent loop bug auto-refunded duplicate. Caught by anomaly detector in 4 min, bulk reverted via compensating handler in 12 min. Postmortem → fix → new safeguard (per-customer daily refund cap)."

---

## 5 follow-ups

**Q1**: "Agent disagrees with human (agent says decline, human approves). Should we train on human?"

**A**: Carefully:
- **Yes, signal**: human override is rich training data
- **But**: humans can be biased / wrong / inconsistent
- **Audit**: random sample of overrides reviewed by senior underwriter
- **Compare to outcome**: did the human's decision pay off (loan repaid)?
- **Don't blindly fine-tune** on override data — could amplify human bias
- **Better signal**: outcome-based (1-year repay history) > human label
- **Combine**: weight outcome-confirmed labels higher than raw human override

**Q2**: "Step has both deterministic + judgment parts (e.g., income verify: extract numbers ✓ + decide if 'enough')."

**A**: **Sub-step decomposition** (Problem 5):
- Sub-step A: extract numbers (agent)
- Sub-step B: compare to policy threshold (agent: deterministic rule)
- Sub-step C: judgment on edge cases (human)
- Most 'judgment' steps decompose into deterministic + small judgment kernel
- 80/20: 80% time is in A+B, agent does. 20% time in C, human does.
- Net: 80% step efficiency gain without giving up human judgment

**Q3**: "Customer wants agent autonomous on Step 11 (final decision). Push back?"

**A**: **Strong push back**. Reasons:
- **Legal liability**: who's accountable when AI denies a qualified borrower? Customer or AI vendor? 责任划分不清楚.
- **Regulator review**: lending decisions often regulated (Fair Lending Act in US, equivalent in Indonesia / Vietnam / etc.), require human review on adverse action.
- **Trust**: even if technically possible, customer's customers (loan applicants) may not accept.
- **Discrimination risk**: AI bias is hard to prove absent. Human in loop = legal safety.
- **Compromise**: "Agent provides recommendation + reasoning + flagged concerns. Underwriter reviews + signs in 10 seconds for routine cases (vs 10 min manual). Speed + compliance + legal safety."

**Q4**: "Step 6 employer call — voice agent could do it. Worth automating?"

**A**:
- **Voice agent calling employer may sound robotic**, employer hesitates to give info to AI
- **Hybrid**: voice agent makes the call, can escalate to human in real-time when employer asks question
- **Volume math**: 100 calls/day × 5 min = 8 hours. Not huge automation ROI unless scale higher.
- **Brand risk**: bad voice call tarnishes lender
- **Better use**: agent **drafts the call script** for human caller (saves prep time), but human makes the call.
- **Eventually**: as voice quality improves + employers get used to AI, can revisit (Phase 5+)

**Q5**: "Phase 4 (agent decides routine loans autonomously). How decide which loans 'routine'?"

**A**:
- **Score-based**: agent confidence + risk score + amount + 5 indicators all favorable
- **Pre-defined criteria** (sign-off with underwriter team):
  - Loan amount < $X (e.g., $100K)
  - Credit score > Y (e.g., 720)
  - Debt-to-income < Z (e.g., 35%)
  - No red flags (gaps, fraud signal, complaint history)
  - Within standard product
- **Per-jurisdiction**: regulatory bounds
- **Customer base**: existing customer with track record > new customer
- **Audit**: 10% sampled by human after the fact
- **Kick-back loop**: any auto-decision can be challenged by applicant or auditor, agent learns from corrections
- **Quarterly review**: criteria adjusted based on observed outcomes

---

## ❌ 易错点 (top 10)

1. **Automate everything** — compliance fail + 不可逆错
2. **No 3-question framework** — gut-feel automation choice
3. **Agent + human duplicate work** — no clear handoff protocol
4. **No state persistence** — human work re-done after pause
5. **No trust ladder** — push too fast, first incident → rolled back
6. **Human task UI shows everything** — overload, 30-min review instead of 2-min
7. **No override metric** — disagreement invisible
8. **Atomic step assumption** — judgment step locked as human-only
9. **No SLA / timeout** — workflow stuck waiting human forever
10. **No customer-visible phase tracker** — customer doesn't see your discipline

---

## ✅ 加分项 (top 10)

1. **3-question framework** explicit (Det / Rev / Latency)
2. **Per-step matrix** for the 12 steps (with rationale)
3. **Hybrid handoff UI** with checklist (prep / question / actions / SLA)
4. **State persistence** with workflow engine (Temporal)
5. **Trust ladder** with 4 phases + advancement criteria
6. **Override-rate observability** + alert on drift
7. **Sub-step decomposition** for "judgment" steps
8. **Signal-driven human wait** with timeout
9. **Customer-visible phase tracker** with current metrics
10. **Quote Indonesia refund tier phased rollout**

---

## 一句话总结

> **Workflow → Agent abstraction = "3-question framework 分类每步 + Temporal-like workflow engine 持久 state + 4-phase trust ladder 渐进 autonomy + hybrid handoff UI 不让人重新读 + sub-step decomposition 把 judgment 拆到 80% 可 auto"**.
>
> 工程上**绝大多数难点不在 LLM, 在 handoff + state + trust**.

---

## Cheat Sheet (印 1 页)

```
3-question framework (per step):
  Q1 Deterministic? (same input → same output)
  Q2 Reversible? (can undo if wrong)
  Q3 Latency-sensitive? (real-time vs async)

4 categorization outcomes:
  Det + Rev + Async → Agent automate
  Det + Irrev → Confirm-required (draft + sign)
  Judgment + Rev → Agent assist, human decide
  Judgment + Irrev → Human only (agent context)

12-step loan workflow (this case):
  1 receive → Agent
  2 KYC → Hybrid (agent gather + human verify)
  3 credit pull → Agent
  4 credit interpret → Agent + escalate outlier
  5 income verify → Agent (80%) + human (20% judgment)
  6 employer call → Human (agent draft script)
  7 appraisal request → Agent
  8 appraisal review → Hybrid
  9 DTI calc → Agent
  10 risk assess → Agent assist
  11 final decision → Human (always)
  12 communicate → Confirm-required

Hybrid handoff UI checklist:
  Agent's preliminary work (visible)
  Specific question to answer
  Flagged concerns (agent's uncertainty)
  Quick actions (1-click: approve / decline / kick-back / escalate)
  Time SLA
  Context links (original docs on demand)
  Audit log of prior agent steps
  Notes field
  Disagree path (training signal)

Workflow engine:
  Temporal (90% choice, enterprise)
  DBOS (Python-DB-native, lighter)
  AWS Step Functions (AWS-native, vendor-lock)
  Self-built (only for very simple)

Temporal core features:
  Durable activities (per-step DB persisted)
  Signals (wait for external event)
  Timeouts (SLA)
  Retry policies
  Replay (time-travel debug)
  Versioning (multi-version coexist)
  Saga / Compensation (failure undo)

Trust ladder 4 phases:
  Phase 1 (w1-8): Suggest mode, human approves all
    advance: override < 10%, time saved > 20%
  Phase 2 (w8-16): Auto-execute deterministic
    advance: error < 1%, time saved > 40%
  Phase 3 (w16-32): Auto + escalate outliers
    advance: escalation < 5%, satisfaction OK
  Phase 4 (w32+): Autonomous on routine (criteria)
    audit 10% sample
  Stays human regardless: final decision, employer call

Sub-step decomposition:
  Judgment-looking step often = (det extract × 80%) + (judgment kernel × 20%)
  Agent does extract / lookup / compute (80%)
  Human does judgment kernel (20%)
  80% efficiency gain without giving up judgment

Override metric:
  Per-step disagreement rate (alert > 10%)
  Outcome verify (was override correct in retrospect?)
  Training signal (carefully — bias risk)

Customer-visible:
  Phase tracker (current phase + progress)
  Live KPI (vs target)
  Roadmap (Phase 2 / 3 / 4 plan)

Anti-patterns:
  - Automate all
  - No 3-question framework
  - Duplicate work agent + human
  - No state persistence
  - No trust ladder
  - UI overload
  - No override metric
  - Atomic step assumption
  - No SLA
  - No phase tracker

Resume hooks:
  - BNPL chatbot collection workflow map
  - Indonesia refund tier 1/2/3 + phased rollout
  - Voice agent escalation + transcript transfer
  - TikTok payment durable workflow
  - 7 markets gradual autonomy
```
