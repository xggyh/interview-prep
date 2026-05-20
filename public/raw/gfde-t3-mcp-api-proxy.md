## 题目

> "Customer has **50 internal microservices**, each with own REST API + auth. They want an agent that can call any of them. Design the **tool abstraction layer**. Why is **MCP** (Model Context Protocol) relevant in 2026?"

或追问形态:

> "What does MCP solve that you can't get from just OpenAI's function-calling API? When would you NOT use MCP?"

**Round**: Tool / Integration Architecture (45 min)

---

## 这道题在考什么

考你**2026 modern integration architecture**:

1. **Tool abstraction** —— LLM-agnostic interface
2. **MCP 是 standard** —— Anthropic propose, Google/OpenAI also adopting
3. **API proxy layer** —— auth / rate-limit / observability 统一
4. **Schema versioning** —— customer API changes don't break agent
5. **Discoverability** —— LLM 怎么知道有哪些 tools

---

## 必问 clarifying

**1. LLM vendor**

> "Single vendor (Claude only) or multi-vendor? Affects design — MCP is vendor-neutral."

**2. Internal API contract stability**

> "Internal APIs change quarterly or monthly? Affects need for versioned tool spec."

**3. Auth model**

> "Per-API key, OAuth, custom token? Agent acts as itself or on-behalf-of user?"

**4. Tool catalog size**

> "50 services × 10 endpoints each = 500 tools. LLM can't see all. Need scoping/routing."

**5. Latency target**

> "Internal API latency + proxy overhead — budget OK?"

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify vendor / catalog size / auth |
| 5-15 min | MCP overview + why fit |
| 15-25 min | Proxy layer (auth / rate-limit / observability) |
| 25-35 min | Tool discovery + scoping (500 tools problem) |
| 35-45 min | Versioning + observability |

---

## 我会这样答（sample）

> "Clarify — *[假设: multi-vendor (Claude + Gemini + GPT), APIs change quarterly, OAuth + on-behalf-of, 500 tools, latency 2s budget]*.
>
> **MCP overview**:
>
> Anthropic's Model Context Protocol (open-source, adopted by major LLM vendors). Standardizes:
>
> ```
> Resources   — read-only data (files, DB rows, search results)
> Tools       — callable functions
> Prompts     — reusable prompt templates
> ```
>
> Servers expose these over JSON-RPC (stdio / HTTP / SSE). Clients (LLM apps) discover and consume uniformly.
>
> **Why MCP for this customer**:
>
> - **Vendor-neutral**: same MCP server consumed by Claude / Gemini / GPT
> - **Future-proof**: spec evolves, customer not vendor-locked
> - **Tool discovery**: clients query `list_tools` dynamically, no hardcode
> - **Standard auth**: OAuth flow standardized
>
> **Architecture for 50 services**:
>
> ```
>             ┌─────────────────────────┐
>             │   Agent (any LLM)       │
>             └────────────┬────────────┘
>                          │ MCP protocol
>             ┌────────────┴────────────┐
>             │  MCP Gateway (proxy)    │
>             │  - Discovery / routing  │
>             │  - Auth / OBO           │
>             │  - Rate limit           │
>             │  - Observability        │
>             │  - Tool selection (RAG) │
>             └─────┬──────┬──────┬─────┘
>             ┌─────┴┐ ┌───┴───┐ ┌┴────┐
>             │MCP-1 │ │MCP-2  │ │... 50│
>             │(Salesforce)    │ │      │
>             └──┬───┘ └───┬───┘ └──┬───┘
>             ┌──┴────┐┌───┴────┐┌──┴────┐
>             │Cust API│Cust API ││Cust API│
>             │  #1   ││  #2    ││  #N   │
>             └───────┘└────────┘└───────┘
> ```
>
> **MCP Gateway (proxy) responsibilities**:
>
> **1. Tool discovery + scoping**
>
> With 500 tools, LLM context can't hold all definitions. Solution:
>
> ```python
> # Tool catalog embedded
> tool_index = vector_index([tool.description for tool in all_tools])
>
> async def list_relevant_tools(user_query, user_role, top_k=20):
>     # 1. RAG: retrieve top tools by query
>     candidates = tool_index.search(user_query, top_k=50)
>     # 2. Filter by user permissions
>     allowed = [t for t in candidates if user_role.can_use(t)]
>     # 3. Return top-k
>     return allowed[:top_k]
> ```
>
> LLM sees top-20 most relevant tools, not all 500.
>
> **2. Auth + OBO (on-behalf-of)**
>
> ```python
> async def proxy_call(tool_name, args, user_token):
>     # Get OAuth token for target service, scoped to user
>     service_token = await oauth.exchange(
>         user_token=user_token,
>         scope=tool_registry[tool_name].required_scopes,
>     )
>     
>     # Call underlying MCP server with delegated auth
>     return await mcp_servers[tool.service].call(
>         tool_name, args,
>         auth=service_token,
>     )
> ```
>
> Agent **never has more perms than user**.
>
> **3. Rate limit + quota**
>
> ```python
> async def proxy_call(...):
>     if not rate_limit.allow(user, tool):
>         raise RateLimitExceeded
>     if user.session_quota_remaining(tool) <= 0:
>         raise QuotaExceeded
>     ...
> ```
>
> **4. Observability**
>
> - Per-call: tool, user, latency, status, cost
> - Aggregated: per-tool success rate, per-user usage
> - Traces propagate to underlying services (OpenTelemetry)
>
> **5. Caching**
>
> ```python
> # For idempotent reads
> async def proxy_call(tool, args):
>     if tool.is_idempotent_read:
>         cache_key = hash(tool, args)
>         cached = await cache.get(cache_key)
>         if cached: return cached
>     
>     result = await underlying_call(...)
>     
>     if tool.is_idempotent_read:
>         await cache.set(cache_key, result, ttl=tool.cache_ttl)
>     return result
> ```
>
> **6. Versioning**
>
> ```python
> # MCP descriptor includes version
> {
>   "name": "create_order",
>   "version": "2.0",
>   "schema": {...},
>   "deprecated_versions": ["1.0"],
> }
>
> # Agent specs which version (default latest)
> # Old agents pinned to v1 work until version EOL
> # Gradual migration on customer schedule
> ```
>
> **Custom API → MCP server adapter** (when underlying API isn't MCP-native):
>
> ```python
> # Each microservice gets a thin adapter
> class SalesforceMCPServer:
>     async def list_tools(self):
>         return [
>             Tool(name='create_lead', schema=..., handler=self.create_lead),
>             Tool(name='get_account', schema=..., handler=self.get_account),
>         ]
>     
>     async def create_lead(self, args):
>         resp = await sf_rest.post('/leads', json=args, auth=...)
>         return self.translate_response(resp)
> ```
>
> Adapter handles: REST → MCP mapping, error code translation, type coercion.
>
> **When NOT to use MCP**:
>
> - Single LLM vendor + small tool count + greenfield → OpenAI function calling is simpler
> - High-frequency tools (microseconds) where MCP proxy overhead matters
> - Tools that don't fit MCP semantics (stateful long-running like SSH session)
>
> **Implementation steps**:
>
> 1. Identify customer's existing API surface (50 services)
> 2. Categorize: which need adapter, which natively MCP, which custom (e.g., GraphQL)
> 3. Build MCP gateway as the single point of contact for LLM
> 4. Per service: write adapter (~1 day each, 50 days for full coverage)
> 5. Tool discovery via vector index + role-based filter
> 6. OAuth + observability baked into gateway"

---

## 多场景变体 + 解法

### 变体 1: SaaS 集成客户内部 stack

> "我们 SaaS 给企业用, 客户有自己的 Salesforce / Workday / Jira。怎么集成？"

**解法**:
- **MCP 适配器 per 客户系统**: 写一次 Salesforce-MCP adapter, 所有客户复用
- **Per-tenant config**: 客户的 endpoint / token 存 secret manager, MCP server 启动注入
- **Customer-hosted MCP server option**: data sensitive 客户自己 host MCP server, 我们的 agent 远程调
- **Network boundary**: VPC peering / VPN tunnel / OAuth bridge
- **Schema discovery**: agent first call `list_tools()` 适应客户 SF 自定义 field

### 变体 2: Multi-tenant agent platform

> "1 平台服务 100 客户, 每客户工具 catalog 不同。"

**解法**:
- **Per-tenant tool registry**: 路由时按 tenant 加载工具子集
- **Shared MCP infrastructure**: 1 套 MCP gateway, multiplex
- **Quota per tenant**: tool call rate, cost budget
- **Isolation**: tenant A 不能看到 tenant B 的 tool/data
- **Per-tenant fine-tune**: 工具描述可能 per-tenant 微调 (业务术语不同)
- **Centralized observability** 但 per-tenant 视图

### 变体 3: Cross-cloud (GCP + AWS + Azure)

> "Agent 要操作 3 个 cloud 资源。"

**解法**:
- **每 cloud 1 个 MCP server**: gcp-mcp / aws-mcp / azure-mcp
- **统一 tool naming**: `cloud:gcp:gcs:upload` / `cloud:aws:s3:upload` 但 schema 相似
- **Cross-cloud workflow**: agent 决定 'copy from gcs to s3' 编排两个 tool
- **Auth**: 各自 cloud IAM, agent 用 OBO 或 service account
- **Cost-tag**: 每 tool call 标 cloud, 成本归属
- **Egress 警告**: 跨云转数据贵, tool wrapper warn

### 变体 4: LLM 厂家可移植性

> "今天用 Claude, 明天可能换 Gemini。Tool spec 不要绑死。"

**解法**:
- **MCP 是 vendor-neutral**: 同 MCP server 对接 Claude / GPT / Gemini
- **Adapter layer**: MCP tool → OpenAI function calling 格式 / Anthropic tool_use / Google function spec
- **Prompt template 抽象**: 'tool calling instruction' per vendor 不同, 用模板
- **测试矩阵**: 同套 eval 在 N 个 LLM 跑, 防 vendor-lock-in regression
- **Routing logic**: 不同 query 走不同 LLM (cost / quality 优化)

### 变体 5: Legacy system 集成 (mainframe / COBOL)

> "客户核心系统是 mainframe, 没 modern API。怎么 agent 化？"

**解法**:
- **Adapter heavy lifting**: REST wrapper around CICS / COBOL screen-scrape
- **CDC (change data capture)**: 不直接调 legacy, read 改动 stream
- **Read-only first**: legacy 改造慢, 先把 query 能力 expose
- **Per-screen mock**: legacy unavailable → mock for dev
- **Latency expect**: legacy 慢 (500ms-5s), agent 超 timeout 要 graceful handle
- **Vendor relationship**: 跟 legacy team 谈, 加 idempotency / audit hook

---

## 简历专属 reframe

| 题 | 你做过 |
|---|---|
| Tool abstraction | Internal Agent Platform — workflow/tool/memory abstraction 你 owned |
| API proxy | TikTok payment — gateway layer 自然有 |
| OAuth / OBO | Voice agent multi-tenant — permission scoping |
| Tool discovery | BNPL chatbot — intent → tool routing |
| Rate limit / quota | TikTok payment — per-user QPS limits 必做 |

**Quote**:

> "On Internal Agent Platform we built exactly this — though pre-MCP we rolled our own protocol. **Tool registry** with JSON-schema-defined inputs/outputs, **gateway** that did auth + rate-limit + observability + retry, and **RAG-based tool discovery** for agents with 200+ tool catalog. The big production lesson: **without discovery**, agents tried to call non-existent tools or use wrong tool for task. After adding RAG retrieval over tool descriptions, agent tool-selection accuracy went from 70% to 92%."

---

## 5 follow-ups

**Q1**: "MCP overhead — extra hop. Latency cost?"
**A**:
- Single proxy hop ~5-20ms
- Auth check / rate limit ~1-2ms (Redis)
- Observability instrumentation ~< 1ms
- Total ~10-25ms — acceptable for 2s budget
- For sub-100ms hard cases: pre-fetch + cache aggressive

**Q2**: "Customer API changes break agent. How handle?"
**A**:
- **Schema versioning** in MCP spec
- **Adapter layer** handles old / new mapping
- **Deprecation warning** for old version, cap usage
- **Eval suite** runs daily against tools, alert on schema drift
- **Customer notification** before breaking change

**Q3**: "500 tools — LLM context can't fit. Beyond RAG retrieval?"
**A**:
- **Hierarchical**: domain → category → tool (LLM picks domain, then tool)
- **Per-agent specialization**: customer-support agent sees only support tools
- **Dynamic loading**: agent calls `list_tools(query)` then uses subset
- **Tool meta-tools**: a 'find_tool' tool that LLM uses to discover

**Q4**: "MCP server crashes — gateway behavior?"
**A**:
- Circuit breaker per-MCP-server
- Health check every 30s
- If down: return ToolUnavailable to agent
- Agent decides: alternative tool / fallback / fail user-visible
- Reconnect attempt after 1 min

**Q5**: "Compare MCP vs OpenAI function calling — when each?"
**A**:
- **OpenAI function calling**: single-vendor, in-process, fast, simple
- **MCP**: vendor-neutral, distributed, has versioning, has discovery
- **In practice**: OpenAI function calling is the LLM-side protocol; MCP is the tool-side protocol. They're complementary — MCP tool defs map to OpenAI function defs
- **Choose MCP** when: multi-vendor, customer-owned tools, long-term

---

## ❌ 易错点

1. **No abstraction** — agent talks directly to each API
2. **Hardcode 500 tools** in LLM context (won't fit)
3. **No OBO** — agent has more perms than user
4. **No versioning** — API change breaks agent
5. **No discovery** — agent doesn't know which tool to use
6. **MCP as the LLM protocol** (confusing with function calling)
7. **No circuit breaker per tool**

---

## ✅ 加分项

1. **MCP standard** awareness + when/why
2. **Gateway responsibilities** (auth / RL / obs / cache / version)
3. **Tool discovery via RAG** for large catalog
4. **OBO** authorization flow
5. **Adapter pattern** for non-MCP-native APIs
6. **Versioning** strategy with deprecation
7. **OpenTelemetry trace propagation**
8. **Quote Internal Agent Platform 70→92% tool accuracy**

---

## Cheat Sheet

```
MCP (Model Context Protocol):
  Anthropic open standard, adopted broadly 2026
  Vendor-neutral
  3 primitives: Resources / Tools / Prompts
  JSON-RPC over stdio / HTTP / SSE

Gateway responsibilities:
  Tool discovery (RAG over descriptions)
  Auth + OBO (OAuth scope exchange)
  Rate limit + quota
  Observability (OTel)
  Caching (idempotent reads)
  Versioning
  Circuit breaker per server

500 tools problem:
  RAG-based discovery (top-20 relevant)
  Hierarchical (domain → category → tool)
  Per-agent specialization
  Meta-tool 'find_tool'

OBO (on-behalf-of):
  User token → exchange for service token
  Service token scope ≤ user's perms
  Agent never has more perms than user

Adapter pattern:
  REST API → MCP server adapter
  Handles: protocol map, type coerce, error translate
  ~1 day per service

Versioning:
  Schema version in MCP spec
  Adapter handles old/new map
  Deprecation warning + EOL date
  Eval suite catches drift

When NOT MCP:
  Single vendor, small tool count, greenfield
  Sub-100ms latency hard
  Stateful long-running (e.g., SSH)

Compared to function-calling:
  OpenAI FC: LLM-side protocol, in-process
  MCP: tool-side protocol, distributed
  Complementary, FC tools defined as MCP tools

红线:
  - No abstraction
  - Hardcode all tools in context
  - No OBO
  - No versioning
  - No discovery
  - No circuit breaker
```
