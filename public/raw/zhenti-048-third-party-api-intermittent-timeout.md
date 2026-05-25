## Q48 · Third-party API intermittent timeouts — diagnose and respond

> "Your production system depends on a third-party API (LLM provider, payment processor, ASR service). **You're seeing intermittent timeouts — some requests succeed, some hit 30-second timeout.** Walk me through your diagnosis methodology and response. Not just 'check status page' — show me you've actually owned this before."

**中文翻译**:

> "你的 production 系统依赖一个第三方 API (LLM 服务商, 支付处理商, 或 ASR 语音识别服务). **你看到间歇性的 timeouts — 有的 request 成功, 有的卡 30 秒超时.** 跟我讲讲你怎么诊断, 怎么响应. 别给我 '看 status page' 这种敷衍答案 — 让我看你是真的在 production 里 own 过这种事."

**Round**: Production / Reliability (45 min)
**出处**: Exponent 2026 FDE Guide · 公司: OpenAI / Anthropic / Cohere / Scale AI — production reality 必问

---

## 📖 术语速查 (本题用到的)

> Reliability / on-call 题. 网络 / 分布式系统 / 监控术语堆.

### 故障类型 ⭐

| 术语 | 解释 |
|---|---|
| **Intermittent / 间歇性** ⭐ | **有时成功有时失败** — 跟 constant failure 截然不同的 debug. 难抓因为 reproduce 难, 但 patterns 通常存在 (peak hours / specific region). |
| **Timeout** | Request 超时. Hard timeout (30s 砍掉) vs slow (5s 慢但成). |
| **Cascading failure** ⭐ | **一个组件挂连带打挂下游** — retry storm 是经典 cascade trigger. |
| **Retry storm / Retry amplification** ⭐ | **Vendor 慢 30% 时, 我们 5x retry → vendor 收 5x 流量 → 更慢 → 更多 retry**. 死循环. |
| **Thundering herd** | 大量 client 同时 retry 撞 vendor. 用 jitter 防. |
| **Partial outage** | 部分功能挂, 其他正常. 比全挂难诊断. |
| **Regional outage** | 只影响一个 region (e.g. AWS us-east-1). |
| **Silent failure** | 没 error 但结果不对. 最可怕, 监控难捕. |

### 监控 / Observability ⭐

| 术语 | 解释 |
|---|---|
| **OpenTelemetry (OTEL)** ⭐ | **开源 observability 标准** — trace / metric / log 统一. 2026 业界默认. |
| **Distributed tracing** ⭐ | **跨服务 request trace** — 看哪步慢 / 挂. 每 request 一个 trace ID 串起来. |
| **Trace** | 一个 request 完整路径. |
| **Span** | Trace 中的一段 — 一次 function / API call. |
| **Correlation ID** | 跨服务关联 log 的 ID. 同 trace ID. |
| **Prometheus** | 开源 metric 系统. Pull 模式从 service 抓 metric. |
| **Grafana** | Metric 可视化. 跟 Prometheus / Datadog 搭. |
| **Datadog** | 商业 APM + monitoring + log. SaaS. |
| **APM (Application Performance Monitoring)** | New Relic / Datadog APM / Dynatrace 类工具. |
| **LangSmith / Phoenix** | LLM-specific tracing. |
| **Status page** | Vendor 公开的 incident 通知页 — status.openai.com 类型. |
| **Webhook** | Vendor push 通知到你 — incident 时收 alert. |

### 可靠性 Patterns ⭐

| 术语 | 解释 |
|---|---|
| **Circuit breaker** ⭐ | **连续失败到 threshold 后停止调用 N 秒**, 给 downstream 喘息. Hystrix 实现. |
| **Retry with exponential backoff** | Retry 间隔指数增长 (1s, 2s, 4s, 8s). |
| **Jitter** ⭐ | **Backoff 加随机抖动** — 避免 thundering herd. ±20% randomness. |
| **Timeout** | 请求超过 X 秒放弃. p99 × 2 常见. |
| **Bulkhead / 隔离舱** | 隔离 user / tenant 资源池. |
| **Hedged request** | 同 request 发 2 个 backend, 用先回的. |
| **Rate limiting / Throttling** | 限 QPS / Server 拒收过载. |
| **DLQ (Dead Letter Queue)** ⭐ | **失败 N 次的 message 进 DLQ**, 人工处理. |
| **Idempotency key** | Retry 安全必备. |
| **Graceful degradation / Cached fallback** | 降级 mode 仍工作 / 返回缓存. |
| **Multi-vendor fallback** | Primary 挂时 auto-switch secondary. |

### Headers / HTTP

| 术语 | 解释 |
|---|---|
| **x-ratelimit-remaining** | Vendor header 告知剩余 quota. |
| **request_id** | Vendor 给每 request 的 ID. Escalate 时必带. |
| **429 / 503 / 5xx** | Too many requests / Service unavailable / Server error 总称. |
| **Payload size** | Request body 大小. 大 payload 易超时. |

### 事故响应 ⭐

| 术语 | 解释 |
|---|---|
| **Incident** | 影响 user 的故障. |
| **P0 / P1 / P2** | Severity. P0 = 立刻 page; P1 = 1h; P2 = 4h. |
| **On-call** | 轮值待命. PagerDuty / Opsgenie alert routing. |
| **Page** | 告警手段 — 打电话叫醒. |
| **MTTA / MTTD / MTTR** ⭐ | **Acknowledge / Detect / Resolve 时间**. Reliability 核心指标. |
| **Blast radius** | 故障影响范围 (用户 / region / tenant 数). |
| **Runbook** ⭐ | **"If X 告警, 跑 Y 步骤"**. 应急手册. On-call 安全网. |
| **Postmortem** | 事后复盘文档. Blameless 文化. |
| **5 whys / RCA** | Root cause analysis — 连续问 5 次 why. |
| **Action item** | Postmortem 后改进项 — 有 owner + ETA. |

### SLO / Error Budget

| 术语 | 解释 |
|---|---|
| **SLO (Service Level Objective)** ⭐ | **可靠性目标** — e.g. 99.9% availability. Internal commit. |
| **SLA (Service Level Agreement)** | 跟客户的合同 — breach 罚款. |
| **Error budget** ⭐ | 100% - SLO. Burn 太快 = freeze feature ship. |
| **Golden signals** | Latency / Traffic / Errors / Saturation — Google SRE 经典. |
| **Saturation / Queue depth** | 接近上限的预警信号. |

---

## 这道题在考什么

表面是 debug 题, 底下藏着 **8 个 FDE evaluation signal**:

1. **Real on-call experience** — 不是 "我看 metrics", 是 specific tools + workflow
2. **Diagnosis discipline** — 系统化排除, 不是猜
3. **Intermittent vs constant** — 区分 pattern, 不能 grep 一条 log
4. **Both sides** — 知道是我们的问题 OR vendor 的问题
5. **Mitigation before root cause** — stop bleeding first
6. **Customer comm** — keeping stakeholders informed during incident
7. **Postmortem mindset** — every incident becomes improvement
8. **STAR storytelling** — voice agent Pakistan ASR 40-min outage 是 perfect story

不考「怎么 debug API」, 考「你 owned a 40-min outage in production, walk me through it」.

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|---|---|---|
| 1 | **Clarify 'intermittent'** | 3 min | Frequency, pattern, time-of-day, scope | "First — what's 'intermittent'? 1 in 10? 1 in 1000? Specific endpoints? Time of day pattern?" |
| 2 | **6-step diagnosis methodology** | 5 min | Our side / their side / scope / mitigate / escalate / postmortem | "I follow 6 steps — our side first, their side, scope, mitigate, escalate, postmortem." |
| 3 | **Step 1: Our side first** | 5 min | Retries amplifying, rate limit, network, payload size | "Our side first — 4 things to check: are we amplifying via retry, hitting rate limit, network DNS, payload size growth?" |
| 4 | **Step 2: Their side** | 5 min | Status page, headers, support, regional | "Their side — status page, response headers (request_id), region-specific, error pattern" |
| 5 | **Step 3: Isolate scope** | 4 min | Single tenant / endpoint / region / customer-specific | "Scope: single tenant? single endpoint? single region? single customer ID range?" |
| 6 | **Step 4: Mitigate** | 5 min | Circuit breaker, retry with jitter, cached fallback, queue | "Mitigate before root cause — circuit breaker, exponential backoff with jitter, cached fallback, async queue, traffic shaping." |
| 7 | **Step 5: Escalate to vendor** | 4 min | Specific data, business impact, contract level | "Escalate with: request_id, error pattern, time range, our trace data, business impact $$" |
| 8 | **Step 6: Postmortem + prevention** | 3 min | Multi-vendor, eval, runbook, MTTR | "Postmortem: action items — multi-vendor fallback, better detection, runbook update, SLO tightening" |
| 9 | **Quote Pakistan ASR 40-min outage** | 5 min | STAR with real numbers | "Voice agent Pakistan ASR — 40-min outage. Detected in 3 min via drift. MTTR 8 min via failover. Postmortem actions implemented." |
| 10 | **Cost of unreliability** | 1 min | Business case for resilience investment | "Every minute of outage = $X revenue + $Y churn risk. Resilience is not optional at scale." |

---

## 详细回答

### Step 1: Clarify "intermittent"

```
First questions to ask before debugging:

1. Rate / frequency
   - 1 in 10? 1 in 100? 1 in 1000?
   - Is it growing or stable?
   - Time-of-day pattern? (peak hours? specific hours?)

2. Pattern
   - All endpoints or specific?
   - All users or subset?
   - All payloads or specific shape (large inputs)?
   - All regions or one?

3. When started
   - Today only? Past 24 hours? Slow creep over week?
   - Coincides with our deploy?
   - Coincides with their deploy (status page)?

4. Severity
   - Hard timeout (30s) or slow (5s+)?
   - Full failure or partial response?
   - User-facing? Internal-only?
```

### Step 2: 6-Step Diagnosis Methodology

```
Step 1: Check OUR side (we cause this more often than we admit)
Step 2: Check THEIR side (vendor status + signals)
Step 3: Isolate SCOPE (what's failing, what's working)
Step 4: MITIGATE (stop bleeding before root cause)
Step 5: ESCALATE to vendor with data
Step 6: POSTMORTEM + prevention
```

### Step 3: Step 1 — Our side first

**Why "our side first"**: vendor blame is satisfying but often wrong. Most "vendor problems" are partly or fully our caused.

```python
# 4 common our-side causes

# Cause 1: Retry amplification
# Our retry policy makes things worse during partial outage
async def buggy_call_with_retries(api_call, max_retries=5):
    for attempt in range(max_retries):
        try:
            return await asyncio.wait_for(api_call(), timeout=30)
        except (TimeoutError, ConnectionError):
            await asyncio.sleep(0.5 * 2 ** attempt)  # exp backoff but no jitter
    
# Problem: When vendor has minor slowdown, our 5x retries amplify
# Their throughput drops 30% → our request volume hits 5x normal → cascading failure

# Diagnosis: graph "actual requests sent" vs "user requests"
# If ratio is climbing during outage, retry is amplifying

# Fix: 
# - Lower max_retries to 2-3
# - Add jitter to backoff
# - Use circuit breaker (stop retrying when failing too much)

# Cause 2: Rate limit
# We're hitting API quota
async def check_rate_limit():
    response = await api.call()
    if response.headers.get('x-ratelimit-remaining', '1000') < '100':
        # We're close to limit, slow down
        await throttle()

# Check vendor's headers:
# - x-ratelimit-remaining
# - x-ratelimit-reset
# - x-quota-used
# - retry-after

# Cause 3: Network / DNS
# Our infra problem masquerading as vendor's
# Tools: dig +short, mtr, traceroute, tcpdump

# Cause 4: Payload size growth
# We're sending bigger requests than vendor expects
# E.g., context grew from 4k to 50k tokens, vendor times out on tokenization
# Check our logs: payload size distribution over time
```

**Specific diagnosis commands**:

```bash
# DNS check
dig +short api.openai.com
nslookup api.openai.com

# Network path
mtr api.openai.com  # interactive trace
traceroute api.openai.com  # one-shot

# TLS handshake time
curl -w "@curl-format.txt" -o /dev/null -s https://api.openai.com/v1/models

# curl-format.txt content:
# time_namelookup:  %{time_namelookup}\n
# time_connect:     %{time_connect}\n
# time_appconnect:  %{time_appconnect}\n  
# time_pretransfer: %{time_pretransfer}\n
# time_redirect:    %{time_redirect}\n
# time_starttransfer: %{time_starttransfer}\n
# time_total:       %{time_total}\n

# Concurrent connections (are we connection-pooled out?)
netstat -an | grep api.openai.com | wc -l

# Active sessions
ss -tn | grep :443

# Inspect our retry pattern
grep "retry attempt" logs/*.log | head -100
grep "timeout" logs/*.log | wc -l
```

### Step 4: Step 2 — Their side

```
Vendor status sources (in priority):

1. Official status page
   - status.openai.com
   - status.anthropic.com
   - status.cohere.com
   - statuspage subscription for push notifications

2. Response headers
   - x-request-id (give to vendor for debugging)
   - retry-after (vendor telling us to slow down)
   - server (CDN / origin info)
   - x-ratelimit-* (quota info)

3. Vendor community
   - OpenAI community / Discord
   - Anthropic Discord
   - Reddit r/OpenAI, r/Anthropic — sometimes faster than status page

4. Cross-check with other monitoring services
   - Down Detector (downdetector.com)
   - Pingdom / StatusGator

5. Direct support
   - Enterprise: dedicated Slack channel / TAM
   - Pro: support ticket + community
   - Free: community only
```

**Patterns to look for**:

```
Vendor-side outage signals:
  - Status page incident
  - error_type changed (was 400 / 429, now 500 / 503)
  - response_time spike at vendor (Server-Timing header sometimes shows)
  - geographic pattern (only US-East affected?)
  - endpoint pattern (only /chat/completions, not /embeddings?)

Our-side signals:
  - Volume spiking from us before failures
  - Specific endpoints (we changed something)
  - One client / one instance failing (config drift?)
```

### Step 5: Step 3 — Isolate scope

```python
# Slice the failure pattern

# By time
errors_by_time = errors.groupby(hour).count()
# Reveals: time-of-day pattern, deploy correlation, gradual vs sudden

# By endpoint
errors_by_endpoint = errors.groupby('endpoint').count()
# Reveals: is one endpoint affected? all?

# By tenant / customer
errors_by_tenant = errors.groupby('tenant_id').count()
# Reveals: single customer affected? all?

# By region
errors_by_region = errors.groupby('aws_region').count()
# Reveals: regional issue? our side or theirs?

# By request size
errors_by_payload_size = errors.groupby(payload_size_bucket).count()
# Reveals: only big payloads failing? token limit?

# By instance
errors_by_pod = errors.groupby('pod_id').count()
# Reveals: one pod misbehaving? rotate it.

# By upstream model
errors_by_model = errors.groupby('model_name').count()
# Reveals: gpt-5 only? sonnet-4-6 only? config drift?
```

**Scoping helps you decide**:

```
If single endpoint:    likely vendor's deploy + specific change
If single region:      vendor region issue OR our region routing
If single customer:    customer-specific data shape issue
If single pod:         our infra problem, rotate
If big payloads only:  context length / tokenization issue
If across all:        vendor wide outage OR our network OR amplification
```

### Step 6: Step 4 — Mitigate (stop bleeding first)

**Critical principle**: Don't wait for root cause. Stop user impact NOW.

```python
# Pattern 1: Circuit breaker
class CircuitBreaker:
    def __init__(self, failure_threshold=10, recovery_timeout=60, half_open_after=30):
        self.failures = 0
        self.state = 'closed'
        self.last_failure_time = None
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_after = half_open_after
    
    async def call(self, fn, *args, **kwargs):
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.half_open_after:
                self.state = 'half-open'  # try one request to test
            else:
                # Fall back without calling vendor
                return await self.fallback(*args, **kwargs)
        
        try:
            result = await fn(*args, **kwargs)
            if self.state == 'half-open':
                self.state = 'closed'  # recovered
            self.failures = 0
            return result
        except (TimeoutError, ConnectionError) as e:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.failures >= self.failure_threshold:
                self.state = 'open'
                # Now all subsequent calls fast-fail to fallback
            raise

# Pattern 2: Exponential backoff with jitter
async def call_with_jitter(fn, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await fn()
        except RetryableError:
            if attempt == max_retries - 1:
                raise
            base_delay = 0.5 * 2 ** attempt  # 0.5, 1, 2 seconds
            jitter = random.uniform(0, base_delay)  # avoid thundering herd
            await asyncio.sleep(base_delay + jitter)

# Pattern 3: Cached fallback
async def call_with_cache_fallback(query):
    try:
        return await api_call_with_circuit_breaker(query)
    except (TimeoutError, CircuitOpenError):
        cached = await cache.get(query.cache_key)
        if cached:
            return cached  # serve stale but not broken
        raise

# Pattern 4: Async queue (degrade to async)
async def call_with_async_fallback(query):
    if circuit_breaker.is_open():
        # Queue for later processing instead of failing
        await queue.enqueue(query, ttl=3600)
        return PendingResponse(message="Your request is queued, we'll notify within 1 hour")
    return await api_call(query)

# Pattern 5: Traffic shaping
async def call_with_load_shedding(query, priority='normal'):
    if circuit_breaker.is_half_open():
        if priority == 'low':
            # Shed low-priority traffic during recovery
            return await fallback(query)
    return await api_call(query)

# Pattern 6: Multi-vendor failover
async def multi_vendor_call(query):
    vendors = [openai_client, anthropic_client, gemini_client]
    
    for vendor in vendors:
        if vendor.circuit_breaker.is_open():
            continue
        try:
            return await vendor.call(query)
        except Exception:
            continue
    
    # All vendors down → cached or queue
    return await cached_fallback(query)
```

**Mitigation playbook by failure pattern**:

| Pattern | Mitigation | Trade-off |
|---|---|---|
| Vendor slow (high latency) | Reduce concurrency, queue | Throughput drops |
| Vendor 500s (errors) | Circuit break + fallback | Some users get cached / queued |
| Vendor rate limited | Throttle to limit + retry-after | Slower throughput |
| Vendor specific region down | Failover to other region | Latency increase |
| Network DNS issue | Hard-code IPs temporarily | Brittle but immediate |
| Our retry amplification | Lower retries, add jitter | Some legit retries fail |

### Step 7: Step 5 — Escalate to vendor with data

**Bad escalation**: "Your API is broken. Fix it."

**Good escalation** (gets fast response):

```
Email / ticket / Slack to vendor support:

Subject: [P1] API timeout regression — 8% error rate spike past 30 min

Hi [vendor support],

We're seeing intermittent 30-second timeouts on /chat/completions 
since 14:32 UTC.

Specifics:
- Error rate: 8% (baseline 0.1%)
- Affected endpoint: /v1/chat/completions  
- Affected model: gpt-5.5
- Our region: us-east-1 (calling api.openai.com)
- Our request volume: 5000 QPS sustained
- Sample request_ids (last 10 minutes):
  - req_abc123 (timestamp 14:35:22)
  - req_def456 (timestamp 14:37:11)
  - req_ghi789 (timestamp 14:42:05)
  ...

Patterns we've observed:
- Specific to long-context requests (>50k tokens input)
- Smaller requests succeed fine
- All other endpoints (embeddings, moderation) work normally
- No correlation with our deploy (last deploy 6 hours ago, no issues until 14:32)

Business impact:
- Customer-facing chatbot serving 100k users
- $20k/hour revenue impact
- Currently mitigating via circuit breaker + cached fallback

Could you confirm if there's a known issue with long-context 
on gpt-5.5 in us-east-1? Any timing for resolution?

Thanks,
Gao Xin / TikTok Global Payment
Enterprise support customer #XXXX
```

**Why this gets fast response**:
- Specific request_ids (vendor can trace immediately)
- Business impact quantified
- Mitigation in progress (you're a competent customer, not panicking)
- Specific question (not "fix it")

**Escalation channels by tier**:

```
Enterprise (Anthropic / OpenAI Enterprise):
  - Dedicated Slack channel with TAM (15-min response SLA)
  - Direct phone for P0
  - Engineering escalation path

Pro / Plus:
  - Support ticket (4h response SLA typical)
  - Community Discord/forum

Free:
  - Community only
  - Status page subscription
```

### Step 8: Step 6 — Postmortem + prevention

**Every incident becomes improvement**:

```
Postmortem template:

1. Timeline (every relevant event)
   14:32 - First 30s timeout observed
   14:35 - Drift dashboard alert (3 min detection)
   14:36 - On-call paged
   14:38 - Initial triage, scope assessment
   14:40 - Mitigation deployed (circuit breaker activated)
   14:45 - Customer comms (status page + Slack)
   14:50 - Vendor escalated with data
   15:12 - Vendor responded: "investigating long-context endpoint"
   15:25 - Vendor mitigation deployed
   15:30 - Normal service restored

2. Impact
   - Duration: 58 min (14:32 - 15:30)
   - Users affected: ~30% of long-context queries
   - Revenue impact: ~$15k
   - SLA breach: Yes (SLA 99.5%, this month 99.2% so far)

3. Root cause
   - Vendor side: bug in gpt-5.5 long-context handling for us-east-1
   - Our side: no multi-region failover, no cached fallback for this endpoint

4. What went well
   - Drift detection caught in 3 min
   - Circuit breaker prevented retry amplification
   - Vendor escalation with specific data → 22-min vendor response

5. What didn't go well
   - No automatic failover to multi-region
   - Cached fallback didn't cover long-context queries
   - Status page update was manual (12-min lag)

6. Action items
   - [HIGH] Add multi-region failover (us-east-1 → us-west-2)
   - [HIGH] Cached fallback for long-context queries (acceptable degradation)
   - [MED] Automate status page updates on circuit breaker trigger
   - [MED] Lower drift detection threshold from 5% to 3% (catch earlier)
   - [LOW] Update runbook with this incident pattern
   
7. Owner + due dates
   - [HIGH items]: Eng lead, 1 week
   - [MED]: Platform team, 2 weeks
   - [LOW]: Runbook owner, immediate
```

---

## 关键决策 / 框架

### 5-phase incident response

```
Phase 1 — DETECT (target < 5 min)
  - Real-time monitoring (latency p99, error rate, drift)
  - Alerting (PagerDuty, custom)
  - Customer reports as backup signal

Phase 2 — TRIAGE (5 min)
  - Severity (P0 / P1 / P2)
  - Scope (all? subset?)
  - Blast radius
  - Acknowledge to team

Phase 3 — MITIGATE (15 min target)
  - Stop bleeding first (circuit breaker, failover, cache fallback)
  - Don't wait for root cause
  - Reversible changes preferred

Phase 4 — INVESTIGATE (1 hour)
  - Our side vs theirs
  - Pattern analysis
  - Specific root cause

Phase 5 — COMM (within 1h for P0)
  - Internal Slack
  - Customer (if impact)
  - Status page
  - Regulatory (if applicable)

Phase 6 — POSTMORTEM (within 1 week)
  - Timeline
  - What went well / poorly
  - Action items
  - Runbook update
```

### Diagnosis priority (cheap-first)

```
Priority 1: Status page (30 seconds)
Priority 2: Response headers (1 minute)
Priority 3: Our logs (5 minutes)
  - Volume spike before failures?
  - Retry amplification?
  - Specific endpoint / payload pattern?
Priority 4: Network diagnostics (10 minutes)
  - DNS, traceroute, latency
Priority 5: Vendor support (asynchronous)
```

---

## 完整代码 / 架构图

### Resilient API wrapper

```python
# resilient_api.py

import asyncio
import random
import time
from typing import Optional
from dataclasses import dataclass

@dataclass
class APICallResult:
    success: bool
    response: Optional[dict] = None
    error: Optional[str] = None
    latency_ms: int = 0
    used_fallback: bool = False
    vendor_used: Optional[str] = None

class ResilientAPIClient:
    def __init__(self, config):
        self.config = config
        self.circuit_breakers = {
            vendor: CircuitBreaker() for vendor in config.vendors
        }
        self.cache = ResponseCache(ttl=3600)
        self.rate_limiters = {
            vendor: RateLimiter(qps=config.rate_limits[vendor])
            for vendor in config.vendors
        }
    
    async def call(self, query, vendor_preferences=None) -> APICallResult:
        start = time.time()
        
        # Try vendors in preference order
        vendors = vendor_preferences or self.config.vendor_priority
        
        last_error = None
        for vendor in vendors:
            cb = self.circuit_breakers[vendor]
            rl = self.rate_limiters[vendor]
            
            # Skip if circuit open
            if cb.is_open():
                continue
            
            # Wait for rate limit
            await rl.acquire()
            
            # Try with retries (vendor-specific)
            for attempt in range(self.config.max_retries):
                try:
                    response = await asyncio.wait_for(
                        self._call_vendor(vendor, query),
                        timeout=self.config.timeout_ms / 1000
                    )
                    cb.record_success()
                    
                    latency = (time.time() - start) * 1000
                    
                    # Cache for future fallback
                    await self.cache.set(query.cache_key, response, ttl=3600)
                    
                    return APICallResult(
                        success=True,
                        response=response,
                        latency_ms=int(latency),
                        vendor_used=vendor
                    )
                
                except asyncio.TimeoutError as e:
                    cb.record_failure()
                    last_error = f'timeout_{vendor}_attempt_{attempt}'
                    
                    # Exponential backoff with jitter
                    if attempt < self.config.max_retries - 1:
                        base = 0.5 * 2 ** attempt
                        jitter = random.uniform(0, base)
                        await asyncio.sleep(base + jitter)
                
                except RateLimitError as e:
                    cb.record_failure()
                    retry_after = e.retry_after or 60
                    await asyncio.sleep(retry_after)
                    last_error = f'rate_limit_{vendor}'
                    break  # try next vendor
                
                except Exception as e:
                    cb.record_failure()
                    last_error = f'{type(e).__name__}_{vendor}'
                    break  # try next vendor
        
        # All vendors failed → try cache
        cached = await self.cache.get(query.cache_key)
        if cached:
            latency = (time.time() - start) * 1000
            return APICallResult(
                success=True,
                response=cached,
                latency_ms=int(latency),
                used_fallback=True,
                vendor_used='cache'
            )
        
        # All exhausted, queue for async
        await self.queue.enqueue(query, ttl=3600)
        return APICallResult(
            success=False,
            error=f'all_vendors_failed_last_{last_error}',
            latency_ms=int((time.time() - start) * 1000),
            used_fallback=True,
        )
    
    async def _call_vendor(self, vendor, query):
        client = self.clients[vendor]
        return await client.complete(query)
```

### Multi-vendor failover architecture

```
                          ┌─────────────────────────────┐
                          │     User Request             │
                          └──────────────┬───────────────┘
                                         │
                                         ▼
                          ┌─────────────────────────────┐
                          │  Resilient API Client       │
                          └──────┬─────────┬────────────┘
                                 │         │
                ┌────────────────┴─────────┴────────────────┐
                │                                            │
                ▼                                            ▼
        ┌──────────────┐                            ┌──────────────┐
        │ Vendor A     │                            │ Circuit      │
        │ (primary)    │                            │ Breakers     │
        │              │                            │              │
        │ + Rate limit │                            │ - Per vendor │
        │ + Retry      │                            │ - Half-open  │
        │ + Timeout    │                            │   testing    │
        └──────┬───────┘                            └──────────────┘
               │
               ▼ (if failing)
        ┌──────────────┐
        │ Vendor B     │  (failover)
        └──────┬───────┘
               │
               ▼ (if failing)
        ┌──────────────┐
        │ Cache        │  (stale OK)
        └──────┬───────┘
               │
               ▼ (if no cache)
        ┌──────────────┐
        │ Async queue  │  (degrade to async)
        └──────────────┘
```

---

## Gao Xin 简历专属 reframe

### Pakistan ASR 40-minute outage (PRIMARY STAR)

**S** (Situation):
> "Voice agent in Pakistan, peak hours (10am-2pm local). Third-party ASR API (transcribe audio to text) had intermittent 30-second timeouts. Approximately 40% of calls in Pakistan affected. This was March 2026, during a regulator-watched pilot."

**T** (Task):
> "Detect, mitigate, and resolve without:
> 1. Calling regulator (they were watching the pilot)
> 2. Breaking the rest of voice agent (other markets unaffected)
> 3. Doubling the bill via amplification
>
> MTTR target was < 15 minutes for P1. Voice agent had SLO of 99.5% uptime per market."

**A** (Action — concrete steps):

```
T+0:00 — ASR timeouts spike to 8%
T+0:03 — Drift dashboard alert (input quality scores dropped)
         (our internal drift metric — confidence on transcribed text)
T+0:04 — On-call paged, joined Slack #voice-agent-incidents
T+0:05 — Triage:
         - Region scope: Pakistan only (other 6 markets fine)
         - Endpoint scope: ASR only (TTS, LLM, payment all fine)
         - Time pattern: started gradually 14:32 local
         - No recent deploys on our side
         - Vendor status page: nothing yet
T+0:08 — Mitigation deployed:
         - Activated circuit breaker on primary ASR vendor (Pakistan region)
         - Failed over to backup vendor (different provider, pre-configured)
         - Backup latency 1.5x but functional
         - Local team notified
T+0:10 — Customer-facing impact:
         - Calls completing with 30% higher latency
         - 0% calls failing (vs would have been 40% without failover)
T+0:12 — Vendor escalation:
         - Submitted ticket with request_ids, time range, error pattern
         - Mentioned regulator-watched pilot for priority
         - Vendor confirmed within 8 min: "investigating Pakistan POP issue"
T+0:35 — Vendor restored primary
T+0:40 — Circuit breaker test (half-open) → success → closed
T+0:42 — Failed back to primary, latency normal
T+1:00 — Initial postmortem draft

Total user impact: 40 min of degraded latency (no failed calls)
MTTR (degradation): 12 minutes (target was 15)
MTTR (full resolution): 40 minutes
```

**R** (Result with concrete numbers):

- **MTTR 12 minutes** vs typical 30+ minutes (without failover)
- **0% calls failed** (vs estimated 40% if no failover)
- **Regulator unaware** (calls completed, just slower)
- **Cost saving**: backup vendor 1.5x cost for 40 min = ~$200 vs estimated $50k revenue impact + brand risk

**Postmortem action items implemented**:
1. **Multi-vendor pre-configuration** for all regions (was only Pakistan)
2. **Faster detection** — drift threshold 5% → 3% (would have caught 1 min earlier)
3. **Automated failover** — was manual button, now auto on circuit breaker
4. **Status page auto-update** — on circuit breaker trigger, internal customer-facing status updates
5. **Vendor SLA enforcement** — added MTTR clause to contract renewal

### BNPL chatbot — vendor latency spike

**S**: Anthropic API latency spike during Asia peak hours.

**T**: Detect, mitigate, not impact users.

**A**:
- Drift on response_latency_p99 caught in 2 min
- Mitigation: scale down concurrency, cache hits served via cached fallback
- Escalated to Anthropic Enterprise with request_ids
- Anthropic confirmed regional issue, resolved in 25 min

**R**: 30% of requests hit cached fallback (acceptable quality), 0 user-facing errors.

### TikTok PayLater — payment provider intermittent failure

**S**: Payment provider intermittent 5xx errors (1-3% rate).

**T**: Don't drop transactions, don't double-charge.

**A**:
- Idempotency key on all transactions (already in place)
- Retry with exponential backoff
- After 3 retries, queue for async processing
- Customer notified "processing" + later confirmation

**R**: 0 lost transactions, 0 double-charges, ~50ms p99 latency increase.

---

## 5 个 Follow-ups

**Q1**: "Vendor support is unresponsive. What do you do?"

**A**: Escalation ladder:
1. **Original ticket** — wait for SLA response
2. **TAM (if Enterprise)** — direct ping, same Slack channel
3. **Account manager** — sales contact, often has internal escalation power
4. **Public visibility** — Twitter / Discord mention can speed response (last resort)
5. **Multi-vendor parallel** — don't wait, failover to alternate vendor
6. **Engineering contacts** — if you've built relationships at vendor conferences / community

For enterprise contracts, **enforce SLA in writing** — if vendor doesn't meet response SLA, document and use at contract renewal.

**Q2**: "How do you decide P0 vs P1 vs P2?"

**A**: 3-axis scoring:
1. **User impact**: how many affected? % of total?
2. **Severity**: hard fail (can't use) vs degradation (slower, partial)?
3. **Business impact**: revenue per minute? reputational? regulatory?

```
P0 (page now, all-hands):
  - >50% users affected
  - Hard fail (service down)
  - >$10k/hour revenue impact
  - Or regulatory / compliance breach

P1 (page within 15 min):
  - 10-50% users affected
  - Major degradation
  - $1-10k/hour impact

P2 (investigate within 1 hour):
  - <10% users
  - Minor degradation
  - <$1k/hour

P3 (track, fix when convenient):
  - Edge cases, no user impact
  - Tech debt
```

**Q3**: "How do you communicate during an incident?"

**A**: 3 channels, different audiences:

```
Internal #incident-channel (real-time):
  - Live updates every 5-10 min
  - "T+15: mitigation deployed, error rate 8% → 2%"
  - Owner / status / next step
  - All hands welcome

Status page (external):
  - First update within 5 min of detection
  - Updates every 15-30 min
  - User-facing language (no jargon)
  - "We're investigating elevated latency for some users"
  - "Issue identified, deploying fix"
  - "Service restored, monitoring"

Stakeholder updates (leadership, customer if direct):
  - First update within 15 min
  - Hourly thereafter
  - Business impact, ETA, decision points
  - Phone / email for P0
```

**Q4**: "Multi-vendor setup — how to maintain?"

**A**: 4 practices:
1. **Eval portability** — eval set runs against all vendors regularly (quarterly minimum)
2. **Active canary** — 95% primary, 5% secondary always live → know vendor quality + maintain warm path
3. **Cost monitoring** — track spend per vendor, rebalance if pricing shifts
4. **Vendor relationship** — even if 5% traffic, maintain TAM contact, attend their events

Cost: 5% canary = ~5% extra cost. Justified by:
- Real-time quality comparison
- Pre-tested failover (vs cold failover risk)
- Negotiating leverage (vendor knows you can leave)

**Q5**: "What's the difference between intermittent and constant failure?"

**A**:
- **Constant**: 100% failure, simpler diagnosis (something broke)
- **Intermittent**: partial failure, harder
  - Could be: shared resource saturation, specific endpoint, specific payload, regional, time-of-day
  - Diagnosis requires slicing (by user, by endpoint, by region, by payload size, by time)
  - Mitigation is often "shed load" + "retry with exponential backoff with jitter"
  - Root cause often takes longer (need pattern, not single failure)

**Specific intermittent patterns**:
- Resource exhaustion: GC, file descriptor leak, connection pool
- Specific request shape: large payloads, certain languages, specific models
- Cascading failure: retry amplification, dependency timeout chain
- Vendor partial outage: one region, one endpoint, one model

---

## ❌ 死路答法

1. **"Just check status page"** — superficial, vendor may not have updated
2. **No 'our side first' check** — blame vendor immediately, often wrong
3. **No mitigation before root cause** — keep user impact going
4. **No specific data in vendor escalation** — slow vendor response
5. **No multi-vendor / fallback** — single point of failure
6. **No idempotency key** — retries cause double-charge / double-action
7. **No retry jitter** — thundering herd amplifies vendor issue
8. **No postmortem culture** — same incident recurs
9. **No customer comm during incident** — silent outage worse than communicated
10. **No SLO / alert tuning after** — same detection gap next time

---

## ✅ 加分项

1. **6-step diagnosis methodology** — systematic, not panicked
2. **Our side first principle** — humility + accurate
3. **Specific tools** (curl-format, mtr, ss, headers parsing)
4. **Mitigation patterns** (circuit breaker, jitter, cached fallback, async queue, multi-vendor)
5. **Idempotency key** for non-idempotent operations
6. **Vendor escalation template** with request_ids + impact
7. **Multi-vendor failover** with active canary
8. **5-phase incident response** (detect / triage / mitigate / investigate / comm)
9. **Postmortem action items** specific + owners + dates
10. **Quote Pakistan ASR 40-min** with concrete MTTR / impact numbers

---

## 一句话总结

> **Intermittent 3rd-party failure diagnosis: clarify pattern first, check our side (retries amplifying, rate limit, network) before blaming vendor, isolate scope (endpoint / region / customer), mitigate before root cause (circuit breaker + fallback + multi-vendor), escalate with specific request_ids + business impact, postmortem with action items. Pakistan ASR 40-min outage with MTTR 12 min is the reference story.**

---

## Cheat Sheet

```
Clarify 'intermittent':
  - Rate (1 in 10? 1 in 1000?)
  - Pattern (time, endpoint, region, user, payload)
  - When started (today? deploy correlation?)
  - Severity (hard timeout? slow? partial?)

6-step diagnosis:
  1. OUR side first
  2. THEIR side
  3. Isolate SCOPE
  4. MITIGATE (stop bleeding)
  5. ESCALATE with data
  6. POSTMORTEM + prevention

Our-side checks:
  - Retry amplification (graph requests vs user requests)
  - Rate limit (x-ratelimit-* headers)
  - Network (dig, mtr, ss)
  - Payload size growth

Their-side signals:
  - Status page
  - Response headers (x-request-id, retry-after)
  - Downdetector / Reddit
  - Pattern (region / endpoint / time)

Scope slicing:
  - By time, endpoint, tenant, region, payload size, instance, model

Mitigation patterns:
  - Circuit breaker (auto-stop calling)
  - Exponential backoff + jitter (avoid herd)
  - Cached fallback (stale OK)
  - Async queue (degrade to async)
  - Multi-vendor failover
  - Idempotency keys (side-effect tools)
  - Load shedding (priority traffic only)

Vendor escalation:
  - Specific request_ids
  - Time range
  - Error pattern
  - Business impact $$
  - Our trace data
  - Mitigation in progress (shows competence)

Escalation tiers:
  Enterprise: TAM / dedicated Slack, 15-min SLA
  Pro: ticket, 4h SLA
  Free: community only

5-phase IR:
  1. Detect (<5 min)
  2. Triage (5 min)
  3. Mitigate (15 min target)
  4. Investigate (1 hour)
  5. Comm + Postmortem

Communication:
  Internal #incident: live every 5-10 min
  Status page: 5 min first, every 15-30 min
  Stakeholders: 15 min first, hourly

Severity:
  P0: >50% users / hard fail / >$10k/hr
  P1: 10-50% users / major degrad / $1-10k/hr
  P2: <10% users / minor / <$1k/hr
  P3: edge cases / tech debt

Postmortem:
  Timeline, impact, root cause
  What went well / poorly
  Action items + owners + dates
  Runbook update

Multi-vendor maintenance:
  - Eval portability (quarterly)
  - Active canary (5% secondary)
  - Cost monitoring + rebalance
  - Vendor relationship investment

Specific tools:
  curl with timing: curl -w "@curl-format.txt"
  network: dig, nslookup, mtr, traceroute, tcpdump
  connections: ss -tn, netstat
  TLS: openssl s_client
  load: ab, wrk, locust

Case studies:
  - Pakistan ASR 40-min outage: MTTR 12 min, 0% failed
  - BNPL latency spike: cached fallback, 0 user-facing errors
  - Payment provider 5xx: idempotency + queue, 0 lost transactions

Anti-patterns:
  - Blame vendor first (often our side)
  - No mitigation before root cause
  - Vague vendor escalation
  - Single-vendor architecture
  - No idempotency on retries
  - No jitter (thundering herd)
  - Silent outage (no comm)
  - No postmortem culture

Quotes for interview:
  - "Our side first — vendor blame is satisfying but often wrong"
  - "Mitigate before root cause — stop the bleeding"
  - "Multi-vendor with active canary is 5% cost for full failover"
  - "Specific request_ids in escalation = fast vendor response"
  - "MTTR 12 min on Pakistan ASR via failover, 0% user-facing failures"
```
