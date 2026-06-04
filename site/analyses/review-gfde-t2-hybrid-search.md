## T2.1 · hybrid search 60→90% recall — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](gfde-t2-hybrid-search.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t2-hybrid-search.html`](gfde-t2-hybrid-search.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"Pure semantic search recall is 60%. Get it to 90%+"** 或 **"Why does hybrid (BM25 + dense) beat pure dense? When does it NOT help?"**, 我按这 8 层回答, 不跳序.

### 📐 60% → 90% Recall Pipeline — 8 层结构

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 |
|---|---|---|---|---|
| 1 | Clarify + Pure dense failure mode | 0-4 min | 文档类型 (PDF / ticket / contract)? Query 形态 (产品名 / 概念 / 多 hop)? Volume? Latency budget? **然后 demo failure**: query "iPhone 15 Pro Max 256GB dual SIM" → dense embed 把它当"高端手机" → 召回 iPhone 12 / 三星 S23, 漏掉 iPhone 15 真文档. 40% miss 的根因是 SKU / acronym / 罕见 token 没语义 | "Before designing the fix — let me show why pure dense leaks 40%. Embedding compresses SKU / acronym / rare token semantics, so 'iPhone 15 Pro Max' and 'iPhone 13' end up close in vector space." |
| 2 | 5-layer pipeline 骨架 | 4-10 min | **L1 Query Understanding** (LLM rewrite + multi-query + HyDE + decompose) **L2 Multi-source** (Dense ANN + BM25 同时检 top-100) **L3 Fusion** (RRF k=60) → top-50 **L4 Cross-encoder rerank** (bge-reranker-v2-m3 GPU) → top-10 **L5 Filter & Boost** (perms / freshness / source-type weight) → final top-K | "I split the pipeline into 5 layers — query understanding, multi-source retrieve, fusion, rerank, filter. Each layer is independently observable and ablatable." |
| 3 | Dense vs BM25 vs Cross-encoder 决策表 | 10-16 min | **Dense bi-encoder** 大 corpus 召回 (10K-1B docs), embed once. **BM25 sparse** exact match / SKU / code / rare term. **Cross-encoder** per-query 重排 top-50, 贵但准. **ColBERT late-interaction** 中间方案. **LLM-as-retriever** 高质量小规模 | "Three retrieval families — dense, sparse, cross-encoder — each has a sweet spot. Here's the decision table." |
| 4 | RRF fusion 数学 | 16-22 min | RRF formula: `score(d) = sum over sources of 1/(k + rank_s(d))`, k=60 default. Rank-invariant (不需要 normalize scores). 比 weighted score 鲁棒 (不被极端 score 主导). 加权变种: 给 BM25 更高 weight for exact-match query | "Fusion choice is RRF. Critical insight is it's rank-invariant — no need to normalize scores from different retrievers. k=60 is the empirical sweet spot." |
| 5 | Reranker 深度 | 22-30 min | bi-encoder 召回快, cross-encoder 精排准 (cross-attention 看 query+doc 一起). bge-reranker-v2-m3 / Cohere rerank-3 / Voyage rerank-2 / Jina rerank. **Cache (query, doc) pair** 30-40% hit. LLM-as-rerank (Claude/Gemini 评 1-5 score) 是新 trend, 贵但准. Fine-tune on domain (legal/medical) 再 +3-5% | "Reranker is the precision booster. Cross-encoder reads query+doc jointly via cross-attention. Caching (query, doc) hashes saves 30-40%; LLM-as-rerank is the 2025 trend." |
| 6 | Ablation methodology | 30-37 min | **关键: 每个 layer 的 recall 增量独立量化**. baseline 60%, +BM25 fusion +12-18% (→ 75%), +query rewrite +3-5% (→ 80%), +HyDE +2-4% (→ 84%), +cross-encoder +3-5% (→ 88%), +domain fine-tune +2-3% (→ 90%). Eval: recall@k, NDCG, MRR, slice eval (per query type) | "Now the methodology — I never deploy a layered system without per-layer ablation. Each layer must prove its recall delta independently. Here's the contribution breakdown." |
| 7 | When hybrid DOESN'T help | 37-43 min | (1) Query 纯概念无 SKU → dense 已够 (BM25 噪音多反而拉低 precision) (2) 短 query 1-2 token → BM25 不稳 (3) Non-English low-resource → BM25 tokenizer 差 (4) 极小 corpus < 1K docs → 直接全 reranker 更简单. **Edge case**: dense + reranker 没 BM25 也可达 85%+ in pure concept domain | "Anti-pattern alert — hybrid isn't always net positive. Pure concept domains, very short queries, small corpus, low-resource languages all break the assumption." |
| 8 | Connect + production hardening | 43-50 min | BNPL chatbot 60→90% 实战: pure dense 漏 BNPL-2024-IDR-late-fee-cap policy ID → 加 BM25 + ID prefix index 解决. Multi-tenant filter via Vertex AI Vector Search `tenant_id` namespace. Freshness decay `score *= exp(-age_days/30)`. Per-tenant eval slice (避免 head tenant 撑住 metric) | "Resume hook — BNPL chatbot 60→90% was this exact ablation. Let me share the policy-ID story and the per-tenant slice eval." |

### 🎯 为啥按这个序

**Pure dense failure mode (Layer 1) 必须最先讲** — 这一句把面试官的 mental model 校准到「embedding 不是万能」, 后面所有改造才有动机. 然后 5-layer pipeline (2) 是骨架, 给整体框架. Decision table (3) 是 building block 介绍. RRF 数学 (4) 是技术细节, k=60 是经典加分知识点. Reranker (5) 单列因为它是 precision booster 而非 recall — 这个区分面试官常考. **Ablation methodology (6) 是关键** — 没这一层, 60→90% 就是空话, 有这一层就是 staff-level scientific rigor. When-doesn't-help (7) 体现反思, 不所有 problem 都用同一锤. Resume close (8) 用 60→90% 数字最有说服力.

### 🔥 哪一层最容易被追问 deeper

- **Layer 5 (reranker)**: "Cross-encoder 为什么准?" → 准备 cross-attention vs dual-tower 解释. "How to choose model?" → 准备 bge-v2 (open) / Cohere rerank-3 (commercial) / Voyage rerank-2 / fine-tuned domain model 对比.
- **Layer 6 (ablation)**: "Recall@k 怎么 ground truth?" → 准备 manual annotation (人标 100-500 query) + LLM-as-judge (Claude eval) + click signal (user 点了哪条) 三个来源.
- **Layer 4 (RRF)**: "为什么 k=60?" → 准备 paper reference (Cormack et al 2009 TREC), k=60 是经验值, 实际可 grid search 在 [10, 100].

### ⏱ 时间压缩版 (30 min round)

- Layer 1 (failure mode) 3 min — 必讲, 这是 anchor
- Layer 2 (5-layer pipeline) 5 min
- Layer 3 (decision table) 跳过 / 一句带过
- Layer 4 (RRF) 3 min
- Layer 5 (reranker) 5 min — 必讲
- Layer 6 (ablation) 6 min — 必讲, 这是分水岭
- Layer 7 (anti-pattern) 跳过 / 1 min
- Layer 8 (connect) 2 min

### 🆘 卡壳兜底 (针对这题)

- 忘了 RRF 公式 → 退回讲「**核心 idea: 每 source 的 rank 转倒数 1/(k+rank), k=60, 多 source sum. 不 normalize, rank-invariant**」
- 忘了具体 reranker 模型名 → 退回讲「**几大族: bge-reranker (open), Cohere rerank, Voyage rerank, Jina rerank. 都是 cross-encoder, 都 ~100-200ms latency on top-50**」
- 被追问 HyDE 是什么 → 退回讲「**Hypothetical Document Embeddings — LLM 先生成 "如果这个 query 的 ideal answer 是什么", 用这个 answer 的 embedding 检索, 不直接 embed query. 因为 doc-to-doc similarity 比 query-to-doc 更准**」
- 忘了 ablation 怎么测 recall → 退回讲「**recall@k = 检索 top-k 中 ground truth doc 占比. Ground truth 来自人工标注或 LLM judge**」
- 被追问 hybrid 不 help 的具体场景 → 退回「**纯概念 query 无 SKU, BM25 噪音多反而 hurt precision**」

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

把 60% recall 推到 90%+ 不是换 embedding, 是 **5-layer 流水线**: Query Understanding → Parallel Retrieval (BM25 ∥ Dense) → RRF Fusion → Cross-encoder Cascade → Filter & Boost, 每层 +3-15%, 各层独立可 ablate.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| **Bi-encoder** | Q/D 独立 embed, cosine score, 可 pre-index | 大 corpus 召回 |
| **BM25** | tf-idf 改良, k1=1.2 b=0.75 | Exact / SKU / 编号 |
| **RRF** | rank-based fusion, k=60, score=Σ 1/(k+rank) | 无 score calibration |
| **Weighted Score Fusion** | α·dense + (1-α)·sparse, 需 min-max normalize | 有 eval set sweep α |
| **Learned-to-Rank (LTR)** | XGBoost / LightGBM 学 click-through | 高 traffic + click 数据 |
| **HyDE** | LLM 生成 hypothetical doc → embed | Query-doc 分布差异 |
| **Multi-query** | 3-5 paraphrase + RRF 合并 | 词汇不匹配 / 同义 |
| **Decompose** | Multi-hop 拆 sub-query 分别检 | 复杂推理 |
| **Cross-encoder** | [CLS] q [SEP] d 联合 attention, per-pair | Rerank top-50 |
| **ColBERT** | Multi-vec per doc, MaxSim, 中间路线 | Quality + ms 级 |
| **Adaptive Fusion** | 根据 query 特征 (acronym ratio) 动态 α | 流量大 + 多语 |
| **HNSW** | Hierarchical NSW graph, M=16 ef=128 | 大多 ANN 默认 |
| **IVF-PQ** | Cluster + product quant, 高压缩 | 1B+ scale, 内存紧 |
| **SPLADE** | LLM 生成 sparse vec, 走倒排 | BM25 升级版 |

### 🎯 5 个核心 Framework

**Framework L1**: Query Understanding (4 子技术)
- When: 任何 production retrieval
- Algorithm: Rewrite (Gemini 3 Flash) → Multi-query × 3 → HyDE (if dist gap) → Decompose (if multi-hop)
- Trade-off: +50-200ms, +5-12% recall
- Tools: Gemini 3 Flash $0.50/1M, Claude Haiku 4.5 $1/1M

**Framework L2**: Parallel Retrieval
- When: 始终
- Algorithm: `await asyncio.gather(bm25_search(q), dense_search(embed(q)))`, top-100 each
- Trade-off: 网络 ~5-15ms, 双索引存储
- Tools: Vertex AI Vector Search + Vertex AI Vector Search / Elasticsearch / Vespa

**Framework L3**: Fusion (3 法)
- When: 始终 (after L2)
- Algorithm: RRF k=60 默认; weighted 有 eval; LTR 有 click 数据
- Trade-off: RRF robust, weighted 上限高 calibration 重, LTR 维护贵
- Tools: 内置实现 50 行 Python

**Framework L4**: Cross-encoder Cascade
- When: Recall@50 > 90% 后, 精度不足
- Algorithm: bge-base 50ms → bge-large 200ms → optional Cohere rerank-3 / LLM-judge
- Trade-off: 每层 +50-200ms, +3-8% NDCG
- Tools: bge-reranker-v2-m3 (free), Cohere rerank-3 ($1/1K), mxbai-rerank, JaColBERT

**Framework L5**: Filter & Boost
- When: 始终 (多租户必须)
- Algorithm: retrieval-time filter (Vertex AI Vector Search query_filter), 非 post-rank
- Trade-off: filter 收缩候选集, 不影响 quality
- Tools: Vertex AI Vector Search filter, Vertex AI Vector Search term filter

### 🌳 关键决策树 (ASCII)

```
Q: 我应该用哪种 fusion?
├── 有 click data + 高流量      → Learned-to-Rank (XGBoost/LightGBM) ⭐
├── 有 eval set + 单 domain     → Weighted (sweep α 0.3-0.7)
└── 起步 / 无 calibration       → RRF k=60 ⭐⭐ default

Q: 我该不该上 reranker?
├── Recall@50 < 85%             → 先优化 retrieval, 别 rerank
├── Recall@50 > 90% & NDCG 差   → 加 bge-base (50ms)
├── Quality 关键 + 预算 OK      → cascade: bge → bge-large → Cohere/LLM
└── Latency p99 < 100ms 必须    → 别 cross-encoder, 用 ColBERT

Q: 哪种 query understanding?
├── 短 keyword query (SKU/ID)   → 跳过, 直 BM25 强
├── 模糊 / 长 / 自然语言        → Rewrite + Multi-query
├── Query-doc 分布差 (Q短D长)   → HyDE
└── 多 hop (where/who/why 套)   → Decompose
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: Bi-encoder vs Sparse 数学**
- Bi: cosine(E_q, E_d) = E_q·E_d / (||E_q||·||E_d||), 双塔独立 forward, 可 pre-index
- BM25: Σ IDF(qi) · (tf(qi,d)(k1+1)) / (tf(qi,d) + k1(1-b+b·|d|/avgdl)), 默认 k1=1.2 b=0.75
- 失败 case: dense miss "iPhone 15 Pro Max 256GB" (压缩到 cluster); BM25 miss "逾期=late payment" (词不重)
- Top 3 gotchas: cosine 不归一化 / stopword 过 / 一刀切 chunk
- Tools: bge-large-zh, Vertex AI Vector Search 默认 BM25, Lucene

**Problem 2: Fusion 策略 (RRF / Weighted / LTR)**
- RRF: `score = Σ 1/(60+rank)`, 无 normalize, default
- Weighted: `score = α·MinMax(d_score) + (1-α)·MinMax(bm25_score)`, sweep α ∈ [0.3, 0.7]
- LTR: features (rank_d, rank_s, score_d, score_s, doc_len, freshness, perm_match) → XGBoost
- Adaptive: 根据 query has_acronym / has_digit 调 α
- Top 3 gotchas: 没 normalize / α 没 sweep / LTR 没在线特征飘移
- Tools: scikit-learn ranknet, XGBoost LambdaRank, LightGBM

**Problem 3: Query Understanding 4 法**
- Rewrite: Gemini 3 Flash "纠错+resolve pronoun"; 1 round 100ms
- Multi-query: LLM 生成 3-5 paraphrase, 各检 RRF
- HyDE: 用 LLM 生成 fake answer 然后 embed; query→doc 分布差大用
- Decompose: "where did the CEO of X go to college" → ["CEO of X", "college of <ceo>"]
- Top 3 gotchas: 每个 query 都 4 路 (cost) / decompose 失败 fallback / cache hit 低
- Tools: Gemini 3 Flash, Claude Haiku 4.5, LangChain MultiQueryRetriever

**Problem 4: Reranker Cascade + Latency 优化**
- Cascade: top-200 → bge-base top-50 → bge-large top-20 → Cohere top-10 → LLM-judge top-3 (optional)
- Latency: FP16 2x / INT8+TensorRT 3x / batch 32-64 throughput 3x / distill 5x
- Caching: Redis (hash(q), [c.id]) 1h TTL, FAQ workload 30-40% hit
- Top 3 gotchas: top-1000 cross-encode 自爆 / CPU forward / 不 cache
- Tools: bge-reranker-v2-m3, Cohere rerank-3 API, vLLM/Triton

**Problem 5: Eval Methodology**
- Recall@k = (#relevant in top-k) / (#total relevant)
- NDCG@k = DCG / IDCG, 位置敏感 (rerank 目标)
- MRR = 1 / rank_first_relevant
- Slice: acronym / SKU / short / long / question / multilingual
- Eval set: 200-500 人工 (kappa > 0.7) + 2K-5K LLM 合成 calibrated
- A/B prod: CTR top-3, time-to-first-click, thumbs, per-tenant
- Top 3 gotchas: 只看 Recall (不看 NDCG) / 没 slice / synthetic 没 calibrate
- Tools: BEIR, MTEB, Phoenix, LangSmith, custom domain eval

### 🔥 Production gotchas (top 15)

1. Pure dense for SKU / 编号 → 必加 BM25
2. Weighted fusion 没 min-max normalize → dense (0-1) 和 BM25 (0-∞) 不可比
3. Reranker 跑 top-1000 → 50s latency 自爆
4. Cross-tenant leak → retrieval-time filter (Vertex AI Vector Search query_filter) 强制
5. Post-rank perms filter → top-k 被吃光, 返回空
6. 凭 feel 调参 → 必有 eval set + CI regression
7. 单 embedding model 通吃 code/legal/medical → 各自 specialized
8. Cosine = confidence (其实是相对排序)
9. Embed query 时不 normalize → 距离全错
10. Hot index 缺 → 新 ticket 24h 不可搜
11. Multi-query 每个 query 都 4 路 → cost 爆
12. LLM-as-rerank 全量 → $0.005/q × 1M = $5K/day
13. HNSW M / ef 默认拷贝 → 大 corpus recall 掉
14. Stopword 过滤过强 → "how to" 整词被吃
15. Embedding model upgrade 没 blue/green → 全索引重建期间断流

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Hybrid + RRF | BNPL chatbot | Dense 78% → +BM25+RRF 89% → +bge-reranker 92%, A/B 上 |
| Query Understanding | BNPL multi-lingual | Multi-query (6 lang) +5pp; pronoun resolution 助 multi-turn |
| Reranker cascade | BNPL chatbot | bge-base → bge-large cascade, +60ms hide in stream |
| Eval slice | BNPL slice metrics | acronym/SKU/long query 单独 weekly regress |
| Multi-tenant filter | BNPL 7 markets | Vertex AI Vector Search query_filter per tenant_id, cross-tenant zero leak |
| LTR | TikTok PayLater | Click data → XGBoost LambdaRank, +6pp NDCG |
| HyDE | ConvFinQA | 财报问题 query 短 doc 长 → HyDE +3pp recall |
| Specialized embed | BNPL code search | bge-large 通用 → CodeBERT 代码 search, +9pp |

### 🎤 面试现场 quotables (top 8)

> "60% to 90% recall isn't one model upgrade — it's 5 layers each contributing 3-15%."

> "RRF beats weighted score because dense cosine (0-1) and BM25 (0-∞) aren't comparable without per-domain calibration."

> "Cross-encoder earns its cost only when first-stage recall is at top-50 and precision is the bottleneck — don't rerank top-1000."

> "On BNPL, dense missed 22% of order-number queries because embedding clusters 'order 12345' with 'order 67890'. BM25 catches that for free."

> "Multi-tenant must filter at retrieval time, not post-rank — post-rank filter eats your top-k and you return empty."

> "HyDE wins when your query is short ('iPhone dual SIM?') and your doc is long — the distribution gap kills cosine."

> "I always carry an eval set of 200 human-labeled + 2000 LLM synthetic calibrated against the human subset, and CI runs it on every model upgrade."

> "ColBERT is the middle ground when you need 95% recall but can't afford cross-encoder latency."

### 🚨 红线 (top 10 anti-patterns)

1. Pure dense for keyword / SKU / 编号
2. No fusion (single-source retrieval)
3. Reranker on top-1000 candidates
4. No eval set ("we feel it's better")
5. Post-rank perms filter (loses top-k)
6. Single embedding model for all domain
7. Cosine = confidence misconception
8. Weighted fusion without min-max normalize
9. No A/B before rolling out reranker
10. Ignoring slice metrics (acronym/SKU/multilingual)

### 🛠️ Tool zoo (2026)

| 类别 | Tool | 一句话 |
|---|---|---|
| Vector DB | Vertex AI Vector Search, Vertex AI Vector Search, Weaviate, Milvus, FAISS, pgvector | Vertex AI Vector Search 性价比 ⭐ |
| Sparse | Vertex AI Vector Search, Elasticsearch, Vespa, Lucene | Vertex AI Vector Search default |
| Embedding | gemini-embedding-001, text-embedding-3-large, bge-large, voyage-3 | Gemini 多语 / bge 自部署 |
| Reranker | bge-reranker-v2-m3, Cohere rerank-3, mxbai-rerank, JaColBERT | bge multilingual free |
| Multi-vec | ColBERTv2, JaColBERT | Late interaction 中间路线 |
| LTR | XGBoost LambdaRank, LightGBM Ranker | Click data 上 LTR |
| Query expansion | LangChain MultiQueryRetriever, DSPy ChainOfThoughtWithHint | Production framework |
| Tracing | Phoenix (Arize), LangSmith, Langfuse | Phoenix 开源 |
| Eval | BEIR, MTEB, Ragas, custom domain | BEIR 通用 benchmark |
| Inference | vLLM, Triton, TensorRT, TGI | vLLM 高 throughput |

### 📊 Recall 提升组合拳 (60% → 92%)

```
Pure dense baseline                  60%
+ BM25 fusion (RRF k=60)            +12-18%   → 72-78%
+ Query rewrite + Multi-query       +3-5%     → 75-83%
+ HyDE                              +2-4%     → 77-87%
+ Cross-encoder reranker            +3-5%     → 80-92%
+ Domain finetune reranker          +3-8%     → 88-95% (in-domain)

Each layer 独立可 ablate, FDE 必能讲清每层贡献多少
```

### 💻 一段最小 prod-ready hybrid

```python
async def hybrid_search(query: str, tenant_id: str, k: int = 10):
    # L1: query understanding (Flash, optional)
    queries = [query] + multi_query_expand(query, n=3)
    
    # L2: parallel retrieval
    dense, sparse = await asyncio.gather(
        qdrant.search(embed(queries[0]), top=100,
                      filter={"tenant_id": tenant_id}),
        opensearch.search(query, top=100, filter={"tenant_id": tenant_id}),
    )
    
    # L3: RRF
    rrf = {}
    for r, d in enumerate(dense): rrf[d.id] = rrf.get(d.id, 0) + 1/(60+r)
    for r, d in enumerate(sparse): rrf[d.id] = rrf.get(d.id, 0) + 1/(60+r)
    fused = sorted(rrf.items(), key=lambda x: -x[1])[:50]
    
    # L4: cross-encoder rerank (cached)
    candidates = [docs[id] for id, _ in fused]
    reranked = await rerank_cached(query, candidates, top=k)
    
    # L5: freshness boost
    return apply_freshness_decay(reranked)
```

### 🎬 45-min answer rhythm

```
0-5    Clarify: corpus / doc type / tenancy / SLA / multilingual / freshness
5-10   Mental model: 5-layer pipeline (L1-L5)
10-15  L2 + L3 (parallel retrieval + RRF k=60), 解释 dense vs BM25 complementarity
15-25  L4 reranker cascade + GPU batch + cache + cost math
25-35  L1 query understanding (rewrite/multi-q/HyDE/decompose) + L5 filter
35-40  Eval set + slice metrics + A/B + production observability
40-45  简历 quote (BNPL 78%→89%→92% recall arc)
```

### 🔑 5 layer mnemonic

```
L1 Query Understanding (rewrite + multi-query + HyDE + decompose)
L2 Parallel Retrieval (BM25 ∥ dense, asyncio.gather)
L3 RRF Fusion (k=60, rank-based)
L4 Cross-encoder Cascade (bge-base → bge-large/Cohere → LLM-judge)
L5 Filter & Boost (perms / freshness / source-type)
```
```
