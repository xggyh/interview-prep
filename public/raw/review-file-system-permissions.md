## Tech #6 · File System Permissions — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](file-system-permissions.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`file-system-permissions.html`](file-system-permissions.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"设计一个 hierarchical file system permission system, 支持 (a) Alice grants Bob read on folder X at T1, (b) revokes at T2, (c) check 'did Bob have access at T1.5 on file X/Y/Z' efficiently"** 我按这 7 层回答, 不跳序.

### 📐 File System Permissions — 7 层 design

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 |
|---|---|---|---|---|
| 1 | Clarify scope 3 question | 30s | 反问: (a) read-heavy vs write-heavy ratio? (b) deny precedence or override allowed? (c) max tree depth + branching factor? — 这 3 个 question 决定 schema | "Before design — 3 clarifying questions on read/write ratio, deny semantics, tree shape…" |
| 2 | Data model: event-sourced ACL | 1.5 min | Per node, list of grant_event: `(file_id, principal, permission, action, granted_at, granted_by, valid_from, valid_to)`. Event sourced append-only — 天然 time-travel audit, never UPDATE never DELETE, revoke = new event with action=revoke. Postgres / Firestore / Bigtable | "Data model — append-only grant_event table per node, time-travel for free, revoke = new event not UPDATE…" |
| 3 | Walk-up resolution algorithm | 2 min | Check access(file_id, principal, ts): traverse from file_id up to root, at each node fetch grants where principal IN (user OR user's groups) AND valid_from ≤ ts AND (valid_to IS NULL OR valid_to > ts), latest event by granted_at. Child override parent default; **deny precedence variant** — single deny anywhere in chain wins | "Walk-up — from file to root, latest-event-≤-ts per node, child overrides parent, optional deny-precedence…" |
| 4 | Time-aware bisect query | 1.5 min | Query "at ts T, did principal P have access on F?" → binary search on sorted (granted_at) per node — O(log E) per node × depth = O(depth × log E). Index on (file_id, principal, granted_at) | "Time query — sorted by granted_at per node, bisect for latest ≤ ts, O(depth × log E)…" |
| 5 | Production scale: cache + materialized | 1.5 min | Read-heavy → 2 optimization: (a) **write-time ancestor cache** — on grant, push event to descendant cache (denormalize, write amplification); (b) **read-time materialized view** — periodic batch recompute "effective permission at now" per (file, principal). Trade-off: write cache (real-time, write-heavy) vs materialized (stale, read-heavy with low staleness tolerance) | "Scale — write-time ancestor cache (write amplification) or read-time materialized view (staleness trade-off)…" |
| 6 | Sharding + concurrency | 1 min | Shard by hash(root_folder_id) — keeps subtree together, cross-shard rare. Concurrency: per-file_id row lock on write (Postgres SELECT FOR UPDATE), read goes through cache (no lock). Conflict on simultaneous grant — latest granted_at wins, application enforces no contradictory grant at exact same ts (add nanosecond tiebreaker) | "Sharding — by root_folder_id keeps subtree colocated, per-file write lock, read via cache lock-free…" |
| 7 | Resume hook | 1 min | "Concrete: Internal Agent Platform shared memory + permission abstraction. Per-agent memory tree (per-tenant root) with event-sourced ACL. Used across 200+ agent. Hierarchical scope (per-tenant → per-user → per-conversation), time-travel useful for incident replay ('what did agent see at T-5 min?'). Same pattern from filesystem permission generalizes to agent memory permission" | "Real example — Internal Agent Platform uses same event-sourced ACL for agent memory permission, time-travel for incident replay…" |

### 🎯 为啥按这个序

Clarify 第一 because permission system 有 5+ design path — 选错 path 花 30 min. Event-sourced ACL 是关键设计决策 (append-only → time-travel 自然, audit 自然). Walk-up + time-aware bisect 是算法核心. Scale optimization 是 "production-grade 还是 academic" 的 signal. Sharding + concurrency 是 distributed gotcha. Resume hook 用 Agent Platform 真案例 land (file system permission 概念 generalize 到 agent memory).

### 🔥 哪一层最容易被追问 deeper

**Layer 3 (walk-up + deny precedence)** — 必被追 "What if deny on parent but allow on child?" → 答 design decision — 2 variant: (a) **child override** (UNIX behavior, allow-wins per node), (b) **deny precedence** (AWS IAM behavior, explicit deny anywhere blocks). 我默认 child override for usability (folder owners can grant deeper), 但 enterprise / compliance system 用 deny precedence (security default). 客户 contract 必须 explicit.

**Layer 5 (cache vs materialized)** — 追 "Which would you pick?" → 答: depends on R/W ratio + freshness tolerance. Read 100:1 write + sub-second freshness → write-time ancestor cache (push grant to descendants on grant). Read 10:1 + minute-level staleness → materialized view (batch recompute every 1 min). Both — write-time for security-critical perms + materialized for analytical query. 关键: 不写直查表 at production scale.

### ⏱ 时间压缩版 (30 min round)

- 0-3 min: Layer 1+2 (clarify + event-sourced model)
- 3-12 min: Layer 3+4 (walk-up + time-aware bisect)
- 12-20 min: Layer 5+6 (cache/materialized + sharding)
- 20-26 min: Layer 7 Agent Platform generalize
- 26-30 min: Q&A buffer

### 🆘 卡壳兜底 (针对这题)

- 不熟 event-sourcing → "append-only log of state changes, current state = fold(events); 优点 audit + time travel + replay; trade-off 是 query 慢 (用 cache / materialized view)"
- 被问 "how to garbage collect old events" → "tombstone snapshot at T_n, keep events from T_n onwards; compliance retention 7y minimum for finance, configurable per-tenant"
- 不会画 schema → tables: `grant_event(id, file_id, principal_id, permission, action, valid_from, valid_to, granted_at, granted_by)` + index `(file_id, principal_id, granted_at DESC)` + `effective_permission_cache(file_id, principal_id, permission, updated_at)`

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 核心心智模型 (1 sentence)

File system permission with hierarchy + timestamps = "树形 ACL (per-node grant events sorted by ts) + event-sourced append-only (天然 time-travel audit) + walk-up resolution (child override parent default, deny precedence variant available) + time-aware bisect query (latest event ≤ ts) + ancestor cache write-time / materialized view read-time / shard by hash(file_id) for scale", production 优化路径 read-heavy → cache + denormalize.

### 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Hierarchy | tree, parent ← child, 权限子继承父 child override | 主结构 |
| Time-bounded ACL | grant 有 effective_from / until 或 event GRANT+REVOKE | 本题考的 |
| GrantEvent | append-only immutable {ts, user, file, GRANT/REVOKE, perm} | 数据 model |
| Event-sourced | 不是 mutable state 是 event log | 时间穿越 audit |
| Walk-up resolution | child → parent → grandparent → root, 首个 explicit 决定 | 主算法 |
| Child override parent | default 子节点 event 永远优先父 | 多数 file system |
| Deny precedence | AWS IAM 风格, 任何 ancestor explicit REVOKE → False | 严合规变体 |
| Effective permission | 某 ts 某 user 某 file 某 action 的计算结果 (不存储) | resolution 结果 |
| Ancestor cache | file_id → [self, parent, ..., root] write-time 算 | read 加速 |
| Materialized view | (file, user, perm) → effective_state 表 | O(1) hot path |
| bisect_right | sorted list 找 latest event ≤ ts | O(log E) |
| Cycle detection | visited set 防 infinite walk-up | 数据 bad 时 |
| Closure table | (ancestor, descendant, depth), 子树查询 | scale |
| RBAC | Role-Based Access Control, role-perm + user-role | 扩展 group |
| Principal | user 或 group 抽象 | group permission |
| Soft delete | deleted_at 标记不真删, audit 仍可查 | compliance |

### 5 个核心 framework / pattern

**Framework 1**: Data model — Tree + Event log + ACL
- When: 建立 storage
- Algorithm: FileNode {file_id, parent_id, is_dir, created_at, deleted_at, grants}; GrantEvent {ts, user, file, action GRANT/REVOKE, perm}; grants: dict[(user, perm)] → sorted_list_of_events
- Trade-off: event-sourced 慢 + audit-friendly vs mutable 快 + no time-travel
- Tools: dataclass, bisect.insort for sorted insert, Postgres for persistence

**Framework 2**: Walk-up resolution (child override parent)
- When: can_user(user, perm, file, ts) 查询
- Algorithm: check created_at ≤ ts < deleted_at; walk current → parent → ... → root; bisect_right 找 latest event ≤ ts; GRANT → True, REVOKE → False, no event → continue up; default deny; cycle visited set
- Trade-off: child override 灵活 vs deny precedence 安全
- Tools: bisect_right, visited set, while parent_id != None

**Framework 3**: Time semantics (event vs interval)
- When: 时间窗口设计
- Algorithm: event-based (GRANT@T1, REVOKE@T2) ↔ interval-based ({from: T1, until: T2}) 等价转换; interval 更自然 (7-day share, vacation cover); same-ts tie-break REVOKE > GRANT
- Trade-off: event-based 一致 model, interval 更直觉
- Tools: Interval tree, SortedList, ZoneInfo UTC

**Framework 4**: Performance (cache / materialize / shard)
- When: 10M+ files, 100k QPS
- Algorithm: Naive O(depth × log E) → ancestor cache write-time O(depth + log E) → materialized view O(1) for current; sharding hash(file_id); hot path Redis 1min TTL
- Trade-off: write 慢 + read 快, 适合 read-heavy
- Tools: lru_cache, Redis TTLCache, Postgres effective_permission table

**Framework 5**: Edge cases checklist
- When: 测试 + production
- Algorithm: file 未创建 (created_at > ts) / file 已删 (deleted_at ≤ ts, active query 拒, audit 允许) / cycle (visited set) / symlink (resolve_symlink + cycle detect) / same-ts grant+revoke (REVOKE wins) / user 不存在 (default deny)
- Trade-off: 60 min Google Doc 必跑 2-3 test
- Tools: pytest, hypothesis property-based, by-hand test on Google Doc

### 关键决策树 (ASCII)

```
can_user(user, perm, file, ts):
   |
   v
file 存在? → NO → False
   |
   v
created_at ≤ ts ≤ deleted_at? → NO → False
   |
   v
current = file_id, visited = {}
   |
   v
while current not in visited:
   visited.add(current)
   events = node.grants.get((user, perm), [])
   idx = bisect_right(events, ts) - 1
   if idx >= 0:
      if GRANT → return True
      if REVOKE → return False
   current = node.parent_id (continue up)
   |
   v
walk done → return False (default deny)

Override variant:
- Default: child wins (immediate return at first explicit)
- Deny precedence: pass 1 find any REVOKE → False; pass 2 find GRANT → True
- Most-specific: same as default child wins
```

### Part 2 五个深度问题速查

**Problem 1: Data model (Tree + Event log + ACL)**
- 核心解法: FileNode + GrantEvent dataclass; per-node grants: dict[(user, perm)] → sorted_events; event-sourced (append-only) > mutable ACL for audit + time-travel
- Top 3 gotchas: 索引选 (user, perm) → events 而不是 file → all events / event-sourced 慢 → cache + materialize 加速 / persistence Postgres files + permission_events with composite index
- Tools: dataclass, bisect.insort, Postgres index (file_id, user_id, permission, timestamp)

**Problem 2: Hierarchy resolution (walk-up + override)**
- 核心解法: walk current → parent → root, bisect latest ≤ ts, GRANT/REVOKE 决定否则继续上, cycle 用 visited set
- Top 3 gotchas: child override parent (默认) vs deny precedence (AWS IAM 安全 variant) vs most-specific / cycle (parent_id 循环) / inclusive vs exclusive (≤ vs <)
- Tools: bisect_right + sentinel for tie-break, visited set, while-loop iteration

**Problem 3: Time-bounded (event vs interval)**
- 核心解法: 两种 model 等价转换 (interval = [GRANT@from, REVOKE@until]); same-ts tie-break REVOKE > GRANT (deny precedence); audit_at_time 遍历 self + ancestors 返回 effective grants
- Top 3 gotchas: timezone 内部 UTC 显示 local / clock skew NTP + 5s tolerance / inclusive `[from, until)` 约定
- Tools: Interval tree, ZoneInfo, sortedcontainers SortedList

**Problem 4: Performance (memoize / denormalize / shard)**
- 核心解法: naive O(depth × log E) → ancestor cache (invalidate on move) → materialized effective_permission view (O(1) current) → sharding hash(file_id) for 1B
- Top 3 gotchas: cache invalidation on move/delete (collect descendants) / materialized view recompute cost on grant event / Redis TTLCache 1min for hot path
- Tools: cachetools TTLCache, debounce 1s for batch recompute, Postgres effective_permission table

**Problem 5: Edge cases + Test**
- 核心解法: created_at / deleted_at check / cycle detection / symlink resolve / same-ts tie-break / user not exist / race condition (event log append-only read no lock, write structural use RLock)
- Top 3 gotchas: file 已删 active query 拒 audit 允许 / hard delete 7-day grace + admin confirm / property-based test with hypothesis for invariants
- Tools: pytest, hypothesis, threading.RLock for structural change

### Production gotchas (top 15)

1. Cycle detection 忘 → infinite loop
2. 没考虑 REVOKE (default 永久 grant)
3. Inherit 方向反 (parent override child = 错)
4. bisect off-by-one (≤ vs <)
5. 没考虑 created_at (file 在 grant 前查)
6. 没 cleanup deleted file (audit 允许 active query 拒)
7. Code 太长 60min 写不完
8. 没测试 by hand (Google Doc 无 IDE)
9. 同 ts grant + revoke 没 tie-break 规则
10. 没 thread safety 讨论 (race condition)
11. Symlink follow loop 没 cycle detect
12. Group permission 没设计 principal 抽象
13. Materialized view recompute cost 估错 (descendant 数巨大)
14. 没 shard by hash(file_id) 单 DB 撑不到 1B
15. Audit log retention 没区分 active vs deleted

### 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Hierarchical permissions | Internal Agent Platform | team 树形 RBAC, manifest-based |
| Time-versioned grants | ConvFinQA experiments | versioned by timestamp |
| Audit trail | Voice agent compliance | per-call + per-access immutable |
| Child override parent inherit | ByteDance internal RBAC | org chart inheritance |
| Performance: 10M+ files | Voice agent multi-market | shard by market |
| Tier-based with time window | Indonesia refund tier | confirmation effective until 48h escalate |
| Group permissions | Team's role-based tool access | principal abstraction with active groups at ts |
| Negative permission | Compliance carve-outs | "auditor cannot edit, only read" |
| Cache + materialize | 50k tool-access checks/s peak | Postgres view → 10ms → 0.1ms p99 |

### 面试现场 quotables (top 8)

1. "Event-sourced (append-only) over mutable ACL — time travel queries for free, audit-friendly, append no conflict on concurrent writes."
2. "Walk-up resolution: child override parent. Cycle protection visited set. bisect_right for latest event ≤ ts is O(log E)."
3. "Same-ts grant + revoke: REVOKE wins (deny precedence). AWS IAM style: any ancestor REVOKE → False regardless of child."
4. "Performance ladder: naive O(depth × log E) → ancestor cache O(depth) → materialized view O(1). Shard by hash(file_id) for 1B."
5. "Internal Agent Platform: 50k tool-access checks/s. Postgres alone hit conn limits. Materialized effective_permission view → 10ms → 0.1ms p99."
6. "Interns get 90-day access, externals get 7-day per-ticket. Time-bounded grants are natural for this — interval semantics on top of event log."
7. "Edge cases: file not created at ts → False. File deleted at ts → False (active) but audit allows walk. Cycle in parent_id → visited set."
8. "Indonesia refund tier with 48h window: agent gets effective_from + effective_until, auto-escalates if no human action."

### 红线 (top 10 anti-patterns)

1. No cycle detection (infinite loop)
2. REVOKE 没考虑 (perpetual grant)
3. Inherit direction reversed
4. bisect off-by-one (≤ vs <)
5. No created_at / deleted_at check
6. No tests run by hand (Google Doc trap)
7. Same-ts tie-break 未定义
8. No thread safety mentioned
9. Symlink follow no cycle protect
10. No materialized view for read-heavy

### 5 permission models comparison

| Model | Definition | Example | Complexity |
|---|---|---|---|
| Unix-style | owner/group/world × rwx | `chmod 644` | Low |
| POSIX ACL | + per-user/group entry | `setfacl -m u:alice:rwx` | Medium |
| RBAC | role → perm, user → role | "editor" role | Medium |
| ABAC | rule engine on attributes | "role=editor AND dept=eng" | High |
| Time-bounded ACL ⭐ | ACL + effective_from/until | "alice can read until 2024-12-31" | Medium |

### Resolution variant override rules

| Variant | Behavior | Used in |
|---|---|---|
| Child override Parent (默认) | Walk up, first explicit (GRANT or REVOKE) wins | Unix, Google Drive |
| Deny precedence | Any ancestor REVOKE → False, else GRANT walk | AWS IAM, security-first |
| Most-specific wins | Same as child override | Most file systems |
| Group union | Union of user + all groups, most permissive wins | RBAC + group |

### Same-ts tie-break conventions

| Convention | Behavior | Used in |
|---|---|---|
| REVOKE > GRANT | Deny precedence, security-first | Recommended |
| Order of insertion | Whichever inserted last wins | Naive impl |
| GRANT > REVOKE | Most permissive | Permissive-first (rare) |

### Test cases checklist (run by hand on Google Doc)

| Test | Expected |
|---|---|
| Basic grant + revoke | grant T1 → True at T2, revoke T3 → False at T4 |
| Child override parent | parent GRANT, child REVOKE → False on child |
| File not yet created | created_at=100, query at T=50 → False |
| File deleted | deleted_at=100, query at T=120 → False (active) |
| Cycle in parent_id | infinite loop avoided via visited set |
| Same ts GRANT + REVOKE | REVOKE wins per deny precedence |
| User doesn't exist | default deny → False |
| Symlink loop | resolve + cycle detect, default deny |
| Race grant + query | event log append-only, last-write-wins by ts |
| Group + user combined | most permissive, deny precedence on any REVOKE |

### Production schema (Postgres)

| Table | Columns | Index |
|---|---|---|
| files | id PK, parent_id FK, is_directory, created_at, deleted_at | (parent_id), (created_at) |
| permission_events | id PK, file_id FK, user_id, permission, action, timestamp | (file_id, user_id, permission, timestamp) |
| effective_permission (materialized) | file_id, user_id, permission, has_access | PK (file_id, user_id, permission) |
| file_closure | ancestor_id, descendant_id, depth | PK (ancestor_id, descendant_id) |
| membership (for groups) | user_id, group_id, granted_at, revoked_at | (user_id), (group_id) |

### Performance ladder

| Stage | Complexity | Trade-off |
|---|---|---|
| Naive walk-up | O(depth × log E) | 简单, depth ≤ 20 实际 fast |
| Ancestor cache (write-time) | O(depth + log E) | move invalidate, read 快 |
| Materialized view | O(1) for current ts | grant event recompute descendants |
| Sharding hash(file_id) | distribute across N nodes | scatter-gather for "alice's all files" |
| Hot path Redis | O(1) with TTL 1 min | invalidate on grant event |

### Time semantics models

| Model | Spec | Equivalent |
|---|---|---|
| Event-based | GRANT@T1, REVOKE@T2 | granted for [T1, T2) |
| Interval-based | {effective_from: T1, effective_until: T2} | granted for [T1, T2) |
| Equivalence | interval = [GRANT@from, REVOKE@until] | bi-directional |
| Convention | `[from, until)` inclusive-exclusive | document explicitly |

### 5 业务场景变体 (anchor stories)

| Variant | Hierarchy | Time-bound |
|---|---|---|
| Internal Agent Platform (ByteDance) | /agent_platform/tools/payments_api | intern: 90-day, contractor: 7-day per-ticket |
| TikTok PayLater multi-market | /data/indonesia/, /data/vietnam/, etc. | auditor temp 1-week-long ticket |
| Indonesia refund tier confirmation | /pending_confirms/{refund_id}/ | region head: 48h, then escalate |
| Google Drive doc share | /docs/q4_earnings.xlsx | "view only, expires in 7 days" |
| ElevenLabs model checkpoint | /models/voice/v3.2.bin | intern: 实习期间, candidate model: original author + reviewers |

### Edge case test matrix (Google Doc 必跑 by hand)

| Test | Setup | Expected |
|---|---|---|
| Basic grant + revoke | grant @ T=10, query @ T=15 | True |
| Child override parent | parent grant, child revoke | False at child |
| File not yet created | created_at=100, query @ T=80 | False |
| File deleted | deleted_at=100, query @ T=120 | False |
| Cycle in parent_id | a → b → c → a | no infinite loop, default deny |
| Same ts GRANT + REVOKE | both @ T=50 | False (deny precedence) |
| User doesn't exist | random user_id | False |
| Symlink loop | /a → /b, /b → /a | resolve + cycle detect |
| Deleted file audit | audit @ T after deleted_at | walk allowed, historical record |
| Group + user combined | user has direct + via group | most permissive, deny precedence |
| Race grant + query | concurrent | last-write-wins by ts |

### Group permission extension (principal abstraction)

| Concept | Definition |
|---|---|
| Principal | user OR group, unified abstraction |
| Membership | {user_id, group_id, granted_at, revoked_at} |
| can_user with groups | check user's direct + all active groups at ts |
| Resolution | most permissive wins, deny precedence on any explicit REVOKE |
| Active group at ts | granted_at ≤ ts < revoked_at |
| Storage | membership table separate, index (user_id), (group_id) |
