# 🍎 HM Q16 · When do you fine-tune vs RAG vs prompt engineering? Give me your decision criteria.

> **类别**: GenAI / ML Concepts · **考点**: 一棵清晰的决策树 — 知识问题→RAG, 格式/风格/窄任务/延迟→fine-tune, prompt 永远先试 · ⚠️ [✏️] 数字背前替换成真实值

## 🧠 这题在测什么 / 面试官想看到

这是 Apple 几乎**必考**的判断题。他们不要你背三个定义，要看你**面对一个真实需求时按什么轴去选**，以及会不会**先上最便宜的手段**。强答案：给一棵决策树 + 一句话判据 + 一个你真做过的例子。弱答案：把三者讲成「平行的三选一」，或者一上来就 fine-tune（成本/运维意识缺失）。最大的陷阱是把它们当互斥——真实系统几乎总是 **prompt + RAG + 偶尔一个小 fine-tune** 叠在一起。面试官也想听到你提**评估**：你怎么知道该升级到下一档。

## 📋 English Answer (背诵稿, 主答 ~60-90 秒 + 可延伸)

> **60 秒脊柱 (背死这句)**: *Prompt first, RAG for knowledge, fine-tune for behavior — and they stack, they're not a menu. I only move down a level when the one above hits a measured ceiling.*

"My default order is prompt engineering first, then RAG, then fine-tuning — cheapest and fastest to iterate at the top, most expensive and slowest at the bottom. I only move down a level when the level above hits a real ceiling I can measure.

The decision axis is one question: **what kind of gap am I closing?**

- **Knowledge gap** — the model doesn't know our policies, our order data, facts that change weekly — that's **RAG**. You never fine-tune facts that change; you retrieve them. Retrieval also gives me citations and lets me update the knowledge base without touching the model.
- **Behavior gap** — I need a specific output format, a consistent tone, reliable tool-call JSON, or a narrow task done well — that's where I consider **fine-tuning**. Fine-tuning teaches a *skill* or a *style*, not a *fact*.
- **Prompt engineering** is always the first probe — system prompt, few-shot examples, structured output. It's free, it's instant, and very often it's enough. And if I *can't* get it working in the prompt, that failure tells me what the harder problem actually is, so it's never wasted.

Two more pulls toward fine-tuning specifically: **latency and cost**. If a big model in a long prompt works but is too slow or too expensive, I'll fine-tune a *smaller* model on that narrow task to hit the same quality cheaper. That's the classic distillation play, and it's the bridge to serving — cheaper per token, lower latency, smaller footprint.

I lived this on our BNPL chatbot. The FAQ side was a pure knowledge problem — policies, refund rules, dispute flows that change — so that was **RAG**, no fine-tuning. The intent routing was a narrow, high-volume classification task where latency mattered, so that leaned toward a **small fine-tuned classifier** rather than asking a big LLM every turn. Same product, two different problems, two different tools. And on the voice agent I did real post-training — SFT plus DPO-style alignment — because there the gap was *behavior*: multilingual style, when to call which tool, staying compliant. You can't prompt your way to that reliably across seven markets."

(可延伸) "The honest cost of fine-tuning isn't the training run — it's that you now own a model. Every base-model upgrade, you re-evaluate or re-train. So I treat fine-tuning as a commitment, not a quick fix, and I only take it when prompt + RAG have provably plateaued."

**🌳 决策树 (口头可画, 面试官常让你 walk through)**

```
新需求来了
  └─ 先问: prompt 能解决吗? ──── 能 ──→ ✅ Prompt engineering (system prompt / few-shot / structured output)
        │ 不能
        ▼
     在补哪种 gap?
        ├─ 知识 gap (会变的事实/政策/私有数据) ──→ ✅ RAG  (retrieve, 别 fine-tune; 给 citation, 知识库可热更)
        ├─ 行为 gap (格式/语气/工具调用/窄任务) ──→ ✅ Fine-tune (教 skill/style, 不教 fact)
        └─ 太慢/太贵 (大模型长 prompt 能用但成本高) ──→ ✅ Fine-tune 小模型 (蒸馏: 同质量更省)
        ▼
     真实系统 = 三者叠加: (fine-tuned or base) 模型 + RAG 喂上下文 + 精心 prompt
```

**一眼对照表**

| 手段 | 治什么 | 成本/迭代速度 | 知识可热更? | 何时升级到下一档 |
|---|---|---|---|---|
| **Prompt** | 先探边界, 临时调行为 | 免费 / 秒级 | — | prompt 调到头, 行为仍不稳 |
| **RAG** | 知识 gap (会变的事实) | 低 / 改数据即可 | ✅ 改知识库, 不动模型 | 检索质量到顶但行为/格式仍差 |
| **Fine-tune** | 行为 gap + 降本降延迟 | 高 / 训练+长期维护 | ❌ 别 fine-tune 事实 | — (最后一档, 慎用) |

## 🇨🇳 中文完整版 (口播稿, 与英文对应)

> **60 秒脊柱 (背死这句)**: *先 prompt，知识问题上 RAG，行为问题才 fine-tune —— 而且它们是叠加的，不是三选一的菜单。只有上面那档撞到一个我能量出来的天花板，我才往下走一级。*

"我的默认顺序是：prompt engineering 先上，然后 RAG，最后才 fine-tune —— 最上面这层最便宜、迭代最快，最下面这层最贵、最慢。只有上面那一档撞到一个我能真实量出来的天花板，我才会往下走一级。

判据其实就一个问题：**我在补的是哪一种 gap？**

- **知识 gap** —— 模型不知道我们的政策、我们的订单数据、那些每周都在变的事实 —— 这是 **RAG**。会变的事实你永远不要去 fine-tune，你要去 retrieve。检索还顺带给我 citation，而且我更新知识库的时候根本不用动模型。
- **行为 gap** —— 我需要一个特定的输出格式、一个稳定的语气、可靠的 tool-call JSON、或者把一个窄任务做到很精 —— 这才是我考虑 **fine-tune** 的地方。fine-tune 教的是一个*技能*或者一个*风格*，不是一个*事实*。
- **prompt engineering** 永远是第一个探针 —— system prompt、few-shot 例子、structured output。它免费、它即时，而且很多时候它就够了。退一步讲，就算我*没法*在 prompt 里把它搞定，那个失败本身也告诉我真正难的问题到底在哪，所以这一步从来不浪费。

另外还有两股力专门把我往 fine-tune 拉：**latency 和 cost**。如果一个大模型配一个长 prompt 能用，但是太慢或者太贵，我就会拿一个*更小*的模型在那个窄任务上做 fine-tune，用更便宜的代价打到同样的质量。这就是经典的蒸馏打法，它也是通往 serving 的桥 —— 每 token 更便宜、latency 更低、footprint 更小。

这个我在我们的 BNPL chatbot 上是真趟过的。FAQ 那一侧是一个纯知识问题 —— 政策、退款规则、会变的争议流程 —— 所以那块走 **RAG**，不 fine-tune。intent routing 是一个窄的、高频的分类任务，而且 latency 很重要，所以那块就偏向用一个**小的 fine-tuned classifier**，而不是每一轮都去问一个大 LLM。同一个产品，两个不同的问题，两种不同的工具。然后在 voice agent 上我做了真正的 post-training —— SFT 加上 DPO-style 的 alignment —— 因为那里的 gap 是*行为*：多语种的风格、什么时候该调哪个 tool、保持合规。这种东西你靠 prompt 是没法在七个市场上都调稳的。"

(可延伸) "fine-tune 真正的成本不是那一次训练 —— 而是你从此就*拥有了一个模型*。每次 base model 升级，你都得重新评估、或者重训一遍。所以我把 fine-tune 当成一个 commitment，不是一个 quick fix，只有当 prompt 加 RAG 已经被证明触顶了，我才会去动它。"

## 🇨🇳 中文要点 (理解 + 记忆骨架)

**一句话骨架**：先 prompt，再 RAG，最后 fine-tune；只有上一档**测出天花板**才往下走。

**核心判据 = 在补哪种 gap**：
- **知识 gap**（模型不知道、会变的事实/政策/订单数据）→ **RAG**。变化的事实**绝不 fine-tune**，要 retrieve，还能给 citation、知识库随时更新不动模型。
- **行为 gap**（固定输出格式、稳定语气、可靠 tool-call JSON、窄任务做精）→ **fine-tune**。fine-tune 教的是「技能/风格」，不是「事实」。
- **prompt** 永远是第一探针：system prompt + few-shot + structured output，免费、即时，常常就够了；不行的话也帮你看清真正难点在哪。

**另外两个拉向 fine-tune 的力**：latency 和 cost。大模型 + 长 prompt 能用但太慢太贵 → 把窄任务 **蒸馏**到一个小 fine-tune 模型，同质量更便宜。

**真实例子（一定要带）**：BNPL chatbot — FAQ 是知识问题走 RAG；intent routing 是高频窄分类、看延迟，走小 fine-tune classifier。同一产品两个问题两种工具。Voice agent 做了真 post-training（SFT + DPO-style），因为那是行为 gap：多语风格、何时调哪个工具、合规——七个市场上靠 prompt 调不稳。

**收尾的成熟度信号**：fine-tune 真正的成本不是那次训练，而是你从此「拥有一个模型」——base 一升级你就得重评/重训。所以它是 commitment，不是 quick fix。

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: Can you combine them? Or is it one or the other?**
"Almost always combined. A real system is usually a fine-tuned-or-base model, with RAG feeding it fresh context, inside a carefully engineered prompt. They're layers, not a menu. My BNPL stack had all three in different parts."

**Q: When would you specifically NOT fine-tune?**
"Three cases. One — the gap is knowledge that changes; retrieve it. Two — I haven't exhausted prompting yet; I'd be paying training and maintenance cost to fix something a better prompt solves. Three — I don't have enough clean, representative labeled data; fine-tuning on a few hundred noisy examples usually makes things worse, not better."

**Q: How much data do you need to fine-tune well?**
"Depends on the goal. For format or style adaptation, a few thousand high-quality examples can move the needle a lot — quality over quantity. For a genuinely new capability, far more. The bigger lever is curation: I'd rather have [✏️ 核实 数千] clean, deduped, on-distribution examples than ten times that of noisy ones. On the voice agent, data construction and cleaning was the part I personally owned, because that's where the quality actually comes from."

**Q: RAG is retrieving the wrong chunks. Do you fine-tune now?**
"No — that's a retrieval-quality problem, not a model problem. I'd fix chunking, try hybrid search (BM25 + dense), add a reranker, tune top-k. Fine-tuning the generator doesn't fix bad retrieval; it just teaches the model to sound confident over wrong context, which is worse."

**Q: How does this map to Apple's on-device world?**
"Same tree, tighter constraints. On device you can't run a huge model, so the 'distill a small model for a narrow task' branch becomes the *default*, not the fallback — which is exactly Apple's task-specific LoRA-adapter approach: one small base, many small fine-tuned adapters hot-swapped per task. And RAG on device means on-device retrieval over the user's own data, which is also a privacy win."

**Q: A PM says 'just fine-tune it on our docs so it knows our product.' How do you respond?**
"I'd gently reframe it — that's a knowledge requirement, so the right tool is RAG, not fine-tuning. Fine-tuning on docs doesn't reliably make a model *recall* facts, and the moment a doc changes you're stale and have to retrain. RAG keeps the docs as a live, updatable source with citations. I'd only fine-tune here if the real ask were a consistent *style* of answer, not the facts themselves."

**Q: Prompt works but it's a 4000-token prompt on a frontier model — fine, or fix it?**
"Works, but it's a cost-and-latency smell. If it's high-volume, I'd fine-tune a smaller model to internalize that behavior so I don't pay for the long prompt every call — distillation again. If it's low-volume, I'd leave it; the engineering and maintenance cost of owning a fine-tuned model wouldn't pay back. The decision is volume-and-economics driven, and I'd back it with the actual cost-per-call numbers."

## ⚠️ 边界 & 红线 (honest limits + what NOT to say)

- 别把三者讲成互斥的「三选一」——这是最常见的失分点。强调它们是**叠加的层**。
- 别一上来就 fine-tune——在 Apple 这种重成本/运维的环境是危险信号。永远先 prompt。
- 如果被追问具体训练超参（lr、epoch、batch）到很深，老实说「调参靠 eval 驱动的扫描，不背死值」，把话题拉回判断逻辑和数据质量——那才是 senior 信号。
- 不要声称 fine-tune 能「注入最新知识」——这是错的，会被当场识破。知识用 retrieval。

## ✅ 加分钩子 (主动抛, steer 到强项)

- 主动点出**「fine-tune 是 commitment 不是 quick fix」**——base 升级要重评/重训，体现运维成熟度，正中 Apple「incorporate latest models」的痛点。
- 用 **BNPL 一产品两工具** 的例子证明你是按问题选工具，不是有锤子找钉子。
- 顺势抛 **voice agent 的真 post-training（SFT + DPO-style + 数据自己 own）**——把概念题变成你的项目深挖，并桥到 Apple 的 **on-device LoRA adapter = 窄任务小 fine-tune** 这条线。
