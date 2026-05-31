# 🔍 T2.1 · Hybrid Search (Dense + Sparse + Rerank) — 冲刺版

> 完整版: [gfde-t2-hybrid-search.html](gfde-t2-hybrid-search.html). 这页是 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: recall@10 on 200 annotated queries (kappa 0.78), queries mixed (40% has SKU/acronym, 60% natural), corpus PDFs+tickets+contracts (avg 800 tok/chunk), latency 1s budget, daily index, multi-tenant strict perms."

**5-layer retrieval pipeline (recall 60→90 的关键)**:

### Layer 1: Query Understanding (Gemini 3 Flash, ~$0.0001/q)

- **Rewrite** (conversational context 补全): "how do I set up dual SIM" + 上文 iPhone → "How to set up dual SIM on iPhone 15 Pro"
- **Multi-query expand** × 3 paraphrase: "逾期付款" → ["late payment", "overdue", "missed payment"]
- **HyDE**: 生成假答案 embed (短 query 长 doc distribution mismatch)
- **Decompose** for multi-hop: "ARR>10M AND headcount<50" → 2 sub-queries

### Layer 2: Parallel retrieval (asyncio.gather, NOT serial)

```python
dense_r, sparse_r = await asyncio.gather(
    qdrant.search(embed(q), k=100, filter={'tenant_id': t}),  # gemini-embedding 768d
    opensearch.search(q, k=100, filter={'tenant_id': t}),     # BM25 k1=1.2 b=0.75
)
```

**Filter at retrieval time** (Vertex Vector Search query_filter), NOT post-rank — post-rank 丢 top-k 大部分.

### Layer 3: RRF fusion (k=60, paper 推荐)

```
score(doc) = Σ over lists: 1 / (k + rank(doc, list))
```

- Rank-based, **不需 calibration** (BM25 0-∞ vs cosine 0-1 不可比)
- Default k=60: rank 1 拿 1/61, rank 100 拿 1/160, 平滑衰减
- Top-100 → top-50

### Layer 4: Cross-encoder rerank cascade

- Stage 2a: bge-reranker-v2-base (CPU/GPU) → top-25, ~80ms
- Stage 2b: bge-reranker-v2-m3 (multilingual, A10G FP16 batch 50) or Vertex AI Ranker → top-10, ~150ms
- High-stake: LLM-judge (Gemini 3 Pro) top-3 final, ~3-5s, optional

### Layer 5: Filter & boost (perms / freshness / source-type)

- **Perms**: tenant_id + ACL groups at retrieval time
- **Freshness**: `exp(-Δt/τ)` τ=90d (news τ=1-7d, legal τ=∞)
- **Source boost**: policy doc > ticket

### Edge cases (背 5 个)

- **EC1 Acronym/SKU 漏召回**: pure dense 把 "iPhone 15 Pro Max" 压到 "phone" 簇 (training 里 long token 稀疏). BM25 IDF 让罕见 token 高分 → 必上 hybrid.
- **EC2 Weighted fusion scale 不可比**: dense cosine [0,1] vs BM25 [0,∞] 直接加权出错 → RRF 用 rank, 完全免 calibration; 若坚持 weighted 必 per-query min-max normalize.
- **EC3 Reranker 跑 top-1000**: 200ms × 1000 = 200s 爆 → cascade narrow 到 top-50 再 cross-encode.
- **EC4 Cross-tenant 数据泄漏**: 共享 index 检到别人 doc → metadata filter at retrieval time, Vertex Vector Search `filter` 原生支持; post-rank filter 会丢 top-k.
- **EC5 Hot index 缺失**: 新 ticket 24h 后才能搜 → hot index (last 24h, in-memory, 5min refresh) + warm (daily Qdrant), RRF merge.

### Production hardening (1 min)

- **Eval**: 200 human-label (kappa>0.7) + 1000 LLM-synth, recall@1/3/5/10 + NDCG@10 + MRR
- **Slice**: short / long / has_sku / has_acronym / is_question / multilingual — 每 slice 独立 metric
- **CI regression**: 每次 retrieval 改动跑 eval, drop >2pp 阻断 merge
- **A/B 1-2 周**: CTR top-3, time-to-answer, thumbs-up, p99 latency
- **Observability**: p99 per layer (Phoenix/LangSmith), per-tenant empty-rate, GPU util

### 🪝 Resume hook

"BNPL chatbot 7 国 RAG: 初版纯 dense (gemini-embedding) recall 67%, 用户 quote 订单号 'BNPL-2024-IDR-late-fee-cap' 类 policy ID 查不到. 加 BM25 hybrid + RRF k=60 → 78%, 加 query rewrite/multi-query → 83%, 加 bge-reranker-v2-m3 (A10G FP16 batch 50, +180ms) → 88%. 用户 thumbs-up +12% (p<0.01, A/B 1 周). 最大单点收益是 BM25 catching SKU/policy ID, dense 压成 'phone' / 'fee policy' 簇."

---

## 🔥 5 Follow-ups (面试官会问)

**Q1: Reranker 太慢 (200ms × top-50 = 10s)?**
Cascade (bge-base → bge-large/Cohere → LLM-judge); GPU batch FP16 (50 pairs 单 forward 80ms vs 单条 50×20ms=1s); TensorRT INT8 3-5x; distillation large→small 80% quality at 5x speed; caching (query, candidate_ids) Redis 1h TTL 30-40% hit; 砍 reranker 投资 better first-stage (HyDE + multi-query).

**Q2: 用户问 "how do I file a refund", 返回的是其他产品 refund?**
缺 entity 上下文. 4 招: (1) Conversational rewrite — prior turn mention 产品 → rewrite 含产品; (2) Session metadata as hard filter; (3) Multi-stage classify intent → identify product → filter index; (4) Personalization signal — past interactions weight specific product doc.

**Q3: Index update — daily 行, 但新 ticket 实时查不到?**
Two-index hybrid: **hot index** last 24h in-memory (Redis vector 或小 Qdrant), 5min refresh; **warm index** rest daily rebuild on Qdrant. Search 两边, RRF merge. 或 Qdrant 原生 incremental upsert (single-doc, no full reindex).

**Q4: Recall 90% 但用户还抱怨?**
Recall ≠ satisfaction. 其他维度: precision @top-3 (reranker quality), answer synthesis (LLM 错总结), coverage (无 relevant doc 时 UX escape valve), citation 缺失让用户不信, latency 4s 即便准也烦, diversity (10 个 near-dup user perceives 窄).

**Q5: 3rd-party API 完全没 BM25, 怎么 hybrid?**
Self-host OpenSearch / Elasticsearch BM25, 同 chunk 双写 dense (Vertex Vector Search) + sparse. 或用 Vertex AI Search (managed hybrid). 或学习 sparse encoder (SPLADE/uniCOIL) 用 LLM 生成 sparse vec 走倒排. 最次也要 keyword filter pre-stage.

---

## ❌ 易错点 (10 条红线)

1. Pure dense everywhere — Acronyms / SKU / error code / 代码 全 miss
2. Weighted score fusion 不 calibrate — BM25 0-∞ vs cosine 0-1 加权出错
3. Reranker 跑 top-1000 — latency × 20, 10s+
4. No eval set, "feels better" 调参 — 三月后没人知好坏
5. No perms filter — 跨租户泄漏 = SaaS 死刑
6. **Post-rank filter** 而不是 retrieval-time — 丢 top-k 大部分
7. 单 embedding 通吃 legal/code/medical — 各需 domain finetune
8. Chunk size 一刀切 512 — FAQ 100 / policy 800 / ticket 300 不同
9. 没 query rewrite — conversational context 丢
10. 没 A/B framework — 上线了不知好坏

---

## ✅ 加分项 (10 条)

1. **Diagnose first** — 4 类失败 case 举例 (acronym/SKU/code/long-doc)
2. RRF default + sweep weighted for advanced
3. Multi-query + HyDE + decompose explicit
4. Cross-encoder cascade (cheap → expensive)
5. GPU batch FP16 + TensorRT INT8 / Vertex AI Ranker managed
6. Eval: recall + NDCG + MRR + slice + IAA kappa>0.7
7. Retrieval-time filter (Vertex Vector Search filter, Qdrant query_filter)
8. Hot + warm index for real-time freshness
9. A/B framework multi-metric (CTR, time, thumbs, latency)
10. Quote BNPL recall 67→88 + bge-reranker-v2-m3 + 12% thumbs

---

## 一句话总结

Hybrid retrieval = **「BM25 抓字面 + Dense 抓语义 + RRF 不需 calibrate + Cross-encoder cascade + Query understanding 扩展 + Eval slice 量化」**, 5 层流水线每层贡献 3-15% recall. **60% → 90% 是组合拳, 不是换 embedding 一招**.

---

## 🃏 Cheat Sheet (印 1 页随身)

```
5-layer pipeline:
  L1 Query understanding (rewrite + multi-query + HyDE + decompose)
  L2 Parallel retrieval (BM25 + dense, asyncio.gather)
  L3 RRF fusion (rank-based, k=60, no calibration)
  L4 Cross-encoder cascade (bge-base → bge-large/Cohere → optional LLM-judge)
  L5 Filter & boost (perms / freshness / source-type)

Recall trajectory (each layer):
  Pure dense baseline:        60%
  + BM25 + RRF:               +12-18% (75-78%)
  + Query rewrite/multi-q:    +3-5%   (80-83%)
  + HyDE:                     +2-4%   (82-85%)
  + Cross-encoder rerank:     +3-5%   (88-92%)

RRF formula:
  score(doc) = Σ 1 / (k + rank(doc, list))
  k=60 paper recommended
  rank 1: 1/61; rank 100: 1/160 (smooth)

Why dense ≠ sparse (complementarity):
  Dense ✓ paraphrase, synonym, natural language
  Dense ✗ SKU, acronym, error code, function name
  BM25  ✓ rare term (high IDF), exact match
  BM25  ✗ paraphrase, "逾期" vs "late payment"

Fusion decision:
  RRF k=60         default, no calibration, robust
  Weighted (α=0.6) have eval set, sweep α per domain
  Adaptive         classify query (has_sku → α=0.3, natural → α=0.7)
  Learned (LTR)    have click data + ML platform

Reranker options (2026):
  bge-reranker-v2-m3   free, multilingual, A10G FP16 150ms ⭐
  bge-reranker-v2-large free, English, 300ms
  Cohere rerank-3      $1/1K calls API, 200ms
  Vertex AI Ranker     managed (GCP), pay-per-use
  LLM-judge (Pro/Opus) high-stake top-3 only, $$$

Reranker latency optimization:
  Cascade (cheap → expensive)
  GPU batch FP16 (50 pairs single forward 80ms)
  TensorRT INT8 (3-5x more)
  Distillation (large→small 80% quality 5x speed)
  Caching (Redis 1h, query+candidate_ids hash)
  Micro-batch across queries (wait 50ms, batch 32)

Eval metrics:
  Recall@k (set coverage, 不被 reranker 改变)
  NDCG@k (position-aware, reranker target)
  MRR (first-relevant rank)
  Slice: short/long/has_sku/has_acronym/multilingual/doc_len
  A/B prod: CTR top-3, time-to-answer, thumbs, p99 latency

Eval set construction:
  200-500 human-labeled (Cohen's kappa > 0.7)
  + 1000-5000 LLM-synthetic (calibrated vs human subset)
  Per-quarter refresh (query distribution drifts)

Multi-tenant perms:
  Filter at retrieval time (Vertex Vector Search filter)
  NEVER post-rank filter (loses top-k)
  Per-tenant index 或 metadata filter 强制

Hot + warm index:
  Hot: last 24h, in-memory, 5min refresh
  Warm: rest, daily rebuild on Qdrant
  Search both, RRF merge

GCP stack (2026):
  Vertex AI Vector Search (向量, filter native)
  Vertex AI Embeddings text-embedding-005 (768d, $0.025/1M tok)
  Vertex AI Ranker (managed cross-encoder)
  OpenSearch on GCE / Elasticsearch managed (BM25)
  Phoenix (Arize) / Cloud Trace (observability)
  Document AI (PDF parse)
  Cloud DLP (PII)
  VPC Service Controls (tenant isolation)
  AWS: OpenSearch + Bedrock KB / Kendra comparison

红线:
  - Pure dense for keyword
  - No fusion / weighted unnormalized
  - Reranker on top-1000
  - No eval / no slice
  - No perms filter (or post-rank filter)
  - One embedding all domain
  - Chunk size 一刀切
  - No A/B in prod
```
