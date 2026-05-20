## 题目

> "Your agent calls an external API (e.g., weather, currency rates, internal billing). It returns **5xx 30% of the time at peak**, with **occasional 30s timeouts**. Design the **retry / timeout / fallback** strategy at agent level."

**Round**: Tool Calling System Design (45 min)

---

## 这道题在考什么

考你**production resilience engineering**:

1. **3 层 retry** 区分 —— transport / tool / agent
2. **Timeout 配置** —— per-call vs total budget
3. **Fallback 设计** —— alternative tool / degraded response / human
4. **Circuit breaker** —— protect downstream
5. **Cost of retry** —— LLM tokens, latency budget

---

## 必问 clarifying

**1. Failure pattern**

> "5xx 是 transient (database stuck) 还是 persistent (key revoked)? Same error code mix or varying?"

**2. Latency budget**

> "Total user-facing budget — 5s for chat, 30s for batch? Per-step latency budget for retries?"

**3. Cost of failure**

> "Failed query = user retries (cheap) or business event (escalation)? Critical path or background?"

**4. Alternative tool availability**

> "Is there fallback data source — cached / staler / less accurate? Or completely no plan B?"

**5. Idempotent?**

> "Underlying call idempotent? If yes, retry safe. If no, retry risk = double execution."

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify failure mode + budget + idempotency |
| 5-15 min | 3-layer retry (transport / tool / agent) |
| 15-25 min | Timeout strategy + circuit breaker |
| 25-35 min | Fallback ladder (alternative / degraded / human) |
| 35-45 min | Cost analysis + observability |

---

## 我会这样答（sample）

> "Clarify — *[假设: 5xx 主要是 transient overload, 30s timeout means caller gives up; budget 5s total per agent step; idempotent read API; cached fallback available]*.
>
> **3-layer retry design**:
>
> **Layer 1: Transport (HTTP client)**
> - 1 immediate retry on connection error / 408 timeout
> - Use HTTP/2 keep-alive to avoid handshake cost
> - Total transport retry budget: 500ms
>
> **Layer 2: Tool wrapper**
> ```python
> @retry(
>     attempts=3,
>     wait=wait_exponential(min=0.1, max=2, multiplier=2, jitter=True),
>     retry=retry_if_exception(transient_error)
> )
> def get_weather(lat, lng):
>     resp = http.get(f'https://api.weather.com/...', timeout=2)
>     resp.raise_for_status()
>     return resp.json()
> ```
> - Exponential backoff: 100ms / 300ms / 1s
> - Jitter ±20% prevents stampede
> - Retry only on transient (5xx, 408, 429); never on 4xx other
>
> **Layer 3: Agent runtime**
> If tool exhausted retries:
> ```python
> def call_tool(name, args):
>     try:
>         return tool_registry[name](**args)
>     except ToolUnavailableError:
>         # Try fallback ladder
>         for fallback in FALLBACK_LADDER[name]:
>             try:
>                 result = fallback(**args)
>                 result['_degraded'] = True
>                 result['_fallback'] = fallback.__name__
>                 return result
>             except Exception:
>                 continue
>         raise ToolUnrecoverableError(name)
> ```
>
> **Fallback ladder** (per tool):
> ```python
> FALLBACK_LADDER = {
>     'get_weather': [
>         get_weather_primary,      # main API
>         get_weather_cached,        # 1h-old Redis cache
>         get_weather_secondary,     # 2nd vendor (worse data)
>         get_weather_default,       # 'assume sunny' for non-critical
>     ],
>     'transfer_funds': [
>         transfer_primary,          # main bank API
>         # NO fallback for destructive — fail explicit
>     ],
> }
> ```
>
> **Timeout strategy** (per call):
> - **L1 transport**: 2s per attempt
> - **L2 tool wrapper**: 5s total (3 attempts × ~1.5s each)
> - **L3 agent**: 10s per tool incl. fallback ladder
> - **Total agent step**: 30s (across multiple tool calls)
>
> **Budget enforcement** at agent loop:
> ```python
> deadline = time.time() + 30
> for tool_call in tool_calls:
>     remaining = deadline - time.time()
>     if remaining < 2:
>         # Not enough time, skip non-critical
>         break
>     timeout = min(remaining, 10)
>     result = call_tool(tool_call.name, tool_call.args, timeout=timeout)
> ```
>
> **Circuit breaker** (per tool):
> ```python
> class CircuitBreaker:
>     # If > 50% calls fail in last 60s, open circuit for 30s
>     # During open: fail-fast, don't even try
>     # After 30s: half-open (try 1 request to test)
> ```
>
> **Fallback to human**:
> When tool exhausted + no fallback works:
> - For chat: inform user "I'm having trouble fetching X, can you provide Y manually?"
> - For background workflow: enqueue task for human review
> - Never silently succeed with bad data
>
> **Cost analysis**:
> - Each retry adds: +1 token cost (model sees error) + latency
> - At 30% error rate, expected calls = 1 / 0.7 ≈ 1.4 per logical call
> - Budget includes 40% retry overhead
>
> **Observability** (must instrument):
> - Per-tool: success rate, retry count, p99 latency, circuit-breaker state
> - Per-call: which retry attempt succeeded
> - Per-agent-step: total tool latency vs budget
> - Alert: circuit breaker open > 5 min
>
> **What NOT to do**:
> - Retry on 4xx (other than 408, 429): client error, retry won't help
> - Retry without backoff: stampede on downstream
> - Retry destructive without idempotency: double execute
> - Unlimited retry: budget burn through
> - Silent fallback: user doesn't know answer is degraded"

---

## 简历专属 reframe

| 题 | 你做过 |
|---|---|
| 3-layer retry | Voice agent ASR / TTS / LLM 都有 |
| Circuit breaker | Multi-tenant SLA monitoring 你做过 |
| Fallback ladder | Voice agent 7 markets — 某 market 挂了 fallback English voice |
| Latency budget | Streaming voice p99 < 800ms |
| Observability | Voice agent weekly metrics |

**Quote**:

> "Voice agent's streaming pipeline (ASR → LLM → TTS) had this exact shape. Each had transport + tool + agent-level retry. ASR specifically had **5 fallback levels**: primary streaming model → primary batch model → secondary vendor → text-input fallback → 'sorry I didn't catch that.' We instrumented circuit-breaker per market — Indonesia's ASR provider went down for 40 min once, circuit opened, all calls degraded to text-input gracefully, zero user-facing 5xx."

---

## 5 follow-ups

**Q1**: "Customer demands 99.99% availability on tool calls. Realistic?"
**A**: Possible only with fallback ladder. Primary API 99% × 2nd 99% × 3rd (cache) 100% locally available = combined 99.99%+. But **data quality degrades** with fallback. Trade-off needed: 99.99% available but 5% of responses use stale-cache data.

**Q2**: "Retry budget is part of total latency. How do you tune?"
**A**:
- 80% of requests succeed on attempt 1 → minimal retry cost
- 15% retry once → +100-300ms
- 5% retry 2-3x → +500ms-1s
- Tune by: alert if p99 retry rate > 20% (something systemically broken)

**Q3**: "Circuit breaker false-positive — opens when downstream is actually fine."
**A**: Heuristic tuning:
- Threshold: 50% failure rate, **minimum 20 requests in window** (not 5 / 5 = 100% but no data)
- Half-open: test 1 request, if success close
- Per-tenant breaker (gold vs bronze) — gold doesn't get blocked by bronze noise

**Q4**: "Tool API rate-limited at 100 QPS but we want 1000 QPS demand. How retry?"
**A**: Not really a retry problem — capacity problem:
- **Queue + throttle**: 100 QPS to downstream, 1000 QPS from us
- **Cache aggressively**: 90% hit reduces actual calls
- **Negotiate higher quota** with vendor
- Retry on 429 with `Retry-After` header

**Q5**: "What about WebSocket / SSE / long-running tools (e.g., code execution)?"
**A**: Different model:
- **Keepalive**: send heartbeat every 5s to detect dead connection
- **Cancellation**: on agent abort, send cancel signal to backend
- **Resumability**: store partial state, resume from checkpoint not restart
- **Timeout-of-no-progress**: not total runtime, but "no token in 30s = dead"

---

## ❌ 易错点

1. **Retry on 4xx** — client error, won't help
2. **No backoff** — stampede downstream
3. **Unlimited retry** — budget overrun
4. **No idempotency check before retry on destructive**
5. **No circuit breaker** — keep hammering broken service
6. **Silent fallback** — user thinks answer is fresh
7. **Total budget ignored** — agent step blows past user-perceived latency

---

## ✅ 加分项

1. **3-layer retry** (transport / tool / agent)
2. **Exponential backoff + jitter** explicit values
3. **Fallback ladder** with degradation labels
4. **Circuit breaker per tool with minimum-volume threshold**
5. **Latency budget** propagation through agent loop
6. **Retry-cost in token + latency** quantified
7. **Quote voice agent multi-vendor ASR fallback**
8. **Cancellation for long-running tools**

---

## Cheat Sheet

```
3-layer retry:
  L1 Transport: 1 retry, 500ms budget
  L2 Tool: 3 retries, exponential backoff 100/300/1000ms, jitter ±20%
  L3 Agent: fallback ladder (alt tool / cache / human)

What to retry:
  ✓ 5xx, 408, 429 (with Retry-After), connection error
  ✗ 4xx (except 408/429), 401, 403, validation errors

Timeout layers:
  Per-attempt: 2s
  Per-tool (incl retries): 5s
  Per-agent-step: 10s
  Per-user-request: 30s

Circuit breaker:
  50% failure threshold
  Min 20 samples in window
  Open 30s → half-open (1 test) → close
  Per-tenant

Fallback ladder example:
  primary API → cached (1h stale) → secondary vendor → safe default → human escalate

Degradation labels:
  Result includes _degraded=True, _fallback=name
  Logged + visible in trace

Observability:
  Per-tool retry rate (alert > 20%)
  Circuit-breaker state (alert open > 5min)
  Latency budget burn rate

红线:
  - Retry on 4xx
  - No backoff
  - Retry destructive without idem
  - Silent fallback
  - Unlimited retry
```
