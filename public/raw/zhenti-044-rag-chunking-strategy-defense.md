## Q44 · Defend your RAG chunking strategy

> "You've built a RAG system for a customer. **Defend your chunking strategy.** Why these chunk sizes? Why this overlap? Why this method (recursive / semantic / heading-aware / fixed)? Walk me through the ablation that justifies your choice — including what you tried and rejected. The customer's data is mostly PDFs with sections, tables, code blocks, and inline figures."

**中文翻译**:

> "你给一个客户搭了一个 RAG (检索增强生成) 系统. **请你来 defend 你的 chunking (切块) strategy.** 为什么用这个 chunk 大小? 为什么用这个 overlap (重叠)? 为什么用这个方法 (recursive 递归 / semantic 语义 / heading-aware 按标题 / fixed 固定大小)? 跟我讲讲你用什么 ablation (消融实验) 来证明你的选择是对的 — 包括你试了什么, 又否决了什么. 客户的数据主要是 PDF, 里面有 sections, tables, code blocks, 还有内嵌的 figures."

**Round**: AI Specialty (45 min)
**出处**: Exponent 2026 FDE Guide · 公司: Cohere / Anthropic / OpenAI / Databricks — RAG specialty 必问

---

## 📖 术语速查 (本题用到的)

> RAG 是 FDE 第一常考方向, 术语堆叠. 5 min 扫完再看 chunking 细节.

### Chunking 策略 ⭐

| 术语 | 解释 |
|---|---|
| **Chunking** ⭐ | **把长文档切成 chunk (块)** 再 embed + 入库. Chunk 太小 = 没 context, 太大 = retrieval 不准. 默认 512 token + 50-100 overlap. |
| **Fixed-size chunking** | 按字符 / token 数硬切. 最简单, 但会切断句子 / table / code. 只适合 uniform text. |
| **Recursive chunking** | 按层级 separator (段 → 句 → 词) 递归切, 保持自然边界. 适合 long-form prose. |
| **Semantic chunking** | 按 embedding 相似度切 — 相邻句相似度 drop 就切. 适合多 topic 文档但贵 (每句都 embed). |
| **Structure-aware chunking** ⭐ | **按文档结构 (heading / paragraph / table / code) 切**. Table / code 当 atomic. Production 多数情况最优. |
| **AST-aware chunking** | 代码专用 — 用 syntax tree 按 function / class 切, 不会切断函数. |
| **Heading-aware chunking** | 按 markdown / HTML 标题级别切. 保留 section context. |
| **Late chunking** | 句子级 embedding, 查询时动态 group 成 chunk. 2024 新 paradigm. |
| **Hierarchical chunking** ⭐ | Embed 小 chunk (子), retrieval 时返回大 chunk (父). 精确召回 + 充足 context. |
| **Contextual retrieval** ⭐ | **Anthropic 2024.9 patent** — embed 前给每个 chunk 加 "这是 X 文档 Y 章节" 前缀. 报 +49% recall. |
| **Overlap** | 相邻 chunk 重叠 50-100 token, 防止信息被 cut off 在 chunk 边界. |
| **Atomic unit** | 不可切的最小单位. Tables / code blocks / equations 当 atomic. |

### Embedding / 检索 ⭐

| 术语 | 解释 |
|---|---|
| **Embedding** ⭐ | **Text → 高维向量** (1024 / 1536 / 3072 维). Cosine 距离 = semantic 相似度. |
| **Embedder / Embedding model** | 生成 embedding 的模型. 2026 主流: text-embedding-3-large (OpenAI) / Voyage-3 (Anthropic) / BGE-M3 (BAAI) / Cohere embed-v4. |
| **Dense retrieval** | 用 embedding 找相似 — semantic match 强 (paraphrase). 但抓不到 exact SKU / 人名. |
| **Sparse retrieval / BM25** | 关键词匹配算法. 跟 dense 互补 — exact match 强. |
| **Hybrid retrieval** ⭐ | **Dense + BM25 同时跑, RRF/weighted 合并**. 标准 production-grade, 比单一 +10pp recall. |
| **Reranker / cross-encoder** ⭐ | 第二阶段精排. Top-50 候选 → cross-encoder 重新打分 → top-10. 比 bi-encoder 准但贵. |
| **bge-reranker** | BAAI 开源 reranker. Self-host. |
| **Cohere Rerank** | Cohere 商业 reranker API. |
| **Cross-encoder vs Bi-encoder** | Bi-encoder: query / doc 分别 embed, 比较 (快但糙). Cross-encoder: query + doc 一起进 model, 共同评分 (准但慢). |
| **HyDE (Hypothetical Document Embeddings)** | LLM 先生成"假想答案", 用其 embedding 检索. 对模糊 query 有效. |
| **Query rewriting** | LLM 把 user query 改写更搜索友好 — "我退款多久" → "BNPL refund processing timeline". |
| **MMR (Maximal Marginal Relevance)** | 检索去重 — 不只取最相关, 还兼顾 diversity. 避免 top-10 都讲同一件事. |
| **Multi-vector retrieval** | 一个 doc 生成多个 embedding (按 aspect / 段). ColBERT 是代表. |
| **CLIP embedding** | 图文共享 embedding 空间 — 图查文 / 文查图. Multimodal RAG 用. |

### Vector DB / 索引

| 术语 | 解释 |
|---|---|
| **Vector DB** | 存 embedding + 支持 ANN 搜索的 DB. |
| **Qdrant** | Rust 写的开源 vector DB. Production 流行选择. |
| **Pinecone** | 商业 managed vector DB. 起步快. |
| **Weaviate** | 开源 vector DB, GraphQL API. |
| **Milvus** | 开源 vector DB. 大规模 production. |
| **ANN (Approximate Nearest Neighbor)** | 近似最近邻搜索算法 — HNSW / IVF 是常见. 没 ANN, 10M 向量比 cosine 要算 10M 次. |
| **HNSW (Hierarchical Navigable Small World)** | ANN 算法, 多层图结构. 速度准度好平衡. |

### Retrieval Metrics ⭐

| 术语 | 解释 |
|---|---|
| **Recall@K** ⭐ | **正确文档在 top-K 检索结果中的比例**. K=10 是 RAG 标准. |
| **NDCG@K (Normalized Discounted Cumulative Gain)** ⭐ | 加权排名好坏 — 正确答案靠前 score 高. 0-1 scale. |
| **MRR (Mean Reciprocal Rank)** | 第一个正确答案的倒数排名平均. 适合 "找到第一个对的就行" 场景. |
| **Precision@K** | Top-K 中相关的比例. 跟 recall 搭配看. |
| **Answer accuracy** | 端到端 — RAG 找对了 + LLM 生成对了. 真目标. |
| **Faithfulness** | LLM 输出是否 grounded 在 retrieved chunks. Hallucination 的反指标. |

### 文档处理工具

| 术语 | 解释 |
|---|---|
| **PyMuPDF** | Python PDF 解析库. |
| **pdfplumber** | 类似, 强于 table extraction. |
| **Unstructured.io** | 商业文档解析 — PDF / DOCX / HTML 统一成结构化输出. |
| **tree-sitter** | 多语言 syntax tree parser. AST-aware chunking 用. |
| **Markdown** | 轻量标记 — heading / table / code 容易识别, RAG 友好. |

---

## 这道题在考什么

表面是 chunking 题, 底下藏着 **8 个 FDE evaluation signal**:

1. **Data-shape awareness** — 知道 chunking strategy 取决于 customer's data shape, 不是 one-size-fits-all
2. **Ablation methodology** — 不是 "我选 512", 是 "我试了 5 种, 这是 winner with these numbers"
3. **Eval discipline** — Recall@10, NDCG@10, downstream answer accuracy
4. **Mixed-modality** — tables / code / figures 各自 atomic 处理
5. **Trade-off thinking** — small chunk = high precision low context, big chunk = opposite
6. **Embedding model awareness** — chunking 和 embed model 互动 (Voyage-3, BGE-M3, text-embedding-3-large)
7. **Production reality** — re-indexing cost, hot-reload, multi-tenant
8. **2026 advanced** — late-chunking, contextual retrieval, hierarchical chunks

不考「chunk size 是什么」, 考「你为什么选这个, 怎么知道是 winner, 数据变了怎么 adapt」.

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|---|---|---|
| 1 | **Data shape first** | 3 min | 问 customer 的 doc structure | "Before I choose strategy, I need to understand the data — PDFs are 5 different things (academic, contracts, technical, semi-structured, scanned)." |
| 2 | **4-strategy taxonomy** | 5 min | Fixed / Recursive / Semantic / Structure-aware | "4 main strategies — fixed-size, recursive character, semantic, structure-aware. Each has a data shape it fits." |
| 3 | **My choice + defense** | 4 min | Structure-aware recursive with fixed fallback | "I'd choose structure-aware recursive (heading + paragraph + sentence + char fallback) with table/code as atomic units." |
| 4 | **Ablation results** | 6 min | Concrete numbers from real eval | "Here's my ablation — 5 strategies × 200-query eval set. Structure-aware wins by 9pp on Recall@10 over fixed-size 512." |
| 5 | **Multi-modal handling** | 5 min | Tables / code / figures atomic | "Tables and code break naive chunkers. Treat them as atomic units with structural metadata." |
| 6 | **Chunk size decision** | 4 min | 256 vs 512 vs 1024 tradeoffs | "Default 512 + 64 overlap, but customize per use case. Long-context model + small chunks = best recent pattern." |
| 7 | **Embedding model interaction** | 3 min | Different models prefer different chunk sizes | "Embedding model affects chunk size — BGE-M3 vs Voyage-3 vs text-embedding-3-large have different optimal." |
| 8 | **2026 advanced patterns** | 4 min | Late-chunking, contextual retrieval, hierarchical | "Anthropic's contextual retrieval (Sept 2024) — prepend chunk-level context to each chunk before embedding. +49% recall." |
| 9 | **Re-eval cadence** | 2 min | How often to re-ablate | "Quarterly re-ablation, or when data shape changes (new doc type)." |
| 10 | **Quote BNPL RAG + ConvFinQA tables** | 4 min | Real shipped chunking | "BNPL: heading-aware on FAQs + tables atomic. ConvFinQA: table-aware chunker because financial tables span pages." |

---

## 详细回答

### Step 1: Why "default 512" is the wrong answer

```
Junior answer: "I use 512 tokens with 50 overlap"

Senior answer: "It depends on the data. Let me walk through:
  - Are the docs structured (headings)? → heading-aware
  - Mostly tables? → table-aware atomic
  - Code-heavy? → AST-aware
  - Mixed? → structure-aware recursive with type detection
  - Long unstructured prose? → semantic chunking
  
And then I'd ablate 3-5 strategies on a 200-query eval set 
to confirm before committing."
```

### Step 2: 4 chunking strategies — taxonomy

**Strategy 1: Fixed-size**

```python
def fixed_chunk(text, size=512, overlap=64):
    """Simplest, character / token count based."""
    chunks = []
    for i in range(0, len(text), size - overlap):
        chunks.append(text[i:i+size])
    return chunks
```

**Pros**: Simple, predictable, fast.
**Cons**: Breaks mid-sentence, mid-table, mid-code-block. Loses structure.
**Best for**: Uniform plain-text corpora (forum posts, transcripts).

**Strategy 2: Recursive character**

```python
def recursive_chunk(text, separators=['\n\n', '\n', '. ', ' '], max_size=512):
    """Try larger separator first, recurse to smaller."""
    for sep in separators:
        parts = text.split(sep)
        if all(len(p) <= max_size for p in parts):
            return parts
    # Last resort: hard char split
    return [text[i:i+max_size] for i in range(0, len(text), max_size)]
```

**Pros**: Preserves natural boundaries (paragraph / sentence / word).
**Cons**: Doesn't understand document structure.
**Best for**: Long-form prose (articles, books).

**Strategy 3: Semantic chunking**

```python
async def semantic_chunk(text, embedding_model, threshold=0.7):
    """Chunk based on embedding similarity."""
    sentences = sent_tokenize(text)
    embeddings = await embed_batch(sentences)
    
    chunks = [[sentences[0]]]
    for i in range(1, len(sentences)):
        sim = cosine(embeddings[i-1], embeddings[i])
        if sim < threshold:  # topic shift
            chunks.append([sentences[i]])
        else:
            chunks[-1].append(sentences[i])
    
    return [' '.join(c) for c in chunks]
```

**Pros**: Adapts to content structure semantically.
**Cons**: Expensive (embed every sentence), threshold tuning, can produce uneven chunks.
**Best for**: Topic-shifting docs (interview transcripts, multi-topic articles).

**Strategy 4: Structure-aware (best for most production)**

```python
def structure_aware_chunk(doc):
    """Use document structure (headings, tables, code blocks)."""
    chunks = []
    
    for section in parse_markdown_sections(doc):  # or PDF section detection
        if section.type == 'heading':
            current_heading = section.text
            continue
        
        if section.type == 'table':
            # Tables atomic — preserve as single chunk
            chunks.append(Chunk(
                text=section.markdown,
                type='table',
                heading=current_heading,
                metadata={'rows': section.row_count, 'cols': section.col_count}
            ))
            continue
        
        if section.type == 'code':
            # Code atomic — preserve as single chunk
            chunks.append(Chunk(
                text=section.text,
                type='code',
                heading=current_heading,
                metadata={'language': section.language}
            ))
            continue
        
        if section.type == 'paragraph':
            # Recursive split within paragraph if too long
            sub_chunks = recursive_chunk(section.text, max_size=512)
            for sc in sub_chunks:
                chunks.append(Chunk(
                    text=sc,
                    type='text',
                    heading=current_heading,
                    parent_section=section.section_id
                ))
    
    return chunks
```

**Pros**: Preserves structural meaning. Tables / code stay intact.
**Cons**: Requires document parser (PDF, DOCX, MD).
**Best for**: Technical docs, manuals, mixed-format enterprise content.

### Step 3: My choice — structure-aware recursive with fixed fallback

**For the customer's data (PDFs with sections, tables, code, figures)**:

```python
class ProductionChunker:
    """Structure-aware with multi-modal handling + fallback."""
    
    def __init__(self):
        self.target_size = 512
        self.overlap = 64
        self.table_max_rows = 50  # large tables get summarized
        self.code_max_lines = 100
    
    def chunk_pdf(self, pdf_path):
        # Step 1: Parse PDF with structure detection
        doc = pdf_parser.parse(pdf_path)  # using PyMuPDF / pdfplumber / unstructured
        
        chunks = []
        
        for page in doc.pages:
            for element in page.elements:
                if element.type == 'heading':
                    self.current_heading = element.text
                    self.current_section_id = element.section_id
                
                elif element.type == 'table':
                    chunks.extend(self._chunk_table(element))
                
                elif element.type == 'code':
                    chunks.extend(self._chunk_code(element))
                
                elif element.type == 'figure':
                    chunks.append(self._chunk_figure(element))
                
                elif element.type == 'paragraph':
                    chunks.extend(self._chunk_text(element.text))
        
        return chunks
    
    def _chunk_table(self, table_element):
        """Tables atomic, with metadata."""
        if table_element.row_count <= self.table_max_rows:
            return [Chunk(
                text=table_element.markdown,  # convert to markdown table
                type='table',
                heading=self.current_heading,
                section_id=self.current_section_id,
                metadata={
                    'rows': table_element.row_count,
                    'cols': table_element.col_count,
                    'columns': table_element.column_headers,
                    'page': table_element.page_num,
                }
            )]
        else:
            # Large table: split by row groups + include header context
            chunks = []
            header_row = table_element.rows[0]
            for i in range(1, len(table_element.rows), self.table_max_rows):
                row_group = table_element.rows[i:i+self.table_max_rows]
                chunk_md = render_markdown_table([header_row] + row_group)
                chunks.append(Chunk(
                    text=chunk_md,
                    type='table_segment',
                    heading=self.current_heading,
                    metadata={'row_range': f"{i}-{i+len(row_group)}", 'total_rows': table_element.row_count}
                ))
            return chunks
    
    def _chunk_code(self, code_element):
        """Code atomic, AST-aware for long files."""
        if code_element.line_count <= self.code_max_lines:
            return [Chunk(
                text=code_element.text,
                type='code',
                heading=self.current_heading,
                metadata={'language': code_element.language}
            )]
        else:
            # Long code: split by function / class boundaries (AST-aware)
            return ast_aware_split(code_element)
    
    def _chunk_figure(self, figure_element):
        """Figures: caption + alt text + image embedding (multimodal RAG)."""
        return Chunk(
            text=figure_element.caption + ' ' + figure_element.alt_text,
            type='figure',
            heading=self.current_heading,
            metadata={
                'image_path': figure_element.image_path,
                'multimodal_embedding': True,  # use CLIP / similar
            }
        )
    
    def _chunk_text(self, text):
        """Recursive paragraph splitting."""
        if len(text) <= self.target_size:
            return [Chunk(
                text=text,
                type='text',
                heading=self.current_heading,
                section_id=self.current_section_id,
            )]
        
        # Recursive split: paragraph → sentence → char
        sub_chunks = recursive_split(text, self.target_size, self.overlap)
        return [Chunk(
            text=sc,
            type='text',
            heading=self.current_heading,
            section_id=self.current_section_id,
            metadata={'split_within_paragraph': True}
        ) for sc in sub_chunks]
```

### Step 4: Ablation results — defending the choice with numbers

```
Eval setup:
  Corpus: 500 customer PDFs (financial reports, technical docs, contracts)
  Queries: 200 stratified (factoid / list / multi-hop / table-lookup / code)
  Embedder: text-embedding-3-large
  Retriever: dense + BM25 + bge-reranker top-50 → 10
  Metrics: Recall@10, NDCG@10, downstream answer accuracy (LLM-judge)
  
Strategies tested:
  1. Fixed 512 + 50 overlap
  2. Fixed 1024 + 100 overlap
  3. Recursive (paragraph → sentence → char) 512
  4. Semantic (sentence-level threshold 0.7)
  5. Structure-aware (my choice)
  6. Structure-aware + table-atomic
  7. Structure-aware + table-atomic + contextual prefix
```

**Results**:

| Strategy | Recall@10 | NDCG@10 | Answer Acc | Latency (ms) | Index Size |
|---|---|---|---|---|---|
| 1. Fixed 512 | 67% | 0.62 | 71% | 32 | 1.0x |
| 2. Fixed 1024 | 71% | 0.65 | 74% | 35 | 0.5x |
| 3. Recursive 512 | 73% | 0.68 | 75% | 38 | 1.0x |
| 4. Semantic | 70% | 0.64 | 73% | 45 | 1.2x |
| 5. Structure-aware | 76% | 0.71 | 78% | 42 | 0.9x |
| 6. + Table-atomic | 81% | 0.74 | 82% | 44 | 0.95x |
| 7. + Contextual prefix | 87% | 0.79 | 86% | 48 | 1.1x |

**Why winner wins**:
- Structure-aware (5): preserves heading context, knows section boundaries
- + Table-atomic (6): table queries had broken results with naive chunkers — fixed by atomic tables (+5pp recall)
- + Contextual prefix (7): Anthropic's pattern — prepend "This chunk is from {section} of {doc} about {topic}" — embeds with context, retrieves better (+6pp recall)

**Critical**: Don't trust offline metrics alone. **Run on production-shaped queries**, measure downstream answer accuracy (not just retrieval).

### Step 5: Multi-modal handling specifics

**Tables**:

```python
# Problem: naive chunker breaks tables mid-row
"Year | Revenue | Profit
2022  | $10M    | $2M
2023  | $12M    | $3M  ← chunk boundary here
2024  | $15M    | $4M"

# Result: chunk 1 has header + 2 rows, chunk 2 has 2 rows without header
# Query "2024 revenue" retrieves chunk 2, but no column headers → useless

# Solution: tables atomic + include header in every fragment if must split
```

**Code**:

```python
# Problem: naive chunker breaks functions mid-definition
def calculate_refund(order_id):
    """Long function body..."""
    # ... 50 lines ...
    return refund_amount  ← chunk boundary in middle

# Solution: AST-aware (Python tree-sitter, similar for other languages)
# Each function / class is its own chunk
```

**Figures + Diagrams**:

```python
# Caption + alt text + image embedding (multimodal RAG)
chunk = {
    'text': 'Figure 3: Architecture diagram showing payment flow with vendor handoffs',
    'image_path': 's3://bucket/figures/fig3.png',
    'multimodal_embedding': clip_embedding(image_path),
    'type': 'figure',
}
```

**Math equations**:

```python
# LaTeX preserved as atomic units
chunk = {
    'text': 'Refund formula: refund = principal × (1 - fee_rate)^days',
    'latex': r'r = P \cdot (1 - f)^d',
    'type': 'equation',
}
```

### Step 6: Chunk size decision

```
Small chunks (256 tokens):
  + Precise retrieval (only relevant content)
  + Cheaper embed cost
  - Limited context per chunk (model may need to chain)
  - More chunks → larger index
  
  Best for: factoid queries, dense corpora
  
Medium chunks (512 tokens):
  + Balance precision and context
  + Default for most RAG
  
  Best for: general-purpose RAG
  
Large chunks (1024-2048 tokens):
  + More context per retrieval (less chaining)
  + Better for complex queries
  - Less precise (more noise in chunk)
  - Slower / more expensive
  
  Best for: long-context model (Gemini 3 Pro 2M, Claude Opus 4.7 1M)
            where you can feed many large chunks
```

**2026 pattern: small chunks + long-context model**

```python
# Retrieve top-50 small chunks (256 tokens each = 12.8k tokens)
# Feed all 50 into long-context Sonnet 4.6 / Opus 4.7
# Model reasons over full retrieved set, picks best info

chunks = await rag.retrieve(query, chunk_size=256, top_k=50)
context = '\n\n'.join([f"[Chunk {i}]: {c.text}" for i, c in enumerate(chunks)])

response = await opus_47.generate(
    f"Using the following retrieved chunks, answer: {query}\n\n{context}"
)
```

**Why this wins**: precision (small chunks find specific facts) + reasoning (long-context model digests all of them).

### Step 7: Embedding model interaction

| Embedder | Optimal chunk size | Notes |
|---|---|---|
| **text-embedding-3-large** (OpenAI) | 256-512 tokens | Trained on chunk-level text |
| **Voyage-3** (Anthropic) | 512-1024 tokens | Strong at longer context |
| **BGE-M3** (BAAI) | 256-512 tokens | Multilingual, good for non-English |
| **Cohere embed-v4** | 512 tokens | Multilingual + reranker pairing |
| **multilingual-e5-large** | 384 tokens | Hugging Face, multilingual |

**Test pattern**: same chunk → embed with 3 models → cosine to query → which best correlates with human relevance label?

### Step 8: 2026 advanced patterns

**1. Anthropic Contextual Retrieval (Sept 2024)**

```python
# Add chunk-level context before embedding
def add_context_prefix(chunk, doc, llm):
    prompt = f"""
    Document: {doc.title}
    
    Chunk: {chunk.text}
    
    Write a 1-2 sentence context describing this chunk's location 
    and topic in the document. Don't restate the chunk content.
    """
    context = llm.generate(prompt)
    return f"Context: {context}\n\n{chunk.text}"

# Reported: +49% recall on Anthropic's eval
```

**2. Late chunking (sentence-level embeddings, dynamic chunking)**

```python
# Embed sentences, retrieve at sentence level, dynamically form chunks at query time
sentences = sent_tokenize(doc)
sentence_embeddings = embed_batch(sentences)

# At query time
query_emb = embed(query)
top_sentences = top_k_by_sim(query_emb, sentence_embeddings, k=20)

# Group adjacent sentences into chunks
chunks = group_adjacent(top_sentences, window=3)
```

**3. Hierarchical chunks (parent / child)**

```python
# Embed small chunks (children) but return parent (paragraph) for context
class HierarchicalChunk:
    parent_text: str  # paragraph, 1024 tokens
    children: list[str]  # sentences, 64 tokens each
    
# Retrieve children, but return parent_text for generation
def retrieve(query, top_k=10):
    child_matches = embedding_search(query, level='child', top_k=top_k*3)
    # Dedupe by parent
    parents = unique([c.parent for c in child_matches])[:top_k]
    return parents  # Generator sees larger context
```

**4. HyDE (Hypothetical Document Embeddings)**

```python
async def hyde_retrieve(query):
    # Generate hypothetical answer
    hypothetical = await haiku_45.generate(
        f"Write 2 paragraphs that would answer: {query}"
    )
    # Embed and search by hypothetical
    return embed_and_search(hypothetical, top_k=10)
```

**5. Query rewriting**

```python
async def rewrite_query(query):
    """Rewrite for better retrieval."""
    return await haiku_45.generate(f"""
    Rewrite this query to maximize retrieval recall:
    Original: {query}
    
    Add likely keywords. Expand abbreviations. Make specific.
    """)
```

---

## 关键决策 / 框架

### Decision tree (data shape → strategy)

```
What's the data?
   │
   ├── Plain prose (articles, books, transcripts)
   │   → Recursive character (paragraph → sentence → char)
   │   → 512 + 64 overlap default
   │
   ├── Structured documents (manuals, technical docs)
   │   → Structure-aware (heading-based)
   │   → Tables / code / figures atomic
   │
   ├── Code repositories
   │   → AST-aware (per function / class)
   │   → Include imports / file path context
   │
   ├── PDFs with mixed content
   │   → Structure-aware + multi-modal handling
   │   → Tables atomic, figures with caption+alt, equations preserved
   │
   ├── Conversational data (chat logs)
   │   → Per-turn or per-thread
   │   → Maintain speaker / timestamp metadata
   │
   ├── Tabular data (CSV, spreadsheets)
   │   → Per-row chunking with column headers
   │   → Or row-group chunks with summary stats
   │
   └── Heterogeneous (mixed everything)
       → Type detection + multi-strategy
```

### Ablation methodology

```
1. Build representative eval set (200 queries, stratified by type)
2. Define metrics:
   - Recall@10 (did we retrieve any relevant chunks?)
   - NDCG@10 (ranked correctly?)
   - Downstream answer accuracy (LLM-judge or human)
3. Test 3-5 strategies in parallel
4. Statistical significance check (paired t-test on recall)
5. Cost / latency trade-off
6. Winner = best answer accuracy at acceptable cost/latency
7. Document for future re-eval
```

### Re-eval triggers

```
- Quarterly default
- Customer adds new document type
- New embedding model release
- Chunk recall regression detected in production
- Customer complaint about retrieval quality
```

---

## 完整代码 / 架构图

### Full chunking pipeline

```python
# chunking/pipeline.py

from typing import Iterator
import re

class ChunkingPipeline:
    def __init__(self, config):
        self.config = config
        self.parsers = {
            'pdf': PDFParser(),
            'html': HTMLParser(),
            'markdown': MarkdownParser(),
            'docx': DocxParser(),
            'code': CodeParser(),
        }
        self.embedder = init_embedder(config.embedding_model)
        self.context_llm = init_llm(config.context_model)  # Haiku 4.5 for cheap context generation
    
    async def index_document(self, doc_path: str, tenant_id: str) -> int:
        """Full pipeline: parse → chunk → enrich → embed → store."""
        # 1. Parse
        doc_type = detect_doc_type(doc_path)
        parser = self.parsers[doc_type]
        doc = parser.parse(doc_path)
        
        # 2. Chunk (structure-aware)
        chunks = self._chunk_document(doc)
        
        # 3. Enrich with contextual prefix (Anthropic pattern)
        chunks_with_context = await self._add_contextual_prefix(chunks, doc)
        
        # 4. Embed (parallel)
        embeddings = await self._embed_chunks(chunks_with_context)
        
        # 5. Store in vector DB + metadata DB
        await self._store(chunks_with_context, embeddings, tenant_id)
        
        return len(chunks_with_context)
    
    def _chunk_document(self, doc):
        chunks = []
        current_heading = None
        section_path = []  # heading hierarchy
        
        for element in doc.iter_elements():
            if element.type == 'heading':
                # Update heading hierarchy
                section_path = section_path[:element.level - 1] + [element.text]
                continue
            
            if element.type == 'table':
                chunks.extend(self._chunk_table(element, section_path))
            
            elif element.type == 'code':
                chunks.extend(self._chunk_code(element, section_path))
            
            elif element.type == 'figure':
                chunks.append(self._chunk_figure(element, section_path))
            
            elif element.type == 'paragraph':
                chunks.extend(self._chunk_paragraph(element, section_path))
            
            elif element.type == 'list':
                chunks.append(self._chunk_list(element, section_path))
        
        return chunks
    
    async def _add_contextual_prefix(self, chunks, doc):
        """Anthropic contextual retrieval — prepend chunk context."""
        enriched = []
        for chunk in chunks:
            # Generate context (cheap LLM call, Haiku 4.5)
            context_prompt = f"""
            Document title: {doc.title}
            Section: {' > '.join(chunk.section_path)}
            
            Chunk: {chunk.text[:1000]}...
            
            Write a 1-2 sentence context describing where this chunk is
            in the document and what it covers (don't restate content).
            """
            
            context = await self.context_llm.generate(context_prompt)
            
            enriched.append(Chunk(
                text=f"{context}\n\n{chunk.text}",  # context prepended for embedding
                display_text=chunk.text,  # for retrieval result (no context)
                type=chunk.type,
                metadata={**chunk.metadata, 'context': context}
            ))
        
        return enriched
    
    async def _embed_chunks(self, chunks):
        batch_size = 100
        embeddings = []
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            batch_emb = await self.embedder.embed_batch([c.text for c in batch])
            embeddings.extend(batch_emb)
        return embeddings
    
    async def _store(self, chunks, embeddings, tenant_id):
        for chunk, emb in zip(chunks, embeddings):
            await self.vector_db.upsert(
                id=chunk.id,
                vector=emb,
                payload={
                    'tenant_id': tenant_id,  # ACL filter
                    'text': chunk.display_text,
                    'type': chunk.type,
                    'doc_id': chunk.doc_id,
                    'section_path': chunk.section_path,
                    'page': chunk.page,
                    **chunk.metadata,
                }
            )
```

### Retrieval with chunk-type awareness

```python
async def retrieve_with_type_aware_rerank(query, tenant_id, top_k=10):
    """Retrieve and rerank with chunk-type-specific scoring."""
    
    # 1. Detect query type
    query_type = await classify_query_type(query)  # 'factoid', 'table_lookup', 'code', 'list'
    
    # 2. Hybrid retrieve (more candidates than needed)
    query_emb = await embed(query)
    
    # Dense
    dense_results = await vector_db.search(
        vector=query_emb,
        filter={'tenant_id': tenant_id},
        top_k=100
    )
    
    # Sparse (BM25)
    sparse_results = await es.search(query=query, top_k=100, filter={'tenant_id': tenant_id})
    
    # 3. RRF fusion
    fused = reciprocal_rank_fusion([dense_results, sparse_results])
    
    # 4. Chunk-type-aware rerank
    if query_type == 'table_lookup':
        # Boost table chunks
        fused = [(c, s * 1.5 if c.type == 'table' else s) for c, s in fused]
        fused.sort(key=lambda x: -x[1])
    
    if query_type == 'code':
        # Boost code chunks
        fused = [(c, s * 1.5 if c.type == 'code' else s) for c, s in fused]
    
    # 5. Cross-encoder rerank top-50 → 10
    candidates = [c for c, _ in fused[:50]]
    rerank_scores = await reranker.score([(query, c.text) for c in candidates])
    
    final = sorted(zip(candidates, rerank_scores), key=lambda x: -x[1])[:top_k]
    
    return [c for c, _ in final]
```

### Architecture diagram

```
                    ┌──────────────────────────────────────┐
                    │   Customer PDF / DOCX / Code / HTML  │
                    └────────────────┬─────────────────────┘
                                     │
                                     ▼
                    ┌──────────────────────────────────────┐
                    │      DOCUMENT PARSER                 │
                    │  PyMuPDF / pdfplumber / unstructured │
                    └────────────────┬─────────────────────┘
                                     │
                  ┌──────────────────┼──────────────────┐
                  │                  │                  │
                  ▼                  ▼                  ▼
        ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
        │   Text + Headings│ │   Tables         │ │   Code blocks    │
        └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
                 │                    │                    │
                 ▼                    ▼                    ▼
        ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
        │ Recursive split  │ │  Atomic chunks   │ │  AST-aware split │
        │ paragraph→sent   │ │  with metadata   │ │  per function    │
        └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
                 │                    │                    │
                 └────────────────────┼────────────────────┘
                                      │
                                      ▼
                    ┌──────────────────────────────────────┐
                    │   CONTEXTUAL PREFIX                  │
                    │  (Anthropic 2024 pattern, +49%)      │
                    │  Haiku 4.5 generates 1-2 sent context│
                    └────────────────┬─────────────────────┘
                                     │
                                     ▼
                    ┌──────────────────────────────────────┐
                    │   EMBEDDING                          │
                    │  text-embedding-3-large /            │
                    │  Voyage-3 / BGE-M3                   │
                    └────────────────┬─────────────────────┘
                                     │
                                     ▼
                    ┌──────────────────────────────────────┐
                    │   STORAGE                            │
                    │  Vector DB (Qdrant / Pinecone)       │
                    │  + Metadata DB (Postgres)            │
                    │  + BM25 index (Elasticsearch)        │
                    └──────────────────────────────────────┘
```

---

## Gao Xin 简历专属 reframe

### BNPL chatbot RAG — heading-aware + table-atomic

**S**: BNPL chatbot needed FAQ + policy doc RAG. Customer FAQs are markdown with H2 sections per topic. Policy docs are PDFs with tables (refund matrix, fee schedule).

**T**: Choose chunking that gets 90%+ recall on both FAQ queries and policy queries.

**A**: Structure-aware:
- FAQs: chunk by H2 section (one Q+A per chunk)
- Policy PDFs: structure-aware parsing, tables atomic
- All chunks include parent heading + doc title in context prefix (Anthropic pattern)
- Ablation: 3 strategies × 200 queries → structure-aware + table-atomic +18pp recall over fixed 512

**R**:
- Recall@10: 67% → 85% (fixed → structure-aware) → 92% (+ contextual prefix)
- Downstream answer accuracy 70% → 88%
- Documented ablation in customer-facing doc

### ConvFinQA — table-aware chunker

**S**: Financial 10-K filings with tables that span pages. Naive chunkers break tables, query "2023 Q4 revenue" returns chunk with rows but no column headers.

**T**: Make tables atomic, include column headers in every fragment.

**A**: Custom table chunker:
- Detect table boundaries in PDF
- Treat as atomic if < 50 rows
- If > 50 rows: split by row groups, include header in every fragment
- Markdown representation (LLM reads better than raw text)
- Metadata: column names, row range, page number

**R**:
- Table-lookup query accuracy 45% → 78%
- Multi-hop queries (combining table + text) +12pp
- Part of 9-variant ablation (you ran)

### Voice agent multilingual RAG

**S**: 7-market voice agent. Per-market policy docs in local language. Different language has different document conventions.

**T**: Multilingual chunking + embedding strategy.

**A**:
- BGE-M3 embedder (multilingual, strong on Asian languages)
- Per-market index (tenant filter)
- Indonesia / Vietnam / Thai docs: structure-aware on H2 sections
- Brazil / Mexico: Portuguese/Spanish-specific tokenizer
- Pakistan: Urdu/English mixed, special handling

**R**:
- Multilingual recall@10 above 80% for all 7 markets
- BGE-M3 outperformed text-embedding-3-large by 9pp on Indonesian queries

---

## 5 个 Follow-ups

**Q1**: "Why not just use a long-context model (Gemini 3 Pro 2M) and skip chunking?"

**A**: Depends on corpus size and access patterns:
- **Long-context wins** when: corpus < 1M tokens, static, low query volume. E.g., "analyze this 200-page contract."
- **RAG (chunked) wins** when: corpus > 1M tokens, dynamic, high query volume, multi-tenant, cost-sensitive.
- **Cost math**: Gemini 3 Pro 2M at $2/M input → $4/query naively. RAG retrieves 5k → $0.01/query. **400x cheaper** for production volume.
- **Hybrid (best 2026 pattern)**: chunk small (256 tokens), retrieve top-50 (12k tokens), feed all into long-context model. Best precision (small chunks find specifics) + best reasoning (long-context digests all). This is what we're testing at BNPL.

**Q2**: "What about chunk overlap — how much and why?"

**A**:
- **Standard**: 10-20% overlap (50-100 tokens on 512-token chunks)
- **Rationale**: queries that need context spanning a chunk boundary still hit at least one chunk with full context
- **Trade-off**: more overlap = more storage cost + more redundant chunks retrieved (need dedupe)
- **No overlap if**: structure-aware chunking already preserves boundaries (e.g., per-heading chunks rarely have query-spanning issue)
- **Higher overlap for**: dense factoid corpora where exact phrase matters

**Q3**: "How do you handle multi-language documents?"

**A**: Per-language chunking + multilingual embedder:
1. **Detect language** per document (or per section if mixed)
2. **Language-specific tokenizer**: Chinese / Japanese / Korean need character-level or BPE-tuned tokenizers
3. **Multilingual embedder**: BGE-M3, multilingual-e5-large, Cohere embed-v4 (all strong)
4. **Per-language eval set**: chunk strategy that works for English may fail for Thai (no whitespace word boundary)
5. **Cross-lingual retrieval**: BGE-M3 enables querying in English, retrieving in Indonesian — useful for multi-market BNPL

**Q4**: "Customer's data updates daily. How do you handle re-chunking and re-indexing?"

**A**: Hot-reload pipeline:
1. **Change detection**: file watcher / webhook on doc updates
2. **Delta indexing**: only re-chunk changed documents (not full re-index)
3. **Version control**: keep old + new chunk versions, point retriever to "active" version
4. **Chunk-level diff**: if doc updated, identify which sections changed (heading-aware), re-chunk only changed sections
5. **Atomic swap**: after delta indexed, swap retriever pointer (zero-downtime)
6. **Background full re-index**: weekly cron, validates incremental indexing didn't drift
7. **Eval gate**: after re-index, run smoke eval (10 queries), block deploy if regression

**Q5**: "What metrics do you use to know your chunking is working in production?"

**A**: 5 metrics:
1. **Recall@K**: golden query set, % top-K contains relevant chunks
2. **NDCG@K**: ranked correctly (relevant chunks higher)
3. **Downstream answer accuracy**: LLM-judge on full RAG pipeline
4. **Citation precision**: chunks cited in response actually contain claimed info
5. **Latency p99**: retrieval + rerank time

**Drift monitoring**:
- Per-query-type recall (factoid vs table-lookup vs multi-hop)
- "I don't know" response rate (spike = retrieval failing)
- User feedback on factual accuracy
- Manually-sampled production queries audited weekly

---

## ❌ 死路答法

1. **"I use 512 chunks with 50 overlap"** — no justification
2. **No mention of multi-modal** (tables, code, figures) — naive chunker breaks these
3. **No ablation** — "I picked it because LangChain default"
4. **Skip eval methodology** — recall and NDCG are basic, must include downstream answer accuracy
5. **Forget hierarchical** — long docs need parent / child relationship
6. **Same embedding model for all data** — multilingual / multi-modal need different
7. **No re-index strategy** — production data updates, can't ignore
8. **Ignore long-context model 2026** — Gemini 3 Pro / Claude Opus 4.7 change calculus
9. **No contextual retrieval awareness** — Anthropic 2024 paper +49% recall
10. **No data-shape dependency** — "this strategy is best" without considering customer's actual data

---

## ✅ 加分项

1. **Data-shape decision tree** (PDF vs code vs prose vs tabular)
2. **5-strategy ablation table** with concrete numbers (Recall@10, NDCG, answer accuracy)
3. **Multi-modal specificity** (tables atomic, code AST-aware, figures multimodal)
4. **Contextual retrieval** (Anthropic 2024, +49% recall pattern)
5. **Embedding model interaction** (BGE-M3 vs text-embedding-3-large vs Voyage-3)
6. **Long-context hybrid** (small chunks + Gemini 3 Pro 2M for reasoning)
7. **Re-index / hot-reload** (production reality)
8. **Eval discipline** (downstream answer accuracy not just retrieval)
9. **Quote BNPL FAQ + ConvFinQA tables + multilingual voice agent**
10. **Re-eval trigger** clarity (quarterly, new doc type, etc.)

---

## 一句话总结

> **Chunking strategy is data-shape-dependent — there's no "best 512." Defend with ablation (5 strategies × 200-query eval set), measure downstream answer accuracy not just retrieval. Structure-aware + table-atomic + contextual prefix (Anthropic 2024) is the 2026 default for mixed enterprise PDFs. Re-eval quarterly + on new doc types.**

---

## Cheat Sheet

```
4 chunking strategies:
  1. Fixed-size: simple, uniform data
  2. Recursive character: preserves natural boundaries
  3. Semantic: embedding-based topic shifts
  4. Structure-aware: best for production (heading/table/code aware)

Decision tree by data shape:
  - Prose → recursive 512+64
  - Structured docs → structure-aware + multi-modal
  - Code → AST-aware
  - Tables → atomic
  - Mixed PDFs → structure-aware + type detection

Default for mixed enterprise data:
  - Structure-aware recursive (heading → paragraph → sentence)
  - Tables atomic (with column headers preserved)
  - Code atomic (or AST-split if long)
  - Figures: caption + alt text + multimodal embedding
  - 512 tokens + 64 overlap default

Chunk size:
  256: precise, factoid-heavy
  512: balance (default)
  1024: more context, less precision
  
  2026 pattern: small chunks (256) + long-context model = best

Embedding model interaction:
  text-embedding-3-large: 256-512 optimal
  Voyage-3: 512-1024
  BGE-M3: 256-512, multilingual
  Cohere embed-v4: 512, multilingual+rerank pair

Ablation methodology:
  1. 200-query eval set (stratified)
  2. 3-5 strategies in parallel
  3. Metrics: Recall@10, NDCG@10, answer accuracy
  4. Statistical significance check
  5. Cost / latency tradeoff
  6. Winner = best answer accuracy at acceptable cost

2026 advanced:
  - Contextual retrieval (Anthropic): prepend context, +49% recall
  - Late chunking: sentence-level, dynamic
  - Hierarchical: embed children, return parent
  - HyDE: hypothetical answer, embed it, retrieve
  - Query rewriting: LLM expands query

Multi-modal:
  Tables: atomic with column headers, markdown rep
  Code: AST-aware per function/class
  Figures: caption + alt + CLIP embedding
  Equations: preserve LaTeX

Production:
  Hot-reload: file watcher → delta chunk → atomic swap
  Eval gate: smoke test on every re-index
  Per-tenant index (multi-tenant)
  Quarterly re-ablation

Anti-patterns:
  - "Use 512, that's the default"
  - No ablation
  - Naive table handling
  - No long-context awareness
  - Skip contextual retrieval (Anthropic 2024)
  - Same embedder for all languages

Case studies:
  - BNPL: heading-aware on FAQ + table-atomic on policy, 67→92% recall
  - ConvFinQA: custom table chunker, 45→78% on table queries
  - Voice agent: BGE-M3 per-language, +9pp on Indonesian

Quotes for interview:
  - "Chunking is data-shape-dependent, no default 'best'"
  - "Ablate 3-5 strategies, measure downstream accuracy"
  - "Tables / code / figures must be atomic units"
  - "Contextual retrieval (Anthropic 2024) gives +49% recall"
  - "Small chunks + long-context model is the 2026 hybrid"
  - "Re-eval quarterly + on new doc types"
```
