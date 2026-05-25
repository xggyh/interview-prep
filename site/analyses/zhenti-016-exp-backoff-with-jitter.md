## Q16 · 给不稳定 API 实现带 jitter 的指数退避

> "Implement an **exponential backoff with jitter** retry mechanism for an unstable HTTP API. **Explain the jitter math**, what errors to retry vs not, and how it interacts with **circuit breaking** and **rate limiting**."

**中文翻译**:

> "为一个不稳定的 HTTP API 实现一套**带 jitter (抖动) 的指数退避**重试机制. **讲清楚 jitter 数学**, 哪些错误该 retry 哪些不该, 以及它怎么跟 **circuit breaking (熔断)** 和 **rate limiting (限流)** 协同."

**Round**: Coding (60 min)
**出处**: Exponent 2026 FDE · 公司: **Anthropic** (high frequency), OpenAI, Stripe, Anyscale
**难度**: Medium
**主要技能**: distributed reliability fundamentals, math, classification, production-aware

---

## 📖 术语速查 (本题用到的)

> 退避重试是 distributed reliability 的灵魂. 这堆术语 5 min 扫完, AWS paper + HTTP 状态码全 get.

### Retry / Jitter 算法

| 术语 | 解释 |
|---|---|
| **Exponential backoff (指数退避)** ⭐ | 每次失败后等 `base × 2^n` 秒. n=0,1,2,3... 间隔 1s, 2s, 4s, 8s... |
| **Jitter (抖动)** ⭐ | 在 backoff 加随机, 防 thundering herd. AWS 推荐 full jitter. |
| **Full jitter** ⭐ | `delay = random.uniform(0, base * 2^n)`. AWS 经典 paper "Exponential Backoff And Jitter" 的推荐. |
| **Equal jitter** | `delay = exp/2 + random(0, exp/2)`. 保证至少一半的 backoff. |
| **No jitter** | `delay = base * 2^n`. 千 client 同时 retry → thundering herd, BAD. |
| **Decorrelated jitter** | `delay = min(cap, random(base, last_delay * 3))`. AWS 推大 fleet (>1k clients) 用这个, 收敛比 full jitter 平稳. |
| **`max_delay_s` / cap** | backoff 单次上限. 不能让 retry 1024 秒. |
| **`max_attempts`** | 总尝试次数. 3-5 合理. |
| **Thundering herd** ⭐ | 大量 client 同时 fail + 同时 retry → 第二波 spike. Jitter 防这个. |
| **Tail at Scale (Google paper)** | "tail latency at scale" — 提出 hedged request 等技巧. |
| **Hedged request** | p95 时 fire 备份请求, 取先返的. cost ↑ tail latency ↓. |

### Retry budget / 全局保护

| 术语 | 解释 |
|---|---|
| **Retry budget** ⭐ | 全局 retry 速率上限 (e.g., 总 retry ≤ 10% 请求). 防 cascading retry storm. 用 token bucket 实现 (Q11). |
| **Retry storm** | 多 client × 多 retry × cascading = 雪崩. budget cap 防这个. |
| **Deadline propagation** | request 总 deadline 跨 retry 不变. 超 deadline 直接 raise, 不再 sleep. |
| **Context cancellation** | caller cancel (`asyncio.CancelledError`) 时 retry 必须立即 propagate, 不能继续 retry. |

### HTTP / API 错误分类

| 术语 | 解释 |
|---|---|
| **4xx vs 5xx** ⭐ | 4xx = client 错 (不 retry); 5xx = server 错 (retry). |
| **`429 Too Many Requests`** | 限流. **必须 honor `Retry-After`**, 不要自己算. |
| **`Retry-After` header** | 服务端告诉 "X 秒后再试". 单位秒, 或 HTTP-date (`Wed, 21 Oct 2026 07:28:00 GMT`). |
| **`500 Internal Server Error`** | 服务端通用错. 可 retry. |
| **`502 Bad Gateway`** | LB / proxy 拿不到后端. 可 retry. |
| **`503 Service Unavailable`** | 服务端过载. 可 retry, 看 Retry-After. |
| **`504 Gateway Timeout`** | LB 等后端超时. **仅 idempotent 时 retry** (不知道 server 跑没跑). |
| **`408 Request Timeout`** | 服务端嫌客户端发太慢. 可 retry. |
| **`400 Bad Request`** | 请求格式错. **不 retry** (bug, 重试无意义). |
| **`401 Unauthorized`** | 没认证. refresh token 后 retry 一次, 不无限. |
| **`403 Forbidden`** | 没权限. 不 retry. |
| **`409 Conflict`** | 冲突 (乐观锁). 默认不 retry. |
| **`422 Unprocessable Entity`** | 语义错 (e.g., schema 校验 fail). 不 retry. |

### 幂等性 (Idempotency)

| 术语 | 解释 |
|---|---|
| **Idempotent (幂等)** ⭐ | 同操作多次执行结果相同. GET / PUT 是; POST / DELETE 默认不是. |
| **Idempotency-Key header** | client 给每个 POST 带 key, 服务端 cache 24h. 重复 key → 返 cached response. Stripe/OpenAI 都用. |
| **`Idempotency-Key` 生成** | `hash(user_id, operation, payload)`. 同 op 永远同 key. |
| **At-least-once + idempotent = de facto exactly-once** | 实际 exactly-once 的工程实现. |

### Circuit breaker / 配合

| 术语 | 解释 |
|---|---|
| **Circuit breaker (熔断器)** ⭐ | 三态: CLOSED (正常 retry) → N 错误 → OPEN (拒绝调用, 等冷却) → HALF-OPEN (试探一次) → 成 → CLOSED. |
| **Half-open** | 熔断器冷却后的探测态. 一次成功就回 CLOSED, 失败回 OPEN. |
| **Cooldown** | 熔断 open 后等待时间. 一般 30s-5min. |

### Python / 异步

| 术语 | 解释 |
|---|---|
| **`asyncio.sleep` vs `time.sleep`** ⭐ | asyncio 用前者 (yield 给 loop), 后者会**阻塞 event loop**, 整个 process 卡住. |
| **`@functools.wraps`** | 写 decorator 时保留原函数名 / docstring. |
| **`asyncio.iscoroutinefunction`** | 检查 fn 是不是 async, 决定 decorator 走 sync 还是 async 路径. |
| **`time.monotonic`** | 单调时钟. deadline 计算必用, 不被 NTP 回拨影响. |
| **`patch('time.sleep')`** | test 时把 `time.sleep` mock 掉, 不真睡几秒. |
| **`freezegun`** | test 时冻结时间的库. mock clock 干净方案. |

### 库 / 工具

| 术语 | 解释 |
|---|---|
| **`tenacity`** | Python retry 库, 行业标准. `@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter())`. |
| **`backoff`** | 另一个 retry 库, 早期流行. |
| **AWS Architecture Blog "Exponential Backoff And Jitter"** | jitter 算法的经典 paper, 2015. 必读. |

### 监控

| 术语 | 解释 |
|---|---|
| **`retry_total / retry_success / retry_exhausted`** | Prometheus counter 三件套. retry rate 看 grafana 必备. |
| **`retry_seconds_total`** | 总 sleep 累积时间 (sum). 跟 retry_count 一起看 backoff 行为. |
| **SLA / SLO / SLI** | Service Level Agreement / Objective / Indicator. 决定 deadline budget. |

---

## 这道题在考什么

很多候选人写完 `time.sleep(2 ** attempt)` 就交 — 0 分. 真考的是:

1. **Jitter math 你真懂吗** — full jitter vs equal jitter vs decorrelated jitter, 各自数学意义和场景. 答得出 AWS 那篇经典 paper 加分.
2. **Retry classification** — 哪些 error 该 retry, 哪些不该. 4xx vs 5xx 还不够, 要细到 `429` (用 Retry-After), `503` (retry), `502` (retry), `504` (depends), `400` (don't), `401` (refresh token then retry).
3. **Retry budget** — 单 call 重试 N 次还不够, 全局 retry budget (e.g., 总 retry < 10% of requests) 防止 cascading.
4. **Circuit breaker integration** — retry + breaker 配合: breaker open 就别 retry, 等冷却.
5. **Idempotency awareness** — POST 你能 retry 吗? Idempotency-Key header 是不是必须.
6. **Async vs sync** — `time.sleep` 阻塞 event loop, async 需要 `asyncio.sleep`.
7. **Context awareness** — retry 期间 deadline / context cancellation 怎么 propagate.

Anthropic 用这道题 filter 出"知道理论 + 写过 production retry 代码"的人. 是他们 Claude SDK 客户端的核心.

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|------|--------|--------|
| 1 | Clarify | 0-5 min | 哪种 API, 幂等性, 错误分类, 总 budget | "5 things..." |
| 2 | Math 推导 | 5-12 min | 写 4 种 jitter 公式 | "There are 4 jitter strategies; let me write each." |
| 3 | Retry function | 12-30 min | sync + async 两版 | "I'll write sync first, async next." |
| 4 | Classify errors | 30-40 min | 4xx/5xx/网络/timeout | "Here's my classification table." |
| 5 | Budget + breaker | 40-50 min | 全局 retry rate + breaker integration | "Two safety rails..." |
| 6 | Test | 50-55 min | 5-6 unit tests with mock clock | "Mock clock to make test deterministic." |
| 7 | Discuss | 55-60 min | thundering herd, deadline propagation | "Trade-offs..." |

---

## 必问 clarifying questions

**1. 上游 API 性质**

> "What kind of API — REST? gRPC? GraphQL? Provider gives Retry-After header? Idempotency-Key support?"

Why: 决定 error 解析 + idempotency 策略.

**2. 幂等性**

> "Are calls idempotent (GET / PUT) or non-idempotent (POST without idempotency-key)?"

Why: 非幂等 + 中间失败 = 双 charge. 必须 idempotency key.

**3. SLA / Deadline**

> "What's the latency budget? p99 5s? p99 60s? Is retry-bounded by deadline?"

Why: deadline 决定 retry 几次 — 5s budget 加 3 次 retry × 2s 就超.

**4. Error 来源**

> "Is the 5xx from cloud (transient), our service (bug), or rate limiter (429)?"

Why: 429 用 Retry-After; 5xx 用 exp backoff; 4xx 不 retry.

**5. 总 budget**

> "Should I have a global retry budget (e.g., max 10% of requests are retries)?"

Why: 防 cascading retry storm.

**6. 调用方期望**

> "What does the caller want — best effort? Strict success? Failed-fast?"

Why: 决定 max_attempts.

**7. 监控**

> "Should I emit metrics — retry_count, retry_success, retry_exhausted?"

Why: 总是要的, 但有时面试官只想看代码不要 telemetry.

---

## 详细解题流程

### Step 1: Design decisions + math (设计决策与数学, 8-10 min)

**4 种 jitter 公式 (写在白板上)**:

```
attempt n (0-indexed), base = 100ms, cap = 30s

1. No jitter (naive, BAD):
     sleep = min(cap, base * 2**n)
     问题: 千个 client 同时 fail 同时 retry → thundering herd

2. Full jitter (RECOMMENDED — AWS / Google):
     sleep = random.uniform(0, min(cap, base * 2**n))
     - 完全打散, 任何瞬间 retry 概率均匀
     - 每次 retry 实际 mean = exponential/2, std = exponential/sqrt(12)
     - 缺点: 某次 retry 可能很短 (0.1s), worker 紧追

3. Equal jitter:
     temp = min(cap, base * 2**n)
     sleep = temp/2 + random.uniform(0, temp/2)
     - 保证至少 half 的 backoff, 避免立刻重发
     - 介于 no-jitter 和 full-jitter 之间

4. Decorrelated jitter:
     sleep = min(cap, random.uniform(base, last_sleep * 3))
     - state-ful, 每次 retry 依赖上次 sleep
     - 收敛比 full jitter 慢但平稳
     - AWS Architecture Blog 推荐 (when you have many retrying clients)
```

**写出来后讲**: "Default I pick **full jitter** because it's the simplest and AWS empirically shows it minimizes both completion time and server load. Decorrelated is slightly better at large fleets (>1000 clients) per AWS blog."

**Error classification table**:

| Code / 类型 | Retry? | 怎么 retry | 备注 |
|-------------|--------|------------|------|
| Network error (DNS, refused, reset) | Yes | exp backoff | 多见于 transient |
| Timeout (deadline exceeded) | Maybe | only if idempotent | non-idempotent POST 不 retry |
| 408 Request Timeout | Yes | exp backoff | server 自己说 retry |
| 429 Too Many Requests | Yes | **respect Retry-After header** | 否则 exp backoff |
| 500 Internal Server Error | Yes | exp backoff | maybe deploy in progress |
| 502 Bad Gateway | Yes | exp backoff | LB / proxy 问题 |
| 503 Service Unavailable | Yes | Retry-After 或 exp backoff | overloaded |
| 504 Gateway Timeout | Maybe | only idempotent | non-idempotent: 不知道 server 跑没跑 |
| 400 Bad Request | No | — | bug, 重试无意义 |
| 401 Unauthorized | Once after token refresh | not infinite | |
| 403 Forbidden | No | — | permission, 重试无意义 |
| 404 Not Found | No | — | (unless eventual consistency 已知) |
| 409 Conflict | No (default) | — | sometimes retry on optimistic lock |
| 410 Gone | No | — | resource gone, permanent |
| 422 Unprocessable | No | — | client bug |

### Step 2: Initial implementation (初始实现, 15-20 min)

```python
"""
Exponential backoff with jitter + retry framework.

Features:
  - 4 jitter strategies (no, full, equal, decorrelated)
  - Configurable retry classification (which errors to retry)
  - Per-call deadline (don't retry past it)
  - Retry budget (global rate limiter on retries)
  - Async (asyncio) and sync versions
  - Circuit breaker integration
  - Honors Retry-After header
  - Emits telemetry callbacks
"""
import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, Awaitable, Any, TypeVar, Generic
from functools import wraps

T = TypeVar('T')
log = logging.getLogger('retry')


class JitterStrategy(Enum):
    NONE = 'none'
    FULL = 'full'
    EQUAL = 'equal'
    DECORRELATED = 'decorrelated'


@dataclass
class RetryConfig:
    max_attempts: int = 5
    base_delay_s: float = 0.5
    max_delay_s: float = 30.0
    jitter: JitterStrategy = JitterStrategy.FULL
    deadline_s: Optional[float] = None       # total budget across all attempts
    # Error classifier: returns (retriable: bool, override_delay_s: float | None)
    classifier: Optional[Callable[[BaseException], 'RetryDecision']] = None


class RetryDecision:
    __slots__ = ('retry', 'override_delay_s', 'reason')

    def __init__(self, retry: bool, override_delay_s: Optional[float] = None,
                 reason: str = ''):
        self.retry = retry
        self.override_delay_s = override_delay_s
        self.reason = reason

    @classmethod
    def yes(cls, delay: Optional[float] = None, reason: str = ''):
        return cls(True, delay, reason)

    @classmethod
    def no(cls, reason: str = ''):
        return cls(False, None, reason)


def compute_delay(
    attempt: int,
    base: float,
    cap: float,
    strategy: JitterStrategy,
    last_delay: float = 0.0,
) -> float:
    """Pure delay computation given a strategy. attempt is 0-indexed."""
    exp = min(cap, base * (2 ** attempt))
    if strategy == JitterStrategy.NONE:
        return exp
    if strategy == JitterStrategy.FULL:
        return random.uniform(0, exp)
    if strategy == JitterStrategy.EQUAL:
        return exp / 2 + random.uniform(0, exp / 2)
    if strategy == JitterStrategy.DECORRELATED:
        return min(cap, random.uniform(base, max(last_delay, base) * 3))
    raise ValueError(f'unknown strategy: {strategy}')


# ============ Default classifier for HTTP exceptions ============

class TransientError(Exception):
    """Network / connection / known transient HTTP — retry."""
    def __init__(self, msg: str, retry_after_s: Optional[float] = None):
        super().__init__(msg)
        self.retry_after_s = retry_after_s


class PermanentError(Exception):
    """4xx-class — do not retry."""


def default_http_classifier(exc: BaseException) -> RetryDecision:
    """Maps exception types to retry decision. Override per use-case."""
    if isinstance(exc, TransientError):
        return RetryDecision.yes(exc.retry_after_s, reason='transient')
    if isinstance(exc, PermanentError):
        return RetryDecision.no(reason='permanent')
    if isinstance(exc, asyncio.TimeoutError):
        return RetryDecision.yes(reason='asyncio_timeout')
    if isinstance(exc, ConnectionError):
        return RetryDecision.yes(reason='connection')
    # Conservative: unknown errors don't retry
    return RetryDecision.no(reason='unknown')


# ============ Retry budget (token bucket — see Q11) ============

class RetryBudget:
    """
    Caps total retry rate. If retries exceed N per second, deny further retries.
    Prevents retry storm in cascading failures.
    """
    def __init__(self, max_retries_per_second: float = 10.0, capacity: float = 50.0):
        self.rate = max_retries_per_second
        self.cap = capacity
        self.tokens = capacity
        self.last_refill = time.monotonic()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.cap, self.tokens + elapsed * self.rate)
        self.last_refill = now

    def try_retry(self) -> bool:
        self._refill()
        if self.tokens < 1:
            return False
        self.tokens -= 1
        return True


# ============ Sync retry ============

def retry_sync(
    fn: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    budget: Optional[RetryBudget] = None,
    on_retry: Optional[Callable[[int, BaseException, float], None]] = None,
    **kwargs,
) -> T:
    """
    Run fn with retry. Returns result or raises the last exception.
    """
    cfg = config or RetryConfig()
    cls = cfg.classifier or default_http_classifier
    deadline_at = time.monotonic() + cfg.deadline_s if cfg.deadline_s else None
    last_delay = 0.0

    for attempt in range(cfg.max_attempts):
        try:
            return fn(*args, **kwargs)
        except BaseException as e:
            decision = cls(e)
            if not decision.retry:
                raise
            if attempt == cfg.max_attempts - 1:
                raise
            if budget is not None and not budget.try_retry():
                log.warning('retry budget exhausted, giving up')
                raise
            # Compute delay
            if decision.override_delay_s is not None:
                delay = decision.override_delay_s
            else:
                delay = compute_delay(attempt, cfg.base_delay_s, cfg.max_delay_s,
                                       cfg.jitter, last_delay)
            last_delay = delay
            # Check deadline
            if deadline_at and (time.monotonic() + delay) > deadline_at:
                log.info('deadline would be exceeded, no more retry')
                raise
            if on_retry:
                on_retry(attempt, e, delay)
            log.info('attempt %d failed (%s), sleeping %.2fs', attempt, decision.reason, delay)
            time.sleep(delay)
    raise RuntimeError('unreachable')


# ============ Async retry ============

async def retry_async(
    fn: Callable[..., Awaitable[T]],
    *args,
    config: Optional[RetryConfig] = None,
    budget: Optional[RetryBudget] = None,
    breaker: Optional[Any] = None,         # optional circuit breaker (q14 style)
    on_retry: Optional[Callable[[int, BaseException, float], None]] = None,
    **kwargs,
) -> T:
    cfg = config or RetryConfig()
    cls = cfg.classifier or default_http_classifier
    deadline_at = time.monotonic() + cfg.deadline_s if cfg.deadline_s else None
    last_delay = 0.0

    for attempt in range(cfg.max_attempts):
        # Circuit breaker: if open, bail without trying
        if breaker is not None and breaker.is_open:
            raise TransientError('circuit breaker open')
        try:
            return await fn(*args, **kwargs)
        except BaseException as e:
            decision = cls(e)
            if breaker is not None:
                breaker.record_error()
            if not decision.retry:
                raise
            if attempt == cfg.max_attempts - 1:
                raise
            if budget is not None and not budget.try_retry():
                log.warning('retry budget exhausted')
                raise
            if decision.override_delay_s is not None:
                delay = decision.override_delay_s
            else:
                delay = compute_delay(attempt, cfg.base_delay_s, cfg.max_delay_s,
                                       cfg.jitter, last_delay)
            last_delay = delay
            if deadline_at and (time.monotonic() + delay) > deadline_at:
                raise
            if on_retry:
                on_retry(attempt, e, delay)
            await asyncio.sleep(delay)
    raise RuntimeError('unreachable')


# ============ Decorator ============

def with_retry(config: Optional[RetryConfig] = None,
               budget: Optional[RetryBudget] = None):
    def deco(fn):
        if asyncio.iscoroutinefunction(fn):
            @wraps(fn)
            async def aw(*a, **kw):
                return await retry_async(fn, *a, config=config, budget=budget, **kw)
            return aw
        else:
            @wraps(fn)
            def sw(*a, **kw):
                return retry_sync(fn, *a, config=config, budget=budget, **kw)
            return sw
    return deco


# ============ Real-world HTTP classifier ============

def http_classifier_for_requests(exc: BaseException) -> RetryDecision:
    """For the `requests` library's HTTPError + sub-exceptions."""
    import requests
    if isinstance(exc, requests.exceptions.ConnectionError):
        return RetryDecision.yes(reason='conn_err')
    if isinstance(exc, requests.exceptions.Timeout):
        return RetryDecision.yes(reason='timeout')
    if isinstance(exc, requests.exceptions.HTTPError):
        r = exc.response
        if r is None:
            return RetryDecision.yes(reason='no_response')
        status = r.status_code
        if status == 429:
            ra = r.headers.get('Retry-After')
            try:
                delay = float(ra) if ra else None
            except ValueError:
                delay = None
            return RetryDecision.yes(delay, reason='rate_limited')
        if status in (408, 500, 502, 503, 504):
            ra = r.headers.get('Retry-After')
            try:
                delay = float(ra) if ra else None
            except ValueError:
                delay = None
            return RetryDecision.yes(delay, reason=f'http_{status}')
        if 400 <= status < 500:
            return RetryDecision.no(reason=f'http_{status}_client_error')
        return RetryDecision.no(reason=f'http_{status}_unknown')
    return RetryDecision.no(reason='unknown_exc')


# ============ HTTP wrapper with idempotency ============

def make_idempotency_key(*parts) -> str:
    import hashlib
    h = hashlib.sha256()
    for p in parts:
        h.update(repr(p).encode())
    return h.hexdigest()[:32]


def call_api_with_retry(method: str, url: str, *, payload=None,
                        idempotency_key: Optional[str] = None,
                        config: Optional[RetryConfig] = None) -> dict:
    """Wrapper showing how to wire retry + idempotency for HTTP calls."""
    import requests

    headers = {}
    if method == 'POST' and idempotency_key:
        headers['Idempotency-Key'] = idempotency_key

    def call():
        r = requests.request(method, url, json=payload, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()

    cfg = config or RetryConfig(classifier=http_classifier_for_requests)
    return retry_sync(call, config=cfg)
```

### Step 3: Tests with mock clock (用 mock clock 测试, 5-10 min)

```python
import unittest
from unittest.mock import patch, MagicMock
import time


class TestComputeDelay(unittest.TestCase):
    def test_no_jitter_is_deterministic(self):
        d0 = compute_delay(0, 1.0, 60, JitterStrategy.NONE)
        d1 = compute_delay(1, 1.0, 60, JitterStrategy.NONE)
        d2 = compute_delay(2, 1.0, 60, JitterStrategy.NONE)
        self.assertEqual(d0, 1.0)
        self.assertEqual(d1, 2.0)
        self.assertEqual(d2, 4.0)

    def test_no_jitter_cap(self):
        d = compute_delay(20, 1.0, 60, JitterStrategy.NONE)
        self.assertEqual(d, 60.0)

    def test_full_jitter_in_range(self):
        random.seed(42)
        for n in range(0, 8):
            for _ in range(20):
                d = compute_delay(n, 1.0, 60, JitterStrategy.FULL)
                self.assertGreaterEqual(d, 0)
                self.assertLessEqual(d, min(60, 1.0 * 2**n))

    def test_equal_jitter_lower_bound(self):
        random.seed(42)
        for n in range(0, 6):
            for _ in range(20):
                d = compute_delay(n, 1.0, 60, JitterStrategy.EQUAL)
                exp = min(60, 1.0 * 2**n)
                self.assertGreaterEqual(d, exp / 2)
                self.assertLessEqual(d, exp)

    def test_decorrelated_uses_last(self):
        random.seed(0)
        d1 = compute_delay(0, 1.0, 60, JitterStrategy.DECORRELATED, last_delay=0)
        d2 = compute_delay(1, 1.0, 60, JitterStrategy.DECORRELATED, last_delay=d1)
        d3 = compute_delay(2, 1.0, 60, JitterStrategy.DECORRELATED, last_delay=d2)
        # Each between base and 3*last_delay (capped)
        for d in (d1, d2, d3):
            self.assertGreaterEqual(d, 1.0)
            self.assertLessEqual(d, 60)


class TestRetrySync(unittest.TestCase):
    def test_succeeds_first_try(self):
        calls = []
        def f():
            calls.append(1)
            return 'ok'
        result = retry_sync(f, config=RetryConfig(max_attempts=3))
        self.assertEqual(result, 'ok')
        self.assertEqual(len(calls), 1)

    def test_succeeds_after_retry(self):
        calls = []
        def f():
            calls.append(1)
            if len(calls) < 3:
                raise TransientError('blip')
            return 'ok'
        with patch('time.sleep'):
            result = retry_sync(f, config=RetryConfig(max_attempts=5, base_delay_s=0.001))
        self.assertEqual(result, 'ok')
        self.assertEqual(len(calls), 3)

    def test_max_attempts_raises(self):
        def f(): raise TransientError('always')
        with patch('time.sleep'):
            with self.assertRaises(TransientError):
                retry_sync(f, config=RetryConfig(max_attempts=2, base_delay_s=0.001))

    def test_permanent_no_retry(self):
        calls = []
        def f():
            calls.append(1)
            raise PermanentError('bad request')
        with self.assertRaises(PermanentError):
            retry_sync(f, config=RetryConfig(max_attempts=5))
        self.assertEqual(len(calls), 1)  # only called once

    def test_deadline_aborts_retry(self):
        calls = []
        def f():
            calls.append(1)
            raise TransientError('blip')
        # Deadline 0.05s, base 0.1s — first retry would exceed deadline
        with self.assertRaises(TransientError):
            retry_sync(f, config=RetryConfig(
                max_attempts=10, base_delay_s=0.1, deadline_s=0.05,
                jitter=JitterStrategy.NONE,
            ))
        self.assertEqual(len(calls), 1)  # gave up before sleeping

    def test_retry_after_honored(self):
        sleeps = []
        with patch('time.sleep', side_effect=lambda s: sleeps.append(s)):
            calls = []
            def f():
                calls.append(1)
                if len(calls) == 1:
                    raise TransientError('rate limited', retry_after_s=2.5)
                return 'ok'
            retry_sync(f, config=RetryConfig(max_attempts=5, base_delay_s=0.001))
        self.assertEqual(sleeps, [2.5])

    def test_budget_exhausted(self):
        budget = RetryBudget(max_retries_per_second=0.1, capacity=1)
        budget.tokens = 0
        def f(): raise TransientError('blip')
        with self.assertRaises(TransientError):
            retry_sync(f, config=RetryConfig(max_attempts=5, base_delay_s=0.001),
                        budget=budget)


class TestRetryAsync(unittest.IsolatedAsyncioTestCase):
    async def test_async_succeeds_after_retry(self):
        calls = []
        async def f():
            calls.append(1)
            if len(calls) < 2:
                raise TransientError('blip')
            return 'ok'
        result = await retry_async(f, config=RetryConfig(
            max_attempts=3, base_delay_s=0.001))
        self.assertEqual(result, 'ok')


if __name__ == '__main__':
    unittest.main()
```

### Step 4: Edge cases + production discussion (边界情况与生产讨论, 10 min)

**Edge cases**:

1. **First attempt success** — no retry, no log spam, no delay
2. **Deadline already passed** — raise immediately, don't sleep
3. **Retry-After header in seconds** — `Retry-After: 30` → sleep 30s exactly
4. **Retry-After in HTTP-date** — `Retry-After: Wed, 21 Oct 2026 07:28:00 GMT` → parse + diff with now
5. **Connection reset mid-stream** — depends on idempotency
6. **Token expired (401) mid-retry** — refresh once, retry once, fail
7. **Two attempts return different errors** — log all, raise last
8. **Caller cancels** (asyncio.CancelledError) — re-raise immediately, don't retry
9. **OOM / KeyboardInterrupt** — don't retry, propagate
10. **Retry storm** — budget caps total retry rate
11. **Clock skew** in deadline math — use monotonic
12. **Reentrant** — same function retrying inside another retry; budget should cover both

**Thundering herd discussion**:

> "1000 clients all hit a 503 at T0. With no jitter all retry at T1, T2, T3, T4 — synchronized, server keeps overloading. With **full jitter**, retries spread uniformly across [0, exp]. AWS paper shows full jitter cuts both completion time and server load vs no jitter."

**Idempotency**:

```python
# When retrying POST, generate idempotency key from request payload + caller
key = make_idempotency_key(user_id, operation, request_body)
# Server: if seen this key in last 24h, return cached response
```

Without idempotency-key, retried POST might double-charge / double-create.

---

## 完整代码 (Production-ready)

整个 module 已在 Step 2. 使用示例:

```python
# Decorator usage
@with_retry(RetryConfig(max_attempts=5, base_delay_s=0.5,
                          jitter=JitterStrategy.FULL,
                          classifier=http_classifier_for_requests))
def fetch_user(uid):
    r = requests.get(f'https://api.example.com/users/{uid}')
    r.raise_for_status()
    return r.json()

# Imperative usage
budget = RetryBudget(max_retries_per_second=20)
result = retry_sync(call_api, config=RetryConfig(deadline_s=10), budget=budget)

# Async usage
result = await retry_async(http_get, url, config=RetryConfig(...))
```

---

## 复杂度分析

| | 说明 |
|--|------|
| Time per attempt | O(API call) |
| Total retry time (worst) | sum_{n=0}^{N-1} delay(n) ≤ N × cap = N × max_delay_s |
| Memory | O(1) per call (no buffer) |
| Budget overhead | O(1) per attempt (token bucket) |

**Expected sleep with full jitter**:
- E[sleep at attempt n] = min(cap, base × 2^n) / 2
- E[total backoff with N attempts] ≈ base × (2^N - 1) / 2

3 retries, base 1s: E[total] = (2^3-1)/2 = 3.5s. Reasonable for p99.

---

## Gao Xin 简历专属 reframe

- **Voice agent (7 markets)**: 我们 outbound call API 调三方 telephony provider (Twilio / Sinch), 用过 full jitter + 5 retries. Provider 429 / 503 经常发生. Retry budget 总 cap = 10% requests.
- **BNPL chatbot**: LLM API (OpenAI / Anthropic) 偶尔 5xx, 客户端用 exp backoff. Anthropic SDK 自带 retry, OpenAI SDK 也有.
- **Internal Agent Platform**: tool call 调外部 API 经常 fail, 我做的 retry framework 几乎和这道题一样 + Idempotency-Key 自动注入.
- **Indonesia refund tier**: fraud check 调外部 API, 用 retry + breaker + DLQ.
- **ConvFinQA**: 9-variant ablation 跑实验时, LLM API rate limited, 用 retry library `tenacity` (但是其实跟这道题等价).

**面试一句话**: "I've used this in production at TikTok across voice agent, chatbot, and refund pipelines. The biggest production learning was 429 with Retry-After must be honored verbatim, not computed — otherwise you fight the rate limiter and lose."

---

## 5 个 Follow-ups

**Q1**: "你给一个 client 实现的 retry, 100 个 client 同时 retry 怎么 coordinate?"

A: 不 coordinate — 用 jitter 让 client 自己 spread. 但 **server side** 可以:
- 不同 client 的 Retry-After 给不同时长 (load-aware)
- 503 时给 hint header `Retry-After: 5..30` random
- 不同 tenant 不同 budget

Server-side coordination 通常不做 — client-side jitter 就够 statistically spread.

**Q2**: "如果 retry 还是 fail, 你怎么 surface?"

A: 三层:
1. **Caller**: raise final exception with details — `(last_error, attempts, total_time_s)`
2. **Telemetry**: `retry_exhausted_total` counter labeled by error class
3. **Customer**: if it's a user-facing operation, 显示 "我们正在处理, 大约 X 分钟后重试" — 给具体, 不要 "something went wrong"

**Q3**: "Idempotent + non-idempotent 你怎么 mix?"

A: 在 decorator / config 加 `idempotent: bool`:
```python
@with_retry(RetryConfig(idempotent=False))  # POST without key
def create_resource(...): ...

# Logic:
if not idempotent and isinstance(exc, asyncio.TimeoutError):
    # We don't know if server processed it — bail to avoid double create
    raise
```
更好的方案: **强制** non-idempotent 必带 idempotency-key, 否则 reject 调用.

**Q4**: "Retry + circuit breaker, 谁优先?"

A: Breaker 优先 — open 时直接 raise, 不 attempt. Closed/half-open 时正常 retry. Breaker 状态由 error 历史驱动, 不由 retry 本身. 一个 call 的 retry 也会 record_error → 加速 breaker open.

**Q5**: "你怎么 test retry 不真睡几秒钟?"

A: 3 方法:
1. **`patch('time.sleep')`** — sync, 直接吃掉 sleep
2. **Mock clock** — inject `clock_fn = time.monotonic`, test 时 mock
3. **Async**: `asyncio.sleep(0)` 直接 yield, 或者 `freezegun`/`pytest-asyncio` fast-forward

Production: 我用 mock clock injection — 比 patch 干净.

---

## 死路答法

1. **`time.sleep(2 ** attempt)`** without jitter — thundering herd
2. **Retry on 400 / 401 / 422** — bug, 永远重试无意义
3. **Retry on connection timeout for non-idempotent POST** — double charge
4. **`max_attempts = 10` 而 base = 1s** — worst case 1+2+4+...+512 = 17min
5. **没 max_delay cap** — exp 增长无限大
6. **silent retry** — 没 log / 没 metric, prod 看不到 retry 风暴
7. **retry 不 propagate cancellation** — caller cancel 了 task 还在 retry
8. **time.sleep in async** — block event loop
9. **每个 retry 重新 build idempotency key** — server 看不到是同 op, double process
10. **没 deadline** — retry 可能比原 request budget 还长
11. **没 retry budget** — 1000 client × 5 retry × cascading = 雪崩

---

## 加分项

**Production discussion 加分**:

- **Decorrelated jitter for fleet > 1k** — full jitter 在小 fleet 够, 大 fleet AWS paper 推荐 decorrelated
- **Per-error-class retry policy** — 不同 error 不同 backoff (e.g., 429 用 Retry-After, 503 用 exp)
- **Adaptive max_attempts** — 历史 success rate 高 → 多 retry; 历史低 → fail fast
- **Hedged requests** (Tail at Scale paper) — 95th percentile 时 fire 备份 request, 取先返回. Trade latency for cost.
- **Server-side cooperation** — 服务端检测自己 overload, 主动给 `Retry-After: jitter[5,30]` 而不是固定值
- **Telemetry**: `retry_total`, `retry_success`, `retry_exhausted`, `retry_seconds_total` (sum of sleep), `retry_decisions{reason="429"}` — Grafana 看 retry pattern
- **Replay tool**: DLQ failed-after-retry 的 msg 可以 batch replay
- **Documentation**: 客户 SDK 文档明示 retry 行为, 比如 "We retry 5xx up to 3 times with full jitter, max 30s total"
- **Tenacity / Backoff library**: 不要 always rewrite — `pip install tenacity` 是行业标准. 但面试要会写, 因为很多客户 codebase 限装 lib.

---

## 一句话总结

> **Full jitter exp backoff + classify retriable (5xx, 429, network) vs not (4xx) + honor Retry-After + budget cap + deadline cap. AsyncIO 用 `asyncio.sleep`, sync 用 `time.sleep`. Non-idempotent → idempotency-key.**

---

## Cheat Sheet

```python
# Full jitter formula (default, recommended):
delay = random.uniform(0, min(cap, base * 2**attempt))

# Other strategies:
#   no jitter: min(cap, base * 2**attempt)        — thundering herd
#   equal:     exp/2 + random.uniform(0, exp/2)   — guarantees min delay
#   decorrelated: random.uniform(base, last*3)    — large fleets

# Classify:
#   Retry: 408, 429 (use Retry-After), 500, 502, 503, 504, network err, timeout (if idempotent)
#   Don't: 400, 401 (refresh once), 403, 404, 409, 410, 422

# Per-call deadline:
#   if (now + delay) > deadline_at: raise without sleep

# Retry budget:
#   token bucket: max_retries_per_second cap (e.g. 10/s)
#   denies further retry if exhausted

# Idempotency:
#   POST: send Idempotency-Key header
#   Server cache: same key in 24h → return cached response

# Anti-patterns:
#   no jitter
#   retry 4xx
#   retry non-idempotent on timeout
#   no max_delay cap
#   no retry budget
#   time.sleep in async loop
#   no Retry-After honored

# Composes with:
#   - Circuit breaker (q14): breaker open → no retry, wait cooldown
#   - Rate limiter (q11): retried request still counts against limit
#   - DLQ (q14): after max_attempts → DLQ for offline analysis
```
