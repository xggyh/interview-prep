## Q26 · 支持优先级 + 重试 + 死信的分布式任务队列

> "Design a **distributed task queue** that supports: **priority** (paid > free), **retry** with exponential backoff, **dead-letter** after N failures, **per-tenant fair scheduling** (one big customer can't starve others), and **idempotency**. Throughput **10K tasks/sec**, task duration ranges 100ms - 10min. Talk through Kafka vs Redis Streams vs Postgres SKIP LOCKED vs Temporal."

**Round**: System Design (60 min)
**出处**: Exponent 2026 FDE · 公司: Anthropic / Stripe / Cloudflare / Temporal · 行业: infra / fintech
**约束**: 10K TPS / multi-tenant fairness / wide duration variance (100ms - 10min) / per-tenant priority / exactly-once semantics where possible / observability for debugging stuck jobs

---

## 📖 术语速查 (本题用到的)

> 这题是分布式系统经典题. 名词不懂直接挂. 5 min 看完.

### 队列概念 (核心)

| 术语 | 解释 |
|---|---|
| **Task queue** ⭐ | 任务队列 — producer 把任务塞队列, worker 拿任务执行. |
| **Producer / Consumer / Worker** | 生产者 (塞任务) / 消费者 (拿任务) / 执行者. |
| **Dispatcher** | 调度器 — 决定 next task 给哪个 worker. |
| **Topic / Partition** | Kafka 概念 — topic 是逻辑队列, partition 是物理分片. |
| **DLQ (Dead Letter Queue)** ⭐ | 死信队列 — N 次重试失败后进的终态队列. |
| **HOL blocking (Head-of-Line)** | 队头阻塞 — 队头慢任务卡住后续. Kafka 长任务的痛. |
| **Backpressure** | 反压 — 下游处理不过来时向上游 push back (e.g. 返回 429). |

### 语义 / 可靠性

| 术语 | 解释 |
|---|---|
| **At-least-once** ⭐ | 至少一次 — 可能重复发, 必须配 idempotency. 业界默认. |
| **Exactly-once** | 恰好一次 — 分布式系统严格意义不可能, 只能 effectively-once. |
| **At-most-once** | 最多一次 — 可能丢, 不重复. |
| **Idempotency / Idempotency key** ⭐ | 幂等 / 幂等键 — 同 key 多次提交结果一样. Stripe 标配. |
| **Dedup window** | 去重窗口 — 24h 内同 idem key 视为同一 task. |
| **Effectively-once** | 实际一次 — at-least-once + idempotent processor. |
| **FIFO** | First-In-First-Out 顺序. |

### 重试 / 失败处理

| 术语 | 解释 |
|---|---|
| **Retry with backoff** ⭐ | 带退避的重试 — 失败后等一段时间再试. |
| **Exponential backoff** | 指数退避 — 1s / 2s / 4s / 8s ... |
| **Jitter** | 抖动 — 在退避时间上加随机扰动, 避免 thundering herd. |
| **Stripe-style 阶梯 backoff** ⭐ | Stripe 公开的退避策略: 30s/2m/10m/1h/6h/24h/3d/7d. 适应真实失败模式. |
| **Thundering herd** | 雷暴 — 多 worker 同时重试导致瞬间洪峰. |
| **Circuit breaker** | 熔断器 — 错误率高时直接拒绝, 给下游恢复时间. |
| **Visibility timeout** ⭐ | 不可见超时 — worker 拿到任务后多久没 ack 就 re-deliver. SQS 概念. |
| **Lease / Leased** | 租约 — task 被 worker 持有的状态. |
| **Heartbeat** ⭐ | 心跳 — long-running worker 定期续 lease, 防 spurious retry. |
| **ack / nack** | acknowledge / negative ack — 任务完成 / 失败的通知. |

### 公平性 / 优先级

| 术语 | 解释 |
|---|---|
| **Priority queue** | 优先级队列 — paid > free. |
| **Per-tenant fair scheduling** ⭐ | 多租户公平调度 — 一个大客户不能 starve 别人. |
| **Starvation** | 饥饿 — 低优先 task 永远拿不到 worker. |
| **WFQ (Weighted Fair Queueing)** ⭐ | 加权公平队列 — 按 weight 分配份额. |
| **DRR (Deficit Round Robin)** | 亏空轮询 — WFQ 的具体实现. |
| **Token bucket** | 令牌桶 — 经典 rate limiting 算法. |
| **Min-share guarantee** | 最低份额保证 — 任何 tenant 至少分到 5%. |
| **Burst** | 突发 — 短时间内大量请求. |
| **Quota / In-flight quota** | 配额 — 同时 leased 上限. |

### Backing Store 选型

| 术语 | 解释 |
|---|---|
| **Kafka** ⭐ | 高吞吐流式日志, 1M+ TPS 但 long task HOL block. |
| **Redis Streams** | Redis 5+ 的 stream 数据结构, 100K TPS 量级. |
| **RabbitMQ** | 经典 AMQP 队列, Erlang 实现. |
| **Postgres SKIP LOCKED** ⭐ | Postgres 9.5+ 的特性 — `FOR UPDATE SKIP LOCKED` 让多 worker 跳过已锁行. |
| **SQS (Simple Queue Service)** | AWS 托管队列. |
| **Temporal** ⭐ | 工作流编排引擎 (不仅是队列). 长 workflow + state 适合. |
| **Celery** | Python 经典任务队列库. |
| **Outbox pattern** | 任务和业务 state 在同一 DB transaction, 后异步 publish. |
| **Saga** | 长流程补偿模式. |

### 数据结构 / 操作

| 术语 | 解释 |
|---|---|
| **Sorted set (ZADD)** | Redis 有序集合 — 按 score 排序, 快速 peek top. |
| **SET NX / EX** | Redis 命令 — NX = if Not eXists; EX = expiry seconds. |
| **JSONB** | Postgres 二进制 JSON 列. |
| **Partial index** | Postgres 部分索引 — WHERE 条件下才建索引. |
| **FOR UPDATE SKIP LOCKED** | Postgres 行锁 + 跳过已锁. |
| **Materialized view** | 物化视图 — 预聚合结果, 定时刷新. |
| **PARTITION BY RANGE** | Postgres 表分区. |

### 部署 / Scale

| 术语 | 解释 |
|---|---|
| **HA (High Availability)** | 高可用 — 主从 + 自动 failover. |
| **DR (Disaster Recovery)** | 灾难恢复 — 跨 region 备份. |
| **RPO / RTO** | Recovery Point Objective / Time Objective — 能丢多少数据 / 多久恢复. |
| **HPA (Horizontal Pod Autoscaler)** | K8s 水平自动伸缩. |
| **Long polling** | 长轮询 — client 等 server 有数据再返回. |
| **Sharding** | 分片 — 按 hash 拆 DB. |
| **Aurora multi-AZ** | Aurora 跨可用区高可用. |

### 监控

| 术语 | 解释 |
|---|---|
| **Queue depth** | 队列深度 — 待处理任务数. |
| **Dispatch lag** | 派发延迟 — 入队到开始执行的时间. |
| **PagerDuty / Slack alert** | 告警工具. |
| **Iceberg (audit)** | 数据湖表格式 — 用于审计日志归档. |
| **Stuck task** | 卡住的 task — leased > 预期时长. |
| **parent_task_id** | 父任务 ID — 用于链式 task lineage. |
| **OTel span chain** | OpenTelemetry span 链 — 跨 service trace 任务生命周期. |

---

## 这道题在考什么

不是考你 Celery + Redis, 是考你**真正在 production 用过分布式 queue, 知道这些 trade-off**:

1. **Queue backend 选型** — Kafka / Redis Streams / Postgres SKIP LOCKED / RabbitMQ / Temporal, 每个有真实 sweet spot
2. **优先级实现** — multi-topic vs sorted set vs priority queue (Kafka 不原生支持)
3. **Retry strategy** — Stripe-style 阶梯 (30s/2m/10m/1h/6h/24h) + jitter, 不是 simple exponential
4. **Idempotency** — 同一 task 不能跑两次, idempotency key + dedup window
5. **Per-tenant fair scheduling** — token bucket / weighted fair queueing / per-tenant topic
6. **Visibility timeout** — worker pick task 后多久没 ack 就 re-deliver, 是 SQS / DLQ 关键
7. **Worker heartbeat** — long-running task 怎么续期 visibility, 不被 spurious retry
8. **Observability** — 卡 task 怎么 debug, lineage 怎么 trace
9. **菜鸟答案失败点**: "Celery + Redis + retry decorator" — 完全没回答 fairness / priority / DLQ / visibility timeout 这些 真正 production 痛点.

---

## 必问 clarifying questions

1. **Task duration distribution**: 100ms - 10min 是 uniform 还是 90% < 1s + 10% > 1min? 完全不同选型
2. **Failure semantics**: exactly-once required (financial)? at-least-once OK (analytics)?
3. **Order matters?**: per-tenant FIFO 还是 unordered? 影响 partition strategy
4. **Latency-sensitive?**: task 入队到开始执行 < 100ms 还是 < 10s 都 OK?
5. **Workers homogeneous?**: 所有 worker 一样 还是 specialized (CPU vs GPU)?
6. **Tenant count**: 10 tenant 还是 10K? 影响 isolation 策略
7. **Persistence requirement**: crash 后 task 不能丢, 多严? RPO 0 vs 1 min
8. **Existing infra**: Kafka 已有? Redis 已有? Postgres 已有? 影响 build-vs-buy

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|------|------|------|
| 1 | Clarify | 5 min | duration / failure semantic / fairness / scale | "三件事先锁: task duration 主分布, exactly-once 要不要, tenant 数" |
| 2 | Requirements + KPI | 4 min | functional + non-functional + observability | "我先列 8 个能力: prio / retry / DLQ / idem / fair / vis / heart / obs" |
| 3 | Backend selection | 8 min | Kafka / Redis / Postgres / Temporal trade matrix | "10K TPS + 10min 长 task + fairness → Redis Streams 或 Postgres" |
| 4 | Architecture | 12 min | Topology + topic/queue design + worker model | "我画 producer → queue → worker → DLQ, fairness 在 dispatcher" |
| 5 | Retry + DLQ | 10 min | Stripe-style backoff + DLQ structure + manual replay | "Exponential 不够, Stripe 阶梯 + jitter, 8 attempts → DLQ" |
| 6 | Idempotency + visibility | 8 min | Idempotency key + visibility timeout + heartbeat | "Idempotency key in payload, visibility 5min default, heartbeat for long" |
| 7 | Multi-tenant fairness | 6 min | Per-tenant queue + weighted fair scheduling | "Per-tenant topic + WFQ dispatcher" |
| 8 | Trade-offs + close | 7 min | Build vs Temporal / SQS / Cloud queue | "10K TPS 我们自建 OK, > 100K 就 Kafka. Temporal 是补充不是替代" |

---

## 端到端架构图 (ASCII)

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                          Task Queue System Architecture                                  │
│                                                                                          │
│   ┌─Producers──────────────────────────────────────┐                                     │
│   │   API service (sync HTTP receive task)         │                                     │
│   │   Cron / scheduler (CronCreate spawns tasks)   │                                     │
│   │   Event-driven (Kafka consumer → produce task) │                                     │
│   └─────────────────┬──────────────────────────────┘                                     │
│                     │  POST /enqueue                                                     │
│                     │  { task_id (uuid), tenant_id, priority, payload, idempotency_key,  │
│                     │    max_attempts, visibility_timeout_s, scheduled_at }              │
│                     ▼                                                                    │
│   ┌──────────────────────────────────────────────────────────────────────┐               │
│   │  Enqueue Service (Go / Rust, stateless)                              │               │
│   │   - Validate schema                                                  │               │
│   │   - Idempotency check (last 24h dedup, Redis SET NX)                 │               │
│   │   - Authorize (tenant has quota? rate limit?)                        │               │
│   │   - Write to backing store + return task_id                          │               │
│   │   - p99 enqueue < 10ms                                               │               │
│   └────────────────────┬────────────────────────────────────────────────┘                │
│                        │                                                                 │
│                        ▼                                                                 │
│   ┌──────────────────────────────────────────────────────────────────────┐               │
│   │  Backing Store: Postgres + Redis hybrid (or Redis Streams alone)      │               │
│   │                                                                       │               │
│   │  Schema (tasks table):                                                │               │
│   │   id, tenant_id, priority, state (queued/leased/done/dead),           │               │
│   │   attempts, payload (JSONB), idempotency_key,                         │               │
│   │   leased_by, leased_until, scheduled_at, created_at                   │               │
│   │   Index: (state, priority, scheduled_at) for SKIP LOCKED              │               │
│   │   Index: (tenant_id, priority, scheduled_at) for fairness             │               │
│   │   Index: idempotency_key (UNIQUE in 24h partition)                    │               │
│   │                                                                       │               │
│   │  Redis (companion):                                                   │               │
│   │   - sorted set per tenant: ZADD ready_tasks score=priority×timestamp │               │
│   │   - hash: leased{task_id} → worker_id, lease_until                    │               │
│   │   - dedup SET NX: idem{key} → task_id, TTL 24h                        │               │
│   └─────────────────────┬────────────────────────────────────────────────┘               │
│                         │                                                                │
│                         ▼                                                                │
│   ┌──────────────────────────────────────────────────────────────────────┐               │
│   │  Dispatcher (lease assigner, runs as horizontal pool)                │               │
│   │   - For each tenant: read top-K from sorted set                      │               │
│   │   - Apply WFQ (weighted fair queueing) across tenants                │               │
│   │   - Apply priority within tenant                                     │               │
│   │   - Lease: BEGIN; UPDATE tasks SET state='leased', leased_by=worker, │               │
│   │            leased_until=now()+visibility_timeout WHERE id=$1; COMMIT │               │
│   │   - Or with Postgres FOR UPDATE SKIP LOCKED                          │               │
│   │   - Atomic via Lua script if Redis-only                              │               │
│   └─────────────────────┬────────────────────────────────────────────────┘               │
│                         │                                                                │
│                         ▼                                                                │
│   ┌──────────────────────────────────────────────────────────────────────┐               │
│   │  Worker pool (containerized, auto-scaling)                           │               │
│   │   - Long poll for lease: GET /lease?worker=W1, blocking 30s          │               │
│   │   - Execute task                                                     │               │
│   │   - Heartbeat every (visibility_timeout / 3) for long tasks          │               │
│   │   - On success: POST /ack?task_id=X → state='done'                   │               │
│   │   - On failure: POST /nack?task_id=X&reason=Y → enqueue retry        │               │
│   │   - On worker crash: lease expires, dispatcher re-leases             │               │
│   └─────────────────────┬────────────────────────────────────────────────┘               │
│                         │                                                                │
│                         ▼                                                                │
│   ┌──────────────────────────────────────────────────────────────────────┐               │
│   │  Retry Manager                                                       │               │
│   │   - On nack: schedule_at = now() + backoff(attempts) + jitter        │               │
│   │   - backoff: [30s, 2m, 10m, 1h, 6h, 24h, 3d, 7d]                     │               │
│   │   - After 8 attempts: move to DLQ                                    │               │
│   │   - DLQ: separate dlq table, 30 day retention                        │               │
│   │   - DLQ alert: PagerDuty if > 100 dead/hr                            │               │
│   │   - Manual replay: ops API POST /dlq/{id}/replay → re-enqueue        │               │
│   └────────────────────────────────────────────────────────────────────┘                 │
│                                                                                          │
│   ┌──────────────────────────────────────────────────────────────────────┐               │
│   │  Observability                                                       │               │
│   │   Metrics:                                                           │               │
│   │     - enqueue_rate, dispatch_lag, processing_time, dlq_rate          │               │
│   │     - queue_depth per tenant                                         │               │
│   │     - retry_rate per tenant per error class                          │               │
│   │   Tracing:                                                           │               │
│   │     - OTel span chain: enqueue → lease → execute → ack               │               │
│   │     - parent_task_id for chained tasks                               │               │
│   │   Dashboards (Datadog / Grafana):                                    │               │
│   │     - Per-tenant queue depth                                         │               │
│   │     - DLQ growth rate by error class                                 │               │
│   │     - Stuck task (leased > 2× expected duration)                     │               │
│   │   Audit log: all state transitions to Iceberg                        │               │
│   └──────────────────────────────────────────────────────────────────────┘               │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 详细设计 (60-min walkthrough)

### Phase 1: Clarify + KPI (5 min)

锁:
- "Duration spectrum: 100ms - 10min. 95% < 1s 还是 30% > 1min? 影响选型 — 长 task 不适合 Kafka (commit lag), 适合 leased model"
- "Failure semantics: exactly-once or at-least-once? 大部分系统接受 at-least-once + idempotency, 真 exactly-once 极难"
- "Tenant count: 10 enterprise customer 还是 10K SMB? 影响 fairness 设计"

假设: at-least-once + idem key, ~80% < 1s + 20% > 1min, 200 tenant (~80/20 distribution), 现成 Postgres + Redis 可用.

KPI:
- **Throughput**: 10K tasks/sec sustained, 30K peak
- **Enqueue latency**: p99 < 10ms
- **Time-to-execute**: p99 < 1s for high-priority, p99 < 60s for low-priority
- **No starvation**: smallest tenant gets ≥ 5% of capacity even under load
- **DLQ rate**: < 0.1% of total
- **Worker crash recovery**: < 60s re-lease

### Phase 2: Requirements + KPI (4 min)

8 个 capability:
1. **Priority** (paid > free, but free not starved)
2. **Retry** with backoff + jitter
3. **DLQ** after N attempts
4. **Idempotency** (dedup window 24h)
5. **Per-tenant fairness** (no single tenant monopolize)
6. **Visibility timeout** (worker fails to ack → re-lease)
7. **Worker heartbeat** (long task extends lease)
8. **Observability** (debug stuck task, per-tenant metrics)

Non-functional:
- HA: backing store 主从 + automatic failover
- DR: cross-region snapshot every 1h
- Backpressure: enqueue rejects with 429 if backing store > 90% capacity
- Audit: state transition log for forensics

### Phase 3: Backend selection (8 min)

**Decision matrix**:

| 选项 | Throughput | Long task | Priority | Fairness | Ops cost | Trade-off |
|---|---|---|---|---|---|---|
| Kafka | 1M TPS | Bad (commit lag) | Multi-topic hack | Hard | High | Good for short stream, bad for leased work |
| RabbitMQ | 50K TPS | OK | Native | OK | Medium | Classic but aging |
| Redis Streams | 100K TPS | OK | Sorted set | OK | Low | New-ish, Redis 6+ |
| Postgres SKIP LOCKED | 10-30K TPS | Great | SQL ORDER BY | Easy (group by tenant) | Low | DB-coupled, simple |
| AWS SQS | 30K TPS | OK | Multi-queue + priority pattern | Per-queue | None | Managed, vendor lock |
| Temporal | 10K TPS | Excellent (durable workflow) | Built-in | Built-in | Medium | Workflow not queue |

**我推**: Postgres SKIP LOCKED + Redis (sorted set for fast peek) hybrid.

理由:
- Postgres SKIP LOCKED durable, ACID, indices 强, 10K TPS 够 (单 Aurora db.r6g.4xlarge)
- Redis sorted set 加速 peek (Postgres SELECT 在大 queue 可能慢)
- 团队已有 PG + Redis, 不引入新 dependency
- 没用 Kafka 因为 long-running task (10min) commit lag 痛
- 没用 Temporal 因为这是 generic task queue 不是 workflow orchestration

**Why not Kafka**:
- Kafka 是 log, 不是 queue. 任务 ack 是 commit offset, 任务在 consumer crash 时 by-default at-least-once 但 没 native visibility timeout
- 10min task: consumer 拿到任务后 commit offset 拖 10min → 同 partition 后续 task 全卡 (HOL blocking)
- Priority: Kafka 不原生支持, hack 是 multi-topic + 消费时 round-robin, 复杂

**Why not RabbitMQ**:
- 可以, 但 RabbitMQ 在 Erlang VM ops 相对 PG/Redis 重
- 没有 native idempotency
- Cluster failover 历史上 painful

**Why not SQS**:
- 如果客户用 AWS 唯一, SQS 是好选项
- 但 visibility timeout max 12h 限制
- 没有 native per-tenant fairness (需要 multi-queue)
- 不 portable

**Why Temporal might fit**:
- 如果 task 是 workflow (multi-step + state), Temporal 完爆 queue
- 但纯 queue (single-step task), Temporal overkill
- 推荐 combo: queue 做 short / stateless task, Temporal 做 workflow

### Phase 4: Architecture deep dive (12 min)

**4.1 Schema (Postgres)**

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    priority SMALLINT NOT NULL DEFAULT 100,  -- 0=highest, 200=lowest
    state TEXT NOT NULL CHECK (state IN ('queued', 'leased', 'done', 'failed', 'dead')),
    attempts SMALLINT NOT NULL DEFAULT 0,
    max_attempts SMALLINT NOT NULL DEFAULT 8,
    payload JSONB NOT NULL,
    result JSONB,
    last_error TEXT,
    
    -- Idempotency
    idempotency_key TEXT,
    
    -- Lease info
    leased_by TEXT,
    leased_until TIMESTAMPTZ,
    visibility_timeout_s INT NOT NULL DEFAULT 300,
    
    -- Scheduling
    scheduled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
) PARTITION BY RANGE (created_at);  -- monthly partition

CREATE INDEX tasks_ready ON tasks (state, priority, scheduled_at)
    WHERE state IN ('queued') AND scheduled_at <= NOW();
CREATE INDEX tasks_lease_expired ON tasks (leased_until)
    WHERE state = 'leased';
CREATE INDEX tasks_idem ON tasks (idempotency_key, created_at)
    WHERE idempotency_key IS NOT NULL;
CREATE INDEX tasks_tenant_q ON tasks (tenant_id, priority, scheduled_at)
    WHERE state = 'queued';
```

Partition by month for retention (drop old partitions cheap).

**4.2 Enqueue path**

```python
async def enqueue(task):
    # 1. Idempotency check
    if task.idempotency_key:
        existing = await redis.set(
            f"idem:{task.idempotency_key}",
            task.id,
            nx=True,  # only set if not exists
            ex=86400  # 24h TTL
        )
        if not existing:
            # Idempotency hit; return existing task_id
            existing_id = await redis.get(f"idem:{task.idempotency_key}")
            return existing_id
    
    # 2. Insert
    await pg.execute("""
        INSERT INTO tasks (id, tenant_id, priority, payload, idempotency_key, scheduled_at, max_attempts)
        VALUES ($1, $2, $3, $4, $5, COALESCE($6, NOW()), $7)
    """, task.id, task.tenant_id, task.priority, task.payload, task.idempotency_key, task.scheduled_at, task.max_attempts)
    
    # 3. Update Redis sorted set for fast peek
    score = task.priority * 1e10 + task.scheduled_at.timestamp()
    await redis.zadd(f"ready:{task.tenant_id}", {task.id: score})
    
    return task.id
```

**4.3 Lease (dispatcher)**

```sql
-- Dispatcher worker N
BEGIN;
WITH next_task AS (
    SELECT id FROM tasks
    WHERE state = 'queued' AND scheduled_at <= NOW()
    ORDER BY priority ASC, scheduled_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED  -- key: skip if another worker holds row lock
)
UPDATE tasks t SET
    state = 'leased',
    leased_by = $1,
    leased_until = NOW() + INTERVAL '300 seconds',
    attempts = attempts + 1,
    started_at = NOW()
FROM next_task n
WHERE t.id = n.id
RETURNING t.id, t.payload, t.tenant_id, t.attempts;
COMMIT;
```

SKIP LOCKED 是 Postgres 9.5+ 关键: 当多 dispatcher 同时跑, 各自跳过被锁的行, 不 contention.

但是这 query 单一 ORDER BY 全局 priority, 没 fairness. 加 fairness 见 4.4.

**4.4 Per-tenant fairness (weighted fair queueing)**

每 tenant 有 weight (paid 高, free 低). Dispatcher 算法:

```python
# Pseudo-code: weighted fair queueing
def dispatch_one():
    # Read top-K from each tenant's Redis sorted set
    tenants = active_tenants()  # tenants with ready tasks
    
    # Calculate which tenant "owes" the queue
    # Deficit Round Robin (DRR)
    for t in tenants:
        deficit[t] += weight[t]  # paid weight=10, free weight=1
    
    candidate_tenants = sorted(tenants, key=lambda t: -deficit[t])
    
    for tenant in candidate_tenants:
        task_id = redis.zpopmin(f"ready:{tenant}")  # cheap
        if task_id:
            # Acquire actual lease in PG
            task = pg_lease(task_id)
            if task:
                deficit[tenant] -= cost_estimate(task)  # 1 unit per task
                return task
    return None
```

更简单 approach: stratified Random
```python
def dispatch_one():
    tenants = active_tenants()
    # weighted random pick
    chosen = weighted_random(tenants, weights=[weight[t] for t in tenants])
    return pg_lease_from_tenant(chosen)
```

效果: paid 10× weight 拿 ~10× capacity, 但 free 不会 starved (总有 1/N probability).

Min-share guarantee: 每 tenant 至少 5% capacity. 实现:
- Round-robin first pass guarantees floor
- Then weight-proportional 分剩余

**4.5 Worker model**

Workers long-poll dispatcher:
```python
while True:
    task = await dispatcher.lease(worker_id=W1, timeout=30)
    if not task:
        continue
    
    try:
        # Start heartbeat coroutine
        heartbeat = asyncio.create_task(send_heartbeat(task.id, interval=60))
        
        result = await process(task)
        
        await ack(task.id, result)
    except Exception as e:
        await nack(task.id, reason=str(e))
    finally:
        heartbeat.cancel()
```

Workers stateless, can scale horizontally. Autoscale by Kubernetes HPA on queue_depth metric.

### Phase 5: Retry + DLQ (10 min)

**5.1 Stripe-style backoff**

```python
def backoff_seconds(attempts):
    # Stripe.com 公开过的: exponential with cap
    base_intervals = [30, 120, 600, 3600, 21600, 86400, 259200, 604800]  
    # 30s, 2m, 10m, 1h, 6h, 24h, 3d, 7d
    if attempts >= len(base_intervals):
        return base_intervals[-1]
    base = base_intervals[attempts]
    
    # Jitter ±20%
    jitter = random.uniform(0.8, 1.2)
    return base * jitter

async def nack(task_id, reason):
    task = await pg.fetch_one("SELECT * FROM tasks WHERE id = $1", task_id)
    
    if task.attempts >= task.max_attempts:
        # Move to DLQ
        await pg.execute("""
            UPDATE tasks SET state = 'dead', last_error = $1, completed_at = NOW()
            WHERE id = $2
        """, reason, task_id)
        await dlq_alert(task, reason)
    else:
        # Retry
        retry_at = NOW() + timedelta(seconds=backoff_seconds(task.attempts))
        await pg.execute("""
            UPDATE tasks SET 
                state = 'queued',
                scheduled_at = $1,
                leased_by = NULL,
                leased_until = NULL,
                last_error = $2
            WHERE id = $3
        """, retry_at, reason, task_id)
```

**为什么 Stripe 阶梯而不是 pure exponential**:
- 真实 transient failures (network blip): 30s 后就好
- API outage: 2m / 10m 等服务恢复
- Persistent (config error): 1h+ 给运维窗口
- Hard failure: 24h+ 让 human 看
- 不 unbound: 限 7 day max (避免永久 zombie task)

**5.2 DLQ structure**

DLQ 不是 single bucket, 按 error class 分:

```sql
-- DLQ is logical (tasks where state='dead')
-- But organize by error class for triage
CREATE INDEX tasks_dlq_class ON tasks (last_error_class, completed_at)
    WHERE state = 'dead';

-- Materialized view for ops dashboard
CREATE MATERIALIZED VIEW dlq_summary AS
SELECT
    tenant_id,
    last_error_class,  -- 'timeout' | 'permission_denied' | 'upstream_500' | 'unknown'
    COUNT(*) as count,
    MAX(completed_at) as last_failed
FROM tasks
WHERE state = 'dead' AND completed_at > NOW() - INTERVAL '7 days'
GROUP BY tenant_id, last_error_class;
```

**5.3 Error classification**

```python
def classify_error(exception):
    if isinstance(exception, asyncio.TimeoutError):
        return 'timeout'
    if isinstance(exception, PermissionDenied):
        return 'permission_denied'  # permanent, no retry
    if 5xx_status(exception):
        return 'upstream_5xx'  # retry helpful
    if 4xx_status(exception):
        return 'upstream_4xx'  # likely permanent, retry futile
    if isinstance(exception, RateLimitError):
        return 'rate_limit'  # back off, retry
    return 'unknown'

def should_retry(error_class, attempts):
    # 4xx (except 429) usually permanent, fail fast
    if error_class in {'permission_denied', 'upstream_4xx'}:
        return attempts < 1  # one retry then DLQ
    return attempts < max_attempts
```

**5.4 Manual replay**

DLQ tasks 在 30 天 retention 期, ops 可 replay:

```python
@app.post("/dlq/{task_id}/replay")
async def replay(task_id, modifications=None):
    task = await pg.fetch_one("SELECT * FROM tasks WHERE id = $1 AND state = 'dead'", task_id)
    if not task:
        raise HTTPException(404)
    
    # Maybe modify payload (ops debugging)
    new_payload = {**task.payload, **(modifications or {})}
    
    # Re-enqueue as NEW task (keep audit)
    new_id = await enqueue(Task(
        tenant_id=task.tenant_id,
        priority=task.priority,
        payload=new_payload,
        parent_task_id=task.id,  # audit chain
        idempotency_key=None,  # NEW key, don't dedup
    ))
    
    # Mark old as 'replayed'
    await pg.execute("UPDATE tasks SET state = 'replayed' WHERE id = $1", task_id)
    
    return {"new_task_id": new_id}
```

**5.5 DLQ alerting**

- Threshold: > 100 DLQ entries/hr → P3 Slack
- Per-error-class spike: timeout suddenly 10× → P2 PagerDuty
- Per-tenant spike: 1 tenant 占 DLQ > 50% → P3 + customer success notification

### Phase 6: Idempotency + visibility timeout + heartbeat (8 min)

**6.1 Idempotency**

Producer 提供 `idempotency_key` (UUID or business key like `payment_{order_id}`):

```python
# Enqueue dedup window: 24h
SET idem:{key} task_id NX EX 86400  # Redis atomic
```

如果 collision: return existing task_id. Idempotency 在 enqueue 阶段, 不是 execute.

Execute 端 idempotency: task processor 必须设计为 idempotent. Best practices:
- Use task_id as key in downstream API (e.g., Stripe 用 `Idempotency-Key: {task_id}`)
- Read-modify-write 用 conditional update (e.g., `UPDATE orders SET status='paid' WHERE id=X AND status='pending'`)
- Side effects (email, SMS): mark sent_at in DB before sending, check before re-send

**6.2 Visibility timeout**

Default 5 min. Task `visibility_timeout_s` field per-task override.

```sql
-- Stuck task recovery (run every 30s by dispatcher cron)
UPDATE tasks SET state = 'queued', leased_by = NULL, leased_until = NULL
WHERE state = 'leased' AND leased_until < NOW();
```

Recovered task 不是 retry (attempts 不 ++), 因为 worker 可能没真正 fail, 只是 heartbeat 失败. 但 attempts 会在 next nack 时 ++.

**6.3 Heartbeat for long tasks**

10min task with 5min timeout — worker must heartbeat.

```python
async def send_heartbeat(task_id, interval=60):
    while True:
        await asyncio.sleep(interval)
        # Extend visibility
        await pg.execute("""
            UPDATE tasks SET leased_until = NOW() + INTERVAL '300 seconds'
            WHERE id = $1 AND leased_by = $2
        """, task_id, worker_id)
```

Heartbeat 每 1 min 续 5 min. Worker crashes → 4 分钟内 timeout expires → 自动 re-lease.

**6.4 Visibility timeout 设置**

- p99 expected duration × 2 是 sane default
- Override per-task type (training task 长, API call task 短)
- 太短: heartbeat overhead + spurious retry
- 太长: stuck task slow recovery

### Phase 7: Multi-tenant fairness (6 min)

**7.1 Per-tenant quota**

每 tenant 配 quota:
- `max_in_flight`: 同时 leased 上限 (e.g., paid=1000, free=100)
- `max_per_sec`: enqueue rate (e.g., paid=1000/s, free=10/s)
- `weight`: dispatch 时 share (paid=10, free=1)

```python
async def enqueue(task):
    # Rate limit
    if not await rate_limiter.try_acquire(task.tenant_id):
        raise HTTPException(429, "tenant rate exceeded")
    
    # In-flight quota
    in_flight = await pg.fetch_val("""
        SELECT COUNT(*) FROM tasks WHERE tenant_id = $1 AND state IN ('queued', 'leased')
    """, task.tenant_id)
    if in_flight >= tenant_config[task.tenant_id].max_in_flight:
        raise HTTPException(429, "tenant in-flight exceeded")
    
    # Proceed
    ...
```

**7.2 Weighted fair queueing in dispatcher**

Already covered in 4.4. Key: deficit round robin or weighted random.

**7.3 Burst absorption**

Big tenant burst (10K tasks in 1 sec): 
- Enqueue 接受 (有 rate limit at higher limit if paid)
- Dispatcher 按 weight 处理, 其他 tenant 不 starved
- Big tenant 自己 task 慢些, 因为他们 weight 不会让所有 worker dedicated 他们

**7.4 Per-tenant isolation (extreme)**

VIP 客户可能要 dedicated worker pool:
- Topology: extra workers labeled `tenant=acme`
- Dispatcher only assigns acme tasks to acme workers
- Other tenants's tasks 不会 starve acme

但 hardware cost up, 通常只 top-3 customer 用.

### Phase 8: Trade-offs + alternatives (7 min)

**Decision 8.1 — Backing store**

我推 Postgres + Redis hybrid. Alternatives:
- **Pure Redis Streams**: 100K TPS, 但 persistence weaker (AOF every sec, may lose 1s). 适合 ≤ 50K TPS + 容忍 1s 数据丢失
- **Pure Postgres SKIP LOCKED**: 10-30K TPS, durable, 适合 < 30K TPS
- **Combined**: Redis for peek + dedup, PG for durable state. 我们 case 10K TPS, 适合

**Decision 8.2 — vs Temporal**

| 维度 | Our queue | Temporal |
|---|---|---|
| Use case | Generic single-step task | Multi-step workflow with state |
| Complexity | Medium | High (workflow code patterns) |
| Throughput | 10K | 10K (similar) |
| Long-running | OK with heartbeat | Excellent (workers can crash, workflow continues) |
| Versioning | Manual | Built-in workflow version |
| Visibility | Custom dashboards | Temporal UI |

我推: queue 做 stateless task (90% case), Temporal 做 long workflow (10%). Two systems coexist.

**Decision 8.3 — vs SQS / Cloud Tasks**

| 维度 | Self-host | SQS |
|---|---|---|
| Ops | We run | Managed |
| Cost @ 10K TPS | Postgres $1K/m + Redis $500/m + ops | SQS $4K/m |
| Customization | Full | Limited (priority is hack) |
| Vendor | None | AWS |

If on AWS and < 50K TPS, SQS is no-brainer. 我们 self-host because cross-cloud + priority + per-tenant fairness customization.

**Decision 8.4 — Visibility timeout strategy**

| Strategy | Pros | Cons |
|---|---|---|
| Fixed 5 min | Simple | Bad for variable duration |
| Per-task type | Tuned | More config |
| Adaptive (worker reports estimated time) | Best | Complex |
| Per-task user-specified | Flexible | Trust users? |

我推 per-task-type + user override. Default by task type sane.

---

## 关键决策点 (with rationale)

1. **Postgres SKIP LOCKED + Redis hybrid** — 10K TPS sweet spot, durable, no new dependency.

2. **Stripe-style 阶梯 backoff** — pure exponential not adaptive to real failure modes (transient vs persistent), 阶梯 + jitter 经过 production verify.

3. **Idempotency at enqueue, idempotent processor** — defense in depth. Enqueue dedup catches duplicate submissions, processor handles late retries.

4. **Visibility timeout + heartbeat** — not "ack within X" model. Worker can extend dynamically.

5. **DLQ as state, not separate queue** — same table, state='dead'. Easier debugging + replay.

6. **Weighted fair queueing** — paid weight×10 dispatch share, but min 5% capacity for any tenant.

7. **Per-tenant quota at enqueue** — backpressure at producer is cheaper than dispatch-time fairness alone.

8. **Partition by month** — old completed tasks drop cheap, archival lossless.

9. **Error class taxonomy** — 4 categories drive different retry behavior (4xx fail fast, 5xx exponential, etc.).

10. **Observability per-tenant per-error-class** — debug stuck task: which tenant, which class, which worker. Tracing parent_task_id chain.

---

## 数字 (capacity sizing, cost math)

**Storage**:
- 10K TPS × 86400s × 7 day = 6 billion task rows (with 7d retention)
- Each row ~2KB (payload + meta) = 12 TB
- Partition monthly + drop after 30d → ~52GB hot
- Postgres Aurora cluster: db.r6g.4xlarge primary + 2 reader, ~$2K/month

**Redis** (sorted sets per tenant):
- 200 tenant × avg 10K ready tasks × 100B per entry = 200MB hot
- ElastiCache cache.r6g.large × 2 (HA): $250/month

**Workers**:
- Avg task 1s, 10K TPS → 10K workers concurrent
- m6i.large (2 vCPU, 8GB) handles ~50 tasks/sec (Python async)
- 10K / 50 = 200 workers × $100/month = $20K/month
- Autoscale to 50 idle off-peak

**Dispatcher**:
- 4 dispatcher pods (HA), m6i.xlarge: $400/month

**Total infra**: ~$25K/month for 10K TPS

**Cost per task**: 25K / (10K × 86400 × 30) = $0.000001/task = $1 per million

**Throughput proof**:
- Postgres SKIP LOCKED: 5K updates/sec sustained on Aurora r6g.4xlarge
- 4 dispatchers × 5K = 20K dispatches/sec ceiling
- 10K TPS dispatch headroom OK

**Failure budget**:
- DLQ rate < 0.1%: 10K TPS × 0.001 = 10 dead/sec max = 36K/hr — exceed → alert
- p99 enqueue < 10ms: Aurora write latency < 5ms + Redis < 1ms + network < 2ms

**SLO**:
- Availability: 99.95% (4 nine, ~4h downtime/year)
- Dispatch latency p99: high priority < 1s, low priority < 60s
- Retry budget: 95% tasks succeed within 8 attempts

---

## Gao Xin 简历专属 reframe

1. **TikTok PayLater BNPL job queue** — 你做过支付任务 queue (deposit / refund), 处理过 idempotency + retry + DLQ, 同样思路.

2. **Indonesia refund tier** — 你做过 multi-step refund workflow with retry + audit, 跟 task queue 模型同源.

3. **TikTok Voice agent task scheduler** — 你做过 worker pool + visibility timeout (call session 长), 直接套.

4. **Internal Agent Platform tool calling** — agent tool call 本质是 task, 你做过 priority + tenant isolation.

5. **BytePay rate limiting** — 你做过 token bucket + per-tenant quota, 跟这道题 multi-tenant fairness 同源.

reframe: "我在字节做 BNPL refund 时本质就是 task queue + retry + DLQ + audit, 那时用 Kafka + Postgres state machine. 这道题如果重做我会换 Postgres SKIP LOCKED + Redis 因为 long-running task 不适合 Kafka HOL blocking. Stripe 阶梯 backoff 我直接借鉴他们 public talk."

---

## 5 个 Follow-ups

1. **"如果一个 worker bug 永远 throw, 同一 task 重试 8 次都死, 怎么 prevent cascade?"** — 答: (a) Error class 'permission_denied' / '4xx' 直接 fail fast (1 retry then DLQ); (b) Per-task-type DLQ growth rate spike → auto-circuit-break (暂停 that task type 进一步 retry); (c) Per-worker error rate watch — 如果某 worker error 率高, drain + replace.

2. **"task 是 financial (转账), 怎么 ensure exactly-once?"** — 答: 真 exactly-once 不可能 in distributed. 我们要 effectively-once. (a) Idempotency key 在 producer + downstream API (Stripe Idempotency-Key); (b) Two-phase commit pattern: prepare → commit / abort, with retries safe; (c) Outbox pattern: task results + side effects 在同一 DB transaction (e.g., 转账 + 通知); (d) 如果 downstream not idempotent, 包一层 saga 或 use Temporal.

3. **"10K TPS 增长到 100K, 我们 architecture 撑不撑?"** — 答: Postgres SKIP LOCKED 极限 ~30K dispatch/sec. 100K 需要换 backend: (a) Shard Postgres by tenant_hash (4-8 shards); (b) Or move to Redis Streams (~100K/sec native); (c) Or Kafka (1M+ TPS) 但接受 long-running tradeoff (smaller batch + visibility hack). 我推 sharded Postgres < 50K, Kafka > 50K with workflow off-load to Temporal.

4. **"如果某 tenant 想看 their queue depth + DLQ, 怎么 expose?"** — 答: Per-tenant API. `GET /tenants/{id}/queue/stats` 返回 (queued_count, leased_count, dead_count, oldest_queued_at, avg_processing_time). 可选 webhook: 当 DLQ 增长触发, push event to tenant's URL.

5. **"Postgres 主挂了, 怎么 failover 不丢任务?"** — 答: (a) Aurora multi-AZ standby, RPO 0 (synchronous replication); (b) Failover < 60s (Aurora自动); (c) Workers see connection error → reconnect to new primary (idempotent retry); (d) In-flight leased task 不丢 (DB committed); (e) Heartbeat 在 failover 期间可能 missed → leased_until expires → re-lease normally. 关键: enqueue 和 ack 都 idempotent.

---

## ❌ 死路答法

1. **"Celery + RabbitMQ + retry decorator"** — 太浅, 没回答 fairness / DLQ / visibility.
2. **"Kafka 全套"** — Kafka 长 task HOL blocking + commit lag, 不适合.
3. **"用 in-memory queue"** — crash 全丢.
4. **"无 priority"** — 不答 priority 问题.
5. **"Exponential backoff 不加 jitter"** — thundering herd retry storm.
6. **"DLQ = log file"** — 不可 replay, 不可 query.
7. **"无 idempotency"** — duplicate task 双扣 / 双发送.
8. **"per-task random worker"** — 没 fairness, 大 tenant monopolize.
9. **"visibility timeout 不存在, ack 时间任意"** — worker crash 永远 stuck.
10. **"Auto-retry forever"** — zombie task 永久 stuck, DLQ 是 essential terminal state.

---

## ✅ 加分项

1. **Postgres SKIP LOCKED + Redis hybrid** — modern, 不 over-engineer
2. **Stripe-style backoff 引用** — production reference
3. **Error class taxonomy** drives retry behavior — staff sense
4. **Heartbeat + visibility timeout** — long task 正解
5. **Weighted fair queueing + deficit round robin** — multi-tenant fairness 深度
6. **DLQ as state, not separate queue** — operational simplicity
7. **Per-task-type visibility timeout** — pragmatic
8. **Backing store comparison matrix** — 完整 ecosystem 知识
9. **Temporal complementary, not competing** — 知道 workflow vs queue 区别
10. **Numbers 给得出来** (10K workers, $25K/month, $1/million tasks, p99 < 10ms enqueue)

---

## 一句话总结

10K TPS 任务队列不是 "Celery 装上", 是 **Postgres SKIP LOCKED + Redis sorted set + Stripe-style 阶梯 backoff + DLQ as state + idempotency at enqueue + visibility timeout with heartbeat + weighted fair queueing + per-tenant quota + error class taxonomy + per-tenant per-error observability** 一整套 production task queue 设计.

---

## Cheat Sheet

```
Backing store: Postgres SKIP LOCKED + Redis (sorted set, dedup)
              Aurora db.r6g.4xlarge × 3 = $2K/m
              ElastiCache r6g.large × 2 = $250/m

Capability mapping:
  Priority:     ORDER BY priority, scheduled_at
  Fairness:     WFQ (deficit round robin) by tenant weight
  Retry:        Stripe 阶梯 [30s, 2m, 10m, 1h, 6h, 24h, 3d, 7d] + ±20% jitter
  DLQ:          state='dead' in same table, 30d retention
  Idempotency:  Redis SET NX with 24h TTL on idem_key
  Visibility:   leased_until column, default 5min, override per-type
  Heartbeat:    Worker extends leased_until every interval/3
  Observability: per-tenant queue_depth, per-error-class DLQ rate

Error class:
  4xx (perm): fail fast (1 retry)
  5xx (trans): full backoff schedule
  timeout: full backoff
  rate_limit: respect Retry-After header
  unknown: full backoff

Schema (tasks):
  PK: id (UUID)
  Index: (state, priority, scheduled_at) PARTIAL where state='queued'
  Index: (leased_until) PARTIAL where state='leased'
  Index: (idempotency_key) UNIQUE per 24h
  Partition: monthly by created_at

Capacity (10K TPS):
  200 workers (50 task/s each, m6i.large)
  4 dispatchers (m6i.xlarge)
  6B rows/week → 12TB → 52GB hot after monthly drop

Cost:
  $25K/month all-in
  $1 per million tasks

vs alternatives:
  Kafka: 100K+ TPS but bad for 10min tasks (HOL block)
  Redis Streams: 100K TPS, less durable
  Temporal: workflow > queue, use for multi-step
  SQS: managed but no native priority/fairness

SLO:
  99.95% availability
  p99 enqueue < 10ms
  Dispatch high-pri < 1s
  Dispatch low-pri < 60s
  DLQ rate < 0.1%
```
