## 题目

> "Customer says: **'We want to use AI to make our sales team more efficient.'** That's all you got. **First customer meeting next week**. Walk through how you'd **scope this into a 3-week MVP demo**."

或追问形态:

> "Walk through how you'd handle a customer who keeps changing their mind every meeting."

**出处**: Google FDE T4 (Forward Deployed Engineer Scenario Delivery) — HR-tipped, 是 4 道 T4 题里最 **FDE-flavor** 的 — 没有标准答案, 考你**怎么把模糊需求收敛成可交付的产品**.

**Round**: FDE Scoping / Discovery (45-60 min)

---

## 这道题在考什么

最 FDE-flavor 题. 考你**ambiguity navigation + delivery speed + customer empathy**:

1. **Discovery framework** — 不要立即写代码, 先搞清楚 "客户到底要什么"
2. **Stakeholder mapping** — customer 不是单一 entity, 5-7 个不同角色每个都有自己的期待
3. **KPI 锁定** — 必须 ONE number, 否则交付什么都没法判断
4. **Decomposition** — 把 "提升销售效率" 拆成 10 个 sub-step, 选最小可演示切片
5. **Customer 心理** — manage expectation + scope creep + 改变主意 + "要快" + "要 100%"
6. **3-week 节奏感** — week 1 discovery, week 2 build, week 3 demo, 几小时一个里程碑

**不考**: "你会写多 fancy 的 agent 架构". 考 "你能不能 3 周内 ship something 让客户 say wow".

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**FDE (Forward Deployed Engineer)**: 一个混合角色 — 半工程师、半 PM、半 customer success、半 architect. 不是普通 engineer 待办公室写代码, 而是**坐到客户现场**, 和客户工程师 / 业务用户一起把产品从 0 到 1 落地. Palantir / Google / 字节 Lark 等都有这岗.

FDE 的工作不是 "写最好的代码", 是 **"让这个客户 6 个月后给我们续约 + 介绍 3 个新客户"**. 评价标准是**delivery (交付了什么) + customer relationship (客户怎么看你)**, 不是 LOC.

**Discovery (发现 / 调研)**: FDE 项目的 week 0 必备阶段. 不写代码、不画架构图, 只**问问题 + 听 + 记**. 目标: 把客户的 vague request (比如 "we want AI") 翻译成可工程化的 spec.

**MVP (Minimum Viable Product)**: 这个词被滥用了, 正确定义是 **"能让一个真实用户走完一条端到端 happy path、获得真实价值的最小产品"**. 不是 "demo video 拍出来好看的 prototype", 是**真用户能用、能验证商业假设的最小切片**.

**Vertical Slice (垂直切片)**: MVP 的实现方式. 不是把一个 workflow 横向砍掉 80% 步骤 (那样客户感受不到价值), 而是**纵向**砍 — 只做 workflow 里的一个 sub-step, 但把这个 sub-step **端到端做完** (从输入到输出, 包括 UI、数据、模型、deploy). 一个完整的纵切片 + 几个 hardcoded mock = MVP.

---

## 2. 核心问题 / 矛盾

**设想没有 D·K·D·M·P 框架的灾难场景**:

```
Week 1: 客户说 "用 AI 提升销售效率"
        你想: 销售大概是 lead 进来、跟进、报价、成单
        你开始写 LangChain agent + Pinecone + Salesforce SDK
        架构图画了 3 张

Week 2: 你写了 RAG over 客户的产品文档
        + LLM 对 lead 自动 qualification
        + 自动起草外呼 script

Week 3: Demo. 客户问:
        "我们的客户不在国内, 这套用得了 Salesforce 吗?"
        "我们的销售跟进主要靠电话, 不是邮件, 这怎么办?"
        "效率提升了多少? 怎么量化?"
        "Sales VP 不在, 这个项目谁拍板?"

结果: 客户全部疑问, 没人能回答. 项目延 3 个月, 客户失去耐心, 砍预算.
```

**问题根源**:

- **没问清楚 KPI** → 不知道什么叫 "效率提升"
- **没识别 stakeholder** → Sales VP 是不是真 buyer? 销售 ops 在不在?
- **没拆解 workflow** → 客户的 sales 流程具体是什么? 哪一步最痛?
- **没定义 MVP** → "AI 提效" 太抽象, 没法判断 demo 算不算成功
- **没管 customer 心理** → 客户期待 / 担心 / 误解全部没 surface

**D·K·D·M·P 解法**:

```
D (Discovery, day 1-3): 5-7 个 stakeholder interviews
   ↓
K (KPI lock, day 3-4): ONE primary metric + baseline + target
   ↓
D (Decomposition, day 4-5): workflow 拆 10 sub-step, 排时间消耗
   ↓
M (MVP design, week 1-3): 选最痛 sub-step 做端到端纵切片
   ↓
P (Pilot, week 4-12): 3 个真实用户用, 实际测 KPI, 迭代
```

---

## 3. 决策树 — 怎么选 MVP 切片

```
                  ┌────────────────────────────────┐
                  │  客户说 "用 AI 做 X"            │
                  └─────────────┬──────────────────┘
                                │
                  Discovery → 5 stakeholder interviews
                                │
                  ┌─────────────┴──────────────┐
                  │  能锁定 ONE KPI 吗?         │
                  └─────────────┬──────────────┘
                                │
                  ┌─────────────┴──────────────┐
              YES │                            │ NO
                  ▼                            ▼
        ┌─────────────────┐           不能 ship, 不锁
        │ 拆 workflow      │           客户没想清楚
        │ N sub-step       │           → push back: "我需要先做
        │ 排耗时           │              一个 1-day workshop 帮你
        └─────────┬───────┘              确定要追的核心指标"
                  │
                  ▼
        ┌─────────────────────────────┐
        │ 选 sub-step:                 │
        │   - 耗时占比 > 20%            │
        │   - 可衡量 (KPI 能 attribute) │
        │   - 数据 ready (1 周内能拿)  │
        │   - LLM-friendly (语言 / 决策)│
        │   - Reversible / 低风险       │
        └─────────────┬───────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │ 纵切片设计:                  │
        │   端到端 (input → output)    │
        │   1 个 happy path            │
        │   Hardcoded 其余             │
        │   Demo-ready week 3          │
        └─────────────────────────────┘
```

---

## 4. 5-7 个 Stakeholder 分类表

不同角色关心不同事, 你的 discovery 问题必须 **per-role tailored**:

| Role | 在乎什么 | 你问什么 | 失败信号 |
|---|---|---|---|
| **Buyer / Sponsor** (Sales VP) | 业务结果, ROI, 自己的 OKR | "如果这个完美 ship, 你 Q3 哪个 number 变好? 多少?" | 答 "都好" → 不是真 buyer |
| **Sales Ops / Process Owner** | 流程顺不顺、工具不打架 | "现在的 sales workflow 是什么? 哪一步最不爽?" | 不知道流程 → 可能不是 owner |
| **End User** (Sales rep × 2) | 自己日常爽不爽、学不学得会 | "走过你一天 — 30% 时间花哪里? 最讨厌哪步?" | 没时间见你 → 这 project 不重要 |
| **IT / Security** | 数据安全、合规、不破坏现有系统 | "数据放哪? SSO 用什么? 我们能调哪些 API?" | 把你拒之门外 → IT 必须早期 align |
| **CFO / Finance** | 钱花得值不值, 多久回本 | "ROI 阈值多少? Payback 期望? 比较什么 baseline?" | 不在意钱 → 项目可能不是真投资 |
| **Champion / Insider** (你和这家公司里最熟的人) | 帮你穿针引线、内部沟通 | "谁是真正决定者? 公司内部还有什么我没看到的?" | 没有 champion → 项目很难推 |
| **CS / Account Mgr (你自己公司这边)** | 客户关系健康度 | "客户过往合作怎样? 之前有什么坑?" | 答不上来 → 内部对接没做好 |

**Async fallback**: 如果有人约不上 (high-level VIP 常见), 用 async option:

- 发一个 5-question 1-pager 让对方填 (10 分钟比 30 分钟 meeting 容易答应)
- 让 champion 转述 (准确度打折但有总比没有好)
- Shadow 一天 (跟一个 rep 一天, 信息量爆炸, 比任何 interview 都准)
- 翻 public 资源 (jobs page / 财报 / 新闻) 推断公司当前优先级

---

## 5. 具体业务场景 (5 个变体)

### 场景 A: 你现在工作的真实场景 — Voice Agent Indonesia 扩张 (Anchor case)

**背景**: 字节 TikTok Global Payment 想把 voice agent (债务催收) 扩到 Indonesia. 之前在 Brazil / Mexico 跑过, 但 Indonesia 是新市场.

**模糊请求**: "Let's expand voice agent to Indonesia in Q2."

**D — Discovery (week 0)**:

- **Sales VP / Indonesia ops head**: KPI 是 collection effectiveness rate (CER), Indonesia 现在 18%, 目标 25%
- **Local ops manager**: Indonesia 用户特点 — 大量 Bahasa, 部分英文; 文化上更倾向 polite, 直接催款抗拒强; 工作时间 GMT+7
- **Compliance**: Indonesia 央行 (BI) 对催收的合规要求 — 不能威胁、不能 lie 关于身份、不能晚上 9 点后打电话
- **IT**: 用什么 telephony provider (本地 Indosat vs 国际 Twilio), 数据存哪 (Singapore region vs Indonesia)
- **Finance**: 单次外呼成本必须 < $0.30 才有商业价值

**K — KPI**:

- Primary: **CER (collection effectiveness rate)** 从 18% → 25% (8 周内)
- Secondary: handle time / cost per call / customer complaint rate

**D — Decomposition**:

```
1. Customer list pull (CRM → voice agent)
2. Call scheduling (timezone + DNC list)
3. Outbound call initiation
4. ASR (Bahasa → text)
5. Intent classification (acknowledgement / dispute / promise / hostile / no-answer)
6. Response generation (LLM, polite Bahasa)
7. TTS (Bahasa)
8. Conversation flow management (multi-turn)
9. Outcome classification (promised / refused / partial / no-contact)
10. CRM write-back (outcome + recording URL + next action)
11. Escalation to human if hostile / VIP / complex
12. Daily metrics + ops dashboard
```

**M — MVP (week 1-3)**:

- Step 3-7 端到端, 1 个 happy path: "礼貌提醒还款" (最 common intent)
- 其他 step (1, 2, 8-12) hardcoded or stub
- 100 个 hardcoded test 用户, 不接 CRM
- Bahasa Indonesia voice (用 Cartesia / ElevenLabs Bahasa voice)
- Demo: ops head 听 5 通 sample call

**P — Pilot (week 4-8)**:

- 1000 真实 overdue 用户, 接 CRM
- 真实跑 CER 对照实验 (50% agent / 50% 人工 baseline)
- 周会 review, 调 prompt + voice tone + escalation logic

**复用度**: 这个 playbook 之后用于 Vietnam / Thailand / Philippines, 每个市场 3-4 周 MVP.

### 场景 B: Customer Support 自动化

> "客户说: 'AI 接管我们的客服, 70% 自动'"

- **Discovery**: 看 ticket 历史 — top-10 intent 占 80% volume (典型长尾)
- **KPI**: deflection rate (% 不转人工), 目标 60% (从 0)
- **Decomposition**: 10 个 intent 各自 sub-workflow
- **MVP**: 最高 volume 的 1 个 intent (e.g., "where is my order") 端到端 + 兜底转人
- **Trust ladder**: 先 suggest-only (人 review), 6 周后渐 auto-respond, 12 周 fully autonomous for that intent
- **Anti-pattern**: 一上来 10 intent 都做 → 90% 半成品, 0% ship

### 场景 C: 内部 IT helpdesk Agent

> "员工 IT 问题 (Wi-Fi / VPN / 密码 reset), 用 AI 接"

- **Discovery**: ticket 历史 mining, top intents — 密码 reset 占 30%
- **KPI**: avg resolution time, 人 30 min → 目标 5 min
- **Decomposition**: 5 大 intent (密码 / VPN / Wi-Fi / 软件安装 / 硬件)
- **MVP**: 密码 reset (high volume, automatable) 一键解决 — SSO API + 验证 + reset
- **Integration**: SSO / AD / MDM
- **Risk lower than customer-facing**: 内部用户更容忍试错, 可以更激进
- **Self-serve docs**: agent 先 retrieve KB, 给答 + 链接, 把不能解的转人

### 场景 D: Marketing Content Generation

> "1 个 marketing team 想用 AI 加速 content (blog / social / ad copy)"

- **Discovery**: 当前 1 篇 LinkedIn post 多久? 8 小时. 谁写? Brand voice 怎么定?
- **KPI**: time per post (8h → 2h), quality (engagement rate 不下降)
- **Decomposition**: 6 channel (LinkedIn / Twitter / blog / email / ad / video script)
- **MVP**: 1 channel (LinkedIn) 端到端 — brief → draft → human edit → publish
- **Brand voice**: brand guide → system prompt + 10 个 few-shot example
- **不是 full auto**: 创意 + brand voice 难全自动, 人在 loop
- **Reuse mechanism**: 高效的 prompt template 沉淀成组织资产, 下次新 channel 复用

### 场景 E: Data Analyst Assistant

> "Non-tech 业务想 ask data question in English"

- **Discovery**: 现在 BI 团队每天答多少问? 哪些重复? 哪些 schema 复杂?
- **KPI**: questions answered / day by self-serve (vs 现在 BI 队列)
- **Decomposition**: schema 涵盖范围 + question 复杂度分级
- **MVP**: 1 个特定 dashboard / schema (不是 "all data") + 5 个 common question pattern
- **Text2SQL**: agent 出 SQL + run + plot
- **Confirm-required for expensive query**: "this will scan 10TB, confirm?"
- **Verifier**: SQL result 给 LLM 校验语义合理 (sanity check)
- **Iterative**: user 改问题, agent 改 SQL, 不是 1-shot

---

## 6. 实施 Playbook (3-week MVP 标准节奏)

**Week 1 — Discovery + Design** (5 工作日):

| Day | 任务 | 产出 |
|---|---|---|
| Day 1 | 内部 kickoff + champion meeting | Stakeholder 名单 + 调研问题 |
| Day 2 | 5 stakeholder interviews (30min each) | Interview 笔记 |
| Day 3 | KPI lock + 1-page design doc | KPI 文档 + 客户 sign-off |
| Day 4 | Workflow decomposition + MVP slice 选定 | 10-sub-step 矩阵 |
| Day 5 | 架构 sketch + tech stack 锁定 + setup | 架构图 + cloud account ready |

**Week 2 — Build core** (5 工作日):

| Day | 任务 | 产出 |
|---|---|---|
| Day 6 | LLM prompt 第一版 + happy path 跑通 | Prompt v1 + local notebook |
| Day 7 | RAG / context loading (hardcoded data OK) | Retrieval 跑通 |
| Day 8 | 业务逻辑 (workflow orchestration) | Core agent loop |
| Day 9 | UI (简单 web form / Streamlit) | Demo UI |
| Day 10 | 第一次端到端 dry-run + 自我 demo | 可演示版本 |

**Week 3 — Integrate + Demo** (5 工作日):

| Day | 任务 | 产出 |
|---|---|---|
| Day 11 | 集成 (CRM API / Salesforce / 客户系统) | Integration 跑通 |
| Day 12 | Eval (10-50 个 test case) + 调 prompt | Eval 报告 |
| Day 13 | Demo prep + rehearsal | Demo 脚本 |
| **Day 14** | **客户 demo** | Demo 反馈 |
| Day 15 | 反馈整理 + 下阶段 plan | Phase 2 roadmap |

**Anti-perfection rules** (MVP 必须遵守):

- Hardcoded company list / 名单 OK
- Single happy path 端到端 — 其他 path 不做
- No multi-tenancy (1 个 customer 1 套环境)
- No proper auth (basic password 即可)
- No fancy UI (Streamlit / Next.js 简单页够了)
- No production observability (基本 log 足矣)
- No CI/CD pipeline (local deploy 也行)
- No edge case handling (happy path only)

**红线** (这些不能省):

- 数据安全 (客户数据不能进自家训练 / 不能 leak)
- 法律 / 合规底线 (regulated industry 不能跳)
- 可证伪的 KPI 输出 (demo 必须能讲 "对照 baseline 改善了 X")

---

## 7. 易错坑表

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **Week 1 就开始写代码** | 设计错了方向 → 浪费 2 周. 强制 Day 1-3 不能写代码, 只能问 |
| 2 | **没 Discovery interview** | 你做出来的不是客户要的. 5 个 30-min 通话省 6 个月返工 |
| 3 | **多个 KPI** | 客户每个会都改优先级. 锁 ONE primary, 其他 secondary |
| 4 | **想把 12 步全自动化** | MVP 永远不 ship. 纵切片 1 步, 端到端 |
| 5 | **直到 week 3 才让客户看** | 没 feedback loop. Week 2 mid 就该 partial demo |
| 6 | **承诺 100% 自动** | 第一次 incident 就翻车. 推进 trust ladder, 渐进 |
| 7 | **没 Sales VP / sponsor align** | Demo 完客户内部讨论, 决策权不在场, 进度卡住 |
| 8 | **忽略 IT / Security** | Week 3 demo 后 IT 说 "API 不开放" — 全废 |
| 9 | **Scope creep 不管** | 每周加一个 "small request", 3 周变 6 周 |
| 10 | **建 perfect architecture** | Multi-tenant / Kubernetes / observability — MVP 不需要 |

---

## 一句话总结 (Part 1)

> **FDE 3-week MVP scoping = "用 D·K·D·M·P 框架把客户的 vague request 收敛成 ONE KPI + ONE vertical slice + ONE end-to-end demo"**.
>
> 90% FDE 项目失败不是代码写错, 是**第 1 周没 scope 清楚** — 错的 scope 写多好的代码都没用.

---

# Part 2 · 5 个深度问题

## ⚙️ Problem 1: D·K·D·M·P Framework 深度拆解

这是 T4 customer scoping 的**主框架**, 面试场把这 5 个字母讲透就拿下大半.

### 1.1 D — Discovery (调研, Week 0, Day 1-3)

**目标**: 从 "客户说一句 vague 话" 到 "我有 1-page design doc 准备 sign-off".

**手段**: 5-7 个 stakeholder interview (前面 Section 4 讲过) + shadow 1-2 个真实 user 一天.

**Interview 节奏** (30 min standard):

```
0-2 min:   开场, 谢谢对方时间, 说明今天目的不是 sales
2-15 min:  开放问题 (let them talk, you listen)
            "Walk me through a typical week"
            "What's frustrating about your current process?"
15-25 min: 收敛问题 (specific, drill into details)
            "Last week did you encounter X? What happened?"
            "If we could fix one thing tomorrow, what?"
25-28 min: 验证假设 (你已经听到的, 复述确认)
            "So if I summarize, the top pain is X — accurate?"
28-30 min: 结束 + 下一步 (谁是你 follow-up 问题的 PoC)
```

**笔记法**:

- 用 verbatim quote 而不是改述. "Customer said *exactly* this." 在内部讨论时更有说服力.
- 标记 strong claim (重点关注): "this is killing us" / "if you could do this, we'd buy yesterday"
- 标记 disagreement (注意): "Sales VP said X, but rep said opposite"

**Output**: 1-page **Stakeholder Map** (谁、关心啥、quote、对项目的态度).

### 1.2 K — KPI Lock (定指标, Day 3-4)

**最关键的一步**. KPI 锁不死, 整个项目方向都飘.

**问题分类**:

- **Top-line KPI** (买单的 number): revenue / cost / customer count
- **Operational KPI** (中间 number): time saved / accuracy / coverage
- **Quality KPI** (体验 number): CSAT / NPS / complaint rate
- **Reliability KPI** (健康 number): uptime / latency

**ONE primary, others secondary**. 不允许平行 KPI.

**KPI Lock Template** (你要让客户 sign-off 的):

```
Primary KPI: <metric name>
Definition: <如何计算>
Baseline (current): <today's number>
Target (post-MVP): <number after 3 weeks>
Target (post-pilot): <number after 12 weeks>
Measurement method: <how to compute>
Attribution: <how do we know the MVP caused the change>
Confounders: <什么会假提升 / 假下降这个数>
```

**示例 (sales efficiency)**:

```
Primary KPI: Time saved per rep per week on lead qualification
Definition: 当周内 rep 对所有 inbound lead 做完 qualification 的总时长
Baseline: 8 hours/week per rep (self-report + 2-week time-tracking pilot)
Target (post-MVP): 4 hours/week per rep
Target (post-pilot): 2 hours/week per rep
Measurement: AI tool 启停时间 + Salesforce activity log
Attribution: A/B 3 reps 用 AI vs 3 reps 不用, 对比 4 周
Confounders: 
  - 季节性 (Q4 lead 多) → 同期对照
  - 销售经验 (新人慢) → 配对相似 reps
```

**Counter-example fail** (这种就 reject):

```
"我们想 improve sales efficiency."  ← 太 vague
"我们想用 AI 让销售更好."           ← 不可衡量
"我们想 increase win rate AND reduce cycle time AND..."  ← 多个 KPI
```

### 1.3 D — Decomposition (分解, Day 4)

**目的**: 把客户的 workflow 拆成 N 个 sub-step, 排耗时, 找最痛 1-2 步.

**Workflow Map** 通常 10-15 步, 例:

```
Sales workflow (典型 B2B):
1. Lead 接收 (inbound email / web form / referral)
2. Lead qualification (查公司、查角色、判断 fit)
3. First outreach (写邮件 / 打电话 / connect LinkedIn)
4. Discovery call (30-min, 了解需求)
5. Demo / pitch (产品演示)
6. Proposal (报价、scope)
7. Negotiate (条款、价格)
8. Close (sign contract)
9. Handoff to CS (onboarding kick-off)
10. Renew / expand (一年后)
```

**每步打分** (1-5):

| Step | 耗时占比 | 痛感 | LLM 友好度 | 数据可用 | 风险 |
|---|---|---|---|---|---|
| 1 Lead 接收 | 5% | 1 | 5 (parsing) | 5 | 1 |
| 2 Qualification | 30% | 5 | 5 (research + judgment) | 4 | 2 |
| 3 First outreach | 20% | 4 | 5 (writing) | 5 | 2 |
| 4 Discovery call | 15% | 3 | 3 (live conversation) | 2 | 4 |
| 5 Demo | 10% | 2 | 2 (human-heavy) | 1 | 4 |
| 6 Proposal | 10% | 4 | 4 (template + custom) | 4 | 3 |
| 7 Negotiate | 5% | 5 | 2 (high-stakes judgment) | 2 | 5 |
| 8 Close | 2% | 1 | 1 (signature) | 1 | 5 |
| 9 Handoff | 2% | 2 | 4 (summarize) | 3 | 2 |
| 10 Renew | 1% | 3 | 3 (relationship) | 3 | 3 |

**Pick** Step 2 (qualification): 耗时最高 + 痛感高 + LLM 擅长 + 数据可用 + 风险可控.

**Phase plan**:

```
MVP (week 1-3):    Step 2 — Lead qualification 端到端
Phase 2 (4-8w):    Step 3 — First outreach draft
Phase 3 (9-16w):   Step 4 — Discovery call notes + auto-CRM
Phase 4 (4-6m):    Step 6 — Proposal automation
Phase 5+ (年):      Pipeline reasoning / forecasting
```

### 1.4 M — MVP Design (Week 1-3)

**核心原则**: **Vertical slice, single happy path, end-to-end**.

**MVP for lead qualification**:

**Input**: 一个 lead 进来 (name, company, email, source)

**Process**:
```
1. Agent loads CRM context (上次 contact? deal history?)
2. Agent retrieves company info (web scrape, LinkedIn, news)
3. Agent generates qualification summary:
   - Company profile (size, industry, recent news)
   - Decision-maker indicator (title, seniority)
   - Fit score (vs ICP)
   - Suggested next action
4. UI shows summary to rep
5. Rep clicks: [Accept] [Edit] [Reject]
6. If accept → Agent drafts first-outreach email
7. Rep reviews + 1-click send
```

**Output**: Lead 进来 5 min 内 rep 有完整 qualification + draft email, 可决定 accept/reject.

**Tech Stack (deliberately minimal for MVP)**:

- **LLM**: Gemini 3 Pro ($2/$12 per 1M) for reasoning + summarization, Gemini 3 Flash ($0.50/$3) for cheap operations (parsing, formatting). Skip self-host.
- **Vector DB**: Pinecone (cloud, 几分钟接好). 不要自建.
- **Frontend**: Streamlit (Python, 1 天起页). 不上 Next.js.
- **Integration**: Salesforce Read-only API. 不写, 减权限审批时间.
- **Storage**: Postgres (Supabase free tier). 不上 distributed DB.
- **Deployment**: GCP Cloud Run / single instance. 不上 K8s.

**Anti-perfection rules** (前面 Section 6 提过, 这里再强调):

- Hardcoded 100 个 demo lead (不接真 CRM live data)
- 1 个 user (sales VP demo 时用自己账号)
- 1 个 happy path (lead qualified + email drafted)
- 不处理 error case (fail loud + Slack alert ok)

### 1.5 P — Pilot Rollout (Week 4-12)

**目标**: 从 demo (3 rep 假装用) 到 pilot (3 rep 真实工作 4 周用), 验证 KPI.

**Phase plan**:

| Week | 阶段 | 谁用 | 监控 |
|---|---|---|---|
| 4 | Soft launch | 3 个 friendly rep, 半使用 | bug + UX 反馈 |
| 5-6 | Limited pilot | 3 rep 全使用 | KPI 测量 |
| 7-8 | A/B | 3 rep 用 vs 3 rep 不用 | KPI 对比 |
| 9-10 | Iterate | 根据 6-8 周反馈 prompt + UI 调 | KPI 改善 |
| 11-12 | Expand | 10-20 rep | Scale 验证 |

**Each phase advance criteria**: 当前 phase KPI 稳定 OR 客户明确 sign-off.

**Anti-pattern**: 一周后就 push 全公司用. 没 stabilize 就 scale = 大故障.

---

## ⚙️ Problem 2: Stakeholder Interview Techniques (5 个角色, 每角色问 5 题)

前面 Section 4 列了 7 个 role, 这里展开**深度问什么**.

### 2.1 Sales VP (Buyer / Sponsor)

**目标**: 问到他的 OKR + 预算 + 决策权 + 时间线.

**5 个核心问题**:

1. "What's the one number you're being measured on this quarter? If this project moves that number, by how much would be a win?"
   — KPI lock 的种子. 强迫他说具体 number.

2. "If this works perfectly in 3 months, what do you tell your CEO?"
   — 测试他真正想宣传的成就. 可能不是 "AI 项目落地" 而是 "我们 Q3 win rate +3pp".

3. "What's your budget for this project? Approved or pending?"
   — 真 buyer 知道预算. 不知道说明决策权不在他.

4. "Who else signs off besides you? CFO? CIO? Legal?"
   — 提前看 decision chain. 别 demo 后才发现还有 5 个人要 align.

5. "What kills this project? Worst-case scenario you're afraid of?"
   — 让他说出忧虑. 通常是 "AI 出错砸了客户" / "rep 不接受" / "Investment 没 ROI".

**Dialog 示例** (failure to lock KPI):

> **You**: "If this works perfectly in 3 months, what number improves?"
>
> **Sales VP**: *"We want our reps to be more efficient."*
>
> **You**: "Sure — efficient measured how? Time saved? Win rate? Deal cycle?"
>
> **Sales VP**: *"All of them, ideally."*
>
> **You**: "Got it. If you had to pick one — what's the number on **your** quarterly review?"
>
> **Sales VP**: *"Win rate."*
>
> **You**: "Got it. Win rate today is what? Target end of Q3?"
>
> **Sales VP**: *"22% today, want to hit 25%."*
>
> **You**: "Perfect. Let's design MVP to demonstrate movement toward 25% win rate. Other metrics secondary."

**Anti-pattern**: VP 说 "all of them" 你就接受 → MVP scope 漫无边际.

### 2.2 Sales Ops (Process Owner)

**目标**: 问清楚现在的 workflow 是什么, 数据在哪, 工具栈是什么.

**5 个问题**:

1. "Walk me through what a sales rep does from a lead arriving to a deal closing — every step."
2. "Which steps are tracked in Salesforce? Which are off-platform (email / Slack / spreadsheets)?"
3. "Where's the data quality worst? CRM fields that reps don't fill?"
4. "What integration's been attempted before? What worked / didn't?"
5. "If I asked your reps 'what tool do you wish existed', what would they say?"

**Output**: 完整 workflow map + 数据 sources + 已知 painpoints.

### 2.3 Sales Rep × 2 (End User)

**目标**: ground-truth 用户体验. 不能只听 VP / Ops.

**5 个问题**:

1. "Walk me through yesterday — when you started, what you did each hour."
2. "Where's the 30% time you most hate spending? Why?"
3. "What did you do last week that AI could've done?"
4. "What tool do you use the most? The least but is required?"
5. "If a new tool added one button to your workflow, what would it do?"

**关键技巧**:

- **Shadow > Interview**: 跟一个 rep 一整天比 30-min interview 信息量大 10 倍. 安排 1-2 个.
- **Anonymous quote**: rep 抱怨 manager / VP, 不能 attribute. 但 pattern 要 surface.
- **At least 2 reps**: 1 个 rep 是 anecdote, 2 个 rep 是 pattern.

### 2.4 IT / Security (Constraints)

**目标**: 早期 unblock — 你 week 3 demo 前必须知道能调哪些 API、数据放哪、SSO 怎么接.

**5 个问题**:

1. "Where can our service live — your cloud / our cloud / hybrid? What region?"
2. "Salesforce API access — read / write / both? Any restrictions?"
3. "Auth — SAML SSO / OAuth / API key? Need our service to be in your IdP?"
4. "Data classification — what data can pass our LLM? PII allowed? Need on-prem inference?"
5. "Security review timeline — 1 week / 1 month / 1 quarter for new vendor approval?"

**红线**:

- 不能 demo week 3 才发现 IT 拒绝接 API
- 不能 demo 完客户问 "你们 LLM 用什么? OpenAI? Google? 这些 data 能不能给?" 你答不上来

### 2.5 CFO / Finance (ROI Gatekeeper)

**目标**: 知道 ROI 阈值, 让 MVP 能 justify.

**5 个问题**:

1. "What's the ROI threshold for new tool approval? 6-month payback? 12-month?"
2. "What's a sales rep's fully-loaded cost? (用来算 time-saved 的 dollar value)"
3. "What's a deal worth, on average? (用来算 win-rate-uplift 的 dollar value)"
4. "What's your AI budget for the year, and how much is already committed?"
5. "What's a comparable AI tool you bought / evaluated, and what was its ROI claim?"

**用法**: 如果你 MVP 能 demo "saves 5 hr/rep/wk × 20 rep × $80/hr × 50 wk = $400K/year" 比 "agents are cool" 强 100 倍.

### Async Fallback Patterns

约不上 interview 时:

| 失败信号 | Fallback |
|---|---|
| VP 太忙, 推到 2 周后 | 让 Champion 转交 1-page questionnaire (5 题, 10 分钟可答) |
| Rep 不愿被 interview | Shadow 一天 (在公司里跟着, 安静观察) |
| IT 不回 email | Find champion in IT, 走非正式渠道 first |
| CFO 不见 vendor | 让 sponsor 帮你拿到 ROI 阈值 (转述 OK) |
| 所有人都 "下次" | Public data: jobs page (recently hiring X 暗示 priority), 财报 ("our digital transformation" 提了什么), news (recent acquisition / restructure) |

---

## ⚙️ Problem 3: KPI Lock — How to Force ONE Number

**最常见的失败**: KPI 列了 5 个, 没有 primary. 客户每次会换重点.

**强制 ONE 的技巧**:

### 3.1 4 个候选 KPI 的 trade-off 矩阵

对 sales efficiency 题, 候选有:

| Candidate | Pro | Con |
|---|---|---|
| **Time saved per rep** | 直接, 易测 | 时间省了 → 干啥? 可能在玩手机 |
| **Win rate increase** | 业务相关 | 长 lag (3-6 月才能验), MVP 期内难证 |
| **Deal cycle time** | 客观, 易测 | 受市场环境影响, 假信号风险 |
| **Lead quality (Q-to-M ratio)** | 早期 indicator | 客户可能不在乎 quality, 在乎 quantity |

**单一选择技巧**: 问 "if you had to bet your bonus on ONE number, which?". VP 的本能答案就是 primary.

### 3.2 KPI Lock Document Template (强制要 sign-off)

```markdown
# Project: AI Sales Efficiency MVP — KPI Sign-Off

**Date**: 2026-05-21
**Stakeholders**: [VP Sales], [Sales Ops], [FDE Team]

## Primary KPI

**Metric**: Time saved per rep per week on lead qualification

**Definition**: 从 lead 进入 Salesforce 到 rep 完成 "qualified / disqualified" 标记的总耗时 / 周.

**Baseline**: 8 hours / rep / week (基于 2 周 time-tracking pilot, 10 rep, May 1-14)

**Target post-MVP** (3 weeks): 4 hours / rep / week (用 AI 工具的 3 rep)

**Target post-pilot** (12 weeks): 2 hours / rep / week (10 rep 推广)

**Measurement**: 
- AI 工具启停时间 (start / end click)
- Salesforce activity log (qualification 时间戳)
- 双 source 校验, 取 max

**Attribution**: 
- 3 rep 用 AI vs 3 rep 不用 (同 region / experience / 配对)
- 4-week 实验, t-test on per-week time

**Confounders**: 
- Lead 数量浮动 (周内可能差 2x) — 归一化 per-lead 时间
- Rep 经验差 (新人慢) — 配对相似 reps
- 季节性 — 4-week 窗内可控

## Secondary KPIs (monitor, not optimize)

- Win rate (long lag, observe only)
- Rep satisfaction (NPS in week 4)
- AI tool usage (% of leads going through tool)

## Signed
[Sales VP]: ✓ 
[Sales Ops]: ✓ 
[FDE]: ✓
```

### 3.3 当客户拒绝锁 KPI 怎么办

> **客户**: *"It's hard to predict exactly. Let's stay flexible."*
>
> **你**: "I hear you — flexibility is important. But without a primary metric, we won't know if the MVP works. Here's what I propose: **let's lock primary KPI now (best guess), and we re-evaluate end of week 3 with real data**. If the number's wrong, we adjust then. Better than no number at all — would 'time saved per rep' work as our starting hypothesis?"

**关键**: 不要 just accept "let's stay flexible". 必须给一个 fallback (锁但可改) 让对方 sign.

### 3.4 Vanity Metric Trap

客户喜欢的 metric 不一定是 outcome metric:

| Vanity (避免) | Outcome (追) |
|---|---|
| Number of leads processed by AI | Win rate / revenue |
| AI usage rate | Time saved / quality |
| Pretty dashboard | Reps' weekly hours back |
| Model accuracy | Business decision quality |

**Rule of thumb**: 如果这 metric 涨了, **客户的客户有没有更好**? 没有 → vanity.

---

## ⚙️ Problem 4: MVP Carve-out — The Anti-Perfection Rules

**最难的不是"做什么", 是"不做什么"**. MVP 的设计本质是**说 NO 的艺术**.

### 4.1 What's IN vs OUT 矩阵 (硬列表)

对 sales-qualification MVP:

| Feature | In MVP? | Why |
|---|---|---|
| LLM-generated qualification summary | YES | Core value |
| RAG over company info | YES | Quality signal |
| Salesforce read API | YES | Real data |
| Simple Streamlit UI | YES | Demo ready |
| 1 happy path end-to-end | YES | Demo proof |
| Salesforce write API | **NO** | Read-only enough for demo, write 增 IT 审批 1 周 |
| Multi-rep support | **NO** | 1 rep demo 够 |
| Email integration | **NO** | Phase 2 |
| Mobile UI | **NO** | Desktop demo |
| Error handling beyond Sentry alert | **NO** | Fail loud OK |
| Multi-language | **NO** | English only |
| Production observability (DataDog / NewRelic) | **NO** | Local log OK |
| Multi-tenancy | **NO** | 1 customer |
| Auth (proper SSO) | **NO** | Basic password / 仅 demo 用 |
| CI/CD pipeline | **NO** | Manual deploy |
| Vector DB self-host | **NO** | Pinecone managed |
| Auto-scaling | **NO** | 1 instance |
| GDPR / compliance | **NO** (for MVP) | Demo data 用 fake, compliance 在 pilot phase |
| Edge case handling | **NO** | 失败让用户 retry |

**目标**: IN 的 1-2 项是 demo 的 wow moment. OUT 的 N 项是 phase 2+.

### 4.2 Hardcoded OK List

MVP 阶段以下 hardcoded 不丢人:

- **Data**: 100 个 hardcoded test lead (不接 live CRM)
- **Config**: 1 个 ICP definition (不做 customer-side config)
- **Templates**: 3 个 hardcoded outreach template
- **Users**: 1 rep (VP demo 用)
- **Routing logic**: 单 path, 没分支
- **Prompt**: 1 个 prompt 跑天下 (不动态选)

**红线** (这些 hardcoded 后 demo 会翻车):

- 不能 hardcode demo 数据然后假装是 customer's data (诚信问题, customer 一问就露)
- 不能 hardcode KPI 计算 (demo 时假数 → pilot 全错)
- 不能 hardcode 业务规则然后 sign-off (后来改了不告诉客户)

### 4.3 Demo Day Storyboard

Week 3 Day 14 demo 30 min 节奏:

```
0-3 min:   Recap context: "3 周前你说要提升 sales 效率, 今天我演示 MVP"
            重申 primary KPI: "time saved per rep on lead qualification"
3-15 min:  Live demo:
            1. 模拟一个 lead 进入
            2. AI 自动 qualify (live)
            3. 显示 summary + suggested action
            4. 我 (扮演 rep) 1-click accept
            5. AI 自动起草外呼 email
            6. 我 review + send
            
            全程计时: 4 min (vs baseline 30 min)
15-22 min:  Data:
            "If extrapolated: 5 leads/day × 26 min saved = 2 hr/day = 10 hr/week per rep"
            "Multiply by 20 reps = 200 hr/week = 5 FTE worth"
22-27 min:  What's NOT in MVP + Phase 2 roadmap:
            "MVP 是 1 rep 用 + read-only. Phase 2 我会做 write + 10 rep + email auto."
27-30 min:  Discussion: questions + next-step alignment
```

**关键技巧**:

- Live demo, 不放 video. Live 出 bug = 真实, video 客户怀疑 fake.
- 拿 stopwatch 对比 baseline. 数字说话.
- 明确说 "phase 2 roadmap" → 让客户知道 MVP 限制不是失败.

---

## ⚙️ Problem 5: Customer Management — Scope Creep, 改变主意, "快点", "全自动"

**这是 T4 题最 FDE-flavor 的部分**. 不是技术, 是**沟通 + 谈判**.

### 5.1 Scope Creep (客户 week 2 加新需求)

**场景**:

> **客户 (week 2)**: *"Actually, can it also do forecasting?"*

**Wrong response**: "Sure, I'll add it." → MVP 延 2 周.

**Right response**:

> **You**: "Forecasting's a great Phase 3 idea. To not delay your week-3 demo, let me keep MVP focused on lead qualification. I'll write up a 1-page forecasting design doc for our week-4 review — we can decide then to bump it next or stay on the roadmap."

**Tactic**:

1. **Acknowledge** the value of the request (don't reject)
2. **Frame** trade-off ("加这个 = 延 demo")
3. **Park** in roadmap doc (有形, 客户不觉得被忽视)
4. **Defer decision** to next sync (不要 in-meeting decide)

**Roadmap doc** (必备工具):

```
## Sales AI Roadmap (Live Doc)

### MVP (Week 1-3) — IN PROGRESS
- [x] Lead qualification end-to-end

### Phase 2 (Week 4-8) — COMMITTED
- [ ] First outreach email drafting

### Phase 3 (Week 9-16) — COMMITTED IF PHASE 2 SUCCEEDS
- [ ] Discovery call notes auto-CRM
- [ ] **Forecasting (added by VP 2026-05-22)**

### Phase 4+ (TBD)
- [ ] Pipeline reasoning
- [ ] Auto-negotiation drafting
```

每周 sync 客户看 doc, 自己看到自己提的 item 被记下来, 心理满足.

### 5.2 客户改变主意 (week 3 说之前定的方向不对)

**场景**:

> **客户 (week 3 day 12)**: *"Actually I think we should focus on outreach instead of qualification. Can we pivot?"*

**评估问题**:

1. 这是 **真 pivot** (业务发现新洞察) 还是 **shiny new toy** (老板昨天看了一篇 LinkedIn post)?
2. **Sunk cost** vs **future value**: 已 build 的 qualification 切片有多少 reusable?
3. **Demo day** 还剩几天? 还能不能现实地 pivot?

**Decision matrix**:

| Pivot 强度 | Demo 剩余时间 | 决策 |
|---|---|---|
| 真 pivot | > 1 周 | 改方向, 但延 demo 1 周 + 重新 KPI lock |
| 真 pivot | < 1 周 | 不延 demo, demo qualification + 当场 propose pivot phase 2 |
| Shiny toy | 任意 | Push back: "Qualification 切片 demo 完, 然后 phase 2 我可以做 outreach" |

**Dialog**:

> **You**: "Help me understand — when you say outreach is the priority, is that based on new feedback from reps this week, or is it more 'let's see if AI can do this too'? Each has a different answer."
>
> **客户**: *"VP 昨天看了一篇 article 说 outreach automation 是 hottest."*
>
> **You**: "Got it — that's interesting context. **My recommendation**: let me ship qualification demo as planned next week — that demo also generates the first outreach draft, so you'll see outreach inline. After demo, we evaluate which to deepen in Phase 2. Stick with our 3-week plan?"

### 5.3 "Faster please" — 客户要求 1 周交付不是 3 周

**场景**:

> **客户**: *"We need this in 1 week, not 3."*

**Wrong response**: "OK, I'll work nights" → 你疲劳 + 质量崩.

**Right response** — 进一步拆解:

> **You**: "1 week is possible — but with different scope. Let me propose two options:
>
> **Option A — 1-week proof of concept**: 
> - Hardcoded 5 leads, manual run, no Salesforce integration
> - Goal: prove the LLM can qualify
> - Demo: I show 5 sample qualifications, you compare to your manual baseline
> - Risk: not production-shape, can't pilot rep
>
> **Option B — 3-week MVP** (original plan):
> - Real Salesforce integration, 1 rep can use it, end-to-end
> - Demo: 1 rep does live qualification, real Salesforce data
> - Pilot-ready: rep can use it in week 4
>
> **Option C — both**: 
> - Week 1: ship A as 'CEO demo' 
> - Week 2-3: continue B for pilot
> - You get both
>
> Which fits your need? If it's 'show CEO Friday', A. If it's 'pilot rep next month', B."

**Tactic**: **multiple choice** + **explicit trade-off**. 让客户自己选, 不是你拒绝.

### 5.4 "100% automation" — 客户要全自动, agent 自己跑

**场景**:

> **客户**: *"We want full automation. Agent decides without human."*

**Push back logic**:

> **You**: "I get the appeal — but let me walk through why **incremental** is faster than going-straight-to-full-auto:
>
> **Phase 1 (Month 1-2)**: Agent **suggests**, rep 1-click accept. 99% safe. We learn:
> - Where agent's right (training signal)
> - Where rep overrides (failure mode)
> - Rep's trust calibration
>
> **Phase 2 (Month 3-4)**: Agent **auto-acts** on patterns rep historically accepts > 95%. Rep notified post-fact.
>
> **Phase 3 (Month 5+)**: Agent **autonomous** within bounds (deal size < $X, ICP-fit > Y). Rep reviews exceptions.
>
> **Why incremental beats full-auto**:
> 1. **Trust**: rep won't use a tool they don't trust. Skipping Phase 1 = adoption fail.
> 2. **Eval**: we don't know agent's failure modes until we observe Phase 1.
> 3. **Recovery**: Phase 1 mistake costs $0 (rep catches). Phase 3 mistake at scale costs $$$$.
> 4. **Org change**: rep workflow takes weeks to adapt, not 1 week.
>
> **Net**: Phase 1-3 = 5 months to full auto. Straight full-auto = 'attempt for 3 months → 1 major mistake → rolled back → restart from Phase 1' = 8+ months.
>
> **Recommendation**: Phase 1 in MVP. Phase 2-3 on roadmap with clear advancement criteria. OK?"

### 5.5 Customer 心理图 (4 个典型反应模式)

| 反应模式 | 触发点 | 应对 |
|---|---|---|
| **Honeymoon** ("AI 完美解决一切") | Week 0-1, 看了 ChatGPT 觉得万能 | 早期降预期: "AI 强但不全能, 我们看你的具体场景" |
| **Doubt** ("万一 AI 出错") | Week 2, 听到 AI hallucination 新闻 | 演示 fallback / human-in-loop / audit |
| **Impatience** ("怎么还没好") | Week 2-3, 老板催 | 周报 + mid-week demo (让看进度) |
| **Buyer's remorse** ("钱花了值不值") | Week 4-8 pilot 期, 等 ROI | KPI dashboard live + 早期 win 标记出来 |

---

# Part 3 · 把 5 个问题串起来看

这 5 个 problem 其实是**一条时间线**:

1. **D·K·D·M·P framework** = 整体大纲 (week 0-12)
2. **Stakeholder interviews** = D 阶段的具体做法 (day 1-3)
3. **KPI lock** = K 阶段的产出 (day 3-4)
4. **MVP carve-out** = M 阶段的纪律 (week 1-3)
5. **Customer management** = 全周期的人际沟通 (week 0-12)

**FDE T4 面试场**, 这 5 个能讲下来, 加上 1-2 个 specific resume story (Indonesia voice agent / BNPL chatbot / refund tier), 基本是 senior FDE 水准.

---

## 必问 clarifying questions

**1. KPI**

> "If this works perfectly, what business metric improves and by how much? Quarterly revenue / win rate / time saved per rep? I need ONE primary."

**2. Who uses**

> "Sales reps (front-line) or managers (oversight) or both? Different workflow, different design."

**3. Current pain**

> "Walk me through a sales rep's typical day — where's the 30% of time that hurts most?"

**4. Existing stack**

> "Salesforce / HubSpot / Outlook? Calendar? Database? Need to integrate or build from scratch?"

**5. Success window**

> "When is the buying decision (budget approval) — 3 weeks / 3 months / next year? Affects scope and demo focus."

**6. Stakeholders**

> "Who else is involved in this decision — VP / CFO / IT / Legal? Demo audience determines what I optimize for."

---

## 5 步框架 (sample 45-min answer 节奏)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify (KPI, users, pain, stack, stakeholders) |
| 5-15 min | D·K·D·M·P framework overview |
| 15-25 min | Stakeholder map + interview plan (week 0) |
| 25-35 min | KPI lock + MVP carve-out (week 1-3) |
| 35-45 min | Customer management (scope creep / change of mind / faster / 100% auto) |

---

## 我会这样答 (sample 完整应答)

> "Before designing anything, I'd resist the urge to scope from my side. The ask is **vague on purpose** — customer hasn't done the thinking yet. My job in week 0 is **discovery**, not code. Here's how I'd run this:
>
> **D·K·D·M·P framework, mapped to 3 weeks + pilot phase**:
>
> **D — Discovery (Day 1-3)**:
> 5-7 stakeholder interviews — VP Sales (buyer), Sales Ops (process), 2 reps (users), IT (constraints), CFO (ROI), champion (insider). Each 30 min. Output: 1-page stakeholder map.
>
> **K — KPI lock (Day 3-4)**:
> Force ONE primary metric. Likely 'time saved per rep on lead qualification' — baseline 8h/week, target 4h/week post-MVP. Get sign-off doc.
>
> **D — Decomposition (Day 4-5)**:
> 10 sub-step sales workflow. Score each on (耗时 × 痛 × LLM-friendly × data ready). Pick Step 2 (qualification) — highest scoring.
>
> **M — MVP (Week 1-3)**:
> Vertical slice: 1 rep, 1 happy path, end-to-end. Tech: Gemini 3 Pro + Pinecone + Streamlit + Salesforce read API. Hardcoded list, single user, no fancy UI. Demo Day 14.
>
> **P — Pilot (Week 4-12)**:
> 3 friendly reps soft launch → 3 vs 3 A/B → iterate → 10-20 rep expand. Weekly KPI review.
>
> **Customer management tactics**:
> Scope creep → roadmap doc, defer. Change of mind → distinguish real-pivot vs shiny-toy. 'Faster please' → strip to PoC (1 week) or stage (1 week PoC + 2 week MVP). '100% auto' → phase 1-3 trust ladder.
>
> **What I'd avoid**: writing code week 1, skipping stakeholder interviews, multiple KPIs, building perfect architecture pre-validation, promising 100% automation.
>
> **My experience anchor**: I did this exact pattern for Indonesia voice agent expansion at TikTok Global Payment. Week 0 stakeholder map (ops head, compliance, finance, IT, champion). KPI = collection effectiveness rate (single number, baseline 18%, target 25%). MVP week 1-3 = 1 use case (overdue reminder, Bahasa voice, 100 hardcoded users). Demo to ops head week 3. Iterate to broader product week 4-8. Same playbook reused for Vietnam / Thailand / Philippines."

---

## 简历专属 reframe

| 题点 | 你做过的具体动作 |
|---|---|
| Customer scoping framework | Voice agent 7 markets — 每个市场都跑 D·K·D·M·P scoping |
| Stakeholder map | TikTok payment — 7-role 调研 (ops / compliance / finance / engineering / IT / product / regional biz) |
| KPI lock | Indonesia refund tier — single KPI (refund auto-decision accuracy), baseline + target + measurement |
| MVP in 3 weeks | Voice agent Indonesia — 3-week MVP (1 intent, 100 user, demo) |
| Scope creep management | Internal Agent Platform — customer requests filtered into quarterly roadmap, 没 say-yes-to-all |
| Customer change of mind | BNPL chatbot — 初版 intent-only, 客户后来要 RAG, 用 phase 切分 ship |
| 'Faster please' handling | Voice agent ASR 紧急 outage — 1-day patch 切到 fallback provider, 之后 1-month proper fix |
| '100% auto' push back | Indonesia refund tier — 客户要全自动, 用 tier 1 auto / tier 2 confirm / tier 3 human |

**主动 quote** (面试场 30-sec story):

> "Voice agent expansion to Indonesia was exactly this shape. Week 0 = 5 stakeholder interviews — operations head wanted higher CER, compliance wanted regulatory adherence, finance wanted cost cap, IT wanted local data residency, local agent supervisor wanted UX that doesn't anger users. Synthesized into **ONE primary KPI: CER, baseline 18%, target 25%, measured over 8 weeks**. MVP was a single intent (overdue payment reminder), in Bahasa Indonesia voice, hardcoded list of 100 users, demoed end of week 3. Pilot phase weeks 4-8 with A/B against human baseline — hit 23% CER, statistically significant. **Two scope creeps managed**: ops head wanted multi-language fallback (Phase 2), finance wanted real-time cost dashboard (Phase 3). Both went into roadmap doc, not MVP. Reused playbook for Vietnam (week 9-12) and Thailand (week 13-16)."

---

## 5 follow-ups

**Q1**: "Customer is non-technical (CMO buying for marketing). How do you present the design?"

**A**:
- **No architecture diagrams** in first meeting — overwhelms
- Show: **before / after rep workflow** (storyboard, 1 page)
- Show: **estimated time saved** with concrete dollar numbers
- Use customer vocabulary: 'AI assistant', not 'agent / embedding / vector'
- Architecture diagrams reserved for tech-stakeholder meeting (IT, Eng)
- Treat first meeting as a **sales conversation**, not a tech review

**Q2**: "Can't get stakeholder interviews booked. Half the people too busy."

**A**:
- **Async via doc**: send 5-question 1-pager — 10-min ask much easier than 30-min meeting
- **Shadow over interview**: spend a day in the office, observe + chat informally
- **Public data**: customer's job posts (recently hiring X reveals priority), press releases, financial reports, recent acquisitions
- **Champion as proxy**: get your insider to interview people 你 can't reach
- **Reduce to 3 critical interviews** + caveat the design ("based on incomplete discovery, assumptions are: A, B, C")

**Q3**: "Customer wants 'agentic' as buzzword but actual need is simpler (just RAG-based Q&A)?"

**A**:
- **Build what's needed**, not what's hyped: "We're delivering an agent-architecture solution that may not need full autonomy in v1. v1 = RAG Q&A. v2 = add tool-use for actions. Phase 3 = autonomy."
- They keep marketing language ("our new AI agent"), you build the right thing
- **Don't add complexity just for buzzword satisfaction** — over-engineering = slow ship
- Frame in 1-pager: "Architecturally an agent, but Phase 1 is rules + RAG. Autonomy unlocked Phase 2+ when trust + eval ready."

**Q4**: "MVP demo fails — customer underwhelmed. What now?"

**A**:
- **Diagnosis question**: "What did you expect that you didn't see?"
- **Common cause**: KPI not visible in demo (showed features, didn't measure time saved)
- **Common cause 2**: demo had bug, eroded trust
- **Recovery (same day)**: "I heard you — let me regroup. Here's revised plan for next week, focused on showing the KPI delta with real numbers."
- **Better than hiding**: face it head-on, ship revised demo fast
- **Postmortem internally**: why didn't I anticipate this? (usually = didn't pre-show champion mid-week)

**Q5**: "Scope creep — customer keeps adding 'small' requests every week."

**A**:
- **Roadmap document** maintained: every request goes in, dated, assigned to phase
- **Trade-off framing**: "Adding X means delaying Y by 1 week. Which?"
- **Quarterly re-prioritize**: not every meeting (prevents thrashing)
- **Sponsor enforces** scope on their team (you're not the bad guy)
- **Cap MVP scope explicit**: "MVP locked, additions go to Phase 2. Phase 2 plan reviewed week 4."
- **Show velocity hit**: if customer keeps adding, plot a chart of "items added vs items shipped" — when ratio diverges, time to recommit

---

## ❌ 易错点 (top 10)

1. **Write code week 1** — no scoping → wrong product
2. **No stakeholder interviews** — designs based on VP's view alone
3. **Multiple KPIs** — never know if MVP succeeded
4. **Try to automate all 10 workflow steps** — never ship MVP
5. **No demo until production-ready** — no early feedback loop
6. **Build for perfection week 1** — multi-tenant + observability + scaling before validation
7. **Say yes to every scope add** — never ship
8. **Promise 100% automation** — first incident = trust collapse
9. **Skip IT / Security align week 1** — week 3 demo blocked by API access
10. **Demo without baseline number** — customer asks "how much better?", you have no answer

---

## ✅ 加分项 (top 10)

1. **D·K·D·M·P framework** named explicitly
2. **5-7 stakeholder roles** with per-role 5-question playbook
3. **ONE primary KPI** with baseline + target + measurement + attribution + confounders
4. **Smallest vertical slice** for MVP (1 step end-to-end, not 10 steps surface)
5. **3-week timeline** with daily breakdown
6. **Trust ladder** (suggest → confirm → auto) instead of full-auto promise
7. **Roadmap doc** as scope-creep defense
8. **Customer-change-of-mind** distinguish (real pivot vs shiny toy)
9. **Multiple-choice negotiation** ("here are 3 options, you pick") instead of saying no
10. **Concrete resume story** (Indonesia voice agent / BNPL chatbot)

---

## 一句话总结

> **FDE T4 Customer Scoping = "把客户的 vague request 用 D·K·D·M·P 框架收敛成 ONE KPI + ONE vertical slice + ONE end-to-end demo, 3 周内 ship"**.
>
> 90% FDE 项目失败在**第 1 周**: 没 interview / 没 KPI / 没拆 workflow / 没说 no. 写代码前的纪律, 比写代码的技术更决定成败.

---

## Cheat Sheet (印 1 页随身)

```
D·K·D·M·P framework (核心):
  Discovery (day 1-3): 5-7 stakeholder interview
  KPI lock (day 3-4): ONE primary, baseline + target + measure
  Decomposition (day 4-5): workflow N steps, score each
  MVP (week 1-3): vertical slice, 1 happy path end-to-end
  Pilot (week 4-12): 3 rep soft → A/B → iterate → expand

5-7 stakeholder roles:
  Buyer / Sponsor (VP) — KPI / budget / decision power
  Process Owner (Ops) — workflow / data / tools
  End User × 2 (reps) — daily pain, time tracking
  IT / Security — API / data / SSO / auth
  CFO / Finance — ROI threshold, payback
  Champion — internal insider
  Your own CS — historical context

Each role: 5 questions, 30 min, verbatim notes, signed quotes

KPI lock template:
  Primary metric (ONE)
  Definition
  Baseline (current)
  Target post-MVP (3w)
  Target post-pilot (12w)
  Measurement method
  Attribution (A/B / before-after)
  Confounders

Decomposition scoring:
  耗时占比 / 痛感 / LLM 友好度 / 数据可用 / 风险
  Pick highest 1-2

MVP carve-out 红线:
  Hardcoded list OK
  1 happy path
  1 user
  Streamlit / Next.js
  Pinecone (managed)
  GCP Cloud Run (single)
  Read-only API
  No multi-tenant
  No proper auth
  Fail loud (Sentry alert OK)

3-week timeline:
  Wk1 Day 1-5: discovery + design + setup
  Wk2 Day 6-10: build core + UI
  Wk3 Day 11-15: integrate + demo + feedback

Customer management:
  Scope creep → roadmap doc, defer to next phase
  Change of mind → real-pivot vs shiny-toy
  'Faster' → multiple options (PoC vs MVP vs both)
  '100% auto' → trust ladder (3 phase)
  Non-tech audience → storyboard, not architecture
  Buzzword 'agentic' → build right, keep their language

Demo Day 14:
  0-3 recap + KPI
  3-15 live demo
  15-22 数据 (time saved $$)
  22-27 roadmap (NOT in MVP)
  27-30 Q&A

Anti-patterns:
  - Code week 1
  - No interviews
  - Multiple KPIs
  - Try automate all
  - No demo til ready
  - Build for perfection
  - Say yes to all
  - Promise 100% auto
  - Skip IT align
  - No baseline number

Resume hooks:
  - Voice agent 7 markets scoping
  - Indonesia CER baseline 18% → target 25%
  - BNPL chatbot phased ship
  - Refund tier 1/2/3 trust ladder
  - Internal Agent Platform roadmap discipline
```
