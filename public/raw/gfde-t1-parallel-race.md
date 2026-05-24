## 题目

> "Your agent decides to call **5 tools in parallel**. How do you schedule them, detect race conditions, and decide which ones can be parallel vs sequential?"

或追问形态:

> "Two parallel tool calls both want to update `user_profile`. Possible race. Walk me through how you'd prevent this AND how you'd debug it if you saw inconsistent state in production. What if it only reproduces 1 in 1000 invocations?"

**出处**: Google FDE T1 (Tool Calling) 高级题. Anthropic / OpenAI agent runtime team interview 也常问 "agent 自己 emit 多 tool call 时 runtime 怎么调度".

**Round**: Tool Calling System Design (45-60 min)

---

## 这道题在考什么

考你**concurrency + correctness** in agent systems, 这是分布式系统经典问题 + LLM 时代新特征的交集:

1. **Read vs Write 区分** —— 90% race condition 是写写冲突 / 写读冲突
2. **Tool 注解系统** —— safety / resources / side_effects metadata
3. **依赖图 + 调度** —— DAG analysis, topological sort, dependency-aware execution
4. **Locking strategy** —— per-resource lock, distributed Redis lock with sorting for 死锁防御
5. **Failure isolation** —— `asyncio.gather(return_exceptions=True)`, partial success
6. **Speedup math** —— Amdahl's law, parallel 不是 free lunch
7. **Debug tools** —— distributed trace, property-based testing for race conditions

考的不是 "你会 asyncio.gather", 是 "你能不能 reason 一个 5 tool 同时跑的 system 在 production 里出 bug 时怎么 debug".

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**Race condition (竞态)**: 多个并发执行的代码读 / 写**同一资源**, 最终结果**依赖执行顺序**, 而该顺序又不确定. 经典例子: `balance = balance + 100` (read → add → write) 非原子.

**Read-after-write hazard / Write-after-write hazard / Read-after-read** (CPU pipeline 同名概念, 在 distributed system 一样适用):
- **WAW (写写)**: 2 个 write 同一 resource, 最终值不确定 — 最常见 race
- **RAW (读后写)**: read 后立刻被 write, read 结果可能 stale
- **WAR (写后读)**: write 后立刻 read, 看到自己写的没问题, 看到别人写的 → race

**Distributed lock**: 跨进程 / 跨机器的互斥. 不能用单机 mutex (mutex 只在单 process 有效). 工具: Redis SETNX (Redlock), ZooKeeper, etcd.

**Dependency graph (DAG)**: tool call 之间的依赖关系. `tool_B` 需要 `tool_A` 的 output → A → B 边. **Topological sort** 后才能并行执行无依赖的部分.

---

## 2. 这个问题的核心是什么

设想 agent emit 5 tool call 没做调度的灾难场景:

```
LLM emit:
  [
    update_user_email(user=42, email='new@example.com'),
    update_user_name(user=42, name='Alice'),
    send_welcome_email(user=42),
    log_audit(user=42, action='profile_updated'),
    get_user_profile(user=42)  # 给 LLM 用作 context
  ]

Naive runtime: asyncio.gather all 5
  ↓
T=0: 全部启动
T=0.1: update_user_email 完成 (write user_profile)
T=0.2: update_user_name 完成 (write user_profile) — race! 可能 email 没保存
T=0.3: get_user_profile 返回 (read user_profile) — 看到的 state 不确定 (可能 0/1/2 个写已完成)
T=0.4: send_welcome_email 发了, 但收件人是 old email (race)
T=0.5: log_audit 写的 'action' 跟实际 final state 不一致
```

**问题来源**:

| 来源 | 例子 |
|---|---|
| **WAW**: 多 write 同一资源 | 2 个 tool 都写 user_profile |
| **RAW**: read 之前的 stale | get_profile 在 update 完成前 |
| **跨 entity 隐式依赖** | order.status 跟 inventory.count 联动 |
| **External event race** | webhook 进来时 agent 正在读 |
| **Tool 内部并发** | 单 tool 已经在用 thread pool, 又被 parallel call |
| **Resource pool exhaustion** | 25 个 parallel call 抢 10 个 DB connection |

**没并发管理的后果**:

- **数据不一致**: user_profile 字段 partial update
- **审计不准**: log_audit 记的状态跟实际不符
- **下游 cascade**: 1 个 tool 因 race 失败, 拖累全部
- **资源耗尽**: 100 parallel call 打挂下游 (类似 DDOS)
- **死锁**: 2 tool 互锁 (A holds R1 wants R2, B holds R2 wants R1)
- **难 debug**: race 1/1000 才出现, 复现极难

---

## 3. 典型流程图 / 决策树

```
                ┌─────────────────────────────┐
                │ LLM emit 5 tool calls       │
                └──────────────┬──────────────┘
                               ↓
                ┌─────────────────────────────┐
                │ Static analysis (annotation)│
                │  Read tools:    {T1, T5}    │
                │  Write tools:   {T2, T3}    │
                │  Destructive:   {T4}        │
                │  Resources used:            │
                │    T1: user_profile:42     │
                │    T2: user_profile:42 (W) │
                │    T3: account:42 (W)      │
                │    T4: email (external)    │
                │    T5: user_profile:42     │
                └──────────────┬──────────────┘
                               ↓
                ┌─────────────────────────────┐
                │ Dependency graph             │
                │   T2 ─────→ T1 (W before R)  │
                │   T2 ─────→ T5 (W before R)  │
                │   T3 (independent)           │
                │   T4 (independent)           │
                └──────────────┬──────────────┘
                               ↓
                ┌─────────────────────────────┐
                │ Schedule plan               │
                │ Wave 1 (parallel):          │
                │   T2, T3, T4 (write-disjoint)│
                │ Wave 2 (after T2):          │
                │   T1, T5 (read, parallel)   │
                └──────────────┬──────────────┘
                               ↓
                ┌─────────────────────────────┐
                │ Execute wave 1 in parallel  │
                │   per-resource lock acquire │
                │   asyncio.gather            │
                └──────────────┬──────────────┘
                               ↓
                ┌─────────────────────────────┐
                │ Collect results              │
                │   gather(return_exceptions) │
                │   Some may fail (isolated)  │
                └──────────────┬──────────────┘
                               ↓
                ┌─────────────────────────────┐
                │ Execute wave 2 in parallel  │
                └──────────────┬──────────────┘
                               ↓
                ┌─────────────────────────────┐
                │ Return all results to LLM   │
                │  (with success/failure tag) │
                └─────────────────────────────┘
```

---

## 4. 关键调度规则分类表

把 5 个 tool 分类后, 调度规则:

| Tool 类型 1 | Tool 类型 2 | 同 resource? | 调度 |
|---|---|---|---|
| read | read | yes | ✅ 完全 parallel (无 race) |
| read | read | no | ✅ 完全 parallel |
| read | write | yes | ⚠️ 依赖 annotation: serialize (W before R) 或 stale-read 接受 |
| read | write | no | ✅ parallel |
| write | write | yes | ❌ SERIALIZE (用 lock 或 reorder) |
| write | write | no | ✅ parallel (disjoint resources) |
| destructive | * | * | ⚠️ 通常 serialize + confirm gate |
| read+side_effect | * | yes | ⚠️ side_effect annotation 决定 |

**Speedup math (Amdahl's law)**:

```
T_parallel = T_serial * (1 - parallel_fraction + parallel_fraction / N_workers)

例: 5 tools, 4 可 parallel, 1 必须 serial after all:
  4 tools at 100ms each, 1 tool at 200ms after:
  Serial: 4*100 + 200 = 600ms
  Parallel: max(4 parallel) + 200 = 100 + 200 = 300ms
  Speedup: 2x (不是 5x, 因为 serial section)
```

**结论**: parallel 不是 silver bullet, 设计要 measure 实际 speedup.

---

## 5. 具体业务场景

### 场景 A: BNPL Chatbot — Intent Fanout (你最贴的业务背景)

User: "我想知道我的订单状态, 然后帮我申请退款"

LLM emit 5 tool 并发:

```python
[
    get_order_details(order_id=42),       # read
    get_refund_eligibility(order_id=42),  # read
    get_user_profile(user_id=user),        # read (different entity)
    check_inventory_status(order_id=42),   # read
    log_user_action(user, action='inquiry')  # write, but logs (append-only, no race)
]
```

**调度分析**:

- 5 个全 read + 1 个 append-only write
- 无 WAW conflict
- 全部 parallel safe
- Latency: max(各 tool) ≈ 200ms vs serial 1s

**生产 bug**: 早期版本没 annotation, 用了「safe-by-default-serialize」, 200ms tool 跑成 1s, 用户体验差. 加 annotation 后 parallel 提速 5x.

### 场景 B: Voice Agent — concurrent reads during call

Voice agent 接通时 emit:

```python
[
    get_customer_info(phone=...),          # read CRM
    get_loan_history(customer_id=...),      # read loans DB
    get_call_attempts_today(customer_id=...),  # read call_log
    check_no_call_list(customer_id=...),    # read compliance DB
    get_market_holidays(country='ID'),      # read static config (cacheable)
]
```

全 read, 全 parallel, 因为开场 0.5s 内必须搞定 (call connect → first sentence < 1s).

**实战**: 这种 read fanout 是 voice agent 启动 phase 标准 pattern. 加 timeout 100ms per tool, fallback 到 cached data.

### 场景 C: Internal Agent Platform — workflow step parallelism

Workflow:

```yaml
- step: validate (parallel)
    - validate_user_input
    - validate_payment_method
    - validate_inventory
- step: process (depends on validate)
    - create_order
    - reserve_inventory
    - charge_payment
- step: notify (depends on process)
    - send_email_confirmation
    - update_crm
    - log_analytics
```

每 step 内 parallel, step 间 serial. Workflow engine (你做的 platform) 必须支持这种 DAG 表达.

### 场景 D: Multi-Agent Orchestration — sibling agents work simultaneously

你的 platform 支持 multi-agent. Orchestrator 给 3 个 sub-agent 各派活:

```
Agent A: 拉数据
Agent B: 分析
Agent C: 生成 report

如果 B 依赖 A, C 依赖 B → serial
如果 B 和 C 都依赖 A 但互相独立 → A 完后 B/C parallel
```

DAG 表示, scheduler 按 topological order 派遣.

### 场景 E: Data Analyst Agent — concurrent SQL queries

Agent 帮分析师跑多 query:

```python
[
    sql("SELECT count(*) FROM orders WHERE date='2026-05-21'"),
    sql("SELECT sum(amount) FROM payments WHERE date='2026-05-21'"),
    sql("SELECT avg(rating) FROM reviews WHERE date='2026-05-21'"),
    sql("SELECT count(*) FROM users WHERE signup_date='2026-05-21'"),
]
```

全 read SQL, parallel safe. 但**注意 connection pool**: 共享 pool size 10, 100 parallel 会排队. Per-tool concurrency limit 必备.

---

## 6. 工程上要做什么 (实施 checklist)

**作为 agent runtime / tool registry 实现方**:

1. **Tool annotation system** — `safety`, `resources`, `side_effects` 必填
2. **Resource template resolution** — `'user_profile:{user_id}'` 动态生成具体 resource key
3. **Static dependency analysis** — pre-execution build DAG from annotations
4. **Topological sort** — 决定 execution waves
5. **Per-wave parallel execute** — `asyncio.gather(return_exceptions=True)`
6. **Per-resource distributed lock** — Redis SETNX with sorted acquisition
7. **Deadlock prevention** — lock ordering by key + timeout + detection
8. **DB-layer CAS** — final safety net via optimistic concurrency
9. **Per-tool concurrency limit** — semaphore (10 concurrent get_weather max)
10. **Per-tenant concurrency limit** — bulkhead pattern
11. **Cancellation propagation** — agent abort → cancel all in-flight
12. **Failure isolation** — 1 tool fail doesn't block others
13. **Partial success protocol** — return both successes + failures to LLM
14. **Distributed tracing** — span per tool call, parent agent span
15. **Property-based testing** — random tool sequences, verify invariants
16. **Chaos engineering** — latency injection, lock contention test
17. **Observability dashboards** — per-resource contention, deadlock alert
18. **Documentation** — tool authors guide on annotation

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **All-parallel without read/write split** | WAW race, data 不一致 |
| 2 | **Lock without sorting** | AB-BA deadlock |
| 3 | **Lock without timeout** | stuck forever, breaker 卡死 |
| 4 | **No partial-success handling** | 1 fail kills all (gather without return_exceptions) |
| 5 | **No per-tool concurrency limit** | DDOS downstream |
| 6 | **Tools not annotated** | scheduler 没法决定, default 退化到全 serial |
| 7 | **No CAS / version on DB layer** | silent override 写丢 |
| 8 | **Resource template 不准** | lock 错 resource, race 没防住 |
| 9 | **Read-after-write 接受 stale 没标记** | LLM 看到 stale 当 fresh |
| 10 | **Distributed lock 用单 Redis instance** | Redis 挂 → 锁失效 |
| 11 | **Lock acquired on Python mutex** | 不跨 process, 无效 |
| 12 | **同 agent 同 turn 重复 emit 同 tool 同 args** | resource lock 自死锁 (re-entrant 需求) |
| 13 | **没 cancellation** | agent abort 后 in-flight 仍跑, 耗资源 |
| 14 | **Observability 缺失** | race 1/1000 出现, debug 极难 |

---

## 一句话总结 (Part 1)

> **Parallel tool execution = "annotate tools (read/write/destructive + resources) → static DAG analysis → per-wave parallel + per-resource distributed lock + DB-layer CAS + partial-success isolation + distributed trace for debug"**.
>
> Agent 时代 LLM 经常 emit 多 tool call, runtime 不做调度就会乱. 但 "全 serialize" 又浪费 LLM 的 fanout 能力, 必须细化到 resource-level concurrency.

---

# Part 2 · 5 个深度工程问题

## ⚙️ Problem 1: Tool Annotation System — Safety / Resources / Side_Effects

调度的前提是**知道每个 tool 的语义**. 没 annotation = 调度无信息 = 退化到 all-serial 或 all-parallel-disaster.

### 1.1 Annotation 字段设计

```python
from typing import Literal
from pydantic import BaseModel

class ToolMetadata(BaseModel):
    name: str
    safety: Literal['read', 'write', 'destructive']
    side_effects: bool  # 是否有副作用 (DB write, external call, ...)
    idempotent: bool
    resources: list[str]  # template, e.g., ['user_profile:{user_id}']
    timeout_sec: float = 5.0
    max_concurrent_per_tenant: int = 10
    requires_confirm: bool = False  # destructive 一般要
    rollback_action: str | None = None  # compensating tool

# Decorator-based registration
def tool(safety='read', resources=None, side_effects=False, **kwargs):
    def decorator(func):
        meta = ToolMetadata(
            name=func.__name__,
            safety=safety,
            side_effects=side_effects,
            resources=resources or [],
            **kwargs
        )
        tool_registry[func.__name__] = (func, meta)
        return func
    return decorator

# 使用
@tool(safety='read', resources=['user_profile:{user_id}'])
def get_user_profile(user_id: int): ...

@tool(
    safety='write',
    resources=['user_profile:{user_id}'],
    side_effects=True,
    idempotent=True,
)
def update_user_email(user_id: int, email: str): ...

@tool(
    safety='destructive',
    resources=['user:{user_id}'],
    side_effects=True,
    idempotent=False,
    requires_confirm=True,
    rollback_action='restore_user',
)
def delete_user(user_id: int): ...
```

### 1.2 Resource template resolution

Resource 用 template 表达, 实际 lock key 根据 args 生成:

```python
def resolve_resources(meta: ToolMetadata, args: dict) -> list[str]:
    resolved = []
    for template in meta.resources:
        try:
            # 'user_profile:{user_id}' → 'user_profile:42'
            key = template.format(**args)
            resolved.append(key)
        except KeyError as e:
            raise InvalidToolCall(f'Tool {meta.name} needs {e} in args')
    return resolved

# 例:
update_user_email_args = {'user_id': 42, 'email': 'a@b.com'}
resources = resolve_resources(meta, update_user_email_args)
# → ['user_profile:42']
```

**复杂 case**: 多 resource

```python
@tool(
    safety='write',
    resources=[
        'account:{from_account}',
        'account:{to_account}',
    ],
)
def transfer_funds(from_account: str, to_account: str, amount: float): ...

# 调用时
transfer_funds(from_account='A123', to_account='B456', amount=100)
# resources = ['account:A123', 'account:B456']
# scheduler 需要同时锁两个 account
```

### 1.3 Side_effects 与 idempotency 区分

```python
# read no side_effects
@tool(safety='read', side_effects=False)
def get_weather(city): ...  # 纯读, 多次调结果可能不同 (天气变了) 但无副作用

# read with side_effects (counter)
@tool(safety='read', side_effects=True, idempotent=False)
def fetch_and_increment_view_count(article_id): ...  # 读 + side-effect

# write idempotent
@tool(safety='write', side_effects=True, idempotent=True)
def set_user_email(user_id, email): ...  # 多次调结果一样

# write non-idempotent
@tool(safety='write', side_effects=True, idempotent=False)
def append_log(message): ...  # 多次调 log 多次
```

调度决策矩阵需要这些细分.

### 1.4 MCP / OpenAI function-calling annotation 实战

MCP (Model Context Protocol) 推动 tool metadata 标准化:

```yaml
# MCP tool spec
name: update_user_email
description: Update user's email address
inputSchema:
  type: object
  properties:
    user_id: { type: integer }
    email: { type: string, format: email }
annotations:
  safety: write
  idempotent: true
  resources:
    - "user_profile:{user_id}"
  cost_estimate: 0.001
  requires_confirm: false
```

OpenAI function-calling 目前没标准 annotation 字段, 但很多 framework (LangChain, LlamaIndex) 已经在 tool spec 加 metadata.

### 1.5 Annotation 来源 + 验证

| 来源 | 信任 | 验证 |
|---|---|---|
| Tool 作者手写 | 中 | 看代码 |
| 自动从 type signature 推断 | 高 (有限) | type checker |
| Manual review at registration | 高 | code review |
| Runtime 学习 (观察 tool 行为推断) | 低 | 不可靠 |

实战做法: **手写 + automated check**.

```python
# Pre-commit hook
def lint_tool_annotation(meta, source_code):
    # If source code contains 'INSERT' / 'UPDATE' / 'DELETE' SQL keywords,
    # safety must be 'write' or 'destructive'
    if has_sql_mutation(source_code) and meta.safety == 'read':
        raise Lint('Tool writes SQL but annotated as read')

    # If tool calls external API (other than read endpoints):
    if has_external_post(source_code) and not meta.side_effects:
        raise Lint('Tool POSTs externally but side_effects=False')
```

### 1.6 Tools

- **Schema**: Pydantic, JSON Schema, MCP spec
- **Decorators**: Python `@tool`, JS `@Tool()` (TypeScript class metadata)
- **Static analysis**: AST inspection (Python `ast`, JS Babel) to verify annotations match code
- **MCP servers**: standardized tool metadata exchange
- **LangChain `Tool` / `StructuredTool`**: built-in metadata

---

## ⚙️ Problem 2: Dependency Graph + Scheduling — Read Parallel / Write Disjoint Parallel / Write Same-resource Serialize

5 tool 怎么排?

### 2.1 Static DAG construction

```python
def build_dag(tool_calls: list[ToolCall]) -> Graph:
    """Build dependency DAG from tool annotations."""
    graph = Graph()
    for tc in tool_calls:
        graph.add_node(tc.id)

    # Add edges based on resource conflict
    for i, tc_i in enumerate(tool_calls):
        for j, tc_j in enumerate(tool_calls):
            if i >= j:
                continue
            edge_type = conflict_type(tc_i, tc_j)
            if edge_type == 'WAW' or edge_type == 'WAR':
                # tc_i must complete before tc_j
                graph.add_edge(tc_i.id, tc_j.id)
            elif edge_type == 'RAW':
                # tc_i (write) must complete before tc_j (read)
                graph.add_edge(tc_i.id, tc_j.id)
            elif edge_type == 'RAR':
                # No edge (both reads, no order required)
                pass
            elif edge_type == 'disjoint':
                # No edge (no shared resource)
                pass

    return graph

def conflict_type(tc1, tc2):
    common = set(tc1.resources) & set(tc2.resources)
    if not common:
        return 'disjoint'
    if tc1.is_write and tc2.is_write:
        return 'WAW'
    if tc1.is_write and tc2.is_read:
        return 'WAR'  # but typically scheduler treats as RAW
    if tc1.is_read and tc2.is_write:
        return 'RAW'
    return 'RAR'
```

**注意 LLM emit 顺序**: 即使 2 个 tool 都 write 同 resource, 如果 LLM 显式按顺序 emit, scheduler 应**保留 LLM 意图顺序**, 不要 reorder:

```python
# LLM emit:
[
    update_email(user=42, email='new@x.com'),  # 想先改 email
    notify_admin(user=42),                       # 然后通知
]
# 即使两 tool 都写 admin_log resource, LLM 意图顺序应保留
# 调度顺序 = LLM 顺序, 不要 reorder 成 notify → update
```

### 2.2 Topological sort + wave 划分

```python
def schedule_waves(graph: Graph) -> list[list[ToolCall]]:
    """Group tool calls into parallel-execution waves."""
    waves = []
    remaining = set(graph.nodes)

    while remaining:
        # Find nodes with no incoming edges from remaining
        wave = []
        for node in remaining:
            if not any(p in remaining for p in graph.predecessors(node)):
                wave.append(node)

        if not wave:
            raise CycleDetected  # graph has cycle, bug

        waves.append(wave)
        remaining -= set(wave)

    return waves

# 例
# tool_calls = [T1 (read prof), T2 (write prof), T3 (write acc), T4 (write email), T5 (read prof)]
# Conflict: T2 → T1 (RAW), T2 → T5 (RAW), T2 ↔ T5 None (both read profile after T2)
# DAG: T2 → T1, T2 → T5; T3, T4 isolated
# Waves:
#   Wave 1: T2, T3, T4 (all start)
#   Wave 2: T1, T5 (after T2)
# Wave 内 parallel, wave 间 sequential
```

### 2.3 Execution

```python
async def execute_waves(waves: list[list[ToolCall]]) -> dict[str, ToolResult]:
    results = {}

    for i, wave in enumerate(waves):
        log.info(f'Executing wave {i} with {len(wave)} tools in parallel')

        # Per-tool task creation
        tasks = []
        for tc in wave:
            task = asyncio.create_task(execute_single_tool(tc))
            tasks.append((tc.id, task))

        # Parallel wait, return_exceptions for isolation
        for tc_id, task in tasks:
            try:
                results[tc_id] = await task
            except Exception as e:
                results[tc_id] = ToolError(error=str(e))

    return results
```

### 2.4 Mid-wave failure 处理

```python
# 一个 wave 内 3 个 tool, 1 个 fail, 怎么办?

# Option A: Abort entire wave + rollback
# Strict, 但失去 partial-success 价值

# Option B: Mark failed, continue 后续 wave
# 但后续 wave 可能依赖 failed tool 的 output → 那些也 fail
async def execute_waves_with_failure_handling(waves):
    failed_nodes = set()
    results = {}

    for wave in waves:
        # Filter out tools whose dependencies failed
        executable = [
            tc for tc in wave
            if not (set(graph.predecessors(tc.id)) & failed_nodes)
        ]
        skipped = [tc for tc in wave if tc not in executable]

        for tc in skipped:
            results[tc.id] = ToolSkipped(reason='dependency_failed')
            failed_nodes.add(tc.id)

        # Execute the runnable ones in parallel
        ...
```

### 2.5 Mixed independent + dependent tools

实战常见: LLM emit 一批 tool, 有的明显独立 (search1, search2), 有的有依赖 (search → process):

```python
[
    search_inventory(product='widgetA'),  # T1
    search_inventory(product='widgetB'),  # T2
    get_pricing(product='widgetA'),       # T3 (logically after T1 but scheduler may not know)
    update_basket(items=...),              # T4 (after T1+T2+T3)
]
```

LLM 不显式声明依赖, scheduler 只能从 resource overlap 推断. 但如果资源是「概念上的同一商品」而 resource template 不一样 → 没 lock 冲突, scheduler 当独立 → bug.

**解法**: tool design 时 resource 命名要 capture 真实依赖. 或 LLM emit 时支持 `dependencies` field:

```yaml
[
  { id: t1, name: search_inventory, args: {product: 'widgetA'} },
  { id: t2, name: get_pricing, args: {product: 'widgetA'}, depends_on: [t1] }
]
```

### 2.6 Tools

- **Graph lib**: `networkx` (Python), `gonum.org/v1/gonum/graph` (Go)
- **Async**: `asyncio.gather`, Go `errgroup`, Java `CompletableFuture`
- **Workflow engine**: Temporal, Airflow, Prefect 都有 DAG 调度
- **MCP**: structured tool list with metadata

---

## ⚙️ Problem 3: Per-Resource Locks — Distributed Redis Lock with Sorting for Deadlock Prevention

写写冲突的核心防御.

### 3.1 单 resource 锁

```python
class DistributedLock:
    def __init__(self, redis_client, key: str, ttl_sec: int = 30):
        self.redis = redis_client
        self.key = f'lock:{key}'
        self.ttl = ttl_sec
        self.token = uuid.uuid4().hex  # Fencing token

    async def acquire(self, timeout_sec: float = 5) -> bool:
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            ok = await self.redis.set(
                self.key, self.token,
                nx=True, ex=self.ttl
            )
            if ok:
                return True
            await asyncio.sleep(0.05)  # poll 50ms
        return False

    async def release(self):
        # Lua script: 检查 token 匹配再删 (防止 TTL 过期后误删别人的)
        lua = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """
        await self.redis.eval(lua, [self.key], [self.token])

async def call_with_lock(tool, args):
    resources = resolve_resources(tool.meta, args)
    locks = [DistributedLock(redis, r, ttl_sec=30) for r in resources]

    # 关键: 按 key 排序后顺序 acquire, 防止 AB-BA 死锁
    locks.sort(key=lambda l: l.key)

    acquired = []
    try:
        for lock in locks:
            ok = await lock.acquire(timeout_sec=5)
            if not ok:
                raise LockAcquireTimeout(lock.key)
            acquired.append(lock)

        # All locks held, execute
        return await tool(**args)
    finally:
        # Release in reverse order
        for lock in reversed(acquired):
            await lock.release()
```

### 3.2 AB-BA deadlock 经典图

```
Task A:                Task B:
  lock(R1) ✓             lock(R2) ✓
  lock(R2) ← wait        lock(R1) ← wait
                         ↓
                      DEADLOCK
```

**Prevention via sorting**:

```
Task A 要 R1, R2 → sort → acquire R1 first, then R2
Task B 要 R1, R2 → sort → acquire R1 first, then R2

如果 A 先拿到 R1, B 等;
如果 B 先拿到 R1, A 等;
没有循环依赖, 不会死锁
```

### 3.3 Redlock for HA

单 Redis instance 挂时锁全失. Redis 官方推荐 Redlock 算法:

```python
from redlock import Redlock

dlm = Redlock([
    {"host": "redis-1", "port": 6379},
    {"host": "redis-2", "port": 6379},
    {"host": "redis-3", "port": 6379},
])

lock = dlm.lock(f'resource:{key}', ttl_ms=30000)
if lock:
    try:
        execute()
    finally:
        dlm.unlock(lock)
else:
    raise LockUnavailable
```

**注意**: Redlock 在 clock drift / GC pause 下不安全 (Martin Kleppmann 名文). 高安全场景用 fencing token 或 ZooKeeper / etcd (CP > AP).

### 3.4 Fencing token (Martin Kleppmann 推荐)

```python
# Storage 层接受 fencing token, 只接受 token >= last_seen 的写
def write_with_fencing(resource, value, fence_token):
    current = db.get_fence(resource)
    if current and current > fence_token:
        raise StaleFence(f'Got {fence_token}, current {current}')
    db.update_fence(resource, fence_token)
    db.write(resource, value)

# Lock service 给每个 acquire 返单调递增 token
token = lock_service.acquire('user_profile:42')
# Even if lock service "thinks" the lock is held but actually expired,
# storage layer rejects stale fence_token writes
```

### 3.5 Re-entrant lock

同 tool 同 args 重复 emit 时:

```
LLM bug: emit 2 个相同 tool call (same args)
runtime: both want lock on user_profile:42
  → first acquires, second waits → timeout
```

Re-entrant lock 允许同 owner 重复 acquire:

```python
class ReentrantLock:
    def __init__(self, redis, key, owner_id):
        self.redis = redis
        self.key = key
        self.owner = owner_id

    async def acquire(self):
        current = await self.redis.get(self.key)
        if current == self.owner:
            # 已持有, 加 reference count
            await self.redis.hincrby(f'{self.key}:refs', self.owner, 1)
            return True
        return await self.redis.set(self.key, self.owner, nx=True, ex=30)
```

Owner_id 可以是 `agent_session_id` 或 `agent_step_id`.

### 3.6 Lock timeout + detection

```python
# Acquire timeout (5s)
ok = await lock.acquire(timeout_sec=5)
if not ok:
    metrics.incr('lock.acquire_timeout', tags={'resource': key})
    if metrics.recent_count('lock.acquire_timeout', tags={'resource': key}, window=60) > 10:
        alert('Possible deadlock or hot resource', resource=key)
    raise LockAcquireTimeout

# Hold timeout (TTL 30s, auto-release)
# If tool actually takes longer, lock expires while holding → race
# Solution: heartbeat extend
async def hold_with_heartbeat(lock, work):
    cancel_event = asyncio.Event()

    async def heartbeat():
        while not cancel_event.is_set():
            await lock.extend_ttl(30)
            await asyncio.sleep(10)

    hb_task = asyncio.create_task(heartbeat())
    try:
        return await work()
    finally:
        cancel_event.set()
        await hb_task
```

### 3.7 Tools

- **Redis**: SETNX + Lua DEL, Redlock library (`redis-py-redlock`)
- **ZooKeeper**: `kazoo` Python client, true CP locks
- **etcd**: `etcd3` lease-based locks
- **Hazelcast / Apache Curator**: enterprise distributed locks
- **PostgreSQL advisory locks**: `pg_advisory_lock`, 简单 use case
- **Cloud**: AWS DynamoDB conditional writes (cheap fencing)

---

## ⚙️ Problem 4: Failure Isolation — asyncio.gather Return_exceptions, Partial Success

1 个 tool fail 不该拖垮全部.

### 4.1 默认 gather 行为陷阱

```python
# Bad: 默认 gather, 1 个 fail 全部抛
try:
    results = await asyncio.gather(t1(), t2(), t3(), t4(), t5())
except Exception as e:
    # 此时其他 4 个 task 仍在跑 (除非 task 自己 cancel)
    # 我们只看到 1 个 exception, 不知道其他 task 是 success 还是 fail
    pass
```

### 4.2 Return_exceptions=True

```python
# Good
results = await asyncio.gather(
    t1(), t2(), t3(), t4(), t5(),
    return_exceptions=True
)

# results = [<value>, ExceptionA, <value>, <value>, ExceptionB]
successes = [r for r in results if not isinstance(r, Exception)]
failures = [r for r in results if isinstance(r, Exception)]
```

### 4.3 Partial success — 返还给 LLM

```python
class WaveResult:
    successes: dict[str, Any]  # tool_id → result
    failures: dict[str, str]    # tool_id → error message

def format_for_llm(wave_result):
    return {
        'tool_results': {
            tc_id: result for tc_id, result in wave_result.successes.items()
        },
        'tool_errors': {
            tc_id: err for tc_id, err in wave_result.failures.items()
        }
    }

# LLM 看到部分 success + 部分 error, 自己决定:
# - 部分 result 够用 → 继续 reasoning
# - critical tool fail → retry / fallback / inform user
```

### 4.4 Critical vs non-critical

某些 tool fail 是 fatal, 必须 abort:

```python
@tool(safety='write', critical=True)
def commit_transaction(...): ...

@tool(safety='read', critical=False)
def get_recommendation(...): ...

# Scheduler 看 critical flag:
if any(r is Exception for r in critical_tool_results):
    raise WaveFailed  # abort entire wave
# Non-critical fail → mark, continue
```

### 4.5 Cancellation propagation

Agent abort (user closed conversation) 时, 所有 in-flight tool 应 cancel:

```python
class ToolContext:
    cancel_event: asyncio.Event
    deadline: float

async def execute_with_cancel(tool, args, ctx):
    task = asyncio.create_task(tool(**args))
    cancel_task = asyncio.create_task(ctx.cancel_event.wait())
    done, pending = await asyncio.wait(
        [task, cancel_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    if cancel_task in done:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        return ToolCancelled

    cancel_task.cancel()
    return task.result()
```

**注意**: tool 内部应 honor cancellation — 长 SQL 应支持 `KILL QUERY`, 长 HTTP 应支持 cancel via httpx `cancel()`.

### 4.6 Timeout granularity

```python
# Per-tool timeout
async def execute_wave(wave, ctx):
    tasks = []
    for tc in wave:
        timeout = min(tc.meta.timeout_sec, ctx.remaining())
        task = asyncio.create_task(
            asyncio.wait_for(execute_single(tc), timeout=timeout)
        )
        tasks.append(task)

    return await asyncio.gather(*tasks, return_exceptions=True)
```

### 4.7 Real example: chatbot fanout

```python
async def fan_out_search(user_query, ctx):
    tools_to_call = plan_searches(user_query)  # LLM emit 5 search

    results = await asyncio.gather(
        *[execute_with_cancel(t, ctx) for t in tools_to_call],
        return_exceptions=True
    )

    successes = []
    failures = []
    for t, r in zip(tools_to_call, results):
        if isinstance(r, Exception):
            failures.append((t.name, str(r)))
        else:
            successes.append((t.name, r))

    # 即使 2/5 失败, 3 个 success 还能用
    if len(successes) == 0:
        return AllFailed(failures)

    # 部分成功, 返还给 LLM 决定
    return PartialSuccess(successes, failures)
```

LLM 看到 `PartialSuccess` 后可以:
- "I got info from 3 sources but couldn't fetch from 2. Let me proceed with what I have."
- 或者 retry 失败的 2 个
- 或者询问用户是否要等

### 4.8 Tools

- **asyncio**: `gather`, `wait_for`, `shield`, `Event`
- **anyio**: cross-async-framework cancellation
- **trio**: cancel scope tree (更安全 cancellation)
- **OpenTelemetry**: trace propagation includes cancellation reason
- **Sentry**: track tool failure rates with context

---

## ⚙️ Problem 5: Observability + Debug — Distributed Trace, Property-Based Testing for Race Conditions

Race conditions 是最难 debug 的 bug — 1/1000 出现, 复现极难.

### 5.1 Distributed tracing

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def execute_with_trace(tool_call, parent_ctx):
    with tracer.start_as_current_span(
        f'tool.{tool_call.name}',
        context=parent_ctx,
        attributes={
            'tool.name': tool_call.name,
            'tool.safety': tool_call.meta.safety,
            'tool.resources': ','.join(tool_call.resources),
            'tool.args_hash': hash_args(tool_call.args),
            'agent.session_id': session_id,
            'agent.step_id': step_id,
        }
    ) as span:
        try:
            with tracer.start_as_current_span('lock_acquire') as lock_span:
                lock_span.set_attribute('lock.resources', tool_call.resources)
                lock_start = time.time()
                lock = await acquire_locks(tool_call.resources)
                lock_span.set_attribute('lock.wait_ms', (time.time() - lock_start) * 1000)

            with tracer.start_as_current_span('execute'):
                result = await tool_call.execute()

            span.set_status(trace.Status(trace.StatusCode.OK))
            return result
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise
```

Trace 在 Jaeger / Tempo / Datadog 里看就是:

```
agent.step.1 [1.2s]
  ├── llm.completion [200ms]
  ├── tool_wave_1 [800ms]
  │   ├── update_user_email [600ms]
  │   │   ├── lock_acquire [50ms]
  │   │   └── execute [550ms]
  │   ├── update_account [400ms]
  │   │   ├── lock_acquire [10ms]
  │   │   └── execute [390ms]
  │   └── send_email [800ms]
  │       └── execute [800ms]
  └── tool_wave_2 [300ms]
      ├── get_profile [200ms]
      └── audit_log [100ms]
```

Race 时能看到 lock_acquire 时间长 = 锁竞争; 多 tool 重叠执行 = 真 parallel.

### 5.2 Resource access log

```python
class ResourceAccessLog:
    """Append-only log: who accessed what resource when."""

    def record(self, agent_id, tool, resources, action, lock_held_ms):
        db.insert('resource_access_log', {
            'ts': time.time(),
            'agent_id': agent_id,
            'session_id': session_id,
            'tool': tool,
            'resources': resources,
            'action': action,  # 'read' / 'write' / 'lock_wait' / 'lock_acquire' / 'lock_release'
            'lock_held_ms': lock_held_ms,
            'trace_id': trace.get_current_span().get_span_context().trace_id,
        })

# Query
def find_contention_on_resource(resource_key, time_range):
    return db.query("""
        SELECT agent_id, tool, action, ts
        FROM resource_access_log
        WHERE resources LIKE %s AND ts BETWEEN %s AND %s
        ORDER BY ts
    """, [f'%{resource_key}%', time_range[0], time_range[1]])
```

### 5.3 Property-based testing

```python
from hypothesis import given, strategies as st

@given(
    tool_sequence=st.lists(
        st.sampled_from([
            ('read', 'user_profile:1'),
            ('write', 'user_profile:1'),
            ('read', 'user_profile:2'),
            ('write', 'user_profile:2'),
        ]),
        min_size=2, max_size=10
    )
)
async def test_no_lost_updates(tool_sequence):
    """Property: serializability — final state equals SOME serial order."""
    initial_state = capture_state()

    # Execute in parallel via scheduler
    actual_final = await scheduler.execute(tool_sequence)

    # Try all possible serial orders, verify at least one matches
    for perm in itertools.permutations(tool_sequence):
        expected = simulate_serial(initial_state, perm)
        if states_equal(expected, actual_final):
            return  # OK
    pytest.fail(f'Parallel execution non-serializable: {tool_sequence}')

# Invariant test
@given(...)
async def test_no_data_race(...):
    # Hypothesis: count(commits to resource X) == count(intent to write X)
    # 即: 不丢写
```

### 5.4 Chaos engineering

```python
# Inject artificial latency
class ChaosMonkey:
    @staticmethod
    async def maybe_delay():
        if random.random() < 0.1:  # 10% chance
            await asyncio.sleep(random.uniform(0.05, 0.5))

    @staticmethod
    async def maybe_lock_contention():
        if random.random() < 0.05:
            # Hold lock extra long
            await asyncio.sleep(2)

# 嵌入到 tool wrapper
async def execute_with_chaos(tool, args, ctx):
    await ChaosMonkey.maybe_delay()
    return await tool(**args)
```

效果: production 流量打到 chaos-enabled environment, race condition 被放大 100x, 加速发现.

### 5.5 Replay from production trace

```python
# Capture failed production trace
class TraceReplay:
    def capture(self, trace_id, tool_sequence, timings):
        s3.write(f'replay/{trace_id}.json', {
            'tools': tool_sequence,
            'timings': timings,
            'env': capture_env_state(),
        })

    def replay(self, trace_id):
        spec = s3.read(f'replay/{trace_id}.json')
        # Replay with same tool sequence + injected timings
        return scheduler.execute(spec['tools'], inject_delays=spec['timings'])
```

实战: 看到 production race incident → 拿 trace_id → replay locally with fault injection → reproduce → fix.

### 5.6 Metrics dashboard

```python
# Per-resource contention
prometheus_metric_lock_wait = Histogram(
    'tool_lock_wait_seconds',
    'Lock acquisition wait time',
    ['resource', 'tool', 'tenant']
)

prometheus_metric_lock_held = Histogram(
    'tool_lock_held_seconds',
    'Lock held duration',
    ['resource', 'tool', 'tenant']
)

prometheus_metric_deadlock_suspected = Counter(
    'tool_deadlock_suspected_total',
    'Lock acquire timeout (possible deadlock)',
    ['resource', 'tenant']
)

# Alert
- alert: high_lock_contention
  expr: histogram_quantile(0.99, rate(tool_lock_wait_seconds_bucket[5m])) > 1
  for: 5m
  annotations:
    summary: Resource {{ $labels.resource }} contention high
```

### 5.7 Debug pattern when seeing inconsistent state

1. **Get trace_id** from incident
2. **Distributed trace** for that request — see exact tool call ordering + lock acquire times
3. **Resource access log** — who locked when, in what order
4. **Re-run with locks logged verbosely** — log every acquire / release
5. **Property-based test** — generate random tool sequences, verify invariants
6. **Chaos replay** — inject 100x latency on production trace, observe
7. **Read DB CAS retry logs** — version mismatch usually = race

### 5.8 Tools

- **Tracing**: OpenTelemetry + Jaeger / Tempo / Datadog / Honeycomb
- **Property test**: `hypothesis` (Python), `QuickCheck` (Haskell), `RapidCheck` (C++)
- **Chaos**: Chaos Mesh, Gremlin, Litmus
- **Replay**: tape recording from production traces
- **Profiling**: pyspy, async-profiler

---

# Part 3 · 把 5 个问题串起来看

这 5 个 deep problem 一起构成 **agent runtime 的 concurrency 框架**:

1. **Annotation system** 给 scheduler 提供决策信息 — 没标注就没法调度
2. **Dependency graph + scheduling** 把 annotation 翻译成 execution plan — 决定哪些 parallel
3. **Per-resource locks** 在执行时强制约束 — annotation 错也兜底
4. **Failure isolation** 让 partial success 可用 — 不让 1 fail 拖垮全部
5. **Observability + property test** 是 debug 的最后防线 — race 隐蔽时靠它定位

**互相依赖**:

```
Annotation 错 (1) → DAG (2) 错构 → 调度错 → race
DAG (2) 错 → 锁也救不了 (因为缺锁)
锁 (3) 有 bug (没 sort) → deadlock
没 isolation (4) → 1 个 race 全栈崩
没 observability (5) → race 出了找不到根因 → 反复发生
```

5 层都做到 = staff-level concurrency engineering. 加上「我自己 debug 过 X race incident」故事 = 老兵.

---

## 必问 clarifying questions

**1. Tool semantics**

> "What do the 5 tools do — all reads, mix of read/write, or all writes? Determines what's safe to parallel."

**2. Dependency graph**

> "Are they independent or does one's output feed into another? DAG or flat? Does LLM declare deps explicitly?"

**3. Shared resources**

> "Do they touch shared state — user profile, account balance, shared cache? At resource level?"

**4. Speedup target**

> "Why parallel — latency reduction (real-time chat) or throughput (batch)? p99 latency budget?"

**5. Failure handling**

> "If 1 of 5 fails, abort all or continue with degraded? Critical-tool concept exists?"

---

## 5 步框架 (sample 45-min answer 节奏)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify read/write + dependencies + shared state + criticality |
| 5-15 min | Annotation system (safety / resources / side_effects) |
| 15-25 min | Static scheduling (parallel-safe vs sequential set) + DAG |
| 25-35 min | Race prevention (per-resource lock, sort, CAS at DB) |
| 35-45 min | Failure isolation + cancellation |
| 45-55 min | Observability + debug (trace, property test, chaos) |
| 55-60 min | Q&A |

---

## 我会这样答（sample monologue）

> "Clarify — *[假设: 5 tools mix of read/write, 1 of them updates user_profile, latency-driven (chat), partial failure should not block useful results, no LLM-declared deps]*.
>
> **Step 1: Annotate tools at registration**:
>
> ```python
> @tool(safety='read', resources=['user_profile:{user_id}'])
> def get_user_profile(user_id): ...
>
> @tool(safety='write', resources=['user_profile:{user_id}'], idempotent=True)
> def update_user_email(user_id, email): ...
>
> @tool(safety='write', resources=['account:{user_id}'])
> def charge(user_id, amount): ...
> ```
>
> **Step 2: Build DAG from annotations + LLM emit order**
>
> Conflict types: WAW serialize, WAR/RAW serialize, RAR parallel.
> Topological sort → waves.
>
> **Step 3: Execute waves**
>
> ```python
> async def execute_wave(wave, ctx):
>     tasks = [execute_with_lock(tc, ctx) for tc in wave]
>     return await asyncio.gather(*tasks, return_exceptions=True)
> ```
>
> **Step 4: Per-resource distributed lock**
>
> Redis SETNX with sorted acquisition (anti-deadlock), TTL 30s with heartbeat, fencing token for storage layer correctness.
>
> **Step 5: DB-layer CAS** as final safety net
>
> ```python
> def update_user(user_id, **fields):
>     current = db.get(user_id)
>     fields['_version'] = current._version + 1
>     ok = db.update_if_version(user_id, fields, expect=current._version)
>     if not ok:
>         raise RaceConditionError  # caller decides retry / abort
> ```
>
> **Edge cases**:
>
> - **EC1: Same agent emit 2 same tool calls (LLM bug)** → re-entrant lock, owner_id = session_id
> - **EC2: Lock TTL expires mid-execute** → heartbeat extend every 10s
> - **EC3: 1 tool fail mid-wave** → return_exceptions=True, partial success to LLM
> - **EC4: Agent abort (user closed)** → cancel propagation via asyncio CancelledError + lock release
> - **EC5: Production race 1/1000** → distributed trace + property-based test + chaos replay
>
> **Production hardening**:
>
> - Observability: per-resource lock wait p99, lock held duration, deadlock counter
> - Property test: hypothesis-generated random tool sequences, invariant 'no lost updates'
> - Chaos: inject 50ms latency 10% of acquires, verify SLA
> - Tier: gold gets bigger concurrency limit, bronze stricter
> - Per-tool concurrency limit (10 concurrent get_weather max)
>
> **Resume context**: I built this on BNPL chatbot — intent fanout pattern, 5 sub-agents working on same user_id. Used Redis distributed lock per user_id for write operations but reads ran fully parallel. Hit a production bug: agent for-loop bug caused 10 simultaneous lock acquires from same agent → deadlock-like behavior. Fix was **idempotent / re-entrant lock acquire** (same caller can re-acquire its own lock). Also built property test framework: hypothesis generated random tool sequences, invariant was 'final state = some serial order'. Caught 3 race bugs before prod."

---

## 简历专属 reframe

| 题角度 | 你的项目 |
|---|---|
| Static classification (read/write) | BNPL chatbot intent routing — fanout to multiple sub-agents |
| Per-resource lock | Voice agent multi-turn shared session state |
| Distributed trace for debug | Voice agent multi-region debugging |
| Partial failure isolation | Voice agent ASR / TTS / LLM 任一挂不挂全栈 |
| MCP-style annotation | Internal Agent Platform tool registry |
| Property-based test | ConvFinQA ablation methodology (similar mindset) |
| Re-entrant lock | BNPL deadlock incident you fixed |

**主动 quote**:

> "BNPL chatbot routed intent to N sub-agents in parallel — order lookup + refund check + product info. Same user_id shared across them. Used Redis distributed lock per user_id for **write operations** but reads ran fully parallel. Hit one production bug: agent for-loop bug caused 10 simultaneous lock acquires from same agent → deadlock-like behavior. Fix was **re-entrant lock acquire** (same caller can re-acquire its own lock). We also built property-test harness using hypothesis — generated random sequences of read/write tool calls, invariant was 'final state equals SOME serial execution order'. Caught 3 races pre-prod that wouldn't have shown in standard tests."

---

## 5 follow-ups

**Q1**: "What if you don't know tool semantics ahead of time (3rd party tool)?"

**A**: Default to **safe-serial** policy:
- Unknown tool → assume write + side_effects, serialize
- Better: dry-run analysis — does tool seem to read or write (heuristic from name / HTTP method)
- Best: require tool authors to annotate semantics in spec / MCP descriptor at registration
- For very high stakes: refuse to expose unannotated destructive tools to agent at all

**Q2**: "Parallel of 5 — 1 of them is slow (30s). Others finish in 100ms. Wait or partial-return?"

**A**: Configurable per-agent:
- **Chat use case**: timeout at 5s, partial return with `pending` markers, async webhook when slow tool completes
- **Batch use case**: wait all, configured longer total timeout
- **Hybrid**: race + first-N completion (return on first 3 succeed if those enough)
- **Speculation**: start slow tool in background, return early with partial result; agent decides if more is needed

**Q3**: "How do you avoid an agent triggering DDOS by parallelizing 100 calls?"

**A**: Multi-layer:
- **Per-agent-step**: max 10 parallel calls per LLM emit
- **Per-tool**: per-tool concurrency limit (10 concurrent gets to weather API)
- **Per-tenant**: rate limit total
- **Budget**: per-step token + dollar cap, hitting cap halts
- **Per-resource**: lock implicitly serializes same-resource writes
- **Backpressure**: queue with depth limit, reject if depth > N

**Q4**: "Production race condition you can't reproduce locally?"

**A**: Tools:
- **Chaos engineering**: inject artificial latency 0-500ms randomly into lock operations
- **Property test**: pytest-asyncio + hypothesis for random tool sequences with delay perturbation
- **Production trace replay**: capture real failure traces (trace_id, timings, args), replay locally with fault injection
- **Distributed trace deep dive**: timeline shows what overlapped when
- **Resource access log**: chronological list of who touched what
- **Statistical**: collect N production traces of same operation, find statistical anomaly in timing

**Q5**: "MCP / tool catalog supports declaring resource scope?"

**A**: Modern MCP allows tool metadata. Tool's input schema can include `@resource_lock_path` annotation. Runtime introspects and acquires. Example:
```yaml
inputSchema:
  properties:
    user_id: { type: integer, x-locks: "user:{}" }
```
Runtime sees `x-locks` and auto-generates lock key. Also: MCP can declare `safety: write` at tool level. This is becoming standard in 2026.

---

## ❌ 易错点

1. **Parallel all without read/write distinction** — race
2. **Lock without sorting** — AB-BA deadlock
3. **Lock without timeout** — stuck forever
4. **No partial-success handling** — 1 fail kills all
5. **No per-tool concurrency limit** — DDOS downstream
6. **Tools not annotated** — scheduler can't decide
7. **No CAS / version on DB layer** — silent override
8. **Single-process mutex** in distributed system — no effect
9. **No re-entrant** for same-owner repeated acquire — self-deadlock
10. **No cancellation propagation** — agent abort but tools still run
11. **No observability for race** — incident impossible to debug
12. **No property test** — race bugs reach prod

---

## ✅ 加分项

1. **Annotation system** (safety / resources / side_effects / idempotent)
2. **Static DAG + topological sort** for waves
3. **Per-wave parallel + per-resource distributed lock**
4. **Sort locks before acquire** anti-deadlock
5. **Fencing token at storage layer** (Kleppmann pattern)
6. **Re-entrant lock** for same-owner
7. **Heartbeat lock TTL extension**
8. **return_exceptions=True** for partial-success
9. **Critical vs non-critical tool flag**
10. **Cancellation propagation** via asyncio
11. **Per-tool / per-tenant concurrency limit**
12. **MCP annotation-based scheduling**
13. **Distributed trace + resource access log**
14. **Property-based test** (hypothesis)
15. **Chaos engineering** for race amplification
16. **Quote BNPL deadlock incident + property test framework**

---

## 一句话总结

> **Parallel tool execution = "annotate (read/write/resources) + static DAG + per-wave parallel + per-resource distributed lock (sorted, fenced, re-entrant) + DB CAS + partial-success isolation + trace + property test"**.
>
> Agent 时代多 tool 并发是常态. Runtime 不做调度 = 数据腐败必然发生. 5 层都做到才是 production-ready.

---

## Cheat Sheet (印 1 页随身)

```
Tool annotation (at registration):
  safety: read | write | destructive
  side_effects: bool
  idempotent: bool
  resources: ['user_profile:{user_id}']  # template
  timeout_sec: 5.0
  max_concurrent_per_tenant: 10
  critical: bool
  requires_confirm: bool

Conflict types:
  WAW (write-write) → SERIALIZE
  RAW (read-after-write) → SERIALIZE
  WAR (write-after-read) → SERIALIZE
  RAR (read-read) → PARALLEL ✓
  Disjoint resources → PARALLEL ✓

Scheduling:
  1. Annotate
  2. Resolve resources (template + args)
  3. Build DAG (conflict edges)
  4. Topological sort → waves
  5. Wave parallel, wave-to-wave serial

Per-resource lock:
  Redis SETNX with token (Lua DEL)
  TTL 30s + heartbeat extend
  Sort acquisition by key (anti-deadlock)
  Fencing token at storage (Kleppmann)
  Re-entrant by owner_id (session_id)

DB layer CAS:
  version column, expect_version on update
  RaceConditionError → caller retry / abort

Failure isolation:
  asyncio.gather(return_exceptions=True)
  Partial success → return to LLM with errors
  Critical tool fail → abort entire wave
  Cancellation: asyncio.CancelledError propagation

Concurrency limits:
  Per-agent-step: 10 parallel max
  Per-tool: 10 concurrent
  Per-tenant: rate-limited
  Per-resource: implicit via lock

Speedup math:
  Amdahl: T_par = T_ser * (1-f + f/N)
  Real speedup ≤ N (workers); usually 2-3x for mixed workload

Observability:
  Trace per tool with lock_acquire_ms, execute_ms
  Resource access log (who touched what when)
  Metrics: lock_wait_p99, lock_held_p99, deadlock_counter
  Alert: lock_wait > 1s, deadlock_counter > 10/min

Debug pattern:
  1. trace_id → distributed trace timeline
  2. Resource access log for resource X
  3. Replay with chaos
  4. Property test: random sequences
  5. CAS retry logs = version mismatch

Test:
  - Property-based: hypothesis sequences, invariant = serializable
  - Chaos: 10% acquire latency injection
  - Production replay: trace recordings
  - Unit: 2 concurrent same-resource writes → 1 wins, 1 retries

红线:
  - Parallel without read/write split
  - Lock without sort (deadlock)
  - No CAS at DB layer
  - 1 failure aborts all (no return_exceptions)
  - No annotation (no scheduler info)
  - Single-process mutex in distributed system
  - No observability for race
  - No property test
```

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
