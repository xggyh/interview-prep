## 题目

> "**Gemini 3 Pro now has 2M context, Claude Opus 4.7 has 200K**. Some say 'long-context kills RAG' — just stuff everything in. Do you agree? When to use which?"

或追问形态:

> "Customer has 100K-page legal docs. Build a chatbot. Long context, RAG, or hybrid? Defend choice."

**出处**: Google FDE T2 / Anthropic Forward Deployed / Vertex AI Vector Search Solutions Engineering 等都问. 2024-2025 业界辩论, 2026 hybrid 是共识.

**Round**: RAG Architecture / Trade-off (45 min)

---

## 这道题在考什么

考你 **modern (2026) understanding** of LLM landscape + production trade-offs:

1. **Long-context truly available** but with caveats (cost, latency, lost-in-middle)
2. **RAG NOT dead** — different sweet spot, complementary
3. **Hybrid 是主流答案**
4. **Cost math** — long-context $$$ per call, RAG sublinear
5. **Update frequency** — RAG natural, long-context needs reload
6. **Citation / provenance** — RAG natural, long-context 靠 prompt
7. **Vendor lock-in** — 1M+ context 主要 Gemini/Claude, 不 portable

不考「RAG 是什么」, 考「100K-page corpus 给你, 你为什么 hybrid, cost / latency / citation 三个维度怎么算」.

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**Context window**: LLM 单次输入能容纳的 token 数. 2026 主流: Gemini 3 Pro **2M**, Gemini 3 Flash 1M, Claude Opus 4.7 200K, Claude Sonnet 4.6 200K, GPT-5.5 256K. 注意: 名义 ≠ effective, 中间部分 attention 弱.

**Effective context**: 模型在 long context 上仍有可靠 recall 的区域. Lost-in-middle 研究表明, 即使 2M 模型, 中间 1.4M 区域的 recall 可能比首尾低 30-40%.

**RAG (Retrieval-Augmented Generation)**: 用 retrieval (BM25 / dense / hybrid) 从大 corpus 取相关 chunk, 拼到 LLM context. 经典模式: 1B token corpus 索引, query 时取 top-10 chunk (~5K token) 进 prompt.

**Long-context mode**: 直接把整 corpus / doc 塞 LLM context, 不做 retrieval. 适合**小 corpus, 全局推理需求高**的场景.

---

## 2. 这个问题的核心是什么

设想两种极端选择的灾难:

### Pure long-context for 大 corpus (灾难 A)

```
100K-page legal corpus = ~500M tokens
Gemini 3 Pro 2M context = 装不下 (500M > 2M, 250x)
即使能装: 500M × $4/1M (Pro >200K tier) = $2000 per call ❌
Latency: 500M context first-token ~10 分钟 ❌

结论: 不可能 pure long-context
```

### Pure RAG for multi-hop reasoning (灾难 B)

```
User: "What's the indemnity cap in the vendor agreement, and how does it interact
       with the limitation of liability in section 12?"

RAG retrieves top-5 chunks:
  - indemnity clause (section 8) ✓
  - limitation of liability heading (section 12 title) ✓
  - ... 但 section 12 body 的 specific limit 没在 top-5

LLM 看到 indemnity cap = $5M, 看到 LoL 标题但不知道具体值
LLM 编: "LoL is probably standard $2M based on industry practice"
答案错 ❌

结论: pure RAG 在 multi-hop / cross-section reasoning 上脆弱
```

### Hybrid 的解法

```
Stage 1 (RAG narrow): retrieve top-10 docs (each ≤ 50K token) → total ~500K
Stage 2 (long-context handle): 500K 进 Claude Opus 4.7 200K? 不行, 但 Gemini 3 Pro 2M 可
  - Pro 在 500K 范围内 attention 还 OK (远比 2M middle 好)
  - 多 hop 推理在这 500K 内 LLM 自由完成
  - Cost: 500K × $2/1M = $1, 而不是 $2000
  - Latency: 500K context first-token ~15s
  - 远远好于 pure long-context ($2000, 600s)
  - 远远好于 pure RAG (miss multi-hop)
```

---

## 3. 典型决策树

```
                ┌─────────────────────────────────────┐
                │  Corpus total tokens?               │
                └────┬────────────────┬───────────────┘
                     │                │
              < 200K │                │ ≥ 200K
                     ▼                ▼
            ┌────────────────┐  ┌──────────────────┐
            │ Pure long-ctx  │  │ Corpus < 2M?     │
            │ Claude / Opus  │  │ (within 1 LLM ctx)│
            │ 200K window 装 │  └─┬────────────────┘
            │ 全, 不 RAG     │   │
            └────────────────┘   ├─ YES (200K-2M)
                                 │  ├─ Cost-sensitive?
                                 │  │  ├─ YES → RAG narrow → long-ctx within
                                 │  │  └─ NO  → Pure long-ctx (Pro 2M)
                                 │  └─ Multi-hop heavy?
                                 │     └─ YES → Pure long-ctx (Pro 2M) 直接
                                 │
                                 └─ NO (≥ 2M)
                                    ├─ Update freq?
                                    │  ├─ Real-time → Pure RAG (long-ctx 没法 reload)
                                    │  └─ Slow → Hybrid RAG → long-ctx
                                    ├─ Multi-hop heavy?
                                    │  └─ YES → Hybrid (RAG narrow + long-ctx within)
                                    └─ Citation strict?
                                       └─ YES → Hybrid (RAG citation natural)
```

```
                ┌──────────────────────────────────────┐
                │  QPS / Cost sensitivity              │
                └──────┬───────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
      Low (<1/min)   Med (1-10/s)   High (>10/s)
        │              │              │
        ▼              ▼              ▼
   Long-ctx OK   Hybrid             Pure RAG must
   (cost ack)    (sublinear $)      (linear $ kills)
```

---

## 4. Long-context vs RAG 对比表

| 维度 | Long-context | RAG | Hybrid (RAG narrow + long-ctx) |
|---|---|---|---|
| **Corpus 上限** | LLM context (2M) | 任意 (索引) | RAG narrow 后 ≤ LLM ctx |
| **Per-query cost** | 高 ($1-10) | 极低 ($0.005-0.05) | 中 ($0.20-1) |
| **Per-query latency** | 长 (10-60s) | 短 (100ms-2s) | 中 (5-20s) |
| **Multi-hop** | 强 (全 ctx 自由) | 弱 (chunk 分散) | 强 (在 narrow 内自由) |
| **Update frequency** | 慢 (reload 全 ctx) | 实时 (delta index) | 中 (RAG 实时, 全 ctx cache) |
| **Citation** | 靠 prompt (易错) | 自然 (chunk id) | 自然 (chunk id) |
| **Vendor lock-in** | 高 (Gemini/Claude only) | 低 (model-agnostic) | 中 |
| **Lost-in-middle** | 严重 (2M 中间 30% 弱) | 不存在 (只看相关) | 轻 (narrow 内仍存在) |
| **Engineering 复杂度** | 低 (装就行) | 高 (索引 / chunk / eval) | 高 (RAG + LLM 编排) |
| **何时最优** | 小 corpus, 多 hop, low QPS | 大 corpus, 实时, 高 QPS | 中等 corpus, 多 hop, 中 QPS |

---

## 5. 具体业务场景 (5 个高频)

### 场景 A: 法律合同问答 (500-page 合同, 100 question)

单 doc ~150K tokens, fit 200K-context model (Claude Opus 4.7) 或 Gemini 3 Pro.

**Decision**:
- 100 questions × 150K = 15M tokens 重复 load → $$$
- **优**: 一次 load → prefix cache (Anthropic 5min, Gemini 1h), 后续 query 走 cache 9 折
- 或: index 一次, per-question RAG 取相关 clause + 上下文 (2-3 个 chunk × 800 token = 2.5K)
- **Hybrid 最优**: cache 全 doc 5 min, 同 user session 内 cheap; cross-session 用 RAG

### 场景 B: Coding agent — 大 repo (50K file, 1M LOC)

总 token 远超 long-context (~50M).

**Decision**:
- **RAG 必须**: 50M >> 2M
- AST chunking, symbol graph
- Iterative: agent first "where is auth?" → search → narrow → "read these 5 files"
- 单文件 < 5K token: 内部用 long-context (一次 read whole file)
- Cross-file 关系靠 call graph 不是 vector search

### 场景 C: 医疗病史 (patient 30 年 records)

总 1M+ tokens, long-context 装不下 (Pro 2M 勉强, 但 cost 高).

**Decision**:
- **RAG + temporal index**: time-range filter ('last 5 years', 'around 2019')
- **Critical record always-in-context**: 过敏 / 慢性病 / 当前药 永远在 system prompt
- **Episode-level summary**: 每次就诊 1 段 summary, retrieve 后展开 detail
- **PHI 合规**: 检索结果不能 leak 给 unauth role (perms filter)

### 场景 D: Daily news / dynamic data

数据每秒变, long-context 装载就过时.

**Decision**:
- **RAG 唯一选项** (long-context 不能实时)
- Hot index (last 24h, refresh 5 min) + warm (1 month, daily) + cold (archive)
- Recency-weighted: time decay
- Personalize: user 关注 topic / region

### 场景 E: ConvFinQA / 财报分析 (你做过)

财报 avg 200K token, multi-hop questions.

**Decision**:
- 单 doc 接近 long-context 上限
- **Hybrid 最优**: RAG retrieves relevant tables + paragraphs, long-context (Claude 100K) handles multi-hop within
- Latency 8s, cost $0.30/q
- 这就是你简历里 ConvFinQA 架构

---

## 6. 工程上要做什么 (实现 checklist)

**Phase 1: 评估 corpus**:

1. **总 token 数**: 这是决策最关键变量
2. **Update frequency**: static / hourly / daily / real-time
3. **Query pattern**: single-doc vs cross-doc, fact lookup vs multi-hop
4. **Volume**: QPS, cost ceiling, latency budget
5. **Citation 要求**: 严 (legal/medical/finance) vs 松 (general chat)

**Phase 2: 选择 architecture**:

6. **Apply decision tree** (上面)
7. **Estimate cost**: 算 per-query cost × QPS × day
8. **Estimate latency**: model first-token + processing
9. **Prefix caching opportunities**: 同 corpus 多 query, 用 ephemeral cache (Anthropic / Gemini 都支持)

**Phase 3: 实现 hybrid (最常见)**:

10. **RAG layer**: BM25 + dense + RRF + reranker (见 hybrid-search 题)
11. **Doc-level retrieval option**: 取整 doc (or 大段) 给 long-ctx, 不是只取小 chunk
12. **Long-ctx layer**: Gemini 3 Pro (2M, $2-4/1M) 或 Claude Opus 4.7 (200K, $5/1M)
13. **Citation enforcement**: post-LLM validate retrieved doc ids referenced
14. **Prefix cache**: 同 session 同 corpus 重 5 min cache

**Phase 4: Eval**:

15. **Eval set 200+**: cross multi-hop questions, single-fact lookup, summary-style
16. **Metrics**: accuracy, citation correctness, latency, cost
17. **Compare modes**: pure RAG / pure long-ctx / hybrid on same eval

**Phase 5: Production**:

18. **Routing**: 不同 query 走不同 mode (cheap query → RAG only; complex → hybrid)
19. **Cost monitoring**: per-query cost, per-day spend, alert thresholds
20. **Cache hit rate** observe: prefix cache 节省多少
21. **Citation validation** in prod

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **"Long-context killed RAG" believing** | 大 corpus 装不下, cost 爆 |
| 2 | **Pure long-context for huge corpus** | $1000/q, 不可持续 |
| 3 | **Pure RAG for multi-hop** | Retrieval miss cross-section, 答错 |
| 4 | **Ignore cost math** | 100K queries/day × $4 = $400K/day, 老板炸 |
| 5 | **No citation strategy in long-ctx** | LLM hallucinate "page X says ..." |
| 6 | **Vendor lock-in** | 1M+ context 主要 Gemini/Claude, 切换模型难 |
| 7 | **Forget update frequency** | 新 doc 进 corpus 但 long-ctx prefix cache 没 invalidate |
| 8 | **Lost-in-middle 不防** | Critical info 埋 2M context 中间, LLM 漏 |
| 9 | **No prefix caching** | 同 corpus 反复 load, 9 折机会浪费 |
| 10 | **Hybrid 不做 query routing** | 所有 query 都走 hybrid, simple query 浪费 |

---

## 一句话总结 (Part 1)

> **Long-context vs RAG: 不是对立, 是 sweet spot 不同. 100K-page 法律 corpus → hybrid (RAG narrow + long-ctx within), 1B token enterprise data lake → RAG 主, 500-page 单合同 → long-ctx 主 + prefix cache.**
>
> 2026 的答案是 **decision tree by corpus size + cost + multi-hop + citation + update freq**, 不是非黑即白.

---

# Part 2 · 5 个深度工程问题

## ⚙️ Problem 1: Decision Tree by Corpus + Cost + Multi-hop

### 1.1 完整决策树

```python
def architecture_decision(
    corpus_tokens: int,
    query_pattern: str,        # 'fact_lookup', 'multi_hop', 'summary', 'cross_doc'
    update_frequency: str,     # 'real_time', 'hourly', 'daily', 'static'
    qps: float,
    cost_budget_per_query: float,
    latency_budget_sec: float,
    citation_required: bool,
) -> str:

    # === Corpus size primary axis ===
    if corpus_tokens < 100_000:
        # Small enough for any model context
        if update_frequency == 'real_time' or citation_required:
            return 'pure_rag'  # citation natural in RAG
        else:
            return 'pure_long_context'

    elif corpus_tokens < 2_000_000:
        # Fits Gemini 3 Pro 2M
        if cost_budget_per_query < 0.10:
            return 'pure_rag'  # long-ctx too expensive
        if query_pattern in ('multi_hop', 'cross_doc'):
            if qps > 10:
                return 'hybrid'  # cost-aware narrow + long-ctx
            else:
                return 'pure_long_context'  # full Pro context
        else:
            return 'pure_rag'  # single fact-lookup, RAG is cheaper

    else:
        # > 2M, doesn't fit any single context
        if update_frequency == 'real_time':
            return 'pure_rag'  # long-ctx can't reload constantly
        elif query_pattern in ('multi_hop', 'cross_doc'):
            return 'hybrid'  # RAG narrow → long-ctx within
        else:
            return 'pure_rag'
```

### 1.2 决策 table

| Corpus | Pattern | Update | QPS | 推荐 |
|---|---|---|---|---|
| < 100K | any | static | any | Pure long-ctx |
| < 100K | any | real-time | any | Pure RAG |
| 100K-2M | fact_lookup | any | any | Pure RAG (cheap) |
| 100K-2M | multi_hop | static | low | Pure long-ctx (Pro 2M) |
| 100K-2M | multi_hop | any | high | Hybrid |
| 100K-2M | multi_hop | real-time | any | Hybrid |
| > 2M | any | real-time | any | Pure RAG |
| > 2M | multi_hop | static | any | Hybrid |
| > 2M | fact_lookup | any | any | Pure RAG |

### 1.3 多场景 decision 详细 walkthrough

**场景 1**: 单个 500-page 合同, 律师每天问 50 个 question
- corpus = 150K tokens (装 Claude Opus 200K / Gemini 3 Pro 2M)
- multi_hop heavy (clause cross-reference)
- static (合同签定不变)
- low QPS
- citation required (法律)
- **Decision**: Pure long-context with prefix caching (5 min ephemeral), citation post-validated.
- Cost: first call $0.75 (150K × $5/1M Opus), subsequent in 5min ~$0.075. Daily 50 × $0.10 avg = $5.

**场景 2**: 50K 内部文档 (Confluence + Slack + GDrive), 全公司搜索 chatbot
- corpus = 200M tokens
- mixed pattern
- daily update
- high QPS (1000/day)
- citation needed (内部审计)
- **Decision**: Pure RAG (200M >> 2M, real-time-ish update).
- Cost: ~$0.005/query × 1000 = $5/day. RAG 工程一次性 $50K, ongoing $5/day.

**场景 3**: ConvFinQA — 100K 财报 corpus, multi-hop, low QPS
- corpus = 50M (100K 财报 × avg 500 token/doc)
- multi_hop heavy
- static (年报)
- low QPS (research)
- citation required
- **Decision**: Hybrid. RAG retrieves top-3 reports (each ~200K), feeds Claude Opus 4.7 200K for multi-hop.
- Cost: $0.30/q (你简历数据)

**场景 4**: News briefing agent, last 24h news
- corpus = 5M tokens (24h news流)
- single article fact-lookup
- real-time update
- medium QPS
- **Decision**: Pure RAG with hot index (5-min refresh).
- Cost: $0.01-0.05/q

**场景 5**: Code agent on monorepo
- corpus = 50M (1M LOC)
- multi_file reasoning
- daily update (git push)
- low-medium QPS
- **Decision**: Hybrid. AST-based RAG narrows to 5-10 files, agent iteratively reads more via tool.
- Cost: $0.50-2/task

---

## ⚙️ Problem 2: Cost Math — Per-query 1M vs RAG Retrieved

### 2.1 2026 pricing 

| Model | Input ≤200K | Input >200K | Output | Cache hit |
|---|---|---|---|---|
| **Gemini 3 Pro** | $2/1M | $4/1M | $12/1M | ~10% of input |
| **Gemini 3 Flash** | $0.50/1M | $1/1M | $3/1M | ~10% |
| **Claude Opus 4.7** | $5/1M | n/a (max 200K) | $25/1M | ~10% |
| **Claude Sonnet 4.6** | $3/1M | n/a (max 200K) | $15/1M | ~10% |
| **Claude Haiku 4.5** | $1/1M | n/a (max 200K) | $5/1M | ~10% |
| **GPT-5.5** | $5/1M | n/a (max 256K) | $30/1M | ~10% |

### 2.2 Per-query cost (typical scenario)

**Pure long-context 1M tokens (Gemini 3 Pro)**:
- Input: 1M × $4/1M (>200K tier) = $4.00
- Output: 500 tok × $12/1M = $0.006
- **Total: ~$4 per query**

**Pure RAG 5K tokens to LLM (Gemini 3 Flash)**:
- Input: 5K × $0.50/1M = $0.0025
- Output: 500 tok × $3/1M = $0.0015
- **Total: ~$0.004 per query** (1000x cheaper)

**Hybrid 500K retrieved + Gemini 3 Pro**:
- Input: 500K × $4/1M = $2.00
- Output: 500 tok × $12/1M = $0.006
- **Total: ~$2 per query** (2x cheaper than pure long-ctx)

**Hybrid with prefix cache (same session)**:
- First query: $2.00 (warm cache)
- Subsequent 5 min: input cache hit ~$0.20 + new query ~$0.05 = $0.25
- **Effective ~$0.25 per query** (16x cheaper)

### 2.3 Volume scaling

```python
def daily_cost(architecture, qps_per_day):
    if architecture == 'pure_long_context':
        return qps_per_day * 4.00  # $4/q
    elif architecture == 'pure_rag':
        return qps_per_day * 0.005  # $0.005/q
    elif architecture == 'hybrid':
        return qps_per_day * 1.00   # $1/q avg
    elif architecture == 'hybrid_cached':
        return qps_per_day * 0.25   # cached most queries
```

**Comparison**:

| QPS / day | Pure long-ctx | Pure RAG | Hybrid | Hybrid + cache |
|---|---|---|---|---|
| 100 (research) | $400 | $0.50 | $100 | $25 |
| 1,000 (small B2B) | $4,000 | $5 | $1,000 | $250 |
| 10,000 (consumer) | $40,000 | $50 | $10,000 | $2,500 |
| 100,000 (large) | $400,000 ❌ | $500 | $100,000 ❌ | $25,000 |
| 1,000,000 (mass) | infeasible | $5,000 | infeasible | $250,000 |

**Insight**:
- < 100 q/day: 任何 architecture 都 OK
- 100-1K: hybrid + cache 黄金区
- 1K-100K: hybrid 还可以, pure long 危险
- > 100K: pure RAG 必须

### 2.4 Prefix caching mechanics

**Anthropic ephemeral cache** (Claude):
```python
import anthropic
client = anthropic.Anthropic()

response = client.messages.create(
    model='claude-opus-4-7-latest',
    system=[
        {
            'type': 'text',
            'text': long_system_prompt,  # 5K tokens
            'cache_control': {'type': 'ephemeral'},  # 5min cache
        },
        {
            'type': 'text',
            'text': legal_corpus_chunk,  # 100K tokens of the contract
            'cache_control': {'type': 'ephemeral'},
        },
    ],
    messages=[{'role': 'user', 'content': user_question}],
)
```

- First call: 105K input × $5/1M = $0.525 + cache write surcharge
- Subsequent (in 5 min): 105K cached × $0.50/1M (10%) + new 2K × $5/1M = $0.063
- Save 85%

**Gemini context caching**:
```python
from google.generativeai import GenerativeModel, caching

cache = caching.CachedContent.create(
    model='gemini-3-pro',
    system_instruction=long_system_prompt,
    contents=[corpus_text],
    ttl=datetime.timedelta(hours=1),  # Gemini up to 1h
    display_name='legal_corpus_session_xyz',
)

model = GenerativeModel.from_cached_content(cache)
response = model.generate_content(user_question)
# Cached input billed at 10% normal rate
```

Gemini cache up to **1 hour** TTL (longer than Anthropic 5 min), but $1/1M/hour storage cost.

### 2.5 Cost optimization strategies

```python
class CostAwareRouter:
    def route(self, query, context):
        # Cheap query → RAG only
        if is_simple_lookup(query):
            return 'rag_only', 'gemini-3-flash'

        # Medium query → hybrid
        if is_multi_hop(query):
            if context.session_age < 300:  # 5 min, cache hot
                return 'hybrid', 'claude-opus-4.7'  # cached prefix
            else:
                return 'hybrid', 'gemini-3-pro'  # cheaper, 2M ctx

        # Complex multi-doc reasoning
        if is_complex(query):
            return 'long_ctx', 'gemini-3-pro'

        return 'hybrid', 'gemini-3-flash'  # default
```

---

## ⚙️ Problem 3: Hybrid Pattern — RAG Narrow → Long-context Within

### 3.1 标准 hybrid 架构

```python
class HybridRagLongContext:
    def __init__(self):
        self.rag = HybridRetriever()       # BM25 + dense + RRF + rerank
        self.llm = GeminiClient(model='gemini-3-pro')

    async def query(self, user_q: str, top_docs: int = 10):
        # Stage 1: RAG retrieves whole docs (not just chunks)
        retrieved = await self.rag.retrieve_docs(
            user_q,
            top_k=top_docs,
            granularity='document',  # whole doc, not chunk
        )

        # Stage 2: Pack docs into long context
        context = self._format_docs(retrieved)
        total_tokens = est_tokens(context)

        if total_tokens > 1_500_000:  # Pro 2M leave headroom
            # Too many docs, narrow further
            retrieved = retrieved[:top_docs // 2]
            context = self._format_docs(retrieved)

        # Stage 3: Long-context LLM answers with multi-hop reasoning
        prompt = f"""You have access to the following documents (each tagged with [Doc N]).
Answer the user's question with citations [Doc N] for every factual claim.

Documents:
{context}

User question: {user_q}

Answer with citations:"""

        response = await self.llm.generate(prompt, max_tokens=2000)

        # Stage 4: Validate citations
        cited_ids = extract_citations(response)
        retrieved_ids = [d.id for d in retrieved]
        invalid = [c for c in cited_ids if c not in retrieved_ids]
        if invalid:
            log_hallucinated_citation(invalid)

        return response

    def _format_docs(self, docs):
        return '\n\n'.join(
            f'[Doc {d.id}] {d.title}\n{d.full_text}'
            for d in docs
        )
```

### 3.2 关键设计点

**1. Doc-level retrieval, not chunk-level**:
- Pure RAG 取 5-20 个 chunk (each ~500 token), 2.5K-10K total
- Hybrid 取 5-10 整 doc (each ~50K), 250K-500K total
- Long-context 在 500K 内自由 multi-hop

**2. RAG 仍 hybrid (BM25 + dense + reranker)**:
- 不能用 vanilla dense, 同样有 acronym / SKU 问题
- 见 hybrid-search 题

**3. Granularity 可调**:
```python
GRANULARITY_MAP = {
    'chunk': 500,         # pure RAG
    'section': 5_000,     # 中
    'document': 50_000,   # hybrid 典型
    'corpus_slice': 500_000,  # 极端
}
```

**4. Multi-hop 推理留给 LLM**:
- RAG 不 decompose query, 拿整 doc
- LLM 在 500K 内自由 jump 不同 section
- 不像 pure RAG 还要 query decomposition + 多轮 retrieve

### 3.3 Caching 加 hybrid

```python
class HybridWithCache(HybridRagLongContext):
    def __init__(self):
        super().__init__()
        self.cache_manager = AnthropicCacheManager(ttl=300)

    async def query(self, user_q, session_id):
        # Check if this session has retrieved a corpus already
        cached_corpus = self.cache_manager.get_session_corpus(session_id)

        if cached_corpus and not self._needs_refresh(user_q, cached_corpus):
            # Reuse cached corpus for same session
            context_blob = cached_corpus['context_blob']
            cache_control = {'type': 'ephemeral'}  # cache hit
        else:
            # Fresh retrieval
            retrieved = await self.rag.retrieve_docs(user_q, top_k=10)
            context_blob = self._format_docs(retrieved)
            self.cache_manager.set_session_corpus(session_id, retrieved, context_blob)
            cache_control = {'type': 'ephemeral'}  # cache write

        response = await self.llm_with_cache(
            user_q, context_blob, cache_control,
        )
        return response
```

**典型 cost (ConvFinQA-like)**:
```
Q1 (cold): retrieve 500K → cache write → query → $1.00
Q2-Q5 (warm, < 5min): cache hit → query → $0.10 each
Q6 (after 5min): cache miss → re-retrieve → $1.00

Average over 5 queries: ~$0.25 each (vs $1 without cache)
```

### 3.4 何时 hybrid 失效

- **Corpus 太大**: 500K narrow 后仍 multi-hop 跨 unretrieved docs. → 多轮 retrieve (agentic).
- **Query 完全跨 corpus**: e.g., "compare all 100K contracts for X" — 单次 retrieve 不可能, 需要 batch + aggregate
- **Update 极频繁**: cache 5min, doc 每秒变 → 缓存价值 0, 退化到 pure RAG

---

## ⚙️ Problem 4: Citation + Provenance Comparison

### 4.1 RAG 的 citation 天然性

```python
# Pure RAG
retrieved = [
    Chunk(id='ch_42', doc_id='doc_5', section='4.2', text='...'),
    Chunk(id='ch_77', doc_id='doc_5', section='4.3', text='...'),
    ...
]

# Citation 直接 = chunk.id, 完全确定
prompt = f"""Sources:
[ch_42] {retrieved[0].text}
[ch_77] {retrieved[1].text}
...

Answer with [ch_id] citations:"""

# Post-validate: extract [ch_42] from answer, check in retrieved
```

**优点**:
- Citation 来源明确 (chunk.id 是真实存在的)
- 可点击跳到原文 (chunk → doc → page)
- LLM 不需要"记忆"页码

### 4.2 Long-context citation 的挑战

```python
# Long-context 把整 corpus 拼给 LLM
context = f"""
[Doc 1, page 1-50] ...
[Doc 2, page 1-30] ...
...
"""

prompt = f"""Documents:
{context}

User: {q}
Answer with page citations like [Doc 1, page 23]."""
```

**问题**:

- LLM 可能编 page number (没准确"看到"页码标记)
- Lost-in-middle: 中间 doc / page 信息易丢
- 无法验证 "page 23 says X" 是真有还是 hallucinate

**Mitigation**:

```python
def inject_page_markers(doc_text, page_size=2000):
    """显式插入 page marker, 让 LLM 能 reference"""
    pages = []
    tokens = tokenize(doc_text)
    for i in range(0, len(tokens), page_size):
        page_num = i // page_size + 1
        page_tokens = tokens[i:i + page_size]
        pages.append(f'<page n="{page_num}">{detokenize(page_tokens)}</page>')
    return '\n'.join(pages)

# Prompt:
"""
<doc id="contract_42">
<page n="1">...</page>
<page n="2">...</page>
...
</doc>

When citing, use [doc_42 p.23] format. Quote the exact text you saw.
"""
```

**Post-validation**:

```python
def validate_long_ctx_citation(answer, context):
    citations = re.findall(r'\[(\w+) p\.(\d+)\]', answer)
    for doc_id, page in citations:
        # Find the page in context
        page_match = re.search(
            rf'<page n="{page}">(.*?)</page>',
            context, re.DOTALL,
        )
        if not page_match:
            return False, f'Citation [{doc_id} p.{page}] not in context'

        # Check claim near citation is grounded in page text
        claim = extract_claim_near_citation(answer, doc_id, page)
        if not is_claim_grounded(claim, page_match.group(1)):
            return False, f'Claim not grounded in [{doc_id} p.{page}]'

    return True, None
```

### 4.3 Hybrid 的 citation (最佳)

```python
# Hybrid: RAG 取 whole doc, citation 用 doc + section/page
prompt = f"""You have access to these documents (each tagged with doc_id):

[Doc contract_42] (sections 1-20)
{doc_42_full_text}

[Doc contract_77]
{doc_77_full_text}

Answer with [doc_id, section.X] citations."""
```

**优点**:
- Doc 来源天然存在 (RAG retrieved)
- Section reference 比 page number 稳 (LLM 看 section heading 不易丢)
- Post-validate: section in doc text

### 4.4 Citation 验证 framework

```python
class CitationValidator:
    def __init__(self):
        self.llm_judge = GeminiClient(model='gemini-3-flash')

    def validate(self, answer: str, context: dict) -> dict:
        citations = self._extract_citations(answer)
        valid = []
        invalid = []
        unsupported = []

        for cite in citations:
            # Format check
            if not self._is_valid_format(cite):
                invalid.append(cite)
                continue

            # Existence check
            source = self._lookup_source(cite, context)
            if not source:
                invalid.append(cite)
                continue

            # Groundedness check (LLM judge)
            claim = self._extract_claim_near(answer, cite)
            if not self._is_grounded(claim, source):
                unsupported.append((cite, claim))
                continue

            valid.append(cite)

        return {
            'total': len(citations),
            'valid': valid,
            'invalid': invalid,
            'unsupported': unsupported,
            'pass_rate': len(valid) / max(len(citations), 1),
        }

    def _is_grounded(self, claim, source_text):
        prompt = f"""Is the following claim factually supported by the source text?

Claim: {claim}
Source: {source_text}

Answer yes or no with brief reason."""
        resp = self.llm_judge.generate(prompt, max_tokens=50)
        return 'yes' in resp.lower()
```

**Production**: every prod answer 跑 validator, alert if pass_rate < 90%.

### 4.5 用户 UI 上的 citation

```
Answer:
  The indemnity cap is $5M [Doc contract_42, §8.2], and the limitation of
  liability is set at $2M [Doc contract_42, §12.1]. These cap each other so
  the effective max liability is $2M.

Sources panel (clickable):
  - [Doc contract_42] Vendor Service Agreement
    §8.2 (page 23): "Indemnity capped at $5M..." [view full]
    §12.1 (page 41): "Limitation of liability $2M..." [view full]
```

让用户能 verify, 也提升信任.

---

## ⚙️ Problem 5: Update Frequency + Freshness Trade-off

### 5.1 Update 模式

| 频率 | 例 | 适用 architecture |
|---|---|---|
| Static (年/never) | 法律合同 (签了不变) | Long-ctx + 永久 cache |
| Slow (月度) | Policy doc | Long-ctx + 重 cache 月度 |
| Daily | KB / Confluence | RAG + nightly reindex 或 long-ctx + daily rebuild |
| Hourly | News feed | RAG + hourly index + delta |
| Real-time (秒级) | Trade data, dashboard | RAG only, hot index |

### 5.2 Long-context update 难题

```
Pure long-context:
  Day 1: load 1M tokens of legal corpus → query
  Day 2: 5 docs were updated
  → 必须 reload 全 1M (因为 long-ctx 不能 partial update)
  → 重新付 cache write cost

Pure RAG:
  Day 1: index 1M tokens → query
  Day 2: 5 docs updated
  → delta reindex only 5 docs' chunks
  → query 时拿到最新 chunk
  → 0 disruption
```

**结论**: 越频繁更新, RAG 越占优.

### 5.3 Hybrid 的 update 处理

```python
class HybridFreshness:
    def __init__(self):
        self.rag = HybridRetriever()
        self.cache_manager = AnthropicCacheManager()

    async def doc_updated(self, doc_id):
        # 1. Update RAG index (delta)
        await self.rag.update_doc(doc_id)

        # 2. Invalidate any cache that included this doc
        affected_sessions = await self.cache_manager.find_sessions_with_doc(doc_id)
        for session_id in affected_sessions:
            await self.cache_manager.invalidate(session_id)

        # 3. Notify ongoing agents
        await self.notify_agents(doc_id, 'doc_updated')
```

### 5.4 Freshness signal in retrieval

```python
def freshness_boost(doc, tau_days=30):
    age = (now() - doc.updated_at).days
    return exp(-age / tau_days)

def hybrid_score(doc, relevance_score):
    return relevance_score * (0.7 + 0.3 * freshness_boost(doc))
```

适用 news / 时效性 content. 长寿 content (法律 / 历史) 不要 freshness 衰减.

### 5.5 Mixing static + dynamic corpus

实际公司 corpus 通常 mixed:
- 静态: 政策 / 合同 / archived (10M tokens, never change)
- 动态: tickets / chat / today's news (1M tokens, hourly update)

**Architecture**:

```python
class MixedFreshness:
    async def query(self, user_q):
        # Always retrieve from both
        static_results = await self.static_rag.search(user_q, top_k=5)
        dynamic_results = await self.dynamic_rag.search(user_q, top_k=5)

        # Static can prefix-cache aggressively
        static_context = self._format(static_results)
        # Dynamic: no caching, fresh every query
        dynamic_context = self._format(dynamic_results)

        # LLM call with cache on static, no cache on dynamic
        response = await self.llm.generate_with_split_cache(
            cached_blocks=[static_context],
            fresh_blocks=[dynamic_context, user_q],
            ttl_seconds=3600,  # 1h on static, dynamic always fresh
        )
        return response
```

### 5.6 Cache invalidation patterns

```python
class CacheInvalidator:
    """精细化 invalidation: 不要一改 doc 就全 cache 重建"""

    async def on_doc_change(self, doc_id, change_type):
        if change_type == 'minor_typo':
            # 不 invalidate cache, 接受短暂不一致
            return

        if change_type == 'content_change':
            # Invalidate cache 但保留 RAG index 同步
            await self.invalidate_cache_containing(doc_id)
            await self.rag.update_doc(doc_id)

        if change_type == 'delete':
            # 立即 invalidate + remove from index
            await self.rag.delete_doc(doc_id)
            await self.invalidate_cache_containing(doc_id)

        if change_type == 'permissions_change':
            # 仅 invalidate cache for affected users
            users = await self.get_affected_users(doc_id)
            for u in users:
                await self.invalidate_user_cache(u)
```

### 5.7 Update frequency cost analysis

```
Pure long-context, 1M token corpus, daily 1% update:
  Daily: re-cache 1M × $5/1M = $5 per refresh per active session
  100 active session × $5 = $500/day just for cache refresh
  + per-query cost

Pure RAG, 1M token corpus, daily 1% update:
  Daily delta reindex: 10K tokens × $0.025/1M (embed) = $0.00025 cost
  Per-query unchanged

Hybrid: in between
```

Update 频繁时 RAG 经济优势压倒一切.

---

# Part 3 · 把 5 个问题串起来看

5 个问题 = 同一架构决策的 5 个维度:

1. **Decision tree** 决定「选哪种 mode」
2. **Cost math** 决定「production 可不可持续」
3. **Hybrid pattern** 决定「实战 mostly 怎么搭」
4. **Citation** 决定「答案可不可信」
5. **Update frequency** 决定「rag vs long-ctx 哪边占优」

把这 5 维度都讲清楚 + ConvFinQA hybrid 案例, 就是 staff-level RAG / LLM 架构师水准.

---

## 必问 clarifying questions

**1. Corpus size**

> "Total token count? 1M context window 大 doc OK; 100M? not even close. 数字决定 mode."

**2. Update frequency**

> "Static (one-time legal corpus) or dynamic (daily news / real-time)? Affects RAG vs long-ctx feasibility."

**3. Query pattern**

> "Single-fact lookup, multi-hop cross-doc, summary, semantic search? Multi-hop 偏 long-ctx, lookup 偏 RAG."

**4. Volume / cost**

> "QPS expected, per-query cost ceiling? 100K queries/day × $4 = $400K/day pure long-ctx 不可持续."

**5. Citation 精度需求**

> "Citation traceability needed (legal/medical)? RAG natural. Long-context citation 靠 prompt + post-validate."

---

## 5 步框架 (sample 45-min answer)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify corpus / volume / cost / multi-hop / citation |
| 5-15 min | Long-context limits (cost / latency / lost-in-middle / vendor lock) |
| 15-25 min | RAG limits (retrieval miss, multi-hop) |
| 25-35 min | Hybrid pattern (RAG narrow + long-ctx within) + prefix cache |
| 35-45 min | Decision tree + cost math + recommendation |

---

## 我会这样答 (sample)

> "Clarify — *[假设: 100K legal docs ≈ 500M tokens total, monthly update, low-volume high-value queries ($5/q acceptable for legal research), citation strict required]*.
>
> Quick answer: **hybrid**. Pure long-context doesn't fit 500M tokens (Pro 2M max). Pure RAG can miss multi-hop. Use **RAG-retrieval + long-context-for-doc-chunks**.
>
> Let me defend by walking trade-offs:
>
> **Long-context strengths**: no retrieval miss within fitted corpus, multi-hop natural, implicit cross-doc reasoning.
>
> **Long-context weaknesses**: cost ($4/q at 1M Gemini 3 Pro >200K tier), latency 30-60s, lost-in-middle still real, doesn't fit > 2M, no granular update.
>
> **RAG strengths**: scales to billion tokens, cheap per query ($0.005-0.05), fast (100ms-2s), granular update, citation natural.
>
> **RAG weaknesses**: retrieval miss, multi-hop hard, chunking fragility, engineering complexity.
>
> **Decision tree**:
> - Corpus < 200K? → Pure long-context
> - Corpus < 2M + cost OK? → Pure long-context if multi-hop heavy
> - Multi-hop heavy + corpus large? → Hybrid
> - Default? → Pure RAG
>
> **Hybrid for our case**:
> - Stage 1: RAG retrieves top-10 whole docs (each ~50K tokens, total ~500K)
> - Stage 2: Gemini 3 Pro reads 500K context, multi-hop reasoning within
> - Citation enforced via doc_id + section ref, post-validate
> - Prefix cache on retrieved docs (5 min for same session)
>
> **Cost**:
> - Pure long-context: $2000/q (500M doesn't fit, infeasible)
> - Pure RAG: $0.005/q, misses multi-hop
> - Hybrid: $1.00/q (500K × $2/1M Pro standard tier; cached: $0.10)
>
> **Volume scaling**:
> - 100 queries/day = $100/day hybrid, manageable
> - 100K queries/day = $100K/day, must optimize (cache, smaller context, cheaper Flash for cheap queries, query routing)
>
> **Citation**: hybrid wins — chunk IDs from RAG natural, validated post-LLM. Long-context citation 靠 prompt prone to hallucinate page numbers.
>
> **Update**: docs change monthly → delta reindex RAG layer cheap; cache invalidate affected sessions; full-context-cache 1h TTL refresh.
>
> **When pure long-context wins**: small corpus (<200K), multi-hop heavy, low QPS (research tools, cost less concern, no RAG engineering team).
>
> **When pure RAG wins**: huge corpus (>10M), high QPS, cost-sensitive, granular updates, strong retrieval engineering team.
>
> **Most production**: hybrid.
>
> **2026 trend**: as context windows grow (2M Pro → 10M next gen), cutoff shifts but hybrid remains optimal for scale/cost balance."

---

## 简历专属 reframe

| 题 | 你的经验 |
|---|---|
| RAG (BNPL chatbot) | 你 + RAG 经验直接相关 |
| **ConvFinQA** | 财务文档 multi-hop, hybrid 思路你做过 |
| Long-context awareness | **Voice agent** — multi-turn long history mgmt 你做过 |
| Cost optimization | **TikTok payment infra** — cost-per-call always 考虑 |
| Citation | **Compliance** — refund / collection 必 citation |
| Prefix caching | **Voice agent** — multi-turn 内 session prefix cache 你天然用过 |

**主动 quote**:

> "ConvFinQA was exactly this trade-off — financial reports avg 200K tokens each, multi-hop questions. We tried pure RAG (recall lost on cross-table joins, 67% acc) and pure long-context (cost prohibitive at scale, plus 200K Claude was slow at 25s/q). Final architecture: **hybrid — RAG retrieves relevant tables + paragraphs (3-5 doc chunks per query), Claude Sonnet 4.6 200K handles within-retrieved multi-hop reasoning**. Latency 8s/q, cost $0.30/q, accuracy 84% — comparable to pure long-context at 1/5 cost. The key insight: **don't shrink RAG to small chunks if you're going to feed long-context anyway** — retrieve at document/section level (50K not 500), let the LLM do the cross-section reasoning, which it does much better than chained-RAG."

---

## 5 follow-ups

**Q1**: "10M context (Gemini next-gen) — will RAG die?"

**A**: No. Reasons:
- **Corpus often > 10M** (enterprise data lakes 100M-1B+ tokens)
- **Cost** still $$$ at 10M tokens/query (~$40/q at $4/1M)
- **Latency** still slow (10M context first-token 2-5 min)
- **Real-time updates**: still RAG advantage
- RAG just shifts to **wider chunks** (whole docs not paragraphs) when long-context cheap

**Q2**: "Hybrid is complex. Can I just use long-context everywhere if cheap enough?"

**A**: Cost is the gate:
- 100K tokens × $2/1M (Pro ≤200K tier) = $0.20/q → 1M queries/day = $200K/day. Prohibitive at scale.
- 10K tokens (RAG-narrowed) × $0.50/1M (Flash) = $0.005/q → $5K/day. Sustainable.
- **Always cheaper to retrieve first**.
- Hybrid complexity is one-time engineering, sustained cost saving > $100K/year easily.

**Q3**: "Long-context is lost-in-middle. Is RAG immune?"

**A**: Not immune, but better managed:
- RAG retrieves **only relevant**, no middle to lose in
- BUT if 50 chunks retrieved, middle ones in LLM context still lost-in-middle
- Mitigation: rerank chunks by relevance order, put best at start/end (see context-window-mgmt题)

**Q4**: "Citation precision — how compare?"

**A**:
- **RAG**: every claim mapped to retrieved chunk ID, deterministic
- **Long-context**: prompt-enforced citation, but model may hallucinate page reference
- **Hybrid**: RAG-style citation (chunk → doc → page), validated post-LLM
- **RAG wins citation reliability**, especially for legal / medical / finance

**Q5**: "Customer prefers long-context for simplicity. Defend hybrid."

**A**:
- Cost scales linearly with context size pure long-ctx; hybrid sublinear with retrieval scope
- 1M queries × $4 = $4M/day pure long-ctx — unscalable. Hybrid $1M-2M with cache and routing.
- Multi-tenancy: each customer's data isolated → RAG natural (perms filter at retrieval)
- Real-time updates: RAG delta re-embed, long-context full reload
- Vendor lock-in: 2M+ context = Gemini/Claude only; RAG portable across models
- **Simplicity** argument loses to **production economics at scale**

---

## ❌ 易错点 (top 10)

1. **'Long-context killed RAG'** — wrong, complementary
2. **Pure long-context for huge corpus** — doesn't fit, $$$
3. **Pure RAG for multi-hop** — retrieval miss across hops
4. **Ignore cost math** — production economics
5. **No citation strategy** — long-context hallucinates refs
6. **Forget vendor lock-in** — 1M+ is Gemini/Claude only
7. **Forget update frequency** — long-context bad for dynamic data
8. **No prefix caching** — leave 80% savings on table
9. **One-size all queries** — should route simple → RAG, complex → hybrid
10. **No post-LLM citation validation** — hallucinations slip through

---

## ✅ 加分项 (top 10)

1. **Hybrid 是默认答案** in production
2. **Decision tree** by corpus size + cost + multi-hop + update + citation
3. **Cost math explicit** ($1.00/q hybrid Pro vs $4 pure long-context vs $0.005 pure RAG Flash)
4. **Lost-in-middle** both approaches awareness
5. **Citation strategy** comparison (RAG natural, long-ctx prompted + validated)
6. **Update frequency** consideration (RAG advantage for dynamic)
7. **Vendor lock-in** awareness (2M ctx = Gemini/Claude only)
8. **Prefix caching** mechanics + economics
9. **Query routing**: simple → RAG, complex → hybrid
10. **Quote ConvFinQA RAG+long-context architecture, 84% accuracy at $0.30/q**

---

## 一句话总结

> **Long-context vs RAG = 不是二选一, 是 sweet spot 不同. 2026 production 默认 hybrid: RAG narrow 到 doc-level → long-context handle multi-hop within. Decision tree by corpus + cost + multi-hop + update + citation.**

---

## Cheat Sheet

```
Long-context strengths:
  No retrieval miss within fitted corpus
  Multi-hop natural
  Implicit cross-doc context

Long-context weaknesses:
  Cost ($4/q at 1M Gemini 3 Pro >200K tier)
  Latency (30-60s for 1M context)
  Lost-in-middle still real (2M middle 30-40% gap)
  Doesn't fit > 2M corpus
  No granular update
  Vendor lock-in (Gemini / Claude)

RAG strengths:
  Scales to billion tokens
  Cheap per query ($0.005-0.05)
  Fast (100ms-2s)
  Granular update (delta indexing)
  Citation natural (chunk_id)
  Model-agnostic

RAG weaknesses:
  Retrieval miss (chunk doesn't have answer)
  Multi-hop hard (cross-chunk reasoning)
  Chunking fragility
  Engineering complexity

Decision tree:
  Corpus < 200K? → Pure long-context
  Corpus < 2M + cost OK + multi-hop? → Pure long-context
  Multi-hop heavy + large corpus? → Hybrid
  Real-time update? → Pure RAG
  Default? → Pure RAG (cheap, scales)

Hybrid pattern:
  RAG: 500M corpus → top-10 docs (500K total tokens, doc-level not chunk)
  Long-context (Gemini 3 Pro 2M): multi-hop within
  Citation: doc_id + section ref
  Prefix cache: 5min Anthropic / 1h Gemini, 90% off

Cost scaling (2026):
  Pure long-ctx 1M tokens: $4/q (Pro >200K)
  Pure RAG narrowed: $0.005/q (Flash)
  Hybrid: $1/q (Pro standard tier)
  Hybrid + cache: $0.25/q (cached prefix)

  100 q/day:    long $400 | RAG $0.50 | hybrid $25
  100K q/day:   long $400K | RAG $500 | hybrid $25K
  1M q/day:     infeasible | $5K | $250K (still tough)

Prefix caching (Anthropic / Gemini):
  Cache write surcharge
  Cache hit ~10% normal rate
  TTL: 5 min (Anthropic) / 1 hour (Gemini)
  Re-use same corpus across multi-turn session

Citation:
  RAG: chunk-id natural, deterministic
  Long-context: prompt + post-validate, prone to hallucinate
  Hybrid: best of both (doc/section, post-validated)

Update freq:
  Static: long-ctx + permanent cache OK
  Daily: hybrid + nightly cache rebuild
  Hourly: hybrid + cache invalidation
  Real-time: pure RAG (hot index)

Query routing in production:
  is_simple_lookup → pure RAG (Flash)
  is_multi_hop + session_warm → hybrid + cached prefix
  is_complex_synthesis → hybrid (Pro 2M)
  default → hybrid Flash

Vendor lock-in:
  2M+ context: Gemini 3 Pro / Gemini 3 Flash 1M
  200K: Claude family, GPT-5.5 256K
  Long-ctx mode → locked to top 1-2 vendors
  RAG mode → model-agnostic

2026 trend:
  Context grows but hybrid remains
  RAG chunks wider as context cheaper
  Both alive
  Prefix caching makes long-ctx cheaper

红线:
  - 'Long-context killed RAG'
  - Pure long for huge corpus
  - Pure RAG for multi-hop
  - Ignore cost math
  - No citation strategy
  - No prefix caching
  - One-size all queries
  - Vendor lock-in 不察觉
```
