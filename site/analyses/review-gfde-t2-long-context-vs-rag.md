## T2.6 · long context vs RAG — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/gfde-t2-long-context-vs-rag.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t2-long-context-vs-rag.html`](questions/gfde-t2-long-context-vs-rag.html)

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

2026 共识 = **hybrid**: long-context 杀不了 RAG; 决策树 by corpus size × cost × multi-hop × update freq × citation; 实战 90% **RAG narrow → long-context within**, 加 prefix cache 90% off cached 改写经济性.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| **Context window** | LLM 单次输入容量 | Gemini 3 Pro 2M, Flash 1M, Claude 200K, GPT-5.5 256K |
| **Effective context** | Attention 真正 work 的区域 | 中部 30-40% 衰减 |
| **Long-context mode** | 整 corpus 塞 LLM 不 RAG | 小 corpus + multi-hop + low QPS |
| **RAG** | Retrieval (BM25/dense/hybrid) → top-K chunk | 大 corpus + 实时 + 高 QPS |
| **Hybrid** | RAG narrow → long-ctx within | 多数 production |
| **Prefix cache** | Anthropic 5min, Gemini 1h, hit 0.10x in | Long prefix reuse |
| **Cache write surcharge** | 1.25-2x in 价 | 写入一次 |
| **Cache hit** | 0.10x in 价 | 后续读 |
| **Lost-in-middle** | Liu 2023, 中部 30-40% gap | Long ctx 通用 |
| **Multi-hop** | 跨 doc/chunk 推理 (A→B→C) | Long-ctx 强, RAG 弱 |
| **Vendor lock-in** | 1M+ ctx 只 Gemini/Claude | 长 ctx 高 lock-in |
| **Hot + warm + cold** | 24h in-mem / month batch / archive | 实时 + 成本平衡 |
| **Cache invalidation** | 1 token 改全失效 | Long-ctx 更新难 |
| **Citation provenance** | RAG chunk_id 自然 / long-ctx prompt 验 | Audit / 防 hallucinate |
| **Per-query cost math** | input × in price + output × out price | FDE 必算 |

### 🎯 5 个核心 framework

**Framework 1**: Decision Tree (Corpus × Cost × Multi-hop × Freshness)
- When: 系统设计开始
- Algorithm: corpus < 200K + static + low-vol → long-ctx + cache ⭐; 200K-2M single tenant → Pure Pro 2M; 200K-2M multi-tenant → Hybrid; > 2M → Pure RAG (default)
- Trade-off: 同 corpus 不同 cost / freshness 走不同分支
- Tools: Gemini 3 Pro 2M, Claude 200K, Qdrant, Pinecone

**Framework 2**: Cost Math (2026 pricing)
- When: 任何 architecture 决策
- Algorithm: Gemini 3 Pro $2 (≤200K)/$4 (>200K)/$12 out; Flash $0.50/$3; Opus 4.7 $5/$25; Sonnet 4.6 $3/$15; Haiku 4.5 $1/$5; GPT-5.5 $5/$30
- Trade-off: 100 q/day pure long-ctx OK ($400/day), 100K q/day RAG must
- Tools: 自实现 cost calculator, OTel cost attribute

**Framework 3**: Hybrid Pattern (RAG narrow → long-ctx within)
- When: 大 corpus + 多 hop
- Algorithm: RAG retrieve top-10 docs (doc-level not chunk) → 500K total → Gemini 3 Pro 2M → multi-hop within
- Trade-off: 双层架构 + RAG infra + LLM 调用, 但 quality + cost 折中
- Tools: Qdrant for RAG, Gemini 3 Pro 2M for ctx, Anthropic prompt cache

**Framework 4**: Citation Strategy
- When: 始终 (audit / 防 hallucinate)
- Algorithm: RAG cite chunk_id 天然 / long-ctx 靠 prompt+post-validate 易 hallucinate / hybrid 最佳 (doc/section + post-validate)
- Trade-off: post-validate 多 LLM 调用, 但 hallucinate cite 杀掉
- Tools: regex citation validator, Flash self-consistency check

**Framework 5**: Update Frequency + Freshness
- When: 数据动态 / 多源混合
- Algorithm: static (年级) → long-ctx + permanent cache; daily → hybrid + nightly cache rebuild; hourly → hybrid + cache invalidate; real-time → pure RAG (hot index)
- Trade-off: 实时数据 long-ctx 不可
- Tools: Qdrant snapshot, freshness decay metadata, cache key versioning

### 🌳 关键决策树 (ASCII)

```
Q: Corpus 大小?
├── < 200K, static, low-vol (1-10 用户/day)
│   → Pure long-ctx + prefix cache ⭐ (Anthropic 5min / Gemini 1h, 90% off)
├── < 200K, 高 QPS (100+ 用户/day) + 静态
│   → Long-ctx + permanent cache OK
├── < 200K, 高 QPS + 动态
│   → RAG (cache 不停失效, 没省钱)
├── 200K - 2M, 单租户 / 公开数据
│   → Gemini 3 Pro 2M direct + prompt cache
├── 200K - 2M, 多租户 (每客户私有)
│   → Hybrid: RAG narrow → Pro 2M within
└── > 2M (装不下)
   ├── Latency tight    → Dense only RAG
   ├── Quality top      → Hybrid + Rerank → long-ctx
   ├── Real-time data   → Pure RAG (hot index)
   └── Multi-tenant     → Per-tenant shard

Q: Multi-hop heavy?
├── 跨 doc cross-reasoning multi-step → Long-ctx within (RAG narrow first)
├── 单跳 fact lookup                    → Pure RAG, 不需要 long-ctx
└── 混合                                → Hybrid w/ self-RAG router

Q: Update freq?
├── Static (年级)        → Long-ctx + permanent cache
├── Daily                → Hybrid + nightly cache rebuild
├── Hourly               → Hybrid + cache invalidate
└── Real-time            → Pure RAG (hot index 5min refresh)

Q: Citation 严格度?
├── 必须 audit / regulated  → RAG / Hybrid (chunk_id 自然) ⭐
├── 一般                    → Long-ctx prompt + post-validate
└── 内部 / 实验             → 都可
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: Decision Tree by Corpus + Cost + Multi-hop**
- 完整树: corpus size × user volume × static/dynamic × multi-hop × multi-tenant × latency × citation
- 多场景 walkthrough: 法律 (150K 合同 → long-ctx + cache); 代码 (1M LOC → RAG + AST + 单文件 long); 医疗 (30 年 records 1M+ → RAG temporal + critical always); news (实时 → RAG hot index); ConvFinQA (财报 multi-doc → hybrid)
- Top 3 gotchas: 一刀切 long-ctx 不分大小 / 不区分单/多租户 / 没 real-time 分支
- Tools: 自实现 router pre-LLM, Gemini 3 Flash query classify

**Problem 2: Cost Math — Per-query 1M vs RAG**
- 2026 pricing: Gemini 3 Pro $2 (≤200K) / $4 (>200K) / $12 out per 1M; Flash $0.50/$3; Opus 4.7 $5/$25; Sonnet 4.6 $3/$15; Haiku 4.5 $1/$5; GPT-5.5 $5/$30
- 500K corpus per-query: Long-ctx Pure $1.00 (no cache) → $0.10 (cache hit); Pure RAG $0.011; Hybrid $0.25 (RAG narrow 500K → Pro within)
- Volume scaling 100 q/day: long-ctx $400, RAG $0.50, hybrid $25
- 100K q/day: long-ctx $400K (不可行), RAG $500, hybrid $25K
- 1M q/day: long-ctx 不可, RAG $5K, hybrid $250K (仍贵)
- Prefix cache mechanics: write 1.25-2x once, hit 0.10x; Anthropic 5min / Gemini 1h; 50K project ctx hit 80% 节省 80%
- Top 3 gotchas: 不算 cost / 忽略 >200K Pro tier 涨价 / 不用 cache
- Tools: 自实现 cost dashboard, OTel cost attrib per query

**Problem 3: Hybrid Pattern (RAG narrow → Long-ctx within)**
- 标准架构: RAG (Qdrant + BM25 + hybrid) top-10 doc-level (not chunk) ~500K → Gemini 3 Pro 2M context within → multi-hop 推理 → answer + citation
- 关键设计: doc-level not chunk (避免 chunk 切碎); top-10 not 100 (cost); 加 prefix cache 5-min reuse
- Caching: 同 user session 内 prefix 同; cross-session 不 reuse; 关键: cache key 含 RAG candidates set
- 失效场景: 跨 turn corpus 不同 → cache miss; doc 更新 → cache invalidate
- Top 3 gotchas: chunk-level not doc-level / 没 cache / 跨 user mix cache
- Tools: Qdrant retrieval, Gemini 3 Pro 2M, Anthropic prompt cache, Redis for cache key

**Problem 4: Citation + Provenance Comparison**
- RAG citation 天然: 每 chunk 有 chunk_id, system prompt 要求引用, post-LLM regex validate
- Long-ctx citation 挑战: prompt 内 source 标 (e.g., [doc-A], [doc-B]) → LLM 易 hallucinate cite (8% 编不存在的 [doc-X])
- Hybrid citation 最佳: RAG 拿 doc/section ref, long-ctx 内 multi-hop, citation 仍能 trace 到 doc + section
- 验证 framework: regex 抓 [doc-N] → 比对 retrieved list / 比对 ctx 内 source tag → mismatch flag → Flash self-consistency check → retry / escalate
- UI: 用户能 click citation → 跳 source doc + highlight
- Top 3 gotchas: 没 post-validate / hallucinate cite 不抓 / 没 self-consistency
- Tools: 自实现 regex validator, Flash for SC, UI link-back

**Problem 5: Update Frequency + Freshness**
- Update mode: static / daily / hourly / real-time
- Long-ctx update 难: 1 token 改, prefix cache 全失效, 必须 reload + re-cache
- Hybrid update: RAG 实时 (delta indexing), long-ctx prefix 半静态 (nightly rebuild)
- Freshness signal: chunk metadata `updated_at`, `score *= exp(-Δt / λ)` λ=30 days news, 365 policy
- Mixing static + dynamic corpus: 静态部分 long-ctx + cache, 动态部分 RAG, RRF merge
- Cache invalidation patterns: TTL-based (5min/1h) / version-based (doc hash) / event-based (Kafka invalidate)
- Update cost analysis: full reload 500K tokens × $2 = $1; delta RAG index 0.001
- Top 3 gotchas: long-ctx for real-time / cache 不 invalidate / 没 freshness decay
- Tools: Qdrant snapshots, Anthropic cache headers, Kafka event invalidate

### 🔥 Production gotchas (top 15)

1. "Long-context killed RAG" (2024 hype, 2026 共识 hybrid)
2. Pure long-ctx for > 2M corpus (装不下 / cost 自爆)
3. Pure RAG for multi-hop (chunk 分散漏关系)
4. 不算 cost math (FDE 必扣分)
5. 不用 prefix cache (90% off cached 大省)
6. Cache key 不含 RAG candidate set → cross-query 混
7. 多租户 long-ctx 直接 (cross-tenant leak)
8. 没 citation 验证 (hallucinated [doc-X])
9. Real-time data 走 long-ctx (cache 不停失效)
10. 单租户 cache 跨 user 共用 (隐私)
11. 不分 single-shot vs multi-turn (multi-turn 必加 cache)
12. Vendor lock-in 不察觉 (2M+ 主 Gemini/Claude)
13. Doc-level vs chunk-level 混 (hybrid 应 doc-level)
14. 不区分 trusted vs untrusted corpus (long-ctx 注入)
15. Long-ctx 中部 lost (2M middle 30-40% gap 仍真)

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Decision tree | ConvFinQA 多财报 | corpus 1000+ 财报 / customer, multi-tenant → RAG narrow → Claude 200K within |
| Cost math | TikTok PayLater | Per-query $0.5 long-ctx vs $0.005 RAG, 10万 q/day 算清 RAG 必 |
| Hybrid pattern | BNPL chatbot | RAG top-10 doc → 500K → Gemini 3 Pro within, multi-hop 推理 |
| Prefix cache | BNPL system prompt | 30K system + 50K project ctx, hit 70%+, $ 80% off |
| Citation validate | ConvFinQA | post-LLM regex + Flash SC, hallucinate cite -60% |
| Hot + warm | BNPL ticket index | hot 24h in-mem 5min, warm month batch, cold archive |
| Multi-tenant | BNPL 7 markets | Per-tenant Qdrant shard, no cross-tenant cache |
| Long-ctx middle | Voice agent | 重要 turn 在 start AND end, periodic recap 每 10 turn |

### 🎤 面试现场 quotables (top 8)

> "Long-context didn't kill RAG — it changed the boundary. Below 200K static low-vol, long-context + cache wins. Above 2M, RAG is mandatory. In between, hybrid."

> "Hybrid pattern is RAG narrow to 500K, then Gemini 3 Pro 2M for multi-hop within. Cost lands around $0.25/query vs $1 pure long-context, $0.011 pure RAG."

> "Prefix caching is the unlock: Anthropic 5-min, Gemini 1-hour, cache hits cost 0.10x. My 50K project context hits 80% cache rate after warmup."

> "Citation: RAG's natural — chunk_id is the cite. Long-context citation is fragile and 8% of LLM answers cite [doc-X] that doesn't exist. I always post-validate with regex + Flash self-consistency."

> "On ConvFinQA we initially tried pure long-context per case, simple and quick. But going production with 1000+ tenants forced hybrid: per-tenant RAG → Claude 200K within."

> "Vendor lock-in is real — 1M+ context is essentially Gemini and Claude. Going pure long-context locks you to two vendors. RAG stays model-agnostic."

> "Lost-in-middle is real even at 2M Gemini 3 Pro — mid-position recall drops 30-40%. Don't assume 2M = 2M of usable attention."

> "Real-time data forces RAG — long-context cache can't track per-second updates. News, ticket, monitoring data: RAG hot index with 5-min refresh."

### 🚨 红线 (top 10 anti-patterns)

1. "Long-context killed RAG" (2022 narrative)
2. Pure long-context for > 2M corpus
3. Pure RAG for multi-hop reasoning
4. Ignore per-query cost math
5. No citation strategy / no post-validate
6. No prefix caching
7. One-size all queries (no router)
8. Multi-tenant prefix cache shared
9. Real-time data → long-ctx (cache 不停失效)
10. Vendor lock-in 不察觉 (1M+ ctx 主 Gemini/Claude)

### 🛠️ Tool zoo (2026)

| 类别 | Tool | 一句话 |
|---|---|---|
| Long-ctx LLM | Gemini 3 Pro 2M, Flash 1M, Claude 200K, GPT-5.5 256K | Pro 2M 最大 |
| Vector DB | Qdrant, Pinecone, Weaviate, Milvus | RAG 索引 |
| Sparse | OpenSearch, Elasticsearch | Hybrid 必须 |
| Prefix cache | Anthropic 5min, Gemini context cache 1h | 90% off cached |
| Tracing | Phoenix (Arize), LangSmith, Langfuse | Per-query cost |
| Citation validate | 自实现 regex + Flash SC | Hallucinate cite |
| Router | DSPy, LiteLLM, Portkey | Query → strategy |
| Cost dashboard | OTel + Grafana | Per-tenant $ |

### 📊 Per-query cost matrix (500K corpus)

```
                     Cost / query    Latency    Multi-tenant   Multi-hop
Pure long-ctx        $1.00           30-60s     ❌ shared cache ⭐ free
+ prefix cache       $0.10 (hit)     15-30s     ❌              ⭐
Pure RAG (Flash)     $0.011          1-2s       ⭐ tenant filter ❌ chunk 分散
Hybrid RAG → ctx     $0.25           5-15s      ⭐               ⭐ within narrow
Hybrid + cache       $0.05-0.10      3-10s     ⭐               ⭐

Volume scaling:
  100 q/day:    long-ctx $400/day OK, RAG $0.50, hybrid $25
  100K q/day:   long-ctx $400K 不可行, RAG $500, hybrid $25K
  1M q/day:     long-ctx 不可, RAG $5K, hybrid $250K (tough)
```

### 💻 一段最小 prod-ready router

```python
async def route_and_answer(query, tenant_id, corpus_meta):
    # Pre-classify
    classification = await flash_classify(query, schema={
        "complexity": ["simple", "multi_hop", "synthesis"],
        "freshness": ["static", "dynamic"],
    })
    
    if corpus_meta.size_tok < 200_000 and corpus_meta.static:
        # Pure long-ctx + cache
        return await long_ctx(query, full_corpus, cache_key=corpus_meta.hash)
    
    if corpus_meta.size_tok > 2_000_000 or corpus_meta.freshness == "real_time":
        # Pure RAG
        chunks = await hybrid_search(query, tenant_id, k=10)
        return await rag_answer(query, chunks)
    
    if classification.complexity in ("multi_hop", "synthesis"):
        # Hybrid: RAG narrow → long-ctx within
        docs = await hybrid_search(query, tenant_id, k=10, level="doc")  # doc-level
        narrow = pack_docs(docs, max_tok=500_000)
        return await long_ctx(
            query, narrow,
            cache_key=f"{tenant_id}:{hash(tuple(d.id for d in docs))}",
        )
    
    # Default: pure RAG (cheap)
    chunks = await hybrid_search(query, tenant_id, k=10)
    return await rag_answer(query, chunks)
```

### 🎬 45-min answer rhythm

```
0-5    Clarify: corpus size / static-dynamic / multi-tenant / multi-hop / QPS / citation strictness
5-10   Mental model: 2024 "long-ctx killed RAG" myth → 2026 hybrid 共识
10-20  Decision tree (corpus × cost × multi-hop × freshness)
20-30  Cost math (2026 pricing) + prefix cache mechanics (90% off cached)
30-37  Hybrid pattern (RAG narrow → long-ctx within) + citation strategy
37-42  Real-time / multi-tenant / vendor lock-in / lost-in-middle 4 个 gotcha
42-45  简历 quote (ConvFinQA per-tenant RAG → Claude 200K)
```

### 🔑 Decision mnemonic

```
< 200K static low-vol         → Long-ctx + cache ⭐
< 200K dynamic                → RAG (cache 失效)
200K-2M single tenant         → Pure Pro 2M
200K-2M multi-tenant          → Hybrid (RAG narrow → ctx)
> 2M                          → Pure RAG
> 2M + multi-hop high-stake   → Hybrid + Rerank → ctx
Real-time data                → Pure RAG (hot index 5min)
Citation regulated            → RAG / Hybrid (chunk_id 天然)
```
```
