## Q17 · 小型 RAG pipeline + 为 chunking 策略辩护

> "Given a folder of documents (mixed PDF / markdown / HTML), build a **small RAG pipeline** end-to-end: chunk → embed → index → retrieve → format → LLM. **Code it.** Then **defend your chunking strategy** — why this chunk size? Why this overlap? How would you evaluate it?"

**Round**: Coding (60 min)
**出处**: Exponent 2026 FDE · 公司: **Anthropic**, OpenAI, Scale AI, Cohere
**难度**: Hard
**主要技能**: end-to-end RAG, chunking decisions, eval methodology, vector DB

---

## 📖 术语速查 (本题用到的)

> RAG 是 AI Engineer 必懂. 这堆术语不熟 = 听不懂 chunking / reranker / MMR 在说啥.

### RAG 核心概念

| 术语 | 解释 |
|---|---|
| **RAG (Retrieval-Augmented Generation)** ⭐ | "先检索后生成" 范式. 把外部知识 embed → 检索 → 塞给 LLM 当 context. 解决 LLM 知识截止 + hallucination. |
| **Ingest (摄取)** | 把文档解析 + chunk + embed + 入 index 的离线过程. |
| **Retrieval (检索)** | 用 query 找 top-k 相似 chunk. 在线过程. |
| **Grounded** | LLM 回答**只用** retrieved context, 不靠自己 parametric knowledge. |
| **"I don't know" fallback** ⭐ | 检索分数低时让 LLM 说 "我不知道" 而不是瞎编. 法律 / 医疗必备. |
| **Citation / inline `[n]`** | 答案里 `[1] [2]` 引用 retrieved chunk. UI 可点回原文. |
| **Faithfulness** | 答案是否忠于 retrieved context (没编). 跟 relevance 不同. |
| **Provenance** | 每个 entity / 答案附 `{doc, page, char_range}`. |

### Chunking 策略

| 术语 | 解释 |
|---|---|
| **Chunking** ⭐ | 把长文档切小块 (LLM context 装得下 + embedder 质量稳). 这题考核心. |
| **Fixed-size chunking** | 每 N tokens 一刀. 简单但切句子中间. |
| **Heading-aware chunking** ⭐ | 按 markdown `#` / HTML `<h1>` 切. 语义边界. |
| **Recursive chunking** | 先按 section, section 太大再按 paragraph, 再按 sentence. langchain `RecursiveCharacterTextSplitter`. |
| **Overlap** | 相邻 chunk 重叠 tokens. 100/12% 常用, 防答案跨边界丢. |
| **Propositional chunking** | LLM 把段落改写成独立 "命题" (e.g., "A 是 B" 一句话), 再 embed. recall 高但 ingest 慢. |
| **Late chunking** | Jina AI 2024 新方法. 先 embed 全文 (long-context embedder), 再切 embedding. 每 chunk embed 见全文 context. |
| **Sliding window** | 同 overlap 概念. |

### Embedding

| 术语 | 解释 |
|---|---|
| **Embedding (嵌入)** ⭐ | 把 text 映射成固定维度 dense 向量 (e.g., 768/1536d). 语义近 → 向量距离近. |
| **`text-embedding-3-small`** | OpenAI 经典 embedder, 1536d, $0.02/1M tokens, fast. |
| **`text-embedding-3-large`** | OpenAI 大模型, 3072d, 更准更贵. |
| **`bge-base-en-v1.5` (BGE)** | BAAI 开源 embedder, 768d, 自托管 GPU 跑. 跟 OpenAI 同档质量, 数据合规 + 0 边际成本. |
| **`e5-large` / `mxbai-embed-large`** | 其他开源选项. |
| **MRL / Matryoshka embedding** | 一个 model 输出可截断: 1024d truncate 到 256d 还能用. cost / quality 灵活权衡. |
| **L2 normalize** ⭐ | embedding 除以模长. 让 inner product = cosine similarity. |
| **Cosine similarity vs Inner product (dot product)** | 同向量在 normalize 后等价. Cosine ∈ [-1, 1], inner product 无 bound. |
| **Dimension (维度)** | embedding 长度. 768 / 1024 / 1536 / 3072 常见. 高 → 准 + 内存大. |

### Vector DB / Index

| 术语 | 解释 |
|---|---|
| **FAISS** ⭐ | Facebook 开源 ANN 库. `IndexFlatIP` (brute), `IndexHNSWFlat`, `IndexIVFPQ` 等. |
| **`IndexFlatIP`** | Brute-force inner product. < 100k vectors 适用. 100% recall. |
| **HNSW** | 图算法 ANN, 详见 Q18. |
| **Chroma** | 开源 vector DB, 持久化 + metadata filter 友好. Demo 阶段标配. |
| **pgvector** | PostgreSQL 向量扩展. 跟业务表共库, 减依赖. |
| **Pinecone / Weaviate / Qdrant / Milvus** | 托管 / 开源 vector DB. 本题题面禁 Pinecone. |
| **HyDE (Hypothetical Document Embedding)** | LLM 先回答 (hypothetically), embed 答案, 用它去 retrieve. 对 vague query 有奇效. |

### Retrieval 算法

| 术语 | 解释 |
|---|---|
| **top-k retrieval** | 取最相似 k 个 chunk. |
| **MMR (Maximal Marginal Relevance)** ⭐ | 在 relevance 和 diversity 之间平衡: `λ × rel - (1-λ) × max_sim_to_selected`. 防 top-5 全是 near-duplicate. |
| **BM25** | 经典 sparse retrieval, 基于 term frequency. 对 exact keyword (产品代码, 名字) 强. |
| **Hybrid retrieval** ⭐ | BM25 + vector 结合. Vector 抓语义, BM25 抓 exact match. |
| **RRF (Reciprocal Rank Fusion)** | Hybrid 融合算法: `score = Σ 1/(k+rank_i)`. 不需要分数 normalize. |
| **Reranker (cross-encoder)** ⭐ | 二段式: vector retrieve top-100 → cross-encoder rerank → top-5. 准但慢. `bge-reranker-large` 是常用. |
| **Cross-encoder vs Bi-encoder** | Bi-encoder = query / doc 独立 embed (快); cross-encoder = query+doc 一起过 model (准 + 慢). |
| **Query rewriting / Query expansion** | LLM 改写 query 成 3 个变体 → 各 retrieve → union. 对模糊 query 有奇效. |

### Eval / Metrics

| 术语 | 解释 |
|---|---|
| **Golden set** ⭐ | 人工标注的 Q&A 测试集 (50-200 examples). Defend chunking 全靠它. |
| **Recall@k** ⭐ | top-k 里有没有正确 doc. |
| **MRR (Mean Reciprocal Rank)** | 正确 doc 的平均排名倒数. 1.0 = 永远 top-1. |
| **nDCG** | 排序质量指标, 考虑相关性分级. |
| **Judge LLM** | 用 GPT-4 评分 (faithfulness / completeness / citation). LLM-as-judge. |
| **RAGAS / DeepEval** | RAG eval 库, 含 faithfulness / context-precision / answer-relevance 等指标. |
| **Ablation study** | 一次改一个变量看效果. 这题 chunking 4 strategy × N 参数 = N 次 ablation. |

### LLM API

| 术语 | 解释 |
|---|---|
| **`gpt-4o-mini`** | OpenAI 小模型, 便宜 + 快. RAG 默认 LLM. |
| **`gpt-4o` (Omni)** | OpenAI 旗舰. 更准更贵, 用于 judge / 高 stakes. |
| **Context window** | LLM 单次能装多少 token. GPT-4o = 128k, Claude 3.5 = 200k. |
| **System / User / Assistant message** | LLM API 标准消息类型. |
| **`temperature=0`** | LLM 输出随机性最低. RAG 用 0 求确定. |
| **Streaming response** | LLM token-by-token 返回, 用户体感快. |

### 上下文工程

| 术语 | 解释 |
|---|---|
| **Context stuffing** | 把 N 个 chunk 全塞进 prompt. 主流策略. |
| **"Lost in the middle"** | 长 context 中部信息被 LLM 忽略的现象 (paper). 重要内容放头尾. |
| **Prompt template** | 固定结构 + 变量替换的 prompt. f-string 或 jinja2. |
| **Score threshold** | top-1 score < N → 返 "I don't know" 不调 LLM, 省钱 + 防幻觉. |

---

## 这道题在考什么

RAG 看起来 "load + split + embed + retrieve + LLM" 五行代码搞定 (`langchain.RAG`). 但题目说**defend your chunking strategy + eval methodology** — 这是真功夫:

1. **End-to-end build 能力** — 5 个 component 都要能写, 不是只熟悉一段
2. **Chunking 策略选择 + 论证** — fixed size vs heading-aware vs late chunking vs propositional chunking, 不同 doc 类型选不同
3. **Embedding 模型选型** — `text-embedding-3-small` vs `bge-base` vs `e5-large` — 维度 / latency / 成本 trade-off
4. **Vector DB 选型** — FAISS (本地, 快) vs Chroma (持久, 元数据 filter 友好) vs pgvector (跟 Postgres 一起) — 这道题用 FAISS 或 Chroma 都行
5. **Retrieval 策略** — top-k, MMR, hybrid (BM25 + vector), reranker — 你能不能讲明白何时上哪个
6. **Eval 方法** — golden Q&A set, retrieval recall@k, end-to-end faithfulness/relevance metrics — 没 eval 没法 defend
7. **真做 prompt 设计** — context 怎么塞, citation 怎么带, "I don't know" 兜底
8. **Cost / latency awareness** — 多大 chunk 多少 token, embed 多少钱, retrieve p99 多少, LLM call 多少

Anthropic 这种公司极其在乎 chunking — 错的 chunking 让 Claude 看不到答案, 客户骂 Claude 不准.

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|------|--------|--------|
| 1 | Clarify | 0-5 min | doc 类型, 体量, query latency budget, faithfulness | "5 things..." |
| 2 | Architecture | 5-10 min | ingest + query pipeline 双图 | "Two stages: offline ingest, online query." |
| 3 | Implement ingest | 10-30 min | load → chunk → embed → index | "I'll write ingestion first." |
| 4 | Implement query | 30-40 min | retrieve → rerank → format → LLM | "Now the query side." |
| 5 | Defend chunking | 40-50 min | 4 个 strategy 对比 + 选哪个 why | "Why 800 tokens + 100 overlap?" |
| 6 | Eval | 50-55 min | golden set, recall@k, faithfulness | "Three metrics I'd measure..." |
| 7 | Discuss | 55-60 min | upgrades: hybrid retrieval, rerank, late chunking | "Three production upgrades..." |

---

## 必问 clarifying questions

**1. Doc 类型 + 体量**

> "PDFs only or mixed (PDF, MD, HTML, DOCX)? How many docs / total size?"

Why: PDF 要 pdfplumber (Q13); HTML 要 BeautifulSoup; DOCX 要 python-docx. 1000 doc 用 in-memory; 1M doc 上 production vector DB.

**2. Query 类型**

> "Factoid Q&A ('what is X')? Summary ('summarize Y')? Multi-hop ('compare X and Y')?"

Why: Factoid 适合 small chunk; summary 适合 large chunk + multiple retrieved; multi-hop 需要 query rewriting.

**3. Latency budget**

> "p99 query latency target? 1s, 5s, 30s?"

Why: 5s 内 LLM call 主导; 不需要 cache embed; 1s 必须 small chunk + small model + cached query.

**4. Updates / freshness**

> "Are docs static or updated daily? Need to re-embed on update?"

Why: Daily update → incremental ingest + versioning; static → 离线 batch.

**5. Faithfulness 要求**

> "Hallucination tolerance? Must cite source? Must say 'I don't know' on unknown?"

Why: Legal/medical 必须 grounded + cite; consumer Q&A 一般 lenient.

**6. Eval**

> "Do we have a golden Q&A set, or do we build one?"

Why: 没 golden 没法 measure; 必须建.

**7. Cost**

> "Embed budget? LLM call budget per query?"

Why: 1M docs × 1k token × `text-embedding-3-small` $0.02/1M ≈ $20 一次 embed. LLM $0.01/query × 100k query = $1k/day.

---

## 详细解题流程

### Step 1: Design decisions (5-10 min)

**Architecture**:

```
Offline ingest (one-time / nightly):
┌─────────┐  ┌──────┐  ┌────────┐  ┌───────┐  ┌───────┐
│ Loader  │→ │ Clean│→ │ Chunker│→ │Embedder│→ │ Index │
│ PDF/MD/ │  │ text │  │heading │  │ (E5 /  │  │(FAISS │
│ HTML    │  │      │  │ -aware │  │ openai │  │ + meta│
└─────────┘  └──────┘  └────────┘  └───────┘  │ store)│
                                              └───────┘
                                                  │
                                                  ▼
                                         ondisk: index.faiss + chunks.jsonl

Online query:
                ┌──────────┐    ┌──────────┐    ┌──────┐    ┌──────┐    ┌───┐
   query  →→→  │ Embed Q  │→→  │ Retrieve │→→  │ MMR  │→→  │ Build│→→  │LLM│
                │          │    │ top 20   │    │ rerank│    │prompt│    │   │
                └──────────┘    └──────────┘    └──────┘    └──────┘    └───┘
                                       │
                                       ↓ load chunk text + metadata
                                  ┌────────────┐
                                  │ chunks.jsonl│
                                  └────────────┘
```

**关键 choices** (开口讲):

- **Chunker**: heading-aware (markdown headers → sections); fixed-size 800 token + 100 overlap; never split mid-sentence
- **Embedder**: `text-embedding-3-small` (OpenAI, 1536-dim, $0.02/1M tokens) — fast cheap good quality. Self-hosted alt: `BAAI/bge-base-en-v1.5` 768-dim.
- **Index**: `FAISS IndexFlatIP` for <100k chunks (brute force fine); `IndexHNSWFlat` for 100k-10M; pgvector + IVF for >10M (本题用 FAISS Flat)
- **Retrieval**: top 20 by cosine, rerank top 5 by MMR diversity
- **Prompt**: explicit instructions "use only context", citation markers `[1] [2]`, "I don't know" on insufficient context

### Step 2: Initial implementation (15-25 min)

```python
"""
Small RAG pipeline: ingest folder, query against it.

Components:
  - DocLoader: PDF/MD/HTML to text
  - HeadingAwareChunker: split by markdown headings, then by token count
  - Embedder: OpenAI text-embedding-3-small (or local model)
  - FaissIndex: in-memory FAISS + persisted to disk
  - Retriever: top-k by cosine, MMR rerank
  - PromptBuilder: stuff with citations
  - LLM: chat completion with context
"""
import os
import json
import re
import logging
import hashlib
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import numpy as np

log = logging.getLogger('rag')


# ============ Data types ============

@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    section: str = ''        # heading path, e.g. "Pricing > Enterprise"
    page: int = 0
    token_count: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float


# ============ Loaders ============

def load_text_file(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace')


def load_pdf(path: Path) -> str:
    import pdfplumber
    out = []
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages):
            t = page.extract_text() or ''
            if t:
                out.append(f'<page n="{i+1}">\n{t}\n</page>')
    return '\n\n'.join(out)


def load_html(path: Path) -> str:
    from bs4 import BeautifulSoup
    html = path.read_text(encoding='utf-8', errors='replace')
    soup = BeautifulSoup(html, 'html.parser')
    # Remove script/style
    for tag in soup(['script', 'style']):
        tag.decompose()
    # Heuristic: keep semantic structure as markdown-ish
    parts = []
    for tag in soup.find_all(['h1', 'h2', 'h3', 'p', 'li']):
        if tag.name.startswith('h'):
            parts.append('#' * int(tag.name[1]) + ' ' + tag.get_text(strip=True))
        else:
            parts.append(tag.get_text(strip=True))
    return '\n\n'.join(p for p in parts if p)


def load_doc(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == '.pdf':
        return load_pdf(path)
    if ext in ('.html', '.htm'):
        return load_html(path)
    if ext in ('.md', '.txt'):
        return load_text_file(path)
    raise ValueError(f'unsupported file type: {ext}')


# ============ Chunker (heading-aware + size-bounded) ============

# Quick token estimate (good enough): 1 token ≈ 4 chars for English
def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


HEADING_RE = re.compile(r'^(#{1,6})\s+(.+?)\s*$', re.MULTILINE)


def split_by_headings(text: str) -> list[tuple[str, str]]:
    """Returns list of (heading_path, body) sections."""
    sections = []
    last = 0
    stack = []  # list of (level, title)
    for m in HEADING_RE.finditer(text):
        if last < m.start():
            body = text[last:m.start()].strip()
            if body:
                path = ' > '.join(t for _, t in stack)
                sections.append((path, body))
        level = len(m.group(1))
        title = m.group(2).strip()
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, title))
        last = m.end()
    if last < len(text):
        body = text[last:].strip()
        if body:
            path = ' > '.join(t for _, t in stack)
            sections.append((path, body))
    if not sections:
        sections.append(('', text))
    return sections


SENTENCE_END = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')


def split_into_sentences(text: str) -> list[str]:
    return SENTENCE_END.split(text)


def chunk_section_by_size(
    body: str,
    max_tokens: int = 800,
    overlap_tokens: int = 100,
) -> list[str]:
    """
    Split a section into chunks of approximately max_tokens.
    Respect sentence boundaries; chunks overlap by overlap_tokens.
    """
    sents = split_into_sentences(body)
    chunks = []
    current: list[str] = []
    current_tokens = 0
    for sent in sents:
        st = estimate_tokens(sent)
        if current_tokens + st > max_tokens and current:
            chunks.append(' '.join(current))
            # Build overlap from tail
            tail = []
            tail_tokens = 0
            for s in reversed(current):
                t = estimate_tokens(s)
                if tail_tokens + t > overlap_tokens:
                    break
                tail.insert(0, s)
                tail_tokens += t
            current = tail
            current_tokens = tail_tokens
        current.append(sent)
        current_tokens += st
    if current:
        chunks.append(' '.join(current))
    return chunks


def chunk_document(text: str, doc_id: str, *,
                    max_tokens: int = 800,
                    overlap_tokens: int = 100) -> list[Chunk]:
    """Heading-aware + size-bounded chunker."""
    out: list[Chunk] = []
    for section, body in split_by_headings(text):
        # Page extraction (if we have <page n="N"> markers from PDF loader)
        page_re = re.compile(r'<page n="(\d+)">\n(.*?)\n</page>', re.DOTALL)
        page_matches = list(page_re.finditer(body))
        if page_matches:
            # PDF section: chunk per-page (preserves page metadata)
            for pm in page_matches:
                page = int(pm.group(1))
                page_body = pm.group(2)
                for piece in chunk_section_by_size(page_body, max_tokens, overlap_tokens):
                    cid = hashlib.sha1(f'{doc_id}|{page}|{piece[:50]}'.encode()).hexdigest()[:16]
                    out.append(Chunk(
                        chunk_id=cid, doc_id=doc_id, text=piece,
                        section=section, page=page,
                        token_count=estimate_tokens(piece),
                    ))
        else:
            for piece in chunk_section_by_size(body, max_tokens, overlap_tokens):
                cid = hashlib.sha1(f'{doc_id}|{section}|{piece[:50]}'.encode()).hexdigest()[:16]
                out.append(Chunk(
                    chunk_id=cid, doc_id=doc_id, text=piece,
                    section=section, token_count=estimate_tokens(piece),
                ))
    return out


# ============ Embedder ============

class OpenAIEmbedder:
    def __init__(self, model='text-embedding-3-small', batch_size=128):
        from openai import OpenAI
        self.client = OpenAI()
        self.model = model
        self.batch_size = batch_size
        self.dim = 1536 if 'small' in model else 3072

    def embed(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            resp = self.client.embeddings.create(model=self.model, input=batch)
            for j, e in enumerate(resp.data):
                out[i + j] = e.embedding
        # L2 normalize for cosine
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return out / norms


class LocalEmbedder:
    """Self-hosted bge-base-en-v1.5 via sentence-transformers."""
    def __init__(self, model_name='BAAI/bge-base-en-v1.5'):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> np.ndarray:
        emb = self.model.encode(texts, normalize_embeddings=True, batch_size=32)
        return emb.astype(np.float32)


# ============ Index ============

class FaissIndex:
    def __init__(self, dim: int):
        import faiss
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self.chunks: list[Chunk] = []

    def add(self, embeddings: np.ndarray, chunks: list[Chunk]):
        assert embeddings.shape[0] == len(chunks)
        self.index.add(embeddings)
        self.chunks.extend(chunks)

    def search(self, query: np.ndarray, k: int) -> list[tuple[int, float]]:
        scores, ids = self.index.search(query.reshape(1, -1), k)
        return [(int(i), float(s)) for i, s in zip(ids[0], scores[0]) if i != -1]

    def save(self, path: Path):
        import faiss
        path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(path / 'index.faiss'))
        with open(path / 'chunks.jsonl', 'w') as f:
            for c in self.chunks:
                f.write(json.dumps(asdict(c)) + '\n')

    @classmethod
    def load(cls, path: Path, dim: int) -> 'FaissIndex':
        import faiss
        inst = cls(dim)
        inst.index = faiss.read_index(str(path / 'index.faiss'))
        with open(path / 'chunks.jsonl') as f:
            for line in f:
                d = json.loads(line)
                inst.chunks.append(Chunk(**d))
        return inst


# ============ Retriever ============

def mmr_rerank(
    query_emb: np.ndarray,
    candidates: list[RetrievedChunk],
    candidate_embs: np.ndarray,
    top_k: int,
    lambda_: float = 0.5,
) -> list[RetrievedChunk]:
    """Maximal Marginal Relevance: balance relevance and diversity."""
    if not candidates:
        return []
    selected: list[int] = []
    remaining = list(range(len(candidates)))
    while remaining and len(selected) < top_k:
        if not selected:
            # Pick highest similarity to query first
            best = max(remaining, key=lambda i: candidates[i].score)
        else:
            def score_fn(i):
                rel = candidates[i].score
                max_sim = max(
                    float(np.dot(candidate_embs[i], candidate_embs[j]))
                    for j in selected
                )
                return lambda_ * rel - (1 - lambda_) * max_sim
            best = max(remaining, key=score_fn)
        selected.append(best)
        remaining.remove(best)
    return [candidates[i] for i in selected]


class Retriever:
    def __init__(self, index: FaissIndex, embedder, top_k_initial: int = 20,
                 top_k_final: int = 5, use_mmr: bool = True):
        self.index = index
        self.embedder = embedder
        self.top_k_initial = top_k_initial
        self.top_k_final = top_k_final
        self.use_mmr = use_mmr
        # cache embeddings of all chunks for MMR (in-memory; 5k chunks × 1536 × 4 = ~30MB)
        self._embeddings: Optional[np.ndarray] = None

    def _ensure_embeddings(self):
        if self._embeddings is not None:
            return
        # In real impl, reuse the embeddings used to build the index
        # (FAISS stores them, can be reconstructed). For demo, re-embed.
        texts = [c.text for c in self.index.chunks]
        self._embeddings = self.embedder.embed(texts)

    def retrieve(self, query: str) -> list[RetrievedChunk]:
        q_emb = self.embedder.embed([query])[0]
        results = self.index.search(q_emb, self.top_k_initial)
        candidates = [RetrievedChunk(self.index.chunks[i], s) for i, s in results]
        if not self.use_mmr or len(candidates) <= self.top_k_final:
            return candidates[:self.top_k_final]
        self._ensure_embeddings()
        cand_embs = np.stack([self._embeddings[i] for i, _ in results])
        return mmr_rerank(q_emb, candidates, cand_embs, self.top_k_final)


# ============ Prompt builder ============

PROMPT_TEMPLATE = """You are a careful assistant answering using ONLY the provided context.

Rules:
1. Use ONLY information from the numbered context excerpts below.
2. If the context does not contain the answer, say "I don't have enough information to answer."
3. Cite sources inline with [1], [2], etc. matching the excerpt numbers.
4. Be concise.

Context:
{context}

Question: {question}

Answer:"""


def build_prompt(question: str, chunks: list[RetrievedChunk], max_context_tokens: int = 4000) -> str:
    parts = []
    total = 0
    for i, rc in enumerate(chunks, 1):
        tag = f'[{i}] ({rc.chunk.doc_id} > {rc.chunk.section or "_"} > p{rc.chunk.page or "_"})'
        snippet = rc.chunk.text
        snippet_tokens = estimate_tokens(snippet)
        if total + snippet_tokens > max_context_tokens:
            # Truncate last snippet
            allowed = max_context_tokens - total
            snippet = snippet[:allowed * 4]
            parts.append(f'{tag}\n{snippet}')
            break
        parts.append(f'{tag}\n{snippet}')
        total += snippet_tokens
    return PROMPT_TEMPLATE.format(context='\n\n'.join(parts), question=question)


# ============ LLM ============

class OpenAIChat:
    def __init__(self, model='gpt-4o-mini'):
        from openai import OpenAI
        self.client = OpenAI()
        self.model = model

    def chat(self, prompt: str, temperature: float = 0.0) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=temperature,
        )
        return resp.choices[0].message.content


# ============ Pipeline orchestration ============

class RAGPipeline:
    def __init__(self, index: FaissIndex, embedder, llm,
                 retriever: Optional[Retriever] = None):
        self.index = index
        self.embedder = embedder
        self.llm = llm
        self.retriever = retriever or Retriever(index, embedder)

    @classmethod
    def build(cls, folder: Path, *, embedder=None, llm=None,
              max_tokens: int = 800, overlap_tokens: int = 100):
        embedder = embedder or OpenAIEmbedder()
        all_chunks: list[Chunk] = []
        for path in folder.rglob('*'):
            if not path.is_file():
                continue
            if path.suffix.lower() not in ('.pdf', '.md', '.txt', '.html', '.htm'):
                continue
            try:
                text = load_doc(path)
            except Exception as e:
                log.warning('skip %s: %s', path, e)
                continue
            doc_id = path.stem
            chunks = chunk_document(text, doc_id,
                                     max_tokens=max_tokens,
                                     overlap_tokens=overlap_tokens)
            all_chunks.extend(chunks)
            log.info('chunked %s -> %d chunks', path.name, len(chunks))
        log.info('total %d chunks; embedding...', len(all_chunks))
        emb = embedder.embed([c.text for c in all_chunks])
        index = FaissIndex(embedder.dim)
        index.add(emb, all_chunks)
        return cls(index, embedder, llm or OpenAIChat())

    def answer(self, question: str) -> dict:
        retrieved = self.retriever.retrieve(question)
        prompt = build_prompt(question, retrieved)
        ans = self.llm.chat(prompt)
        return {
            'answer': ans,
            'sources': [
                {'chunk_id': r.chunk.chunk_id, 'doc_id': r.chunk.doc_id,
                 'section': r.chunk.section, 'page': r.chunk.page,
                 'score': r.score}
                for r in retrieved
            ],
        }
```

**讲给面试官**: "I've kept it modular: Loader, Chunker, Embedder, Index, Retriever, PromptBuilder, LLM. Each is swappable — local embedder vs OpenAI, FAISS vs Chroma, gpt-4o-mini vs Claude — and I can run unit tests on each piece independently."

### Step 3: Eval (5-10 min)

```python
# eval.py
@dataclass
class GoldExample:
    question: str
    expected_doc_ids: set[str]    # which docs should be retrieved
    reference_answer: str         # human-written


def eval_retrieval(pipeline: RAGPipeline, gold: list[GoldExample]) -> dict:
    """Recall@k and MRR over a gold set."""
    recall_at_1 = 0
    recall_at_5 = 0
    mrr_sum = 0.0
    for ex in gold:
        retrieved = pipeline.retriever.retrieve(ex.question)
        doc_ids = [r.chunk.doc_id for r in retrieved]
        # Find rank of first matching doc
        rank = None
        for i, did in enumerate(doc_ids):
            if did in ex.expected_doc_ids:
                rank = i + 1
                break
        if rank == 1: recall_at_1 += 1
        if rank and rank <= 5: recall_at_5 += 1
        if rank: mrr_sum += 1.0 / rank
    n = len(gold)
    return {
        'recall@1': recall_at_1 / n,
        'recall@5': recall_at_5 / n,
        'mrr': mrr_sum / n,
        'n': n,
    }


def eval_faithfulness(pipeline: RAGPipeline, gold: list[GoldExample]) -> dict:
    """Use a judge LLM to score whether answer is grounded in retrieved context."""
    judge = OpenAIChat(model='gpt-4o')
    judged = []
    for ex in gold:
        result = pipeline.answer(ex.question)
        prompt = f"""Question: {ex.question}
Reference answer: {ex.reference_answer}
Model answer: {result['answer']}

Rate 1-5:
- Faithfulness (does answer match reference, no hallucination)?
- Completeness (does it cover key facts)?
- Citation (does it cite [n] correctly)?
Return JSON: {{"faithfulness": N, "completeness": N, "citation": N}}"""
        score_str = judge.chat(prompt)
        try:
            scores = json.loads(score_str)
            judged.append(scores)
        except Exception:
            pass
    if not judged:
        return {'faithfulness': 0, 'completeness': 0, 'citation': 0}
    return {
        'faithfulness': sum(j['faithfulness'] for j in judged) / len(judged),
        'completeness': sum(j['completeness'] for j in judged) / len(judged),
        'citation': sum(j['citation'] for j in judged) / len(judged),
        'n': len(judged),
    }
```

### Step 4: Defend chunking strategy (10 min)

**Why heading-aware + 800 token + 100 overlap?** (这一段是面试 critical):

```
4 Strategies Compared:

A. Fixed-size only (e.g., every 500 tokens):
   PROS: dead simple, predictable.
   CONS: cuts mid-section, mid-sentence; semantically incoherent chunks → retrieval recall drops.
   USE WHEN: docs have no structure (plain text logs).

B. Heading-aware (split by markdown # / HTML h1-h6):
   PROS: semantically coherent — each chunk is one topic.
   CONS: section sizes vary wildly. One section might be 100 tokens (intro), another 5000 (deep dive).
   USE WHEN: docs have clear hierarchical structure (manuals, books, docs sites).

C. Heading-aware + size-bounded (我们的 choice):
   1. First split by heading (preserve section boundaries)
   2. If a section is > max_tokens, recursively split by paragraph then sentence
   3. Add overlap between sub-chunks
   PROS: combines A's predictability with B's semantic boundaries.
   CONS: complex, but worth it.
   USE WHEN: mixed structured docs (most real-world).

D. Late chunking (Jina AI 2024):
   1. Embed entire doc as one long context
   2. Take embeddings of token-positions, then chunk THEM
   PROS: each chunk's embedding sees the FULL doc context
   CONS: needs long-context embedder (e.g., jina-embed-v2 8k), slow.
   USE WHEN: contextual references matter ('it', 'the above').
```

**Defend chosen params**:

- **max_tokens = 800**: 
  - Empirically, `text-embedding-3-small` quality plateaus past ~500 tokens; degrades > 1500
  - GPT-4o context limit allows ~5 chunks × 800 = 4k token of context
  - Big enough to contain a typical answer's full evidence (1-2 paragraphs)
  - Small enough that retrieval hits the exact section, not whole chapter
- **overlap = 100 (≈ 12%)**:
  - 0 overlap risks splitting an answer's two halves into different chunks
  - 200+ overlap wastes 25% of embedding budget on duplicated content
  - 100 is enough to catch boundary cross-references
- **Heading-aware**:
  - Markdown headers are author's semantic divisions — respect them
  - For PDFs: detect heading via font-size heuristic (pdfplumber gives `chars[].size`)

**Eval to defend**:

```
Build golden set of 50 Q&A pairs.
For each chunking config, measure:
  - Recall@5: did right doc appear in top-5?
  - MRR: how high did right doc rank?
  - Faithfulness (judge LLM): is answer grounded?

Sample table:
  Config                     R@5   MRR   Faith
  fixed 500 no overlap      0.62   0.41   3.8
  fixed 500 overlap 100      0.71   0.49   4.0
  heading-aware unbounded    0.68   0.52   4.1   ← sections too big sometimes
  heading + 800/100 (ours)   0.81   0.61   4.4   ← winner
  late chunking              0.83   0.66   4.5   ← marginal gain, 4x latency

Defense: heading-aware + 800/100 is on Pareto frontier — best quality at acceptable cost.
```

### Step 5: Test (skipped real-LLM, here's structure)

```python
# Mock embedder + LLM for tests
class FakeEmbedder:
    dim = 4
    def embed(self, texts):
        return np.array([[hash(t) & 0xFFFF for _ in range(4)] for t in texts],
                         dtype=np.float32)

class FakeLLM:
    def chat(self, prompt, temperature=0.0):
        return f"Answer based on context. [1]"

def test_chunk_doc_basic():
    text = "# Title\n\nParagraph one. Sentence two.\n\n## Sub\n\nMore content."
    chunks = chunk_document(text, 'doc1', max_tokens=20, overlap_tokens=5)
    assert all(c.doc_id == 'doc1' for c in chunks)
    assert any('Title' in c.section or 'Sub' in c.section for c in chunks)

def test_chunk_respects_max_tokens():
    text = ' '.join(['word'] * 1000)
    chunks = chunk_document(text, 'd', max_tokens=50, overlap_tokens=10)
    for c in chunks:
        assert c.token_count <= 60  # max + slack

def test_chunk_overlap():
    text = ' '.join(['word'] * 1000)
    chunks = chunk_document(text, 'd', max_tokens=50, overlap_tokens=20)
    # Adjacent chunks should share some text
    for i in range(len(chunks) - 1):
        tail = chunks[i].text[-50:]
        head = chunks[i+1].text[:50]
        # Not exact, but should be non-zero overlap by word
        words_tail = set(tail.split())
        words_head = set(head.split())
        assert words_tail & words_head

def test_mmr_diverse():
    # If 5 candidates are near-duplicates, MMR picks the most diverse subset
    pass  # detailed test omitted; structure shown
```

### Step 6: Production discussion (5 min)

**Upgrades a real prod RAG ships with**:

1. **Hybrid retrieval**: BM25 + vector. Vector gets semantic match; BM25 catches exact keyword (product codes, names). `λ × bm25 + (1-λ) × cosine`.
2. **Reranker**: After top-100 from vector, rerank with cross-encoder `BAAI/bge-reranker-large`. 10x precision boost on top-5.
3. **Query rewriting**: LLM-rewrite user's question into 3 search-friendly variants, retrieve each, union.
4. **HyDE**: Hypothetical Document Embedding — LLM answers question (hypothetically), embed the answer, retrieve docs similar to it.
5. **Multi-vector / ColBERT**: per-token embedding for finer-grained match. Slower but more recall.
6. **Late chunking**: as Strategy D above.
7. **Citations**: inline `[1]` matching numbered context — UI clickable.
8. **"I don't know" detection**: if top-1 score < threshold, return "I don't know" without LLM call.
9. **Cache**: query embedding cache (5-min TTL) + answer cache for popular queries.
10. **Incremental ingest**: doc hash + diff — only re-embed changed sections.

---

## 完整代码 (Production-ready)

完整 module 已在 Step 2. Install + run:

```bash
pip install openai faiss-cpu pdfplumber beautifulsoup4 sentence-transformers numpy
export OPENAI_API_KEY=sk-...

# Build:
python -c "
from rag import RAGPipeline
from pathlib import Path
p = RAGPipeline.build(Path('./docs'))
p.index.save(Path('./out'))
"

# Query:
python -c "
from rag import RAGPipeline, FaissIndex, OpenAIEmbedder, OpenAIChat, Retriever
from pathlib import Path
emb = OpenAIEmbedder()
idx = FaissIndex.load(Path('./out'), emb.dim)
p = RAGPipeline(idx, emb, OpenAIChat(), Retriever(idx, emb))
print(p.answer('What does the document say about pricing?'))
"
```

---

## 复杂度分析

| 阶段 | Time | Notes |
|------|------|-------|
| Ingest (per doc) | O(D / chunk_size) embed calls | bottleneck: embedding API |
| Build FAISS Flat | O(N × d) | N chunks, d dim |
| Search Flat | O(N × d) per query | brute force |
| Search HNSW | O(log N × d) | ANN, 10x faster |
| MMR rerank | O(K^2 × d) | K=20-50 candidates |
| LLM call | O(context_tokens) | ~1-3s |

**Sample numbers**: 1000 PDFs × 50 pages avg → ~50k chunks. Embedding cost: ~$10. Flat index search p99 ~5ms. End-to-end query p99 ~2s (LLM dominates).

---

## Gao Xin 简历专属 reframe

- **BNPL chatbot (RAG + intent routing)**: 这就是我的主项目. 我们用过 Chroma, 后来切 pgvector (跟业务表共库). Chunking 用过 fixed 512 → 切到 heading-aware 800/100 后 recall@5 从 0.65 → 0.81. Embedder 用 `bge-base-en` 自托管 (vLLM), 因为 cost + 数据合规.
- **ConvFinQA**: 9-variant ablation 里有 4 个变量是 chunking strategy (fixed vs heading vs propositional vs late chunking) — 这道题考的就是我做过的事.
- **Voice agent (7 markets)**: agent 需要 retrieve policy doc 实时回答客户. 同样 pipeline 但 latency 苛刻 (p95 < 800ms), 所以 chunk 小 (400 token), top-k 小 (3), 用 reranker.
- **Internal Agent Platform**: tool 文档 ingest 成 RAG, agent 用它选 tool.

**面试一句话**: "I've shipped this exact pipeline three times at TikTok — BNPL chatbot, voice agent, internal tool docs. The single biggest learning: heading-aware chunking + a reranker gets you from 'demo good' to 'customer happy'."

---

## 5 个 Follow-ups

**Q1**: "How would you handle a 5000-page legal document?"

A: 几个 lever:
1. **Hierarchical retrieval**: 一级 retrieve = section level (chunk 大粒度), 二级 retrieve = paragraph level
2. **Pre-LLM filter**: 用 BM25 first cut 5000 → 500, vector cut 500 → 20
3. **Multi-stage RAG**: q1 retrieve outline → q2 retrieve specific section → q3 final answer
4. **Long-context model**: Claude 200k context — 可以一次塞 100 chunks, 但 cost 高

**Q2**: "Chunking 错了 retrieval 是不是就死?"

A: Yes — chunking 是 RAG 第一道闸. 错的 chunk = right doc 找不到 = retrieve fail = LLM hallucinate. 我做过的 ablation: chunk size 从 200 → 800, recall@5 涨 30%. 比换 embedder 影响大.

**Q3**: "你怎么 know retrieval 找不到时, LLM 不胡说?"

A: 多层防御:
1. **Score threshold**: top-1 score < 0.7 → return "I don't know"
2. **Prompt instruction**: "If context doesn't contain answer, say 'I don't know'"
3. **Faithfulness eval (judge LLM)**: 每周抽 100 个 prod query 跑 judge
4. **Hallucination detector**: a separate classifier (e.g., self-RAG, RAGAS faithfulness score)

**Q4**: "If user query is too vague, what to do?"

A: 多策略:
1. **Query rewrite**: LLM 改写成 3 个 specific variant
2. **Clarification turn**: 反问 "Did you mean X or Y?"
3. **HyDE**: generate hypothetical answer, embed, retrieve docs similar to hypothesis
4. **Fallback to general LLM**: 没好 retrieval result 时, prompt LLM say "I'll answer from general knowledge, this may be outdated"

**Q5**: "Cost optimization?"

A:
1. **Cheaper embedder**: `text-embedding-3-small` $0.02/1M vs `bge-base` 自托管 $0 (但 GPU)
2. **Smaller chunk**: 5 × 400 token instead of 5 × 800 → halve LLM input cost
3. **Cache embeddings of common queries**
4. **Use cheaper LLM for filter, expensive LLM for final**: gpt-4o-mini retrieve → gpt-4o synthesize
5. **Pre-compute embeddings of FAQ → direct semantic search → bypass LLM**

---

## 死路答法

1. **`langchain.load_chain('rag')`** — 调用现成 chain 不写代码, 不能 defend
2. **Fixed 500 char split** — 切句子中间, retrieval recall 烂
3. **No overlap** — 答案跨 chunk 边界丢
4. **No heading awareness** — 一整 chapter 一个 chunk
5. **Hardcoded `top_k=3`** — 没考虑 MMR 多样性
6. **No "I don't know" path** — LLM 胡说
7. **No citation** — 客户看到答案不知道哪里来的
8. **No eval set** — defend chunking 全靠拍脑袋
9. **No persistence** — index 重启丢
10. **No incremental ingest** — 加一个 doc 全部 re-embed

---

## 加分项

**Production gotchas**:

- **Doc dedupe**: 客户上传同 PDF 多次, 用 file_hash 去重
- **Version**: doc 改了, 旧 chunk 留 audit, 新 chunk 上线 (versioned index)
- **Metadata filter**: 限定 `doc_type=policy AND region=ID` 后 retrieve — Chroma / pgvector 都支持
- **Reranker**: cross-encoder 给 top-50 重排, precision 提升大
- **Streaming answer**: LLM token-by-token 流式返回, 用户体感快
- **Observability**: log `query, retrieved_chunks, score_dist, top_score, latency_ms, llm_tokens`
- **A/B framework**: 跑两个 chunking strategy 各 10% traffic, compare faithfulness
- **PII / safety**: ingest 前 redact, retrieve 后 check no PII leaked
- **Multi-language**: detect lang → pick lang-specific embedder
- **Refresh**: nightly cron re-embed changed docs + reindex
- **Recovery**: index corruption → rebuild from chunks.jsonl

---

## 一句话总结

> **Loader → heading-aware 800/100 chunker → text-embed-3-small → FAISS Flat → top-20 + MMR top-5 → prompt with citations → LLM with "I don't know" guardrail. Defend chunking via golden set + recall@5 + MRR + faithfulness judge.**

---

## Cheat Sheet

```python
# Pipeline:
load_doc() -> text
chunk_document(text, max_tokens=800, overlap=100)  # heading-aware + size-bounded
embedder.embed(texts) -> ndarray  # text-embedding-3-small (1536d) or bge-base (768d)
FaissIndex.add(embeddings, chunks)
retrieve(query) -> top-20 cosine -> mmr_rerank -> top-5
build_prompt(question, chunks) -> string with [n] citations + "I don't know" rule
llm.chat(prompt) -> answer

# Chunking choice (defend):
#   heading-aware (semantic) + size-bounded (predictable) + overlap (boundary)
#   800 tokens: embedder quality peaks; LLM context budget allows 5 chunks
#   100 overlap (~12%): catches cross-references without wasting too much

# Eval:
#   golden Q&A set (50-200 examples)
#   Retrieval: recall@1, recall@5, MRR
#   Generation: judge LLM scores faithfulness / completeness / citation

# Upgrades:
#   - Hybrid (BM25 + vector)
#   - Cross-encoder reranker (bge-reranker-large)
#   - Query rewriting / HyDE
#   - Late chunking (Jina)
#   - Score-threshold "I don't know"

# Cost:
#   embed 1M tokens with text-embed-3-small = $0.02
#   LLM query gpt-4o-mini 4k context = $0.0006
#   Cache query embeds + answers for common queries

# Don't:
#   fixed-size cut mid-sentence
#   no overlap
#   no MMR (all top-5 redundant)
#   no eval set (can't defend)
#   no "I don't know" path
```
