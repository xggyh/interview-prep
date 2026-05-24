## AI Deep Dive #1 · Why That Chunking — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/why-chunking-strategy.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`why-chunking-strategy.html`](questions/why-chunking-strategy.html)

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

> **Chunking 不是「切 doc」, 是「让 retrieval + generation 联合最优的设计决策」**. 5 个决策维度: corpus 特征 / query pattern / retrieval method / embedding context limit / latency budget. Production 默认: structure-aware 300-500t + 30% overlap + hybrid (dense 0.7 + BM25 0.3 RRF) + bge-reranker-v2 top-50→10 + metadata (heading_path / doc_id / tenant / freshness / ACL). **Eval-driven 不是 intuition-driven**.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Chunking | 长文档切片段独立 embed | RAG 第一步 |
| Fixed-size token | 每 N tokens 一切 (e.g., 512) | baseline only |
| Recursive | \n\n → \n → . 递归 split | LangChain 默认 safe |
| Semantic chunking | embed 邻句, 相似度变化点切 | 主题混杂长文 |
| Structure-aware | 按 markdown header / HTML DOM 切 | ⭐ 结构化文档 |
| Hierarchical (parent-child) | retrieve small, send large parent to LLM | 长文回答需 large context |
| Late chunking | 先 embed 整 doc, 再切 (Jina v3) | 上下文依赖强 |
| Dense | text-embedding 向量检索 | 语义近义 |
| BM25 (Sparse) | 关键词 / TF-IDF | 精确术语 / ID |
| Hybrid | dense + BM25 加权 | ⭐ production 默认 |
| Late interaction | ColBERT, token-level | 5x storage 高 precision |
| Rerank | cross-encoder 二次精排 | bge-reranker-v2-m3 |
| RRF | Reciprocal Rank Fusion | hybrid 融合方法 |
| HNSW | Hierarchical Navigable Small World | 向量索引 |
| ANN | Approximate Nearest Neighbor | 向量检索 |
| Metadata | heading_path / acl / freshness / lang | chunk 自带身份证 |
| LLM-as-judge | 用更强 LLM 评 retrieval | answer correctness eval |
| Cohen's kappa | judge 校准, > 0.6 acceptable | LLM judge 不能裸用 |

### 🎯 5 个核心 framework

**Framework 1**: 6-Strategy Chunking Taxonomy
- When: 任何 RAG 系统初始化
- Algorithm: Fixed-size (baseline) / Recursive (safe default) / Semantic (主题混杂) / Structure-aware (markdown/PDF ⭐) / Hierarchical (parent-child) / Late chunking (Jina v3)
- Trade-off: 速度 vs coherence vs implementation complexity
- Tools: LangChain TextSplitter, llama_index node parsers, Jina-embed-v3 late, semantic-text-splitter

**Framework 2**: 5-Method Retrieval Stack
- When: 配合 chunking 联合设计
- Algorithm:
  - Dense only (BGE-M3 / text-embedding-3-large) for 语义
  - BM25 only (Elasticsearch / Tantivy) for 精确术语 / ID
  - Hybrid (α=0.6-0.8 dense, RRF fusion) ⭐ production 默认
  - ColBERT (5x storage, 极致 precision)
  - + Cross-encoder rerank top-50 → top-10 (bge-reranker-v2-m3, 3-5x latency) ⭐ if budget
- Trade-off: precision vs latency vs storage
- Tools: Pinecone / Weaviate / Qdrant / pgvector, Elasticsearch, Cohere rerank-v3

**Framework 3**: 5 Decision Factors
- When: 选 chunking 时
- Algorithm:
  1. Corpus characteristics (length P50/P99, structure, tables, code, languages)
  2. Query patterns (entity density, multi-hop, ID matching)
  3. Retrieval method (joint design, dense vs hybrid 决定 chunking)
  4. Embedding model context limit (bge-large 512, OpenAI 3-large 8191)
  5. Latency budget (rerank 3-5x latency, budget < 200ms 可能跳)
- Trade-off: 一个 factor 错 = full redesign
- Tools: profile_corpus script (doc_count / length percentile / has_tables / has_code / languages / has_headings)

**Framework 4**: Multi-Modal Chunking
- When: 文档含 tables / code / 公式 / lists / images
- Algorithm:
  - Tables → integral chunk + row chunks + NL description ("Q3 revenue was $1.2B (+8% YoY)")
  - Code → AST-aware (函数/类边界, 保持完整)
  - Formulas → LaTeX → NL + keep original
  - Lists → unit when small, header-replicated when split
  - Images → CLIP embed + caption + surrounding text
- Trade-off: 多 chunker = 系统复杂度, 但单一 chunker 在混合 doc 表现差
- Tools: unstructured.io, llama-parse, pdfplumber, tree-sitter (AST), CLIP / SigLIP

**Framework 5**: 3-Layer Eval Methodology
- When: 证明 "我选的是最优"
- Algorithm:
  - Layer 1 Retrieval (golden set 200-500 queries): recall@10, NDCG@10, MRR
  - Layer 2 Generation: answer correctness via LLM-judge (Gemini 3 Pro / Claude Opus 4.7), Cohen's kappa > 0.6 校准
  - Layer 3 Operational: latency P50/P99, cost per query, ingest throughput
  - Ablation: 9 variants, isolated changes
  - Slice: by query_type / difficulty / language
  - Cost-Quality Pareto front
- Trade-off: 不只看 recall, 看 cost-quality 平衡
- Tools: ragas, trulens, BEIR benchmark, custom golden set, LLM-judge calibration

### 🌳 关键决策树

```
文档类型?
├── 纯文本 / Markdown → Structure-aware (按 H2 切) ⭐
├── PDF 含表格 / 公式 → 分类型 chunk (table integral / code AST / prose paragraph)
├── 代码 → AST-aware (函数/类边界)
├── Wiki / Confluence → Structure-aware + ACL metadata
└── 多语言混杂 → BGE-M3 multilingual + per-language metadata

Query 类型?
├── 含 ID / 缩写 / 错拼 → Hybrid (BM25 抓精确)
├── 纯语义 → Dense
├── 多 hop reasoning → Hierarchical (small retrieve, large parent to LLM)
└── 时间精确 ("Q3 2024") → BM25 + freshness metadata filter

Latency budget?
├── < 200ms → skip rerank, 仅 hybrid
├── 200-500ms → hybrid + rerank top-50→10 ⭐
└── > 500ms OK → ColBERT 全量 precision

Corpus scale?
├── < 100K docs → 任意 setup
├── 1M docs → HNSW + per-tenant sharding
├── 100M docs → distilled embedding (768→256), tiered hot/cold
└── 长 corpus + long-context model? → Hybrid (RAG narrows, Gemini 3 Pro / Claude Opus 4.7 digests)
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: 6-Strategy Taxonomy 实操**
- 核心解法:
  ```python
  # 1. Fixed-size: RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
  # 2. Recursive: 按 \n\n → \n → . 递归
  # 3. Semantic: SemanticChunker, threshold breakpoint
  # 4. Structure-aware: MarkdownHeaderTextSplitter or unstructured.io
  # 5. Hierarchical: ParentDocumentRetriever, child 200t / parent 1500t
  # 6. Late chunking: jina-embeddings-v3 with context-aware embed
  
  Production 默认: structure-aware 300-500t + 30% overlap + metadata enrich
  ```
- Top 3 gotchas: 默认 512 fixed → 句子截断 / 表格当 prose 切 → 信息丢失 / 切完换 embedding → 全部 re-embed
- Tools: LangChain TextSplitters, llama_index node parser, semantic-text-splitter rust

**Problem 2: 5-Decision-Factor**
- 核心解法:
  ```python
  profile = {
      'doc_count': 50000,
      'length_p50_p99': (1200, 8500),  # tokens
      'has_tables': True,
      'has_code': False,
      'languages': {'en': 0.6, 'id': 0.2, 'vi': 0.1, 'th': 0.1},
      'has_headings_pct': 0.85,
      'query_pattern': 'entity_heavy + multi_hop',
      'latency_budget_ms': 400,
      'embed_ctx_limit': 8191,
  }
  → choose: structure-aware + hybrid + rerank
  ```
- Top 3 gotchas: 不 profile 直接 default / ignore latency budget / 忽略 query pattern
- Tools: profile script, Pandas describe, Counter

**Problem 3: Multi-Modal Chunking**
- 核心解法:
  ```
  Tables (financial 10-K):
    Integral chunk (整张表 + 表标题 + 列名 metadata)
    + Row chunks (每行单独 index)
    + NL description ("Q3 revenue $1.2B, +8% YoY")
  
  Code:
    AST-based (tree-sitter)
    Function/Class boundary 保持完整
    Imports + class signature 作为 metadata
  
  Formulas:
    LaTeX original + NL translation
    Both indexed
  
  Lists:
    Small → unit chunk
    Long → header-replicated when split
  
  Images:
    CLIP / SigLIP embed
    Caption text 一同 index
    Surrounding paragraph context
  ```
- Top 3 gotchas: 表格当 prose / 代码乱切 / 公式只存 LaTeX
- Tools: unstructured.io, llama-parse, pdfplumber, tree-sitter, CLIP

**Problem 4: Metadata Enrichment (chunk 身份证)**
- 核心解法:
  ```python
  metadata = {
      'chunk_id': uuid,
      'doc_id': '...',
      'chunk_order': 3,
      'heading_path': ['Chapter 2', 'Refund Policy', 'Timeline'],
      'chunk_type': 'prose' | 'table' | 'code' | 'list',
      'section_level': 2,
      'source_url': '...',
      'created_at': '2026-05-01',
      'updated_at': '2026-05-15',
      'author': '...',
      'acl_list': ['ml_team', 'fde'],  # 硬过滤 pre-search
      'tenant_id': 'acme',  # 硬过滤
      'freshness_score': 0.92,
      'confidence': 0.88,
      'review_status': 'approved',
      'language': 'id',
      'topic_tags': ['refund', 'paylater'],
      'embedding_model_version': 'bge-m3-v1.5',
  }
  ```
- Top 3 gotchas: 没 ACL 硬过滤 (越权检索) / 没 freshness (旧政策被检) / 没 embedding_model_version (model 升级混淆)
- Tools: pgvector with JSONB, Pinecone metadata filter, pre-search WHERE clause

**Problem 5: Eval Methodology (3-Layer)**
- 核心解法:
  ```python
  # Layer 1: Retrieval
  recall_at_10 = num_relevant_in_top10 / num_relevant_total
  ndcg_at_10 = sum(rel_i / log2(i+1)) / ideal_ndcg
  mrr = mean(1/rank_first_relevant)
  
  # Layer 2: Generation
  llm_judge_score = gemini_pro.complete(f"Rate answer correctness 0-10: {ans} vs {gold}")
  kappa = cohen_kappa(human_score, judge_score)  # > 0.6
  
  # Layer 3: Operational
  p50, p99 latency; cost_per_query; ingest_throughput
  
  # Ablation: 9 variants, isolated changes
  # Slice: by query_type / difficulty / language
  # Pareto front: cost vs quality
  ```
- Top 3 gotchas: 只看 recall (忽略 generation correctness) / LLM-judge 不校准 / 没 ablation 不知道哪个 component lift
- Tools: ragas, trulens, BEIR, MS MARCO, custom 200-500 golden, LLM-judge with kappa

### 🔥 Production gotchas (top 15)

1. 默认 512 token 没 overlap → 句子截断 ("7-" / "-14" 分裂)
2. 表格当 prose 切 → 信息丢失
3. 没 metadata → LLM 不知道 chunk 出处
4. 凭 intuition 选 → eval-driven 才 production-grade
5. 切完换 embedding model → 必须 re-embed 全部
6. 没 ACL 硬过滤 → 越权检索, 用户能 enumerate 文档存在性
7. 没 freshness metadata → 旧政策被检 → 答错
8. Hybrid 没 RRF 直接 weighted sum → 分数不可比
9. Rerank 不分 latency budget → P99 爆
10. Hierarchical 没存 parent → retrieve 后无 large context
11. Semantic chunking 全量跑 → 2-3x slow ingest, 1M doc 跑不动
12. Late chunking 不支持的 embed model → 用了等于白用
13. 没 stratify eval → 某 language 退步被掩盖
14. LLM-judge self-preference bias → 用不同 family
15. 没 cost-quality Pareto → 选最高 recall 不一定最 optimal

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Structure-aware FAQ | BNPL 客服 RAG | FAQ Q-A 对切 + lang metadata |
| Multi-modal table | ConvFinQA | 表格 integral + row + NL desc, 数字 BM25 |
| Hierarchical | Voice agent 7 markets 法规 | small retrieve large parent to LLM |
| ACL filter pre-search | Internal Agent Platform | per-team 权限隔离 |
| Hybrid α tuning | BNPL multi-lang | 0.6 dense + 0.4 BM25 ID match |
| Eval methodology | ConvFinQA 9-variant ablation | golden + ablation + slice |
| Cost-quality Pareto | Voice agent | rerank 不是默认开 |
| LLM-as-judge calibration | ConvFinQA | kappa > 0.6 校准 |
| Multi-language BGE-M3 | Voice agent | 7 markets 6 languages |

### 🎤 面试现场 quotables (top 8)

1. "I chose structure-aware over fixed-size because the corpus had 85% headings — fixed would break the semantic boundary"
2. "Hybrid with α=0.7 dense + 0.3 BM25, RRF fusion, because queries had both semantic and entity components"
3. "I'd never pick chunking without first profiling the corpus — length P99, table density, language mix all matter"
4. "ConvFinQA — tables are integral chunks with row-level sub-chunks. Numbers go into BM25 separately, calculator agent verifies"
5. "Hierarchical for legal queries — child chunk retrieves the exact clause, parent gives LLM the section context"
6. "Eval is 3-layer: retrieval (recall@10), generation (LLM judge with kappa > 0.6), operational (P99 latency + cost)"
7. "I'd switch to ColBERT only if precision is critical and storage 5x is OK — for most production, hybrid + rerank wins Pareto"
8. "At 100M scale I'd distill embedding 768 → 256, tiered hot/cold storage, and may skip rerank or distill the rerank model"

### 🚨 红线 (top 10 anti-patterns)

1. 默认 512 fixed 没 overlap
2. 表格当 prose 切
3. 没 metadata
4. 凭 intuition 选不 eval
5. 切完换 embedding model
6. 没 ACL 硬过滤 pre-search
7. Hybrid 没 RRF 直接 weighted sum
8. Hierarchical 没存 parent
9. LLM-judge 不校准 kappa
10. 没 stratify eval, aggregate 掩盖
