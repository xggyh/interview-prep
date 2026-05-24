## Recruiter #1 · Why FDE Specifically — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](why-fde-specifically.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`why-fde-specifically.html`](why-fde-specifically.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"Why FDE specifically / 为什么不是 SWE 不是 MLE"**, 我按这 7 层回答, 不跳序. **核心心法: framework anchor (FDE vs SWE vs MLE 三角) → fit-to-me → fit-to-company → why-NOT-just-X → STAR story → vulnerability → close**.

### 📐 Why FDE Specifically — 7 层结构

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 (literal) |
|---|---|---|---|---|
| 1 | Framework anchor (FDE 三角) | 20s | FDE = engineering depth + customer-facing + AI 业务落地. 不是 SWE (纯 product 深度), 不是 MLE (纯 research / model), 不是 SE (presale 不写 prod code). 三者交集 | "FDE sits at the intersection of three things — engineering depth, customer-facing, and bringing AI from prototype to production for a real business problem. It's not SWE pure depth, not MLE pure research, not SE presale without prod code" |
| 2 | Fit-to-me (具体 evidence) | 30s | 我职业一直在 hybrid: TikTok PayLater 7 markets 同时是 engineer + 业务 PM + 区域 stakeholder. Voice agent ASR cascade 40 min outage 同时 debug + 跟客户跟监管沟通. ConvFinQA 同时 research + product feasibility | "Looking at my career — TikTok PayLater across 7 markets I was simultaneously the engineer, the product owner, and the regional stakeholder partner. Voice agent during a 40-min ASR outage I was simultaneously debugging and on the phone with regulators. That hybrid is FDE" |
| 3 | Fit-to-company (per-company specific) | 25s | OpenAI: research-to-product velocity, GPT-5.5 上线即 enterprise — 需要 FDE 把 model capability 翻译成客户落地. Google: Gemini 3 Pro 2M context 是 platform, 客户需要 architect 帮他用对. (Per-company hook 具体) | "OpenAI specifically — the research-to-product velocity is unique. GPT-5.5 ships and enterprise customers immediately want it deployed. That gap from model release to customer production deployment is exactly what FDE owns" |
| 4 | Why-NOT-just-SWE | 20s | 我试过纯 SWE — 不够. ByteDance 早期我做 pure backend, 6 个月就 itch. 缺 1) customer 直接反馈 loop 2) AI 落地 ambiguity 3) cross-function (engineer / PM / 区域 business). FDE 三者都给 | "I've done pure SWE — at ByteDance early. Six months in I felt the itch for direct customer feedback and the ambiguity of AI productization. Pure backend is too far from the user; FDE closes that loop" |
| 5 | Why-NOT-just-MLE | 20s | MLE 我也试过 (ConvFinQA research methodology) — 我喜欢 model 训练但不想 pure research. MLE 离 customer 远, 离 business loop 远. 我 ConvFinQA 设计了 9-variant ablation 但最终 motivating 我的不是 paper 是 production impact | "MLE — I did the ConvFinQA research, designed a 9-variant ablation. I love training models but pure research keeps me too far from the customer and the business loop. The motivating signal for me is production impact, not papers" |
| 6 | STAR story (1 strong) | 30s | Voice agent ASR cascade 40 min outage — Situation: ASR primary down, 7 markets fall. Task: minimize CER spike + 跟监管沟通 + restore. Action: 5 min triage fallback secondary ASR, parallel call to Indonesia regulator with status, 25 min full restore. Result: CER spike contained 18→25% not 40%, regulator escalation avoided. Reflection: FDE moment — 1 person 同时 eng + customer-facing | "Concrete moment — Voice agent 40-min ASR outage. I was simultaneously triaging the cascade, swapping to secondary ASR, AND on the call with the Indonesia regulator explaining status. CER spike contained 18 to 25 percent instead of 40. One person, both hats — that's the FDE moment, and I want more of it" |
| 7 | Vulnerability + close | 15s | Acknowledge trade-off: FDE 不是 stepping stone — 我知道 FDE 30% travel / 客户压力大 / less depth than pure MLE. 我 want this fit, not "tolerate" it | "I want to be clear — I know FDE means 30% travel, customer pressure, less depth than pure MLE. I'm not picking FDE as a stepping stone to PM or research. I want this fit specifically, and I'd ask you to evaluate me on whether I'm convincing" |

### 🎯 为啥按这个序

**先 framework 再 fit 再 why-NOT 再 STAR 再 vulnerability**: Recruiter 真在筛 5 个 risk — apply-everywhere / will-jump-to-research / can't-handle-customer / won't-last / can't-code. Framework anchor 化解 "你只是 apply 所有 role", fit-to-me 化解 "won't last", why-NOT-just-X 直接 preempt research/SWE 跳, STAR 证明能 code + 能 customer-facing, vulnerability 化解 "stepping stone" 风险. **Per-company specific hook + acknowledge trade-off 是 differentiator**.

### 🔥 哪一层最容易被追问 deeper

- **Layer 6 (STAR Voice agent)**: "那个 outage 你具体怎么 triage?" → 准备好 5-min sub-timeline: T+0 alert / T+2 ASR primary 确认 down / T+5 secondary failover script ready / T+8 regulator call initiated / T+25 primary restored. 每分钟具体 action
- **Layer 3 (Why this company)**: "为什么不是 Anthropic? 不是 Google?" → 准备 per-company differentiator. OpenAI: research velocity + enterprise API + agentic 方向. 不要套用同一稿子

### ⏱ 时间压缩版 (30 min round)

- 30s: "FDE = engineering + customer-facing + AI 业务落地, 三角交集. 我职业一直在 hybrid. Voice agent ASR outage 是 FDE moment"
- 1 min: + why-NOT-SWE + why-NOT-MLE 一句
- 2 min: + 完整 STAR + vulnerability close

### 🆘 卡壳兜底 (针对这题)

1. **被问到 "你不是更适合 PM?"**: "Fair question. PM I'd be one step further from the code — I write the code, I want to keep doing that. The difference between FDE and PM is FDE owns prod implementation; PM owns the spec. I want to own implementation"
2. **被问到 "FDE 离开 customer 后悔?"**: "I've thought about it. Indonesia refund tier where I went CER 18 to 25 — that came from being in the room with the ops team, not from a Jira ticket. I don't see customer time as cost, I see it as input"
3. **没准备好 per-company hook**: "Honestly I'd want to know more about what your FDE team specifically owns — I've read [public hook] but I'd like to hear from you what a typical engagement looks like. Then I can give you a sharper answer on fit"

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

> **"Why FDE specifically" = 60-90 秒 monologue 用 AURA-T framework + per-company specific hook + 5 ready STAR stories + acknowledge trade-off (not stepping stone)**. 不是 motivation 题, 是 fit + clarity + 角色边界 + trajectory 复合考察. recruiter 真正在筛 5 个 risk: apply-everywhere / will-jump-to-research / can't handle customer / won't last / can't code.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| FDE | Forward Deployed Engineer | technically deep + customer-facing + 端到端 |
| AURA-T | Anchor / Underlying / Right fit / Aligned / Trade-off | 60-90 sec answer framework |
| SWE | Software Engineer, 不对客户 | 边界 contrast |
| MLE | ML Engineer, model 内部 | 边界 contrast |
| Research | frontier model paper output | 边界 contrast |
| SE / SA | Sales Engineer / Solutions Architect | pre-sales, deal close 切断 |
| CS | Customer Success, post-sales 关系 | 技术 low |
| Tomoro | Anthropic 收购的英国 FDE 队伍 | 2026 context |
| Operator | OpenAI 浏览器 agent | OpenAI product portfolio |
| Codex | OpenAI 代码助手 | OpenAI product portfolio |
| Vertex AI | Google Cloud ML 平台 | Google FDE 用 |
| Foundry | Palantir 数据平台 | Palantir FDE 用 |
| Constitutional AI | Anthropic safety framework | Anthropic 文化匹配钩子 |
| Frontier proximity | research 团队距离 | FDE 角色 perk 度量 |
| Stepping stone | FDE → PM / 创业 path | recruiter 警惕红线 |
| Right answer faster | 主动重 scope vs slow ship wrong | FDE quote |
| Honest reporting | negative result 公开 (ConvFinQA) | FDE trust 建立 |

### 🎯 5 个核心 framework

**Framework 1**: AURA-T Monologue Structure (60-90s)
- When: recruiter 开场 / HM 第一题
- Algorithm:
  - A Anchor 10s: "Algo engineer at TikTok Global Payment Singapore, 3 years building production GenAI"
  - U Underlying 20s: "Bridge frontier capability to specific business constraint at customer site"
  - R Right fit proof 25s: "Already doing FDE-shaped work — 7 markets, 4 stakeholders, end-to-end ownership"
  - A Aligned target 15s: Company-specific hook ("OpenAI FDE = frontier researcher down the hall")
  - T Trade-off ack 10s: "Not research because outcome > paper; not SWE because customer interaction matters"
- Trade-off: 短不过 60s (没思考), 长不过 100s (啰嗦)
- Tools: 5 STAR stories preloaded, per-company hooks ready

**Framework 2**: 5 Company Differentiation
- When: 任何 FDE 面试都需要 customize
- Algorithm:
  - OpenAI: Frontier model + post-training + agent platform (vLLM / SGLang / SFT / DPO)
  - Anthropic: Safety-first + high-stakes industries (Indonesia tier-3 confirm = constitutional AI pattern)
  - Google Cloud Vertex: Multi-cloud scale + 多 vertical (7 markets × 6 languages analog)
  - Palantir: Data + ops + ontology, NOT LLM-first (TikTok PayLater 支付合规 + 财务系统)
  - Databricks: Data + ML lifecycle (ConvFinQA ablation methodology)
- Trade-off: 模板 pitch = 失败, customize 准备 cost
- Tools: per-company hook table, company-specific story selection

**Framework 3**: 5 Recruiter Risk Mitigation
- When: 准备答题前先 inventory 风险
- Algorithm:
  - Risk 1 (apply-everywhere): 用 specific FDE language, 不模糊
  - Risk 2 (will jump to research): 主动 ack "我考虑过 research, 但 outcome > paper"
  - Risk 3 (can't handle customer): quote Indonesia ops / 7-market 对接故事
  - Risk 4 (won't last): trajectory 讲 long-term "FDE 是 GenAI 行业未来十年 key role"
  - Risk 5 (can't code): 主动 quote vLLM / SGLang / SFT / DPO 技术深度
- Trade-off: ack 风险 vs 显得 defensive
- Tools: each risk → 1-2 specific story

**Framework 4**: 5 STAR Stories Ready
- When: HM 追问细节
- Algorithm:
  1. Indonesia refund tier 1/2/3 (★ scoping, push back, reversibility) — 60s STAR
  2. Pakistan ASR cascade (ops-driven design, 70→92%)
  3. BNPL chatbot 70→92% (data quality > model)
  4. Internal Agent Platform 14 teams (multi-customer abstraction)
  5. ConvFinQA 9-variant ablation (honest reporting negative result)
- Trade-off: 太多 story 散, 5 个 enough
- Tools: STAR template (Situation 1 sentence / Task 1 sentence / Action 3-4 bullets / Result 2 specific numbers + 1 lesson)

**Framework 5**: Anti-Pattern Avoidance (Phrases to Never Use)
- When: 答题中 self-monitor
- Algorithm:
  - ❌ "I love AI" / "Hot new field" (generic motivation)
  - ❌ "Better comp" / "More remote" (financial / lifestyle)
  - ❌ "I don't want to do research" (negative framing)
  - ❌ "FDE is stepping stone to PM" (recruiter 警惕)
  - ❌ "My friend works there" (no substance)
  - ❌ "Can probably cover 90%" (treating as SWE JD)
- Trade-off: 避雷 vs 显得过 polished
- Tools: phrase ban list, recruiter-perspective check

### 🌳 关键决策树

```
什么公司面试?
├── OpenAI → Frontier model + post-training + agent platform hook
├── Anthropic → Safety-first + tier-confirm = constitutional AI
├── Google Cloud → Multi-cloud scale + 7 markets analog
├── Palantir → Payment + ops + compliance, NOT LLM-first
├── Databricks → ConvFinQA ablation = data-driven decision
└── ByteDance/Ali/Tencent → "我已经在做 FDE 工作, 找匹配 title"

Recruiter 在筛什么 signal?
├── "已经在做 FDE 工作"? → Indonesia refund tier 故事
├── 角色边界清晰? → 5 个 role 1-line 对比
├── 公司差异化? → per-company hook
├── 个人热情? → specific story, not abstract
└── Trade-off 自觉? → "give up frontier paper"

追问什么 follow-up?
├── "Why now?" → inflection point + role doesn't compound at TikTok
├── "Why not internal transfer?" → frontier model not built at TikTok
├── "Comfortable with small team?" → I prefer it
├── "Comp target?" → reverse anchor with range
└── "SWE-Production instead?" → depends on customer-facing %
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: FDE vs SWE vs MLE vs Research 边界讲清**
- 核心解法:
  ```
  Research:   distance to customer = max, unit = paper
  MLE:        distance to customer = med, unit = model quality
  SWE:        missing direct customer dialog, unit = feature
  SE / SA:    cutoff at deal close, doesn't own deployment
  CS:         post-sales relationship, technical low
  FDE:        distance to customer = min, unit = customer outcome ⭐
  
  Quote: "I'm not optimizing for a paper or for a single model metric — 
         my unit of progress is customer outcome at scale"
  ```
- Top 3 gotchas: "我也想做 research / product" 模糊 / 把 FDE 当 SE / 不知道 SA 跟 FDE 区别
- Tools: 1-line 5 角色 contrast, "unit of progress" framing

**Problem 2: "我已经在做 FDE 工作" Framing 最强**
- 核心解法:
  ```
  "My current role at TikTok is technically titled Expert Algorithm Engineer + Technical POC,
   but in practice 60% of my time is FDE-shaped:
   - 7 markets, each with own ops / compliance / legacy systems
   - Customer (internal regional ops team) face-to-face scoping
   - End-to-end ownership: scoping → POC → production → on-call
   - Translating business asks (Indonesia OJK compliance, Brazil BCB) into model deliverables
   
   I'm looking for the matching title, not a new skill. 
   I want the FDE org structure where this work is the center, not a side gig"
  ```
- Top 3 gotchas: 听起来 settling (实际是 promotion) / 没量化 (60%) / 没 quote customer-facing
- Tools: "title 不重要, 工作形态匹配" framing, specific % time allocation

**Problem 3: Per-Company Hook Customization**
- 核心解法:
  ```
  OpenAI:
    "I do post-training (SFT / DPO / RL alignment) and inference optimization
     (vLLM / SGLang). At OpenAI FDE you're down the hall from the team that built
     the model. That's irresistible for someone like me — I can ship feedback
     up the chain in days, not quarters"
  
  Anthropic:
    "My Indonesia refund tier-3 confirm pattern is structurally constitutional AI
     — high-stakes decisions get human verification by design.
     Anthropic's safety framing matches the financial / debt collection work I've
     been doing — same first principles"
  
  Palantir:
    "I'm not pitching Palantir as LLM company.
     TikTok PayLater is payment + fraud + compliance + ops.
     I've integrated 7 legacy regional repayment systems, dealt with OJK / BACEN,
     worked with multi-stakeholder ontology. That's exactly Palantir's gravity"
  ```
- Top 3 gotchas: 模板 pitch / 不知道 Palantir 不是 LLM-first / 没 quote 公司 product
- Tools: per-company research (last 3 launches / blog / podcast), specific hook per company

**Problem 4: "Why not SWE / MLE / Research" Acknowledgment**
- 核心解法:
  ```
  "I considered each path honestly:
   - Research: I respect frontier work, but my energy is in business outcome
     at scale, not paper publication
   - SWE: missing the customer face-to-face dialog that informs design
   - MLE: too narrow on model quality, customer trust requires more
   - SE / SA: cutoff at deal close, I want to own deployment
   
   FDE is the only role where I get all 4: technical depth + customer dialog
   + end-to-end ownership + frontier proximity"
  ```
- Top 3 gotchas: "I don't want X" negative framing / 没 acknowledge research 价值 / sound like settling
- Tools: positive framing ("get all 4"), respect for other roles

**Problem 5: Demonstrate Fit Through Specific Stories**
- 核心解法:
  ```
  Indonesia refund tier 1/2/3 (60s STAR):
    S: Indonesia ops wanted full AI refund automation 30 days
    T: scope + push back without losing relationship
    A: Tier 1 auto (70% volume), Tier 2 recommend + human (25%), Tier 3 full human (5%)
    R: 70% throughput up, 0% error rate increase, Maria 至今是 champion
    Lesson: scoping > heroics. Customer values 'right answer faster' over 'wrong answer on time'
  
  Same structure for 4 other stories.
  ```
- Top 3 gotchas: abstract claims no story / 没量化 result (70% / 0%) / 没 lesson
- Tools: STAR template, 5 stories preloaded, lesson 1-line per story

### 🔥 Production gotchas (top 15)

1. "我对 FDE 不熟, 但听起来不错" → fishing for any offer
2. "我想做 customer-facing 的 AI" → 模糊任何角色都能讲
3. "FDE 是 stepping stone 到 PM" → recruiter 立刻降权重
4. "看了 JD 我觉得能 cover 90%" → treating as SWE JD
5. 模板 pitch → 公司差异化失败
6. 没 customer story → "can handle customer" risk 不缓解
7. 没 specific 技术 quote → "can code" risk 不缓解
8. 没 trade-off ack → 显得 "什么都想要" 不成熟
9. "I love AI" → generic 任何 candidate 都说
10. Open salary first → 失去 anchor
11. 80s answer 长过 100s → 啰嗦
12. 60s answer 短过 60s → 没思考
13. "stepping stone to PM" 暗示 → trajectory 不长
14. 没 acknowledge research 价值 → 显得 dismissive
15. "more remote / better comp" → lifestyle motivation 不专业

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| FDE-shaped 工作 | TikTok 7 markets | 60% time customer face-to-face scoping |
| Customer dialog | Indonesia ops + 印尼 OJK | 跨语言跨时区 stakeholder |
| End-to-end ownership | Voice agent 跨市场 | scoping → POC → production → on-call |
| Technical depth | vLLM / SGLang / SFT / DPO | 不是 PPT 工程师 |
| Multi-stakeholder | BNPL chatbot | product / ops / legal / compliance |
| Honest reporting | ConvFinQA negative result | 9-variant 都失败, 公开论文 |
| Right answer faster | Indonesia refund tier | scope down 70% throughput up |
| Constitutional AI 同构 | Indonesia tier 3 confirm | safety-by-design pattern |
| Multi-market scale | 7 markets 6 languages | Google Vertex Multi-tenant analog |

### 🎤 面试现场 quotables (top 8)

1. "I've been doing FDE work without the title. I'm looking for the matching org structure where this work is the center"
2. "FDE is the only role where I get all 4: technical depth + customer dialog + end-to-end ownership + frontier proximity"
3. "My unit of progress is customer outcome at scale, not paper publication or single model metric"
4. "Customer values 'right answer faster' over 'wrong answer on time' — that's the scoping discipline I bring"
5. "OpenAI FDE is down the hall from the team that built the model. I can ship feedback up the chain in days, not quarters"
6. "Indonesia tier-3 confirm pattern is structurally constitutional AI — high-stakes decisions get human verification by design"
7. "I considered research honestly — I respect frontier work, but my energy is in business outcome at scale"
8. "Customer trust built on honest reporting, not polished slides. I published a negative result on ConvFinQA — 9 variants, all worse than baseline"

### 🚨 红线 (top 10 anti-patterns)

1. Stepping stone to PM implication
2. Generic answer ("I love AI / hot new field")
3. No specific story
4. No company differentiation (template pitch)
5. Open salary first
6. "I don't want to do research" (negative framing)
7. "Can probably cover 90%" (SWE JD treatment)
8. "Better comp / more remote" (lifestyle motivation)
9. 没 trade-off ack (显得 "什么都想要")
10. "My friend works there" (no substance)

### 📊 数字 anchors (面试必记)

| Metric | Value | Source |
|---|---|---|
| 60-90 sec monologue target | 80 sec optimal | 短 60 sec 没思考, 长 100 sec 啰嗦 |
| AURA-T section times | A 10s / U 20s / R 25s / A 15s / T 10s | 5 段 |
| 5 STAR stories preloaded | Indonesia refund, Pakistan ASR, BNPL 70→92%, Internal Agent 14 teams, ConvFinQA | 5 ready |
| Per-company hooks | 5 公司 specific (OpenAI/Anthropic/GCP/Palantir/DB) | customize 必备 |
| Indonesia refund tier 1/2/3 | 70/25/5 split, +70% throughput, 0% error rise | top story metrics |
| TikTok 7 markets coverage | 6 languages | scale 故事 |
| 5 recruiter risks | apply everywhere / jump to research / can't customer / won't last / can't code | 提前 mitigate |
| 5 banned phrases | "I love AI / hot field / better comp / stepping stone / cover 90%" | self-monitor |
| 5 anchor phrases | "FDE-shaped work / bridge frontier to constraint / right answer faster / outcome > paper / customer outcome unit" | quote arsenal |
| Salary anchor reverse | "$400-600k total, right base + equity mix" + "What's your range?" | reverse anchor |
| Trade-off ack | "give up frontier paper for outcome at scale" | 成熟 signal |
| Story metric per STAR | minimum 2 specific numbers + 1 lesson | concrete |
| FDE vs 5 role distinction | research/MLE/SWE/SE/CS - 1 line each | 边界 quote |
| Frontier proximity rank | OpenAI 极高 / Anthropic 高 / GCP 中 / Palantir 低 / Databricks 低-中 | company customize |
| Story selection per company | Indonesia tier-3 → Anthropic constitutional / 7-market → GCP Vertex / Payment ops → Palantir Foundry | 切换思路 |
| Follow-up Q ready | "Why now / internal transfer / small team / comp / SWE alt" | 5 Q 备好 |
| Trade-off explicit list | "give up: pure research, pure SWE, pure SE" | trio acknowledgment |
