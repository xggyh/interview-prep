## AI Deep Dive #3 · LLM Inference Latency — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/llm-inference-latency.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`llm-inference-latency.html`](questions/llm-inference-latency.html)

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

> **LLM latency debug = instrument first (per-stage OTel spans), 不靠猜**. 区分 TTFT (UX for streaming) vs TPOT (flow fluency), 知道 7 stages (gateway / RAG / rerank / tokenize / queue / prefill / decode / post-process), 选对应 optimization (prefix cache for TTFT, quantization for TPOT). Diagnostic ladder 从便宜到贵: OTel → vLLM metrics → PyTorch Profiler → Nsight Systems → Nsight Compute.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| TTFT | Time-To-First-Token | streaming UX |
| TPOT / ITL | Time-Per-Output-Token | flow fluency |
| TTLT | Time-To-Last-Token (total) | user 总 wait |
| Throughput | tokens/sec aggregate | capacity planning |
| Prefill | 一次性 forward 算 KV cache, O(N²) | compute-bound |
| Decode | 自回归生成, 一次一 token | memory-bandwidth-bound |
| KV cache | key/value cache per token | decode 必读 |
| Continuous batching | vLLM 动态混合 prefill + decode | GPU 利用率拉满 |
| PagedAttention | KV cache 分页存储 | KV 效率 90%+ |
| Prefix caching | 共享 system prompt KV | TTFT 50-90% save |
| Chunked prefill | 长 prefill 切片不阻塞 decode | SGLang default |
| Speculative decoding | 小 draft + 大 verify | 2-3x decode speed |
| Tensor Parallel (TP) | 一层切到多卡 | layer 太大 |
| Pipeline Parallel (PP) | 不同层在不同卡 | very deep model |
| AWQ / GPTQ | INT4 weight quantization | 4x memory 2x speed |
| FP8 / INT8 | half/quarter precision | 2x throughput |
| vLLM / SGLang | 主流 LLM serving | continuous batching |
| TensorRT-LLM | NVIDIA 闭源 serving | 最快但锁定 NVIDIA |
| Nsight Systems | GPU profiler | kernel timeline |

### 🎯 5 个核心 framework

**Framework 1**: 7-Stage Pipeline + Latency Budget
- When: 任何 LLM serving 系统
- Algorithm:
  - LB + Gateway 5-10ms
  - Token Service 10-50ms
  - RAG retrieve 30-100ms
  - Rerank 50-200ms
  - Queue wait 0-500ms
  - Prefill 100-500ms (long prompt, O(N²))
  - Decode 30ms/token × N
  - Post-process 5-20ms
  - Egress 2-5ms
- Trade-off: 每 stage SLO budget 总和 <= 总 target
- Tools: OpenTelemetry spans, Grafana per-stage dashboard

**Framework 2**: TTFT vs TPOT Diagnostic
- When: 用户投诉 "slow"
- Algorithm:
  - TTFT 高 → prefill 慢 / prefix cache miss / queue wait → 加 prefix cache, chunked prefill, scale capacity
  - TPOT 慢 → memory bandwidth / batch contention → quantization (AWQ INT4), speculative decoding
  - 某 slice 慢 → hot tenant / specific query pattern → 看 per-slice p99 metric
  - Cold start spike → 服务重启 KV cache empty → keepalive, scheduled warmup
- Trade-off: 优化 prefill 跟 decode 是不同问题, 一刀切优化错
- Tools: Diff TTFT vs total, time-series alert by slice

**Framework 3**: Diagnostic Ladder (Cheap → Expensive)
- When: instrument → drill down
- Algorithm:
  1. Per-stage OTel spans (always on, 1ms cost) ← must have
  2. vLLM /metrics endpoint (Prometheus scrape)
  3. PyTorch Profiler (per-incident, on demand)
  4. NVIDIA Nsight Systems (deep dive, GPU timeline)
  5. NVIDIA Nsight Compute (kernel-level, 最深)
- Trade-off: 深度 vs 时间, 永远 cheap first
- Tools: OpenTelemetry, Prometheus, Jaeger, py-spy, Nsight

**Framework 4**: Optimization Levers (Priority Order)
- When: 找到 bottleneck 后
- Algorithm:
  1. Continuous batching (free, vLLM default)
  2. Prefix caching (50-90% TTFT save on shared sys prompt)
  3. Chunked prefill (decode 不被长 prefill 阻塞)
  4. Quantization (AWQ INT4: 4x memory, 2x speed)
  5. Speculative decoding (2-3x decode 速度 if accept_rate 高)
  6. PagedAttention (default, KV efficiency 90%+)
  7. Tensor/Pipeline parallelism (大 model)
- Trade-off: 每个 lever 收益边际递减, 先 quick win
- Tools: vLLM flags (enable_prefix_caching, chunked_prefill), AWQ checkpoint, SpecDec draft model

**Framework 5**: Multi-Stage Pipeline Latency (RAG + Rerank + LLM + Tool)
- When: agentic 系统
- Algorithm:
  - Per-stage SLO budget (e.g., 3s total → 200ms RAG / 200ms rerank / 1.5s LLM / 1s tool / 100ms post)
  - Parallelize independent stages (RAG + tool 并行)
  - Cascade routing (简单 query → skip rerank, 复杂 → 全 pipeline)
  - Stream early ACK + tokens (用户看 "Thinking..." 立即)
  - Cache embedding / retrieval / response separately
- Trade-off: parallelization 增加复杂度, 但 P99 reduce 50%+
- Tools: asyncio.gather, Redis cache layered, OTel span tree

### 🌳 关键决策树

```
用户报 slow, 第一步?
├── 看 dashboard total p99 vs baseline
├── 区分 TTFT 高还是 TPOT 慢?
│   ├── TTFT 高 → drill prefill / RAG / queue
│   ├── TPOT 慢 → drill decode / batch contention
│   └── 总 high 但 TTFT TPOT 都 normal? → 看 RAG / tool / post-process
└── per-slice (user / tenant / region)? → hot 现象?

TTFT 高 root cause?
├── prefix_cache_hit_rate 低? → enable prefix caching
├── num_requests_waiting 高? → queue wait, scale up
├── prompt 长? → chunked prefill, shorter prompt
├── 冷启 / restart? → keepalive, warmup
└── RAG 慢? → vector DB metrics

TPOT 慢 root cause?
├── gpu_cache_usage_perc > 90%? → KV pressure, scale or reduce max output
├── batch size 大? → tensor parallel tune
├── memory bandwidth bound? → quantization AWQ INT4
├── model 大 (70B+)? → speculative decoding 7B draft
└── GPU 共享? → 独占 instance

Cold start spike?
├── KV cache empty → keepalive + scheduled warmup
├── Model weights from disk → preload, RAMdisk
└── First batch suboptimal → run synthetic warmup queries
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: TTFT vs TPOT Latency Breakdown**
- 核心解法:
  ```
  TTFT = network + auth + RAG + tokenize + queue_wait + prefill
  TPOT = model_forward / output_token (decode step)
  TTLT = TTFT + N_output_tokens * TPOT
  
  Stream metric (latency by token):
    token_1_time = TTFT (key UX moment)
    token_2_time - token_1_time = TPOT_1
    ...
  
  Per-stage OTel spans:
    span.start("rag_retrieve") ... span.end()
    span.start("rerank") ... span.end()
    span.start("llm_prefill") ... span.end()
    span.start("llm_decode") ... span.end()
  ```
- Top 3 gotchas: 混淆 TTFT vs TPOT / 没 stream metric (只看 total) / OTel 没 per-stage span
- Tools: OpenTelemetry, OTLP exporter, Jaeger / Tempo, Grafana

**Problem 2: Diagnostic Tools (Nsight, OTel, vLLM Metrics)**
- 核心解法:
  ```
  vLLM /metrics endpoint:
    num_requests_running, num_requests_waiting (queue depth)
    gpu_cache_usage_perc (KV pressure, > 90% alert)
    num_preemptions_total (slow request killed)
    time_to_first_token_seconds (histogram)
    prefix_cache_hit_rate
  
  Nsight Systems:
    nsys profile -t cuda,nvtx,osrt python serve.py
    See: prefill kernel time, decode kernel time, host-side overhead
  
  PyTorch Profiler:
    with torch.profiler.profile() as prof:
      llm.generate(prompts)
    prof.export_chrome_trace("trace.json")
  
  OTel global setup:
    from opentelemetry import trace
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("rag_retrieve"):
      ...
  ```
- Top 3 gotchas: 没 vLLM /metrics enabled / Nsight 没装就 debug / OTel 全 on full request 浪费
- Tools: vLLM Prometheus, Nsight Systems / Compute, py-spy, PyTorch Profiler

**Problem 3: Optimization Levers**
- 核心解法:
  ```python
  # 1. Continuous batching (vLLM default)
  # 2. Prefix caching
  llm = LLM(model="meta-llama/Llama-3.1-70B", enable_prefix_caching=True)
  # 3. Chunked prefill (decode 不被阻塞)
  llm = LLM(..., enable_chunked_prefill=True, max_num_batched_tokens=8192)
  # 4. Quantization
  llm = LLM(model="...-AWQ", quantization="awq", dtype="float16")
  # 5. Speculative decoding
  llm = LLM(model="70B", speculative_model="7B-draft", num_speculative_tokens=5)
  ```
- Top 3 gotchas: 不知 prefix caching flag (vLLM 0.6 默认 off) / quantization 不 verify quality drop / spec decode accept_rate 没量化
- Tools: vLLM config, AWQ / GPTQ quantized weights, SGLang alternative, TensorRT-LLM 极致

**Problem 4: System Bottlenecks (Network, GPU Memory, KV Cache, Scheduling)**
- 核心解法:
  ```
  Memory bandwidth (decode 主要瓶颈):
    quantize to INT4 → 2x speed
    smaller model + spec decode
  
  Compute (prefill 主要瓶颈):
    prefix cache 50-90% save
    chunked prefill
    shorter prompt
  
  Network (cross-region):
    co-locate gateway with serving
    gRPC > REST
    HTTP/2 multiplexing
  
  KV cache full:
    scale up GPU
    reduce max_output_tokens
    offload to CPU (PagedAttention)
    preempt long-running, return error
  
  Scheduling (FIFO 不 fair):
    custom scheduler for tenant quota
    priority queue for premium tier
    SLO-aware admission control
  ```
- Top 3 gotchas: 不区分 memory vs compute bound / KV cache 满 OOM / scheduling FIFO 一个 tenant 占死
- Tools: vLLM scheduler config, NVLink topology, NVMe for weights, GPU monitoring

**Problem 5: Multi-Stage Pipeline Latency**
- 核心解法:
  ```python
  # Per-stage SLO budget
  budget = {
    'rag': 200, 'rerank': 200, 'llm': 1500, 'tool': 1000, 'post': 100
  }  # ms
  
  # Parallelize independent stages
  rag_task, tool_task = await asyncio.gather(
    rag_retrieve(query),
    tool_call_async(query)
  )
  
  # Cascade routing
  if simple_query(query):
    return await llm.complete(query)  # skip rerank
  else:
    chunks = await rag_retrieve(query)
    chunks = await rerank(chunks)
    return await llm.complete_with_chunks(query, chunks)
  
  # Stream early
  await stream.send("Thinking...")  # ACK immediately
  async for token in llm.stream(prompt):
    await stream.send(token)
  
  # Cache layered
  embedding_cache (1h TTL)
  retrieval_cache (5min TTL, query hash)
  response_cache (30s TTL, full query hash)
  ```
- Top 3 gotchas: 顺序 stage 不 parallelize / 简单 query 全 pipeline 走 / 没 stream ACK 用户卡顿感
- Tools: asyncio.gather, Redis layered cache, streaming SSE / WebSocket

### 🔥 Production gotchas (top 15)

1. 没 per-stage timing 就 debug → 浪费小时猜
2. 上 hardware fix 先 → 钱浪费
3. 不知 vLLM features → 免费 optim 没用
4. 没 GPU memory monitoring → KV cache 满了不知道
5. 没 canary / SLO → 同样问题复发
6. Test fix on 1 request → 生产 load 完全不同
7. Config drift 不 diff → 隐性 regression (vLLM 0.5→0.6 prefix cache 默认 off)
8. 混淆 TTFT vs TPOT → 优化错方向
9. 没 stream ACK → 用户感知 latency 是 TTFT, 不是 total
10. KV cache 满 preempt long-running → P99 显著退步
11. FIFO scheduling 一个 tenant 占死 → 其他 tenant SLO 爆
12. Cold start spike 没 keepalive → 重启后 1 分钟 P99 高
13. 冷数据从 disk 加载 → preload 到 RAM
14. Cross-region call → co-locate, gRPC
15. 没 per-tenant metric → hot tenant 不知道

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| TTFT debug 实战 | Voice agent vLLM 0.5→0.6 升级 | prefix cache 默认 off, TTFT 4x |
| Streaming UX | Voice agent | p99 < 800ms streaming critical |
| vLLM production | Voice agent + BNPL | continuous batching, prefix caching |
| Speculative decoding | Voice agent 70B model | 7B draft accept_rate > 70% |
| OTel per-stage span | Voice agent | day-1 instrumented |
| Multi-stage pipeline | BNPL chatbot | RAG + rerank + LLM + tool parallel |
| Cascade routing | BNPL intent | 简单 skip rerank |
| KV cache management | Voice agent peak load | preemption avoid via scale up |
| Per-tenant SLO | Voice agent 7 markets | quota + priority queue |

### 🎤 面试现场 quotables (top 8)

1. "First action is instrumentation — per-stage OTel spans cost 1ms but save hours of guessing"
2. "TTFT vs TPOT — different bottlenecks, different fixes. Prefix caching for TTFT, quantization for TPOT"
3. "vLLM 0.5→0.6 default changed — prefix caching went from on to off. Voice agent TTFT 4x. Config diff is the first thing I check after a regression"
4. "Diagnostic ladder cheap to expensive — OTel → vLLM metrics → PyTorch Profiler → Nsight Systems → Nsight Compute"
5. "Prefill is compute-bound O(N²), decode is memory-bandwidth-bound. Different bottlenecks, different optimization"
6. "KV cache full at 90%+ → preemption kicks in, P99 explodes. Scale GPU or reduce max output"
7. "Multi-stage agentic — parallelize independent stages, cascade routing for simple queries, stream early ACK so user sees 'Thinking...'"
8. "I'd never test fix on 1 request — production load distribution is completely different. Synthetic canary 100 queries every 5 min"

### 🚨 红线 (top 10 anti-patterns)

1. 没 per-stage timing 就 debug
2. 上 hardware fix 先
3. 不知 vLLM features
4. 没 GPU memory monitoring
5. 没 canary / SLO
6. Test fix on 1 request
7. Config drift 不 diff
8. 混淆 TTFT vs TPOT
9. 没 stream ACK
10. FIFO scheduling 一个 tenant 占死
