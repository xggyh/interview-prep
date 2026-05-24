## T4.2 · workflow abstraction — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/gfde-t4-workflow-abstraction.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t4-workflow-abstraction.html`](questions/gfde-t4-workflow-abstraction.html)

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 核心心智模型 (1 sentence)

Workflow → agent abstraction = "per step 用 Det × Rev × Latency 3 问题分到 4 个 owner (agent auto / confirm-required / hybrid / human), Temporal-like 持久 state, 4-phase trust ladder 渐进 autonomy, sub-step 分解把 judgment 拆 80% 可 auto", 90% 实战难点不在 LLM 在 handoff + state + trust.

### 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Business workflow | N 个 sequential / parallel step 由人手工跑 | 起点 |
| Agent workflow | 至少部分 step 交给 agent (LLM+tool+state+decision) | 目标 |
| Hybrid workflow | agent + human 在 same workflow 穿插, 90% real cases | 实战 |
| Trust ladder | suggest → auto safe → auto + escalate → autonomous routine | 反 "全 auto" |
| Deterministic | 同 input → 同 output (公式 / 查表 / API) | Q1 分类 |
| Reversible | 1 小时内 100% undo 无副作用 | Q2 分类 |
| Confirm-required | agent 起草 + human 1-click sign | det + irrev |
| Agent assist | agent 起草 context, 人决定 | judgment + rev |
| Sub-step decomposition | judgment-looking step 拆 (det 80% + judgment kernel 20%) | 最反直觉招 |
| Signal (Temporal) | wait_for_signal('kyc_verified', timeout=3day) | 等人审 |
| Durable activity | 每 step 跑完写 DB, restart 续跑 | state persistence |
| Compensation / Saga | 失败时 reverse order 走 undo | Temporal pattern |
| Override rate | per-step disagreement 率, alert > 10% | 健康度信号 |
| Phase advance gate | 4 周 stable + KPI 达 + 客户 sign-off | 不日历驱动 |

### 5 个核心 framework / pattern

**Framework 1**: 3-question framework (per step)
- When: 每个 step 分类时
- Algorithm: Q1 Det? + Q2 Rev? + Q3 Latency? → 4 outcomes (auto / confirm / hybrid / human)
- Trade-off: 每步独立判断, 不是 "全 auto 或全人"
- Tools: matrix 表格 12-step × 5 column

**Framework 2**: 4-categorization outcome 表
- When: 应用 3Q 结果后
- Algorithm: Det+Rev+Async → agent auto / Det+Irrev → confirm-required / Judgment+Rev → agent assist / Judgment+Irrev → human only
- Trade-off: 4 类 cover 90% real case
- Tools: per-step owner doc + handoff design

**Framework 3**: Hybrid handoff UI 9-element checklist
- When: agent → human 时 design
- Algorithm: agent prep visible + specific question + flagged concerns + 1-click actions + SLA + context links + audit log + notes + disagree path
- Trade-off: 别让人重做 agent 已做的 (从 20 min → 2 min review)
- Tools: 单 dashboard 优于 Slack DM

**Framework 4**: Trust ladder 4 phase
- When: rollout 节奏
- Algorithm: P1 suggest (8w) → P2 auto deterministic (8w) → P3 auto + escalate outlier (16w) → P4 autonomous routine (with criteria)
- Trade-off: 32 周 vs 直接 P4 50+ 周 (含 reset)
- Tools: customer-visible phase tracker + advancement KPI per phase

**Framework 5**: Sub-step decomposition (80/20 拆)
- When: judgment-looking step 看起来不能 auto
- Algorithm: judgment step = (det extract 80%) + (judgment kernel 20%); agent 接管 80%, 人专注 20%
- Trade-off: 80% efficiency gain 不放弃 judgment
- Tools: 给 SME 录像看, list 每个动作, 大部分是 "look up / compute / format"

### 关键决策树 (ASCII)

```
每 step → Q1 Deterministic? Same input → same output?
   |        |
  YES      NO (judgment-heavy)
   |        |
   v        v
  Q2 Rev?    Q2' Rev?
   |  |      |
  YES NO    任意
   |   |     |
   v   v     v
  Q3   Confirm  Agent assist
  Latency? required  (draft + human decide)
   |   ↓
   v  agent draft + human 1-click
  Real-time / Async
   |       |
   v       v
  Agent    Agent
  realtime auto background

Per-step matrix output:
  Step 1 (receive)     → Agent
  Step 2 (KYC)         → Hybrid (法规要求人眼)
  Step 3 (credit pull) → Agent
  Step 4 (interpret)   → Agent + escalate outlier
  Step 5 (income)      → Sub-step 拆: agent 80% + human 20%
  Step 6 (employer)    → Human (agent draft script)
  Step 7 (appraisal)   → Agent
  Step 8 (review)      → Hybrid
  Step 9 (DTI)         → Agent
  Step 10 (risk)       → Agent assist
  Step 11 (final)      → Human (法律责任 + 不可逆)
  Step 12 (comm)       → Confirm-required
```

### Part 2 五个深度问题速查

**Problem 1: 3-question framework 深度拆解**
- 核心解法: Q1 Det? Q2 Rev? Q3 Latency? 每步独立判断 → 4-category 表 → owner 分配
- Top 3 gotchas: Det 不是 binary 是 spectrum (mixed step 拆 sub-step) / Reversible-but-painful (e.g., reject loan) 也是 irreversible / Real-time + Judgment 最难, defer 或 cached classifier
- Tools: 矩阵 5-col score (耗时×痛×LLM 友好×数据可用×风险)

**Problem 2: Hybrid handoff UI**
- 核心解法: 9-element checklist (prep / question / flags / 1-click / SLA / context / audit / notes / disagree), bad handoff 20min → good 2min = 10x gain
- Top 3 gotchas: 不要给 raw data 让人重 derive / 不要假装 confident (60% 必 flag 95% threshold) / 不要没 escalate option 让 human stuck
- Tools: Underwriter dashboard, Slack/Linear notify with deep-link

**Problem 3: State persistence with Temporal**
- 核心解法: durable activity 每 step 写 DB, signal-based human wait (timeout days), retry policy auto-fix transient, replay debug, saga compensation
- Top 3 gotchas: 内存 state 重启就丢 / human wait 必带 timeout 防永远 pending / cascade compensation 最多 2 levels manual review > 1
- Tools: Temporal 90% choice / DBOS python-native / AWS Step Functions / Cadence (legacy)

**Problem 4: Trust ladder 4-phase rollout**
- 核心解法: P1 suggest-only (w1-8) → P2 auto det (w8-16) → P3 auto + escalate (w16-32) → P4 autonomous routine (w32+ 内 criteria 内)
- Top 3 gotchas: 不日历驱动 — 指标驱动 (override < 10%, time saved > 20%, etc.) / rollback criteria (2x threshold → rollback) / customer-visible phase tracker
- Tools: phase advancement KPI table + sign-off doc

**Problem 5: Sub-step decomposition (反原子假设)**
- 核心解法: judgment step 录像分析 → list 每个动作 → 80% = look up / compute / format (det) + 20% = "decide whether" (judgment)
- Top 3 gotchas: 错: "这步是 judgment 所以 human only" / 对: "judgment kernel 多大? 其他是不是 det?" / income verify 实际 OCR + sum + compare 都是 det
- Tools: SME 跟踪 / 动作 list / per-action det 标记

### Production gotchas (top 15)

1. Automate everything (合规违反 + 不可逆错)
2. No 3-question framework (gut-feel automation choice)
3. Agent + human duplicate work (no handoff protocol)
4. No state persistence (workflow pause days → 丢)
5. No trust ladder (直 P4 first incident → rollback)
6. Human task UI 显全部信息 (30min vs 2min review)
7. No override metric (disagreement invisible)
8. Atomic step assumption (judgment step 锁 human)
9. No SLA / timeout (workflow 永 pending)
10. No customer-visible phase tracker
11. No cascade compensation cap (compensation 引 compensation 引)
12. No clarifying clause: regulator 要求人眼 / Final decision 法律责任
13. No escalation path 反向 (human stuck 时 punt up)
14. No advancement criteria definition
15. No quarterly red-team on sub-step boundary

### 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Workflow → agent abstraction | BNPL chatbot collection | intent → ack/dispute/promise/hostile/escalate 5-class workflow map |
| 3Q framework | Refund tier | tier1 (det+rev+async) auto / tier2 (det+irrev) confirm / tier3 (judgment) human |
| Hybrid handoff | Voice agent escalation | transcript + agent's prep + concerns + sentiment → human, no re-explain |
| State persistence | TikTok payment | Temporal-like durable workflow for refund/dispute/chargeback |
| Trust ladder 4-phase | Voice agent 7 markets | script-only → LLM-augmented → LLM-led human review → autonomous routine |
| Sub-step decomposition | BNPL chatbot | "is user disputing?" = pattern match (det) + nuance (judgment) |
| Phase advance discipline | Indonesia refund tier | 6 weeks Phase 1 → 12 weeks Phase 2 → ... advance only override < 5% stable 2-week window |
| Compensation handler | Refund flow | per refund type auto-reverse + bulk rollback API |
| Override metric tracking | Voice agent | per-market per-intent disagreement rate, retrain trigger > 10% |

### 面试现场 quotables (top 8)

1. "Most 'judgment' steps decompose into deterministic 80% + judgment kernel 20% — agent does 80%, human does 20%, 80% efficiency without giving up judgment."
2. "Indonesia refund tier was exactly this 3Q framework: tier 1 (small + routine) fully auto, tier 2 (moderate) confirm-required, tier 3 (high-value / suspicious) human."
3. "Trust ladder 32 weeks to autonomous beats direct-Phase-4 50+ weeks after the first incident reset."
4. "Hybrid handoff UI: 20 min review becomes 2 min. The 10x gain is agent's prep + flagged concerns + 1-click actions + SLA."
5. "Step 11 (final decision) stays human regardless of phase — legal liability + regulatory requirement + AI bias discrimination risk."
6. "Phase 2 incident: agent loop bug auto-refunded duplicate ~200 users. Anomaly detector caught in 4 min (per-customer daily cap). Bulk reverse via compensating handler in 12 min. Zero customer-facing impact."
7. "Workflow engine choice: Temporal 90% for enterprise (durable activity + signal + saga + replay). DBOS for Python-DB-native. Self-built only for simple linear workflows."
8. "Each phase only advances when human-override rate stable < 5% over 2-week window. Indicator-driven, not calendar."

### 红线 (top 10 anti-patterns)

1. Day-1 全自动化 (合规炸 + 法律责任)
2. 无 3-question framework (gut feel)
3. Agent 隐藏 uncertainty (假装 confident)
4. Workflow state in memory only (restart 丢)
5. 直接 Phase 4 跳 Phase 1-3
6. Human UI 给 raw data 让人 re-derive
7. 同一阈值 cover 所有 step types
8. No SLA on human review tasks
9. No advancement criteria — 时间驱动 advancement
10. No cascade compensation level cap (>2 hop → manual review)

### Workflow engine selection 矩阵

| Engine | 强项 | 弱点 | 适合 |
|---|---|---|---|
| **Temporal** | 工业标准, replay, signal, multi-language SDK | 自建运维重 (Temporal Cloud $200+/mo) | 大型 / 关键流程 / 跨语言 ⭐ |
| **DBOS** | DB-native (Postgres), Python first, transactional consistency | 多语言弱, 小生态 | Python-heavy + 数据库优先 |
| **AWS Step Functions** | AWS-native, 不需运维 | vendor lock-in | AWS, 简单流程 |
| **Cadence** (Temporal 前身) | 旧 Uber 系统在用 | 维护不积极 | legacy 迁移到 Temporal |
| **自建 + Postgres FOR UPDATE SKIP LOCKED** | 极简 | 缺 retry / signal / replay | toy / 极简 workflow |

### 12-step loan workflow categorization (anchor case)

| # | Step | Det | Rev | Latency | Owner | Sub-step decomposition |
|---|---|---|---|---|---|---|
| 1 | Receive | Y | Y | RT | Agent | parse + ack auto |
| 2 | KYC | Mixed | N | Async | Hybrid | doc gather agent + verify human (法规) |
| 3 | Credit pull | Y | Y | RT | Agent | API call |
| 4 | Score interpret | Mostly | Y | Async | Agent + escalate | 大多 routine, outlier human |
| 5 | Income verify | Mixed | Y | Async | Agent assist | OCR + sum (det) + stable judgment (human) |
| 6 | Employer call | N | Y | Async | Human (agent draft script) | 关系 + 判断 |
| 7 | Appraisal request | Y | Y | Async | Agent | schedule + track |
| 8 | Appraisal review | Mixed | Y | Async | Hybrid | extract + comparable (det) + reasonable (human) |
| 9 | DTI calc | Y | Y | RT | Agent | 公式 |
| 10 | Risk assess | Mixed | Y | Async | Agent assist | ML score + reasoning, human review |
| 11 | Final decision | N | N | Async | Human (always) | 法律责任 |
| 12 | Communicate | Y | Mostly | Async | Confirm-required | template + sign |

### Hybrid handoff UI 9-element example (Loan #4283 KYC review)

| Element | Content |
|---|---|
| Summary (30-sec) | "User refund $200 damaged product. Photo verified. Agent 0.4 conf — couldn't confirm extent." |
| Specific question | "Approve KYC?" (not "Review everything") |
| Flagged concerns | ⚠ Name slight differ ⚠ Recent address change |
| Quick actions | [Approve KYC] [Request info] [Decline] [Escalate] |
| SLA | "respond by Fri 5pm (8h)" |
| Context links | full doc on-demand |
| Audit log | prior 4 agent steps |
| Notes field | reviewer adds, audit 留 |
| Disagree path | "I think agent's wrong" → training signal |

### 5 业务场景变体 (anchor stories)

| Variant | 关键 step | Owner 分布 |
|---|---|---|
| Insurance claims (12 step) | 欺诈检测 + 高金额需 human | small auto, large human, ML + 异常 flag |
| HR Onboarding (12 step) | Buddy / 1-on-1 / probation 永远 human | training agent assign, equipment IT fulfill |
| Software release (12 step) | Canary auto-rollback + critical human gate | code review hybrid, security scan agent + human triage |
| Customer complaint (12 step) | refund amount tier + 法律风险 | 接收 / 分类 / verify agent, propose confirm-required |
| B2B SaaS onboarding (12 step) | Go-live CSM (relationship moment) | data import hybrid, schema map hybrid |

### Sub-step decomposition 80/20 examples

| Step (judgment-looking) | Det 80% | Judgment 20% (human) |
|---|---|---|
| Income verify | OCR payslip + sum 12-month + compare DTI threshold | "Stable enough?" + edge case |
| Appraisal review | extract value + compare listing + lookup comparable | "Reasonable given comparable?" + "Order 2nd appraisal?" |
| Credit interpret | score lookup + categorize + late payment count + utilization + length + inquiries | "Concerning patterns?" + "Approve based on this profile?" |
| Refund tier | amount + reason category + customer history + fraud signal | "Tier 3 escalate to legal?" |
| Customer support intent | regex + pattern match + KB lookup | "Sentiment escalation?" |

### Phase advancement criteria matrix

| Phase | Advance gate metric | Threshold |
|---|---|---|
| 1 → 2 | Override rate (deterministic steps) | < 10% |
| 1 → 2 | Time saved % | > 20% |
| 1 → 2 | Customer sign-off | required |
| 2 → 3 | Auto-step error rate | < 1% |
| 2 → 3 | Time saved % | > 40% |
| 3 → 4 | Escalation rate (auto + escalate) | < 5% |
| 3 → 4 | Customer satisfaction | ≥ baseline |
| 4 maintenance | Autonomous decision error | < 0.5% |
| any phase rollback | Any metric | > 2× threshold |
