## Q35 · 保险公司 3000 万历史理赔 LLM 摘要 (多州监管约束)

> "An insurance company wants to use **LLM to summarize 30 million historical claims** for downstream actuarial / legal / customer-service use. They operate across **all 50 US states**, each with its own insurance regulator. **How would you scope this in 60 minutes?**"

**中文翻译**:

> "一家保险公司想用 **LLM 把 3000 万条历史理赔 (claim) 做 summary (摘要)**, 给下游精算 (actuarial) / 法务 / 客服用. 他们业务覆盖 **全美 50 个州**, 每个州有自己的保险监管. **你怎么在 60 分钟内 scope (定范围) 这个项目?**"

**Round**: Decomposition Case (60 min)
**出处**: Exponent 2026 FDE · Palantir + OpenAI Enterprise + Anthropic insurance vertical
**行业**: Insurance / regulated data / large-scale ETL

---

## 📖 术语速查 (本题用到的)

> 保险术语 + 50 州监管 + 大规模 LLM 批处理. 5 min 速查.

### 保险行业核心

| 术语 | 解释 |
|---|---|
| **Claim (理赔)** ⭐ | 保险事件 — 用户出险后向保险公司提交的赔付申请. 完整 claim 包含 ACORD 表 + 调查员笔记 + 警察报告 + 医疗记录 + 修理估价 + 照片 + 录音陈述. 这题 30M 件. |
| **LOB (Line of Business)** ⭐ | 保险险种 — Auto / Homeowners / Health / Life / Workers Comp / Commercial. 每个 LOB schema + 监管 + 用户都不同, **不能混着 v1**. |
| **Personal auto** | 个人车险 — 美国最大 LOB. 这题 v1 锁定. |
| **Actuary / Actuarial team** ⭐ | 精算师 / 精算团队 — 用历史 claim 数据建模预测未来 loss, 决定 premium 定价. 这题 primary user. |
| **Underwriting** | 核保 — 决定是否承保 + 价格. |
| **Reserves** | 准备金 — 已知 claim 但还没结清的预估金额. 监管要求. |
| **Reinsurance / Treaty pricing** | 再保险 / 条约定价 — 保险公司给保险公司投保. |
| **Subrogation** | 代位求偿 — 我赔了客户, 我去找责任方追偿. |
| **Loss amount / Fault attribution** | 损失金额 / 责任归属 — claim 关键事实. |
| **Rate filing** | 保费定价文件 — 保险公司必须向州 DOI 申报费率. AI-derived 输入会被审查. |

### 文档 / 数据格式

| 术语 | 解释 |
|---|---|
| **ACORD form** | 美国保险行业标准化的 claim 表单. 结构化, 干净, 易处理. |
| **Adjustor notes (调查员笔记)** | claim 调查员手写 / 打字的笔记 — 自由文本, 缩写 + 主观意见混事实. 50% claims 的内容. |
| **Police report** | 警察报告 — PDF 扫描件, 含第三方 PII. |
| **Medical record (bodily injury)** | 医疗记录 — HIPAA 保护, 单独 pipeline. |
| **Recorded statement** | 录音陈述 — claimant + 证人, recording-consent law 各州不同. |
| **Repair estimate** | 修理估价 — 来自维修厂. |
| **Reserves history** | 准备金历史 — 时间序列, 每次估价调整. |

### 50 州监管

| 术语 | 解释 |
|---|---|
| **DOI (Department of Insurance)** ⭐ | 美国各州保险监管局 — 50 个州 50 个 DOI, 各有自己的规则. **跟联邦无关**. |
| **NAIC (National Association of Insurance Commissioners)** | 全国保险监管协会 — 制定 model law (模板法), 各州可改可加. |
| **NY DFS (Department of Financial Services)** | 纽约金融监管 — 最严, 2024 出 AI 在保险中的 model regulation. |
| **CA DOI** | 加州保险监管 — 第二严, AI used in consumer-impact decisions 必看. |
| **TX TDI / FL** | 德州 / 佛州监管 — 较 lenient. |
| **Algorithmic accountability report** | 算法问责报告 — NY DFS 2024 directive 要求 AI 处理客户数据必须提交. |
| **Explainable AI documentation** | 可解释 AI 文档 — 部分州要求 rate filing 用 AI 输入时必交. |
| **Disparate impact / Bias eval** | 差别影响 / 偏见评估 — NAIC + 多州盯, AI 输出对不同人群是否有系统性偏差. |
| **Right to know** | "知情权" — 部分州要求消费者知道 AI 是否影响了他们的 underwriting. |

### 数据保护 / 法律

| 术语 | 解释 |
|---|---|
| **HIPAA** | 医疗隐私法 — 医疗记录走单独 pipeline. |
| **GLBA (Gramm-Leach-Bliley Act)** | 金融隐私法 — 金融机构客户数据保护. 保险适用. |
| **Attorney-client privilege (律师-客户特权)** ⭐ | 律师-客户通讯不可被强制披露. **一份 privileged 文件进 LLM = 对方律师可主张 privilege waived = 灾难**. 必须分类排除. |
| **PII (Personally Identifiable Information)** | 个人可识别信息 — SSN, DL, 地址. 进 LLM 前必 redact. |
| **PHI (Protected Health Information)** | 受保护健康信息 — HIPAA 定义, 比 PII 更严. |
| **Recording-consent law** | 录音同意法 — 各州不同: One-party (1 方同意即可) vs Two-party (双方都得同意, 如加州). |
| **BAA (Business Associate Agreement)** | HIPAA 框架下的合规合同. 用 commercial API 必谈. |
| **DPA (Data Processing Agreement)** | 数据处理合同. |

### LLM / 系统架构

| 术语 | 解释 |
|---|---|
| **Claude on AWS Bedrock + PrivateLink** | 私有部署 Claude — 数据不走公网, 中等合规适用. |
| **Llama 3.1 70B fine-tuned** | 自托管开源模型. |
| **Prompt caching** ⭐ | 提示缓存 — 相同 prompt 前缀的 token 缓存复用, 大幅降本. Batch 处理必用. |
| **Citation tracking** ⭐ | 引用追踪 — 每个 fact 必须 trace 回源文档的 paragraph + sentence. 这题 non-negotiable, hallucination = 监管曝光. |
| **Sub-paragraph granularity** | 引用必到段落 + 句子级, 不能仅 doc 级. 人能秒级验证. |
| **Hallucination (幻觉)** | LLM 编造源文档没的事实. Claim summary 里 = 法律 / 监管曝光. |
| **Stratified sampling (分层采样)** | 按 state + claim type + severity 分层抽样, 保证 pilot 代表性. 这题 100K 抽法. |
| **RAG (Retrieval-Augmented Generation)** | 检索增强生成 — LLM 先检索源文档再生成. |
| **Dense vs sparse retrieval** | 向量检索 vs 关键词检索 — recall@k 关键指标. |
| **Tiered model use** | 分层模型 — 简单 claim 用 8B 小模型, 复杂用 70B / Claude. 省钱. |
| **Stratified evaluation** | 分层评估 — 按 demographic / 文档类型分群验证, 找 bias. |

### 方法论 / 流程

| 术语 | 解释 |
|---|---|
| **Use case scoping** | 用例聚焦 — 1 LOB + 1 user, 不要 5M 同时多 use case. 这题 v1 = Actuarial + Personal Auto + 10 states. |
| **Walking skeleton** | 端到端最薄版, 100 claim + 1 state + 手动 review. |
| **Pilot before batch** | 先 pilot 后批量 — 100K 验证, 5M 批量. |
| **Human-in-loop** | 人工复核 — 异常 case 人审, actuarial 关键决策必含. |
| **Negative-result ablation** | 消融实验 — 系统性拆解 retrieval × prompt × model × CoT 各 component 的贡献. Gao Xin ConvFinQA 经验. |

### 角色

| 术语 | 解释 |
|---|---|
| **Chief Actuary** | 首席精算师 — 这题 sponsor. |
| **General Counsel (GC)** | 总法律顾问 — 管 privilege + 诉讼风险. |
| **CCO (Chief Compliance Officer)** | 首席合规官 — 管 50 州监管. |
| **State DOI engagement officer** | 州 DOI 关系官 — 跟 CA / NY DFS 沟通的内部岗位. **不能跳过**. |
| **CISO** | 信息安全官. |

---

## 这道题在考什么

**不是**: 考你能不能 estimate LLM cost.

**是**: 考你能不能克制 **"30M × $0.05 = $1.5M for LLM cost"** 的反射性回答, 先去问 **"为什么要 summary? 谁用? 哪种 use case?"**

4 个 signal:

1. **Don't estimate cost first** (别一上来估成本) — 90% candidates 立刻算 token cost. Real win: ask **what downstream use needs summary**? (下游谁要用 summary?) Actuarial wants different summary than legal vs CS.
2. **Per-state regulatory variance is HUGE** (按州监管差异极大) — California ≠ Texas ≠ NY. NAIC model law + state amendments + state DOI directives. Can't treat as monolithic (不能当成铁板一块)
3. **Sample for pilot, NOT batch everything** (先抽样做 pilot, 不要一次全 batch) — running 30M through LLM = $1M-5M of compute. Sample 100K stratified (分层抽样 100K), prove value, batch later
4. **Citation-required output** (输出必带引用) — claims = legal evidence. Every summary must cite source claim file paragraphs, hallucination (幻觉) = legal exposure

---

## ❌ 最常见的挂法

**挂法 #1: 立刻冲 LLM cost estimate** (立刻冲去估 LLM 成本)

> "30M claims × ~500 tokens × $0.005/1K = $750K, plus storage and indexing..."

死. 你**没问**:
- Summary 给谁用 (actuarial 模型输入? Legal e-discovery? CS deflection?)
- 每个 use case 需要什么粒度的 summary (1-line vs 500-word)
- 不同 use case 是否可共用同一个 summary
- 哪些 claim 类型最有价值 (auto > life > homeowners > workers comp 等)
- 50 个州对 AI processing claim 数据的合规要求

**挂法 #2: 把它当 batch ETL 题做** (把它当批量 ETL 系统设计题答)

> "30M claims, peak 50 TPS to LLM, distribute across 100 workers, total time 5 days..."

死. 当 system design 题做 = miss the point. 这道题考的是 scope discipline.

**挂法 #3: 假设 1 个 universal summary 适合所有 use case** (以为一个万能 summary 能满足所有用户)

> "We'd generate a 200-word summary per claim, store, and query."

死. Actuarial 用结构化 fields, 不是 narrative. Legal 需要 timeline + key facts + parties. CS 需要 status + next action. 你 generate 1 个 generic 等于没 generate.

---

## 完美答案架构 (5 步)

### Step 1: 澄清问题 (10 min)

> "Before I sketch, 10 questions. The key issue: 30M claims is a big number, but **'summarize' means 5 different things** to 5 different downstream users."

**10 个 clarifying questions**:

> **Q1**: "**Who's the downstream user**? Actuarial (modeling future loss)? Legal (e-discovery, dispute review)? Customer service (status lookup, deflection)? Underwriting (risk assessment)? Reinsurance (treaty pricing)? Fraud (pattern detection)? **Each needs different summary structure**."

> **Q2**: "What's the **business value** for each user? Actuarial saving X hours? Legal saving Y in litigation prep? CS deflection rate +Z%? Without value attributed to use case, we can't prioritize."

> **Q3**: "**Per-state regulatory**: NY DFS + CA DOI + TX TDI etc each has guidance on AI processing of claim data. Some states require **algorithmic accountability reports**. Have you mapped state-by-state requirements?"

> **Q4**: "**PII / PHI handling**: claims contain medical records (workers comp, health), driver's license + SSN (auto), property valuations. **HIPAA + GLBA + state privacy laws**. What's your current data classification?"

> **Q5**: "Is this **all lines of business** (auto, homeowners, commercial, life, health, workers comp) or one line? **Each has different schema, different regulator, different downstream user**."

> **Q6**: "What's the **target use case for v1** — actuarial 1 LOB seems most tractable, vs all-LOBs-all-use-cases."

> **Q7**: "**Latency requirement** — real-time on new claims (every claim summarized as it closes) vs **batch historical** (process 30M backlog once)? **The first is operations, the second is research**."

> **Q8**: "Are there **previous AI deployments** (e.g., claim adjustor chatbot, fraud ML)? Reputation history shapes this project."

> **Q9**: "What's the **document format** — structured (ACORD claim forms), semi-structured (claim adjustor notes), unstructured (medical records PDFs, photos)? **Each requires different ingestion**."

> **Q10**: "**Veto holders**: General Counsel, Chief Actuary, Chief Compliance Officer, state DOI compliance team, CISO, IT director?"

**面试官 likely 回答**:
- Use case v1: **Actuarial modeling** for **personal auto** in **top 10 states by claim volume** (representing 70% of claims)
- Business value: replace manual claim review (currently 3 hrs/claim for sampling 1% for model retraining)
- 10 states have varying rules; CA + NY most strict; some require **explainable AI** documentation for any model using AI-processed inputs
- PII: contains SSN, license, medical records, repair shop addresses. Currently in encrypted DB + RBAC + audit log
- LOB: scope to personal auto first (5M of the 30M claims)
- Latency: batch historical 5M backlog + then real-time on new closures
- Previous AI: fraud ML in production 3 years. **No customer-facing AI** yet. Conservative culture.
- Format: ~40% structured ACORD, ~50% adjustor notes (PDF/Word), ~10% medical records + photos
- Veto: GC + Chief Actuary + CCO + State DOI engagement officer

→ **Real scope**: in 90 days, build a **summarization pipeline for personal auto claims in 10 states**, producing **actuarial-structured summaries** with citations to source documents, sampling 100K for pilot validation before batching the 5M backlog.

NOT "summarize 30M claims for everyone".

---

### Step 2: 找干系人 + 成功指标 (10 min)

**Stakeholder map**:

| Stakeholder | 在意什么 | 对项目态度 | 我对他们的关键动作 |
|---|---|---|---|
| **Chief Actuary** | Model quality, actuarial defensibility | Primary sponsor | Weekly review, validation methodology |
| **General Counsel** | Litigation risk, attorney-client privilege | Gates everything | Architecture review, citation chain |
| **CCO** | State DOI compliance | Critical gate | State-by-state matrix review |
| **State DOI engagement officer** | Regulator relationships | Critical for blocked states | Pre-brief CA / NY DOI |
| **CISO** | Encryption, PII handling | Approval gate | Data flow + audit |
| **IT Director** | Cloud cost, integration with policy admin | Operational | Architecture + cost ceiling |
| **Actuarial team (50)** | Daily usability, model quality | End users | Pilot feedback loop |
| **Legal e-discovery team** | Phase 2 customer (litigation prep) | Watching | Future use case, not v1 |
| **Customer Service Director** | Phase 3 customer (deflection) | Future | Not v1 |
| **Internal Audit** | SOX-adjacent controls | Approval for production | Audit log architecture |

**Key insight**: **State DOI engagement is the silent risk**. NY DFS has issued AI directives (2024 model regulation). CA DOI follows up on AI used in consumer-impact decisions. Even if your use case is **internal actuarial**, if outputs influence pricing → state DOI cares. **Must pre-brief CA and NY DOI**.

**Success metrics (3 layers)**:

**Layer 1 — Pilot KPIs** (Chief Actuary):
- Actuarial reviewer agreement with LLM-extracted facts (target > 95% on key fields like loss amount, accident date, fault attribution)
- Time-to-summary per claim (manual 3 hrs → target < 1 min)
- Pilot ROI: hours saved × actuary hourly rate

**Layer 2 — Compliance KPIs**:
- 100% citation coverage (every claim in summary cites source paragraphs)
- 0 PII leakage in summaries
- 100% audit log of LLM calls (input, output, model version, prompt template version)
- State-by-state compliance check pass

**Layer 3 — Strategic** (CEO / board):
- Total actuarial efficiency gain
- Foundation for Phase 2/3 (legal, CS)

**Counter-metrics**:
- Hallucination rate (facts in summary NOT in source)
- Privilege violation (attorney-client communications in summary)
- State DOI inquiry count
- Actuarial team complaints

---

### Step 3: 梳理输入数据 (10 min)

**Data inventory**:

| Dataset | Format | Quality | Privacy tier | Notes |
|---|---|---|---|---|
| **Structured claim header (ACORD)** | DB | Clean | Medium | Loss type, amount, dates, parties |
| **Adjustor notes** | Text in claim system | Free-form, abbreviations | High | Personal opinion + facts mixed |
| **Police reports** | PDF attachments | Scanned, OCR'd | High | Includes other parties' PII |
| **Medical records (auto bodily injury)** | PDF | Scanned, varied quality | **HIPAA** | Restricted access |
| **Repair estimates / invoices** | PDF / structured | Semi-clean | Medium | Vendor data |
| **Photos (vehicle damage, property)** | Image | High | Medium | May contain license plates |
| **Recorded statements** | Audio + transcript | Transcript quality varies | High | Witness, claimant |
| **Litigation documents (subset)** | PDF | Varies | **Attorney-client privilege** | Filtered access |
| **Reserves history** | DB | Clean | Medium | Time-series |
| **Subrogation outcomes** | DB | Clean | Medium | Recovery from other carrier |

**Critical privacy fences**:

1. **Attorney-client privileged** documents must be excluded from LLM pipeline entirely. If even one privileged document goes into LLM, opposing counsel can argue privilege is waived. **Need separate ingestion classifier**.
2. **Other-party PII**: police reports name 3rd parties. Their PII may be subject to different state laws. **Need PII redaction layer**.
3. **HIPAA-protected health information** in bodily injury claims requires separate HIPAA-compliant pipeline.
4. **Recorded statements** include claimant + witness statements, governed by recording-consent laws (varies by state).

**Data movement constraints**:
- Self-hosted LLM strongly preferred (insurance is risk-averse like pharma)
- If using commercial API: requires BAA + DPA + indemnification
- Some states (e.g., NY DFS) require **algorithmic accountability documentation** for any AI processing customer data

**Architecture implications**:
- **Self-hosted LLM**: Claude on Bedrock (AWS PrivateLink) or Llama 3.1 70B fine-tuned
- **Privacy layer FIRST**: classifier separates privileged / HIPAA / standard claims, routes accordingly
- **Citation tracking**: every fact in output traces to a source paragraph (chunk ID + offset)
- **Per-state config**: model + prompt template differs by state per regulatory requirement

---

### Step 4: 拆成可解子问题 (15 min)

**10 subproblems**:

| # | 子问题 | Risk | Value | 90-day pri |
|---|---|---|---|---|
| **A** | **Use case scoping**: lock to 1 LOB + 1 user (actuarial + auto), defer rest | Low | Foundation | **1** |
| **B** | **Ingestion + privacy classification**: separate privileged / HIPAA / standard | High | Critical | **2** |
| **C** | **PII redaction layer**: SSN / DL / medical removed before LLM | Medium | Required | **3** |
| **D** | **Stratified sampling for pilot**: 100K of 5M, representative across states | Low | High | **4** |
| **E** | **LLM summarization with citations**: every fact traces to source | Medium | Critical | **5** |
| **F** | **Actuarial validation**: human reviews sample, agreement rate | Low | Critical | **6** |
| **G** | **State-by-state regulatory matrix**: per-state prompt + audit config | High | Critical | **7** |
| **H** | **Cost optimization**: model selection + prompt caching for batch | Low | High (financial) | **8** |
| **I** | **Batch infrastructure**: process 5M when pilot proven | Low | Future | Defer to month 4-6 |
| **J** | **Real-time on new claims**: hook into claim closure | Low | Future | Defer to month 6+ |

**Sequencing rationale**:

> **A first** because: scoping to 1 LOB + 1 user removes 80% of complexity. Actuarial-only-auto-only is the right v1.

> **B + C critical** because: getting privilege wrong = litigation exposure. Getting PII wrong = HIPAA + state law violation. Both must be solid before any LLM call.

> **D before batch** because: running 5M through LLM = $250K-$500K of compute, plus weeks of time, before knowing if output is useful. Sample 100K (stratified across states + claim types) for pilot → validate → batch.

> **E with citations** because: actuarial use of LLM output requires defensibility. Hallucinated fact in summary that gets into actuarial model = potential rate-filing challenge. Citation = trace + verify.

> **F validation** because: agreement rate with senior actuarial reviewer is the only credible metric.

> **G state matrix** because: CA + NY + WA = strict; some states require algorithmic accountability docs. **Per-state config**, not monolithic.

> **H cost optimization** matters because batch is $$$. **Caching common context + selective re-ranking + tiered model use (small for easy claims, large for complex)**.

> **I + J deferred** to month 4-6+ after pilot validates.

---

### Step 5: Walking-skeleton MVP (15 min)

**Walking-skeleton (Week 1-4)**:

```
Week 1: Use case scoping + GC + CCO + State DOI engagement officer meetings
Week 2: 100-claim sample, manual hand-tag "ideal summary"
Week 3: Self-hosted LLM stack + first prompt + citation tracking
Week 4: Show actuarial reviewer the 100-claim output, get agreement rate
```

**Walking-skeleton scope**:
- 100 claims, not 5M
- 1 state (e.g., Texas as least strict)
- Actuarial use case only
- Manual privacy review (no automated classifier yet)
- No batch infra
- No state-by-state config yet

**Why this works**:
- **Tiny cost** (~$10 of LLM compute)
- **Tight feedback loop** with actuarial reviewer
- **No PII exposure risk** at this scale (manual review)
- **Validates the hardest thing**: can LLM produce defensible summaries with citations?

**Phase 2 (Week 5-8) — Pilot Sampling**:

After walking-skeleton validates approach:
- Stratified 100K sample across 10 states + claim severity tiers
- Build privacy classification automation
- Build per-state prompt config
- Self-hosted LLM with cost projection

**Phase 3 (Week 9-12) — Validation Methodology**:

- 1000-claim stratified subset → 3 senior actuaries independently review LLM output
- Agreement rate by field (loss amount, fault, dates)
- Bias analysis: are LLM summaries systematically over/under-stating reserves?
- State DOI pre-brief: show CA + NY DOI the methodology

**Phase 4 (Month 4-6) — Batch the 5M**:

After phase 3 sign-off:
- Cost optimization: prompt caching, batch API, tiered model
- Distributed batch processing (5M / 5K/hr = ~6 weeks)
- Quality monitoring during batch

**Phase 5 (Month 7+) — Real-time + Expansion**:

- Hook into claim closure (real-time)
- Expand to other LOBs (one at a time)
- Expand to other use cases (legal, CS) — each is a re-scoping exercise

---

## 详细回答 (Sample 60-min monologue)

> "Before I sketch, 10 questions. The key issue: '30M claims' is a big number, but 'summarize' means 5 totally different things to 5 different users.
>
> *(asks 10 Qs)*
>
> *(gets answers: actuarial use case, personal auto, top 10 states, 5M of 30M claims, batch + real-time, conservative culture, GC + Chief Actuary + CCO veto)*
>
> OK so real scope: **90 days = pilot summarization pipeline for personal auto claims in 10 states, actuarial use case only, sampling 100K of 5M for validation before batch**.
>
> NOT '30M claims for everyone'. That's year 2+.
>
> **The reflex answer** that costs people the round: 'Let me estimate LLM cost. 30M × 500 tokens × $0.005/1K = $750K.' I won't lead with that.
>
> **Why scope matters more than cost**: running 30M through LLM = $1M-$5M of compute. **Before spending any of that, I need to know who uses the output, in what format, with what regulatory constraint**. Actuarial wants structured fields + reserves history. Legal wants timeline + parties. CS wants status. 1 generic summary fails all 3.
>
> **Stakeholders**: Chief Actuary sponsor, GC gates legal, CCO gates 10-state compliance, State DOI engagement officer is critical (CA + NY DOI will care about any AI processing). Conservative culture means slow + careful, not fast + scrappy.
>
> **Data sensitivity**:
> - Structured ACORD = clean, low risk
> - Adjustor notes = free text, opinion mixed with fact
> - Police reports = third-party PII
> - Medical records = HIPAA
> - Litigation docs = attorney-client privilege, MUST be excluded
> - Recorded statements = recording-consent law varies by state
>
> Privacy classifier is the FIRST production layer before any LLM call.
>
> **10 subproblems**:
>
> 1. Use case scoping (actuarial + auto only)
> 2. Ingestion + privacy classification (privileged / HIPAA / standard)
> 3. PII redaction
> 4. Stratified sampling 100K for pilot
> 5. LLM summarization with citations
> 6. Actuarial validation methodology
> 7. State-by-state regulatory matrix
> 8. Cost optimization (model selection, caching)
> 9. Batch infra (defer to month 4-6)
> 10. Real-time on new claims (defer to month 6+)
>
> **Walking-skeleton Week 1-4**:
>
> 100 claims, 1 state (Texas, least strict), manual hand-tag ideal summary, self-hosted LLM, citation tracking. ~$10 of compute. Show actuarial reviewer the 100-claim output, get agreement rate.
>
> If 95%+ agreement → expand to 100K stratified across 10 states.
>
> **Phase 2 Week 5-8**: 100K stratified sample, build privacy classification automation, per-state prompts.
>
> **Phase 3 Week 9-12**: 1000-claim subset validation with 3 senior actuaries, bias analysis, State DOI pre-brief.
>
> **Phase 4 Month 4-6**: batch 5M (after pilot signed off).
>
> **Three things to flag proactively**:
>
> **(a) Citation tracking is non-negotiable**. Every fact in summary traces to a source paragraph. Otherwise actuarial output uses LLM-hallucinated fact → rate-filing challenge → state DOI inquiry.
>
> **(b) Privilege classifier in ingestion**. One privileged document in LLM pipeline = opposing counsel argues privilege waived = catastrophe. Auto-classify + manual review for borderline.
>
> **(c) State DOI pre-brief in week 6-8, NOT after launch**. CA + NY DOI want to see methodology before you ship. Building the relationship is project insurance.
>
> Want me to deep-dive citation architecture, state regulatory matrix, or cost optimization?"

---

## Gao Xin 简历专属 reframe

The **ConvFinQA** project is directly relevant — that's where you did **multi-hop QA over financial documents with citation requirement**, exactly the structural problem here:

> "ConvFinQA was the most directly applicable project for this. I built multi-hop QA over financial reports — required structured answers with **citation back to source paragraphs**. The setup is very close to insurance claim summary:
>
> - **Multi-paragraph source documents** (financial reports = claim files)
> - **Multi-fact extraction** (revenue, segment, growth = loss amount, fault, dates)
> - **Citation required** for defensibility
> - **Hallucination detection** as core eval metric
>
> What I learned that I'd apply here:
>
> 1. **Citation must be at sub-paragraph granularity, not document level**. Saying 'this fact comes from doc 47' isn't enough — needs to be 'paragraph 3, sentence 2' so a human can verify in seconds.
>
> 2. **Negative-result ablation methodology**: I systematically ablated retrieval quality, prompt format, model size, CoT. For claim summaries I'd do same:
>    - Retrieval ablation: dense vs sparse vs hybrid; what's the recall@k for finding the loss-amount paragraph?
>    - Prompt format: structured field extraction vs narrative summary vs hybrid; which gives best actuary agreement rate?
>    - Model size: 8B vs 70B vs Claude; cost vs accuracy tradeoff per claim
>    - This is the **measure-then-decide** discipline that turns 'we built a LLM pipeline' into 'we built the right LLM pipeline'.
>
> 3. **Bias analysis matters**: ConvFinQA showed me that LLMs systematically miss certain types of facts (e.g., footnotes, parenthetical adjustments). For claims: LLM may systematically under-extract from handwritten adjustor notes, photo captions, or medical record annotations. **Need stratified eval across document type**.
>
> Also — my **TikTok PayLater work in Indonesia** taught me to ask 'what does the REGULATOR think about AI processing this data' before any code. Same instinct here for state DOI engagement.
>
> The pattern: **don't run 30M through LLM first and ask 'is it useful'. Sample 100K, hand-validate, prove value, THEN batch**. That's the difference between $5K of compute and $5M."

**Other resume hooks**:

- **Internal Agent Platform onboarding** — translated different team needs into a shared platform. Same skill as translating actuarial vs legal vs CS into a shared summary architecture (where it makes sense) vs separate (where it doesn't).

---

## 5 个 Follow-ups

**Q1**: "What's your cost estimate for batching 5M claims?"

**A**: Order-of-magnitude with assumptions stated:

- Avg claim file: ~10K tokens (mix of structured + notes + reports)
- Model: Claude 3.5 Sonnet on AWS Bedrock with prompt caching
- Input tokens: 5M × 10K = 50B; at $3/1M with caching effective rate ~$1.5/1M = **$75K**
- Output tokens: 5M × 500 = 2.5B; at $15/1M = **$37.5K**
- Embedding for retrieval: 5M × ~1500 chunks × 384-dim = ~$5K (one-time)
- Infrastructure (S3, Bedrock, compute, monitoring): ~$10K
- **Total batch one-time: ~$130K**

This is an order of magnitude smaller than my "$1M-$5M" mention earlier — that's the spread depending on model choice and document size. **For a $X billion insurer, $130K is a rounding error**.

**Caveats**: depends on actual avg document size (could be 50K not 10K), model choice (Claude vs GPT-4 vs Llama hosted), and quality requirements (more re-tries = more cost). Pilot will produce the real number.

**Q2**: "How do you ensure the LLM doesn't introduce bias in summaries that affects actuarial pricing fairness?"

**A**: This is exactly what NAIC and several state DOIs are pushing on (model disparate impact):

- **Stratified evaluation**: validation set has claims from all demographic segments (where claim file contains demographic info). Compare LLM extraction agreement rate per segment.
- **Bias test**: take same factual claim, vary only the demographic-correlated fields (zip code, name, etc.) → does LLM produce systematically different summaries?
- **Documentation**: write the bias eval methodology in algorithmic accountability doc. Submit to state DOIs that require (NY DFS 2024 directive).
- **Human-in-loop**: any claim used in actuarial model with anomalous summary metrics goes to human review.

**Caveat**: claim files contain less directly demographic info than e.g. lending data, so disparate impact risk is lower than other use cases — but not zero. Still need eval.

**Q3**: "Why not just use GPT-4 API directly? Saves all the self-hosting hassle."

**A**: Tradeoff depending on customer's risk tolerance:

**Pro API**: faster ship, better quality, less infra.

**Con API** (per insurance customer):
- Data movement compliance: must negotiate BAA + DPA + indemnification with OpenAI. Insurance legal teams typically take 3-6 months for these.
- State DOI exposure: NY DFS will ask "where physically does the data go for processing?" Answering "OpenAI" needs documentation.
- Audit log access: when you use API, you don't fully control the audit log retention or access.
- Catastrophic event risk: if OpenAI has a breach, customer claim data is in third-party hands.

**My recommendation**: explicitly raise this with GC + CCO. **If they're OK** with API + BAA, go faster. **If they want self-host**, plan for longer engagement. **Don't make the call unilaterally**.

For a conservative carrier, default is self-host. For a more aggressive carrier (digital-native, established API risk framework), API is acceptable.

**Q4**: "What if we need the summaries to feed into a regulatory rate filing? Does the LLM need to be 'qualified'?"

**A**: This is where state DOI conversations matter:

- **For internal actuarial modeling** (not used in rate filing): use freely with documentation
- **For rate filing input**: many states (CA, FL especially) require "**actuarially sound and explainable**" inputs. LLM-derived inputs may need:
  - Disclosure to state DOI that LLM was used
  - Methodology document (what model, what prompt, what validation)
  - Sample audit (DOI requests N claims for verification)
- **For underwriting decisioning**: many states restrict AI in consumer-impact decisions (some require "right to know" disclosures)
- **For claims handling automated decisions** (denial, etc.): heavily regulated

**My recommendation**: scope v1 to **non-rate-filing use** (actuarial research, claim audit prep) to avoid this. Year 2+ engage state DOIs on rate-filing usage.

**Q5**: "How do you handle the case where adjustor notes contain personal opinions that aren't facts?"

**A**: This is a quality issue specific to insurance. Adjustor notes often have "claimant seems exaggerating" or "vehicle appears modified" — opinion not fact. Approach:

- **Prompt engineering**: instruct LLM to **extract objective facts** with citation, **flag subjective opinions** separately
- **Schema**: summary has two sections — "Facts (with citations)" and "Subjective notes (with citations)"
- **Downstream guidance**: actuarial training emphasizes that subjective section is informational only, not for model input
- **Eval**: include "opinion vs fact" classification in agreement rate metric

**Risk**: LLM may treat opinion as fact (hallucination of confidence). Eval set includes claims with known subjective notes to catch this.

---

## ❌ 死路答法 (top 7)

1. **冲 cost estimate** before use-case scoping
2. **当 batch ETL system design 题做** (TPS calculation等)
3. **1 generic summary** for all downstream uses
4. **Run 30M before validating on 100**
5. **Skip per-state regulatory matrix**
6. **Skip citation tracking** (legal exposure)
7. **Include privileged documents** in LLM pipeline

---

## ✅ 加分项 (top 7)

1. **Scope to 1 LOB + 1 user** for v1 explicitly
2. **Citation at sub-paragraph granularity** required
3. **Stratified sampling 100K** before batching 5M
4. **State DOI pre-brief** in week 6-8
5. **Privacy classification (privileged / HIPAA / standard)** as first production layer
6. **Tiered model use** (small for easy, large for complex) for cost
7. **Quote your ConvFinQA citation + ablation methodology**

---

## 一句话总结

> **保险 30M 理赔 LLM summary = "scope reduction 是核心: 1 LOB + 1 user + 100K pilot 之前不要批量 + citation 不可省 + per-state regulatory matrix"**.
>
> 真正的 win 不是处理 30M, 是**让 actuary 用 100K 的 LLM summary 替代 3 hr 手动 review, 同时 GC + CCO + state DOI 全部满意**. 30M batch 是 month 4+ 的事, 不是 90 天.

---

## Cheat Sheet

```
不要做:
  - 冲 cost estimate 算 token
  - 当 batch ETL 题做
  - 1 generic summary for everyone
  - Batch 30M 前 validate
  - 跳过 state regulatory matrix
  - 跳过 citation tracking
  - Include privileged 文档

要做 (5 step):
  1. Clarify (10min): 10 Q, 锁 use case + state + LOB
  2. Stakeholder: Chief Actuary sponsor, GC + CCO + State DOI veto
  3. Data: ACORD / adjustor notes / police / medical / litigation
  4. Decompose: 10 subproblem, privacy classification 第一
  5. MVP: 4 周, 100 claim, 1 state, manual review

Clarify Q 必问:
  - 谁用 summary (actuarial / legal / CS / 等)?
  - 每个 use case 的 value?
  - State regulatory map?
  - PII / HIPAA / privilege handling?
  - 哪个 LOB?
  - V1 use case 优先?
  - Latency (batch / real-time)?
  - 之前 AI 部署?
  - Document format?
  - Veto holders?

Veto holders:
  - Chief Actuary (sponsor)
  - General Counsel
  - Chief Compliance Officer
  - State DOI engagement officer
  - CISO

Data privacy tiers:
  - Attorney-client privileged (EXCLUDE from LLM)
  - HIPAA (separate pipeline)
  - PII (redact before LLM)
  - Standard (process normally)

10 subproblems:
  1. Use case scoping (1 LOB + 1 user)
  2. Ingestion + privacy classification
  3. PII redaction
  4. Stratified sampling 100K pilot
  5. LLM summarization with citations
  6. Actuarial validation
  7. State-by-state regulatory matrix
  8. Cost optimization
  9. Batch infra (month 4+)
  10. Real-time (month 6+)

Walking-skeleton Week 1-4:
  100 claims, 1 state (Texas easy), manual privacy review,
  ~$10 compute, show actuarial reviewer
  Goal: 95%+ agreement on fact extraction

Phase plan:
  W1-4: 100-claim walking-skeleton
  W5-8: 100K stratified pilot
  W9-12: 1000-claim 3-actuary validation, state DOI pre-brief
  M4-6: batch 5M
  M7+: real-time + expansion

Citation requirement:
  - Sub-paragraph granularity (not doc-level)
  - "para 3, sentence 2" specificity
  - Human can verify in seconds

State regulatory map:
  CA + NY = strict (algorithmic accountability)
  TX + FL = less strict
  Some require explainable AI documentation

Cost estimate (5M claims):
  Input tokens (caching): ~$75K
  Output tokens: ~$37.5K
  Infrastructure: ~$10K
  Total batch one-time: ~$130K
  (small for $X-billion insurer)

Resume quote:
  "ConvFinQA: multi-hop QA over financial docs
   with citation, same structure as claim summary.
   Negative-result ablation methodology applies:
   retrieval × prompt × model × CoT.
   100K stratified BEFORE 5M batch."

Key phrases:
  - "Before cost estimate, who uses the summary..."
  - "Sample 100K before batching 5M"
  - "Citation at sub-paragraph granularity"
  - "Privacy classifier is the first production layer"
  - "Per-state regulatory matrix, not monolithic"
  - "State DOI pre-brief in week 6-8"
```
