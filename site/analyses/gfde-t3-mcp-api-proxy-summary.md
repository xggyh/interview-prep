# 🔌 T3.2 · MCP (Model Context Protocol) / API Proxy 抽象 — 冲刺版

> 完整版: [gfde-t3-mcp-api-proxy.html](gfde-t3-mcp-api-proxy.html). 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: multi-vendor LLM (Claude + Gemini + GPT-5.5), 50 internal microservice × 10 endpoints = 500 tools, OAuth + on-behalf-of, quarterly schema change, 2s latency budget per tool call, multi-tenant SaaS."

**核心 framing**: 不要把 50 个 API hardcode 到 LLM prompt (25K token prompt + 30% 误选率). 走 **MCP-based Gateway** = 2026 industry standard.

### Layer 1: MCP 3 原语 (vs OpenAI function call)

```
Resources : 只读数据  file://docs/policy.md, db://users/42
Tools     : 可执行函数 create_order, send_email
Prompts   : 可复用模板 "summarize_meeting_notes"
```

MCP (Anthropic 2024 开源, 2026 业界标准) = vendor-neutral, 跨 Claude/Gemini/GPT. JSON-RPC over stdio/HTTP/SSE/WebSocket. OpenAI function calling 只对应 Tools, 没 Resources/Prompts.

### Layer 2: Gateway 6 责任 (统一入口)

```
1. Tool discovery   RAG over tool descriptions (Qdrant + RRF)
2. Auth + OBO       OAuth scope exchange (RFC 8693), token broker
3. Rate limit       Token bucket per (user, tool, tenant)
4. Observability    OTel trace propagation end-to-end
5. Caching          Idempotent reads, per-tool TTL
6. Versioning       Schema diff CI + adapter chain + 90-day deprecation
```

### Layer 3: 500 tools 怎么 discovery (LLM context 装不下)

```python
async def list_tools(user, query):
    accessible = await rbac.tools_for(user)         # L1 RBAC filter
    if query:
        emb = await embed(query)                     # L2 RAG search
        candidates = await qdrant.search(emb, top_k=50,
            filter={"tool_id": {"$in": accessible}})
    ranked = rank_by_usage_history(candidates, user) # L3 历史加权
    return ranked[:20]                               # 返 top-20
```

**4 层 discovery**: RBAC → RAG → Hierarchical (domain→category→tool) → meta-tool `find_tool`. 实战: tool 选率 70% → 92% after RAG + history boost.

### Layer 4: OBO (enterprise 红线)

```python
service_token = await oauth.exchange(
    user_token=req.user_token,
    target_service=tool_meta.service,
    scopes=tool_meta.required_scopes,  # scope ≤ user's perms
)
# Agent 永远不能拥有比用户更高权限
```

Agent service principal 不直接调 API. 每次走 token broker 换 service_token, scope ≤ user 权限. Bug 时 agent 不能越界. RFC 8693 OAuth 2.0 token exchange.

### Edge cases

- **EC1 Customer schema 季度升级 break agent**: semver 在 tool spec + adapter chain v1↔v2 + 90-day deprecation + schema diff CI + daily eval suite alert pass rate drop.
- **EC2 MCP server crash**: per-server circuit breaker (10 fails/min → open 5min cooldown). Health check 30s. Agent 收到 ToolUnavailable, fallback / degraded.
- **EC3 Auto-gen MCP from OpenAPI**: 不要做. OpenAPI summary 写给 dev 太技术 ("Returns 200"), LLM 选不对. 人手 curate description + use case examples, ~1 day per service.
- **EC4 Latency sub-100ms 不允许 MCP overhead**: 预取 token (OBO cache 10min) + Redis Lua rate limit (1ms) + sidecar pattern (Envoy ext_authz) 把 overhead 降到 ~5ms.
- **EC5 Legacy mainframe COBOL 没 modern API**: 3 fallback — 3270 screen-scrape (read-only) / CDC stream Debezium / 文件 drop S3 daily batch. Plus graceful degradation: tier-1 real-time → tier-2 cached → tier-3 analytics replica → tier-4 "unavailable".

### Production hardening

- **Trace propagation**: OTel `traceparent` header inject before forward. E2E: agent → gateway → MCP server → real API.
- **Cost attribution**: per-span tag (tenant_id, tool_id), monthly bill auto-gen.
- **Cache policy**: idempotent read cached (per-tool TTL), write 永不 cache, per-user namespace 隔离敏感数据.
- **Eval suite**: 200-500 golden cases per tool, daily run, alert on pass rate drop > 5pp.

### 🪝 Resume hook

"On ByteDance Internal Agent Platform we built 200+ tool catalog (pre-MCP, rolled JSON-RPC), 50 services × 4 avg endpoint. RAG-based discovery 把 LLM context 35K → 4K token (每 call 省 $0.06), tool 误选率 30% → 8%. OBO 通过 token broker 实现 — early version agent 有 admin scope, security review caught, 3 周建 broker. Voice agent 7 markets 每 market 独立 OAuth scope. 这就是 staff-level MCP/gateway 设计."

---

## 🔥 5 Follow-ups

**Q1: MCP overhead - extra hop latency cost?**
Single proxy hop ~5-20ms (HTTP + JSON-RPC serialize). Auth + OBO ~1-2ms cached / 50ms cold. Rate limit Redis Lua 1-2ms. Observability inject <1ms. 总 ~10-25ms — 2s budget 完全 OK. Sub-100ms 硬需求: OBO cache 10min + sidecar Envoy ext_authz.

**Q2: Customer API 变更 break agent. 怎么 handle?**
(1) semver 在 MCP tool spec; (2) adapter chain v1↔v2 declarative or code; (3) deprecation warning in response 90-day window; (4) eval suite daily alert pass rate drop; (5) customer 自动 notification (email + dashboard); (6) schema diff CI check — breaking change without major bump = PR fail.

**Q3: 500 tools 怎么处理 beyond RAG?**
Hierarchical (domain → category → tool, LLM 2-call 选). Per-agent specialization (support agent 只看 support tool). Per-user RBAC pre-filter before RAG. Meta-tool `find_tool` 让 LLM 主动调. Usage history boost (recent + frequent rank higher). Hybrid BM25 + dense embedding RRF.

**Q4: MCP vs OpenAI function calling 何时选?**
OpenAI function call: in-process, 单 vendor, fast, 简单. LLM-side 协议. MCP: cross-process, vendor-neutral, 有 versioning, dynamic discovery, Resources + Prompts. Tool-side 协议. **互补不互斥** — MCP tool def 可 adapter 转 OpenAI function format. 选 MCP 当 multi-vendor / customer-owned tools / long-term platform / dynamic discovery.

**Q5: Prompt injection / tool abuse 风险 with MCP?**
MCP 不变好坏, 但抽象层是 enforce 策略最佳位置. (1) Tool description sanitize (LLM 读 description = 注入面); (2) arg schema validate before call; (3) OBO scope 兜底 (LLM 被骗也限权限); (4) 敏感 tool 必须 user explicit confirm (`send_email`, `transfer_money`); (5) audit log every call; (6) rate limit + quota 防 burn budget. Gateway 是 chokepoint, 安全实施在这里.

---

## ❌ 易错点 (10 条红线)

1. **Hardcode 500 tools in LLM context** — token cost + selection accuracy 暴跌
2. **Agent has direct API access** — 无 OBO, scope creep, security review fail
3. **No tool discovery** — agent 不知用哪个 tool, error 多
4. **Auto-gen MCP from OpenAPI** — description 太技术, LLM 选错
5. **No versioning** — customer schema 变更直接 break agent
6. **No circuit breaker per server** — 一个 server 挂 → agent 死循环 retry
7. **MCP 当 LLM 协议** (concept 混淆) — MCP 是 tool-side, function calling 是 LLM-side
8. **Cache all tool outputs** — write op 不能 cache, 灾难
9. **OAuth token broker 缺失** — agent 用 user_token 直接调所有 service (安全事故)
10. **No trace propagation** — debug agent flow 不可能

---

## ✅ 加分项 (12 条)

1. **MCP 3 原语** (Resources / Tools / Prompts) awareness
2. **Gateway 6 责任** 清晰列举
3. **OBO** as enterprise standard, **RFC 8693** OAuth token exchange by name
4. **RAG-based discovery** + embedding + RRF + recency boost
5. **Hierarchical / meta-tool** 替代方案 for 500+ tools
6. **Adapter pattern** for non-MCP-native APIs (~1 day per service)
7. **Versioning strategy** + deprecation 90-day window
8. **Eval suite + schema diff CI** for drift detection
9. **OpenTelemetry trace propagation** end-to-end
10. **Legacy 4 patterns** (REST adapter / 3270 scrape / file drop / graceful degrade tier 1-4)
11. **2026 vendor-neutral** (Anthropic + Google + OpenAI 都支持 MCP)
12. **Quote Internal Agent Platform 70 → 92% tool accuracy**

---

## 一句话总结

**MCP-based Gateway 是 2026 LLM agent integration 事实标准**: 一个统一入口 + 3 原语 (Resources/Tools/Prompts) + 6 责任 (discovery/auth/RL/obs/cache/version). 500 tool 用 RAG discovery + RBAC + 历史加权. 50 service 用 1 天/服务 adapter. Schema 演化用 version + adapter chain + 90 day deprecation. OBO 保证 agent 权限 ≤ 用户权限. 这是 staff-level platform 设计.

---

## 🃏 Cheat Sheet (印 1 页随身)

```
MCP (Model Context Protocol):
  Anthropic 2024 开源, 2026 业界标准
  Vendor-neutral (Claude + Gemini + GPT)
  3 primitives: Resources / Tools / Prompts
  JSON-RPC over stdio / HTTP / SSE / WebSocket

Gateway 6 责任: Tool discovery (RAG) + Auth+OBO (OAuth exchange) + Rate limit (per user×tool×tenant) + Observability (OTel propagation) + Caching (idempotent reads) + Versioning+adapter

500 tools discovery: L1 RBAC filter + L2 RAG vector top-20 + L3 Hierarchical (domain→category→tool) + L4 Meta-tool find_tool + usage history boost + RRF (dense+BM25)

OBO (On-Behalf-Of):
  User token → exchange service token, scope ≤ user
  RFC 8693 OAuth 2.0 token exchange
  Agent never more perms than user

Adapter pattern: REST → MCP wrapper ~1 day/service, hand-curate description (NOT auto-gen OpenAPI), translate args + error codes

Versioning: semver in tool spec + adapter chain v1↔v2 + 90-day deprecation + schema diff CI + daily eval suite

Legacy: REST→adapter modern / Mainframe→3270 scrape read-only / Batch→file drop S3 / always graceful degrade tier 1-4

Cache policy: idempotent read cached w/ TTL, write NEVER cached, per-user isolation, semantic for fuzzy

Trace: OTel `traceparent` header inject before forward, E2E agent→gateway→mcp→real api

Circuit breaker: per-MCP-server CB, 10 fails/1min → open 5min cooldown, health check 30s

Cost: per-call LLM + tool + obs overhead, tag span tenant_id+tool_id, monthly bill auto-gen

When NOT MCP: single vendor + small tool + greenfield / sub-100ms hard / stateful SSH long-running
When MCP: multi-vendor / customer-owned tools / long-term platform / need dynamic discovery

Discovery accuracy (your Internal Agent Platform):
  Without RAG 70% tool selection / With RAG+history 92%
  Context 35K → 4K token (per-call save $0.06)

红线:
  - All tools in LLM prompt
  - Agent direct API call (no OBO)
  - No tool discovery
  - Auto-gen from OpenAPI
  - No versioning
  - No circuit breaker
  - Cache writes
  - No trace propagation
  - MCP = function calling 概念混淆

Resume quotes:
  "Internal Agent Platform 200+ tools, 70→92% accuracy via RAG"
  "Voice agent 7 markets per-tenant OBO"
  "BNPL chatbot intent → tool routing"
  "Pre-MCP rolled own JSON-RPC, lesson learned"
```
