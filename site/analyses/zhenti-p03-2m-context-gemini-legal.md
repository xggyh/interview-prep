## Q-P3 · Gemini 2M 长上下文 + RAG · 律师事务所 100K 合同分析

> "A boutique law firm has a corpus of **100,000 contracts** (avg 200 pages each, ~50K tokens per contract). Lawyers want to ask questions like 'Find all NDA clauses across all M&A contracts from 2020-2024 where the non-compete duration exceeds 24 months', or 'Summarize how this template has evolved across our last 10 versions'. You have access to **Gemini 3 Pro (2M context window)** and **Vertex AI Search**. **Should you use long-context, RAG, or both? Design the system. Defend your choice.**"

**中文翻译**:

> "一家精品律所有 **10 万份合同**的语料库 (平均每份 200 页, 约 5 万 token 每份). 律师想问类似 '找出 2020-2024 所有 M&A 合同里 NDA 条款中竞业限制 (non-compete) 超过 24 个月的'; 或者 '总结这个模板在我们最近 10 个版本里是怎么演变的'. 你能用 **Gemini 3 Pro (200 万 token 上下文窗口)** 和 **Vertex AI Search**. **要用长上下文, 还是 RAG, 还是两个都用? 设计系统. 为你的选择辩护.**"

**Round**: System Design (60 min)
**出处**: 🔮 预测题 — 针对 Google FDE 长上下文主场 (Gemini 2M context is Google's signature differentiator vs OpenAI/Anthropic)
**行业 / 约束**: Legal tech · 100K 合同 · cross-document reasoning · cost-conscious 精品律所 · citation 必须精确 · M&A / NDA / non-compete 法律语义复杂
**Distinguishing**: 这道题的杀手锏是 **"long-context vs RAG"** 决策, 不是简单 RAG. Gemini 2M token 是 Google 跟 OpenAI/Anthropic 最大差异化 — FDE 必须秀这个能力. 正确答案: **2 阶段 hybrid (RAG 收窄 → long-context 推理)**, 不是 either-or.

---

## 📖 术语速查 (本题用到的)

### 法律 / 合同业务

| 术语 | 解释 |
|---|---|
| **Contract corpus** ⭐ | 律所积累的所有合同 (生成版 + 客户版 + 历史版). 这道题 10 万份 × 200 页 = 律所核心 IP. |
| **M&A (Mergers & Acquisitions)** | 并购合同. 典型一份 200-500 页, 含 SPA / SPA Schedules / Disclosure Letter / TSA / Non-Compete / NDA / Reps & Warranties / Indemnity. |
| **NDA (Non-Disclosure Agreement)** | 保密协议. 比 M&A 短 (5-20 页). 也常单独签. |
| **Non-compete clause** ⭐ | 竞业限制条款. 限制对方在 X 个月 / 区域 / 行业内不能跟竞争对手做生意. **Duration > 24 months 在美国多州可能违法**. 这是题目特意点出的合规热点. |
| **MSA (Master Services Agreement)** | 主服务协议. 框架性 + 附 SOW. |
| **SOW (Statement of Work)** | 工作说明书. 附在 MSA 下, 描述具体项目. |
| **Indemnity clause** | 赔偿条款. 一方约定在某情况下赔另一方. |
| **Reps & Warranties (R&W)** | 陈述与保证. 卖方保证某些事实, 违反 = 索赔依据. |
| **Most-Favored-Nation (MFN)** | 最惠国待遇条款. 一方保证给对方的条件不比其他客户差. |
| **Force majeure** | 不可抗力. COVID 后被重写过的高频条款. |
| **Governing law / Jurisdiction** | 适用法律 / 管辖法院. |
| **Template evolution** ⭐ | 合同模板演化 — 律所内部模板每月小改, 每季度大改. 律师问 "这个版本跟 6 个月前差什么". 这是 cross-version reasoning. |
| **Clause library** | 律所内部条款库 — 律师从这里抠 boilerplate 拼合同. |
| **Redline / Track changes** | Word 的修订模式. 律师改合同标准动作. |
| **Privilege (attorney-client privileged)** ⭐ | 律师特权 — 律师 ↔ 客户沟通受保护, 法庭不能强制 disclose. 这道题的数据敏感度. |
| **Boutique law firm** | 精品律所 — 通常 20-100 律师, 专精某领域 (M&A / IP / Tax). 不像 Big Law 有充裕 IT 预算, 必须 cost-conscious. |

### Long-context vs RAG (本题核心)

| 术语 | 解释 |
|---|---|
| **Context window** ⭐ | LLM 一次能"看到"的最大 token 数. **Gemini 3 Pro = 2M tokens** (~3000 页 text or ~40 个本题的合同). GPT-5.5 = 200K. Claude Opus 4.7 = 500K. **Gemini 是唯一 2M, FDE 必提**. |
| **Long-context advantage** ⭐ | 一次性塞 N 个 doc 让 LLM 整体推理. 优点: cross-doc reasoning, 不丢上下文, 不依赖 retrieval 准确. 缺点: 贵 + 慢, 有 token 上限. |
| **Long-context "needle in haystack"** | 测 LLM 能否从大 context 里精准捞特定 fact. Gemini 2M 表现接近完美. |
| **RAG (Retrieval-Augmented Generation)** | 先 retrieve top-K → 再让 LLM 看 K 个 chunk. 优点: 便宜, 可 scale. 缺点: retrieval miss → answer miss. |
| **Hybrid retrieval** | 向量 + BM25 双路并行. 法律合同 keyword (clause name, statute reference) 多 → BM25 必须. |
| **Embedding** | 文本 → 向量. Vertex AI Search 用 text-embedding-005. |
| **Chunking strategy (legal)** ⭐ | 法律合同 chunk 必须 **clause-aware**, 不能按固定 512 token 切. 一个 NDA clause 可能 300 token 也可能 1500, chunk 边界必须是 clause 边界. |
| **Reranker** | Cross-encoder rerank top-100 → top-10. |
| **Citation grounding** ⭐ | LLM 答案每个 claim 必须带 source span. 法律场景 = 律师必须能 click 到原合同的 section number 验证. |
| **Multi-doc reasoning** ⭐ | 跨多 doc 推理 — "找所有 X 类合同里 Y 条款的 Z 情况". 长尾 cross-doc 任务. 这是 long-context 的杀手锏. |
| **Synthesis vs lookup** | Lookup = 直接 retrieval 答 (这条 NDA 怎么写). Synthesis = 跨多 doc 综合答 (我们历史上 NDA 怎么演变). Long-context 在 synthesis 占优. |

### Google Cloud / Vertex AI 体系

| 术语 | 解释 |
|---|---|
| **Vertex AI Search** | Google 托管 RAG / 搜索. 自动 chunking + embedding + retrieve + rerank. 这道题用于 stage 1 (RAG 收窄). |
| **Vertex AI Search filters** | 元数据 filter (e.g. contract_type='M&A', year=2020-2024). 缩小候选集. |
| **Gemini 3 Pro** ⭐ | $2/$12 per 1M tokens. **2M context window**. 这道题旗舰. |
| **Gemini 3 Flash** | $0.50/$3 per 1M. 1M context. 用于轻量 task. |
| **Vertex AI evaluation framework** | Built-in eval pipeline — gold set, autoraters, metric tracking. 法律 case 评估必备. |
| **BigQuery** | 存合同 metadata + 历史 query / answer 审计. |
| **Cloud Storage** | 存原始合同 PDF / DOCX. |
| **Document AI** | 合同 OCR + 结构化抽取 (parties, dates, governing law). 这道题 ingestion 必用. |
| **Document AI Contract Parser** ⭐ | Document AI 专门的合同解析器, 自动抽 clause / parties / dates / amounts. Google 2026 已成熟. |
| **Workspace 整合** | 律师在 Word / Docs 写合同, 整合 entry point. |

### Cost / 性能 (这道题反复算)

| 术语 | 解释 |
|---|---|
| **2026 LLM pricing** ⭐ | Gemini 3 Pro $2/$12 per 1M tokens (in/out) | Flash $0.50/$3 | Claude Opus 4.7 $5/$25 | GPT-5.5 $5/$30 |
| **Total corpus tokens** ⭐ | 100K contracts × 50K tokens = **5B tokens**. Long-context can hold 2M = 0.04% of corpus. **Must RAG-narrow before long-context.** |
| **Cost per long-context query** | 2M tokens × $2/M in + 5K tokens × $12/M out = $4 + $0.06 = ~**$4 per query**. Bursting. |
| **Cost per RAG query** | 10K tokens × $2/M + 500 × $12/M = $0.02 + $0.006 = **$0.026 per query**. ~150× cheaper. |
| **Prompt caching** ⭐ | Gemini 支持 cached context — 同 context 重用 50% off after first call. 关键 cost lever 在 multi-query session. |

---

## 这道题在考什么

**不是**: 考你会不会 RAG 或会不会 long-context.

**是**: 考你能不能在 **5B token corpus + 2M context window + multi-doc legal reasoning + cost-conscious 精品律所** 4 重约束下, **决定何时 RAG, 何时 long-context, 何时 hybrid**.

4 个 signal:

1. **The answer is "both" — 2-stage hybrid** (正确答案是"两个都用 — 2 阶段 hybrid") — 90% 候选人答 either-or. 错. 正确: **RAG 收窄到 top-30 contracts → long-context 一次性塞进 Gemini 推理**. 这是 Gemini 2M 的 unique pattern.

2. **Math first — 5B token corpus** (先算 token 数学) — 100K × 50K = 5B tokens. 2M context = 0.04% of corpus. **数学先讲清楚, 后面 trade-off 才有依据**.

3. **Cross-doc query ≠ single-doc query** (跨 doc query 跟单 doc query 是不同 path) — "总结这个合同" = single doc, RAG 即可. "比较 10 个版本" = cross-doc, long-context 占优. Path 要分.

4. **Citation grounding for legal is non-negotiable** (法律场景 citation 是底线) — 律师不接受 hallucination, 每个 claim 必须 link 到 contract section. Gemini grounding API + 显式 NLI verify.

---

## ❌ 最常见的挂法

**挂法 #1: "Just use long-context — Gemini 2M is huge"**

> "Since Gemini has 2M context, just put all relevant contracts in one prompt..."

死. **数学不通**:
- 100K contracts × 50K tokens = 5B tokens
- 2M context = 0.04% of corpus
- 单次 query 也塞不下 40 个合同 (40 × 50K = 2M, 已满)
- 全 corpus 一次塞 = impossible

**挂法 #2: "Just use RAG, ignore long-context"**

> "Standard RAG pipeline: embed, retrieve top-10 chunks, generate..."

死. 暴露不懂 Gemini 差异化能力:
- Cross-doc query (e.g. "non-compete > 24 months across 5K M&A contracts") 在 chunk 级别 retrieval 经常 miss — clause 在 doc 中段, embedding 抓不准
- "Template evolution across 10 versions" 需要看完整 10 个版本 = 500K tokens, RAG top-10 chunk 看不全
- 不用 long-context = 浪费 Gemini 最大卖点 = signal "你可能不该来 Google"

**挂法 #3: "Use long-context for all queries"**

> "Send top-50 retrieved docs (2.5M tokens, chunk down to 2M) to Gemini..."

死. **经济不可行**:
- 每 query $4 (long-context) vs $0.026 (RAG)
- 律师 50 人 × 20 query/day × 250 day = 250K queries/year
- 全 long-context: $1M/year
- 全 RAG: $6.5K/year
- 精品律所看到 $1M/year cost → 立刻砍项目
- 必须 routing: **simple query → RAG, complex multi-doc → long-context**

**挂法 #4: "Use fixed 512-token chunks"**

> "Standard chunking, 512 tokens..."

死. **法律合同 = clause-bounded**:
- NDA "Confidentiality" clause 可能 300 token 也可能 1500
- 固定 chunk 切断 clause 中间 → retrieval 找到的 chunk 答非所问
- 必须 **clause-aware chunking** (Document AI Contract Parser 自动做)

**挂法 #5: 不算 cost / 不提 prompt caching**

> "Architecture is fine, let's move on..."

死. 长上下文 cost 是这道题的核心 trade-off:
- 必须算: long-context $4/query, RAG $0.026/query
- 必须提 **Gemini prompt caching** — 同 context 重用 50% off, 律师 session 内多次问同合同 cost 大幅降
- 不提 = 暴露没真用过 Gemini production

**挂法 #6: 把 "template evolution" 当 single-doc query**

> "Retrieve current template, summarize..."

死. "Evolution across 10 versions" 需要看 10 个版本 = 500K tokens. RAG retrieve "current template" 只能给当前版. 这是经典 **long-context 杀手锏 query**, 必须用 long-context.

---

## 完美答案架构 (9 步 Response Architecture, 本题定制)

| # | Step | 时间 | 这层该说什么 (custom) | 开口句 |
|---|---|---|---|---|
| 1 | **Clarify (G·O·O·D-F·T)** | 7 min | 10 个 Q 沿 6 维度. 锁 query 类型 / cost budget / corpus 增长 / IP 风险 | "Before I decide RAG vs long-context, I need to know the query distribution — 'find clause across 5K contracts' is very different from 'compare 10 versions of template'." |
| 2 | **Math first (corpus + token cost)** | 4 min | 5B token corpus, 2M context, $4 vs $0.026/query | "Let me lay out the math first because it drives the design. 5B token corpus, 2M context window, 150× cost ratio." |
| 3 | **Query taxonomy (the central insight)** | 8 min | 4 类 query, 每类决定 RAG / long-context / hybrid | "There are 4 query types here, and the optimal path is different for each. Let me categorize." |
| 4 | **2-stage hybrid architecture** | 8 min | RAG narrows 100K → top-50 → long-context Gemini reasons across 50 | "The right pattern is 2-stage hybrid: RAG narrows the corpus, long-context Gemini does cross-doc reasoning." |
| 5 | **Ingestion deep dive** | 8 min | Document AI Contract Parser → clause-aware chunks + metadata → Vertex AI Search | "Ingestion has 2 outputs: (a) clause chunks for RAG retrieval, (b) full-doc index for long-context fetch." |
| 6 | **Query routing logic** | 8 min | Intent classifier → RAG path / hybrid path / long-context path. Cost-aware. | "Routing logic is the cost lever. 70% query route RAG, 25% hybrid, 5% pure long-context." |
| 7 | **Citation + grounding for legal** | 5 min | Gemini grounding + section number citation + NLI verify | "Lawyer's bar for citation is precise section, not 'this doc'. NLI verify on top of grounding." |
| 8 | **MVP plan + cost optimization** | 6 min | 90-day phased. Prompt caching. Tier cost by query type. | "I'd phase by query complexity. Phase 1 = RAG-only (most queries). Phase 2 = add long-context for cross-doc." |
| 9 | **Trade-offs + close** | 6 min | When long-context > RAG, when RAG > long-context, when hybrid wins | "If you give me unlimited budget, more long-context. With realistic budget, routing matters." |

---

## G·O·D·D·S Clarifying Framework (Clarify ↔ Decompose 双向映射) ⭐

> **核心理念**: 5 个 clarifying 维度 1:1 映射到 5 个 decompose 步骤. 问完一轮 G·O·D·D·S, decompose 也就基本写好了.

```
┌──────────────┐     ┌───────────────────────────────────┐
│ Clarify (问) │  →  │          Decompose (答)           │
├──────────────┼─────┼───────────────────────────────────┤
│ G oal        │ →   │ Step 1: KPI lock                  │
│ O wner       │ →   │ Step 2: Stakeholder map           │
│ D ata        │ →   │ Step 3: 数据 inventory            │
│ D eadline    │ →   │ Step 4: 子问题排序 (risk × value) │
│ S cope cut   │ →   │ Step 5: Walking-skeleton MVP      │
└──────────────┴─────┴───────────────────────────────────┘
```

### G — Goal (→ feeds Decompose Step 1: KPI lock)

> **Q1**: "When you say 'lawyers want to ask questions', what's the **expected query distribution**? Is it 80% **single-contract lookup** ('what's the non-compete in this contract'), 15% **cross-contract within a deal** ('compare NDA across all related agreements'), or is there a significant % of **cross-corpus reasoning** ('across all M&A contracts, find this pattern')? The split determines RAG vs long-context routing."

> **Q2**: "What's the **success metric**? Time saved per lawyer hour? Quality of clause discovery? Revenue per associate? Different metrics drive different priorities. **And critically: are lawyers paid hourly to their clients?** If yes, time savings may actually decrease billable hours — counter-intuitive incentive."

**这层 → 解锁 Decompose Step 1**: 答完 G 问题, 你就知道这道题的 KPI 是什么 (e.g., 5h saved per DD review + 100% citation traceback + cost ≤ $X/query), 后面 5 步的所有决策按这个 KPI 优化 — 也决定了 RAG-first vs long-context-first 的 routing.

### O — Owner (→ feeds Decompose Step 2: Stakeholder map)

> **Q3**: "Who's the **buyer** — Managing Partner, KM (Knowledge Management) Director, or General Counsel function? **Boutique firms often have no IT director** — the buyer = a senior partner who also funds + uses. **What's the engineering capacity** — do you have any in-house tech, or is everything outsourced to us?"

> **Q4**: "Who **uses** day-to-day — only partners (~10), all associates + partners (~50), or also paralegals + KM staff (~80)? Different roles = different complexity tolerance. **Who's the internal champion** for 90 days? And: **existing landscape** — iManage/NetDocs DMS? Kira/Luminance/Spellbook? What does this NOT replace + which UX must we co-exist with?"

**这层 → 解锁 Step 2**: 答完 O 问题, 你画出 stakeholder map (buyer = Managing Partner / champion = senior associate-turned-tech-lead / blocker = malpractice insurer + privilege committee / user = associates + paralegals / SME = KM librarian), 知道每步要 align 谁.

### D — Data (→ feeds Step 3: 数据 inventory)

> **Q5**: "**Corpus composition**: 100K contracts is total — what's the breakdown? % in (a) PDF (need OCR), (b) DOCX (clean text), (c) scanned old paper (poor OCR quality), (d) emails attached as contracts? Different ingestion paths. **And: how is the corpus growing** — 100/month or 1000/month?"

> **Q6**: "**Confidentiality classification**: are all 100K contracts treated equally, or are some marked extra-sensitive (attorney-privileged client matters)? **Does anything need to NOT be indexed at all?** And: **what's the position on client data going to a 3rd-party LLM** (even with Google BAA + VPC-SC)? Some firms keep deal-specific confidential DBs separate from general clause library."

**这层 → 解锁 Step 3**: 答完 D 问题, 你能画 data inventory 表 (open clause library / active matter / privileged-matter × format × OCR quality × growth × privilege tier × VPC-SC zone) — 知道每个 sub-problem 用哪份 corpus, 哪些直接 not-index.

### D — Deadline (→ feeds Step 4: 子问题排序)

> **Q7**: "**Why this timeline**? Is it driven by (a) competitive (other boutique firms shipping AI tools), (b) client demand (clients asking 'do you use AI'), (c) partnership decision, (d) specific deal pipeline (a big M&A coming where they want to use it)? Driver determines what we can compromise."

> **Q8**: "**Worst case + post-MVP roadmap**: lawyer relies on AI 'no non-compete > 24 months exists' → misses it in DD → malpractice. How prevent (confidence threshold, citation always, lawyer-in-loop)? **What's the malpractice insurance position**? Is this a 1-time MVP or 12-month platform? Will we have continuous lawyer feedback for tuning?"

**这层 → 解锁 Step 4**: 答完 Deadline 问题, 你知道**为什么** 这个 deadline, 才能 push back 或拆 phase. Sub-problems 按 (deadline 紧迫度 × malpractice risk × demo wow value) 排序 — citation-traceback + lawyer-confirmation 排最前 (insurer blocker), cross-corpus reasoning 推到 Phase 2 但保留作 demo wow.

### S — Scope cut (→ feeds Step 5: Walking-skeleton MVP)

> **Q9**: "If we ship a 60-day MVP, would you accept: **(a)** RAG-only for narrow queries (no long-context, no cross-contract reasoning), **(b)** RAG + long-context but only on the latest 3 years of M&A contracts (~5K docs, fits in 2M window), or **(c)** full 100K corpus from day 1 (much larger cost + complexity, ~$X/query)? My instinct: (b) — gives the demo wow factor (cross-doc) but bounds cost + privilege blast radius."

> **Q10**: "Which categories are **out of scope** for MVP — (a) any active-matter client deal, (b) any non-English contracts, (c) any pre-2020 scanned paper, (d) any non-M&A practice area (employment, IP, litigation)? Each cut narrows scope + de-risks. My recommendation: **MVP = English M&A clause library (open + recent 3 years) + RAG-first + long-context for cross-doc within single deal**; defer active-matter + non-English + cross-practice to Phase 2."

**这层 → 解锁 Step 5**: 答完 S 问题, MVP 边界明确. 你知道**哪 80% 砍掉先不做** (active-matter, non-English, pre-2020 scans, non-M&A, full 100K corpus, auto-redline), 哪 20% 是 walking skeleton (RAG-first + long-context for cross-doc-in-deal + 3-year M&A subset + citation-mandatory + lawyer-confirm UX + VPC-SC zone).

**面试官 likely 回答**:
- 80% single-contract, 15% within-deal cross-doc, 5% cross-corpus reasoning. Cross-corpus is **the demo wow factor**.
- Success = time saved on diligence + clause library discovery (associate level). NOT replace partner judgment.
- Buyer = Managing Partner who's also tech-savvy. 1 paralegal capable of running queries. No in-house IT.
- 30 lawyers + 15 paralegals = 45 users.
- Existing: iManage DMS + Word + email. No prior AI tool. Privilege concern HIGH — must Google BAA + VPC-SC.
- 90% PDF (need OCR), 10% DOCX. Growth ~200/month.
- All client matters confidential, but distinguish "open clause library" (templates, public deals) vs "active matter" (specific client deals, more sensitive).
- Worst case = missed clause in DD → malpractice. Must lawyer-confirm before relying. Malpractice insurer wants written AI usage policy.
- Driver: competitive — peer firm just shipped similar. Plus a big M&A deal in 6 months where they want to use it.
- 12-month platform planned. Continuous feedback yes.

→ **Real scope**: 90-day MVP serves 45 users, 100K-contract corpus (mostly PDF), 4 query types with smart routing, privilege-aware. **Cross-corpus reasoning = the wow factor we must nail in demo**.

---

## 详细分析 + 回答 (60-min walkthrough)

### Phase 1: Clarify + KPI (7 min)

> "Let me ask 10 things along G·O·O·D-F·T. The biggest unknown is query distribution — RAG vs long-context routing depends on it."
>
> *(asks 10, gets answers)*
>
> "OK. **Real scope**:
> - 45 users (30 lawyers + 15 paralegals), 100K-contract corpus
> - Query mix: 80% single-contract, 15% within-deal cross-doc, 5% cross-corpus
> - Privilege concern → Google BAA + VPC-SC
> - **Cross-corpus reasoning is the wow factor for partner demo**
> - 12-month platform, 90-day MVP to ship competitive feature
>
> **Three KPIs**:
> - **Retrieval quality**: nDCG@10 ≥ 0.80 on legal golden set (300 questions, validated by senior associate)
> - **Citation accuracy**: 100% citations link to correct contract section (no hallucinated section numbers)
> - **Cost**: < $50K/year all-in for 45 users (boutique budget reality)
>
> **Counter-metrics**:
> - **False negative** in clause discovery: < 1% (missing a non-compete = malpractice risk)
> - **Latency**: p50 < 5s for RAG path, p50 < 30s for long-context (acceptable for complex queries)

### Phase 2: Math first (4 min)

> "Before I sketch, let me lay out the math because it drives everything."

**Corpus size**:
- 100K contracts × 50K tokens avg = **5 billion tokens**
- Compressed (Gemini Pro 2M tokens window) = 5B / 2M = need 2500 separate Gemini calls to cover full corpus
- Total ingestion compute (one-time): ~5B tokens to embed

**Per-query cost comparison**:

| Path | Tokens consumed | Per-query cost | At 250K queries/year |
|---|---|---|---|
| **Pure RAG** (top-10 chunks of 1K) | 10K in + 500 out | 10000 × $2/M + 500 × $12/M = **$0.026** | $6,500/year |
| **Mid-hybrid** (RAG narrows to top-30 contracts, 30 × 5K abstract = 150K) | 150K in + 1K out | 150000 × $2/M + 1000 × $12/M = **$0.31** | $77,500/year |
| **Heavy hybrid** (RAG narrows to top-30 full contracts = 1.5M tokens) | 1.5M in + 5K out | 1.5M × $2/M + 5000 × $12/M = **$3.06** | $765,000/year |
| **Pure long-context** (40 full contracts = 2M) | 2M in + 5K out | 2M × $2/M + 5000 × $12/M = **$4.06** | $1,015,000/year |

**Key insight**: 150× cost ratio between RAG and long-context. Must **route by query**.

**Prompt caching savings** (Gemini feature):
- Same 1.5M context cached, additional queries: 50% off input cost
- Lawyer session: 1 lawyer asks 10 follow-up questions on same M&A deal → 1.5M × $2/M for first, then 9× at $1/M
- Effective cost: ($3.06 + 9 × $1.56) / 10 = $1.71/query (44% saving)

> "Prompt caching is what makes long-context affordable for multi-turn sessions. We design for it."

### Phase 3: Query taxonomy — the central insight (8 min)

> "Now the key insight. There are 4 query types here. Each has a different optimal path."

**Query Type A — Single-contract lookup (80% of volume)**:

Example: "What's the non-compete duration in this contract?"

- Lawyer is reading 1 specific contract, asks a question
- **Path**: RAG within that contract (filter by `contract_id`) → top-5 clause chunks → Gemini Flash answer
- Tokens: ~5K in, 200 out → **$0.013/query**
- Use case: 80% of lawyer day-to-day

**Query Type B — Within-deal cross-doc (15% of volume)**:

Example: "Across all related agreements in deal XYZ (SPA + NDA + TSA + Disclosure Letter + 5 schedules), find conflicting terms"

- Deal usually has 5-20 related docs, total 200K-500K tokens
- **Path**: RAG narrows to all docs in deal (filter by `deal_id`), if total tokens < 1M → long-context. If > 1M → RAG within deal first.
- Tokens: 200-500K in, 2K out → **$0.43-$1.03/query**
- Use case: M&A diligence, deal closing review

**Query Type C — Cross-corpus reasoning, narrow (4% of volume)** ⭐ THE WOW FACTOR:

Example: "Find all NDA clauses across all M&A contracts from 2020-2024 where non-compete duration > 24 months"

- Need to scan ~5K M&A contracts (50K × 5K = 250M tokens) for non-compete clauses
- Cannot fit all 5K contracts in 2M
- **Path**: 2-stage hybrid:
  - Stage 1: Vertex AI Search filters `contract_type=M&A AND year IN (2020-2024)` → 5K contracts
  - Stage 2: BM25 + dense search for "non-compete" → top-100 clause chunks from those contracts
  - Stage 3: Group by contract_id → top-30 contracts with non-compete > 24mo (filter on extracted duration metadata)
  - Stage 4: Send top-30 contracts' non-compete sections (30 × 5K = 150K tokens) to Gemini 3 Pro for cross-doc analysis
  - Stage 5: Gemini reasons across, returns structured answer with citations
- Tokens: 150K in, 5K out → **$0.36/query**
- Use case: thematic clause research, partner asks for cross-deal pattern

**Query Type D — Template evolution / version history (1% of volume)** ⭐ THE OTHER WOW:

Example: "Summarize how our M&A SPA template has evolved across our last 10 versions"

- Need to see all 10 versions of one template (10 × 50K = 500K tokens)
- **Path**: Pure long-context — load all 10 versions into Gemini 3 Pro context
- Tokens: 500K in, 5K out → **$1.06/query**
- Use case: KM activity, partner reviewing what's changed

**Cost projection per 250K queries/year**:

| Type | % | Per-query | Annual |
|---|---|---|---|
| A: Single-contract | 80% | $0.013 | $2,600 |
| B: Within-deal | 15% | $0.65 | $24,375 |
| C: Cross-corpus narrow | 4% | $0.36 | $3,600 |
| D: Template evolution | 1% | $1.06 | $2,650 |
| **Total** | 100% | weighted | **~$33,225/year LLM cost** |

Add Vertex AI Search ($2K/year) + Cloud Storage + BigQuery + Cloud Run + DLP → **total ~$50K/year**. Within budget.

> "**Without query routing, pure long-context would cost ~$1M/year**. Routing is the cost lever that makes this viable for a boutique firm. 150× cost compression by matching query type to path."

### Phase 4: 2-stage hybrid architecture (8 min)

```
                       Customer GCP Project (HIPAA/SOC2 isolated)
                       VPC-SC perimeter around: Vertex AI / BigQuery / GCS / KMS
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                          │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐  │
│  │  Lawyer in Workspace (Word + Docs side panel, or web UI)                            │  │
│  │  ─ Add-on UI in Word / Docs                                                         │  │
│  │  ─ Web UI for complex queries (cross-corpus reasoning visualization)                │  │
│  │  ─ Always shows citations + click-to-source                                          │  │
│  └────────────────────────────────────────────────────────────────────────────────────┘  │
│                                              │                                            │
│                                              ▼                                            │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐  │
│  │  Agent Backend (Cloud Run)                                                          │  │
│  │                                                                                     │  │
│  │  [1] Auth + privilege check (OAuth + iManage SSO + ACL)                            │  │
│  │  [2] Intent classifier (Gemini 3 Flash, $0.50/1M):                                  │  │
│  │      ─ Type A: single-contract → RAG path                                           │  │
│  │      ─ Type B: within-deal → hybrid (deal-scoped)                                   │  │
│  │      ─ Type C: cross-corpus → 2-stage hybrid                                        │  │
│  │      ─ Type D: template evolution → pure long-context                               │  │
│  │  [3] Routing layer                                                                  │  │
│  └────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                          │
│  ┌──────────────────────────────┐   ┌─────────────────────────────────────────────────┐  │
│  │  RAG Path (Type A, 80%)      │   │  Long-context Path (Type B/C/D, 20%)            │  │
│  │                              │   │                                                  │  │
│  │  Vertex AI Search query      │   │  [Stage 1] Filter narrow corpus via Vertex AI   │  │
│  │  ─ Filter by contract_id     │   │              Search filters (type, year, deal)  │  │
│  │  ─ Hybrid: BM25 + dense      │   │              → 30-100 candidate contracts        │  │
│  │  ─ Cross-encoder rerank      │   │  [Stage 2] Retrieve full text from GCS          │  │
│  │  ─ Top-5 clause chunks       │   │              → 30 × 50K = 1.5M tokens            │  │
│  │       │                      │   │  [Stage 3] If > 2M: rerank to top-30 first      │  │
│  │       ▼                      │   │  [Stage 4] Gemini 3 Pro with grounding tool     │  │
│  │  Gemini 3 Flash answer       │   │              + Vertex AI Search grounding       │  │
│  │  + citation [contract:sec]   │   │              → cross-doc reasoning              │  │
│  │  ─ $0.013/query              │   │  [Stage 5] Citation verify + section anchor     │  │
│  │  ─ p50 latency 3s            │   │  ─ $0.36-$1.06/query                            │  │
│  │                              │   │  ─ p50 latency 15-30s                           │  │
│  └──────────────────────────────┘   └─────────────────────────────────────────────────┘  │
│                                                                                          │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐  │
│  │  Citation enforcement (both paths)                                                  │  │
│  │  ─ Every claim tagged with [contract_id:section_number]                             │  │
│  │  ─ NLI verifier (Gemini Flash entailment check) on each claim                       │  │
│  │  ─ Confidence < 0.8 → marked "unverified" in UI, raw source shown                   │  │
│  └────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                          │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐  │
│  │  Storage tier                                                                        │  │
│  │  ─ Cloud Storage (raw PDF / DOCX), CMEK encrypted, per-deal partition               │  │
│  │  ─ Vertex AI Search datastore (clause chunks + metadata)                            │  │
│  │  ─ BigQuery `contracts.metadata` (party, dates, governing_law, contract_type)       │  │
│  │  ─ BigQuery `contracts.clauses` (parsed clauses with section number + text)         │  │
│  │  ─ BigQuery `audit.queries` (every query + answer + citations, 7yr retention)       │  │
│  └────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### Phase 5: Ingestion deep dive (8 min)

**Step 5.1 — Document AI Contract Parser**:

This is Google's killer service for this domain. **Use it, don't reinvent**.

```python
from google.cloud import documentai_v1 as documentai

# Use Contract Parser processor (Google trained for legal contracts)
processor = "projects/{PROJECT}/locations/us/processors/CONTRACT_PARSER"

# Parse a contract
def parse_contract(gcs_uri):
    doc = documentai_client.process_document(
        request={
            "name": processor,
            "raw_document": {"content": fetch_pdf(gcs_uri), "mime_type": "application/pdf"},
        }
    )
    
    return {
        "parties": extract_entity(doc, "Party"),
        "effective_date": extract_entity(doc, "Effective_Date"),
        "governing_law": extract_entity(doc, "Governing_Law"),
        "term_clause": extract_entity(doc, "Term"),
        "termination_clause": extract_entity(doc, "Termination_Clause"),
        "indemnity_clause": extract_entity(doc, "Indemnity_Clause"),
        "non_compete_clause": extract_entity(doc, "Non_Compete"),
        "non_disclosure_clause": extract_entity(doc, "Confidentiality"),
        "clauses": [
            {"section": s.title, "text": s.text, "start_page": s.start_page}
            for s in doc.sections
        ]
    }
```

**Output schema for BigQuery**:

```sql
CREATE TABLE contracts.metadata (
  contract_id STRING NOT NULL,
  contract_type STRING,  -- 'M&A', 'NDA', 'MSA', 'SOW', 'License', ...
  parties ARRAY<STRING>,
  effective_date DATE,
  governing_law STRING,
  jurisdiction STRING,
  deal_id STRING,
  matter_id STRING,
  privilege_class STRING,  -- 'open' | 'matter_confidential' | 'attorney_privileged'
  gcs_pdf_uri STRING,
  gcs_text_uri STRING,
  ingest_ts TIMESTAMP,
  ingest_version STRING
);

CREATE TABLE contracts.clauses (
  clause_id STRING NOT NULL,
  contract_id STRING NOT NULL,
  section_number STRING,  -- e.g. "5.2.1"
  section_title STRING,
  clause_type STRING,  -- 'non_compete' | 'indemnity' | 'reps_warranties' | ...
  text STRING,
  -- Extracted structured fields for typed queries
  non_compete_duration_months INT64,  -- NULL if not non_compete clause
  non_compete_geography STRING,
  indemnity_cap_amount NUMERIC,
  start_page INT64,
  end_page INT64
);
```

**Why structured extraction matters**: query "non-compete > 24 months" can be answered by **BigQuery SQL alone** (no LLM needed):

```sql
SELECT 
  c.contract_id, 
  c.section_number, 
  c.non_compete_duration_months,
  m.contract_type,
  m.parties
FROM contracts.clauses c
JOIN contracts.metadata m USING(contract_id)
WHERE m.contract_type = 'M&A' 
  AND EXTRACT(YEAR FROM m.effective_date) BETWEEN 2020 AND 2024
  AND c.non_compete_duration_months > 24
```

This is **the secret weapon for query Type C**. If Document AI extracts well, many "find clause X where Y" queries become SQL. LLM only needed for narrative summary on top.

**Cost**: Document AI Contract Parser ~$0.10 per page. 100K contracts × 200 pages = **$2M for full backfill**. **Whoa, expensive.**

**Cost optimization**:
- Phase 1: parse only 20K most-recent contracts ($400K). Older ones lazy-parse on first query.
- Negotiate enterprise pricing with Google (often 50% off at this volume)
- Self-hosted alternative: Llama-3-medical-legal NER + custom prompts → $0 per page but 6 week build
- **Reality**: Boutique firm 不会预算 $400K-$2M 一次性. **Phase 1 do 20K recent ($400K), phase later**.

> "I'd push back on full backfill cost. Phase 1 = 20K most-recent contracts via Document AI ($400K), with a lazy-parse path for older contracts on first access (amortized over years). Total Y1 ingestion cost: ~$500K."

**Step 5.2 — Clause-aware chunking**:

NOT fixed 512 tokens. Use Document AI Contract Parser output:

```python
def chunk_contract(parsed_doc):
    chunks = []
    for clause in parsed_doc["clauses"]:
        clause_text = clause["text"]
        section = clause["section_number"]
        clause_type = classify_clause_type(clause)  # via small classifier
        
        if len(tokenize(clause_text)) <= 1500:
            # Whole clause as one chunk
            chunks.append({
                "chunk_id": f"{contract_id}_clause_{section}",
                "text": clause_text,
                "metadata": {
                    "contract_id": contract_id,
                    "section_number": section,
                    "section_title": clause["section_title"],
                    "clause_type": clause_type,
                }
            })
        else:
            # Sub-chunk long clauses on sentence boundary
            sub_chunks = sentence_chunk(clause_text, max_tokens=1500, overlap=200)
            for i, sub in enumerate(sub_chunks):
                chunks.append({
                    "chunk_id": f"{contract_id}_clause_{section}_{i}",
                    "text": sub,
                    "metadata": {
                        "contract_id": contract_id,
                        "section_number": section,
                        "sub_chunk": i,
                        "clause_type": clause_type,
                    }
                })
    return chunks
```

**Why this matters**: when lawyer queries "non-compete", retrieval finds chunk with `clause_type='non_compete'` metadata. Filter ranks it higher than chunks merely mentioning "non-compete" in passing. Improves nDCG@10 by ~0.1.

**Step 5.3 — Vertex AI Search ingestion**:

```python
documents = []
for chunk in all_chunks:
    documents.append({
        "id": chunk["chunk_id"],
        "structData": {
            "contract_id": chunk["metadata"]["contract_id"],
            "section_number": chunk["metadata"]["section_number"],
            "clause_type": chunk["metadata"]["clause_type"],
            "contract_type": parent_metadata[contract_id]["contract_type"],
            "effective_year": parent_metadata[contract_id]["effective_year"],
            "deal_id": parent_metadata[contract_id]["deal_id"],
            "matter_id": parent_metadata[contract_id]["matter_id"],
            "privilege_class": parent_metadata[contract_id]["privilege_class"],
        },
        "content": {
            "mimeType": "text/plain",
            "rawText": chunk["text"],
        }
    })

# Bulk import
import_request = ImportDocumentsRequest(
    parent=f"projects/{PROJECT}/locations/global/dataStores/{DATASTORE_ID}/branches/default_branch",
    gcs_source=GcsSource(input_uris=["gs://contracts-import/chunks-*.jsonl"]),
    reconciliation_mode=ReconciliationMode.INCREMENTAL,
)
```

**Vertex AI Search auto**:
- Embedding (text-embedding-005, Google internal)
- Hybrid indexing (dense + sparse)
- Reranking (semantic ranker built-in)
- ACL via `structData.privilege_class` and `structData.matter_id` filtering

**Throughput**: ~10K chunks/sec import. 100K contracts × ~30 clauses each = 3M chunks → 5 min import.

### Phase 6: Query routing logic (8 min)

**Intent classifier** (Gemini Flash, $0.50/1M, ~80ms):

```python
INTENT_PROMPT = """Classify the legal query into one of 4 types:
- TYPE_A_SINGLE_CONTRACT: question about ONE specific contract user is viewing
- TYPE_B_WITHIN_DEAL: question across multiple docs in ONE matter/deal
- TYPE_C_CROSS_CORPUS: question across many contracts in firm corpus
- TYPE_D_TEMPLATE_EVOLUTION: question about how a template has changed over time

Also extract:
- has_contract_context: is the user looking at a specific contract right now? (true/false)
- has_deal_context: is the question scoped to a specific deal/matter? (true/false)
- requires_cross_doc_reasoning: needs comparison/aggregation across docs? (true/false)
- filters: any explicit filters (contract type, year range, party)

Query: {query}
Context: {workspace_context}  # if user is viewing a doc, include contract_id

Return JSON.
"""

def classify_intent(query, context):
    response = flash.generate(INTENT_PROMPT.format(query=query, workspace_context=context))
    return json.loads(response)
```

**Routing logic**:

```python
def route_query(intent, query):
    if intent["type"] == "TYPE_A_SINGLE_CONTRACT":
        return rag_path(query, contract_filter=intent["contract_id"])
    
    elif intent["type"] == "TYPE_B_WITHIN_DEAL":
        docs_in_deal = bq.query(
            "SELECT contract_id FROM metadata WHERE deal_id = ?", 
            intent["deal_id"]
        )
        total_tokens = bq.query(
            "SELECT SUM(token_count) FROM metadata WHERE deal_id = ?",
            intent["deal_id"]
        )
        if total_tokens < 1_500_000:  # fits in 2M context with output budget
            return long_context_path(query, contract_ids=docs_in_deal)
        else:
            return rag_within_deal_path(query, deal_id=intent["deal_id"])
    
    elif intent["type"] == "TYPE_C_CROSS_CORPUS":
        # 2-stage hybrid
        return cross_corpus_hybrid_path(query, filters=intent["filters"])
    
    elif intent["type"] == "TYPE_D_TEMPLATE_EVOLUTION":
        template_versions = bq.query(
            "SELECT contract_id FROM templates_history WHERE template_id = ? ORDER BY version DESC LIMIT 10",
            intent["template_id"]
        )
        return long_context_path(query, contract_ids=template_versions)
    
    else:
        # Fallback: ask user to clarify
        return ask_clarification(query)
```

**The 2-stage hybrid (Type C, the wow factor)**:

```python
def cross_corpus_hybrid_path(query, filters):
    # STAGE 1: Vertex AI Search with filters → narrow contracts
    filter_str = build_vertex_filter(filters)
    # e.g. "contract_type: ANY(\"M&A\") AND effective_year >= 2020 AND effective_year <= 2024"
    
    # Search for relevant clauses
    search_results = vertex_search.search(
        query=query,
        filter=filter_str,
        page_size=100,  # top 100 chunks
    )
    
    # STAGE 2: Use structured BigQuery for typed conditions
    if "non_compete > 24 months" in query:  # detected by Gemini
        # Direct SQL filter on extracted metadata
        sql_results = bq.query("""
          SELECT c.contract_id, c.section_number, c.text, c.non_compete_duration_months
          FROM contracts.clauses c
          JOIN contracts.metadata m USING(contract_id)
          WHERE m.contract_type = 'M&A'
            AND EXTRACT(YEAR FROM m.effective_date) BETWEEN 2020 AND 2024
            AND c.non_compete_duration_months > 24
            AND c.clause_type = 'non_compete'
        """)
        # SQL is authoritative for typed fields, RAG is for narrative
        candidate_contracts = sql_results
    else:
        # Group RAG results by contract
        candidate_contracts = group_by_contract(search_results)
    
    # STAGE 3: Top-30 contracts (cap on long-context budget)
    top_30 = candidate_contracts[:30]
    
    # STAGE 4: Load relevant clauses (not full contracts) into Gemini context
    clauses_for_context = []
    for contract_id in top_30:
        relevant_clauses = bq.query(
            "SELECT section_number, text FROM contracts.clauses WHERE contract_id = ? AND clause_type IN ('non_compete', 'restrictive_covenant')",
            contract_id
        )
        clauses_for_context.append({
            "contract_id": contract_id,
            "clauses": relevant_clauses,
        })
    
    # Total tokens: 30 contracts × 3 clauses × 1K tokens = 90K tokens. Well under 2M.
    
    # STAGE 5: Gemini 3 Pro with grounding
    response = gemini_pro.generate_content(
        contents=[
            f"""You are analyzing legal contracts. Answer the lawyer's query 
            with citations to specific contracts and section numbers.
            
            Query: {query}
            
            Relevant clauses from {len(top_30)} contracts:
            {format_clauses(clauses_for_context)}
            
            Answer with structured output:
            - Summary
            - List of findings (each with contract_id, section, key quote)
            - Confidence
            """
        ],
        tools=[grounding_tool],  # Vertex AI Search grounding
        generation_config={"temperature": 0.0},
    )
    
    return response
```

**Why this beats pure long-context**:
- Pure long-context: 5K M&A contracts × 50K = 250M tokens. Cannot fit.
- Pure RAG: top-10 chunks may miss contracts. Cross-doc aggregation hard.
- **2-stage hybrid**: RAG narrows 5K → 30 most-relevant. Long-context reasons across 30. Best of both.

**Why this beats heavy hybrid (sending 30 full contracts = 1.5M tokens)**:
- Lawyer asks "non-compete clauses" — don't need to load entire 200-page contracts.
- Load only the `non_compete` clauses from those 30 contracts → 90K tokens (16× cheaper).
- Cost: $0.18/query vs $3.06/query. **17× savings**.
- This is **clause-aware loading**, a level beyond clause-aware chunking.

### Phase 7: Citation + grounding for legal (5 min)

> "Lawyer's citation bar is precise section, not just 'this document'. Let me explain how we hit 100% citation accuracy."

**Citation strategy**:

```python
class LegalCitation:
    contract_id: str
    section_number: str  # e.g. "5.2.1"
    section_title: str
    quote: str  # exact span
    page: int
    confidence: float  # 0.0-1.0
    nli_score: float  # entailment score

def format_citation(c: LegalCitation) -> str:
    return f"[{c.contract_id}, §{c.section_number} \"{c.section_title}\", p.{c.page}]"
```

**Grounding via Vertex AI Search + Gemini grounding**:

```python
response = gemini.generate_content(
    contents=[...],
    tools=[grounding.GroundingTool(vertex_ai_search=...)],
)

# Gemini returns grounded chunks with confidence per claim
for claim, attribution in zip(response.claims, response.grounding_chunks):
    if attribution.confidence < 0.8:
        # Mark unverified in UI
        # Show raw source chunk
        ui_render.mark_unverified(claim, raw_chunk=attribution.text)
```

**NLI verification (defense in depth)**:

```python
# For each claim, verify entailment with cited source
for claim, citation in extract_claims_with_citations(answer):
    cited_text = bq.query(
        "SELECT text FROM contracts.clauses WHERE contract_id = ? AND section_number = ?",
        citation.contract_id, citation.section_number
    )
    
    # Use Gemini Flash as NLI verifier
    entailment_prompt = f"""Premise: {cited_text}
    Hypothesis: {claim}
    Does the premise entail the hypothesis? Answer JSON: {{"entailed": true/false, "confidence": 0-1}}"""
    
    nli_result = flash.generate(entailment_prompt, response_format="json")
    nli = json.loads(nli_result)
    
    if not nli["entailed"] or nli["confidence"] < 0.8:
        # Mark this claim as low-confidence
        flag_claim(claim, "citation_does_not_support_claim")
```

**Lawyer UI**:

```
┌──────────────────────────────────────────────────────────────────┐
│  Query: Find non-competes > 24 months in 2020-2024 M&A           │
│                                                                   │
│  Found 7 contracts:                                               │
│                                                                   │
│  1. Acme-TargetCo Acquisition (2022)                              │
│     [Acme-TargetCo-SPA, §8.4 "Restrictive Covenants", p.47]      │
│     "Seller shall not...for a period of 36 months..." [click]    │
│     Confidence: 0.97 ✓                                            │
│                                                                   │
│  2. ... (6 more)                                                  │
│                                                                   │
│  ⚠️ 1 claim flagged unverified:                                   │
│  "Smith-Jones LLC also has 30-month covenant"                     │
│  → NLI score 0.62 — citation §5.1 mentions "non-solicitation"    │
│    not "non-compete". Please verify. [show raw clause]            │
└──────────────────────────────────────────────────────────────────┘
```

**Why this UX is critical**: lawyer **trusts NLI-flagged warnings**. Without them, lawyer treats AI as authoritative → misses subtle errors → malpractice.

### Phase 8: 90-day MVP + cost optimization (6 min)

**Phase 1 (Week 1-4): Foundation + Type A**:
- Document AI Contract Parser kickoff (20K recent contracts, $400K, parallel)
- Vertex AI Search datastore + ingestion pipeline
- Cloud Storage + BigQuery schema for metadata + clauses
- VPC-SC perimeter + IAM
- Intent classifier (Gemini Flash)
- RAG path (Type A — single-contract Q&A)
- Workspace Add-on UI v1
- Citation enforcement v1
- **Mid-phase**: 5-lawyer alpha, 50 Q&A golden set

**Phase 2 (Week 5-8): Type B + C (the wow)**:
- Long-context path (Type B — within-deal cross-doc)
- 2-stage hybrid (Type C — cross-corpus reasoning)
- BigQuery clause-typed schema (`non_compete_duration_months` etc.)
- SQL-based filters for typed queries
- Prompt caching enabled
- Confidence + NLI verification
- **Mid-phase**: 15-lawyer beta, 200 Q&A golden set, **Managing Partner demo of Type C** (the wow)

**Phase 3 (Week 9-13): Type D + polish + go-live**:
- Long-context path (Type D — template evolution)
- Template version tracking (BigQuery `templates_history`)
- Cost dashboard (per-user, per-type spend)
- Malpractice insurer-ready usage policy document
- Pen test + privilege handling review
- Soft launch: 30 lawyers + 15 paralegals

**Day 90 deliverable**: 45 users, 100K-contract corpus (20K Document-AI-parsed + 80K lazy-parse on demand), 4 query types, **$50K/year budget**.

**Cost optimization levers** (5 of them):

1. **Query routing** (already core): RAG vs long-context. 150× cost ratio.
2. **Prompt caching**: 50% off on cached context. Lawyer sessions benefit huge.
3. **Clause-aware loading**: don't load full contracts, load only relevant clauses. 17× savings on Type C.
4. **SQL pre-filter**: typed queries via BigQuery, no LLM needed. Free for many "find clause X where Y" queries.
5. **Flash for intent + summary**: Pro for reasoning only. 4× cost saving on lighter tasks.

> "Without these 5 levers, this product is **$1M/year**. With them, $50K/year. The architecture IS the cost optimization."

### Phase 9: Trade-offs + close (6 min)

**Decision 9.1 — When long-context > RAG**:

| Scenario | Why long-context wins |
|---|---|
| Template evolution (D) | Need all 10 versions in one context to compare |
| Within-deal review (B) | All deal docs need cross-reference, total < 1M |
| Multi-version comparison | Each version's full text needed |
| Synthesis tasks | LLM needs to see whole picture |

**Decision 9.2 — When RAG > long-context**:

| Scenario | Why RAG wins |
|---|---|
| Single-contract Q&A (A) | Question scoped to 1 doc, no need for full context |
| Specific clause lookup | Top-3 chunks more accurate than 50K tokens |
| Latency-sensitive | RAG 3s vs long-context 30s |
| Cost-sensitive (high volume) | 150× cheaper per query |

**Decision 9.3 — When hybrid (2-stage) > pure either**:

| Scenario | Why hybrid wins |
|---|---|
| Cross-corpus search at scale (C) | Corpus > 2M tokens, but query needs reasoning |
| Combined typed + narrative | SQL filter + LLM reasoning |
| Cost-sensitive cross-doc | Stage 1 narrows, stage 2 reasons cheaply |

**Decision 9.4 — Document AI Contract Parser vs self-build**:

| 维度 | Document AI Contract Parser | Self-build |
|---|---|---|
| Build time | 1 week integration | 6-8 weeks NER + parser |
| Quality | Google-trained, 90%+ on standard clauses | Variable depending on training data |
| Cost | $0.10/page (~$20/contract) | Free per page after build |
| Maintenance | Google updates | Our problem |
| Languages | English + ~10 others | English only out of gate |

My choice: **Document AI Contract Parser for Phase 1**. Even $400K for 20K contracts is faster path to ship and the structured extraction enables the SQL pre-filter optimization. Can self-build later if cost becomes problematic at full scale.

**Decision 9.5 — Privilege handling**:

- Contracts marked `privilege_class='attorney_privileged'` → **separate Vertex AI Search datastore** (separate ACL)
- Only authorized lawyers (per-matter ACL) can query privileged datastore
- Privileged queries log to **separate audit table** with extra access controls
- Per Google BAA, attorney-privileged content is technically covered, but **belt-and-suspenders**: encrypt with **separate KMS key** so even GCP admins can't decrypt
- Cross-datastore queries (open + privileged) require explicit lawyer flag in UI

**Decision 9.6 — Workspace integration**:

- Add-on in Google Docs (where lawyers redline contracts)
- Add-on in Word (via Microsoft 365 OAuth, for lawyers using Word — common in legal)
- Web app for complex cross-corpus query visualization (graph view of clause evolution, etc.)
- iManage integration for DMS — pull contract context based on which doc lawyer has open

---

## Gao Xin 简历专属 reframe + STAR

### STAR: ConvFinQA multi-hop reasoning

**Situation**: ConvFinQA 是 multi-hop QA benchmark, query 需要 cross-document financial reasoning.

**Task**: 设计 hybrid retrieval + multi-step reasoning pipeline, 在 100K 财报文档上跑.

**Action**:
- Stage 1: BM25 + dense retrieval → top-100 candidate documents
- Stage 2: Cross-encoder rerank → top-20
- Stage 3: LLM cross-doc reasoning with explicit "intermediate computation steps"
- Ablation: 单 retrieval / 单 rerank / single-hop vs multi-hop

**Result**: 17% accuracy improvement over single-stage RAG. Ablation method 成为团队 playbook.

**桥段**:
> "ConvFinQA 的 multi-hop + ablation 经验 100% 直接套到这道题. 'Cross-corpus reasoning across 5K M&A contracts' 跟 'multi-doc financial QA' 是同问题. 我会直接复用 2-stage hybrid pattern + ablation methodology (1-stage vs 2-stage vs full long-context 量化 nDCG / accuracy / cost 三轴)."

### STAR: BNPL Chatbot (TikTok PayLater)

**Situation**: TikTok PayLater 7 市场 chatbot, 用户问从简单 ("我账户余额") 到复杂 ("我下个月最低还款是多少 + 我能不能延期").

**Task**: 用 intent routing 把简单 query 用便宜 model, 复杂 query 用大 model.

**Action**:
- Intent classifier (小模型, ~80ms)
- 4 类 intent: account_lookup / payment_help / dispute / general
- Routing: 60% account_lookup → 小模型 + SQL, 30% payment → 中模型 + RAG, 10% 复杂 → 大模型 + tools

**Result**: cost 优化 4×, latency 改善 30%, accuracy 不降.

**桥段**:
> "Query routing 这道题 = BNPL intent routing 同样 pattern. 这里 4 类 query (A/B/C/D) 路径不同, 跟 PayLater 同模式. 这是 FDE 'cost-conscious 架构' 必备技能, 我做了 2 年."

### STAR: Internal Agent Platform

**Situation**: 字节内部 Agent Platform 50+ 服务接入, tool registry + intent routing 复杂.

**Task**: 定义 tool routing 标准, 让 LLM 选对 tool.

**Action**:
- Tool metadata schema (scope, side effect, latency, cost)
- LLM-first routing (LLM 自己选 tool, 不是 hardcoded if-else)
- Eval framework: 每 tool 用对率, end-to-end success rate

**Result**: 50+ tool 接入, LLM 选错 tool 率 < 5%.

**桥段**:
> "这道题的 query type 4 个 path 决策, 我做 Internal Agent Platform 时是 50+ tool 决策. Architectural pattern 一样: intent classify → route → execute → measure. Path 多了, 框架同."

### Voice agent 7 markets

**桥段**:
> "Latency-sensitive multi-model routing (Gemini Pro 30s vs Flash 3s) 跟 voice agent 多语种多复杂度 routing 同模式. PagedAttention + continuous batching 优化 long-context inference 我有经验, 这里可以扩展到 Vertex AI prompt caching 策略."

---

## 5 个 Follow-ups

### Q1: "如果 partner 坚持 '把全部 100K 合同 always-loaded long-context, 就用 2M 窗口', 怎么 push back?"

**A**: Math + 备选:

> "Math 不通, 我直接画给 partner 看:
>
> 1. **Math**: 100K × 50K = 5B tokens. 2M context = 0.04% of corpus. 一次 query 也塞不下 40 个合同. 'Always loaded' 是 impossible by physics.
> 2. **Cost**: 即使我们能塞 40 contract (2M), 每 query $4. 50 lawyer × 20 query/day × 250 day = 250K queries × $4 = $1M/year. **vs $50K/year hybrid**. partner 看到 $1M 立刻不要.
> 3. **Latency**: 2M context Gemini ~30s p50. 律师 query 等 30s 影响生产力. RAG 3s 是 baseline.
> 4. **Right framing**: 'You don't load all books in the library when reading — you check the index, get the relevant book, then read.' RAG = index, long-context = reading the chosen book.
> 5. **The wow demo**: 我会专门 demo Type C (cross-corpus reasoning) 来证明 long-context 在该用的时候用了, 大部分时候用 RAG = 又快又省. Hybrid = 两全其美.
>
> 如果 partner 仍坚持: '我们 6 个月内必须 cost > $1M, latency > 30s 一直跑, 你愿意吗?' 大概率 partner 听完会接受 hybrid."

### Q2: "对于完全新 lawyer query (intent classifier 没见过的 pattern), 怎么 fallback?"

**A**: 多层 fallback:

> "**4 层 fallback**:
>
> 1. **Intent classifier 'unsure' branch**: Flash classifier 输出 confidence. < 0.7 → fallback path.
> 2. **Default to RAG (cheapest)**: unsure → RAG with broad filter. 至少给 lawyer 一些 source 看.
> 3. **Show retrieved sources, ask user**: 'I found these 10 contracts that may be relevant. Do you want me to: (a) summarize them, (b) extract specific clauses, (c) compare them?'. User-guided refinement.
> 4. **Log + retrain**: 这些 'unsure' query 是 intent classifier 的训练数据. 每周 review, 加新类别 / 改 prompt.
>
> 关键: **NEVER pretend** the agent understood — 让 lawyer 看到 source list 比给个 hallucination 强 100×."

### Q3: "如果一个合同有 OCR 错误 (例如 '24 months' 识别成 '2.4 months'), 怎么办?"

**A**: OCR 质量是法律 case 命门:

> "**多管齐下**:
>
> 1. **Document AI confidence**: 每个 extracted field 有 confidence score. < 0.85 → flag for human review.
> 2. **典型 OCR 错误检测**: 数字 + 单位 cross-check ('2.4 months' is non-standard, '24 months' is standard) → 自动 flag.
> 3. **Dual-source verification for typed queries**: SQL 找到 `non_compete_duration_months > 24` 时, **also retrieve the original clause text** + Gemini cross-check '是否文本支持 duration > 24 months claim'. NLI verifier 抓 mismatch.
> 4. **Source-of-truth**: 任何 typed answer 都附上原 PDF 页面 highlight. Lawyer 点 [view source] 看原文确认. 不依赖 OCR 结构化输出独自答.
> 5. **Re-OCR workflow**: 高频用到的合同, 如果 Document AI v1 解析有问题, 用 Document AI 新版重新 parse + diff. 老合同每年 batch refresh.
>
> 关键: **AI 不替代 lawyer 验证**. Citation + click-to-source 是 contract — lawyer 总能看到原文."

### Q4: "另一家律所 onboard 了, 100K + 50K corpus, 总 7.5B tokens. 我们的 Vertex AI Search datastore 能 scale 吗?"

**A**: Multi-tenant scale:

> "**Two-axis scaling**:
>
> 1. **Per-firm datastore isolation**: 不能共享 Vertex AI Search datastore (privilege concern). Each firm = separate datastore + separate VPC-SC perimeter. **物理隔离**.
> 2. **Vertex AI Search limits**: 单 datastore 支持 100M docs (Google quota). 100K contract × 30 chunks = 3M chunks. **空间充足 30×**.
> 3. **Cost**: Vertex AI Search ~$0.02 per query. 250K queries × $0.02 = $5K/year per firm. 跟 LLM cost 比小.
> 4. **Compute scaling**: Cloud Run auto-scales. Backend stateless, scale to N firms = N Cloud Run instances (or multi-tenant deployment with per-firm config).
> 5. **Multi-tenant onboarding playbook**: 7-day onboard per firm. Day 1: Document AI parse subset. Day 3: Vertex AI Search index. Day 5: UAT. Day 7: go-live.
>
> 第 2 个 firm onboard 不需要重新设计架构, 因为已经 multi-tenant by design."

### Q5: "怎么 measure 这个工具 actually helping lawyers? Lawyers are billable, time savings might reduce hours billed."

**A**: 这是法律行业**反直觉** metric:

> "**核心 paradox**: lawyer billable hours. AI saves time → fewer billable hours → less revenue. 但律所长期看 AI 必须采用. **如何 measure**:
>
> **Leading (week-month)**:
> - **Adoption**: % lawyers used in week 1. Target 60%. Without adoption, no impact.
> - **Query depth**: avg query length + sophistication. Trending up = lawyers learning to use.
> - **Confirm rate**: 用 AI suggestion / total. Target 70%+. 低 = quality issues.
>
> **Mid-term (month-quarter)**:
> - **Diligence speed**: time from intake → first draft. Target -30% (this is **delivered to client faster, not less billable**).
> - **Junior lawyer empowerment**: % work done by senior vs junior. AI lifts junior productivity → can take more cases per partner.
> - **New matter win rate**: 'we use AI' 在 pitch deck 提供. Target win rate +5%.
>
> **Lagging (6-12 month)**:
> - **Revenue per lawyer**: even with fewer hours per case, more cases per lawyer = higher RPL.
> - **Client satisfaction**: faster turnaround → better NPS.
> - **Associate retention**: AI takes drudge work → less burnout.
>
> **Counter-metrics**:
> - **Malpractice incidents**: 0 (the contract)
> - **Privilege breach**: 0
> - **AI-attributed errors caught in pre-billing review**: track to ensure quality not slipping
>
> **The framing for partner**: 'AI doesn't reduce your revenue, it **shifts where revenue comes from** — fewer hours per matter, but more matters won, faster delivery, junior leverage.'  This is the only framing that gets partners to fund AI."

---

## ❌ 死路答法 (top 7)

1. **"Use only long-context, 5B tokens 装 2M"** — 数学不通, 暴露不算 cost
2. **"Use only RAG"** — 浪费 Gemini 2M context 差异化, 不能答 cross-doc
3. **"Use long-context for everything"** — $1M/year cost, 律所拒绝
4. **Fixed 512-token chunking** — 切断 clause 边界
5. **不算 cost** — 这道题中心是 cost trade-off
6. **不用 Document AI Contract Parser, 自己写 NER** — 6 周搞不定
7. **把 template evolution 当 single-doc query** — 错误 path 选择

---

## ✅ 加分项 (top 10)

1. **第一步: math (5B / 2M / cost ratio 150×)** — staff-level cost thinking
2. **Query taxonomy 4 类** — 反 either-or framing, 显示 nuance
3. **2-stage hybrid (RAG 收窄 → long-context 推理)** = 标准答案
4. **Clause-aware chunking via Document AI Contract Parser** — Google native
5. **Clause-aware loading (only relevant clauses)** — 17× cost saving
6. **SQL pre-filter for typed queries** — 不依赖 LLM 答 deterministic 问题
7. **Prompt caching** — Gemini 特有, multi-turn session 大幅省
8. **Citation 必须 section number, NLI verify** — 法律 bar
9. **Privilege-aware datastore + separate KMS key** — 法律行业特有
10. **G·O·O·D-F·T 10-question clarify** + 数学驱动 push back

---

## 一句话总结

> **Google FDE 律所合同分析 = "Math first" + "Query taxonomy 4 类决定 path" + "2-stage hybrid (RAG narrows → long-context reasons)" + "Clause-aware chunking + Clause-aware loading" + "SQL pre-filter for typed queries"**.
>
> 关键: long-context vs RAG **不是 either-or, 是 by-query routing**. 路由对了 = $50K/year, 路由错了 = $1M/year. **150× cost lever**. Gemini 2M context 是杀手锏 (template evolution + 跨 30 contracts 推理), 但 80% 简单 query 仍 RAG.

---

## Cheat Sheet

```
Math (这道题中心):
  Corpus     : 100K contracts × 50K tokens = 5B tokens
  Context    : Gemini 3 Pro 2M (0.04% of corpus)
  Pure RAG   : $0.026/query
  Pure long  : $4.06/query (150× more)
  Hybrid     : $0.18-0.36/query (17× less than pure long)

Query Type 4 类 (the central insight):
  A: Single-contract       80%  → RAG only           $0.013/q
  B: Within-deal cross-doc 15%  → Hybrid (deal-scope)$0.65/q
  C: Cross-corpus narrow    4%  → 2-stage hybrid    $0.36/q  ⭐ wow factor
  D: Template evolution     1%  → Pure long-context $1.06/q  ⭐ Gemini 2M

Annual cost (250K queries):
  Weighted blended: ~$33K LLM + $17K infra = $50K/year
  Compare pure long-context: $1M+ /year
  150× lever from query routing

Stack (Google native):
  Ingest    : Cloud Storage + Document AI Contract Parser
  Storage   : BigQuery (metadata + clauses + audit) + GCS (PDFs)
  Search    : Vertex AI Search (auto-embed/index/rerank)
  LLM       : Gemini 3 Pro (long-context + reasoning) + Flash (intent + NLI)
  Compute   : Cloud Run backend, no GKE
  Security  : VPC-SC + CMEK + separate KMS per matter class
  UI        : Workspace Add-on (Word + Docs) + web app for complex viz

2-stage hybrid pattern (Type C, the magic):
  Stage 1: Vertex AI Search filter (contract_type, year, etc.) → top-100 chunks
  Stage 2: Group by contract → top-30 contracts
  Stage 3: BigQuery SQL for typed conditions (e.g. non_compete_months > 24)
  Stage 4: Load only relevant CLAUSES (not full contracts) into Gemini context
           = 30 × 3 clauses × 1K = 90K tokens
  Stage 5: Gemini 3 Pro grounded reasoning + citation

90-day phases:
  Week 1-4 : RAG + Type A (single-contract Q&A), Document AI parse 20K recent
  Week 5-8 : Type B (within-deal) + Type C (cross-corpus) — the WOW for partner demo
  Week 9-13: Type D (template evolution) + polish + go-live with 45 users

Cost optimization 5 levers:
  1. Query routing (150×)
  2. Prompt caching (2×)
  3. Clause-aware loading (17×)
  4. SQL pre-filter (free for typed queries)
  5. Flash for intent + NLI (4×)

G·O·O·D-F·T Clarify 10 Q:
  G: query distribution? success metric? billable-hour conflict?
  O: buyer = Managing Partner? lawyer count?
  O: existing tools? privilege concerns?
  D: corpus composition (PDF %)? growth rate? privilege class?
  F: malpractice scenario? insurance position?
  T: why 90 days? competitive pressure?

Document AI Contract Parser:
  ─ Extract clauses (non_compete, indemnity, R&W, etc.)
  ─ Extract typed fields (duration months, indemnity cap)
  ─ Section numbers preserved
  ─ Cost $0.10/page × 200 pages = $20/contract
  ─ 20K contracts × $20 = $400K (Phase 1)
  ─ Self-build alternative: 6-8 weeks, free per-page

Citation strategy:
  ─ Gemini grounding (API-native)
  ─ Format: [contract_id, §section "title", p.page]
  ─ NLI verify per claim (Flash entailment)
  ─ Confidence < 0.8 → flag "unverified", show raw clause
  ─ 100% citation accuracy target

Death traps:
  - Use only long-context (math fails, $1M)
  - Use only RAG (miss Gemini differentiator)
  - Use long-context everywhere ($1M, 30s latency)
  - Fixed 512 chunk (breaks clause)
  - 不算 cost (avoid the central trade-off)
  - Self-build NER (6-8 weeks)
  - Template evolution treated as single-doc

加分:
  - Math first (5B / 2M / 150×)
  - 4-type query taxonomy
  - 2-stage hybrid
  - Document AI Contract Parser
  - Clause-aware loading
  - SQL pre-filter for typed
  - Prompt caching
  - Section-number citation + NLI verify
  - Privilege-aware datastore
  - G·O·O·D-F·T + math-driven push back

Key phrases:
  "Math first: 5B token corpus, 2M context, 150× cost ratio"
  "Long-context vs RAG is not either-or — it's per-query routing"
  "2-stage hybrid: RAG narrows, long-context reasons"
  "Clause-aware chunking + clause-aware loading = 17× savings"
  "SQL pre-filter on typed fields — free queries, no LLM"
  "Prompt caching is what makes long-context affordable for sessions"
  "Citation must be section-precise, NLI verified"
  "Gemini 2M is the moat — use it on D queries (template evolution), not on A"
  "$50K/year with routing vs $1M/year without — architecture IS cost optimization"
```
