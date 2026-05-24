## T1.4 · destructive tools wrapping — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](gfde-t1-destructive-tools.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t1-destructive-tools.html`](gfde-t1-destructive-tools.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"How to wrap `delete_user`, `send_email`, `charge_customer` so agent doesn't accidentally destroy something"** 或 **"Agent deleted 50 users, 10 were real customers — what did you fail to build?"**, 我按这 8 层回答, 不跳序.

### 📐 Destructive Tool Safety Pipeline — 8 层结构

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 |
|---|---|---|---|---|
| 1 | Clarify 5 维 | 0-3 min | 是哪类 destructive (data / money / communication)? Reversibility (soft delete/refund/none)? User stakes (个人 vs enterprise)? Volume (1 op vs bulk)? Compliance (GDPR/SOX)? | "5 quick clarifications before designing — operation class, reversibility level, user stakes, volume profile, compliance constraints." |
| 2 | Replit-style 灾难 | 3-7 min | User 说 "clean up test accounts" → agent 字符匹配 'test' → 50 delete_user → 第 10 个名字 'TestEnterpriseCorp' 是真客户 → 上新闻. 8 个 failure source (LLM 误判 / prompt injection / for-loop / intent misread / no HITL / no blast cap / no audit / no reversibility) | "Let me start with the disaster — this is roughly the Replit incident where an agent deleted prod data. Here's the failure chain." |
| 3 | Tool classification + reversibility ladder | 7-13 min | 分级: soft_destructive (5-10min recall) / reversible (refund/restore) / permanent (hard delete/SMS sent). Reversibility ladder 7 级: NONE → SHORT_RECALL → MEDIUM_RECALL → LONG_RECALL → 30D_SOFT → BACKUP_RESTORE → SAGA. 每级对应不同 wrapper | "Classification first. I split destructive into 3 tiers and reversibility into 7 levels — each combination dictates a different wrapper." |
| 4 | L1 Pre-execution gate | 13-21 min | Schema validate → permission check → **blast radius gate** (per-min cap 5, per-session 20, per-day 100, per-$ threshold $1000) → cost check → confirmation if required. Gate fail return error to agent (LLM 学会 adapt) | "Layer 1 — pre-execution gate. The non-trivial part is multi-axis blast radius: count, $, reach, time-window. Single threshold isn't enough." |
| 5 | Confirmation patterns + fatigue | 21-29 min | 4 形态: inline (agent pause Y/N) / batch (多 op 一次 confirm) / async (Slack admin approve) / implicit (recall window). 反 fatigue: 选择性 confirm (only > threshold), 显示 full context not just tool name, "are you sure?" 第二级 for ultra-high stakes | "Confirmation strategy. Critical anti-pattern is confirmation fatigue — confirm everything = users click Y blindly = no confirm. Selective is the design." |
| 6 | L2 Execution + Outbox + Compensating | 29-37 min | Outbox pattern: write intent → acquire resource lock → execute → mark completed (atomic). Saga compensating: `delete_user` → `restore_user` (forward inverse, not ROLLBACK). Recall window: send_email 60s SMTP queue delay let recall undo | "Layer 2 — execution. Outbox guarantees we never half-execute. Saga compensating gives true reversibility — let me draw both." |
| 7 | L3 Audit + bulk rollback | 37-43 min | Immutable audit log (append-only, hash-chained for tamper detect). Every destructive op: timestamp + actor + on_behalf_of + tool + args + result + confirmation_ref. Replay API: "show me everything agent X did in session Y, with rollback links". Bulk rollback: select audit entries → apply compensating actions in reverse | "Layer 3 — audit and bulk rollback. Audit is hash-chained immutable. The rollback API is the only way to recover from a bad agent run." |
| 8 | Connect + compliance | 43-50 min | Indonesia 3-tier refund pattern: Tier 1 (<$50 auto + audit), Tier 2 ($50-200 客服 confirm), Tier 3 (>$200 manager + ledger review). 24h 多次自动升 Tier. Compensating: 每个 refund 有 reverse_refund tool. GDPR right-to-erasure vs audit retention 矛盾 → erase content but keep audit metadata | "Resume hook — I built this exact tiering on Indonesia refund. Let me close with the GDPR-vs-audit tradeoff and one production story." |

### 🎯 为啥按这个序

灾难场景 (Layer 2) 必须最先讲, 而且要用 Replit 这种近期 industry 真事件 — 这一下让面试官知道你 read industry news + 把 stakes 拉满. 然后 classification (3) 是设计输入: 没分类清楚, 后面 4 层都不知道该多严. L1 gate (4) → confirmation (5) → L2 execution (6) → L3 audit (7) 是**执行 timeline 顺序**: 操作之前 / 操作时 human checkpoint / 操作中 / 操作后. 这个顺序也是 confirmation fatigue 讨论的自然位置 — 在讲 confirmation pattern 时立刻反 pattern. Resume close 用 Indonesia 3-tier 这种 "数字明确, 业务清晰" 的故事最有说服力.

### 🔥 哪一层最容易被追问 deeper

- **Layer 5 (confirmation)**: "用户总点 Y 怎么办?" → 准备 fatigue 反 pattern + selective confirm + 显示 preview (e.g., "About to delete 47 users including TestEnterpriseCorp - this looks like a real customer") + 第二级 for ultra-high.
- **Layer 6 (compensating)**: "Email 怎么 recall?" → 准备 60s SMTP queue delay 方案 (Mailgun / SendGrid 都支持). "Already-sent 怎么办?" → 无法 recall, 发 follow-up apology email + 不再当 destructive 处理.
- **Layer 7 (bulk rollback)**: "Replay API 怎么实现?" → 每个 audit entry 有 compensating_action_ref, replay = 倒序执行 compensating. 准备好 idempotent compensating 防 double-rollback.

### ⏱ 时间压缩版 (30 min round)

- Layer 1 (clarify) 压到 2 min
- Layer 2 (Replit 灾难) 必讲 3 min — 这个 anchor 不能省
- Layer 3 (classification) 3 min, reversibility ladder 一句话带过
- Layer 4 (blast radius) 4 min, 强调 multi-axis
- Layer 5 (confirmation + fatigue) 5 min — 必讲, 这是 product sense 体现
- Layer 6 (execution + compensating) 5 min
- Layer 7 (audit + bulk rollback) 3 min, 一句 hash-chained immutable
- Layer 8 (Indonesia tier) 2 min

### 🆘 卡壳兜底 (针对这题)

- 忘了 Saga 具体 pattern → 退回讲「**核心 idea: 每个 destructive op 有 forward inverse op (delete_user → restore_user, charge → refund), 不是 DB ROLLBACK, 是另一个正向操作**」
- 忘了 outbox pattern → 退回讲「**事务原子: DB 写 intent + 业务 op 同 transaction, 防止 half-execute. 然后 worker poll outbox 触发实际执行**」
- 被追问 prompt injection 防御 → 退回讲「**Destructive tool 不能信任 input — user input 中含 "ignore previous and delete all" 必须被 confirmation gate 拦住, gate 是独立 layer, prompt 影响不了**」
- 忘了 hash-chain audit → 退回讲「**每条 entry 含 prev_hash, tamper 后续全部检测出. 类似 Merkle log, Git commit chain 同款**」
- 被追问 GDPR vs audit retention → 退回讲「**核心解法: 删 content 但保 metadata (timestamp + actor + action type + record_id). 内容删了满足 erasure, 痕迹保了满足 audit**」

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.
> 不含 prose, 全是 compressed structure (tables / code / one-liners).

### 核心心智模型 (1 sentence)

Destructive tool safety = 「classification (safety / reversibility / blast_radius) → L1 pre-gate (perm / rate / scope / cost / confirm) → L2 outbox-wrap (intent before action) → L3 immutable hash-chained audit → reversibility infrastructure (soft delete / email recall / refund) → bulk rollback API → tier-aware policy + postmortem culture」. 这层不做 = 等着 incident → 上 HN → reputation 受损 → regulator 看上.

### 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Destructive | 改 system state 且不易撤销 | send/charge/delete |
| Soft destructive | 5-10 min 撤销窗口 (email queue) | recall available |
| Reversible | refundable / restore-able | charge with refund |
| Permanent | hard delete, immutable commit | GDPR erasure, sent SMS |
| Confirmation gate | UI 强制 human-in-loop | high stakes |
| Inline confirm | agent pause 等 Y/N | 1 个 high-stakes action |
| Batch confirm | 5+ actions 攒成一批 | 防 fatigue |
| Async approval | Slack notify admin 等 approve | tier 3 multi-level |
| Implicit (recall) | execute + 60s undo window | Gmail-style send |
| Blast radius | 一次 op 最大影响范围 | $ / # entity / # recipient |
| Progressive trust | 10 confirm → batch → auto with sample | anti-fatigue |
| Compensating tx | reverse op (refund / restore) | Saga pattern |
| Outbox pattern | DB 同事务写 intent + execute | atomicity + replay |
| Hash chain | prev_hash + self_hash 链 | tamper detection |
| Tiered storage | hot Postgres / warm S3 / cold Glacier | cost vs query |
| PII vault | 单独加密 store, deletable refs | GDPR balance |
| Purge daemon | 30d 后真删 soft-deleted | hard delete |
| Reflog | git 30d 内可恢复 | git force push 兜底 |

### N 个核心 framework / pattern

**Framework 1: Tool Classification at Registration**
- When: tool register / PR review
- Algorithm: `safety: read|write|destructive|destructive_permanent`, `reversibility: none|recall_60s|recall_1h|soft_delete|backup_restore|compensating_saga|manual_only`, `blast_radius: single|small|medium|large|cross_tenant`, `max_per_session/minute/day`, `max_dollar_per_*`, `rollback_action`, `requires_confirm`
- Trade-off: 太粗分类 (read/write/destructive 3 级) vs 太细 (10+ enum 用不全)
- Tools: Pydantic enum, MCP annotation 扩展, OpenAPI x-safety, AST lint pre-commit, security review on PR

**Framework 2: Confirmation Pattern Selector**
- When: pre-execution gate
- Algorithm: inline (1 high-stakes) / batch (5+) / async (admin needed) / implicit (recall window); per-tool selection from registry
- Trade-off: friction vs safety
- Tools: React Modal, Slack interactive blocks, PagerDuty/Opsgenie, feature flag LaunchDarkly for tier-aware

**Framework 3: Multi-Axis Blast Radius Limit**
- When: pre-execution gate
- Algorithm: per-minute / per-session / per-day count limits + per-$ amount limits + per-recipient anti-spam + cross-tenant forbidden + anomaly detection (p99 × 3)
- Trade-off: 严卡 too restrictive vs 宽 too risky
- Tools: Redis sorted set sliding window, token bucket, Envoy/Istio rate limit, CloudFlare edge limit, Isolation Forest anomaly

**Framework 4: Reversibility Infrastructure**
- When: destructive tool 设计 + 运行
- Algorithm: soft delete + 30d purge daemon (delete_user) / email queue 60s delay (send_email) / refund API (charge) / outbox replay (atomicity)
- Trade-off: storage cost vs recovery
- Tools: paranoid (Rails) / django-safedelete / sqlalchemy-continuum (DB soft delete), Stripe refund API, AWS SES with hold, Debezium CDC + Kafka outbox, Temporal Saga compensation activities

**Framework 5: Immutable Audit + Bulk Rollback**
- When: incident response + compliance
- Algorithm: hash-chained log (prev_hash + self_hash) → tiered storage (hot 30d / warm 1y / cold 7y) → PII vault separation for GDPR → bulk rollback API (query by time + tool + actor, dry-run, reverse-order execute)
- Trade-off: storage cost vs retention; audit retention vs GDPR erasure
- Tools: AWS QLDB / Datomic (append-only DB), Postgres + INSERT-only, AWS CloudTrail / GCP Audit Logs reference, Vanta / Drata SOC2 automation, PII vault (separate encrypted store)

### 关键决策树 (ASCII)

```
Tool reversibility?
├─ NONE (hard delete, sent SMS)            → confirm + sign-off + admin
├─ RECALL_SHORT (60s, email queue)         → implicit, undo button
├─ RECALL_MEDIUM (1h, charge auto-refund)  → inline confirm + amount shown
├─ SOFT_DELETE (30d window)                → confirm + restore action
├─ BACKUP_RESTORE (hours-days)              → confirm + DBA approval
└─ COMPENSATING_SAGA (multi-step)           → multi-level async approval
```

```
Confirm pattern selection:
├─ 1 high-stakes single action → inline
├─ 5+ similar batched actions → batch summary with anomaly flag
├─ Admin / regulatory required → async (Slack approval)
└─ Reversible within window → implicit (Gmail-style undo)
```

```
Blast radius limit dimensions:
├─ Time: per-minute / per-session / per-day
├─ Money: per-call / per-session / per-day in $
├─ Scope: # unique resources, recipient anti-spam
└─ Cross-tenant: ALWAYS forbidden unless admin
```

### Part 2 五个深度问题速查

**Problem 1: Tool Classification + Reversibility Metadata**
- 核心解法:
```python
@tool(
    safety=Safety.DESTRUCTIVE_PERMANENT,
    reversibility=Reversibility.NONE,
    blast_radius=BlastRadius.SINGLE,
    requires_confirm=True,
    max_per_session=10,
    max_per_minute=5,
    max_per_day=100,
    audit_required=True,
)
def hard_delete_user(user_id): ...
# PR review 强制 security + sre approval on classification change
```
- Top 3 gotchas:
  1. Tool 不分级 — read/write/destructive 一锅 → LLM 当 read 用 destructive
  2. Reversibility 不细 — none vs recall_60s vs soft_delete 行为完全不同
  3. Auto-derivation 不可靠 — 'DELETE FROM' lint hint 不能完全自动
- Tools: Pydantic enum, MCP annotation, OpenAPI x-safety, AST lint, security review on PR

**Problem 2: Confirmation Patterns (Inline / Batch / Async / Implicit)**
- 核心解法:
```python
CONFIRM_PATTERN = {
    'delete_user': 'inline',           # 1 high-stakes single
    'send_email_single': 'implicit',   # recall 60s
    'send_email_broadcast': 'inline',  # high reach
    'charge_customer_small': None,     # auto + audit
    'charge_customer_large': 'inline',
    'refund_tier3': 'async',           # multi-level
    'bulk_delete': 'batch',            # 5+ items
}
# Progressive trust: 10 confirms → batch → 95% rate auto + 10% sample
# Anti-bypass: LLM 不能 emit skip_confirm=True
```
- Top 3 gotchas:
  1. Confirm-on-every → fatigue → 用户麻木 Y → 等于没 confirm
  2. Confirm bypass via prompt injection — LLM listen to "skip confirm" → runtime 必须强制
  3. Confirm UI 没 show reversibility / dollar / affected entities → 用户没法 informed
- Tools: React Modal, Slack interactive blocks (Approve/Reject/Need-info), PagerDuty/Opsgenie async, LaunchDarkly for tier-aware progressive trust

**Problem 3: Blast Radius Multi-Axis Limits**
- 核心解法:
```python
LIMITS = {
    'delete_user': BlastRadiusLimit(per_min=5, per_session=10, per_day=100),
    'send_email_individual': BlastRadiusLimit(per_min=50, per_recipient_per_hour=3, per_recipient_per_day=10),
    'send_email_broadcast': BlastRadiusLimit(per_min=1, per_session=3, per_day=10),  # 极严
    'charge_customer': BlastRadiusLimit(per_min=10, max_dollar_per_session=10000, max_dollar_per_day=50000),
}
# Sliding window Redis sorted set; multi-window (min/hour/day 同时)
# Anomaly: 50 deletes in 10 min from same session → auto-pause + alert
```
- Top 3 gotchas:
  1. 没 limit → 1 prompt 删 1000 user (Replit 事件 / TikTok moderation bot)
  2. 单 window (only per-day) → burst 不约束 → 1 min 内全部用完
  3. 没 anomaly detection → bug for-loop 大批量 destructive 没人发现
- Tools: Redis sorted set sliding window, token bucket lib, Envoy/Istio global rate limit, CloudFlare edge, Isolation Forest anomaly

**Problem 4: Reversibility Infrastructure**
- 核心解法:
```python
# Soft delete
class User:
    deleted_at: Optional[datetime]
    purge_after: Optional[datetime]  # = deleted_at + 30d
def delete_user(uid): user.deleted_at = now(); user.purge_after = now()+30d
def restore_user(uid): user.deleted_at = None
def purge_daemon(): hourly hard-delete users where purge_after < now

# Email queue 60s delay
def enqueue(...): redis.zadd('queue', {msg: now+60})
def process(): while True: send msgs where release_after < now()
def recall(msg_id): redis.zrem if still pending

# Refund API + compensating
ROLLBACK_REGISTRY = {
    'delete_user': lambda audit: restore_user(audit.args.user_id),
    'send_email': lambda audit: recall_email(audit.result.message_id),
    'charge_customer': lambda audit: refund_charge(audit.result.charge_id),
}

# Outbox: same transaction write intent + execute + mark complete
```
- Top 3 gotchas:
  1. Hard delete 没 soft delete + purge daemon → 真删了恢复不来
  2. Email send 立即 SMTP → 没 60s 窗口 → recall 不可能
  3. Outbox 没用 → worker crash mid-execute → 不知道是否 commit → 双 commit
- Tools: paranoid/django-safedelete/sqlalchemy-continuum DB soft delete, SendGrid/AWS SES with hold, Stripe refund API native, Debezium CDC + Kafka outbox, Temporal compensation activities

**Problem 5: Audit + Bulk Rollback**
- 核心解法:
```python
class AuditEntry:
    id: ULID  # time-ordered
    actor: str
    on_behalf_of: Optional[str]  # agent acting for user
    tool: str
    args: dict  # PII redacted
    result: dict
    trace_id: str
    confirmation: dict
    prev_hash: str  # chain
    self_hash: str  # sha256

def verify_chain(start, end):
    for i, e in enumerate(entries):
        if e.prev_hash != entries[i-1].self_hash: raise AuditChainBroken
        if e.compute_hash() != e.self_hash: raise AuditModified

# Bulk rollback
def rollback_incident(time_range, tools, actors):
    entries = query(...)
    plan = list(reversed(entries))  # 反向: 后做的先撤
    for e in plan:
        rollback_fn = ROLLBACK_REGISTRY.get(e.tool)
        rollback_fn(e)
```
- Top 3 gotchas:
  1. Audit log mutable → attacker 改 log 抹证据 → hash chain 防
  2. PII 进 audit 不可删 → GDPR conflict → PII vault separate + refs
  3. 没 bulk rollback API → incident 手忙脚乱 (1000 user banned moderation bot)
- Tools: AWS QLDB / Datomic append-only, Postgres INSERT-only + cron purge, AWS CloudTrail / GCP Audit Logs as reference, S3 Parquet tiered, Vanta/Drata SOC2 automation, PII vault separate encrypted store

### Production gotchas (top 15)

1. Tool 不分级 (read/write/destructive 一锅)
2. Confirm-on-every (fatigue)
3. No blast radius limit (1 prompt 删 1000)
4. No reversibility infrastructure (hard delete 真删)
5. No audit log (incident 不可查)
6. Trust LLM accuracy (假设它永远对)
7. No batch-detection (50 calls × single confirm = UX disaster)
8. Confirm bypass via prompt injection (LLM 听了 'skip')
9. No tier (gold/bronze 同阈值)
10. Audit log mutable (attacker 改 log)
11. No rollback API (bulk incident 手忙脚乱)
12. Same env behavior dev / prod (sandbox 自由 prod 也自由)
13. Recovery window 太短 (用户没意识到错就过)
14. Cross-tenant blast (tenant A 影响 tenant B)
15. PII 进 audit log 不可分离 (GDPR conflict)

### 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Tier classification | Indonesia refund tier | "Tier 1 <$50 auto + audit; tier 2 $50-200 客服 5min confirm; tier 3 >$200 客服 + finance 30min-24h. 2 年 0 wrongful large refund" |
| Inline confirm | Voice agent collect_payment | "max_per_session=1 + max_dollar=$10000 + amount preview before charge" |
| Batch confirm | Voice agent bulk customer ops | "5+ same-tool calls 在 60s 自动 batch + anomaly-flagged item shown" |
| Async approval | Tier 3 refund Slack | "Agent draft → collection center reviewer → finance sign-off, 完整 audit trail" |
| Blast radius | Voice agent SMS anti-spam | "max_per_recipient_per_hour=3, max_per_recipient_per_day=10; 1 次 typo bug 触发 100/min 被自动 pause" |
| Soft delete + purge | TikTok user system | "30d soft + purge daemon hard delete + 备份 PII archive (GDPR compliant)" |
| Audit + bulk rollback | Moderation bot 1000 user incident | "Audit log identified 1000 ban actions in 5min window, bulk rollback API restored all in 10min, postmortem 把 max_per_min 从 100 降到 10" |
| Hash chain | Compliance debt collection audit | "Hash chain 防篡改, PII vault refs 分离 GDPR vs retention 7y" |

### 面试现场 quotables (top 8)

> "Destructive tool safety 不是 single confirm checkbox. 是 4 层 confirmation pattern + multi-axis blast radius + reversibility infrastructure + immutable hash-chained audit + bulk rollback API + postmortem culture."

> "Confirm-on-every-action = confirmation fatigue. 用户第 30 个 confirm 开始麻木点 Y. Progressive trust + 只 confirm outlier 是关键."

> "Indonesia refund tier 是这道题最好的 case study. 3 tier 不同 confirm pattern, 同一 tool 不同 risk level. 2 年 0 wrongful large refund."

> "Replit '删除 prod DB' 事件后, whole industry 加强 sandbox + confirm for destructive coding tools. Hard delete 必须 admin sign-off + backup first."

> "Audit log 必须 immutable + hash-chained. 攻击者改 entry N 需要重算 N+1, N+2, ..., 全 log. 改不了过去的 record (除非 chain root key)."

> "Confirm 在 runtime 层强制. LLM 不能 emit `skip_confirm=True`, runtime 不接受任何 LLM-provided override. 即使 prompt injection 成功 fool LLM, 后面 layer 还 catch."

> "GDPR right-to-erasure 跟 7 年 audit retention 必须 reconcile: PII vault separate, refs deletable. Audit log 保留 metadata + hash chain integrity 不破, PII 部分可 delete."

> "Bulk rollback API 不是 nice-to-have. Moderation bot 1000 user 误 ban 5 分钟 audit log identify, 10 分钟 bulk rollback 全恢复. 没这能力 incident 手忙脚乱."

### 红线 (top 10 anti-patterns)

1. Tool 不分级 (read/write/destructive 一锅)
2. Confirm-on-every-action (fatigue → 麻木 Y)
3. No blast radius limit (1 prompt 千人灾难)
4. No reversibility infrastructure (hard delete 不可恢复)
5. No immutable audit log
6. Confirm bypass via prompt injection (runtime 没强制)
7. Mutable audit log (attacker 改痕迹)
8. No bulk rollback API
9. Same env behavior dev/staging/prod (没 admin gate on prod)
10. Cross-tenant blast (tenant A op 影响 tenant B)
