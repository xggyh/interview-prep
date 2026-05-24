## T1.3 · parallel tools + race conditions — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/gfde-t1-parallel-race.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t1-parallel-race.html`](questions/gfde-t1-parallel-race.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"Agent emits 5 parallel tool calls — how do you schedule them?"** 或 **"Two parallel tools both update user_profile, prevent race AND debug 1-in-1000 inconsistency"**, 我按这 8 层回答, 不跳序.

### 📐 Parallel Tool Scheduling + Race — 8 层结构

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 |
|---|---|---|---|---|
| 1 | Clarify 5 维 | 0-3 min | Tools 都是 read 还是混 write? 同 entity 还是多 entity? 是否 idempotent? Failure isolation (1 fail others continue)? Tool 内部本身是否已并发? | "5 quick clarifications before scheduling — read/write mix, entity overlap, idempotency, failure isolation policy, and whether tools internally use thread pools." |
| 2 | 灾难场景 (WAW + RAW) | 3-7 min | 5 tool naive gather: T2 写 email → T2 写 name 覆盖 email → get_profile 读到 partial state → send_welcome_email 用 old email → log_audit 记错 state. WAW + RAW 同时发生 | "Let me show the naive disaster first — 5 tools fired with asyncio.gather, here's how race silently corrupts state." |
| 3 | Tool 注解系统 | 7-13 min | 每个 tool 在 spec 里 declare: `safety=read/write/destructive`, `resources_read=['user_profile:{user_id}']`, `resources_write=[...]`, `side_effects=[]`. 这是 static analysis 的输入. Runtime 才能 reason | "Scheduling needs metadata. Each tool declares safety class, resources read/written (templated by arg), and external side-effects." |
| 4 | DAG + Wave Scheduling | 13-22 min | Static analysis 生成 dependency graph: T2(W user_profile) → T1,T5(R user_profile); T3,T4 independent. Topological sort 分 wave: Wave1 [T2,T3,T4] parallel (write-disjoint), Wave2 [T1,T5] parallel (read after T2 done) | "I build a DAG from the metadata, topological sort it into waves. Wave 1 runs independent writes in parallel; Wave 2 runs reads after dependency-satisfied writes." |
| 5 | Locking 策略 | 22-30 min | Per-resource distributed lock (Redis SETNX or Redlock). Lock granularity = `(tool_name, resource_id)` not just tool_name. 死锁防御: **deterministic resource ordering** (按 resource_id sort 后再 acquire). Lock timeout 严格短于 tool timeout | "For same-resource writes I serialize via per-resource locks. Two non-obvious things — granularity is per-resource not per-tool, and I sort resource_ids before acquire to prevent deadlock." |
| 6 | Failure isolation + speedup math | 30-37 min | `asyncio.gather(return_exceptions=True)` 不让 1 fail 拖累 4. Partial result + LLM 看到 mixed success. Amdahl: 4 parallel 100ms + 1 serial 200ms = 300ms (2x speedup not 5x). Bounded concurrency (Semaphore=8) 避免 DB conn pool exhaustion | "Failure isolation via return_exceptions=True. Speedup is bounded by Amdahl — measure don't assume. Cap concurrency to avoid pool exhaustion." |
| 7 | Debug 1-in-1000 race | 37-43 min | Distributed trace (OpenTelemetry) 每 tool call attach session_id + resource_id. Property-based test (Hypothesis) generate random tool sequences, invariant `final state = sequential equivalent`. Chaos: inject artificial delay 随机化执行顺序 | "Now the hard part — debugging a race that reproduces 1-in-1000. My playbook: distributed trace with resource_id tags, property-based test for sequential equivalence, chaos delay injection." |
| 8 | Connect + production hardening | 43-50 min | BNPL chatbot multi-tool fanout: user message 触发 5 sub-agent (查 credit + 查 due + 查 dispute + 查 reward + 查 channel). 4 read parallel, 1 write (log) on user_id lock. **Bug story**: gather 默认 fail-fast cancel all → changed to return_exceptions=True, partial result 可用 | "Resume hook — BNPL chatbot had this exact 5-fanout. The cancellation behavior of gather caught us once — let me share." |

### 🎯 为啥按这个序

灾难场景 (Layer 2) 先讲是因为 race condition 抽象, 不画 timeline 面试官 follow 不上「为啥 read-write 顺序会错」. 然后 annotation system (3) 必须放在 DAG (4) 之前 — 没 metadata 就没法 reason. Locking (5) 单列因为是 production 重头戏, 死锁防御 (deterministic ordering) 是经典 staff-level 知识点. Failure isolation (6) 和 speedup math 合并是因为它们都是 "parallel 不是 free lunch" 的 nuance. Debug (7) 单列因为面试官 80% 会追问 "1-in-1000 race 怎么 debug" — 这是分水岭. Resume close (8) 用 BNPL 5-fanout 锚定.

### 🔥 哪一层最容易被追问 deeper

- **Layer 5 (locking)**: "Redlock 安全吗?" → 准备 Martin Kleppmann clock-drift 质疑 + fencing token 兜底. "Per-row vs per-table lock?" → 准备粒度选择 (per-row 高并发但 lock 多, per-table 简单但 contention).
- **Layer 7 (debug)**: "1-in-1000 怎么复现?" → 必杀 chaos injection: 在 staging artificially delay 随机 tool 100-2000ms 打乱顺序, 1 小时内大概率复现. 然后 property-based test 把这变成 regression.
- **Layer 4 (DAG)**: "If LLM emits 100 tools 怎么办?" → 准备 batch + cap N=10 + LLM 重新 plan (告诉 LLM "too many, please re-prioritize").

### ⏱ 时间压缩版 (30 min round)

- Layer 1 (clarify) 压到 2 min
- Layer 2 (灾难) 压到 3 min, 一句 timeline
- Layer 3 (annotation) + Layer 4 (DAG) 合 6 min, 一起讲
- Layer 5 (locking) 5 min, 强调 deterministic ordering 防死锁
- Layer 6 (failure isolation + Amdahl) 3 min
- Layer 7 (debug) 5 min — 必讲, 这是分水岭
- Layer 8 (connect) 2 min

### 🆘 卡壳兜底 (针对这题)

- 忘了 deterministic ordering 防死锁怎么实现 → 退回讲「**关键 insight: 所有 worker acquire resource 时按同一 ordering (e.g., sort resource_id), 就不可能 circular wait, deadlock 数学上不存在**」
- 被追问 Redlock 算法 → 退回讲「**关键 idea 是多数派 quorum + TTL + ownership token. 我倾向用 ZooKeeper/etcd 替代, CP 比 AP 更适合强一致场景**」
- 忘了 Amdahl 公式 → 退回讲「**speedup 上限取决于 serial fraction, parallel 不是 N 倍加速**」, 不背公式
- 被追问 asyncio.gather 行为 → 退回讲「**默认 fail-fast 取消所有, 加 return_exceptions=True 才 partial**」, 一句话定调
- 被追问 dependency analysis 怎么做 → 退回讲「**最简单 static — 用 tool spec 的 resources_read/write 字段; 进阶 dynamic — 实际运行时 trace 资源 access 反推依赖**」

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.
> 不含 prose, 全是 compressed structure (tables / code / one-liners).

### 核心心智模型 (1 sentence)

Parallel tool execution = 「tool annotation (safety/resources/side_effects) → 静态 DAG analysis → 拓扑 wave 分层 → wave 内 parallel + per-resource distributed lock (sorted by key, fenced token, re-entrant) → DB-layer CAS 兜底 → return_exceptions partial-success → distributed trace + property-based test for race debug」. 5 层缺 1 都数据腐败.

### 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Race condition | 并发读写同 resource, 结果依赖顺序 | 多 tool 并发 |
| WAW | write-after-write 同 resource (最常见) | 必 serialize |
| RAW | read-after-write (read 看 stale) | 必 serialize |
| WAR | write-after-read (write 后 read 别人写的) | serialize |
| RAR | read-after-read | parallel safe |
| Disjoint resources | 无共享 resource | parallel safe |
| DAG | dependency graph, 拓扑 sort 后 wave 化 | scheduling |
| Topological sort | 无依赖节点先, 分 wave | scheduler |
| Wave | DAG 同层无依赖的一组 tool | parallel 单位 |
| Distributed lock | 跨进程 / 机器互斥 | shared resource write |
| SETNX | Redis atomic NX flag | lock 实现 |
| Redlock | Redis cluster 分布式锁算法 | HA Redis |
| Fencing token | 单调递增 token storage 拒 stale | Redlock 不安全场景 (Kleppmann) |
| Re-entrant | 同 owner 重复 acquire OK | self-deadlock 防 |
| AB-BA deadlock | A 拿 R1 等 R2, B 拿 R2 等 R1 | sort by key 防 |
| CAS | compare-and-set version 列 expect | DB optimistic concurrency |
| Bulkhead | per-tenant 资源隔离 | 噪声邻居 |
| Resource template | `user_profile:{user_id}` | 动态 lock key |
| Heartbeat extend | TTL 长 op periodic 延期 | 防 TTL 到期 release |
| return_exceptions | asyncio.gather 不中断, 收集异常 | partial success |
| Hypothesis | Python property-based test | race invariant |
| Chaos engineering | 注入 latency/fail 放大 race | debug 难复现 race |

### N 个核心 framework / pattern

**Framework 1: Tool Annotation System**
- When: tool registration
- Algorithm: `safety: read|write|destructive`, `side_effects: bool`, `idempotent: bool`, `resources: ['user_profile:{user_id}']` template, `timeout_sec`, `max_concurrent_per_tenant`, `critical: bool`
- Trade-off: 手写 annotation 累 vs 自动推断不准
- Tools: Python `@tool` decorator, Pydantic schema, MCP standardized metadata, AST lint pre-commit

**Framework 2: DAG + Topological Wave Scheduling**
- When: LLM emit 多 tool 一 turn
- Algorithm: build DAG by resource conflict (WAW/RAW/WAR edge, RAR/disjoint none) → topological sort → group into waves
- Trade-off: LLM emit order vs scheduler reorder (要保留 LLM 显式意图)
- Tools: networkx (Python), gonum graph (Go), Temporal / Airflow / Prefect workflow DAG

**Framework 3: Per-Resource Distributed Lock**
- When: WAW / write-shared-resource
- Algorithm: Redis SETNX with token (UUID) + Lua DEL check token + TTL 30s + heartbeat extend; sort keys before acquire (anti AB-BA)
- Trade-off: Redis (AP) 不安全场景 → ZooKeeper / etcd (CP); 性能 vs 正确性
- Tools: redis-py SET NX EX + Lua, Redlock library, ZooKeeper kazoo, etcd3, Postgres pg_advisory_lock, AWS DynamoDB conditional write

**Framework 4: Failure Isolation + Cancellation**
- When: wave 执行
- Algorithm: `asyncio.gather(return_exceptions=True)` → partial success; critical tool fail → abort wave; cancellation via CallContext.cancel_event + asyncio.shield
- Trade-off: 1 fail abort all (strict) vs 部分 success 给 LLM (灵活)
- Tools: asyncio.gather/wait_for/shield, anyio (cross-framework cancellation), trio cancel scope tree

**Framework 5: Observability for Race Debug**
- When: 1/1000 race incident
- Algorithm: OpenTelemetry span per tool with lock_acquire_ms/execute_ms → resource_access_log (who touched what when) → property-based test (hypothesis random sequences invariant serializable) → chaos replay (inject 50ms latency)
- Trade-off: 100% trace overhead vs sampled trace miss race
- Tools: OpenTelemetry + Jaeger/Tempo/Datadog/Honeycomb, hypothesis (Python), QuickCheck (Haskell), Chaos Mesh, pyspy, replay from prod traces

### 关键决策树 (ASCII)

```
2 tools concurrent:
├─ read + read same resource → PARALLEL ✓
├─ read + read different resource → PARALLEL ✓
├─ read + write same resource → SERIALIZE (RAW)
├─ read + write different resource → PARALLEL ✓
├─ write + write same resource → SERIALIZE (WAW)
├─ write + write different resource → PARALLEL ✓
└─ destructive ANY → SERIALIZE + confirm gate
```

```
Lock granularity:
├─ tool_name only → 太粗 (update_user(u1) 和 update_user(u2) 不能 parallel)
├─ resource_key (tool, resource_id) ⭐ → 对的粒度
└─ DB row-level → 最细但 lock 数量爆
```

```
Production race 1/1000 debug:
├─ Get trace_id → distributed trace timeline
├─ resource_access_log for resource X
├─ Replay with chaos (50ms inject)
├─ Property test random sequences
└─ CAS retry log = version mismatch
```

### Part 2 五个深度问题速查

**Problem 1: Tool Annotation System**
- 核心解法:
```python
@tool(
    safety='write',
    resources=['user_profile:{user_id}'],
    side_effects=True,
    idempotent=True,
    timeout_sec=5.0,
    max_concurrent_per_tenant=10,
    critical=True,
)
def update_user_email(user_id, email): ...

def resolve_resources(meta, args):
    return [tpl.format(**args) for tpl in meta.resources]
```
- Top 3 gotchas:
  1. 没 annotation → scheduler 退化全 serial 或全 parallel disaster
  2. Resource template 不准 → lock 错 resource, race 没防
  3. side_effects vs idempotent 混淆 — read 也可能 side_effect (counter)
- Tools: Pydantic schema, MCP annotation 扩展, OpenAPI x-safety/x-reversibility, AST lint pre-commit

**Problem 2: DAG + Topological Scheduling**
- 核心解法:
```python
def build_dag(tool_calls):
    for i, j in pairs:
        if conflict_type(tc_i, tc_j) in ['WAW','RAW','WAR']:
            graph.add_edge(tc_i.id, tc_j.id)
    return graph

def schedule_waves(graph):
    waves = []
    while remaining:
        wave = [n for n in remaining if no incoming from remaining]
        waves.append(wave); remaining -= wave
    return waves

# 保留 LLM emit 顺序 (即使可重排, 显式意图优先)
```
- Top 3 gotchas:
  1. LLM 不显式 declare deps → scheduler 只能从 resource overlap 推 → 漏 logical dep
  2. Mid-wave failure → 后续 wave 依赖 failed tool output → skip with reason
  3. 2 个 write 同 resource LLM 顺序 emit → 保留 LLM 顺序不要 reorder
- Tools: networkx Python, asyncio.gather wave parallel, Temporal/Airflow DAG, MCP `depends_on` field

**Problem 3: Per-Resource Distributed Lock + Sort + Fence + Re-entrant**
- 核心解法:
```python
async def call_with_lock(tool, args):
    resources = resolve_resources(tool.meta, args)
    locks = [DistributedLock(redis, r, ttl=30) for r in resources]
    locks.sort(key=lambda l: l.key)  # anti AB-BA deadlock
    acquired = []
    try:
        for lock in locks:
            ok = await lock.acquire(timeout=5)
            if not ok: raise LockAcquireTimeout
            acquired.append(lock)
        return await tool(**args)
    finally:
        for lock in reversed(acquired): await lock.release()
# Lua DEL check token (TTL 过期不误删)
# Heartbeat extend TTL (long op)
# Re-entrant by owner_id (same caller re-acquire OK)
# Fencing token at storage (Kleppmann pattern)
```
- Top 3 gotchas:
  1. Lock without sort → AB-BA deadlock (A 拿 R1 等 R2, B 拿 R2 等 R1)
  2. TTL 过期 mid-execute → 锁失效 → 别人拿走 → 需 heartbeat extend
  3. 单 Redis instance → Redlock for HA cluster; clock drift/GC pause → fencing token at storage
- Tools: redis-py SET NX EX + Lua, Redlock library, ZooKeeper kazoo, etcd3, Postgres pg_advisory_lock, Hazelcast/Curator enterprise

**Problem 4: Failure Isolation — return_exceptions, Partial Success, Cancellation**
- 核心解法:
```python
results = await asyncio.gather(
    *[execute_with_cancel(tc, ctx) for tc in wave],
    return_exceptions=True
)
# results = [<value>, ExceptionA, ...]
successes = [r for r in results if not isinstance(r, Exception)]
failures = [r for r in results if isinstance(r, Exception)]
# Critical tool fail → abort wave; non-critical → mark, continue

# Cancellation via ctx.cancel_event:
done, pending = await asyncio.wait([task, cancel_task],
                                    return_when=FIRST_COMPLETED)
if cancel_task in done: task.cancel()
```
- Top 3 gotchas:
  1. 默认 `gather` 1 fail 全部抛 → 必加 `return_exceptions=True`
  2. Cancellation 内部 tool 没 honor (长 SQL) → 需 KILL QUERY + httpx cancel
  3. Critical vs non-critical 没区分 → 任一 fail abort 太严
- Tools: asyncio.gather/wait_for/shield, anyio cancellation, trio scope tree, OpenTelemetry trace cancellation reason

**Problem 5: Observability + Property Test for Race Debug**
- 核心解法:
```python
# Distributed trace per tool
with tracer.start_as_current_span('tool.update_user_email',
    attributes={'tool.resources': ..., 'lock.wait_ms': ...}): execute()

# Property test
@given(tool_sequence=st.lists(st.sampled_from(read_write_ops), min=2, max=10))
async def test_no_lost_updates(seq):
    actual = await scheduler.execute(seq)
    for perm in itertools.permutations(seq):
        if states_equal(simulate_serial(perm), actual): return
    fail('non-serializable')

# Chaos: 10% chance inject 50-500ms latency
```
- Top 3 gotchas:
  1. Race 1/1000 复现极难 → property test + chaos amplify 100x
  2. 没 resource access log → incident 后查不到根因
  3. CAS retry 不记 log → version mismatch 是 race signal 看不到
- Tools: OpenTelemetry + Jaeger/Tempo/Datadog, hypothesis (Python) + QuickCheck (Haskell) + RapidCheck (C++), Chaos Mesh/Gremlin/Litmus, replay from prod traces, pyspy/async-profiler

### Production gotchas (top 15)

1. All-parallel without read/write split → WAW race
2. Lock without sort → AB-BA deadlock
3. Lock without timeout → stuck forever
4. No return_exceptions=True → 1 fail abort all
5. No per-tool concurrency limit → DDOS downstream
6. Tools not annotated → scheduler 决策无信息 → 全 serial
7. No CAS at DB layer → silent override 写丢
8. Resource template 不准 → lock 错 resource
9. Read-after-write 接受 stale 没标记 → LLM 当 fresh
10. Distributed lock 单 Redis instance → Redis 挂锁全失
11. Single-process mutex 跨 process 无效
12. 同 agent 同 turn 重复 emit 同 tool → self-deadlock (需 re-entrant)
13. No cancellation propagation → agent abort 后 in-flight 仍跑
14. No observability → race 1/1000 不可 debug
15. Worker crash mid-execute TTL 过期前 → lock 误失效 (heartbeat extend)

### 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Annotation | Internal Agent Platform tool registry | "MCP-style metadata: safety/resources/idempotent/timeout/critical. PR review 强制 annotation 跟 source 一致" |
| DAG scheduling | BNPL chatbot intent fanout | "5 sub-agent emit, scheduler 4 read parallel + 1 write sequential per user_id" |
| Per-resource lock | BNPL user_profile 多 tool 写 | "Redis SETNX with sorted acquisition. 一次 deadlock incident: agent for-loop 同 tool 重复 emit → self-deadlock → fix re-entrant by session_id" |
| Property test | Pre-prod race detection | "Hypothesis 生成随机 sequences, invariant = final state = some serial order, 抓到 3 race bugs" |
| Chaos | Voice agent staging | "10% chance inject 50-500ms latency to lock acquire, race condition reproduce rate from 1/1000 → 1/10" |
| Trace debug | Multi-region voice agent | "Jaeger 看 lock_acquire_ms 长说明 contention; multi tool 重叠时 disjoint resource confirmed" |
| Cancellation | Voice agent 用户挂电话 | "ctx.cancel_event + KILL QUERY + httpx cancel; lock release on cleanup" |

### 面试现场 quotables (top 8)

> "Parallel tool 不是 silver bullet. Amdahl's law: 4 tool parallel + 1 serial = 2x speedup 不是 5x. 必须 measure 实际 gain."

> "Lock granularity = (tool_name, resource_id) 对. 不是 tool_name 太粗 (update_user(u1) 和 update_user(u2) 不能 parallel). 不是 DB row 太细 (lock 数量爆)."

> "Lock sort by key 是 AB-BA deadlock 防御标准. A 和 B 都按字母序拿锁, 没有循环依赖."

> "Redlock 在 clock drift / GC pause 下不安全 (Kleppmann 名文). 高安全场景用 fencing token at storage layer."

> "return_exceptions=True 是 asyncio.gather 必备. 否则 1 fail 全部抛, 其他 task 还在跑你只看到 1 个 exception, 不知道其他是 success 还是 fail."

> "Cancellation 不是单方向. Agent abort → cancel propagation → tool 内部必须 honor (长 SQL 用 KILL QUERY, 长 HTTP 用 httpx cancel). 否则资源 leak."

> "Race 1/1000 production 复现极难. Property-based test + chaos engineering 是唯一可靠工具. Hypothesis 生成随机 sequences, invariant = serializability."

> "BNPL chatbot 一个 production race: agent for-loop bug 同 session 重复 emit 同 tool → 同 owner self-deadlock. Fix 是 re-entrant lock by owner_id = session_id."

### 红线 (top 10 anti-patterns)

1. Parallel without read/write split (race 必然)
2. Lock without sort (AB-BA deadlock)
3. No CAS at DB layer (silent override)
4. 1 failure aborts all (no return_exceptions)
5. No annotation (scheduler 没信息)
6. Single-process mutex in distributed system
7. No re-entrant for same-owner (self-deadlock)
8. No cancellation (agent abort 但 tools 仍跑)
9. No observability for race (incident 不可 debug)
10. No property test (race bug 到 prod)
