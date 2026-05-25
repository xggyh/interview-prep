## Q28 · LLM 搜索从 1.5s 压到 100ms

> "Your LLM-powered semantic search (over 10M documents) is hitting **p50 1500ms**. PM wants **p50 100ms**. Current path: embed query (100ms) → vector search (200ms) → LLM rerank (500ms) → LLM summarize (300ms) → post-process (400ms). **How do you get 15× speed-up?** What can you cut without killing quality?"

**Round**: System Design (60 min)
**出处**: Exponent 2026 FDE · 公司: Anthropic Search / Perplexity / Cohere / Glean · 行业: AI search / enterprise search
**约束**: 10M docs / quality bar (nDCG@10 ≥ baseline, factuality ≥ 95%) / cost can grow modestly (≤ 2×) / no quality regression > 2% / streaming UI allowed

---

## 📖 术语速查 (本题用到的)

> 这题是 search + LLM latency 优化. 不懂术语跟不上每个 ms 的攻略. 5 min 看完.

### Latency / UX 概念

| 术语 | 解释 |
|---|---|
| **p50 / p95 / p99** ⭐ | 50% / 95% / 99% 分位的延迟. p50 = 中位数. |
| **TTFT (Time-To-First-Token)** ⭐ | 首字延迟 — streaming 时关键. |
| **TTFB (Time-To-First-Byte)** | 首字节延迟. |
| **Perceived latency** ⭐ | 用户感知延迟 — 100ms TTFT 即使总 300ms 也感觉 instant. |
| **Streaming (SSE)** | Server-Sent Events — 边算边返回. |
| **Debouncing** | 防抖 — user 还在 type 时不触发 search. |

### Search 架构

| 术语 | 解释 |
|---|---|
| **Semantic search** ⭐ | 语义搜索 — 用 embedding 找语义相近文档. |
| **Vector search / K-NN** | 向量最近邻搜索. |
| **HNSW (Hierarchical Navigable Small World)** ⭐ | 主流近似最近邻算法. |
| **ef_search** ⭐ | HNSW 搜索宽度 — 调大 recall ↑ 速度 ↓. 调小反之. |
| **ef_construction** | HNSW 建图宽度. |
| **M (graph degree)** | HNSW 每节点连接数. |
| **BM25** | 经典 keyword 检索算法. |
| **Hybrid retrieval** | 向量 + BM25 双路融合. |
| **RRF (Reciprocal Rank Fusion)** | 排名倒数融合算法. |
| **ColBERT / Late interaction** | token-level 后期交互检索, 比 single-vector 准. |
| **Prefilter vs Postfilter** ⭐ | 搜索前 / 后过滤. ACL 用 prefilter. |
| **Filter-aware HNSW** | 内置 filter 跳过不符合节点的 HNSW. |
| **Navigational query** | 导航式查询 ("facebook login") — 直接跳到已知页面. |
| **Lookup query** | 查找式 — 给我一堆链接. |
| **Analytical query** | 分析式 — 需要 LLM 综合回答. |

### Cascade / 路由

| 术语 | 解释 |
|---|---|
| **Cascade architecture** ⭐ | 级联架构 — 简单 query 走便宜路径, 难 query 走全套. |
| **Query router / classifier** | 查询路由 / 分类器. |
| **Fast path vs Full path** ⭐ | 快路径 (80% 流量, 80ms) vs 全路径 (20%, 300ms). |
| **Skip ladder** | 跳过阶梯 — 高置信度时跳过 reranker / LLM. |
| **Tail query** | 长尾查询 — rare entity, 难 query. |

### Reranker

| 术语 | 解释 |
|---|---|
| **Reranker** ⭐ | 重排 — top-100 retrieve 后用更准但更慢模型重排到 top-10. |
| **Cross-encoder** | 双输入交叉模型 — query 和 doc 一起算 score, 比 bi-encoder 准. |
| **Bi-encoder** | 双塔模型 — query 和 doc 分别 encode, 余弦相似度. 快. |
| **MS MARCO** | 微软 search 数据集, 训 reranker 标配. |
| **MiniLM** | 小型 BERT 系列, distill 用. |
| **Cohere Rerank** | Cohere 的 reranker API. |
| **Score gap / Score separation** | top-k 分数差距 — 大 = confident, 小 = ambiguous. |

### 量化 / 蒸馏

| 术语 | 解释 |
|---|---|
| **Distillation** ⭐ | 蒸馏 — 用大模型当 teacher 训小模型 student. |
| **Distilled embedder** | 蒸馏小 embedder (BGE-small 384d). |
| **BGE-large vs BGE-small** | 1024 / 384 维 embedder. |
| **text-embedding-3-large** | OpenAI 3072 维 embedder. 慢但准. |
| **FP16 / FP8 / INT8** | 不同精度量化. |
| **Speculative decoding** | 推测解码 — 小模型预测大模型 verify. |

### LLM / 生成

| 术语 | 解释 |
|---|---|
| **Claude Haiku vs Opus** ⭐ | Anthropic 小型 / 旗舰. Haiku 3× 快 5× 便宜. |
| **GPT-4 / GPT-4 Turbo** | OpenAI 大模型. |
| **Prompt caching** ⭐ | Anthropic 的 prompt cache — system prompt 命中 cache 时 90% 便宜 + 快. |
| **KV cache prefix sharing** | KV 缓存前缀共享. |
| **Prefill** | LLM 输入 forward 阶段. |
| **Decode** | LLM 输出阶段, 一次一个 token. |
| **Max output tokens** | 输出长度上限. |
| **Citation parsing** | 引用解析. |

### Caching

| 术语 | 解释 |
|---|---|
| **Result cache** ⭐ | 完整结果缓存 (Redis), 同 query 同 user 命中. |
| **Embed cache** | 查询 embedding 缓存. |
| **Semantic cache** | 相似 query 的语义级缓存. |
| **Negative cache** | 失败结果短暂缓存防 retry flood. |
| **Cache invalidation** | 缓存失效. |
| **TTL (Time-To-Live)** | 缓存过期时间. |
| **Zipf distribution** | 查询频次 Zipf 分布 — top 20% query 占 80% 流量. |
| **Cache pre-warm** | 预热 — 启动时填好 cache. |
| **Doc-id-aware invalidation** | doc 更新时反向找含它的 cache 失效. |

### 质量评估

| 术语 | 解释 |
|---|---|
| **nDCG@10** ⭐ | Normalized Discounted Cumulative Gain top-10 — 检索质量金标准. |
| **MRR (Mean Reciprocal Rank)** | 平均倒数排名. |
| **Recall@K** | top-K 中相关文档比例. |
| **Precision@K** | top-K 中精确率. |
| **Factuality** | 事实准确性 — LLM 输出有依据 vs 编造. |
| **Hallucination** | 幻觉 — 编造内容. |
| **Human eval / Golden set** | 人工评估 / 黄金集. |
| **Active learning** | 主动学习 — 低 confidence 样本人工标后重训. |
| **A/B test** | 上线前的对比实验. |

### 部署 / 后处理

| 术语 | 解释 |
|---|---|
| **PII redaction** | PII 脱敏. |
| **Audit log** | 审计日志. |
| **Async fire-and-forget** | 异步不阻塞主流程. |
| **CDN / Edge caching** | 边缘缓存 — Cloudflare / CloudFront. |
| **OTel (OpenTelemetry)** | observability 标准. |
| **Bedrock** | AWS LLM 托管服务. |
| **T4 / H100 GPU** | NVIDIA GPU 型号. |

---

## 这道题在考什么

不是考你 "更快", 是考你**理解每一个 ms 在哪 + 知道哪些可以 cut**:

1. **Cascade architecture** — small model first, escalate only when needed
2. **Caching layers** — embed cache, retrieval cache, reranker cache, generation cache
3. **Pre-computation** — index time vs query time work split
4. **Parallelism** — sequential 200+500+300 = 1000, parallel = 500
5. **Quantization + distillation** — smaller faster model with eval-validated quality
6. **HNSW tuning** — ef_search, prefilter strategies
7. **Skip ladders** — high-confidence skip reranker, skip summarize
8. **Streaming partial** — perceived latency vs actual
9. **菜鸟答案失败点**: "上更快 GPU" — 没 attack architecture. "缓存" — 没说 invalidation. "去掉 reranker" — 没 quality guard.

---

## 必问 clarifying questions

1. **What's "search" UI**: 像 Google 给 top-10 link, 还是 Perplexity 给 answer + citations? 巨大不同
2. **Quality bar**: nDCG / MRR / human eval, 多少 budget 可降?
3. **Cost budget**: 1500ms infra cost vs 100ms, willing 2× spending?
4. **Cache friendliness**: query repeat rate? 高 cache 可以大. (e.g., 70% queries 看过)
5. **Doc corpus update**: static 还是 hourly inflow? 影响 pre-compute
6. **Streaming OK?**: 100ms first token + rest stream OK 还是 must be full result 100ms?
7. **User behavior**: 用户输 query 后 type more 还是 immediate submit? 关系 to debouncing
8. **Existing infra**: 已经有 vector DB / GPU pool 吗?

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|------|------|------|
| 1 | Clarify + decompose | 5 min | 拆 1500ms into 5 stages, 哪个最难 cut | "我先 attribute 每个 stage, 然后选 attack" |
| 2 | Cascade architecture | 10 min | 大部分 query 走 fast path, hard query 走 full | "70% query 用 fast path 100ms, 30% 用 full" |
| 3 | Embed: cache + small model | 7 min | Query embed cache + distilled embed | "Embed cache hit 80% → 100ms → 5ms" |
| 4 | Retrieval: HNSW tune + prefilter | 8 min | ef_search 调小 + pre-filter ACL | "HNSW ef 调 + prefilter → 200ms → 30ms" |
| 5 | Reranker: skip ladder + cascade | 8 min | High-conf skip + distilled cross-encoder | "500ms → 0ms or 50ms" |
| 6 | LLM: distill + speculative + skip | 8 min | 300ms LLM → 50ms with skip-summary | "Skip summary if user wants link list" |
| 7 | Post-process: parallelize + async | 4 min | 400ms post → 20ms sync, rest async | "Audit / analytics push 到 background" |
| 8 | Trade-offs + close | 5 min | 100ms vs quality matrix, streaming option | "100ms p50 OK, p99 200ms; streaming for hard queries" |

---

## 端到端架构图 (ASCII)

```
                                User submits query
                                       │
                                       ▼
   ┌─────────────────────────────────────────────────────────────────────────────┐
   │  QUERY ROUTER (decide fast vs full path, < 5ms)                             │
   │   ▸ Cache lookup (Redis): result for (query_hash, user_acl_hash)            │
   │   ▸ Query classifier: hard query (long, multi-hop)? OR simple?              │
   │   ▸ Pick path                                                               │
   └────────────────────────┬───────────────────────┬────────────────────────────┘
                            │                       │
                            ▼                       ▼
   ┌─────────────────────────┐         ┌─────────────────────────────────────────┐
   │  FAST PATH (target 80ms)│         │  FULL PATH (target 300ms streaming)     │
   │                         │         │                                         │
   │  1. Query embed         │         │  1. Query embed (cache or compute)      │
   │     - 80% cache hit (5ms)         │     - 50ms                              │
   │     - else BGE-small (30ms)       │  2. Hybrid retrieval (50ms)             │
   │  2. HNSW search ef=32   │         │     - HNSW + BM25 + RRF                 │
   │     - return top-10     │         │  3. Cross-encoder rerank (40ms)         │
   │  3. Cheap rerank (skip) │         │     - distilled, top-100 → top-10       │
   │  4. Return top-10 links │         │  4. LLM summarize (200ms streaming)     │
   │     + snippet           │         │     - Claude Haiku 4.6 distill           │
   │  5. Post-process async  │         │     - First token < 100ms               │
   │                         │         │  5. Post-process parallel               │
   │  Total: ~80ms p50       │         │  Total: ~300ms p50 (200ms TTFT)         │
   └─────────────────────────┘         └─────────────────────────────────────────┘
                                                  │
                                                  ▼
                                       ┌─────────────────────────┐
                                       │  Stream to user         │
                                       └─────────────────────────┘

   Background (async, doesn't block):
   ─ Cache write (Redis SET 1h TTL)
   ─ Analytics emit (Kafka → DWH)
   ─ Eval sample (1% queries → human review queue)
   ─ Telemetry (OTel)

   Periodic (off-line):
   ─ Distill reranker (weekly, from logs)
   ─ Index rebuild HNSW (nightly delta + monthly full)
   ─ Query log embedding for cache pre-warm
```

---

## 详细设计 (60-min walkthrough)

### Phase 1: Clarify + decompose (5 min)

开口:
- "1500ms 是 p50 还是 p99? PM 想 100ms 是 p50 还是 p99?"
- "Search UI: link list (Google-like) 还是 answer (Perplexity-like)? 巨大区别"
- "Cache friendliness: query repeat 率? 70% 重复 vs 5% 重复 完全不同 strategy"

假设: p50 1500 → 100, UI 是 link list 主 + answer 可选, query repeat ~50%.

KPI:
- **p50 latency**: 100ms (target)
- **p99 latency**: 500ms (acceptable)
- **TTFB (time to first byte)**: 50ms
- **Quality (nDCG@10)**: ≥ 95% of current
- **Cost**: ≤ 2× current

阶段分:
- Embed 100ms
- Vector search 200ms
- LLM rerank 500ms
- LLM summarize 300ms
- Post 400ms
- Total 1500ms

Attack priority by impact:
1. LLM rerank 500ms — biggest, cut to ~0-50ms
2. Post-process 400ms — easy to async out
3. LLM summarize 300ms — cut to 0 (link list) or 200ms streaming
4. Vector search 200ms — tune HNSW
5. Embed 100ms — cache aggressive

### Phase 2: Cascade architecture (10 min)

**核心 insight**: 不是所有 query 都需要 LLM rerank + summarize. Cascade = cheap path for easy queries, expensive path for hard.

**Query classifier (< 5ms)**:
```python
def classify_query(query, user_context):
    # Fast features
    token_count = len(tokenize(query))
    has_question_words = any(w in query.lower() for w in ['what', 'how', 'why', 'explain'])
    is_navigational = matches_known_entity(query)  # "facebook login"
    
    if is_navigational:
        return 'navigational'  # cached top-1 result
    if token_count < 5 and not has_question_words:
        return 'lookup'  # link list, no LLM
    if 'compare' in query or 'difference' in query:
        return 'analytical'  # full path
    return 'mixed'
```

**Path routing**:
- `navigational` (10% of traffic): pure cache, ~20ms
- `lookup` (60%): fast path, top-10 link + snippet, no LLM, ~80ms
- `analytical` (20%): full path with LLM summarize, ~300ms streaming
- `mixed` (10%): fast path first, async escalate if needed

**Fast path detail**:
- Cache lookup
- If miss: embed (cache 80% hit) → HNSW search → return links
- No LLM rerank for lookup (use vector similarity as rank)
- No LLM summarize

**Full path detail**:
- Cache lookup (less hit since varied)
- Embed → hybrid retrieve → cross-encoder rerank → LLM summarize streaming

**Why this works**:
- LLM rerank for navigational/lookup is overkill, vector similarity sufficient
- Most users want quick links, only some want answer
- Streaming for analytical means 100ms TTFT acceptable for 300ms total

### Phase 3: Embed: cache + small model (7 min)

**Current**: 100ms embed (probably text-embedding-3-large or BGE-large via API call)

**Fix 1: Query cache**

```python
# Redis cache, key by normalized query
key = f"emb:{normalize(query)}"
cached = await redis.get(key)
if cached:
    return numpy.frombuffer(cached, dtype=np.float32)

# Miss: compute
emb = await embedder.encode(query)
await redis.setex(key, 3600, emb.tobytes())  # 1h TTL
return emb
```

Hit rate: 80% for popular queries (skewed Zipf distribution).
- Hit: 1ms (Redis GET)
- Miss: 30ms (small embedder)
- Average: 0.8 × 1 + 0.2 × 30 = 6.8ms ≈ 7ms

**Fix 2: Distilled smaller embedder**

OpenAI text-embedding-3-large 100ms-ish (3072 dim).
Replace with BGE-small (384 dim) self-host:
- 7ms inference on CPU batch, 2ms on T4 GPU
- Quality 90-95% of large (acceptable with reranker)

If quality drops too much, train smaller embed model:
- Distill from large to small: teacher (large) generates embeddings, student (small) learn to mimic
- 1-2% quality drop, 10× speed

**Fix 3: Index size implication**

10M docs × 384 dim × 4 bytes = 15GB raw vs 10M × 3072 × 4B = 120GB raw.
Smaller embedding → smaller index → faster HNSW (less memory pressure).

**Result**: 100ms → 7ms average

### Phase 4: Retrieval: HNSW tune + prefilter (8 min)

**Current**: 200ms HNSW search, probably default `ef_search=128`

**HNSW parameters trade-off**:
| Param | Higher | Lower |
|---|---|---|
| `M` (graph degree) | Better recall, slower build, more memory | Faster, lower recall |
| `ef_construction` | Better build quality | Faster build |
| `ef_search` | Better recall, slower query | Faster query, lower recall |

For 10M docs, common: M=32, ef_construction=200, ef_search=128.

**Fix 1: Reduce ef_search**

`ef_search=32` cuts search time ~4× (200ms → 50ms). Recall@10 drops ~1-2%.

For lookup path (cascade fast), 1-2% recall drop OK.
For analytical path, keep `ef_search=128`.

**Fix 2: Prefilter ACL**

Pre-filter user accessible doc_ids (e.g., 500 / 10M = 5K docs user can see) → search on small subset.

```python
# Bad: search 10M then filter
results = hnsw.search(query_emb, k=100)
filtered = [r for r in results if r.doc_id in user_acl_ids]

# Good: prefilter then search
hnsw.search(query_emb, k=10, filter_ids=user_acl_ids)  # internal candidate skip
```

Most vector DBs (Qdrant, Milvus, Weaviate) support filter-aware HNSW that skips non-matching nodes.

**Fix 3: Hybrid (BM25 + HNSW)**

If query has rare token (e.g., product code "ABC-123"), BM25 wins. HNSW alone misses.

```python
# Parallel
hnsw_task = asyncio.create_task(hnsw.search(query_emb, k=50))
bm25_task = asyncio.create_task(bm25.search(query, k=50))
hnsw_res, bm25_res = await asyncio.gather(hnsw_task, bm25_task)

# Fuse with RRF (rank reciprocal)
final = rrf_fuse(hnsw_res, bm25_res, k=10)
```

Latency: max(hnsw, bm25) = ~50ms (parallel).

**Fix 4: Pre-computed dense + sparse**

- HNSW for dense
- BM25 sparse via Lucene/OpenSearch
- ColBERT for late interaction (precompute token embeddings, score at query time)

Latency: 30-50ms hybrid retrieval.

**Result**: 200ms → 30-50ms

### Phase 5: Reranker: skip ladder + cascade (8 min)

**Current**: 500ms LLM rerank (probably GPT-4 or Cohere Rerank API)

This is the **biggest cut opportunity**.

**Fix 1: Skip reranker on high confidence**

```python
def needs_reranker(hnsw_results):
    # If top-3 results have clear score separation, no need to rerank
    top_3_scores = [r.score for r in hnsw_results[:3]]
    if top_3_scores[0] - top_3_scores[2] > 0.15:
        return False  # confident
    return True  # ambiguous, need rerank
```

~40% queries have confident ranking, skip rerank → 500ms → 0ms.

**Fix 2: Distilled cross-encoder (not LLM)**

LLM rerank is overkill for most cases. Use cross-encoder:
- MS MARCO-trained cross-encoder (e.g., ms-marco-MiniLM-L-12-v2)
- 50ms for top-100 candidates
- Quality 95% of LLM rerank on benchmarks

```python
# 100 candidates × cross-encoder → top-10
scores = cross_encoder.score([(query, c.text) for c in candidates])
top_10 = sorted(zip(candidates, scores), key=lambda x: -x[1])[:10]
```

**Fix 3: Cascade rerank**

```
Level 1: HNSW score → top-100 (free)
Level 2: Bi-encoder (small) score → top-30 (10ms)
Level 3: Cross-encoder rerank → top-10 (40ms only on hard queries)
Level 4: LLM rerank → top-3 (200ms only on very hard / paid)
```

Most queries stop at Level 2-3. Level 4 only for analytical / VIP.

**Fix 4: Reranker batch + cache**

Identical (query, doc) pair → cache score. Hit rate ~30% on popular queries.

**Result**: 500ms → average 20ms (60% skip + 40% × 50ms)

### Phase 6: LLM summarize: distill + speculative + skip (8 min)

**Current**: 300ms LLM summarize (probably GPT-4 Turbo)

**Fix 1: Skip for lookup path**

60% queries are lookup (just want links). No summary needed.
→ 0ms for 60% queries.

**Fix 2: Smaller distilled model for summarize**

For analytical queries, use:
- Claude Haiku 4.6 instead of Opus 4.7
- Cost: 5× cheaper, speed: 3× faster
- Quality: 90% of Opus on summary benchmarks
- ~100ms instead of 300ms

**Fix 3: Streaming first token**

Even if total 200ms, stream first token at 30ms → user perceives instant.
- Server-Sent Events
- Client buffers and displays incrementally

UI perception:
- 100ms before first character: feels instant
- 100ms-1s: noticeable but acceptable
- > 1s: feels slow

So 300ms total with 30ms first token is OK perceptually.

**Fix 4: Prefill optimization**

Reuse system prompt KV cache (prefix caching in vLLM / Anthropic prompt cache).
- 4K system prompt prefill ~50ms saved
- Anthropic cached prompt 90% cheaper

**Fix 5: Limit output**

Summarize in 3 sentences, not 5. Cuts ~30% decode time.

**Result**: 300ms → 30ms (skip 60%) or 150ms (streaming, perceived < 100ms TTFT).

### Phase 7: Post-process: parallelize + async (4 min)

**Current**: 400ms post-process (probably synchronous: PII redact, citation parse, audit log, analytics emit)

**Fix 1: Async non-critical**

Critical for response: PII redact, citation parse (~50ms total).
Non-critical: audit log, analytics emit, eval sample → async background.

```python
# Sync
text = redact_pii(text)            # 30ms
citations = parse_citations(text)  # 20ms
# Send response

# Async (fire and forget)
asyncio.create_task(audit_log(query, response, user))
asyncio.create_task(analytics_emit(query, response, latency))
asyncio.create_task(maybe_sample_for_eval(query, response))
```

**Fix 2: Pre-compute heavy work**

PII detector training, citation parser regex compilation → load at startup, not per request.

**Result**: 400ms → 20-50ms sync

### Phase 8: Trade-offs + alternatives (5 min)

**Total latency after fixes**:

| Stage | Before | Fast path | Full path |
|---|---|---|---|
| Embed | 100ms | 7ms | 7ms |
| Retrieval | 200ms | 30ms | 50ms |
| Rerank | 500ms | 0ms (skip) | 40ms |
| LLM | 300ms | 0ms (skip) | 150ms streaming |
| Post | 400ms | 20ms | 30ms |
| **Total** | **1500ms** | **57ms p50** | **277ms with 100ms TTFT** |

Fast path: 57ms ✓ < 100ms target

Full path (20% of traffic): 277ms with streaming → perceived 100ms.

Weighted avg: 80% × 57 + 20% × 277 = 100ms p50 ✓

**Decision 8.1 — Quality risk**

| Fix | Quality impact |
|---|---|
| Smaller embedder | -1-2% recall |
| Lower ef_search | -1-2% recall |
| Skip reranker on confident | -0.5% nDCG |
| Distilled reranker | -1% nDCG |
| Claude Haiku for summary | -3% summary quality |
| Total | -5-6% in worst case, OK if measured |

Mitigation: A/B test before rollout, measure nDCG@10 + human eval on 1% sample.

**Decision 8.2 — Cost impact**

| Item | Before | After |
|---|---|---|
| Embedding API | $5K/m (OpenAI) | $500/m (self-host BGE-small) |
| Vector DB | $3K/m | $3K/m (same) |
| Reranker | $4K/m (Cohere API) | $1K/m (self-host) |
| LLM | $20K/m (GPT-4) | $5K/m (Claude Haiku) |
| Total | $32K/m | $9.5K/m |

3× cheaper + 15× faster. The "1-2% quality loss" is well worth it.

**Decision 8.3 — When NOT to cascade**

- Regulatory: financial / medical search may require full path for all queries (audit defensibility)
- VIP user: paid tier gets full path always

---

## 关键决策点 (with rationale)

1. **Cascade architecture** — 80% queries cheap path, 20% expensive. 一刀切 fast = quality挂.

2. **Embed cache 80% hit** — Zipf distribution of queries makes cache hugely effective.

3. **Smaller embedder (BGE-small 384d)** — 10× faster, 90% quality, with downstream reranker compensating.

4. **HNSW ef_search 调小** for fast path — recall trade-off accepted on lookup queries.

5. **Skip reranker on confident scores** — 40% queries don't need it.

6. **Distilled cross-encoder, not LLM rerank** — 10× faster, 95% quality.

7. **Stream LLM output** — TTFT 50ms perceived instant even with 300ms total.

8. **Async non-critical post-process** — analytics / audit doesn't block response.

9. **Anthropic prompt cache** — system prompt prefix shared, 50ms saved per call.

10. **A/B + nDCG monitoring** — every cut has eval gate.

---

## 数字 (capacity sizing, cost math)

**Volumes**:
- 1M queries/day, 50 QPS sustained, 200 peak

**Hardware (cascading)**:
- Embedding: 4× T4 GPUs (BGE-small batched) = $300/m
- HNSW: r6gd.4xlarge × 4 (128GB, 4 shards) = $1200/m
- Cross-encoder rerank: 2× T4 = $150/m
- LLM (Claude Haiku via Bedrock): pay per token = $5K/m for 200K queries × analytical path

**Cache**:
- Redis cluster (3× cache.r6g.large): $400/m
- 80% embed hit, 50% result hit

**Total**: ~$9.5K/m for 1M queries = $0.0001 per query (cf. $32K/m before)

**Latency budget validation**:
- Fast path (80% traffic): 7+30+0+0+20 = 57ms ✓
- Full path (20%): 7+50+40+(50 TTFT) = 147ms TTFT, 300ms total with stream
- Weighted p50: 100ms ✓

**Quality**:
- nDCG@10 drop: 0-2% on lookup, 1-3% on analytical
- Within < 5% acceptable budget

**Throughput**:
- 200 QPS peak, each takes 100ms → 20 concurrent
- Current infra handles 500+ concurrent → headroom

---

## Gao Xin 简历专属 reframe

1. **TikTok PayLater BNPL RAG** — 你直接 prod 优化过 LLM 搜索, cache + retrieval + rerank trade-off 你做过.

2. **TikTok Voice agent latency** — voice 1.5s 已是死刑, 你 push 过 < 800ms, 这道题模式同源.

3. **ConvFinQA multi-hop** — 你处理过 retrieve + compose latency, 减少 LLM call 数 是优化重点.

4. **Internal Agent Platform** — 你做过 tool selection cache + RAG over tool catalog, 这道题里 result cache 同思路.

5. **Indonesia 7 market latency** — region affinity + caching, 你都跑过.

reframe: "我在字节做 BNPL search 时面对类似 problem: 1.2s p50 压到 300ms, 用了 cascade (60% lookup 不走 LLM) + embed cache + distilled reranker. 这道题 100ms 更激进, 加 stream + skip ladder + parallel hybrid retrieval. 我之前 quality 监控是 nDCG + human eval 1% sample, 这道题直接套."

---

## 5 个 Follow-ups

1. **"smaller embedder quality drop 太多 (nDCG -5%), 怎么 mitigate?"** — 答: (a) Distill larger to smaller, finetune on your data (1-2% recoverable); (b) Multi-vector: keep large embed for offline pre-compute index + small for query (cheaper); (c) Hybrid retrieval (BM25 + small dense) compensates for individual recall loss; (d) ColBERT late interaction expensive but better.

2. **"cache invalidation? doc 更新了 cached result 仍 stale"** — 答: (a) TTL 1h reasonable for most search (acceptable staleness); (b) Doc-id-aware invalidation: when doc updates, invalidate any cache containing doc_id (maintain reverse index); (c) Versioned doc: cache key include doc_version, automatic miss on update; (d) For critical fresh queries (news, finance), bypass cache with `?bypass_cache=true` param.

3. **"如果 query 没 cached + lookup classified wrong, 100ms 装不下, 怎么 fallback?"** — 答: (a) Server-Sent Events streaming: emit partial result early, refine later; (b) Per-request budget enforcement: 100ms hit, return what we have, mark "partial"; (c) Background continue: complete full result, user can refresh (rare); (d) Re-classify on retry: misclassified query reclassify with more context.

4. **"distilled reranker quality drop 在 long-tail query (rare entities) 比 popular 严重, 怎么办?"** — 答: (a) Cascade rerank: small + medium + large; (b) Tail detect: query rarity score (TF-IDF + entity match) high → route to bigger rerank; (c) Active learning: log low-confidence queries, label, retrain; (d) Hybrid retrieval (BM25) for rare entity catches that distilled embedder misses.

5. **"if PM 也要 p99 100ms 不只 p50, 怎么 do?"** — 答: 100ms p99 极困难. (a) 杀死 full path (analytical 也走 fast); (b) Aggressive cache (95% hit); (c) Pre-compute popular query result offline; (d) Edge caching (CDN) for popular results; (e) 接受 5-10% queries 触发 fast fail + retry with stream "give me a moment"; (f) 跟 PM 谈 p95 vs p99 trade-off — p95 100ms 可达, p99 200ms 合理.

---

## ❌ 死路答法

1. **"上 H100"** — 没 attack architecture, GPU 加 1.5× speed only.
2. **"cache everything"** — 不区分 cacheable vs 不可 cacheable, invalidation 灾难.
3. **"去掉 reranker"** — quality 大跌, 没 eval support.
4. **"用 GPT-3.5"** — 没 distill strategy, quality 不可控.
5. **"async 全部"** — critical 也 async 用户看不到完整结果.
6. **"无 streaming"** — 损失 perceived 优化.
7. **"prefilter? 慢"** — 真正 prefilter 在 vector DB 内部 fast, 没读懂.
8. **"semantic cache 用同 query"** — 不一定 same intent, hallucinate.
9. **"不做 A/B, push 上线"** — quality 跌 5% 没人知道.
10. **"100ms p50 不可能, 1500 太多"** — defeatist, 没拆解.

---

## ✅ 加分项

1. **Cascade with query classifier** — 80/20 思维, 不一刀切
2. **5-stage attribution + targeted cut** — 不空谈, 数字驱动
3. **Embed cache + distill + HNSW tune + rerank cascade + LLM stream** — 多 angle attack
4. **Skip reranker on confident scores** — clever trick
5. **Anthropic prompt cache** — 2026 cost optimization
6. **Async non-critical post** — production hygiene
7. **A/B + nDCG monitoring** — quality gate
8. **Streaming SSE for perceived latency** — UX-aware
9. **Cost reduction 3× alongside latency 15×** — staff-level
10. **Numbers 给得出来** (7ms embed cache, ef=32, 100ms TTFT, $9.5K/m)

---

## 一句话总结

1500ms → 100ms 不是 "GPU 加大", 是 **cascade routing (80% lookup 不走 LLM) + embed cache 80% hit + distill small embedder + HNSW tune + skip-or-distilled reranker + stream LLM with skip on lookup + async non-critical post** 一整套 cost-aware quality-controlled 系统优化.

---

## Cheat Sheet

```
Architecture: CASCADE
  Navigational (10%): pure cache, 20ms
  Lookup (60%):       fast path, 80ms
  Analytical (20%):   full path, 300ms with 100ms TTFT streaming
  Mixed (10%):        fast first, async escalate

Per-stage optimization:

Embed (100ms → 7ms):
  - Query cache Redis 1h TTL, hit 80%
  - BGE-small (384d) self-host, 30ms miss
  - Smaller dim = smaller index

Retrieval (200ms → 30ms):
  - HNSW ef_search 32 for fast, 128 for full
  - Prefilter ACL via filter-aware HNSW
  - Hybrid BM25 + HNSW parallel + RRF
  - Total 50ms for full, 30ms fast

Rerank (500ms → 20ms avg):
  - Skip on confident score gap > 0.15 (40% queries)
  - Distilled cross-encoder (ms-marco-MiniLM)
  - Cascade: small → medium → large
  - LLM rerank only for VIP / very hard

LLM summarize (300ms → 0-150ms):
  - Skip for lookup path (60%)
  - Claude Haiku 4.6 not Opus
  - Stream SSE, TTFT 30-50ms
  - Anthropic prompt cache (50ms saved)
  - Limit output 3 sentences

Post-process (400ms → 30ms):
  - Sync: redact PII, parse citation (50ms)
  - Async: audit log, analytics, eval sample

Cost (3× cheaper):
  - Before: $32K/m (OpenAI embed + Cohere rerank + GPT-4)
  - After:  $9.5K/m (BGE + distilled rerank + Claude Haiku)
  - Per query: $0.0001

Quality (≤ 5% drop):
  - Embedder swap: -1-2% recall
  - Lower ef: -1-2% recall
  - Skip rerank: -0.5% nDCG
  - Distilled rerank: -1% nDCG
  - Smaller summary: -3% subjective
  - A/B test + nDCG@10 dashboard + 1% human eval

Latency hit ratio:
  Fast path:  80% traffic, p50 57ms
  Full path:  20% traffic, p50 277ms with 100ms TTFT
  Weighted:   p50 100ms ✓ target

Streaming:
  Always SSE for analytical
  TTFT 30-50ms = perceived instant
  Total ms matters less than TTFT
```
