## Q39 · 客户安全团队拒绝给生产凭证 (你必须解锁)

> "The customer's **security team is refusing to give your deployment team production credentials** to the systems you need to integrate with. You have a **30-min call with the head of their Security & IT team**. Your project is **stalled on this for 2 weeks already**. **Unblock it.**"

**Round**: Client Simulation (30 min)
**出处**: Exponent 2026 FDE · Palantir / OpenAI / Anthropic deployment 必踩
**场景**: Security blocks production credentials. Project stalled. You need to unblock without escalation war.

---

## 这道题在考什么

**不是**: 考你能否 push security to give credentials.

**是**: 考你能否在 30 分钟内**理解 security 实际担心什么** + **propose scope they can approve** + **bring their preferred tools to the table** + **not turn this into a war**.

5 个 signal:

1. **Don't lead with frustration** — "we've been blocked 2 weeks" = win the wrong fight
2. **Diagnose THEIR actual fear** — data exfiltration, audit trail, breach surface, compliance exposure
3. **Offer narrow scope** — read-only, time-bounded, IP-allowlisted, vault-managed
4. **Use THEIR preferred tools** — HashiCorp Vault, Okta, AWS IAM Identity Center, their existing JIT pattern
5. **Give them the win** — they're protecting the company. You're enabling that, not bypassing

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 该说什么 | 开口句 (literal) |
|---|---|---|---|---|
| 1 | **Open: respect their role** | 0:00 - 0:30 | "You're the gate. I'm here to make it easy to say yes." | "James, before I make the ask — I want to acknowledge your team is doing exactly what you're paid to do." |
| 2 | **Diagnose the fear** | 0:30 - 6:00 | What's the actual blocker? | "What's the specific concern? Data exfiltration? Audit trail? Breach blast radius? Compliance posture?" |
| 3 | **Mirror back** | 6:00 - 7:00 | Show you got it | "OK so the 3 concerns are X, Y, Z." |
| 4 | **Reframe ask narrowly** | 7:00 - 12:00 | Read-only, time-bounded, scoped | "Let me re-scope the ask: not full production credentials. Specifically: read-only, X duration, Y IPs, Z roles." |
| 5 | **Bring their tools** | 12:00 - 17:00 | Vault, Okta, JIT, allowlist | "Can we use your existing Vault setup? Your Okta SSO? Your IP allowlist?" |
| 6 | **Audit + monitoring** | 17:00 - 22:00 | How they retain visibility | "Every query logged to your SIEM. Daily report. They monitor, we run." |
| 7 | **Pre-mortem the failure** | 22:00 - 25:00 | What if breach happens | "If breach, here's the blast radius. Here's the kill switch." |
| 8 | **Commit + close** | 25:00 - 30:00 | Specific next step | "By end of week: detailed scope doc. Can we get green light by next Friday?" |

**Total**: 6 min listening, 10 min reframe + tools, 5 min audit, 5 min commit.

---

## 30-second 开场脚本 (Verbatim)

> "James, before I make the ask — **I want to acknowledge your team is doing exactly what you're paid to do**.
>
> A vendor walking in asking for production credentials should get pushback. **I'd be skeptical too**.
>
> So I'm not here to argue around your concerns. I'm here to **understand them**, **re-scope what we're asking for**, **bring tools you already trust**, and **leave the audit trail you need**. Whatever the right answer turns out to be — read-only, time-bounded, JIT-issued, vault-managed — **that's the answer I want to land on with you, together**.
>
> So let me start with a question: **what's the specific concern that's blocked this for 2 weeks?**
>
> Walk me through what your team is worried about. I want to know the real reasons, not the polite-no version."

→ Open with **respect for their role** + **ask what they actually fear**. Don't lead with frustration.

---

## 完整对话流 (15-min back-and-forth)

> **James (Security Head)**: "Honestly, it's three things. **(1)** Your team is going to query our production DB and we don't know what queries you'll run. **(2)** Your credentials would be powerful enough to dump our entire customer table. **(3)** If your team has a breach, our customer data is part of the blast radius. None of those are acceptable."

> **You**: "Got it. Three real concerns: **(a)** scope of what we query, **(b)** power of the credential we'd hold, **(c)** blast radius if we're breached.
>
> Let me re-scope our ask **specifically against each concern**, because I think what we actually need is **much narrower than what we initially asked for**.
>
> **For concern (a) — query scope**:
>
> We need to query **3 specific tables**: `customers`, `transactions`, `support_tickets`. We **don't need** anything else. We don't need write access. We don't need to query customer-PII fields (just IDs).
>
> Proposal: **define a read-only DB role** that's restricted to just these 3 tables. Not `SELECT *` — explicitly allowlist columns. **No raw customer SSN / DL / email** in the role. Just enough for our deployment to work.
>
> **For concern (b) — credential power**:
>
> Instead of static credentials, **JIT-issued via your HashiCorp Vault setup**. Credential valid for **15-minute sessions**. Auto-rotated. No long-lived secrets stored anywhere on our side. **Even if our team leaks a credential, it's dead in 15 minutes.**
>
> **For concern (c) — blast radius**:
>
> All queries from us go through **a specific IP allowlist** (our dedicated subnet, not general internet). **Plus**: every query logged to **your SIEM** in real-time, so your team sees what we're doing. If you don't like a query pattern, **kill switch** — pull the role binding, we lose access in seconds.
>
> **Does this match your tooling**? You use Vault and Splunk, right?"

---

> **James**: "Yes Vault + Splunk. OK that's better. But what about non-prod testing? You're going to need to develop against something."

> **You**: "**Great question.** Two options:
>
> **Option A — Sanitized prod replica**: Your team's already producing a sanitized replica for your QA, right? We use that for development + staging. **Zero production credentials during development**. Production credentials only used during the actual production sync runs.
>
> **Option B — Synthetic data**: If sanitized replica isn't available, we generate synthetic data matching your schema. **Schema only — no real values, no PII.** Slower to set up, but fully isolated.
>
> **My preference**: Option A if your replica exists. Faster, more realistic. **Want to check with your team if your QA replica is suitable for our use case?**"

---

> **James**: "Replica exists. OK so JIT credentials, 15-min sessions, IP allowlist, SIEM logging. What's the audit story I'd take to my CISO?"

> **You**: "**Audit story for CISO**:
>
> 1. **Access scope**: read-only on 3 specific tables, allowlisted columns. **Cannot dump customer table.**
> 2. **Credential lifecycle**: JIT-issued via Vault, 15-min TTL, no static credentials anywhere on vendor side.
> 3. **Identity**: vendor team SSO via your Okta. Named individuals, MFA required. **Can attribute every query to a named person.**
> 4. **Network**: dedicated subnet IP allowlist. **Cannot connect from arbitrary internet.**
> 5. **Logging**: every query streamed to your Splunk + your SIEM. **You see what we query, in real-time.**
> 6. **Alerting**: anomalous query pattern (e.g., full table scan, query outside business hours) triggers your existing security incident response.
> 7. **Kill switch**: you can revoke our role binding in Vault, **our access dies in seconds**. No vendor coordination needed.
> 8. **Quarterly review**: audit log review with your team. **If anything's off, we adjust.**
>
> **The compliance frame**: **least privilege + JIT + audit + revocability**. Hits 4 of the 5 NIST 800-53 access control areas. **Your CISO will recognize this pattern.**
>
> **For your CISO meeting**, I'll send a 1-page diagram showing this. **Want me to draft it for you?**"

→ Help them sell to their CISO. **Hand them a defensible artifact.**

---

> **James**: "What if your team needs to add a 4th table later?"

> **You**: "**Two paths**:
>
> **Path A — Pre-define expansion criteria now**: We agree at signing that **read-only role can be expanded to additional tables with same scope rules** with **your approval per table**, **takes 1 business day** to add via Vault config. No re-negotiation of access pattern.
>
> **Path B — Treat each addition as new ask**: Each new table requires full security review. Slower, but you have more control.
>
> **My recommendation**: Path A with clear scope criteria — '**any additional table must be read-only, must be allowlisted at column level, must include identity + PII columns hashed, must update SIEM logging**'. Pre-defined criteria, so adding doesn't require re-review **as long as it fits**.
>
> **If we ever ask for write access or for PII columns, that's a separate conversation**, not in this scope."

---

> **James**: "OK. What's the rollback if your team has a breach 6 months from now?"

> **You**: "**Walking through the breach scenario**:
>
> **Step 1**: Your SIEM alerts (anomalous query pattern from our subnet OR a query attempted from outside our subnet)
>
> **Step 2**: Your team revokes our Vault role binding. **Access dies within seconds.**
>
> **Step 3**: We have a **24/7 security contact on our side** (I'll give you the name + on-call rotation). Your team can call them immediately.
>
> **Step 4**: **Forensics**: your SIEM has every query we made for the last 6 months. **You can reconstruct exactly what we accessed.** If a specific customer is impacted, you have the data to do customer-care direct contact.
>
> **Step 5**: **Re-issuing access**: only after your team's security review of the incident. No automatic re-grant.
>
> **What you DON'T have to worry about**:
>
> - Credentials sitting on a leaked laptop (no static creds)
> - Vendor team going rogue (revokable in seconds)
> - Mass data dump (column allowlist prevents)
> - Unknown queries (SIEM has every query)
>
> **What's still YOUR responsibility**: SIEM monitoring rules, incident response runbook, vendor security review cadence.
>
> Anything missing in this story?"

---

> **James**: "Looks comprehensive. Send me the 1-pager + the proposed Vault config + the dedicated subnet IP range by Friday. I'll review with my CISO next Monday. If she greenlights, we issue you JIT credentials by Wednesday."

> **You**: "**Done. Specifically**:
>
> **By Friday EOD**:
>
> 1. 1-page audit story for your CISO
> 2. Proposed Vault role config (will share Terraform if you use it)
> 3. Dedicated subnet IP range (our infra team is provisioning this week)
> 4. Splunk integration sample (the queries we plan to log)
>
> **Your action**:
>
> - Review with CISO Monday
> - If approved, issue first JIT credential Wednesday
>
> **Once we have first credential**, my team will run **a synthetic-data smoke test first** (verifying connectivity + logging works) **before any production query**. **Will let you know the timing**.
>
> James — **thank you for spending the 30 minutes here**. **Your team is the reason this rollout will be clean in 12 months**, not the reason it's slow this month. **I'd rather we get this right.**"

→ Close with **genuine appreciation for them protecting the company**. Don't grovel; acknowledge.

---

## Gao Xin 简历专属 reframe

> "I had this exact scenario at TikTok PayLater Indonesia. We needed access to **the production transaction database** for the voice agent to look up customer payment history. The Indonesia InfoSec team had a 6-week hold on issuing credentials.
>
> What worked (and what I'd apply directly here):
>
> 1. **I asked what they were afraid of, not what their policy was**. Turned out their three fears:
>    - **PII exfiltration to ByteDance global** (Indonesia data sovereignty concern)
>    - **Voice agent prompts becoming training data** (data leakage)
>    - **OJK auditing them for unauthorized data movement**
>
> Not 'we don't trust your team'. **Specific compliance + regulatory fears**.
>
> 2. **I re-scoped against each fear**:
>    - **PII fear**: only allowlisted columns, no national ID
>    - **Training data leak fear**: NDA on prompts + audit log showing no training pipeline access to data
>    - **OJK audit fear**: 1-pager methodology doc pre-shared with OJK
>
> 3. **I used their existing tools**: their HashiCorp Vault setup + Okta + Splunk. Didn't introduce any new tool.
>
> 4. **I gave them artifacts to take upward**: 1-page audit story they could share with their CISO + with OJK if asked.
>
> 5. **I respected their role explicitly**. **'You're the reason this is clean in 12 months'** — said in writing on our project kickoff doc.
>
> Outcome: credentials issued in 2 weeks (down from 6-week hold), zero security incidents in 18 months of operation, **security team became a champion for expanding our access to other markets** because we'd done it right.
>
> The pattern that transfers: **'unblock security' isn't about convincing security to give in. It's about understanding the specific fear, re-scoping to match, using their tools, and giving them defensible artifacts for their upward conversations.**"

**Other resume hooks**:

- **Indonesia voice agent partner negotiations** — direct analogy
- **BNPL chatbot data access scoping** — similar PII + audit conversation, different market

---

## 5 个 Follow-ups

**Q1**: "What if James actually has no specific concern, just 'no vendor production access'?"

**A**: Treat as policy that needs internal advocacy. Help him build the business case.

> "OK so it's policy-level, not a specific concern about us. **Let me ask — what would it take to update the policy**?
>
> Usually 3 paths:
>
> **(a) Policy exception**: ask CISO for a one-time exception with the scoped access we just discussed. Document the controls, set quarterly review.
>
> **(b) Policy update**: 'vendor access OK if [scoped + JIT + audited + revocable]'. **More work, but it sets precedent for future vendors**.
>
> **(c) Architecture change**: maybe vendor doesn't need direct access. We could **deploy on your side** — your team runs the inference, our IP is just the code + model. **This removes vendor access entirely**.
>
> Which path is feasible? **I'm flexible — I want to find the path that works for your team's frame, not impose mine.**"

**Q2**: "What if James demands you self-host everything (option (c) above)?"

**A**: Engage seriously. This is sometimes the right answer.

> "OK. Let me think through the tradeoffs:
>
> **Self-host benefits for you**:
> - No vendor production access (your top concern resolved)
> - Data never leaves your perimeter
> - Standard ops model (your team runs everything)
>
> **Self-host costs for you**:
> - You operate the GPU cluster (capacity + scaling)
> - You patch the model + dependencies
> - You handle model upgrades
> - **Your team needs MLOps capacity**
>
> **My honest assessment**: if your team has MLOps capacity (you've deployed ML before), self-host is a great answer. If not, the operational burden is real.
>
> **Want me to do a 1-week assessment of your team's readiness** for self-host? I'll come back with: 'self-host works for these 3 reasons, doesn't for these 2, here's the cost'. **Then you decide informed**."

**Q3**: "What if James says yes verbally but his CISO blocks?"

**A**: Anticipate. Pre-empt with CISO 1:1.

> "Smart to anticipate. **Two moves**:
>
> **(a) Brief CISO directly**: I'd offer a 30-min meeting with your CISO + you + me. **Not to bypass you — but to give CISO the audit story directly so she trusts your judgment when you bring it back**. CISO often blocks because she doesn't have full context.
>
> **(b) Pre-empt CISO's likely concerns**: what does she usually ask? 'Audit story', 'comparable vendor handling', 'compliance posture mapping to [NIST / ISO / SOC2]'? **I'll have all three in the 1-pager**.
>
> **Want me to schedule the 3-way for the week after the 1-pager?**"

**Q4**: "What if the project is genuinely blocked beyond 30 minutes' worth of conversation?"

**A**: Adjust scope realistically.

> "If we don't unblock today, **what's the minimum viable engagement we can run while security review continues**?
>
> Options:
>
> **(a) Demo / POC on sanitized data**: continue development on QA replica, no production data, no credentials needed. Show value, security review continues in parallel.
>
> **(b) Read-only batch export**: nightly batch dump (you control), our team consumes the export. Slower data refresh, but no live credentials.
>
> **(c) Move other workstreams forward**: while credential conversation continues, what else can we ship that doesn't depend on it?
>
> **My recommendation**: option (a) — POC on sanitized data, 2 weeks of work, demonstrates value, **gives security team more time without project being entirely stalled**."

**Q5**: "What if you find out James actually has authority but is being slow because he doesn't like your account team?"

**A**: Diagnose carefully. Don't accuse.

- **First**: ask directly but gently. "James, beyond the technical concerns, is there anything about working with us specifically that I should know about? I'd rather hear it than guess."
- **Possible reasons**: bad past experience with your company, AE personality conflict, internal politics where he's anti-vendor in general
- **If account-specific**: bring it to your director + AE. **Don't try to fix the relationship single-handedly without internal alignment.**
- **If personal**: align on different point of contact from his side. Sometimes change of personnel unblocks.

The goal isn't to "win" with James. It's to remove blockers — sometimes that means changing who interacts with him.

---

## ❌ 死路答法 (top 7)

1. **Lead with frustration** ("we've been blocked 2 weeks") — win the wrong battle
2. **Demand full production credentials** — same ask security already declined
3. **Push back on policy** without understanding why — fight the wrong thing
4. **Refuse to use their tools** — insist on your tooling stack
5. **Skip audit story** — no defensible artifact for CISO
6. **Escalate to CEO** as first move — burns bridges
7. **Refuse self-host as alternative** — show you're flexible, not just trying to extract data

---

## ✅ 加分项 (top 7)

1. **Lead with respect for their role**
2. **Diagnose specific fear** (not policy)
3. **Re-scope narrowly** (read-only, time-bounded, IP-allowlisted)
4. **Use their preferred tools** (Vault, Okta, Splunk)
5. **Hand them audit story for CISO** as 1-pager
6. **Pre-mortem breach scenario** with clear roles
7. **Quote your Indonesia InfoSec experience**

---

## 一句话总结

> **Unblock security on production credentials = "respect their role + diagnose specific fear + narrow re-scope + use their tools + hand them defensible artifact + pre-mortem breach"**.
>
> 真正的 win 不是说服 security to give in, 是**让 security 觉得「这个 vendor 帮我做了我的工作 + 给我审计 story 上 CISO + 给我 kill switch」**. 6 周 hold 变 2 周通过 + security 成 champion 不是反对者.

---

## Cheat Sheet

```
不要说:
  - "We've been blocked 2 weeks"
  - "We need full credentials"
  - "Your policy is too strict"
  - "Just trust us"
  - "Other vendors don't ask this"
  - "I'll escalate to your CEO"
  - "Self-host is too hard for us"

要说:
  - "Your team is doing what you're paid to do"
  - "What's the specific concern?"
  - "Let me re-scope to match your concerns"
  - "Can we use your Vault / Okta / Splunk?"
  - "Here's the audit story for your CISO"
  - "Kill switch: your team revokes in seconds"
  - "Your team is the reason this is clean in 12 months"

8-layer response:
  1. Open respect (0:00-0:30)
  2. Diagnose fear (0:30-6:00)
  3. Mirror back (6:00-7:00)
  4. Re-scope narrowly (7:00-12:00)
  5. Bring their tools (12:00-17:00)
  6. Audit story (17:00-22:00)
  7. Pre-mortem breach (22:00-25:00)
  8. Commit (25:00-30:00)

Their likely fears:
  1. Data exfiltration (PII leak)
  2. Credential power (can dump table)
  3. Blast radius (your breach → their data)
  4. Audit trail (regulator inquiry)
  5. Compliance posture (NIST / SOC2 / ISO mapping)

Re-scope against each:
  Exfiltration → read-only + column allowlist
  Power → JIT 15-min via Vault
  Blast radius → IP allowlist + SIEM
  Audit → every query logged
  Compliance → 1-pager NIST mapping

Their preferred tools (anticipate):
  - HashiCorp Vault (JIT credentials)
  - Okta (SSO + MFA)
  - Splunk / SIEM (audit logging)
  - AWS IAM Identity Center
  - CrowdStrike (endpoint)
  - Use what they already operate

The 8-point audit story:
  1. Access scope: read-only + allowlist
  2. Credential: JIT 15-min via Vault
  3. Identity: Okta SSO + MFA, named individuals
  4. Network: dedicated subnet IP allowlist
  5. Logging: real-time SIEM stream
  6. Alerting: anomaly detection
  7. Kill switch: Vault revoke, seconds
  8. Quarterly review

Pre-mortem breach scenario (5 steps):
  1. SIEM alerts on anomaly
  2. Vault revoke (seconds)
  3. Call our 24/7 security contact
  4. Forensics from SIEM (every query logged)
  5. Re-issue only after review

For development:
  Option A: sanitized QA replica
  Option B: synthetic data
  Never: production credentials for development

Alternative if self-host required:
  Honest tradeoff:
  - Pro: no vendor access
  - Con: operational burden on their team
  Offer: 1-week readiness assessment

When James verbally yes but CISO might block:
  Pre-empt with 3-way 30-min CISO + James + you
  Pre-load 1-pager with CISO-anticipated concerns

When asking adding 4th table later:
  Path A: pre-defined expansion criteria
  Path B: new ask each time
  Recommend A with clear scope rules

Specific commits:
  - 1-pager for CISO (date)
  - Vault config / Terraform
  - IP range
  - Splunk integration sample

Resume quote:
  "TikTok PayLater Indonesia: 6-week hold on
   production DB access. Diagnosed 3 specific fears
   (PII to ByteDance global, training-data leak, OJK
   audit). Re-scoped per fear, used their Vault +
   Splunk + Okta. 2 weeks to unblock. Security
   became champion for other markets. Pattern:
   respect role + diagnose fear + their tools + artifacts."

Close line:
  "James — thank you for spending these 30 minutes.
   Your team is the reason this rollout will be clean
   in 12 months, not the reason it's slow this month.
   I'd rather we get this right."
```
