## T3.3 · 1M QPS LLM serving — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](gfde-t3-high-throughput.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t3-high-throughput.html`](gfde-t3-high-throughput.html)

---
## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"customer wants 1M QPS LLM serving, p99 < 1s, fine-tuned model. Walk through your serving stack"**, 我按这 9 层回答, 不跳序. 这是我**简历最硬核 hook 区** (vLLM/SGLang/DeepSpeed 简历明示).

### 📐 1M QPS LLM Serving — 9 层结构

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 |
|---|---|---|---|---|
| 1 | Throughput 数学锚点 | 1 min | 1M QPS × avg 700 token output = 700M tokens/sec. 单 H100 FP8 8B model vLLM full stack ~600 QPS → 1700 GPU baseline. 加 prefix cache + spec dec 减半到 ~800-900 GPU | "Let me anchor the math first — 1M QPS × 700 tokens / 600 QPS per H100 = ~1700 GPUs. With prefix cache 减半..." |
| 2 | Clarify 6 问 | 90s | Model size (8B / 70B / 200B)? Avg input / output token? p99 latency vs throughput priority? TTFT vs TPOT? FP16 / FP8 / INT4 quality budget? Multi-tenant fine-tune? | "Before I commit to a stack, 6 questions — model size, token mix, latency target, quant budget, multi-tenant?" |
| 3 | 6 levers 排序 + 数学 | 5 min | Baseline HF Trans 5-10 QPS → continuous batch **5x** → PagedAttn **10x** (24x concurrency) → prefix cache **20x** → spec dec **40x** (70% accept) → FP8 quant **60x**. 各 lever 触发条件 | "6 levers multiplicative — 1x baseline to 60x full stack. Let me walk through each with the math..." |
| 4 | Continuous batching deep-dive | 3 min | Token-level scheduler (vLLM Scheduler class). 不是 batch-level 等满. 1 个 req 完成立刻 swap 新 req in. 无 padding. 8 token block. Iter-level preemption with chunked prefill | "Continuous batching is token-level — vLLM Scheduler swaps in new requests every iteration, no padding waste..." |
| 5 | PagedAttention 像 OS 页表 | 3 min | KV cache 切 16-token block. Block 按需分配, copy-on-write for shared prefix. 24x more concurrent vs pre-allocate max_seq_len. **生产实测 70B FP8 H100 单节点 8 卡: pre-alloc 4 concurrent → PagedAttn 80-100 concurrent** | "PagedAttention 像 OS 虚拟内存 — 16-token block, CoW for shared prefix, 24x concurrency on 70B FP8..." |
| 6 | Multi-LoRA serving | 2 min | S-LoRA / Punica: 100 tenant fine-tune adapters 共享 1 个 base model. Adapter swap < 1ms on H100. 比 100 个 base replica 便宜 **33x**. Voice agent 7 market 你正好这个 case | "Multi-LoRA via S-LoRA — 100 tenant adapters share 1 base, 33x cheaper than replicas. Voice agent 7 markets fits this exactly..." |
| 7 | Parallelism 选型 | 2 min | TP within node (NVLink 900GB/s), DP across node (Ethernet 100Gb/s). **70B FP8 sweet spot = TP=8 single node 8×H100 80GB**. > 200B 用 EP for MoE. PP 几乎不用了 | "Parallelism — TP within node only (NVLink), DP across. 70B FP8 sweet spot 是 TP=8 single 8×H100..." |
| 8 | Cost-aware routing 数学 | 2 min | 单 model: 全 Opus $5/$25 → $0.0085/call → 1M QPS × 86400s = blended $735M/day. 70/25/5 路由 → blended $0.85/1M = $73M/day, **10x reduction**. 加 self-host vLLM 8B fine-tuned → $0.30/1M | "Cost layer — hosted blended $0.85/1M with 70/25/5 routing vs $5/1M all-Opus = 10x. Self-host vLLM 再降 3x..." |
| 9 | 简历 resume hook | 90s | "Voice agent self-host LLM 用 **vLLM 0.6** (continuous batch + PagedAttn + prefix cache + FP8), Llama 3.1 8B fine-tuned, **A100 8 卡 → 150 QPS sustained, 18x HF baseline**. BNPL chatbot 用 **SGLang RadixAttention**, multi-turn 多 20-30% extra cache hit." | "On voice agent we ran vLLM TP=8 with FP8 — 18x baseline. BNPL chatbot SGLang RadixAttention for multi-turn..." |

### 🎯 为啥按这个序

数学锚点先开场: 算出来 1700 GPU 让面试官知道你能直接 size capacity. Clarify 5 问是 senior IC 信号 — 没问 model size 就给方案是 junior 反模式. 6 levers 是骨干, 必须给数字 (5x / 10x / 24x 等), 不能停在概念. Continuous batch + PagedAttn 是最容易被追问的两个, 必须能讲 OS-page-table 类比. Multi-LoRA 是 2026 新热点, 你简历 voice agent 7 market 正好对上. Parallelism 选型 (TP within / DP across) 显示你做过 H100 部署. Cost 数学锚点把 throughput 和 economic 串起来. 简历 hook 最后, vLLM + SGLang 双 stack 是 staff 信号.

### 🔥 哪一层最容易被追问 deeper

**Layer 5 (PagedAttention)** — 追问 "block size 怎么选?". 回答: 16 token 是 vLLM 默认 sweet spot, 太小 metadata overhead 大, 太大 fragmentation. 70B FP8 实测 block=16 vs 32 差 < 2%. **Layer 4 (continuous batching)** 追问 "chunked prefill 是什么". 回答: 长 prompt prefill 阶段切成 chunk, 每 chunk 和 decode 共享 batch slot, 避免长 prefill 阻塞短 decode (vLLM 0.5+ 默认 enable). **Layer 6 (multi-LoRA)** 追问 "adapter swap 怎么 sub-ms". 回答: adapter 是 low-rank decomposition (rank=8/16/32), GPU mem 几 MB, 预加载到 HBM, swap 是 pointer 切换.

### ⏱ 时间压缩版 (30 min round)

1. 数学锚点 (1 min) + clarify 3 问 (1 min)
2. 6 levers 数字 + 各加速比 (5 min)
3. PagedAttn + continuous batch 深入 (4 min)
4. Multi-LoRA + parallelism 选型 (3 min)
5. Cost 数学 + 简历 vLLM/SGLang quote (3 min)

### 🆘 卡壳兜底 (针对这题)

1. **被问 "1M QPS 真的可行吗"**: 主动承认 "对单个 product 几乎不存在 — Google search 全球 ~100K QPS. 但用 6 levers + 70/25/5 routing 把绝大多数 traffic 引到便宜 model, 可以让 cost / latency 都达标"
2. **被问 "spec decoding 什么时候不用"**: accept rate < 50% 时 overhead > 收益, 关掉. 通常发生在 draft 和 verifier 模型 distribution 差距大 (e.g., draft 0.5B vs base 70B 不同 tokenizer)
3. **被问 "INT4 vs FP8 选哪个"**: FP8 < 0.5% quality drop, sweet spot 2026 default. INT4 (AWQ/GPTQ) 2-5% drop, consumer chatbot 可接受, legal/medical 不行. Self-host 选 FP8 (H100/Blackwell 硬件加速), edge / 小 GPU 才用 INT4
4. **被问 "TensorRT-LLM vs vLLM"**: TRT-LLM 在 NVIDIA stack 上极致优化, +20-30% over vLLM, 但 engine 编译时间长 (1-2h per model), 模型迭代慢. vLLM dev velocity 强, 生产默认 vLLM, TRT-LLM 只在稳定 model + 极致 throughput 需求时用

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖 6 lever 数学 / parallelism / quant / spec / multi-LoRA / cache 全量. 你的 **strongest 简历 hook** (vLLM/SGLang/DeepSpeed) — 必背.

### 🧠 核心心智模型 (1 sentence)

LLM serving throughput 是 **6 个 lever 乘法叠加** (continuous batch × PagedAttn × prefix cache × spec dec × TP/PP × quant), HF Transformers baseline 5-10 QPS / A100 → 全 stack 200-600 QPS = **50-60x**; 2026 default 是 **vLLM 0.6 + H100 + TP=8 + FP8 + prefix cache enabled**.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Continuous batching | Token-level scheduling, 完成的 req 立刻拿掉, 新 req 拼进 | vLLM 默认, 5-10x |
| PagedAttention | KV cache 按 16-token block 切, 像 OS 页表 | vLLM, 24x concurrency |
| Prefix cache | Shared system prompt KV block reuse | 多 user 共 prompt |
| Speculative decoding | Draft 小模型 + verify 大模型 | 2-3x latency, 单 query |
| Eagle / Medusa | 开源 spec dec 实现 | vLLM 集成 |
| TP (Tensor Parallel) | Weight matrix 沿 hidden dim 切, 多 GPU 并行 | model 装不下单 GPU |
| PP (Pipeline Parallel) | Layer 切到不同 GPU stages | 200B+ 跨 node |
| DP (Data Parallel) | Replica 同 model, request 分流 | scale out |
| EP (Expert Parallel) | MoE expert 分多 GPU | Mixtral, GPT-4 style |
| SP (Sequence Parallel) | 长 context 切到多 GPU | 1M+ context |
| FP8 (E4M3) | H100/Hopper 原生 8-bit float | 默认 2026 quant |
| INT4 (AWQ/GPTQ) | 4-bit integer, 2-5% quality drop | 高量 / 容忍质量 |
| Multi-LoRA (S-LoRA) | 共享 base + per-tenant LoRA adapter | 多租户 fine-tune |
| TTFT | Time-to-first-token | voice < 300ms |
| TPOT | Time-per-output-token | 30-100ms 典型 |
| KV cache util | GPU mem 用于 KV 占比 | vLLM metric |

### 🎯 6 个核心 framework / lever

**Lever 1: Continuous Batching (vLLM)** — 5-10x
- When: 任何 LLM serving (default ON)
- Algorithm: 不等批满, token-level prefill + decode 混合调度
- Trade-off: 复杂度 ↑, 单 req 延迟 minor variance
- Tools: vLLM 0.6+, TGI, TensorRT-LLM, SGLang

**Lever 2: PagedAttention** — 24x concurrency
- When: vLLM default, KV cache mem 优化
- Algorithm: KV cache 切 16-token block, block table per req, OS-style page sharing
- Trade-off: per-token 微 overhead vs no padding 浪费
- Tools: vLLM `--enable-prefix-caching`, block manager 自动

**Lever 3: Prefix Caching** — 2-3x for shared prompt
- When: 1k+ user 共同 system prompt / RAG prefix
- Algorithm: hash prefix block, lookup → reuse computed KV; vendor side: Anthropic 90% off, OpenAI 50%, Google 75%
- Trade-off: prompt 微改 → all invalid; per-tenant isolation needed
- Tools: vLLM auto, Anthropic `cache_control={"type":"ephemeral"}`, conv_id hint

**Lever 4: Speculative Decoding** — 2-3x latency
- When: latency-bound single-query (voice / coding agent)
- Algorithm: draft model K=5 token → verify 1 forward → accept prefix
- Trade-off: accept < 50% → 关掉; high batch → 关 (overhead > saving)
- Tools: vLLM Eagle / Medusa, draft model same family (Llama 3 8B for 70B)

**Lever 5: TP/PP/DP/EP Parallelism**
- When: model 装不下单 GPU
- Algorithm: < 80GB FP8 → DP only; 70B → TP=8 single node; 200B+ → TP=8 + PP cross node
- Trade-off: TP 跨 node kill perf (NVLink 内 OK), PP idle bubble
- Tools: vLLM `--tensor-parallel-size 8`, Megatron-LM, DeepSpeed, Ray Serve

**Lever 6: Quantization (FP16 → FP8 / INT8 / INT4)**
- When: cost / latency 不够时
- Algorithm: FP8 (H100 native) 默认 < 0.5% drop; INT4 AWQ 2-5% drop
- Trade-off: quality drop need eval gate
- Tools: vLLM `--quantization fp8`, AWQ / GPTQ scripts, TensorRT-LLM

**Bonus Lever 7: Multi-LoRA (S-LoRA)** — 33x cheaper vs replicas
- When: 多租户 fine-tune (你 voice agent 7 markets)
- Algorithm: 1 base + N LoRA adapters (50-100MB each), GPU hot pool 200 LoRA
- Trade-off: per-LoRA cold-load 100ms
- Tools: vLLM `--enable-lora --max-loras 50`

### 🌳 关键决策树 (ASCII)

```
Self-host or hosted API?
  ├─ < 100K QPS / proven volume → hosted (Anthropic/Gemini cost cap)
  └─ > 100K QPS / cost-driven → self-host vLLM

Parallelism for model X?
  ├─ X FP8 < 80GB ── DP only (1 GPU/replica)
  ├─ X FP8 < 640GB ── TP within node (8 GPU) + DP across nodes (70B sweet spot)
  ├─ X FP8 > 640GB ── TP=8 + PP cross node (200B+)
  ├─ MoE ── + EP across GPUs (Mixtral, GPT-4)
  └─ Long ctx (1M+) ── + SP for sequence

Quantization choice?
  ├─ Quality critical (medical, legal) ── FP16 baseline
  ├─ Default 2026 ── FP8 (< 0.5% drop) ⭐
  ├─ Cost down moderate ── INT8 (1-2% drop)
  └─ Aggressive cost ── INT4 AWQ (2-5% drop, eval gate)

Spec decoding?
  ├─ Latency-bound single-query ── ON (draft K=5)
  ├─ High-batch throughput ── OFF (overhead > save)
  └─ Accept rate < 50% ── OFF (broken)
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: Continuous Batching + PagedAttention 数学**

```
Static padding: 4 req [10, 50, 200, 100] token → pad to 200 → 800 token compute, 用 360 → 55% waste
Continuous batching: 4 req scheduled token-level, no padding, 100% used

PagedAttention: KV block 16 token, share across same-prefix req
  e.g., 1000 req 同 5K system prompt → 312 block × 1 = 312 block (vs 312K block in naive)
  → KV mem ↓ 1000x for shared prefix

Tune-able vLLM:
  --max-num-batched-tokens 8192   (per batch max compute)
  --max-num-seqs 256              (concurrent req cap)
  --enable-prefix-caching          (block share)
  --gpu-memory-utilization 0.9     (mem budget)
```
- Top 3 gotchas: (1) max-num-seqs 太低 → batch starve (2) GPU mem util 0.95+ → OOM crash (3) batch 太大 spec dec overhead 抵消收益
- Tools: vLLM 0.6+, NVIDIA Nsight profiler

**Problem 2: Parallelism — TP / PP / DP / EP, When Each**

```python
# vLLM 70B FP8 setup
vllm serve meta-llama/Llama-3.1-70B-Instruct \
  --tensor-parallel-size 8 \
  --quantization fp8 \
  --gpu-memory-utilization 0.92 \
  --max-model-len 8192 \
  --enable-prefix-caching \
  --enable-chunked-prefill

# Megatron-LM 200B training
TP=8, PP=4, DP=4 → 128 GPU, MFU 45-55% 是工业目标
```
- Top 3 gotchas: (1) TP 跨 node (NVLink 没了, 通信 kill perf) (2) PP idle bubble (small batch) (3) EP all-to-all 通信 bottleneck
- Tools: vLLM, Megatron-LM, DeepSpeed-MII, Ray Serve, FlashAttention v3

**Problem 3: Cache Hierarchy — Prefix / Semantic / Result, Server vs Client**

```
L1 Result cache (exact hash): 10-20% hit
  Key = hash(model + prompt + temperature + seed)
L2 Semantic cache (embedding): 30-50% hit FAQ workload
  Vertex AI Vector Search 0.95 threshold; per-domain tunable
L3 Prefix cache (vLLM server): 60-90% hit shared prefix
  Auto + conv_id hint
L4 Tool output cache: per-tool TTL
  get_balance 5s / static doc 24h

Vendor prefix cache discount:
  Anthropic: 90% off (1h TTL)
  OpenAI: 50% off
  Google: 75% off
```
- Top 3 gotchas: (1) semantic threshold 0.90 看似激进但 wrong-hit 是 silent kill (2) prefix cache 不 per-tenant → cross-tenant leak (3) cache invalidation 不 event-based → stale
- Tools: Redis (L1), Vertex AI Vector Search (L2), vLLM auto (L3), per-tool config (L4)

**Problem 4: Speculative Decoding + Quantization Trade-offs**

```
Spec decoding accept rate:
  Same-family draft model (Llama 3 8B for 70B): 70-80% accept
  Cross-family draft: 40-60%, often net negative
  Sweet spot: K=5, accept 70%, speedup 2-3x

Quantization quality drops (8B Llama benchmark):
  FP16: baseline
  FP8 (H100): < 0.5% drop ⭐
  INT8: 1-2% drop
  INT4 AWQ: 2-5% drop (consumer chatbot OK; legal/medical 不行)
  FP4 (B100, 2026): 2-4% drop, 4x speed

vLLM config:
  --speculative-model JackFram/llama-160m
  --num-speculative-tokens 5
  --quantization fp8 (or awq for INT4)
```
- Top 3 gotchas: (1) spec accept < 50% 关掉 (2) INT4 不 eval gate → silent regression (3) FP8 没 H100 (A100 不支持 native)
- Tools: vLLM Eagle, AutoAWQ, GPTQ, TensorRT-LLM

**Problem 5: Multi-Tenant Serving — Per-Tenant LoRA, Cost-Aware Routing**

```
S-LoRA pattern:
  Base 70B Llama frozen (140GB FP16 / 70GB FP8)
  Per-tenant LoRA adapter 50-100 MB
  GPU hot pool: 200 LoRA cached
  Cold: load from CPU RAM (50ms) or GCS (500ms)
  
vLLM: --enable-lora --max-loras 50 --lora-modules tenant1=path tenant2=path

Routing:
  Cost-aware: 90% Flash + 9% Pro + 1% Opus
  Conv-aware: sticky hash by conv_id (KV cache locality)
  Per-tenant LoRA selection by tenant_id
```
- Top 3 gotchas: (1) hot pool 满 + cold load 高频 → latency spike (2) LoRA 用 base 不匹配 (3) routing 没 sticky → KV cache miss
- Tools: vLLM Multi-LoRA, SGLang RadixAttn, LiteLLM router, Envoy hash

### 🔥 Production gotchas (top 15)

1. **Static batching pre-pad max-len**: 55% GPU waste
2. **Pre-allocate KV max_len per req**: 6MB/req × 1000 = 6GB waste, 实际 100 token 用
3. **No prefix cache for shared workload**: 5K system prompt × 1000 req = 5M token 重算
4. **TP across node (no NVLink)**: 通信 kill perf, 70B 应单节点 TP=8
5. **No quantization in 2026**: 直接 FP16 → cost 2x
6. **Spec decoding accept < 50%**: 不关掉 → overhead 净负
7. **No autoscale pre-warm**: 突发流量 cold start 30s
8. **Single GPU for 70B**: 不可能装下, 必须 TP
9. **Multi-tenant 无 LoRA share**: N tenant N replica = N× GPU cost
10. **No sticky routing for KV**: same conv 跨 pod → cache miss
11. **GPU mem util 0.95+**: 突发请求 OOM crash
12. **No eval gate for quant**: INT4 silent quality regression
13. **MoE 没 EP**: expert 分配不均 GPU 闲
14. **Long context 没 SP**: 1M context 单 GPU 装不下
15. **HF Transformers in prod**: 8 QPS/A100, 客户 cost 50x 比 vLLM

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| vLLM continuous batching + PagedAttn | Voice agent self-host | "vLLM 0.6, A100 8 → 150 QPS, 18x baseline" |
| FP8 quantization | Voice agent H100 | "FP8 quant 2x throughput, eval drop 0.3% within tolerance" |
| TP=8 70B | BNPL Llama 70B FP8 | "Single node 8×H100 NVLink, TP=8, no cross-node" |
| Spec decoding | Voice agent latency optim | "Eagle K=5 draft 8B for 70B verify, 72% accept, 2.3x latency" |
| Multi-LoRA | Voice agent 7 markets | "S-LoRA 1 base + 7 LoRA, 6x GPU saving vs 7 replicas" |
| SGLang RadixAttn | BNPL chatbot multi-turn | "SGLang multi-turn cache hit 20-30% extra vs vLLM" |
| Megatron + DeepSpeed | 200B training experiment | "TP=8 PP=4 DP=4 128 GPU, MFU 47%" |
| Cost math self-host | BNPL Llama 70B | "$0.30/1M output vs Opus $25, 80x cheaper at scale" |

### 🎤 面试现场 quotables (top 8)

1. "Continuous batching + PagedAttention is the foundation; everything else is x on top"
2. "vLLM 0.6, A100 single GPU 8B model: 150 QPS, that's 18x HF Transformers baseline"
3. "TP within node, DP across; 70B FP8 single node 8×H100 is sweet spot"
4. "FP8 (H100) is the new FP16, < 0.5% drop, default 2026"
5. "Spec decoding only if accept > 60%; otherwise overhead > saving"
6. "Multi-tenant: S-LoRA + base shared, 33x cheaper than N replicas"
7. "Anthropic prompt cache 90% off — restructure system prompt to maximize hit"
8. "Self-host 70B FP8 vLLM: $0.30/1M output, 16-80x cheaper than Opus"

### 🚨 红线 (top 10 anti-patterns)

1. Static batching pre-pad max-len (55% waste)
2. Pre-allocate KV max_len per req (mem 浪费)
3. No prefix cache for shared workload
4. 1 GPU for 70B (impossible)
5. No quantization in 2026 (cost 2x)
6. TP across node without NVLink
7. No autoscale pre-warm
8. Spec accept < 50% 不关
9. Multi-tenant no LoRA share (cost N×)
10. HF Transformers in prod (cost 50x vs vLLM)

### 📊 throughput stack 累积表

| Stack | QPS / A100 (8B, 256 token out) | Multiplier |
|---|---|---|
| HF Transformers baseline | 5-10 | 1x |
| + Continuous batching (vLLM) | 50 | 5x |
| + PagedAttention | 100 | 10x |
| + Prefix cache | 200 | 20x |
| + Speculative decoding | 400 | 40x |
| + FP8 quantization | 600 | 60x |
| + Multi-LoRA (vs 7 replicas) | 6x saving | 33x cost↓ |

### 🔢 关键 production 数字 (你简历项目)

- Voice agent TTFT: 800ms → 280ms (65% drop via 6-lever)
- BNPL Llama 70B FP8 TP=8: H100×8 NVLink, $0.30/1M output
- BNPL self-host vs hosted Opus: 80x cost ↓ at scale
- Voice agent 7 markets S-LoRA: 6x GPU saving (1 base + 7 LoRA pool)
- Voice agent Eagle spec decoding: 72% accept, 2.3x latency drop
- BNPL SGLang RadixAttn multi-turn cache: 20-30% extra hit vs vLLM
- Megatron + DeepSpeed 200B: TP=8 PP=4 DP=4, 128 GPU, MFU 47%
- Anthropic prompt cache: 90% off cached input, 1h TTL
- FP8 H100 vs FP16: 2x throughput, < 0.5% eval drop

### 🧰 2026 工具栈 quick lookup

| 类别 | 默认 | Alt | 你用过 |
|---|---|---|---|
| Inference engine | vLLM 0.6+ | SGLang, TensorRT-LLM | vLLM + SGLang ✅ |
| Training framework | Megatron + DeepSpeed | FSDP, Colossal-AI | DeepSpeed ✅ |
| Hardware | H100 80GB / H200 144GB / B100 FP4 | A100 (older) | H100 |
| Quantization | FP8 (H100 native) | AWQ INT4, GPTQ | FP8 + INT4 |
| Spec decoding | vLLM Eagle | Medusa, draft same-family | Eagle ✅ |
| Multi-LoRA | vLLM Multi-LoRA / S-LoRA | Punica | vLLM Multi-LoRA |
| Parallelism | TP within node + DP across | PP only when 200B+ | TP=8 |
| Cache | vLLM prefix + Vertex AI Vector Search semantic | Redis exact | vLLM + Vertex AI Vector Search |
| Observability | Prometheus + Grafana | NVIDIA DCGM, Nsight | Prometheus |
| Router | LiteLLM | OpenRouter, Portkey | LiteLLM
