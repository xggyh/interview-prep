## T2 · RAG / Context 全景 — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](gfde-t2-overview.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t2-overview.html`](gfde-t2-overview.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"Walk me through how you'd design RAG / context management for an agent"** (T2 开放全景题), 我按这 8 层回答, 不跳序.

### 📐 RAG / Context Management 全景 — 8 层结构

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 |
|---|---|---|---|---|
| 1 | Reframe: 不是 "embedding + 向量库" | 0-2 min | 2022 RAG = "chunk → embed → cosine top-K". 2026 production RAG = 7-step pipeline. 直接砍掉 baseline view, 拉到 staff level. | "Before diving — one reframe. The 2022 textbook RAG (chunk-embed-cosine) is now just a baseline. 2026 production RAG is a 7-step pipeline; let me draw it." |
| 2 | Clarify 5 维 | 2-5 min | 客户数据规模 (1k docs / 1M / 10M)? Update frequency (静态 vs 实时)? Latency budget (chat 5s, batch 30s)? 多租户隔离? 文档类型 (prose / tabular / code / mixed)? | "5 clarifications first — data scale, update frequency, latency budget, tenancy isolation, document types." |
| 3 | 3-layer mental model | 5-9 min | **Knowledge boundary** (LLM cutoff 之后 + private = retrieval) / **Context boundary** (fits in 2M 也要 RAG — cost / latency / quality drop / 隔离) / **Trust boundary** (retrieved 是 untrusted, ground in retrieved + resist injection) | "RAG operates at 3 mental layers — knowledge, context, trust. Long-context doesn't kill any of them; let me walk through why." |
| 4 | 7-step online pipeline | 9-20 min | Query understanding (rewrite + intent) → Retrieval routing (skip / SQL / dense / sparse / graph / tool) → Multi-source parallel retrieval → Rerank (RRF + cross-encoder + LLM-as-rerank) → Context assembly (token budget + Lost-in-middle 排序) → Generation with citations → Post-eval (faithfulness, thumbs) | "Now the online pipeline — 7 steps. Each step is a separate design choice and a separate FDE surface area. Let me trace one query through." |
| 5 | 6 sub-topic map | 20-26 min | T2.1 Hybrid Search (dense+sparse+RRF+rerank) / T2.2 Chunking (per-doc-type strategy + late chunking) / T2.3 Context Window Mgmt (sliding/summarize/hierarchical/RAG-on-history) / T2.4 Tool Output→Prompt (XML wrap + provenance) / T2.5 Reranking (cross-encoder + cache) / T2.6 Long-context vs RAG (hybrid is winning) | "RAG splits into 6 sub-topics. Let me give you the 1-paragraph version of each so you can zoom in wherever interests you." |
| 6 | Offline indexing pipeline | 26-32 min | Source ingest (crawler/DB/S3/Confluence) → Parse (PDF: LlamaParse, HTML: trafilatura) → Chunk (recursive/semantic/late) → Embed (text-embed-3 / voyage-3 / cohere-v4 / gemini-embed-1) → Index (Pinecone / OpenSearch BM25 / Neo4j graph). Refresh strategy: incremental + version control | "The online pipeline is half the story. Offline indexing is the other — let me walk through ingest → parse → chunk → embed → index and refresh strategy." |
| 7 | 2026 hot trends | 32-40 min | (1) Late chunking (Jina v3 / Cohere v4) - embed full doc then chunk, 保 long-range context (2) GraphRAG for relation queries (3) LLM-as-rerank with Claude/Gemini scoring (4) Adaptive retrieval (LLM 决定要不要 retrieve) (5) Long-context + RAG hybrid (5K top-K → 200K window) (6) Multi-modal retrieval (image + text + table) | "Industry trends FDE 必懂 — let me hit 6: late chunking, GraphRAG, LLM-as-rerank, adaptive retrieval, long-context + RAG hybrid, multi-modal." |
| 8 | Connect + resume hooks | 40-50 min | BNPL chatbot (RAG hybrid + intent routing, recall 60%→90%). ConvFinQA (multi-hop reasoning + ablation methodology, why GraphRAG helps). Voice agent RAG-on-history (用户上次问什么 retrieval-able) | "Resume hooks — BNPL chatbot hybrid search 60→90%, ConvFinQA multi-hop ablation, voice agent RAG-on-history. Let me close with one specific story." |

### 🎯 为啥按这个序

T2 全景题最容易死法是「上来讲 embedding 怎么算余弦」— 2022 demo 视角. **Reframe (Layer 1) 直接定调**: "我把 RAG 当 7-step pipeline 看, 不当 vector DB 看", 这一句把 leveling 从 L4 推到 L5. Mental model (3) 在 clarify 之后讲是因为它定的是问题框架. 7-step pipeline (4) 是骨架, 6 sub-topic (5) 是分支. Offline (6) 必须讲, 80% 候选人只讲 online 部分, 你讲 offline 立刻显得 production. 2026 trends (7) 是 FDE 加分必讲 — late chunking / GraphRAG / LLM-as-rerank 三个词出来面试官就知道你 read 2024-25 papers. Resume close (8) 用 BNPL 60→90% 数字最有说服力.

### 🔥 哪一层最容易被追问 deeper

- **Layer 4 (pipeline)**: 面试官 80% 会 zoom 到 Step 4 Reranking 或 Step 5 Context Assembly. 准备好 RRF k=60 default 和 Lost-in-middle papers (Liu et al 2023).
- **Layer 7 (hot trends)**: "Late chunking 是什么?" → 准备好 Jina v3 paper 一句话总结 (embed full doc → chunk embedding, 保留 cross-chunk context).
- **Layer 5 (6 sub-topic)**: 面试官选其中 1 个深问 → 准备每个 sub-topic 10 分钟独立 deep-dive 模板 (见 T2.1-T2.6 单独 review 页).

### ⏱ 时间压缩版 (30 min round)

- Layer 1 (reframe) 1 min
- Layer 2 (clarify) 2 min
- Layer 3 (mental model) 跳过 / 压到 1 min, 一句 "3 个 boundary"
- Layer 4 (7-step pipeline) 8 min — 必讲, 这是骨架
- Layer 5 (6 sub-topic) 4 min, 每个 30 秒
- Layer 6 (offline) 4 min — 必讲, 区分 production vs demo
- Layer 7 (hot trends) 5 min — 必讲, 选 3 个 (late chunking + LLM-as-rerank + long-context hybrid)
- Layer 8 (connect) 2 min

### 🆘 卡壳兜底 (针对这题)

- 忘了 7-step 完整顺序 → 退回讲「**3 个核心 stage: Retrieval (multi-source parallel) + Rerank (RRF + cross-encoder) + Generation (citation + faithfulness check). 这 3 个能 cover 80%**」
- 被追问 embedding 模型选哪个 → 退回讲「**text-embed-3-large / voyage-3 / cohere-v4 / gemini-embed-1 are 2026 mainstream. Benchmark on 自己 domain (MTEB 不一定 reflect)**」
- 忘了 RRF 公式 → 退回讲「**核心 idea: 每 source 排名转倒数 1/(k+rank), k=60 default, sum across sources. 不需要 normalize score, rank-invariant**」
- 被追问 long-context 替代 RAG → 退回「**Partial — fits + 少用户 + 非敏感 = long-context 简单胜. 但 cost / latency / 多租户 / knowledge update 还需 RAG. Hybrid (RAG top-K → 200K window) is winning pattern**」
- 不熟某 sub-topic → 主动「**这正好连着 T2.X, 我可以借用吗**」, 把控制权拉回

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

2026 RAG = **query understanding → routing → multi-source retrieval → fusion → rerank → context assembly → grounded generation → post-eval**, 是 7-step pipeline 而非 "embed + vector DB"; 每步都有 design choice + cost knob, FDE 题深 dive 一步.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| **Dense retrieval** | Embed query → cosine vs doc embeddings | 语义 / paraphrase / synonym |
| **Sparse retrieval (BM25)** | tf-idf lexical match | SKU / 人名 / 编号 / exact match |
| **Hybrid search** | Dense + Sparse 并行 + fusion | 生产 default |
| **RRF** | Rank-based fusion, score = Σ 1/(k+rank), k=60 | 无需 calibrate, robust 默认 |
| **Cross-encoder** | 联合 [q;d] 过 transformer, 50-200ms/pair | 重排 top-50 → top-10 |
| **ColBERT** | Multi-vector per doc, MaxSim 操作 | 极致 precision, 存储 10x |
| **HyDE** | LLM 生成假答案 → embed assumed answer | Query-doc 分布差异大 |
| **Multi-query** | LLM 生成 3-5 query 变体, RRF 合并 | 词汇不匹配 |
| **Decompose** | 把 multi-hop 拆成 sub-question | 复杂推理 |
| **Late chunking** | 先 embed 整 doc, 再切 chunk-embedding | 长文+小 chunk 同享上下文 |
| **Contextual Retrieval** | Anthropic 2024, 每 chunk 加 doc summary | +35-49% recall |
| **GraphRAG** | KG 增强 RAG, entity edge expand | 关系型 query |
| **Lost in middle** | 中部内容被 LLM 忽视 | Long context 通用问题 |
| **Self-RAG** | LLM 决定 retrieve / 不 retrieve / retrieve N 次 | Adaptive 触发 |
| **Prefix cache** | Anthropic 5min / Gemini 1h, cache hit ~10% 价 | 长 prefix reuse |

### 🎯 6 个核心 sub-topic Framework

**Framework T2.1**: Hybrid Search
- When: 任何 production retrieval (default)
- Algorithm: Dense + BM25 并行 asyncio.gather → RRF k=60 → cross-encoder rerank top-50→10
- Trade-off: +50-80ms latency, +8-12% recall
- Tools: Qdrant + OpenSearch + bge-reranker-v2-m3

**Framework T2.2**: Chunking Decision
- When: 文档接入 pipeline
- Algorithm: by doc type → fixed/recursive/heading/late/AST; size 512 + overlap 64 default
- Trade-off: 越结构化 chunker 准但 indexing 慢
- Tools: LlamaParse, unstructured, tree-sitter, jina-embeddings-v3

**Framework T2.3**: Context Window Mgmt
- When: Multi-turn agent / long session
- Algorithm: sliding + summarize + hierarchical 4-tier + RAG-on-history
- Trade-off: aggressive compress 失细节, lazy compress 爆 budget
- Tools: LangChain ConversationSummaryBufferMemory, MemGPT, LlamaIndex memory

**Framework T2.4**: Tool Output → Prompt
- When: Tool result > 1K token / 含 PII / untrusted source
- Algorithm: schema validate → truncate by intent → XML wrap trust → provenance + row_id
- Trade-off: 多层包装增 token, 但 inject defense + 可 cite
- Tools: presidio, pydantic schema, XML namespace

**Framework T2.5**: Reranking
- When: Recall 已够 (top-50+), precision 不足
- Algorithm: cascade bi → bge-base → bge-large/Cohere → optional LLM-judge
- Trade-off: +60-200ms, +8-15% NDCG; cache 30-40% hit 抵消
- Tools: bge-reranker-v2-m3, Cohere rerank-3, mxbai-rerank, JaColBERT

**Framework T2.6**: Long-context vs RAG
- When: 大 corpus + cost / 多 hop / 多租户 决策
- Algorithm: 决策树 by corpus size × cost × multi-hop × freshness
- Trade-off: long-ctx 简单贵, RAG 复杂便宜, hybrid 折中
- Tools: Gemini 3 Pro 2M, Claude 200K, Anthropic prompt cache

### 🌳 关键决策树 (ASCII)

```
Q: corpus size?
├── < 200K, static, low-vol  → Long-context + prefix cache ⭐
├── < 2M, multi-tenant       → Hybrid (RAG narrow → long-ctx)
├── 200K-2M, single tenant   → Gemini 3 Pro 2M direct
└── > 2M                     → Pure RAG
       ├── Latency tight     → Dense only
       ├── Quality top       → Hybrid + Rerank
       └── Multi-tenant      → Per-tenant shard

Q: chunking strategy?
├── Pure prose       → Recursive 512+64 ⭐
├── Markdown / HTML  → Heading-aware
├── PDF complex      → LlamaParse + doc-structure
├── Code             → tree-sitter function-level
├── Chat logs        → Turn-aware 3-5 turn
└── Long-range ctx   → Late chunking (Jina v3)
```

### ⚙️ Part 2 五个深度框架速查

**Framework 1: 7-step Pipeline (Step 1-7)**
- Step 1 Query Understanding: rewrite + pronoun + multi-query + HyDE
- Step 2 Routing: skip / SQL / dense / sparse / graph / API
- Step 3 Multi-retrieval: dense ∥ BM25 ∥ KG ∥ tool, asyncio.gather
- Step 4 Fusion + Rerank: RRF k=60 → cross-encoder cascade
- Step 5 Assembly: token budget (40 history / 60 retrieved); Lost-in-middle defense
- Step 6 Generation: cite [doc-id]; system reminder ground-only
- Step 7 Post-eval: faithfulness LLM judge, thumbs, slice metrics
- Tools: Phoenix, LangSmith, Langfuse

**Framework 2: Chunking decision tree**
- 5 strategies: fixed / recursive / doc-structure / semantic / late
- Recall: 65% → 72% → 78-85% → 80-87% → 85-92%
- 实战 default: Recursive 512+64; Quality 上限: Late chunking

**Framework 3: 5 retrieval methods 量化对比**
- Dense: 75-85% recall, 10ms
- BM25: 60-75%, 5ms
- Hybrid: 82-90%, 12ms ⭐
- + Rerank: 90-97%, +60ms
- ColBERT: 92-98%, 30ms, 10x storage

**Framework 4: Long-ctx vs RAG cost math**
- Pure long-ctx (Gemini 3 Pro 500K corpus): $1/q; with cache $0.10
- Pure RAG: $0.011/q
- Hybrid: $0.25/q (RAG narrow → long-ctx within)
- 100 q/day breakeven: long-ctx + cache OK; 100K q/day: RAG wins

**Framework 5: Production gotcha map**
- 12 gotchas: drift / chunk-cut / BM25-stopword / PDF / multilingual / cache / cross-tenant / lost-middle / hallucinate-cite / vector-scale / rate-limit / chunk-too-long
- 全部需在 design 时打补丁

### 🔥 Production gotchas (top 15)

1. Embedding model drift on re-index → versioned blue/green migration
2. Chunk cuts entity (e.g., 订单号一半) → overlap 64 + parent doc ref
3. BM25 stopword 过 ("how to" 被砍) → custom stopword per domain
4. PDF parse 丢表格 → LlamaParse / Azure Document Intelligence
5. Multilingual mix → gemini-embedding-001 / voyage-multilingual-3
6. Stale cache (doc 更新但 cache 还在) → doc-version-aware cache key
7. Cross-tenant leak → 必须 retrieval-time filter, 不能 post-rank filter
8. Lost-in-middle (中部 30-40% gap) → 顺序 system → history → retrieved → query
9. Hallucinated citation [doc-99] 不存在 → regex post-validate, retry
10. Vector DB 容量爆 (10M × 1536 × 4B = 60GB+) → int8 / binary quantization
11. Embedding rate limit (1M doc OpenAI 限流) → batch 1-2K + exp retry
12. Retrieved chunk 太长占 prompt → truncate + per-chunk summarize
13. Prompt injection in retrieved → XML wrap trust="untrusted" + system reminder
14. Multi-tenant index 共享 → tenant_id 强制 metadata filter
15. Reranker 全量上 (top-1000) → cascade narrow first 才合理

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Hybrid Search | BNPL chatbot | Order# 类查询 dense miss 22%, +BM25 hybrid+RRF 升 89%, +rerank 92% |
| Chunking | BNPL FAQ Confluence | Fixed-512 → heading-aware, recall 72→87%, 表格 chunk type 标 |
| Context Mgmt | Voice agent 7 markets | 10-20 turn 20K+ tok, hierarchical 4-tier + RAG-on-history, token 减半 |
| Tool Output | ConvFinQA 5 calc tools | XML wrap calc result + system reminder "use exact", hallucinate -40% |
| Reranking | BNPL chatbot A/B | hybrid vs hybrid+bge-rerank, faithfulness +12%, thumbs +15%, +60ms hide in stream |
| Long-ctx vs RAG | ConvFinQA 多财报 | Per-customer RAG top-3 → Claude 200K, quality + multi-tenant |
| Agent Platform | Internal | Tool result schema registry + provenance + per-tenant quota |
| Indonesia refund | TikTok PayLater | Refund tier policy doc chunk + heading-aware, slice recall +15pp |

### 🎤 面试现场 quotables (top 8)

> "RAG isn't embed-and-query — it's a 7-step pipeline where each step is a design knob."

> "I picked hybrid + RRF over pure dense because users queried order numbers, and dense missed 22% of those."

> "Reranker only earns its 60ms when first-stage recall is already at top-50 and precision is the bottleneck."

> "Lost-in-middle isn't a 2022 paper artifact — Gemini 3 Pro at 2M still shows 30-40% mid-position recall gap."

> "On ConvFinQA we initially tried long-context, but multi-tenancy forced us to RAG-narrow → long-ctx hybrid."

> "Prefix caching changes the long-context math — Anthropic 5-min cache cuts repeat-prefix cost 10x."

> "Citation hallucination is real: 8% of LLM answers cited [doc-X] that didn't exist. We regex post-validate."

> "On chunking, the right answer is 'depends on doc type' — recursive for prose, heading-aware for markdown, AST for code, late chunking for long-range context."

### 🚨 红线 (top 10 anti-patterns)

1. "RAG = vector DB + cosine top-K" (2022 view)
2. Always rerank (60ms cost without justification)
3. "Long-context killed RAG" (cost / multi-tenant / freshness)
4. Larger chunk = better (dilution destroys precision)
5. No cost math in answer (FDE 必扣分)
6. No multi-tenant filter (cross-tenant leak)
7. Post-rank metadata filter (loses top-k)
8. Pure dense for SKU / 编号 / 人名 (BM25 必须并)
9. No eval set (sweep without ground truth = 玄学)
10. Ignore Lost-in-middle (mid-context gap real even in 2M)

### 🛠️ Tool zoo (2026)

| 类别 | Tool | 一句话 |
|---|---|---|
| Vector DB | Qdrant, Pinecone, Weaviate, Milvus, pgvector, FAISS | Qdrant 自部署首选, Pinecone SaaS |
| Sparse / BM25 | OpenSearch, Elasticsearch, Vespa, Lucene | OpenSearch 开源默认 |
| Embedding | gemini-embedding-001, text-embedding-3, bge-large, voyage-3 | Gemini 多语好, bge 自部署 |
| Reranker | bge-reranker-v2-m3, Cohere rerank-3, mxbai-rerank, JaColBERT | bge multilingual free 起步 |
| PDF parse | LlamaParse, unstructured, pymupdf, Azure Doc Intelligence | LlamaParse 表格强 |
| Code AST | tree-sitter | 必备 |
| PII | presidio (Microsoft) | 自实现 mask 函数兜底 |
| Tracing | Phoenix (Arize), LangSmith, Langfuse, OpenTelemetry | Phoenix 开源 |
| Prompt cache | Anthropic 5min, Gemini 1h, OpenAI 5min | 90% off cached input |
| Frameworks | LangChain, LlamaIndex, Haystack, DSPy | DSPy 程序化 prompt opt |
| Eval | BEIR, MTEB, Ragas, Phoenix eval | Ragas faithfulness/context-recall |

### 📊 Mini cost calculator (2026)

```
Per-query cost:
  cost = (input_tok × in_price) + (output_tok × out_price)
  
  Gemini 3 Pro:    in $2 (≤200K) / $4 (>200K) / out $12 per 1M
  Gemini 3 Flash:  in $0.50 / out $3
  Claude Opus 4.7: in $5 / out $25
  Claude Sonnet 4.6: in $3 / out $15
  Claude Haiku 4.5: in $1 / out $5
  GPT-5.5:         in $5 / out $30

Prefix cache:
  write surcharge 1.25-2x in price
  hit 0.10x in price
  Anthropic TTL 5min, Gemini 1h

Embedding:
  gemini-embedding-001: $0.025 / 1M token
  text-embedding-3-large: $0.13 / 1M
  bge-large self-host: GPU $ amortized

Vector DB (Pinecone serverless):
  storage $0.33 / GB / month
  query $0.40 / 1M ops
```

### 🎬 45-min answer rhythm (T2 通用)

```
0-5    Clarify: corpus / doc type / tenancy / freshness / SLA / QPS
5-10   Mental model: 7-step pipeline 画图 + "RAG ≠ vector DB"
10-25  Deep-dive 1 sub-topic (面试官 zoom-in) + Pattern A/B/C/D/E
25-35  Tradeoffs + cost math (Section 8 cost table)
35-42  2026 trends: Contextual Retrieval / Late chunking / GraphRAG / prompt cache
42-45  简历 quote (BNPL / Voice agent / ConvFinQA / Indonesia refund)
```

### 🔑 7-step pipeline mnemonic

```
Q  Query understanding    (rewrite / multi-q / HyDE / decompose)
R  Routing                (skip / SQL / dense / sparse / KG / API)
M  Multi-source retrieve  (parallel asyncio.gather)
F  Fusion + rerank        (RRF k=60 → cross-encoder cascade)
A  Assembly               (token budget + Lost-in-middle defense)
G  Generation             (cite chunk_id + system reminder ground-only)
P  Post-eval              (faithfulness / thumbs / slice / regression)
```
```
