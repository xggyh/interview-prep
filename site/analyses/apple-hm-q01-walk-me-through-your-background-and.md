# 🍎 HM Q1 · "Walk me through your background and what you're working on right now."

> **类别**: Opening / 自我介绍 · **考点**: 60-90 秒讲清主线，落点到 voice agent + agentic，与 Apple 这个 team 强相关 · ⚠️ [✏️] 数字背前替换成真实值

## 🧠 这题在测什么 / 面试官想看到

这是 HM 第一题，定全场基调。Andrew / Yu Ping 想在 90 秒内判断：你是不是"会讲故事的资深人"——能不能把 5 年经历压成一条清晰主线，而不是流水账念简历。

- **强答案** = 一条贯穿线（CV → 风控 → LLM/agent → 现在 0→1 voice agent），层层递进，最后一句精准砸到"这正是你们 team 在做的事"。
- **弱答案** = 从本科开始按时间顺序背、每段平均用力、最后没有落点。
- **陷阱 1**：讲太久——超过 90 秒 HM 会走神，第一印象就散了。
- **陷阱 2**：把 voice agent 一笔带过，却花时间在早期 CV / 实习上——把篇幅给了最不相关的部分。

记住一条铁律：**最近、最相关的项目（voice agent）要占大约 60% 的篇幅**，早期经历压成铺垫。这一题不是讲"你做过什么"，是讲"你为什么正好适合这个岗位"。

## 📋 English Answer (背诵稿, 主答 ~60-90 秒 + 可延伸)

> 按句换行 = 方便逐句背诵、控制节奏。整段练到 ~75 秒收尾。

"Sure.
I'm an Expert Algorithm Engineer at TikTok / ByteDance Global Payment in Singapore — about five years in, and currently the technical POC for our GenAI work in payments.

My path has been pretty deliberate.
I started in computer vision — my master's at Kyushu was in CV, and at Shopee I shipped an ID-document tamper-detection model for Indonesia banking onboarding: 95% true-accept at 1% false-accept, in production.
That taught me how to ship ML that touches real money and real compliance.

Over the last two years I moved fully into LLMs and agents.
I built a BNPL customer-service chatbot — intent gating into workflow sub-agents with tool calling, and general queries into a RAG path.
Then I co-designed our internal agent platform — orchestration, tool integration, memory, observability, eval pipelines — and I drove LLM inference acceleration on GPUs with vLLM and SGLang.

What I'm working on right now, and what I'm most excited about, is a zero-to-one production **voice agent** for debt collection.
I lead a team of three.
It runs across **seven markets** — Chinese, English, Japanese, Korean, Malay, Indonesian, Thai.
I own the full stack: streaming ASR, TTS and VAD; the LLM dialogue policy; tool orchestration; and the foundation-model post-training — SFT, DPO-style alignment, eval-driven iteration, plus RL-style optimization over the multi-step workflow.

So it's multi-turn, multilingual, agentic, latency-sensitive, and money-touching — which is basically the problem your team is solving for Apple customers.
That's why this conversation is interesting to me."

*(可延伸，如果 HM 说 "tell me more")*: "Happy to go deep on any of it — the part I'd geek out on most is how we got end-to-end latency low enough to feel like a real phone call, while keeping the dialogue compliant."

**备用：30 秒压缩版**（如果 HM 明显赶时间或只想要一句话）：
"Five years in payments ML at ByteDance, currently the GenAI technical POC. I came up through computer vision and fraud, then moved fully into LLMs and agents. Right now I lead a three-person team building a zero-to-one production voice agent for debt collection across seven languages — I own it end to end, from post-training to the streaming latency budget. Multi-turn, multilingual, agentic, money-touching — basically your team's problem."

## 🇨🇳 中文完整版 (口播稿, 与英文对应)

> 按句换行 = 方便逐句背诵、控制节奏。整段练到 ~75 秒收尾。

"好的。
我现在是 TikTok / 字节跳动 Global Payment 新加坡的 Expert Algorithm Engineer，做了大概五年，目前是我们 payments 这边 GenAI 方向的 technical POC。

我这条路走得挺有意图性的。
我是 computer vision 出身——硕士在九州大学做的就是 CV，在 Shopee 我上线过一个针对印尼 banking onboarding 的证件防篡改模型：95% true-accept、1% false-accept，是跑在生产上的。
那段经历教会我怎么去 ship 一个会碰到真金白银、真合规的 ML 系统。

过去这两年我完全转到了 LLM 和 agent。
我做过一个 BNPL 的客服 chatbot——用 intent gating 把请求分流，工作流类的进 workflow sub-agent 做 tool calling，通用问题走 RAG 那条路。
然后我参与设计了我们内部的 agent 平台——orchestration、工具集成、memory、observability、eval pipeline，同时我还在 GPU 上推动 LLM 推理加速，用的是 vLLM 和 SGLang。

我现在手上在做、也是我最兴奋的，是一个 zero-to-one 的生产级 **voice agent**，用在债务催收。
我带一个三个人的 team。
它跑在 **七个市场**——中文、英文、日文、韩文、马来文、印尼文、泰文。
整个 stack 都是我 own 的：streaming ASR、TTS、VAD；LLM 的对话 policy；tool orchestration；还有底座模型的 post-training——SFT、DPO-style alignment、eval 驱动的迭代，以及对这个多步 workflow 做的 RL-style 优化。

所以它是 multi-turn、multilingual、agentic、对 latency 敏感、又碰钱的——这基本上就是你们 team 在为 Apple 用户解决的问题。
这也是为什么这次聊天对我来说特别有意思。"

*(可延伸，如果 HM 说 "tell me more")*: "任何一块我都很乐意往深里讲——我自己最想聊的，是我们怎么把 end-to-end latency 压到让它感觉像在打一通真正的电话，同时还能让对话保持 compliant。"

**备用：30 秒压缩版**（如果 HM 明显赶时间或只想要一句话）：
"在字节做了五年 payments ML，现在是 GenAI 的 technical POC。我是从 computer vision 和风控一路走过来的，后来完全转到了 LLM 和 agent。现在我带一个三人 team，做一个 zero-to-one 的生产级 voice agent，用于债务催收，跨七种语言——我端到端都 own，从 post-training 一直到 streaming 的 latency budget。multi-turn、multilingual、agentic、又碰钱——基本上就是你们 team 的问题。"

## 🇨🇳 中文要点 (理解 + 记忆骨架)

骨架四段，**前三段各压成一两句，第四段讲透**：

1. **现在身份（1 句）**：ByteDance Global Payment，5 年，GenAI 的 technical POC。一句话立住资历和领域。
2. **出身 + 一个硬数字（铺垫）**：CV 出身（Kyushu 硕士 + Shopee **95% TAR@1%FAR** 上线）。关键不是炫 CV，而是那句落点——"shipped ML that touches **real money + compliance**"。这是为了和 Apple 的 customer / payments 场景同频：我一直在做"出错有后果"的 ML。
3. **过渡到 LLM/agent（一口气带过）**：BNPL chatbot（intent gating + sub-agent + RAG）→ 内部 agent platform → vLLM/SGLang 推理加速。目的：证明你不是"只会调 API"，而是从 infra 到应用全栈，且做过多 agent 编排。
4. **落点（重点，最大篇幅）**：voice agent，0→1，带 3 人 team，**7 markets**，全栈 own（ASR/TTS/VAD + dialogue + post-training + RL）。最后一句把它和 Apple 的 team 直接对齐：multi-turn / multilingual / agentic / latency-sensitive / money-touching。

**记忆口诀**：**CV → 风控 → LLM → voice agent**，前三个各一句，最后一个讲透，结尾一句"这就是你们正在做的事"。

**节奏提示**：四段之间留半秒停顿，不要一口气冲完——HM 需要时间在脑子里给你贴标签。

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: That's a lot of areas — what would you say is your single strongest area?**
**中**: 你涉猎的领域挺多——要说你最强的单个领域是哪个?
"Production agentic systems, end to end. Specifically: taking a multi-turn LLM agent from prototype to something reliable enough to touch money, in multiple languages. The voice agent is the clearest example — I own it from the post-training data all the way to the streaming latency budget."
> 🇨🇳 端到端的生产级 agentic 系统。具体来说：把一个 multi-turn 的 LLM agent，从原型做到可靠到能碰钱的程度，而且是跨多语言的。voice agent 就是最清楚的例子——从 post-training 的数据，一直到 streaming 的 latency budget，整个都是我 own 的。

**Q: Why did you move from CV into LLMs?**
**中**: 你为什么从 CV 转到了 LLM?
"Two reasons. One — in payments, the highest-leverage problems shifted from perception to reasoning and conversation; that's where the customer pain moved. Two — I wanted problems where the system has to *act*, not just classify. Agents do that. I didn't abandon CV — the discipline of shipping ML under a hard precision/recall bar carried straight over."
> 🇨🇳 两个原因。第一——在 payments 里，杠杆最高的问题，从感知转移到了推理和对话；客户的痛点就是往那边走的。第二——我想做那种系统必须去*行动*的问题，而不只是分类。Agent 就是干这个的。我并没有抛弃 CV——那套在硬性 precision/recall 标准下 ship ML 的功夫，是直接迁移过来的。

**Q: You're a POC — is that an IC role or a lead role?**
**中**: 你是 POC——这是一个 IC 的角色，还是一个 lead 的角色?
"Both, honestly. I'm hands-on in the code and the model training, and I'm also the technical point of contact — I make the architecture calls and I'm accountable for them across the three of us. I can be specific about which decisions were mine versus the team's if that's useful." *(为 Q7 埋钩子)*
> 🇨🇳 老实说，两者都是。我在代码和模型训练上是 hands-on 的，同时我也是技术上的 point of contact——架构上的决策是我拍板，并且在我们三个人里我要为这些决策负责。如果有用的话，我可以具体说清楚哪些决策是我的、哪些是团队的。

**Q: Five years and you've changed domains twice — are you going to get bored at Apple too?**
**中**: 五年里你换了两次领域——你在 Apple 是不是也会做腻?
"The opposite read, I'd argue. The thread through all of it is the same: applied ML where mistakes have real consequences. I didn't job-hop — I followed where the hard, consequential problems went, inside payments. On-device agentic systems for customers is the next hard version of that, not a different thing."
> 🇨🇳 我会说，恰恰相反。贯穿这一切的主线是同一条：出错有真实后果的 applied ML。我不是在跳来跳去——我是在 payments 内部，跟着那些又难、又有后果的问题走。面向客户的 on-device agentic 系统，是这件事的下一个更难的版本，不是另一码事。

## ⚠️ 边界 & 红线 (honest limits + what NOT to say)

- 别把简历从头到尾背一遍——本科、每段实习、每个项目平均用力，是这一题最大的失分点。早期 CV / Laboro 实习压成半句话或干脆不提。
- 别在开场白里报任何没核实的 voice agent 指标（latency ms、automation %、conversion %）。开场只用**简历真实数字**：7 markets、team of 3、95% TAR@1%FAR。具体延迟 / 转化数字留到 HM 追问 Q3/Q4/Q8 时再给，且届时口头标注 "approximately"。
- 别说 "I love Apple products / I've always wanted to work at Apple"——HM 听腻了，且 Q2 专门处理动机，开场说显得空洞。
- 别用 "we" 笼统带过 voice agent——这是你的主项目，要敢说 "I lead" / "I own"。
- 如果紧张容易讲超时：练到 **75 秒**收尾，留 15 秒余量。宁可短，HM 一定会追问。

## ✅ 加分钩子 (主动抛, steer 到强项)

- "multilingual across seven markets, including Chinese" —— JD 明确要 **LLM in Chinese for Greater China + fluent Chinese**，开场就让对方知道你天然满足这条硬性要求，不用他们来问。
- "I own the foundation-model post-training *and* the streaming latency budget" —— 一句话同时覆盖 JD 的 fine-tuning 和 latency 两个核心词，暗示你是少见的"训练 + 工程"双修，不是单边人才。
- 结尾那句 "that's basically the problem your team is solving" —— 主动把球递到项目 deep-dive，引导 HM 顺势问 voice agent（你最强的牌），把面试节奏握在自己手里。
