## Q51 · P0 postmortem in customer environment — how do you handle?

> "A P0 incident happened in a customer's production environment — your system caused customer-visible downtime. **Walk me through how you handle the postmortem with the customer** — 24h initial, 5-day full RCA, blameless tone but specific accountability, long-term reliability commitments. Different from internal postmortem."

**Round**: Production / Reliability (45 min)
**出处**: Exponent 2026 FDE Guide · 公司: OpenAI / Anthropic / Cohere / Scale AI — customer-facing IR experience 必问

---

## 📖 术语速查 (本题用到的)

> Customer-facing postmortem 题. 涉及 IR / 通讯 / 合规 / 客户管理多领域.

### Postmortem 类型 ⭐

| 术语 | 解释 |
|---|---|
| **Postmortem** ⭐ | **事后复盘文档**. Timeline + RCA + action items. |
| **Internal postmortem** | 给自己 team 看 — 完整技术细节, "我们 screwed up" tone. |
| **Customer-facing postmortem** ⭐ | **给客户看 — 技术但去 jargon, 抽象 internal team 名, "we own this" 但不 self-flagellate**. 跟 internal 截然不同. |
| **Public postmortem** | 完全公开 — Cloudflare / GitLab 常发. 透明 = 信任. |
| **24-hour brief / 24h initial** ⭐ | **事故 24h 内的简版 summary**. 5 elements: what / when / who-impacted / our actions / current status. |
| **5-day full RCA** ⭐ | **5 天内完整 Root Cause Analysis**. 含 timeline, RCA, action items + owners + ETAs. |
| **30-day status update** | 1 个月后 action items 进展. |
| **Quarterly reliability review** | 季度 trust-rebuilding meeting. |

### 通讯 Tone ⭐

| 术语 | 解释 |
|---|---|
| **Blameless** ⭐ | **不甩锅个人**. 系统 / process 失败. Google SRE 文化. |
| **Blameless but specific** ⭐ | **不甩锅 ≠ 模糊**. "We made mistake, here's exactly which gap, here's specific fix". |
| **Accountable** | 担责. "We own this" tone. |
| **Self-flagellating** | 自残式自责. 过头反而 erode customer trust. |
| **Trust rebuilding** ⭐ | **事故损害 trust, postmortem 是 ER, 长期 trust 靠持续 action**. |
| **Anonymize** | 去 internal team 名 — "team-X" 改 "our engineering team". |
| **De-jargonize** | 去技术黑话 — "K8s HPA" 改 "auto-scaling system". |

### RCA / 根因分析 ⭐

| 术语 | 解释 |
|---|---|
| **RCA (Root Cause Analysis)** ⭐ | 找真正原因 — 不是症状. |
| **5 whys** | 连续问 5 次 why 找根因. |
| **Contributing factor** ⭐ | **不是根因但 made things worse 的因素**. 多因素并列比单根因诚实. |
| **Trigger event / Root cause / Latent bug** | 直接触发 / 底层 gap / 老 bug 等触发. |
| **Single point of failure (SPOF)** | 一个 component 挂全挂. |

### Incident 元素 ⭐

| 术语 | 解释 |
|---|---|
| **Timeline** ⭐ | 事故 timestamp + event 列表. UTC 时间. |
| **Detection / Mitigation / Resolution** | 怎么发现 / 怎么止血 / 完全恢复. |
| **Impact / Blast radius** | User 数 / region / 持续时间 / business 损失. |
| **Affected requests** | 多少 request 挂. |
| **Data integrity** | 有没有丢 / 损坏数据. |
| **Customer impact statement** | "X% of your traffic for Y minutes" 公式. |

### Action Items ⭐

| 术语 | 解释 |
|---|---|
| **Action item** | 具体改进项. 必须有: title / owner / ETA / customer-visible. |
| **Owner** | 负责人. 不能是 "team", 必须 specific person. |
| **ETA (Estimated Time of Arrival)** | 完成日期. Customer 看到的承诺. |
| **Ticket ID / JIRA ticket** | 可 track 的工单. Customer 可 follow. |
| **Customer-visible action item** | Customer 能看见进度的 item. 跟 internal-only 区分. |
| **Trackable** | 有 ticket + 状态. |
| **Reliability OKR** | 季度可靠性目标. 跟客户 joint OKR = trust signal. |

### Customer Meeting ⭐

| 术语 | 解释 |
|---|---|
| **Customer review meeting** | Postmortem 后跟客户的视频会. Exec sponsor 必到. |
| **Walk-through + Q&A** | Doc 逐段读给客户听 + 答问. |
| **Commitment dates** | 具体承诺的 fix 日期. |
| **CSM / AE / TAM** | Customer Success Mgr / Account Exec / Technical Account Mgr — 客户管理三角. |

### 合规 / 监管 ⭐

| 术语 | 解释 |
|---|---|
| **HIPAA breach notification** ⭐ | **60 天内通知客户 + HHS**. PHI 涉及就触发. |
| **GDPR 72-hour notification** ⭐ | **72h 内通知 supervisory authority**. EU 数据涉及. |
| **SEC disclosure / SOX 404** | 上市公司重大 incident 披露 / 财报内控. |
| **PCI DSS incident** | 信用卡数据 incident — 通知 acquirer / 卡组织. |
| **DPO (Data Protection Officer)** | GDPR 下数据保护官. Breach 时要联系. |
| **Audit trail** | 不可变 log. Postmortem RCA 必备数据源. |

### 长期承诺 + IR 阶段 ⭐

| 术语 | 解释 |
|---|---|
| **Shared SLO dashboard** | 跟客户共享的可靠性 dashboard. 透明 = 信任. |
| **Joint OKR** | 跟客户共定 reliability 目标. 强 trust 信号. |
| **Quarterly business review (QBR)** | 季度业务回顾. 重大 incident 后强化频率. |
| **Renewal risk** | 续约风险. 大 incident 后升高. |
| **Detect → Triage → Mitigate → Investigate → Comm → Postmortem** | IR 6 阶段. |
| **MTTA / MTTD / MTTR** | Acknowledge / Detect / Resolve 时间. |
| **Steering committee** | 大 incident 升级到这里. |

---

## 这道题在考什么

表面是 postmortem 题, 底下藏着 **8 个 FDE evaluation signal**:

1. **Customer-facing IR experience** — 知道 customer postmortem 不是 internal postmortem
2. **Comm timing discipline** — 24h initial, 5-day full RCA, 30-day follow-up
3. **Blameless 但 specific** — 不甩锅, 但 specific 自己 team's actions
4. **Trust rebuilding** — postmortem 是 trust 损害的 ER, 不是 confession
5. **Customer review meeting** — face-to-face / video call execution
6. **Long-term commitment** — quarterly reliability review, shared dashboard, joint OKRs
7. **Specific shipped incidents** — Pakistan ASR, BNPL Anthropic spike, payment provider
8. **Regulatory awareness** — HIPAA / SOX 72-hour notification, regulator requirements

不考「postmortem template」, 考「你 broken customer's production, 24 小时内 first comm, 你写什么」.

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|---|---|---|
| 1 | **Customer postmortem ≠ internal** | 3 min | 5 key differences | "Customer postmortem is fundamentally different — tone, depth, audience, format, cadence." |
| 2 | **24-hour initial: what + when + how + impact + status** | 5 min | 5 elements of first comm | "24h doc: brief written incident summary. 5 elements — what happened, when, our actions, customer impact, current status." |
| 3 | **5-day full RCA: deep + accountable + action items** | 6 min | Timeline, RCA, prevention, owner | "5-day doc: detailed RCA with timeline, root cause analysis, action items with owners + ETAs." |
| 4 | **Tone: blameless but specific** | 4 min | We did X. Why? Y system gap. Fix: Z. | "Blameless ≠ vague. 'We made a mistake' ≠ 'X had bad day.' Specific: 'our X process gap allowed Y, we'll add Z.'" |
| 5 | **Customer review meeting** | 4 min | Live walkthrough + Q&A + commitment | "Meeting (Zoom / in-person): exec sponsor present, walk through doc, take questions, commit dates." |
| 6 | **Long-term reliability commitment** | 5 min | Shared dashboard, quarterly review, joint OKR | "30+ days: shared SLO dashboard, quarterly reliability review meeting, joint reliability OKRs." |
| 7 | **Customer-visible action items** | 4 min | Trackable, visible, dated | "Every action item: ticket ID, owner, date, monthly status sent to customer until closed." |
| 8 | **Regulatory specifics** | 3 min | HIPAA 60d, SOX, GDPR 72h, SEC | "If regulated industry: HIPAA breach 60 days, GDPR 72 hours, SEC may apply, work with customer's compliance team." |
| 9 | **Quote BNPL Anthropic spike postmortem / payment provider** | 4 min | Real customer-facing PM | "BNPL Anthropic latency spike — wrote 24h summary, full RCA day 4, monthly status until action items closed." |
| 10 | **Trust rebuilding mindset** | 2 min | Long-game, prove with action | "Postmortem is start, not end. Trust = consistent action over time. Don't promise what you can't deliver." |

---

## 详细回答

### Step 1: Customer postmortem ≠ Internal postmortem (5 differences)

```
Difference 1: AUDIENCE
  Internal:   eng team, engineering manager, VP eng
  Customer:   customer engineering + product + sometimes executives
              + legal + compliance

Difference 2: DEPTH OF DETAIL
  Internal:   full technical depth (specific code, configs)
  Customer:   technical but not "internal jargon" 
              (anonymize internal team names, abstract some specifics)

Difference 3: TONE
  Internal:   "we screwed up", reflective, learning
  Customer:   "we own this", accountable but not self-flagellating
              (don't undermine customer's trust in your team)

Difference 4: ACTION ITEMS
  Internal:   "fix the regression"
  Customer:   "we will deploy regression test by date X, you'll be 
              notified when complete"
              (customer-visible commitment)

Difference 5: CADENCE
  Internal:   one postmortem doc, weekly action items review
  Customer:   24h initial → 5-day full → 30-day status → ongoing 
              quarterly review
```

### Step 2: 24-Hour Initial Communication

**Send within 24 hours of incident**:

```
Email: [P0] Postmortem — Service Disruption 2026-05-22

Hi [customer eng lead],

We experienced a P0 incident affecting your tenant from 14:32 UTC 
to 15:30 UTC on 2026-05-22 (58 minutes).

Below is our initial incident summary. We will provide a full RCA 
with action items by 2026-05-27.

---

WHAT HAPPENED:
A deployment we made introduced a regression in our inference 
service's handling of long-context requests (>50k tokens). 
This caused approximately 30% of long-context requests in your 
tenant to timeout instead of returning responses.

WHEN:
- 14:32 UTC — First failed request observed
- 14:35 UTC — Internal alerting fired (drift detection)
- 14:38 UTC — Investigation began
- 14:50 UTC — Mitigation deployed (rollback to previous version)
- 15:30 UTC — Service fully restored

WHO WAS IMPACTED:
- Estimated 30% of your tenant's queries during the incident window
- All requests with >50k input tokens
- Approximately 8,500 user-facing requests affected
- No data loss or corruption — all requests were retried client-side 
  successfully after mitigation

OUR ACTIONS (immediate):
- Engineering ack'd within 3 minutes of detection
- Mitigation (rollback) deployed within 18 minutes
- All affected requests have been retried per our retry policy

CURRENT STATUS:
- Service stable since 15:30 UTC
- Previous version (1.4.2) running, no degradation
- 24/7 monitoring active

WHAT'S NEXT:
- Full RCA + action items document by 2026-05-27 (5 days)
- We will schedule a review call with your team
- 30-day status updates on action item progress

We deeply regret the disruption. Please reach out with any 
immediate questions.

[Account team contact]
[Engineering escalation contact]
```

**5 elements**:
1. **What happened** (technical summary, accessible)
2. **When** (timeline)
3. **Who was impacted** (specific numbers)
4. **Our actions** (response timeline)
5. **What's next** (full RCA promise + ETA)

### Step 3: 5-Day Full RCA Document

**Format** (10-15 pages):

```markdown
# Postmortem: Service Disruption — Long-Context Request Regression
## Date: 2026-05-22 | Duration: 58 minutes | Severity: P0

## Executive Summary

On 2026-05-22 at 14:32 UTC, a software regression in our inference 
service caused approximately 30% of long-context requests (>50k tokens) 
in [Customer]'s tenant to timeout for 58 minutes. The root cause was 
an untested code path in our deployment, deployed during off-hours 
without manual canary verification.

We have implemented immediate mitigations and committed to 6 
preventive action items with completion dates within 30 days.

## Incident Timeline

| Time (UTC) | Event |
|-----------|-------|
| 14:30:00 | Deploy of v1.4.3 to production completed (automated) |
| 14:32:00 | First failed long-context request observed |
| 14:35:00 | Internal alerting fired (drift detection threshold) |
| 14:35:30 | On-call engineer paged, acknowledged |
| 14:38:00 | Triage begins |
| 14:42:00 | Hypothesis: regression in v1.4.3 long-context handling |
| 14:44:00 | Customer Slack channel notified |
| 14:47:00 | Rollback initiated to v1.4.2 |
| 14:50:00 | Rollback complete, monitoring |
| 14:55:00 | Error rate dropping (30% → 8%) |
| 15:05:00 | Error rate normal (<0.5%) |
| 15:30:00 | Confirmed full restoration, monitoring period complete |
| 15:35:00 | Customer status page updated to "resolved" |

## Impact

### Customer Impact
- **Tenant affected**: [Customer]
- **Duration**: 58 minutes
- **Requests affected**: ~8,500 (30% of long-context queries)
- **Endpoints affected**: /v1/chat/completions with >50k input tokens
- **Other endpoints**: unaffected
- **Data integrity**: no loss, no corruption
- **Compliance**: no PHI/PII exposure (verified via audit log review)

### Service Impact
- Error rate: spiked to 30% on affected endpoint
- Latency p99: 8s (baseline 800ms) before timeout
- Cost: refund to customer for impacted window per SLA = $X

## Root Cause Analysis

### Direct Cause
A regression in v1.4.3 introduced incorrect handling of attention 
mask for context lengths exceeding 50,000 tokens. The new code path 
attempted to allocate a buffer that exceeded the GPU memory limit, 
causing the inference to silently hang until our 30-second timeout.

### Contributing Factors

**Factor 1: Test coverage gap**
Our test suite does not include >50k token integration tests. The 
regression passed all unit tests because they used inputs <2k tokens.

**Factor 2: Canary deployment skipped**
Our automated deploy pipeline ran v1.4.3 directly to 100% of traffic 
without canary stage. The canary configuration for this service was 
disabled due to flaky tests blocking deploys. We had not re-enabled 
canary after fixing the test flakiness.

**Factor 3: Detection threshold**
Our drift detection threshold was at 5% error rate. Errors crossed 
that threshold at 14:35 UTC (3 minutes after first failure), causing 
3-minute detection lag.

### 5-Whys Analysis

Q1: Why did errors spike?
A1: v1.4.3 deploy introduced regression in long-context handling.

Q2: Why was the regression not caught in testing?
A2: No long-context test in our test suite.

Q3: Why no long-context test?
A3: Long-context functionality added 6 months ago, tests not added.

Q4: Why were tests not added?
A4: No mandatory test coverage requirement for new endpoints.

Q5: Why no requirement?
A5: Test discipline process gap. We add tests when bugs are found 
    rather than as standard practice.

→ Root cause: Process gap in test discipline, not individual error.

## What Went Well

1. **Detection**: drift monitoring caught within 3 minutes
2. **Acknowledgment**: on-call acked within 30 seconds of page
3. **Mitigation**: rollback deployed within 18 minutes
4. **Communication**: customer Slack notified at 14:44 (12 min after start)
5. **Recovery**: errors back to baseline within 23 min of mitigation

## What Went Poorly

1. **No canary deployment** for v1.4.3 (would have caught at <1% traffic)
2. **Test gap** allowed regression to ship
3. **Detection lag** of 3 minutes (could be faster)
4. **Customer notification** delayed by 12 minutes (target was 5)
5. **Status page** updated 12 minutes after detection (target was 5)

## Action Items

| # | Action | Severity | Owner | Due | Status |
|---|--------|----------|-------|-----|--------|
| 1 | Add integration test suite for long-context (>50k tokens) | High | Eng [team A] | 2026-06-05 | In progress |
| 2 | Re-enable canary deployments for inference service | High | DevOps [team B] | 2026-05-29 | Open |
| 3 | Lower drift detection threshold from 5% to 3% | Med | SRE [team C] | 2026-06-12 | Open |
| 4 | Automated status page updates on incident detection | Med | DevOps [team B] | 2026-06-19 | Open |
| 5 | Mandatory test coverage requirement for new endpoints | Med | Eng leadership | 2026-07-01 | Open |
| 6 | Update runbook with this incident pattern | Low | On-call rotation | 2026-05-29 | Open |

## Customer Commitments

We will provide [Customer]:
- **Weekly status update** on action items until all closed
- **30-day follow-up call** to review progress
- **Quarterly reliability review** ongoing
- **Shared SLO dashboard** showing real-time error budget for your tenant
- **Service credit** of $X per our SLA

## Long-term Reliability Commitments

Beyond this specific incident, we are committing to:

1. **Quarterly Reliability Review**: 60-minute call each quarter to 
   review SLO performance, action items, and reliability investments.

2. **Joint Reliability OKR**: We propose joint OKR with [Customer]'s 
   team for next quarter:
   - 99.9% uptime for your tenant (vs current 99.5% SLA)
   - Detection MTTR < 2 minutes (vs current 3 minutes)
   - Customer notification < 5 minutes from detection

3. **Reliability Investment**: $X engineering capacity dedicated to 
   reliability improvements next quarter.

## Appendix

### A. Affected Request Sample
[Anonymized list of 10 sample request_ids and timestamps]

### B. Mitigation Process Detail
[Step-by-step what engineering did]

### C. SLA / Contract Reference
[Relevant SLA clauses, service credit calculation]

### D. Internal Engineering References
[Links to internal tickets for action items — visible if customer requests]

---

Prepared by: Gao Xin, Forward Deployed Engineer
Approved by: VP Engineering
Date: 2026-05-27
```

### Step 4: Tone — blameless but specific

**Blameless ≠ vague**.

```
BAD (vague, defensive):
"We experienced some service issues yesterday. We're investigating and 
will improve. Our team works hard to provide quality service."

→ Customer thinks: "They're hiding something. They'll do it again."

BAD (blameful, throws individuals under bus):
"Engineer X failed to add tests. Engineer Y deployed without canary. 
We've spoken with them."

→ Customer thinks: "Bad culture. People are afraid. Won't be transparent next time."

GOOD (blameless, specific):
"Our test coverage process did not require integration tests for new 
endpoints, allowing a regression to ship. We will deploy a mandatory 
test coverage policy by 2026-07-01.

Our deployment pipeline had canary stage disabled due to unrelated 
test flakiness from 3 weeks ago. We did not re-enable canary after 
fixing the flakiness. We've re-enabled canary effective 2026-05-29, 
and will add a 'canary enabled' check to our deploy verification."

→ Customer thinks: "They understand the system gap. They're fixing it. 
                    Trust restored."
```

**Tone principles**:
- **First person plural**: "we" not "engineering" or "the team"
- **Specific actions**: "we will deploy X by date Y" not "we'll work on it"
- **Acknowledge without apologizing 10x**: one clear "we regret this" is enough
- **No "expected" language**: don't say "we expected this could happen" — that's worse
- **No hedging**: don't say "this was unprecedented" if it wasn't

### Step 5: Customer review meeting

**Format**: 60-minute video call within 3-5 days of incident.

**Attendees**:
- Our side: FDE (you), engineering lead, account exec, optionally VP eng
- Customer side: their engineering lead, product, sometimes exec, sometimes legal

**Agenda**:

```
0-5 min: Greetings + opening
  Customer exec: "We're disappointed but want to understand"
  Our exec: "We take this seriously, here's our plan"

5-25 min: Walk through postmortem doc (FDE leads)
  - Timeline
  - Root cause
  - Action items
  - Long-term commitments

25-45 min: Q&A
  - Customer asks specific questions
  - We answer with specifics + commitments
  - Document any new commitments

45-55 min: Forward-looking discussion
  - Quarterly reliability review schedule
  - Joint OKRs proposal
  - Communication channels

55-60 min: Close
  - Thank you, commitments restated
  - Next touchpoint (30-day status)
```

**Tips**:
- **No defensiveness**. If they're angry, let them vent. Don't argue.
- **Specifics over generalities**. "We've added test X by date Y" > "We'll improve testing"
- **Take action items publicly**. If they ask for something new, "Let me commit to that — owner Z, by date W"
- **Document**. Send written summary within 24 hours of the call.

### Step 6: Long-term reliability commitments

```
Beyond the immediate postmortem, build reliability partnership:

1. Shared SLO Dashboard
   - Real-time view of your tenant's error budget
   - Customer can see if you're burning budget
   - Builds trust through transparency

2. Quarterly Reliability Review
   - 60-min meeting every quarter
   - Review past quarter SLO performance
   - Discuss upcoming reliability investments
   - Joint OKR check-in

3. Joint Reliability OKR
   - Mutual goal (e.g., 99.9% uptime for your tenant)
   - Both sides accountable
   - Tracked in shared doc

4. Reliability Investment Commitment
   - $X engineering capacity dedicated
   - Specific projects (e.g., HA infrastructure, drift detection)
   - Visible to customer

5. Direct Engineering Communication
   - Dedicated Slack channel with on-call eng
   - 15-min response SLA for P1+
   - Direct phone for P0

6. Status Page Subscription
   - Customer subscribed to incidents
   - SMS / email notifications

7. Pre-incident Communication
   - For planned maintenance: 7+ days notice
   - For risky deploys to their tenant: 24+ hours notice
   - For dependency changes: 48+ hours notice
```

### Step 7: Action item tracking

```
Every action item must be:

1. SPECIFIC
   Bad: "Improve testing"
   Good: "Add integration test suite for long-context (>50k tokens) requests"

2. OWNED
   Bad: "Engineering will do this"
   Good: "[Specific team / person]"

3. DATED
   Bad: "Soon"
   Good: "2026-06-05"

4. TRACKABLE
   - Internal ticket: JIRA-12345
   - Customer-visible: monthly status update

5. VERIFIED
   - When complete, demonstrate to customer
   - "Action item #1 (long-context tests) — deployed 2026-06-04, 
      see test results: [link]"

Monthly status template to customer:

"30-day status on Action Items from 2026-05-22 incident:

#1 Long-context test suite: COMPLETE (deployed 2026-06-04)
#2 Canary deployments re-enabled: COMPLETE (deployed 2026-05-28)
#3 Drift threshold 5%→3%: COMPLETE (deployed 2026-06-08)
#4 Status page automation: IN PROGRESS (target 2026-06-19)
#5 Test coverage policy: IN PROGRESS (rolling out, complete 2026-07-01)
#6 Runbook update: COMPLETE (2026-05-29)

Next status: 2026-07-22"
```

### Step 8: Regulatory specifics

```
Different industries have different requirements:

HIPAA (US healthcare):
  - Breach notification within 60 days
  - Affected individuals + HHS notification (if 500+ people)
  - Media notification (if 500+ in one state)
  - Breach assessment required

GDPR (EU):
  - Notification within 72 hours of awareness
  - Personal data controller authority + affected individuals (if high risk)
  - Breach register maintained

SOX (US financial reporting):
  - Material weakness disclosure may be required
  - Internal controls update
  - Auditor notification

SEC Reg SCI (US securities):
  - Incident report within 24 hours
  - SEC notification for major events
  - Update systems compliance

PCI-DSS (payment cards):
  - Investigation within 72 hours
  - Notify card brands
  - Forensic investigation
  - SAQ / certification impact assessment

Working with customer's compliance team:
  - Determine if your incident triggers their regulatory obligation
  - Provide evidence / documentation they need
  - May be required to engage their legal counsel
  - Document chain of custody for evidence
```

---

## 关键决策 / 框架

### Postmortem timeline (canonical)

```
T+0:     Incident starts
T+0-1h:  Detect → triage → mitigate
T+1-4h:  Resolve, initial monitoring
T+24h:   Initial customer postmortem (24-hour comm)
T+24h-5d: Investigation, action item planning
T+5d:    Full RCA document delivered
T+5-7d:  Customer review meeting
T+30d:   First monthly status update
T+60d:   Second monthly status
T+90d:   Quarterly reliability review begins
T+90d+:  Ongoing quarterly reviews
```

### Action item severity → response

```
CRITICAL: blocks future incidents OR has regulatory implication
  Must complete within 2 weeks
  Updates weekly

HIGH: prevents class of incidents
  Must complete within 30 days
  Updates monthly

MEDIUM: incremental improvement
  Must complete within 90 days
  Updates quarterly

LOW: nice to have
  Track but no commitment
```

### Customer-visible vs internal action items

```
ALWAYS customer-visible:
  - Process changes (deploy, testing, comm)
  - Direct mitigations
  - Long-term reliability commitments

CAN remain internal:
  - Specific tooling changes (CI/CD details)
  - Individual training
  - Code-level fixes (mention without details)
```

---

## 完整代码 / 架构图

### Customer postmortem workflow

```python
from datetime import datetime, timedelta
from enum import Enum

class IncidentSeverity(Enum):
    P0 = 0  # major customer-visible outage
    P1 = 1  # significant degradation
    P2 = 2  # minor impact
    P3 = 3  # internal only

class CustomerPostmortemWorkflow:
    """Automated reminders + commitments for customer-facing PM."""
    
    def __init__(self, incident_id, customer_id, severity, started_at):
        self.incident_id = incident_id
        self.customer_id = customer_id
        self.severity = severity
        self.started_at = started_at
        self.resolved_at = None
        self.deliverables = []
        self.action_items = []
    
    def schedule_deliverables(self):
        """Schedule all customer-facing deliverables."""
        if self.severity not in (IncidentSeverity.P0, IncidentSeverity.P1):
            return  # only P0/P1 get formal customer PM
        
        # 24-hour initial comm
        self.deliverables.append(Deliverable(
            type='initial_comm',
            due=self.started_at + timedelta(hours=24),
            template='initial_24h.md',
            recipient=self.customer_id
        ))
        
        # 5-day full RCA
        self.deliverables.append(Deliverable(
            type='full_rca',
            due=self.started_at + timedelta(days=5),
            template='full_rca.md',
            recipient=self.customer_id,
            requires_approval=['eng_lead', 'vp_eng']
        ))
        
        # Customer review meeting
        self.deliverables.append(Deliverable(
            type='review_meeting',
            due=self.started_at + timedelta(days=7),
            format='video_call_60min',
            attendees=['customer_eng_lead', 'customer_product', 'us_fde', 'us_eng_lead', 'us_account_exec']
        ))
        
        # 30-day status
        self.deliverables.append(Deliverable(
            type='status_update',
            due=self.started_at + timedelta(days=30),
            template='30d_status.md'
        ))
        
        # 60-day, 90-day status
        for days in [60, 90]:
            self.deliverables.append(Deliverable(
                type='status_update',
                due=self.started_at + timedelta(days=days),
                template='monthly_status.md'
            ))
        
        # Quarterly reliability review (recurring)
        self.deliverables.append(Deliverable(
            type='quarterly_review',
            recurring=True,
            cadence=timedelta(days=90),
            first_due=self.started_at + timedelta(days=90)
        ))
    
    def add_action_item(self, action_item):
        self.action_items.append(action_item)
    
    def status_update(self):
        """Generate status update for customer."""
        action_status = []
        for item in self.action_items:
            action_status.append({
                'id': item.id,
                'description': item.description,
                'status': item.status,
                'due': item.due,
                'completion_evidence': item.evidence if item.status == 'complete' else None,
            })
        return action_status

@dataclass
class ActionItem:
    id: str
    description: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    owner: str
    due: datetime
    status: str  # 'open', 'in_progress', 'complete', 'verified'
    evidence: Optional[str] = None  # link / proof of completion
    customer_visible: bool = True
```

### Architecture: trust restoration system

```
                  ┌───────────────────────────────────────┐
                  │  P0 Incident in Customer Tenant       │
                  └────────────────┬──────────────────────┘
                                   │
                                   ▼
                  ┌───────────────────────────────────────┐
                  │  IMMEDIATE (0-1 hour)                  │
                  │  • Triage + mitigate                   │
                  │  • Customer Slack ping                 │
                  │  • Engineering eng manager on call     │
                  └────────────────┬──────────────────────┘
                                   │
                                   ▼
                  ┌───────────────────────────────────────┐
                  │  24-HOUR COMM                          │
                  │  • Initial summary email/doc           │
                  │  • What/when/who/actions/status        │
                  │  • Commit to 5-day full RCA            │
                  └────────────────┬──────────────────────┘
                                   │
                                   ▼
                  ┌───────────────────────────────────────┐
                  │  5-DAY FULL RCA                        │
                  │  • Detailed timeline                   │
                  │  • Root cause + 5-whys                 │
                  │  • Action items + owners + dates       │
                  │  • What went well/poorly               │
                  │  • Long-term commitments               │
                  └────────────────┬──────────────────────┘
                                   │
                                   ▼
                  ┌───────────────────────────────────────┐
                  │  CUSTOMER REVIEW MEETING (5-7 day)     │
                  │  • Video call, exec sponsors           │
                  │  • Walk through doc                    │
                  │  • Q&A                                 │
                  │  • Forward-looking partnership         │
                  └────────────────┬──────────────────────┘
                                   │
                                   ▼
                  ┌───────────────────────────────────────┐
                  │  30-60-90 DAY STATUS UPDATES           │
                  │  • Action items progress               │
                  │  • Evidence of completion              │
                  │  • Recurring touchpoints               │
                  └────────────────┬──────────────────────┘
                                   │
                                   ▼
                  ┌───────────────────────────────────────┐
                  │  ONGOING QUARTERLY RELIABILITY REVIEW  │
                  │  • Joint OKRs                          │
                  │  • Shared SLO dashboard                │
                  │  • Reliability investment              │
                  │  • Direct engineering contact          │
                  └───────────────────────────────────────┘
```

---

## Gao Xin 简历专属 reframe

### BNPL Anthropic latency spike postmortem (PRIMARY STAR)

**S** (Situation):
> "February 2026, Anthropic API regional outage caused BNPL chatbot to have elevated latency for our biggest customer (a financial holding company) for 25 minutes. Some users saw 'slow loading' indicators. Customer noticed and escalated to their VP eng."

**T** (Task):
> "Customer-facing postmortem demonstrating accountability without overpromising. Customer was angry but wanted to understand if this was systemic vs one-off."

**A** (Action — concrete postmortem timeline):

```
T+0       Anthropic regional issue starts
T+2 min   Our drift detection caught latency spike
T+5 min   Mitigation: cached fallback activated, 30% of queries served from cache
T+10 min  Customer eng pinged in shared Slack ('we're seeing slow loading')
          → I responded immediately: "We're investigating, on-call engaged"
T+25 min  Anthropic resolved, normal latency restored
T+30 min  Customer-facing status update: "Issue resolved, postmortem incoming"

T+24h     Initial 24-hour comm sent:
          "Service experienced elevated latency for 25 min on 2026-02-15 
           due to upstream provider (Anthropic API) regional issue. 
           Our cached fallback mitigated user-facing failures (0% errors,
           ~25% queries served from cache with acceptable quality).
           Full RCA by 2026-02-20."

T+5d      Full RCA delivered:
          - Detailed timeline with Anthropic's status correlation
          - Action items:
            1. Multi-vendor failover (currently Anthropic-only)
            2. Tiered fallback (cache → multi-vendor → degraded)
            3. Customer notification at <5 min detection (was 10 min)
            4. Shared SLO dashboard with customer

T+7d      Customer review call (90 minutes, longer than usual)
          - Customer VP eng angry about Anthropic dependency
          - I walked through multi-vendor architecture plan
          - Committed multi-vendor failover by end of Q1
          - Customer agreed to quarterly reliability review

T+30d     Status update:
          - Multi-vendor framework deployed (action #1 complete)
          - Tiered fallback in testing (action #2 in progress)
          - Customer notification <5 min implemented (action #3 complete)
          - Shared SLO dashboard live (action #4 complete)

T+90d     Quarterly reliability review:
          - SLO performance reviewed (99.8% uptime achieved, target 99.5%)
          - 2 more incidents in quarter, both <P2
          - Trust noticeably restored
```

**R** (Result):
- **Customer relationship**: from threatened cancellation to strongest customer reference
- **Multi-vendor architecture** shipped (action item)
- **0 P0 incidents** in following 6 months
- **Quarterly reviews** continued, now expanded to 4 different customers
- **Industry recognition**: customer mentioned us as reliability exemplar at industry event

### Pakistan ASR 40-min outage (with regulator angle)

**S**: Pakistan ASR vendor 40-min outage. Calls completed but with 1.5x latency. Regulator was watching pilot.

**T**: Customer postmortem with regulatory implications. Pakistan financial regulator required incident report within 14 days.

**A**:
- T+8h: First customer comm (Pakistan ops team, not full RCA yet)
- T+24h: Initial summary email
- T+5d: Full RCA, included regulator-facing addendum
- T+7d: Customer review meeting (Pakistan ops + compliance + ours)
- T+10d: Submitted regulator incident report (per their schedule)
- T+30d: Status update with multi-vendor failover deployed

**R**: 
- Regulator approved the incident handling
- Pakistan pilot continued (was at risk of suspension)
- Multi-vendor pre-configured for all markets (action item)
- 0 regulatory issues in 12 months following

### Payment provider intermittent failures (no incident, but proactive PM)

**S**: Payment provider had intermittent 5xx errors (1-3% rate). No customer-visible impact thanks to idempotency + retry + queue.

**T**: Proactive postmortem-style comm because some customers noticed slowness.

**A**:
- Wrote "proactive incident summary" — short doc explaining we detected and mitigated upstream issue
- Sent to 3 affected customers within 12 hours
- Followed up with monthly reliability summary

**R**: Customer trust strengthened by proactive transparency vs being asked later "what happened."

---

## 5 个 Follow-ups

**Q1**: "Customer asks for personal accountability — 'who did this?' How do you respond?"

**A**: Redirect from individual to system:
1. **Acknowledge their frustration**: "I understand you want to know who's accountable."
2. **Reframe to system**: "I want to be transparent — the system gap that allowed this is [process X]. The accountable team is [team Y], led by [eng lead Z]."
3. **No throwing under bus**: don't name individual engineers ("an engineer made a mistake"). Use team / process framing.
4. **Specific accountability**: "I am the FDE accountable for your engagement. [Eng lead] is accountable for the service. We both report to [VP] who is ultimately accountable."
5. **Action over name**: "More important than who: what we'll do. Action items #1-6 prevent recurrence."

Blameless ≠ unaccountable. Be specific about who owns fixes.

**Q2**: "Customer asks for service credit. How do you handle?"

**A**:
1. **Check SLA**: "Our SLA provides X% credit for downtime exceeding Y. Let me calculate based on this incident."
2. **Be generous beyond SLA if appropriate**: "Per SLA you'd get $X. Given this was clearly preventable, we're offering $Y." Build trust.
3. **Don't argue specifics during the heat**: agree to credit, finalize amount in writing within 1 week.
4. **Document precedent**: "This credit is per SLA, doesn't set precedent for future." Or "We're treating this as exceptional, here's why."
5. **Process automation**: most mature companies auto-calculate SLA credit so you don't argue.

**Q3**: "Customer wants you to fire the engineer responsible. How handle?"

**A**: Hard line — don't.
1. **Listen first**: "I hear you. Let me understand specifically what concerns you."
2. **Reframe firmly**: "Firing won't prevent recurrence — the process gap will recur with anyone. The fix is process, not person."
3. **Show action**: "What you really want is confidence this won't recur. Here's our action plan to prevent that."
4. **If still demanding**: escalate to leadership. "I understand. Let me bring my VP and your VP into this conversation. This is above my level."
5. **Never agree to fire** in heat of moment. Internally HR / leadership decides individual performance — not a customer demand.

**Q4**: "What if the incident was the customer's fault (their config / their usage)?"

**A**: Even then, be customer-centric:
1. **Don't blame customer publicly**: "Our system allowed the misconfiguration to cause impact" — that's the gap.
2. **Joint postmortem**: present facts, customer's config + our response. Both sides own learnings.
3. **System fix**: "Our system could have caught the bad config / provided better error / prevented this." Often we can improve.
4. **Education**: "We'll provide documentation / training on the configuration that triggered this."
5. **Set expectation**: if customer keeps doing the same thing, eventually push back firmly. But first incident — own it.

**Q5**: "How do you measure if customer trust is restored?"

**A**: 5 signals:
1. **Engagement**: are they responding to your status updates? Asking questions?
2. **Renewal**: did contract renew at next cycle?
3. **Expansion**: are they buying more / adding products?
4. **Referral**: do they mention you positively to other customers?
5. **Joint OKR**: do they want to set joint reliability goals?

If any 3 of these are positive within 90 days, trust is restoring. If all 5 negative, may have lost the customer regardless of postmortem quality.

---

## ❌ 死路答法

1. **Customer PM = internal PM** (different audience, depth, tone, cadence)
2. **Vague language** ("we'll improve") without specific actions / dates
3. **Blame individuals** publicly (bad culture, customer loses trust)
4. **Defensive tone** (the customer notices, trust drops)
5. **No long-term commitment** (postmortem is start, not end)
6. **No customer review meeting** (written-only feels cold)
7. **Skip 30-60-90 day status** (forget about customer after initial PM)
8. **No regulatory awareness** (HIPAA / GDPR / SOX have requirements)
9. **No service credit offer** (sometimes part of trust restoration)
10. **Heroic individual rhetoric** ("our engineer worked all night") — sounds bad, suggests dependency on individual not system

---

## ✅ 加分项

1. **24h initial + 5-day full RCA cadence** explicit
2. **5 elements of 24h comm** (what / when / who / actions / status)
3. **Blameless but specific** principle — process not person
4. **Customer review meeting** format (60 min video, exec sponsors)
5. **Long-term reliability commitments** (quarterly review, joint OKR, shared dashboard)
6. **Action items: specific, owned, dated, trackable, verified**
7. **30-60-90 day status updates**
8. **Regulatory specifics** (HIPAA 60d, GDPR 72h)
9. **Quote BNPL Anthropic + Pakistan ASR + payment proactive**
10. **Trust rebuilding mindset** — postmortem is start of partnership, not end

---

## 一句话总结

> **Customer postmortem ≠ internal — different audience, depth, tone, cadence. Cadence: 24h initial (what/when/who/actions/status) + 5-day full RCA + customer review meeting + 30-60-90 day status + ongoing quarterly review. Tone: blameless but specific (process gap not individual). Long-term reliability commitments: joint OKR, shared SLO dashboard, quarterly review. Trust rebuilding is long-game — prove with consistent action over months. BNPL Anthropic spike postmortem story rebuilt customer trust from threatened cancellation to strongest reference.**

---

## Cheat Sheet

```
5 differences (customer vs internal PM):
  1. AUDIENCE: customer eng/product/exec (not just our eng)
  2. DEPTH: technical but accessible, no internal jargon
  3. TONE: accountable but not self-flagellating
  4. ACTION ITEMS: customer-visible with dates
  5. CADENCE: 24h + 5d + 30/60/90 + quarterly

24-hour initial (5 elements):
  - What happened (technical summary)
  - When (timeline)
  - Who impacted (specific numbers)
  - Our actions (response timeline)
  - What's next (full RCA ETA)

5-day full RCA structure:
  - Executive summary (1 para)
  - Timeline (every event > 1 min)
  - Impact (customer + service + compliance)
  - Root cause (direct + contributing + 5 whys)
  - What went well / poorly
  - Action items (table with owner + date + status)
  - Customer commitments
  - Long-term reliability commitments
  - Appendix (samples, SLA, internal refs)

Tone — blameless but specific:
  BAD: "we'll improve our service"
  BAD: "engineer X made mistake"
  GOOD: "process gap [Y] allowed Z. We'll deploy [fix] by [date]"

Customer review meeting:
  - 60 min video call
  - Exec sponsors both sides
  - Walk through PM doc
  - Q&A (let them vent if angry)
  - Forward-looking discussion
  - Written summary within 24h after

Long-term commitments:
  - Shared SLO dashboard
  - Quarterly reliability review
  - Joint reliability OKR
  - Reliability investment commitment
  - Direct engineering contact
  - Status page subscription
  - Pre-incident comm (planned changes)

Action item requirements:
  - SPECIFIC (not "improve testing")
  - OWNED (specific team/person)
  - DATED (specific date)
  - TRACKABLE (ticket ID, visible)
  - VERIFIED (evidence of completion)

Severity → response:
  CRITICAL: 2 weeks max
  HIGH: 30 days
  MEDIUM: 90 days
  LOW: track but no commitment

Status update template (30/60/90 day):
  - List of action items with status
  - Evidence of completion
  - Next status date
  - Any new issues / learnings

Regulatory specifics:
  HIPAA: 60 days notification
  GDPR: 72 hours notification
  SOX: material weakness if applicable
  SEC Reg SCI: 24h for major
  PCI: 72h investigation

Trust restoration signals (90 days):
  - Engagement with status updates
  - Contract renewal
  - Product expansion
  - Referral / reference
  - Joint OKR agreement

Anti-patterns:
  - Vague language
  - Blame individuals publicly
  - Defensive tone
  - No long-term commitment
  - No review meeting (text-only)
  - Skip 30/60/90 status
  - Hero rhetoric

Case studies:
  - BNPL Anthropic spike: multi-vendor commitment, became strongest customer
  - Pakistan ASR 40-min: regulator handled, pilot continued
  - Payment provider proactive: trust strengthened by transparency

Quotes for interview:
  - "Customer PM ≠ internal — different audience, depth, tone, cadence"
  - "24h initial + 5-day RCA + 30/60/90 status + quarterly review"
  - "Blameless but specific — process gap not individual"
  - "Action items: specific, owned, dated, trackable, verified"
  - "Trust restoration is long-game — months of consistent action"
  - "BNPL Anthropic spike rebuilt customer trust from threatened cancellation"
```
