## Q05 · 你和客户意见不合并坚持了立场

> "Tell me about a time you disagreed with a customer or stakeholder and stood firm. What was the disagreement, how did you navigate it, and what was the outcome?"

**Round**: Behavioral (30-45 min, hiring manager 或 cross-functional)
**出处**: Exponent 2026 FDE Guide · 公司: Anthropic / OpenAI / Palantir / Databricks 高频. 变体: "tell me about a time you pushed back on a customer" / "describe a disagreement where you didn't back down" / "when have you said no to a powerful stakeholder"

---

## 📖 术语速查 (本题用到的)

> 这题是 judgment vs stubbornness 的故事 — 涉及大量决策方法论术语 + LLM / 量化 / 监管术语.

### 决策方法论 ⭐ 这题的核心

| 术语 | 解释 |
|---|---|
| **Hill worth dying on** ⭐ | 值得死磕的山头. Principle-grounded + one-way door + 高 blast radius. Senior FDE 一年只 stand firm 2-3 次. |
| **Principle-grounded vs ego-grounded** ⭐ | 立场基于原则 (数据 / 监管 / 安全 / 用户) 还是基于自我. Principle 是 strength, ego 是 red flag. |
| **Steel-man** ⭐ | 把对方最强 argument 复述一遍, 确认 understand. 跟 strawman (扎稻草人) 相反. |
| **Reversibility (one-way vs two-way door)** ⭐ | 决策可逆性. One-way = 错了高代价 (e.g., 改 base model 要全部 retrain). Two-way = 错了易撤. |
| **Blast radius** | 错误影响范围. 单 team vs 多用户 / 美元 / 监管. |
| **A/B pilot + abide by data** | 对照试验 + 双方承诺听数据. "Pilot data resolve, not who's right". |
| **Conditional commitment** | 条件承诺. "If pilot shows X < threshold, I'll back down". 让 stand firm 不变 stubborn. |
| **Confirmation bias** | 确认偏误. 见 contradictory data 先找 alternative explanation 而不是 update. |
| **Admit partial loss** | 承认部分失败. Stand firm 赢了之后 admit 哪部分对方对的, 维持关系. |
| **Trust bank** | 信任银行. Stand firm 在 trust bank 高时 spend 一次, 然后立刻 deposit 回去. |

### 5 种 ego variants (要警惕的)

| 术语 | 解释 |
|---|---|
| **Sunk cost** | "spent 4 weeks on this, can't change now". |
| **Public commitment** | "Told VP this, can't reverse now". |
| **Identity-grounded** | "I'm the ML expert, you're ops, my call". |
| **Stubborn loop** | "They keep pushing back so I keep digging in". |
| **Ego-as-principle** | "Standardize" when really "I want to build". |

### LLM / 量化技术

| 术语 | 解释 |
|---|---|
| **Llama 2 7B / 13B** ⭐ | Meta 开源 LLM. 7B 跟 13B 参数量差近 2×, inference 成本差更大 (~3×). 13B 更聪明但贵. |
| **INT8 quantization** ⭐ | 把模型从 FP16 量化到 INT8, 显存减一半. 13B INT8 cost 只比 7B FP16 高 1.4× (不是 3×). |
| **FP16** | Half-precision floating point. LLM 训练 / 部署常用. |
| **Hallucination rate** | 模型编造事实的比例. 7B 在金融数字上 4.2%, 13B 1.5%, 差距显著. |
| **SFT (Supervised Fine-Tuning)** | 监督微调. Base model 升级 = SFT 全部 retrain. |
| **DPO (Direct Preference Optimization)** | 直接偏好优化. 同样 base model 改了要 retrain. |
| **Retrain cost** | 重训成本. Base model swap 后 SFT 50k dialog + DPO 20k pair 全 redo, $200k + 8 weeks. |
| **vLLM** | 高吞吐 LLM inference engine. INT8 latency 280ms vs FP16 320ms. |
| **Latency (推理延迟)** | 单次推理耗时. Voice agent 实时性关键. |
| **Throughput** | 单位时间处理量. INT8 throughput 高于 FP16. |

### 业务 / 监管

| 术语 | 解释 |
|---|---|
| **OJK** | 印尼监管. 2023 罚款过 fintech RMB 8M = 类似 case 的 precedent. |
| **OJK precedent** | 监管前例. 数据论证里强力的引用. |
| **Regulator exposure** | 监管暴露. 4% hallucination × 数百万 monthly call = 数万 wrong info → 监管行动. |
| **Hidden cost** | 隐藏成本. 7B 便宜的 inference 是 visible, regulator fine + retrain 是 hidden. |
| **Industry precedent** | 行业先例. "同类 fintech voice agent 大多 7B" 是 weak argument 之一. |
| **Internal benchmark** | 内部基准测试. 1k labeled financial dialog 自己 eval. |
| **Statistical significance** | 统计显著性. CI 不重叠 = 显著差异. |

### 沟通 / 升级

| 术语 | 解释 |
|---|---|
| **Stand firm** | 坚持立场. 跟 stubborn 区分 — selective + principle-grounded. |
| **Back down** | 让步. 不是 weakness, 是知道 hill not worth dying on. |
| **Push back** | 反推. 跟 reframe / acknowledge 配合用. |
| **Escalation ladder** | 升级阶梯. Peer → joint manager 1:1 → written objection. |
| **Joint manager 1:1** | 双方 manager 一起开会. "Not over their head, this exceeds peer authority". |
| **Counter (counter-argument)** | 反驳论证. |
| **Skip-level** | 越级反馈. Ops director 跟 my manager 的 manager 说. |

### 工程 stack

| 术语 | 解释 |
|---|---|
| **LangGraph** | LangChain 出的 agent orchestration framework. 生态广. |
| **Agent orchestration framework** | Agent 编排框架 — 多 tool + memory + planning 组合. |
| **Memory layer (agent)** | Agent 记忆层. Short / long / shared memory. |
| **Pluggable backend** | 可插拔后端. Memory layer 给 SQL or vector 选择, 不强制. |
| **Vector DB** | 向量数据库. Semantic search 适用. |
| **Pinecone / Qdrant / pgvector** | 三个主流 vector DB. pgvector 是 Postgres 插件. |

### 反 pattern

| 术语 | 解释 |
|---|---|
| **Tattling** | 打小报告. Escalation too early 给人这种感觉. |
| **Ass-covering** | 自保. Written objection 既是 self-protection 也是 learning record. |

---

## 这道题在考什么

这是 FDE 题里 **judgment 跟 stubbornness 区分度最高的一道**. 表面问坚持, 实际筛 6 件事:

- **Judgment, not stubborn** —— 你坚持的是 principle 还是 ego. Principle-based push back 是 strength, ego-driven 是 red flag
- **Data 替代 opinion** —— 你 ground 在数据 / 监管 / 安全, 还是 ground 在 "我觉得"
- **Customer empathy maintained** —— 坚持立场过程中你 lose customer relationship 没有
- **Escalation maturity** —— 你 escalate 是 systematic 还是 cry for help
- **Outcome accountability** —— 你 stood firm, 然后结果对不对? 错了你认不认
- **When to back down** —— Senior FDE 知道哪些 hill 不值得 die on, 不是 everything

**没说出口的红线**:

- "我跟 customer 经常 disagree, 我都坚持立场" → 显得 difficult to work with
- "他们 wrong, 我 right" → no nuance, no humility
- "We had to escalate to VP" → 显得 escalation 是第一选项
- "I held my ground for 3 weeks" → 长时间僵持 = leadership failure
- 没有 "事后看我对吗" reflection → 你 confirm bias, 不 self-evaluate
- 没有 example of when you backed down → 显得不知 trade-off

---

## 完美答案架构 (Layered Response)

8 段结构, total ~4-5 分钟:

| # | 层 | 时间 | 这层该说什么 | 开口句 |
|---|---|---|---|---|
| 1 | **Context + relationship** | 20s | 哪个 customer, 我的角色, 信任基线 | "Indonesia ops director, 6 months working together, good trust..." |
| 2 | **Disagreement essence** | 20s | 具体什么 disagreement, both sides | "They wanted Llama 7B baseline; I wanted Llama 13B with quantization..." |
| 3 | **Why I stood firm (principle, not ego)** | 30s | 你坚持的 ground 是什么 (data / 监管 / 安全) | "I grounded in 3 things: hallucination rate, regulator exposure, irreversibility..." |
| 4 | **What I considered before standing firm** | 30s | 你 explicitly 看过 their side 才决定 stand | "I steel-manned their case: cost saving $X, training speed 2×, smaller model is industry default for their bracket..." |
| 5 | **The actual conversation** | 60s | 具体怎么 push back, dialog | "First meeting I lost — they had VP backing. Second meeting I came with pilot data..." |
| 6 | **Pivot / escalation moment** | 45s | Stuck 怎么 unstuck, when to escalate | "After 2 meetings stuck, I proposed 2-week A/B pilot, both sides commit to abide by data..." |
| 7 | **Outcome (incl. partial wins / losses)** | 30s | 结果 + 你对/错 reflection | "Pilot data sided with my position 70%, ops side 30% (their concern on cost was valid)..." |
| 8 | **What I'd back down on (for balance)** | 20s | 这是关键 — 对比 a time 你 backed down | "Compare: similar dispute on inference framework choice (LangChain vs custom) — there I backed down because reversibility was high..." |

Total: ~4-5 min. 8 段 必须有 段 8 (back down example), 否则显得 stubborn.

---

## 详细回答 (Sample Monologue) — 可以照背

> "我讲印尼 voice agent base model 选择那次 disagreement, 因为它是我 'stood firm' 最 complete 的一次, 包括我自己 wrong 的部分.
>
> **Context**: 印尼 ops director + 我的 manager + 我, 三方 review voice agent base model choice. 我跟 ops 合作 6 个月, trust 基础好. 这次 disagreement 是关于 base LLM —— ops director (有 backing from product VP) 想用 Llama 2 7B, 我推荐 Llama 2 13B with INT8 quantization.
>
> **Disagreement essence**:
>
> Ops director 的 argument (legitimate):
> - Cost: 7B inference cost 3× cheaper
> - Training speed: 7B fine-tune 2× faster, 我们 multi-market rollout 紧
> - Industry precedent: 同类 fintech voice agent 大多 7B
>
> 我的 argument:
> - Hallucination: 7B 在金融数字上 hallucination rate 4-5%, 13B 在我们 internal benchmark 上 1.5%
> - Regulator exposure: 7B 4% × monthly calls 数百万 = 数万 wrong-info incidents, OJK threshold 必触发
> - Irreversibility: 选 7B 之后训了 SFT, 想升 13B = 全部 retrain ($200k + 8 weeks)
>
> 第一次会, 我 lost. Ops director 有 VP backing, 加上 cost argument 是 hard concrete number. 我说 'hallucination rate' 是 abstract. 我承认我 communicate 失败.
>
> **Why I stood firm — 3 grounds**:
>
> **Ground 1 — Regulator exposure not negotiable**: 印尼 OJK 2023 罚款过一家 fintech 类似 case, RMB 8M. 4% wrong info 在我们 scale 下 monthly 会触发. 这是 binary, 不是 trade-off.
>
> **Ground 2 — Irreversibility**: Base model swap 是 one-way door (SFT/DPO 全 retrain). 决定错了 8 周才能 undo. Hill 值得 die on.
>
> **Ground 3 — Hidden cost**: 7B cheap inference 是 visible cost, regulator fine + retrain 是 hidden cost. 我的 job 是 surface hidden cost 让 decision maker know full picture.
>
> 这 3 个 ground 不是 ego, 是 principle. 区别在 — 如果数据 prove 7B hallucination rate < 1.5%, 我 back down.
>
> **What I considered before standing firm**:
>
> 我 steel-manned ops side:
> - Cost 是 real concern, 不是 dismissable
> - Training speed 影响 multi-market timeline, ops Q-end target
> - Industry precedent 不是 weak argument
>
> 我也 considered: 如果我 wrong (i.e., 13B hallucination 也 4%), I lose credibility 6 months work.
>
> Steel man + risk-of-being-wrong analysis 之后我仍然 believe 我 right. 这才是 stand firm 不是 cry wolf.
>
> **The actual conversation**:
>
> 第二次会, 我 prep 2 周.
>
> 我 came with:
> - **Internal benchmark**: 1k labeled financial dialogs, 7B vs 13B hallucination, 7B 4.2% (95% CI 3.8-4.7%), 13B 1.5% (CI 1.2-1.9%). Statistically significant.
> - **Cost comparison full picture**: 7B inference $X/year. 13B INT8 inference $X × 1.4 (not 3×). Plus 7B regulator-fine 期望 $80k-$500k. Plus 7B retrain cost if we have to swap.
> - **OJK precedent slide**: 2023 fintech RMB 8M fine, similar use case.
> - **Alternative**: 13B INT8 quantization. Quality close to FP16 13B, cost only 1.4× 7B.
>
> 开场我 acknowledge their concern: 'Your cost concern is valid. 我之前没 surface hidden cost, 这次我把全图 show 一下.'
>
> 然后 walk through 数据. 30 分钟.
>
> Ops director quiet 1 分钟. 然后 ask: '13B INT8 你 confident 不会 latency 退化?'
>
> 我: 'INT8 我跑过 vLLM 部署, latency 280ms vs FP16 320ms. 实际更快, 因为 INT8 throughput 高.'
>
> Ops director: 'OK. 我重新跟 VP align.'
>
> **Pivot / escalation moment**:
>
> 实际上我没 escalate. 但我 prep 了 escalation plan:
>
> - If Ops director 仍然 push 7B, I propose 2-week A/B pilot in 1 market (Vietnam), 两边 commit abide by data. Data wins, not opinion.
> - If pilot 显示 13B 没显著 advantage, I back down.
> - If pilot 显示 7B regulator risk, ops back down.
>
> 这种 'pilot + abide by data' 是 senior disagreement 解决方式 — 不是 'who's right', 是 'let data resolve'.
>
> **Outcome — incl. my wrong part**:
>
> - 13B INT8 上线, 印尼 hallucination 1.5% (跟 benchmark 一致), 0 OJK incident in 12 months
> - Cost: 1.4× 7B, 不是 3×, 因为 INT8
> - 但 — **我也 partial wrong**. Ops director 的 training speed concern: 我假设 13B fine-tune 2× 慢但 acceptable. 实际上印尼 SFT 50k dialogs, 13B 花 5 days vs 7B 2 days. Multi-market rollout 我们最初计划 6 个月, 因 base model 选择部分 stretch 到 8 个月. Ops director Q-end target 因此 miss 5%. 我事后认这一点.
>
> **What I'd back down on (compare)**:
>
> 同期我有另一个 disagreement, **我 backed down**. 选 agent orchestration framework — LangGraph vs 自研. 我推自研, my manager 推 LangGraph (生态广, 团队学习曲线低). 我跟 manager debate 1 周后 backed down.
>
> Why backed down:
> - Reversibility: 框架可换, abstraction thin, swap cost ≤ 2 weeks. **Two-way door**.
> - Blast radius: low. Wrong choice 影响开发速度, 不影响 customer outcome.
> - My ego ≠ principle: 我推自研部分是 'I want to build', 不是纯 technical 必要. Honest 自查 confirm.
>
> 6 个月后, LangGraph 我们用得 OK, 选 manager 推的是 right call.
>
> **Stand firm 的 mental model**:
> - Hill 值得 die on: principle-grounded (data / 监管 / 安全 / 用户) + one-way door + 错了 high blast radius
> - Hill 不值得 die on: ego-grounded ('I want to build' / 'my style') + two-way door + 错了 low blast radius
>
> 区分这两类是 senior FDE signature. **Junior 把每个 disagreement 当 hill to die on. Senior 一年 stand firm 2-3 次, 每次都 worth**."

---

## Gao Xin 简历专属 STAR 模板

至少 1 完整 STAR (Indonesia base model), 2 alternate.

### ★ STAR 1: Indonesia Base Model 7B vs 13B (★ PRIMARY)

**S** (Situation):
> "印尼 voice agent base model 选择. Ops director (VP backing) 想 Llama 2 7B (cost cheap, training fast, 同行业 precedent). 我推 Llama 2 13B INT8 quantization (hallucination 低, regulator 安全). 我跟 ops 合作 6 个月, trust 基础好."

**T** (Task):
> "在 disagreement 中坚持 principle-grounded position (regulator exposure + irreversibility), 同时 maintain relationship + 不 ego-drive."

**A** (Action):
1. **First meeting lost**: 我 communicate 失败, hallucination 是 abstract, cost 是 concrete. Ops 有 VP backing.
2. **Steel-man their side**: cost real, training speed real, industry precedent real
3. **Self-check**: 我的 stand firm 是 principle 还是 ego? Confirm principle (regulator + irreversibility + hidden cost)
4. **Prep 2 weeks**:
   - Internal benchmark 1k labeled financial dialog 7B vs 13B
   - Hallucination 7B 4.2% vs 13B 1.5%, statistically significant
   - Cost full picture: 13B INT8 是 1.4× 不是 3×
   - OJK precedent slide
5. **Second meeting**:
   - Acknowledge cost concern first ("hidden cost 我之前没 surface")
   - Data walk-through 30 min
   - Address INT8 latency concern with vLLM 部署 evidence
6. **Escalation plan prep (didn't need)**: A/B pilot Vietnam 2 weeks, both sides commit abide by data

**R** (Result):
- 13B INT8 上线, hallucination 1.5%, **0 OJK incident in 12 months**
- Cost: 1.4× 7B (within budget)
- **Partial loss admitted**: training time 5 days vs 2 days, multi-market timeline stretch 6 → 8 months, ops Q-end miss 5%
- Ops director 仍 trust 我 (relationship intact)
- 这个 stand firm decision 我事后 confirm 仍然 right call, but acknowledge cost

**Vulnerability line**:
> "我 wrong part: training time 我 underestimate. 我 assume 'acceptable', 实际 stretch timeline 让 ops Q-end miss 5%. 我事后 owe ops director: 'you were right that training time would cost us, I underestimated impact'. 这种 admit partial loss 在 stand firm 之后是 trust 维持的关键. 不 admit = next disagreement 你 credibility 损耗."

---

### STAR 2: BNPL Chatbot Output Schema (Compliance vs Product UX) — Alternate

**S**: BNPL chatbot 上线 month 3, Product VP 想 chatbot output 更 conversational ("more natural language, less structured"). 我推 keep strict output schema (boolean / enum / structured fields). Disagreement 是 'conversational UX vs compliance safety'.

**T**: Stand firm on strict schema even if Product VP push for conversational.

**A**:
1. **Steel-man Product side**: conversational UX 是 real user benefit, structured 感觉 robotic
2. **My ground**: chatbot output 上 free-form 之后, LLM 自由扩展 surface area, compliance 风险高 (BNPL VP case 已 documented)
3. **Data**:
   - 50 sample test, free-form output 32% triggered specific 数字 surface (vs structured 0%)
   - Compliance team 已 review, structured 是 required
   - Regulator precedent: RMB 8M fine for similar fintech
4. **Alternative**: hybrid — structured at compliance-critical surface (额度 / 利率 / promise), conversational at general FAQ surface
5. **Delivery**:
   - 1v1 with VP, frame: "we both want best UX, I want to share compliance findings"
   - Walk data 30 min
   - Address VP "robotic" concern: hybrid keeps conversational on 80% surface
6. **VP accepted hybrid**

**R**:
- Hybrid schema ship, conversational 80% / structured 20%
- User satisfaction +12% (hybrid better than pure structured)
- **0 compliance incident** in 18 months
- VP 后来 quarterly review: "应该 Gao 跟 compliance team 一起 review every new tool from day 1"
- 我变成 product-side compliance trusted advisor

**Vulnerability**:
> "我 sub-mistake: 我初始 framed disagreement 成 'safety vs UX' (binary). VP defensive 因为 framing 让他 sound like 'against safety'. 后来 reframe 成 'how to ship BOTH safety AND UX', 找到 hybrid. Reframe binary → both 是 senior dispute resolution skill."

---

### STAR 3: Internal Agent Platform Memory Layer Storage Backend — Alternate (Lost This One)

**S**: Internal Agent Platform 设计 Memory layer, Risk team lead 想 SQL backend (their existing infra), 我推 vector DB (semantic search 更适合 agent memory).

**T**: Initially stand firm on vector DB, but eventually back down on Risk team's specific use case.

**A**:
1. **My initial position**: vector DB 是 agent memory 行业 standard, semantic search 比 SQL exact match 适合 agent retrieval
2. **Steel-man Risk side**: SQL is their existing infra, ops familiarity, faster integration, their use case is more structured (rule-based memory)
3. **Self-check**: 我的 stand firm 是 principle 还是 ego? Confirm partially ego ("I want to standardize")
4. **Pivot**: 我 backed down, design Memory layer with **pluggable backend** (SQL or vector). Risk team uses SQL, other teams use vector.
5. **6 months later**: Risk team's use case grew (semantic recall needed), they migrated to vector by themselves

**R**:
- Memory layer adoption: Risk team Month 1 (with SQL), 6 个月后 voluntary migrate to vector
- 0 conflict, 0 push back
- This taught me: **abstraction with escape hatch > forced standardization**

**Vulnerability**:
> "我 initial stand firm 是 wrong call. Stand firm 应该 ground 在 principle (one-way + high blast). Memory backend 是 two-way (可换) + low blast (Risk team only). 我把 ego 当 principle. 现在我每次 stand firm 先问 '如果错了, blast radius 是什么? 可逆吗?' 这 30 秒 self-check 救我多次."

---

## 5 个 Follow-ups (interviewer 追问 + 准备答案)

### Follow-up 1: "What if pilot data sided with ops (i.e., 7B hallucination 也 OK)?"

**Answer**:
> "I would have backed down. Stand firm 不是 'I'm always right', 是 'until data prove otherwise'.
>
> 我 prep escalation plan 时 explicit commit: 'A/B pilot 2 weeks, both sides abide by data'. If pilot 显示 7B hallucination < 2% (acceptable), 我会 ship 7B. 我的 credibility 来自 'data wins', 不是 'I never lose'.
>
> 实际数据 7B 4.2%, 远超 acceptable. 但 if it were 1.8%, I'd ship 7B. 这种 conditional commitment 才让 stand firm credible 不是 stubborn."

### Follow-up 2: "How do you know when to escalate vs continue at peer level?"

**Answer**:
> "**Two triggers for escalation**:
>
> **One — Stuck > 2 rounds + no new information**. Disagreement 第 3 round 还在 repeat 同 argument = peer level 不能 resolve, need senior decision.
>
> **Two — Decision exceeds peer authority**. 我跟 ops director peer-level disagree, 但 base model 选择影响 quarterly cost + regulator, 需要 product VP 决定. 我escalate 'not because I can't convince you, but because this decision needs your boss in the room'.
>
> 反面: 不 escalate scenarios:
> - Rounds 1-2 normal back-and-forth, escalate too early = 'tattling'
> - Two-way door + low blast = let peer resolve, escalate is overkill
>
> Indonesia base model 我没 escalate, 因为 second meeting with data 直接 resolve. BNPL VP case 我也没 escalate, 1v1 with VP resolve. 实际 18 个月 FDE 工作只 escalated 2 次 'joint manager 1:1'."

### Follow-up 3: "Have you ever stood firm and been wrong?"

**Answer**:
> "Yes — 这个 question 我必须 honest answer.
>
> Internal Agent Platform Memory layer SQL vs vector. 我 initial stand firm 'vector DB is standard', argued 3 rounds with Risk team lead. Eventually 6 个月后 voluntarily migrate to vector, 但 those 3 rounds 创造 friction + delay onboarding.
>
> **What I learned**: 我 stand firm 时没做 reversibility check. Memory backend 是 two-way door (可换), low blast (single team). Stand firm 应该 reserve for one-way + high blast. 我用 ego 当 principle.
>
> 现在我 stand firm 前先问 30 秒: 'one-way? high blast? if wrong, recover cost?' 如果三个 No, I don't stand firm.
>
> 这种 self-honesty 让我 stand firm 的 cases 反而更 credible — 因为我知道 distinguish."

### Follow-up 4: "How did you maintain relationship after standing firm?"

**Answer**:
> "三件事:
>
> **One — Acknowledge their valid concerns explicitly**. Indonesia base model 那次, 我 second meeting opening 是 'cost concern is valid, 我之前没 surface hidden cost'. Not 'I was right all along'. Acknowledge让 ops 觉得 his concern 被听到不是 dismissed.
>
> **Two — Admit partial loss after stand firm wins**. Training time 我 underestimate. Multi-market timeline miss 5%. 我事后 owe ops 'you were right on training time'. Admit partial loss 让 disagreement 看起来 collaborative 不是 zero-sum.
>
> **Three — Bank trust between disputes**. Stand firm 不能频繁. 我跟 Indonesia ops 18 个月只 stand firm 2 次. 其他 disagreement 我 deferred (small things) 或 found middle ground (medium things). Stand firm 在 trust bank 余额高时 'spend' 一次, 然后立刻 deposit 回去.
>
> Ops director 18 个月后 跟 my manager skip-level: 'Gao 跟我们 disagree 时候我们最 trust 他'. 这是关系 net positive 因为 stand firm well."

### Follow-up 5: "What's the worst version of 'stand firm'?"

**Answer**:
> "Worst version 是 'stand firm 在 wrong thing for wrong reason'.
>
> 几个 anti-pattern:
> 1. **Ego-grounded**: 'I designed it, can't admit it's wrong'
> 2. **Identity-grounded**: 'I'm the ML expert, you're ops, my call'
> 3. **Sunk cost**: 'we spent 4 weeks on this, can't change now'
> 4. **Public commitment**: 'I told VP this is right, can't reverse now'
> 5. **Stubborn loop**: 'they keep pushing back so I keep digging in'
>
> 全是 ego variants, not principle.
>
> **Counter-test**: 'if X person on my team made this call, would I support?' 如果 No, 不应该 stand firm. Stand firm 应该 transferable —— principle-grounded position 不依赖 individual.
>
> 我 Internal Platform Memory layer case 是 ego variant 4. 现在我 stand firm 前 explicit check 5 个 ego trigger."

---

## ❌ 死路答法 (碰了就挂)

### 死路 1: "I was right, they were wrong, end of story."

**为什么挂**: No nuance, no humility. FDE manager 立刻判断 "difficult to work with".

**怎么改**: Steel-man their side explicitly. "Ops cost concern was valid, training speed concern was valid. I disagreed on regulator exposure specifically, not their whole framing."

---

### 死路 2: "We escalated to VP and VP sided with me."

**为什么挂**: Escalation 看起来 first move 而不是 last resort. FDE manager 怕你 escalation-first 风格.

**怎么改**: 显式讲 "I prep escalation plan as Plan B, but resolved at peer level via data". Escalation 是 backup, 不是 main strategy.

---

### 死路 3: "I held my ground for 3 weeks."

**为什么挂**: 3 周僵持 = leadership failure. Senior FDE 不让 disagreement 3 周.

**怎么改**: 2 meetings, 2 weeks max. 加 'data-driven resolution mechanism' (A/B pilot, abide by data) 让 disagreement converge fast.

---

### 死路 4: "我跟 customer 经常 disagree."

**为什么挂**: Frequency = difficult signal. FDE manager 怕你 friction generator.

**怎么改**: "我 18 个月 stand firm 2 次, 其他 disagreement 我 defer 或 middle ground. Stand firm 在 trust bank 高时 spend 一次." Rarity 是 signal of judgment.

---

### 死路 5: 没有 example of when you backed down

**为什么挂**: 不能区分 'principle vs ego'. 显得 always stand firm = stubborn.

**怎么改**: 必须有 段 8 (back down example). LangGraph case 或 Memory layer case. Compare 显示 你 distinguish.

---

### 死路 6: "我对的 because I have more experience."

**为什么挂**: Identity-grounded, not principle-grounded. Hierarchy 是 weak argument in FDE.

**怎么改**: Ground in data / 监管 / 安全 / 用户. 不是 'I'm senior so'. 'Data shows regulator exposure $X' 是 universal language.

---

### 死路 7: 没讲 outcome reflection (你对吗?)

**为什么挂**: Confirmation bias 信号. Senior FDE 事后 audit 自己的 stand firm.

**怎么改**: 显式 quote outcome. "Pilot data sided 70% my position, 30% ops side. I admitted partial loss on training time."

---

## ✅ 加分项 (top 5)

### 加分 1: "Hill worth dying on" criteria 显式

讲 3 criteria: principle-grounded + one-way door + high blast radius. 反过来 Hill not worth: ego-grounded + two-way + low blast. 这种 explicit criteria 是 senior signal.

### 加分 2: Steel-man before stand firm

"我 steel-manned ops side: cost real, training speed real, industry precedent real. 然后 self-check 我是 principle 还是 ego." 这种显式 considered both sides 让 stand firm credible.

### 加分 3: "A/B pilot abide by data" resolution mechanism

不是 'who's right' debate, 是 'let data resolve'. Conditional commitment ("I'll ship 7B if pilot shows hallucination < 2%") 让 stand firm not stubborn.

### 加分 4: Admit partial loss after standing firm

"Training time I underestimated, multi-market miss 5%. Ops was right on this." Admitting partial loss 是 stand firm 之后维持 relationship 的 trust signal.

### 加分 5: 显式 back-down example contrast

LangGraph case 或 Memory layer case. 这种 contrast 让 manager 知道 你 distinguish.

---

## 一句话总结

> **"Stand firm" 的 winning answer 不是讲你赢 disagreement, 是用 hill-worth-dying-on criteria (principle + one-way + high blast) + steel-man + A/B pilot + admit partial loss + back-down example 证明 "我 stand firm 是 selective judgment 不是 stubborn instinct"**.
>
> 18 个月 stand firm 2 次. Rarity + selectivity = credibility.

---

## Cheat Sheet (面试前 30s 扫一眼)

```
Question type:
  Behavioral / Judgment / Conflict (4-5 min monologue)
Key skill being tested:
  Principle vs ego distinction + steel-man + data-driven resolution + admit partial loss + back-down example

Answer arc (8 段, must have 段 8):
  1. Context + relationship (20s)         — 6-month trust基线
  2. Disagreement essence (20s)           — both sides 具体
  3. Why stand firm — principle (30s)     — 3 grounds (data/监管/irreversibility)
  4. What I considered before (30s)       — Steel-man + self-check ego
  5. Actual conversation (60s)            — Lost first meeting, prepped 2 weeks, won second with data
  6. Pivot / escalation prep (45s)        — A/B pilot abide by data
  7. Outcome incl. partial loss (30s)     — 70% my position, 30% their concern valid
  8. Back-down example (20s)              — LangGraph or Memory layer compare

Numbers to drop:
  Indonesia base model:
    7B hallucination 4.2% (CI 3.8-4.7%)
    13B hallucination 1.5% (CI 1.2-1.9%)
    Cost: 13B INT8 是 1.4× 7B (not 3×)
    OJK precedent: RMB 8M fine
    Latency: vLLM 280ms vs FP16 320ms
    Outcome: 12 months 0 OJK incident
    Partial loss: training 5d vs 2d, timeline 6→8 months, ops Q-end miss 5%
  BNPL VP hybrid schema: 32% queries triggered 数字 in free-form
  Memory layer: 6 months Risk team voluntary migrate to vector

Vulnerability:
  "Memory layer SQL vs vector — 我 initial stand firm 是 ego ('I want to standardize').
   Reversibility check: two-way door + low blast. Not worth standing firm.
   现在我 stand firm 前 30 秒 check '如果错了, blast radius? 可逆吗?'
   如果三个 No, I don't stand firm."

Close:
  "18 个月 stand firm 2 次. 其他 disagreement 我 defer 或 middle ground.
   Stand firm 在 trust bank 高时 spend 一次. Rarity + selectivity = credibility."

Red lines:
  - "I was right, they were wrong" (no nuance)
  - "Escalated to VP" (escalation-first)
  - "Held ground 3 weeks" (僵持太久)
  - "Often disagree" (friction generator)
  - 没 back-down example (always stand firm = stubborn)
  - "I have more experience" (identity-grounded)
  - 没 outcome reflection (confirmation bias)

3 ready STAR (alternate):
  STAR 1: Indonesia base model 7B vs 13B (★ primary, won + admit partial loss)
  STAR 2: BNPL chatbot output schema (won via hybrid reframe)
  STAR 3: Memory layer SQL vs vector (LOST, back-down example)

5 follow-ups ready:
  Q1: Pilot sided with ops? → "I'd back down. Conditional commit makes stand firm credible"
  Q2: When escalate? → "Stuck > 2 rounds + no new info" or "decision exceeds peer authority"
  Q3: Stand firm wrong? → Memory layer SQL story, ego masquerading as principle
  Q4: Maintain relationship? → Acknowledge + admit partial loss + bank trust between disputes
  Q5: Worst version stand firm? → 5 ego variants (designed it / I'm expert / sunk cost / public commit / stubborn loop)

Hill-worth-dying-on criteria (3):
  1. Principle-grounded (data / 监管 / 安全 / 用户) — not ego
  2. One-way door — recovery cost high
  3. High blast radius — multiple users / dollars / regulator

Hill-NOT-worth criteria (mirror):
  1. Ego-grounded ("I want to build" / "my style")
  2. Two-way door — reversible
  3. Low blast — single team / no users impact

Stand firm playbook (sequence):
  1. Steel-man their side (out loud)
  2. Self-check ego vs principle (30 sec)
  3. Reversibility analysis (one-way? blast?)
  4. Prep data + alternatives + escalation plan
  5. Acknowledge their concern first
  6. Walk data, address their concerns
  7. Propose data-driven resolution (A/B pilot)
  8. Admit partial loss after winning

5 ego variants to watch:
  1. Sunk cost ("spent 4 weeks can't change")
  2. Public commitment ("told VP, can't reverse")
  3. Identity ("I'm the expert")
  4. Stubborn loop ("they push so I dig in")
  5. Ego-as-principle ("standardize" when really "I want to build")
```
