## 题目

> "Design **human-agent interaction patterns** for a customer support chatbot. When should the agent: (a) act autonomously, (b) ask the user to confirm, (c) ask a human agent to take over? Walk through the **escalation logic** end-to-end."

或追问形态:

> "Agent confidence is hard to calibrate. How do you decide 'agent confident enough to act' vs 'needs human'?"

**Round**: Human-Agent UX / Interaction Design (45-60 min)

---

## 这道题在考什么

考你**human-in-the-loop product design**:

1. **4 interaction patterns** —— co-exist
2. **Confidence calibration** —— LLM scores unreliable raw
3. **Escalation paths** —— smooth, not jarring
4. **State preservation** —— human sees what agent did
5. **Trust building** —— UX teaches user when to trust

---

## 必问 clarifying

**1. Use case**

> "Customer support — chat / email / voice? Different escalation UX."

**2. Operating hours**

> "Human agents 24/7 or only daytime? Affects fallback design."

**3. Stakes**

> "Common queries (FAQ) or money/account changes? Different friction."

**4. Volume**

> "Q/day or Q/sec? Affects how many humans needed."

**5. Customer demographic**

> "Tech-savvy or not? Affects how to communicate confidence / escalation."

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify use case / hours / stakes |
| 5-15 min | 4 interaction patterns overview |
| 15-25 min | Confidence calibration |
| 25-35 min | Escalation paths + state transfer |
| 35-45 min | Observability + iteration |

---

## 我会这样答（sample）

> "Clarify — *[假设: chat support 24/7, common = FAQ, some = account changes, 10K Q/day, mainstream consumer]*.
>
> **4 interaction patterns — coexist in same product**:
>
> **A. Confidence threshold escalation**
>
> Agent tries, if not confident → human.
>
> ```python
> async def handle(user_msg):
>     response, confidence = await agent.respond(user_msg)
>     if confidence < THRESHOLD:
>         await escalate_to_human(user_msg, agent_draft=response)
>     else:
>         return response
> ```
>
> **B. Confirm-required for destructive**
>
> Agent drafts, user approves before execution.
>
> ```python
> if action.is_destructive:
>     draft = await agent.draft(action)
>     confirmed = await ui.confirm(draft)  # 'About to refund $50. Confirm?'
>     if confirmed:
>         await execute(action)
> ```
>
> **C. Scheduled review** (post-hoc human oversight)
>
> Agent acts autonomously, human reviews sample later.
>
> ```python
> # Daily batch
> for action in agent_actions_yesterday:
>     if random.random() < 0.05:  # 5% sample
>         await queue_for_human_review(action)
>
> # If reviewer marks as wrong → train signal + alert
> ```
>
> **D. User-initiated takeover**
>
> User can type `/human` any time → routed to human agent.
>
> ```python
> if 'speak to human' in user_msg.lower() or user_msg.startswith('/human'):
>     await route_to_human(conversation_history)
> ```
>
> **All 4 coexist** — different scenarios. Most products start with A + B + D, add C later.
>
> **Decision matrix per query type**:
>
> | Query type | Pattern | Why |
> |---|---|---|
> | 'What's my balance?' | A (auto) | Low stakes, deterministic |
> | 'Reset my password' | B (confirm) | Action with consequence, identity-protective |
> | 'Refund $500' | B (confirm) + D (offer human) | High stakes, complex |
> | 'I'm angry, you suck' | D (auto human) | Sentiment detects, human relationship |
> | 'How do I file a tax form for my country?' | A with low conf → D | Specialized, agent uncertain |
> | New / weird question | A + D fallback | Unknown territory |
>
> **Confidence calibration** — the hard part:
>
> Raw LLM confidence (token log-prob) is **unreliable**:
> - Same answer can score high one prompt, low another
> - Confidence ≠ correctness
> - Models often overconfident
>
> **Better signals**:
>
> 1. **Self-consistency**: same query 3 times → if all 3 agree, more confident
>    ```python
>    answers = [await agent.respond(query) for _ in range(3)]
>    consistency = len(set(answers)) == 1  # all same
>    ```
>
> 2. **Tool-grounding**: does answer cite retrieved docs? If hallucinated (no citation), low confidence.
>
> 3. **Schema validation**: structured output passes schema?
>
> 4. **Out-of-distribution detection**: query semantically novel vs known successful queries?
>    ```python
>    nearest = vector_db.search(query, top_k=1)[0]
>    if nearest.distance > THRESHOLD:
>        confidence_modifier = -0.3  # novel territory
>    ```
>
> 5. **Sentiment / complexity**: long / multi-part / negative sentiment → escalate
>
> 6. **Explicit refusal**: agent says 'I don't know' / 'consult a professional' → flag
>
> Combine into composite score:
>
> ```python
> def composite_confidence(response_data):
>     score = 1.0
>     if response_data.self_consistency_check_failed:
>         score *= 0.5
>     if not response_data.has_citations:
>         score *= 0.7
>     if response_data.ood_distance > 0.4:
>         score *= 0.6
>     if response_data.contains_refusal:
>         score = 0.0
>     return score
> ```
>
> **Calibration via eval**:
>
> ```python
> # On 500 known-answer queries
> for q in eval_set:
>     agent_response, agent_confidence = agent.respond(q)
>     is_correct = check_correctness(agent_response, q.expected)
>     log(agent_confidence, is_correct)
>
> # Plot: bucket confidence 0.1, 0.2, ..., 0.9 — within each, % correct should match
> # If 0.9 confidence = only 60% correct → uncalibrated, agent overconfident
> # Apply calibration (Platt scaling / isotonic regression)
> ```
>
> **Threshold tuning**:
>
> ```
> Confidence > 0.85 → auto-respond
> 0.5 < conf < 0.85 → respond but offer human option ('not sure? talk to human?')
> conf < 0.5 → preempt: 'let me get a human for this'
> ```
>
> **Escalation handoff — smooth UX**:
>
> When escalating to human:
>
> ```python
> async def escalate_to_human(conv, agent_draft=None):
>     human = await assign_agent(conv.topic, conv.priority)
>     await human.notify({
>         'conversation': conv.history,
>         'agent_understanding': conv.agent_state.summary,
>         'agent_attempted_response': agent_draft,
>         'agent_concerns': conv.agent_state.flags,
>         'user_sentiment': conv.user_sentiment_score,
>     })
>     # User sees:
>     await conv.send_message(
>         "I'm connecting you with a specialist who can help. "
>         "They have the context of our conversation."
>     )
> ```
>
> **Critical**: human sees agent's work, doesn't restart from zero. **No 'tell me your problem again'**.
>
> **State transfer specifics**:
>
> Human agent UI shows:
> - Full conversation transcript
> - Agent's intent classification
> - Agent's attempted actions + results
> - User's account context (authorized lookup)
> - Suggested next action (from agent)
> - Time on conversation (helps with prioritization)
>
> Human agent can:
> - Take over fully
> - Approve agent's draft
> - Edit agent's draft + send
> - Hand back to agent ('agent take over, I'll watch')
>
> **Returning user**:
>
> Next time user comes back, prior escalation reason logged → agent knows to default to human-mediated for similar topics.
>
> **Observability**:
>
> | Metric | Why |
> |---|---|
> | Confidence calibration plot | Agent accuracy by confidence bucket |
> | Escalation rate per type | Where agent struggles |
> | Human override rate (after agent attempt) | Agent quality |
> | User satisfaction by path (auto / confirm / human) | UX comparison |
> | Time-to-resolution by path | Speed vs quality |
> | 'False escalation': human resolves trivially | Agent too conservative |
> | 'Missed escalation': low confidence agent answered anyway, was wrong | Agent too aggressive |
>
> **What NOT to do**:
> - Trust raw LLM confidence (uncalibrated)
> - Sudden escalation without context transfer
> - Always human (no automation value)
> - Always auto (no safety net)
> - No threshold tuning (one-size-fits-all)
> - No user-initiated takeover option"

---

## 多场景变体 + 解法

### 变体 1: Coding agent (Cursor / Copilot-style)

> "Coding agent 写代码 + apply diff。何时停下问 dev?"

**解法**:
- **Auto-apply** for small / non-destructive (单文件 < 20 行 + 在 git working tree 内)
- **Confirm-required** for: > 1 文件 / > 100 行 / delete file / 改 config (CI / deploy)
- **Test gate**: agent 跑 test, fail 时 必 dev review (不强 apply)
- **Diff preview UI**: dev 能 inspect, accept / reject 部分 hunk
- **Branch isolation**: agent 在 agent/* 分支, main 永远 PR
- **Takeover**: dev 改 file 直接覆盖, agent 不 fight

### 变体 2: 医疗 triage

> "AI triage 助手 — patient 描述症状, 决定急诊 / 普通门诊 / 家庭医生"

**解法**:
- **保守 default**: 不确定 → 上调到更严重 tier (false positive 比 false negative 好)
- **Confirm-required** for downgrade: 'symptoms mild → primary care' 需 nurse 确认
- **Red flags 永远人**: 胸痛 / 呼吸困难 / neurological → 不 triage, 直接 ER
- **Confidence + explainability**: 不只给决定, 给 reasoning, nurse 能 sanity check
- **Doctor takeover trivial**: 任何时候 nurse / doctor 可 override agent
- **Audit + outcome track**: triage → 实际 outcome 对账, miss 严重的 root cause

### 变体 3: Sales agent

> "AI sales 跟客户 chat。何时 handoff 到真 sales?"

**解法**:
- **High-value signal**: deal size estimate > $X → 立即 human sales
- **Decision-maker signal**: 客户提企业 / 角色高 → human
- **Stuck signal**: 多轮 user 重复同 question → agent 答不到 → 转人
- **Emotion / negative**: sentiment → 不愉快 → 转人
- **Buying signal**: '想试用' / '价格几何' → 转 human close
- **Agent 默默学**: 每次 handoff 后, sales 看 transcript, feedback 给 agent

### 变体 4: Internal IT helpdesk

> "AI 接 IT ticket, 何时转 IT engineer?"

**解法**:
- **L1 vs L2/L3**: 密码 / 软件安装 / Wi-Fi (L1) — auto/self-serve; 硬件 / 网络 / 权限 (L2+) → 人
- **VIP user fast path**: CEO / VP 永远 priority + human
- **Repeat ticket**: 同 user 同 issue 第二次 → 直接转人 (前次没解决)
- **Knowledge gap**: agent KB 没覆盖 → 转 + 同时建议 KB update
- **Hardware needed**: 实物动作 → 必人
- **Audit**: 每 ticket 解决方案归档, 用于 KB / agent training

### 变体 5: Trading / financial agent

> "AI trading 助手 (建议 / 执行 trade)。何时必人?"

**解法**:
- **Threshold by amount**: < $X agent auto, > 人 confirm
- **Per-asset risk**: 流动性低 / 波动大 → 必人
- **Regulatory**: 某些 trade type (大宗 / cross-border) 法规要求人审
- **Algorithm 异常**: agent 信号 vs market move 大背离 → pause + human
- **Day-trading limit**: per-day 最多 N 笔 auto
- **Audit + 可解释**: 每 trade 决策附理由, 后续审查能复盘
- **Kill switch**: 一键停所有 agent, 风控团队随时可触发

---

## 简历专属 reframe

| 题 | 你做过 |
|---|---|
| Confidence threshold | BNPL chatbot — confidence-based routing to live agent |
| Confirm-required | Indonesia refund tier 2 — agent draft + human approve |
| Scheduled review | Voice agent — weekly metric review of agent decisions |
| User takeover | Voice agent — 'speak to human' option always available |
| State handoff | Voice agent — when transferred to live agent, transcript shared |

**Quote**:

> "BNPL chatbot did this exact pattern. Confidence threshold combined 4 signals: LLM log-prob, retrieval citations (must have for factual claim), OOD distance (novel query → low confidence), explicit refusal detection. Threshold 0.85 for auto, 0.5-0.85 for 'agent + offer human', < 0.5 for preemptive escalate. **Calibration eval** showed initial agent was overconfident — 0.8 confidence = 65% actual accuracy. Applied isotonic regression calibration → matched. After deployment, **false-escalation rate dropped from 18% to 7%**, **missed-escalation dropped from 5% to 2%**."

---

## 5 follow-ups

**Q1**: "Calibration drifts as model / data shifts. Maintain?"
**A**:
- **Continuous eval**: 5% sampled, ground-truth labeled by human
- **Weekly review**: recalibrate if drift detected
- **Re-train calibrator** on recent data
- **Alert**: if accuracy at confidence-X drops below threshold

**Q2**: "User keeps trying to bypass agent ('I want human, you're useless'). Handle?"
**A**:
- **Respect user choice**: route to human immediately
- **Don't gate the human path**: avoid making user prove they need human
- **Track**: high bypass-rate signals agent quality issue
- **Don't 'fight'**: 'OK, connecting you' beats 'let me try again'

**Q3**: "Escalation queue is full, no human available. What happens?"
**A**:
- **Queue with ETA**: 'You're #4 in line, ~5 min wait'
- **Async option**: 'Want us to email you instead?'
- **Self-serve docs**: 'While you wait, here's our help center'
- **Off-hours**: 'No agents available, here's a callback form for tomorrow'
- **Never silently drop**: always communicate

**Q4**: "Human agent disagrees with what AI did. Surface to user?"
**A**:
- **No, internally only**: don't undermine AI trust in front of user
- **Log + train signal**: feed back to model improvement
- **If correction needed**: human takes over, fixes, doesn't blame agent verbally
- **Postmortem internally**

**Q5**: "Agent confidence high but wrong (hallucination). Detect?"
**A**: Hardest case. Layers:
- **Citation enforcement**: claim → must cite source, validate
- **Fact-check second pass**: cheap LLM verifies
- **Anomaly detection**: response very different from similar queries
- **Outcome telemetry**: did action have expected effect (refund went through?)
- **User feedback loop**: thumbs / corrections

---

## ❌ 易错点

1. **Single pattern** (only auto or only human)
2. **Trust raw LLM confidence**
3. **Sudden escalation** (user re-explains everything)
4. **No threshold tuning** per query type
5. **No calibration eval** — confidence numbers don't mean correctness
6. **No takeover option** — user trapped with bad agent
7. **No observability** — escalation patterns invisible

---

## ✅ 加分项

1. **4 patterns coexist** explicitly
2. **Composite confidence** (5+ signals)
3. **Calibration eval + recalibration**
4. **Smooth handoff** with full state
5. **Tiered threshold** (auto / offer / preempt)
6. **Off-hours / queue full handling**
7. **False / missed escalation observability**
8. **Quote BNPL calibration story**

---

## Cheat Sheet

```
4 interaction patterns (coexist):
  A: Confidence threshold escalation
  B: Confirm-required for destructive
  C: Scheduled human review (post-hoc)
  D: User-initiated takeover (/human)

Composite confidence signals:
  1. LLM log-prob (raw, unreliable alone)
  2. Self-consistency (3 runs agree)
  3. Tool-grounding (citations present)
  4. Schema validation
  5. OOD detection (vector distance)
  6. Sentiment / complexity
  7. Explicit refusal detected

Calibration:
  Eval set of 500 known-answer queries
  Plot confidence bucket vs % correct
  Apply Platt / isotonic regression
  Recalibrate weekly / on drift

Threshold tiers:
  > 0.85: auto-respond
  0.5-0.85: respond + offer human
  < 0.5: preempt escalate

Escalation handoff:
  Show human: transcript + intent + draft + concerns
  No re-explain from user
  Human can: take over / approve / edit / hand back

Off-hours / queue full:
  Queue with ETA
  Async option (email back)
  Self-serve docs
  Callback form
  Never silent drop

Observability:
  Calibration plot
  Escalation rate per query type
  Human override rate
  User satisfaction by path
  Time-to-resolution by path
  False escalation (human trivial)
  Missed escalation (low conf agent wrong)

User-initiated takeover:
  Don't gate
  Respect immediate
  Track bypass rate (agent quality signal)

红线:
  - Single pattern
  - Raw LLM confidence
  - Sudden escalation
  - No threshold tuning
  - No calibration
  - No takeover option
  - No observability
```
