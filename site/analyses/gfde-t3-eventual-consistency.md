## 题目

> "Agent executes a **5-step workflow**: create_order → reserve_inventory → charge_payment → send_confirmation_email → schedule_shipping. **Step 3 (charge_payment) times out**. You don't know if charged. **Step 4 + 5 didn't run yet**. Design recovery."

或追问形态:

> "Why is **eventual consistency** unavoidable for agentic workflows? Walk through Saga, Outbox, and when to use Temporal."

**Round**: Distributed Systems / Agent Reliability (45-60 min)

---

## 这道题在考什么

考你**distributed transaction patterns** applied to agent workflows:

1. **2PC 为什么不行** —— 多 vendor, no global coordinator
2. **Saga pattern** —— forward + compensating
3. **Outbox pattern** —— transactional + reliable event
4. **Workflow engine** —— Temporal / DBOS
5. **Idempotency** —— retry-safe everywhere

---

## 必问 clarifying

**1. Reversibility**

> "Each step — reversible (refund) or irreversible (email sent)?"

**2. Latency tolerance**

> "Can finish workflow in 100ms / 10s / minutes / hours?"

**3. Failure rate**

> "Each step success rate? 99% × 5 = 95% workflow success. Lower → need retry."

**4. Customer-visible**

> "User waits for confirm or async background?"

**5. State store**

> "Have a workflow engine (Temporal) or roll-your-own with DB?"

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify reversibility / latency / failure rate |
| 5-15 min | Why 2PC fails, why eventual consistency |
| 15-25 min | Saga pattern (forward + compensating) |
| 25-35 min | Outbox pattern + idempotency |
| 35-45 min | Temporal / workflow engine choice |

---

## 我会这样答（sample）

> "Clarify — *[假设: charge reversible (refund), email irreversible (recall window 60s), latency tolerance minutes, ~99% per step, async background OK]*.
>
> **Why eventual consistency for this workflow**:
>
> - Each step is a **separate service** (inventory, payment, email, shipping). No global transaction.
> - 2PC requires all participants vote — but vendor APIs (payment provider) don't speak 2PC.
> - Latency to coordinate 2PC across vendors prohibitive.
> - Network partitions guaranteed at scale.
>
> So: **forward execution + compensating actions on failure** = Saga pattern.
>
> **Saga design for our workflow**:
>
> ```
> Step 1: create_order              ← compensate: cancel_order
> Step 2: reserve_inventory          ← compensate: release_inventory
> Step 3: charge_payment             ← compensate: refund_payment
> Step 4: send_confirmation_email    ← compensate: recall_email (within 60s) or send_apology
> Step 5: schedule_shipping          ← compensate: cancel_shipping
> ```
>
> **State machine**:
>
> ```
> [Start]
>   → [Step 1 running] → success → [Step 2 running] → success → [Step 3 running]
>                                                                       ↓
>                                                                  timeout
>                                                                       ↓
>                                                              [Step 3 status uncertain]
>                                                                       ↓
>                                                          Verify (idempotent get_payment_status)
>                                                                       ↓
>                                                          ┌──────────────┐
>                                                          ↓              ↓
>                                                  charged: continue   not_charged: retry step 3
> ```
>
> **For step 3 timeout specifically**:
>
> ```python
> async def step_3_charge(order, idem_key):
>     try:
>         result = await payment_api.charge(
>             amount=order.total,
>             account=order.account,
>             idempotency_key=idem_key,
>             timeout=30,
>         )
>         return result
>     except Timeout:
>         # DON'T retry blindly — first VERIFY state
>         await asyncio.sleep(5)  # give downstream time to settle
>         status = await payment_api.get_status(idem_key)
>         if status == 'completed':
>             return reconstruct_result(status)
>         elif status == 'failed' or status == 'not_found':
>             # Safe to retry
>             return await step_3_charge(order, idem_key)
>         else:
>             # Still uncertain → escalate
>             raise UncertainState(idem_key)
> ```
>
> **Key**: `idempotency_key` lets retries be safe + lets us **query state** to resolve uncertainty.
>
> **Outbox pattern** (durable workflow state):
>
> ```python
> # Each step writes intent + result to outbox table (in same DB transaction)
> 
> # Step 3:
> async with db.transaction():
>     outbox.write({
>         'workflow_id': wf_id,
>         'step': 3,
>         'intent': {'tool': 'charge_payment', 'args': {...}, 'idem_key': key},
>         'state': 'pending',
>     })
> # outside transaction — actually execute
> result = await execute(...)
> # write result
> async with db.transaction():
>     outbox.update(wf_id, step=3, state='completed', result=result)
> ```
>
> **Reliable worker** picks up uncommitted intents on restart, completes them. Ensures no step lost.
>
> **Failure handling per step**:
>
> ```python
> async def execute_workflow(wf_id, steps):
>     completed = []
>     for step in steps:
>         try:
>             result = await execute_step(step, idem_key_for(wf_id, step))
>             completed.append((step, result))
>         except UnrecoverableError as e:
>             # Trigger compensation in reverse
>             await compensate(completed)
>             raise WorkflowFailed(wf_id, step, e)
>         except UncertainState as e:
>             # Escalate to human / pause workflow
>             await pause_for_review(wf_id, step, e)
>             return PausedForReview
>     return Success
> 
> async def compensate(completed_steps):
>     # Reverse order
>     for step, result in reversed(completed_steps):
>         try:
>             await compensating_action(step, result)
>         except Exception as e:
>             # Compensation failed — alert, manual intervention
>             await alert(f'Compensation failed for {step}')
> ```
>
> **Workflow engine (Temporal / DBOS) recommendation**:
>
> Instead of roll-your-own:
>
> ```python
> @workflow.defn
> class OrderWorkflow:
>     @workflow.run
>     async def run(self, order):
>         try:
>             await workflow.execute_activity(create_order, order, start_to_close=10s)
>             await workflow.execute_activity(reserve_inventory, order, start_to_close=10s)
>             charge = await workflow.execute_activity(
>                 charge_payment, order,
>                 start_to_close=30s,
>                 retry_policy=RetryPolicy(max_attempts=3, ...),
>             )
>             await workflow.execute_activity(send_email, order, charge, start_to_close=10s)
>             await workflow.execute_activity(schedule_shipping, order, start_to_close=10s)
>         except ActivityError as e:
>             # Compensate in reverse
>             await compensate(...)
>             raise
> ```
>
> Temporal handles:
> - Durable state (no in-memory loss)
> - Retries with backoff per activity
> - History replay (debug-friendly)
> - Compensating handlers built-in
> - Long-running (workflow can pause for hours / days)
>
> **For LLM agent workflows specifically**:
>
> Agent step often = LLM decides → tool call. Wrap as:
>
> ```python
> @workflow.defn
> class AgentWorkflow:
>     @workflow.run
>     async def run(self, user_query):
>         conversation = []
>         while True:
>             # LLM decides next action
>             decision = await workflow.execute_activity(
>                 call_llm, conversation,
>                 start_to_close=30s,
>             )
>             if decision.action == 'reply':
>                 return decision.content
>             if decision.action == 'tool':
>                 # Execute tool as activity (idempotent, retried)
>                 result = await workflow.execute_activity(
>                     execute_tool, decision.tool, decision.args,
>                     start_to_close=10s,
>                     retry_policy=RetryPolicy(...),
>                 )
>                 conversation.append((decision, result))
> ```
>
> Benefits:
> - Workflow can pause when LLM context gets too big
> - Resume on different node (durable state)
> - Replay history for debugging
> - Per-activity retry / fallback
>
> **What NOT to do**:
> - In-memory workflow state (lost on crash)
> - Retry without idempotency
> - Skip verification on timeout
> - No compensating action defined per step
> - 'It worked in test' for multi-step (didn't test failure modes)"

---

## 多场景变体 + 解法

### 变体 1: E-commerce 下单 workflow

> "Order workflow: 库存预留 → 支付 → 发货 → 邮件确认。任意步出错怎么办？"

**解法**:
- **Saga compensate**: 库存预留 → 释放, 支付 → 退款, 发货 → 取消, 邮件 → 不发或道歉信
- **Order state machine**: pending → paid → shipped → completed, 不允许逆转
- **Outbox**: 每步状态变化 outbox event, 下游 (analytics / customer email) 异步 consume
- **Inventory pre-reserve TTL**: 预留 15 min 后未支付自动释放 (防长 hold)
- **Idempotency keys**: order_id 贯穿全链路
- **Customer comms 最后**: 邮件确认 在 shipped 之后才发, 避免 'paid' 邮件后才发现库存其实没了

### 变体 2: Multi-step research agent

> "Agent: search → read → summarize → draft → review → finalize。中间步骤 LLM 出错了"

**解法**:
- **Persistent intermediate state**: 每步 output 写文件 (research_notes.md / draft.md)
- **Resumable**: 失败重启从最后 checkpoint
- **Idempotent steps**: search 同 query 同结果 (除非 web 变), summarize 同 input 同 output (low temp)
- **Compensating optional**: research 步骤多是 read-only, 失败不需 compensate (重做即可)
- **Quality gate**: 每步完成跑 sanity check (output length / format), fail 时 retry 不进下步
- **Long-running tolerance**: 几小时 / 几天 OK, 走 Temporal workflow

### 变体 3: 旅行订票 (flight + hotel + car)

> "1 个 trip 订 3 个独立 vendor (flight, hotel, rental)。flight 成功, hotel 失败"

**解法**:
- **Saga**: hotel 失败 → 取消 flight (compensating)
- **Hold-and-confirm**: 先 hold 3 个 (preauth), 全 hold 成功才 commit-charge
- **Two-phase booking**: similar 2PC but with timeout (hold 24h auto release)
- **User-visible UX**: 'still searching hotel, your flight is held for 5 min...'
- **Refund 不等值**: flight 退款可能 fee, hotel free 取消 — 退款边界要透明
- **Reconciliation**: 24h 后 audit 'all bookings in trip consistent?'

### 变体 4: User profile update 传播到 5 个 service

> "User 改 email, 要同步给 CRM, Marketing, Auth, Billing, Notification"

**解法**:
- **Event bus**: profile.updated event → 5 consumer 各自处理
- **At-least-once delivery**: consumer 必须 idempotent (用 event_id dedup)
- **Eventually consistent**: 不保证所有 service 同时更新, 数秒延迟可接受
- **Saga 不适用 here**: 不是 transactional, 是 propagation; 失败的 consumer retry 即可
- **Dead-letter queue**: 重试 N 次仍失败 → DLQ + alert ops
- **User-facing 期望管理**: 'email update may take a few minutes to apply across all services'

### 变体 5: Agent training loop with checkpoint

> "Fine-tune agent 跑 100 epoch, 第 67 个 crash"

**解法**:
- **Per-N-step checkpoint**: every 1000 step 写 weight + optimizer state
- **Resume from last checkpoint**: crash 后从 epoch 67 step 65000 继续
- **Deterministic seed + dataset position**: 重启同 batch 顺序 (reproducibility)
- **Data loader checkpoint**: shuffle seed + epoch position + sample index
- **Gradient accumulation 也要 save**: mid-step crash
- **Distributed**: 多 GPU 上 checkpoint 协调 (DeepSpeed / FSDP)
- **Eval 中间 checkpoint**: 万一最后 epoch 反而变差, 早期 checkpoint 是 best

---

## 简历专属 reframe

| 题 | 你做过 |
|---|---|
| Saga / compensating | TikTok payment refund flow |
| Outbox | TikTok payment — transactional event pattern |
| Idempotency on retry | Voice agent SMS — you've done this |
| Multi-step state | BNPL chatbot — collection workflow |
| Verify on timeout | Payment integration — natural |

**Quote**:

> "Indonesia refund tier had this exact shape: 5-step refund workflow (verify → approve → charge → notify → audit). Each step had **idempotency key per workflow_id** + **outbox table for state**. On step 3 (charge) timeout, we'd call `get_payment_status(idem_key)` to verify before retry. The verify step prevented double-refund 100% in 6 months production. **Compensating handlers** for each step were defined upfront and tested in chaos mode. Saga > 2PC for cross-vendor."

---

## 5 follow-ups

**Q1**: "Email sent then payment refunded (compensation). User got email saying 'paid' but actually refunded. Bad UX. Handle?"
**A**:
- **Reorder**: email LAST (after payment confirmed durable)
- If reorder impossible: **delay** email by N seconds, check workflow state before sending
- **Apology + recovery message**: send follow-up explaining
- **Quarantine** if compensation in flight: hold downstream actions

**Q2**: "Saga compensation also fails. Now what?"
**A**:
- **DLQ** for failed compensations
- **Alert** human ops
- **Manual reconciliation** UI for ops to inspect + resolve
- **Compensation must be more reliable than forward** — design for it (retry-heavy, idempotent, all data captured)

**Q3**: "Workflow engine adds operational complexity. When NOT use Temporal?"
**A**:
- **Simple workflows** (< 3 steps, all reversible) — direct DB + retries enough
- **High-frequency** (microsecond) — Temporal overhead too much
- **Greenfield + small team** — roll-your-own works initially
- **Use Temporal when**: > 5 steps, long-running, multi-vendor, audit required, multiple workflows

**Q4**: "Agent in middle of workflow — LLM service goes down. What user sees?"
**A**:
- Workflow paused (Temporal handles)
- User notified: 'still processing'
- LLM service recovers, workflow resumes from durable state
- If LLM down > 5 min: alert ops + customer
- Eventually consistent — finish when service back

**Q5**: "Multi-turn agent conversation — eventual consistency for state?"
**A**:
- Each turn: read state → LLM → tool calls → write state (all in 1 workflow execution)
- State stored in DB + KV-cache
- If race (user sends 2 msgs fast): serialize via lock per conversation_id
- Workflow engine handles: per-conversation_id workflow instance, queued events

---

## ❌ 易错点

1. **2PC** for cross-vendor (impossible)
2. **In-memory state** (lost on crash)
3. **Retry without idempotency** (double execute)
4. **No verify on timeout** (don't know if executed)
5. **No compensating action** per step
6. **No DLQ for compensation failures**
7. **Email before payment confirmed** (UX bug)

---

## ✅ 加分项

1. **Saga pattern** explained explicitly
2. **Outbox** for durable state
3. **Idempotency key + verify** for timeout
4. **Temporal / workflow engine** recommendation with rationale
5. **Compensating handlers** designed per step
6. **DLQ for compensation failures**
7. **Order of operations** considered (email last)
8. **Quote Indonesia refund tier**

---

## Cheat Sheet

```
Why eventual consistency:
  Multi-vendor (no 2PC)
  Network partitions
  Latency prohibitive

Saga pattern:
  Forward steps with compensating actions
  On failure: compensate in reverse
  Per-step: idempotent + retryable

Outbox pattern:
  Each step writes intent + state to DB
  In same transaction as work
  Reliable worker picks up unfinished
  Ensures no step lost

Idempotency:
  Per-step idempotency_key (workflow_id + step)
  On retry: same key
  On timeout: VERIFY first (get_status)
  Only retry if confirmed not-executed

Verify-on-timeout pattern:
  try execute
  catch timeout:
    sleep, get_status(idem_key)
    if completed: reconstruct
    if failed: retry
    if uncertain: escalate

Compensating action design:
  Per step defined upfront
  Tested in chaos mode
  Idempotent
  More reliable than forward
  DLQ for failures

Workflow engine (Temporal / DBOS):
  Durable state (replay history)
  Per-activity retry
  Compensating support
  Long-running (hours/days)
  Recommend when > 5 steps

Agent workflow shape:
  LLM decides → tool call (as activity)
  Each tool call retryable
  Conversation state durable
  Pause / resume across LLM calls

Order matters:
  Email/notify LAST (after all confirmed)
  Reversible actions before irreversible
  If irreversible early: queue + delayed

红线:
  - 2PC for cross-vendor
  - In-memory state
  - Retry without idem
  - No verify on timeout
  - No compensating action
  - No DLQ for compensation
  - Email before payment
```
