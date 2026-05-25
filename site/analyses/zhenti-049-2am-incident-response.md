## Q49 · 2 AM incident — show me you've been paged

> "It's 2 AM. PagerDuty wakes you up. **Walk me through the next 30 minutes.** Not generic 'I look at metrics' — show me you've actually been on-call. Be specific: what dashboards, what commands, what comms, how you decide P0 vs P1, when you wake someone up."

**Round**: Production / Reliability (45 min)
**出处**: Exponent 2026 FDE Guide · 公司: OpenAI / Anthropic / Cohere / Scale AI — on-call experience 必问

---

## 这道题在考什么

表面是 IR 题, 底下藏着 **8 个 FDE evaluation signal**:

1. **Real on-call experience** — specifically know what dashboards to open at 2 AM
2. **Triage discipline** — severity classification under sleepy conditions
3. **Mitigate before root cause** — stop bleeding first
4. **Customer comm timing** — when status page, when phone customer
5. **Knowing when to wake teammates** — P0 vs heroics
6. **Blameless culture** — postmortem mindset baked in
7. **Real numbers** — MTTR, MTTA, error budget burn rate
8. **Pakistan ASR 40-min outage** — STAR ready story

不考「incident response 是什么」, 考「2 AM 你 phone 响, 30 秒后你做什么」.

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|---|---|---|
| 1 | **First 60 seconds** | 2 min | What I do literally first | "First 60 seconds: open laptop, ack page, open Slack #incidents, glance at dashboard." |
| 2 | **5-phase IR framework** | 4 min | Detect / triage / mitigate / comm / investigate / resolve / postmortem | "5 phases — detect, triage, mitigate, comm, investigate. 30 min covers detect through mitigate." |
| 3 | **Triage in 5 minutes** | 6 min | Severity scoring, scope, blast radius | "Triage in 5 min — severity (P0/P1/P2), scope (all? subset?), blast radius, customer impact, then announce." |
| 4 | **Mitigate within 15 min** | 6 min | Stop bleeding patterns | "Mitigate before root cause — 5 levers: rollback, circuit breaker, traffic shape, scale, kill switch." |
| 5 | **Customer comm during** | 4 min | Status page, slack, leadership, customer direct | "Comm in parallel with mitigation — status page within 5 min, internal Slack live, customer if >P1." |
| 6 | **When to wake people** | 3 min | P0 yes, P1 maybe, P2 morning | "Wake teammates: P0 always (multiple people, multiple roles). P1 if I'm stuck > 15 min. P2 wait for morning." |
| 7 | **Runbook discipline** | 3 min | Standard runbooks for common incidents | "Every common incident has runbook. New incident → write runbook after postmortem." |
| 8 | **MTTR / MTTA targets** | 3 min | Real numbers | "MTTA target < 5 min (acknowledge), MTTR < 30 min (resolve degradation) / < 1 hour (full resolve)." |
| 9 | **Quote Pakistan ASR + BNPL Anthropic spike** | 4 min | Specific STAR | "Pakistan ASR 2 AM page — drift detected in 3 min, MTTR 12 min via failover." |
| 10 | **Blameless culture** | 2 min | Postmortem mindset | "Always blameless — incidents are system failures, not person failures. Every incident becomes runbook update." |

---

## 详细回答

### Step 1: First 60 seconds (the literal sequence)

```
2:03:00 AM  Phone rings. PagerDuty.
2:03:15 AM  Snooze alarm. Sit up. (Yes, I sleep with laptop in reach.)
2:03:30 AM  Look at PagerDuty:
            - What service?
            - What metric tripped?
            - What threshold? Critical or warning?
            - How many alerts firing? (One = isolated; many = cascade)
2:04:00 AM  Open laptop. VPN.
2:04:30 AM  Acknowledge page in PagerDuty
            (this stops escalation to next on-call)
2:05:00 AM  Open 3 tabs:
            - Slack #incidents
            - Grafana / Datadog primary dashboard for that service
            - Internal incident comm channel
2:05:30 AM  Quick scan:
            - Error rate spike? Latency spike? Throughput drop?
            - Self-healed? (Sometimes alerts fire on transient)
            - Affecting which segments? (One region / one tenant?)
2:06:00 AM  Post in Slack:
            "@here On-call ack'd, investigating ${service} alert"
            (lets team know I'm awake and looking)
```

**Why this sequence**:
- **Acknowledge first** stops escalation to backup on-call (don't wake them too)
- **Slack post early** so anyone else awake can help / observe
- **Glance dashboard before deep-dive** to know if self-healed or active

### Step 2: Triage in 5 minutes

```python
# Mental triage checklist

# Severity scoring (3-axis)
def assess_severity(symptoms):
    user_impact = score_user_impact(symptoms)  # % affected
    severity_type = score_severity_type(symptoms)  # hard fail vs degraded
    business_impact = score_business_impact(symptoms)  # revenue/hour, compliance
    
    if user_impact > 0.5 or severity_type == 'hard_fail' or business_impact > 10000:
        return 'P0'
    elif user_impact > 0.1 or severity_type == 'major_degrad' or business_impact > 1000:
        return 'P1'
    elif user_impact > 0.01:
        return 'P2'
    else:
        return 'P3'
```

**Triage questions (literally what I ask in Slack)**:

```
"Triage update T+5:
- Severity: P1 (would be P0 but only EU region affected)
- Scope: EU region, 30% of EU users
- Symptoms: 503s on /v1/chat/completions, p99 latency 8s (baseline 800ms)
- Started: 1:55 AM UTC (deploy?)
- Recent changes: deploy at 23:30 (might be related)
- Blast radius: ~5000 users active in EU right now
- Self-healing? No, error rate stable at 30%
- Mitigation in progress: investigating rollback option"
```

**Severity ladder (with examples from real incidents)**:

```
P0 (page everyone, all-hands):
  - Service completely down
  - Data loss in progress
  - Security breach
  - Major customer can't use product
  - Regulatory breach (HIPAA, SOX in progress)
  Examples:
  - "All inference returning 503"
  - "Database write replica down, writes failing"
  - "Bug discovered exposing customer PII"

P1 (urgent, single on-call, wake teammates if stuck):
  - Major degradation (>10% users)
  - Single major customer broken
  - SLO breach in progress
  - Latency 5x baseline
  Examples:
  - "EU region 30% error rate"
  - "One enterprise customer's tenant returning 500s"
  - "Latency p99 8s, baseline 800ms"

P2 (investigate within 1 hour):
  - Minor degradation (<10% users)
  - Non-critical service slow
  - Error budget burning faster than SLO
  Examples:
  - "Embedding latency 2x normal"
  - "Some users reporting slowness, < 5% by metric"

P3 (track, fix during work hours):
  - Edge case bug
  - Tech debt manifesting
  - Single-user issue (might not be system fault)
```

### Step 3: Mitigate within 15 minutes

**Principle: Stop bleeding before root cause.**

```
5 mitigation levers (cheapest first):

Lever 1: Roll back recent change (1-5 min)
  - Last deploy in suspicious window? Roll back.
  - Last config change? Revert.
  - Cost: lose forward progress on whatever was deployed
  - Benefit: often fastest fix

Lever 2: Traffic shape (5 min)
  - Reduce concurrency to vendor / downstream
  - Throttle expensive operations
  - Disable non-critical features
  - Cost: capacity reduction
  - Benefit: stops cascading failure

Lever 3: Failover / circuit break (5-10 min)
  - Failover to backup vendor / region
  - Activate circuit breaker on failing dep
  - Serve cached responses
  - Cost: degraded experience
  - Benefit: keeps functional

Lever 4: Scale up (5-15 min)
  - Add capacity (autoscaler trigger / manual)
  - Increase rate limit
  - Cost: $$$
  - Benefit: handles transient load

Lever 5: Kill switch (immediate)
  - Disable feature / service entirely
  - Show maintenance page
  - Cost: bad UX
  - Benefit: prevents worse damage (data loss, security)
```

**Decision matrix**:

```python
def choose_mitigation(severity, root_cause_hypothesis):
    if severity == 'P0':
        # Stop bleeding immediately, even if drastic
        if root_cause_hypothesis == 'recent_deploy':
            return 'rollback'
        elif root_cause_hypothesis == 'vendor_failure':
            return 'failover'
        elif root_cause_hypothesis == 'data_corruption':
            return 'kill_switch'  # prevent further damage
        else:
            return 'traffic_shape + kill_switch'
    
    elif severity == 'P1':
        # Significant mitigation, but try less drastic first
        if root_cause_hypothesis == 'recent_deploy':
            return 'rollback'
        elif root_cause_hypothesis == 'vendor_slow':
            return 'circuit_breaker + cached_fallback'
        elif root_cause_hypothesis == 'load_spike':
            return 'scale_up + traffic_shape'
        else:
            return 'traffic_shape'
    
    elif severity == 'P2':
        # Investigate first, mitigate if needed
        return 'investigate'
```

**Specific mitigation commands (no improvisation under stress)**:

```bash
# Rollback (Kubernetes)
kubectl rollout undo deployment/inference-service -n production
kubectl rollout status deployment/inference-service -n production

# Rollback (specific version)
kubectl set image deployment/inference-service container=inference:v1.4.2 -n production

# Scale up
kubectl scale deployment inference-service --replicas=20 -n production

# Disable feature via config
curl -X POST https://config.internal/api/features/long_context_mode \
  -d '{"enabled": false, "reason": "incident_2026_05_25", "ttl_minutes": 60}'

# Circuit breaker (via runtime config)
curl -X POST https://config.internal/api/circuit/openai_api \
  -d '{"state": "open", "reason": "vendor_latency_spike", "ttl_minutes": 30}'

# Drain traffic from region
aws elbv2 modify-rule --rule-arn $RULE_ARN --conditions '[{"Field":"path-pattern","Values":["/v1/*"]}]' \
  --actions Type=forward,TargetGroupArn=$BACKUP_REGION_TG_ARN

# Kill switch
curl -X POST https://config.internal/api/services/risky-feature/disable

# Database — set read-only
mysql -h $DB_HOST -u admin -e "SET GLOBAL read_only = ON;"
```

**Mitigation report after 15 min**:

```
T+15 Mitigation Update:
- Action: rolled back inference-service to v1.4.2
- Result: error rate 30% → 4% within 3 min
- Latency p99: 8s → 1.2s
- Still elevated baseline 800ms — investigating residual
- Customer-facing: status page updated, "monitoring"
- ETA full recovery: 30 min more
```

### Step 4: Customer communication during

```
3 audiences, 3 channels, different cadence:

1. Internal #incidents (real-time, every 5-10 min)
   - For: on-call team, leadership watching
   - Content: full technical detail
   - Format: "T+15: rolled back to v1.4.2, errors 30%→4%"

2. Status page (public, every 15-30 min)
   - For: customers, users
   - Content: user-facing impact only, no internal jargon
   - Format: "We're investigating elevated errors for some users in EU."
   - Updates: "Issue identified, deploying fix."
   - Updates: "Service restored. Monitoring."

3. Direct customer (phone / Slack / email)
   - For: major customers affected (single tenant impacted)
   - Content: personalized, includes impact estimate
   - Trigger: P0 or specific large customer
```

**Status page progression**:

```
T+5  Initial: "Investigating reports of elevated error rates affecting some users."
T+15 Identified: "We've identified a recent deployment causing the issue. 
                  Rolling back now."
T+30 Mitigating: "Rollback complete. Error rates returning to normal."
T+60 Resolved: "Service fully restored. Postmortem will follow."
```

**Customer phone call template** (for major enterprise customer):

```
"Hi [name], this is Gao Xin from TikTok PayLater on-call.
We've experienced a degradation affecting your tenant starting at 1:55 AM your time.
Symptoms: elevated errors and latency.
We've mitigated via rollback at 2:15 AM. Currently monitoring.
Estimated full recovery: 2:45 AM.
We'll send written incident summary within 24 hours, full postmortem within 5 days.
Anything urgent on your side I can help with?"
```

**Why call vs text**: high-stakes customer feels valued by phone. Text feels cold.

### Step 5: When to wake teammates

```
P0:
  ALWAYS wake:
  - On-call lead (always)
  - Engineering manager
  - VP eng if persisting > 30 min
  - PR / Comms if customer-visible
  - Compliance if regulatory implications
  
  Get on call: 2-3 people minimum

P1:
  WAKE IF:
  - You're stuck after 15 min
  - Need second opinion on mitigation
  - Need specific expert (database, security)
  - Pattern unfamiliar
  
  Don't wake if:
  - You have a mitigation plan
  - It's clearly recoverable
  - Backup on-call also paged

P2:
  Wait for morning unless:
  - Affects major customer
  - Could escalate to P1
  - You need an expert
```

**Don't be a hero**:

```
Anti-pattern: "I'll figure it out alone"
  Risks:
  - Cognitive impairment from sleep deprivation
  - Wrong decision under stress
  - Missing context (other team knows something)
  - Wasted time exploring known issues

Pattern: "Lift the team"
  Benefits:
  - 2 brains see what 1 misses
  - Documented decision-making
  - Faster resolution
  - Doesn't burn out solo
```

### Step 6: Runbook discipline

**Every common incident has a runbook**:

```markdown
# Runbook: Inference service 503 spike

## Symptoms
- Error rate > 5% sustained for 2+ min
- p99 latency > 5x baseline
- Drift dashboard alert

## First Actions (within 5 min)
1. Check status page: https://status.openai.com
2. Check our deploy log: was there a deploy in last 30 min?
3. Check Grafana: which region/endpoint affected?

## Common Causes + Mitigations

### Cause: Vendor outage
- Check: vendor status page, our circuit breaker metrics
- Mitigate: trigger circuit breaker, failover to backup
- Command: `curl -X POST https://config.internal/api/circuit/openai/open`

### Cause: Recent deploy
- Check: deploy log, error correlates with deploy time
- Mitigate: rollback
- Command: `kubectl rollout undo deployment/inference-service`

### Cause: Load spike
- Check: QPS dashboard, autoscaler decisions
- Mitigate: manually scale up, throttle low-priority
- Command: `kubectl scale deployment inference-service --replicas=30`

### Cause: Database degradation
- Check: DB metrics, slow query log
- Mitigate: failover to read replica, kill long-running queries
- Command: `mysql -e "SHOW PROCESSLIST" then "KILL ${id}"`

## Communication
- T+5: First Slack post
- T+5: Status page initial
- T+15: Status page update
- T+30: Status page update or resolved
- T+24h: Internal postmortem doc

## Escalation
- After 15 min stuck: page backup on-call
- After 30 min: page eng manager
- P0: page VP eng

## Last Updated
2026-04-12 by Gao Xin
Incident: pakistan-asr-outage-2026-03-15
```

**Runbook discipline**:
- Every postmortem updates a runbook
- New incident type → write runbook within 1 week
- Quarterly runbook audit (still accurate?)

### Step 7: MTTA / MTTR targets

```
MTTA (Mean Time To Acknowledge):
  - Target: < 5 minutes
  - Industry baseline: 5-10 min
  - Tracked per on-call shift
  - If consistently > 5 min: improve alerting / wake-up SOP

MTTR (Mean Time To Resolve):
  - Mitigation MTTR: < 30 min (degradation stopped)
  - Full MTTR: < 2 hours (fully resolved)
  - Tracked per service per quarter
  - SLO ties: 99.5% uptime → 21.6 min/month budget

Error budget burn rate:
  - 99.5% SLO = 21.6 min/month allowable downtime
  - Burn rate 1x = on track
  - Burn rate 2x = at risk (action item: investigate)
  - Burn rate 5x = will breach SLO this month
  - Burn rate 10x = freeze deploys, all-hands on reliability

P0 incident contributes to SLO breach risk
P1 may or may not (depends on duration + severity)
```

### Step 8: Postmortem culture (blameless)

```
Within 48 hours: postmortem doc draft
Within 1 week: postmortem review meeting

Template:

# Postmortem: [Incident name + date]

## Summary (one paragraph)
What happened in 3 sentences for execs.

## Timeline (every event > 1 min)
00:00 — Event
00:01 — Event
...

## Impact
- Duration: X minutes
- Users affected: Y%
- Revenue impact: $Z
- SLO impact: SLO Q1 down to W%

## Root Cause Analysis (5 whys)
Why did errors spike?  → Deploy introduced bug.
Why was the bug not caught?  → No regression test for this case.
Why was no test? → Edge case not in test suite.
Why missed in QA? → QA focused on happy path.
Why? → QA process doesn't include adversarial cases.

→ Real cause: QA process gap, not "developer made bug"

## What Went Well
- Detection in 3 min via drift dashboard
- Mitigation in 12 min via rollback
- Customer comms timely

## What Went Poorly
- No regression test caught this
- Runbook for this case was outdated
- Postmortem took 8 days (target 5)

## Action Items
- [HIGH] Add regression test for X scenario (Owner: A, Due: 1 week)
- [HIGH] Update runbook (Owner: B, Due: 3 days)
- [MED] Improve QA adversarial test coverage (Owner: C, Due: 1 month)
- [LOW] Investigate alert noise from yesterday (Owner: D, Due: 2 weeks)

## Lessons Learned
- Adversarial QA gap
- Runbook staleness
- (Generalizable insights for org)

## Action Item Tracking
- Tracked in [tool] with status
- Reviewed weekly until all closed
```

**Blameless principles**:
- Focus on **system failures**, not person failures
- "Why was it possible for X to happen?" not "Why did X do this?"
- Mistakes are learning opportunities for the team
- Reward people who flag incidents, not punish

---

## 关键决策 / 框架

### 30-minute timeline (canonical)

```
T+0   Phone rings
T+1   Ack page, snooze alarm
T+3   Laptop open, VPN, Slack
T+5   Triage post: severity + scope
T+8   First dashboard scan, hypothesis
T+10  Choose mitigation lever
T+12  Apply mitigation
T+15  Verify mitigation impact
T+20  Customer comm (status page + internal Slack)
T+25  Wake teammates if needed
T+30  Investigation continues, mitigation holding
```

### Severity → Action matrix

```
P0 → page everyone, mitigate aggressively, customer comm immediate
P1 → solo first, escalate at 15 min stuck, status page in 5 min
P2 → investigate, mitigate if needed, comm if customer-visible
P3 → track, fix during work hours
```

### Mitigation lever cost/benefit

```
Lever        Speed     Reversibility   Cost
Rollback     1-5 min   Easy            Lose forward progress
Traffic shape 5 min    Easy            Capacity reduction
Failover     5-10 min  Medium          Degraded experience
Scale up     5-15 min  Easy            $$$
Kill switch  Immediate Easy            Bad UX
```

---

## 完整代码 / 架构图

### On-call dashboard checklist

```python
# I open these tabs in order, every page:

DASHBOARDS = [
    # 1. Service health (am I burning error budget?)
    ('Grafana', 'https://grafana.internal/d/service-health'),
    
    # 2. Per-region status
    ('Grafana', 'https://grafana.internal/d/by-region'),
    
    # 3. Deploy log (recent changes?)
    ('Deploy log', 'https://argo.internal/deploys?service=inference'),
    
    # 4. Vendor status
    ('Status pages', [
        'https://status.openai.com',
        'https://status.anthropic.com',
        'https://status.aws.amazon.com',
    ]),
    
    # 5. Slack channels
    ('Slack', [
        '#incidents-current',
        '#oncall-handoff',  # context from previous shift
        '#alerts-firing',   # raw alerts
    ]),
    
    # 6. Customer-facing status page (am I lying to customers?)
    ('Public status', 'https://status.tiktok-pay.com'),
]
```

### Resilience patterns inventory

```python
# All these should be pre-built, deployed, tested before they're needed

class IncidentResponseToolkit:
    """Everything I need at 2 AM, pre-built and tested."""
    
    def __init__(self):
        self.runbooks = load_runbooks()
        self.feature_flags = FeatureFlagClient()
        self.circuit_breakers = CircuitBreakerClient()
        self.k8s = KubernetesClient()
        self.alerts = AlertManager()
        self.status_page = StatusPageClient()
    
    async def rollback_service(self, service_name, target_version=None):
        """One-liner rollback with audit."""
        if target_version:
            await self.k8s.set_image(service_name, target_version)
        else:
            await self.k8s.rollout_undo(service_name)
        await self.alerts.log_incident_action(
            action='rollback',
            service=service_name,
            target=target_version or 'previous'
        )
    
    async def trigger_circuit_breaker(self, dependency, reason, ttl_minutes=30):
        """Open circuit breaker, log action."""
        await self.circuit_breakers.open(dependency, reason, ttl_minutes)
        await self.alerts.log_incident_action(
            action='circuit_break',
            dependency=dependency,
            reason=reason
        )
    
    async def failover_region(self, from_region, to_region):
        """Drain traffic from one region."""
        await self.k8s.update_loadbalancer(from_region, weight=0)
        await self.k8s.update_loadbalancer(to_region, weight=100)
    
    async def kill_switch(self, feature_name, reason):
        """Disable a feature immediately."""
        await self.feature_flags.set(feature_name, enabled=False, reason=reason)
    
    async def post_status_update(self, severity, message, eta=None):
        """Update public status page."""
        await self.status_page.create_incident(
            severity=severity,
            message=message,
            eta=eta,
        )
    
    async def page_teammates(self, severity, message, who):
        """Wake people up."""
        await self.alerts.page(
            severity=severity,
            message=message,
            recipients=who
        )
```

### Architecture: incident response observability

```
                   ┌─────────────────────────────────┐
                   │   Production System             │
                   │   (LLM service, RAG, agents)    │
                   └────────────────┬────────────────┘
                                    │
                          ┌─────────┴─────────┐
                          │                   │
                          ▼                   ▼
              ┌──────────────────┐  ┌──────────────────┐
              │  Metrics         │  │  Logs (centralized)│
              │  (Prometheus)    │  │  (Elastic / Loki) │
              └────────┬─────────┘  └──────────┬───────┘
                       │                       │
                       ▼                       ▼
              ┌──────────────────────────────────────┐
              │  Dashboards (Grafana / Datadog)      │
              │  - Service health                    │
              │  - Per-region                        │
              │  - Per-tenant                        │
              │  - Drift / quality                   │
              │  - Business metrics                  │
              └────────────────┬─────────────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │  Alert Manager           │
                  │  - SLO-based alerts      │
                  │  - Burn rate alerts      │
                  │  - Per-component alerts  │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │  PagerDuty / Opsgenie    │
                  │  - On-call schedule      │
                  │  - Escalation policy     │
                  │  - Acknowledgment        │
                  └────────────┬─────────────┘
                               │
                               ▼
                       [Sleepy on-call]
                               │
                               ▼
                  ┌──────────────────────────┐
                  │  Incident Response       │
                  │  - Runbooks              │
                  │  - Toolkit (rollback,    │
                  │    circuit breaker, etc) │
                  │  - Status page           │
                  │  - Slack #incidents      │
                  └──────────────────────────┘
```

---

## Gao Xin 简历专属 reframe

### Pakistan ASR 40-minute outage (PRIMARY 2 AM STAR)

**S** (Situation):
> "March 15, 2026, 2:14 AM Singapore time (which is 11:14 PM Pakistan time). Voice agent in Pakistan, peak hours for our debt collection (people answer phones in evening). Third-party ASR API (audio → text) starts showing 30-second timeouts. Approximately 40% of calls affected over 5-minute window."

**T** (Task):
> "Triage, mitigate, restore service. Constraints:
> - Regulator-watched pilot — can't have outage publicized
> - Other 6 markets unaffected — don't break them
> - MTTR target < 15 min for P1
> - I'm primary on-call, backup is in San Francisco (just got off work)"

**A** (Action with concrete timestamps):

```
2:14:00 AM  Phone rings (PagerDuty: ASR confidence drop)
2:14:30 AM  Ack page, lap top open
2:15:00 AM  Slack post: "On-call ack'd, investigating ASR alert Pakistan"
2:16:00 AM  Triage:
            - Severity: P1 (Pakistan-only, but high impact)
            - Scope: Pakistan region only (verified via per-region dashboard)
            - Symptoms: 40% calls failing transcription, 30s timeouts
            - Started: 2:09 AM (5 min before alert — detection lag we'll fix)
            - Recent changes: no deploy on our side past 4 hours
2:18:00 AM  Hypothesis: vendor ASR issue in Pakistan POP
            - Status page: no incident yet (vendors slow to update)
            - Cross-check: Down Detector shows some reports
2:20:00 AM  Mitigation decision: failover to backup ASR vendor
            - Pre-configured backup vendor for this exact case
            - Manual trigger (planning to automate post-incident)
            
2:21:00 AM  Failover command:
            curl -X POST config/api/asr/primary -d '{"vendor": "backup", "reason": "pakistan_outage"}'
            
2:22:00 AM  Verification: error rate 40% → 8% within 1 min (some in-flight)
2:24:00 AM  Verification: error rate 8% → 0% (all in-flight rotated)
            Latency 1.5x normal (backup vendor higher latency, acceptable)
2:25:00 AM  Slack update:
            "T+11: Failed over to backup ASR vendor.
             Error rate 40% → 0%. Latency 1.5x normal.
             Investigating primary vendor."
2:27:00 AM  Vendor escalation:
            Email to ASR vendor support with:
            - Request_ids from failed transcriptions
            - Time window
            - Pakistan POP affected
            - Business impact (regulator-watched pilot)
2:30:00 AM  Customer-facing: Pakistan ops team Slack notified
            (no public status page because no user-visible impact)
2:35:00 AM  Vendor responded: "Investigating Pakistan POP routing issue"
2:50:00 AM  Vendor confirmed mitigation deployed
2:55:00 AM  Tested primary vendor: low error rate
2:57:00 AM  Failed back to primary, monitoring
2:59:00 AM  Verification: stable, latency normal
3:00:00 AM  Slack: "Incident resolved. Full timeline + AI in postmortem."
3:30:00 AM  Postmortem draft started
4:00:00 AM  Back to sleep
```

**R** (Result with concrete numbers):

- **MTTR (degradation stopped)**: 12 minutes (target was 15)
- **MTTR (full resolution)**: 43 minutes
- **0 user-facing calls failed** (failover absorbed)
- **Regulator unaware** (no public-visible outage)
- **Cost**: backup vendor 1.5x cost for 43 min = ~$300
- **vs estimated**: $50k revenue impact + pilot suspension if no failover

**Postmortem action items** (implemented):
1. **Automated failover on circuit breaker** (was manual)
2. **Lower detection threshold** — 5% → 3% (would have caught 2 min earlier)
3. **Multi-vendor for ALL markets** (was only Pakistan pre-configured)
4. **Vendor SLA enforcement** — MTTR clause added at renewal
5. **Status page automation** on circuit breaker open (for future user-visible cases)

### BNPL Anthropic latency spike (secondary STAR)

**S**: 2026 February, Anthropic API latency spike (regional, US-East). Affected BNPL chatbot during Asia peak hours.

**T**: Detect, mitigate without user-facing failure.

**A**:
- Drift on response_latency_p99 caught in 2 min
- Mitigation: cached fallback for high-similarity queries (acceptable quality)
- Escalated to Anthropic Enterprise with request_ids
- Anthropic confirmed regional issue, resolved in 25 min

**R**: 30% of requests hit cached fallback during outage (acceptable quality), 0 user-facing errors.

### TikTok PayLater payment provider intermittent failure (third STAR)

**S**: Payment provider intermittent 5xx errors (1-3% rate).

**T**: Don't drop transactions, don't double-charge.

**A**:
- Idempotency key on all transactions (preexisting)
- Retry with exponential backoff + jitter
- After 3 retries, queue for async processing
- Customer notified "processing" + later confirmation

**R**: 0 lost transactions, 0 double-charges, ~50ms p99 latency increase.

---

## 5 个 Follow-ups

**Q1**: "What if you can't immediately determine root cause?"

**A**: Mitigate anyway. Real principles:
1. **Stop bleeding first** — most mitigations are reversible (rollback, circuit breaker, traffic shape)
2. **Hypothesis-driven investigation** — pick 2-3 likely causes, validate or rule out
3. **Don't be paralyzed by uncertainty** — apply safest mitigation (e.g., rollback to known-good)
4. **Time-box investigation** — if not closer to root cause after 30 min, wake teammate
5. **Document hypotheses** in Slack — let team see your reasoning

**Q2**: "How do you handle on-call burnout?"

**A**:
- **Rotation discipline**: max 7 days on-call per month per person
- **Backup on-call**: 2-person rotation minimum
- **Page reduction**: every page audited weekly — was it actionable? noise reduced.
- **Runbooks** reduce cognitive load (don't think under stress, follow procedure)
- **Postmortem fixes** prevent recurrence (same incident shouldn't happen twice)
- **Compensation**: on-call differential pay ($5-10k/month extra)
- **Recovery time**: half-day off after major P0 incident

**Q3**: "Communication during incident — what's the right cadence?"

**A**:
- **Internal Slack**: every 5-10 min, real-time updates
- **Status page**: 5 min for initial, every 15-30 min until resolved
- **Stakeholders**: 15 min initial, hourly during incident
- **Customer (direct)**: phone for major customers, email for others, within 30 min for P0

**Cadence rule**: communicate proactively, even when "nothing new" — silence creates anxiety.

**Q4**: "When do you call it 'resolved'?"

**A**: 4 criteria:
1. **Metrics back to baseline** for at least 15 min sustained
2. **No new alerts firing**
3. **Customer-visible impact confirmed restored** (sample customer queries succeed)
4. **Team consensus** — not just on-call's call

**Pattern**: "Resolved" doesn't mean "done." Postmortem starts. Watch for 24 hours for recurrence. Some incidents have "long tail" — don't celebrate too early.

**Q5**: "What's the most important thing for someone new to on-call?"

**A**: 3 things:
1. **Read every existing runbook** before first shift. Don't improvise under stress.
2. **Shadow experienced on-call** for 2-3 incidents before primary. Learn the patterns.
3. **Ask for help early** — heroism is a bad habit. Wake teammates at 15 min stuck, not 30.

Plus: **practice incident drills**. We do quarterly "wheel of misfortune" — random incident scenario, on-call practices response with team observing. Catches process gaps before real incidents.

---

## ❌ 死路答法

1. **"I check the metrics"** — too vague, no specifics
2. **No severity classification** — P0 vs P1 vs P2 matters for response
3. **Investigate before mitigate** — keeps users impacted longer
4. **No customer comm during** — silent outage is worse than communicated
5. **Heroic solo approach** — burns out, slower resolution
6. **No runbook reference** — improvising under stress is error-prone
7. **No specific dashboards / commands** — shows lack of real on-call
8. **No MTTA / MTTR numbers** — shows no operational measurement
9. **Blame individual** — incidents are system failures
10. **No postmortem follow-through** — same incident recurs

---

## ✅ 加分项

1. **Literal 60-second sequence** (ack page, Slack post, dashboards)
2. **3-axis severity scoring** (user impact + severity + business)
3. **5 mitigation levers** with cost/benefit
4. **Specific commands** (kubectl rollout, curl config API)
5. **Customer comm cadence** (Slack 5-10 min, status page 15-30, customer 30)
6. **Wake teammates rules** (P0 always, P1 if stuck 15 min)
7. **MTTA < 5 min, MTTR < 30 min targets**
8. **Error budget burn rate awareness**
9. **Blameless postmortem culture**
10. **Quote Pakistan ASR with timestamp-level detail** — credible STAR

---

## 一句话总结

> **2 AM incident response: ack page in 60 sec, triage in 5 min (severity + scope), mitigate before root cause within 15 min (rollback / circuit break / failover / scale / kill switch), comm in parallel (status page + Slack + customer if P0), wake teammates when stuck > 15 min, MTTR target < 30 min for degradation, blameless postmortem within 1 week. Pakistan ASR 40-min outage with MTTR 12 min is the gold-standard STAR.**

---

## Cheat Sheet

```
First 60 seconds:
  - Phone rings → ack page (stops escalation)
  - Laptop open → VPN
  - Slack #incidents post: "On-call ack'd, investigating"
  - 3 dashboards: service health, deploy log, vendor status

Triage in 5 min:
  - Severity (3-axis): user impact + severity + business
  - Scope: all/subset/single tenant?
  - Blast radius
  - Acknowledge to team

Severity ladder:
  P0: >50% users / hard fail / >$10k/hour / regulatory
  P1: 10-50% users / major degrad / $1-10k/hour
  P2: <10% users / minor / <$1k/hour
  P3: edge cases / tech debt

5 mitigation levers (cheapest first):
  1. Rollback (1-5 min, reversible)
  2. Traffic shape (5 min, capacity drop)
  3. Failover / circuit break (5-10 min, degraded)
  4. Scale up (5-15 min, $$$)
  5. Kill switch (immediate, bad UX)

Mitigation by hypothesis:
  Recent deploy → rollback
  Vendor issue → failover or circuit break
  Load spike → scale + shape
  Data corruption → kill switch
  Unknown → traffic shape (safer)

Communication (3 audiences):
  Internal #incidents: every 5-10 min, full detail
  Status page: 5 min initial, 15-30 min updates
  Customers (direct): phone for P0, within 30 min

Wake teammates:
  P0 always (multiple roles)
  P1 if stuck 15 min, expert needed
  P2 wait for morning unless escalating

MTTA / MTTR targets:
  MTTA: < 5 min
  MTTR (mitigation): < 30 min
  MTTR (full): < 2 hours
  Error budget: 99.5% SLO = 21.6 min/month

Runbook discipline:
  Common incident has runbook
  Every postmortem updates runbook
  Quarterly runbook audit

Postmortem (within 1 week):
  Timeline, impact, root cause (5 whys)
  What went well/poorly
  Action items + owners + dates
  Blameless: system not person

Specific commands:
  Rollback: kubectl rollout undo deployment/X
  Scale: kubectl scale deployment X --replicas=N
  Circuit break: curl -X POST config/circuit/Y/open
  Disable feature: curl -X POST config/features/Z/disable
  Drain region: aws elbv2 modify-rule

Dashboard checklist (open every page):
  1. Grafana service health
  2. Per-region
  3. Deploy log
  4. Vendor status pages
  5. Slack #incidents
  6. Public status page

Toolkit pre-built:
  - Rollback automation
  - Circuit breaker control
  - Feature flag service
  - Region drain
  - Kill switch UI
  - Status page API
  - Page teammates

Anti-patterns:
  - Vague "I check metrics"
  - No severity classification
  - Investigate before mitigate
  - Silent outage (no comm)
  - Heroic solo approach
  - No runbook follow
  - Blame individual

Case studies:
  - Pakistan ASR 2 AM: MTTR 12 min, 0 failed calls
  - BNPL Anthropic spike: 30% cached fallback, 0 errors
  - Payment 5xx: idempotency + queue, 0 lost

Quotes for interview:
  - "Ack page in 60 sec, triage in 5 min, mitigate in 15"
  - "Stop bleeding before root cause"
  - "Heroism is anti-pattern — wake teammates at 15 min stuck"
  - "Every postmortem becomes runbook update"
  - "Blameless culture — system not person"
  - "Pakistan ASR: MTTR 12 min, 0 failed calls"
```
