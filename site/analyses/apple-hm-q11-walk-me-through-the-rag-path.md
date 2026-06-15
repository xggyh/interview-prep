# 🍎 HM Q11 · Walk me through the RAG path: chunking, retrieval, rerank. Why those choices?

> **类别**: BNPL & Agent Platform · **考点**: chunking 策略 + hybrid (BM25+dense) 检索 + rerank + citation,讲清取舍 · ⚠️ 这是相对偏弱区,给一个站得住的可辩护设计 · [✏️] 数字背前替换成真实值

## 🧠 这题在测什么 / 面试官想看到

JD 明写 "RAG / retrieval / vector search",这是必答硬题。面试官想看你能不能把 RAG 拆成**可辩护的工程决策链**,而不是背"embed → cosine → stuff into prompt"。强答对每个环节给**为什么这样选 + 取舍**:chunk 怎么切、为什么 hybrid 而不是纯向量、rerank 解决什么、怎么保证 grounding 不幻觉。陷阱:这是你相对偏弱的区,被钻细节 (embedding 模型、chunk token 数) 时不要硬编 —— 给**有原则的默认值** + 标明可调,比报假数字强。

## 📋 English Answer (背诵稿, 主答 ~60-90 秒 + 可延伸)

"I think of the RAG path as four decisions — chunk, retrieve, rerank, ground — and each one is a precision lever.

**Chunking — semantic, not fixed-size.**
- For a policy and FAQ corpus I split on document *structure*: a FAQ entry, a policy clause, a section.
- Fixed-size character chunks cut sentences in half and destroy meaning; structure-aware chunks keep each unit self-contained.
- I keep a small overlap between chunks so context isn't lost at boundaries.
- I attach metadata — source doc, section, *market* — because in a 7-market product the same question has different answers per region, so I filter on market *before* I even rank.

**Retrieval — hybrid, BM25 plus dense.**
- Dense embeddings catch paraphrase and semantic match.
- BM25 catches exact terms — policy codes, product names, numbers — where lexical match matters and embeddings are weak.
- I run both and fuse the results. Pure vector misses exact tokens; pure BM25 misses paraphrase.
- Hybrid is the defensible default for a policy KB full of specific terms.

**Rerank — two stages, deliberately split.**
- First-stage retrieval optimizes *recall* — get the candidate set right, say top-20 or 30.
- A cross-encoder reranker then reorders those by true relevance; I keep the top few for the prompt.
- The split is the cost lever: first stage is cheap and approximate over the whole index; the reranker is expensive but runs on only a handful of candidates.

**Grounding and citation.**
- The model answers *only* from retrieved passages, with citations back to the source.
- If retrieval returns nothing above a relevance floor, the agent says it doesn't know and hands off — it does not free-generate.
- In a compliance context, a confident wrong policy answer is worse than 'let me get a human.'"

*(可延伸:)* "And I'd be honest that RAG quality is mostly a *retrieval* problem, not a generation problem — so the metrics I cared about were retrieval recall and answer faithfulness, measured *separately*, so a failure tells me which half broke."

## 🇨🇳 中文完整版 (口播稿, 与英文对应)

"我把 RAG 这条路看成四个决策 —— chunk、retrieve、rerank、ground —— 每一个都是一个 precision lever（精度杠杆）。

**Chunking —— 按语义切，不是定长切。**
- 对一个 policy 和 FAQ 的语料，我按文档的*结构*来切：一条 FAQ、一个 policy clause、一个 section。
- 定长的字符 chunk 会把句子切成两半、把语义毁掉；结构感知的 chunk 能让每个单元自成一体。
- 我在 chunk 之间留一点小 overlap，这样在边界处上下文不会丢。
- 我会挂上 metadata —— source doc、section、还有 *market* —— 因为在一个 7 市场的产品里，同一个问题在不同地区答案是不同的，所以我在排序*之前*就先按 market 过滤。

**Retrieval —— hybrid，BM25 加 dense。**
- dense embedding 抓改写和语义上的匹配。
- BM25 抓精确的词 —— policy code、产品名、数字 —— 这些地方字面匹配才要紧，而 embedding 偏弱。
- 我两路都跑，然后把结果 fuse 起来。纯向量会漏掉精确 token；纯 BM25 会漏掉改写。
- 对一个全是专有名词的 policy KB 来说，hybrid 是站得住脚的默认选择。

**Rerank —— 两段式，故意拆开。**
- 第一段检索优化的是 *recall* —— 把候选集弄对，比如 top-20 或 30。
- 然后一个 cross-encoder reranker 按真实相关性把它们重排；我留最前面那几个进 prompt。
- 这个拆分就是 cost lever：第一段在整个索引上又便宜又近似；reranker 很贵，但只在那一小把候选上跑。

**Grounding 和 citation。**
- 模型*只*从检索到的段落作答，并带 citation 回到 source。
- 如果检索结果没有任何东西高过一个相关性下限，agent 就说它不知道、然后 handoff —— 它不会自由生成。
- 在合规语境里，一个自信但错误的 policy 答案，比 '让我帮你转个人工' 更糟。"

*(可延伸:)* "而且我会老实说，RAG 的质量主要是个*检索*问题，不是生成问题 —— 所以我在意的指标是 retrieval recall 和 answer faithfulness，而且是*分开*量的，这样一个 failure 能告诉我是哪一半坏了。"

## 🇨🇳 中文要点 (理解 + 记忆骨架)

记四步:**chunk → retrieve → rerank → ground**,每步都是一个 precision lever。

- **Chunking — 语义切,不是定长切**:按文档结构切 (一条 FAQ / 一个 policy clause / 一节)。定长会把句子切断、毁语义。chunk 间留小 overlap 防边界丢失。挂 metadata (source / section / **market**) —— 7 市场同一问题答案不同,**先按 market 过滤再排序**。
- **Retrieval — hybrid (BM25 + dense)**:dense 抓 paraphrase / 语义;BM25 抓精确词 (policy code、产品名、数字),embedding 在精确 token 上弱。两路 fuse。纯向量漏精确词,纯 BM25 漏改写 —— policy KB 全是专有名词,**hybrid 是站得住的默认**。
- **Rerank — 两段式 (cost lever)**:一段检索优化 recall (top-20/30,便宜、近似、扫全库);cross-encoder reranker 精排,贵但只跑这几十个候选 → 取 top few 进 prompt。
- **Ground + cite**:只从检索段落答 + 引用;低于相关性下限就说"不知道"转人工,**绝不 free-generate**。合规场景里,自信答错 policy 比"找人工"更糟。

**一句关键认知:** RAG 主要是**检索问题**不是生成问题 —— 所以 measure **recall** 和 **faithfulness** 分开,坏了能定位是哪一半。

骨架一句话:**"语义 chunk + hybrid 召回 + cross-encoder 精排 + 严格 grounding;recall 和 faithfulness 分开量;RAG 是检索问题不是生成问题。"**

讲述节奏:
1. 开口给四步总纲 "chunk, retrieve, rerank, ground — each a precision lever"。
2. 逐步讲,每步**带一句为什么** (定长毁语义 / 纯向量漏精确词 / 两段式是 cost lever / grounding 防幻觉)。
3. 收尾抛 "RAG 是检索问题不是生成问题" —— 这一句立刻建立可信度。
4. 细节数字 (chunk size、embedding 模型) **被问再说**,且用原则 + [✏️ 核实],不主动报。

强答 vs 弱答对照 (这题偏弱,更要靠结构取胜):
- 弱答:"embed 文档,query 时取最近的 top-k 塞进 prompt" → 教科书一句话,没有任何取舍,显得没真做过。
- 弱答:"用向量数据库做语义检索" → 漏了精确词召回 (policy code)、漏了 rerank、漏了 grounding,一钻就空。
- 中等:"chunk + dense retrieval + 塞进 prompt 生成" → 缺 hybrid 和 rerank 的*为什么*。
- **强答 (你要给的):四步每步带取舍 (语义 chunk / hybrid 为什么 / rerank 为什么两段 / grounding 防幻觉) + 一句"RAG 是检索问题不是生成问题" + recall 和 faithfulness 分开量** → 即使你实现没那么全,这个*决策框架*本身就证明你懂 RAG。

口播提醒:这题你不熟,**靠结构不靠细节**。先把四步框架稳稳讲完,把 chunk size / embedding 模型这类细节留到追问、并明确说"按 eval 调 + 可换"。框架完整 > 细节精确。

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: What chunk size and overlap, concretely?**
**中**: 具体说，chunk size 和 overlap 是多少？
- A structure-aware unit, typically a few hundred tokens, with a small overlap [✏️ 核实 实际 chunk size / overlap].
- But I'd push back on a fixed number being the right frame — the right unit is *semantic*: a short FAQ answer is one chunk; a long policy section splits on subheadings.
- I tune size against retrieval recall on an eval set, not by a rule of thumb.
> 🇨🇳 一个 structure-aware 的单位，通常几百个 token，带一点点 overlap [✏️ 核实 实际 chunk size / overlap]。但我会反驳"一个固定数字"是对的框架 —— 对的单位是*语义*的：一条短的 FAQ 答案就是一个 chunk；一段长的 policy 按子标题切。我是在 eval set 上对着 retrieval recall 来调 size 的，不是靠经验法则拍。

**Q: Which embedding model, and why?**
**中**: 用的哪个 embedding 模型，为什么？
- I'd pick based on the eval, and importantly a *multilingual* model given the 7-market, Chinese-inclusive corpus — English-only embeddings degrade badly on Chinese policy text.
- The specific model is a swappable component [✏️ 核实 实际用的模型].
- What's load-bearing is that it's multilingual and that I validated it on *our* retrieval set, not a public benchmark.
> 🇨🇳 我会基于 eval 来选，而且很重要的一点是选一个*多语言*的模型，因为是 7 个市场、包含中文的语料 —— 只支持英文的 embedding 在中文 policy 文本上会退化得很厉害。具体哪个模型是一个可替换的组件 [✏️ 核实 实际用的模型]。真正 load-bearing 的是：它是多语言的，而且我是在*我们自己*的 retrieval set 上验证的，不是在一个公开 benchmark 上。

**Q: How do you fuse BM25 and dense scores?**
**中**: BM25 和 dense 的分数你怎么融合？
- Reciprocal rank fusion is my default — it combines two ranked lists without needing the score scales to be comparable, which is the practical pain with raw score blending.
- Then the reranker does the final ordering anyway, so fusion just needs to assemble a high-recall candidate set.
> 🇨🇳 reciprocal rank fusion 是我的默认选择 —— 它把两个排好序的列表合起来，不需要两边的分数 scale 可比，而这恰恰是直接混原始分最头疼的地方。反正后面 reranker 还会做最终排序，所以 fusion 只需要拼出一个高 recall 的候选集就行。

**Q: How do you evaluate the RAG path?**
**中**: 这条 RAG 路径你怎么评估？
- Two *separate* metrics, deliberately.
- *Retrieval*: recall@k — is the right passage even in the candidate set? If not, no generation saves you.
- *Generation*: faithfulness / groundedness — does the answer actually follow from the cited passages? LLM-as-judge plus human spot-checks.
- Separating them tells me *where* a failure is.
> 🇨🇳 刻意分成两个*独立*的指标。*Retrieval*：recall@k —— 对的段落到底有没有进候选集？没进的话，再好的 generation 也救不了你。*Generation*：faithfulness / groundedness —— 答案是不是真的从引用的段落里推出来的？用 LLM-as-judge 加人工抽检。把它们分开，能告诉我失败到底*在哪一环*。

**Q: A user asks something genuinely not in the KB. What happens?**
**中**: 用户问了一个知识库里确实没有的东西，会怎样？
- Nothing above the relevance floor gets retrieved, so the agent declines and hands off rather than hallucinating.
- That floor is a tuned threshold.
- I'd rather have a slightly higher "I don't know" rate than one confident wrong policy statement in a money-touching, regulated flow.
> 🇨🇳 没有任何东西能超过那个 relevance 下限被检索出来，所以 agent 会拒答并转人工，而不是去 hallucinate。那个下限是一个调出来的阈值。在一个碰钱、受监管的流程里，我宁可"我不知道"的比例略高一点，也不要出现一句自信但错误的 policy 陈述。

**Q: How do you keep the index fresh when policies change?**
**中**: policy 变了的时候，你怎么保持 index 是新的？
- Re-index on document change, with source-doc metadata so I can invalidate and re-embed only what changed.
- Stale policy answers are a real correctness risk in this domain — so freshness is part of correctness, not an afterthought. [✏️ 核实 实际 re-index 频率/机制]
> 🇨🇳 文档一变就 re-index，带上 source-doc 的 metadata，这样我只对变了的部分做 invalidate 和重新 embed。过期的 policy 答案在这个域里是一个实打实的 correctness 风险 —— 所以新鲜度是 correctness 的一部分，不是事后才想的。[✏️ 核实 实际 re-index 频率/机制]

**Q: Why not just stuff the whole policy doc into a long-context prompt and skip retrieval?**
**中**: 为什么不干脆把整份 policy 文档塞进 long-context prompt，跳过检索？
- Cost, latency, and faithfulness. Long-context is expensive per turn and the model still has to find the needle — recall degrades in the middle of long contexts.
- Retrieval narrows to the relevant passages, which is cheaper *and* easier to ground and cite.
- For a small, stable FAQ it could be fine; for a large multi-market policy corpus, retrieval wins.
> 🇨🇳 cost、latency 和 faithfulness。long-context 每一轮都贵，而且模型照样得在里面捞那根针 —— recall 在长上下文的中间会退化。检索把范围收窄到相关段落，既更便宜，又更容易 ground 和 cite。对一个又小又稳定的 FAQ，塞进去也许还行；但对一个大型、多市场的 policy 语料，检索胜出。

**Q: How do you handle a query that needs two different passages to answer — e.g. eligibility *and* the fee?**
**中**: 一个查询需要两段不同的文本才能回答 —— 比如 eligibility *加* 手续费 —— 你怎么处理？
- Top-k with k > 1 is exactly for this — I retrieve several passages and let the model synthesize across them, citing each.
- The reranker matters here: I need *both* relevant passages in the top few, not one passage twice, so I'd watch for redundancy and tune k against multi-passage questions on the eval set.
- If a question reliably needs multi-hop reasoning I'd flag that as a harder case [✏️ 核实 是否遇到多跳], but most policy/FAQ questions are answerable from a small set of passages, not a reasoning chain.
> 🇨🇳 top-k 里 k > 1 就是为这个准备的 —— 我检索好几段，让模型跨这几段去综合，每段都 cite。reranker 在这里很关键：我需要*两段*相关的都进前几名，而不是同一段出现两次，所以我会盯着冗余，并在 eval set 上对着多段落的问题去调 k。如果某类问题稳定地需要 multi-hop 推理，我会把它标成更难的 case [✏️ 核实 是否遇到多跳]，但大多数 policy/FAQ 问题是能从一小撮段落里回答出来的，不是一条推理链。

**Q: How do you stop the model from blending retrieved facts with its own pretrained "knowledge" of how BNPL usually works?**
**中**: 你怎么阻止模型把检索到的事实，和它自己预训练里"BNPL 一般怎么运作"的"知识"混在一起？
- Instruction plus grounding discipline: the prompt tells it to answer *only* from the provided passages and to say it doesn't know if they don't cover it.
- Citations are the enforcement mechanism — every claim should map to a passage, and I can check that in faithfulness eval.
- In a regulated product, the model's generic prior about "how BNPL usually works" is a liability — *our* policy is the only source of truth, which is the whole reason for RAG over a parametric answer.
> 🇨🇳 靠 instruction 加上 grounding 的纪律：prompt 告诉它*只*能从给定的段落里回答，如果段落没覆盖就说不知道。citation 是强制机制 —— 每一条 claim 都应该映射到某个段落，而我能在 faithfulness eval 里去查这一点。在一个受监管的产品里，模型那个"BNPL 一般怎么运作"的通用先验是个负债 —— *我们的* policy 才是唯一的 source of truth，这正是用 RAG 而不是用参数化答案的全部理由。

## ⚠️ 边界 & 红线 (honest limits + what NOT to say)

- **这是你偏弱区 —— 用"有原则的默认 + 可调"代替硬编数字。** 被问 chunk size / 具体 embedding 模型,给原则 (语义单元、多语言、按 eval 调) 并标 [✏️ 核实],不要张口报一个假精确值。
- 不要声称跑了一整套 advanced RAG (HyDE / GraphRAG / 多跳)。如果当时是直球 hybrid + rerank,就说直球 —— 并能讲清*为什么够用*。把复杂度说超过实际会被钻穿。
- 反复强调 RAG 是**检索**问题,measure recall 和 faithfulness 分开 —— 这一句就建立可信度。
- 诚实区分:如果 rerank 当时用的是 LLM judge 而不是专门 cross-encoder,直接说;如果只做了 hybrid 没上 rerank,也说,并说明你*会*怎么加。
- 如果当时其实只用了纯 dense (没 BM25),诚实说 —— 然后讲"我现在会加 BM25,因为 policy code 这种精确词向量召回不稳",把它变成"我知道怎么改进"而不是假装当时就做了。

## ✅ 加分钩子 (主动抛, steer 到强项)

- 主动抛 **"7 市场 → market metadata 预过滤 + 多语言 embedding"** —— 把你真实的多语言、多市场经验变成 RAG 差异化,直接对上 Apple 的 Greater China / Chinese LLM 需求。
- 强调 **grounding floor → 不知道就转人工,绝不 free-generate** —— 命中 customer-facing + compliance,顺势引到 Q18 (幻觉治理)。
- 把 **"recall 和 faithfulness 分开 measure"** 抛出来 —— 体现 eval-driven,接 JD 的 LLM eval,也呼应 voice agent 的 eval harness。
- 提一句 **两段式 retrieve→rerank 是 cost lever** —— 把 RAG 和 latency/cost 主线挂钩,显示你不是只懂质量、也懂生产成本 (引到 Q20)。
