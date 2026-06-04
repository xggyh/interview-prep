## 🎯 T3 主题：LLM Engineering System Design 全景

> HR 提示原话："**系统设计方面可能会问高吞吐、高可用、架构一致性、eventual consistency、stateless/stateful 的取舍**；**协议和工程集成上可能会问 MCP、API proxy、工具抽象、权限/安全边界**；**rate limit / queue / cache、observability / logging / tracing**。"

这是 4 个主题里**最 "system design" 的**, 也是 Google FDE 区别一般 ML engineer 的关键 round. 下面 6 个 sub-topic 各自有独立场景页. 本页负责把**LLM system 的独特属性、6 大 throughput levers、4 层 observability、4 层 cost defense、3 种 consistency 策略**讲透.

---

# Part 1 · LLM Engineering 的全景视图

## 1. 心智模型 — LLM application 不是普通 web service

**先纠正一个常见误区**:

候选人面试时, 把 LLM app 当普通 micro-service 答系统设计, 引 Designing-Data-Intensive-Applications 那套. 这是不够的, 因为 **LLM workload 有 5 个独特属性**, 改变了系统设计的所有 tradeoff.

### LLM system 的 5 个独特属性

| 维度 | Traditional web service | LLM application |
|---|---|---|
| **Single-request 延迟** | < 100ms p99 | 5-30s+ p99 (生成长度可变) |
| **Single-request cost** | Negligible (compute 摊销小) | $0.001 - $1.0 per request (token-priced) |
| **Output 确定性** | 同 input 同 output (mostly) | Non-deterministic (temperature > 0) |
| **Downstream calls** | 1-2 DB + 1 cache | 1 LLM + N tool calls + M retrieval calls |
| **Failure modes** | Network / 5xx | Network + LLM error + tool error + hallucination + rate limit + quota |

### 推论 1: 不能用普通 RPS 思维

```
普通 web service: 1 server 5k RPS, 因为 100ms × 50 cores
LLM service: 1 GPU 至多 10 RPS (30s × 7B model)
            或 100 RPS 用 continuous batching + speculative decoding

→ Capacity planning, autoscaling 都是新逻辑
```

### 推论 2: Cost 是 first-class concern

```
普通 web service: cost 是次要 metric (compute 已摊销)
LLM service: cost 是 product 经济性的核心
  - Gemini 3 Flash:   $0.50 / $3 per 1M token
  - Gemini 3 Pro:     $2 / $12 per 1M token
  - Claude Opus 4.7:  $5 / $25 per 1M token

  Bad routing:  user query 全用 Opus → 单 query $0.05 → 100 user/day × $0.05 = $5/day per user
  Good routing: 70% Flash + 25% Pro + 5% Opus → blended $0.008 → $0.80/day per user
  → 6x cost reduction
```

### 推论 3: Failure handling 是 multi-layer

```
请求失败可能是:
  - Network (重试)
  - Provider 5xx (重试 / failover provider)
  - Provider quota (queue / fallback)
  - LLM hallucination (eval-level, 不是请求级)
  - Tool failure (T1 retry / fallback)
  - User intent unparseable (clarify back)

→ Distributed-system retry vs application-level recovery, 都要 handle
```

### 推论 4: Observability 是 multi-dim

```
普通 web service: latency / error rate / RPS
LLM service: + token cost per request / model used / cache hit / eval pass rate / 用户 thumbs-up
            + per-prompt-template metrics (因为 prompt 是产品代码)
```

### 推论 5: State 是混合的

```
普通 web service: stateless app + stateful DB
LLM service: 
  - Session state (conversation_id → KV cache / message history)
  - User state (preferences, embedding profile)
  - Agent workflow state (multi-step recovery)
  - Model state (fine-tune checkpoint, lora adapter)
→ 5 种 state, 各自 lifecycle 不同
```

**Google FDE 在 T3 考的是**: 你能不能 design a production-grade LLM app considering all 5 推论. 别答得像传统 web service.

---

## 2. 核心概念地图 (ASCII)

```
                              ┌─────────────────────┐
                              │     Edge / CDN      │
                              │   - WAF, DDoS       │
                              └──────────┬──────────┘
                                         │
                              ┌─────────────────────┐
                              │     API Gateway     │
                              │   - Auth, rate      │
                              │     limit, routing  │
                              └──────────┬──────────┘
                                         │
       ┌──────────────────────────────────────────────────────────────┐
       │                  Application Layer (stateless)               │
       │                                                              │
       │   Conversation     Cost Router       MCP Proxy   Observ.     │
       │   Service        ←→ (Flash/Pro/Opus) ↑           Pipeline    │
       │      │                ↑              │              │        │
       │      │                │              │              │        │
       │   ┌──┴──┐  ┌────────┐ │  ┌──────┐  ┌─┴────┐  ┌──────┴───┐   │
       │   │Cache│  │Queue   │ │  │Rate  │  │ Tool │  │Tracing/  │   │
       │   │Layer│  │/Batch  │ │  │Limit │  │ Reg. │  │Logging   │   │
       │   └──┬──┘  └────────┘ │  └──────┘  └──┬───┘  └──────────┘   │
       │      │                │               │                     │
       └──────────────────────────────────────────────────────────────┘
              │                │               │
              ▼                ▼               ▼
       ┌──────────┐    ┌──────────────┐  ┌─────────────┐
       │ Redis    │    │ LLM Providers│  │ MCP servers │
       │ DragonFly│    │ - OpenAI     │  │ - Salesforce│
       │ (cache + │    │ - Anthropic  │  │ - Internal  │
       │ session) │    │ - Google     │  │ - Tools     │
       │          │    │ - Self-host  │  │             │
       │          │    │   (vLLM/SGL) │  │             │
       └──────────┘    └──────────────┘  └─────────────┘
              │                │
              ▼                ▼
       ┌──────────┐    ┌──────────────┐
       │ Vector   │    │  Workflow    │
       │ DB       │    │  Engine      │
       │(Vertex AI Vector Search │    │  (Temporal / │
       │ /Vertex AI Vector Search) │    │   DBOS)      │
       └──────────┘    └──────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │ Object Store │
                       │ Audit DB     │
                       │ Eval DB      │
                       └──────────────┘
```

记住这张图. T3 任何 sub-topic 都能映射到这里某一个 box.

---

## 3. 6 个核心子主题（关联的 scenario 页）

| # | Sub-topic | 核心 question | 何时被问 | 场景页 |
|---|---|---|---|---|
| **T3.1** | **Stateless vs Stateful** | 哪个 architecture 选哪个 | 多轮对话 / session 管理 | [独立页](gfde-t3-stateless-stateful.html) |
| **T3.2** | **MCP / API Proxy** | 怎么抽象 N 个 LLM + tool ecosystem | Multi-LLM 路由 / 集成 | [独立页](gfde-t3-mcp-api-proxy.html) |
| **T3.3** | **High Throughput** | 1M QPS LLM serving | Capacity / 大流量 | [独立页](gfde-t3-high-throughput.html) |
| **T3.4** | **Observability** | Trace / log / metric 怎么做 | 出事故 / debug 类问题 | [独立页](gfde-t3-observability.html) |
| **T3.5** | **Rate Limit / Queue / Cache** | LLM API 慢 + 贵 + rate-limited, 怎么扛 | Cost / SLA / 流量类 | [独立页](gfde-t3-rate-limit-queue-cache.html) |
| **T3.6** | **Eventual Consistency** | Multi-step agent workflow partial commit | 复杂工作流 / 事务类 | [独立页](gfde-t3-eventual-consistency.html) |

### 子主题段落速览

**T3.1 Stateless vs Stateful**: ChatGPT-style API 是 stateless (client 维护 conversation_id, server 每次 rebuild context). Voice agent / 多轮低延迟场景才 stateful. **生产默认 stateless**, 但混合也常见 (e.g., session-level prefix cache 是 server 侧 stateful 优化, 但语义上对外仍 stateless).

**T3.2 MCP / API Proxy**: MCP 是 Anthropic 2024 提出的 open standard, 把 tool / resource / prompt 通过 JSON-RPC 暴露, vendor-neutral. API Proxy 层负责跨 LLM 路由 (OpenAI / Anthropic / Google), 处理认证 / quota / retry / cost tracking. **生产**: 大型 SaaS 必须自建 proxy, 不直接调 vendor API.

**T3.3 High Throughput**: 1M QPS LLM 几乎不可能, 但通过 **continuous batching + PagedAttention + prefix caching + speculative decoding + tensor parallelism + quantization** 6 个 lever, 可以从 10 QPS/GPU 推到 100-500 QPS/GPU. 你简历 vLLM/SGLang 是关键 hook.

**T3.4 Observability**: 4 层 — distributed tracing (OpenTelemetry / Jaeger) + LLM-specific (LangSmith / Phoenix / Helicone, 看 prompt + completion + token) + cost tracking (per-user / per-feature) + quality monitoring (eval-in-prod, drift detect).

**T3.5 Rate Limit / Queue / Cache**: 4 层防御 — cache (semantic + exact, 30-50% hit) → queue (priority by tier) → rate limit (token bucket, per-user / per-tenant) → cost-aware routing (cheap model first). 平均 5-10x cost reduction without quality loss.

**T3.6 Eventual Consistency**: Agent 跑 5 步, 第 3 步崩了, 前 2 步副作用怎么处理? 3 种 — Saga (compensate forward) / Outbox (intent table + reliable worker) / Workflow Engine (Temporal / DBOS). 生产推荐 Workflow Engine, 不要 reinvent.

---

## 4. 设计 Patterns 速查表

### Pattern A: Stateless API with Client-side Conversation ID

```python
# Client maintains conversation_id (in cookie / app state)
POST /chat
{
  "conversation_id": "conv_abc123",
  "user_message": "follow-up question"
}

# Server (stateless):
def chat_handler(req):
    history = db.fetch_history(req.conversation_id)
    response = llm.complete(history + [req.user_message])
    db.append_to_history(req.conversation_id, req.user_message, response)
    return response
```

**优**: horizontally scalable, any pod can handle any request.

### Pattern B: Stateful Session for Voice (low-latency)

```python
# WebSocket connection per call, server holds session
class VoiceSession:
    def __init__(self, call_id):
        self.kv_cache = None  # prefix cache, GPU-resident
        self.history = []
        
    async def on_audio_chunk(self, chunk):
        text = await asr(chunk)
        # Reuse KV cache → save 50% latency
        response = await llm.stream(self.history + [text], kv_cache=self.kv_cache)
        self.kv_cache = response.new_kv_cache
        ...

# Sticky session via WebSocket, but: if pod dies → reconnect to any pod, lose 200ms re-warm
```

**何时用**: voice agent / gaming agent — < 500ms 强 latency 要求.

### Pattern C: Cost-Aware Model Routing

```python
def route(query, history, user_tier):
    complexity = classify_complexity(query, history)
    
    # Tier 1: gold users get best model
    if user_tier == "gold" and complexity > 0.5:
        return "claude-opus-4.7"
    
    # Tier 2: by complexity
    if complexity < 0.3:
        return "gemini-3-flash"      # $0.50 / $3 per 1M
    elif complexity < 0.7:
        return "gemini-3-pro"        # $2 / $12 per 1M
    else:
        return "claude-opus-4.7"     # $5 / $25 per 1M
```

**实际效果** (你 BNPL chatbot 数据可参考): blended cost 从 $5/1M 降到 $0.85/1M (5-6x cheaper).

### Pattern D: Saga / Outbox for multi-step Agent

```python
def agent_workflow(user_intent):
    workflow_id = uuid4()
    steps = plan(user_intent)
    
    for step in steps:
        outbox.write({
            "workflow_id": workflow_id,
            "step_id": step.id,
            "tool": step.tool,
            "args": step.args,
            "status": "pending",
        })
    
    # Reliable worker picks up + executes
    for step in steps:
        try:
            result = execute(step)
            outbox.update(step.id, status="done", result=result)
        except Exception as e:
            # Compensate previous steps
            for prev_step in reversed(steps[:steps.index(step)]):
                run_compensation(prev_step)
            outbox.update(step.id, status="failed", error=str(e))
            raise
```

### Pattern E: 4-Layer Observability Pipeline

```python
@trace_span("agent_request")
def handle_request(req):
    with otel_span("query_understanding") as span:
        span.set_attribute("query.original", req.query)
        rewritten = rewrite(req.query)
        span.set_attribute("query.rewritten", rewritten)
    
    with otel_span("retrieval") as span:
        retrieved = retrieve(rewritten)
        span.set_attribute("retrieval.docs_count", len(retrieved))
    
    with otel_span("llm_generation") as span:
        response = llm.complete(...)
        span.set_attribute("llm.model", response.model)
        span.set_attribute("llm.input_tokens", response.input_tokens)
        span.set_attribute("llm.output_tokens", response.output_tokens)
        span.set_attribute("llm.cost_usd", calc_cost(response))
    
    # Sampled eval in prod
    if random.random() < 0.01:
        eval_score = run_eval(req.query, response.text)
        otel_metric("eval_score").record(eval_score)
    
    return response
```

---

# Part 2 · 深度教学 (4 个系统化框架)

## 5. 系统化框架 1: 6 个 High-Throughput Levers (LLM serving 提速 5-50x)

普通 LLM serving (HuggingFace Transformers stock) ≈ 5-10 QPS / A100 GPU. 经过 6 个 lever 可以推到 100-500 QPS / A100 (50x).

### Lever 1: Continuous Batching (动态拼批)

```
传统 static batch:
  [req1 | req2 | req3 | req4]  长度都 padding 到最长那个 → GPU 利用率低
  必须等批满才发, 单批延迟高
  
Continuous batching (vLLM):
  - Token-level scheduling
  - 一个 req 完成立刻把新 req 拼进 batch
  - 无 padding 浪费
  - 5-10x throughput
```

**Reference**: vLLM (UC Berkeley), TGI (HuggingFace), TensorRT-LLM (NVIDIA).

### Lever 2: PagedAttention (KV cache 像 OS 内存)

```
传统 KV cache:
  每 req 预分配 max-seq-len 内存 (e.g., 4k token × 768 dim × FP16 = 6MB)
  实际只用了 100 token → 浪费 98%
  
PagedAttention (vLLM):
  - KV cache 按 page (e.g., 16 token) 切分
  - 按需分配, 像 OS 页表
  - 多 req 共享 page (e.g., 共同 prefix)
  - 24x more concurrent requests in same GPU memory
```

### Lever 3: Prefix Caching (共享 system prompt)

```
场景: 1000 user 同问问题, 每 req 都带相同 5k token system prompt
传统: 5k × 1000 = 5M token 重复计算
Prefix cache: 系统 prompt 计算 1 次, 缓存 KV
  → 后续 999 req 跳过这 5k 计算
  → 2-3x throughput for prompt-cache-friendly workload
  
Anthropic / OpenAI / Google 现在 API 层就支持 prompt caching
  - Anthropic: 90% off cached input (1h cache TTL)
  - OpenAI: 50% off cached prefix
  - Google: 75% off cached
```

### Lever 4: Speculative Decoding (小模型起草 + 大模型验证)

```
传统: 大模型每 token forward 1 次, 慢
Speculative:
  Step 1: 小 draft model (e.g., 0.5B) 提前生成 5 token
  Step 2: 大 verifier model (e.g., 70B) 1 次 forward 验证全部 5 token
    - 如果都对 → 5 token 一次出 → 5x 加速
    - 如果第 3 个错 → 接受前 2, 大模型 resume
  
  Net effect: 2-3x latency reduction
  Cost: 额外 ~5% compute on draft, value/cost 强
```

**生产使用**: Anthropic / Google 内部用 (官方未公开 detail), Eagle / Medusa 是开源等价物.

### Lever 5: Tensor Parallelism (TP) — 模型 split 多 GPU

```
70B model FP16 = 140GB. 单 A100 80GB 装不下.
TP: weight matrix 沿 hidden dim 切, 多 GPU 各持一部分
  - 8 GPU TP, 每 GPU 持 1/8 weight (17.5GB)
  - 一次 forward 多 GPU 协作
  - 通信开销 ~10-15%, but allows bigger model
  
Best for: 70B+ model, 强延迟需求
Tools: vLLM, SGLang, DeepSpeed, Megatron-LM
```

### Lever 6: Quantization (压缩权重)

```
FP16 → INT8: 模型大小 ↓50%, throughput ↑1.5-2x, quality ↓1-3%
FP16 → INT4 (GPTQ / AWQ): 模型大小 ↓75%, throughput ↑2-3x, quality ↓3-5%
FP8 (Hopper, Blackwell GPU): nearly FP16 quality, ↓50% mem, ↑1.5x throughput

→ 选取决于 quality budget. 客服 chatbot INT4 OK, 法律分析 FP16 must
```

### 综合 throughput 提升表 (你简历 vLLM 的硬实力)

| Stack | QPS / A100 (8B model, 256 token output) | 相对 baseline |
|---|---|---|
| **HF Transformers (baseline)** | 5-10 | 1x |
| **+ Continuous batching** | 50 | 5x |
| **+ PagedAttention** | 100 | 10x |
| **+ Prefix cache** | 200 | 20x |
| **+ Speculative decoding** | 400 | 40x |
| **+ INT8 quantization** | 600 | 60x |
| **+ TP 4-way** (70B model)** | scales differently, ~ 50 QPS @ 70B | n/a |

**你简历**: "GPU-accelerated inference with vLLM, SGLang" → 提到 PagedAttention + continuous batching 是 必杀 quote.

**生产场景**:

- BNPL chatbot 用 vLLM serving Llama 3.1 8B fine-tuned, prefix cache + continuous batching = 60% cost reduction vs hosted API
- Voice agent 用 SGLang 因为 RadixAttention prefix tree, multi-turn cache 更佳

---

## 6. 系统化框架 2: 4-Layer Observability (LLM 系统专属)

普通 web service: Latency / Error / Throughput (RED method) 就够.

LLM system 需要 4 层, 每层有专门工具:

### Layer 1: Distributed Tracing (OpenTelemetry standard)

```
1 user query → N spans:
  - http.request
    - auth.verify
    - rate_limit.check
    - cache.lookup (miss)
    - llm.query_rewrite
    - retrieval.vector_search
    - retrieval.bm25_search
    - retrieval.rerank
    - llm.generation
    - tool.get_order (called by LLM)
    - tool.send_email (called by LLM)
    - audit.log
    - http.response

Each span: start/end, attributes (e.g., llm.model, tool.name, retrieval.docs_count), status
Tools: Jaeger / Zipkin / Tempo (Grafana) / DataDog APM
```

**关键 attribute** 必须 instrument:
- `llm.model`, `llm.input_tokens`, `llm.output_tokens`, `llm.cost_usd`
- `tool.name`, `tool.duration_ms`, `tool.outcome`
- `retrieval.method`, `retrieval.docs_count`, `retrieval.top1_score`
- `user.tier`, `tenant.id`, `session.id`

### Layer 2: LLM-Specific Tracing (prompt + completion 级别)

OpenTelemetry trace 不够细 — 你需要看 **prompt 全文 + completion 全文**.

| 工具 | 提供 | Best for |
|---|---|---|
| **LangSmith** (LangChain) | Full prompt/completion log, eval datasets, A/B framework | LangChain 用户 |
| **Phoenix / Arize** | Open-source, RAG-specific traces, eval | 自部署 |
| **Helicone** | Drop-in proxy, no code change | 快速接入 |
| **Langfuse** | Open-source, traces + eval + prompt mgmt | 自部署 |
| **W&B Weave** | Trace + eval + experiment tracking | ML team 已用 W&B |

**关键 view**:
- Per-prompt-template metrics (因为 prompt = product code)
- Token cost 趋势
- Eval pass rate (sampled)
- Per-tool error rate

### Layer 3: Cost Tracking (per-user / per-feature)

```python
class CostTracker:
    def record(self, user_id, feature, model, input_tokens, output_tokens):
        price = MODEL_PRICING[model]
        cost = (input_tokens * price.input + output_tokens * price.output) / 1_000_000
        
        # Per-user (daily/monthly aggregate)
        redis.hincrby(f"cost:user:{user_id}:{today()}", "total", int(cost * 10000))
        
        # Per-feature
        redis.hincrby(f"cost:feature:{feature}:{today()}", "total", int(cost * 10000))
        
        # Per-model
        redis.hincrby(f"cost:model:{model}:{today()}", "total", int(cost * 10000))
        
        # Alert if user exceeds quota
        daily_total = int(redis.hget(f"cost:user:{user_id}:{today()}", "total")) / 10000
        if daily_total > USER_DAILY_LIMIT[user_tier(user_id)]:
            alert("user_quota_exceeded", user_id, daily_total)
            raise QuotaExceeded
```

**Dashboard 必备**:
- Daily/monthly spend trend (per-tenant)
- Cost per active user (LTV-relevant)
- Cost per feature (kill expensive feature ideas)
- Cost per query trend (catch regression)

### Layer 4: Quality Monitoring (eval-in-prod, drift)

LLM 不像 traditional code, 没有 unit test 能保护 prod. 必须 continuous eval.

```python
def sampled_eval(req, response):
    if random.random() > 0.01:  # 1% sample
        return
    
    # Auto eval via LLM judge
    eval_dimensions = ["faithfulness", "relevance", "completeness", "safety"]
    scores = {}
    for dim in eval_dimensions:
        scores[dim] = llm_judge(req.query, response.text, dim)
    
    # Log to eval DB
    eval_db.insert({
        "ts": now(),
        "query": req.query,
        "response": response.text,
        "model": response.model,
        "scores": scores,
        "prompt_template_version": PROMPT_VERSION,
    })
    
    # Real-time alert if scores drop
    if scores["faithfulness"] < 0.6:
        alert("low_faithfulness", req, response, scores)
```

**Drift 检测**:
- Per-prompt-template eval score 7-day trend
- Model version change → eval delta
- Retrieved doc distribution shift

**工具**: Braintrust, Phoenix, Langfuse, custom in-house pipeline.

### 综合 dashboard 必备 view

```
┌──────────────────────────────────────────────────────────┐
│ Top dashboard widgets (60s glance):                     │
│                                                          │
│ 1. P50/P99 latency by model (multi-line)                │
│ 2. Error rate by model + tool (heatmap)                  │
│ 3. Daily spend (per-tenant pie + trend line)             │
│ 4. Cache hit rate (semantic + result, 7-day)             │
│ 5. Eval scores per prompt template (drift detection)     │
│ 6. Tool latency p99 (top 10 tools)                       │
│ 7. Per-user thumbs-up rate (product NPS)                 │
│ 8. Token usage distribution (find heavy users)           │
└──────────────────────────────────────────────────────────┘
```

---

## 7. 系统化框架 3: 4-Layer Cost Defense (rate limit / queue / cache)

LLM API 慢 + 贵 + 限流 + non-deterministic. 不做 cost defense, blended cost 高 5-10x.

### Layer 1: Caching (most cost-saving)

```
┌─────────────────────────────────────────────────────────┐
│ A. Exact-match result cache                            │
│    Key: hash(model + prompt + temperature + seed)       │
│    TTL: 1h - 7d depending on feature                    │
│    Hit rate: 5-15% (only exact same query)              │
│                                                         │
│ B. Semantic cache                                       │
│    - Embed query, lookup in vector cache                │
│    - If similarity > 0.95 → return cached response      │
│    - Hit rate: 30-50% on FAQ-style workload             │
│    - Risk: false positive (回答错的 cache)              │
│      → use threshold 0.97+ for safety-critical          │
│                                                         │
│ C. Prefix cache (provider-level)                        │
│    - Anthropic / OpenAI / Google 已支持                 │
│    - 90% off cached input (Anthropic), 50% (OpenAI)     │
│    - 1h cache TTL                                       │
│    - Strategy: 把 system prompt + few-shot examples     │
│      放最前面 → max cache benefit                       │
└─────────────────────────────────────────────────────────┘

Combined cache hit rate target: 30-50% blended cost reduction
```

### Layer 2: Queue (smooth burst, fairness)

```python
class PriorityQueue:
    """Per-tenant + per-priority queue"""
    
    def enqueue(self, request):
        tier = user_tier(request.user_id)
        priority = TIER_PRIORITY[tier]  # gold=1, silver=2, bronze=3
        
        # Check per-tenant in-flight quota
        in_flight = redis.get(f"inflight:{request.tenant_id}") or 0
        if in_flight >= MAX_INFLIGHT[tier]:
            return self.push_to_wait_queue(request, priority)
        
        redis.incr(f"inflight:{request.tenant_id}")
        return self.dispatch(request)
    
    def push_to_wait_queue(self, request, priority):
        # Use Redis sorted set, score = priority + timestamp
        score = priority * 1e10 + time.time()
        redis.zadd(f"wait:{request.tenant_id}", {request.id: score})
```

**Why**: burst protection + fairness (gold user not starve).

### Layer 3: Rate Limit (defense)

```python
# Token bucket per dimension
def check_rate_limit(req):
    checks = [
        rate_limit(f"user:{req.user_id}", limit=100, window=60),       # 100/min per user
        rate_limit(f"tenant:{req.tenant_id}", limit=10000, window=60), # 10k/min per tenant
        rate_limit(f"global:{req.model}", limit=PROVIDER_QUOTA[req.model]),
    ]
    if not all(checks):
        raise RateLimitExceeded
```

**Granularity**: per-user → per-tenant → per-API-key → per-model → global. 多维拒绝防一类滥用拖死全局.

### Layer 4: Cost-Aware Model Routing

```python
def route(query, history, user_tier, budget_remaining):
    complexity = classify_complexity(query, history)
    
    # Budget exhausted → cheap or refuse
    if budget_remaining < 0.01:
        if user_tier == "gold":
            return "gemini-3-flash"  # degraded but cheap
        else:
            raise BudgetExhausted
    
    # Normal routing
    if complexity < 0.3:
        return "gemini-3-flash"      # 70% queries
    elif complexity < 0.7:
        return "gemini-3-pro"        # 25%
    else:
        return "claude-opus-4.7"     # 5%
```

**Blended cost reduction**: 5-10x without quality loss (BNPL chatbot 你的 case).

### 综合: 4-layer 累计效果

| Layer | Cost reduction | 配合 |
|---|---|---|
| **L1 Cache** (semantic 40% hit) | 40% | 全 layer |
| **L2 Queue** (smooth) | 0% (但 SLA 改善) | L3 |
| **L3 Rate Limit** | 0% (但防滥用) | L1 |
| **L4 Routing** (cheap model 70%) | 5-6x | L1 |
| **Combined** | **8-12x** total | |

> "Without cost defense: $5 per 1M token (all Opus)
> With 4 layers: $0.5-0.8 per 1M (blended) = 6-10x cheaper"

---

## 8. 系统化框架 4: Eventual Consistency 3 patterns (Saga / Outbox / Workflow)

Agent 跑 5 步, 第 3 步 crashed. 前 2 步副作用 (DB write, API call) 怎么处理?

### Pattern A: Saga (compensating actions)

```
执行 forward: A → B → C
若 C 失败: 反向 compensate: C.undo() → B.undo() → A.undo()

适合: 短工作流 (< 10 步), 每步都有明确 undo

例:
  A. Create order (DB insert)
  B. Reserve inventory (call inventory API)
  C. Charge card (call Stripe) ← 失败
  
  Compensation:
  C.undo() — 取消 charge intent (Stripe void)
  B.undo() — release inventory reservation
  A.undo() — mark order as cancelled
```

**Code**:

```python
class Saga:
    def __init__(self):
        self.completed_steps = []
    
    async def run(self, steps):
        for step in steps:
            try:
                result = await step.forward()
                self.completed_steps.append((step, result))
            except Exception as e:
                # Compensate completed steps in reverse
                for prev_step, prev_result in reversed(self.completed_steps):
                    try:
                        await prev_step.compensate(prev_result)
                    except Exception as compensation_err:
                        # Compensation 自己失败了 → alert ops, manual recovery
                        log_critical(f"Compensation failed: {prev_step}")
                raise e
```

**陷阱**: compensation 自己也可能失败. 必须有 manual recovery path.

### Pattern B: Outbox (transactional intent log)

```
每步: 先写 intent 到 outbox table (同 transaction with business state)
独立 worker poll outbox, 执行后 mark done
Retry until success (with idempotency key)

适合: 跨服务 / 跨数据库 / 不确定 downstream 可用性
```

```python
def step_with_outbox(business_action):
    with db.transaction():
        result = business_action()  # e.g., update order status
        outbox.insert({
            "id": uuid4(),
            "action": "send_email",
            "args": {"to": user.email, "template": "order_confirmed"},
            "status": "pending",
            "idempotency_key": uuid4(),
        })
    
    # Worker poll separately:
    while True:
        pending = outbox.fetch(status="pending", limit=100)
        for item in pending:
            try:
                execute_action(item.action, item.args, item.idempotency_key)
                outbox.update(item.id, status="done")
            except Exception as e:
                outbox.update(item.id, status="failed", error=str(e))
                # Retry with backoff
```

**优**: at-least-once 保证. **缺**: 单独 worker, 复杂.

### Pattern C: Workflow Engine (Temporal / DBOS / Inngest)

```python
# Temporal-style workflow as code
@workflow.defn
class OrderProcessing:
    @workflow.run
    async def run(self, order_id):
        # Each step is durable, auto-replayed on crash
        await workflow.execute_activity(create_order, order_id, retry_policy=RetryPolicy(maximum_attempts=3))
        await workflow.execute_activity(reserve_inventory, order_id)
        
        try:
            await workflow.execute_activity(charge_card, order_id)
        except ActivityError:
            # Workflow auto-runs compensation
            await workflow.execute_activity(release_inventory, order_id)
            await workflow.execute_activity(cancel_order, order_id)
            raise
        
        await workflow.execute_activity(send_confirmation, order_id)
```

**Temporal magic**: workflow state persistent, 任何步骤 crash, restart 时从 last checkpoint resume. 你不写 outbox / state machine code, framework 帮你.

**适合**: 复杂多步骤 agent workflow / 长时间 (天 / 周) workflow / 跨服务编排.

### 选哪个

| 场景 | 推荐 |
|---|---|
| 简单 2-3 步 + clear compensation | Saga |
| 跨服务 + 不要 framework lock-in | Outbox |
| 5+ 步 / 长时间 / 状态恢复关键 | **Workflow engine (Temporal) ⭐** |

**FDE 加分**: 提 Temporal / DBOS by name, 表示你知道 industry direction.

---

# Part 3 · Production gotchas + 现场 + Cheat sheet

## 9. Production Gotchas

| Gotcha | 现象 | 防御 |
|---|---|---|
| **Cost spike from infinite loop** | Agent self-call until $1000 spent | Per-session cost cap + max iterations + auto-stop |
| **Timeout propagation** | Outer 30s timeout, inner LLM call 25s, retry layered fails | Budget-aware timeout (deadline propagation) |
| **Provider rate limit** | OpenAI 429 in burst | Multi-provider failover (OpenAI → Anthropic → self-host) |
| **KV cache thrash** | New session every request, no prefix cache hit | Stable system prompt + sticky session for repeat users |
| **Streaming partial output** | LLM stream interrupted, client gets half | Resumable stream (anchor token + replay) or full retry |
| **Log explosion** | Logging full prompt + completion → TB/day | Sampled logging + redaction + tiered storage |
| **PII in prompt** | User pastes credit card → logs / cache leak | PII detection + redaction before LLM call |
| **Model deprecation** | OpenAI deprecates gpt-4, your prompt only works there | Multi-model eval before deprecation, prompt portability test |
| **Workflow stuck** | Agent step pending forever (waited for human, human gone) | Time-bound waits, escalation on stuck |
| **Cache poisoning** | Bad response cached, served to many | Eval-gated cache write, invalidation API |
| **Tenant isolation breach** | User A's cache served to user B (semantic match) | Per-tenant cache namespace |
| **Eval drift unnoticed** | New prompt deployed, faithfulness drops, no alert | Pre-deploy eval gate + post-deploy drift alarm |
| **Cost dashboard wrong** | Forgot to count cached input → underestimate | Use provider's reported cost (response.usage), not your guess |

---

## 10. Anthropic / OpenAI / Google 2026 Engineering 生态

| 进展 | 出处 | FDE 影响 |
|---|---|---|
| **MCP 1.0** (Anthropic 2024) | open standard | 客户 internal API → MCP server, FDE 主流交付 |
| **Prompt caching 普及** | Anthropic / OpenAI / Google | Long-context 经济性翻转, RAG 边界变化 |
| **Multi-LLM routing 普及** | LiteLLM, OpenRouter | 自建 proxy 路由层是大客户标配 |
| **Workflow engines** | Temporal Cloud, DBOS, Inngest | 替代手写 Saga / Outbox 的事实标准 |
| **Observability SaaS** | LangSmith, Helicone, Langfuse | 客户期望 in-house dashboard, 整合现有 OTel |
| **vLLM / SGLang OS adoption** | UC Berkeley, Stanford | Self-host LLM 服务的事实标准 |
| **Eval frameworks** | OpenAI Evals, Anthropic Evals, Braintrust | 必须有 eval suite, 否则 prompt 改动靠 vibes |

**FDE 加分**: 主动提 Temporal / vLLM / LangSmith / MCP — 这是 senior IC 的语言.

---

## 11. 45-min 面试节奏 (T3 通用版)

| 时长 | 阶段 | 你该做什么 |
|---|---|---|
| **0-5 min** | Clarify | "QPS? p99 SLA? Cost budget? Single-region or global? Multi-tenant?" 至少 5 问 |
| **5-10 min** | Mental model | LLM system 的 5 个独特属性 (Section 1.1), 然后画 Section 2 那张架构图 |
| **10-25 min** | Deep-dive | 面试官 zoom-in 一个 sub-topic. 用 Section 4 pattern + Section 5-8 框架展开 |
| **25-35 min** | Tradeoffs | 主动讲 cost math, blended pricing, 6 个 throughput lever |
| **35-42 min** | Failure modes | Section 9 至少 3-5 个 gotcha |
| **42-45 min** | 简历 quote | "On voice agent / BNPL chatbot / Internal Agent Platform" |

**关键 framing**: T3 是 system design, 不是 ML. 主动用 distributed-system / SRE / cost optimization 语言.

---

## 12. 你简历对应 hook (具体 story arc)

| Sub-topic | 你简历 hook | 完整 story arc |
|---|---|---|
| **T3.1 Stateless vs Stateful** | Voice agent (stateful) + BNPL chatbot (stateless) | "Voice agent 7 markets 是 stateful WebSocket session — call 期间 server 持 KV cache + ASR/TTS pipeline. 失败重连有 200ms re-warm 成本. BNPL chatbot 反之 stateless — REST API + Redis session blob, 任何 pod 都能 serve. 决定因素: voice latency < 500ms, chatbot 接受 2-5s p99" |
| **T3.2 MCP / API Proxy** | Internal Agent Platform | "ByteDance Internal Agent Platform — 我们做了 unified tool catalog (类 MCP server pattern), 各业务 team register tool, 平台层统一 auth / versioning / quota / cost meter. LLM proxy 层路由到 self-host (vLLM) or hosted (OpenAI / Anthropic / Google), 一套 SDK, fail-over 自动" |
| **T3.3 High Throughput** | vLLM + SGLang + DeepSpeed (简历明示) | "Voice agent self-host LLM 用 vLLM (continuous batching + PagedAttention + prefix cache), Llama 3.1 8B fine-tuned, 单 A100 sustained 150 QPS (vs HF Transformers baseline 8 QPS, 18x speedup). BNPL chatbot 用 SGLang 因 RadixAttention 在 multi-turn cache 更佳, 20-30% extra hit rate" |
| **T3.4 Observability** | Voice agent 7 markets weekly metric review | "Voice agent 每周 review: per-market p99 latency, error rate by ASR/TTS/LLM 三段, eval score (CER, intent accuracy), 用户 hangup rate. 加了 LangSmith 的 prompt-level tracing 后, 一次 catch 到 Indonesian prompt 因 LLM 升级 faithfulness drop 12%, 提前 rollback" |
| **T3.5 Rate Limit / Queue / Cache** | TikTok PayLater scale + voice agent | "PayLater chatbot peak 5k QPS. 4-layer: (1) semantic cache (Vertex AI Vector Search, threshold 0.97) hit 35%; (2) priority queue (Gold tenant 优先, 5% traffic); (3) token bucket per user / tenant; (4) cost-aware routing — 70% Flash, 25% Pro, 5% Opus. Blended cost $0.85/1M vs all-Opus $5/1M, 6x savings. 同 quality (faithfulness ≥ 0.85)" |
| **T3.6 Eventual Consistency** | Indonesia refund tier + Voice agent retry | "Refund tier 3 (> $200) 是 multi-step: (1) lookup customer history; (2) call risk score; (3) write ledger entry; (4) trigger fund return API; (5) send confirmation. 用 Temporal workflow — step 3 失败自动 compensate step 1-2, alert ops. 比起手写 outbox + saga, dev velocity 3-4x, bug 显著少" |

**面试主动 quote 范例**:

> "On the BNPL chatbot, the throughput story was about **layered defense, not single bullet**. We had: 35% semantic cache hit (Vertex AI Vector Search, 0.97 threshold) + priority queue for Gold tier + token bucket rate limit + cost-aware model routing across Gemini 3 Flash / Pro / Claude Opus. Net result: blended cost $0.85/1M tokens vs $5/1M if we'd run everything on Opus — 6x reduction, same quality. The hardest part wasn't picking the techniques; it was the **eval harness to prove no quality regression** across the cheaper routes."

---

## 13. Cheat Sheet (印 1 页)

```
═══════════════════════════════════════════════
T3: LLM Engineering System Design 全景
═══════════════════════════════════════════════

CORE INSIGHT:
  LLM system ≠ traditional web service.
  5 独特属性:
    - 30s request (vs 100ms)
    - $0.001 - $1 per request
    - Non-deterministic output
    - 1 req → N downstream
    - Cost is first-class

6 SUB-TOPICS:
  T3.1 Stateless vs Stateful  (default stateless, voice 例外)
  T3.2 MCP / API Proxy        (unified abstraction)
  T3.3 High Throughput        (6 levers, 5-50x speedup)
  T3.4 Observability          (4-layer, OTel + LangSmith)
  T3.5 Rate Limit/Queue/Cache (4-layer cost defense)
  T3.6 Eventual Consistency   (Saga / Outbox / Workflow)

5 PATTERNS:
  A. Stateless API + client conv_id
  B. Stateful WebSocket (voice only)
  C. Cost-aware model routing
  D. Saga / Outbox workflow
  E. 4-layer observability pipeline

6 THROUGHPUT LEVERS (vs HF Transformers baseline 1x):
  1. Continuous batching       5-10x
  2. PagedAttention            24x concurrency
  3. Prefix caching            2-3x
  4. Speculative decoding      2-3x latency
  5. Tensor Parallelism        bigger model
  6. INT8 quantization         1.5-2x
  Combined (8B model on A100): 50-60x baseline

4-LAYER OBSERVABILITY:
  L1 Distributed Tracing (OTel + Jaeger)
  L2 LLM-specific (LangSmith / Phoenix / Helicone / Langfuse)
  L3 Cost Tracking (per-user / feature / model)
  L4 Quality Monitor (sampled eval + drift)

4-LAYER COST DEFENSE:
  L1 Cache (exact + semantic + prefix)  40% reduction
  L2 Queue (priority by tier)            SLA保
  L3 Rate Limit (token bucket multi-dim) 防滥用
  L4 Cost-aware Routing (Flash/Pro/Opus) 5-6x reduction
  Combined: 8-12x total

3 CONSISTENCY PATTERNS:
  Saga          → 简单 2-3 步 + clear compensate
  Outbox        → 跨服务 / no framework
  Workflow ⭐   → Temporal / DBOS / Inngest (5+ steps)

2026 MODEL PRICING:
  Gemini 3 Flash:   $0.50 / $3 per 1M
  Gemini 3 Pro:     $2 / $12
  Claude Opus 4.7:  $5 / $25
  Sonnet 4.7:       ~$3 / $15
  
  Blended (70/25/5 routing): ~$0.85/1M  (vs $5/1M all-Opus)
  + Cache (40% hit): ~$0.5/1M
  → 10x savings without quality loss

PRODUCTION GOTCHAS (top 10):
  1. Cost runaway (per-session cap)
  2. Timeout propagation (deadline)
  3. Provider rate limit (multi-provider failover)
  4. KV cache thrash (stable prompt)
  5. PII in prompt (redact)
  6. Cache poisoning (eval-gated write)
  7. Tenant isolation (per-tenant namespace)
  8. Eval drift (pre/post deploy gates)
  9. Streaming interrupt (resumable)
  10. Provider deprecation (multi-model eval)

45-MIN ANSWER RHYTHM:
  0-5    Clarify (QPS, SLA, cost budget, multi-tenant?)
  5-10   Mental model (5 unique properties + arch image)
  10-25  Deep-dive 1 sub-topic + pattern
  25-35  Tradeoffs + cost math
  35-42  Failure modes (3-5 gotchas)
  42-45  Resume quote ("On voice agent / BNPL...")

YOUR RESUME HOOKS:
  Voice agent stateful WebSocket → T3.1
  Internal Agent Platform        → T3.2
  vLLM/SGLang/DeepSpeed          → T3.3 (你的 strongest)
  Voice agent 7 markets metrics  → T3.4
  TikTok PayLater scale          → T3.5
  Indonesia refund tier          → T3.6

RED LINES:
  - Treat LLM service like普通 web service (lose immediate)
  - 不提 cost (FDE 死穴)
  - "Use exactly-once delivery" (网络分布式不存在)
  - 不提 eval drift / quality monitoring
  - 不能 ID Temporal / vLLM / MCP by name
```
