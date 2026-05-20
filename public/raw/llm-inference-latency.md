## 题目（verbatim）

> **[OpenAI Technical Screen]**
>
> "How would you **diagnose high latency in an LLM inference pipeline** in production?"

**出处**：OpenAI FDE 真题, Google FDE (Vertex AI inference) 必问.

**Round**：Technical Screen (60 min)

---

## 这道题在考什么

考你**LLM serving production 经验**：

1. **Inference pipeline 各阶段** —— 知道哪些 component 在 critical path
2. **常见 bottleneck pattern** —— TTFT vs throughput 区分
3. **vLLM / SGLang / TensorRT 优化点** —— 知不知道
4. **Cold start vs steady state**
5. **Diagnosis order** —— cheapest first

---

## LLM inference pipeline 解剖

```
Request → API Gateway → Rate limiter → Auth
              ↓
        Token Service / OAuth
              ↓
        Pre-processing (prompt assembly, RAG retrieve)
              ↓
        Inference Engine (vLLM / SGLang / TensorRT)
              ↓ 
              ├── Tokenize input
              ├── Prefill (compute KV cache for prompt)
              ├── Decode (generate tokens, autoregressive)
              ├── Stream tokens back
              ↓
        Post-processing (parse JSON, validate, structured output)
              ↓
        Response to client
```

每段都可能是瓶颈, **每段 latency 量级不同**:

| Stage | Typical latency | Common pathology |
|---|---|---|
| Gateway / auth | < 5ms | Token Service 1 hop adds 5-50ms |
| RAG retrieve | 20-100ms | Vector DB cold start, network |
| Tokenize | 1-5ms | Big prompt, rare unicode |
| Prefill | 50-500ms | Long context, batch size, no KV cache hit |
| Decode | 10-30 tokens/s | Model size, sampling, batch contention |
| Post-process | < 10ms | Structured output (JSON schema enforce) |
| Network egress | < 5ms | Cross-region, TLS handshake |

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-3 min | Clarify which latency (TTFT? throughput? total?) |
| 3-10 min | Walk down 7-stage pipeline, where to add timing |
| 10-25 min | Common pathology patterns |
| 25-40 min | Tools for diagnosis (traces, profiles) |
| 40-60 min | Specific scenario deep dive |

---

## 必问 clarifying

**1. Which latency metric**

> "p50 / p99 / max? **Time-to-first-token (TTFT)** or **time-to-last-token (TTLT)** or total? Streaming or non-streaming?"

**2. New problem or recent regression**

> "Always slow, or got worse recently? If recent: deploy / config / traffic change?"

**3. All requests or specific**

> "Long prompts only? Specific user / tenant? Specific time of day?"

**4. Magnitude**

> "How much over expectation — 2x slower, 10x slower? Helps narrow."

**5. Existing observability**

> "Do we have per-stage timing? Trace spans? Or do I need to add instrumentation first?"

---

## 我会这样答（sample）

> "Clarify — *[假设: streaming use case, **TTFT (time-to-first-token) p99 jumped from 800ms to 3.5s** last week, only on **long prompt requests (>2k tokens)**, observability shows total time but no per-stage breakdown]*.
>
> Last week change + long prompt + TTFT → **strong hypothesis: prefill bottleneck**, but I'd still go systematic.
>
> **Step 1: Add per-stage timing first** (1h)
> Without breakdown, all diagnosis is guess. Instrument:
> - `gateway_start`, `auth_done`, `prompt_assembled`, `rag_retrieved`, `tokenized`, `prefill_done`, `first_token`, `last_token`, `response_sent`
> - Tag each span with `prompt_tokens`, `output_tokens`, `model_id`, `region`, `tenant_id`
>
> **Step 2: Look at where the 2.7s went** (1h)
> If it's prefill (KV cache compute on prompt): consistent with long prompt → **prefill bottleneck**
> If it's decode: not it (TTFT regression, not throughput)
> If it's RAG: pre-prompt step
>
> **Step 3: Common prefill bottleneck causes**:
>
> **A: Long prompt + small batch**
> Prefill compute scales O(N²) with prompt tokens. 2k → 4k prompt is 4x compute. Combined with low batch utilization → bad.
> **Fix**: enable **prefix caching** (vLLM, SGLang both support) — if many requests share prefix (e.g., system prompt), cache its KV.
>
> **B: KV cache eviction under load**
> If GPU memory full, KV from one request evicted, **prefill recomputes** on next access. Catastrophic.
> **Fix**: paged-attention (vLLM standard), increase GPU memory, or reduce max concurrent.
>
> **C: Batch size too small (low GPU utilization)**
> vLLM continuous batching: if traffic light, batches small, GPU underutilized but still N²
> **Fix**: chunked prefill — break long prefill into chunks that mix with decode in same step. SGLang 默认开.
>
> **D: Cold start / model not warm**
> First request after idle: weights paged from CPU to GPU, slow.
> **Fix**: keepalive / scheduled warm-up
>
> **E: Tensor parallelism overhead**
> If TP=4 (model split across 4 GPUs), cross-GPU comm adds latency.
> **Fix**: tune TP based on batch size; smaller batch → less TP benefit.
>
> **F: Tokenizer / preprocessing**
> Rare but real — unusual unicode, large vocabulary, slow tokenize.
>
> **G: Quantization mode mismatch**
> If runtime quantization (FP16 → INT8) is on but kernels are slow → unexpected lag
>
> **Step 4: After identifying, fix + measure** (4h)
>
> **For long-prompt regression specifically**:
> 1. Check vLLM version / config — was prefix caching disabled?
> 2. Check if max prompt length recently bumped (causing more requests to hit slow path)
> 3. Check GPU memory headroom — under load?
> 4. Test with **chunked prefill** enabled
>
> **Step 5: Tools I'd use**:
> - **NVIDIA Nsight Systems** for GPU profile (kernel-level breakdown)
> - **vLLM metrics endpoint** (request scheduler stats, batch sizes, GPU util)
> - **PyTorch Profiler** for ad-hoc CPU/GPU stage timing
> - **Distributed tracing** (Jaeger / OpenTelemetry) for cross-service
> - `nvidia-smi dmon -s u` for live GPU util
>
> **Step 6: Prevent recurrence**:
> - **TTFT SLO + alert** on regression
> - **Synthetic canary**: 100 standard prompts every 5 min, measure latency, alert on p99 deviation
> - **Per-deploy automated benchmark**: prefill / decode / total latency baseline before merge
>
> **What I'd skip on first pass**:
> - Hardware change (more GPUs) — expensive, fix software first
> - Model swap to smaller — quality regression risk"

---

## 简历专属 reframe

你的 **vLLM / SGLang post-training infra** + **voice agent latency**:

| 题 | 你做过 |
|---|---|
| LLM inference optimization | **你简历直接写 'vLLM, SGLang, memory-efficiency tuning'** |
| Streaming voice latency p99 < 800ms | Voice agent 你 own |
| KV cache management | Multi-turn voice agent 必处理 |
| GPU profiling | vLLM tuning 你做过 |

**主动说**:

> "I literally lived this in our voice agent. We hit a TTFT regression after upgrading vLLM 0.5 → 0.6 — turned out prefix caching default changed, our system prompt re-prefilled every request. Adding **explicit prefix cache hint + chunked prefill** brought TTFT from 1.2s back to 400ms. The pattern I'd recommend: **never assume your infra config is what you think — diff against the actual runtime config before each diagnosis**."

→ 这是你简历最强 match 的题, 一定 ace。

---

## 5 follow-ups

**Q1**: "GPU at 100% but latency is still high. What gives?"
**A**:
- 100% GPU util ≠ effective work. Could be memory copy / kernel launch overhead
- **Profile**: NVIDIA Nsight → check kernel-level. If `Memcpy` 占 30% → memory bound, not compute
- **vLLM stats**: check `gpu_cache_usage` — if > 95%, KV cache pressure causing eviction
- Could be **batch wait time** — requests waiting for batch fill, GPU not the bottleneck

**Q2**: "Smaller model latency similar to bigger model. Why?"
**A**:
- **Network / preprocessing** dominates if model compute is small
- **Batch overhead constant** regardless of model size
- **Decode speed** is memory-bandwidth-bound, smaller model marginal improvement
- Smaller model wins on **throughput** more than latency unless prompt is huge

**Q3**: "Customer reports 5x latency, but our metrics show p99 fine. Disconnect?"
**A**:
- Metrics likely miss **client-perceived** latency: TLS handshake, DNS, client-side parsing
- Add **client SDK timing**: time from user action → display
- **Mid-percentile drift**: p99 fine but p99.9 catastrophic → "they happen to land on the long-tail"
- **Streaming TTFT vs TTLT** mismatch: customer sees TTLT, we measure TTFT

**Q4**: "vLLM vs SGLang vs TensorRT — which for production?"
**A**:
- **vLLM**: most popular, broad model support, good ops tooling. Default choice.
- **SGLang**: faster (better chunked prefill, RadixAttention), but newer + smaller community
- **TensorRT-LLM**: highest throughput for NVIDIA, locked into NVIDIA stack, complex to operate
- For most: **vLLM**. For very high QPS / NVIDIA-only: TensorRT-LLM. For latency-sensitive multi-turn: try SGLang.

**Q5**: "Multi-region serving — how route?"
**A**:
- **Latency-based routing** (AWS Global Accelerator / GCP Premium Tier): user → closest region
- **Affinity routing** for multi-turn: same user → same region → reuse KV cache
- **Failover**: region failure → next closest, prewarm second-region cache
- **Cost optimization**: cheaper inference in US-East, route batch / async there

---

## ❌ 易错点

1. **No per-stage instrumentation first** — diagnosis by hypothesis
2. **Confuse TTFT vs TTLT vs throughput**
3. **Hardware fix first** (more GPUs) — expensive
4. **Don't know vLLM features** — prefix cache, chunked prefill, paged attention
5. **Skip GPU memory check** — KV cache pressure subtle
6. **Don't profile, just guess** — Nsight / vLLM metrics are free
7. **No SLO / canary** to prevent recurrence

---

## ✅ 加分项

1. **7-stage pipeline breakdown**
2. **Per-stage instrumentation first** before fix
3. **7 common prefill pathology** (A-G)
4. **Specific tools** (Nsight, vLLM metrics, OTel)
5. **Prefix caching** as standard
6. **Chunked prefill** technique
7. **Synthetic canary** for regression prevention
8. **Quote vLLM 0.5→0.6 upgrade experience**

---

## Cheat Sheet

```
LLM inference 7 stages:
  Gateway/auth (5ms)
  RAG retrieve (20-100ms)
  Tokenize (1-5ms)
  Prefill (50-500ms, O(N²))
  Decode (10-30 tok/s)
  Post-process (10ms)
  Network egress (5ms)

Metrics distinguish:
  TTFT (time to first token) — UX for streaming
  TTLT (time to last token) — total
  Throughput (tokens/s) — capacity

Common prefill bottleneck (A-G):
  A: Long prompt + small batch → prefix cache
  B: KV cache eviction → paged-attention + more mem
  C: Batch too small → chunked prefill
  D: Cold start → keepalive / warm
  E: TP overhead → tune TP per batch
  F: Tokenizer slow → rare
  G: Quantization mode → check config

Diagnosis order:
  1. Instrument per-stage (free, must do first)
  2. Identify regression stage from spans
  3. Check vLLM/SGLang config diff
  4. Check GPU memory + util
  5. Profile with Nsight
  6. Test fix on canary
  7. Add SLO + alert

Tools:
  - vLLM metrics endpoint
  - NVIDIA Nsight Systems
  - PyTorch Profiler
  - Jaeger / OpenTelemetry
  - nvidia-smi dmon -s u

Stack choice:
  vLLM default
  SGLang for low-latency multi-turn
  TensorRT-LLM for max throughput NVIDIA-only
```
