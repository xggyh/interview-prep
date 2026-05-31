# 🎯 T4.2 · 业务流程 → Agent Workflow 抽象 — 冲刺版

> 完整版: [gfde-t4-workflow-abstraction.html](gfde-t4-workflow-abstraction.html). 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: 客户给 12-step manual workflow (e.g., loan approval / claim handling), 部分步骤监管要求 human, single underwriter 决策 final, 100 application/day 量, 1-2 wrong approve/month 错误容忍, GCP + Vertex AI 限定."

**核心 framing**: 90% real enterprise workflow = **hybrid**, 不是 "全 auto" 也不是 "全人". 工程上**绝大多数难点不在 LLM, 在 handoff + state + trust**.

### Layer 1: 3-Question Framework (per step 分类)

```
Q1 Deterministic? (same input → same output?)
Q2 Reversible? (can undo if wrong?)
Q3 Latency? (real-time vs async OK?)

→ 5 outcomes:
  Det + Rev + Async      → Agent automate (background)
  Det + Rev + Real-time  → Agent automate (with fallback)
  Det + Irrev            → Confirm-required agent (draft + human sign)
  Judgment + Rev         → Agent assist (draft + human decide)
  Judgment + Irrev       → Human only (agent provides context)
```

### Layer 2: 12-Step Loan Workflow 应用矩阵

| # | Step | Det? | Rev? | Owner | Why |
|---|---|---|---|---|---|
| 1 | Receive application | Y | Y | Agent | Parse + ack |
| 2 | KYC check | Mixed | N | **Hybrid** (agent prep + human verify) | 法规要求人眼 |
| 3 | Credit bureau pull | Y | Y | Agent | API deterministic |
| 4 | Credit score interpret | Mostly | Y | Agent + escalate outlier | 大多 routine |
| 5 | Income verify | Mixed | Y | Agent assist (OCR + sum) + human spot-check | Sub-step decomp |
| 6 | Employer call | N | Y | Human (agent draft script) | Relationship |
| 7 | Appraisal request | Y | Y | Agent | Scheduling |
| 8 | Appraisal review | Judgment | Y | **Hybrid** (agent extract + flag, human validate) | Numbers det, judgment human |
| 9 | DTI calc | Y | Y | Agent | Formula |
| 10 | Risk assess | Judgment | Y | Agent assist (ML score + reasoning) | Model + interpret |
| 11 | Final decision | Judgment | **N** | **Human only** | 法律责任 + 不可逆 |
| 12 | Communicate | Y | Mostly | **Confirm-required** (agent draft + underwriter sign) | Template + irrev |

**结果**: 8/12 agent 参与, 4/12 纯人. **Customer keeps human touch on judgment + irreversible, agent handles deterministic 80%**.

### Layer 3: Hybrid Handoff UI (smooth transition)

**Bad** (常见): "Loan #4283 needs review, click here" → human 读 30 页 PDF → 20 min.
**Good**: human dashboard 显示 agent prep + flagged concerns + 1-click actions + SLA → 2 min decide.

**Checklist** (每个 hybrid step UI 必含):
- Agent's preliminary work (visible)
- Specific Q to answer ("Approve KYC" 比 "Review all" 清楚)
- Flagged concerns (agent's uncertainty)
- Quick actions 1-click (Approve / Decline / Kick-back / Escalate)
- Time SLA (deadline 可见)
- Context links (raw doc on demand)
- Audit log (prior agent steps)
- Notes field (后续 audit)
- Disagree path (training signal)

### Layer 4: State Persistence — Workflow Engine

朴素 Python script restart 丢 state. 用 **Temporal** (90% 选择 for enterprise) 持久化每 step. Pattern: `workflow.execute_activity(parse_application, ..., timeout=5m)` for durable steps + `workflow.wait_for_signal('kyc_verified', timeout=days=3)` for human waits (signal-based, 可等 days).

**Temporal core features**: Durable activities (per-step DB persisted) / Signals (wait for external event) / Timeouts (SLA enforcement) / Retry policies / Replay (time-travel debug) / Versioning (multi-version coexist) / Saga compensation (failure undo).

### Edge cases (5 个最高频)

- **EC1 Agent disagree with human (agent decline, human approve)**: Signal-rich training data, but humans biased/inconsistent. Outcome-based label (1-yr repay history) > raw human override. Audit random sample, 别 blindly fine-tune.
- **EC2 Step mixed Det + Judgment (income verify)**: Sub-step decomposition — extract numbers (agent) + threshold compare (agent) + judgment kernel (human). 80/20: 80% time agent, 20% human.
- **EC3 客户要 agent autonomous on Step 11 (final decision)**: **Strong push back**. Legal liability + 监管 (Fair Lending Act) + discrimination risk + customer trust. Compromise: agent recommends + underwriter signs 10 sec for routine.
- **EC4 Step 6 employer call automate?**: Voice agent calling employer sounds robotic, employer hesitates. Hybrid — agent **drafts script** for human caller. Volume math: 100 calls × 5 min = 8 hr, ROI 不大. Revisit Phase 5+ 当 voice quality improves.
- **EC5 Phase 4 routine autonomous criteria**: Pre-defined sign-off — loan < $100K + credit > 720 + DTI < 35% + no red flag + within standard product + existing customer track record. 10% sampled by human audit. Per-jurisdiction bound. Quarterly review.

### Production hardening (Trust Ladder 4 Phase)

```
Phase 0 baseline:    全人工
Phase 1 (wk 1-8):    Suggest mode, human approves all
  advance: override < 10%, time saved > 20%
Phase 2 (wk 8-16):   Auto-execute deterministic steps
  advance: error < 1%, time saved > 40%
Phase 3 (wk 16-32):  Auto + escalate outliers
  advance: escalation < 5%, satisfaction OK
Phase 4 (wk 32+):    Autonomous on routine (criteria-defined)
  audit: 10% human sample
  Stays human regardless: Step 11 final + Step 6 employer call
```

**Rollback**: 任何 phase 指标 > 2x threshold → rollback to previous phase + investigate.

### 🪝 Resume hook

"Indonesia refund tier 就是这套 3-question framework. Tier 1 (small < IDR 50K, routine 'wrong item') = fully auto agent decides + executes. Tier 2 (moderate IDR 50K-500K) = confirm-required (agent draft + ops 1-click sign). Tier 3 (high-value > IDR 500K / fraud signal / VIP) = full human (agent provides summary). Phase rollout — wk 1-6 Phase 1 agent suggests all + human reviews all, wk 6-12 Phase 2 auto on tier 1, wk 12+ Phase 3 auto tier 1+2 + human tier 3. Each phase advance only when human-override rate stable < 5% over 2-week window. ONE incident in Phase 2 — agent loop bug auto-refunded duplicate, anomaly detector caught 4 min, bulk reverted via compensating handler 12 min. Postmortem → fix → new safeguard (per-customer daily refund cap)."

---

## 🔥 5 Follow-ups

**Q1: Agent 和 human disagree (agent decline, human approve). 训 agent on human label?**
Carefully. Yes signal (human override 是 rich data), but humans biased/inconsistent. **Outcome-based label** (loan repaid?) > raw override. Audit sample by senior. Combine: weight outcome-confirmed higher than raw override. 不要 blindly fine-tune.

**Q2: Step 是 mixed (income verify = extract numbers ✓ + decide if "enough")?**
Sub-step decomposition. (a) OCR extract (agent) / (b) sum 12-month (agent) / (c) compare threshold (agent) / (d) judgment "is income stable?" (human) / (e) "ask more docs?" (human). 80% time in a-c, 20% in d-e. 80% efficiency without giving up judgment.

**Q3: 客户要 agent autonomous on Step 11 (final decision). Push back?**
**Yes strongly**. Legal liability (谁 accountable for AI denial?) + regulator (Fair Lending Act) + discrimination risk (bias hard to prove absent) + customer trust. Compromise: agent recommends + reasoning + flagged concerns. Underwriter signs 10 sec for routine (vs 10 min manual). Speed + compliance + legal safety.

**Q4: Step 6 employer call — voice agent could do it. Worth?**
Robot voice → employer hesitates to verify info. Hybrid — voice agent drafts script for human caller (saves prep). Volume math: 100 calls × 5 min = 8 hr/day, ROI 不大. Revisit Phase 5+ 当 voice 改进 + employer accept AI.

**Q5: Phase 4 — 哪些 loan 算 "routine"?**
Pre-defined criteria (sign-off with underwriter team): loan < $X (e.g., $100K) + credit > Y (720) + DTI < Z (35%) + no red flag + within standard product + existing customer w/ track record. Per-jurisdiction bound. 10% human sample audit. Kick-back loop. Quarterly review.

---

## ❌ 易错点 (10 条红线)

1. **Automate everything** — 法规违规 (KYC) + 不可逆错 + 信任崩
2. **No 3-question framework** — gut-feel automation choice
3. **Agent + human duplicate work** — no clear handoff protocol
4. **No state persistence** — human work re-done after pause
5. **No trust ladder** — push too fast, 1st incident → 全 rollback
6. **Human task UI shows everything** — overload, 30-min review instead of 2-min
7. **No override metric** — disagreement invisible
8. **Atomic step assumption** — judgment step locked as human-only (miss 80% decomposition)
9. **No SLA / timeout** — workflow stuck waiting human forever
10. **No customer-visible phase tracker** — customer doesn't see your discipline

---

## ✅ 加分项 (12 条)

1. 3-question framework explicit (Det / Rev / Latency)
2. Per-step matrix for 12 steps with rationale
3. Hybrid handoff UI checklist (prep / Q / actions / SLA)
4. State persistence with Temporal (signal-based human wait)
5. Trust ladder 4 phase + advancement criteria
6. Override-rate observability + alert on drift
7. Sub-step decomposition for "judgment" step (80/20 split)
8. Customer-visible phase tracker + live KPI
9. Per-jurisdiction Phase 4 criteria (loan < $X + credit > Y + DTI < Z)
10. Signal-driven human wait with timeout + escalate
11. Saga / compensation for failed step undo
12. Indonesia refund tier phased rollout + incident story (4 min anomaly catch)

---

## 一句话总结

T4.2 = **3-question framework 分类每步 + Temporal-like engine 持久 state + 4-phase trust ladder 渐进 autonomy + hybrid handoff UI 不让人重读 + sub-step decomposition 把 judgment 拆到 80% 可 auto**. 工程上**绝大多数难点不在 LLM, 在 handoff + state + trust**.

---

## 🃏 Cheat Sheet (印 1 页)

```
3-question framework (per step):
  Q1 Deterministic? Q2 Reversible? Q3 Latency-sensitive?

5 categorization outcomes:
  Det + Rev + Async    → Agent automate (background)
  Det + Rev + RT       → Agent automate (with fallback)
  Det + Irrev          → Confirm-required (draft + sign)
  Judgment + Rev       → Agent assist (draft + human decide)
  Judgment + Irrev     → Human only (agent context)

12-step loan workflow:
  1  Receive          → Agent
  2  KYC              → Hybrid (agent gather + human verify)
  3  Credit pull      → Agent
  4  Credit interpret → Agent + escalate outlier
  5  Income verify    → Agent 80% + human 20% judgment
  6  Employer call    → Human (agent draft script)
  7  Appraisal req    → Agent
  8  Appraisal review → Hybrid
  9  DTI calc         → Agent
  10 Risk assess      → Agent assist
  11 Final decision   → Human (always, legal liability)
  12 Communicate      → Confirm-required

Hybrid handoff UI checklist:
  Agent prep visible / Specific Q to answer /
  Flagged concerns / 1-click quick actions /
  Time SLA / Context links / Audit log /
  Notes field / Disagree path (training signal)

Workflow engine:
  Temporal  90% choice, enterprise (durable, signals, replay, saga)
  DBOS / AWS Step Functions / self-built (only simple)

Trust Ladder 4 phases:
  Phase 1 (w1-8):   Suggest mode, human approves all
    advance: override < 10%, time saved > 20%
  Phase 2 (w8-16):  Auto deterministic + reversible
    advance: error < 1%, time saved > 40%
  Phase 3 (w16-32): Auto + escalate outlier
    advance: escalation < 5%
  Phase 4 (w32+):   Autonomous on routine (criteria-defined)
    audit: 10% human sample
  Stays human regardless: final decision + employer call

Sub-step decomposition:
  Judgment-looking step = (det extract × 80%) + (judgment kernel × 20%)
  Agent: extract / lookup / compute / threshold (80%)
  Human: judgment kernel (20%)
  → 80% efficiency without giving up judgment

Override metric:
  Per-step disagreement rate (alert > 10%)
  Outcome verify (was override correct retrospectively?)
  Training signal carefully (bias risk)

Customer-visible:
  Phase tracker / Live KPI / Roadmap (Phase 2/3/4)

Anti-patterns (红线):
  - Automate all / No 3-question / Duplicate agent+human
  - No state persistence / No trust ladder / UI overload
  - No override metric / Atomic step assumption / No SLA

Resume hooks:
  - BNPL chatbot collection workflow map
  - Indonesia refund tier 1/2/3 phased rollout
  - Voice agent escalation transcript transfer
  - TikTok payment Temporal-like durable workflow
```
