## 题目

> "**Gemini 1.5 / Claude has 1M / 200K context now**. Some say 'long-context kills RAG' — just stuff everything in. Do you agree? When to use which?"

或追问形态:

> "Customer has 100K-page legal docs. Build a chatbot. Long context, RAG, or hybrid? Defend choice."

**Round**: RAG Architecture / Trade-off (45 min)

---

## 这道题在考什么

考你**modern (2026) understanding** of LLM landscape + production trade-offs:

1. **Long-context truly available** but with caveats (cost, latency, lost-in-middle)
2. **RAG NOT dead** — different sweet spot
3. **Hybrid 是主流答案**
4. **Cost math** — long-context $$$ per call
5. **Update frequency** —— RAG natural, long-context needs reload

---

## 必问 clarifying

**1. Corpus size**

> "Total token count? 1M context window 大 doc OK; 100M? not even close."

**2. Update frequency**

> "Static (one-time legal corpus) or dynamic (daily news)? Affects feasibility."

**3. Query pattern**

> "1 user, 10 query/day or 1000 users, 10K query/day? Cost scaling differs."

**4. Latency / cost tolerance**

> "Each query $5 + 30s OK (research tool with Claude Opus 4.7 long-context) or need $0.01 + 1s (consumer Gemini 3 Flash)?"

**5. Precision需求**

> "Citation traceability needed (legal)? RAG natural. Long-context needs special prompting."

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify corpus / volume / cost / precision |
| 5-15 min | Long-context limits (cost / latency / lost-in-middle) |
| 15-25 min | RAG limits (retrieval miss, multi-hop) |
| 25-35 min | Hybrid pattern (RAG retrieval + long-context for chunks) |
| 35-45 min | Decision tree + recommendation |

---

## 我会这样答（sample）

> "Clarify — *[假设: 100K legal docs ~ 500M tokens total, monthly update, low-volume high-value queries ($5/q acceptable), citation required]*.
>
> Quick answer: **hybrid**. Pure long-context doesn't fit 500M tokens (1M max). Pure RAG can miss multi-page context. Use **RAG-retrieval + long-context-for-chunks**.
>
> Let me defend by walking trade-offs:
>
> **Long-context strengths**:
> - **No retrieval miss** —— model sees everything
> - **Multi-hop reasoning** without explicit retrieval planning
> - **Implicit context** across distant pages handled
>
> **Long-context weaknesses**:
> - **Token cost**: 1M tokens × $4/1M = $4 per call (Gemini 3 Pro at >200K tier); output ~$0.01 (500 tok @ $18/1M)
> - **Latency**: 1M context ~30-60s per call
> - **Lost-in-middle**: even with 1M, attention is U-shaped, middle pages worse recall
> - **Doesn't scale to 500M corpus** — fits 1M max
> - **No granular update**: change 1 doc → reload all
>
> **RAG strengths**:
> - **Scales to billion-token corpus** (indexed once, query small)
> - **Per-query cost cheap**: $0.001-0.05 (Gemini 3 Flash retrieval-narrowed)
> - **Per-query latency low**: 100ms-2s
> - **Granular update**: change 1 doc → re-embed that chunk
> - **Citation natural**: retrieved chunks have provenance
>
> **RAG weaknesses**:
> - **Retrieval miss**: if relevant info not in top-k, LLM can't see it
> - **Multi-hop**: 'A relates to B which connects to C' — needs iterative retrieval
> - **Chunking fragility**: bad chunking → broken context
> - **Engineering complexity**: indexing pipeline, eval, reranker
>
> **Decision tree**:
>
> ```
> Corpus total < 200K tokens?
>   YES → Long-context (just stuff it)
>   NO  ↓
> 
> Corpus < 1M tokens AND query budget > $1?
>   YES → Long-context if Gemini/Claude
>   NO  ↓
> 
> Multi-hop reasoning heavy?
>   YES → Hybrid (RAG retrieve + agent-iterative)
>   NO  → Pure RAG
> ```
>
> **Hybrid pattern recommended for our case**:
>
> ```python
> def hybrid_qa(query, corpus_index, long_context_model):
>     # Stage 1: RAG retrieves top relevant docs (whole docs, not chunks)
>     relevant_docs = retrieve_docs(query, corpus_index, top_k=10)
>     # 10 docs × 50K tokens each = 500K tokens — fits Gemini 1.5
>     
>     # Stage 2: Long-context model reads all top-10
>     context = '\n'.join([f'[Doc {d.id}]\n{d.full_text}' for d in relevant_docs])
>     
>     answer = long_context_model.generate(
>         prompt=f"""
>         Documents:
>         {context}
>         
>         Question: {query}
>         
>         Answer with citations [Doc N].
>         """,
>     )
>     return answer
> ```
>
> Best of both:
> - RAG narrows 500M → 500K
> - Long-context handles within-500K with multi-hop, no chunking loss
> - Cost per query: $1.00 (500K × $2/1M Gemini 3 Pro standard tier) instead of $4 (1M @ Pro >200K tier)
> - Latency: 15s instead of 60s
>
> **Cost math** for our case:
>
> | Approach | Cost/query | Latency | Feasibility |
> |---|---|---|---|
> | Pure long-context | N/A | N/A | Corpus 500M > 1M limit |
> | Pure RAG (Flash) | $0.005 | 2s | Misses multi-hop |
> | **Hybrid (10 docs, 500K Gemini 3 Pro)** | **$1.00** | **15s** | **Fits + multi-hop OK** |
> | Hybrid (3 docs, 150K Pro) | $0.30 | 5s | Compromise |
> | Hybrid (10 docs, Opus 4.7 200K) | $1.25 | 25s | Highest quality, $$$ |
>
> **Volume scaling**:
>
> If 100 queries/day, hybrid is $150/day → manageable
> If 100K queries/day, $150K/day → must optimize: cache, smaller context, cheaper model
>
> **Citation / traceability**:
>
> Even with long-context, **enforce citation**:
>
> ```
> Prompt: "...Answer with [Doc N, page M] citations for every factual claim."
> Post-process: parse citations, validate against actual doc text.
> ```
>
> RAG natural (retrieved chunk has ID). Long-context needs explicit prompt.
>
> **Update strategy for hybrid**:
>
> - Doc changes → re-embed only that doc (RAG-level update)
> - Index searchable, query latency unchanged
> - Long-context model sees fresh docs (loaded fresh each query)
>
> **When pure long-context wins**:
> - Small corpus (< 200K tokens)
> - Multi-hop with cross-doc reasoning
> - Research / one-off analysis (cost less concern)
> - No retrieval engineering team
>
> **When pure RAG wins**:
> - Large corpus (> 10M tokens)
> - High QPS, cost-sensitive
> - Granular real-time updates
> - Strong retrieval engineering team
>
> **Most production**: **hybrid**.
>
> **2026 trend**: as context windows grow (1M → 10M), the cutoff shifts, but hybrid remains optimal for scale-cost balance."

---

## 多场景变体 + 解法

### 变体 1: 法律合同问答 (500-page 合同)

> "1 个 500-page 合同, 律师问 50 个 question。选 long-context / RAG / hybrid?"

**解法**: **Hybrid 最佳**
- 单文件 ~150K tokens → fit 200K-context model (Claude / Gemini)
- 但 50 questions × 150K = 7.5M tokens, $$$
- **方案**: 一次性 long-context "load + index", 后续 question 用 RAG 取相关 clause + 上下文段
- Cost: $1.50 一次 indexing + $0.05/q × 50 = $4 vs pure long-context $50+

### 变体 2: Coding agent — 大 repo

> "Repo 50K files, agent 帮改 bug。"

**解法**: **RAG 必须**
- Repo 总 token 远超 long-context (~50M tokens)
- **Code-aware RAG**: AST chunks, symbol graph
- **Iterative**: agent first asks 'where is auth handled' → search → narrow → 'read these 5 files'
- Long-context **不能** load 全 repo
- 但 single file 内部用 long-context (一次 read whole file fine)

### 变体 3: 医疗病史

> "Patient 历史 30 年 records, doctor 问诊。"

**解法**: **RAG + temporal index**
- 总 records 1M+ tokens, long-context 装不下
- **Time-indexed retrieval**: 'last 5 years' / 'around 2019' 这种 temporal filter
- **Critical record always-in-context**: 过敏 / 慢性病 / 当前药 这种永远在 context
- **Episode-level summary**: 每次就诊 1 段 summary, retrieve 后展开 detail
- **PHI 合规**: 检索结果不能 leak 给 unauth 角色

### 变体 4: Daily news / dynamic data

> "News 每秒更新, agent 给 user briefing。"

**解法**: **RAG 唯一选项**
- 数据每秒变, long-context 装载就过时
- **Hot index** (last 24h, refresh 5 min) + warm (1 month, daily) + cold (archive)
- **Recency-weighted**: time decay (newer > older), 配合 relevance
- **Diversity**: 同事件多 source dedup
- **Personalize**: user 关注的 topic / region 加 weight

### 变体 5: 多轮对话历史

> "Agent 跟同 user 累计聊了 6 个月 (10K 轮对话)。Context 怎么管？"

**解法**: **Hybrid (mostly RAG + recent context)**
- Recent 20 turns 永远 verbatim
- 30-100 轮前 → hierarchical summary
- 100+ 轮前 → fully RAG'd (vector index of all turns)
- **Memory categories**: facts (用户偏好) / events (重要事件) / preferences (沟通风格) — 不同存储策略
- **Episodic vs semantic memory** 区分: 具体某次对话 vs 用户的'我喜欢简洁回答'这种归纳

---

## 简历专属 reframe

| 题 | 你做过 |
|---|---|
| RAG (BNPL chatbot) | 你 + RAG 经验直接相关 |
| ConvFinQA | 财务文档 multi-hop, hybrid 思路 |
| Long-context awareness | Voice agent — multi-turn long history mgmt 你做过 |
| Cost optimization | TikTok payment infra — cost-per-call always考虑 |
| Citation | Compliance — refund / collection 必 citation |

**Quote**:

> "ConvFinQA was exactly this trade-off — financial reports avg 200K tokens each, multi-hop questions. We tried pure RAG (recall lost on cross-table joins) and pure long-context (cost prohibitive at scale, plus 200K Claude was slow). Final architecture: **RAG retrieves relevant tables + paragraphs**, **long-context (Claude 100K) handles within-retrieved-context multi-hop reasoning**. Latency 8s, cost $0.30/q, accuracy comparable to pure long-context at 1/5 cost."

---

## 5 follow-ups

**Q1**: "10M context — will RAG die?"
**A**: No. Reasons:
- **Corpus often > 10M** (enterprise data lakes)
- **Cost** still $$$ at 10M tokens/query
- **Latency** still slow
- RAG just shifts to **wider chunks** (whole docs not paragraphs) when long-context cheap

**Q2**: "Hybrid is complex. Can I just use long-context everywhere if cheap enough?"
**A**: Cost is the gate:
- 100K tokens × $2/1M = $0.20/q (Gemini 3 Pro) → 1M queries/day = $200K/day. Prohibitive.
- 10K tokens (RAG-narrowed) × $0.50/1M (Flash) = $0.005/q → $5K/day. Sustainable.
- Always cheaper to retrieve first

**Q3**: "Long-context is lost-in-middle. Is RAG immune?"
**A**: Not immune, but better managed:
- RAG retrieves **only relevant**, no middle to lose in
- BUT if 50 chunks retrieved, middle ones in LLM context still lost-in-middle
- Mitigation: rerank chunks by relevance order, put best at start/end

**Q4**: "Citation precision — how compare?"
**A**:
- **RAG**: every claim mapped to retrieved chunk ID
- **Long-context**: prompt-enforced citation, but model may hallucinate page reference
- **Hybrid**: RAG-style citation (chunk → doc → page), validated post-LLM
- RAG wins citation reliability

**Q5**: "Customer prefers long-context for simplicity. Defend hybrid."
**A**:
- Pure long-context **cost scales fast**: at Gemini 3 Pro $4/1M (>200K tier), 1M queries × $4 = $4M / day — unscalable. Hybrid sublinear.
- Cost scales linearly with context size, hybrid sublinear with retrieval
- Multi-tenancy: each customer's data isolated → RAG natural
- Real-time updates: RAG re-embed delta, long-context full reload

---

## ❌ 易错点

1. **'Long-context killed RAG'** — wrong, complementary
2. **Pure long-context for huge corpus** — doesn't fit, $$$
3. **Pure RAG for multi-hop** — retrieval miss across hops
4. **Ignore cost math** — production economics
5. **No citation strategy** — long-context hallucinates refs
6. **Forget vendor lock-in** — 1M is Gemini/Claude only
7. **Forget update frequency** — long-context bad for dynamic data

---

## ✅ 加分项

1. **Hybrid 是默认答案** in production
2. **Decision tree** by corpus size + cost + multi-hop
3. **Cost math** explicit ($1.00/q hybrid Pro vs $4 pure long-context vs $0.005 pure RAG Flash)
4. **Lost-in-middle** both approaches
5. **Citation strategy** comparison
6. **Update frequency** consideration
7. **Vendor lock-in** awareness
8. **Quote ConvFinQA RAG+long-context architecture**

---

## Cheat Sheet

```
Long-context strengths:
  No retrieval miss
  Multi-hop natural
  Implicit cross-doc context

Long-context weaknesses:
  Cost ($4/q at 1M Gemini 3 Pro >200K tier)
  Latency (30-60s)
  Lost-in-middle still real
  Doesn't fit > 1M corpus
  No granular update

RAG strengths:
  Scales to billion tokens
  Cheap per query ($0.005-0.05 Gemini 3 Flash)
  Fast per query
  Granular update
  Citation natural

RAG weaknesses:
  Retrieval miss
  Multi-hop hard
  Chunking fragility
  Engineering complexity

Decision tree:
  Corpus < 200K? → long-context
  < 1M + cost OK? → long-context
  Multi-hop heavy? → hybrid
  else → RAG

Hybrid pattern:
  RAG: 500M → top-10 docs (500K tokens)
  Long-context: handle multi-hop within
  Cost: ~$1.00/q (Gemini 3 Pro hybrid) vs $4/q (1M full) vs $0.005/q (pure Flash RAG)

Cost scaling:
  100 q/day pure long: $300/day, OK
  100K q/day pure long: $300K/day, no
  Hybrid sublinear with retrieval

Citation:
  RAG: chunk-id natural
  Long-context: prompt + post-validate
  Hybrid: best of both

2026 trend:
  Context grows but hybrid remains
  RAG chunks wider as context cheaper
  Both alive

红线:
  - 'Long-context killed RAG'
  - Pure long for huge corpus
  - Pure RAG for multi-hop
  - Ignore cost math
  - No citation strategy
```
