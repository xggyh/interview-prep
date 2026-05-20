## 题目

> "Customer's loan-approval team has a **manual 12-step workflow**: receive application → KYC check → credit check → income verify → property appraisal → ... → approve / decline. Each step takes minutes-to-days, human-mediated. Convert this into an **agent workflow**. Which steps go to agent, which stay human, which are hybrid?"

或追问形态:

> "Walk through how you decide what's automatable vs what stays human, and how the agent and humans collaborate."

**Round**: FDE Workflow Design (45-60 min)

---

## 这道题在考什么

考你**workflow → agent abstraction** + product sense:

1. **3 questions per step** (Deterministic / Reversible / Latency)
2. **Hybrid 是常态** not exception
3. **Human handoff** smooth design
4. **State persistence** across human-mediated pauses
5. **Trust ladder** —— agent autonomy grows over time

---

## 必问 clarifying

**1. Current pain**

> "Which step has longest delay / most errors today? Where do customers complain?"

**2. Regulatory**

> "KYC / credit check legally require human eyes-on or AI-allowed by jurisdiction?"

**3. Data systems**

> "Which steps already have APIs (credit bureau)? Which manual / paper?"

**4. Decision authority**

> "Final approval — committee / single person / role-based? Agent assists or decides?"

**5. Volume**

> "10 apps/day or 1000? Affects automation ROI."

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify pain / regulatory / volume |
| 5-15 min | 3-question framework per step |
| 15-25 min | Apply to 12 steps (matrix) |
| 25-35 min | Hybrid design (human handoff) |
| 35-45 min | Trust ladder + rollout |

---

## 我会这样答（sample）

> "Clarify — *[假设: longest delay = appraisal (3-5 days), KYC must be human-verified per regulator, credit bureau has API, single underwriter decides final, 100 apps/day]*.
>
> **3-question framework per step**:
>
> 1. **Deterministic?** Same input → same output? Or requires human judgment?
> 2. **Reversible?** Easy to undo, or irreversible?
> 3. **Latency-sensitive?** Real-time response or async OK?
>
> **Outcome category**:
> - Deterministic + Reversible + Async OK → **Agent automate**
> - Deterministic + Irreversible → **Confirm-required agent** (draft, human approves)
> - Judgment-heavy → **Agent assist, human decide** (or pure human)
> - Latency-sensitive → **Real-time agent with fallback**
>
> **Apply to 12 steps**:
>
> | # | Step | Determ? | Revers? | Latency? | Owner |
> |---|---|---|---|---|---|
> | 1 | Receive application | Yes | Yes | Real-time | **Agent**: parse + acknowledge |
> | 2 | KYC check | Mixed | No | Async | **Hybrid**: agent gathers docs + scoring, human verifies identity |
> | 3 | Credit bureau pull | Yes | Yes | Real-time | **Agent**: API call |
> | 4 | Credit score interpret | Mostly | Yes | Async | **Agent**: with edge-case escalation |
> | 5 | Income verify (payslips / W2) | Mixed | Yes | Async | **Agent assist**: OCR + extract, human spot-check |
> | 6 | Employer verify (phone call) | No | Yes | Async | **Human**: voice agent could draft script |
> | 7 | Property appraisal request | Yes | Yes | Async | **Agent**: schedule + track |
> | 8 | Appraisal review | Judgment | Yes | Async | **Hybrid**: agent extracts numbers + flags anomalies, human validates |
> | 9 | Debt-to-income calc | Yes | Yes | Real-time | **Agent**: deterministic formula |
> | 10 | Risk assessment | Judgment | Yes | Async | **Agent assist**: ML model score + reasoning, human reviews |
> | 11 | Final decision | Judgment | No | Async | **Human**: underwriter, agent provides full summary |
> | 12 | Communicate decision | Yes | Mostly | Async | **Confirm-required agent**: drafts email/letter, underwriter signs off |
>
> **Where automation wins**:
>
> - **Step 1, 3, 9** (deterministic, structured) → full automation, save days
> - **Step 5, 8** (data extraction) → 90% automation, human spot-check 10%
> - **Step 12** (templated comms) → draft + 1-click send
>
> **Where human stays**:
>
> - **Step 2 KYC** (regulator requires)
> - **Step 6 employer call** (judgment + relationship)
> - **Step 11 final decision** (legal liability)
>
> **Hybrid design — handoff smooth**:
>
> ```python
> # Per-step state machine
> step_state = {
>     'step_id': 2,
>     'name': 'KYC',
>     'state': 'awaiting_human_verify',  # or 'agent_running', 'completed', 'failed'
>     'agent_output': {
>         'docs_gathered': [...],
>         'preliminary_score': 0.87,
>         'flagged_concerns': [...],
>     },
>     'human_assigned': 'reviewer_42',
>     'sla_due': '2026-05-25 17:00',
> }
> ```
>
> **Workflow orchestration**:
>
> Use Temporal (durable workflow engine):
>
> ```python
> @workflow.defn
> class LoanWorkflow:
>     @workflow.run
>     async def run(self, application):
>         # Step 1: Agent receives + parses
>         parsed = await activity(parse_application, application)
>         
>         # Step 2: Hybrid KYC
>         agent_kyc = await activity(agent_kyc_prep, parsed)
>         human_kyc = await activity(
>             human_kyc_verify, 
>             agent_kyc,
>             timeout=timedelta(days=1),
>         )
>         if not human_kyc.passed:
>             return await activity(send_kyc_failure, ...)
>         
>         # Step 3-4: Agent automate
>         credit = await activity(get_credit_score, parsed.identity)
>         interpretation = await activity(agent_interpret_credit, credit)
>         
>         # ... etc
>         
>         # Step 11: Human final decision
>         final = await activity(
>             human_underwriter_review,
>             all_prior_data,
>             timeout=timedelta(days=3),
>         )
>         
>         # Step 12: Confirm-required agent comms
>         draft = await activity(agent_draft_communication, final)
>         human_approved = await activity(human_approve_comms, draft, timeout=timedelta(hours=4))
>         await activity(send_communication, human_approved)
> ```
>
> **Human task UI**:
>
> When agent hands off to human, the human sees:
> - **Agent's preliminary work** (don't redo, augment)
> - **Specific question to answer** (not 'review everything')
> - **Time SLA** displayed
> - **Quick actions** (approve / decline / kick-back / escalate)
>
> Example:
>
> ```
> [Loan #4283 — KYC review needed]
>
> Agent gathered:
> - Driver's license: matches DOB on application ✓
> - Address: matches utility bill ✓
> - SSN: bureau confirms identity ✓
>
> Agent flags 2 concerns:
> - Name on bank statement: 'J. Smith' vs application 'John Smith' (likely same)
> - Address change in last 6 months
>
> [Approve] [Request more info] [Decline] [Escalate]
> ```
>
> Human decision in 2 min instead of 20.
>
> **Trust ladder — rollout strategy**:
>
> Don't go from 0 → autonomous overnight:
>
> | Phase | Agent autonomy | Human role |
> |---|---|---|
> | **0** | Manual | Full |
> | **1** | Agent suggests for steps 1, 3, 9, 12 | Reviews everything |
> | **2** | Agent auto-runs steps 1, 3, 9; drafts 12 | Spot checks |
> | **3** | Agent auto + escalates outliers | Reviews escalations |
> | **4** | Agent decides routine (< $100K loans) autonomously | Reviews exceptions |
>
> Each phase: 4-8 weeks of monitoring, eval, customer comfort.
>
> **Observability for hybrid workflow**:
>
> Per step:
> - Agent confidence + decision
> - Human override rate (when agent suggests A, human picks B)
> - Disagreement → training signal
> - Latency (agent ms, human hours/days)
> - Error / kickback rate
>
> If human override > 10%, agent design needs revisiting.
>
> **What NOT to do**:
> - 'Automate everything' → fail compliance + customer trust
> - 'Automate nothing' → no value
> - Agent + human work in parallel (duplicates work, conflicts)
> - No handoff protocol → human re-reads everything
> - No trust ladder → push too fast, big incident, rolled back"

---

## 简历专属 reframe

| 题 | 你做过 |
|---|---|
| Workflow → agent abstraction | BNPL chatbot — collection workflow you mapped step by step |
| Hybrid design | Indonesia refund tier — tier 1 auto, tier 2 confirm, tier 3 human |
| State persistence | TikTok payment — transactional workflows |
| Trust ladder | Voice agent — 7 markets gradual autonomy |
| Human handoff | Internal Agent Platform — confidence-threshold escalation |

**Quote**:

> "Indonesia refund tier was exactly this 3-question framework applied. Tier 1 (small, common) = fully auto, agent decides + executes. Tier 2 (moderate) = confirm-required agent, draft + human 1-click. Tier 3 (high-value / suspicious) = full human, agent provides summary. **Phase rollout**: started phase 1 (agent suggests all tiers, human reviews), 6 weeks later phase 2 (auto on tier 1), 12 weeks phase 3 (auto on tier 1+2). Each phase only advanced when human-override rate stable < 5%."

---

## 5 follow-ups

**Q1**: "Agent disagrees with human (agent says decline, human approves). Train on human?"
**A**: Carefully:
- **Yes, signal**: human override is training data
- **But**: humans can be biased / wrong
- **Audit**: random sample of overrides reviewed by senior
- **Compare to outcome**: did the human's decision pay off (loan repaid)?
- **Don't blindly fine-tune** on override data — could amplify human bias

**Q2**: "Step has both deterministic + judgment parts (e.g., income verify: extract numbers ✓ + decide if 'enough')."
**A**: **Split the step**:
- Sub-step A: extract numbers (agent)
- Sub-step B: compare to policy (agent: deterministic rule)
- Sub-step C: judgment call on edge cases (human)
- **Most 'judgment' steps decompose** into deterministic + small judgment kernel

**Q3**: "Customer wants agent autonomous on Step 11 (final decision). Push back?"
**A**: Strong push back. Reasons:
- **Legal liability**: who's accountable when AI denies a qualified borrower?
- **Regulator review**: lending decisions often regulated, need human
- **Trust**: even if technically possible, customer's customers may not accept
- **Compromise**: 'Agent provides recommendation + reasoning + flags. Underwriter signs off (10s)'. Compliance + speed.

**Q4**: "Step 6 employer call — voice agent could do it. Worth automating?"
**A**:
- Voice agent calling employer may sound robotic, employer hesitates
- **Hybrid**: voice agent calls, escalates to human in real-time when employer asks question
- **Volume math**: 100 calls/day × 5 min = 8 hours. Not huge automation ROI unless scale higher.
- **Brand risk**: a bad voice call experience tarnishes lender

**Q5**: "Phase 4 (agent decides routine loans autonomously). How decide which loans 'routine'?"
**A**:
- **Score-based**: agent confidence + risk score + amount → routine if all favorable
- **Pre-defined criteria**: amount < $X, credit > Y, debt-to-income < Z → autoroute
- **Per-jurisdiction**: regulatory bounds
- **Audit**: 10% sample reviewed by human after the fact
- **Kick-back loop**: any auto-decision can be challenged, agent learns from corrections

---

## ❌ 易错点

1. **Automate everything** — compliance fail
2. **No 3-question framework** — gut-feel automation choice
3. **Agent + human duplicate work** — no clear handoff
4. **No state persistence** — human work re-done after pause
5. **No trust ladder** — push too fast, blow up
6. **Human task UI shows everything** — overload, slow
7. **No override metric** — disagreement invisible

---

## ✅ 加分项

1. **3-question framework** explicit
2. **Per-step matrix** for the 12 steps
3. **Hybrid handoff** UI design
4. **State persistence** with workflow engine (Temporal)
5. **Trust ladder** with phases + criteria
6. **Override-rate observability**
7. **Sub-step decomposition** for judgment
8. **Quote Indonesia refund tier phased rollout**

---

## Cheat Sheet

```
3-question framework per step:
  Deterministic? same input → same output
  Reversible? easy undo
  Latency-sensitive? real-time vs async

Categorization:
  Det + Rev + Async → Agent automate
  Det + Irrev → Confirm-required (draft + approve)
  Judgment + High-stakes → Agent assist, human decide
  Latency-sensitive → real-time agent + fallback

Per-step matrix (this loan example):
  Step 1 receive → agent
  Step 2 KYC → hybrid (agent gather, human verify)
  Step 3 credit bureau → agent
  Step 4 score interpret → agent + escalate outlier
  Step 5 income verify → agent + spot-check
  Step 6 employer call → human (voice agent assist)
  Step 7 appraisal request → agent
  Step 8 appraisal review → hybrid
  Step 9 DTI calc → agent
  Step 10 risk assess → agent assist
  Step 11 final decision → human
  Step 12 communicate → confirm-required agent

Human task UI design:
  Show agent's preliminary work
  Specific question to answer
  Time SLA
  Quick actions (approve / decline / kick-back / escalate)

Workflow orchestration:
  Temporal / DBOS for durable state
  Per-step state machine
  Hand-off events
  Long-pause supported (days)

Trust ladder rollout:
  Phase 1: agent suggests all, human reviews
  Phase 2: agent auto-runs deterministic steps
  Phase 3: agent auto + escalates outliers
  Phase 4: agent autonomous on routine
  Each phase 4-8 weeks of stable override < 5%

Override observability:
  Per-step disagreement rate
  Outcome verify (was override correct?)
  Training signal (carefully — bias risk)
  Alert if rate > 10%

Sub-step decomposition:
  Judgment steps often = (determ extract) + (small judgment)
  Decompose: agent does determ, human does judgment

Anti-patterns:
  - Automate all
  - No 3-question framework
  - Duplicate work agent + human
  - No state persistence
  - No trust ladder
  - UI overload
  - No override metric
```
