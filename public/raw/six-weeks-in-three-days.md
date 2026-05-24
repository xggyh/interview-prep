## 题目（verbatim）

> "Client **demands a 6-week feature delivered in 3 days**. Manage expectations without losing the relationship."

**出处**: fde.academy 客户模拟. 几乎所有 enterprise SaaS FDE 都遇到. Palantir / OpenAI / Anthropic / Stripe FDE 都问过.

**Round**: Client Simulation (45 min)

---

## 这道题在考什么

**不**考你怎么 estimate 工程量, 也**不**考你怎么挤压 timeline. 考 **拒绝的艺术 + 协商的工程感 + 内外双向 alignment**:

1. **不能直接说 no** → 杀关系, 客户找别人
2. **不能直接说 yes** → 杀团队, 你的工程师恨你, 下次出事没人帮你
3. **不能说 "let me check"** → 把决策延迟回 vendor 内部, 看起来 weak
4. **不能说 "we'll try"** → ambiguity 是承诺反模式, 后续 blame game
5. **必须 surface 真实需求** → 客户「6 周功能」往往 80% 是 nice-to-have
6. **必须 offer 备选** → 不替客户做决定, 给他 menu
7. **必须 written** → 口头承诺 24h 后会漂移

这是一道 **scope negotiation 题里最经典的形态**. 你的目标不是「让客户接受 6 周」也不是「3 天 ship 全部」, 而是**找到一个双方都能接受 + 你团队能 deliver + 不损害产品质量**的中间路径.

---

# Part 1 · 教学讲解

## 1. 四个核心术语先解释

**Scope (范围)**: 一个 feature 包含的所有功能点. "Multi-tenant analytics dashboard" 听起来一个 feature, 实际可能包含: 数据 schema / ETL pipeline / 权限模型 / UI / 导出 / 提醒 / 历史趋势 / 多语言 / 移动端. 你的 job 是把这 9 个组件**显式拆解**.

**Quality (质量)**: 包含 bug rate / latency / reliability / 测试覆盖 / 文档 / 可维护性. **质量是不可见维度** — 客户感觉不到, 但你们 6 个月后 fix bug 时就感觉到了.

**Time (时间)**: 显性时间 (deadline). 还有隐性时间 (技术债 catch-up time, post-launch fix time, on-call cost). 客户只看显性, 你必须 surface 隐性.

**Iron Triangle (铁三角)** = Scope × Quality × Time. 工程界的物理定律: 三者**只能选 2**. 客户要 "6 周 scope + 3 天 time" → 必须牺牲 **quality**. 但客户不会主动接受 "low quality", 你得用语言让他们意识到 trade-off.

**MVP (Minimum Viable Product)**: 不是 "Minimum Viable" = 凑合能跑, 是 "Minimum Viable" = **最小但仍 viable** — 解决核心问题, 不解决全部问题. MVP carve-out 是这道题的核心技能.

**Goal-post shifting (目标移动)**: 客户当下说 "3 天就够了", 等你 ship 完, 客户说 "现在 ASAP 我要 Tier 2". 经典模式, 必须**用文档 ahead-of-time** 预防.

---

## 2. 这个场景的核心矛盾是什么

**矛盾 1: 信任 vs 可行**

直接说 "不可能" → 客户不信任你的判断, 觉得你在保护团队偷懒. 不说 "不可能" 又会被当作 "yes" 应承.

**矛盾 2: 短期客户满意 vs 长期产品健康**

你 3 天 ship 一个垃圾 → 客户当周满意, 下周开始抱怨 bug, 你的 team 接下来 4 周修这些 bug, **总耗时比 6 周还长**.

**矛盾 3: 个体面子 vs 系统利益**

你的 AE 在房间里盯着你, 希望你给客户 yes 来 close deal. 你的工程经理在 Slack 上盯着你, 希望你 push back. 你两个都不能 alienate.

**矛盾 4: 表面需求 vs 真实需求**

客户说要 "完整的 multi-tenant analytics dashboard". 真实需求可能只是「明天给 CFO 一张 chart」. 你的工作是**深挖到真实需求**, 但又不能让客户感觉你在 "diminish" 他们的 ask.

**矛盾 5: 客户体面 vs 内部 alignment**

你内部还没跟 engineering 对齐, 但客户在等你回答. 答错损客户, 不答损客户耐心. 用 "I'll get back in 30 min with a structured proposal" 平衡.

**矛盾 6: 这单 vs 长期关系**

如果客户**真的可能** churn (流失), 是不是应该 just say yes? 答案: **如果 yes 意味着 ship 灾难, churn 反而更快**. 你的 job 是教育客户**「ship 灾难比 churn 更糟」**.

---

## 3. 决策树 / 反应模板

| 时间 | 你的核心动作 | 输出 |
|---|---|---|
| **5 分钟内 (会议中)** | Acknowledge + 问 "what's driving the timeline" | 听到真实 driver |
| **5-15 分钟** | Decompose 「6 周 scope」into discrete components | 让客户看到 scope 内部结构 |
| **15-25 分钟** | 提 "must-have-day-3" 问题, 把 monolithic ask 拆成 P0/P1/P2 | 找到 20% 解决 80% 的部分 |
| **25-35 分钟** | 给 3 选项 (3 天最小 / 2 周中等 / 6 周完整) + tradeoffs | 让客户 choose, 你 not deciding |
| **35-45 分钟** | Recommit specific date + 提出 written commitment | 1-pager design doc 在 24h 内发出 |
| **会议后 24h** | 内部 alignment + design doc + 跟客户 review | 双方签字的 scope 协议 |
| **3 天 / 2 周末** | Ship + retro + 自然 roll into Tier 2 讨论 | 信任建立 + 后续 roadmap |

---

## 4. 关键利益相关方对照表

| Stakeholder | 他们在意什么 | "6 周变 3 天" 时他们的内心 OS | 你对他们的关键动作 |
|---|---|---|---|
| **客户 业务方** (e.g., VP Sales 想要 dashboard) | 自己的 CFO 会议 / quota | "我承诺了 board, 必须 ship" | 帮他**重构承诺**: "你向 board 承诺的是 chart, 不是 dashboard. 我让你 ship chart" |
| **客户 工程方** (e.g., 客户的 Tech Lead) | 集成质量 / 后续维护 | "怕你们 ship 垃圾我们要 own" | 提供完整 design doc, 让他参与 review |
| **客户 决策者** (CFO/CEO) | ROI / 风险 | "vendor 能不能 deliver" | 透明 tradeoff: "你想要 ship 还是 ship 对" |
| **你的 AE** | 这单能签否 | "Don't lose the deal" | 私下对齐: "我会 ship 一个能签单的版本, 不 ship 垃圾" |
| **你的 Engineering Manager** | 团队 sanity + 技术债 | "这是 vendor 端 hero culture" | 内部 escalate, 把 demand 转 official scope doc |
| **你的工程师** | 自己的工作量 + 周末加班 | "又要 heroics?" | 内部明确: "Tier 1 是 3 天工作量, 不是周末加班" |
| **客户内部 champion** | 自己面子 + 内部影响力 | "我推这家厂商, 不能 ship 垃圾让我 backlash" | 单独沟通: "Tier 1 让你 ship, Tier 2-3 让你 look ahead" |
| **你的法务 / contract team** | 合同 vs 实际 scope | "deliverable 是什么?" | Design doc 当 contract amendment 让法务 sign |

---

## 5. 具体业务场景 (4 个变种带人物)

### 场景 A: TikTok PayLater Indonesia ops 要 "完整 refund 自动化" 上线 (贴近 Gao Xin 工作)

**人物**:
- 你 (FDE) + 你的 EM Linda
- 客户 (Indonesia ops): Maria (Ops Director), Andi (Tech Lead), Budi (Compliance)

**他们的 ask**:
> "我们需要 **AI agent 自动处理所有 refund 请求**, 30 天内上线. 月底前 board demo."

**真实 driver**: Maria 在 board 上承诺了 "AI 提效", 怕落不下来.

**6 周 vs 3 天版本**:
- **6 周完整**: AI agent 看完 case file → 自主决定 refund 金额 / 决策推送给客户
- **3 天 MVP**: AI agent 自动提取 case info → 推送给 human ops, human 决策, AI 自动 fill form

→ 这正是 Gao Xin **真实做过的 Indonesia refund tier scoping**. Tier 1 上线 → 信任建立 → Tier 2-3 后续 graduate.

### 场景 B: Acme Bank 要 multi-tenant analytics dashboard for CFO meeting

**人物**:
- 你 + Raj (CTO) + Linda (CFO 的 EA)

**他们的 ask**:
> "Need the **multi-tenant dashboard** with drill-down, exports, scheduled reports, alerts, mobile view. **Thursday — 3 days**."

**真实 driver**: CFO 周四要 board Q3 review.

**真实需求**: 5 张图, 不是 platform.

**6 周 vs 3 天 carve**:
- 6 周: 完整 dashboard with everything
- 3 天: 静态截图 of top-10 customer chart + revenue. Email 给 CFO PDF format

### 场景 C: Bank 的合规团队要 "AI agent 全链路审计"

**他们的 ask**:
> "Need every LLM decision logged, replayable, query-able, exportable for regulator. 30 days max."

**真实 driver**: 监管来访 30 天后, 要展示 governance.

**3 天 MVP**:
- Read-only log dashboard with 5 fields per decision: timestamp / input / output / model_version / decision
- Export to CSV (regulator format)
- 不做: real-time alerting / advanced filters / privacy redaction (Tier 2)

### 场景 D: 内部团队要 "Voice agent 接 7 个新市场" 30 天内

**他们的 ask**:
> "PayLater 要扩 7 个新市场 (越南 / 菲律宾 / 印度 / 巴基斯坦 / 埃及 / 沙特 / 巴西). 30 天上线."

**真实 driver**: 业务目标已定, 不上线就丢市场.

**6 周 vs 3 天**:
- 6 周完整: 每市场原生 ASR / TTS / LLM fine-tune
- 3 天: **只越南** (next priority), 用 multilingual model + minimal prompt eng, 其他 6 个市场分阶段
- **Joint ownership**: 业务方 own data 收集, 你 own 模型

---

## 6. 工程上 / 应对上要做什么 (Playbook)

按 **会议中 / 24h / 3 天 ship / 2-6 周** 4 个阶段:

### 阶段 1 · 会议中 (0–45 min)

1. **不要急着回答 yes/no**. 先 5 分钟问 clarifying questions
2. **挖真实 driver**: "Help me understand what happens on day 4 if this isn't ready"
3. **拆 scope**: "Of the full feature, what's the must-have-on-day-3 vs nice-to-have"
4. **提 3 选项**: 3-day minimum / 2-week medium / 6-week full, 各自 explicit tradeoffs
5. **Recommend 一个**, 但不替客户决定: "My recommendation is X because Y"
6. **One ask back**: 让客户 contribute something — 数据 / 决策 / 试点用户
7. **Commit 时间**: "Written design doc by EOD today"

### 阶段 2 · 24 小时内

8. **内部 align**: 跟 EM + AE 30 分钟 sync, 把 Tier 1 工作量确认
9. **Design doc** 写完发客户 (templates 见下)
10. **Customer review** 30 min, 客户签字 / 提修改

### 阶段 3 · 3 天 ship

11. **Daily 15-min sync** with 客户 (visibility 让他不焦虑)
12. **Day 1 end-of-day status**: 进度 / 风险 / 需 unblock
13. **Day 2 demo**: 内部先 dry-run, 确认 ship 物
14. **Day 3 deliver** + run customer demo

### 阶段 4 · 2-6 周 (Tier 2/3 自然 graduate)

15. Tier 1 stable 后, 主动 propose Tier 2 timeline
16. 把后续 roadmap formalize 成 product feature, 不是 vendor heroics
17. Retrospective: 内部讨论 hero culture 是否 sustainable

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **直接说 no** | 关系 ender. Replace: "Here's what we can ship in 3 days..." |
| 2 | **直接说 yes** | 团队 ender. Replace: 用 tier 化 commit Tier 1 |
| 3 | **"Let me check with engineering"** | 看起来 weak + middleman. Replace: "Let me propose 3 options in 30 min" |
| 4 | **"We'll try our best"** | 模糊承诺 = 后续 blame game. Replace: 具体 day + deliverable |
| 5 | **没问 driver** | 错过 80% 减 scope 的机会 |
| 6 | **Heroics culture** ("we'll work weekends") | 后续每次都被预期 heroics, team burnout, attrition |
| 7 | **Verbal commitment only** | 24h 后客户记成 "你说要 ship 全部" |
| 8 | **没 internal alignment 就承诺** | EM 当场否决, 公司面子 -100 |
| 9 | **Tier 1 ship 后 ghost 不提 Tier 2** | 客户感觉 abandoned, 信任崩 |
| 10 | **Tier 1 ship 完美就停** | 客户 goal-post shift, 你 commit Tier 3 速度更快 → 灾难 |

---

## 一句话总结 (Part 1)

> **"6 weeks → 3 days" 的真正问题不是「时间太短」, 是「客户没想清楚自己要啥」**.
>
> 你的 craft 不是挤压 timeline, 而是**通过结构化提问把客户 monolithic ask 拆解, 找到 must-have, 然后 ship 它 + 把剩余的 90% 放进 official roadmap**.
>
> 60% 的 "6 周变 3 天" 在你拆完 scope 之后会自动变成 "3 天足够". 剩下 40% 是真有需求, 那时 tier-1 + roadmap 是唯一可持续答案.

---

# Part 2 · 5 个深度问题 (Client Sim 硬核细节)

## ⚙️ Problem 1: Diagnose What They ACTUALLY Need — 真实需求挖掘术

**80% 的 "6 周变 3 天" 在你深挖之后会发现真实需求只占 20%**.

### 1.1 "What's driving the timeline" 是第一句

你的 first response 不应该是 "OK let me think about scope" 或 "let me check with engineering". 应该是:

> "Before I respond on scope, **help me understand what's driving the timeline**. Is there a specific meeting, deadline, customer commitment, or board ask that anchors the 3-day window?"

**为什么这句话重要**:

- **70% 的情况下**, 客户 自己也没想清楚 driver. 你的 question 让他 step back
- **20% 的情况下**, 客户 reveal 真实 driver — 而 driver 本身比 6-week feature 小得多
- **10% 的情况下**, 客户 真的有刚性 deadline (e.g., 监管要求), 这时你转 negotiation

### 1.2 真实 driver 的 6 个 archetypes

每种 driver 对应不同应对:

| Driver 类型 | 示例 | 真实需求 | 应对 |
|---|---|---|---|
| **A. Board / CEO 承诺** | "CFO 要看 dashboard" | 1 张 chart | Ship a chart, 不 ship dashboard |
| **B. 监管 / 合规 deadline** | "OJK 要看 audit log" | Read-only audit panel | Ship MVP audit panel, defer advanced filters |
| **C. 竞品 demo 比较** | "competitor 演示了..." | 一个能演示的 prototype | Ship demo-only version, 标记 "preview", explicit not production |
| **D. 已签合同 deliverable** | "contract says Q2" | Contract amendment + tier | 让法务介入 amend |
| **E. 内部 PM 焦虑** | "PM 觉得 fall behind" | 看到 progress | Visibility (weekly demo) 而不是 feature ship |
| **F. 客户自己也不知道** | "感觉应该早点要" | 没真需求 | 引导客户 prioritize, 帮他想清楚 |

### 1.3 深挖问题清单 (在客户回答 driver 后用)

| Q | 你期待发现 |
|---|---|
| "Of the full feature list (multi-tenant + drill-down + exports + alerts + scheduled + mobile), **which is the one your CFO actually opens during the meeting**?" | 大部分功能他根本不看 |
| "If your CFO sees the dashboard, **what specific question does she ask first**? Let's solve that first." | 通常 1-2 个 question |
| "What would happen if we ship only the chart by Thursday, full dashboard 2 weeks later? **What does the CFO see Thursday that she doesn't see today**?" | 让他自己说 "Thursday 只要 chart" |
| "Is there a previous report your team already uses? Can we **extend that** rather than build new?" | 60% 情况已有报表, 客户没意识到 |
| "Who else needs this? **Just CFO Thursday**, or also CRO / Board / Audit?" | 单点需求 vs 多点需求, 设计不同 |

### 1.4 把模糊 ask 转 SMART deliverable 的语言模板

客户原话:

> "We need the multi-tenant analytics dashboard by Thursday."

你的 reframe:

> "OK so let me try to make this concrete. By Thursday, **the artifact that matters** is: a chart that the CFO can open during her Q3 board review and answer the question 'how is each customer trending in revenue?'.
>
> If that's right, **the deliverable is** = an interactive visualization (or even a static PDF) showing **revenue per customer for top-10 customers** for last 90 days. **Not the full dashboard**, just that one chart. Does that match what she needs?"

→ **关键转化**: 从 "multi-tenant analytics dashboard" → "chart for CFO showing top-10 revenue trend". 减 scope 80%.

### 1.5 当客户拒绝缩减 scope 时

**Pattern 1: 客户坚持 "we need all of it"**

你的回应:
> "I hear you want the full feature. **Two paths forward**:
>
> **Path 1**: We ship the **must-have-for-Thursday** (chart) in 3 days. **Same 3-day deadline**, but only the chart. Full dashboard ships 2-3 weeks later. Total time to complete dashboard: ~3 weeks.
>
> **Path 2**: We commit to ship 'full dashboard' in 3 days. **Reality**: it will have bugs, no exports won't actually work, alerts will be flaky. We'll spend the **next 4 weeks fixing bugs**. Total time to **stable** dashboard: ~5 weeks.
>
> **Path 1 gets you to a stable full dashboard faster**, and gives the CFO her chart Thursday. **Path 2 gets you a buggy dashboard Thursday and a stable one in 5 weeks**.
>
> Which do you prefer?"

→ 用**时间数学**而不是「能不能做」让客户自己看到 Path 2 是 trap.

**Pattern 2: 客户说 "but our competitor demoed all of this"**

你的回应:
> "Could be true. Two things to consider:
>
> (1) Demo ≠ ship. A demo can be hacked together for show; production is different.
>
> (2) If they can really ship full features in 3 days with quality, **they should win this deal**. But based on my 5 years of building these, what they likely shipped is a similar minimal version dressed up for demo. I'd encourage you to ask them: **what's the SLA on this once we go live?**
>
> Meanwhile, my offer is the **most honest version of what we can ship that gives you what you actually need Thursday**, with full dashboard in 3 weeks. That's the same thing competitor will end up doing — they just won't tell you upfront."

### 1.6 Internal alignment before saying anything (3 分钟规则)

会议中, 如果你需要内部 quick check, do 30 秒 not 30 分钟:

> "Let me take 30 seconds to confirm one thing with my engineering team — I want to make sure my proposal is grounded. *(Slack EM: 'I'm proposing Tier 1 = static chart in 3 days, OK?' EM: '✓')* OK confirmed. Here's my proposal..."

**绝不**:
- "Let me get back to you in 2 days"
- "I need to talk to engineering first"

**绝对** OK:
- "Let me check 30 seconds while you keep talking"

---

## ⚙️ Problem 2: Negotiation Framework — Scope/Quality/Time Triangle

**铁三角是 negotiation 的语言基础. 客户不懂铁三角, 你的 job 是教他**.

### 2.1 铁三角解释 (用客户能懂的语言)

| 维度 | 客户看到 | 客户感受到 (但不一定意识到) |
|---|---|---|
| **Scope** | 功能数量 | "我要的都给我" |
| **Quality** | bug-free / fast / 易用 | "正常用就行" — 但 bug 出来超敏感 |
| **Time** | deadline | "越早越好" |

**Iron Triangle 法则**: **只能选 2**.

```
       Scope
      /     \
     /       \
    /  PICK   \
   /    2      \
  /             \
Quality ———————— Time
```

| 选 | 含义 |
|---|---|
| Scope + Quality (放弃 Time) | 6 周完整功能, 高质量. Standard 路径 |
| Scope + Time (放弃 Quality) | 3 天完整功能, 低质量. **客户不接受 explicitly, 但默认 demand 这个** |
| Quality + Time (放弃 Scope) | 3 天部分功能, 高质量. ⭐ **你应该 push 这个** |

### 2.2 把铁三角讲给客户的 sample script

> "I want to share how we think about delivery, because it'll make our 3 options clearer.
>
> Every feature has **3 dimensions**: how much it does (**scope**), how well it works (**quality**), how fast we ship it (**time**). **In any project, you can prioritize 2 of these but not all 3**.
>
> **Today you're asking for**:
> - Full scope (6-week feature)
> - High quality (bug-free, no surprises in front of CFO)
> - Fast time (3 days)
>
> Honestly: I can't credibly commit all 3. **What I can do** is hold 2 of them rock-solid and let one flex:
>
> **(A) Hold scope + quality, flex time**: 6 weeks for the complete, polished dashboard. You'd miss Thursday.
>
> **(B) Hold scope + time, flex quality**: 3 days for the complete dashboard. **Risk: bugs, performance issues, hand-holding in front of CFO**. We'd spend 4 weeks post-launch fixing. CFO might see something weird on Thursday.
>
> **(C) Hold quality + time, flex scope**: 3 days for the **most critical 20%** that solves CFO's actual need. **Same Thursday delivery, same quality, less scope**.
>
> **I'd recommend (C)** because it gets CFO what she needs Thursday without risking embarrassment, and full dashboard ships in 3 weeks afterward.
>
> What's your reaction?"

→ 这段语言把客户从 "vendor 拒绝我" 转 "我自己在选 trade-off".

### 2.3 不同 stakeholder 对铁三角的偏好 (用来 tailor 提议)

| Stakeholder | 倾向 |
|---|---|
| **客户 业务方** | Time > Scope > Quality (要 ship 出去 demo) |
| **客户 工程方** | Quality > Scope > Time (后续他要 maintain) |
| **客户 CFO** | Quality > Time > Scope (怕 cost-overrun) |
| **客户 CEO** | Time > Quality > Scope (动作要快) |

→ 听 ask 时识别 who 在 push. **对业务方** push (C), **对工程方** push (A), **对 CFO** push (C with audit emphasis), **对 CEO** push (A with demo backup).

### 2.4 拒绝时不能说的话 vs 应该说的话

| 不该说 | 为什么 | 应该说 |
|---|---|---|
| "That's not realistic" | 否定客户判断, defensive | "Here are 3 options with explicit trade-offs..." |
| "We can't do that" | 关系 ender | "We can ship 3-day version with X scope; full scope takes Y" |
| "Your timeline is unreasonable" | 责备客户 | "Help me understand what's driving Thursday — that helps me propose the right shape" |
| "We'll try" | 模糊承诺 | "I'll commit to Tier 1 by Thursday EOD with written design doc" |
| "If we work weekends..." | Heroics, 不可持续 | "Within standard work hours, Tier 1 fits 3 days" |
| "Engineering needs to approve" | Middleman, slow | "Let me propose 3 options based on my engineering judgment" |
| "It's complicated" | Hand-wave | "Here are the 5 specific components in the 6-week scope..." |

### 2.5 显示 quality trade-off 的 concrete 数字

当客户 push Path B (full scope in 3 days), 给具体数字:

> "If we ship full scope in 3 days, based on my experience with similar 6-week features:
>
> - **Bug count**: typical 20-30 P1/P2 bugs in first 2 weeks (vs <5 on properly-scoped MVP)
> - **Performance**: page load 5-10s (vs <1s when properly engineered)
> - **Outage probability** during CFO demo: 15-20% (vs <1%)
> - **Hand-holding time** post-launch: 2 engineers full-time for 3-4 weeks (vs 0.5 engineer)
> - **Customer-facing apologies needed**: 2-5 in first month (vs 0)
>
> Translation: **you'd spend the next month explaining bugs to your team and to the CFO, rather than enjoying the new dashboard**. Path C avoids that."

→ **数字 + concrete 后果** 比 "low quality" 这种抽象词 punch 100x.

### 2.6 给客户主动权 (不替他决定)

最后一定要让客户 explicitly choose:

> "Three options on the table. Each is honest. **I have a recommendation but the choice is yours**:
>
> A: 6 weeks, full scope, high quality
> B: 3 days, full scope, **known risk in front of CFO**
> C: 3 days, **CFO-essential 20% only**, high quality, **full dashboard 3 weeks later**
>
> Which fits your priorities best? **I want this to be your call, not mine.**"

→ 把 decision 给客户. 你的 role 是 advisor, 不是 deny-er.

---

## ⚙️ Problem 3: MVP Carve-Out — What 20% Delivers 80%

**这是 negotiation 落地为工程的技能**.

### 3.1 80/20 法则在 feature 设计的应用

任何 feature 都可以拆成:

- **Core value (20% work, 80% value)** — 客户每天用
- **Polish (40% work, 15% value)** — 让产品 "感觉 done", 但客户不一定在意
- **Edge cases (40% work, 5% value)** — 1% 用户用, 但不做会被骂

**3 天版本**应该**只 ship core value**. 其余 defer.

### 3.2 Multi-tenant analytics dashboard 的 carve-out 示例

完整 6 周 scope:

```
1. 数据 schema 定义                       (1 week)
2. ETL pipeline (实时 + 离线)             (1 week)
3. 权限模型 (RBAC + tenant isolation)    (0.5 week)
4. Top-10 customers revenue chart        (0.5 week)  ← MVP
5. Drill-down by date/region/product     (1 week)
6. Custom date range picker              (0.5 week)
7. CSV / PDF export                       (0.5 week)
8. Scheduled email reports                (0.5 week)
9. Alert rules + notifications            (0.5 week)
10. Mobile responsive                     (0.5 week)
11. Multi-language                        (0.5 week)
```

**3 天 MVP** = #4 only:

```
- 复用 已存在的 CRM revenue API (跳过 schema + ETL)
- 单页面, 单 tenant view (跳过 RBAC, 用 admin token)
- 静态 chart, 90天数据, top-10 hardcode (跳过 customization)
- Login + chart + 1 number summary
- 不做: drill-down / export / schedule / alerts / mobile / i18n
- 不做: 任何会让 CFO 点击除了「open page」之外的事情
```

**输出**: 1 个 URL, CFO 打开看到 1 张图 + 1 段 commentary. **CFO 在 board 会议上不会点击, 不会 export, 不会 filter — 她只 share screen**.

→ 这是 MVP carve-out 的核心: **不只是「少做」, 是「精准识别 user 实际行为」**.

### 3.3 Carve-out 决策矩阵

| 维度 | Tier 1 (3 day) 包含 | Defer to Tier 2 (2 weeks) | Defer to Tier 3 (6 weeks) |
|---|---|---|---|
| **覆盖人群** | 1 user (CFO) | 5 users (CFO + analysts) | All (multi-tenant) |
| **数据范围** | 90 天, top 10 | 1 年, top 50 | 全量 + 历史 |
| **交互** | 静态 view | Drill-down + filter | Custom queries |
| **导出** | 截图 / PDF | CSV download | API access |
| **告警** | 无 | Email digest weekly | Real-time + Slack |
| **权限** | 单 admin token | Per-team RBAC | Full tenant isolation |
| **平台** | Desktop browser | + Mobile | + Native app |
| **语言** | 英语 | + 中文 | + 7 languages |

### 3.4 与客户对齐 carve-out 的沟通模板

> "Here's the **Tier 1 / 2 / 3 plan** I'd propose. Each tier is an actual product release, not a hack:
>
> **Tier 1 (3 days, Thursday 4pm)**:
> - 1 URL, login-gated
> - Static chart: top-10 customers by revenue, last 90 days
> - One-line summary commentary
> - Tested in production, no known bugs
> - **What it solves**: CFO has chart for board meeting
>
> **Tier 2 (Week 2-3)**:
> - + Drill-down by region / product
> - + CSV export
> - + Per-team access (basic RBAC)
> - **What it solves**: Sales analysts can self-serve
>
> **Tier 3 (Week 4-6)**:
> - + Full multi-tenant isolation
> - + Custom date ranges
> - + Scheduled reports + alerts
> - + Mobile responsive
> - **What it solves**: Becomes a real platform tool
>
> **All three tiers are committed**. I'll send written 1-pager today with dates locked. **Tier 1 is your 3-day deliverable. Tier 2/3 graduate automatically into your roadmap.**
>
> Does this shape work?"

### 3.5 1-Pager Design Doc 模板 (24h 内必须发给客户)

```
DESIGN DOC: Acme Multi-Tenant Analytics Dashboard
────────────────────────────────────────────────
Author: [you]
Date: 2026-05-21
Status: PROPOSAL (awaiting customer sign-off)

CONTEXT
────────
Acme requested multi-tenant analytics dashboard within 3 days for
CFO Q3 board review (Thursday 2026-05-23, 2pm AEST).

Full scope is a 6-week engineering effort. To meet the Thursday
deadline while maintaining quality, we propose a 3-tier delivery.

PROBLEM TO SOLVE THURSDAY
─────────────────────────
CFO needs to show top-10 customer revenue trend during board Q3
review. Specific question she'll answer: "Which customers are
growing / shrinking?"

She will share screen for ~5 minutes. She will NOT click, drill,
export, or filter during the meeting.

TIER 1 SCOPE (3 days, Thursday EOD)
────────────────────────────────────
Build:
  - URL: dashboard.acme.example.com/q3-cfo-view
  - Auth: SSO with Acme IDP, single 'admin' role
  - View: 1 chart (top-10 customers revenue, 90 days, line chart)
  - View: 1 number summary ('Q3 total revenue: $X.XM, +Y% YoY')
  - View: 1-line commentary auto-generated from data

Do NOT build:
  - Multi-tenant RBAC
  - Drill-down
  - Export / scheduled reports / alerts
  - Mobile responsive
  - Internationalization
  - Custom date range

Why this scope:
  - Solves CFO's exact Thursday need
  - 80% lower bug surface than full scope
  - Reusable in Tier 2 (we'll extend, not replace)

TIER 2 SCOPE (Weeks 2-3)
────────────────────────
Add: drill-down, CSV export, basic RBAC (3 roles).
Target: 2026-06-13

TIER 3 SCOPE (Weeks 4-6)
────────────────────────
Add: full multi-tenant, custom date range, scheduled reports,
alerts, mobile, i18n.
Target: 2026-07-04

DEPENDENCIES (FROM ACME)
────────────────────────
We need by EOD 2026-05-22 (Wednesday):
  1. Acme IDP integration credentials (SSO setup)
  2. Confirmed list of top-10 customers (any ranking criteria
     other than revenue?)
  3. CFO's preferred chart style (Acme branding / color palette)

If we don't receive these by Wed EOD, Thursday delivery shifts
to Friday.

DAILY CHECK-IN
──────────────
Tue 2026-05-21, 4pm: progress update + risks
Wed 2026-05-22, 4pm: pre-launch readiness review
Thu 2026-05-23, 9am: final smoke test, Acme team confirms

QUALITY GATES
─────────────
Tier 1 ships only if:
  - 3 internal dry-runs pass (page load < 2s, chart renders correctly)
  - Acme team reviews chart at Wed 4pm checkpoint
  - All 10 customer datapoints validated against source

If quality gate fails, we ship a recorded walk-through (CFO
demos with backup) AND ship live version Friday.

SIGN-OFF
────────
Acme: ________________ (Raj, VP Sales / business sponsor)
Acme: ________________ (Maria, Tech Lead / engineering sponsor)
Us:   ________________ (Gao Xin, FDE)
Date: 2026-05-21

NEXT STEPS
──────────
1. Review this doc with Acme stakeholders by 2026-05-21 5pm
2. Send Wed-pre-launch checklist by 2026-05-22 4pm
3. Ship Thursday EOD
4. Start Tier 2 design Mon 2026-05-27
```

→ 这份 doc 是**合同的微观版本**. 签字后 24h, 任何 goal-post shifting 都有 paper trail.

---

## ⚙️ Problem 4: Saying "No" Without Losing the Deal

**这是 negotiation 中最微妙的部分**.

### 4.1 不能说 "no" 的原因 (心理学层)

| 心理 | 影响 |
|---|---|
| **Loss aversion** | 客户听到 "no" → 感觉损失, 反弹 |
| **Status threat** | 客户觉得 "你在挑战我的判断" → 防御 |
| **Cognitive ease** | "yes" 是最简单回答; "no" 需要解释 → 客户觉得你麻烦 |

但**说 yes 又会害死你**. **Solution: 不说 no, 说 "what we can do is..."**

### 4.2 7 种「绕过 no」的语言模板

**模板 1: 替代而非拒绝**

```
❌ "We can't deliver in 3 days"
✅ "What we can deliver in 3 days is [X]. The full scope ships in
   [Y weeks] as Tier 2."
```

**模板 2: Tradeoff 而非 denial**

```
❌ "That timeline is too tight"
✅ "If we hold both scope and time, quality becomes the variable.
   Here's what 'low quality in 3 days' means concretely: [bugs / risk]"
```

**模板 3: Reframe 而非 push back**

```
❌ "You don't need all that"
✅ "Of the 9 components, which is the one your CFO actually opens?
   Let's solve that one first."
```

**模板 4: Commit to less, but commit hard**

```
❌ "Maybe by Friday?"
✅ "I commit to Tier 1 by Thursday EOD with written design doc.
   Tier 2 by [date]. Tier 3 by [date]. All in writing."
```

**模板 5: 共同 ownership**

```
❌ "We need your team to do X"
✅ "If your team can [provide data / make decision / do user testing],
   we can ship Tier 1 in 3 days. Otherwise it's 5 days. Want to split?"
```

**模板 6: 让数据说话**

```
❌ "It's risky"
✅ "Based on 10 similar engagements, shipping full scope in 3 days
   produces 20-30 P1/P2 bugs in first 2 weeks. Tier 1 produces <5.
   The math doesn't favor option B."
```

**模板 7: 邀请第三方角度**

```
❌ "Trust me, 3 days isn't enough"
✅ "I'd recommend talking to [reference customer]. They had the same
   timeline pressure 6 months ago, chose Tier 1, and the relationship
   with their CFO is now solid. Want me to set up a 15-min intro?"
```

### 4.3 客户「shopping around」威胁的应对

客户说: "Other vendor said they can do all of it in 3 days."

**不要的 response**:
- "That's not realistic, they're lying" (sounds defensive)
- "OK, fine, we can also do it" (放弃 craft)
- "I doubt that" (challenging customer 判断)

**推荐 response**:
> "Could be true. **Two questions to consider before deciding**:
>
> (1) **Demo ≠ ship**. Has the other vendor demoed in 3 days, or actually delivered to production? Big difference.
>
> (2) **What's their post-launch story**? Ask them: 'How many P1 bugs in the first 2 weeks of a 3-day delivery?' If they say 'zero', they're either uniquely magical or evasive. Industry average is 20-30.
>
> (3) **What's the actual SLA they'll commit to** for the 3-day version? If they ship buggy stuff in 3 days, your CFO sees bugs Thursday — that's the real cost.
>
> If they can answer these and still ship, **they should win the deal**. I'd encourage you to ask them — it's good due diligence either way.
>
> Meanwhile, my offer remains: Tier 1 in 3 days, full scope in 3 weeks, with **explicit written quality commitments**. **I prefer to be honest than to win on optimistic promises that hurt your business later.**"

→ 这个 reply 牛在: (a) 不否认 competitor, (b) 把 "compare on promises" 转 "compare on rigor", (c) reaffirm 自己的 honest 立场. 客户尊重这个.

### 4.4 当 sales 内部 pressure 你 over-commit

**Scene**: 你的 AE David 在会议中插话: "We can absolutely deliver full scope in 3 days, [your name] is just being conservative."

**当下的应对** (公开场合):

> "David and I will align on internal capacity offline. **What I can commit to in writing**: Tier 1 by Thursday EOD, with full scope in 3 weeks. Anything beyond that needs me to confirm with engineering — and I won't put something in writing today that I'd have to renegotiate Wednesday."

→ **关键**: 公开**不**反驳 David, 但**用 written commitment** 锁定. 客户看的是 written 不是 verbal.

**会议后的应对** (私下 with David):

> "David, I get the pressure to close. **3-day full-scope commitment is a deal-killer in 2 weeks, not a deal-saver today**. Let's align tonight on what I can responsibly commit. **If we lose this deal because we don't over-promise, I'd rather that than win + lose the customer in 2 months for shipping broken stuff.**"

如果 David 继续 push:

- 内部 escalate: 跟你的 EM + AE 的 manager 同时谈
- 要求 written record: "If we commit to X, I want a written internal agreement on what 'X' means specifically"
- 极端情况: refuse to put your name on a commitment you can't deliver

### 4.5 "No" 的 escalation ladder

| Severity | 你的 action |
|---|---|
| 客户 ask 不合理但有 alternative | Reframe + offer 3 options |
| 客户 push back, 接受不下来 alternative | Insist + show trade-off math + recommend 选项 |
| 客户 threatens 切走 vendor | 「让数据说话 + 邀请 reference 客户」 |
| Sales 内部 pressure over-commit | Public 不反驳 + written commit 锁定 + 私下 align |
| Sales 继续 push | Escalate 到 EM + AE manager 联合 |
| 极端 | Refuse to sign / put name on it |

---

## ⚙️ Problem 5: When to Bring in Account Exec / Leadership

**这是 know-your-role 题**.

### 5.1 Escalation 的 3 个层次

| 层次 | 谁 | 何时 | 怎么 |
|---|---|---|---|
| **L1 客户内 escalation** | 你 + 客户 business sponsor 私下沟通 | 客户内部有 disagreement (业务方 vs 工程方) | 私下问 sponsor, 不公开 |
| **L2 内部 escalation** | 你 + AE + EM 三方对齐 | 你判断 Tier 1 可行, 但需要内部资源 commit | Slack / 1-on-1, 不在 customer 面前 |
| **L3 cross-leadership escalation** | 你 + AE + EM + AE manager + 你的 director, 可能 CRO | 这单的 commitment 超出 FDE 决策权 (e.g., service credit, special terms) | Formal call, structured proposal |

### 5.2 何时 escalate L1 (客户内部)

**Trigger**:
- 客户业务方 push 速度, 客户工程方 push 质量, 双方在你面前 disagree
- 客户 sponsor 内部受压, 跟你 align 但跟 boss disagree
- 客户 procurement / legal 在 contract 上加压

**Action**:
- 单独 30-min 1:1 with sponsor: "What's the internal politics? What do you need from me to push back internally?"
- 提供 sponsor 武器: design doc / quality math / reference customer

**Example dialog with sponsor (Maria)**:

> "Maria, between us — I want to understand the internal dynamics here. Your CTO seems to be pushing back on the 3-week Tier 2 timeline. **What's behind that?**
>
> *[Maria: 'CTO wants to look like he's tough on vendors']*
>
> OK that's helpful context. **What if I give you a written timeline with specific quality gates and Acme veto authority at each tier?** That gives your CTO control without him having to push us. Would that defuse the situation?"

### 5.3 何时 escalate L2 (内部)

**Trigger**:
- Tier 1 scope 需要工程团队额外 resource
- Tier 1 timeline 跟其他客户 deliverable 冲突
- AE 想 over-commit, 你想 push back

**Action**:
- 30-min 三方同步: 你 + AE + EM
- 提议: "Here's my proposal to customer. Confirm engineering can hit Tier 1 in 3 days?"
- 如果有 conflict (e.g., EM 说 4 days), 立即 transparency: "我必须告诉客户 4 days 不是 3 days"

**绝不**:
- 你内部承诺 "3 days", EM 不知道, 然后 EM 反对
- 跟 AE 单独 commit, 不 loop EM

### 5.4 何时 escalate L3 (cross-leadership)

**Trigger**:
- 客户 demand 超出标准合同 (e.g., 要 90% uptime SLA, 要 source code escrow, 要 unlimited liability cap)
- Service credit / pricing concession 超出你权限
- 客户 threatens churn, 需要 leadership 介入 retention

**Action**:
- 给你 director / VP 一个 1-pager: 客户状况 / 提议 / 风险 / 建议
- 调度 leadership call: 不到 24h, 不超 48h
- 你**预备话术**, 让 leadership 用一致语言

**Sample brief to your director**:

```
TO: Director of FDE
FROM: Gao Xin
RE: Acme Bank — escalation request

SITUATION
─────────
Acme demanded multi-tenant dashboard in 3 days (vs 6 weeks
estimated). I've proposed Tier 1/2/3 plan with written commitments.

DECISION NEEDED FROM YOU
────────────────────────
Acme also demands:
- 99.5% uptime SLA on Tier 1 (vs our standard 95%)
- 30-day full refund clause if Tier 1 fails CFO review
- Source code escrow

These are above my pay grade.

WHAT I RECOMMEND
────────────────
- 99.5% SLA: ACCEPT (Tier 1 is single chart, low blast radius)
- 30-day refund: COUNTER with "no-charge re-engagement instead"
- Source code escrow: DEFER to Tier 3 launch (Q3 2026)

NEXT STEP
─────────
30-min call with Acme CFO (Thursday 11am AEST). Want you on
the call to commit on SLA + refund clause if Acme insists.
```

### 5.5 谁 own customer 关系 — 永远是你

即便 escalate, **customer-facing primary 仍然是你**, 不是 leadership. Leadership 进来是 reinforcement, 不是 takeover.

| 场景 | 谁 own customer 沟通 |
|---|---|
| L1 客户内部 | 你 |
| L2 内部 resource | 你 (AE / EM 不直接跟客户讲) |
| L3 cross-leadership | 你 + 你的 director 一起, 但你主讲 |

→ 客户感受的连续性: 永远是你这张脸. 否则**关系反复 reset**.

### 5.6 Escalation 之后必做的事

每次 escalation, **写下**:

```
ESCALATION LOG
──────────────
Date: 2026-05-21
Level: L3
Customer: Acme Bank
Trigger: Customer demanded non-standard SLA + refund clause
Stakeholders involved:
  - Acme: CFO Linda, CTO Raj
  - Us: Gao Xin (FDE), David (AE), Linda (EM), Yang (Director)
Outcome:
  - 99.5% SLA: accepted with quarterly review clause
  - Refund: countered with "free Tier 2 if Tier 1 fails CFO review"
  - Escrow: deferred to Tier 3
Lessons:
  - Need pre-approved authority levels for FDE on SLA / refund
  - Need standard customer demand response template
```

→ Escalation log 是 organizational learning. **没 log 的 escalation 等于没发生**.

---

# Part 3 · 把 5 个问题串起来看

这 5 个问题其实是**同一个 negotiation 的不同阶段**:

1. **Diagnose 真实需求** (Problem 1) — 让 ask 缩水 80%
2. **铁三角 framework** (Problem 2) — 让客户自己看到 trade-off
3. **MVP carve-out** (Problem 3) — 把 negotiation 落地为工程
4. **绕过 "no"** (Problem 4) — 不说 deny, 说 alternative
5. **Escalation hierarchy** (Problem 5) — know your role + your power

每一层做对, **客户感觉的是「这个 FDE 在帮我」** 而不是 「FDE 在拒绝我」. 这就是为什么有的 FDE 拒绝 90% 的不合理 ask 仍然 customer-loved, 有的 FDE 接 100% 但 6 个月后客户 churn.

---

## 必问 clarifying questions

**1. 听完题目先问 setup**

> "Who's demanding it — business buyer, technical buyer, or executive? Each has different trade-off appetite."

**2. Driver**

> "What's driving the 3-day deadline? Board meeting? Regulatory? Competitive demo? Customer self-imposed?"

**3. Customer maturity**

> "Is this an existing customer or new? Past delivery history? Have they accepted MVP-style delivery before?"

**4. Internal resources**

> "Do I have authority to commit Tier 1 immediately, or do I need engineering sign-off first?"

**5. Stakes**

> "What's the deal size? Existing relationship value? Implications of losing this customer?"

---

## 5 步框架 (45-min answer 节奏)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify driver + stakeholders + stakes |
| 5-15 min | Diagnose real need (Problem 1) — 真实需求挖掘 |
| 15-25 min | Iron triangle framing + 3-option present (Problem 2) |
| 25-35 min | MVP carve-out spec + design doc structure (Problem 3) |
| 35-45 min | Saying no playbook + escalation thresholds (Problem 4-5) |

---

## 简历专属 reframe

| 题 | Gao Xin 的经验 |
|---|---|
| Customer demands too much | **Indonesia refund tier scoping** — 直接套, 完美 match |
| Decompose into tiers | Tier 1 (info lookup) / Tier 2 (structured task) / Tier 3 (refund decision) |
| MVP carve-out | Voice agent 7 markets 你**只先上越南**, 其他后续 |
| Iron triangle education | BNPL chatbot for OJK — 教 OJK 什么叫 production-ready vs demo |
| Saying no with alternative | ConvFinQA — 你向研究 lead push back negative results 而不是 hide |
| Escalation to leadership | TikTok PayLater fraud + compliance 跨部门 escalation 你做过 |

**主动 quote**:

> "This is **exactly** the move I made with Indonesia ops 6 months ago. They wanted **full autonomous refund decisions on day 1** — like the AI agent reading the case file and approving / denying refund money on its own. 6-week to ship full version. They wanted 2 weeks.
>
> I decomposed into 3 tiers:
> - **Tier 1**: AI agent extracts case info from images / chats, **human ops make decision**, AI auto-fills form. Ships in 2 weeks.
> - **Tier 2**: AI agent **recommends** refund decision with confidence score, human approves/overrides.
> - **Tier 3**: AI agent **autonomous decision** for high-confidence cases, human review for low-confidence.
>
> We shipped Tier 1 in 2 weeks. Ran 2 weeks of data to validate. **Tier 2 graduated naturally after Tier 1 stability proven**. **70% of value delivered in 4 weeks at 0% wrong-call rate**, vs alternative of 8% wrong-call rate if we'd shipped Tier 3 on day 1.
>
> The lesson that applies here: **what customer asks for is rarely what they need**. The honest question is **'what's the smallest thing that solves your actual day-3 problem'**, then build that with a written roadmap to bigger.
>
> The trickiest part wasn't the tiering — it was getting **business sponsor (Maria, Ops Director) to defend tiering to her CFO**. I gave her a 1-pager with the math: 'Tier 3 day-1 = 8% bad decisions on customer money. Tier 1 + graduate = 0% bad. Same end state, 4 weeks later.' She used that in her CFO meeting. **The CFO chose Tier 1**.
>
> That's the FDE skill: **give your champion ammunition to defend the right scope internally**."

---

## 5 follow-ups

**Q1**: "Client refuses tiering — wants everything Thursday."

**A**: Escalate transparency:
- "I want to be honest with you. We **can** ship 'a version' in 3 days, but it will have known bugs, and we'll spend the next 4 weeks fixing them. **Total time to stable** is **longer** than tiering. The CFO meeting is **the wrong use case to risk a bad demo on**."
- Bring in your EM + their tech lead for peer-level conversation
- Ultimate fallback: "If you insist, I'll need written acknowledgment that Tier-1-quality is acceptable for Thursday — basically a CYA. Want me to draft that?"

**Q2**: "Client agrees Tier 1, but Thursday demands Tier 3 'soon'."

**A**: This is **goal-post shifting**, classic pattern:
- "Glad Tier 1 works. Tier 2 is committed for [date], Tier 3 for [date]. **I'll send weekly progress updates** so you have visibility."
- **Written date + weekly progress** > vague urgency. Goal-post shifting needs paper trail to counter.

**Q3**: "Engineering says even Tier 1 in 3 days is impossible."

**A**: Don't unilaterally commit to customer:
- "If Tier 1 can't be done in 3 days, what **can** be done? Maybe a hardcoded mockup, manual data pull, single-view PDF?"
- Find **smallest possible 3-day deliverable** even smaller than original Tier 1
- Re-propose to customer: "Tier 0 = static PDF, Tier 1 = interactive (5 days), Tier 2 onwards original timeline"

**Q4**: "Customer says other vendor promised 6w-in-3d."

**A**: Don't take bait:
- "If they can really do that with quality, they should win. Honestly — I'd rather lose this deal than ship something that hurts both our reputations. **But in my experience**, promises like that mean the work continues for weeks past the demo. I'd ask them: what happens day 4-30?"
- Converts conversation to **due diligence**. If you're confident in your craft, exposing competitor's optimism as bug is good for you.

**Q5**: "Sales manager pressures you to commit 6w-in-3d to close."

**A**: Hardest. Internal alignment first:
- "If we commit, here are 3 ways this fails: buggy demo + 4-week recovery / can't actually demo + lost trust / team burnout + attrition."
- Offer: "I can commit Tier 1 in 3 days, full scope by week 10. If sales needs 6w-in-3d, **that's a different deal** — let's get legal to write 'demo-readiness' rather than 'production-ready'."
- Worst case: **document your concerns in writing** before agreeing. CYA.
- Extreme: refuse to put your name on a commitment you can't deliver. **Your reputation > one deal**.

---

## ❌ 易错点 (top 10)

1. **直接 no** — kills relationship instantly
2. **直接 yes** — kills team, leads to churn 2 months later
3. **"Let me check with engineering"** — middleman + slow
4. **"We'll try our best"** — ambiguity = setup for blame
5. **没问 "what's driving timeline"** — miss 80% scope reduction opportunity
6. **没 internal alignment** before committing to customer
7. **Verbal-only commitment** — drifts in 24h
8. **Heroics promise** ("we'll work weekends") — unsustainable + sets precedent
9. **Ship Tier 1 then ghost on Tier 2/3** — destroys trust
10. **没 written design doc with quality gates** — goal-post shifting opportunity

---

## ✅ 加分项 (top 10)

1. **D·D·O·C framework** explicit (Deeper why / Decompose / Offer / Commit)
2. **"What happens on day 4"** discovery move
3. **Iron triangle education** with concrete numbers
4. **3-option presentation** with explicit trade-offs, customer chooses
5. **MVP carve-out** based on actual user behavior (CFO won't click)
6. **24h written design doc** with quality gates + dependencies
7. **Joint ownership** — ask customer team to contribute (data / decision)
8. **Reference customer story** for credibility
9. **Quote Indonesia refund tier scoping** (real Gao Xin work)
10. **Tier 1/2/3 roadmap** committed in writing, not just Tier 1

---

## 一句话总结

> **「6 周变 3 天」的真正问题不是「时间太短」, 是「客户没想清楚自己要啥」**.
>
> 你的 job 不是挤压 timeline, 是**通过结构化提问把 monolithic ask 拆解, 找到 must-have, ship 它, 把剩余 90% 放进 official roadmap**.
>
> 60% 的 "6 周变 3 天" 在你拆完 scope 后自动变成 "3 天足够". 剩下 40% 是真有需求, 那时 tier-1 + roadmap 是唯一可持续答案.

---

## Cheat Sheet (印 1 页)

```
D·D·O·C framework:
  Deeper why — "What happens on day 4 if not ready?"
  Decompose — break 6-week ask into 9 components, find P0
  Offer phased — 3 options, all honest, all written
  Commit specifically — date + deliverable + 24h design doc

Iron triangle:
       Scope
      /     \
     /  PICK \
    /    2    \
  Quality — Time

  Push (C) = quality + time, flex scope = ⭐ recommended
  Resist (B) = scope + time, flex quality = bug bomb

3-option standard format:
  A: 6 weeks, full scope, high quality (baseline)
  B: 3 days, full scope, KNOWN bugs (risk + math)
  C: 3 days, 20% scope, high quality + roadmap to full ⭐

MVP carve-out questions:
  - Which 1 component does CFO actually open?
  - What question does she answer first?
  - Does she click / drill / export / share?
  - What user behavior is the deliverable for?

Carve-out output (Tier 1):
  - 1 URL
  - 1 view (no interaction)
  - 1 metric / chart
  - 1 user (not multi-tenant yet)
  - 90 days data (not full history)
  - English (not i18n)
  - Desktop browser (not mobile)

Carve-out output (Tier 2/3):
  Tier 2 = + drill-down + export + basic RBAC
  Tier 3 = + multi-tenant + scheduled + alerts + mobile + i18n

24h design doc must contain:
  Context
  Problem to solve (specific user behavior)
  Tier 1 scope (build / NOT build)
  Tier 2 + 3 scope + dates
  Dependencies from customer
  Daily check-in schedule
  Quality gates (ship criteria)
  Sign-off signature lines

Saying "no" replacements:
  ❌ "Not realistic" → ✅ "Here are 3 honest options"
  ❌ "We can't" → ✅ "What we can deliver is..."
  ❌ "Timeline is unreasonable" → ✅ "Help me understand driver"
  ❌ "Let me check" → ✅ "Let me propose 30 sec sync"
  ❌ "We'll try" → ✅ "I commit Tier 1 by [date]"
  ❌ "If we work weekends" → ✅ "Within work hours, Tier 1 fits"

Customer wants ALL:
  Math response: "Tier 1 = stable in 3 weeks. Full scope rushed
  = 5 weeks to stable. Tier 1 actually faster."

Competitor promise:
  "Demo ≠ ship. Ask their post-launch SLA. 3-day full scope
  yields 20-30 P1 bugs. If they say zero, they're evasive."

Sales pressure to over-commit:
  Public: don't contradict, use written commit to anchor
  Private: align on math, refuse if needed, escalate if needed

Escalation hierarchy:
  L1: Customer internal (1:1 with sponsor)
  L2: Internal resource (you + AE + EM)
  L3: Cross-leadership (your director / VP / CRO)
  Customer-facing primary = always you

红线:
  - Yes without alignment
  - Verbal-only commitments
  - Heroics culture promise
  - No written design doc
  - Ghost on Tier 2/3
  - Put your name on impossible commitment
```
