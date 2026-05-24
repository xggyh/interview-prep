## 题目

> "You're indexing 10K technical PDFs (each 50-500 pages) for RAG. How do you **chunk** them? Walk through your decision tree and the failure modes of naive approaches."

或追问形态:

> "RAG recall drops 20% when you change chunking from 512 tokens to 1024. Why? When is each better?"

**出处**: Google FDE T2 / Pinecone / Cohere / LangChain / LlamaIndex 等几乎所有 RAG round 必问.

**Round**: RAG Pipeline Design (45 min)

---

## 这道题在考什么

考你 **chunking is non-trivial** awareness + production choices:

1. **Naive fail modes** —— fixed-size 切到句中, semantic cut wrong, 切到表格中间
2. **Strategy choice** —— sentence / paragraph / heading-aware / late chunking
3. **Overlap rationale** —— 防止 boundary 信息丢, 但有成本
4. **Size vs precision** —— 大 chunk 信息全, 小 chunk 精确
5. **Multi-modal awareness** —— tables / code / formulas / lists 不同处理
6. **Metadata enrichment** —— heading path / source / perms / freshness
7. **Index update strategy** —— delta indexing, versioning
8. **Eval methodology** —— sweep chunk size × overlap × strategy

不考「chunking 是什么」, 考「你有 10K PDF, 三天内要 launch, 决策路径」.

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**Chunk (块)**: RAG 系统里的 retrieval 最小单元. 一个 doc → 多个 chunk → 每个 chunk 独立 embed + index. Query 时检索回的也是 chunk, 不是整 doc.

**Chunk size**: chunk 的 token 数. 不是字数, 不是字符数, 是 LLM tokenizer 的 token (BPE / SentencePiece). Embedding 模型有 max context (512 / 8192), 超了会被 truncate.

**Overlap**: 相邻 chunk 之间重叠的 token. 典型 10-20% (512 chunk → 50-100 overlap). 目的: borderline 信息 (跨越两 chunk 的句子) 不丢.

**Late chunking** (2024-2025 新): 先用长 context embedding 模型 embed 整 doc, 拿 token-level embedding, 然后 pool 成 chunk-level embedding. 区别于经典先 chunk 再 embed.

---

## 2. 这个问题的核心是什么

设想 naive fixed-size 512 chunking 在 10K 技术 PDF 上的灾难:

```
PDF: "iPhone 15 Pro Max Technical Specifications"
原文 page 47:
  "Rated voltage: 5V
   Maximum current: 3A
   ...
   [Table 4: Operating Temperature]
   Min: -20°C
   Max: 60°C
   ..."

Naive fixed 512-token chunk 切割位置:
  Chunk 23: "...Rated voltage: 5V\nMaximum cur" ← 切在表格中间
  Chunk 24: "rent: 3A\n[Table 4: Operating Te" ← 表格散到两块
  Chunk 25: "mperature]\nMin: -20°C\nMax: 60°C"

Query: "iPhone 15 Pro Max operating temperature range"
Dense retrieval: 命中 chunk 25 → 拿到 "Min: -20°C Max: 60°C"

LLM 答: "The operating temperature is -20°C to 60°C"
User: "of what device? you didn't say"
LLM: ¯\_(ツ)_/¯ (chunk 25 没有 device context, heading 信息没了)
```

**问题**:

- **切表格** → 半个表格无意义
- **切代码** → 半个 function 无用
- **切句子中间** → 语义碎片
- **丢 heading 上下文** → "5V" 不知道是哪个 device 的
- **chunk 跨多 topic** → 单个 embedding 表示多主题, 召回率低
- **chunk 太小** → 答案被切到 2 个 chunk, 单个 retrieve 不到全部
- **chunk 太大** → 单个 embedding 信息密度低, 噪声多

**好 chunking 的解法**:

```
Heading-aware recursive chunking:
  PDF parse → tree (Chapter → Section → Subsection → Paragraph)
  Walk tree:
    if section fits in max_chunk_size:
      → 1 chunk, embed includes heading path
    elif has subsections:
      → recurse into subsections
    else (leaf too big, e.g., raw prose):
      → fixed-size with overlap fallback

  Table / Code / Formula: ATOMIC chunk (don't split)
  Each chunk metadata: {doc_id, heading_path, page_range, source_type, perms, ...}
```

---

## 3. 决策树 / 流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                  Chunking Decision Tree                          │
└─────────────────────────────────────────────────────────────────┘

Q1: 文档有 structure (heading / chapter / section)?
  YES → Heading-aware recursive (default)
  NO  → 继续

Q2: 文档是对话 / log / 流式?
  YES → Speaker-turn / time-window chunking
  NO  → 继续

Q3: 文档是代码?
  YES → AST-based (function / class boundary)
  NO  → 继续

Q4: 文档是表格密集型 (财报 / 数据手册)?
  YES → Table-as-atomic-chunk + surrounding text chunk
  NO  → 继续

Q5: 文档短 (< 1000 tok)?
  YES → Whole-doc as one chunk
  NO  → 继续

Q6: 嵌入模型支持长 context (Jina v3 / Gemini embed long)?
  YES + 文档 < 8K tok → Late chunking (advanced)
  NO  → 继续

DEFAULT → Fixed-size (500 tok) + overlap (50) + sentence-aware boundary
```

```
┌─────────────────────────────────────────────────────────────────┐
│                  Multi-modal sub-tree                            │
└─────────────────────────────────────────────────────────────────┘

For each element in doc:
  if element is TABLE:
    → atomic chunk
    → text representation: Markdown table
    → metadata: {is_table: true, caption: ..., headers: [...]}
  elif element is CODE:
    → atomic chunk (don't split mid-function)
    → text: ```{lang}\n{code}\n```
  elif element is FIGURE:
    → caption + alt text chunk
    → optionally separate image embed (multimodal RAG)
  elif element is FORMULA:
    → LaTeX representation chunk
    → optionally rendered description
  elif element is LIST:
    → if short: atomic
    → if long: split at item boundary
  else (prose):
    → heading-aware or fallback
```

---

## 4. 关键 chunking 策略分类表

| 策略 | Avg chunk size | 何时用 | 实现复杂度 | 召回质量 |
|---|---|---|---|---|
| **Fixed-size + overlap** | 500 tok + 50 | baseline, 无结构 prose | ⭐ 简单 | ⭐⭐ 一般 |
| **Sentence-aware** | 5-10 句 | 略好 baseline | ⭐⭐ | ⭐⭐⭐ |
| **Paragraph / section** | 200-800 tok | 有 paragraph break | ⭐⭐ | ⭐⭐⭐ |
| **Heading-aware recursive** | 可变, 按 section | 有 heading 层级 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Semantic chunking** | 可变, 按 topic shift | 长 prose 无明显 break | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **AST-based** (code) | 函数 / 类 | 代码 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Late chunking** | 可变 | 长 context embed 模型 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ (intra-doc context heavy) |
| **Hierarchical / parent-doc** | 子 + 父 | 需要 wider context | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

production 90% 用 **heading-aware recursive + fixed-size fallback + table/code 特殊处理**.

---

## 5. 具体业务场景 (5 个高频)

### 场景 A: 技术 PDF 手册 (本题主战场, 你的工作背景类似)

10K 个 50-500 页技术 PDF (硬件 datasheet / API doc / 用户手册):
- 有 heading 层级 (Chapter X.Y.Z)
- 含表格 (规格参数)
- 含代码示例
- 含图表 (caption + 图)

**策略组合**:
- Heading-aware recursive (主)
- 表格 → atomic + Markdown serialize
- 代码 → atomic + lang annotation
- 图 → caption chunk + 图存 blob

### 场景 B: 客服 ticket + KB articles (你的 BNPL chatbot)

混合 source:
- KB articles (long-form, 有 heading)
- Tickets (短, 对话式, 1-3 KB)
- FAQ (一问一答)

**策略**:
- KB: heading-aware (avg 600 tok)
- Ticket: 整 ticket as 1 chunk (avg 300 tok), 或 split by 客户 vs 客服 turn
- FAQ: 一组 Q+A as 1 chunk (avg 100 tok)
- Source-type 作为 metadata 标签, retrieval 时可 boost / filter

### 场景 C: 代码仓库 (monorepo)

1M LOC monorepo:
- **AST-based**: tree-sitter 解析, function / method / class 为 chunk 单位
- **不切函数内部** — 一个函数永远是 1 chunk (即便 500 行)
- **Import + signature 嵌入**: chunk content = `imports + signature + body`
- **3 个 index**: code (BM25 on identifier), comment (dense), doc (dense)
- **Cross-file 关系**: 单独存 call-graph, retrieve 后扩展 1-hop

### 场景 D: 法律合同

500-page 商业合同:
- **Clause-level chunking**: 不是 paragraph, 是 clause boundary (section 4.2, 5.1)
- **Metadata**: contract_type, parties, effective_date, jurisdiction, section_number
- **Heading 强制保留**: "§4.2 IP Assignment" 永远在 chunk 开头
- **Reference 解析**: "as defined in §1.3" 自动扩展引用上下文

### 场景 E: 学术论文 (arXiv)

含公式 / 引用 / 图:
- **Section-aware**: abstract / intro / method / experiments / conclusion 各自 chunk
- **Equation 保留 LaTeX**: 不 OCR 截图, parse PDF 拿 LaTeX
- **Figure caption** 单独 index (caption 信息密度最高)
- **Citation graph**: paper → cited papers, 1-hop retrieve
- **Domain-aware embedding**: SciBERT / BiomedBERT 而非通用

---

## 6. 工程上要做什么 (实现 checklist)

**Phase 1: 文档解析**:

1. **PDF → 结构化**: 用 `unstructured`, `pymupdf`, `PyPDF2`, 或商用 (Azure Document Intelligence, AWS Textract)
2. **Element 分类**: title / heading / paragraph / table / list / code / figure
3. **Heading hierarchy 建树**: H1 > H2 > H3, 维护 ancestor path
4. **OCR fallback** for image-only PDF (Tesseract / Azure)

**Phase 2: Chunk 生成**:

5. **遍历 element tree**, 应用 chunking strategy (上面决策树)
6. **Atomic 处理 table / code / figure** — 不切
7. **Fallback fixed-size + overlap** for unstructured leaf section
8. **每 chunk 附 metadata**

**Phase 3: Embedding**:

9. **Heading prepend** to chunk text before embed: `embed(f"{heading_path}\n{text}")`
10. **Batch embed** (Gemini embedding-001 / OpenAI text-embedding-3 都支持 batch 256)
11. **L2 normalize** for cosine similarity

**Phase 4: Index**:

12. **Dense index** to Qdrant / Pinecone (含 metadata)
13. **Sparse index** to OpenSearch (BM25) — 同 chunk text
14. **Metadata 双写** 保持一致

**Phase 5: 更新管理**:

15. **Delta indexing**: doc 改 → chunk 重 hash, 仅改 chunk 重 embed
16. **Versioning**: 保留旧 chunk 短期 (灰度切换)
17. **Async pipeline**: 用户上传 → queue → background worker

**Phase 6: Eval**:

18. **Eval set**: 200 (query, [chunk_ids]) 标注
19. **Sweep**: chunk_size ∈ {256, 512, 768, 1024} × overlap ∈ {0, 50, 100} × strategy ∈ {fixed, heading-aware}
20. **CI**: 每次 chunking 改动跑 regression

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **Fixed-size everywhere** | 切表格 / 代码 / 句子中间, 召回严重 |
| 2 | **No overlap** | Boundary 信息丢, 跨 chunk 答案抓不到 |
| 3 | **Heading discarded** | "5V" 不知道是哪个设备, embedding 没 context |
| 4 | **Cut tables / code in middle** | 半 table 无意义 |
| 5 | **All same chunk size 一刀切** | 不同 source-type 应该不同策略 |
| 6 | **No metadata** | 检索后无法 filter (date / author / perms) |
| 7 | **No eval, 凭 feel** | 不知道 512 / 1024 哪个好, 调参靠运气 |
| 8 | **Single mega-chunk per doc** | "PDF in 1 vector" 信息密度低, 失精 |
| 9 | **Reindex 全量** | 1 doc 改 → 10K doc 全重 embed, 浪费 |
| 10 | **OCR 不做 / 做错** | Image-only PDF 0 text, 召回 0 |
| 11 | **Tokenizer mismatch** | 用 GPT tokenizer 数 token 但 embedding 用 BERT — 估算偏差 30%+ |
| 12 | **No table-to-text conversion** | 表格 raw cell 顺序乱, LLM 读不懂 |

---

## 一句话总结 (Part 1)

> **Chunking = 「按 doc 结构切 + 不切表格 / 代码 / 句子 + 附 heading metadata + overlap 兜底边界 + 多种 source 多种策略 + eval 量化」**.
>
> 不是「fixed 512」一个数字, 是一套**多策略组合 + 工程流水线**.

---

# Part 2 · 5 个深度工程问题

## ⚙️ Problem 1: Chunking 策略 Taxonomy — Fixed / Sentence / Paragraph / Heading / Late

### 1.1 Fixed-size + overlap (baseline)

```python
def fixed_size_chunk(
    text: str,
    chunk_size: int = 500,    # in tokens
    overlap: int = 50,
    tokenizer=tiktoken.get_encoding('cl100k_base'),
):
    tokens = tokenizer.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
        start += chunk_size - overlap  # advance with overlap
    return chunks
```

**优点**: 简单, 可预测 chunk 数量, 任何 text 都 work
**缺点**: 切 mid-sentence, mid-table, 丢 structure
**用在哪**: baseline benchmark, 完全无结构 prose

### 1.2 Sentence-aware

```python
import nltk
def sentence_aware_chunk(text, max_size=500, overlap_sentences=2):
    sentences = nltk.sent_tokenize(text)
    chunks = []
    current, current_size = [], 0
    for sent in sentences:
        sent_tokens = count_tokens(sent)
        if current_size + sent_tokens > max_size and current:
            chunks.append(' '.join(current))
            # Overlap: keep last N sentences
            current = current[-overlap_sentences:]
            current_size = sum(count_tokens(s) for s in current)
        current.append(sent)
        current_size += sent_tokens
    if current:
        chunks.append(' '.join(current))
    return chunks
```

**优点**: 不切 mid-sentence
**缺点**: 仍然无 heading awareness; 多语言 sentence splitter 不准
**用在哪**: 比 fixed 略好的 fallback

### 1.3 Heading-aware recursive (推荐 default)

```python
def heading_aware_chunk(doc_tree: SectionNode, max_size=500, overlap=50):
    """
    doc_tree: 解析出来的 section 树
      SectionNode { title, level, text, children: [SectionNode], page_range }
    """
    chunks = []

    def walk(node, ancestor_path):
        path = ancestor_path + [node.title]
        node_text = node.text or ''
        node_tokens = count_tokens(node_text)

        if node_tokens <= max_size and not node.children:
            # Leaf section fits in 1 chunk
            chunks.append(Chunk(
                text=node_text,
                metadata={
                    'heading_path': path,
                    'page_range': node.page_range,
                    'section_level': node.level,
                },
                # embed text includes heading context
                embed_text=f"{' > '.join(path)}\n\n{node_text}",
            ))
        elif node.children:
            # Recurse into children
            # Note: we DON'T add node.text here unless it's a section-intro paragraph
            if node_text:
                # Optionally include intro paragraph as own chunk
                chunks.append(Chunk(text=node_text, metadata={
                    'heading_path': path, 'kind': 'intro', ...
                }))
            for child in node.children:
                walk(child, path)
        else:
            # Leaf section too big, fall back to fixed-size with overlap
            sub_chunks = fixed_size_chunk(node_text, max_size, overlap)
            for i, sc in enumerate(sub_chunks):
                chunks.append(Chunk(
                    text=sc,
                    metadata={
                        'heading_path': path,
                        'sub_index': i,
                        'total_subs': len(sub_chunks),
                    },
                    embed_text=f"{' > '.join(path)}\n\n{sc}",
                ))

    walk(doc_tree, ancestor_path=[doc_tree.doc_title])
    return chunks
```

**关键**:
- **Heading prepended to embed text** — 让 embedding 知道 context
- **Recursion 处理深 hierarchy**
- **Fallback** 到 fixed-size 应对长 prose section

### 1.4 Semantic chunking (topic shift detection)

```python
def semantic_chunk(text, model='all-mpnet-base-v2', threshold=0.3):
    """
    切在 topic 转换处. 句子之间 embedding cosine 距离 > threshold 处切.
    """
    sentences = nltk.sent_tokenize(text)
    embeddings = [embed(s) for s in sentences]

    chunks, current = [], [sentences[0]]
    for i in range(1, len(sentences)):
        sim = cosine(embeddings[i], embeddings[i-1])
        if sim < (1 - threshold):  # 相似度低 = topic shift
            chunks.append(' '.join(current))
            current = [sentences[i]]
        else:
            current.append(sentences[i])
    if current:
        chunks.append(' '.join(current))
    return chunks
```

**优点**: 自适应找 topic 边界, 不依赖 heading
**缺点**: 慢 (per-sentence embed), threshold 调参敏感, 长文本 chunk 数不稳定
**用在哪**: 长 prose 无 heading 但有明显 topic 划分

### 1.5 Late chunking (2024-2025 advanced)

```python
def late_chunk(doc_text, embedding_model='jinaai/jina-embeddings-v3', max_tokens=8192):
    """
    1. 整 doc 进 long-context embedding 模型
    2. 拿到 token-level embeddings (shape [n_tokens, d])
    3. 按 chunk boundary pool (mean) 成 chunk embedding
    """
    tokens, token_embeds = embed_with_token_outputs(doc_text)  # 长 ctx 模型

    # 按 sentence / paragraph 边界确定 chunk 范围
    chunk_boundaries = find_boundaries(tokens)  # e.g., paragraph breaks

    chunk_embeds = []
    for start, end in chunk_boundaries:
        chunk_emb = token_embeds[start:end].mean(axis=0)  # mean pool
        chunk_text = tokenizer.decode(tokens[start:end])
        chunk_embeds.append(Chunk(text=chunk_text, embedding=chunk_emb, ...))
    return chunk_embeds
```

**核心收益**: 每个 chunk 的 embedding **已经包含整 doc context**, 因为 long-context model 在算 token embedding 时看了全 doc.

**对比经典 chunking**:
```
经典:  text → split → 每个 chunk 独立 embed (chunk 只有自己的 context)
Late:  text → 整文档 embed → 按 chunk 切 pool (每个 chunk 有全 doc context)
```

**实测收益**: intra-doc context heavy 的场景 (legal / 科研) NDCG +5-10%
**代价**:
- 必须 long-context embedding 模型 (Jina v3 8K, Gemini embedding long)
- Embed 成本上升 (但 reindex 频率降)
- Doc 改 → 重 embed 全文 (不能 delta single chunk)

**何时用 / 不用**:
- ✓ Doc 长 (5K-50K tok), intra-doc context 重要
- ✓ Doc 更新慢 (月度)
- ✗ Doc 极长 (>50K) 超长 ctx 模型限制
- ✗ Doc 频繁更新 (delta 不便)

### 1.6 Hierarchical / Parent-doc chunking

存两套: **小 chunk for retrieval, 大 chunk for LLM context**.

```python
def hierarchical_chunk(doc):
    # 小 chunk (200 tok) for 精确检索
    small_chunks = chunk_by(doc, size=200, overlap=20)
    # 大 chunk (800 tok) for LLM 上下文
    large_chunks = chunk_by(doc, size=800, overlap=80)

    # 每个小 chunk 知道其所属 large chunk
    for sc in small_chunks:
        sc.metadata['parent_id'] = find_parent(sc, large_chunks)

    # Index 小 chunk (高精度 retrieval)
    # Retrieve 后, 用 parent_id 拿大 chunk 给 LLM (more context)
    return small_chunks, large_chunks
```

LangChain `ParentDocumentRetriever` 实现的就是这个.

**优点**: 精确 retrieve + 富 context
**缺点**: 多一份存储, 复杂

### 1.7 Strategy 选择 decision table

| Doc 类型 | Strategy |
|---|---|
| 技术文档 (有 heading) | Heading-aware recursive |
| 代码 | AST-based (function / class) |
| 法律 / 合同 | Clause-aware (legal section) |
| 学术论文 | Section-aware (abstract / method / ...) |
| 对话 / 客服 | Turn-aware (speaker boundary) |
| Log / time series | Time-window (5 min bucket) |
| YouTube transcript | Time-window + topic segmentation |
| 短 doc (< 1K tok) | Whole doc as 1 chunk |
| 长 doc + 长 ctx embed | Late chunking |
| 一般 prose | Sentence-aware + fixed fallback |

---

## ⚙️ Problem 2: Multi-modal Handling — Tables / Code / Formulas / Lists

### 2.1 Tables (重灾区)

技术 PDF 一半 value 在表格里, naive chunking 切完全废.

**步骤**:

```python
def extract_table_chunk(table_element):
    """
    table_element: PDF parser 返回的 table object
      { rows: [[cell, cell, ...], ...], caption: str, page: int, bbox: ... }
    """
    # 1. Serialize to Markdown
    headers = table_element.rows[0]
    body = table_element.rows[1:]
    md = '| ' + ' | '.join(headers) + ' |\n'
    md += '| ' + ' | '.join(['---'] * len(headers)) + ' |\n'
    for row in body:
        md += '| ' + ' | '.join(str(c) for c in row) + ' |\n'

    # 2. Caption + context for embedding
    caption = table_element.caption or 'Table'
    surrounding = table_element.preceding_paragraph or ''  # 紧邻段落作 context

    embed_text = f"{caption}\n\nContext: {surrounding}\n\n{md}"
    # Embedding 把 caption + 上下文 + Markdown 一起 embed
    # 这样查 "operating temperature" 能命中含此关键词的 caption

    # 3. Chunk content for LLM
    return Chunk(
        text=md,
        metadata={
            'is_table': True,
            'caption': caption,
            'headers': headers,
            'row_count': len(body),
            'page': table_element.page,
            'doc_id': ...,
            'heading_path': ...,
        },
        embed_text=embed_text,
    )
```

**关键**:
- **Markdown 表示** — LLM 训练数据见过 Markdown 表格, 能理解
- **Caption + 上下文** 加进 embedding (单纯 cell 数据 embedding 像 noise)
- **永远 atomic**, 即便表格大. 大表格 → 多个 sub-table by row block? **少做** — LLM 看不懂半张表

**特殊大表格策略**:
- 表格 > 100 行 → 拆 by row group (但 header 在每个 sub-chunk 重复)
- 同时存"表格摘要" chunk: "Table 4 contains 200 rows of test data with columns ..." (供宽语义检索)

### 2.2 Code blocks

```python
def extract_code_chunk(code_element):
    return Chunk(
        text=f"```{code_element.language}\n{code_element.text}\n```",
        metadata={
            'is_code': True,
            'language': code_element.language,
            'symbols_defined': extract_symbols(code_element.text),  # 函数/类名
            'line_count': len(code_element.text.split('\n')),
            'page': code_element.page,
        },
        embed_text=(
            f"Code in {code_element.language}: "
            f"defines {', '.join(extract_symbols(code_element.text))}\n\n"
            f"```{code_element.language}\n{code_element.text}\n```"
        ),
    )
```

**原则**:
- **不切 function 中间** — 跨 def 切不可
- **Language annotation** in embed_text (用户查 "Python function for X")
- **Symbol extraction** 加 metadata (BM25 命中函数名)
- **超长 function (> 800 tok)** 例外: 接受切, 但每 sub-chunk 标明 part 1/3

### 2.3 Formulas / 数学公式

LaTeX 直接保留:

```python
def extract_formula_chunk(formula_element):
    return Chunk(
        text=formula_element.latex,
        metadata={
            'is_formula': True,
            'page': formula_element.page,
            'equation_ref': formula_element.label,  # e.g., "Eq. 3.5"
        },
        # 加文字描述以便检索 "Pythagorean theorem"
        embed_text=(
            f"Equation {formula_element.label}: {formula_element.latex}\n"
            f"Description: {formula_element.surrounding_text}"
        ),
    )
```

**为什么不渲染**: LLM 已学过 LaTeX, 渲染图片反而 LLM 看不懂.

### 2.4 Lists

```python
def chunk_list(list_element, max_size=500):
    items = list_element.items
    # 短 list → atomic
    if sum(count_tokens(i) for i in items) < max_size:
        return [Chunk(text='\n'.join(f'- {i}' for i in items), ...)]
    # 长 list → split at item boundary, 不切 item 中间
    chunks, current, current_size = [], [], 0
    for item in items:
        item_tokens = count_tokens(item)
        if current_size + item_tokens > max_size and current:
            chunks.append(Chunk(text='\n'.join(f'- {i}' for i in current), ...))
            current = []
            current_size = 0
        current.append(item)
        current_size += item_tokens
    if current:
        chunks.append(Chunk(text='\n'.join(f'- {i}' for i in current), ...))
    return chunks
```

### 2.5 Figures / Images

**两种模式**:

**Mode 1: Caption-only** (cheaper):
```python
def figure_chunk_caption_only(fig):
    return Chunk(
        text=f"Figure {fig.label}: {fig.caption}",
        metadata={'is_figure': True, 'image_path': fig.image_path, ...},
        embed_text=f"Figure {fig.label}: {fig.caption}\n\n{fig.surrounding_text}",
    )
```

**Mode 2: Multimodal RAG** (with vision embedding):
```python
def figure_chunk_multimodal(fig):
    image_embedding = vision_model.embed(fig.image)  # CLIP / Gemini vision
    text_embedding = text_model.embed(fig.caption)
    return MultimodalChunk(
        text=fig.caption,
        image=fig.image,
        embeddings={'text': text_embedding, 'image': image_embedding},
        metadata={...},
    )
```

Query 时可以 text-query 命中 image (CLIP-class 共享空间) 或 hybrid query.

### 2.6 工具

| 任务 | 工具 |
|---|---|
| PDF 结构化 | `unstructured`, `pymupdf`, Azure Document Intelligence, AWS Textract |
| 表格提取 | Camelot, Tabula, pdfplumber, Azure Form Recognizer |
| OCR | Tesseract, AWS Textract, Google Document AI |
| Code AST | tree-sitter (语言无关), Python ast 模块 |
| LaTeX from PDF | mathpix API, pix2tex |
| Multimodal embed | CLIP, BLIP, gemini-embedding multimodal |

---

## ⚙️ Problem 3: Metadata Enrichment — Heading Path / Source / Perms / Freshness

### 3.1 完整 metadata schema

```python
Chunk = {
    # Identity
    'chunk_id': 'uuid-...',
    'doc_id': 'doc-abc',
    'chunk_index': 23,           # 在 doc 内序号
    'total_chunks_in_doc': 80,

    # Source
    'doc_title': 'iPhone 15 Pro Max User Guide',
    'doc_url': 'https://...',
    'doc_type': 'manual',        # 'policy', 'ticket', 'kb', 'code', 'paper'
    'source_system': 'confluence',  # 'confluence', 'jira', 'sharepoint', 'github'

    # Structure
    'heading_path': ['Chapter 4', 'Section 4.2', 'Configuration'],
    'section_level': 3,
    'page_range': (45, 47),
    'is_table': False,
    'is_code': False,
    'is_figure': False,

    # Time
    'created_at': '2024-01-15T10:00:00Z',
    'updated_at': '2026-05-20T14:30:00Z',
    'effective_date': '2024-02-01',  # for policy docs

    # Access control
    'tenant_id': 'tenant_xyz',
    'visibility': 'internal',      # 'public', 'internal', 'confidential'
    'acl_groups': ['eng', 'sre'],
    'pii_level': 0,                # 0 none, 1 low, 2 medium, 3 high

    # Quality / boost signals
    'quality_score': 0.85,
    'view_count_30d': 1234,
    'positive_feedback_rate': 0.78,
    'is_canonical': True,           # KB authoritative source

    # Tags
    'tags': ['installation', 'troubleshooting'],
    'language': 'en',
    'product': 'iPhone 15 Pro Max',
}
```

### 3.2 Heading path 的妙用

**Embed with heading**:
```python
# Bad
embed_text = chunk.text
# 'Rated voltage: 5V, max current: 3A'  ← 不知道是什么设备

# Good
embed_text = f"{' > '.join(chunk.heading_path)}\n\n{chunk.text}"
# 'iPhone 15 Pro Max > Specifications > Electrical\n\nRated voltage: 5V, max current: 3A'
# Embedding 现在能命中 'iPhone 电压'
```

**Filter at retrieval**:
```python
# 用户问 'how to install', filter chunks with heading 含 'Installation'
qdrant.search(
    query_vector=q_vec,
    query_filter={
        'should': [
            {'key': 'heading_path', 'match': {'any': ['Installation', 'Setup']}},
        ]
    },
)
```

### 3.3 Freshness decay

```python
def freshness_score(chunk, tau_days=90):
    """指数衰减, 90 天后权重降到 1/e ≈ 0.37"""
    age_days = (now() - chunk.updated_at).days
    return math.exp(-age_days / tau_days)

# 检索 rerank 时
for chunk in candidates:
    chunk.final_score = chunk.relevance_score * (0.7 + 0.3 * freshness_score(chunk))
```

**特殊场景**:
- News / 实时数据: τ = 1-7 day
- 技术文档: τ = 90-180 day
- 法律 / 合同: τ = ∞ (历史合同永远有效)
- 政策 (有 effective_date): hard filter `effective_date <= now` AND `(expires_at IS NULL OR expires_at > now)`

### 3.4 Perms enforcement

**Retrieval-time filter** (NOT post-rank):

```python
def retrieve_with_perms(query, user):
    user_groups = get_user_groups(user)
    qdrant_filter = {
        'must': [
            {'key': 'tenant_id', 'match': {'value': user.tenant_id}},
            {'key': 'visibility', 'match': {'any': ['public', 'internal']}},
        ],
        'should': [
            {'key': 'acl_groups', 'match': {'any': user_groups}},
        ],
    }
    return qdrant.search(
        query_vector=embed(query),
        query_filter=qdrant_filter,
        limit=100,
    )
```

**绝对不要 post-rank filter**:
```python
# BAD
results = qdrant.search(query_vector=embed(query), limit=10)
results = [r for r in results if user_can_see(r)]  # 可能 0 个剩下
```

为什么? 因为 vector search 拿 top-10, filter 后剩 2 个, 而真正应该返回的 perm-allowed top-10 在 retrieve 时被 ranked 50 名外 → 全丢.

### 3.5 PII tagging

```python
def tag_pii(chunk_text):
    # 用 presidio / Microsoft Presidio analyzer
    from presidio_analyzer import AnalyzerEngine
    analyzer = AnalyzerEngine()
    results = analyzer.analyze(
        text=chunk_text,
        entities=['PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER', 'CREDIT_CARD',
                  'IBAN_CODE', 'IP_ADDRESS', 'US_SSN'],
        language='en',
    )
    return {
        'pii_entities': [(r.entity_type, r.start, r.end) for r in results],
        'pii_level': len(results) // 2,  # 简单 heuristic
    }
```

后续 retrieval / display 可以基于 pii_level 决定 mask 或 drop.

---

## ⚙️ Problem 4: Index Update Strategy — Delta / Versioning / Async Reindex

### 4.1 Full reindex 为何不可

```
10K PDF × avg 100 chunk per doc = 1M chunks
1M chunks × gemini-embedding-001 batch 256 = 4000 batch calls
Each batch ~200ms = 800s = 13 minutes (just for embedding)
+ Qdrant bulk upsert ~10 minutes
+ OpenSearch bulk index ~15 minutes

总: 40+ 分钟 stop-the-world reindex
每天 / 每小时改个 doc 都 full reindex → 显然不可
```

### 4.2 Delta indexing

```python
class DeltaIndexer:
    def index_doc(self, doc_id, new_content):
        # 1. Compute new chunks
        new_chunks = chunk_doc(new_content)
        new_chunk_hashes = {c.id: hash_content(c.text + json.dumps(c.metadata))
                            for c in new_chunks}

        # 2. Load existing chunks for this doc
        existing = self.db.query(
            "SELECT chunk_id, content_hash FROM chunks WHERE doc_id = ?",
            doc_id,
        )
        existing_hashes = {row.chunk_id: row.content_hash for row in existing}

        # 3. Compute diff
        to_add = [c for c in new_chunks if c.id not in existing_hashes]
        to_update = [c for c in new_chunks
                     if c.id in existing_hashes
                     and existing_hashes[c.id] != new_chunk_hashes[c.id]]
        to_delete = [cid for cid in existing_hashes
                     if cid not in new_chunk_hashes]

        # 4. Apply
        for c in to_add + to_update:
            c.embedding = embed(c.embed_text)
        self.dense_index.upsert(to_add + to_update)
        self.sparse_index.upsert(to_add + to_update)
        self.dense_index.delete(to_delete)
        self.sparse_index.delete(to_delete)

        # 5. Update meta DB
        self.db.execute("UPDATE chunks SET content_hash=? WHERE chunk_id=?", ...)

        return {'added': len(to_add), 'updated': len(to_update), 'deleted': len(to_delete)}
```

**Chunk ID 稳定性是关键**:
- 不能用纯 random UUID — 每次都不同
- 用 `hash(doc_id + heading_path + chunk_index_in_section)` 这样**结构性 hash** — 只有结构变才换 ID

### 4.3 Versioning + 灰度切换

```
Index versions:
  v1: 2025-12 原始 chunking strategy
  v2: 2026-01 改用 heading-aware
  v3: 2026-03 加 late chunking 实验

Strategy:
  双写 v2 + v3 一段时间
  Search 走 traffic split: 80% v2 / 20% v3
  Eval v3 hold ≥ v2 → 全切 v3, drop v2 collection
```

```python
def search_with_versioning(query, user_id):
    if hash(user_id) % 100 < 20:
        return search_index_v3(query)
    return search_index_v2(query)
```

### 4.4 Async pipeline

```python
# Doc 上传 / 修改 webhook
@app.post('/doc/update')
async def doc_update(doc_id, content):
    # 1. 立即写 doc 主表 (canonical source)
    db.upsert_doc(doc_id, content)
    # 2. Enqueue reindex job
    await kafka.produce(
        topic='reindex_jobs',
        key=doc_id,           # 同 doc_id 进同 partition, 保证 FIFO
        value={'doc_id': doc_id, 'ts': now()},
    )
    return {'status': 'queued'}

# Background worker
async def reindex_worker():
    async for msg in kafka.consume('reindex_jobs'):
        doc_id = msg.value['doc_id']
        try:
            content = db.get_doc(doc_id)
            DeltaIndexer().index_doc(doc_id, content)
            metrics.incr('reindex.success', tags={'doc_id': doc_id})
        except Exception as e:
            metrics.incr('reindex.failure')
            log.exception('reindex failed')
            # 进 DLQ retry
```

**Backpressure**: 如果 reindex queue 积压 > 1 小时 → alert + 扩 worker.

### 4.5 Hot + warm index pattern

新建 doc 可能在 retrieval 里几小时不可见 (queue lag). 解决:

```
Hot index:
  Last 24h created/updated docs
  In-memory Qdrant 小 collection
  Refresh every 5 min from doc DB

Warm index:
  Older docs
  Persistent Qdrant collection
  Async background reindex

Query: search both, RRF merge
```

### 4.6 Cost / time 实测 (10K doc)

| 操作 | Time | Cost |
|---|---|---|
| Full reindex 10K doc (1M chunks) | 40 min | ~$25 embedding (gemini-embedding-001 $0.025/1M tok × 500M tok) |
| Delta single doc (100 chunks, 10% change) | 1 sec | $0.0001 |
| Hot index 5-min refresh | < 1 sec | negligible |

---

## ⚙️ Problem 5: Eval Methodology — Sweep Chunk Size × Overlap × Strategy

### 5.1 Eval set 构建

**人工标注 200 query**:
```python
# 每个 query 标注:
# - relevant_chunk_ids: list of ground-truth relevant chunks
# - graded_relevance: { chunk_id: 0-3 score }
```

构造小心点:
- 真实 user query 取样 (不要全合成)
- 覆盖各种 doc 类型 (table-heavy / code-heavy / prose)
- 覆盖各种 query 类型 (factual / how-to / lookup)
- 双 annotator + adjudicate

### 5.2 Sweep 实验

```python
configs = []
for chunk_size in [256, 384, 512, 768, 1024]:
    for overlap in [0, 25, 50, 100]:
        for strategy in ['fixed', 'sentence', 'heading-aware']:
            configs.append({
                'chunk_size': chunk_size,
                'overlap': overlap,
                'strategy': strategy,
            })

results = []
for cfg in configs:
    # Rebuild index with this config
    chunker = build_chunker(cfg)
    chunks = chunker.chunk_all_docs(docs)
    index = build_index(chunks)

    # Eval
    metrics = evaluate(index, eval_set)
    results.append({**cfg, **metrics})
    log.info(f'config {cfg} → recall@10={metrics["recall@10"]:.3f} '
             f'NDCG@10={metrics["ndcg@10"]:.3f}')

# 找最优
best = max(results, key=lambda r: r['ndcg@10'])
print(f'Best: {best}')
```

**典型 sweep 结果**:

```
strategy=fixed, size=256, overlap=0:     recall@10=0.62, NDCG@10=0.51
strategy=fixed, size=512, overlap=50:    recall@10=0.73, NDCG@10=0.62
strategy=fixed, size=1024, overlap=100:  recall@10=0.71, NDCG@10=0.58
strategy=sentence, size=512, overlap=50: recall@10=0.75, NDCG@10=0.64
strategy=heading-aware, size=512:        recall@10=0.84, NDCG@10=0.73
strategy=heading-aware, size=768:        recall@10=0.86, NDCG@10=0.74  ← Best
strategy=heading-aware, size=1024:       recall@10=0.83, NDCG@10=0.72
```

**典型 finding**:
- **256 tokens**: 高 precision (chunk = answer), 低 recall (答案跨 chunk)
- **512 tokens**: sweet spot for most
- **1024+ tokens**: 更多 context 但 embedding 噪声
- **Overlap 对小 chunk 更重要**
- **Heading-aware 总是优于 fixed**

### 5.3 Slice eval

```python
slices = {
    'table_query': lambda q: 'table' in q.lower() or any(k in q for k in ['spec', 'rating']),
    'how_to_query': lambda q: q.lower().startswith(('how', 'why')),
    'code_query': lambda q: any(k in q for k in ['function', 'class', 'api']),
}
for name, fn in slices.items():
    sliced = [(q, e) for q, e in eval_set if fn(q)]
    m = evaluate(index, sliced)
    print(f'{name}: n={len(sliced)} recall@10={m["recall@10"]:.3f}')
```

**典型发现**:
- Table query slice: 单 chunk size 512 → recall 0.58 (差); 改 table-as-atomic → 0.82 (大幅好)
- Code query slice: fixed-size → recall 0.45; AST-based → 0.91

**每个 slice 独立改造**, 不是一个 chunk_size 通吃.

### 5.4 Per-source-type 不同策略

```python
class HybridChunker:
    def chunk(self, doc):
        if doc.source_type == 'faq':
            return self.atomic_chunker.chunk(doc)  # 1 FAQ = 1 chunk
        elif doc.source_type == 'policy':
            return self.heading_chunker.chunk(doc, max_size=600)
        elif doc.source_type == 'ticket':
            return self.conversation_chunker.chunk(doc, max_size=300)
        elif doc.source_type == 'code':
            return self.ast_chunker.chunk(doc)
        elif doc.source_type == 'paper':
            return self.section_chunker.chunk(doc, max_size=800)
        else:
            return self.fallback_chunker.chunk(doc, max_size=500, overlap=50)
```

`source_type` 也写 metadata, retrieval 可 boost.

### 5.5 CI / regression

```yaml
# .github/workflows/chunking-eval.yml
name: Chunking Eval Regression
on:
  pull_request:
    paths:
      - 'src/chunking/**'
      - 'configs/chunker.yaml'

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - run: python -m eval.chunking --baseline main --candidate ${{ github.sha }}
      # Fails if recall@10 drops > 2pp from main
```

每次 chunking 改动**必须**跑 eval, 否则会 silent regression.

### 5.6 Production observability

| Metric | Alert |
|---|---|
| Avg chunk count per doc | spike or drop > 20% from baseline |
| Chunks with empty heading_path | > 30% → chunker broken |
| Chunks > max_size (should be 0) | > 0 → bug |
| Reindex job latency p99 | > 1 min |
| Reindex failure rate | > 1% |
| Empty retrieval result rate | > 5% → chunk too small or filter too strict |

---

# Part 3 · 把 5 个问题串起来看

5 个问题是同一个工程问题的 5 个层面:

1. **Strategy taxonomy** 决定「按什么逻辑切」
2. **Multi-modal handling** 决定「特殊内容怎么处理」
3. **Metadata enrichment** 决定「retrieval 能不能 filter / boost」
4. **Index update** 决定「production 怎么 maintain」
5. **Eval** 决定「怎么知道每个改动有用」

面试场把这 5 层都讲, 加上「我们 BNPL chatbot 3 种 chunker 共存 71→84 recall」, 就是 senior RAG 工程师水准.

---

## 必问 clarifying questions

**1. Document structure**

> "PDFs have headings / hierarchy / TOC? Or unstructured prose? Different strategy decision tree branch."

**2. Content mix**

> "Text-only or includes tables, code blocks, figures, formulas? % of each? Tables 占主要 value 还是 prose?"

**3. Query type**

> "Users ask about facts ('what's the rated voltage of X') or concepts ('how does Y work') or both?"

**4. Embedding model**

> "What model? Max context (512 / 8192 / long)? Different chunking max size; long-context 才能 late chunking."

**5. Update frequency**

> "Reindex monthly OK or daily reindex needed (affects delta strategy)? Real-time (< 5 min) requires hot index."

---

## 5 步框架 (sample 45-min answer)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify structure + content mix + query type + update freq |
| 5-15 min | Strategy decision tree + heading-aware default |
| 15-25 min | Multi-modal handling (table / code / formula / figure) |
| 25-35 min | Metadata enrichment + perms + freshness |
| 35-45 min | Index update (delta + versioning + hot/warm) + eval sweep |

---

## 我会这样答 (sample)

> "Clarify — *[假设: 10K technical PDFs 50-500 页, mixed prose+tables+code+formulas, query 是 fact-lookup + concept-explanation, embedding 用 gemini-embedding-001 (768d, 2K max), daily reindex 可接受]*.
>
> **5 个 chunking strategies** — decision tree:
>
> 1. Fixed-size + overlap (baseline, unstructured)
> 2. Sentence-aware (略好 fallback)
> 3. Paragraph / section (有 paragraph)
> 4. **Heading-aware recursive** (有 heading, 默认选)
> 5. Late chunking (长 ctx embedding, 高级)
>
> **我的选择**: heading-aware recursive + fixed-size fallback + table/code 特殊处理.
>
> **算法**: parse PDF → section tree → walk:
> - Section 适合 1 chunk (< 500 tok) → 单 chunk, embed prepended with heading path
> - 有 subsection → 递归
> - Leaf 太大 → fixed-size + 50 token overlap fallback
> - Table / code / formula → atomic chunk, 不切
>
> **Why heading-aware**: 保留语义边界, heading 进 metadata 可 filter, heading 进 embed text 提升召回.
>
> **Multi-modal**: table → Markdown serialize + caption + 上下文一起 embed; code → atomic + symbol metadata; formula → LaTeX + 描述 embed.
>
> **Metadata schema**: doc_id, heading_path, page_range, source_type, tenant_id, visibility, updated_at, quality_score, pii_level, tags.
>
> **Index update**: delta indexing — 改 doc → chunk hash 比对 → 仅 changed chunk re-embed; chunk_id stability via `hash(doc_id + heading_path + chunk_index)`.
>
> **Eval**: 200 人工标注 + 1000 LLM 合成, sweep chunk_size × overlap × strategy, slice by query type (table / how-to / code), CI regression on each chunker change.
>
> **Expected**: heading-aware 768/50 should hit recall@10 ≈ 85%; with multi-modal special handling, table-query slice should reach 0.82+; 总 NDCG@10 ≈ 0.74.
>
> **What I would NOT do**: fixed-size everywhere; cut tables/code; discard heading; one chunk_size for all source types; reindex full corpus on each change."

---

## 简历专属 reframe

| 题 | 你的经验 |
|---|---|
| Chunking strategy | **BNPL chatbot RAG** — corpus mixed (tickets / docs / FAQs), 3 种 chunker 共存 |
| Metadata enrichment | **Voice agent** — every utterance + market + intent in retrieval metadata |
| Multi-modal | **Voice agent** — text + audio combined, ASR transcript + caller market metadata |
| Eval methodology | **ConvFinQA** — sweep ablation methodology 是这道题原型 |
| Index update | **Internal Agent Platform** — shared retrieval abstraction, delta indexing primitive |
| Multi-tenant perms | **TikTok PayLater** — natural cross-tenant isolation |

**主动 quote**:

> "BNPL chatbot had **3 chunking strategies coexisting**: FAQs as atomic chunks (avg 100 tokens, 1 FAQ = 1 chunk), policy docs heading-aware (avg 600 tokens, retain section hierarchy), support tickets paragraph-level (avg 300 tokens, split by speaker turn). Metadata included `source_type`, allowing retrieval to **mix sources** per query but weight relevant source higher (policy doc > ticket). Naive 'one chunk size fits all' at 512 had recall@10 = 71%, after split-by-source-type strategy + heading-aware on policies + table-as-atomic on regulatory docs, it went to 84%. The biggest jump (8pp) was from **table-as-atomic** because regulatory tables (interest rates, fee caps) were our highest-value content."

---

## 5 follow-ups

**Q1**: "Smaller chunks = more vectors = more storage. Cost concern."

**A**:
- **Storage**: 1M chunks × 768d × 4 bytes = 3GB. Cheap on Qdrant.
- **Index size (HNSW)**: 1.5-2x raw, still cheap
- **Query cost**: ANN search O(log n), small impact
- **Real cost**: embedding upfront — 1M chunks × 500 tok × $0.025/1M = $12.5 one-time. Negligible amortized.
- **Counter**: smaller chunks improve precision, fewer chunks fed to LLM → save LLM cost

**Q2**: "Reindexing — when doc changes, recompute embeddings expensive."

**A**:
- **Delta indexing**: chunk-level hash, only re-embed changed
- **Chunk ID stability** via structural hash (not random UUID)
- **Versioning**: old + new coexist briefly during transition
- **Async**: doc change → Kafka queue → background worker, eventual consistency acceptable
- **Hot index** for sub-5-min freshness on new docs

**Q3**: "Some chunks are 'TOC' or 'copyright' — junk for retrieval."

**A**:
- **Pre-filter at index time**: heuristic on heading text ('Table of contents', 'Copyright', 'References') skip
- **Quality scoring**: chunks with high keyword density / structure → kept
- **Hand-curated stoplist** for known patterns
- **LLM cheap pass**: 'is this chunk informative?' on questionable

**Q4**: "User question spans 3 sections. Retrieval gets 1, misses other 2."

**A**:
- **Hierarchical / parent-doc retrieval**: small chunk retrieved, large parent chunk returned (more context)
- **Multi-query expansion**: rewrite question into 3 sub-queries
- **Iterative retrieval (agentic)**: agent retrieves, sees gap, retrieves more
- **Document-level retrieval first**: find doc, then chunk within (two-stage)
- **Late chunking**: chunks inherently see doc context

**Q5**: "Late chunking sounds great — why not always use it?"

**A**:
- **Embedding cost** higher (long-context inference $$$)
- **Model availability**: not all embedding models support long context (need Jina v3, Gemini long-ctx)
- **Reindex granularity**: changes anywhere in doc → re-embed all
- **Best use**: long-document corpus, high intra-doc context (legal, scientific)
- **Not great for**: short-doc corpus, daily-changing data, multi-tenant where docs differ wildly

---

## ❌ 易错点 (top 10)

1. **Fixed-size everywhere** — no structural awareness
2. **No overlap** — boundary info lost
3. **Heading discarded** — embedding loses context
4. **Cut tables / code in middle** — broken semantic
5. **All same chunk size for all source types** — content variety ignored
6. **No metadata** — retrieval can't filter / boost
7. **No eval, 凭 feel** — chunk size 'feels right'
8. **Full reindex on each update** — wasteful, slow
9. **Random chunk IDs** — delta indexing impossible
10. **No PII tagging** — compliance issue

---

## ✅ 加分项 (top 10)

1. **Decision tree** for strategy choice (5 strategies)
2. **Heading-aware + recursive fallback** as default
3. **Overlap rationale** with cost trade-off
4. **Multi-modal special handling** (table/code/formula/figure)
5. **Metadata enrichment** including heading_path / perms / freshness
6. **Late chunking** awareness (2024-2025)
7. **Delta indexing** + chunk_id stability
8. **Eval sweep** chunk_size × overlap × strategy
9. **Per-source-type chunker** (not one-size-fits-all)
10. **Quote BNPL 3-strategy + 71→84 recall**

---

## 一句话总结

> **Chunking = 「按 doc 结构切, 不切表格代码句子, 附 heading metadata, overlap 兜底边界, 多种 source 多种策略, eval sweep 量化」**.
>
> 不是「fixed 512」一个数字, 是**多策略组合 + 工程流水线 + delta update + slice eval** 的整套.

---

## Cheat Sheet

```
5 strategies (decision tree):
  Fixed-size + overlap: baseline / unstructured
  Sentence-aware: respects sentence
  Paragraph / section: structured docs
  Heading-aware recursive: hierarchical (best general)
  Late chunking: long-context embedding model

Typical sizes:
  256 tokens: high precision, low recall
  512-768 tokens: sweet spot
  1024+ tokens: more context, noisier
  Overlap: 10% (50 tok for 512)

Multi-modal handling:
  Tables: atomic + Markdown serialize + caption embed
  Code: atomic + symbol metadata + lang annotation
  Formulas: LaTeX + textual description
  Figures: caption + optional vision embed
  Lists: atomic if short, item-boundary split if long

Metadata schema:
  Identity: chunk_id, doc_id, chunk_index
  Source: doc_title, doc_type, source_system
  Structure: heading_path, page_range, is_table/code/figure
  Time: created_at, updated_at, effective_date
  Access: tenant_id, visibility, acl_groups, pii_level
  Quality: quality_score, view_count, feedback_rate, is_canonical
  Tags: tags, language, product

Embed with heading context:
  embed_text = ' > '.join(heading_path) + '\n\n' + chunk.text

Delta indexing:
  chunk_id = hash(doc_id + heading_path + chunk_index)
  Compute new chunk hashes
  Diff with existing
  to_add / to_update / to_delete
  Apply to dense + sparse index

Versioning + 灰度:
  Double-write v_old + v_new
  Traffic split per user_id hash
  Eval new >= old → cutover

Hot + warm index:
  Hot: last 24h, 5-min refresh, in-memory
  Warm: rest, async delta indexing
  Search both, RRF merge

Eval methodology:
  Eval set: 200 human + 1000 synthetic
  Sweep: chunk_size × overlap × strategy
  Slice: by query type (table / how-to / code)
  CI regression on each chunker change

Per-source-type chunker:
  FAQ: atomic (1 entry = 1 chunk)
  Policy: heading-aware (600 tok)
  Ticket: turn-aware (300 tok)
  Code: AST-based (function / class)
  Paper: section-aware (800 tok)

Tool zoo (2026):
  PDF parse: unstructured, pymupdf, Azure Document Intelligence
  Tables: Camelot, Tabula, AWS Textract
  Code AST: tree-sitter
  PII: presidio (Microsoft)
  Embedding: gemini-embedding-001, text-embedding-3, bge-large
  Late chunking: jina-embeddings-v3
  Vector DB: Qdrant, Pinecone, Weaviate, Milvus

红线:
  - Fixed-size everywhere
  - No overlap
  - Cut tables / code mid
  - No metadata
  - All same size
  - No eval
  - Full reindex on update
  - Random chunk IDs
  - No PII tagging
```
