## 题目（verbatim）

> "Client's **IT team blocks your integration** citing **security concerns**. Navigate the politics, get unblocked, ship the deployment."

**出处**：fde.academy 客户模拟. Enterprise FDE 必经的政治情景.

**Round**：Client Simulation (45 min)

---

## 这道题在考什么

考你**enterprise politics navigation**:

1. **理解 IT 真实诉求** —— security 是表面理由，真问题可能是 NIH / 控制欲 / 担心 layoff
2. **Joint problem solving** —— 跟 IT 站一边对外, 不是 vs IT
3. **Compliance language** —— 你说"我们 secure" → IT 听 "noise"; 你说 "SOC 2 + DPA + per-tenant encryption" → IT 听 "checklist items I can take to my boss"
4. **Phased approach** —— restrictive first, expand on trust

---

## 必问 clarifying questions

**1. What specifically is the concern**

> "Did they say which control they're worried about — data residency, encryption in transit, identity management, audit logging?"

**2. Who specifically**

> "Is it CISO, CISO's deputy, security architect, compliance team? Each has different motivations."

**3. Past pattern**

> "Have they blocked other vendor integrations recently? If so, what got unblocked? What didn't?"

**4. Business sponsor pressure**

> "Is our business sponsor (e.g., VP of Sales whose team needs us) pushing back at IT internally?"

**5. Timing**

> "Hard block (we can't proceed) or soft (delayed pending review)? What's their stated process / timeline?"

---

## IT 真实顾虑的 4 个 layer

| Layer | What they say | What they mean |
|---|---|---|
| **L1 Surface** | "Data leaves our network" | Standard infosec concern, addressable with controls |
| **L2 Control** | "We don't manage your access" | Want oversight, not necessarily veto |
| **L3 NIH** | "We have internal alternative" | They've been building or own competing system |
| **L4 Career** | "Vendor outage = my fault" | Personal risk if you fail |

每层 different remedy. **L1 = checklist; L2 = governance access; L3 = make them ally; L4 = legal & contract guarantees**.

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify which layer + who specifically |
| 5-15 min | **1:1 with IT lead** to understand real concern (not group call) |
| 15-25 min | Propose 3-tier integration (most restricted → expanding) |
| 25-35 min | Compliance / cert / contract checklist |
| 35-45 min | Joint pilot + governance |

---

## Sample script (full role-play)

> *[Setting: I've gotten the message that IT (CISO Maria) blocks our integration. Business sponsor (VP Sales David) is pushing back internally. I request a 1:1 with Maria.]*
>
> "Hi Maria, thanks for taking the time. I want to start by understanding your concerns directly rather than getting them filtered through David.
>
> *[Listen for 5-10 min, don't argue]*
>
> *[Maria: 'You're sending sensitive customer data to your servers. We don't know your infrastructure. And David's team wants to skip our review process.']*
>
> OK, three concerns there:
>
> **1. Sensitive data leaving your network** — that's a legitimate concern. Here's our standard answer:
>    - All data **encrypted at rest with AES-256, per-tenant DEK + customer-controlled KEK**. We can't decrypt without your key.
>    - **TLS 1.3 in transit**, no exceptions
>    - **SOC 2 Type II** + **ISO 27001** certifications, recent audit reports available
>    - **DPA + customer-owned encryption** option — your KMS controls our access
>    - Optional: **private deployment** — we run in your VPC, no data crosses your network
>
> **2. Unknown infrastructure** — fair. Here's what I can offer:
>    - **Technical due diligence package**: architecture diagrams, threat model, pen-test reports
>    - **30-day evaluation** in non-production sandbox, you and your team have full audit access
>    - **Quarterly security reviews** post-deploy
>    - **Hotline access** to our security team
>
> **3. Bypass of your review** — that's something I want to fix, not avoid. **What's your normal vendor security review process?** Let me put us through it formally, not skip it. David's urgency doesn't justify bypassing your process — that creates more risk than it solves.
>
> **What I'd propose: 3-tier rollout**:
>
> **Tier 1 (week 1-2): Sandbox-only pilot**
> - Non-prod data, single use case, restricted access
> - Your team gets full audit visibility
> - You can pull the plug any time
>
> **Tier 2 (week 3-6): Production with limits**
> - Specific use case, single team
> - Customer-controlled encryption keys (Bring-Your-Own-Key)
> - Daily access log to you
>
> **Tier 3 (week 7-12+): Broader rollout**
> - Only with your team's explicit signoff at each stage
> - You define the criteria for expansion
>
> **One thing I want to ask back**: David is pushing because his team has real business needs. **Could we set up a 3-way working session** with you, David, and me to align on what's acceptable timeline given security review? I don't want this to be 'sales vs IT'. I want us to be 'partners against the actual constraints'.
>
> What questions do you have? Or what concerns I haven't addressed?"

---

## 简历专属 reframe

你的 **ByteDance internal cross-org deployment** + **multi-market regulatory engagement**:

| 题 | 你的经验 |
|---|---|
| IT block on security | ByteDance 内部多 region compliance 你必经过 |
| 1:1 with CISO style | 7 markets each has CISO/security lead |
| 3-tier rollout | Indonesia refund tier scoping 同思路 |
| BYOK encryption | Voice agent for regulated banking |
| SOC 2 / ISO 27001 | ByteDance enterprise security stack |

**主动说**:

> "I've done this exact dance for the voice agent in Indonesia — their financial regulator (OJK) had security review pushback. The move that unstuck us: I requested a **1:1 with the OJK compliance lead** to hear the real concern (turns out: a previous foreign vendor had been opaque about data residency). I proposed (a) data-residency-in-Indonesia guarantee, (b) BYOK encryption with their KMS, (c) **3-tier rollout with their veto at each step**. **Took 2 months instead of 2 weeks but we got production approval — and they trusted us afterward**, which paid back 10x over the project lifecycle."

---

## 5 follow-ups

**Q1**: "Sales VP wants to escalate over IT to CIO. Should I support?"
**A**: Almost always **don't**:
- "Escalation wins the battle, loses the war. IT will block harder next time + every time after."
- "Better: I run the security process. If after 30 days I've addressed concerns and still blocked, **then** we talk escalation. Right now we haven't done the work to deserve escalation."
- Coach the sales VP to be patient.

**Q2**: "IT requires 6-month security review. Customer needs deploy in 6 weeks."
**A**: Decompose:
- "Full security review for full feature: 6 months. We respect that."
- "**Sandbox pilot with non-prod data: 2 weeks** through a lighter review (no production data, no production access). Customer can test integration patterns."
- "**Limited production scope** with strict controls: 6 weeks (with your continued review of bigger scope in parallel)."
- 让 IT come up with the smallest reviewable unit.

**Q3**: "IT really doesn't want any 3rd party vendor. NIH attitude."
**A**: Convert NIH to ally:
- "Maria, your team's expertise in [their domain] is something we'd lose if we just dropped a vendor solution. **What if we structured this as a joint platform** — your team owns the data layer, we own the AI layer, you have full visibility and control. We're partners, not vendor-customer."
- This is **building IT's career** not threatening it.

**Q4**: "Pen-test report from us — IT's pen-tester rejects it, wants their own."
**A**: 绝对 yes:
- "Of course. Recommend [reputable firm] or your preferred — we'll pay for the engagement (within reason) and grant whatever access you need."
- "**Their pen-test gives them confidence we can't fake**. It also catches things we'd miss. Win-win."

**Q5**: "Legal team says our standard contract isn't acceptable. Customizations required."
**A**:
- "Legal customizations are normal at enterprise — we have a contract review process. Walk me through what specifically needs to change?"
- Top common: data ownership, liability cap, audit rights, indemnification, source code escrow
- Don't promise but commit to fast-tracking review — **48h response on each request**

---

## ❌ 易错点

1. **Argue with IT in group call** — public loss
2. **Escalate over IT to CIO** — long-term lose
3. **Promise "我们 secure"** without checklist
4. **Skip their process** — bypass = burning bridge
5. **Blame sales VP** to IT — internal disloyalty
6. **NIH attitude 当 obstinacy** — miss ally opportunity
7. **No phased option** — all-or-nothing fails

---

## ✅ 加分项

1. **1:1 first** before group call
2. **4-layer concern model** (Surface/Control/NIH/Career)
3. **BYOK customer-controlled encryption**
4. **SOC 2 + ISO 27001 + DPA** specific
5. **3-tier rollout with IT veto** at each stage
6. **3-way working session** with sales + IT + you
7. **Joint platform framing** for NIH cases
8. **Customer-paid 3rd party pen-test**
9. **Quote Indonesia OJK regulatory experience**

---

## Cheat Sheet

```
IT 4-layer real concern:
  L1 Surface: data leaving network → checklist
  L2 Control: oversight → governance access
  L3 NIH: internal alternative → make ally
  L4 Career: vendor failure = my fault → legal/SLA

5 步 flow:
  1. 1:1 with IT lead first
  2. Listen, no defending
  3. 3-tier rollout with IT veto each stage
  4. Compliance checklist (SOC 2 / ISO / DPA / BYOK)
  5. Joint working session sales + IT + you

Standard checklist:
  - AES-256 at rest, per-tenant DEK + customer KEK
  - TLS 1.3 in transit
  - SOC 2 Type II + ISO 27001
  - DPA + BYOK option
  - Private deployment in their VPC option
  - Quarterly security review
  - 3rd party pen-test (their choice, we pay)

3-tier rollout:
  T1 (2 wk): sandbox, non-prod, audit access
  T2 (4-6 wk): prod with limits, BYOK
  T3 (12 wk): broader, IT signoff each stage

Phrases:
  "I want to understand directly, not filtered"
  "What's your normal process — let's go through it"
  "Joint platform, you own data, we own AI"
  "You can pull the plug any time"

红线:
  - Escalate over IT
  - Skip review process
  - Public group argument
  - Promise without checklist
```
