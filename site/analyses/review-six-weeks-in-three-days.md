## Client Sim #2 · 6-Week Feature in 3 Days — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](six-weeks-in-three-days.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`six-weeks-in-three-days.html`](six-weeks-in-three-days.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"Customer wants a 6-week feature delivered in 3 days. What do you say?"**, 我按这 7 层回答, 不跳序. 这题考的不是 "你能不能加班", 是 **structured scope decomposition + Tier-1 ship strategy**.

### 📐 6-Week Feature in 3 Days — 7 层结构

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 (literal) |
|---|---|---|---|---|
| 1 | "What's driving the timeline?" — first question | 1 min | **不立刻 push back, 不立刻 yes**. 先问 verbatim: > *"Before I say yes or no, help me understand — what's driving the 3-day deadline? Is it a board meeting, a regulatory date, a competitor move, or a customer commitment?"* 80% case timeline 是 self-imposed | "First sentence out of my mouth: 'what's driving the 3-day deadline?'..." |
| 2 | Decompose monolithic ask | 3 min | "6-week feature" 是 monolithic. 拆成 **3-tier**: > **Tier 1 (must-have for 3-day reason, 20% of scope, 3 days)** > **Tier 2 (nice-to-have, 2-3 weeks)** > **Tier 3 (full feature, 6 weeks)**. 然后讲 verbatim: > *"If we deliver Tier 1 by Friday, does that solve the [board meeting / regulatory / competitor] problem?"* | "I'd structurally decompose the ask. Three tiers, three timelines. Then ask which tier solves their actual problem..." |
| 3 | 5 hidden need types | 3 min | 真实 need 通常是 5 种之一: **(a) board demo (need screenshot, not feature)**, **(b) regulatory deadline (need partial coverage, not full)**, **(c) competitor parity (need press release, not feature)**, **(d) customer escalation (need acknowledgment + plan)**, **(e) self-imposed (need pushback)**. 每种不同 response | "Five archetypes of 'urgent feature'. Each has a different real answer. Most aren't 'build the feature'..." |
| 4 | Stakeholder dialog scripts (verbatim) | 4 min | **To customer sponsor**: > *"Let me make sure I understand the real outcome. If we ship X by Friday and deliver full Y in 4 weeks, does that work?"* **To internal eng lead**: > *"I'm not committing 3 days. I'm scoping the slice that's actually 3 days. Can you size Tier 1?"* **To customer if they push back**: > *"I'd rather under-promise and over-deliver than commit a 3-day full feature and ship a 3-day broken feature."* | "Three dialog scripts, verbatim. Customer sponsor, eng lead, and customer-when-pushing-back..." |
| 5 | Ship Tier 1 + roadmap commit | 2 min | 3 天 ship Tier 1 (minimum viable, prod-quality), 24h 内 deliver **written roadmap** Tier 2 + Tier 3 with dates + owners. **Roadmap 是 trust artifact** — customer 看到你不是说 "no", 是说 "yes for what matters, plan for the rest". Update roadmap weekly | "Tier 1 ships Friday. Tier 2 and 3 land on roadmap with owners and dates. That roadmap is the trust artifact..." |
| 6 | Anti-pattern: heroics | 1 min | **绝对避免**: (a) commit 3 天全 scope + 加班通宵 → 通常 ship broken thing, customer trust 反而损坏, (b) flat "no" 不给替代方案 → customer 觉得你不 partner, (c) silent extension to 5 days → 比 honest "Tier 1 first" 更损 trust | "Heroics are the worst answer. Three anti-patterns I'd refuse..." |
| 7 | Resume reframe — Indonesia ops | 1 min | "我在 TikTok PayLater Indonesia, ops team 要 '完整 refund 自动化 3 天上线'. 我问 driver, 真实 driver 是 **regulator quarterly review 周五**. 拆: Tier 1 (auto-refund 5 categories, 80% volume) ship Friday → Tier 2 (其余 categories, 2 weeks) → Tier 3 (full workflow, 6 weeks). Regulator 满意, 没加班通宵, ops 后来 graduate 全功能" | "I lived this — Indonesia ops, full refund automation in 3 days. Real driver was a regulator review. Tier 1 shipped Friday..." |

### 🎯 为啥按这个序

**先 driver, 再 decompose, 再 dialog, 再 roadmap** — 因为 90% candidates 立刻讨论 "我能不能 ship", 不问 "真正要解决什么". **80% case real driver 不是 timeline, 是 audience/event**. 拆完 monolithic ask 后, 20% 是 must-have.

Tier 1 + roadmap (Layer 5) 是这题的 **Client Sim 区分项** — 一般 candidate 给 yes/no, FDE 给 yes-for-X + roadmap-for-Y.

### 🔥 哪一层最容易被追问 deeper

- **Layer 1 (driver)**: 面试官扮 customer 说 "I just need it, don't ask me why" → 答: > *"Completely fair — and I'll figure out a path. But the more I understand the outcome, the more likely I ship something useful. If I had to guess: is this for [board / regulator / competitor]?"* — 永远 follow up, 不接受 stonewalling
- **Layer 4 (eng lead pushback)**: 面试官扮 eng lead 说 "3 天什么都做不出来" → 答: > *"I'm not asking for everything. I'm asking you to size the Tier 1 slice — what's the smallest thing that solves problem X. If even Tier 1 is impossible, we have a different conversation with customer."*

### ⏱ 时间压缩版 (30 min round)

- 3 min: driver question + decompose (Layer 1-2)
- 5 min: hidden need types (Layer 3)
- 10 min: dialog scripts verbatim (Layer 4, 重点)
- 5 min: ship Tier 1 + roadmap (Layer 5)
- 2 min: anti-pattern + resume hook (Layer 6-7)

### 🆘 卡壳兜底 (针对这题)

- 卡 dialog → fall back to **"what's driving the deadline?"** 永远是第一句
- 卡 decomposition → use **TikTok Indonesia refund automation Tier 1 = 5 categories** 故事
- 卡 push-back → use **"Tier 1 first" framing**, 不是 "no"

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

> **"6 weeks → 3 days" 真问题不是「时间太短」, 是「客户没想清楚自己要啥」**. 80% case 在你深挖 scope 后真实需求只占 20%, 剩下 40% 真有需求时 tier-1 ship + roadmap 是唯一答案. 你的 craft 不是挤压 timeline, 而是结构化提问拆 monolithic ask 找 must-have, ship 它 + 把 90% 放进 official roadmap.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Iron Triangle | Scope × Quality × Time, 只能选 2 | 客户教育核心语言 |
| MVP carve-out | 最小但仍 viable, 解决核心不解全部 | 80/20 application |
| D·D·O·C | Deeper why / Decompose / Offer phased / Commit specifically | 现场 4 步 framework |
| Goal-post shifting | Tier 1 ship 后客户 ASAP Tier 2 | 用 written 文档预防 |
| Real driver | board / 监管 / 竞品 / 合同 / PM 焦虑 / 不知道 | 6 archetype |
| Tier 1/2/3 | P0 must / P1 nice / P2 future | scope 拆解输出 |
| Hero culture | 周末加班 ship | 红线, 不可持续 |
| Bug bomb | 3 天 full scope = 20-30 P1 bugs | Path B 灾难 |
| Design doc | 24h written contract | 客户签字防 ghost |
| Joint ownership | 客户也 own 数据/试点 | reciprocal commitment |
| SMART deliverable | Specific / Measurable / ... | reframe 工具 |
| Path A/B/C | full / rush / scoped | 3-option standard 模式 |
| Sponsor ammunition | 数据 + roadmap | 给客户内部 champion |
| Escalation L1-L3 | 客户内部 / 你+AE+EM / leadership | 何时升级 |
| Math response | "Tier 1 3w stable vs Rush 5w stable" | 客户坚持 ALL 时用 |
| Competitor counter | "Demo ≠ ship. Ask SLA" | 客户提竞品时 |

### 🎯 5 个核心 framework

**Framework 1**: D·D·O·C 现场 4 步
- When: 客户 demand "6 周 3 天"
- Algorithm: 1. Deeper why ("What happens day 4 if not ready?") 2. Decompose 9 component (schema/ETL/RBAC/chart/drill/date/export/email/alert/mobile/i18n) 3. Offer 3 phased option (A 6w full / B 3d full bug bomb / C 3d 20% scoped ⭐) 4. Commit specific date + 24h design doc
- Trade-off: 慢但稳, 急功 yes/no 都死
- Tools: 30-sec internal Slack check (not 30-min)

**Framework 2**: Iron Triangle 教育 (Scope × Quality × Time)
- When: 客户坚持 full scope rush time high quality
- Algorithm: 教法则 "只能选 2" → 给 3 option (A scope+quality flex time / B scope+time flex quality / C quality+time flex scope) → recommend C → 让客户 explicitly choose
- Trade-off: 客户教育需要时间但建立长期信任
- Tools: triangle 画图, 数字 (20-30 P1 bugs, 15-20% outage 概率 demo 时, 2 engineers 4 weeks fix)

**Framework 3**: MVP Carve-Out 80/20
- When: tier 1 拆解时
- Algorithm:
  - Core (20% work, 80% value): 客户每天用
  - Polish (40% work, 15% value): 感觉 done 但不在意
  - Edge (40% work, 5% value): 1% user 用, 不做会骂
  - Output: 1 URL + 1 view (no interaction) + 1 metric + 1 user (no multi-tenant) + 90 days (no full history) + English (no i18n) + Desktop (no mobile)
- Trade-off: 精准识别 user 实际行为 (CFO board demo 不点 不 export 不 filter, 只 share screen)
- Tools: 5 MVP 问题清单 ("which 1 component CFO opens?")

**Framework 4**: 6 Driver Archetype 真实需求挖掘
- When: 客户说 "需要 6 周功能"
- Algorithm:
  - A. Board/CEO 承诺 → 真需 1 chart
  - B. 监管 deadline → MVP audit panel, defer advanced
  - C. 竞品 demo → demo-only prototype 标 "preview"
  - D. 合同 deliverable → 法务 amend
  - E. PM 焦虑 → visibility (weekly demo), not feature ship
  - F. 客户也不知道 → 引导 prioritize 帮想
- Trade-off: 直接 push back 失关系, 引导 prioritize 帮客户想清楚
- Tools: 5 question 清单 ("CFO opens what component?" "asks what question first?" "previous report extend?" "who else needs?")

**Framework 5**: Saying No Without Losing Deal
- When: 必须 push back 但不毁关系
- Algorithm:
  - Replace ❌ "Not realistic" / "We can't" / "Try our best" / "Let me check"
  - With ✅ "Here are 3 honest options" / "What we can deliver is..." / "I commit Tier 1 by [date]" / "Let me propose 30 sec sync"
  - Math response: "Tier 1 stable 3w. Full rush stable 5w. Tier 1 faster"
  - Competitor counter: "Demo ≠ ship. Ask their post-launch SLA"
  - Sales pressure: 公开不反驳, 用 written commit anchor, 私下 align, 必要 escalate
- Trade-off: 拒绝艺术, AE 在场尤其难
- Tools: 1-pager design doc, customer sign-off, daily 15-min sync visibility

### 🌳 关键决策树

```
客户说 "6 weeks in 3 days"
├── 第一句永远: "What's driving the 3-day window?"
│   ├── Board/CEO commit? → 真需 1 chart (Driver A)
│   ├── 监管? → MVP audit panel (Driver B)
│   ├── 竞品 demo? → demo-only prototype (Driver C)
│   ├── 合同? → 法务 amend (Driver D)
│   ├── PM 焦虑? → weekly visibility (Driver E)
│   └── 不知道? → 引导 prioritize (Driver F)
├── Decompose 9 component
├── Offer 3 option (A 6w / B 3d full bug bomb / C 3d 20% ⭐)
└── 客户选 explicit
   ├── 选 C → 24h design doc → daily sync → Tier 1 ship
   ├── 选 B → math response (5w stable not 3d) → 仍选 → escalate
   └── 选 A → Tier 1 ship 后 Tier 2 graduate

Sales 在场, AE over-promise "24h fix guarantee"
├── 公开: 不当面反驳
├── 私下立刻: "If miss, lose them permanently"
├── Written follow-up: 用更精确语言 anchor
└── AE 坚持? → escalate manager. Reputation > 这一单
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: Diagnose Real Need (80% 真实只占 20%)**
- 核心解法:
  > "Before I respond on scope, help me understand what's driving the timeline. Is there a specific meeting, deadline, customer commitment, or board ask that anchors the 3-day window?"
  > Reframe: "OK by Thursday, the artifact that matters is a chart showing top-10 customer revenue. Not the full dashboard, just that one chart. Match?"
- Top 3 gotchas: 急着回答 yes/no / 不问 driver 错过 80% reduce / 客户 reject scope 缩减时不会 math response
- Tools/tactics: 5 question 清单, SMART reframe template, 30-sec Slack internal check

**Problem 2: Iron Triangle Negotiation**
- 核心解法:
  > "Every feature has 3 dimensions: scope / quality / time. In any project, you can prioritize 2 of these but not all 3.
  > (A) Hold scope + quality, flex time: 6 weeks
  > (B) Hold scope + time, flex quality: 3 days with 20-30 P1 bugs
  > (C) Hold quality + time, flex scope: 3 days for 20% that solves CFO's need ⭐
  > Which fits your priorities? I want this to be your call, not mine"
- Top 3 gotchas: "Not realistic" / "We can't" / "Try our best" (3 红线短语)
- Tools/tactics: 数字 (20-30 P1 bugs / 15-20% outage 概率 demo 时 / 4 weeks 2 engineers fix)

**Problem 3: MVP Carve-Out (80/20)**
- 核心解法:
  ```
  Full 6w: 11 components
  3d MVP = #4 chart only:
    - 复用 existing CRM API (skip schema + ETL)
    - 单页 admin token (skip RBAC)
    - 静态 chart 90d hardcode top-10
    - 不做: drill / export / schedule / alert / mobile / i18n
    - 不做: 任何 CFO 会点击的东西
  Output: 1 URL, CFO open → see chart → share screen
  ```
- Top 3 gotchas: 全做 polish (40% work 15% value) / 加 edge case (40% work 5% value) / 没识别 CFO 实际行为
- Tools/tactics: 5 MVP 问题 ("which 1 component CFO opens?")

**Problem 4: Saying No Without Losing the Deal**
- 核心解法:
  ```
  Replace 7 banned phrases:
    ❌ "Not realistic" → ✅ "3 honest options"
    ❌ "We can't" → ✅ "What we can deliver is..."
    ❌ "Timeline unreasonable" → ✅ "Help me understand driver"
    ❌ "Let me check" → ✅ "Let me propose 30 sec sync"
    ❌ "We'll try" → ✅ "I commit Tier 1 by [date]"
    ❌ "If we work weekends" → ✅ "Within work hours, Tier 1 fits"
    ❌ "Engineering needs approve" → ✅ "Let me propose based on judgment"
  Customer wants ALL math: "Tier 1 = stable 3w. Rush = stable 5w. Tier 1 faster"
  Competitor: "Demo ≠ ship. Ask their SLA"
  ```
- Top 3 gotchas: 直接 no (关系 ender) / 直接 yes (团队 ender) / verbal-only commit (24h 漂移)
- Tools/tactics: written 24h design doc, customer sign-off, daily 15-min sync

**Problem 5: When to Escalate (AE / Leadership)**
- 核心解法:
  ```
  L1 (你处理): 客户内部 1:1 with sponsor, 政治 spin
  L2 (你 + AE + EM): 内部资源 align, 工程承诺确认
  L3 (你的 director / VP / CRO + 客户 leadership): 战略层 deal at risk
  AE over-promise 公开不反驳, 私下立刻校准
  Sponsor 私下 brief, 给 ammunition (postmortem, data, roadmap)
  Engineering Manager pushback? → 把 demand 转 official scope doc, escalate 不 absorb
  Customer-facing primary 永远是你, internal cross-leadership 不要 cut you out
  ```
- Top 3 gotchas: AE 当面反驳 (公司面子) / 没 brief sponsor (失内 champion) / EM 当场否决 (没 internal alignment 就承诺)
- Tools/tactics: 30-sec internal Slack, escalation template, sponsor ammunition pack

### 🔥 Production gotchas (top 15)

1. 直接 no → 关系 ender
2. 直接 yes → 团队 ender
3. "Let me check with engineering" → weak middleman
4. "We'll try our best" → ambiguity 后续 blame game
5. 不问 driver → 错过 80% 减 scope 机会
6. Hero culture promise → 后续每次预期 heroics, burnout, attrition
7. Verbal commitment only → 24h 后客户记成 "你说 ship 全部"
8. 没 internal alignment 就承诺 → EM 当场否决
9. Tier 1 ship 后 ghost → 客户感觉 abandoned
10. Tier 1 ship 完美就停 → 客户 goal-post shift Tier 3 更快 = 灾难
11. 3 day full scope ship → 20-30 P1 bugs + 4w fix = 总 5w
12. 替客户决定 → "我推荐 C" 不让客户 explicitly choose
13. AE 公开反驳 → 公司面子 -100
14. 没 daily 15-min sync → 客户每天焦虑无 visibility
15. CFO 用 polish (export/drill/mobile/i18n) → 她在 board 不点击

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Tier 1/2/3 scope | Indonesia refund tier | 真实做过的同款 framework |
| Driver 挖真需 | Voice agent 7 markets 30天 | 越南 priority, 其他 6 分阶段 |
| Math response | Multi-market rollout | 5w stable rush vs 3w Tier 1 stable |
| Iron Triangle | BNPL chatbot | scope flex 客户教育 |
| MVP carve-out | Internal Agent Platform | 30 行复用 |
| 24h design doc | ConvFinQA reference impl | written ahead-of-time |
| Daily sync visibility | Voice agent rollout | weekly cross-region |
| Hero culture refuse | EM pushback | 内部 boundary |
| Sponsor ammunition | Maria refund champion | postmortem + data |

### 🎤 面试现场 quotables (top 8)

1. "Before I respond on scope, help me understand what's driving the 3-day window"
2. "Of the full feature, what's the must-have-on-day-3 vs nice-to-have?"
3. "I want this to be your call, not mine — here are 3 honest options"
4. "Path 1 gets you to stable full dashboard faster than Path 2. The math is 3 weeks vs 5 weeks"
5. "Demo ≠ ship. Ask your competitor what's their post-launch SLA on this"
6. "Within standard work hours, Tier 1 fits 3 days. I won't put my team on weekends because that's not how we deliver"
7. "Indonesia refund tier 1/2/3 — same shape. Tier 1 in 3 days, Tier 2 in 2 weeks, Tier 3 in 6 weeks. Customer got chart Thursday + full dashboard 3 weeks later"
8. "I'll commit Tier 1 by Thursday EOD with a written design doc — verbal commitments drift in 24h"

### 🚨 红线 (top 10 anti-patterns)

1. Yes without internal alignment
2. Verbal-only commitments
3. Heroics culture promise
4. No written design doc
5. Ghost on Tier 2/3 after Tier 1 ship
6. Put your name on impossible commitment
7. "Let me check with engineering" (weak)
8. "We'll try our best" (ambiguity)
9. 替客户决定 (不让客户 explicitly choose)
10. AE 公开反驳 (公司面子 -100)

### 📊 数字 anchors (面试必记)

| Metric | Value | Source |
|---|---|---|
| First-conversation response time | 5 minutes 内 acknowledge + ask driver | 不急 yes/no |
| 5 question clarify budget | 5-7 questions max | BSCFS-aligned |
| Path A (full scope, 6w) | high quality | baseline 选项 |
| Path B (full scope, 3d) | 20-30 P1 bugs + 4w fix = 5w stable total | bug bomb |
| Path C (20% scope, 3d, polished) | 3w to full dashboard | ⭐ recommend |
| 6 driver archetypes | Board/CEO commit / 监管 / 竞品 / 合同 / PM 焦虑 / 客户不知 | identify 真因 |
| 80/20 carve-out | 20% work delivers 80% value | core only |
| Polish work | 40% work, 15% value | defer |
| Edge case | 40% work, 5% value | defer |
| Tier 1 MVP scope | 1 URL, 1 view (no interact), 1 metric, 1 user, 90 days data, EN only, Desktop only | radical |
| 30-sec internal Slack check | EM ✓ before committing | 不 30-min |
| 24h design doc | written commit, customer sign-off | 防 goal-post shift |
| Daily 15-min sync during ship | visibility low anxiety | 客户 not focused on counting |
| Pessimistic numbers (Path B) | 20-30 P1 bugs / 15-20% outage demo / 4w 2 engineers fix | concrete > vague |
| Customer "wants ALL" math | "Tier 1 stable 3w vs Rush stable 5w" | math response |
| Iron Triangle picks 2 of 3 | scope × quality × time | 教育 framework |
| AE over-promise written follow-up | "RCA EOD tomorrow, re-demo Thursday" | anchor not "24h fix" |
| Heroics refusal | within standard work hours | sustainability |
| Indonesia refund tier 1/2/3 reference | tier 1 in 3d / tier 2 in 2w / tier 3 in 6w | proven shape |

### 💡 24h Design Doc cheat (背诵 structure)

| Section | Content |
|---|---|
| Context | 1 paragraph what / when / who |
| Problem to solve | Specific user behavior (CFO opens chart in board review) |
| Tier 1 scope | What we WILL build (5 bullets) |
| Tier 1 NOT-scope | What we WON'T build (5 bullets, explicit) |
| Tier 2 + 3 scope + dates | Roadmap with realistic dates |
| Dependencies from customer | Their commitments (data / decision / sign-off) |
| Daily check-in schedule | Same time, 15 min, owner per side |
| Quality gates | Ship criteria (functional + non-functional) |
| Sign-off signature lines | Customer side: __ Our side: __ Date: __ |
