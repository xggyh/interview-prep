## Q25 · 诊断 LLM 推理 pipeline 高延迟 (OpenAI 最爱)

> "Your LLM-powered customer support assistant is hitting **p99 latency of 8 seconds**, target is **2.5 seconds**. You have access to the full stack — client SDK, API gateway, tokenizer service, request queue, batch scheduler, GPU inference (Llama-70B on 8x H100 via vLLM), detokenizer, post-process. **Walk me through how you diagnose and fix this.**"

**中文翻译**:

> "你的 LLM 客服助手 **p99 (99 分位) 延迟到了 8 秒**, 目标是 **2.5 秒**. 你能看到全栈 — client SDK, API gateway (网关), tokenizer service (分词服务), request queue (请求队列), batch scheduler (批处理调度器), GPU 推理 (Llama-70B 用 vLLM 跑在 8 张 H100 上), detokenizer (反分词), 后处理. **走我一遍你怎么诊断 + 修.**"

**Round**: System Design (60 min)
**出处**: Exponent 2026 FDE · 公司: OpenAI (almost always) · Anthropic Inference team · 行业: AI infra
**约束**: vLLM / SGLang / TensorRT-LLM / continuous batching / KV cache / FP8 quant / tensor parallel / dynamic batching trade-off

---

## 📖 术语速查 (本题用到的)

> 这题是 LLM inference 内核知识. 不懂术语直接挂 OpenAI/Anthropic 面试. 5 min 看完.

### Latency 指标 (核心)

| 术语 | 解释 |
|---|---|
| **TTFT (Time-To-First-Token)** ⭐ | 第一个 token 出来的时间 — streaming UX 关键指标. |
| **ITL (Inter-Token Latency)** ⭐ | token 之间的间隔 — decode 阶段每步耗时. |
| **E2E latency** ⭐ | end-to-end 全部 token 出完的总时间. |
| **p50 / p95 / p99** | 50% / 95% / 99% 分位的延迟. p99 = 1% 慢请求的延迟. |
| **RPS / QPS** | Requests / Queries Per Second. |
| **Throughput** | 吞吐量 — 单位时间处理的 token / request 数. |
| **Streaming SSE** | Server-Sent Events — token 流式返回, 用户感知比 non-streaming 快很多. |

### Inference 阶段 (核心)

| 术语 | 解释 |
|---|---|
| **Prefill** ⭐ | 输入阶段 — 一次性 forward 所有 input token, 填充 KV cache. compute-bound. |
| **Decode** ⭐ | 输出阶段 — 自回归一次生成一个 token. memory-bandwidth-bound. |
| **Autoregressive** | 自回归 — 每个 token 依赖前面所有 token. |
| **Chunked prefill** | 把长 input 分成多个 chunk, 跟 decode 交错执行. |
| **Compute-bound vs Memory-bound** | 计算瓶颈 vs 内存带宽瓶颈. Prefill 是前者, Decode 是后者. |

### Batching

| 术语 | 解释 |
|---|---|
| **Continuous batching** ⭐ | 持续批处理 — 完成的 sequence 释放 slot, 新 request 即时加入. vLLM/SGLang 核心. |
| **Static batching** | 静态批处理 — 一批一起开始一起结束 (旧). |
| **Dynamic batching** | 动态等待凑批 — 中间态, 不如 continuous. |
| **max_num_seqs** | vLLM 参数 — 同时 in-flight 最大 sequence 数. 调大 throughput ↑ ITL ↑. |
| **max_num_batched_tokens** | 每 step token 上限. |
| **Batch size** | 单次 forward pass 内的 sequence 数. |
| **Slot** | 一个 in-flight sequence 占的位置. |

### KV Cache (核心)

| 术语 | 解释 |
|---|---|
| **KV cache** ⭐ | Key/Value 缓存 — decode 时复用之前 token 的 attention K/V, 避免重算. |
| **PagedAttention** ⭐ | vLLM 发明 — 把 KV cache 像虚拟内存一样分页, 解决碎片化. |
| **RadixAttention** ⭐ | SGLang 的 prefix tree-based KV 共享, 比 vLLM prefix caching 更激进. |
| **Prefix caching** | 共享 system prompt 等公共前缀的 KV cache. |
| **KV eviction** | KV 满了把老 sequence 的 KV 踢出去 (LRU). |
| **KV swap to CPU** | KV 满 fallback 到 CPU 内存 (慢 50×). |
| **H2O / FastGen / KIVI** | KV cache 压缩 / 量化方法. |
| **GQA (Grouped Query Attention)** | 共享 KV 头的 attention 变体 — Llama-70B 用 8 KV 头不是 64. KV size 小 8×. |
| **MHA / MQA** | Multi-Head / Multi-Query Attention — 传统 vs 极端共享. |

### 量化 / 加速

| 术语 | 解释 |
|---|---|
| **FP16 / BF16** | 16-bit 浮点 — baseline. |
| **FP8 (E4M3)** ⭐ | 8-bit 浮点 — Hopper H100 native, 1.5× 加速 / < 1% quality drop. |
| **INT8 / INT4** | 8-bit / 4-bit 整数量化. 更狠. |
| **AWQ (Activation-aware Weight Quantization)** | 按 activation 重要性量化权重的 INT4 方法. |
| **GPTQ** | 另一种 INT4 量化方法. |
| **SmoothQuant** | INT8 量化, 把 outlier 平滑到 activation. |
| **QAT (Quantization Aware Training)** | 训练时就考虑量化, 修正 quant loss. |
| **Speculative decoding** ⭐ | 推测解码 — 小 draft model 一次生成 n 个 token, 大 model 一次 verify. 2× 加速. |
| **Medusa / EAGLE** | 在 model 头上加多个 spec head 的 spec decoding 变体. |
| **Lookahead decoding** | 并行 n-gram 生成. |
| **Draft model** | spec decoding 里的小模型. |
| **Accept rate** | spec decoding 接受率 — 60-80% 算好. |

### Inference Stack

| 术语 | 解释 |
|---|---|
| **vLLM** ⭐ | UC Berkeley 开源, 业界最常用. PagedAttention 发源地. |
| **SGLang** | LMSYS 开源, RadixAttention 强 + structured output. |
| **TensorRT-LLM** ⭐ | NVIDIA 自家 inference 引擎, 性能最强但 lock-in. |
| **TGI (Text Generation Inference)** | HuggingFace 的 inference server. |
| **Triton Inference Server** | NVIDIA 通用推理框架 (不止 LLM). |
| **OpenRouter** | LLM API 聚合层. |

### 并行 / 拓扑

| 术语 | 解释 |
|---|---|
| **Tensor Parallel (TP)** ⭐ | 张量并行 — 把每层切到多个 GPU. 70B TP=8 标配. |
| **Pipeline Parallel (PP)** | 流水线并行 — 不同层在不同 GPU. |
| **Data Parallel (DP)** | 数据并行 — 多 replica. |
| **TP=8** | 8 个 GPU 张量并行. |
| **GPU replica** | 完整模型的一个副本. |
| **NVLink** | NVIDIA GPU 间高速互联. |
| **InfiniBand** | 节点间高速网络. |

### GPU 硬件

| 术语 | 解释 |
|---|---|
| **H100** ⭐ | NVIDIA Hopper 80GB GPU, LLM 推理主流. |
| **H200** | H100 升级版, 141GB 内存. |
| **A100** | 上一代, 40/80GB. |
| **Blackwell B100/B200** | H100 下一代. |
| **TFLOPS** | Tera Floating Point Operations Per Second. |
| **nvidia-smi dmon** | GPU 监控命令. |

### 网络 / 部署

| 术语 | 解释 |
|---|---|
| **TLS handshake** | HTTPS 首次连接的握手 — 50ms 量级. |
| **HTTP/2 multiplex** | HTTP/2 的多路复用. |
| **Keepalive / Connection pool** | 持久连接 — 避免每次 TLS 重握手. |
| **gRPC** | Google RPC 框架, HTTP/2 上的二进制协议. |
| **Region affinity** | 路由到最近 region. |
| **AZ (Availability Zone)** | 可用区. |
| **CDN (Cloudflare / CloudFront)** | 内容分发网络 / 边缘 TLS 终止. |
| **WAF** | Web Application Firewall. |

### 观测

| 术语 | 解释 |
|---|---|
| **OpenTelemetry (OTel)** ⭐ | 跨厂商 observability 标准. |
| **APM (Datadog / Grafana Tempo)** | 应用性能监控. |
| **USE method** | Utilization / Saturation / Errors — 系统瓶颈方法论. |
| **RED method** | Rate / Errors / Duration — 服务级方法论. |
| **GPU utilization** | GPU 使用率 — < 90% 通常说明 batching 没饱和. |

### 路由 / 模型策略

| 术语 | 解释 |
|---|---|
| **Dual-model routing** ⭐ | 双模型路由 — 简单查询走小模型, 复杂走大模型. |
| **Cascade** | 级联 — 小模型先尝试, 失败 escalate 到大模型. |
| **Priority queue** | 优先级队列 — paid > free user. |
| **Preemption** | 抢占 — 高优先 request 把低优先 KV evict. |

### 工具

| 术语 | 解释 |
|---|---|
| **HF tokenizers (Rust)** | HuggingFace Rust tokenizer, 比 Python 快 10×. |
| **SentencePiece / tiktoken** | 两种 tokenization 算法. |
| **FastAPI / Envoy** | Web 框架 / 服务代理. |

---

## 这道题在考什么

OpenAI / Anthropic FDE 最爱这道题, 因为它**测你是否真懂 inference stack**, 不是 black-box "API 调一下":

1. **Stage-by-stage latency attribution** — 8s 是哪个环节, 不能 hand-wave "model 慢"
2. **TTFT vs ITL vs E2E** — 知道 Time-To-First-Token / Inter-Token-Latency / End-to-End 三个不同 metric
3. **Continuous batching 内部机制** — vLLM PagedAttention, prefill vs decode 分离, max_num_seqs
4. **KV cache size + eviction** — 70B model KV size 计算, prefix sharing, RadixAttention (SGLang)
5. **Tokenizer 是 CPU bottleneck** — 多数人忽略, 但 100k token 的 prompt tokenize 可能 200ms
6. **Network + region affinity** — TLS handshake, region cross-link, gRPC vs HTTP/2
7. **Quantization trade-off** — FP8 / INT4 vs quality, AWQ vs GPTQ vs SmoothQuant
8. **菜鸟答案失败点**: "model 慢, 上更小的 model" — too shallow. 没回答 batching / KV cache / 网络 / 量化 / prefill-decode 拆分这些 真正大头.

---

## 必问 clarifying questions

1. **TTFT vs E2E**: 8s 是 streaming first-token 还是 full response? 决定 prefill vs decode 主战场
2. **Average input / output tokens**: 4K in / 500 out 跟 100K in / 100 out 完全不同 bottleneck
3. **Concurrent users**: 10 vs 1000, 影响 batching 效率
4. **GPU 用了几张, model 怎么放**: TP=8 单 model 还是 TP=2 多 replicas
5. **Streaming returned?**: 如果 streaming, TTFT 是关键; 如果 non-streaming, E2E
6. **Model 真的是 Llama-70B?**: 是否可换 Llama-30B 或 8B 满足质量
7. **Region / Network**: client 在 us-east, API 在 us-west? 跨 region 100ms+
8. **Existing metric/trace**: 有 OpenTelemetry / 自建 metric 吗

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|------|------|------|
| 1 | Clarify + decompose | 5 min | TTFT/ITL/E2E 拆 + token shape | "8s 拆成 stage 前: client_send + queue + tokenize + prefill + decode + detokenize + return. 我画 budget" |
| 2 | Telemetry first | 5 min | 加 stage timing + RED + USE | "诊断前先 instrument. OTel span per stage" |
| 3 | Stage diagnosis | 12 min | 7 stage 逐个分析 + 真实数字 | "我假设当前 budget 是这样, 我去 measure 哪个超" |
| 4 | Batching deep dive | 10 min | Continuous batching + max_num_seqs + max_wait_ms | "vLLM continuous batch 是关键, max_wait_ms tradeoff" |
| 5 | KV cache + prefix share | 8 min | 70B KV size 计算 + RadixAttention | "70B KV is huge, prefix cache save 60%+" |
| 6 | Quantization + decode tuning | 6 min | FP8 / INT4 / speculative decode | "FP8 1.5× speed + < 1% quality loss" |
| 7 | Network + topology fixes | 5 min | Region affinity + persistent conn | "TLS handshake 50ms × N call 是隐藏 cost" |
| 8 | Trade-offs + close | 5 min | Quality vs latency vs cost | "8s → 2s 路线: 量化 + batch tuning + KV share + smaller model 兜底" |

---

## 端到端架构图 (ASCII)

```
                            LLM Inference Pipeline (full stack)
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                          │
│  Client (browser / mobile / API consumer)                                                │
│    │                                                                                     │
│    │  [Latency 1] HTTPS request, TLS handshake ~50ms first call, 5ms keep-alive          │
│    ▼                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐         │
│  │ Edge / CDN (Cloudflare / AWS CloudFront)                                    │         │
│  │  ▸ TLS termination                                                          │         │
│  │  ▸ WAF                                                                      │         │
│  │  ▸ Routing to nearest region                                                │         │
│  │   [Latency 2] ~5-20ms                                                       │         │
│  └─────────────────────────────────────────────────────────────────────────────┘         │
│    │                                                                                     │
│    ▼                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐         │
│  │ API Gateway (FastAPI / Envoy)                                               │         │
│  │  ▸ Auth (API key validation, JWT verify)                                    │         │
│  │  ▸ Rate limit (token bucket per user)                                       │         │
│  │  ▸ Schema validation                                                        │         │
│  │   [Latency 3] ~10-30ms (depends on JWT crypto)                              │         │
│  └─────────────────────────────────────────────────────────────────────────────┘         │
│    │                                                                                     │
│    ▼                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐         │
│  │ Tokenizer service (SentencePiece / tiktoken in HF tokenizers Rust)          │         │
│  │  ▸ Convert prompt → token IDs                                               │         │
│  │  ▸ CPU bound, batch friendly                                                │         │
│  │  ▸ Prompt 8K token tokenize ~30-80ms on 1 CPU                               │         │
│  │   [Latency 4] depends on prompt size                                        │         │
│  └─────────────────────────────────────────────────────────────────────────────┘         │
│    │                                                                                     │
│    ▼                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐         │
│  │ Request Router / Queue                                                      │         │
│  │  ▸ Pick GPU replica with most free KV cache                                 │         │
│  │  ▸ Wait if all replicas saturated (queue depth)                             │         │
│  │  ▸ Priority queue (paid > free tier)                                        │         │
│  │   [Latency 5] queue wait can be 0-2000ms under load                         │         │
│  └─────────────────────────────────────────────────────────────────────────────┘         │
│    │                                                                                     │
│    ▼                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐         │
│  │ vLLM / SGLang Inference Server (8x H100, TP=8, Llama-70B FP16)              │         │
│  │                                                                             │         │
│  │   ┌─PREFILL phase (compute-bound)───────────────────────────┐              │         │
│  │   │ Forward pass on all input tokens at once                │              │         │
│  │   │ 8K input × 70B = ~70 ms on 8x H100 BF16                 │              │         │
│  │   │ 32K input → ~280ms (linear in input length)             │              │         │
│  │   │ KV cache populated here                                 │              │         │
│  │   │   [Latency 6 = TTFT contributor]                        │              │         │
│  │   └─────────────────────────────────────────────────────────┘              │         │
│  │                                                                             │         │
│  │   ┌─DECODE phase (memory-bandwidth-bound)─────────────────────┐            │         │
│  │   │ Generate 1 token per pass, autoregressive                 │            │         │
│  │   │ Each token: ~25ms on Llama-70B FP16 single sequence       │            │         │
│  │   │ 500 token gen → 500 × 25 = 12500ms ← BAD                  │            │         │
│  │   │ Continuous batching helps: batch_size=32 → 30ms per step  │            │         │
│  │   │   but each user gets token every 30ms not 25ms              │            │         │
│  │   │   [Latency 7 = ITL × N_tokens contributor]                │            │         │
│  │   └────────────────────────────────────────────────────────────┘            │         │
│  └─────────────────────────────────────────────────────────────────────────────┘         │
│    │                                                                                     │
│    ▼                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐         │
│  │ Detokenizer + Post-process                                                  │         │
│  │  ▸ Token IDs → string (streaming chunks)                                    │         │
│  │  ▸ Safety check / PII redact / citation parse                               │         │
│  │  ▸ Could add 100-500ms if heavy                                             │         │
│  │   [Latency 8]                                                               │         │
│  └─────────────────────────────────────────────────────────────────────────────┘         │
│    │                                                                                     │
│    ▼                                                                                     │
│  Client (final response)                                                                 │
│    [Latency 9] Return path: ~5-20ms                                                      │
└──────────────────────────────────────────────────────────────────────────────────────────┘

   Bottleneck candidates (P99 = 8000ms):
   ┌────────────────────────────────────────────────────────────────────────────┐
   │  ▸ Network + TLS  (cross-region, no keepalive)     200-800ms               │
   │  ▸ Tokenize       (8K prompt, no Rust tokenizer)   50-200ms                │
   │  ▸ Queue wait     (under load, no priority)        0-3000ms ←★ often       │
   │  ▸ Prefill        (32K prompt, no chunked prefill) 100-500ms               │
   │  ▸ Decode         (500 tok × 25ms = 12.5s) ←★ ★ ★ ★ MOST LIKELY            │
   │  ▸ Detokenize     (heavy safety check)             100-500ms               │
   │  ▸ Return         (no streaming)                   ~0 (if streaming) up to TBD│
   └────────────────────────────────────────────────────────────────────────────┘
```

---

## 详细设计 (60-min walkthrough)

### Phase 1: Clarify + decompose (澄清 + 拆解延迟) (5 min)

开口必须先拆 metric, 不要直接 dive 解决:

"8s 是什么? Streaming TTFT? End-to-end 全部 token? 这影响诊断重心. 我假设是 e2e p99, 输入 4K input + 500 output, streaming on. 那 TTFT 应在 1s, decode 1.5s, 共 2.5s budget."

Token shape 关键:
- **4K in, 500 out**: prefill 70ms (8x H100 FP16), decode 主要
- **32K in, 100 out**: prefill 280ms+ 主要, decode 短
- **500 in, 2000 out**: decode 极长, 主要

KPI:
- **p50 < 1.5s, p99 < 2.5s**
- **TTFT < 800ms**
- **ITL (per token) < 30ms streaming**
- **Throughput**: maintain or improve QPS

### Phase 2: Telemetry first (先埋点, 后修) (5 min)

"在诊断前我先 instrument 每个 stage, 不然在猜":

```python
# Add OpenTelemetry spans per stage
@tracer.start_as_current_span("llm.request")
async def handle(req):
    with span("auth"):       await auth_check(req)
    with span("tokenize"):   tokens = await tokenize(req.prompt)
    with span("queue_wait"): replica = await router.pick()  # measure queue
    with span("prefill"):    kv_cache = await replica.prefill(tokens)
    with span("decode_first_token") as s:
        first_tok = await replica.decode_one(kv_cache)
        s.set_attribute("ttft_ms", s.duration_ms)
    with span("decode_rest"):
        rest_tokens = await replica.decode_remaining(kv_cache)
    with span("detokenize"): text = await detokenize(rest_tokens)
```

Dashboards:
- p50/p95/p99 per stage (Datadog APM / Grafana Tempo)
- Histogram: queue_wait_ms, prefill_ms, decode_ms_per_token
- Heatmap: time-of-day vs latency (反映 batching 饱和度)

也要 USE (Utilization / Saturation / Errors):
- GPU utilization (`nvidia-smi dmon`): 应该 ≥ 90% 才说明 compute-bound
- GPU memory: 看 KV cache 占多少, 接近 80% 说明 KV pressure
- Queue depth / wait time

3 hours instrumentation, 数据出来再 talk solutions.

### Phase 3: Stage-by-stage diagnosis (逐阶段诊断) (12 min)

假设 instrument 后看到 p99 breakdown:

```
| Stage          | p50    | p99    | Notes                             |
|----------------|--------|--------|-----------------------------------|
| Network/TLS    | 30ms   | 800ms  | TLS handshake on cold conn        |
| Auth           | 10ms   | 50ms   | OK                                |
| Tokenize       | 40ms   | 200ms  | Python tokenizer, not Rust        |
| Queue wait     | 50ms   | 3000ms | LOAD! main suspect                |
| Prefill        | 80ms   | 300ms  | OK (4K avg, occasional 32K spike) |
| Decode TTFT    | 30ms   | 100ms  | first token after prefill         |
| Decode rest    | 1500ms | 5000ms | 500 tokens × 30ms ITL, vary       |
| Detokenize     | 20ms   | 100ms  | OK                                |
```

Diagnosis:
- **Queue wait p99 3000ms** — 主嫌疑. 系统饱和 + lack of priority.
- **Decode rest p99 5000ms** — 第二大. 500 tokens × 10ms ITL spike (long batch sees stragglers).
- **Network p99 800ms** — TLS handshake on cold connections, missing keepalive.

3 个 issue, 3 个 fix path:

**Fix 1: Queue wait p99 3000ms → < 200ms**

原因: GPU pool 饱和, request 等其他 batch 完成. 选项:
- (a) **Add more replicas** — 8x H100 × 2 = 16 GPUs, double throughput, queue 减半
- (b) **Smaller per-replica batch** — 让 batch slot 释放快, mean queue time 降
- (c) **Continuous batching tuning** — `max_num_seqs` 调高, 让一个 batch 装更多 in-flight
- (d) **Priority queue** — paid tier 优先, free 用户 queue 长

我推 (c) + (d). vLLM `max_num_seqs=256` 默认 64, 如果 KV cache memory 允许, 提到 128.

**Fix 2: Decode rest p99 5000ms → < 1500ms**

500 tokens × 25ms = 12.5s 单 sequence. Continuous batching 把 batch 内每 step ~30ms, decode 同时进行, 实际每个 user 30ms × 500 = 15000ms 看起来更慢, 但 throughput 高.

真正 cut decode latency 的方法:

- (a) **FP8 quantization** — 70B FP8 ~半 size, decode 速度 1.5-1.8× — 15ms ITL → ~7.5ms ITL, 500 × 7.5 = 3.75s, 仍超
- (b) **Smaller model** — Llama-30B FP16 vs 70B, 1.4× faster + cheaper. Quality drop case-by-case.
- (c) **Speculative decoding** — small draft model + 70B verifier, 2-3× faster for accept-heavy cases
- (d) **Tensor parallel + Pipeline parallel mix** — TP=8 already optimal for 70B intra-node
- (e) **KV cache compression** — H2O / FastGen / 8-bit KV cache
- (f) **Continuous batching with larger batch** — batch_size 64 → step 50ms (only +20ms) → throughput 2×
- (g) **Truncate output** — 500 tokens 真的需要吗? `max_tokens=300`?

Best combo: FP8 + speculative decoding + batch tuning → 70B decode 30ms → 12ms ITL → 500 × 12 = 6s → 仍超.

Real cut: + smaller model fallback for 70% queries (low complexity), 30% stays Llama-70B.

Or: prompt engineer to reduce output to 200 tokens average → 200 × 12 = 2.4s ✓

**Fix 3: Network 800ms TLS**

- HTTP/2 keepalive + connection pool — first call 50ms, subsequent 5ms
- Cross-region routing: client routes to nearest API region
- gRPC over HTTP/2 instead of HTTP/1.1 multipart

After fixes: 200ms (queue) + 80ms (prefill) + 1500ms (decode) + 200ms (overhead) = ~2.0s p99 ✓

### Phase 4: Batching deep dive (批处理深度剖析) (10 min)

vLLM Continuous Batching 是关键概念, 多数人不懂:

**Static batching (旧)**:
```
T0: receive 8 requests → batch them → run forward 8 sequence in parallel
T1: req5 finishes 200 tokens early, sits idle waiting for slowest
T2: when slowest done, return all 8
```
Problem: idle waste, latency = slowest sequence

**Continuous batching (vLLM/SGLang)**:
```
T0: receive req1, start prefill+decode
T1: receive req2, slot in same batch
T2: req2 finishes (short response), slot freed
T3: receive req3, slot in batch
T4: req1 keeps decoding while req3 prefilling (chunked prefill)
```

每个 step, scheduler 决定哪些 sequence 加入. 已 done 的 release slot. 这让 GPU utilization 90%+ 但 latency variance 高.

**Key params**:
- `max_num_seqs`: 同时 in-flight 最大 batch size. 大 = throughput 高 + 单 token latency 高
- `max_num_batched_tokens`: 每 step token 上限. Prefill 重的话调小防 stall
- `gpu_memory_utilization`: 给 KV cache 留多少. 0.9 是 sweet spot.
- `swap_space`: 当 KV 满, swap to CPU (slow but fallback)

**Trade-off**:
- 高 `max_num_seqs` (256): throughput up 2×, 但单 user p99 ITL +10ms
- 低 `max_num_seqs` (32): throughput down, 但 ITL 稳定

**Chunked prefill (vLLM v0.4+)**:
- Long input 32K 一次性 prefill 占 GPU 1000ms → 其他 decode 停
- Chunked: 32K 分 4 个 8K chunk, 跟 decode 交错执行
- 牺牲 5-10% throughput, gain stable latency

**Priority + preemption**:
- 高优先 user 可 preempt 低优先, 把 KV cache evict 到 CPU
- 我推: paid > free, 但 free 不 starve (max wait 5s)

### Phase 5: KV cache + prefix sharing (KV 缓存 + 前缀共享) (8 min)

KV cache 在 70B 上巨大, 占 GPU memory 主要部分.

**KV size calculation**:
- Llama-70B: 80 layers × 64 heads × 128 head_dim × 2 (K, V) × 4 bytes (FP16) = ~5 MB per token
- Wait, that's wrong. Actually:
- Layers × heads × head_dim × 2 (KV) × 2 bytes (FP16) per token
- 80 × 8 (GQA, not 64) × 128 × 2 × 2 = ~328 KB per token

(70B uses GQA with 8 KV heads, not 64 like MHA)

- 8K token context: 8000 × 328KB = 2.6 GB KV per sequence
- 80GB H100 × 8 = 640GB total, model takes 140GB (70B FP16), leaves ~500GB for KV
- Theoretical max: 500GB / 2.6GB = ~190 concurrent 8K-context sequences

But in practice GPU memory utilization 0.85 + model + activations, real budget ~400GB, ~150 sequences max.

**Prefix sharing (RadixAttention)**:
- Many requests share system prompt (e.g., "You are a helpful customer support agent...")
- Cache prefix KV once, share across requests
- 4K shared system prompt = 4000 × 328KB = 1.3GB saved per request
- 150 concurrent → 200GB saved → can run 300 concurrent

vLLM has prefix caching, SGLang has RadixAttention (more aggressive tree-based sharing).

**Eviction**:
- LRU per-sequence eviction
- Swap to CPU memory (DRAM), 50× slower 但 fallback
- Better: kick low-priority requests out, fail fast with retry

**KV cache compression**:
- H2O (Heavy Hitter Oracle): keep only important KV slots
- FastGen / KIVI: 4-bit KV cache, 4× more capacity
- Trade-off: quality drop on long context (>16K)

### Phase 6: Quantization + decode tuning (量化 + 解码调优) (6 min)

**Quantization options**:

| Method | Speed-up | Quality | Tool |
|---|---|---|---|
| FP16 (baseline) | 1× | baseline | vLLM default |
| FP8 (E4M3) | 1.5-1.8× | -0.5% | vLLM, TRT-LLM (Hopper required) |
| INT8 (SmoothQuant) | 1.4× | -1-2% | vLLM, TGI |
| INT4 (AWQ / GPTQ) | 1.8-2.2× | -2-5% | vLLM, AutoAWQ |
| INT4 + KV INT8 | 2.5× | -3-7% | TRT-LLM Best Effort |

我推 **FP8 first** — Hopper H100 native, < 1% quality drop, 1.5× decode speedup.

If quality OK, **INT4 AWQ** for 2× speedup.

**Speculative decoding**:
- Draft model (e.g., Llama-8B FP8) generates n_draft=5 tokens
- 70B verifies in 1 forward pass (batched)
- Accept rate 60-80% in chat → 2× effective speedup
- Tool: vLLM `--speculative-draft-model llama-8b-fp8`

**Other decode tricks**:
- **Lookahead decoding**: parallel n-gram generation
- **Medusa / EAGLE**: multi-head spec decoding
- **PagedAttention** (vLLM): KV cache in pages, no fragmentation

**Quality eval after quantize**:
- Don't just trust benchmarks. Run on your real eval set.
- Llama-70B FP8 vs FP16 on customer support: < 0.5% accuracy diff, 1.5× speed
- Llama-70B INT4 vs FP16: 1-2% accuracy diff, sometimes hallucination ↑

### Phase 7: Network + topology fixes (网络 + 拓扑修复) (5 min)

**TLS overhead**:
- Cold connection: 100ms TCP + 50ms TLS handshake = 150ms
- Warm pool: 5-10ms reuse
- Fix: client SDK pool connections (`max_keepalive_connections=100`)

**Region affinity**:
- Client us-east → API us-west = 70ms RTT × 2 (request + response) = 140ms baseline
- Fix: Multi-region API, route by client geo
- Within a region: AZ-aware routing (cross-AZ 1-3ms vs same-AZ 0.1ms)

**Streaming**:
- Non-streaming: wait for all tokens (500 × 30ms = 15s) before client sees anything
- Streaming SSE / chunked: first token in 1s, subsequent every 30ms — perceived MUCH faster
- Always stream user-facing

**gRPC vs HTTP**:
- HTTP/1.1: head-of-line blocking
- HTTP/2 multiplex: ok
- gRPC: ~10% lower overhead for high-frequency calls (internal service-to-service)

**Compression**:
- gzip for response (if streaming, use per-chunk gzip)
- Cuts wire bytes 3-5× for text

### Phase 8: Trade-offs + close (权衡 + 收尾) (5 min)

**Decision 8.1 — Quality vs latency**

| 选项 | Quality | Latency | Cost |
|---|---|---|---|
| Llama-70B FP16 baseline | 100% | 8s ❌ | 8× H100 |
| Llama-70B FP8 + spec decode + batch tune | 99% | 2.5s ✓ | 8× H100 (same) |
| Llama-30B FP8 | 92% | 1.5s ✓✓ | 4× H100 |
| Llama-70B FP16 + smaller batch + more replicas | 100% | 3s | 16× H100 ($$$) |
| Dual-model routing (8B for simple, 70B for hard) | 95% avg | 1.8s | mixed cost |

我推 **dual-model routing** — 70% queries 用 8B (latency 0.5s), 30% complex 用 70B FP8 (2.5s). Average 1.1s, p99 2.5s, quality avg 95%.

**Decision 8.2 — Continuous batching settings**

| Param | Conservative | Aggressive | 我推 |
|---|---|---|---|
| max_num_seqs | 32 | 256 | 128 |
| max_num_batched_tokens | 4K | 32K | 8K |
| gpu_mem_util | 0.8 | 0.95 | 0.9 |
| Chunked prefill | on | on | on |
| Prefix caching | off | on | on |

**Decision 8.3 — Stack: vLLM vs SGLang vs TensorRT-LLM**

| 选项 | Pros | Cons |
|---|---|---|
| vLLM | OSS, easy, large community | Some perf left on table |
| SGLang | RadixAttention 强, structured output 好 | Smaller community |
| TensorRT-LLM | NVIDIA native, fastest | NVIDIA lock-in, ops harder |

我推 **vLLM Phase 1** (容易, 团队 onboard), **TRT-LLM Phase 2** if 需要 last 15% perf.

---

## 关键决策点 (with rationale)

1. **Instrument before fix** — 不知道 bottleneck 在哪 dont guess. OpenTelemetry per stage 是 day 1.

2. **TTFT vs ITL vs E2E 分开看** — Streaming UX 看 TTFT, total budget 看 E2E.

3. **Queue wait 是 #1 嫌疑** — load 大 + lack of priority + small batch size 共谋, 通常占 30-50% of p99.

4. **Continuous batching tuning** — `max_num_seqs` 是 throughput vs latency knob, 不是默认就好.

5. **FP8 first quantization** — Hopper native, 1.5× speedup with < 1% quality, no-brainer.

6. **Prefix caching + RadixAttention** — system prompt 共享是大 win, especially for chat with long system prompt.

7. **Speculative decoding** — 2× decode speedup with no quality loss is rare, worth adding.

8. **Dual-model routing** — 不是所有 query 都需要 70B. 70% 用 8B 是 huge cost + latency win.

9. **Streaming SSE** — non-streaming 是 perception killer, always stream.

10. **Persistent connection pool** — TLS handshake 50ms × N call 是 silent killer.

---

## 数字 (capacity sizing, cost math)

**Hardware (8× H100 80GB):**
- Cost: ~$30/hr on-demand AWS p5, ~$80K/year reserved
- Memory: 8 × 80GB = 640GB
- Compute: 8 × ~3000 TFLOPS FP16 = 24K TFLOPS

**Model size**:
- Llama-70B FP16: 140 GB (TP=8 distributes ~18GB/GPU)
- Llama-70B FP8: 70 GB (~9GB/GPU)
- KV cache budget: 640 - 140 = 500GB FP16, 640 - 70 = 570GB FP8

**Throughput (after tuning)**:
- 8K avg context, batch_size 128 → 50 RPS sustained, ~200 RPS peak
- FP8 + spec decode: 80 RPS sustained, ~320 RPS peak
- Cost per request: $30/hr / (80 RPS × 3600) = $0.0001 + 8B model + IO ≈ $0.002 per request

**Latency budget (target 2.5s p99)**:
| Stage | Budget | After fix |
|---|---|---|
| Network + TLS | 100ms | keepalive |
| Tokenize | 50ms | Rust HF tokenizer batched |
| Queue wait | 200ms | larger batch, priority |
| Prefill | 100ms | chunked prefill |
| Decode TTFT | 50ms | first token after prefill |
| Decode rest | 1800ms | 400 tokens × 4.5ms (FP8 + spec) = 1800ms |
| Detokenize | 30ms | offload PII to async |
| Return | 20ms | streaming |
| **Total** | **2350ms** | ✓ < 2500ms target |

**Cost projection**:
- Before: 8× H100 1 replica, p99 8s, 50 RPS sustained → $80K/yr handles 1.5M req/day
- After: 8× H100 + FP8 + tune, 80 RPS, p99 2.5s → 6.9M req/day on same hardware
- 4.6× capacity, same cost → effective $0.0005 per request

**ROI**:
- Latency fix: $0 hardware change (just config), engineer week 2
- FP8 quant: 1-day work, 1.5× speedup
- Speculative decoding: 2-week eval + deploy, 2× speedup
- Smaller model routing: 4-week complexity, 70% queries cut latency 5×

---

## Gao Xin 简历专属 reframe

1. **TikTok voice agent (vLLM/SGLang, 7 markets, multi-tenant)** — 你直接 deploy 过 vLLM, tune 过 continuous batching, debug 过 production latency. 这道题是你的舒适区.

2. **TikTok PayLater chatbot (RAG + LLM)** — RAG context 长 (4K-32K), 你处理过 long-context latency, prefix caching 你跑过.

3. **BNPL fraud agent multi-model** — 你做过 cascade routing (small model first, escalate to big), dual-model routing 直接 transferable.

4. **Indonesia 7 market deploy** — region affinity / network 你都处理过.

5. **Internal Agent Platform inference platform** — 你 build 过 inference platform, queue + scheduler 你设计过.

reframe: "我做 voice agent 在字节, vLLM + SGLang 我都 prod 用过. 这道题里 queue tuning + FP8 + spec decode 我在公司 deploy 过 Llama-70B 时跑过. 真正 production 经验是: 大概 50% case 是 queue wait, 30% decode tuning, 15% network, 5% 其他. 我会先 instrument 30min 拿数据再 dive."

---

## 5 个 Follow-ups

1. **"FP8 后 quality drop 太多 (-3%), 怎么 mitigate?"** — 答: (a) 用 AWQ INT4 量化更狠 (per-channel calibration), quality drop 1% but worse perf; (b) Mixed precision: keep attention FP16 + MLP FP8 (attention 对 quant 敏感); (c) QAT (quantization aware training) — finetune 修正 quant loss, 但需要训练 cost; (d) 接受 quality drop 改在 dataset / prompt 上补.

2. **"Spec decode accept rate 只有 40% (low), 怎么诊断?"** — 答: draft model 跟 target model 不匹配. (a) Use specifically-distilled draft (Medusa head, EAGLE); (b) Domain-specific: draft on your data finetune; (c) Multi-head spec (n_draft=2 with stagger) accept rate 高; (d) 如果 accept < 50%, spec decode 净亏 (verify cost > save), 关掉.

3. **"GPU memory 80% 还满了, KV cache OOM, 怎么办?"** — 答: (a) Smaller `max_num_seqs`; (b) FP8 KV cache (KIVI); (c) Swap to CPU (slow but fallback); (d) Preempt low-priority requests, return 429; (e) Long context (32K) requests routed to dedicated GPU pool not shared with chat. (f) 长 prompt 切 chunked + prefix share.

4. **"客户问 'why don't you just use GPT-5 API?', 怎么答?"** — 答: 多个原因. (a) Cost: 500K req/day × $0.005 GPT-5 = $2500/day = $900K/yr, vs 我们 self-host 8× H100 $80K/yr. (b) Data privacy: 客户 PHI / PII 不能出 own VPC; (c) Customization: 我们 fine-tune Llama-70B 在客户 data, GPT-5 不行; (d) Latency: GPT-5 API call cross-region 200ms baseline + queueing on OpenAI side variable, 自己 host 可控.

5. **"如果 latency 必须 1s p99, 但 quality 不让降, 物理上能做到吗?"** — 答: 看 input/output size. 100 token in / 50 token out: 可以 (50 × 10ms = 500ms decode, < 1s). 4K in / 500 out: 1s 单 70B 不可能 (decode 即 1.5s+). 出路: (a) 砍 output (`max_tokens=100`); (b) 8B model + better prompting; (c) parallel inference + sampling (e.g., n=3 让 LLM 选最快); (d) 接受 trade-off 跟 PM 谈.

---

## ❌ 死路答法

1. **"用 GPT-5 API"** — 不答 inference stack 知识, OpenAI / Anthropic 必挂.
2. **"上 H200"** — 1.4× memory, perf 提升有限, 不解决 architecture issue.
3. **"砍 model 到 13B"** — 没说 quality trade-off, 没 RCT eval.
4. **"加 cache"** — 不区分 KV cache vs semantic cache vs response cache.
5. **"static batching size 32"** — outdated, continuous batching 是 SOTA.
6. **"INT2 quant"** — quality 崩, 几乎所有 model 不可用.
7. **"vLLM 默认参数好"** — 默认 `max_num_seqs=64`, max_batched_tokens=2K, tune-able.
8. **"streaming 不重要"** — TTFT 直接影响 UX perception, 必须 stream.
9. **"加 GPU 解决"** — 1.5x cost +50%, addressed nothing about per-request latency.
10. **"用 Triton Inference Server"** — generic, no LLM-specific tricks (continuous batch, paged attn).

---

## ✅ 加分项

1. **Instrument first, fix second** — production sense, 不猜
2. **TTFT vs ITL vs E2E 分开** — 显示真懂 streaming UX
3. **KV cache 大小算得出来** (5 MB/token for 70B GQA) — 真懂 model architecture
4. **Continuous batching + chunked prefill + prefix cache** — 现代 inference stack
5. **FP8 first + spec decode + smaller-model routing** — multi-prong, not single hammer
6. **vLLM vs SGLang vs TRT-LLM trade-off** — full ecosystem awareness
7. **Persistent conn / streaming / region affinity** — full stack 看, 不仅是 GPU
8. **Dual-model routing 70%/30%** — staff-level 思维 (cost-quality-latency optimization)
9. **Numbers 给得出来** (640GB H100 cluster, 5MB/token KV, $0.002/req, FP8 1.5× speedup)
10. **Decision matrix (quality vs latency vs cost)** — 不一刀切

---

## 一句话总结

8s → 2.5s 不是 "model 慢上小 model", 是 **instrument 7 stage 后 attack queue wait (continuous batching tune + priority) + decode (FP8 + speculative + smaller batch) + KV (prefix share + paged attention) + network (keepalive + stream + region) + dual-model routing** 多管齐下的 inference systems engineering.

---

## Cheat Sheet

```
Pipeline stages (7):
  1. Network/TLS         100ms (warm) - 800ms (cold)
  2. API gateway/Auth    10-30ms
  3. Tokenize            30-200ms (Rust HF batched)
  4. Queue wait          0-3000ms (★ main suspect)
  5. Prefill             input_tokens × 10us/token (compute bound)
  6. Decode TTFT         ~30ms (one token after prefill)
  7. Decode rest         output_tokens × ITL (mem-bandwidth bound)
  8. Detokenize          20-100ms

Latency metric:
  TTFT = stages 1-6 (streaming UX)
  ITL = decode step time (per token)
  E2E = TTFT + (output_tokens × ITL)

KV cache (Llama-70B GQA):
  ~328 KB/token
  8K context = 2.6 GB per seq
  8× H100 = 640GB total
  Model 140GB FP16, KV ~500GB → ~150 concurrent 8K seq

vLLM tuning:
  max_num_seqs=128 (throughput vs ITL trade)
  max_num_batched_tokens=8K
  gpu_mem_util=0.9
  chunked_prefill=True
  prefix_caching=True

Quantization:
  FP8 (E4M3 on Hopper): 1.5× speedup, < 1% quality drop ← default
  INT4 AWQ: 1.8-2.2× speedup, 1-2% quality drop
  KV INT8 (KIVI): 4× capacity, < 2% quality drop

Speculative decoding:
  Draft Llama-8B FP8 → 70B verify in batch
  Accept 60-80% → 2× effective speedup
  Set up: vLLM --speculative-draft-model

Routing:
  70% queries → Llama-8B (latency 0.5s)
  30% complex → Llama-70B FP8 (2.5s)
  Average: 1.1s, quality avg 95%

Network:
  TLS keepalive (connection pool 100)
  HTTP/2 multiplex
  Region affinity (route by client geo)
  Streaming SSE (always)

Cost (after tune):
  8× H100 = $80K/yr
  80 RPS sustained = 6.9M req/day
  $0.0005/req (vs GPT-5 API $0.005)
  10× cheaper, latency match

Halt criteria:
  p99 > 3.0s for 5 min → page
  TTFT > 1.5s for 5 min → page
  Quality eval drop > 1pp → revert
```
