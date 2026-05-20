## 题目

> "You're indexing 10K technical PDFs (each 50-500 pages) for RAG. How do you **chunk** them? Walk through your decision tree and the failure modes of naive approaches."

或追问形态:

> "RAG recall drops 20% when you change chunking from 512 tokens to 1024. Why? When is each better?"

**Round**: RAG Pipeline Design (45 min)

---

## 这道题在考什么

考你**chunking is non-trivial** awareness + production choices:

1. **Naive fail modes** —— fixed-size 切到句中, semantic cut wrong
2. **Strategy choice** —— sentence / paragraph / heading-aware / late chunking
3. **Overlap rationale** —— 防止 boundary 信息丢
4. **Size vs precision** —— 大 chunk 信息全, 小 chunk 精确
5. **Multi-modal awareness** —— tables / code / figures 不同处理

---

## 必问 clarifying

**1. Document structure**

> "PDFs have headings / hierarchy / TOC? Or unstructured prose? Different strategy."

**2. Content mix**

> "Text-only or includes tables, code blocks, figures, formulas?"

**3. Query type**

> "Users ask about facts ('what's the rated voltage of X') or concepts ('how does Y work')?"

**4. Embedding model**

> "What model? Max context (512 / 8192)? Different chunking max size."

**5. Update frequency**

> "Reindex monthly OK or daily reindex needed (affects chunk granularity)?"

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify structure + content mix + query type |
| 5-15 min | Strategy decision tree |
| 15-25 min | Overlap + metadata enrichment |
| 25-35 min | Multi-modal handling (tables / code) |
| 35-45 min | Eval + tuning |

---

## 我会这样答（sample）

> "Clarify — *[假设: PDFs are technical manuals with headings + tables + code, queries are fact-lookup + concept-explanation, embedding model with 8K context window, daily reindex possible]*.
>
> **5 chunking strategies — decision tree**:
>
> | Strategy | When | Avg chunk size |
> |---|---|---|
> | **Fixed-size + overlap** | Unstructured text, baseline | 512 tokens, 50 overlap |
> | **Sentence-aware** | Better than fixed, respects sentence | 5-10 sentences |
> | **Paragraph / section** | Doc has structure | 200-800 tokens |
> | **Heading-aware (recursive)** | Hierarchical doc | Variable, by section |
> | **Late chunking** | Long-context model | Embed first, then chunk |
>
> **My choice for this corpus**: **heading-aware recursive** with **fallback to fixed-size + overlap** for unstructured sections.
>
> **Algorithm**:
>
> ```python
> def chunk_doc(doc, max_size=512, overlap=50):
>     # 1. Parse hierarchical structure
>     sections = parse_headings(doc)  # tree: chapter → section → para
>     
>     chunks = []
>     for section in sections:
>         if estimate_tokens(section.text) <= max_size:
>             # Fits in 1 chunk, preserve as-is
>             chunks.append(Chunk(
>                 text=section.text,
>                 metadata={'heading_path': section.path, ...},
>             ))
>         else:
>             # Too big, recursively split at sub-heading
>             if section.subsections:
>                 chunks.extend([chunk_doc(s, max_size) for s in section.subsections])
>             else:
>                 # Leaf section too big, fall back to fixed-size with overlap
>                 chunks.extend(fixed_size_chunk(section.text, max_size, overlap))
>     return chunks
> ```
>
> **Why heading-aware**:
> - Preserves semantic boundary (chapter / section)
> - Heading path becomes metadata for filtering
> - Heading + content combined for embedding context
>
> **Why overlap (50 tokens)**:
> - Borderline information not lost at chunk seam
> - Trade-off: more storage cost, more chunks to embed
> - Typical 10% overlap is sweet spot
>
> **Metadata enrichment** (crucial for retrieval quality):
>
> ```python
> Chunk(
>     text='...',
>     embedding=embed('Heading: X.Y\nContent: ' + text),
>     metadata={
>         'doc_id': ...,
>         'doc_title': ...,
>         'heading_path': ['Chapter 5', 'Section 3', 'Subsection 2'],
>         'chunk_index': 23,
>         'total_chunks': 80,
>         'updated_at': ...,
>         'page_range': (45, 47),
>         'tags': ['installation', 'troubleshooting'],
>     },
> )
> ```
>
> Embedding includes heading context → better semantic representation.
>
> **Multi-modal handling**:
>
> | Content | Strategy |
> |---|---|
> | **Tables** | Don't chunk in middle of table; capture as 1 chunk + Markdown serialize for LLM readability |
> | **Code blocks** | Atomic unit, don't split function in middle |
> | **Figures** | Extract caption + alt text; image embed separately if vision-RAG |
> | **Formulas** | LaTeX → text representation in chunk |
> | **Lists** | Bullet list as 1 chunk if short, else split at items |
>
> ```python
> def specialized_chunk(element):
>     if element.type == 'table':
>         md = table_to_markdown(element)
>         return Chunk(text=f"[Table: {element.caption}]\n{md}", ...)
>     elif element.type == 'code':
>         return Chunk(text=f"[Code]\n```{element.lang}\n{element.text}\n```", ...)
>     ...
> ```
>
> **Why naive fixed-size fails on this corpus**:
> 1. Cuts mid-table → broken cells in different chunks
> 2. Cuts mid-code function → useless half-function
> 3. Cuts mid-sentence → broken semantic unit
> 4. Loses heading context → 'voltage rating 5V' without knowing which device
>
> **Late chunking (advanced, 2026)**:
>
> If embedding model supports long context (Jina v3, Gemini), can do **late chunking**:
>
> ```
> 1. Embed entire long doc with long-context model
> 2. Aggregate per-token embeddings to produce chunk embeddings
> 3. Chunks have full document context baked in
> ```
>
> Wins when context within doc matters (e.g., earlier pages set definitions). Cost: more inference compute upfront, but reindex frequency lower.
>
> **Tuning chunk size — eval loop**:
>
> ```python
> for chunk_size in [256, 512, 1024, 2048]:
>     for overlap in [0, 50, 100]:
>         pipeline.reindex(chunk_size, overlap)
>         metrics = eval(eval_set, pipeline)
>         log(chunk_size, overlap, metrics)
> ```
>
> Typical findings:
> - **256 tokens**: high precision (chunk = answer), low recall (answer spans 2 chunks)
> - **512 tokens** (sweet spot for most): balance
> - **1024 tokens**: more context, but noise in single embedding
> - **Overlap matters more** for small chunks
>
> **Failure I'd guard against**:
> - **Single mega-chunk per doc**: 'PDF in 1 vector' loses detail
> - **No overlap**: boundary loss
> - **Heading discarded**: 'voltage 5V' embed without knowing context
> - **All same chunk size**: not all content equal in length
>
> **Hybrid**: I'd recommend heading-aware where structure exists, fall back to fixed-size + overlap for unstructured."

---

## 简历专属 reframe

| 题 | 你做过 |
|---|---|
| Chunking strategy | BNPL chatbot RAG — corpus mixed (tickets / docs / FAQs), different chunk strategy per type |
| Metadata enrichment | Voice agent — every utterance + market + intent in retrieval metadata |
| Eval methodology | ConvFinQA — sweep ablation methodology you've used |
| Multi-modal | Voice agent — text + audio combined retrieval |

**Quote**:

> "BNPL chatbot had **3 chunking strategies coexisting**: FAQs as atomic chunks (avg 100 tokens), policy docs heading-aware (avg 600 tokens), support tickets paragraph-level (avg 300 tokens). Metadata included source_type, allowing retrieval to **mix sources** per query but weight relevant source higher. Naive 'one chunk size fits all' at 512 had recall@10 = 71%, after split-by-source-type strategy it went to 84%."

---

## 5 follow-ups

**Q1**: "Smaller chunks = more vectors = more storage. Cost concern."
**A**:
- **Storage scale**: 1M chunks × 1KB embedding = 1GB. Cheap.
- **Index size**: HNSW index has overhead but sub-linear with chunk count
- **Query cost**: ANN search log(n), small impact
- **Real concern**: embedding cost upfront (1M × $0.0001 = $100). Amortize over query.

**Q2**: "Reindexing — when doc changes, recompute embeddings expensive."
**A**:
- **Delta indexing**: chunk-level changes detected via hash, only re-embed changed chunks
- **Versioning**: old + new coexist briefly during transition
- **Async**: change → queue → background reindex (eventual consistency acceptable for most RAG)

**Q3**: "Some chunks are 'TOC' or 'copyright' — junk for retrieval. Filter?"
**A**:
- **Pre-filter at index time**: heuristic on heading text ('Table of contents', 'Copyright') skip
- **Quality scoring**: chunks with high keyword density / structure → kept
- **Hand-curated stoplist** for known junk patterns
- **LLM-based filter (cheap pass)**: 'is this chunk informative?'

**Q4**: "User question spans 3 sections. Retrieval gets 1, misses other 2."
**A**:
- **Larger chunks** at index time (but loses precision)
- **Multi-query expansion**: rewrite question into 3 sub-queries
- **Iterative retrieval**: agent retrieves, sees gap, retrieves more
- **Document-level retrieval**: first find doc, then chunk within (hierarchical)

**Q5**: "Late chunking sounds great — why not always use it?"
**A**:
- **Embedding cost** higher (long-context inference is $$$)
- **Model availability**: not all embedding models support long context
- **Reindex granularity**: changes anywhere in doc → re-embed all
- **Use case**: long-document with high intra-doc context (legal, scientific) — best fit
- **Not great for**: short-doc corpus, daily-changing data

---

## ❌ 易错点

1. **Fixed-size everywhere** — no structural awareness
2. **No overlap** — boundary info lost
3. **Heading discarded** — embedding loses context
4. **Cut tables / code in middle** — broken semantic
5. **All same chunk size** — content variety ignored
6. **No metadata** — retrieval can't filter
7. **No eval** — chunk size 'feels right'

---

## ✅ 加分项

1. **Decision tree** for strategy choice
2. **Heading-aware + recursive fallback**
3. **Overlap rationale** with cost trade-off
4. **Metadata enrichment** including heading_path
5. **Multi-modal special handling** (table / code / figure)
6. **Late chunking** awareness
7. **Eval loop** for tuning
8. **Quote BNPL 3-strategy + recall jump**

---

## Cheat Sheet

```
5 strategies (decision tree):
  Fixed-size + overlap: baseline / unstructured
  Sentence-aware: respects sentence boundary
  Paragraph / section: structured docs
  Heading-aware recursive: hierarchical (best general)
  Late chunking: long-context embedding model

Typical sizes:
  256 tokens: high precision, low recall
  512 tokens: sweet spot
  1024 tokens: more context, noisier
  Overlap: 10% (50 tokens for 512)

Metadata to attach:
  doc_id, doc_title
  heading_path (list of headings)
  chunk_index, total_chunks
  updated_at
  page_range
  tags / source_type
  perms

Embed with heading context:
  embed('Heading: X.Y\nContent: ' + text)

Multi-modal handling:
  Tables: atomic + Markdown serialize
  Code: atomic + lang annotation
  Figures: caption + alt text + image embed
  Formulas: LaTeX → text
  Lists: atomic if short

Naive failure modes:
  Cut mid-table / mid-code / mid-sentence
  Lose heading context
  No overlap → boundary loss
  Single mega-chunk per doc

Eval loop:
  Sweep (size, overlap)
  Eval recall@k + NDCG
  Per-source-type chunking

Late chunking (advanced):
  Long-context embed first, then aggregate
  Use case: long-doc, high intra-doc context

红线:
  - Fixed-size everywhere
  - No overlap
  - Cut tables/code
  - No metadata
  - All same size
  - No eval
```
