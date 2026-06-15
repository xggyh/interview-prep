# 🍎 HM Q22 · Tell me about working with very unclear or shifting requirements.

> **类别**: Behavioral · **考点**: STAR · BNPL「让客服更聪明」一句话需求 → 拉 ticket 数据收敛范围 + 架构用 config/RAG 吸收变化而非改代码 · ⚠️ [✏️] 数字背前替换成真实值

## 🧠 这题在测什么 / 面试官想看到

Apple 想看你**面对模糊不慌**：能不能主动把一句话诉求**收敛成可交付的范围**（而不是等别人想清楚，也不是自己拍脑袋猜），以及能不能**设计出吸收变化的架构**（需求会一直变，好工程师让变化落在 config/数据/RAG 上，而不是每次改代码重发）。强答案：S 是真实的一句话需求 → 用数据收敛 → 架构层面让后续变化便宜。弱答案：「需求不清我就去问 PM，问清了就做」——太被动，没有架构思维。陷阱：把「应对模糊」讲成纯沟通技巧而漏掉**工程设计如何让系统对变化鲁棒**——后者才是 senior 信号，也是这题的关键差异点。

## 📋 English Answer (背诵稿, 主答 ~80-90 秒, STAR)

> **60 秒脊柱 (背死这句)**: *The requirement was one line — "make support smarter with AI." I converged scope with ticket data, not meetings, and — the senior part — I architected so shifting requirements land in config and RAG, not code. The intent-router-plus-RAG-fallback design itself absorbs the ambiguity.*

**⭐ STAR 一眼回忆卡**

| | |
|---|---|
| **S** | BNPL 启动需求就一句话: "make customer support smarter with AI". 无范围/无指标/各想各的. |
| **T** | 把一句话变成能建、能量的东西; 且明知范围会一直变. |
| **A** | ① 拉 **ticket 数据**收敛范围 (高频 intent→workflow agent, 长尾→FAQ RAG) + 和 product/ops 前置定指标. ② 架构让变化落在 **config/RAG/tool 不在代码**: 改 intent=config, 改政策=知识库热更, 新动作=tool. |
| **R** | 一句话→上线可量化系统; 范围变动主要靠 config+知识库吸收, 不重构. **让变化变便宜**才是真考验. |
| **学到** | 模糊时别等也别猜——拿让范围显而易见的数据, 把确定会变的部分架构成易改的. |

**Situation.** "When we kicked off the BNPL chatbot, the requirement I got was essentially one line: **'make customer support smarter with AI.'** That was it. No defined scope, no target metric, no agreement on which problems to solve first — and product, ops, and engineering each had a different picture in their head of what 'smarter' meant."

**Task.** "My job was to turn that one-liner into something we could actually build and measure — without guessing wrong and burning a quarter, and knowing the scope would keep moving as we learned."

**Action.** "I did two things deliberately.

**First, I converged the scope with data, not with meetings.** Instead of debating what to build in the abstract, I **pulled the support ticket data** and looked at what customers actually contacted us about. The volume concentrated in a handful of intents — order lookup, refunds, disputes — with a long tail of general questions. That turned a vague ambition into a concrete plan: automate the high-volume, well-defined intents with workflow sub-agents, and handle the long tail with FAQ RAG. Now product and ops could argue about something real, and we agreed on a first scope and the metric — case-resolution rate — grounded in where the actual demand was.

**Second, and more importantly, I designed the architecture so shifting requirements wouldn't mean rewrites.** I knew the intent list would change, policies would change, new flows would get requested — so I built the system so most of that lands in **configuration and data, not code**. New or changed intents are routing config; new policies and FAQ content go into the **RAG knowledge base**, which updates without touching or redeploying the model; new actions are tools the sub-agents can call. So when requirements shifted — and they did, constantly — most changes were a config or content update, not an engineering cycle. The intent router plus RAG-fallback structure was itself a way to *absorb* the ambiguity: we didn't have to enumerate every possible request up front, because anything unrecognized had a safe home in the FAQ path."

**Result.** "We went from a one-line ask to a shipped, measured system, and — the part I'm proud of — when scope shifted, we mostly absorbed it through config and knowledge-base updates rather than re-architecting. The design made change cheap, which is the real test when requirements are unstable. And defining the metric *with* product and ops up front meant 'smarter' stopped being subjective."

(可延伸) "The lesson I carry: when requirements are vague, don't wait for them to firm up and don't guess — go get the data that makes the right scope obvious, and architect so that the things you *know* will change are cheap to change. Ambiguity is a given; my job is to make the system tolerant of it."

## 🇨🇳 中文要点 (理解 + 记忆骨架)

**两个动作 = 这题的灵魂**：(1) 用**数据**收敛范围；(2) 用**架构**吸收变化。第二点是 senior 分水岭，别漏。

**STAR 骨架**：
- **S**：BNPL chatbot 启动时，需求就一句话——**"make customer support smarter with AI"**。无范围、无目标指标、product/ops/eng 各想各的「smarter」。
- **T**：把这句话变成**能建、能量**的东西，别猜错烧一个季度，且明知范围会一直变。
- **A**（核心，两件事）：
  - **① 用数据收敛，不靠开会吵**：拉**客服 ticket 数据**看用户真正在问什么 → 量集中在几个 intent（order lookup / refund / dispute）+ 长尾通用问题。模糊诉求变具体方案：高频明确 intent 用 workflow sub-agent 自动化，长尾用 FAQ RAG。product/ops 终于能就**真东西**讨论，定下首版范围 + 指标（case-resolution rate）。
  - **② 架构让变化不等于重写**（更重要）：明知 intent 会变、政策会变、新流程会来 → 让大部分变化落在 **config 和数据，不是代码**。新增/改 intent = 路由 config；新政策/FAQ = 进 **RAG 知识库**（更新不动模型、不重发）；新动作 = sub-agent 可调的 tool。需求一直变，但多数变更是 config/内容更新，不是工程周期。**intent router + RAG fallback 本身就是吸收模糊的结构**——不必前期穷举所有请求，没识别的有 FAQ 这个安全归宿。
- **R**：从一句话到上线可量化系统；范围变动时主要靠 config + 知识库更新吸收，而非重构——**让变化变便宜，才是需求不稳时的真考验**。和 product/ops 一起前置定指标，让「smarter」不再主观。

**复盘句**：需求模糊时——别等它清晰、也别猜，去拿**让正确范围显而易见的数据**，并把**你确定会变的部分**架构成易改的。模糊是常态，我的工作是让系统对它鲁棒。

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: How did you get product and ops to actually agree on a scope?**
"The ticket data did most of the work — it's hard to argue against 'this is what customers actually contact us about.' I anchored the conversation on volume and resolvability: which intents are both high-volume and well-defined enough to automate safely. We agreed to start where impact and tractability overlapped, and I made the first scope explicitly a *first* scope — a starting point we'd expand from — so nobody felt their priority was dropped, just sequenced."

**Q: Give a concrete example of a requirement that shifted, and what it cost you.**
"A new intent or a changed policy — say a refund rule changes, or ops wants a new dispute sub-flow. Because policies lived in the RAG knowledge base and intents were routing config, those landed as a content or config update, not a model change or redeploy. A genuinely new *action* — something requiring a new backend call — did cost real engineering, because that's a new tool. So I'd be honest: the design made the *common* changes cheap; truly new capabilities still cost what they cost. The win was not paying engineering cost for the changes that happen most often."

**Q: Doesn't pushing everything into config/RAG just move the complexity somewhere harder to debug?**
"It's a real trade-off — config and knowledge-base content become things you now have to govern and test. So I treated them as first-class: the FAQ content went through the same eval as the model, and routing config had its own regression checks. The point isn't 'no complexity,' it's putting the *frequently-changing* complexity somewhere you can update and validate fast, instead of in code that needs a deploy. I'd rather debug a knowledge-base entry than ship a hotfix."

## ⚠️ 边界 & 红线 (honest limits + what NOT to say)

- 别把「应对模糊」讲成纯沟通技巧（「我就去多问 PM」）——必须带**架构吸收变化**这一层，否则不是 senior 答案。
- 别假装架构能让**所有**变化免费——主动承认「真正的新能力/新 tool 仍要花工程」，体现诚实 + 判断力（Apple 加分）。
- 别把自己讲成「等需求清晰才动手」——要主动用数据去**制造**清晰。
- 别编 ticket 数量/intent 占比的精确数字——用定性（「volume concentrated in a handful of intents」）或 [✏️ 核实]。
- 不要漏掉「和 product/ops 一起定指标」——这是把模糊业务诉求落地的关键，也命中 JD。

## 🎯 面试官按什么打分 (自检清单, 背前对一遍)

- ☑ 你**主动制造清晰** (拉数据收敛), 不是被动等需求 → 主动性
- ☑ 你有**架构吸收变化**这一层 (config/RAG/tool), 不只沟通技巧 → senior 信号
- ☑ 你**和 product/ops 一起定指标**, 把模糊业务诉求翻成工程目标 → 跨职能协作 (JD)
- ☑ 你诚实承认**新能力仍要花工程**, 没把架构吹成万能 → 判断力 + humility
- ☑ 有可迁移的**复盘** (拿数据 + 把会变的部分做易改) → 自我迭代
- ☒ 红旗: 「需求不清我就一直等」/「我猜了一个方向就开干」/「架构让一切都免费」

## ✅ 加分钩子 (主动抛, steer 到强项)

- 主动抛 **「让变化落在 config/RAG/tool，不在代码」**——这是这题最高分的工程洞见，体现平台/架构思维，对上 JD 的 scalable deployment。
- 强调 **「intent router + RAG fallback 本身就是吸收模糊的结构」**——把行为题变成你 BNPL 多 agent 架构的展示。
- 顺势带 **「用 ticket 数据把一句话需求收敛成可量化范围」+「和 product/ops 前置定指标」**——直接命中 JD 强调的跨非技术 stakeholder 协作（也为 Q24 铺垫）。
- 复盘句「让变化变便宜」呼应 Apple 「incorporate latest models / 持续演进」的核心诉求。
