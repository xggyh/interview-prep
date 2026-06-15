# 🍎 HM Q11 · Walk me through the RAG path: chunking, retrieval, rerank. Why those choices?

> **类别**: BNPL & Agent Platform · **考点**: chunking 策略 + hybrid (BM25+dense) 检索 + rerank + citation,讲清取舍 · ⚠️ 这是相对偏弱区,给一个站得住的可辩护设计 · [✏️] 数字背前替换成真实值

## 🧠 这题在测什么 / 面试官想看到

JD 明写 "RAG / retrieval / vector search",所以这是必答硬题。面试官想看你能不能把 RAG 拆成**可辩护的工程决策链**,而不是背"embed → cosine → stuff into prompt"。强答会对每个环节给出**为什么这样选 + 取舍**:chunk 怎么切、为什么 hybrid 而不是纯向量、rerank 解决什么、怎么保证 grounding 不幻觉。陷阱:这是你相对偏弱的区,被钻细节 (具体 embedding 模型、chunk token 数) 时不要硬编 —— 给出**有原则的默认值**并标明可调,比报一个假数字强。

## 📋 English Answer (背诵稿, 主答 ~60-90 秒 + 可延伸)

"I think of the RAG path as four decisions — chunk, retrieve, rerank, ground — and each one is a precision lever.

**Chunking.** For a policy and FAQ corpus I chunk *semantically*, not by fixed character count — split on document structure: a FAQ entry, a policy clause, a section. Fixed-size chunks cut sentences in half and destroy meaning; structure-aware chunks keep each unit self-contained. I keep a small overlap between chunks so context isn't lost at boundaries, and I attach metadata — source doc, section, market — because in a 7-market product the *same* question has different answers per region, so I filter on market before I even rank.

**Retrieval — hybrid, BM25 plus dense.** Dense embeddings catch paraphrase and semantic match; BM25 catches exact terms — policy codes, product names, numbers — where lexical match matters and embeddings are weak. I run both and fuse the results. Pure vector search misses the exact-token cases; pure BM25 misses paraphrase. Hybrid is the defensible default for a policy KB full of specific terms.

**Rerank.** First-stage retrieval optimizes recall — get the candidate set right, say top-20 or 30. Then a cross-encoder reranker reorders those by true relevance and I keep the top few for the prompt. The split matters: the first stage is cheap and approximate over the whole index; the reranker is expensive but only runs on a handful of candidates. That's the cost/quality trade-off.

**Grounding and citation.** The model answers *only* from the retrieved passages, with citations back to the source. If retrieval returns nothing above a relevance floor, the agent says it doesn't know and hands off — it does not free-generate. In a compliance context, a confident wrong policy answer is worse than 'let me get a human.'"

*(可延伸:)* "I'd also be honest that RAG quality is mostly a *retrieval* problem, not a generation problem — so the eval I cared about was retrieval recall and answer faithfulness, measured separately."

## 🇨🇳 中文要点 (理解 + 记忆骨架)

记四步:**chunk → retrieve → rerank → ground**,每步都是一个 precision lever。

- **Chunking — 语义切,不是定长切**:按文档结构切 (一条 FAQ / 一个 policy clause / 一节)。定长会把句子切断、毁语义。chunk 间留小 overlap 防边界丢失。挂 metadata (source / section / **market**) —— 7 个市场同一问题答案不同,先按 market 过滤再排序。
- **Retrieval — hybrid (BM25 + dense)**:dense 抓 paraphrase / 语义;BM25 抓精确词 (policy code、产品名、数字),embedding 在精确 token 上弱。两路 fuse。纯向量漏精确词,纯 BM25 漏改写 —— policy KB 全是专有名词,hybrid 是站得住的默认。
- **Rerank — 两段式**:一段检索优化 recall (top-20/30,便宜、近似、扫全库);cross-encoder reranker 精排,贵但只跑这几十个候选 → 取 top few 进 prompt。这就是 cost/quality 取舍。
- **Ground + cite — 只从检索段落答 + 引用**;低于相关性下限就说"不知道"转人工,**绝不 free-generate**。合规场景里,自信地答错 policy 比"找人工"更糟。

骨架一句话:**"RAG 主要是检索问题不是生成问题 —— 语义 chunk + hybrid 召回 + cross-encoder 精排 + 严格 grounding,measure recall 和 faithfulness 分开看。"**

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: What chunk size and overlap, concretely?**
A structure-aware unit, typically a few hundred tokens, with a small overlap [✏️ 核实 实际 chunk size / overlap]. But I'd push back on a fixed number being the right frame — the right unit is *semantic*, so a short FAQ answer is one chunk and a long policy section might be split on subheadings. I tune the size against retrieval recall on an eval set, not by a rule of thumb.

**Q: Which embedding model, and why?**
I'd pick based on the eval, and importantly a *multilingual* embedding model given the 7-market, Chinese-inclusive corpus — English-only embeddings degrade badly on Chinese policy text. I'd be honest that the specific model is a swappable component [✏️ 核实 实际用的模型];what's load-bearing is that it's multilingual and that I validated it on our own retrieval set rather than trusting a public benchmark.

**Q: How do you fuse BM25 and dense scores?**
Reciprocal rank fusion is my default — it combines the two ranked lists without needing the score scales to be comparable, which is the practical pain with raw score blending. Then the reranker does the final ordering anyway, so the fusion just needs to assemble a good candidate set with high recall.

**Q: How do you evaluate the RAG path?**
Two separate metrics, deliberately. *Retrieval*: recall@k — is the right passage even in the candidate set; if it's not, no amount of good generation saves you. *Generation*: faithfulness / groundedness — does the answer actually follow from the cited passages, which I'd check with an LLM-as-judge plus human spot-checks. Separating them tells me *where* a failure is.

**Q: A user asks something genuinely not in the KB. What happens?**
Nothing above the relevance floor gets retrieved, so the agent declines and hands off rather than hallucinating. That floor is a tuned threshold. I'd rather have a slightly higher "I don't know" rate than a single confident wrong policy statement in a money-touching, regulated flow.

**Q: How do you keep the index fresh when policies change?**
Re-index on document change, with the source-doc metadata so I can invalidate and re-embed only what changed. Stale policy answers are a real risk in this domain, so freshness is part of correctness, not an afterthought. [✏️ 核实 实际 re-index 频率/机制]

## ⚠️ 边界 & 红线 (honest limits + what NOT to say)

- **这是你偏弱区 —— 用"有原则的默认 + 可调"代替硬编数字。** 被问 chunk size / 具体 embedding 模型,给原则 (语义单元、多语言、按 eval 调) 并标 [✏️ 核实],不要张口报一个假精确值。
- 不要声称跑了一整套 advanced RAG (HyDE / GraphRAG / 多跳)。如果当时是直球 hybrid + rerank,就说直球 —— 并能讲清*为什么够用*。把复杂度说超过实际会被钻穿。
- 不要把 RAG 讲成"生成"问题。反复强调它是**检索**问题,measure recall 和 faithfulness 分开 —— 这一句就建立可信度。
- 诚实区分:如果 rerank 当时用的是 LLM judge 而不是专门 cross-encoder,直接说;如果只做了 hybrid 没上 rerank,也说,并说明你*会*怎么加。

## ✅ 加分钩子 (主动抛, steer 到强项)

- 主动抛 **"7 市场 → market metadata 预过滤 + 多语言 embedding"** —— 把你真实的多语言、多市场经验变成 RAG 的差异化,直接对上 Apple 的 Greater China / Chinese LLM 需求。
- 强调 **grounding floor → 不知道就转人工,绝不 free-generate** —— 命中 customer-facing + compliance,顺势可引到 Q18 (幻觉治理)。
- 把 **"recall 和 faithfulness 分开 measure"** 抛出来 —— 体现 eval-driven,接 JD 的 LLM eval,也呼应你 voice agent 的 eval harness。
