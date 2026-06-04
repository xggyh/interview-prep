## 题目（verbatim）

> **[OpenAI / Anthropic Hiring Manager Round — 60 min]**
>
> "How do you **handle ambiguity**? Tell me a story where requirements were unclear and you had to make calls without complete information.
>
> Follow-up: What kind of ambiguity gives you the most trouble? How do you push back when someone asks for the impossible?"

**出处**: OpenAI / Anthropic / Google FDE hiring manager 必问. Palantir / Salesforce / Databricks 也常问. 几乎所有 FDE / staff-level engineering role 都会问.

**Round**: Hiring Manager (60 min, 通常作为 round 中段问题)

---

## 这道题在考什么

FDE 工作 **90% 时间在 ambiguity 里**. Recruiter / HM 想验证 5 件事:

1. **Process** —— 面对模糊, 你有 framework 还是 panic
2. **Decision-making** —— 在不完整信息下能不能 commit, 还是 paralysis
3. **Reversibility awareness** —— 知不知道 one-way vs two-way doors
4. **Communication** —— 用 stakeholder 验证 vs 自己 silo
5. **Story quality** —— STAR + 具体 metrics + 真实细节

**没说出口的 anti-signal**:

- "I just ship and iterate" → no thoughtfulness, HM 担心你乱来
- "I align with my manager and ask them" → 显示没 judgment
- "I do a lot of research first" → 字面理解 = analysis paralysis
- "It depends" without follow-through → wishy-washy
- 故事没 metric → 显得不真实

---

# Part 1 · 教学讲解

## 1. 5 种 ambiguity 类型先讲清

不是所有 ambiguity 一样. 不同类型应对方式完全不同. **会区分**本身就是一个 senior 信号.

| Type | 含义 | 典型 trigger | 应对原则 |
|---|---|---|---|
| **Goal ambiguity** | 客户不知道想要什么 | "我想要 AI" / "make it better" | 用 discovery 帮客户决定 |
| **Technical ambiguity** | 多个 viable 架构都能做 | "VectorDB 选 Vertex AI Vector Search 还是 Vertex AI Vector Search?" | 用 trade-off matrix + reversibility |
| **Data ambiguity** | 数据稀疏 / 矛盾 / 噪声 | "我们的 retention 数据有 3 个 source 对不上" | 用 hypothesis-driven exploration |
| **Organizational ambiguity** | 多 stakeholder 优先级冲突 | "Ops 想自动化, Legal 想 audit, Product 要速度" | 用 stakeholder map + escalation |
| **Outcome / metric ambiguity** | 成功标准没定义 | "增加 efficiency" | 用 KPI lock framework |

**关键 insight**: 每次面对模糊先 **classify type**, 再选 framework. 这是 SR/Staff 跟 Junior 的区别 — Junior 把所有 ambiguity 当 "需要更多信息".

## 2. 这道题在考你什么 (深入)

### 表面 vs 深层 signal

**表面**: 听你讲一个故事, 看叙事是否清晰

**深层** (HM 真正在筛):

| 信号 | 权重 | 怎么 demonstrate |
|---|---|---|
| **有 framework 处理 ambiguity** | ★★★★★ | 不是 case-by-case 反应, 是有 D·D·D·V 这种 reusable 结构 |
| **Reversibility awareness** | ★★★★★ | One-way door 跟 two-way door 自动 distinguish |
| **数据驱动 push back** | ★★★★ | 不是直觉拒绝, 是用 pilot data 反驳 |
| **Stakeholder collaboration** | ★★★★ | 不是自己 silo 决定, 是把 ambiguity 拉到 stakeholder 一起 resolve |
| **故事 specificity + metrics** | ★★★★ | "70% throughput, 0% wrong call, 6 weeks" 这种具体数字 |
| **承认错误判断** | ★★★ | follow up 时能讲一个真实的 wrong call |
| **Speed-quality trade-off 自觉** | ★★★ | 两个都不偏废 |

## 3. 黄金 framework: D·D·D·V

**这个 framework 是这道题的核心 takeaway**. 当你说 "I have a framework for ambiguity called D·D·D·V" 时, HM 立刻 update 你的 seniority.

| Step | 含义 | 关键问题 |
|---|---|---|
| **D** — Diagnose | 识别 ambiguity type (上面 5 类) | "这是哪种 ambiguity?" |
| **D** — Decompose | 拆分 已知 / 未知 / 假设 | "什么是 fact, 什么是 belief?" |
| **D** — Decide | 按 reversibility 决策 | "这是 one-way 还是 two-way door?" |
| **V** — Validate | 用 stakeholder + pilot data 验证 | "我的 decomposition 错了怎么办?" |

### 为什么是这个顺序

**Diagnose first** — 不知道是哪种 ambiguity, 选错 framework 浪费时间.

**Decompose 比 Decide 先** — 没拆分清楚就 decide, 是赌博. 拆开后看到 "其实 80% 已知, 20% 未知" 跟 "其实 30% 已知, 70% 未知" 应对完全不同.

**Decide 用 reversibility** — Bezos 的 Type 1 (one-way) vs Type 2 (two-way) decision 经典 framework. Two-way door 可以 fast + iterate, one-way door 必须 slow + investigate. 这个区分本身是 senior 标志.

**Validate 收尾** — 防止 silo. 你的 decomposition 是 hypothesis, 不是 commandment, 必须跟 stakeholder verify.

## 4. Reversibility 决策框架 (Bezos Door Model + FDE 改造)

经典 Bezos:
- **Type 1 / One-way door**: 错了改不回来 (e.g., 公司 IPO, 决定退出市场)
- **Type 2 / Two-way door**: 错了易撤 (e.g., 试一个新功能, A/B test)

FDE 改造 (加 2 个 axis):

| Axis | One-way 增强 | Two-way 减弱 |
|---|---|---|
| **Reversibility** | 错了不能撤 | 错了能撤 |
| **Blast radius** | 影响多 stakeholder / 多客户 | 影响小 / 隔离 |
| **Time to detect** | 错了 6 个月后才发现 | 错了下周看到 |
| **Recovery cost** | $100k+ / monthly liability | < 1 week eng time |

### FDE Reversibility Decision Matrix

```
                One-way (slow + investigate)
                        │
                        │
   High blast radius    │   Pure one-way: 12 weeks scoping
                        │
        ◆ Indonesia tier 3 refund decisions
        ◆ Production model swap (Llama 2 → 3)
        ◆ Pricing change to customer
                        │
   ─────────────────────┼──────────────────────
                        │
        ◇ Add new tier 1 FAQ                ◇ Two-week pilot
        ◇ Adjust retry logic                ◇ A/B test new prompt
        ◇ Add observability metric          ◇ Toggle feature flag
                        │
   Low blast radius     │   Pure two-way: ship + measure
                        │
                        │
                Two-way (fast + measure)
```

**FDE 应用**:

- One-way + high blast → invest 8-12 weeks scoping (Indonesia tier 3)
- One-way + low blast → 2-4 weeks scoping (production single-customer change)
- Two-way + high blast → 1-2 weeks pilot then scale (multi-market rollout)
- Two-way + low blast → ship + measure same day (prompt tuning)

## 5. 不同 ambiguity 类型的 角色对照表

| Type | 你的 role | Stakeholder role |
|---|---|---|
| Goal ambiguity | 帮客户 articulate (you ask) | 客户 commit (they decide) |
| Technical ambiguity | 主导决策 (you decide) | Stakeholder review (they ratify) |
| Data ambiguity | 探索 + 报告 (you investigate) | Stakeholder consume (they read) |
| Organizational ambiguity | 映射 + escalate (you map) | Exec resolve (they decide) |
| Outcome ambiguity | 提议 + benchmark (you propose) | 客户 lock (they sign) |

**核心 insight**: 不是所有 ambiguity 都是 "你 decide". Goal / organizational / outcome ambiguity, FDE role 是 **帮客户 / stakeholder decide**, 不是替他们 decide.

## 6. 4 个真实场景演示

### 场景 A: Goal ambiguity — Indonesia ops 想 "automate refunds"

**Trigger**: Friday Slack — "we want full automation by next quarter, can you do it?"

**Ambiguity content**:
- 什么 refunds (full / partial / dispute)?
- 多大 amount limit?
- "Next quarter" 是 8 周还是 13 周?
- Wrong call 谁 accountable?
- 8% error rate 接受吗?

**Diagnose**: Goal ambiguity (客户没拆分自己的 ask) + Outcome ambiguity (没 lock 接受的 error rate)

**Action**: 2 周 pilot tier 1+2, 跟 ops 用 data reframe.

**Outcome**: 70% throughput, 0% wrong call, 6 weeks. Tier 3 6 个月后 0 wrong refund.

### 场景 B: Technical ambiguity — Voice agent ASR provider 选择

**Trigger**: "We need ASR for Pakistan launch in 4 weeks. Which provider?"

**Ambiguity content**:
- Azure / Google / AWS / self-host Whisper 都能 cover Urdu
- 价格差 5×, accuracy 差 ~2%, latency 差 ~200ms
- 没 single source of truth comparison data

**Diagnose**: Technical ambiguity (多 viable 选项)

**Decompose**:
- 已知: 4 weeks deadline, 业务需 < 500ms latency
- 未知: 真实 Urdu accuracy (vendor benchmark 不可信)
- 假设: 用户口音分布跟 vendor test set 类似

**Decide by reversibility**:
- 这是 two-way door (provider 可以换, integration layer 是 abstraction)
- 但 high blast radius (生产事故影响整个 Pakistan)
- 应对: **3-day quick eval** — 用真实 Pakistan 客户录音 (脱敏) 测 3 个 provider
- 结果: Google 在 Urdu 上 +3% accuracy 但 latency 高, Azure latency 好但 accuracy 一般, Whisper 慢但 controllable
- **Cascade design** — Azure primary, Google fallback, Whisper local last-resort

**Outcome**: Pakistan launch 按时, ASR 0 incident 第一个月.

**Reflection**: Technical ambiguity 关键不是 "选哪个", 是 "怎么设计架构让 wrong choice 易撤". Cascade fallback 让 provider 选择从 one-way 变 two-way.

### 场景 C: Data ambiguity — BNPL chatbot routing 70% accuracy

**Trigger**: Launch month 1, routing accuracy 70%, 远低于预期 90%.

**Ambiguity content**:
- Confusion matrix 没看
- 60% 错在哪类 intent 不知道
- 是模型 capacity 不够 vs prompt 模糊 vs tool description 烂 vs 用户表达不清?

**Diagnose**: Data ambiguity (root cause 不明) — 跟 goal / technical 不一样, 需要 hypothesis-driven exploration

**Decompose** (hypothesis list):
- H1: 模型 capacity 不够 → 需要 fine-tune
- H2: Prompt 模糊 → 重写 prompt
- H3: Tool description 烂 → 用 RAG-based discovery
- H4: 用户表达问题 → 加 disambiguation 提问
- H5: 数据分布偏 → 训练数据 augment

**Action**: 优先 cheap 的 hypothesis. 先看 confusion matrix 数据 (1 天) → 排除 H1 (模型 capacity 够). 看 mis-route 案例 (2 天) → 60% 是 H3 (tool description 模糊). 重写 12 个 tool description + RAG-based discovery.

**Outcome**: 70 → 92% in 6 weeks. **关键**: 没花时间 fine-tune (省 3-4 周).

**Reflection**: Data ambiguity 的处理原则 — **不要从最贵的 hypothesis 开始**. Cheap experiments first. MLE 第一反应是训模型 (贵), FDE 第一反应是看数据 (便宜).

### 场景 D: Organizational ambiguity — BNPL chatbot 的 4 个 stakeholder

**Trigger**: Product + Compliance + CS + Risk 4 个 stakeholder 各自有诉求.

**Ambiguity content**:
- Product: 越多 chatbot 越好 (UX)
- Compliance: chatbot 不能 promise specific 额度
- CS: 别抢 CS 的 job
- Risk: 不能泄漏信用数据

**Diagnose**: Organizational ambiguity (优先级冲突)

**Decompose** (stakeholder map):
| Stakeholder | 真实诉求 | 红线 | 妥协空间 |
|---|---|---|---|
| Product | UX 好 | 不能慢 > 3s | tier 2/3 可以慢 |
| Compliance | 不踩监管线 | 任何具体数字 promise | tier 1 通用 FAQ 可放 |
| CS | 不被替代 | 复杂 case 要给 CS | 简单 FAQ 可 chatbot |
| Risk | 用户数据不泄漏 | 不能 surface PII | 不含 PII 的 query 可 |

**Decide**: 这是 organizational ambiguity, FDE role 是 **map + escalate**, 不是 unilateral decide. 我做了 tier-based design 让 4 个 stakeholder 各自的红线都不被踩.

**Outcome**:
- Tier 1 (通用 FAQ) — Product + Compliance 都 happy
- Tier 2 (账户信息, 限制 surface) — Risk + Compliance 一起 review schema
- Tier 3 (复杂 case) — CS 接, 反而拿到 high-value case 提升 satisfaction

**Reflection**: Organizational ambiguity 不能 unilateral decide. **FDE 的工作是把 ambiguity 显性化, 帮 stakeholder 一起达成 consensus**. Tier-based design 是工具, 不是答案.

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | 把所有 ambiguity 当一类 | 用错 framework, 浪费时间 |
| 2 | 没 Diagnose 直接 Decide | 拍脑袋, 经常 wrong |
| 3 | Decompose 太久 (> 20% 总时长) | analysis paralysis |
| 4 | One-way door 当 two-way ship | 灾难性 wrong call |
| 5 | Two-way door 当 one-way over-scope | 浪费几周 |
| 6 | Solo decide 不 validate | 跟 stakeholder 错位 |
| 7 | "I'll get back to you" 拖延 | 信任下降 |
| 8 | Push back 不带 data | 显得 "你不愿意做" 不是 "数据说不该做" |
| 9 | Discovery 没 timebox | 永远在 discovery |
| 10 | 没 follow up 验证 hypothesis | decomposition 错了不知道 |

## 一句话总结 (Part 1)

> **Handle ambiguity 不是 "我能 ship 没 spec 的项目", 是 "我能 classify ambiguity 类型, decompose 成已知/未知/假设, 按 reversibility 决策, 用 stakeholder 验证假设"**.
>
> D·D·D·V framework + reversibility classification + stakeholder validation = senior FDE handling of ambiguity.

---

# Part 2 · 5 个深度子问题

## ⚙️ Problem 1: Goal Ambiguity — 客户不知道想要什么

### 1.1 这种 ambiguity 长什么样

典型表达 (注意捕捉):
- "We want AI."
- "Make it better."
- "Automate this."
- "Reduce cost."
- "Use GPT for our customer support."

特征:
- 抽象 verb (better / more / less)
- 没有 specific metric
- 没说 baseline
- 没说 budget / timeline / constraint

### 1.2 Discovery framework (FDE 帮客户拆 goal)

不是问 "你想要什么" — 这会 trigger 客户 defensive ("你 vendor 怎么不知道?"). 是 **帮客户 articulate**.

**5-question discovery sequence**:

1. **What's the ONE metric** that would tell you in 6 months 'this worked'?

   > Sample dialog:
   > 客户: "We want AI to improve customer support."
   > 你: "如果 6 个月后我们 review 这个项目, 一个 metric 能告诉你 'this worked', 你会看什么 number?"
   > 客户: "Hmm... ticket resolution time?"
   > 你: "OK, 'ticket resolution time'. 目前平均多少?"
   > 客户: "我 actually 不知道, 我得问 CS team."
   > 你: "Great. 这就是 step 1 — 我们 lock 这个 metric 作为 success criteria, 现 baseline 我们 next week 一起确认."

2. **What's the current baseline** without our system?

   > 关键: 客户经常不知道 baseline. 这是 discovery 第一个 actionable next step.

3. **Who's the loser** if we succeed?

   > Sample dialog:
   > 客户: "我们要 AI 自动化客服."
   > 你: "如果 chatbot 自动化 80% inbound query, 谁的 job description 会变?"
   > 客户: "CS team 的人会处理 less ticket, 但也可能 reorg 到更难的 case..."
   > 你: "OK, 这是 organizational impact. 我们 design 的时候要把 CS team 拉进来, 不然他们会 silently sabotage 项目."

4. **What's an outcome** that would make us look stupid (instead of successful)?

   > Sample dialog:
   > 你: "想象 6 个月后, 项目上线了, 但 outcome 是 disastrous. 最可能的 disaster scenario 是什么?"
   > 客户: "Chatbot 给错信息, customer 投诉到 social media."
   > 你: "Got it. 这告诉我 'accuracy + reversibility' 比 'speed' 重要. 我们 design 一个 tier 系统, tier 3 让 human 兜底."

5. **What does week-1 look like?**

   > Sample dialog:
   > 你: "如果项目 launch week 1, 你看 dashboard 上想看到什么?"
   > 客户: "Volume served by chatbot? Customer satisfaction?"
   > 你: "OK. 这两个 metric 我们 week 1 一定 instrument. 那 week 1 的 'pass' threshold 是多少?"
   > 客户: "至少 50% volume served, satisfaction > baseline."
   > 你: "Locked. 这是我们 launch criteria."

### 1.3 Goal ambiguity 的 STAR (Indonesia tier 3 refund)

**S**: Indonesia ops "我们想 automate refund, 下季度 done"

**T**: 把 abstract "automate refund" 拆成可 commit 的 specific scope

**A**:
1. Discovery — "What's the ONE metric?" → wrong-call rate
2. Discovery — "Baseline?" → 当前 manual 0.3% wrong-call
3. Discovery — "Loser?" → CS team 怕被替代; ops 要保留 oversight
4. Discovery — "Disaster?" → wrong refund 导致 customer 投诉到 OJK (监管机构)
5. Discovery — "Week 1 success?" → tier 1+2 throughput, 不 touch tier 3
6. Decompose → tier 1/2/3, 不同 reversibility
7. Pilot 2 weeks → tier 1+2 = 70% volume, 0% wrong, vs tier 3 projected 8% wrong
8. Reframe → "give you right answer faster, not wrong on time"

**R**: 6 weeks tier 1+2 上线, 70% throughput at 0% risk. Tier 3 6 个月后, 90 day 0 wrong refund.

**Key takeaway**: Goal ambiguity 不是 "客户 lazy 不告诉我", 是 **客户自己没拆开 think**. FDE 工作是帮他们 articulate.

### 1.4 Push-back dialog

如果客户拒绝 discovery, 想直接 ship:

> 客户: "Don't ask so many questions, just build it."
> 你: "Fair. 我可以 sketch 一个 strawman design in 10 minutes, 但我想 flag **3 assumptions** I'm making. 如果任一 assumption 错, design 就 invalid.
>
> Assumption 1: success metric 是 ticket resolution time
> Assumption 2: 接受 < 1% wrong-answer rate
> Assumption 3: 必须 integrate with ServiceNow (而不是 self-hosted)
>
> 你想我先 sketch, 还是先 confirm 这 3 个?"

90% 情况客户会 say "先 confirm 这 3 个".

---

## ⚙️ Problem 2: Technical Ambiguity — 多个 viable 架构

### 2.1 这种 ambiguity 长什么样

- "VectorDB 选 Vertex AI Vector Search 还是 Vertex AI Vector Search 还是 pgvector?"
- "Streaming 用 Kafka 还是 Pulsar?"
- "Voice agent ASR 选 Azure 还是 Google?"
- "Agent orchestration 用 LangGraph 还是自研?"

特征:
- N 个 viable options
- 每个 option 都能 work
- Trade-off 真实但不致命
- 决策 reversibility 不一致

### 2.2 Trade-off matrix framework

**Step 1**: 列出 options (2-5 个, 多了无意义)
**Step 2**: 列出 axes (5-7 个 dimension)
**Step 3**: 给每个 axis weight (重要性)
**Step 4**: 评分每个 (option, axis) cell
**Step 5**: 计算 weighted score
**Step 6**: 检查最高分是否 robust (敏感度分析)

### 2.3 例子: Voice agent ASR provider (Pakistan launch)

| Axis | Weight | Azure | Google | AWS | Whisper local |
|---|---|---|---|---|---|
| Urdu accuracy | 30% | 92 | 95 | 88 | 91 |
| Latency (ms) | 25% | 250 | 400 | 280 | 600 |
| Cost ($/min) | 15% | 0.016 | 0.024 | 0.018 | 0.005 |
| Reliability (uptime) | 15% | 99.9 | 99.95 | 99.9 | 99.5 |
| Lock-in risk | 10% | medium | medium | medium | low |
| Integration time | 5% | 1d | 1d | 2d | 1w |
| **Weighted score** | | **3.7** | **3.9** | **3.5** | **3.2** |

Google 微胜. 但敏感度分析: 如果 latency weight 从 25% 提到 35% (业务 strict 要求 < 500ms), Azure 反超.

**Decision**: 不 single-pick, **cascade**: Azure primary, Google fallback, Whisper local last-resort. 把 trade-off 从 single choice 变 architectural design.

### 2.4 Reversibility check

```
Decision: ASR provider 选哪个
- One-way 吗? No — provider 可换 (有 abstraction layer)
- Blast radius? High — production 用户调用
- Time to detect? Day 1 (latency / accuracy 立刻看)
- Recovery cost? 1 week eng to swap provider

→ Two-way door + high blast → 1-2 weeks pilot, then commit
→ 加 cascade design 把 single provider risk 进一步降低
```

### 2.5 Technical ambiguity 的 STAR (BNPL agent orchestration)

**S**: BNPL chatbot 要做 agentic orchestration. 选项: LangChain / LangGraph / Semantic Kernel / 自研.

**T**: 在 4 周内 ship MVP, 选一个 framework.

**A**:
1. **Decompose**: 已知 (4 周 deadline, 10 个 tool, 支持 multi-turn). 未知 (framework 稳定性, 中文 documentation). 假设 (我们的 use case 不需要 framework 自带的复杂 graph orchestration).
2. **Trade-off matrix**:
   - LangChain: 生态广, 但当时 stability 差, 频繁 breaking change
   - LangGraph: 表达力强, 但 learning curve
   - Semantic Kernel: 微软栈, 与 Azure 集成好
   - 自研: 灵活, 但 4 周不够
3. **Reversibility check**: 框架可换 (我们写 thin wrapper), 但 4 周 deadline 严
4. **Decide**: 自研 minimal orchestration (workflow / tool / memory 三层), 后续可替换为成熟框架

**R**: 4 周 MVP 上线, 92% routing accuracy. 6 个月后这个 minimal orchestration 成为内部 Agent Platform 雏形.

**Reflection**: Technical ambiguity 没有 "best choice", 只有 "given constraints, best choice". 选了之后立刻设计 abstraction 让 reversibility 提高.

### 2.6 Push-back dialog (技术决策被质疑)

> Tech lead: "为什么自研而不是 LangChain?"
> 你: "三个原因.
>
> One: LangChain 当时 (2024) 频繁 breaking change. 我们 4 周 deadline 不能花 1 周追新版本.
>
> Two: 我们的 use case 简单 (10 tool, 单 turn, 没 graph) — LangChain 90% 功能我们用不到, 带来 overhead.
>
> Three: 我们写 thin wrapper, 后续如果生态稳定可以替换. Reversibility 保留.
>
> 但你的 concern 我接受 — 如果 use case 复杂化, 比如要 graph orchestration, 我们 6 个月内会 reevaluate. 我们设 quarterly check-in 看是否换."

---

## ⚙️ Problem 3: Data Ambiguity — 稀疏 / 矛盾 / 噪声

### 3.1 这种 ambiguity 长什么样

- "Routing accuracy 70%, 不知道为什么"
- "Conversion rate 三个 dashboard 数字不一样"
- "用户投诉激增, 但 metric 没变化"
- "Pilot 数据看上去 promising, 但 sample 太小"

特征:
- 数据有但模糊 / 矛盾 / 不够
- 用 intuition 选 hypothesis 风险大
- 需要 systematic exploration

### 3.2 Hypothesis-driven exploration framework

**Step 1**: List all hypotheses (5-10 个), include "boring" ones
**Step 2**: For each hypothesis, list cost-to-verify
**Step 3**: Sort by cost ascending, run cheapest first
**Step 4**: 每个 experiment 设 success/fail criteria 前置
**Step 5**: Stop when explanation found, document

**关键 trap**: 不要从最贵 hypothesis 开始. MLE 第一反应是 "训模型", 经常是最贵 hypothesis. 应该 cheap 的先排除.

### 3.3 例子: BNPL routing 70% accuracy 诊断

**Hypotheses + cost**:

| H | Hypothesis | Cost to verify |
|---|---|---|
| H1 | 模型 capacity 不够 | High (fine-tune 1 周) |
| H2 | Prompt 模糊 | Low (1 天 read + manual rewrite) |
| H3 | Tool description 模糊 | Low (1 天 read confusion matrix) |
| H4 | 用户表达不清 | Low (1 天 sample real query) |
| H5 | 数据分布偏 | Med (3 天 distribution analysis) |
| H6 | Embedding model 不够好 | Med (2 天 swap embedding) |
| H7 | Routing 阈值 wrong | Low (半天 tune threshold) |

**Run order**: H7 → H3 → H2 → H4 → H6 → H5 → H1

**Reality**: H3 在 day 2 confirmed (60% mis-route 是 tool description 模糊). H1 (fine-tune) never needed.

**Saved**: 3-4 weeks of unnecessary fine-tuning.

### 3.4 Data ambiguity 的 STAR (Voice agent ASR 准确率诊断)

**S**: Voice agent 在巴西上线第二周, ASR 准确率从 95% (test data) 掉到 87% (production).

**T**: 找 root cause, fix within 1 week.

**A**:
1. **Hypotheses** + **cost**:
   - H1: Vendor 服务降级 (low cost, 1h - 检查 vendor status)
   - H2: 客户口音分布与 test set 不同 (med cost, 1 day - 分析 audio sample)
   - H3: 网络延迟导致 audio frame drop (low cost, 2h - 检查 streaming)
   - H4: 客户使用环境噪音大 (med cost, 1 day - manual listen)
   - H5: ASR model 在某 dialect 表现差 (high cost, 1 week - per-dialect eval)
2. **Run**:
   - H1 1h → ruled out, vendor normal
   - H3 2h → ruled out, no frame drop
   - H4 1 day → partially confirmed, 60% calls have moderate background noise
   - H2 1 day → confirmed, 巴西北部口音占比 30% (vs test set 5%)
3. **Fix**: 加 audio preprocessing (noise reduction) + 针对北部口音 fine-tune 一个 lightweight adapter

**R**: 87% → 93% in 1 week. Test set 重新 sample 包含北部口音.

**Reflection**: Data ambiguity 的核心是 **不要 jump to conclusion**. 列出所有 hypothesis, 按 cost 排序, 系统排除. ConvFinQA 项目教会我这个 — 用 ablation 替代直觉.

### 3.5 Push-back dialog (急于结论)

> Manager: "Just retrain the model, accuracy 一定能上去."
> 你: "Retrain 1 周成本. 我能不能先用 1 天看 confusion matrix? 如果 root cause 在 data side (e.g., tool description 模糊), retrain 也救不了. 如果 1 天后 confirm 是 model capacity, 我立刻 retrain."

90% 情况, 1 天 cheap exploration 能避免 1 周贵的 retrain.

---

## ⚙️ Problem 4: Organizational Ambiguity — 多 stakeholder 冲突

### 4.1 这种 ambiguity 长什么样

- "Ops 想自动化, Legal 要 audit trail, Product 要速度"
- "Sponsor 是 Product VP, 但 IT 才能批 deployment"
- "几个 team 各自 sponsor 一部分, 没人 own end-to-end"
- "Customer 说一件事, 实际 user 说另一件"

特征:
- 多人各自 valid 诉求
- 没有 single decision maker
- 优先级冲突
- 不是技术问题, 是 organizational

### 4.2 Stakeholder map framework

**5 column**:
| Stakeholder | 真实诉求 | 红线 (不能踩) | 妥协空间 | Veto power? |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

**关键问题**:
1. Who's the decision maker?
2. Who funds it?
3. Who blocks deployment?
4. Who uses it?
5. Who's the loser if it succeeds?

经常: decision maker ≠ funder ≠ blocker ≠ user ≠ loser. 5 个 hat 5 个人.

### 4.3 例子: BNPL chatbot 的 4 stakeholder

| Stakeholder | 真实诉求 | 红线 | 妥协空间 | Veto? |
|---|---|---|---|---|
| Product VP | UX 好, 上线快 | 不能 break user flow | 可接受 phase rollout | 部分 |
| Compliance | 不踩监管 | 任何具体 promise (额度/利率) | tier 1 FAQ 可放 | **是** |
| CS Manager | CS team 不被替代 | 复杂 case 必给 CS | 简单 FAQ 可 chatbot | 部分 |
| Risk | 不泄漏 PII | 不能 surface 用户信用数据 | 不含 PII 可 | **是** |

**Conflict**:
- Product 要快, Compliance 要 careful
- CS 要保留, Product 要自动化最大化
- Risk 要严, Product 要 surface 多

**Resolution**:
- **Tier-based design** — 把 ambiguity 显性化, 让每个 stakeholder 在自己 tier 红线内决定
- Tier 1 (通用 FAQ, no PII, no promise) — Compliance + Risk 都批
- Tier 2 (账户信息 limited) — Risk + Compliance 一起 review schema
- Tier 3 (复杂 case) — 转 CS, CS 保留 + 拿到更难 case

### 4.4 Escalation framework

当 stakeholder 冲突无法在你 layer resolve, **不要硬撑**. Escalate to 共同 owner.

**Escalation script**:
> "Hey [manager], I've talked to Product (wants speed) + Compliance (wants careful review) + CS (wants to keep human role). 三方 valid 诉求, 我 layer 无法 fully reconcile. 我提议 tier-based 方案, 但需要 [you / exec] 来确认 priority. 我下周三 10am 跟 3 方一起 review, 你能否参与做最终 call?"

**关键**: escalate 时带 proposal + invite 决策, 不是 dump 问题.

### 4.5 Organizational ambiguity 的 STAR (Voice agent 多市场 stakeholder)

**S**: Voice agent 扩展到 6 个市场, 每个市场 ops / product / compliance 各 1 个 stakeholder = 18 stakeholders.

**T**: 设计架构 + scope 让 18 个 stakeholder 都 align.

**A**:
1. Per-market stakeholder map (18 行)
2. 找共性 — LLM backbone, ASR pipeline, RAG framework 是 shared
3. 找差异 — persona, TTS voice, escalation rules, compliance prompt 是 per-market
4. **Workshop**: 每市场 1 day kickoff, 3 个 stakeholder 同时 in room, 当场决定 per-market layer
5. **Decision log**: 每个市场的决定 written down, sign-off

**R**: 6 个月内 6 个市场上线, 0 个市场上线后大改架构. **关键**: 上线前 align 比上线后 fix 快 10×.

**Reflection**: Organizational ambiguity 的最大错误是 **silo build, late align**. 反过来 — **early align, then build** — 慢一点 start, 但 finish 快很多.

### 4.6 Push-back dialog (stakeholder 让步)

> 你 to Product VP: "I hear you want to launch in 8 weeks. Compliance 需要 12 weeks for review. 选项:
> A) 12 weeks 完整 launch
> B) 8 weeks 只 launch tier 1 (Compliance can pre-approve tier 1 in 4 weeks)
> C) 8 weeks pilot 100 user, full launch 14 weeks
>
> 我建议 B — 8 weeks tier 1 是 60% volume, 你的 KPI 第一阶段满足. Tier 2/3 在 12-14 周 follow up."

**给 option, 不 dump 问题**. Stakeholder 通常感谢 trade-off framing.

---

## ⚙️ Problem 5: Outcome / Metric Ambiguity — 成功标准没定义

### 5.1 这种 ambiguity 长什么样

- "Increase efficiency"
- "Improve customer experience"
- "Reduce cost"
- "Make it better"
- "Be like ChatGPT but for our business"

特征:
- 没 specific metric
- 没 baseline
- 没 threshold
- 没 measurement plan

### 5.2 KPI Lock framework

**4 step**:

1. **Convert vague to specific**: "Efficiency" → "Tickets per hour" or "Cost per ticket" or "First-call resolution rate"?
2. **Establish baseline**: 当前 number 是多少?
3. **Set threshold**: 多少算 success? "10% improvement", "20% improvement", "match human"?
4. **Define measurement**: 怎么 measure? 谁 collect? 多频?

### 5.3 Reference-point framing

如果客户答 "I don't know", 给 reference:

> "Let me give you 3 reference points so you can decide:
>
> (a) **Consumer search engine** — wrong result annoying, retry free. Acceptable error 5-10%.
> (b) **Credit decision** — wrong call has financial + regulatory impact. Acceptable error < 1%.
> (c) **Medical diagnosis** — wrong call life-threatening. Acceptable error < 0.01%.
>
> 你的 use case 落在 spectrum 哪里?"

客户通常能 anchor 到某点, 然后 lock metric.

### 5.4 例子: BNPL chatbot KPI lock

**初始**: "Improve customer support."

**Discovery**:
- Specific? → "Reduce ticket resolution time" or "Increase deflection rate"? 客户选 deflection rate.
- Baseline? → 当前 0% (无 chatbot). 客户原目标 50%.
- Threshold? → 客户答 "as high as possible". 反问 "如果 50% 就 done, 60% 是 stretch, 70% 是 stretch goal?" 客户接受.
- Measurement? → Daily dashboard, 周三 weekly review.

**Lock**: 50% deflection in 3 months as success, 60% as stretch, 70% as stretch goal. Measured daily, reviewed weekly.

**Result**: 上线 3 个月达到 65% (between target and stretch). 双方 happy.

### 5.5 Outcome ambiguity 的 STAR (Internal Agent Platform metric lock)

**S**: 做 Internal Agent Platform, leadership 问 "platform 算 success 的标准是什么?"

**T**: 把 vague "make agents easier" 锁成 measurable.

**A**:
1. **Reference points**:
   - Internal infra usually measured by # of teams adopting
   - Or by build cost reduction
   - Or by quality of agents built
2. **Stakeholder workshop** (leadership + 5 种子 team lead)
3. **Lock**: 6 个月内 5 → 10 teams onboard, build time per agent 50% reduce, 0 P0 incident
4. **Measurement plan**: monthly adoption review, per-team survey on build time, on-call rotation tracking incident

**R**: 6 个月 5 → 14 teams (140% of target), avg build time -65%, 0 P0. Stretch goals 都过.

**Reflection**: Outcome ambiguity 是 FDE 工作最常见. 把 vague 锁成 measurable 是 FDE core skill. 没 lock 的 outcome = 6 个月后双方对 "成功" 定义不一致 = 失败.

### 5.6 Push-back dialog (客户拒绝 lock metric)

> 客户: "I don't want to commit to a specific number. Just do your best."
> 你: "I hear you. But 'best' 不可 measurable, 6 个月后我们无法 evaluate 是否成功. 我提议这样:
>
> 我提一个 number based on industry benchmark, 你 push back. 比如 50% deflection rate in 3 months. 你觉得 ambitious / conservative / 完全不对?
>
> 如果 ambitious → 我调整 architecture more aggressive
> 如果 conservative → 我们 lock 60%
> 如果不对 → 你 propose 一个 alternative metric
>
> Lock metric 不是 contract, 是 alignment tool. 我们 quarterly review 可以 update."

90% 情况, 客户能 react 到一个 strawman number 比 "from scratch propose" 容易很多.

---

# Part 3 · 串起来看

这 5 种 ambiguity 是 FDE 工作的 5 个不同维度:

1. **Goal ambiguity** — "客户不知道要啥" — 用 discovery 帮客户拆
2. **Technical ambiguity** — "多个架构都行" — 用 trade-off matrix + reversibility
3. **Data ambiguity** — "数据不清" — 用 hypothesis-driven 系统排除
4. **Organizational ambiguity** — "stakeholder 冲突" — 用 stakeholder map + escalate
5. **Outcome ambiguity** — "成功没定义" — 用 KPI lock + reference points

**核心 mental model**: 每次面对 ambiguity 先 **classify type**, 再选 framework. 不要把所有 ambiguity 当一类处理.

---

## 必问 clarifying questions

如果 HM 给一个具体场景问 "你会怎么 handle", 你可以反问 clarifying:

**1. 哪种 ambiguity?**

> "你描述的场景里, ambiguity 是关于 [goal / technical / data / org / outcome], 还是几种混合?"

**2. Reversibility**

> "这是 one-way 还是 two-way door? 我的 framework 不一样."

**3. Stakeholder count**

> "牵涉几个 stakeholder? 有没有 single decision maker?"

**4. Timeline pressure**

> "Timeline 是 days / weeks / months? 短 timeline 我 prioritize ship-and-measure, 长 timeline 我 invest 更多 discovery."

**5. Blast radius**

> "Wrong call 的 blast radius? 单一客户 vs 多客户 vs 公司层面? 影响 scoping 投入."

---

## 5 步框架 (回答这道题的 60 秒结构 + STAR)

| 段 | 时长 | 内容 |
|---|---|---|
| Setup | 15s | "FDE 工作 90% 在 ambiguity 里, 我有 D·D·D·V framework" |
| Framework | 20s | Diagnose type / Decompose / Decide by reversibility / Validate |
| Story setup | 30s | "举一个 example — Indonesia tier 3 refund" |
| Story action | 60s | 详细讲 4 个 D + 数据 |
| Story result | 20s | 70% throughput, 0% risk, 6 weeks |
| Takeaway | 15s | "Decomposition is hypothesis, not commandment" |

Total: ~2.5 min. HM 通常会 follow up.

---

## 简历专属 reframe — MANY STAR stories

### STAR 1: Indonesia Refund Tier (★ PRIMARY)

**Use for**: Goal ambiguity + Outcome ambiguity (most behavioral questions)

**S**: Ops "auto refund 下季度"
**T**: 不完整信息下 commit conditionally
**A**: 3-tier decomp by reversibility, 2-week pilot, data-driven reframe
**R**: 70% throughput, 0% risk, 6 weeks; tier 3 0 wrong refund

**FDE framing**: "Decomposition is hypothesis. Pilot validates. Data reframes ask."

### STAR 2: Pakistan ASR Provider (Technical Ambiguity)

**S**: 4 weeks deadline, ASR vendor 选择 (Azure / Google / AWS / Whisper)
**T**: Choose without single source of truth
**A**: Trade-off matrix, 3-day quick eval, cascade design instead of single-pick
**R**: Pakistan launch on time, 0 ASR incident month 1

**FDE framing**: "Don't pick the best. Design architecture so wrong choice is reversible."

### STAR 3: BNPL Routing 70 → 92% (Data Ambiguity)

**S**: Launch month 1, routing 70%, 不知道 why
**T**: Diagnose root cause without disabling
**A**: Hypothesis list ordered by cost, confusion matrix Day 2 → H3 confirmed (tool desc 模糊), rewrite + RAG discovery
**R**: 70 → 92% in 6 weeks. Saved 3-4 weeks of unnecessary fine-tuning.

**FDE framing**: "Cheap hypotheses first. MLE wants to train, FDE looks at data first."

### STAR 4: BNPL 4-Stakeholder Conflict (Organizational Ambiguity)

**S**: Product / Compliance / CS / Risk 4 个 stakeholder, 优先级冲突
**T**: Design 满足 4 方红线
**A**: Stakeholder map (5 col), tier-based design (tier 1/2/3 各 stakeholder 红线内决定)
**R**: 0 compliance incident, CS satisfaction 提升 (拿到 high-value case), Product VP renew project

**FDE framing**: "Make ambiguity explicit, help stakeholders reach consensus, don't unilateral decide."

### STAR 5: ConvFinQA Ablation (Data Ambiguity + Honesty)

**S**: 6-stage pipeline ablation, 2 stages negative lift
**T**: Diagnose which stage really matters, decide on publication
**A**: Per-stage ablation, publish all results including negative
**R**: Paper accepted with reviewer praise for honesty; principle transferred to production retros

**FDE framing**: "Ablation is the systematic way to handle data ambiguity. Honest reporting builds trust."

### STAR 6: Voice Agent 7-Market Stakeholder Workshop (Organizational)

**S**: Voice agent 扩展 6 个市场, 18 个 stakeholder
**T**: Align 18 个 stakeholder 不 silo build then late align
**A**: Per-market 1-day kickoff workshop, 3 stakeholder in room, shared/per-market layer 设计
**R**: 6 markets 6 months, 0 markets 上线后大改

**FDE framing**: "Early align then build, not silo build then align. 10× faster."

### STAR 7: Internal Agent Platform KPI Lock (Outcome Ambiguity)

**S**: Leadership "platform success criteria?"
**T**: Vague → measurable
**A**: Reference points + workshop, lock teams adoption count + build time + incident count
**R**: 5 → 14 teams (140% target), -65% build time, 0 P0

**FDE framing**: "Lock metric 不是 contract, 是 alignment tool. Without it, 6 月后双方定义不一致."

### STAR 8: Wrong Call I Made (Show Vulnerability)

**S**: Voice agent multi-region 我初始 scope 成 "translate prompts per language, ship"
**T**: Multi-market localization
**A** (wrong): 没 scope cultural review
**R** (wrong): 上线后发现债务沟通文化差异 (Thailand 礼貌, Korea 直接), 4 周 redo persona + escalation logic
**Lesson**: "Localization for AI > translation. 我现在 scope multi-market 必包含 cultural review."

**FDE framing**: HM 想听一个真实 wrong call. 这是关键 trust signal. Don't fake humble — show genuine learning.

---

## 5 follow-ups (HM 会追问)

**Q1**: "What if your decomposition turns out wrong — tier 3 actually fine to automate quickly?"

**A**:
> "Then I learn and reshape. 2-week pilot 是专门 stress-test 我的 assumption. 如果 pilot 显示 tier 3 difficult case 0% wrong, 我会 accelerate.
>
> **Decomposition is hypothesis, not commandment**. Eval 是 truth. 我 explicitly 留 pilot 检测我自己 wrong 的可能."

**Q2**: "What if ops got angry at the pushback?"

**A**:
> "They were initially 不爽 — 'we asked 8 weeks, 你 12 weeks for tier 3'.
>
> Reframe 帮助: 'I want to give you the **right answer faster, not the wrong answer on time**'. 加上 cost-of-wrong-call 估算 (projected 8% wrong rate × $X per refund × monthly volume = $Y monthly liability). 数字 diffuse emotion.
>
> Ops 最终 thank me. 后来跟 my manager 反馈 'Gao 是少数 push back 但能让我感谢的 vendor.'"

**Q3**: "How do you know when 'decompose more' becomes procrastination?"

**A**:
> "Pragmatic rule: **decomposition > 10% of total project timeline = over-decomposition**.
>
> 12-week project, > 1 week scoping 是 procrastination. **At some point, ship small piece and learn from data**.
>
> 我 prefer over-decompose by 1 day 不是 under-ship by 4 weeks. Two-way door 决定可以 quick ship + measure; one-way door 才需要长 scoping."

**Q4**: "Have you ever made a wrong call under ambiguity?"

**A** (use STAR 8 above):
> "Yes. Voice agent multi-region rollout 我 initial scope 是 'translate prompts per language, ship'.
>
> Turns out 债务沟通文化差异巨大 — Thailand 礼貌 framing 是 polite, 直接说 'pay your debt' 是 rude. Korea 反过来, 礼貌过头反而 less credible.
>
> 我 redo persona + escalation logic per market, cost 4 extra weeks.
>
> Lesson: **'Localization' for AI > translation**. Cultural review 现在是 multi-market project 的 scope item, not optional."

**Q5**: "How do you balance speed vs quality under ambiguity?"

**A**:
> "By **reversibility classification**:
>
> - Two-way doors → speed (ship + measure)
> - One-way doors → quality (invest in scoping)
>
> 我 explicitly tag every decision at scoping time. **Most decisions are two-way and can be reversed cheaply** — over-optimizing quality on those is waste.
>
> 但 one-way doors (e.g., tier 3 refund, production model swap, pricing) — 我 explicitly slow down 投资 scoping. 错了 12 个月才发现的 decision 不应该 1 周决定."

---

## ❌ 易错点 (top 10)

1. **No structured framework** — 纯 narrative, 没 framework signal
2. **Pure speed or pure caution** — 没 nuance
3. **Story 没 metrics** — 70% / 0% / 6 weeks 数字必须有
4. **Blame stakeholder** for ambiguity — 显得 immature
5. **Solo decide** 不 validate — 显示 silo 倾向
6. **Generic story** — 听起来 rehearsed
7. **Doesn't tie to FDE** — 没 connect 到 deployment ambiguity
8. **Push back without data** — 显得 "你不愿意做"
9. **不承认 wrong call** — 显示不 self-aware
10. **没 reversibility 区分** — One-way / Two-way 不 distinguish

---

## ✅ 加分项 (top 10)

1. **D·D·D·V framework** explicit, named, reusable
2. **5 types of ambiguity** classification (goal / technical / data / org / outcome)
3. **Reversibility classification** (one-way vs two-way doors)
4. **"Decomposition is hypothesis"** awareness
5. **Specific metrics** (70% / 0% / 8 weeks)
6. **Acknowledge wrong call** with genuine learning
7. **Tie to FDE day-to-day** (deployment ambiguity is universal)
8. **Business-language reframe** ("right answer faster vs wrong on time")
9. **Stakeholder validation** explicit
10. **Cheap hypothesis first** in data ambiguity

---

## 一句话总结

> **Handle ambiguity 不是 "我能 ship 没 spec 的项目", 是 "我能 classify ambiguity 5 类, decompose 成已知/未知/假设, 按 reversibility 决策, 用 stakeholder + data validate"**.
>
> D·D·D·V framework + reversibility classification + cheap hypothesis first + early stakeholder align = senior FDE.

---

## Cheat Sheet (印 1 页)

```
D·D·D·V framework:
  Diagnose      — 哪种 ambiguity (goal/tech/data/org/outcome)
  Decompose     — 已知/未知/假设
  Decide        — by reversibility (one-way slow, two-way fast)
  Validate      — stakeholder + pilot data

5 ambiguity types + 应对:
  Goal       — 客户不知道想要啥     → Discovery 帮拆
  Technical  — 多架构 viable        → Trade-off matrix + reversibility
  Data       — 稀疏/矛盾/噪声       → Hypothesis-driven, cheap first
  Org        — Stakeholder 冲突     → Stakeholder map + escalate
  Outcome    — 成功没定义           → KPI lock + reference points

Reversibility matrix:
  One-way + high blast → 8-12 wk scoping (tier 3 refund)
  One-way + low blast  → 2-4 wk scoping (single-customer change)
  Two-way + high blast → 1-2 wk pilot then scale (multi-market)
  Two-way + low blast  → ship + measure same day (prompt tune)

5-question discovery (Goal ambiguity):
  1. The ONE metric in 6 months?
  2. Current baseline?
  3. Who's the loser if we succeed?
  4. What outcome makes us look stupid?
  5. What does week-1 success look like?

Hypothesis order (Data ambiguity):
  - List 5-10 hypotheses including "boring" ones
  - Order by cost-to-verify (ascending)
  - Run cheapest first
  - Stop when explanation found
  ❌ Don't start with "let's retrain" (most expensive usually)

Stakeholder map (Org ambiguity, 5 col):
  Stakeholder | 真实诉求 | 红线 | 妥协空间 | Veto power

Reference points (Outcome ambiguity):
  Consumer search (5-10% error OK)
  Credit decision (< 1% error)
  Medical (< 0.01% error)

8 ready STAR stories:
  1. Indonesia refund tier (★ goal + outcome)
  2. Pakistan ASR cascade (technical)
  3. BNPL routing 70→92% (data)
  4. BNPL 4-stakeholder (org)
  5. ConvFinQA ablation (data + honesty)
  6. Voice agent 7-market workshop (org)
  7. Internal Platform KPI lock (outcome)
  8. Multi-region wrong call (vulnerability)

Phrases to use:
  "Decomposition is hypothesis, not commandment"
  "Right answer faster, not wrong on time"
  "Two-way door → ship + measure"
  "Cheap hypothesis first"
  "Make ambiguity explicit, help stakeholders consensus"

Phrases to NEVER use:
  "I just ship"
  "I ask my manager"
  "I research first" (alone, no concrete)
  "It depends" (no follow through)

Push-back dialog templates:
  Customer impatient → "Sketch + flag 3 assumptions, or confirm first?"
  Vague KPI → "Reference 3 industry anchors"
  Solo lock metric refused → "I propose strawman, you push back"
  Stakeholder conflict → "Give option A/B/C with trade-offs"

5 follow-ups ready:
  Q1: Decomp wrong? → Pilot stress-tests, learn + reshape
  Q2: Stakeholder angry? → Reframe + cost data
  Q3: Decompose vs procrastinate? → 10% rule
  Q4: Wrong call story? → Multi-region localization (cultural)
  Q5: Speed vs quality? → Reversibility classification

Red lines:
  - No framework signal
  - No metrics in story
  - No wrong call acknowledged
  - No reversibility distinction
  - Solo silo decision
```
