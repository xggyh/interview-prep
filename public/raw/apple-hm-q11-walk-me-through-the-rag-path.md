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

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: What chunk size and overlap, concretely?**
- A structure-aware unit, typically a few hundred tokens, with a small overlap [✏️ 核实 实际 chunk size / overlap].
- But I'd push back on a fixed number being the right frame — the right unit is *semantic*: a short FAQ answer is one chunk; a long policy section splits on subheadings.
- I tune size against retrieval recall on an eval set, not by a rule of thumb.

**Q: Which embedding model, and why?**
- I'd pick based on the eval, and importantly a *multilingual* model given the 7-market, Chinese-inclusive corpus — English-only embeddings degrade badly on Chinese policy text.
- The specific model is a swappable component [✏️ 核实 实际用的模型].
- What's load-bearing is that it's multilingual and that I validated it on *our* retrieval set, not a public benchmark.

**Q: How do you fuse BM25 and dense scores?**
- Reciprocal rank fusion is my default — it combines two ranked lists without needing the score scales to be comparable, which is the practical pain with raw score blending.
- Then the reranker does the final ordering anyway, so fusion just needs to assemble a high-recall candidate set.

**Q: How do you evaluate the RAG path?**
- Two *separate* metrics, deliberately.
- *Retrieval*: recall@k — is the right passage even in the candidate set? If not, no generation saves you.
- *Generation*: faithfulness / groundedness — does the answer actually follow from the cited passages? LLM-as-judge plus human spot-checks.
- Separating them tells me *where* a failure is.

**Q: A user asks something genuinely not in the KB. What happens?**
- Nothing above the relevance floor gets retrieved, so the agent declines and hands off rather than hallucinating.
- That floor is a tuned threshold.
- I'd rather have a slightly higher "I don't know" rate than one confident wrong policy statement in a money-touching, regulated flow.

**Q: How do you keep the index fresh when policies change?**
- Re-index on document change, with source-doc metadata so I can invalidate and re-embed only what changed.
- Stale policy answers are a real correctness risk in this domain — so freshness is part of correctness, not an afterthought. [✏️ 核实 实际 re-index 频率/机制]

**Q: Why not just stuff the whole policy doc into a long-context prompt and skip retrieval?**
- Cost, latency, and faithfulness. Long-context is expensive per turn and the model still has to find the needle — recall degrades in the middle of long contexts.
- Retrieval narrows to the relevant passages, which is cheaper *and* easier to ground and cite.
- For a small, stable FAQ it could be fine; for a large multi-market policy corpus, retrieval wins.

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
