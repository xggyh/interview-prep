# ⚡ T3.3 · High-throughput LLM Serving (1M QPS) — 冲刺版

> 完整版: [gfde-t3-high-throughput.html](gfde-t3-high-throughput.html). 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: 70B fine-tuned model, avg 500 in / 200 out token, p99 <1s, $0.001/1K tok 目标, H100 80GB available, multi-tenant 100 LoRA, multi-region."

**核心 framing**: 1M QPS × 700 tok/req = 700M tok/sec → 单 replica 5K tok/s → ~140K replicas in steady-state. 现实 ~8 region × 2000 replicas × 8 H100/replica = 128K H100. 不是单公司搞得起, 但架构思路要对. 6 个 lever **multiplicatively** 叠加才行.

### Layer 1: 6 throughput levers (vs HF Transformers baseline 1x)

```
1. Continuous batching   vLLM       5-10x naive (token-level scheduling, 无 padding)
2. PagedAttention        vLLM       24x more concurrent (KV cache 像 OS 虚拟内存)
3. Prefix caching        vLLM       2-3x (system prompt + RAG 共享 KV)
4. Speculative decoding  vLLM 0.6   2-3x latency (7B draft + 70B verify, 70% accept)
5. TP / PP / DP / EP     Megatron   70B+ enables (TP=8 on 8 H100 NVLink)
6. Quantization FP8/INT4 native     1.5-2x mem + speed (H100 FP8 < 0.5% drop)
+ Multi-LoRA S-LoRA      vLLM       33x cheaper vs separate replica
```

叠加: naive 8 QPS/A100 → 优化后 ~400-500 QPS/A100 ≈ 60x. 这是 vLLM 0.6+ 的实战数字.

### Layer 2: Default 2026 stack

```
Engine        vLLM 0.6+ (90% production)
Hardware      H100 80GB SXM (或 H200 144GB / B100 FP4)
Parallelism   TP=8 single node for 70B+ FP8
Quantization  FP8 default (E4M3, H100 native, < 0.5% drop)
Cache         --enable-prefix-caching ON
LoRA          --enable-lora --max-loras 50

Per-replica spec:
  8 × H100 80GB NVLink (TP=8)
  70B FP8 weights = 70GB → 9GB/GPU
  KV cache pool: 50GB/GPU
  Throughput: 5-7K out tok/s
  TTFT cold: 400ms / cache hit: 150ms
  TPOT: 30ms steady
```

### Layer 3: Speculative decoding 数学

```
7B draft propose K=5 tok → 70B verify 1 forward
Accept rate 70%:
  Best case: 5 token output / 2 forwards = 2.5x speedup
  70% accept, K=5: ~3.5 token / forward = 3.5x
  Cost: +5% draft compute, net 2-3x latency 收益

Disable spec decode if:
  - Batch 太大 (overhead > savings)
  - Accept rate < 50% (拉低 throughput)
  - Pure throughput priority (TPOT, not TTFT)
```

### Layer 4: Multi-LoRA (S-LoRA / Punica)

```
Base 70B FP8 on 8 H100 = 70GB shared (frozen)
Hot LoRA pool 50 tenants × 50MB = 2.5GB + KV cache 30GB

Per-request: route by tenant_id → look up LoRA (hot apply / cold swap 50-200ms)
Multiple tenants same batch, per-request LoRA, custom CUDA kernel base GEMM + delta
vs 100 separate replicas: 33-100x cost reduction, <0.1% quality diff
```

### Edge cases

- **EC1 Cold start 1-5min kill burst**: pre-warm 20% buffer + predictive scaling (15min ahead) + burst spillover to vendor API (Gemini Flash) + smaller model graceful degrade (Llama 8B fallback).
- **EC2 Long context 1M token**: naive 2.5TB KV cache 不可能. KV quantize FP8/INT8 (50% mem) + sliding window 128K + sequence parallelism + sparse attention. 2026 production 通常 ≤ 128K verbatim, 长走 Gemini 3 Pro 1M with cache discount.
- **EC3 Eval quality 神秘 drop**: 5 个 root cause — quantization regression (INT4 太激进) / spec decode accept <50% / prefix cache corruption / model version drift / tokenizer mismatch. A/B 5% baseline 对比 quantized 找元凶.
- **EC4 Replica failover**: per-replica 5s heartbeat, inflight retry healthy replica, KV cache lost on crash (redo prefill ~1s), active-active 罕见 (state 主要 ephemeral KV, OK 丢).
- **EC5 Cache 不均 sticky 路由失衡**: 大 user (long conv) 集中某 replica → 100% GPU util. Fix: routing 算法考虑 conv length, balance, drain hot replica.

### Production hardening

- **TTFT/TPOT p50/p99** (per model, per tenant), batch size avg/max, KV cache util %, prefix cache hit rate, spec decode accept rate, GPU util %, queue depth.
- **Cost math**: H100 $3/hr × 8 (TP=8) = $24/hr/replica. 5K out tok/s × 3600 = 18M tok/hr → $0.30 / 1M out token self-host. vs Opus 4.7 $25/1M → **80x 更便宜**.
- **Routing**: cost-aware 90% Llama self-host + 9% Gemini Pro + 1% Opus + conv-aware sticky (80% prefix hit) + per-tenant LoRA selection.

### 🪝 Resume hook

"On TikTok Global Payment voice agent 我做过 vLLM + SGLang 70B fine-tuned 完整 6-lever stack. Journey: HF Transformers 800ms TTFT 35% util → vLLM 0.5 continuous batch (650ms, 75% util, 3x) → prefix cache (350ms) → FP8 quantize (same TTFT 2x throughput, 0.3% eval drop) → spec decode 7B draft 72% accept (280ms TTFT) → S-LoRA 7 markets 1 base 7 LoRA (6x GPU saving). End: p99 380ms, p50 220ms, 12x throughput vs naive. 这就是 vLLM 0.6+ 的 magic — 6 levers multiply 不 add."

---

## 🔥 5 Follow-ups

**Q1: TTFT vs TPOT trade-off?**
TTFT = 用户感知 "开始回应" (prefill 决定), 重 chat / voice. TPOT = 后续 token 间隔 (decode), 重 batch. Voice: 优先 TTFT — 小 batch + spec decode + prefix cache aggressive. Batch: 优先 TPOT — 大 batch + 无 spec decode + max GPU util. 调 `max_num_batched_tokens` per use case.

**Q2: Multi-LoRA - vLLM 怎么 same batch 处理 per-request LoRA?**
S-LoRA / Punica 算法. LoRA 计算分解: 共享 base GEMM + per-request LoRA delta. Custom CUDA kernel per-token LoRA apply. Hot pool 200 LoRA in GPU (50MB each), cold CPU RAM / S3 LRU. Cold swap 50-200ms overhead. `--enable-lora --max-loras 50`.

**Q3: Autoscaling LLM cold start 1-5min 怎么 burst?**
Pre-warm 20% extra running (5x burst absorb). Predictive scaling 10min ahead (ML on traffic pattern). Burst spillover vendor API (Gemini Flash) — 贵但弹性. Graceful degrade 小 model (Llama 8B fallback). Cold start mitigate: pre-pull weights to local SSD + warm CUDA kernels + first N req mark "warming" not "healthy".

**Q4: vLLM vs SGLang vs TensorRT-LLM 选哪个?**
vLLM 0.6+: default 2026, 最全 feature, 易 ops, 大社区. 90% 生产场景. SGLang: structured output (JSON/regex) + RadixAttention (advanced prefix) + multi-LoRA 一流. 选当需要 structured generation 或 extreme multi-tenant. TensorRT-LLM: NVIDIA tooling, 绝对 peak throughput, 10-20% 多吞吐换 complex setup. TGI: HF 生态简单, perf 落后. Llama.cpp: CPU / edge.

**Q5: Long context 1M token 可行吗?**
单 req 1M × 32KB × 80 layer = 2.5TB KV cache (naive 不可能). Mitigation: KV quantize FP8/INT8 (50%) + sliding window N=128K (Longformer) + sequence parallelism 跨 GPU + sparse attention + hierarchical summarized context. 2026 生产: Gemini 3 Pro 1M token with cache discount 是 vendor-side, self-host 通常 ≤128K verbatim.

---

## ❌ 易错点 (10 条红线)

1. **Naive static padding batching** — 5-10x throughput loss
2. **Pre-allocate KV cache per req max_seq_len** — 88% memory waste
3. **No prefix cache for FAQ / shared system prompt** — 2-3x prefill waste
4. **One GPU per replica for 70B** — 不可能 (140GB > 80GB), 必须 TP
5. **No quantization in 2026** — FP8 H100 native 是 free perf 不要不用
6. **No autoscaling pre-warm** — cold start 1-5min kill burst
7. **No quality eval per optim** — silent regression
8. **Spec decoding accept rate <50%** — overhead 大于 savings, 反而拖慢
9. **Multi-tenant 不 share base via LoRA** — 100x cost
10. **No sticky routing for KV cache locality** — cache hit 80% → 30% 暴跌

---

## ✅ 加分项 (12 条)

1. **6-lever mental model** with multiplicative gains (不是 additive)
2. **Continuous batching mechanics** explained (per-step scheduling, 无 padding)
3. **PagedAttention math** (block_size=16 token, KV mem per token formula)
4. **Prefix caching** for shared prefix (system + RAG 90% hit possible)
5. **Speculative decoding** with accept rate math (70% sweet spot, K=5)
6. **Quantization 2026 choice** (FP8 default, INT4 if memory-bound)
7. **TP / PP / DP / EP** selection by model size + workload
8. **Multi-LoRA S-LoRA / Punica** with hot LoRA cache pool
9. **Cost math** vs vendor API ($0.30/1M self-host vs $25/1M Opus = 80x)
10. **Conv-aware sticky routing** for KV cache locality (80% hit)
11. **Quality A/B** for every optim (5% baseline route)
12. **Quote your vLLM/SGLang/Megatron/DeepSpeed/SFT/DPO/RL** experience

---

## 一句话总结

**High-throughput LLM serving = 6 levers multiplicatively stacked**: continuous batching + PagedAttention + prefix cache + speculative decoding + parallelism + quantization + multi-LoRA. vLLM 0.6 default 2026, FP8 默认 quantization, TP=8 单 node for 70B, sticky routing per conv_id for cache locality. 不叠加任一 lever 都做不到 1M QPS scale. 这是 your simple 强项区, 用 voice agent 实战数字背熟.

---

## 🃏 Cheat Sheet (印 1 页随身)

```
6 levers (multiplicative):
  1. Continuous batching     vLLM   5-10x naive
  2. PagedAttention          vLLM   24x more concurrent
  3. Prefix caching          vLLM   2-3x shared prefix
  4. Speculative decoding    vLLM   2-3x latency
  5. TP/PP parallelism       Megatron enables 70B+
  6. Quantization            FP8/INT4 2x mem + 1.5-2x speed
  7. Multi-LoRA (multi-tenant) S-LoRA 33x cheaper

Default 2026 stack:
  Engine        vLLM 0.6+ (90% prod)
  Hardware      H100 80GB (H200 144GB / B100 FP4)
  Parallelism   TP=8 single node 70B+ FP8
  Quantization  FP8 default (E4M3)
  Cache         --enable-prefix-caching ON
  GCP           A3 Mega VM (8 H100 NVLink) / TPU v5p / v6e

Parallelism selection:
  <80GB FP8: DP only, 1 GPU/replica
  <640GB FP8: TP within + DP cross (70B common)
  >640GB FP8: TP=8 + PP=2+ cross node (200B+)
  MoE +EP / Long ctx +SP

Quantization (2026):
  FP16 baseline / FP8 50% mem 1.5-2x speed <0.5% drop ⭐
  INT8 50% mem 1.3x / INT4 25% mem 2-3x 2-5% drop
  FP4 B100 25% mem 4x 2-4% drop

Speculative decoding:
  Draft same family (Llama 8B for 70B)
  Accept 70-80% sweet, speedup 2-3x at K=5
  Disable if batch large (overhead > savings)

Multi-LoRA (S-LoRA):
  Base shared frozen / per-tenant LoRA 50-100MB
  Hot pool 200 LoRA in GPU / cold CPU RAM/S3
  vLLM: --enable-lora --max-loras 50

Cache hierarchy: L1 exact hash 10-20% / L2 semantic 0.95 30-50% FAQ / L3 prefix vLLM 60-90% / L4 tool per-TTL

Routing: cost-aware 90/9/1 + conv-aware sticky (80% KV hit) + per-tenant LoRA

Observability: TTFT/TPOT p50/p99 + batch avg/max + KV util % + prefix hit + spec accept + GPU util + queue + cost + eval 5% A/B

Cost math (self-host 70B FP8): H100 $3/hr × 8 = $24/hr × 5K out tok/s → $0.30/1M output. vs Opus $25/1M = 80x cheaper

Autoscale: pre-warm 20% + predictive + spillover vendor + graceful degrade smaller model

Failover: per-replica health 5s + inflight retry healthy + KV lost (redo prefill 1s) + AA rare

红线:
  - Naive batching (static padding)
  - Pre-allocate KV max_len
  - No prefix cache shared workload
  - 1 GPU for 70B (impossible)
  - No quantization in 2026
  - No autoscale pre-warm
  - No quality eval per optim
  - Spec accept <50%
  - Multi-tenant no LoRA share
  - No sticky routing

Voice agent journey (your hook):
  HF naive       800ms TTFT, 35% util
  + cont batch   650ms, 75%, 3x
  + prefix cache 350ms (3x prefill saved)
  + FP8 quant    same TTFT 2x throughput, 0.3% drop
  + spec decode  280ms (72% accept)
  + 7-market LoRA (S-LoRA, 6x GPU save)
  End: p99 380ms, p50 220ms, 12x throughput

Resume quotes:
  "Voice agent vLLM 0.6, 800→280ms via 6-lever"
  "FP8 quantization, 0.3% drop, 2x throughput"
  "7 markets S-LoRA, 1 base 7 LoRAs, 6x save"
  "Spec decoding 72% accept rate"
  "Megatron + DeepSpeed for 200B training experiments"
```
