## 题目

> "Your agent decides to call **5 tools in parallel**. How do you schedule them, detect race conditions, and decide which ones can be parallel vs sequential?"

或追问形态:

> "Two parallel tool calls both want to update user_profile. Possible race. Walk me through how you'd prevent this AND how you'd debug it if you saw inconsistent state in production."

**Round**: Tool Calling System Design (45-60 min)

---

## 这道题在考什么

考你**concurrency + correctness** for agent systems:

1. **Read vs Write 区分** —— 90% race condition 是写写冲突
2. **Locking strategy** —— per-resource lock, deadlock 防御
3. **Speedup math** —— parallel 不是 silver bullet
4. **Failure isolation** —— 1 个 parallel call 挂别拖累 others
5. **Debug tools** —— distributed trace, lock contention metrics

---

## 必问 clarifying

**1. Tool semantics**

> "What do the 5 tools do — all reads, mix of read/write, or all writes? Determines what's safe to parallel."

**2. Dependency graph**

> "Are they independent or does one's output feed into another? DAG vs flat?"

**3. Shared resources**

> "Do they touch shared state — user profile, account balance, shared cache?"

**4. Speedup target**

> "Why parallel — latency reduction (real-time chat) or throughput (batch)? Different optim."

**5. Failure handling**

> "If 1 of 5 fails, abort all or continue with degraded?"

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify read/write + dependencies + shared state |
| 5-15 min | Static scheduling (parallel-safe vs sequential set) |
| 15-25 min | Race prevention (locks / serialize per resource) |
| 25-35 min | Failure isolation + cancellation |
| 35-45 min | Debugging + observability |

---

## 我会这样答（sample）

> "Clarify — *[假设: 5 tools mix of read/write, 1 of them updates user_profile, latency-driven (chat), partial failure should not block useful results]*.
>
> **Static scheduling: classify tools at registration time**:
>
> ```python
> @tool(safety='read', side_effects=False)
> def get_user_profile(user_id): ...
> 
> @tool(safety='write', side_effects=True, resources=['user_profile:{user_id}'])
> def update_user_email(user_id, email): ...
> 
> @tool(safety='write', side_effects=True, resources=['account_balance:{user_id}'])
> def charge(user_id, amount): ...
> ```
>
> **Scheduler rules**:
>
> ```
> 1. All reads → run in parallel (asyncio.gather)
> 2. Writes touching DIFFERENT resources → also parallel
> 3. Writes touching SAME resource → serialize (by resource lock)
> 4. Read + Write on same resource → 
>      Option A: serialize (read after write)
>      Option B: parallel with stale-read accepted
>      → tool annotation determines
> ```
>
> **Execution**:
>
> ```python
> async def execute_parallel(tool_calls):
>     # Group by resource for serialization
>     by_resource = group_by_resource(tool_calls)
>     
>     async def run_serial(group):
>         results = []
>         for tc in group:
>             try:
>                 r = await call_with_timeout(tc, 10)
>                 results.append(('ok', r))
>             except Exception as e:
>                 results.append(('error', e))
>         return results
>     
>     # Run resource-groups in parallel, within-group serial
>     all_results = await asyncio.gather(
>         *[run_serial(group) for group in by_resource.values()],
>         return_exceptions=True
>     )
>     return all_results
> ```
>
> **Race prevention** — 3 layers:
>
> **L1: Static (compile time)**: tool annotations declare resources, scheduler respects
>
> **L2: Runtime (per-request)**: distributed lock per resource
>
> ```python
> async def call_with_resource_lock(tool, args):
>     resources = tool.resources_for(args)  # e.g., ['user_profile:42']
>     locks = [redis_lock(r, ttl=30) for r in resources]
>     # Sort to prevent deadlock!
>     locks = sorted(locks, key=lambda l: l.key)
>     
>     async with acquire_all(locks):
>         return await tool(args)
> ```
>
> **L3: Database (final safety net)**: optimistic concurrency control (CAS with version)
>
> ```python
> # In tool itself
> def update_user(user_id, **fields):
>     current = db.get(user_id)
>     fields['_version'] = current._version + 1
>     ok = db.update_if_version(user_id, fields, expect_version=current._version)
>     if not ok:
>         raise RaceConditionError  # caller decides retry / abort
> ```
>
> **Deadlock prevention**:
> - **Lock ordering**: always acquire in sorted resource-key order. Prevents AB-BA deadlock.
> - **Timeout**: lock TTL 30s, if can't acquire in 5s → fail fast
> - **Detection**: monitor lock wait time, alert > p99 5s
>
> **Failure isolation**:
>
> ```python
> # `return_exceptions=True` keeps successes
> results = await asyncio.gather(*tasks, return_exceptions=True)
> 
> success_results = [r for r in results if not isinstance(r, Exception)]
> failures = [(t, r) for t, r in zip(tasks, results) if isinstance(r, Exception)]
> 
> if failures:
>     # Log + maybe notify agent so it can decide
>     log.warning("Partial failure: %s", failures)
>     return PartialResults(success_results, failures)
> ```
>
> Agent sees partial → can decide:
> - Have enough info to proceed → continue
> - Critical failure → user-visible error
>
> **Observability**:
>
> Per-call: distributed trace span linked to parent agent step
> Per-resource: lock contention rate, average wait time
> Alert: deadlock (wait > 30s + count > 5)
>
> **Debug pattern when seeing inconsistent state**:
> 1. **Distributed trace** for the request — see exact tool call ordering
> 2. **Resource access log** — who locked when
> 3. **Re-run with locks logged verbosely**
> 4. **Property-based test**: generate random tool sequences, verify invariants
>
> **What NOT to parallel**:
> - Tools where order matters semantically (e.g., create_order → charge → confirm)
> - Tools that don't say so — annotate-or-default-serialize
> - Long-running (>5s) bundled with fast ones — bottleneck whole batch"

---

## 多场景变体 + 解法

### 变体 1: 同 agent 1 turn 内 2 个 tool 都改 wallet

> "Agent 一个 turn 内 emit 了 [debit_wallet(amount=100), debit_wallet(amount=50)]。这俩是 fanout parallel 还是必须 serialize？"

**关键差异**: 同 user 同 resource, 同 agent 同 turn。

**解法**:
- **Resource declarative**: tool 注册时声明 `resources=['wallet:{user_id}']`
- Scheduler 看到两个 tool 同 resource → **自动 serialize**
- LLM 不需要知道这事 — runtime 处理
- **Order**: 按 LLM 输出顺序 (LLM 隐含意图)
- **All-or-nothing**: outbox + saga，若第二个失败补偿第一个
- **Visible to LLM**: 两个 result 都送回 LLM 完整 context

### 变体 2: 多用户共享一个 backend connection pool

> "Agent 给 5 user serving。每个 user 5 个 parallel tool。25 个并发查 DB，pool 只 10 connection。怎么调度？"

**关键差异**: Resource 边界不是 user 而是 **shared infra**。

**解法**:
- **Per-pool semaphore**: 最多 10 concurrent
- **Per-user concurrency limit**: 每 user 最多 3，防 1 user 独占
- **Priority queue**: gold tenant 优先
- **Tool-level**: read-only query 可走 read replica (扩 pool)
- **Latency budget propagation**: 排队过久的 task 主动 abort (上层 agent 重 plan)
- **Observability**: pool wait time p99 alert

### 变体 3: 同 user 2 个设备同时 active

> "User 手机 + laptop 都开着 chat。两边都给 agent 发指令，可能同时改 profile。"

**关键差异**: **跨 session race**, agent 不知道有 sibling。

**解法**:
- **Per-user advisory lock** (Redis): 写操作必须拿
- **Conversation_id 不同** but **user_id 同** → 锁是 user-level 不是 conv-level
- **CAS at DB**: profile.version 每写 +1; 写时检查 version, 不一致 retry
- **冲突 UI**: 'profile changed by other session, refresh' 提示
- **Last-write-wins** 业务上常见但要 audit; 必要时**操作合并** (additive ops 不冲突)
- **Worst case**: read-modify-write 用 DB transaction + row lock

### 变体 4: Parallel LLM calls (multi-query RAG)

> "RAG 用 3 个 paraphrase 并发查 vector DB。这是 race condition 吗？怎么 coordinate?"

**关键差异**: 全 read-only, no shared write state。

**解法**:
- **完全独立 parallel** 没 race — 都是 read
- **聚合后处理**: results 拿到后做 RRF / dedup
- **Cost concern**: 3x LLM cost (paraphrase generation) + 3x vector query
- **Cancellation**: 主 query 已经 hit 阈值 → cancel 多余 paraphrase
- **Timeout per branch**: 1 个 paraphrase 慢，其他不等
- **Observability**: paraphrase 各自命中 chunk 集合差异度 (overlap < 50% 才有意义)

### 变体 5: Agent action vs incoming webhook race

> "Agent 读了 order.status='pending'。同时 payment webhook 进来把 status 改成 'paid'。Agent 接下来基于 stale 'pending' 写新状态，覆盖了 'paid'。"

**关键差异**: 不是 agent 内部 race, 是 **agent vs external event**。

**解法**:
- **Read-modify-write with CAS**: 写时检查读取时的 version
- **Event sourcing**: 不直接写 status, 写 action ('user_clicked_confirm'), reducer 决定 final state
- **Optimistic lock**: 写时 `WHERE status='pending'`, 0 rows affected → 退出 + re-read
- **Webhook race awareness**: agent 在长操作前重新读 latest state
- **状态机校验**: 'pending → paid' OK, 'paid → pending' 拒绝 (业务规则)

---

## 简历专属 reframe

| 题 | 你做过 |
|---|---|
| Static classification (read/write) | BNPL chatbot intent routing — fanout to multiple sub-agents |
| Per-resource lock | Voice agent 多 turn shared session state |
| Distributed trace for debug | Voice agent multi-region debugging |
| Partial failure isolation | Voice agent ASR / TTS / LLM 任一挂不挂全栈 |

**Quote**:

> "BNPL chatbot routed intent to N sub-agents in parallel — order lookup + refund check + product info. Same user_id shared across them. Used Redis distributed lock per user_id for **write operations** but reads ran fully parallel. Hit one production bug: agent for-loop bug caused 10 simultaneous lock acquires from same agent → deadlock. Fix was **idempotent lock acquire** (same caller can re-acquire its own lock)."

---

## 5 follow-ups

**Q1**: "What if you don't know tool semantics ahead of time (3rd party tool)?"
**A**: Default to **safe-serial** policy:
- Unknown tool → assume write, serialize
- Optional: dry-run analysis — does tool seem to read or write?
- Better: require tool authors to annotate semantics in spec / MCP descriptor

**Q2**: "Parallel of 5 — 1 of them is slow (30s). Others finish in 100ms. Wait or partial-return?"
**A**: Configurable per-agent:
- **Chat use case**: timeout at 5s, partial return + "still loading X..." async
- **Batch use case**: wait all
- **Hybrid**: race + first-N completion (return on first 3 succeed if those enough)

**Q3**: "How do you avoid an agent triggering DDOS by parallelizing 100 calls?"
**A**: Multi-layer:
- **Per-agent-step**: max 10 parallel calls per LLM step
- **Per-tool**: per-tool concurrency limit (10 concurrent gets to weather API)
- **Per-tenant**: rate limit total
- **Budget**: per-step token + dollar cap, hitting cap halts

**Q4**: "Production race condition you can't reproduce locally?"
**A**: Tools:
- **Chaos engineering**: inject artificial latency 0-500ms randomly
- **Property test**: pytest-asyncio + hypothesis for random tool sequences
- **Production trace replay**: capture real failure traces, replay locally with fault injection

**Q5**: "MCP / tool catalog supports declaring resource scope?"
**A**: Modern MCP allows tool metadata. Tool's input schema can include `@resource_lock_path` annotation. Runtime introspects and acquires.

---

## ❌ 易错点

1. **Parallel all without read/write distinction** — race
2. **Lock without sorting** — AB-BA deadlock
3. **Lock without timeout** — stuck forever
4. **No partial-success handling** — 1 fail kills all
5. **No per-tool concurrency limit** — DDOS downstream
6. **Tools not annotated** — scheduler can't decide
7. **No CAS / version on DB layer** — silent override

---

## ✅ 加分项

1. **Static (annotation) + runtime (lock) + DB (CAS)** 3 layers
2. **Sort locks before acquire** anti-deadlock
3. **return_exceptions=True** for partial-success
4. **Per-tool / per-tenant concurrency limit**
5. **MCP annotation-based scheduling**
6. **Property-based test** awareness
7. **Quote BNPL deadlock incident**

---

## Cheat Sheet

```
Static classification (at tool registration):
  safety: read | write | destructive
  resources: ['user_profile:{user_id}']
  parallel-safe: read | write-disjoint-resources

Scheduling rules:
  reads → all parallel
  writes-disjoint → parallel  
  writes-same-resource → serialize
  read+write same → annotation decides

Race prevention 3 layers:
  L1 Static annotation
  L2 Distributed lock per resource (sorted, TTL)
  L3 DB optimistic concurrency (CAS + version)

Deadlock prevention:
  Acquire locks in sorted key order
  TTL on each lock (30s)
  Max wait 5s, fail fast
  Monitor wait p99

Failure isolation:
  asyncio.gather(return_exceptions=True)
  Partial success → log + return to agent
  Agent decides continue or abort

Concurrency limits:
  Per-agent-step: 10 parallel max
  Per-tool: 10 concurrent
  Per-tenant: rate-limited

Debug tools:
  Distributed trace
  Resource access log
  Property-based test
  Chaos latency injection

红线:
  - Parallel without read/write split
  - Lock without sort (deadlock)
  - No CAS at DB layer
  - 1 failure aborts all
```
