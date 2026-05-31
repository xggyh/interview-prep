# 💰 T3.5 · Rate Limit / Queue / Cache Layer 设计 — 冲刺版

> 完整版: [gfde-t3-rate-limit-queue-cache.html](gfde-t3-rate-limit-queue-cache.html). 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: customer chatbot 100K QPS bursty (100x peak), Claude Opus 4.7 vendor 10K TPM / 100 RPM rate limit, $5/$25 per 1M token, 3 tier tenant (gold/silver/bronze), monthly contract per tenant, multi-vendor + self-host vLLM available."

**核心 framing**: LLM API 慢+贵+rate-limited. **5-layer defense** 累积 8-12x cost reduction without quality loss. 不做 cost defense, blended cost 高 5-10x.

### Layer 1: Cache (try first, cheapest, no LLM call)

```
A. Exact-match (hash)       SHA256(model+prompt+temp+seed), TTL 1h, 10-20% hit
B. Semantic (embedding)     cosine >0.95, 30-50% hit FAQ workload
C. Tool output              per-tool TTL (get_balance 5s, static 24h), 60-90% hit
D. LLM prefix (vLLM/Anthropic) server-side, 60-90% shared prefix, 90% off cached input
Combined: ~60% of queries avoid full LLM call
```

### Layer 2: Priority Queue + per-tenant concurrency

```
Gold   queue depth 100   p99 <2s   concurrency 50  Sonnet 4.6 / Gemini Pro
Silver queue depth 500   p99 <5s   concurrency 20  Haiku / Flash
Bronze queue depth 2000  p99 <30s  concurrency 5   Flash
Free   queue depth 10K   best-eff  concurrency 1   Flash + canned
```

Per-tenant Redis Lua semaphore (atomic, <1ms). 防 noisy neighbor: tenant A spike 不能拖 tenant B (gold).

### Layer 3: Vendor rate limit (token bucket per vendor)

```python
def check_vendor_limit(req):
    # 每 vendor 独立 bucket
    if not vendor_bucket[req.vendor].try_acquire(req.tokens):
        # 429 → spillover to alt vendor
        return spillover(req)
    # 多维 token bucket
    rate_limit(f"user:{req.user_id}", limit=100, window=60)
    rate_limit(f"tenant:{req.tenant_id}", limit=10000, window=60)
```

429 → Retry-After 尊重. Spillover chain: Self-host → Gemini Flash → Claude.

### Layer 4: Cost-aware model routing (黄金 90/9/1)

```python
def route(query, history, user_tier, budget_remaining):
    complexity = classify_complexity(query, history)  # cheap LLM Haiku or heuristic
    
    if budget_remaining < 0.01:
        return "gemini-3-flash" if user_tier == "gold" else raise BudgetExhausted
    
    if complexity < 0.3:    return "gemini-3-flash"   # 90% $0.50/$3
    elif complexity < 0.7:  return "gemini-3-pro"     # 9% $2/$12
    else:                   return "claude-opus-4.7"  # 1% $5/$25
```

Blended cost: $0.0011 × 90% + $0.0044 × 9% + $0.0085 × 1% = **$0.0014 / call**. vs all-Opus $0.0085 → **84% reduction**, eval drop <1%.

### Layer 5: Budget enforcement (per-tenant monthly cap)

```python
# Atomic Redis Lua + Postgres durable
if redis.eval(LUA_INCR_IF_BELOW, key, increment, limit):
    proceed
else:
    if 80% used:   alert email
    if 95% used:   urgent + in-app banner
    if 100% used:  hard stop "monthly limit reached, upgrade"
```

Per-tenant atomic check (Redis Lua) + Postgres durable record. Cost spike detector (5x hourly vs 7d baseline) → proactive alert.

### Edge cases

- **EC1 Burst 100x (10K QPS spike)**: pre-launch capacity plan (2h warm 10x replica) + tenant temp 升级 Gold + aggressive cache 预热 (lower threshold 0.95 → 0.90) + spillover to alt vendor. Communicate "request #423 in queue, est 30s" instead of silent fail.
- **EC2 Semantic cache wrong-hit**: threshold per product (medical 0.97, FAQ 0.88, general 0.95). Verification pass: cheap LLM Haiku ($1/$5) compares cached question to current, 10ms latency. Personalization layer fills template (don't return verbatim).
- **EC3 Cache invalidation stale**: TTL based (1h general / 5min fresh data like balance) + event-based (data update → Pub/Sub → invalidate matching) + versioning (cache key includes data_version, bump on update).
- **EC4 Single-tenant noisy neighbor**: token bucket per tenant + concurrency semaphore + tier-based dispatch + isolated replica pool for gold + backpressure visible to client (429 with Retry-After + queue depth in headers).
- **EC5 Free user 用完 budget**: 提前 alert 80% / 90% → at limit ($5) → graceful response (不 silent fail) → cached-only mode (familiar queries 还能 work) → cheap model fallback (Flash 4x cheaper extends budget 4x).

### Production hardening

**Graceful degradation 7-step ladder**:
```
L1 queue >80%     → smaller model (Pro → Flash)
L2 cost trend up  → aggressive cache (0.95 → 0.90)
L3 vendor 429     → spillover to alt vendor
L4 latency >3s    → drop parallel tool calls
L5 context >30K   → drop multi-turn (single-shot)
L6 severe         → canned response from cache
L7 total fail     → static "service busy, try later"
```

### 🪝 Resume hook

"On BNPL chatbot at TikTok PayLater - 50% incoming queries were 5 FAQ variations ('how reschedule', 'balance', 'when due', 'cancel payment', 'change card'). Added semantic cache 0.92 threshold + 1h TTL on Qdrant + text-embedding-3-large. Hit rate 38%, **cost reduction 42%**. 3 priority tiers (gold ahead of bronze 5x). When peak hit, cost-routing pushed non-critical to Gemini 3 Flash ($0.50/$3, ~10x cheaper than Opus), no eval drop. **Budget**: per-tenant atomic Redis Lua check + Postgres durable. One Indonesia customer's bug ran 10K loop in 1 day — budget cap saved us from $50K hit, hard stop at $1K monthly limit."

---

## 🔥 5 Follow-ups

**Q1: Semantic cache wrong-hit (返回相似但不同 query 的答案), 怎么 mitigate?**
**Threshold tuning per domain**: medical 0.97 / FAQ 0.88 / general 0.95. **Verification pass**: cheap Haiku ($1/$5) compare cached question to current, 10ms latency. **Personalization layer**: cached answer + user context → tailored (不 return verbatim). **Per-domain stricter**: 金融/医疗高 threshold. **A/B canned vs LLM**: measure thumbs ratio, canned 匹配 LLM → safe.

**Q2: Cache invalidation - 数据变 stale answer?**
**TTL based**: 1h general / 5min fresh (real-time balance). **Event-based**: data update → Pub/Sub → invalidate matching pattern. **Versioning**: cache key includes data_version, bump on update → naturally bypass old. **Best-effort 5% stale acceptable** for cost saving; alert if more. **Per-tool config**: get_balance 5s, get_static_doc 24h.

**Q3: Customer 说 cache 让 response 'feel canned'. Address?**
**Variation layer**: cache + cheap LLM 'rephrase' for variety. **Lower threshold + personalize**: get semantic hit + quick personalization pass. **Smarter granularity**: cache structured answer, LLM formats per user. **Disable cache for chatty / creative** (only cache transactional). **Personalization slots**: cached "Your balance is {AMOUNT}, due {DATE}" — fill from DB.

**Q4: Burst 100x - queue fills, users wait long. Better?**
**Reservation system**: gold tier guaranteed slots, never wait. **Spillover to cheaper model**: never reject, downgrade. **Async response** for non-realtime: "we'll notify when ready". **Pre-scale based on burst prediction**: ML on traffic patterns scale ahead. **Communicate**: "high traffic, request #423, est 30s". **Customer SLA enforce**: gold pays for guaranteed slots, that's the value.

**Q5: Cost grew 3x in 1 week - root cause?**
Common causes: (1) new customer high traffic (check tenant spend leaderboard); (2) prompt template change increased token count (check prompt_template_version metric); (3) cache hit rate dropped (new query patterns? invalidation bug?); (4) model auto-routed expensive more (check model distribution); (5) loop bug agent re-calling LLM (check per-session call count); (6) hostile use / jailbreak inflating tokens; (7) RAG corpus update increased context size. Observability slice dashboard 必须 catch each.

---

## ❌ 易错点 (10 条红线)

1. **No cache layer** — 50% wasted cost on redundant LLM calls
2. **One queue for all tenants** — noisy neighbor, gold 被 bronze 拖死
3. **Sync to LLM API (no queue)** — burst → vendor 429 → cascade fail
4. **Single model for all** — cost 5-10x over optimal
5. **No budget cap** — runaway customer 烧光 bank ($50K/天)
6. **Cache threshold too loose** — wrong-hits 用户骂
7. **No graceful degradation** — peak = total fail
8. **No multi-vendor failover** — vendor down = service down
9. **Cache invalidation 缺失** — stale answers
10. **No retry-after respect** — 429 retry loop amplifies issue

---

## ✅ 加分项 (12 条)

1. **4-layer cache** (exact / semantic / tool / LLM prefix)
2. **Per-tenant priority queues** (gold/silver/bronze)
3. **Per-tenant Redis Lua semaphore** (atomic, <1ms)
4. **Cost-aware routing** with complexity classifier (90/9/1 黄金分布)
5. **Budget enforcement** with atomic Lua + Postgres durable
6. **Graceful degradation 7-step ladder**
7. **Cache invalidation strategy** (TTL + event-based + versioning)
8. **Multi-vendor failover** chain (Self-host → Flash → Claude)
9. **Cost spike detector** (proactive, 5x baseline)
10. **Backpressure signal** in response headers
11. **2026 model pricing precise** (Flash $0.50/$3, Pro $2/$12, Opus $5/$25, Sonnet $3/$15)
12. **Quote BNPL 38% hit / 42% cost reduction** + Indonesia $50K saved

---

## 一句话总结

**LLM cost/scale = 5 layers (cache + queue + rate-limit + cost-routing + budget) + graceful degradation ladder + multi-vendor failover**. 4-layer cache 节 60% LLM call. Cost-aware routing 90/9/1 → 84% cost reduction. Budget cap 防 runaway. Per-tenant 隔离 + priority queue 保 gold SLA. 这是 staff-level cost engineering.

---

## 🃏 Cheat Sheet (印 1 页随身)

```
5 layers in order:
  L1 Cache (exact + semantic + tool + LLM prefix)
  L2 Queue (per-tier priority + per-tenant concurrency)
  L3 Rate limit (token bucket per vendor + per tenant)
  L4 Cost-aware model routing
  L5 Budget enforcement (per-tenant monthly cap)

4-layer cache:
  Exact (hash):   10-20% hit, 100% accurate, TTL 1h
  Semantic (emb): 30-50% on FAQ, 0.95 threshold
  Tool output:    per-tool TTL (balance 5s, static 24h)
  LLM prefix:     vLLM/Anthropic server-side, 60-90% shared

Semantic cache: 0.95 baseline / 0.90 aggressive FAQ / 0.88 verify w/ Haiku / medical 0.97

Priority queue tiers:
  Gold   depth 100  p99 <2s  conc 50 Sonnet/Pro
  Silver depth 500  p99 <5s  conc 20 Haiku/Flash
  Bronze depth 2K   p99 <30s conc 5  Flash
  Free   depth 10K  best-eff conc 1  Flash+canned

Cost-aware routing (90/9/1 黄金):
  <0.3 Flash/Self-host 90% / <0.7 Pro 9% / ≥0.7 Opus 1%
  → Saves 84% vs all-Opus

2026 pricing (memorize):
  Gemini 3 Flash $0.50/$3 (cache $0.10)
  Gemini 3 Pro   $2/$12   (cache $0.40)
  Haiku 4.5      $1/$5    (cache $0.10)
  Sonnet 4.6     $3/$15   (cache $0.30)
  Opus 4.7       $5/$25   (cache $0.50)
  GPT-5.5        $5/$30   (cache $1)
  Self-host 70B  ~$0.30 all

Budget enforcement: per-tenant cap + Atomic Redis Lua + Postgres durable + alert 80/95/100% + 5x baseline spike detector + pre-flight estimate

Graceful degrade 7-step: L1 smaller model / L2 aggressive cache / L3 spillover vendor / L4 drop parallel tools / L5 drop multi-turn / L6 canned / L7 static "try later"

Cache invalidation: TTL 1h general / 5min fresh + event-based Pub/Sub + versioned key

Per-tenant isolation: token bucket per (user,tool,tenant) + concurrency Redis Lua + dedicated replicas gold + backpressure headers

Multi-vendor failover: Self-host 90% / Gemini Flash 8% / Claude Opus 2% — same internal API contract

Observability: cache hit/tier, queue depth/tier, cost/tenant real-time+forecast, model distribution, degradation events, budget util

Cost math 100K QPS: all-Opus $73M/day → optimized $12M/day (84% reduction, $0.0085 → $0.0014/call)

红线:
  - No cache (50% waste)
  - One queue for all (noisy neighbor)
  - Sync to LLM (burst blow)
  - Single model (cost 5-10x)
  - No budget cap (runaway)
  - Cache threshold too loose
  - No degradation (peak fail)
  - Single vendor (down = down)

Resume quotes:
  "BNPL semantic cache 38% hit, cost -42%"
  "Voice agent 7 markets per-tenant budget+concurrency"
  "TikTok payment Redis Lua atomic, <1ms"
  "Self-host Llama 70B 90%, $0.30/1M"
  "Indonesia customer bug $50K saved via budget cap"
```
