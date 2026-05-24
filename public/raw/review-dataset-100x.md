## AI Deep Dive #2 · Dataset 100x — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](dataset-100x.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`dataset-100x.html`](dataset-100x.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"dataset / corpus 100x 怎么 scale"**, 我按这 8 层回答, 不跳序. **核心心法: 先 bottleneck 定位 (不是 brute force), 再 ingest pipeline, 再 index/storage 分层, 再 retrieval 优化, 最后 cost math + ConvFinQA / Voice agent hook**.

### 📐 Dataset 100x Scaling — 8 层结构

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 (literal) |
|---|---|---|---|---|
| 1 | Bottleneck 定位 (不 brute) | 20s | 100x = 不同 bottleneck: 10k→1M ingest, 1M→100M storage/index, 100M→10B retrieval. 先 profile 现状 P50/P99 ingest_throughput / index_size / retrieve_latency | "I don't 100x everything — I locate the bottleneck. 10k to 1M is ingest, 1M to 100M is index sharding, beyond that retrieval. Profile first" |
| 2 | Ingest pipeline 并行化 | 30s | 流水线 (parse → chunk → embed → metadata → index), 每 stage 独立扩, batch embed (vLLM 32-64 batch), checkpoint resume, idempotent (doc_id + content_hash), DLQ retry | "Pipeline: parse, chunk, embed, metadata enrich, index — each stage horizontally scaled. Batch embed via vLLM 32-64. Idempotent on doc_id + content_hash so we resume on failure" |
| 3 | Embedding cost/速度 trade-off | 30s | bge-m3 self-host vs OpenAI 3-large API. 100M chunks × 500t = 50B token. OpenAI $0.13/1M = $6.5K. A100 spot $0.5/hr × 2800 hr ≈ $1.4K self-host. 100x → 必须 self-host | "100M chunks × 500 tokens = 50 billion. OpenAI 3-large API: $6.5K. Self-hosted bge-m3 on A100 spot: ~$1.4K for 2800 GPU-hours. The math forces self-host" |
| 4 | Index 分层 (hot/warm/cold) | 30s | HNSW in-memory hot (top 10% access, last 30d), pgvector warm, parquet cold; per-tenant shard; embedding distill 768→256 saves 3x memory | "Tiered: HNSW in-memory hot for the 10% accessed in last 30 days, pgvector warm, parquet cold. Distill embedding 768 to 256 — quality drops < 2 points, memory drops 3x" |
| 5 | Retrieval latency 优化 | 30s | ANN (HNSW M=16 ef=200), pre-filter ACL/tenant 硬 WHERE, rerank latency budget < 200ms 跳 否则 top-50→10, distill rerank model, Redis cache 5-min TTL | "HNSW M=16 ef=200, pre-filter ACL and tenant as hard WHERE, rerank only when budget allows. Cache popular queries 5-min TTL — 30% hit rate cut P50 in half" |
| 6 | Drift / 维护 | 25s | embedding_model_version metadata (模型升级 = blue-green re-embed), freshness_score decay, content_hash 增量, 月度全量重 index | "Every chunk carries embedding_model_version. Model upgrade is blue-green re-embed, not in-place. Content_hash for delta detection, incremental index daily, full rebuild monthly" |
| 7 | Cost math + LLM routing | 30s | Storage 100M × 256d × 4B = 100GB ~$100/mo, retrieve $2K/mo, generation route Gemini 3 Flash $0.50/$3 不是 Pro $2/$12, 4x 便宜; escalate to Pro on confidence < 0.7 | "Storage ~$100/mo, retrieve ~$2K/mo. Generation I route to Gemini 3 Flash at $0.50 in / $3 out, escalate to Pro $2/$12 only when retrieve confidence < 0.7 — 4x cost saved on 80% of queries" |
| 8 | Resume hook | 15s | Voice agent 7 markets 6 languages per-market shard / ConvFinQA 9-variant ablation methodology / Internal Agent Platform shared workflow | "I've shipped per-market sharding on the Voice agent — 7 markets, 6 languages, BGE-M3 multilingual, per-tenant HNSW. And ConvFinQA where I designed the 9-variant ablation that proved which scaling levers matter" |

### 🎯 为啥按这个序

**先 bottleneck 再 pipeline 再 cost**: 100x 是 trap question — 面试官想看你 "不 brute force". 先定位 (10k→1M 不是同一个问题), 再 stage 并行化, 再 storage 分层, 最后 cost math + resume hook 落地. **Embedding cost math + Gemini 3 Flash routing 是 differentiator**.

### 🔥 哪一层最容易被追问 deeper

- **Layer 3 (Embedding cost)**: "self-host 真的 $1.4K? 怎么算?" → A100 BGE-M3 throughput ~5K tok/s batch 64, 50B / 5K = 10M sec = 2800 GPU-hour, A100 spot $0.5/hr ≈ $1.4K. 不算开销 (parse / I/O), real 可能 2-3x
- **Layer 4 (Tiered storage)**: "怎么知道 10% hot? 怎么 promote/demote?" → access log Bloom filter, 每 6h 重排 hot set, LRU eviction warm→cold

### ⏱ 时间压缩版 (30 min round)

- 30s: "Bottleneck 不同 stage 不同. Pipeline 并行 + self-host embed + tiered storage + Gemini Flash routing 是核心"
- 1 min: + 5 decision sub-layers + cost math 一句
- 2 min: + Voice agent 7 markets concrete numbers + ConvFinQA ablation hook

### 🆘 卡壳兜底 (针对这题)

1. **不知道具体 throughput 数**: "It depends on the embedding model — for BGE-M3 on A100 I've seen 3-5K tokens/sec batch 64, but for a different model you'd benchmark first. The point is the throughput is bounded, so you parallelize"
2. **被问到 1B+ doc**: "Honestly I haven't run 1B production myself — closest was Voice agent in the millions. At 1B I'd think distributed (Vespa, Vald), shard by tenant + hash, ScaNN or DiskANN over HNSW. I'd want to talk to someone who's done it"
3. **被问到 streaming / real-time ingest**: "Stream via Kafka, embed worker pool, write to staging index with TTL, promote to main in batches. The trade-off is freshness vs index churn — I've done batch hourly, not true real-time"

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

> **100x 不是 "100 倍", 是「架构换、成本结构变、组织 process 变」**. 拐点 10k→1M (单机→分布式 batch) / 1M→100M (单节点 vector DB→分片+多 GPU) / 100M→10B (batch→streaming, HNSW→DiskANN) / 10B+ (集中→lakehouse, train→continual). 5 维度: ingest / storage / train / serve / label / eval / cost.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Spark | 老牌 batch ETL framework | 10k+ doc 分布式 |
| Ray | ML-native distributed train/serve | Python-friendly |
| Dask | Pandas-like 分布式 | smaller scale |
| Sharding | 按 key 拆数据到多节点 | 1M+ vector DB |
| Hot shard | 80% 流量打到 20% 节点 | sharding key 选错经典事故 |
| HNSW | Hierarchical Navigable Small World | in-memory vector index |
| DiskANN | disk-based ANN | 100M+ 时换 |
| IVF | Inverted File Index | clustering 减搜索空间 |
| DDP | Distributed Data Parallel (PyTorch) | model 装单卡时 |
| FSDP | Fully Sharded Data Parallel | model 不装单卡时 |
| ZeRO-3 | DeepSpeed zero redundancy | 同 FSDP |
| 3D parallelism | TP + PP + DP | 100B+ model |
| Tensor Parallel | 一层切片到多卡 | layer 太大 |
| Pipeline Parallel | layer 分组到多 stage | very deep model |
| Weak supervision | rules / LLM generate noisy labels | 100M+ unlabeled |
| Snorkel | weak supervision framework | labeling functions |
| Active learning | model 选 uncertain case 给人标 | 标注 budget 紧 |
| Statistical power | sample n ≈ (1.96+0.84)² σ²/Δ² | eval sample size |
| Iceberg | 表格式 lakehouse storage | 10B+ scale |
| KV cache | LLM serving 关键资源 | hot shard 时 OOM |

### 🎯 5 个核心 framework

**Framework 1**: Scale Breakpoint Decision (10k / 1M / 100M / 10B+)
- When: 拿到 100x 题第一刻
- Algorithm:
  - 10k → 1M: 单机 Pandas → Spark / Ray distributed batch
  - 1M → 100M: 单节点 vector DB → Qdrant / Pinecone cluster sharded, 单 GPU → multi-GPU DDP
  - 100M → 10B: batch → streaming + Kafka, HNSW → DiskANN / IVF-Disk
  - 10B+: 集中 → Iceberg lakehouse, per-batch → continual learning
- Trade-off: 早换太复杂, 晚换炸
- Tools: Spark / Ray / Dask, Qdrant / Pinecone / Milvus / Vespa, DDP / FSDP / DeepSpeed

**Framework 2**: Distributed Training Picks
- When: model + data 不装单卡
- Algorithm:
  - DDP (PyTorch): model fits single GPU, batch 并行
  - FSDP / ZeRO-3: model 不装, shard params + grad + optimizer state
  - 3D parallelism (Tensor + Pipeline + Data): 100B+ model
  - LoRA / QLoRA: 训 7B-70B on 单 8xH100, base frozen
- Trade-off: complexity, debug 难度
- Tools: PyTorch DDP / FSDP, DeepSpeed, Megatron-LM, PEFT for LoRA

**Framework 3**: Sharding Key Selection
- When: 数据存储分片
- Algorithm:
  - hash(user_id): uniform 但失 locality
  - tenant_id: multi-tenant 友好但 hot-shard 风险
  - region + language: compliance + latency ⭐ (TikTok 用)
  - composite (region, tenant, ts): 复杂但灵活
- Trade-off: locality vs uniformity vs compliance
- Tools: consistent hashing, virtual nodes, hot shard detector

**Framework 4**: Cost Optimization Stack (Priority Order)
- When: scale cost 爆
- Algorithm:
  1. Prompt caching (70-90% input save, Anthropic / OpenAI / Gemini support)
  2. Smaller model tiering (5-10x: Haiku for easy, Sonnet for hard)
  3. Self-host open model (5-10x at scale: Llama / Qwen)
  4. Quantization (2-4x: INT8 / INT4)
  5. Result caching by query hash (30-90% by hit rate)
  6. Speculative decoding (2-3x latency speedup)
- Trade-off: quality vs cost, infrastructure 成本
- Tools: vLLM / SGLang / TGI, GPTQ / AWQ quantization, Redis cache, prefix-cache routing

**Framework 5**: 100x Eval Methodology
- When: 不能 manual review 100k
- Algorithm:
  - Sample size by effect size: 5-10k 通常 enough (statistical power)
  - Stratified by slice: language / difficulty / domain / customer_tier
  - Online sampling + LLM-judge (Haiku batched, kappa > 0.6 校准)
  - Drift detection: KL / Wasserstein on input distribution
  - Statistical significance test per slice
- Trade-off: 不可 manual all, 但 sampling 失精度
- Tools: scipy.stats, LLM-judge with Cohen kappa, BigQuery sample stratified

### 🌳 关键决策树

```
数据规模 N?
├── < 10k → Notebook + Pandas + SQLite + manual eval
├── 10k-1M → Single Python + Postgres + Single GPU + LoRA + LLM-judge
├── 1M-100M → Spark/Ray + Sharded vector DB + DDP multi-GPU + stratified sample
├── 100M-10B → Spark + Vespa/Milvus + Multi-node FSDP + sampled eval + streaming
└── > 10B → BigQuery/Snowflake/Iceberg + continual training + sampled+streaming eval

Model 大小 vs Memory?
├── 7B fits A100 80GB → LoRA single GPU
├── 13B+ → DDP 2-4 GPU
├── 70B+ → FSDP / ZeRO-3 8 GPU
└── 100B+ → 3D parallelism (TP + PP + DP)

Labeling budget?
├── < 10k → 100% manual ($2k)
├── 100k → 10% manual + 90% weak supervision (Snorkel rules + cheap LLM + regex)
├── 10M+ → 1% manual + active learning + synthetic
└── 100M+ → boostrap from existing logs, no manual

Storage budget?
├── < 1M docs → Postgres + pgvector
├── 1M-100M → Qdrant/Pinecone cluster mode + hot/cold tier
├── 100M-1B → DiskANN + S3 cold + Redis hot
└── > 1B → Iceberg lakehouse + Iceberg+Vespa hybrid
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: Data Infrastructure (Storage + Distributed Processing)**
- 核心解法:
  ```python
  # Ingest
  spark.read.parquet(s3_path).repartition(200) \
    .write.format("iceberg").save("warehouse.docs")
  # Or Ray for ML
  ds = ray.data.read_parquet(s3_path)
  ds.map_batches(embed_fn, num_gpus=1).write_parquet(out)
  
  # Storage tier
  hot (last 30d): Redis + Pinecone HNSW
  warm (30d-1yr): Qdrant cluster
  cold (> 1yr): DiskANN on EBS / S3
  
  # Sharding (region + language) 我们 TikTok 用
  shard_key = f"{region}_{language}"
  ```
- Top 3 gotchas: hash(user_id) 失 locality compliance / 单节点 HNSW > 10M / 没断点续跑
- Tools: Spark / Ray, Iceberg, Pinecone / Qdrant cluster, DiskANN

**Problem 2: Training & Serving Impact**
- 核心解法:
  ```python
  # DDP for model fits
  model = nn.parallel.DistributedDataParallel(model, device_ids=[local_rank])
  
  # FSDP for model doesn't fit
  from torch.distributed.fsdp import FullyShardedDataParallel
  model = FullyShardedDataParallel(model, sharding_strategy=ShardingStrategy.FULL_SHARD)
  
  # 3D parallelism (Megatron-LM)
  # TP=8 (tensor) + PP=4 (pipeline) + DP=2 (data)
  
  # Serving
  vLLM with prefix caching (system prompt 共享 70-90% input)
  Speculative decoding (Llama 70B + Llama 7B draft)
  Continuous batching
  ```
- Top 3 gotchas: batch size 不调炸 OOM / KV cache pressure under load / 没 prefix caching
- Tools: PyTorch DDP/FSDP, DeepSpeed, Megatron, vLLM / SGLang / TensorRT-LLM

**Problem 3: Quality at Scale (Sampling, Weak Sup, Active Learning)**
- 核心解法:
  ```python
  # Weak supervision (Snorkel)
  @labeling_function()
  def lf_keyword_match(row):
      return SPAM if 'free $$$' in row.text.lower() else ABSTAIN
  @labeling_function()
  def lf_cheap_llm(row):
      return haiku.classify(row.text)  # $0.001 per call
  applier = PandasLFApplier([lf_keyword_match, lf_cheap_llm, ...])
  L_train = applier.apply(df_train)
  
  # Active learning
  uncertainties = model.predict_uncertainty(unlabeled)
  to_label = uncertainties.top_k(1000)  # 人工标 boundary
  
  # Bootstrap: 1% manual gold → train weak → label rest
  ```
- Top 3 gotchas: 100% manual 不 scale / weak supervision 没 conflict resolution / active learning 没 uncertainty calibration
- Tools: Snorkel, Cleanlab, modAL active learning, Haiku as cheap labeler

**Problem 4: Cost Economics**
- 核心解法:
  ```
  Prompt caching: 70-90% input save (Anthropic 90% off cached, Gemini 75% off, OpenAI 50% off)
  Model tiering: Haiku ($0.25/$1.25) → Sonnet ($3/$15) → Opus 4.7 ($5/$25). 5-10x save.
  Self-host: 5-10x cheaper at > 1B token/month
    Llama 3.1 70B on H100: $0.50/M token vs OpenAI $5/M
  Quantization: INT8 2x, INT4 4x. Quality 1-2% drop on most tasks.
  Result caching: query hash → cached response, 30-90% hit by usage pattern
  Speculative decoding: 70B + 7B draft, 2-3x latency speedup
  
  2026 pricing:
    Gemini 3 Pro $2 / $12
    Gemini 3 Flash $0.50 / $3
    Claude Opus 4.7 $5 / $25
    GPT-5.5 $5 / $30
  ```
- Top 3 gotchas: 全用 Opus 4.7 (5-10x 浪费) / 没 prompt cache / 没 monitor cost dashboard
- Tools: FinOps dashboard (Vantage / Datadog), per-tenant cost attribution, alert on > 10% growth

**Problem 5: Evaluation at Scale**
- 核心解法:
  ```python
  # Statistical power
  n = (1.96 + 0.84)**2 * sigma**2 / delta**2
  # For 5pp detection at 80% power: n ~ 5k
  # 100x data ≠ 100x sample, cap 30k-100k 够
  
  # Stratified sampling
  strata = ['language', 'difficulty', 'domain', 'customer_tier']
  sampled = df.groupby(strata).apply(lambda g: g.sample(min(len(g), 200)))
  
  # Online LLM-judge (Haiku batched)
  judge_score = haiku.batch_complete([judge_prompts])  # $0.001 each
  kappa = cohen_kappa(human_score, judge_score)  # > 0.6
  
  # Drift detection
  kl = sum(p * np.log(p/q) for p, q in zip(today_dist, baseline_dist))
  if kl > 0.5: alert
  ```
- Top 3 gotchas: 100x sample = 100x cost (实际 30k 够) / 不 stratify aggregate 掩盖 / LLM-judge 不 calibrate
- Tools: scipy.stats kendalltau / ks_2samp, BigQuery sampling, Haiku batched judging

### 🔥 Production gotchas (top 15)

1. Linear projection (100x = 100 倍) → 架构不换 explode
2. 单机 architecture for > 100M → 单节点 HNSW 20GB 装不下
3. Embed in same model after upgrade → 必须 re-embed 全部
4. 没 incremental ingest → 一次性 batch 处理时间不可接受
5. 假设 manual labeling scale → 100k 不能 100 周
6. 没 graceful degradation → scale 下某 feature 崩
7. 没 cost monitoring → bill shock 月底爆
8. Sharding key 选 hash(user_id) → 失 locality + compliance
9. 没断点续跑 → 8h ETL 中途 OOM 重头来
10. KV cache pressure 没 monitor → load 下 OOM
11. 没 prefix caching → input cost 高 5-10x
12. 没 stratify eval → aggregate 改善某 language 退步
13. LLM-judge 不 calibrate → kappa < 0.6 噪声大
14. 没 region serving → cross-region latency P99 爆
15. 100% manual labeling → 标注 budget 不可线性

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| 7 markets → 30 markets | Voice agent | scaling 100x markets, language transfer |
| Per-language SFT/DPO | Voice agent 6 lang → 20 lang | cross-lingual transfer |
| Region sharding | TikTok PayLater | region+language sharding 真做过 |
| Distributed training | Voice agent RL alignment | DDP/FSDP on H100 |
| Weak supervision | BNPL chatbot | rules + cheap LLM + regex Snorkel |
| Active learning | BNPL intent | uncertain query → human queue |
| Eval at scale | ConvFinQA stratified 300 | scale to 30k via LLM-judge |
| Cost optimization | Voice agent vLLM + prefix cache | 70% input save |
| Migration dual-write | Voice agent v2 rollout | shadow → 1% → 50% → 100% |

### 🎤 面试现场 quotables (top 8)

1. "100x isn't 100 times — it's a different architecture at every break point"
2. "What breaks first at 100x is usually embedding cost, not query speed — re-embedding on model upgrade is $1k+"
3. "We sharded by region + language at TikTok — compliance and latency, both wins. Hash sharding loses locality"
4. "At 100M I'd switch from HNSW in-memory to DiskANN — single-node index build becomes the bottleneck"
5. "5pp recall loss for 50% latency improvement is an OK tradeoff at scale — Pareto front, not absolute best"
6. "Statistical power says 5k samples detect 5pp at 80% power. 100x data doesn't mean 100x sample size"
7. "Prompt caching 70-90% input save is my first cost lever before anything else — Haiku tiering, self-host come second and third"
8. "Migration is never big-bang. Dual-write week 3, 1% A/B week 4, 50% week 5, 100% week 6. Keep old readable 30d"

### 🚨 红线 (top 10 anti-patterns)

1. Linear projection (100x = 100 倍)
2. 单机 architecture for > 100M
3. Embed same model after upgrade (must re-embed)
4. 没 incremental ingest
5. 假设 manual labeling scale
6. 没 graceful degradation
7. 没 cost monitoring
8. 100% Opus 4.7 (没 tiering)
9. Sharding 选 hash(user_id)
10. Big-bang migration
