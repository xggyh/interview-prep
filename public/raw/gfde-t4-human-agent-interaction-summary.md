# 🎯 T4.3 · Human-Agent Interaction 设计 — 冲刺版

> 完整版: [gfde-t4-human-agent-interaction.html](gfde-t4-human-agent-interaction.html). 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: chat support 24/7, 混合 query (FAQ + account change + sensitive refund), 10K query/day peak, mainstream consumer, human agent fallback 可用, GCP + Vertex AI + Gemini 3 Pro 限定."

**核心 framing**: 不是 "agent 100% auto" 也不是 "全人". 必须 **4 pattern 共存** + **calibrated composite confidence** + **smooth handoff**. 90% chatbot 失败不是 LLM 不行, 是没设计 4 pattern coexist + 没校准 confidence + handoff 不顺.

### Layer 1: 4 Interaction Patterns (Coexist, 不是选一个)

| Pattern | When | Agent | Human |
|---|---|---|---|
| **A. Confidence threshold** | High conf | Auto-respond | Reviews escalations |
| **B. Confirm-required** | Destructive action | Draft only | 1-click approve |
| **C. Scheduled review** | All auto actions | Auto-act | Post-hoc 5% sample audit |
| **D. User-initiated takeover** | User says /human | Hands off | Take over (no friction) |

**Handler order**: (1) Pattern D first (explicit user takeover) → (2) Pattern B (destructive gate, intent classify + confirm UI) → (3) Pattern A (confidence routing, > 0.85 auto, 0.5-0.85 offer, < 0.5 preempt) → (4) Pattern C (5% sample to review queue when auto-respond).

### Layer 2: Composite Confidence (5+ signals)

**Raw LLM log-prob 不可信** — typically overconfident (说 0.9 实际 60%). 综合 7 signals:

1. **LLM log-prob** (continuous, weak but free)
2. **Self-consistency** (3 runs agree → high; differ → penalty *0.5)
3. **Tool grounding** (citations present → RAG-grounded, low hallucination)
4. **Schema validation** (structured output passes → high)
5. **OOD detection** (vector distance to known-success queries; > 0.4 → penalty)
6. **Sentiment / complexity** (long + multi-part + multi-entity → harder, low conf)
7. **Explicit refusal detected** ("I don't know" / "I'm not sure" → override to 0)

**Calibration**: 500-1000 known-answer eval set → plot confidence bucket vs accuracy → Platt scaling (small data) or Isotonic regression (500+). Weekly drift detect (any bucket > 10% off diagonal → recalibrate).

### Layer 3: Tiered Threshold (per-query-type)

```
> 0.85       → Pattern A auto (just respond)
0.5 - 0.85   → Pattern A + offer ("Talk to human?")
< 0.5        → Preempt ("Let me get a human for this")
```

**Per-query-type override**:
```
balance / read-only  → 0.7 (low risk, easier auto)
product info         → 0.6 (marketing, low harm)
refund / sensitive   → 0.95 + B confirm
password reset       → 0.95 + B confirm + 2FA
medical / legal      → 1.0 (NEVER auto)
```

**Cost-sensitive optimization**: 选 threshold τ 使 `auto_correct(0) + auto_wrong(100) + esc_correct(10) + esc_wrong(30)` total cost 最小.

### Layer 4: Smooth Handoff (no re-explain)

**Bad**: "How can I help you today?" (用户重新解释 5 分钟)
**Good**: "Hi! I see you're asking about refund on order #ABC-12 for damaged product. I have your photos and details — let me resolve this in a moment."

**EscalationContext (handoff data)**:
- Conversation summary (agent-gen 1-paragraph)
- Agent's draft response (unsent)
- Agent confidence + concerns
- Customer history + sentiment
- Suggested next action
- Quick actions 1-click
- SLA + priority

**Human UI**: summary first (30-sec read) / quick actions visible / full transcript collapsed / sentiment indicator / confidence transparent / disagree path.

### Edge cases (5 个最高频)

- **EC1 Calibration drift (model / data shift)**: Continuous eval (Pattern C 5% sample, human-labeled). Weekly recalibrate if any bucket drifts > 10%. Re-train calibrator on recent 30-day. Per-bucket alert. Model version change → mandatory recalibration before deploy.
- **EC2 User bypass ("I want human, you're useless")**: Respect choice immediately (Pattern D). 不要 gate ("Let me try again"). Track bypass rate (agent quality signal). 不 "fight" — "OK, connecting you" beats "let me try again".
- **EC3 Queue full / off-hours**: Queue with ETA ("you're #4, ~5 min"). Async option ("email back?"). Self-serve docs while wait. Callback form for off-hours. Priority lane for VIP / high-sentiment-loss. **Never silently drop**.
- **EC4 Human disagree with agent**: Internal only (don't undermine AI trust to user). Log + train signal. If correction needed, human takes over + fixes (don't blame agent verbally). Postmortem: why didn't agent escalate?
- **EC5 Agent high confidence but wrong (hallucination)**: Hardest case. Defense layers — citation enforcement (factual claim must cite RAG) / fact-check 2nd pass (cheap Gemini Flash) / anomaly detect (semantically different from past) / outcome telemetry (action have expected effect?) / user feedback loop (thumbs up/down) / Pattern C sample review.

### Production hardening (Observability)

**4 critical metrics**:
1. **Calibration plot** (per query type, alert any bucket > 10% off diagonal)
2. **Override rate** (% agent auto-respond marked wrong by reviewer, target < 10% high-conf)
3. **False escalation** (% escalations human resolves trivially < 30 sec, target < 15% — agent too conservative)
4. **Missed escalation** (% auto-responses turn wrong post-hoc, target < 2% — agent too aggressive)

**Per-path CSAT**: Pattern A 4.3 / Pattern B 4.5 / A+offer 4.4 / Pattern D 4.7 / Failed 1.8 → fix Failed first.

**Iteration loop**: Weekly dashboard review → worst-type pull 50 examples → manual review → fix (prompt / RAG / threshold) → deploy → monitor. Quarterly full re-calibration + threshold A/B.

### 🪝 Resume hook

"BNPL chatbot at TikTok PayLater did exactly this. **Composite confidence** combined 4 signals: LLM log-prob + retrieval citations (must have for factual claim) + OOD distance + explicit refusal detection. **Threshold 0.85 auto / 0.5-0.85 offer / < 0.5 preempt**. **Calibration eval** — 800 known-answer queries showed initial agent overconfident (0.8 conf = 65% actual). Applied isotonic regression. After deployment: false-escalation 18% → 7%, missed-escalation 5% → 2%. Tool selection accuracy 70% → 92% by adding RAG-based discovery as another signal. **Iteration loop**: weekly dashboard (calibration plot per query type), quarterly recalibration with fresh eval set."

---

## 🔥 5 Follow-ups

**Q1: Calibration 持续 drift, 怎么维护?**
Continuous eval (5% sample → human-labeled, Pattern C). Weekly review per-bucket accuracy. Recalibrate if any bucket > 10% off. Re-train calibrator on recent 30-day. Triggers: model version change / prompt version change / drift > 10% / quarterly scheduled.

**Q2: User keep saying "you're useless, I want human"?**
Respect immediately (Pattern D). 不要 gate. Don't fight ("Let me try again" = bad UX). Track bypass rate (agent quality signal). Friendly: "I'll connect you with specialist — they'll have context." Post-hoc analyze high-bypass query types → improve.

**Q3: Escalation queue full, no human available?**
Queue with ETA ("#4, ~5 min"). Async option ("email back?"). Self-serve docs while wait. Off-hours callback form. Priority lane VIP. **Never silent drop** — always communicate state.

**Q4: Human disagree with agent's auto-action. Surface to user?**
**No, internal only**. Don't undermine AI trust in front of user. Log + train signal. Human takes over + fixes (don't blame agent verbally). Postmortem: why didn't agent escalate? Calibration drift? Customer messaging: "I've looked into this and want to update the resolution..."

**Q5: Agent high confidence but wrong (hallucination, missed escalation)?**
Hardest case. Defense layers: (a) citation enforcement (factual must cite RAG) (b) fact-check 2nd pass (cheap Gemini Flash 校 KB) (c) anomaly detection (semantically different from similar past queries) (d) outcome telemetry (action had expected effect?) (e) user feedback (thumbs up/down feeds training) (f) Pattern C 5% sample (g) customer complaint route → instant investigation.

---

## ❌ 易错点 (10 条红线)

1. **Single pattern** (只 auto 或只 human) — 体验差或没 value
2. **Trust raw LLM confidence** — overconfident, 错都不知道
3. **Sudden escalation** (user re-explains) — UX 崩
4. **No threshold tuning per query type** — 一刀切, 不灵活
5. **No calibration eval** — confidence number 没意义
6. **No takeover option** — user 被困
7. **No observability** — escalation pattern 看不见
8. **Gate the human path** ("Let me try again, please") — user frustration
9. **No queue / off-hours fallback** — silent drop
10. **No false / missed escalation track** — quality 不可量化

---

## ✅ 加分项 (12 条)

1. 4 patterns coexist explicit (A/B/C/D)
2. Composite confidence with 5+ signals (log-prob + self-consistency + citations + schema + OOD + complexity + refusal)
3. Calibration eval + Platt / Isotonic regression
4. Per-query-type threshold (medical 1.0 / refund 0.95 / balance 0.7)
5. Tiered threshold (auto / offer / preempt)
6. Smooth handoff with full state context (no re-explain)
7. Off-hours / queue-full handling (ETA / async / callback)
8. False & missed escalation observability + per-path CSAT
9. Cost-sensitive threshold optimization (minimize total cost)
10. Bi-directional handoff (agent → human → agent)
11. Citation enforcement + fact-check 2nd pass (hallucination defense)
12. BNPL chatbot calibration story (18% → 7% false escalation, measurable)

---

## 一句话总结

T4.3 = **4 pattern coexist (auto + confirm + sample-review + user-takeover) + calibrated composite confidence (5+ signals) + smooth handoff (no re-explain) + per-type observability + weekly iteration**. 90% chatbot 失败不是 LLM 不行, 是没设计 4 pattern coexist 和 confidence calibration.

---

## 🃏 Cheat Sheet (印 1 页)

```
4 interaction patterns (COEXIST):
  A: Confidence threshold escalation
  B: Confirm-required for destructive
  C: Scheduled human review (5% sample post-hoc)
  D: User-initiated takeover (/handoff, no friction)

Handler order:
  1. Pattern D first (explicit user intent)
  2. Pattern B (destructive action gate)
  3. Pattern A (confidence-based routing)
  4. Pattern C (5% sample to review queue)

Composite confidence signals (5+):
  1. LLM log-prob (continuous)
  2. Self-consistency (3 runs agree)
  3. Tool-grounding (citations present)
  4. Schema validation
  5. OOD detection (vector distance)
  6. Sentiment / complexity (length / multi-part)
  7. Explicit refusal detected (override → 0)

Calibration:
  Eval set 500-1000 known-answer queries
  Plot confidence bucket vs % correct
  Platt (small data) or Isotonic (500+)
  Recalibrate weekly / on drift > 10%

Threshold tiers (default):
  > 0.85       auto-respond (Pattern A)
  0.5-0.85     respond + offer human
  < 0.5        preempt escalate

Per-query-type override:
  medical / legal      1.0 (never auto)
  refund / password    0.95 + B + 2FA
  product info         0.6
  balance / read-only  0.7

Cost-sensitive optimization:
  min(auto_correct=0, auto_wrong=100, esc_correct=10, esc_wrong=30)
  pick τ minimizing total cost

Escalation handoff data:
  Conversation summary (agent-gen)
  Agent draft (unsent) + confidence + concerns
  Customer history + sentiment + LTV
  Suggested next action + 1-click quick actions
  SLA + priority

Smooth handoff UX:
  Agent: "Connecting you with specialist who has context."
  Human: "Hi! I see you're asking about [SPECIFIC] — let me resolve."
  NEVER: "How can I help you today?" (proves transfer fake)

Off-hours / queue full:
  Queue with ETA / Async option (email back) /
  Self-serve docs / Callback form / VIP priority lane
  Never silent drop

Observability 4 metrics:
  Calibration plot (per query type)
  Override rate (target < 10% high-conf)
  False escalation (< 15%, agent too conservative)
  Missed escalation (< 2%, agent too aggressive)
  Per-path CSAT (A/B/C/D + Failed)

User takeover (Pattern D):
  Don't gate (immediate transfer)
  Respect choice / Track bypass rate
  Don't fight ("Let me try again" = bad)

Hallucination defense (high-conf wrong):
  Citation enforcement (RAG-grounded)
  Fact-check 2nd pass (cheap LLM)
  Anomaly + outcome telemetry
  User feedback + Pattern C sample

Anti-patterns (红线):
  - Single pattern / Raw confidence / Sudden escalation
  - No threshold tuning / No calibration / No takeover
  - No observability / Gate human path / Silent drop

Resume hooks:
  - BNPL chatbot 4-signal + isotonic + 18%→7% false esc
  - Indonesia refund tier 2 confirm-required
  - Voice agent 7 markets escalation + transcript transfer
  - Per-type calibration drift detection
```
