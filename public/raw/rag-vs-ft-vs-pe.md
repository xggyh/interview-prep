## 题目（verbatim）

> **[OpenAI Technical Deep Dive - 60 min]**
>
> "Walk me through the **tradeoffs of RAG vs fine-tuning vs prompt engineering**. When does each win?"

**出处**：OpenAI FDE 真题. Google Cloud FDE / Anthropic FDE 都问.

**Round**：Technical Deep Dive (60 min)

---

## 这道题在考什么

考你**production AI decision-making**：

1. **3 个技术 distinct 区分** —— 很多 candidate 混淆
2. **真实 cost / quality / latency tradeoffs**
3. **Combinations** —— 真实 production 是 hybrid
4. **When NOT to use each** —— 同等重要
5. **Knowing limits** —— FT 不能 inject knowledge, PE 限于 context window

---

## 3 个技术 cheat sheet

| Aspect | Prompt Engineering | RAG | Fine-tuning |
|---|---|---|---|
| **改变什么** | Input only | Input (retrieved context) | Model weights |
| **典型 cost** | $ / query | $$ / query (retrieve + LLM) | $$$$ upfront, $ / query |
| **Latency** | Fast | +50-100ms for retrieval | Same as base model |
| **数据需求** | 0 / few-shot | 知识 corpus | 1k-100k examples |
| **更新成本** | Edit prompt | Re-embed delta | Re-train |
| **可解释性** | High | Cite sources | Low (black-box) |
| **Best for** | Reasoning patterns | Factual knowledge | Style / format / structure |
| **Worst for** | Domain knowledge | Reasoning patterns | Frequently-changing facts |

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-3 min | 1 sentence each |
| 3-15 min | When each wins (with examples) |
| 15-30 min | When each loses |
| 30-45 min | Combinations + hybrid systems |
| 45-60 min | Cost analysis at scale |

---

## 我会这样答（sample monologue）

> "Three distinct techniques with different cost/quality/maintainability profiles.
>
> **Prompt Engineering** changes the **input format** — system prompt, examples, structure. Cheapest, fastest, most maintainable. Loses to: factual knowledge the model doesn't have, style requirements that don't fit prompts.
>
> **RAG** retrieves relevant docs at query time. Best for **factual / domain-specific / frequently-updated knowledge**. Loses to: tasks where the model just doesn't reason well even with the info, or where retrieval is slow/expensive.
>
> **Fine-tuning** updates the model weights to bake-in patterns. Best for **style, output format, low-resource languages, or specific reasoning patterns**. Loses to: factual knowledge (can't reliably 'inject' facts), changing data, cost.
>
> **When each wins**:
>
> **PE wins**:
> - **Structured output format** (e.g., JSON schema following)
> - **Light persona / tone** ('you are a helpful assistant')
> - **Few-shot reasoning patterns** (chain-of-thought)
> - **Quick MVP / prototype** before commitment
> - **Frequently changing requirements** — just edit prompt
>
> **RAG wins**:
> - **Company-specific docs** (HR policy, product docs)
> - **Up-to-date info** (today's news, current customer data)
> - **Citing sources** required (legal, medical)
> - **Tenant-specific knowledge** (each customer has own corpus)
> - **Knowledge corpus too large for context window**
>
> **Fine-tuning wins**:
> - **Consistent output format / style** that prompts can't reliably enforce
> - **Low-resource language / domain** model doesn't speak well
> - **Specific reasoning patterns** model needs to learn (e.g., medical diagnostics framework)
> - **Volume cost reduction**: small fine-tuned model can replace expensive prompts on big model
> - **Compliance**: domain-specific behaviors auditable in weights, not configurable
>
> **When each loses**:
>
> **PE loses when**:
> - Knowledge isn't in model + can't fit in context (RAG win)
> - Output style requirements are subtle (FT win)
> - Prompts get > 5000 tokens, paying ineffectively per query
>
> **RAG loses when**:
> - The task is **reasoning**, not knowledge retrieval (just sending retrieved chunks doesn't help)
> - **Latency budget** is tight (< 100ms total — RAG adds 30-100ms)
> - Corpus is **noisy** and retrieval brings irrelevant content
> - **Small static knowledge** that fits in prompt (just put it in prompt)
>
> **FT loses when**:
> - Knowledge changes (re-train cost prohibitive)
> - **Small data** (< 1k examples, will overfit)
> - **Base model quality** matters and you don't have eval discipline
> - Hallucination concerns — FT can amplify, not reduce
>
> **Combinations (real production)**:
>
> 1. **PE + RAG**: most common. Prompt teaches reasoning + format, RAG injects current knowledge.
>    Example: customer support — system prompt teaches escalation rules, RAG retrieves customer history.
>
> 2. **PE + FT**: fine-tune for style + format, prompt for query specifics.
>    Example: code generation — FT on company codebase style, prompt with specific task.
>
> 3. **RAG + FT**: rare but valuable. FT for query-rewriting / retrieval, RAG for knowledge.
>    Example: financial advisor — FT on advisor reasoning patterns, RAG on portfolio data.
>
> 4. **All 3**: enterprise systems. FT for company-specific reasoning, RAG for facts, prompt for query.
>    Example: ChatGPT-for-enterprise wrappers do this.
>
> **Cost analysis at scale**:
>
> At 100k queries/day with GPT-4-class model:
>
> | Technique | Setup cost | Per-query cost | Total / month |
> |---|---|---|---|
> | PE only | $0 | $0.05 | $150k |
> | + RAG | $1k (embed) | $0.06 | $180k |
> | + FT (small data) | $5-50k | $0.05 | $150k + 5-50k amortized |
> | FT + RAG hybrid | $50k+ | $0.04 (smaller model) | $120k + 50k |
>
> Hybrid usually wins at scale because FT lets you use **smaller cheaper model**. But **only after** you've proven the use case with PE+RAG.
>
> **My pragmatic order**:
> 1. **Start with PE only** (week 1) — establish baseline + eval suite
> 2. **Add RAG** (week 2-3) — measure recall@K, eval lift
> 3. **Add FT** (month 2+) — only if PE+RAG plateaus and high volume justifies cost
>
> **Anti-pattern: FT for facts**: "let's fine-tune on our product docs to teach the model" — almost always wrong. FT doesn't reliably encode facts. **Use RAG**."

---

## 简历专属 reframe

你的 **BNPL chatbot (Agentic + RAG)** + **voice agent (SFT + DPO + RL post-training)**:

| 题 | 你做过 |
|---|---|
| RAG for company knowledge | BNPL chatbot FAQ RAG |
| Fine-tuning for style/domain | Voice agent SFT/DPO for multilingual debt collection style |
| RL alignment | Voice agent reward modeling 你 own |
| Combination in production | BNPL + voice agent 都是 hybrid |
| Cost-aware decisions | TikTok scale 你 always think cost |

**主动说**:

> "I've literally shipped all three in production. For BNPL chatbot: prompt engineering for intent routing + RAG for FAQ knowledge — works great, no fine-tuning needed. For voice agent: needed cross-lingual debt-collection tone consistency that prompts couldn't reliably enforce, so we **post-trained (SFT + DPO + RL alignment)** for style. The lesson I'd offer: **start with PE-only, add RAG when knowledge gap visible, fine-tune only when style/format quality plateaus**. Never fine-tune to inject facts — RAG is the right tool."

→ 你简历最 match 的题之一。

---

## 5 follow-ups

**Q1**: "Customer wants their docs 'baked into the model'. Should we fine-tune?"
**A**: **No, almost certainly RAG**:
- FT doesn't reliably encode facts (can hallucinate variations)
- Docs change → need re-FT → expensive
- No citation → compliance issues
- **Sit-and-explain why** to customer with their actual docs: "if your policy changes monthly, RAG handles automatically; FT requires monthly re-train."

**Q2**: "When does fine-tuning make economic sense at 100k queries/day?"
**A**: Math:
- GPT-4 ($0.03/1k input + $0.06/1k output) → ~$0.05/query → $150k/month
- Fine-tuned GPT-4o-mini ($0.0015/1k input + $0.006/1k output) → $0.005/query if quality match → $15k/month
- FT setup $50k one-time → recover in **3.5 months at this volume**
- **Rule of thumb**: > 50k queries/day, FT a smaller model often pays back in < 6 months

**Q3**: "What if RAG isn't returning relevant docs?"
**A**: Multi-pronged:
- **Chunking**: try semantic / paragraph-aware vs fixed
- **Retrieval method**: try hybrid (dense + BM25), reranker
- **Query rewriting**: LLM rewrite user query before retrieve (handles ambiguous)
- **HyDE**: have LLM hypothesize an answer, embed that, retrieve similar docs
- **Don't fine-tune** to fix retrieval — separate problem

**Q4**: "Our fine-tuned model performs worse than base + prompt. Why?"
**A**: Common causes:
- **Overfitting** to small training set (< 1k examples)
- **Catastrophic forgetting** — model loses general capability
- **Bad eval** — measured on training data not held-out
- **Wrong base model** — fine-tuning the wrong base for task
- **Format issues** — training examples inconsistent

Fix: **bigger eval set first, LoRA not full fine-tune, mixture of new + general data**.

**Q5**: "Long-context (Gemini 1.5 Pro / Claude 200k) — does this kill RAG?"
**A**: **Not yet**:
- Long-context wins when corpus < 1M tokens, static, no privacy concerns
- RAG wins when: large + dynamic / multi-tenant / per-user / cost
- **Hybrid**: RAG retrieves top-K, feeds 50-100k into long-context model. Best of both.

---

## ❌ 易错点

1. **Treat as 3 alternatives** when they're complementary
2. **FT to inject facts** — top anti-pattern
3. **PE only** when knowledge gap obvious
4. **Skip eval baseline** before adding techniques
5. **Forget cost analysis** at scale
6. **No mention of combinations**
7. **Confuse RAG with semantic search** — RAG is retrieve + generate, not retrieve alone

---

## ✅ 加分项

1. **3x3 comparison table** sharp
2. **Concrete cost math** ($150k/mo + amortize)
3. **PE → RAG → FT pragmatic order**
4. **Combinations (all 4 patterns)**
5. **Anti-pattern: FT for facts** named
6. **Long-context awareness** (current)
7. **HyDE / query rewriting** beyond basic RAG
8. **Quote BNPL chatbot + voice agent experience**

---

## Cheat Sheet

```
3 techniques cheat sheet:
                PE        RAG       FT
  Changes:      input     input+ctx weights
  Setup cost:   $0        $1k       $5-50k
  Per query:    $$$$      $$$$      $$
  Latency:      fast      +retrieve same
  Updates:      edit      re-embed  re-train
  Best for:     reasoning facts     style
  Worst for:    knowledge reasoning facts

Combinations (production reality):
  PE + RAG (most common — customer support)
  PE + FT (style + query)
  RAG + FT (rare — finance / medical)
  All 3 (enterprise)

Pragmatic order:
  Week 1: PE only + eval suite
  Week 2-3: + RAG, measure lift
  Month 2+: + FT only if quality plateaus + volume justifies

Cost @ 100k queries/day:
  PE only: $150k/month
  + RAG: $180k/month
  FT smaller model: $15k/month after $50k setup
  Payback: 3-6 months at this volume

Anti-patterns:
  - FT for facts (use RAG)
  - PE only when knowledge gap (add RAG)
  - FT on < 1k examples (overfits)
  - FT to fix retrieval problem
```
