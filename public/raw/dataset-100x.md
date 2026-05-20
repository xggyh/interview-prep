## 题目（verbatim）

> **[OpenAI Technical Screen, post take-home]**
>
> "Take-home was on small dataset. **What would you change architecturally if the dataset was 100x larger**?"

**出处**：OpenAI FDE 真题. Google Cloud FDE 必问 (Gemini + Vertex AI scaling).

**Round**：Technical Screen (60 min)

---

## 这道题在考什么

考你**scaling 思维**——take-home 是 toy problem, production 是另一回事:

1. **What breaks first at 100x** —— bottleneck 识别
2. **5 dimensions of scale** —— ingest / storage / index / query / cost
3. **trade-offs at scale** —— precision vs latency vs cost
4. **graceful degradation** —— 哪些 feature 在 scale 下牺牲
5. **knowing the platform** —— 用 Vertex AI / Pinecone / OpenSearch 的限制

---

## 5 个 scale dimensions

| Dim | 100x impact | What breaks |
|---|---|---|
| **1. Ingestion** | 100x docs to embed | Embedding API rate / cost / time |
| **2. Storage** | 100x vectors | Memory budget, cluster size |
| **3. Index build** | 100x indexing time | Single-node infeasible |
| **4. Query latency** | More vectors to search | ANN recall degrades, p99 grows |
| **5. Cost** | 100x compute + storage | Budget |

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-3 min | Frame: assume 1M docs → 100M docs |
| 3-10 min | Walk through 5 scale dimensions, what breaks |
| 10-25 min | Architecture changes for each |
| 25-40 min | Cost / latency tradeoffs |
| 40-60 min | Deep dive on chosen change |

---

## 我会这样答（sample）

> "Assume take-home was 1k docs, 100x = 100k. Or if take-home was 1M, 100x = 100M docs. Walk through both since architecture changes are different.
>
> **For 100k docs** (1k → 100k):
> - **Ingestion**: 100k embeds @ 50ms/doc = 1.4h serial → batch parallel + OpenAI batch API → 30 min
> - **Storage**: 100k × 1.5KB = 150MB → still fits in RAM, no infra change
> - **Index**: rebuild on every add infeasible → switch to **incremental index** (HNSW supports add)
> - **Query**: HNSW p99 < 50ms at 100k → fine
> - **Cost**: 100k × $0.0001 embed = $10 one-time, $0.001/query — cheap
>
> Most changes are **operational**, not architectural.
>
> **For 100M docs** (1M → 100M):
> - **Ingestion**: 100M @ 50ms = 1400h serial → MUST batch + parallel + distributed → 10 days even with 100 workers
> - **Storage**: 100M × 1.5KB = 150GB — RAM-tight. **Switch to disk-backed ANN** (DiskANN / FAISS IVF-Disk) or **per-shard cluster**
> - **Index**: 100M HNSW won't fit single-node. **Sharded index** (10 shards × 10M each) with parallel query
> - **Query**: HNSW recall degrades at scale → **2-stage retrieve**: cheap shard 1 (recall@100), expensive rerank top-10
> - **Cost**: $10k+ one-time embed, $0.05/query — material
>
> **Architecture diff**:
>
> ```
> 1k - 1M docs:        Single-node HNSW + bi-encoder rerank
> 1M - 100M docs:      Sharded HNSW (or IVF) + 2-stage rerank
> > 100M docs:         Distributed cluster (Vespa / Milvus) + tiered hot/cold
> ```
>
> **At 100M I'd specifically change**:
> 1. **Embedding model**: maybe distill to smaller (768→256 dim) to save 3x storage
> 2. **Vector quantization**: PQ (Product Quantization) on cold tier, full precision on hot
> 3. **Sharding strategy**: by topic/category for query routing → only hit relevant shard
> 4. **Cache layer**: top-1000 common queries cached in Redis, 90% hit rate at 5ms
> 5. **Async indexing**: docs queued, indexed within 5 min, eventually consistent
> 6. **Cold tier**: docs not accessed in 30 days → moved to S3 (still retrievable but with latency premium)
>
> **What breaks first** in my experience: **embedding cost + ingestion time**, not query speed. People underestimate this:
> - 100M docs × $0.0001 = $10k for first embed
> - On every model upgrade, re-embed → $10k each time
> - **Lesson**: pick embedding model carefully because migration is expensive
>
> **Tradeoffs at 100M I'd accept**:
> - **Recall@10 drops 5pp** (from 92% to 87%) for 50% latency reduction
> - **5-min indexing lag** for 10x cost reduction
> - **Cold queries slower** (200ms vs 50ms) for 90% storage cost reduction
>
> **What I'd NOT change** at 100M:
> - Reranking (still cheap relative to retrieval)
> - Embedding model (consistency across vectors > cost)
> - Hybrid retrieval (BM25 scales fine)"

---

## 简历专属 reframe

你的 **TikTok scale (1B users)** + **vLLM/SGLang infra**:

| 题 | 你做过 |
|---|---|
| 100x scale planning | TikTok payment scale — 你 daily 想 |
| Distributed inference | vLLM / SGLang you optimized |
| Cost-aware architecture | Voice agent 7 markets 你必 cost-tune |
| Sharding strategy | 你处理过多 region routing |

**主动说**:

> "At TikTok we constantly think about 100x — what was per-region in Singapore at 10M users becomes per-region across 7 markets at 100M users. The pattern I learned: **embedding cost + ingestion time hit first, not query speed**. We had to switch to distilled embedding (768→384) + per-region sharding by language to control cost. The trick: **never re-embed entire corpus on model upgrade — embed delta, run dual-index during migration, cutover when new is faster**."

---

## 5 follow-ups

**Q1**: "Cold tier queries — how slow is acceptable?"
**A**: Depends on user expectation:
- Interactive query (user waiting): < 500ms total budget
- Background / async (e.g., batch reports): < 30s
- For cold queries that miss hot tier, **partial result fast** (top-10 from hot) + **full result async** (top-100 from hot + cold)
- User UX: "showing top results now, full results refreshing..."

**Q2**: "How do you migrate embeddings on model upgrade?"
**A**: **Dual-index pattern**:
- Build new index in shadow (read v2 while serving v1)
- Run **A/B for 1 week** — same query, return both v1 + v2 results, measure recall + user metrics
- If v2 is better on user metrics, cutover
- Keep v1 readable for 1 month (rollback safety)

**Q3**: "Cost is bigger concern than latency. What changes?"
**A**: Aggressively:
- Distilled embedding (50% storage save)
- Aggressive PQ quantization (8x compression, 5pp recall loss)
- Smaller rerank model
- Aggressive cache (24h TTL on results)
- Cold tier earlier (after 7 days idle)

**Q4**: "Distributed system means new failure modes. How handle?"
**A**:
- **Query fan-out**: ask all shards, merge top-K. If a shard fails, **degraded result** (top-K from N-1 shards) rather than 5xx
- **Shard rebalancing**: hot shard detected → split. Live, no downtime
- **Re-index after failure**: shard goes down + comes back → reads from replica, no service interruption
- **End-to-end SLO**: degraded vs failed, alert on degraded but don't page

**Q5**: "Customer wants real-time index. Embed in < 1s after upload."
**A**:
- 1s embed feasible for single doc (50ms embed + 100ms HNSW add + 100ms commit)
- Batch ingest > 100 docs/s breaks single-node ingest queue
- Mitigations:
  - **Write-ahead log** (Kafka) for ingest events
  - **Multi-shard parallel ingest**
  - **Tiered ingest priority**: VIP customer ingests prioritized

---

## ❌ 易错点

1. **Just "use Pinecone scaling"** — vendor lock-in answer
2. **Same architecture for 100x** — 1M vs 100M needs different design
3. **Ignore cost** — 100x docs = 100x embed cost
4. **Reranking 不 scale** assumption — 实际 reranks scale fine
5. **Single-node HNSW for 100M** — won't fit
6. **No graceful degradation** — fail loud > degrade quiet
7. **Forget operational** (rate limits, batch APIs)

---

## ✅ 加分项

1. **5-dimension scale framework**
2. **Different architecture for 100k vs 100M**
3. **Embedding cost + migration as #1 concern**
4. **Dual-index migration pattern**
5. **PQ quantization + distilled embed** for cost
6. **Graceful degradation** (return partial top-K)
7. **Quote TikTok 1B user experience**
8. **Tradeoff transparency** (5pp recall for 50% latency)

---

## Cheat Sheet

```
5 scale dimensions:
  Ingest / Storage / Index build / Query latency / Cost

Architecture by scale:
  1k - 1M: single-node HNSW + bi-encoder + cross-encoder rerank
  1M - 100M: sharded HNSW or IVF + 2-stage rerank
  >100M: distributed Vespa/Milvus + tiered hot/cold

At 100M changes:
  - Distilled embedding (50% storage)
  - PQ quantization (8x compression)
  - Sharding by topic/category (query routing)
  - 5-min async indexing
  - Cache top-1000 queries
  - Cold tier after 30d idle

What breaks first:
  - Embedding cost (not query speed)
  - Re-embed on model upgrade ($10k+ each time)
  - Index build time on single node

Migration pattern:
  Dual-index v1 + v2 in parallel
  A/B for 1 week with metrics
  Cutover only on win
  Keep v1 readable 1 month

Tradeoffs accept:
  - 5pp recall for 50% latency
  - 5-min indexing lag for 10x cost down
  - Cold query 4x slower for 90% storage save
```
