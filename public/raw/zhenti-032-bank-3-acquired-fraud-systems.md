## Q32 · 银行并购后统一 3 套反欺诈系统

> "A regional bank has **grown via acquisitions**. They now have **3 fraud detection systems** — one from each acquired entity — with **inconsistent labels, conflicting thresholds, and 3 different vendor stacks**. They want a **unified fraud platform in 90 days**. Walk me through your approach."

**Round**: Decomposition Case (60 min)
**出处**: Exponent 2026 FDE · Palantir / Databricks 高频
**行业**: Fintech / banking / fraud / risk

---

## 这道题在考什么

**不是**: 考你能不能 design 一个反欺诈模型.

**是**: 考你能不能在**遗留系统、政治、合规、3 个 owner、90 天 deadline** 的真实约束下做出**冷静的拆解 + 反时间压力的 push back**.

4 个 signal:

1. **Don't start with ML** — 90% 的候选人冲去讲 model. 真正的 win 是 **ontology + label unification** + **baseline-per-system** 在做 model 之前
2. **Push back on the 90 days** — 90 天 unify 3 个 acquired stack 是 fantasy. 你必须 reverse scope 到一个 90 天能交付且测得到的 milestone
3. **Treat 3 systems as 3 customers** — 每个 acquired entity 都有 fraud SME, 他们的 expertise 是 asset 不是 debt. 不能 "throw away their model"
4. **Compliance + audit first** — 反欺诈错判会被 monitor 罚. 不能 "improve overall recall" 同时 increase false positive rate 在某 region

---

## ❌ 最常见的挂法

**挂法 #1: 立刻冲 "trained one unified XGBoost on combined data"**

> "I'd merge all 3 datasets, train a unified XGBoost on labeled fraud examples, ensemble it with the 3 legacy models, and gradually deprecate them."

死. 你**没问**:
- 3 个 system 的 "fraud" 定义一致吗? (Card-not-present vs ACH vs wire vs synthetic ID — 每家 acquired 都是不同)
- Labels 怎么来的? (Manual review? Customer chargeback? Investigator confirmed?)
- Acquired entity 的 fraud team 还在吗 (人事变动) ?
- 监管要求 (OCC / Fed / 各州) 是 entity-level 还是 holding-co level ?
- 已有的 false positive rate / false negative rate 各自是多少?

**挂法 #2: 接受 90 天 deadline 不 push back**

> "Yes, 90 days is doable. Week 1 we'll do data integration, week 2 model training..."

死. 90 天 unify 3 stack + clean labels + train model + compliance approval + go-live = impossible. 你必须 reverse scope.

**挂法 #3: 把 acquired team 当 "legacy debt"**

> "We'll deprecate the old systems and migrate to the unified platform."

死. Acquired fraud SME 知道**为什么** threshold 设 0.78 而不是 0.80. 那个数字背后是 18 个月 chargeback dispute + monitor 沟通的血泪. 直接扔掉 = 6 个月后你又踩同样的坑.

---

## 完美答案架构 (5 步)

### Step 1: 澄清问题 (10 min)

> "Before I sketch, I want to ask 10 questions. The key issue is that 'unify 3 fraud systems' could mean 5 totally different things."

**10 个 clarifying questions**:

> **Q1**: "When you say 'unify', do you mean (a) **one operational dashboard** that aggregates 3 systems' alerts, (b) **one decision engine** that produces the canonical fraud-yes/no, (c) **one model** that replaces 3, or (d) **one data lake** with raw events from all 3? These are 5 different projects with different scopes."

> **Q2**: "Is 'fraud' the same business definition across the 3 systems? Card fraud, ACH fraud, account takeover, synthetic identity, wire fraud, money laundering (AML), check fraud — each acquired entity probably specialized in one. **Are we unifying all fraud types, or starting with one?**"

> **Q3**: "What's the **label hierarchy** across the 3? Each system probably has its own taxonomy — System A says 'CNP fraud / ATO / synthetic'; System B says 'P0 / P1 / P2'; System C says 'Confirmed / Suspected / Disputed'. **Has anyone mapped these to a common ontology?**"

> **Q4**: "Are the **fraud SMEs from acquired entities still on staff**? If yes, they're our primary partners. If no, who do we ask 'why is this threshold 0.78'?"

> **Q5**: "What's the **regulatory structure**? OCC / Fed / FDIC have entity-level expectations. Are the 3 entities legally consolidated, or still separate charters? Each scenario has totally different audit + compliance work."

> **Q6**: "What's the **current performance** of each — Precision, Recall, False Positive Rate, dollar loss prevented, customer friction (false positive on legitimate transactions)? **Without baselines we can't measure improvement**."

> **Q7**: "**Why 90 days specifically?** Is it driven by (a) cost (3 vendor contracts expiring), (b) regulatory (OCC exam coming), (c) risk (one of the 3 systems has known gap), (d) executive (CEO wants quick win)? The driver determines what we can compromise."

> **Q8**: "What's the **dollar magnitude** of fraud and false positive cost? Total fraud loss / year? Total customer friction events / year (legitimate transactions blocked)? If fraud is $50M and friction is $2M, optimize differently than reverse."

> **Q9**: "What's the **vendor stack** — proprietary, FICO Falcon, ThreatMetrix, in-house? Some are SaaS (we can keep), some on-prem (we may need to host)."

> **Q10**: "**Stakeholders + veto**: CRO, Chief Risk Officer? CISO? Each acquired entity's former Head of Fraud? CCO (compliance)? Internal Audit? Who can kill the project?"

**面试官 likely 回答**:
- (a) Unified decision engine + operational dashboard (NOT one model)
- Card fraud + ACH + ATO (deprioritize wire / AML for now)
- 3 different taxonomies, NOT mapped
- 2 of 3 fraud SMEs retained, 1 left
- Legally consolidated, but OCC examines per-portfolio
- Baselines: System A precision 78%, recall 60%; B: 82%/55%; C: 70%/68% (note: not apples-to-apples because of label inconsistency)
- 90 days driven by OCC exam in Q3 (need consistent reporting)
- Fraud loss $42M/year combined, friction $8M/year
- Stack: System A = FICO Falcon (SaaS), System B = in-house Python on AWS, System C = SAS on-prem
- Veto: CRO + each retained fraud SME + CCO

→ **Real scope**: in 90 days, build a **unified ontology + label mapping + operational dashboard + consistent reporting for OCC exam**. NOT replace the 3 models.

This is a **massive reframe** from "build a unified ML model" to "build the data foundation".

---

### Step 2: 找干系人 + 成功指标 (10 min)

**Stakeholder map**:

| Stakeholder | 在意什么 | 对项目态度 | 我对他们的关键动作 |
|---|---|---|---|
| **CRO (Chief Risk Officer)** | Capital reserves, regulatory exam | Sponsor, wants quick win | Weekly leadership review, OCC-ready dashboard |
| **CCO (Compliance)** | Audit trail, OCC exam Q3 | Critical, gates go-live | Daily standup during cutover, audit trail demo |
| **Acquired Head of Fraud A** (retained) | Her model's continued operation | Defensive, suspects shutdown | First meeting: "your model stays, we're just adding a layer" |
| **Acquired Head of Fraud B** (retained) | Her team's expertise valued | Skeptical of unification | Co-design the ontology with her |
| **Acquired Head of Fraud C** (left, replaced by IC) | N/A | IC knows the model but not the why | Document tribal knowledge fast |
| **CISO** | Data movement security (PCI / GLBA) | Approval needed | Network segmentation review |
| **Internal Audit** | Replay / reproduce decisions | Will demand audit log | Show audit log architecture |
| **Customer Service** | False positive impact on customers | Operational | Brief on what to expect post-cutover |
| **Vendor: FICO** | Contract / churn | Tangential | Get their FAE on a call early |

**Success metrics (3 层)**:

**Layer 1 — Compliance / Audit-ready** (must achieve for Q3 OCC exam):
- Unified fraud taxonomy with mapping from each legacy system's labels
- Consistent OCC reporting across the 3 portfolios
- Audit log demonstrating every decision with source system + reasoning

**Layer 2 — Operational** (CRO's daily view):
- 3-system unified dashboard with normalized precision / recall / FPR
- Cross-system fraud signal sharing (a fraudster seen in System A getting flagged in System B)
- Total fraud loss trend
- Total customer friction trend

**Layer 3 — Model unification** (deferred to month 6+):
- Per-fraud-type unified model
- Cross-portfolio retraining
- Vendor consolidation

**Counter-metrics** (must not move negatively during cutover):
- Per-portfolio recall (don't let one acquired entity's recall drop because we changed something)
- False positive rate on legitimate transactions
- OCC compliance posture per entity

**The reframe**:

> "The 90-day milestone isn't 'unify the model'. It's 'unify the **ontology + reporting + audit trail** so the Q3 OCC exam treats the 3 portfolios consistently'. Model unification is a 6-12 month follow-up. Trying to do model unification in 90 days **will fail the OCC exam** — the worst outcome."

---

### Step 3: 梳理输入数据 (10 min)

**Data inventory (3 systems, each has different shape)**:

| Dataset | System A (FICO Falcon SaaS) | System B (In-house Python) | System C (SAS on-prem) |
|---|---|---|---|
| **Transaction events** | Real-time API + daily export | Streaming Kafka | Daily SAS dataset |
| **Fraud labels** | "fraud_score" 0-1000 + 5 categorical types | "is_fraud" binary + investigator tag | "fraud_class" multi-label |
| **Investigator notes** | Free text in FICO portal | Tickets in Jira | Excel spreadsheet (yes, really) |
| **Customer chargebacks** | Visa/Mastercard feed | Daily batch | Daily batch |
| **Authentication signals** | ThreatMetrix integration | Custom device + behavior | None |
| **Schema docs** | FICO documentation | Confluence (partial) | Tribal knowledge in 1 IC's head |

**Key gaps + dirty data issues**:

1. **Label semantic drift across systems**:
   - System A "fraud" = confirmed chargeback in 60 days
   - System B "is_fraud" = investigator marked confirmed OR suspected
   - System C "fraud_class" = mixed (some labeled by customer report, some by analyst)
   - **None of these are the same label**.

2. **Schema drift within each system**:
   - System A FICO upgraded model 2x in last 3 years, feature set changed
   - System B has 3 generations of features (some deprecated but still in DB)
   - System C SAS code last touched 18 months ago

3. **Tribal knowledge in 1 IC's head** for System C is the **single biggest risk**.

4. **Cross-system customer matching**: same customer may exist in 2-3 systems with different IDs. Need entity resolution before any cross-system signal sharing.

5. **PCI / GLBA constraints**: data movement between the 3 stacks needs CISO + legal review. Some data may not be transferable.

**Week 1 must-do**:
- Lock down System C IC for 2 weeks (don't let her quit or get reassigned)
- Schedule meeting with each acquired Head of Fraud
- CISO data movement approval (initiate before week 1 ends — this takes 2-4 weeks usually)

---

### Step 4: 拆成可解子问题 (15 min)

> "Now I have scope + stakeholders + data. Here's the decomposition, ranked by risk × value, with a strong opinion on sequencing."

**8 subproblems**:

| # | 子问题 | Risk | Value | 90-day pri |
|---|---|---|---|---|
| **A** | **Ontology design**: unified fraud taxonomy + label mapping from each system | Medium | Critical | **1** |
| **B** | **Baseline per system**: compute apples-to-apples P/R/FPR using unified labels | Low | Critical | **2** |
| **C** | **Unified operational dashboard**: 3-system view with normalized metrics | Low | High | **3** |
| **D** | **Audit log architecture**: every decision traceable to source system + reason | Medium | High (OCC critical) | **4** |
| **E** | **Cross-system signal sharing**: fraudster in A flagged in B/C | High | Medium | Defer to month 4-6 |
| **F** | **Unified ML model**: replace 3 with 1 | High | High | **Defer 6-12 months** |
| **G** | **Vendor consolidation**: kill FICO / SAS, in-house only | High | Cost-driven | Defer 12+ months |
| **H** | **Entity resolution**: cross-system customer identity | High | Required for E/F | Run in parallel to A |

**Why this sequencing**:

> **A first** because: without unified ontology, every other metric is meaningless. "System A has 78% precision" means nothing if A's definition of fraud is "chargeback in 60 days" and B's is "investigator tagged". This is **the foundation**.

> **B second** because: until we can compute P/R/FPR using **unified labels**, we don't know how each system actually performs. The current "78%/82%/70%" comparisons are misleading.

> **C third** because: CRO needs operational visibility for daily ops. Dashboard ships once A + B exist.

> **D parallel** because: OCC exam Q3 demands audit log. Build it alongside C.

> **E deferred** because: requires entity resolution (H) and is medium value vs high risk. Phase 2.

> **F + G deferred 6-12 months** because: trying to do a unified model in 90 days is exactly the scope creep that **fails the OCC exam**. Strong push back here.

> **H runs parallel to A** because: it's a prerequisite for E and F. Long lead time (entity resolution is hard).

**Strong opinion**: I'd **explicitly defer model unification** and push back if the customer insists.

---

### Step 5: Walking-skeleton MVP (15 min)

**Walking-skeleton (Week 1-2)**:

```
[System A: FICO events] ──┐
[System B: in-house]      ├──→ [Schema-mapper / ontology layer] ──→ [Unified events store]
[System C: SAS daily]     ──┘                                              │
                                                                            ▼
                                                              [Mock unified dashboard]
                                                              (3 systems shown side-by-side,
                                                              NOT yet normalized)
```

**Week 1**:
- Day 1: Kickoff with CRO + 2 retained Heads of Fraud + CISO + CCO
- Day 2-3: Lock System C IC for 8 weeks
- Day 4-5: Initiate CISO data movement approval

**Week 2**:
- Build a "label normalizer" in Python that takes each system's label and maps to a stub unified taxonomy ({CNP_fraud, ACH_fraud, ATO, synthetic_ID, other})
- Sample 1000 transactions from each system, manually validate the mapping with the SME (or System C IC)
- Initial dashboard: 3 columns, raw labels shown, NO comparisons yet

**Walking-skeleton works because**:
- **No ML, no model change** (zero risk to existing fraud operations)
- **Immediate value** to CRO: "I can see all 3 portfolios in one screen for the first time"
- **Foundation for everything**: ontology + sample data is what every subsequent step builds on
- **Politically safe**: each acquired Head of Fraud sees their own data still flowing, just visible in a new place

**Week 3-6: Phase 1 — Unified Ontology + Baseline**

- Final ontology design (workshop with both SMEs + System C IC)
- Backfill 90 days of historical events using ontology mapper
- Compute unified P/R/FPR baseline per system
- CRO + CCO review baselines, sign off on definitions

**Week 7-10: Phase 2 — Operational Dashboard + Audit Log**

- Production dashboard with normalized metrics
- Audit log capturing every decision + source system + reason
- OCC-friendly reporting format (3 portfolios consistent)

**Week 11-13: Phase 3 — OCC Exam Prep**

- Mock exam with Internal Audit
- Documentation package
- Training for CCO team

**90-day deliverable**: NOT a unified model. **A unified ontology + dashboard + audit trail that makes the OCC exam pass cleanly** AND lays the foundation for model unification in month 6.

**Why this MVP framing wins**:

> "If the customer pushes back 'but we wanted a unified model in 90 days', I'd say: '**Let's be honest about what 90 days can deliver. A unified ML model trained on inconsistent labels is worse than 3 separate models — it'll degrade both precision and recall. The OCC exam is in Q3. If we ship a broken unified model, we fail the exam. If we ship a unified ontology + dashboard, we pass the exam cleanly AND set up the model work for Q4-Q1. I'll commit to month 6 for model unification, with weekly progress to the CRO from month 3.'**"

---

## 详细回答 (Sample 60-min monologue)

> "Before I sketch, I want to ask 10 things. The key issue: 'unify 3 fraud systems' could mean operational dashboard, decision engine, one model, or one data lake — five totally different projects.
>
> *(asks 10 Qs, gets answers)*
>
> OK so the real scope: in 90 days, build a unified ontology + label mapping + operational dashboard + consistent reporting for the Q3 OCC exam. Model unification is a 6-12 month follow-up.
>
> Before I go further, I want to **push back on the 90-day deadline if it includes model unification**. 90 days to unify 3 acquired stacks + clean labels + train model + compliance approval + go-live is fantasy, and **the worst outcome is failing the OCC exam by shipping a broken unified model**. I'd commit to month 6 for model, 90 days for ontology + dashboard + audit trail. Is that acceptable?
>
> *(gets buy-in)*
>
> **Stakeholders**: CRO is sponsor. CCO is the gatekeeper for OCC exam Q3. 2 retained Heads of Fraud are my primary partners — I treat their expertise as asset, not legacy debt. System C IC is single point of failure because the previous Head left; I'd lock her for 8 weeks immediately. CISO needs to approve data movement, that's a 2-4 week lead time.
>
> **Data**: 3 systems, 3 completely different label taxonomies. System A 'fraud' = chargeback in 60 days, System B = investigator marked confirmed OR suspected, System C = mixed. **None of these are the same label**. So all the existing '78% precision' numbers are not comparable. First job: unified ontology.
>
> **Decomposition**: 8 subproblems.
>
> 1. **Ontology design** — foundation. Without it, every other metric is meaningless.
> 2. **Baseline per system** using unified labels — until we have this, we don't know how each system actually performs.
> 3. **Unified operational dashboard** — CRO's daily view, normalized metrics.
> 4. **Audit log architecture** — OCC exam Q3 requires this.
> 5. **Cross-system signal sharing** — defer to phase 2, requires entity resolution.
> 6. **Unified ML model** — defer 6-12 months, push back if pressured.
> 7. **Vendor consolidation** — defer 12+ months.
> 8. **Entity resolution** — runs parallel to ontology, long lead time.
>
> **Walking-skeleton MVP Week 1-2**:
>
> Build a label normalizer in Python. Map each system's label to a stub unified taxonomy. Sample 1000 transactions from each system, validate mapping with SMEs. Initial dashboard shows 3 systems side-by-side, NO normalization yet. Zero risk to existing operations, immediate value to CRO.
>
> **Week 3-6**: final ontology + 90-day backfill + apples-to-apples baseline.
>
> **Week 7-10**: production dashboard + audit log.
>
> **Week 11-13**: OCC exam prep + mock exam with Internal Audit.
>
> **90-day deliverable**: unified ontology + dashboard + audit trail. OCC exam passes cleanly. Model work starts month 4 with weekly CRO updates.
>
> **Three things to flag proactively**:
>
> **(a) System C IC is single point of failure**. Previous Head left, only she knows why the thresholds are what they are. Lock her contract + interview her for tribal knowledge in week 1.
>
> **(b) Don't deprecate retained SMEs**. Their thresholds encode 18 months of monitor sign-off and chargeback dispute history. Co-design ontology with them, not around them.
>
> **(c) PCI / GLBA data movement** between 3 stacks has 2-4 week CISO lead time. Start that approval day 1, not when we're ready to ingest.
>
> Want me to deep-dive ontology design, audit log architecture, or the push-back conversation with CRO?"

---

## Gao Xin 简历专属 reframe

This problem **directly parallels** your TikTok PayLater experience integrating risk systems across 7 markets:

> "I had this exact pattern at TikTok PayLater. We had **7 markets** (Indonesia, Brazil, Mexico, ...) each with **different fraud / risk definitions** because each was approved by a different regulator under different framework. The Indonesia OJK definition of 'high risk' wasn't the same as Brazil BACEN's.
>
> I had to unify them for **cross-market reporting** to leadership without breaking each market's regulator-approved decisioning. **The 5-step framework I'd apply**:
>
> 1. **Clarify**: leadership wanted 'consistent global risk metrics'. I asked: 'consistent for *which* purpose?' Turned out it was internal board-level reporting, NOT decision-making. Huge scope difference.
> 2. **Stakeholder map**: each market's local risk Head had veto. Plus regional compliance. Plus our credit risk modeling team.
> 3. **Data inventory**: 7 different label taxonomies. Indonesia had granular 'collection bucket 1-7', Mexico had binary, Brazil had 3-tier. Same problem as the 3 fraud systems here.
> 4. **Decompose**: ontology first, not unified model. **Each market's local model stayed**, we added an ontology layer that mapped local labels → global taxonomy for reporting.
> 5. **Walking-skeleton MVP**: in 2 weeks, I shipped a Python ontology mapper that took each market's daily risk export and produced global-taxonomy aggregates. Leadership saw global numbers for the first time. Each local Head was not threatened because their model + thresholds were unchanged.
>
> **Key insight that transfers**: when customers ask 'unify our 3 systems', the right move is usually 'unify the **measurement / reporting** layer first, models second'. Trying to do both at once in 90 days is what fails.
>
> Also, the **labels-are-not-the-same-across-systems** problem is *the* hardest thing about cross-system unification. I've spent 60% of my time on label semantic disambiguation in the past 2 years, not on model architecture."

**Other resume hooks**:

- **ConvFinQA ablation methodology** — your structured approach to "which variable actually matters" applies directly when figuring out why the 3 systems have different precision (is it data, labels, or model architecture?).
- **Internal Agent Platform onboarding multiple teams** — you've already done the "treat each team's domain knowledge as asset not legacy debt" dance.

---

## 5 个 Follow-ups

**Q1**: "What if CRO insists on unified model in 90 days, not 6 months?"

**A**: This is the make-or-break push back. Don't capitulate. Frame:

> "I want to be direct about this because the cost of failing is huge. Here are the 3 likely outcomes if we try unified model in 90 days:
>
> 1. **Most likely**: We ship a model trained on inconsistent labels. It looks unified but performs worse than the 3 separate models on each portfolio's true distribution. **Customer friction goes up 20-30%, recall drops 5-10pp per portfolio**. OCC examines and finds we have **inconsistent predictions across portfolios for similar transactions** — that's worse than no unification.
>
> 2. **Less likely**: We rush a model that doesn't actually unify (just trained on 1 portfolio, applied to all 3). **We don't pass the exam either** because the OCC sees we're inconsistent.
>
> 3. **Best case**: We ship something that 'works' but we don't have the audit trail / decision explainability ready. **OCC exam finds documentation gap, gives finding**.
>
> Versus: **90 days for ontology + dashboard + audit trail = clean OCC pass + foundation for model unification in month 6**. The board press release writes the same: 'unified fraud platform' — we just delivered the right unit, not the wrong unit.
>
> I'm happy to put this in writing. If after this conversation you still want me to ship unified model in 90 days, I'll need to escalate to my leadership because I don't want to put my name on something that's likely to fail your exam."

**Q2**: "What if System C IC quits during the project?"

**A**: This is **the** scenario I'd plan for from week 1. Mitigation:

- **Week 1**: Lock her on a 90-day contract / project-completion bonus
- **Week 1-2**: Document EVERYTHING. Pair her with a junior on our team for 2 weeks. Have her record screen + voice walkthroughs.
- **Week 3-4**: Validate her documentation by having someone else (not her) execute against it.
- **Risk fallback**: if she quits, System C's continued operation is at risk for ~2-4 weeks while team picks up. Keep System C running on autopilot during that window — don't try to migrate during the gap.

**Q3**: "What if one of the 2 retained Heads of Fraud refuses to participate?"

**A**: This is political, not technical. Diagnose first:

- **What's her actual concern?** Usually one of: (a) she thinks her team will be deprecated, (b) she's worried about losing the model her team built, (c) she's worried about her own career.
- **Counter-offer per concern**:
  - For (a): "Your team's model stays. We're adding ontology on top, your team keeps owning the model."
  - For (b): "We commit to your model running unchanged through 2027. We're not deprecating it in this project."
  - For (c): "I want you co-leading the ontology design. Your name on the launch readme, your contribution highlighted to CRO."
- If still no: escalate to CRO. "I need her cooperation. Either she joins, or you assign someone empowered to make decisions on her portfolio." Don't proceed without authority on each portfolio.

**Q4**: "What if OCC exam comes early (Q2 not Q3)?"

**A**: Time compression → narrow scope further.

- **Q2 scope**: ontology + reporting consistency only. Skip audit log v1, defer to Q3.
- **Honest with examiner**: "We're in the middle of a 90-day unification. Here's the ontology, here are the baselines. We commit to audit log by Q3."
- **Risk**: OCC may give a finding about audit log gap. **That's better than failing the exam outright.**
- **Don't fake**: don't ship a half-done audit log that misrepresents what we have. OCC will find it.

**Q5**: "What's your eval methodology for whether unification actually improved things?"

**A**: This is subtle because unification's win isn't immediately measurable:

**Leading indicators (week-month)**:
- Time to investigate cross-portfolio cases (was high pre-unification because had to log into 3 systems)
- Fraud SME team efficiency (cases / SME / day)
- OCC quarterly reporting prep time (was X days, now Y days)

**Mid-term (3-6 month)**:
- Catch rate of fraudsters seen across portfolios (e.g., fraudster active in System A's portfolio gets flagged when they try System B's)
- Audit findings count

**Lagging (6-12 month)**:
- Total fraud loss (combined)
- False positive customer friction (combined)
- Vendor cost (when we eventually consolidate)

**Counter-metric (must watch)**:
- Per-portfolio recall (don't let it drop on any acquired entity due to unification changes)
- Customer friction per portfolio
- Investigator workload distribution

---

## ❌ 死路答法 (top 7)

1. **冲 "train one unified XGBoost"** without checking label consistency
2. **接受 90-day deadline** for full model unification
3. **Treat acquired SMEs as legacy debt** to deprecate
4. **Skip ontology / label work**, jump to architecture
5. **Ignore OCC exam timing** — that's the real deadline driver
6. **Ignore single-IC-knows-System-C risk**
7. **Promise vendor consolidation in 90 days** (politically + contractually impossible)

---

## ✅ 加分项 (top 7)

1. **Push back on 90-day deadline** with specific failure modes
2. **Treat ontology as foundation, model as deferred**
3. **Co-design with retained SMEs**, not around them
4. **Identify single-IC tribal knowledge risk** in week 1
5. **CISO data movement lead time** flagged early
6. **OCC exam reframed as the real driver**
7. **Quote your TikTok PayLater 7-market unification experience**

---

## 一句话总结

> **银行并购 3 套 fraud 系统统一 = "ontology 第一, 模型最后" + "把 90-day 'unify' reverse-scope 到 'unify 报告与审计' 而非 unify model" + "treat acquired SME as asset not debt"**.
>
> 真正的 win 不是新 model, 是**让 OCC 看到 3 portfolio 用同一套语言报告 + audit trail 可 replay**. Model 留到 month 6 启动, 在 ontology + baseline 都稳了之后.

---

## Cheat Sheet

```
不要做:
  - 立刻冲 unified XGBoost
  - 接受 90-day model deadline
  - 把 acquired SME 当 legacy
  - 跳过 ontology / label
  - 忽略 OCC 时机
  - 假设 vendor 可 90-day 替换

要做 (5 step):
  1. Clarify (10min): 10 Q, 锁 "unify" 的具体含义
  2. Stakeholder: CRO sponsor, CCO gatekeeper, SME 是 partner
  3. Data: 3 系统 3 不同 label, 不可比
  4. Decompose: ontology > baseline > dashboard > audit log > defer model
  5. MVP: 2 周 label normalizer + 3-column dashboard

Clarify Q 必问:
  - "Unify" = dashboard / engine / model / lake?
  - 哪些 fraud type?
  - Label taxonomy 已经 mapped?
  - SME 还在吗?
  - 监管结构 (entity-level vs holding-co)?
  - 当前 baseline P/R/FPR?
  - 为啥 90 days? (OCC exam!)
  - 美元规模 (fraud vs friction)?
  - Vendor stack?
  - Stakeholder veto 谁?

Stakeholder veto:
  - CRO (sponsor)
  - CCO (OCC exam)
  - Acquired Head of Fraud A & B (retained)
  - System C IC (single point of failure)
  - CISO (data movement)

8 subproblems:
  1. Ontology (must, pri 1)
  2. Baseline per system (must, pri 2)
  3. Dashboard (high, pri 3)
  4. Audit log (high, pri 4, OCC)
  5. Cross-system signal (defer to month 4-6)
  6. Unified model (defer 6-12 months)
  7. Vendor consolidation (defer 12+ months)
  8. Entity resolution (parallel)

Walking-skeleton Week 1-2:
  - Label normalizer Python
  - Stub ontology
  - Sample 1000 / system
  - 3-column raw dashboard
  - 0 ML, 0 model change

Push back script:
  "90-day unified model = likely OCC exam fail.
   90-day unified ontology + dashboard + audit = clean OCC pass + month 6 model.
   Same press release, right unit shipped."

Risk callout:
  - System C IC = single point of failure
  - 2 SMEs are partners, not deprecated
  - CISO data movement = 2-4 week lead
  - PCI / GLBA may block some data movement

OCC exam Q3 = real deadline, not "90 days"

Success metric 3-layer:
  L1 Compliance: unified ontology + audit trail
  L2 Operational: 3-system dashboard normalized
  L3 Model (deferred): per-fraud-type model month 6+

Counter-metric:
  - Per-portfolio recall must not drop
  - FPR per portfolio
  - OCC posture per entity

Resume quote:
  "TikTok PayLater 7 markets had same problem —
   7 label taxonomies. I added ontology layer for
   cross-market reporting, kept each market's model.
   Same answer here: ontology first, model last."

Key phrases:
  - "Let me ask 10 things before I sketch..."
  - "I want to push back on the 90-day model timeline..."
  - "The OCC exam is the real deadline driver"
  - "Treat acquired SMEs as asset, not legacy debt"
  - "Label semantic across systems is THE hardest part"
  - "Walking-skeleton: ontology + dashboard, no ML, 2 weeks"
```
