## 题目（verbatim）

> **[ElevenLabs FDE Coding Round]**
>
> In Google Doc with Python: **Assess permissions in a file system based on user IDs**. Account for **hierarchy and timestamps**.

**出处**: ElevenLabs FDE 真题 (候选人 report via Exponent guide). Production-ish coding 题, 不是纯 LeetCode.

**Round**: Coding (60 min, Google Doc with Python — 无 IDE, 无 syntax check)

---

## 这道题在考什么

考你 **production-system coding** — 不是 algo puzzle, 是接近真实业务:

1. **Data model 设计能力** — tree (hierarchy) + interval (time) + ACL (permission)
2. **Permission inheritance 模型** — child 怎么从 parent 继承, override 规则
3. **Time-aware 查询** — "user X 在 2024-03-15 14:00 这一刻能不能 read file Y"
4. **Edge case 思维** — cycle, symlink, race, mid-flight permission change, deleted file
5. **Production scale 思维** — 10M files / 1M users / 高 QPS, 怎么不用 O(N) per query
6. **Clean code 在 Google Doc 上** — 没 syntax check, 一个 colon 错半天

这是 ElevenLabs / Anthropic / Databricks 等公司常用的 **"system-y coding"** 题型, 介于 LeetCode 和 design 之间.

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**File system permission**: 控制 "**谁** 能对 **什么文件** 做 **什么操作** 在 **什么时间**" 的机制. Unix 是 owner/group/world × rwx 的简化版, 真实企业系统通常用 ACL (Access Control List) 更精细.

**Hierarchy** (层级): 文件系统天然是**树**. `/` → `/dir` → `/dir/file.txt`. 权限继承基本规则: **子继承父**, 子可以**override** (deny 或 grant). 这种「子优先, 但回退到父」是这道题核心.

**Timestamps** (时间戳): 不只是 "file 创建时间". 这道题考的是 **time-bounded permission**: 一个 grant 可能是 `effective_from = 2024-01-01, effective_until = 2024-12-31`, 过了就失效. 或者一个 grant 在 2024-03-15 14:00 被 revoke 了, 之后再查就是 false.

**Effective permission**: **某个时刻**对某个 file 的某个 user 的某个 action 的**计算结果**. 它不是直接存的, 是从 ACL 表 + hierarchy + time 三个维度**算出来的**.

---

## 2. 这个问题的核心是什么

设想一个**没有 hierarchy + timestamp 的 naive permission 系统**:

```
File: /confidential/q4_earnings.xlsx
ACL: { 'alice': {'read': True} }

问题:
- /confidential 文件夹本身的权限呢?
- Alice 上个月被授权, 这个月离职了, 怎么及时 revoke?
- 上周的审计要查 "去年 10 月 15 日谁能 read 这个文件" — 答不出
- /confidential/2023_archive/ 是 /confidential 的子目录, 但权限要更严格 — 没法 override
```

**这道题想测**: 你能不能**同时**处理:

```
1. 树形继承 (parent → child propagate, child override 优先)
2. 时间窗口 (每个 grant 有 effective_from / until)
3. Audit 查询 (任意 user × file × time 一发即查)
4. 高效查询 (10M files 不能 O(N) per query)
```

---

## 3. 典型架构图

```
                    Permission Query API
              "can(user, file, action, at_time)?"
                          │
                          ▼
                ┌────────────────────────────┐
                │   Resolution Engine         │
                │  (核心算法见 Problem 2)      │
                └────┬────────────────┬──────┘
                     │                │
                     ▼                ▼
        ┌────────────────────┐  ┌──────────────────────┐
        │  Tree Structure    │  │  ACL Event Store     │
        │  /                 │  │  (sorted by ts)      │
        │   ├── /dir/        │  │                      │
        │   │   ├── /a.txt   │  │  per (file, user,    │
        │   │   └── /b.txt   │  │   permission) →      │
        │   └── /etc/        │  │   [grant_events...]  │
        └────────────────────┘  └──────────────────────┘
                     ▲                    ▲
                     │                    │
              create_file()       apply_grant_event()
              move_file()         apply_revoke_event()
              delete_file()       (events are append-only)
```

**关键设计选择**:

- **Tree**: 双向链 (parent ← child) 还是 nested set / closure table — 我们用最简单的 parent ID
- **Events** 还是 **state**? Event-sourced (append-only) 比 mutable state 好 — 天然支持 time-travel 查询
- **Resolve at write or read?** 默认 read-time, 但热点路径可以 materialize

---

## 4. 5 类 permission model 对比

| 模型 | 含义 | 例子 | 复杂度 |
|---|---|---|---|
| **Unix-style** | owner/group/world × rwx | `chmod 644` | 低 |
| **POSIX ACL** | + per-user/group entry | `setfacl -m u:alice:rwx` | 中 |
| **RBAC** (Role-Based) | role → permission, user → role | "editor" role | 中 |
| **ABAC** (Attribute-Based) | rule engine on attributes | "role=editor AND dept=eng" | 高 |
| **Time-bounded ACL** ⭐ | ACL + effective_from/until | "alice can read until 2024-12-31" | 中 (本题考的) |

**这道题考的是 "Time-bounded ACL with hierarchy"**, 介于 POSIX ACL 和 RBAC 之间.

---

## 5. 具体业务场景

### 场景 A: 你的 ByteDance Internal Agent Platform (你工作背景)

**场景**: 多个 team 共享一个 Agent Platform, 每个 team 能访问的工具 / 数据 / model 不同.

```
/agent_platform/
  ├── /tools/
  │   ├── /payments_api          ← Voice agent team can use
  │   └── /internal_crm          ← BNPL team can use
  ├── /memory/
  │   └── /user_conversations    ← Most teams read-only, BNPL team RW
  └── /models/
      ├── /llama_3_70b           ← All teams
      └── /finetuned_voice_bnpl  ← Only voice team
```

每个 team 的 permission 写在 manifest 里, **支持时间窗口** (e.g., "intern X 在 2024-06-01 到 2024-08-31 期间可读 voice tool"). 离职 / 调岗 / 暑期实习结束自动失效.

### 场景 B: TikTok PayLater 多市场隔离

每个市场 ops team 只能访问**自己市场**的 customer data:

```
/data/
  ├── /indonesia/
  │   ├── /loan_applications
  │   └── /payment_history
  ├── /vietnam/
  │   └── /...
  └── /thailand/
      └── /...
```

- 印尼 ops team 只能访问 `/data/indonesia/*`
- 全球 fraud team 能访问所有市场的 fraud-related subfolder
- 审计员**临时**能访问任意, 但带 expiry (week-long ticket)

### 场景 C: Indonesia Refund Tier Confirmation 系统 (你做过)

- 一个 refund 进入 "manual confirm" tier 后
- 进入一个 `/pending_confirms/{refund_id}/` 文件夹
- Region head 有 review 权限, 但 expires after 48h
- 48h 后 escalate to higher tier, region head 自动失去权限

### 场景 D: Google Drive 文档分享

- Alice 把文档分享给 Bob "view only, expires in 7 days"
- Bob 把 parent folder 也分享给 Carol "edit"
- 问: Carol 能 edit 这个文档吗? (child 没 explicit 给 Carol, 但 parent 有)
- 问: 7 天后 Bob 还能看吗?
- 这就是 hierarchy + timestamp 的实战

### 场景 E: ElevenLabs / OpenAI 内部 (本题出处)

- Speech model checkpoint 存在 `/models/voice/v3.2.bin`
- 训练 team 全员能访问最新的, 但 fork 出去的 candidate 模型只有原作者+他指定的 reviewer
- 实习生只能访问 `/models/public_research/`, 且只在实习期间
- Audit 法务有任意时间任意文件查权限, 但任何访问都 log

---

## 6. 工程上要做什么 — 实现 checklist

**Stage 0: Clarify (5 min)**

1. 输入是 stream of events 还是 static snapshot? → 决定是 event-sourced 还是 mutable
2. 单机内存 OK 还是要 distributed? → 决定 DS 选择
3. 查询 QPS? → 决定要不要 cache / materialize
4. Permission model 是 grant/deny 还是只 grant? → 影响 resolution 逻辑
5. 时间是 instant grant (T1 grant, T2 revoke) 还是 interval (effective_from, until)?

**Stage 1: Data Model (10 min)**

6. Define `FileNode` (file_id, parent_id, is_dir, created_at, deleted_at)
7. Define `GrantEvent` (timestamp, user_id, file_id, action GRANT/REVOKE, permission)
8. Define `FileSystem` class with 2 stores: nodes + per-file grants

**Stage 2: Core Algorithms (25 min)**

9. `create_file()`: validate parent exists, store node
10. `apply_grant()`: append to per-file event list (kept sorted)
11. `can_user()`: walk up tree, at each node find latest event ≤ query_time
12. `audit_file()`: dump all events affecting a file (incl. ancestors)

**Stage 3: Edge cases + Test (15 min)**

13. File not yet created at query time
14. File deleted at query time
15. REVOKE in middle of grants
16. Grant at child, revoke at parent — child wins
17. Cycle detection (visited set)
18. Run 2-3 test cases by hand

**Stage 4: Production (5 min)**

19. Cache ancestor chain (write-time)
20. Materialize effective_permission table (denormalized)
21. Negative permission (DENY) precedence
22. Group permission via principal abstraction

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **Cycle detection 忘** | Hierarchy 循环时无限 loop |
| 2 | **没考虑 REVOKE** | 默认 grant 永远有效 |
| 3 | **Inherit 方向反** | Parent override child (错), 应该 child override parent |
| 4 | **`bisect` off-by-one** | timestamp 边界判断错 |
| 5 | **没考虑 created_at** | File 在 grant 之前就被查 |
| 6 | **没 cleanup deleted file** | Audit 应该能看到历史, 但 active query 不该 |
| 7 | **Code 太长** | 60 min 在 Google Doc 写不完, 留 deep dive 空间 |
| 8 | **没测试** | Google Doc 没 IDE, 必 run tests by hand |
| 9 | **混淆 `<` 和 `≤`** | Time bound 究竟是 inclusive 还是 exclusive |
| 10 | **没 thread safety 讨论** | 高并发下 race condition |

---

## 一句话总结 (Part 1)

> **File system permission with hierarchy + timestamps = "树形 ACL + event log + walk-up resolution + time-aware query"**.
>
> Production 优化点是 **write-time cache ancestor + denormalized effective_permission view**, 让 read 路径快.

---

# Part 2 · 5 个深度工程问题

## ⚙️ Problem 1: Data Model — Tree + Event Log + ACL

### 1.1 Skeleton

```python
from dataclasses import dataclass, field
from typing import Optional
from bisect import bisect_right, insort

@dataclass
class GrantEvent:
    """单条权限变更事件 — 不可变, append-only."""
    timestamp: int           # unix epoch ms
    user_id: str
    file_id: str
    action: str              # 'GRANT' or 'REVOKE'
    permission: str          # 'read' | 'write' | 'admin' | ...

    def __lt__(self, other):
        # 用 timestamp 排序, action 作为 tie-breaker
        return (self.timestamp, self.action) < (other.timestamp, other.action)


@dataclass
class FileNode:
    """一个文件 / 目录节点."""
    file_id: str
    parent_id: Optional[str]
    is_directory: bool
    created_at: int
    deleted_at: Optional[int] = None
    # 主索引: (user_id, permission) → 按 timestamp 排序的 event 列表
    grants: dict = field(default_factory=dict)


class FileSystem:
    def __init__(self):
        self.nodes: dict[str, FileNode] = {}
        # 可选: 缓存 ancestor chain
        self._ancestor_cache: dict[str, list[str]] = {}
```

### 1.2 为什么用 event log 而不是 mutable ACL

**Event-sourced 优势**:

- **时间穿越**: 任意历史时刻的 permission 可查 (audit 必备)
- **Append-only**: 高并发 friendly, 不存在 update conflict
- **Repro / Replay**: 出 bug 可以 replay 到任意时间点 debug
- **审计原生**: 每个 event 自带 "who, when, what"

**Mutable ACL 优势** (我们不用):

- 查询时一行查到结果, 不需要扫 event
- 存储小

**Trade-off**: event-sourced 慢 (每次查要 walk event log) → 用 **cache + materialized view** 加速.

### 1.3 索引选择 — 为什么 `(user_id, permission) → events[]`

```python
# 选项 A: 按 file → all events (一个文件所有 user 所有 perm)
grants: list[GrantEvent]
# 查询时需 filter by (user, perm) — O(N) on event count

# 选项 B (我们选): 按 (user, perm) → events sorted by ts
grants: dict[tuple[str, str], list[GrantEvent]]
# 查询直接 O(log N) bisect

# 选项 C: 全局 user × file × perm → events
# 单文件大时内存浪费
```

**选 B 因为查询模式**: 多数查询是 "**这个 user** 对**这个 file** 有没有**某个 perm**", 直接 hit `(user_id, permission)` key.

### 1.4 持久化考虑

```python
# 内存版 (interview 用)
self.nodes = {}
self.grants = {}

# Production:
#   - PostgreSQL:
#     files (file_id PK, parent_id FK, is_dir, created_at, deleted_at)
#       INDEX (parent_id), INDEX (created_at)
#     grants (id PK, file_id FK, user_id, permission, action, ts)
#       INDEX (file_id, user_id, permission, ts)
#
#   - Or event store (Kafka topic) + projection to PostgreSQL view
#   - Hot path: Redis cache of computed effective_permission
```

---

## ⚙️ Problem 2: Hierarchy Resolution Algorithm — Walk-up + Override

### 2.1 Resolution 规则 (要先确认清楚)

**默认 deny + walk up + child override 模型**:

```
def can_user(user, perm, file, ts):
    current = file
    while current exists:
        # 1. 找当前 node 上 (user, perm) 在 ts 之前最后一条 event
        last_event = find_last_event(current, user, perm, ts)
        if last_event is GRANT:
            return True   # child override 父
        if last_event is REVOKE:
            return False  # 显式拒绝
        # 没 explicit event, 继续向上 walk
        current = parent(current)
    return False  # 全程没 grant, default deny
```

**关键 invariant**: 子节点上的 event **永远** 优先于父节点的, 不论 grant 还是 revoke.

### 2.2 实现

```python
class FileSystem:
    def can_user(self, user_id: str, permission: str,
                 file_id: str, timestamp: int) -> bool:
        """
        判断 user 在 timestamp 时刻对 file 有没有 permission.
        
        规则:
          1. file 必须 created_at <= timestamp < deleted_at
          2. walk up hierarchy from file to root
          3. 在每个 node 上找 (user, permission) 的 latest event <= timestamp
          4. 如果是 GRANT → True; REVOKE → False
          5. 没 explicit event 继续向上
          6. 到 root 还没找到 → default deny
        """
        node = self.nodes.get(file_id)
        if not node:
            return False

        # 时间窗口检查
        if node.created_at > timestamp:
            return False  # file 还没创建
        if node.deleted_at is not None and node.deleted_at <= timestamp:
            return False  # file 已删除

        visited = set()  # cycle protection
        current_id: Optional[str] = file_id

        while current_id is not None and current_id not in visited:
            visited.add(current_id)
            node = self.nodes.get(current_id)
            if not node:
                break

            # 这一层有没有 grant 信息?
            events = node.grants.get((user_id, permission), [])
            if events:
                # bisect_right: 找 ts <= timestamp 的最后一条
                # 用 sentinel 'Z' 来确保同 ts 时 GRANT/REVOKE 都被包含
                idx = bisect_right(
                    events,
                    GrantEvent(timestamp, '', '', 'Z', '')
                ) - 1
                if idx >= 0:
                    last = events[idx]
                    if last.action == 'GRANT':
                        return True
                    if last.action == 'REVOKE':
                        return False
                    # 异常情况 fall through

            current_id = node.parent_id

        return False  # default deny
```

### 2.3 Override 规则的几种变体

**变体 A: Child override Parent (我们的默认)**

```
/dir       grant alice read at T1
/dir/file  revoke alice read at T2
→ query "alice read /dir/file at T3" → False (child REVOKE wins)
```

**变体 B: Deny precedence (任何 REVOKE 都赢)**

```
/dir       revoke alice read at T1
/dir/file  grant alice read at T2
→ query "alice read /dir/file at T3" → False (parent REVOKE forbids)
```

这是 **security-first** 模型, AWS IAM 用这个: explicit deny 永远 win.

```python
def can_user_with_deny_precedence(...):
    # 先 walk 一遍找 explicit DENY (任何 ancestor 有 → False)
    current = file_id
    while current:
        node = self.nodes[current]
        events = node.grants.get((user_id, permission), [])
        idx = bisect_right(events, ...) - 1
        if idx >= 0 and events[idx].action == 'REVOKE':
            return False  # 任何 ancestor 显式 deny → 拒绝
        current = node.parent_id

    # 再 walk 一遍找 GRANT
    current = file_id
    while current:
        node = self.nodes[current]
        events = node.grants.get((user_id, permission), [])
        idx = bisect_right(events, ...) - 1
        if idx >= 0 and events[idx].action == 'GRANT':
            return True
        current = node.parent_id

    return False
```

**变体 C: 严格分层 (Most specific wins)**

```
匹配规则按"最具体"(distance 0 比 distance 1 优先), 不论 grant/revoke
```

### 2.4 Complexity

```
Naive walk-up:
  O(depth × log E)
  where depth = hierarchy depth (~10-20 typically)
        E = events per node per (user, perm)

With ancestor cache:
  O(depth + log E_max_in_chain)

With materialized effective view:
  O(1) — 但 write 时要重算 (Problem 4)
```

---

## ⚙️ Problem 3: Time-bounded Permissions — Effective_from / Until

### 3.1 两种时间模型

**Model A: Event-based (我们目前的)**

```
Event 1: GRANT alice read /file at T1
Event 2: REVOKE alice read /file at T2

Effective: granted for [T1, T2)
```

**Model B: Interval-based**

```
Grant: alice read /file effective_from=T1 effective_until=T2

Effective: granted for [T1, T2)
```

**两者的等价转换**:

```python
def interval_to_events(grant):
    return [
        GrantEvent(grant.effective_from, grant.user, grant.file, 'GRANT', grant.perm),
        GrantEvent(grant.effective_until, grant.user, grant.file, 'REVOKE', grant.perm),
    ]
```

但 interval-based 在某些场景更**自然**:

- Time-limited share (Google Drive 分享 7 天)
- Vacation cover (alice 代 bob 一周)
- Audit window (auditor 1 月内可查)

### 3.2 Interval Tree Implementation

如果用 interval-based, 用 **Interval Tree** 加速查询:

```python
from sortedcontainers import SortedList

@dataclass
class TimedGrant:
    user_id: str
    file_id: str
    permission: str
    effective_from: int
    effective_until: int  # 可为 inf 表示永久

class IntervalACL:
    """
    用 interval tree 加速 'at time T 有效的 grant 是哪些' 查询.
    """
    def __init__(self):
        # 按 effective_from 排序
        self.grants_by_start = SortedList(key=lambda g: g.effective_from)

    def add(self, grant: TimedGrant):
        self.grants_by_start.add(grant)

    def find_at(self, file_id, user_id, permission, ts):
        """找 ts 时刻有效的 grant."""
        # 二分: 所有 effective_from <= ts 的
        idx = self.grants_by_start.bisect_right(
            type('Q', (), {'effective_from': ts})()
        )
        for grant in self.grants_by_start[:idx]:
            if (grant.file_id == file_id and
                grant.user_id == user_id and
                grant.permission == permission and
                grant.effective_until > ts):
                return True
        return False
```

### 3.3 Audit at Point-in-time

```python
def audit_at_time(self, file_id: str, timestamp: int) -> list:
    """返回 timestamp 时刻 file 上所有有效的 (user, perm) grant."""
    effective = []

    # 遍历 file 自己 + 所有 ancestor
    current_id = file_id
    visited = set()
    while current_id and current_id not in visited:
        visited.add(current_id)
        node = self.nodes.get(current_id)
        if not node:
            break

        # 每个 (user, perm) 找 latest event ≤ timestamp
        for (user_id, perm), events in node.grants.items():
            idx = bisect_right(events, GrantEvent(timestamp, '', '', 'Z', '')) - 1
            if idx >= 0:
                last = events[idx]
                if last.action == 'GRANT':
                    effective.append({
                        'user': user_id,
                        'permission': perm,
                        'inherited_from': current_id if current_id != file_id else 'self',
                        'granted_at': last.timestamp,
                    })

        current_id = node.parent_id

    return effective
```

### 3.4 Common 时间相关 gotcha

| 坑 | 应对 |
|---|---|
| Timezone 混乱 | 内部全 UTC, 显示时转 user_tz |
| Clock skew (多 service) | NTP + 留 5s tolerance |
| Inclusive vs exclusive `≤` 还是 `<` | 文档明确约定 (我建议 `[from, until)`) |
| 同 ts 的 GRANT + REVOKE | 排序时 tie-break: REVOKE > GRANT (deny precedence) |
| `effective_until` is None (永久) | 用 `float('inf')` or sentinel `9999-12-31` |

---

## ⚙️ Problem 4: Performance — Memoization / Denormalize / Write-time Computation

### 4.1 Naive Performance

```
10M files, average depth 10
1M users
Query QPS 100k

Per query: O(depth) = 10 hops
Total: 100k × 10 = 1M hops/sec across cluster

→ Manageable if each hop O(1) (in-memory hash + bisect)
→ But Postgres: 10 sequential SELECTs per query = 10ms latency → 不够
```

### 4.2 Ancestor Chain Cache

```python
class FileSystem:
    def _get_ancestor_chain(self, file_id):
        """缓存 file_id → [file_id, parent, grandparent, ..., root]."""
        if file_id in self._ancestor_cache:
            return self._ancestor_cache[file_id]

        chain = []
        current = file_id
        visited = set()
        while current and current not in visited:
            visited.add(current)
            chain.append(current)
            node = self.nodes.get(current)
            if not node:
                break
            current = node.parent_id

        self._ancestor_cache[file_id] = chain
        return chain

    def move_file(self, file_id, new_parent_id):
        """move 时 invalidate cache (含所有 descendant)."""
        # 收所有受影响 descendant
        affected = self._collect_descendants(file_id)
        for f in affected:
            self._ancestor_cache.pop(f, None)
        # 真 move
        self.nodes[file_id].parent_id = new_parent_id
```

**Trade-off**: write 略慢 (invalidate cache), read 快很多.

### 4.3 Materialized Effective Permission View

更激进: 维护一张 **effective_permission** 表, 已经把 hierarchy 解析后的结果存好.

```python
class MaterializedView:
    """
    Table: effective_permission(file_id, user_id, permission, current_state)
    
    每次 grant/revoke event:
      1. 找受影响的所有 (descendant_file, user, perm) 组合
      2. recompute effective_state
      3. update view
    
    Read 路径变成 O(1) 单点查询.
    """
    def __init__(self, fs):
        self.fs = fs
        # (file_id, user_id, perm) → bool (current effective)
        self.view = {}

    def on_grant_event(self, ev):
        # 找所有 descendant 文件
        descendants = self.fs._collect_descendants(ev.file_id)
        for d in descendants:
            # 重新算 can_user (用当前时间作为 query ts)
            new_state = self.fs.can_user(ev.user_id, ev.permission, d, now())
            self.view[(d, ev.user_id, ev.permission)] = new_state

    def can_user_fast(self, user_id, perm, file_id, ts):
        if ts == now():  # only valid for "now" queries
            return self.view.get((file_id, user_id, perm), False)
        # Historical → fallback to walk-up
        return self.fs.can_user(user_id, perm, file_id, ts)
```

**Trade-off**:

- Read O(1) 
- Write O(num_descendants × num_users_affected)
- 适合 **read-heavy** 场景 (典型权限查询: 90% read)

### 4.4 Hot Path Cache

```python
from functools import lru_cache
from cachetools import TTLCache

# Redis-backed cache for hot queries
@lru_cache(maxsize=100000)
def can_user_cached(user_id, perm, file_id, time_bucket):
    """time_bucket = ts // 60 (1 min granularity for caching)."""
    return fs.can_user(user_id, perm, file_id, time_bucket * 60)

# Invalidation: 任何 grant event → drop all cache for affected user × descendants
```

### 4.5 Sharding Strategy (10M+ files)

```
Shard by file_id hash → permission service shards
Shard by user_id      → 用户的所有 grant 在同一 shard

实际:
  Files 表 shard by hash(file_id)
  Grant events shard by hash(file_id)  -- 同 file
  Materialized view sharded by hash(file_id)
  
Cross-shard query (rare): "alice 能访问哪些 file" — scatter-gather
```

---

## ⚙️ Problem 5: Edge Cases + Test Design

### 5.1 Edge Cases Checklist

| Case | 处理 |
|---|---|
| File 还没创建时查 | `created_at > ts` → False |
| File 已删除后查 (current) | `deleted_at <= ts` → False |
| File 已删除, audit 查历史 | Allow walk (audit purpose) |
| Cycle in parent_id | `visited` set 防 infinite loop |
| Symlink (软链接) | 实现一个 `resolve_symlink()` 先解链, 但 follow loop 同样要 cycle detect |
| Grant 在 file 创建之前 | 拒绝写入或忽略 |
| Same ts grant + revoke | Tie-break: REVOKE > GRANT (deny precedence) |
| Multiple grant from different ancestor | child override parent |
| User 不存在 | 默认 False |
| Negative permission | 显式 REVOKE 即可 |
| Race: 同时 grant + revoke | Event log append-only, last-write-wins by ts |
| Mid-flight permission change | 用 query 时的 ts (snapshot semantics) |
| Concurrent move + query | move 之后的查询用新 chain, 之前用旧 chain |
| Empty file_id / None | Defensive: raise ValueError |
| Very deep hierarchy (1000+) | depth limit + cache must handle |
| Permission on file vs directory | 同一框架, is_directory 只是元数据 |

### 5.2 测试用例 (面试展示)

```python
def test_basic_grant_revoke():
    fs = FileSystem()
    fs.create_file('/', None, True, 0)
    fs.create_file('/dir', '/', True, 1)
    fs.create_file('/dir/file.txt', '/dir', False, 2)

    fs.apply_grant(GrantEvent(10, 'alice', '/dir', 'GRANT', 'read'))

    # T=5: alice 还没被 grant
    assert fs.can_user('alice', 'read', '/dir/file.txt', 5) == False
    # T=15: alice 通过 /dir 继承
    assert fs.can_user('alice', 'read', '/dir/file.txt', 15) == True


def test_child_override_parent():
    fs = FileSystem()
    fs.create_file('/', None, True, 0)
    fs.create_file('/dir', '/', True, 1)
    fs.create_file('/dir/secret.txt', '/dir', False, 2)

    fs.apply_grant(GrantEvent(10, 'alice', '/dir', 'GRANT', 'read'))
    fs.apply_grant(GrantEvent(20, 'alice', '/dir/secret.txt', 'REVOKE', 'read'))

    # T=15: alice 通过继承能读
    assert fs.can_user('alice', 'read', '/dir/secret.txt', 15) == True
    # T=25: 显式 revoke 生效
    assert fs.can_user('alice', 'read', '/dir/secret.txt', 25) == False


def test_file_not_yet_created():
    fs = FileSystem()
    fs.create_file('/', None, True, 0)
    fs.create_file('/dir', '/', True, 100)
    fs.apply_grant(GrantEvent(50, 'alice', '/', 'GRANT', 'read'))

    # T=80: dir 还没创建
    assert fs.can_user('alice', 'read', '/dir', 80) == False
    # T=120: dir 已创建, alice 继承
    assert fs.can_user('alice', 'read', '/dir', 120) == True


def test_cycle_protection():
    fs = FileSystem()
    fs.create_file('a', None, True, 0)
    fs.create_file('b', 'a', True, 1)
    # 人为制造 cycle (move b 的子 c 为 a 的 parent)
    fs.nodes['a'].parent_id = 'b'

    # 不应该 infinite loop
    result = fs.can_user('alice', 'read', 'b', 100)
    assert result == False  # no grant, default deny


def test_deleted_file():
    fs = FileSystem()
    fs.create_file('/file', None, False, 0)
    fs.nodes['/file'].deleted_at = 100
    fs.apply_grant(GrantEvent(50, 'alice', '/file', 'GRANT', 'read'))

    # T=80: 文件还在
    assert fs.can_user('alice', 'read', '/file', 80) == True
    # T=120: 文件已删
    assert fs.can_user('alice', 'read', '/file', 120) == False


def test_same_ts_grant_revoke_deny_precedence():
    fs = FileSystem()
    fs.create_file('/file', None, False, 0)
    fs.apply_grant(GrantEvent(50, 'alice', '/file', 'GRANT', 'read'))
    fs.apply_grant(GrantEvent(50, 'alice', '/file', 'REVOKE', 'read'))

    # Same ts: REVOKE wins per our convention
    assert fs.can_user('alice', 'read', '/file', 50) == False
    assert fs.can_user('alice', 'read', '/file', 60) == False
```

### 5.3 Property-based Test (advanced)

```python
from hypothesis import given, strategies as st

@given(
    n_files=st.integers(min_value=1, max_value=100),
    n_grants=st.integers(min_value=0, max_value=200),
)
def test_invariants(n_files, n_grants):
    fs = build_random_fs(n_files, n_grants)

    # Invariant 1: 同 query 多次结果一样
    for user, perm, fid, ts in random_queries(10):
        r1 = fs.can_user(user, perm, fid, ts)
        r2 = fs.can_user(user, perm, fid, ts)
        assert r1 == r2

    # Invariant 2: 时间单调性 (after REVOKE, all future ts 都是 False until next GRANT)
    # ...
```

### 5.4 Race Condition Handling

```python
import threading

class ThreadSafeFileSystem(FileSystem):
    def __init__(self):
        super().__init__()
        self._lock = threading.RLock()

    def apply_grant(self, ev):
        with self._lock:
            super().apply_grant(ev)

    def can_user(self, *args, **kwargs):
        # Read 不需要 lock (event log is append-only)
        return super().can_user(*args, **kwargs)

    def move_file(self, file_id, new_parent_id):
        with self._lock:
            super().move_file(file_id, new_parent_id)
```

**关键洞察**: event log append-only → read 不需要 lock; 只有结构变化 (create/move/delete) 需要 lock.

---

# Part 3 · 把 5 个问题串起来看

这 5 个问题是**同一件事的 5 个 layer**:

1. **Data model** = 「**数据怎么存**」 — Tree + Event log + ACL
2. **Resolution algorithm** = 「**怎么算 effective**」 — Walk-up + Override 规则
3. **Time-bounded** = 「**怎么处理时间**」 — Event vs Interval, audit at time
4. **Performance** = 「**Read 路径怎么快**」 — Cache + Materialize + Shard
5. **Edge cases + Test** = 「**生产怎么不挂**」 — Cycle / Deleted / Race / 测试

面试场: code 占 70% 时间, 后面 30% 留给「production scale」讨论. 不能只写 code 不讨论 scale, 也不能只 talk 不写 code.

---

## 必问 clarifying questions

**1. Input shape**

> "What does input look like — list of grant events, JSON tree, SQL tables? Stream or static? Determines storage."

**2. Permission model**

> "Unix-style (rwx by user/group/world) or ACL-style (per-user explicit)? Inheritance rules — child override parent, deny precedence, most-specific-wins?"

**3. Time semantics**

> "Are grants point-in-time (granted at T1, revoked separately at T2) or interval (effective_from + effective_until)?"

**4. Query types**

> "What questions — 'can user X read file Y at time T?', 'who could read file Y at T?', 'audit trail for file Y'? Decides DS optimization."

**5. Scale**

> "10 files, 100, 10M? Query QPS? Determines whether to cache / materialize / shard."

**6. Group support**

> "Do we need user groups (e.g., 'engineers' role)? Adds principal abstraction layer."

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify input + permission model + queries + scale |
| 5-15 min | Data model + class skeleton (dataclass + types) |
| 15-35 min | Core algorithms: build tree + grant + can_user + audit |
| 35-50 min | Edge cases + test cases (run by hand) |
| 50-60 min | Production scale (cache / materialize / shard / threadsafe) |

---

## 简历专属 reframe

你的 **voice agent multi-tenant + Internal Agent Platform + Indonesia refund tier** 都涉及:

| 题 | 你做过 |
|---|---|
| Hierarchical permissions | Internal Agent Platform — team 树形 RBAC |
| Time-versioned grants | ConvFinQA experiments versioned by timestamp |
| Audit trail | Voice agent compliance logs (per call + per access) |
| Inheritance (child override parent) | ByteDance internal RBAC inherit by org chart |
| Performance: 10M files scale | Voice agent multi-market data partition |
| Tier-based confirmation | Indonesia refund tier with effective time window |
| Group permissions | Internal team's role-based access to tools |
| Negative permission | Compliance carve-outs ("auditor cannot edit, only read") |

**主动 quote**:

> "This is essentially **versioned RBAC + tree inheritance + time-bound grants** — I implemented something very close for our internal Agent Platform: which teams can invoke which tools, with **per-team effective time windows** (interns get 90-day access, externals get 7-day per-ticket). The two tricks that I'd transfer here: (1) **Cache the ancestor chain at write-time**, invalidate on move — reads become O(depth) without graph traversal cost. (2) **Event log + materialized view** — append-only event log gives us audit-at-any-time queries for free; materialized view gives us O(1) hot-path reads. We had 50k tool-access checks per second at peak, and Postgres alone (no view) was hitting connection limits — materialized view was the difference between 10ms and 0.1ms p99. For the Indonesia refund tier system, I added the **interval semantics on top** — auditors get `effective_from + effective_until` instead of point-in-time GRANT/REVOKE, which was more natural for the use case."

---

## 5 follow-ups

**Q1**: "What's time complexity of `can_user`?"

**A**: 
- Naive: `O(depth × log E)` where depth = hierarchy depth (~10-20 typically), E = events per node per (user, perm)
- With ancestor cache: `O(depth + log E_max_in_chain)` (chain is precomputed)
- With materialized effective view: `O(1)` for current-time queries, fallback to naive for historical
- Most file systems depth ≤ 20, so even naive is fast in absolute terms

**Q2**: "How do you handle group permissions?"

**A**: Add a principal abstraction:
```python
@dataclass
class Membership:
    user_id: str
    group_id: str
    granted_at: int
    revoked_at: Optional[int]

# can_user checks user's own grants + all groups they belong to at time T
def can_user(user, perm, file, ts):
    if check_principal(user, perm, file, ts):  # direct user grant
        return True
    for group in active_groups(user, ts):
        if check_principal(group, perm, file, ts):
            return True
    return False
```
**Most permissive wins** unless explicit DENY. Same time-window semantics apply to group membership.

**Q3**: "What if events arrive out of order (delayed)?"

**A**:
- Append to per-node grant list anyway
- **Re-sort** the affected list after insert (O(N log N) but rare for delayed events)
- Or use **sorted insert** (`bisect.insort`) per event — O(N) insert but O(log N) lookup
- For high-volume, use **immutable event log + periodic reconcile** (Lambda architecture style)
- **Invalidate** materialized view for affected (user, file, perm) tuples

**Q4**: "What about deletions of files?"

**A**: 
- Add `deleted_at` to `FileNode` (soft delete)
- `can_user` first checks `created_at <= ts < deleted_at`
- **Audit log preserves grants even after deletion** for compliance
- Hard delete (purge from storage): after retention window (e.g., 90 days), but keep audit reference

**Q5**: "Database design?"

**A**:
```sql
-- Files table
CREATE TABLE files (
    id           TEXT PRIMARY KEY,
    parent_id    TEXT REFERENCES files(id),
    is_directory BOOLEAN,
    created_at   BIGINT,
    deleted_at   BIGINT
);
CREATE INDEX idx_files_parent ON files(parent_id);

-- Permission events table (append-only)
CREATE TABLE permission_events (
    id           BIGSERIAL PRIMARY KEY,
    file_id      TEXT REFERENCES files(id),
    user_id      TEXT,
    permission   TEXT,
    action       TEXT,  -- 'GRANT' or 'REVOKE'
    timestamp    BIGINT
);
CREATE INDEX idx_perm_lookup ON permission_events(file_id, user_id, permission, timestamp);

-- Materialized effective permission (denormalized for hot reads)
CREATE TABLE effective_permission (
    file_id      TEXT,
    user_id      TEXT,
    permission   TEXT,
    has_access   BOOLEAN,
    PRIMARY KEY (file_id, user_id, permission)
);
-- Recompute on grant change (debounce 1s for burst)
```

Add **closure table** for efficient subtree queries:
```sql
CREATE TABLE file_closure (
    ancestor_id   TEXT,
    descendant_id TEXT,
    depth         INT,
    PRIMARY KEY (ancestor_id, descendant_id)
);
-- Lookup all descendants of /dir: WHERE ancestor_id = '/dir'
```

**Q6**: "How would you scale to 1B files?"

**A**:
- **Shard by hash(file_id)** across N nodes
- Each shard has its own files + events + materialized view
- Cross-shard query (rare, e.g., "all alice's files") = scatter-gather
- **Closure table** per shard (parent_id is local to shard if hierarchy is balanced)
- **Hot tenant** (one tenant owns 10% of files) — re-shard by `(tenant_id, file_id)` to spread
- Hot path: Redis cache of effective_permission (TTL 1 min, invalidate on grant event)

---

## ❌ 易错点 (top 10)

1. **Cycle detection 忘** — hierarchy loops can happen on bad data
2. **没考虑 REVOKE** — assume always GRANT
3. **Inherit 方向写反** — child should take precedence
4. **`bisect` 用错** — off-by-one on timestamp comparison
5. **没考虑 file 不存在 at time T** — `created_at` check missing
6. **Test 0 cases** — Google Doc 没 IDE, 必 run tests by hand
7. **Code 太长** — 60 min 内写不完, 留 deep dive 空间
8. **没区分 GRANT vs REVOKE 在同 ts** — tie-break 规则未定义
9. **没 thread safety 提及** — production 必谈
10. **没 audit-at-time** — 错过 event-sourcing 的核心优势

---

## ✅ 加分项 (top 10)

1. **Dataclass + type hints** — clean code in Google Doc
2. **`bisect` for sorted timestamp lookup** (O(log N))
3. **Cycle detection** with visited set
4. **Test cases run by hand** on examples
5. **Time complexity stated**
6. **Production scale considerations** — cache / materialize / shard
7. **Group permissions extension** proactively suggested
8. **Denormalized view for hot path** mentioned
9. **Event-sourced architecture rationale** (audit + repro + append-only)
10. **Deny precedence vs child-override rules** explicitly discussed
11. **Thread safety / race condition** addressed
12. **Symlink / cycle / deleted-file edge cases** noted

---

## 一句话总结

> **File system permission with hierarchy + timestamps = "树形 ACL (per-node grant events sorted by ts) + walk-up resolution (child override parent) + time-aware bisect query + ancestor cache for read perf + materialized view for hot path"**.
>
> 这道题考的不是"你会写树遍历", 是"你 own 过 production RBAC / IAM, 处理过 audit + scale + race".

---

## Cheat Sheet (印 1 页)

```
Data model:
  FileNode {id, parent_id, is_dir, created_at, deleted_at, grants}
  GrantEvent {timestamp, user, file, action GRANT/REVOKE, perm}
  grants: dict[(user, perm)] → sorted_list_of_events

Permission resolution (child override parent):
  walk hierarchy from self upward
  at each node, find latest event ≤ query time
  GRANT → True, REVOKE → False, no event → continue up
  Default: deny
  Cycle: visited set protection

Time variants:
  Event-based: GRANT@T1, REVOKE@T2
  Interval-based: {from: T1, until: T2}
  转换: interval = [GRANT@from, REVOKE@until]

Same-ts tie-break:
  REVOKE > GRANT (deny precedence, security-first)

Deny precedence model (AWS IAM style):
  any explicit REVOKE in ancestor chain → False
  否则 walk for GRANT
  没找 → False

Key algorithms:
  bisect_right for "latest event ≤ timestamp"
  Walk-up while parent_id != None
  Cycle detection via visited set
  
Edge cases checklist:
  - File not yet created at T → False
  - File deleted at T → False
  - File deleted but audit historical → walk allowed
  - Cycle in hierarchy → visited set
  - Same ts GRANT+REVOKE → REVOKE wins
  - Grant before file creation → reject write
  - User doesn't exist → default deny
  - Symlink → resolve first, cycle detect

Performance:
  Naive: O(depth × log E)
  Ancestor cache: O(depth + log E), invalidate on move
  Materialized view: O(1) read, expensive write
  Sharding: hash(file_id) across nodes
  Hot path: Redis 1min TTL

Production schema:
  files(id, parent_id, is_dir, created_at, deleted_at)
    INDEX (parent_id)
  permission_events(file_id, user_id, perm, action, ts)
    INDEX (file_id, user_id, perm, ts)
  effective_permission(file_id, user_id, perm, has_access)
    PK (file_id, user_id, perm)
  file_closure(ancestor_id, descendant_id, depth)  -- for subtree

Group support:
  Membership(user, group, granted_at, revoked_at)
  can_user = check(user) || any(check(group) for group in active_groups)
  Most permissive wins (unless explicit DENY)

Thread safety:
  Read = no lock (event log append-only)
  Write structural (create/move/delete) = RLock
  Write event (grant/revoke) = append atomic

Time complexity summary:
  Naive: O(depth × log E)
  Cached: O(depth + log E)
  Materialized: O(1) current, O(depth × log E) historical

红线:
  - 没 cycle detection
  - REVOKE 没考虑
  - bisect off-by-one
  - 没 created_at / deleted_at 检查
  - 没 test 跑一遍
  - 60min 写不完 (代码太长)
```
