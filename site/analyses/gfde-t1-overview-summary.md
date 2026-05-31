# ⚡ T1 · Agent Tool Calling 全景 — 冲刺版

> 完整版: [gfde-t1-overview.html](gfde-t1-overview.html). 这页是 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: agent runtime owns tool dispatch, multi-tenant SaaS, mix of read + write tools, 2026 GCP stack (Vertex AI + Gemini 3 Pro for default tier, Flash for cheap router, Claude 4.7 for hard cases), MCP-style tool catalog."

**核心 mental model**:

Tool call 不是 function call. 是 **跨边界 side-effect 投影** — LLM 给外部系统发 intent, 但**看不到执行, 不保证 0/1/N 次, 可能并发, 可能 untrusted**. 这是 distributed system + security 问题, 不是 ML 问题. 这就是为啥 T1 90% 在考你 backend mindset.

### Layer 1: 6-stage lifecycle (每 stage 都是 surface 区)

```
Registration → Discovery → Planning → Invocation → Result → Continuation
   (静态 @tool / MCP)  (RBAC + intent filter top-K)  (ReAct/Plan/Parallel)
   (auth/dedup/limit/confirm)  (schema/sanitize/wrap)  (max_iter cap)
```

### Layer 2: 5 个 sub-topic = 5 类风险防御

- **T1.1 Idempotency** → 防"转 2 次" (网络抖动 retry double-charge)
- **T1.2 Retry/Fallback** → 防"vendor 挂时系统崩"
- **T1.3 Parallel/Race** → 防"5 tool 同时写同 entity 数据腐败"
- **T1.4 Destructive** → 防"agent 误删真客户"
- **T1.5 Output Validation** → 防"tool 返回 inject 进 prompt hijack"

### Layer 3: 5 个 production pattern (面试当场可写代码)

```python
# A. Idempotency key (Redis 1h + DB unique 双层)
key = blake2b(tenant_id + session_id + tool + canonical(args))

# B. Layered retry (tool 3x exp backoff → alt vendor → human)
# C. Parallel split (PARALLEL_SAFE prefix vs SEQUENTIAL_ONLY)
PARALLEL_SAFE = {"get_*", "list_*", "search_*"}
SEQUENTIAL_ONLY = {"create_*", "update_*", "delete_*", "send_*", "charge_*"}

# D. Confirm-required wrapper (threshold lambda, compensating_action)
# E. Sandboxed output (<tool_output> XML wrap + system reminder)
```

### Edge cases (5 个必背)

- **EC1 Schema drift**: tool API 加新 required field → tool spec 带 `schema_version`, runtime reject mismatch
- **EC2 N+1 tool calls**: agent for-loop 调 100 次 → 提供 batch tool, single-item 标 `prefer_batch=True`
- **EC3 Tool dependency cycle**: A→B→A 死循环 → max_depth=5 + call stack 检测
- **EC4 Cost runaway**: agent infinite loop on $5/M tool → per-session $1 cap + max_iter=20 + auto-stop
- **EC5 Permission escalation**: agent 用 platform 大 perm 而非 user perm → `agent_token = min(platform, user)`, audit 分 actor + on_behalf_of

### Production hardening

- **Tool description 3 件**: when to use / when NOT / 1 example — 缺一个 LLM 选错
- **MCP for vendor-neutral**: customer internal API 包成 MCP server, Claude/GPT/Gemini 都能消费
- **Cost-aware routing**: Gemini Flash $0.50/$3 routes → Pro $2/$12 default → Claude Opus 4.7 $5/$25 hard cases. Blended ~$0.85/M vs all-Opus $5/M = 5-6x savings
- **VPC Service Controls** (GCP): tool calls cross-org boundary 要 explicit perimeter

### 🪝 Resume hook

"我在 TikTok PayLater 7-market voice agent + BNPL chatbot + Indonesia refund tier 都跑过完整 5 子题. Internal Agent Platform 做 shared tool catalog with versioning (`get_order:v2`) + per-team perm + per-tool cost meter — 业务团队 register tool, 平台层管 lifecycle. 这正是 Google FDE 给客户 internal API 包统一 tool catalog 的事."

---

## 🔥 5 Follow-ups

**Q1: Tool description 应该多长?**
够长够清楚. 短描述节省 token 是假经济 — LLM 选错 tool 浪费多 10x. 黄金标准: name + 1 行 purpose + "Use when..." + "Do NOT use when..." + 1 example with input/output. Anthropic 实测 description 加 example 后 tool selection accuracy +25%.

**Q2: 1000+ tools 怎么 scale?**
Static discovery 塞不下. 走 **dynamic top-K**: (a) RBAC 过滤 (b) intent embedding (text-embedding-005) similarity top-20 (c) recent usage boost (d) cost tier filter. 2026 industry 已经从 "能 tool calling" 转到 "scale to 1000+ tools".

**Q3: ReAct vs Plan-Then-Execute vs Parallel 怎么选?**
Read-heavy → **Multi-tool parallel** (Gemini 3 Pro 一 turn 可 emit 8+); write-heavy 多步 → **ReAct**; 复杂 workflow with branching → **Plan-Then-Execute**. 不要 over-engineer plan, 通常 ReAct + prompt caching 就够. Claude 4.7 prompt cache tool schema 让大 catalog 成本降 90%.

**Q4: MCP vs OpenAI function-calling vs Gemini tool use?**
**MCP** (Anthropic 2024, 2026 industry standard) vendor-neutral, 客户 internal API 包成 MCP server 不论 LLM 都能用 — 这是 FDE 主流交付物. **OpenAI** 简单但 vendor lock-in. **Gemini** 整合 Google Search grounding + code exec 深, Vertex AI 一体化. 加分回答: "我们 MCP 抽象 + JSON Schema 兼容, 路由层根据 query 复杂度选 Flash/Pro/Opus."

**Q5: Tool 返回 200 但 body 是 `{"error": "..."}` 怎么办?**
经典坑. 错误处理不能只看 HTTP code, 必须看 body status field. Tool wrapper 统一规范: 所有 tool 返回 `{"status": "success|error|degraded", "data": ..., "error_code": "...", "retry_after": N}`. LLM 看到 structured error 能 reason ("rate limit, ask user to wait"), 不会盲目当 success 用.

---

## ❌ 易错点 (10 条红线)

1. 把 tool call 当 function call 答 (2023 demo 视角, 不是 2026 FDE 视角)
2. "Exactly-once tool call" — 不存在, 老老实实 at-least-once + idempotent
3. Tool 返回直接 string concat 进 prompt (没 XML wrap, 没 sanitize)
4. 把 100 个 tool 全塞给 LLM 看 (token 浪费 + 选错率高)
5. Tool description 写得短 / 没 example / 没 "when NOT to use"
6. 错误处理只看 HTTP 200 不看 body status field
7. 没 max_iterations + cost cap (infinite loop 烧钱)
8. Agent token 用 platform 大 perm 而非 user perm (permission escalation)
9. 所有 tool 都 confirm → 用户疲劳 → 都点 Y → 等于没 confirm
10. "Retry until success" 没 budget cap = retry storm 放大下游故障

---

## ✅ 加分项 (12 条)

1. 心智模型清楚: tool = 跨边界 + 不可信 + 不确定调用方
2. 6-stage lifecycle (Registration → Continuation) 任意 stage 能展开
3. 5 个 sub-topic 都能 1 段话讲清 (idem/retry/race/dest/output)
4. 5 个 pattern 配代码骨架 (A-E) 当场可写
5. MCP vs OpenAI vs Gemini 对比 + 选 MCP 理由 (vendor-neutral)
6. 2026 模型 pricing 倒背如流 + blended cost 算 5-6x 省
7. Per-tool 独立 timeout / retry / breaker (不 global)
8. Tool description 3 件 (when/when-NOT/example)
9. Schema versioning + drift 处理
10. Cost-aware routing (Flash → Pro → Opus 三档)
11. 简历 hook 5 个项目对应 5 子题 (voice agent / BNPL / refund / ConvFinQA / Platform)
12. 主动 quote "我在 X 项目踩过这个坑, 这样修的"

---

## 一句话总结

Agent tool calling = **distributed system + untrusted input + 不确定调用方**. 6-stage lifecycle 每 stage 有 failure mode, 5 sub-topic 防 5 类风险, 5 pattern (idem/retry/parallel/confirm/sandbox) 是元 pattern. MCP 是 2026 vendor-neutral 标准, 用 Flash/Pro/Opus 三档 cost-aware routing.

---

## 🃏 Cheat Sheet (印 1 页随身)

```
Mental model:
  Tool call = 跨边界 side-effect 投影
  NOT function call. At-least-once. 可能 0/1/N 次.
  Distributed system + security problem, NOT ML.

5 sub-topics (each 1-sentence):
  T1.1 Idem      → key + Redis + DB unique 双层
  T1.2 Retry     → 3-layer (tool exp backoff / alt / human)
  T1.3 Parallel  → annotate + DAG + per-resource lock
  T1.4 Destruct  → confirm + threshold + compensate
  T1.5 Output    → schema + truncate + XML wrap + provenance

5 patterns (元 pattern):
  A. Idempotency key (Redis 1h + DB unique)
  B. Layered retry (tool 3x → alt → human)
  C. Parallel/sequential split (read prefix vs write)
  D. Confirm-required wrapper (threshold + compensating)
  E. Sandboxed output (XML wrap + system reminder)

6-stage lifecycle:
  Registration → Discovery → Planning → Invocation
  → Result Handling → Continuation
  (每 stage 是 FDE failure surface)

MCP vs OpenAI vs Gemini (2026):
  MCP (Anthropic) — vendor-neutral, industry standard ⭐
  OpenAI Function — simple, tied to OpenAI
  Gemini 3 tool use — 2M context + Vertex 一体化

2026 model pricing (cost routing):
  Gemini 3 Flash   $0.50/$3  per 1M  cheap tier (router/classify)
  Gemini 3 Pro     $2/$12    per 1M  default
  Claude Opus 4.7  $5/$25    per 1M  hard cases
  GPT-5.5          $5/$30    per 1M  alt premium
  Blended cost ~$0.85/M vs all-Opus $5/M = 5-6x savings

Tool description (黄金标准):
  - Name + 1 行 purpose
  - "Use when X"
  - "Do NOT use when Y (use Z instead)"
  - 1 example input + output
  - Common pitfalls

Discovery filter chain:
  1000 catalog → RBAC → intent embed top-K → recent usage
  → cost tier → 10-20 tools to LLM

Production gotchas (top 8):
  1. Stale tool result (add fetched_at)
  2. Ambiguous description
  3. N+1 calls (batch API)
  4. Cycle (max depth 5)
  5. Hot key (per-resource lock)
  6. Prompt injection (XML wrap)
  7. Cost runaway (per-session cap)
  8. Permission escalation (min(platform, user))

45-min answer rhythm:
  0-5    Clarify (3 questions)
  5-10   Mental model (distributed, not ML)
  10-25  Deep-dive 1 pattern + code skeleton
  25-35  Failure modes (3-5 gotchas)
  35-42  MCP/OpenAI/Gemini tradeoff
  42-45  Resume quote "I did this on X"

Resume hooks → sub-topic:
  Voice agent 7 markets → T1.1 idem, T1.2 retry
  BNPL chatbot         → T1.3 parallel, T1.2 fallback
  Indonesia Refund tier → T1.4 destructive + compensating
  ConvFinQA 5 calc tools → T1.5 output validation
  Internal Agent Platform → T1 general (catalog/versioning)

红线 (说错负分):
  - "Exactly-once" (不存在)
  - "Tool 返回是 trusted" (必须 sanitize)
  - "All tools confirm" (fatigue)
  - "Retry until success" (storm)
  - 短 tool description 节省 token (反而贵)
  - 100 tool 一起塞 LLM
```
