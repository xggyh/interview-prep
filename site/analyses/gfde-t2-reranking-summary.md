# 🎯 T2.5 · Reranking (何时加 / 用什么 / 怎么 cache) — 冲刺版

> 完整版: [gfde-t2-reranking.html](gfde-t2-reranking.html). 这页是 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: first-stage recall@50 = 92% (hybrid BM25 + dense + RRF), latency 500ms budget, top-3 accuracy core target, 100 QPS, multilingual technical doc, citation required, $0.01/q cost ceiling."

**5-layer reranking pipeline**:

### Layer 1: Why reranker (bi vs cross encoder 数学)

```
Bi-encoder: E_q = T(q), E_d = T(d), score = cos(E_q, E_d)
  - Independent forward, doc pre-index OK, ANN scale 1B docs
  - 没 cross-attention → 看不见 query-doc 细粒度对齐
  - 'iPhone 15 Pro Max' 和 'iPhone 12' 压到同 '高端手机' 簇

Cross-encoder: input = [CLS] q [SEP] d [SEP], score = Linear(CLS_repr)
  - Joint forward, cross-attention 矩阵 (n+m)²
  - q-d block 让 'Pro Max' token 和 doc 'Pro Max' token 对齐
  - Per-query inference, 不能 pre-index, 必须 narrow first
```

### Layer 2: Cascade design (cheap → expensive)

```
Stage 0: Query understanding (Gemini 3 Flash, 50ms)
Stage 1: Hybrid first-stage parallel BM25 + dense → top-100 (50ms)
Stage 1.5: RRF fusion k=60 → top-100 (5ms)
Stage 2a: bge-reranker-v2-base (A10G FP16 batch 100) → top-25 (80ms)
Stage 2b: bge-reranker-v2-m3 / Cohere rerank-3 / Vertex AI Ranker → top-10 (200ms)
Stage 2c (optional): LLM-judge Gemini 3 Pro listwise → top-3 (3-5s, high-stake only)
Total typical: ~330ms within 500ms budget
```

每层 candidates 数减半到 1/4, 模型 cost 加 2-5x.

### Layer 3: Reranker options (2026)

| Reranker | Deploy | Latency (50 docs A10G) | Cost | Quality | 何时 |
|---|---|---|---|---|---|
| bge-reranker-v2-m3 | Self-host | 80-150ms | Free + GPU | Good multilingual ⭐ | Default open-source |
| bge-reranker-v2-large | Self-host | 200-400ms | Free | Better EN | English mono |
| Cohere rerank-3 | API | 150-250ms | $1/1K | Excellent | 不想自部署 GPU |
| Vertex AI Ranker | Managed (GCP) | ~200ms | Pay-per-use | Excellent | GCP-native, no GPU |
| mxbai-rerank-large-v1 | Self-host | 250-400ms | Free | Excellent | Open Cohere-class |
| LLM-judge (Gemini 3 Pro) | API | 5-10s | $0.10-0.30/q | Best | Top-3 high-stake only |
| Domain-finetune bge | Self-host | 100-300ms | $50-100 train | Best in domain | 1K+ labeled pair |

### Layer 4: Latency engineering

- **FP16 vs FP32**: 2x speedup, <0.1% NDCG drop (default)
- **INT8 + TensorRT**: 3-5x more, 0.5-1% NDCG drop
- **Batching 32-64**: GPU util 30→85%, throughput 3x (micro-batch wait 50ms cross queries)
- **Distillation**: large 568M → 30M student, 5x speed at 80% teacher quality
- **Triton/vLLM** inference server (not raw Python serve)
- **Caching** Redis 1h TTL on (query, candidate_ids hash): FAQ-heavy workload 30-40% hit

### Layer 5: Eval + domain finetune

- **NDCG@k 核心** (not recall — reranker 不改 set 只改 ordering)
- **MRR** (first-relevant rank)
- **Recall stays same** (sanity check — 若 reranker 把 relevant 踢出 top-k 是 bug)
- **Slice eval**: short / long / has_acronym / multilingual / doc_length
- **Domain finetune**: 1K production click + 5K LLM-synth + hard-neg mining, bge-base + LoRA 1 GPU-day = +3-8pp NDCG

### Edge cases (背 5 个)

- **EC1 Reranker 跑 top-1000**: 200ms × 1000 = 200s 爆 → cascade first-stage narrow 到 top-50/100, cross-encoder 必须二阶段, 不能 scale 1M docs (no pre-index possible).
- **EC2 Bi-encoder used for reranking**: 没 cross-attention 与 first-stage 同质 redundant → 必 cross-encoder (joint [CLS] q [SEP] d forward).
- **EC3 LLM-as-judge mass deploy**: 1M query × $0.30 = $300K/day 不可持续 + 5-15s latency 杀 UX + judgment 随 run drift → 仅 top-3 final pass for high-stake (legal/medical/financial); 或 listwise 一次 10 个 $0.02 vs pairwise 45 调用 $0.22.
- **EC4 Length bias**: reranker 偏长 doc → slice eval by doc length 4 quartile; length normalization `score / f(doc_length)`; 多 reranker per-slice 比较, 找 best by slice; calibration test (synthesize known-rel short docs verify).
- **EC5 6 个月 NDCG 不动**: eval drift (refresh quarterly), data 加 production feedback, hard-neg from analysis of failures (top-ranked-but-wrong), newer model (bge v2→v3, mxbai-large), domain coverage gap targeted improvement, multi-task (relevance + freshness + diversity).

### Production hardening (1 min)

- **GPU monitoring**: util >90% scale up, queue depth >100 backpressure
- **NDCG weekly regression**: drop >1pp vs last week alert
- **A/B in prod**: CTR top-3 / time-to-first-click / thumbs / latency multi-metric, t-test p<0.05
- **Continual learning**: weekly retrain on new clicks, A/B candidate vs current, promote if +0.5pp NDCG
- **Failure isolation**: reranker down → fallback to first-stage ordering (graceful degrade)
- **Caching layer**: (query, candidate_id sorted hash) Redis 1h TTL

### 🪝 Resume hook

"BNPL chatbot RAG 加 bge-reranker-v2-m3 在 top-50 → top-5 stage. NDCG@5 0.71 → 0.83. Latency +180ms (A10G GPU batched FP16), 内 1.5s budget. 单点最大胜利在 acronym query — bi-encoder 给 'phone' 当 query 是 'iPhone Pro' (Pro Max 不 generalize embedding 空间), reranker 通过 cross-attention 正确选 iPhone-specific doc. A/B 1 周, 用户 thumbs-up +12%, p<0.01. 后来 fine-tuned bge-reranker-base on 2K production click pairs + 5K LLM-synthesized + hard-negative mining, 6 GPU-hours, +4pp NDCG. Fine-tuned bge 匹配 Cohere quality at 1/10 inference cost (self-host vs API)."

---

## 🔥 5 Follow-ups (面试官会问)

**Q1: Reranker latency 太高 (1s), 需 <200ms total, 招?**
Cheaper model (bge-base 或 distilled small), fewer candidates (top-20 not 50), GPU + FP16 + INT8 + TensorRT 3-5x, distillation 5x speed 80% quality, no reranker invest better first-stage (HyDE + multi-query), Redis cache 1h hot queries, async fan-out stream first-stage to LLM while rerank background.

**Q2: LLM-judge 听起来最好, 为啥不全用?**
Cost: 50 candidates pair-rank ~$0.10-0.20/q Pro, $0.30-0.80/q Opus; 1M queries/day = $100K-500K/day. Latency 5-15s kill UX. Consistency: LLM judgment 随 run drift calibration 问题. Use case: top-3 final pass high-stake only ✓, 或 eval offline; mass deployment 太贵.

**Q3: Reranker 有 bias (favors longer docs), 怎么 detect?**
Slice eval by doc length quartile (NDCG by short/med/long); calibration test (synthesize known-rel short docs check still surface); diversity 在 eval set 跨 length distribution; compare multiple rerankers (best per-slice 可能不同); length normalization 公式 (score / f(doc_length)) 去 bias.

**Q4: Domain-specific (medical, legal), generic reranker 够吗?**
Finetune bge-base on 1K-10K labeled domain pairs + hard-negative mining (top-ranked-but-wrong as negatives) + synthetic LLM-generated (query-doc from corpus). Cost 1-2 GPU-day $50-100 one-time. Gain typical 3-8 pp NDCG. Alternative: specialized embedding (BiomedBERT) at first stage too.

**Q5: 6 个月 reranker 性能不动, 怎么提?**
Eval drift refresh quarterly (query distribution changes); 数据 add recent production user feedback; hard-neg from failure analysis ('almost-right' docs mis-ordered); newer model bge v2→v3 / mxbai-large / Cohere rerank-3 new version; domain coverage gap targeted improvement; multi-task train (relevance + freshness + diversity).

---

## ❌ 易错点 (10 条红线)

1. Bi-encoder used for reranking — no cross-attention, 与 first stage 同质
2. Rerank top-1000 — latency × 20, 10s+ 爆
3. No first-stage to narrow — cross-encoder 不能 scale 1M docs
4. No eval set, 'feels better' — silent regression
5. Single reranker for all domain — legal/code/medical 都用 generic
6. LLM-as-judge for everything — $100K/day cost blow
7. No cascade — pay expensive on every candidate
8. CPU 单条 forward — GPU batch FP16 是 3-5x 提升 (50 × 20ms = 1s vs batch 80ms)
9. No quantization — leave 50% perf 桌上
10. Forget recall stays same — focus NDCG / MRR not recall (reranker 不改 set)

---

## ✅ 加分项 (10 条)

1. **Bi vs cross encoder 数学** explanation with attention 矩阵视角
2. **Cascade design** (cheap → expensive → optional LLM-judge top-3)
3. **Per-domain finetuning** workflow (production click + LLM-synth + hard-neg + LoRA)
4. **GPU batch FP16 + TensorRT INT8** for latency engineering
5. **NDCG / MRR > recall** for reranker eval (recall stays same)
6. **A/B framework** multi-metric (CTR / time / thumbs / latency / p99)
7. **LLM-as-judge as final pass** for high-stake only (listwise cheap, pairwise expensive but accurate)
8. **Hard-negative mining** from production failures
9. **Continual learning** weekly retrain + auto-promote on +0.5pp NDCG
10. Quote BNPL bge-reranker-v2-m3 0.71→0.83 NDCG + 12% thumbs

---

## 一句话总结

Reranker = **「cross-encoder 看 (q,d) joint, cross-attention 抓细粒度匹配, 必须 cascade 限 candidate 数, GPU batch + FP16 + TensorRT 上线, NDCG 是核心指标, domain finetune + hard-neg 持续提升」**. 不是 "加 reranker 就完事", 是 **cascade + latency engineering + eval + finetune** 的工程系统.

---

## 🃏 Cheat Sheet (印 1 页随身)

```
Bi vs Cross encoder:
  Bi:    E_q, E_d independent, cos score, fast ms, scale 1B, pre-index OK
  Cross: [CLS] q [SEP] d joint, cross-attn (n+m)², 50-200ms/pair, top-50 max
  Attention matrix 4 blocks: [q-q|q-d;d-q|d-d], q-d block 是关键

Reranker options (2026):
  bge-reranker-v2-m3      free, multilingual, A10G FP16 150ms ⭐ default
  bge-reranker-v2-large   free, EN mono, 300ms
  Cohere rerank-3         $1/1K, ~200ms API
  Vertex AI Ranker        managed GCP, pay-per-use ⭐ GCP-first
  mxbai-rerank-large-v1   open Cohere-class
  LLM-judge (Pro/Opus)    high-stake top-3 only, $$$
  Domain-finetune bge     1-2 GPU-day, +3-8pp NDCG

Cascade (production default):
  Hybrid first-stage → top-100 (50ms parallel BM25 + dense)
  bge-base → top-25 (80ms)
  bge-large / Cohere / Vertex Ranker → top-10 (200ms)
  LLM-judge → top-3 (optional, 3-5s, high-stake only)

Latency optimization:
  FP16 2x, <0.1% NDCG drop
  INT8 + TensorRT 3-5x, 0.5-1% drop
  Batching 32-64 throughput 3x (GPU util 30→85%)
  Distillation large→small 5x speed 80% quality
  Micro-batch across queries (wait 50ms, batch 32)
  Caching (query, candidate_ids) Redis 1h TTL

Eval metrics:
  NDCG@k 核心 (position-aware, reranker target)
  MRR first-relevant rank
  Recall stays same (set unchanged) — sanity check only
  Slice: short/long/acronym/SKU/multilingual/doc_len

A/B prod: CTR top-3/top-1, time-to-first-click, thumbs, p99 latency, t-test p<0.05, 1-2 weeks

Domain finetune:
  Data: production click + 5x LLM synthetic
  Hard-neg: top-ranked-but-not-clicked
  Train: bge-base + LoRA, 1-2 GPU-day, $50-100
  Gain: +3-8pp NDCG, continual weekly auto-promote if +0.5pp

LLM-judge modes (10 candidates):
  Pointwise:  $0.05 Pro / $0.15 Opus, 8-12s
  Pairwise:   $0.22 / $0.65, 30-50s (most accurate)
  Listwise:   $0.02 / $0.06, 3-5s ⭐ economic

GCP stack (2026):
  Vertex AI Ranker (managed cross-encoder, no GPU mgmt)
  Vertex AI Endpoints (self-host bge on A10G/A100)
  Triton/vLLM | Cloud Trace | Cloud Monitoring
  AWS: SageMaker / Vertex AI Reranker / Kendra

Decision when to use:
  QPS<10 generic       → Cohere rerank-3 API
  QPS 10-100           → bge-reranker-v2-m3 self-host A10G
  QPS>100 <200ms       → bge-base + INT8/TensorRT
  Multilingual          → bge-reranker-v2-m3 ⭐
  Domain (legal/code)  → Finetune bge-base
  High-stake top-3     → Cascade + LLM-judge final
  Quality max          → LLM-judge pointwise Opus 4.7

红线:
  - Bi for reranking (no x-attn)
  - Top-1000 cross-encode
  - No first stage narrow
  - No eval
  - LLM-judge mass deploy
  - No cascade
  - CPU forward
  - No quantization
  - Single reranker all domain
  - Forget recall stays same
```
