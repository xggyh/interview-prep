## T3.2 · MCP / API proxy — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/gfde-t3-mcp-api-proxy.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t3-mcp-api-proxy.html`](questions/gfde-t3-mcp-api-proxy.html)

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖 MCP 协议 / Gateway 6 责任 / 500-tool discovery / versioning / legacy 集成 全量.

### 🧠 核心心智模型 (1 sentence)

MCP 是 **vendor-neutral JSON-RPC 协议** (Resources/Tools/Prompts 三原语), Gateway 在 LLM 与 50 个 backend service 间承担 **6 责任** (discovery / auth+OBO / rate / observability / cache / versioning), 解决 "全 50 个 schema 塞 prompt" 和 "Agent 直调 API 没 IAM" 两大灾难.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| MCP | Model Context Protocol, Anthropic 2024 开源, 2026 业界标准 | enterprise + multi-LLM |
| Resources | MCP 只读数据原语 (`file://`, `db://`) | 读 doc / DB row |
| Tools | MCP 可执行函数原语 | mutate action |
| Prompts | MCP 可复用 prompt 模板原语 | 标准化 prompt |
| JSON-RPC | MCP transport-agnostic 调用语义 (id + method + params) | 所有 transport |
| stdio transport | Subprocess + stdin/stdout JSON-RPC | 桌面工具 (Claude Desktop) |
| HTTP transport | Per-call POST request | 跨网络简单 |
| SSE transport | Server-sent events 长连接 | streaming tool |
| WebSocket transport | 全双工 (2026 加入) | bidirectional |
| OBO (RFC 8693) | OAuth Token Exchange, user token → agent service token scope ≤ user | enterprise IAM |
| Tool discovery | LLM 在 N tool 中找适用的 (RAG / hierarchical / meta) | 500+ tools |
| Adapter chain | v1 ↔ v2 schema 转换 layer | versioning |
| Schema diff CI | PR 自动检测 breaking change | tool repo |
| Circuit breaker | 单 MCP server 10 fail / 1min → open 5min | per-server |
| Function calling | OpenAI 私有协议, only Tools, no Resources/Prompts | 区别 MCP |

### 🎯 6 个 Gateway 责任 + 4 discovery 层

**Responsibility 1: Tool Discovery (RAG over descriptions)**
- When: 任何 enterprise > 20 tools
- Algorithm: embed tool descriptions + RAG top-20 + RBAC filter + RRF (dense+BM25)
- Trade-off: RAG miss rate vs prompt 装满
- Tools: Pinecone / Qdrant + sentence-transformers embedding, hand-curated descriptions

**Responsibility 2: Auth + OBO**
- When: enterprise + multi-tenant
- Algorithm: user OAuth token → exchange (RFC 8693) → agent service token (scope ≤ user)
- Trade-off: per-call exchange latency vs caching token (TTL trade)
- Tools: Auth0 / Okta / Keycloak token exchange, Vault for secret storage

**Responsibility 3: Rate Limit + Quota**
- When: multi-tenant cost control
- Algorithm: token bucket per (user, tool, tenant); 429 + Retry-After
- Trade-off: per-dim rate limit complexity vs noisy neighbor
- Tools: Envoy rate limit filter, Redis Lua atomic, LiteLLM router

**Responsibility 4: Observability (OTel trace propagation)**
- When: any production MCP gateway
- Algorithm: inject traceparent header before forward, span.attr tool.name + tenant_id
- Trade-off: trace sampling cost vs debug visibility
- Tools: OpenTelemetry SDK, Honeycomb / Datadog / Tempo, LangSmith for LLM-specific

**Responsibility 5: Caching (idempotent reads)**
- When: read-only tools, fuzzy queries
- Algorithm: per-tool TTL (get_balance 5s, static 24h), per-user isolation, semantic for fuzzy
- Trade-off: stale data vs cost saving
- Tools: Redis + Pinecone (semantic), per-tool config

**Responsibility 6: Versioning + Adapter Chain**
- When: customer API quarterly upgrade
- Algorithm: semver in tool spec + adapter v1↔v2 + 90-day deprecation window + schema diff CI + daily eval
- Trade-off: adapter maintenance overhead vs immediate break
- Tools: Buf / openapi-diff, GitHub Actions schema check, custom eval suite

### 🌳 关键决策树 (ASCII)

```
Use MCP?
  ├─ Single LLM vendor + < 20 tool + greenfield ── 用 OpenAI function calling (low overhead)
  ├─ Sub-100ms hard latency tool ── 直调 (MCP overhead 10-50ms)
  ├─ Stateful long-running tool (SSH) ── 直接 SSH session (MCP 不合适)
  └─ Multi-vendor / 20+ tool / customer ecosystem ── MCP ⭐ (2026 standard)

Tool discovery strategy?
  ├─ < 20 tool ── all in prompt
  ├─ 20-100 ── RAG top-20 by query
  ├─ 100-500 ── Hierarchical (domain → category → tool)
  └─ > 500 ── + meta-tool find_tool(query)
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: MCP Protocol Deep Dive — Resources / Tools / Prompts**

```json
// Initialization handshake
{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{...},"clientInfo":{"name":"agent","version":"1.0"}}}
// List tools
{"jsonrpc":"2.0","method":"tools/list"} 
// Call tool
{"jsonrpc":"2.0","method":"tools/call","params":{"name":"create_order","arguments":{...}}}
// List resources
{"jsonrpc":"2.0","method":"resources/list"}
// Read resource
{"jsonrpc":"2.0","method":"resources/read","params":{"uri":"db://users/42"}}
```
- Top 3 gotchas: (1) confuse function calling with MCP (only Tools, no Resources) (2) 不知道 initialization 必须 handshake (3) 用 SSE 时忘 keepalive
- Tools: Anthropic MCP SDK (Python/TS), modelcontextprotocol.io spec

**Problem 2: Gateway 6 责任 (Auth + Rate + Obs + Cache)**

```python
async def gateway_call(req, user_token):
    # 1. Auth + OBO
    agent_token = await oauth.exchange(user_token, scope=tool.required_scope)
    # 2. Rate limit per (user, tool, tenant)
    if not await rate_limit_check(req.user_id, req.tool, req.tenant_id):
        return 429
    # 3. Cache (idempotent reads)
    if tool.cacheable:
        cached = await redis.get(cache_key(req))
        if cached: return cached
    # 4. Trace propagation
    headers["traceparent"] = otel.current_traceparent()
    # 5. Forward + circuit breaker
    with cb(req.tool):
        resp = await mcp_server.call(req, agent_token, headers)
    # 6. Cost track + audit
    audit_log(actor=agent, on_behalf_of=user, action=req.tool, args=req.args, result=resp)
    return resp
```
- Top 3 gotchas: (1) cache write op (灾难) (2) trace context not propagated (debug stuck) (3) agent service principal admin scope (违反 OBO)
- Tools: Envoy, Auth0 token exchange, Redis Lua, OpenTelemetry, Hystrix-style CB

**Problem 3: Tool Discovery at Scale — RAG, Hierarchical, Meta-tool**

```
L1 RBAC filter:        user 权限内 tool catalog (per-tenant)
L2 RAG by query:       embed query, vector top-20 + RRF (dense + BM25)
L3 Hierarchical:       LLM 先选 domain → category → tool (递归 narrow)
L4 Meta-tool find_tool: agent 主动调 find_tool(query) 当作 tool
Boost: tool usage history (recent / popular) re-rank
```
- 实测数据 (ByteDance Internal Agent Platform): tool selection accuracy 70% → 92% after RAG discovery
- Top 3 gotchas: (1) auto-gen from OpenAPI (description 不到位 → RAG miss) (2) 不 hand-curate description (3) 不 boost by usage history
- Tools: Pinecone / Qdrant, sentence-transformers / bge-large, hybrid retrieval RRF

**Problem 4: Versioning + Schema Evolution**

```
Versioning:
  semver in tool spec: { name: "create_order", version: "1.2.0" }
  Adapter chain: v2.adapter(v1.call_args) → v2.call → v1.adapter(v2.result)
  Deprecation: 90-day window with warning header

Schema diff CI:
  openapi-diff / buf breaking-change detection on PR
  Eval suite daily: run golden cases against v1 vs v2

Customer notification:
  Webhook: schema_change(tool, old_version, new_version, breaking_yes_no, deadline)
```
- Top 3 gotchas: (1) breaking change 没 warn (2) adapter v1↔v2 missing 双向 (3) eval suite 不 daily (drift unnoticed)
- Tools: Buf, openapi-diff, GitHub Actions, custom eval golden cases

**Problem 5: Legacy Integration — REST → MCP Adapter, Screen Scrape, File Drop**

| Type | Strategy | Effort | When |
|---|---|---|---|
| REST API | Adapter wrap, hand-curate desc | 1 day/service | 现代 internal API |
| Mainframe (COBOL) | Screen scrape (3270 terminal) | 1 week | read-only legacy |
| Batch-only | File drop S3 + polling | 1 day | overnight ETL |
| SOAP/XML | Adapter + XSL transform | 2 day | enterprise legacy |

Graceful degradation tier:
- T1 MCP server up + tool fast → normal
- T2 slow → circuit-break / longer timeout
- T3 down → cached response if read-only
- T4 sustained outage → user message "service temporarily unavailable"

- Top 3 gotchas: (1) auto-gen MCP from OpenAPI (description 不足 → tool select 错) (2) screen scrape 不 handle screen redesign (3) file drop 不 idempotent
- Tools: Anthropic MCP SDK, py3270 (mainframe), boto3 S3, hand-written adapter

### 🔥 Production gotchas (top 15)

1. **All 50 tool schema in prompt**: 25K token waste $0.05/call, tool selection 30% miss
2. **Agent direct API call (no OBO)**: agent service principal admin → 权限灾难
3. **No tool discovery**: prompt overflow, LLM picks wrong tool
4. **Auto-gen from OpenAPI**: description 不准 → RAG miss → 错 tool
5. **No versioning**: customer 升级 API → eval drop overnight
6. **No circuit breaker**: 1 slow MCP server 拖垮 gateway
7. **Cache writes**: idempotent assumed but mutation cached → double-side-effect
8. **No trace propagation**: agent 卡哪步 debug 不能
9. **MCP = function calling 混淆**: 不知道 Resources / Prompts 原语
10. **Per-call OAuth exchange**: 100ms 每 call, 不缓存 token (TTL 5min sweet spot)
11. **No per-tool TTL config**: get_balance 缓 1h → 用户已转账显示余额错
12. **Tool description 不 hand-curate**: "create order" → "create new order entry" 微改 RAG hit 20%
13. **Schema diff CI 缺**: breaking 没 detect, 客户上线挂
14. **No DLQ for MCP server crash**: 丢请求
15. **Mainframe scrape 不 handle screen redesign**: 客户 IT 改 screen → adapter 死

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| MCP gateway design | Internal Agent Platform | "50+ MCP server, unified gateway 6 责任, 200+ agent 用同套 SDK" |
| Tool discovery RAG | Internal Agent Platform | "Pinecone embedding tool desc + RRF, accuracy 70% → 92%" |
| OBO scope exchange | Voice agent 7 markets | "per-tenant OBO, agent token scope ≤ user, audit log immutable" |
| Versioning + adapter | BNPL chatbot intent | "intent → tool route, semver schema, daily eval golden 0 drift" |
| Legacy integration | ConvFinQA legacy bank API | "SOAP → adapter + hand-curated desc, 3 day to integrate" |
| Circuit breaker | TikTok PayLater | "per-MCP-server CB 10/1min, 5min cooldown, recovery success 95%" |
| Trace propagation | Internal Agent Platform | "OTel context across agent → gateway → MCP → real API, E2E trace 视化" |

### 🎤 面试现场 quotables (top 8)

1. "MCP ≠ function calling. MCP 是 vendor-neutral 协议 + 3 原语 (Resources/Tools/Prompts)"
2. "Gateway 6 责任合一. 直调没 IAM + rate + observ = enterprise 不接受"
3. "500 tool 一定要 RAG discovery, 不能全塞 prompt — token cost 25K/call"
4. "OBO 是 enterprise 红线. Agent 永远不能比 user 权限大"
5. "Schema diff CI + 90 day deprecation + daily eval = 安全升级 API"
6. "Tool description 必须 hand-curate, 不能 auto-gen OpenAPI — RAG hit rate 差 20-30 个点"
7. "Versioning 用 semver + adapter chain v1↔v2 双向, customer 升级 0 downtime"
8. "Internal Agent Platform 70% → 92% tool selection accuracy after RAG"

### 🚨 红线 (top 10 anti-patterns)

1. 50 tool 全塞 LLM prompt (cost + 选错)
2. Agent 直 API 调用 (no OBO, 权限灾难)
3. No tool discovery (prompt overflow)
4. Auto-gen from OpenAPI (RAG miss)
5. No versioning (升级 break)
6. No circuit breaker (1 slow kill all)
7. Cache writes (double-side-effect)
8. No trace propagation (debug stuck)
9. MCP = function calling 混淆
10. Per-call OAuth no caching (latency × N)

### 📊 2026 工具栈 quick lookup

| 类别 | 默认 | Alt | 你用过 |
|---|---|---|---|
| MCP SDK | Anthropic MCP Python/TS | — | ✅ |
| Gateway | Envoy + custom filters | Kong, Apigee | Envoy |
| Token exchange | Auth0 / Okta | Keycloak | Auth0 |
| Vector DB (discovery) | Pinecone | Qdrant, Milvus, Weaviate | Pinecone |
| Embedding model | bge-large / nomic-embed | text-embedding-3 | bge-large |
| Rate limit | Envoy filter + Redis Lua | Kong rate-limit | Envoy |
| Trace | OpenTelemetry → Honeycomb | Datadog, Tempo | OTel |
| LLM observ | LangSmith | Phoenix, Helicone, Langfuse | LangSmith ✅ |
| Schema diff CI | Buf / openapi-diff | swagger-diff | Buf |
| Adapter | hand-written wrapper | OpenAPI generator (caveat) | hand-written |

### 🎬 45-min 节奏 (T3.2 专属)

```
0-5    Clarify    "Tool count? Multi-LLM? Customer ecosystem? Compliance? Legacy stack?"
5-10   Mental     "MCP = vendor-neutral 协议; Gateway 6 责任"; 画 ASCII
10-25  Deep-dive  挑 1 个责任 (discovery / OBO / versioning) 展开
25-35  Versioning  semver + adapter chain + 90 day deprecation
35-42  Legacy      REST adapter / screen scrape / file drop / degradation tier
42-45  Resume      "Internal Agent Platform — 70% → 92% accuracy"
```

### 🔢 关键 production 数字

- Internal Agent Platform tool selection: 70% → 92% (RAG discovery)
- MCP overhead: 10-50ms per call (gateway 走一遍)
- OAuth token exchange: 50-200ms (cache TTL 5min sweet spot)
- Per-MCP-server CB: 10 fail / 1min open + 5min cooldown
- Schema diff CI: PR check < 5s
- Adapter v1↔v2: 1 day implement per breaking change
- 50 internal service 接入: 50 day (1 day/service hand-curate desc)
- ByteDance Internal Agent Platform: 200+ agent, 50+ MCP server, 1M+ tool call/day
