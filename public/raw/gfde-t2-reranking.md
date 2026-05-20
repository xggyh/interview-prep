## 题目

> "First-pass retrieval gives you top-50 candidates. **Reranker** picks top-10. Explain why you need it, the tradeoffs, and how you'd evaluate."

或追问形态:

> "Cohere rerank vs cross-encoder vs LLM-as-judge for reranking — when each?"

**Round**: RAG Quality / Reranking (45 min)

---

## 这道题在考什么

考你**bi-encoder ≠ cross-encoder** 区别 + production reranker engineering:

1. **First-stage vs second-stage** retrieval 不同 model class
2. **Cross-encoder mechanics** —— 为什么 slower 但 accurate
3. **Latency-accuracy trade-off** —— tune k 平衡
4. **Reranker options** —— Cohere / bge / LLM-judge / custom finetune
5. **Eval methodology** —— NDCG > recall

---

## 必问 clarifying

**1. First-stage 质量**

> "Top-50 recall — what% of expected relevant in top-50? If already 95%, reranker just reorders. If 60%, reranker can't fix what's missing."

**2. Latency budget**

> "Per-query budget — 100ms / 1s / 10s? Affects k size and reranker class."

**3. Quality target**

> "Looking for top-1 accuracy (single best) or top-3 / top-10 (set of good)?"

**4. Volume / cost**

> "QPS expected. Per-query reranker cost compounds."

**5. Domain**

> "Generic web / e-commerce / legal / code? Domain-specific reranker available?"

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify first-stage recall + latency / cost / quality target |
| 5-15 min | Why reranker (bi vs cross encoder math) |
| 15-25 min | Reranker options trade-off |
| 25-35 min | Latency / cost optimization (cascade) |
| 35-45 min | Eval methodology |

---

## 我会这样答（sample）

> "Clarify — *[假设: first-stage recall@50 = 92%, latency 1s budget, top-3 accuracy target, 100 QPS, technical doc domain]*.
>
> **Why reranker** — bi-encoder limitation:
>
> First-stage (dense ANN search) uses **bi-encoder**:
> - Embed query: q_emb = encoder(query)
> - Embed each doc once at index time: d_emb = encoder(doc)
> - Score = cosine(q_emb, d_emb)
>
> **Limitation**: query and doc embedded **independently**. Embedding model never sees them together. So can't learn 'this query word is asking about that doc term'.
>
> **Cross-encoder**:
> - Concatenate: input = [CLS] query [SEP] doc [SEP]
> - Model sees both jointly, attention can cross
> - Single forward pass → relevance score
>
> Cross attention catches subtle relevance that bi-encoder misses. **+15-30% NDCG** typically.
>
> **Cost trade-off**:
> - Bi-encoder: index once, query embedding once → ANN search ~ms
> - Cross-encoder: per query, must run forward pass for **each candidate**. 50 candidates × 100ms = 5s. Too slow for k=1M.
>
> Hence pipeline: bi-encoder narrow to top-50 → cross-encoder rerank to top-10.
>
> **Reranker options — decision matrix**:
>
> | Option | Latency (50 docs) | Cost | Quality | When |
> |---|---|---|---|---|
> | **bge-reranker-base** | ~200ms (CPU) | Free (self-host) | Good | Default, latency-sensitive |
> | **bge-reranker-large** | ~500ms (GPU) | GPU $ | Better | Quality > latency |
> | **Cohere rerank API** | ~200ms | $1/1K calls | Excellent | Easy, no infra |
> | **mxbai-rerank-large** | ~400ms (GPU) | GPU $ | Excellent | Self-hosted Cohere-class |
> | **LLM-as-judge** (GPT-4) | 5-10s | $$$ | Best | Top-3 final pass, expensive |
> | **Domain-finetuned** | varies | training cost | Best for that domain | Have labeled data |
>
> **My recommendation for this case**:
>
> ```
> Stage 1: BM25 + dense → top-50 (50ms)
> Stage 2: bge-reranker-large → top-10 (500ms)
> Stage 3 (optional): LLM-as-judge → top-3 (3s) for high-stakes only
> Total: ~600ms, fits 1s budget
> ```
>
> **Cascade for cost / latency optimization**:
>
> ```python
> def cascade_rerank(query, candidates, target_top_k=10):
>     # Stage A: cheap reranker (bge-base) on top-50
>     scores_a = bge_base.predict([(query, c.text) for c in candidates])
>     top_25 = top_k_by_score(candidates, scores_a, 25)
>     
>     # Stage B: expensive reranker (bge-large) on top-25
>     scores_b = bge_large.predict([(query, c.text) for c in top_25])
>     top_10 = top_k_by_score(top_25, scores_b, target_top_k)
>     
>     return top_10
> ```
>
> Cuts cost ~50% with minimal accuracy loss.
>
> **Reranker prompt for LLM-as-judge** (when used):
>
> ```python
> prompt = f"""
> Query: {query}
> 
> Doc A: {doc_a}
> Doc B: {doc_b}
> 
> Which doc better answers the query? Respond with just A or B.
> """
> ```
>
> Pairwise + sort by win-count. Slower but uses LLM's nuanced understanding. Good for **top-3 final pass** only.
>
> **Eval methodology**:
>
> ```python
> for query, expected_graded in eval_set:
>     reranked = pipeline.retrieve_and_rerank(query, top_k=10)
>     ndcg = compute_ndcg(reranked, expected_graded, k=10)
>     mrr = compute_mrr(reranked, expected_graded)
>     # Pair recall@k with NDCG — recall captures 'in set', NDCG captures 'position-aware'
> ```
>
> Key insight: reranker doesn't improve recall (set is same), improves **NDCG / MRR** (ordering within set).
>
> **A/B test in production**:
> - 50% with reranker, 50% without
> - Compare: CTR, time-to-answer, user thumbs
> - Latency monitoring: alert if reranker p99 > budget
>
> **Latency optimization**:
> - **Batching**: 50 (q, doc) pairs in single forward pass
> - **GPU**: 5-10x speedup over CPU
> - **Distillation**: large reranker → small reranker via knowledge distillation
> - **Quantization**: INT8 / FP16 for inference
> - **TensorRT / vLLM**: production inference engine
>
> **What NOT to do**:
> - Rerank top-1000 (latency blow)
> - Use bi-encoder for reranking (no cross-attention)
> - Skip eval set ('feels better')
> - Replace bi-encoder retrieval with reranker alone (impossible at scale)
> - Same reranker for all query types (some domains need domain-finetuned)"

---

## 多场景变体 + 解法

### 变体 1: E-commerce relevance — product ranking

> "User 搜 'red running shoes size 9'. Top-50 候选, 怎么 rerank?"

**解法**:
- **Multi-objective**: relevance + price + stock + delivery time
- **Learning-to-rank** (LTR): XGBoost / LightGBM with features (semantic_score, BM25, price_diff, has_stock, review_score)
- **Personalization signals**: user history (买过 brand X) 作 feature
- **Diversity penalty**: top-10 都是 Nike → 加多样性
- **Business rule overlay**: promo / margin / inventory clearance 单独 boost (transparent)
- **A/B with revenue**: 不只 NDCG, 看 GMV / CVR

### 变体 2: Q&A passage selection

> "RAG 返回 50 段, 选哪 3 段 feed LLM 答题？"

**解法**:
- **Cross-encoder rerank** with QA-finetune (Cohere rerank, mxbai-rerank)
- **Span-level extract**: 不只选 passage, 用 QA 模型抽出 answer span
- **Multi-passage fusion**: 答案跨段 → 选 complementary 段 (不是冗余)
- **Citation-aware**: 每段加 source ID, 后续 LLM 答时 cite
- **Confidence gating**: top-1 score 低 → 'no good answer found, escalate' 不强答
- **Eval**: SQuAD-style EM/F1 on subsample

### 变体 3: Code search — function from repo

> "Dev agent 搜 'function that parses JWT'. 候选 50 个函数 chunk."

**解法**:
- **Signature match**: 'parse_jwt(token)' 命名 → exact match 优先
- **Symbol-aware reranker**: fine-tune on (query, function) pairs from PR descriptions
- **Test pair boost**: 有对应 test 的函数 > 无 test
- **Usage signal**: 高被调用次数函数 > 孤儿函数 (说明它经过 production 验证)
- **Recency**: 1 月前改的 > 5 年前未改 (后者可能 deprecated)
- **Language-specific**: Python 用 Python-aware encoder, 不是通用

### 变体 4: Multi-modal rerank — image + text query

> "User search 'similar to this dress, but in black'. Image + text query."

**解法**:
- **CLIP-class embedding**: image + text 进同空间, 直接 cosine
- **Reranker**: 大 multimodal model (Cohere multimodal / GPT-4V) 看 query image + candidate image 评分
- **Attribute extraction**: query image → 'red, A-line, knee-length' attribute; combine with 'black' modifier
- **Visual diff penalty**: 太相似的 (perceptual hash) 去重
- **Style transfer aware**: 'similar style, different color' → 颜色 feature 单独 swap
- **Cost**: vision API 贵, 不要 rerank 50 张, narrow to 10 先

### 变体 5: Personalized rerank — user history factored in

> "Top-50 候选, user 看过 / buy 过 / dismiss 过的 history 怎么用？"

**解法**:
- **User embedding**: aggregate 历史 interaction → 1 个 user vector
- **Re-score**: relevance × (1 + α × cos(user_vector, item_vector))
- **Negative signals**: dismissed item 减分 (但不是永久 ban, 时间 decay)
- **Exploration**: 80% personalized, 20% novel (avoid filter bubble)
- **Cold-start fallback**: 新 user 没 history → popularity-based + onboarding 问题
- **Privacy**: user vector 本地化或 federated (隐私敏感场景)

---

## 简历专属 reframe

| 题 | 你做过 |
|---|---|
| Cross-encoder reranker | BNPL chatbot RAG — added bge-reranker, recall@5 → @3 mapping improved |
| Cascade | Voice agent — multi-stage ASR (fast model → expensive verifier) |
| LLM-as-judge | ConvFinQA — your ablation evaluator was LLM-judge style |
| Latency engineering | Voice agent p99 < 800ms streaming — naturally optimized for this |
| Eval set | ConvFinQA — annotated eval set methodology you've done |

**Quote**:

> "BNPL chatbot added bge-reranker-large in the top-50 → top-5 stage. NDCG@5 jumped from 0.71 to 0.83. Latency cost +180ms (GPU batched), within our 1.5s budget. The single biggest win was on **acronym queries** — bi-encoder gave 'phone' for 'iPhone Pro' query, reranker correctly preferred the iPhone-specific doc. We A/B tested 1 week, user thumbs-up rate +12%."

---

## 5 follow-ups

**Q1**: "Reranker latency too high (1s). Need < 200ms total. Options?"
**A**:
- **Cheaper reranker**: bge-reranker-base or distilled small
- **Fewer candidates**: top-20 instead of top-50
- **No reranker, better first stage**: invest in HyDE / multi-query / better embeddings
- **Caching**: cache (query, top-k) for common queries

**Q2**: "LLM-as-judge sounds best — why not always?"
**A**:
- **Cost**: GPT-4 pair-rank 50 candidates ≈ $0.50/query
- **Latency**: 5-10s
- **Consistency**: LLM judgment varies, calibration drift
- **Use case**: top-3 final pass only, high-stakes ✓
- **Mass deployment**: too expensive

**Q3**: "Reranker has its own biases (favors longer docs). How detect?"
**A**:
- **Slice eval by doc length**: NDCG by length quartile
- **Calibration test**: synthesize known-relevant short docs, check still surfaces
- **Diversity in eval set**: span all doc length distributions
- **Compare multiple rerankers**: best per-slice may differ

**Q4**: "Domain-specific (medical, legal). Generic reranker not enough?"
**A**:
- **Finetune** on domain pairs: pre-train + fine-tune on 1K-10K labeled query-doc pairs
- **Hard-negative mining**: include top-ranked-but-wrong as negatives
- **Synthetic data**: LLM generate query-doc pairs for training
- **Cost**: 1 GPU-day to fine-tune, big quality gain in narrow domain

**Q5**: "Reranker performance flat for 6 months. How improve?"
**A**:
- **Data**: add more training pairs from production user feedback
- **Hard negatives**: 'almost-right' docs that reranker mis-orders
- **Newer model**: bge → mxbai → next-gen
- **Eval drift**: ensure eval set reflects current query distribution

---

## ❌ 易错点

1. **Bi-encoder used for reranking** — no cross-attention
2. **Rerank top-1000** — latency blow
3. **No first-stage to narrow** — try to cross-encode 1M docs
4. **No eval** — 'feels better'
5. **Single reranker for all** — domain mismatch
6. **LLM-as-judge for everything** — cost blow
7. **No cascade** — pay expensive on every

---

## ✅ 加分项

1. **Bi vs cross encoder math** explanation
2. **Cascade rerank** (cheap → expensive)
3. **Per-domain finetuning** awareness
4. **GPU + batching + quantization** for latency
5. **NDCG / MRR > recall** for reranker eval
6. **A/B test framework**
7. **LLM-as-judge** as final pass for high-stakes
8. **Quote BNPL bge-reranker +12% thumbs**

---

## Cheat Sheet

```
Bi-encoder vs Cross-encoder:
  Bi: independent embed, cosine score, fast, scale to 1M
  Cross: joint forward pass, accurate, slow, top-50 max
  Use bi for first stage, cross for rerank

Reranker options:
  bge-base: free, fast, good
  bge-large: GPU, slower, better
  Cohere rerank API: $1/1K, excellent
  mxbai-rerank: self-host Cohere-class
  LLM-judge: $$$, slow, top-3 only
  Domain-finetune: best in narrow

Cascade pattern:
  bi-encoder → top-50 (50ms)
  bge-base → top-25 (200ms)
  bge-large → top-10 (500ms)
  LLM-judge → top-3 (optional, slow)

Latency optimization:
  Batching (50 pairs single fwd)
  GPU (5-10x CPU)
  Distillation (large → small)
  Quantization (INT8/FP16)
  TensorRT / vLLM

Eval metrics for reranker:
  NDCG@k (position-aware)
  MRR (first relevant rank)
  Recall stays same (set unchanged)

A/B test in prod:
  CTR
  Time-to-answer
  Thumbs up
  Latency p99

Domain finetune:
  1K-10K labeled (q, doc, score)
  Hard-negative mining
  Synthetic from LLM

红线:
  - Bi for reranking
  - Top-1000 cross
  - No first stage narrow
  - No eval
  - LLM-judge mass
  - No cascade
```
