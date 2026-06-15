# 🍎 HM Q18 · How do you detect and reduce hallucinations in a customer-facing agent?

> **类别**: GenAI / ML Concepts · **考点**: grounding + citation 强制 + faithfulness eval (LLM judge) + 低置信转人工 · ⚠️ [✏️] 数字背前替换成真实值

## 🧠 这题在测什么 / 面试官想看到

customer-facing + money-touching 的场景，hallucination 不是「质量问题」是「信任与合规问题」。面试官想看你把它拆成**预防 → 检测 → 兜底**三段闭环，而不是只说「加个 prompt 让它别瞎编」。强答案：grounding（只在检索到的内容上生成）+ citation 强制 + 用 LLM-as-judge 做 faithfulness 离线评估 + 在线低置信转人工，并且承认**消不到零、所以要有 fallback**。弱答案：以为 prompt 一句「don't hallucinate」就解决，或者假装能 100% 消除。陷阱：把 hallucination 和 retrieval error 混在一起——检索错了不是模型幻觉，要分开治。

## 📋 English Answer (背诵稿, 主答 ~60-90 秒 + 可延伸)

> **60 秒脊柱 (背死这句)**: *You can't hit zero, so build a loop: prevent (grounding + citations + facts-from-tools), detect (LLM-judge faithfulness + human-calibrated), contain (low confidence → escalate to a human). Separate facts from phrasing.*

**🔁 三段闭环一图**

```
        PREVENT (生成时)              DETECT (离线+在线)            CONTAIN (低置信)
   ┌────────────────────┐      ┌────────────────────┐     ┌────────────────────┐
   │ grounding: 只答检索内容 │      │ LLM-judge faithfulness │     │ 弱 grounding / 库外    │
   │ enforce citations ↩  │ ───▶ │ vs golden set         │ ──▶ │ → 不让它猜            │
   │ 涉钱数字 = tool, 非模型 │      │ + 人工抽样 calibrate    │     │ → escalate to human   │
   └────────────────────┘      │ + unsupported-claim率  │     └────────────────────┘
                                └──────────┬───────────┘              │
                                           └──── 真实失败回灌 golden set ◀┘ (闭环)
```

"I treat it as a closed loop with three stages — **prevent, detect, contain** — because you can't drive hallucination to zero, so the system has to be safe even when it happens.

**Prevent — at generation time.** The single biggest lever is **grounding**: don't let the model answer from its parametric memory, make it answer *from retrieved context*. So RAG, with the instruction to answer only from the provided documents and to say 'I don't know' when the context doesn't cover it. On top of that I **enforce citations** — every claim has to point back to a source chunk. That does two things: it constrains the model to stay on the evidence, and it gives me something checkable. For anything money-touching — a balance, a due date, a refund amount — I don't let the LLM *generate* the number at all; I have it call a tool and render the authoritative value. The LLM phrases the sentence, the system owns the fact.

**Detect — offline and online.** Offline I run a **faithfulness eval**: an LLM-as-judge checks 'is every statement in this answer supported by the retrieved context?' against a golden set, and I also verify citations actually resolve. Online I attach a **confidence signal** — retrieval scores, whether citations grounded, judge score on a sample of live traffic — and I track an unsupported-claim rate as a real metric, not a vibe.

**Contain — when confidence is low.** This is the part people forget. If the model is about to answer with weak grounding, or the question is outside the knowledge base, I **don't let it guess** — I route to a safe fallback: 'I don't have that, let me get you to a specialist,' i.e. **escalate to a human**. A confident wrong answer in a customer-facing money product is far more expensive than a humble handoff.

I built exactly this on our BNPL chatbot. The FAQ path was **grounded generation over RAG** — answers came from retrieved policy docs, not free-form generation — and order-specific facts came from tool calls against the system of record, never from the model. And the whole thing sat behind an intent router, so anything we weren't confident about could fall back rather than improvise."

(可延伸) "If I had to name the highest-leverage single fix: separate facts from phrasing. Most damaging hallucinations in a support agent are *wrong specifics* — a number, a date, a policy. Pull those from tools and retrieval, and you've removed most of the blast radius before you even talk about model quality."

## 🇨🇳 中文完整版 (口播稿, 与英文对应)

> **60 秒脊柱 (背死这句)**: *你做不到零，所以要搭一个闭环：prevent（grounding + citation + 事实走 tool）、detect（LLM-judge 测 faithfulness + 人工 calibrate）、contain（低置信 → 转人工）。把事实和措辞分开。*

"我把它当成一个三段的闭环来做 —— **prevent、detect、contain**，预防、检测、兜底 —— 因为你没法把 hallucination 压到零，所以系统必须在它发生的时候依然是安全的。

**Prevent —— 在生成的时候。** 最大的那根杠杆是 **grounding**：别让模型用它的参数记忆（parametric memory）来答，逼它*基于检索到的上下文*来答。所以是 RAG，加上指令'只根据提供的文档来回答，上下文没覆盖到的就说我不知道（I don't know）'。在这之上我还**强制 citation** —— 每一句陈述都得指回一个 source chunk。这干了两件事：它把模型约束在证据上，同时给了我一个可以核查的东西。任何涉钱的东西 —— 一个余额、一个到期日、一个退款金额 —— 我根本不让 LLM 去*生成*那个数字；我让它调一个 tool，把那个权威值渲染出来。LLM 负责把句子说顺，系统负责拥有那个事实。

**Detect —— 离线加在线。** 离线我跑一个 **faithfulness eval**：用一个 LLM-as-judge 去对着 golden set 检查'这个答案里的每一句话，是不是都被检索到的上下文支持'，我还会去验证 citation 是不是真的能 resolve（指得到）。在线我挂一个**置信度信号** —— 检索分、citation 有没有落地、对一部分线上流量抽样跑 judge 分 —— 然后我把 unsupported-claim rate 当成一个真正的指标来追，不是凭感觉。

**Contain —— 当置信度低的时候。** 这是大家最容易忘的一段。如果模型正要在 grounding 很弱的情况下作答，或者这个问题在知识库之外，我**不让它瞎猜** —— 我把它路由到一个安全的 fallback：'这个我没有，我帮你转一个专员'，也就是**转人工（escalate to a human）**。在一个涉钱的、面向客户的产品里，一个自信的错答，远比一个谦逊的转接要贵得多。

这套我在我们的 BNPL chatbot 上是原样建出来的。FAQ 那条路是 **RAG 上的 grounded generation** —— 答案来自检索到的政策文档，不是自由生成 —— 而订单相关的事实来自打 system of record 的 tool call，绝不来自模型。整个东西坐在一个 intent router 后面，所以任何我们没把握的，都可以 fall back 而不是即兴发挥。"

(可延伸) "如果非要我点出那个杠杆最大的单一改法：把事实和措辞分开。客服 agent 里最有破坏力的 hallucination 大多是*错的具体值* —— 一个数字、一个日期、一条政策。把这些从 tool 和检索里拿，你在还没开始谈模型质量之前，就已经把大半个 blast radius 给砍掉了。"

## 🇨🇳 中文要点 (理解 + 记忆骨架)

**三段闭环骨架（核心）**：**prevent → detect → contain**。前提先说清：**消不到零，所以系统在它发生时也得安全**。

**Prevent（生成时）**：
- 最大杠杆 = **grounding**：别让模型用 parametric memory 答，让它**基于检索内容**答（RAG + 只答 provided docs + 不覆盖就说 I don't know）。
- **强制 citation**：每句话指回 source chunk → 既约束模型贴证据，又给我可核查的东西。
- 涉钱的数字（余额/到期日/退款额）**不让 LLM 生成**——调 tool 取权威值，LLM 只负责措辞，系统负责事实。

**Detect（离线 + 在线）**：
- 离线 **faithfulness eval**：LLM-as-judge 判「每句话是否被检索上下文支持」+ 核 citation 是否真能 resolve（对 golden set）。
- 在线挂 **confidence 信号**（检索分 / citation 是否落地 / 抽样 judge 分），把 unsupported-claim rate 当**真指标**追。

**Contain（低置信）**——最多人忘的一段：grounding 弱 / 问题在知识库外 → **不让它猜**，走安全 fallback：「我没有这个，转专员」= **转人工**。在涉钱客服里，自信的错答远比谦虚的转接贵。

**真实例子（BNPL）**：FAQ 路径 = **RAG 上的 grounded generation**（答案来自检索到的政策文档，不是自由生成）；订单事实走 tool call 打 system of record，绝不靠模型；整体在 intent router 后面，不确定的就 fallback 不即兴。

**一句话最高杠杆**：把**事实和措辞分开**。客服里最伤的幻觉是「错的具体值」——数字/日期/政策从 tool+检索拿，blast radius 在谈模型质量前就先砍掉一大半。

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: How do you actually measure hallucination — what's the metric?**
"Faithfulness / groundedness rate on a labeled golden set: for each answer, is every claim supported by the retrieved context? I'd report unsupported-claim rate and citation-resolution rate. On live traffic I sample and run the same LLM-judge, and I'd also watch downstream proxies — escalation rate, customer correction/complaint rate. I'd put a real number here from our BNPL eval [✏️ 核实 faithfulness %]."

**Q: Isn't using an LLM to judge an LLM circular — what if the judge hallucinates?**
"It's a real risk, so I calibrate the judge against human labels first and only trust it where it agrees with humans. The judge's job is narrow and easier than the original task — 'is X supported by this passage?' is close to entailment, not open generation — so it's more reliable than the generator. And I keep a human-labeled sample as ground truth to catch judge drift."

**Q: Retrieval returned the wrong document and the model faithfully summarized it. Is that a hallucination?**
"No — that's a *retrieval* failure, and it's important to separate them because the fix is different. The model was faithful to bad evidence. I'd catch it on the retrieval side — relevance scoring, reranking, top-k tuning — not by touching the generator. Grounding protects you from invention; it does not protect you from wrong sources. Both need their own eval."

**Q: Can you fine-tune the hallucination away?**
"Not directly — facts that change can't be trained in, and fine-tuning a model to 'be confident' often makes it *more* fluently wrong. Fine-tuning helps adjacent behaviors — saying 'I don't know' more reliably, citing more consistently — but the load-bearing fixes are grounding, tool-sourced facts, and the human fallback."

**Q: How does this change on-device / at Apple?**
"The principles hold, and a couple get sharper. On device you can do **on-device retrieval over the user's own data**, which is both a grounding win and a privacy win — the facts never leave the device. And with a smaller on-device model, the 'escalate when unsure' branch — to a larger server model in Private Cloud Compute, or to a human — matters even more, because a 3B model has a smaller safe envelope than a frontier one."

**Q: What's your single highest-leverage fix if you only had time for one?**
"Separate facts from phrasing. Pull every specific — number, date, policy — from a tool or retrieval, and let the model only do the wording. Most damaging support-agent hallucinations are *wrong specifics*, and that one move removes most of the blast radius before you even touch model quality."

## ⚠️ 弱答 vs 强答 (一眼看出什么措辞赢)

| 问 | 🔴 弱答 (初级) | 🟢 强答 (Gao 该说) |
|---|---|---|
| 怎么减 | 「加 prompt 让它别瞎编」 | 「**grounding + citation 强制 + 涉钱数字走 tool**, 三件套」 |
| 怎么测 | 「人工看一看」 | 「LLM-judge 测 faithfulness vs golden set, **人工 calibrate** + 追 unsupported-claim 率」 |
| 消除程度 | 「能基本消除」 | 「**消不到零**, 所以低置信 → escalate to human 兜底」 |
| 检索错了 | 「也算幻觉, 调模型」 | 「那是 **retrieval 失败**, 治检索 (rerank/top-k), 不是治模型」 |

## ⚠️ 边界 & 红线 (honest limits + what NOT to say)

- **绝不**说「我能把幻觉降到零」——立刻显得不懂。说「消不到零，所以有检测 + 兜底」。
- 别把 **retrieval error 和 hallucination 混为一谈**——这是 senior 的分水岭，主动区分。
- 别声称 fine-tune 能根治幻觉——会被追问到崩。
- LLM-judge 别讲成绝对真理——主动提「先用人工标注 calibrate，留人工 ground truth 防 judge drift」。
- 不要只停在「加 prompt 让它别瞎说」——这是初级答案，必须带 grounding + tool-sourced facts + fallback 三件套。

## ✅ 加分钩子 (主动抛, steer 到强项)

- 主动抛 **「facts vs phrasing 分离 / 涉钱数字走 tool 不走模型」**——这是 money-touching 场景最高分的洞见，直接对上 Apple Customer Systems。
- 用 **BNPL grounded generation + tool call 打 system of record** 做实证，把概念题落到你真做过的产品。
- 顺势提 **on-device retrieval = grounding + privacy 双赢**，主动把隐私这个 Apple 关键词自然带进来。
