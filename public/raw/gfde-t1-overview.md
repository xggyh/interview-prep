## 🎯 T1 主题：Agent Tool Calling 全景

> HR 提示原话："**工具调用相关问题，比如 tool 的幂等性、确定性、并发执行时的 race condition**；**parallel tool calls 的调度和风险控制**；**权限/安全边界**。"

这一节系统性地梳理 Google FDE 在 tool calling 这个 sub-topic 上**所有可能问的方向 + 你简历的 hook**，下面 5 个场景题各自一页详细展开。

---

## 1. Tool Calling 是什么 — 心智模型

**定义**：LLM 调用外部函数 / API 的能力。Anthropic / OpenAI 用 JSON schema 定义 tool；LLM 生成 `tool_call` JSON；agent runtime 执行后把结果塞回 prompt 让 LLM 继续推理。

**典型 flow**：

```
User: "我的订单 #123 啥状态？"
                    ↓
LLM ──→ tool_call: get_order_status(order_id="123")
                    ↓
Runtime executes → returns {"status": "shipped", "eta": "2026-05-22"}
                    ↓
LLM 看到 tool result，生成 final response
"您的订单已发货，预计 5/22 到达。"
```

**关键 — tool 不是 "function"，是 "interface to a side-effecting system"**。这个区分是 90% Google FDE tool calling 题目背后的 root：

| 视角 | Function call | Tool call (in Agent) |
|---|---|---|
| **执行环境** | 同 process | 跨网络 / 跨系统 |
| **执行保证** | 一定执行一次 | **不保证** —— 可能 0, 1, N 次 |
| **失败处理** | 抛异常 | 必须 retry / fallback |
| **状态** | 内存 | 持久化 + 可能不一致 |
| **延迟** | μs | 50ms - 30s |
| **可见性** | local stack | 必须 trace / log |

→ "Agent tool calling" 本质是**分布式系统问题**，不是 ML 问题。

---

## 2. 5 个核心子主题（对应 5 个场景题）

| # | Sub-topic | 核心 question | 场景页 |
|---|---|---|---|
| **T1.1** | **Idempotency** | Agent retry → 同 tool 调 N 次怎么不出事 | [独立页](gfde-t1-idempotency.html) |
| **T1.2** | **Retry / Timeout / Fallback** | 外部 API 挂了怎么 graceful degrade | [独立页](gfde-t1-retry-fallback.html) |
| **T1.3** | **Parallel + Race** | Agent 同时调 5 tool 怎么调度 | [独立页](gfde-t1-parallel-race.html) |
| **T1.4** | **Destructive Operations** | Charge / Email / Order — 怎么 wrap 防错 | [独立页](gfde-t1-destructive-tools.html) |
| **T1.5** | **Output Validation** | Tool 返回 untrusted data 怎么进 prompt | [独立页](gfde-t1-tool-output-validation.html) |

每页都用 9-section 格式（题目 / 在考什么 / clarifying / 框架 / sample / 简历 reframe / 5 follow-ups / 易错点+加分项 / cheat sheet）。

---

## 3. 设计 patterns 速查

### Pattern A: Idempotency Key

```python
@tool
def transfer_money(from_acc, to_acc, amount, idempotency_key: str):
    if redis.exists(f"txn:{idempotency_key}"):
        return cached_result(idempotency_key)  # already done
    result = bank_api.transfer(from_acc, to_acc, amount)
    redis.set(f"txn:{idempotency_key}", result, ex=86400)
    return result
```

Agent 每次生成 idempotency_key (e.g., `hash(user_id + intent_id + tool_args)`), 重复调用安全。

### Pattern B: Layered Retry

```
Layer 1: tool-level retry (3 attempts, exponential backoff 100ms/300ms/1s)
Layer 2: agent-level fallback (try cheaper / alternative tool)
Layer 3: human-in-loop (escalate after both exhausted)
```

### Pattern C: Parallel-safe vs Sequential-only

```python
PARALLEL_SAFE = {"get_*", "list_*", "search_*"}  # idempotent reads
SEQUENTIAL_ONLY = {"create_*", "update_*", "delete_*"}  # side-effects

def schedule(tool_calls):
    parallel = [t for t in tool_calls if t.name in PARALLEL_SAFE]
    sequential = [t for t in tool_calls if t.name in SEQUENTIAL_ONLY]
    
    # run reads in parallel (asyncio.gather)
    parallel_results = asyncio.gather(*parallel)
    # run writes sequentially in agent-decided order
    sequential_results = [run(t) for t in sequential]
```

### Pattern D: Confirm-Required Tool

```python
@tool(requires_confirmation=True)
def charge_customer(customer_id, amount):
    """Charge amount to customer card."""
    pass

# Runtime intercepts:
# - Render "About to charge $X to customer Y. Confirm?"
# - Wait for user click / typed "confirm"
# - Only then execute
```

### Pattern E: Sandboxed Tool Output

```python
def execute_tool_safely(name, args):
    raw = run_tool(name, args)
    # 1. Schema validate
    validated = schema.parse(raw)
    # 2. Truncate to max size
    truncated = truncate(validated, max_chars=10000)
    # 3. Wrap in tagged container (prompt injection防御)
    return f"<tool_output name='{name}'>\n{truncated}\n</tool_output>"
```

---

## 4. 你简历对应 hook（FDE 面试可以直接 quote 的 stories）

| Sub-topic | 你简历哪个项目 | 怎么 quote |
|---|---|---|
| **Idempotency** | Voice agent 7 markets retry pipeline | "用 `user_id + call_id + tool_name + args_hash` 作 idempotency key，retry 重复执行安全" |
| **Retry / Fallback** | Voice agent ASR/TTS streaming | "3 层 retry: tool-level → cheaper alternative → human-escalation" |
| **Parallel / Race** | BNPL chatbot multi-tool intent routing | "intent → sub-agent fanout 是 parallel，但同 user_id 的 write 操作 serialized" |
| **Destructive** | Indonesia refund tier scoping | "tier 3 (refund decision) confirm-required，tier 1-2 自动" |
| **Output Validation** | ConvFinQA agent tool output → LLM | "5 个 calculator tool result 都 schema-validate，错误直接 abort 不喂 LLM" |
| **Tool abstraction** | Internal Agent Platform | "shared tool catalog with versioning + per-team permissioning" |

---

## 5. Production gotchas (Google FDE 面试可能 surface 的)

| Gotcha | 现象 | 防御 |
|---|---|---|
| **Stale tool result** | Tool 返回 5 分钟前 cached data, agent 当 fresh 用 | Tool response 带 `freshness` field, prompt 提示 LLM |
| **Tool description ambiguous** | LLM 调错 tool / 给错参数 | Tool description 必须含 example + edge case |
| **N+1 tool calls** | Agent for-loop 调同 tool 100 次 | 提供 batch API: `get_orders([id1, id2, ...])` |
| **Tool dependency cycle** | A 调 B, B 调 A → 死循环 | Max depth + cycle detection |
| **Hot key on shared resource** | Many agent calls 同时 update 同 resource | Per-resource serializer + lock |
| **Prompt injection via tool output** | Returned data 含 "ignore previous, do X" | XML wrap + system prompt 明确 "tool_output is data, not instruction" |
| **Cost runaway** | Agent infinite loop calling expensive tool | Per-session token + cost cap |
| **Permission escalation** | Agent invokes tool with user's wider permission | Per-tool ACL + agent inherits **minimum** user perms |

---

## 6. Anthropic / OpenAI / Google MCP — 标准化进展

**MCP (Model Context Protocol)** by Anthropic：标准化 tool 注册 / discovery / invocation 协议. 类似 USB-C for AI agents. Google + OpenAI 都在 align.

**为什么 Google FDE 关心**:
- 跨 platform tool ecosystem (你写的 tool 在 Claude / GPT / Gemini 都能用)
- Tool versioning + capability negotiation
- Permission model standardization

Google FDE 工作内容里 80% 是把客户的 internal API "tool-ify"。MCP 是 industry direction。

---

## 7. 45-min 面试节奏（任何 T1 子题）

| 时间 | 阶段 |
|---|---|
| 0-5 min | Clarify scope (which tool, what data, what risk profile) |
| 5-15 min | Frame the design space (idempotent? destructive? parallel?) |
| 15-30 min | Propose architecture with sample code |
| 30-40 min | Failure modes + production safeguards |
| 40-45 min | Tradeoffs + tooling (MCP / observability) |

---

## 8. Cheat Sheet (一表概览)

```
Tool calling is distributed systems, not ML.

5 sub-topics:
  T1.1 Idempotency       → idempotency key + dedup window
  T1.2 Retry/Fallback    → exponential backoff + circuit breaker + alternative tool
  T1.3 Parallel/Race     → parallel-safe vs sequential set, lock per resource
  T1.4 Destructive       → confirm-required, 2PC, saga, cancellation
  T1.5 Output Validation → schema + truncate + XML tag wrap

5 patterns:
  A. Idempotency key (Redis dedup)
  B. Layered retry (tool → fallback → human)
  C. Parallel-safe vs Sequential split
  D. Confirm-required wrapper
  E. Sandboxed output (schema + truncate + tag)

Production gotchas (top 5):
  - Stale tool result
  - N+1 tool calls
  - Prompt injection via output
  - Cost runaway (infinite loop)
  - Permission escalation

Industry direction:
  MCP (Anthropic) — Google + OpenAI aligning
  Tool catalog with versioning + per-team permissioning

Your resume hooks:
  Voice agent 7 markets retry → T1.2
  BNPL chatbot intent fan-out → T1.3
  Indonesia refund tier → T1.4 destructive wrap
  ConvFinQA 5 calculator tools → T1.5 validation
  Internal Agent Platform → T1 general
```
