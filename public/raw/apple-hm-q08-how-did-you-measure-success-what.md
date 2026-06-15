# 🍎 HM Q8 · "How did you measure success? What does 'the agent is working' actually mean here?"

> **类别**: Project deep-dive / eval + 指标体系 · **考点**: 多指标（任务完成 / 动作正确 / 还款转化 / 合规违规率 / 延迟 SLO），且讲清它们如何互相制衡 · ⚠️ [✏️] 数字背前替换成真实值

## 🧠 这题在测什么 / 面试官想看到

JD 明确要 "LLM eval"。HM 想看你**有没有一套多维度、会互相打架的指标体系**，而不是只盯一个数。强答案 = 给出一组指标，分清**业务指标 / 质量指标 / 系统指标 / 红线指标**，并且——这是关键——讲清它们**如何 trade-off**（比如只优化还款转化会撞合规红线），以及哪个是**不可妥协的约束**（合规违规率）。弱答案 = "我们看自动化率"或"我们看准确率"——单指标，没有制衡意识。陷阱：(1) 把"the agent is working"等同于一个数；(2) 忘了合规/安全类指标是**约束（constraint）不是优化目标**；(3) 说不清离线 eval 和线上指标的关系。Apple 会钻"如果这俩指标冲突你优化哪个"。

## 📋 English Answer (背诵稿, 主答 ~60-90 秒 + 可延伸)

> 数值全部 [✏️ 核实]——可只讲指标是什么、怎么算、怎么 trade-off，不报硬数。按句换行方便背。

"'Working' is never one number for an agent like this.
And the most important thing is that some of these metrics *fight each other* — so the design is really about which ones are goals and which are hard constraints.

I tracked four families.

**Business outcome** — the reason it exists.
Repayment conversion, and automation rate — what fraction of calls the agent resolves end to end without a human.
Those are the dollars and the cost savings.

**Task quality** — is it doing the job correctly.
Task-completion rate — did the call achieve its intent — and correct-action rate: when the agent took an action, like logging a promise-to-pay or pulling a balance, was it the right action with the right data.
Correct-action is the one I watch hardest, because a confident wrong action is worse than no action.

**System and experience.**
A latency SLO — perceived time-to-first-audio under our bar, tracked at p95, not just the mean — plus ASR accuracy and interruption-handling quality.
Because if it feels laggy or talks over people, none of the business numbers matter.

**The red line** — and this one is a *constraint*, not a metric I trade: compliance-violation rate.
I don't optimize this against conversion.
It has to stay at or near zero, and a regression is a release blocker, no matter how good the conversion looks.

The key relationship is the tension.
I could juice repayment conversion by letting the agent be more aggressive or over-promise — and that would blow up compliance and customer trust.
So the way I frame it: compliance and a vulnerable-customer-safety bar are **hard constraints**; within those, I optimize repayment conversion and automation; and the latency SLO and correct-action rate are quality gates that keep it from being a bad experience.
'The agent is working' means it's resolving calls and recovering money — *while* staying inside compliance, taking correct actions, and feeling like a real-time conversation.
All four at once — not the best conversion number with violations hiding underneath."

*(可延伸，离线 vs 线上)*: "And I separate offline from online — an eval harness with labeled cases for action-correctness and compliance that gates every release, then the live business and latency metrics in production. The offline harness is what lets me move fast without shipping a regression on the red line."

## 🇨🇳 中文完整版 (口播稿, 与英文对应)

> 数值全部 [✏️ 核实]——可只讲指标是什么、怎么算、怎么 trade-off，不报硬数。按句换行方便背。

"对这样一个 agent 来说，'working'从来都不是一个数。
而最重要的一点是，这些指标里有些是**互相打架的**——所以设计的本质，其实是想清楚哪些是目标、哪些是 hard constraint。

我盯四个家族的指标。

**Business outcome（业务结果）**——它存在的理由。
repayment conversion，以及 automation rate——也就是有多大比例的通话是 agent 端到端搞定、不需要人介入的。
这两个就是钱，和省下来的成本。

**Task quality（任务质量）**——它有没有把活干对。
task-completion rate——这通电话有没有达成它的意图——还有 correct-action rate：当 agent 采取了一个动作，比如记一笔 promise-to-pay 或者拉一个余额，它是不是用对的数据做了对的动作。
correct-action 是我盯得最紧的一个，因为一个自信地做错的动作，比不做动作更糟。

**System 和 experience（系统与体验）。**
一条 latency SLO——感知到的 time-to-first-audio 要在我们那条线以下，看的是 p95，不只是均值——再加上 ASR accuracy 和打断处理的质量。
因为如果它感觉卡，或者老压着人说话，那些业务数字一个都不重要了。

**红线（red line）**——这一个是个 **constraint**，不是一个我会拿去交易的指标：compliance-violation rate。
我不会拿它去跟 conversion 做权衡优化。
它必须保持在零、或者接近零，而一旦它回退，就 block 发布，不管 conversion 看起来多漂亮。

关键的关系，就是这种张力。
我大可以靠让 agent 更激进、或者去过度承诺，来把 repayment conversion 刷上去——但那会把 compliance 和客户信任炸掉。
所以我是这么 frame 的：compliance 和一条 vulnerable-customer-safety 的线是 **hard constraint**；在这些约束之内，我去优化 repayment conversion 和 automation；而 latency SLO 和 correct-action rate 是 quality gate，防止它变成一个糟糕的体验。
'agent is working'的意思是：它在解决通话、在把钱收回来——**与此同时**还待在 compliance 之内、采取正确的动作、感觉像一场实时对话。
四个一起达标——而不是一个最漂亮的 conversion 数字，底下藏着 violation。"

*(可延伸，离线 vs 线上)*: "而且我把离线和线上分开——一个带标注 case 的 eval harness，用来测 action-correctness 和 compliance，它 gate 住每一次发布，然后是生产里实时的业务和 latency 指标。正是这个离线 harness，让我能快速推进，又不会在红线上 ship 一个 regression。"

## 🇨🇳 中文要点 (理解 + 记忆骨架)

**开场定调（最重要）**：agent 的"working"从来不是一个数，关键是**有些指标互相打架**，所以设计的本质是分清**哪些是优化目标、哪些是硬约束**。

四个指标家族（数值全 [✏️]）：

| 家族 | 指标 | 角色 |
|---|---|---|
| **Business outcome** | repayment conversion、automation rate | 存在的理由（钱 + 省人力） |
| **Task quality** | task-completion rate、**correct-action rate** | 做得对不对（correct-action 最该盯，**自信地做错比不做更糟**）|
| **System / experience** | latency SLO（first-audio p95）、ASR 准确率、打断质量 | 体验，崩了业务数字无意义 |
| **红线 Red line** | **compliance-violation rate** | **约束，不是优化目标**，必须≈0，回退就 block 发布 |

**核心是张力（必须讲）**：我可以靠让 agent 更激进/过度承诺来拉高 repayment conversion——但那会炸掉合规和信任。所以框架是：
- 合规 + 脆弱客户安全 bar = **hard constraints**；
- 在约束内，优化 repayment conversion + automation；
- latency SLO + correct-action = quality gates 防止体验变差。

**"working"的定义**：在合规内、动作正确、像实时对话的前提下，**同时**解决通话 + 回收欠款。四个一起达标——不是"转化最高但底下藏着违规"。

**延伸**：离线 vs 线上分开——离线 eval harness（labeled cases 测 action-correctness + 合规）gate 每次发布；线上跑 business + latency 指标。离线 harness 是"能快但不在红线上回退"的保障。

记忆口诀：**四家族(业务/质量/系统/红线) + 一句张力(合规是约束不是目标，否则用激进话术刷转化会炸) + working=四个同时达标**。

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: If conversion goes up but compliance violations also tick up, what do you ship?**
"You don't ship it. Compliance is a constraint, not a dial — a higher conversion bought with violations is a net loss, because one violation in a regulated collections context can cost far more than the incremental recovery, in fines and trust. So that release is blocked, and I'd go find conversion that doesn't come from crossing the line — better grounding, better objection handling, not more aggression."

**Q: How do you measure 'correct-action' — who decides what the right action was?**
"Labeled eval cases. We build a set of call situations with the correct expected action — log promise-to-pay, escalate, pull balance, do nothing — defined with ops and compliance, not by me alone. The agent's action is scored against that. In production I sample real calls for the same review. The hard part is the label definition, so I co-own it with the people who own the policy, which also means the metric is defensible when someone challenges it." *(复用 BNPL 经历: defined metrics + eval harness with product/ops)*

**Q: Automation rate — isn't higher always better? Why not push it to 100%?**
"No, and this ties back to vulnerable customers. Some calls *should* go to a human — hardship, disputes, distress. If I optimized automation rate naively, I'd be automating exactly the conversations that need a person, which is both an ethics and a brand problem. So automation rate is good only *within* the safety constraint — I'd rather a lower automation number than auto-handling a call that should've escalated."

**Q: How do offline eval scores correlate with the live business metrics?**
"Imperfectly, and I treat that gap as information. Offline gives me fast, repeatable signal on action-correctness and compliance so I can gate releases; it doesn't fully predict conversion, which depends on real customer behavior. So offline is the safety/quality gate, online is the outcome truth, and when they diverge — offline looks fine but conversion drops — that's a signal my eval set is missing a real-world case, and I go add it."

**Q: What single metric would you put on a dashboard for an exec?**
"I wouldn't give them one — I'd give them two with a rule: repayment conversion as the headline, with compliance-violation rate right next to it as a gate, framed as 'conversion only counts while this stays at zero.' A single number invites optimizing it into a corner. The pairing communicates the actual deal: outcome, bounded by the red line."

## ⚠️ 边界 & 红线 (honest limits + what NOT to say)

- **别给单指标答案**——"我们看自动化率/准确率"是最大失分。必须是体系 + 张力。
- 所有具体数值（conversion %、automation %、violation rate、latency ms）标 [✏️]，口头不报硬数除非已对齐真实 dashboard。可以讲指标**是什么**、**怎么算**、**怎么 trade-off**，而不报具体值——这样既安全又显专业。
- 合规违规率必须定位成**约束**不是优化目标——把它当可 trade 的指标是 Apple 眼里的危险信号。
- correct-action 的 label 谁定：**如实说和 ops/compliance 共同定义**，别说"我一个人定标准"——既不可信也不 defensible。
- 离线 eval 和线上的相关性：**主动承认 imperfect**，别假装离线分数能完美预测转化。Apple 喜欢这种诚实。
- 别声称达到了某个具体 SLO/违规率数字除非真实——可说"目标是 p95 under bar / violations at or near zero"。

## ✅ 加分钩子 (主动抛, steer 到强项)

- 开场"some of these metrics fight each other" —— 立刻显示你有 senior 的指标体系思维，而非单点优化，正中 JD 的 "LLM eval" 要求。
- "compliance is a constraint, not a dial" + "a confident wrong action is worse than no action" —— 两句强金句，把安全/质量意识钉死，且自然回扣 Q6。
- 主动复用 BNPL 经历"defined metrics + eval harness with product/ops" —— 证明你不止在 voice agent 一个项目做过 eval 体系，是成体系的能力。
- 离线 harness gate 发布 + 线上指标 truth + 二者 divergence 是信号 —— 展示完整的 eval-driven 工程闭环，Apple 的 scalable deployment + monitoring 关切直接命中。
- "I'd give the exec two numbers with a rule, not one" —— 把指标设计上升到"如何向上沟通"，显示你懂指标会被如何使用与滥用，是难得的成熟度信号。
