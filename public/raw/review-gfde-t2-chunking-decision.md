## T2.2 · chunking decision — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/gfde-t2-chunking-decision.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t2-chunking-decision.html`](questions/gfde-t2-chunking-decision.html)

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
