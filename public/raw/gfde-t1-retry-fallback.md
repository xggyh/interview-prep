## 题目

> "Your agent calls an external API (e.g., weather, currency rates, internal billing). It returns **5xx 30% of the time at peak**, with **occasional 30s timeouts**. Design the **retry / timeout / fallback** strategy at agent level."

或更尖锐 framing:

> "Gemini 3 Pro is your primary LLM. At 14:00 PT it suddenly 429s for 10 minutes. Your agent has hard SLA of 5s p99 to user. **What happens between 14:00 and 14:10**, and how do you keep the agent serving?"

**出处**: Google FDE T1 (Tool Calling) 经典 production resilience 题. Anthropic / Cohere / OpenAI agent infra round 也常问 vendor failover 版本.

**Round**: Tool Calling System Design (45 min)

---

## 这道题在考什么

考你**production resilience engineering** 在 agent 场景的特殊性:

1. **3 层 retry 区分** —— transport / tool wrapper / agent runtime, 每层 budget 不同
2. **Backoff 策略** —— exponential + jitter + budget + cap, 4 个一起做才 robust
3. **Timeout 配置** —— per-call vs total budget, deadline propagation
4. **Circuit breaker** —— per-tool + per-tenant, half-open 探活
5. **Fallback ladder** —— alternative tool / cached / degraded / human, 不能 silent
6. **Multi-vendor failover** —— Gemini → Claude → GPT 的 spillover
7. **Cost of retry** —— LLM tokens, latency, 下游 capacity

特别考你**怎么不让 retry storm 反过来打挂自己 / 上下游**.

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**Retry**: 调用失败后再调一次, 期望第二次成功. 但**不是所有错误都该 retry**, 也不是越多越好.

**Backoff**: retry 之间的**等待时间策略**. 4 种主流:

- **Constant**: 每次等 1s. 简单但激进.
- **Linear**: 1s, 2s, 3s, 4s. 中庸.
- **Exponential**: 1s, 2s, 4s, 8s, 16s. 现代默认.
- **Decorrelated jitter**: AWS Builder's Library 推荐的, `sleep = random(base, sleep * 3)`, 更平滑.

**Circuit breaker (熔断器)**: 检测下游连续失败时**主动停止请求**, 给下游恢复时间. 3 态: `closed (正常) → open (停止 5min) → half-open (试探 1 个 request)`.

**Fallback**: 主路径挂时**切到备路径**. 3 种主流:
- **Alternative tool**: 同样能力的备选工具 (e.g., Gemini 挂了用 Claude)
- **Cached / staler data**: 用 1 小时前的 cache
- **Degraded response**: "I can't fetch live weather, but typically Singapore is hot and humid"
- **Human escalation**: "Let me transfer you to a human agent"

---

## 2. 这个问题的核心是什么

设想 agent 没做 retry/fallback 的灾难场景:

```
T=0    用户: "今天新加坡天气怎么样?"
T=0.1  agent: 调 weather_api(SG)
T=2.0  weather_api: 5xx 错误
T=2.0  agent: 把 5xx error 当 tool result 塞回 LLM
T=2.5  LLM: "Sorry, I encountered an error fetching weather. Please try again later."
T=2.5  用户: 😤 (这种回复太差)

或更糟:
T=0    用户问 → agent 调 transfer_funds (没 retry)
T=2.0  transfer_funds: timeout (实际已 commit 了)
T=2.0  agent: 看到 error, 再调一次 (没 idempotency)
T=2.5  bank: 又收一笔 → 双花
```

**问题来源**:

| 故障类型 | 概率 | 例子 |
|---|---|---|
| **Transient 5xx** | 0.1-1% 常态, 5-30% peak | DB temp slow, cache miss flood |
| **Network blip** | < 0.1% | LB failover, AZ network issue |
| **Timeout** | 0.5-5% | downstream slow query |
| **Rate limit (429)** | 0-2% | vendor quota hit |
| **DNS failure** | rare | infrastructure incident |
| **TLS handshake fail** | rare | cert expired, version mismatch |
| **Vendor outage** | < 0.01% | Gemini 完全 down (历史上发生过) |
| **Permanent (4xx)** | varies | 客户端 bug, 不该 retry |

**没 retry/fallback 的后果**:

- **UX**: 5% 用户每次都遇到 error, 满意度暴跌
- **Funnel**: 转化率下降 (用户放弃)
- **Downstream cascade**: 不 retry 时 caller 自己崩, 再传染上游
- **Tokens**: LLM 看到 tool error 后自己 retry, 浪费 token + 触发更深 retry storm
- **SLA**: 服务整体 availability = 各 tool availability 累乘 (4 tool 99% = 96% 总体)

**Retry/fallback 的解法 (1 句话)**:

```
3 层 retry (transport/tool/agent) + exponential backoff + jitter + budget cap
+ per-tool circuit breaker
+ fallback ladder (alt tool → cache → degraded → human)
+ multi-vendor LLM failover (Gemini → Claude → GPT)
```

---

## 3. 典型流程图 / 决策树

```
                  ┌──────────────────────────┐
                  │   Agent calls tool       │
                  └──────────────┬───────────┘
                                 ↓
                  ┌──────────────────────────┐
                  │ Tool wrapper             │
                  │  - timeout: 2s/attempt   │
                  │  - 3 retries             │
                  │  - exp backoff + jitter  │
                  └──────────────┬───────────┘
                                 ↓
              ┌──────────────────────────────────┐
              │  HTTP request                    │
              │  Result?                         │
              └──────────────────────────────────┘
                                 ↓
        ┌────────────────────────┼────────────────────────┐
        ↓                        ↓                        ↓
     2xx OK                  5xx / timeout            4xx (perm)
        ↓                        ↓                        ↓
     return                Retry decision           Return error
                                 ↓                  (no retry)
                  ┌──────────────────────────┐
                  │ Within budget?           │
                  │ - attempts < 3?          │
                  │ - elapsed < 5s?          │
                  │ - retry budget < 20%?    │
                  │ - circuit closed?        │
                  └──────────────┬───────────┘
                                 ↓
                ┌────────────────┴────────────────┐
                ↓                                 ↓
              YES                                NO
                ↓                                 ↓
            backoff + jitter                Open circuit
            retry once more                       ↓
                                          ┌──────────────┐
                                          │ Fallback     │
                                          │ ladder       │
                                          │ 1. Alt tool  │
                                          │ 2. Cached    │
                                          │ 3. Default   │
                                          │ 4. Human     │
                                          └──────────────┘
```

**3 层 retry 各自负责**:

| Layer | 谁 | 时机 | Budget |
|---|---|---|---|
| L1 Transport | HTTP client (requests/aiohttp) | conn refused / immediate fail | 500ms, 1-2 retry |
| L2 Tool wrapper | tenacity / our wrapper | 5xx, 408, 429 | 5s, 3 retries |
| L3 Agent runtime | agent loop | tool exhausted retries | fallback to alt |

---

## 4. 关键 HTTP status code 决策表

每个状态码该不该 retry, 是常考点:

| Status | Retry? | Backoff? | 说明 |
|---|---|---|---|
| 200, 201, 202, 204 | NO | — | 成功 |
| 301, 302, 303, 307, 308 | follow | — | 重定向, 不算 retry |
| 400 Bad Request | NO | — | 客户端永久错误 |
| 401 Unauthorized | NO* | — | 签名/token 问题, retry 不变, 但 alert |
| 403 Forbidden | NO | — | 权限拒绝 |
| 404 Not Found | NO | — | URL 不存在 |
| 408 Request Timeout | YES | exp | 网络层 timeout |
| 409 Conflict | NO* | — | 业务冲突, 通常不该 retry (除非 transient race) |
| 410 Gone | NO | — | 资源永久消失 |
| 422 Unprocessable | NO | — | 客户端数据格式问题 |
| 425 Too Early | YES | exp | TLS replay 防御, retry 安全 |
| 429 Too Many Requests | YES | **Retry-After header** ⭐ | 遵守 vendor 限流提示 |
| 500 Internal Server Error | YES | exp | 服务端临时 |
| 501 Not Implemented | NO | — | 功能不支持 |
| 502 Bad Gateway | YES | exp | LB / proxy 临时 |
| 503 Service Unavailable | YES | **Retry-After if present** | 服务暂时不可用 |
| 504 Gateway Timeout | YES | exp | 上游 timeout |
| Connection refused | YES | exp | 服务暂时不可用 |
| Connection reset | YES | exp | 网络层 |
| Connection timeout | YES | exp | 网络层 |
| DNS error | YES | exp | DNS / infra |
| SSL/TLS handshake error | NO* | — | 证书过期等, alert 上来人解决 |
| Body validation error (200 + bad JSON) | YES once | exp | transient corruption |

`*` 标的: 默认不 retry, 但要 alert. Retry 也不会解决根因.

---

## 5. 具体业务场景

### 场景 A: TikTok PayLater Voice Agent — Repayment Channel Failover (你最贴的工作背景)

Voice agent 在 Indonesia / Brazil / Mexico / Philippines 等 7 markets 跑, 每个 market 的 repayment channel 都不稳定. Indonesia 用 GoPay, peak 时 5xx 高达 30%.

**3 层 retry 在这里**:

```python
# L1 Transport
http_client = httpx.Client(
    timeout=2.0,
    transport=httpx.HTTPTransport(retries=1)  # 1 immediate retry on conn err
)

# L2 Tool wrapper
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.1, max=2) + wait_random(0, 0.2),
    retry=retry_if_exception_type((TransientError, Timeout))
)
def call_gopay(amount, account):
    return http_client.post('https://gopay.id/api/...', json={...})

# L3 Agent runtime - vendor failover
def collect_payment(amount, account):
    try:
        return call_gopay(amount, account)
    except (ToolExhausted, CircuitOpenError):
        # Indonesia 的 fallback ladder
        try: return call_dana(amount, account)  # alt channel
        except: pass
        try: return call_ovo(amount, account)
        except: pass
        # 最后兜底: 留 callback 让客户用别的方式还
        return create_pending_collection(amount, account, status='channel_unavailable')
```

**Real production observation**: Indonesia GoPay 14:00-15:00 local time peak rush 期间 5xx 涨到 25%. 加 L2 retry 3 次后 effective success rate 从 75% → 96%. 加 vendor failover 后到 99.5%.

### 场景 B: BNPL Chatbot — RAG retrieval + LLM call

Chatbot 调:
1. Vector DB (Milvus) for RAG
2. LLM (Gemini 3 Pro primary)
3. Stripe for refund

每层都要 retry/fallback:

```
RAG Milvus: 5xx 0.5% → 2 retry, cache fallback to last successful query
LLM Gemini: 429/5xx → 1 retry on Gemini, then Claude Sonnet 4.6, then GPT-5.4
Stripe: 5xx 1% → 5 retry (exp), idem_key required, no fallback (financial)
```

**Vendor failover 实战**: 2024 年 OpenAI 一次全球 outage 30 min, 你在 chatbot 上配了 Anthropic 兜底, 用户**完全无感**. SLA report 99.99% (没算 fallback 期间 cost +30%).

### 场景 C: Internal Agent Platform — multi-tenant SLA tiering

你做的 internal Agent Platform 给其他团队提供 workflow + tool. 不同租户 SLA tier:

```
Gold tier:    retry 5 次 + dedicated worker pool + 优先 LLM 配额
Silver tier:  retry 3 次 + shared pool
Bronze tier:  retry 1 次 + best-effort
```

Circuit breaker 也分 tier: gold 的 breaker 标准更宽松 (用 5xx 50% 才 open), bronze 更严 (20% 就 open, 防止占用资源).

### 场景 D: ConvFinQA Agent — ablation methodology

ConvFinQA 你做 multi-hop financial Q&A, ablation 实验里要测「不同 retry 策略对 accuracy 的影响」:

```
Config A: no retry → 90% accuracy (10% questions die on transient errors)
Config B: 3 retry exp → 95% accuracy
Config C: 3 retry + alt LLM fallback → 96% accuracy (1% gain from fallback)
Config D: + cache fallback (stale by 1h) → 96.5% (minor gain, but answer quality drop)
```

ablation 让我们决定**生产用 B/C 组合**, D 太 stale.

### 场景 E: Voice Agent Streaming — ASR retry vs latency trade-off

Voice agent ASR / TTS 是 streaming, 不能像 batch 那样 retry 整个 audio chunk. **Streaming 下 retry 策略不同**:

- ASR fail mid-stream: 切到 fallback ASR vendor, **resume from last partial hypothesis**
- TTS fail mid-stream: replay last audio buffer + fallback TTS
- LLM fail mid-token: emit "..." 占位, 等待 reconnect

**Retry budget 极小** — 50ms 内必须决定走 fallback, 因为 voice 延迟超 200ms 用户就觉得卡.

---

## 6. 工程上要做什么 (实施 checklist)

**作为 tool wrapper / agent runtime 实现方**:

1. **3 层 retry 分明** — Transport (HTTP client) / Tool (wrapper) / Agent (runtime)
2. **Backoff = exponential + jitter** — 不要纯 constant 或纯 linear
3. **Per-tool retry budget** — 最多占 20% 流量, 防退化成 retry-only-storm
4. **Timeout 分层** — per-attempt < per-tool < per-agent-step < per-user-request
5. **Circuit breaker per-tool** — 50% failure 触发, 30s open, 1 个 half-open test
6. **Retry-After header 尊重** — 429 / 503 给的等待时间必须等
7. **Idempotency check before retry** — destructive tool 没 idem 不该 retry
8. **Fallback ladder per-tool** — 显式 declarative 配置, 不藏在代码里
9. **Multi-vendor LLM failover** — Gemini → Claude → GPT, 同 schema 包装
10. **Degradation label** — fallback result 必须带 `_degraded=True` flag
11. **No silent fallback** — 用户 / agent 都该知道结果是 degraded
12. **Observability** — retry rate, circuit state, fallback hit rate, latency budget burn
13. **Cancellation propagation** — agent abort 时, 所有 in-flight retry / waiting cancel
14. **Cost tracking** — retry × token = real cost, alert if budget overrun
15. **Test harness** — fault injection, chaos engineering

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **Retry on 4xx** | 4xx 是客户端永久错误, retry 浪费. 例外: 408, 425, 429 |
| 2 | **没 backoff** | thundering herd, retry storm 把下游打挂 |
| 3 | **没 jitter** | 同 cohort retry 同 tick, 周期性峰值 |
| 4 | **Unlimited retry** | 永远不放弃, latency budget 爆 |
| 5 | **Retry destructive 无 idem** | 双花 / 重复扣款 |
| 6 | **没 circuit breaker** | 下游 down 时继续打, 雪崩 |
| 7 | **Circuit breaker 用 absolute count** | 5/5 = 100% 但 sample too small, 应 minimum volume |
| 8 | **Silent fallback** | 用户不知道 answer is degraded, 信任崩塌 |
| 9 | **Fallback 也 down** | cascade, 主备同挂 |
| 10 | **Retry budget 没 cap** | 长期 retry 占主流量 50%+ |
| 11 | **不 respect Retry-After** | vendor 让等 60s 你 5s 就重试, 被封更久 |
| 12 | **Deadline 不 propagation** | agent step 30s budget, 单 tool 已用 25s, 还在 retry |
| 13 | **Fallback 切到更贵 vendor 不告警** | 月底账单暴涨才发现 |

---

## 一句话总结 (Part 1)

> **Retry/Fallback strategy = "3 层 retry (transport/tool/agent) + exponential backoff + jitter + budget cap + per-tool circuit breaker + fallback ladder (alt/cache/degraded/human) + multi-vendor failover"**.
>
> 没做 retry/fallback 的 agent, 在 30% 5xx rate 下基本不可用. 做错的 (无 jitter / 无 budget / silent fallback) 比不做还危险 — 会主动制造雪崩.

---

# Part 2 · 5 个深度工程问题

## ⚙️ Problem 1: 3-Layer Retry — Transport / Tool Wrapper / Agent Runtime

为什么必须 3 层而不是 1 层 retry?

### 1.1 1 层 retry 的问题

```python
# Naive: 只在 agent 层 retry
def call_tool_with_retry(name, args, max_attempts=10):
    for i in range(max_attempts):
        try:
            return tool[name](**args)
        except Exception:
            time.sleep(2**i)
    raise ToolFailed
```

问题:
- Connection refused 这种 immediate failure 等 1s/2s/4s 太慢, 应该立即 retry
- HTTP body 解析 transient 错误, 也应该立即 retry
- Total budget 没控制, 10 次可能要等 1000s
- 不区分 retryable / permanent error

### 1.2 3 层分工

```python
# Layer 1: Transport (HTTP client level)
http_client = httpx.Client(
    timeout=httpx.Timeout(connect=1.0, read=2.0, write=2.0),
    transport=httpx.HTTPTransport(
        retries=1,  # immediate retry on conn refused / DNS / network reset
    )
)
# 总 budget: 500ms

# Layer 2: Tool wrapper (semantic level)
@retry(
    stop=stop_after_attempt(3) | stop_after_delay(5),
    wait=wait_exponential(multiplier=0.1, max=2) + wait_random(0, 0.2),
    retry=retry_if_exception_type((Transient5xx, Timeout, RateLimitExceeded)),
    reraise=True,
)
def get_weather(lat: float, lng: float) -> WeatherData:
    resp = http_client.get(f'https://api.weather.com/v1/current', params={'lat': lat, 'lng': lng})
    resp.raise_for_status()
    return WeatherData.parse_obj(resp.json())
# 总 budget: 5s

# Layer 3: Agent runtime (orchestration level)
async def execute_tool(call: ToolCall, deadline: float):
    remaining = deadline - time.time()
    if remaining < 1:
        return ToolResult(error='budget_exhausted')

    try:
        return await asyncio.wait_for(
            asyncio.to_thread(tool_registry[call.name], **call.args),
            timeout=min(remaining, 10)
        )
    except ToolExhaustedError:
        # L2 exhausted retries → L3 fallback
        return await execute_fallback(call, remaining)
# 总 budget: 30s (跨 multiple tool calls)
```

### 1.3 各层 budget 嵌套关系

```
┌────────────────────────────────────────────────────┐
│ User-facing request: 30s total                     │
│  ├─ Agent loop: planning + tool calls              │
│  │   ├─ Tool A: 10s budget                         │
│  │   │   ├─ Wrapper retry: 5s budget               │
│  │   │   │   ├─ Attempt 1: 2s timeout              │
│  │   │   │   ├─ Backoff: 100ms-300ms               │
│  │   │   │   ├─ Attempt 2: 2s timeout              │
│  │   │   │   │   └─ Transport: 500ms inner retry   │
│  │   │   │   └─ Attempt 3: 2s timeout              │
│  │   │   ├─ Fallback to alt: 3s                    │
│  │   │   └─ Cache lookup: 200ms                    │
│  │   └─ Tool B: 5s budget                          │
│  └─ LLM final generation: 5s                       │
└────────────────────────────────────────────────────┘
```

**Deadline propagation** (经典实现):

```python
class CallContext:
    deadline: float  # absolute Unix time
    parent_trace_id: str

    def remaining(self) -> float:
        return max(0, self.deadline - time.time())

    def with_timeout(self, timeout: float) -> 'CallContext':
        new_deadline = min(self.deadline, time.time() + timeout)
        return CallContext(deadline=new_deadline, parent_trace_id=self.parent_trace_id)

# 使用
ctx = CallContext(deadline=time.time() + 30, parent_trace_id=trace_id)
result = await tool_a(args, ctx=ctx.with_timeout(10))
# tool_a 内部所有 retry 看 ctx.remaining(), 超时立即 abort
```

### 1.4 Layer responsibility split

| 层 | 处理 | 不处理 |
|---|---|---|
| Transport | DNS, conn refused, TLS, socket reset | 200 但 body 错, business logic error |
| Wrapper | 5xx, 408, 429, schema validation fail | Conn refused (上层已 handle), permanent 4xx |
| Runtime | tool exhausted, switch alt, fallback ladder | 低层 transport / wrapper 已 handle |

### 1.5 Tools

- **HTTP client**: `httpx` (async), `requests` + `urllib3 Retry`, Go `net/http`
- **Wrapper retry**: `tenacity` (Python), `resilience4j` (Java), `backoff` (Python)
- **Async cancellation**: `asyncio.wait_for`, `asyncio.shield`
- **Deadline / context**: `contextvars` for propagation
- **Tracing**: OpenTelemetry spans per layer

---

## ⚙️ Problem 2: Backoff Strategies — Exponential + Jitter + Budget + Cap

Backoff 数学比看上去复杂. 4 个 component 都重要.

### 2.1 Exponential base

```python
delay_n = base * (multiplier ** n)
# base=100ms, multiplier=2
# n=0: 100ms, n=1: 200ms, n=2: 400ms, n=3: 800ms, n=4: 1.6s, n=5: 3.2s
```

**为什么 exponential 而不是 linear**:

- Linear (100/200/300/400ms): 总 budget 1s, 4 次, 短故障不够等
- Exponential (100/200/400/800ms): 总 1.5s, 4 次, 覆盖 1.5s 故障窗口
- 故障持续 5s 时, linear 4 次还在打, exponential 已经放弃

**Cap on max**: 不让 exponential 爆掉

```python
# 没 cap
delay_10 = 100 * 2**10 = 102.4s  # 太长

# 加 cap
delay_n = min(base * (multiplier ** n), max_delay)  # max=2s
# n=10 时还是 2s
```

### 2.2 Jitter

没 jitter 的灾难:

```
T=0: 10K requests 同时到, 全 timeout
T=2s: 10K requests 同时 retry (全部 wait 2s) → 下游再次被打挂
T=4s: 10K requests 同时 retry (全 wait 4s) → 又挂
... 周期性 spike, 永不平稳
```

**3 种 jitter**:

```python
# Option A: Full jitter (Marc Brooker / AWS推荐)
delay = random.uniform(0, base * 2**n)
# 完全均匀, 不会聚集

# Option B: Equal jitter
half = base * 2**n / 2
delay = half + random.uniform(0, half)
# 保留一半固定, 一半随机

# Option C: Decorrelated jitter (AWS Builder's Library)
delay = random.uniform(base, prev_delay * 3)
# 用上一次的 delay 决定下一次, 自适应

# Option D: Multiplicative jitter (常用简化版)
delay = base * 2**n * (1 + random.uniform(-0.2, 0.2))
# 总额 ±20%
```

AWS 实验 (https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) 比较: **full jitter** 在大多数场景 throughput 最优. **decorrelated jitter** 在故障恢复后收敛最快.

### 2.3 Retry budget

最容易被忽略的 component. 没 budget 的问题:

```
Normal: 100 QPS first-attempt, ~0 retry
Outage: 100 QPS first-attempt + 100 QPS retry attempt 1 + 100 retry 2 + ...
        Total: 300 QPS, retry 占 67%
After 1 min: retry 累积更高比例, downstream 看到的全是 retry
            → 主流量被 retry 挤压 → 更多 fail → 更多 retry
```

**Retry budget 实现**:

```python
class RetryBudget:
    """Token bucket-style retry quota."""

    def __init__(self, ratio=0.2, window_sec=60, min_per_second=1):
        self.ratio = ratio
        self.window_sec = window_sec
        self.min_rate = min_per_second
        self.first_attempts = SlidingWindowCounter(window_sec)
        self.retries = SlidingWindowCounter(window_sec)

    def can_retry(self) -> bool:
        first = self.first_attempts.count()
        retry = self.retries.count()
        # 至少允许 min_rate 个 retry / sec
        allowed = max(first * self.ratio, self.min_rate * self.window_sec)
        return retry < allowed

    def record(self, is_retry: bool):
        if is_retry:
            self.retries.add()
        else:
            self.first_attempts.add()

# 使用
budget = RetryBudget(ratio=0.2)
def call_with_budget(fn):
    if budget.can_retry():
        try:
            return fn()
        except TransientError:
            budget.record(is_retry=True)
            if budget.can_retry():
                return fn()  # retry
            raise
    return fn()  # no retry, return first error
```

效果: retry 流量被 cap 在 first-attempt × 20%. 长期 outage 期间 retry 不会无限增长.

### 2.4 实际 retry schedule

经典 Stripe 风格:

```
Attempt 1: T=0,     timeout=2s
Attempt 2: T=0.1±0.02s,   timeout=2s   (immediate, jittered)
Attempt 3: T=0.5±0.1s,    timeout=2s
Attempt 4: T=2±0.4s,      timeout=2s
Attempt 5: T=8±1.6s,      timeout=2s
[DLQ if 5 fails]

Total wall time: ~12s
Per-attempt timeout: 2s
Effective requests in 12s window: 5
```

### 2.5 Tools

- **Python**: `tenacity` (decorator-based), `backoff` (decorator), `urllib3 Retry`
- **Go**: `cenkalti/backoff/v4`, stdlib custom
- **Java**: `resilience4j` (Hystrix successor), `failsafe`
- **AWS SDK**: built-in adaptive retry mode
- **Envoy / Istio**: retry policy as service mesh config
- **Math**: numpy + matplotlib to plot distributions

---

## ⚙️ Problem 3: Circuit Breaker — Per-tool + Per-tenant

Circuit breaker 防止下游 down 时打死自己也打死下游.

### 3.1 状态机

```
                ┌──────────────┐
                │   CLOSED     │  ← normal, allow all requests
                │  (normal)    │
                └──────┬───────┘
                       │ failure rate > threshold + min_volume
                       ↓
                ┌──────────────┐
                │    OPEN      │  ← block all, fast-fail
                │  (blocked)   │
                └──────┬───────┘
                       │ after open_duration
                       ↓
                ┌──────────────┐
                │  HALF-OPEN   │  ← allow 1 test request
                │   (probe)    │
                └──────┬───────┘
                       │
            ┌──────────┴──────────┐
            ↓                     ↓
         success                 fail
            ↓                     ↓
         CLOSED                  OPEN
```

### 3.2 阈值设计

```python
class CircuitBreaker:
    def __init__(
        self,
        failure_rate_threshold=0.5,  # 50% failure
        min_volume=20,                # 至少 20 req 才判断
        window_sec=60,                # 1 min sliding window
        open_duration=30,             # open 30s
        half_open_max_calls=1,
    ):
        self.state = 'closed'
        self.opened_at = None
        self.failures = SlidingWindowCounter(window_sec)
        self.successes = SlidingWindowCounter(window_sec)

    def call(self, fn):
        if self.state == 'open':
            if time.time() - self.opened_at > self.open_duration:
                self.state = 'half_open'
            else:
                raise CircuitOpenError(f'Circuit open, retry after {...}')

        if self.state == 'half_open':
            # Allow 1 probe
            if not self.try_acquire_probe():
                raise CircuitOpenError('Half-open, probe in progress')

        try:
            result = fn()
            self.on_success()
            return result
        except TransientError as e:
            self.on_failure()
            raise

    def on_success(self):
        self.successes.add()
        if self.state == 'half_open':
            self.state = 'closed'
            self.opened_at = None

    def on_failure(self):
        self.failures.add()
        if self.state == 'half_open':
            self.state = 'open'
            self.opened_at = time.time()
            return

        # closed → maybe open
        total = self.failures.count() + self.successes.count()
        if total < self.min_volume:
            return  # not enough data

        rate = self.failures.count() / total
        if rate >= self.failure_rate_threshold:
            self.state = 'open'
            self.opened_at = time.time()
            metrics.incr('circuit.opened', tags={'tool': self.tool_name})
```

### 3.3 Per-tool 配置

```python
CIRCUIT_CONFIGS = {
    'weather_api': CircuitBreaker(
        failure_rate_threshold=0.5,
        min_volume=20,
        open_duration=30,
    ),
    'gopay_collect': CircuitBreaker(
        failure_rate_threshold=0.3,  # 更严, 因为是 destructive
        min_volume=10,
        open_duration=60,
    ),
    'llm_gemini': CircuitBreaker(
        failure_rate_threshold=0.4,
        min_volume=50,
        open_duration=10,  # 短, 因为有 fallback vendor
    ),
}
```

### 3.4 Per-tenant 隔离 (Bulkhead pattern)

```python
class TenantCircuitBreaker:
    """每 tenant 独立 circuit, 防止 1 个 tenant 的 noise 影响其他."""

    def __init__(self, base_config):
        self.base_config = base_config
        self.per_tenant = {}  # tenant_id → CircuitBreaker

    def for_tenant(self, tenant_id):
        if tenant_id not in self.per_tenant:
            self.per_tenant[tenant_id] = CircuitBreaker(**self.base_config)
        return self.per_tenant[tenant_id]

# 使用
def call_tool(tenant_id, tool_name, args):
    cb = circuit_breakers[tool_name].for_tenant(tenant_id)
    return cb.call(lambda: tool[tool_name](**args))
```

**Tier-aware**:

```python
def get_circuit(tenant_id, tool_name):
    tier = get_tier(tenant_id)
    base = CIRCUIT_CONFIGS[tool_name]
    if tier == 'gold':
        return CircuitBreaker(
            failure_rate_threshold=0.6,  # Gold 更宽容
            min_volume=50,
            open_duration=10,
        )
    elif tier == 'silver':
        return base
    else:  # bronze
        return CircuitBreaker(
            failure_rate_threshold=0.3,  # Bronze 更严
            min_volume=10,
            open_duration=60,
        )
```

### 3.5 False-positive 防御

```
问题: 5 个 request 4 个 fail = 80%, 触发 open. 但实际可能是 transient blip.

解法:
1. Min volume (20 req 才判断)
2. Sliding window (1 min) 而非 absolute count
3. EMA-based smoothing (新近故障权重大)
4. Multi-resource correlation (其他 tool 也在 5xx → 全局事件, breaker 别开)
```

### 3.6 Tools

- **Python**: `pybreaker`, `circuitbreaker`, `tenacity` 有简单版
- **Java**: `resilience4j` (Hystrix successor)
- **Go**: `sony/gobreaker`
- **Service mesh**: Istio Envoy `outlier_detection` 自带
- **Metrics**: Prometheus + Grafana for state visualization
- **Adaptive**: Netflix `concurrency-limits` (BBR-style auto-tune)

---

## ⚙️ Problem 4: Fallback Ladder — Alternative Tool / Cached / Degraded / Human

主路径挂了, 接下来怎么办? 不能只 "return error", 要有 graceful 降级.

### 4.1 4 层 fallback

```python
FALLBACK_LADDER = {
    'get_weather': [
        ('primary', get_weather_primary),       # 1. Main API
        ('cached', get_weather_cached),          # 2. Redis cache 1h-old
        ('secondary', get_weather_secondary),    # 3. 2nd vendor (worse data)
        ('default', get_weather_default),        # 4. 'assume sunny' for non-critical
    ],
    'transfer_funds': [
        ('primary', transfer_primary),
        # NO fallback — 钱不能用 cache 或 default
    ],
    'send_sms': [
        ('primary_twilio', send_via_twilio),
        ('secondary_messagebird', send_via_messagebird),
        ('email_fallback', send_via_email),  # 降级到 email
        # 'human' 是最后选项, 让 ops 手动联系客户
    ],
    'llm_call': [
        ('gemini_pro', call_gemini_pro),
        ('gemini_flash', call_gemini_flash),    # smaller model, faster
        ('claude_sonnet', call_claude_sonnet),  # different vendor
        ('gpt_5_5', call_gpt_5_5),
        # 不到 human, LLM 至少有
    ],
}
```

### 4.2 执行逻辑

```python
async def call_with_fallback(tool_name, args, ctx):
    ladder = FALLBACK_LADDER[tool_name]
    errors = []

    for level_name, fn in ladder:
        if ctx.remaining() < MIN_TIMEOUT:
            # 没时间了, 停
            break

        try:
            result = await fn(args, ctx=ctx.with_timeout(level_budget(level_name)))
            if level_name != 'primary':
                # Mark as degraded
                result._degraded = True
                result._fallback_level = level_name
                result._original_errors = errors
                metrics.incr('fallback.used', tags={'tool': tool_name, 'level': level_name})
            return result
        except (TransientError, CircuitOpenError, TimeoutError) as e:
            errors.append((level_name, str(e)))
            metrics.incr('fallback.failed', tags={'tool': tool_name, 'level': level_name})
            continue

    # 所有 fallback 都 fail
    return ToolError(
        tool=tool_name,
        levels_tried=[e[0] for e in errors],
        message='All fallback levels exhausted',
    )
```

### 4.3 Degradation 显式标记

```python
# Tool result 永远带 metadata
class ToolResult:
    data: Any
    _degraded: bool = False
    _fallback_level: str = 'primary'
    _stale_age_sec: int = 0
    _provenance: str = ''  # 'live API' / 'cache from 14:00' / 'static default'

# Agent / LLM 必须看 metadata 决定怎么用
def render_to_user(result):
    if result._degraded:
        prefix = ''
        if result._fallback_level == 'cached':
            prefix = f"[As of {result._stale_age_sec / 60:.0f} min ago] "
        elif result._fallback_level == 'default':
            prefix = "[Estimated, no live data] "
        return prefix + str(result.data)
    return str(result.data)
```

**这是关键 — 不能 silent fallback**:

- 用户必须知道答案 degraded
- LLM 看到 `_degraded=True` 可决定是否要 caveat
- Observability 必须 track fallback hit rate

### 4.4 Per-tool fallback design

| Tool | Fallback strategy | 原因 |
|---|---|---|
| `get_weather` | cache → secondary → default | 不准确 OK |
| `search_inventory` | cache → smaller index → empty | empty result tolerable |
| `transfer_funds` | NONE (no fallback) | 钱不能用 stale data |
| `send_email` | secondary SMTP → queue + later | latency tolerable |
| `llm_call` | smaller model → other vendor → cached previous answer | quality degradation acceptable |
| `delete_user` | NONE | destructive, fail explicit |
| `get_user_profile` | cached → minimal projection | full profile not always needed |

**Destructive 操作禁止 fallback** (Problem 4 in destructive-tools 详细讲).

### 4.5 Human escalation

```python
class HumanEscalation:
    def trigger(self, tool_name, args, errors, urgency='normal'):
        ticket = ops_system.create_ticket(
            title=f'{tool_name} fallback exhausted',
            details={
                'tool': tool_name,
                'args': redact_pii(args),
                'errors': errors,
                'urgency': urgency,
                'trace_id': current_trace_id(),
            }
        )

        if urgency == 'critical':
            pagerduty.page(on_call_engineer, ticket)

        # Tell user
        return ToolResult(
            data=None,
            _degraded=True,
            _fallback_level='human',
            _message=f'Issue escalated, ticket #{ticket.id}, an engineer will follow up',
        )
```

Voice agent 实战: 当 collection channel 全挂时, **不要让 LLM 假装能收钱**. Escalate 到人工客服:

```python
# Bad
agent: "Sorry, I'll process your payment later" (谎言)

# Good
agent: "Our payment systems are temporarily down. I've notified our team
       (ticket #1234) and a human agent will call you within 1 hour."
```

### 4.6 Tools

- **Service mesh**: Istio retry / outlier_detection / fallback routes
- **Feature flag**: LaunchDarkly / Unleash to toggle fallback paths
- **Cache**: Redis cluster, Cloudflare KV
- **Queue for human**: PagerDuty, OpsGenie, Slack alert
- **Tracing**: OpenTelemetry to show fallback path in span

---

## ⚙️ Problem 5: Multi-Vendor LLM Failover — Gemini → Claude → GPT Spillover

LLM API outage 是 agent 时代特有的 risk. Google FDE 主场用 Gemini 3 Pro, 但 vendor failover 是必备.

### 5.1 Vendor outage 现实

历史上发生过的:

- **OpenAI Nov 2023 outage**: 30 min global down, 所有 GPT-based agent 瘫痪
- **Anthropic Jan 2024 elevated errors**: 1 hour partial degradation
- **Gemini 2024 partial outages**: 偶发 EU 区不可用
- **Rate limit 突袭**: Google Cloud quota 限制突然 enforce, 限流 30 min

**Agent 不能 100% bet 单 vendor**. 但要做 vendor-agnostic 不容易.

### 5.2 Wrapping multi-vendor

```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, messages, tools=None, **kwargs) -> Response:
        pass

class GeminiProvider(LLMProvider):
    async def complete(self, messages, tools=None, **kwargs):
        # Convert to Gemini format
        gemini_msgs = to_gemini_format(messages)
        gemini_tools = to_gemini_tools(tools)
        resp = await google.generativeai.generate(
            model='gemini-3-pro',
            contents=gemini_msgs,
            tools=gemini_tools,
            **kwargs
        )
        return from_gemini_format(resp)

class ClaudeProvider(LLMProvider):
    async def complete(self, messages, tools=None, **kwargs):
        anthropic_msgs = to_anthropic_format(messages)
        anthropic_tools = to_anthropic_tools(tools)
        resp = await anthropic.messages.create(
            model='claude-opus-4-7',
            messages=anthropic_msgs,
            tools=anthropic_tools,
            **kwargs
        )
        return from_anthropic_format(resp)

class GPTProvider(LLMProvider):
    async def complete(self, messages, tools=None, **kwargs):
        # OpenAI format
        ...
```

**关键挑战**: 不同 vendor schema 差异巨大

| 维度 | Gemini | Claude | OpenAI |
|---|---|---|---|
| Tool 定义 | `function_declarations` | `tools` (Anthropic schema) | `tools` with `function` object |
| Tool call 返回 | `parts[].function_call` | `content[type=tool_use]` | `tool_calls[]` |
| Tool result 输入 | `parts[].function_response` | `content[type=tool_result]` | `role=tool` message |
| System prompt | `system_instruction` | `system` parameter | `role=system` message |
| Stop sequences | `stop_sequences` | `stop_sequences` | `stop` |
| Streaming | server-sent events | server-sent events | server-sent events |
| Pricing (2026) | $2/$12 per 1M (Pro), $0.5/$3 (Flash) | $5/$25 (Opus), $3/$15 (Sonnet) | $5/$30 (GPT-5.5), $2.5/$15 (GPT-5.4) |

**Translation layer** 是 multi-vendor 的核心工程量.

### 5.3 Failover 策略

**Strategy A: Cascade (primary → fallback only on hard fail)**

```python
async def call_llm_cascade(messages, tools):
    providers = [GeminiProvider(), ClaudeProvider(), GPTProvider()]

    for i, p in enumerate(providers):
        cb = circuit_breakers[p.name]
        if cb.is_open:
            continue
        try:
            return await p.complete(messages, tools)
        except (RateLimitError, ServerError) as e:
            cb.on_failure()
            if i == len(providers) - 1:
                raise
            continue
```

**Strategy B: Hedging (并发调多个, 取最快)**

```python
async def call_llm_hedged(messages, tools):
    # 并发 fire 2 vendor, 取第一个返回的
    tasks = [
        asyncio.create_task(GeminiProvider().complete(messages, tools)),
        asyncio.create_task(ClaudeProvider().complete(messages, tools)),
    ]
    done, pending = await asyncio.wait(
        tasks,
        return_when=asyncio.FIRST_COMPLETED,
        timeout=5
    )
    for t in pending:
        t.cancel()

    if done:
        return done.pop().result()
    raise AllVendorsTimeout
```

Hedging cost: 2x token cost. 用在 critical path 短时间内.

**Strategy C: Smart routing (按 query type 选 vendor)**

```python
def choose_vendor(query):
    if query.requires_long_context:
        return GeminiProvider()  # 2M context window
    elif query.complex_reasoning:
        return ClaudeProvider()  # Best reasoning
    elif query.cost_sensitive:
        return GeminiFlashProvider()  # cheapest
    else:
        return default_vendor
```

### 5.4 Quality consistency across vendors

```python
# 同一 prompt 不同 vendor 输出可能差很多
# 需要 normalization
class NormalizedLLMResponse:
    text: str
    tool_calls: List[ToolCall]
    usage: TokenUsage
    finish_reason: str  # normalized: 'stop' | 'length' | 'tool_call' | 'error'

# 也需要 prompt 兼容性测试
def cross_vendor_eval():
    eval_set = load_eval_set()
    for prompt in eval_set:
        gemini_resp = GeminiProvider().complete(prompt)
        claude_resp = ClaudeProvider().complete(prompt)
        gpt_resp = GPTProvider().complete(prompt)

        # Compare accuracy, latency, cost
        # If divergence high → prompt 需要 vendor-specific tuning
```

### 5.5 Cost spillover 监控

```python
# 月底账单暴涨 risk: 长期失败时, fallback 切到更贵的 vendor
class CostTracker:
    def __init__(self, budget_per_day_usd=1000):
        self.budget = budget_per_day_usd
        self.spent_today = 0
        self.per_vendor = defaultdict(float)

    def record(self, vendor, tokens_in, tokens_out):
        prices = {
            'gemini-3-pro': (2 / 1e6, 12 / 1e6),
            'gemini-3-flash': (0.5 / 1e6, 3 / 1e6),
            'claude-opus-4-7': (5 / 1e6, 25 / 1e6),
            'claude-sonnet-4-6': (3 / 1e6, 15 / 1e6),
            'gpt-5-5': (5 / 1e6, 30 / 1e6),
        }
        in_price, out_price = prices[vendor]
        cost = tokens_in * in_price + tokens_out * out_price
        self.spent_today += cost
        self.per_vendor[vendor] += cost

        if self.spent_today > self.budget:
            alert('Daily LLM cost over budget')
        if self.per_vendor[vendor] > self.budget * 0.5:
            alert(f'{vendor} dominating cost, check fallback config')
```

### 5.6 Real-world quote (Voice agent context)

你的 voice agent 2024 经历过 LLM vendor 30 min outage:

- 14:00 Gemini API 全 region 5xx
- Circuit breaker 在 14:01 open
- 14:01-14:31 所有 traffic 切到 Claude Sonnet 4.6
- Cost 涨 30% (Claude 更贵), 但 SLA 维持 99.99%
- 14:31 Gemini 恢复, 14:32 half-open probe 成功, 14:33 重新 close

**lessons learned**:
- LLM 比 traditional API outage 更长 (model serving 复杂)
- Vendor schema 差异要 translation layer 抽象
- 不同 vendor 输出 style 不同, prompt 要 vendor-aware 调
- 真正 critical 时 hedging > cascade (latency 优先)

### 5.7 Tools

- **Multi-vendor**: LiteLLM (统一 SDK), LangChain integrations, OpenRouter (API aggregator)
- **Translation**: 自己写 normalize layer (vendor schema 易变, 第三方库追不上)
- **Cost tracking**: OpenLLMetry, Langfuse, Helicone
- **Eval**: Inspect (UK AISI), Promptfoo, LangSmith
- **A/B routing**: Feature flags + routing rules

---

# Part 3 · 把 5 个问题串起来看

这 5 个 deep problem 是**resilience 工程的递进层次**:

1. **3-layer retry** 是骨架 — 每层 budget 分明
2. **Backoff strategies** 是 micro 行为 — exp + jitter + budget
3. **Circuit breaker** 是 macro 保护 — 防雪崩
4. **Fallback ladder** 是 graceful degradation — 不让用户体验崩
5. **Multi-vendor failover** 是 LLM 时代特有 — 不被单 vendor 绑死

**互相依赖**:

```
Retry 没做好 (1) → backoff (2) 也救不了 (打挂下游)
Backoff 没做好 (2) → circuit (3) 永远开着 (永久退化)
Circuit 没做好 (3) → fallback (4) 没法触发 (一直 retry primary)
Fallback 没做好 (4) → multi-vendor (5) 没意义 (vendor 切换无效)
Multi-vendor 没做好 (5) → 单 vendor outage 时全栈瘫痪
```

5 层都做到 = staff-level resilience engineering. 加上 "我自己 production 看过 X outage" 故事 = 老兵.

---

## 必问 clarifying questions

**1. Failure pattern**

> "5xx 是 transient (database stuck) 还是 persistent (key revoked, schema change)? Same error code mix or varying? 30% 是 sustained 还是 spike?"

**2. Latency budget**

> "Total user-facing budget — 5s for chat, 30s for batch? Per-step latency budget for retries? Streaming or batch?"

**3. Cost of failure**

> "Failed query = user retries (cheap UX) or business event (escalation / compliance)? Critical path or background?"

**4. Alternative tool availability**

> "Is there fallback data source — cached / staler / less accurate? Or completely no plan B? Multi-vendor LLM available?"

**5. Idempotent?**

> "Underlying call idempotent? If yes, retry safe. If no, retry risk = double execution. (See idempotency 题)"

---

## 5 步框架 (sample 45-min answer 节奏)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify failure pattern + budget + idempotency + fallback availability |
| 5-15 min | 3-layer retry (transport / tool / agent) + budget hierarchy |
| 15-25 min | Backoff (exp + jitter + budget + cap) + retry decision table |
| 25-35 min | Circuit breaker (per-tool + per-tenant) + half-open probe |
| 35-45 min | Fallback ladder + multi-vendor LLM failover |
| 45-55 min | Cost / observability / monitoring |
| 55-60 min | Q&A |

---

## 我会这样答（sample monologue）

> "Clarify — *[假设: 5xx 主要 transient overload, 30s timeout means caller gave up; user budget 5s p99; read API idempotent; cached + secondary vendor available]*.
>
> **3-layer retry**:
>
> **L1 Transport**: HTTP client (httpx) with `retries=1` on conn refused / DNS / reset. Budget 500ms.
>
> **L2 Tool wrapper**: tenacity `@retry(stop=stop_after_attempt(3) | stop_after_delay(5), wait=exp + jitter, retry_on=Transient5xx/Timeout/429)`. Budget 5s.
>
> **L3 Agent runtime**: tool exhausted → enter fallback ladder. Deadline propagation via `CallContext` with `.remaining()`.
>
> **Backoff** = exp + jitter + budget:
>
> ```
> Attempt 1: T=0, timeout=2s
> Attempt 2: T=100±20ms, timeout=2s
> Attempt 3: T=500±100ms, timeout=2s
> [stop]
> ```
>
> Jitter ±20% prevents stampede. Per-tool retry budget 20% caps long-term retry ratio.
>
> **Retry decision**:
> - 5xx, 408, 425, 429 (with Retry-After) → yes
> - Conn err, DNS err, timeout → yes
> - 4xx (except above) → no
> - SSL err → no, alert
>
> **Circuit breaker per-tool**: 50% failure rate in 60s window, min 20 req volume. Open 30s. Half-open allows 1 probe.
>
> **Per-tenant bulkhead**: gold tier more lenient (60% threshold, 50 volume), bronze stricter (30% / 10).
>
> **Fallback ladder per-tool**:
>
> ```
> get_weather: primary API → cached (1h stale) → secondary vendor → 'sunny default'
> transfer_funds: primary → NONE (no fallback for $$)
> llm_call: Gemini 3 Pro → Gemini 3 Flash → Claude Sonnet 4.6 → GPT-5.4
> ```
>
> Result always tagged `_degraded=True`, `_fallback_level='cached'`, `_stale_age=...`. Never silent.
>
> **Multi-vendor LLM**: wrap each in `LLMProvider` interface, normalize schemas. Cascade strategy on circuit-open. Hedging strategy on user-critical path. Cost tracker per-vendor with daily budget alert.
>
> **Edge cases**:
>
> - **EC1: Cascade failure** — primary down, all switch to secondary, secondary 也挂 → bulkhead (rate-limit fallback) + final 'human escalate'
> - **EC2: 429 with Retry-After: 60s** — 60s > user budget 5s → immediate vendor failover (don't wait)
> - **EC3: Retry on destructive without idem** — refuse to retry, return error to agent with `retry_unsafe=True`
> - **EC4: Deadline 用完 mid-retry** — cancel in-flight, return partial / fallback
> - **EC5: Cost spillover** — daily budget tracker, alert when fallback vendor cost > 50%
>
> **Production hardening**:
>
> - Observability: retry rate, circuit state, fallback hit rate, p99 latency per layer
> - Chaos engineering: inject 5xx 30% in staging, verify SLA
> - Per-tenant Tier with different config
> - Cost dashboard per vendor
> - Document fallback behavior to LLM via prompt ('if you see `_degraded`, caveat user')
>
> **Resume context**: I built this exact 3-layer pattern on the voice agent. Indonesia GoPay 5xx 25% at peak — L2 retry brought effective success to 96%. Added vendor failover (DANA / OVO) to reach 99.5%. ASR also had 5-level ladder: streaming primary → batch primary → secondary vendor → text-input → 'sorry didn't catch'. When Indonesia ASR went down 40 min once, circuit opened, all calls degraded to text-input, zero user-facing 5xx."

---

## 简历专属 reframe

| 题角度 | 你的项目 |
|---|---|
| 3-layer retry | Voice agent: ASR + LLM + TTS 每层都有 |
| Circuit breaker | Multi-tenant SLA monitoring 你做过 |
| Fallback ladder | Voice agent 5-level ASR fallback (streaming → batch → text input) |
| Multi-vendor LLM | BNPL chatbot: Gemini 3 Pro + Claude Opus 4.7 + GPT-5.5 |
| Latency budget | Streaming voice p99 < 800ms |
| Observability | Voice agent weekly metrics |
| Cost tracking | Internal Agent Platform 计量给租户 |
| Cancellation | Voice agent — 用户挂电话立即 cancel 所有 in-flight |

**主动 quote**:

> "Voice agent's streaming pipeline (ASR → LLM → TTS) had this exact 3-layer shape. ASR specifically had 5 fallback levels: primary streaming model → primary batch model → secondary vendor → text-input fallback → 'sorry I didn't catch that'. We instrumented circuit-breaker per market with per-tenant bulkhead — Indonesia's ASR provider went down for 40 min once, circuit opened, all calls degraded to text-input gracefully, zero user-facing 5xx. The bigger insight was **cost spillover**: when we failed over from Gemini 3 Pro to Claude Opus 4.7 during a 30-min Gemini outage, cost went up 2.5x — we now alert when fallback vendor cost > 50% of daily LLM spend."

---

## 5 follow-ups

**Q1**: "Customer demands 99.99% availability on tool calls. Realistic?"

**A**: Possible only with fallback ladder. Primary API 99% × secondary 99% × cache (locally 100% available) = combined 99.99%+. But **data quality degrades** with fallback. Trade-off:
- 99.99% available, but 5% of responses use stale-cache or default data
- Customer must accept degradation labels visible
- For destructive tools (transfer / charge), no fallback → 99.9% is the limit, customer can't have both

**Q2**: "Retry budget is part of total latency. How do you tune?"

**A**:
- 80% requests succeed on attempt 1 → minimal cost
- 15% retry once → +100-300ms median latency increase
- 5% retry 2-3x → +500ms-1s
- p99 latency = primary + max(retry_total) = 2s + 1.5s = 3.5s
- Tune by: alert if p99 retry rate > 20% (systemically broken)
- Alert if any single request retried > 3 times (probably idempotency or 4xx mishandling)

**Q3**: "Circuit breaker false-positive — opens when downstream is actually fine."

**A**: Heuristic tuning:
- Threshold: 50% failure rate, **minimum 20 requests in window** (not 5/5 = 100% but no data)
- Half-open: test 1 request, success → close immediately, fail → open another 30s
- Per-tenant breaker (gold vs bronze) — gold doesn't get blocked by bronze noise
- Cross-correlate: if other tools also 5xx → likely infra event, breaker should stay closed (whole system is having issue, not this tool)
- Manual override: SRE can force-close breaker after investigation

**Q4**: "Tool API rate-limited at 100 QPS but we want 1000 QPS demand. How retry?"

**A**: Not a retry problem — capacity problem:
- **Queue + throttle**: 100 QPS to downstream, 1000 QPS from us; queue absorbs burst
- **Cache aggressively**: 90% hit rate reduces actual calls
- **Negotiate higher quota** with vendor (Business / Enterprise tier)
- Retry on 429 with `Retry-After` header strict respect
- **Per-tenant quota** — fairshare so 1 tenant can't eat all QPS
- **Semantic deduplication** — same query within 1s → cache hit, don't double-send

**Q5**: "What about WebSocket / SSE / long-running tools (e.g., code execution, streaming LLM)?"

**A**: Different retry model:
- **Keepalive**: heartbeat every 5s to detect dead connection
- **Cancellation**: agent abort → send cancel signal, cleanup downstream resource
- **Resumability**: store partial state, resume from checkpoint not restart
- **Timeout-of-no-progress**: not total runtime, but "no token in 30s = dead, retry"
- **Idempotent partial result**: ASR streaming — partial transcript, retry doesn't lose what's already transcribed
- **Sticky session**: load balancer route retry to same backend (state cache hit)

---

## ❌ 易错点

1. **Retry on 4xx** — client error, won't help (except 408, 425, 429)
2. **No backoff** — stampede downstream, cascade failure
3. **No jitter** — periodic spikes
4. **Unlimited retry** — budget overrun, latency explosion
5. **No retry budget cap** — retry takes over majority of traffic during outage
6. **No idempotency check before retry on destructive** — double execute
7. **No circuit breaker** — keep hammering broken service
8. **Circuit breaker without min volume** — 5/5 fail → false open
9. **Silent fallback** — user thinks answer is fresh
10. **No deadline propagation** — agent step blows past user-perceived latency
11. **Single vendor LLM** — outage = total failure
12. **Cost spillover unmonitored** — month-end bill shock

---

## ✅ 加分项

1. **3-layer retry** (transport / tool / agent) explicit
2. **Exponential backoff + full jitter + budget + cap** all four
3. **Retry decision table** (5xx/408/425/429 yes, 4xx no, SSL no)
4. **Circuit breaker per-tool with minimum-volume threshold**
5. **Per-tenant bulkhead** with tier-aware config
6. **Fallback ladder** with explicit degradation labels
7. **Multi-vendor LLM failover** with translation layer
8. **Hedging strategy** for critical path
9. **Cost tracker per-vendor** with alerts
10. **Deadline propagation** via CallContext
11. **Cancellation for long-running tools**
12. **Chaos engineering** for resilience test
13. **Quote voice agent multi-vendor ASR fallback**
14. **Quote 30-min Gemini outage failover story**

---

## 一句话总结

> **Retry/Fallback = "3 层 retry (transport/tool/agent) + exp backoff + jitter + budget + circuit breaker + fallback ladder + multi-vendor failover + cost tracking"**.
>
> 越简单的系统越只做 retry, 越成熟的系统 retry 是 5 层 resilience 的最 inner layer. Agent 时代多 vendor failover 是新刚需.

---

## Cheat Sheet (印 1 页随身)

```
3-layer retry:
  L1 Transport: 1 retry, 500ms budget    (conn err)
  L2 Tool: 3 retries, exp 100/300/1000ms ±20% jitter (5xx/408/429)
  L3 Agent: fallback ladder (alt / cache / degraded / human)

What to retry:
  ✓ 5xx, 408, 425, 429 (with Retry-After)
  ✓ Connection refused / reset / DNS / timeout
  ✗ 400, 401, 403, 404, 422 (permanent client error)
  ✗ SSL error (alert, don't retry)

Backoff math:
  base * 2^n * (1 + uniform(-0.2, 0.2))
  max_cap: 2-30s depending on tool
  Full jitter alt: random(0, base*2^n)

Retry budget:
  Cap at 20% of first-attempt rate
  Window 60s sliding
  Per-tool + per-tenant

Timeout hierarchy:
  Per-attempt: 2s
  Per-tool (incl retries): 5s
  Per-agent-step: 10s
  Per-user-request: 30s

Circuit breaker:
  Threshold: 50% failure rate
  Min volume: 20 requests in window
  Open: 30s
  Half-open: 1 probe
  Per-tool + per-tenant (bulkhead)

Tier-aware:
  Gold: 60% / 50 / 10s open
  Silver: 50% / 20 / 30s open
  Bronze: 30% / 10 / 60s open

Fallback ladder:
  primary API → cached (1h stale) → secondary vendor → safe default → human escalate
  Each result tagged _degraded=True _fallback_level=X _stale_age=N

Multi-vendor LLM (2026 pricing):
  Gemini 3 Pro: $2/$12 per 1M (≤200K ctx)
  Gemini 3 Flash: $0.5/$3 (4x cheaper)
  Claude Opus 4.7: $5/$25
  Sonnet 4.6: $3/$15
  Haiku 4.5: $1/$5
  GPT-5.5: $5/$30
  GPT-5.4: $2.5/$15

Failover strategies:
  Cascade: try in order, switch on hard fail
  Hedging: parallel, take fastest (2x cost)
  Smart routing: by query type

Cost tracking:
  Per-vendor daily budget
  Alert if fallback vendor > 50% spend
  Per-tenant chargeback

Cancellation:
  CallContext with deadline
  ctx.remaining() check before each retry
  Asyncio: shield critical sections, cancel safely

Test:
  Chaos: inject 30% 5xx in staging
  Property: invariant 'never retry destructive without idem'
  Replay: real outage traces

红线:
  - Retry on 4xx (except 408/425/429)
  - No backoff (stampede)
  - Unlimited retry
  - Retry destructive without idem
  - Silent fallback
  - Single vendor LLM no failover
  - No deadline propagation
  - No cost monitoring
```

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.
> 不含 prose, 全是 compressed structure (tables / code / one-liners).

### 核心心智模型 (1 sentence)

Retry/Fallback = 「3 层 retry (transport/wrapper/agent) 分明 + exp backoff + jitter + retry budget cap (20%) + per-tool circuit breaker (min volume) + fallback ladder (alt/cache/degraded/human, 显式 _degraded label) + multi-vendor LLM failover (Gemini→Claude→GPT) + cost tracker」. 越简单系统只 retry, 越成熟系统 retry 是 5 层 resilience 最 inner layer.

### 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Retry | 失败后再调, 期望第二次成功 | 5xx/timeout/429 |
| Backoff | retry 间等待时间策略 | 防 stampede |
| Exponential | base × 2^n | 现代默认 |
| Decorrelated jitter | `random(base, prev*3)` | AWS Builders Library 推荐 |
| Full jitter | `random(0, base × 2^n)` | AWS 实验 throughput 最优 |
| Retry budget | retry 流量 cap (20% first-attempt rate) | 防 retry-only-storm |
| Circuit breaker | 熔断器 3 态 closed/open/half-open | 防雪崩 |
| Min volume | breaker 判断的最小样本数 (20) | 防 5/5 = 100% false-open |
| Half-open | open 后 allow 1 probe | 探活 |
| Bulkhead | per-tenant 资源隔离 (噪声邻居) | multi-tenant |
| Fallback ladder | primary → cached → secondary → degraded → human | graceful degradation |
| Cascade | 主挂依次切备 | 单线 failover |
| Hedging | 并发 fire 多 vendor 取最快 | critical path, 2x cost |
| Smart routing | 按 query type 选 vendor | cost 优化 |
| Deadline propagation | parent ctx 把 remaining 传给 sub | 防超 budget |
| Cancellation | abort 时取消 in-flight | 长 op |
| Retry-After | 429/503 vendor 给的等待时间 header | MUST respect |
| Translation layer | 多 vendor schema 规整成统一 interface | LLM failover |

### N 个核心 framework / pattern

**Framework 1: 3-Layer Retry**
- When: 任何外部依赖
- Algorithm: L1 transport (httpx retries=1, 500ms, conn err) → L2 wrapper (tenacity 3 retry, exp 100/300/1000ms + ±20% jitter, 5xx/408/429) → L3 agent (fallback ladder)
- Trade-off: 单层 retry 太弱; 5+ 层 over-engineer
- Tools: httpx HTTPTransport, tenacity, asyncio.wait_for, CallContext with deadline

**Framework 2: Backoff with 4 Components**
- When: 任何 retry
- Algorithm: `delay = min(base × 2^n, max_cap) × (1 + uniform(-0.2, 0.2))` + retry budget (token bucket 20% of first-attempt rate)
- Trade-off: 纯 exp 容易 stampede; 纯 jitter 没有恢复保证
- Tools: tenacity wait_exponential + wait_random, retry budget sliding window counter

**Framework 3: Per-Tool Circuit Breaker**
- When: 任何外部 tool
- Algorithm: failure rate > 50% + min 20 req volume → open 30s → half-open 1 probe → success close / fail reopen
- Trade-off: false-positive 早开 (sample too small) vs late-open (太多 5xx 才 trip)
- Tools: pybreaker, resilience4j, sony/gobreaker, Istio outlier_detection

**Framework 4: Fallback Ladder**
- When: 任何 user-facing critical tool
- Algorithm: primary → cached (1h stale) → secondary vendor → safe default → human escalate; 每 result 带 `_degraded=True _fallback_level=X _stale_age=N`
- Trade-off: degradation quality vs availability (destructive 禁止 fallback)
- Tools: feature flag (LaunchDarkly), Redis cache, PagerDuty escalation, OpenTelemetry track fallback path

**Framework 5: Multi-Vendor LLM Failover**
- When: LLM critical path
- Algorithm: translation layer normalize schemas → Cascade (try in order on hard fail) / Hedging (parallel take fastest) / Smart routing (by query type)
- Trade-off: hedging 2x cost vs cascade 慢; vendor schema 易变
- Tools: LiteLLM, OpenRouter, vendor SDKs (anthropic/google.generativeai/openai), Langfuse cost tracker

### 关键决策树 (ASCII)

```
Status code retry?
├─ 200/201/202/204 → no, success
├─ 301/302/303/307/308 → follow, not retry
├─ 400/401/403/404/422 → no, permanent client err
├─ 408 → YES (timeout)
├─ 409 → no (business conflict), unless transient race
├─ 425 → YES (TLS replay safe)
├─ 429 → YES (respect Retry-After header)
├─ 500/502/504 → YES (exp)
├─ 503 → YES (respect Retry-After if present)
├─ Conn refused/reset/DNS → YES (exp)
└─ SSL/TLS handshake err → no, alert
```

```
Fallback strategy by tool type:
├─ read tool → cache → secondary → default → human
├─ write idempotent → retry primary, no fallback to stale write
├─ destructive ($, send) → NONE (fail explicit, no fallback)
└─ llm_call → smaller model → other vendor → cached previous answer
```

```
Retry budget exceeded?
├─ Per-tool 20% of first-attempt rate → halt retry
├─ Per-tenant tier-aware (gold 30%, bronze 10%) → halt
└─ Per-request deadline propagation → cancel + fallback
```

### Part 2 五个深度问题速查

**Problem 1: 3-Layer Retry**
- 核心解法:
```python
# L1 Transport: httpx retries=1, timeout 2s, 500ms budget
# L2 Wrapper: @retry(stop=stop_after_attempt(3) | stop_after_delay(5),
#                    wait=wait_exponential(0.1, max=2) + wait_random(0, 0.2),
#                    retry=retry_if(Transient5xx|Timeout|RateLimit))
# L3 Agent: CallContext.remaining() check, fallback ladder
```
- Top 3 gotchas:
  1. 单层 retry 不区分 conn refused (立即) vs 5xx (exp wait)
  2. Total budget 没控制 → 10 retry × 1s exp = 1000s
  3. Deadline 不 propagation → agent step 30s budget, 单 tool 已用 25s 还在 retry
- Tools: httpx HTTPTransport(retries=1), tenacity, asyncio.wait_for, contextvars for deadline

**Problem 2: Backoff (exp + jitter + budget + cap)**
- 核心解法:
```python
# Stripe-style schedule:
# Attempt 1: T=0, timeout=2s
# Attempt 2: T=0.1±0.02s, timeout=2s
# Attempt 3: T=0.5±0.1s, timeout=2s
# Attempt 4: T=2±0.4s, timeout=2s
# Attempt 5: T=8±1.6s, timeout=2s
# Total wall ~12s

# Retry budget token bucket: cap at 20% first-attempt × 60s window
```
- Top 3 gotchas:
  1. 没 jitter → thundering herd (10K request 同 tick retry)
  2. 没 cap → exp 爆 (n=10 → 102s)
  3. 没 budget → retry 流量长期占 50%+ → 主流量被挤压
- Tools: tenacity wait_exponential + wait_random_exponential, AWS Builders Library decorrelated jitter, prometheus counter

**Problem 3: Circuit Breaker per-tool + per-tenant**
- 核心解法:
```python
class CircuitBreaker:
    failure_rate_threshold = 0.5  # 50%
    min_volume = 20               # 至少 20 req
    open_duration = 30            # 30s
    half_open_max_calls = 1       # probe
# Per-tenant tier:
# gold:   60% / 50 / 10s   (宽容)
# silver: 50% / 20 / 30s
# bronze: 30% / 10 / 60s   (严)
```
- Top 3 gotchas:
  1. False-positive: 5/5 fail = 100% trigger; 必加 min volume
  2. 全局 breaker 不 per-tenant → 1 tenant 噪声影响全部 (bulkhead pattern)
  3. Half-open 没限 1 probe → 同时多个 probe → 二次过载
- Tools: pybreaker / circuitbreaker (Python), resilience4j (Java), sony/gobreaker, Istio outlier_detection, Netflix concurrency-limits (BBR auto-tune)

**Problem 4: Fallback Ladder**
- 核心解法:
```python
FALLBACK_LADDER = {
    'get_weather': [primary, cached_1h, secondary_vendor, sunny_default],
    'transfer_funds': [primary],  # NONE — 钱不能 fallback
    'send_sms': [twilio, messagebird, email_fallback],
    'llm_call': [gemini_pro, gemini_flash, claude_sonnet, gpt_5_5],
}
# 每 result _degraded=True _fallback_level=X _stale_age=N _provenance=...
```
- Top 3 gotchas:
  1. Silent fallback → user 当 fresh 用 → 信任崩
  2. Destructive 也加 fallback → 钱用 stale 决策 → 灾难
  3. Cascade failure: 主备同挂 → final 'human escalate' 必备
- Tools: feature flag (LaunchDarkly/Unleash), Redis cache, Cloudflare KV, PagerDuty/OpsGenie escalation, OpenTelemetry span fallback path

**Problem 5: Multi-Vendor LLM Failover**
- 核心解法:
```
Cascade: try Gemini Pro → Claude Sonnet → GPT-5.4
Hedging: fire 2 vendor parallel, asyncio.wait FIRST_COMPLETED, cancel other (2x cost)
Smart routing: long context → Gemini 2M ctx; complex reasoning → Claude; cost sensitive → Gemini Flash
Translation layer: to_gemini_format() / to_anthropic_format() — schemas 差异大
```
- Top 3 gotchas:
  1. Vendor schema 不同 (`function_declarations` vs `tools` vs `tool_calls`) → translation layer 易变
  2. Cost spillover: failover 2.5x 月底 bill 暴涨 → daily budget alert
  3. Prompt 在不同 vendor 输出 style 不同 → vendor-specific tuning + eval
- Tools: LiteLLM (统一 SDK), OpenRouter (API aggregator), Langfuse / Helicone / OpenLLMetry (cost track), Promptfoo / Inspect (UK AISI) eval

### Production gotchas (top 15)

1. Retry on 4xx (except 408/425/429) — 永久错误浪费
2. No jitter — thundering herd 周期性 spike
3. No backoff cap — n=10 时 100s+
4. Unlimited retry — latency / cost budget 爆
5. Retry destructive without idem — 双花 (link idempotency)
6. No circuit breaker — 下游 down 时继续打 → 雪崩
7. Circuit breaker absolute count (5/5) — false-open, 必 min volume
8. Silent fallback — user 当 fresh 用 stale
9. Fallback 也 down — cascade, 主备同挂 → human escalate
10. Retry budget 没 cap — long outage retry 占 50%+
11. 不 respect Retry-After header — vendor 让等 60s 你 5s → 被封更久
12. Deadline 不 propagation — agent step 25s 用了, tool 还在 retry
13. Cost spillover — failover 切到更贵 vendor 月底 bill shock
14. Single vendor LLM — 30 min outage = 全栈瘫痪
15. Streaming retry 整 audio chunk — 该 resume from partial, 不该 restart

### 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| 3-layer retry | Voice agent ASR + LLM + TTS pipeline | "Each stream 5-level fallback: primary streaming → batch primary → secondary vendor → text-input → 'sorry didn't catch'" |
| Backoff exp+jitter | Indonesia GoPay 14:00 peak 5xx 25% | "L2 retry 3 次后 effective success 75% → 96%; full jitter ±20%" |
| Circuit breaker | Multi-tenant SLA monitoring | "Per-tool + per-tenant tier-aware (gold 60% / bronze 30%); min volume 20 防 false-open" |
| Fallback ladder | BNPL RAG / LLM critical path | "Layer 2 cached 必须标 `_stale_warning`, LLM 自信 hallucinate fresh 是最大坑" |
| Multi-vendor LLM | BNPL chatbot Gemini → Claude | "30 min Gemini outage, circuit open, 全切 Claude Sonnet 4.6, cost +2.5x, SLA 99.99% 维持" |
| Cancellation | Voice agent 用户挂电话 | "Asyncio CancelledError propagation, cleanup downstream resource, ctx.cancel_event" |
| Cost tracker | Internal Agent Platform | "Per-vendor daily budget, alert if fallback vendor > 50% spend" |
| Chaos test | Staging environment | "Inject 5xx 30% 验证 SLA, retry rate 与 expected 一致" |

### 面试现场 quotables (top 8)

> "Retry 不是单层. Transport 处理 conn refused (500ms 立即), wrapper 处理 5xx/timeout (5s exp+jitter), agent 处理 dependency outage (alt vendor/cache/human). 3 层 budget 嵌套."

> "Backoff 4 component 缺一不可: exp + jitter + budget + cap. 单纯 exp 容易 stampede; 加 jitter ±20% + cap 2s 才平稳."

> "Circuit breaker 必须有 min volume. 5 个 request 全 fail = 100% rate, 但 sample too small. 至少 20 req 才判断."

> "Fallback 不能 silent. Result 必须带 `_degraded=True _fallback_level _stale_age`. LLM 看到 metadata 知道 caveat 给 user."

> "Destructive tool 禁止 fallback. 钱不能用 stale data. Transfer fail → 显式 error, 不要默认 'try cached balance'."

> "Multi-vendor LLM 不是 nice-to-have. 2024 年 OpenAI 30 min global outage, 我们 voice agent 全切 Claude, 用户完全无感. Cost 涨 30% 但 SLA 99.99%."

> "Cost spillover 是隐形大坑. Gemini 挂时切 Claude Opus, cost 2.5x. Alert if fallback vendor > 50% daily spend, 否则月底 bill shock."

> "Streaming retry 不能整 audio chunk restart. Resume from last partial hypothesis, 否则用户感知 latency 翻倍."

### 红线 (top 10 anti-patterns)

1. Retry on 4xx (except 408/425/429)
2. No backoff (thundering herd)
3. No jitter (周期性 spike)
4. Unlimited retry (budget 爆)
5. Retry destructive 无 idem (双花)
6. No circuit breaker (雪崩)
7. Circuit breaker 无 min volume (false-open)
8. Silent fallback (信任崩)
9. Single vendor LLM 无 failover
10. No cost monitoring on fallback path (月底 bill shock)
