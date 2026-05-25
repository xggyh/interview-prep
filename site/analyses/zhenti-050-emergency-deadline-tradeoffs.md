## Q50 · Emergency deadline — what do you compromise on?

> "Customer escalation. **Major customer says they need feature X live by Friday or they cancel** (it's Tuesday). You estimated 2 weeks. Walk me through what you compromise on — and crucially, what you **NEVER** compromise on. Show me you've actually shipped under pressure."

**Round**: Production / Reliability (45 min)
**出处**: Exponent 2026 FDE Guide · 公司: OpenAI / Anthropic / Cohere / Scale AI — judgment under pressure 必问

---

## 📖 术语速查 (本题用到的)

> Deadline 题. 涉及 scope / 工程方法论 / 通讯 / tech debt 术语.

### Scope / Phasing ⭐

| 术语 | 解释 |
|---|---|
| **MVP (Minimum Viable Product)** ⭐ | **最小可行版**. 70% 用例 + zero polish. 不是 cut corner 是 cut scope. |
| **Walking skeleton** ⭐ | **每组件 stub / mock 但端到端跑通**. 跑稳后再换真组件. 不同于 MVP. |
| **Slice / Vertical slice** | 一个功能完整的薄片. 比 horizontal feature 更可 ship. |
| **Happy path** | 最常见的成功路径. Emergency 时只保 happy path. |
| **Edge case** | 不常见但合法的情况. Emergency 时 defer. |
| **Phased rollout** | 分阶段交付 — Tier 1 周五, Tier 2 下周. |
| **Tier 1/2/3** | 按风险 / 复杂度分层 — 简单先 ship, 复杂的延后. |
| **Reverse scope** | 客户 ask X, 你说 "X 太大, 给你 X' 小版本". |
| **Scope creep** | 项目过程中不断加需求. Deadline 下死敌. |
| **Anchored ask** | 客户随便说的 deadline 没想清楚 — push back 通常有 flex. |

### 工程妥协 / Trade-off ⭐

| 术语 | 解释 |
|---|---|
| **Tech debt / 技术债** ⭐ | **赶工时省的 quality work**. 不是 bad code, 是 "我们没时间做 right". 必须 track + 还. |
| **Debt log / Debt register** | 列出所有 shortcut 的清单, 含 owner + payback date. |
| **Manual override** | 自动化没跑通时, 人工干预 workflow. 短期 OK. |
| **Hardcode** | 写死值不参数化. 短期 OK 长期问题. |
| **Hack / Quick fix** | 不优雅但能跑的方案. |
| **Workaround** | 绕过问题不修根因. |
| **Polish** | UI / UX / 边缘 case 抛光. Emergency 时第一个 cut. |
| **Code freeze** | 暂停 feature ship, 只修 bug. |

### 永不妥协 ⭐

| 术语 | 解释 |
|---|---|
| **Reversibility** ⭐ | **必须能 rollback**. Migration 必须 reversible, 否则 ship 错没法救. |
| **Data integrity** ⭐ | 不能丢 / 损坏数据. Emergency 也不能省. |
| **Idempotency** | 同 request 多次执行结果一致. Retry 安全必备. |
| **Observability** ⭐ | **能 debug**. 没 log 没 metric 出问题瞎. |
| **Security / Auth** | 认证授权. Emergency 时也不能跳. |
| **Compliance** | HIPAA / SOX / GDPR. 监管要求 hard requirement. |
| **Backward compatibility** | 旧 client 还能跑. API breaking 时小心. |
| **Migration safety** | DB schema 改要 backfill + dual write + cutover, 不能直接砍. |

### Deploy / Rollout ⭐

| 术语 | 解释 |
|---|---|
| **Canary rollout** ⭐ | 1% → 5% → 25% → 100%. 出 SLO breach 自动 rollback. |
| **Shadow mode** | 新代码跟旧并跑, 新只记录不生效. 零风险收数据. |
| **Feature flag** ⭐ | **不重新部署就能开关功能**. LaunchDarkly / Statsig 用. Emergency 时尤关键. |
| **Blue-green deployment** | 两套环境切换 — blue 跑, green 待命; ship 时切到 green. 0 downtime. |
| **A/B test** | 两 version 同跑比 metric. Statistical test. |
| **Kill switch** | 一键关功能. Production 必备. |

### 通讯 / 客户管理 ⭐

| 术语 | 解释 |
|---|---|
| **Push back** ⭐ | **温和拒绝客户 ask**. 不是 "no", 是 "let's clarify why". |
| **Under-promise, over-deliver** ⭐ | 承诺保守, 超额完成. 比反过来 trust 多 10x. |
| **Status update** | 项目进度通报. Frequency 越高 trust 越高. |
| **Stakeholder alignment** | 跟所有相关方 sync. Emergency 时尤其重要. |
| **Customer Success Manager (CSM)** | 客户关系负责人. FDE 跟 CSM 配合. |
| **Executive sponsor** | 客户那边出钱拍板的人. |
| **Steering committee** | 项目治理委员会 — 出问题升级到这里. |
| **Escalation path** | 升级链. Customer 不满意时. |

### Eval / 验证

| 术语 | 解释 |
|---|---|
| **Smoke test** | 最低限度 "能跑就行" 测试. Emergency 时只跑这个. |
| **Regression test** | 检查老功能没坏. |
| **Golden path test** | 覆盖 happy path. |
| **0% wrong-call** | Indonesia refund tier 1 的 metric — 没 false positive. |
| **Coverage** | 自动化覆盖比例. Tier 1 70% coverage = 7 成 case 自动处理. |

### Postmortem / 学习

| 术语 | 解释 |
|---|---|
| **Tech debt sprint** | Ship 完 emergency 后专门还债的迭代. |
| **Postmortem (no-incident)** | 项目复盘 — 没事故也复盘 "what hurts". |
| **Wedding cake metaphor** | 90% 完成的蛋糕能 ship, 50% 是另一种产品. |

---

## 这道题在考什么

表面是 timeline 题, 底下藏着 **8 个 FDE evaluation signal**:

1. **Judgment under pressure** — 知道 cut scope, not corner-cut quality
2. **Never-compromise discipline** — data integrity, security, reversibility
3. **Scope reduction skill** — what to cut to fit
4. **Negotiation with customer** — push back vs accept
5. **Tech debt acceptance** — short-term ugly OK, long-term debt tracked
6. **Reversibility obsession** — must rollback if shipped breaks
7. **Customer relationship** — over-deliver communication > under-deliver code
8. **Specific shipped examples** — Indonesia refund tiered approach, voice agent phased market rollout

不考「怎么 ship 快」, 考「你被 deadline 砸过, 给了客户什么 + 拒绝了什么」.

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|---|---|---|
| 1 | **Push back first** | 3 min | Validate the deadline, understand the why | "Before I compromise, I push back gently — what's behind the deadline? Real business need vs anchored ask?" |
| 2 | **Renegotiate scope, not deadline** | 4 min | Slice feature into MVP + later phases | "Then I renegotiate scope, not deadline. Feature X is probably 5 capabilities — which 2 do you need by Friday?" |
| 3 | **What I compromise (5 things)** | 6 min | Scope, polish, automation, test depth, docs | "5 things I'll compromise — scope, polish/UX, automation (manual OK short-term), test depth (golden path only), docs (TODO)." |
| 4 | **What I NEVER compromise (5 things)** | 6 min | Data integrity, security, reversibility, observability, compliance | "5 things I NEVER compromise — data integrity, security/auth, reversibility (must rollback), observability (must debug), compliance." |
| 5 | **The tradeoff conversation** | 5 min | How to have it with customer + internal | "I have this conversation early. Customer-facing: 'Here's what fits, here's what doesn't.' Internal: 'Here's the debt, here's the payback plan.'" |
| 6 | **Phased rollout (compromise pattern)** | 4 min | Tier 1 by Friday, tier 2 next week | "Compromise pattern: phased rollout. Friday: tier 1 (70% of use cases, fully automated). Week 3: tier 2. Month 2: tier 3." |
| 7 | **Tech debt tracking** | 3 min | Track every shortcut, plan payback | "Every shortcut goes in a debt log with owner + payback date. No 'we'll fix later' without ticket." |
| 8 | **Quote Indonesia refund tier + voice agent market rollout** | 5 min | Real stories | "Indonesia refund — ops wanted full automation. I shipped tier 1+2 in 2 weeks at 70% coverage, 0% wrong. Tier 3 6 months later." |
| 9 | **The "no" conversation** | 3 min | When to say no even with pressure | "Sometimes I say no. Wedding cake metaphor: if you'd ship 90% finished cake, fine. If 50%, that's a different product." |
| 10 | **Post-emergency cleanup** | 1 min | Tech debt sprint, postmortem | "Within 2 weeks post-launch: tech debt sprint, postmortem on what we cut, what hurts." |

---

## 详细回答

### Step 1: Push back first (validate the deadline)

```
Don't accept "Friday or cancel" at face value. 4 questions:

1. "What specifically about Friday — is it tied to a customer event,
   contract clause, internal deadline?"
   
   Sometimes "Friday" means "this week ideally" — Wednesday next 
   week might be acceptable.

2. "What's the business consequence of missing Friday?"
   
   "They'll cancel" might be "they'll be upset." Verify with their
   stakeholder if possible.

3. "What does 'live' mean? Available to all users, or available to 
   specific team? Production-ready, or proof-of-concept?"
   
   Often "live by Friday" = "demo to their CEO on Friday" = MVP works
   for specific scenario.

4. "Have they expressed flexibility before? Is this their default ask, 
   or a hard deadline?"

After validation, often:
  - Friday is real for X reason (binding event)
  - Their actual need is Y scope, not full Z
  - I can deliver Y by Friday, defer Z to next week
```

**The negotiation script**:

```
Me: "I want to understand the deadline before committing. 
     Help me work through this — what's driving Friday specifically?"

Customer: "Our board meeting is Friday at 2 PM. CEO wants to 
           announce X capability."

Me: "Got it. Two scenarios:
     A) We have full X live for general users by Friday — need 2 weeks
     B) We have CEO-demo-ready slice of X by Friday — 3 days
     
     Which do you actually need on Friday?"

Customer: "Probably B is fine. We can roll out to users next week."

Me: "OK, I can do B by Thursday for prep time before Friday.
     Then we ship full X by [next Friday]. Sound good?"
```

**This isn't pushing back hard** — it's clarifying. Most "emergency deadlines" have flex inside.

### Step 2: Renegotiate scope, not deadline

```
If deadline is firm, scope becomes the variable.

"Feature X" almost always breaks into 5-7 capabilities:

Customer asks: "We need refund automation by Friday"

Decompose:
  - Identity verification (must)
  - Eligibility check (must)
  - Tier 1: simple refunds < $50 (high-value, low-risk)
  - Tier 2: medium refunds $50-200 (medium-value, medium-risk)
  - Tier 3: complex refunds > $200 / disputes (low-value, high-risk)
  - Notifications (nice-to-have)
  - Reporting / analytics (nice-to-have)

By Friday: Identity + Eligibility + Tier 1
Week 2:   + Tier 2
Month 2:  + Tier 3 (after extensive eval)
Month 3:  Notifications + Reporting
```

**Phased delivery is the answer** to most emergency deadlines.

### Step 3: What I compromise (5 things)

```
Compromise 1: SCOPE
  - Cut features (already discussed)
  - Cover happy path, defer edge cases
  - Single-tenant first, multi-tenant later
  - One language first, others later

Compromise 2: POLISH / UX
  - Rough UX OK short-term
  - "Click here" button instead of beautiful flow
  - Error messages "Something went wrong" OK (improve later)
  - No animations / transitions
  - Mobile responsive: desktop-first, mobile next phase

Compromise 3: AUTOMATION
  - Manual steps OK if rare (< 100/day)
  - Half-automated with human checkpoint
  - Cron job instead of event-driven
  - SQL queries instead of dashboard
  - "Run this script daily" runbook

Compromise 4: TEST DEPTH
  - Golden path tests only (no edge cases)
  - No mutation testing
  - Manual smoke test instead of full E2E
  - Skip cross-browser testing
  - But: ALWAYS have at least golden path coverage

Compromise 5: DOCS
  - Internal wiki "MVP-style" notes
  - README with TODO list of what's missing
  - Comments in code: "# HACK: hardcoded for emergency launch, see DEBT-123"
  - Customer-facing docs: minimum viable + verbal
```

**Examples of OK compromises**:

```
Indonesia refund tier 1+2 launched in 2 weeks (vs 6 weeks for full 3-tier):
  - Scope: tier 1+2 only (70% volume)
  - Polish: manual ops dashboard, no flashy UI
  - Automation: tier 2 had human checkpoint (not full auto)
  - Tests: golden path + edge cases for tier 1+2 only
  - Docs: 3-page runbook, customer training in person
```

### Step 4: What I NEVER compromise (5 things)

```
NEVER 1: DATA INTEGRITY
  - All writes must be transactional or idempotent
  - No "we'll reconcile later" for financial data
  - Every state change must be auditable
  - Race conditions must be addressed (not "we'll fix")
  
  Why: data corruption is irreversible. Money owed wrong = lawsuit / churn.

NEVER 2: SECURITY / AUTH
  - Authentication must be production-grade
  - Authorization checks on every endpoint
  - No "we'll add ACL later"
  - PII must be encrypted at rest + transit
  - Tokens never logged
  - Tenant isolation enforced
  
  Why: security breach is catastrophic + irreversible. PII leak = legal.

NEVER 3: REVERSIBILITY
  - Must be able to roll back (any deploy, any data migration)
  - Feature flags for new behaviors (toggle off without deploy)
  - Database migrations: forward + backward
  - No one-way doors
  
  Why: if shipped breaks, must restore previous state. 
  "We can't undo" = panic on incident.

NEVER 4: OBSERVABILITY
  - Logs, metrics, traces on critical paths
  - Audit trail of all writes
  - Per-user / per-tenant attribution
  - Alerts on SLO breach
  
  Why: at 2 AM you need to debug. Can't debug blind code.

NEVER 5: COMPLIANCE
  - HIPAA / SOX / GDPR / PCI applicable rules
  - Audit log retention
  - Data residency
  - Consent tracking
  
  Why: regulatory breach = fines, contract loss, license revoke.
```

**Hard rule**: even at 2 AM Friday, no compromise on these. If can't do them in time, **don't ship**.

### Step 5: The tradeoff conversation (with customer + internal)

**Customer-facing script**:

```
"I want to set expectations clearly. Here's what I can deliver Friday:

INCLUDED:
✓ Feature X for tier 1 use cases (70% coverage)
✓ Full security + authentication
✓ Audit log + ability to rollback
✓ Manual ops dashboard for monitoring
✓ Customer team training

NOT INCLUDED until [date]:
✗ Tier 2 use cases (need 1 more week)
✗ Beautiful UX (functional but rough)
✗ Self-service customer dashboard (using internal tool)
✗ Real-time notifications (email-batched for now)
✗ Reporting dashboards

DEBT WE'RE TAKING:
- Some manual steps (Ops will do 5-10 manual escalations/day)
- Hardcoded thresholds (configurable later)
- English-only error messages (i18n later)

I'll ship the full version by [date 2 weeks later]. 
Until then, we have 4 weekly check-ins to track tech debt cleanup.

Are these tradeoffs acceptable?"
```

**Why this works**:
- **Transparent** — customer sees exactly what they're getting
- **Limits** — what's NOT included is clear
- **Plan** — when full version arrives
- **Trust** — they see I respect their deadline AND quality

**Internal conversation** (with eng / PM):

```
"To hit Friday, here's our cut:
- Scope: tier 1 only
- Polish: manual ops dashboard
- Tests: golden path only
- Docs: TODO list

Tech debt we're taking (tracked in DEBT-123 to DEBT-128):
- Hardcoded thresholds
- Manual escalation step
- No retry on Indonesia-specific payment provider
- ...

Payback plan:
- Week 2: tier 2 + retry logic
- Week 4: ops dashboard automation
- Month 2: tier 3 + i18n
- Month 3: customer self-service

If we slip on payback, we re-evaluate at month 2."
```

### Step 6: Phased rollout (the compromise pattern)

```
Phase 1: Friday — MVP for 1 customer
  - Single-tenant, manually onboarded
  - Tier 1 scope (70% coverage)
  - Manual ops dashboard
  - Golden path tested
  - Feature flag gated to this customer only
  - Rollback plan tested

Phase 2: Week 2 — Tier 2 + 2nd customer
  - Add tier 2 scope (90% coverage)
  - Retry logic
  - 2nd customer onboarded
  - More edge cases tested

Phase 3: Week 4 — Tier 3 + GA prep
  - Tier 3 scope (98% coverage)
  - Auto-escalation workflow
  - Tested with synthetic edge cases
  - Other customers can enable

Phase 4: Month 2 — GA
  - Full feature parity
  - All customers
  - Self-service UI
  - Internal team trained
```

**Why phased**: 
- **Customer gets value Friday** (anchor)
- **Risk contained** (1 customer first)
- **Iteration** (learn from 1st customer before scaling)
- **Reversible** (feature flag off any time)

### Step 7: Tech debt tracking

```
Every shortcut goes into the debt log:

| Debt ID | Description | Created | Severity | Owner | Payback Date | Status |
|---------|-------------|---------|----------|-------|--------------|--------|
| DEBT-123 | Hardcoded refund threshold | 2026-05-20 | Med | Gao | 2026-06-05 | open |
| DEBT-124 | Manual ops dashboard | 2026-05-20 | Low | Gao | 2026-06-20 | open |
| DEBT-125 | No retry on payment | 2026-05-20 | High | Eng | 2026-05-30 | open |
| DEBT-126 | English-only errors | 2026-05-20 | Low | i18n | 2026-07-01 | open |

Review weekly. Closed = done. Overdue = team meeting.

Rule: no "we'll fix later" without DEBT ticket.

If accumulating > 20 open debt tickets: stop new features, debt sprint.
```

### Step 8: The phased recovery (post-emergency)

```
Week 1 post-launch:
  - Monitor production closely
  - Daily team sync
  - Customer feedback collection

Week 2 post-launch:
  - Postmortem: what went well / poorly
  - Debt sprint: clear top 3 highest-priority items
  - Customer follow-up: anything urgent?

Week 4 post-launch:
  - Tier 2 launch (was committed)
  - More debt cleared
  - Process improvement (so we don't do this again)

Month 2 post-launch:
  - Tier 3 launch
  - Most debt cleared
  - Postmortem on whole engagement
```

### Step 9: When to say "no" (even under pressure)

```
Saying "no" is sometimes the right answer:

Scenario: "Skip security review to hit deadline"
  Answer: NO. We can scope down, but we don't skip security.
  If we can't security-review in time, we don't ship.

Scenario: "Hardcode customer credentials to save 1 day"
  Answer: NO. Reversibility / security NEVER compromised.

Scenario: "Skip the postmortem because we're behind"
  Answer: NO. Skipping postmortem causes more incidents.

Scenario: "Just ship without testing, fix in production"
  Answer: NO. At minimum, golden path test.

When I say "no", I offer alternatives:
  - "I can't skip security, but I can scope down to a smaller feature 
    that needs less review"
  - "I can't ship without tests, but I can write golden-path tests 
    in 3 hours that cover 80% of usage"
```

**Cake metaphor**:
- **Yes**: ship 90% finished cake (looks rough, tastes great)
- **No**: ship 50% finished cake (half-raw, dangerous, ruins the brand)

---

## 关键决策 / 框架

### 5 things I compromise (memorize)

```
1. SCOPE         (cut features, phase rollout)
2. POLISH        (rough UX OK short-term)
3. AUTOMATION    (manual steps OK if rare)
4. TEST DEPTH    (golden path only, defer edges)
5. DOCS          (TODO list + verbal training)
```

### 5 things I NEVER compromise

```
1. DATA INTEGRITY    (transactional, idempotent, auditable)
2. SECURITY / AUTH   (production-grade authn/authz, tenant iso)
3. REVERSIBILITY     (rollback any change, feature flags)
4. OBSERVABILITY     (logs, metrics, traces, audit)
5. COMPLIANCE        (HIPAA/SOX/GDPR/PCI applicable)
```

### Decision framework

```
Q1: Can I deliver full scope by deadline?
   No → Q2
   Yes → Ship full scope

Q2: Can I cut scope to deliver core value?
   Yes → Phased delivery (Friday: tier 1, Week 2: tier 2, ...)
   No → Q3

Q3: Will compromising on quality items work?
   Polish: Yes
   Automation: Yes (if rare manual OK)
   Test depth: Partial (golden path required)
   Docs: Yes (TODO OK)
   Data integrity / Security / Reversibility: NO
   
Q4: Can deadline shift?
   No → Q5
   Yes → Renegotiate (Friday → Tuesday is often OK)

Q5: Say "no" — explain consequences
   "We cannot ship Friday without compromising data integrity / security.
    Options: (a) shift deadline to Tuesday, (b) cut scope to MVP X.
    What do you prefer?"
```

---

## 完整代码 / 架构图

### Phased delivery template

```python
# Phased rollout via feature flags

from datetime import datetime

class PhasedRollout:
    PHASES = [
        # Phase 1: Friday — MVP for 1 customer
        {
            'name': 'mvp',
            'start': datetime(2026, 5, 22, 18, 0),  # Friday 6 PM
            'features': ['feature_x_tier_1'],
            'enabled_for_tenants': ['customer_a'],
            'rollback_plan': 'feature flag off',
            'sla': 'best-effort, manual ops',
        },
        
        # Phase 2: Week 2 — Tier 2 + retry
        {
            'name': 'tier_2',
            'start': datetime(2026, 6, 5, 0, 0),
            'features': ['feature_x_tier_1', 'feature_x_tier_2', 'auto_retry'],
            'enabled_for_tenants': ['customer_a', 'customer_b'],
            'rollback_plan': 'tier_2 flag off, tier_1 remains',
            'sla': '99% uptime',
        },
        
        # Phase 3: Week 4 — Tier 3 + GA prep
        {
            'name': 'tier_3',
            'start': datetime(2026, 6, 19, 0, 0),
            'features': ['feature_x_tier_1', 'feature_x_tier_2', 
                         'feature_x_tier_3', 'auto_escalation'],
            'enabled_for_tenants': ['customer_a', 'customer_b', 'customer_c'],
            'rollback_plan': 'tier_3 flag off',
            'sla': '99.5% uptime',
        },
        
        # Phase 4: Month 2 — GA
        {
            'name': 'ga',
            'start': datetime(2026, 7, 22, 0, 0),
            'features': ['feature_x_ga'],
            'enabled_for_tenants': 'all',
            'rollback_plan': 'feature flag off + revert deploy',
            'sla': '99.9% uptime',
        },
    ]
    
    @staticmethod
    def current_phase():
        now = datetime.now()
        for phase in reversed(PhasedRollout.PHASES):
            if now >= phase['start']:
                return phase
        return None
    
    @staticmethod
    def is_enabled(feature_name, tenant_id):
        phase = PhasedRollout.current_phase()
        if not phase:
            return False
        if feature_name not in phase['features']:
            return False
        if phase['enabled_for_tenants'] == 'all':
            return True
        return tenant_id in phase['enabled_for_tenants']
```

### Tech debt tracker

```python
# debt/tracker.py

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class Severity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class TechDebt:
    id: str
    description: str
    created_date: datetime
    severity: Severity
    owner: str
    payback_date: datetime
    related_incident: Optional[str] = None
    status: str = 'open'
    closed_date: Optional[datetime] = None

class DebtTracker:
    def __init__(self, db):
        self.db = db
    
    async def add(self, debt: TechDebt):
        await self.db.insert('tech_debt', debt.__dict__)
        await self.notify_owner(debt)
    
    async def overdue(self):
        """Items past payback date."""
        return await self.db.query(
            'SELECT * FROM tech_debt WHERE status="open" AND payback_date < NOW()'
        )
    
    async def by_severity(self):
        """Group by severity."""
        return await self.db.query(
            'SELECT severity, COUNT(*) FROM tech_debt WHERE status="open" GROUP BY severity'
        )
    
    async def health_check(self):
        """Are we in good debt shape?"""
        overdue = await self.overdue()
        critical_count = await self.db.count('tech_debt', severity='CRITICAL', status='open')
        total_open = await self.db.count('tech_debt', status='open')
        
        return {
            'total_open': total_open,
            'overdue_count': len(overdue),
            'critical_count': critical_count,
            'health_status': 'red' if critical_count > 5 or len(overdue) > 10 else 'yellow' if total_open > 20 else 'green',
            'recommendation': self._recommend(total_open, critical_count, len(overdue))
        }
    
    def _recommend(self, total, critical, overdue):
        if critical > 5:
            return "STOP new features. Debt sprint required."
        if overdue > 10:
            return "Debt sprint next week. Critical items first."
        if total > 20:
            return "Slow new features. Allocate 30% time to debt."
        return "Healthy. Continue normal cadence."
```

### Architecture: emergency delivery

```
                  ┌─────────────────────────────────────┐
                  │  Customer: Need feature X Friday    │
                  └────────────────┬────────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────────┐
                  │  Step 1: PUSH BACK                  │
                  │  Validate deadline + scope          │
                  │  Negotiate "by Friday demo-ready"   │
                  └────────────────┬────────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────────┐
                  │  Step 2: DECOMPOSE FEATURE           │
                  │  Tier 1 (must)                       │
                  │  Tier 2 (nice)                       │
                  │  Tier 3 (later)                      │
                  └────────────────┬────────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────────┐
                  │  Step 3: PHASE PLAN                 │
                  │  Friday: Tier 1 to customer A       │
                  │  Week 2: + Tier 2 + customer B      │
                  │  Week 4: + Tier 3 + GA              │
                  └────────────────┬────────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────────┐
                  │  Step 4: COMPROMISE list             │
                  │  ✓ Scope cut                         │
                  │  ✓ Polish (rough UX OK)              │
                  │  ✓ Automation (manual OK)            │
                  │  ✓ Tests (golden path)               │
                  │  ✓ Docs (TODO list)                  │
                  │  ✗ Data integrity (no)               │
                  │  ✗ Security (no)                     │
                  │  ✗ Reversibility (no)                │
                  │  ✗ Observability (no)                │
                  │  ✗ Compliance (no)                   │
                  └────────────────┬────────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────────┐
                  │  Step 5: DEBT TRACKING               │
                  │  Every shortcut → DEBT-XXX ticket   │
                  │  Weekly review                       │
                  └────────────────┬────────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────────┐
                  │  Step 6: COMM                        │
                  │  Customer: "what's in, what's not"   │
                  │  Internal: "debt + payback plan"     │
                  │  Status page: phased rollout         │
                  └────────────────┬────────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────────┐
                  │  Step 7: SHIP + WATCH                │
                  │  Feature flag controlled             │
                  │  Rollback plan tested                │
                  │  Daily monitoring week 1            │
                  └────────────────┬────────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────────┐
                  │  Step 8: POST-LAUNCH                 │
                  │  Postmortem week 2                   │
                  │  Debt sprint                         │
                  │  Next phase delivery                 │
                  └─────────────────────────────────────┘
```

---

## Gao Xin 简历专属 reframe

### Indonesia refund tier (PRIMARY STAR)

**S** (Situation):
> "Indonesia ops team wanted full refund automation in 2 weeks. Their original ask was tier 1 + 2 + 3 (all complexity levels) fully automated, with self-service customer portal. Realistic estimate was 6-8 weeks for safe deployment. Indonesia regulator was watching after recent fintech industry issues — wrong refund = audit fail = market shutdown."

**T** (Task):
> "Deliver value in 2 weeks while not compromising on safety / data integrity / regulatory. Customer wanted full automation; I needed to convince them tiered approach was better."

**A** (Action — what I compromised + didn't):

```
Compromised:
✓ Scope: tier 1+2 only, not tier 3 (yet)
✓ Polish: internal ops dashboard, no customer self-service
✓ Automation: tier 2 had human "review and approve" checkpoint
✓ Test depth: comprehensive on tier 1 (full), golden path on tier 2 edges
✓ Docs: 5-page runbook + in-person training for ops team

NEVER compromised:
✗ Data integrity: every refund transaction has idempotency_key + audit log
✗ Security: customer auth + tier-specific authorization rules
✗ Reversibility: tier 3 hard-gated (must rollback decision available)
✗ Observability: real-time dashboard for ops + audit log for regulator
✗ Compliance: per-Indonesia regulator rules, separate ledger, immutable log

Phased plan:
Week 0:  Discovery + clarification
Week 1:  Build tier 1 + ops dashboard + audit log
Week 2:  Build tier 2 + human checkpoint, deploy with regulator
Week 3-26: Tier 1+2 production, learning
Month 6: Tier 3 launched with extensive eval (vs initial Friday ask)
```

**R** (Result):
- **Tier 1 + 2 launched in 2 weeks**: 70% volume coverage, **0% wrong refunds** in 6-month pilot
- **Tier 3 launched at month 6** after extensive eval (compared to initial Friday ask, much safer)
- **Regulator audit passed** (the no-wrong-refund record was decisive)
- **Ops throughput up 60%** vs manual baseline
- **Customer relationship strengthened**: "the tier-based approach was correct, we learned from your discipline" — they referenced this approach in subsequent projects

### Voice agent multi-market phased rollout (SECONDARY STAR)

**S**: Multi-market voice agent (7 markets). Product team wanted all 7 markets live in 2 months. Each market had different language, regulation, infrastructure.

**T**: Realistic delivery without sacrificing quality per market.

**A**: Phased market rollout:
- Month 1: Indonesia + Vietnam (similar regulations, primary languages have ASR strong)
- Month 2: Thailand + Brazil (medium complexity)
- Month 3: Philippines + Mexico (newer markets)
- Month 5: Pakistan (most complex — Urdu/English mixed, weakest infra)

Per market:
- Eval set 500 calls
- Compliance review with local regulator
- Pilot with 1% traffic before scaling

**R**: All 7 markets live by month 5, **0 regulatory incidents**, customer trust strong. (Original ask: all 7 by month 2.)

### BNPL chatbot — phased product rollout (TERTIARY STAR)

**S**: BNPL chatbot needed across 3 products (PayLater, Pay-in-4, Merchant Loan). PM wanted all 3 in launch.

**T**: Limited eng capacity, 3 products = unreasonable.

**A**: PayLater first (highest volume), Pay-in-4 next month, Merchant Loan month 3. Compromised: shared FAQ infrastructure, customized intent routing.

**R**: Each product launched smoothly. Merchant Loan would have been buggy if rushed.

---

## 5 个 Follow-ups

**Q1**: "Customer refuses tiered approach. Says 'all or nothing.' What do you do?"

**A**: 3-step response:
1. **Acknowledge** their position: "I understand 'all or nothing' is your strong preference."
2. **Show data**: "Here's what 'all by Friday' looks like — incomplete tier 3 = wrong refunds = regulator audit fail = market shutdown. The data integrity / compliance line is hard."
3. **Offer alternatives**:
   - (a) Cut tier 3 from scope entirely (it's the risky one)
   - (b) Extend deadline 2 weeks to do tier 3 safely
   - (c) Ship tier 1+2 Friday, tier 3 next month
   - (d) Different feature you might value more (e.g., notifications instead of tier 3)

If they STILL insist after data: **document my objection in writing**, escalate to my manager (and theirs), proceed only with explicit acknowledgment of risk. FDE is trusted advisor — sometimes "trusted" means saying "I disagree but I'll do it under your direction" or "I can't ship this safely, please choose alternative."

**Q2**: "Manager says 'just ship it, fix in production.' How do you handle?"

**A**:
1. **Specific objection**: "What I can't ship is X because Y. Specifically: shipping without retry on payment provider means 0.5% double-charges = $50k loss / week."
2. **Alternative**: "I can ship in 3 days with manual retry workaround. Or 2 days with feature flag off if anything breaks."
3. **Disagree and document**: if forced to ship anyway, document the risk in writing (email / Slack). When it breaks, the trail shows engineering tried to prevent.
4. **Don't quit on principle**, but don't ship unsafe code silently. Be transparent.

**Q3**: "Tech debt is piling up. When do you stop new features?"

**A**: 3 triggers for "debt sprint":
1. **Critical-severity debt count > 5**: stop, fix critical first
2. **Overdue debt > 10**: schedule 2-week debt sprint
3. **Production incidents linked to debt**: immediate debt sprint

Healthy state: < 20 open debt items, < 5 critical, < 5 overdue.

**Allocation rule**: at any time, 70% capacity new features, 20% bugs / quality, 10% debt. If debt is high, flip to 50/30/20 or 30/30/40 during sprint.

**Q4**: "How do you communicate tradeoffs to non-technical stakeholders?"

**A**: 3 techniques:
1. **Concrete examples**: "If we skip retry logic, 0.5% of payments will double-charge. At 100k payments/week, that's 500 customers, $50k loss + churn risk."
2. **Tradeoff matrix**: "Option A: full feature Friday + risk B. Option B: phased delivery + slower rollout. Option C: extend deadline 2 weeks."
3. **Analogies**: "It's like building a house — we can put in the walls now or skip them. Skipping saves time but the house collapses in a year. Worth it?"

Avoid: jargon ("idempotency"), false certainty ("this will be fine"), passive voice ("compromises were made").

**Q5**: "Post-emergency, debt cleanup — how do you make sure it actually happens?"

**A**: 4 mechanisms:
1. **Tracked in ticket system** (Jira / Linear) — visible, assigned, dated
2. **Weekly review** — 30 min team standup on debt status
3. **Quarterly debt sprint** — 2 weeks dedicated, no new features
4. **Customer-visible commitment** — "We promised this feature by date X. We deliver by date X."
5. **OKR / performance review** — debt cleanup counts as engineering output, not just feature velocity

Anti-pattern: "we'll get to it" — debt grows. Right pattern: scheduled time, visible tracking, accountability.

---

## ❌ 死路答法

1. **"I'll work overtime to ship full scope"** — hero culture, burns out, often misses anyway
2. **No "what I never compromise" list** — shows lack of judgment
3. **Compromise on security / data integrity** — irreversible damage
4. **No phased rollout consideration** — all-or-nothing thinking
5. **No tech debt tracking** — debt forgotten = recurs as incident
6. **No transparent customer comm** — under-delivers without setting expectation
7. **Accept deadline without question** — "yes, sir" attitude
8. **Refuse without alternative** — pure "no" without options
9. **No postmortem after emergency** — same pattern repeats
10. **Heroic solo** — doesn't lift team

---

## ✅ 加分项

1. **5 compromises + 5 never-compromise** explicit list
2. **Push-back first principle** — validate deadline
3. **Phased rollout pattern** as default
4. **Customer comm template** — what's in / what's not
5. **Tech debt log discipline** with owners + dates
6. **Reversibility obsession** — feature flags, rollback plans
7. **Specific examples** (Indonesia tier, voice agent market, BNPL product)
8. **Cake metaphor / 90% vs 50% finished**
9. **Post-emergency debt sprint** scheduled
10. **Quote regulator scrutiny + zero wrong refunds**

---

## 一句话总结

> **Emergency deadlines: compromise on SCOPE / POLISH / AUTOMATION / TEST DEPTH / DOCS. NEVER compromise on DATA INTEGRITY / SECURITY / REVERSIBILITY / OBSERVABILITY / COMPLIANCE. Default pattern is phased rollout (Friday: tier 1, Week 2: tier 2, Month 2: tier 3). Track every shortcut in debt log with owner + payback date. Indonesia refund tier 1+2 launched in 2 weeks at 70% coverage, 0% wrong refunds is the reference STAR.**

---

## Cheat Sheet

```
First step: PUSH BACK
  - What's behind the deadline?
  - What does "live" mean?
  - "Demo-ready" vs "production-ready"?
  - Hard deadline vs default ask?

Second step: RENEGOTIATE SCOPE NOT DEADLINE
  - Decompose feature (5-7 capabilities)
  - Phase delivery (tier 1 → tier 2 → tier 3)
  - "By Friday: most important slice"

5 things I compromise:
  1. SCOPE (cut features, phase rollout)
  2. POLISH / UX (rough OK short-term)
  3. AUTOMATION (manual OK if rare)
  4. TEST DEPTH (golden path only)
  5. DOCS (TODO list + verbal)

5 things I NEVER compromise:
  1. DATA INTEGRITY (transactional, idempotent, auditable)
  2. SECURITY / AUTH (production-grade, tenant iso)
  3. REVERSIBILITY (feature flags, rollback plan)
  4. OBSERVABILITY (logs/metrics/traces/audit)
  5. COMPLIANCE (HIPAA/SOX/GDPR/PCI)

Phased rollout (compromise pattern):
  Phase 1 (Friday): MVP, single customer, tier 1
  Phase 2 (Week 2): tier 2, second customer
  Phase 3 (Week 4): tier 3, GA prep
  Phase 4 (Month 2): GA

Tech debt tracking:
  - Every shortcut → DEBT-XXX ticket
  - Severity (low/med/high/critical)
  - Owner + payback date
  - Weekly review
  - Quarterly debt sprint
  - 70/20/10 allocation: features / bugs / debt
  - Flip to 30/30/40 during sprint

Health thresholds:
  Open debt: < 20 = healthy, > 30 = red
  Critical debt: > 5 = stop new features
  Overdue: > 10 = debt sprint scheduled

Customer comm template:
  INCLUDED: ...
  NOT INCLUDED until [date]: ...
  DEBT WE'RE TAKING: ...
  Are these tradeoffs acceptable?

When to say "no":
  - Skip security review
  - Skip data integrity
  - Skip reversibility
  - Skip compliance
  
  Always offer alternative.

Cake metaphor:
  90% finished cake (rough but functional) → YES
  50% finished cake (half-raw) → NO

Post-emergency:
  Week 1: monitor closely, daily sync
  Week 2: postmortem + debt sprint
  Week 4: tier 2 delivery (was committed)
  Month 2: tier 3 delivery + most debt cleared

Case studies:
  - Indonesia refund: tier 1+2 in 2 weeks, 0% wrong, tier 3 month 6
  - Voice agent: 7 markets in 5 months (not 2), 0 regulator incidents
  - BNPL chatbot: 1 product first, then 2, then 3 (not all at once)

Anti-patterns:
  - Hero overtime culture (burns out, misses anyway)
  - No "never compromise" line (shows poor judgment)
  - All-or-nothing (no phasing)
  - Silent under-delivery (no comm)
  - Yes-sir attitude (accept any deadline)
  - Pure refusal without alternative

Quotes for interview:
  - "Compromise on scope, not on data integrity"
  - "Friday is 'demo to CEO,' Tuesday is 'live to users' — clarify which"
  - "Phased rollout: tier 1 Friday, tier 2 Week 2, tier 3 Month 2"
  - "Every shortcut becomes a DEBT-XXX ticket"
  - "Indonesia tier 1+2 in 2 weeks at 70% coverage, 0% wrong"
  - "Reversibility is non-negotiable — must rollback if breaks"
```
