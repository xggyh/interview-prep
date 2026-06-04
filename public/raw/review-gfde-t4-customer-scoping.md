## T4.1 · customer scoping — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](gfde-t4-customer-scoping.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t4-customer-scoping.html`](gfde-t4-customer-scoping.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"客户说 'we want AI to help our customer service team', 你怎么把这句话变成可 ship 的 project?"** 我按这 8 层回答, 不跳序.

### 📐 Customer Scoping — 8 层 vague-to-ship funnel

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 |
|---|---|---|---|---|
| 1 | Refuse to code 立刻 | 20s | 显示职业反应: "Before I write any code I need 3 things — who, what KPI, what 'done' looks like" — 这 1 句过滤掉 90% 候选人 | "First reaction — I do not write code yet. I run Discovery week 0…" |
| 2 | 5 stakeholder map | 2 min | Exec (funding/timeline/why now) + End user (current pain, day-in-life) + IT (stack, SSO, sec review process) + Legal/Compliance (data residency, audit, regulator) + Adjacent team (谁的 upstream/downstream dependency) — 每类 1-3 人, 30-60 min interview each | "I interview at minimum 5 stakeholder buckets…" |
| 3 | KPI lock (ONE metric + baseline + target + anti-goals) | 2 min | E.g., refund resolution time, baseline 24h (我们 actually measure 1 week first), target 4h, anti-goals = "NOT optimizing agent count / cost / channel mix in phase 1" — anti-goals 跟 goals 一样重要 | "I lock exactly ONE KPI with baseline + target + anti-goals…" |
| 4 | Workflow decomp + tier | 2 min | 把 vague 拆 8-12 step, per step 用 T4.2 3-question (Det/Rev/Latency) → 5 outcome, 选 MVP slice = 客户 highest-pain × lowest-risk × highest-volume step | "I decompose the manual workflow into 8-12 atomic steps…" |
| 5 | MVP carve (vertical slice 3 weeks) | 2 min | Week 1 design + 5 interview + KPI lock; Week 2 build vertical slice E2E (hard-coded happy path OK, 2 edge case); Week 3 demo + 5-10 stakeholder feedback + top 3 prioritized; 3-week 红线 不可破 | "MVP is a vertical slice, not a horizontal slice…" |
| 6 | Pilot rollout 10→50→200 | 1 min | Week 4-8 build production rail (auth/audit/observ/recovery), Week 9-12 measure KPI, daily/weekly review, kill/iterate/scale decision at week 12 | "Pilot is staged 10 → 50 → 200 user…" |
| 7 | Indonesia resume hook | 1 min | "Real example: Indonesia voice agent expansion. Discovery uncovered 3 things US 没有 — language code-mixing (Bahasa+English), carrier API quirks, local payment rail. KPI = collection success rate. Baseline 18%, target 25%, achieved 25% in pilot, 18→25% CER (collection efficiency rate) improvement" | "Concrete example — Indonesia expansion of our voice agent…" |
| 8 | Anti-pattern 总结 | 30s | (a) Skip Discovery → wrong thing perfectly; (b) 不 lock KPI → 半年漂移; (c) MVP > 3 week → 客户决策变化前期白做; (d) Vendor narrative not customer KPI → exec 听不进 | "Top failure modes I actively avoid…" |

### 🎯 为啥按这个序

Layer 1 "refuse to code" 是 trust signal — 让面试官知道你不是 demo-driven. Stakeholder map 在 KPI 前面是因为 KPI 必须从 stakeholder 嘴里挖, 不能你猜. Workflow decomp + MVP carve 紧跟 KPI 是 "把抽象目标变可 ship slice" 的关键转换. Indonesia hook 放第 7 层因为前面 6 层已经搭好 framework, 这时候 land 一个真实数字 (18→25%) 最有杀伤力. Anti-pattern 在结尾让面试官记住你的 discipline.

### 🔥 哪一层最容易被追问 deeper

**Layer 2 (5 stakeholder)** — 必被追 "What do you actually ASK each stakeholder?" → 准备好 per-bucket script: Exec ("what would make you call this a win in 12 weeks / what kills funding"), End user ("walk me through yesterday's worst case / where do you currently work around the system"), IT ("what's your SSO / where does data sit / what's your sec review SLA"), Legal ("what data CAN'T leave the country / what audit retention do you need"), Adjacent ("what breaks upstream if we automate this step").

**Layer 3 (KPI lock)** — 追 "What if customer can't give you a baseline?" → 答: I spend week 0 measuring it myself (logs / shadowing 3-5 agents / sampling tickets). 不接受 "我感觉是 X hours", 必须有 1 week observable baseline.

### ⏱ 时间压缩版 (30 min round)

- 0-3 min: Layer 1+2 (refuse to code + 5 stakeholder)
- 3-12 min: Layer 3+4 (KPI lock + workflow tier with Indonesia case)
- 12-22 min: Layer 5+6 (MVP 3-week + pilot staged)
- 22-27 min: Layer 7 (Indonesia 18→25% concrete numbers)
- 27-30 min: Layer 8 anti-pattern + Q&A

### 🆘 卡壳兜底 (针对这题)

- 被问 "if exec sponsor disagrees with end-user pain" → 答 "I document the divergence in the stakeholder map and surface it as risk in the design doc — week 0 not week 8"
- 不知道客户 stack → "I lead with platform-agnostic prototype (FastAPI + Streamlit), bind to their stack in week 4-8"
- KPI 是 multi-dim (cost + speed + CSAT) → "I pick ONE primary + 2 guardrail metrics (anti-goal violations); if they insist on 3 KPI, week 0 fails and I escalate"

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 核心心智模型 (1 sentence)

FDE T4 scoping = "客户说一句 vague 话 (week 0) → 用 D·K·D·M·P 把它 funnel 成 ONE KPI + ONE vertical slice + ONE end-to-end demo (week 1-3) → pilot 3 rep A/B 4 周 → expand (week 4-12)", 90% 失败在 week 1 没纪律 (没 interview / 没 KPI / 没 say no).

### 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| FDE | half-engineer half-PM half-CS, 坐客户现场 ship 端到端 | T4 round 自我定位 |
| Discovery | week 0 不写代码只 interview + shadow | Day 1-3 |
| MVP | "1 真实 user 走完端到端 happy path 获得真实价值" 的最小切片 | week 1-3 ship |
| Vertical slice | 纵切 1 sub-step 端到端, 不是横切 N steps 半成品 | MVP 选型 |
| Stakeholder map | 5-7 role × 关心啥 × quote × 项目态度 | discovery 产出 |
| D·K·D·M·P | Discovery/KPI lock/Decomposition/MVP/Pilot 主框架 | 整体 12-week 路线 |
| Trust ladder | suggest → confirm → auto-routine → autonomous 4 phase | 反 "100% auto" push back |
| Roadmap doc | Live doc 接所有 scope creep 提议, 推 phase 2+ | 客户加需求时 |
| KPI lock | primary metric + baseline + target + measure + attribution + confounders | day 3-4 必签 |
| Vanity metric | "agent usage rate" 而非 "time saved" | 反例 |
| Anti-perfection rule | MVP 阶段必须 hardcode / single-user / no observability | week 1-3 纪律 |
| ICP | Ideal Customer Profile (sales 用语) | qualification 切片 |
| Champion | 客户内部熟人, 帮你穿针引线 + 内部沟通 | discovery 必锁 |
| Shadow (动词) | 跟 rep 一天观察 vs 30-min interview | rep 不愿意 interview 的 fallback |
| Phase advance gate | 当前 phase 指标稳定 + 客户 sign-off 才能 advance | pilot 路线 |

### 5 个核心 framework / pattern

**Framework 1**: D·K·D·M·P (5 letter 时间线)
- When: 任何 vague request
- Algorithm: D(day1-3 interview) → K(day3-4 ONE KPI 签字) → D(day4-5 workflow N steps 评分) → M(week1-3 vertical slice ship) → P(week4-12 pilot 3 rep A/B → expand)
- Trade-off: 强纪律, 不接 "let me just code first"
- Tools: Streamlit / Vertex AI Vector Search / Gemini 3 Pro / Salesforce read API (MVP 默认栈)

**Framework 2**: 7-role stakeholder interview (per-role 5 questions, 30 min each)
- When: D 阶段 day 1-3
- Algorithm: Buyer (KPI / 预算 / 决策) + Process owner (workflow) + 2 reps (用户痛) + IT (API / SSO) + CFO (ROI) + Champion + 自家 CS
- Trade-off: 7 个 interview 占 2.5 day, vs 直接 build 看似快但 90% return 不上
- Tools: verbatim quote, async fallback (1-pager / shadow / public data)

**Framework 3**: ONE KPI lock template
- When: Day 3-4 强制 sign
- Algorithm: "if you had to bet bonus on ONE number?" + baseline + target post-MVP + target post-pilot + measurement + attribution (A/B / before-after) + confounders
- Trade-off: 客户想要 5 个 KPI, 你必锁 1 个, 其他 secondary
- Tools: sign-off doc (邮件 / Notion), 拒 "let's stay flexible"

**Framework 4**: Workflow decomposition score (耗时×痛×LLM友好×数据可用×风险)
- When: Day 4-5
- Algorithm: workflow 10-15 step 每步 1-5 分, sum 找 top 1-2
- Trade-off: 客观分 > gut feel, 但分要诚实
- Tools: matrix 表格 + 客户 review

**Framework 5**: Trust ladder (反 "100% auto")
- When: 客户要 full auto 时 push back
- Algorithm: Phase 1 (suggest only) → Phase 2 (auto on safe) → Phase 3 (auto + escalate outlier) → Phase 4 (autonomous within bounds), 每 phase 4-8 周 stable advance
- Trade-off: 客户感觉慢 5 个月, 但避免 8+ 月 reset
- Tools: customer-visible phase tracker + advancement KPI

### 关键决策树 (ASCII)

```
模糊 request "用 AI 做 X"
        |
        v
Discovery 5-7 interviews
        |
        v
能锁 ONE KPI?
   |          |
  YES        NO → push back "需要 1-day workshop 确定核心指标"
   v
Workflow N step 评分
   |
   v
Sub-step 耗时 > 20% + 可衡量 + 数据 1 周内 ready + LLM-friendly + reversible
   |
   v
纵切片 1 happy path 端到端
   |
   v
Demo Day 14: live demo + 数据 + phase 2 roadmap
   |
   v
Pilot 3 rep soft → A/B → iterate → expand
```

```
Customer 反应 → 应对
honeymoon → 早期降预期
doubt → 演示 fallback + human-in-loop
impatience → 周报 + mid-week demo
scope creep → roadmap doc, defer phase 2
change of mind → real-pivot vs shiny-toy
"faster" → 给 3 options 让选
"100% auto" → 4-phase trust ladder
```

### Part 2 五个深度问题速查

**Problem 1: D·K·D·M·P 5 letter 深度拆解**
- 核心解法: D (day1-3, 5-7 interview verbatim) → K (day3-4 ONE metric signed doc) → D (day4-5 score matrix) → M (week1-3 anti-perfection vertical slice) → P (week4-12 phased rollout)
- Top 3 gotchas: 用 verbatim quote 不改述 / KPI sign-off doc 强制签 / 不允许 "all of them" 平行 KPI
- Tools: Gemini 3 Pro + Vertex AI Vector Search + Streamlit + Salesforce read API (MVP), Notion sign-off doc

**Problem 2: 5-role × 5-question interview 矩阵**
- 核心解法: per-role tailored question, 30 min standard 节奏 (0-2 开场 / 2-15 开放 / 15-25 收敛 / 25-28 验证 / 28-30 next step), verbatim quote 笔记
- Top 3 gotchas: rep 1 个 anecdote 2 个 pattern / shadow > interview / VP 答 "all good" → 不是真 buyer
- Tools: async fallback (1-pager 5题 10min) / shadow 1 day / champion 转交 / public data (job posts / 财报 / 新闻)

**Problem 3: KPI lock — force ONE number**
- 核心解法: "bet your bonus on ONE number" 强迫表态, sign-off doc 6 字段 (metric / def / baseline / target / measure / attribution / confounders), reject vague language
- Top 3 gotchas: vanity metric (AI usage rate) vs outcome (revenue / time saved) / KPI 多个就没 KPI / "stay flexible" 必给 fallback "lock 但 week 3 可重评"
- Tools: signed Notion doc, KPI dashboard live demo day, 反 vanity test "客户的客户有没有更好?"

**Problem 4: MVP anti-perfection rules (说 NO 的艺术)**
- 核心解法: IN 列 (1 happy path + Streamlit + Vertex AI Vector Search + Salesforce read + 1 rep), OUT 列 (multi-tenant / proper auth / observability / CI/CD / edge case / mobile / multi-lang)
- Top 3 gotchas: hardcode demo 数据假装真 (诚信问题) / hardcode KPI 计算 / 不写到 customer 的 expected scope
- Tools: Demo Day 30-min storyboard (0-3 recap / 3-15 live demo / 15-22 数据 / 22-27 phase 2 roadmap / 27-30 Q&A), stopwatch vs baseline

**Problem 5: Customer 管理 (scope creep / 改主意 / "faster" / "100% auto")**
- 核心解法 (dialog 模板):
  - Scope creep: "Great idea, into phase 2 roadmap (live doc). Now: stay on MVP or delay 2 weeks?"
  - Change of mind: "Based on rep feedback or shiny LinkedIn article?" 分 real-pivot vs shiny-toy
  - "Faster": 3 options (1-wk PoC hardcode / 3-wk MVP integration / both stage)
  - "100% auto": Phase 1-3 trust ladder, "Phase 1 mistake $0, Phase 4 mistake $$$$, net 5 month vs 8+ month reset"
- Top 3 gotchas: 不在 meeting 当场 decide / roadmap doc 让 customer 看到 item 被记 / 多 choice 让 customer 选不让你拒
- Tools: live roadmap doc, scope creep ratio chart, sponsor 替你 enforce

### Production gotchas (top 15)

1. Code week 1 — wrong product 风险 ↑
2. Skip stakeholder interview — design 基于 VP 一人 view
3. Multiple parallel KPI — never know MVP succeeded
4. Automate all 10 steps — never ship
5. No demo until production-ready — no feedback loop
6. Build perfect architecture pre-validation (K8s / multi-tenant / observability)
7. Say yes to every scope add — never ship
8. Promise 100% auto — first incident trust collapse
9. Skip IT/Security week 1 — week 3 demo API blocked
10. Demo without baseline number — "how much better?" 答不出
11. Hardcode KPI 计算 — pilot 全错
12. 不区分 real-pivot vs shiny-toy
13. 不写 anti-perfection 红线 — over-engineer scope
14. No champion identified — 内部沟通卡死
15. 不让 sponsor enforce scope on their team — 你成坏人

### 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| D·K·D·M·P scoping | Voice agent Indonesia | 5-stakeholder, KPI=CER 18%→25%, MVP=overdue Bahasa 100-user, demo 后 pilot 8 weeks |
| Stakeholder map 7-role | TikTok PayLater | ops/compliance/finance/eng/IT/product/regional biz 各 30-min |
| ONE KPI lock | Indonesia refund tier | "refund auto-decision accuracy" 单 metric + baseline + target + measure |
| 3-week MVP | Voice agent Indonesia | 1 intent / 100 user / Bahasa demo end-of-week3 |
| Scope creep management | Internal Agent Platform | 客户 requests → quarterly roadmap, 没 say-yes-to-all |
| Real-pivot vs shiny-toy | BNPL chatbot intent → RAG | phase 切分 ship, 不立刻 pivot |
| "Faster" handle | Voice agent ASR outage | 1-day patch (fallback provider) + 1-month proper fix |
| Trust ladder 4 phase | Indonesia refund tier | tier 1 auto / tier 2 confirm / tier 3 human |
| Customer manage non-tech | TikTok PayLater regional biz lead | storyboard not architecture, dollar number not features |

### 面试现场 quotables (top 8)

1. "I'd resist the urge to scope from my side. The ask is vague on purpose — customer hasn't done the thinking yet. My job in week 0 is discovery, not code."
2. "If you had to bet your bonus on ONE number, what is it?"
3. "MVP is the smallest end-to-end vertical slice, not 80%-of-horizontal-workflow."
4. "Phase 1 mistake costs $0 (rep catches), Phase 4 mistake at scale costs $$$$. Net Phase 1-2-3-4 = 5 months. Direct-4 attempt = 8+ months after reset."
5. "Indonesia voice agent: stakeholder map → KPI=CER 18→25% → MVP single intent Bahasa → pilot A/B → 23% statistically significant → reused playbook for Vietnam/Thailand."
6. "Lock the KPI now (best guess), re-evaluate end of week 3 with real data. Better than no number."
7. "Forecasting's great Phase 3 idea. To not delay your week-3 demo, let me park in roadmap. We decide next sync."
8. "We're delivering agent-architecture v1 that may not need full autonomy. v1 = RAG Q&A. v2 = tool-use. Phase 3 = autonomy. You keep marketing language, we build right thing."

### 红线 (top 10 anti-patterns)

1. Code in week 1 before any interview
2. Accept "all of them" multiple-KPI answer
3. Promise 100% automation day 1
4. Build multi-tenant / observability / CI/CD in MVP
5. Demo without before/after baseline numbers
6. Say YES to every scope creep ask
7. Skip IT / Security alignment (week 3 demo blocked)
8. Hardcode customer's data and pretend it's real
9. No champion identified (no internal eyes/ears)
10. Decide pivot in-meeting (must defer to next sync with data)

### 工具栈 cheat (2026 pricing)

| 阶段 | Tool | 2026 pricing | 用途 |
|---|---|---|---|
| MVP LLM reasoning | Gemini 3 Pro | $2 in / $12 out per 1M | 主对话 + 复杂推理 |
| MVP cheap ops | Gemini 3 Flash | $0.50 / $3 | parse / format / classify |
| MVP reflection | Claude Opus 4.5 | $15 / $75 | high-stakes 复核 |
| Vector DB | Vertex AI Vector Search Serverless | $25/mo starter, $0.40/1M query | managed, 几分钟 setup |
| Frontend | Streamlit Cloud | free tier OK for MVP demo | Python 1 天起页 |
| Frontend prod | Next.js + Vercel | free tier | Phase 2+ |
| Backend deploy | GCP Cloud Run | pay-per-request | serverless, 不上 K8s |
| Storage | Supabase | free tier | Postgres-as-a-service |
| Auth (later) | Auth0 | $35-/mo | proper SSO Phase 2 |
| Observability | Sentry | free tier | error tracking only |
| Workflow engine | Temporal Cloud | $200/mo+ | Phase 2 onward |

### 4-phase trust ladder timing (per phase advance gate)

| Phase | Week | What | Advance criteria |
|---|---|---|---|
| 0 Baseline | 0 | 全人工 | Discovery + KPI lock |
| 1 Suggest only | 1-8 | Agent generate, human review + edit | Override < 10% / time saved > 20% / 客户 sign-off |
| 2 Auto deterministic | 8-16 | Agent auto on safe steps, human review judgment | Auto-step error < 1% / time saved > 40% |
| 3 Auto + escalate | 16-32 | Auto on routine, escalate outlier | Escalation < 5% / customer satisfaction OK |
| 4 Autonomous routine | 32+ | Within bounds (e.g., refund < $X) auto-full | Audit 10% sample / customer sign-off |

### 7-role discovery interview 30-min 节奏 (template)

| 时段 | 内容 | Output |
|---|---|---|
| 0-2 min | 谢时间, 说明今天不是 sales 而是 discovery | rapport |
| 2-15 min | 开放问题 (let them talk) "Walk me through a typical week" | verbatim quote |
| 15-25 min | 收敛 drill into specific recent events "Last week..." | specific pain |
| 25-28 min | 验证假设 复述 "So if I summarize..." | sign-off |
| 28-30 min | Next-step (PoC for follow-up Q + intro to other stakeholders) | follow-up name |

### 5 业务场景变体 (anchor stories per type)

| Variant | KPI | MVP slice | Trust ladder phases |
|---|---|---|---|
| Voice agent Indonesia (anchor) | CER 18→25% | Step 3-7 overdue Bahasa hardcoded 100-user | script-only → LLM-augmented → LLM-led human review → autonomous routine |
| Customer support automation | Deflection rate 0→60% | Top-1 intent "where is my order" 1-click + 兜底转人 | suggest-only → auto-respond per intent → fully autonomous |
| Internal IT helpdesk | Resolution time 30→5 min | 密码 reset SSO API auto | self-serve docs first → guided → auto |
| Marketing content generation | Time per post 8h → 2h | LinkedIn brief → draft → human edit → publish | human-in-loop forever, just faster |
| Data analyst assistant | Self-serve Q/day from BI queue | 1 schema + 5 question pattern + Text2SQL | confirm before expensive query → auto on small |

### 5 customer-management dialog scripts (memorize)

| Situation | Bad response | Good response |
|---|---|---|
| Scope creep "add forecasting" | "Sure I'll add it" → delay | "Great Phase 3 idea. To not delay week-3 demo, I'll write 1-page design doc for week-4 review — decide then." |
| Change of mind "pivot to outreach" | "OK pivoting" | "Real pivot or shiny LinkedIn article? Let me ship qualification demo — it generates outreach draft inline. After demo, decide Phase 2." |
| "Faster please 1 week not 3" | "OK I'll work nights" | "1 week possible with different scope. Option A: 1-week PoC hardcoded 5 leads. Option B: 3-week MVP integrated. Option C: both. Pick." |
| "100% automation now" | "OK fully auto" | "Phase 1 suggest, Phase 2 auto safe, Phase 3 auto + escalate, Phase 4 autonomous routine. Phase 1 mistake $0, Phase 4 mistake $$$$. Net 5 month vs 8+ month reset." |
| "Be flexible on KPI" | "OK no fixed KPI" | "Lock primary now (best guess), re-evaluate end of week 3 with real data. Better than no number." |

### KPI lock sign-off template fields (强制要 sign-off)

| Field | Example |
|---|---|
| Primary metric | "Time saved per rep per week on lead qualification" |
| Definition | 从 lead 进 Salesforce 到 rep 完成 qualified/disqualified 标记总耗时 |
| Baseline | 8 hours/week per rep (2-week time-tracking pilot, 10 rep) |
| Target post-MVP (3w) | 4 hours/week per rep (用 AI 工具的 3 rep) |
| Target post-pilot (12w) | 2 hours/week per rep (10 rep 推广) |
| Measurement method | AI tool 启停时间 + Salesforce activity log, 双 source 校验取 max |
| Attribution | 3 rep AI vs 3 rep 不用, 4-week t-test |
| Confounders | 季节性 (Q4 lead 多) 同期对照 / Rep 经验 (新人慢) 配对相似 reps |
