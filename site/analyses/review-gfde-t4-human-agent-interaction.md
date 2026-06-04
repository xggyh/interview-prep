## T4.3 · human-agent interaction — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](gfde-t4-human-agent-interaction.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t4-human-agent-interaction.html`](gfde-t4-human-agent-interaction.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"你的 chatbot 什么时候 escalate 给 human? 怎么 escalate 不让用户感觉断裂?"** 我按这 7 层回答, 不跳序.

### 📐 Human-Agent Interaction — 7 层 coexist + calibrate + handoff

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 |
|---|---|---|---|---|
| 1 | 拒绝 "single rule" 框架 | 30s | 反 single-trigger ("confidence < 0.7 escalate"), 因为 4 种触发条件本质不同 — 必须 coexist | "First — escalation is not a single rule. I run 4 patterns coexisting…" |
| 2 | 4 pattern coexist (A/B/C/D) | 2 min | A confidence threshold (uncertainty trigger) + B confirm-required (irreversibility trigger) + C scheduled human review (drift detection trigger) + D /handoff user-initiated (frustration / emotion trigger) — 4 个 trigger 解决 4 个 不同问题 | "Pattern A handles uncertainty, B handles irreversibility, C handles drift, D handles emotion…" |
| 3 | Per-query-type matrix | 2 min | 不是一个 0.7 cutoff 全场, 而是 per-intent × per-action 矩阵: FAQ (threshold 0.5, no confirm), account_query (0.7, no confirm), refund < $50 (0.7, confirm 1-tap), refund > $200 (0.85, confirm 2-step + tier-2 review), dispute (force human) | "Threshold is per intent × per action — not a single global cutoff…" |
| 4 | Confidence calibration (composite) | 2 min | LLM raw logprob 不可信. Composite = 5+ signal: (a) LLM top-1 logprob, (b) retrieval similarity score, (c) intent classifier softmax margin, (d) tool-call schema validation pass, (e) historical user-feedback for this intent. Platt scaling / isotonic regression 校准成 well-calibrated probability | "Raw LLM confidence is uncalibrated — I compose 5+ signals and fit Platt/isotonic…" |
| 5 | Smooth handoff mechanics | 1.5 min | 3 必备: (a) Agent prep summary visible to human first responder (transcript + intent + last action + customer profile), (b) human's first line auto-references context ("Hi Sari, I see you were asking about refund #1234, let me help…"), (c) user side gets "transferring you to specialist" not "agent failed" — 0 friction perceived | "Handoff is 3 mechanics — prep summary, context-aware first line, framed transition…" |
| 6 | False / missed escalation observability | 1.5 min | 2 误差类型监控: false escalate (agent could have handled but bailed → cost) vs missed escalate (agent shouldn't have handled, bad outcome). Calibration plot weekly (expected vs actual error rate per confidence bucket), per-path CSAT, weekly Mon review 50 random by scheduled pattern C | "Two error types to track — false-escalate and missed-escalate — both on weekly review…" |
| 7 | Indonesia refund tier resume hook | 1 min | "Concrete: Indonesia refund tier — all 4 pattern in prod. Tier 1 (auto < $20) confidence > 0.7. Tier 2 ($20-200) confirm-required + agent suggests, customer 1-tap. Tier 3 (> $200 OR fraud signal) forced human, tier-2 ops review. /handoff anytime. Result: CER 18→25%, fraud ↓40%, NPS ↑8 pts. The 4 patterns are why it works" | "Real example — Indonesia refund tier with all 4 patterns…" |

### 🎯 为啥按这个序

Layer 1 "reject single rule" 立刻区分有 production agent 经验 vs 没有. 4 pattern coexist 是 frame, per-query-type matrix 是 zoom-in — 必须先 frame 再 zoom. Calibration 在第 4 层因为前面 3 层把 "什么时候 escalate" 讲完了, 这层讲 "我怎么知道 confidence 数字可信". Handoff mechanics + observability 是 production-only knowledge. Indonesia hook 用真实数字 land.

### 🔥 哪一层最容易被追问 deeper

**Layer 4 (calibration)** — 必被追 "How do you actually calibrate?" → 答: collect 10k labeled outcomes from production over 4 weeks; bucket by composite confidence (0.5/0.6/0.7…); plot expected error rate vs actual; fit isotonic regression (monotonic, doesn't assume shape) on validation set; deploy. Re-calibrate monthly because model + user pattern drift. LangSmith for tracing, custom calibration job in Airflow.

**Layer 5 (handoff)** — 追 "What if human is busy / queue is long?" → 答: pre-handoff 3 path — (a) if SLA < 2 min available human, route normal; (b) if queue 2-10 min, agent says "putting you in queue, ETA X min, want callback?"; (c) if queue > 10 min, offer async ticket with priority flag. Never silent-wait — explicit ETA always.

### ⏱ 时间压缩版 (30 min round)

- 0-3 min: Layer 1+2 (single rule reject + 4 pattern frame)
- 3-10 min: Layer 3+4 (per-query matrix + calibration)
- 10-18 min: Layer 5+6 (handoff + false/missed observability)
- 18-25 min: Layer 7 (Indonesia 4-pattern, CER 18→25, fraud ↓40, NPS ↑8)
- 25-30 min: Q&A buffer

### 🆘 卡壳兜底 (针对这题)

- 不会校准 → "calibrate weekly using isotonic regression on labeled production outcomes; LangSmith 抓 trace + custom job"
- 被问 "how to handle agent over-escalating (lazy)" → "track false-escalate rate per intent; if false rate > 30% for one intent, action item is prompt + threshold rework, not human staffing"
- 客户 demand 100% automation → "I show false vs missed cost matrix — refund > $200 missed-escalate could cost $X per incident vs false-escalate cost human 30s. Math forces 4-pattern coexist"

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 核心心智模型 (1 sentence)

Human-Agent Interaction = "4 pattern coexist (A confidence threshold + B confirm-required + C scheduled review + D user-takeover) + calibrated composite confidence (5+ signal + Platt/isotonic regression) + smooth handoff (agent prep visible, human first line refs context) + per-type observability (calibration plot, false/missed escalation, per-path CSAT) + weekly iteration", 90% chatbot 失败不是 LLM 不行而是 4 pattern coexist 没设计 / confidence 没校准 / handoff 不顺.

### 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| HAI | user × agent × human 三角交互 | 整体框架 |
| Pattern A | confidence threshold escalation (auto / offer / preempt) | 大部分 info query |
| Pattern B | confirm-required for destructive (refund / pwd reset) | irreversible action |
| Pattern C | scheduled human review (post-hoc 5% sample audit) | 持续 quality monitor |
| Pattern D | user-initiated takeover (/human, no friction) | 用户明确表达 |
| Composite confidence | 5+ signal 合成 (logprob + self-consist + citation + schema + OOD + complexity + refusal) | 不信 raw LLM logprob |
| Platt scaling | sigmoid logistic regression 校准, 数据少时用 | 500 sample 以下 |
| Isotonic regression | non-monotonic 校准, 数据多时用 | 500+ sample |
| Calibration drift | 任意 bucket > 10% off diagonal | 周 alert |
| False escalation | human resolves trivially (< 30 sec) | agent 太保守 |
| Missed escalation | auto-respond turn out wrong | agent 太激进 (overconfident) |
| Self-consistency | 同 query 跑 3 次答案一致 | composite signal 2 |
| OOD distance | embed query 找最近已 known query, 1-similarity | composite signal 5 |
| Tool grounding | response 引用 RAG retrieved doc | hallucination 防线 |
| Tiered threshold | > 0.85 auto / 0.5-0.85 offer / < 0.5 preempt | 不 binary |

### 5 个核心 framework / pattern

**Framework 1**: 4 pattern coexist (顺序 D > B > A > C)
- When: 每个 user message 进 handler
- Algorithm: 1) D 先检测 /human 明确意图 → escalate / 2) B 检测 destructive action → 起草 + confirm UI / 3) A composite confidence routing (auto / offer / preempt) / 4) C 5% sample to review queue
- Trade-off: 多 pattern coexist 复杂, 但单 pattern 必失败
- Tools: matches_human_request regex, ui.confirm out-of-band, schedule_review async queue

**Framework 2**: Composite confidence (5+ signal)
- When: agent 决定是否 auto-respond 前
- Algorithm: score = logprob_norm × (0.5 if !self_consistent) × (0.7 if !cited) × (0.5 if !schema) × (0.3-1 if OOD > 0.4) × (0.5-1 if complex) × (0 if refusal)
- Trade-off: 多 signal 慢, 但 raw logprob 不可信
- Tools: self-consistency 3-run / citation grounding / schema validation / vector OOD / regex refusal detect

**Framework 3**: Platt / Isotonic calibration with eval set
- When: 部署前 + 每周 drift check + model/prompt 升级时
- Algorithm: 500-1000 known-answer eval → plot confidence bucket vs accuracy → fit Platt (small data) or Isotonic (large) → re-deploy
- Trade-off: eval 数据贵, 但不校准 = confidence 没意义
- Tools: sklearn IsotonicRegression / LogisticRegression, weekly cron drift check

**Framework 4**: Tiered + per-query-type threshold
- When: routing decision
- Algorithm: > 0.85 auto / 0.5-0.85 respond + offer / < 0.5 preempt; per-type override (medical=1.0 never auto, balance=0.7, refund=0.95+B confirm)
- Trade-off: 三 tier 比 binary 复杂, 但中段 confidence 不浪费 human
- Tools: THRESHOLDS dict per intent, cost-sensitive optimization

**Framework 5**: Smooth handoff (no re-explain)
- When: agent → human takeover
- Algorithm: human dashboard 显 summary + draft + concerns + sentiment + history + 1-click actions; human 第一句必 reference 之前 context ("I see you're asking about refund on order #X...")
- Trade-off: 准备 dashboard 工程量, 但 20-min 变 2-min
- Tools: EscalationContext data structure, sentiment indicator, priority queue

### 关键决策树 (ASCII)

```
User msg → handler entry
   |
   v
matches_human_request? → YES → Pattern D escalate (no gate)
   |
   NO
   v
intent.requires_confirm? → YES → Pattern B (draft + confirm UI)
   |
   NO
   v
composite_confidence(query, response, agent_state)
   |
   ├─> 0.85 → Pattern A auto-respond
   |          └─> 5% sample → Pattern C review queue
   |
   ├─> 0.5-0.85 → Pattern A respond + offer "talk to human?"
   |
   └─> < 0.5 → Pattern A preempt "let me get a human"
```

```
Per-query-type threshold:
medical / legal → 1.0 (never auto)
account password reset → 0.95 + B confirm + 2FA
refund processing → 0.95 + B confirm
account balance → 0.7 (low risk, recoverable)
product info → 0.6 (marketing, low harm)
new / weird → A + D fallback
```

### Part 2 五个深度问题速查

**Problem 1: 4 pattern coexisting**
- 核心解法: 顺序 D > B > A > C 在 same handler, 不是选一个 必须四个 coexist
- Top 3 gotchas: D 别 gate ("let me try again" = bad UX) / B 大额必 type 'confirm' or 2FA / C 5% sample stratified per query type
- Tools: matches_human_request regex incl. 中文 "人工/转人工", confirm UI out-of-band

**Problem 2: Composite confidence calibration**
- 核心解法: 7 signal (logprob + self-consistency 3run + citation + schema + OOD + complexity + refusal); weights 用 eval set 跑
- Top 3 gotchas: raw LLM logprob 通常 overconfident (0.8 报为 60% 实际) / OOD distance 用 embedding nearest neighbor / refusal detected → override score 0
- Tools: sentence-transformers OOD, BPE token logprob, Vertex AI Vector Search vector OOD

**Problem 3: Threshold tuning + tiered response**
- 核心解法: cost-sensitive optimization (auto_correct 0 / auto_wrong 100 / esc_correct 10 / esc_wrong 30 → min cost), 三 tier > binary, per-query-type override
- Top 3 gotchas: 不同 query type 不同 threshold / monthly A/B test (0.85 vs 0.80) / vanity threshold "low p99" 不 reflect true cost
- Tools: per-intent THRESHOLDS dict, cost_matrix grid search

**Problem 4: Smooth handoff no re-explain**
- 核心解法: EscalationContext 包含 (conv summary / agent draft / concerns / sentiment / history / suggested action / quick actions / SLA); human 第一句必 ref context
- Top 3 gotchas: bad handoff "How can I help today?" = trust 崩 / good handoff "I see you're asking about refund on order #X" / bi-directional handback (human resolved → back to agent)
- Tools: priority queue, sentiment indicator, full transcript collapsed default

**Problem 5: Observability — 4 metrics**
- 核心解法: calibration plot (per-type) + override rate (< 10% high-conf, < 30% mid) + false escalation (< 15%) + missed escalation (< 2%); per-query-type breakdown + per-path CSAT
- Top 3 gotchas: aggregate 看不到 per-type drift / weekly review + quarterly recalibration / 不只指标看 CSAT path 分解
- Tools: dashboard 4 quadrant + per-type table, alerts on drift > 10%

### Production gotchas (top 15)

1. Single pattern (only auto or only human)
2. Trust raw LLM logprob (overconfident invisible)
3. Sudden escalation (user 重复 5 分钟 context)
4. No threshold tuning per query type
5. No calibration eval (confidence 数没意义)
6. No takeover option (user trapped)
7. No observability (escalation pattern invisible)
8. Gate the human path ("Let me try again, please")
9. No queue / off-hours handling (silent drop)
10. No false / missed escalation tracking
11. Auto-respond mindless confirm B (1-click 100% within 1s = fatigue)
12. Hallucination at high confidence (citation enforcement)
13. Model version change without recalibrate
14. Per-path CSAT 不看 (auto vs confirm vs human 差异)
15. Bypass rate 不 track (高 bypass = agent quality 信号)

### 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Composite confidence 4-signal | BNPL chatbot | logprob + citation + OOD + refusal 合成 |
| Isotonic calibration | BNPL chatbot | 800 eval, 0.8 conf → 65% 实际 → 校准后 80% |
| False / missed escalation drop | BNPL chatbot | false 18% → 7%, missed 5% → 2% |
| Tool selection accuracy gain | BNPL agent platform | 70% → 92% 加 RAG discovery signal |
| Pattern B confirm-required | Indonesia refund tier 2 | agent draft + ops 1-click 确认 |
| Pattern C scheduled review | Voice agent | weekly 5% sample 人工 review |
| Pattern D user takeover | Voice agent | "speak to human" any time no friction |
| Smooth handoff state transfer | Voice agent escalation | transcript + agent prep + sentiment 全 transfer |
| Per-type calibration drift | Voice agent 7 markets | weekly buckets review per market |

### 面试现场 quotables (top 8)

1. "4 patterns coexist in same product — A confidence threshold + B confirm-required for destructive + C scheduled human review + D user-initiated takeover. Most start A+B+D, add C after."
2. "Raw LLM logprob is unreliable — at 0.8 confidence we saw 65% actual accuracy. Composite from 5+ signals + isotonic regression."
3. "BNPL chatbot: false-escalation 18% → 7%, missed 5% → 2% after composite + isotonic."
4. "Human's first line must reference context: 'I see you're asking about refund on order #X' — never 'How can I help you today?'"
5. "Per-query-type threshold: medical/legal = 1.0 (never auto), balance = 0.7 (low risk), refund = 0.95 + B confirm."
6. "Tiered response not binary: > 0.85 auto, 0.5-0.85 respond + offer human, < 0.5 preempt."
7. "Don't gate the human path — 'Let me try again, please' is the worst UX. Respect user choice, track bypass rate as quality signal."
8. "Weekly dashboard per-query-type calibration plot. Quarterly recalibration with fresh eval set. Drift alert > 10% off diagonal."

### 红线 (top 10 anti-patterns)

1. Single pattern (only auto or only human)
2. Trust raw LLM logprob without calibration
3. Sudden escalation (user re-explains everything)
4. No threshold tuning per query type
5. No calibration eval (eval set < 500)
6. No takeover option (user trapped)
7. Gate the human path (friction = trust崩)
8. Silent drop on off-hours / queue full
9. No false/missed escalation tracking
10. Auto-respond at high conf without citation grounding (hallucination)

### Per-query-type threshold reference

| Query type | Auto threshold | Pattern | Why |
|---|---|---|---|
| Account balance / read-only | 0.7 | A | Low risk, recoverable |
| Order status lookup | 0.7 | A | Read-only |
| Product info / FAQ | 0.6 | A | Marketing, low harm |
| Refund < $X | 0.95 | A+B confirm | High stakes |
| Refund > $X | 1.0 | B+D | Human required |
| Password reset | 0.95 | B+2FA | Identity sensitive |
| Account delete | 1.0 | B+D | Irreversible |
| Personal data lookup | 0.95 | B confirm | Privacy |
| Subscription cancel | 0.85 | B (retention attempt) | Reversal pattern |
| Medical advice | 1.0 (never auto) | D | Liability |
| Legal advice | 1.0 (never auto) | D | Liability |
| Emotional / "I'm angry" | n/a | D | Human relationship |
| New / weird question | n/a | A + D fallback | Unknown territory |

### Composite confidence 7 signal weights (BNPL chatbot 真实)

| Signal | Weight | Implementation |
|---|---|---|
| LLM logprob (norm) | continuous multiplier | from OpenAI / Anthropic logprobs response |
| Self-consistency 3-run | × 0.5 if disagree | 3 parallel runs, canonical_form() compare |
| Tool grounding (citations) | × 0.7 if no citation | retrieved doc cite check |
| Schema validation | × 0.5 if invalid | JSON schema for structured |
| OOD distance | × max(0.3, 1-ood) if > 0.4 | embedding nearest-neighbor in known-good DB |
| Query complexity | × max(0.5, 1/complexity) if > 2.0 | word + clause + entity count |
| Explicit refusal | override → 0 | regex "I don't know" / "consult professional" |

### Calibration drift detection

| Bucket | Expected accuracy | Actual (drift example) | Action |
|---|---|---|---|
| 0.9 | ~ 0.88 | 0.65 | drift > 10% → recalibrate |
| 0.7 | ~ 0.7 | 0.55 | drift > 10% → recalibrate |
| 0.5 | ~ 0.5 | 0.48 | OK |
| 0.3 | ~ 0.3 | 0.32 | OK |

### Per-path CSAT tracking

| Path | CSAT | NPS | 启示 |
|---|---|---|---|
| Pattern A auto | 4.3 / 5 | 30 | 提升 agent 质量 |
| Pattern B confirm | 4.5 / 5 | 40 | 中等 |
| Pattern A + offer | 4.4 / 5 | 35 | 中段 conf OK |
| Pattern D human | 4.7 / 5 | 50 | 最高 (human win) |
| Failed (no resolution) | 1.8 / 5 | -60 | 主拉低, fix |

### Confirm UI design pattern

| Component | Example |
|---|---|
| Title | "Agent suggests: Refund $200 to card ending 4242" |
| Side effects list | ✓ Refund $200 USD ✓ Take 3-5 business days ✓ Send email confirmation |
| Detail toggle | Full args expandable |
| 1-click actions | [Confirm Refund] [Modify amount] [Cancel] |
| High-stakes friction | type 'CONFIRM' / 2FA for > $X |
| Time tracking | start → user confirm time (analytics) |

### Escalation handoff data structure

| Field | Type | Purpose |
|---|---|---|
| conversation_id | str | unique session |
| user_sentiment | float -1 to 1 | human knows tone before opening |
| full_transcript | List[Message] | Collapsed expand on demand |
| summary | str | agent-generated 1-paragraph |
| agent_intent_classification | str | "refund_request" |
| agent_attempted_response | str (unsent) | human sees draft |
| agent_confidence | float | transparent to human |
| agent_concerns | List[str] | flagged concerns |
| agent_actions_taken | List | already executed (e.g., verified order) |
| agent_actions_pending | List | drafts not executed |
| user_account_info | Dict | account context |
| user_history | List | past interactions |
| user_lifetime_value | float | VIP signal |
| user_vip_status | bool | priority queue flag |
| suggested_next_action | str | agent's recommended |
| suggested_response_template | str | starter for human reply |
| sla_target | datetime | response deadline |
| priority | int 1-5 | queue priority |
| queue_assigned | str | which team / agent |

### Phase rollout 4-stage

| Phase | Week | What | Advance |
|---|---|---|---|
| 1 | 1-2 | Pattern D + manual routing only | data collection ("typical query 长啥样") |
| 2 | 3-8 | Pattern A + B | threshold roughly tuned |
| 3 | 8-12 | Calibration + tuning | eval set + Platt/isotonic + per-type threshold |
| 4 | 12+ | Pattern C + observability | 5% sample review + dashboard + iteration |
