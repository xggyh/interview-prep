# 🍎 HM Q19 · How do you evaluate a multi-turn conversational agent? Offline and online.

> **类别**: GenAI / ML Concepts · **考点**: golden set + LLM-as-judge + 人工抽样 + 在线 A/B + per-turn vs task-level · ⚠️ [✏️] 数字背前替换成真实值

## 🧠 这题在测什么 / 面试官想看到

JD **明确**写了要 LLM eval，所以这题几乎必问，而且要答得有体系。面试官想看你区分**离线（上线前）和在线（上线后）**两条线，并且懂**多轮的难点**——单轮看着对、整段任务却失败。强答案：golden set 回归 + LLM-as-judge 规模化 + 人工抽样校准 + 在线 A/B + 业务指标；并且讲清 **per-turn 指标 ≠ task-level 指标**。弱答案：只说「我看 accuracy」或「让 GPT 打个分」就完了。陷阱：把多轮当成多个独立单轮来评（忽略上下文累积、状态、最终任务是否完成）。Gao 真做过 eval harness，这题要把它讲成主场。

## 📋 English Answer (背诵稿, 主答 ~60-90 秒 + 可延伸)

> **60 秒脊柱 (背死这句)**: *Offline gates the release, online proves it. Three offline layers — golden set, LLM-judge, human-calibrate. Online — A/B on business metrics. And always score two levels: per-turn vs task-level, because every turn can look right and the task still fails.*

**🗺️ Eval 全景一图**

```
                 ┌──────────── OFFLINE (gate 发布) ────────────┐   ┌──── ONLINE (真用户验证) ────┐
  per-turn 层 ──▶ │ golden set 回归 · LLM-judge · 人工抽样 calibrate │   │ A/B on 真流量              │
  (这条对吗?)     │   ↑ 同一 rubric                              │   │ 业务/行为指标 (非模型分):   │
                 │                                            │ ▶ │  task completion / 正确动作  │
  task 层    ──▶ │ golden set 回归 · LLM-judge (整段是否解决意图)  │   │  / escalation率 / 业务结果  │
  (整段解决了吗?) └────────────────────────────────────────────┘   │ + 在线 judge 抽样 + 人工抽查 │
                              ▲                                    └──────────┬────────────────┘
                              └────────── 真实失败回灌 golden set ◀──────────────┘ (闭环, 缩小离线-在线 gap)
```

"I split it into offline — what gates a release — and online — what tells me it's actually working with real users. And the thing that makes *multi-turn* hard is that turn-level quality and task-level success are different metrics: every turn can look fine and the conversation still fails to resolve the user's problem. So I measure both.

**Offline, three layers.** First, a **golden set** — a curated set of representative conversations with known good outcomes, including the nasty edge cases and past failures. That's my regression gate; nothing ships if it regresses here. Second, **LLM-as-judge** for scale — I can't human-label thousands of dialogues every iteration, so a judge scores dimensions like *task success, faithfulness/groundedness, tone, and whether the right tool was called*. Critically I score at two levels: **per-turn** (was this response correct and grounded?) and **task-level** (did the whole conversation resolve the intent?). Third, **human sampling** to calibrate — I validate the judge against human labels on a sample, and only trust it where they agree, with humans as the ground-truth anchor.

**Online, after launch.** This is where truth lives. I run **A/B tests** on real traffic and watch **business and behavioral metrics**, not just model scores — task completion rate, correct-action rate, escalation-to-human rate, and the downstream business outcome. On the chatbot that was case-resolution rate; on the voice agent, repayment conversion and automation rate. I also keep online **LLM-judge sampling** plus human review of a slice of live conversations, so offline and online use the *same rubric* — that consistency is what lets me trust that an offline win predicts an online win.

I built this end to end. On the BNPL chatbot I defined the metrics and the eval harness *with product and ops* — that partnership mattered, because 'correct' for a refund dispute is a business definition, not just a model one. And on the voice agent the whole post-training loop was **eval-driven**: I'd construct data, train, and let the eval harness tell me whether SFT or a DPO-style pass actually moved the metric before shipping."

(可延伸) "Two failure modes I specifically design against. One — **judge gaming**: an LLM-judge can be fooled by confident, verbose answers, so I calibrate against humans and keep adversarial examples in the set. Two — **offline-online gap**: golden sets drift from reality, so I feed real failures back into the golden set continuously. Eval is a living asset, not a one-time script."

## 🇨🇳 中文完整版 (口播稿, 与英文对应)

> **60 秒脊柱 (背死这句)**: *离线 gate 发布，在线证明它真行。离线三层 —— golden set、LLM-judge、人工 calibrate。在线 —— 在业务指标上做 A/B。而且永远打两个层级：per-turn 和 task-level，因为每一轮都可能看着对、整段任务还是失败。*

"我把它拆成离线 —— 决定一个版本能不能发 —— 和在线 —— 告诉我它在真实用户身上到底行不行。而让*多轮*这件事变难的，是轮级的质量和任务级的成功是两个不同的指标：每一轮都可能看着挺好，整段对话却没能解决用户的问题。所以这两个我都测。

**离线，三层。** 第一，一个 **golden set** —— 一批精挑的、有代表性的对话，带着已知的好结果，里面包括那些恶心的 edge case 和过去的失败案例。这是我的回归 gate；在这上面只要退步了，任何东西都别想发。第二，**LLM-as-judge** 来做规模化 —— 我没法每一次迭代都人工标几千段对话，所以让一个 judge 去打这些维度的分：*task success、faithfulness/groundedness、tone、以及有没有调对 tool*。关键是我在两个层级上打分：**per-turn**（这一条回应正确吗、贴证据吗？）和 **task-level**（整段对话解决了那个意图吗？）。第三，**人工抽样**来 calibrate —— 我拿人工标注在一个样本上去 validate 这个 judge，只在它和人一致的地方信它，让人工当 ground truth 的锚。

**在线，上线之后。** 真相在这里。我在真实流量上跑 **A/B 测试**，看**业务和行为指标**，不只是模型分 —— task completion rate、correct-action rate、escalation-to-human rate，以及下游的业务结果。在 chatbot 上那是 case-resolution rate；在 voice agent 上是 repayment conversion 和 automation rate。我同时也保留在线的 **LLM-judge 抽样**加上对一部分线上对话的人工 review，这样离线和在线用的是*同一套* rubric —— 正是这种一致性，才让我敢相信'离线赢能预测在线赢'。

这套我是端到端建起来的。在 BNPL chatbot 上，我是**和 product、ops 一起**定义指标和 eval harness 的 —— 那个合作很关键，因为对一个退款争议来说，'正确'是一个业务定义，不只是一个模型定义。然后在 voice agent 上，整个 post-training 闭环都是 **eval 驱动**的：我会去造数据、训、然后让 eval harness 告诉我，到底是 SFT 还是一个 DPO-style 的 pass 真正推动了指标，再决定上不上线。"

(可延伸) "有两个失败模式是我特意去防的。一 —— **judge 被刷分**：一个 LLM-judge 会被自信、啰嗦的答案骗到，所以我拿人工去 calibrate，并且在集合里保留对抗样本。二 —— **离线-在线 gap**：golden set 会和现实漂移，所以我持续把真实的失败回灌进 golden set。Eval 是一个活的资产，不是一次性的脚本。"

## 🇨🇳 中文要点 (理解 + 记忆骨架)

**总骨架**：离线（gate 发布）+ 在线（真用户验证）。**多轮难点先点破**：**per-turn 对 ≠ task-level 成功**——每轮都像对的、整段任务仍可能失败，所以两个层级都要测。

**离线三层**：
1. **Golden set**：精选代表性对话 + 已知好结果 + 脏 edge case + 历史失败 → **回归 gate**，退步就不发。
2. **LLM-as-judge**（规模化）：打分维度 = task success / faithfulness / tone / 是否调对工具。**两个层级都打**：per-turn（这条回应对不对、贴不贴证据）+ task-level（整段是否解决意图）。
3. **人工抽样校准**：拿人工标注 validate judge，只在一致处信它，人工当 ground truth 锚。

**在线（上线后，真相所在）**：
- 真流量 **A/B**，看**业务/行为指标**不只模型分：task completion / correct-action / escalation rate / 下游业务结果。chatbot = case-resolution rate；voice agent = repayment conversion + automation rate。
- 在线也跑 **LLM-judge 抽样 + 人工抽查**，离线在线**用同一套 rubric** → 一致性才让你信「离线赢能预测在线赢」。

**真实例子**：BNPL chatbot — 我**和 product/ops 一起**定义指标 + eval harness（「退款争议算不算对」是业务定义不是模型定义）；voice agent 整个 post-training 是 **eval 驱动**——造数据→训→让 harness 告诉我 SFT 或 DPO-style 是否真的推动指标再上线。

**两个主动防的失败模式**：(1) **judge 被刷分**（自信啰嗦的答案会骗过 judge）→ 人工 calibrate + 留对抗样本；(2) **离线-在线 gap**（golden set 会漂）→ 把真实失败持续回灌 golden set。Eval 是活资产，不是一次性脚本。

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: What exactly does the LLM-judge score, and how do you keep it reliable?**
"Narrow, well-defined dimensions with a rubric — task success, groundedness, tone, tool-call correctness — each as a small focused judgment rather than one vague 'is this good' score. Reliability comes from calibration against human labels, keeping the judge's task narrow (narrow judgments are close to entailment, which models do well), and holding out a human-labeled set to detect drift over time."

**Q: How do you evaluate the agent when the *user* part is simulated — do you use a user simulator?**
"For multi-turn you can, yes — an LLM user-simulator lets you generate many conversation trajectories cheaply and stress-test recovery, interruptions, topic switches. I treat simulator results as a fast signal, not truth — they over-represent how the simulator behaves. So simulator for breadth and regression, real-traffic A/B and human review for the actual verdict."

**Q: Per-turn looks great but task success is low. How do you debug that?**
"That's the classic multi-turn trap and exactly why I score both. I'd trace failed conversations turn by turn to find *where* it breaks — usually context loss as the conversation grows, a wrong tool call mid-dialogue, or the agent answering the literal turn but losing the user's overall goal. The fix is usually in state/context management or routing, not in single-response quality."

**Q: Offline said ship, online regressed. What happened and what do you do?**
"Offline-online gap — my golden set wasn't representative of live distribution, or the judge rewarded something users don't. First I roll back or shift traffic down. Then I pull the regressed live conversations into the golden set and re-examine the judge rubric against them. The permanent fix is the feedback loop: real failures continuously refresh the offline set so the gap shrinks."

**Q: How does eval change at Apple — on-device, privacy?**
"Privacy constrains how you can look at real conversations — you may not be able to log raw user content the way a cloud product does. So you lean more on synthetic/golden sets, opt-in or aggregated signals, and on-device or privacy-preserving evaluation. The rubric and the offline/online split are the same; the data-access surface is tighter, which actually pushes you to invest more in high-quality curated eval sets up front."

**Q: What's the very first eval you'd stand up on a brand-new agent?**
"A small golden set of representative conversations with known good outcomes, including a handful of known-hard cases. It's cheap, it's a regression gate from day one, and it forces the team to agree on what 'good' even means — which is half the value. I'd grow it from real failures as they appear rather than trying to make it comprehensive up front."

## ⚠️ 弱答 vs 强答 (一眼看出什么措辞赢)

| 问 | 🔴 弱答 (初级) | 🟢 强答 (Gao 该说) |
|---|---|---|
| 怎么评 | 「看 accuracy / 让 GPT 打个分」 | 「离线 golden+judge+人工 三层 + 在线 A/B 业务指标, **同一 rubric**」 |
| 多轮难点 | (没提) | 「**per-turn 对 ≠ task-level 成功**, 两层都打」 |
| judge 可信吗 | 「LLM 打分挺准」 | 「人工 calibrate, 留 ground truth 防 drift, 防 **judge gaming**」 |
| 看什么指标 | 「模型分高就行」 | 「在线看 **业务/行为**: completion / 正确动作 / escalation率 / 业务结果」 |

## ⚠️ 边界 & 红线 (honest limits + what NOT to say)

- 别把多轮评成「一堆独立单轮」——必须明确 **per-turn vs task-level** 两层，否则暴露不懂多轮。
- 别把 **LLM-judge 当绝对真理**——主动讲 calibrate + 人工 ground truth + 防 judge gaming。
- 别只说离线不说在线，或反之——两条线都要，且强调用**同一 rubric**。
- 如果被追问统计显著性 / A/B 样本量算法细节超出深度，老实说「显著性和分流由实验平台标准流程保证，我聚焦在指标定义和 rubric 上」——划清边界。
- 不要假装所有指标都有现成数字——业务指标用 [✏️ 核实] 标注，宁可诚实。

## ✅ 加分钩子 (主动抛, steer 到强项)

- 主动抛 **「和 product/ops 一起定义指标」**——直接命中 JD 强调的「partner with non-technical stakeholders」+ 证明你懂「correct 是业务定义」。
- 把 **voice agent 的 eval 驱动 post-training 闭环** 讲出来——SFT/DPO 是否上线由 eval 说了算，这是 senior + JD（LLM eval）双重命中。
- 顺势点 **离线-在线 gap 的 feedback loop**（真实失败回灌 golden set）——体现你做的是「活的 eval 系统」不是一次性脚本，是平台思维信号。
