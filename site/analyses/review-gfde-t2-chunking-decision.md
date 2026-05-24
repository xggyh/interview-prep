## T2.2 · chunking decision — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](gfde-t2-chunking-decision.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t2-chunking-decision.html`](gfde-t2-chunking-decision.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"Indexing 10K technical PDFs for RAG — how do you chunk?"** 或 **"Recall drops 20% when chunk size changes 512→1024 — why?"**, 我按这 8 层回答, 不跳序.

### 📐 Chunking Decision Tree — 8 层结构

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 |
|---|---|---|---|---|
| 1 | Clarify + Naive 灾难 | 0-5 min | Doc 类型 (PDF / code / chat log / table-heavy)? Total volume + page distribution? Query 形态 (具体 vs 概念)? Refresh cadence? **然后 demo failure**: 512 fixed chunk 切到表格中间 → "Min: -20°C Max: 60°C" chunk 没有 device 上下文 → LLM 答不出是哪个 device | "5 clarifications first. And let me show the naive failure — fixed-512 chunking on a PDF datasheet splits a temperature table mid-row; the chunk loses device context entirely." |
| 2 | 7 种 failure mode | 5-10 min | (1) 切表格 (2) 切代码 function (3) 切句中 (4) 丢 heading 路径 (5) chunk 跨多 topic (单 embedding 表示多主题, recall 低) (6) chunk 太小 (答案跨 2 chunk 单 retrieve 漏) (7) chunk 太大 (信息密度低噪声多) | "Before strategy — 7 distinct failure modes. Each strategy targets specific ones. Let me enumerate so we agree on what we're optimizing." |
| 3 | 8 种 chunking 策略表 | 10-18 min | Fixed-size + overlap (baseline) / Sentence-aware / Paragraph-section / **Heading-aware recursive (production default)** / Semantic (topic-shift) / AST-based (code) / **Late chunking (Jina v3 / Cohere v4)** / Hierarchical parent-doc. 每个标 quality / complexity / 何时用 | "8 strategies on the menu. Production default is heading-aware recursive with table/code atomic fallback. Late chunking is the 2024-25 frontier." |
| 4 | Decision tree per doc type | 18-25 min | Q1 有 heading 层级? → heading-aware recursive. Q2 对话/log? → speaker-turn / time-window. Q3 代码? → AST. Q4 表格密集? → table-atomic + surrounding text. Q5 极短? → whole-doc. Q6 长 context embed 可用? → late chunking. Default → fixed-500 + overlap-50 + sentence-aware | "Here's my decision tree. 6 questions, deterministic strategy choice. Let me walk through each branch with examples." |
| 5 | Multi-modal 处理 | 25-31 min | Table → atomic chunk, Markdown serialize, `is_table=true caption=... headers=[...]`. Code → atomic, lang annotation. Figure → caption chunk + image blob (multimodal RAG). Formula → LaTeX + 渲染描述. List → atomic if 短, item-boundary split if 长 | "Multi-modal is non-obvious. Tables must be atomic with Markdown serialize; code never split mid-function; formulas keep LaTeX. Each gets explicit metadata for the retriever." |
| 6 | Size + overlap 的数学 | 31-37 min | Embedding model max context: 512 (legacy) / 8192 (modern) / 32K (gemini-embed). Chunk size sweet spot: prose 300-500 tok / table-heavy doc 800-1000 / code function-level. Overlap 10-20%: borderline 句子不丢, 但 storage cost +10-20%, dedup retrieve 后处理 | "Size tuning math — embedding model max sets the cap. Sweet spots vary by doc type. Overlap rationale is borderline-sentence recovery, cost is +10-20% storage and dedup overhead." |
| 7 | Late chunking 深度 | 37-43 min | 经典先 chunk 再 embed → 每 chunk 单独看不到 cross-chunk context. Late chunking: 先 embed 整 doc 拿 token-level embeddings (用 Jina v3 8K context / Cohere v4), pool 成 chunk-level. 保留 long-range context. Recall +5-10% on cross-section query | "Late chunking is the 2024-25 advance. Instead of chunk-then-embed, you embed-then-pool. Long-range context preserved. Recall +5-10% on cross-section queries. Tradeoff is requires long-context embed model." |
| 8 | Eval methodology + connect | 43-50 min | Sweep grid: chunk_size × overlap × strategy. Per-doc-type slice eval (PDF vs code vs prose). Metric: recall@10 + NDCG. **Bug story**: BNPL chatbot 切到 policy table 中间 → recall 12% → 改 table-atomic 涨到 27%. ConvFinQA 数字表格用 row-aware chunking, multi-hop reasoning recall +18% | "I sweep chunk_size × overlap × strategy as a grid, slice eval by doc type. Resume — BNPL chatbot policy table fix gave 12→27%, ConvFinQA table-row chunking +18% on multi-hop." |

### 🎯 为啥按这个序

**Naive failure (Layer 1) 必须最先讲** — 不画灾难, 面试官不知道为啥 fixed-512 不行. Failure mode 7 类 (Layer 2) 是 building block — 后面策略选择全是 "对治哪些 failure mode". Strategy table (3) 必须在 decision tree (4) 之前 — 不知道 menu 有啥就无法选. Multi-modal (5) 单列因为它是 production 重头戏 (表格 / 代码 / 公式 没人讲就拉胯). Size math (6) 是数字层细节. Late chunking (7) 是 2024-25 frontier, 讲出来面试官知道你 read latest papers. Eval methodology (8) 必须有 — 没 ablation 就是 toy demo.

### 🔥 哪一层最容易被追问 deeper

- **Layer 4 (decision tree)**: "PDF datasheet 怎么 parse heading?" → 准备 LlamaParse / Unstructured / PyMuPDF 工具链 + 提取 TOC 树. "代码怎么 AST?" → tree-sitter / tree-parser 多语言支持.
- **Layer 7 (late chunking)**: "Jina v3 怎么实现?" → 准备 long-context bi-encoder + mean-pooling over token range. Paper: Günther et al 2024 "Late Chunking".
- **Layer 6 (size math)**: "为啥 512 切到 1024 recall drop 20%?" → 准备 "chunk 大 = 单 embedding 多 topic = noise; chunk 小 = 答案被切碎. Sweet spot 数据集相关, 必须 sweep".

### ⏱ 时间压缩版 (30 min round)

- Layer 1 (clarify + 灾难) 4 min — 必讲
- Layer 2 (failure mode) 2 min, 只列 3 个关键 (切表格 / 丢 heading / 跨 topic)
- Layer 3 (strategy table) 4 min, 只重点讲 heading-aware + late chunking
- Layer 4 (decision tree) 4 min
- Layer 5 (multi-modal) 4 min — 必讲, 区分 production
- Layer 6 (size math) 3 min
- Layer 7 (late chunking) 跳过 / 1 min, 一句带过
- Layer 8 (eval + connect) 4 min — 必讲 ablation

### 🆘 卡壳兜底 (针对这题)

- 忘了 late chunking 具体 → 退回讲「**核心 idea: 先 embed 整 doc 拿 token-level, 再按 chunk boundary pool. 保留 long-range context. 需要 long-context embed 模型支持**」
- 被追问 chunk size 具体值 → 退回讲「**Domain-dependent, 必须 sweep. Empirical: prose 300-500, code function-level, table atomic. 没有 one-size-fits-all**」
- 忘了 AST tool → 退回讲「**tree-sitter / Pygments / language-specific parser. 核心是按 function/class boundary 切, 不按 token count**」
- 被追问 hierarchical chunking → 退回讲「**Small chunk for retrieval, large parent chunk for context. Retrieve small, return parent. Trade off recall vs context window**」
- 忘了 overlap 推荐值 → 退回讲「**10-20% overlap. 太多浪费 storage + retrieve 重复, 太少 borderline 信息丢**」

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

Chunking = **doc-type → strategy + size + overlap + metadata + atomic-elements**; 一刀切 fixed-512 是 toy demo, 生产是 **heading-aware recursive + table/code 原子 + 富 metadata + delta reindex + sweep eval**.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| **Chunk** | RAG 最小检索单元, 1 doc → N chunk → N 个 embedding | 索引时 |
| **Chunk size** | LLM tokenizer token 数 (不是字符) | 设 512 / 768 / 1024 |
| **Overlap** | 相邻 chunk 重叠 token | 10-15% 防 boundary 切碎 |
| **Late chunking** | 先 embed 整 doc, 再 pool chunk-level | Jina v3 / Cohere v4 |
| **Heading path** | "/Ch3/3.2/逾期费率" 拼到 embed text | 提升 +5-15% recall |
| **Hierarchical / Parent-doc** | 子 chunk 检索, 父 doc 返回 LLM | Wide-context query |
| **Semantic chunking** | 用 embedding 找 topic shift 切点 | 长 prose 无结构 |
| **AST chunking** | tree-sitter 解析 → function-level | Code |
| **Atomic chunk** | 不可再切的单元 (table / code / formula) | 表格 / 代码 / 公式 |
| **Delta indexing** | 仅更新变化 chunk (hash diff) | 增量更新 |
| **Versioning + 灰度** | v_old / v_new 双写 + traffic split | 模型升级 / 策略切换 |
| **Hot + warm index** | 24h 内 in-mem, 其余 async batch | 实时性 + 成本 |
| **Quality score** | per-chunk view_count / feedback / canonical | Rerank boost / dedup |
| **PII level** | 0-5 sensitivity tag | 输出 mask / 角色过滤 |
| **Freshness decay** | exp(-Δt / λ) 加权 | 时效内容 (news / ticket) |

### 🎯 6 个核心 chunking strategy framework

**Strategy 1**: Fixed-size + overlap (baseline)
- When: 无结构 prose, prototype
- Algorithm: split by token count, 512 + 64 overlap
- Trade-off: 简单, 切碎语义, recall 65-72%
- Tools: LangChain RecursiveCharacterTextSplitter

**Strategy 2**: Sentence-aware
- When: 有完整句子的 prose
- Algorithm: NLTK / spaCy sentence split → group 5-10 sentences
- Trade-off: 不切句中, 多 chunk size 不均
- Tools: spaCy, NLTK, langdetect

**Strategy 3**: Heading-aware recursive ⭐ default
- When: Markdown / HTML / PDF 有 heading
- Algorithm: parse tree → if section fits → 1 chunk; else recurse; embed 含 heading_path
- Trade-off: recall 78-85%, 实现 ★★★
- Tools: unstructured, LlamaParse, pymupdf, Azure Document Intelligence

**Strategy 4**: Semantic chunking
- When: 长 prose 无明显 break
- Algorithm: sentence embed → consecutive distance → split at top-K change points
- Trade-off: recall 80-87%, 慢 (embedding-based 切点)
- Tools: LlamaIndex SemanticSplitterNodeParser

**Strategy 5**: Late chunking ⭐ 2026 hot
- When: 长 corpus + 小 chunk 需保留长程依赖
- Algorithm: 1 forward 整 doc (8K-32K tok ctx model) → token embedding → pool chunk-level
- Trade-off: recall 85-92%, embedding 模型限制
- Tools: jina-embeddings-v3, voyage-3, cohere-v4

**Strategy 6**: Hierarchical / Parent-doc
- When: 检小 chunk, 返回宽 context
- Algorithm: small chunk index (search), parent doc retrieval (LLM input)
- Trade-off: 存储 2x, quality top
- Tools: LlamaIndex AutoMergingRetriever

### 🌳 关键决策树 (ASCII)

```
Q: 你的 doc 是什么 type?
├── Pure prose (blog/FAQ)        → Recursive 512+64 ⭐
├── Markdown / HTML 有 heading   → Heading-aware recursive
├── PDF (含表格/公式/代码)        → LlamaParse + heading-aware + atomic table/code
├── Code (monorepo)              → tree-sitter AST function-level
├── Chat / Ticket logs           → Turn-aware 3-5 turn (含 timestamp)
├── 法律 / 合同                  → Clause-level
├── 学术 paper                   → Section-aware 800 tok
├── 数据手册 / 财报 (表格密集)    → Table atomic + 周围 text chunk
└── 长 prose 无结构 + 长上下文需求 → Late chunking (Jina v3)

Q: chunk size?
├── 128 tok   → 高精度低召回, 实验
├── 256 tok   → FAQ / 短 entry
├── 512 tok ⭐ → default
├── 768 tok   → 略宽上下文
├── 1024 tok  → context 充分但 dilution
└── overlap = 10-15% of chunk size, code 用 0
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: Chunking Strategy Taxonomy**
- 6 类: fixed / sentence / heading-recursive ⭐ / semantic / late / hierarchical
- Decision table by doc type: FAQ→atomic, Policy→heading, Ticket→turn, Code→AST, Paper→section
- Top 3 gotchas: fixed 通吃 / 没 overlap / chunk size 一刀切
- Tools: LlamaParse, unstructured, tree-sitter, jina-embeddings-v3

**Problem 2: Multi-modal Handling**
- Tables: atomic + Markdown serialize ("| col1 | col2 |") + caption embed; Camelot/Tabula/Textract 解析
- Code: atomic + tree-sitter + lang annotation + symbol metadata
- Formulas: LaTeX + textual description ("二次方程 x² = ...")
- Figures: caption embed + alt text + 可选 vision multi-modal
- Lists: 短 atomic, 长 split at item boundary
- Top 3 gotchas: 表格切半 / 代码切函数 / 公式当 garbage text
- Tools: Camelot, Tabula, AWS Textract, tree-sitter, CLIP for vision

**Problem 3: Metadata Enrichment**
- Schema: identity (chunk_id, doc_id, idx) + source (title, type, system) + structure (heading_path, page, is_table/code/figure) + time (created, updated, effective) + access (tenant_id, visibility, acl, pii_level) + quality (score, view_count, feedback, is_canonical) + tags (tags, lang, product)
- Embed text = `' > '.join(heading_path) + '\n\n' + chunk.text`
- Freshness: `score *= exp(-Δt / λ)` λ=30 days news, λ=365 policy
- Perms: 必须 retrieval-time filter (Qdrant query_filter)
- PII: presidio scan, tag pii_level 0-5
- Top 3 gotchas: 没 heading 在 embed text / post-rank perms / 没 PII tag
- Tools: presidio, Qdrant payload index, pgvector metadata

**Problem 4: Index Update Strategy**
- Full reindex 不可行 (10K doc × 5min embed = 35 days)
- Delta: chunk_id = `hash(doc_id + heading_path + chunk_index)`, diff old vs new, to_add/update/delete
- Versioning + 灰度: 双写 v_old + v_new, traffic split by user_id hash, eval new >= old → cutover
- Async pipeline: Kafka → embed worker pool → bulk upsert
- Hot + warm: hot (24h) in-mem 5min refresh, warm async daily; RRF merge
- Cost (10K doc): full $50 + 5h; delta $0.5 + 5min
- Top 3 gotchas: 没 deterministic chunk_id / 同步 reindex 阻塞 / 没 blue-green
- Tools: Kafka, Qdrant snapshots, embedding batch worker

**Problem 5: Eval Methodology (Sweep)**
- Eval set: 200 human + 1000 LLM synthetic calibrated
- Sweep: chunk_size × overlap × strategy × embedding_model = 5×3×6×3 = 270 combos
- Slice: by query type (table / how-to / code / multi-hop)
- Per-source-type 不同策略 (FAQ atomic, Policy heading, Code AST)
- CI / regression: eval set 每 commit 跑, NDCG@10 阈值 < -2pp 阻塞 merge
- Production observability: per-chunker recall, chunk size distribution, retrieval-empty rate
- Top 3 gotchas: 一组参数通吃 / 只看 mean (不 slice) / 没 CI
- Tools: BEIR, MTEB, Phoenix, LangSmith, custom domain set

### 🔥 Production gotchas (top 15)

1. Fixed-size 通吃所有 doc type → 必须 per-doc-type 策略
2. 没 overlap → boundary 信息丢
3. 切表格 / 切代码 → atomic 强制
4. 没 heading_path 进 embed text → -5-15% recall
5. 一刀切 chunk size 512 → FAQ 100 / policy 800 / code AST
6. 没 chunk_id deterministic → 每次 reindex 全变, 缓存失效
7. Full reindex on update → 必须 delta
8. 没 PII tag → 用户拿到 SSN
9. Cross-tenant 共享 chunk → 必须 tenant_id metadata + filter
10. Embedding model upgrade → 必须 blue-green + 双索引
11. PDF parse 丢表格 → LlamaParse / Azure Document Intelligence
12. Multilingual mix → 多语 embedding (gemini-embedding-001)
13. Hot index 缺 → 新 ticket 24h 才搜
14. Random chunk_id → 无法 delta diff
15. 没 freshness decay → 老 news / outdated policy 排前面

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Heading-aware | BNPL Confluence FAQ | Fixed-512 → markdown heading-aware, recall 72%→87%, 表格 atomic 标 |
| Atomic table | BNPL policy PDF | 利率表格 atomic + caption embed, 表格 query NDCG +12pp |
| Multi-modal | TikTok PayLater 政策 | 文字 + 表格 + footnote 联合 chunk, recall +9pp |
| Metadata schema | BNPL 7 markets | tenant_id + heading_path + freshness + PII level, prod 检索零跨租 |
| Delta indexing | Internal Agent Plt | chunk_id=hash(doc+heading+idx), 10K doc 5min 更新 vs 全量 5h |
| Hot + warm | BNPL ticket index | hot 24h in-mem 5min refresh, warm async daily, p99 < 200ms |
| Late chunking | ConvFinQA | Jina v3 全 doc embed, 财报长程依赖, recall +8pp |
| Per-source chunker | BNPL | FAQ atomic + policy heading + ticket turn-aware, slice recall +15pp |

### 🎤 面试现场 quotables (top 8)

> "Chunking isn't 'split every 512 tokens' — it's a decision tree on doc type, with atomic protection for tables, code, formulas."

> "I always embed the heading path into the chunk text: '/Ch3/3.2/Late fee' + body. That's free +5-15% recall."

> "On BNPL we have FAQ (atomic 1-entry), policy (heading 600 tok), ticket (turn-aware 300 tok), code (tree-sitter AST). One strategy doesn't fit all."

> "Late chunking is the 2024 breakthrough: embed the whole doc with Jina v3, then pool chunk-level. Long-range context for free."

> "Delta indexing is mandatory — full reindex on 10K docs is 5 hours. With deterministic chunk_id = hash(doc + heading + idx), I diff and only touch changed chunks."

> "Tables must be atomic with Markdown serialization. Cut a table mid-row and your embedding is junk."

> "Metadata is half the win: tenant_id, heading_path, pii_level, freshness, quality_score. Each unlocks a downstream feature — filter, rerank, mask, decay."

> "PDF parsing is the silent killer. unstructured loses tables 30% of the time; we use LlamaParse + Azure Document Intelligence + Camelot for tables."

### 🚨 红线 (top 10 anti-patterns)

1. Fixed-size 通吃所有 doc type
2. No overlap (boundary 切碎)
3. Cut tables / code mid-element
4. No metadata (heading / tenant / pii / freshness 全缺)
5. All chunks same size (FAQ 应该小, policy 应该大)
6. No eval set / no sweep
7. Full reindex on every update
8. Random chunk IDs (无法 delta)
9. No PII tagging (合规风险)
10. No hot + warm index (新 doc 24h 不可搜)

### 🛠️ Tool zoo (2026)

| 类别 | Tool | 一句话 |
|---|---|---|
| PDF parse | LlamaParse, unstructured, pymupdf, Azure Doc Intelligence, Adobe Extract | LlamaParse 表格 ⭐ |
| Tables | Camelot, Tabula, AWS Textract | Textract 高准 |
| Code AST | tree-sitter | 必备 |
| PII | presidio (Microsoft) | 自实现 mask 兜底 |
| Embedding | gemini-embedding-001, text-embedding-3-large, bge-large, jina-embeddings-v3 | jina v3 late chunking |
| Vector DB | Qdrant, Pinecone, Weaviate, Milvus, pgvector | Qdrant payload index 富 metadata |
| Sparse | OpenSearch, Elasticsearch | 同 chunk 同步 |
| Chunkers | LangChain RecursiveCharacterTextSplitter, LlamaIndex SemanticSplitterNodeParser | 起步 |
| Late chunking | jina-embeddings-v3, voyage-3, cohere-v4 | 2026 hot |
| Streaming | Kafka + delta indexing worker | 增量 |

### 📊 Chunk size + overlap 速查

```
Size 128 tok    → 高 precision 低 recall, 实验
Size 256 tok    → FAQ / 短 entry
Size 512 tok ⭐ → default, 适大多 prose
Size 768 tok    → 略宽上下文
Size 1024 tok   → context 充分但 dilution

Overlap 默认 10-15% of chunk size:
  512 → 64 overlap
  256 → 25-40 overlap
  Code → 0 overlap (每 chunk 完整 function)
  Dense fact → 0 overlap
```

### 💻 一段最小 prod-ready chunker

```python
def chunk_doc(doc):
    if doc.type == "code":
        return chunk_ast(doc)  # tree-sitter function-level
    
    if doc.type in ("md", "html") and doc.has_headings:
        chunks = chunk_by_heading(doc, max_tok=512)
    elif doc.type == "pdf":
        elements = llamaparse.parse(doc)
        chunks = []
        for e in elements:
            if e.is_table: chunks.append(atomic_chunk(e, type="table"))
            elif e.is_code: chunks.append(atomic_chunk(e, type="code"))
            else: chunks.extend(chunk_recursive(e, max_tok=512, overlap=64))
    else:
        chunks = chunk_recursive(doc, max_tok=512, overlap=64)
    
    # Enrich + embed
    for i, c in enumerate(chunks):
        c.id = f"{doc.id}#{hash(c.heading_path + str(i))}"
        c.metadata = build_metadata(doc, c, i)  # heading_path, tenant_id, pii_level, ...
        c.embed_text = " > ".join(c.heading_path) + "\n\n" + c.text
    return chunks
```

### 🎬 45-min answer rhythm

```
0-5    Clarify: doc type / size / heading? / table-heavy? / multi-lingual? / tenant?
5-10   Mental model: chunking ≠ "split every 512", decision tree by type
10-15  Strategy 1-6 + atomic for tables/code
15-25  Metadata schema (heading_path / tenant / freshness / pii) + perms filter
25-35  Delta indexing + versioning + hot/warm/cold + cost math
35-40  Eval (sweep + slice + CI regression)
40-45  简历 quote (BNPL FAQ 72%→87% via heading-aware)
```

### 🔑 Chunking strategy mnemonic

```
F  Fixed-size + overlap        (baseline)
S  Sentence-aware              (略好)
H  Heading-aware recursive ⭐   (default for structured)
M  Semantic (topic shift)      (no structure prose)
L  Late chunking ⭐             (jina v3, 2026 hot)
P  Parent-doc / hierarchical   (wide context)
A  AST (code)                  (tree-sitter)
T  Turn-aware (chat / ticket)  (timestamp metadata)
```
```
