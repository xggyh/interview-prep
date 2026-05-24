## T2.5 · reranking 架构 — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](gfde-t2-reranking.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t2-reranking.html`](gfde-t2-reranking.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"First-pass top-50, reranker picks top-10 — why, tradeoffs, how to evaluate"** 或 **"Cohere rerank vs cross-encoder vs LLM-as-judge — when each?"**, 我按这 8 层回答, 不跳序.

### 📐 Reranking Architecture — 8 层结构

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 |
|---|---|---|---|---|
| 1 | Clarify + Bi-encoder 失败场景 | 0-5 min | Latency budget (chat 200ms / batch 5s)? Volume? Multilingual? Domain (general / legal / medical)? **然后 demo**: query "iPhone 15 Pro Max dual SIM" → bi-encoder top-10 全是 "iPhone 12 dual SIM / Samsung dual SIM / iPad cellular" → top-1 错答. 真正答案排在 top-50 第 4 位 — bi-encoder 召回够但排序烂 | "Before reranking — let me show why pure bi-encoder fails ordering even when recall is fine. The answer is in top-50 at rank 4, but bi-encoder puts iPhone 12 doc at rank 1." |
| 2 | Bi-encoder vs Cross-encoder 机制 | 5-12 min | Bi-encoder: query + doc 各自独立 embed → cosine. 看不见 query-doc 交互. Pre-indexable, 1M doc 秒级 ANN. **Cross-encoder**: `[CLS] query [SEP] doc [SEP]` 一起进 Transformer, cross-attention 看 token-level alignment. 不能 pre-index, per-query 推理 50-200ms. 这就是为什么 cross-encoder 准但慢 | "Mechanism first. Bi-encoder is dual-tower, query and doc never see each other. Cross-encoder uses cross-attention to align tokens like 'Pro Max'. That's why it's slower but catches fine-grained matches." |
| 3 | Multi-stage cascade pipeline | 12-19 min | **Stage 0** Query understanding (rewrite / multi-query / HyDE) **Stage 1** BM25 + Dense → top-100 (RRF fusion) **Stage 2a** Cheap rerank (bge-v2-base CPU, ~100ms) → top-25 **Stage 2b** Expensive rerank (bge-v2-large GPU 或 Cohere rerank-3 API, ~200ms) → top-10 **Stage 2c** (optional) LLM-as-judge (Gemini 3 Pro / Opus 4.7, ~3-5s) → top-3 for high-stake | "Production isn't one reranker, it's a cascade. Cheap rerank narrows 100→25, expensive narrows 25→10, optional LLM-as-judge for top-3 high-stake. Each stage cuts cost without losing quality." |
| 4 | Reranker 模型选择表 | 19-26 min | **bge-reranker-v2-m3** (open, multilingual default, 80-150ms) / **bge-reranker-v2-large** (English better, 200-400ms) / **Cohere rerank-3** (API $1/1K, 150-250ms, excellent) / **mxbai-rerank-large-v1** (open, Cohere-class) / **JaColBERT** (late-interaction, 50-100ms) / **LLM-as-judge Gemini 3 Pro** ($0.10/query) / **LLM-as-judge Claude Opus 4.7** ($0.30/query, legal/medical) / **Domain finetuned bge** (1K-10K labeled pair, +5-10% NDCG) | "8 reranker options on the menu. Default open-source is bge-reranker-v2-m3 for multilingual. API default is Cohere rerank-3. LLM-as-judge for top-3 in high-stake domains." |
| 5 | Latency engineering | 26-33 min | GPU batch (50 doc 一次 forward 比 50 单次快 5x). FP16 / INT8 quantization (-50% latency, -1% accuracy). Distill smaller model (bge-large 200ms → bge-small 50ms). Cache (query_hash, doc_id) score pair: 30-40% hit. Pre-warm GPU on traffic spike | "Latency engineering is 5 levers — batch, quantize, distill, cache, prewarm. Production reranker p99 should be <250ms; if not, you missed one of these." |
| 6 | Eval methodology (NDCG > recall) | 33-40 min | Recall@k 不够 — 10 个里都对但顺序烂 NDCG 还是低. **NDCG@10** 是 reranking 主指标 (gain × discount by position). MRR for first-answer-position. Slice eval: per query type (concept / SKU / multi-hop) / per language / per domain. A/B with downstream metric (LLM answer accuracy) 不只 retrieval metric | "Reranker eval is NDCG-driven, not recall. Recall is set by first-stage; reranker job is ordering. Always slice by query type and language, and A/B with downstream answer accuracy." |
| 7 | Domain fine-tune + hard negative | 40-46 min | 1K-10K (query, positive, hard_negative) triplets. Hard negatives 来自 first-stage top-50 但实际无关 (混淆样本). Margin loss training. Production NDCG +3-8%. Synthetic data: LLM 生成 query for each doc, 再 LLM judge negative. 必 dedup query 防训练泄漏 | "Domain fine-tune is the last 5-8% NDCG. Hard negatives mined from first-stage's confusing top-50. Synthetic data via LLM-generated queries closes the labeled-data gap." |
| 8 | Connect + production hardening | 46-50 min | BNPL chatbot 7 markets + multilingual: bge-reranker-v2-m3 multilingual → NDCG@5 0.71→0.83, latency +180ms. Cache hit 35%. ConvFinQA reranker for numeric-heavy queries fine-tuned with 2K financial triplets, NDCG +6%. E-commerce learning-to-rank (LightGBM LambdaRank) for multi-objective (relevance + price + stock + delivery) | "Resume hook — BNPL multilingual rerank + ConvFinQA domain fine-tune + e-commerce learning-to-rank. Let me share the BNPL story with metrics." |

### 🎯 为啥按这个序

**Bi-encoder 失败场景 (Layer 1) 必须最先讲** — 不画失败 example 面试官不知道为啥要 reranker. Bi-encoder vs Cross-encoder 机制 (2) 必须在 cascade (3) 之前 — 不懂 cross-attention 不能解释为啥 cascade 有意义. Cascade (3) 是骨架. Model table (4) 是 menu. Latency engineering (5) 单列因为 production 没这个就上不了 chat 200ms SLA. **Eval methodology (6) 必讲 NDCG > recall** — 这个 nuance 是分水岭. Domain fine-tune (7) 单列因为它是最后 5-8% 提升的来源, 体现 staff 思考. Resume close (8) 用 BNPL NDCG 0.71→0.83 数字最有说服力.

### 🔥 哪一层最容易被追问 deeper

- **Layer 4 (model choice)**: "Cohere vs bge 怎么选?" → 准备 commercial (Cohere) vs self-host GPU 成本 trade-off + latency / quality 数据.
- **Layer 6 (NDCG)**: "NDCG 公式?" → 准备 DCG = sum(rel_i / log2(i+1)), NDCG = DCG / IDCG (perfect ranking). 重点是 position-discounted.
- **Layer 7 (hard negative)**: "怎么 mine hard negative?" → 准备 "first-stage top-50 但人工 / LLM judge 实际无关 = hard. Random 是 easy negative, BM25 confuse 是 hardest negative".

### ⏱ 时间压缩版 (30 min round)

- Layer 1 (failure scenario) 3 min — 必讲
- Layer 2 (mechanism) 4 min
- Layer 3 (cascade) 5 min — 必讲, 骨架
- Layer 4 (model table) 3 min
- Layer 5 (latency engineering) 4 min
- Layer 6 (eval) 4 min — 必讲 NDCG insight
- Layer 7 (domain fine-tune) 跳过 / 2 min
- Layer 8 (connect) 3 min

### 🆘 卡壳兜底 (针对这题)

- 忘了 NDCG 公式 → 退回讲「**核心 idea: position-discounted gain. rank 1 doc 全计, rank 10 doc 折扣. Normalize by perfect ranking 得 [0,1] score**」
- 忘了具体 reranker 模型名 → 退回讲「**3 大族: bge-reranker (open) / Cohere rerank (API) / LLM-as-judge. 默认 bge-v2-m3, 升级 Cohere 或 LLM-judge**」
- 被追问 cross-encoder latency 怎么救 → 退回讲「**5 levers: GPU batch / quantize FP16/INT8 / distill smaller / cache score / prewarm. p99 < 250ms 是 production 标准**」
- 被追问 LLM-as-judge 怎么用 → 退回讲「**Pointwise score 1-5 / pairwise compare / listwise rank 三种. 贵, 只 top-3 final 用. 法律 / 医疗 / 资金高 stake**」
- 被追问 reranker 不 work 的场景 → 退回讲「**Recall already 100% top-K (小 corpus / 完美 first-stage) → reranker 无价值. Very short query 1-2 token → cross-encoder 也分不清**」

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

Reranker = **cross-attention 看 (query, doc) 联合 score**, bi-encoder 必须先 narrow 到 top-50 才合理; cascade (cheap → expensive → optional LLM-judge) + GPU batch FP16/INT8 + cache (q, candidates) + domain finetune, NDCG +8-18pp at +60-200ms.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| **Bi-encoder** | Q/D 独立 forward, cosine, ms 级 | 第一阶段 ANN 召回 |
| **Cross-encoder** | [q; d] 联合 forward, 50-200ms/pair | 第二阶段 rerank top-50 |
| **ColBERT** | Multi-vec per doc + MaxSim | 中间路线, 比 cross 快 |
| **JaColBERT** | ColBERT 日语 / multilingual 版 | 多语 / late interaction |
| **LLM-as-judge** | LLM 直评 pointwise/pairwise/listwise | High-stake top-3 final |
| **Pointwise** | LLM 给每 doc 单独 score | LLM judge 简单 |
| **Pairwise** | LLM 比 doc A vs B | LLM judge 准但 O(n²) |
| **Listwise** | LLM 看全 list 排序 | LLM judge 最准但贵 |
| **bge-reranker-v2-m3** | BAAI 开源 multilingual, 150ms | Default self-host |
| **Cohere rerank-3** | API $1/1K, 200ms | 不想 self-host GPU |
| **mxbai-rerank-large-v1** | mixedbread Cohere-class 开源 | 自部署高质量 |
| **Cascade** | cheap → expensive 多阶段 | 省 50% latency |
| **GPU batch + FP16** | 32-64 batch, half precision, 2x 提速 | 必备 |
| **TensorRT INT8** | NVIDIA 编译 + 量化, 3x 提速 | 极致 latency |
| **Distillation** | 大模型 → 小模型, 5x speed, 1-2pp 损 | Latency budget 紧 |
| **Hard-negative mining** | top-ranked-but-not-clicked 作 negative | Finetune 必备 |
| **NDCG** | DCG / IDCG, position-sensitive | Rerank 核心指标 |
| **MRR** | Mean Reciprocal Rank, 1/rank_first_relevant | 单答案场景 |

### 🎯 5 个核心 framework

**Framework 1**: Bi-encoder vs Cross-encoder
- When: 决定阶段使用
- Algorithm: Bi 独立 forward + cosine (1B doc 可 pre-index); Cross 联合 [CLS] q [SEP] d cross-attention
- Trade-off: Bi 快但粗, Cross 慢但准
- Tools: bge-large (bi), bge-reranker-v2-m3 (cross)

**Framework 2**: Reranker Options 矩阵
- When: 选哪个 reranker
- Algorithm: bge-reranker-v2-m3 free multilingual / bge-large 单语好 / Cohere API 省事 / mxbai 自部署 / LLM-judge 高 stake / domain finetune 1-2pp 上限
- Trade-off: 自部署 GPU 钱 vs API 调用钱
- Tools: HuggingFace, Cohere API, vLLM serving

**Framework 3**: Cascade Optimization
- When: 减 latency
- Algorithm: top-100 (bi) → bge-base 50ms top-25 → bge-large/Cohere 200ms top-10 → LLM-judge 3-5s top-3 (optional)
- Trade-off: 多 hop 但总 latency 省 50%
- Tools: 自实现 cascade, Triton ensemble

**Framework 4**: Latency Engineering
- When: P99 > 300ms 或 GPU 利用率 < 70%
- Algorithm: GPU A10G/A100 + FP16 (2x) + INT8 TensorRT (3x) + batch 32-64 (3x throughput) + distillation 5x speed + caching (q, candidates) Redis 1h TTL
- Trade-off: 量化 1-2pp NDCG 损, distill 2-3pp
- Tools: TensorRT, vLLM, Triton, TGI, Redis cache

**Framework 5**: Eval + Domain Finetuning + A/B
- When: 上 prod 前必做
- Algorithm: NDCG > Recall (set 不变, 排序变); slice eval (short/long/acronym/SKU/multilingual); A/B prod CTR top-3 / time-to-click / thumbs; domain finetune: prod clicks + LLM synthetic + hard-neg mining + MSE distill + margin ranking, 1-2 GPU-day $50-100, +3-8pp NDCG
- Trade-off: finetune 维护 weekly 重跑
- Tools: sentence-transformers, HuggingFace Trainer, BEIR, MTEB, Phoenix

### 🌳 关键决策树 (ASCII)

```
Q: 我该用哪个 reranker?
├── 起步 / multilingual 必要        → bge-reranker-v2-m3 (free) ⭐
├── 英文单语 + 自部署 GPU OK         → bge-reranker-large
├── 不想自部署 + 预算 OK             → Cohere rerank-3 ($1/1K)
├── 自部署 + Cohere-class quality    → mxbai-rerank-large-v1
├── 日语 / late interaction          → JaColBERT
├── 高 stake top-3 (legal/medical)   → + LLM-judge (Gemini 3 Pro / Opus 4.7)
├── 有 1K-10K labeled pair           → Domain finetune (+3-8pp NDCG)
└── Latency p99 < 100ms 必须         → distillation 或 ColBERT

Q: Cascade 层级?
├── Top-100 输入                     → bge-base 50ms → top-25
├── Top-25 输入                      → bge-large / Cohere 200ms → top-10
├── Top-10 + 高 stake                → LLM-judge 3-5s → top-3
└── Top-3                            → 直接送 LLM context

Q: 怎么 squeeze latency?
├── 模型 FP32 → FP16                → 2x
├── FP16 → INT8 + TensorRT          → 3x (1-2pp 损)
├── Batch 1 → 32-64                 → throughput 3x
├── 大模型 → distill 小              → 5x speed (2-3pp 损)
├── 加 Redis cache (q, candidates)  → 30-40% hit, 直接绕过 inference
└── CPU forward                      → 永远不要
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: Bi-encoder vs Cross-encoder 数学**
- Bi forward: `E_q = encoder(q); E_d = encoder(d); score = cos(E_q, E_d)` — 双塔独立, 可 pre-index
- Cross forward: `score = head(encoder([CLS] q [SEP] d [SEP]))` — 联合, 不可 pre-index
- Attention view: cross 有 q-d block (q token vs d token 对齐), bi 没有
- 量化对比: NDCG 0.65 (bi only) → 0.83 (+ cross-encoder rerank), +18pp; 但 latency 50ms → 230ms
- ColBERT 中间路线: per-token doc embedding + MaxSim, 50-100ms, quality 接近 cross
- Top 3 gotchas: bi 用作 rerank / cross 跑 top-1000 / 不归一化 cosine
- Tools: bge-large (bi), bge-reranker-v2-m3 (cross), ColBERTv2

**Problem 2: Reranker Options 决策矩阵**
- Open-source self-host: bge-reranker-v2-m3 (150ms, free, multilingual ⭐) / bge-large (300ms, 单语好) / mxbai-rerank-large-v1 (open Cohere-class)
- API: Cohere rerank-3 ($1/1K, 200ms, top quality) / Voyage rerank-2 ($0.5/1K, 70ms)
- LLM-as-judge: Gemini 3 Pro $0.10-0.30/q, Opus 4.7 $0.30-0.80/q, 3-5s, top-3 final only
- Domain finetune: 1K-10K pairs → +3-8pp NDCG, 1-2 GPU-day $50-100
- Top 3 gotchas: 一个 reranker 通吃 / LLM-judge 全量 (cost 爆) / 不 domain finetune
- Tools: HuggingFace sentence-transformers, Cohere SDK, vLLM serving

**Problem 3: Cascade Optimization**
- 数学: 单 reranker 跑 N candidates O(N) ; cascade 总 cost = c1·N + c2·(N/4) + c3·(N/16), 通常省 50%
- 实战 cascade: bi-encoder top-100 (50ms) → bge-base top-25 (80ms) → bge-large/Cohere top-10 (200ms) → 可选 LLM-judge top-3 (3-5s, high-stake)
- Layer 选择: cost ratio 5-10x 才值得加层, NDCG gain 必须 > 2pp
- Caching: key = hash(query, tuple(c.id for c in candidates)), Redis 1h TTL, FAQ 30-40% hit
- Asymmetric: short query rerank, long query 不 rerank
- Top 3 gotchas: 没 cascade 跑 1000 / cache key 不含 candidate set / 同层模型重复
- Tools: 自实现 cascade, Triton ensemble, Redis

**Problem 4: Latency Engineering**
- GPU 选: A10G 性价比 / A100 极致 / T4 budget; FP16 必开, INT8 TensorRT 编译
- Batch: 32-64, 等 50ms 累积 (micro-batch across queries)
- TensorRT: ONNX export → trtexec FP16/INT8 → 3x speed (1-2pp NDCG 损)
- Distillation: teacher (bge-large) → student (bge-small via TinyBERT-style), 5x speed, 2-3pp 损
- Quant details: INT8 calibrate set 1000 samples; QAT 上限更高
- Latency budget breakdown (e.g., 300ms p99): retrieval 50 + cascade r1 80 + r2 200 + serialize 10
- Top 3 gotchas: CPU forward / batch=1 / 不量化
- Tools: TensorRT, vLLM, Triton, TGI, ONNX Runtime

**Problem 5: Eval + Domain Finetuning + A/B**
- Metrics: NDCG@k (DCG/IDCG, 位置敏感) ⭐ rerank 核心 / MRR (1/rank_first_relevant) / Recall 不变 (rerank 不改 set)
- Slice eval: short query / long / acronym / SKU / multilingual / time-sensitive
- A/B prod: CTR top-3 / top-1, time-to-first-click, thumbs up rate, latency p99, per-variant slice
- Domain finetune workflow: collect (q, click, no-click) → hard-neg mine (top ranked but not clicked) → MSE distill + margin ranking loss → 1-2 GPU-day → +3-8pp NDCG → weekly continual retrain
- Continual learning: 每周 retrain, eval set CI, regression 触发 alert
- Production observability: p99 rerank latency, GPU util, NDCG weekly regression, slice metrics, click position distribution
- Top 3 gotchas: 只看 Recall (rerank 改不了) / 没 slice / 没 A/B 上线
- Tools: BEIR, MTEB, Phoenix, LangSmith, sentence-transformers, HuggingFace Trainer

### 🔥 Production gotchas (top 15)

1. Bi-encoder 用作 rerank (没 cross-attention)
2. 跑 top-1000 cross-encoder → 50s latency 自爆
3. 没 first-stage narrow (bi 召回必须先 top-50)
4. 没 eval set ("feel" 调)
5. LLM-judge 全量 (cost 爆 $5K/day)
6. 没 cascade (单 layer 跑全 100)
7. CPU forward (10x 慢)
8. 不量化 (FP32 浪费一半 GPU)
9. 单 reranker 全 domain (code / legal / medical 各异)
10. 没 cache (q, candidates) → 重复推理
11. 没 NDCG (只看 Recall)
12. 没 slice metrics (acronym/SKU/multilingual)
13. 没 A/B (盲上线)
14. Domain finetune 没 hard-neg mining
15. Continual learning 缺 weekly retrain pipeline

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Cross-encoder rerank | BNPL chatbot | hybrid (no rerank) vs hybrid+bge-reranker, faithfulness +12%, thumbs +15%, +60ms hide in stream |
| Cascade | BNPL prod | bge-base → bge-large cascade, latency p99 230ms, NDCG +14pp |
| Cohere API | Internal Agent Plt | Cohere rerank-3 起步, 后期换 self-host bge-reranker, $/q 降 80% |
| LLM-as-judge | ConvFinQA high-stake | Top-3 final Gemini 3 Pro judge, 关键计算 NDCG +3pp |
| Domain finetune | BNPL refund | 5K click-data + hard-neg mining + margin loss, +6pp domain NDCG |
| GPU latency | BNPL prod | FP16 + batch 32, A10G, p99 180ms |
| TensorRT | TikTok PayLater | INT8 TensorRT 编译, 3x throughput, 1pp NDCG 损 |
| A/B test | BNPL chatbot | A/B 1 周 CTR top-3 +18%, thumbs +15%, 全量上 |

### 🎤 面试现场 quotables (top 8)

> "Bi-encoder for first stage, cross-encoder for rerank — they're different model classes. Don't try to use bi for rerank or cross for retrieval."

> "Reranker only earns its 60-200ms when first-stage recall@50 is already at 92% and precision is the bottleneck."

> "Cascade cheap → expensive saves 50% latency at the same NDCG. We do bge-base 50ms → bge-large 200ms → optional LLM-judge 3-5s for top-3."

> "LLM-judge on top-1000 will cost you $5K/day. Use it only for the final top-3 in high-stakes domains."

> "Domain finetuning with hard-negative mining (top-ranked-but-not-clicked) gets +3-8pp NDCG with 1-2 GPU-days, $50-100."

> "NDCG, not Recall, is the rerank metric. Reranker doesn't change the candidate set; it changes the ordering."

> "On BNPL, A/B'd hybrid vs hybrid+bge-reranker: faithfulness +12%, thumbs +15%, latency +60ms hidden behind LLM first-token stream."

> "TensorRT INT8 quantization + batch 32-64 + FP16 — without these you're paying 3-5x for the same NDCG."

### 🚨 红线 (top 10 anti-patterns)

1. Bi-encoder 用作 reranker
2. Cross-encoder 跑 top-1000
3. No first-stage narrow before rerank
4. No eval set / no NDCG slice
5. LLM-judge mass (cost 自爆)
6. No cascade
7. CPU forward
8. No quantization (FP32 浪费)
9. Single reranker for all domain
10. No A/B test before rollout

### 🛠️ Tool zoo (2026)

| 类别 | Tool | 一句话 |
|---|---|---|
| Reranker models | bge-reranker-v2-m3, bge-reranker-large, mxbai-rerank-large-v1, Cohere rerank-3, Voyage rerank-2, JaColBERT | bge-v2-m3 起步 ⭐ |
| LLM judge | Gemini 3 Pro, Claude Opus 4.7, Sonnet 4.6, Haiku 4.5 | Top-3 high-stake |
| Inference | vLLM, Triton, TGI, TensorRT, ONNX Runtime | vLLM throughput ⭐ |
| Training | sentence-transformers, HuggingFace Trainer | Domain finetune |
| Eval | BEIR, MTEB, Phoenix eval, custom domain | BEIR benchmark |
| Tracing | Phoenix (Arize), LangSmith, Langfuse | Per-layer p99 |
| Cache | Redis, Memcached | (q, candidates) cache 1h |
| GPU | A10G ($/hr good), A100 (极致), T4 (budget) | A10G 性价比 ⭐ |

### 📊 Reranker latency budget (50 doc batch)

```
Model               GPU       Quant   Latency    NDCG lift
bge-reranker-v2-m3  A10G      FP16    80-150ms   +8-10%
bge-reranker-large  A10G      FP16    200-400ms  +10-12%
mxbai-rerank-large  A10G      FP16    250-400ms  +10-13%
Cohere rerank-3     API       n/a     150-250ms  +10-12%
JaColBERT           A10G      FP16    50-100ms   +8-10%
LLM-judge Pro       API       n/a     5-10s      +12-15%
LLM-judge Opus      API       n/a     8-15s      +12-15%
Domain finetune     A10G      FP16    100-300ms  +3-8pp (in-domain)

Optimizations:
  FP32 → FP16:           2x
  FP16 → INT8 TensorRT:  3x (1-2pp 损)
  Batch 1 → 32-64:       3x throughput
  Distill large→small:   5x (2-3pp 损)
  Cache 30-40% hit:      bypass inference
```

### 💻 一段最小 prod-ready cascade

```python
async def rerank_cascade(query, candidates, top=10):
    # Cache check
    key = hash((query, tuple(c.id for c in candidates)))
    if cached := await redis.get(f"rerank:{key}"):
        return cached
    
    # Layer 1: cheap base reranker (top-100 → top-25)
    base_scores = await bge_base.predict(
        [(query, c.text) for c in candidates], batch_size=64
    )
    candidates = top_k(candidates, base_scores, k=25)
    
    # Layer 2: expensive large reranker (top-25 → top-10)
    large_scores = await bge_large.predict(
        [(query, c.text) for c in candidates], batch_size=32
    )
    final = top_k(candidates, large_scores, k=top)
    
    # Layer 3 (optional, high-stake only): LLM judge top-10 → top-3
    if is_high_stake(query):
        final = await llm_judge_top3(query, final[:10])
    
    await redis.setex(f"rerank:{key}", 3600, final)
    return final
```

### 🎬 45-min answer rhythm

```
0-5    Clarify: corpus / QPS / multilingual / domain / latency SLA / budget
5-10   Mental model: bi vs cross 数学, first-stage narrow 必要
10-20  Cross-encoder cascade (bge-base → bge-large → optional LLM judge) + latency math
20-30  Latency engineering (GPU / FP16 / INT8 / batch / distill / cache)
30-37  Domain finetune (hard-neg mining + MSE + margin) + continual learning
37-42  Eval (NDCG + slice + A/B) + production observability
42-45  简历 quote (BNPL hybrid+rerank +12% faithfulness, +15% thumbs)
```

### 🔑 Cascade mnemonic

```
B  Bi-encoder retrieve            (top-100, 50ms)
C  Cheap cross (bge-base)         (top-25, +80ms)
L  Large cross (bge-large/Cohere) (top-10, +200ms)
J  LLM judge (optional, hi-stake) (top-3, +3-5s)
F  FP16 + INT8 + batch + cache    (latency engineering)
```
```
