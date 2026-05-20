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

## 多场景变体 + 解法

### 变体 1: DB connection pool exhaustion

> "你的 agent 调 internal DB tool。某段时间所有 query 都 timeout。Pool 已满，新 request queue 等连接。怎么 retry？"

**关键差异**: Bottleneck 不在 downstream service 而在我们自己的资源。

**解法**:
- **不要 retry on connection-pool-full** — 你 retry 也是排队抢同一个池子
- **Backpressure**: 直接 return 429 给 caller (上层 agent 看到 'busy, try later')
- **Pool 监控**: alert pool > 80% 持续 1 min
- **根因**: pool size 太小 / slow query 拖死连接 / N+1 query bug
- **临时**: 加 pool size + tune timeout
- **长期**: query plan, slow-query log, batch where possible

### 变体 2: LLM API 返回 NaN / 空字符串 / malformed JSON

> "Tool 调 ML serving，response 200 OK 但 content 是 NaN 或者 schema 不匹配。重试吗？"

**关键差异**: 不是 HTTP error 是 **content error**。

**解法**:
- **Schema 验证 first**: 5xx 当然 retry，但 200 也得 validate output
- **Validation fail** → retry **一次** with same input (transient corruption)
- 第二次还 fail → **不是 transient**: 模型本身遇到 corner case
- **Diff 策略**:
  - Retry with different sampling params (temp + 0.2)
  - Retry with different model version (cascade fallback)
  - Truncate input / re-prompt
- **Don't infinite retry** on validation fail — wastes tokens
- **Observability**: track per-tool validation-fail rate

### 变体 3: 上游 API 返回 "service in maintenance, ETA 2h"

> "Tool API 200 OK 但 body 说 'maintenance window, retry after 2h'。Agent 怎么 fallback？"

**关键差异**: Failure 是 **structured business signal**, 不是 network error。

**解法**:
- Tool wrapper parse maintenance signal → raise `ServiceUnavailable(retry_after=7200)`
- **Don't keep retrying** in agent loop (2h > user latency budget)
- **Cache 兜底**: 如果有 stale data, mark 'as of 1h ago' return
- **告知用户**: "Service X is down for maintenance until 4pm, here's cached data" — UX 透明
- **Workflow-level**: 写 outbox, 2h 后自动 resume
- **Avoid**: silent 'sorry could not fetch'，用户不知道为啥

### 变体 4: Cascade failure — primary 挂了 fallback 也被打挂

> "Primary API down，你 fallback 到 secondary。但所有人都 fallback 过去，secondary 也被挂了。怎么防？"

**关键差异**: Fallback 不是免费的，**有 capacity 边界**。

**解法**:
- **Bulkhead pattern**: secondary 设独立 rate limit (e.g., 只接 100 QPS)
- **Backpressure**: 超过 → 给 caller 'all variants overloaded, try later'
- **Probabilistic fallback**: 50% 直接 fail, 50% 试 secondary (减少 fallback 流量)
- **Pre-arrange**: 跟 secondary vendor 预先签 burst quota，提前通知
- **Graceful degradation as final layer**: 缓存 / 简单默认值
- **Postmortem**: cascade 一旦发生，capacity plan 要重做

### 变体 5: 429 with `Retry-After: 60s` — 60s 比 user budget 还长

> "LLM vendor 突然限流, 让我们等 60s。但用户 chat 体验等 5s 都嫌长。怎么办？"

**关键差异**: 限流时间 > 用户 latency budget。

**解法**:
- **Multi-vendor failover**: GPT-4 限流 → 立即试 Claude / Gemini
- **降级到更小 model**: gpt-4 → gpt-4o-mini (10x rate limit)
- **告诉用户排队**: "high traffic, position 12 of 50" — 非 chat 场景可接受
- **预测性 throttle**: 接近 rate limit 时 (e.g., 80%) 提前拒绝 non-critical
- **Cache hit**: 限流期间 cache hit rate 拉满，semantic cache 降阈值
- **跟 vendor 谈**: 长期 quota 提升，但 short-term 还是要软兜底

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
