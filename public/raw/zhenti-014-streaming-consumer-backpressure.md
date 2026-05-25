## Q14 · 处理下游变慢时 backpressure 的流式消费者

> "You're consuming messages from a stream (e.g. Kafka / Redis Streams). For each message you call a **slow downstream API** (e.g. an LLM). If the downstream gets even slower or errors, you must **apply backpressure** rather than blow up memory. Code it in asyncio. Explain how backpressure propagates."

**Round**: Coding (60 min)
**出处**: Exponent 2026 FDE · 公司: **Anthropic**, OpenAI, Scale AI, Anyscale
**难度**: Hard
**主要技能**: asyncio, queue, concurrency, latency budget, robustness

---

## 📖 术语速查 (本题用到的)

> 流式系统满地术语. 这张表 5 min 扫完, 后面 backpressure / DLQ / circuit breaker 全跟得上.

### 流式系统核心概念

| 术语 | 解释 |
|---|---|
| **Backpressure (背压)** ⭐ | 下游慢时, **上游主动停 pull**, 不要继续 buffer. 防 OOM. 这题核心. 来自 reactive streams / Akka / Flink. |
| **Producer / Consumer (生产/消费)** | 生产者从 source 取消息, 消费者处理. 中间用 queue 解耦. |
| **Bounded queue (有界队列)** ⭐ | 容量上限的 queue. 满了 `put()` block — backpressure 自然 propagate. |
| **Little's Law** ⭐ | `throughput × latency = in-flight`. 100 msg/s × 200ms = 20 并发. **决定 workers 数**. |
| **In-flight count** | 当前正在处理 (从 queue 取出但未完成) 的 message 数. |
| **Lag (消费滞后)** | Kafka 中 `high_water_mark - committed_offset`. Lag 涨 = consumer 跟不上. |
| **Partition (分区)** | Kafka topic 的物理分片单位. 一个 partition 串行, 多个 partition 并行. |

### 投递语义 (delivery semantics)

| 术语 | 解释 |
|---|---|
| **At-least-once** ⭐ | 至少投一次, 可能重复. **Default** + 要求 downstream idempotent. |
| **Exactly-once** | 严格一次. Kafka 有 EOS (transactional), 但 downstream 不是 Kafka 时很难. |
| **At-most-once** | 至多一次, 可能丢. fire-and-forget 场景 (e.g., metrics). |
| **Idempotent downstream** | 同 message 多次处理结果相同. 用 SETNX(msg_id) 实现 dedupe. |
| **Outbox pattern** | 处理结果先写 outbox 表 (with msg_id), 单独 worker poll outbox → side effect. Transactional 保证. |

### asyncio / 并发原语

| 术语 | 解释 |
|---|---|
| **`asyncio`** ⭐ | Python 异步 IO 框架. 单线程 + event loop + coroutine. |
| **`asyncio.Queue(maxsize=K)`** ⭐ | 异步队列. 满时 `await q.put()` block — backpressure 入口. |
| **`asyncio.Semaphore(N)`** | 限并发 N 个. 跟 queue 不同: queue 限 buffer 容量, semaphore 限并发. |
| **`asyncio.Event`** | 多 task 协调用 flag. `event.set()` 通知所有等的 task. shutdown 信号常用. |
| **`asyncio.create_task`** | 启动一个并发 task (不 block 当前). |
| **`asyncio.wait_for(coro, timeout)`** | 给 coroutine 加 timeout. 防 worker 卡在 `q.get()` 不响应 shutdown. |
| **`asyncio.gather`** | 等多个 task 全部完成. 但**unbounded gather 就是 OOM 元凶**. |
| **`asyncio.CancelledError`** | task 被 cancel 时抛的异常. 必须 propagate, 不能吞. |
| **`task_done()` + `queue.join()`** ⭐ | task_done() 标记一条消息完成; queue.join() 等所有 in-flight 完成. 漏 task_done() 会让 join 永远 hang. |
| **`asyncio.iscoroutinefunction`** | 检查 fn 是不是 `async def` 定义的. 用来写既支持 sync 又支持 async 的 decorator. |
| **Event loop** | asyncio 的核心 — 单线程跑所有 coroutine. `time.sleep()` 会**阻塞它**, 必须用 `asyncio.sleep()`. |
| **Coroutine** | `async def` 函数返回的对象. 必须 `await` 才执行. |

### 错误处理 / 健壮性

| 术语 | 解释 |
|---|---|
| **Retry with backoff** | 失败后重试, 间隔指数增长. 详见 Q16. |
| **Exponential backoff + jitter** | 间隔 = `base * 2^n + random`. 防 thundering herd. |
| **Full jitter** | `random.uniform(0, base * 2^n)`. AWS 推荐. |
| **Circuit breaker (熔断器)** ⭐ | N 错误 in 窗口 → open → 一段时间内直接 reject 不试 → cooldown 后 half-open 探测. 防 cascading failure. |
| **DLQ (Dead Letter Queue)** ⭐ | 死信队列. 重试穷尽的消息丢这里, 离线分析 + 手动 replay. |
| **Poison message** | 总是 fail 的消息 (e.g., schema 不合规). 卡 partition 不 ack 就死循环 — 必须 DLQ + ack. |
| **Cascading failure** | 一个慢/挂的下游让上游堆积, 上游又拖更上游, 雪崩. backpressure + breaker 防这个. |
| **Thundering herd** | 大量 client 同时 fail 同时 retry → 第二波 spike 又挂. |

### Production / 部署

| 术语 | 解释 |
|---|---|
| **Graceful shutdown** ⭐ | 收 SIGTERM 后: 停止 pull → drain in-flight → ack → exit. 不丢消息. |
| **SIGTERM / SIGINT** | Unix 信号. SIGTERM = 优雅停 (K8s 默认), SIGINT = Ctrl+C. SIGKILL 无法捕获. |
| **K8s `preStop` hook** | Pod 被终止前的最后机会. 30s grace 期发 SIGTERM. |
| **K8s `readinessProbe`** | 健康检查 - 不 ready 时 LB 不送流量. 满 queue 时返回 not ready 是常用手段. |
| **HPA (Horizontal Pod Autoscaler)** | K8s 按指标 (CPU / queue depth) 自动扩容. |
| **Hedged request** | "Tail at Scale" paper — p95 时同时发备份请求, 取先返的. 牺牲 cost 换 tail latency. |
| **Replay tool** | 从 DLQ 重投失败的消息. Production 必备. |

### Kafka / 上下游具体

| 术语 | 解释 |
|---|---|
| **Kafka offset** | 每条消息在 partition 的位置. consumer 提交 offset 表示已处理. |
| **Consumer group** | 一组 consumer 共享 topic. Kafka 把 partition 均匀分到 group 内. |
| **Kafka EOS (Exactly-Once Semantics)** | Transactional producer + transactional offset commit. Hard 但可能. |
| **Redis Streams** | Redis 5.0+ 的流式 data structure, 比 Kafka 轻. `XADD` 写, `XREAD` 读. |
| **AIOKafka / aiokafka** | Python asyncio 版 Kafka client. 替代 sync `kafka-python`. |
| **`httpx.AsyncClient`** | asyncio HTTP client. 替代 sync `requests`. |

---

## 这道题在考什么

这道题考你**懂不懂流式系统**, 不是"会不会 async":

1. **Backpressure 概念** — 当下游慢, 上游必须**停止 pull** 而不是 buffer 无限. 这是 reactive streams / Akka / Flink 的核心
2. **`asyncio.Queue` 的 `maxsize` 语义** — `await q.put()` 在 full 时 block, 这就是 backpressure 入口
3. **Semaphore vs Queue 区别** — Semaphore 限并发, Queue 限 buffer 容量, 一般要**同时用**
4. **优雅停机** — 上游 EOF 或 SIGTERM 时, 排空 queue, drain in-flight, 不丢消息
5. **错误处理** — 一条消息 fail 不应该 kill consumer; retry / DLQ / circuit breaker
6. **观测** — lag (queue depth), p99 latency, in-flight count, RPS — 没这些就不算 production
7. **资源约束** — 内存上限 / CPU / 网络 — 都用 Semaphore + Queue 表达

Anthropic 这个题超高频, 因为他们 Claude API rollout 经常碰到: 客户 burst → consumer 慢 → consumer OOM → 雪崩.

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|------|--------|--------|
| 1 | Clarify | 0-5 min | 上游什么, 下游什么, lag budget, at-least-once 还是 exactly-once | "Before I code, 5 things..." |
| 2 | Architecture sketch | 5-10 min | 三层 producer / queue / N consumer | "Three components: source, buffer, workers." |
| 3 | Basic skeleton | 10-20 min | `asyncio.Queue` + N workers | "Let me write the skeleton, then we'll harden." |
| 4 | Backpressure propagation | 20-30 min | `await q.put()` blocks → producer pauses | "Backpressure here means producer stops when queue full." |
| 5 | Error + retry | 30-40 min | per-message try/except + retry + DLQ | "Each message gets up to N retries with backoff." |
| 6 | Graceful shutdown | 40-50 min | sigterm → stop pulling → drain | "On signal: cancel producer, await workers, drain queue." |
| 7 | Observability | 50-55 min | emit metrics every second | "Three metrics that matter: lag, in-flight, RPS." |
| 8 | Discuss | 55-60 min | scaling, tuning, partition, exactly-once | "Trade-offs..." |

---

## 必问 clarifying questions

**1. Source + sink semantics**

> "What's upstream — Kafka, Redis Streams, an HTTP poll? What's downstream — a single API, multiple APIs, GPU inference cluster?"

Why: Kafka has consumer groups + offset commit semantics; Redis Streams has XADD / XREAD; HTTP poll is simpler. Downstream affects 并发 / rate-limit posture.

**2. At-least-once / exactly-once?**

> "OK to process a message twice in failure case, or strict exactly-once?"

Why: at-least-once 是 default + idempotent downstream; exactly-once 要 transactional commit (Kafka EOS).

**3. Latency budget**

> "p99 budget per message? p99 lag we can tolerate?"

Why: 决定 queue size + workers + retry strategy.

**4. Volume + concurrency**

> "Avg / peak msg/sec? Avg downstream latency? Burst tolerance?"

Why: workers = throughput × latency = little's law.

**5. Failure mode**

> "On downstream 500s: retry forever? DLQ after N? Circuit breaker?"

Why: retry forever 会 cascade; DLQ + alert 是 production 主流.

**6. Order**

> "Per-partition ordering matters? Or out-of-order OK?"

Why: 并发 worker 会乱序 — 若必 ordered 只能 1 worker per partition.

**7. Memory cap**

> "Hard memory limit? Per-message size?"

Why: queue size × msg size = memory; 必算清楚.

---

## 详细解题流程

### Step 1: Design decisions (5-10 min)

**Architecture**:

```
┌──────────┐     ┌──────────────┐     ┌────────────┐
│ Producer │ →→  │ asyncio.Queue│ →→  │ N workers  │
│ (source) │     │ maxsize=K    │     │ (calls API)│
└──────────┘     └──────────────┘     └────────────┘
   pull /              │                    │
   poll Kafka          │                    │
                       ▼                    ▼
              backpressure if         downstream slow → 
              queue is full           q.put() blocks producer
                                       ↑ producer pauses
                                       ↑ no more pull from source

Plus:
- asyncio.Semaphore(N) inside workers if downstream has its own concurrency cap
- shutdown_event for graceful stop
- DLQ for poison messages
- Metrics task emits every 1s
```

**关键 invariant**: 
- Queue 是 **唯一** 的 buffer. 不能在 worker 里再开 buffer.
- Backpressure 通过 `await q.put()` block 自然传递到 producer
- Producer 在 block 时**停止 pull**, 这样 source 端 (Kafka) 看到 consumer 没新 commit, 会让 partition lag 涨, 但**不会 OOM**
- 满 queue → 慢 producer → Kafka 自动 keep messages → 系统自我保护

**`asyncio.Queue` 关键参数**: `maxsize=K`. K = 你能承受的 buffered 消息数. 一般 K = workers × 2.

**Worker 并发**: `N` 个 worker task, 每个 `while True: msg = await q.get(); process(msg); q.task_done()`.

**Backoff retry**:
```python
for attempt in range(MAX_RETRIES + 1):
    try:
        return await downstream(msg)
    except RetriableError:
        if attempt == MAX_RETRIES:
            await dlq.send(msg, reason='max_retries')
            return
        sleep = min(BASE * 2 ** attempt + random_jitter, MAX_BACKOFF)
        await asyncio.sleep(sleep)
```

### Step 2: Initial implementation (15-20 min)

```python
"""
Streaming consumer with backpressure.
- asyncio.Queue maxsize: hard memory cap
- N worker tasks: bounded concurrency
- Graceful shutdown via signal / explicit event
- Per-message retry + DLQ + circuit breaker
- Observability: lag, in-flight, processed, errors
"""
import asyncio
import logging
import random
import signal
import time
from dataclasses import dataclass, field
from typing import AsyncIterator, Awaitable, Callable, Optional

log = logging.getLogger('consumer')


# ============ Errors ============

class RetriableError(Exception):
    """Downstream failed transiently — retry."""


class FatalError(Exception):
    """Bad message — do not retry, send to DLQ."""


# ============ Config ============

@dataclass
class ConsumerConfig:
    queue_size: int = 200           # Max in-flight + buffered
    num_workers: int = 16           # Parallel downstream calls
    max_retries: int = 3
    base_backoff_s: float = 0.5
    max_backoff_s: float = 10.0
    metrics_interval_s: float = 1.0
    shutdown_timeout_s: float = 30.0  # max wait at shutdown to drain
    # Circuit breaker
    error_window_s: float = 30.0
    error_threshold: int = 50       # if >= N errors in window, open breaker
    breaker_cooldown_s: float = 30.0


# ============ Metrics ============

@dataclass
class Metrics:
    processed: int = 0
    failed: int = 0
    retried: int = 0
    sent_to_dlq: int = 0
    in_flight: int = 0
    started_at: float = field(default_factory=time.monotonic)

    def snapshot(self, queue_depth: int) -> dict:
        elapsed = time.monotonic() - self.started_at
        return {
            'processed': self.processed,
            'failed': self.failed,
            'retried': self.retried,
            'dlq': self.sent_to_dlq,
            'in_flight': self.in_flight,
            'queue_depth': queue_depth,
            'rps': round(self.processed / elapsed, 2) if elapsed > 0 else 0,
            'elapsed_s': round(elapsed, 1),
        }


# ============ Circuit breaker ============

class ErrorWindowCircuitBreaker:
    """Open after N errors within window_s. Cooldown then half-open."""
    def __init__(self, threshold: int, window_s: float, cooldown_s: float):
        self.threshold = threshold
        self.window_s = window_s
        self.cooldown_s = cooldown_s
        self.errors: list[float] = []
        self.open_until: float = 0.0

    def record_error(self) -> None:
        now = time.monotonic()
        self.errors.append(now)
        # Evict old
        cutoff = now - self.window_s
        while self.errors and self.errors[0] < cutoff:
            self.errors.pop(0)
        if len(self.errors) >= self.threshold:
            self.open_until = now + self.cooldown_s
            log.warning('Circuit breaker OPEN until %s', self.open_until)
            self.errors.clear()

    def record_success(self) -> None:
        pass  # success doesn't close breaker eagerly; let cooldown decide

    @property
    def is_open(self) -> bool:
        return time.monotonic() < self.open_until


# ============ Consumer ============

class StreamingConsumer:
    def __init__(
        self,
        config: ConsumerConfig,
        # Producer: async generator yielding (message_id, message_body)
        source: Callable[[asyncio.Event], AsyncIterator[tuple[str, bytes]]],
        # Sink: async callable invoking downstream API
        sink: Callable[[bytes], Awaitable[None]],
        # Commit offset back to source (e.g., Kafka commit)
        ack: Callable[[str], Awaitable[None]],
        # Dead letter sink
        dlq: Optional[Callable[[str, bytes, str], Awaitable[None]]] = None,
    ):
        self.config = config
        self.source = source
        self.sink = sink
        self.ack = ack
        self.dlq = dlq or (lambda mid, body, reason: asyncio.sleep(0))
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=config.queue_size)
        self.shutdown_event = asyncio.Event()
        self.metrics = Metrics()
        self.breaker = ErrorWindowCircuitBreaker(
            threshold=config.error_threshold,
            window_s=config.error_window_s,
            cooldown_s=config.breaker_cooldown_s,
        )

    async def producer_task(self) -> None:
        """Pull from source. await q.put() blocks when full = backpressure."""
        try:
            async for mid, body in self.source(self.shutdown_event):
                if self.shutdown_event.is_set():
                    log.info('shutdown set; producer stopping')
                    break
                # If circuit breaker is open, wait — don't pull more
                while self.breaker.is_open and not self.shutdown_event.is_set():
                    log.info('breaker open, producer pausing')
                    await asyncio.sleep(1.0)
                # THIS IS BACKPRESSURE: queue full → block here → source pause
                await self.queue.put((mid, body))
        except asyncio.CancelledError:
            log.info('producer cancelled')
            raise
        except Exception:
            log.exception('producer crashed')
            self.shutdown_event.set()
            raise
        finally:
            log.info('producer ended')

    async def worker_task(self, worker_id: int) -> None:
        """Consume from queue, call sink with retry."""
        while True:
            try:
                mid, body = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                # Empty queue + shutdown → exit
                if self.shutdown_event.is_set():
                    log.info('worker %d exiting (queue empty)', worker_id)
                    return
                continue
            self.metrics.in_flight += 1
            try:
                await self._process_with_retry(mid, body)
            finally:
                self.metrics.in_flight -= 1
                self.queue.task_done()

    async def _process_with_retry(self, mid: str, body: bytes) -> None:
        for attempt in range(self.config.max_retries + 1):
            try:
                await self.sink(body)
                self.metrics.processed += 1
                self.breaker.record_success()
                await self.ack(mid)
                return
            except FatalError as e:
                log.warning('fatal on %s: %s', mid, e)
                self.metrics.failed += 1
                self.metrics.sent_to_dlq += 1
                await self.dlq(mid, body, f'fatal: {e}')
                await self.ack(mid)  # ack so source doesn't redeliver
                return
            except RetriableError as e:
                self.breaker.record_error()
                if attempt == self.config.max_retries:
                    log.warning('exhausted retries for %s', mid)
                    self.metrics.failed += 1
                    self.metrics.sent_to_dlq += 1
                    await self.dlq(mid, body, f'max_retries: {e}')
                    await self.ack(mid)
                    return
                # Backoff with jitter
                backoff = min(
                    self.config.base_backoff_s * (2 ** attempt),
                    self.config.max_backoff_s,
                )
                jitter = random.uniform(0, backoff)  # full jitter
                self.metrics.retried += 1
                await asyncio.sleep(jitter)
            except Exception as e:
                # Unknown — treat as fatal but log
                log.exception('unknown error on %s', mid)
                self.metrics.failed += 1
                self.metrics.sent_to_dlq += 1
                await self.dlq(mid, body, f'unknown: {e!r}')
                await self.ack(mid)
                return

    async def metrics_task(self) -> None:
        while not self.shutdown_event.is_set():
            await asyncio.sleep(self.config.metrics_interval_s)
            snap = self.metrics.snapshot(self.queue.qsize())
            log.info('METRICS %s', snap)

    async def run(self) -> dict:
        """Run until source exhausted or signaled. Returns final metrics."""
        self._install_signal_handlers()
        log.info('starting %d workers, queue_size=%d',
                 self.config.num_workers, self.config.queue_size)

        producer = asyncio.create_task(self.producer_task(), name='producer')
        workers = [
            asyncio.create_task(self.worker_task(i), name=f'worker-{i}')
            for i in range(self.config.num_workers)
        ]
        metrics = asyncio.create_task(self.metrics_task(), name='metrics')

        try:
            await producer
            log.info('producer finished; draining queue')
            # Wait for queue to drain (graceful)
            try:
                await asyncio.wait_for(
                    self.queue.join(),
                    timeout=self.config.shutdown_timeout_s,
                )
            except asyncio.TimeoutError:
                log.warning('drain timeout; %d items unprocessed', self.queue.qsize())
        finally:
            # Signal workers to exit
            self.shutdown_event.set()
            for w in workers:
                w.cancel()
            metrics.cancel()
            await asyncio.gather(*workers, metrics, return_exceptions=True)

        final = self.metrics.snapshot(self.queue.qsize())
        log.info('final %s', final)
        return final

    def _install_signal_handlers(self) -> None:
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, self._on_signal)
            except NotImplementedError:
                pass  # Windows

    def _on_signal(self) -> None:
        log.info('signal received, initiating graceful shutdown')
        self.shutdown_event.set()
```

**讲给面试官的关键点**:

1. **`maxsize=K` on Queue → 满了 `await q.put()` block → producer 停 pull → 自然 backpressure**
2. **`task_done()` + `q.join()`**: 让 graceful shutdown 等所有 in-flight 完成
3. **`asyncio.Event` for shutdown signal**: 多个 task 协调干净
4. **Worker timeout in `q.get`**: 避免 worker stuck wait queue 而不响应 shutdown
5. **Circuit breaker**: 上游告诉 producer "pause", 防 cascade
6. **DLQ + ack**: 哪怕 fail 也 ack, 避免 source 永远重投 poison

### Step 3: Edge cases + tests (5-10 min)

```python
import asyncio
import time
import unittest
from unittest.mock import MagicMock

# Module being tested: consumer (above code)


async def fake_source(shutdown: asyncio.Event, count: int = 100, delay: float = 0.0):
    for i in range(count):
        if shutdown.is_set():
            return
        if delay:
            await asyncio.sleep(delay)
        yield f'msg-{i}', f'body-{i}'.encode()


class FastSink:
    def __init__(self):
        self.calls = []

    async def __call__(self, body: bytes):
        self.calls.append(body)


class SlowSink:
    def __init__(self, latency_s: float):
        self.latency = latency_s
        self.calls = []

    async def __call__(self, body: bytes):
        await asyncio.sleep(self.latency)
        self.calls.append(body)


class FailingSink:
    def __init__(self, fail_n: int):
        self.fail_n = fail_n
        self.calls = 0
        self.successes = 0

    async def __call__(self, body: bytes):
        self.calls += 1
        if self.calls <= self.fail_n:
            raise RetriableError(f'fail attempt {self.calls}')
        self.successes += 1


def noop_ack():
    acks = []
    async def _ack(mid):
        acks.append(mid)
    return acks, _ack


def collecting_dlq():
    dlq = []
    async def _dlq(mid, body, reason):
        dlq.append((mid, body, reason))
    return dlq, _dlq


class TestStreamingConsumer(unittest.IsolatedAsyncioTestCase):

    async def test_processes_all_messages(self):
        sink = FastSink()
        acks, ack = noop_ack()
        c = StreamingConsumer(
            ConsumerConfig(queue_size=10, num_workers=4),
            source=lambda ev: fake_source(ev, count=50),
            sink=sink, ack=ack,
        )
        m = await c.run()
        self.assertEqual(m['processed'], 50)
        self.assertEqual(len(acks), 50)

    async def test_backpressure_caps_queue(self):
        """Producer must wait when queue full — queue depth <= maxsize."""
        observed_depths = []

        # Slow sink + fast source
        sink = SlowSink(latency_s=0.05)
        acks, ack = noop_ack()
        c = StreamingConsumer(
            ConsumerConfig(queue_size=5, num_workers=2, metrics_interval_s=0.01),
            source=lambda ev: fake_source(ev, count=30),
            sink=sink, ack=ack,
        )
        # Patch metrics_task to record queue depth
        orig = c.metrics_task
        async def patched():
            while not c.shutdown_event.is_set():
                observed_depths.append(c.queue.qsize())
                await asyncio.sleep(0.01)
        c.metrics_task = patched

        await c.run()
        self.assertLessEqual(max(observed_depths), 5)

    async def test_retry_then_success(self):
        sink = FailingSink(fail_n=2)  # fail 2x then succeed
        acks, ack = noop_ack()
        c = StreamingConsumer(
            ConsumerConfig(queue_size=2, num_workers=1, max_retries=3,
                            base_backoff_s=0.001),
            source=lambda ev: fake_source(ev, count=1),
            sink=sink, ack=ack,
        )
        m = await c.run()
        self.assertEqual(m['processed'], 1)
        self.assertEqual(m['retried'], 2)
        self.assertEqual(sink.successes, 1)

    async def test_max_retries_sends_dlq(self):
        sink = FailingSink(fail_n=100)  # always fail
        acks, ack = noop_ack()
        dlq, dlq_fn = collecting_dlq()
        c = StreamingConsumer(
            ConsumerConfig(queue_size=2, num_workers=1, max_retries=2,
                            base_backoff_s=0.001),
            source=lambda ev: fake_source(ev, count=1),
            sink=sink, ack=ack, dlq=dlq_fn,
        )
        m = await c.run()
        self.assertEqual(m['failed'], 1)
        self.assertEqual(m['sent_to_dlq'], 1)
        self.assertEqual(len(dlq), 1)
        self.assertIn('max_retries', dlq[0][2])

    async def test_graceful_shutdown_drains(self):
        sink = SlowSink(latency_s=0.05)
        acks, ack = noop_ack()
        c = StreamingConsumer(
            ConsumerConfig(queue_size=10, num_workers=2,
                            shutdown_timeout_s=10.0),
            source=lambda ev: fake_source(ev, count=10),
            sink=sink, ack=ack,
        )
        m = await c.run()
        self.assertEqual(m['processed'], 10)
        self.assertEqual(m['queue_depth'], 0)

    async def test_fatal_goes_to_dlq_no_retry(self):
        class FatalSink:
            calls = 0
            async def __call__(self, body):
                FatalSink.calls += 1
                raise FatalError('bad json')

        acks, ack = noop_ack()
        dlq, dlq_fn = collecting_dlq()
        c = StreamingConsumer(
            ConsumerConfig(queue_size=2, num_workers=1, max_retries=5),
            source=lambda ev: fake_source(ev, count=1),
            sink=FatalSink(), ack=ack, dlq=dlq_fn,
        )
        m = await c.run()
        # Only 1 call, no retries (fatal)
        self.assertEqual(FatalSink.calls, 1)
        self.assertEqual(len(dlq), 1)
        self.assertIn('fatal', dlq[0][2])


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.WARNING)
    unittest.main()
```

**Edge cases (说给面试官)**:

1. **Source exhausted** — producer ends, workers drain queue, graceful exit
2. **Source slow / empty for a while** — workers idle on `q.get()` with timeout
3. **Sink burst slow** — queue 满, `q.put()` block, source 停 pull — **核心 case**
4. **One message poison** (always throws fatal) — DLQ + ack 不影响 others
5. **Transient downstream errors (5xx, timeout)** — retry with exponential + jitter
6. **Persistent downstream outage** — circuit breaker opens, producer pauses
7. **SIGTERM mid-flight** — set shutdown event, stop pulling, drain in-flight, ack each, exit clean
8. **Memory cap respected** — `qsize() <= queue_size` always (assert in test)
9. **Same msg redelivered (at-least-once)** — sink must be idempotent (我们 caller responsibility)
10. **Worker crash on bug** — `worker_task` has try/except; one worker death does not kill others
11. **Out-of-order processing** — multi-worker 会乱序; doc 注明; 需 order 时 single worker / partition
12. **Backoff explosion** — `max_backoff_s` cap, 不会 retry 1000 秒
13. **DLQ itself fails** — wrap in try/except + log; 不要因 DLQ 挂导致 main loop 死

### Step 4: Trade-offs + extensions (5-10 min)

**Scale + tune**:

```
Little's Law: throughput × latency = in_flight
  E.g., 100 msg/s × 200ms latency = 20 concurrent
  So num_workers ≈ 20–40 (with headroom)

queue_size:
  - Too small (1–4): pipeline starvation, workers idle while producer waits
  - Too large (10000): memory unbounded; backpressure kicks too late
  - Sweet spot: workers × 2-5 = 40-200

max_retries:
  - 0: too aggressive DLQ for transient blips
  - 3-5: reasonable
  - 10+: dangerous tail latency

backoff:
  - base 0.5s, cap 30s, 3 retries → max 0.5+1+2+4 = 7.5s
  - full jitter random.uniform(0, base*2^n) — better than equal-jitter
```

**Partitioning + ordering**:

```python
# If per-key ordering matters, partition workers by key hash
async def routed_worker(worker_id, partition_id, total_partitions):
    while True:
        mid, body = await queue.get()
        if hash(mid) % total_partitions != partition_id:
            await queue.put((mid, body))  # not mine — danger of livelock
            await asyncio.sleep(0.01)
            continue
        ...
```

Better: **N queues, 1 worker per queue**, partition at enqueue:

```python
queues = [asyncio.Queue(maxsize=K) for _ in range(N_PARTITIONS)]
async def producer():
    async for mid, body in source(...):
        p = hash(mid) % N_PARTITIONS
        await queues[p].put((mid, body))  # backpressure per partition
```

**Exactly-once**:

```
At-least-once + idempotent downstream = de facto exactly-once
  - dedupe by msg_id at downstream (Redis SETNX cache)
  - 5-min TTL on cache covers replay window

Kafka EOS:
  - Transactional producer + transactional offset commit
  - Hard to do for arbitrary downstream (e.g., LLM API)
```

**Multi-stage pipeline**:

```
source → queue1 → preprocess workers → queue2 → llm workers → queue3 → write workers → sink
```

每个 queue + worker pool 是一个 stage. Backpressure 自动 propagate from sink upward.

**HTTP source (poll instead of push)**:

```python
async def http_source(shutdown):
    while not shutdown.is_set():
        # Pull batch
        msgs = await client.poll(max_messages=10, timeout=5)
        for mid, body in msgs:
            yield mid, body
        # If consumer is keeping up, this loop runs continuously
        # If consumer is slow, q.put() blocks, polling pauses
```

---

## 完整代码 (Production-ready)

完整 module 已在 Step 2. 安装 + 跑:

```bash
# No 3rd party deps for core (stdlib asyncio only)
python -c "import asyncio; asyncio.__version__"

# Run tests:
python -m unittest test_consumer.py -v
```

**Real-world wiring example (Kafka source + OpenAI sink)**:

```python
async def kafka_source(shutdown):
    consumer = AIOKafkaConsumer('topic', bootstrap_servers='kafka:9092',
                                 group_id='my-app')
    await consumer.start()
    try:
        async for record in consumer:
            yield str(record.offset), record.value
            # Commit only after ack
    finally:
        await consumer.stop()

async def openai_sink(body):
    async with httpx.AsyncClient() as c:
        r = await c.post('https://api.openai.com/v1/...',
                          json=json.loads(body), timeout=30.0)
        if r.status_code == 429:
            raise RetriableError('rate limited')
        if r.status_code >= 500:
            raise RetriableError(f'server error {r.status_code}')
        if r.status_code >= 400:
            raise FatalError(f'client error {r.status_code}')
        r.raise_for_status()
```

---

## 复杂度分析

| 资源 | 上限 |
|------|------|
| Memory (queue) | `queue_size × avg_msg_size` |
| In-flight | `num_workers × avg_msg_size` |
| File descriptors | num_workers + producer + signal handlers |
| Total throughput | `min(source_rate, num_workers / avg_latency)` |
| Tail latency | `max_retries × max_backoff + sink_p99` |

**Little's Law tuning**: target throughput T, sink latency L → workers ≈ T × L.
e.g., 200 msg/s × 250ms = 50 workers.

---

## Gao Xin 简历专属 reframe

- **Voice agent (7 markets)**: outbound call queue + LLM inference (vLLM/SGLang) downstream. 我做的是 Ray actor + Anyscale serve, 但 asyncio 版本一样 — bounded queue, retry, DLQ for "客户挂电话" 类 fatal. 实际值: queue_size 100, workers 16-32 per pod, max_retries 2 (call latency 已经长).
- **BNPL chatbot**: 消息 (用户输入) 进 queue → RAG retrieve (slow downstream: ES/Chroma) → LLM → reply. backpressure on RAG 慢时, 我们 cancel 旧消息 (用户已经走了) — Redis Streams 加 TTL.
- **Internal Agent Platform**: tools (HTTP API) 经常 slow / fail, 我做的 retry + circuit breaker + DLQ 框架几乎和这道题一样.
- **Indonesia refund tier**: refund decision pipeline 是 Kafka → fraud scoring (slow ML model) → decision → write. backpressure 是 fraud model 慢时 Kafka lag 涨, 但 OOM 风险隔离.
- **ConvFinQA**: 9-variant ablation 跑 LLM API 时 client-side 限流 + retry + DLQ.

**面试一句话**: "Built this exact pattern at TikTok for the voice agent — Kafka → asyncio queue → LLM workers. The hardest bug was a missing `task_done()` causing `q.join()` to hang on shutdown."

---

## 5 个 Follow-ups

**Q1**: "你怎么 measure backpressure 真的发生了?"

A: 三个指标:
1. **Queue depth** (`qsize()`) — 持续 close to maxsize 就在 backpressure
2. **Producer block time** — instrument `await q.put()` 前后 `time.monotonic()`, 如果 > 100ms 就 backpressure
3. **Consumer lag** (Kafka 特有) — `lag = high_water_mark - committed_offset`. Lag 上涨 = consumer 慢
Tooling: emit `consumer.queue.depth`, `consumer.producer.block_ms`, `kafka.lag` to Prometheus / Datadog.

**Q2**: "如果 sink 慢到不能接受 (e.g., p99 > 30s), 怎么办?"

A: 几个 lever:
1. **Increase workers** — Little's Law, T = N / L, N↑ → T↑ (前提 sink 自己能并发)
2. **Drop messages** with TTL — `if msg.age > 60s: drop + log` (适合 best-effort 场景如 metrics)
3. **Downgrade quality** — slow downstream → switch to cheaper / faster path (e.g., GPT-4o → GPT-4o-mini)
4. **Shed load** — circuit breaker open → reject new messages with 503, let source retry later
5. **Scale horizontally** — k8s HPA on queue depth

**Q3**: "Exactly-once 你怎么做?"

A: 真 exactly-once 几乎不可能, 实际方案:
1. **At-least-once + idempotent downstream**: downstream 用 msg_id 做 SETNX, 重复 msg 直接 short-circuit
2. **Kafka EOS**: transactional commit, 但限制 downstream 也得 Kafka 或同一 transaction
3. **Outbox pattern**: 处理结果先写 outbox 表 (with msg_id), 单独 worker poll outbox → side effect

我做的 BNPL refund 用 idempotent — refund_id 作为 SETNX key, redis 24h TTL.

**Q4**: "在 K8s 上跑你怎么 scale?"

A: 
- HPA 指标: `kafka_consumer_lag` 或 `queue_depth_p99`
- Pod readinessProbe: `qsize < maxsize × 0.8` (满了说明 backpressure, 不 ready 收新)
- preStop hook: SIGTERM → graceful shutdown 30s grace
- partitions per pod: Kafka topic partitions = pod count × N, N=2-3
- Don't auto-scale on CPU — IO-bound, CPU 永远低

**Q5**: "如果 source 自己也是 backpressure-aware (e.g., HTTP poll), 你怎么传?"

A: HTTP poll 比 push 更 natural:
```python
async def http_source(shutdown):
    while not shutdown.is_set():
        if queue.qsize() > queue_size * 0.8:
            await asyncio.sleep(0.5)  # don't poll if buffer half full
            continue
        msgs = await client.poll(max=10)
        for m in msgs:
            await queue.put(m)
```
对 Kafka 是隐式: consumer 不 commit, partition 就停在那, broker 不 push 新的.

---

## 死路答法

1. **`asyncio.gather([process(m) for m in source])`** — unbounded concurrency, 立即 OOM
2. **`for m in source: asyncio.create_task(process(m))`** — 同上, task 无限创建
3. **`asyncio.Queue()` 无 maxsize** — 没 backpressure, queue 涨到 GB 内存
4. **没 `task_done()`** — `queue.join()` 永远 hang, graceful shutdown 失败
5. **没 timeout on `q.get()`** — worker stuck wait, 不响应 shutdown event
6. **Retry 用 `time.sleep(N)`** — block event loop, 其他 task 死
7. **没 jitter on backoff** — 多 worker 同步 retry, thundering herd 打挂 downstream
8. **Catch all exceptions silently** — bug 被吞, 客户看不到 fail
9. **Ack 在 process 之前** — process 失败但 source 以为 done, 丢消息
10. **不 ack fatal 错误的 message** — source 永远重投 poison, 卡死整 partition

---

## 加分项

**Production discussion 加分**:

- **Heartbeat / liveness**: 单独 task 每秒 update `last_active_ts`, K8s probe check
- **Graceful pod rotation**: rolling update 时 preStop 30s, 期间 SIGTERM 触发 graceful drain
- **DLQ schema**: `{msg_id, body, error, attempt, first_seen, last_seen, owner_app}` — re-process tool 可拣回
- **DLQ alerting**: `dlq_rate > 1% → page` — 客户问"为什么我消息丢了" 提前看到
- **Replay tool**: `replay --since 2024-01-15 --filter status=failed` 从 DLQ 重投
- **Idempotency key**: `Idempotency-Key: msg_id` HTTP header — downstream 帮忙 dedupe
- **Cost observability**: per-msg cost (LLM tokens) emit, total spend per minute
- **Backpressure visualization**: Grafana panel: queue depth over time + producer block time + sink p99 — 一眼看出谁是瓶颈
- **Chaos**: 周期性注入 5% latency / error, 验证 backpressure + retry 行为
- **Multi-region**: source 多个 region, 每 region 一组 consumer + 区域 DLQ + 跨区 audit log

---

## 一句话总结

> **Bounded `asyncio.Queue` + N workers + per-msg retry + circuit breaker + graceful drain. Backpressure 通过 `await q.put()` block 自然 propagate to producer, 不会 OOM.**

---

## Cheat Sheet

```python
# Skeleton:
queue = asyncio.Queue(maxsize=K)
shutdown = asyncio.Event()

async def producer():
    async for msg in source:
        if shutdown.is_set(): break
        await queue.put(msg)        # ← backpressure here

async def worker():
    while True:
        msg = await asyncio.wait_for(queue.get(), timeout=1)
        try:
            await process_with_retry(msg)
        finally:
            queue.task_done()

# Tuning (Little's law):
#   workers ≈ throughput × latency
#   queue_size ≈ workers × 2-5

# Retry:
#   classify: Retriable (5xx, timeout) vs Fatal (4xx, schema)
#   exponential + full jitter: random.uniform(0, base * 2**n)
#   max_retries cap; on exhaust → DLQ + ack

# Circuit breaker:
#   N errors in window_s → open for cooldown_s
#   producer pauses while open

# Graceful shutdown:
#   signal handler → set shutdown event
#   producer break loop
#   await queue.join()         # wait in-flight to drain
#   cancel workers, gather

# Metrics that matter:
#   queue.qsize() = backpressure depth
#   producer block ms = where time spent waiting
#   in_flight = current concurrency
#   retried / failed / dlq counts
#   sink p99 latency

# Pitfalls:
#   no maxsize → OOM
#   no task_done → join hangs
#   no timeout on get → worker stuck
#   sync sleep in retry → blocks loop
#   ack before process → message loss
```
