## 题目（verbatim）

> **[OpenAI Technical Screen - 60 min, post take-home]**
>
> "**Why did you choose that chunking strategy?** Why not a different retrieval method?"

**出处**：OpenAI FDE 真题（gaijineer.co 候选人 report）. Google FDE 上 Vertex AI RAG, ElevenLabs FDE 都会问.

**Round**：Technical Screen / Take-home Follow-up (60 min)

---

## 这道题在考什么

这是个 **追问式** 问题, follow up on candidate's take-home. 考你:

1. **能不能解释 design choice 的 reasoning** —— 不是"我用了 X", 是 "我考虑了 X / Y / Z, 选 X 因为..."
2. **知不知道 alternative** —— 没考虑过 = 没经验
3. **knowing what you don't know** —— "这是我做的选择, 但 X 场景我会重选"
4. **Honest tradeoffs** —— 不假装 perfection

---

## 5 个 chunking strategies (必知)

| 策略 | What | When |
|---|---|---|
| **1. Fixed-size token** | 每 512 token 一切 | Default baseline, fast |
| **2. Recursive sentence/paragraph** | 按 hierarchy split (paragraph > sentence > word) until <= limit | Better for prose |
| **3. Semantic chunking** | Embed neighboring sentences, group by similarity | Better topic coherence, slower |
| **4. Document-structure aware** | Markdown / PDF / HTML respects headers, tables, lists | Best for structured docs |
| **5. Late chunking** | Embed full doc first, then chunk on the embeddings | Preserves long-range context |

每个 trade off: **speed × coherence × granularity**.

---

## 5 个 retrieval methods (必知)

| 方法 | What | When |
|---|---|---|
| **1. Dense (semantic)** | Vector embedding + ANN search | Default semantic match |
| **2. Sparse (BM25 / keyword)** | TF-IDF style word match | Acronyms, exact terms, IDs |
| **3. Hybrid** | Dense + sparse weighted | Production best practice |
| **4. ColBERT / Late interaction** | Per-token embeddings, expensive | Very high precision |
| **5. Reranking** | Initial retrieve 100 candidates, cross-encoder rerank top 10 | Production quality boost |

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-2 min | Anchor: what you chose, **summarize in 1 sentence** |
| 2-7 min | Why you chose it (tradeoffs you considered) |
| 7-12 min | Alternatives you considered + why rejected |
| 12-20 min | When you'd change choice (scale / data shape / latency) |
| 20-60 min | Deeper followups |

---

## 我会这样答（sample, assuming take-home used semantic chunking + hybrid retrieval）

> "For the take-home, I chose **semantic chunking (300-500 tokens, paragraph-aware) + hybrid retrieval (dense + BM25 with α=0.7 dense weight) + cross-encoder rerank top-10**.
>
> **Why semantic chunking**:
> - Take-home docs were **technical articles** — concept-coherent paragraphs matter. Fixed-size token chunking splits mid-sentence which hurts recall on multi-sentence concepts.
> - I started with fixed-512 baseline, saw retrieval missing answers that spanned sentence boundaries.
> - Semantic chunking with **30% overlap** (so concepts spanning boundary are in both chunks) fixed it.
> - **Tradeoff I accepted**: chunk count increased 1.4x (vs fixed), embedding cost up 1.4x, retrieval slightly slower. Acceptable for the quality lift.
>
> **Why hybrid retrieval (not pure dense)**:
> - Take-home docs contained **product codes / API names / specific identifiers** (e.g., "GPT-4-turbo", "0.7-temperature").
> - Pure semantic embedding doesn't index those well — "GPT-4" and "GPT-3" embed close, but for the user's question they're meaningfully different.
> - BM25 catches exact term match. Hybrid gets both.
> - α=0.7 dense was empirical: I tried 0.5/0.6/0.7/0.8 on eval set, 0.7 best.
>
> **Why cross-encoder rerank**:
> - Bi-encoder retrieval is fast but coarse — top-10 from bi-encoder might have 30% miss rate
> - Cross-encoder (e.g., `cross-encoder/ms-marco-MiniLM-L-12-v2`) is slow but precise
> - **Compromise**: retrieve top-100 with bi-encoder (cheap), rerank top-10 with cross-encoder (3x latency cost, 20pp recall@10 improvement)
>
> **What I considered and rejected**:
> - **Late chunking (Jina v3 style)**: better long-range context but **slow embedding** + new infra. Not worth for 100-doc take-home.
> - **ColBERT**: maximum precision but **5x storage** — overkill for this scale.
> - **Document-structure-aware chunking**: docs were not strictly structured (no clear markdown hierarchy), so paragraph-aware was the right level.
>
> **When I'd change choice**:
> - **Dataset > 1M docs**: pre-rerank latency adds up, would consider distilled cross-encoder or skip rerank for top-50
> - **Multi-modal (image + text)**: need different chunker entirely (image embedding model)
> - **Tabular / structured data**: chunking is wrong abstraction, use direct cell retrieval (text-to-SQL or RowEmbedding)
> - **Long-context model (Gemini 1.5 Pro 1M)**: maybe skip retrieval altogether, put whole doc in context — chunking becomes anti-pattern
>
> **Honest gap**: I didn't try **HyDE (Hypothetical Document Embedding)** which Anthropic + others recommend for short queries. Would test that next iteration."

⏱️ ~6 min spoken.

---

## 简历专属 reframe

你的 **BNPL chatbot RAG** + **ConvFinQA reference impl**：

| 题 | 你做过 |
|---|---|
| Chunking choice | BNPL FAQ RAG — 你必经过 chunking debugging |
| Hybrid retrieval | BNPL 含 product/order ID, hybrid 是 production reality |
| Rerank vs no rerank | ConvFinQA `match_numeric` 思路类似 |
| Eval-driven choice | ConvFinQA 9-variant ablation 你做过 evidence-driven |

**主动说**：

> "For our BNPL chatbot at TikTok, I went through this exact decision path. Started with fixed-512 chunking + pure semantic. Quickly realized customer queries contained **product codes and merchant names** — semantic alone was missing 20% of high-intent queries. Added BM25 weighted at 0.3 → recall@5 jumped from 72% to 86%. Then for the 'why was my refund delayed' kind of query that requires multi-paragraph context, we did **30% chunk overlap + cross-encoder rerank**. Each addition we measured before keeping. **Eval first, optimization second**."

---

## 5 follow-ups

**Q1**: "Why not just use a vector DB's default settings?"
**A**: Vector DB defaults are **infrastructure choices, not retrieval-quality choices**. Pinecone's default fixed-size chunker is fine for getting started, but the retrieval-quality difference between default and tuned can be 20pp on recall@10. **In production, defaults cost you accuracy that translates to user complaints**.

**Q2**: "Tell me about a time chunking strategy failed for you."
**A**: BNPL chatbot example — initial fixed-512 chunking split refund-policy mid-paragraph. User asks "what's the refund timeline?", retrieval gets first half ("Refunds processed via...") not second half ("...within 14 days"). Fix: paragraph-aware chunking + 30% overlap.

**Q3**: "Cross-encoder rerank is expensive. How do you make it production-fast?"
**A**:
- **Distillation**: train smaller cross-encoder (50M params) on bigger model's outputs
- **Batching**: rerank top-K in single forward pass
- **Caching**: hot queries' rerank results cached for 1h
- **Skip for high-confidence**: if top-1 bi-encoder score > 0.9, skip rerank

**Q4**: "How would you handle multi-language docs?"
**A**:
- **Multilingual embeddings**: LaBSE / multilingual-e5
- **Cross-lingual retrieval**: query in English, retrieve from Chinese docs via shared embedding space
- **Per-language BM25** if hybrid (tokenization differs)
- Test on actual user query language distribution

**Q5**: "Long-context models (Gemini 1.5 / Claude 200k) — does RAG become obsolete?"
**A**: **Not yet, but the use case narrows**:
- Long-context replaces RAG when: doc set is **small** (< 1M tokens), **static**, **no privacy issues** with sending it
- RAG still wins when: doc set is huge / dynamic / per-user / cost-sensitive (long context is expensive per call)
- **Hybrid**: RAG retrieves the 50-100k most relevant tokens, feed into long-context model

---

## ❌ 易错点

1. **"我用了 X 因为 X 是 standard"** — no reasoning
2. **不知道 alternatives** — limited experience signal
3. **过度 optimization without eval** — guessing
4. **Defensive when challenged** — interview is about thinking, not being right
5. **"我会试 HyDE"** without specific plan — vague
6. **Ignore long-context trend** — out of date
7. **Talk implementation 太久** without articulating principle

---

## ✅ 加分项

1. **List 5 chunking + 5 retrieval methods** systematically
2. **Eval-driven choice** (numbers, not opinions)
3. **"When I'd change"** — situational awareness
4. **Honest gap** — what you didn't try
5. **Long-context model awareness** — current
6. **Quote your TikTok BNPL experience**
7. **30% overlap specific number**
8. **α=0.7 specific dense weight from eval**

---

## Cheat Sheet

```
5 chunking strategies:
  1. Fixed-size token (default, fast)
  2. Recursive sentence/paragraph (prose)
  3. Semantic (similarity-based, slower)
  4. Document-structure aware (markdown/PDF)
  5. Late chunking (preserves long-range)

5 retrieval methods:
  1. Dense (semantic embed + ANN)
  2. Sparse (BM25 / TF-IDF)
  3. Hybrid (dense + sparse weighted)
  4. ColBERT / late interaction (precision, expensive)
  5. Rerank (cross-encoder top-10)

Production standard:
  Semantic chunking 300-500 tokens, 30% overlap
  + Hybrid retrieval (α=0.7 dense)
  + Cross-encoder rerank top-10 of top-100

When to change:
  > 1M docs → drop rerank or distill
  Multi-modal → different chunker
  Tabular → row retrieval not chunking
  Long-context 1M → maybe skip RAG

Key principle:
  Eval first, optimize second
  α weight is empirical not theoretical
  Default settings cost 20pp recall
```
