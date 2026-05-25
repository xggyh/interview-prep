## Q08 · 你推翻过的一个技术决策, 从中学到了什么

> "Tell me about a technical decision you made and later had to overrule yourself on — or one you were overruled on. What did you learn, and how do you make decisions differently now?"

**Round**: Behavioral (30-45 min, hiring manager 或 cross-functional)
**出处**: Exponent 2026 FDE Guide · 公司: OpenAI / Anthropic / Palantir / Databricks 高频. 变体: "tell me about a technical decision you regret" / "describe a time you changed your mind" / "what's a technical mistake that taught you the most"

---

## 📖 术语速查 (本题用到的)

> 这题是 wrong decision + reversal 故事. 重点是 self-awareness 方法论 + 多市场 localization + agent platform 一些技术术语.

### 自我审查 / 反转方法论 ⭐ 这题的核心

| 术语 | 解释 |
|---|---|
| **Wrong-process vs wrong-outcome** ⭐ | Wrong-outcome = 信息当时合理但运气差 (可 OK). Wrong-process = 决策过程有 avoidable gap (真正 growth opportunity). |
| **Assumption list** ⭐ | 显式假设清单. Major decision 前列 explicit + implicit assumption + verification plan. Peer review 5 min 比 review final design 30 min 更有效. |
| **Confirmation bias** ⭐ | 确认偏误. 见 contradictory data 先找 alternative explanation. |
| **Signal convergence (3-signal threshold)** | 信号收敛. 1 customer = noise, 3 customers same pattern = real, 3 + direct observation = reverse decision. |
| **Direct observation > metric** ⭐ | 直接观察 (现场看 47 通话) 比抽象 metric 更能 shift conviction. |
| **24-hour pause** | 24 小时暂停. First contradictory signal 不立刻 dismiss, 暂停一天 confront data. |
| **Refuse diffusion of ownership** | 拒绝分摊 ownership. Tech lead 说 "I also approved" 你说 "I was scope owner". |
| **Hypothesis order** | 假设顺序. Cheapest hypothesis 先验证, 不 jump to most expensive (e.g., fine-tune). |
| **Generalization assumption** | 泛化假设. "印尼 working pattern 能推广" 是 invisible 假设 — 没 verbalize 没人能 catch. |
| **Damage control** | 损害控制. Wrong decision 已 ship 后怎么 unwind + customer comm + path forward. |

### 反转 sequence

| 术语 | 解释 |
|---|---|
| **Conviction shift** | 信念转变. Direct observation 比 abstract metric 更易 trigger. |
| **Reversal owner statement** | 反转主动认领声明. 不 hedge "我们 should have", direct "I was wrong". |
| **Path forward** | 前进路径. 不让 conversation 停在 problem 上, 立刻提 next step. |
| **Reversed default** | 反转默认. "Every parameter is hyperparameter until proven constant". |

### 多市场 / Localization

| 术语 | 解释 |
|---|---|
| **Multi-region localization** ⭐ | 多市场本地化. 翻译只是其中一层. |
| **Cultural workshop** | 文化研讨. 1 周 with local ops, 进 scoping default. |
| **Persona design** | 人设设计. Agent 在不同市场的语气. |
| **Escalation logic per-market** | 各市场升级逻辑不同. |
| **TTS A/B with local audience** | TTS 声音跟当地受众 A/B test. |
| **Catch rate variance** | 各市场 catch rate 方差. 8pp → 2pp 是显著收敛. |
| **Persona/voice culturally mismatched** | 人设 / 声音 跟文化不匹配. 巴西女声听起来像 telemarketing. |
| **Cultural cue mismatch** | 文化信号错位. 客户 ask "are you human?". |
| **Cultural advisor** | 文化顾问. Per-market persona 设计 with local 顾问. |

### Agent Platform 术语 (alternate STAR)

| 术语 | 解释 |
|---|---|
| **Memory layer (vector vs SQL)** | Agent 记忆层后端选择. Vector DB (semantic search) vs SQL (exact match). |
| **Pluggable backend** | 可插拔后端. 让客户选 storage. |
| **Forced standardization** | 强制标准化. Anti-pattern, 用 escape hatch 替代. |
| **Semantic recall** | 语义召回. Vector DB 能力, SQL 不能. |
| **Voluntary migrate** | 自愿迁移. 客户用 SQL 跑了 6 个月, 主动换 vector. |

### Routing / Fine-tune 术语 (alternate STAR)

| 术语 | 解释 |
|---|---|
| **Fine-tuning** | 微调. Routing 70% 不够先 jump to fine-tune 是 wrong hypothesis order. |
| **Confusion matrix** | 混淆矩阵. 看 mis-classification 落在哪. 这题的 "look at data first" 工具. |
| **Tool description ambiguity** | 工具描述歧义. Routing 错的真正 root cause, fine-tune 修不了. |
| **RAG-based tool discovery** | 基于 RAG 的工具发现. 修复 routing 的方法. |
| **'Data before model' principle** | 先看数据再训模型. MLE 第一反应 train, FDE 第一反应 look at data. |

### 业务 / 监管

| 术语 | 解释 |
|---|---|
| **OJK / OJK audit** | 印尼监管 + 审计. |
| **Compliance team** | 合规团队. BNPL VP case catch 你 over-confidence. |
| **Eligibility surface** | 资格暴露. Chatbot 自由 surface 具体额度 = 监管红线. |
| **Monetary promise** | 金钱承诺. 自由 surface 数字 = 触发 monetary promise regulation. |

### ASR / Cascade 术语 (alternate)

| 术语 | 解释 |
|---|---|
| **ASR cascade** | ASR 级联. Azure → Google → Whisper. |
| **Per-language fallback order** | 各语言的兜底顺序不同. "Fallback order is hyperparameter not constant". |
| **Whisper** | OpenAI 开源 ASR. 各语言性能不一. |
| **Hyperparameter** | 超参数. 跟 constant 区分 — hyperparameter 要 per-language tune. |

### 反 pattern / 红线

| 术语 | 解释 |
|---|---|
| **Humblebrag** | 谦虚式炫耀. 用 "wrong decision" 故事其实在炫耀自己最终对.. |
| **Luck-credit, not learning** | "Wrong decision but everything turned out fine" — 把运气当 learning. |
| **Over-claim** | 夸大. "I'm now expert in X" 4 months 后是 over-claim. |
| **Blame shifting** | 推锅. "Vendor 不靠谱" 是 anti-pattern. |

---

## 这道题在考什么

这是 **FDE 题里 self-awareness signal density 最高的一道**. 表面问技术决策, 实际筛 6 件事:

- **Intellectual honesty about being wrong** —— 你能不能讲一个真实你 wrong 的 decision, 不是 humblebrag
- **Specific technical depth** —— wrong call 的 detail level 让 manager 判断你真做过
- **Learning extraction (transferable)** —— 不是 "学到 X 重要", 是 "我现在每个 decision 默认做 Y"
- **Reversal mechanism / detection** —— 你怎么 know 你 wrong, 多快, 通过什么 signal
- **Damage control** —— Wrong decision 已 ship 后怎么 unwind, customer comm 怎么做
- **Distinguish wrong-process vs wrong-outcome** —— Senior FDE 区分 'right decision wrong outcome' (acceptable) vs 'wrong decision regardless of outcome' (real learning)

**没说出口的红线**:

- "I haven't really made a wrong decision" → fake competence
- "It wasn't really wrong, just a different priority" → no honesty
- "Manager overruled me but I still think I was right" → no growth
- "Wrong decision but everything turned out fine" → not learning, lucky
- "I learned to think before deciding" → too generic
- 没有 specific technical detail → 你没真做过

---

## 完美答案架构 (Layered Response)

8 段结构, total ~4-5 分钟:

| # | 层 | 时间 | 这层该说什么 | 开口句 |
|---|---|---|---|---|
| 1 | **Context — the decision** | 20s | What decision, when, who involved | "Voice agent multi-region rollout, my call to scope localization as 'translate prompts per language'..." |
| 2 | **Why I thought I was right** | 30s | Decision rationale at time | "My reasoning at the time: (1) translation is the standardized localization framework, (2) cost is high to do more, (3) Indonesia worked..." |
| 3 | **The signal that I was wrong** | 30s | How / when you detected | "Thailand launch week 2, ops told me catch rate 比印尼 low 8 percentage points. Specific: directness in 泰语 felt rude..." |
| 4 | **First reaction (vulnerability)** | 30s | Did you immediately accept? | "First reaction was 'maybe Thai market less mature, give it 4 weeks'. I almost dismissed signal. 关键 vulnerability admit..." |
| 5 | **What it took to convince me** | 45s | 2nd / 3rd signal, data confronts you | "Brazil launch same pattern. By 3rd market same issue, I went to Bangkok 3 days sit with ops, watched 47 calls..." |
| 6 | **The reversal + damage control** | 60s | How you unwound, customer comm | "I told my manager + tech lead: 'I was wrong on scope, need 4 weeks to redo persona + escalation per market'. Customer comm to ops..." |
| 7 | **The systemic learning** | 30s | What you default to NOW | "Now every multi-market deployment scoping default includes cultural workshop, persona design with local advisor, TTS A/B with local audience..." |
| 8 | **Meta lesson — process vs outcome** | 30s | Distinguish wrong-process vs wrong-outcome | "Lesson: 'right decision wrong outcome' OK, 'wrong decision regardless of outcome' is real growth opportunity..." |

Total: ~4-5 min.

---

## 详细回答 (Sample Monologue) — 可以照背

> "我讲 voice agent multi-region localization 那次, 因为它是我最 painful + most teaching wrong technical decision.
>
> **Context — the decision**:
>
> 印尼 voice agent 跑了 6 个月 成功. 团队让我 lead multi-market expansion (6 个 markets: 越南 / 泰国 / 菲律宾 / 巴西 / 墨西哥 / 巴基斯坦).
>
> Architecture 决策: 我 scope localization as 'translate prompts per language, reuse persona + escalation logic'. **核心假设**: 印尼 working persona + escalation logic generalize.
>
> 我 ship 这个 scope, kicked off 6 markets in parallel.
>
> **Why I thought I was right**:
>
> 三个 rationale at the time:
>
> **One**: Translation is the standardized localization framework. 软件工业 i18n best practice = string externalization + translation. 我 reuse 这个 pattern.
>
> **Two**: Cost. Per-market cultural design 我 estimate 4 weeks/market × 6 markets = 24 weeks. Translation-only 1 week/market = 6 weeks. 4× cost saving.
>
> **Three**: 印尼 worked. 印尼 persona + escalation logic is empirically successful. Empirical > theoretical, 我 think.
>
> 三个 rationale 当时 看都 sensible. 我 spent 1 hour 跟 tech lead align scope, 通过.
>
> **The signal that I was wrong**:
>
> 泰国 launch week 2, 泰国 ops lead Slack 我:
>
> '我们 catch rate 比印尼 low 8 percentage points. 客户挂电话比例 高. 客户 feedback 是 agent 太 direct, rude.'
>
> 具体 example 她发给我: agent 说 'Please confirm your payment plan today' — 在泰国语 culture 里 'today' 加 imperative 感觉 push 太 hard, polite framing 应该 'when you have time this week, would you consider...'.
>
> Catch rate 8pp drop = real material impact (印尼 25%, 泰国 17%). 不是 noise.
>
> **First reaction — vulnerability admit**:
>
> 我 first reaction 不是 'shit I was wrong'. 我 first reaction 是 'maybe 泰国 market less mature, give it 4 weeks to ramp up'.
>
> 这是 confirmation bias attack. 我 invest 1 hour scoping translation-only, 我 emotionally bought into it. 见 contradictory data 我 first 找 alternative explanation (market less mature) 而不是 update.
>
> 这种 first reaction 大约 occupied me 1 week. 1 weeks 我 actively 不 confront 泰国 data, 处理其他 market launch logistics.
>
> **What it took to convince me**:
>
> Week 6 (after Thailand launch), 巴西 launch. 巴西 ops Slack 我:
>
> '客户 hang-up rate 比印尼 30% 高. TTS 女声听起来像 telemarketing, 客户 reflexively hang up.'
>
> 第二 market same essential pattern (不是 same surface, 但 underlying cause same: persona/voice culturally mismatched).
>
> Week 8 墨西哥 launch, **same pattern**.
>
> 3/3 后续 markets exhibit cultural mismatch. 我 still 不 100% convinced. 我 flew to 曼谷 3 days, sit with 泰国 ops, **watch 47 真实 calls**.
>
> Watch live calls 是 conviction-changing experience. 47 calls 我 listen, 中 18 calls 客户 explicit hang up because agent 太 push. 5 calls 客户 confused by direct phrasing. 4 calls 客户 ask 'are you human?' (cultural cue mismatch).
>
> **直接 confront 数据 + 直接看 customer reaction = conviction shift**. 不是抽象 metric, 是看到具体 47 个 humans hang up because of my scope decision.
>
> Bangkok day 3, I admit: 'I was wrong. Translation 不够. Persona + escalation 必须 per-market.'
>
> **The reversal + damage control**:
>
> 我回 Singapore, schedule meeting with manager + tech lead + 6 个 market ops leads.
>
> Opening:
>
> '我 scoping decision 8 weeks 前我 made was wrong. Translation-only localization 不够 multi-market voice agent. 我 need 4 weeks redo persona + escalation logic per market. 这 cost 我们 6 weeks (1 week scope + 4 weeks redo + 1 week re-launch) per market 已 launched. 4 markets affected = 24 person-weeks delay.'
>
> 我 没 sugar-coat. 没 say 'we should have done this'. Say 'I should have done this'.
>
> Tech lead (initially aligned with translation-only scope) 第一反应: 'I also approved scope, this isn't just on you'.
>
> 我 appreciate, but maintained: 'I was scope owner. Tech lead approved my proposal, but proposal was mine.'
>
> Customer comm to 6 ops lead:
>
> Specific status update: '我 wrong on initial scope. 我们 launched 4 markets with sub-optimal localization. Catch rate impact 8-10pp. 我们 redo persona + escalation, 4 weeks. 我 personally apologize to ops teams 已 launched markets — your weeks dealing with sub-optimal agent was my call.'
>
> Damage control:
>
> 1. **4 weeks rapid redo**. Per-market cultural workshop (3 days each), persona redesign with local advisor, TTS A/B
> 2. **2 unlaunched markets pause**: Mexico / 巴基斯坦 pause until new playbook
> 3. **Apology personal Zoom** 跟 4 个 already-launched ops lead 各 30 分钟. Listen, no defense.
>
> **The systemic learning — what I default NOW**:
>
> 三件事 now default mandatory:
>
> **One — Multi-market scoping default includes cultural workshop**. 1 week per market, before scoping doc closed. Cultural review 是 mandatory line item, 不是 optional.
>
> **Two — Localization > Translation 显式 principle**. Multi-market 任何 product, 我 write '应包括' list: translation + cultural framing + persona + UX modality + TTS voice / image choice + escalation rules + compliance prompt. 不能 only translate.
>
> **Three — 'Generalization assumption' challenge default**. 我 reuse 印尼 working pattern 时, default question: 'what about 印尼 context made this work? Is this context true in other market?' 这个 question 我 8 weeks 前 should have asked.
>
> **Meta lesson — process vs outcome**:
>
> 这个 case 我 wrong-process 不仅是 wrong-outcome. 区分:
>
> **Wrong-outcome**: 我 made best decision with info I had, outcome 偏差 (e.g., vendor unexpectedly downgraded). 不 actionable learning.
>
> **Wrong-process**: 我 made decision with avoidable gap in process. 印尼 generalization assumption I never explicit challenged. 如果我 explicit asked '什么 made 印尼 work?', I'd have surface 'culture-specific persona is invisible factor'. 这种 process gap 是 actionable learning.
>
> Senior FDE distinguishes 这两类. **Wrong-outcome 可 OK + 改进. Wrong-process 是 growth opportunity, not optional**.
>
> 我现在每个 major architectural decision 写 'assumption list' — explicit list 我 assume true (often invisible). Peer review 这 list 比 review final design 更有效."

---

## Gao Xin 简历专属 STAR 模板

至少 1 完整 STAR (multi-region localization wrong scope), 2 alternate.

### ★ STAR 1: Multi-Region Localization Wrong Scope (★ PRIMARY)

**S** (Situation):
> "印尼 voice agent 跑 6 个月成功. Team 让我 lead multi-market expansion (6 markets). 我 scope localization 'translate prompts per language, reuse persona + escalation'. Tech lead approve. Ship to 6 markets parallel."

**T** (Task):
> "Detect wrong decision, accept conviction shift, reverse + damage control + extract systemic learning."

**A** (Action):
1. **Decision context**: 3 rationale (translation is standard / cost 4× saving / Indonesia worked)
2. **First signal week 6 (Thailand)**: catch rate 8pp lower
3. **First reaction wrong (vulnerability)**: 'market less mature' alternative explanation. Confirmation bias attack 1 week.
4. **2nd / 3rd signal (Brazil / Mexico)**: same pattern across 3 markets
5. **Conviction shift**: fly to Bangkok 3 days, watch 47 calls live. 27 calls show cultural mismatch impact.
6. **Reversal owner statement**: 'I was scope owner, this is my call wrong'. Refuse tech lead diffusion.
7. **Damage control**:
   - 4 weeks redo per-market persona
   - 2 unlaunched markets pause until new playbook
   - Personal Zoom apology to 4 ops leads
8. **Systemic defaults established**:
   - Cultural workshop mandatory in multi-market scoping
   - 'Localization > Translation' principle documented
   - 'Generalization assumption challenge' default in design

**R** (Result):
- 4 markets redo, **4 weeks/market** redo cost
- Total delay: 24 person-weeks
- Post-redo: catch rate variance 印尼 to 泰国 8pp → 2pp
- Subsequent 2 markets (Mexico / 巴基斯坦) using new playbook, **0 cultural redo needed**
- 'Cultural workshop' default adopted by BNPL chatbot team + Internal Agent Platform team

**Vulnerability line**:
> "我 worst sub-failure 不是 wrong scope, 是 **week 6 first signal 我 dismissed**. 1 week confirmation bias 让 damage compound (Brazil launched on same wrong scope). 现在我 first contradictory signal 不 immediately dismiss, 我 explicit pause 24 hours 'is this real?'. 1 day pause > 1 week dismiss."

---

### STAR 2: Memory Layer Vector DB Forced Standardization (Alternate)

**S**: Internal Agent Platform Memory layer 设计. 我 propose vector DB as standard storage backend. Risk team lead push back (their team uses SQL infra).

**T**: I initially stood firm. Multiple rounds debate. Eventually I overruled myself.

**A**:
1. **Initial decision**: vector DB standard, 3 round disagreement with Risk team lead
2. **Self-check moment**: 我 ask myself 'is this principle or ego?'. Honest answer: partially ego ("I want to standardize, easier to reason about").
3. **Reversibility check**: Memory backend is two-way (可换) + low blast (single team). Doesn't meet 'hill worth dying on' criteria.
4. **Reversal**: I overruled myself, redesigned Memory layer with pluggable backend
5. **Outcome**: Risk team adopt SQL Month 1. 6 months later their use case grew, voluntarily migrate to vector

**R**:
- Memory layer adoption: Risk team Month 1 + voluntary migrate 6 months later
- **0 forced standardization tension** with other team
- Pattern (escape hatch + pluggable backend) reused 14 internal teams adopt platform
- Risk team lead later became champion of platform

**Vulnerability line**:
> "我 wrong process: 3 rounds debate before self-checking ego. 我 should have done self-check round 1, save 3 weeks delay. 现在我 initial disagreement round 1 我 explicit self-check '是 principle 还是 ego? Reversibility? Blast?' 30 秒 self-check 救我多次."

---

### STAR 3: BNPL Routing Initial Approach (Wrong Heuristic Order) (Alternate)

**S**: BNPL chatbot launch month 1, routing accuracy 70%. Far below 90% target. I needed to diagnose.

**T**: Diagnose root cause + fix.

**A**:
1. **Initial decision**: Jump to fine-tuning. Rationale: routing accuracy 是 model task, fine-tune the model.
2. **Spent 1 week**: data preparation for fine-tuning, training pipeline set up
3. **Manager push back week 1**: 'have you looked at confusion matrix?'
4. **Wrong call admitted**: Day 8, I look at confusion matrix. 60% mis-route is **tool description ambiguity**, not model capacity. Fine-tuning would NOT have fixed it.
5. **Reversal**: Pause fine-tuning, switch to RAG-based tool discovery + rewrite 12 tool descriptions
6. **Result week 6**: routing 70% → 92%

**R**:
- Routing **70% → 92% in 6 weeks** (would not have been achievable via fine-tuning alone)
- **Saved 3-4 weeks** of unnecessary fine-tuning work
- 'Data before model' principle adopted by Internal Agent Platform team
- I now default 'confusion matrix first, model last' for routing problems

**Vulnerability**:
> "我 wrong call 是 hypothesis order. 我 jump to most expensive hypothesis (fine-tune) without first checking cheapest (look at data). MLE 第一反应 is 'train', FDE 第一反应 should be 'look at data'. Manager 的 1 question 'have you looked at confusion matrix' 救我 3-4 周. 现在我 every routing / quality issue 默认 'confusion matrix first 1 day, model intervention last'."

---

## 5 个 Follow-ups (interviewer 追问 + 准备答案)

### Follow-up 1: "How did you tell your manager you were wrong?"

**Answer**:
> "Multi-region case, my opening to manager + tech lead + 6 ops leads (one meeting):
>
> 'My scoping decision 8 weeks ago was wrong. Translation-only localization 不够. I need 4 weeks redo persona + escalation per market. Cost 24 person-weeks delay.'
>
> 不 hedge ('我们 should have'). Direct ownership ('I was'). 不 blame ('tech lead approved').
>
> Tech lead tried diffuse 'I also approved'. I appreciate but maintained 'I was scope owner'. Refusing diffusion 是 trust-building.
>
> 然后 path forward immediately: '4 weeks redo, 2 unlaunched markets pause, personal apology to 4 ops leads'. 不让 conversation 在 problem 上 stuck, 立刻 path forward.
>
> Manager 第一反应: 'thanks for owning it. Let's redo'. 没 anger, 因为我 ownership + path forward + lesson 三件齐.
>
> **Key**: telling manager you wrong 是 trust-building if 3 件齐. 是 trust-destroying if 只 confess 没 path."

### Follow-up 2: "What if you had been right? How do you know when to override gut vs respect dissent?"

**Answer**:
> "**Two tests**:
>
> **Test 1 — Convergence of evidence**. 1 customer complaint = noise. 3 customer same pattern = real. Multi-region case 我等到 3/3 markets 同 pattern 才 conviction shift. 1/3 markets 我 dismiss 是 mathematically reasonable.
>
> **Test 2 — Confront direct observation**. Bangkok 3 days watch 47 calls. 直接 看 customer reaction 比 metric stronger. 印尼 base model 13B vs 7B 我 stand firm 因为 pilot data direct.
>
> 区分:
> - 1 noisy signal contradicts gut → 维持 gut, gather more
> - 3 convergent signals + direct observation contradicts gut → override gut
> - 1 noisy signal contradicts gut + direct observation confirms signal → override gut quicker
>
> 多 region wrong 我 sub-failure: signal was noisy at 1/3, real at 3/3. 我 should have flown to Bangkok 1/3 signal time, but bias 让 me wait 3/3."

### Follow-up 3: "Have you ever NOT reversed when you should have?"

**Answer**:
> "Yes. ASR cascade per-language fallback order. I designed cascade global same order (Azure → Google → Whisper). Pakistan launch revealed Urdu fallback order wrong (Whisper > Google on Urdu).
>
> Signal week 2 巴基斯坦 ops Slack 'Whisper better for Urdu'. I dismissed, kept global same order. 'Whisper too slow for fallback, accept lower accuracy'.
>
> 2 个 weeks later second Urdu accent issue. Still dismissed.
>
> 4 weeks later I finally tested per-language fallback order. Confirmed. 4 weeks of avoidable accuracy on Urdu.
>
> **What I learned**: 'fallback order is hyperparameter not constant'. 我 default 'constant', signal told me hyperparameter, I dismissed.
>
> 现在我 default 'every architectural parameter is hyperparameter until proven constant'. Reversed default."

### Follow-up 4: "How do you separate 'wrong decision' from 'right decision wrong outcome'?"

**Answer**:
> "**3 questions**:
>
> **Q1**: With info I had at decision time, was the decision logically sound?
> - Multi-region scope: at decision time, my 3 rationale were all reasonable. But I missed 1 implicit assumption (印尼 generalization). So **wrong-process**.
>
> **Q2**: What did I assume that I didn't explicit verify?
> - Multi-region: 'cultural assumption generalizes from 印尼'. Implicit, never verified. **Wrong-process**.
>
> **Q3**: If I redo with same constraint, would I make same call?
> - Multi-region: No, because now I default cultural workshop. **Wrong-process confirmed**.
>
> Counter-example: ASR vendor selection 巴基斯坦. Azure went down 40 min. **Right decision wrong outcome** — at decision time vendor SLA was 99.9%, my cascade fallback was insurance against unlikely event. Vendor reliability degraded, not my decision wrong.
>
> Senior FDE distinguishes these. Wrong-process needs systemic learning. Wrong-outcome may need monitoring improvement but not decision process change."

### Follow-up 5: "What's the most important systemic change you made from learning to overrule yourself?"

**Answer**:
> "**Explicit assumption list 在 architectural decision time**.
>
> Multi-region case taught me — wrong-process 90% 是 invisible assumption. 印尼 generalization 假设 I made without verbalizing. Not on doc, not on whiteboard, only in my head.
>
> Now every major architectural decision I write:
> ```
> Assumptions:
> 1. [explicit, e.g., 'cultural persona generalize from 印尼']
> 2. [explicit, e.g., 'ASR vendor SLA 99.9% sufficient']
> ...
>
> Verification plan per assumption:
> 1. [e.g., '1 week cultural workshop per market before scoping close']
> 2. [e.g., 'pre-design cascade fallback']
> ...
> ```
>
> Peer review this assumption list (5 min) better than review final design (30 min). Catches invisible assumption.
>
> 这个 'assumption list' default 我 transferred to BNPL, Internal Agent Platform, ConvFinQA. Cross-domain pattern. Adopted by 2 other internal teams.
>
> **The biggest systemic change from this lesson**."

---

## ❌ 死路答法 (碰了就挂)

### 死路 1: "I haven't really made a wrong technical decision."

**为什么挂**: Fake competence. 任何 3 年 production 经验都有 wrong decision. 不讲 = 你 没真 own 过 OR 不 self-aware.

**怎么改**: 选 1 个 specific wrong call. Multi-region scope, Memory layer SQL, BNPL fine-tune jump. Real with specifics.

---

### 死路 2: "It wasn't really wrong, just a different priority."

**为什么挂**: 不 honest. 抽象化 wrong decision = 不 take ownership.

**怎么改**: 显式 "I was wrong on X". Not "we had different priority". Own it.

---

### 死路 3: "Manager overruled me but I still think I was right."

**为什么挂**: No growth. 顽固 ego signal. Manager 听到 candidate 还在 reljustify old wrong, immediate red flag.

**怎么改**: 显式 update — "manager was right, I was wrong, here's what I learned". 不 cling.

---

### 死路 4: "Wrong decision but everything turned out fine."

**为什么挂**: Luck-credit, not learning. FDE manager 想看 systemic learning.

**怎么改**: 即使 outcome OK, 显式 "process was flawed, here's what I default now to prevent". Process > outcome.

---

### 死路 5: "I learned to think before deciding."

**为什么挂**: 太 generic. 谁不知道 think before? FDE manager 想 specific 默认 change.

**怎么改**: "我现在 default 写 'assumption list' before major decision, peer review the list 5 min". Specific actionable change.

---

### 死路 6: 没 customer comm part

**为什么挂**: Wrong decision often impact customer. SWE 视角 misses customer comm. FDE 视角必须 include.

**怎么改**: 显式讲 你 communicate wrong decision 给 customer / stakeholder. Status update, apology, path forward.

---

### 死路 7: 没 quantify damage / cost

**为什么挂**: Wrong decision 没 cost = not real. Specific dollar / time / customer impact 让 story credible.

**怎么改**: "24 person-weeks delay, 4 markets affected, catch rate 8pp lower for 4 weeks". Quantify.

---

## ✅ 加分项 (top 5)

### 加分 1: 区分 wrong-process vs wrong-outcome

显式 frame this distinction. "Wrong-outcome may be just bad luck, wrong-process is real growth opportunity". 这种 framework 是 senior signal.

### 加分 2: First reaction wasn't immediate accept (vulnerability)

"My first reaction was alternative explanation 'market less mature'. Confirmation bias 1 week before I confronted data." 这种 self-honest 让 trust 拉满.

### 加分 3: Direct observation > metric (Bangkok 47 calls)

"Watched 47 live calls. 27 showed cultural mismatch. Direct observation shifted conviction." 这是 senior FDE pattern — metric can be argued, direct observation can't.

### 加分 4: Refusing diffusion of ownership

"Tech lead said 'I also approved'. I appreciated but maintained 'I was scope owner'". 这种 sole ownership 在 wrong call 是 maturity signal.

### 加分 5: Systemic default change (assumption list)

"Now every major architectural decision I write explicit assumption list, peer review the list". Specific transferable default 是 real learning evidence.

---

## 一句话总结

> **"Overruled technical decision" 的 winning answer 不是讲你做对了什么, 是 用 'first reaction wrong + 3-signal convergence + direct observation + refuse-diffusion ownership + systemic default change' 证明 "我 wrong call 给我 systemic learning, 我现在 default 写 assumption list, peer review the list 比 final design 更有效"**.
>
> Wrong-process > wrong-outcome 区分. Reversed default ('every parameter is hyperparameter until proven constant') 是 senior FDE signal.

---

## Cheat Sheet (面试前 30s 扫一眼)

```
Question type:
  Behavioral / Self-awareness / Technical Decision-making (4-5 min monologue)
Key skill being tested:
  Honest about wrong + specific technical detail + signal-driven reversal + ownership refusal of diffusion + systemic default change + process vs outcome

Answer arc (8 段):
  1. Context — the decision (20s)         — What, when, who
  2. Why I thought I was right (30s)     — Decision rationale at time (3 reasons)
  3. The signal that I was wrong (30s)   — How/when detected
  4. First reaction wrong (30s)          — Confirmation bias vulnerability
  5. What convinced me (45s)             — 3-signal convergence + direct observation
  6. Reversal + damage control (60s)     — Customer comm + refuse diffusion + path forward
  7. Systemic learning (30s)             — Specific default now (assumption list, cultural workshop)
  8. Meta lesson (30s)                   — Wrong-process vs wrong-outcome distinction

Numbers to drop:
  Multi-region localization wrong scope:
    6 markets parallel rollout
    Thailand catch rate 8pp lower (印尼 25% → 泰国 17%)
    Brazil hang-up 30% higher
    3/3 markets pattern after Mexico
    Bangkok 3 days, 47 calls watched (27 showed cultural mismatch)
    4 weeks redo per market × 4 markets = 24 person-weeks
    2 unlaunched markets paused (Mexico / Pakistan)
    After redo: catch rate variance 8pp → 2pp
  Memory layer (alternate): 3 rounds wasted debate, 6 months voluntary migrate
  BNPL routing (alternate): 1 week wasted on fine-tune prep, 70 → 92% in 6 weeks

Vulnerability:
  "Worst sub-failure: week 6 first signal I dismissed for 1 week
   (confirmation bias 'maybe Thai market less mature').
   Brazil launched on same wrong scope during my 1-week dismissal.
   Now first contradictory signal I explicit pause 24 hours
   'is this real?' before dismissing.
   1 day pause > 1 week dismiss."

Close:
  "Wrong-process distinguishes from wrong-outcome. Wrong-outcome
   may be bad luck. Wrong-process is real growth opportunity.
   I now default 'assumption list + peer review the list' for
   every major decision. 5 min review the list > 30 min review
   final design. Catches invisible assumption."

Red lines:
  - "Haven't made wrong decision" (fake competence)
  - "Not really wrong, just different priority" (no ownership)
  - "Manager overruled, I still think right" (顽固 ego)
  - "Turned out fine" (luck credit, not learning)
  - "Learned to think before deciding" (too generic)
  - 没 customer comm (SWE 视角)
  - 没 quantify damage

3 ready STAR (alternate):
  STAR 1: Multi-region localization wrong scope (★ primary, scope mismatch)
  STAR 2: Memory layer vector DB forced standardization (ego vs principle)
  STAR 3: BNPL routing fine-tune jump (wrong hypothesis order)

5 follow-ups ready:
  Q1: How tell manager you wrong? → Direct + path forward + refuse diffusion
  Q2: Override gut vs respect dissent? → 3-signal convergence + direct observation tests
  Q3: NOT reversed when should? → ASR cascade per-language fallback, dismissed 4 weeks
  Q4: Wrong-decision vs right-decision-wrong-outcome? → 3 questions (logic sound? assumption verified? redo same?)
  Q5: Most important systemic change? → Explicit assumption list + peer review the list

Wrong-process vs wrong-outcome (3 questions):
  Q1: Decision logically sound with info I had?
  Q2: What did I assume but not verify?
  Q3: If redo, would I make same call?
  Yes all three Yes = wrong-outcome (acceptable + improve monitoring)
  No on any = wrong-process (systemic learning required)

Signal convergence thresholds:
  1 customer same complaint   = noise, don't update yet
  3 customers same pattern    = real, update conviction
  3 + direct observation      = update + reverse decision
  1 + direct observation      = update conviction sooner

Sequence (when first contradictory signal):
  1. Pause 24 hours (don't immediately dismiss)
  2. Confront data (read confusion matrix, check sample)
  3. If still uncertain, fly to source (Bangkok 47 calls)
  4. If reversal needed: own publicly + refuse diffusion + path forward

Systemic defaults from this lesson:
  - Assumption list before major architectural decision
  - Peer review the assumption list (5 min) > review final design (30 min)
  - 'Every parameter is hyperparameter until proven constant'
  - First contradictory signal: 24-hour pause + look at data, don't dismiss
  - Direct observation > metric for conviction shift
```
