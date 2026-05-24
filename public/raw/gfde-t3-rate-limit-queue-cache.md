## 题目

> "Your LLM service serves customer's chatbot. Underlying LLM API has **rate limit (10K TPM, 100 RPM)** and is **expensive ($5/$25 per 1M, Claude Opus 4.7)**. Customer traffic is bursty (100x peaks). Design the system."

或追问形态:

> "Cost is blowing up — 50% of LLM spend is repeated similar questions. Reduce cost without hurting UX."

**出处**: Google FDE T3 cost/scale round 高频题. 2026 几乎所有 enterprise LLM platform 都 hit 这个题.

**Round**: System Design — Cost / Scale (45-60 min)

---

## 这道题在考什么

考你**economics + throughput** for LLM workloads, 同时**保持 UX 不崩**:

1. **4-layer cache** —— exact + semantic + tool output + LLM prefix (vLLM)
2. **Priority queue + per-tenant concurrency** —— gold/silver/bronze tier, noisy neighbor 隔离
3. **Cost-aware model routing** —— Gemini Flash 90% / Pro 9% / Opus 1% 黄金分布
4. **Budget enforcement** —— per-tenant monthly cap, alert 80%, hard stop 100%
5. **Graceful degradation** —— smaller model / aggressive cache / canned response ladder
6. **Vendor rate limit** —— token bucket, 429 retry-after respect
7. **Multi-vendor failover** —— Claude / Gemini / OpenAI / self-host 不绑死

不只 "加 cache 加 queue" 这么简单. 答 staff-level 需要 cost math + tenant tier strategy + graceful UX under burst.

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**Token bucket**: 速率限制经典算法. 一个 bucket 容量 N (burst), 每秒填充 r token. Request 来时消耗对应 token 数, 不够则等待 / 拒绝. 比 fixed-window 更平滑, 比 sliding-window 更轻量. Redis Lua 实现 < 1ms.

**Semantic cache**: 不是精确 hash 匹配, 而是 query embedding 比对相似度. "What's my balance?" 和 "show my account balance" 可能 cosine similarity 0.94 → hit 同一 cached response. 30-50% hit rate on FAQ workloads, 比 exact cache 强很多, 但有 wrong-hit 风险.

**Priority queue with tenant tier**: 多租户 SaaS 必备. Gold tier 优先服务 (低延迟), Bronze tier 高延迟可接受. 每 tier 不同 concurrency cap + queue depth, 防止 noisy neighbor 拖垮 gold tier.

**Graceful degradation**: 系统过载时**不挂, 但降低质量**. 比如: 排队 → 切小 model → 用 cached canned response → 最后 fallback "服务忙, 请稍后". 5 个 step ladder, 每步成本递减, 质量递减.

---

## 2. 核心问题 (灾难场景)

设想没有任何 cache / queue / budget / routing, naive LLM serving:

**灾难 A — Burst 突袭无 queue**:

```
Background: 100 QPS sustained, 突然新闻 push 来流量 → 10K QPS spike

Naive 系统:
  - 10K request 同时打到 LLM API
  - LLM API rate limit 100 RPM → 100 个通过, 9900 个 429
  - 客户端 retry: 9900 × 3 retry = 29700 个 429
  - 用户 95% 看到 "error"
  - 营销 launch 失败, 客户怒

正确: queue + admission control. 10K request 进队列, 按 LLM 容量速度慢慢消费. 用户 wait 几秒比看 error 强.
```

**灾难 B — 没 cache, 50% query 是 FAQ**:

```
Background: chatbot 50% query 是 "how do I reset password?" 之类 5 个 FAQ 变体

Naive: 每个 query 都打 LLM API
Result:
  100K QPS × $0.003/call (Sonnet 4.6) = $300/sec = $25.9M / day
  But 50% 是 FAQ, 50K QPS 重复算
  浪费: $12.95M / day on FAQ redundancy

正确:
  Exact cache: 10-20% hit (重复 query)
  Semantic cache: 30-50% hit on FAQ
  Total cache hit: 50% (主要是 semantic)
  Cost saving: $12.95M / day on FAQ
  实际只需 50K real LLM call × $0.003 = $12.95M / day
  半价
```

**灾难 C — Single model for everything**:

```
Background: 客服 chatbot, 90% query 是简单 ("我能退款吗?"), 10% 复杂 ("帮我分析这 5 个对账单为什么不一致")

Naive: 全用 Claude Opus 4.7 ($5/$25 per 1M tokens)
  Per-call avg: 1K input + 200 output = $0.0085
  100K QPS × $0.0085 = $850/sec = $73M / day

正确: cost-aware routing
  90% → Gemini 3 Flash ($0.50/$3): $0.0011/call
  9% → Gemini 3 Pro ($2/$12): $0.0044/call
  1% → Claude Opus 4.7: $0.0085/call
  
  Avg: 90% × $0.0011 + 9% × $0.0044 + 1% × $0.0085 = $0.0014/call
  Total: $0.0014 × 100K = $140/sec = $12M / day
  
  Saving 84%, eval drop < 1% (因为 simple query 不需要 Opus)
```

**灾难 D — No budget cap, 1 client burn the bank**:

```
Background: 给 100 tenant 服务, 月费 $1000 each

某 tenant 接入 bot, 因为代码 bug 进入死循环 (无限重发同 query)
Bug 持续 24h 才发现
Cost: 100 QPS × $0.005/call × 86400 sec = $43K / day
Tenant 月费 $1000, 你亏 $42K / 月

正确: per-tenant budget cap
  $1000 月费 → $1000 budget cap
  80% used → email alert
  100% used → hard stop, return "monthly limit reached"
  Bug tenant 触顶后停, 你亏 < $1000
```

**正确的 mental model — 5 layer 防御**:

```
Layer 1: Cache (no LLM call needed)        ← cheapest
Layer 2: Queue + concurrency (smooth burst)
Layer 3: Rate limit (respect vendor SLA)
Layer 4: Cost-aware routing (cheap model first)
Layer 5: Budget enforcement (hard stop)

Plus: Graceful degradation ladder under load
```

---

## 3. 典型架构图

**Production stack** (2026 LLM cost/scale):

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Client / Application                             │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     API Gateway / LB                                │
│  - Auth + tenant identification                                     │
│  - Tier lookup (gold / silver / bronze)                             │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 1: Cache (try first, cheapest)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Exact Cache  │→ │ Semantic     │→ │ Tool Output Cache         │  │
│  │ (hash, 1h)   │  │ Cache        │  │ (per-tool TTL)           │  │
│  │ 10-20% hit   │  │ 30-50% hit   │  │                          │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ cache miss
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 2: Priority Queue + Concurrency                              │
│  - Gold queue   (depth 100,  p99 < 2s)                              │
│  - Silver queue (depth 500,  p99 < 5s)                              │
│  - Bronze queue (depth 2000, p99 < 30s)                             │
│  - Per-tenant semaphore (noisy neighbor isolation)                  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 3: Vendor Rate Limit (Token Bucket)                          │
│  - Claude Sonnet 4.6: 50K TPM, 1K RPM bucket                        │
│  - Gemini 3 Pro: 100K TPM, 2K RPM bucket                            │
│  - Self-host: 1M TPM (essentially unlimited)                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 4: Cost-Aware Model Routing                                  │
│  ┌───────────────────────────────────────────┐                      │
│  │ Complexity classifier (cheap LLM Haiku)   │                      │
│  │  query → score (0-1)                       │                      │
│  └────────────────┬──────────────────────────┘                      │
│                   │                                                 │
│        ┌──────────┼──────────┐                                      │
│        ▼ <0.3     ▼ <0.7     ▼ ≥0.7                                 │
│   ┌────────┐ ┌────────┐ ┌────────┐                                  │
│   │ Flash  │ │ Pro    │ │ Opus   │                                  │
│   │ $0.5/3 │ │ $2/12  │ │ $5/25  │                                  │
│   │ 90%    │ │ 9%     │ │ 1%     │                                  │
│   └────────┘ └────────┘ └────────┘                                  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 5: Budget Enforcement (per tenant)                           │
│  - Track running cost per tenant per month                          │
│  - Alert at 80%, hard stop at 100%                                  │
│  - Degraded service ladder                                          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  LLM API call (Claude / Gemini / OpenAI / self-host)                │
└─────────────────────────────────────────────────────────────────────┘

Plus: Graceful Degradation Ladder (when overloaded)
  Step 1: queue depth > 80% → smaller model
  Step 2: cost trend up 50% → aggressive cache (lower threshold)
  Step 3: severe overload → canned response from cache
  Step 4: latency budget hit → drop parallel tool calls
  Step 5: context > 30K → drop multi-turn (single-shot only)
```

---

## 4. 关键分类表

### 4.1 4-layer cache types

| Layer | Match | Hit rate (typical) | Cost | TTL |
|---|---|---|---|---|
| **Exact (hash)** | SHA-256 of (query + conv_id + model) | 10-20% | $0 | 1h |
| **Semantic (embedding)** | cosine > 0.95 | 30-50% on FAQ | embed: $0.02/1M | 1-24h |
| **Tool output** | (tool_id, args_hash) | varies (60-90% for idempotent reads) | $0 | per-tool |
| **LLM prefix (vLLM)** | hash chained blocks | 60-90% shared prefix | $0 | LRU GPU |

### 4.2 Tenant tier 配置

| Tier | Priority queue | Max depth | Concurrency | p99 SLA | Default model | Monthly budget |
|---|---|---|---|---|---|---|
| **Gold** | 1 | 100 | 50 | < 2s | Sonnet 4.6 / Gemini Pro | $10K |
| **Silver** | 2 | 500 | 20 | < 5s | Gemini Flash / Haiku | $1K |
| **Bronze** | 3 | 2000 | 5 | < 30s | Gemini Flash | $100 |
| **Free trial** | 4 | 10000 | 1 | best effort | Flash + canned | $5 |

### 4.3 Cost-aware routing breakdown (2026 prices)

| Model | Input $/1M | Output $/1M | Cache hit $/1M | Use for |
|---|---|---|---|---|
| **Gemini 3 Flash** | $0.50 | $3 | $0.10 (5x off) | 90% of traffic (simple Q&A) |
| **Gemini 3 Pro** | $2 | $12 | $0.40 | 9% (medium complexity) |
| **Claude Haiku 4.5** | $1 | $5 | $0.10 (10x off) | Alt for Flash (better at instruction) |
| **Claude Sonnet 4.6** | $3 | $15 | $0.30 | Alt for Pro |
| **Claude Opus 4.7** | $5 | $25 | $0.50 | 1% hardest cases |
| **GPT-5.5** | $5 | $30 | $1 | Alt for Opus |
| **Self-host Llama 70B FP8** | ~$0.30 | ~$0.30 | N/A | 90% if scale justifies |

### 4.4 Graceful degradation ladder

| Step | Trigger | Strategy | UX impact |
|---|---|---|---|
| **1** | Queue depth > 80% | Switch to smaller model | Slightly lower quality |
| **2** | Cost trending high | Aggressive cache (threshold 0.90 from 0.95) | Some wrong-hits |
| **3** | Severe overload | Canned response from cache, no LLM call | Slow / stale answers |
| **4** | Latency budget exceeded | Drop parallel tool calls | Sequential, slower |
| **5** | Context > 30K | Drop multi-turn (single-shot only) | Less personalized |
| **6** | Vendor down | Spillover to alternative vendor | Different style maybe |
| **7** | All vendors down | Static "service busy, try later" | Last resort |

---

## 5. 具体业务场景 (4-5 个深度变体)

### 场景 A: 新客户 launch 突发流量 (你做过 TikTok PayLater)

```
背景: 客户 launch 新功能 ("Buy Now Pay Later" promotion), 流量 100 QPS → 10K QPS (100x)

事前准备 (跟客户 sync launch 时间):

Step 1: Pre-launch capacity plan
  - 跟客户 sync launch time + 预期流量
  - 提前 2h pre-warm 10x replicas
  - 准备 spillover quota with 备用 vendor (Gemini)

Step 2: Tenant 临时升级到 Gold tier
  - 优先 dispatch
  - Concurrency cap 提高 5x
  - Budget cap 提高 (跟客户谈)

Step 3: Aggressive cache 预热
  - 提前用 launch 期望的 FAQ list 预填 cache
  - Semantic cache threshold 临时降到 0.90 (从 0.95)

Step 4: Real-time monitoring
  - 每 10s 查看 queue depth / cache hit / cost trend
  - 异常 → human-in-loop 决策

Burst arrives:

  10K QPS 进来:
    Cache: 60% hit (FAQ heavy + 预热)
    Queue: 40% pass-through = 4K real QPS
    Within Gold tier capacity ✓
  
  剩余 4K QPS:
    Cost-aware routing:
      90% to Gemini Flash (self-host backup)
      8% to Gemini Pro
      2% to Claude Opus (only for high-value sessions)
  
  Vendor rate limit:
    Token bucket per vendor
    Hit 429: backoff + spillover to alt vendor
  
  Budget:
    Tenant has 5x budget for launch
    Track separately (launch budget vs normal)

Post-launch:
  24h 后流量回 100 QPS, scale down replicas
  Cost reconcile, customer billing breakdown

简历挂钩: 这是 TikTok PayLater promotion 你做过的类型
```

### 场景 B: FAQ-heavy workload (BNPL chatbot)

```
背景: BNPL chatbot, 50% query 是 5 个 FAQ 变体 ("如何还款", "我能 reschedule 吗", "balance 怎么查")

正常 stack:
  Exact cache: 10% hit (重复 query 加 conv_id)
  Semantic cache: 0.95 threshold
  → 综合 30% hit

优化策略:

Step 1: 提取 top FAQ
  - 分析 7d traffic, 找 top 5 高频 query pattern
  - 手动撰写 canonical answer (high quality)
  - 入 'gold list' cache (永不 evict)

Step 2: Lower semantic threshold for FAQ
  - 0.95 → 0.88 (FAQ 专用)
  - Risk: 偶尔 wrong-hit
  - Mitigation: cheap LLM (Haiku $1/$5) verify

Step 3: Personalization on hit
  Cached canonical:
  "您的下次还款日期是 {DATE}, 应还金额 {AMOUNT}"
  
  Hit on cache → 取出 template → 用 user-specific 数据填充
  (不走 LLM, 直接 SQL + template)

Step 4: A/B test canned vs LLM
  - 5% 流量: cached answer
  - 5% 流量: fresh LLM
  - Compare user feedback (thumbs)
  - If canned 同质 → 推广 95% 流量用 canned

实测 (BNPL chatbot 你做过的):
  Cache hit rate: 30% → 38%
  Cost reduction: 30% → 42%
  Quality: thumbs ratio 同样 (canned vs LLM)
  
简历 quote:
  "BNPL chatbot — 50% incoming queries were variations of 5 FAQs. Added semantic cache 0.92 threshold + 1h TTL. Hit rate 38%, cost reduction 42%. Queue with 3 priority tiers (gold ahead of bronze by 5x)."
```

### 场景 C: Multi-tenant noisy neighbor (TikTok payment scale)

```
背景: 10 个 tenant, tenant_A 突发 10x 流量, 把 tenant_B (gold) 拖慢

Without isolation:
  Single queue, single concurrency pool
  Tenant_A 占满 queue → tenant_B 排到后面
  Tenant_B (gold) p99 从 2s → 30s
  Customer breach SLA, churn risk

With per-tenant isolation:

Step 1: Per-tenant quota
  Tenant_A normal: 100 QPS
  Spike to 1000 QPS:
    Token bucket per tenant
    100 QPS pass, 900 QPS 429 "rate limit, retry"
  
  Tenant_B unaffected (own bucket)

Step 2: Per-tenant concurrency semaphore
  Tenant_A: max 200 concurrent in-flight
  超过 → 等待 / 拒绝
  Tenant_A 不能独占 worker pool

Step 3: Tier-based dispatch
  Gold (tenant_B) queue 优先
  Bronze (tenant_A) 排后面 (after gold serviced)

Step 4: Isolated replica pool (优化)
  Gold tier 独立 vLLM replica
  Bronze 用 shared replicas
  Gold 永远不与 bronze 竞争资源

Step 5: Backpressure visible to tenant
  Tenant_A 看到自己的 429 / queue depth dashboard
  自我约束: 改 code 避免 spike

Step 6: Cost transparency
  Tenant_A 看自己 cost spike → 触发自己 budget alert → 自我调整

Result:
  Tenant_B p99 保持 < 2s (gold SLA 守住)
  Tenant_A 自我 throttle, 不再 spike
  Customer A 也满意 (有 429 反馈, 不是 silent fail)

简历挂钩: TikTok payment infra 自然有 per-user QPS 限制
```

### 场景 D: Per-user budget 用完 (free tier scenario)

```
背景: 免费用户每月 $5 budget, 用完了. Agent 怎么办?

Hard stop with graceful UX:

Step 1: 提前 alert
  80% used ($4) → email + in-app banner:
    "You've used $4 of $5 monthly limit. Upgrade for unlimited."
  
  90% used ($4.5) → 警告:
    "Approaching monthly limit. Service will be limited soon."

Step 2: At limit ($5)
  Block real LLM calls
  Graceful response:
    "You've reached your free tier monthly limit. 
     Try our paid tier ($X/month, unlimited) or wait until next month."
  
  Don't 'silent fail' — explicitly tell user

Step 3: Cached-only mode (optional)
  Even after limit hit:
    if query has exact / semantic cache hit:
      return cached (no LLM cost)
    else:
      return upgrade prompt
  
  This way users still get value (familiar queries) but can't burn $$$

Step 4: Cheap model fallback (alt)
  Instead of hard stop:
    Route to Gemini 3 Flash ($0.50/$3, 4x cheaper)
    Extend effective budget 4x
  
  But mark response: "Limited mode (free tier)"

Step 5: Show usage progress
  Always visible: "$3.5 of $5 used (70%)"
  Helps user self-throttle

Step 6: Upsell trigger
  80% used → in-product upgrade CTA
  Reset on month boundary
```

### 场景 E: LLM vendor 突然 cut quota (operational risk)

```
背景: OpenAI 把你配额从 100K TPM 砍到 50K. 还能扛吗?

Setup (proactive):

Setup 1: Multi-vendor接入早就 ready
  - Claude (Anthropic)
  - Gemini (Google)
  - Llama 自托管 (vLLM cluster)
  - OpenAI

  Each as adapter behind same internal API

Setup 2: Real-time fallback config
  primary: openai-gpt-5.5
  fallback_chain: [claude-sonnet-4.6, gemini-3-pro, self-host-llama-70b]
  
  If primary 429 / down: cascade through fallback

Setup 3: Cost-aware routing
  Already mostly on self-host (90%) + Flash (8%) + premium (2%)
  OpenAI cut doesn't kill us if not main load

Response to vendor cut:

Step 1: Immediate spillover (automatic)
  Hit OpenAI 429 → fallback chain kicks in
  
Step 2: Adjust routing weights (5 min)
  Manual: shift 50% OpenAI 路由 to Gemini
  Test eval: 同样 task Gemini quality 如何 (probably 90%+ same)

Step 3: Aggressive cache (1h)
  Lower semantic threshold 0.95 → 0.90
  Hit rate 30% → 50%
  Effective traffic to LLM: half

Step 4: Cheaper model main (4h)
  90% 流量 to Gemini Flash instead of Pro
  Cost saving offsets quota loss

Step 5: Queue + delay (24h, if needed)
  Bronze tier 流量推后处理 (queue, not fail)
  Async response acceptable for non-real-time

Step 6: Notify customer (transparently)
  "Due to vendor capacity, some non-critical features may be delayed"
  SLA breach risk: communicate proactively

Step 7: Long-term (week)
  Negotiate with vendor (or buy more quota)
  Or: scale self-host capacity 2x

防御深度 = multi-vendor + cache + degradation + customer comms
```

---

## 6. 工程 checklist

**设计 5-layer system**:

1. **Cache infrastructure** — Redis (exact + semantic), Qdrant (vector), per-tool TTL config
2. **Embedding model** — text-embedding-3-large or BGE for semantic
3. **Priority queue** — RabbitMQ / Kafka with priority field, or Redis sorted set
4. **Per-tenant rate limiter** — Redis Lua script, token bucket
5. **Per-tenant concurrency** — Redis SETNX semaphore
6. **Cost-aware router** — small classifier (Haiku LLM or trained model)
7. **Multi-vendor adapter** — same API contract over Claude / Gemini / OpenAI / self-host
8. **Budget tracker** — atomic increment in Postgres, alert at 80%, hard stop at 100%
9. **Graceful degradation triggers** — automated monitor + manual override
10. **Observability** — cache hit rate per tier, queue depth, model distribution, cost per tenant

**Cache config per use case**:

```yaml
chatbot_general:
  exact_cache:
    ttl: 3600s
    enabled: true
  semantic_cache:
    threshold: 0.95
    ttl: 7200s
    enabled: true
    verify_with_llm: false   # high-perf path
  tool_output_cache:
    get_balance: {ttl: 5s}    # stale OK
    get_inventory: {ttl: 60s}
    send_email: {ttl: 0}      # don't cache writes

faq_workflow:
  semantic_cache:
    threshold: 0.88           # aggressive
    verify_with_llm: true     # verify with Haiku
  canonical_answers:
    enabled: true
    list: [faq_1, faq_2, ...]
```

---

## 7. 易错坑表

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **No cache layer** | 50% cost wasted on redundant LLM calls. 解: 4-layer cache |
| 2 | **One queue for all tenants** | Noisy neighbor 拖慢 gold tier. 解: per-tenant queue + tier priority |
| 3 | **Sync to LLM API (no queue)** | Burst → vendor 429 → cascade fail. 解: queue + backpressure |
| 4 | **Single model for all** | Cost 5-10x over optimal. 解: cost-aware routing |
| 5 | **No budget cap per tenant** | One client 死循环 burn the bank. 解: monthly cap, alert + hard stop |
| 6 | **Semantic cache threshold too loose** | Wrong-hit rate 高. 解: 0.95 default, lower only after eval |
| 7 | **No graceful degradation** | Peak = total fail. 解: 7-step ladder |
| 8 | **No multi-vendor接入** | Vendor down = service down. 解: 接 2-3 个 vendor + self-host |
| 9 | **Cache invalidation 缺失** | Stale answers when source data changes. 解: TTL + event-based invalidation |
| 10 | **No retry-after respect** | 429 后继续 retry, 加剧 vendor 限流. 解: respect Retry-After header |

---

## 一句话总结 (Part 1)

> **LLM cost/scale system = 5 layers**: (1) cache (exact + semantic + tool + prefix), (2) priority queue + per-tenant concurrency, (3) vendor rate limit (token bucket), (4) cost-aware model routing (Flash 90% / Pro 9% / Opus 1%), (5) budget enforcement (per-tenant cap, alert 80%, hard stop 100%). Plus graceful degradation ladder + multi-vendor failover.
>
> 不做 cache → cost 5x. 不做 routing → cost 5-10x. 不做 budget → 1 个 buggy client 一晚把月预算烧光. 不做 queue → burst 期间用户全 see error.

---

# Part 2 · 5 个深度工程问题

## ⚙️ Problem 1: 4-Layer Cache — Exact, Semantic, Tool Output, LLM Prefix

最便宜的优化是不调用 LLM. 4-layer cache 深挖.

### 1.1 Layer 1: Exact cache (hash match)

```python
class ExactCache:
    """Cheapest cache, 100% accurate when hit"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def cache_key(self, query, conv_id, model, prompt_template_version):
        # Hash everything that affects response
        key_components = f"{query}|{conv_id}|{model}|{prompt_template_version}"
        return hashlib.sha256(key_components.encode()).hexdigest()
    
    async def lookup(self, query, conv_id, model, version):
        key = self.cache_key(query, conv_id, model, version)
        cached = await self.redis.get(f"exact:{key}")
        if cached:
            metrics.incr('cache.exact.hit')
            return msgpack.unpackb(cached)
        metrics.incr('cache.exact.miss')
        return None
    
    async def set(self, query, conv_id, model, version, response):
        key = self.cache_key(query, conv_id, model, version)
        ttl = 3600  # 1h default
        await self.redis.set(
            f"exact:{key}",
            msgpack.packb(response),
            ex=ttl,
        )

# Hit rate analysis:
# - Same user same query within TTL: high hit
# - Different conv but same query: miss (different conv_id)
# - 100K QPS chatbot: 10-20% exact cache hit (repeat queries)
# - Per-call savings: $0.001 per hit (Gemini 3 Flash) to $0.01 (Claude Opus)
# - Storage: 10M cache entries × 5KB = 50GB Redis (manageable)
```

### 1.2 Layer 2: Semantic cache (embedding similarity)

```python
class SemanticCache:
    """Cosine similarity over query embeddings"""
    
    def __init__(self, vector_db, embedding_model):
        self.vector_db = vector_db  # Qdrant / Pinecone
        self.embedding_model = embedding_model
        self.threshold = 0.95
    
    async def lookup(self, query, conv_id=None):
        # 1. Compute query embedding
        emb = await self.embed(query)  # $0.02 / 1M for text-embedding-3-small
        
        # 2. Vector search top-3
        results = await self.vector_db.search(
            emb,
            top_k=3,
            filter={
                "deprecated": False,
                # Optional: per-tenant filter
                "tenant_id": conv_id.split(":")[0] if conv_id else None,
            },
        )
        
        # 3. Apply threshold + optional verification
        for hit in results:
            if hit.score > self.threshold:
                # High confidence hit
                metrics.incr('cache.semantic.hit')
                
                # Optional: verify with cheap LLM if threshold borderline
                if self.threshold - 0.02 <= hit.score <= self.threshold + 0.02:
                    verified = await self._verify(query, hit.payload['original_query'])
                    if not verified:
                        metrics.incr('cache.semantic.verify_miss')
                        continue
                
                return hit.payload['response']
        
        metrics.incr('cache.semantic.miss')
        return None
    
    async def _verify(self, current_query, cached_query):
        """Cheap LLM verifies semantic equivalence"""
        verify_prompt = f"""Are these two questions asking the same thing?
        
Question A: {cached_query}
Question B: {current_query}

Answer only "yes" or "no".
"""
        # Use Haiku 4.5 ($1/$5) — 极便宜
        response = await self.llm.generate(
            verify_prompt,
            model="claude-haiku-4.5",
            max_tokens=5,
        )
        return "yes" in response.content.lower()
    
    async def set(self, query, response, metadata=None):
        emb = await self.embed(query)
        await self.vector_db.upsert(
            id=str(uuid.uuid4()),
            vector=emb,
            payload={
                "original_query": query,
                "response": response,
                "ts": time.time(),
                "metadata": metadata or {},
            },
        )

# Hit rate:
# - FAQ-heavy workload: 30-50%
# - Generic chat: 10-20%
# - Per-call savings: same as exact (when hit)
# - Storage: vector DB scales differently, ~10x cost of Redis but still small

# Threshold tuning:
# 0.95: high precision, lower hit rate
# 0.90: more hits, occasional wrong-hit
# 0.88: aggressive, requires verification step
# Per-domain tuned: medical strict (0.97), FAQ aggressive (0.88)
```

### 1.3 Layer 3: Tool output cache

```python
class ToolOutputCache:
    """Cache idempotent tool reads"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        # Per-tool config
        self.tool_config = {
            "get_balance":      {"ttl": 5,    "user_isolated": True},
            "get_inventory":    {"ttl": 60,   "user_isolated": False},
            "search_users":     {"ttl": 300,  "user_isolated": False},
            "get_static_doc":   {"ttl": 86400,"user_isolated": False},
            "send_email":       {"ttl": 0,    "user_isolated": True},  # don't cache
            "create_order":     {"ttl": 0,    "user_isolated": True},  # don't cache
        }
    
    def cache_key(self, tool_id, args, user_id=None):
        config = self.tool_config.get(tool_id, {})
        if config.get("user_isolated") and user_id:
            return f"tool:{tool_id}:user:{user_id}:{hash(args)}"
        return f"tool:{tool_id}:{hash(args)}"
    
    async def execute_with_cache(self, tool_id, args, user_id, executor):
        config = self.tool_config.get(tool_id, {})
        ttl = config.get("ttl", 0)
        
        if ttl == 0:
            # Don't cache writes
            return await executor(tool_id, args)
        
        key = self.cache_key(tool_id, args, user_id)
        
        # Lookup
        if cached := await self.redis.get(key):
            metrics.incr('cache.tool.hit', tags={"tool": tool_id})
            return msgpack.unpackb(cached)
        
        # Execute
        result = await executor(tool_id, args)
        
        # Cache (only successful)
        if result.success:
            await self.redis.set(key, msgpack.packb(result), ex=ttl)
        
        return result

# Hit rate:
# - Same user query for balance: 80%+ (within 5s TTL)
# - Inventory check during shopping session: 90%+
# - Static doc lookup: 99%+
```

### 1.4 Layer 4: LLM prefix cache (vLLM server-side)

```python
# Already covered in T3.3 (high-throughput).
# Quick recap:

# vLLM 0.6+ flag: --enable-prefix-caching
# Automatically hashes prefix blocks (16 tokens each, chained hash)
# Same conversation / shared system prompt → KV cache reused

# Hit rate:
# - Shared system prompt across all calls: 100% hit (after first)
# - Same conv multi-turn: 80-95% hit
# - Random queries with no shared prefix: 20% hit (only system prompt portion)

# How to maximize:
# 1. Pass conversation_id hint to vLLM (sticky routing by conv_id)
# 2. Use Anthropic prompt_caching (cache_control marker) for cached prefix
# 3. Keep system prompt stable (don't include timestamp / random in it)

# Cost saving:
# - Prefill is 70-80% of LLM call cost
# - 80% prefix hit → 60-70% prefill saved
# - Net cost reduction: 50-60%

# Anthropic prompt caching pricing (2026):
# - Cached input: $0.30 / 1M (Sonnet 4.6) vs $3 / 1M uncached
# - 90% discount on cache hits
# - 5min TTL automatic
```

### 1.5 Combined cache flow

```python
async def query_with_cache(query, conv_id, user_id, request):
    # L1: exact cache
    if cached := await exact_cache.lookup(query, conv_id, ...):
        return cached  # 100% accurate, 0 cost
    
    # L2: semantic cache
    if cached := await semantic_cache.lookup(query):
        return cached  # 95%+ accurate
    
    # L3 caching happens during execution (in tool layer)
    
    # L4: LLM call with prefix cache hint (server-side)
    response = await llm.generate(
        query=query,
        conversation_id=conv_id,  # vLLM uses this for prefix lookup
        prompt_cache=True,  # Anthropic cache_control
    )
    
    # Store in L1 + L2 for future
    await exact_cache.set(query, conv_id, ..., response)
    await semantic_cache.set(query, response)
    
    return response

# Real-world performance (BNPL chatbot type):
# L1 exact:    15% hit, 0 cost when hit
# L2 semantic: 25% hit (of L1 miss), $0.0002 verify cost
# L3 tool:     90% hit on tool ops (when relevant)
# L4 prefix:   75% hit (of fresh LLM calls), 50-60% cost reduction
# 
# Total effective cost reduction: 70-80%
# Original $0.005/call → $0.001-0.0015/call
```

### 1.6 Cache invalidation

```python
class CacheInvalidator:
    """Event-based invalidation for stale data"""
    
    async def on_event(self, event_type, entity):
        if event_type == "user.email_changed":
            # Invalidate all tool caches for this user
            await self.redis.delete_pattern(
                f"tool:get_user_info:user:{entity.user_id}:*"
            )
            await self.redis.delete_pattern(
                f"exact:*user:{entity.user_id}*"
            )
        
        elif event_type == "inventory.stock_changed":
            # Invalidate inventory caches
            await self.redis.delete_pattern(
                f"tool:get_inventory:*sku:{entity.sku}*"
            )
        
        elif event_type == "prompt_template.updated":
            # Old template responses are stale
            await self.redis.delete_pattern(
                f"exact:*template:{entity.template_id}*"
            )
            # Semantic cache: ideally re-index, but expensive
            # Pragmatic: TTL handles it naturally
    
    async def listen(self):
        async for msg in pubsub.subscribe("cache.invalidate"):
            event = json.loads(msg.data)
            await self.on_event(event["type"], event["entity"])
```

---

## ⚙️ Problem 2: Priority Queue + Per-Tenant Concurrency — Gold/Silver/Bronze

Multi-tenant SaaS, gold tier 不能被 bronze 拖慢. 详细讲清楚.

### 2.1 Priority queue implementation

```python
import asyncio
from heapq import heappush, heappop

class PriorityRequest:
    def __init__(self, request, priority, tenant_id, ts):
        self.request = request
        self.priority = priority  # 1=gold, 2=silver, 3=bronze, 4=free
        self.tenant_id = tenant_id
        self.ts = ts
        # Tiebreaker: FIFO within same priority
    
    def __lt__(self, other):
        return (self.priority, self.ts) < (other.priority, other.ts)

class TieredQueue:
    def __init__(self):
        self.queues = {
            "gold":   asyncio.PriorityQueue(maxsize=100),
            "silver": asyncio.PriorityQueue(maxsize=500),
            "bronze": asyncio.PriorityQueue(maxsize=2000),
            "free":   asyncio.PriorityQueue(maxsize=10000),
        }
        self.workers = {
            "gold":   50,  # dedicated worker pool
            "silver": 20,
            "bronze": 5,
            "free":   1,
        }
    
    async def submit(self, request, tier, tenant_id):
        priority_map = {"gold": 1, "silver": 2, "bronze": 3, "free": 4}
        priority = priority_map[tier]
        
        item = PriorityRequest(request, priority, tenant_id, time.time())
        
        try:
            self.queues[tier].put_nowait(item)
        except asyncio.QueueFull:
            # Queue full → fail fast with retry hint
            retry_after = self._estimate_wait(tier)
            raise QueueFull(retry_after=retry_after)
        
        # Wait for result
        return await item.future
    
    def _estimate_wait(self, tier):
        # Based on queue depth + worker count + avg processing time
        depth = self.queues[tier].qsize()
        workers = self.workers[tier]
        avg_proc_time = 1.0  # seconds, from metrics
        return depth * avg_proc_time / workers

class QueueWorker:
    def __init__(self, tier, queue, executor):
        self.tier = tier
        self.queue = queue
        self.executor = executor
        self.running = True
    
    async def run(self):
        while self.running:
            try:
                item = await asyncio.wait_for(self.queue.get(), timeout=1)
            except asyncio.TimeoutError:
                continue
            
            # Acquire per-tenant semaphore (noisy neighbor isolation)
            sem = await self._get_tenant_semaphore(item.tenant_id)
            
            async with sem:
                try:
                    result = await self.executor(item.request)
                    item.future.set_result(result)
                except Exception as e:
                    item.future.set_exception(e)
                finally:
                    self.queue.task_done()
    
    async def _get_tenant_semaphore(self, tenant_id):
        # Per-tenant concurrency cap (e.g., 50 for gold)
        cap = self._tenant_concurrency_cap(tenant_id)
        return asyncio.Semaphore(cap)
```

### 2.2 Per-tenant concurrency semaphore (Redis-based for distributed)

```python
class DistributedTenantSemaphore:
    """Concurrency limit per tenant across all replicas"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    @asynccontextmanager
    async def acquire(self, tenant_id, max_concurrent):
        key = f"sem:tenant:{tenant_id}"
        
        # Lua script for atomic acquire
        acquired = await self.redis.eval("""
            local current = redis.call('INCR', KEYS[1])
            redis.call('EXPIRE', KEYS[1], 60)
            if current > tonumber(ARGV[1]) then
                redis.call('DECR', KEYS[1])
                return 0
            end
            return 1
        """, 1, key, max_concurrent)
        
        if not acquired:
            current = await self.redis.get(key)
            raise TenantConcurrencyExceeded(
                f"Tenant {tenant_id} concurrency {current}/{max_concurrent}"
            )
        
        try:
            yield
        finally:
            await self.redis.decr(key)

# Usage
async def serve(request, tenant_id):
    tier = await get_tenant_tier(tenant_id)
    concurrency_cap = TIER_CONFIG[tier]["concurrency"]
    
    async with semaphore.acquire(tenant_id, concurrency_cap):
        return await execute(request)
```

### 2.3 Tier-based dispatch strategy

```python
class TierDispatcher:
    """Process gold before silver before bronze"""
    
    async def dispatch_loop(self):
        while True:
            # Always check gold first
            if item := await self._try_get(self.gold_queue, timeout=0.01):
                asyncio.create_task(self._process(item, "gold"))
                continue
            
            # Then silver
            if item := await self._try_get(self.silver_queue, timeout=0.01):
                asyncio.create_task(self._process(item, "silver"))
                continue
            
            # Then bronze
            if item := await self._try_get(self.bronze_queue, timeout=0.1):
                asyncio.create_task(self._process(item, "bronze"))
                continue
            
            # No work, brief sleep
            await asyncio.sleep(0.01)
    
    # Better: separate worker pools per tier
    # Gold workers serve only gold queue (guaranteed capacity)
    # Silver workers serve silver primarily, can help gold if idle
    # Bronze workers serve bronze
```

### 2.4 Isolated replica pool (advanced)

```python
# For maximum gold isolation:
# - Dedicated vLLM replicas for gold tier
# - Shared replicas for silver/bronze
# - Gold never competes with bronze for GPU

class IsolatedPool:
    def __init__(self):
        self.gold_replicas = ["vllm-gold-0", "vllm-gold-1", ...]
        self.shared_replicas = ["vllm-shared-0", ...]
    
    def route(self, tier, tenant_id):
        if tier == "gold":
            return random.choice(self.gold_replicas)
        else:
            return self._least_loaded(self.shared_replicas)

# Trade-off:
# Pros: gold absolute isolation, no noisy neighbor possible
# Cons: gold replicas may be underutilized (低 traffic 时浪费)
# Solution: dynamic 'borrow' — gold can use shared if idle
```

### 2.5 Backpressure signaling

```python
class BackpressureManager:
    """Tell upstream when to slow down"""
    
    async def get_backpressure_signal(self, tier):
        depth = await self._queue_depth(tier)
        cap = TIER_CONFIG[tier]["max_depth"]
        utilization = depth / cap
        
        return {
            "queue_depth": depth,
            "queue_capacity": cap,
            "utilization_pct": utilization * 100,
            "estimated_wait_seconds": self._estimate_wait(tier),
            "should_throttle": utilization > 0.8,
        }

# Response headers to clients
@app.get("/v1/chat")
async def chat(req):
    response = await serve(req)
    bp = await backpressure.get_backpressure_signal(req.tier)
    
    headers = {
        "X-Queue-Depth": str(bp["queue_depth"]),
        "X-Queue-Utilization": f"{bp['utilization_pct']:.1f}",
        "X-Estimated-Wait": str(bp["estimated_wait_seconds"]),
    }
    if bp["should_throttle"]:
        headers["X-Throttle-Suggested"] = "true"
    
    return Response(content=response, headers=headers)

# Client SDK can adapt:
# If X-Throttle-Suggested: slow down (e.g., batch requests)
# If queue near full: don't retry aggressively
```

### 2.6 Queue depth metrics + alerts

```python
# Prometheus metrics
queue_depth = Gauge(
    'request_queue_depth',
    'Current queue depth',
    ['tier'],
)

queue_wait_time = Histogram(
    'request_queue_wait_seconds',
    'Time spent in queue',
    ['tier'],
)

queue_full_total = Counter(
    'request_queue_full_total',
    'Requests rejected due to queue full',
    ['tier'],
)

# Alerts
# Gold queue depth > 80 (of 100 max) for 5 min → page
# Silver queue depth > 400 (of 500) for 10 min → slack
# Bronze queue depth > 1800 (of 2000) for 30 min → email
# Queue full rate > 5% sustained → escalate
```

---

## ⚙️ Problem 3: Cost-Aware Model Routing — Gemini Flash 90% / Pro 9% / Opus 1%

不同 query 复杂度不同, 用不同价位 model. 这是 2026 LLM platform 标配.

### 3.1 Complexity classifier

```python
class ComplexityClassifier:
    """Score query complexity 0.0 to 1.0"""
    
    def __init__(self):
        # Lightweight features first
        self.heuristic_rules = [
            (lambda q: len(q.split()) < 5, 0.1),  # very short → simple
            (lambda q: "compare" in q.lower(), 0.7),  # comparison → complex
            (lambda q: "analyze" in q.lower(), 0.7),
            (lambda q: "explain" in q.lower(), 0.5),
            (lambda q: "list" in q.lower(), 0.3),
            (lambda q: q.endswith("?"), 0.4),  # questions vary
        ]
        # Heavier: LLM classifier (Haiku $1/$5)
        self.use_llm_for_borderline = True
    
    async def score(self, query, context=None):
        # Step 1: heuristic fast path
        h_score = 0.5  # default mid
        for rule, score in self.heuristic_rules:
            if rule(query):
                h_score = max(h_score, score)
        
        # Step 2: if borderline (0.4-0.7), use LLM
        if 0.4 <= h_score <= 0.7 and self.use_llm_for_borderline:
            llm_score = await self._llm_classify(query, context)
            return (h_score + llm_score) / 2
        
        return h_score
    
    async def _llm_classify(self, query, context):
        """Haiku classifies complexity"""
        prompt = f"""Score this query's complexity from 0.0 (trivial) to 1.0 (very complex):

Query: {query}
Context: {context or "none"}

Consider:
- Does it need multi-step reasoning? (higher score)
- Does it need specialized knowledge? (higher score)
- Is it a simple fact lookup? (lower score)
- Does it need creative generation? (higher score)

Return only a number between 0.0 and 1.0.
"""
        response = await self.llm.generate(
            prompt,
            model="claude-haiku-4.5",  # cheap classifier
            max_tokens=10,
        )
        try:
            return float(response.content.strip())
        except:
            return 0.5  # fallback
```

### 3.2 Routing logic

```python
class CostAwareRouter:
    def __init__(self, classifier):
        self.classifier = classifier
        # Route config
        self.routes = [
            {"max_complexity": 0.3, "model": "gemini-3-flash", "cost_input": 0.50, "cost_output": 3},
            {"max_complexity": 0.7, "model": "gemini-3-pro", "cost_input": 2, "cost_output": 12},
            {"max_complexity": 1.0, "model": "claude-opus-4.7", "cost_input": 5, "cost_output": 25},
        ]
        # Or self-host:
        # 1st: self-host Llama-70B FP8 (~$0.30/$0.30)
        # 2nd: Gemini 3 Pro
        # 3rd: Claude Opus 4.7
    
    async def route(self, query, context, tenant_tier):
        complexity = await self.classifier.score(query, context)
        
        # Tier-based override
        if tenant_tier == "gold":
            # Gold tier minimum: Pro (don't downgrade to Flash)
            for route in self.routes:
                if route["max_complexity"] >= complexity:
                    if route["model"] == "gemini-3-flash":
                        # Upgrade to Pro for gold tier
                        return self.routes[1]["model"]
                    return route["model"]
        
        # Normal routing
        for route in self.routes:
            if complexity <= route["max_complexity"]:
                return route["model"]
        
        return self.routes[-1]["model"]  # most premium fallback

# Distribution typical:
# 90% complexity < 0.3 → Gemini Flash
# 9% complexity 0.3-0.7 → Gemini Pro
# 1% complexity > 0.7 → Claude Opus

# Cost math:
# 100K QPS × 90% × $0.0011/call = $99/sec (Flash)
# 100K QPS × 9% × $0.0044/call = $40/sec (Pro)
# 100K QPS × 1% × $0.0085/call = $8.5/sec (Opus)
# Total: $147.5/sec = $12.7M / day

# vs all Opus:
# 100K × 1.0 × $0.0085 = $850/sec = $73M / day

# Saving: 84% cost reduction
```

### 3.3 Quality A/B testing

```python
class RoutingQualityMonitor:
    """A/B test to ensure routing doesn't hurt quality"""
    
    async def maybe_promote_for_eval(self, request, complexity, chosen_model):
        # 5% of queries: also run with "premium" model for comparison
        if random.random() < 0.05:
            asyncio.create_task(
                self._dual_run(request, chosen_model)
            )
    
    async def _dual_run(self, request, chosen_model):
        # Run with both chosen model and premium (Opus)
        chosen_resp = await self.llm.generate(request, model=chosen_model)
        premium_resp = await self.llm.generate(request, model="claude-opus-4.7")
        
        # Judge which is better
        comparison = await self.judge.compare(
            query=request.query,
            response_a=chosen_resp.content,
            response_b=premium_resp.content,
            judge_model="claude-sonnet-4.6",
        )
        
        # Track
        await metrics.observe('routing.quality_compare', {
            "chosen_model": chosen_model,
            "winner": comparison.winner,  # 'a' (chosen) / 'b' (premium) / 'tie'
            "complexity_score": request.complexity,
        })
        
        # If chosen loses too often, suggest threshold adjustment
        if comparison.winner == 'b':
            await metrics.incr('routing.suboptimal_count')
```

### 3.4 Per-tenant default model

```yaml
tenant_config:
  acme_corp:
    tier: gold
    default_models:
      simple:    gemini-3-pro          # no Flash for gold
      medium:    claude-sonnet-4.6
      complex:   claude-opus-4.7
    custom_routing:
      override_complex_threshold: 0.6   # easier to hit complex
  
  bnpl_startup:
    tier: silver
    default_models:
      simple:    gemini-3-flash
      medium:    gemini-3-pro
      complex:   gemini-3-pro          # no Opus access
    custom_routing:
      max_model: gemini-3-pro
  
  free_user_pool:
    tier: free
    default_models:
      simple:    gemini-3-flash
      medium:    gemini-3-flash
      complex:   gemini-3-flash         # only Flash for free
```

### 3.5 Self-host fallback chain

```python
class FailoverChain:
    """Try cheap self-host first, escalate to vendor"""
    
    def __init__(self):
        self.chain = [
            {"vendor": "self-host-llama-70b", "cost": 0.0003, "available_check": self.check_self_host},
            {"vendor": "gemini-3-flash", "cost": 0.0011, "available_check": self.check_gemini},
            {"vendor": "claude-haiku-4.5", "cost": 0.001, "available_check": self.check_claude},
            {"vendor": "gemini-3-pro", "cost": 0.0044, "available_check": self.check_gemini},
            {"vendor": "claude-sonnet-4.6", "cost": 0.005, "available_check": self.check_claude},
        ]
    
    async def execute(self, request, max_cost_per_call=0.01):
        for option in self.chain:
            # Skip if too expensive
            if option["cost"] > max_cost_per_call:
                continue
            
            # Skip if not available
            if not await option["available_check"]():
                continue
            
            try:
                return await self.llm.generate(
                    request,
                    model=option["vendor"],
                )
            except (RateLimitExceeded, ServiceUnavailable):
                # Try next in chain
                continue
        
        raise NoFallbackAvailable("All LLM options exhausted")
```

### 3.6 Real ByteDance scale example

```
Voice agent for 7 markets:
- Self-host Llama-3-70B FP8 (vLLM cluster) main: 90% of traffic
- Gemini 3 Flash fallback: 8% (when self-host saturated)
- Claude Opus 4.7: 2% (for high-value enterprise customers)

Cost per call:
- 90% × $0.0003 (self-host) = $0.00027
- 8% × $0.0011 (Flash) = $0.000088
- 2% × $0.0085 (Opus) = $0.00017
Avg: $0.000528/call

100M calls/day × $0.000528 = $52,800/day
Per market: ~$7,500/day
Per user (assuming 100K active): $0.075/user/day = $2.25/user/month

vs all Opus: $52,800 / 0.000528 × 0.0085 = $850K/day (16x more)
Saving: $797K/day = $24M/month
```

简历 quote:

> "For BNPL chatbot, we routed: 90% to self-host Llama-70B ($0.30/1M), 9% to Gemini Pro ($2/$12), 1% to Claude Opus ($5/$25). Eval quality stayed within 1.5% of all-Opus baseline. Cost saving 80%+ vs all-Opus."

---

## ⚙️ Problem 4: Budget Enforcement — Per-Tenant Monthly Cap, Alert 80%, Hard Stop 100%

Budget runaway 是 SaaS 最常见的坑. 详细 enforcement.

### 4.1 Budget tracker (Postgres atomic counter)

```python
class BudgetTracker:
    def __init__(self, db_pool, redis_client):
        self.db = db_pool
        self.redis = redis_client
    
    async def track_cost(self, tenant_id, cost_usd, request_id, metadata):
        """Atomic cost increment"""
        month_key = datetime.utcnow().strftime("%Y-%m")
        
        async with self.db.acquire() as conn:
            async with conn.transaction():
                # Increment monthly spend
                new_spend = await conn.fetchval("""
                    INSERT INTO monthly_spend (tenant_id, month, total_usd)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (tenant_id, month)
                    DO UPDATE SET total_usd = monthly_spend.total_usd + $3,
                                  last_updated = NOW()
                    RETURNING total_usd
                """, tenant_id, month_key, cost_usd)
                
                # Detail log for audit
                await conn.execute("""
                    INSERT INTO cost_log
                    (tenant_id, request_id, cost_usd, ts, model, tokens_in, tokens_out, feature)
                    VALUES ($1, $2, $3, NOW(), $4, $5, $6, $7)
                """, tenant_id, request_id, cost_usd,
                     metadata['model'], metadata['tokens_in'],
                     metadata['tokens_out'], metadata['feature'])
        
        # Cache new spend for fast checks
        await self.redis.set(
            f"spend:{tenant_id}:{month_key}",
            new_spend,
            ex=3600,
        )
        
        return new_spend
    
    async def get_spend(self, tenant_id, month=None):
        month_key = month or datetime.utcnow().strftime("%Y-%m")
        
        # Try cache first
        if cached := await self.redis.get(f"spend:{tenant_id}:{month_key}"):
            return float(cached)
        
        # Fall back to DB
        result = await self.db.fetchval("""
            SELECT total_usd FROM monthly_spend
            WHERE tenant_id = $1 AND month = $2
        """, tenant_id, month_key)
        
        return float(result or 0)
```

### 4.2 Budget enforcement gates

```python
class BudgetGate:
    """Check budget before LLM call, enforce hard stop"""
    
    def __init__(self, tracker, alerter):
        self.tracker = tracker
        self.alerter = alerter
    
    async def check_and_reserve(self, tenant_id, estimated_cost):
        tenant = await db.get_tenant(tenant_id)
        budget = tenant.monthly_budget_usd
        spend = await self.tracker.get_spend(tenant_id)
        
        # Hard stop at 100%
        if spend >= budget:
            await self._handle_over_budget(tenant_id, spend, budget)
            raise BudgetExceeded(
                tenant_id=tenant_id,
                spent=spend,
                budget=budget,
                reset_date=self._next_reset_date(),
            )
        
        # Alert at 80%
        if spend / budget > 0.8 and not await self._already_alerted_80(tenant_id):
            await self.alerter.send_warning(
                tenant_id,
                f"You've used 80% of your monthly budget (${spend:.2f} of ${budget})."
            )
            await self._mark_alerted_80(tenant_id)
        
        # Critical at 95%
        if spend / budget > 0.95 and not await self._already_alerted_95(tenant_id):
            await self.alerter.send_urgent(
                tenant_id,
                f"You've used 95% of your monthly budget. Service will be limited at 100%."
            )
            await self._mark_alerted_95(tenant_id)
        
        # Reserve (optimistic, allow approximate)
        # Note: race condition possible — see section 4.4 for atomic alternative
        return True
    
    async def _handle_over_budget(self, tenant_id, spend, budget):
        tenant = await db.get_tenant(tenant_id)
        
        if tenant.tier == "free":
            # Free tier hard stop, no service
            return "hard_stop"
        elif tenant.tier == "self_serve":
            # Paid but capped, offer upgrade
            return "upgrade_prompt"
        elif tenant.tier == "enterprise":
            # Enterprise: alert account manager, don't hard stop
            await self.alerter.send_to_account_manager(
                tenant_id,
                f"Enterprise customer exceeded ${budget} budget (now ${spend:.2f}). Contact for renewal."
            )
            return "soft_overage"
```

### 4.3 Estimated cost pre-call

```python
class CostEstimator:
    """Estimate cost BEFORE making LLM call"""
    
    def estimate(self, prompt, model, max_output_tokens):
        # Approximate input tokens (tokenizer-dependent, rough 4 chars/token)
        input_tokens = len(prompt) // 4
        
        # Worst case output
        max_output = max_output_tokens
        
        # Get pricing
        prices = MODEL_PRICES[model]
        
        max_cost = (
            input_tokens * prices["input_per_1m"] / 1_000_000 +
            max_output * prices["output_per_1m"] / 1_000_000
        )
        
        return max_cost

# Use in request handler
async def chat_handler(req, tenant_id):
    # Pre-flight estimate
    estimated_cost = cost_estimator.estimate(
        req.prompt,
        req.model,
        max_output_tokens=req.max_tokens
    )
    
    # Check budget
    await budget_gate.check_and_reserve(tenant_id, estimated_cost)
    
    # Execute
    response = await llm.generate(req)
    
    # Track actual cost
    actual_cost = (
        response.usage.input_tokens * MODEL_PRICES[req.model]["input_per_1m"] / 1_000_000 +
        response.usage.output_tokens * MODEL_PRICES[req.model]["output_per_1m"] / 1_000_000
    )
    await tracker.track_cost(tenant_id, actual_cost, req.id, {...})
    
    return response
```

### 4.4 Atomic budget check (race-free)

```python
class AtomicBudgetGate:
    """Race-free budget reservation using Lua"""
    
    async def reserve_or_reject(self, tenant_id, estimated_cost, budget):
        # Atomic check-and-increment
        result = await self.redis.eval("""
            local current = tonumber(redis.call('GET', KEYS[1]) or 0)
            local limit = tonumber(ARGV[1])
            local cost = tonumber(ARGV[2])
            
            if current + cost > limit then
                return {err = 'exceeded', current = current}
            end
            
            redis.call('INCRBYFLOAT', KEYS[1], cost)
            return {ok = 'reserved', current = current + cost}
        """, 1,
            f"reserve:{tenant_id}:{this_month}",
            budget,
            estimated_cost
        )
        
        if result["err"] == "exceeded":
            raise BudgetExceeded(...)
        
        return result["current"]
    
    async def finalize(self, tenant_id, estimated_cost, actual_cost):
        """Adjust reservation to actual"""
        diff = actual_cost - estimated_cost
        if diff != 0:
            await self.redis.incrbyfloat(
                f"reserve:{tenant_id}:{this_month}",
                diff
            )
        # Also write to durable Postgres
        await self.tracker.track_cost(tenant_id, actual_cost, ...)
```

### 4.5 Budget dashboard

```python
# Customer-facing dashboard
async def get_budget_dashboard(tenant_id):
    month_key = datetime.utcnow().strftime("%Y-%m")
    
    tenant = await db.get_tenant(tenant_id)
    spend = await tracker.get_spend(tenant_id, month_key)
    
    # Daily breakdown
    daily = await db.fetch("""
        SELECT DATE(ts) as day, SUM(cost_usd) as cost
        FROM cost_log
        WHERE tenant_id = $1 AND ts >= DATE_TRUNC('month', NOW())
        GROUP BY DATE(ts)
        ORDER BY day
    """, tenant_id)
    
    # By feature
    by_feature = await db.fetch("""
        SELECT feature, SUM(cost_usd) as cost
        FROM cost_log
        WHERE tenant_id = $1 AND ts >= DATE_TRUNC('month', NOW())
        GROUP BY feature
        ORDER BY cost DESC
        LIMIT 10
    """, tenant_id)
    
    # Forecast
    days_in_month = 30  # simplified
    day_of_month = datetime.utcnow().day
    daily_avg = spend / day_of_month
    forecast = daily_avg * days_in_month
    
    return {
        "tenant_id": tenant_id,
        "budget": tenant.monthly_budget_usd,
        "spend": spend,
        "remaining": tenant.monthly_budget_usd - spend,
        "utilization_pct": (spend / tenant.monthly_budget_usd) * 100,
        "forecast_end_of_month": forecast,
        "will_exceed": forecast > tenant.monthly_budget_usd,
        "days_until_reset": days_in_month - day_of_month,
        "daily_breakdown": daily,
        "top_features_by_cost": by_feature,
    }
```

### 4.6 Cost spike detection (proactive)

```python
class CostSpikeDetector:
    """Detect unusual cost patterns before budget hit"""
    
    async def check(self, tenant_id):
        # Hourly spend
        hourly = await db.fetchval("""
            SELECT SUM(cost_usd) FROM cost_log
            WHERE tenant_id = $1 AND ts > NOW() - INTERVAL '1 hour'
        """, tenant_id)
        
        # 7-day same hour average
        baseline = await db.fetchval("""
            SELECT AVG(hourly_cost) FROM (
                SELECT DATE_TRUNC('hour', ts) as h, SUM(cost_usd) as hourly_cost
                FROM cost_log
                WHERE tenant_id = $1
                  AND ts BETWEEN NOW() - INTERVAL '7 days' AND NOW() - INTERVAL '1 hour'
                  AND EXTRACT(HOUR FROM ts) = EXTRACT(HOUR FROM NOW())
                GROUP BY h
            ) t
        """, tenant_id)
        
        if baseline > 0 and hourly > baseline * 5:
            # 5x spike alarm
            await alerter.send_to_tenant(
                tenant_id,
                f"Unusual cost spike: ${hourly:.2f} this hour vs avg ${baseline:.2f}. Investigate to avoid budget exceeded."
            )
            
            # Auto-investigate
            recent = await db.fetch("""
                SELECT feature, COUNT(*) as calls, SUM(cost_usd) as cost
                FROM cost_log
                WHERE tenant_id = $1 AND ts > NOW() - INTERVAL '1 hour'
                GROUP BY feature
                ORDER BY cost DESC
                LIMIT 3
            """, tenant_id)
            
            await alerter.send_diagnostics(tenant_id, recent)
```

---

## ⚙️ Problem 5: Graceful Degradation Ladder — Smaller Model / Aggressive Cache / Canned Response

系统过载时不能挂. 7-step ladder 详细.

### 5.1 Ladder 总览

```
Trigger 越严重, 降级越深:

Level 1: Queue depth > 80%
  → Switch to smaller model (Pro → Flash)

Level 2: Cost trending up 50% / hour
  → Aggressive cache (threshold 0.95 → 0.90)

Level 3: Vendor 429 / partial outage
  → Spillover to alternative vendor

Level 4: Latency budget exceeded (TTFT > 3s)
  → Drop parallel tool calls (sequential only)

Level 5: Context > 30K tokens
  → Drop multi-turn (single-shot only)

Level 6: Severe overload (queue > 95%, all vendor down)
  → Canned response from cache, no LLM call

Level 7: Total fail
  → Static "Service busy, try again in N minutes"
```

### 5.2 Degradation controller

```python
class DegradationController:
    """Monitor system state, trigger degradation levels"""
    
    def __init__(self):
        self.level = 0  # 0 = normal
        self.recovery_window = 60  # seconds
        self.last_change_ts = 0
    
    async def update_state(self):
        """Run every 10s"""
        triggers = await self._check_all_triggers()
        
        # Pick most severe
        new_level = max(triggers.values()) if triggers else 0
        
        # Smooth transitions (don't flap)
        if new_level > self.level:
            # Degrade quickly
            self.level = new_level
            self.last_change_ts = time.time()
            await self._notify_systems(self.level, triggers)
        elif new_level < self.level:
            # Recover slowly (wait for sustained improvement)
            if time.time() - self.last_change_ts > self.recovery_window:
                self.level = new_level
                self.last_change_ts = time.time()
                await self._notify_systems(self.level, triggers)
    
    async def _check_all_triggers(self):
        triggers = {}
        
        # Trigger 1: queue depth
        depth = await self._max_queue_utilization()
        if depth > 0.95:
            triggers["queue"] = 6
        elif depth > 0.80:
            triggers["queue"] = 1
        
        # Trigger 2: cost trend
        cost_growth = await self._hourly_cost_growth()
        if cost_growth > 1.5:
            triggers["cost"] = 2
        
        # Trigger 3: vendor health
        unhealthy = await self._unhealthy_vendors()
        if len(unhealthy) >= 2:
            triggers["vendor"] = 3
        
        # Trigger 4: latency
        p99 = await self._p99_latency_last_5min()
        if p99 > 3.0:
            triggers["latency"] = 4
        
        # Trigger 5: context size
        avg_context = await self._avg_context_size()
        if avg_context > 30000:
            triggers["context"] = 5
        
        return triggers
    
    async def _notify_systems(self, level, triggers):
        """Broadcast new level to all subsystems"""
        await pubsub.publish("degradation.level", {
            "level": level,
            "triggers": triggers,
            "ts": time.time(),
        })
```

### 5.3 Subsystem responses

```python
class ModelRouter:
    """Adjust routing based on degradation level"""
    
    def __init__(self):
        self.degradation_level = 0
        asyncio.create_task(self._subscribe_degradation())
    
    async def _subscribe_degradation(self):
        async for msg in pubsub.subscribe("degradation.level"):
            event = json.loads(msg.data)
            self.degradation_level = event["level"]
    
    def adjusted_route(self, query, original_route):
        if self.degradation_level >= 1:
            # Level 1: downgrade model
            return self._downgrade(original_route)
        return original_route
    
    def _downgrade(self, model):
        downgrade_map = {
            "claude-opus-4.7": "claude-sonnet-4.6",
            "claude-sonnet-4.6": "claude-haiku-4.5",
            "gemini-3-pro": "gemini-3-flash",
            "gpt-5.5": "claude-sonnet-4.6",
        }
        return downgrade_map.get(model, model)

class CacheController:
    """Adjust cache aggressiveness"""
    
    def __init__(self):
        self.semantic_threshold = 0.95
        asyncio.create_task(self._subscribe_degradation())
    
    async def _subscribe_degradation(self):
        async for msg in pubsub.subscribe("degradation.level"):
            event = json.loads(msg.data)
            level = event["level"]
            
            if level >= 2:
                self.semantic_threshold = 0.90  # more aggressive
            elif level >= 4:
                self.semantic_threshold = 0.85  # very aggressive
            else:
                self.semantic_threshold = 0.95  # normal
            
            log.info(f"Cache threshold adjusted to {self.semantic_threshold} (level {level})")
```

### 5.4 Canned response fallback

```python
class CannedResponseFallback:
    """Pre-defined responses for severe overload"""
    
    def __init__(self):
        self.canned = {
            "balance_inquiry": "Your balance information is temporarily unavailable. Please check the app directly or try again in a few minutes.",
            "general_help": "I'm currently experiencing high demand. Here are common topics: [list of FAQ]. Or try again in a few minutes.",
            "fallback": "Service is temporarily busy. Please try again in 1-2 minutes. Sorry for the inconvenience.",
        }
        # Pre-computed vector embeddings for matching
        self.canned_embeddings = {}
    
    async def maybe_canned(self, query, degradation_level):
        if degradation_level < 6:
            return None  # not yet at canned fallback
        
        # Match query to canned category
        emb = await embed(query)
        
        best_match = None
        best_score = 0
        for canned_key, canned_emb in self.canned_embeddings.items():
            score = cosine_similarity(emb, canned_emb)
            if score > best_score:
                best_score = score
                best_match = canned_key
        
        if best_score > 0.7:
            response = self.canned[best_match]
        else:
            response = self.canned["fallback"]
        
        # Log degraded response
        await metrics.incr('degradation.canned_response_served')
        
        return response
```

### 5.5 User-facing communication

```python
class UserFacingDegradation:
    """Communicate degradation to users gracefully"""
    
    async def wrap_response(self, response, degradation_level):
        if degradation_level == 0:
            return response  # normal
        
        if degradation_level >= 4:
            # Add 'high demand' badge
            response.metadata["degraded"] = True
            response.metadata["badge"] = "Limited mode (high demand)"
        
        if degradation_level >= 6:
            # Explicit notification
            response.content = f"{response.content}\n\n_(Note: Service is currently busy. Some features may be limited.)_"
        
        return response

# Frontend uses metadata to show banner:
# "High traffic — responses may be slower than usual"
```

### 5.6 Recovery + post-incident

```python
class RecoveryManager:
    """Monitor recovery and run post-incident analysis"""
    
    async def on_recovery(self, from_level, to_level):
        # Run automatic post-incident
        incident = await db.get_active_incident()
        if not incident:
            return
        
        # Compute incident metrics
        report = {
            "incident_id": incident.id,
            "started": incident.started_at,
            "ended": datetime.utcnow(),
            "peak_level": incident.peak_level,
            "affected_tenants": incident.affected_tenants_count,
            "requests_degraded": incident.degraded_request_count,
            "canned_responses_served": incident.canned_count,
            "estimated_cost_avoided": incident.cost_avoided,
            "estimated_revenue_at_risk": incident.revenue_at_risk,
        }
        
        # Generate timeline
        timeline = await db.fetch("""
            SELECT ts, level, triggers
            FROM degradation_events
            WHERE incident_id = $1
            ORDER BY ts
        """, incident.id)
        
        report["timeline"] = timeline
        
        # Slack post-mortem
        await slack.post(
            channel="#incident-review",
            text=f"Degradation recovery: {report['incident_id']}",
            attachments=[report],
        )
        
        # Update incident as closed
        await db.close_incident(incident.id, report)
```

---

# Part 3 · 串起来看

5 个 problem 是同一系统的不同 layer:

1. **4-layer cache** 决定 "能不能不调 LLM"
2. **Priority queue + concurrency** 决定 "noisy neighbor 怎么隔离"
3. **Cost-aware routing** 决定 "什么 query 用什么 model"
4. **Budget enforcement** 决定 "怎么防止 client 烧光"
5. **Graceful degradation** 决定 "过载时怎么不挂"

面试场把 5 层讲清楚 + 给 cost math + 你 BNPL chatbot 经验, 就是 staff-level cost engineering.

---

## 必问 clarifying questions

**1. Latency tolerance**

> "Per query < 1s real-time, or 10s OK? Affects queue depth + degradation strategy."

**2. Cache feasibility**

> "FAQ-heavy (50% similar queries) or all unique? Determines semantic cache ROI."

**3. Tenant tiers**

> "Gold / silver / bronze? Different SLA? Affects priority queue + budget design."

**4. Budget model**

> "Per-customer-monthly contract, pay-as-you-go, or freemium? Affects budget enforcement strictness."

**5. Quality bar**

> "Acceptable to fallback to smaller model under load? (Affects degradation ladder.)"

**6. Vendor strategy**

> "Single vendor lock-in or multi-vendor + self-host? Affects failover design."

---

## 5 步框架 (sample 45-60 min answer)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify latency / cache / tenant / budget |
| 5-15 min | 5-layer architecture overview |
| 15-25 min | 4-layer cache deep dive (exact + semantic + tool + prefix) |
| 25-35 min | Cost-aware routing + budget enforcement |
| 35-45 min | Priority queue + per-tenant isolation |
| 45-55 min | Graceful degradation ladder + observability |
| 55-60 min | Q&A + cost math |

---

## 我会这样答 (sample 完整版)

> "Clarify — *[假设: latency < 3s OK, FAQ-heavy (50% similar), 3 tenant tiers, monthly contract per tenant, smaller-model fallback acceptable, multi-vendor + self-host available]*.
>
> **5-layer defense**:
>
> **(L1) Cache** — Try first, cheapest:
> - Exact (hash): 15% hit
> - Semantic (Qdrant + embedding cosine > 0.95): 35% hit on FAQ
> - Tool output (per-tool TTL): 80% hit on idempotent reads
> - LLM prefix (vLLM server-side): 75% hit when shared system prompt
> - Combined: 60% of queries avoid full LLM call
>
> **(L2) Queue + per-tenant concurrency**:
> - 3 tier priority queue (Gold/Silver/Bronze)
> - Per-tenant Redis Lua semaphore (no noisy neighbor)
> - Gold tier dedicated worker pool (isolation)
> - Backpressure signal in response headers
>
> **(L3) Vendor rate limit** (token bucket per vendor):
> - Respect vendor SLA (e.g., Claude 50K TPM)
> - 429 → Retry-After respected
> - Spillover to alternative vendor when one hits limit
>
> **(L4) Cost-aware routing**:
> - Complexity classifier: heuristic + Haiku fallback for borderline
> - 90% Self-host Llama 70B ($0.30/1M) for simple
> - 9% Gemini 3 Pro ($2/$12) for medium
> - 1% Claude Opus 4.7 ($5/$25) for hard
> - Tier override: Gold tenants never get Flash, Free never gets Opus
>
> **(L5) Budget enforcement**:
> - Per-tenant monthly cap
> - Atomic Redis Lua check + Postgres durable record
> - Alert at 80% (email), 95% (urgent), 100% (hard stop or upgrade prompt)
> - Cost spike detector (5x hourly vs 7-day baseline)
>
> **Graceful degradation ladder** (7-step):
> Level 1 (queue 80%): downgrade model (Pro → Flash)
> Level 2 (cost trend up 50%): aggressive cache (0.95 → 0.90)
> Level 3 (vendor 429): spillover to alt vendor
> Level 4 (latency p99 > 3s): drop parallel tool calls
> Level 5 (context > 30K): drop multi-turn
> Level 6 (severe overload): canned response from cache
> Level 7 (total fail): static "service busy, try later"
>
> **Cost math** (100K QPS chatbot):
> Without optimization (all Opus): $73M / day
> With full stack: $12M / day (84% reduction)
> Per-call: $0.0085 → $0.0014
>
> **Observability**: cache hit rate per tier, queue depth per tier, cost per tenant real-time, model distribution, degradation events.
>
> **The single biggest win**: semantic cache 38% hit rate at 0.92 threshold for FAQ-heavy workloads — saw on BNPL chatbot, dropped cost 42%."

---

## 简历专属 reframe — Gao Xin's hooks

| Topic | 你的经验 | How to quote |
|---|---|---|
| **Cache strategy** | Voice agent — repeated phrase recognition | "Voice agent had semantic cache for repeated user phrases (e.g., 'check my balance'). 35% hit rate, cost dropped 30%." |
| **Rate limit + queue** | TikTok payment infra natural scale | "TikTok payment had natural per-user QPS limits. Per-tenant token bucket Redis Lua, sub-1ms latency. Easy to apply to LLM rate limits." |
| **Cost routing** | BNPL chatbot — intent → tool routing | "BNPL chatbot: simple query → small model (Gemini Flash), complex → big (Claude). 90/9/1 split, eval drop < 1%." |
| **Multi-tenant** | Voice agent 7 markets | "Voice agent for 7 markets had per-market budget + concurrency cap. Indonesia spikes didn't affect Singapore." |
| **Budget enforcement** | TikTok payment quota / chargeback | "TikTok payment had quota workflow — atomic Redis Lua check + Postgres durable record. Applied same pattern to LLM cost cap." |
| **Degradation** | Voice agent fallback to text-input under ASR overload | "Under ASR overload, voice agent gracefully fell back to text-input mode. Same pattern for LLM: smaller model → cached canned → text fallback." |
| **Multi-vendor** | Self-host vLLM + external API | "Self-host vLLM main (90%), Gemini Flash spillover (8%), Claude Opus VIP (2%). Vendor outage = no service disruption." |

**主动 quote**:

> "BNPL chatbot at TikTok PayLater — 50% of incoming queries were variations of 5 FAQs ('how do I reschedule', 'what's my balance', 'when due', 'cancel payment', 'change card'). We added semantic cache with 0.92 threshold + 1h TTL on Qdrant + text-embedding-3-large. Hit rate 38%, cost reduction 42%. Queue with 3 priority tiers (gold ahead of bronze by 5x). When peak hit, cost-routing automatically pushed non-critical queries to Gemini 3 Flash ($0.50/$3 per 1M, ~10x cheaper than Claude Opus 4.7), no measurable quality drop on eval suite. Budget enforcement: per-tenant atomic Lua check + Postgres durable record. One Indonesian customer's bug ran 10K loop in 1 day — budget cap saved us from $50K hit, hard stop at $1K monthly limit."

---

## 5 follow-ups

**Q1**: "Semantic cache wrong-hit — returns answer for slightly different question. Mitigate?"

**A**:
- **Threshold tuning per product**: medical strict (0.97), FAQ aggressive (0.88), general 0.95
- **Verification pass**: cheap LLM (Haiku $1/$5) compares cached question to current. 10ms latency.
- **Personalization layer**: cached answer + user context → tailored response (don't return verbatim)
- **Per-domain stricter**: financial / medical higher threshold
- **A/B canned vs LLM**: measure thumbs ratio, if canned matches LLM → safe to use

**Q2**: "Cache invalidation — when underlying data changes, stale cached answer."

**A**:
- **TTL based**: 1h for general, 5min for fresh data (e.g., real-time balance)
- **Event-based**: data update → pub/sub → invalidate cache entries matching pattern
- **Versioning**: cache key includes data_version, bump on update → naturally bypass old
- **Best-effort**: 5% stale acceptable for cost savings; alert if more
- **Per-tool config**: get_balance 5s, get_static_doc 24h

**Q3**: "Customer says cache makes responses 'feel canned'. Address?"

**A**:
- **Variation layer**: cache + cheap LLM 'rephrase' for variety
- **Lower threshold + personalize**: get semantic hit + run quick personalization pass
- **Smarter granularity**: cache structured answer, LLM formats per user
- **Disable cache for chatty / creative interactions** (only cache transactional)
- **Personalization slots**: cached "Your balance is {AMOUNT}, due {DATE}" — fill from DB

**Q4**: "Burst 100x — queue fills, users wait long. Better?"

**A**:
- **Reservation system**: gold tier guaranteed slots, never wait
- **Spillover to slower / cheaper model**: never reject, just downgrade
- **Async response** for non-realtime: 'we'll notify when ready'
- **Pre-scale based on burst prediction**: ML model on traffic patterns, scale ahead
- **Communicate**: 'high traffic, your request is #423 in queue, estimated 30s'
- **Customer SLA enforce**: gold pays for guaranteed slots, that's the value

**Q5**: "Cost grew 3x in 1 week — root cause?"

**A**: Common causes:
- **New customer with high traffic** (check tenant spend leaderboard)
- **Prompt template change increased token count** (check prompt_template_version metric)
- **Cache hit rate dropped** (look at why — new query patterns? cache invalidation bug?)
- **Model switch** (auto-routed expensive more — check model distribution)
- **Loop bug** (agent re-calling LLM unnecessarily — check per-session call count)
- **Hostile use / jailbreak attempts** inflating tokens
- **RAG corpus update** increased context size

Observability must catch each via slice analysis dashboard.

**Q6** (bonus): "Customer wants 'unlimited' tier — how price?"

**A**:
- **Fair use cap**: 'unlimited' but hidden cap (10x average usage) to prevent abuse
- **Anomaly detection**: if usage spikes 10x baseline, auto-throttle + alert
- **Per-user-per-day cap within tenant**: prevents single user burning shared budget
- **Cost-plus pricing**: bill per-token at margin (e.g., 2x raw cost)
- **Reserved capacity model**: tenant pays for X GPU-hours, that's their cap
- **Tier limits**: enterprise gets 100K calls/day, that's it

---

## ❌ 易错点 (top 10)

1. **No cache layer** — 50% wasted cost on redundant LLM calls
2. **One queue for all tenants** — noisy neighbor
3. **Sync to LLM API (no queue)** — burst → vendor 429 → cascade fail
4. **Single model for all** — cost 5-10x over optimal
5. **No budget cap** — runaway customer burns the bank
6. **Cache threshold too loose** — wrong-hits
7. **No graceful degradation** — peak = total fail
8. **No multi-vendor接入** — vendor down = service down
9. **Cache invalidation 缺失** — stale answers
10. **No retry-after respect** — 429 retry loop amplifies issue

---

## ✅ 加分项 (top 12)

1. **4-layer cache** (exact / semantic / tool / LLM prefix)
2. **Per-tenant priority queues** (gold/silver/bronze)
3. **Per-tenant Redis Lua semaphore** (atomic, < 1ms)
4. **Cost-aware routing** with complexity classifier (90/9/1)
5. **Budget enforcement** with atomic Lua + Postgres durable
6. **Graceful degradation ladder** (7 steps)
7. **Cache invalidation strategy** (TTL + event-based + versioning)
8. **Multi-vendor failover** chain
9. **Cost spike detector** (proactive, 5x baseline)
10. **Backpressure signal** in response headers
11. **2026 model pricing** (Flash $0.50/$3, Pro $2/$12, Opus $5/$25)
12. **Quote BNPL 38% hit / 42% cost reduction**

---

## 一句话总结

> **LLM cost/scale = 5 layers (cache + queue + rate-limit + cost-routing + budget) + graceful degradation ladder + multi-vendor failover**. 4-layer cache 节 60% LLM call. Cost-aware routing 84% cost reduction (Flash 90% / Pro 9% / Opus 1%). Budget cap 防止 runaway. Per-tenant 隔离 + priority queue 保 gold SLA. 这是 staff-level cost engineering.

---

## Cheat Sheet (印 1 页)

```
5 layers in order:
  L1 Cache (exact + semantic + tool + LLM prefix)
  L2 Queue (per-tier priority + per-tenant concurrency)
  L3 Rate limit (token bucket per vendor + per tenant)
  L4 Cost-aware model routing
  L5 Budget enforcement (per-tenant monthly cap)

4-layer cache:
  Exact (hash):   10-20% hit, 100% accurate
  Semantic (emb): 30-50% on FAQ, 0.95 threshold
  Tool output:    per-tool TTL (get_balance 5s, static 24h)
  LLM prefix:     vLLM server-side, 60-90% shared prefix

Semantic cache config:
  Threshold 0.95: high precision baseline
  Threshold 0.90: aggressive (FAQ)
  Threshold 0.88: verify with cheap LLM (Haiku $1/$5)
  Per-domain: medical 0.97, FAQ 0.88

Priority queue tiers:
  Gold:   depth 100,  p99 < 2s,  concurrency 50, model Sonnet/Pro
  Silver: depth 500,  p99 < 5s,  concurrency 20, model Haiku/Flash
  Bronze: depth 2000, p99 < 30s, concurrency 5,  model Flash
  Free:   depth 10K,  best effort, concurrency 1, model Flash + canned

Cost-aware routing (90/9/1):
  Complexity < 0.3: Self-host or Flash ($0.50/$3) — 90%
  Complexity < 0.7: Gemini Pro ($2/$12) — 9%
  Complexity ≥ 0.7: Opus 4.7 ($5/$25) — 1%
  
  Saves 84% cost vs all-Opus

2026 pricing:
  Gemini 3 Flash:  $0.50/$3  (cache $0.10)
  Gemini 3 Pro:    $2/$12    (cache $0.40)
  Haiku 4.5:       $1/$5     (cache $0.10)
  Sonnet 4.6:      $3/$15    (cache $0.30)
  Opus 4.7:        $5/$25    (cache $0.50)
  GPT-5.5:         $5/$30    (cache $1)
  Self-host 70B:   ~$0.30 all

Budget enforcement:
  Per-tenant monthly cap
  Atomic Redis Lua check (race-free)
  Postgres durable record
  Alert at 80%, urgent at 95%, hard stop at 100%
  Cost spike detector (5x hourly baseline)
  Pre-flight cost estimate

Graceful degradation (7-step):
  L1 queue 80%:   smaller model
  L2 cost trend:  aggressive cache 0.90
  L3 vendor 429:  spillover to alt vendor
  L4 latency >3s: drop parallel tool calls
  L5 ctx >30K:    drop multi-turn
  L6 severe:      canned response from cache
  L7 total fail:  static "try later"

Cache invalidation:
  TTL: 1h general, 5min fresh data
  Event-based: data update → pub/sub → invalidate
  Versioning: cache key includes data_version

Per-tenant isolation:
  Token bucket per (user, tool, tenant)
  Concurrency semaphore Redis Lua
  Dedicated replicas for gold
  Backpressure headers to client

Multi-vendor failover:
  Self-host (cheapest, 90%)
  Gemini Flash (8%, fallback)
  Claude Opus (2%, VIP)
  Cross-vendor: same internal API contract

Observability priorities:
  Cache hit rate per tier
  Queue depth per tier
  Cost per tenant (real-time + forecast)
  Model distribution (% Flash / Pro / Opus)
  Degradation events
  Budget utilization

Cost math (100K QPS):
  All Opus:     $73M/day
  Optimized:    $12M/day (84% reduction)
  Per-call:     $0.0085 → $0.0014

红线:
  - No cache (50% waste)
  - One queue for all (noisy neighbor)
  - Sync to LLM (burst blow)
  - Single model (cost 5-10x)
  - No budget cap (runaway)
  - Cache threshold too loose (wrong-hits)
  - No degradation (peak fail)
  - Single vendor (down = down)

Resume quotes:
  "BNPL chatbot semantic cache 38% hit, cost down 42%"
  "Voice agent 7 markets per-tenant budget + concurrency"
  "TikTok payment Redis Lua atomic check, < 1ms"
  "Self-host Llama 70B 90%, cost $0.30/1M"
```
