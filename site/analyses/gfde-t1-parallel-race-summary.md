# ⚡ T1.3 · Parallel Tool Calls + Race Condition — 冲刺版

> 完整版: [gfde-t1-parallel-race.html](gfde-t1-parallel-race.html). 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: agent 一 turn emit 5 tool calls, mix read+write, latency-driven (chat 2s p99), partial failure 可接受, LLM 不显式声明依赖, 跨进程 distributed 部署, multi-tenant SaaS."

**5-layer 架构**:

### Layer 1: Tool annotation system (调度的前提)

```python
@tool(safety='write', side_effects=True, idempotent=True,
      resources=['user_profile:{user_id}'],  # template, resolved per-call
      timeout_sec=5.0, max_concurrent_per_tenant=10,
      critical=True, requires_confirm=False)
def update_user_email(user_id: int, email: str): ...
```

`safety: read|write|destructive` + `resources: [template]` + `idempotent` 三件必填. 没标注 = scheduler 没决策信息 = 退化到全 serial 或 all-parallel-disaster.

### Layer 2: Static DAG construction (4 conflict types)

```
WAW (write-write 同 resource)  → SERIALIZE
RAW (read-after-write 同 res)  → SERIALIZE
WAR (write-after-read 同 res)  → SERIALIZE
RAR (read-read)                → PARALLEL ✓
Disjoint resources             → PARALLEL ✓
```

Topological sort 后划 **waves** — wave 内 parallel, wave 间 sequential. LLM 显式 emit 顺序 不要 reorder (保留意图).

### Layer 3: Per-resource distributed lock

```python
# Redis SETNX with fencing token, Lua DEL (token match)
locks.sort(key=lambda l: l.key)   # 排序 acquire 防 AB-BA 死锁
for lock in locks:
    await lock.acquire(timeout_sec=5)
# 执行 + heartbeat extend (TTL 30s, 每 10s renew)
# release 反向
```

**Fencing token** (Kleppmann pattern): storage 层只接受 token >= last_seen 的写, 即使 Redis 误判锁失效也兜底.

**Re-entrant lock by owner_id (session_id)**: LLM bug 同 turn emit 重复 tool, 同 session 可重入避免自死锁.

### Layer 4: DB-layer CAS (锁失效兜底)

```python
def update_user(user_id, **fields):
    fields['_version'] = current._version + 1
    ok = db.update_if_version(user_id, fields, expect=current._version)
    if not ok: raise RaceConditionError  # caller retry / abort
```

锁有 bug, CAS 兜底. 双层防御.

### Layer 5: Failure isolation + cancellation

```python
results = await asyncio.gather(*tasks, return_exceptions=True)
# 1 fail 不全死. critical=True flag tool fail → abort wave; non-critical fail → partial
# Agent abort → asyncio.CancelledError propagate + lock release
```

### Edge cases

- **EC1 LLM bug emit 2 同 tool 同 args**: re-entrant lock (owner_id = session_id 可重入), 不要自死锁
- **EC2 Lock TTL expires mid-execute** (tool 真跑了 35s): heartbeat 任务每 10s extend, 不要硬 TTL
- **EC3 1 tool fail mid-wave**: `return_exceptions=True` partial success 给 LLM; critical tool fail → abort entire wave
- **EC4 Agent abort (user closed)**: `asyncio.wait` 监听 cancel_event + asyncio.CancelledError → cancel all in-flight + lock release. Tool 必须 honor SQL KILL / httpx cancel
- **EC5 Production race 1/1000 难复现**: distributed trace timeline + resource access log + property test (hypothesis) + chaos replay (10% acquire latency inject)

### Production hardening

- **Per-tool concurrency limit**: semaphore 10 concurrent get_weather max (防 DDOS 下游)
- **Per-tenant bulkhead**: gold 高配额, bronze 严
- **Observability**: lock_wait_p99, lock_held_p99, deadlock_counter (acquire timeout); alert lock_wait > 1s
- **Property test**: hypothesis 生成随机 tool 序列, 不变式 "final state = SOME serial order" (serializability)
- **Chaos**: ChaosMonkey inject 50ms-500ms 10% acquires, race condition 放大 100x
- **Replay**: 抓 production failed trace_id → 本地 inject 相同 timing → reproduce → fix

### 🪝 Resume hook

"BNPL chatbot 一 user message 触发 5 sub-agent fanout (查 credit/due/dispute/reward/channel). 4 read 走 asyncio.gather parallel, 1 write 走 Redis per-user_id lock serial. 踩的最深坑: agent for-loop bug 同 session 触 10 个 simultaneous lock acquire 同 user_id → deadlock-like. 修法: re-entrant lock owner=session_id. 还自建 property test framework, hypothesis 生成 random read/write 序列, invariant 'final = some serial order', 跑出 3 个 prod 测不到的 race bug."

---

## 🔥 5 Follow-ups

**Q1: 3rd party tool 不知道 semantics 怎么调度?**
默认 **safe-serial**: unknown → 假定 write + side_effects → 全 serialize. 进阶: heuristic 从 name 推 (read prefix `get_*/list_*/search_*` vs write); 最佳: 注册时强制 tool author 标注 MCP descriptor. 高 stakes 场景: 拒绝 expose unannotated destructive tool 给 agent.

**Q2: 5 parallel 里 1 个慢 30s, 4 个 100ms — 等还是 partial?**
按场景配: **Chat use case** 5s timeout, partial return 带 `pending` marker, async webhook 回调慢 tool. **Batch** 等全部, 总 timeout 拉长. **Hybrid**: race + first-N (前 3 success 够就返). **Speculation**: 慢 tool 后台跑, partial 早返, agent 再决定是否等.

**Q3: agent 用 parallel 触发 DDOS (一次 100 calls) 怎么防?**
多层: per-agent-step max 10 calls/emit + per-tool semaphore 10 concurrent + per-tenant rate limit + per-session $$$ budget cap + per-resource implicit serialize (lock) + backpressure queue with depth limit. 任一 axis 命中就 reject.

**Q4: Production race 1/1000 本地复现不了?**
6 件: (a) trace_id → Jaeger/Tempo timeline 看 lock_acquire 重叠 (b) resource_access_log 按 timestamp 排序 (c) chaos engineering 注入 0-500ms 锁延迟随机 (d) hypothesis property test 跑 1000 随机序列 verify serializable (e) production trace 抓 timing 本地 replay with fault injection (f) statistical p99 of timing across N traces 找 anomaly.

**Q5: MCP / tool catalog 支持 resource scope declaration?**
2026 MCP 标准已支持. Tool input schema 加 `x-locks: "user:{}"` annotation, runtime 自动 introspect 生成 lock key. Tool 顶层 `safety: write` 标注也是标准. 这是 industry 从 "能 tool calling" 转 "scale + safe scheduling" 的关键能力.

---

## ❌ 易错点 (12 条红线)

1. **All-parallel without read/write 区分** — WAW race, 数据 partial update
2. **Lock without sorting** — AB-BA deadlock 经典
3. **Lock without timeout** — stuck forever, breaker 卡死
4. **No `return_exceptions=True`** — 1 fail gather 整个抛, 其他 in-flight 仍跑但结果丢
5. **No per-tool concurrency limit** — DDOS 下游 (100 parallel 打挂 weather API)
6. **Tools 不 annotate** — scheduler 无信息 → 退化 all-serial / all-parallel
7. **No CAS / version on DB layer** — 锁失效就 silent override 写丢
8. **Single-process mutex in distributed** — 不跨 process 无效
9. **No re-entrant for same-owner** — agent 重 emit 自死锁
10. **No cancellation propagation** — agent abort 但 in-flight 继续耗资源
11. **Resource template 不准** — `user:{user_id}` 但 args 字段叫 `uid` → lock 错 resource race 没防
12. **同 session 同 tool 同 args 共用 lock 但不识别 same owner** — 自家自己阻塞自己

---

## ✅ 加分项 (14 条)

1. Annotation system 完整 (safety/resources/side_effects/idempotent/critical)
2. Resource template resolution (`'user_profile:{user_id}'.format(**args)`)
3. Static DAG + 4 conflict types (WAW/RAW/WAR/RAR/disjoint)
4. Topological sort → waves (wave 内 parallel, wave 间 serial)
5. Per-resource distributed lock (Redis SETNX + Lua DEL)
6. Sort locks before acquire (anti-deadlock)
7. Fencing token at storage layer (Kleppmann 名文)
8. Re-entrant lock by owner_id (session_id)
9. Heartbeat lock TTL extension (每 10s renew)
10. DB-layer CAS as final safety net (version column + expect_version)
11. `return_exceptions=True` partial success to LLM
12. Critical vs non-critical flag (fatal tool abort wave)
13. Cancellation propagation via asyncio.CancelledError + lock release
14. Property test (hypothesis serializability invariant) + chaos replay

---

## 一句话总结

Parallel = **annotate (read/write/resources) + static DAG + per-wave parallel + per-resource sorted-acquire fenced re-entrant lock + DB CAS + return_exceptions partial isolation + cancellation + trace + property test**. Agent 时代 LLM 常 emit 多 tool, runtime 不调度数据腐败必然.

---

## 🃏 Cheat Sheet (印 1 页随身)

```
Annotation (at registration):
  safety: read | write | destructive
  resources: ['user_profile:{user_id}']  # template
  side_effects / idempotent / critical / requires_confirm: bool
  timeout_sec / max_concurrent_per_tenant

Conflict types (DAG edges):
  WAW / RAW / WAR (same resource) → SERIALIZE
  RAR / Disjoint resources         → PARALLEL ✓

Schedule waves:
  1. Annotate → 2. Resolve resources (template+args)
  3. Build DAG (conflict edges) → 4. Topological sort → waves
  5. Wave 内 asyncio.gather, wave 间 sequential

Per-resource lock (Redis):
  SETNX + Lua DEL (token match release)
  TTL 30s + heartbeat extend every 10s
  Sort acquisition by lock.key (anti-deadlock AB-BA)
  Fencing token at storage (Kleppmann)
  Re-entrant by owner_id = session_id

Lock flow:
  for lock in sorted(locks, key=lambda l: l.key):
    ok = await lock.acquire(timeout_sec=5)
    if not ok: raise LockAcquireTimeout
  try: work() finally: release reverse order

DB layer CAS (safety net):
  _version column, UPDATE ... WHERE id=? AND _version=?
  not ok → RaceConditionError → retry / abort

Failure isolation:
  asyncio.gather(*tasks, return_exceptions=True)
  critical=True fail → abort wave
  non-critical fail → partial success to LLM
  Agent abort → asyncio.CancelledError + lock release

Concurrency limits (defense in depth):
  Per-agent-step 10 max | Per-tool semaphore 10
  Per-tenant rate limit | Per-resource implicit lock
  Per-session $$$ cap

Speedup (Amdahl): T_par = T_ser × (1 - f + f/N)
  5 tools, 4 par @100ms + 1 ser @200ms = 2x (not 5x)

Observability:
  Trace: lock_acquire_ms / execute_ms per tool
  Resource access log (who/what/when/action)
  Metrics: lock_wait_p99 / lock_held_p99 / deadlock_counter
  Alert: lock_wait > 1s sustain 5min

Debug pattern (race incident):
  1. trace_id → Jaeger/Tempo timeline
  2. Resource access log for resource X
  3. CAS retry log = version mismatch
  4. hypothesis property test serializable
  5. Chaos replay (inject latency)

Test:
  Property: hypothesis random sequences,
    invariant: final state = SOME serial order
  Chaos: 10% acquire 50-500ms latency inject
  Unit: 2 concurrent same-res write → 1 wins 1 retries
  Production replay: trace recording → local fault inject

Resume BNPL story:
  5 sub-agent fanout: 4 read parallel, 1 write locked
  Bug: for-loop 10 same-session acquire → deadlock
  Fix: re-entrant lock owner=session_id
  Built hypothesis property test → caught 3 pre-prod races

红线:
  - Parallel without read/write split (race)
  - Lock without sort (AB-BA deadlock)
  - No CAS at DB layer (silent override)
  - 1 fail aborts all (no return_exceptions)
  - No annotation (scheduler blind)
  - Single-process mutex in distributed
  - No observability / property test
```
