# 🧭 T2 · RAG / Context Management 全景 — 冲刺版

> 完整版: [gfde-t2-overview.html](gfde-t2-overview.html). 这页是 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: enterprise wiki 50M token, 多 doc 类型 (markdown + PDF + code), multi-tenant SaaS, daily update, citation required, latency budget 1.5s, QPS 100."

**4-layer 心智模型**:

### Layer 1: RAG ≠ "embed + vector DB"

2022 view = chunk → embed → cosine top-K. **2026 production RAG 是 7-step pipeline**:
Query understanding → Routing → Multi-source retrieval → Rerank → Context assembly → Generation with citations → Post-eval. 面试官 zoom-in 一步深挖, 不是问「什么是 RAG」.

### Layer 2: 6 sub-topic 全景图

```
T2.1 Hybrid Search       BM25 + Dense + RRF + Rerank (recall 60→90)
T2.2 Chunking Decision   按 doc 类型选 (5 strategy decision tree)
T2.3 Context Window Mgmt 4 strategy combine (sliding/summary/hierarchical/external)
T2.4 Tool Output→Prompt  6 件套 (format/truncate/mask/wrap/provenance/iterate)
T2.5 Reranking           Cross-encoder cascade (cheap→expensive→LLM-judge)
T2.6 Long-ctx vs RAG     Hybrid 是答案 (RAG narrow → long-ctx within)
```

### Layer 3: 5 retrieval method 定量对比 (Recall@10 BEIR avg)

| 方法 | Recall@10 | Latency | Cost | 何时用 |
|---|---|---|---|---|
| Dense (semantic) | 75-85% | 10ms | $$ | 语义为主 |
| BM25 (sparse) | 60-75% | 5ms | $ | exact match |
| Hybrid (RRF) | 82-90% | 12ms | $$ | ⭐ default |
| + Rerank | 90-97% | +60ms | $$$ | quality critical |
| ColBERT | 92-98% | 30ms | $$$$ | 极致精度 |

### Layer 4: 3 mental boundary

```
Knowledge boundary  → LLM cutoff 之后 / private data 必 retrieval
Context boundary    → 装得下也 retrieval (cost + lost-in-middle + 隔离)
Trust boundary      → retrieved 是 untrusted input (prompt injection)
```

### Edge cases (背 5 个)

- **EC1 Acronym/SKU 漏召回**: pure dense 把 "iPhone 15 Pro Max" 压到 "phone" 簇 → 必上 BM25 hybrid.
- **EC2 Multi-tenant 数据泄漏**: 跨 tenant index 检索 → metadata filter at retrieval time, NOT post-rank filter (会丢 top-k).
- **EC3 Lost-in-middle**: 长 context 中间 attention 弱 30-40% → 顺序 system→history→retrieved→query, 最相关放头尾.
- **EC4 Embedding drift**: 重 embed 后老 chunk 不一致 → versioned index + blue/green migration.
- **EC5 Stale cache**: doc 已更新但 RAG cache 30min TTL 未过期 → doc-version-aware cache key.

### Production hardening (1 min)

- **Monitor**: faithfulness score, citation completeness, per-slice recall (acronym/SKU/long/short), p99 latency per layer
- **Eval**: 200 human-label + 1000 LLM-synth, CI regression on chunker / reranker change, A/B 1-2 周 multi-metric
- **Cost math 必算**: 1k QPS A 划算, 100k QPS B 划算
- **2026 trends 主动 quote**: Contextual Retrieval (+35-49%), Late chunking, GraphRAG, prefix caching

### 🪝 Resume hook

"BNPL chatbot 7 国: 初版 pure dense recall 67%, 加 BM25 hybrid + RRF → 78%, 加 bge-reranker-v2-m3 → 88%, 加 Contextual Retrieval style 加 chunk + doc summary → 92%. ConvFinQA take-home 用 hybrid RAG + long-ctx-within: per-customer RAG → top-3 段落 → Claude 200k 处理 multi-hop, accuracy 84% at $0.30/q."

---

## 🔥 5 Follow-ups (面试官会问)

**Q1: 你怎么从 60% recall 提到 90%?**
5 层组合拳: Hybrid (BM25+dense+RRF) +12-18% → Query rewrite/multi-query +3-5% → HyDE +2-4% → Cross-encoder rerank +3-5% → 合计 88-92%. 每层独立 ablation 可量化.

**Q2: Long-context 出来后 RAG 还要不要?**
要. 2026 hybrid 是答案. Pure long-ctx 不可: corpus >2M 装不下; cost 爆 ($4/q at Pro >200K tier × 100k QPS = $400K/day); update 不能 partial reload; vendor lock-in (2M+ 只有 Gemini/Claude). Pure RAG miss multi-hop. **Hybrid**: RAG retrieves doc-level top-10 (500K total) → Gemini 3 Pro 2M 在 500K 内 multi-hop. 加 prefix cache 9 折.

**Q3: 你的 RAG cost math 怎么算?**
500k corpus 的 query: Pure long-ctx $1/q (Pro), 加 cache $0.10/q (10x), RAG (top-10 chunks ~5K) $0.011/q (100x). 1k QPS A 划算, 100k QPS B 显著. 必算 daily cost: pure long 100k × $4 = $400K/day 不可持续, RAG $50/day.

**Q4: 你为什么不直接用 vector DB 一招?**
Production RAG 是 7-step pipeline 不是 "vector DB". Query understanding (rewrite + multi-query + HyDE) +30%, retrieval routing (adaptive RAG skip simple query) -50% cost, fusion (RRF), rerank (cross-encoder), context assembly (token budget + lost-in-middle defense), citation, post-eval (faithfulness). 单 vector DB 拿不到分.

**Q5: 2026 你 follow 什么新趋势?**
**Contextual Retrieval** (Anthropic Sep 2024) — 每 chunk 加 doc-level summary 一起 embed, +35% recall, 配 rerank +49%. **Late chunking** (Jina v3) — 先 embed 整 doc 再切, intra-doc context 重的场景 +30-40%. **GraphRAG** (Microsoft) 关系型 query 强. **Self-RAG / Adaptive RAG** LLM 自决 retrieve. **Prompt caching** 90% off 改变 long-ctx 经济性.

---

## ❌ 易错点 (10 条红线)

1. 一开口「先 chunk embed 存 Chroma cosine top-K」— 2022 view, 拿不到分
2. Pure dense everywhere — Acronym / SKU / error code 全 miss
3. "Long-context killed RAG" 信念 — 大 corpus 装不下, cost 爆
4. Reranker 跑 top-1000 — latency × 20 爆
5. 没 perms filter at retrieval time → 跨租户泄漏 = SaaS 死刑
6. Post-rank filter 而不是 retrieval-time → 丢 top-k 大部分
7. 一刀切 chunk_size 512 — 不同 source-type 应不同策略
8. 没 eval set 凭 feel 调 — 三个月后没人知道好坏
9. Lost-in-middle 不防 — critical info 埋中间被忽视
10. 不算 cost math — FDE 必考

---

## ✅ 加分项 (13 条)

1. 主动画 7-step pipeline 图 (query understanding → routing → multi-retrieve → rerank → assembly → gen → eval)
2. 3 mental boundary (knowledge/context/trust)
3. 5 retrieval method 定量对比 (Recall@10 + latency + cost 表)
4. RRF 公式 score = Σ 1/(k+rank), k=60 paper 推荐
5. Adaptive RAG: 30-50% query 实际不需 retrieval
6. Hybrid + RRF + cross-encoder cascade
7. Lost-in-middle 顺序优化 + 关键 info 头尾放
8. Cost math 显式: 1k vs 100k QPS 决策不同
9. Prefix caching 经济学 (Anthropic 5min / Gemini 1h, 90% off)
10. Contextual Retrieval (Anthropic) +35-49% 主动 quote
11. Late chunking (Jina v3) +30-40%
12. Per-slice eval (acronym/SKU/multilingual/long-doc) 独立 metric
13. BNPL 7 国 67→88 recall + ConvFinQA hybrid 84% acc 实战 story

---

## 一句话总结

RAG = **7-step pipeline (query understanding → routing → multi-source retrieve → rerank → assembly → cite → eval)**, 不是 vector DB. 2026 production default = **Hybrid (RAG narrow + long-ctx within) + prefix cache + per-slice eval + cost math**, 6 sub-topic (hybrid search / chunking / context mgmt / tool output / reranking / long-ctx vs RAG) 各自独立深挖.

---

## 🃏 Cheat Sheet (印 1 页随身)

```
RAG 7-step pipeline:
  1. Query understanding   (rewrite + multi-query + HyDE + decompose)
  2. Retrieval routing      (skip simple, SQL for structured)
  3. Multi-source retrieve  (dense + sparse + graph + tool, parallel)
  4. Rerank & fusion        (RRF + cross-encoder cascade)
  5. Context assembly       (token budget + lost-in-middle defense)
  6. Generation w/ citations
  7. Post-eval & feedback   (faithfulness score)

6 sub-topics:
  T2.1 Hybrid Search        BM25 + Dense + RRF + Rerank, recall 60→90
  T2.2 Chunking Decision    5 strategy decision tree by doc type
  T2.3 Context Window Mgmt  4 strategy combine (sliding/summary/hier/ext)
  T2.4 Tool Output→Prompt   6 件套 (format/truncate/mask/wrap/prov/iter)
  T2.5 Reranking            Cross-encoder cascade + GPU FP16 + finetune
  T2.6 Long-ctx vs RAG      Hybrid is the answer + cost math

5 retrieval methods (Recall@10 BEIR avg):
  Dense:              75-85% | 10ms  | $$
  BM25:               60-75% |  5ms  | $
  Hybrid (RRF):       82-90% | 12ms  | $$  ⭐ default
  +Rerank:            90-97% | +60ms | $$$ ⭐ quality
  ColBERT:            92-98% | 30ms  | $$$$

5 chunking strategies (decision tree):
  Fixed-token         prototype only, baseline
  Recursive (default) prose, 512 token + 64 overlap
  Doc-structure aware markdown/PDF with headers
  Late chunking       2026 hot, +30-40% (Jina v3 / Cohere v4)
  AST-based           code (tree-sitter, function-level)

Context mgmt (4 strategies, combine):
  Sliding window      last 10 turn verbatim
  Hierarchical        4 tier (ancient/mid/recent/latest)
  External memory     blob (>1K out) + Qdrant (episodic) + Postgres (decisions)
  Selective pruning   importance score + pinned

Cost (2026):
  Gemini 3 Pro      $2 (≤200K) / $4 (>200K) / $12 out
  Gemini 3 Flash    $0.50 / $3
  Claude Opus 4.7   $5 / $25 (200K max)
  GPT-5.5           $5 / $30 (256K max)
  Cache hit         ~10% of normal input

Decision: corpus → architecture
  <200K static                 → Pure long-ctx + cache
  <2M multi-hop                → Pure long-ctx
  Multi-hop heavy + large      → Hybrid (RAG doc-level + long-ctx within)
  Real-time / huge / cost      → Pure RAG
  Default                      → RAG narrow → long-ctx

Multi-tenant perms:
  Filter at retrieval time (Qdrant query_filter / Vertex Vector Search)
  NEVER post-rank (loses top-k)
  Per-tenant index 或 metadata filter 强制

2026 hot trends (FDE 加分):
  Contextual Retrieval (Anthropic): +35% recall, +49% w/ rerank ⭐⭐
  Late chunking (Jina v3 / Cohere v4): intra-doc context
  GraphRAG (Microsoft): relational queries
  Self-RAG / Adaptive RAG: LLM 自决
  Prompt caching: 90% off cached input

GCP-first stack (2026):
  Vertex AI Vector Search       (向量库)
  Vertex AI Embeddings          (text-embedding-005)
  Vertex AI Ranker              (managed rerank)
  Document AI                   (PDF parse + table extract)
  Cloud DLP                     (PII detect/mask)
  Cloud Storage                 (blob tier)
  BigQuery                      (analytics + RAG-on-warehouse)
  Pub/Sub                       (delta reindex queue)
  VPC Service Controls          (multi-tenant isolation)
  AWS comparison: OpenSearch / Kendra / Bedrock KB

45-min rhythm:
  0-5    Clarify (corpus, doc type, tenancy, fresh, SLA)
  5-10   7-step mental model 画图
  10-25  Deep-dive 1 sub-topic + pattern
  25-35  Cost math (1k vs 100k QPS)
  35-42  2026 trends (Contextual Retrieval ⭐)
  42-45  Resume quote (BNPL / ConvFinQA / Voice agent)

红线:
  - "RAG = embed + vector DB" (2022)
  - "Long-context killed RAG"
  - Pure dense for keyword/SKU
  - Reranker on top-1000
  - No cost math
  - No perms filter / post-rank filter
  - One chunk_size 通吃
```
