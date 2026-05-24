## Client Sim #4 · CFO Model Variability — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](cfo-model-variability.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`cfo-model-variability.html`](cfo-model-variability.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"CFO refuses to deploy your model because it gives different answers to the same question. How do you respond?"**, 我按这 8 层回答, 不跳序. 这题考的不是 "怎么 reduce temperature", 是 **mental model translation + 2-mode system design**.

### 📐 CFO Model Variability — 8 层结构

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 (literal) |
|---|---|---|---|---|
| 1 | Acknowledge before educating | 1 min | **不立刻 "let me explain stochasticity"**. 先 acknowledge: > *"You're right to be concerned — same input giving different output is fundamentally different from what your spreadsheet does. That's not a model bug, it's a category difference. Let me show you how I'd think about when each behavior is appropriate."* | "First sentence: 'You're right to be concerned.' Validate the gut before educating..." |
| 2 | 6 analogies ranked by effectiveness | 3 min | **(1) Equity analyst's narrative writeup (different wording, same takeaway) — 90% effective for CFOs** > **(2) Weather forecast 70% rain (uncertainty quantified, decision usable)** > **(3) Junior analyst variance vs error** > **(4) Translator (faithful but not word-for-word)** > **(5) Spell checker confidence** > **(6) Survey margin of error**. 我按 CFO type 挑 (1) or (2) | "Six analogies, ranked. For a CFO from finance background, equity analyst writeup works 90% of the time..." |
| 3 | Variance-vs-error reframe | 2 min | 关键 reframe: **variance ≠ error**. Junior analyst write 2 different summaries of same quarter = both correct, just different wording. **错的是 wrong number**, 不是 different wording. 然后 show: pin the numbers, vary only the prose | "Variance and error are different. Different wording of correct facts is not error. Wrong fact is error. Here's how we engineer for that..." |
| 4 | 4-layer guardrails | 3 min | (i) **Number pinning** (deterministic retrieval, never LLM-generated numbers), (ii) **Citation requirement** (every number cited to source row), (iii) **LLM-as-judge for factual consistency** (5 runs, flag if numerical drift), (iv) **Human review checklist for material outputs**. **CFO 看到这 4 层后 95% case 满意** | "Four guardrails. Numbers are pinned by deterministic retrieval. LLM only writes prose. Citation required. Judge model checks for drift..." |
| 5 | 2-mode system | 3 min | Offer CFO **two modes, CFO chooses per use case**: > **Default mode (variance OK)** — exploratory analysis, briefing summary, prose. Temp = 0.3, citations on. > **Audit mode (pinned)** — regulatory filings, board reports, audit responses. Temp = 0, seeded, cached, version-locked output. **Same model, two configurations**, CFO selects | "Two modes, CFO chooses. Default for prose, Audit for filings. Same model, different config. Let me show the toggle..." |
| 6 | Push-back judgment | 2 min | **当 CFO 说 "I want deterministic always"**, 答: > *"We can do that. The cost is: prose quality drops by ~30%, model can't synthesize across rows. If you accept that for filings but want full quality for briefings, that's the 2-mode setup. If you want deterministic everywhere, here's what we lose."* — **让 CFO 看 trade-off**, 不是 fight him | "If CFO insists deterministic-everywhere, I show the cost. Not fight, illustrate trade-off. CFO decides..." |
| 7 | 24h follow-up artifact | 2 min | 24h 内 deliver: (i) **1-page memo: 5 examples** showing same-input/different-prose/same-fact, (ii) **demo of 2-mode toggle**, (iii) **calibration report** (LLM judge on 100 finance questions, pass rate by category), (iv) **invitation for CFO to add 10 audit-mode questions**. **CFO owns the test set** | "24-hour deliverable. Five examples, mode toggle demo, calibration report, CFO adds 10 audit questions to my test set..." |
| 8 | Resume reframe — ConvFinQA + BNPL | 1 min | "我做过 ConvFinQA, multi-hop financial QA — 我们 deliberately pinned numbers with deterministic retrieval, LLM only generated reasoning chain. **9-variant ablation 我跑过 calibration**. Plus TikTok PayLater fraud explanation 给 compliance, 我们用 2-mode system, regulator 喜欢 audit mode (deterministic), ops 用 default mode (prose). **CFO 这场是同 playbook**" | "I've built this — ConvFinQA had deterministic number pinning, BNPL had 2-mode for regulator vs ops..." |

### 🎯 为啥按这个序

**先 acknowledge (Layer 1), 再 analogy (Layer 2), 再 reframe variance≠error (Layer 3), 再 system design (Layer 4-5)** — 因为 90% candidates 直接讲 temperature/seeding, CFO 听不懂. **CFO 的 concern 是 mental model, 不是 hyperparameter**. 用他自己 domain 的 analogy (equity analyst writeup) 是 unlock.

2-mode system (Layer 5) 是这题的 **Client Sim 区分项** — 一般 candidate 给 yes/no on temperature, FDE 给 CFO 决定权 + 2 mode toggle.

### 🔥 哪一层最容易被追问 deeper

- **Layer 2 (analogy)**: 面试官扮 CFO 说 *"equity analyst is paid to be different, your model isn't paid"* → 答: > *"Fair pushback. Replace equity analyst with internal CFO briefing: same data, two analysts write it up differently, both correct. The wording variance doesn't change the decision. That's the analogy."*
- **Layer 4 (guardrails)**: 面试官会问 "how do you prove number pinning works?" → 答: 1000-question regression test, deterministic retrieval, assert numerical fields against ground truth, 100% pass rate before deployment. Re-run on every model update.

### ⏱ 时间压缩版 (30 min round)

- 3 min: acknowledge + analogy selection (Layer 1-2)
- 5 min: variance-vs-error reframe (Layer 3)
- 8 min: 4-layer guardrails + 2-mode (Layer 4-5, 重点)
- 5 min: push-back + 24h artifact (Layer 6-7)
- 2 min: resume hook (Layer 8)

### 🆘 卡壳兜底 (针对这题)

- 卡 analogy → fall back to **equity analyst writeup** — 永远 work for finance CFO
- 卡 guardrails → use **ConvFinQA deterministic number pinning** 故事
- 卡 push-back → use **"let CFO see trade-off, don't fight"** principle

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

> **CFO 的 concern 不是技术问题, 是 mental model 冲突 (deterministic spreadsheet vs stochastic LLM)**. 不是说服他 stochastic is fine, 是给他 mental model 工具区分 use case + 给 deterministic 路径. 70% case default mode (variance OK 因为 wording 而非数字), 30% case audit/regulatory mode (pinned). **Both options offered, CFO chooses**.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Non-determinism | 同 input 不一定同 output | 不要在 CFO 面前说这词 |
| Determinism | 同 input → 同 output (spreadsheet) | CFO 心智 default |
| Stochastic | 随机过程, output 是 distribution | 内部术语 |
| Temperature | 0=deterministic 1=高随机 | 跟 CFO 绝不提 |
| Reproducibility | pin seed + version 可重现 | CFO 可接受概念 |
| Audit log | 每次 LLM 调用记录 input/output/seed/temp/timestamp | 合规 / 审计 / replay 基础 |
| Variance / Consistency | 多次跑 output 离散度 | 必 monitor + report 数字 |
| Guardrails | LLM 输出之外 deterministic rules / validators | CFO 喜欢这词 |
| 2-mode system | default 0.3 temp + audit/compliance 0 pinned | 核心架构方案 |
| Confidence-based routing | conf > 95% auto, < 95% human review | 高 stake guardrail |
| LLM-as-narrator | 数字 from SQL, LLM 写 commentary | 关键 framing |
| Hash-stored artifact | 输出 + hash 一次性写盘 | audit replay 用 |
| Decision invariance | 同 input → 同 decision (reason text 可变) | 监管角度 |
| ECE | Expected Calibration Error | confidence 校准指标 |
| Human-in-loop (HITL) | 高 stake 强制 human | 金融 / 监管 |
| Replay | 用 audit log 参数重跑 | 审计 friendly |

### 🎯 5 个核心 framework

**Framework 1**: A·B·C·D Mental Model Translate
- When: CFO 提出 concern 第一刻
- Algorithm: 1. Acknowledge concern ("I understand why this looks like a defect") 2. Business-language analogy (financial advisor / 2 auditors / email drafts vs sent) 3. Concrete bounds (99.1% numerical / 99.7% decision / 0.3% mean deviation) 4. Deterministic option (pin seed + cache result)
- Trade-off: 用 analogy 风险 over-simplify, 必须配 concrete numbers
- Tools: 3 analogy stack, pre-measure consistency real data, audit-friendly language

**Framework 2**: Variance Bounds + Confidence Display
- When: CFO 问 "how much variance"
- Algorithm:
  - Pre-measure: numerical 99.1% identical / categorical 99.7% / confidence ±2pp / numerical mean deviation 0.3% / time stability < 0.2%/wk
  - vs human baseline (70% identical, 2-5% deviation) → LLM 10x better
  - Confidence-based routing: > 95% auto-finalize / < 95% human review / amount > $1M mandatory HITL
- Trade-off: 给具体数字 vs 承认不确定 + ECE
- Tools: consistency dashboard, calibration probe model, confidence-based routing API

**Framework 3**: LLM-as-Narrator (numbers vs prose 分离)
- When: 财务数字 + commentary 混合 use case
- Algorithm:
  - Numbers come from SQL / Excel (deterministic source of truth)
  - LLM writes commentary about numbers
  - Numbers NEVER regenerated by LLM
  - "Financial truth = deterministic, narrator = LLM"
- Trade-off: 增加架构复杂度但消除 CFO 关键焦虑
- Tools: 2-stage pipeline (SQL aggregator → LLM commentator), audit log 分别记两阶段

**Framework 4**: 2-Mode System + 4-Layer Guardrails
- When: 不同 use case 不同需求
- Algorithm:
  - Default mode: temp=0.3, slight variance, productivity (70% case)
  - Audit/compliance mode: temp=0, pinned seed, hash-stored (30% case)
  - 4 guardrail layers:
    - Input: schema + range validation
    - Output: schema enforcement + citation check (RAG sources)
    - Deterministic core: numbers from SQL not LLM
    - Human-in-loop: low conf or high stake amount
- Trade-off: 加 layer = 加 latency, 但 financial / regulatory worth it
- Tools: feature flag mode selector, pydantic schema, JSON output validation

**Framework 5**: Push Back vs Accommodate Decision
- When: 客户 ask 跟 LLM 本质冲突
- Algorithm:
  - **Push back when**: 客户要 100% determinism on UX (rigid robot 体验差) / 客户要 autonomous LLM on financial decisions (high stake 必须 HITL) / 客户 skip audit log / 客户 skip HITL on high stake
  - **Accommodate when**: 客户要 0 variance for audit artifact ✓ (hash-stored) / SQL-deterministic numbers ✓ / 行业 strict reproducibility (banking / pharma) ✓
- Trade-off: 不是所有客户 ask 都对, 但 push back 必须基于 first principles 不是 ego
- Tools: use case classifier framework, regulatory mapping (FINRA / OJK / etc)

### 🌳 关键决策树

```
CFO concern 类型?
├── "数字不一样" → Critical. Pin LLM-as-narrator (numbers from SQL, NEVER LLM regenerate)
├── "Wording 不一样" → Default mode OK. Analogy: 2 advisor same conclusion different wording
├── "审计 reproducibility" → Audit mode (temp=0 + pinned seed + hash-stored)
├── "合规 explanation" → Decision invariance (同 decision, reason text 可变)
└── "100% deterministic 必须" → Accommodate (pin everything + cache hash) OR change architecture

Use case 适合 default vs audit mode?
├── Internal productivity / draft → default 0.3 ✓
├── Financial commentary → LLM-as-narrator + audit log
├── Regulatory filing → audit mode pinned
├── Customer-facing decision → confidence routing + HITL
└── High-stake number (> $1M) → mandatory HITL

CFO 是 right (push back 错误)?
├── 财报数字真的需 100% reproducible? → Architecture: pin + cache
├── 监管要求审计? → Audit log + replay
└── 客户 self-service expect 一致? → Cache by query hash

AE over-promise "100% reliable"?
├── 公开 不 contradict
├── 私下立刻 align
├── Follow-up written 用精确语言
└── AE 坚持 → escalate manager
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: CFO Analogies That Work**
- 核心解法:
  ```
  3-Analogy stack:
  1. Financial advisor: 2 个 advisor 看同 data 给同 conclusion, 但 wording 不同. CFO 不会觉得 advisor "broken"
  2. Two auditors: 同 financials 同 flagged issues, 但 audit report 措辞不同. CFO 接受这是 professional 常态
  3. Email drafts vs sent: 你 drafting 时 variance, 一旦 send 就 frozen. LLM 也类似 (audit log 记 frozen artifact)
  
  CFO-specific: "你的 CFO advisor 同 P&L 看 2 次, 描述 phrasing 会不同. 你不觉得 advisor broken. Same model, more reliable"
  ```
- Top 3 gotchas: generic analogy / 用 "temperature" / patronize ("you don't need to understand")
- Tools/tactics: pre-measure CFO use case real data, 3 analogy stack

**Problem 2: Variance Bounds + Confidence (Calibration)**
- 核心解法:
  ```
  Pre-measure 5 metric (CFO use case 真实数据):
    Numerical consistency: 99.1% identical
    Categorical decision: 99.7% identical
    Confidence calibration: ECE < 0.05, ±2pp
    Numerical mean deviation: 0.3%
    Time stability: < 0.2%/week
  
  vs human baseline:
    Human: 70% identical 2-5% deviation
    LLM: 99% identical 0.3% deviation
    → LLM 10x better than current
  
  Confidence routing:
    conf > 95% → auto-finalize
    conf < 95% → human queue
    amount > $1M → mandatory HITL
  ```
- Top 3 gotchas: vague reassurance / 没 pre-measure / faking metrics
- Tools/tactics: consistency dashboard, ECE measurement, probe model

**Problem 3: Variance as Feature, Not Bug**
- 核心解法:
  ```
  Reframe: variance < human variance (existing process)
  Show CFO: 你的 finance team 也不 100% identical
    - 2 analyst 看同 P&L 写 commentary, wording 70% identical
    - LLM 99% identical 反而更 consistent
  
  Productivity dividend:
    - LLM 在 commentary 多样性帮 CFO 看到不同 angle
    - Same data 不同 angle 是 feature for board prep
  
  Audit invariance:
    - 同 input → 同 decision (approve/deny)
    - 同 input → 同 numerical answer (SQL-backed)
    - 仅 prose wording 有 variance (low stake)
  ```
- Top 3 gotchas: 不 quantify human baseline / variance 全是负面 framing / 不分 decision vs wording variance
- Tools/tactics: human baseline pre-measure, decision invariance dashboard

**Problem 4: Guardrails (4 Layer)**
- 核心解法:
  ```python
  # Layer 1: Input validation
  schema_validate(input)  # pydantic
  range_check(financial_data, [-1e9, 1e9])
  
  # Layer 2: Output schema
  llm_output = llm.complete(prompt)
  validate_json_schema(llm_output, OutputSchema)
  validate_citations(llm_output.sources)
  
  # Layer 3: Deterministic core
  # NEVER let LLM compute numbers
  numbers = sql_query("SELECT SUM(revenue) FROM ...")
  commentary = llm_narrate(numbers)
  
  # Layer 4: Human-in-loop
  if confidence < 0.95 or amount > 1e6 or hazard_flag:
      queue_for_human_review(case)
  ```
- Top 3 gotchas: 让 LLM 算数字 / 没 input validation / HITL threshold 太高
- Tools/tactics: pydantic, JSON schema, SQL deterministic compute, confidence probe

**Problem 5: When to Push Back vs Accommodate**
- 核心解法:
  ```
  Push back when (基于 first principles, 不 ego):
    100% determinism on UX → rigid robot, 体验差
    Autonomous LLM on financial decisions → 必须 HITL high-stake
    Skip audit log → 合规灾难
    Skip HITL on high stake amount > $1M
  
  Accommodate when:
    Audit artifact 0 variance → pin + cache + hash-store ✓
    SQL-deterministic numbers ✓
    Industry strict reproducibility (FINRA / pharma) → audit mode default ✓
    Regulatory filing → audit mode pinned ✓
  
  Sales pressure to over-commit:
    公开: 不 contradict AE
    私下: align math, refuse if needed
    Written follow-up: precise language anchor
    AE 坚持 → escalate manager
  ```
- Top 3 gotchas: 完全 yes 失底线 / 完全 no 失关系 / 不区分 use case 一刀切
- Tools/tactics: use case classifier, regulatory mapping table, escalation hierarchy

### 🔥 Production gotchas (top 15)

1. 用 "temperature / top-p / stochastic / sampling" → CFO 听不懂失信
2. Argue "it's not a bug" → defensive loses
3. 没 concrete consistency 数字 → vague reassurance CFO 不信
4. 没提 determinism option → CFO 觉得没出路
5. Patronize "you don't need to understand" → insulting CFO 反弹
6. 没 audit log story → compliance ask 主要没回答
7. Promise 0 variability 不改架构 → 第二天 demo 失信
8. 没区分 use case → all-or-nothing 错失 nuance
9. 没用 CFO 自己 domain analogy → generic 不 stick
10. AE 当场 over-promise 你不 push back → 后续背锅
11. 没承认 "有些 use case LLM 不该用" → 卖锤子 to everything
12. 让 LLM 算数字 → financial truth 应 deterministic SQL
13. HITL threshold 太高 (e.g., > $10M) → high stake 漏网
14. 没 confidence routing → 低 conf 也 auto-finalize
15. Audit log 不 hash-stored → replay 无法 byte-exact

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| LLM-as-narrator | BNPL chatbot | 决策结果 deterministic, prose LLM 生成 |
| Audit log | Voice agent | input/output/model/temp/seed 完整记录 |
| Confidence routing | Indonesia refund tier | conf > 95% auto, < 95% manual |
| Decision invariance | Voice agent risk | 同 input → 同 decision, reason text 可变 |
| Calibrated confidence | Voice agent | ECE < 0.05 deployment 门槛 |
| Variance bounds | ConvFinQA ablation | numerical 99% identical |
| Regulatory framing | Indonesia BNPL OJK | 监管 decision invariance |
| 2-mode system | Voice agent multi-market | productivity vs compliance mode |
| Push back AE | 7 markets cross-team | "I won't promise lies" |

### 🎤 面试现场 quotables (top 8)

1. "I understand why this looks like a defect — let me explain how we think about it"
2. "Imagine 2 financial advisors looking at the same P&L. Same conclusion, different wording. That's our LLM"
3. "For audit, we hash-store the artifact. You see the same signed PDF every time, not a re-run"
4. "Numerical consistency is 99.1%, decision consistency 99.7%. Your current human process is 70%"
5. "Numbers come from SQL — deterministic source of truth. LLM only writes the commentary. Financial truth is never regenerated by LLM"
6. "Two modes: default temperature 0.3 for productivity, audit mode temp=0 + pinned seed + hash-stored for compliance. You pick per use case"
7. "Confidence > 95% auto-finalize, < 95% human review, > $1M mandatory human-in-loop"
8. "I won't promise 100% reliability — that would be a lie. Here's what I can promise with numbers"

### 🚨 红线 (top 10 anti-patterns)

1. Promise 100% reliable (lie)
2. Faking consistency metrics
3. Skipping audit log
4. Patronizing CFO ("you don't need to understand")
5. AE over-promise + you silent
6. Autonomous LLM on financial decisions
7. Let LLM compute numbers (use SQL)
8. HITL threshold 太高 漏 high-stake
9. 用 "temperature / stochastic / by design" 术语
10. "AI is unpredictable" defensive 即使 true
