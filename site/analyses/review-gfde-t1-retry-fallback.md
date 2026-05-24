## T1.2 · retry / timeout / fallback — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/gfde-t1-retry-fallback.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t1-retry-fallback.html`](questions/gfde-t1-retry-fallback.html)

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
