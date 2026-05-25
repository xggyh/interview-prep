## Q40 · 你不认同客户的架构选择 (如何提出反对)

> "You're 4 weeks into a deployment. The customer's Lead Architect has chosen a specific **architecture** (let's say: **microservices + Kafka + on-prem K8s** for what could be a simple monolith + Postgres + AWS managed service). **You believe it's the wrong choice for their actual needs and timeline.** **You're on a 30-min call with the Lead Architect. Tell them.**"

**Round**: Client Simulation (30 min)
**出处**: Exponent 2026 FDE · Palantir / OpenAI Enterprise · 经典必踩
**场景**: 客户 Lead Architect 已经做了架构决定. 你认为错了. 你必须 disagree 但又不羞辱他们.

---

## 这道题在考什么

**不是**: 考你能否解释你的架构 superior.

**是**: 考你能否 **disagree without being a jerk + lead with what they got right + frame as collaborative pre-mortem + respect their context you don't fully know + offer reversibility plan**.

5 个 signal:

1. **Don't open with "I disagree"** — burn bridge. **Open with "what they're right about"**
2. **Pre-mortem framing** — "have you considered…" not "you're wrong"
3. **Acknowledge what you don't know** — they have context you don't (regulatory, org chart, past projects)
4. **Frame as their decision, not yours** — they're the architect, you're the FDE. **Their org, their call**
5. **Offer reversibility plan** — "if 6 months from now this doesn't work, here's the migration path"

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 该说什么 | 开口句 (literal) |
|---|---|---|---|---|
| 1 | **Open: ask context** | 0:00 - 2:00 | "Tell me how you arrived at this" | "Priya, before I share where I see it differently — walk me through how you and your team arrived at this architecture." |
| 2 | **Active listen** | 2:00 - 8:00 | They explain reasoning | (Take notes, ask 1-2 clarifying questions) |
| 3 | **Reflect + acknowledge** | 8:00 - 10:00 | What you respect about the decision | "OK so 3 things you got right: X, Y, Z. I see where this is coming from." |
| 4 | **Frame your concern as Q** | 10:00 - 14:00 | "Have you considered..." | "Three things I want to check with you, because if there's a gap, I'd rather flag now than 6 months in." |
| 5 | **Specific concerns** | 14:00 - 20:00 | Concrete, 2-3 not 10 | "Concern 1: ... Concern 2: ... Concern 3: ..." |
| 6 | **Alternative as option** | 20:00 - 24:00 | Not "do this instead", show option | "An alternative I'd consider: simpler stack first, migrate later if scale demands. Here's the tradeoff..." |
| 7 | **Reversibility plan** | 24:00 - 27:00 | If current path doesn't work | "If 6 months in this doesn't pan out, here's the migration path. Lock-in is real but not absolute." |
| 8 | **Defer to their decision** | 27:00 - 30:00 | Their call, you support | "You know your org better than I do. Whichever you decide, I'll ship it well." |

**Total**: 6 min listen, 10 min reflect + concerns, 10 min alternative + commit.

**Key**: **They're the architect. Their call. Your job is to surface, not impose.**

---

## 30-second 开场脚本 (Verbatim)

> "Priya, before I share where I see things differently — and I want to do that honestly because I think it's important — **I want you to walk me through how you and your team arrived at this architecture**.
>
> I've been on this 4 weeks. You and your team have been thinking about it longer. There's context you have — about your org, your past projects, your platform constraints, your team's skills — that I haven't fully absorbed.
>
> **I might be wrong about what I'm about to raise.** And even if I'm right on some things, **you might have already evaluated them and decided this was still the right path**.
>
> So — walk me through the reasoning. What problems is this architecture solving for you? What alternatives did you evaluate? What's the team's familiarity with the stack? **I want to understand before I push back.**"

→ Open with **humility + curiosity + recognition of their longer context**. Don't open with your disagreement.

---

## 完整对话流 (15-min back-and-forth)

> **Priya (Lead Architect)**: "We chose microservices + Kafka + on-prem K8s for three reasons. First, we already have a Kafka cluster for other workloads, so reusing that infra is cheaper than standing up a new managed service. Second, our platform team has K8s expertise, so on-prem matches our skillset. Third, we're expecting 10x scale in 18 months — monolith would be a rewrite later, microservices position us better. Also, our InfoSec team prefers on-prem over AWS for regulated data."

> **You**: "OK. Three solid reasons:
>
> 1. **Reuse existing Kafka infrastructure** (cost + ops efficiency)
> 2. **Match team's K8s expertise** (don't introduce new technology)
> 3. **Future-proof for 10x scale** (avoid rewrite)
> 4. Plus InfoSec preference for on-prem (regulated data)
>
> Those are all real. **None of them is wrong**.
>
> Three things I want to check with you — because if there's a gap, I'd rather flag now than 6 months in.
>
> **Concern 1 — Initial complexity vs current scale**:
>
> Today's traffic is ~50 TPS based on the volumes you shared. Microservices + Kafka + K8s deployment is ~6 services for v1. For 50 TPS, **a monolith + Postgres + a worker queue could ship in 4 weeks. Microservices + Kafka takes ~12-16 weeks** — and most of that complexity is paying for scale you don't have yet.
>
> **Question**: are we sure about 10x in 18 months? If yes — I see it. If 'maybe', the complexity now might lock you into ops burden that doesn't pay off.
>
> **Concern 2 — On-prem K8s ops burden**:
>
> 6 services on K8s means 6 deployment pipelines, 6 sets of alerts, 6 sets of dependency upgrades. Your platform team has K8s expertise — but **for 6 microservices, that's significant ops time**. **How much of your platform team's monthly bandwidth would this consume**?
>
> **Question**: if it's 30%+ of your platform team's time on ops, is that the highest-value use of that capacity?
>
> **Concern 3 — InfoSec on-prem preference vs managed service compliance**:
>
> AWS managed services like RDS / MSK actually have **stronger compliance certifications** than most on-prem setups (SOC2, FedRAMP, HIPAA), and they handle patching + backup + DR automatically. **Has your InfoSec team explicitly evaluated AWS managed services, or is on-prem preference based on assumption?**
>
> Often InfoSec preference is from 5 years ago when AWS managed services weren't as mature. Worth re-checking.
>
> **Help me understand each of these — I might be missing context.**"

→ **Three concerns framed as questions**, not statements. Each one ends "help me understand".

---

> **Priya**: "On scale — we're being told to plan for 10x by Q1 2027. On platform bandwidth — yeah, it's significant, maybe 40% of one team's quarter. On InfoSec — they did a review 2 years ago, on-prem was the conclusion. Are you saying we should re-evaluate?"

> **You**: "**Not 'should' — that's your call.** But let me share what I'd consider:
>
> **On the 10x scale**: 10x of 50 TPS is 500 TPS. **Postgres + a worker queue handles 500 TPS comfortably** if the workload is similar to today. **Kafka + microservices** make sense at **5000+ TPS** typically. **You might not need microservices for the 10x target.**
>
> Unless the 10x is also accompanied by **fundamental shape change** (new modes, new data types, different latency targets), monolith scales well into the 1000s of TPS with appropriate read replicas and partitioning.
>
> **On the 40% platform bandwidth**: that's a huge cost. 40% of 4 engineers = 1.6 engineers indefinitely on ops. If we ship monolith + managed services, that 1.6 engineers do features instead. **Over 18 months, that's ~24 engineer-months of feature work**.
>
> **On the InfoSec 2-year-old review**: I'd ask them to re-evaluate. AWS managed services have changed a lot. The decision should be made on current capability, not 2-year-old context. **If they re-evaluate and still prefer on-prem, that's a valid answer**. But the review's worth doing.
>
> **An alternative I'd consider**:
>
> **Phase 1 (now)**: Monolith + Postgres + managed worker queue (SQS / managed Kafka). Ship in 4 weeks. Handle 50 TPS easily, scale to 500 TPS.
>
> **Phase 2 (when scale demands)**: If 5000+ TPS materializes, then extract the hot services into microservices. **Migrating monolith → microservices is well-tooled and predictable**. Not zero cost, but **deferring complexity until you need it**.
>
> **What I'm not arguing**: that microservices are wrong. **They're right for 5000+ TPS systems**. I'm arguing that **the complexity is paid for the future, not for today, and you can defer that payment**.
>
> **But — your call. You have context I don't.**"

→ Specific concerns + alternative offered. **Then immediately re-assert their authority**.

---

> **Priya**: "OK that's a legitimate point on the deferred-complexity angle. But if we go monolith + managed and 6 months in we need microservices, that migration is painful."

> **You**: "**Yes, migration has cost.** Let me put a number on it.
>
> **Monolith → microservices migration in our pattern**:
>
> - **Extract first service**: 4-6 weeks
> - **Extract subsequent**: 2-3 weeks each
> - **Total for 6 services**: ~3-4 months
>
> **Compare to building microservices day 1**: 12-16 weeks now + 1.6 engineers ongoing ops.
>
> **Math**:
>
> - **Monolith now**: 4 weeks build + 4 months future migration (if needed) = 5 months
> - **Microservices now**: 16 weeks build + ongoing ops = 4 months upfront, 0 saved
>
> If migration probability is 100% (you definitely will need microservices): roughly same total cost.
>
> If migration probability is 60%: monolith saves 1.6 months of upfront work + ongoing ops.
>
> If migration probability is 30%: monolith saves 4 months + ongoing ops cost forever.
>
> **The question is: what's the probability you actually hit 5000+ TPS in 18 months that requires microservices**?
>
> **Reversibility plan**: if we go monolith and hit scale, **I commit to writing the migration plan now**, so when you need it, the path is known. No surprise architectural rewrite — pre-planned extraction sequence.
>
> **Want me to write the migration plan as part of this engagement**, so you have it in the drawer for when (or if) you need it?"

→ Quantify migration cost. **Offer to write the contingency plan upfront**. Reduces fear of "what if monolith fails".

---

> **Priya**: "OK that's compelling. Let me bring this to my team. What's your recommendation specifically?"

> **You**: "**My recommendation**:
>
> 1. **Get InfoSec re-evaluation on managed services**: 1 week. If they still say on-prem, that constrains the answer.
>
> 2. **Pressure-test the 10x assumption with your business team**: is it really 10x at 500 TPS, or 10x at 5000+ TPS? Make sure you have shape clarity.
>
> 3. **If InfoSec OK with managed services + scale target is 500 TPS-ish**: monolith + Postgres + SQS for v1. Migrate to microservices if and when scale actually demands.
>
> 4. **If InfoSec mandates on-prem or scale is genuinely 5000+ TPS**: stick with your current architecture, but **I'd argue for fewer microservices to start** — maybe 2-3 services instead of 6. Easier ops, can split further later.
>
> **What I'm not doing**: telling you my architecture is right and yours is wrong. **You know your business, your team, your past projects, your political context better than I do**. **Whichever you and your team decide**, my job is to ship it well.
>
> **What I am doing**: making sure you have the info to make the decision with full picture. **If you've already considered all 3 of my concerns and the answer is still microservices on-prem, that's a fine answer — I just want to make sure we evaluated together**.
>
> **What I need from you**:
>
> 1. **By next Tuesday**: decision on InfoSec re-evaluation (yes/no)
> 2. **By next Friday**: confirmation of scale target (500 TPS or 5000+)
> 3. **By following Tuesday**: final architectural decision
>
> I'll wait. **Whatever you and your team decide, we'll execute on it well**."

---

> **Priya**: "OK. I'll loop in my team this week. Thanks for raising this honestly."

> **You**: "**Thank you for the openness to revisit it 4 weeks in.** That's not always easy — once architecture is decided, momentum is real. The fact that your team can re-evaluate without ego is a sign you'll build something good regardless of which path you choose.
>
> **One more thing**: even if you decide to stay with microservices on-prem after re-evaluation, **I'll have learned a lot from this conversation**. I'd rather we have it than I sit silently and ship something I worry about. **So thank you for the conversation.**"

→ Close with **genuine appreciation for their willingness to engage**. Show you respect them more, not less, after the disagreement.

---

## Gao Xin 简历专属 reframe

> "I had this exact pattern at TikTok PayLater. The Brazil team chose **Apache Pulsar + Kubernetes on bare-metal** for the voice agent's message queue + agent orchestration. **I disagreed** — I thought it was over-engineered for Brazil's traffic profile, and the team's familiarity with Pulsar was thin.
>
> What worked (and what I'd apply directly here):
>
> 1. **I asked them to walk me through their reasoning first**. Turned out their answer was: 'Pulsar handles the multi-tenancy better than Kafka, and our regional team has Pulsar expertise from a past project'. **The Pulsar expertise was a strong point I hadn't appreciated**. Made me update my view immediately.
>
> 2. **I acknowledged what they got right** publicly. In the meeting, I said: 'The multi-tenancy advantage is real, and your team's expertise is the strongest argument'. Then I raised my 2 remaining concerns.
>
> 3. **I framed concerns as questions, not statements**. 'Have you considered the bare-metal ops burden vs your team's capacity?' Not 'bare metal will kill your team's velocity'.
>
> 4. **I offered an alternative + cost-quantified migration plan**. 'Phase 1 RabbitMQ on managed service, Phase 2 Pulsar if multi-tenancy becomes needed'. With specific migration timeline.
>
> 5. **I deferred to their decision and committed to ship well either way**.
>
> Outcome: they re-evaluated, ended up with a **hybrid** — Pulsar for the multi-tenant aspects, managed RabbitMQ for the high-volume single-tenant path. **Took 2 weeks, but the architecture was better for it**. They later said 'thank you for not just saying yes to our first choice'.
>
> The pattern that transfers directly: **'disagree well' means making them feel respected, surfacing concerns as questions, offering alternatives + reversibility plans, and deferring to their authority. The opposite — 'I think you're wrong because [reasons]' — burns trust even when you're correct.**"

**Other resume hooks**:

- **Internal Agent Platform multi-team architecture debates** — frequent disagreement on per-team architecture choices. Same template applied.
- **ConvFinQA methodology disagreements** with research team — same pattern of "ask context first, then concerns as questions".

---

## 5 个 Follow-ups

**Q1**: "What if Priya is offended and pushes back hard?"

**A**: Don't escalate emotionally. Diagnose her actual concern.

> "Priya, I hear that this feels like I'm second-guessing the team's decision. **That's not my intent**. Two things:
>
> **(a)** **Your call still stands**. I raised concerns. **Your team is the deciders.** If after evaluation you stay with current architecture, I will execute it well. **Nothing in this conversation changes that.**
>
> **(b)** **I felt obligated to raise these explicitly because I have 4 weeks of ramp-up and 18 months of similar deployments in pattern. If I sat silently and the project ran into the issues I'm worried about**, that would be worse than this awkward conversation. **You'd rightfully be upset I didn't speak up earlier.**
>
> **What I want to avoid**: making this personal. **What I want**: you have my honest perspective + your team has the call.
>
> **Are we OK to continue this conversation, or should we take a break and come back tomorrow?**"

**Q2**: "What if Priya is wrong AND defensive AND there's pressure to ship quickly?"

**A**: Time-pressure exacerbates wrong architecture costs. Frame that.

> "I understand the timeline pressure. Here's what concerns me about the timeline + architecture interaction:
>
> **If we ship in 16 weeks with microservices + Kafka, you may make the deadline but**:
>
> - Operational issues in first 3 months will consume the team
> - Tuning takes another 3 months
> - Net: 22+ weeks before stable production
>
> **If we ship in 4 weeks with monolith**:
>
> - Operational simplicity from day 1
> - Tuning is straightforward
> - Net: 6-8 weeks to stable production
>
> **The deadline you have isn't actually 'shipping in 16 weeks'. It's 'having stable production'.**
>
> If the actual production target is 6 months, **the monolith path is far more likely to hit it. The microservices path is far more likely to be in 'operational firefighting' at month 6.**
>
> I'd ask you to re-frame your deadline with your business team: not 'when does v1 ship' but 'when is it operationally stable'. **The architecture choice changes which date that is.**"

**Q3**: "What if you find out Priya's architecture was actually mandated by her CTO and she has no choice?"

**A**: Big difference. Switch frame entirely.

> "Got it. So this was a CTO-level decision, not a team architectural exercise. **That changes everything for me.**
>
> Two things:
>
> **(a) Your hands are tied** on the high-level architecture. So my concerns about microservices vs monolith are **out of scope for you to change unilaterally**.
>
> **(b) Within microservices + Kafka + on-prem**, I can still help you **scope smartly**:
>
> - Start with fewer services (3 instead of 6)
> - Use the existing Kafka cluster (don't add new)
> - Defer the most complex service to Phase 2
> - Aggressive shared library to reduce inter-service complexity
>
> **My ask**: can I get a 30-min with your CTO at some point? Not to argue, but to share **the operational complexity reality of microservices in pharma compliance** as I've seen it. **CTO might want that input for future architecture decisions even if this one is set**.
>
> **For this deployment, I'll execute on the path you have**. Let me know your timeline for any new decisions."

**Q4**: "What if Priya agrees with you privately but says her team would lose face if they reverse the decision?"

**A**: Help her navigate the political reframe.

> "I hear you. Reversing architectural decisions publicly is hard. **Let me suggest a framing that's true and lets the team save face**:
>
> 'In the kickoff, we made the architectural choice based on the scale targets we had at the time. As we've been working with [vendor], we've **refined the scale targets** and **re-evaluated managed services compliance** — both came back differently than expected. **Based on updated information, we're going with monolith + managed services for v1, with a documented migration path to microservices if scale grows beyond [X].**'
>
> **This is true** — the targets HAVE been refined. InfoSec re-eval IS new information. Your team isn't reversing; they're **incorporating new information**.
>
> **Want me to draft this in writing for you to share with your team**? You can edit and present as your own."

→ Help her sell the reversal as growth, not failure.

**Q5**: "What if you're actually wrong and microservices was the right call?"

**A**: Acknowledge openly. Don't dig in.

> "Priya — based on what you've shared (specifically the 10x scale at 5000+ TPS, the InfoSec re-evaluation that came back same, the team's K8s expertise being unique to your org) — **I think you're right and I was wrong**.
>
> I appreciate you walking me through this in detail. **The microservices + on-prem path is the right call for your context**, and **I would NOT make the same recommendation I started this call with if I were in your shoes**.
>
> **What I'll do differently**: I'll get up to speed on your K8s setup faster, and I'll engage your platform team early on the ops handoff plan. **My initial 'monolith' instinct was wrong here, and I want to ship your actual architecture well.**
>
> Thanks for the patience to walk through it."

**Disagreeing well includes being able to update.** Strong FDEs change their mind in public when they're shown new information.

---

## ❌ 死路答法 (top 7)

1. **Open with "I disagree"** — burn bridge
2. **Use absolute language** ("monolith is always better")
3. **Don't acknowledge what they got right**
4. **Frame as statements, not questions**
5. **Pretend you have full context** — you don't
6. **Don't offer reversibility plan**
7. **Take it personally if they don't update view**

---

## ✅ 加分项 (top 7)

1. **Open with "walk me through how you got here"**
2. **Acknowledge what they got right** explicitly
3. **Concerns as questions** ("have you considered…")
4. **Quantify costs** (specific weeks, engineers, $)
5. **Offer reversibility plan** as commitment
6. **Defer to their authority** — their org, their call
7. **Quote your past disagreement-handled-well experience**

---

## 一句话总结

> **Disagree with customer architect = "walk me through your reasoning + acknowledge what's right + frame concerns as questions + alternative + reversibility plan + their call"**.
>
> 真正的 win 不是说服对方采用你的架构, 是**让对方觉得 "this person respects me enough to engage seriously rather than just say yes". 关系 + 决策 quality both up**.

---

## Cheat Sheet

```
不要说:
  - "I disagree with your architecture"
  - "Monolith is better than microservices"
  - "You should have considered..."
  - "This is wrong because..."
  - "I've seen this fail at other customers"
  - "Trust me, I know better"
  - Absolute language ("always", "never")

要说:
  - "Walk me through how you arrived here"
  - "Three things you got right: X, Y, Z"
  - "Have you considered..."
  - "Help me understand..."
  - "Your call — you know your org"
  - "If 6 months in this doesn't pan out, here's the path"
  - "I might be missing context"

8-layer response:
  1. Ask context (0:00-2:00)
  2. Listen (2:00-8:00)
  3. Reflect + acknowledge (8:00-10:00)
  4. Concerns as questions (10:00-14:00)
  5. Specific concerns (14:00-20:00)
  6. Alternative offered (20:00-24:00)
  7. Reversibility plan (24:00-27:00)
  8. Defer to their decision (27:00-30:00)

Time allocation:
  Listen: 8 min (most important)
  Reflect: 2 min
  Concerns: 6 min
  Alternative: 4 min
  Reversibility: 3 min
  Defer + commit: 3 min

Open script:
  "Before I share where I see it differently —
   walk me through how you arrived at this.
   You've thought about it longer than I have.
   I might be missing context."

Concerns as questions, not statements:
  ❌ "Microservices will slow you down"
  ✓ "Have you considered the ops burden of 6 services
     vs your platform team's bandwidth?"

  ❌ "Kafka is overkill at 50 TPS"
  ✓ "Help me understand — is the 10x target
     5000 TPS or 500 TPS? Different architectures
     fit different shapes."

Quantification matters:
  - "12-16 weeks vs 4 weeks build"
  - "40% of platform team time = 1.6 engineers"
  - "Over 18 months, 24 engineer-months of features"
  - "Migration cost: 4-6 weeks first, 2-3 weeks each"

Reversibility framing:
  "If monolith now and need microservices later:
   - Extract first service: 4-6 weeks
   - Subsequent: 2-3 weeks each
   - Total: 3-4 months migration
   I'll write the migration plan now as part of engagement."

Defer to their authority:
  - "Your call — you know your context"
  - "Whatever you and your team decide, I'll ship well"
  - "I'm not telling you my architecture is right"
  - "I want to make sure you have full info"

When asked your recommendation:
  Don't impose. Lay out options with conditions:
  - "If [A] then [path 1]"
  - "If [B] then [path 2]"
  - "I'd avoid [C] for these reasons but it's not unreasonable"

When CTO-mandated:
  Switch from architecture to scoping smartly within
  - Fewer services
  - Reuse infra
  - Defer complex services
  - Ask for 30-min with CTO separately

When Priya can't reverse for face:
  Help her frame as "incorporating new info"
  - Refined scale targets (true)
  - InfoSec re-eval result (true)
  - Draft the reframe doc for her

When you're actually wrong:
  Acknowledge openly
  Don't dig in
  "Based on what you've shared, I think you're right
   and I was wrong. Here's what I'll do differently."

Resume quote:
  "TikTok PayLater Brazil: Pulsar + bare-metal K8s.
   I disagreed. Asked their reasoning first, learned
   their Pulsar expertise was the strongest arg.
   Framed concerns as questions, offered hybrid alternative,
   committed reversibility plan. Ended up with hybrid
   (Pulsar for multi-tenant, RabbitMQ for high-volume).
   Architecture was better. They thanked me for not
   just saying yes to first choice."

Close line:
  "Thank you for the openness to revisit 4 weeks in.
   That's not always easy. Whatever you decide,
   I'll have learned a lot from this conversation."
```
