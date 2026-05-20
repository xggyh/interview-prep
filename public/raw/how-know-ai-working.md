## 题目（verbatim）

> **[OpenAI Technical Deep Dive]**
>
> "How do you **know your AI system is actually working well** in production? Cover evaluation: automated metrics, human feedback, online vs offline."

**出处**：OpenAI FDE 真题. 几乎所有 FDE 都问 (Google / Anthropic / Salesforce).

**Round**：Technical Deep Dive (60 min)

---

## 这道题在考什么

考你**production AI eval discipline**:

1. **Offline vs Online vs Production** 三层
2. **Automated metrics 局限** —— 知道 BLEU / ROUGE 不够
3. **Human-in-the-loop** —— 知不知道怎么 scale
4. **Drift detection** —— production over time
5. **LLM-as-judge** —— 知道但 caution

---

## Eval 3 层架构

| Layer | When | Cost | Speed | Signal quality |
|---|---|---|---|---|
| **Offline (golden set)** | Pre-deploy, every CI run | Low | Fast | High but limited coverage |
| **Online (live A/B)** | Post-deploy, controlled rollout | Medium | Days | High, real user signal |
| **Production monitoring** | Always-on | Low | Real-time | Lag indicator only |

**最佳 production 系统三者都有**, 各自 catch 不同 failure.

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Frame: 3-layer eval pyramid |
| 5-20 min | Layer 1: Offline metrics (auto + LLM-judge + human) |
| 20-35 min | Layer 2: Online A/B + canary |
| 35-50 min | Layer 3: Production drift monitoring |
| 50-60 min | Special: human-in-loop scaling, eval cost |

---

## 我会这样答（sample）

> "Production AI eval is **3 layers**, each catches different failures.
>
> **Layer 1: Offline (Golden Set + Automated + LLM-Judge)**
>
> Before deploy, every CI run:
> - **Golden set** of 500-2000 hand-curated query+expected pairs
> - Run model on all, measure metrics
> - Required pass rate (e.g., 80% exact-match or rubric pass) before merge
>
> **Automated metrics** (cheap, narrow):
> - Exact match for structured tasks (math answer, classification)
> - **String similarity** (BLEU, ROUGE) — known weak signal for generation
> - **Embedding similarity** to reference — better than ROUGE
> - **JSON schema compliance** for structured output
> - **Refusal rate** (does model fail when it should refuse?)
>
> **LLM-as-judge** (medium, broader):
> - Stronger model evaluates outputs on rubric
> - Score 1-5 on dimensions: relevance / accuracy / safety / format
> - **3-judge ensemble** if single judge biased
> - **Calibration**: judge accuracy on hand-labeled subset must be > 90%
> - **Cost**: ~$0.05/eval, run on 500-sample golden set = $25/CI run
>
> **Human eval** (expensive, gold):
> - Curated 50-100 examples reviewed by subject experts
> - Run weekly + before major changes
> - **Use case**: catch what LLM-judge misses (subtle quality, domain nuance)
>
> **Layer 2: Online A/B + Canary**
>
> Post-deploy:
> - **Canary**: 1% → 5% → 50% → 100% over 1-2 weeks
> - **A/B test**: half users on new, half on old, measure user outcomes
> - **Auto-rollback** on error budget breach (e.g., error rate > 1% over 1h)
>
> **User outcomes** (best signal):
> - **Direct feedback**: thumbs-up / thumbs-down ratio per response
> - **Implicit signals**: response acceptance / regeneration / abandonment
> - **Downstream**: did user achieve their goal? (e.g., did the bot resolve the support ticket?)
> - **Business**: revenue / engagement / retention impact
>
> **Layer 3: Production Drift Monitoring**
>
> Always-on:
> - **Input distribution drift**: today's queries vs last week. KL divergence alert.
> - **Output drift**: response length / refusal rate / structure mix
> - **Error rate**: per request type, alert on spike
> - **Latency p99**
> - **Per-user / per-tenant metrics** for fairness
>
> **Critical pattern: Online + Production catches what offline misses**:
> - **Distribution shift** — golden set goes stale
> - **Adversarial queries** — users find edge cases offline didn't anticipate
> - **Subtle drift** — model behavior changes after dependency updates
>
> **Special: Human-in-the-loop scaling**:
>
> Pure human eval doesn't scale. Pattern:
> - **Triage**: only escalate samples where LLM-judge confidence is low or disagrees with metrics
> - **Active learning**: model identifies cases it's uncertain on → human reviews → expands golden set
> - **Expert hours budget**: 10-20% of expert team time on eval is sustainable; more burns out
>
> **Specific tools**:
> - **Braintrust** / **Langfuse** / **Phoenix** for eval pipelines
> - **W&B Tables** for offline eval logging
> - **Grafana** for production drift dashboards
> - **PagerDuty** for SLO alerts
>
> **Eval cost** at scale:
> - 1000-query golden set × $0.05 LLM-judge eval = $50 per CI run × 50 runs/week = $2.5k/week
> - Production drift: 100M queries/day × $0.001 monitoring = $100/day
> - Total: ~$15k/year, often **less than 1% of inference cost**, very worth it
>
> **What I'd warn against**:
> - **Eval debt**: launching without offline eval, hoping production catches issues. Disaster.
> - **Goodhart's Law**: optimize for metric → metric gets gamed (e.g., optimize for length → bot gets verbose)
> - **No human in loop**: 100% LLM-judge → blind spots compound
> - **Same model judges itself** — biased
> - **Static golden set** without refresh — gets stale"

---

## 简历专属 reframe

你的 **ConvFinQA stratified-300 eval + 9-variant ablation** + **voice agent multi-market eval**:

| 题 | 你做过 |
|---|---|
| Offline golden set + auto metrics | ConvFinQA stratified eval pipeline (你 own) |
| LLM-as-judge with disagreement | ConvFinQA critic 实验 — 4/358 trigger, you honestly reported |
| A/B test in production | Voice agent 7 markets phased rollout |
| Drift detection | Voice agent per-market metric monitoring |
| Human-in-loop for low-confidence | Refund tier — agent flags uncertain → human |

**主动说**:

> "I've built this exact 3-layer system for two AI projects. For ConvFinQA I built **stratified 300-conv eval + critic variant**, where critic only triggered on percent_change/divide ops — got 4/358 useful flags. The negative result taught me **eval cost vs signal quality trade-off**: aggressive eval triggers cost more but mostly produce noise. **Cheap broad eval + targeted expensive eval beats one-size-fits-all**. For voice agent, we ran **shadow-mode for 4 weeks per market + thumbs feedback + business metric (repayment rate) A/B**. Catching distribution shift on Indonesia after the first week saved 2 weeks of bad metrics."

→ ConvFinQA negative result + voice agent A/B 都是 gold reference。

---

## 5 follow-ups

**Q1**: "LLM-as-judge — how do you know judge is reliable?"
**A**: 3-step validation:
1. **Hand-label 100 examples** by experts (gold standard)
2. **Run judge on same 100**, compute agreement (Cohen's kappa, accuracy)
3. Judge must reach **> 90% agreement** with human to be trusted
4. **Re-validate quarterly** as model / task drift
5. **Avoid same model self-eval** — bias

**Q2**: "Customer asks: how confident are you the model is working today?"
**A**: Build a **live confidence dashboard**:
- Error budget remaining (e.g., 99.5% SLO, 0.3% burned)
- Drift indicators (input distribution Δ vs 7d baseline)
- Recent canary results
- Human-flag rate (production samples flagged by LLM-judge)
- "Latest weekly human eval pass rate: 94%"

Show numbers, not feels. Customers trust numbers + trend graphs.

**Q3**: "We don't have user feedback signal. What do we use?"
**A**:
- **Implicit signals**: regeneration rate (user hit retry), session length, click-through
- **Downstream**: did user complete intended action (purchase, file ticket close)
- **External sensors**: changes in support ticket volume after deploy
- **Hire human eval**: if no implicit signal, contract human eval

**Q4**: "How much should eval cost as % of inference cost?"
**A**:
- Mature: 5-15% of inference. < 5% likely under-investing.
- Early production: 20-50% (need confidence in deploys)
- Critical domains (medical, legal): 50%+ — human review on everything

Cost is justified by avoided incidents (1 silent quality regression in production = lost contract).

**Q5**: "Eval suite passes but customers complain. Why?"
**A**: Eval suite doesn't reflect production. Causes:
- **Golden set unrepresentative** (e.g., synthetic queries vs real customer language)
- **Wrong metric**: ROUGE high but users hate verbose output
- **No diversity** in golden set (overfit to certain query type)
- **Drift**: production distribution shifted, eval set stale

Fix: **production sampling**, hand-label random samples weekly, add to eval set. **Always have human review channel**.

---

## ❌ 易错点

1. **Offline only** (no production monitoring)
2. **Metrics without human** — LLM-judge or implicit signal at minimum
3. **BLEU / ROUGE for generation** — known weak
4. **Single judge, same model family** — biased
5. **Static golden set** — stale fast
6. **No drift detection** — production silently drifts
7. **No alerts / SLOs** — discover regression from customer complaint

---

## ✅ 加分项

1. **3-layer eval pyramid** explicit
2. **LLM-judge calibration via human-labeled subset**
3. **Production sampling → golden set refresh**
4. **Goodhart's Law awareness**
5. **Specific tools** (Braintrust, Langfuse, Phoenix)
6. **Cost as % of inference** (5-15% mature)
7. **Quote ConvFinQA + voice agent experience**
8. **Confidence dashboard** for customer-facing

---

## Cheat Sheet

```
3-layer eval pyramid:
  Offline (CI / pre-deploy): golden set + auto + LLM-judge + human
  Online (canary + A/B): user signals + outcomes
  Production (always-on): drift + error rate + per-tenant

Offline metrics:
  - Exact-match (structured)
  - Embedding similarity (vs ROUGE)
  - JSON schema compliance
  - Refusal rate
  - LLM-judge with rubric
  - 3-judge ensemble
  - Human expert weekly

LLM-judge requirements:
  - Different model than under test
  - > 90% agreement with human labels
  - Quarterly recalibration
  - Rubric not opinion

Online:
  - Canary 1% → 5% → 50% → 100%
  - A/B with user outcomes
  - Auto-rollback on SLO breach

Production:
  - Input distribution drift (KL divergence)
  - Output length / refusal rate
  - Per-tenant error rate
  - Latency p99
  - User feedback (thumbs / implicit)

Anti-patterns:
  - BLEU / ROUGE only for generation
  - Same model self-eval
  - Static golden set
  - No drift detection
  - No alerts / SLOs

Cost target: 5-15% of inference cost
```
