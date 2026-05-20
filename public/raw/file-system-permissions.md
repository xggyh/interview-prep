## 题目（verbatim）

> **[ElevenLabs FDE Coding Round]**
>
> In Google Doc with Python: **Assess permissions in a file system based on user IDs**. Account for **hierarchy and timestamps**.

**出处**：ElevenLabs FDE 真题（候选人 report via Exponent guide）。Production-ish coding 题, 不是纯 LeetCode.

**Round**：Coding (60 min, Google Doc with Python)

---

## 这道题在考什么

考你**production-system coding** —— 不是 algo puzzle, 是接近真实业务：

1. **Data structure choice** —— tree (file hierarchy) + interval / event log (timestamps)
2. **Permission inheritance** —— child inherits parent unless overridden
3. **Time-aware queries** —— "what could user X do at time T"
4. **Edge cases** —— deleted file, transferred ownership, expired grants
5. **Clean code** —— Google Doc 没 syntax check, 错一个 colon 看半天

---

## Clarifying questions (必问)

**1. Data shape**

> "What does the input look like — list of grant events, JSON tree, SQL tables? Stream or static?"

**2. Permission model**

> "Are permissions Unix-style (read/write/execute by user/group/world) or ACL-style (per-user explicit list)? Inheritance? Negative permissions (explicit deny)?"

**3. Time semantics**

> "Are grants point-in-time (granted at T1, valid until T2) or step events ('granted at T1', revoked separately)?"

**4. Query types**

> "What questions do we answer — 'can user X read file Y now?', 'who could read file Y at time T?', 'audit trail for file Y'?"

**5. Scale**

> "10 files, 100, 10M? Determines DS choice and whether to think about indexing."

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify data shape + queries |
| 5-15 min | Data model + class skeleton |
| 15-35 min | Core algorithms: build tree + grant interval + query |
| 35-50 min | Edge cases + test |
| 50-60 min | Production considerations (caching / index / persistence) |

---

## 我会这样答（with code）

> "Clarify — *[假设：input is stream of events (CREATE_FILE, GRANT_PERMISSION, REVOKE_PERMISSION) each with timestamp; ACL-style with inheritance; queries are 'can user X do action A on file Y at time T?']*.
>
> Let me first set up the data model:

```python
from dataclasses import dataclass, field
from typing import Optional
from bisect import bisect_left, bisect_right

@dataclass
class GrantEvent:
    """Permission change event."""
    timestamp: int           # unix ms
    user_id: str
    file_id: str
    action: str              # 'GRANT' or 'REVOKE'
    permission: str          # 'read' | 'write' | 'admin'

@dataclass
class FileNode:
    """A file or directory in the hierarchy."""
    file_id: str
    parent_id: Optional[str]
    is_directory: bool
    created_at: int
    # Per (user_id, permission) → sorted list of (timestamp, action) events
    grants: dict = field(default_factory=dict)

class FileSystem:
    def __init__(self):
        self.nodes: dict[str, FileNode] = {}
        # For fast hierarchy traversal: child → parent lookup is direct
        # But we'll also cache: file_id → ancestors list

    def create_file(self, file_id: str, parent_id: Optional[str], 
                    is_directory: bool, timestamp: int):
        if file_id in self.nodes:
            raise ValueError(f"File {file_id} already exists")
        if parent_id is not None and parent_id not in self.nodes:
            raise ValueError(f"Parent {parent_id} doesn't exist")
        self.nodes[file_id] = FileNode(file_id, parent_id, is_directory, timestamp)

    def apply_grant(self, ev: GrantEvent):
        """Record a grant or revoke event for (user, file, permission)."""
        node = self.nodes.get(ev.file_id)
        if not node:
            raise ValueError(f"File {ev.file_id} doesn't exist")
        key = (ev.user_id, ev.permission)
        if key not in node.grants:
            node.grants[key] = []  # sorted list of (timestamp, action)
        node.grants[key].append((ev.timestamp, ev.action))
        # Keep sorted; in practice events arrive in order, so just append

    def can_user(self, user_id: str, permission: str, 
                 file_id: str, timestamp: int) -> bool:
        """Check if user has permission on file at given time.
        
        Walks up the hierarchy. First explicit GRANT or REVOKE in 
        ancestor chain (including self) wins.
        """
        node = self.nodes.get(file_id)
        if not node or node.created_at > timestamp:
            return False
        
        current_id = file_id
        while current_id is not None:
            node = self.nodes[current_id]
            grants = node.grants.get((user_id, permission), [])
            # Find latest event with timestamp <= query timestamp
            idx = bisect_right(grants, (timestamp, '\\xff')) - 1
            if idx >= 0:
                last_ts, action = grants[idx]
                if action == 'GRANT':
                    return True
                elif action == 'REVOKE':
                    return False
                # If somehow weird, fall through to parent
            current_id = node.parent_id
        
        return False  # no grant found, default deny

    def audit_file(self, file_id: str) -> list:
        """Return all events affecting this file or its ancestors."""
        events = []
        current_id = file_id
        while current_id is not None:
            node = self.nodes[current_id]
            for (uid, perm), grants in node.grants.items():
                for ts, action in grants:
                    events.append((ts, current_id, uid, perm, action))
            current_id = node.parent_id
        return sorted(events)
```

> Now let me walk through edge cases:
> 1. **File doesn't exist at query time** (created_at > timestamp): `can_user` returns False. ✓
> 2. **REVOKE overrides earlier GRANT at same level**: bisect finds latest event before timestamp. ✓
> 3. **Grant at child, revoke at parent — child wins**: we walk child first, find GRANT, return True. ✓
> 4. **Grant at parent, no setting at child**: child has no entry, parent has GRANT, return True. ✓
> 5. **Cycle in hierarchy**: would loop. **Add cycle detection** with visited set.

> Let me add cycle detection and a quick test:

```python
    def can_user(self, user_id, permission, file_id, timestamp):
        visited = set()
        current_id = file_id
        while current_id is not None and current_id not in visited:
            visited.add(current_id)
            # ... same as before
            current_id = self.nodes[current_id].parent_id
        return False

# Quick test
fs = FileSystem()
fs.create_file('/', None, True, 0)
fs.create_file('/dir', '/', True, 1)
fs.create_file('/dir/secret.txt', '/dir', False, 2)
fs.apply_grant(GrantEvent(10, 'alice', '/dir', 'GRANT', 'read'))
fs.apply_grant(GrantEvent(20, 'alice', '/dir/secret.txt', 'REVOKE', 'read'))

assert fs.can_user('alice', 'read', '/dir/secret.txt', 5) == False  # before grant
assert fs.can_user('alice', 'read', '/dir/secret.txt', 15) == True  # inherits from /dir
assert fs.can_user('alice', 'read', '/dir/secret.txt', 25) == False  # explicit revoke at file
```

> **Production considerations** (if interviewer asks):
> 1. **Scale** to 10M files: cache ancestor chain per node (compute once on create, invalidate on move). O(1) parent lookup → O(depth) per query.
> 2. **Hot path**: cache `(user, file, time) → bool` with short TTL if query is repeat.
> 3. **Group permissions**: extend to support `(group_id, file)` grants + `(user, group)` memberships.
> 4. **Negative permissions** (explicit DENY): change model so DENY > GRANT at same level, walk continues only if no explicit setting.
> 5. **Persistence**: events to event store (Kafka), nodes to SQL with `(parent_id)` index.

⏱️ ~30-40 min of coding given Google Doc. 留 5-10 min for production discussion.

---

## 简历专属 reframe

你的 **voice agent multi-tenant + IAM-style permissions** 直接 reframe：

| 题 | 你做过 |
|---|---|
| Hierarchical permissions | Voice agent 7 markets × multi-team access |
| Time-versioned grants | ConvFinQA experiments versioned by timestamp |
| Audit trail | Voice agent compliance logs |
| Inheritance | Bytedance internal RBAC inherit by org chart |
| Performance: 10M files | You think about scale instinctively |

**主动说**:

> "This is essentially **versioned RBAC + tree inheritance** — I implemented something similar for the voice agent's internal tool access (which markets can invoke which workflows). The trick I'd transfer: **cache the ancestor chain at write-time, invalidate on move**, so reads are O(depth) without graph traversal cost."

---

## 5 follow-ups

**Q1**: "What's time complexity of `can_user`?"
**A**: O(depth × log E) where depth is hierarchy depth, E is events per node per (user, perm). With ancestor caching: O(depth + log E_total). Most file systems depth ≤ 20.

**Q2**: "How do you handle group permissions?"
**A**: Add `groups: dict[user_id, set[group_id]]` and modify grants to be keyed by `(principal, permission)` where principal = `user:alice` or `group:engineers`. `can_user` checks user's grants + all groups they belong to. Take **most permissive** unless explicit DENY.

**Q3**: "What if events arrive out of order (delayed)?"
**A**:
- Append to per-node grant list anyway
- **Re-sort** the affected list after insert (O(N log N) but rare)
- Or use **sorted insert** (bisect.insort) per event
- For high-volume, use immutable event log + periodic reconcile

**Q4**: "What about deletions of files?"
**A**: Add `deleted_at` to FileNode. `can_user` first checks `created_at <= timestamp < deleted_at`. **Audit log preserves grants even after deletion** for compliance.

**Q5**: "Database design?"
**A**:
- `files (id, parent_id, is_dir, created_at, deleted_at)` indexed by parent_id
- `permission_events (file_id, user_id, permission, action, timestamp)` indexed by (file_id, user_id)
- Hot read path: **denormalized materialized view** of effective permissions per (user, file)
- Recompute on grant change (debounce 1s)

---

## ❌ 易错点

1. **Cycle detection 忘** — hierarchy loops can happen on bad data
2. **没考虑 REVOKE** — assume always GRANT
3. **Inherit 方向写反** — child should take precedence
4. **bisect 用错** — off-by-one on timestamp comparison
5. **没考虑 file 不存在 at time T** — `created_at` check
6. **Test 0 cases** — Google Doc 没 IDE, 必 run tests by hand
7. **Code 太长** — 60min 内写不完, 留 deep dive 空间

---

## ✅ 加分项

1. **Dataclass + type hints** — clean code
2. **bisect** for sorted timestamp lookup (O(log N))
3. **Cycle detection** with visited set
4. **Test cases run** by hand on examples
5. **Time complexity** stated
6. **Production scale considerations** at end
7. **Group permissions** extension proactively
8. **Denormalized view for hot path**

---

## Cheat Sheet

```
Data model:
  FileNode {id, parent_id, is_dir, created_at, grants}
  GrantEvent {timestamp, user, file, action GRANT/REVOKE, perm}
  
Permission resolution:
  walk hierarchy from self upward
  at each node, find latest event ≤ query time
  GRANT → True, REVOKE → False
  Default: deny

Key algorithms:
  bisect_right for "latest event ≤ timestamp"
  Cycle detection via visited set
  
Edge cases:
  - File not yet created at time T → False
  - File deleted → check deleted_at
  - Child grant overrides parent revoke (specific > inherited)
  - REVOKE in middle of grant chain → blocks

Production:
  Cache ancestor chain on create
  Materialize effective perm view
  Group support via principal abstraction
  Event log + periodic reconcile

Time complexity:
  Naive: O(depth × E)
  Cached: O(depth + log E)
  Materialized: O(1)
```
