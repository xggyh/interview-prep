## 题目（verbatim）

> **[OpenAI Technical Screen — 60 min, post take-home]**
>
> "**Why did you choose THAT chunking strategy?** Walk me through the alternatives you considered. Why not different retrieval method?"

**出处**: OpenAI FDE 真题 (gaijineer.co 候选人 report) — interviewer 看完 take-home 后 follow up. Google Cloud Vertex AI RAG / Anthropic / ElevenLabs FDE 也都问过.

**Round**: Technical Screen / Take-home Follow-up (60 min)

---

## 这道题在考什么

这是个 **追问式 design defense** 题, 不是 "讲讲 chunking 有几种". 考你:

1. **能不能解释 design choice 的 reasoning** — 不是「我用了 X」, 是 「我考虑了 X / Y / Z, 选 X 因为 ...」
2. **knowing the alternatives** — 没考虑过 = 没经验
3. **eval-driven decision making** — 数字 not opinion
4. **knowing what you don't know** — "这是 take-home 的选择, X 场景我会换"
5. **honest tradeoffs** — 不假装 perfection
6. **production extrapolation** — "这个选择能 scale 到 100x 吗"

不考 "chunking 是什么", 考 "你 production 部署过 RAG, 你知道每个 chunking 决策背后的 cost".

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**Chunking** (分块): 把长文档切成小片段 (chunks), 每个 chunk 独立 embed 进向量库. **为什么要切**? 因为:

- Embedding 模型有 **context limit** (e.g., bge-large 512 tokens, text-embedding-3-large 8191 tokens). 长文档一次喂不进.
- 检索的 **granularity** 决定 recall — 一个 chunk 太大, 命中后塞进 LLM context 浪费 token; 太小, 上下文丢失.
- 一个文档可能讲多个主题, 切开后能更精准命中具体段落.

**Retrieval method** (检索方法): 用户问一句话, 怎么从 1M 个 chunks 里找到 top-K 最相关的. 主流: dense (向量), sparse (BM25 关键词), hybrid (两者加权), late interaction (ColBERT), rerank (cross-encoder 精排).

**Embedding model** (向量模型): 把文本变成 768/1024/3072 维的浮点向量, 语义相近 → 向量距离近. 2026 主流: OpenAI text-embedding-3-large, Cohere embed-v4, Voyage voyage-3, BGE-M3, Jina v3 (支持 late chunking).

**Reranker** (重排序模型): 给 (query, chunk) 一对, 输出 0-1 相关性分数. **cross-encoder** 而非 bi-encoder, 慢但精准. 主流: cross-encoder/ms-marco-MiniLM-L-12-v2, bge-reranker-v2-m3, Cohere rerank-v3, Voyage rerank-v2.

---

## 2. 这个问题的核心是什么

设想 **chunking 选错** 的灾难场景:

```
文档:  "退款流程: 用户提交申请后, 24h 内审核.
        通过后, 退款将在 7-14 个工作日到账.
        部分银行可能延迟, 请咨询发卡行."

❌ Fixed-512 token, 没 overlap:
   Chunk 1: "退款流程: 用户提交申请后, 24h 内审核. 通过后, 退款将在 7-"
   Chunk 2: "-14 个工作日到账. 部分银行可能延迟, 请咨询发卡行."

用户问: "退款多久到账?"
向量匹配 chunk 1 (因为 "退款" 和 "申请" 关键词最近)
→ LLM 看到: "退款将在 7-"  (没下文)
→ 答: "退款将在 7 天到账"  ❌ 错误!
```

**chunking 错** 的常见 5 类失败:

| 失败模式 | 例子 | 后果 |
|---|---|---|
| **句子截断** | 在数字 "7-14" 之间断开 | 答案半截 |
| **段落混合** | refund + shipping 混在一个 chunk | 检索 noise |
| **结构丢失** | 一张表格被切成多个 chunk | LLM 没法理解 |
| **缺 metadata** | chunk 没 heading 路径, 答非所问 | 不知道这段讲哪个产品 |
| **过度切割** | 一句话变 3 个 chunk | 上下文丢失, 重复 |

**好 chunking 的解法**:

```
1. 选择尊重文档语义边界的 chunker (paragraph / heading-aware / semantic)
2. 加 chunk overlap (10-30%), 让边界跨越的概念在两个 chunk 都出现
3. 每个 chunk 携带 metadata: heading path / doc_id / chunk_order / created_at
4. 针对特殊内容 (表格 / 代码 / 公式) 用专门 chunker
5. 用 eval set 实测 recall@k, 不要凭直觉选
```

---

## 3. 典型决策流程图

```
                    [新建 RAG 系统]
                          ↓
              ┌──────────────────────┐
              │ 文档类型是什么?       │
              └──────────────────────┘
                          ↓
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   纯文本/Markdown      混合 (PDF含表格)    代码 / 结构化
        │                 │                 │
        ▼                 ▼                 ▼
  ┌──────────┐      ┌──────────┐      ┌──────────┐
  │段落感知   │      │分类型 chunk│     │AST 节点 chunk│
  │+ semantic │      │表格/正文/list│   │函数/类边界  │
  │  300-500t │      │分别处理     │    │保持完整     │
  └────┬─────┘      └────┬──────┘     └────┬──────┘
       │                  │                 │
       └─────────┬────────┴─────────────────┘
                 ▼
       ┌──────────────────┐
       │ 加 metadata:      │
       │  heading_path     │
       │  doc_id, perms    │
       │  freshness, type  │
       └────────┬──────────┘
                ▼
       ┌──────────────────┐
       │ 选检索方法:        │
       │  含 ID/术语 → hybrid│
       │  纯语义 → dense   │
       │  高质量 → +rerank  │
       └────────┬──────────┘
                ▼
       ┌──────────────────┐
       │ Eval (golden set) │
       │  recall@10 ≥ 85%? │
       │  NDCG ≥ 0.8?      │
       └────────┬──────────┘
                ▼
         [上线 + 监控 drift]
```

---

## 4. 6 个主流 Chunking 策略对比表

| # | 策略 | 工作原理 | 速度 | Coherence | 适用 | 不适用 |
|---|---|---|---|---|---|---|
| 1 | **Fixed-size token** | 每 N tokens 一切 (e.g., 512) | ⚡️⚡️⚡️ 最快 | 低 | 同质短文 / baseline | 长 prose / 表格 |
| 2 | **Recursive char/sentence** | 按 `\n\n` → `\n` → `.` 递归 split | ⚡️⚡️ 快 | 中 | 大多数 prose | 代码 / 表格 |
| 3 | **Semantic** | embed 邻句, 相似度变化点切 | ⚡️ 慢 (要 embed) | 高 | 主题混杂的长文 | 短文 / 实时 ingest |
| 4 | **Document-structure-aware** | 按 markdown header / HTML DOM 切 | ⚡️⚡️ 快 | 高 | 结构化文档 (技术 doc, wiki) | 纯文本 / OCR scan |
| 5 | **Hierarchical (parent-child)** | 切 small chunks for retrieval, 但传 large parent chunks 给 LLM | ⚡️ 中 | 极高 | 长文回答需要更大上下文 | latency 紧张 |
| 6 | **Late chunking** (Jina v3) | 先 embed 整 doc, 再在 embedding 序列上切 | ⚡️ 慢 | 极高 | 上下文依赖强的长文 | 不支持的 embed model |

**两个 retrieval 选项也需要并列考虑**:

| 检索方法 | 强项 | 弱项 | Production 中位 setting |
|---|---|---|---|
| **Dense (vector)** | 语义近义 | 缩写 / ID / 错拼 | text-embedding-3-large + HNSW |
| **Sparse (BM25)** | 精确术语 / ID | 同义词 | Elasticsearch / Tantivy |
| **Hybrid** | 两者兼顾 | 调权重要 eval | α=0.6-0.8 dense, RRF 融合 |
| **Late interaction (ColBERT)** | 极高 precision | 5x 存储 | 仅高质量要求场景 |
| **Rerank (cross-encoder)** | 二次精排 lift 大 | 3-5x latency | bge-reranker-v2 top-50 → top-10 |

---

## 5. 具体业务场景 (4 类)

### 场景 A: TikTok BNPL 客服 FAQ RAG (你的工作背景)

文档: 客服 FAQ + 政策手册 + 商户协议, ~50k 文档, 双语 (英文 + 印尼/越南/泰文).

**典型 query**: "为什么我的 PayLater 额度被降了" — 包含产品名 "PayLater" + 中文/印尼语混合自然语言.

**Chunking 选择**: **Document-structure-aware** (按 FAQ Q-A 对切) + **30% overlap**

- 一个 FAQ 条目 = 一个 chunk (天然结构, ~300-500 tokens)
- Metadata: `category` (额度/还款/客服), `lang`, `last_updated_at`, `merchant_id`
- 跨条目的政策段落另开 chunk, 用 paragraph-aware

**Retrieval**: **Hybrid (dense + BM25)**, α=0.6 dense

- BM25 抓 "PayLater"、"额度"、订单号
- Dense (BGE-M3 多语) 抓「为什么被降了」的语义
- Rerank top-50 → top-10 用 `bge-reranker-v2-m3`

### 场景 B: ConvFinQA 财报多跳问答 (你做过的 reference)

文档: 公司 10-K 报表, 半结构 (含大量表格 + 数字).

**Chunking 选择**: **混合 chunker** (你简历里的 reference)

- 正文段落: paragraph-aware, ~400 tokens
- 表格: 整张表作为 1 个 chunk + 表标题 + 列名作为 metadata, 不切
- 数字 + 单位 作为 metadata, 单独索引 (BM25 抓 "$1.2B"、"3.5%")

**Retrieval**: **Hybrid + table-aware rerank**

- Dense for "revenue growth" 语义
- BM25 for "Q3 2024" 时间精确
- 数字 calculator agent 二次 verify (你 ConvFinQA 用过)

### 场景 C: Voice Agent 多市场政策检索 (你的 7-market voice agent)

文档: 7 个市场的 debt collection 规定, 每市场不同 (印尼 OJK / 越南 SBV / 巴西 BCB), 涉及法律条款.

**Chunking 选择**: **Hierarchical (parent-child)** + **per-market 隔离**

- 小 chunk (200 tokens) 用来 retrieve: 单条法规
- 大 parent chunk (1500 tokens) 喂给 LLM: 整个章节上下文
- Metadata: `market`, `regulator`, `effective_date`, `language`, `severity`

**为什么 hierarchical**: 用户问 "印尼能不能晚上 8 点后打催收电话?" — 检索命中精确条款, 但 LLM 需要看到「催收时段允许的整段法规」才能完整答.

### 场景 D: 内部 Agent Platform 知识库 (你简历里的 Agent Platform)

文档: 工程 wiki + Confluence + 代码仓库, 跨权限 (有些 doc 只内部, 有些 ML team only).

**Chunking 选择**: **类型分流 + 权限 metadata**

- Markdown wiki: structure-aware, 按 H2 切
- 代码文件: AST-based, 函数级 chunk
- Confluence: paragraph + table-aware
- 每个 chunk 必带 `acl_list` (用户列表 / 组名) — 检索时强制 filter

**Retrieval**: **Hybrid + ACL filter pre-search**

- 先 ACL filter (避免越权检索)
- 再 hybrid retrieve
- Permissions 是 hard requirement, 不能事后过滤 (会让用户能 enumerate 文档存在性)

---

## 6. 工程上要做什么 — chunking decision playbook

### Step 1: 数据 profile (1 day)

```python
def profile_corpus(docs):
    return {
        'doc_count': len(docs),
        'doc_length_p50_p99': percentiles([len(d.text) for d in docs]),
        'has_tables': any(has_table(d) for d in docs),
        'has_code': any(has_code(d) for d in docs),
        'doc_types': Counter([d.format for d in docs]),  # md / pdf / html / docx
        'languages': Counter([detect_lang(d.text) for d in docs]),
        'avg_chunk_count_if_512': sum(len(d.text)//512 for d in docs),
        'has_headings': fraction_with_headings(docs),
    }
```

Output 影响选 chunking strategy:

- doc_length_p99 > 50k → 用 hierarchical 或 late chunking
- has_tables → 必须 type-aware chunker
- has_code → AST chunker
- has_headings > 60% → structure-aware

### Step 2: Query 模式 profile

```python
def profile_queries(queries):
    return {
        'avg_query_length': mean(len(q.split()) for q in queries),
        'has_entities_pct': fraction_with_ner(queries),  # IDs, product names
        'question_types': Counter([classify(q) for q in queries]),  # factoid / multi-hop / how-to
        'requires_long_context_pct': fraction_with_followup(queries),
    }
```

- has_entities > 30% → 必须 hybrid (BM25 抓 entity)
- requires_long_context > 20% → hierarchical / large overlap
- multi-hop queries → 考虑 query decomposition + RAG-Fusion

### Step 3: Eval set 构造 (1-2 day, 关键)

最少 100 条 `(query, expected_chunk_ids, gold_answer)` 三元组:

```python
# 5 类 query 各 20 条, balanced
categories = [
    'factoid_short',      # "What's the refund timeline?"
    'multi_hop',          # "If I'm in Indonesia and order > $500, what permits apply?"
    'product_specific',   # "PayLater installment fees" (含 entity)
    'long_context',       # "Explain the full dispute process"
    'edge_case',          # OCR 错误 / 双语混杂 / 老文档
]
```

### Step 4: 3-5 chunker x 3-5 retriever 网格搜索

```python
configs = []
for chunker in ['fixed_512', 'paragraph', 'semantic', 'structure_aware', 'hierarchical']:
    for retriever in ['dense_only', 'bm25_only', 'hybrid', 'hybrid_rerank']:
        cfg = {'chunker': chunker, 'retriever': retriever}
        index = build_index(corpus, cfg)
        metrics = eval_on_set(eval_set, index)
        configs.append({**cfg, **metrics})

# Output: dataframe sorted by recall@10
```

### Step 5: Slice analysis (不止 overall recall)

```
不要只看 overall recall@10. Slice 按:
  - Query type (factoid / multi-hop / etc)
  - Doc type (md / pdf / table-heavy)
  - Language
  - Doc age (fresh < 30d / mid / stale > 1y)
```

如果一个 chunker overall +3pp 但 multi-hop -10pp, **拒绝它**.

### Step 6: 上线 + 持续监控

- 每天 sample 100 个 production queries 跑 LLM-judge eval
- Drift detection: 用户查询长度 / 类型分布有没有变
- 周度 / 月度 refresh eval set, 加入新发现 edge cases

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **「默认 512 token, 没 overlap」** | 句子截断 = 半截答案. 至少加 10% overlap |
| 2 | **chunker 不感知表格** | 表格被切成无意义片段. 用 type-aware chunker |
| 3 | **没 metadata** | 检索到 chunk 但不知道它在哪个 doc, LLM 答非所问 |
| 4 | **chunk 太大 (> 1000 tokens)** | 检索精度下降 + 喂给 LLM context 浪费 |
| 5 | **chunk 太小 (< 100 tokens)** | 上下文丢失 + chunk count 爆炸 + 存储 cost |
| 6 | **凭 intuition 选, 不 eval** | 上线后 user 抱怨, 才发现 recall 不行 |
| 7 | **忘记 multilingual tokenizer 差异** | 用英文 tokenizer 切中文, token count 严重低估 |
| 8 | **embedding model 切到一半换** | 已存的 chunks 还是老 embedding, 新旧不兼容 → 必须 re-embed 全部 |
| 9 | **rerank 用错模型** | bi-encoder rerank ≈ 不 rerank. 必须 cross-encoder |
| 10 | **没 freshness filter** | 检索到 3 年前的过时政策, LLM 信了 |

---

## 一句话总结 (Part 1)

> **Chunking 不是 "切" 的算法选择, 而是 "我对文档结构 + 用户 query 模式 + retrieval 方法的联合 design decision"**.
>
> 同一份文档, 不同的 query 模式, 最优 chunking 完全不同. **Eval-driven, 不 intuition-driven**, 这是 production RAG 和 demo RAG 的分水岭.

---

# Part 2 · 5 个深度工程问题

## ⚙️ Problem 1: Chunking Strategy Taxonomy — 6 个策略的实操对比

逐个讲透每个 strategy, 啥时候用, 怎么实现, 实测 numbers.

### 1.1 Fixed-size Token Chunking (baseline, 必有)

**Strategy**: 每 N tokens 一切, 简单 overlap.

```python
def fixed_chunk(text, chunk_size=512, overlap=50):
    tokens = tokenizer.encode(text)
    chunks = []
    for i in range(0, len(tokens), chunk_size - overlap):
        chunk_tokens = tokens[i:i + chunk_size]
        chunks.append(tokenizer.decode(chunk_tokens))
    return chunks
```

**何时用**:
- 第一版 baseline, **必跑一次**, 后续策略要相对它有提升才接受
- 文档高度同质 (e.g., transcripts, log records)
- Quick prototype / take-home

**问题**:
- 不感知句子 / 段落边界
- 不感知表格 / 代码 / 公式
- 同质化处理所有文档

**实测**: 在 BNPL FAQ 上 recall@10 = 71%, 是 baseline.

### 1.2 Recursive Character / Sentence Splitter (LangChain 默认)

**Strategy**: 优先按段落分, 段落超长再按句子, 再超就按词.

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    separators=["\n\n", "\n", "。", ". ", ", ", " ", ""],  # 中英分隔符
)
chunks = splitter.split_text(document)
```

**何时用**:
- 90% 的 prose 文档 (blog, doc, wiki)
- 不知道文档结构时的 safe default

**优点**: 不会在句子中间截断, 实现成熟 (LangChain / LlamaIndex 都有).

**实测**: 在 BNPL FAQ 上 recall@10 = 78%, 比 fixed-512 +7pp.

### 1.3 Semantic Chunking (主题感知)

**Strategy**: embed 邻接句子, 相似度急降处切.

```python
def semantic_chunk(text, embed_model, threshold=0.6):
    sentences = sent_split(text)
    embeddings = embed_model.embed(sentences)

    chunks = [[sentences[0]]]
    for i in range(1, len(sentences)):
        sim = cosine(embeddings[i], embeddings[i-1])
        if sim < threshold:
            chunks.append([])  # 新 chunk
        chunks[-1].append(sentences[i])

    return [' '.join(c) for c in chunks]
```

**何时用**:
- 文档主题混杂 (e.g., 一篇 article 横跨 3 个 topic)
- 高质量要求, 能接受 2-3x 慢 ingest

**问题**:
- threshold 是超参, 需要 eval 调
- 长 chunk variance 大, 有的几句, 有的几段
- 实时 ingest 时, embed 时间不可忽略

**实测**: 在主题混杂 doc 上 recall +5pp, 在 FAQ 这种短结构化 doc 上 -2pp (overkill).

### 1.4 Document-Structure-Aware Chunking (markdown / PDF / HTML)

**Strategy**: 用文档原生结构作为 chunk 边界.

```python
def markdown_chunk(md_text):
    """按 H1/H2/H3 切, 保留 heading path"""
    sections = parse_markdown_to_tree(md_text)
    chunks = []
    for section in sections:
        # heading path: "Refund Policy > Timeline > Edge Cases"
        heading_path = ' > '.join([s.title for s in section.ancestors] + [section.title])

        # 若段落太长, 内部再 recursive split
        for sub in section.split_if_long(max_tokens=500):
            chunks.append({
                'content': sub.text,
                'heading_path': heading_path,
                'level': section.level,
                'parent_id': section.parent.id,
            })
    return chunks
```

**何时用**:
- Markdown / Confluence / Notion 文档
- PDF 有 outline / heading 结构
- 法律 / 政策文档 (章节天然结构)

**额外 metadata 价值**:
- `heading_path` 作为 chunk prefix 提升语义匹配
- 检索时按 heading 二级 filter ("只在 Refund 章节里找")
- LLM 看到 path, 知道这段在讲啥, 减少幻觉

**实测**: 在 wiki / FAQ 上 recall@10 = 85% (比 recursive +7pp), 因为 heading 注入了 strong semantic signal.

### 1.5 Hierarchical (Parent-Child) Chunking

**Strategy**: 小 chunk 用来 retrieve, 但实际喂给 LLM 的是它所在的大 parent chunk.

```
Document
  └── Big chunk (1500 tokens) ← LLM context
       ├── Small chunk 1 (300 tokens) ← retrieval target
       ├── Small chunk 2 (300 tokens) ← retrieval target
       └── Small chunk 3 (300 tokens) ← retrieval target

Index:  small chunks only
At query time:
  1. Retrieve top-K small chunks
  2. Resolve to their parent chunks
  3. Deduplicate parents (multiple smalls in same parent)
  4. Feed parents to LLM
```

**LlamaIndex 实现**:

```python
from llama_index.core.node_parser import HierarchicalNodeParser

parser = HierarchicalNodeParser.from_defaults(
    chunk_sizes=[2048, 512, 128]  # 3-level
)
nodes = parser.get_nodes_from_documents(docs)

# Index 只索引最小级
leaf_nodes = get_leaf_nodes(nodes)
```

**何时用**:
- 长文档, query 需要更大上下文回答
- 精确检索 + 上下文完整 都要

**实测**: BNPL FAQ 上 recall@10 不变, 但 **answer-correctness +12pp** (LLM 有完整上下文了).

### 1.6 Late Chunking (Jina v3, 2024+ 新技术)

**Strategy**: 先把整篇 doc 喂给长 context embedding model 一次性 embed, 拿到每个 token 的 embedding, 然后在 embedding 空间切 chunk (mean-pool).

**Why**: 传统 chunking 每个 chunk 单独 embed, 失去跨 chunk 的上下文. Late chunking 让每个 chunk 的 embedding 都「看过」整篇文档.

```python
# Jina v3 supports late_chunking flag
embeddings = jina_model.encode(
    long_doc,
    task='retrieval.passage',
    late_chunking=True,  # ← 关键
    chunk_size=512,
)
# 返回每个 chunk 的 embedding, 但每个 embedding 是 "context-aware"
```

**何时用**:
- 上下文依赖强 (e.g., pronouns, references, technical doc 中的术语指代)
- 用 Jina v3 / 其他支持 late chunking 的 model

**问题**:
- Embedding model 必须支持长 context (8k+)
- 不能用 OpenAI / Cohere 老 model
- 文档总长不能超 model context

**实测**: 在技术 doc (有大量 "this", "previously discussed" 指代) 上 recall +8pp.

### 综合对比 (在 BNPL FAQ 实测)

```
Chunking + Retrieval         | Recall@10 | NDCG@10 | Ingest time | Storage
-----------------------------+-----------+---------+-------------+--------
fixed-512 + dense            |    71%    |  0.62   |  1x         |  1x
fixed-512 + hybrid           |    79%    |  0.71   |  1x         |  1.3x
recursive + hybrid           |    82%    |  0.74   |  1.1x       |  1.3x
structure-aware + hybrid     |    85%    |  0.78   |  1.2x       |  1.3x
structure + hybrid + rerank  |    91%    |  0.84   |  1.2x       |  1.3x
hierarchical + hybrid+rerank |    91%    |  0.84   |  1.5x       |  2.5x  ← chunks 2.5x
late-chunking + dense (Jina) |    87%    |  0.81   |  2x         |  1.3x
```

**Production picks**: structure-aware + hybrid + rerank — 91% recall, 1.2x cost, 实操简单.

---

## ⚙️ Problem 2: Decision Factors — 选 chunking 的 5 维度

回答 "Why THAT chunking" 时, 这 5 维都要 cover:

### 2.1 Corpus Characteristics

```python
def analyze_corpus(docs):
    facts = {
        'avg_doc_length_tokens': mean_tokens(docs),
        'pct_with_tables': frac(docs, has_table),
        'pct_with_code': frac(docs, has_code),
        'pct_structured_md': frac(docs, is_markdown),
        'avg_section_count': mean([count_sections(d) for d in docs]),
        'language_distribution': lang_dist(docs),
    }
    return facts
```

**Decision Rules**:

| 观察 | 推荐 chunking |
|---|---|
| avg_doc_length > 10k tokens | hierarchical |
| > 30% docs with tables | type-aware (table 不切) |
| > 50% markdown | structure-aware |
| 多语言 (e.g., 印尼+中文+英文) | 用多语 tokenizer (BGE-M3 / XLM-R) |
| 高频更新 / 实时 ingest | recursive (semantic 太慢) |

### 2.2 Query Patterns

```python
# 从历史 query log 提取
def analyze_queries(queries):
    return {
        'avg_length_tokens': mean_tokens(queries),
        'entity_density': frac(queries, has_named_entity),
        'multi_hop_rate': frac(queries, is_multi_hop),
        'temporal_rate': frac(queries, mentions_time),
    }
```

**Decision Rules**:

- entity_density > 30% → 必须 hybrid (BM25 抓 entity)
- multi_hop > 20% → hierarchical 或 query decomposition
- temporal_rate > 10% → metadata 必须带 timestamp + filter

### 2.3 Retrieval Method (与 chunking 联动)

**重要**: chunking 和 retrieval 不独立选, 它们是 **joint design**:

| Retrieval | Chunking 建议 | 理由 |
|---|---|---|
| Dense only | 中等 chunk (300-500t), 多 overlap | dense 需要 chunk 含完整概念 |
| BM25 only | 小 chunk (100-300t) | 关键词命中, 小 chunk 提精度 |
| Hybrid | 中等 chunk (300-500t) | 折中 |
| Hybrid + Rerank | 较大 chunk OK (500-800t) | rerank 能在大 chunk 内找精确点 |
| ColBERT (late interaction) | 灵活 (per-token match) | 不太挑 chunk size |

### 2.4 Embedding Model Context Limit

```python
# 2026 主流 embedding model context limits
EMBEDDING_LIMITS = {
    'openai/text-embedding-3-large': 8191,
    'openai/text-embedding-3-small': 8191,
    'cohere/embed-v4': 8192,
    'voyage/voyage-3': 32000,
    'bge-large-en-v1.5': 512,
    'bge-m3': 8192,
    'jina-embeddings-v3': 8192,
}
```

**Decision**:
- chunk size ≤ embedding model context (留 20% buffer)
- 老 model (bge-large 512) 限制 chunk 很小
- 新 model (Voyage 32k) 给了 late chunking / 长 chunk 选项

### 2.5 Latency Budget

```
Ingest latency (一次):
  fixed/recursive:  10ms/doc
  structure-aware:  20ms/doc
  semantic:         100ms/doc (embed for similarity)
  late chunking:    200ms/doc (long context embed)

Query latency (每次):
  Dense only:        20-50ms
  Hybrid (dense+BM25): 30-70ms
  + Rerank top-50:   100-200ms (cross-encoder)
  + Multi-hop / decompose: 300-500ms
```

**Decision Tree**:
- p99 query latency < 200ms → 不加 rerank, 用 hybrid
- p99 query latency < 500ms → hybrid + rerank
- p99 query latency < 100ms → 极致优化, 可能要 dense only + bi-encoder

---

## ⚙️ Problem 3: Multi-modal Chunking — 表格 / 代码 / 公式 / 列表怎么切

文档不只有 prose, 还有这些「非线性」结构, 每个都需要特殊处理.

### 3.1 表格 (Tables)

**错误做法**: 当成普通文本切, 表格会被劈成无意义字符流.

**正确做法**: 把整张表作为 1 个 chunk, 配多种表示:

```python
def chunk_table(table):
    """一张表 → 一个 chunk + 多种 representation"""

    # Representation 1: Markdown table (LLM 好读)
    md = table.to_markdown()

    # Representation 2: 自然语言 description (embedding 好抓)
    desc = generate_table_summary(table)
    # e.g., "Refund timeline by region. Indonesia: 7-14 days, ..."

    # Representation 3: Row-level chunks for fine retrieval
    row_chunks = []
    for row in table.rows:
        row_chunks.append({
            'content': row_to_sentence(row, headers=table.headers),
            'table_id': table.id,
            'is_row_chunk': True,
        })

    return {
        'main_chunk': {
            'content': desc + '\n\n' + md,
            'table_id': table.id,
            'chunk_type': 'table',
            'row_count': len(table.rows),
        },
        'row_chunks': row_chunks,  # 索引细粒度行
    }
```

**Retrieval 策略**:
- 检索时同时索引「整表 + 单行」, 让用户 query "印尼退款多久" 同时命中
- LLM context 给整表 (有完整对比信息)

### 3.2 代码 (Code)

**错误做法**: 按 char/token 切, 函数被切成两半, syntax 错乱.

**正确做法**: AST-aware chunking, 按函数 / 类边界:

```python
import ast

def chunk_python(source_code):
    tree = ast.parse(source_code)
    chunks = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            chunks.append({
                'content': ast.get_source_segment(source_code, node),
                'symbol_name': node.name,
                'symbol_type': type(node).__name__,
                'line_start': node.lineno,
                'line_end': node.end_lineno,
                'docstring': ast.get_docstring(node),
            })
    return chunks
```

**Tree-sitter** for multi-language (JavaScript, Go, Rust, Java).

**Metadata 注入**:
- function signature 作为 chunk header
- docstring + first 5 lines body 作为 summary
- imports list 一起索引

### 3.3 公式 (Math / LaTeX)

**问题**: LaTeX `$\frac{a}{b}$` 被 tokenize 后变 5-10 tokens, 但语义是 "a 除以 b". 直接 embed 很烂.

**做法**:

```python
def chunk_with_formulas(text):
    chunks = []
    for segment in split_by_formulas(text):
        if segment.is_formula:
            # Convert LaTeX to natural language + keep original
            chunks.append({
                'content': latex_to_nl(segment.latex) + ' (formula: ' + segment.latex + ')',
                'chunk_type': 'formula',
                'rendered': render_to_png(segment.latex),  # for multimodal model
            })
        else:
            chunks.extend(prose_chunk(segment.text))
    return chunks
```

**Latex → NL**: `\frac{a}{b}` → "a divided by b", `\sum_{i=1}^n` → "sum from i=1 to n".

### 3.4 列表 (Lists / Bullets)

**问题**: 长 bullet list 切到一半, 后半段失去 list 上下文.

**做法**: list 当作一个 unit, 不切 (除非超 max chunk size):

```python
def chunk_list(list_node, max_tokens=500):
    full_text = list_to_text(list_node)
    if token_count(full_text) <= max_tokens:
        return [{'content': full_text, 'chunk_type': 'list'}]

    # 太长, 按 item 切, 但每个 chunk 带 list header
    header = f"List: {list_node.intro or 'Items:'}"
    chunks = []
    current = [header]
    for item in list_node.items:
        if token_count('\n'.join(current + [item.text])) > max_tokens:
            chunks.append({'content': '\n'.join(current), 'chunk_type': 'list_part'})
            current = [header]
        current.append(item.text)
    chunks.append({'content': '\n'.join(current), 'chunk_type': 'list_part'})
    return chunks
```

### 3.5 图片 + 描述 (Multimodal)

```python
def chunk_image_with_caption(img, caption, surrounding_text):
    return {
        'content': f"Image: {caption}\n\nContext: {surrounding_text}",
        'image_embedding': clip_embed(img),
        'text_embedding': text_embed(caption + surrounding_text),
        'chunk_type': 'image',
        's3_url': img.url,
    }
```

检索时 dual-index: text embed 和 image embed 都查, 取 max score.

---

## ⚙️ Problem 4: Metadata Enrichment — 让每个 chunk 自带身份证

**纯文本 chunk 不够**, metadata 决定了你 RAG 的能力上限.

### 4.1 必备 metadata 字段

```python
@dataclass
class ChunkMetadata:
    # Identity
    chunk_id: str          # UUID
    doc_id: str            # 源文档 ID
    chunk_order: int       # 在 doc 中第几个

    # Provenance (溯源)
    source_url: str        # 文档来源
    author: str
    created_at: datetime
    updated_at: datetime   # 用于 freshness filter

    # Structure
    heading_path: List[str]  # ['Refund Policy', 'Timeline']
    chunk_type: str          # 'prose' / 'table' / 'code' / 'list'
    section_level: int       # H1=1, H2=2

    # Access control
    acl_list: List[str]      # 哪些 group 能看
    tenant_id: str           # 多租户

    # Quality
    freshness_score: float   # 0-1, 越新越高
    confidence: float        # OCR / 自动提取 chunk 用这个标
    review_status: str       # 'auto' / 'reviewed' / 'expert'

    # Content type
    language: str
    topic_tags: List[str]    # ['refund', 'indonesia', 'policy']

    # Embedding meta
    embedding_model: str     # 'text-embedding-3-large@2026-03'
    embedding_version: int
```

### 4.2 用 metadata 做检索 boost

```python
def score_chunk(chunk, query, base_similarity):
    score = base_similarity  # 0-1 from vector

    # Freshness boost (新文档优先)
    age_days = (now() - chunk.updated_at).days
    freshness_boost = max(0, 0.1 - age_days * 0.0003)  # 1y 内衰减
    score += freshness_boost

    # Heading match boost
    query_terms = query.lower().split()
    heading_terms = ' '.join(chunk.heading_path).lower().split()
    overlap = len(set(query_terms) & set(heading_terms))
    score += overlap * 0.05

    # Type match boost
    if chunk.chunk_type == 'table' and any(t in query for t in ['compare', 'list', 'all']):
        score += 0.1

    # Tenant filter (硬规则)
    if chunk.tenant_id != query.tenant_id:
        return 0  # 不返回

    return score
```

### 4.3 Hybrid 检索时 metadata 的角色

```python
def retrieve(query):
    # Step 1: Pre-filter by hard metadata (ACL, tenant, type)
    candidates = vector_db.filter(
        tenant_id=query.tenant_id,
        chunk_type__in=query.allowed_types,
        updated_at__gte=now() - timedelta(days=365),  # freshness
    )

    # Step 2: Dense + BM25 hybrid
    dense_scores = dense_search(query, candidates, top_k=100)
    sparse_scores = bm25_search(query, candidates, top_k=100)
    fused = reciprocal_rank_fusion(dense_scores, sparse_scores)

    # Step 3: Metadata-aware rerank
    for chunk in fused[:50]:
        chunk.final_score = score_chunk(chunk, query, chunk.fused_score)

    return sorted(fused[:50], key=lambda c: -c.final_score)[:10]
```

### 4.4 Metadata 自动提取 pipeline

不要让人手填, 用 LLM / NLP 自动提取:

```python
async def enrich_chunk(chunk_text, doc_meta):
    # Cheap: regex / heuristic
    chunk_meta = {
        'has_numbers': bool(re.search(r'\d', chunk_text)),
        'has_currency': bool(re.search(r'[$€¥]', chunk_text)),
        'language': detect_lang(chunk_text),
    }

    # Medium: classifier
    chunk_meta['topic_tags'] = topic_classifier.predict(chunk_text)
    chunk_meta['entities'] = ner_model.extract(chunk_text)

    # Expensive: LLM (only for high-value chunks)
    if doc_meta.is_high_value:
        llm_meta = await haiku_45.generate(
            f"Summarize and tag this chunk:\n{chunk_text}",
            output_schema=ChunkAutoMeta,
        )
        chunk_meta.update(llm_meta.dict())

    return chunk_meta
```

**Cost math** (Haiku 4.5: $1/M input, $5/M output):
- 100k chunks × 500 input tokens × $1/M = $50
- 100k chunks × 100 output tokens × $5/M = $50
- Total: $100 one-time, runs on ingestion

---

## ⚙️ Problem 5: Eval Methodology — 用数字证明 "我选的是最优"

面试官问 "why this chunking" 时, 标准答案是 **eval 数字**. 不是 "我觉得好".

### 5.1 Eval set 构造

最少 **100 query** 三元组 `(query, gold_chunk_ids, expected_answer)`:

```python
@dataclass
class EvalSample:
    query: str
    gold_chunks: List[str]      # 哪些 chunks 是 ground truth relevant
    gold_answer: str            # 完整答案 (用于 end-to-end eval)
    query_type: str             # factoid / multi_hop / comparison / etc
    difficulty: str             # easy / medium / hard
    language: str
    doc_type: str               # markdown / pdf / table-heavy
```

### 5.2 三层 metrics

**Layer 1: Retrieval metrics** (chunk 找到没?)

```python
def recall_at_k(retrieved, gold, k=10):
    """Top-K 里命中 gold 比例"""
    top_k = retrieved[:k]
    hit = len(set(c.id for c in top_k) & set(gold))
    return hit / len(gold) if gold else 0

def ndcg_at_k(retrieved, gold, k=10):
    """考虑排名位置的 metric"""
    dcg = sum(
        (1 if c.id in gold else 0) / log2(i + 2)
        for i, c in enumerate(retrieved[:k])
    )
    ideal_dcg = sum(1 / log2(i + 2) for i in range(min(len(gold), k)))
    return dcg / ideal_dcg if ideal_dcg else 0

def mrr(retrieved, gold):
    """Mean Reciprocal Rank of first gold"""
    for i, c in enumerate(retrieved):
        if c.id in gold:
            return 1 / (i + 1)
    return 0
```

**Layer 2: Generation metrics** (LLM 答对没?)

```python
def answer_correctness(generated, expected):
    """用 LLM-as-judge 评 (避免 BLEU/ROUGE 弱信号)"""
    judge_prompt = f"""
    Question: {sample.query}
    Expected answer: {expected}
    Generated answer: {generated}

    Is the generated answer factually equivalent to expected?
    Score 1-5: 5=perfect, 4=mostly correct, 3=partial, 2=mostly wrong, 1=wrong.
    Return JSON: {{"score": int, "reason": str}}
    """
    return claude_sonnet_46.judge(judge_prompt)
```

**Layer 3: Operational metrics** (能 production 跑吗?)

```python
ops_metrics = {
    'ingest_throughput_docs_per_min': ...,
    'index_size_gb': ...,
    'query_p50_ms': ...,
    'query_p99_ms': ...,
    'cost_per_query_usd': ...,
    'cost_per_1k_docs_index_usd': ...,
}
```

### 5.3 Ablation 方法 (你 ConvFinQA 做过)

不要只比 baseline vs final, 要逐个 component ablate:

```python
# 9 个 ablation variants
configs = [
    ('A', 'baseline', dict(chunker='fixed_512', retriever='dense')),
    ('B', '+recursive', dict(chunker='recursive', retriever='dense')),
    ('C', '+structure', dict(chunker='structure_aware', retriever='dense')),
    ('D', '+hybrid', dict(chunker='structure_aware', retriever='hybrid')),
    ('E', '+rerank', dict(chunker='structure_aware', retriever='hybrid_rerank')),
    ('F', '+overlap', dict(chunker='structure_aware', retriever='hybrid_rerank', overlap=0.3)),
    ('G', '+metadata', dict(...)),  # heading_path injection
    ('H', '+query_rewrite', dict(...)),
    ('I', 'final', dict(...)),
]

results = []
for label, name, cfg in configs:
    metrics = run_eval(cfg, eval_set)
    results.append({'label': label, 'name': name, **metrics})

# Output as table — interviewer 一目了然
```

### 5.4 Slice analysis (关键, 但常被忽略)

```python
def slice_eval(results, eval_set):
    """每个 slice 单独看"""
    slices = {
        'by_query_type': groupby('query_type'),
        'by_difficulty': groupby('difficulty'),
        'by_language': groupby('language'),
        'by_doc_type': groupby('doc_type'),
    }

    for slice_name, group_fn in slices.items():
        print(f'\n=== {slice_name} ===')
        for group, samples in group_fn(eval_set):
            recall = mean(recall_at_k(...) for s in samples)
            print(f'  {group}: recall@10 = {recall:.1%} (n={len(samples)})')
```

**为啥重要**: overall +3pp 但 multi-hop -10pp 是不可接受的. Slice eval 暴露这种问题.

### 5.5 Cost-Quality Pareto

不是「越高 recall 越好」, 而是 cost 维度:

```python
import matplotlib.pyplot as plt

# Plot all configs
for cfg in results:
    plt.scatter(cfg['cost_per_query'], cfg['recall_at_10'], label=cfg['name'])

plt.xlabel('Cost per query ($)')
plt.ylabel('Recall@10')
plt.title('Pareto frontier')
```

通常 Pareto frontier 上 3-4 个点, 选哪个看 product 的 quality vs cost 偏好.

### 5.6 LLM-as-judge calibration (你 ConvFinQA 经验)

- 用 LLM-judge 评 answer correctness 之前, 必须验证 judge 自己准:
  - Hand-label 50 samples
  - 跑 judge on 同 50 samples
  - 计算 Cohen's kappa, 要求 > 0.6 (substantial agreement)
- 多个 judge ensemble (Claude Sonnet 4.6 + Gemini 3 Pro + GPT-5.5) 取众数, 减少单 model bias
- Calibration 每季度重做

### 5.7 Production 持续 eval

上线后不是结束:

```python
# 每天 sample 200 production queries
async def daily_eval():
    samples = sample_production_queries(n=200)
    for q in samples:
        retrieved = retrieve(q)
        answer = generate(q, retrieved)
        # LLM-judge 评 retrieve + answer 质量
        scores = await judge_pipeline(q, retrieved, answer)
        log_to_dashboard(scores)

    # Alert 如果 7-day rolling avg recall 跌 > 3pp
    if rolling_recall_drop() > 0.03:
        page_oncall('RAG recall regression')
```

---

# Part 3 · 把 5 个问题串起来看

这 5 个问题其实是**回答 "Why THAT chunking" 的 5 个证据层**:

1. **Taxonomy** 让你能说「我考虑了所有 6 种」
2. **Decision factors** 让你能说「我评估了这 5 维」
3. **Multi-modal** 让你能说「我针对 table / code / formula 做了特殊处理」
4. **Metadata** 让你能说「我让 chunk 自带身份证」
5. **Eval** 让你能说「这是数字, 不是猜测」

面试场把这 5 层都讲出来, 加上「我自己在 BNPL chatbot / ConvFinQA 上做过 ablation」, 就是 staff-level RAG design 水准.

---

## 必问 clarifying questions

**1. Corpus shape**

> "How many docs, average length, language mix, has structure (markdown/headings) or raw text, has tables/code/images?"

**2. Query patterns**

> "User queries — short keyword or natural language? Multi-hop or factoid? Per-tenant or global? Have query logs?"

**3. Latency budget**

> "User-facing real-time (<500ms) or async (seconds OK)? Affects whether we can rerank."

**4. Quality bar**

> "What recall target? 80% is OK for many; 95% for medical/legal requires more eval + rerank."

**5. Update frequency**

> "Docs change daily? Weekly? Affects ingestion architecture (semantic chunking is slow)."

**6. Budget**

> "Embedding $ + storage $ + inference $ — any hard caps? Affects chunker choice (late chunking is 2x cost)."

---

## 5 步框架 (sample 45-min answer)

| 时长 | 阶段 |
|---|---|
| 0-3 min | Clarify corpus + queries + latency + quality |
| 3-10 min | Anchor: what I chose + 1-sentence why (claim) |
| 10-25 min | Walk down 6 chunking strategies, why I picked X (evidence) |
| 25-35 min | Multi-modal handling (tables/code) + metadata strategy |
| 35-45 min | Eval methodology + slice analysis numbers |
| 45-55 min | When I'd change choice (100x scale / different domain) |
| 55-60 min | Honest gaps + what I'd test next |

---

## 简历专属 reframe

你的 **BNPL chatbot RAG** + **ConvFinQA reference impl** + **Voice agent multi-market**:

| 题 | 你做过 |
|---|---|
| Chunking choice with eval | BNPL FAQ RAG — 必经过 chunking debug |
| Hybrid retrieval | BNPL 含 product/order ID, hybrid 是 production reality |
| Rerank empirical α | BNPL: BM25 weight 0.3 → recall +14pp |
| Ablation methodology | ConvFinQA 9-variant ablation (critic 4/358 honest result) |
| Multi-modal chunking | ConvFinQA 表格特殊处理 |
| Multilingual + tokenizer | Voice agent 6 语言 |
| Production drift monitoring | Voice agent 7 markets 持续 eval |

**主动 quote**:

> "For BNPL chatbot at TikTok, I went through this decision: started fixed-512 + pure dense, recall@5 was 71%. Customer queries had **product codes (PayLater, BNPL_ID_3.x) + Bahasa / Vietnamese / Thai混杂**. Added **BM25 weighted 0.3** → recall jumped to 86%. Then for "why was my refund delayed" type queries that need multi-paragraph context, did **structure-aware chunking + 30% overlap + bge-reranker-v2-m3 rerank top-50→10** → recall 91%, answer-correctness +12pp.
>
> **Key lesson**: I never picked these numbers up-front. **9-variant ablation on stratified eval set** (factoid / multi-hop / product-specific / long-context / edge-case x 20 each). The BM25 0.3 weight was the **only** value that beat dense alone across all 5 slices — anything higher hurt multi-hop. **Eval first, optimize second**.
>
> Honest gap: I didn't try **late chunking with Jina v3** — would be next iteration if I had to push recall past 95%."

---

## 5 follow-ups

**Q1**: "Why not just use Pinecone / Weaviate defaults?"

**A**: Vector DB defaults are **infrastructure choices, not retrieval-quality choices**. Pinecone's default fixed-size chunker assumes generic prose — works for blog ingestion demo, breaks on technical docs with tables. **Retrieval-quality gap between default and tuned is consistently 15-20pp recall@10 in our benchmarks**. In production, defaults cost user trust.

**Q2**: "Tell me about a time chunking strategy failed."

**A**: BNPL chatbot v1 — fixed-512 + dense. User asks "refund timeline" → retrieval gets chunk "Refunds processed via..." (first half) but not "...within 14 days" (second half, in next chunk). Bot answered "refunds processed via the system" — **useless**. Fix: structure-aware + 30% overlap + heading-path metadata. Specifically: the heading "Refund Policy > Timeline" injected as chunk prefix gave dense retrieval the strong signal to find both halves.

**Q3**: "Cross-encoder rerank is expensive. How do you make it production-fast?"

**A**: 4 levers:
1. **Distill** to smaller cross-encoder (50M params) — `cross-encoder/ms-marco-TinyBERT-L-2-v2`
2. **Batch** rerank top-50 in 1 forward pass (vLLM / SGLang for embedding service)
3. **Cache** hot queries (1h TTL, 30% hit rate typical)
4. **Skip threshold**: if top-1 bi-encoder score > 0.92, skip rerank entirely

In BNPL we got rerank latency from 180ms → 50ms via 1 + 3 + 4.

**Q4**: "Multi-language docs — does chunking strategy change?"

**A**: Yes:
- **Tokenizer choice critical** — using English BPE on Chinese/Thai grossly miscounts tokens, chunks become 3-5x larger than intended
- Use **multilingual tokenizer** (BGE-M3, XLM-R)
- **Sentence boundary** detection differs (Chinese has no spaces, Thai has no punctuation between words) — need language-specific sent splitter (e.g., `pythainlp`, `jieba`)
- **Per-language BM25** indices (Chinese tokenization is different problem entirely)
- **Cross-lingual retrieval**: user queries in English, docs in Indonesian — works with multilingual embedding model (BGE-M3, multilingual-e5)

**Q5**: "Long-context models (Gemini 3 Pro 2M context, Claude Opus 4.7 1M) — does RAG become obsolete?"

**A**: **Not yet, but use case narrows**:
- Long-context **wins** when: corpus < 1M tokens, **static**, no privacy issues, latency tolerant (long context is slow). E.g., "analyze this contract" with 50-page doc.
- **RAG wins** when: corpus huge / dynamic / multi-tenant / per-user / cost-sensitive (Gemini 3 Pro 2M context at $2/M input → $4/query, RAG retrieves 5k context → $0.01/query).
- **Hybrid pattern (most common 2026)**: RAG retrieves top-K, feeds 50-100k into long-context Claude Opus 4.7 → best precision (RAG narrows search) + best reasoning (long context model digests). This is what we use in BNPL chatbot for complex queries.

---

## ❌ 易错点 (top 10)

1. **"我用了 X 因为 X 是 standard"** — no reasoning, sounds copy-paste
2. **不知道 alternatives** — limited experience signal
3. **过度 optimize without eval** — guessing, not engineering
4. **Defensive when challenged** — interview is about thinking, not being right
5. **只讲 chunking, 忽略 retrieval pairing** — they're joint decision
6. **忽略 multi-modal** (tables/code) — common in production
7. **没 metadata 设计** — chunks 只有文本是 amateur
8. **没 slice analysis** — overall recall 是不够的
9. **没考虑 long-context model 替代** — out of date
10. **只讲 happy path** — 不提 fallback / degradation

---

## ✅ 加分项 (top 10)

1. **6 chunking + 5 retrieval systematic taxonomy**
2. **9-variant ablation** with concrete numbers
3. **Slice analysis** (by query type / difficulty / lang)
4. **Multi-modal chunking** (tables / code / formulas)
5. **Metadata as first-class** (heading_path, ACL, freshness)
6. **Joint chunking + retrieval** design
7. **Cost-Quality Pareto** thinking
8. **LLM-judge calibration** discipline (你 ConvFinQA 经验)
9. **Long-context awareness** (2026 reality)
10. **Honest gaps** ("I didn't try late chunking yet")

---

## 一句话总结

> **Chunking strategy = (corpus shape × query patterns × retrieval method × embedding limit × latency budget) → evaluate empirically → ship the one that wins on slice metrics, not overall**.
>
> 不是「选择 chunker」, 而是「设计一套 retrieval system, chunker 是其中一个旋钮」.

---

## Cheat Sheet (印 1 页)

```
6 chunking strategies:
  1. Fixed-size token (baseline only)
  2. Recursive char/sentence (LangChain default, safe)
  3. Semantic (主题混杂, 2-3x slow ingest)
  4. Structure-aware (markdown/PDF, +heading_path) ⭐
  5. Hierarchical (parent-child, 长文 + 完整上下文)
  6. Late chunking (Jina v3, context-aware embed)

5 retrieval methods:
  1. Dense only (semantic)
  2. BM25 only (exact term)
  3. Hybrid (dense+BM25, α=0.6-0.8) ⭐ production default
  4. ColBERT (5x storage, max precision)
  5. + Cross-encoder rerank top-50→10 ⭐ if budget allows

Production middle ground:
  Structure-aware chunking (300-500 tokens, 30% overlap)
  + Hybrid retrieval (dense 0.7 + BM25 0.3, RRF fusion)
  + bge-reranker-v2-m3 rerank top-50 → top-10
  + Metadata: heading_path, doc_id, tenant_id, freshness, ACL

5 decision factors:
  1. Corpus characteristics (length, structure, tables)
  2. Query patterns (entity density, multi-hop)
  3. Retrieval method (joint design)
  4. Embedding model context limit
  5. Latency budget

Multi-modal:
  Tables → integral chunk + row chunks + NL description
  Code → AST-aware (function/class boundary)
  Formulas → LaTeX → NL + keep original
  Lists → unit when small, header-replicated when split
  Images → CLIP embed + caption + surrounding text

Metadata (必备):
  chunk_id, doc_id, chunk_order
  heading_path, chunk_type, section_level
  source_url, created_at, updated_at, author
  acl_list, tenant_id (硬过滤)
  freshness_score, confidence, review_status
  language, topic_tags
  embedding_model_version

Eval methodology:
  Layer 1: Retrieval (recall@10, NDCG@10, MRR)
  Layer 2: Generation (answer correctness via LLM-judge)
  Layer 3: Operational (latency, cost, ingest throughput)
  Ablation: 9 variants, isolated changes
  Slice: by query_type / difficulty / language
  Cost-Quality Pareto: not just highest recall
  LLM-judge calibration: Cohen's kappa > 0.6

红线:
  - 默认 512 token, 没 overlap → 句子截断
  - 表格当 prose 切 → 信息丢失
  - 没 metadata → 检索后 LLM 不知道在说啥
  - 凭 intuition 选 → eval-driven 才 production-grade
  - 切完再换 embedding model → 必须 re-embed 全部

When you'd change choice:
  100x scale (1M → 100M docs):
    - Sharded vector DB (per-shard chunking 一致)
    - Distilled embedding (768 → 256 dim)
    - Skip rerank or distill rerank model
    - Tiered hot/cold storage
  Multi-modal-heavy (images, video):
    - CLIP / SigLIP for visual
    - 分别 index, query-time fusion
  Tabular data heavy:
    - 不要硬切, 用 text-to-SQL 或 row-level retrieve
  Long-context Gemini 3 Pro / Claude Opus 4.7:
    - Hybrid pattern (RAG narrows, long-context digests)
    - For small static corpora, maybe skip RAG entirely
```
