## 题目

> "First-pass retrieval gives you top-50 candidates. **Reranker** picks top-10. Explain why you need it, the tradeoffs, and how you'd evaluate."

或追问形态:

> "Cohere rerank vs cross-encoder vs LLM-as-judge for reranking — when each?"

**出处**: Google FDE T2 / Cohere / Vertex AI Vector Search / Vespa / Weaviate / OpenAI / Anthropic Forward Deployed 等 RAG 相关 round 必问.

**Round**: RAG Quality / Reranking (45 min)

---

## 这道题在考什么

考你 **bi-encoder ≠ cross-encoder** 区别 + production reranker engineering:

1. **First-stage vs second-stage** retrieval 是两个不同 model class
2. **Cross-encoder mechanics** —— 为什么 slower 但 accurate (cross-attention)
3. **Latency-accuracy trade-off** —— tune k 平衡
4. **Reranker options** —— Cohere / bge / mxbai / LLM-judge / 自训
5. **Cascade optimization** —— cheap → expensive 多阶段
6. **Latency engineering** —— GPU batch / quant / distill
7. **Eval methodology** —— NDCG > recall, slice, A/B
8. **Domain finetuning** —— hard-negative mining, synthetic data

不考「reranker 是什么」, 考「你 production 上线过 reranker 没, 把 NDCG 提了多少」.

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**Bi-encoder**: query 和 doc **独立** embedding 到同一向量空间, score = cosine. 优势 doc 可 pre-index, 1M doc 也能秒级 ANN; 劣势看不见 query-doc 交互. 代表模型: `text-embedding-3-large`, `gemini-embedding-001`, `bge-large-zh`, `e5-mistral-7b`.

**Cross-encoder**: 把 `[CLS] query [SEP] doc [SEP]` **一起** 进 Transformer, cross-attention 算 relevance score. 不能 pre-index (没 query 不能算), 必须 per-query 推理. 代表模型: `bge-reranker-v2-m3`, `Cohere rerank-3`, `mxbai-rerank-large-v1`.

**Reranker**: 通常指 cross-encoder 用于二阶段 reranking. 第一阶段 bi-encoder 召回 top-50, 第二阶段 reranker 看 (query, doc) pair 重排成 top-10.

**LLM-as-judge**: 用 LLM (Gemini 3 Pro / Claude Opus 4.7) 直接判断 doc 是否相关, 可以是 pointwise score / pairwise compare / listwise rank. 最贵, 但最 nuanced.

---

## 2. 这个问题的核心是什么

设想没有 reranker 的 pure bi-encoder retrieval 灾难:

```
Query: "iPhone 15 Pro Max dual SIM setup"

Bi-encoder top-10:
  1. "iPhone 12 dual SIM guide"          ← cluster到通用 iPhone 高分
  2. "Samsung Galaxy dual SIM"            ← "dual SIM" 命中, 但 wrong device
  3. "iPhone 13 mini eSIM"                ← 又一个 iPhone
  4. "iPhone 15 Pro Max user guide"       ← 真正想要的, 但排第 4
  5. "Dual SIM activation FAQ"            ← 通用
  6. "iPad cellular setup"
  7. "iPhone 14 review"
  8. "Apple Watch cellular"
  9. "Android dual SIM"
  10. "Verizon dual SIM"

LLM 看 top 3, 答 "请按 iPhone 12 步骤" — 但 user 用的是 15 Pro Max.
```

**问题**:

- Bi-encoder 把 query 和 doc 各自压缩到 768 维, **细粒度匹配丢失**
- "iPhone 15 Pro Max" 和 "iPhone 12" 在 embedding 空间太近
- Top-50 里其实有正确答案, 但**排在第 4-20 位**, 没被 LLM 看到
- Top-1 / top-3 错答影响 user 信任

**加 cross-encoder reranker 解法**:

```
Stage 1 (bi-encoder): top-50 召回
  (recall 已经 92%, 但 ordering 烂)

Stage 2 (cross-encoder rerank): 看每对 (query, doc) 联合
  - bge-reranker-v2-m3 score (query, doc_4) > score (query, doc_1)
  - 因为 cross-attention 看到 "Pro Max" 和 doc_4 里 "Pro Max" 对齐
  - 重新排序

Final top-10:
  1. "iPhone 15 Pro Max user guide"       ← 升到第 1
  2. "iPhone 15 Pro Max eSIM activation"  ← 升到第 2
  3. "Dual SIM activation FAQ"
  ...

LLM 答正确.
NDCG@10 从 0.65 → 0.83 (+18 percentage points)
Latency +180ms (A10G GPU batch)
```

---

## 3. 典型流程图

```
┌─────────────────────────────────────────────────────────────────┐
│           Multi-stage Retrieval + Rerank Pipeline                │
└─────────────────────────────────────────────────────────────────┘

  Query
    │
    ▼
  ┌──────────────────────────────────────────┐
  │  Stage 0: Query understanding             │
  │  - rewrite / multi-query / HyDE           │
  └──────────────┬───────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
  ┌──────────┐       ┌──────────┐
  │ BM25     │       │ Dense    │
  │ top-100  │       │ ANN      │
  │          │       │ top-100  │
  └─────┬────┘       └─────┬────┘
        │                  │
        └────────┬─────────┘
                 ▼
         ┌───────────────┐
         │  RRF fusion   │
         │  → top-100    │
         └───────┬───────┘
                 │
                 ▼
   ┌─────────────────────────────┐
   │  Stage 2a: Cheap reranker    │
   │  bge-reranker-v2-base (CPU)  │
   │  or fast small model         │
   │  100 → 25 candidates         │
   │  ~ 100ms                     │
   └─────────────┬───────────────┘
                 │
                 ▼
   ┌─────────────────────────────┐
   │  Stage 2b: Expensive reranker│
   │  bge-reranker-large (GPU)    │
   │  or Cohere rerank-3 API      │
   │  25 → 10 candidates          │
   │  ~ 200ms                     │
   └─────────────┬───────────────┘
                 │
                 ▼
   ┌─────────────────────────────┐
   │  (Optional) Stage 2c:        │
   │  LLM-as-judge for top-3      │
   │  Gemini 3 Pro / Opus 4.7     │
   │  10 → 3 candidates           │
   │  ~ 3-5s (high-stake only)    │
   └─────────────┬───────────────┘
                 │
                 ▼
            Final top-K to LLM context
```

**Cascade 收益**: 比单一 reranker 跑全 100 candidates 省 50% 时间, 精度不降.

---

## 4. 关键 reranker 模型分类表

| Reranker | 部署 | Latency (50 docs A10G) | Cost | Quality | 何时用 |
|---|---|---|---|---|---|
| **bge-reranker-v2-m3** | Self-host | 80-150ms | Free (GPU 卡钱) | Good multilingual | Default open-source |
| **bge-reranker-v2-large** | Self-host | 200-400ms | Free | Better | 单语种英文 |
| **Cohere rerank-3** | API | 150-250ms | $1 / 1K calls | Excellent | 不想自部署 GPU |
| **mxbai-rerank-large-v1** | Self-host | 250-400ms | Free | Excellent | 自部署 Cohere-class |
| **JaColBERT** | Self-host | 50-100ms | Free | Good (Japanese) | 日语 / late interaction |
| **LLM-as-judge (Gemini 3 Pro)** | API | 5-10s | $0.10-0.30/query | Best | 高 stake, top-3 final |
| **LLM-as-judge (Claude Opus 4.7)** | API | 8-15s | $0.30-0.80/query | Best | 法律 / 医疗 / 资金 |
| **Domain-finetuned bge** | Self-host | 100-300ms | Training $1-10 | Best in domain | 有 1K-10K labeled pairs |

production 90% 用 `bge-reranker-v2-m3` 或 `Cohere rerank-3`. 高 stake 加 LLM-as-judge top-3.

---

## 5. 具体业务场景 (5 个高频)

### 场景 A: BNPL chatbot RAG (你的工作背景)

7 个市场, 多语言, 客服文档检索:
- First stage: hybrid BM25 + multilingual dense → top-50
- Rerank: `bge-reranker-v2-m3` (天然 multilingual)
- 不需要 LLM-judge (cost prohibitive for chatbot QPS)
- 实测: NDCG@5 从 0.71 → 0.83, latency +180ms

### 场景 B: E-commerce product ranking

用户搜 "red running shoes size 9":
- First stage: BM25 + dense → top-50
- Multi-objective rerank: relevance + price + stock + delivery + review_score + personalize
- Learning-to-rank (LightGBM / XGBoost LambdaRank) 而不是 pure cross-encoder
- A/B with revenue / CVR, 不只 NDCG

### 场景 C: Q&A passage selection

RAG 返回 50 段, 选 3 段 feed LLM 答题:
- Reranker QA-finetuned (Cohere rerank-3 trained on MS-MARCO)
- Span-level extract: 不只选 passage, 用 QA 模型抽 answer span
- Multi-passage fusion: 答案跨段 → 选 complementary (not redundant)
- Confidence gating: top-1 score 低 → 'no good answer, escalate'

### 场景 D: Code search — function from monorepo

Dev agent 搜 "function that parses JWT":
- First stage: 3 个 index (code BM25 + comment dense + doc dense) → top-50
- Reranker 专门 fine-tune on (PR description, function code) pairs
- Symbol match boost: `parse_jwt(token)` 命名严格匹配优先
- Test pair boost: 有 test 的 function > 无 test
- Recency: 1 月前改的 > 5 年前未改

### 场景 E: Legal / medical (高 stake)

Lawyer / doctor agent, 不能错答:
- First stage: hybrid retrieve top-50
- Stage 2a: bge-reranker → top-25
- Stage 2b: domain-finetuned reranker (legal-rerank on case law) → top-10
- Stage 2c: LLM-as-judge (Claude Opus 4.7) on top-10 → top-3
- 严格 citation, post-LLM 验
- Latency tolerable: 5-15s (用户接受高质量)
- Cost: $0.30-1/query, 但单 query 价值高

---

## 6. 工程上要做什么 (实现 checklist)

**模型选择**:

1. **Domain audit**: generic web / e-commerce / legal / code / medical?
2. **Latency budget**: < 200ms / < 1s / < 10s? 决定 cascade 深度
3. **QPS**: 1 / 10 / 100 / 1000? 决定 self-host vs API
4. **Quality target**: top-1 / top-3 / top-10 accuracy?
5. **Cost target**: $0.01 / $0.10 / $1 per query?

**部署**:

6. **GPU**: A10G / A100 选型, FP16 default, INT8 if extra speed needed
7. **Batching**: 单 query 50 pairs → single forward, 不要 for-loop
8. **Triton / vLLM** inference server, 不是直接 Python serve
9. **Auto-scaling**: per-replica GPU util > 70% trigger scale up
10. **Failure isolation**: reranker down → fallback to first-stage ordering

**Cascade 设计**:

11. **Stage 1 first-stage**: BM25 + dense + RRF → top-100
12. **Stage 2a cheap reranker**: bge-base → top-25 (cuts 75%)
13. **Stage 2b expensive reranker**: Cohere / bge-large → top-10
14. **(Optional) Stage 2c LLM judge**: top-3 for high-stake

**Eval**:

15. **Eval set**: 200 (query, [graded_docs])
16. **Metrics**: NDCG@k (核心), MRR, recall@k stability
17. **Slice**: by domain / query length / doc length / has_acronym
18. **A/B in prod**: CTR, time-to-answer, thumbs

**Domain finetune (optional)**:

19. **Collect labels**: production click data + 1K human label
20. **Hard-negative mining**: top-ranked-but-wrong from current model
21. **Synthetic data**: LLM generate (query, positive, negative)
22. **Train**: bge-base + LoRA, 1 GPU-day, 1-3% NDCG gain typical

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **Bi-encoder used for reranking** | No cross-attention, 与 first stage 同质 |
| 2 | **Rerank top-1000** | latency × 20, 10s+ |
| 3 | **No first-stage to narrow** | 不能 cross-encode 1M docs |
| 4 | **No eval set** | 'feels better' 调参 |
| 5 | **Single reranker for all domain** | Legal / code 用 generic 不够 |
| 6 | **LLM-as-judge for everything** | $$$, 1M query × $0.30 = $300K |
| 7 | **No cascade** | 单 reranker 跑全 100, 浪费 |
| 8 | **CPU 单条 forward** | 50 × 30ms = 1.5s, GPU batch 80ms |
| 9 | **No quantization** | FP32 model, 2x more memory + slower |
| 10 | **Forget recall stays same** | Reranker 只改 ordering, 不改 set |
| 11 | **No latency budget** | "我先把 reranker 加上" 然后系统超时 |
| 12 | **Caching not used** | 相同 (query, top-50) 重复算 |

---

## 一句话总结 (Part 1)

> **Reranker = 「cross-encoder 看 (query, doc) joint, cross-attention 抓细粒度匹配, 必须 cascade 限 candidate 数, GPU batch + FP16 才能上线, NDCG 是核心指标」**.
>
> 不是 "加 reranker 就完事", 是 **cascade + latency engineering + eval slice** 的工程系统.

---

# Part 2 · 5 个深度工程问题

## ⚙️ Problem 1: Bi-encoder vs Cross-encoder 数学

### 1.1 Bi-encoder forward

```
Input:  query q (tokens t_q)
        doc   d (tokens t_d)

Forward (independent):
  E_q = Transformer(t_q) → q_emb (768d)        # query encoder
  E_d = Transformer(t_d) → d_emb (768d)        # doc encoder
  (same weights, two passes)

Score:
  sim(q, d) = cos(q_emb, d_emb) = q_emb · d_emb / (||q_emb|| ||d_emb||)
```

**关键性质**:

- Doc encoder 只看 doc, 看不见 query
- Query encoder 只看 query, 看不见 doc
- **没有 query-doc 交互**, 只有"独立表征 + 后置 cosine"
- Doc embedding 可以 pre-compute 离线存

**这是它能 scale 到 1B doc 的原因 — ANN 搜事先 build 好的 index**.

### 1.2 Cross-encoder forward

```
Input:  query q, doc d

Concatenate:
  input = [CLS] q [SEP] d [SEP]
                  ↑       ↑
              full cross-attention here

Forward (joint):
  out = Transformer(input)
  cls_repr = out[0]            # [CLS] hidden state
  score = Linear(cls_repr) → relevance ∈ [0, 1]
```

**关键性质**:

- query 和 doc 的所有 token 都能互相 attend
- 每对 (q, d) 独立 forward, 不能 pre-index
- 每次 inference 都跑 full Transformer 一遍

### 1.3 数学差异 — Attention 视角

**Bi-encoder**:
```
Final score = f(E_q(q)) · f(E_d(d))     # late interaction
              ↑              ↑
        独立, 没看到对方
```

**Cross-encoder**:
```
Final score = Linear(CLS(Transformer([q; d])))
                                          ↑
              attention 矩阵 |q+d| × |q+d|, 所有 token 互相看
```

具体看 attention 矩阵:

```
Bi-encoder (无 cross):
  Q: [q1, q2, ..., qn]       attention 内部 q-q
  D: [d1, d2, ..., dm]       attention 内部 d-d
  Score: cos(pool(Q), pool(D))

Cross-encoder:
  Combined: [q1, ..., qn, d1, ..., dm]
  Attention matrix (n+m) × (n+m), 含 4 个 block:
    [q-q | q-d ]
    [d-q | d-d ]
    ↑      ↑
  q-d block 让模型学到 "q 的某个 token 应该和 d 的某个 token 对齐"
```

**举例**: query "iPhone 15 Pro Max", doc "iPhone 15 Pro Max user guide"
- Bi-encoder: 两个 embedding 各自 pool, 都接近 "高端 iPhone 文档"
- Cross-encoder: attention 把 query 的 "Pro Max" token 和 doc 的 "Pro Max" token 对上, score 显著 > query 的 "Pro Max" vs doc "iPhone 12" 的得分

### 1.4 量化对比 (实测数字)

| Model class | Recall@50 | NDCG@10 | Latency / query |
|---|---|---|---|
| Bi-encoder only (bge-large) | 92% | 0.68 | 30ms |
| + cross-encoder rerank (bge-rerank-v2-m3) | 92% (no change) | 0.83 | 30ms + 150ms = 180ms |
| + cross-encoder rerank (Cohere rerank-3) | 92% | 0.85 | 30ms + 200ms = 230ms |

**Key**: rerank 不提升 recall (set 不变), 提升 NDCG / MRR (ordering 更好).

### 1.5 ColBERT — 中间路线

ColBERT (late interaction):
- 每 doc 存 token-level embedding (不是单一 pooled vector)
- Query 时用 MaxSim: `Σ_q max_d cos(emb_q, emb_d)`
- 比 bi-encoder 强 (token 级匹配), 比 cross-encoder 弱 (无 full attention)
- 可 pre-index, 但 index 大 30-100x

```python
# ColBERT pseudo
def colbert_score(q_token_embs, d_token_embs):
    """对每个 query token, 找 d 里最像的, 累加"""
    score = 0.0
    for q_emb in q_token_embs:
        max_sim = max(cos(q_emb, d_emb) for d_emb in d_token_embs)
        score += max_sim
    return score
```

适用: 想要 cross-encoder 精度但又要 scale.

---

## ⚙️ Problem 2: Reranker Options 决策矩阵

### 2.1 Open-source self-host

**bge-reranker-v2-m3** (推荐 default):
```python
from sentence_transformers import CrossEncoder
model = CrossEncoder('BAAI/bge-reranker-v2-m3')
scores = model.predict([(query, doc.text) for doc in candidates])
```
- 多语言 (100+ 语种)
- 568M params
- A10G batch 50, FP16, ~150ms
- 完全 free, MIT-like license
- 实测 BEIR avg NDCG@10 = 0.55

**bge-reranker-v2-large**:
- 1.3B params
- 单语种英文略好
- ~300-400ms

**mxbai-rerank-large-v1**:
- Cohere-class quality, 1B params
- 完全开源
- ~250-400ms

### 2.2 API services

**Cohere rerank-3**:
```python
import cohere
co = cohere.Client(api_key=...)
resp = co.rerank(
    model='rerank-english-v3.0',
    query=query,
    documents=[c.text for c in candidates],
    top_n=10,
)
ranked = [candidates[r.index] for r in resp.results]
```
- $1 / 1K queries
- 150-250ms p99
- 不需要 GPU 自部署
- multilingual 模型可选

**Voyage rerank**:
- 跟 Cohere 同类, AnthropicAI 子公司
- $0.50 / 1K (略便宜)

### 2.3 LLM-as-judge

**Pointwise**:
```python
prompt = f"""Rate the relevance of the document to the query on a scale 0-3:
- 3: Perfect match
- 2: Highly relevant
- 1: Partially relevant
- 0: Irrelevant

Query: {query}
Document: {doc.text}

Score (just the number):"""

scores = []
for doc in candidates:
    resp = gemini_pro.generate(prompt.format(query=query, doc=doc), max_tokens=2)
    scores.append(int(resp.strip()))
```

**Pairwise** (更准, 但 N² 调用):
```python
prompt = f"""Which document better answers the query?

Query: {query}
Doc A: {doc_a.text}
Doc B: {doc_b.text}

Respond with just A or B."""
```

**Listwise** (一次给 10 个让 LLM 排):
```python
prompt = f"""Rank these documents by relevance to the query.

Query: {query}

Docs:
[1] {doc1}
[2] {doc2}
...
[10] {doc10}

Return ranked indices in JSON: {{"ranking": [3, 7, 1, ...]}}"""
```

**Cost / latency** (10 candidates):

| Mode | Gemini 3 Pro | Claude Opus 4.7 |
|---|---|---|
| Pointwise 10 calls | $0.05, 8s | $0.15, 12s |
| Pairwise 45 calls | $0.22, 30s | $0.65, 50s |
| Listwise 1 call | $0.02, 3s | $0.06, 5s |

Listwise 最划算, 但 LLM 一次排 10 个稳定性差; pointwise 中庸; pairwise 最准最贵.

### 2.4 Domain finetune

```python
# 准备 (query, positive_doc, negative_doc) triplet
training_data = [
    {'query': '...', 'positive': '...', 'negative': '...'},
    ...
]

# Fine-tune bge-reranker-base on triplets (Margin loss)
from sentence_transformers import CrossEncoder, InputExample
train_examples = [
    InputExample(texts=[ex['query'], ex['positive']], label=1.0) for ex in training_data
] + [
    InputExample(texts=[ex['query'], ex['negative']], label=0.0) for ex in training_data
]

model = CrossEncoder('BAAI/bge-reranker-base', num_labels=1)
model.fit(
    train_dataloader=DataLoader(train_examples, batch_size=32),
    epochs=3,
    warmup_steps=100,
    output_path='./bge-reranker-bnpl',
)
```

**Hard-negative mining**:
```python
def mine_hard_negatives(query, positive_doc_id, current_model, top_k=20):
    """从 current model 的 top results 中, 取 'rank 高但人工标 irrelevant' 作为 hard negative"""
    results = current_model.search(query, top_k=top_k)
    hard_negs = []
    for r in results[1:]:  # skip top-1 if it's positive
        if r.doc_id != positive_doc_id and is_irrelevant(query, r.doc):
            hard_negs.append(r.doc)
    return hard_negs[:5]  # top-5 hardest
```

**典型收益**:
- Base bge-reranker NDCG@10: 0.72
- Fine-tune on 1K domain pairs + hard negatives: 0.81-0.85
- Cost: 1 GPU-day (~$50), one-time

### 2.5 决策表

```
QPS < 10, latency < 1s, generic:
  → Cohere rerank-3 (API)
QPS 10-100, latency < 500ms, generic:
  → bge-reranker-v2-m3 self-host on A10G
QPS > 100, latency < 200ms:
  → bge-reranker-v2-base + quantization (INT8 / TensorRT)
Multilingual:
  → bge-reranker-v2-m3 (天然 100+ lang)
Domain (legal / medical / code):
  → Fine-tune bge-base on domain data
High-stake top-3 (legal / medical / financial):
  → Cascade with LLM-as-judge on top-3 only
Latency irrelevant, quality max:
  → LLM-as-judge pointwise with Claude Opus 4.7
```

---

## ⚙️ Problem 3: Cascade Optimization — Cheap → Expensive

### 3.1 Cascade 数学

假设你想从 100 候选选 top-3, 用单一 expensive reranker:
- 100 × 200ms = 20s ❌

用 cascade:
- Cheap reranker on 100 → top-25: 100 × 30ms = 3s
- Expensive reranker on 25 → top-10: 25 × 200ms = 5s
- LLM-judge on top-10 → top-3: 1 × 3s = 3s
- Total: 11s, 但**精度比单一 LLM-judge 高**

**经验法则**: 每层 candidates 数减半到 1/4, 模型 cost 加 2-5x.

### 3.2 实际 cascade 代码

```python
class CascadeReranker:
    def __init__(self):
        self.cheap = SentenceTransformer.CrossEncoder('BAAI/bge-reranker-v2-base')
        self.expensive = CohereClient(api_key=...)
        self.llm = GeminiClient(model='gemini-3-pro')

    def rerank(
        self,
        query: str,
        candidates: List[Doc],
        final_k: int = 3,
        use_llm: bool = False,
    ) -> List[Doc]:

        # Stage 1: cheap reranker, 100 → 25
        if len(candidates) > 25:
            pairs = [(query, c.text) for c in candidates]
            cheap_scores = self.cheap.predict(pairs, batch_size=32)
            top_25 = [c for c, _ in sorted(zip(candidates, cheap_scores),
                                           key=lambda x: -x[1])[:25]]
        else:
            top_25 = candidates

        # Stage 2: expensive reranker, 25 → 10
        if final_k <= 10 and len(top_25) > 10:
            resp = self.expensive.rerank(
                model='rerank-multilingual-v3.0',
                query=query,
                documents=[c.text for c in top_25],
                top_n=10,
            )
            top_10 = [top_25[r.index] for r in resp.results]
        else:
            top_10 = top_25

        # Stage 3 (optional): LLM judge, 10 → final_k
        if use_llm and len(top_10) > final_k:
            ranked = self._llm_listwise_rank(query, top_10)
            return ranked[:final_k]

        return top_10[:final_k]

    def _llm_listwise_rank(self, query, docs):
        prompt = f"""Rank the documents by relevance to the query.

Query: {query}

Documents:
{format_docs_for_rank(docs)}

Return JSON: {{"ranking": [doc_index, ...]}} in order of relevance."""
        resp = self.llm.generate(prompt, response_format='json', max_tokens=200)
        data = json.loads(resp)
        return [docs[i] for i in data['ranking']]
```

### 3.3 Layer 选择策略

| 用户场景 | Layers |
|---|---|
| 普通客服 chatbot | first-stage + bge-base (200ms) |
| 内部知识库 | + bge-large (300ms) |
| E-commerce | first-stage + LightGBM LTR (multi-feature) |
| 法律 / 医疗 | + Cohere + LLM-judge top-3 |
| 极致 latency (<150ms) | first-stage + distilled small + caching |

### 3.4 Caching layer

```python
class RerankCache:
    """同 (query, candidate_doc_ids) 缓存 rerank 结果"""
    def __init__(self, ttl=3600):
        self.redis = redis.Redis()
        self.ttl = ttl

    def _key(self, query, candidate_ids):
        return f'rerank:{hashlib.sha1(query.encode()).hexdigest()}:{",".join(sorted(candidate_ids))}'

    def get(self, query, candidate_ids):
        return self.redis.get(self._key(query, candidate_ids))

    def set(self, query, candidate_ids, ranked):
        self.redis.set(self._key(query, candidate_ids), json.dumps(ranked), ex=self.ttl)
```

**何时有效**: 用户 query 重复率高 (热门 query), 或同一 query 重 issue.

### 3.5 Asymmetric cascade

```
对 cheap query (常见, 简单) → 短 cascade (just bge-base)
对 hard query (罕见, 长) → 长 cascade (+ Cohere + LLM-judge)
```

```python
def adaptive_cascade(query, candidates):
    if is_simple_query(query):       # rules: short, common keywords
        return cheap_rerank(query, candidates, top_k=10)
    elif is_complex_query(query):    # rules: long, multi-hop, technical
        return full_cascade(query, candidates, top_k=3, use_llm=True)
    else:
        return medium_cascade(query, candidates, top_k=5)
```

---

## ⚙️ Problem 4: Latency Engineering — GPU / Batch / Quant / Distill

### 4.1 GPU 选型 + FP16

```python
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class GpuReranker:
    def __init__(self, model_name='BAAI/bge-reranker-v2-m3'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            torch_dtype=torch.float16,  # FP16 = 2x faster on A10G/A100
        ).cuda().eval()

    @torch.no_grad()
    def predict_batch(self, pairs: List[Tuple[str, str]]) -> List[float]:
        # 单次 batch forward, 不是 for-loop
        inputs = self.tokenizer(
            [p[0] for p in pairs],
            [p[1] for p in pairs],
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors='pt',
        ).to('cuda')

        scores = self.model(**inputs).logits.squeeze(-1).float()
        return scores.cpu().tolist()
```

**FP32 vs FP16 vs INT8 (A10G batch 50)**:

| Precision | Latency | Accuracy loss |
|---|---|---|
| FP32 | 200ms | baseline |
| FP16 | 80ms | < 0.1% NDCG drop |
| INT8 (TensorRT) | 35ms | 0.5-1% NDCG drop |

### 4.2 Batching strategy

```python
class BatchingReranker:
    """微批: 等同一秒内多个 query 凑批, 单次 GPU forward"""
    def __init__(self, batch_size=64, wait_ms=50):
        self.batch_size = batch_size
        self.wait_ms = wait_ms
        self.pending = asyncio.Queue()
        self.task = asyncio.create_task(self._batch_loop())

    async def rerank(self, query, docs):
        future = asyncio.Future()
        await self.pending.put((query, docs, future))
        return await future

    async def _batch_loop(self):
        while True:
            batch = [await self.pending.get()]
            # Wait up to wait_ms for more
            try:
                while len(batch) < self.batch_size:
                    item = await asyncio.wait_for(self.pending.get(), timeout=self.wait_ms / 1000)
                    batch.append(item)
            except asyncio.TimeoutError:
                pass

            # Flatten all (q, d) pairs across queries
            all_pairs = []
            offsets = []
            for q, docs, _ in batch:
                offsets.append(len(all_pairs))
                all_pairs.extend([(q, d.text) for d in docs])

            scores = self.model.predict_batch(all_pairs)

            # 分发回 each future
            for i, (q, docs, fut) in enumerate(batch):
                start = offsets[i]
                end = offsets[i+1] if i+1 < len(offsets) else len(all_pairs)
                doc_scores = scores[start:end]
                ranked = [d for d, _ in sorted(zip(docs, doc_scores), key=lambda x: -x[1])]
                fut.set_result(ranked)
```

**收益**: GPU util 从 30% → 85%, throughput 3x.

### 4.3 TensorRT / ONNX

```python
# 1. Export ONNX
import torch.onnx
dummy = ...
torch.onnx.export(model, dummy, 'reranker.onnx', opset_version=14)

# 2. TensorRT compile
# $ trtexec --onnx=reranker.onnx --int8 --saveEngine=reranker.trt \
#           --workspace=2048 --maxBatch=64

# 3. Triton Inference Server config
"""
name: "reranker"
platform: "tensorrt_plan"
max_batch_size: 64
input [ ... ]
output [ ... ]
instance_group [
  { kind: KIND_GPU, count: 2 }
]
dynamic_batching {
  preferred_batch_size: [ 32, 64 ]
  max_queue_delay_microseconds: 50000
}
"""
```

**实测**: FP32 PyTorch 200ms → FP16 PyTorch 80ms → INT8 TensorRT 35ms.

### 4.4 Distillation — 自训小 reranker

```python
# Teacher: bge-reranker-large (slow but accurate)
# Student: 6-layer 小模型 (我们要的)

from sentence_transformers.cross_encoder import CrossEncoder
import torch.nn.functional as F

teacher = CrossEncoder('BAAI/bge-reranker-large')
student = CrossEncoder('BAAI/bge-reranker-base', num_labels=1)

for batch in train_loader:
    queries, docs, labels = batch
    pairs = list(zip(queries, docs))

    # Teacher scores
    with torch.no_grad():
        teacher_scores = teacher.predict(pairs, convert_to_tensor=True)

    # Student scores
    student_scores = student.predict(pairs, convert_to_tensor=True)

    # MSE distillation loss + ground truth loss
    loss = F.mse_loss(student_scores, teacher_scores) + \
           F.margin_ranking_loss(student_scores, labels, margin=0.2)

    loss.backward()
    optimizer.step()
```

**收益**:
- Student 30M params vs Teacher 568M
- 5x faster, 80% teacher quality
- Distillation 1-2 GPU-day, one-time

### 4.5 Quantization details

```python
# Post-training quantization (PTQ) - no retrain
from optimum.onnxruntime import ORTQuantizer
from optimum.onnxruntime.configuration import AutoQuantizationConfig

q_config = AutoQuantizationConfig.avx512_vnni(is_static=False, per_channel=False)
quantizer = ORTQuantizer.from_pretrained('./reranker-onnx')
quantizer.quantize(save_dir='./reranker-int8', quantization_config=q_config)
```

**Trade-off**: 0.5-1% NDCG drop in exchange for 2-3x speed.

### 4.6 Latency budget breakdown

```
Target p99: 500ms

Budget:
  Query understanding:    50ms (Gemini Flash + paraphrase)
  Hybrid first-stage:     50ms (BM25 + dense parallel)
  RRF fusion:             5ms
  Stage 2a bge-base:      80ms (FP16, batch 50)
  Stage 2b Cohere API:    200ms (P99 incl. network)
  LLM judge (if used):    SKIP (off, too slow)
  Post-filter / format:   20ms
  Margin:                 95ms
  Total:                  500ms ✓
```

每层有 latency 上限, 超了砍掉.

---

## ⚙️ Problem 5: Eval + Domain Finetuning + A/B

### 5.1 NDCG > Recall (for reranker)

Reranker 不改 set, 只改 ordering. 所以 recall@k 几乎不变 (除非 reranker 把 relevant 踢出 top-k, 这是 bug).

```python
def evaluate_reranker(pipeline, eval_set, ks=[1, 3, 5, 10]):
    """关键: NDCG > recall > MRR"""
    results = defaultdict(list)
    for q, expected in eval_set:
        # First-stage only
        first_stage = pipeline.first_stage(q, top_k=50)
        # First-stage + reranker
        reranked = pipeline.rerank(q, first_stage, top_k=max(ks))

        for k in ks:
            # NDCG (核心)
            ndcg_fs = compute_ndcg(first_stage[:k], expected['graded'], k=k)
            ndcg_re = compute_ndcg(reranked[:k], expected['graded'], k=k)
            results[f'ndcg@{k}_first_stage'].append(ndcg_fs)
            results[f'ndcg@{k}_reranked'].append(ndcg_re)
            results[f'ndcg@{k}_delta'].append(ndcg_re - ndcg_fs)

            # Recall (sanity, 应该不变)
            recall_fs = compute_recall(first_stage[:k], expected['relevant'])
            recall_re = compute_recall(reranked[:k], expected['relevant'])
            results[f'recall@{k}_first_stage'].append(recall_fs)
            results[f'recall@{k}_reranked'].append(recall_re)

        # MRR
        mrr_fs = compute_mrr(first_stage, expected['relevant'])
        mrr_re = compute_mrr(reranked, expected['relevant'])
        results['mrr_first_stage'].append(mrr_fs)
        results['mrr_reranked'].append(mrr_re)

    return {k: statistics.mean(v) for k, v in results.items()}
```

**典型结果**:
```
recall@10_first_stage:  0.92
recall@10_reranked:     0.92      # 不变
ndcg@10_first_stage:    0.68
ndcg@10_reranked:       0.83      # +15 pp ← 这才是关键
ndcg@10_delta:          +0.15
mrr_first_stage:        0.61
mrr_reranked:           0.78
```

### 5.2 Slice eval

```python
slices = {
    'short_query': lambda q: len(q.split()) <= 3,
    'long_query': lambda q: len(q.split()) > 10,
    'has_sku': lambda q: bool(re.search(r'\b[A-Z]{2,}\d+', q)),
    'has_acronym': lambda q: bool(re.search(r'\b[A-Z]{2,5}\b', q)),
    'is_question': lambda q: '?' in q,
    'doc_short': lambda q, d: avg_doc_length(d) < 100,
    'doc_long': lambda q, d: avg_doc_length(d) > 500,
    'multilingual': lambda q: detect_language(q) != 'en',
}
```

**典型发现**:
- 总 NDCG@10 = 0.83
- multilingual slice: 0.76 (reranker bge-v2-m3 应优于英文专用)
- has_sku: 0.72 → reranker 对 SKU exact match 不够好, 加 BM25 stronger weight 或 SKU-specific boost
- doc_long: 0.79 → reranker 在长 doc 上略差 (max 512 token 截断)

### 5.3 A/B test in production

```python
# Feature flag
def search(query, user_id):
    bucket = hash(f'rerank_v4:{user_id}') % 100
    if bucket < 50:
        pipeline = pipeline_v3      # control (Cohere rerank-3)
        variant = 'control'
    else:
        pipeline = pipeline_v4      # treatment (bge-reranker-v2-m3 self-host)
        variant = 'treatment'

    results = pipeline.retrieve(query)
    log_search_event({
        'user_id': user_id, 'query': query,
        'variant': variant, 'top_5_doc_ids': [r.id for r in results[:5]],
        'first_stage_latency_ms': pipeline.first_stage_latency,
        'rerank_latency_ms': pipeline.rerank_latency,
    })
    return results

# Click tracking
def on_click(user_id, query_id, clicked_doc_id, position):
    log_click_event({
        'user_id': user_id, 'query_id': query_id,
        'doc_id': clicked_doc_id, 'position': position,
        'variant': lookup_variant(query_id),
    })
```

**分析**:
```python
# 1 周后
control = events.filter(variant='control')
treatment = events.filter(variant='treatment')

metrics = ['ctr_top_3', 'ctr_top_1', 'time_to_first_click', 'thumbs_up_rate']
for m in metrics:
    c_val = compute(control, m)
    t_val = compute(treatment, m)
    p_value = t_test(control, treatment, m)
    print(f'{m}: control={c_val:.3f} treatment={t_val:.3f} p={p_value:.4f}')

# 决策: treatment 提升 thumbs_up +12% (p<0.01), latency +30ms (p=0.0001)
# → 上线 treatment (latency 增加可接受)
```

### 5.4 Domain finetune workflow

**Step 1: 收集数据**:

```python
# From production click data
training_pairs = []
for event in click_events:
    positive = event.clicked_doc
    # Hard negatives: docs ranked higher than positive but not clicked
    candidates = event.search_results
    pos_rank = candidates.index(positive)
    hard_negs = candidates[:pos_rank]  # ranked higher but not clicked
    for neg in hard_negs[:3]:
        training_pairs.append({
            'query': event.query,
            'positive': positive.text,
            'negative': neg.text,
        })
```

**Step 2: LLM 合成 (扩充)**:

```python
prompt = """Given this document, write a question that would be answered by it,
plus a question that would NOT be answered by it but is on a similar topic.

Document: {doc.text}

JSON: {"positive_query": "...", "negative_query": "..."}"""

for doc in random_sample(corpus, 5000):
    resp = gemini_flash.generate(prompt.format(doc=doc), response_format='json')
    data = json.loads(resp)
    training_pairs.append({
        'query': data['positive_query'],
        'positive': doc.text,
        'negative': random.choice(corpus).text,  # easy negative
    })
    training_pairs.append({
        'query': data['negative_query'],
        'positive': doc.text,  # 不该匹配, swap
        'negative': doc.text,
    })
```

**Step 3: Fine-tune**:

```python
from sentence_transformers.cross_encoder import CrossEncoder
from sentence_transformers import InputExample
from torch.utils.data import DataLoader

# Convert to InputExample
examples = []
for pair in training_pairs:
    examples.append(InputExample(texts=[pair['query'], pair['positive']], label=1.0))
    examples.append(InputExample(texts=[pair['query'], pair['negative']], label=0.0))

model = CrossEncoder('BAAI/bge-reranker-v2-base', num_labels=1)
train_loader = DataLoader(examples, batch_size=32, shuffle=True)

model.fit(
    train_dataloader=train_loader,
    epochs=3,
    warmup_steps=int(0.1 * len(train_loader) * 3),
    output_path='./bge-reranker-bnpl',
    evaluator=CECorrelationEvaluator(eval_pairs),
    evaluation_steps=500,
)
```

**Step 4: Eval + 比较**:

```python
base_metrics = evaluate(CrossEncoder('BAAI/bge-reranker-v2-base'), eval_set)
finetune_metrics = evaluate(CrossEncoder('./bge-reranker-bnpl'), eval_set)
print(f'NDCG@10 base: {base_metrics["ndcg@10"]}')
print(f'NDCG@10 fine-tuned: {finetune_metrics["ndcg@10"]}')
# Typical: 0.78 → 0.84 (+6pp)
```

### 5.5 Continual learning

```python
# 持续 retrain on new click data
def weekly_retrain():
    new_pairs = collect_pairs(time_range='last_7_days')
    if len(new_pairs) < 500:
        return  # not enough
    model = CrossEncoder('./bge-reranker-bnpl-current')
    model.fit(new_pairs, epochs=1, output_path='./bge-reranker-bnpl-candidate')

    # A/B candidate vs current
    candidate_ndcg = evaluate(model, eval_set)['ndcg@10']
    current_ndcg = evaluate(load('./bge-reranker-bnpl-current'), eval_set)['ndcg@10']
    if candidate_ndcg > current_ndcg + 0.005:  # +0.5pp threshold
        promote('./bge-reranker-bnpl-candidate', './bge-reranker-bnpl-current')
        alert(f'Promoted new reranker: NDCG {current_ndcg:.3f} → {candidate_ndcg:.3f}')
```

### 5.6 Production observability

| Metric | Alert |
|---|---|
| p99 rerank latency | > budget × 1.2 sustained |
| Rerank GPU util | > 90% → scale up |
| Rerank queue depth | > 100 → backpressure |
| NDCG weekly regression | drop > 1pp vs last week |
| Click position distribution | top-3 click drop > 5pp |
| Per-slice NDCG | any slice drop > 3pp |

---

# Part 3 · 把 5 个问题串起来看

5 个问题 = 同一工程问题 5 层:

1. **Bi vs cross encoder 数学** 决定「为什么需要 reranker」
2. **Reranker options** 决定「用哪个模型」
3. **Cascade** 决定「多层组合 cost / latency / quality 平衡」
4. **Latency engineering** 决定「能不能 production 上线」
5. **Eval + domain finetune** 决定「持续提升」

把这 5 层都讲, + BNPL chatbot 0.71 → 0.83 NDCG / +12% thumbs, 就是 staff-level RAG / IR 工程师水准.

---

## 必问 clarifying questions

**1. First-stage 质量**

> "Top-50 recall — what% of expected relevant in top-50? If already 95%, reranker just reorders. If 60%, reranker can't fix what's missing."

**2. Latency budget**

> "Per-query budget — 100ms / 500ms / 1s / 10s? Determines cascade depth + model class."

**3. Quality target**

> "Top-1 accuracy (single best) or top-3 / top-10 (set of good)? NDCG@k for which k?"

**4. Volume / QPS / cost**

> "QPS expected. Per-query reranker cost compounds: 100 QPS × $1/1K = $360/hour. Self-host or API?"

**5. Domain**

> "Generic web / e-commerce / legal / code / medical? Domain-specific reranker / fine-tuning data available?"

---

## 5 步框架 (sample 45-60 min answer)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify first-stage recall + latency / cost / quality target + domain |
| 5-15 min | Why reranker (bi vs cross encoder math + attention 视角) |
| 15-25 min | Reranker options trade-off (open-source / API / LLM-judge / finetune) |
| 25-35 min | Cascade design + latency engineering (GPU batch / FP16 / TensorRT) |
| 35-45 min | Eval methodology (NDCG / slice / A/B) + domain finetune workflow |

---

## 我会这样答 (sample)

> "Clarify — *[假设: first-stage recall@50 = 92% (hybrid BM25 + dense + RRF), latency 500ms budget, top-3 accuracy core target, 100 QPS, multilingual technical doc domain]*.
>
> **Why reranker** — bi-encoder limit: query 和 doc 独立 embed, 没 cross-attention, top-50 set OK but ordering 烂. Cross-encoder joint forward, attention 跨 query-doc, ordering 大幅好.
>
> **Reranker choice**: bge-reranker-v2-m3 (multilingual, 568M params, A10G batch 50 FP16 ~150ms) — open-source default. Cohere rerank-3 as fallback if API latency stable.
>
> **Cascade**:
> - Stage 1 hybrid first-stage → top-100 (parallel BM25 + dense, ~50ms)
> - Stage 2a bge-base → top-25 (batch 100 FP16, ~80ms)
> - Stage 2b Cohere rerank-3 → top-10 (API, ~200ms)
> - Total ~330ms, fits 500ms budget
>
> **Latency engineering**: FP16, batch 50, TensorRT INT8 if extra speed needed, micro-batching across queries (wait 50ms, batch 32), Triton Inference Server. Caching (Redis 1h TTL) for hot queries.
>
> **Domain finetune**: collect 1K (query, positive, hard_negative) from production clicks + 5K LLM-synthesized. Fine-tune bge-base 3 epochs, eval NDCG@10. Continual retrain weekly if delta > 0.5pp.
>
> **Eval**: 200 human-labeled (query, graded_docs), NDCG@1/3/5/10 + MRR + recall stability. Slice by query length / has_acronym / language / doc_length. A/B in prod with CTR / time-to-answer / thumbs.
>
> **Expected**: NDCG@10 from 0.68 (first-stage only) → 0.83 (+cascade) → 0.85 (+domain finetune). MRR 0.61 → 0.78.
>
> **What I would NOT do**: bi-encoder for rerank; rerank top-1000; one reranker all domains; LLM-judge mass deploy; no slice eval; no caching."

---

## 简历专属 reframe

| 题 | 你的经验 |
|---|---|
| Cross-encoder reranker | **BNPL chatbot RAG** — added bge-reranker-v2-m3, NDCG@5 0.71→0.83 |
| Cascade | **Voice agent** — multi-stage ASR (fast model → expensive verifier) |
| LLM-as-judge | **ConvFinQA** — ablation evaluator was LLM-judge style |
| Latency engineering | **Voice agent** p99 < 800ms streaming — 你天然必须做 |
| GPU batching | **Voice agent** — vLLM / SGLang inference 你做过 |
| Domain finetune | **Voice agent** — SFT / DPO / RL post-training 你做过 |
| Eval set | **ConvFinQA** — annotated eval set methodology |

**主动 quote**:

> "BNPL chatbot added bge-reranker-v2-m3 in the top-50 → top-5 stage. NDCG@5 jumped from 0.71 to 0.83. Latency cost +180ms (A10G GPU batched FP16), within our 1.5s budget. The single biggest win was on **acronym queries** — bi-encoder gave 'phone' for 'iPhone Pro' query because Pro Max didn't generalize in embedding space, reranker correctly preferred the iPhone-specific doc via cross-attention. We A/B tested 1 week, user thumbs-up rate +12%, p<0.01.
>
> Later we **fine-tuned bge-reranker-base on 2K production click pairs + 5K LLM-synthesized**, with hard-negative mining (ranked higher but not clicked). 6 GPU-hours training, additional +4pp NDCG. The pattern I'd reuse: **always start with open-source baseline (bge), measure NDCG gap to Cohere as ceiling estimate, then decide if fine-tuning closes it cheaper**. In our case fine-tuned bge matched Cohere quality at 1/10 inference cost (self-host vs API)."

---

## 5 follow-ups

**Q1**: "Reranker latency too high (1s). Need < 200ms total. Options?"

**A**: Multiple:
- **Cheaper reranker**: bge-base or distilled small student
- **Fewer candidates**: top-20 instead of top-50
- **GPU + FP16 + INT8 + TensorRT**: 3-5x speedup
- **Distillation**: large → small via knowledge distill, 5x speed at 80% quality
- **No reranker, better first stage**: invest in HyDE / multi-query / better embeddings
- **Caching**: hot (query, candidates) cached 1h
- **Async fan-out**: stream first-stage to LLM while rerank in background

**Q2**: "LLM-as-judge sounds best — why not always?"

**A**:
- **Cost**: Gemini 3 Pro pair-rank 50 candidates ≈ $0.10-0.20/q (50 pairs × ~2K tokens × $2/1M); Opus 4.7 ~$0.50/q. At 1M queries/day = $100K-500K/day
- **Latency**: 5-15s per query, kill UX
- **Consistency**: LLM judgment varies between runs, calibration drift
- **Use case**: top-3 final pass only, high-stakes ✓; or eval offline
- **Mass deployment**: too expensive

**Q3**: "Reranker has its own biases (favors longer docs). How detect?"

**A**:
- **Slice eval by doc length**: NDCG by length quartile (short / med / long)
- **Calibration test**: synthesize known-relevant short docs, check still surfaces
- **Diversity in eval set**: span all doc length distributions
- **Compare multiple rerankers**: best per-slice may differ
- **Length normalization**: divide score by f(doc_length) to debias

**Q4**: "Domain-specific (medical, legal). Generic reranker not enough?"

**A**:
- **Finetune** on domain pairs: 1K-10K labeled (q, d) on top of bge-base
- **Hard-negative mining**: include top-ranked-but-wrong as negatives
- **Synthetic data**: LLM generate query-doc pairs from corpus
- **Cost**: 1-2 GPU-days, $50-100, one-time
- **Gain**: typical 3-8 pp NDCG in narrow domain
- **Alternative**: use specialized embedding (BiomedBERT) at first stage too

**Q5**: "Reranker performance flat for 6 months. How improve?"

**A**:
- **Eval drift**: ensure eval set reflects current query distribution (refresh quarterly)
- **Data**: add more training pairs from recent production user feedback
- **Hard negatives**: 'almost-right' docs that reranker mis-orders (analyze failures)
- **Newer model**: bge v2 → v3, mxbai-rerank-large, Cohere rerank-3 new version
- **Domain coverage gap**: which slice still bad? targeted improvement
- **Multi-task**: train on multiple objectives (relevance + freshness + diversity)

---

## ❌ 易错点 (top 10)

1. **Bi-encoder used for reranking** — no cross-attention, 无意义
2. **Rerank top-1000** — latency blow, 应 first-stage narrow
3. **No first-stage to narrow** — cross-encoder 不能 scale 1M docs
4. **No eval, 'feels better'** — silent regression
5. **Single reranker for all domain** — code / legal / medical 都用 generic
6. **LLM-as-judge for everything** — cost blow
7. **No cascade** — pay expensive on every candidate
8. **CPU 单条 forward** — GPU batch FP16 是 3-5x 提升
9. **No quantization** — leave 50% perf 桌上
10. **Forget recall stays same** — focus NDCG / MRR

---

## ✅ 加分项 (top 10)

1. **Bi vs cross encoder 数学** explanation with attention 视角
2. **Cascade design** (cheap → expensive → optional LLM-judge)
3. **Per-domain finetuning** workflow (data + hard-neg + synth)
4. **GPU + batch + FP16 + TensorRT** for latency
5. **NDCG / MRR > recall** for reranker eval (recall stays same)
6. **A/B framework** with multi-metric (CTR / time / thumbs)
7. **LLM-as-judge as final pass** for high-stakes only
8. **Hard-negative mining** from production
9. **Continual learning** weekly retrain
10. **Quote BNPL bge-reranker-v2-m3 0.71→0.83 NDCG + 12% thumbs**

---

## 一句话总结

> **Reranker = 「cross-encoder 看 (query, doc) joint, 必须 cascade 限 candidate 数, GPU batch + FP16 上线, NDCG 是核心指标, domain finetune + hard-neg 持续提升」**.
>
> 不是「加个 reranker 就完事」, 是 **cascade + latency engineering + eval + finetune** 的整套工程系统.

---

## Cheat Sheet

```
Bi-encoder vs Cross-encoder:
  Bi: independent embed, cosine score, fast (ms), scale to 1B
  Cross: joint forward [CLS] q [SEP] d, cross-attention, slow (50-200ms/pair), top-50 max
  Use bi for first stage, cross for rerank

Cross-encoder attention 视角:
  combined sequence [q; d], attention matrix (n+m)²
  q-d block: query token 和 doc token 互相对齐
  Bi-encoder 没这 block, 只能各自 pool

Reranker options (2026):
  bge-reranker-v2-m3: free, multilingual, 150ms A10G
  bge-reranker-large: free, bigger, 300ms
  Cohere rerank-3: $1/1K, ~200ms API
  mxbai-rerank-large-v1: open Cohere-class
  LLM-as-judge: Gemini 3 Pro / Opus 4.7, top-3 final
  Domain-finetune: 1-2 GPU-day, +3-8pp NDCG

Cascade pattern:
  bi-encoder → top-100 (50ms)
  bge-base → top-25 (80ms)
  bge-large or Cohere → top-10 (200ms)
  LLM-judge → top-3 (optional, 3-5s, high-stake only)

Latency optimization:
  FP16 → 2x
  INT8 + TensorRT → 3x
  Batching 32-64 → throughput 3x
  Distillation large→small → 5x speed
  Micro-batching across queries (wait 50ms)
  Caching (query, candidates) Redis 1h TTL

Eval metrics for reranker:
  NDCG@k (position-aware, 核心)
  MRR (first relevant rank)
  Recall stays same (set unchanged)
  Slice: short / long / acronym / SKU / multilingual

A/B test in prod:
  CTR top-3, top-1
  Time-to-first-click
  Thumbs up rate
  Latency p99
  Per-variant slice metrics

Domain finetune:
  Data: production clicks + LLM synthetic
  Hard-negative mining: top-ranked-but-not-clicked
  Loss: MSE distillation + margin ranking
  1-2 GPU-day, ~$50-100, +3-8pp NDCG
  Weekly continual retrain

Production observability:
  p99 rerank latency
  GPU util (>90% scale up)
  NDCG weekly regression
  Slice metrics
  Click position distribution

Tool zoo (2026):
  Models: bge-reranker-v2-m3, Cohere rerank-3, mxbai-rerank, JaColBERT
  Inference: Triton, vLLM, TGI, TensorRT
  Tracing: Phoenix (Arize), LangSmith
  Training: sentence-transformers, Hugging Face Trainer
  Eval: BEIR, MTEB, custom domain eval set

红线:
  - Bi for reranking
  - Top-1000 cross-encode
  - No first stage narrow
  - No eval
  - LLM-judge mass
  - No cascade
  - CPU forward
  - No quantization
  - Single reranker all domain
```
