## 🎯 T3 主题：LLM Engineering System Design 全景

> HR 提示原话："**系统设计方面可能会问高吞吐、高可用、架构一致性、eventual consistency、stateless/stateful 的取舍**；**协议和工程集成上可能会问 MCP、API proxy、工具抽象、权限/安全边界**；**rate limit / queue / cache、observability / logging / tracing**。"

---

## 1. 心智模型 — LLM application 是 distributed system + AI failure modes

不是 traditional web service：
- 单 request 可能 30s + (vs 100ms)
- Per-request cost $0.01 - $1 (vs ~free)
- Output non-deterministic
- Tool calls 让 1 request → 多 downstream call
- Failure mode 多: model error + tool error + LLM hallucination + 上游 API quota

**Google FDE 在 T3 考的是**: 你能不能 design a production-grade LLM app considering all these.

---

## 2. 6 个核心子主题（对应场景题）

| # | Sub-topic | 核心 question | 场景页 |
|---|---|---|---|
| **T3.1** | **Stateless vs Stateful** | 哪个 architecture 选哪个 | [独立页](gfde-t3-stateless-stateful.html) |
| **T3.2** | **MCP / API Proxy** | 怎么抽象 N 个 LLM + tool ecosystem | [独立页](gfde-t3-mcp-api-proxy.html) |
| **T3.3** | **High Throughput** | 1M QPS LLM serving | [独立页](gfde-t3-high-throughput.html) |
| **T3.4** | **Observability** | Trace / log / metric 怎么做 | [独立页](gfde-t3-observability.html) |
| **T3.5** | **Rate Limit / Queue / Cache** | LLM API 慢 + 贵 + rate-limited, 怎么扛 | [独立页](gfde-t3-rate-limit-queue-cache.html) |
| **T3.6** | **Eventual Consistency** | Multi-step agent workflow partial commit | [独立页](gfde-t3-eventual-consistency.html) |

---

## 3. Stateless vs Stateful — 决策矩阵

| Aspect | Stateless | Stateful |
|---|---|---|
| **Per-request** | 重建全 context | Server-side session |
| **Scalability** | Horizontal trivially | Sticky session required |
| **Latency** | + context rebuild cost (~100ms) | Low (memory cached) |
| **Failover** | Trivial (request to any node) | Need state replication / re-warm |
| **Cost** | More tokens per request | Less tokens (state cached) |
| **Best for** | OpenAI ChatGPT (default!) | Real-time multi-turn, low-latency |

**Production 默认 stateless** + **client maintains conversation_id**. Server side rebuilds context from KV cache + DB on each call. 这是 OpenAI / Google API 标准 model.

**Stateful 例外**: voice agent (latency sensitive, < 500ms), gaming bot, low-volume high-engagement.

---

## 4. MCP (Model Context Protocol) — 必须知道

**What**: Anthropic 2024 末 propose 的 open standard. 把 tool / context / data source 都标准化为 MCP servers, LLM client 通过统一 protocol invoke.

**Why it matters for Google FDE**:
- Customer 的 internal API → 包成 MCP server → 任何 LLM 都能用
- Tool discovery / versioning / permissioning 标准化
- Vendor-neutral (Claude / GPT / Gemini 都能 consume)

**Core 3 primitives**:

```
Resources   (data the LLM can read, like files, DB rows)
Tools       (functions the LLM can call, like APIs)
Prompts     (reusable prompt templates)
```

**典型架构**:

```
LLM Client (Claude Desktop / VSCode / 任何 app)
        ↓ MCP protocol (JSON-RPC over stdio / HTTP / SSE)
    ┌─────────────┬─────────────┬─────────────┐
    │ MCP Server  │ MCP Server  │ MCP Server  │
    │ (Salesforce)│ (GitHub)    │ (PostgreSQL)│
    └─────────────┴─────────────┴─────────────┘
```

每个 MCP server 是独立 process / container, 暴露 resources/tools/prompts.

**Google FDE 现实**: 大量工作是把客户的 internal stack tool-ify, 多数会用 MCP 形态.

---

## 5. High Throughput LLM Serving — 6 个 lever

| Lever | What | Speedup |
|---|---|---|
| **Continuous batching (vLLM)** | Dynamic batch size, no padding | 5-10x throughput vs static batch |
| **PagedAttention (vLLM)** | KV cache in pages, like OS paging | 24x more concurrent requests |
| **Prefix caching** | Common system prompt cached | 2-3x for repeated prefixes |
| **Speculative decoding** | Smaller draft model + bigger verifier | 2-3x latency reduction |
| **Tensor parallelism (TP)** | Model split across GPUs | More compute available |
| **Pipeline parallelism (PP)** | Stages of model on different GPUs | More throughput |

**你简历**: "GPU-accelerated inference with vLLM, SGLang" → 这是你的强 match.

---

## 6. Observability for Agent Systems — 4 个 layer

| Layer | What | Tools |
|---|---|---|
| **Distributed tracing** | 1 user request → N LLM calls / M tools — full trace | OpenTelemetry + Jaeger |
| **LLM-specific tracing** | Prompts / completions / token usage / cost per step | LangSmith, Phoenix (Arize), Helicone |
| **Cost tracking** | Per-user / per-feature dollar spent | Custom (sum tokens × price per model) |
| **Quality monitoring** | Eval-in-prod, drift detection | Braintrust, Phoenix, Langfuse |

**Critical metric to instrument**:
- Per-tool latency p50/p99
- LLM call count + token count per turn
- Tool error rate (4xx / 5xx / timeout)
- Cost per user-session
- Eval pass rate sampled in prod
- Cache hit rate (semantic + result)

---

## 7. Rate Limit / Queue / Cache — 4 个 layer

### Layer 1: Caching (cheapest)

- **Result cache** (exact query hash → response): Redis 1h TTL
- **Semantic cache** (similar query → reuse response): embedding similarity > 0.95 threshold

**Hit rate target**: 30-50% for FAQ-like workloads. Saves $$$.

### Layer 2: Queue (smooth burst)

- **Priority queue** by user tier (gold ahead of bronze)
- **Per-tenant**: max N concurrent
- **Cost-aware**: cheaper model first, escalate to expensive if needed

### Layer 3: Rate limit (defense)

- **Per-user**: token bucket 100 req/min
- **Per-API-key**: total quota (e.g., $100/day)
- **Per-tenant**: tier-based limits

### Layer 4: Cost-aware routing

```python
def route(request, complexity_score):
    if complexity_score < 0.3:
        return "gpt-4o-mini"  # 90% cases
    elif complexity_score < 0.7:
        return "gpt-4o"
    else:
        return "gpt-4-turbo"  # hard cases only
```

Cost optimization 10-50% without quality loss.

---

## 8. Eventual Consistency — Agent multi-step state

Agent 跑 5 步：
- Step 1: call create_order → DB write OK
- Step 2: call charge_payment → API timeout (unknown if charged)
- Step 3: ?

3 patterns to handle:

### Pattern A: Saga (forward + compensating)

```
Step 1 ✓ → Step 2 ✗ → Compensate Step 1 (cancel order)
```

### Pattern B: Outbox / 2PC-light

```
Each step writes intent to outbox table
Reliable worker picks up + executes + marks done
Retry until success or escalate
```

### Pattern C: Workflow engine (Temporal / DBOS)

```
Agent workflow as code, Temporal handles retries / state / recovery
```

**Google FDE 高级答**: Use Temporal for complex agentic workflows. Don't reinvent.

---

## 9. 你简历对应 hook

| Sub-topic | 你简历 hook |
|---|---|
| **Stateless vs Stateful** | Voice agent (stateful WebSocket) + BNPL chatbot (mostly stateless) — 你有两面 |
| **MCP / Proxy** | Internal Agent Platform — workflow / tool / memory 抽象 |
| **High Throughput** | vLLM / SGLang / Megatron / DeepSpeed — 你简历全列了 |
| **Observability** | Voice agent 7 markets weekly metric review |
| **Rate Limit / Queue / Cache** | TikTok scale — payment is rate-limit aware |
| **Eventual Consistency** | Refund tier — tier 3 必须 transactional |

---

## 10. Cheat Sheet

```
Stateless vs Stateful:
  Default stateless (OpenAI / Google API model)
  Stateful only for: latency-sensitive multi-turn (voice)

MCP (Model Context Protocol):
  3 primitives: Resources / Tools / Prompts
  JSON-RPC over stdio/HTTP/SSE
  Standardizes tool ecosystem across LLM providers
  Google FDE: customer API → MCP server

High throughput 6 levers:
  Continuous batching (vLLM) — 5-10x
  PagedAttention — 24x concurrency
  Prefix caching — 2-3x
  Speculative decoding — 2-3x latency
  TP — more compute
  PP — more throughput

Observability 4 layers:
  Distributed tracing (OTel)
  LLM-specific (LangSmith / Phoenix)
  Cost tracking
  Quality monitoring (eval in prod)

Rate limit / Queue / Cache:
  L1: Result cache + semantic cache (30-50% hit)
  L2: Priority queue per tenant
  L3: Token bucket (per-user / per-tenant)
  L4: Cost-aware model routing

Eventual consistency:
  Saga (forward + compensate)
  Outbox / 2PC-light
  Workflow engine (Temporal / DBOS) — recommend

Your resume hooks:
  vLLM/SGLang (T3.3)
  Internal Agent Platform (T3.2)
  Voice agent stateful WebSocket (T3.1)
  TikTok payment rate-limit (T3.5)
  Refund tier transactional (T3.6)
```
