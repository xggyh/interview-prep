## 题目（verbatim）

> "After deployment, the **model performs worse than the previous manual process** the customer was using. How do you investigate and what do you do?"

**出处**：fde.academy 列出的"AI deployment 失败诊断"经典题。OpenAI / Google FDE 都常问。

**Round**：Case Study / Deployment Scenario (45 min)

---

## 这道题在考什么

考你**面对 AI deployment 失败时的工程冷静**。AI deployment 失败比成功多。考点：

1. **Don't panic, don't blame** —— 立刻 reach for "model is bad" 或 "customer integrated wrong" 都是 ego
2. **First measure, then hypothesize** —— 你拿什么数据来比较 model vs manual?
3. **5 个 hypothesis class** —— 你能拆出来吗
4. **De-risk vs Roll back** —— 知道 partial 退回 / kill switch
5. **Don't avoid 'maybe model is wrong for this task'** —— 这是有可能的, 你愿不愿意诚实说

---

## 5 个 clarifying questions

**1. Define "worse"**

> "What metric is worse — accuracy? Speed? User satisfaction? **Worse for the customer's KPI or for some technical metric we set**?"

**2. Worse by how much**

> "5% worse or 50% worse? In a controlled comparison or anecdotal?"

**3. Population overlap**

> "Is the model handling the **same cases** the manual process did? Or is it triggering on different inputs?"

**4. Time since deployment**

> "How long has it been live? 1 week (still ramping) vs 3 months (stable comparison)?"

**5. Customer's actual complaint**

> "What did the customer **specifically say**? 'Numbers are bad' vs 'one user yelled at me' is very different signal."

---

## 5 个 hypothesis classes (诊断框架)

| Hypothesis | What's wrong | Investigation |
|---|---|---|
| **H1: Apple-to-orange comparison** | Model handles harder cases than human did | Compare on same input distribution |
| **H2: Distribution shift** | Live data ≠ training data | Compare train / test / live distributions |
| **H3: Edge case dominance** | Manual = expert with 20 years intuition handling rare cases. Model trained on bulk cases. | Stratify by case rarity, see where model fails |
| **H4: System integration failure** | Model is fine, but upstream feature is broken / latent in prod | Trace feature pipeline end-to-end |
| **H5: 真的 model 不行** | Task may need different ML approach | Compare ML SOTA vs human, look at error analysis |

每个 hypothesis 对应不同 fix。**Don't fix before diagnosing**.

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-10 min | Clarify metric + magnitude + time |
| 10-25 min | 5 hypothesis classes, propose diagnosis order |
| 25-40 min | Pick most likely hypothesis (usually H1 or H3), deep dive investigation |
| 40-50 min | Remediation by hypothesis + safeguard |
| 50-60 min | Communicate to customer + organizational implication |

---

## 我会这样答（sample monologue）

> "First, I need to scope what 'worse' actually means — *[clarifying questions]*. Assume **accuracy worse by 8% on customer's primary KPI, 3 months post-deploy, customer says 'numbers are bad'**.
>
> Before assigning blame, I want to **5-way hypothesize**:
>
> **H1: Apple-to-orange comparison** — manual process was handling 70% of easy cases + escalating hard ones. Model now handles 100%. Of course aggregate looks worse.
>   - **Investigate**: rerun manual process **on the model's hard cases only** (or use historical data). If manual loses to model on hard cases, story changes.
>
> **H2: Distribution shift** — training data was 2 years old, customer's business changed.
>   - **Investigate**: compute KL divergence between training and live features. Check for new categories / values that weren't in training.
>
> **H3: Edge case dominance** — manual = 20-year expert handling 5% rare-but-critical cases perfectly. Model trained on 95% bulk cases, fails on the rare 5%.
>   - **Investigate**: stratify error rate by case rarity. If model is fine on common, terrible on rare, this is it.
>
> **H4: Integration / feature pipeline failure** — model is OK in offline eval, but in prod a feature is missing or stale.
>   - **Investigate**: trace 10 live errors end-to-end. Check feature values vs training distribution. Look for nulls / defaults / encoding bugs.
>
> **H5: 真的 model 不行 for this task** — maybe task is fundamentally hard, manual was a low bar, and our ML choice was wrong.
>   - **Investigate**: error analysis on 100 errors. If errors are correlated and structurally hard, consider that ML may not be the right tool.
>
> **My priority order** (typical):
> 1. Start with **H1 + H3** (5 days) — fastest to investigate, usually reveals truth
> 2. Then **H4** (2 days) — easy to check via tracing
> 3. **H2** (3 days) — distributional analysis
> 4. **H5** last — only after others ruled out
>
> **Most likely outcome**: **H1 + H3 combo**. Manual was selective + expert-on-rare. Model is comprehensive + average-on-rare.
>
> **Remediation if H1 + H3**:
> - **Triage routing**: model handles common cases (90% volume, accuracy > manual). Hard cases auto-route to human reviewer (5%) or expert (5%).
> - **Specialist sub-model**: train second model fine-tuned on rare-but-critical cases.
> - **Confidence threshold**: model only auto-decides when confidence > X, else escalate.
> - **Net business outcome**: 90% throughput improvement at 0% accuracy regression on the critical 10%. Customer wins.
>
> **Safeguards while diagnosing**:
> - **Roll back to manual** for highest-stakes case category immediately while we investigate (1 day to set up)
> - Keep model running on low-stakes for telemetry
> - Daily standup with customer for first 2 weeks
>
> **Communicating to customer**:
> - **Day 1: We acknowledge** the issue, we have a diagnosis plan, here's the timeline (2 weeks for full diagnosis).
> - **Day 7: Interim findings** with most likely hypothesis.
> - **Day 14: Diagnosis + concrete remediation plan**.
> - Never say 'it's working as designed' before diagnosing.
>
> **Two risks to surface**:
> - **If it's H5** (model genuinely wrong for task), the right answer is **graceful retreat** — partial scope, manual still owns most cases, model assists. Don't double down trying to make ML fit.
> - **If customer wants instant rollback**, push back: "We can roll back stake-1 today, but full rollback wastes our 6 months of integration. Let me show you 2-week diagnosis path." Buy time."

---

## 简历专属 reframe

你的 **voice agent deployment** + **ConvFinQA ablation** 直接 reframe：

| 题里的情况 | 你做过 |
|---|---|
| Model worse than manual diagnosis | ConvFinQA 你做过 9 variant ablation — 都比 control 差！这就是这道题的精确等价 |
| Apple-to-orange comparison | ConvFinQA "conditional acc on non-None preds" — 你已经做过这种 trick |
| Edge case dominance | Voice agent ASR 在某些方言上 degrade — 你处理过 |
| H4: feature pipeline failure | Voice agent 上线后 latency 漂移 / context window 漏 features 你 debug 过 |
| Roll back to manual safety | Voice agent fallback to human agent 你设计过 |
| Triage routing (model + human) | Indonesia refund tier 经典 case |

**主动说**：

> "Funnily this is exactly what happened with my ConvFinQA ablation experiment. I tried 9 variants of common agent patterns — typed lookup, critic, plan tags, all combinations — and **none beat the simple baseline**. I documented it as a negative result. The lesson I took: **before assigning model performance loss to 'model is bad', exhaustively rule out apples-to-orange and integration issues**. In the customer case, I'd run the same 5-hypothesis decomposition with shadow data first."

→ ConvFinQA negative result 在这里成神器 — 真实 deployment 失败诊断经验。

---

## 5 个 follow-ups

**Q1**: "Customer demands full rollback today. CFO threatening contract cancellation."
**A**: 谈判, 不投降：
- "We hear you. **Stake-1 / safety-critical category rolls back to manual today** (1 day to set up). Lower-stake stays on model so we can keep telemetry to diagnose."
- "If after 2 weeks we can't show concrete improvement plan, we agree to discuss broader rollback. But pulling all 6 months of work in 24 hours is in your interest to avoid too."
- Get this in writing.

**Q2**: "H5 turns out true. Model genuinely worse. Now what?"
**A**: **Graceful retreat**, not denial:
- "We were wrong about scope. The model **assists not replaces** the manual process. New goal: 50% volume reduction on bulk cases, 100% volume kept on critical."
- Renegotiate contract terms (consulting fees for ongoing optimization, not SaaS for replacement)
- Add specialist human review tier for cases model is bad at
- Track new KPI: total cost per case, not pure accuracy.

**Q3**: "Model is right but customer hates it because output looks different from human's. Cosmetic problem."
**A**: 这是 H4 变种 — UX integration issue, not model issue. 解：
- **Format normalization layer**: make model output **look like** human output (rounding, terminology, structure)
- **Side-by-side display** in UI for first month so customer can build trust
- **Confidence indicators** — show "model 88% sure" so user can intuit when to verify
- 通常 2-4 周 fix。**Don't retrain the model**.

**Q4**: "Manual process operator quit. Now there's no 'better' baseline to fall back to."
**A**: 紧急但好机会：
- **Hire interim contractor for 6 weeks** as fallback while we fix model
- Document operator's decision logic from their case history → **enrich training data**
- 紧急 retrain on operator's specific decisions
- **Don't let "they quit" become "model gets blamed" by default** — establish the model has known issues, set realistic expectations

**Q5**: "Customer wants you to add lots of 'rules' on top of model to fix specific cases."
**A**: 危险路。Rules-on-top spreads infinitely + becomes unmaintainable. Better:
- **Whitelist concrete failure modes**: 5-10 specific case patterns where manual rule overrides model. Document them. Cap at 20.
- **Track override rate**: if > 30% of decisions overridden by rules, the model itself needs retraining, not more rules.
- **Sunset rules**: each rule has expiry, retrain model to absorb the rule's intent.

---

## ❌ 易错点

1. **立刻 blame model** — 没诊断 jumping to "我们 model 有问题"
2. **立刻 blame customer** — "你们 integrate 错了" 出口
3. **没 5 hypothesis 框架** — 没结构化
4. **跳过 H1 apple-to-orange** — 最常见原因
5. **没 immediate safeguard** — diagnose 期间不保护 customer
6. **不敢说 H5** — 永远不承认 model 是错选
7. **直接 retrain** — 没诊断就 retrain, 大概率没解决根因

---

## ✅ 加分项

1. **5-hypothesis decomposition** 完整说出来
2. **Apple-to-orange first** — 最常 root cause
3. **Triage routing (model + human)** 作为 H1/H3 standard fix
4. **Daily standup with customer** 期间
5. **Graceful retreat plan** for H5
6. **Negotiate rollback scope** 不全 yield
7. **Quote ConvFinQA negative result experience**
8. **Sunset rules** — 防 rules-on-top death spiral

---

## Cheat Sheet

```
5 Hypotheses (diagnose 顺序):
  H1 Apple-to-orange (manual on easy cases only)
  H2 Distribution shift  
  H3 Edge case dominance (expert intuition rare)
  H4 Integration / feature pipeline fail
  H5 Model genuinely wrong for task

Priority diagnose:
  H1 + H3 first (5 days)
  H4 fast (2 days)
  H2 medium (3 days)
  H5 last (only if others rule out)

Standard fix if H1 + H3:
  - Triage routing (90% common to model, 10% rare to human)
  - Specialist sub-model on rare cases
  - Confidence threshold escalation

Customer comms cadence:
  Day 1: acknowledge + plan
  Day 7: interim hypothesis
  Day 14: diagnosis + remediation
  Daily standup during diagnosis

Safeguard:
  - Roll back highest-stake category immediately
  - Keep model on low-stake for telemetry
  - Kill switch always live

红线 (don't):
  - Blame customer
  - Blame model without diagnosis
  - Retrain blindly
  - Rules-on-top death spiral
  - Refuse H5 even if true
```
