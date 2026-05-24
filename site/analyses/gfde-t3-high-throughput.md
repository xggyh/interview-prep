## 题目

> "Customer wants to serve a fine-tuned LLM at **1M QPS**, p99 latency < 1s. Walk through your **serving stack**: hardware, software, optimizations."

或追问形态:

> "Why is vLLM faster than naive transformer serving? Walk through PagedAttention + continuous batching."

**出处**: Google FDE T3 LLM infra round 高频题. 你简历明列 vLLM / SGLang / Megatron / DeepSpeed — **这是你强项区**.

**Round**: LLM Infra / Serving (45-60 min)

---

## 这道题在考什么

考你 **LLM serving 实战 + 数学**:

1. **Continuous batching** — vLLM 核心机制, 不是 static padding
2. **PagedAttention** — KV cache 虚拟内存式管理, 24x more concurrent
3. **Prefix caching** — 共享 system prompt + RAG context 复用 KV
4. **Parallelism** — TP / PP / DP / EP 各自适用范围
5. **Speculative decoding** — 小 draft + 大 verifier, latency 2-3x
6. **Quantization** — INT8 / FP8 / INT4 trade-offs, 2026 主流 FP8
7. **Multi-LoRA** — S-LoRA / Punica, 100 个 tenant 1 个 base
8. **Production stack** — vLLM / SGLang / TensorRT-LLM / Triton 选型

这是你简历明确强项 ("voice agent vLLM / SGLang inference, SFT / DPO / RL post-training"). 面试场要 **拿出数据 + 实际部署经验**, 不要只讲概念.

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**vLLM**: UC Berkeley 开源的 LLM serving 引擎. 三大创新: continuous batching (vs static padding), PagedAttention (KV cache 虚拟内存), prefix caching (共享 prefix 跳 prefill). 2026 业界事实标准, deploy 90% LLM workload.

**KV cache**: Transformer 推理时, 每个 token 在每层的 attention 计算需要前面 token 的 key + value tensor. 这些 tensor 在 prefill 阶段算好后 **缓存在 GPU 显存**, decode 时直接复用. 单 request 的 KV cache 占用: `2 × num_layers × num_heads × head_dim × seq_len × batch_size × dtype_size`. 70B model 70 layer × 8K context 大约 5-10 GB per request.

**Prefill vs Decode**: LLM 推理两阶段. **Prefill** = 计算输入 prompt 的所有 token 的 K/V (并行, GPU-bound, 慢但单次). **Decode** = 一次生成 1 个 token (sequential, memory-bound, 快但要重复). Prefill 占 70-80% 时间, 是优化重点.

**TTFT vs TPOT**: **TTFT** (Time To First Token) = 用户感知的首字符延迟, prefill 决定. **TPOT** (Time Per Output Token) = 后续 token 间隔, decode 决定. 不同场景两者权重不同 (voice 重 TTFT, batch 重总吞吐).

---

## 2. 核心问题 (灾难场景)

设想不懂 vLLM, 用 naive PyTorch + transformers 直接 serve 70B model:

**灾难 A — Static batching**:

```
策略: 等 8 个 request 凑齐, padding 到最长, 一起推理
实测:
  - Request 1: 100 token, 等了 5 秒等满 batch
  - Request 2-7: 100 token, 但 batch 里有 1 个 1000 token, 全部 pad 到 1000
  - 浪费: 90% 计算花在 pad token 上
  - 用户体验: 短 prompt 用户也等长 prompt 用户
  - GPU 利用率: 40% (大部分时间等)
  - TTFT: 平均 3s (等 batch + prefill 长 prompt)
```

**灾难 B — KV cache 预分配 max_seq_len**:

```
策略: 每 request 预分配 max_seq_len (e.g., 4096) 的 KV cache 显存
实测:
  - 70B model, 4096 max, FP16: 单 request KV cache 占 ~3 GB
  - H100 80GB - 140GB model weights (FP16, 多 GPU 分摊) = 剩余 ~30GB per GPU
  - 能容纳 concurrent request: 30 / 3 = 10 个
  - 实际多数 request 只用 500 token, 但仍占 4096 内存
  - 浪费: 88% KV cache 内存空着
```

**灾难 C — 不做 prefix cache**:

```
场景: 客服 agent, system prompt + RAG context 共享 3K token, user query 100 token
策略: 每个 request 完整 prefill 3.1K token
实测:
  - Prefill 3.1K token: ~300ms
  - 10K QPS: 每秒 3.1M token prefill
  - 实际 system + RAG context 同样的 token 被算了 10K 次/秒
  - 浪费 95% prefill compute
```

**灾难 D — 不 quantize**:

```
70B model in FP16: 140 GB
H100 80GB: 单卡装不下, 需要 2 卡 TP
要 1M QPS: 假设单 replica 5K tokens/s 输出 → 200K replica → 400K GPU
$3/hr/GPU × 400K = $1.2M / hour = $14B / 年 (荒谬)

正确: FP8 quantization 70B → 70GB, 1 卡 H100 装下. 单卡 throughput 翻倍.
70K replica × $3/hr = $5M / 年. 仍然贵但合理.
```

**正确的 mental model**:

```
6 个 lever 叠加才能达到 production scale:
  1. Continuous batching       (vLLM)       → 5-10x naive
  2. PagedAttention            (vLLM)       → 24x more concurrent
  3. Prefix caching            (vLLM)       → 2-3x for shared prefix
  4. Speculative decoding      (vLLM/SGLang) → 2-3x latency
  5. Tensor parallelism        (Megatron)   → big model 分布式
  6. Quantization              (FP8/INT4)   → 2-4x memory + speed
  
叠加: naive 1x → 优化后 ~100x throughput at same hardware
```

---

## 3. 典型架构图

**Production stack (1M QPS, 70B fine-tuned)**:

```
┌────────────────────────────────────────────────────────────────────┐
│                    Client SDK / Application                        │
└──────────────────────────────┬─────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│           Load Balancer (Envoy / Linkerd / Cloud LB)               │
│  - SSL termination                                                 │
│  - Region routing (close-to-user)                                  │
│  - Rate limit per-tenant                                           │
└──────────────────────────────┬─────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                Routing Layer (Custom / Envoy filter)               │
│  - Conv-aware sticky routing (same conv → same replica)            │
│  - Cost-aware model routing (Flash 90%, Pro 9%, Opus 1%)           │
│  - Per-tenant LoRA selection                                       │
└──────────────────────────────┬─────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │ vLLM Replica │ │ vLLM Replica │ │ vLLM Replica │
        │ TP=8 (H100)  │ │ TP=8 (H100)  │ │ TP=8 (H100)  │
        │ FP8 70B      │ │ FP8 70B      │ │ FP8 70B      │
        │ + 50 LoRAs   │ │ + 50 LoRAs   │ │ + 50 LoRAs   │
        │ PagedAttn    │ │ PagedAttn    │ │ PagedAttn    │
        │ ContinBatch  │ │ ContinBatch  │ │ ContinBatch  │
        │ PrefixCache  │ │ PrefixCache  │ │ PrefixCache  │
        │ SpecDecode   │ │ SpecDecode   │ │ SpecDecode   │
        └──────────────┘ └──────────────┘ └──────────────┘

Across 8 regions × 2000 replicas/region × 8 GPU/replica = 128K H100
Throughput: 128K × ~6K out_tok/s = 768M tok/s ≈ 1M QPS (assuming 500-700 token avg response)

Per-replica spec:
  - 8 × H100 80GB SXM (NVLink full bandwidth)
  - 70B FP8 weights: 70GB → 9GB per GPU (TP=8)
  - KV cache pool: 50GB per GPU available
  - Throughput: ~5-7K output tok/s
  - TTFT (cold): ~400ms; (cache hit): ~150ms
  - TPOT: ~30ms steady state

Auxiliary:
  - Prefix cache: cross-replica? No (each replica has own GPU mem)
  - Soft routing same conv to same replica → 80%+ prefix hit
  - LoRA adapters: S-LoRA, ~50 hot LoRA per replica
```

**Request lifecycle inside vLLM (continuous batching)**:

```
Time T0: 
  Batch state = [req_A: gen tok 5, req_B: gen tok 12]
  Step 1 GPU pass: compute next token for A and B simultaneously
  
Time T1 (10ms later):
  req_C arrives. Insert into batch (prefill).
  Batch state = [req_A: gen tok 6, req_B: gen tok 13, req_C: prefill 200 token]
  Step: prefill C + decode A + decode B in same forward pass
  
Time T2 (10ms later):
  req_B done (hit EOS). Remove.
  req_D arrives.
  Batch state = [req_A: gen tok 7, req_C: gen tok 1, req_D: prefill 500 token]

要点: 每 step 独立调度, 不等 batch 凑齐, 不 padding. GPU 永远 busy.
```

---

## 4. 关键分类表

### 4.1 6 个 throughput lever 对比

| Lever | Throughput gain | Latency impact | Quality impact | 实现工具 |
|---|---|---|---|---|
| **Continuous batching** | 5-10x naive | TTFT 略增 (batch size 大) | None | vLLM, SGLang, TensorRT-LLM |
| **PagedAttention** | 24x more concurrent | None | None | vLLM 原生 |
| **Prefix caching** | 2-3x repeated prefix | TTFT 大幅下降 | None | vLLM, SGLang |
| **Speculative decoding** | 2-3x latency reduction | TTFT 略增 | Same if accept rate > 70% | vLLM 0.6+, SGLang |
| **Tensor parallelism** | Enables 70B+ on multi-GPU | Adds NVLink latency | None | Megatron, vLLM |
| **Quantization (FP8)** | 1.5-2x throughput + 2x memory | None | < 1% benchmark | FP8 native H100, AWQ INT4 |

### 4.2 Parallelism strategies

| Type | 分割什么 | 适用 | 通信成本 |
|---|---|---|---|
| **TP (Tensor Parallelism)** | Attention/FFN weights 跨 GPU | 单 model 装不下 (70B+) | High (every layer, NVLink) |
| **PP (Pipeline Parallelism)** | Layers 跨 GPU | 超大 model (400B+) | Low (per layer boundary) but bubbles |
| **DP (Data Parallelism)** | 不分 model, 多 replica | Replicate 完整 model | None (replicas independent) |
| **EP (Expert Parallelism)** | MoE experts 跨 GPU | Mixtral / DeepSeek MoE | Moderate (gate routing) |
| **SP (Sequence Parallelism)** | 长 sequence 跨 GPU | Long context (1M+ tok) | High (per-token sync) |

Production combo:
- 7B model: 1 GPU, DP only
- 70B FP8: TP=4 (one node) or TP=8 (more headroom)
- 200B+: TP=8 + PP=2 (cross-node)
- 1T+ MoE: TP=8 + EP=8

### 4.3 Quantization 选项

| Method | Precision | Memory | Speed | Quality drop | Tool |
|---|---|---|---|---|---|
| **FP16** | bf16/fp16 | 1x | 1x | 0 | Baseline |
| **FP8** | E4M3 / E5M2 | 0.5x | 1.5-2x | < 0.5% | H100 native, vLLM 0.6 |
| **INT8** | int8 weights, fp16 act | 0.5x | 1.3x | 1-2% | AWQ, GPTQ |
| **INT4** | int4 weights, fp16 act | 0.25x | 2-3x | 2-5% | AWQ, GPTQ |
| **2:4 sparsity** | structured sparse | 0.5x | 1.5x | 0-1% | NVIDIA Ampere+ |
| **FP4** (B100, 2026) | E2M1 | 0.25x | 4x | 2-4% | Blackwell native |

**2026 default**: FP8 for serving (best quality/perf), INT4 for memory-constrained (consumer GPUs).

### 4.4 Serving engine 对比

| Engine | 强项 | 弱项 | 用在 |
|---|---|---|---|
| **vLLM 0.6+** | Continuous batch + PagedAttn + prefix cache 全功能, multi-LoRA, easy ops | 不是 absolute peak throughput | 90% 生产场景 ⭐ |
| **SGLang** | Structured output (JSON, regex), RadixAttention (advanced prefix), multi-LoRA 一流 | 较新, 小生态 | 需要 structured generation, multi-tenant LoRA |
| **TensorRT-LLM** | Absolute peak throughput, NVIDIA tooling | Complex setup, NVIDIA-only, 升级慢 | 极致 throughput, 内部成熟团队 |
| **Triton Inference Server** | Multi-model, multi-framework | 不是 LLM-native | Multi-model deployments (LLM + ranker + embedder) |
| **TGI (Text Generation Inference)** | HuggingFace 生态, 易用 | 性能落后 vLLM | HuggingFace-centric stack |
| **Llama.cpp / MLC** | CPU / consumer GPU | 不适合 prod scale | Edge deployment |

---

## 5. 具体业务场景 (4-5 个深度变体)

### 场景 A: 消费 chatbot — 100K QPS, 低 value per query

```
背景: 你为某 1B+ DAU 电商 app 做 chatbot, 100K QPS sustained, $0.001/call 都贵.

设计:
  Model:    Self-host Llama-3-8B (FP8 quantized → 8GB on 1 GPU)
  Engine:   vLLM 0.6 (continuous batch + PagedAttn + prefix cache)
  Stack:    vLLM cluster on H100 + Envoy LB
  
  Routing:
    Cost-aware: 90% 流量到 8B self-host ($0.05/1M tok)
               9% 到 Gemini 3 Flash ($0.50/1M)
               1% 到 Claude Opus 4.7 ($5/1M) for hard cases

  Cache:
    Semantic cache: 0.92 threshold, 30% hit on FAQ
    Prefix cache: system prompt + tenant context shared, 70% hit
    Result cache: exact query hash, 15% hit

  Throughput per replica:
    8B FP8: ~6K out tok/s × 100 concurrent = 600K tok/s
    100K QPS / 200 tok avg = need 20M tok/s
    Replicas: 20M / 600K = ~35 replicas (35 × 1 H100)

  Cost:
    35 H100 × $3/hr × 24 × 30 = $76K / month for self-host
    + Flash spillover ~$5K
    + Opus spillover ~$5K
    Total: ~$86K / month for 100K QPS sustained
    Per-call: ~$0.000033, 30x cheaper than pure Opus

简历挂钩: 你 voice agent 7 markets 大概类似 scale
```

### 场景 B: 代码助手 — Copilot-like, 1M dev

```
背景: 1M 开发者使用, p99 < 300ms (typing UX), 大 context (open files)

设计:
  Model:    Fine-tuned 70B (FP8) for code completion
  Engine:   vLLM with speculative decoding
  
  Latency 优化:
    Spec decoding: 7B draft + 70B verifier, 70% accept rate → 2.5x speedup
    Prefix cache: same user opens same files → 90% prefix hit
    Sticky routing: conv_id (user session) → 固定 replica, KV cache hit
    Streaming: 首 token 一出就推
    Edge deploy: region closer to user, < 50ms network
  
  Per-language routing:
    Python user → Python-tuned LoRA on same base
    JS user → JS-tuned LoRA
    Multi-LoRA via S-LoRA, base 70B 共享
  
  Throughput:
    Avg completion 50 tok output, 5K tok input
    p99 < 300ms TTFT: spec decoding + prefix cache + edge
    Replicas: per region 200 replicas × 8 region = 1600 H100
  
  Cost amortize: 月费 user, peak 期 graceful degrade smaller model
```

### 场景 C: Voice agent — < 300ms first-token (你简历强项)

```
背景: 7 markets 6 languages, voice call WebSocket, 1K concurrent calls/region

设计:
  Pipeline:
    Audio → ASR (Whisper streaming) → LLM (70B FP8) → TTS streaming → Audio
  
  ASR: Whisper-large-v3 turbo, ~50ms latency per chunk
  
  LLM 优化 (你做过的):
    vLLM + speculative decoding (7B draft, 70% accept rate)
    Sticky routing per call_id (KV cache hit 95% within call)
    Streaming generation: 1 sentence ready → TTS
    Pre-warm: 来电时 ASR/LLM/TTS 已 ready, 不 lazy load
  
  TTS: ElevenLabs / 自托管 XTTS streaming, ~80ms latency per chunk
  
  TTFT 拆解:
    ASR final:        80ms
    LLM TTFT (cached prefix): 150ms
    TTS first chunk:  80ms
    Network roundtrip: 30ms
    Total:            340ms (need < 300ms for ideal UX, 实际 OK)
  
  实测数字 (你的工作经验, 2026 quote):
    voice agent p50 TTFT: 220ms (cached prefix case)
    voice agent p99 TTFT: 380ms (cold start case)
    Acceptance rate spec decode: 72%
    Continuous batching not too aggressive (latency > throughput priority)

简历挂钩: 这就是你 vLLM + SGLang 在 voice agent 的实战
```

### 场景 D: Batch processing — overnight 1M docs summarize

```
背景: Overnight job 跑 1M document summarize, 不在乎 latency, 在乎 throughput + cost

设计:
  Model:    Llama-3-70B FP8 self-host (cheapest)
  Engine:   vLLM with large continuous batches (256-512)
  
  Throughput priority:
    Batch size 大: 全 GPU 利用率最大化
    No spec decoding: 不需要 latency, 反而吞吐降
    Prefix cache: 同 system prompt 跨所有 doc 共享, 90% hit on system+instruction
    Pipeline parallelism: 多 stage (embed → LLM → store)
  
  Cost math:
    Avg doc: 5K input, 500 output token
    Total: 5K × 1M = 5B input tok, 500M output tok
    Self-host Llama-3-70B FP8: ~$0.30 / 1M token
    Cost: 5.5B × $0.30 / 1M = $1650 for the whole batch
    
    Compare to Gemini 3 Flash ($0.50/$3): 5B × $0.50 + 0.5B × $3 = $4000
    Self-host cheaper 60% for batch.
  
  Spot instances: 容灾的 batch (失败可重做), use AWS Spot / GCP Preemptible
    spot H100: $1.5/hr vs on-demand $3/hr (50% off)
  
  Retry / partial: 失败 task DLQ, 不阻塞整 batch
  
  实际跑: 100 H100 × 4hr = 400 GPU-hr × $1.5 spot = $600 + LLM cost = ~$2250
```

### 场景 E: Multi-LoRA serving — 100 fine-tuned tenants

```
背景: 100 个 enterprise 客户, 每客户 fine-tune 自己的 LoRA, 不能 100 个 replica

设计 (S-LoRA / Punica pattern):

  Base model 共享 (70B FP8 on 8 H100):
    ┌───────────────────────────────────────┐
    │ Base 70B weights (shared, fixed)     │ 70 GB
    │                                       │
    │ Active LoRA pool (hot 50 tenants):    │
    │   tenant_001_lora (50 MB)             │
    │   tenant_002_lora (50 MB)             │
    │   ...                                 │
    │   tenant_050_lora (50 MB)             │
    │ Total active LoRA: 2.5 GB             │
    │                                       │
    │ KV cache pool (PagedAttn):            │
    │   ~30 GB                              │
    └───────────────────────────────────────┘
  
  Per-request:
    1. Route by tenant_id, look up LoRA
    2. If LoRA not in hot pool, swap from disk (S3) — adds ~200ms
    3. vLLM applies base + LoRA delta for this request
    4. Multiple tenants in same batch, different LoRAs applied per-request
  
  Cold LoRA cache:
    Hot 50 LoRA in GPU
    Cold 50 LoRA in CPU RAM (LRU)
    Even colder in S3
    Tenant first request: cold load + warm up
  
  vLLM 0.6+ 原生支持: --enable-lora --max-loras 50

实测:
  vs 100 replicas (no LoRA sharing): cost 100x
  S-LoRA: 1 replica serves 100 LoRA, cost 1x
  LoRA swap overhead: ~50ms (in-GPU swap) to 200ms (CPU → GPU swap)
  Quality vs separate: < 0.1% difference

简历挂钩: 你 voice agent 7 markets 可能就是 multi-LoRA (per-market 定制)
```

---

## 6. 工程 checklist

**设计 LLM serving stack**:

1. **Model size + parallelism** — 7B (1 GPU DP), 70B (TP=8 single node), 200B+ (TP + PP cross-node)
2. **Engine choice** — vLLM default; SGLang if structured output / heavy LoRA; TensorRT-LLM if peak throughput
3. **Quantization** — FP8 default 2026 (H100 native), INT4 if memory-bound
4. **Hardware** — H100 80GB 主力, H200 144GB 大内存场景, B100 (2026) FP4 native
5. **Continuous batching** — vLLM default ON, tune `max_num_seqs` (256-512)
6. **PagedAttention** — vLLM default, `block_size=16` token default
7. **Prefix caching** — `--enable-prefix-caching`, hash 前缀自动复用
8. **Speculative decoding** — `--speculative-model llama-3-8b` for latency wins
9. **Multi-LoRA** — `--enable-lora --max-loras 50` (if multi-tenant fine-tunes)
10. **Routing** — Envoy + custom filter for cost-aware + sticky-by-conv-id

**Observability**:

1. **TTFT p50/p95/p99** — user-perceived latency
2. **TPOT p50/p95/p99** — generation speed
3. **Batch size avg / max** — utilization
4. **KV cache utilization** — memory pressure
5. **Prefix cache hit rate** — how much prefill saved
6. **Speculative decoding accept rate** — quality of draft
7. **GPU util % per replica** — capacity planning
8. **Queue depth per replica** — backpressure
9. **Token cost per request** — $ tracking
10. **Eval pass rate (sampled)** — quality drift

**Autoscaling**:

1. **Predict load 5-15min ahead** (time-of-day patterns) — prewarm GPUs
2. **Pre-allocated buffer 20%** — burst absorber
3. **Cold start mitigation** — model weights loaded, KV cache warm via canary traffic
4. **Burst spillover** — overflow to API-based model
5. **Graceful degradation** — smaller model under load

---

## 7. 易错坑表

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **Naive batching (static padding)** | 5-10x throughput loss, GPU util 40%. 解: vLLM continuous batching |
| 2 | **Pre-allocate KV per request max_len** | 88% memory 浪费. 解: PagedAttention 动态分页 |
| 3 | **No prefix cache for FAQ / shared system prompt** | 2-3x prefill 浪费. 解: `--enable-prefix-caching` |
| 4 | **One GPU per replica for 70B** | 装不下 (140GB FP16 > 80GB H100). 解: TP=4 or TP=8 |
| 5 | **No quantization** | 2x cost + 50% slower. 解: FP8 (默认 2026) |
| 6 | **No autoscaling pre-warm** | Cold start 1-5 min, burst 失败. 解: predictive + 20% buffer |
| 7 | **No quality eval per optim** | Quantization / spec decode 静默 regression. 解: 5% A/B baseline |
| 8 | **Speculative decoding accept rate < 50%** | Latency 不降反升 (verify cost > prefill cost). 解: tune draft model, target 70%+ |
| 9 | **Multi-tenant 没 LoRA sharing** | 100 replica 100x cost. 解: S-LoRA, 1 replica serve N LoRA |
| 10 | **Sticky routing 没考虑 KV cache locality** | Cache hit 30% vs 80%. 解: 按 conv_id soft sticky |

---

## 一句话总结 (Part 1)

> **1M QPS 70B LLM serving** = vLLM continuous batching (5-10x naive) + PagedAttention (24x more concurrent) + Prefix cache (2-3x shared prefix) + FP8 quantization (1.5-2x perf + 2x memory) + TP=8 parallelism (装下 70B) + Multi-LoRA (per-tenant fine-tune 共享 base) + Sticky routing per conv_id (KV cache locality).
>
> 6 个 lever 叠加, 同硬件 throughput 提升 ~100x. 不叠加任何一个都做不到 1M QPS.

---

# Part 2 · 5 个深度工程问题

## ⚙️ Problem 1: Continuous Batching + PagedAttention 数学

vLLM 的两大核心. 把数学讲明白 = 面试官知道你真懂.

### 1.1 Static padding 的浪费

```python
# Naive PyTorch batching
def naive_batch_inference(prompts):
    # Tokenize and pad all to max length
    max_len = max(len(p) for p in prompts)
    batch = []
    for p in prompts:
        tokens = tokenize(p)
        padded = tokens + [PAD] * (max_len - len(tokens))
        batch.append(padded)
    
    # Single forward pass on padded batch
    return model(batch)

# 实例:
prompts = [
    "Short",                    # 1 token (after tokenize)
    "Medium length prompt",     # 3 tokens
    "Very long prompt with lots of words ...",   # 1000 tokens
]
# max_len = 1000
# Compute: 3 × 1000 = 3000 token-passes
# Actual content: 1 + 3 + 1000 = 1004 token-passes
# Waste: (3000 - 1004) / 3000 = 67% pad compute
```

### 1.2 Continuous batching 机制

vLLM 调度器在每个 GPU step (一个 token forward) 独立调度:

```python
class ContinuousBatcher:
    """Simplified vLLM scheduler"""
    
    def __init__(self):
        self.running = []        # Currently in-batch
        self.waiting = []        # Queued (prefill needed)
        self.max_batch = 256
    
    def step(self):
        # Each GPU step:
        
        # 1. Admit new requests (prefill in this step)
        while self.waiting and len(self.running) < self.max_batch:
            req = self.waiting.pop(0)
            self.running.append(req)
            req.state = 'prefill'  # this step will prefill
        
        # 2. Single forward pass: prefill + decode interleaved
        outputs = model.forward([req.next_input() for req in self.running])
        
        # 3. Update each request's state
        for req, out in zip(self.running, outputs):
            req.append_token(out)
            if req.state == 'prefill':
                req.state = 'decode'  # next step is decode
            if req.is_done():
                self.running.remove(req)
                req.complete()
        
        # Continue with next step (new requests can join, old can leave)
```

**关键洞察**: prefill 和 decode 在同一 batch 同一 forward pass 里. 不需要等 batch 凑齐 prefill, 也不需要等所有 request 同时 decode.

### 1.3 PagedAttention 数学

KV cache 大小:

```
Per layer per token KV size:
  2 (K + V) × num_heads × head_dim × dtype_size
  
Llama 3 70B:
  num_layers = 80
  num_heads = 64
  head_dim = 128
  dtype = FP16 (2 bytes)
  
Per token KV: 2 × 64 × 128 × 2 = 32768 bytes = 32 KB
Per token full model: 80 × 32 KB = 2.56 MB
For 4096 token request: 2.56 MB × 4096 = 10.5 GB per request !!!
```

Naive: 预分配 max_len = 4096 → 每 request 10.5 GB → H100 80GB 装 7 个 request

PagedAttention:

```
Block size: 16 tokens (vLLM default)
Per block KV: 2.56 MB × 16 = 41 MB per block per layer? No wait
Per block: 32 KB × 16 = 512 KB per layer per block
Per block all layers: 80 × 512 KB = 40 MB per block

Allocate blocks on demand:
  Request with 500 token actual: needs 500/16 = 32 blocks
  Memory: 32 × 40 MB = 1.28 GB (not 10.5 GB!)

H100 80GB - 9 GB model (TP=8) = 71 GB available
71 GB / 1.28 GB avg = 55 concurrent requests
vs naive 7 → 8x more concurrent
```

实际 vLLM 报 24x 是因为很多 request 短得多 (avg 200 tok), block 边界 share, fragmentation 小:

```
Request with 200 tokens: 13 blocks × 40 MB = 520 MB
71 GB / 520 MB = 136 concurrent requests

vs naive (pre-alloc 4096): 71 / 10.5 GB = 6 requests
Improvement: 136 / 6 = 22.7x
```

### 1.4 Block table 实现

```python
class PagedAttention:
    def __init__(self):
        # Physical memory pool (pre-allocated GPU blocks)
        self.physical_blocks = AllocPool(num_blocks=10000, block_size=16)
        
        # Per request logical → physical mapping
        self.block_tables = {}   # request_id → [phys_block_id, ...]
    
    def allocate(self, req_id, num_tokens):
        num_blocks_needed = (num_tokens + 15) // 16
        already_have = len(self.block_tables.get(req_id, []))
        new_blocks_needed = num_blocks_needed - already_have
        
        new_block_ids = self.physical_blocks.alloc(new_blocks_needed)
        self.block_tables.setdefault(req_id, []).extend(new_block_ids)
        return self.block_tables[req_id]
    
    def free(self, req_id):
        if blocks := self.block_tables.pop(req_id, None):
            self.physical_blocks.free(blocks)
    
    def attention(self, req_id, query):
        # Look up physical blocks, do attention over scattered memory
        block_ids = self.block_tables[req_id]
        return paged_attention_kernel(query, block_ids, self.physical_blocks)
```

### 1.5 Prefix caching via block sharing

PagedAttention 让 prefix sharing 几乎免费:

```
Request A: [system prompt 200 tok] + [RAG 1000 tok] + [user query 100 tok]
Request B: [system prompt 200 tok] + [RAG 1000 tok] + [different query 100 tok]

Block 0 (sys prompt 0-15):   shared between A and B
Block 1 (sys prompt 16-31):  shared
...
Block 75 (RAG 1184-1199):    shared
Block 76 (A's query 0-15):   A only
Block 77 (B's query 0-15):   B only

vLLM 用 hash chain:
  block_0.hash = hash(tokens[0:16])
  block_1.hash = hash(tokens[16:32], block_0.hash)  # chained
  ...
  
A 来时: 全 prefill, cache 所有 block
B 来时: 查 hash, block 0-75 cache hit (跳过 prefill), 只 prefill 76 (B 的 query)
```

实际节省:

```
Without prefix cache:
  Request A prefill: 1300 tokens × 30ms/1000 = 39ms
  Request B prefill: 1300 tokens × 30ms/1000 = 39ms
  Total: 78ms

With prefix cache:
  Request A prefill: 1300 tokens × 30ms/1000 = 39ms (cache miss, fill cache)
  Request B prefill: 100 tokens × 30ms/1000 = 3ms (1200 cached, only B's query)
  Total: 42ms
  
Saving: 46% prefill time
```

对于 100 concurrent users 同 system + RAG:
- 第 1 个 user 39ms
- 第 2-100 user 3ms each (cache hit)
- Avg: ~4ms per user
- vs no cache: 39ms per user
- **10x speedup for shared-prefix workloads**

### 1.6 Tune-able parameters

```bash
# vLLM serve command
vllm serve meta-llama/Llama-3-70B-Instruct \
  --tensor-parallel-size 8 \           # TP=8 H100
  --quantization fp8 \                  # FP8 weights
  --max-num-seqs 256 \                  # max batch size
  --max-num-batched-tokens 16384 \      # tokens per step (prefill + decode combined)
  --enable-prefix-caching \             # prefix cache ON
  --block-size 16 \                     # PagedAttention block
  --gpu-memory-utilization 0.95 \       # use 95% GPU mem
  --speculative-model meta-llama/Llama-3-8B-Instruct \
  --num-speculative-tokens 5 \
  --enable-lora \
  --max-loras 50
```

---

## ⚙️ Problem 2: Parallelism — TP / PP / DP / EP, When Each

70B+ 模型必须 distributed, 但用哪种 parallelism 是 trade-off.

### 2.1 Tensor Parallelism (TP) — 主力

```
70B FP16 = 140 GB
H100 80 GB 装不下 → 必须 split

TP 思路: Linear layer 矩阵按列 split
  Y = X @ W
  W shape: [hidden, 4*hidden] (FFN up projection)
  
  Split across N GPU:
    GPU 0: Y[:, 0:hidden] = X @ W[:, 0:hidden]
    GPU 1: Y[:, hidden:2*hidden] = X @ W[:, hidden:2*hidden]
    ...
  
  Aggregate: AllGather (combine all GPUs' partial Y)

Communication: per layer, AllGather + AllReduce
  Latency: NVLink ~5us per AllReduce
  Bandwidth: NVLink 900 GB/s
  Per layer overhead: ~50us
  70 layer × 50us = 3.5ms overhead per forward
  
Acceptable when: model splits cleanly, NVLink available
Bad when: cross-node (PCIe 50 GB/s, far slower than NVLink)
```

### 2.2 Pipeline Parallelism (PP) — for超大 model

```
PP 思路: 层按 stage split
  Stage 0: layer 0-19    on GPU 0
  Stage 1: layer 20-39   on GPU 1
  Stage 2: layer 40-59   on GPU 2
  Stage 3: layer 60-79   on GPU 3

Forward:
  Token in → Stage 0 → activation → Stage 1 → ... → Stage 3 → output

Problem: "bubbles" — Stage 1 等 Stage 0 finish before start
  Solution: micro-batching, 切 batch 成 small batch, pipeline 起来

PP 优点:
  - 每 layer 内部不需要 cross-GPU comm
  - 只有 stage boundary 通信
  - 适合 cross-node (PCIe / InfiniBand 100 Gbps OK for stage boundary)

PP 缺点:
  - Latency 增加 (要走完所有 stage)
  - Bubble 浪费 GPU cycle
  - Generation 时尤其问题 (每 token forward, bubble 占比大)

适用: 400B+ model 或 cross-node serving
不适用: < 100B model (TP 就够)
```

### 2.3 Data Parallelism (DP) — 多 replica

```
DP 思路: 不拆 model, 多 replica 独立工作
  Replica 0: 完整 model, serve request 1-256
  Replica 1: 完整 model, serve request 257-512
  ...
  
通信成本: 0 (replica 之间不通信)
扩展: 线性 — N replica = N x throughput

适用: model 装得下单 node (e.g., 70B FP8 + TP=8 单 node)
推荐: 1 replica = 1 node (8 H100 TP), N replicas = N nodes (DP)
```

### 2.4 Expert Parallelism (EP) — for MoE

```
MoE (Mixtral 8x22B, DeepSeek):
  Each layer has 8 experts (e.g., 8 separate FFN)
  Gate router picks top-2 experts per token
  Different tokens → different experts

EP 思路: experts 跨 GPU split
  GPU 0: Expert 0, 1
  GPU 1: Expert 2, 3
  GPU 2: Expert 4, 5
  GPU 3: Expert 6, 7

通信: AllToAll (token → expert routing, expert outputs → token)
  Heavy when token batch large and routing uneven

适用: MoE only (Mixtral, DeepSeek-V3, Llama-4 MoE variants)
```

### 2.5 Combinations in practice

```
Setup 1 (7B Llama):
  DP only, 1 GPU per replica, N replicas

Setup 2 (70B Llama FP8, single node):
  TP=8 (one 8-H100 node)
  DP across nodes (N nodes = N replicas)
  
Setup 3 (200B model, cross-node):
  TP=8 within node
  PP=2 across nodes (2 nodes per replica)
  DP across replica groups

Setup 4 (Mixtral 8x22B MoE):
  TP=8 for attention
  EP=8 for experts
  Within single node

Setup 5 (Long context 1M token):
  TP=8 for model
  SP (Sequence Parallelism) for context split across GPUs
```

### 2.6 Selection rule

```
if model_size_fp8 < gpu_memory:
    return "DP only"
elif model_size_fp8 < node_memory (8 × 80GB = 640GB):
    return "TP within node + DP across nodes"  # most common
elif model_size_fp8 > node_memory:
    return "TP=8 within node + PP across nodes + DP across replica groups"

if model_type == "MoE":
    add "EP for experts"

if avg_context_len > 100K:
    consider "SP for long sequences"
```

### 2.7 实际 70B Llama-3 FP8 setup

```bash
# 1 replica = 8 H100 (TP=8), one node
vllm serve meta-llama/Llama-3-70B-Instruct \
  --tensor-parallel-size 8 \
  --pipeline-parallel-size 1 \
  --quantization fp8 \
  --max-num-seqs 256 \
  --gpu-memory-utilization 0.95

# Capacity:
# 70B FP8 = 70 GB
# Per GPU: 9 GB model + 5 GB activation + 50 GB KV cache pool + ~15 GB headroom = 80 GB ✓
# Throughput: ~5-7K output tok/s

# Scale: N nodes for N replicas (DP)
# 200 replicas = 1600 H100 = 200 nodes
```

---

## ⚙️ Problem 3: Cache Hierarchy — Prefix / Semantic / Result, Server vs Client

LLM serving 有多层 cache, 每层节省不同 cost.

### 3.1 Cache 4 tier

```
L1: Result cache         (exact query → exact answer)
L2: Semantic cache       (similar query → previous answer)
L3: Prefix cache         (server-side KV cache, vLLM)
L4: Tool output cache    (idempotent reads in agentic flow)

Different layers, different lifetimes, different hit rates.
```

### 3.2 Layer 1: Result cache (exact)

```python
class ExactCache:
    async def lookup(self, query, conv_id, model_version):
        key = hashlib.sha256(
            f"{query}|{conv_id}|{model_version}".encode()
        ).hexdigest()
        return await redis.get(f"result:{key}")
    
    async def set(self, query, conv_id, model_version, response):
        key = hashlib.sha256(...).hexdigest()
        await redis.set(f"result:{key}", response, ex=3600)

# Hit rate: 10-20% on chat (repeat queries)
# 100% accurate, 0 cost when hit
```

### 3.3 Layer 2: Semantic cache

```python
class SemanticCache:
    def __init__(self):
        self.vector_db = QdrantClient(...)
    
    async def lookup(self, query):
        emb = await embed(query)   # text-embedding-3-small, $0.02/1M
        hits = await self.vector_db.search(
            emb,
            top_k=3,
            filter={"deprecated": False},
        )
        for hit in hits:
            if hit.score > 0.95:   # threshold
                # Optional: cheap LLM (Haiku $1/1M) verify
                verified = await self.verify(query, hit.payload["query"])
                if verified:
                    return hit.payload["response"]
        return None
    
    async def set(self, query, response):
        emb = await embed(query)
        await self.vector_db.upsert(
            id=str(uuid.uuid4()),
            vector=emb,
            payload={"query": query, "response": response, "ts": time.time()},
        )

# Hit rate: 30-50% on FAQ workloads
# Cost: embedding $0.02/1M query (cheap), no LLM call when hit
# Risk: wrong-hit if threshold loose
```

### 3.4 Layer 3: Prefix cache (vLLM server-side)

Already covered in Problem 1. Key points:

```
- Server-side, automatic with --enable-prefix-caching
- Hash 前缀 block, 复用 KV cache
- Hit rate 60-90% for shared system prompt / RAG
- Pass conversation_id hint for sticky routing → better hit
- 节省 prefill cost, decode 不变
```

### 3.5 Layer 4: Tool output cache (agentic)

```python
class ToolCache:
    """Cache for tool calls in agent loop"""
    
    async def call_tool(self, tool_id, args):
        tool = TOOL_REGISTRY[tool_id]
        
        if tool.cache_policy == "no_cache":
            return await self._execute(tool_id, args)
        
        if tool.cache_policy == "user_isolated":
            cache_key = f"tool:{tool_id}:user:{current_user.id}:{hash(args)}"
            ttl = tool.cache_ttl
        elif tool.cache_policy == "global":
            cache_key = f"tool:{tool_id}:{hash(args)}"
            ttl = tool.cache_ttl
        
        if cached := await redis.get(cache_key):
            metrics.incr('tool_cache.hit', tags={'tool': tool_id})
            return cached
        
        result = await self._execute(tool_id, args)
        await redis.set(cache_key, result, ex=ttl)
        return result

# Tool TTL examples:
# get_user_info: 5 min (rarely changes)
# get_inventory: 60s (stale OK)
# get_stock_price: 5s (volatile)
# create_order: NO CACHE (write op)
```

### 3.6 Total cost stacking

```python
# Cost stack for a typical request
async def serve(query, conv_id):
    # L1 exact
    if cached := await exact_cache.lookup(query, conv_id):
        return cached   # cost: $0, latency: 5ms
    
    # L2 semantic
    if cached := await semantic_cache.lookup(query):
        return cached   # cost: $0.02/1M embed, latency: 30ms
    
    # L3 LLM call (with prefix cache hint on server)
    response = await llm.generate(
        query,
        conversation_id=conv_id,
        extra={"prefix_cache_hint": True},
    )
    # cost: depends on prefix cache hit
    # If 90% prefix hit: ~$0.0003/call (Llama 70B self-host)
    # If miss: ~$0.003/call (10x for full prefill)
    # latency: 200-500ms
    
    await exact_cache.set(query, conv_id, response)
    await semantic_cache.set(query, response)
    return response

# Aggregate effect:
# L1 hit: 15% → $0 × 15% = $0
# L2 hit: 35% (of L1 miss) → $0.02/1M × 35% × 85% = ~$0
# L3 hit (prefix): 80% (of L2 miss) → $0.0003 × 80% × 0.85 × 0.65 = $0.00013/req
# Full LLM: 20% (no prefix hit) → $0.003 × 20% × 0.85 × 0.65 = $0.00033/req
# Total avg: ~$0.0005 per request

# vs no caching: $0.003 per request
# Saving: 83%
```

### 3.7 Cache 失效

```python
# Per-tier invalidation strategy

# L1 exact: TTL only (1h default)
#   Updates require: explicit invalidation by event

# L2 semantic: TTL + content version
#   When source content changes, increment version, all old cache stale
#   Or: invalidate by event

# L3 prefix: 
#   vLLM auto-evict (LRU)
#   No manual invalidation needed

# L4 tool: TTL per tool + event-based for critical
#   get_inventory: 60s TTL + invalidate on stock event
#   get_balance: 5s TTL (high freshness need)

async def invalidate_on_event(event_type, entity_id):
    if event_type == "user.email_changed":
        # Invalidate all caches keyed by user
        await redis.delete_pattern(f"tool:get_user_info:user:{entity_id}:*")
        await redis.delete_pattern(f"result:*user:{entity_id}*")
        # L3 prefix cache: not user-tagged, OK to leave
```

---

## ⚙️ Problem 4: Speculative Decoding + Quantization Trade-offs

两个 advanced 优化, latency 大杀器.

### 4.1 Speculative decoding 原理

```
Naive decoding:
  Step 1: 70B model → 1 token (slow)
  Step 2: 70B model → 1 token
  Step 3: 70B model → 1 token
  ...
  
Speculative:
  Draft model (7B fast) proposes K tokens at once (e.g., K=5)
  Verifier model (70B) evaluates all K in parallel
  Accept until first divergence
  
Step 1: 7B → propose [t1, t2, t3, t4, t5]   (5ms, small model)
Step 2: 70B → verify [t1, t2, t3, t4, t5]   (50ms, parallel forward)
  Result: accept [t1, t2, t3] (first 3 match), reject [t4, t5]
  Got 3 tokens in 55ms
  
vs naive: 3 tokens × 50ms = 150ms
Speedup: 150/55 = 2.7x
```

### 4.2 Accept rate 数学

```python
def expected_speedup(accept_rate, K=5):
    """
    K: number of speculative tokens
    accept_rate: P(draft matches verifier per token)
    
    Expected accepted tokens per step ≈ sum_{i=0..K} accept_rate^i
    (geometric-like)
    """
    expected_accepted = 0
    for i in range(K):
        expected_accepted += accept_rate ** i
    
    # Cost per step: draft (5 token) + verify (1 forward) ≈ 1.05x of 1 verify
    # Speedup = expected_accepted / 1.05
    return expected_accepted / 1.05

# Examples:
expected_speedup(0.5, K=5)   # ~1.85x
expected_speedup(0.7, K=5)   # ~2.74x
expected_speedup(0.8, K=5)   # ~3.4x
expected_speedup(0.9, K=5)   # ~3.95x

# If accept_rate < 50%, speedup degrades because verify cost > savings
```

### 4.3 Selecting draft model

```
Same family (recommended): Llama 3 8B draft for Llama 3 70B verify
  Accept rate: 70-80% typical
  Training: distillation or shared tokenizer ensures alignment

Different family: bad accept rate (30-40%), often no speedup

EAGLE / Medusa: small draft head on top of verifier model
  Accept rate: 80-90%
  Less GPU mem (vs separate model)
  Slightly worse than dedicated 7B draft, but cheaper to deploy
```

### 4.4 vLLM speculative decoding config

```bash
vllm serve meta-llama/Llama-3-70B-Instruct \
  --speculative-model meta-llama/Llama-3-8B-Instruct \
  --num-speculative-tokens 5 \
  --speculative-disable-by-batch-size 16    # disable if batch large (overhead not worth)
```

### 4.5 Quantization 深入

```
FP16 (baseline):
  Weights: 16-bit float
  Activations: 16-bit
  70B → 140 GB
  Quality: baseline

FP8 (E4M3 / E5M2):
  H100 native, 8-bit float with exponent + mantissa
  Weights + activations both can be FP8
  70B → 70 GB (50% memory)
  Throughput: 1.5-2x (FP8 matrix multiply faster)
  Quality drop: < 0.5% on benchmark
  2026 default for serving

INT8 (W8A16 or W8A8):
  Weights int8, activations fp16 (W8A16) — most common
  Or both int8 (W8A8) — for absolute max throughput
  70B → 70 GB
  Throughput: 1.3x
  Quality: 1-2% drop

INT4 (AWQ / GPTQ):
  Weights 4-bit int, scale factors
  Activations fp16
  70B → 35 GB (fits 1 H100 with TP=4)
  Throughput: 2-3x
  Quality: 2-5% drop (depends on tuning)
  Use when: memory constrained, OK with quality drop

FP4 (Blackwell B100, 2026):
  4-bit float, hardware-accelerated
  70B → 35 GB
  Throughput: 4x vs FP16
  Quality: 2-4% drop
  Available 2026 with B100
```

### 4.6 Quantization 实战 (AWQ INT4)

```python
# Pre-quantize model offline
from awq import AutoAWQForCausalLM

model = AutoAWQForCausalLM.from_pretrained("meta-llama/Llama-3-70B-Instruct")
model.quantize(
    quant_config={
        "zero_point": True,
        "q_group_size": 128,
        "w_bit": 4,
        "version": "GEMM",
    },
    calib_data=load_calibration_set(),   # 128-512 examples representative
)
model.save_quantized("./llama-3-70b-awq-int4")

# Serve with vLLM
# vllm serve ./llama-3-70b-awq-int4 --quantization awq
```

### 4.7 Quality A/B for quantization

```python
# Always A/B test quantization before prod
async def eval_quantization(baseline_model, quant_model, eval_set):
    results = []
    for example in eval_set:
        baseline_resp = await baseline_model.generate(example.prompt)
        quant_resp = await quant_model.generate(example.prompt)
        
        # LLM judge
        baseline_score = await judge.score(baseline_resp, example.expected)
        quant_score = await judge.score(quant_resp, example.expected)
        
        results.append({
            "example_id": example.id,
            "baseline_score": baseline_score,
            "quant_score": quant_score,
            "diff": quant_score - baseline_score,
        })
    
    avg_diff = mean([r["diff"] for r in results])
    p10_diff = percentile([r["diff"] for r in results], 10)
    
    # Acceptable: avg < 1% drop, p10 < 5% drop
    return {
        "avg_quality_drop": -avg_diff,
        "worst_case_drop": -p10_diff,
        "decision": "deploy" if avg_diff > -0.01 and p10_diff > -0.05 else "investigate",
    }
```

简历挂钩 (你的强项):

> "On voice agent 70B model, we tested FP8 vs FP16: avg eval drop 0.3%, worst case 1.2%. Deployed FP8 — same hardware can serve 2x concurrent calls. Tested INT4 AWQ: avg drop 1.8%, kept as 'budget tier' for non-premium markets."

---

## ⚙️ Problem 5: Multi-LoRA Serving — S-LoRA / Punica, Hot LoRA Cache

100+ tenant 每个有 fine-tuned LoRA, 但用 100 个 replica 太贵. 这是 multi-tenant LLM 经典问题.

### 5.1 LoRA 概念

```
Base model: 70B weights (frozen)
Per tenant: LoRA adapter (~50-100 MB), small rank delta matrices

For tenant T's request:
  Output = base_model(x) + tenant_T_lora(x)
  
LoRA is fast to compute, small to store.
```

### 5.2 Multi-LoRA serving challenges

```
Challenge 1: GPU memory
  70B base = 70 GB (FP8)
  N LoRAs × 50 MB each = N × 50 MB
  Can fit ~200 hot LoRA in remaining GPU memory

Challenge 2: Per-request LoRA selection
  Batch of 256 requests, each from different tenant
  Each request needs different LoRA applied
  Can't compile separate kernel per tenant

Challenge 3: LoRA swap latency
  Cold LoRA (in S3): load takes ~500ms
  Cold LoRA (in CPU RAM): swap to GPU ~50ms
  Hot LoRA (in GPU): instant
```

### 5.3 S-LoRA / Punica 机制

```python
class MultiLoRABatching:
    """
    Modified continuous batching that handles per-request LoRA.
    """
    
    def __init__(self):
        self.lora_cache = LRUCache(maxsize=200)   # hot LoRA in GPU
        self.cpu_lora_cache = LRUCache(maxsize=1000)  # warm in CPU RAM
        # Cold in S3
    
    async def ensure_lora_loaded(self, lora_id):
        if lora_id in self.lora_cache:
            return  # hot
        
        # Try CPU RAM
        if lora_id in self.cpu_lora_cache:
            lora = self.cpu_lora_cache[lora_id]
            await self._cpu_to_gpu(lora)  # ~50ms swap
            self.lora_cache[lora_id] = lora
            return
        
        # Cold: load from S3
        lora_bytes = await s3.get(f"loras/{lora_id}.safetensors")
        lora = LoRA.from_bytes(lora_bytes)
        await self._cpu_to_gpu(lora)
        self.lora_cache[lora_id] = lora
        self.cpu_lora_cache[lora_id] = lora
    
    async def step(self, batch):
        # Each request in batch may have different LoRA
        # Group by LoRA for efficient kernel
        
        # First, ensure all LoRAs loaded
        loras_needed = {req.lora_id for req in batch}
        for lora_id in loras_needed:
            await self.ensure_lora_loaded(lora_id)
        
        # Forward pass with per-request LoRA application
        outputs = paged_attention_with_lora(
            batch,
            self.lora_cache,
        )
        return outputs
```

### 5.4 vLLM multi-LoRA config

```bash
# Start vLLM with multi-LoRA enabled
vllm serve meta-llama/Llama-3-70B-Instruct \
  --enable-lora \
  --max-loras 50 \                # max concurrent LoRAs in GPU
  --max-lora-rank 64 \            # rank up to 64 (typical 16-32)
  --lora-modules \
    tenant_001=/loras/tenant_001 \
    tenant_002=/loras/tenant_002 \
    ...

# Per-request LoRA selection
curl http://vllm:8000/v1/completions \
  -d '{
    "model": "tenant_001",       # specify LoRA via model name
    "prompt": "...",
    ...
  }'
```

### 5.5 Hot LoRA prediction (advanced)

```python
class HotLoRAPredictor:
    """Predict which LoRAs will be hot next 10 minutes, preload"""
    
    def __init__(self):
        self.usage_history = defaultdict(list)  # tenant_id → [timestamps]
    
    def record_usage(self, tenant_id, timestamp):
        self.usage_history[tenant_id].append(timestamp)
        # Keep last 1h
        cutoff = time.time() - 3600
        self.usage_history[tenant_id] = [
            t for t in self.usage_history[tenant_id] if t > cutoff
        ]
    
    def predict_hot(self, top_k=50):
        # Recent usage frequency
        scores = {}
        for tenant_id, timestamps in self.usage_history.items():
            recent = [t for t in timestamps if t > time.time() - 600]  # last 10min
            if recent:
                scores[tenant_id] = len(recent) / 600  # req/sec
        
        # Top-k
        sorted_tenants = sorted(scores.items(), key=lambda x: -x[1])
        return [t for t, _ in sorted_tenants[:top_k]]
    
    async def preload_loop(self):
        while True:
            hot = self.predict_hot(top_k=50)
            for tenant_id in hot:
                lora_id = f"tenant_{tenant_id}"
                if lora_id not in self.engine.lora_cache:
                    asyncio.create_task(
                        self.engine.ensure_lora_loaded(lora_id)
                    )
            await asyncio.sleep(60)
```

### 5.6 Cost comparison

```
Scenario: 100 tenants, each 100K req/day, all on Llama 3 70B FP8

Option A: 100 separate replicas (no LoRA sharing)
  Each replica: 8 H100 (TP=8) for 70B
  Total GPU: 100 × 8 = 800 H100
  Cost: 800 × $3/hr × 730 hr/month = $1,752,000/month
  
Option B: S-LoRA shared base
  Single replica serves 100 tenants
  Need 8 H100 for 1 replica + DP scaling for total QPS
  Total QPS: 100 × 100K / 86400 = ~115 QPS sustained
  Each replica handles ~50 QPS (with multi-LoRA overhead)
  Replicas needed: ~3
  Total GPU: 3 × 8 = 24 H100
  Cost: 24 × $3/hr × 730 = $52,560/month
  
Saving: $1.7M → $50K = **33x cheaper**

Quality difference: usually < 0.5% (LoRA delta well-isolated)
```

### 5.7 Per-tenant SFT / RL training pipeline

```python
# Customer uploads training data
@app.post("/v1/lora/train")
async def train_lora(req: TrainRequest):
    tenant_id = req.tenant_id
    training_data = req.training_data
    
    # Validate
    if len(training_data) < 100:
        raise BadRequest("Need 100+ examples")
    
    # Submit training job
    job_id = await train_queue.submit({
        "tenant_id": tenant_id,
        "training_data": training_data,
        "base_model": "llama-3-70b-instruct",
        "lora_rank": 16,
        "training_method": "sft",  # or "dpo", "rl"
    })
    
    return {"job_id": job_id, "estimated_time_min": 30}

# Background trainer
async def train_lora_worker(job):
    # Run on 8 H100 (training, not serving)
    # SFT: ~30 min for 1K examples
    # DPO: ~1h for 1K pairs
    # RL: 2-4h for converge
    
    result = await peft_train(
        base_model=job["base_model"],
        training_data=job["training_data"],
        lora_rank=job["lora_rank"],
        method=job["training_method"],
    )
    
    # Eval against tenant's eval set
    eval_score = await evaluate(result.model, job.get("eval_set"))
    
    # Upload to S3 for serving
    await s3.put(f"loras/tenant_{job['tenant_id']}.safetensors", result.lora_weights)
    
    # Notify serving cluster to refresh LoRA list
    await serving_cluster.broadcast_lora_update(f"tenant_{job['tenant_id']}")
    
    return {
        "job_id": job["id"],
        "lora_id": f"tenant_{job['tenant_id']}",
        "eval_score": eval_score,
    }
```

简历挂钩 (你的强项 SFT/DPO/RL post-training):

> "Voice agent for 7 markets — each market had its own LoRA fine-tuned on local language patterns + market-specific debt collection scripts. We used S-LoRA serving — 1 base 70B serving all 7 markets via per-call LoRA selection. Reduced GPU cost ~6x vs separate replica per market. Post-training pipeline ran SFT then DPO with market-specific preference data."

---

# Part 3 · 串起来看

5 个 problem 是 LLM serving 优化的完整体系:

1. **Continuous batching + PagedAttention** 是基础 — 没这两个, 一切优化无意义
2. **Parallelism** 决定 model 怎么 fit GPU
3. **Cache hierarchy** 决定哪些 cost 可以省
4. **Speculative + quantization** 决定 latency 和 throughput 极限
5. **Multi-LoRA** 决定 multi-tenant 经济性

面试场把这 5 个 layer 讲清楚 + 数学算清 + 给 production 数字, 就是 staff/principal level 的 LLM infra 水准. 你简历的 vLLM/SGLang/Megatron/DeepSpeed 是直接对位.

---

## 必问 clarifying questions

**1. Model size + version**

> "7B / 70B / 200B? Llama / Mixtral / proprietary? Determines GPU class + parallelism."

**2. Request profile**

> "Avg input/output token? Bursty or steady? Voice (low TPOT priority) or batch (throughput priority)?"

**3. SLA**

> "p99 < 1s — for TTFT or full response? Voice often needs TTFT < 300ms."

**4. Cost target**

> "$ per 1M tokens? Compared to vendor API (Gemini 3 Flash $0.50/$3 baseline, self-host ~$0.30)?"

**5. Hardware availability**

> "H100s, A100s, H200s, B100s (2026), TPUs, mixed? Cloud or on-prem?"

**6. Multi-tenant**

> "1 model for all or per-tenant fine-tunes? Multi-LoRA changes design significantly."

---

## 5 步框架 (sample 45-60 min answer)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify model / load / SLA / hardware / multi-tenant |
| 5-15 min | Hardware + parallelism plan (TP=8 H100 for 70B FP8) |
| 15-25 min | vLLM internals (continuous batching + PagedAttention + prefix cache) |
| 25-35 min | Optimizations (spec decode + quantization + multi-LoRA) |
| 35-45 min | Routing / autoscaling / observability |
| 45-60 min | Cost math + failover + Q&A |

---

## 我会这样答 (sample 完整版)

> "Clarify — *[假设: 70B fine-tuned model, avg in/out 500/200 tokens, p99 < 1s for full response, $0.001/1K tokens target, H100 80GB available, multi-tenant 100 LoRAs]*.
>
> **1M QPS at 70B is non-trivial**: 1M × 700 tok/req = 700M tok/sec output. At 5K tok/s per replica = 140K replicas needed in steady-state. Realistic deployment: ~5-10 region × 2000 replicas × 8 H100 = 80K-160K H100. 不是一家公司就能 deploy 的 scale, 但题面要的是 architecture, 不是 capex.
>
> **Stack choice**:
>
> Engine: **vLLM 0.6** (default 2026) — continuous batching, PagedAttention, prefix cache, multi-LoRA all built-in. SGLang considered for structured output / radix attention edge.
>
> Quantization: **FP8** (H100 native, 50% memory, <0.5% quality drop). INT4 AWQ if memory-constrained.
>
> Parallelism: **TP=8** within single node (8 H100 NVLink). DP across nodes. PP not needed for 70B FP8 (fits single node).
>
> **6-lever stack** (each multiplicatively improves throughput):
> 1. Continuous batching: 5-10x naive
> 2. PagedAttention: 24x more concurrent
> 3. Prefix caching: 2-3x repeated prefix (system + RAG shared)
> 4. Speculative decoding: 2-3x latency reduction (7B draft + 70B verify, 72% accept)
> 5. TP=8 + FP8: enables 70B on single node
> 6. Multi-LoRA: 100 tenants on 1 base model, 33x cheaper than separate replicas
>
> **Routing**:
> - Cost-aware: 90% Llama 70B self-host ($0.30/1M), 9% Gemini 3 Pro ($2/$12), 1% Claude Opus 4.7 ($5/$25)
> - Conv-aware sticky: same conversation_id → same replica → KV cache locality 80%+ hit
> - Per-tenant LoRA selection
>
> **Autoscaling**:
> - Predict load 15min ahead (time-of-day)
> - 20% pre-warmed buffer
> - Cold start: 1-5min (load weights), so warm pool essential
> - Burst spillover: overflow to Gemini Flash if self-host saturated
>
> **Observability**:
> - TTFT / TPOT p50/p99
> - Batch size avg/max
> - KV cache utilization
> - Prefix cache hit rate
> - Spec decoding accept rate
> - GPU util %
> - Queue depth
> - Token cost per request
> - Eval quality 5% A/B baseline
>
> **Cost math**:
> H100 ~$3/hr. 70B FP8 TP=8 single node: 8 H100. Throughput ~5K out tok/s = 18M tok/hr = $24/M output tok raw compute. With batching efficiency, ~$0.30 / 1M tok all-in (self-host).
>
> Vs Gemini 3 Flash ($0.50/$3) — self-host wins on output. Vs Claude Opus 4.7 ($5/$25) — self-host wins 10x.
>
> **Failover**:
> - Per-replica health check (heartbeat every 5s)
> - Inflight requests on failed replica → retry on healthy
> - KV cache lost on failover; LLM redoes prefill (~1s recovery)
> - Active-active not common for LLM (state is mostly ephemeral KV cache, OK to lose)
>
> **Simple sanity check** to validate setup:
> - Run 1 replica with `vllm benchmark`, target 5K out tok/s
> - Multiply by replica count for total
> - Compare to required QPS × avg tokens
>
> **Most likely interview follow-ups**: TTFT vs TPOT trade-off, multi-LoRA economics, when not to use vLLM, prefix cache eviction policy, speculative accept rate tuning."

---

## 简历专属 reframe — Gao Xin's strong area

| Topic | 你的经验 | How to quote |
|---|---|---|
| **vLLM / SGLang** | Voice agent inference stack | "I worked on vLLM 0.5 → 0.6 migration for our 70B voice agent. Continuous batching alone got 6x throughput over static batching." |
| **PagedAttention** | KV cache management | "Our voice agent uses PagedAttention block_size=16. Concurrent capacity went from 8 to ~120 calls per replica." |
| **Prefix caching** | System prompt + RAG shared | "Added prefix caching for shared system prompt across all calls in voice agent. Prefix hit rate 85%, prefill compute saved 75%." |
| **Speculative decoding** | TTFT < 300ms voice | "Used 7B draft + 70B verify spec decoding. 72% accept rate, TTFT dropped from 800ms to 280ms — enabled voice UX." |
| **FP8 quantization** | H100 native | "Moved voice agent from FP16 to FP8. Eval drop 0.3% (acceptable), throughput 1.8x. Same hardware now serves 2x calls." |
| **Multi-LoRA** | 7 markets each LoRA | "Each market had per-language LoRA — 7 LoRAs total. S-LoRA via vLLM enabled 1 base model serving all, 6x GPU savings vs per-market replica." |
| **Megatron / DeepSpeed** | TP + ZeRO | "For 200B+ training experiments, used Megatron TP=8 + DeepSpeed ZeRO-3. Production serving was TP only (no PP for 70B)." |
| **SFT / DPO / RL** | Post-training pipeline | "Post-training pipeline: SFT on cleaned dialogues → DPO with preference data (high-quality vs low-quality voice agent responses) → RL with reward model." |

**主动 quote** (面试场说出来):

> "I worked on vLLM + SGLang serving stack for a 70B fine-tuned voice agent at TikTok Global Payment. The journey through optimizations:
>
> 1. Started with HuggingFace transformers naive serving: 800ms TTFT, GPU util 35%
> 2. Moved to vLLM 0.5 continuous batching: TTFT 650ms, util 75% (3x throughput)
> 3. Added prefix caching (system prompt shared): 350ms TTFT (3x prefill saved)
> 4. FP16 → FP8 quantization: same TTFT, 2x throughput, eval drop 0.3%
> 5. Added speculative decoding (7B draft + 70B verify): 280ms TTFT, 72% accept rate
> 6. Multi-LoRA for 7 markets: 1 base model, 7 LoRAs, 6x cost saving
>
> End state: p99 TTFT 380ms, p50 220ms. Same hardware throughput ~12x increase from naive. This is the real magic of vLLM 0.6+ — the 6 levers multiply, not add."

---

## 5 follow-ups

**Q1**: "TTFT vs TPOT trade-off?"

**A**:
- **TTFT** = user-perceived "did it start responding". Matters for chat / voice / streaming.
- **TPOT** = token generation rate after start. Matters for total response time, batch jobs.
- vLLM optimizes both via continuous batching, but priority can shift:
  - Voice: priority TTFT — smaller batches, spec decode, prefix cache aggressive
  - Batch: priority TPOT — large batches, no spec decode overhead, max GPU util
- Speculative decoding: TTFT slightly worse (extra forward), TPOT better
- Per-use-case tuning of `max_num_batched_tokens` and batch size

**Q2**: "Multi-LoRA serving — how does vLLM handle per-request LoRA in same batch?"

**A**:
- vLLM 0.6+ supports it natively via S-LoRA / Punica algorithms
- LoRA computation factorized: shared base GEMM + per-request LoRA delta
- Custom CUDA kernel handles per-token LoRA application
- LoRA tensor stays in GPU memory (hot pool), swapped from CPU/disk as LRU
- Max ~200 hot LoRAs per GPU (50 MB each), more in CPU RAM
- Cold LoRA swap: 50-200ms overhead per swap

**Q3**: "Autoscaling for spikes — LLM cold start 1-5 min. How handle?"

**A**:
- **Pre-warm buffer**: always 20% extra running, ready for 5x burst absorption
- **Predictive scaling**: ML model trained on historical traffic, scale 10min ahead
- **Burst spillover**: overflow to vendor API (Gemini Flash) — expensive but elastic
- **Graceful degradation**: smaller model under load (Llama 8B fallback)
- **Cold start mitigation**:
  - Pre-pull model weights to local SSD (avoid S3 cold)
  - Warm up CUDA kernels on startup
  - First N requests do prefill but mark replica "warming"
- Healthcheck only marks replica "healthy" after warm-up completes

**Q4**: "vLLM vs SGLang vs TensorRT-LLM — when each?"

**A**:
- **vLLM 0.6+**: default 2026, most features, easy ops, large community. Choose unless specific reason not to.
- **SGLang**: structured output (JSON, regex), RadixAttention (advanced prefix sharing), multi-LoRA first-class. Choose when need structured generation or extreme multi-tenant.
- **TensorRT-LLM**: NVIDIA's tooling, absolute peak throughput, integration with Triton. Choose when need 10-20% extra throughput justifies complex setup.
- **TGI (HuggingFace)**: easy ops, HuggingFace integration. Lags vLLM on perf.
- **Llama.cpp / MLC**: CPU / consumer GPU / edge.

**Q5**: "Eval quality drops mysteriously. Debug?"

**A**:
- **Quantization regression**: INT4 too aggressive on certain query types. Run A/B baseline vs quantized.
- **Speculative decoding low accept rate**: < 50% causes silent quality drop (draft pulls verifier's logits in non-greedy mode). Check accept rate metric.
- **Prefix cache corruption**: rare bug where stale cache served. Look for `<--clear-cache>` admin tool.
- **Model version drift**: someone deployed slightly different checkpoint, check `model_version` in logs.
- **Tokenizer mismatch**: critical. Mismatch between training and serving tokenizer = garbage output.
- **A/B**: route 5% to baseline (no optims) — compare eval pass rate. If baseline OK and optim has drop → optim is culprit.

**Q6** (bonus): "Long context — 1M token. Affordable?"

**A**:
- 1M token KV cache: 1M × 32KB × 80 layers = 2.5 TB (impractical naively)
- Mitigations:
  - **Quantize KV cache to FP8/INT8**: 50% memory
  - **Sliding window attention**: only keep last N=128K tokens
  - **Sequence parallelism**: split context across GPUs
  - **Sparse attention** (e.g., Longformer): attention windowed
  - **Hierarchical / summarized context**: most of context summarized, only recent verbatim
- 2026 production: Gemini 3 Pro 1M token context with cache discount; self-host hard, usually <= 128K verbatim, longer requires architectural tricks

---

## ❌ 易错点 (top 10)

1. **Naive batching (static padding)** — 5-10x throughput loss
2. **Pre-allocate KV cache per request max_len** — 88% memory waste
3. **No prefix cache for FAQ / shared system prompt** — 2-3x prefill waste
4. **One GPU per replica for 70B** — impossible (140GB > 80GB)
5. **No quantization in 2026** — FP8 H100 native, free perf
6. **No autoscaling pre-warm** — cold start kills burst
7. **No quality eval per optim** — silent regression
8. **Speculative decoding accept rate < 50%** — overhead worse than savings
9. **Multi-tenant no LoRA sharing** — 100x cost
10. **No sticky routing for KV cache locality** — cache hit rate drops 80% → 30%

---

## ✅ 加分项 (top 12)

1. **6-lever mental model** with multiplicative gains
2. **Continuous batching mechanics** explained (per-step scheduling)
3. **PagedAttention math** (block_size, KV memory per token)
4. **Prefix caching** for shared prefix (system + RAG)
5. **Speculative decoding** with accept rate math
6. **Quantization** (FP8 default 2026, INT4 for memory)
7. **TP / PP / DP / EP** selection by model size
8. **Multi-LoRA** S-LoRA / Punica with hot LoRA cache
9. **Cost math** vs vendor API ($0.30/1M self-host vs $5/1M Opus)
10. **Conv-aware sticky routing** for KV cache locality
11. **Quality A/B** for every optim
12. **Quote your vLLM/SGLang/SFT/DPO/RL experience**

---

## 一句话总结

> **High-throughput LLM serving = 6 levers multiplicatively stacked**: continuous batching + PagedAttention + prefix cache + speculative decoding + parallelism + quantization + multi-LoRA. vLLM 0.6 default 2026, FP8 默认 quantization, TP=8 单 node for 70B, sticky routing per conv_id for cache locality. 不叠加任何一个都做不到 1M QPS.

---

## Cheat Sheet (印 1 页)

```
6 levers for high throughput (multiplicative):
  1. Continuous batching       vLLM       5-10x naive
  2. PagedAttention            vLLM       24x more concurrent
  3. Prefix caching            vLLM       2-3x shared prefix
  4. Speculative decoding      vLLM       2-3x latency
  5. TP/PP parallelism         Megatron   enables 70B+ fit
  6. Quantization              FP8/INT4   2x memory + 1.5-2x speed
  7. Multi-LoRA (multi-tenant) S-LoRA     33x cheaper vs separate replica

Default 2026 stack:
  Engine:      vLLM 0.6+ (90% prod)
  Hardware:    H100 80GB (or H200 144GB or B100 FP4)
  Parallelism: TP=8 single node for 70B+ FP8
  Quantization: FP8 default (E4M3)
  Cache:       enable-prefix-caching ON

Parallelism selection:
  < 80GB FP8:  DP only, 1 GPU per replica
  < 640GB FP8: TP within node + DP across nodes (most common, 70B)
  > 640GB FP8: TP=8 + PP=2+ cross node (200B+)
  MoE:         + EP across GPUs
  Long ctx:    + SP for sequence

Quantization choices:
  FP16:    baseline
  FP8:     50% mem, 1.5-2x speed, < 0.5% drop ⭐
  INT8:    50% mem, 1.3x speed, 1-2% drop
  INT4:    25% mem, 2-3x speed, 2-5% drop
  FP4 (B100, 2026): 25% mem, 4x speed, 2-4% drop

Speculative decoding:
  Draft model: same family (Llama 3 8B for 70B)
  Accept rate: 70-80% sweet spot
  Speedup: 2-3x at 70% accept, K=5
  Disable if batch large (overhead > savings)

Multi-LoRA (S-LoRA):
  Base shared (frozen)
  Per-tenant LoRA 50-100 MB
  Hot pool: 200 LoRA in GPU
  Cold: CPU RAM / S3
  vLLM: --enable-lora --max-loras 50

Cache hierarchy:
  L1 Exact result    (hash, 10-20% hit)
  L2 Semantic        (embedding 0.95, 30-50% hit FAQ)
  L3 Prefix (vLLM)   (server-side, 60-90% hit shared prefix)
  L4 Tool output     (idempotent reads, per-tool TTL)

Routing:
  Cost-aware: 90% cheap, 9% mid, 1% premium
  Conv-aware: sticky by conv_id (KV cache locality)
  Per-tenant LoRA selection

Observability:
  TTFT / TPOT p50/p99
  Batch size avg/max
  KV cache util
  Prefix cache hit rate
  Spec accept rate
  GPU util %
  Queue depth
  Token cost / request
  Eval quality 5% A/B

Cost math (2026, self-host 70B FP8):
  H100 $3/hr × 8 (TP=8) = $24/hr per replica
  5K out tok/s × 3600 = 18M tok/hr
  Cost: $24 / 18M tok = $0.30 / 1M output
  
  vs Gemini 3 Flash $0.50/$3
  vs Claude Opus 4.7 $5/$25 (16x more!)

Autoscale:
  Pre-warm 20% buffer
  Predictive (time-of-day)
  Burst spillover (vendor API overflow)
  Graceful degradation (smaller model)

Failover:
  Per-replica health check 5s
  Inflight retry on healthy
  KV cache lost on crash, redo prefill (1s)
  Active-active rare for LLM

红线:
  - Naive batching (static padding)
  - Pre-allocate KV max_len
  - No prefix cache for shared workload
  - 1 GPU for 70B (impossible)
  - No quantization in 2026
  - No autoscale pre-warm
  - No quality eval per optim
  - Spec accept < 50%
  - Multi-tenant no LoRA share
  - No sticky routing

Resume quotes:
  "Voice agent vLLM 0.6, TTFT 800ms → 280ms via 6-lever stack"
  "FP8 quantization, eval drop 0.3%, throughput 2x"
  "7 markets S-LoRA, 1 base 7 LoRAs, 6x GPU saving"
  "Spec decoding 72% accept rate"
  "Megatron + DeepSpeed for 200B training experiments"
```
