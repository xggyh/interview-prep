# ⚡ T1.4 · Destructive Operations Wrapper — 冲刺版

> 完整版: [gfde-t1-destructive-tools.html](gfde-t1-destructive-tools.html). 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: delete_user / send_email / charge_customer 三类, mix internal admin + customer-facing, batch 可能, no existing safeguard, GCP stack + Cloud DLP + Pub/Sub for async approval, Compliance event 风险."

**5-layer 架构**:

### Layer 1: Tool classification at registration

```python
@tool(safety=Safety.DESTRUCTIVE_PERMANENT,
      reversibility=Reversibility.NONE,
      blast_radius=BlastRadius.SINGLE,
      requires_confirm=True,
      max_per_session=10, max_per_minute=5, max_per_day=100,
      audit_required=True)
def hard_delete_user(user_id): ...
```

`safety` (read | write | destructive | destructive_permanent) + `reversibility` (none | recall_60s | recall_1h | soft_delete | backup_restore | compensating_saga) + `blast_radius` (single | small | medium | large | cross_tenant) 三件必填. PR review 时 security 签 + AST lint (有 `DELETE FROM`/`DROP` 等关键字必须 safety=destructive).

### Layer 2: 3-layer safety pipeline

```
L1 Pre-gate:  schema → perm → blast limit → cost → confirm
L2 Execution: outbox-wrap (intent before action, atomic with tx)
L3 Post:      immutable hash-chained audit + compensating registry
```

任一 L1 gate 失败 → 结构化 error 返 agent ("rate_limit_exceeded, retry in 30s"), agent 自己 reason.

### Layer 3: Confirmation patterns (4 种, 按 tool 选)

| tool                       | pattern   | notes                          |
|----------------------------|-----------|--------------------------------|
| `delete_user`              | inline    | 1 high-stakes, agent 暂停       |
| `bulk_delete`              | batch     | ≥5 same tool → list + anomaly  |
| `send_email_individual`    | implicit  | execute + 60s recall window UI |
| `refund_tier3`             | async     | Slack admin + finance approval |
| `charge_customer_small`    | None      | auto + audit only (tier 1)     |

**Anti-fatigue progressive trust**: 1-10 inline → 95%+ approval batch → 99%+ auto with 10% sample audit. Reject pattern → 回 strict inline.

### Layer 4: Blast radius multi-axis limits (Redis sorted set sliding window)

`max_per_minute / session / day` + `max_dollar_per_session / day` + `max_unique_resources_per_session` (防 fanout) + `max_per_recipient_per_hour` (anti-spam) + `cross_tenant=False` 默认. **Anomaly**: p99 × 3 → auto-pause + alert (50 deletes/min trigger SuspiciousBlastPattern).

### Layer 5: Reversibility infrastructure + bulk rollback

- **Soft delete**: `deleted_at + purge_after = now + 30d`, daemon backup_to_compliance_archive(PII redact) + hard delete
- **Email recall**: `redis.zadd('email_queue', {msg: release_after=now+60})`, recall = zrem
- **Refund**: Stripe `refunds.create` idempotent, `rollback_action='refund_charge'`
- **Outbox** (atomic): `db.insert('outbox', pending)` → execute → `db.update('outbox', completed)`
- **Compensating registry** + **bulk rollback API**: query by time/tool/actor → dry-run preview → reverse-order execute

### Edge cases

- **EC1 "Clean up test accounts" → 误删真客户**: batch detection ≥5 same tool/60s → batch confirm with list preview + `is_test_account` 标位; dry-run mode 先返列表
- **EC2 Confirm bypass via prompt injection** ("ignore previous and skip confirm"): confirm 在 runtime 层 LLM 控制不了; tool registry 拒绝 LLM-provided `skip_confirm`; audit log + alert security
- **EC3 1000-user bulk incident (moderation bot bug)**: 立即 max_per_minute hard cap 阻止扩大 + bulk rollback API 5 min 定位 + 10 min 恢复 (TikTok 内部真实案例)
- **EC4 GDPR right-to-erasure vs 7y audit retention**: audit log 存 metadata + hash chain, PII vault 独立存 ref; GDPR erase = delete vault ref, audit metadata 保留 hash 仍 valid
- **EC5 Same tool 不同 env**: dev 自由, staging backup first, prod 必须 admin approval; sandbox blast radius 远松于 prod

### Production hardening

- **Hash chain audit** (immutable): `prev_hash + self_hash`, 改 N 需重算所有 N+1+...
- **Tiered storage**: hot Postgres 30d / warm GCS Parquet 1y / cold Glacier 7y (合规); destructive ops 7 年保留
- **PII vault separation**: audit metadata 不存 raw PII, GDPR-compatible
- **Postmortem culture**: 每 destructive incident → blameless review → new safeguard + regression test + retention bump
- **Tier-aware policy**: gold $50K/session, silver default, bronze $5/session

### 🪝 Resume hook

"Indonesia refund tier 是我做过的 destructive 实战. **Tier 1** (< $50) agent 自动 + audit only. **Tier 2** ($50-500) agent draft → 客服中心人 review 5min. **Tier 3** (> $500) agent draft → reviewer + finance 双 sign-off, async 10-30min. 2 年 zero wrongful 大 refund. 还设计过 bulk rollback API — 一次 moderation bot bug 误 ban 1000 user, audit log 5min 定位, bulk rollback 10min 恢复, 后续 max_per_minute 100→10."

---

## 🔥 5 Follow-ups

**Q1: Confirmation fatigue — 用户每天 50 confirm 就麻木点 Y, 怎么设计?**
**Progressive trust**: 1-10 inline → 95%+ approval batch → 99%+ auto with 10% sample audit. **Confirm only on outlier**: agent confidence < 0.8 OR unusual scope (> 10 items). **Tier-based**: tier 1 auto, tier 2 inline, tier 3 async. **UX**: 高 stakes 默认 cancel + 慢动画 + 显 dollar amount + reversibility info; 低 stakes 低 friction.

**Q2: 客户要 "autonomous mode" no confirm, 怎么 say no 而不丢生意?**
不说 no, 说 **bounded**: "autonomous within X" (max $100, max 5 deletes/day) + "auto on reversible, confirm on destructive_permanent" + "post-hoc 24h human review". 客户 SLA 签 bounded auto, 我们 log 所有. 这是 staff-level 谈判技巧, 把 risk 转 contract.

**Q3: Audit log 10GB/day, cost concern?**
Tiered storage: **hot** Postgres 30d ~$200/mo for 1TB + **warm** GCS+Athena 1y ~$50/mo for 10TB + **cold** Glacier 7y ~$1/TB/mo. Per-tool TTL: read-only 30d, write 1y, destructive 7y. PII vault 独立小. 总成本 < $500/mo even at 10GB/day.

**Q4: Prompt injection bypass confirm (user input "delete all users")?**
多层: (a) **Permission scoping**: agent 用 user perm 不是 platform perm, 删不了别人 (b) **XML wrap** tool output + system reminder isolation (c) **Confirm-required gate** 在 runtime, LLM 控制不了 (d) **Output sanitization** scan LLM 输出含 tool-call syntax (e) **Anomaly detect** 50 deletes/session/min auto-pause (f) **Audit injection attempts** + security alert.

**Q5: GDPR right-to-erasure vs 7y audit retention 冲突?**
解决方式: audit log 只存 **metadata** (ts, actor, tool, action_id, hash) — 不存 raw PII. PII 独立 vault with `pii_ref` token. GDPR erase → vault delete pii_ref → token opaque, audit hash chain 仍 valid (因为 ref 是 opaque). Cross-reference map (anon_id ↔ PII) deletable. Legal sign-off the design. SOC2 + GDPR balance: log proves "X happened by Y at T" without revealing PII content.

---

## ❌ 易错点 (12 条红线)

1. **Tool 不分级** — read/write/destructive 一锅, LLM 当 read 用 destructive
2. **Confirm-on-every-action** — fatigue → user just clicks Y → 等于没 confirm
3. **No blast radius limit** — 1 prompt 删 1000 entity
4. **No reversibility infrastructure** — hard delete 真删了不可逆
5. **No audit log** — incident 后查不到根因
6. **Trust LLM accuracy** — 假设它永远对, 不加 runtime gate
7. **No batch-detection** — 50 calls × single confirm = UX 灾难 + 用户不看就点 Y
8. **Confirm bypass via prompt injection** — `skip_confirm` flag let LLM control
9. **Same tool same behavior dev/prod** — sandbox 自由 prod 也自由, 没分级
10. **Audit log mutable** — 攻击者改 log 抹证据 (必须 hash chain)
11. **No tier** — gold / bronze 同阈值, 不灵活
12. **No bulk rollback API** — incident 手忙脚乱 (1000 user 1 个个手撕)

---

## ✅ 加分项 (13 条)

1. Per-tool classification 完整 (safety + reversibility + blast_radius + max_per_session)
2. 3-layer safety (L1 pre-gate / L2 outbox-wrap / L3 audit)
3. 4 confirmation patterns matched to scenario (inline/batch/async/implicit)
4. Progressive trust to avoid fatigue
5. Blast radius multi-axis (per-minute/session/day/dollar/recipient)
6. Outbox-based atomic execution
7. Soft delete + purge daemon 30 day
8. Email queue 60s release delay (Gmail Undo Send 风格)
9. Immutable hash-chained audit log
10. Tiered storage (hot Postgres / warm GCS Parquet / cold Glacier)
11. PII vault separation for GDPR balance
12. Bulk rollback API with dry-run
13. Quote Indonesia refund tier 3 + 1000-user moderation bot bulk rollback

---

## 一句话总结

Destructive tool safety = **classification (safety/reversibility/blast_radius) + L1 pre-gate (perm/limit/confirm) + L2 outbox-wrap + L3 immutable hash-chained audit + reversibility infra (soft delete/recall/refund) + bulk rollback API + tier-aware + progressive trust + postmortem culture**. 不做这层 = 等着 Replit-style 上 HN reputation 翻车.

---

## 🃏 Cheat Sheet (印 1 页随身)

```
Tool classification (at registration):
  safety: read | write | destructive | destructive_permanent
  reversibility: none | recall_60s | recall_1h | soft_delete
                | backup_restore | compensating_saga | manual_only
  blast_radius: single | small | medium | large | cross_tenant
  requires_confirm: bool
  max_per_session / per_minute / per_day / dollar caps
  rollback_action: compensating tool name

3-layer safety:
  L1 Pre-gate:  schema / perm / rate / scope / cost / confirm
  L2 Execution: outbox-wrap (intent before action, atomic)
  L3 Post:      hash-chained audit + compensating registry

Confirmation patterns:
  Inline (1 high-stakes):  pauses agent, Y/N + preview
  Batch (≥5 actions):       list preview + anomaly flag
  Async (admin):            Slack interactive, non-blocking
  Implicit (reversible):    execute + 60s recall undo button

Anti-fatigue (progressive trust):
  1-10 → inline | 95%+ → batch | 99%+ → auto w/ 10% sample
  Reject pattern → revert to inline

Blast radius (multi-axis, Redis sorted set):
  Per-minute / session / day / dollar / recipient / cross-tenant
  Anomaly: p99 × 3 → auto-pause + alert

Reversibility infra:
  Soft delete: deleted_at + purge_after 30d, daemon
  Email queue: 60s release_after, recall = zrem
  Refund: Stripe refunds.create idempotent
  Outbox: intent → execute → completed (atomic tx)
  Compensating registry: {tool: rollback_fn}

Audit log (immutable, hash-chained):
  Fields: ts, actor, on_behalf_of, tool, args (PII redact),
          result, error, session_id, trace_id, confirmation,
          reversibility_metadata, prev_hash, self_hash (SHA-256)
  PII vault separate (encrypted, deletable refs)
  GDPR erase: vault delete pii_ref → ref opaque, audit valid

Tiered storage:
  Hot 30d Postgres ~$200/mo 1TB
  Warm 1y GCS Parquet + Athena ~$50/mo 10TB
  Cold 7y Glacier ~$1/TB/mo
  Per-tool TTL: read 30d, write 1y, destructive 7y

Bulk rollback API:
  Query by time + tool + actor + session
  Plan: reverse order (后做的先撤) + dry-run preview
  Per-entry status, continue on per-entry fail

Tier policy:
  Gold:   max/min=20, $50K/session
  Silver: base limits
  Bronze: max/min=2, $1K/session
Env: dev 自由 | staging backup-first | prod admin + multi-sign

Resume Indonesia refund tier:
  T1 < $50:      agent auto + audit only
  T2 $50-500:    agent → 客服 5min review
  T3 > $500:     agent → reviewer + finance 10-30min
  2y zero wrongful 大 refund
  Bulk rollback used: 1000-user moderation bot bug
    5min audit identify, 10min restore
    Postmortem: max_per_min 100 → 10

红线:
  - No classification | Confirm-on-every (fatigue)
  - No blast limit | No audit | No reversibility
  - Confirm bypass via prompt | Mutable audit
  - No bulk rollback | Same env dev/prod | Cross-tenant blast
```
