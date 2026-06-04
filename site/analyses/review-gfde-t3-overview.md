## T3 · LLM System Design 全景 — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](gfde-t3-overview.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t3-overview.html`](gfde-t3-overview.html)

---
## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"design a production-grade LLM application for a Fortune 500 customer"** (T3 open-ended 总入口题), 我按这 8 层回答, 不跳序.

### 📐 LLM System Design — 8 层结构 (T3 总入口)

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 |
|---|---|---|---|---|
| 1 | 5 独特属性破题 | 1 min | LLM ≠ traditional web service — 30s/req, $0.01-1/req, non-deterministic, 1 req → N downstream, cost first-class. 直接否定面试官内心默认的 DDIA 套路 | "Before I dive in, LLM systems break 5 assumptions of traditional web service design..." |
| 2 | Clarify 7 问 | 2 min | QPS / p99 SLA / cost budget per query / single vs multi-region / multi-tenant / self-host vs hosted / compliance (HIPAA / SOC2 / data residency) / PII | "Let me pin down the constraint envelope — what's the QPS, p99 SLA, and cost per query?" |
| 3 | Arch ASCII + 6 sub-topic 地图 | 4 min | 画 Edge → Gateway → App layer (stateless) → 4 lateral (Cache / Queue / Rate / Tool Reg) → Provider 层. 然后 map 到 6 sub-topic | "Here's the high-level box diagram, and 6 sub-systems each map to a specific design concern..." |
| 4 | 选 1 个 sub-topic deep-dive | 6 min | 让面试官选 zoom-in, 你 follow up. 默认 fallback = T3.3 high throughput (强项区) | "Which sub-system do you want me to drill into first? — I'd default to throughput since the QPS target is non-trivial" |
| 5 | 6 throughput levers 数学 | 5 min | HF baseline 5-10 QPS/A100 → vLLM continuous batch 5x → PagedAttn 10x → prefix cache 20x → spec dec 40x → FP8 60x → multi-LoRA 33x | "The throughput story is multiplicative — 6 levers compound from baseline 1x to 50-60x..." |
| 6 | 4-layer cost defense 数学 | 4 min | All-Opus $5/1M → cache 40% hit → 70/25/5 routing → blended $0.85/1M → 加 cache → $0.50/1M = **10x reduction** | "Cost is the first-class concern — without 4-layer defense, blended cost is $5/1M, with it $0.5/1M, 10x" |
| 7 | 4-layer observability + eval drift | 3 min | L1 OTel trace + L2 LangSmith prompt log + L3 cost per (user/feature/model) + L4 sampled eval-in-prod LLM-judge | "Observability is 4 layers, not RED — eval-in-prod is the LLM-specific 4th layer most teams forget" |
| 8 | 简历 hook 7 个 quote | 2 min | Voice agent stateful / BNPL stateless / Internal Agent Platform MCP / vLLM SGLang DeepSpeed / Indonesia refund Temporal / TikTok PayLater 5k QPS / ConvFinQA eval | "These 6 sub-topics each map to a project on my resume — pick the one you want detail on" |

### 🎯 为啥按这个序

5 独特属性破题强制面试官切换思维框架 (避免他用 DDIA 评分). Clarify 早做出来才能让后续 number 有锚 (没 QPS 就没 GPU 数算法). Arch 图是 "lateral pass" — 不深但 cover 全 6 sub-topic, 给面试官选 deep-dive 入口. 6 throughput + 4 cost + 4 obs 是 3 个最高质量 framework, 任选一个进去都能撑 10-15 min. 简历 hook 留最后, 主动 quote 比被动问出来分高.

### 🔥 哪一层最容易被追问 deeper

**Layer 5 (throughput levers)** — 面试官最爱问 "why is PagedAttention 24x?" 或 "spec decoding accept rate 怎么调". 必须能讲 KV cache pagination 机制 (像 OS page table, block size 16 token) + speculative draft model 大小关系 (0.5B / 7B base, 70% accept sweet spot). **Layer 7 (eval-in-prod)** 次之, 因为多数人不知道 LLM-as-judge 怎么 calibrate (5% sample + 周度人工 100 条对齐 + MMD drift test).

### ⏱ 时间压缩版 (30 min round)

1. 5 独特属性 (30s) + clarify 5 问 (90s)
2. Arch + 6 sub-topic 一句话 (3 min)
3. Throughput 6 levers 数学 + cost 4-layer 数学 (8 min)
4. Observability 4 层 + eval drift (4 min)
5. 3 个 gotcha (cost runaway / timeout propagate / eval drift, 3 min)
6. 简历 quote 2 个 (vLLM/SGLang + TikTok PayLater 5k QPS, 2 min)

### 🆘 卡壳兜底 (针对这题)

1. **被问 "design a chatbot"**: 立刻 reframe → "before I design UI, let me clarify the system scale — is this 10 user demo or 100K MAU?" 把题拉回 T3 distributed system 层
2. **被问 cost math 数字记不住**: 锚 "Opus 4.7 是 $5/$25, Flash 是 $0.50/$3" 这 2 个最常用, 其他临场算
3. **被问 specific tool 不熟**: "我没在 prod 用过 X, 但用过 Y (vLLM/SGLang) — 同类问题我会这样解" — 别假装熟
4. **被问 system 比较时**: 永远先讲 trade-off 维度 (cost / latency / consistency / dev velocity / vendor lock-in), 再 plot 各方案在维度上的位置

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页 6 个 sub-topic / 4 个框架 / 全部 production gotcha. 比 Section 13 稠 3-4x, 是面试前一晚的 last-look 版本.

### 🧠 核心心智模型 (1 sentence)

LLM system 是「30s/req + $0.01-1/req + 非确定输出 + 1 req → N downstream + cost 是 first-class」的特殊分布式系统, 必须把 distributed-system / SRE / cost-optimization / eval / MLOps 五种思维同时叠加才能 design pass.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Stateless | Server 不存 session, client 带 conv_id 每次 rebuild | 默认 95% LLM 场景 |
| Stateful (sticky) | Server 持 KV cache + WebSocket, pod 死则丢 | voice / 强延迟 |
| MCP | Anthropic 2024 开源 JSON-RPC tool 协议 (Resources/Tools/Prompts) | 2026 enterprise default |
| API Proxy / Gateway | Auth + rate + observ + cache + version 的统一入口 | self-host LLM serving |
| Continuous batching | Token 级动态拼批 (vLLM) | high throughput baseline |
| PagedAttention | KV cache 按 page 切, 像 OS 页表, 24x concurrency | self-host serving |
| Prefix cache | Shared system prompt 算 1 次 (Anthropic 90% off) | 多 user 同 system prompt |
| Speculative decoding | Draft 小模型 + verify 大模型, 2-3x latency↓ | 单 query 延迟优化 |
| Saga | Forward + per-step compensate, 反向 undo | 短 (< 5 步) workflow |
| Outbox | Intent table + 独立 worker, at-least-once | 跨服务 + no framework |
| Workflow engine | Temporal / DBOS / Inngest 持久化 workflow as code | 5+ 步 / 长时 / 多 agent |
| Eval drift | Prompt/model 升级后质量悄悄掉 | 必装 pre-deploy gate |
| Semantic cache | Embedding 相似度 → 命中 cached response | FAQ-style 30-50% hit |
| Cost-aware routing | Flash/Pro/Opus 按 complexity 路由 | 6x 成本降 |
| OBO (On-Behalf-Of) | Agent token = user token 子集, scope ≤ user | enterprise IAM |

### 🎯 6 个 sub-topic + 4 个深度框架 (overview 视角)

**Sub-topic 1: Stateless vs Stateful**
- When: 多轮对话 / session / failover
- Algorithm: 默认 stateless + Redis blob + client conv_id; voice 例外 stateful WebSocket
- Trade-off: stateless infinite scale + 30 wire重传 vs stateful TTFT 280ms + sticky failure
- Tools: Redis Cluster, DragonFly, sticky LB (Envoy hash), vLLM prefix cache

**Sub-topic 2: MCP / API Proxy**
- When: 50+ internal tools / multi-LLM vendor / customer ecosystem
- Algorithm: MCP gateway (Resources + Tools + Prompts) + RAG tool discovery + OBO auth
- Trade-off: MCP overhead 10-50ms vs vendor lock-in
- Tools: Anthropic MCP SDK, Kong, Envoy, OAuth token exchange (RFC 8693)

**Sub-topic 3: High Throughput (6 levers)**
- When: 1k+ QPS / GPU cost optimization / self-host
- Algorithm: Continuous batch × PagedAttn × Prefix cache × Spec dec × TP × Quant
- Trade-off: 50-60x baseline 但 setup 复杂; quality eval gate 必须
- Tools: **vLLM 0.6+**, **SGLang RadixAttention**, TensorRT-LLM, Megatron-LM, DeepSpeed-MII, FP8 (H100), AWQ INT4

**Sub-topic 4: Observability (4 layers)**
- When: 任何 production LLM, 必装
- Algorithm: L1 OTel trace, L2 LLM trace (LangSmith), L3 cost track, L4 eval-in-prod
- Trade-off: 100% sample $$$$$, tail-based sample 1% baseline + 100% slow/error
- Tools: OpenTelemetry, Honeycomb, Datadog, Tempo, LangSmith, Phoenix, Helicone, Langfuse, Braintrust, Presidio (PII)

**Sub-topic 5: Rate Limit / Queue / Cache (4-layer cost defense)**
- When: 100K+ QPS / multi-tenant / cost runaway risk
- Algorithm: cache → priority queue → token bucket rate → cost-aware route
- Trade-off: 8-12x cost ↓ blended, 但 cache wrong-hit 是 silent kill
- Tools: Redis Lua atomic, Vertex AI Vector Search semantic cache (0.95-0.97 threshold), Envoy rate limit, LiteLLM router

**Sub-topic 6: Eventual Consistency (3 patterns)**
- When: agent multi-step 跨 vendor 副作用
- Algorithm: Saga (< 5 步), Outbox (cross-service no framework), Workflow engine (5+ 步)
- Trade-off: Temporal lock-in vs handroll bug-prone
- Tools: **Temporal**, **DBOS**, Inngest, Kafka outbox, Postgres SELECT FOR UPDATE SKIP LOCKED, Stripe Idempotency-Key

### 🌳 关键决策树 (ASCII)

```
Stateful or Stateless?
  ├─ Latency < 500ms 必需? ── yes ── Stateful WebSocket (voice)
  └─ no
      ├─ Multi-region failover < 1s? ── yes ── Stateless + Redis hybrid
      └─ no ── Stateless (default), 95% 场景

High-throughput stack?
  ├─ Self-host? ── yes
  │   ├─ < 8B params ── vLLM single GPU FP8
  │   ├─ 70B params ── vLLM TP=8 single node FP8
  │   └─ > 200B ── TP=8 + PP cross-node + EP for MoE
  └─ Hosted API ── multi-vendor router (LiteLLM) + prompt cache

Consistency pattern?
  ├─ < 3 steps + all reversible ── Saga DIY
  ├─ Cross-service no framework ── Outbox + Kafka
  └─ 5+ steps / long-running / audit ── Temporal ⭐
```

### ⚙️ 4 框架速查 (overview 简化 5-Problem)

**Framework 1: 6 Throughput Levers**
```
HF Transformers baseline                   1x  (5-10 QPS/A100)
+ Continuous batching     (vLLM)            5x
+ PagedAttention          (vLLM)           10x  (24x concurrency)
+ Prefix caching          (vLLM)           20x
+ Speculative decoding    (vLLM eagle)     40x  (70% accept)
+ FP8 quantization        (H100)           60x  (< 0.5% drop)
+ Multi-LoRA              (S-LoRA)         33x cheaper vs replicas
TP=8 needed when model > 80GB FP8
```

**Framework 2: 4-Layer Observability**
- L1 OTel trace: span.attr llm.model, input_tokens, cost_usd, prompt_template_version
- L2 LLM logs: prompt + completion (PII-redacted), tool calls, eval scores
- L3 Cost: per-(user,feature,model)/day; daily/monthly tenant report
- L4 Eval: 5% sample LLM-judge + force-flag, drift MMD test daily
- Sampling: 1% baseline + 100% error/slow/expensive/VIP/jailbreak

**Framework 3: 4-Layer Cost Defense**
| Layer | Saving | Mechanism |
|---|---|---|
| L1 Cache (exact + semantic + prefix) | 30-50% | Vertex AI Vector Search 0.95 + vLLM block share |
| L2 Queue (priority/tenant) | 0% (SLA保) | Redis sorted set, gold = score×1e10 |
| L3 Rate limit | 0% (防滥用) | Token bucket per user/tenant/model |
| L4 Cost-aware routing | 5-6x | 70% Flash + 25% Pro + 5% Opus |
| Combined | **8-12x** | $5/1M → $0.5-0.85/1M blended |

**Framework 4: 3 Consistency Patterns**
| Pattern | When | Code skeleton |
|---|---|---|
| Saga | < 5 步 + clear undo | try forward; except: reverse compensate |
| Outbox | cross-service | tx { biz + outbox.insert }; worker poll FOR UPDATE SKIP LOCKED |
| Workflow ⭐ | 5+ / long / audit | @workflow.defn + execute_activity retry_policy |

### 🔥 Production gotchas (top 15)

1. **Cost runaway**: Agent infinite self-call → per-session cap $1 + max 10 iter + auto-stop
2. **Timeout propagation**: 30s outer < 25s LLM call → deadline header passed downstream
3. **Provider 429**: OpenAI burst limit → multi-provider failover (OpenAI → Anthropic → self-host vLLM)
4. **KV cache thrash**: 每 req new conv → 0 prefix hit → 必须 stable system prompt + sticky route
5. **Streaming interrupt**: client 断连 → resumable token anchor or full retry idempotent
6. **Log explosion**: 100K QPS × full prompt = TB/day → sample + redact + tier storage
7. **PII in prompt**: 用户粘信用卡 → Presidio NER redact before LLM call + log
8. **Cache poisoning**: 1 bad response 服万人 → eval-gated cache write + invalidate API
9. **Tenant isolation**: tenant A 的 cache hit tenant B → per-tenant namespace + RLS
10. **Eval drift**: prompt 改 12% faithfulness 掉 → pre-deploy eval gate + 7-day MMD
11. **Provider deprecation**: gpt-4 EOL → multi-model eval + abstract via gateway
12. **Workflow stuck**: 等 human forever → time-bound waits + escalation
13. **Cost dashboard 错**: 忘算 cached input → 用 provider response.usage 不是 estimate
14. **Spec decoding accept < 50%**: 关掉, overhead > 收益
15. **TP > node**: 跨 node 通信 kill perf, 70B FP8 single-node 8×H100 sweet spot

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Stateless vs Stateful | Voice agent (stateful) + BNPL (stateless) | "Voice WebSocket TTFT 280ms; BNPL REST + Redis blob 任意 pod" |
| MCP / API Proxy | Internal Agent Platform | "50+ tool MCP gateway, OBO + RAG discovery 92% accuracy" |
| High Throughput | **vLLM/SGLang/DeepSpeed** | "vLLM 0.6 TP=8 FP8, A100 8 → 150 QPS, 18x baseline; SGLang RadixAttn multi-turn 20-30% extra" |
| Observability | Voice agent 7 markets weekly | "LangSmith catch Indonesian prompt faithfulness drop 12% pre-rollback" |
| Rate / Queue / Cache | TikTok PayLater 5k QPS peak | "Semantic 35% hit + priority queue + 70/25/5 route → $0.85/1M (vs $5)" |
| Eventual Consistency | Indonesia refund tier | "Temporal 5-step Saga, 156K refunds 0 double-refund, 1.9% verify-on-timeout" |
| ConvFinQA | Financial QA evaluation | "Custom eval harness, faithfulness ≥ 0.85 gate before deploy" |

### 🎤 面试现场 quotables (top 8)

1. "LLM system 5 个独特属性改变所有 tradeoff — 30s req / $1 req / 非确定 / N downstream / cost first-class"
2. "Throughput stack: 6 levers compound, vLLM PagedAttention + continuous batching 是 50x baseline 的起点"
3. "Cost defense 4 层叠 8-12x, 单 layer 都打不到目标"
4. "Saga 简单 + Outbox 跨服务 + Workflow Engine (Temporal) 复杂, 别 reinvent"
5. "Eval 是 LLM 的 unit test, 没有 eval gate 就是 prompt-by-vibes"
6. "Anthropic prompt caching 90% off, 把 system prompt 放最前面是新经济学"
7. "TP within node, DP across node — 70B FP8 单节点 8×H100 是 sweet spot"
8. "MCP 不是 function calling, 是 vendor-neutral 协议 + Resources/Tools/Prompts 三原语"

### 🚨 红线 (top 10 anti-patterns)

1. 当 LLM service 普通 web service 答 (lose immediate)
2. 不提 cost / blended pricing (FDE 死穴)
3. "Use exactly-once delivery" (不存在)
4. 不提 eval drift / quality monitoring
5. 不能 ID Temporal / vLLM / SGLang / MCP / LangSmith by name
6. Static padding / pre-allocate max KV (浪费 GPU 90%)
7. Cache without eval gate (poisoning 服万人)
8. 没有 OBO, agent ≥ user 权限 (enterprise 红线)
9. 全 100% trace sampling (TB/day, cost ↑↑)
10. 单 vendor 单 model 路由 (cost 5-10x + 单点)

### 📊 2026 Pricing 全表 (背下来, 临场算 cost math)

| Model | Input $/1M | Output $/1M | Cached Input $/1M | Best for |
|---|---|---|---|---|
| Gemini 3 Flash | 0.50 | 3 | 0.10 | 70% 简单 query, FAQ |
| Gemini 3 Pro | 2 | 12 | 0.40 | 25% 中等复杂 |
| Claude Haiku 4.5 | 1 | 5 | 0.10 | 极速 + 便宜 |
| Claude Sonnet 4.6 | 3 | 15 | 0.30 | 中端 reasoning |
| Claude Opus 4.7 | 5 | 25 | 0.50 | 5% 高复杂 / VIP |
| GPT-5.5 | 5 | 30 | 1 | 高复杂 alt |
| Self-host Llama 70B (vLLM TP=8 H100) | ~0.30 blended | ~0.30 | n/a | 高量 / 强合规 |

**典型 routing**: 70/25/5 (Flash/Pro/Opus) → blended $0.85/1M (vs $5/1M all Opus = 6x). + 40% prefix cache hit (Anthropic 90% off) → $0.50/1M (10x).

### 🎬 45-min 节奏 quick reference

```
0-5    Clarify    QPS? p99 SLA? Cost budget $/req? Single/multi region? Multi-tenant? 自host/hosted? Eval要求? Compliance (HIPAA/SOC2)? Data residency? PII?
5-10   Mental     "LLM ≠ web service, 5 properties"; draw Section 2 ASCII
10-25  Deep-dive  面试官选 1 sub-topic, 你按 Pattern + Framework 展开
25-35  Tradeoff   Cost math, blended pricing, throughput levers compound
35-42  Failure    至少 3 个 gotcha: cost runaway / timeout propagate / eval drift
42-45  Resume     "On voice agent / BNPL / Indonesia refund / Internal Agent Platform"
```

### 🧰 2026 工具生态 quick lookup

| 类别 | 默认选择 | Alt | 你简历用过 |
|---|---|---|---|
| Inference engine | vLLM 0.6+ | SGLang, TensorRT-LLM | ✅ vLLM, SGLang |
| Training framework | Megatron-LM + DeepSpeed | FSDP, Colossal-AI | ✅ DeepSpeed |
| LLM proxy router | LiteLLM | OpenRouter, Portkey | 自建 |
| Workflow engine | Temporal | DBOS, Inngest | ✅ Temporal |
| Observability (trace) | OpenTelemetry → Honeycomb/Datadog | Tempo, Jaeger | ✅ OTel |
| LLM-specific obs | LangSmith | Phoenix, Helicone, Langfuse, Braintrust | ✅ LangSmith |
| Vector DB | Vertex AI Vector Search | Vertex AI Vector Search, Milvus, Weaviate | ✅ Vertex AI Vector Search |
| Cache | Redis Cluster | DragonFly, KeyDB | ✅ Redis |
| Queue | Kafka | NATS, RabbitMQ | ✅ Kafka |
| Service mesh | Envoy | Istio, Linkerd | ✅ Envoy |
| PII redaction | Microsoft Presidio | AWS Macie | ✅ Presidio |
| Eval suite | Braintrust | OpenAI Evals, Anthropic Evals | 自建 |

### 🔢 关键 production 数字 (记下来)

- HF Transformers baseline: 5-10 QPS / A100 (8B)
- vLLM full stack: 200-600 QPS / A100 (8B) — 50-60x baseline
- TTFT target: voice 280ms / chat 800ms / batch 2-5s
- Semantic cache hit rate: FAQ 30-50% / general chatbot 15-25%
- Prefix cache (vLLM with conv_id hint + sticky): 80-85%
- Anthropic prompt cache discount: 90% off cached input (1h TTL)
- Spec decoding accept rate sweet spot: 70-80%
- FP8 quality drop: < 0.5% (sweet spot 2026)
- INT4 (AWQ) quality drop: 2-5% (consumer chatbot OK, legal/medical 不行)
- 70B FP8: TP=8 single node 8×H100 80GB sweet spot
- Indonesia refund: 156K processed, 1.9% verify-on-timeout, 0 double-refund

### 🧠 mental model anchors (背一句话)

- Stateless: 默认 95% 场景, client conv_id, Redis blob, infinite scale
- Stateful: voice / 强延迟 only, sticky WebSocket, < 1s failover require 3x cost
- MCP: vendor-neutral, 3 原语 (Resources/Tools/Prompts), JSON-RPC over stdio/HTTP/SSE/WS
- Throughput: 6 levers compound, vLLM 是 50-60x baseline 起点
- Observability: 4 layer (trace/log/metric/eval), tail-based sample, PII redact at write
- Cost defense: 4 layer (cache/queue/rate/route), 8-12x blended save
- Consistency: Saga 短 / Outbox 跨服务 / Temporal 长 — 别 reinvent

### 🎤 1-liner go-to phrases (背 5 句, 任何 T3 题都能 anchor)

1. "LLM system 5 个独特属性: 30s req, $1 req, 非确定, 1 req → N downstream, cost first-class"
2. "Throughput 6 levers compound: vLLM PagedAttn + continuous batch + prefix cache + spec dec + TP + FP8"
3. "Cost defense 4-layer = 8-12x ↓: cache + queue + rate + cost-aware routing"
4. "Eventual via Saga short / Outbox cross-service / Temporal 5+ steps — 别 reinvent"
5. "Eval-in-prod is the LLM-specific 4th obs layer; without it = prompt-by-vibes"

### 📌 Cross-reference 索引

| 题问 | 主页 | 关联页 |
|---|---|---|
| "How to handle multi-turn?" | T3.1 stateless-stateful | T3.3 (KV cache), T3.5 (cache) |
| "How to add a new tool?" | T3.2 MCP | T3.4 (trace propagate) |
| "Voice agent latency optim" | T3.3 high-throughput | T3.1 (sticky), T3.4 (TTFT metric) |
| "Cost spike alert" | T3.4 observability | T3.5 (budget cap) |
| "Agent self-loop infinite cost" | T3.5 rate-limit | T3.6 (workflow stop) |
| "Refund step fails mid-way" | T3.6 eventual consistency | T3.4 (audit trail) |
