## Q27 · SAP + Salesforce + Postgres 统一给 AI agent 用

> "Customer has data scattered in **SAP S/4HANA** (orders + inventory), **Salesforce** (CRM, customer 360), and **internal Postgres DB** (operational data, custom). They want an **AI agent** that can answer questions like 'show me the top 10 customers with overdue invoices and their last interaction'. **How do you make this data accessible to the agent?** Don't try to merge into one DB."

**中文翻译**:

> "客户数据散落在 **SAP S/4HANA** (订单 + 库存, ERP 系统), **Salesforce** (CRM, 客户 360 全景), 还有**内部 Postgres DB** (运营数据 + 自建表). 他们想要一个 **AI agent**, 能回答类似 '给我看 top 10 过期账单的客户和他们最近一次互动' 的问题. **怎么把这些数据开放给 agent?** 不要尝试合并到一个 DB."

**Round**: System Design (60 min)
**出处**: Exponent 2026 FDE · 公司: Palantir / Anthropic / Glean / Sierra · 行业: cross-industry (B2B SaaS)
**约束**: heterogeneous data sources (SAP / SFDC / PG) / different auth models / different latency / no ETL into single warehouse / per-user permission preserved / agent must compose queries across sources

---

## 📖 术语速查 (本题用到的)

> 这题是 agent + enterprise data integration 题. 名词不懂直接误入 ETL 死路. 5 min 看完.

### Agent / Tool 调用

| 术语 | 解释 |
|---|---|
| **MCP (Model Context Protocol)** ⭐ | Anthropic 2024 开源的 agent tool 调用标准, JSON-RPC over HTTP. 2026 业界 default. |
| **MCP server** | 实现 MCP 协议的服务 — 每个 source 一个 server. |
| **MCP gateway** | 中心化的 MCP 路由层 — 做 auth / cache / 日志. |
| **Tool / Function calling** ⭐ | LLM 调用外部 function 的能力. OpenAI 命名 "function calling", Anthropic 叫 "tool use". |
| **Tool catalog** | 工具目录 — 所有可用 tool 的 metadata 集合. |
| **Domain tool vs Raw tool** ⭐ | Domain = `get_overdue_invoices` (业务语义); Raw = `POST /sap/odata/...` (技术细节). 用 domain. |
| **Composite tool** | 组合工具 — 一个 tool 内部调多个 API, 减少 LLM compose 错误. |
| **Tool description** | 工具描述 — 给 LLM 看的 docstring, 决定 LLM 选不选这个 tool. |
| **LangGraph** | LangChain 的 stateful agent 框架, 支持 parallel tool call. |
| **Claude Sonnet 4.6** | Anthropic 旗舰中端 model. |

### Auth / 权限 (核心)

| 术语 | 解释 |
|---|---|
| **OBO (On-Behalf-Of)** ⭐ | 代理身份调用 — agent 以 user 身份调用 source, 不是 service account. |
| **Token exchange (RFC 8693)** | OAuth 2.0 token 互换标准 — user JWT 换 SAP/SFDC 的 access token. |
| **JWT Bearer flow** | SFDC 的 JWT 认证流 — 签发的 JWT 直接换 access token. |
| **Subject token** | 被代理的 user 的 token. |
| **Service account** | 服务账号 — 不依赖具体 user 的身份. 这题尽量不用. |
| **Permission flattening** | 权限拍平 — ETL 后 source 端 RLS 丢失, 风险. |
| **RLS (Row-Level Security)** | 行级安全 — Postgres / BigQuery 按 user 过滤行. |
| **IdP (Identity Provider)** | 身份提供商 — Okta / Azure AD. |
| **Okta** | 头部 SSO SaaS. |
| **SAML / OIDC** | 两种企业身份联合协议. |

### 数据源

| 术语 | 解释 |
|---|---|
| **SAP S/4HANA** ⭐ | SAP 现代 ERP 平台. Cloud 版有 OData API. |
| **SAP ECC** | SAP 老一代 ERP, 主要 BAPI / RFC API. |
| **OData v4** | SAP S/4 Cloud 的 RESTful API 标准. |
| **BAPI / RFC** | SAP ECC 的远程函数调用. |
| **SAP Cloud Connector** | 连接 on-prem SAP 和 cloud 的网关. |
| **SAP JCo / pyrfc** | Java / Python SAP RFC 客户端库. |
| **Salesforce (SFDC)** ⭐ | 头部 CRM SaaS. REST + Bulk API. |
| **SFDC governor limits** ⭐ | Salesforce 强制的 API 上限 (100K/24h free, 1M premium). |
| **SFDC org** | Salesforce 客户实例. |
| **Postgres** | 开源关系数据库. |
| **read replica** | 只读副本 — 减轻主库压力. |
| **Customer 360** | 客户全景视图 — 销售 + 服务 + 营销整合. |

### ETL / 数据架构 (这题反例)

| 术语 | 解释 |
|---|---|
| **ETL / ELT** | Extract-Transform-Load — 数据仓库经典. 这题不能用. |
| **Data warehouse / BigQuery** | 列式分析仓. |
| **Staleness** | 数据陈旧度 — ETL 通常 30min-6h 滞后. |
| **Federated query** | 联邦查询 — Trino / Presto 跨 source 直查. 慢但 real-time. |
| **Trino / Presto** | 联邦 SQL 引擎. |

### Caching / 性能

| 术语 | 解释 |
|---|---|
| **Per-user cache key** ⭐ | 缓存 key 包含 user_id — 不同 user 看不同数据时正确. |
| **Per-tool TTL** | 每个 tool 不同的 cache 时长. |
| **Semantic cache** | 语义缓存 — 相似 query 命中同 cache. |
| **Negative cache** | 负缓存 — 错误结果也短暂缓存, 防止 flood retry. |
| **Cache invalidation** | 缓存失效 — 数据变了如何清 cache. |
| **Cache hit rate** | 缓存命中率 — 这题目标 > 60%. |
| **Bulk API** | SFDC 的批量 API — 1 个 call 拿 10K 行. |
| **Governor limit** | SFDC API 24h 上限. |

### Schema / Discovery

| 术语 | 解释 |
|---|---|
| **Schema registry / Tool catalog** | 工具元数据中心. |
| **RAG over tool catalog** ⭐ | 用 vector search 从 1500 tool 里找 top-20 给 LLM. |
| **Vector DB (PGvector / Vertex AI Vector Search / Vertex AI Vector Search)** | 向量数据库. |
| **Embedding** | 把 query / tool description 转成向量. |
| **Tool eval suite** | 工具评估套件 — golden Q × expected tool sequence. |
| **Identifier mapping** | ID 映射 — SAP customer_id ↔ SFDC account_id. |

### 安全 / 沙箱

| 术语 | 解释 |
|---|---|
| **Safe SQL / Sandboxed SQL** | 受限 SQL 执行 — read-only + 表黑名单 + 行数上限 + 5s timeout. |
| **statement_timeout** | Postgres 单 query 超时. |
| **EXPLAIN cost** | Postgres 查询计划成本估算. |
| **SQL injection** | SQL 注入 — LLM 写 raw SQL 时风险. |
| **Audit log** | 审计日志 — 谁在何时调了什么 tool. |
| **Immutable store** | 不可变存储 — 审计日志写 WORM. |

### 部署 / 运维

| 术语 | 解释 |
|---|---|
| **VPC** | AWS 私有网络. |
| **Vertex AI** | AWS 托管 LLM 服务. |
| **OTel span chain** | 跨 service 的 trace 链. |
| **Dual-confirm UX** | 双重确认界面 — 写操作前 user 显式 confirm. |
| **Eval suite daily run** | 每日跑评估 — 检测 regression. |

### 业务术语

| 术语 | 解释 |
|---|---|
| **Overdue invoices** | 逾期未付发票. |
| **Accounts receivable aging** | 应收账款账龄. |
| **Collections** | 催收. |
| **Customer master** | 客户主数据 — SAP 概念. |
| **Lead / Opportunity / Account** | SFDC 销售概念: 潜客 / 商机 / 客户. |
| **Activity (SFDC)** | 互动记录 (电话 / 邮件 / 会议). |
| **SKU** | Stock Keeping Unit — 库存单位. |

---

## 这道题在考什么

不是考你 RAG, 是考你**异构数据源 agent 接入的 modern pattern**:

1. **Tool-per-source pattern** — 每 source 一组 tool, agent compose, 不是 fetch-then-LLM-join
2. **MCP server abstraction** — 2026 industry standard, 每 source 一个 MCP server
3. **Permission preservation** — user 在 SAP 看不到某 customer, agent 替 user 也不能
4. **Don't merge into one DB** (题目明确) — 知道为什么 ETL 死路 (real-time / 双倍维护 / staleness)
5. **Cross-source composition** — agent 要 join SAP order with SFDC contact, 这个 join 在 agent 端不是 DB
6. **Caching per source** — SAP 查询慢, Salesforce 有 governor limits, 必须 cache
7. **Schema discovery** — agent 怎么知道有哪些 table / field 可查
8. **菜鸟答案失败点**: "ETL 到 BigQuery" — 题目明说不要. "OpenAI function calling 50 个 function" — token cost 爆炸. "Text-to-SQL 单一 DB" — 不解决 3 个 source.

---

## 必问 clarifying questions

1. **Read or read+write**: agent 能改 SAP / SFDC 数据吗? 99% case 是只读, 影响 transaction / consistency 复杂度
2. **Real-time required?**: customer 1 分钟前更新 SFDC, agent 必须看到? 决定 cache TTL
3. **User identity**: agent run as user (per-user auth) or as service account?
4. **Query complexity**: agent 主要做 lookup ('show me customer X') 还是 aggregation ('top 10 by revenue')?
5. **SAP module**: 客户用的是 S/4 cloud (OData public) 还是 ECC (BAPI)? 决定 connector
6. **Volume**: agent 一天 10K queries 还是 1M? 影响 cache / cost
7. **Latency budget**: < 3s e2e 还是 < 30s OK? 影响是否 async + status check
8. **Existing IdP**: Okta? Azure AD? 决定 OBO flow

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|------|------|------|
| 1 | Clarify + reject ETL | 5 min | 锁 read-only / latency / 提为何 ETL 不行 | "题目说不要 merge, 我答应. 我会用 tool-per-source + MCP server pattern" |
| 2 | Anti-pattern critique | 5 min | 3 个 wrong way + 真正问题 | "ETL 死: real-time fail, permission lost, 双倍 maintain" |
| 3 | Tool-per-source pattern | 10 min | Each source = 1 MCP server, agent compose | "SAP MCP server, SFDC MCP server, PG MCP server" |
| 4 | Schema discovery + tool design | 10 min | Domain tools not raw SQL, RAG over tool catalog | "Domain tools 'get_customer', 不 raw 'SELECT * FROM'" |
| 5 | Permission preservation (OBO) | 8 min | Per-user token exchange, scope ≤ user | "OBO: user token → SF token, agent never has more权限" |
| 6 | Caching + governor limits | 7 min | Per-tool TTL, SFDC governor, semantic cache | "SFDC 100K API calls/24h 是 hard cap, cache critical" |
| 7 | Cross-source composition | 8 min | Agent orchestrates, not DB joins | "Customer 360: agent calls SAP + SFDC + PG, joins in memory" |
| 8 | Trade-offs + close | 7 min | Tool-per-source vs federated SQL vs ETL | "100K query/day 用 tools, > 10M 考虑 hybrid (cache layer = 'lite ETL')" |

---

## 端到端架构图 (ASCII)

```
                                User asks Agent:
                "show top 10 customers with overdue invoices and last interaction"
                                         │
                                         ▼
   ┌──────────────────────────────────────────────────────────────────────────────┐
   │  Agent (LangGraph / Claude Sonnet 4.6, runs as user identity)                │
   │   1. Decompose: need (a) overdue invoices, (b) customer info, (c) last log   │
   │   2. Tool discovery: search MCP gateway "invoices overdue customers"          │
   │   3. Plan: SAP.get_overdue_invoices(limit=10) → SFDC.get_customer_by_id      │
   │                                              → SFDC.get_last_interaction     │
   │   4. Execute, compose, respond with citations                                │
   └────────────────────────────────────┬─────────────────────────────────────────┘
                                        │  MCP JSON-RPC over HTTP
                                        ▼
   ┌──────────────────────────────────────────────────────────────────────────────┐
   │             MCP Gateway (central orchestration, runs in VPC)                  │
   │                                                                              │
   │   ▸ Auth: validate user JWT (from Okta)                                      │
   │   ▸ OBO token exchange: user JWT → SAP / SFDC / PG service token             │
   │   ▸ Tool discovery: RAG over tool catalog (1500 tools, return top-20)        │
   │   ▸ Rate limit per (user, source)                                            │
   │   ▸ Caching layer (Redis)                                                    │
   │   ▸ Trace propagation (OTel span chain)                                      │
   │   ▸ Audit log per tool call                                                  │
   └────────┬─────────────────┬──────────────────┬─────────────────────────────────┘
            │                 │                  │
            ▼                 ▼                  ▼
   ┌──────────────────┐ ┌────────────────────┐ ┌────────────────────┐
   │  SAP MCP Server  │ │  SFDC MCP Server   │ │  PG MCP Server      │
   │                  │ │                    │ │                     │
   │  Tools:          │ │  Tools:            │ │  Tools:             │
   │  - get_order     │ │  - get_account     │ │  - get_user_metric  │
   │  - search_orders │ │  - get_contact     │ │  - get_activity_log │
   │  - get_overdue_  │ │  - get_opportunity │ │  - get_custom_field │
   │    invoices      │ │  - search_activities│ │  - run_safe_query   │
   │  - get_inventory │ │  - get_case        │ │    (sandboxed SQL)  │
   │  - get_customer  │ │  - update_lead*    │ │                     │
   │                  │ │                    │ │                     │
   │  Auth:           │ │  Auth:             │ │  Auth:              │
   │  - OAuth2 client_│ │  - External OAuth  │ │  - JWT + RLS        │
   │    credentials   │ │    (user passthru) │ │                     │
   │                  │ │                    │ │                     │
   │  Transport:      │ │  Transport:        │ │  Transport:         │
   │  - OData v4 to   │ │  - SF REST API     │ │  - Postgres directly│
   │    S/4 Cloud     │ │  - Bulk API for big│ │    (no proxy)        │
   │  - BAPI to ECC   │ │                    │ │                     │
   └──────┬───────────┘ └──────┬─────────────┘ └────────┬─────────────┘
          │                    │                         │
          ▼                    ▼                         ▼
   ┌──────────┐         ┌────────────────┐       ┌──────────────┐
   │  SAP     │         │  Salesforce    │       │  Internal PG  │
   │  S/4HANA │         │  org + Lightning│       │  (read replica)│
   │  Cloud   │         │   API           │       │  + RLS        │
   └──────────┘         └────────────────┘       └──────────────┘

   Cross-cutting:
   ─ Caching (Redis): per tool, TTL configurable, semantic cache for similar queries
   ─ Audit: every tool call logged to immutable store
   ─ Observability: OTel trace per agent step, including tool calls
   ─ Schema registry: tool catalog with version, owner, change log
   ─ Eval suite: golden questions × expected tool sequence, daily run
```

---

## 详细设计 (60-min walkthrough)

### Phase 1: Clarify + reject ETL (澄清 + 拒绝 ETL 死路) (5 min)

开口:
- "Agent read-only or read+write? 我假设 99% read, 偶尔 write (SFDC update lead, SAP create order)"
- "Real-time: 1 min latency OK? 我假设是, SAP 1min cache OK, SFDC 30s, PG 5s"
- "Per-user permission preserved? — 假设是, agent run as user, OBO 流"

明确说: "题目说 'don't try to merge into one DB' — 这是好建议. 即使 ETL 到 BigQuery, 我会面对 3 个 problem: (1) latency 30min-6h 不 real-time; (2) permission flatten (RLS 在 SAP / SFDC 各有 model, ETL 后丢失); (3) 双倍 maintain (schema change in source → ETL → analyst 维护). Tool-per-source 是正解."

KPI:
- **Latency p99**: < 5s for single-source query, < 15s for cross-source (3 source compose)
- **Permission accuracy**: 100% (user 不应通过 agent 看到他在 source 里看不到的)
- **Tool call success rate**: > 95% (not network / API error)
- **Cache hit rate**: > 60% (cost saving)

### Phase 2: Anti-pattern critique (反模式批评) (5 min)

3 个常见 wrong way:

**Wrong 1: ETL 到 single warehouse**
- 30min - 6h staleness, agent 答不上 "5 min前我更新的 lead"
- Permission collapse: SAP / SFDC RLS 不易 reproduce in SQL warehouse
- 维护翻倍: schema 改 SAP / SFDC, 还要改 ETL
- Cost: 复制全部数据 + warehouse compute
- 只适合 BI / analytics, 不适合 transactional agent

**Wrong 2: 50 个 OpenAI function**
- 50 function schemas × 200 token avg = 10K prompt token, per call $0.05 just system prompt
- LLM "too many tools" 综合症, tool 误选率 30%+
- Schema 改一处, prompt 改一处, eval 跑全套
- 无 server-side catalog, hard to discover

**Wrong 3: Text-to-SQL 单一 DB**
- 假设数据能 union 进 single DB, 不成立 (SAP / SFDC 你不能 query 任意 table)
- SQL 安全 huge concern (SQL injection by LLM)
- 跨 source join unworkable

**Right: tool-per-source MCP**

3 个理由:
- Real-time: 每 source 直查, latency 1-2s
- Permission: OBO 让 user 自身权限 enforced by source
- Modular: schema 变只动一个 MCP server, 不动 agent

### Phase 3: Tool-per-source pattern (每个数据源一个 tool 模式) (10 min)

**3.1 MCP server per source**

每 source 一个 MCP server. 每 server 输出一组 domain tool (不是 raw SQL/API).

```python
# SAP MCP Server
from mcp.server import Server
server = Server("sap-s4hana")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="sap_get_overdue_invoices",
            description=(
                "Get list of overdue invoices in SAP S/4HANA. "
                "Returns invoices past their due date with customer info."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Optional SAP customer ID to filter"},
                    "days_overdue_min": {"type": "integer", "default": 0},
                    "limit": {"type": "integer", "default": 50, "maximum": 500}
                }
            }
        ),
        Tool(
            name="sap_get_customer",
            description="Get SAP customer master data including credit limit, address.",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "required": True}
                }
            }
        ),
        Tool(
            name="sap_get_inventory_for_sku",
            description="Get current inventory quantity for a SKU across all warehouses.",
            inputSchema={...}
        ),
        # 15-20 tools total per source
    ]

@server.call_tool()
async def call_tool(name, args):
    if name == "sap_get_overdue_invoices":
        # OData query on S/4 Cloud (or BAPI for ECC)
        query = f"/sap/opu/odata/sap/API_BILLING_DOCUMENT_SRV/A_BillingDocument?$filter=DueDate lt {today}"
        if args.get("customer_id"):
            query += f" and SoldToParty eq '{args['customer_id']}'"
        query += f"&$top={args.get('limit', 50)}"
        
        resp = await sap_client.get(query)  # auth via OAuth2 client creds
        return [TextContent(type="text", text=json.dumps(resp.value))]
```

**3.2 Why domain tools, not raw SQL/API**

- LLM 理解 `sap_get_overdue_invoices` (semantic) >> `POST /sap/odata/...` (syntactic)
- Tool author 把复杂 SAP OData query 写好, agent 只需选 tool + 填参数
- Schema 改时只改 tool 实现, 不改 prompt

**3.3 Tool count per source**

| Source | Tool count | 例子 |
|---|---|---|
| SAP S/4 | 20 | get_customer, get_order, search_orders, get_invoice, get_overdue_invoices, get_inventory, get_purchase_order, ... |
| Salesforce | 25 | get_account, get_contact, get_opportunity, get_lead, get_case, get_activity, search_activities, update_lead, ... |
| PG (internal) | 10 | get_user_metric, get_activity_log, get_custom_field, run_safe_query, ... |

Total ~55 tools. 太多让 prompt 装不下, 用 RAG over tool catalog (见 3.4).

**3.4 Tool discovery via RAG**

```python
@gateway.post("/mcp/tools/list")
async def list_relevant_tools(query: str, user: User):
    # 1. RBAC filter
    accessible_tools = [t for t in all_tools if user.can_access(t)]
    
    # 2. Vector search over tool descriptions
    query_emb = await embed(query)
    candidates = await vector_db.search(
        query_emb,
        top_k=30,
        filter={"tool_id": {"$in": [t.id for t in accessible_tools]}}
    )
    
    # 3. Re-rank by user history
    ranked = rank_by_usage(candidates, user)
    
    return ranked[:20]  # only top 20 to LLM
```

Tool descriptions 在 vector DB, query relevance + 用户偏好 → top 20 给 LLM, prompt 不爆.

### Phase 4: Schema discovery + tool design (Schema 发现 + 工具设计) (10 min)

**4.1 Tool design principle**

每 tool 要回答 4 个问题:
1. **What can I do** (single sentence)
2. **When should LLM call me** (use case examples in description)
3. **What input** (clear schema, types, examples)
4. **What output** (sample JSON, structure)

Good tool description:
```
sap_get_overdue_invoices: Returns SAP invoices past their due date.
Use when: user asks about late payments, accounts receivable aging,
collections priorities, or 'show overdue invoices'.
Returns: array of {invoice_id, customer_id, customer_name, amount, due_date, days_overdue}.
Limit: 500 per call. Filter by customer_id if known.
```

Bad tool description:
```
get_billing_doc: Retrieves billing documents from SAP.
```

**4.2 Composite tools (cross-table)**

Some questions need multiple SAP tables. Build composite tools rather than asking LLM to compose:

```python
@server.call_tool()
async def call_tool(name, args):
    if name == "sap_get_overdue_with_customer":
        # Composite: invoices + customer master + credit limit
        invoices = await sap_client.get("/billing/overdue")
        customer_ids = [i.SoldToParty for i in invoices]
        customers = await sap_client.batch_get("/customer", customer_ids)
        # Inline join
        return zip_invoices_customers(invoices, customers)
```

为什么 composite: 减少 LLM 串多 tool 的错误率, 减少 latency (1 tool call 比 3 快).

**4.3 Safe SQL tool (PG)**

PG MCP server 包一个 `run_safe_query` tool 让 agent 跑 ad-hoc SQL:

```python
@server.tool("run_safe_query")
async def run_safe_query(sql: str, user: User):
    # SAFETY:
    # 1. Read-only enforced via read-only PG user
    # 2. SET statement_timeout = '5s'
    # 3. Forbid certain tables (PII, secrets) at parser level
    # 4. Result row cap 1000
    # 5. EXPLAIN first, abort if cost > threshold
    
    parsed = sqlparse.parse(sql)
    if any_forbidden(parsed, user.access_blocklist):
        return {"error": "access denied to table X"}
    
    if uses_disallowed_syntax(parsed):  # no INSERT/UPDATE/DROP/CREATE
        return {"error": "only SELECT allowed"}
    
    async with pg_pool.acquire() as conn:
        # User identity for RLS
        await conn.execute(f"SET LOCAL ROLE {user.pg_role}")
        await conn.execute("SET LOCAL statement_timeout = '5s'")
        await conn.execute("SET LOCAL row_security = on")
        
        result = await conn.fetch(sql)
        if len(result) > 1000:
            return {"error": "too many rows, narrow your query"}
        
        return rows_to_json(result)
```

SAP / SFDC 不开 `run_safe_query` — 那些只能用 vendor API, 没 SQL access.

### Phase 5: Permission preservation (OBO) (权限传递 - On-Behalf-Of) (8 min)

**5.1 OAuth On-Behalf-Of**

Agent runs as user 身份. 流程:

```
1. User → Okta → Agent receives id_token + access_token (user-bound)
2. Agent → MCP Gateway with user JWT
3. Gateway: validate JWT → resolve user identity
4. Gateway → SAP / SFDC / PG: exchange user JWT for source-specific token
   - SAP: OAuth2 token exchange grant_type with SAP IdP
   - SFDC: SAML / OAuth assertion flow, user becomes SF user
   - PG: SET ROLE to user's role for RLS
5. Source executes query as USER, applies RLS / object permissions
6. Result returned, gateway audits, passes back to agent
```

Critical: agent never holds elevated permissions. If user can't see customer X in SFDC, agent can't show user customer X data either.

**5.2 Token exchange details**

```python
async def get_sap_token(user_jwt):
    # OAuth 2.0 Token Exchange (RFC 8693)
    resp = await sap_token_endpoint.post(
        grant_type="urn:ietf:params:oauth:grant-type:token-exchange",
        subject_token=user_jwt,
        subject_token_type="urn:ietf:params:oauth:token-type:jwt",
        audience="sap-s4-cloud",
        scope="read"
    )
    return resp.access_token  # scoped to user, expires in 1h

async def get_sfdc_token(user_jwt):
    # SF JWT Bearer Flow with user assertion
    assertion = sign_jwt({
        "iss": SF_CONSUMER_KEY,
        "sub": user_email,  # User's SF email
        "aud": "https://login.salesforce.com",
        "exp": now + 300
    }, private_key)
    
    resp = await sfdc_token_endpoint.post(
        grant_type="urn:ietf:params:oauth:grant-type:jwt-bearer",
        assertion=assertion
    )
    return resp.access_token
```

Cache tokens (Redis) by user, refresh before expiry.

**5.3 Permission edge cases**

- User has SAP access but not SFDC: agent answers only SAP, says "you don't have access to Salesforce data — please request from admin"
- User permissions change mid-session: cache TTL 5 min for permissions, re-check on critical operations
- Service account fallback: ONLY when user permission doesn't apply (e.g., background sync), explicit elevation with audit

**5.4 Audit trail**

Every tool call logged: `{user_id, tool, args_redacted, source, latency, status, ts}` to immutable store. Auditable for: did user X really access customer Y's data?

### Phase 6: Caching + governor limits (缓存 + API 调用配额) (7 min)

**6.1 Salesforce governor limits (real constraint)**

Salesforce hard limits per 24h:
- API calls: 100K per org (free) - 1M (premium edition)
- Concurrent requests: 25 (free)
- Bulk API records: 150M per 24h

Agent 没 cache 直接打 SFDC, 大客户 1 day 就 exhaust.

**6.2 Cache strategy per source**

| Source | Cache TTL | Why |
|---|---|---|
| SAP customer master | 24h | Slow-changing dim data |
| SAP orders | 5 min | Operational, freshness matters |
| SAP inventory | 1 min | Real-time critical |
| SFDC account | 1h | Sales data, daily-ish refresh OK |
| SFDC opportunity | 15 min | Sales pipeline updates |
| SFDC activity | 30 min | Logged history |
| PG metrics | 5 min | Operational |
| PG audit log | no cache | Recency critical |

**6.3 Cache key design**

```python
def cache_key(tool, args, user):
    # Include user_id for permission-aware caching
    arg_hash = sha256(json.dumps(args, sort_keys=True))
    return f"tool:{tool}:user:{user.id}:args:{arg_hash}"
```

Why include user_id: same tool + args but different user might get different data (RLS). Caching per user_id ensures permission correctness.

Cost: 多倍 cache space, but acceptable (Redis 便宜).

**6.4 Semantic cache (optional)**

Similar queries → same answer:
- "show top 5 customers by revenue" 和 "list 5 highest-revenue customers" 语义同
- Embed query, compare cosine sim > 0.95, return cached

但 risk: 不同意图 same embed → wrong cached answer. 限于 read-only + idempotent tool.

**6.5 Negative cache**

Tool fail with permission error → cache the fail for 5min (避免 flood retry). User permission change → invalidate.

### Phase 7: Cross-source composition (跨数据源组合查询) (8 min)

Question: "show top 10 customers with overdue invoices and their last interaction"

Agent plan:
```
Step 1: SAP.get_overdue_invoices(limit=10) → list of (invoice_id, customer_sap_id, amount)
Step 2: For each customer_sap_id, map to SFDC account_id (via PG mapping table or SFDC search)
Step 3: For each account_id, SFDC.get_last_activity(account_id) → last interaction
Step 4: Compose: zip SAP invoice + SFDC interaction by customer_id, format
```

LLM 在 plan + compose. Data join 在 agent memory (Python list comprehension), 不在 DB.

**Why agent compose, not DB join**:
- 3 source 不在同一 DB, 无法直接 SQL join
- Federated query (Trino) 慢, 复杂
- Agent compose 灵活, 同时 LLM 可以做 fuzzy match (customer name 不一致时 reconcile)

**Identifier mapping**:
SAP customer_id 跟 SFDC account_id 通常不同. 需要 mapping:
- 维护在 PG `customer_mapping(sap_id, sfdc_id, last_synced)`
- Daily sync (background job): SAP → SFDC by tax_id or email
- Tool `pg_get_sfdc_id_from_sap_id` 暴露给 agent

**Latency budget for cross-source query**:
- SAP get_overdue_invoices: 800ms (10 invoices)
- Mapping 10 ids in PG: 50ms (1 query)
- 10 × SFDC get_last_activity: 10 × 300ms parallel = 300ms (with cache hits, 50ms)
- Compose + LLM response: 1500ms
- Total: ~2.7s — OK with parallel + cache

Without parallel + cache: 800 + 50 + 3000 + 1500 = 5.4s — slow.

Parallel execution is key. Agent framework (LangGraph) supports parallel tool calls.

### Phase 8: Trade-offs + alternatives (权衡 + 备选方案) (7 min)

**Decision 8.1 — Tool-per-source vs federated query vs cached ETL**

| 选项 | Latency | Real-time | Complexity | Permission | When to use |
|---|---|---|---|---|---|
| Tool-per-source (我推) | 1-5s | Yes | Medium | Preserved (OBO) | Most cases |
| Federated query (Trino + connectors) | 5-30s | Yes | High | Hard | Heavy analytics |
| Cached ETL (BigQuery + sync) | <1s | No (30min stale) | High | Often flatten | BI dashboards only |
| Hybrid (cache common queries) | 0.5-3s | Mixed | High | Mixed | High volume |

Hybrid 是 staff-level — cache 常 queries 答案 in Redis (e.g., daily revenue), 不常 queries 现查. 但 cache invalidation 复杂.

**Decision 8.2 — Per-source MCP server vs single gateway**

| 选项 | Pros | Cons |
|---|---|---|
| Per-source MCP server (我推) | Modular, source-specific ops, easy to add new source | More services to run |
| Single gateway with internal routing | Less ops | Tight coupling, hard to evolve |

3 sources 现在, future 加 SAP HR module / Workday HR / ServiceNow — modular wins.

**Decision 8.3 — How to handle write operations**

| 选项 | Pros | Cons |
|---|---|---|
| Read-only agent (我推 default) | Safe | Limits agent value |
| Read-write with dual-confirm | More valuable | Complex consent UX |
| Read-write with sandbox first | Best | Complex (preview mode) |

Write is high-stakes. Default read-only. Add write tools (sf_update_lead) with explicit confirmation step in UI: agent shows "I'll update lead X with Y, confirm?" before action.

**Decision 8.4 — Schema change handling**

When SAP DBA adds new field:
- Old SAP MCP tool description doesn't know
- Plan: tool catalog auto-discovery 不可靠 (auto-generated tools too technical for LLM)
- Reality: manual update of tool description on quarterly cadence
- 自动: SAP / SFDC schema diff CI job → notify tool maintainer

**Decision 8.5 — Eval suite**

Daily golden:
- "Show me top 10 overdue customers" → expect SAP.get_overdue + SFDC.get_account + compose
- 100 golden questions × expected tool sequence
- Daily run with synthetic queries, real APIs (low traffic)
- Regression: tool sequence change OR wrong answer → alert

---

## 关键决策点 (with rationale)

1. **Tool-per-source MCP, not ETL** — real-time + permission + modular.

2. **Domain tools, not raw SQL/API** — LLM understands semantic > syntactic, tool author abstracts complexity.

3. **OAuth OBO, agent never elevates** — security red line, customer compliance ready.

4. **Per-source MCP server, separate process** — modular evolution, add new source easy.

5. **RAG over tool catalog (1500 tools, return top-20)** — solves "too many tools" without dropping coverage.

6. **Per-user, per-tool cache** — permission-aware caching, SFDC governor limits forced.

7. **Agent compose in memory, not DB join** — sources independent, agent flexibility.

8. **Composite tools for common cross-table SAP queries** — reduce LLM compose error rate.

9. **Safe SQL tool for PG only** — internal DB lets us sandbox, external SaaS no SQL access.

10. **Identifier mapping table maintained in PG, daily synced** — SAP / SFDC id alignment.

---

## 数字 (capacity sizing, cost math)

**Volumes**:
- 1000 enterprise users × 50 queries/day = 50K queries/day
- Cross-source avg 2.5 tool calls per query = 125K tool calls/day
- Per source split: SAP 40K, SFDC 60K, PG 25K calls/day

**SFDC governor**:
- 100K cap, we use 60K → 40K headroom OK
- Cache hit rate 60% → 60K → 24K actual SFDC calls

**Cache infrastructure**:
- Redis cluster (3 node, r6g.xlarge): $500/month
- Memory: 50K queries × 1KB avg = 50MB hot, 1GB total with growth
- Hit ratio target: > 60%

**MCP servers** (per source, K8s pod):
- SAP MCP server: 4 pods × m6i.large = $400/month
- SFDC MCP server: 4 pods × m6i.large = $400/month
- PG MCP server: 2 pods × m6i.large = $200/month

**Gateway**:
- 4 gateway pods × m6i.xlarge = $800/month

**LLM cost** (Claude Sonnet 4.6 in customer Vertex AI):
- 50K queries/day × avg 4K in + 500 out = 200M in + 25M out / day
- Per day: $0.6 in + $0.375 out = ~$1/day per user
- 1000 users × $1 × 30 = $30K/month — main cost driver

**Total**: ~$32K/month infra + LLM

**Per-query cost**: $32K / (50K × 30) = $0.02 — acceptable for B2B

**Latency budgets**:
- Single source query: < 3s p99 (e.g., "show SAP customer X")
  - Auth + tool lookup: 200ms
  - SAP API call: 1500ms
  - LLM compose: 1000ms
- Cross source (3 sources): < 8s p99
  - Parallel tool calls: 1500ms max
  - LLM compose: 1500ms
  - Multiple turns possible: 3-5s

---

## Gao Xin 简历专属 reframe

1. **TikTok Internal Agent Platform (50+ services)** — 你直接做过这道题, 50+ service MCP tool abstraction. 写下 "我做过 prod 5K+ user agent platform 接 50+ internal services, MCP-pattern tool gateway".

2. **TikTok PayLater BNPL chatbot** — RAG + intent routing + tool calling, 直接相关.

3. **ConvFinQA multi-hop** — agent compose across sources, you 跑过 multi-hop with citations.

4. **BytePay financial system integration** — 你接过 SAP-like ERP, OBO 你做过.

5. **Voice agent 7 markets** — multi-tenant + per-market data isolation, OBO pattern 你跑过.

reframe: "我在字节做 Agent Platform 接 50+ service, 这道题 3 个 source 是 simpler version. 我会直接套 MCP gateway pattern. 增量: SAP S/4HANA OData 我不熟 (字节内部不用 SAP), 我会找 SAP consultant 培训 1 周. Salesforce / Postgres 都熟."

---

## 5 个 Follow-ups

1. **"如果 user 问 '最贵的 SKU 在哪个 warehouse 库存 < 10', 需要 SAP price + inventory + warehouse 3 个 API, agent compose 慢, 怎么办?"** — 答: (a) 加 composite tool `sap_get_low_stock_high_value_items(min_price, max_stock)` — server 端做 join 更快; (b) 加 parallel tool call (LangGraph 支持); (c) 长期 cache 高 value SKU 列表; (d) 如果 query 太常用, 考虑物化 view in SAP (DBA 配合).

2. **"SAP S/4HANA on-prem (ECC), 没 OData, 只有 BAPI / RFC, MCP 怎么接?"** — 答: 走 SAP Cloud Connector (between on-prem and cloud) + BAPI wrapper. MCP server 跑在客户 VPC, 通过 SAP JCo (Java Connector) or pyrfc 调 BAPI. Tools 跟 OData 版本 same interface, internal 实现不同. 性能略差 (BAPI 1-3s vs OData 500ms).

3. **"我们 agent 想 'create SAP order', 怎么做 write?"** — 答: (a) Tool `sap_create_order` with confirmation UX (agent 不直接 create, 先 show user "I'm about to create order X with items Y, total $Z, confirm?"); (b) Idempotency: user-provided idempotency_key, dedup 24h; (c) Audit: full payload + user_id + ts → immutable log; (d) Optimistic lock or pre-check: get current inventory before order; (e) Rollback path: if order create succeeds but downstream fail, easier to write SAP cancel-order tool for compensation.

4. **"SFDC governor 100K 24h cap, 大 customer 1 day 用完, 怎么 protect?"** — 答: (a) Per-tenant rate limit at gateway, paid > free; (b) Cache aggressive (1h account, 24h customer master); (c) Bulk API for batch operations (1 API call returns 10K records); (d) 预先 schedule heavy analytics overnight; (e) Premium SFDC tier $3K/month gets 5M cap; (f) Track per-user API usage in dashboard, alert at 80% of 24h cap.

5. **"如果 customer 同时 use SAP + SFDC + custom PG + Workday HR + BigQuery DWH + 5 more sources, 我们怎么 scale tool catalog?"** — 答: (a) Tool catalog 用 vector DB (Vertex AI Vector Search/Vertex AI Vector Search/PGvector), 不再 prompt-include, RAG retrieve top-20 per query; (b) Hierarchical: domain → category → tool (LLM 先选 domain "finance" 再选 tool "sap_get_invoice"); (c) Tool ownership: each source has team owner, version tool descriptions; (d) Per-tenant catalog: customer 选启用哪些 tools, 减小 their catalog; (e) Tool eval suite: golden questions × expected tool, daily regression.

---

## ❌ 死路答法

1. **"ETL 到 BigQuery"** — 题目明说不要, 直接挂.
2. **"50 个 OpenAI function 在 prompt 里"** — token cost 爆炸 + tool 误选高.
3. **"Text-to-SQL 跨 3 个 source"** — federated SQL 慢复杂.
4. **"Service account (admin) 给 agent, simple"** — 失去 permission preservation, 违反客户 SOC 2.
5. **"用 LangChain 默认 tool"** — 没 schema, 没 permission, demo OK production 不行.
6. **"无 cache, 实时直查"** — SFDC governor 立刻 trip.
7. **"agent 写 raw SAP OData URL"** — LLM 出错率高, schema 变就崩.
8. **"无 audit log"** — compliance 不过.
9. **"composite tool? agent 自己 compose"** — agent 错误率高 (LLM hallucinate column name), composite 必要.
10. **"new source 加 = 新 LangChain tool 在 main repo"** — 不模块化, 改一个 source 影响所有.

---

## ✅ 加分项

1. **拒绝 ETL 并解释 3 个理由** — 直接 signal 真懂 trade-off
2. **MCP tool-per-source pattern** — 2026 industry standard
3. **OBO + per-source token exchange** — security 严肃
4. **RAG over tool catalog** — scalability 设计
5. **Per-user-per-tool cache** — permission-aware caching, SFDC governor aware
6. **Composite tools for common cross-table** — reduce LLM compose error
7. **Safe SQL tool only for PG (sandboxed)** — pragmatic balance
8. **Agent compose in memory, parallel tool call** — modern agent framework
9. **Identifier mapping table + daily sync** — real-world cross-source pain
10. **Eval suite (golden Q × expected tool sequence)** — production hygiene

---

## 一句话总结

异构数据源给 agent 用不是 "合并到一处", 是 **per-source MCP server + domain tool + OAuth OBO + RAG-over-tool-catalog + per-user-per-tool cache + composite tools for common cross-table + agent compose in memory + identifier mapping + daily eval suite**, 让 agent 像 navigator 调 3 个 source 而不是 ETL into 1.

---

## Cheat Sheet

```
Pattern: Tool-per-source MCP

Per source MCP server:
  SAP S/4HANA  : 20 domain tools (OData v4 client_credentials OAuth2)
  Salesforce   : 25 domain tools (REST + Bulk API, External OAuth)
  Postgres     : 10 domain tools + run_safe_query sandboxed
  
Gateway:
  - User JWT (Okta) validation
  - OBO token exchange per source
  - RAG over tool catalog (return top-20)
  - Rate limit per (user, source)
  - Cache per-user-per-tool
  - OTel trace + audit log

Cache TTL:
  SAP customer master:  24h
  SAP orders:           5m
  SAP inventory:        1m
  SFDC account:         1h
  SFDC opportunity:     15m
  PG metrics:           5m
  PG audit log:         no cache

Volumes:
  1000 user × 50 q/day = 50K queries/day
  Avg 2.5 tool calls per query = 125K tool calls/day
  Cache hit 60% → 50K actual source calls

SFDC governor:
  100K cap × 60% cache hit + bulk API → 24K actual ≪ 100K ✓

LLM cost (Claude Sonnet 4.6 via Vertex AI):
  50K queries × 4K in + 500 out = $30K/month
  Total all-in: ~$32K/month
  Per query: $0.02

Latency:
  Single source: < 3s p99
  Cross-source (3): < 8s p99 (parallel tool call critical)

OBO flow:
  User → Okta → user JWT
  Gateway → SAP token endpoint (RFC 8693 token exchange)
  Gateway → SFDC token endpoint (JWT Bearer with user assertion)
  Gateway → PG SET ROLE for user RLS
  All source queries scope to user permission

Anti-patterns:
  ETL: staleness + permission flatten + double maintain
  50 functions in prompt: token cost + tool误选
  Text-to-SQL: SQL injection by LLM, no cross-source

Schema discovery:
  Tool catalog in vector DB (PGvector)
  PR-based tool definition change
  Quarterly schema diff CI from source vendor
  Daily eval: 100 golden Q × expected tool sequence

Write operations:
  Default read-only
  sf_update_lead etc. with dual-confirmation UX
  Idempotency key + audit
```
