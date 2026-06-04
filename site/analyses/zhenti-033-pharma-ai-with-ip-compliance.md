## Q33 · 药企内部化合物 AI 助手 (IP + 合规约束)

> "A **top-10 pharma company** wants to deploy an **AI assistant for researchers** to query **internal compound libraries, assay data, and patent claims**. Their **legal, IP, and compliance teams** have strong concerns. Walk me through how you'd **scope** this in the first 90 days."

**中文翻译**:

> "一家 **全球前十大药企** 想给科研人员部署一个 **AI 助手**, 让他们查询 **内部化合物库 (compound library)、实验数据 (assay data)、专利权利要求 (patent claims)**. 他们的 **法务、IP (知识产权)、合规团队都有很强的担忧**. 跟我讲讲你前 90 天怎么 **scope** (定范围) 这个项目."

**Round**: Decomposition Case (60 min)
**出处**: Exponent 2026 FDE · Palantir / Anthropic (life sciences) · OpenAI Enterprise
**行业**: Pharma / life sciences / IP-sensitive

---

## 📖 术语速查 (本题用到的)

> 这题术语**药企特定 + IP / 监管词最多**, 5 min 看完后面跟得上.

### 药企 / 制药行业核心

| 术语 | 解释 |
|---|---|
| **Compound library (化合物库)** ⭐ | 药企内部所有候选化合物的数据库 — 结构 + 性质 + 测试结果. **核心知识产权**, 一旦泄露 = 几亿美金研发白做. |
| **Assay data** | 实验数据 — 在 lab 里测某化合物对靶点的活性 / 毒性 / 选择性. 跟 compound library 配对. |
| **Lead optimization (lead opt)** | 先导化合物优化 — 找到 hit 后, 改结构提高活性 + 降低副作用的迭代过程. **Pre-filing 最敏感阶段**. |
| **SMILES (Simplified Molecular-Input Line-Entry System)** | 化合物结构的文本表示, 比如 "CC(=O)OC1=CC=CC=C1C(=O)O" 是阿司匹林. RAG 检索化学语料必处理. |
| **Therapeutic area** | 治疗领域 — Oncology (肿瘤) / Immunology / Cardiovascular / Neurology 等. 这题 pilot scope 是 Oncology, 不是全公司. |
| **Medicinal chemist** | 药物化学家 — 设计 + 合成 candidate compound 的人. 这题 30 人 pilot 用户. |
| **Pharmacovigilance** | 药物警戒 — 上市后跟踪副作用. Adverse event database 在这里. |
| **LIMS (Laboratory Information Management System)** | 实验室管理系统 — 存 assay 数据 + sample tracking. 数据源之一. |

### FDA / 监管 / 合规

| 术语 | 解释 |
|---|---|
| **FDA (Food and Drug Administration)** | 美国食药监 — 药企最大监管. |
| **EMA** | European Medicines Agency, 欧盟同等机构. |
| **Phase I / II / III trials** | 临床试验 3 阶段: Phase I (安全, 几十人) → Phase II (有效, 几百人) → Phase III (确认, 几千人). Phase III 数据极敏感. |
| **BLA / NDA** | Biologics License Application / New Drug Application — 向 FDA 申请药上市的申报. 文件极敏感. |
| **21 CFR Part 11** ⭐ | FDA 法规第 21 卷第 11 部分 — 规定电子记录 + 电子签名的合规要求. AI 系统如果输出进入 FDA submission, 必须 21 CFR Part 11 validated. |
| **GxP** | Good x Practice 总称 (GMP 生产, GLP 实验室, GCP 临床). FDA 监管的所有 quality framework. |
| **Validated use vs non-validated use** ⭐ | "Validated" = 用于 FDA 申报 / 患者安全决策, 必须正式 validation (耗时 1-2 年). "Non-validated" = 仅 R&D / exploration, 不进 submission, 流程轻得多. 这题 v1 是 non-validated. |
| **FDA AI guidance** | FDA 2023+ 发布的 AI/ML 在药品研发中的应用指引. |
| **Freedom-to-operate (FTO)** | 自由实施权 — 我做这个化合物会不会侵犯他人专利? IP attorney 的核心工作. |
| **Pre-filing data** | 还没向专利局 / FDA 申报的数据. **最敏感**, 一泄露竞品就抄. |
| **Adverse event report (AE)** | 副作用报告 — HIPAA + 21 CFR Part 11 双重监管. 不在这题 pilot scope. |

### 跨国合规

| 术语 | 解释 |
|---|---|
| **GDPR / SCC** | 欧盟数据保护法 / Standard Contractual Clauses (跨境传输条款). 欧盟数据出境必合规. |
| **PIPL (China)** | 中国个人信息保护法 — 中国患者数据跨境受严控. |
| **CCPA / NYSHIELD** | 加州 / 纽约州的数据保护法. |
| **Data residency** | 数据必须留在某国境内的要求. EU 项目数据必须 EU 内, US 项目 US 内. 跨境是 veto. |

### IP / 法务

| 术语 | 解释 |
|---|---|
| **Chief IP Officer (CIPO)** ⭐ | 首席知识产权官 — 这题**最大 veto holder + 创伤来源** (18 个月前 ChatGPT 化合物结构泄露事件). |
| **Trade secret** | 商业秘密 — 比专利保护更敏感, 因为一公开就没了. Pre-filing 化合物属于这类. |
| **Patent claims** | 专利权利要求 — 专利说明书里定义保护范围的条款. |
| **Patent prep notes** | 专利申报前的草稿 + 律师笔记 — 在律师笔记本电脑里, 不在系统. **永久 defer**. |
| **CLO (Chief Legal Officer)** | 首席法务官. |
| **CCO (Chief Compliance Officer)** | 首席合规官 — 管 FDA / GxP 合规. |
| **CMO (Chief Medical Officer)** | 首席医学官 — 管 patient safety + 临床决策. |

### AI / 系统 / 架构

| 术语 | 解释 |
|---|---|
| **RAG (Retrieval-Augmented Generation)** | 检索增强生成 — LLM 先检索内部文档, 再基于文档生成答案 + 引用. 比 fine-tuning 适合企业内部知识. |
| **Self-hosted vs API** ⭐ | 模型部署模式选择 — 自托管 (数据不离开公司) vs commercial API (数据走 OpenAI/Anthropic). **药企几乎必选 self-hosted**, 是 IP / 法务决策不是技术决策. |
| **Llama 3.1 70B / Mistral** | 主流 self-host LLM. 这题 likely 选择. |
| **Vertex AI + PrivateLink** | AWS 的私有 LLM hosting, 数据不走公网. 中等合规级别的选择. |
| **Vertex AI Vector Search / Weaviate (self-hosted)** | 自托管向量数据库. 用 self-hosted 而不是 Vertex AI Vector Search (SaaS) 因为 IP team 不批多租户云服务. |
| **Hallucination (幻觉)** | LLM 编造不存在的事实 — 在化学领域 = 编造化合物结构 / 假活性数据. 极危险. |
| **Citation / provenance** | 每个答案必须引用来源文档. Audit + 合规必需. |
| **Walking skeleton** | 最薄端到端版本, 每组件可 mock 但流程跑通. **Decomposition 题 MVP 方法论**. |
| **Red team** | 红队测试 — 主动 probe 模型, 找漏洞. 化学领域 = 问竞品化合物看会不会泄露训练数据. |

### 角色 / 用户

| 术语 | 解释 |
|---|---|
| **Head of Research** | 研究负责人 — 这题 oncology pilot 的 sponsor. |
| **Regulatory affairs** | 法规事务 — 跟 FDA 沟通的内部团队. |
| **Patent attorney** | 专利律师 — 内部 IP 团队成员. |
| **InfoSec / CISO** | 信息安全 — 管 network + encryption. |
| **Internal Audit** | 内审 — SOX-adjacent controls 审查. |

---

## 这道题在考什么

**不是**: 考你能不能 build 一个 RAG.

**是**: 考你能不能在**最 IP-sensitive 行业 + 多 veto 持有者 + 全球合规拼盘**下做 careful, conservative scoping. 这是 FDE 题里**政治维度最重**的之一.

4 个 signal:

1. **Stop and ask before architecting** (先停下来问问题, 别急着画架构) — 90% 候选人开始讲 RAG / vector DB. 实际 90 天里 60-70% 时间是法务 / IP / 合规审批, 不是技术
2. **Data classification first** (数据分类优先) — 化合物结构 + 临床试验 + 专利说明书 + assay data 各自 IP / 合规等级不同, 不能一刀切
3. **Pilot scope discipline** (pilot 范围要克制) — pilot 不是 "全公司 5000 研究员", 是 "1 个 therapeutic area (治疗领域) 的 30 人 team 用 6 个月"
4. **Self-host vs API as a decision, not a default** (自托管 vs API 是个决策, 不是默认值) — IP 暴露容忍度决定 architecture, FDE 必须帮客户做这个 tradeoff (权衡)

---

## ❌ 最常见的挂法

**挂法 #1: 立刻冲 RAG architecture** (立刻冲去讲 RAG 架构)

> "Sure, I'd ingest compound data + assays + patents into a vector DB, use Anthropic Claude API with prompt caching, add reranker, build a Slack bot..."

死. 你**没问**:
- 化合物数据是 **public domain** (FDA filed) 还是 **trade secret pre-filing**? 这是天差地别
- 用 commercial API 是否违反内部 IP policy? (大药企经常禁)
- 临床试验数据 (BLA / NDA 涉及) 跟 prescriber 数据有 HIPAA 合规
- 用户是 medicinal chemist / biologist / regulatory / IP attorney? 各自需求完全不同
- 跨国 (欧盟 GDPR + 中国 PIPL + 美国) 是否要求 data residency?

**挂法 #2: 假设 self-host vs API 是技术选择** (以为自托管 vs API 是个纯技术选择)

> "We can use OpenAI API, it's the most cost-effective."

死. 在大药企**这是 legal + IP 决策, 不是技术决策**. 候选人没意识到 → 整个 architecture 假设破产.

**挂法 #3: 把 IP attorney 当 "blocker" 而不是 partner** (把专利律师当"拦路虎"而不是合作伙伴)

> "We'll work around legal."

死. IP attorney 在大药企**是 sponsor 之一**. 把他们当 blocker = 项目政治上死.

---

## 完美答案架构 (5 步)

### Step 1: 澄清问题 (10 min)

> "Before I sketch, I want to ask 10 things. The reason: pharma is the **most IP-sensitive industry** I work with, and the answer depends entirely on data sensitivity + user role + jurisdictional constraints. None of these are software questions."

**10 个 clarifying questions**:

> **Q1**: "Who is the **primary user**? Medicinal chemist? Biologist? Regulatory affairs? IP attorney? Each role has different queries, different data access, different risk tolerance. 'Researcher' is too broad."

> **Q2**: "**Data classification tiers**: what's public (FDA-filed, published patents), what's confidential (active program but no IP filed), what's trade-secret (pre-filing, lead optimization)? Each tier likely has different policy on AI ingestion."

> **Q3**: "Is **commercial AI API** allowed by IP policy? Or must this run **self-hosted** (no data leaves company perimeter)? **This is THE architecture-determining question** and is a legal/IP call, not technical."

> **Q4**: "Are there **jurisdictional data residency** requirements — EU GDPR / SCC, China PIPL, US state laws (CCPA / NYSHIELD)? Pharma is global; can data move across borders?"

> **Q5**: "What's the **regulatory exposure** of the use case? Querying compound library for pre-research = low. Querying clinical trial efficacy data = high (could be deemed 'promotion' under FDA / EMA rules if leaked). Querying adverse event database = HIPAA + 21 CFR Part 11."

> **Q6**: "**Is the goal exploration or evidence**? Exploration ('show me molecules similar to X') is brainstorming, LLM is fine. Evidence (deciding to terminate a $500M program) needs deterministic citation + reproducibility."

> **Q7**: "Are you **already FDA-validated** for any AI? 21 CFR Part 11 + GxP + EMA AI policy mean some AI usage requires formal validation. **Is this 'validated' use or 'non-validated' (R&D only)?**"

> **Q8**: "Who has **veto** — Chief Medical Officer? Chief Legal Officer? Chief Compliance Officer? IP team? Information Security? List them so I know who needs to sign off."

> **Q9**: "Is there a **previous failed AI deployment** at this company? (Often yes.) Why did it fail — IP leak, hallucination on assay, regulatory finding? That history shapes everything."

> **Q10**: "What's the **specific business value** they want — speeding lit review (low risk, easy), accelerating compound prioritization (medium risk, harder), automating clinical narrative generation (high risk, FDA-watched)? Per use case, the scope is different."

**面试官 likely 回答**:
- Primary user: medicinal chemists in **Oncology** therapeutic area, ~30 people in 1 site
- Data: compound library (mix of public + confidential pre-filing), assay results (confidential), patent literature (public + internal patent prep notes)
- API: commercial API **explicitly forbidden** by IP policy. Self-host or nothing.
- Residency: must stay in US for US program, EU for EU program (cross-border is veto)
- Regulatory: non-validated use only (R&D, no FDA submissions). If used in submission later, formal validation required.
- Exploration, not evidence (in v1)
- Veto: CMO + CLO + Chief IP Officer + InfoSec
- Previous attempt: 18 months ago, killed by IP leak (researcher pasted compound structure into ChatGPT, structure showed up in OpenAI's blog post months later — embarrassing). **The trauma is real**.
- Business value v1: speeding internal literature review + compound similarity search within library

→ **Real scope**: 90 days = pilot for 30 oncology medicinal chemists, self-hosted, internal data only, low-risk exploration use cases, IP + compliance team sign-off on architecture before pilot starts.

This is **NOT** "deploy AI assistant across the company". It's "**get one team using one carefully-scoped use case after IP + compliance say yes**".

---

### Step 2: 找干系人 + 成功指标 (10 min)

**Stakeholder map (pharma is heavy on veto)**:

| Stakeholder | 在意什么 | 对项目态度 | 我对他们的关键动作 |
|---|---|---|---|
| **Chief Medical Officer (CMO)** | Patient safety, GxP, regulatory | Cautious, wants validation path | Quarterly review, FDA AI guidance briefing |
| **Chief Legal Officer (CLO)** | Liability, contracts, exposure | Gates everything | Weekly during pilot, written architecture doc |
| **Chief IP Officer** | Trade secret protection, freedom-to-operate | **Highest veto, most trauma from past leak** | Daily during week 1, sign-off on every data class |
| **InfoSec / CISO** | Encryption, access control, breach | Approval needed | Network architecture, pen test |
| **Chief Compliance Officer (CCO)** | 21 CFR Part 11, GxP, FDA / EMA | Gates "validated use" | Pre-validation checklist for v2 |
| **Head of Research (Oncology)** | Speed of research, scientist productivity | **Champion / sponsor for pilot** | Weekly, demo to chemists |
| **Medicinal chemists (~30)** | Daily usability, time saved | **End users, ultimate veto via non-adoption** | Daily during pilot, office hours |
| **Patent attorneys** | Won't accidentally disclose pre-filing | Need consult | Ensure pre-filing data NOT in pilot v1 |
| **Internal Audit** | SOX-adjacent controls | Need approval for production | Audit log architecture |

**Key insight**: Chief IP Officer's **18-month-old trauma** (ChatGPT leak) is the **single biggest blocker**. They will **demand**: data stays within perimeter, audit log of every query, ability to redact / pull data, periodic re-review.

**Success metrics (3 layers)**:

**Layer 1 — Pilot KPIs** (Head of Research + chemists view):
- Time-to-answer for "compound similarity / lit review" queries (currently 30-60 min via SciFinder + manual, target < 5 min)
- Adoption: % of 30 chemists using weekly (target > 60%)
- Satisfaction: NPS from chemists (target > 30)

**Layer 2 — Compliance KPIs** (CLO / CIPO view):
- 0 IP leaks (binary)
- 0 hallucinated citations going into formal docs (track via audit log review)
- 100% audit log coverage of every query

**Layer 3 — Strategic** (CEO / board view):
- Time-to-clinical-candidate (lagging, 12-24 months)
- Cost per drug program (lagging)

**Counter-metrics (must not move negatively)**:
- Number of compliance findings during/after pilot
- Researcher complaints about restrictiveness ("this AI doesn't know anything useful")
- IP team workload (review queue)

**The framing**:

> "90 days is a pilot, not a launch. Success = (a) 30 chemists getting real value, (b) 0 IP / compliance incidents, (c) clear path to expand to 200+ chemists in month 4-6 and validated use in year 2."

---

### Step 3: 梳理输入数据 (10 min)

**Data inventory + classification (THE central artifact)**:

| Data type | Source | Classification | Pilot scope? | Rationale |
|---|---|---|---|---|
| **FDA-filed patents (own + competitor)** | PubMed, USPTO, internal Patent DB | **PUBLIC** | YES | Already disclosed |
| **Published literature (PubMed, etc)** | External | PUBLIC | YES | Standard lit search |
| **Internal patent prep notes (pre-filing)** | IP team docs | **TRADE SECRET** | **NO (defer to v2 after IP approval)** | Highest risk |
| **Compound library structures (cleared for disclosure)** | Internal LIMS | CONFIDENTIAL | YES (with controls) | Internal use OK |
| **Compound library structures (lead opt, pre-filing)** | Internal LIMS | **TRADE SECRET** | **NO (defer to v2)** | One leak = entire program exposed |
| **Assay results (cleared)** | LIMS | CONFIDENTIAL | YES | Standard |
| **Assay results (active lead optimization)** | LIMS | TRADE SECRET | **NO** | Same reason |
| **Clinical trial protocols (published)** | ClinicalTrials.gov | PUBLIC | YES | Already public |
| **Clinical trial raw data (BLA / NDA stage)** | Internal | **REGULATED + CONFIDENTIAL** | **NO (separate platform)** | GxP, separate compliance path |
| **Adverse event reports** | Pharmacovigilance DB | **HIPAA + 21 CFR Part 11** | **NO** | Different system, validation required |
| **HR / employee data** | HR | PERSONAL | NO | Not relevant |
| **Financial data** | Finance | CONFIDENTIAL | NO | Not relevant |

**Pilot v1 data scope**: ONLY public + confidential-cleared data. **No trade secret, no clinical trial raw data, no adverse events**.

**Data movement constraints**:
- All data stays within company perimeter (self-hosted LLM, no commercial API)
- US-data only for US oncology pilot (EU pilot would be separate)
- Audit log captures every query + every retrieved document

**Key gap / risk**:
- LIMS data isn't pre-classified by trade-secret status. **Someone has to label which compounds are pre-filing and which are cleared**. This is human work, not automation. Estimated 2 weeks.
- Patent prep notes are in Word docs on individual attorneys' laptops, not in any DB. Defer permanently to v2 if ever.

**Architecture implications**:
- **Must be self-hosted**: Llama 3 / Mistral / Anthropic claude on Vertex AI with PrivateLink (depending on what IP / InfoSec approves)
- **Likely choice**: Llama 3.1 70B fine-tuned + RAG over internal corpus, hosted on internal SageMaker / GPU cluster
- **Backup model**: smaller (8B) for cost / latency optimization, with re-ranker
- **Vector DB**: self-hosted (Vertex AI Vector Search / Weaviate), NOT Vertex AI Vector Search (multi-tenant SaaS, IP team won't approve)

---

### Step 4: 拆成可解子问题 (15 min)

> "Now decomposition. The unique thing about pharma is the **'easy' subproblems are legal/compliance, the 'hard' subproblems are model quality on chemistry-specific queries**. Both have to be solved."

**9 subproblems**:

| # | 子问题 | Risk | Value | 90-day pri |
|---|---|---|---|---|
| **A** | **IP + Compliance sign-off**: architecture review, data classification, audit log design | Critical | Gates everything | **1 (week 1-3)** |
| **B** | **Self-hosted LLM stack**: model selection, infra, deploy | Medium | Foundation | **2 (week 1-4)** |
| **C** | **Data ingestion + classification labeling**: only cleared data, with provenance | High | Foundation | **3 (week 2-6)** |
| **D** | **RAG over chemistry corpus**: retrieval that handles SMILES + chemical names + assay vocabulary | Medium | High | **4 (week 4-8)** |
| **E** | **UI + workflow integration**: Slack? web? embed in existing tools? | Low | Medium | **5 (week 6-10)** |
| **F** | **Citation + provenance**: every answer cites source documents | Medium | High (audit) | **6 (week 6-10)** |
| **G** | **Hallucination detection on chemistry-specific outputs** | High | High | **7 (week 8-12)** |
| **H** | **Pilot run + iteration**: 30 chemists, weekly retros | Low | Critical | **8 (week 10-13)** |
| **I** | **Validated use path (for v2)**: 21 CFR Part 11 documentation framework | High | Future | Document, don't ship in 90 days |

**Sequencing rationale**:

> **A first** because: without IP + compliance sign-off, **everything else is wasted work**. Spend week 1-3 in meetings with CIPO, CLO, CCO, InfoSec. **No code merge before week 2**.

> **B parallel with A** because: while legal is reviewing, our infra team can stand up self-hosted Llama on internal GPU cluster. This is approvable in parallel.

> **C requires data classification labels** which is human work — defer until week 2 when classification is approved.

> **D-F build on B + C**.

> **G is the unique pharma technical risk**: hallucinating a compound structure or assay result. Need eval set + classifier.

> **I documented but not shipped** — validated use is year 2.

---

### Step 5: Walking-skeleton MVP (15 min)

**Walking-skeleton (Week 1-4)**:

```
Week 1: Legal + IP + Compliance meetings (NO code)
Week 2: Self-hosted Llama 3.1 stood up on internal AWS, basic prompt eval
Week 3: Public-only RAG (PubMed lit search), tested by FDE team
Week 4: Show to Head of Research with 5 sample queries (lit search only)
```

**Walking-skeleton has ZERO confidential data in v1**.

**Why**:
- **Risk mitigation**: if anything leaks during the demo, it's already public data
- **Architectural proof**: shows the stack works end-to-end without IP exposure
- **Buy-in from chemists**: even just lit search faster than SciFinder is value
- **Trust building with IP team**: see system works without touching their crown jewels

**Phase 2 (Week 5-8) — Add Confidential Internal Data**:

After IP team approves the architecture review:
- Ingest "cleared compound library" data
- Add "cleared assay results"
- Run pilot internally with 5 friendly chemists (not full 30 yet)

**Phase 3 (Week 9-13) — 30-Chemist Pilot**:

- All 30 oncology chemists onboarded
- Weekly retro with researchers + IP team
- Daily audit log review by InfoSec
- Bi-weekly checkpoint with CMO / CLO

**Phase 4 (Month 4-6) — Expansion**:

- Other therapeutic areas
- Expand data scope (with re-classification)
- Begin validated-use documentation framework

**Phase 5 (Year 2) — Validated Use**:

- 21 CFR Part 11 documented validation
- Used in regulatory submissions

---

## 详细回答 (Sample 60-min monologue)

> "Before I sketch, I want to ask 10 things. Pharma is the most IP-sensitive industry I work with, and the architecture depends entirely on data classification + IP policy + jurisdictional constraints. These are legal, not software, questions.
>
> *(asks 10 Qs)*
>
> *(gets answers: 30 oncology chemists, self-hosted only, no commercial API, US-only, non-validated R&D use, exploration-not-evidence, CIPO has highest veto, previous ChatGPT leak trauma 18 months ago, low-risk lit search + compound similarity)*
>
> OK so real scope: **90 days = pilot for 30 oncology chemists. Self-hosted. Internal data only. Low-risk exploration use cases. Sign-off from IP / Compliance / Legal before any data ingest**.
>
> This is **NOT** 'deploy AI assistant across the company'. It's 'get one team using one carefully-scoped use case after IP + compliance say yes'.
>
> **Stakeholders**: CIPO has highest veto — and they're traumatized by 18-month-old ChatGPT leak. CLO and CMO gate compliance. Head of Research (Oncology) is sponsor. 30 medicinal chemists are end users.
>
> **Key insight**: 60-70% of the 90 days is **legal / compliance / IP review work**, not technical. Week 1-3 is meetings, not code.
>
> **Data classification table** (I'd want to show this in the first review):
>
> - **Public** (PubMed, USPTO patents): YES in pilot
> - **Confidential cleared** (cleared compound library, cleared assays): YES in pilot
> - **Trade secret** (pre-filing structures, lead opt assays, patent prep notes): **NO, defer to v2 after IP approval**
> - **Regulated** (clinical trial raw, adverse events): NO, separate validated platform
>
> **9 subproblems**:
>
> 1. **IP + Compliance sign-off** (gates everything, week 1-3, no code yet)
> 2. **Self-hosted LLM stack** (parallel, week 1-4, Llama 3.1 70B on internal AWS)
> 3. **Data ingestion + classification** (week 2-6)
> 4. **RAG over chemistry corpus** (handles SMILES + chemical names)
> 5. **UI / workflow integration**
> 6. **Citation + provenance**
> 7. **Hallucination detection on chemistry outputs** (unique pharma risk)
> 8. **Pilot run + iteration**
> 9. **Validated use documentation** (year 2, just framework)
>
> **Walking-skeleton Week 1-4**: NO confidential data. Public-only RAG (PubMed). Demos that the stack works end-to-end without IP exposure. Trust-build with IP team.
>
> **Phase 2 Week 5-8**: add cleared confidential data after IP signs off. Pilot with 5 friendly chemists first.
>
> **Phase 3 Week 9-13**: full 30-chemist pilot, weekly retro with researchers + IP team.
>
> **Three things to flag proactively**:
>
> **(a) Self-hosted is non-negotiable**. Commercial API is forbidden by IP policy. Llama 3.1 / Mistral on internal AWS, with PrivateLink. Vertex AI Vector Search is out, Vertex AI Vector Search / Weaviate self-hosted are in.
>
> **(b) Trade secret data is DEFERRED**. Pre-filing compound structures + patent prep notes are the highest-risk data and adding them to pilot v1 = repeat of the ChatGPT leak trauma. IP team will block. Defer to v2 after pilot proves architecture.
>
> **(c) Chemistry-specific hallucination is the technical risk**. LLM will make up compound structures + assay values if not constrained. Need (1) RAG forcing answers to cite retrieved documents, (2) refusal when retrieval is weak, (3) eval set of 'gotcha' chemistry questions that the model should say 'I don't know' on, not hallucinate.
>
> Want me to deep-dive the IP sign-off process, self-hosted architecture, or hallucination defense?"

---

## Gao Xin 简历专属 reframe

This is the most regulator-heavy scenario in the 5 decomposition cases, and your **Indonesia OJK + Vietnam SBV + Thailand BoT** experience translates directly:

> "I had this pattern at TikTok PayLater across 7 markets. Each market regulator (OJK in Indonesia, BACEN in Brazil, CNBV in Mexico, etc.) had **different requirements about what data could be processed by AI and where**. Some required data residency, some restricted certain AI applications entirely, some required pre-approval.
>
> **The 5-step that worked**:
>
> 1. **Clarify**: I learned to ask 'what's the regulatory framework' BEFORE 'what does the product do'. In Indonesia, OJK's Fintech P2P regulation explicitly required certain decisioning logic to be **deterministic and auditable**, not pure ML. That constraint shaped architecture before any model selection.
>
> 2. **Stakeholder map**: per market, the regulator's compliance officer was a stakeholder. Plus our internal Legal + Compliance + Product. Plus the local market General Manager. **Treating regulators as partners, not blockers, was the unlock**.
>
> 3. **Data classification**: I built a per-market data classification matrix similar to what I'd build for pharma here. Some data could go through LLM (e.g., open-ended customer chat for empathy), some couldn't (e.g., credit decisioning required deterministic logic).
>
> 4. **Decompose**: scope reduction was constant. The version we eventually shipped to OJK was 1/3 of what product team originally wanted. The remaining 2/3 went to a v2 / v3 roadmap with regulator co-design.
>
> 5. **Walking-skeleton**: in Indonesia, I shipped a **voice agent that could only do 3 things initially**: (a) confirm identity, (b) share payment due date, (c) escalate to human if customer said anything beyond these. OJK approved it because the scope was clearly bounded and auditable. Then we expanded one capability at a time, each with re-approval.
>
> The pattern that transfers to pharma: **scope reduction is the FDE's job**. The customer wants 'AI assistant for everything'. The right v1 is 'PubMed lit search and cleared compound similarity for 30 chemists in oncology, defending IP team's veto with explicit data exclusions'.
>
> Also — I've shipped to a customer who had **previous-AI-deployment trauma** before (a market where a previous vendor had a chatbot leak issue). I know the conversation: validate the trauma, name it, explicitly architect to make that specific failure impossible, demo before launch. Don't hand-wave 'we're different'."

**Other resume hooks**:

- **ConvFinQA negative-result ablation** — you've done careful eval to figure out what really matters. Chemistry-specific hallucination eval is the same craft, different domain.
- **Internal Agent Platform onboarding multiple teams** — you've negotiated scope reduction with multiple internal customers, this is the same skill.

---

## 5 个 Follow-ups

**Q1**: "What if IP team rejects self-hosted Llama because 'open-source models could have unknown data in their training set'?"

**A**: This is a legitimate concern (theoretical data leakage from training set into outputs). Mitigations:

- **Use a model with documented training data** (e.g., Mistral's training data is more documented than some)
- **Add output filter**: post-generation classifier that checks if output contains anything that looks like a specific compound structure or company name not in retrieved context
- **Use retrieval-grounded generation** with strict requirement that response must cite retrieved documents (no free-form generation)
- **Run dedicated red-team** before launch: probe model with "tell me about [competitor's compound]" and verify it doesn't reveal training-leaked info

If IP team still rejects: **escalate to alternatives** like running a smaller in-house-trained model on company data only. Slower to ship, but if that's what they need, accommodate.

**Q2**: "What if researchers complain pilot is too restrictive ('it doesn't know any of the interesting compounds')?"

**A**: This is the **value vs IP tension**. Diagnose first:

- **What specific queries are failing?** Get examples. Often it's something we can add (e.g., compound is already in public patent, just not in our ingestion).
- **Categorize complaints**:
  - "I need to query trade-secret data" → "We're working on v2 IP approval, here's the timeline. Use case is logged."
  - "Lit search results are slow / bad" → fix retrieval
  - "It hallucinated a structure" → reproduce, add to eval set, fix
- **Don't expand scope unilaterally**. Bring complaints to IP team in weekly retro. Let IP team decide what to add.
- **Set expectations early**: in onboarding, tell chemists "v1 is limited by design, here's what's in scope, here's what's coming, here's how to log requests".

**Q3**: "What's your audit log architecture? IP team wants to know."

**A**: Every query logs:
- User ID + role
- Timestamp
- Raw query text
- Retrieved documents (IDs + chunks)
- Generated response
- Token counts
- Latency
- User feedback (thumbs up/down)
- Trust score (model confidence)

**Storage**: append-only, immutable, separate from main app DB, retained 7 years (matches pharma standard).

**Access**: IP team + InfoSec + Internal Audit have read access. Searchable by user, by query keywords, by retrieved document. Daily aggregate report sent to IP team.

**Red flag detection**: query containing competitor names, query mentioning pre-filing keywords, query returning trade-secret-tagged document — all auto-flagged for IP team review.

**Q4**: "Why not just use Anthropic's enterprise tier with HIPAA-compliant + zero-retention API?"

**A**: Good question, and worth raising with IP team because the tradeoff matters:

- **Pro**: faster to ship, better model quality, lower infra burden
- **Pro**: enterprise tier doesn't retain customer data, doesn't train on customer data
- **Con (IP team view)**: data physically leaves company perimeter. If Anthropic has a breach, our compound structures are in third-party hands.
- **Con**: legal exposure analysis required (BAA-equivalent for pharma data + IP indemnification)
- **Con**: if our regulator (FDA, EMA) audits and asks where the data was processed, "third party" answer is harder than "internal cluster"

**If IP team open to this path**: pursue it as a parallel track. Could ship faster. But **respect the 18-month-old trauma** — they may need 6 months of architecture review + Anthropic team meetings + indemnification negotiation before saying yes.

**My default recommendation**: start with self-hosted for fast pilot approval, document the API alternative as v2 if pilot proves value and IP team comfort grows.

**Q5**: "How would you scope this differently if it were 30 days instead of 90?"

**A**: 30 days is too short for any data ingestion + IP review. Would scope to:

- **Day 1-7**: Just legal + IP review meetings. No code.
- **Day 8-21**: Self-hosted Llama stood up. Public-only RAG (PubMed). Demo internal.
- **Day 22-30**: Demo to Head of Research + 3 friendly chemists. NO production. NO confidential data. **Decision point**: is the company committed to a longer engagement?

**30 days delivers**: architecture review approval, working public-data demo, friendly-chemist feedback. **NOT** production pilot.

This is honest scoping. Customers who insist on 30-day production in pharma are unrealistic and that's a project I'd politely decline.

---

## ❌ 死路答法 (top 7)

1. **冲 RAG architecture** without checking commercial-API policy
2. **Assume self-host vs API is technical** (it's legal)
3. **Treat IP attorney as blocker** instead of partner
4. **Skip data classification** (one-size-fits-all data ingest)
5. **Include trade secret in pilot v1** (repeats the leak trauma)
6. **Promise 100% accurate** (chemistry hallucination is real)
7. **Don't budget time for legal review** (60-70% of 90 days is non-code)

---

## ✅ 加分项 (top 7)

1. **Data classification table** as a central artifact
2. **Self-host explicitly defended** as not-just-default
3. **Validate IP team's past trauma** ("18-month ago leak") explicitly
4. **Walking-skeleton with public-only data** in week 1-4
5. **Defer trade secret to v2** with documented criteria
6. **Audit log architecture** with red-flag detection
7. **Quote your Indonesia OJK / multi-regulator experience**

---

## 一句话总结

> **Pharma AI 部署 = "60% legal/IP/compliance, 40% engineering" + "data classification BEFORE architecture" + "scope reduction is your job"**.
>
> 真正的 win 不是大 RAG, 是**让 30 个 oncology 化学家 6 个月内日常用上、0 IP incident, 同时为 v2 expansion 留路径**. 防止 "ChatGPT 那次的事" 再发生比任何模型 metric 都重要.

---

## Cheat Sheet

```
不要做:
  - 冲 RAG / vector DB design
  - 假设 commercial API 可用
  - 把 IP team 当 blocker
  - 跳过 data classification
  - V1 含 trade secret
  - 承诺 100% 准确
  - 低估 legal review 时间

要做 (5 step):
  1. Clarify (10min): 10 Q, 锁数据敏感度 + API policy
  2. Stakeholder: CIPO 最大 veto, 验证 trauma
  3. Data: 4 tier 分类表 (public / confidential / trade secret / regulated)
  4. Decompose: 9 subproblem, IP sign-off 第一
  5. MVP: 4 周 walking-skeleton, 公开数据 only

Clarify Q 必问:
  - 用户角色 (chemist / biologist / regulatory / IP)?
  - 数据 tier (public / confidential / trade secret / regulated)?
  - Commercial API 允许吗?
  - Jurisdictional residency?
  - Regulatory exposure (validated / non-validated)?
  - Exploration vs evidence?
  - Veto 谁?
  - 过去失败案例?
  - 具体 use case (lit search / similarity / generation)?

Veto holders:
  - Chief IP Officer (highest, trauma)
  - CLO
  - CMO
  - CCO
  - InfoSec
  - Head of Research (sponsor)

Data classification (THE artifact):
  Public (PubMed, USPTO): pilot YES
  Confidential cleared (LIMS cleared): pilot YES
  Trade secret (pre-filing): pilot NO, defer v2
  Regulated (CT raw, AE): NO, separate platform

Architecture (IP-forced):
  Self-hosted Llama 3.1 70B or Mistral
  Internal AWS / SageMaker
  Vertex AI Vector Search / Weaviate self-host (NOT Vertex AI Vector Search)
  PrivateLink, no public internet egress
  Audit log immutable 7 yr

9 subproblems:
  1. IP + Compliance sign-off (1st, gates all)
  2. Self-hosted stack (parallel)
  3. Data ingest + classify
  4. RAG over chemistry
  5. UI / workflow
  6. Citation / provenance
  7. Chemistry hallucination defense
  8. Pilot run + iterate
  9. Validated use doc (yr 2)

Walking-skeleton Week 1-4:
  Week 1: legal/IP/compliance meetings, NO code
  Week 2: Llama self-hosted internal
  Week 3: Public-only RAG (PubMed)
  Week 4: Demo to Head of Research

Phase plan:
  W1-4: legal + public-data MVP
  W5-8: confidential-cleared data, 5 friendly chemists
  W9-13: 30-chemist pilot
  M4-6: expansion
  Yr 2: validated use

Trauma handling:
  "18-month-ago ChatGPT leak":
   - Acknowledge explicitly
   - Architecture to make that failure impossible
   - Demo before launch
   - Don't hand-wave "we're different"

Hallucination defense (chemistry-specific):
  - RAG forces citation
  - Refuse when retrieval weak
  - Eval set of "gotcha" questions
  - Output filter for compound structures
  - Red team before launch

Audit log fields:
  user_id, role, timestamp, query, retrieved_docs,
  response, tokens, latency, feedback, confidence
  red-flag detection: competitor names, pre-filing keywords,
                      trade-secret tag retrieval

Resume quote:
  "TikTok PayLater 7 markets — each regulator
   different framework. OJK Indonesia required
   deterministic decisioning. I scope-reduced product
   by 2/3, shipped narrow v1, expanded with re-approval.
   Same scope-reduction-is-FDE-job pattern."

Key phrases:
  - "Before I sketch, 10 questions..."
  - "60-70% of 90 days is legal review, not code"
  - "Self-host is non-negotiable per IP policy"
  - "Trade secret deferred to v2"
  - "Walking-skeleton: public-only data, week 1-4"
  - "Validate the past leak trauma explicitly"
```
