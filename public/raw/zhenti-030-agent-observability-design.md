## Q30 · Agent 系统可观测性 — 记录什么, 告警什么, 看板

> "You're running a production multi-step **AI agent** (LLM + tools + RAG + multi-turn). Customer reports 'sometimes the agent gives wrong answer or hangs'. **Design the observability**: what to log, what to alert on, what dashboards to build. Cover **traces, metrics, logs, evals, costs**."

**Round**: System Design (60 min)
**出处**: Exponent 2026 FDE · 公司: Anthropic / OpenAI / Sierra / Glean / LangChain · 行业: AI infra / agent platform
**约束**: multi-step agent with tool calls / multi-tenant / PII redaction / cost tracking / debugging stuck or wrong runs / SLO tracking / per-customer view

---

## 📖 术语速查 (本题用到的)

> 这题是 agent 生产可观测性集大成. 名词不懂 dashboard / alert / eval 都搭不起来. 5 min 看完.

### 5 Pillars / 整体框架

| 术语 | 解释 |
|---|---|
| **Observability** ⭐ | 可观测性 — 通过外部输出推测系统内部状态. |
| **Traces / Metrics / Logs** | 传统 3 pillars. |
| **Evals / Costs** ⭐ | Agent 时代新增 2 pillar — 质量 + 成本. |
| **Telemetry** | 遥测数据 — traces / metrics / logs 统称. |
| **OpenTelemetry (OTel)** ⭐ | 跨厂商可观测性标准, CNCF 项目. |
| **OTLP** | OTel 的传输协议. |
| **OTel Collector** | 中间转发层 — 接收 + 处理 + 路由 telemetry. |
| **GenAI semantic conventions** ⭐ | 2026 OTel 给 LLM 的标准属性 (gen_ai.request.model 等). |

### Traces / Spans (核心)

| 术语 | 解释 |
|---|---|
| **Trace** ⭐ | 一次请求的完整轨迹 — 由多个 span 组成. |
| **Span** ⭐ | 一个操作单元 (一次 LLM call / 一次 tool call). |
| **Root span** | trace 的最外层 span (agent.run). |
| **Span hierarchy** | span 的父子关系树. |
| **Span attributes** | span 上挂的 key/value (model name / cost / latency). |
| **Trace context (W3C TraceContext)** | 跨 service 传 trace_id 的标准 — `traceparent` header. |
| **trace_id / span_id** | 链路 / 操作的唯一 ID. |
| **Trace waterfall** | trace 可视化 — span 按时间排列的瀑布图. |
| **Tempo / Datadog APM / Jaeger** | 3 大 trace backend. |
| **LangSmith** ⭐ | LangChain 出的 LLM-native trace + eval 平台. |
| **Helicone** | OpenAI proxy 加可观测性. |

### Sampling (采样)

| 术语 | 解释 |
|---|---|
| **Sampling rate** | 采样率 — 1% 表示 1/100 trace 留下. |
| **Head sampling** | 头部采样 — trace 开始时决定保留. 随机 1%. |
| **Tail sampling** ⭐ | 尾部采样 — 看完整 trace 后决定 (错误 / 慢 / 贵 100% 保留, 其余 1%). |
| **Tier-1 / tier-2 / tier-3** | 重要级 — tier-1 100% 采样, tier-3 1%. |

### Metrics 方法论

| 术语 | 解释 |
|---|---|
| **RED method** ⭐ | Rate / Errors / Duration — 服务级三件套. |
| **USE method** ⭐ | Utilization / Saturation / Errors — 基础设施级. |
| **Cardinality** | 维度基数 — per-tenant × per-flow × per-model 组合. 太高 metric 系统爆. |
| **Pre-aggregation** | 预聚合 — 1min 桶降低 cardinality. |
| **Prometheus / Grafana** | 开源 metrics + 可视化. |
| **Datadog metrics** | Datadog 的 metrics SaaS. |

### SLO / 告警

| 术语 | 解释 |
|---|---|
| **SLO (Service Level Objective)** ⭐ | 服务水平目标 — 99.5% availability. |
| **SLI (Service Level Indicator)** | 衡量 SLO 的具体指标 (成功率). |
| **SLA (Service Level Agreement)** | 对客户的合同承诺, 通常宽于 SLO. |
| **Error budget** ⭐ | 错误预算 — 99.5% = 月内允许 36h downtime. |
| **MTTD (Mean Time To Detect)** ⭐ | 故障平均发现时间. |
| **MTTR (Mean Time To Recover)** | 平均恢复时间. |
| **PagerDuty / Slack alert** | 告警通道. |
| **Alert fatigue** | 告警疲劳 — 假阳过多 on-call 麻木. |
| **Compound conditions** | 复合条件 — 多个 metric 同时超阈才告警, 减少误报. |
| **Anomaly detection (EWMA / z-score)** | 异常检测 — 不用固定阈值. |

### Agent 特有指标

| 术语 | 解释 |
|---|---|
| **Stuck detection** ⭐ | 卡住检测 — agent 长时间无 span emit 视为 hang. |
| **Tool selection drift** ⭐ | 工具选择漂移 — agent 用工具的分布随时间变化. PSI > 0.2 告警. |
| **Hallucination rate** ⭐ | 幻觉率 — agent 答案无 source 依据的比例. |
| **NLI (Natural Language Inference)** | 蕴含判断 — 证据是否蕴含 claim. |
| **Tool error rate** | 每个 tool 失败率, 识别 flaky integration. |
| **LLM refusal rate** | LLM 拒绝回答率 — safety filter trigger. |
| **Tokens per run** | 每 run 用的 token 数, runaway 信号. |
| **Loop bug** | agent 死循环 bug — tool_calls 无界增长. |

### Eval (生产环境)

| 术语 | 解释 |
|---|---|
| **In-loop eval** ⭐ | 在生产中持续 eval, 不只 offline. |
| **LLM-as-judge** ⭐ | 用 LLM 当 judge 评 quality. |
| **Synthetic eval / Golden replay** | 定期跑 golden set 跟踪 quality. |
| **Active learning queue** | 低 confidence 样本进人工标注. |
| **Citation check** | 引用检查 — 答案声明能否定位到 source span. |
| **NLI threshold** | NLI 阈值 (0.7 / 0.85). |
| **Hourly batch eval** | 每小时批量 eval 已 log 的 run. |

### Logs / PII

| 术语 | 解释 |
|---|---|
| **Structured JSON logging** ⭐ | 结构化日志 — key/value JSON, 可 query. |
| **Loki / ELK / Splunk** | 3 大 log backend. |
| **PII redact** ⭐ | PII 脱敏 — 在 OTel collector 阶段处理. |
| **Presidio** | Microsoft 开源的 PII 检测库. |
| **Log levels** | DEBUG / INFO / WARN / ERROR. |
| **Hot / Cold / Archive retention** | 3 层保留: 14-30d hot / 90d cold / 7yr archive. |
| **Debug vault** | 受限的原始数据存储, 仅 break-glass 访问. |
| **Break-glass access** | 紧急访问 — manager 审批 + 时间窗 + audit. |

### Cost Tracking

| 术语 | 解释 |
|---|---|
| **Per-request cost breakdown** ⭐ | 每次请求成本拆分 — LLM in/out + embedding + tool + storage. |
| **Per-tenant budget** | 每客户月预算. |
| **Runaway cost** ⭐ | 失控成本 — agent 死循环 / prompt 长 50% 时月底破产. |
| **Cost burn rate** | 成本烧速 ($/hour). |
| **Hard stop vs Soft throttle** | 超预算硬停 vs 软限速. |
| **Cost anomaly** | 成本异常 — 单 request p95 > 2× baseline. |
| **Margin** | 利润率 — 成本 vs 收入. |

### Agent 框架

| 术语 | 解释 |
|---|---|
| **LangGraph** | LangChain 的 stateful agent 框架. |
| **AutoGen** | Microsoft 的 multi-agent 框架. |
| **Plan-act-reflect loop** | agent 标准 3 步循环. |
| **Tool calling / MCP** | LLM 调外部 function 的协议. |
| **Multi-step agent** | 多步 agent (不是单次 LLM call). |
| **Multi-turn** | 多轮对话 — agent 有 conversation history. |
| **Multi-tenant** | 多租户 — 服务多个 customer. |

### 部署 / 数据

| 术语 | 解释 |
|---|---|
| **Iceberg lake** | 数据湖表格式 — 用于 cold telemetry 存储. |
| **Snowflake** | 数据仓库 — cost dashboard 源数据. |
| **FINRA / SOC 2 / HIPAA** | 合规框架. |
| **RBAC** | 角色 / 行级访问控制. |
| **Sankey diagram** | 桑基图 — 显示 tool 调用顺序流. |
| **PSI (Population Stability Index)** | 分布漂移度量. |

---

## 这道题在考什么

不是考你 Datadog, 是考你**真正 debug 过 agent production incident 的人才会想到**:

1. **Trace per agent run** — OpenTelemetry span chain, 每 LLM call / tool call 一个 span
2. **PII redact at telemetry layer** — user query 含 PII, 不能直接 log
3. **Cost tracking per request** — token cost + tool API cost, breakdown
4. **Eval scoring on sampled runs** — LLM-as-judge in production loop
5. **Hallucination detection** — claim 是否有 source
6. **Tool selection distribution** — agent 是否过度 / 漏选某 tool
7. **Stuck detection** — agent run > p99 still running, alert
8. **Per-tenant view** — customer 想看自己 agent 表现
9. **菜鸟答案失败点**: "log everything to Datadog" — 没拆 trace/metric/log/eval, 没考虑 PII, 没考虑 agent 特有 signal.

---

## 必问 clarifying questions

1. **Agent shape**: single-step (LLM call) 还是 multi-step (plan-act-reflect loop)? 决定 trace granularity
2. **Tool count**: 5 还是 100? 决定 tool distribution dashboard
3. **PII tier**: zero PII tolerance (healthcare) vs OK with redaction?
4. **Multi-tenant view**: customer 想看自己 agent 表现 (Glean-like) 还是 only we (internal)?
5. **Cost budget**: per-request hard limit? per-tenant budget alarm?
6. **Eval frequency**: every run (expensive) vs sample 1%?
7. **Compliance**: SOC 2 / HIPAA / FINRA 要求 immutable audit?
8. **Existing stack**: Datadog / Splunk / Grafana / OpenTelemetry? 决定 integration

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|------|------|------|
| 1 | Clarify + 4 pillars | 5 min | Traces / Metrics / Logs / Evals + Costs | "Observability 不是 Datadog, 5 维度: trace, metric, log, eval, cost. Agent 加 PII 维度" |
| 2 | Trace per run | 10 min | OTel span hierarchy + agent-specific spans | "Per agent run = trace, every LLM call + tool call = span" |
| 3 | Metrics + SLO | 8 min | RED + USE + agent-specific (tool dist, hallucination) | "RED for service, USE for infra, plus agent-specific" |
| 4 | Logs + PII redact | 6 min | Structured + redact + retention tiers | "Structured JSON, redact PII at emit, 3-tier retention" |
| 5 | Eval in loop | 10 min | LLM-judge 1% + 关键 events 100% + human queue | "LLM-judge on 1% sampled, 100% on tier-1 events, human review escalate" |
| 6 | Cost tracking | 6 min | Per-request breakdown, per-tenant budget | "Cost as observability dimension, breakdown by token/tool/storage" |
| 7 | Dashboards + alerts | 8 min | Per-tenant, per-flow, per-model, on-call | "Dashboards 4 levels: fleet, tenant, flow, individual run" |
| 8 | Trade-offs + close | 7 min | Build vs LangSmith/Helicone, sampling | "OTel + LangSmith + Datadog hybrid stack" |

---

## 端到端架构图 (ASCII)

```
                                User request → Agent run begins
                                            │
                                            ▼
   ┌────────────────────────────────────────────────────────────────────────────────┐
   │  Agent Runtime (LangGraph / Autogen / custom)                                  │
   │   - assign trace_id (W3C TraceContext)                                         │
   │   - start agent_run span                                                       │
   │                                                                                │
   │  Each step emits OTel span:                                                    │
   │   ▸ agent.plan          (LLM call: planning)                                   │
   │   ▸ agent.tool_call.{N} (each tool invocation)                                 │
   │   ▸ agent.reflect       (self-check)                                           │
   │   ▸ agent.decide        (final response)                                       │
   │                                                                                │
   │  Per LLM call, span attributes:                                                │
   │   - model, temperature, prompt_version                                         │
   │   - tokens_in, tokens_out, cost_usd                                            │
   │   - latency_ms, ttft_ms                                                        │
   │   - prompt_hash (no raw prompt, just hash)                                     │
   │   - response_hash                                                              │
   │   - retrieved_chunks_count                                                     │
   │   - tools_listed_count                                                         │
   └────────────────────────────────┬───────────────────────────────────────────────┘
                                    │
                                    ▼
   ┌────────────────────────────────────────────────────────────────────────────────┐
   │  OTel Collector (in VPC)                                                       │
   │   - Receive OTLP traces, metrics, logs                                         │
   │   - PII redact processor (Presidio integration)                                │
   │   - Sample: 100% traces for tier-1 events, 10% for tier-2, 1% baseline         │
   │   - Routing:                                                                   │
   │     ▸ Traces → Tempo / Datadog APM                                             │
   │     ▸ Metrics → Prometheus / Datadog Metrics                                   │
   │     ▸ Logs → Loki / Datadog Logs                                               │
   │     ▸ Evals → LangSmith / custom store                                         │
   │     ▸ Costs → Iceberg lake → Snowflake → Datadog                               │
   └─────────┬─────────────┬─────────────────┬───────────────┬──────────────────────┘
             │             │                 │               │
             ▼             ▼                 ▼               ▼
   ┌──────────────┐ ┌──────────────────┐ ┌────────────┐ ┌────────────────┐
   │ Tempo / DD   │ │ Prometheus / DD  │ │ Loki / DD  │ │ LangSmith      │
   │ APM (traces) │ │ Metrics (RED+USE)│ │ Logs (text)│ │ Evals + traces │
   └──────┬───────┘ └────────┬─────────┘ └─────┬──────┘ └───────┬────────┘
          │                  │                 │                │
          └──────────────────┴─────────────────┴────────────────┘
                                │
                                ▼
   ┌────────────────────────────────────────────────────────────────────────────────┐
   │  Dashboards + Alerts                                                           │
   │                                                                                │
   │   Fleet level:                                                                 │
   │     - Total RPS, p50/p99 latency, error rate                                   │
   │     - Cost burn rate                                                           │
   │     - Tool selection distribution                                              │
   │     - LLM model usage                                                          │
   │                                                                                │
   │   Per-tenant:                                                                  │
   │     - Customer's agent runs, success rate                                      │
   │     - Their cost (per their budget)                                            │
   │     - Top failed runs (with link to trace)                                     │
   │                                                                                │
   │   Per-flow (specific agent use case):                                          │
   │     - "customer_support" flow funnel                                           │
   │     - Tool sequence frequency                                                  │
   │     - Eval scores trend                                                        │
   │                                                                                │
   │   Individual run drill-down:                                                   │
   │     - Trace waterfall (Tempo / Datadog APM UI)                                 │
   │     - LLM prompts (redacted) + responses                                       │
   │     - Tool inputs / outputs                                                    │
   │     - Eval score + breakdown                                                   │
   │     - Cost breakdown                                                           │
   │                                                                                │
   │   Alerts (PagerDuty + Slack):                                                  │
   │     P1: error rate > 2× baseline 5min                                          │
   │     P1: cost > $1000/hr (runaway)                                              │
   │     P1: agent stuck > 5min (no span for 60s)                                   │
   │     P2: hallucination rate > 5% on tier-1 flow                                 │
   │     P2: tool selection drift (new tool jumps to top-3)                         │
   │     P3: eval score drop > 5% 24h trailing                                      │
   │     P3: per-tenant cost approaching budget                                     │
   └────────────────────────────────────────────────────────────────────────────────┘
```

---

## 详细设计 (60-min walkthrough)

### Phase 1: Clarify + 5 pillars (5 min)

开口:
- "Agent multi-step? 我假设 plan-act-reflect with 5-10 step avg"
- "Per-tenant view yes? 我假设 customer 看自己的, 不看 fleet"
- "PII tier: redact at telemetry, 不能 raw log"

5 pillars (4 + cost):
1. **Traces** — request flow, where time goes, what tools called
2. **Metrics** — quantitative SLO, RED + USE + agent-specific
3. **Logs** — text events, debugging
4. **Evals** — quality, hallucination, correctness
5. **Costs** — $ per request, per tenant, per model

KPI:
- **Trace coverage**: 100% production runs, no untraced execution
- **Sampling**: 1% baseline, 100% on flags (error/slow/expensive)
- **Alert false positive rate**: < 5%
- **MTTD (mean time to detect)**: < 5 min for P1
- **MTTR**: < 30 min with traces in hand

### Phase 2: Trace per agent run (10 min)

**2.1 OpenTelemetry semantic conventions for LLM (2026 spec)**

OTel has GenAI semantic conventions standardizing LLM trace attributes:
- `gen_ai.system`: "openai" | "anthropic" | "gemini"
- `gen_ai.request.model`: "claude-sonnet-4.6"
- `gen_ai.request.temperature`
- `gen_ai.request.max_tokens`
- `gen_ai.response.id`
- `gen_ai.usage.input_tokens`
- `gen_ai.usage.output_tokens`
- `gen_ai.usage.cost_usd`

**2.2 Span hierarchy for agent run**

```
agent.run (root span)
├── auth.verify (50ms)
├── tool_discovery.list_tools (30ms)
├── llm.plan (LLM call: "what should I do?")
│   ├── prompt_render
│   └── anthropic.chat (500ms, 4K in, 200 out)
├── tool_call.sap_get_customer (200ms)
│   ├── auth.obo_exchange (30ms)
│   ├── cache.lookup (5ms, miss)
│   ├── http.request (150ms)
│   └── cache.write (5ms)
├── tool_call.sfdc_get_account (300ms)
├── llm.reflect (300ms)
├── llm.decide (final response, 800ms)
└── eval.score (async, 500ms, 1% sample)
```

每个 span 自动 attributes + 业务 attributes.

**2.3 Trace context propagation**

W3C TraceContext (`traceparent` header). 跨 service:
- Agent → MCP gateway: pass traceparent
- MCP gateway → tool server: pass traceparent
- Tool server → external API (Snowflake/SAP): pass if supported (otherwise audit only)

Result: 单一 trace view 跨整个 agent + 所有 tool + LLM call.

**2.4 Agent-specific span attributes**

不仅 GenAI standard, 我们 add:
- `agent.step_count`: 第几步
- `agent.flow_name`: "customer_support" / "refund_handler"
- `agent.user_id_hash`: hash (PII safe)
- `agent.tenant_id`
- `agent.prompt_version`: "customer_support@1.2.0"
- `agent.tools_invoked`: list of tool names
- `agent.success`: true/false
- `agent.error_class`: 'tool_error' / 'llm_refuse' / 'hallucination'

**2.5 Sampling**

100% trace 全部 store 太贵. 智能 sample:
- **100% on tier-1 events**: error / cost > threshold / latency > p99
- **10% on tier-2**: paid customer
- **1% on tier-3**: free tier baseline

但 1% baseline 仍存所有 trace 30 day (cold storage, Iceberg).

**Why keep 1% even baseline**: production bug 多 surface in 1% sample. Tail issue 不在 average.

### Phase 3: Metrics + SLO (8 min)

**3.1 RED for service**:
- **Rate**: agent runs/sec
- **Error**: % failed runs
- **Duration**: p50/p95/p99 e2e latency

**3.2 USE for infra**:
- **Utilization**: GPU %, CPU %, memory %
- **Saturation**: queue depth
- **Errors**: 5xx from LLM API, network

**3.3 Agent-specific metrics**:

| Metric | Why |
|---|---|
| tokens_per_run (in/out) | Cost driver, growth catches runaway |
| tool_calls_per_run | Loop bug if grows unbounded |
| llm_calls_per_run | Same as above, plan-reflect loop |
| tool_distribution (which tools, %) | Catch tool drift |
| top_K_tools_call_count | Most common tools |
| hallucination_score_p50 | NLI score for grounded responses |
| eval_score_avg | Sampled LLM-judge score |
| retrieval_hit_rate | RAG quality |
| tool_error_rate (per tool) | Identify flaky integration |
| llm_refusal_rate | Safety triggers |
| user_thumb_up_rate | UX signal |
| user_thumb_down_rate | UX signal |
| cost_per_run_p99 | Outlier detection |
| stuck_runs_count (running > 5 min) | Detection of hung runs |

**3.4 Per-cardinality**

Most metrics need per-tenant, per-flow, per-model dimension. Cardinality management:
- Pre-aggregate at 1 min granularity
- Limit dim values (top N tenant, others bucket "_other")
- Cold-store raw for ad-hoc analysis

**3.5 SLO definition**

| SLO | Target | Window |
|---|---|---|
| Availability (success rate) | 99.5% | 30d rolling |
| p99 latency | < 10s | 30d rolling |
| Hallucination rate (tier-1 flow) | < 2% | 7d rolling |
| Cost per run (p95) | < $0.20 | 7d rolling |
| Tool error rate (per tool) | < 1% | 7d rolling |

Error budgets:
- 99.5% availability = 36h downtime / month allowed
- > 10% budget burn in 1 day → freeze deploys

### Phase 4: Logs + PII redact (6 min)

**4.1 Structured JSON logging**

```python
logger.info("agent.tool_call", extra={
    "trace_id": ctx.trace_id,
    "span_id": ctx.span_id,
    "tenant_id": tenant.id,
    "user_id_hash": hash(user.id),
    "tool_name": "sap_get_customer",
    "tool_args_hash": hash(args),  # not raw args
    "latency_ms": 200,
    "success": True,
    "result_summary": "customer ACME-123 found"  # high-level, not raw data
})
```

**Why no raw**: user query / tool args might have PII.

**4.2 PII redaction pipeline**

OTel Collector has redaction processor:

```yaml
processors:
  attributes/redact:
    actions:
      - key: agent.user_query
        action: hash    # store hash, lookup separately if needed for debug
      - key: gen_ai.request.prompt
        action: delete  # never store raw prompt
      - key: tool.args
        action: hash
      - key: user.email
        action: delete
      - key: user.phone
        action: delete
```

Production: don't trust this 100%, additional layer:
- Presidio scan all log lines before write
- Anything matching PII pattern (SSN, MRN, email, phone) → redact

**4.3 Log levels + retention**

| Level | Retention | Use |
|---|---|---|
| ERROR | 30 days hot, 7 yr cold | Debugging incidents, compliance |
| WARN | 30 days hot, 90 days cold | Trend analysis |
| INFO | 14 days hot, 30 days cold | Normal operations |
| DEBUG | 1 day hot, never cold | Dev only, sample 0.1% in prod |

Cost: Datadog logs $1.20 / GB ingestion. 200M agent runs × 5 log per run × 1KB = 1TB/day = $1200/day = $36K/month for logs alone. Aggressive sampling + log levels critical.

**4.4 Debug hash → raw via separate secure store**

If real PII / raw needed for debugging:
- Hash stored in log/trace
- Raw stored encrypted in separate "debug vault" (only senior eng access, 24h auto-delete, audit access)
- Lookup process: request access → manager approval → time-bound access

### Phase 5: Eval in loop (10 min)

Eval 不只 offline, production 持续 eval:

**5.1 Sampling strategy**

| Type | Frequency | Cost |
|---|---|---|
| LLM-as-judge automated | 1% baseline, 100% errors, 100% tier-1 critical flow | $0.01/judge call |
| Human review | 0.1% sampled, 100% escalated | $5/review |
| Synthetic eval | Hourly golden set replay | $1/run |

**5.2 LLM-as-judge in production**

```python
async def post_agent_eval(run_id, query, response, retrieved_chunks):
    # 1. Hallucination check (NLI)
    claims = extract_claims(response)
    for claim in claims:
        evidence = find_supporting_chunk(claim, retrieved_chunks)
        entailment = await nli_model(premise=evidence, hypothesis=claim)
        if entailment < 0.7:
            log_hallucination(run_id, claim)
    
    # 2. Quality scoring (LLM-judge)
    judgment = await judge_llm.run("""
        Rate response on:
        - Helpfulness (1-5)
        - Accuracy (1-5)
        - Tone (1-5)
        - Safety (1-5)
        
        Query: {query}
        Response: {response}
        Sources: {chunks}
    """, query=query, response=response, chunks=summarize(retrieved_chunks))
    
    # 3. Emit eval metric
    await metrics.emit(
        "eval.score.helpfulness", judgment['helpfulness'],
        tags={"flow": run.flow_name, "model": run.model}
    )
    
    # 4. Queue to human if low score
    if min(judgment.values()) < 3:
        await human_review_queue.add(run_id)
```

Cost: 1% × 200M runs × $0.01 = $20K/month — significant. Sample wisely.

**5.3 Hallucination detection**

Beyond NLI:
- Citation check: claim 是否引 chunk_id, span 是否 in chunk
- Entity verification: named entity 是否在 sources mention
- Factual cross-check: 2 different LLM independently summarize, compare

**5.4 Tool selection drift**

Track over time which tool agent invokes:
```
Tool distribution Week 1: {sap_get_customer: 30%, sfdc_get_account: 25%, ...}
Tool distribution Week 4: {sap_get_customer: 50%, sfdc_get_account: 10%, ...}
                          → drift! agent stopped using SFDC. why?
```

PSI > 0.2 on tool distribution → alert.

**5.5 Stuck detection**

Agent run no span emit for 60s but trace still "running" → stuck. Causes:
- LLM API hang (rare)
- Tool API timeout but not handled
- Deadlock in agent state machine

Detection: trace 60s no progress → mark as 'stuck', kill, alert.

### Phase 6: Cost tracking (6 min)

**6.1 Per-request cost breakdown**

```json
{
  "run_id": "...",
  "cost_breakdown": {
    "llm_input_tokens": 4500,
    "llm_input_cost_usd": 0.0135,    // claude-sonnet-4.6 $3/M
    "llm_output_tokens": 600,
    "llm_output_cost_usd": 0.009,    // $15/M
    "embedding_calls": 1,
    "embedding_cost_usd": 0.0001,
    "tool_api_calls": {
      "sap_get_customer": {"count": 1, "cost_usd": 0.0005},  # SAP cost model
      "sfdc_get_account": {"count": 1, "cost_usd": 0.0001}
    },
    "storage_cost_usd": 0.00001,     # logging/audit
    "total_cost_usd": 0.0227
  }
}
```

**6.2 Per-tenant budget**

```python
class TenantBudgetMonitor:
    async def on_run_complete(self, run):
        await db.execute("""
            UPDATE tenant_spend SET 
                month_total = month_total + $1
            WHERE tenant_id = $2 AND month = $3
        """, run.cost_usd, run.tenant_id, current_month())
        
        spend = await db.fetch_val("SELECT month_total FROM tenant_spend WHERE tenant_id = $1 AND month = $2", run.tenant_id, current_month())
        budget = await db.fetch_val("SELECT monthly_budget FROM tenants WHERE id = $1", run.tenant_id)
        
        if spend > budget * 0.8:
            await alert.email(tenant.admin, f"Spend at 80% of budget")
        if spend > budget:
            # Soft throttle or hard stop, configurable
            if tenant.config['budget_hard_stop']:
                await disable_agent_for_tenant(run.tenant_id)
```

**6.3 Cost dashboards**

- Daily/monthly burn by tenant
- Cost by flow (which agent use case spends most)
- Cost per run trend (catch creep)
- Cost vs revenue per tenant (margin)

**6.4 Cost anomaly detection**

Per-tenant p95 cost per run baseline. > 2× alert. Catches:
- Bug in agent loop (multiple LLM calls)
- Bad customer query (extremely long context)
- Bug in prompt (token waste)

### Phase 7: Dashboards + alerts (8 min)

**7.1 Dashboard hierarchy**

**Level 1: Fleet (us ops view)**
- Total runs/sec, errors, latency
- Cost burn rate ($/hour)
- Top failing customers
- Top error classes
- Model usage distribution
- Trend: 24h, 7d, 30d

**Level 2: Per-tenant (customer-facing)**
- This customer's agent usage
- Their success rate
- Their cost (vs budget)
- Their top flows
- Top failed runs (with trace link)

**Level 3: Per-flow (specific use case)**
- "customer_support" flow funnel
- Tool sequence frequency (sankey)
- Hallucination rate
- Eval score trend

**Level 4: Individual run drill-down**
- Trace waterfall view
- Prompt (redacted)
- Tool calls (input/output redacted)
- LLM responses (redacted)
- Eval scores
- Cost breakdown

**7.2 Alert routing**

| Alert | Severity | Channel | Owner |
|---|---|---|---|
| Error rate > 2× 5 min | P1 | PagerDuty | on-call |
| Cost burn > $1000/hr | P1 | PagerDuty | on-call + finance |
| Stuck runs > 10 | P1 | PagerDuty | on-call |
| Hallucination > 5% tier-1 | P2 | PagerDuty + Slack | flow owner + ML |
| Tool sel drift PSI > 0.2 | P2 | Slack | flow owner |
| Eval drop > 5% 24h | P3 | Slack | ML team |
| Tenant budget 80% | P3 | Email customer + slack | customer success |
| Per-tool error > 5% 10 min | P2 | Slack | tool owner |

**7.3 Customer-facing dashboard**

Glean-like: customer logs in, sees their agent dashboard. Need:
- Per-tenant data isolation (RBAC)
- Only their data (no fleet)
- Trace drill-down with PII redacted (they see their own data anyway, but our raw redacted)
- Export: CSV download for their report

### Phase 8: Trade-offs + alternatives (7 min)

**Decision 8.1 — Build vs buy**

| Capability | Build | Buy |
|---|---|---|
| Traces | OTel SDK + Tempo (self-host) | Datadog APM, LangSmith |
| Metrics | Prometheus | Datadog, Grafana Cloud |
| Logs | Loki / ELK | Datadog Logs, Splunk |
| Evals | Custom (Python + LLM-judge) | LangSmith, Arize, Helicone |
| Costs | DB + Iceberg | DD custom dashboard, LangSmith |

I推 hybrid:
- **OTel SDK** for instrumentation (vendor-neutral)
- **LangSmith** for LLM-specific traces + eval (mature for agent)
- **Datadog** for metrics + logs + APM (universal)
- **Custom DB + Iceberg** for cost (need custom dim)

**Decision 8.2 — Sample vs full trace**

| Option | Pros | Cons |
|---|---|---|
| 100% trace | Complete | $$$, retention cost |
| Tail sampling (errors 100%, others 1%) | Targeted | Need post-hoc decide |
| Head sampling (random 1%) | Cheap | Miss long-tail issue |

我推 tail sampling: collector decides after seeing trace (error/slow/expensive → keep 100%, else 1%).

**Decision 8.3 — PII strategy**

| Option | Pros | Cons |
|---|---|---|
| Never log PII | Safe | Can't debug specific issue |
| Redact PII automatic | Safe + debug-able | False negatives |
| Encrypted PII vault | Best | Complex |

我推 redact + encrypted vault for full data when needed (with audit access).

**Decision 8.4 — In-loop eval cost**

| Option | Pros | Cons |
|---|---|---|
| Every run | Full visibility | $$$ (LLM-judge call per run) |
| Sample 1% + 100% errors | Cost-effective | May miss subtle drift |
| Hourly batch on logged runs | Cheaper, async | Latency to detect |

我推 1% + 100% on errors + hourly batch on tier-1.

---

## 关键决策点 (with rationale)

1. **OTel semantic conventions for GenAI (2026)** — vendor-neutral, future-proof.

2. **Tail sampling 100% errors / 1% baseline** — catch issues without breaking budget.

3. **PII redact at OTel collector** — defense in depth, before storage.

4. **5 pillars: traces + metrics + logs + evals + costs** — eval and cost are first-class observability for agent.

5. **Per-tenant per-flow per-model cardinality** — necessary for debugging.

6. **LLM-as-judge 1% + 100% errors** — cost-effective eval coverage.

7. **Hallucination NLI check** — quality dimension, not just success/fail.

8. **Tool selection drift PSI** — agent quality decay early signal.

9. **Stuck detection (no span 60s)** — common agent failure mode.

10. **Hybrid stack (OTel + LangSmith + Datadog + custom DB)** — best-of-breed.

---

## 数字 (capacity sizing, cost math)

**Volumes**:
- 200M agent runs/day, avg 5 LLM call + 3 tool call = ~1.5B spans/day
- 1% baseline sample → 15M spans hot retain
- 100% errors (5%) → 75M spans full → ~75GB/day traces

**Storage**:
- Tempo / Datadog traces: 75GB × 30 day = 2.2TB hot, $50/GB-month = $110K/month — too high
- Cost-control: 30 day for tier-1 only, 7 day others, S3 cold for 90 day

**Logs**:
- 1TB/day at 5 log lines / run × 1KB = $1200/day Datadog = $36K/month

**Eval cost**:
- 1% × 200M × $0.01 (Claude Haiku judge) = $20K/month
- 100% on tier-1 (50M run/day at tier-1, 0.5% of runs are tier-1) = 1M × $0.01 = $10K/month

**Total observability cost**:
- Traces: $80K/month
- Logs: $30K/month
- Metrics: $5K/month
- Evals: $30K/month
- Cost system: $1K/month
- Tools (LangSmith, DD): $5K/month
- **Total**: ~$150K/month

**As % of agent infra**:
- Agent LLM cost: ~$500K/month (200M runs × $0.025)
- Observability 30% of LLM cost — high but agent observability is essential

**Alert SLA**:
- MTTD < 5 min for P1
- MTTR < 30 min with traces
- < 5% false positive rate (tuned thresholds)

---

## Gao Xin 简历专属 reframe

1. **TikTok PayLater BNPL agent observability** — 你 build 过 multi-step agent monitoring, eval in loop, cost tracking. 写下 "我做过 prod 100K runs/day BNPL agent observability with OTel + custom eval".

2. **TikTok Voice agent 7 markets** — per-market dashboard 你做过, multi-tenant view 直接套.

3. **Indonesia OJK 合规 audit trail** — immutable log 7 年 retention, 你做过.

4. **Internal Agent Platform observability** — fleet-level + per-team view, 你做过.

5. **ConvFinQA hallucination detection** — citation + NLI 你写过.

reframe: "我做 PayLater agent 时直接面对这道题. Stack 是 OTel + LangSmith + 自建 cost DB + Datadog. 关键经验: stuck detection 我没设 60s, 用了 5min, 导致一次 1h 没人发现 — lesson learned. 这道题我会 60s 设."

---

## 5 个 Follow-ups

1. **"如果 LLM provider (Anthropic) 没 OTel native, 怎么集成?"** — 答: (a) Anthropic Python SDK 2026 自带 OTel hook (PostHogAI / Helicone proxy 也 OK); (b) 自己 wrap SDK 在 trace span 里; (c) 用 LangChain / LangGraph (有 OTel built-in); (d) Helicone proxy on top of Anthropic — adds tracing layer.

2. **"trace data 太多, $80K/month 太贵, 怎么 cut 50%?"** — 答: (a) 严格 tail sampling (errors only + 0.1% baseline); (b) Shorter retention (7 day hot, 30 day cold S3); (c) Drop full prompt/response in trace (already hashed); (d) Pre-aggregate trace metrics, drop raw spans for old data; (e) 自建 (Tempo + S3 backend) 比 Datadog cheaper.

3. **"customer 想看自己 trace 但不能看到 prompt 内容 (他们 PII), how?"** — 答: PII redact 后给 customer trace. 自身 PII 已经 redact (因为 own VPC 部署 redact happen 在 source). 同时给 customer "request raw" 按钮, 走 break-glass: customer DPO 审批 + 24h time-bound access.

4. **"agent hallucinate 但 NLI 没 catch, 怎么 improve?"** — 答: (a) NLI 阈值调严 (0.85 not 0.7); (b) Add LLM-judge "fact-check" specifically; (c) External fact source (Wikipedia/Google) for entity verify; (d) Active learning: human-labeled hallucinations train better detector; (e) Force citation in response, missing citation = flag.

5. **"如果 P1 alert 误触 (false positive) 多, on-call 疲劳, 怎么 reduce?"** — 答: (a) Compound conditions (error rate AND latency, not just one); (b) Per-tenant baseline (some tenant naturally noisy); (c) Anomaly detection (z-score / EWMA) not fixed threshold; (d) Suppression: post-deploy 30 min skip alert (deploy causes brief spike); (e) Alert review weekly: kill alerts firing > 5× without action.

---

## ❌ 死路答法

1. **"log everything to Datadog"** — 没分 trace/metric/log, 没 PII.
2. **"OpenAI usage dashboard 够"** — 只看 LLM, 不见 tool / agent loop.
3. **"无 trace"** — 多步 agent debug 不能.
4. **"无 PII redact"** — 合规挂.
5. **"全 trace store 30 day"** — $300K+/month, 破产.
6. **"100% LLM-judge"** — $200K+/month eval, 不划算.
7. **"无 stuck detection"** — agent hang 没人知道.
8. **"无 cost tracking"** — runaway 月底才发现.
9. **"single dashboard for all"** — fleet vs tenant vs flow vs run 不同视角.
10. **"alert 全 PagerDuty"** — alert fatigue, dilute P1.

---

## ✅ 加分项

1. **5 pillars (传统 3 + evals + costs)** — agent observability framework
2. **OTel GenAI semantic conventions (2026)** — current standard
3. **Tail sampling 100% error + 1% baseline** — cost-effective
4. **PII redact at collector** — defense in depth
5. **Per-tenant per-flow per-model cardinality** — debug-able
6. **In-loop LLM-as-judge 1% + 100% errors** — production eval
7. **Hallucination NLI + citation check** — quality dimension
8. **Tool selection drift PSI** — early decay signal
9. **Stuck detection 60s no progress** — common failure mode
10. **Numbers 给得出来** ($150K/month total, 30% of LLM cost, 200M runs/day, MTTD 5min)

---

## 一句话总结

Agent 可观测性不是 "Datadog 上挂个 trace", 是 **OTel GenAI spans + tail sampling + PII redact + RED/USE + agent-specific metrics (tool dist, hallucination, stuck) + in-loop LLM-judge + cost breakdown per run + 4-level dashboard (fleet/tenant/flow/run) + 8-channel alert routing**, 5 pillar (traces + metrics + logs + evals + costs) 一整套 production agent ops.

---

## Cheat Sheet

```
5 Pillars:
  Traces: OTel GenAI semantic conventions
  Metrics: RED + USE + agent-specific
  Logs: structured JSON, PII redacted
  Evals: LLM-judge in loop, hallucination check
  Costs: per-request breakdown, per-tenant budget

Trace structure per agent run:
  agent.run (root)
  ├── auth.verify
  ├── tool_discovery
  ├── llm.plan (LLM call span)
  ├── tool_call.X (per tool)
  ├── llm.reflect
  ├── llm.decide
  └── eval.score (async)

OTel GenAI attributes:
  gen_ai.system, request.model, request.temperature
  gen_ai.usage.input_tokens, output_tokens, cost_usd

Agent-specific spans:
  agent.step_count, flow_name, prompt_version
  tools_invoked, success, error_class

Sampling:
  100% on tier-1 events (error/slow/cost outlier)
  10% paid tier baseline
  1% free tier baseline
  Tail sampling at OTel Collector

Agent-specific metrics:
  tokens_per_run, tool_calls_per_run
  tool_distribution (% per tool)
  hallucination_score_p50
  eval_score_avg
  tool_error_rate (per tool)
  stuck_runs_count

Logs:
  Structured JSON
  PII redact at collector (Presidio integration)
  3-tier retention: 30d hot / 90d cold / 7yr archive

Evals in loop:
  LLM-as-judge (Claude Haiku) 1% sample + 100% errors
  Hallucination: NLI on claim vs evidence
  Citation: claim → chunk_id span check
  Human review queue for low scores

Cost tracking:
  Per-request: LLM in/out + embedding + tool API + storage
  Per-tenant monthly aggregation
  Budget alerts: 80% / 100%
  Anomaly: > 2× baseline

Dashboards (4 levels):
  Fleet: total RPS, error, cost burn, model dist
  Per-tenant: their runs, success, budget vs spend
  Per-flow: funnel, tool sequence, eval trend
  Per-run: trace waterfall, cost breakdown

Alerts:
  P1: error rate > 2× 5m | cost > $1K/hr | stuck > 5min
  P2: hallucination > 5% | tool drift PSI > 0.2
  P3: eval drop > 5% | tenant budget 80%

Stack:
  OTel SDK (instrument)
  LangSmith (LLM traces + eval)
  Datadog (metrics + logs + APM)
  Custom DB (cost dimension)

Cost:
  ~$150K/month for 200M runs/day
  30% of LLM cost (high but essential)

SLO:
  Availability 99.5%
  p99 < 10s
  Hallucination < 2% tier-1
  Cost p95 < $0.20
  MTTD < 5 min, MTTR < 30 min
```
