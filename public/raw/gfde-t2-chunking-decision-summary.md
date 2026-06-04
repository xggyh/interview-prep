# ✂️ T2.2 · Chunking 策略决策树 — 冲刺版

> 完整版: [gfde-t2-chunking-decision.html](gfde-t2-chunking-decision.html). 这页是 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: 10K technical PDFs 50-500 页, mixed prose+tables+code+formulas, query 是 fact-lookup + concept-explanation, embedding 用 text-embedding-005 (768d, 2K max), daily reindex 可接受, latency budget 1s, multi-tenant."

**4-layer chunking pipeline (recall 71→87 的关键)**:

### Layer 1: Strategy decision tree (按 doc 类型选)

```
Pure prose (blog/FAQ)            → Recursive 512 tok + 64 overlap ⭐ default
Markdown/HTML w/ headers         → Heading-aware recursive
PDF w/ tables (legal/财报)       → Document AI parse → doc-structure aware
Code / Repo                      → Tree-sitter AST, function-level atomic
Chat / Conversation logs         → Turn-based, 3-5 turn group
Mixed enterprise wiki             → Late chunking (Jina v3 / Cohere v4) ⭐ 2026
```

### Layer 2: Multi-modal special handling

- **Tables**: ATOMIC chunk (永远不切), Markdown serialize + caption + 上下文一起 embed
- **Code**: ATOMIC (跨 def 不切), imports + signature + body 作 chunk, symbol metadata
- **Formula**: 保留 LaTeX (不渲染图), 加文字描述 embed
- **Figure**: caption + alt text chunk, 或 multimodal embed (CLIP)
- **List**: 短 atomic, 长 split at item boundary (不切 item 中间)

### Layer 3: Metadata enrichment

```python
Chunk = {
    'chunk_id': hash(doc_id + heading_path + chunk_index),  # 稳定 ID for delta
    'doc_id', 'heading_path', 'page_range', 'section_level',
    'is_table'/'is_code'/'is_figure', 'tenant_id', 'visibility',
    'acl_groups', 'pii_level', 'created_at', 'updated_at',
    'quality_score', 'is_canonical', 'language', 'product',
}
# Embed text prepend heading: f"{' > '.join(heading_path)}\n\n{chunk.text}"
```

### Layer 4: Delta indexing + versioning + hot/warm

- **Delta**: chunk_id 稳定 hash → 仅 changed chunk re-embed (10K doc full reindex 40min vs delta 1 doc 1s)
- **Versioning**: 双写 v2 + v3, traffic split 80/20, eval pass → cutover
- **Hot + warm**: last 24h in-memory 5min refresh + rest daily Vertex AI Vector Search, RRF merge
- **Async pipeline**: doc change → Pub/Sub queue → background worker

### Edge cases (背 5 个)

- **EC1 切表格中间**: naive fixed-512 把表格切两半, 半个表无意义 → Document AI 解析为 table element, atomic chunk + Markdown serialize, caption embed.
- **EC2 Heading 丢上下文**: "Rated voltage: 5V" 不知是哪个设备 → embed_text prepend heading_path ('iPhone 15 Pro Max > Specs > Electrical\n\n5V'), embedding 有 context.
- **EC3 Random chunk ID**: 每次 random UUID → delta indexing 不可能 (无法 diff) → 用 `hash(doc_id + heading_path + chunk_index_in_section)` 结构性 hash.
- **EC4 Tokenizer mismatch**: 用 GPT tokenizer 数 token 但 embedding 用 BERT → 估算偏差 30%+ → 用 embedding model 自己的 tokenizer 数.
- **EC5 PII tagging 漏**: chunk 含 SSN/credit card 直接 embed 进 index → 索引前 Cloud DLP 扫描, mask 或 drop, 标 pii_level 用于检索时 perms.

### Production hardening (1 min)

- **Eval sweep**: chunk_size ∈ {256,384,512,768,1024} × overlap ∈ {0,25,50,100} × strategy ∈ {fixed, sentence, heading-aware} — 找最优 NDCG@10
- **Slice eval**: table_query / how_to_query / code_query — 每 slice 独立改造
- **CI regression**: 每次 chunker 改动跑 eval, recall drop >2pp 阻断 merge
- **Per-source-type chunker**: FAQ atomic / policy heading-aware / ticket turn-aware / code AST
- **2026 trend**: Late chunking (整 doc 先 embed 再切 pool) intra-doc context heavy +30-40% recall

### 🪝 Resume hook

"BNPL chatbot 3 chunker 共存: FAQ atomic (1 FAQ = 1 chunk, avg 100 tok), policy heading-aware (avg 600 tok, retain hierarchy), ticket turn-aware (avg 300 tok, split by speaker). Metadata `source_type` 让 retrieval 混搜但 boost policy > ticket. Naive 一刀切 512 recall@10 = 71%, 后变 84%. 最大单点 8pp 收益是 table-as-atomic — 监管表格 (利率/费率 cap) 是最高价值 content, 切 mid-cell 完全废. ConvFinQA 用 LlamaParse / Document AI 解析财报表格 + 用 tree-sitter parse 配套 code 例, 每类独立 chunker."

---

## 🔥 5 Follow-ups (面试官会问)

**Q1: 小 chunk 更多向量, 存储 cost 担忧?**
1M chunks × 768d × 4 bytes = 3GB, Vertex AI Vector Search/Vertex Vector Search 便宜; HNSW 1.5-2x; embedding 一次性 1M × 500 tok × $0.025/1M = $12.5 amortized 0; 小 chunk 提升 precision → fed LLM 更少 → 省 LLM cost. Counter-net positive.

**Q2: Reindex — doc 改时重 embed 贵?**
Delta indexing: chunk-level hash, 仅 re-embed changed; chunk_id 稳定 via `hash(doc_id + heading_path + chunk_index)`; versioning 灰度 (v_old + v_new 双写一段时间); async via Pub/Sub queue background worker; hot index for sub-5-min freshness on new docs.

**Q3: 有些 chunk 是 'TOC' / 'copyright' / junk, 怎么过?**
Pre-filter at index time: heuristic on heading text ('Table of Contents', 'References') skip; quality score (keyword density / structure); hand-curated stoplist for known patterns; LLM cheap pass 'is this informative?' on questionable.

**Q4: 用户问题跨 3 个 section, retrieval 拿 1 个 miss 2 个?**
Hierarchical / parent-doc: small chunk retrieve, large parent chunk return (更多 context); multi-query expand 分 3 sub-query; iterative agentic retrieve (LLM 看 gap 再 retrieve); document-level retrieval first 再 chunk within; **Late chunking** chunks inherently 有 doc context.

**Q5: Late chunking 听起来好, 为啥不全用?**
Embedding cost 高 (long-context inference $$); model availability (Jina v3 / Gemini long-ctx 才支持); reindex granularity (任何 chunk 改 → 全 doc re-embed, delta 不便); best use: 长 doc 高 intra-doc context (legal/科研); not for: 短 doc / 日变 / 多租户 doc 差异大.

---

## ❌ 易错点 (10 条红线)

1. Fixed-size everywhere — no structural awareness, 切表格代码句子
2. No overlap — boundary info 丢, 跨 chunk 答案抓不到
3. Heading discarded — "5V" 不知什么设备, embedding 没 context
4. Cut tables / code mid — 半张表 / 半个 function 无意义
5. All same chunk_size for all source-types — FAQ/policy/code 一刀切
6. No metadata — retrieval 无法 filter / boost
7. No eval, 凭 feel chunk_size — silent regression
8. Full reindex on each update — 10K doc 40min stop-the-world
9. Random chunk IDs — delta indexing impossible
10. No PII tagging — compliance 炸弹 (GDPR/PDPA)

---

## ✅ 加分项 (10 条)

1. **Decision tree** for strategy (5 strategies by doc type)
2. Heading-aware + recursive fallback as default
3. Overlap rationale (10-15% chunk size, 防 boundary 切碎)
4. Multi-modal special handling (table/code/formula/figure atomic)
5. Metadata enrichment 完整 schema (heading_path/perms/freshness/PII)
6. **Late chunking** (Jina v3 / Cohere v4) 2026 hot trend +30-40%
7. **Delta indexing** + chunk_id structural hash
8. Eval sweep chunk_size × overlap × strategy + slice by query type
9. Per-source-type chunker (FAQ atomic / policy heading / ticket turn / code AST)
10. Quote BNPL 3-strategy 71→84 recall + table-as-atomic 8pp jump

---

## 一句话总结

Chunking = **「按 doc 结构切 + 不切表格/代码/句子 + 附 heading metadata + overlap 兜底边界 + 多 source 多策略 + delta indexing + eval sweep 量化」**. 不是 "fixed 512" 一个数字, 是**多策略组合 + 工程流水线 + 持续 eval**.

---

## 🃏 Cheat Sheet (印 1 页随身)

```
5 strategies (decision tree):
  Fixed-size + overlap   baseline, unstructured prose
  Sentence-aware         略好 fallback
  Paragraph/section      有 paragraph break
  Heading-aware ⭐       hierarchical, best general
  Late chunking ⭐ 2026  long-ctx embed model (Jina v3), +30-40%

Typical sizes:
  256 tokens:  high precision, low recall
  512-768:     sweet spot ⭐ default
  1024+:       more context, noisier (dilution)
  Overlap:     10-15% (50-64 tok for 512)
  Code:        0 overlap (each func atomic, independent)

Multi-modal handling:
  Tables:    atomic + Markdown serialize + caption + 上下文 embed
  Code:      atomic + symbol metadata + lang annotation, no mid-func split
  Formulas:  LaTeX preserved + textual description
  Figures:   caption + alt + optional CLIP multimodal embed
  Lists:     atomic if short, item-boundary split if long

Metadata schema (production):
  Identity:  chunk_id (structural hash), doc_id, chunk_index, total
  Source:    doc_title, doc_url, doc_type, source_system
  Structure: heading_path, page_range, is_table/code/figure, section_level
  Time:      created_at, updated_at, effective_date
  Access:    tenant_id, visibility, acl_groups, pii_level
  Quality:   quality_score, view_count, feedback_rate, is_canonical
  Tags:      tags, language, product

Embed with heading context:
  embed_text = ' > '.join(heading_path) + '\n\n' + chunk.text
  e.g., "iPhone 15 Pro Max > Specs > Electrical\n\nRated voltage: 5V"

Delta indexing:
  chunk_id = hash(doc_id + heading_path + chunk_index_in_section)  # stable
  Compute new chunk hashes per doc
  Diff with existing → to_add / to_update / to_delete
  Apply to dense + sparse index
  Async via Pub/Sub queue

Versioning + 灰度:
  Double-write v_old + v_new for transition
  Traffic split per user_id hash (80/20)
  Eval v_new >= v_old → cutover, drop v_old

Hot + warm index:
  Hot: last 24h, in-memory (Redis vec or small Vertex AI Vector Search), 5min refresh
  Warm: rest, async delta indexing daily
  Search both, RRF merge

Eval methodology:
  Eval set: 200 human-labeled + 1000 LLM-synthetic
  Sweep: chunk_size × overlap × strategy
  Slice: table_query / how_to / code_query / multilingual
  CI: recall drop >2pp blocks merge
  Per-quarter refresh (query distribution drift)

Per-source-type chunker:
  FAQ:     atomic (1 entry = 1 chunk, ~100 tok)
  Policy:  heading-aware (~600 tok)
  Ticket:  turn-aware (~300 tok, split by speaker)
  Code:    AST-based (tree-sitter, function/class)
  Paper:   section-aware (~800 tok, abstract/method/results)
  Web:     trafilatura clean + recursive
  PDF:     Document AI / Unstructured / LlamaParse + doc-aware

GCP stack (2026):
  Document AI         (PDF parse + table extract + OCR)
  Vertex Vector Search (向量库 + filter)
  Vertex Embeddings   (text-embedding-005, 768d, $0.025/1M)
  Cloud DLP           (PII detect/mask)
  Cloud Storage       (raw PDF blob)
  Pub/Sub             (delta reindex queue)
  BigQuery            (chunk metadata + analytics)
  Cloud Run           (chunker worker, async)
  VPC Service Controls (tenant isolation)
  AWS: Document AI / Vertex AI Vector Search / Kendra comparison

Tool zoo:
  PDF parse:     unstructured, pymupdf, LlamaParse, Document AI
  Table extract: Camelot, Tabula, Document AI, Document AI Form Parser
  Code AST:      tree-sitter (语言无关)
  PII:           presidio (Microsoft), Cloud DLP
  Embedding:     text-embedding-005, gemini-embedding, bge-large
  Late chunking: jina-embeddings-v3 (8K ctx)
  Vector DB:     Vertex Vector Search, Vertex AI Vector Search, Vertex AI Vector Search, Weaviate

红线:
  - Fixed-size everywhere
  - No overlap
  - Cut tables / code mid
  - Heading discarded from embed
  - No metadata / no PII tagging
  - All same chunk_size
  - No eval / no slice
  - Full reindex on update
  - Random chunk IDs (delta impossible)
```
