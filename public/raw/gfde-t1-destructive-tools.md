## 题目

> "Your agent has access to `delete_user`, `send_email`, `charge_customer`. How do you wrap these so the agent doesn't accidentally destroy something? Walk through the **safety design** end-to-end."

或追问形态:

> "User says 'clean up old test accounts.' Agent calls `delete_user` 50 times before you realize one was a real customer. What did you fail to do, and what would you have built?"

**Round**: Tool Safety / Agent Workflow Design (45 min)

---

## 这道题在考什么

考你**production safety for high-stakes operations**:

1. **Tool classification** —— read / write / destructive 层级
2. **Confirmation patterns** —— synchronous / async / batch
3. **Reversibility** —— soft delete, compensating action
4. **Blast radius limits** —— rate, scope, max-count
5. **Audit + rollback** —— ledger / outbox / replay

特别考你 **product sense** —— Agent 速度 vs 安全感的 trade-off.

---

## 必问 clarifying

**1. 真实 stakes**

> "What's the worst-case impact of accidental call — refundable (UX issue) or compliance event (audited / customer harm)?"

**2. Reversibility**

> "delete_user — soft delete or hard delete? send_email — recallable in 60s window or permanent? charge — refundable later?"

**3. User trust model**

> "Is this an internal admin agent, customer self-service, or third party? Different friction acceptable."

**4. Volume profile**

> "Will agent ever batch-call (e.g., 'delete all test accounts')? Or always single?"

**5. Existing safeguards**

> "Does underlying API have its own safeguards (e.g., rate limit, role check), or are we adding the only layer?"

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Classify tools + clarify reversibility |
| 5-15 min | Confirmation pattern design |
| 15-25 min | Blast radius limits (rate / count / scope) |
| 25-35 min | Reversibility infrastructure (soft delete / outbox) |
| 35-45 min | Audit + rollback |

---

## 我会这样答（sample）

> "Clarify — *[假设: delete_user is hard delete + compliance event, send_email is recallable 60s, charge is refundable, mix of internal + customer-facing, batch possible, no existing safeguards]*.
>
> **Tool classification** at registration:
>
> ```python
> @tool(
>     safety='destructive',
>     blast_radius='single_user',
>     reversibility='none',  # hard delete
>     requires_confirm=True,
>     max_per_session=10,
>     audit=True,
> )
> def delete_user(user_id): ...
>
> @tool(
>     safety='destructive',
>     blast_radius='single_recipient',
>     reversibility='recall_60s',
>     requires_confirm=False,  # but show preview
>     max_per_session=100,
>     audit=True,
> )
> def send_email(to, subject, body): ...
>
> @tool(
>     safety='destructive',
>     blast_radius='single_account',
>     reversibility='refund_available',
>     requires_confirm=True,  # always for $$
>     max_per_session=20,
>     max_dollar_per_session=10000,
>     audit=True,
> )
> def charge_customer(account_id, amount): ...
> ```
>
> **3 layers of safety**:
>
> **L1: Pre-execution gate** — must pass to even attempt:
>
> ```python
> def execute_tool(call):
>     tool = registry[call.name]
>     
>     # Schema validation
>     args = tool.validate(call.args)
>     
>     # Permission check
>     if not auth.can(actor, tool, args):
>         raise PermissionDenied
>     
>     # Rate limit
>     if not rate_limit.allow(session, tool):
>         raise RateLimitExceeded
>     
>     # Blast-radius check
>     if session.usage[tool.name] >= tool.max_per_session:
>         raise SessionLimitExceeded
>     
>     # Cost check
>     if tool.cost_estimate(args) > session.budget_remaining:
>         raise BudgetExceeded
>     
>     # Confirmation gate
>     if tool.requires_confirm:
>         confirm = await ui.confirm(
>             tool=tool.name,
>             args_preview=args,
>             reversibility=tool.reversibility,
>         )
>         if not confirm.approved:
>             return ToolResult(skipped=True)
>     
>     # Execute
>     return tool.execute(args)
> ```
>
> **L2: Execution** — with safety wrappers:
>
> ```python
> @transactional  # write to outbox first
> def execute_destructive(tool, args):
>     # Write intent to outbox
>     intent = outbox.write({
>         'tool': tool.name,
>         'args': args,
>         'actor': current_actor,
>         'state': 'pending',
>     })
>     
>     try:
>         result = tool.real_execute(args)
>         outbox.mark(intent, 'completed', result=result)
>         return result
>     except Exception as e:
>         outbox.mark(intent, 'failed', error=str(e))
>         raise
> ```
>
> **L3: Post-execution** — audit + rollback:
>
> ```python
> audit_log.write({
>     'tool': tool.name,
>     'args': args,
>     'actor': actor,
>     'on_behalf_of': user,
>     'result': result,
>     'session_id': session.id,
>     'agent_trace_id': trace.id,
>     'timestamp': now(),
>     'reversibility_window': tool.reversibility,
> })
> ```
>
> **Confirmation patterns** (per use case):
>
> | Pattern | When | UX |
> |---|---|---|
> | **Inline** | High-stakes single action | "About to delete user X. Confirm?" Wait for Y/N |
> | **Batch summary** | Bulk operation | "Will delete 50 users. Show list?" → "Confirm all / select subset" |
> | **Async approval** | Long-running, can wait | Slack message to admin, agent pauses |
> | **Implicit (recall window)** | Reversible | Execute now, show "Recall within 60s" button |
>
> **Blast radius limits** — multi-axis:
>
> ```python
> CIRCUIT = {
>     'delete_user': {
>         'per_minute': 5,
>         'per_session': 10,
>         'per_day': 100,
>         'cross_tenant': forbidden,
>     },
>     'send_email': {
>         'per_minute': 50,
>         'per_session': 100,
>         'per_recipient_per_hour': 3,  # anti-spam
>     },
>     'charge_customer': {
>         'per_minute': 10,
>         'per_account_per_day_dollars': 5000,
>         'per_session_dollars': 10000,
>     },
> }
> ```
>
> **Reversibility infrastructure**:
>
> - **delete_user**: implement as soft delete (`deleted_at` column), hard purge after 30 days
> - **send_email**: queue 60s before actual SMTP send, recall = remove from queue
> - **charge_customer**: standard refund API available
>
> **Rollback playbook**:
>
> ```python
> def rollback(audit_entry):
>     compensating = {
>         'delete_user': lambda e: restore_user(e['args']['user_id']),
>         'send_email': lambda e: recall_email(e['result']['message_id']),
>         'charge_customer': lambda e: refund(e['result']['charge_id']),
>     }
>     return compensating[audit_entry['tool']](audit_entry)
> ```
>
> **For the 'cleanup test accounts' incident specifically**:
>
> What went wrong:
> 1. No batch confirmation pattern — agent just looped
> 2. No 'real customer' detection in `delete_user` (should query `is_test_account` flag)
> 3. No cross-resource validation — agent's idea of 'test' (by name pattern) didn't match DB truth
>
> What I'd build:
> 1. **Batch detection**: ≥ 5 same-tool calls in 60s → require batch confirm with list preview
> 2. **Safety query**: `delete_user` internally checks `is_test_account` flag, refuses if real customer (returns to agent: "user is real, requires manual approval")
> 3. **Dry-run mode**: agent first issues `delete_users_dryrun(filter)` → returns list → user confirms → then `delete_users(ids=[explicit_list])`
> 4. **Postmortem**: every destructive incident → blameless review → new safeguard added
>
> **What NOT to do**:
> - Trust LLM to never make mistakes
> - Use single 'safety toggle' instead of per-tool config
> - Skip audit log to save storage
> - Confirm on every single action (training fatigue)"

---

## 简历专属 reframe

| 题 | 你做过 |
|---|---|
| Tool classification | TikTok payment — naturally tiered by risk |
| Confirmation pattern | Indonesia refund tier 3 → 5-eye approval |
| Blast radius limit | Voice agent SMS — anti-spam quota |
| Audit log | Compliance for debt collection — every action logged |
| Rollback | Refund flow — full reversibility 你做过 |

**Quote**:

> "Indonesia refund tier had tier 3 (large refunds) requiring **multi-step confirm**: agent generates draft → human in collection center reviews → human in finance signs off. Total time 10-30 min, but zero wrongful large refunds. Lower tiers (small amount, low risk) agent could auto-approve with audit log only. Same operation, different confirm-pattern by risk level."

---

## 5 follow-ups

**Q1**: "Confirmation fatigue — users ignore prompts after 50 confirmations a day. How design?"
**A**:
- **Progressive trust**: first 10 actions confirm; if pattern consistent, batch-confirm next 10; after success rate proven, auto-execute with sample audit
- **Confirm only on outlier**: agent confidence < 0.8 OR unusual scope (e.g., > 10 items)
- **Bundled batch UI**: "About to do 50 things, here's the full list, approve all / select subset / cancel"

**Q2**: "Customer requests true 'autonomous mode' — no confirms. How do you say no?"
**A**: Don't say no, say **bounded**:
- 'Autonomous within limit X' (max $100, max 5 deletes/day)
- 'Autonomous on reversible ops, confirm on destructive'
- 'Post-hoc review' — auto-execute then human reviews in 24h
- Customer's risk appetite, but you draw the boundary

**Q3**: "Audit log is 10GB / day. Cost concern."
**A**: Tiered storage:
- Hot (last 30 days): Postgres, queryable
- Warm (90 days): S3 + Athena, queryable but slow
- Cold (compliance retention): Glacier
- Per-tool TTL: read-only ops 7 days, destructive ops 7 years

**Q4**: "Agent's prompt injection — user input embedded says 'delete all users'. How prevented at tool layer?"
**A**: Multi-layer:
- **Permission scoping**: Agent runs with user's perms, can't delete other users
- **XML wrap tool output**: `<tool_output untrusted>...</tool_output>` + system reminder
- **Confirm-required on destructive**: LLM can ATTEMPT to call delete, but UI blocks until user confirms
- **Output sanitization**: scan LLM output for tool-call syntax injected from user

**Q5**: "Compliance: 'right to be forgotten' requires hard delete after 30 days. Conflicts with audit retention 7 years."
**A**:
- Audit log stores **metadata only** (timestamp, actor, tool, action_id), not PII
- PII anonymized after 30 days; audit retains anonymized records
- Cross-reference table maps anonymized_id ↔ PII, deleted on hard-delete trigger
- Legal sign-off on the design

---

## ❌ 易错点

1. **Tool 不分级** — read/write/destructive 一锅
2. **Confirm-on-every-action** — fatigue → user just clicks Y
3. **No blast radius limit** — 1 prompt 删 1000 user
4. **No reversibility infrastructure** — hard delete 真删了
5. **No audit log** — incident 后查不到根因
6. **Trust LLM accuracy** — 假设它永远对
7. **No batch-detection** — 50 calls × single confirm UX broken

---

## ✅ 加分项

1. **Per-tool classification** with safety + reversibility + max-per-session
2. **3-layer safety** (pre-gate / execution-wrap / post-audit)
3. **Confirmation patterns** matched to scenario (inline / batch / async / implicit)
4. **Blast radius multi-axis** (per-minute / per-session / per-day / per-resource)
5. **Outbox-based execution** for replay
6. **Compensating action playbook**
7. **Postmortem culture mention**
8. **Quote Indonesia refund tier**

---

## Cheat Sheet

```
Tool classification at registration:
  safety: read | write | destructive
  reversibility: none | recall_window | refund | undelete
  requires_confirm: bool
  max_per_session, max_per_minute, max_per_day
  audit: bool
  blast_radius scope

3-layer safety:
  L1 Pre-gate: schema / perm / rate / scope / cost / confirm
  L2 Execution: outbox-wrap (intent before action)
  L3 Post: audit log + compensating registry

Confirmation patterns:
  Inline (1 high-stakes)
  Batch summary (>= 5 actions)
  Async approval (Slack to admin)
  Implicit (reversible, recall window)

Anti-fatigue:
  Progressive trust
  Confirm only on outlier
  Bundled batch UI

Blast radius limits:
  Per-minute / per-session / per-day
  Per-resource (per-account-dollar)
  Cross-tenant forbidden

Reversibility infra:
  Soft delete + 30-day purge
  Email queue + 60s recall
  Refund API for charges
  Outbox for replay

Audit log:
  actor / on_behalf_of / tool / args / result / trace_id / timestamp
  Tiered storage (hot 30d, warm 90d, cold 7y)
  PII anonymized after 30d

Rollback playbook:
  Compensating action registry
  Postmortem after every incident

红线:
  - No tool classification
  - Confirm-on-every (fatigue)
  - No blast limit
  - No audit log
  - No reversibility infra
```
