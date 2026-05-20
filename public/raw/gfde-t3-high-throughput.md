## 题目

> "Customer wants to serve a fine-tuned LLM at **1M QPS**, p99 latency < 1s. Walk through your **serving stack**: hardware, software, optimizations."

或追问形态:

> "Why is vLLM faster than naive transformer serving? Walk through PagedAttention + continuous batching."

**Round**: LLM Infra / Serving (60 min)

---

## 这道题在考什么

考你**LLM serving infra**:

1. **Continuous batching** —— vLLM 核心
2. **PagedAttention** —— KV cache 管理
3. **Prefix caching** —— shared prompt 优化
4. **Speculative decoding** —— 小 model + 大 model
5. **Parallelism** —— TP / PP / data parallel
6. **Production stack** —— Triton / vLLM / SGLang / TensorRT

这是你简历明确有的领域 ("vLLM, SGLang, Megatron, DeepSpeed").

---

## 必问 clarifying

**1. Model size**

> "7B / 70B / 400B params? Determines GPU class + parallelism."

**2. Request profile**

> "Avg input + output tokens? Burst / steady?"

**3. SLA**

> "p99 < 1s — for TTFT (time to first token) or full response?"

**4. Cost target**

> "$ per 1K tokens you can charge / spend?"

**5. Hardware available**

> "H100s / A100s / TPUs / mixed? Cloud / on-prem?"

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify model / load / SLA / hardware |
| 5-15 min | Hardware + parallelism plan |
| 15-25 min | vLLM internals (batching + PagedAttention) |
| 25-35 min | Optimizations (prefix cache / spec decode / quantization) |
| 35-45 min | Routing / autoscaling / observability |
| 45-60 min | Cost math + failover |

---

## 我会这样答（sample）

> "Clarify — *[假设: 70B model, avg in/out 500/200 tokens, p99 < 1s for full response, $0.001/1K tokens target, H100 80GB available]*.
>
> **1M QPS at 70B is non-trivial**: 1M QPS × 700 tokens/req = 700M tokens/sec. At 100 tokens/sec/GPU baseline = 7M GPUs naively. So we need **batching + concurrency tricks** for orders-of-magnitude speedup.
>
> **Hardware + parallelism plan**:
>
> 70B in FP16 = 140GB → must split across GPUs.
>
> ```
> Tensor Parallelism (TP=8): model split column-wise across 8 GPUs
> Per-replica: 8 × H100 80GB
> 1 replica throughput: ~3-5K tokens/sec output (with batching)
> For 700M tokens/sec → need ~150K-200K replicas → ~1.5M GPUs
> ```
>
> Realistic numbers say no single deployment hits 1M QPS for 70B. So:
> - Distill / cascade: cheaper model handles 90%, escalate to 70B for hard
> - Or scale horizontally with router
>
> **vLLM internals** (核心):
>
> **Continuous batching**:
>
> Naive batching: collect N requests, pad to longest, process. Wastes compute on padding + delayed requests.
>
> vLLM continuous batching: at each step (one token generation), **independently scheduled per request**. New request joins running batch; completed exits. No padding waste.
>
> ```
> Time T0: batch = [req_A (gen tok 5), req_B (gen tok 12)]
> Time T1: req_C arrives, batch = [req_A (tok 6), req_B (tok 13), req_C (prefill)]
> Time T2: req_B done, req_D arrives, batch = [req_A (tok 7), req_C (gen tok 1), req_D (prefill)]
> ```
>
> Throughput: 5-10x naive batching.
>
> **PagedAttention**:
>
> KV cache for transformer can be huge (multi-GB per request). Naive: pre-allocate max possible per request → wasteful.
>
> vLLM PagedAttention: store KV cache in **pages** (like OS virtual memory). 
> - Each request has page table mapping logical → physical pages
> - Pages allocated on-demand, freed when request done
> - Multiple requests share unused page space
>
> Result: 24x more concurrent requests fit in GPU memory.
>
> **Prefix caching**:
>
> Common scenario: many requests share prefix (system prompt, RAG context).
>
> ```
> Req A: [system prompt] [RAG: doc-X] [user query 1]
> Req B: [system prompt] [RAG: doc-X] [user query 2]
> Shared prefix: [system prompt] [RAG: doc-X]
> ```
>
> Compute KV for prefix once, reuse across requests. Saves prefill compute.
>
> Gains: 2-3x for FAQ workloads (lots of repeated prefix).
>
> **Speculative decoding**:
>
> Small draft model proposes N tokens fast, big model verifies in parallel.
>
> ```python
> # Draft: 7B model proposes [tok_a, tok_b, tok_c, tok_d]
> # Big: 70B model evaluates all 4 in parallel
> # Accept until first divergence
> ```
>
> If acceptance rate 70%, get ~2-3x latency reduction. Best for latency-sensitive.
>
> **Quantization**:
>
> FP16 → INT8 / FP8 / INT4. 70B FP16 (140GB) → INT4 (35GB). Less GPUs needed, faster ops.
>
> Quality cost: 1-3% on benchmark. Production: usually OK.
>
> Tools: **GPTQ, AWQ, FP8 (H100 native)**.
>
> **Stack choice**:
>
> | Component | Choice | Why |
> |---|---|---|
> | Serving engine | **vLLM 0.6+** | Continuous batch + paged attn + prefix cache built-in |
> | Or **SGLang** | Better for structured output / multi-LoRA |
> | Lower-level | **TensorRT-LLM** | Best raw throughput, more setup |
> | Frontend | **Triton Inference Server** | Multi-model deployment |
> | Routing | Custom or **Envoy + custom filter** | Tenant / model routing |
>
> **Routing layer**:
>
> ```python
> def route(request):
>     model = decide_model(request)  # complexity-based routing
>     replica = least_loaded_replica(model)
>     return replica.handle(request)
> ```
>
> Cost-aware routing: cheap model first, escalate.
>
> **Autoscaling**:
>
> Predict load 5-15 min ahead (time-of-day patterns), pre-warm GPUs. Cold start of LLM serving is **slow** (load weights 1-5 min).
>
> Strategies:
> - **Pre-allocated buffer**: 20% extra capacity always running
> - **Burst absorber**: queue with timeout, cheap model spillover
> - **Graceful degradation**: reduce quality (smaller model) under load
>
> **Observability**:
>
> | Metric | Why |
> |---|---|
> | TTFT (time-to-first-token) | User-perceived latency |
> | TPOT (time-per-output-token) | Throughput per request |
> | Batch size avg / max | Utilization |
> | KV cache utilization | Memory pressure |
> | Token cost per request | Economics |
> | Queue depth | Backpressure signal |
> | Eval pass rate (sampled) | Quality drift |
>
> **Cost math**:
>
> H100 ~ $3-4/hour, 5K tokens/sec per replica = 18M tokens/hour = $0.0002/1K tokens raw compute.
> Plus: prefix-cache hit gains, batching efficiency.
> Achievable: $0.001-0.002 / 1K tokens with optimization.
>
> **Failover**:
>
> - Per-replica health check (heartbeat)
> - Inflight requests on failed replica → retry on healthy
> - KV cache lost on failover; LLM redoes prefill (acceptable, < 1s usually)
>
> **What NOT to do**:
> - Naive batching (no continuous)
> - Pre-allocate KV per request (use PagedAttention)
> - Spawn replica per request (use multi-tenant)
> - Skip prefix caching for FAQ-like workloads
> - Ignore quantization (50% cost savings free)"

---

## 简历专属 reframe

| 题 | 你做过 |
|---|---|
| vLLM / SGLang | 你简历明列 |
| Megatron / DeepSpeed | 你简历明列 — TP/PP 你 know |
| GPU-accelerated inference | 你简历明列 |
| Cost optimization | TikTok payment infra scale |
| Multi-tenant routing | Voice agent 7 markets |

**Quote**:

> "I worked on vLLM + SGLang serving stack for a 70B fine-tuned model. Continuous batching alone got us 6x throughput over static batching. Adding **prefix caching** for our agent-loop (where system prompt is shared across all calls in a session) saved another 30% prefill compute. We used **TP=8 + speculative decoding** with 7B draft model — for latency-bound calls (voice agent), TTFT dropped from 800ms to 300ms. INT8 quantization let us fit 2 replicas where 1 fit before, near-zero quality loss on eval set."

---

## 5 follow-ups

**Q1**: "TTFT vs TPOT trade-off?"
**A**:
- **TTFT** matters for streaming UX (user starts seeing tokens)
- **TPOT** matters for total completion time
- vLLM optimizes both via batching
- Speculative decoding: TTFT slightly worse, TPOT better
- Per-use-case: chat priority TTFT, batch priority TPOT

**Q2**: "Multi-LoRA serving — many fine-tuned versions of base model. Approach?"
**A**:
- **S-LoRA / Punica**: serve many LoRA adapters on same base model
- Base model weights shared in GPU
- LoRA adapters small (~MB), hot-swap per request
- vLLM 0.6+ supports built-in
- Saves cost massively vs separate replicas per fine-tune

**Q3**: "Autoscaling for spikes — LLM cold start 1-5 min. How handle?"
**A**:
- **Pre-warm buffer**: always 20% extra running
- **Predictive scaling**: time-of-day patterns, pre-warm 10 min ahead
- **Burst spillover**: overflow to cheaper model / queue
- **Graceful degradation**: smaller model during spike

**Q4**: "vLLM vs SGLang vs TensorRT-LLM — when each?"
**A**:
- **vLLM**: most popular, best continuous batching, easy setup
- **SGLang**: structured output (JSON / regex), multi-LoRA, lang-level optimization
- **TensorRT-LLM**: max raw throughput, complex setup, NVIDIA-locked
- **Default**: vLLM unless need specific feature

**Q5**: "Eval quality drops mysteriously. Debug?"
**A**:
- **Quantization regression**: INT8 too aggressive on certain queries
- **Speculative decoding accept rate too low** → silent quality drop
- **Prefix cache corruption** rare bug
- Eval suite must include corner cases for these specific optims
- **A/B**: route 5% to baseline (no optims), compare quality

---

## ❌ 易错点

1. **Naive batching** — 5x throughput loss
2. **Pre-allocate KV per request** — use PagedAttention
3. **No prefix cache for FAQ workload** — leave 2-3x on table
4. **One GPU per replica** — for 70B impossible
5. **No quantization** — 50% extra cost
6. **No autoscaling pre-warm** — cold start kills burst
7. **No quality eval per optim** — silent regression

---

## ✅ 加分项

1. **Continuous batching mechanics** explained
2. **PagedAttention** with virtual-memory analogy
3. **Prefix caching** for shared prefix
4. **Speculative decoding** trade-off
5. **TP/PP** for big models
6. **Quantization** (INT8/INT4 + FP8 native H100)
7. **vLLM/SGLang/TensorRT-LLM** stack choice rationale
8. **TTFT vs TPOT** distinction
9. **Cost math** explicit
10. **Quote your vLLM+SGLang work**

---

## Cheat Sheet

```
6 levers for high throughput:
  1. Continuous batching (vLLM) — 5-10x naive
  2. PagedAttention — 24x more concurrent
  3. Prefix caching — 2-3x repeated prefix
  4. Speculative decoding — 2-3x latency
  5. Tensor parallelism — big model fit
  6. Quantization (INT8/INT4/FP8) — 50% memory

Stack:
  Engine: vLLM (default) / SGLang (structured) / TensorRT-LLM (max)
  Frontend: Triton
  Routing: Envoy + custom

Parallelism strategies:
  TP: split model across GPUs (column-wise)
  PP: split layers across GPUs (pipeline)
  DP: replicate model, split batch
  Combine for big models (70B+)

Latency optimization:
  Speculative decoding (small draft → big verify)
  KV cache reuse (prefix)
  FlashAttention v2/v3
  CUDA graphs

Throughput optimization:
  Continuous batching
  Larger batch sizes
  PagedAttention
  S-LoRA multi-tenancy

Quantization:
  INT8 — 1-2% quality cost
  INT4 — 2-5% quality cost
  FP8 — H100 native, near-FP16 quality
  Tools: GPTQ, AWQ, FP8

Routing:
  Cost-aware (cheap first, escalate)
  Least-loaded replica
  Tenant isolation
  Burst spillover

Autoscaling:
  Pre-warm 20% buffer
  Predictive (time-of-day)
  Burst absorber (queue + cheap model)
  Graceful degradation

Observability:
  TTFT / TPOT
  Batch size avg/max
  KV cache util
  Token cost / req
  Queue depth
  Eval quality (5% baseline A/B)

红线:
  - Naive batching
  - Pre-allocate KV
  - One GPU per req
  - No quantization
  - No autoscale
  - No quality eval per optim
```
