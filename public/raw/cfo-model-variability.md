## 题目（verbatim）

> "Explain to a **non-technical CFO** why the model produces **different outputs for the same input** (non-determinism is **not a bug**). Without losing trust."

**出处**: fde.academy 客户模拟. OpenAI / Anthropic / Google FDE / AI deploy companies 都问. 跨所有 LLM enterprise sales 必经.

**Round**: Client Simulation (30-45 min)

---

## 这道题在考什么

考你**技术 → business 翻译**能力 + **judgment about when to push back vs accommodate**:

1. **类比能力** — CFO 不需要懂 temperature, 但需要 mental model
2. **Trust framing** — "不一致" 听起来像 "不可靠"
3. **Audit & guardrails** — CFO 关心 compliance / financial impact
4. **Concrete numbers** — vague reassurance 没用, 99.1% 之类的 concrete number 才信
5. **When CFO is right** — if use case actually needs determinism, **don't argue, change architecture**
6. **Variance as feature, not bug** — show CFO that variability beats human variance in their existing process
7. **Internal pushback when sales over-promises** — 不接受 "我们的模型 100% reliable" 这种 lie

这是一道 **technical communication 题里最考 craft** 的, 因为你要:
- 用 CFO 听得懂的语言 (但不 patronize)
- 给具体数字 (但承认不确定性)
- 提供 audit/compliance 路径 (而不是说 "trust us")
- 知道何时 push back 客户 premise (有些场景 LLM 真的不适合)

---

# Part 1 · 教学讲解

## 1. 五个核心术语先解释

**Non-determinism (非确定性)**: 同一 input 不一定产生同一 output. **不是 bug**, 是 LLM 本质属性. 来自 sampling (temperature > 0) + 浮点运算累积差异 + 硬件并行调度 (即使 temperature = 0).

**Determinism (确定性)**: 同 input → 同 output. 传统数据库 / spreadsheet / 大部分软件都是 deterministic. CFO 的 mental model 默认是 deterministic — 这是冲突源头.

**Stochastic vs Probabilistic**: Stochastic = 随机过程, output 是一个 distribution. Probabilistic = output 带 probability score. LLM 是 stochastic + 通过 sampling 输出 1 个具体答案 + 可以通过 logprob 看出 distribution.

**Temperature (温度, 0-1)**: 控制 sampling 随机性. 0 = 几乎 deterministic (但不 100%, 因为 hardware 因素), 1 = 高随机. 这是**你不该跟 CFO 说的词**, 但内部要懂.

**Reproducibility (可重现性)**: 给定 input + 完整 context (model version + seed + temp + system prompt), 能不能产生同一 output. **可重现 ≠ deterministic**: 可以 stochastic 但 reproducible (pin seed).

**Audit log (审计日志)**: 每次 LLM 调用记录 input + output + model + seed + temp + timestamp. **合规 / 审计 / replay 的基础**.

**Variance / Confidence (方差 / 置信度)**: 同 input 多次跑, output 的离散程度. 低 variance = 高 consistency. 你应该 monitor + report 这个数字.

**Guardrails (护栏)**: 在 LLM 输出之外加的 deterministic rules / classifiers / validators, 防止异常输出进入下游. CFO 听到 "guardrails" 比 "we trained the model" 更安心.

---

## 2. 这个场景的核心矛盾是什么

**矛盾 1: LLM 本质 vs CFO 心智模型**

CFO 一辈子用 spreadsheet, 看 ERP system, =SUM(A1:A10) 永远是同一个数. 他的 mental model 是 **deterministic 是 baseline**, anything else 是 bug. 你需要**重塑 mental model**, 不是 explain 技术细节.

**矛盾 2: 诚实 vs 信任**

"我们的模型有时输出不一样" → CFO 想 walk away. "我们 100% reliable" → 是 lie, 后续 explode. 必须找中间表达.

**矛盾 3: 默认 vs 可调**

LLM 默认 stochastic. 但你**可以**做成接近 deterministic (pin seed + temperature=0). CFO 不知道这个选项. 你需要 reveal 选项.

**矛盾 4: 业务 use case vs 一刀切**

不同 use case 对 variability 容忍度不同. 写报告: 多样性 OK. 计算财务数字: 必须 deterministic. **你的 job 是帮 CFO 区分**, 不是一刀切.

**矛盾 5: 内部销售压力 vs honest framing**

你的 AE 想说 "我们的模型 100% reliable". 你不能 backup 这个谎. **但你也不能在 CFO 面前 contradict AE**. 平衡 craft 需要.

**矛盾 6: 解释 vs patronize**

CFO 不是技术人, 但他**不蠢**. 用幼儿园语言 = 失信. 用术语 = 失信. 平衡: business-domain analogy + concrete numbers + audit-friendly framing.

**矛盾 7: 当 CFO 真的 right**

某些 use case (annual report number / regulatory filing) **真的需要 100% reproducibility**. 这时 push back 「LLM is fine」是 wrong. **正确**: change architecture (pinned seed + cached result).

---

## 3. 决策树 / 反应模板

| Stage | 你的核心动作 |
|---|---|
| **CFO 提出 concern (0-2 min)** | Validate: "I understand why this looks like a defect" |
| **2-5 分钟** | Business-language analogy (financial advisor / auditor / weather forecast) |
| **5-15 分钟** | Concrete numbers: variance bounds, consistency rate |
| **15-25 分钟** | Use-case 分类: where variability is feature, where it's risk |
| **25-35 分钟** | Architecture options: 2-mode system, audit log, deterministic mode |
| **35-45 分钟** | CFO chooses + commitment to ship audit/replay capability |

---

## 4. 关键利益相关方对照表

| Stakeholder | 他们在意什么 | "LLM 不一致" 时的内心 OS | 你对他们的关键动作 |
|---|---|---|---|
| **CFO** | Risk / ROI / compliance / audit | "I'm paying $1M for randomness?" | Business analogy + concrete numbers + audit path |
| **CFO 的 audit team** | Reproducibility / signed-off artifacts | "If auditor sees different outputs, we're toast" | Show audit log + hash-stored artifacts + replay |
| **CFO 的 CTO** | Technical depth / architecture | "Is this team naive about prod determinism?" | Technical detail to CTO 1:1 (don't bore CFO) |
| **CFO 的 risk team** | Worst case / compliance gap | "Can we explain to regulator if it goes wrong?" | Per-query control + guardrails + escalation path |
| **CFO 的 业务 user** | Daily usefulness | "I just want it to work" | Show that variance is hidden (UI looks consistent) |
| **你的 AE** | Close the deal | "Just promise 100% reliable" | Internally align: I won't promise lies |
| **你的 EM** | Don't over-promise | "Make sure architecture matches commit" | Confirm we can ship audit / determinism mode |
| **Your model team** | Don't lock into restrictive use | "Don't commit zero-temp on all use cases" | Negotiate: 2-mode, not 1-mode |

---

## 5. 具体业务场景 (4 个变种带人物)

### 场景 A: Acme Bank CFO 看 LLM-generated 财务摘要 (贴近你工作)

**人物**:
- 你 + AE David + EM Linda
- Acme: CFO Linda Chen, audit lead Raj, CTO 不在 (CFO 先 vetted)

**Setup**: 你的产品给 CFO 用 LLM 自动生成 monthly financial commentary, 输入是 raw P&L 数字, 输出是 1-2 paragraph commentary "Revenue grew 8% QoQ driven by APAC; OpEx outpaced inflation by 2pp; recommend tightening Q3..."

**Linda 的 concern**: 跑了 3 次同一份 P&L, 3 段 commentary **数字一样但 wording 不同**. 「How am I supposed to put this in the board deck if it changes every time I re-run?」

**关键 insight**: 数字是 fixed (你 deterministic compute), prose 是 LLM-generated (有 variance). CFO 焦虑的不是数字, 是 prose 看起来 "shaky".

→ Part 2 全部以此为蓝本.

### 场景 B: TikTok PayLater 风控 LLM 跟监管解释

**人物**:
- 你 + Indonesia 区 GM
- OJK (印尼 监管): 3 examiner + 1 compliance director

**Setup**: BNPL 风控 LLM 给客户做 credit decision. 同一客户 profile 2 次跑, decision 一致 (approve / deny) 但 reason text 不同.

**OJK 的 concern**: 「If we audit, would the regulator see consistent reasoning?」

**特殊性**: 监管语言, 不是 financial language. 你要展示 **decision invariance** (同 input → 同 decision) 即便 reason text 有 variance.

### 场景 C: 内部 ConvFinQA-style 多跳 QA 给 finance team

**Setup**: 内部 finance team 用 LLM agent 做多跳财报分析, 提问 "Year-over-year operating margin change?"

**Concern**: 跑 2 次, 答案数字偶尔差 0.1pp (因为不同 reasoning path).

**特殊性**: 数字 variance 本身是技术 issue. 不能光 "analogy", 要真正 fix (deterministic compute step + LLM-generated prose 分离).

### 场景 D: Bank dashboard 客户 self-service 查询

**Setup**: 客户在 dashboard 问 "What was last quarter top customer?", LLM 给 SQL-like reasoning + answer.

**Concern**: 同一客户问 2 次, 同一答案, 但解释不同.

**特殊性**: 客户期待 self-serve, variability 会被理解成 bug. 解法: cache LLM output by query hash, return cached version.

---

## 6. 工程上 / 应对上要做什么 (Playbook)

按 **会议中 / 24h / 1 周 / 长期** 4 阶段:

### 阶段 1 · 会议中 (0-45 min)

1. **Validate concern**: "Your concern makes sense, this looks like a defect"
2. **Analogy** to anchor mental model (financial advisor / auditor / etc)
3. **Concrete numbers** of consistency (要 pre-measure)
4. **Classify use cases**: where variability is OK, where not
5. **Offer 2-mode system**: default (slight variance) + audit/deterministic (pinned)
6. **CFO chooses + commit**: written followup with architecture
7. **不允许**: 用 "temperature" / "sampling" / "stochastic" / "by design"
8. **不允许**: "trust us" / "this is how AI works"

### 阶段 2 · 24 小时内

9. **Pre-measure consistency** for CFO's actual use case (real data)
10. **1-pager doc** with architecture + numbers
11. **Audit log demo**: show CFO 一个 mock audit log + replay
12. **Internal align**: with EM + model team on what mode we ship

### 阶段 3 · 1 周

13. **Ship 2-mode** capability (if not exists)
14. **Audit log + replay** functionality demo
15. **Onboard CFO's audit team**: train them on viewing log

### 阶段 4 · 长期

16. **Quarterly consistency metric review**: report drift over time
17. **New use case classification**: 每加新 use case, 重新做 mode 选择
18. **Compliance / regulatory engagement**: 提前 brief regulator

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **用 "temperature" / "top-p" / "stochastic"** | CFO 听不懂 → 失信. Replace: "model reasons rather than retrieves" |
| 2 | **Argue "it's not a bug"** | Defensive, loses. Replace: "I understand why this looks like a defect" |
| 3 | **没 concrete consistency 数字** | Vague reassurance, CFO 不信. Pre-measure! |
| 4 | **没提 determinism option** | CFO 觉得没出路, 走 |
| 5 | **Patronize** "you don't need to understand" | Insulting, CFO 反弹 |
| 6 | **没 audit log story** | Compliance ask 主要, 没回答等于没 propose |
| 7 | **Promise 0 variability without changing architecture** | 第二天 CFO 跑 demo 又 variance, 失信 |
| 8 | **没区分 use case** | All-or-nothing, 错失 nuance |
| 9 | **没用 CFO 自己 domain 的 analogy** | Generic analogy 不 stick |
| 10 | **AE 当场 over-promise, 你不 push back** | 后续你背锅 |
| 11 | **没承认 "有些 use case LLM 不该用"** | 显得 you sell hammer to everything |

---

## 一句话总结 (Part 1)

> **CFO 的 concern 不是技术问题, 是 mental model 冲突**. 他的世界是 deterministic (spreadsheet, ERP), LLM 的世界是 stochastic. 你的 job 不是说服他 "stochastic is fine", 是**给他 mental model 工具区分 use case + 给他 deterministic 路径**.
>
> 70% 的 case 用 default mode (variance OK 因为 wording 而非数字), 30% 用 deterministic mode (audit / regulatory). **Both options offered, CFO chooses**.

---

# Part 2 · 5 个深度问题 (Client Sim 硬核细节)

## ⚙️ Problem 1: Analogies That Work — 用 CFO 自己 domain 的语言

**这是 technical translation 的核心 craft. 一个好 analogy 抵 10 段技术解释**.

### 1.1 Bad analogy 的反面教材

| ❌ Analogy | 为什么 fail |
|---|---|
| "It's like a creative writer" | 太 fluffy, CFO 不想 creative |
| "Imagine if you had 5 brains" | 听起来 unstable / multiple personality |
| "Like a roulette wheel" | 暗示 gambling, fatal |
| "Random number generator" | 暗示 noise, 失信 |
| "It learns and grows" | 暗示 unpredictable evolution, CFO 想 stable |
| "Quantum computing" | 不相关, sounds buzzwordy |
| "Magic / black box" | 永远 don't say "black box" |

### 1.2 Good analogies 排行 (按 effectiveness)

**Analogy #1: Financial Advisor (⭐⭐⭐⭐⭐)**

> "Imagine you ask the same financial advisor the same question twice. Each time, you'd expect the **same recommendation**, but slightly different wording — they might emphasize different angles based on what they're thinking that day. **The conclusion is consistent, the wording varies**.
>
> Our model is like that — the **bottom-line decision is stable across runs**, but the prose around it varies. That's by design, because it produces **better answers than a robot reading from a script**. The robot is consistent but rigid; the advisor is consistent on the conclusion but flexibly explains.
>
> Most importantly: for **the numerical output**, we can pin it down so it's identical every time. The variability is only in **wording**, never the number."

**为什么 ⭐⭐⭐⭐⭐**:
- CFO 雇过 financial advisor, mental model exists
- 区分 "conclusion stable" vs "wording varies" — 这是核心 distinction
- 暗示 humanlike sophistication (positive framing)
- 留出口: 数字可 pin

**Analogy #2: Two Auditors (⭐⭐⭐⭐⭐)**

> "Think about two of your auditors looking at the same financials. You wouldn't expect them to produce **word-for-word identical** reports. You'd expect them to **flag the same issues** and reach the **same conclusions**.
>
> Our model is the same — for compliance-critical fields, **flagged issues are >99% consistent across runs**. The framing varies. We track that consistency rate as a metric.
>
> So 'identical wording' isn't the right standard. 'Consistent decisions and flagged issues' is — and we measure exactly that."

**为什么 ⭐⭐⭐⭐⭐**:
- 直接对接 CFO 的 audit world
- 已经 normalize variance 在他的 domain
- 给具体 metric (99%) 让 abstract concept 锚定

**Analogy #3: Stock Analyst Reports (⭐⭐⭐⭐)**

> "If you ask 5 analysts the same question on different days, they don't write **identical** reports — but they reach **similar conclusions**. Our model has similar natural variation. The decision is what matters, not the wording."

**为什么 ⭐⭐⭐⭐**: CFO 看过分析师报告, 知道 variance is normal. 稍微弱于 advisor / auditor 因为没那么 specific 到 CFO 个人经验.

**Analogy #4: Weather Forecast Confidence (⭐⭐⭐⭐)**

> "Weather forecasters give you '70% chance of rain'. The forecast varies day to day — sometimes they're more confident, sometimes less. But **with the confidence number, you can decide whether to bring an umbrella**.
>
> Our model can output **confidence alongside the answer**. When it's 95%+ confident, treat it like a hard fact. When confidence is lower, **trigger human review**. So you're never guessing whether to trust it — the model tells you."

**为什么 ⭐⭐⭐⭐**: 引入 **confidence** concept, 有用. 弱于 advisor/auditor 因为 weather 跟 finance 距离远.

**Analogy #5: Polling Margin of Error (⭐⭐⭐)**

> "Election polls have margin of error — '52% ± 3%'. The poll varies slightly each time, but margin of error tells you the **range you should trust**. Our model has measurable variability, and we report it as a number — typically <1% for numerical outputs."

**为什么 ⭐⭐⭐**: 抽象一点, 但 CFO 会懂. Backup analogy.

**Analogy #6: Email Drafts vs Sent Email (⭐⭐⭐⭐)**

> "Think of every model output as an **email draft**. Drafts vary — you might write the same email differently in the morning vs evening. But once you **hit send**, it's a fixed artifact. We do that with **caching**: any output that becomes 'sent' (the artifact you put in your report) is hash-stored. The cached version is what auditors see. **Variance in drafting, determinism in archive**."

**为什么 ⭐⭐⭐⭐**: 直接 introduce 解决方案 (cached artifact). Good for transitioning to architecture talk.

### 1.3 Analogy 串联使用

不要只用 1 个 analogy. 串 2-3 个:

> "Three ways to think about this:
>
> **(1) Like a financial advisor** — same conclusion, different wording.
>
> **(2) Like two auditors** — same flagged issues, different reports.
>
> **(3) Like email drafts vs sent email** — drafts vary, the archive is fixed.
>
> All three describe the same reality: **the substance is stable, the prose varies, the archive is deterministic**."

**串联效果**: 3 个 angles 锁定 mental model, CFO 自己挑 most resonant 那个 internalize.

### 1.4 当 CFO 拒绝 analogy 时

CFO: "Stop with the analogies. Just tell me technically what's happening."

(这种 CFO 是 ex-engineer, 知道一点)

**Response**:

> "Fair. Here it is: our model is a **statistical predictor** — given input, it predicts the most likely next token (word/number/symbol). Predictions are made one token at a time, and **multiple predictions can be equally likely**. The model picks one according to a probability distribution.
>
> **For numerical outputs**, we can configure it to always pick the highest-probability prediction (deterministic). For prose, we let it sample within high-probability range (slight variance, better quality).
>
> **For your audit needs**: we (a) pin the choice to deterministic per query, (b) cache the result with a hash, (c) record every input + output + version + seed in audit log.
>
> Three controls available per use case. **You pick the configuration**."

→ 当 CFO 是技术倾向时, **直接 give it 技术细节** (但仍然 framing-friendly).

### 1.5 检测 CFO 是哪种 type

| Signal | CFO type | 应对 |
|---|---|---|
| 说 "我不是 technical" 第一句 | Business CFO | Heavy on analogy |
| 提了 "deterministic" 这个词 | Tech-aware CFO | Light analogy, 直接 technical |
| 来自 banking 老背景 | Compliance-focused | Heavy on audit framing |
| 来自 startup 背景 | Risk-tolerant | Less audit, more value framing |
| 看着像在 take notes 给 board | Reporting CFO | Heavy on artifact / archive |

---

## ⚙️ Problem 2: Show Variance Bounds + Confidence (Calibration)

**抽象 reassurance 没用. 数字才信. 这里讲怎么得到 + 展示 concrete 数字**.

### 2.1 你应该 pre-measure 的 6 个 metric

会议前准备好 (or 在 24h follow-up 给):

| Metric | 定义 | Target | 怎么 measure |
|---|---|---|---|
| **Numerical output consistency** | 同 input 跑 10 次, 数字 identical 的比例 | >99% | Run 1000 prod queries × 10 runs, count |
| **Categorical decision consistency** | 同 input, decision (approve/deny) identical 比例 | >99.5% | Same protocol |
| **Confidence calibration** | model 报 95% confident 时, 实际 accuracy | 92-95% | Empirical |
| **Numerical deviation magnitude** | 当数字不一致时, 偏差 mean/max | <1% / <3% | Empirical |
| **Time-stability** | 同 input 跨周跑, drift | <0.5% per month | 定期 re-run |
| **Cross-tenant consistency** | 不同 tenant 同 input, 一致 | >99% | Sampling |

**Without these numbers, you're handwaving. CFO 不接受 handwave.**

### 2.2 怎么 measure (内部 process)

```python
# consistency_measurement.py
def measure_consistency(use_case, num_queries=1000, runs_per_query=10):
    """
    For each query, run N times, measure output consistency.
    """
    queries = sample_production_queries(use_case, num_queries)

    metrics = {
        'numerical_consistent': 0,
        'categorical_consistent': 0,
        'numerical_max_deviation': 0,
        'numerical_mean_deviation': 0,
    }

    for q in queries:
        outputs = [model.run(q) for _ in range(runs_per_query)]

        # Numerical consistency
        numbers = [extract_numbers(o) for o in outputs]
        if all_identical(numbers):
            metrics['numerical_consistent'] += 1
        else:
            dev = compute_deviation(numbers)
            metrics['numerical_max_deviation'] = max(
                metrics['numerical_max_deviation'], dev.max()
            )
            metrics['numerical_mean_deviation'] += dev.mean()

        # Categorical decisions (approve/deny etc)
        decisions = [extract_decision(o) for o in outputs]
        if all_identical(decisions):
            metrics['categorical_consistent'] += 1

    # Normalize
    metrics['numerical_consistent'] /= num_queries
    metrics['categorical_consistent'] /= num_queries

    return metrics
```

**结果展示**:

```
Consistency Report — Acme Use Case (Financial Commentary)
─────────────────────────────────────────────────────────
Measured on 1000 production queries × 10 runs per query
Date range: 2026-05-01 to 2026-05-20
Model version: gpt-4-1106 (pinned)

Numerical consistency:     99.2%
Categorical decisions:     99.7%
Confidence calibration:    93% (predicted 95%, actual 92.8%)
When numbers differ:
  Mean deviation:          0.3% of value
  Max deviation observed:  0.8% of value
Time stability (4 weeks):  0.2% drift per week
```

→ **这一张表是 CFO 信任的 anchor**.

### 2.3 把 metric 讲给 CFO 的 script

> "I want to give you concrete numbers, not just analogies. We ran your specific use case 1000 times across 10 trials each — that's 10,000 model invocations.
>
> **Here's what we found**:
>
> - **Numerical outputs identical**: 99.2% of the time. When different (0.8% of cases), the difference is less than 1% of the value.
> - **Categorical decisions identical**: 99.7%.
> - **Confidence is well-calibrated**: when the model says it's 95% confident, the actual accuracy is 93%.
> - **Time-stable**: less than 0.2% drift per week.
>
> Translation: **for 99 out of every 100 queries, you'd see the same output every time**. For the 1 query where it differs, the difference is so small it's well within the noise of human variance you already accept in your team's manual work.
>
> Plus — for any output you finalize, **we cache it**. The cached version is identical forever. So the variance only exists during exploration, not in your archive."

### 2.4 当 CFO 推 "what about the 1% that differs"

CFO 不会满足 99%, 会 zoom in 异常.

**Response**:

> "Good question. **The 1% that differs is the safety net working, not failing**. Here's what happens:
>
> When the model isn't confident, it samples among 2-3 plausible answers. For 99% of queries, those 2-3 happen to converge to the same. For 1%, they slightly diverge.
>
> **But we tag those queries automatically**. Confidence-flag triggers:
> - If confidence < 90% → tag for human review
> - If 95%+ → auto-finalize
>
> So the 1% that differs is **routed to human review by design**, not silently shipped. **You'll never see surprising variance in production**.
>
> And — for **your audit / annual report use case** — you don't even need to worry: we pin seed + cache result, **deviation = 0**.
>
> Want to see the workflow diagram of how confidence-flag routes work?"

→ 把 "1% scary" 转 "1% intentionally human-reviewed".

### 2.5 Confidence calibration 概念引入

CFO 不熟悉 calibration. 用 weather analogy:

> "**Calibration** = when the model says 'I'm 90% confident', is it actually right 90% of the time?
>
> - Well-calibrated: says 90% confident, right 90% of time. ✓
> - Overconfident: says 90%, right 70%. Dangerous — humans trust too much.
> - Underconfident: says 90%, right 99%. Wastes effort on human review.
>
> Our model is **well-calibrated within ±2pp** for your use case. That means **the confidence number you see is meaningful** — you can trust it as a signal for when to human-review."

### 2.6 Confidence-based routing architecture

```
┌─────────────────────────────────────────┐
│         LLM Output                       │
│         + confidence score (0-1)         │
└────────────────┬────────────────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │ Confidence > 95%│
        └────┬─────────┬──┘
             │ YES     │ NO
             │         │
             ▼         ▼
        ┌────────┐  ┌──────────────────┐
        │ Auto-  │  │ Human review     │
        │finalize│  │ queue            │
        │+ cache │  │ (typically <5%)  │
        └────────┘  └──────────────────┘
             │              │
             └──────┬───────┘
                    ▼
            ┌────────────────┐
            │ Audit log:     │
            │ input + output │
            │ + confidence   │
            │ + reviewer     │
            │ + timestamp    │
            └────────────────┘
```

→ 这个图比 100 段话有效. CFO 看到 "human review for low confidence" 立刻 calm down.

---

## ⚙️ Problem 3: Convert Variability into Business Value — Better Than Human Variance

**反守为攻: variance is feature, not bug, because it beats human-baseline**.

### 3.1 客户 implicit 假设: "currently we have determinism"

CFO 默认假设是: "我们现在的 process 是 deterministic, LLM 引入 variance". **错**.

CFO 现有 process:
- Junior analyst manually pull data → 不同 analyst 不同 wording
- Excel formulas — **deterministic 数字**, **不 deterministic interpretation**
- Boss review — 不同 manager 不同 emphasis
- Final report — 一个版本 ship, 但前面**多版本 churn**

**The current process has variance. It's just hidden.**

### 3.2 LLM variance vs human variance 数据 (要有)

Pre-measure 你自己 use case 的 human variance:

| Metric | Human baseline | LLM | Win |
|---|---|---|---|
| 同 input 相同 commentary 比例 | ~70% | 99% | ✓ LLM |
| 数字 deviation | 2-5% (typo / rounding) | 0.3% | ✓ LLM |
| 处理 time | 2 hours | 30 seconds | ✓ LLM |
| Human review needed | 30% | 5% | ✓ LLM |
| Cost per query | $50 | $0.5 | ✓ LLM |

→ **All-around win**. CFO 看到 human baseline 后, LLM variance 反而**显得 conservative**.

### 3.3 Reframe variance to value 的 script

> "I want to **reframe** the variance conversation. Currently, your team produces these reports manually. Let me ask:
>
> *(听 CFO 描述 current process)*
>
> So today, **3 analysts pulling the same data write 3 different commentaries**. The numbers might even differ by 2-5% due to typos / rounding choices / interpretation. Right?
>
> *(CFO: yes)*
>
> **Our LLM has 99% numerical consistency, 0.3% deviation, vs human's 2-5%**. By replacing the manual step, you actually **reduce variance in your final deliverable**, not introduce it.
>
> Plus: **5 minutes vs 2 hours**. Per query.
>
> The 1% LLM variance is **routed to human review** — so a human still touches the edge cases that need judgment. **You get human judgment where it matters, automation where it doesn't, and lower variance overall.**
>
> Variability isn't your enemy. **Unreliability disguised as determinism is your enemy** — and that's what manual processes are."

→ 把 conversation 从 "variance is bad" 转 "current baseline already has variance, LLM is improvement".

### 3.4 量化 variance reduction 的 ROI

| Without LLM | With LLM | Annual delta |
|---|---|---|
| 3 analysts × 2h × 100 reports = 600 hours | 1 reviewer × 0.5h × 100 reports = 50 hours | **-550 hours** |
| 2-5% number variance | 0.3% | **-90% variance** |
| 30% rework rate | 5% | **-83% rework** |
| $50 × 600 = $30,000 labor | $0.5 × 100 + $50 × 50 = $2,550 | **$27,450 saved** |
| Manager review variance: high | Standardized review: low | **Less manager second-guessing** |

→ **CFO 喜欢 ROI 数字. Pre-compute these for their specific use case before meeting.**

### 3.5 LLM 跟 Excel formula 的关系 (重要 mental model)

> "Think of LLM as **a layer on top of Excel formulas, not a replacement**.
>
> - Excel = deterministic numerical compute. We **keep that for the actual numbers**.
> - LLM = generates **commentary about** the numbers.
>
> Workflow:
>
> 1. **Excel / SQL / BI tool** computes the numbers — fully deterministic, audit-friendly.
> 2. **LLM reads the numbers + writes commentary** explaining trend / outliers / recommendations.
> 3. **Numbers in the report = Excel numbers**, never re-generated by LLM.
> 4. **Commentary** has slight prose variance.
>
> So your **financial truth remains deterministic**. LLM is the **narrator**, not the **calculator**."

→ 这是 critical reframe. CFO worry 是数字 randomness. **告诉他数字不是 LLM 生成的**, 立刻 calm down.

### 3.6 当客户的 use case 真的需要 0 variance

有时 (e.g., regulatory filing) 客户 absolutely 不能容忍 variance. 不要 push back. **Accommodate**:

> "For your annual report use case, **I agree — 0 variance is the right standard**. Here's the architecture:
>
> **Step 1**: Compute numbers via deterministic SQL / spreadsheet pipeline.
>
> **Step 2**: Generate commentary with **pinned seed + temperature = 0**.
>
> **Step 3**: Hash-store the output. **Once generated, it's frozen. Never regenerated.**
>
> Auditor sees: input + output + model_version + seed + temp + hash. Re-run any time with same parameters → identical output, byte-for-byte. **This is fully deterministic for this use case.**
>
> For other use cases (drafts, exploration, brainstorming), we use default mode with slight variance. Your team configures per use case via UI checkbox. **You pick the level**."

→ Accept the premise where CFO is right. Don't fight.

---

## ⚙️ Problem 4: Guardrails — Constraints, Validation, Human-in-Loop on Critical

**这是 architecture 层的 reassurance — 不是 trust the model, 是 trust the system around the model**.

### 4.1 4 类 guardrails

| Type | 目的 | 例 |
|---|---|---|
| **Input guardrail** | 拒绝 invalid input | 数据完整性检查 / schema validation |
| **Output guardrail** | 拒绝 invalid output | 数字 range check / format validation |
| **Constraint** | 强制 deterministic 部分 | 公式 deterministic compute / cached result |
| **Human-in-loop** | 关键决策 review | Low confidence trigger / high stake trigger |

### 4.2 Concrete guardrail examples (财务 use case)

```python
# guardrails.py

def input_guardrail(query):
    """Reject invalid input before model sees it."""
    # Schema check
    if not all(k in query for k in ['revenue', 'opex', 'period']):
        raise ValueError("Missing required fields")
    # Range check
    if query['revenue'] < 0 or query['revenue'] > 1e12:
        raise ValueError("Revenue out of expected range")
    return True

def output_guardrail(output, expected_schema):
    """Validate model output before downstream."""
    # Schema compliance
    if not matches_schema(output, expected_schema):
        retry_with_strict_prompt(output)

    # Numerical sanity
    if 'qoq_growth' in output:
        if abs(output['qoq_growth']) > 1.0:  # >100% growth
            flag_for_review(output, reason="Implausible growth")

    # Citation check
    if 'citation' in output:
        if not verify_citation_against_source(output):
            reject(output, reason="Citation hallucinated")

    return output

def deterministic_constraint(query, output):
    """Replace LLM-generated numbers with deterministic source."""
    deterministic_numbers = compute_via_sql(query)  # ← source of truth
    # Override any LLM-generated numbers with SQL-computed
    output = replace_numbers(output, deterministic_numbers)
    return output

def human_in_loop(output, confidence):
    """Route to human if low confidence or high stake."""
    if confidence < 0.95:
        return enqueue_for_review(output, priority="standard")
    if output.get('flagged') or output.get('amount', 0) > 1e6:
        return enqueue_for_review(output, priority="high")
    return finalize(output)
```

### 4.3 跟 CFO 讲 guardrails 的 script

> "I want to show you the **guardrails** around the model. Think of them as **internal controls** — same concept as SOX controls or your audit team's reconciliation checks.
>
> **4 layers**:
>
> **(1) Input control**: model never sees malformed data. Before it touches input, we validate schema + ranges + completeness. **Bad input gets rejected at the door**.
>
> **(2) Output validation**: model output gets checked before being saved. **Numbers verified against source data. Citations verified against documents. Schema enforced.**
>
> **(3) Deterministic core**: actual financial numbers come from your SQL pipeline, never from the model. **Model writes commentary about numbers, not the numbers themselves.**
>
> **(4) Human review for critical**: anything above $1M, anything with confidence < 95%, anything flagged unusual — **routes to your team for review before going downstream**.
>
> So even if the model itself has slight variance, **the system around it has 4 deterministic / human checks**. The model is a tool with safety; not a unilateral decision-maker.
>
> Your auditor sees these layers. **Each layer logs its decision**: input passed, output validated, numbers from SQL, human reviewed at $1M+. Full audit trail."

### 4.4 Guardrail 不是 ad-hoc, 是 systematic

跟客户 commit:

> "Guardrails are part of every deployment. **Standard configuration**:
>
> - Output schema: enforced per use case
> - Numerical sanity: range + delta checks
> - Citation verification: when relevant
> - Confidence threshold: configurable per use case (default 95%)
> - Stake threshold: configurable (default $1M for finance)
> - Audit log: 100% of queries
>
> **Configurable per use case**. Your team picks thresholds. Defaults are conservative — you can lower confidence threshold (more auto, less review) if you're confident in the model's domain, or raise (more review) for new domains."

### 4.5 Human-in-loop scale 计算

CFO 担心: "Won't human review become a bottleneck?"

**Response**:

> "Let me show the math.
>
> Your team currently does **100% manual review** — 100 reports × 2 hours each = 200 hours/week.
>
> With LLM + 95% confidence threshold:
> - 95% of queries → auto-finalize (no human time)
> - 5% → human review at 0.5h each
> - Total: 100 × 0.05 × 0.5 = **2.5 hours/week**
>
> **80x reduction in human time**, while **all critical decisions still see human eyes**. Better signal-to-noise for your team — they only review the cases that actually need judgment.
>
> If you want stricter — 90% confidence threshold → 10% review → 5 hours/week. Still 40x reduction.
>
> Your team picks the slider."

### 4.6 Demo 1 个 guardrail 报告 (CFO 看 dashboard)

```
Daily Guardrail Report — Acme Finance Commentary
────────────────────────────────────────────────
Date: 2026-05-20

Queries processed:           487
Input rejected:               3 (0.6%)
  Reasons: malformed schema (2), revenue out of range (1)

Output validation:
  Schema check passed:        484/484 (100%)
  Numerical sanity:           483/484 (99.8%)
  Citation verified:          480/484 (99.2%)

Auto-finalized (conf >95%):   459 (94.8%)
Human review queued:          25 (5.2%)
  Of which reviewed:          25
  Approved as-is:             21
  Edited:                     3
  Rejected:                   1

Audit log entries:            484 (100% complete)
Average human time:           0.42h/review
Total human time today:       10.5 hours
```

→ **CFO loves this**. Looks like SOX report.

---

## ⚙️ Problem 5: When to Push Back on Customer Premise vs Accommodate

**这是道德 + judgment 题: 客户不总是 right**.

### 5.1 客户 premise 类型分类

| Premise | 你应该 |
|---|---|
| "我们的数据必须 reproducible for audit" | **Accommodate** (真的需要 deterministic) |
| "All AI must be 100% deterministic" | **Push back** (over-generalized, missed nuance) |
| "AI is dangerous and shouldn't touch finance" | **Push back gently** (overreaction, propose hybrid) |
| "Just give us a chatbot with no audit" | **Push back** (you violate compliance for them) |
| "Trust the model, no human review needed" | **Push back** (you advocating for human-in-loop) |
| "We need full determinism even on prose" | **Accommodate** (some industries are this strict) |

### 5.2 Accommodate 的 framing

> "**For your audit-critical use case, your premise is correct**. Reproducibility is non-negotiable. Here's how we deliver it:
>
> - Pinned seed + temperature 0
> - Hash-stored output
> - SQL-deterministic numbers
> - Audit log with replay capability
>
> Variance = 0 for this use case. **Engineered, not promised.**
>
> For your **non-audit use cases** (brainstorming, exploration), we'd recommend default mode for better quality. But **you choose per use case**."

→ Don't fight on the right premise. Just engineer the solution.

### 5.3 Push back 的 art

When CFO has the wrong premise, push back **without 直接 disagreeing**:

**Wrong premise**: "All our AI must be 100% deterministic."

**Bad response**: "Actually that's not how AI works."

**Good response**:

> "I hear you. Before we lock that as a design constraint, can we walk through what 'all AI' includes?
>
> *(Listen as CFO lists use cases)*
>
> OK so I'm hearing:
> - Quarterly financial commentary
> - Customer support chat
> - Document drafting
> - Internal Q&A
>
> **The quarterly commentary** — yes, **0 variance, audit-critical**. We engineer for that.
>
> **The customer support chat** — if we lock to determinism, **customers get rigid robotic responses, deflect more, customer satisfaction drops**. The 1% variance in wording is the difference between 'AI-feel' and 'robot-feel'. Most peer banks accept that variance because of the user experience win.
>
> **Document drafting** — drafts are explicitly meant to vary. We'd lose the productivity.
>
> **Internal Q&A** — variance is actually fine because employees iterate.
>
> So I'd propose: **rather than 'all AI = deterministic'**, we do **per-use-case configuration**. For finance / audit-critical, 0 variance. For UX / drafts, default mode.
>
> Your audit team gets what they need. Your business teams don't get hamstrung. **Does that work?**"

→ Push back via **showing concrete cost** of the wrong premise + offering nuanced alternative.

### 5.4 Push back 红线: 当你 must say no

**Scenario**: CFO says "Just deploy LLM as autonomous decider for refund decisions. No human review."

**Response**:

> "I want to be direct: **I can't recommend that, and I won't deploy it**. Here's why.
>
> Refund decisions are **financial-impact decisions**. The model's accuracy is 95%+, which is high — but 5% wrong-decision rate on customer money creates:
>
> - Reputation risk (5/100 wrong refund denials → angry customers)
> - Regulatory risk (if monitor flags patterns)
> - Financial risk (5/100 wrong approvals → over-payment)
>
> **Industry best practice is**:
> - Auto-approve clear-cut cases (high confidence, low amount)
> - Human review for ambiguous (low confidence) or high stake (large amount)
>
> Even with a 99% accuracy model, you'd want human review on edge cases. **It's not a model quality issue — it's a deployment pattern**.
>
> **I'll engineer human-in-loop for refund. Or, I'll engineer this for a different use case where 95% accuracy is OK.** But I won't ship autonomous LLM on refund decisions — it's not safe, and it puts your business at risk."

→ Sometimes you say no. **Reputation > one deal**. But frame as 「我在保护你的 business」, not "I'm refusing to do work".

### 5.5 内部 align before pushing back

跟 CFO push back 前, **必须** internal align:

- **AE**: 不能跟你公开 contradict. 让 AE 知道你为啥 push back.
- **EM**: confirm engineering 不愿 ship over-permissive deployment.
- **Director**: pre-brief on your stance, get backing.

**绝不**: 跟 CFO push back 后, AE 当场 say "actually we can do that". 这是 organizational 灾难.

### 5.6 客户已经决定要 dangerous deployment, 你怎么办

**Scenario**: 即便你 push back, CFO 仍坚持 autonomous refund LLM.

**Escalation ladder**:

1. **Document your concerns in writing** to internal leadership + CFO
2. **Insist on staged rollout**: 5% traffic → measure 30 days → reassess
3. **Insist on emergency kill switch**: feature flag, you can disable in 1 minute
4. **Insist on real-time monitoring**: confidence + outcome metrics dashboard
5. **If still 拒绝 stage**: escalate to your CEO + their CEO. **This is "I won't put my name on this" moment**.
6. **Last resort**: politely decline to ship. Lose the deal. **Your reputation matters more**.

### 5.7 Self-check: 你 push back 太多吗?

| Self-check question | 信号 |
|---|---|
| 我 push back 是因为 customer 错, 还是因为我 lazy? | 如果 lazy → don't |
| Customer 的 premise 真的会害到他们吗? | 如果 yes → push back |
| 有没有 hybrid 方案我没想到? | 如果 yes → propose hybrid |
| 我的 push back 是基于 industry experience 还是 personal bias? | If bias → reconsider |
| 我会跟 CTO 朋友 backup 这个 push back 吗? | If yes → stand firm |

---

# Part 3 · 把 5 个问题串起来看

这 5 个问题其实是**同一个 CFO conversation 的 5 层 craft**:

1. **Analogies** (Problem 1) — Build mental model
2. **Concrete numbers** (Problem 2) — Anchor abstract with metric
3. **Variance as value** (Problem 3) — Reframe negative to positive
4. **Guardrails** (Problem 4) — System-level reassurance, not model-level
5. **Push back judgment** (Problem 5) — Know when to accommodate vs decline

每一层做对, **CFO 从 skeptic 变 advocate**. 每一层错, **CFO walks away**.

---

## 必问 clarifying questions

**1. CFO type**

> "What's the CFO's background — banking compliance? Tech startup? Big 4 audit? Each requires different framing."

**2. Use case specifics**

> "Is this for audit / regulatory artifact, or for internal exploration / draft?"

**3. Current process baseline**

> "What's the current variance in their manual process? We need that to compare."

**4. Pre-measured data**

> "Do I have consistency metrics for their specific use case? If not, can I measure before the meeting?"

**5. Internal alignment**

> "Has AE / EM aligned on what we can commit (2-mode system, audit log, etc)?"

---

## 5 步框架 (45-min answer 节奏)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify CFO type + use case + baseline |
| 5-15 min | Analogy + acknowledge concern + introduce variance vs decision split |
| 15-25 min | Concrete numbers (99.2% etc) + confidence calibration |
| 25-35 min | Architecture: 2-mode + guardrails + audit log + human-in-loop |
| 35-45 min | Push back judgment + customer chooses per use case + commitment |

---

## 简历专属 reframe

| 题 | Gao Xin 的经验 |
|---|---|
| Non-technical stakeholder explanation | **印尼 OJK monitor** + **多市场 ops teams** — 多数非技术 |
| Compliance / audit framing | Debt collection / BNPL 是 regulated industry, 你必懂 |
| Determinism for compliance | Voice agent 有 fixed-decision paths for regulated actions |
| Consistency metric | **ConvFinQA eval methodology** — consistency 是 measurable |
| Confidence calibration | Voice agent threshold-based escalation 你做过 |
| Push back on dangerous deployment | Indonesia refund tier scoping — 你 pushed back on "full autonomy day 1" |
| Variance vs human baseline | 你做过 LLM vs human ops on debt collection KPI |

**主动 quote**:

> "I had this exact conversation with the Indonesia regulatory body (OJK) when we deployed the voice agent. They worried about model 'inconsistency' — would **two customers** asking the same question get different financial answers?
>
> **My move** was 3 layers:
>
> **(1) Concrete numbers**: I showed them the 99% consistency rate on **numerical decisions**, with 0.4% mean deviation in the 1% that varied. **Pre-measured on Indonesia traffic specifically**, not generic benchmarks.
>
> **(2) Per-use-case mode**: For **regulated dialog paths** (decision to extend payment / waive fee), we **pinned the response template** — fully deterministic, scripted decision tree. For **natural conversation paths** (greeting / clarification / empathy), default mode with variance. **OJK could audit either path independently**.
>
> **(3) Variance vs human baseline**: I showed them that **the existing human call center had 8-15% inconsistency** across agents (same customer, different agents, different decisions). LLM at 1% was **strictly better**.
>
> **They signed off** because we gave them both — flexibility where it's value-add, determinism where compliance requires it, and **honest comparison to human baseline**.
>
> The lesson I'd apply to a CFO conversation: **don't argue variance is OK; engineer the variance away where required, and let it stay where it adds value. Make CFO pick per use case.**"

---

## 5 follow-ups

**Q1**: "Auditor demands all outputs be reproducible. Full determinism."

**A**: Agree + explain tradeoff:
- "Doable. **Pin seed + temperature = 0** for audit-flagged queries. Tradeoff: outputs become slightly more rigid, may feel less helpful. For audit specifically that's the right call."
- "What I'd suggest: **2-mode system**. **Default mode** for productivity (some variance). **Audit mode** for compliance-flagged queries (full reproducibility, with hash log). Your team **flags per query** or **per use case**."
- Specific commit: ship within 2 weeks.

**Q2**: "Show me the numbers — what's the actual numerical consistency rate?"

**A**: Don't ballpark:
- "Let me pull the data. Last 1000 production queries, run each 3x. **For numerical outputs**: 99.1% identical, 0.7% within ±1% of mean, 0.2% > 1% deviation."
- If you don't have data: "I'll have this measured + reported by Wednesday. Specifically on **your** use case, not generic."
- **Never fake numbers**. 一旦造数据被发现, 信用永久 gone.

**Q3**: "What if I get audited and the auditor sees different outputs?"

**A**: 3-tier defense:
- **Audit log**: every query timestamped + input + output + model version + seed + temp
- **Reproducibility on demand**: with audit log, re-execute identical input + params → identical output
- **Read-only artifacts**: production-final outputs (like annual report figures) hash-stored, immutable
- "Show your auditor **the artifact**, not a re-run. Artifact is by definition the signed version."

**Q4**: "Why not just always use determinism then?"

**A**:
- "For **creative / analytical** tasks, slight variation produces **better answers** — the model explores more solution space."
- "For **procedural / lookup / compliance** tasks, determinism is right."
- "**We give you per-query control**: deterministic for finance, default for general. Each use case gets the right mode."
- "Locking everything to determinism would cost you ~15% in answer quality on exploratory tasks — measurable in our benchmarks. Per-use-case is the right granularity."

**Q5**: "Our CTO says LLM is too unpredictable for finance. Should we cancel?"

**A**: Don't fight the rejection:
- "Your CTO is right to be cautious. LLM in finance is **about deployment patterns**, not about whether LLM is good. We can build the deterministic + audit-friendly version they want. **Can we get them in a 30-min call** so I can show specifically the architecture? I want to address their concerns, not just yours."
- "Specifically, I'd want to address: (1) deterministic mode for audit-critical, (2) guardrails + human-in-loop, (3) audit log + replay. If they still have concerns after that, **valid to walk away**. But let's give them the chance to evaluate the real architecture, not the generic 'AI is unpredictable' framing."
- Shifts conversation from "should we use this" to "**how** do we use this safely".

---

## ❌ 易错点 (top 12)

1. **Use "temperature" / "top-p" / "stochastic"** — CFO 听不懂 → 失信
2. **Argue "it's not a bug"** — defensive, CFO 反弹
3. **No concrete consistency 数字** — vague reassurance 没用
4. **No determinism option proposed** — CFO 没出路
5. **Patronize** ("you don't need to understand") — explosive
6. **No audit log story** — compliance ask 主要
7. **Promise 0 variability without changing architecture** — Second-day demo 又有 variance, 信用 gone
8. **Don't distinguish numerical vs prose variance** — easy to clarify, CFO 立刻 calm
9. **Don't quote human baseline** — miss reframe opportunity
10. **Don't show LLM is "narrator not calculator"** — miss critical mental model
11. **AE over-promise, you don't push back** — you 背锅
12. **Don't pre-measure metrics for their specific use case** — generic numbers are weak

---

## ✅ 加分项 (top 12)

1. **A·B·C·D framework** explicit (Acknowledge / Business-language analogy / Concrete bounds / Deterministic option)
2. **3 analogies stacked** (financial advisor + auditor + email drafts)
3. **Concrete metrics** (99.1% etc, pre-measured)
4. **Variance vs human baseline** comparison
5. **"Narrator not calculator"** mental model
6. **2-mode system** (default + audit/deterministic)
7. **Hash-stored artifacts** for immutability
8. **Confidence-based routing** with human-in-loop
9. **Guardrails as 4-layer system** (input / output / deterministic / HITL)
10. **Per-query / per-use-case control** — flexibility
11. **Quote Indonesia OJK experience** (real Gao Xin work)
12. **Push back when CFO premise is wrong** (over-determinism) + accommodate when right (audit)

---

## 一句话总结

> **CFO's concern 不是技术 problem, 是 mental model 冲突**. 他的世界是 deterministic (spreadsheet, ERP), LLM 的世界是 stochastic.
>
> 你的 job 不是说服他 "stochastic is fine", 是**给他 mental model 工具区分 use case + 给他 deterministic 路径**:
> - For audit/regulatory: 0 variance via pinned seed + cached artifact
> - For productivity: default mode beats human baseline 10x with proper guardrails
>
> Variance is feature where users want fluency, eliminated where compliance requires. **CFO picks per use case, you engineer both.**

---

## Cheat Sheet (印 1 页)

```
A·B·C·D framework:
  Acknowledge concern ("I understand why this looks like a defect")
  Business-language analogy (FA / auditor / email drafts)
  Concrete bounds (99.1% identical, 0.3% mean deviation)
  Deterministic option (pin seed + cache result)

Useful analogies (stack 3):
  Financial advisor: same conclusion, different wording
  Two auditors: same flagged issues, different reports
  Email drafts vs sent: variance in drafting, frozen in archive

Words to AVOID:
  temperature, top-p, stochastic, sampling
  "by design", "trust us", "black box"
  "AI is unpredictable" (defensive even if true)

Words to USE:
  reasoning vs lookup
  consistency rate
  audit log
  artifact / signed document
  replay
  narrator vs calculator
  guardrails
  confidence-based routing

Concrete metrics to quote (pre-measure):
  Numerical consistency: 99.1%
  Categorical decision consistency: 99.7%
  Confidence calibration: ±2pp
  Numerical mean deviation: 0.3%
  Time stability: <0.2%/week

LLM-as-narrator framing:
  Numbers from SQL/Excel (deterministic source of truth)
  LLM writes commentary about numbers
  Numbers NEVER regenerated by LLM
  Financial truth = deterministic

2-mode system:
  Default mode: temp=0.3, slight variance, productivity
  Audit/compliance mode: temp=0, pinned seed, hash-stored
  Per-query or per-use-case selector

Variance vs human baseline:
  Human: 70% identical, 2-5% deviation
  LLM: 99% identical, 0.3% deviation
  LLM 10x better than current process

Confidence-based routing:
  conf > 95% → auto-finalize
  conf < 95% → human review queue
  any flag → human review priority
  amount > $1M → mandatory human review

4 guardrail layers:
  Input: schema + range validation
  Output: schema enforcement + citation check
  Deterministic core: numbers from SQL not LLM
  Human-in-loop: low conf or high stake

Audit log fields:
  timestamp, input, output, model_version, seed, temp,
  confidence, guardrail_results, reviewer (if HITL),
  outcome, hash

For audit:
  Show artifact (hash-stored), not a re-run
  Replay on demand using audit log params

Push back when:
  Customer wants 100% determinism on UX (rigid robot)
  Customer wants autonomous LLM on financial decisions
  Customer skips audit log
  Customer skips human-in-loop on high stake

Accommodate when:
  Customer demands 0 variance for audit artifact ✓
  Customer demands SQL-deterministic numbers ✓
  Customer demands hash-stored result ✓
  Industry has strict reproducibility ✓

红线:
  - Promise 100% reliable
  - Faking consistency metrics
  - Skipping audit log
  - Patronizing CFO
  - AE over-promise + you silent
  - Autonomous LLM on financial decisions
```
