## Q11 · 单用户限流 + 全局限流 Rate Limiter

> "Design and implement a rate limiter that supports **per-user limits** (e.g. 100 req/min per API key) **AND** a **global limit** (e.g. 10,000 req/min total across all users). Walk us through it, then code it. We may ask you to evolve it for a distributed setup."

**中文翻译**:

> "设计并实现一个 rate limiter (限流器), 支持**单用户限流** (e.g., 每个 API key 每分钟 100 个请求) **加上**一个**全局限流** (e.g., 所有用户加起来每分钟 10,000 个请求). 先讲思路再写代码. 我们可能让你演进到分布式版本."

**Round**: Coding (60 min, shared IDE or Google Doc)
**出处**: Exponent 2026 FDE · 公司: **Anthropic** (高频出题), OpenAI, Scale AI
**难度**: Medium-Hard
**主要技能**: 分布式协调, atomic ops, algorithm trade-offs, production robustness

---

## 📖 术语速查 (本题用到的)

> 限流题里的术语如果不懂, 算法解释都听不懂. 5 min 扫完, 后面跟得上.

### 算法 / 数据结构

| 术语 | 解释 |
|---|---|
| **Token bucket (令牌桶)** ⭐ | 限流主流算法. 桶里有 N 个 token, 每次请求消耗 1 个, 按固定 rate 回填; 桶空 → reject. 允许短时 burst (桶里囤的 token). |
| **Leaky bucket (漏桶)** | 请求进队列, 按固定速率漏出. 严格 shaping, 不允许 burst. 跟 token bucket 互斥语义. |
| **Fixed window counter** | 每个固定时窗 (e.g., 每分钟) 计数. 简单粗暴, 缺点是窗口边界可双倍 burst (59 秒 + 0 秒). |
| **Sliding window log** | 存所有 request timestamp, 查最近 N 秒数量. 精确但 O(N) memory per user. |
| **Sliding window counter** | Fixed window + 当前窗口线性插值, 平滑近似 sliding log. O(1) memory ±5% 精度. |
| **Burst (突发)** | 短时间内的流量峰值. Token bucket 允许 burst 等于桶 capacity. |
| **Refill rate** | Token 回填速率 (tokens/sec). 决定稳态吞吐. |
| **Atomic invariant** | 多个状态变更必须**全成功或全不变**. 这题里: 两个 bucket 都有 token 才扣, 否则**一个都不扣**. |

### Python / 并发 / 数据类型

| 术语 | 解释 |
|---|---|
| **`time.monotonic()`** ⭐ | 单调时钟 — 永远只增, NTP 不会回拨. 限流必用; `time.time()` 会被 NTP 调回. |
| **`@dataclass`** | Python 3.7+ 自动生成 `__init__/__eq__/__repr__` 的装饰器. 替代手写 boilerplate. |
| **`field(default_factory=...)`** | dataclass 默认值用工厂函数生成 (避免 mutable default 共享 bug). |
| **`threading.Lock`** | 单进程线程互斥锁. `with lock:` 保证临界区串行. |
| **GIL (Global Interpreter Lock)** | Python 全局解释器锁, 单进程内 CPython bytecode 互斥. 救一部分 race 但不全救 (e.g., 复合操作). |

### Redis / 分布式

| 术语 | 解释 |
|---|---|
| **Redis Lua script** ⭐ | Redis 执行 Lua 脚本是**原子的** (单线程执行, 不会被其他命令插进来). 用于 read-decide-write 不可分割的限流逻辑. |
| **`EVALSHA`** | 用 SHA-1 引用已加载的 Lua 脚本, 比每次 EVAL 全文重传快. |
| **`SETNX`** | "Set if Not Exists" — 不存在才设. Idempotency / lock 用. |
| **`HMSET / HMGET`** | Hash multi set/get — 一次设/取多个 hash field. (Redis 4+ 推荐 HSET 多参数). |
| **`EXPIRE`** | 给 key 设 TTL, 到点自动删. 限流里给 idle user 自动 GC. |
| **Redis Sentinel / Cluster** | Sentinel = master-replica 自动 failover; Cluster = sharded 多 master. |
| **CAS (Compare-And-Swap)** | 原子比较交换. Redis 用 WATCH/MULTI/EXEC 实现, 但 Lua 更简单. |
| **Consistent hashing (一致性哈希)** | 把 key 映射到节点的算法, 节点增减时只迁移少量 key. 限流里用于 sticky routing. |
| **Sticky routing** | 同一 user 永远落同一 instance (基于 hash). 让 in-memory 限流不在分布式下失准. |

### HTTP / API 语义

| 术语 | 解释 |
|---|---|
| **`429 Too Many Requests`** ⭐ | HTTP 状态码, 限流标准返回. |
| **`Retry-After` header** | 服务端告诉客户端 "X 秒后再试". 单位秒或 HTTP-date. Client SDK 看到 429 应尊重这个. |
| **`X-RateLimit-Limit/Remaining/Reset`** | 三件套 header — 限额 / 剩余 / 重置时刻. OpenAI/Anthropic 都返这套. |
| **Fail-open vs fail-close** ⭐ | Redis 挂时: fail-open = 放行所有请求 (好 UX 但失限流); fail-close = 拒绝所有 (安全但伤客户). 大厂多 fail-open + 告警. |
| **Clock skew** | 不同机器时钟不同步. NTP 一般在 ms 级, 但偶尔几秒. 分布式限流不能依赖各节点本地时钟. |

### 业务 / Production

| 术语 | 解释 |
|---|---|
| **RPM / TPM / RPS / QPS** | Requests Per Minute / Tokens Per Minute / Requests Per Second / Queries Per Second. Anthropic 同时跑 RPM + TPM + daily cap 三层. |
| **Hot key (热 key)** | 单个 key (e.g., 超大客户 api_key) 流量占 single Redis shard 大头, 打满该 shard. |
| **Hierarchical buckets** | 多层限流: per-key + per-org + per-tier + global capacity. 一次 atomic 检查全部. |
| **Pre-flight estimate** | 请求来了先**估**这次会用多少 token (e.g., LLM input+output), 预扣; 完成后真实 reconcile (refund or claw-back). |
| **Token (LLM 语境)** | LLM 计费单位, 不是限流的 token. 1 个英文 token ≈ 4 chars ≈ 0.75 词. 容易跟 "token bucket 的 token" 混. |
| **Tail latency (p99)** | 99 分位延迟. 限流自身延迟必须 << 用户 latency budget. Redis Lua call ~0.5-1ms. |

---

## 这道题在考什么

考的不是会不会写 token bucket — 满地都是教程. 考的是:

1. **你能不能在 5 分钟内问清楚 5 个 dimension 的 requirement** — 单机/分布式? 100ms 延迟预算? Reject vs queue? Burst tolerance? Distributed clock skew?
2. **算法选型是否对症** — 4 种主流算法各自的 trade-off 必须张口就来, 而且会主动 map 到面试官给的 requirement
3. **distributed 那一层是不是 hand-waving** — Redis Lua 是不是真懂, race condition 处理过没有, clock 不同步怎么办
4. **production-aware** — 限流 trigger 后怎么 communicate? Retry-After header, 429 vs 503, 监控 metric, fail-open vs fail-close
5. **代码能不能写出来** — token bucket 算法在白板上 15 分钟写完且能跑测试, 不要查 stackoverflow
6. **double-limiter 怎么处理** — 单用户和全局两个限制怎么 atomic 地一起 check, 既不超 user 又不超 global

Anthropic 把这题作为 final loop 的 coding round 高频问 — 因为他们自己的 Claude API 每天处理 user-level + tier-level + capacity-level 三层 rate limiting, 是他们 production 真问题.

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|------|--------|--------|
| 1 | Clarify | 0-5 min | 问 scale, latency, burst, distributed | "Before I code, let me clarify 5 things..." |
| 2 | Algorithm choice | 5-10 min | 列 4 种, 选 token bucket + 给理由 | "I see 4 candidates here; I'd pick token bucket because..." |
| 3 | Single-process impl | 10-25 min | 写 in-memory token bucket | "Let me start with single-process — we'll lift it to distributed after." |
| 4 | Double limiter | 25-30 min | check user AND global atomically | "The key invariant: never grant if either bucket is empty." |
| 5 | Test | 30-40 min | Burst, refill, denial, edge cases | "Let me run through 3 scenarios..." |
| 6 | Distributed evolution | 40-50 min | Redis + Lua atomic CAS | "For multi-instance, Redis Lua is the standard answer because..." |
| 7 | Production discussion | 50-60 min | Headers, monitoring, fail-mode | "Three production concerns: 429 communication, observability, fail-open vs close..." |
| 8 | Wrap | 59 | "Trade-off summary: ..." |

---

## 必问 clarifying questions

**1. Scope / scale**

> "How many API keys? Total QPS budget? Tail latency budget per check?"

Why: 1k users vs 1M users 决定能不能用 in-memory dict. 100 QPS vs 100k QPS 决定是不是用 lua. p99 5ms vs 50ms 决定 Redis round-trip 是否 OK.

**2. 限流单位**

> "Is it per-second, per-minute, per-day? Multiple tiers (e.g. 100/min and 1000/hour) at once?"

Why: Anthropic Claude API 同时有 RPM + TPM + daily-cap 3 个 limit, multi-tier 决定 schema 设计.

**3. Burst tolerance**

> "Should we allow a short burst above the steady rate? Or strictly cap at the limit?"

Why: 这区分了 token bucket (allow burst) 和 leaky bucket (strict) — 两种算法语义差很多.

**4. 触发后行为**

> "On limit exceeded: reject with 429, queue the request, or downgrade to a slower tier?"

Why: 决定接口语义. 默认 429 + Retry-After header.

**5. 单机 vs 分布式**

> "Single instance or multi-instance behind a load balancer? Are we OK with eventual consistency or do we need strict global limits?"

Why: 单机用 in-memory dict 就够, 分布式必上 Redis + Lua.

**6. Fail-open vs fail-close**

> "If Redis is down, do we deny all requests (safe but breaks customers) or allow all through (good UX but loses rate limit)?"

Why: 大公司一般 fail-open + 监控告警, 但安全敏感系统 fail-close.

**7. 时间精度 + clock skew**

> "Are all instances NTP-synced? Sub-second precision needed?"

Why: 分布式 token bucket 用本地时间会因 clock skew 导致 burst leak.

---

## 详细解题流程

### Step 1: Design decisions (设计决策, 5-10 min)

**算法 4 选 1**:

| 算法 | 思想 | Burst? | 内存 | Atomic? | 适合 |
|------|------|--------|------|---------|------|
| **Token bucket** | 桶里有 token, 每次消耗 1, 按 rate 补 | ✓ allow burst up to capacity | O(1) per key | ✓ easy | 默认选这个 |
| **Leaky bucket** | 请求进队列, 按固定速率漏出 | ✗ strict shaping | O(queue) | 中 | traffic shaping |
| **Fixed window counter** | 每个固定窗口 count | 在窗口边界 burst | O(1) | ✓ 最简单 | 简单粗暴 |
| **Sliding window log** | 存所有 timestamp, 查最近 N 秒数量 | 平滑 | O(N) | 复杂 | 精确但贵 |
| **Sliding window counter** | 固定窗口 + 当前窗口线性插值 | 平滑 | O(1) | 简单 | 中间方案 |

**我选 Token bucket**, 原因:

1. 容许小 burst — 用户体验好 (短时 spike 不被砍)
2. 内存 O(1) per key — 1M users × 32 bytes = 32MB 可控
3. Atomic check-and-decrement 在 Lua 里 5 行写完
4. 大多数 cloud API (AWS, GCP, Stripe, Anthropic, OpenAI) 用的就是 token bucket

**Double-limiter 怎么做**:

两个 bucket: `user_bucket(api_key)` 和 `global_bucket`. 一次 request 必须**两个都拿到 token** 才放行. **atomic invariant**: 如果其中一个失败, 另一个不能扣 (否则两个数据不一致).

```
def allow():
    with atomic:
        if user_bucket.tokens < 1 or global_bucket.tokens < 1:
            return False
        user_bucket.tokens -= 1
        global_bucket.tokens -= 1
        return True
```

### Step 2: Initial implementation (初始实现, 15-20 min)

```python
import time
import threading
from dataclasses import dataclass, field

@dataclass
class TokenBucket:
    """
    Token bucket. Refill rate is constant. Capacity = max burst size.
    """
    capacity: float        # max tokens (= max burst)
    refill_rate: float     # tokens added per second
    tokens: float = field(default=0.0)
    last_refill_ts: float = field(default_factory=time.monotonic)

    def __post_init__(self):
        # Start full so a fresh user can burst once immediately
        if self.tokens == 0:
            self.tokens = self.capacity

    def _refill(self, now: float) -> None:
        """Refill tokens based on elapsed time. Capped at capacity."""
        elapsed = max(0.0, now - self.last_refill_ts)
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill_ts = now

    def try_consume(self, n: float = 1.0) -> bool:
        """Atomically try to take n tokens. Returns True if granted."""
        now = time.monotonic()
        self._refill(now)
        if self.tokens >= n:
            self.tokens -= n
            return True
        return False


class RateLimiter:
    """
    Two-tier rate limiter:
      - Per-user bucket (configurable per api_key tier)
      - Global bucket (system-wide)

    Single-process, thread-safe via a single lock.
    """

    def __init__(self,
                 global_rate: float,       # global tokens/sec
                 global_capacity: float,   # global burst
                 default_user_rate: float, # default per-user tokens/sec
                 default_user_capacity: float):
        self.global_bucket = TokenBucket(global_capacity, global_rate)
        self.default_user_rate = default_user_rate
        self.default_user_capacity = default_user_capacity
        self.user_buckets: dict[str, TokenBucket] = {}
        self.user_tiers: dict[str, tuple[float, float]] = {}  # api_key -> (rate, cap)
        self._lock = threading.Lock()

    def set_user_tier(self, api_key: str, rate: float, capacity: float) -> None:
        """Override default rate/capacity for a specific user (e.g. paid tier)."""
        with self._lock:
            self.user_tiers[api_key] = (rate, capacity)
            # Reset bucket so new tier takes effect immediately
            if api_key in self.user_buckets:
                self.user_buckets[api_key] = TokenBucket(capacity, rate)

    def _get_user_bucket(self, api_key: str) -> TokenBucket:
        if api_key not in self.user_buckets:
            rate, cap = self.user_tiers.get(
                api_key,
                (self.default_user_rate, self.default_user_capacity)
            )
            self.user_buckets[api_key] = TokenBucket(cap, rate)
        return self.user_buckets[api_key]

    def allow(self, api_key: str, cost: float = 1.0) -> tuple[bool, str]:
        """
        Try to admit a request. Returns (allowed, reason).
        Reason on deny: 'user_limit' | 'global_limit'.
        Critical invariant: never debit one bucket if the other refuses.
        """
        with self._lock:
            user_bucket = self._get_user_bucket(api_key)
            now = time.monotonic()
            user_bucket._refill(now)
            self.global_bucket._refill(now)

            # Pre-check: both must have tokens
            if user_bucket.tokens < cost:
                return False, 'user_limit'
            if self.global_bucket.tokens < cost:
                return False, 'global_limit'

            # Commit
            user_bucket.tokens -= cost
            self.global_bucket.tokens -= cost
            return True, 'ok'

    def retry_after_seconds(self, api_key: str, cost: float = 1.0) -> float:
        """How long until the user/global bucket will have `cost` tokens."""
        with self._lock:
            user_bucket = self._get_user_bucket(api_key)
            now = time.monotonic()
            user_bucket._refill(now)
            self.global_bucket._refill(now)
            user_wait = max(0.0, (cost - user_bucket.tokens) / user_bucket.refill_rate)
            global_wait = max(0.0, (cost - self.global_bucket.tokens) / self.global_bucket.refill_rate)
            return max(user_wait, global_wait)
```

**关键设计点 (开口讲给面试官听)**:

- `time.monotonic()` 而不是 `time.time()` — monotonic 不会被 NTP 回拨, 但是 process-local
- `float` tokens 而不是 int — 因为 elapsed × rate 通常是小数, 用 float 不丢精度
- `_refill` lazy: 不用后台 thread tick, 来一个 request 才算到现在 — O(1) per call, 不会跑 worker
- `_lock` 整个 `allow()` — 单机 fine; 分布式要用 Lua

### Step 3: Edge cases + tests (边界情况和测试, 5-10 min)

```python
def test_single_user_burst():
    """Burst then drained."""
    rl = RateLimiter(
        global_rate=1000, global_capacity=1000,
        default_user_rate=10, default_user_capacity=10,
    )
    # First 10 requests should all pass (burst)
    for _ in range(10):
        ok, reason = rl.allow('alice')
        assert ok, reason
    # 11th should fail
    ok, reason = rl.allow('alice')
    assert not ok and reason == 'user_limit'


def test_user_refill():
    """After waiting, tokens should be back."""
    rl = RateLimiter(
        global_rate=1000, global_capacity=1000,
        default_user_rate=10, default_user_capacity=10,
    )
    for _ in range(10):
        assert rl.allow('alice')[0]
    assert not rl.allow('alice')[0]
    time.sleep(0.3)  # should get ~3 tokens back
    assert rl.allow('alice')[0]
    assert rl.allow('alice')[0]


def test_global_limit():
    """Many users each within their limit, but global cap kicks in."""
    rl = RateLimiter(
        global_rate=5, global_capacity=5,           # tiny global
        default_user_rate=100, default_user_capacity=100,
    )
    granted = 0
    for i in range(20):
        if rl.allow(f'user_{i}')[0]:
            granted += 1
    assert granted == 5, f'global cap broken: granted={granted}'
    # Next request should fail with global_limit
    ok, reason = rl.allow('any_user')
    assert not ok and reason == 'global_limit'


def test_user_isolation():
    """Alice's exhaustion does not affect Bob."""
    rl = RateLimiter(
        global_rate=1000, global_capacity=1000,
        default_user_rate=5, default_user_capacity=5,
    )
    for _ in range(5):
        assert rl.allow('alice')[0]
    assert not rl.allow('alice')[0]
    # Bob still fresh
    for _ in range(5):
        assert rl.allow('bob')[0]


def test_paid_tier():
    """A paid user should get higher rate."""
    rl = RateLimiter(
        global_rate=1000, global_capacity=1000,
        default_user_rate=5, default_user_capacity=5,
    )
    rl.set_user_tier('pro_user', rate=50, capacity=50)
    for _ in range(50):
        assert rl.allow('pro_user')[0]
    assert not rl.allow('pro_user')[0]


def test_invariant_atomic_double_debit():
    """If global is empty but user has tokens, user should NOT be debited."""
    rl = RateLimiter(
        global_rate=0, global_capacity=0,
        default_user_rate=100, default_user_capacity=100,
    )
    ok, reason = rl.allow('alice')
    assert not ok and reason == 'global_limit'
    # Alice should still have full tokens
    assert rl.user_buckets['alice'].tokens == 100


if __name__ == '__main__':
    test_single_user_burst()
    test_user_refill()
    test_global_limit()
    test_user_isolation()
    test_paid_tier()
    test_invariant_atomic_double_debit()
    print('All tests passed.')
```

**关键 edge cases 列出来 (说给面试官)**:

1. **First request 立即 burst** — 新 user 桶要初始 full, 不能让人冷启动等 100 秒
2. **Clock backwards** — `time.monotonic()` 保证不回拨; 但分布式得用 Redis time
3. **Atomic double-debit** — global 空时不能扣 user (易踩)
4. **High cost per call** — 一个 request 算 5 tokens (e.g., 大文档生成), 要支持 `cost` param
5. **Idle user 内存累积** — `user_buckets` 长期不清, 1M user 后内存膨胀 — LRU 或定期 GC
6. **Refill cap** — 长时间没用过, tokens 不能无限累积超过 capacity
7. **`rate=0` 或 `capacity=0`** — 全 deny
8. **Same user 并发** — single lock 串行; 分布式靠 Redis Lua atomic

### Step 4: Trade-offs + extensions (取舍与扩展, 5-10 min)

**Scale up: 分布式 Redis + Lua**

```lua
-- rate_limit.lua
-- KEYS[1] = user bucket key  (e.g. "rl:user:alice")
-- KEYS[2] = global bucket key (e.g. "rl:global")
-- ARGV[1] = now_ms
-- ARGV[2] = user_rate (tokens/sec)
-- ARGV[3] = user_capacity
-- ARGV[4] = global_rate
-- ARGV[5] = global_capacity
-- ARGV[6] = cost
-- Returns: { allowed, reason, retry_after_ms, user_tokens_left, global_tokens_left }

local user_key, global_key = KEYS[1], KEYS[2]
local now_ms      = tonumber(ARGV[1])
local user_rate   = tonumber(ARGV[2])
local user_cap    = tonumber(ARGV[3])
local global_rate = tonumber(ARGV[4])
local global_cap  = tonumber(ARGV[5])
local cost        = tonumber(ARGV[6])

-- Load user bucket
local user_data = redis.call('HMGET', user_key, 'tokens', 'last_refill_ms')
local user_tokens = tonumber(user_data[1]) or user_cap
local user_ts     = tonumber(user_data[2]) or now_ms

-- Refill user
local user_elapsed_s = (now_ms - user_ts) / 1000.0
user_tokens = math.min(user_cap, user_tokens + user_elapsed_s * user_rate)

-- Same for global
local global_data = redis.call('HMGET', global_key, 'tokens', 'last_refill_ms')
local global_tokens = tonumber(global_data[1]) or global_cap
local global_ts     = tonumber(global_data[2]) or now_ms
local global_elapsed_s = (now_ms - global_ts) / 1000.0
global_tokens = math.min(global_cap, global_tokens + global_elapsed_s * global_rate)

-- Check
if user_tokens < cost then
    -- Still persist refilled state (do NOT debit)
    redis.call('HMSET', user_key, 'tokens', user_tokens, 'last_refill_ms', now_ms)
    redis.call('EXPIRE', user_key, 3600)  -- GC idle keys
    local wait_ms = math.ceil(((cost - user_tokens) / user_rate) * 1000)
    return { 0, 'user_limit', wait_ms, user_tokens, global_tokens }
end
if global_tokens < cost then
    redis.call('HMSET', user_key, 'tokens', user_tokens, 'last_refill_ms', now_ms)
    redis.call('HMSET', global_key, 'tokens', global_tokens, 'last_refill_ms', now_ms)
    local wait_ms = math.ceil(((cost - global_tokens) / global_rate) * 1000)
    return { 0, 'global_limit', wait_ms, user_tokens, global_tokens }
end

-- Commit both
user_tokens = user_tokens - cost
global_tokens = global_tokens - cost
redis.call('HMSET', user_key, 'tokens', user_tokens, 'last_refill_ms', now_ms)
redis.call('HMSET', global_key, 'tokens', global_tokens, 'last_refill_ms', now_ms)
redis.call('EXPIRE', user_key, 3600)
return { 1, 'ok', 0, user_tokens, global_tokens }
```

**Python client**:

```python
import redis
from pathlib import Path

class DistributedRateLimiter:
    def __init__(self, redis_client: redis.Redis, script_path: str):
        self.r = redis_client
        # Load Lua once, get SHA for EVALSHA (avoid re-shipping script every call)
        with open(script_path) as f:
            self.script_sha = self.r.script_load(f.read())

    def allow(self, api_key: str, cost: float = 1.0,
              user_rate: float = 100, user_cap: float = 100,
              global_rate: float = 10000, global_cap: float = 10000):
        now_ms = int(time.time() * 1000)
        result = self.r.evalsha(
            self.script_sha,
            2,                                   # numkeys
            f'rl:user:{api_key}', 'rl:global',  # KEYS
            now_ms, user_rate, user_cap,        # ARGV
            global_rate, global_cap, cost,
        )
        allowed, reason, retry_ms, user_left, global_left = result
        return {
            'allowed': bool(allowed),
            'reason': reason.decode() if isinstance(reason, bytes) else reason,
            'retry_after_ms': retry_ms,
            'user_tokens': float(user_left),
            'global_tokens': float(global_left),
        }
```

**为什么 Lua**:

- Redis Lua runs **atomically** — no two clients can interleave the read-decide-write
- One round-trip → tail latency 同 1 个 GET
- 服务端时钟统一 (Redis 节点的 wall clock, 避免每个 app instance clock skew)

**Fail-open vs fail-close**:

```python
def allow_with_fallback(self, api_key: str):
    try:
        return self._redis_check(api_key)
    except redis.RedisError:
        metric_counter('rate_limit.fallback').inc()
        if FAIL_OPEN:
            return {'allowed': True, 'reason': 'fallback_open'}
        return {'allowed': False, 'reason': 'fallback_close'}
```

**Hierarchical buckets** (Anthropic 真实需求):

```
- Per-API-key bucket (RPM)
- Per-organization bucket (sum across all keys in org)
- Per-tier bucket (free vs pro vs enterprise capacity)
- Global capacity bucket (model GPU budget)
```

Lua 接受 `KEYS[1..N]` 然后一次检查所有 bucket, 同样的 atomic invariant.

---

## 完整代码 (Production-ready)

完整可运行的单机版 + Redis-Lua 版已在 Step 2 / Step 4. 把单机版搁这里再贴一次, 完整 self-contained:

```python
"""
Rate limiter — single-process token bucket with per-user + global cap.
Run: python rate_limiter.py
"""
import time
import threading
from dataclasses import dataclass, field


@dataclass
class TokenBucket:
    capacity: float
    refill_rate: float
    tokens: float = 0.0
    last_refill_ts: float = field(default_factory=time.monotonic)

    def __post_init__(self):
        if self.tokens == 0:
            self.tokens = self.capacity

    def _refill(self, now: float) -> None:
        elapsed = max(0.0, now - self.last_refill_ts)
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill_ts = now


class RateLimiter:
    def __init__(self,
                 global_rate: float, global_capacity: float,
                 default_user_rate: float, default_user_capacity: float):
        self.global_bucket = TokenBucket(global_capacity, global_rate)
        self.default_user_rate = default_user_rate
        self.default_user_capacity = default_user_capacity
        self.user_buckets: dict[str, TokenBucket] = {}
        self.user_tiers: dict[str, tuple[float, float]] = {}
        self._lock = threading.Lock()

    def set_user_tier(self, api_key: str, rate: float, capacity: float) -> None:
        with self._lock:
            self.user_tiers[api_key] = (rate, capacity)
            self.user_buckets[api_key] = TokenBucket(capacity, rate)

    def _get_user_bucket(self, api_key: str) -> TokenBucket:
        if api_key not in self.user_buckets:
            rate, cap = self.user_tiers.get(
                api_key,
                (self.default_user_rate, self.default_user_capacity)
            )
            self.user_buckets[api_key] = TokenBucket(cap, rate)
        return self.user_buckets[api_key]

    def allow(self, api_key: str, cost: float = 1.0) -> tuple[bool, str]:
        with self._lock:
            ub = self._get_user_bucket(api_key)
            now = time.monotonic()
            ub._refill(now)
            self.global_bucket._refill(now)
            if ub.tokens < cost:
                return False, 'user_limit'
            if self.global_bucket.tokens < cost:
                return False, 'global_limit'
            ub.tokens -= cost
            self.global_bucket.tokens -= cost
            return True, 'ok'

    def retry_after_seconds(self, api_key: str, cost: float = 1.0) -> float:
        with self._lock:
            ub = self._get_user_bucket(api_key)
            now = time.monotonic()
            ub._refill(now)
            self.global_bucket._refill(now)
            uw = max(0.0, (cost - ub.tokens) / ub.refill_rate)
            gw = max(0.0, (cost - self.global_bucket.tokens) / self.global_bucket.refill_rate)
            return max(uw, gw)

    def gc_idle_users(self, idle_seconds: float = 3600) -> int:
        """Periodically called to evict idle users. Returns count evicted."""
        with self._lock:
            now = time.monotonic()
            cutoff = now - idle_seconds
            removed = [k for k, b in self.user_buckets.items()
                       if b.last_refill_ts < cutoff and b.tokens >= b.capacity]
            for k in removed:
                del self.user_buckets[k]
            return len(removed)


# ---- Tests ----
def _run_tests():
    rl = RateLimiter(global_rate=1000, global_capacity=1000,
                     default_user_rate=10, default_user_capacity=10)
    for _ in range(10):
        assert rl.allow('alice')[0]
    assert rl.allow('alice') == (False, 'user_limit')

    # Refill
    time.sleep(0.5)
    assert rl.allow('alice')[0]

    # Global limit
    rl2 = RateLimiter(5, 5, 100, 100)
    granted = sum(1 for i in range(20) if rl2.allow(f'u{i}')[0])
    assert granted == 5

    # Atomic invariant
    rl3 = RateLimiter(0, 0, 100, 100)
    ok, reason = rl3.allow('alice')
    assert not ok and reason == 'global_limit'
    assert rl3.user_buckets['alice'].tokens == 100  # not debited

    print('All tests passed.')


if __name__ == '__main__':
    _run_tests()
```

---

## 复杂度分析

| 操作 | Time | Space |
|------|------|-------|
| `allow()` (single-proc) | O(1) — refill + 2 compares + 2 subs | O(1) per active user |
| `allow()` (Redis Lua) | O(1) Lua + 1 RTT (~0.5ms intra-AZ) | O(N users) Redis memory |
| `gc_idle_users()` | O(U) where U = active users | — |
| Memory per user (in-proc) | ~80 bytes (dataclass + float fields) | 1M users ≈ 80MB |
| Memory per user (Redis) | ~50 bytes hash | 1M users ≈ 50MB |

**热点路径** 是 `allow()`. 单机大约 200ns/call (有 lock), Redis 大约 0.5–1ms (within DC).

---

## Gao Xin 简历专属 reframe

把这套限流框架 map 到我做过的:

- **Voice agent (7 markets)**: 我们对 outbound call API 有 per-tenant rate limit (每个市场 BNPL 每分钟最大 outbound 数量), 也有 vLLM/SGLang inference cluster 的全局 capacity (GPU 数 × throughput). 我用过类似的 token bucket pattern, 但 backend 是 Anyscale Ray 的 priority queue 而不是 Redis Lua.
- **BNPL chatbot (RAG + intent routing)**: 用户级 rate limit 防 abuse (一个 user 1 min 不能问 100 次), 全局级 cap 防 model API 账单失控. 我们 fail-open 但发 PagerDuty.
- **Internal Agent Platform**: 多 team 共享 inference cluster, 我加过 quota 系统 (per-team daily-cap + per-job rate cap), 跟这题双层一模一样.
- **ConvFinQA**: 不直接相关, 但 9-variant ablation 跑实验时, 我们对 LLM API 也有自己的 client-side rate limit (sliding window log on local file).
- **TikTok PayLater**: 风控决策 API 对内部调用方有 RPS cap, 用 Redis token bucket — 我做的 Indonesia refund tier 是 caller.

**面试时一句话**: "I've shipped this exact pattern at TikTok — a Redis-Lua based two-tier limiter for our inference cluster. The global cap protects GPU budget, the per-tenant cap protects fairness."

---

## 5 个 Follow-ups

**Q1**: "现在系统跑在 10 个 instance 后面 LB, in-memory token bucket 会怎么样?"

A: 每个 instance 各自维护 bucket, 实际限流 = `nominal × 10`. 三个修法:
1. **Sticky routing** by api_key (一致性 hash) — 同 user 永远落同 instance, 单机限流就准. Drawback: instance 故障 / scale-out 后 hash 重映射会丢 bucket state.
2. **Redis 中央化** — 上 Lua 那个方案, 强一致但延迟 +0.5ms.
3. **Approximate distributed** — 每个 instance 维护 1/N rate, 接受 ±N 倍误差. 大流量场景常用.

**Q2**: "Redis 这台机器挂了, 怎么办?"

A: Fail-open + replica failover. 具体:
- Redis Sentinel / Cluster 自动 failover, downtime ~5s
- App 侧设 200ms timeout (避免 redis 慢拖垮 app)
- timeout / connection error → log + counter, default allow (fail-open) — 这是大公司主流, 防止 Redis 故障 cascade 拖垮整个 API
- 若 fail-close, 设很短 grace period (5 min) 然后告警

**Q3**: "Daily / Weekly quota 怎么加 (e.g., free tier 1M tokens/month)?"

A: 加 fixed-window counter 跟 token bucket 并存. Lua 里多一行:
```lua
local daily_used = redis.call('INCRBY', 'rl:daily:'..api_key, cost)
if daily_used > daily_cap then
    return { 0, 'daily_limit', ... }
end
-- 设 EXPIRE 至今天结束 UTC
```
Trade-off: fixed window 有"jan-31 23:59 + feb-01 00:01 双倍 burst", 但 daily quota 场景一般不在乎.

**Q4**: "如果 user 真的把 burst 用完, 怎么 communicate 给他?"

A: HTTP 标准:
- Status `429 Too Many Requests`
- Header `Retry-After: 30` (seconds)
- Header `X-RateLimit-Limit: 100`, `X-RateLimit-Remaining: 0`, `X-RateLimit-Reset: 1716120000`
- Body JSON: `{"error": {"type": "rate_limit_error", "message": "...", "retry_after_ms": 30000}}`

OpenAI / Anthropic API 都这套. SDK 看到 429 自动 exponential-backoff retry.

**Q5**: "Token bucket vs sliding window log 你怎么选?"

A: Token bucket allow controlled burst, 实现简单 O(1) memory; sliding window log 完全准 (任意 window 都精确) 但 O(N) memory per user, 不适合 1M user × 高 QPS. **生产: token bucket + 监控 burst pattern**. 真要超精确就 sliding window counter (混合方案), 精度 ±5% 但 O(1) memory.

---

## 死路答法

**1. 直接 while True polling 等 refill** — 上来就写 `while not allow(): time.sleep(0.1)`, 这是 client 行为不是 limiter 行为. Limiter 只 yes/no, 不该 block.

**2. 没考虑 atomic invariant** — global 空但 user 有 token, 然后扣了 user 但 global 没扣 → 用户白被扣 token, fairness 破坏.

**3. 单 dict 没 lock** — Python GIL 救一部分但 refill 涉及 `last_refill_ts` 读写 + tokens 计算, 多线程下 race.

**4. 直接 `time.time()` 不 monotonic** — NTP 回调一次 limiter 错乱; 用 `time.monotonic()` 才对单机 OK.

**5. 没 `EXPIRE` Redis key** — 不活跃 user 的 hash 永远在 Redis 里, 1 年累积内存炸. 每次 `HMSET` 后 `EXPIRE 3600`.

**6. Lua 写一半再 GET 一遍** — Lua 已经 atomic, 不需要外面再 `WATCH`. 反例: app 先 `GET tokens`, 比较, 再 `SET` — 经典 race condition.

**7. Hand-wavy distributed** — 面试官问"分布式怎么搞", 答"用 Redis" 但不写 Lua 是没答到位.

---

## 加分项

**Production gotchas (说给面试官加分)**:

- **Hot key**: 一个超大客户的 api_key 把 Redis 单 shard 打满 — 解法: 给 hot user 单独 shard, 或 client-side bucket (in-proc per app) + 异步报告给 redis (eventually consistent)
- **Time skew in Lua**: 在 lua 里用 `redis.call('TIME')` 而非 client-passed `now_ms`, 避免 client clock 不同
- **Cost ≠ 1**: API tokens (LLM) 时 cost = `input_tokens + output_tokens × 4`, lua 要支持 float cost
- **Pre-flight estimate**: Anthropic 真做的 — request 来了根据 model 估 token cost, 用估值预扣, 真实完成后 reconcile (refund or claw-back)
- **Multi-tier (tiered cap)**: free user 60/min, pro 600/min, enterprise unlimited — 用 `user_tiers` map, lua 接受 dynamic rate/cap 参数
- **Bursty user warning**: 监控 burst 用尽 in 10s 的 user, log + alert + 营销机会 (upsell to higher tier)
- **Telemetry**: emit metric `rate_limit.granted`, `rate_limit.denied.user`, `rate_limit.denied.global`, `rate_limit.tokens_remaining` 分位数
- **Graceful degradation**: when global cap 90% used, downgrade response quality (e.g., smaller model) instead of 429

---

## 一句话总结

> **Token bucket per-user + token bucket global, 两个 atomic check, 单机 thread-lock 分布式 Redis Lua.**
>
> 核心 invariant: **never debit either bucket if either would be insufficient.**

---

## Cheat Sheet

```python
# Algorithm: Token Bucket
# State per bucket: { capacity, refill_rate, tokens, last_refill_ts }

def refill(bucket, now):
    elapsed = now - bucket.last_refill_ts
    bucket.tokens = min(bucket.capacity, bucket.tokens + elapsed * bucket.refill_rate)
    bucket.last_refill_ts = now

def try_consume(bucket, cost, now):
    refill(bucket, now)
    if bucket.tokens >= cost:
        bucket.tokens -= cost
        return True
    return False

# Double limiter
def allow(api_key, cost):
    refill both, check both, debit both — ATOMIC
    if either fails, debit NONE

# Distributed:
#   Redis HASH per bucket: HMGET/HMSET tokens, last_refill_ms
#   Single Lua script for atomic check-and-debit
#   EXPIRE 3600 to GC idle users
#   evalsha for low latency

# Edge cases checklist:
#   - First request: bucket starts FULL
#   - Time backwards: use time.monotonic() / Redis TIME
#   - Atomic invariant: NEVER debit one if other would fail
#   - Idle GC: cleanup buckets unused > 1h
#   - Cost > 1: support float / int cost param
#   - rate=0: degenerate but should not crash
#   - 429 communication: Retry-After + X-RateLimit-* headers
```

**Big-O**: `allow()` O(1) per call. Memory O(active_users).

**Fail mode**: fail-open by default (log + metric), fail-close for sensitive endpoints.

**Anthropic / OpenAI real pattern**: per-key RPM + per-key TPM + per-org daily-cap + global GPU-capacity bucket = 4 buckets check atomically.
