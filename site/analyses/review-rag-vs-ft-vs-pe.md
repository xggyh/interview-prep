## AI Deep Dive #4 · RAG vs FT vs PE — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/rag-vs-ft-vs-pe.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`rag-vs-ft-vs-pe.html`](questions/rag-vs-ft-vs-pe.html)

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
