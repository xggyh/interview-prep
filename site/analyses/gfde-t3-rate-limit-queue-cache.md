## 题目

> "Your LLM service serves customer's chatbot. Underlying LLM API has **rate limit (10K TPM, 100 RPM)** and is **expensive ($5/$25 per 1M, Claude Opus 4.7)**. Customer traffic is bursty (100x peaks). Design the system."

或追问形态:

> "Cost is blowing up — 50% of LLM spend is repeated similar questions. Reduce cost without hurting UX."

**Round**: System Design — Cost / Scale (45 min)

---

## 这道题在考什么

考你**economics + throughput** for LLM workloads:

1. **Cache layers** —— exact + semantic + result + tool
2. **Queue + rate-limit** —— smooth burst, fair share
3. **Cost-aware routing** —— cheap model first
4. **Budget enforcement** —— per-user / per-tenant
5. **Graceful degradation** —— quality vs availability

---

## 必问 clarifying

**1. Latency tolerance**

> "Per query — < 1s real-time, or 10s OK? Affects queue depth."

**2. Cache feasibility**

> "Many similar queries (FAQ) or all unique? Affects cache hit potential."

**3. Tenant tiers**

> "Multi-tenant — gold / silver / bronze? Different QoS?"

**4. Budget model**

> "Per-customer-monthly contract, or pay-as-you-go?"

**5. Quality bar**

> "Acceptable to fallback to smaller model under load?"

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify latency / cache / tenant / budget |
| 5-15 min | 4-layer architecture (cache → queue → rate-limit → route) |
| 15-25 min | Semantic cache deep dive |
| 25-35 min | Cost-aware routing + budget enforcement |
| 35-45 min | Graceful degradation + observability |

---

## 我会这样答（sample）

> "Clarify — *[假设: < 3s latency tolerance, FAQ-heavy (50% similar queries), 3 tenant tiers, monthly contract per tenant, smaller-model fallback acceptable]*.
>
> **4 layers in order**:
>
> **Layer 1: Caching**
>
> Cheapest defense — never call LLM if can avoid.
>
> **Result cache (exact hash)**:
>
> ```python
> def query(user_msg, conv_id):
>     key = sha256(user_msg + conv_id + model_version)
>     cached = await redis.get(key)
>     if cached:
>         return cached  # 100% hit, 0 cost
>     ...
> ```
>
> Hit rate: 10-20% on typical chat workloads (repeat queries).
>
> **Semantic cache (embedding similarity)**:
>
> ```python
> async def semantic_lookup(query):
>     q_emb = await embed(query)
>     hits = await vector_db.search(q_emb, top_k=3)
>     for hit in hits:
>         if hit.score > 0.95:  # threshold tuned per use case
>             # Cache hit — return previous response (verify still applicable)
>             return hit.response, hit.metadata
>     return None
>
> async def query(user_msg):
>     # Try exact cache first (cheap)
>     exact = await redis.get(hash(user_msg))
>     if exact: return exact
>     
>     # Try semantic cache (cheaper than LLM)
>     semantic = await semantic_lookup(user_msg)
>     if semantic: 
>         # Optional: cheap LLM pass to verify/personalize
>         return semantic.response
>     
>     # Cache miss — full LLM
>     response = await llm.generate(...)
>     await store_cache(user_msg, response)
>     return response
> ```
>
> Hit rate: 30-50% on FAQ workloads. **Saves $$$**.
>
> **Threshold tuning** crucial:
> - 0.95+ = high precision, low hit rate
> - 0.90+ = more hits, occasional wrong answer
> - Per-product tuned. Conservative for medical, aggressive for FAQ.
>
> **Tool output cache**:
>
> ```python
> # For idempotent reads (search_inventory, get_user_info)
> cache_key = (tool_name, hash(args))
> ttl_per_tool = 60s to 1h depending on freshness
> ```
>
> **Prefix cache (LLM-server side)**:
>
> When system prompt + context shared across requests, LLM serving (vLLM) caches the KV. Free 2-3x speedup on prefill.
>
> **Layer 2: Queue + concurrency control**
>
> Burst arrives → don't fail, queue:
>
> ```python
> class BackpressureQueue:
>     async def submit(self, request, tier):
>         if queue_depth(tier) >= MAX[tier]:
>             # Queue full — fail fast with retry hint
>             raise QueueFull(retry_after_seconds=...)
>         
>         enqueue(request, priority=tier_priority(tier))
>         return await wait_for_result()
> ```
>
> **Priority queues** by tier:
>
> ```
> Gold tier: priority 1, max queue depth 100, p99 < 2s
> Silver: priority 2, max queue depth 500, p99 < 5s
> Bronze: priority 3, max queue depth 2000, p99 < 30s
> ```
>
> **Per-tenant concurrency limit** (avoid noisy neighbor):
>
> ```python
> tenant_semaphore[tenant_id].acquire(timeout=...)
> ```
>
> **Layer 3: Rate limit (LLM vendor SLA)**
>
> Token bucket against underlying API limit (10K TPM):
>
> ```python
> class TokenBucket:
>     # 10K TPM = 167 tokens/sec capacity
>     # Burst allowance 2K tokens
>     
>     async def acquire(self, estimated_tokens):
>         while not self._can_consume(estimated_tokens):
>             await asyncio.sleep(0.1)
>         self._consume(estimated_tokens)
> ```
>
> Don't blast above API limit → 429 → retry storm.
>
> **Per-tenant rate limit**:
>
> Each tenant has own bucket. Prevents one tenant exhausting underlying quota.
>
> **Layer 4: Cost-aware model routing**
>
> ```python
> async def route_model(query):
>     complexity = complexity_score(query)  # cheap classifier or heuristic
>     
>     if complexity < 0.3:
>         return 'gemini-3-flash'    # $0.50 / $3 per 1M — 90% of traffic
>     elif complexity < 0.7:
>         return 'gemini-3-pro'      # $2 / $12 per 1M — 8% of traffic
>     else:
>         return 'claude-opus-4.7'   # $5 / $25 per 1M — 2% hard cases
> ```
>
> **Classification**:
> - Length + question type + keyword
> - Pre-classifier (small model) for hard cases
> - Per-tenant default model (gold tier gets Gemini 3 Pro / Claude Opus 4.7, bronze gets Gemini 3 Flash / Haiku 4.5)
>
> Saves 30-70% cost with negligible quality loss in benchmark.
>
> **Budget enforcement** (per tenant monthly):
>
> ```python
> async def query(request, tenant):
>     monthly_spend = await db.get_spend(tenant, this_month)
>     if monthly_spend >= tenant.monthly_budget:
>         # Hard stop — return error or degraded mode
>         return graceful_degrade(request)
>     
>     # Track per-call
>     response = await execute(...)
>     await db.add_spend(tenant, response.cost)
>     
>     # Alert at thresholds
>     if monthly_spend > 0.8 * budget:
>         await alert(tenant, 'approaching budget cap')
> ```
>
> **Graceful degradation**:
>
> Under load / over budget:
>
> | Strategy | Trigger | UX impact |
> |---|---|---|
> | Smaller model | Queue depth > 80% | Slightly lower quality |
> | More aggressive cache | Cost trending high | Slightly stale answers |
> | Cached canned response | Severe overload | 'Service busy, try later' |
> | Reduce parallel tool calls | Latency budget exceeded | Slower response |
> | Drop multi-turn context | Context > 30K tokens | Less personalized |
>
> **Observability priorities**:
>
> - Cache hit rate (exact + semantic + result + LLM prefix)
> - Queue depth per tier
> - Cost per tenant (real-time + forecast)
> - Model distribution (% Flash / Pro / Opus)
> - Degradation events
>
> **Putting it together — request lifecycle**:
>
> ```
> Request arrives
>   ↓
> Exact cache → hit? return. 10-20% rate.
>   ↓ miss
> Semantic cache → hit? return. 30-50% rate.
>   ↓ miss
> Per-tenant rate-limit check → exceed? 429.
>   ↓ pass
> Submit to priority queue (by tier)
>   ↓ scheduled
> Concurrency semaphore per tenant
>   ↓ acquired
> Cost-aware model routing
>   ↓
> Token-bucket rate-limit (vs LLM vendor)
>   ↓
> LLM call (with KV prefix cache on server)
>   ↓
> Store in caches (exact + semantic + result)
>   ↓
> Track tenant budget
>   ↓
> Return response
> ```
>
> **What NOT to do**:
> - No cache layer (most expensive)
> - One queue for all tenants (noisy neighbor)
> - Synchronous to LLM API (burst blow)
> - Single model for all queries (cost waste)
> - No budget cap (runaway customer)"

---

## 多场景变体 + 解法

### 变体 1: 新客户 launch 带来突发流量

> "客户 launch 一个产品, 流量从 100 QPS 暴涨到 10K QPS"

**解法**:
- **Pre-launch capacity plan**: 跟客户 sync launch 时间, 提前 pre-warm
- **Burst absorber queue**: 队列容量 = 5 min × peak QPS, 容量内 'normal', 超过 fail fast
- **Tier-based**: launch 客户 gold-tier, 优先, 但仍有 cap
- **Spillover**: 自有 LLM 容量打满 → spillover 到 OpenAI API (贵但能扛)
- **Communicate**: 'high traffic, expected delay 30s' 给用户透明
- **Post-launch**: 24h 后 scale down

### 变体 2: FAQ-heavy workload

> "用户重复问类似 question, 50% query 是 5 个 FAQ 变体"

**解法**:
- **Semantic cache 极度激进**: threshold 0.88 (低), 命中率拉高
- **Cache 'gold list'**: 5 个 FAQ 手动配 canonical answer, 直 serve, 不走 LLM
- **Personalization layer**: cached canonical + per-user param substitute
- **Cache hit telemetry**: monitor 哪 5 个最热, 优化它们答案
- **A/B canned vs LLM**: canned 答案是否真和 LLM 同质 → eval

### 变体 3: Multi-tenant noisy neighbor

> "Tenant A 突发 10x 流量, 把 tenant B (gold) 拖慢"

**解法**:
- **Per-tenant quota**: tenant A 有 quota 上限, 超了被 rate-limit
- **Per-tenant concurrency**: tenant A 最多 100 concurrent, 不抢 GPU
- **Tier priority**: gold tier 永远先 dispatch, bronze 排队
- **Backpressure visible**: tenant A 看到 429, 知道自己被限
- **Isolated pool**: gold tier 独立 replica (不与 bronze 共享)
- **Cost transparency**: tenant A 看自己 cost 涨, 自我约束

### 变体 4: Per-user budget 用完

> "免费用户 $5/month budget, 用完了。Agent 怎么办？"

**解法**:
- **Hard stop at limit**: 不能继续无脑 serve (亏钱)
- **Graceful UX**: 'monthly limit reached, upgrade or wait until next month'
- **Cached only mode**: 限额后, 仅命中 cache 时 serve, 不走 LLM
- **Cheap model fallback**: 限额客户走 Gemini 3 Flash ($0.50/$3 per 1M, ~4x cheaper than Pro)
- **Show usage**: progress bar '4 of 5 USD used'
- **Upsell trigger**: 80% 时推 upgrade

### 变体 5: LLM vendor 突然 cut quota

> "OpenAI 把我们配额从 100K TPM 砍到 50K, 还能扛吗？"

**解法**:
- **多 vendor 早就接上**: Claude + Gemini + Llama 都接, 立即 spillover
- **Aggressive cache**: 临时把 cache threshold 调松到 0.85, 命中翻倍
- **Cheaper model 主力**: Gemini 3 Pro → Gemini 3 Flash 临时降级 (4x 便宜)
- **Queue + delay**: < SLA 影响下推后部分非紧急
- **Notify customer**: SLA breach 风险预警
- **Long-term**: 加 self-host (vLLM 自托管) 减依赖

---

## 简历专属 reframe

| 题 | 你做过 |
|---|---|
| Cache strategy | Voice agent — semantic cache for repeated user phrases |
| Rate limit + queue | TikTok payment — natural at scale |
| Cost routing | BNPL chatbot — small model for routing, big for complex |
| Multi-tenant | Voice agent 7 markets |
| Budget enforcement | TikTok payment — quota / chargeback flow |
| Degradation | Voice agent fallback to text-input under ASR overload |

**Quote**:

> "BNPL chatbot — 50% of incoming queries were variations of 5 FAQs ('how do I reschedule', 'what's my balance', etc.). We added semantic cache with 0.92 threshold + 1h TTL. **Hit rate 38%**, **cost reduction 42%** (caches are free). Queue with 3 priority tiers (gold ahead of bronze by 5x). When peak hit, **cost-routing** automatically pushed non-critical queries to Gemini 3 Flash ($0.50/$3 per 1M, ~10x cheaper than Claude Opus 4.7), no measurable quality drop."

---

## 5 follow-ups

**Q1**: "Semantic cache wrong-hit — returns answer for slightly different question. Mitigate?"
**A**:
- **Threshold tuning** per product (high precision FAQ ok, lower precision risky)
- **Verification pass**: cheap LLM compares cached answer to current query
- **Personalization layer**: cached answer + user context → tailored response
- **Per-domain stricter**: medical / financial — higher bar

**Q2**: "Cache invalidation — when underlying data changes, stale cached answer."
**A**:
- **TTL based**: 1h for general, 5 min for fresh data
- **Event-based**: data update → invalidate cache entries via pub/sub
- **Versioning**: cache key includes data_version, bump on update
- **Best-effort**: 5% stale acceptable for cost savings; alert if more

**Q3**: "Customer says cache makes responses 'feel canned'. Address?"
**A**:
- **Variation layer**: cache + cheap LLM 'rephrase' for variety
- **Lower threshold + personalize**: get semantic hit + run quick personalization pass
- **Smarter granularity**: cache structured answer, LLM formats per user
- **Disable cache for chatty / creative interactions** (only cache transactional)

**Q4**: "Burst 100x — queue fills, users wait long. Better?"
**A**:
- **Reservation system** (gold tier guaranteed slots)
- **Spillover to slower / cheaper model**
- **Async response** (acknowledge + Slack-style 'still working')
- **Pre-scale** based on burst prediction
- **Communicate**: 'high traffic, your request is #423 in queue'

**Q5**: "Cost grew 3x in 1 week — root cause?"
**A**: Common causes:
- New customer with high traffic (check tenant spend)
- Prompt template change increased token count
- Cache hit rate dropped (look at why — new queries pattern?)
- Model switch (auto-routed expensive more?)
- Loop bug (agent re-calling LLM unnecessarily)
- Hostile use (jailbreak attempts inflate)

Observability must catch each.

---

## ❌ 易错点

1. **No cache layer** — 50% wasted cost
2. **One queue for all tenants** — noisy neighbor
3. **Sync to LLM API** — burst blow
4. **Single model** — cost waste
5. **No budget cap** — runaway customer
6. **Cache threshold too loose** — wrong-hits
7. **No graceful degradation** — peak = total fail

---

## ✅ 加分项

1. **4-layer cache** (exact / semantic / result / LLM prefix)
2. **Per-tenant priority queues**
3. **Per-tenant rate limit + concurrency**
4. **Cost-aware routing**
5. **Budget enforcement** with alerts
6. **Graceful degradation** ladder
7. **Cache invalidation** strategy
8. **Quote BNPL 38% hit / 42% cost reduction**

---

## Cheat Sheet

```
4 layers in order:
  L1 Cache (exact + semantic + tool + prefix)
  L2 Queue (per-tier priority + concurrency)
  L3 Rate limit (token bucket per tenant + vendor)
  L4 Cost-aware model routing

Cache types:
  Exact (hash): 10-20% hit
  Semantic (embedding): 30-50% on FAQ
  Tool output: per-tool TTL
  LLM prefix: server-side KV cache

Semantic cache:
  Embed query
  Vector DB search top-3
  Threshold 0.95 (tune per use case)
  Verify with cheap LLM optional

Queue priority:
  Gold: depth 100, p99 < 2s
  Silver: depth 500, p99 < 5s
  Bronze: depth 2000, p99 < 30s
  Per-tenant semaphore (noisy neighbor)

Rate limit:
  Token bucket (vs vendor API)
  Per-tenant bucket (fair share)
  429 with Retry-After

Cost-aware routing:
  Complexity classifier
  < 0.3: cheap (mini)
  < 0.7: mid (4o)
  >= 0.7: expensive (4-turbo)
  Saves 30-70% cost

Budget enforcement:
  Per-tenant monthly cap
  Alert at 80%
  Hard stop or degrade at 100%

Graceful degradation ladder:
  Smaller model (queue 80%)
  Aggressive cache (cost trend)
  Canned response (overload)
  Drop parallel calls (latency)
  Drop multi-turn (context blow)

Cache invalidation:
  TTL (1h general, 5min fresh)
  Event-based (data update → invalidate)
  Versioning (key includes data_version)

Observability:
  Cache hit rate per layer
  Queue depth per tier
  Cost per tenant (real-time)
  Model distribution
  Degradation events

红线:
  - No cache
  - One queue for all
  - Sync to LLM
  - Single model
  - No budget cap
  - Cache threshold loose
  - No degradation
```
