## 题目

> "Design a **search system** for an enterprise RAG application. Customer documents include technical PDFs, support tickets, contracts. Currently using **pure semantic search (cosine on embeddings)**; recall is 60%. Get it to 90%+."

或追问形态:

> "Why does **hybrid search** (BM25 + dense) often beat pure dense? When does it NOT help? Walk through your retrieval pipeline."

**Round**: RAG / Search System Design (45-60 min)

---

## 这道题在考什么

考你**production retrieval engineering** beyond toy demos:

1. **Dense vs sparse tradeoffs** —— 都不完美
2. **Hybrid fusion** —— RRF / score fusion 怎么 combine
3. **Reranker** —— bi-encoder 召回 + cross-encoder 重排
4. **Query understanding** —— query rewrite / multi-query / HyDE
5. **Eval methodology** —— recall@k, NDCG, MRR

也考 **practical sense** —— 不只是 'pure RAG', 还要考虑 metadata filter, freshness, perms.

---

## 必问 clarifying

**1. 现状 baseline**

> "60% recall — measured at recall@k for what k? On what eval set? Annotated ground truth or proxy?"

**2. Query 类型**

> "Keyword-heavy ('error code X'), semantic ('how do I troubleshoot Y'), mixed? Acronyms / product names?"

**3. 数据 corpus 特征**

> "Documents avg length? Modality (PDF / text / table / code)? Update frequency?"

**4. Latency budget**

> "p99 latency for retrieval — 100ms, 1s, 10s? Affects reranker feasibility."

**5. Index update freshness**

> "Real-time / hourly / daily? Affects index choice."

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify recall@k definition + query/data profile |
| 5-15 min | Diagnose: why pure dense at 60%? |
| 15-25 min | Hybrid retrieval (BM25 + dense + RRF) |
| 25-35 min | Reranker layer + query understanding |
| 35-45 min | Eval + observability |

---

## 我会这样答（sample）

> "Clarify — *[假设: recall@10 on 200 annotated queries, queries mixed (keyword + semantic), corpus PDFs+tickets+contracts (long-form), latency 1s, daily index update]*.
>
> **Diagnose first** — common reasons pure dense fails:
> 1. **Acronyms / product names** — 'TPv3' doesn't embed well, BM25 catches exact
> 2. **Long documents** — single embedding loses detail, chunks too coarse
> 3. **Domain mismatch** — base embedding model not finetuned to your jargon
> 4. **Numeric / code** — semantic meaningless on '5xx errors', BM25 catches
>
> **My proposal — 5-layer retrieval pipeline**:
>
> **Layer 1: Query understanding**
>
> ```python
> def expand_query(raw):
>     # LLM-based rewrite for context-poor queries
>     rewritten = llm.rewrite(raw, context=prev_messages)
>     # HyDE (Hypothetical Document Embeddings): generate fake answer, embed it
>     hyde_doc = llm.generate_answer(raw)
>     # Multi-query: 3 paraphrases for recall
>     paraphrases = llm.generate_paraphrases(raw, n=3)
>     return {
>         'original': raw,
>         'rewritten': rewritten,
>         'hyde': hyde_doc,
>         'paraphrases': paraphrases,
>     }
> ```
>
> **Layer 2: Parallel retrieval (BM25 + dense)**
>
> ```python
> async def hybrid_retrieve(queries, top_k=50):
>     # Dense: embed + ANN search
>     dense_results = await asyncio.gather(*[
>         dense_index.search(embed(q), top_k=top_k)
>         for q in [queries['original'], queries['hyde']]
>     ])
>     
>     # Sparse: BM25
>     sparse_results = await asyncio.gather(*[
>         bm25_index.search(q, top_k=top_k)
>         for q in [queries['original']] + queries['paraphrases']
>     ])
>     
>     return dense_results, sparse_results
> ```
>
> **Why both**:
> - Dense good at semantic (paraphrase, synonym)
> - Sparse good at keyword (rare terms, exact match)
> - Recall typically +15-20% combining
>
> **Layer 3: Fusion (RRF)**
>
> ```python
> def reciprocal_rank_fusion(result_lists, k=60):
>     # Standard formula: score(doc) = sum over lists: 1 / (k + rank(doc, list))
>     scores = defaultdict(float)
>     for lst in result_lists:
>         for rank, doc in enumerate(lst):
>             scores[doc.id] += 1.0 / (k + rank + 1)
>     return sorted(scores.items(), key=lambda x: -x[1])[:100]
> ```
>
> RRF is **simpler than weighted score fusion** and works because it operates on ranks (no calibration needed).
>
> **Layer 4: Reranker (cross-encoder)**
>
> ```python
> def rerank(query, candidates, top_k=10):
>     # Cross-encoder scores [query, doc] jointly
>     pairs = [(query, doc.text) for doc in candidates]
>     scores = cross_encoder.predict(pairs)  # e.g., bge-reranker-large
>     ranked = sorted(zip(candidates, scores), key=lambda x: -x[1])
>     return [c for c, s in ranked[:top_k]]
> ```
>
> Cross-encoder is **slower per pair but more accurate**. Use for top-50 → top-10 stage.
>
> **Layer 5: Metadata filter + freshness boost**
>
> ```python
> def post_filter(results, user_perms, time_decay=True):
>     filtered = [r for r in results if user_perms.can_access(r)]
>     if time_decay:
>         # Boost recent docs
>         for r in filtered:
>             r.score *= exp(-(now() - r.updated_at) / TIME_DECAY_TAU)
>     return sorted(filtered, key=lambda x: -x.score)
> ```
>
> **Expected recall trajectory**:
> - Pure dense baseline: 60% recall@10
> - + BM25 fusion: 75-78%
> - + Query rewrite: 80-83%
> - + HyDE / multi-query: 83-86%
> - + Cross-encoder reranker: 90-92%
>
> **Eval setup (critical)**:
>
> ```python
> # Ground truth set: 200 (query, [relevant_doc_ids]) pairs
> for query, expected in eval_set:
>     retrieved = pipeline.retrieve(query, top_k=10)
>     # Recall@10
>     hits = len(set(retrieved) & set(expected))
>     recall = hits / len(expected)
>     # NDCG: positional + graded relevance
>     ndcg = compute_ndcg(retrieved, expected_graded)
>     # MRR: position of first relevant
>     mrr = 1 / first_relevant_rank
> ```
>
> Track all 3 metrics. Recall is **necessary but not sufficient** — NDCG catches 'right doc but at position 9'.
>
> **Observability** in production:
> - Click-through rate per result position (engagement-based eval)
> - User explicit feedback (thumbs)
> - Diversity (avoid 10 near-duplicates in top 10)
> - Coverage (% queries finding > 0 relevant)
> - Latency p99 per layer
>
> **What I would NOT do**:
> - Use vector search alone for keyword-heavy queries
> - Skip eval set (just 'feels better')
> - Apply reranker to top-1000 (too slow)
> - Forget perms filter (data leak)"

---

## 简历专属 reframe

| 题 | 你做过 |
|---|---|
| Hybrid (BM25 + dense) | BNPL chatbot RAG — 你必处理 product code (sparse needed) |
| Query rewrite | Voice agent — ASR errors require rewrite before search |
| Reranker | Internal Agent Platform retrieval — 你 likely 用过 cross-encoder |
| Eval set methodology | ConvFinQA — ablation eval methodology 你做过 |
| Perms filter | TikTok payment — natural multi-tenant |

**Quote**:

> "On BNPL chatbot RAG, switching from pure dense (e5-large) to BM25 + dense + RRF + reranker bumped recall@10 from 67% to 88%. The biggest single jump was BM25 because customer support tickets had **product codes** ('iPhone 15 Pro Max 256GB' kind) that pure embeddings collapsed into generic 'phone' clusters. BM25 caught exact code matches. RRF fusion was almost free, no calibration tuning. Reranker (bge-reranker-large) added 3-4 points at the end with +200ms latency cost."

---

## 5 follow-ups

**Q1**: "Reranker too slow (200ms × top-50 = 10s). How fix?"
**A**:
- **Distill**: bge-reranker-base instead of large, 3-5x faster
- **Parallel**: batch reranker inference
- **Cascade**: cheap reranker top-100 → top-30 → expensive reranker → top-10
- **Hardware**: GPU inference, TensorRT optimization

**Q2**: "Query 'how do I file a refund' returns relevant docs but they're for a DIFFERENT product. How fix?"
**A**: Missing entity / context awareness:
- **Conversational context**: prior turns mention product
- **Session metadata**: user's product list
- **Multi-stage**: identify product → filter index pre-search
- **Personalization signal**

**Q3**: "Index update — daily okay, but real-time content (new tickets) missed."
**A**: Two-index hybrid:
- **Hot index**: last 24h, in-memory, refreshed every 5 min
- **Warm index**: rest, daily rebuild
- Search both, merge results

**Q4**: "User wants to find docs by date range / author. Current search ignores."
**A**: **Structured filter alongside semantic**:
- Query: "errors from last week by SRE team" → parse → filter `date_range + author + free_text`
- Run BM25/dense on free_text, apply structured filter at retrieval (not post-rank)
- Use vector DB that supports metadata filter natively (Qdrant, Weaviate)

**Q5**: "Recall is 90% but users still complain. Why?"
**A**: Recall ≠ user satisfaction. Other axes:
- **Precision** at top-3: is most relevant first?
- **Answer synthesis quality**: retrieval right, LLM still mis-summarizes
- **Coverage**: queries where no relevant doc exists at all (expected behavior, set expectations)
- **UX**: source citations missing makes user distrust

---

## ❌ 易错点

1. **Pure dense everywhere** — fails on keyword-heavy
2. **No fusion** — pick one of dense/sparse, lose other side
3. **Apply reranker to too many** — latency blow
4. **No eval set** — 'feels better'
5. **No perms filter** — data leak
6. **No metadata filter** — date/author/scope ignored
7. **No freshness signal** — stale docs surface

---

## ✅ 加分项

1. **Diagnose first** before blanket fix
2. **RRF over weighted score** (no calibration)
3. **Query rewrite / HyDE / multi-query** explicit
4. **Cross-encoder reranker** with cascade
5. **Eval: recall + NDCG + MRR**
6. **Metadata filter** at retrieval not post-rank
7. **Hot + warm index** for real-time
8. **Quote BNPL chatbot recall improvement 67→88**

---

## Cheat Sheet

```
5-layer retrieval pipeline:
  L1 Query understanding (rewrite + HyDE + multi-query)
  L2 Parallel retrieval (BM25 + dense)
  L3 RRF fusion (rank-based, no calibration)
  L4 Cross-encoder reranker (top-50 → top-10)
  L5 Metadata filter + freshness + perms

Why hybrid > pure dense:
  Dense: semantic, paraphrase, synonym (good)
  Sparse: rare terms, codes, exact match (good)
  Combined: +15-20% recall typical

RRF formula:
  score(doc) = sum: 1 / (k + rank(doc, list))
  Default k=60

Eval metrics:
  Recall@k (necessary)
  NDCG (positional + graded)
  MRR (first relevant rank)
  Plus production: CTR, thumbs, diversity, coverage

Reranker:
  bge-reranker-large / cohere-rerank
  Cascade if too slow: cheap reranker → expensive
  GPU + TensorRT

Metadata filter:
  Date / author / perms / product
  Apply at retrieval level (vector DB native filter)

Hot + warm index:
  Hot: last 24h, every 5 min refresh
  Warm: rest, daily rebuild

红线:
  - Pure dense for keyword
  - No fusion
  - Reranker on top-1000
  - No eval set
  - No perms filter
```
