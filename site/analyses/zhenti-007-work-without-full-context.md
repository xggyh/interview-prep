## Q07 · 在你并不完全理解的环境里工作

> "Tell me about a time you had to work in an environment you didn't fully understand — unfamiliar domain, codebase, customer industry, or stack. How did you ramp up and deliver?"

**Round**: Behavioral (30-45 min, hiring manager 或 cross-functional)
**出处**: Exponent 2026 FDE Guide · 公司: OpenAI / Anthropic / Palantir / Scale AI / Databricks 高频. 变体: "tell me about a time you ramped up fast" / "describe working in a new domain" / "how do you handle unfamiliar technical territory" — 对 FDE 几乎 100% 必问 (因为 FDE 每个客户都是 new domain)

---

## 📖 术语速查 (本题用到的)

> 这题主线是 ConvFinQA (金融 QA 学术项目) 的 ramp-up. 涉及大量金融 / NLP / 工程术语. 这张表过完, 故事里的 jargon 就跟得上.

### Ramp-up 方法论 ⭐ 这题的核心

| 术语 | 解释 |
|---|---|
| **Three-track parallel ramp** ⭐ | 3 个 track 并行 — Domain learning / Technical implementation / Validation. 不 sequential. |
| **Ramp ≠ master** ⭐ | Ramp = 够 ship first piece + 知道剩余 gap. 不等于 master domain. |
| **Source of truth = specific human** ⭐ | 不 Google. 找 specific 领域专家 1 小时 lunch chat, 比 1 周 doc 强 10×. |
| **Calibrated confidence** ⭐ | 校准自信. 我 know 我 know 什么, partial 什么, 不 know 什么. Ship 前 explicit flag low-confidence. |
| **First small delivery (week 2)** | 第 2 周就 ship 个小东西. Ramp + ship 并行, 不是 ramp 完才 ship. |
| **Cold email / cold-DM** | 冷邮 / 主动私信. 找 grad student / industry expert 时用. |
| **Lunch chat / coffee chat** | 1 小时非正式聊天. 比 formal interview 高效. |
| **Office hour** | 答疑时间. Mentor / senior 开放预约. |
| **Hypothesis logging** | 假设记录. 结构化试错 — 每个 hypothesis 1 天实验 + success metric + writeup. |
| **Skim vs deep** | 跳读 vs 深读. Depth proportional to "depth-of-impact-on-decisions-I'll-make". |

### Financial / SEC 术语 (ConvFinQA 用)

| 术语 | 解释 |
|---|---|
| **ConvFinQA** ⭐ | Multi-hop financial QA 公开数据集 + paper. 用户简历里的学术项目. |
| **Multi-hop QA** | 多跳问答. 一个问题需要从多 doc / 多段抽信息再组合. |
| **SEC 10-K filing** ⭐ | 美国上市公司年报. 200-400 页, 包含 MD&A / financial statements / footnotes. |
| **MD&A (Management Discussion & Analysis)** | 10-K 里管理层的讨论分析章节. |
| **EBITDA** | Earnings Before Interest, Taxes, Depreciation, Amortization. 衡量 operating cash flow. |
| **Operating income** | 营业利润. 跟 EBITDA 区别在是否扣折旧摊销. |
| **Working capital** | 营运资金 = 流动资产 - 流动负债. |
| **Deferred revenue** | 递延收入. 客户已付钱但服务未交付的负债. |
| **Accrual accounting** | 权责发生制. 跟 cash basis 相反. |
| **Earnings transcripts** | 财报电话会议 transcript. |
| **NYU Stern** | 纽约大学 Stern 商学院. 金融 grad student source. |
| **Honoraria** | 小额答谢费 / 顾问费. Pay grad student review. |

### NLP / 检索术语

| 术语 | 解释 |
|---|---|
| **Retrieval module** | 检索模块. 把 query → top-k 相关 doc. |
| **Dense embedding** | 稠密向量嵌入. BERT / OpenAI embedding 都是 dense. |
| **Sparse retrieval (BM25)** | 稀疏检索. 基于词频 (TF-IDF / BM25), 跟 dense 互补. |
| **Hybrid retrieval** | Dense + Sparse 结合. 金融 entity 在 dense 上 confused, 需要 hybrid. |
| **Numeric reasoning** | 数值推理. 处理金额 / 百分比 / 增长率等. |
| **Aggregation** | 聚合. 多段数字合并算总和 / 平均. |
| **Sub-question decomposition** | 子问题分解. 复杂 question 拆成多个简单 sub-question. |
| **Verification (numeric)** | 数值校验. 算完 cross-check 是否一致. |
| **9-variant ablation** ⭐ | 9 种组合实验, 逐个 disable / replace 组件看 lift. |
| **Negative result** | 负结果. 实验显示某组件没用. Publish 是 honesty 信号. |
| **End-to-end accuracy** | 端到端准确率. 跟 per-stage metric 区分. |

### Voice / Production 术语 (alternate STAR)

| 术语 | 解释 |
|---|---|
| **ASR / TTS** | 语音识别 / 语音合成. |
| **Twilio** | 提供 SMS / voice / video API 的云通信平台. |
| **Telephony provider** | 电信提供商. Twilio / Plivo / Vonage. |
| **Streaming audio** | 流式音频. 边收边处理, 不等完整 audio. |
| **WebSocket** | 浏览器 / server 之间持久连接, 双向. Voice streaming 用. |
| **Jitter buffer** | 抖动缓冲区. 缓冲音频 frame 应对网络延迟波动. |
| **Audio frame ordering** | 音频帧顺序. 包乱序到达, 需排序重组. |
| **ElevenLabs (as TTS provider)** | 第 3 方 TTS, 简历也提过. |

### BNPL / 风控术语 (alternate STAR)

| 术语 | 解释 |
|---|---|
| **BNPL funnel** | 先买后付漏斗. Apply → credit decision → disburse → repay. |
| **PD / LGD / EAD** | Probability of Default / Loss Given Default / Exposure At Default. 风控核心三件套. |
| **Credit decision** | 信用决策. 是否给客户授信. |
| **Fraud signal taxonomy** | 欺诈信号分类体系. |
| **Affirm / Klarna** | 美国 / 欧洲两大 BNPL 上市公司. |

### Cross-function 术语

| 术语 | 解释 |
|---|---|
| **Stakeholder mapping** | 利益相关方梳理. 谁决定 / 谁阻拦 / 谁付钱 / 谁用. |
| **Customer mental model** | 客户心智模型. 他们怎么想问题. FDE 独有 ramp 维度. |
| **Organizational politics** | 组织政治. VP vs compliance vs ops 之间 tension. |
| **Round-robin (ramp)** | 第 1 周问每个 function "what should I be careful of from your perspective?". |
| **Failure mode** | 失败模式. Ship 之前 list 5-10 个 potential failure mode = ready signal. |

---

## 这道题在考什么

这是 **FDE 工作 80% 时间的真实写照**. 表面问 ramp-up, 实际筛 6 件事:

- **Intellectual humility** —— 你能不能 say "I don't know" 不 fake 懂
- **Ramp-up speed + system** —— 你有 framework 还是 ad-hoc 学
- **Asking the right person** —— 你 know 谁是 source of truth (不是 google / 不是 docs / 是 specific human)
- **Domain ≠ stack** —— 你能区分 domain 学习 (regulation, industry workflow, customer mental model) vs stack 学习 (codebase, framework)
- **Speed to first delivery** —— 你不是 ramp 完才 ship, 是 ramp + ship 并行
- **Calibrate confidence** —— 你能 articulate "我 X 部分 confident, Y 部分 not confident, 我 ship X first"

**没说出口的红线**:

- "I quickly learned everything and shipped" → fake competence, FDE manager 不信
- "I asked a lot of questions" → 太 vague, 哪些 question? 问谁?
- "I read all the docs" → 没 prioritize, 没 efficient
- "I figured it out alone" → no help-seeking, no humility
- "I pretended to understand and Google'd later" → 不 honest, 大忌
- 没讲 "我学的时候 wrong 过 X" → no vulnerability, no learning artifact

---

## 完美答案架构 (Layered Response)

8 段结构, total ~4-5 分钟:

| # | 层 | 时间 | 这层该说什么 | 开口句 |
|---|---|---|---|---|
| 1 | **Context — unfamiliar what** | 20s | 哪个 domain / stack / customer 不懂 | "I joined the ConvFinQA team — financial reasoning project. I had ML background but zero accounting / SEC filings / multi-hop financial reasoning..." |
| 2 | **What I didn't know (specific)** | 30s | List 3-4 具体 gap | "Three gaps: (1) accounting concepts (EBITDA, working capital), (2) SEC 10-K filing structure, (3) financial multi-hop reasoning theory..." |
| 3 | **Why I had to deliver anyway** | 20s | Timeline + constraint | "Paper deadline 4 months, my role was lead engineer + lead methodology designer..." |
| 4 | **Ramp-up framework** | 60s | 系统化 not ad-hoc | "Three-track parallel ramp: domain learning track, technical implementation track, validation track. Each with timebox + checkpoint..." |
| 5 | **Asking the right person** | 45s | Source of truth identification | "For accounting I found 2 grad students in finance dept... For SEC filing I found compliance team at TikTok... For multi-hop reasoning I read 3 papers + emailed authors..." |
| 6 | **First small delivery (ramp + ship parallel)** | 45s | 你 ship 第一个东西 in week 1-2, 不是 month 4 | "Week 2 I shipped a small data preprocessing component — not core, but allowed me to test understanding..." |
| 7 | **Calibrated confidence** | 30s | 你 know 你 know 什么, 不 know 什么 | "By month 2 I could confidently design retrieval module. But I flagged 'numeric reasoning is unfamiliar, I need senior review'..." |
| 8 | **Outcome + transferable learning** | 30s | Result + meta lesson | "Project shipped on time. Lesson: 'ramp ≠ master', ramp = enough to deliver first piece + identify gaps you still have..." |

Total: ~4-5 min.

---

## 详细回答 (Sample Monologue) — 可以照背

> "我讲 ConvFinQA 项目, 因为它是我第一次进入完全 unfamiliar domain — 我 ML 出身, financial reasoning 跟我 prior work 完全没 overlap.
>
> **Context**: ConvFinQA 是 multi-hop financial QA 学术项目. 模型要读 financial document (SEC 10-K filings, earnings transcripts), 回答 multi-hop question (e.g., 'EBITDA grew X% from Q2 to Q3, what was the absolute Q3 figure?'). 我加入是 lead engineer + lead methodology designer.
>
> **What I didn't know (具体)**:
>
> **Gap 1 — Accounting concepts**: EBITDA, working capital, deferred revenue, accrual accounting... 这些 finance 基本概念我都不熟. 我 ML PhD 期间没 touch 过 finance.
>
> **Gap 2 — SEC 10-K filing structure**: 10-K 是美国上市公司 annual report, 200-400 页 specific structure (MD&A, financial statements, footnotes). 我不知道哪一节在哪.
>
> **Gap 3 — Multi-hop financial reasoning theory**: Multi-hop QA 是 NLP 领域 sub-field, financial domain 有 specific challenge (numbers + entities + temporal + units). 我没 read 过 prior literature.
>
> **Gap 4 — TikTok's existing financial pipeline**: 项目跟 TikTok finance team 有数据共享, 我不熟他们 internal ontology.
>
> **Why I had to deliver anyway**:
>
> Paper deadline 4 months. 我是 lead engineer + lead methodology designer. Junior researcher 1 个, intern 2 个 (依赖我). 我不能 'I'm still learning, give me 2 more months'. Ramp + deliver 必须并行.
>
> **Ramp-up framework — three-track parallel**:
>
> 我 explicit 设计 3 个 parallel track, 每个 timebox + checkpoint:
>
> **Track 1 — Domain learning (week 1-4, ongoing background)**:
> - Week 1: 通读 1 本 accounting intro book ('Financial Statements' by Thomas Ittelson, 200 pages). Timebox 1 week (不 deep, just 概念覆盖).
> - Week 2: 读 3 个真实 10-K filings (Apple, Tesla, Walmart), note 结构差异.
> - Week 3: 跟 finance dept 2 个 grad student (我 cold-email 找的) 各 1 小时 lunch chat, 问他们 'what do junior analysts wish ML researchers knew about finance?'.
> - Ongoing: 每周 30 min 读 1 paper on financial NLP.
>
> **Track 2 — Technical implementation (week 1, immediate start)**:
> - Week 1: 开始写 data preprocessing pipeline (我 ML expertise apply 这里, domain ignorance ok)
> - Week 2-4: build retrieval module (我 expertise on retrieval/embedding, domain ignorance manageable)
> - Week 4-8: numeric reasoning module (我 partial expertise + need domain help)
>
> **Track 3 — Validation / sanity check (week 2+, continuous)**:
> - 每周 sample 10 个 prediction 给 finance grad student review (我 paid them small honoraria)
> - 这 step catches 我 domain ignorance 在 output 上的 manifestation
>
> 3 个 track parallel 跑, 不 sequential. 这是 ramp 跟 ship 并行的关键.
>
> **Asking the right person — source of truth**:
>
> 我不 Google 知识. Google 给 general 答案, ConvFinQA 需 specific.
>
> - **Accounting concepts**: 我 cold-email 2 个 grad student in NYU Stern (我大学 alumni network). Lunch chat $30, learn 比 1 周 Google 多. 关键: 我 ask specific question, 不是 "teach me finance". E.g., "EBITDA vs operating income 区别, ConvFinQA 这 2 个 question 哪个更 common?"
> - **SEC 10-K structure**: 我找 TikTok 内部 compliance team (我们做 SEC reporting 给 ByteDance 美国子公司). 1 小时 walkthrough one 10-K, point out commonly-referenced sections.
> - **Multi-hop reasoning theory**: 我 read 3 个 prior paper (Drop, FinQA, ConvFinQA precursors). 给 paper author 之一 email, 礼貌请教 1 个 specific question, 他答复 + share related unpublished work.
> - **TikTok internal pipeline**: 我 sit 1 天 with finance ops team, observe their workflow. Learn ontology.
>
> **核心 principle**: source of truth 是 specific human with specific expertise, 不是 generic resource. **Ask the right person 比 read 100 doc 快 10×**.
>
> **First small delivery — ramp + ship parallel**:
>
> Week 2 我 ship 了一个 data preprocessing pipeline. 不 core, 但 deliverable. 这有 3 个 effect:
>
> **One — Demonstrates progress**. Junior researcher / intern 看到 ship, 不焦虑.
>
> **Two — Tests my understanding**. Preprocessing 我 need handle '$1,234,567' format + '(456)' negative parens + '$M' vs '$B' unit. Domain ignorance 立刻 manifest 在 bug 上. I caught 4 bugs week 2 而不是 month 4.
>
> **Three — Build momentum + confidence**. Week 2 small win 让 week 4 medium task / week 8 big task more approachable.
>
> Week 4 ship retrieval module. Week 8 ship numeric reasoning v1.
>
> **Calibrated confidence — what I know vs don't**:
>
> By month 2:
> - **Confident**: retrieval (我 expertise), data pipeline (我 expertise), evaluation framework (我 expertise)
> - **Partial confident**: numeric reasoning (我 understand mechanics, not sure about edge cases)
> - **Not confident**: domain-specific reasoning (e.g., 'this question requires understanding deferred revenue concept', 我 still learning)
>
> 我 explicit flag 给 advisor: 'numeric reasoning module 我 design, but I need your review on domain edge cases'. Senior advisor review 找出 3 个 domain-specific edge case I missed.
>
> **Calibrated confidence 不是 weakness, 是 strength**. 我 know 我 know 什么 = 我 know 我 ship 什么 first, 我 ask review on 什么. Senior 见过太多 'fake confidence ship 然后 fail' 候选, calibrated confidence 立刻是 senior signal.
>
> **Outcome + meta learning**:
>
> ConvFinQA 项目 ship paper on deadline (4 months). Paper accepted top-tier venue. Reviewer specifically 评 'methodology design' (我 own 的部分) 是 paper strength.
>
> 9-variant ablation 我设计, 包括 2 个 negative result (publish honesty).
>
> Domain knowledge: 4 个月我从 0 到 'can intelligent design financial QA system'. Not 'finance expert', but 'enough domain to ship'.
>
> **Meta lesson — 'ramp ≠ master'**:
>
> Ramp = enough to deliver first piece + identify gaps you still have. Not = master domain.
>
> 4 个 month ConvFinQA 后我 still 不是 finance expert. 我是 'ML engineer who can intelligent build financial NLP system, knows which finance question to ask, and ship in unfamiliar domain'. 后者 valuable enough.
>
> 现在我每个 unfamiliar domain entry, 4 个 track + 'ramp ≠ master' framework. Voice agent 我 entry 时不懂 ASR/TTS production, 用同 framework 4 个 month entry. BNPL 我 entry 时不懂 BNPL business model + 风控, 用同 framework entry. Internal Agent Platform 我 entry 时不懂 internal infrastructure 全貌, 用同 framework entry.
>
> **Transferable across domain**. 这才是 senior FDE signal — 不是 'I know 7 domain', 是 'I have ramp framework that works in any new domain'."

---

## Gao Xin 简历专属 STAR 模板

至少 1 完整 STAR (ConvFinQA), 2 alternate.

### ★ STAR 1: ConvFinQA Financial Reasoning Ramp (★ PRIMARY)

**S** (Situation):
> "加入 ConvFinQA multi-hop financial QA 学术项目, lead engineer + lead methodology designer. ML 出身, financial domain 完全不熟 — accounting, SEC filings, financial NLP literature 都不熟. Paper deadline 4 months."

**T** (Task):
> "Ramp + ship 并行. Junior + intern 依赖我. 不能 'give me 2 more months'."

**A** (Action):
1. **Identify 4 gaps**: accounting concepts / SEC 10-K structure / multi-hop financial reasoning theory / TikTok internal pipeline
2. **Three-track parallel framework**:
   - Track 1 (Domain learning): book + filings + grad student chat + ongoing paper reading
   - Track 2 (Technical implementation): data preprocessing → retrieval → numeric reasoning (apply existing ML expertise)
   - Track 3 (Validation): weekly sample review by finance grad student (paid honoraria)
3. **Source of truth identification**:
   - Accounting: 2 grad students NYU Stern, alumni network
   - SEC structure: TikTok internal compliance team
   - Multi-hop theory: 3 prior papers + email author
   - TikTok pipeline: sit 1 day with finance ops
4. **First small delivery week 2**: data preprocessing pipeline, catches 4 bugs from my domain ignorance early
5. **Calibrated confidence**: confident on retrieval/data/eval, partial on numeric, low on domain-specific reasoning. Explicit flag for senior review on low-confidence areas

**R** (Result):
- **Paper shipped 4 months on deadline**
- **Top-tier venue accepted**
- Reviewer cited "methodology design" (my owned piece) as paper strength
- **9-variant ablation** including 2 negative results (publish honesty)
- 4 month ramp = 'enough to ship', not 'master domain'

**Vulnerability line**:
> "Week 2-4 retrieval module 我 hit one wrong assumption: '10-K filings 是 structured PDF, retrieval like research paper retrieval'. 实际 10-K 是 semi-structured + numeric heavy + footnote-dense, 跟 paper retrieval 不同. 我 retrieval baseline 第一版 accuracy 64%, debug 1 周才意识到 root cause domain mismatch. Lesson: 'apply prior expertise' 不等于 'prior expertise 是 free transfer'. 新 domain check assumption 比 reuse intuition 重要."

---

### STAR 2: Voice Agent Production ASR/TTS Ramp (Alternate)

**S**: 我 algo engineer 出身, 之前没做过 production voice 系统 (ASR/TTS/streaming/telephony). Voice agent debt collection 项目我 lead, 必须 ramp ASR/TTS production stack.

**T**: 4 周内 ship 第一个市场 voice agent MVP.

**A**:
1. **Identify gaps**: ASR provider 选型 (Azure / Google / AWS) / TTS voice cloning / streaming audio frame / telephony provider (Twilio) / call routing infra
2. **Three-track parallel**:
   - Track 1 (Domain learning): read Twilio docs + Azure Speech docs + 跟 2 个 friend (做过 voice 系统) 各 1 小时 chat
   - Track 2 (Technical implementation): set up POC pipeline in 1 week (deliberately simple)
   - Track 3 (Validation): test on 10 internal team member voices first, catch obvious bugs
3. **Source of truth**:
   - ASR/TTS vendor: 我 schedule 30 分钟 call with Azure account team (they 答 specific question free)
   - Telephony: alumni 介绍 1 个 ex-Twilio engineer, 1 hour mentor chat
   - Production streaming: 字节内部 streaming team 1 个 SWE, lunch chat
4. **First delivery week 2**: POC with Azure ASR + ElevenLabs TTS + Twilio call, can dial out & echo back. Not production, but pipeline-end-to-end.
5. **Calibrated**: confident on LLM part, partial on streaming, low on telephony reliability. Flag telephony reliability for SRE team support.

**R**:
- 4 weeks MVP ship Indonesia pilot
- 6 months later voice agent 7 markets
- Indonesia CER 18% → 25% (later)
- ASR/TTS/telephony 我从 0 知识到 6 个月后 mentor junior on production voice

**Vulnerability**:
> "我 wrong assumption: 'streaming audio = HTTP chunked transfer'. 实际 production streaming voice 用 WebSocket + jitter buffer + audio frame ordering, 跟我想的完全不同. 我 spent 3 days build wrong abstraction, 然后 ex-Twilio engineer mentor 30 分钟解释 jitter buffer. **Cold ask expert 30 分钟 > 我 self-debug 3 天**. Now I always ask expert first for unfamiliar production patterns."

---

### STAR 3: BNPL Business + Risk Domain Ramp (Alternate)

**S**: Voice agent 团队让我 lead BNPL chatbot project. BNPL business model + 风控 + 信用 domain 我完全不熟 (我之前做 voice / debt collection, BNPL 是 different funnel — pre-loan + 信用决策).

**T**: 8 weeks design + ship BNPL chatbot MVP.

**A**:
1. **Identify gaps**: BNPL funnel (apply → credit decision → disburse → repay) / 风控 model 输出 (PD/LGD/EAD) / 信用 regulation per market / fraud signal taxonomy
2. **Three-track parallel**:
   - Track 1: 读 BNPL competitor product (Affirm, Klarna) public materials + TikTok BNPL internal product doc 2 weeks
   - Track 2: 立刻 ship FAQ-only chatbot (no credit decisions), test on internal team
   - Track 3: weekly review with BNPL product manager + 1 风控 engineer
3. **Source of truth**:
   - BNPL business: TikTok BNPL product VP, 1 hour onboarding
   - 风控: TikTok 风控 team lead, 2 sessions
   - Compliance: legal + compliance team各 1 session per market
4. **First small delivery week 2**: FAQ-only chatbot, 100 internal users, catch many issues
5. **Calibrated**: confident on LLM/RAG/routing (my expertise), partial on BNPL UX, low on 风控 integration. Explicit ask 风控 team to design schema, I integrate.

**R**:
- 8 weeks MVP ship
- 6 months later: routing 70% → 92%, 80% inbound traffic coverage
- BNPL ramp 让我能后续 cross-pollinate voice agent + BNPL (debt collection + pre-loan = full funnel coverage)

**Vulnerability**:
> "Week 4 我 over-confident, propose chatbot 直接 surface eligibility (BNPL VP case). Compliance team catch this 之前 detection lag 1 week. 我 ramp 期 over-confident 是 systematic risk. 现在 unfamiliar domain ramp 期我 explicit 'I'm in ramp mode, please catch my over-confidence', 让 reviewer 知道 raise concern."

---

## 5 个 Follow-ups (interviewer 追问 + 准备答案)

### Follow-up 1: "How do you decide what to learn deeply vs skim?"

**Answer**:
> "**Rule of thumb**: depth proportional to 'depth-of-impact-on-decisions-I'll-make'.
>
> ConvFinQA 例: I went deep on retrieval + numeric reasoning theory (these were my code modules). I skimmed accounting (I needed to recognize 'EBITDA' but didn't need to compute it).
>
> **Concretely**:
> - Deep: anything I'll write code about, design API for, debug production
> - Skim: contextual knowledge I'll reference but not implement
> - Skip: cool but not on path to delivery
>
> Voice agent: deep on ASR/TTS/streaming. Skim on telephony 法规 (1 paragraph background). Skip on advanced audio DSP.
>
> 测试: 'if X concept is wrong, does my code break?' Yes → deep. No → skim."

### Follow-up 2: "What if you can't find the right expert?"

**Answer**:
> "Then I do **structured trial-and-error with explicit hypothesis logging**.
>
> 真实例: Voice agent 我做 巴基斯坦 Urdu dialect tuning. 字节内 0 个 Urdu native speaker (TikTok 巴基斯坦 ops 都 in 巴基斯坦, 我 in 新加坡 time zone offset). 我 cold-find 巴基斯坦 university linguist (LinkedIn), 但他们 not response.
>
> 我 fallback to structured trial-and-error:
> - Hypothesis log: 'Dialect 1 sounds X way, fallback to Whisper if Y'
> - Each hypothesis: 1-day experiment, defined success metric
> - Each experiment: writeup so future-me / colleague don't repeat
>
> 4 weeks of structured experiments, I had data even without expert.
>
> **Key**: structured trial-and-error 跟 random poke 区别. Hypothesis explicit, success criteria predefined, results logged. 这样 4 weeks 实验 generate 比 4 weeks pure experimentation 多 10× insight."

### Follow-up 3: "How do you know when you're ready to deliver vs still need to ramp?"

**Answer**:
> "**Two tests**:
>
> **Test 1 — Can I articulate what could go wrong?** 如果我 ship X 之前, 能 list 5-10 个 potential failure mode + mitigation, 我 ready. 如果 0-2 个, still ramping.
>
> **Test 2 — Calibration check**. 我 confident on which sub-component, partial on which, low on which? 如果 confident covers 60%+ of code, ship with 'low confidence parts flagged for review'. 如果 confident < 60%, more ramp.
>
> ConvFinQA: week 8 numeric reasoning module, I could list 8 failure modes (numeric overflow, decimal precision, currency unit confusion, negative paren parsing, ...). Confidence 70%. Shipped with senior advisor review.
>
> Voice agent: week 4 POC, 0 list of failure mode for telephony. Not ready. Ramp 2 more weeks before scaling beyond POC."

### Follow-up 4: "Mistake you made because of ramping fast?"

**Answer**:
> "Yes - BNPL VP case (我已经讲过的 vulnerability). Week 4 我 over-confident proposed chatbot surface eligibility specifics. Compliance catch 1 week later.
>
> Root cause: 我 ramped fast on BNPL technical, ramped slow on BNPL compliance landscape. 我 didn't realize 'surface eligibility number' 触发 monetary promise regulation. 这种 cross-functional gap typical in ramp.
>
> **What I learned**: ramp 期 explicit ask 'what should I be careful of from your perspective?' to each function (product / compliance / risk / CS). 不是 'review my design', 是 'what's invisible to me'. 现在我 every new domain ramp 第 1 周做这个 round-robin."

### Follow-up 5: "How is ramping at FDE different from ramping at SWE / MLE?"

**Answer**:
> "SWE / MLE ramp 主要是 stack ramp (codebase, framework, tools).
>
> FDE ramp 是 **stack ramp + domain ramp + customer mental model ramp + organizational politics ramp** 同时.
>
> Stack ramp 我 reuse from SWE experience.
>
> Domain ramp 我用 ConvFinQA 框架 (3 track parallel + source of truth + first small delivery + calibrated confidence).
>
> Customer mental model ramp 是 FDE 独有 — 你不只学 customer 的 domain, 你学 customer team's 内部 dynamics (who decides, who blocks, who funds). 这没有 doc 可读, only 1:1 conversation.
>
> Organizational politics ramp — 例: BNPL VP 跟 compliance team 之间 tension, 我 ramp 期需要 identify 不是 'fix' (太 early), 而是 navigate.
>
> **FDE ramp 比 SWE 复杂 5×**. 这就是为什么 FDE 招的人是已经 demonstrate ramp ability in unfamiliar context."

---

## ❌ 死路答法 (碰了就挂)

### 死路 1: "I quickly learned and shipped."

**为什么挂**: Fake competence. FDE manager 想看 calibration, 不想看 hero story.

**怎么改**: 显式 framework (3-track parallel) + calibrated confidence (我 know X 不 know Y) + vulnerability (我 wrong assumption Z).

---

### 死路 2: "I read all the documentation."

**为什么挂**: 没 prioritize. Doc 通常 50% irrelevant. Reading all = wasted ramp time.

**怎么改**: 显式 prioritize: book intro (1 week) + 真实 sample (10-K filings) + grad student lunch chat. Not "all docs".

---

### 死路 3: "I asked a lot of questions."

**为什么挂**: 太 vague. 问谁? 问什么? 答案怎么 transformed your work?

**怎么改**: Quote 1-2 specific question + specific person. "I cold-emailed 2 NYU Stern grad students, asked 'EBITDA vs operating income, ConvFinQA which more common?'"

---

### 死路 4: "I figured it out alone."

**为什么挂**: No help-seeking signal. FDE 工作 60% 是 cross-function, 不 ask help = silo.

**怎么改**: 显式 list 4 source of truth (grad student / compliance / paper author / ops sit-in). Quote how each helped specifically.

---

### 死路 5: "I pretended to understand."

**为什么挂**: 大忌. FDE manager 听完立刻 next candidate.

**怎么改**: Honest "I told advisor I'm not confident on X, please review". Calibrated confidence 是 strength.

---

### 死路 6: 没讲 "ramp 期 wrong assumption"

**为什么挂**: No vulnerability artifact. Ramp 期 wrong assumption 是 universal — 不讲 = 不 self-aware.

**怎么改**: 显式 1 个 wrong assumption + 怎么 caught + 学到什么. (E.g., "10-K filings 我 assume structured like paper, 实际 semi-structured numeric heavy".)

---

### 死路 7: "I'm now an expert in X."

**为什么挂**: 4 months 不可能 expert. Over-claim signal.

**怎么改**: "Ramp ≠ master. 4 months 我从 0 到 'enough to ship', 不是 'expert'. Senior FDE 知道 distinguish."

---

## ✅ 加分项 (top 5)

### 加分 1: 显式 "three-track parallel ramp" framework

Domain learning + Technical implementation + Validation. 三个 track parallel 不 sequential. 这种 systematic framework 是 senior signal.

### 加分 2: "Ramp ≠ master" 显式

"4 months ConvFinQA 后我 still not finance expert. 是 'enough to ship + know which question to ask'." 这种 calibrated 是 maturity.

### 加分 3: Source of truth = specific human

"我不 Google. Source of truth 是 specific human." Quote 4 specific person + their expertise + how they helped. 不是 generic resource.

### 加分 4: First small delivery week 2

Ramp + ship parallel. Week 2 ship preprocessing, catch domain ignorance early. 这种 deliberate first delivery 是 senior signal.

### 加分 5: Calibrated confidence (what I know / partial / don't know)

"Confident on retrieval, partial on numeric, low on domain reasoning. Flagged low for senior review." 这种 explicit calibration 让 trust 立刻建立.

---

## 一句话总结

> **"Work in unfamiliar context" 的 winning answer 不是讲你多快 ramp, 是用 three-track parallel framework + source-of-truth-is-specific-human + first-small-delivery-week-2 + calibrated-confidence 证明 "我 ramp 有 system, 我 know 我 know 什么, 我 ship 前 explicit flag low-confidence 给 senior review"**.
>
> Ramp ≠ master. Ramp = enough to deliver first piece + identify remaining gaps.

---

## Cheat Sheet (面试前 30s 扫一眼)

```
Question type:
  Behavioral / Ramp-up / Intellectual Humility (4-5 min monologue)
Key skill being tested:
  Systematic ramp framework + ask right person + first small delivery + calibrated confidence + vulnerability

Answer arc (8 段):
  1. Context (20s)              — unfamiliar what (ConvFinQA 4 gaps)
  2. What I didn't know (30s)   — 4 specific gaps
  3. Why deliver anyway (20s)   — timeline + role
  4. Ramp framework (60s)       — 3-track parallel + timebox + checkpoint
  5. Asking right person (45s)  — Source of truth = specific human (4 people)
  6. First small delivery (45s) — Week 2 ship preprocessing, catch domain ignorance
  7. Calibrated confidence (30s)— Confident / partial / low, flag low for review
  8. Outcome + meta (30s)       — Ramp ≠ master, transferable framework

Numbers to drop:
  ConvFinQA:
    4 months deadline (paper)
    4 specific gaps (accounting / SEC 10-K / multi-hop theory / TikTok pipeline)
    Week 2 first delivery (preprocessing, catch 4 bugs)
    Week 4 retrieval, Week 8 numeric reasoning v1
    9-variant ablation including 2 negative results
    Paper top-tier accepted
  Voice agent (alternate): 4 weeks MVP, 6 months 7 markets, CER 18→25%
  BNPL ramp (alternate): 8 weeks MVP, 70→92% routing

Vulnerability:
  "Week 2-4 retrieval module wrong assumption: '10-K filings structured
   like paper, retrieval similar'. 实际 semi-structured + numeric heavy.
   Retrieval baseline accuracy 64%, debug 1 week before realizing
   domain mismatch. Lesson: 'apply prior expertise' ≠ 'free transfer'.
   New domain check assumption > reuse intuition."

Close:
  "Ramp ≠ master. 4 months ConvFinQA = 'enough to ship + know
   which question to ask', not 'finance expert'.
   Framework transferable across domain. 这才是 senior FDE signal."

Red lines:
  - "Quickly learned and shipped" (fake competence)
  - "Read all documentation" (no prioritization)
  - "Asked a lot of questions" (vague, no specific)
  - "Figured out alone" (no help-seeking)
  - "Pretended to understand" (大忌)
  - "I'm now expert in X" (over-claim, 4 months ≠ expert)
  - 没 wrong assumption (no vulnerability)

3 ready STAR (alternate):
  STAR 1: ConvFinQA financial reasoning ramp (★ primary, academic + paper)
  STAR 2: Voice agent ASR/TTS/telephony ramp (production system)
  STAR 3: BNPL business + 风控 + compliance ramp (cross-function)

5 follow-ups ready:
  Q1: Deep vs skim? → "Depth proportional to depth-of-impact-on-decisions"
  Q2: Can't find expert? → Structured trial-and-error with hypothesis logging
  Q3: Ready to deliver vs ramp more? → List 5-10 failure modes + 60% confident on code
  Q4: Mistake from ramping fast? → BNPL VP case, ramp fast technical slow compliance
  Q5: FDE vs SWE ramp? → FDE = stack + domain + customer mental model + politics, 5× complexity

Three-track parallel framework:
  Track 1 (Domain learning):    book + sample + grad student chat + ongoing paper
  Track 2 (Technical impl):     start week 1, apply existing expertise
  Track 3 (Validation):         weekly sample review by domain expert

Source of truth identification (specific human):
  Accounting        → grad student NYU Stern, alumni network
  SEC structure     → internal compliance team
  Multi-hop theory  → 3 papers + email author
  Internal pipeline → sit 1 day with ops team

Calibrated confidence (3-level):
  Confident      — ship with normal review
  Partial        — ship with explicit "review please"
  Low            — don't ship, ask senior to design + I integrate

First small delivery effects (3):
  1. Demonstrates progress to team
  2. Tests understanding (bugs surface domain ignorance early)
  3. Builds momentum + confidence

"Ramp ≠ master" sticker phrases:
  "Enough to deliver first piece + identify remaining gaps"
  "Know which question to ask, not know all answers"
  "4 months = enough to ship intelligent design, not master domain"
```
