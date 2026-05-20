## 题目（verbatim）

> "Explain to a **non-technical CFO** why the model produces **different outputs for the same input** (non-determinism is **not a bug**). Without losing trust."

**出处**：fde.academy 客户模拟. OpenAI / Google FDE / AI deploy companies 都问.

**Round**：Client Simulation (30-45 min)

---

## 这道题在考什么

考你**技术 → business 翻译**能力。LLM stochastic output 对工程师 obvious, 对 CFO 是 "I'm paying $1M for randomness?":

1. **类比能力** —— CFO 不需要懂 temperature, 但需要 mental model
2. **Trust framing** —— "不一致" 听起来像 "不可靠"
3. **Audit & guardrails** —— CFO 关心 compliance / financial impact
4. **When CFO is right** —— if their use case actually needs determinism, **don't argue, change architecture**

---

## 黄金 framework：A·B·C·D

| Step | What | Sample |
|---|---|---|
| **A** | **Acknowledge concern** | "I understand why this looks like a defect" |
| **B** | **Business-language analogy** | Use CFO's domain (financial, accounting) |
| **C** | **Concrete bounds** | What is and isn't varying — show metrics |
| **D** | **Deterministic option** | "If your use case needs strict determinism, here's the path" |

---

## 3 个 successful analogies for CFO

**Analogy #1: Financial advisor**

> "Imagine you ask the same financial advisor the same question twice. Each time, you'd expect the **same recommendation**, but slightly different wording, different supporting arguments. They might emphasize different angles based on what they're thinking that day. **The conclusion is consistent, the wording varies**. Our model behaves similarly — the **bottom-line decision is stable**, but the prose varies. This is by design, because it actually produces **better answers** than a robot reading from a script."

**Analogy #2: Auditing**

> "When two auditors look at the same financials, you wouldn't expect identical reports word-for-word. You'd expect them to **flag the same issues**. Our model is the same — for compliance-critical fields, the **flagged issues are 99% consistent**. The framing varies. We track the consistency rate as a metric — 99% means the model is healthy."

**Analogy #3: Stock analyst**

> "If you ask 5 analysts the same question on different days, they don't write **identical** reports — but they reach **similar conclusions**. Our model has the same kind of natural variation. **The decision is what matters, not the wording**."

---

## Sample script (full role-play)

> *[CFO: "I ran the same query 3 times and got 3 different answers. How am I supposed to trust this for our annual report?"]*
>
> "I completely understand why this looks broken. Let me walk you through what's actually happening, then propose how we make this safe for the annual-report use case.
>
> **What's happening**: our model isn't a database lookup — it's more like a **financial analyst on your team**. Imagine you asked 3 different analysts the same question. They'd reach **similar conclusions** but with different wording, different supporting arguments, different angles emphasized. That's because they're **reasoning** about your data, not just retrieving it. The model does the same — it's how it produces nuanced answers, not just lookup-table responses.
>
> **What's actually different vs the same**: I can show you metrics. For the kind of question you ran:
> - **Numerical answer**: same in 99.2% of repeats (we measure this)
> - **Key findings flagged**: same in 97% of repeats
> - **Wording / supporting prose**: varies — and we want it to, because identical wording would feel robotic
>
> **For the annual report specifically**, you're right that you need **strict reproducibility** — auditors need to verify the same input gave the same output. For that use case, we offer **2 options**:
>
> **Option 1: Pin random seed** — for any query you mark 'production-final', we use a fixed random seed. Same input → exact same output, every time. Tradeoff: slightly more rigid wording.
>
> **Option 2: Cached result** — your annual report query runs once, result is stored with a verification hash. All future re-reads return the cached version with full audit trail.
>
> **My recommendation**: Option 2 for the annual report — that's how financial systems handle this. The model **generates the analysis once**, and from that point on it's a **stored artifact**, like a signed document. You can re-open it any time, byte-for-byte identical.
>
> Would that address what you're concerned about? Anything else feels off?"

⏱️ 5-6 min spoken. 

---

## 简历专属 reframe

你的 **voice agent for debt collection** 必涉及这种 conversation：

| 题 | 你的经验 |
|---|---|
| Non-tech stakeholder explanation | 7 markets ops teams 多数非技术 |
| Compliance/audit framing | Debt collection is regulated, 你必懂 |
| Determinism path for compliance | Voice agent 有 fixed-decision paths for regulated actions |
| Numerical consistency metric | 你的 ConvFinQA eval — consistency is measurable |

**主动说**:

> "I had this exact conversation with the Indonesia regulatory body when we deployed the voice agent. They worried about model 'inconsistency' — would two customers asking the same question get different financial answers? My move was: (1) show them the **99% consistency on numerical decisions**, (2) for regulated dialog paths, we **pinned the response template** (deterministic), (3) for natural-conversation paths, we accept variation but log every decision for audit. **They signed off because we gave them both — flexibility where it's value-add, determinism where compliance requires it**."

---

## 5 follow-ups

**Q1**: "Auditor demands all outputs be reproducible. Full determinism."
**A**: 答应 + 解释 tradeoff:
- "Doable. We can pin seed + temperature=0 for audit-flagged queries. **Tradeoff**: outputs become slightly more rigid, may feel less helpful. For audit specifically that's the right call."
- "What I'd suggest: **2-mode system**. Default mode for productivity (some variation). Audit mode for compliance-flagged queries (full reproducibility, with hash log)."

**Q2**: "Show me the numbers — what's the actual numerical consistency rate?"
**A**: 不 ballpark:
- "Let me pull the data. Last 1000 production queries, run each 3x. **For numerical outputs: 99.1% identical, 0.7% within ±1% of mean, 0.2% > 1% deviation**."
- If you don't have data: "I'll have this measured + reported by Wednesday."
- **Never fake numbers**.

**Q3**: "What if I get audited and the auditor sees different outputs?"
**A**: 3-tier defense:
- **Audit log**: every query timestamped + input + output + model version + seed + temp
- **Reproducibility on demand**: with the audit log, we can re-execute identical inputs → identical outputs (using same model+seed+temp)
- **Read-only artifacts**: production-final outputs (like annual report figures) hash-stored, immutable
- "Show your auditor the artifact, not a re-run."

**Q4**: "Why not just always use determinism then?"
**A**:
- "For creative / analytical tasks, slight variation produces **better answers** — the model explores more solution space."
- "For procedural / lookup / compliance tasks, determinism is right."
- "We give you per-query control: deterministic for finance, default for general."

**Q5**: "Our CTO says LLM is too unpredictable for finance. Should we cancel?"
**A**: 不 fight 全否认:
- "Your CTO is right to be cautious. LLMs in finance is **about deployment patterns, not model choice**. We can build the deterministic + audit-friendly version they want. Can we get them in a 30-min call so I can show specifically the architecture?"
- This shifts conversation from "should we use this" to "how do we use this safely".

---

## ❌ 易错点

1. **用 'temperature' 'top-p' 'stochastic'** — CFO 听不懂 → 失信
2. **Argue 'it's not a bug'** — defensive, loses
3. **没 concrete consistency 数字** — feels handwavy
4. **没提 determinism option** — CFO 没出路
5. **Patronize** — "you don't need to understand" — explosive
6. **没 audit log story** — compliance ask 主要
7. **Promise 0 variability without changing architecture**

---

## ✅ 加分项

1. **Financial advisor / auditor / stock analyst** analogies
2. **Concrete consistency metrics** (99.1% etc)
3. **2-mode system**: default + audit/deterministic
4. **Hash-stored artifacts** for immutable
5. **Per-query control** — flexibility
6. **Quote Indonesia regulatory experience**
7. **Joint call with CTO** to address tech objections
8. **Audit log + replay** capability

---

## Cheat Sheet

```
A·B·C·D:
  Acknowledge concern
  Business-language analogy (FA / auditor / stock analyst)
  Concrete bounds (99% consistency on decision)
  Deterministic option (pin seed / cache result)

Useful analogies:
  - "Same advisor, slightly different wording, same conclusion"
  - "Auditors flag same issues, write different reports"  
  - "Stock analysts reach similar conclusions"

Concrete metrics to quote:
  - 99.1% identical numerical outputs
  - 97% identical flagged findings
  - <0.5% > 1% deviation

2-mode system:
  Default: temp=0.3, slight variation, more nuanced
  Compliance: temp=0, pinned seed, exact reproducible

For audit:
  - Every query logged: input + output + model + seed + temp
  - Production-final results hash-stored as immutable
  - Replay on demand
  - "Show artifact, not re-run"

Words to avoid:
  - temperature, top-p, stochastic, sampling
  - "by design"
  - "trust me"

Words to use:
  - reasoning vs lookup
  - consistency rate
  - audit log
  - artifact / signed document
  - replay
```
