# 🔁 T3.6 · Eventual Consistency for Agent State (Multi-step) — 冲刺版

> 完整版: [gfde-t3-eventual-consistency.html](gfde-t3-eventual-consistency.html). 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: 5-step agent workflow (create_order → reserve_inventory → charge_payment → send_email → schedule_shipping), charge reversible (refund 24h), email irreversible (recall 60s), latency tolerance minutes, ~99% per-step success, async background OK, multi-vendor (Stripe + SMTP + carrier)."

**核心 framing**: 2PC fails cross-vendor (vendor 不支持 + network partition + coordinator block). 必须 accept eventual consistency. **Saga + Outbox + idempotency + verify-on-timeout + Temporal/DBOS** 是 staff-level 答案.

### Layer 1: 为什么 2PC 不行 (cross-vendor)

```
Coordinator → Salesforce: prepare (锁 lead)      ← Salesforce 没 prepare endpoint
Coordinator → PayPal: prepare (锁 fund)          ← PayPal 没
Coordinator → Twilio: prepare (锁 SMS slot)      ← 也没

即便支持: latency 5s+ unacceptable, network partition coordinator 死锁
→ Saga + compensating + verify-on-timeout 是 reality
```

### Layer 2: Saga pattern (forward + compensating)

```python
@workflow.defn
class OrderWorkflow:
    async def run(self, order):
        completed = []
        try:
            await activity.execute(create_order, idem_key, retry_policy)
            completed.append(("create_order", order))
            await activity.execute(reserve_inventory, idem_key)
            completed.append(...)
            charge = await activity.execute(charge_payment, idem_key)
            completed.append(...)
            await activity.execute(schedule_shipping, idem_key)
            await activity.execute(send_email, ...)   # email LAST (irreversible)
            return OrderSuccess
        except ActivityError as e:
            await compensate(reversed(completed))     # 反向 undo
            raise

COMPENSATION = {
    "create_order": cancel_order,           # set status=cancelled
    "reserve_inventory": release_inventory, # free stock
    "charge_payment": refund_payment,       # void / refund
}
```

**Order matters**: email 在 charge 后 (不可 recall). 1→2→3→shipping→email. 早期版本 email 在 charge 前: charge 失败但已发 "paid" 邮件 → user 困惑.

### Layer 3: Idempotency 3-tier + verify-on-timeout

```python
idem_key = f"wf_{workflow_id}:step_{step_name}"  # 确定性, 同 retry 同 key

async def step_3_charge(order, idem_key):
    try:
        return await payment_api.charge(amount, idem_key, timeout=30)
    except Timeout:
        await asyncio.sleep(5)  # let downstream settle
        status = await payment_api.get_status(idem_key)
        if status == 'completed':   return reconstruct_from_status(status)
        elif status == 'not_found': return await payment_api.charge(...)  # safe retry
        elif status == 'failed':    raise StepFailed(status.reason)
        else:                       raise UncertainState(idem_key)  # escalate ops
```

3-tier idempotency: Layer 1 Redis SETNX (fast in-flight protection) + Layer 2 DB unique constraint (durable safety net) + Layer 3 vendor-side Idempotency-Key header (Stripe / PayPal honor).

### Layer 4: Outbox pattern (durable intent + event)

```python
with db.transaction():
    business_action()  # e.g., update order status
    outbox.insert({
        "id": uuid4(),
        "action": "send_email",
        "args": {...},
        "status": "pending",
        "idempotency_key": uuid4(),
    })

# Background worker:
while True:
    pending = outbox.fetch(status="pending", FOR UPDATE SKIP LOCKED, limit=100)
    for item in pending:
        try:
            execute_action(item.action, item.args, item.idempotency_key)
            outbox.update(item.id, status="done")
        except Exception as e:
            outbox.update(item.id, error=str(e))  # retry with backoff
```

保证 "业务变更 + 事件 atomic" — 不会出现业务改了但事件没发. FOR UPDATE SKIP LOCKED 让 multi-worker safe.

### Edge cases

- **EC1 Email 已发但 charge 后被 refund (compensation 反序)**: **Reorder** — email LAST after payment confirmed durable. Standard pattern. If reorder impossible: delay email N seconds + check workflow state before sending. Apology + recovery message if still happens.
- **EC2 Compensation 自己 fail**: **DLQ** for failed compensations → P1 PagerDuty alert ops → manual reconciliation UI. Compensation 必须 more reliable than forward — heavy retry (max_attempts=10, exp backoff), multiple methods (API + batch file fallback), manual escalation last resort.
- **EC3 Workflow engine 何时不用 Temporal**: simple <3 step all reversible (DB transaction 够), high-freq microsecond (overhead too much), greenfield 小 team (roll-your-own later migrate), tightly coupled single DB.
- **EC4 Agent middle workflow LLM service down**: Temporal pause workflow + user "still processing" + LLM recover → resume from last activity. >5min: alert ops + customer comm. >30min: SLA breach + credit policy.
- **EC5 Cross-region DR**: Temporal cluster replication multi-region active-active, workflow resume in other region if primary down. Eventually consistent — workflow 可能 execute twice cross-region (rare race). Idempotency key still works. Vendor handles dedup. RPO <1s, RTO <5min.

### Production hardening

- **Compensation tested in chaos mode**: random step failure injection, verify compensation properly undoes. Weekly chaos test.
- **DLQ + ops UI**: failed compensations queue, manual reconciliation UI shows vendor status + internal status + audit log, ops resolves with action.
- **Audit log per state change**: every activity start/complete/fail logged with workflow_id, step, output, retry_count.

### 🪝 Resume hook

"Indonesia refund at TikTok PayLater was my biggest distributed-systems learning. **5-step Saga**: verify_eligibility → get_approval (tier-based, may pause for human 24h) → reverse_charge (vendor API) → update_balance → notify_user. Key patterns landed: (1) Saga not 2PC — vendor APIs 不支持 2PC; (2) idempotency key per step `wf_{refund_id}:step_{name}`, vendor honors Idempotency-Key header; (3) verify-on-timeout for step 3, **1.9% timeout rate, 93% recoverable via get_status, 0.4% escalated ops**; (4) Outbox for durable state; (5) Temporal-style orchestration (rolled own pre-Temporal, would use Temporal now); (6) DLQ + ops UI. **Result: 156K refunds 6 months, 0 double-refund**. Hard lesson: **email LAST** — early version emailed 'refund processed' before charge_reverse confirmed."

---

## 🔥 5 Follow-ups

**Q1: Email 发了之后 payment compensation refund 了. User 收到 'paid' 但实际 refunded. Bad UX, 怎么 handle?**
**Reorder**: email LAST (after payment durably confirmed). Standard pattern. If reorder impossible: **delay** email N seconds, check workflow state before sending. **Apology + recovery message**: send follow-up explaining. **Quarantine** if compensation in flight: hold downstream actions.

**Q2: Saga compensation 自己 fail. Now what?**
**DLQ** for failed compensations → **P1 PagerDuty alert** human ops → **manual reconciliation UI** for ops to inspect + resolve. **Compensation must be more reliable than forward** — heavy retry policy (max_attempts=10, exp backoff) + multiple methods (refund via API, then via batch file) + manual escalation last resort. Production: 3 DLQ over 6 months, all <24h resolved manually.

**Q3: Workflow engine 增加 operational complexity. 何时 NOT use Temporal?**
**Simple workflows** (<3 steps all reversible) — direct DB + retries 够. **High-frequency microsecond** — Temporal overhead too much. **Greenfield + small team** — roll-your-own initial, can migrate later. **Tightly coupled single DB** — DB transaction 够简单. **Use Temporal when**: >5 steps, long-running (hours-days), multi-vendor, audit required, multiple workflow types. **DBOS** as lighter Postgres-centric alternative.

**Q4: Agent middle workflow LLM service down. User 看到啥?**
Workflow paused (Temporal handles automatically). User notified "still processing". LLM service recovers → workflow resumes from durable state (last successful activity). If LLM down >5min: alert ops + customer comm "we're investigating". Eventually consistent — finish when service back. User SLA breach if >30min — credit policy.

**Q5: Multi-turn agent conversation - eventual consistency for state?**
Each turn: read state → LLM → tool calls → write state (all in 1 workflow execution). State stored in DB (durable) + Redis (warm cache). If race (user sends 2 msgs fast): serialize via lock per conversation_id, or queue. Workflow engine handles: per-conversation_id workflow instance, queued events. Or stateless API: each turn load state from DB, process, write back (DB is source of truth).

---

## ❌ 易错点 (10 条红线)

1. **2PC for cross-vendor** — impossible at scale (vendor 不支持 + network partition)
2. **In-memory workflow state** — lost on crash, no resume
3. **Retry without idempotency** — double-execute (double charge 灾难!)
4. **No verify on timeout** — don't know if executed, blind retry
5. **No compensating action per step** — Saga incomplete, hang on failure
6. **No DLQ for compensation failures** — silent stuck
7. **Email before payment confirmed** — UX bug, "paid" email then refund
8. **Workflow_id 重复** — Saga runs twice, double business action
9. **Compensation not idempotent** — double-compensate corrupt state
10. **No timeout per step** — hang on vendor slow indefinitely

---

## ✅ 加分项 (12 条)

1. **Saga pattern** explicitly explained (forward + compensating reverse order)
2. **Outbox** for durable state + atomic event (FOR UPDATE SKIP LOCKED)
3. **Idempotency key per step** with **3-tier** (Redis + DB + vendor)
4. **Verify-on-timeout pattern** with `get_status(idem_key)` resolution
5. **Temporal / DBOS workflow engine** recommendation with rationale
6. **Compensating handlers** designed **upfront per step**
7. **DLQ for compensation failures** + ops manual reconciliation UI
8. **Order of operations** considered (email LAST, irreversible 后置)
9. **Cross-region disaster recovery** awareness
10. **Agent-as-workflow** pattern (LLM call = activity, tool call = activity)
11. **Production case study** (Indonesia refund 156K / 0 double / 1.9% verify-on-timeout)
12. **Quote Indonesia refund tier** experience directly

---

## 一句话总结

**Agent workflow eventual consistency = Saga (forward + compensating) + Outbox (durable intent) + Idempotency key per step + Verify-on-timeout (get_status) + Workflow engine (Temporal / DBOS) for >5 step orchestration**. 2PC fails cross-vendor (network partition + no vendor support). Must accept eventual consistency. Design every step's compensating handler upfront. Test compensation in chaos mode. DLQ + ops manual review for the <1% truly uncertain.

---

## 🃏 Cheat Sheet (印 1 页随身)

```
Why eventual consistency: multi-vendor (Stripe/SF/SMTP) no 2PC support / network partitions / latency prohibitive / coordinator block

Saga pattern: forward + compensating per step, on fail compensate reverse order, per-step idempotent+retryable, **compensation MUST be more reliable than forward**

Outbox pattern: business + outbox event in SAME DB TX, reliable worker FOR UPDATE SKIP LOCKED reads outbox publish to Pub/Sub mark done, cleanup after N days

Idempotency 3-tier:
  L1 Redis SETNX (fast in-flight protection)
  L2 DB unique constraint (durable safety net)
  L3 Vendor Idempotency-Key (Stripe/PayPal honor)
Idem key: `workflow_id + step_name` deterministic, same on retry

Verify-on-timeout (critical):
  try execute w/ idem_key, catch timeout:
    sleep 5s → get_status(idem_key)
    completed → reconstruct / not_found → safe retry
    failed → compensate / uncertain → escalate ops

Compensation: upfront defined + idempotent + chaos tested + heavy retry + DLQ + manual escalation

Workflow engine: Temporal ⭐ >5 steps long-run multi-vendor audit / DBOS Postgres lighter / Cloud Tasks simple / DIY <3 steps all reversible

Agent-as-workflow: LLM call=activity / Tool call=activity (idempotent) / conv state=workflow state / long pause=wait_condition

Order matters: email LAST (after confirmed), reversible before irreversible
Ops: DLQ + manual reconciliation UI + audit log per state change

Production (Indonesia refund 6mo): 156K refunds, 0 double-refund, 1.9% verify-on-timeout, 93% auto-recover, 0.4% ops, 3 DLQ all <24h

Models: Strong/Linearizable(Spanner)/Sequential/Causal/Eventual ⭐
Patterns: 2PC(fail x-vendor)/Saga ⭐/Outbox+CDC/Choreography/Orchestration Temporal ⭐

红线:
  - 2PC cross-vendor (impossible)
  - In-memory state (lost on crash)
  - Retry without idempotency (double-execute)
  - No verify on timeout
  - No compensating action
  - No DLQ
  - Email before payment confirmed
  - Workflow_id duplicate
  - Compensation not idempotent
  - No timeout per step

Resume quotes:
  "Indonesia refund: 5-step Saga, 156K refunds, 0 double"
  "TikTok payment Outbox, 0 event lost 12 months"
  "Voice agent SMS idempotency key per message"
  "Tried 2PC cross-vendor, abandoned in a week, moved Saga"
  "1.9% verify-on-timeout, 93% auto-recover"
```
