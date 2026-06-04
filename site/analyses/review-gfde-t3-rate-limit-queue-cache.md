## T3.5 · rate limit / queue / cache — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](gfde-t3-rate-limit-queue-cache.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t3-rate-limit-queue-cache.html`](gfde-t3-rate-limit-queue-cache.html)

---
## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"LLM service serves customer chatbot. Provider has 10K TPM, 100 RPM, $5/$25 (Opus). Customer traffic bursty (100x peaks). Design the system"**, 我按这 9 层回答, 不跳序.

### 📐 Cost Defense + Burst Protection — 9 层结构

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 |
|---|---|---|---|---|
| 1 | Burst 数学锚点 | 1 min | Sustained 100 QPS → spike 10K QPS (100x). Provider 100 RPM → 100/60 = 1.67 RPS = **1/600 of peak**. Naive 直打 = 99.83% 429. 这是 burst 的真实 economic | "Let me anchor the burst math — 100 RPM provider vs 10K QPS spike = 1/600 throughput. 99.83% 429 if naive..." |
| 2 | Clarify 5 问 | 90s | Multi-tenant? Tier (gold/silver/bronze)? p99 vs p50 SLA? Cost budget $/month? Quality regression tolerance? PII/compliance? | "5 clarify — tier model, SLA, budget, quality tolerance, compliance" |
| 3 | 4-layer cost defense 概览 | 1 min | L1 cache (40% reduction) / L2 priority queue (SLA 保护) / L3 rate limit (defense) / L4 cost-aware routing (5-6x). Combined **8-12x blended cost ↓** | "4 layers stacked — cache, queue, rate, routing. Combined 8-12x blended cost reduction..." |
| 4 | L1 多 cache 设计 | 4 min | (a) **Exact** hash(model+prompt+temp+seed), 10-20% hit; (b) **Semantic** Vertex AI Vector Search, threshold **0.97 safety / 0.95 normal**, 30-50% FAQ hit; (c) **Tool output** cache for idempotent tool; (d) **vLLM prefix** 自动 share KV. **Per-tenant namespace 防 cross-tenant leak** | "Cache 4 sub-layers — exact, semantic (threshold 0.97), tool output, vLLM prefix. Per-tenant namespace 是红线..." |
| 5 | L2 priority queue | 2 min | Per-tenant Redis sorted set, score = `tier_priority × 1e10 + timestamp`. Gold tier 5% traffic 优先, Silver 25%, Bronze 70%. Per-tier max concurrency, noisy neighbor 隔离 | "L2 — Redis sorted set per tenant, score = priority×1e10 + ts. Gold 5%, Silver 25%, Bronze 70% concurrency budget..." |
| 6 | L3 token bucket 多维 | 2 min | 5 dimension: user / tenant / API key / model / global. Redis Lua atomic, < 1ms. **Token-based 不是 request-based** (LLM 1 req 可以 50K token). 429 retry-after header propagate | "L3 token bucket 5-dim — user, tenant, API key, model, global. Critical: token-based not request-based..." |
| 7 | L4 cost-aware routing | 3 min | 70% Flash ($0.50/$3) + 25% Pro ($2/$12) + 5% Opus ($5/$25). Complexity classify (heuristic + small LLM). Tier override: gold + complex → Opus. Budget exhausted → cheap-only or fallback canned | "L4 routing — 70/25/5 baseline. Complexity classifier (small LLM judge). Budget exhausted → graceful degrade..." |
| 8 | Graceful degradation ladder | 2 min | 5 step: priority queue → smaller model → aggressive cache → canned response → "服务忙稍后". 每步 cost ↓ quality ↓, 但永远不挂 | "Graceful ladder 5 steps — queue → smaller → cache → canned → busy. 永远不返回 5xx..." |
| 9 | 简历 resume hook | 90s | "TikTok PayLater chatbot peak 5K QPS. 4-layer: semantic 35% hit (Vertex AI Vector Search 0.97), priority queue gold 5%, token bucket per user/tenant, 70/25/5 routing. Blended $0.85/1M vs $5/1M = **6x savings**, faithfulness ≥ 0.85 unchanged. Eval harness 证明 no quality regression" | "On TikTok PayLater 5K QPS, blended cost $0.85/1M vs $5/1M = 6x, eval harness 证明 no regression..." |

### 🎯 为啥按这个序

Burst 数学锚点 (1/600) 让面试官知道 "naive 直打"为什么必死. Clarify 5 问 是 senior 标记. 4 层 framework 是骨架 — 必须先讲完整再深入. L1 cache 是 cost-saving 最大头, 4 sub-layer (exact / semantic / tool / prefix) 要分清, 多数候选人只想到 exact. **Semantic threshold 0.97 safety / 0.95 normal** 是踩过坑才知道的数字. L2 queue 是 SLA 保护 (不省钱但保 gold). L3 rate limit "token-based 不是 request-based" 是 LLM-specific 细节. L4 routing 数学 (70/25/5) + tier override 显示完整 product thinking. Graceful degradation ladder 是 "永远不挂" 的 mindset. 简历 hook 用 TikTok PayLater 5K QPS 是 concrete win.

### 🔥 哪一层最容易被追问 deeper

**Layer 4 (semantic cache)** — 追问 "0.97 vs 0.95 threshold 怎么定?". 回答: per-feature calibrate — 在 1000 历史 query pair 上跑, 找 false-positive rate < 1% 的 threshold. Safety-critical (medical/legal/financial) 0.97+, FAQ 0.93-0.95. Cache poisoning 是 silent kill, 必须 **eval-gated cache write** (写之前先 eval, pass 才写). **Layer 7 (cost-aware routing)** 追问 "complexity classifier 怎么训". 回答: 起步 heuristic (query 长度 / 关键词), 累积 10K labeled sample 后用 small LLM (Haiku) 做 classifier, accuracy 88-92%. 错路到 cheap model 的影响要在 eval harness 监控.

### ⏱ 时间压缩版 (30 min round)

1. Burst 数学 (1 min) + 4 layer framework (1 min)
2. L1 cache 4 sub-layer (3 min)
3. L2 queue + L3 rate limit (3 min)
4. L4 routing 70/25/5 + 数学 (3 min)
5. Graceful ladder + 简历 TikTok PayLater (3 min)

### 🆘 卡壳兜底 (针对这题)

1. **被问 "semantic cache 答错了怎么办"**: 这是 cache poisoning silent kill. 防御: (a) eval-gated cache write, (b) per-tenant namespace, (c) per-user thumbs-down 直接 invalidate, (d) periodic re-eval on cached entries
2. **被问 "queue 排太久 user 流失"**: 设 max wait time (e.g., gold 500ms / silver 3s / bronze 10s), 超时 fallback canned / smaller model. Never block forever
3. **被问 "complexity classifier 跑错 cheap model 用户感受差"**: A/B test — 1% traffic 强制 Opus 做 ground truth, 对比 cheap model 答案 thumbs-up rate, drift > 5% 时 retrain classifier
4. **被问 "multi-vendor failover 怎么做"**: LiteLLM router. OpenAI 429 → Anthropic → Google → self-host vLLM. 关键: 路由前 normalize schema (function calling / tool / prompt format)

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖 5 layer / 4-tier cache / priority queue / cost routing / budget / degradation 全量.

### 🧠 核心心智模型 (1 sentence)

LLM API 慢 + 贵 + rate-limited, 防御靠 **5 layer 叠加** (cache → queue → rate → routing → budget) 实现 **8-12x blended cost ↓**, 单 layer 都不够; 加 **7-step graceful degradation** 保 peak SLA.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Exact cache | hash(model + prompt + temp + seed), 10-20% hit | 重复 query |
| Semantic cache | embedding similarity > threshold 命中 | FAQ-style 30-50% hit |
| Tool output cache | per-tool TTL (get_balance 5s, static 24h) | idempotent reads |
| LLM prefix cache | vLLM 内 KV block share | self-host serving |
| Priority queue | per-tier (gold/silver/bronze/free) sorted | 多租户 SLA |
| Concurrency semaphore | per-tenant in-flight cap (Redis SETNX) | 防 noisy neighbor |
| Token bucket | rate limit with burst tolerance | per-(user,tenant,model) |
| Cost-aware routing | complexity → Flash/Pro/Opus | 5-10x cost ↓ |
| Budget cap | per-tenant monthly USD cap | 防 runaway |
| Atomic Redis Lua | race-free check-and-decrement | budget enforcement |
| Graceful degradation | 多 tier 降级 (model / cache / canned) | peak / vendor down |
| Spillover | vendor 429 → 备用 vendor | multi-vendor router |
| Pre-flight cost estimate | call 前估 cost, 拒超 budget | budget enforcement |
| Cost spike detector | 5x hourly baseline → alert | catch bad prompt |
| Wrong-hit | semantic cache 误命中 (similar query 不同 answer) | 必须 eval gate |

### 🎯 5 个 Layer Framework

**Layer 1: Cache (4 tier)**
- When: 50% 流量是 cache-able (FAQ-heavy)
- Algorithm: exact (hash) → semantic (embedding 0.95) → tool output (per-TTL) → LLM prefix (vLLM)
- Trade-off: stale data vs cost; wrong-hit on semantic
- Tools: Redis (exact + tool), Vertex AI Vector Search / Vertex AI Vector Search (semantic, threshold 0.95-0.97), vLLM (prefix), per-tool config

**Layer 2: Priority Queue + Concurrency**
- When: multi-tenant, SLA differential
- Algorithm: Redis sorted set, score = priority×1e10 + ts; per-tenant Redis SETNX concurrency
- Trade-off: queue depth vs starvation low-tier
- Tools: Redis sorted set, Redis Lua atomic, Envoy filters

**Layer 3: Rate Limit (Token Bucket Multi-dim)**
- When: 防滥用 + per-tenant fair
- Algorithm: token bucket per (user, tenant, tool, model); 429 with Retry-After
- Trade-off: dim 越多越精细, 也越复杂
- Tools: Envoy rate limit filter, Redis Lua INCRBY, LiteLLM router

**Layer 4: Cost-Aware Model Routing**
- When: cost-driven
- Algorithm: complexity classifier (small LM or rules) → 90% Flash / 9% Pro / 1% Opus
- Trade-off: routing complexity vs quality A/B
- Tools: small LM classifier (Haiku $1/$5), LiteLLM router, per-tenant default

**Layer 5: Budget Enforcement (Per-Tenant Monthly Cap)**
- When: enterprise multi-tenant
- Algorithm: Postgres atomic counter + Redis Lua check, alert 80%/95%/100% hard stop
- Trade-off: pre-flight estimate accuracy vs over-spend
- Tools: Postgres + Redis Lua + alert (Slack / PagerDuty)

### 🌳 关键决策树 (ASCII)

```
Cache strategy?
  ├─ Exact only ── 10-20% hit, 不够
  ├─ + Semantic 0.95 ── 30-50% hit (FAQ), wrong-hit risk
  ├─ + Tool output cache (read-only) ── per-tool TTL
  └─ + LLM prefix (vLLM server) ── 60-90% shared prefix ⭐ (combined)

Routing strategy?
  ├─ Complexity < 0.3 ── Self-host 70B OR Gemini Flash ($0.50/$3)
  ├─ Complexity < 0.7 ── Gemini Pro ($2/$12)
  └─ Complexity ≥ 0.7 ── Opus 4.7 ($5/$25)
  → 90/9/1 mix → blended $0.85/1M (vs $5 all-Opus = 6x ↓)

Degradation tier?
  L1 Queue 80% ── smaller model
  L2 Cost trend ── aggressive cache 0.90 threshold
  L3 Vendor 429 ── spillover alt vendor
  L4 Latency >3s ── drop parallel tool
  L5 Ctx >30K ── drop multi-turn history
  L6 Severe ── canned response from cache
  L7 Total ── "try later" static
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: 4-Layer Cache — Exact, Semantic, Tool Output, LLM Prefix**

```python
async def cached_llm_call(req):
    # L1 Exact
    exact_key = sha256(f"{req.model}|{req.prompt}|{req.temp}|{req.seed}")[:16]
    if cached := await redis.get(f"exact:{exact_key}"):
        return cached
    # L2 Semantic
    emb = await embed(req.prompt)
    matches = await pinecone.query(emb, top_k=1, namespace=req.tenant_id)
    if matches and matches[0].score >= 0.95:
        return matches[0].metadata.cached_response
    # L3 Tool output (skip for non-tool)
    # L4 LLM prefix via vLLM extra_body conv_id
    resp = await vllm.complete(req.prompt, extra_body={"conversation_id": req.conv_id})
    # Write back (eval-gated for semantic)
    await redis.setex(f"exact:{exact_key}", 3600, resp)
    if random.random() < 0.05:  # 5% eval gate before semantic cache
        if eval_pass(req.prompt, resp):
            await pinecone.upsert(emb, {"cached_response": resp}, namespace=req.tenant_id)
    return resp
```
- Top 3 gotchas: (1) semantic threshold 0.90 wrong-hit silent (用 0.95+) (2) cache 不 per-tenant → cross-tenant leak (3) write 不 eval-gated → poisoning
- Tools: Redis (exact), Vertex AI Vector Search (semantic, threshold 0.95), vLLM prefix cache (auto)

**Problem 2: Priority Queue + Per-Tenant Concurrency**

```lua
-- Redis Lua atomic priority enqueue + concurrency check
local tenant_id = KEYS[1]
local priority = tonumber(ARGV[1])  -- 1=gold, 2=silver, 3=bronze
local req_id = ARGV[2]
local max_concurrent = tonumber(ARGV[3])

local in_flight = tonumber(redis.call('GET', 'inflight:'..tenant_id) or 0)
if in_flight >= max_concurrent then
    -- Queue with score (priority×1e10 + timestamp)
    local score = priority * 1e10 + tonumber(ARGV[4])
    redis.call('ZADD', 'wait:'..tenant_id, score, req_id)
    return {-1, 'queued'}
end

redis.call('INCR', 'inflight:'..tenant_id)
return {1, 'dispatch'}
```

| Tier | Queue depth | p99 SLA | Concurrency | Model |
|---|---|---|---|---|
| Gold | 100 | < 2s | 50 | Sonnet / Pro |
| Silver | 500 | < 5s | 20 | Haiku / Flash |
| Bronze | 2000 | < 30s | 5 | Flash |
| Free | 10K | best effort | 1 | Flash + canned |

- Top 3 gotchas: (1) concurrency check 不 atomic → race over-dispatch (2) starvation low-tier (Bronze 永远 wait) → 加 max-wait fairness (3) queue depth 没 metric → silent overflow
- Tools: Redis Lua, Envoy filter, custom dispatcher

**Problem 3: Cost-Aware Model Routing — Gemini Flash 90% / Pro 9% / Opus 1%**

```python
async def route(query, history, user_tier, budget_remaining):
    # Complexity classifier (cheap LM or rules)
    complexity = await classify(query, history)  # Haiku $1/$5 or rules
    
    if budget_remaining < 0.01:
        if user_tier == "gold":
            return "gemini-3-flash"  # degraded but cheap
        raise BudgetExhausted
    
    if complexity < 0.3:
        return "self-host-llama70b"  # $0.30/1M
    elif complexity < 0.7:
        return "gemini-3-pro"        # $2/$12
    else:
        return "claude-opus-4.7"     # $5/$25

# Quality A/B per route
# 5% sample → Sonnet judge → log eval score by route
# Alert if any route quality < baseline 5pp
```
- Top 3 gotchas: (1) complexity classifier 不 calibrate (2) routing 没 A/B test 比 single model (3) Opus route 占比 > 5% 时 cost / 6 lost
- Tools: LiteLLM router, Haiku classifier, Braintrust A/B

**Problem 4: Budget Enforcement — Per-Tenant Monthly Cap**

```lua
-- Redis Lua atomic budget check & decrement (race-free)
local tenant_id = KEYS[1]
local month = KEYS[2]
local estimated_cost = tonumber(ARGV[1])  -- in micro-USD
local hard_cap = tonumber(ARGV[2])

local current = tonumber(redis.call('GET', 'budget:'..tenant_id..':'..month) or 0)
if current + estimated_cost > hard_cap then
    return {-1, 'budget_exhausted', current, hard_cap}
end
redis.call('INCRBY', 'budget:'..tenant_id..':'..month, estimated_cost)

-- Alert thresholds
if current >= hard_cap * 0.95 then
    redis.call('PUBLISH', 'budget_alert', 'urgent:'..tenant_id)
elseif current >= hard_cap * 0.8 then
    redis.call('PUBLISH', 'budget_alert', 'warn:'..tenant_id)
end
return {1, 'ok', current + estimated_cost}
```
- Top 3 gotchas: (1) pre-flight estimate too low → overshoot (2) Redis 单 source, no Postgres backup → 数据丢 (3) cost spike detector 没 → 1 bad prompt 整月用完
- Tools: Redis Lua (fast), Postgres (durable), Slack alert, custom Grafana dashboard

**Problem 5: Graceful Degradation Ladder — 7 step**

```python
class DegradationController:
    def __init__(self):
        self.queue_pressure = 0.0  # 0-1
        self.cost_trend = 0.0
        self.vendor_429_rate = 0.0
        self.latency_p99 = 0.0
    
    async def check_and_apply(self, req):
        # L1 Queue 80% full
        if self.queue_pressure > 0.8:
            req.model = downgrade_model(req.model)
        # L2 Cost trend up
        if self.cost_trend > 1.5:
            req.cache_threshold = 0.90  # aggressive
        # L3 Vendor 429 rate up
        if self.vendor_429_rate > 0.1:
            req.vendor = alt_vendor(req.vendor)
        # L4 Latency >3s
        if self.latency_p99 > 3.0:
            req.parallel_tools = False
        # L5 Ctx >30K
        if req.context_size > 30000:
            req.history = req.history[-5:]  # only last 5
        # L6 Severe: serve canned
        if self.severity > 0.9:
            return await canned_response(req.intent)
        # L7 Total: static
        if self.total_fail:
            return "Service temporarily unavailable. Try again later."
```
- Top 3 gotchas: (1) degradation 没 user comm (突然变笨用户骂) (2) recovery 没 hysteresis (反复抖动) (3) canned response 不 per-intent (单 "try later" 体验糟)
- Tools: custom Grafana threshold dashboard, Slack ops, canned response cache

### 🔥 Production gotchas (top 15)

1. **No cache (50% waste)**: 重复 query 全走 LLM
2. **One queue for all tenants**: noisy neighbor 拖死全局
3. **Sync to LLM (no queue)**: burst 时全 fail
4. **Single model only**: cost 5-10x vs routing
5. **No budget cap**: 1 bad prompt 月费爆
6. **Cache threshold 0.85**: wrong-hit silent kill
7. **No degradation plan**: peak time 全挂
8. **Single vendor**: 该 vendor down = down
9. **No pre-flight cost estimate**: 才 call 才知 overshoot
10. **Eval gate 缺**: cache poisoning 服万人
11. **Per-tenant 不 isolate**: tenant A 用完 tenant B 同 quota 也死
12. **No cost spike detector**: 1 prompt 100x token 不知
13. **Atomic check 不 Lua**: race 时 over-dispatch
14. **Recovery 不 hysteresis**: 反复 degrade-recover 抖动
15. **Canned response 1 句通用**: 没 per-intent 体验差

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Semantic cache | BNPL chatbot | "Vertex AI Vector Search 0.95 threshold, FAQ 38% hit, cost ↓ 42%" |
| Priority queue | Voice agent 7 markets | "Gold 50 concurrent, Silver 20, Bronze 5, Free 1; SLA differential" |
| Cost-aware routing | TikTok PayLater 5k QPS | "70/25/5 Flash/Pro/Opus, blended $0.85/1M (vs $5)" |
| Budget cap | Voice agent | "Per-tenant monthly $5K cap, Redis Lua atomic, 80/95/100 alert" |
| Self-host fallback | BNPL Llama 70B | "Self-host 90% traffic $0.30/1M, vendor 10% spillover" |
| Atomic Redis Lua | TikTok payment | "< 1ms atomic check, 0 race condition over 6M txn" |
| Graceful degrade | TikTok peak | "7-step ladder, peak hour faithfulness 95%→89% acceptable" |
| Cost spike detect | BNPL incident | "5x hourly baseline alert caught 1 bad prompt 100x token spike in 15min" |

### 🎤 面试现场 quotables (top 8)

1. "Cost defense 5 layer 叠 8-12x blended; 单 layer 都打不到目标"
2. "Semantic cache 0.95 threshold + eval-gated write; 0.90 太激进, wrong-hit silent kill"
3. "Priority queue per-tier; Gold concurrency 50 vs Free 1 — SLA differential"
4. "Routing 90/9/1 Flash/Pro/Opus → blended $0.85/1M, 6x cheaper than all-Opus"
5. "Budget cap atomic Redis Lua; pre-flight estimate + 80/95/100 alert tiered"
6. "Self-host Llama 70B $0.30/1M, 16-80x cheaper than hosted Opus at scale"
7. "Graceful degradation 7-step ladder, peak hour 95% → 89% faithfulness acceptable"
8. "Cost spike detector 5x baseline catches bad prompt within 15min"

### 🚨 红线 (top 10 anti-patterns)

1. No cache (50% waste)
2. One queue all tenants (noisy neighbor)
3. Sync to LLM no queue (burst kill)
4. Single model (cost 5-10x)
5. No budget cap (runaway)
6. Cache threshold loose (wrong-hits)
7. No degradation plan (peak fail)
8. Single vendor (down = down)
9. No pre-flight cost estimate
10. No eval gate on cache write (poisoning)

### 📊 2026 pricing + 数学全表

| Model | Input $/1M | Output $/1M | Cache In $/1M | When |
|---|---|---|---|---|
| Self-host Llama 70B FP8 (vLLM TP=8) | ~0.30 | ~0.30 | n/a | 90% complexity < 0.3 |
| Gemini 3 Flash | 0.50 | 3 | 0.10 | 70% complexity < 0.5 |
| Gemini 3 Pro | 2 | 12 | 0.40 | 9% complexity 0.5-0.7 |
| Claude Haiku 4.5 | 1 | 5 | 0.10 | classifier / cheap A/B |
| Claude Sonnet 4.6 | 3 | 15 | 0.30 | mid-end |
| Claude Opus 4.7 | 5 | 25 | 0.50 | 1% complexity > 0.7 |
| GPT-5.5 | 5 | 30 | 1 | alt high-end |

**Cost math (100K QPS LLM workload)**:
- All Opus baseline: $73M/day
- 90/9/1 routing only: $12M/day (84% ↓)
- + 38% semantic cache: $7.4M/day (90% ↓)
- + Anthropic prefix cache 90% off: $5M/day (93% ↓)
- → blended $0.50-0.85/1M, 10x ↓

### 🧰 2026 工具栈 quick lookup

| 类别 | 默认 | Alt | 你用过 |
|---|---|---|---|
| Cache (exact + tool) | Redis Cluster | DragonFly, KeyDB | Redis ✅ |
| Vector cache (semantic) | Vertex AI Vector Search | Vertex AI Vector Search, Milvus, Weaviate | Vertex AI Vector Search ✅ |
| LLM prefix cache | vLLM auto | SGLang RadixAttn | vLLM ✅ |
| Atomic check | Redis Lua | Postgres advisory lock | Redis Lua ✅ |
| Priority queue | Redis sorted set | Kafka tiered topic | Redis |
| Concurrency sema | Redis SETNX | semaphore service | Redis Lua |
| Router | LiteLLM | OpenRouter, Portkey | LiteLLM |
| Rate limit | Envoy filter | Kong, NGINX | Envoy |
| Budget tracker | Postgres + Redis | Firestore / Bigtable atomic | Postgres + Redis |
| Alert | PagerDuty + Slack | Opsgenie | PagerDuty |
| Self-host | vLLM TP=8 H100 | TensorRT-LLM | vLLM ✅ |

### 🎬 45-min 节奏 (T3.5 专属)

```
0-5    Clarify    "QPS? Multi-tenant tier? Cost budget? Vendor? FAQ-heavy?"
5-10   Mental     "5 layer cost defense + 7 degrade"; 画 ASCII
10-25  Cache+Queue 4-tier cache + priority queue + concurrency
25-35  Routing+Budget complexity classifier + 90/9/1 + atomic Redis Lua
35-42  Degrade    7-step ladder + canned response per-intent
42-45  Resume     "BNPL 38% cache hit; PayLater 5k QPS cost ↓ 84%"
```

### 🔢 关键 production 数字

- BNPL semantic cache: Vertex AI Vector Search 0.95, 38% hit, cost ↓ 42%
- TikTok PayLater: 5k QPS peak, 70/25/5 routing, blended $0.85/1M
- Voice agent 7 markets: per-tenant $5K monthly cap, 80/95/100 alert
- Self-host Llama 70B: $0.30/1M output (vLLM TP=8 H100)
- Atomic Redis Lua: < 1ms p99 check, 0 race in 6M transactions
- Cache hit rate target: exact 10-20% + semantic 30-50% + prefix 60-90%
- Combined cost reduction (all 5 layer): 8-12x
- Cost spike detector: 5x hourly baseline → alert in 15 min
- Graceful degradation peak hour: faithfulness 95% → 89% acceptable
