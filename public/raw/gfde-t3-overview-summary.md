# 🎯 T3 · LLM Engineering System Design 全景 — 冲刺版

> 完整版: [gfde-t3-overview.html](gfde-t3-overview.html). 这页是 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: production-grade LLM platform, multi-tenant SaaS, 10K-100K QPS sustained, p99 chat 1-2s / voice 300ms / batch best-effort, 月预算 $1M, multi-region GCP-first stack, multi-LLM vendor + self-host vLLM."

**核心 framing**: LLM system ≠ 普通 web service. 5 个独特属性改变所有 tradeoff:

```
| 维度        | Web service | LLM application      |
| Latency     | <100ms p99  | 5-30s p99 (token变长) |
| Cost/req    | Negligible  | $0.001-$1.0 (token)  |
| Determinism | Yes         | No (temp>0)          |
| Downstream  | 1 DB+cache  | LLM + N tool + M RAG |
| Failures    | Net/5xx     | + hallucination + quota |
```

→ 推论: cost 是 first-class, observability 是 multi-dim, state 是 5 种, failure handling multi-layer.

### Layer 1: 架构骨架 (一张图)

```
Edge → API Gateway (auth/rate) → App Layer (Conversation/Router/MCP Proxy/Observ)
  → Cache + Queue + Tool Registry + Tracing
  → vLLM cluster + LLM vendors (Gemini 3 Pro $2/$12, Flash $0.50/$3, Opus 4.7 $5/$25)
  → Vector DB (Qdrant/Pinecone) + Temporal workflow + GCS audit/eval DB
```

### Layer 2: 6 个 sub-topic (各 1 句压扁)

- **T3.1 Stateless vs Stateful**: 生产 default API 表面 stateless + 内部 hybrid 4-tier (LRU/Redis/DB/KV cache), voice 是 strict stateful 例外.
- **T3.2 MCP / API Proxy**: MCP (Anthropic 2024 标准) 3 原语 (Resources/Tools/Prompts) + Gateway 6 责任 (discover/auth/RL/obs/cache/version).
- **T3.3 High throughput**: 6 levers (continuous batch + PagedAttn + prefix cache + spec decode + TP + FP8) 叠乘 50-100x naive baseline.
- **T3.4 Observability**: 4 layers (OTel trace + LLM-specific log + Prometheus metric + eval-in-prod 5% LLM-judge).
- **T3.5 Rate limit/Queue/Cache**: 5-layer cost defense, 4-layer cache + priority queue + cost-aware routing (90/9/1 Flash/Pro/Opus) → 6-10x cost reduction.
- **T3.6 Eventual consistency**: 2PC fails cross-vendor → Saga + Outbox + idempotency + verify-on-timeout + Temporal/DBOS for 5+ step.

### Layer 3: 5 设计 Patterns 全记 (面试速查)

```
A. Stateless API + client conversation_id (default chatbot)
B. Stateful WebSocket (voice only, <500ms latency)
C. Cost-aware model routing (Flash 90% / Pro 9% / Opus 1%)
D. Saga / Outbox for multi-step agent
E. 4-layer observability pipeline (OTel + LangSmith + Prom + eval)
```

### Edge cases

- **EC1 Cost runaway**: agent 自循环 → per-session cost cap + max iterations + auto-stop.
- **EC2 Timeout propagation**: outer 30s / inner 25s 嵌套挂 → deadline propagation header.
- **EC3 Vendor 429 burst**: multi-provider failover, Gemini → Anthropic → Self-host.
- **EC4 PII in prompt**: 用户粘信用卡 → Presidio redact before LLM call.
- **EC5 Eval drift**: model 升级后 faithfulness 掉 → pre-deploy eval gate + post drift alarm.

### Production hardening

- **Monitor**: cache hit rate, blended cost/1M token, eval pass rate trend, jailbreak attempts/min.
- **Alert tiers**: P0 PagerDuty (SLO breach 5min), P1 Slack ML (eval drop > 5pp), P2 weekly email.
- **Cost guard**: per-tenant monthly budget cap, 80% alert / 100% hard stop.
- **Chaos test**: weekly random node kill + monthly AZ failure + quarterly region failover.

### 🪝 Resume hook

"我在 TikTok PayLater 7-market voice agent + BNPL chatbot 跑过这 6 个 sub-topic 完整 stack. Voice agent 是 stateful WebSocket (TTFT 280ms via vLLM 6-lever stack), BNPL 是 stateless 4-tier cache (cost $0.85/1M vs all-Opus $5/1M = 6x). Indonesia refund 是 Temporal Saga 156K refunds 0 double. 这 3 个产品覆盖整个 T3 圈."

---

## 🔥 5 Follow-ups

**Q1: LLM system 和普通 micro-service 设计区别最大的是什么?**
5 个属性: (1) 30s 请求 vs 100ms (2) $0.001-$1/req 而非 negligible (3) non-deterministic output (4) 1 req → N downstream (LLM + tool + RAG) (5) state 5 种 (session / user / workflow / model checkpoint / LoRA). Cost 是 first-class concern, 不是 nice-to-have.

**Q2: Cost 怎么从 $5/1M token 降到 $0.5/1M?**
4-layer stack 累积: (1) Semantic cache 40% hit → 40% off; (2) Cost-aware routing 70% Flash $0.50 + 25% Pro + 5% Opus → blended $0.85; (3) Prefix cache via vLLM/Anthropic 90% off cached input; (4) Self-host Llama-70B FP8 90% 流量 → $0.30/1M. 综合 8-12x reduction, 同 eval quality.

**Q3: Observability 4 layer 缺哪个最致命?**
缺 L4 quality eval. 传统 metric (latency/error) 全绿但用户感受变差 = 静默 quality drift. 5% LLM-as-judge sample + drift detect 是唯一能抓的. 缺这个就是盲飞.

**Q4: 5+ step agent workflow 怎么保 consistency?**
不能用 2PC (vendor 不支持 + network partition). 走 Saga + Outbox + idempotency key per step + verify-on-timeout. > 5 步必上 Temporal / DBOS, 不要手写. Compensation handler 上线前 chaos test (random kill mid-workflow).

**Q5: 一句话总结 T3 staff-level mental model?**
"LLM 服务表面 stateless, 内部 hybrid stateful (4-tier cache). MCP 抽象 tool, OBO 限权限. 6-lever vLLM 叠 50x throughput. 4-layer observability 抓 quality drift. 5-layer cost defense 降 10x. Saga + Temporal 保 multi-step consistency. Cost 是 first-class metric."

---

## ❌ 易错点 (10 条红线)

1. 把 LLM service 当普通 web service 设计 (用 DDIA 那套答) — 立失分
2. 不提 cost — FDE 死穴, cost 是 LLM platform 核心
3. "Use exactly-once delivery" — 分布式不存在, 暴露不懂 distributed system
4. 不提 eval drift / quality monitoring — LLM 静默退化无人知
5. 不能 ID Temporal / vLLM / MCP / LangSmith by name — 暴露没做过 prod
6. Cache 不分 exact / semantic / prefix 三种 — 漏 30-50% 节省机会
7. Single vendor lock-in — vendor 429 / outage 全瘫
8. State 设计只考虑 session — 忘了 user state / workflow state / model checkpoint
9. 答 "我会加 retry" 但没说 idempotency key — 双扣灾难
10. 不讲 multi-tenant 隔离 — gold tenant 被 bronze 拖死

---

## ✅ 加分项 (13 条)

1. **5 个独特属性** 开场 (latency / cost / determinism / fanout / failure)
2. **2026 模型 pricing 精确** (Flash $0.50/$3, Pro $2/$12, Opus 4.7 $5/$25, Sonnet 4.6 $3/$15)
3. **6-lever throughput stack** (vLLM + spec decode + FP8 + prefix cache 数字背熟)
4. **4-layer observability** 命名 (OTel + LangSmith + Prom + eval-in-prod)
5. **5-layer cost defense** 累积 8-12x reduction 数字
6. **Saga + Temporal + DBOS** 按场景选
7. **MCP 3 原语** (Resources / Tools / Prompts) 区分 OpenAI function call
8. **OBO** (RFC 8693 OAuth token exchange) 提名
9. **Per-tenant** isolation (priority queue + Redis Lua semaphore + dedicated replica)
10. **Chaos engineering** (Chaos Mesh / Litmus, weekly random node kill)
11. **Cost math 出口** (blended $0.85/1M 6x vs all-Opus story)
12. **简历 hook**: voice agent stateful + BNPL stateless + Internal Agent Platform + Indonesia refund Saga
13. **45-min 节奏自我提示** (clarify 5min → mental model 5 → deep-dive 15 → tradeoff 10 → failure 7 → resume 3)

---

## 一句话总结

T3 = **LLM 系统 5 独特属性 → 6 sub-topic + 6-lever throughput + 4-layer observability + 5-layer cost defense + Saga 共识**. Cost 永远是 first-class. 不答 cost, 不提 vLLM/Temporal/MCP by name, 不讲 eval drift — 三大死穴.

---

## 🃏 Cheat Sheet (印 1 页随身)

```
T3 LLM System Design 全景:

5 独特属性 (vs web service):
  Latency 30s / cost $0.001-1 / non-determ /
  N downstream / 5 state types

6 sub-topics:
  T3.1 Stateless vs Stateful (default API stateless + hybrid)
  T3.2 MCP / API Proxy (3 primitives + 6 responsibilities)
  T3.3 High throughput (6 levers, 50-100x naive)
  T3.4 Observability (4 layers, OTel+LangSmith)
  T3.5 Rate/Queue/Cache (5 layers, 6-10x cost)
  T3.6 Eventual consist (Saga+Outbox+Temporal)

5 patterns:
  A. Stateless API + client conv_id
  B. Stateful WebSocket (voice <500ms)
  C. Cost-aware routing 90/9/1
  D. Saga / Outbox multi-step
  E. 4-layer observability

6 throughput levers (mult):
  Cont batch 5-10x / PagedAttn 24x concurrent
  Prefix cache 2-3x / Spec decode 2-3x latency
  TP 70B+ enable / FP8 quant 1.5-2x
  Combined: 50-100x naive

4-layer observability:
  L1 OTel trace + Jaeger/Tempo/Honeycomb
  L2 LangSmith/Phoenix prompt+completion
  L3 Prometheus per-user/feature cost
  L4 LLM-judge eval 5% + drift

5-layer cost defense:
  L1 Cache (exact+semantic+prefix) 40% off
  L2 Queue (priority by tier)
  L3 Rate limit (token bucket multi-dim)
  L4 Cost routing (Flash 90/Pro 9/Opus 1)
  L5 Budget cap (per-tenant monthly)
  Combined: 8-12x total

3 consistency patterns:
  Saga (2-3 step + compensation)
  Outbox (cross-service no framework)
  Temporal / DBOS ⭐ (5+ step long-run)

2026 pricing (memorize):
  Gemini 3 Flash $0.50/$3 (cache $0.10)
  Gemini 3 Pro   $2/$12 (cache $0.40)
  Haiku 4.5      $1/$5 (cache $0.10)
  Sonnet 4.6     $3/$15 (cache $0.30)
  Opus 4.7       $5/$25 (cache $0.50)
  GPT-5.5        $5/$30 (cache $1)
  Self-host 70B  ~$0.30 all

Blended (70/25/5): ~$0.85/1M
With cache 40%: ~$0.5/1M → 10x savings

Top gotchas:
  Cost runaway loop / timeout propagation /
  Provider 429 / KV cache thrash /
  PII in prompt / cache poisoning /
  Tenant breach / eval drift / streaming interrupt /
  Provider deprecation

45-min rhythm:
  0-5 Clarify (QPS/SLA/budget/multi-tenant)
  5-10 Mental model + arch image
  10-25 Deep-dive 1 sub-topic
  25-35 Tradeoffs + cost math
  35-42 Failure modes
  42-45 Resume quote

红线 (interview kill):
  - LLM = web service
  - 不提 cost
  - exactly-once delivery
  - 不提 eval drift
  - 不识 Temporal/vLLM/MCP/LangSmith
```
