## 题目（verbatim）

> **[OpenAI Technical Screen]**
>
> "How would you **diagnose high latency in an LLM inference pipeline** in production? Walk through tools, methodology, common bottlenecks, and optimization levers."

**出处**: OpenAI FDE 真题. Google FDE (Vertex AI inference), Anthropic FDE, Databricks ML platform 都问.

**Round**: Technical Screen / Production Debug (60 min)

---

## 这道题在考什么

考你 **LLM serving production 经验** + **系统化 debugging 方法**:

1. **Inference pipeline 各阶段** — 知道哪些 component 在 critical path
2. **TTFT vs TPOT 区分** — 大多数 candidate 混淆
3. **vLLM / SGLang / TensorRT 优化点** — 知不知道 2026 主流工具
4. **GPU profiling skill** — Nsight, vLLM metrics, perf flame graph
5. **Multi-stage pipeline latency** — RAG retrieve + rerank + LLM + tool call
6. **Diagnosis order** — cheapest first, instrument before guess
7. **Cold start vs steady state**
8. **Prevention** — SLO + canary

不考「LLM 是什么」, 考「你 own 过一个 LLM 服务, 凌晨被 paging 起来 debug 过」.

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**TTFT (Time-To-First-Token)**: 从 request 发出到第一个 output token 出现的时间. **流式应用 (chat / voice) 用户感知最强**. 包含: 网络 + auth + RAG retrieve + tokenize + prefill.

**TPOT (Time-Per-Output-Token)** / **ITL (Inter-Token Latency)**: 生成第 N+1 个 token 相对第 N 个的间隔. 决定流式输出的「流畅度」. 典型 10-30 tokens/s.

**TTLT (Time-To-Last-Token)** = TTFT + (output_tokens × TPOT). 总响应时间.

**Prefill** vs **Decode**: LLM 推理两阶段.
- **Prefill**: 把 prompt 一次性 forward, 算出每个 token 的 KV cache. **compute-bound, O(N²)** with prompt length.
- **Decode**: 自回归生成 output token, 一次一个 token. **memory-bandwidth-bound**, 每个 token 都要读完整 model weights.

```
Prefill (1 forward, batch over prompt tokens):
  Prompt: "What is the refund policy?" (10 tokens)
  → GPU computes K, V for all 10 tokens in parallel
  → KV cache: 10 × N_layers × hidden_dim stored

Decode (N forwards, 1 token each):
  Step 1: generate "Refunds"  ← reads all weights + reads KV cache + writes new KV
  Step 2: generate " are"     ← reads all weights + reads bigger KV cache
  Step 3: generate " processed" ...
  → 每个 step ~30ms (model size depending)
```

**Continuous batching**: vLLM / SGLang 的核心创新. 不是等满 batch 才发送, 而是 prefill + decode 阶段动态混合多个 request, GPU 利用率拉满.

**PagedAttention**: vLLM 把 KV cache 分页存储, 像 OS 虚拟内存, 避免碎片化. KV cache 使用效率 90%+ vs 静态 batching 40%.

**Prefix caching**: 不同请求共享相同 prefix (e.g., system prompt) 时, 复用已计算的 KV. 系统 prompt 长 + 重复时, 节省 50-90% prefill 时间.

---

## 2. 这个问题的核心是什么

设想 **没有任何 observability + 没有优化** 的 inference 灾难场景:

```
9:00am 周一:  PM:    "用户抱怨 chat 卡顿"
                    │
                    ▼
你:           "卡多久?"
PM:           "不知道, 用户截图"
                    │
                    ▼
你:           "我看 dashboard"
Grafana:     【显示 1 个 metric: "request latency p99"】
你:           "950ms, 比 baseline 400ms 高 2x"
                    │
                    ▼
你:           "哪个阶段慢了?"
Grafana:     【没 per-stage breakdown】
你:           😱

你 ssh GPU 机器:
  nvidia-smi:    99% util
  vLLM logs:     "request received" → "response sent"
                 中间没 timing
你:           "好的, 我猜一下..."
```

**这就是 production debug 灾难**: 没数据, 全靠猜, 改一通, 不知道改对没.

**Reliable diagnosis 的解法**:

```
Step 1: Per-stage instrumentation (OTel spans)
Step 2: Look at where time went
Step 3: Identify bottleneck pattern
Step 4: Apply 对应 optimization
Step 5: Verify with same trace
Step 6: Add regression test + SLO
```

---

## 3. LLM Inference Pipeline 解剖图

```
┌──────────────────────────────────────────────────────────────────────┐
│                          User Request                                  │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                          ┌────────────────┐
                          │ Load Balancer  │  ~ 1ms
                          │ (region route) │
                          └────────────────┘
                                  │
                                  ▼
                          ┌────────────────┐
                          │ API Gateway    │  ~ 2-5ms
                          │ Rate limit     │
                          │ Auth (OAuth)   │
                          └────────────────┘
                                  │
                                  ▼
                          ┌────────────────┐
                          │ Token Service  │  ~ 5-50ms (network hop)
                          │ (validate)     │
                          └────────────────┘
                                  │
                                  ▼
                          ┌────────────────┐
                          │ App Layer:     │
                          │ Prompt build   │  ~ 1ms
                          │ + RAG retrieve │  ~ 20-100ms ← 经常 bottleneck
                          │ + Rerank top-K │  ~ 50-200ms
                          │ + Tool call    │  ~ 100-500ms (external API)
                          └────────────────┘
                                  │
                                  ▼
                          ┌────────────────┐
                          │ Inference Eng. │
                          │ (vLLM/SGLang)  │
                          │                │
                          │  Tokenize      │  ~ 1-5ms
                          │  Queue wait    │  ~ 0-500ms (load-dependent)
                          │  Prefill       │  ~ 50-500ms (prompt length)
                          │  Decode token1 │  ~ 30ms (TTFT done)
                          │  Decode token2 │  ~ 30ms
                          │  ...           │
                          │  Decode tokenN │  ~ 30ms × N
                          │  Detokenize    │  ~ 1ms
                          └────────────────┘
                                  │
                                  ▼
                          ┌────────────────┐
                          │ Post-process   │  ~ 5-20ms
                          │ JSON parse     │
                          │ Schema verify  │
                          │ Safety filter  │
                          └────────────────┘
                                  │
                                  ▼
                          ┌────────────────┐
                          │ Response       │  ~ 2-5ms egress
                          │ (stream / json)│
                          └────────────────┘
                                  │
                                  ▼
                              [User]
```

**Typical latency budgets** (chat use case, 100 output tokens):

| Stage | p50 | p99 | When 问题 |
|---|---|---|---|
| LB + Gateway | 5ms | 10ms | rare |
| Token Service | 10ms | 50ms | network hop, cache miss |
| RAG retrieve | 30ms | 100ms | vector DB cold / large index |
| Rerank | 50ms | 200ms | cross-encoder slow |
| Queue wait | 10ms | 300ms | over-subscribed |
| Prefill | 100ms | 500ms | long prompt, no prefix cache |
| Decode 100 tok | 3s | 8s | slow model, contention |
| Post-process | 5ms | 20ms | rare |
| Total p99 | 4s | 10s | 视情况 |

---

## 4. 4 类延迟问题分类表

| 问题类型 | 症状 | 主要 metric | 常见根因 |
|---|---|---|---|
| **TTFT 高** | 用户等待首字符久 | TTFT p99 | Long prompt, no prefix cache, queue wait |
| **TPOT 慢** | 生成卡顿 | tokens/sec | Memory bandwidth, batch contention, GPU shared |
| **某 slice 慢** | 特定用户 / tenant / query type | per-slice p99 | Hot tenant, specific query pattern, region |
| **Cold start spike** | 服务重启或 idle 后第一波 | spike pattern | KV cache empty, model not warm, weights from disk |

**Diagnostic question matrix**:

```
Slow request → 问:
  1. TTFT or TPOT?           ← stream timing
  2. Specific user or all?    ← per-user p99
  3. Long prompt or short?    ← prompt token histogram
  4. Recent regression?       ← time-series alert
  5. GPU util normal?         ← nvidia-smi
  6. Queue depth normal?      ← vLLM scheduler metric
  7. Network normal?          ← OS-level metric
```

---

## 5. 具体业务场景 (5 类)

### 场景 A: Voice Agent TTFT regression (你的工作背景, 真实 case)

**症状**: Voice agent 接入 vLLM 0.5 → 0.6 升级后, TTFT p99 从 800ms 涨到 3.5s, 用户在电话里听到长时间「思考...」.

**Debug 路径**:

```
1. 看 grafana — total latency p99 升, TTFT 升 4x, TPOT 不变
2. 看 OTel trace — prefill 阶段 200ms → 1800ms (9x ↑)
3. 看 vLLM metrics — `prefix_cache_hit_rate` = 5% (之前 90%)
4. Diff vLLM config — 0.5 → 0.6 default 改了, 需要显式 enable_prefix_caching=True
5. Fix: 加 config flag + chunked_prefill=True
6. Verify: TTFT 回到 400ms (比原始还好)
```

**Lesson**: **版本升级 default 改变是隐性 bug 源**, dependency 升级要 diff config.

### 场景 B: BNPL Chatbot RAG 多阶段 latency

**症状**: 用户问「我的订单为什么还没退款」, 总响应 4s, 用户抱怨.

**Debug 路径**:

```
OTel trace:
  Total: 4200ms
    ├── Gateway:        5ms
    ├── Auth:           15ms
    ├── Intent classify: 80ms  (Haiku 4.5)
    ├── RAG retrieve:   1200ms ← 异常 ❌
    │   ├── Embed query: 50ms
    │   ├── Vector search: 800ms ← 大头
    │   └── Rerank:     350ms
    ├── Tool call (DB query): 200ms
    ├── LLM generate:   2500ms (Sonnet 4.6, 300 output tokens)
    └── Post-process:   30ms

vector search 800ms 异常 (baseline 50ms):
  Vertex AI Vector Search metric: shard rebalancing in progress
  Fix: 等 rebalance 完, latency 回到 50ms
```

**Lesson**: 多阶段 pipeline, 单 stage 异常 dominates. 必须 per-stage breakdown.

### 场景 C: 高 throughput 时 batch 排队

**症状**: 周一 9am 高峰, p99 latency 从 1s 涨到 6s, GPU util 一直 100%.

**Debug 路径**:

```
看 vLLM metrics:
  - GPU util: 100% (✓ but 100% != good)
  - num_running_requests: 64 (max)
  - num_waiting_requests: 200 ← 排队
  - kv_cache_usage: 98% ← 满了, 没法接新请求

诊断: KV cache 满, 调度器 throttle 新请求, queue depth 涨
Fix:
  1. 增加 GPU memory (升 A100 80GB → H100 80GB or add replica)
  2. 减小 max output tokens (cap at 1024)
  3. 启用 chunked prefill (减少长 prefill 阻塞 decode)
  4. 启用 KV cache offload to CPU for long contexts
```

### 场景 D: Tool call cascade slow

**症状**: 用户问「我能用 PayLater 在 Shopee 买这个 iPhone 16 吗?」, agent 调 3 个 tool (price check + credit check + product compat), 总 5s.

**Debug 路径**:

```
Tool calls 是 sequential, 时间叠加:
  Tool 1: 800ms (Shopee API)
  Tool 2: 700ms (Credit API)
  Tool 3: 600ms (PayLater inventory)
  + LLM reason: 2s
  Total: 4.1s

Fix:
  1. Tool 1, 2, 3 并行 (Promise.all / asyncio.gather)
     → Total: max(800, 700, 600) + 2s = 2.8s (-32%)
  2. Cache 频繁 query (Shopee 价格 5min TTL)
     → Cache hit case: -800ms
  3. Speculative tool call (用历史预测哪些 tool 会调, 提前 prefetch)
     → 复杂, 收益 marginal, skip
```

### 场景 E: Long prompt 突然变多导致 prefill 拖累 decode

**症状**: 客户上线新功能, prompt 平均长度 800 → 4000 tokens, 整体 TTFT p99 从 500ms → 2.5s, 即使 short-prompt 用户也受影响.

**Debug 路径**:

```
vLLM 默认调度: 长 prefill 阻塞 decode (不混合)
  → 200 step 一个长 prefill 占整个 step, decode 等
  → Short user 等 prefill 完

Fix: chunked_prefill=True
  长 prefill 被切成 N 段 (e.g., 1024 tokens 一段)
  每个 step 混合 prefill chunk + 多个 decode
  → Short user TPOT 不被影响

SGLang 默认就是这样, vLLM 0.5+ 需 flag
```

---

## 6. 工程上要做什么 — diagnosis playbook (8 step)

### Step 1: Define problem precisely (5 min)

```
Bad: "latency is high"
Good:
  - Metric:       TTFT p99 (specifically)
  - Magnitude:    400ms → 2.3s
  - Scope:        all users, all queries
  - When:         started 2pm yesterday (after vLLM upgrade)
  - SLO:          TTFT p99 < 800ms
```

### Step 2: Existing observability inventory (5 min)

```
Have:
  - request total latency in Grafana ✓
  - vLLM request counter ✓

Missing:
  - Per-stage spans (need to add OpenTelemetry)
  - vLLM internal metrics (need to enable /metrics endpoint)
  - GPU profile (need Nsight session if deep dive)
```

### Step 3: Add per-stage instrumentation FIRST (30 min - 1h)

**Without breakdown, all diagnosis is guess**. Instrument:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def handle_request(req):
    with tracer.start_as_current_span("handle_request") as root:
        root.set_attribute("tenant_id", req.tenant_id)
        root.set_attribute("model", req.model)
        root.set_attribute("prompt_tokens", count_tokens(req.prompt))

        with tracer.start_as_current_span("auth"):
            user = await auth(req)

        with tracer.start_as_current_span("rag_retrieve"):
            with tracer.start_as_current_span("embed_query"):
                q_vec = embed(req.query)
            with tracer.start_as_current_span("vector_search"):
                chunks = await vector_db.search(q_vec, top_k=50)
            with tracer.start_as_current_span("rerank"):
                top10 = await reranker.rerank(req.query, chunks)

        with tracer.start_as_current_span("llm_inference") as llm_span:
            llm_span.set_attribute("prefill_tokens", count_tokens(prompt))
            # vLLM should auto-instrument with internal spans
            response = await llm.generate(prompt, ...)
            llm_span.set_attribute("output_tokens", response.usage.output_tokens)

        return response
```

Send to Jaeger / Tempo / Datadog APM.

### Step 4: Look at trace (10 min)

```
Trace view:
  handle_request: 2300ms
    ├── auth:        20ms (✓)
    ├── rag_retrieve: 1500ms ← 异常
    │   ├── embed_query: 50ms (✓)
    │   ├── vector_search: 1200ms ← 找到大头
    │   └── rerank:  250ms (✓)
    └── llm_inference: 780ms (✓)
```

### Step 5: Drill into bottleneck (1h)

For "vector_search 1200ms":

```python
# Check vector DB metrics
- Index size:           ✓ 10M vectors
- HNSW M, efSearch:     ✓ 32, 100
- Query QPS:            high  ← 可能 contention
- Disk IO:              high ← 可能 cold
- Memory pressure:      90% used ← cache eviction

# Look at vector DB logs
- "Loading segment from disk" appears every query
- Index hot tier 不够大

Fix: 增加 vector DB instance memory / 加 replica
```

### Step 6: Apply fix + verify (15 min - 几小时)

```python
# Before:
TTFT p99 = 2300ms

# Apply: increase Vertex AI Vector Search memory, enable better caching

# After (1h after deploy):
TTFT p99 = 600ms ✓
```

### Step 7: Add regression detection

```python
# SLO + alert
SLO:    TTFT p99 < 800ms
Alert:  burn rate > 2x for 10 min → page

# Canary
canary_test = SyntheticBenchmark(
    queries=hundred_standard_queries,
    target_metric='ttft_p99',
    threshold=800,
)
canary_test.run_every_5_min()
```

### Step 8: Document + post-mortem

```
Incident postmortem:
  - Root cause:       Vertex AI Vector Search memory pressure under load growth
  - Detection time:   45 min (users complained)
  - Resolution time:  2h (after diagnosis)
  - Action items:
    - Add memory utilization alert (< 80%)
    - Capacity planning quarterly
    - Document runbook for vector DB scaling
```

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **No per-stage instrumentation, just total latency** | 全靠猜, 浪费几小时 |
| 2 | **Confuse TTFT / TPOT / TTLT** | 优化错地方 |
| 3 | **Hardware fix first** (更多 GPU) | 钱浪费, 不解决根本 |
| 4 | **Don't know vLLM features** (prefix cache, chunked prefill) | 大量免费 optimization 没用上 |
| 5 | **Skip GPU memory check** | KV cache pressure subtle, 但 fatal |
| 6 | **No GPU profile** when needed | Nsight 是 free 信息, 但很多人不用 |
| 7 | **Don't diff config after upgrade** | vLLM 0.5→0.6 default 改, 隐性 regression |
| 8 | **Optimize for p50, miss p99** | tail latency 是用户感知的 |
| 9 | **Test fix on single request** | production load 下完全不同 |
| 10 | **No regression alert** | 同样问题 6 month 后又出现 |

---

## 一句话总结 (Part 1)

> **LLM 延迟 debug = 「先 instrument, 再看 trace, 找 bottleneck, 用对应 optimization, 加 SLO 防复发」**.
>
> 区分 TTFT vs TPOT vs queue wait vs tool latency 是基础功. **每个 stage 都可能是 bottleneck, 不要预判**.

---

# Part 2 · 5 个深度工程问题

## ⚙️ Problem 1: Latency Breakdown — TTFT vs TPOT vs 各阶段构成

### 1.1 TTFT 详细构成

```
TTFT = network_in + auth + app_logic + tokenize + queue_wait + prefill + first_decode

Typical share (TTFT = 500ms case):
  network_in:    20ms  (4%)
  auth:          20ms  (4%)
  app_logic:     30ms  (6%) — prompt build, RAG retrieve preview
  tokenize:      5ms   (1%)
  queue_wait:    50ms  (10%)
  prefill:       350ms (70%) ← 通常 dominates
  first_decode:  25ms  (5%)
```

**Prefill 占大头原因**:
- Compute: O(N²) with prompt tokens
- 对长 prompt, prefill 时间显著长于 decode 1 token

### 1.2 TPOT 详细构成

```
TPOT (per output token) = forward_pass + sampling + scheduling

For Llama 3 70B on H100, batch=1:
  forward_pass:    25ms  (95%) ← memory bandwidth bound
  sampling:        1ms
  scheduling:      < 1ms
  Total:           ~26ms

For batch=16:
  Per-token effective latency drops to ~10ms because batching amortizes weight loading
  But each individual user's TPOT might be 30ms (more compute per step)
```

### 1.3 Memory bandwidth vs Compute bound

```
Prefill (compute-bound):
  N² operations on KV
  GPU compute fully utilized
  Larger model = quadratically slower

Decode (memory-bandwidth-bound):
  1 token forward, but reads ALL model weights every step
  GPU compute UNDER-utilized (1-10%)
  Larger model = linearly slower, depending on bandwidth
```

**Implication**: 优化策略不同.

- **Prefill 慢** → reduce N (prefix cache, shorter context) or batch多人
- **Decode 慢** → quantization (smaller weights, less bandwidth), speculative decoding, batch 更多人

### 1.4 实测 numbers (2026 H100, Llama 3 70B fp16)

```
Single request, no batching:
  Prefill 1k token:       80ms
  Prefill 8k token:       500ms
  Prefill 32k token:      6s  (∼ N², 哦
  TPOT:                   25ms

Batch=16 with continuous batching:
  Prefill 1k × 16:        Stages mix in continuous batching
  Effective TPOT per user: 30-40ms (slight slowdown vs batch=1)
  Throughput:             ~640 tokens/sec aggregate

Batch=64 with continuous batching:
  Effective TPOT per user: 50-80ms (user feels slower)
  Throughput:             ~2000 tokens/sec aggregate

→ Trade-off: throughput vs per-user latency
```

### 1.5 Per-stage timing instrumentation

```python
# vLLM with OpenTelemetry
import time
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def generate_with_timing(req):
    timings = {}
    start = time.time()

    with tracer.start_as_current_span("tokenize"):
        t0 = time.time()
        tokens = tokenizer.encode(req.prompt)
        timings['tokenize_ms'] = (time.time() - t0) * 1000

    with tracer.start_as_current_span("queue_wait"):
        t0 = time.time()
        slot = await scheduler.acquire()
        timings['queue_wait_ms'] = (time.time() - t0) * 1000

    with tracer.start_as_current_span("prefill"):
        t0 = time.time()
        kv_cache = await engine.prefill(tokens)
        timings['prefill_ms'] = (time.time() - t0) * 1000

    with tracer.start_as_current_span("decode") as span:
        t0 = time.time()
        ttft = None
        output = []
        async for token in engine.decode(kv_cache):
            if ttft is None:
                ttft = (time.time() - start) * 1000
                span.set_attribute("ttft_ms", ttft)
            output.append(token)
        timings['decode_total_ms'] = (time.time() - t0) * 1000
        timings['tpot_avg_ms'] = timings['decode_total_ms'] / len(output)

    timings['ttft_ms'] = ttft
    timings['total_ms'] = (time.time() - start) * 1000
    return output, timings
```

---

## ⚙️ Problem 2: Diagnostic Tools — Nsight, OpenTelemetry, vLLM Metrics

### 2.1 Tool ladder (cheap → expensive)

```
Level 1 (always on, 1ms cost):
  - OpenTelemetry spans (per request)
  - vLLM /metrics endpoint (Prometheus)
  - Custom counters / histograms

Level 2 (per-incident, 10ms cost):
  - PyTorch Profiler (record specific request)
  - Memray (Python memory profile)
  - py-spy (Python CPU sampling)

Level 3 (deep dive, expensive):
  - NVIDIA Nsight Systems (GPU profile, ~100MB trace)
  - NVIDIA Nsight Compute (kernel-level)
  - Custom CUDA instrumentation
```

### 2.2 OpenTelemetry setup

```python
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="otel-collector:4317"))
)

# Visualize in Jaeger / Tempo / Datadog / Grafana
```

### 2.3 vLLM metrics endpoint

```
# Enable in vLLM startup
$ vllm serve meta-llama/Llama-3-70B --metrics-port 8001

# Scrape /metrics endpoint
$ curl localhost:8001/metrics
vllm:num_requests_running 32
vllm:num_requests_waiting 5
vllm:gpu_cache_usage_perc 0.78
vllm:num_preemptions_total 12
vllm:time_to_first_token_seconds_bucket{le="0.5"} 5234
vllm:time_to_first_token_seconds_bucket{le="1.0"} 8932
vllm:time_per_output_token_seconds_bucket{le="0.03"} 12044
vllm:prompt_tokens_total 1234567
vllm:generation_tokens_total 234567
```

**关键 metric to alert on**:
- `gpu_cache_usage_perc > 0.95` (KV cache 满, 即将 preempt)
- `num_requests_waiting > 0 sustained` (queue 积压)
- `num_preemptions_total` 增长率 (有 request 被牺牲)
- `time_to_first_token_seconds` p99 > SLO

### 2.4 PyTorch Profiler 实战

```python
from torch.profiler import profile, ProfilerActivity

# Single request profile
with profile(
    activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
    record_shapes=True,
    with_stack=True,
) as prof:
    output = model.generate(prompt)

# Top-10 slowest ops
print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=10))

# Export Chrome trace (visualize in chrome://tracing)
prof.export_chrome_trace("trace.json")
```

### 2.5 NVIDIA Nsight Systems

```bash
# Profile vLLM server for 30s
$ nsys profile --duration=30s --output=vllm_profile \
    --capture-range=cudaProfilerApi \
    python -m vllm.entrypoints.openai.api_server ...

# Analyze: 看 GPU timeline, kernel launches, memcpy, idle gaps
$ nsys-ui vllm_profile.nsys-rep
```

**关键问题 Nsight 能回答**:
- GPU 是否真在做 useful work, 还是空转?
- 哪些 kernel 占时间最多?
- Memory copy 占多少? (CPU↔GPU 频繁是 anti-pattern)
- Kernel launch overhead (small batch 时 launch 比 compute 还久)

### 2.6 GPU 实时观测

```bash
# nvidia-smi 实时
$ nvidia-smi dmon -s u  # utilization
$ nvidia-smi -l 1       # refresh every 1s

# GPU memory详细
$ nvidia-smi --query-gpu=memory.used,memory.free --format=csv -l 1

# Bandwidth (memory bandwidth indication)
$ dcgmi profile --pause --reset --resume  # NVIDIA DCGM
```

### 2.7 LangSmith / Phoenix / Braintrust (LLM-specific tracing)

```python
# LangSmith (LangChain ecosystem)
from langsmith import Client
client = Client()

@client.trace
def llm_call(prompt):
    return llm.generate(prompt)
# Auto-records prompts, outputs, latency, cost

# Phoenix (Arize, OSS)
from phoenix import register
register()  # Auto-instruments OpenAI / LangChain / LlamaIndex

# Braintrust (eval + tracing)
import braintrust
with braintrust.start_span("rag_query") as span:
    span.log(input=query, output=answer, latency_ms=latency)
```

### 2.8 Diagnostic Flowchart

```
Latency 异常
  │
  ▼
Per-stage trace (OTel)?
  ├── No  → instrument first (1h investment)
  └── Yes
      ↓
  哪个 stage 大头?
      ├── RAG → check vector DB metrics, network, index health
      ├── Tool call → external API SLO, parallelize sequential
      ├── Inference → continue ↓
      │
      ▼
  TTFT or TPOT?
      ├── TTFT → check prefill, prefix cache, queue depth, prompt length
      ├── TPOT → check batch size, GPU memory bandwidth, model size
      │
      ▼
  vLLM metrics 看到啥?
      ├── kv_cache > 95% → memory pressure, add GPU/reduce concurrent
      ├── waiting_requests > 0 → over-subscribed, scale out
      ├── prefix_cache_hit_rate low → enable / fix
      └── preemption增长 → reduce max output, scale
      │
      ▼
  Profile with Nsight if 深 dive 需要
```

---

## ⚙️ Problem 3: Optimization Levers — Continuous Batching, Prefix Caching, Speculative Decoding, Quantization

### 3.1 Continuous Batching (vLLM 标志特性)

**传统 static batching 问题**:

```
Time:    0────────1s────────2s────────3s
Req A:   [prefill][decode 100 tokens......]  done at 2s
Req B:   [        wait        ][prefill][decode...]  done at 4s
Req C:   ...等

GPU 大部分时间在 decode (1 user 1 token), 利用率低
```

**Continuous batching**:

```
Each step:
  - 选 pending requests (mix prefill + decode)
  - 1 forward pass: prefill A's prompt + decode B's next token + decode C's next token
  - GPU 利用率 90%+
```

**没有 trade-off, vLLM/SGLang 默认开. 但要 verify config 正确**.

### 3.2 Prefix Caching

```python
# 场景: 多个用户共享同 system prompt
SYSTEM_PROMPT = """You are a debt collection agent for TikTok PayLater..."""  # 2000 tokens

# Without prefix cache:
# Each request: prefill 2000 sys + N user tokens = expensive

# With prefix cache:
# First request: prefill 2000 sys → cache KV for sys prompt
# Subsequent requests: skip 2000 sys prefill, jump to user tokens
# → TTFT -70% on long system prompts
```

```yaml
# vLLM enable
$ vllm serve ... --enable-prefix-caching
```

**Cache hit rate** 应该 monitor — 如果 < 30%, prompts 不够相似, 不 worth.

### 3.3 Speculative Decoding

**Idea**: 用 cheap small model 生成 N token candidates, big model 一次 verify N tokens.

```
Without spec decode:
  Big model: 1 forward = 1 token (30ms/token)
  100 tokens = 3s

With spec decode (4-token speculation):
  Small model: 1 forward = 1 token (3ms × 4 = 12ms)
  Big model: 1 forward = verify 4 tokens (40ms)
  Effective: 4 tokens in 52ms = 13ms/token
  100 tokens = 1.3s (2x speedup if accept_rate=70%)
```

**Trade-off**:
- 需要 draft model (Llama 3 70B + Llama 3 8B as draft)
- Accept rate 决定收益 (典型 60-80%)
- 适合 decode-heavy (long generation), not prefill-heavy

**vLLM config**:
```python
LLMEngine(
    model="meta-llama/Llama-3-70B",
    speculative_model="meta-llama/Llama-3-8B",
    num_speculative_tokens=5,
)
```

### 3.4 Quantization

| Precision | Memory | Speed | Quality |
|---|---|---|---|
| FP16 | 1.0x | 1.0x | baseline |
| BF16 | 1.0x | 1.0x | baseline |
| FP8 | 0.5x | 1.3x | < 1pp loss |
| INT8 | 0.5x | 1.2x | 1-2pp loss |
| INT4 (GPTQ/AWQ) | 0.25x | 1.5-2x | 3-5pp loss |

**实测**: Llama 3 70B FP16 需 140GB → AWQ INT4 36GB (能放 1 张 H100 80GB).

```python
# Load AWQ quantized model
LLM(model="TheBloke/Llama-3-70B-AWQ", quantization="awq")
```

**Caveat**: 量化对 reasoning task 影响更大 (vs chat). 必须 eval calibrate.

### 3.5 KV Cache 优化

**KV cache size** = `batch_size × seq_len × n_layers × n_heads × head_dim × 2 (K+V) × precision`

For Llama 3 70B (80 layers, 64 heads, 128 head_dim, FP16):
- Per token KV: 80 × 64 × 128 × 2 × 2 byte = 2.6 MB
- Batch 32 × 4096 tokens = 343 GB ← 装不下任何 GPU!

**Solutions**:
- **PagedAttention** (vLLM default): non-contiguous, no fragmentation, 90%+ util
- **GQA (Grouped Query Attention)**: 减少 K, V heads (Llama 3 用了)
- **KV cache quantization** (FP8 / INT4 for KV separately)
- **CPU offload** for long context (slower but works)
- **Sliding window attention** (Mistral): 只保留最近 N tokens KV

### 3.6 Chunked Prefill

**Without**: 长 prefill 阻塞 decode

```
Step 1: prefill 4k tokens (300ms, blocks decode)
Step 2: decode all users (30ms)
Step 3: decode all users (30ms)
```

**With**:

```
Step 1: prefill 512 chunk + decode user A + decode user B  (60ms)
Step 2: prefill 512 chunk + decode user A + decode user B  (60ms)
...
Step 8: prefill last 512 + decode A + B  (60ms)
Total prefill: 480ms (slight overhead), but decode never blocked
```

**SGLang 默认开**. vLLM 0.5+ 加 flag `--enable-chunked-prefill`.

### 3.7 Optimization 选型 decision tree

```
延迟问题
  │
  ├── TTFT 高
  │   ├── prompt 长 + 共享 prefix → 启 prefix caching
  │   ├── prompt 长 + 不共享 → 启 chunked prefill
  │   ├── queue 排队 → 加 replica / 减 max concurrent
  │   └── cold start → keepalive / warm-up
  │
  ├── TPOT 高
  │   ├── batch 太小 → 增大 batch (但牺牲 per-user latency)
  │   ├── model 太大 → 量化 (AWQ INT4)
  │   ├── memory bandwidth 瓶颈 → 量化 / speculative decode
  │   └── KV cache 满 → 减 max output / 加 GPU
  │
  └── Throughput 低
      ├── GPU util < 60% → batch size 加大 / continuous batching
      ├── Memcpy 占多 → 减 CPU↔GPU 数据 (避免 unnecessary)
      └── Kernel launch overhead → bigger batch / CUDA graph
```

---

## ⚙️ Problem 4: System Bottlenecks — Network, GPU Memory, KV Cache, Scheduling

### 4.1 网络层瓶颈

```
Cross-region:    50-150ms RTT (Asia → US)
Same region:     1-5ms RTT
Same AZ:         < 1ms
Same node:       < 100us

DNS lookup:      0-20ms (cache MISS expensive)
TLS handshake:   30-100ms (新连接)
HTTP/2 reuse:    免重建
```

**Optimizations**:
- Persistent connection pool (HTTP/2)
- Co-locate inference + storage in same region
- gRPC instead of REST (less overhead)
- Skip auth check for internal calls (mTLS only)

### 4.2 GPU Memory 瓶颈

```
H100 80GB breakdown for Llama 3 70B FP16:
  Model weights:     140GB  ← 装不下! 需 TP=2 或量化
  KV cache (max):    剩余 = (160GB - 140GB) / 2 GPU = 10GB per GPU
  
Real life:
  AWQ INT4:          36GB weights → 1 H100 80GB
  KV cache budget:   44GB
  Max concurrent:    44GB / 2.6MB per token = ~16k tokens total budget
  
  If avg user = 1000 tokens (prompt + output):
    Max concurrent users = 16
```

### 4.3 KV Cache Eviction

```
当 KV cache 满, 新请求 vLLM 怎么处理?

Strategy 1: Wait (default)
  新 request 加入 waiting queue, GPU 闲也不接

Strategy 2: Preempt (eviction)
  最旧 (or least progress) request 的 KV 被 evict 到 CPU / 重新计算
  → 优先级低的 request latency 飙升

Strategy 3: Reject
  返回 503, 等 client retry

vLLM 默认 Strategy 1 (wait). 可配置.
```

**Avoidance**: 监控 `gpu_cache_usage_perc`, > 90% 时 alert + scale out.

### 4.4 Scheduling 算法

```python
# vLLM scheduler 决策
def schedule_step():
    # 1. Check running requests, advance decode
    for req in running:
        decode_one_step(req)
        if req.kv_cache_full:
            preempt(req)

    # 2. Check waiting requests, see if can fit
    for req in waiting:
        kv_needed = req.prompt_len * kv_per_token
        if kv_needed <= available_cache:
            running.add(req)
            prefill(req)

    # 3. Combine in single GPU forward pass
    forward_pass(prefill_batch + decode_batch)
```

**Fairness vs throughput**: vLLM default favors throughput (FIFO + greedy fit). 不公平但快.

**Per-tenant fairness**: 需要 custom scheduler (e.g., weighted fair queue per tenant) — vLLM 不内置, SGLang 有 hooks.

### 4.5 Compute vs Memory Bandwidth bound

```
Arithmetic Intensity (AI) = FLOPs / Bytes
GPU spec: H100 has ~989 TFLOPS, 3.4 TB/s bandwidth → optimal AI ~ 290

LLM prefill: AI ~ N (high), compute-bound
LLM decode: AI ~ batch_size (low), memory-bandwidth-bound

Implication:
  - Bigger batch = higher AI = better GPU util (for decode)
  - 但 batch 太大 latency 涨
  - Sweet spot: batch 16-64 typical
```

### 4.6 Detecting bottleneck type

```
GPU util high, throughput low? → memcpy bound (CPU<->GPU)
GPU util high, throughput high? → optimal, no bottleneck here
GPU util low, queue depth low? → request rate低, OK
GPU util low, queue depth high? → CPU bound (tokenize / scheduling)
Memory pressure高? → KV cache full, need scale
```

---

## ⚙️ Problem 5: Multi-stage Pipeline Latency — RAG + Rerank + LLM + Tool

### 5.1 典型 agentic pipeline

```
User query
   ↓
[1. Intent classify] (Haiku 4.5, 80ms)
   ↓
[2. Query rewriting] (Sonnet 4.6, 200ms)
   ↓
[3. RAG retrieve] (Vertex AI Vector Search, 50ms)
   ↓
[4. Rerank] (bge-reranker-v2, 200ms)
   ↓
[5. Tool calls in parallel] (max 500ms)
     ├── Tool A: 400ms
     ├── Tool B: 300ms
     └── Tool C: 500ms
   ↓
[6. LLM generate] (Sonnet 4.6, 2500ms)
   ↓
[7. JSON parse + validate] (10ms)
   ↓
Response

Total p50: 80 + 200 + 50 + 200 + 500 + 2500 + 10 = 3540ms
```

### 5.2 Where to cut

**1. 并行化 sequential stages**

```python
# Before (sequential):
intent = await classify(query)        # 80ms
rewritten = await rewrite(query, intent)  # 200ms
chunks = await retrieve(rewritten)    # 50ms
reranked = await rerank(query, chunks) # 200ms
# Total: 530ms

# After (parallel where possible):
intent_fut = classify(query)
rewritten_fut = rewrite(query)  # 不依赖 intent
intent, rewritten = await asyncio.gather(intent_fut, rewritten_fut)
chunks = await retrieve(rewritten)
reranked = await rerank(query, chunks)
# Total: max(80, 200) + 50 + 200 = 450ms (-15%)
```

**2. Cascade routing (skip stages if confident)**

```python
async def smart_pipeline(query):
    intent = await classify(query)

    # 简单 intent (greeting, FAQ) 跳过 RAG
    if intent in ['greeting', 'goodbye']:
        return await small_llm.generate(query)  # 200ms total

    # 标准 RAG flow
    if intent == 'factual':
        chunks = await retrieve(query)
        return await medium_llm.generate(query, chunks)  # 1500ms

    # 复杂 multi-hop
    return await full_agentic_flow(query)  # 4000ms
```

**3. Streaming + speculative response**

```python
# Stream LLM output as soon as available
async def stream_response(query):
    # Quick acknowledgment (50ms perceived latency)
    yield "Looking up your account..."

    # Parallel: RAG + LLM warmup
    rag_task = asyncio.create_task(retrieve(query))
    llm_warmup = asyncio.create_task(prepare_llm_session())

    chunks = await rag_task
    await llm_warmup

    # Stream tokens as they generate
    async for token in llm.stream(query, chunks):
        yield token
```

**4. Caching**

```python
# Cache levels
embedding_cache:    LRU 10k queries, 1h TTL  (skip embed)
retrieval_cache:    LRU 1k queries, 5min TTL (skip retrieve + rerank)
response_cache:     LRU 500 exact-match queries, 30s TTL (skip LLM)

# Hit rate typical:
embedding_cache:    40% (popular queries)
retrieval_cache:    25% (semantic similar)
response_cache:     10% (exact match)
```

**5. Reduce output tokens**

```python
# Generation tokens dominate TTLT
# 300 token response × 30ms TPOT = 9000ms decode
# 100 token response × 30ms TPOT = 3000ms

# Force concise output via prompt + max_tokens
prompt = """Answer in 1-2 sentences max."""
max_tokens = 150  # hard cap
```

### 5.3 Tool call optimization

```python
# Pattern 1: Parallel independent tools
async def run_tools(query, tool_calls):
    return await asyncio.gather(*[t.execute() for t in tool_calls])

# Pattern 2: Speculative tool prefetch
async def smart_tool_caller(query):
    # 用 cheap model 预测 likely tools
    predicted = await haiku_45.predict_tools(query)
    
    # 提前调用 (speculative)
    speculative = [tool.execute() for tool in predicted]
    
    # LLM 决定真正要哪些
    actual_calls = await llm.decide_tools(query)
    
    # 复用 speculative 结果
    results = []
    for call in actual_calls:
        if call in predicted:
            results.append(speculative[predicted.index(call)])
        else:
            results.append(await call.execute())
    return results

# Cost: 2x tool calls (但很多 cached / cheap)
# Benefit: latency 减少 (some tools 提前做了)
```

### 5.4 End-to-end SLO 拆分

```
User SLO: response p99 < 3s

Allocate budget:
  Network in:       100ms (3%)
  Auth + routing:   100ms
  RAG + rerank:     500ms (17%)
  Tool calls:       500ms (17%, parallel)
  LLM (avg 150 out): 1500ms (50%)
  Network out:      100ms

Tight budget — each stage 不能爆.

Per-stage alert:
  RAG > 800ms → page
  Tool call > 800ms → page
  LLM TTFT > 800ms → page
```

### 5.5 Streaming TTFT trick

```python
# Make user feel fast even if total slow
async def perceived_fast_response(query):
    # 50ms: ACK
    yield "..."  # show typing indicator
    
    # 200ms: intent classify done, hint
    intent = await classify(query)
    if intent == 'refund':
        yield "Looking up your refund status..."
    
    # 1500ms: chunks retrieved, can start LLM
    chunks = await retrieve(query)
    
    # 2500ms: first token from LLM, real response starts
    async for tok in llm.stream(query, chunks):
        yield tok
```

User perception: 50ms TTFT (vs 2500ms naive).

---

# Part 3 · 把 5 个问题串起来看

这 5 个问题是 **LLM latency debugging 的 5 个层次**:

1. **Latency breakdown** 让你能说「问题在哪个 stage」
2. **Diagnostic tools** 让你能说「我会用 X 工具拿数据」
3. **Optimization levers** 让你能说「我知道 vLLM 有这些功能」
4. **System bottlenecks** 让你能说「我知道 GPU / 网络 / KV cache 的限制」
5. **Multi-stage pipeline** 让你能说「我处理过 agentic system 的 end-to-end latency」

面试场把这 5 层都讲出来, 加上「我自己 production 踩过 X 坑 (vLLM 升级 / Vertex AI Vector Search memory 等)」, 就是 staff-level inference engineer 水准.

---

## 必问 clarifying questions

**1. Which latency metric**

> "p50 / p99 / max? TTFT or TPOT or TTLT? Streaming or non-streaming?"

**2. New problem or recent regression**

> "Always slow, or recent? If recent: deploy / config / traffic change?"

**3. All requests or specific**

> "Long prompts only? Specific user / tenant? Specific time of day? Specific model?"

**4. Magnitude**

> "How much over expectation — 2x or 10x? Helps narrow."

**5. Existing observability**

> "Per-stage timing? Trace spans? vLLM metrics? Or do I need to add instrumentation first?"

**6. Acceptable downtime for fix**

> "Can we restart vLLM? Rolling restart? Or zero-downtime required?"

---

## 5 步框架 (sample 60-min answer)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify metrics + scope + magnitude |
| 5-15 min | Walk down 7-stage pipeline, add timing first |
| 15-30 min | 7 common bottleneck pattern (A-G) |
| 30-45 min | Tools (Nsight, vLLM metrics, OTel) deep dive |
| 45-55 min | Optimization levers + when to use each |
| 55-60 min | Prevent recurrence — SLO + canary + post-mortem |

---

## 简历专属 reframe

你的 **vLLM / SGLang post-training infra** + **voice agent latency**:

| 题 | 你做过 |
|---|---|
| LLM inference optimization | **简历直接写 'vLLM, SGLang, memory-efficiency tuning'** |
| Streaming voice TTFT p99 < 800ms | Voice agent 你 own |
| Prefix caching / chunked prefill | Voice agent system prompt 共享 |
| KV cache management | Multi-turn voice agent 必处理 |
| GPU profiling | vLLM tuning 你做过 |
| Multi-stage pipeline | BNPL agentic + voice agent ASR→LLM→TTS pipeline |

**主动 quote**:

> "I literally lived this in our voice agent. We hit TTFT regression after vLLM 0.5 → 0.6 upgrade — turned out prefix caching default changed, our system prompt re-prefilled every request. I diagnosed by:
>
> 1. **First instrument** — added OTel spans for prefill / decode (15 min)
> 2. **Looked at trace** — prefill 200ms → 1800ms, decode unchanged
> 3. **Checked vLLM metrics** — prefix_cache_hit_rate dropped from 90% to 5%
> 4. **Diff config** — found `enable_prefix_caching` default flipped to false
> 5. **Fixed + verified** — re-enabled flag + added chunked_prefill, TTFT back to 400ms
>
> The pattern I'd recommend: **never assume your infra config is what you think — always diff against actual runtime config before each diagnosis**.
>
> For agentic multi-stage pipeline at BNPL, I learned to **budget latency per stage** with SLO alerts. When RAG retrieve started taking 800ms (Vertex AI Vector Search rebalance), we caught it in 5 min, not after users complained. Per-stage SLO + canary = sleep at night."

→ 这是你简历最强 match 的题, 一定 ace.

---

## 5 follow-ups

**Q1**: "GPU at 100% but latency still high. What gives?"

**A**: 100% GPU util ≠ effective work:
- Could be **memory copy** (CPU↔GPU): use Nsight to see if `Memcpy` 占 30%+ → memory-bound, not compute
- Could be **batch wait time** — requests waiting for batch fill, GPU not真 bottleneck
- **Kernel launch overhead** — small batch, frequent launches, GPU mostly launching not computing
- **KV cache pressure** — `gpu_cache_usage_perc > 95%` causing preemption
- Diagnosis: Nsight Systems profile, look at GPU timeline gaps

**Q2**: "Smaller model latency similar to bigger model. Why?"

**A**: Several possibilities:
- **Network / preprocessing dominates** when model compute is small
- **Batch overhead constant** regardless of model size
- **Memory bandwidth bottleneck** — decode is bandwidth-bound, smaller model doesn't help proportionally
- **Tokenizer cost amortizes badly** on short generation
- Smaller model usually wins on **throughput** more than latency, unless prompt is huge

**Q3**: "Customer reports 5x latency, but our metrics show p99 fine. Disconnect?"

**A**: Common causes:
- Metrics miss **client-perceived latency**: TLS handshake, DNS, client-side parsing
- Add **client SDK timing**: time from user action → first display
- **Mid-percentile drift**: p99 fine but p99.9 catastrophic → customers happen to land on long-tail
- **Streaming TTFT vs TTLT mismatch**: customer sees TTLT, we measure TTFT
- **Region routing**: customer in slow region (cross-region), our average masks it
- Fix: add **per-customer p99** + **per-region p99** in metrics

**Q4**: "vLLM vs SGLang vs TensorRT — which for production 2026?"

**A**:
- **vLLM**: most popular, broad model support, mature ecosystem, default choice
- **SGLang**: faster (better chunked prefill, RadixAttention for prefix caching), but smaller community
- **TensorRT-LLM**: highest throughput on NVIDIA, locked into NVIDIA, complex to operate (1-2 weeks setup vs vLLM 1 hour)
- For most: **vLLM**. For very high QPS + NVIDIA-only: TensorRT-LLM. For low-latency multi-turn (voice agent, copilot): try SGLang.
- 2026 趋势: vLLM 在 catch up SGLang features, gap closing.

**Q5**: "Multi-region serving — how route?"

**A**:
- **Latency-based routing** (AWS Global Accelerator / GCP Premium Tier): user → closest region
- **Affinity routing** for multi-turn: same user → same region → reuse KV cache (huge win)
- **Failover**: region failure → next closest, pre-warm second-region cache
- **Cost optimization**: cheaper inference in some regions, route batch / async there
- **Compliance**: EU users must hit EU region (GDPR), India users India region (data residency)
- We did this at TikTok: per-market routing for both latency AND compliance.

---

## ❌ 易错点 (top 10)

1. **No per-stage instrumentation first** — diagnosis by hypothesis
2. **Confuse TTFT vs TPOT vs TTLT vs throughput**
3. **Hardware fix first** (more GPUs) — expensive, doesn't fix root
4. **Don't know vLLM features** — prefix cache, chunked prefill, paged attention
5. **Skip GPU memory check** — KV cache pressure subtle
6. **Don't profile, just guess** — Nsight / vLLM metrics are free
7. **No SLO / canary** to prevent recurrence
8. **Optimize for p50** — p99 is user-perceived
9. **Skip post-mortem** — same problem comes back
10. **No regression test on deploy** — config drift undetected

---

## ✅ 加分项 (top 10)

1. **7-stage pipeline breakdown** systematic
2. **Per-stage OTel instrumentation** as first step
3. **7 common prefill pathology** (A-G) named
4. **vLLM internal metrics** knowledge (kv_cache_usage, num_preemptions)
5. **NVIDIA Nsight Systems** for GPU profile
6. **Prefix caching + chunked prefill** as standard
7. **Speculative decoding + quantization** awareness
8. **Synthetic canary** for regression prevention
9. **Multi-stage budget** with per-stage SLO
10. **Quote vLLM 0.5→0.6 upgrade experience** (resume gold)

---

## 一句话总结

> **LLM inference latency debugging = 「先 per-stage instrument, 再 find bottleneck, 再用 vLLM/SGLang 对应 lever 优化, 再加 SLO 防复发」**.
>
> 没有 instrumentation 就没有 debug, 全是猜测.

---

## Cheat Sheet (印 1 页)

```
LLM inference 7 stages:
  Gateway/auth (5-20ms)
  RAG retrieve + rerank (50-300ms)
  Tokenize (1-5ms)
  Queue wait (0-500ms)
  Prefill (50-500ms, O(N²)) ← compute-bound
  Decode (10-30 tokens/sec) ← memory-bandwidth-bound
  Post-process + egress (10-20ms)

Metrics distinguish (must clarify which):
  TTFT (time to first token) — UX for streaming
  TPOT (per-token latency) — flow fluency
  TTLT (time to last token) — total user wait
  Throughput (tokens/sec aggregate) — capacity

Common prefill bottleneck (A-G):
  A. Long prompt + small batch → enable prefix caching
  B. KV cache eviction under load → paged-attention + more GPU
  C. Batch too small → chunked prefill (SGLang default, vLLM flag)
  D. Cold start / model not warm → keepalive / scheduled warmup
  E. Tensor parallel overhead → tune TP per batch size
  F. Tokenizer slow → rare (unusual unicode)
  G. Quantization mode mismatch → diff config

Diagnostic ladder (cheap → expensive):
  1. Per-stage OTel spans (always on, 1ms cost) ← must have
  2. vLLM /metrics endpoint (Prometheus)
  3. PyTorch Profiler (per-incident)
  4. NVIDIA Nsight Systems (deep dive)
  5. NVIDIA Nsight Compute (kernel-level)

Key vLLM metrics:
  num_requests_running     — current load
  num_requests_waiting     — queue depth
  gpu_cache_usage_perc     — KV pressure (alert > 90%)
  num_preemptions_total    — slow requests being killed
  time_to_first_token p99  — TTFT histogram
  prefix_cache_hit_rate    — prefix cache effectiveness

Optimization levers (priority):
  1. Continuous batching (free, vLLM default)
  2. Prefix caching (50-90% TTFT save on shared sys prompt)
  3. Chunked prefill (decode 不被长 prefill 阻塞)
  4. Quantization (AWQ INT4: 4x memory, 2x speed)
  5. Speculative decoding (2-3x decode速度 if accept_rate高)
  6. Paged attention (default, KV efficiency 90%+)

System bottlenecks:
  Memory bandwidth: decode 主要瓶颈 → quantization 救
  Compute: prefill 主要瓶颈 → prefix cache / shorter prompt
  Network: cross-region → co-locate, gRPC
  KV cache: 满 → scale, reduce max output, offload to CPU
  Scheduling: FIFO not fair → custom scheduler for tenant

Multi-stage agentic pipeline:
  Per-stage SLO budget (e.g., 3s total → 500ms RAG)
  Parallelize independent stages
  Cascade routing (skip stages if simple)
  Stream early ACK + tokens
  Cache embedding / retrieval / response separately

Diagnostic flowchart:
  Latency 异常 → instrument first
    → 哪个 stage 大头?
      RAG → vector DB metrics
      Inference → TTFT or TPOT?
        TTFT → prefill / prefix cache / queue
        TPOT → batch / quant / GPU memory
    → Apply 对应 optimization
    → Verify with trace
    → Add SLO + canary

红线:
  - 没 per-stage timing 就 debug → 浪费小时
  - 上 hardware fix 先 → 钱浪费
  - 不知 vLLM features → 免费 optim 没用
  - 没 GPU memory monitoring → KV cache 满了不知道
  - 没 canary / SLO → 同样问题复发
  - Test fix on 1 request → 生产 load 完全不同
  - Config drift 不 diff → 隐性 regression

Production-ready checklist:
  ✓ OpenTelemetry traces, per-stage spans
  ✓ vLLM /metrics enabled, Prometheus scrape
  ✓ Grafana dashboard (TTFT, TPOT, queue, KV usage)
  ✓ SLO alerts (TTFT p99, error rate, queue depth)
  ✓ Synthetic canary (100 standard queries every 5 min)
  ✓ Per-deploy benchmark (block merge if regression)
  ✓ Runbook for common issues (KV full, prefix cache miss)
  ✓ Per-tenant / per-region metrics (catch hot tenant / region issue)
```
