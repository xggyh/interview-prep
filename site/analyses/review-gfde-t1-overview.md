## T1 · Agent Tool Calling 全景 — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/gfde-t1-overview.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t1-overview.html`](questions/gfde-t1-overview.html)

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.
> 不含 prose, 全是 compressed structure (tables / code / one-liners).

### 核心心智模型 (1 sentence)

Tool call = 跨边界 side-effect 投影. LLM 发意图 → runtime 跨网络执行 → 不保证次数 / 不保证成功 / 数据 untrusted / 可能并发 / 可能 destructive. 它是 **distributed system + security 问题**, 不是 ML 问题.

### 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Tool call | LLM emit 的跨边界意图 (JSON) | 区别 function call |
| Idempotency key | deterministic hash 标识 1 次意图 | 任何 retry-able write |
| Dedup window | server 记住 key 的 TTL | 5min / 1h / 24h / permanent 多 tier |
| At-least-once | 至少 1 次, 可能多次 | 网络默认保证 |
| Exactly-once | 不存在; 用 at-least-once + idempotent 模拟 | 业务层 |
| Circuit breaker | failure 高时主动停, 给下游恢复 | 任何外部依赖 |
| Fallback ladder | 主挂 → alt tool → cache → degraded → human | 任何 critical path |
| Bulkhead | per-tenant 资源隔离 | multi-tenant SaaS |
| MCP | Anthropic 协议, tool-as-server 跨 vendor | platform 产品 |
| Provenance | tool output 的 source / trust / ts metadata | 给 LLM 决定信任 |
| Confirm gate | UI 强制 human-in-loop 拦截 destructive | high stakes |
| Blast radius | 一次操作影响范围 (实体数 / $ / 人) | 限 destructive 上限 |
| Compensating action | reverse 一个 op (refund / restore) | Saga pattern |
| Outbox | DB 同事务写 intent + 执行 | atomicity |
| Hash chain audit | 每 entry 含 prev_hash 防篡改 | compliance |
| ReAct | 一 turn 一 tool, 看结果决定下一步 | 多步推理 |
| Plan-then-execute | 先列计划, 再批量执行 | 省 LLM call |
| Multi-tool parallel | 一 turn emit N tool call | read-heavy fanout |

### N 个核心 framework / pattern

**Pattern A: Idempotency Key**
- When: 任何 retry-able 写
- Algorithm: hash(tenant + session + tool + canonical_args) → Redis SETNX in_flight → execute → mark completed → DB unique 兜底
- Trade-off: short TTL 防 logical collision vs long TTL 防 stale retry
- Tools: Redis SETNX, BLAKE2b-128, Postgres UNIQUE, Stripe Idempotency-Key header

**Pattern B: Layered Retry**
- When: tool 调外部 API
- Algorithm: L1 transport (1 retry, 500ms) → L2 wrapper (3 retry, exp 100/300/1000ms ±20% jitter) → L3 agent fallback ladder
- Trade-off: retry storm risk → 20% budget cap
- Tools: httpx HTTPTransport, tenacity, asyncio.wait_for

**Pattern C: Parallel-safe vs Sequential split**
- When: LLM emit 多 tool 一 turn
- Algorithm: annotate read/write → static DAG → wave-by-wave parallel + per-resource Redis lock (sorted by key, fenced token)
- Trade-off: 全 serial 慢 / 全 parallel race
- Tools: asyncio.gather(return_exceptions=True), Redis Redlock, ZooKeeper

**Pattern D: Confirm-Required Wrapper**
- When: irreversible / high $ / high-reputation
- Algorithm: tool 注 requires_confirm + threshold → runtime 拦截 → UI render preview → user Y/N → execute or skip
- Trade-off: fatigue vs safety → progressive trust + tier-based
- Tools: Slack interactive blocks, async approval ticket, PagerDuty

**Pattern E: Sandboxed Tool Output**
- When: 任何 tool. 没例外.
- Algorithm: Pydantic validate → size cap (top-N + blob_ref) → injection scan (regex+LLM) → PII redact (Presidio) → XML wrap + system_reminder + provenance
- Trade-off: FP block legit vs FN allow injection
- Tools: Pydantic v2, Presidio, garak, tiktoken, DuckDB query_blob

### 关键决策树 (ASCII)

```
你的 tool 有 side effect?
├─ No (read-only)
│   └─→ Pattern C parallel + E output validate
└─ Yes (write/destructive)
    ├─ Reversible (update DB row)
    │   └─→ A idem + B retry + E
    └─ Irreversible (send email / charge)
        ├─ Low $ / low risk
        │   └─→ A + B + E
        └─ High $ / high risk
            └─→ A + B + D confirm + E + audit + compensate
```

```
Tool output > 4K tokens?
├─ No → full content
└─ Yes
    ├─ < 40K → truncate top-N + summary
    ├─ < 400K → top-N + blob_ref + query_blob tool
    └─ > 400K → blob_ref only + sample 5 + schema
```

### Part 2 五个深度问题速查 (overview 角度 - 6 阶段生命周期)

**Stage 1: Registration**
- 核心解法: 3 种注册 (static @tool decorator / dynamic DB / MCP server)
- Top 3 gotchas:
  1. Description 缺 when/when-not/example → LLM 选错
  2. JSON schema 没 regex/enum → arg 错传
  3. 无 schema_version → upstream 改 schema 旧 agent 调坏
- Tools: Pydantic, JSON Schema, MCP spec, AST lint

**Stage 2: Discovery**
- 核心解法: filter by perm → intent semantic match → recent usage → cost budget → top 10-20 to LLM
- Top 3 gotchas:
  1. 一股脑塞 100 tools → token 浪费 + LLM 困惑
  2. RBAC filter 漏掉 → 调到禁用 tool
  3. Cost budget 没过滤 → 选了 $5/M Opus 做 $0.5/M Flash 就够的事
- Tools: embedding 相似度 (text-embedding-3), per-tenant tool catalog, intent classifier

**Stage 3: Planning**
- 核心解法: ReAct (灵活, 贵) / Plan-then-execute (省 LLM call, plan 错重做) / Multi-tool parallel (快, 要 runtime 处理并发)
- Top 3 gotchas:
  1. 全 ReAct 时 read-heavy 场景慢 5x (LLM call 串行)
  2. Plan-then-execute plan 错全 re-plan
  3. Multi-tool parallel runtime 没调度 → race
- Tools: LangGraph, AutoGen, OpenAI Assistants

**Stage 4: Invocation**
- 核心解法: authorize → dedup → rate_limit → confirm → dispatch → timeout → audit → return
- Top 3 gotchas:
  1. Authorize 用 platform token (越权)
  2. Rate limit 全局而非 per-tenant (噪声邻居)
  3. Timeout 没分 tool 配置 → p99 全 fail
- Tools: Vault token delegation, Redis token bucket, OpenTelemetry per-stage span

**Stage 5: Result Handling**
- 核心解法: schema validate → size truncate → sanitize PII → XML wrap → metadata (freshness/cost/source)
- Top 3 gotchas:
  1. String concat 进 prompt → tag injection
  2. Raw 不 truncate → context 爆
  3. 无 provenance → LLM 把 stale 当 fresh
- Tools: Pydantic, Presidio, tiktoken, blob ref

**Stage 6: Continuation**
- 核心解法: max_iterations (20) + cost cap ($1/session) + dedup detection (same tool same args 3x → escalate)
- Top 3 gotchas:
  1. 无 cost cap → infinite loop $$$ 爆
  2. 无 dedup detection → LLM stuck retry 同 tool
  3. 无 max_iterations → agent 永远不停
- Tools: Per-session cost meter, agent_step graph cycle detect

### Production gotchas (top 15)

1. Stale tool result — 加 `fetched_at` field + prompt 提醒
2. Description ambiguous — when/when-not/example 缺一即错
3. N+1 tool calls — 提供 batch API + `prefer_batch=True` flag
4. Cycle (A→B→A) — max_depth 5 + stack 含同 tool 检测
5. Hot key contention — per-resource serializer queue
6. Prompt injection via tool output — XML wrap + `<system_reminder>` + Claude/Gemini 较 robust
7. Cost runaway — per-session $cap + alert at 80%
8. Permission escalation — agent token = min(platform, user), audit actor + on_behalf_of
9. Schema drift — tool spec `schema_version` + runtime reject mismatch
10. 200 OK but body is `{"error":...}` — 检查 body status field 不只 HTTP code
11. Timeout 太短 — per-tool p99 监控 auto-tune
12. Error message blow — 结构化 `{"error_code":"RATE_LIMIT","retry_after":30}`
13. LLM 当 tool 失败 silent retry → 双花 (link idempotency)
14. Parallel write 同 entity → race (link parallel-race)
15. Untrusted tool output 进 prompt → injection (link tool-output-validation)

### 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Idempotency | Voice agent 7 markets | "Deterministic key on (user, intent, args canonical), Redis 24h + bank ledger 永久, 7 markets 双花从 3/month → 0" |
| Retry/Fallback | BNPL chatbot | "3 层 retry, layer 2 cache 必须标 `_stale_warning`, LLM 自信 hallucinate fresh 是最大坑" |
| Parallel/Race | BNPL multi-tool fanout | "5 sub-agent fanout, 4 read parallel asyncio.gather, 1 write serialize per user_id lock, return_exceptions partial OK" |
| Destructive | Indonesia refund tier | "3 tier: <$50 auto, $50-200 客服 confirm, >$200 manager+ledger; 24h 内多 refund 自动升 tier" |
| Output validation | ConvFinQA calculator | "Pydantic float + NaN/Inf check; inf bug → `if isinf(v): raise InvalidToolOutput`" |
| MCP abstraction | Internal Agent Platform | "ByteDance 内部 shared tool catalog versioning + per-team perm + per-tool cost meter" |

### 面试现场 quotables (top 8)

> "Tool call 不是 function call. 它是 distributed system + security 问题, 不是 ML 问题. 这是 2026 production FDE 视角."

> "Exactly-once tool call 不存在. 工程上是 at-least-once + idempotent consumer = 业务层 exactly-once."

> "Idempotency key 必须 runtime 生成不是 LLM 生成. LLM sampling 不确定, 同意图可能不同 key. Tenant + session + tool + canonical(args) hash."

> "Layered retry 不只 1 层: transport (500ms, conn err) + wrapper (5s, 5xx/429) + agent (alt tool / cache / human)."

> "Parallel-safe 看 (tool_name, resource_id) 对. update_user(u1) 和 update_user(u2) parallel, 但 update_user(u1, name=A) 和 update_user(u1, email=B) 必须 serialize."

> "Tool output 是 untrusted. 即使 tool 是自家的, 它返回的 data 可能来自 user note. XML wrap + system_reminder 是底线."

> "Confirm-on-every-action = confirmation fatigue. Progressive trust + tier-based 是关键."

> "MCP 是 2026 vendor-neutral 标准. Customer internal API 包成 MCP server 是 FDE 主流交付物."

### 红线 (top 10 anti-patterns)

1. "Exactly-once tool call" — 网络环境下不存在
2. LLM-generated idempotency_key — 不确定性
3. Trust tool output as instruction — prompt injection 灾难
4. Retry on 4xx (except 408/425/429) — 永久错误浪费
5. No backoff — thundering herd
6. Confirm-on-every — fatigue → 麻木 Y
7. Tool description 短 — LLM 选错反而贵
8. Single vendor LLM no failover — outage = 全栈瘫痪
9. Silent fallback - user 不知 result degraded
10. Tools 不分级 (read/write/destructive 一锅) — destructive 被当 read 用
