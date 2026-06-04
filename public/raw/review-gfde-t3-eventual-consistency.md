## T3.6 · eventual consistency — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](gfde-t3-eventual-consistency.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t3-eventual-consistency.html`](gfde-t3-eventual-consistency.html)

---
## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"agent 跑 5-step workflow: create_order → reserve_inventory → charge_payment → send_email → schedule_shipping. Step 3 (charge) times out. 不知道是否扣了. Step 4-5 没跑. Design recovery"**, 我按这 9 层回答, 不跳序.

### 📐 Agent Workflow Consistency — 9 层结构

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 |
|---|---|---|---|---|
| 1 | 为什么 2PC 不可行 | 1 min | 跨 vendor (Stripe / SendGrid / 内部 ERP) 没 global coordinator. Network partition 时 2PC 会无限 hang. CAP 下 AP 是 default, 必然 eventual | "Why 2PC fails — cross-vendor 没 global coordinator, network partition hang. CAP forces AP, eventual is the only path..." |
| 2 | Verify-on-timeout 起手 | 2 min | Step 3 timeout 不等于失败. 立刻调 Stripe `get_payment_status(idempotency_key)` 看真实状态. **3 outcome: succeeded / failed / unknown**. Unknown 必须 retry 同 idem_key | "First action — verify-on-timeout. Stripe `get_status(idem_key)`. Timeout 不等于 failure, 3 outcomes..." |
| 3 | Idempotency key 设计 | 2 min | Per-step idem_key, 不是 per-workflow. Key 格式: `{workflow_id}:{step_id}:{attempt_n}`. Stripe / SendGrid / Twilio 都支持 Idempotency-Key header. 24h TTL on provider side | "Idempotency-Key per step, format {workflow_id}:{step_id}:{attempt}. All major vendors support — Stripe / SendGrid / Twilio..." |
| 4 | 3 pattern 速选 | 2 min | **Saga** < 5 step + clear undo. **Outbox** 跨服务 no framework, Kafka push. **Workflow engine (Temporal/DBOS) 5+ step / 长 / audit-heavy**. 这题 5 step + audit-required → **Temporal** | "3 patterns — Saga short, Outbox cross-service, Temporal 5+ step. 这题 5 step + audit → Temporal..." |
| 5 | Temporal workflow as code | 3 min | `@workflow.defn` class, `execute_activity` 每步 durable. Retry policy per step (`maximum_attempts=3, exponential_backoff`). Crash 自动 replay from last checkpoint. Compensation 在 try/except 里写, framework 保证 reliable | "Temporal workflow as code — @workflow.defn, execute_activity 自动 durable + retry. Crash replay from checkpoint..." |
| 6 | Order matters (irreversible 后置) | 2 min | Email 后置 — `send_email` 不能 undo (refund email 用户已读). `schedule_shipping` 也是. **Irreversible step 一定在 payment 确认后**. Compensate 顺序: inventory release → order cancel (payment refund 单独 manual path) | "Order critical — irreversible (email, ship) 必须 after payment confirmed. Compensate reverse: inventory → order, payment refund manual..." |
| 7 | Compensation 自己失败怎么办 | 2 min | DLQ + ops manual intervention. 不能 silent fail. Alert PagerDuty + ticket 自动开. 财务级别 (refund > $200) 一定 human approval gate, 不全自动 | "Compensation 自己失败 → DLQ + PagerDuty + auto-ticket. 财务级别强制 human gate..." |
| 8 | Step 3 具体 recovery flow | 2 min | (1) verify_status → unknown (2) retry charge same idem_key, get answer (3) succeeded → continue step 4-5 (4) failed → compensate step 1-2: inventory.release + order.cancel + alert user "payment failed, retry later" | "Concrete recovery: verify → retry same idem → if succeeded continue, if failed compensate inventory + order + alert..." |
| 9 | 简历 resume hook | 90s | "Indonesia refund tier 3 (> $200) — 5-step Temporal workflow: lookup → risk → ledger → fund return → notify. Step 3 fail 自动 compensate 1-2, alert ops. **156K refund processed, 1.9% verify-on-timeout, 0 double-refund**. Temporal 比 hand-roll Saga dev velocity 3-4x, bug 少 70%" | "Indonesia refund tier 3 — Temporal 5-step. 156K processed, 1.9% verify-on-timeout, 0 double-refund..." |

### 🎯 为啥按这个序

2PC 不可行 直接关上面试官 "为什么不用 strong consistency" 的退路. Verify-on-timeout 是 timeout = unknown 这个核心洞察, 必须先讲. Idempotency key 是基础设施前提, 没它后面都白讲. 3 pattern 速选 是 framework, 这题答案是 Temporal — 要直接说出来. Temporal workflow as code 演示具体代码思维. Order matters 是踩过坑才知道 — irreversible 后置. Compensation 失败的 fallback 显示 ops mindset. Step 3 concrete recovery 是 "你能不能落地" 信号. 简历 hook 用 Indonesia refund 156K + 0 double-refund 是 hard number.

### 🔥 哪一层最容易被追问 deeper

**Layer 5 (Temporal mechanics)** — 追问 "Temporal 怎么 replay 不重复执行 side effect?". 回答: workflow code 必须 deterministic, side effect 都在 `execute_activity` 里, activity 结果记录到 Temporal history. Replay 时跳过已记录 activity, 从下一个未执行的开始. **Layer 3 (idempotency)** 追问 "idem_key 多久 TTL?". Stripe 24h, SendGrid 24h, Twilio 5 days. 跨 TTL retry 行为不确定, 应在 workflow 层算 deadline 控制. **Layer 7 (compensation fail)** 追问 "DLQ 谁消费". 回答: ops team 有专门 runbook + dashboard, P0 alert PagerDuty, P1 ticket. 财务级别 human gate 必须.

### ⏱ 时间压缩版 (30 min round)

1. 2PC 不行 + verify-on-timeout (2 min)
2. Idempotency key + 3 pattern 选 Temporal (3 min)
3. Temporal workflow as code + order matters (4 min)
4. Step 3 concrete recovery flow (2 min)
5. 简历: Indonesia refund 156K (1 min)

### 🆘 卡壳兜底 (针对这题)

1. **被问 "为什么不用 saga 而用 Temporal"**: Saga 在 5+ step 时 hand-roll state machine 复杂 + bug 多. Temporal framework 帮你管 state + retry + compensation, dev velocity 3-4x. 短 workflow (< 3 step) 反而 Temporal overkill
2. **被问 "exactly-once 怎么保证"**: 直接说 "exactly-once delivery 在分布式不存在, 只能 at-least-once + idempotency. Idempotency-Key 让 retry 安全, effectively-once"
3. **被问 "Temporal vs DBOS vs Inngest"**: Temporal 最成熟 (Uber Cadence 起源), 生态强但 self-host 复杂; DBOS 轻量 MIT 起源, Postgres-native; Inngest serverless 优. 2026 enterprise default 是 Temporal Cloud
4. **被问 "compensation 也 timeout 怎么办"**: 同样 verify-on-timeout 套路 — 调 status query 看 compensation 真实结果. 死循环时 fall back DLQ + human

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖 2PC fail / Saga / Outbox / Workflow / Verify-on-timeout 全量. 你的 **Indonesia refund** 是核心 hook.

### 🧠 核心心智模型 (1 sentence)

跨 vendor agent workflow **2PC 不可行** (network partition + coordinator failure + cross-vendor lock 不存在), 必须靠 **Saga (短) / Outbox (跨服务) / Workflow Engine (长 + 5+ step)** + **3 层 idempotency** + **verify-on-timeout** 保证最终一致.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| 2PC | Two-phase commit, coordinator prepare + commit | 单 DB 内 OK, 跨 vendor 不行 |
| Saga | Forward + compensating action per step | < 5 步 + all reversible |
| Outbox | Intent table in same TX as biz state | 跨 service 可靠 publish |
| Workflow Engine | Temporal / DBOS, durable state as code | 5+ 步 / long-running |
| Compensating action | 反向 undo (refund, cancel, release) | Saga 必备 |
| Idempotency key | 同 key 多次 call 同 effect | retry safety |
| Vendor Idempotency-Key | Stripe / PayPal header honor | 防 double-charge |
| FOR UPDATE SKIP LOCKED | Postgres multi-worker outbox poll | 不冲突 dispatch |
| Verify-on-timeout | call → timeout → get_status(idem_key) → reconstruct or retry | uncertain state |
| Activity (Temporal) | retryable, durable step | LLM / tool call |
| Workflow state | Temporal 持久化 history, replay-able | crash recovery |
| Agent-as-workflow | LLM agent step = activity | 复杂 agent |
| Compensation 不可逆 | refund 退一半 / email 发了不能撤 | order matters |
| DLQ | dead-letter queue for failed compensations | manual recovery |
| Uncertain state | downstream status 未知, escalate ops | verify-on-timeout 出口 |

### 🎯 4 个核心 framework

**Framework 1: 2PC vs Eventual (When 2PC Fails)**
- When: 任何 cross-vendor agent
- Algorithm: 2PC 需要 coordinator + locking + atomic commit; 跨 vendor 这三都没
- Trade-off: strong consistency 不可能 → 接受 eventual
- Tools: SAGA / Outbox / Temporal, NOT 2PC

**Framework 2: Saga Pattern**
- When: < 5 步 + 每步 reversible + 简单
- Algorithm: try forward; on fail → reverse compensate completed steps
- Trade-off: compensation 也可能 fail → DLQ + manual escalation
- Tools: Temporal SAGA orchestrator, custom state machine

**Framework 3: Outbox Pattern**
- When: 跨 service, 不 framework lock-in
- Algorithm: tx { biz_action + outbox.insert(intent) }; worker poll FOR UPDATE SKIP LOCKED → publish to Kafka → mark published
- Trade-off: at-least-once 保证, consumer dedup 必须
- Tools: Postgres outbox table, Kafka publish, idempotency key

**Framework 4: Workflow Engine (Temporal / DBOS)**
- When: 5+ 步 / long-running (天/周) / multi-vendor / audit
- Algorithm: @workflow.defn + execute_activity with retry_policy + workflow state persistent
- Trade-off: framework lock-in vs handroll bug-prone
- Tools: **Temporal**, **DBOS**, Inngest

### 🌳 关键决策树 (ASCII)

```
Consistency pattern选哪个?
  ├─ < 3 步 + 全 reversible ── Saga DIY 简单
  ├─ 跨 service + no framework ── Outbox + Kafka
  ├─ 5+ 步 / 长时 / audit ── Workflow Engine (Temporal) ⭐
  └─ 单 DB ACID 内 ── direct transaction (2PC fine)

Idempotency 怎么做?
  L1 Redis SETNX (fast, in-flight protect)
  L2 DB unique constraint (durable safety net)
  L3 Vendor Idempotency-Key (Stripe, PayPal honor)
  → 3 层叠 safe-by-design

Timeout 怎么处理?
  call with idem_key + timeout 10s
  → timeout: sleep 5s, call get_status(idem_key)
     - completed → reconstruct from response
     - not_found → safe retry
     - failed → compensate
     - in_progress → wait + recheck
     - uncertain → escalate ops UI
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: Why 2PC Fails for Agents — Cross-Vendor**

```
2PC 步骤:
  1. Coordinator → 各 participant: PREPARE
  2. Participant: vote YES (lock resource) / NO
  3. Coordinator: 全 YES → COMMIT, 否则 ABORT
  4. Participant: ack

跨 vendor failure:
  - Vendor 不接受 external coordinator (Stripe 不会 PREPARE then 等你 COMMIT)
  - Network partition: coordinator down → participants 一直 lock
  - Latency: cross-vendor 2PC 多 round-trip = 10s+
  - Stripe / Salesforce / SMTP 各自 commit semantic 不同
  → 工程师都明白 2PC 跨 vendor impossible
```
- When 2PC still works: 单 DB / 单 cluster 内部 (Postgres + XA), 不出 vendor 界
- Top 3 gotchas: (1) 候选人不能直接说 "用 2PC" (面试官 confirm 你不懂) (2) 知道 saga / outbox 名称 (3) Indonesia refund 你说试过 2PC 不行
- Tools: PostgreSQL prepared transactions (within), Temporal SAGA cross-vendor

**Problem 2: Saga Pattern + Compensating Actions**

```python
class SagaOrchestrator:
    async def run(self, steps):
        completed = []
        try:
            for step in steps:
                result = await step.forward(idempotency_key=step.idem_key)
                completed.append((step, result))
            return [r for _, r in completed]
        except Exception as e:
            # Compensate in reverse
            for step, result in reversed(completed):
                try:
                    await step.compensate(result, idempotency_key=step.idem_key + ":undo")
                except Exception as ce:
                    # Compensation failed → DLQ
                    dlq.send(step, result, ce)
                    page_ops(step, ce)
            raise

# Example: Indonesia refund 5-step
steps = [
    Step("lookup_customer", forward=lookup, compensate=noop),
    Step("risk_score", forward=score, compensate=noop),
    Step("write_ledger", forward=ledger_insert, compensate=ledger_reverse),
    Step("fund_return", forward=trigger_return, compensate=cancel_return),
    Step("send_confirmation", forward=send_sms, compensate=send_correction_sms),
]
```
- Top 3 gotchas: (1) compensation 自己也可能 fail → DLQ + manual (2) compensation 不 idempotent (3) order matters: email LAST (after all confirmed)
- Tools: Temporal SAGA, custom state machine, DLQ via Kafka topic

**Problem 3: Outbox Pattern + Idempotency 3-tier**

```python
# Outbox write in same transaction as business state
async def step_with_outbox(workflow_id, step_name, biz_action, event_payload):
    async with db.transaction():
        await biz_action()  # e.g., update order status
        await db.execute("""
            INSERT INTO outbox (id, workflow_id, step_name, event_type, payload,
                                 idempotency_key, status, created_at)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, 'pending', now())
        """, workflow_id, step_name, "send_confirmation",
            event_payload, f"{workflow_id}:{step_name}")

# Worker (multi-instance safe)
async def outbox_worker():
    while True:
        rows = await db.fetch("""
            SELECT * FROM outbox WHERE status = 'pending'
            ORDER BY created_at LIMIT 100
            FOR UPDATE SKIP LOCKED
        """)
        for row in rows:
            try:
                await kafka.produce("events", row.payload,
                                     headers={"Idempotency-Key": row.idempotency_key})
                await db.execute("UPDATE outbox SET status='published' WHERE id=$1", row.id)
            except Exception:
                await db.execute("UPDATE outbox SET attempts=attempts+1 WHERE id=$1", row.id)

# Idempotency 3-tier:
# L1 Redis SETNX (fast in-flight lock)
async def check_in_flight(idem_key):
    return await redis.set(f"in_flight:{idem_key}", "1", nx=True, ex=300)

# L2 DB unique constraint backup
# CREATE UNIQUE INDEX idx_idem ON outbox(idempotency_key);

# L3 Vendor side (Stripe)
# headers: {"Idempotency-Key": "wf123:charge_card"}
```
- Idem key 结构: `{workflow_id}:{step_name}` deterministic, 同 workflow 重试同 key
- Top 3 gotchas: (1) outbox 没 FOR UPDATE SKIP LOCKED → 多 worker 重发 (2) idem key 用 timestamp (retry 不 same) (3) cleanup 不删 published row → outbox 表无限大
- Tools: Postgres outbox, Kafka publish, Redis SETNX, Stripe Idempotency-Key header

**Problem 4: Workflow Engine (Temporal / DBOS) — When + Agent-as-Workflow**

```python
# Temporal workflow as code
@workflow.defn
class RefundWorkflow:
    @workflow.run
    async def run(self, refund_request):
        # Each activity: retryable, durable, replay-safe
        customer = await workflow.execute_activity(
            lookup_customer, refund_request.customer_id,
            retry_policy=RetryPolicy(maximum_attempts=3, backoff_coefficient=2.0)
        )
        score = await workflow.execute_activity(risk_score, customer)
        
        if score > 0.8:
            # Long-running pause: wait for human approval
            approval = await workflow.wait_condition(
                lambda: self.approval_received, timeout=timedelta(hours=24)
            )
            if not approval:
                raise ApprovalTimeout
        
        ledger_id = await workflow.execute_activity(write_ledger, refund_request)
        try:
            await workflow.execute_activity(trigger_fund_return, ledger_id)
        except ActivityError:
            # Auto compensate
            await workflow.execute_activity(reverse_ledger, ledger_id)
            raise
        await workflow.execute_activity(send_sms, customer.phone)

# Agent-as-workflow pattern for LLM agents:
# - LLM call = activity (retryable)
# - Tool call = activity (idempotent)
# - Conversation state = workflow state (durable)
# - Loop = workflow.execute_activity in for loop
# - Long pause = workflow.wait_condition (human-in-loop)
```
- When NOT to use Temporal: simple < 3 step, all reversible, no audit need
- Top 3 gotchas: (1) activity 不 idempotent (Temporal retry double-execute) (2) workflow body call non-deterministic code (random / time / network) → replay broken (3) workflow_id 重复 → Temporal reject
- Tools: **Temporal Cloud / SDK**, **DBOS** (Postgres-centric), Inngest

**Problem 5: Verify-on-Timeout Pattern**

```python
async def call_with_verify(idem_key, action, timeout=10.0):
    try:
        return await asyncio.wait_for(action(idem_key), timeout=timeout)
    except asyncio.TimeoutError:
        # Settle delay, then probe
        await asyncio.sleep(5)
        status = await vendor.get_status(idem_key)
        
        if status == "completed":
            return await vendor.reconstruct(idem_key)  # fetch result by idem
        elif status == "not_found":
            # Safe to retry (vendor never saw it)
            return await action(idem_key)
        elif status == "failed":
            raise OperationFailed(status.reason)
        elif status == "in_progress":
            # Wait + recheck up to 60s
            await asyncio.sleep(10)
            return await call_with_verify(idem_key, action, timeout=30)
        else:
            # Uncertain → escalate to ops UI for manual reconciliation
            await ops_queue.escalate(idem_key, "uncertain_state")
            raise UncertainState(idem_key)

# Vendor-side get_status requirements:
# - Honor idempotency key indexing (5-day window minimum)
# - Return canonical status + idempotent fetch of result
# - SLA < 200ms for get_status
```
- Production data (Indonesia refund 6 months): 156K refunds, 1.9% verify-on-timeout triggered, of those 93% auto-recover via get_status, 0.4% escalate to ops
- Top 3 gotchas: (1) timeout 太短 + sleep 太短 → 边缘 case 仍 retry (2) vendor get_status latency 高 → block (3) uncertain 不 escalate → silent corrupt
- Tools: vendor get_status (Stripe / PayPal honor), Temporal as orchestrator, custom ops UI dashboard

### 🔥 Production gotchas (top 15)

1. **2PC for cross-vendor**: impossible, 候选人不能说
2. **In-memory state**: crash 时 lost
3. **Retry without idempotency**: double-execute
4. **No verify on timeout**: uncertain state silent
5. **No compensating action**: forward-only, partial commit 不能 undo
6. **Compensation 也 fail**: 没 DLQ + manual escalation path
7. **Email before payment confirmed**: order matters, email LAST
8. **Workflow_id 重复**: Temporal reject 或 state corrupt
9. **Compensation 不 idempotent**: retry compensation 双 undo
10. **No timeout per step**: 一步 hang forever
11. **Outbox 没 FOR UPDATE SKIP LOCKED**: 多 worker 重发
12. **Idem key 用 timestamp**: retry 不 same → 不 dedup
13. **Workflow body non-deterministic**: replay broken
14. **Cleanup 不删 published outbox**: 表无限大
15. **Uncertain state 不 escalate**: silent corrupt

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Saga + compensation | Indonesia refund tier | "5-step Temporal Saga, 156K refunds, 0 double-refund" |
| Verify-on-timeout | Indonesia refund | "1.9% trigger verify-on-timeout, 93% auto-recover, 0.4% ops escalate" |
| Outbox pattern | TikTok payment | "Postgres outbox + Kafka publish, 0 event lost in 12 months" |
| Idempotency 3-tier | Voice agent SMS | "Redis SETNX + DB unique + vendor Idempotency-Key, 0 double SMS" |
| Workflow engine | Indonesia refund | "Temporal workflow as code, 5+ step durable, dev velocity 3-4x vs handroll" |
| Agent-as-workflow | Internal Agent Platform | "LLM call = activity, conversation = workflow state, crash auto-replay" |
| 2PC tried + abandoned | Cross-vendor refund | "Tried 2PC week 1, network partition + Stripe no PREPARE, moved Saga week 2" |
| DLQ + ops UI | Indonesia refund ops | "Failed compensations → DLQ, ops dashboard manual reconcile" |

### 🎤 面试现场 quotables (top 8)

1. "Cross-vendor 2PC is impossible — coordinator failure + no PREPARE + network partition; eventually consistent only"
2. "Saga short / Outbox cross-service / Workflow Engine (Temporal) for 5+ step long-running — pick by complexity"
3. "Idempotency 3-tier: Redis SETNX (fast) + DB unique (durable) + vendor Idempotency-Key (Stripe)"
4. "Indonesia refund 5-step Temporal Saga: 156K processed, 0 double-refund, 1.9% verify-on-timeout"
5. "Order matters: email LAST after all confirmed, irreversible last or use delayed queue"
6. "Verify-on-timeout: timeout → sleep 5s → get_status by idem_key → completed / not_found / failed / in_progress / uncertain"
7. "Outbox: tx { biz + outbox.insert }, worker FOR UPDATE SKIP LOCKED, Kafka publish, dedup downstream"
8. "Agent-as-workflow with Temporal — LLM call = activity, conversation = workflow state, crash auto-replay"

### 🚨 红线 (top 10 anti-patterns)

1. 2PC for cross-vendor (impossible)
2. In-memory state (lost on crash)
3. Retry no idempotency (double-execute)
4. No verify on timeout (uncertain silent)
5. No compensating action
6. No DLQ for compensation failures
7. Email before payment confirmed (order)
8. Workflow_id duplicate
9. Compensation not idempotent
10. No timeout per step

### 📊 Indonesia refund production stats (你的 hook)

```
6-month data:
  156K refunds processed
  0 double-refund
  1.9% trigger verify-on-timeout (network blip / vendor slow)
    of those: 93% auto-recover via get_status
    of those: 0.4% escalate ops manual reconcile
  100% audit trail
  P99 refund completion: 8.5s (multi-step)
  Compensation triggered: 0.3% (most catch in step 4 = trigger_fund_return)

Stack:
  Temporal Cloud + Postgres outbox + Kafka events
  Stripe Idempotency-Key + Redis SETNX in-flight
  Ops dashboard React + Postgres + custom replay tool
```

### 🧰 2026 工具栈 quick lookup

| 类别 | 默认 | Alt | 你用过 |
|---|---|---|---|
| Workflow engine | Temporal Cloud / SDK | DBOS, Inngest | Temporal ✅ |
| Outbox store | Postgres | MySQL | Postgres |
| Event bus | Kafka | NATS, RabbitMQ | Kafka |
| Idempotency cache | Redis SETNX | Memcached | Redis |
| Vendor idem | Stripe / PayPal honor header | — | Stripe |
| DLQ | Kafka DLQ topic | Cloud Tasks DLQ | Kafka |
| Audit log | Postgres append-only + GCS | Firestore / Bigtable | Postgres + GCS |
| Ops UI | Custom React + Temporal Web | Retool | Custom |
| Replay | Temporal replay debugger | custom | Temporal |
| Saga orchestrator | Temporal SAGA | custom state machine | Temporal |

### 🎬 45-min 节奏 (T3.6 专属)

```
0-5    Clarify    "Step count? Cross-vendor? SLA? Audit? Tenant?"
5-10   Mental     "2PC impossible cross-vendor; eventual via Saga/Outbox/Temporal"
10-25  Pattern    Saga + compensation, Outbox + worker, Workflow engine
25-35  Idempotency 3-tier + verify-on-timeout + vendor Idempotency-Key
35-42  Production  Indonesia refund 156K + DLQ + ops escalate
42-45  Resume      "Indonesia refund 0 double, TikTok outbox 0 event lost"
```

### 🔢 关键 production 数字

- Indonesia refund: 156K processed, 0 double-refund, 1.9% verify-on-timeout
- Of verify-on-timeout: 93% auto-recover via get_status, 0.4% ops escalate
- TikTok payment outbox: 0 event lost in 12 months
- Voice agent SMS: 0 double-SMS via 3-tier idempotency
- Temporal vs handroll: 3-4x dev velocity, significantly less bug
- 2PC tried: week 1 → abandoned → Saga week 2 (cross-vendor case)
- P99 multi-step refund: 8.5s
- Compensation trigger rate: 0.3% (most in fund_return step)
- Idempotency key TTL (vendor side): 5 days minimum (Stripe spec)

### 🧠 mental model anchors

- "2PC is impossible cross-vendor"
- "Saga short / Outbox cross-service / Temporal long"
- "Idempotency 3-tier: Redis + DB unique + vendor"
- "Order matters: email LAST"
- "Verify-on-timeout: get_status → 5 outcomes"
- "Agent-as-workflow: LLM = activity, conversation = state"
- "DLQ + ops UI for stuck workflow"
