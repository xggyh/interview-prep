## 题目（verbatim）

> **[OpenAI Technical Deep Dive — 60 min]**
>
> "Walk me through the **tradeoffs of RAG vs fine-tuning vs prompt engineering**. When does each win? When do you combine them?"

**出处**: OpenAI FDE 真题. Google Cloud / Anthropic / Databricks ML platform FDE 都问. **AI Deep Dive 经典**.

**Round**: Technical Deep Dive (60 min)

---

## 这道题在考什么

考你 **production AI decision-making**:

1. **3 个技术 distinct 区分** — 很多 candidate 混淆 RAG / FT / PE 的本质
2. **真实 cost / quality / latency / staffing tradeoffs**
3. **Combinations** — 真实 production 是 hybrid
4. **When NOT to use each** — 同等重要
5. **Knowing limits** — FT 不能 inject knowledge, PE 限于 context window, RAG 不能教 reasoning
6. **Pragmatic order** — 不是「都用最好」, 是「按 ROI 顺序加」
7. **2026 long-context era** — Gemini 3 Pro 2M context, Claude Opus 4.7 1M, 影响哪个 wins

不考概念定义, 考「你给客户做 deployment, 怎么选」.

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 三个术语先讲透

**Prompt Engineering (PE)**: 改 **input format**. 包括 system prompt 设计, few-shot example, structured output schema, chain-of-thought 引导. **不改 model weight, 不改 retrieval pipeline, 只改进 prompt**.

```
Bad PE:    "回答这个问题"
Good PE:   "你是 TikTok PayLater 的客服 agent. 用户问题如下: ...
            按以下步骤思考: 1) 识别 intent ... 
            输出 JSON: {intent: str, response: str, escalate: bool}"
```

**RAG (Retrieval-Augmented Generation)**: 在 prompt 里**动态注入** retrieved context. 让 LLM「带着资料答」.

```
User query  →  Retrieve relevant docs from vector DB
            →  Prompt = "Based on this context: {chunks}\n\nAnswer: {query}"
            →  LLM generates answer with citations
```

**Fine-Tuning (FT)**: 改 **model weights**. 用 (input, expected_output) 对训练, 让 model 学新的行为 / 风格 / 输出 schema. 2026 主流 3 种:

- **SFT (Supervised Fine-Tuning)**: 标准 next-token prediction on labeled data
- **DPO (Direct Preference Optimization)**: 用 (chosen, rejected) 对学偏好, 不需要 reward model
- **RLHF / RL alignment**: 加 reward model + PPO, 复杂但 quality 最高 (Anthropic, OpenAI 用这个)

---

## 2. 这个问题的核心是什么

设想 **PE / RAG / FT 选错** 的 4 类典型灾难:

### 错误 1: 用 FT 注入 facts (经典反面教材)

```
客户: "把我们的 5000 页产品手册 baked into the model"
工程师: "好, 我 fine-tune"

结果:
  - 训练 3 周 + $50k 成本
  - Model 答时 hallucinate variations of 真实事实
  - "退款 14 天" 被记成 "退款 7-21 天" (probabilistic memory)
  - 产品 doc 更新 → 必须 re-train
  - 没有 citation, 合规审计过不去
```

**正确**: RAG, 因为 facts 是离散的, 不是 pattern.

### 错误 2: 用 PE 解决 multilingual style

```
客户: "我们要 6 种语言一致的债务催收风格"
工程师: "我在 system prompt 写 'be polite in all languages'"

结果:
  - 印尼语输出 ok
  - 越南语句子结构错误 (没学过本地客服 norm)
  - 葡萄牙语 (巴西) 太正式 (本地需 informal)
  - PM 抱怨 "听起来像翻译软件"
```

**正确**: 多语言 SFT + 每语言 5k 真实 case, learn style.

### 错误 3: 用 RAG 解决 reasoning

```
客户: "用户问 '我能用 PayLater 同时分期 A 和 B 吗?', 答错了"
工程师: "加更多 doc 到 RAG"

结果:
  - 加了 100 篇 doc
  - Model 检索到 "A 的限额" 和 "B 的限额"
  - 但不知道怎么 reason: total credit > sum or max(A, B)?
```

**正确**: PE (CoT prompt + structured reasoning) 或 FT on multi-hop examples.

### 错误 4: PE-only on 100k queries/day

```
工程师: "PE 最简单, 直接用"
PM 半年后: "API 费用 $200k / 月"

分析:
  - GPT-5.5 $5/M input + $30/M output
  - 100k × 800 input × $5/M = $400/day
  - 100k × 200 output × $30/M = $600/day
  - $1k/day × 30 = $30k/月 → 一年 $360k ❌
```

**正确**: PE → 找到 winning prompt → SFT 较小 model (Haiku 4.5) 用 PE-generated data, 成本降 10x.

### 正确的解法 — 知道每个技术的 **首选场景**:

```
PE:    Reasoning patterns, output format, low-volume / prototype
RAG:   Facts, frequently-updated knowledge, citation needs
FT:    Style, consistency, low-resource lang, cost-down at volume
```

---

## 3. 决策流程图

```
            [Customer 问题]
                 │
                 ▼
   ┌──────────────────────────┐
   │ 问题本质是什么?           │
   └──────────────────────────┘
        ├── 缺知识?
        │   ├── Static + small → 放 prompt (PE)
        │   ├── Dynamic / large → RAG
        │   └── Per-tenant private → RAG with tenant filter
        │
        ├── 缺 reasoning skill?
        │   ├── Try CoT prompt first (PE)
        │   ├── Few-shot example (PE)
        │   └── If still failing → FT on multi-hop examples
        │
        ├── 缺 style / format consistency?
        │   ├── Try structured output schema (PE)
        │   ├── Try detailed system prompt (PE)
        │   └── If still inconsistent → FT (SFT or DPO)
        │
        ├── Cost太高?
        │   ├── Smaller model + PE (cheap)
        │   ├── Distill big model → small via FT
        │   └── Cache responses (free)
        │
        └── Latency 太高?
            ├── Smaller model (PE adapt)
            ├── Skip RAG if knowledge in prompt (PE only)
            └── Quantize / speculative decode (infra)

最佳实践 sequence:
  Week 1:  PE only, build eval set
  Week 2-3: + RAG, measure lift
  Month 2+: + FT only if PE+RAG plateau AND volume justifies cost
```

---

## 4. 3 技术 cheat sheet 详细对比

| Aspect | Prompt Engineering | RAG | Fine-tuning |
|---|---|---|---|
| **改变什么** | Input format | Input (retrieved context) | Model weights |
| **典型 setup cost** | $0 (engineer time only) | $1-5k (vector DB + embed) | $5-100k (compute + data) |
| **Per-query cost** | LLM call only | LLM + retrieval + rerank | LLM call (often cheaper if small FT model) |
| **Latency overhead** | None | +30-200ms retrieval | None (same as base) |
| **数据需求** | 0 / few-shot examples | Knowledge corpus | 1k-100k labeled pairs |
| **Time to iterate** | Minutes (edit prompt) | Hours (re-embed delta) | Days-weeks (re-train) |
| **可解释性** | High (prompt visible) | High (cite sources) | Low (black-box weights) |
| **Best for** | Reasoning patterns, format, MVP | Factual knowledge, current info | Style, format consistency, cost-reduction at scale |
| **Worst for** | Domain knowledge gap | Reasoning patterns | Frequently-changing facts |
| **Failure mode** | Prompt creep (>5k tokens) | Garbage retrieval → garbage out | Catastrophic forgetting, overfit |
| **Compliance** | Easy (audit prompts) | Cite sources (good for regulated) | Hard (weights opaque) |
| **2026 examples** | Custom GPT, system prompt | ChatGPT search, Perplexity | Anthropic Constitutional AI, OpenAI o1 |

---

## 5. 具体业务场景 (5 类 real-world)

### 场景 A: TikTok BNPL 客服 chatbot (你的工作)

**问题分解**:

| 子任务 | 选哪个? | 理由 |
|---|---|---|
| Intent classification | PE + small model (Haiku) | Few-shot 足够, 改 intent label fast |
| Multilingual response | FT (SFT on multilingual data) | 风格一致性, PE 不够 |
| FAQ knowledge retrieval | RAG | 知识动态, 每月更新 |
| Multi-step reasoning ("我能不能 X") | PE (CoT) + RAG | Structured prompt + retrieve facts |
| Escalation policy | PE (structured output schema) | Rules clear, just enforce format |

**Pipeline**:

```
User: "Saya tidak bisa membayar bulan ini, apa yang harus dilakukan?"
  ↓
[1. Intent classify] (Haiku 4.5 + PE) → intent: "payment_difficulty"
  ↓
[2. RAG retrieve] (Qdrant) → policy chunks on debt restructuring
  ↓
[3. Generate response] (SFT Sonnet 4.6 on Indonesian collection data)
   → "Halo, kami memahami situasi Anda. Berikut opsi yang tersedia: ..."
  ↓
[4. JSON parse] → {response, escalate: false, next_action: "extend_30d"}
```

### 场景 B: ConvFinQA-style 多跳金融问答 (你做过)

**问题**: "What was the % change in revenue from 2022 Q3 to 2023 Q4, and how does it compare to industry average?"

| 子任务 | 选哪个? | 理由 |
|---|---|---|
| Query decomposition | PE (CoT) | "First find 2022 Q3 revenue, then 2023 Q4, then % change" |
| Number extraction | RAG (tabular index) | Numbers in 10-K tables |
| Calculation | Code tool call | LLM bad at arithmetic, use Python |
| Industry comparison | RAG (other companies' 10-K) | Knowledge lookup |
| Final synthesis | PE (template) | Format consistent answer |

**不用 FT 的原因**: 财务知识每季度变, FT 不适合. 用 RAG + tool.

### 场景 C: Voice Agent 多市场债务催收 (你 own 的)

**问题**: 7 markets, 6 languages, consistent tone, regulatory-compliant.

| 子任务 | 选哪个? | 理由 |
|---|---|---|
| Multilingual collection tone | FT (SFT + DPO) | 风格一致性 PE 不行 |
| Per-market regulatory phrases | RAG (per-market policy DB) | 法规更新 |
| Conversation flow | PE (state machine in prompt) | Stateful logic |
| Off-policy detection | FT (classifier head) | Real-time需要 |
| Voice TTS naturalness | Separate (TTS model) | 不同 problem |

**Why FT 主导**:
- 用户体验依赖 tone 一致性 (PE 做不到 6 lang 同步)
- DPO 用 (good_collection_dialogue, bad_dialogue) 对训, 1 month 数据足够
- 训完 model 比 PE 便宜 (cheaper Sonnet 4.6 with FT 接近 Opus 4.7 quality)

### 场景 D: Code Generation Copilot (e.g., GitHub Copilot, Cursor)

**问题**: 给 codebase context, 生成代码补全.

| 子任务 | 选哪个? | 理由 |
|---|---|---|
| Codebase context | RAG (代码 embed + AST chunker) | 仓库太大 fit 不进 prompt |
| Function name conventions | FT (per-company codebase SFT) | 风格 PE 学不会 |
| Bug fix suggestion | PE + RAG | Few-shot + retrieve similar issues |
| Comment style | FT | 风格一致 |

### 场景 E: 内部 Agent Platform (你简历里的)

**问题**: 一个 platform 服务多个内部 team, 每 team 不同 agent.

| 设计选择 | 选哪个? | 理由 |
|---|---|---|
| Shared base capability | Base model (no FT) | 通用能力 |
| Per-team customization | PE templates (system prompt per team) | Fast iteration |
| Cross-team knowledge sharing | Shared RAG (with ACL) | 知识动态 |
| 内部专用 tone (e.g., 内部沟通风格) | Light SFT on internal logs | 一致风格 |

**模式**: PE first, RAG when knowledge needed, FT only when scale justifies.

---

## 6. 工程上要做什么 — pragmatic ordering

### Step 1: Eval baseline first (Week 1)

```python
# 最小可执行的 eval set
eval_set = [
    EvalSample(query="...", expected="...", category="..."),
    # 100-200 samples
]

# Measure: just PE on base model
results = [base_model.answer(q.query) for q in eval_set]
baseline_score = score(results, eval_set)
print(f"Baseline (PE only): {baseline_score:.1%}")
```

### Step 2: PE iteration (Week 1-2)

```python
# Try different prompt strategies
strategies = {
    'naive': "Answer: {query}",
    'cot': "Think step by step. Question: {query}",
    'fewshot': "Examples:\n{examples}\n\nQ: {query}",
    'structured': "Answer in JSON: {schema}\nQ: {query}",
}

best_pe = max(strategies, key=lambda s: eval_with_strategy(s))
```

### Step 3: Add RAG if knowledge gap (Week 2-3)

```python
# Check: failure mode is knowledge gap?
errors = [r for r in results if not r.correct]
manual_review_sample = random.sample(errors, 20)

# For each error, ask: did model lack info or fail to reason?
if 'lack_info' is dominant_failure:
    # → RAG will help
    build_rag_index(corpus)
    rag_results = test_with_rag(eval_set)

elif 'fail_reason' is dominant:
    # → RAG won't help, try better PE / FT
    pass
```

### Step 4: Cost analysis at scale (before FT)

```python
def project_cost(volume_per_day, model_strategy):
    if model_strategy == 'big_model_pe':
        return volume_per_day * 0.05  # GPT-5.5
    elif model_strategy == 'big_model_rag':
        return volume_per_day * 0.06
    elif model_strategy == 'small_ft_model':
        return volume_per_day * 0.005 + amortized_train_cost
    
# At 100k qps/day:
#   big_model_pe:        $5k/day = $150k/month
#   big_model_rag:       $6k/day = $180k/month
#   small_ft_model:      $0.5k/day = $15k/month + $30k FT
#   FT payback:          $135k saving / month, FT pays back in < 1 month
```

### Step 5: Fine-tune only after PE+RAG plateau

```python
# Criteria to start FT:
criteria = {
    'pe_rag_quality_plateaued': True,  # Can't improve via prompts
    'volume_justifies_cost': True,     # > 50k queries/day usually
    'data_available': True,            # 1k+ labeled examples
    'use_case_stable': True,           # Won't change next week
    'engineering_capacity': True,      # 1-2 engineers for 1 month
}

if all(criteria.values()):
    start_ft_project()
else:
    print("Don't FT yet, focus on PE+RAG")
```

### Step 6: Production deployment + monitoring

```
- Cascade routing (cheap model first, fall back to expensive)
- Per-model A/B test
- Drift detection
- Cost monitoring (daily $$ per model)
```

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **Treat as 3 alternatives** when they're complementary | 选错, 落坑 |
| 2 | **FT to inject facts** | Top anti-pattern, hallucinate variations |
| 3 | **PE only when knowledge gap obvious** | Hallucination, customer 抱怨 |
| 4 | **Skip eval baseline before adding techniques** | Don't know what's working |
| 5 | **Forget cost analysis at scale** | $200k/month surprise |
| 6 | **No mention of combinations** | Production reality is hybrid |
| 7 | **Confuse RAG with semantic search** | RAG = retrieve + generate, search is half of it |
| 8 | **FT on < 1k examples** | Overfit, worse than base |
| 9 | **No long-context awareness** | Out of date, sometimes RAG 不必要 |
| 10 | **Same model judges itself in eval** | Bias, false confidence |

---

## 一句话总结 (Part 1)

> **PE / RAG / FT 是 complementary tools, 不是 alternatives. 选择不是 "用哪个", 是 "什么 layer 用哪个 + 什么时候加下一个"**.
>
> 大多数 production system 是 **PE + RAG ± FT** 的某种混合, 看 cost / quality / latency 三角具体怎么权衡.

---

# Part 2 · 5 个深度工程问题

## ⚙️ Problem 1: Decision Framework — 怎么选, 用什么 dimension

### 1.1 选型的 6 维度

```
1. Data freshness need
   ├── Static (rarely changes) → PE (prompt) or FT (weights)
   └── Dynamic (changes daily) → RAG

2. Knowledge size
   ├── < 5k tokens → fit in PE prompt
   ├── 5k - 100M tokens → RAG
   ├── 100M+ tokens → RAG with sharding + tiering
   └── < 1M tokens, static → maybe long-context model (Gemini 3 Pro)

3. Customization need
   ├── Per-tenant data → RAG with tenant filter
   ├── Per-team prompts → PE templates
   ├── Per-company style → FT
   └── Global, shared → base model

4. Quality bar
   ├── < 80% acceptable → PE on big model
   ├── 80-90% → PE + RAG
   ├── > 90% → PE + RAG + FT + rerank
   └── > 95% → human-in-loop layer + extensive eval

5. Latency budget
   ├── < 100ms → PE on small model only
   ├── 100-500ms → PE + small RAG
   ├── 500ms-2s → PE + RAG + rerank
   └── > 2s OK → multi-step agent

6. Cost budget
   ├── < $0.01/query → small model + PE
   ├── $0.01-0.10/query → mid model + RAG
   ├── $0.10-1.00/query → big model + RAG + tool calls
   └── > $1/query OK → premium model + multi-step
```

### 1.2 6 维度决策矩阵

```python
def recommend_approach(criteria):
    if criteria.knowledge_size > 100_000:  # tokens
        if criteria.freshness == 'dynamic':
            return 'RAG'
        elif criteria.fits_in_long_context:
            return 'Long-context model'  # Gemini 3 Pro 2M
        else:
            return 'RAG'

    if criteria.quality_bar > 0.9 and criteria.volume > 50_000_per_day:
        return 'PE + RAG + FT (smaller model)'

    if criteria.latency_budget_ms < 100:
        return 'PE + cache (skip retrieve)'

    if criteria.consistency_need == 'critical' and criteria.style_specific:
        return 'FT (DPO)'

    # Default
    return 'PE + RAG'
```

### 1.3 Time-to-deploy ranking

```
PE only:         hours (write + test prompt)
PE + RAG:        days (build vector DB + retrieve pipeline)
+ Rerank:        days
SFT:             1-3 weeks (data + train + eval)
DPO:             2-4 weeks (preference data harder)
RLHF:            1-3 months (reward model + PPO complex)
```

### 1.4 实战 decision: BNPL chatbot

```
Criteria:
  - 100k queries/day (volume justifies FT)
  - Multi-lingual (6 languages, FT helps style)
  - FAQ knowledge dynamic (RAG essential)
  - Latency < 1s (RAG OK, FT serves faster)
  - Per-tenant (RAG with tenant filter)
  - Quality bar > 90% (need all 3)

Verdict: All 3
  - PE: structured output + few-shot CoT
  - RAG: FAQ + per-tenant policy
  - FT: multilingual tone + intent classifier
```

---

## ⚙️ Problem 2: RAG Deep Dive — When wins, Hybrid Retrieval, Reranker, Eval

### 2.1 When RAG wins

```
✓ Knowledge corpus > 5k tokens (doesn't fit in prompt economically)
✓ Knowledge updates frequently (daily / weekly)
✓ Need citations / source attribution
✓ Multi-tenant (each customer's data separate)
✓ Compliance / audit needs traceability
✓ Cost-sensitive (RAG cheaper than long-context for large corpora)
```

### 2.2 When RAG loses

```
✗ Task is pure reasoning (not knowledge retrieval)
✗ Latency budget < 100ms (RAG adds 30-200ms)
✗ Corpus noisy / low quality (RAG amplifies bad data)
✗ Small static knowledge that fits in prompt
✗ Need very high precision on specific facts (RAG might miss)
```

### 2.3 RAG anatomy — 5 components

```
1. Indexer:
   - Document parser (PDF / HTML / Markdown / DOCX)
   - Chunker (structure-aware / semantic / hierarchical)
   - Embedder (text-embedding-3-large, BGE-M3, Voyage-3)
   - Metadata extractor (heading, freshness, ACL)

2. Storage:
   - Vector DB (Qdrant, Pinecone, Weaviate, Vespa, Milvus)
   - Optional: BM25 index (Elasticsearch, Tantivy)
   - Metadata store (Postgres)

3. Retriever:
   - Embed query
   - Dense + sparse search
   - Pre-filter (ACL, tenant, freshness)
   - Fusion (RRF / weighted)

4. Reranker:
   - Cross-encoder model (bge-reranker-v2, Cohere rerank-v3)
   - Top-100 → top-10

5. Generator:
   - Prompt builder (system + retrieved chunks + query)
   - LLM call (with citations in output)
   - Optional: self-RAG (model decides if it needs more retrieval)
```

### 2.4 Hybrid retrieval 实操

```python
def hybrid_retrieve(query, top_k=10):
    # 1. Dense
    query_emb = embed(query)
    dense_results = qdrant.search(query_emb, top_k=100)

    # 2. Sparse (BM25)
    sparse_results = elasticsearch.search(query, top_k=100)

    # 3. RRF fusion (no weight tuning needed)
    def reciprocal_rank_fusion(results, k=60):
        scores = {}
        for rank, doc in enumerate(results):
            scores[doc.id] = scores.get(doc.id, 0) + 1 / (k + rank)
        return sorted(scores.items(), key=lambda x: -x[1])

    fused = reciprocal_rank_fusion(dense_results)
    fused.update(reciprocal_rank_fusion(sparse_results))
    sorted_results = sorted(fused.items(), key=lambda x: -x[1])

    # 4. Rerank top-50 via cross-encoder
    candidates = [doc for doc, _ in sorted_results[:50]]
    rerank_scores = bge_reranker.score([(query, doc.text) for doc in candidates])
    
    final = sorted(zip(candidates, rerank_scores), key=lambda x: -x[1])
    return [doc for doc, _ in final[:top_k]]
```

### 2.5 Advanced RAG patterns

**Query Rewriting**:

```python
async def rewrite_for_retrieval(query):
    """LLM rewrites query to be more retrievable"""
    prompt = f"""
    Original query: {query}
    
    Rewrite to be more specific for retrieval. 
    Add likely keywords. Expand ambiguity.
    """
    return await haiku_45.generate(prompt)

# "退款多久" → "PayLater refund timeline policy days processing"
```

**HyDE (Hypothetical Document Embeddings)**:

```python
async def hyde_retrieve(query):
    """Generate hypothetical answer, embed it, retrieve similar"""
    hypothetical = await haiku_45.generate(
        f"Write a paragraph that answers: {query}"
    )
    return embed_and_search(hypothetical, top_k=10)

# Especially effective for short / vague queries
```

**Multi-query RAG**:

```python
async def multi_query_rag(query):
    # Generate 3 variations
    queries = await llm.generate_queries(query, n=3)
    
    # Retrieve for each
    all_results = []
    for q in queries:
        all_results.extend(retrieve(q))
    
    # Deduplicate, rerank
    return deduplicate_and_rerank(all_results, original_query=query)
```

**Self-RAG**: Model decides if it needs more retrieval mid-generation.

### 2.6 RAG Eval

```python
# Retrieval-level
retrieval_metrics = {
    'recall@10': fraction_relevant_in_top_10,
    'precision@10': fraction_top_10_relevant,
    'NDCG@10': ranking_quality,
    'MRR': mean_reciprocal_rank,
}

# Generation-level (need ground truth)
generation_metrics = {
    'faithfulness': LLM_judge_does_answer_match_chunks,
    'answer_relevance': LLM_judge_answers_query,
    'context_relevance': LLM_judge_chunks_are_relevant,
}

# End-to-end
e2e_metrics = {
    'answer_correctness': LLM_judge_vs_expected,
    'citation_accuracy': all_claims_have_source,
    'hallucination_rate': claims_not_in_chunks,
}
```

Tools: **Ragas**, **TruLens**, **Phoenix**, **LangSmith** all support these.

---

## ⚙️ Problem 3: Fine-tuning Deep Dive — When wins, SFT vs DPO vs RLHF, Dataset, Eval

### 3.1 When FT wins

```
✓ Consistent output format / style (PE can't reliably enforce)
✓ Low-resource language / domain
✓ Specific reasoning patterns model needs to learn
✓ Volume cost reduction (small FT > big PE at 100k+ qps)
✓ Compliance: domain-specific behaviors auditable in weights
✓ Latency-critical (FT model can be smaller, faster)
```

### 3.2 When FT loses

```
✗ Knowledge changes frequently (re-train cost prohibitive)
✗ Small data (< 1k examples, overfits)
✗ Base model quality matters and you lack eval discipline
✗ Hallucination concerns (FT can amplify, not reduce)
✗ Time-to-deploy < 2 weeks
```

### 3.3 SFT (Supervised Fine-Tuning)

**Format**: (prompt, expected_output) pairs.

```python
# Data format (JSONL)
{"messages": [
    {"role": "system", "content": "You are a debt collection agent..."},
    {"role": "user", "content": "I can't pay this month"},
    {"role": "assistant", "content": "I understand your situation. Let me check..."}
]}
```

**Training**:

```python
# Using OpenAI fine-tuning API
client.fine_tuning.jobs.create(
    training_file="train.jsonl",
    validation_file="val.jsonl",
    model="gpt-5.4",
    hyperparameters={
        "n_epochs": 3,
        "learning_rate_multiplier": 0.1,
    }
)

# Or Hugging Face for open models
from transformers import AutoModelForCausalLM, Trainer, TrainingArguments
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3-8B")
trainer = Trainer(
    model=model,
    args=TrainingArguments(
        learning_rate=2e-5,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
    ),
    train_dataset=train_ds,
)
trainer.train()
```

**Dataset construction**:

- **1k examples minimum** (LoRA can work with less)
- **Diverse coverage** of edge cases, not just happy path
- **Quality > quantity** — 1k carefully labeled > 10k auto-generated
- **Test set 完全 hold out** — 20% of data, never seen during train

**Failure modes**:
- Catastrophic forgetting (model loses general capability)
- Overfit to train distribution
- Format drift (training examples inconsistent)

**LoRA** (Low-Rank Adaptation): Train small adapter (1-3% params), much cheaper, less forgetting.

### 3.4 DPO (Direct Preference Optimization, 2023+)

**Format**: (prompt, chosen, rejected) triples.

```python
# Data format
{
    "prompt": "User: I'm angry, you didn't refund me.\nAssistant:",
    "chosen": "I understand your frustration. Let me investigate your refund...",
    "rejected": "Sorry but per our policy, refunds take 14 days. There's nothing I can do."
}
```

**Why DPO over SFT**:
- 学 preference (相对好) 不只是 absolute output
- 不需要 reward model (RLHF 需要)
- Stable training (no PPO instability)

**Where DPO 数据从哪来**:
- Crowdworker comparison (2 responses, pick better)
- A/B production data (好 response = 用户没 retry / 满意)
- LLM-as-judge generation (Opus 4.7 picks better, 然后用 DPO 训 Sonnet 4.6)

### 3.5 RLHF (Reinforcement Learning from Human Feedback)

最复杂, 最强:

```
1. SFT base model on demonstrations
2. Train reward model (RM) on preference data
3. PPO optimization: model generates → RM scores → policy gradient update
```

**When used 2026**:
- Anthropic Claude (Constitutional AI variation)
- OpenAI o1, GPT-5 (RL on reasoning)
- 你的 voice agent post-training (你简历提到 RL alignment)

**Why hard**:
- PPO instability (要小心 hyperparams)
- Reward hacking (model 找 reward model 漏洞)
- Need engineer-month to implement

### 3.6 FT Eval

```python
# 必须在 hold-out test set 上 eval
test_metrics = {
    'task_accuracy': exact_match_on_held_out,
    'style_consistency': human_or_LLM_judge_rate,
    'general_capability': mmlu_or_helm_subset,  # 别 regression 通用能力
    'safety': red_team_attacks_held,
    'efficiency': latency_p99_vs_base,
}

# 比较 vs base + PE alternative
print(f"FT vs base+PE: {ft_score - pe_score:+.2%}")
# 必须 +2pp 以上才 worth FT 的 cost
```

### 3.7 FT cost reality

```
SFT on 10k examples:
  Compute: 8 GPU × 4h × $2.50/GPU-hr = $80
  Data labeling: 10k × $1.5 = $15k
  Engineering: 2 weeks × $5k = $10k
  Total: ~$25k

DPO on 5k preferences:
  Compute: 8 GPU × 8h × $2.50 = $160
  Data: 5k × $3 (2x cost vs SFT label) = $15k
  Engineering: 3 weeks × $5k = $15k
  Total: ~$30k

RLHF:
  Reward model training: $5k
  PPO loop: $30k compute (volatile)
  Labeling: $40k (lots of comparisons)
  Engineering: 8 weeks × $5k = $40k
  Total: $115k+

→ Payback math:
  If big model API = $0.05/query, small FT = $0.005/query, save $0.045/query
  $25k SFT payback at 556k queries
  At 100k qps/day, payback in 6 days
```

---

## ⚙️ Problem 4: Prompt Engineering Deep Dive — Few-shot, CoT, Structured Output, System Prompt

### 4.1 PE 核心 techniques

**1. System Prompt Design**

```
Anatomy of good system prompt:
  - Role: "You are a debt collection agent for TikTok PayLater..."
  - Capabilities: "You can negotiate payment plans, escalate, refer..."
  - Constraints: "Don't discuss policies you're unsure about..."
  - Output format: "Always respond in JSON with..."
  - Tone: "Empathetic but firm. Use customer's language..."
  - Examples: "{2-3 few-shot examples}"
  - Edge cases: "If user is hostile, escalate..."
```

**2. Few-shot Examples**

```python
prompt = """Examples:

Q: I can't pay my bill this month.
A: {"intent": "payment_difficulty", "response": "I understand. Let me help you set up a payment plan."}

Q: What's the interest rate?
A: {"intent": "policy_inquiry", "response": "[CHECK_RAG: interest_rate_policy]"}

Q: This is fraud!
A: {"intent": "dispute", "response": "I'm sorry to hear that. I'll escalate immediately.", "escalate": true}

Now: {user_query}
A:"""
```

**3. Chain-of-Thought (CoT)**

```python
# Without CoT
"Q: User asked X. Should we approve?"
"A: Yes/No"

# With CoT
"Q: User asked X. Should we approve?
Reasoning: First check eligibility... Then check credit limit... Then check risk... 
Conclusion: ..."
```

**实测**: CoT 在 reasoning tasks 上 +20% accuracy.

**4. Structured Output (JSON Schema)**

```python
from pydantic import BaseModel

class Response(BaseModel):
    intent: str
    confidence: float
    response: str
    requires_escalation: bool
    next_action: Optional[str]

# Anthropic / OpenAI / Gemini all support this 2026
response = client.messages.create(
    model="claude-sonnet-4-6",
    response_format={"type": "json_schema", "schema": Response.model_json_schema()},
    messages=[...]
)
```

**5. Prompt Caching** (Anthropic Claude / OpenAI 2024+)

```python
# Cache system prompt + few-shot (long, repeats per call)
response = client.messages.create(
    model="claude-sonnet-4-6",
    messages=[
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": LONG_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},  # 5-min cache
                }
            ],
        },
        {"role": "user", "content": query},
    ],
)
# First call: full cost
# Subsequent calls within 5 min: 90% cheaper input cost
```

### 4.2 PE 高级 patterns

**6. Self-consistency** (sample N, vote):

```python
async def self_consistent(query, n=5):
    responses = await asyncio.gather(*[
        llm.generate(query, temperature=0.7) for _ in range(n)
    ])
    # Vote on most common answer
    return Counter(responses).most_common(1)[0][0]
```

**7. Tree of Thoughts**:

```
Generate 3 candidate paths
  → Evaluate each
  → Branch on most promising
  → Backtrack if stuck
```

**8. ReAct** (Reasoning + Acting):

```
Thought: User wants to know X. I need to look up Y.
Action: search(Y)
Observation: Y = ...
Thought: Now I can answer.
Answer: ...
```

### 4.3 PE Limits (when PE fails)

```
✗ When prompt > 5k tokens, cost per query becomes painful
✗ Multilingual style consistency (PE inconsistent across languages)
✗ Complex multi-step reasoning beyond CoT
✗ Strict output format that few-shot can't enforce (LLMs drift)
✗ Tone consistency across millions of queries
```

### 4.4 PE Eval

```python
# Test prompts against eval set systematically
prompts = ['naive', 'cot', 'few_shot', 'few_shot_cot', 'structured', 'role_play']

results = {}
for p_name in prompts:
    p_template = load_prompt(p_name)
    scores = [eval_one(p_template, sample) for sample in eval_set]
    results[p_name] = mean(scores)

# Output:
# naive:         0.62
# cot:           0.71
# few_shot:      0.74
# few_shot_cot:  0.81  ← winner
# structured:    0.78
# role_play:     0.72
```

### 4.5 PE 也有 versioning

```python
# Treat prompts like code
prompts/v1.txt
prompts/v2.txt
prompts/v3-with-examples.txt

# A/B test prompt versions
- 50% traffic on v3, 50% on v2
- After 1 week, pick winner by user metric
```

---

## ⚙️ Problem 5: Hybrid Approaches — Real production combinations

### 5.1 Pattern A: PE + RAG (最常见)

```
Use case: 客服 / 助理类
  - PE for: response format, tone, escalation logic
  - RAG for: FAQ, customer-specific data, policy
  - No FT: knowledge is dynamic

Implementation:
  query → PE (intent) → RAG (knowledge) → PE+RAG (answer)
```

**Example**: BNPL 客服 chatbot — PE 教 escalation, RAG 抓 customer FAQ.

### 5.2 Pattern B: PE + FT (无需 retrieve)

```
Use case: 风格 / 格式严格要求, knowledge 静态
  - FT for: tone, multilingual style, output format
  - PE for: per-query specifics (which language, escalation flag)
  - No RAG: no external knowledge needed

Implementation:
  query → FT model (with PE constraints) → response
```

**Example**: Voice agent 多语言 collection tone — FT 教 style, PE 控制 escalation.

### 5.3 Pattern C: RAG + FT (rare 但有价值)

```
Use case: 需要 reasoning pattern + knowledge
  - FT for: 学 multi-step financial reasoning
  - RAG for: 抓 current financial data
  - PE: minimal, structure

Implementation:
  query → FT model (with RAG context)
  Specifically: FT 教 model 怎么用 retrieved info, RAG 提供 info
```

**Example**: ConvFinQA agent — FT 在 financial multi-hop reasoning data, RAG 抓 10-K filings.

### 5.4 Pattern D: All 3 (enterprise)

```
Use case: 复杂 enterprise agent
  - FT: company-specific tone + reasoning
  - RAG: per-tenant knowledge
  - PE: query-time customization + structured output

Implementation:
  query → FT classifier (intent + routing)
       → RAG retrieve (tenant filter)
       → FT generator (with retrieved + PE constraints)
       → PE post-process (JSON validate, redact PII)
```

**Example**: TikTok BNPL chatbot full stack — 你 ship 过的.

### 5.5 Pattern E: Cascade (cheap → expensive)

```
99% queries → small FT model + PE
0.9%        → medium model + RAG
0.1%        → big model + multi-step agent

Routing logic:
  - If intent classifier returns 'simple_greeting' → small FT
  - If intent 'factual_query' → medium + RAG
  - If 'complex_multi_hop' → big agent

Cost: 10x cheaper than always using big model
Quality: 同等水平 (right tool per query)
```

### 5.6 Pattern F: Long-context + RAG (2026 趋势)

```
Knowledge size 100k - 1M tokens, dynamic:
  Option A: Pure RAG → 50k chunks
  Option B: Long-context (Gemini 3 Pro 2M) → 整 corpus in context
  Option C: RAG narrows + long-context digests

Pattern C (best):
  RAG retrieves top-100 chunks (50k tokens)
  Feed all 50k into Gemini 3 Pro
  Gemini reasons over full retrieved set
  
Pros: 
  - Better than pure RAG (model sees more context)
  - Cheaper than full long-context (only relevant chunks)
  - Citation possible (RAG gives sources)
```

### 5.7 Migration path (典型 production)

```
Week 0:     PE on big model (baseline)
Week 1:     Build eval set
Week 2:     PE iteration, best prompt found
Week 3-4:   + RAG (knowledge gap obvious from errors)
Month 2:    Production with PE+RAG, monitor cost
Month 3-4:  Cost too high → FT smaller model on PE+RAG outputs
Month 5:    Cascade: small FT (90%) + big PE+RAG (10%)
Month 6+:   Continuous improvement: collect feedback, DPO refresh

End state: hybrid optimized for cost + quality
```

### 5.8 Hybrid 失败案例

```
"All 3 但没 eval discipline":
  - 加 FT 时 没 hold-out test
  - 加 RAG 时 没 measure recall  
  - 加 PE 时 没 versioning
  → 全部上线, 不知道哪个有用, 想 rollback 没法 isolate

"Premature optimization":
  - Week 1 就 FT (没 baseline)
  - 后来发现 PE+RAG 就够了, FT 浪费

"Cost ignored":
  - 上 RAG + FT + 大 model
  - $ per query 飙升, PM 砍预算
  - 没 cascade 设计, 难 retrofit
```

---

# Part 3 · 把 5 个问题串起来看

这 5 个问题是 **production AI deployment 的完整思考链**:

1. **Decision framework** 给「选什么」的 6 维度
2. **RAG deep dive** 讲清 RAG 各 component
3. **FT deep dive** 讲清 SFT vs DPO vs RLHF 选择
4. **PE deep dive** 讲清 prompt 的 advanced patterns
5. **Hybrid** 讲清 production 怎么组合 3 种

面试场把这 5 层讲透, 加上「我在 BNPL chatbot 用 PE+RAG, voice agent 用 FT, ConvFinQA 用 RAG + tool」, 就是 staff-level applied AI 水准.

---

## 必问 clarifying questions

**1. Use case specifics**

> "What's the task — generation / classification / extraction / agent? Determines technique fit."

**2. Volume + cost budget**

> "Queries/day? Cost cap per query? Affects whether FT economically worth it."

**3. Quality bar**

> "What % accuracy / quality is the floor? Affects whether we need all 3."

**4. Latency budget**

> "Real-time (<500ms) or async? Affects RAG inclusion."

**5. Data availability**

> "Have labeled data for FT? Have knowledge corpus for RAG?"

**6. Team / time budget**

> "1 engineer / 2 weeks vs 5 engineers / 6 months — different recommendations."

---

## 5 步框架 (sample 60-min answer)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify use case + volume + quality + latency + budget |
| 5-15 min | 3 techniques cheat sheet (compare table) |
| 15-30 min | When each wins / loses (5 scenarios each) |
| 30-45 min | Combinations + hybrid patterns (6 patterns) |
| 45-55 min | Cost analysis at scale + pragmatic ordering |
| 55-60 min | Quote my BNPL / voice agent / ConvFinQA experience |

---

## 简历专属 reframe

你的 **BNPL chatbot (Agentic + RAG)** + **voice agent (SFT + DPO + RL post-training)** + **ConvFinQA**:

| 题 | 你做过 |
|---|---|
| RAG for company knowledge | BNPL chatbot FAQ RAG |
| Fine-tuning for style/domain | Voice agent SFT/DPO for multilingual debt collection |
| RL alignment | Voice agent reward modeling 你 own |
| PE + RAG combination | BNPL chatbot — PE for intent + RAG for FAQ |
| RAG + tool call | ConvFinQA — RAG + calculator |
| Cascade routing | BNPL (intent classifier → Haiku/Sonnet/Opus) |
| Cost-aware decisions | TikTok scale forces this |

**主动 quote**:

> "I've literally shipped all three in production at TikTok PayLater.
>
> **For BNPL chatbot**: Started with PE only on Sonnet 4.6 — got 75% accuracy on FAQ queries. Added RAG (FAQ corpus + product-specific docs) → 88%. Tried adding FT but realized our FAQ updates weekly, FT would constantly stale — kept PE+RAG.
>
> **For voice agent**: Multi-lingual debt collection in 6 languages — PE could not enforce consistent empathetic-yet-firm tone across Bahasa / Vietnamese / Thai / Portuguese. Did **SFT on 30k human-curated multilingual examples + DPO on 5k preference pairs** (from actual customer interactions where one response led to repayment, other didn't). Quality lift was +25% on collection success rate. Couldn't have achieved this with PE.
>
> **For ConvFinQA**: Multi-hop financial reasoning — RAG retrieves 10-K chunks, PE structures the reasoning, calculator tool does the math. No FT here — financial knowledge changes quarterly and base model reasoning was sufficient given good PE.
>
> **The lesson**: **Start PE-only, add RAG when knowledge gap is visible, fine-tune only when (style consistency OR cost-at-scale OR latency) demands it**. Never FT to inject facts — RAG is the right tool.
>
> **2026 nuance**: With Gemini 3 Pro 2M context and Claude Opus 4.7 1M context, for **smaller static corpora (< 500k tokens)**, RAG is no longer obviously the right choice. Long-context + cache can win on quality (model sees full context). We're testing this for our internal docs use case."

→ 这是你简历最 perfect match 的题, 一定 ace.

---

## 5 follow-ups

**Q1**: "Customer wants their docs 'baked into the model'. Should we fine-tune?"

**A**: **No, almost certainly RAG**:
- FT doesn't reliably encode facts (hallucinate variations like "policy says X" when it's Y)
- Docs change → need re-FT → expensive ($25k each round)
- No citation → compliance issues (legal / financial / medical)
- **Sit-and-explain why** to customer with their actual docs: "If your policy changes monthly, RAG handles automatically. FT requires monthly re-train at $25k each. Plus FT loses citation capability."
- If customer insists: **mention base model's general knowledge is already strong**, FT might *reduce* general capability while adding marginal facts.

**Q2**: "When does fine-tuning make economic sense at 100k queries/day?"

**A**: Cost math (2026 pricing):
- Opus 4.7 ($5/M input + $25/M output) → ~$0.05/query → **$150k/month**
- Fine-tuned Sonnet 4.6 (3x cheaper if quality match) → $0.015/query → **$45k/month**
- FT setup ~$25k one-time + $30k engineering → **payback in 1 month at this volume**
- **Rule of thumb**: > 50k queries/day, FT a smaller model often pays back in < 3 months
- Plus: FT smaller model has **lower latency** (Sonnet vs Opus ~ 40% faster), so dual benefit

**Q3**: "What if RAG isn't returning relevant docs?"

**A**: Multi-pronged debugging:
- **Chunking**: try structure-aware vs fixed (often the issue)
- **Retrieval method**: pure dense → hybrid (BM25 catches IDs / entities)
- **Reranker**: add cross-encoder rerank top-50 → 10 (+10-15pp recall typical)
- **Query rewriting**: LLM rewrite user query before retrieve (handles ambiguous)
- **HyDE**: have LLM hypothesize an answer, embed that, retrieve similar docs
- **Don't fine-tune** to fix retrieval — that's a separate problem
- **Eval first**: build 100-query golden set, ablation each change, keep what helps

**Q4**: "Our fine-tuned model performs worse than base + prompt. Why?"

**A**: Common causes (in order):
- **Overfitting** to small training set (< 1k examples) — usual culprit
- **Catastrophic forgetting** — model loses general capability (mix in 20% general data)
- **Bad eval** — measured on training data not held-out
- **Wrong base model** — fine-tuning Haiku for complex reasoning when Sonnet base would be better
- **Format inconsistency** — training examples have mixed format → model confused
- **Wrong hyperparams** — learning rate too high (overfit) or too low (no adaptation)

Fix:
- **LoRA not full fine-tune** (less forgetting)
- **Mix new + general data** (prevent catastrophic forgetting)
- **Bigger eval set with diverse examples**
- **Compare to base + best PE** as honest baseline

**Q5**: "Long-context models (Gemini 3 Pro 2M, Claude Opus 4.7 1M) — does this kill RAG?"

**A**: **Not yet, but use case narrows**:
- **Long-context wins** when: corpus < 1M tokens, **static**, no privacy issues, latency tolerant (long context is slow + expensive). E.g., "analyze this 200-page contract".
- **RAG wins** when: corpus huge / dynamic / multi-tenant / per-user / cost-sensitive.
  - Cost math: Gemini 3 Pro 2M context at $2/M input → $4/query naively. RAG retrieves 5k → $0.01/query. **400x cheaper**.
- **Hybrid pattern (most common 2026)**: RAG retrieves top-K chunks (50k tokens), feeds into long-context Claude Opus 4.7 → best precision (RAG narrows) + best reasoning (long context model). This is what we're testing for BNPL complex queries.

---

## ❌ 易错点 (top 10)

1. **Treat as 3 alternatives** when they're complementary
2. **FT to inject facts** — top anti-pattern
3. **PE only when knowledge gap obvious** — hallucination
4. **Skip eval baseline before adding techniques**
5. **Forget cost analysis at scale** — $200k/month surprise
6. **No mention of combinations** — production reality
7. **Confuse RAG with semantic search** (RAG = retrieve + generate, search is half)
8. **FT on < 1k examples** — overfits, worse than base
9. **No long-context awareness** — 2026 reality
10. **Same model judges itself in eval** — bias, false confidence

---

## ✅ 加分项 (top 10)

1. **3x10 dimension comparison table**
2. **Concrete cost math** ($150k/month → FT payback in 1 month)
3. **PE → RAG → FT pragmatic order**
4. **6 combination patterns** with examples
5. **Anti-pattern: FT for facts** named
6. **Long-context awareness** + RAG+LC hybrid
7. **HyDE / query rewriting / self-RAG** beyond basic
8. **DPO vs SFT vs RLHF** distinction
9. **Quote BNPL / voice agent / ConvFinQA** specific lessons
10. **Cascade routing** for production cost

---

## 一句话总结

> **PE / RAG / FT 不是选择题, 是组合题**.
>
> 起点: PE-only baseline. 加 RAG 当 knowledge gap. 加 FT 当 style/cost-at-scale 需要. 真正 production 永远是 hybrid.

---

## Cheat Sheet (印 1 页)

```
3 techniques cheat sheet:
                PE            RAG          FT
  Changes:      input         input+ctx    weights
  Setup cost:   $0            $1-5k        $25-100k
  Per query:    $$$$          $$$$         $$
  Latency:      fast          +30-200ms    same
  Updates:      edit (min)    re-embed     re-train
  Best for:     reasoning     facts        style
  Worst for:    knowledge     reasoning    facts
  Compliance:   easy          easy (cite)  hard

6 decision dimensions:
  1. Data freshness (static → PE/FT, dynamic → RAG)
  2. Knowledge size (small → PE, large → RAG, huge → tiered)
  3. Customization (per-tenant → RAG, per-team → PE)
  4. Quality bar (>90% → all 3, <80% → PE only)
  5. Latency budget (<100ms → PE, >500ms OK → all)
  6. Cost budget (cheap → small+PE, expensive OK → all)

Pragmatic order:
  Week 1: PE only + eval set + baseline
  Week 2-3: + RAG (measure recall lift)
  Month 2+: + FT only if PE+RAG plateau AND volume justifies

PE techniques:
  - System prompt (role+constraints+format+examples)
  - Few-shot examples (2-5 representative)
  - Chain-of-thought ("Think step by step")
  - Structured output (JSON schema)
  - Prompt caching (Claude/OpenAI, 90% input save)
  - Self-consistency (sample N, vote)
  - ReAct (reasoning + acting loop)

RAG components:
  Indexer → Storage → Retriever → Reranker → Generator
  Hybrid: dense + BM25 + RRF fusion + rerank top-50→10
  Advanced: query rewriting, HyDE, multi-query, self-RAG
  Eval: recall@K, NDCG, faithfulness, hallucination rate

FT variants:
  SFT (1k+ examples): standard, supervised, $25k typical
  DPO (preference pairs): style learning, no reward model, $30k
  RLHF (full pipeline): max quality, $115k+, engineer-months

FT failure modes:
  - Overfit on <1k examples
  - Catastrophic forgetting (mix 20% general)
  - Wrong hyperparams (LoRA + low LR safer)
  - Format inconsistency in train data

6 hybrid patterns:
  A. PE + RAG (most common — chatbot)
  B. PE + FT (style + query — voice agent)
  C. RAG + FT (reasoning + facts — financial advisor)
  D. All 3 (enterprise — BNPL)
  E. Cascade (cheap → expensive based on intent)
  F. Long-context + RAG (2026 — Gemini 3 Pro 2M)

Cost @ 100k queries/day:
  PE only Opus 4.7: $150k/month
  + RAG: $180k/month (small overhead)
  FT Sonnet 4.6: $45k/month + $25k FT (payback < 1 month)
  Cascade (Haiku 90% + Sonnet 9% + Opus 1%): ~$25k/month

Anti-patterns:
  - FT for facts (use RAG)
  - PE only when knowledge gap (add RAG)
  - FT on <1k examples (overfits)
  - FT to fix retrieval (separate problem)
  - Same model judges itself (bias)
  - Skip eval baseline (don't know what works)

2026 long-context reality:
  Gemini 3 Pro: 2M context, $2 input
  Claude Opus 4.7: 1M context, $5 input
  Long-context wins: small static, latency tolerant
  RAG still wins: large dynamic, cost-sensitive, multi-tenant
  Hybrid (RAG + long-context): best of both

Quotes for interview:
  - "Start PE-only, add RAG when knowledge gap visible, FT when style/cost demands it"
  - "Never FT to inject facts — RAG is the right tool"
  - "PE+RAG covers 80% of production AI use cases"
  - "FT economic at >50k queries/day, payback often <3 months"
  - "Cascade routing 10x cost reduction without quality loss"
```

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

> **PE 改 input format / RAG inject context / FT 改 weights — 3 完全不同手段, 解决不同问题**. PE for reasoning + format, RAG for facts + current info + citation, FT for style + cost-down at scale. **不互斥, production 80% 是 hybrid**. Pragmatic order: PE → RAG → FT (only if plateau + volume justifies). 2026 long-context era: Gemini 3 Pro 2M / Claude Opus 4.7 1M 改变了 RAG vs long-context 边界, 但没 kill RAG.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| PE (Prompt Engineering) | 改 input format, system prompt / few-shot / CoT / schema | 起步必选 |
| RAG | 动态注入 retrieved context, 带资料答 | facts 频繁更新 |
| FT (Fine-Tuning) | 改 model weights, learn pattern | style 一致性 / cost 降 |
| SFT | Supervised, (input, output) labeled | 标准 FT, $25k typical |
| DPO | (chosen, rejected) 偏好对, no reward model | style 学习 |
| RLHF | reward model + PPO | quality max, $115k+ |
| Constitutional AI | Anthropic 用 AI 自我 critique | RLHF 变种 |
| LoRA / QLoRA | low-rank adapter, base frozen | cheaper FT |
| CoT | Chain-of-Thought "step by step" | reasoning PE |
| Few-shot | 2-5 example in prompt | learn pattern |
| ReAct | Reasoning + Acting loop | tool-using agent |
| Self-consistency | sample N + vote | quality > latency |
| HyDE | Hypothetical Document Embedding | RAG query rewrite |
| Multi-query | 1 query → N rephrased | recall boost |
| Self-RAG | model decides 何时 retrieve | adaptive |
| RRF | Reciprocal Rank Fusion | hybrid dense+BM25 |
| Faithfulness | answer 是否 grounded in context | RAG eval metric |
| Hallucination rate | 编造率, RAG critical | RAG eval |
| Catastrophic forgetting | FT 后丢失 general ability | mix 20% general data |
| Prompt caching | Anthropic/OpenAI 输入复用 | 90% input save |

### 🎯 5 个核心 framework

**Framework 1**: 3-Technique Distinction
- When: 任何 AI deployment 决策
- Algorithm:
  - PE: changes input format. $0 setup. fast iterate (mins). Easy compliance.
  - RAG: changes input + retrieved context. $1-5k setup. +30-200ms latency. Citations.
  - FT: changes model weights. $25-100k setup. Days-weeks iterate. Black-box.
- Trade-off: 3 个不互斥, 但起步选错 = 浪费时间金钱
- Tools: LangSmith for PE iteration, Pinecone/Qdrant for RAG, OpenAI fine-tuning API / unsloth for FT

**Framework 2**: 6-Decision Dimensions
- When: 不知道哪个起步
- Algorithm:
  1. Data freshness: static → PE/FT, dynamic → RAG
  2. Knowledge size: small → PE in prompt, large → RAG, huge → tiered (long-context narrow + RAG wide)
  3. Customization: per-tenant → RAG metadata filter, per-team → PE persona
  4. Quality bar: > 90% → all 3, < 80% → PE only
  5. Latency budget: < 100ms → PE, > 500ms OK → all
  6. Cost budget: cheap → small + PE, expensive OK → all
- Trade-off: 6 个 dim 互相 conflict, 必须 ranking
- Tools: decision matrix, ROI calculator per dim

**Framework 3**: Pragmatic Ordering (PE → RAG → FT)
- When: 起步 production
- Algorithm:
  - Week 1: PE only + build eval set + baseline metric
  - Week 2-3: + RAG (measure recall lift, faithfulness)
  - Month 2+: + FT only if PE + RAG plateau AND volume justifies cost
- Trade-off: 慢 vs 一次性 all-in 风险大
- Tools: ragas eval, ablation harness, eval gate

**Framework 4**: 6 Hybrid Patterns (Production Reality)
- When: 真实 production deployment
- Algorithm:
  - A. PE + RAG (most common, chatbot)
  - B. PE + FT (style + query, voice agent)
  - C. RAG + FT (reasoning + facts, financial advisor)
  - D. All 3 (enterprise, BNPL)
  - E. Cascade (cheap → expensive by intent, Haiku 90% / Sonnet 9% / Opus 1% → 10x cost reduce)
  - F. Long-context + RAG (Gemini 3 Pro 2M context, RAG narrow + long-context digest)
- Trade-off: complexity vs quality / cost
- Tools: vLLM router, intent classifier, prefix caching

**Framework 5**: 2026 Long-Context Reality
- When: model 2M+ context 出现
- Algorithm:
  - Gemini 3 Pro 2M ($2/$12) / Claude Opus 4.7 1M ($5/$25)
  - Long-context wins: small static corpus, latency tolerant, simple query
  - RAG still wins: large dynamic, cost-sensitive, multi-tenant, citation required
  - Hybrid (RAG + long-context): RAG narrows to top-50, long-context digests all
- Trade-off: long-context $20+ per query, RAG $0.05 per query
- Tools: Gemini 3 Pro, Claude Opus 4.7, hybrid pattern routing

### 🌳 关键决策树

```
Customer 问题本质?
├── 缺 knowledge?
│   ├── Static + small (<10 pages)? → PE in prompt
│   ├── Dynamic / large? → RAG
│   ├── Per-tenant private? → RAG with tenant filter (ACL)
│   └── Huge corpus + cost OK? → Long-context (Gemini 3 Pro 2M)
├── 缺 reasoning skill?
│   ├── Try CoT prompt first (PE)
│   ├── Few-shot example (PE)
│   └── Still failing? → FT on multi-hop examples
├── 缺 style / format consistency?
│   ├── Try structured output schema (PE)
│   ├── Try detailed system prompt (PE)
│   └── Still inconsistent? → FT (SFT or DPO)
├── Cost 高?
│   ├── Smaller model + PE (Haiku 4.5)
│   ├── Distill big model → small via FT
│   ├── Cache responses (free 30-90% by hit rate)
│   └── Cascade routing (10x cost reduce)
└── Latency 高?
   ├── Smaller model
   ├── Skip RAG if knowledge fits prompt
   └── Quantize / speculative decode

何时 FT 经济?
├── Volume > 50k queries/day → FT 减小 model 经济
├── Style 一致性 across multi-language → FT
├── Per-tenant model 微差异 → LoRA per-tenant
└── < 10k/day OR knowledge frequent update → 不 FT
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: Decision Framework (6 dim)**
- 核心解法:
  ```
  Score 每个 dim 1-5:
    Freshness: 1 static → 5 hourly
    Knowledge size: 1 small → 5 huge
    Customization: 1 same all → 5 per-tenant
    Quality bar: 1 > 80% OK → 5 must > 95%
    Latency budget: 1 < 100ms → 5 > 5s OK
    Cost: 1 cheap → 5 expensive OK
  
  Rule of thumb:
    Score high freshness + size + customization → RAG
    Score high quality + latency tight + cost tight + style → FT
    All else → PE first
  ```
- Top 3 gotchas: 一个 dim 决定 (实际多 conflict) / 没量化 score / 没考虑 staffing 维度
- Tools/tactics: decision matrix excel, eval cost calculator

**Problem 2: RAG Deep Dive (Hybrid Retrieval, Rerank, Eval)**
- 核心解法:
  ```python
  # Hybrid retrieval
  dense_results = vector_db.search(query_embedding, top_k=100)
  sparse_results = elasticsearch.search(query, top_k=100)
  fused = reciprocal_rank_fusion(dense_results, sparse_results, k=60)
  
  # Rerank
  reranked = bge_reranker.rerank(query, fused[:50])
  top_chunks = reranked[:10]
  
  # Advanced: HyDE (Hypothetical Document Embedding)
  hypothetical = llm.complete(f"Write a paragraph answering: {query}")
  query_emb = embed(hypothetical)  # better retrieval
  
  # Multi-query
  variations = llm.complete(f"Rephrase 3 ways: {query}")
  all_results = [search(v) for v in variations] → dedup → rerank
  
  # Eval: recall@10, NDCG@10, faithfulness, hallucination
  faithfulness = llm_judge("Is answer grounded in context?")
  ```
- Top 3 gotchas: dense only 缺 ID match / 不 rerank / 没 faithfulness eval (hallucination 漏检)
- Tools/tactics: ragas, Cohere rerank-v3, bge-reranker-v2-m3, BEIR benchmark

**Problem 3: Fine-tuning Deep Dive (SFT / DPO / RLHF)**
- 核心解法:
  ```
  SFT (1k+ examples, $25k):
    (input, output) labeled data
    next-token prediction standard
    Mix 20% general data → prevent catastrophic forgetting
    LoRA + low LR safer
  
  DPO (1k+ preference pairs, $30k):
    (chosen, rejected) tuples
    No reward model needed
    Style learning easier than SFT for nuanced
  
  RLHF ($115k+, engineer-months):
    SFT base → reward model → PPO
    Anthropic / OpenAI use
    Best quality but complex pipeline
  
  Failure modes:
    Overfit on < 1k examples → augment or skip
    Catastrophic forgetting → mix general data
    Wrong hyperparams → LoRA + low LR
    Format inconsistency in train data → strict schema validate
  ```
- Top 3 gotchas: FT to inject facts (use RAG) / overfit < 1k / forget general (no mix)
- Tools/tactics: unsloth, axolotl, trl library, LoRA + QLoRA, DPO library

**Problem 4: Prompt Engineering Deep Dive**
- 核心解法:
  ```
  System prompt structure:
    Role + Constraints + Format + Examples
  
  Few-shot: 2-5 representative example (NOT 20+)
  
  CoT: "Think step by step:
    1. Identify intent
    2. Retrieve relevant policy
    3. Apply policy to user case
    4. Output JSON: {response, escalate}"
  
  Structured output (JSON schema):
    "Output strict JSON matching: {intent: string, ...}"
  
  Prompt caching (Anthropic 90% off, Gemini 75% off, OpenAI 50% off):
    System prompt + few-shot 一次缓存
    后续 1000 query 复用
  
  Self-consistency: sample N times → vote majority
  
  ReAct: Thought → Action (tool) → Observation → Thought → ... → Final
  ```
- Top 3 gotchas: prompt creep > 5k tokens (cost + quality drop) / few-shot 太多 (20+ overfits) / 没 schema enforce
- Tools/tactics: LangChain prompt template, pydantic schema, Anthropic prompt caching API

**Problem 5: Hybrid Approaches (Production Combinations)**
- 核心解法:
  ```
  BNPL chatbot (all 3):
    1. PE intent classify (Haiku 4.5, few-shot)
    2. RAG retrieve policy (Qdrant, hybrid)
    3. FT SFT Sonnet 4.6 multilingual response
    4. PE structured output (JSON enforce)
    5. Cascade: 90% Haiku, 9% Sonnet, 1% Opus 4.7
  
  Cost math @ 100k queries/day:
    PE only Opus 4.7: $150k/month
    + RAG: $180k/month (small overhead)
    FT Sonnet 4.6: $45k/month + $25k FT (payback < 1 month)
    Cascade: ~$25k/month (10x save)
  
  2026 long-context + RAG hybrid:
    Gemini 3 Pro 2M context $2/M input
    RAG narrows to top-50 (60K token)
    Long-context digests all 50 + reasoning
    $0.12 per query vs $20 brute force
  ```
- Top 3 gotchas: all-in one technique / 不 cascade (cost 10x 浪费) / 不 hybrid long-context + RAG
- Tools/tactics: LangGraph routing, intent classifier first, Anthropic/Gemini prompt caching

### 🔥 Production gotchas (top 15)

1. FT for facts → hallucinate variations, no citation
2. PE only when knowledge gap → 加 RAG
3. RAG only when reasoning gap → 加 PE CoT or FT multi-hop
4. FT on < 1k examples → overfit
5. FT to fix retrieval → separate problem, fix retrieval
6. Same model judges itself → self-preference bias
7. Skip eval baseline → 不知道 what works
8. Prompt creep > 5k tokens → cost + quality drop
9. Catastrophic forgetting (no general data mix) → FT 后 lose general
10. RAG dense only → 缺 ID match (e.g., "Q3 2024" 错过)
11. 不 rerank → top-K precision 低
12. 没 faithfulness eval → hallucination 漏检
13. PE only at 100k queries/day → $360k/year cost (不 FT 浪费)
14. Long-context vs RAG 一刀切 → hybrid 才 optimal
15. FT data 格式 inconsistent → schema validate strict

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| All-3 hybrid | BNPL chatbot | PE intent + RAG + FT response + cascade |
| Multilingual SFT | Voice agent | per-language style 6 lang FT |
| Cascade routing | Voice agent | Haiku 90% / Sonnet 9% / Opus 1% |
| RAG with metadata | Internal Agent Platform | per-team ACL + freshness |
| Eval ablation | ConvFinQA 9-variant | RAG vs PE vs hybrid 比较 |
| FT for cost-down | Voice agent at scale | Sonnet > 50k/day, FT payback < 1mo |
| PE first MVP | BNPL initial | PE-only 2 周, 后续加 RAG |
| Hybrid long-context + RAG | ConvFinQA 多跳 | retrieve + Claude Opus digest |
| DPO for style | Voice agent collection tone | preference pair 5k per market |

### 🎤 面试现场 quotables (top 8)

1. "PE changes input, RAG adds context, FT changes weights — 3 different tools for 3 different problems"
2. "Never FT to inject facts. RAG is the right tool — facts are discrete, FT learns probability distributions"
3. "Pragmatic order: PE week 1, RAG week 2-3, FT month 2+ only if plateau + volume justifies"
4. "FT becomes economic at 50k queries/day — payback often < 3 months on small fine-tuned model vs Opus 4.7"
5. "Cascade routing — Haiku 90%, Sonnet 9%, Opus 1% — 10x cost reduce without quality loss"
6. "2026 long-context didn't kill RAG. Gemini 3 Pro 2M context is $20/query brute force, RAG hybrid is $0.12/query"
7. "FT on < 1k examples overfits — augment or skip. SFT needs 1k+, DPO needs 1k+ preference pairs"
8. "BNPL chatbot — all 3 stacked: PE intent classify, RAG policy retrieve, FT multilingual response, PE schema enforce, cascade route"

### 🚨 红线 (top 10 anti-patterns)

1. FT for facts
2. PE only when knowledge gap
3. RAG only when reasoning gap
4. FT on < 1k examples
5. FT to fix retrieval
6. Same model judges itself
7. Skip eval baseline
8. Prompt creep > 5k tokens
9. Catastrophic forgetting (no general mix)
10. Long-context vs RAG 一刀切

