## Q45 · End-to-end agent design — tools, memory, evaluation

> "Design an end-to-end production agent for a customer use case. Cover **tool registry, planning, execution, memory (short and long-term), and evaluation**. The agent needs to handle multi-step workflows, recover from tool failures, and you must convince me you can sleep at night when it's running in production."

**中文翻译**:

> "给一个客户的 use case 设计一个端到端的 production agent (生产环境的智能体). 要覆盖 **tool registry (工具注册表), planning (规划), execution (执行), memory (记忆 — 短期和长期都要), 还有 evaluation (评估)**. 这个 agent 要能 handle 多步骤 workflow, 还要能从 tool failure 中恢复, 并且你得说服我 — 它在 production 跑的时候我能睡得着觉."

**Round**: AI Specialty (45 min)
**出处**: Exponent 2026 FDE Guide · 公司: OpenAI / Anthropic / Cohere / LangChain — agent design 必问

---

## 📖 术语速查 (本题用到的)

> Agent 设计题混了 ML / 分布式系统 / workflow 术语. 5 min 速查再读详解.

### Agent 架构 ⭐

| 术语 | 解释 |
|---|---|
| **Agent** ⭐ | **能调用 tool / 多步推理的 LLM 系统**. 不只生成文字, 而是 "查日历 → 找时间 → 发邮件" 这种 chain. |
| **Tool / Function calling** ⭐ | **LLM 可调用的外部能力** (查 DB / 调 API / 算数). OpenAI 2023 推出 function calling, 现在通用. |
| **Tool registry** | 系统 manage 所有可用 tool 的 catalog — schema, auth, idempotency 都登记. |
| **Planner** | LLM 决定 "下一步调哪个 tool". Plan-then-execute 或 ReAct. |
| **Executor** | 实际执行 tool call, 处理 retry / timeout. |
| **ReAct (Reason + Act)** ⭐ | **Reasoning 和 Acting 交替** — think → act → observe → think → act ... 不预先规划全 pipeline. |
| **Plan-then-execute** | 先 LLM 生成完整 plan, 然后 deterministic 执行. 比 ReAct 可控但少灵活. |
| **Multi-agent / Swarm** | 多个 agent 协作 — planner agent + worker agent. 复杂任务用. |
| **MCP (Model Context Protocol)** ⭐ | **Anthropic 2024.11 推的 tool standard**. Tool 提供方实现 MCP server, 任意 client (Claude / Cursor / Cline) 用. |
| **OpenAI Agents SDK** | OpenAI 2024.10 推的 agent framework. |
| **LangGraph** | LangChain 推的 state-machine-style agent framework. 适合复杂 flow. |
| **LangChain** | Python LLM 框架, 提供 chain / tool / memory 抽象. |
| **CrewAI / AutoGen** | Multi-agent frameworks. |

### Memory 三层架构 ⭐

| 术语 | 解释 |
|---|---|
| **Working memory** ⭐ | **当前 conversation context window** — 这一轮对话的内容. 容量 = model context length. |
| **Short-term memory** | 同 working memory, 用户的最近几轮对话. |
| **Long-term memory** ⭐ | **跨 session 持久化的记忆**. 通常存 vector DB, 检索后注入 prompt. |
| **Episodic memory** | 长记忆的一种 — 历史 conversation / event 的具体记录. |
| **Semantic memory** | 长记忆的一种 — 抽象知识 / 偏好 (用户喜欢简洁回答). |
| **Structured KV memory** | 结构化的 fact 存 KV store — 用户名 / 偏好 / business state. 比 vector 检索精确. |
| **Memory consolidation** | 把 short-term 压缩 / abstract 后存 long-term. 模仿大脑机制. |
| **Context window** | Model 一次能看的最大 token 数. 2026: Opus 4.7 1M / Gemini 3 Pro 2M. |
| **Context stuffing** | 暴力把所有相关 context 塞进 prompt. 简单但贵 + 不 scale. |

### Tool 设计

| 术语 | 解释 |
|---|---|
| **JSON schema** | 定义 tool input/output 的 schema. LLM 用它知道 call 怎么写. |
| **Idempotency** ⭐ | **同一 request 多次执行结果一致**. Retry 安全必备 — 否则 retry 可能扣两次钱. |
| **Idempotency key** | Request 带的 unique ID, 系统识别重复. e.g. `Idempotency-Key: <uuid>`. |
| **Function calling schema** | OpenAI/Anthropic 的 tool definition 格式 — name + description + parameters JSON schema. |
| **Tool choice** | 强制 LLM call 特定 tool / 不 call tool / 自选. |

### 可靠性 / Workflow ⭐

| 术语 | 解释 |
|---|---|
| **Durable workflow** ⭐ | **Workflow 状态持久化, 中途崩了能从断点续跑**. Temporal / Inngest 实现. |
| **Temporal** | Workflow orchestration 平台. Production agent 标配. |
| **Inngest** | TypeScript-friendly durable workflow. |
| **Saga pattern** | 长事务分多个 step, 每 step 有 compensating action (回滚). Distributed system 标准. |
| **Circuit breaker** ⭐ | **连续失败到 threshold 后停止调用 N 秒**, 给 downstream 喘息. 防 cascading failure. |
| **Retry with exponential backoff** | Retry 间隔指数增长 (1s, 2s, 4s, 8s ...). 防止 retry storm. |
| **Jitter** | Backoff 加随机抖动 — 避免大量 client 同时 retry 撞车. |
| **Timeout** | Request 超过 X 秒就放弃. 防 hang 死. |
| **Dead letter queue (DLQ)** | 失败 N 次的 message 进 DLQ, 人工处理. 防止丢消息. |
| **Rate limiting** | 限制 client QPS. Token bucket / leaky bucket 算法. |

### Eval — Agent 特别篇

| 术语 | 解释 |
|---|---|
| **Per-step success rate** | 每个 tool call 成功比例. End-to-end 看不出哪 step 挂. |
| **End-to-end task completion** | 整个 task 完成比例. 真目标. |
| **Trajectory eval** | 看 agent 走过的 step 序列对不对. |
| **Tool call accuracy** | LLM 选对 tool + 参数对的比例. |
| **Self-consistency** | 同 query 跑 N 次, 看 result 一致性. 高 → 信心高. |

### Production 工具

| 术语 | 解释 |
|---|---|
| **OpenTelemetry / OTEL** | 开源 observability 标准 — trace / metric / log 统一. |
| **Distributed tracing** | 跨服务的 request trace, 看哪 step 慢 / 挂. |
| **Span** | Trace 中的一个 unit — 一次 function call / API call. |
| **Pydantic** | Python schema validation. LLM 输出 → Pydantic 校验. |
| **Sentry** | Error tracking. |

---

## 这道题在考什么

表面是 agent 题, 底下藏着 **8 个 FDE evaluation signal**:

1. **Component awareness** — 知道 production agent 是 tool registry + planner + executor + memory + eval 5 part system
2. **Tool design discipline** — 不只是 "list tools", 是 input schema + idempotency + retry + observability
3. **Memory architecture** — short-term context vs long-term vector vs structured KV facts, 何时用哪个
4. **Planning vs ReAct** — 知道何时 plan-then-execute vs interleave
5. **Failure handling** — tool timeout / retry / circuit breaker / human escalation
6. **Eval methodology** — per-step success + end-to-end task completion + cost + latency
7. **Specific tools (2026)** — LangGraph, MCP, Temporal, Inngest, OpenAI Agents SDK
8. **Production reality** — durable workflow, idempotency keys, dead letter queue

不考「agent 是什么」, 考「你设计的 agent half-failed mid-workflow, 怎么 recover」.

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|---|---|---|
| 1 | **Clarify use case** | 3 min | What customer task? volume? latency? failure tolerance? | "Before I design, what task is this agent automating? what's the failure cost?" |
| 2 | **5-component architecture** | 5 min | Tool registry / Planner / Executor / Memory / Eval | "5 components — tool registry, planner, executor, memory (3 layers), eval pipeline." |
| 3 | **Tool registry design** | 6 min | Schema, idempotency, retry, observability | "Each tool needs JSON schema, idempotency contract, retry policy, latency SLO, audit log." |
| 4 | **Planning approach** | 5 min | Plan-then-execute vs ReAct vs LangGraph state machine | "3 patterns — plan-then-execute (deterministic), ReAct (interleaved), state machine (LangGraph for complex flows)." |
| 5 | **Memory architecture** | 5 min | 3 layers (working / structured / vector) | "Memory has 3 layers — short-term in context, structured KV facts, long-term vector store." |
| 6 | **Failure handling** | 5 min | Timeout, retry with backoff, circuit breaker, human handoff | "Failure modes: tool timeout, schema fail, infinite loop, partial completion. Each has playbook." |
| 7 | **Eval pipeline** | 4 min | Per-step + end-to-end + cost + latency + safety | "Eval is multi-layered — per-step success, end-to-end task completion, cost per task, latency p99." |
| 8 | **Specific tools 2026** | 3 min | LangGraph, MCP, Temporal, OpenAI Agents SDK | "Stack — LangGraph for flow, MCP for tool standard, Temporal/Inngest for durable workflows, custom Pydantic for schemas." |
| 9 | **Quote BNPL chatbot + internal Agent Platform** | 4 min | Real shipped agents | "BNPL chatbot was a 4-tool agent (FAQ retrieve, policy lookup, escalate, log). Internal Agent Platform supports 12 internal teams." |
| 10 | **Production checklist** | 2 min | What I'd build week 1 / week 4 / month 3 | "Week 1: tool registry + planner + happy path. Week 2-3: failure handling + eval. Month 2: durable workflows + cascading." |

---

## 详细回答

### Step 1: 5-Component Architecture

```
            ┌──────────────────────────────────────────┐
            │           USER REQUEST                   │
            └────────────────────┬─────────────────────┘
                                 │
                                 ▼
            ┌──────────────────────────────────────────┐
            │   1. TOOL REGISTRY                       │
            │   • JSON schema for each tool            │
            │   • Idempotency contracts                │
            │   • Auth / ACL                           │
            │   • Versioning                           │
            │   • Observability hooks                  │
            └────────────────────┬─────────────────────┘
                                 │
                                 ▼
            ┌──────────────────────────────────────────┐
            │   2. PLANNER (LLM)                       │
            │   • Inspects task                        │
            │   • Selects tools                        │
            │   • Generates plan / state machine       │
            │   • Re-plans on failure                  │
            └────────────────────┬─────────────────────┘
                                 │
                                 ▼
            ┌──────────────────────────────────────────┐
            │   3. EXECUTOR                            │
            │   • Calls tools per plan                 │
            │   • Retry with backoff                   │
            │   • Timeout handling                     │
            │   • Idempotency tracking                 │
            │   • Audit log                            │
            └────────────────────┬─────────────────────┘
                                 │
            ┌────────────────────┼───────────────────┐
            │                    │                   │
            ▼                    ▼                   ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │ 4a. WORKING MEM  │  │ 4b. STRUCTURED   │  │ 4c. LONG-TERM    │
   │ (context window) │  │      KV FACTS    │  │      VECTOR      │
   │  - current state │  │  - user prefs    │  │  - history       │
   │  - tool results  │  │  - business data │  │  - knowledge     │
   │  - reasoning     │  │  - structured    │  │  - examples      │
   └──────────────────┘  └──────────────────┘  └──────────────────┘
                                 │
                                 ▼
            ┌──────────────────────────────────────────┐
            │   5. EVAL PIPELINE                       │
            │   • Per-step success                     │
            │   • End-to-end task completion           │
            │   • Cost per task                        │
            │   • Latency p99                          │
            │   • Safety / refusal                     │
            └──────────────────────────────────────────┘
```

### Step 2: Tool Registry (the foundation)

**Each tool is a contract** — not a Python function. Treat tools like API endpoints.

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class ToolDefinition(BaseModel):
    name: str
    description: str  # critical — LLM uses this to decide when to call
    input_schema: dict  # JSON schema
    output_schema: dict
    
    # Behavior contracts
    idempotent: bool  # safe to retry?
    side_effects: bool  # writes to external system?
    requires_confirmation: bool  # human-in-loop before execution?
    
    # SLOs
    expected_latency_p99_ms: int
    timeout_ms: int
    
    # Retry policy
    retry_strategy: Literal['none', 'linear', 'exponential']
    max_retries: int
    
    # Auth
    required_scopes: list[str]
    
    # Versioning
    version: str
    deprecated: bool = False
    deprecation_date: Optional[datetime] = None

# Example tool
refund_tool = ToolDefinition(
    name='process_refund',
    description="""
    Process a refund for a TikTok PayLater order. 
    
    Use this when: customer requests refund AND eligibility verified AND amount < $500.
    Don't use when: refund > $500 (escalate to human), or order > 90 days (out of policy).
    """,
    input_schema={
        'type': 'object',
        'properties': {
            'order_id': {'type': 'string', 'pattern': '^ORDER-[0-9]+$'},
            'amount_cents': {'type': 'integer', 'minimum': 1, 'maximum': 50000},
            'reason_code': {'type': 'string', 'enum': ['defect', 'not_received', 'duplicate', 'fraud']},
            'idempotency_key': {'type': 'string', 'format': 'uuid'}
        },
        'required': ['order_id', 'amount_cents', 'reason_code', 'idempotency_key']
    },
    output_schema={
        'type': 'object',
        'properties': {
            'refund_id': {'type': 'string'},
            'status': {'type': 'string', 'enum': ['processed', 'pending_review', 'rejected']},
            'estimated_completion_date': {'type': 'string', 'format': 'date'},
        }
    },
    idempotent=True,  # via idempotency_key
    side_effects=True,  # writes to payment system
    requires_confirmation=True,  # human confirms for >$200
    expected_latency_p99_ms=2000,
    timeout_ms=5000,
    retry_strategy='exponential',
    max_retries=3,
    required_scopes=['refund:process'],
    version='2.1.0',
)
```

**Why idempotency matters**:

```
User asks agent: "Refund my order #123"

Agent calls refund tool. 
  → Tool times out at 4.9s (just before 5s timeout)
  → Did refund go through or not?
  
Without idempotency key: retry might double-refund (financial loss)
With idempotency key: retry with same key → tool returns same result
```

**Tool registry as MCP server (2026 standard)**:

```python
# Model Context Protocol (Anthropic 2024+, OpenAI adopted 2025)
# Standard tool exposure for any agent framework

@mcp.tool()
async def process_refund(
    order_id: str,
    amount_cents: int,
    reason_code: Literal['defect', 'not_received', 'duplicate', 'fraud'],
    idempotency_key: str,
) -> dict:
    """Process a refund for a TikTok PayLater order.
    
    Use this when: customer requests refund AND eligibility verified AND amount < $500.
    Don't use when: refund > $500 or order > 90 days.
    """
    # Idempotency check
    existing = await db.refunds.find_one({'idempotency_key': idempotency_key})
    if existing:
        return existing
    
    # Validate eligibility
    order = await get_order(order_id)
    if order.amount_cents < amount_cents:
        raise InvalidRefundAmountError()
    
    # Process
    refund = await payment_service.refund(order_id, amount_cents, reason_code)
    
    # Persist with idempotency key
    await db.refunds.insert({
        'idempotency_key': idempotency_key,
        'refund_id': refund.id,
        'status': refund.status,
        'estimated_completion_date': refund.eta,
    })
    
    return refund.dict()
```

### Step 3: Planner — 3 patterns

**Pattern A: Plan-then-Execute (deterministic, auditable)**

```python
async def plan_then_execute(task, tools):
    # 1. Plan
    plan = await llm.generate_plan(task, tools, structured_output=Plan)
    # Plan = list of (tool_name, args, depends_on)
    
    # 2. Validate plan
    if not all(t in tools for t in plan.tool_names):
        raise InvalidPlanError()
    
    # 3. Execute (sequential or parallel based on deps)
    results = {}
    for step in plan.steps:
        if step.depends_on:
            await wait_for(step.depends_on, results)
        
        result = await execute_tool(step.tool_name, step.args, results)
        results[step.id] = result
    
    return synthesize(results, task)
```

**Pros**: Deterministic, auditable, can validate before execution
**Cons**: Inflexible, can't adapt mid-execution
**Best for**: Well-understood workflows (invoice processing, scheduled jobs)

**Pattern B: ReAct (Reasoning + Acting interleaved)**

```python
async def react_loop(task, tools, max_steps=20):
    history = []
    
    for step in range(max_steps):
        # 1. Reason about next action
        prompt = build_react_prompt(task, history, tools)
        thought = await llm.generate(prompt)
        
        # 2. Decide: tool call or finish?
        if thought.action == 'finish':
            return thought.answer
        
        # 3. Execute tool
        result = await execute_tool(thought.action, thought.args)
        
        # 4. Append to history
        history.append({
            'thought': thought.text,
            'action': thought.action,
            'args': thought.args,
            'observation': result
        })
    
    return "Max steps reached, escalating"
```

**Pros**: Flexible, can adapt to surprises mid-task
**Cons**: Can loop infinitely, harder to audit, more LLM calls
**Best for**: Open-ended tasks, exploration, debugging

**Pattern C: LangGraph state machine (complex flows)**

```python
from langgraph.graph import StateGraph

class AgentState(TypedDict):
    task: str
    intent: str
    retrieved: list
    plan: Plan
    results: dict
    failures: list
    needs_human: bool

def classify_intent(state):
    state['intent'] = llm.classify_intent(state['task'])
    return state

def retrieve_context(state):
    state['retrieved'] = rag.search(state['task'])
    return state

def make_plan(state):
    state['plan'] = llm.plan(state['task'], state['retrieved'])
    return state

def execute_step(state):
    next_step = state['plan'].next()
    try:
        result = execute_tool(next_step.tool, next_step.args)
        state['results'][next_step.id] = result
    except ToolFailure as e:
        state['failures'].append(e)
        if len(state['failures']) >= 3:
            state['needs_human'] = True
    return state

def synthesize(state):
    return llm.synthesize(state['task'], state['results'])

def route_after_execute(state):
    if state['needs_human']:
        return 'human_handoff'
    if state['plan'].is_complete():
        return 'synthesize'
    return 'execute_step'

# Build graph
workflow = StateGraph(AgentState)
workflow.add_node('classify', classify_intent)
workflow.add_node('retrieve', retrieve_context)
workflow.add_node('plan', make_plan)
workflow.add_node('execute', execute_step)
workflow.add_node('synthesize', synthesize)
workflow.add_node('human_handoff', handoff)

workflow.set_entry_point('classify')
workflow.add_edge('classify', 'retrieve')
workflow.add_edge('retrieve', 'plan')
workflow.add_edge('plan', 'execute')
workflow.add_conditional_edges('execute', route_after_execute)

agent = workflow.compile()
```

**Pros**: Explicit state, conditional edges, easy to audit / visualize
**Cons**: Verbose, requires upfront design
**Best for**: Multi-step workflows with branching, complex production agents

### Step 4: Memory Architecture (3 layers)

```
┌────────────────────────────────────────────────────────────┐
│ LAYER 1: WORKING MEMORY (current LLM context window)       │
│  - Current task description                                │
│  - Recent tool calls + results (last N)                    │
│  - Reasoning trace                                         │
│  - Lifetime: single agent invocation                       │
│  - Storage: in-process / Redis                             │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ LAYER 2: STRUCTURED FACTS (KV store)                       │
│  - User preferences (language, timezone, tier)             │
│  - Business data (subscription tier, credit limit)         │
│  - Last-known state (last interaction, last balance)       │
│  - Lifetime: across sessions                               │
│  - Storage: Postgres / Firestore / Bigtable / Redis                    │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ LAYER 3: LONG-TERM VECTOR MEMORY                           │
│  - Past conversations (chunked, embedded)                  │
│  - Knowledge corpus (FAQ, policy)                          │
│  - Similar successful task examples                        │
│  - Lifetime: months-years                                  │
│  - Storage: Vertex AI Vector Search / Vertex AI Vector Search / Vespa                      │
└────────────────────────────────────────────────────────────┘
```

**When to use which**:

```python
class MemorySystem:
    def __init__(self):
        self.working = WorkingMemory()  # in-context
        self.structured = StructuredKV(redis_client)
        self.vector = VectorStore(qdrant_client)
    
    async def get_user_context(self, user_id):
        """Loaded once at agent invocation."""
        # Structured facts: cheap KV lookup
        prefs = await self.structured.get(f'user:{user_id}:prefs')
        
        # Recent history: vector search on past conversations
        recent_history = await self.vector.search(
            query=f'user:{user_id} recent',
            filter={'user_id': user_id},
            top_k=5,
            sort='timestamp_desc'
        )
        
        return {
            'preferences': prefs,
            'recent_history_summary': summarize(recent_history)
        }
    
    async def remember(self, fact_type, key, value):
        """During / after agent execution, persist learnings."""
        if fact_type == 'structured':
            await self.structured.set(key, value, ttl=86400 * 365)
        elif fact_type == 'episodic':
            embedding = await embed(value['summary'])
            await self.vector.upsert(
                id=generate_id(),
                vector=embedding,
                payload=value
            )
        elif fact_type == 'working':
            # Already in context, just append
            self.working.append(value)
```

**Memory cost**:

```
Working: free (in context)
Structured KV: $0.0001 per get/set (Redis)
Vector: $0.001 per search (Vertex AI Vector Search)
Embed cost: $0.0001 per chunk (text-embedding-3-large)

100k agent invocations/day:
  Working: $0
  Structured: $0.10 (very cheap)
  Vector: $100/day for memory search
  Embed (on writes): $10/day
  Total: ~$110/day = $3,300/month
```

### Step 5: Failure handling (production grit)

**Failure modes**:

```
1. Tool timeout
2. Tool returns error
3. Tool returns unexpected schema
4. Tool partially completes (side effect happened)
5. LLM hallucinates tool call (wrong tool / args)
6. LLM gets stuck in infinite loop
7. Plan fails mid-execution
8. Downstream service rate-limited
9. Context window exhausted
10. Customer aborts mid-conversation
```

**Per-failure playbook**:

```python
class FailureHandler:
    async def handle_tool_failure(self, tool_call, error, attempt):
        if isinstance(error, TimeoutError):
            # Check tool's retry policy
            if attempt < tool_call.tool.max_retries:
                backoff = 2 ** attempt  # exponential
                await asyncio.sleep(backoff)
                return RetryAction(backoff=backoff)
            else:
                return EscalateAction(reason='timeout_exhausted')
        
        elif isinstance(error, SchemaValidationError):
            # LLM-induced bad args, ask LLM to fix
            return ReplanAction(
                feedback=f"Tool call failed validation: {error}. Fix args."
            )
        
        elif isinstance(error, RateLimitedError):
            # Vendor rate limit
            await asyncio.sleep(60)
            return RetryAction()
        
        elif isinstance(error, AuthError):
            # Hard fail, can't recover
            return EscalateAction(reason='auth_failure', urgency='P1')
        
        elif isinstance(error, PartialCompletionError):
            # Tool may have done side effect — careful!
            if tool_call.tool.idempotent:
                return RetryAction(idempotency_key=tool_call.idempotency_key)
            else:
                # Don't retry, escalate to human
                return EscalateAction(
                    reason='non_idempotent_partial',
                    context=f"Tool {tool_call.tool.name} may have completed. Verify with audit log."
                )
        
        else:
            # Unknown error
            return EscalateAction(reason='unknown_error', urgency='P2')
```

**Circuit breaker**:

```python
class CircuitBreaker:
    """Stop calling a failing tool to avoid cascading failures."""
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failures = 0
        self.state = 'closed'  # closed = normal, open = failing, half-open = testing
        self.last_failure_time = None
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
    
    async def call(self, tool, *args):
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'half-open'
            else:
                raise CircuitOpenError(f"Circuit open for {tool.name}")
        
        try:
            result = await tool(*args)
            if self.state == 'half-open':
                self.state = 'closed'  # recovered
            self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.failure_threshold:
                self.state = 'open'
            raise e
```

**Loop detection**:

```python
class LoopDetector:
    def __init__(self, max_repeats=3):
        self.history = []
        self.max_repeats = max_repeats
    
    def check(self, action, args):
        key = (action, hash(json.dumps(args, sort_keys=True)))
        recent = self.history[-10:]
        repeat_count = sum(1 for k in recent if k == key)
        
        self.history.append(key)
        
        if repeat_count >= self.max_repeats:
            raise InfiniteLoopError(
                f"Agent repeated {action} with same args {self.max_repeats}x"
            )
```

**Durable workflows (Temporal / Inngest)**:

```python
# For workflows that must survive process crashes, restarts
# Temporal / Inngest provide durable execution

@workflow.defn
class RefundWorkflow:
    @workflow.run
    async def run(self, refund_request):
        # Each step is a checkpoint
        # If process crashes mid-step, resumes from last checkpoint
        
        eligibility = await workflow.execute_activity(
            check_eligibility,
            refund_request.order_id,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        if not eligibility.eligible:
            return RefundResult(status='ineligible', reason=eligibility.reason)
        
        # Human approval for large refunds
        if refund_request.amount > 200:
            approval = await workflow.execute_activity(
                request_human_approval,
                refund_request,
                start_to_close_timeout=timedelta(hours=24),
            )
            if not approval.approved:
                return RefundResult(status='denied')
        
        # Process refund
        refund = await workflow.execute_activity(
            process_refund,
            refund_request,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=5)
        )
        
        # Notify customer
        await workflow.execute_activity(
            send_notification,
            refund_request.customer_id, refund,
        )
        
        return refund
```

### Step 6: Eval Pipeline (multi-layered)

```python
class AgentEvalSuite:
    """Multi-layered eval for production agents."""
    
    async def run(self, agent, eval_set):
        results = {
            'per_step': [],
            'end_to_end': [],
            'cost': [],
            'latency': [],
            'safety': [],
        }
        
        for task in eval_set:
            start = time.time()
            
            # Run agent (with detailed tracing)
            tracer = AgentTracer()
            output = await agent.run(task.query, tracer=tracer)
            
            latency = time.time() - start
            cost = tracer.total_cost()
            
            # 1. End-to-end task completion
            success = await self.task_succeeded(task, output)
            results['end_to_end'].append(success)
            
            # 2. Per-step success
            for step in tracer.steps:
                step_success = await self.step_succeeded(step, task)
                results['per_step'].append({
                    'task_id': task.id,
                    'step': step.tool_name,
                    'success': step_success,
                    'latency': step.latency
                })
            
            # 3. Cost
            results['cost'].append({'task_id': task.id, 'cost_usd': cost})
            
            # 4. Latency
            results['latency'].append({'task_id': task.id, 'latency_s': latency})
            
            # 5. Safety
            safety = await self.safety_check(output)
            results['safety'].append(safety)
        
        return self.aggregate(results)
    
    def aggregate(self, results):
        return {
            'task_success_rate': mean([r for r in results['end_to_end']]),
            'per_step_success_rate': mean([s['success'] for s in results['per_step']]),
            'avg_cost_per_task': mean([c['cost_usd'] for c in results['cost']]),
            'latency_p99': p99([l['latency_s'] for l in results['latency']]),
            'safety_pass_rate': mean([s['safe'] for s in results['safety']]),
        }
```

**Production metrics dashboard**:

```
Per-step metrics:
  - Tool call accuracy (right tool selected?)
  - Tool arg validity (schema valid?)
  - Tool success rate (no error?)
  - Step latency p99

End-to-end metrics:
  - Task completion rate
  - Average steps per task
  - Cost per task
  - Latency p99 per task
  
Failure mode breakdown:
  - % timeouts
  - % schema fails
  - % infinite loops (caught)
  - % human escalations

Business metrics:
  - User satisfaction
  - Resolved without escalation
  - Conversion / retention
  - Cost savings vs human agents
```

### Step 7: Specific tools (2026 stack)

```
Framework:
  LangGraph (LangChain) — state machine, most flexible
  OpenAI Agents SDK — official, integrates with GPT-5
  Anthropic Claude SDK + custom — bare-bones, max control
  CrewAI — multi-agent orchestration
  LlamaIndex Agents — RAG-heavy agents

Tool protocol:
  MCP (Model Context Protocol) — Anthropic 2024, now industry standard
    - JSON-RPC over stdio / HTTP
    - Tools, resources, prompts standardized
    - OpenAI / Cohere all adopted 2025+

Durable workflows:
  Temporal — Java/Go/Python/TS, enterprise-grade
  Inngest — TS-native, serverless
  Restate — Rust, low-latency
  Cadence — Uber-spec, older

Observability:
  LangSmith — LangChain's, traces / playgrounds
  Phoenix (Arize) — open-source, OTel-based
  Langfuse — open-source alternative
  Helicone — proxy-based, easy setup

Vector stores:
  Vertex AI Vector Search — open-source, fast, mature
  Vertex AI Vector Search — managed, easy
  Weaviate — open-source, schema-aware
  Vespa — Yahoo's, hybrid search
  Milvus — open-source, scale
  pgvector — Postgres extension, simpler stack

Memory frameworks:
  Mem0 — agent memory abstraction
  LangChain memory — built-in modules
  Custom (Redis + Vertex AI Vector Search + Postgres) — best control
```

### Step 8: Production checklist (week-by-week)

```
WEEK 1 — Foundation:
  ☐ Tool registry with 3-5 critical tools (schema, idempotency)
  ☐ Plan-then-execute planner (deterministic, simpler than ReAct)
  ☐ Working memory (in-context)
  ☐ Happy-path test with 10 golden tasks
  ☐ Audit log of every tool call

WEEK 2 — Resilience:
  ☐ Retry with exponential backoff
  ☐ Timeout handling per tool
  ☐ Circuit breaker for unreliable tools
  ☐ Loop detector
  ☐ Idempotency for non-idempotent tools (idempotency_key pattern)
  ☐ Human escalation path

WEEK 3 — Memory:
  ☐ Structured KV (user prefs, business data)
  ☐ Long-term vector memory (history, examples)
  ☐ Memory loading at invocation
  ☐ Memory persistence after task

WEEK 4 — Eval:
  ☐ 100-task eval set (stratified by complexity)
  ☐ Per-step success metrics
  ☐ End-to-end task completion
  ☐ Cost and latency tracking
  ☐ Safety check (refusal on disallowed)

MONTH 2 — Production:
  ☐ Durable workflow (Temporal) for long-running tasks
  ☐ Cascade routing (small model for simple, big model for complex)
  ☐ Continuous golden set refresh from production samples
  ☐ Per-tenant isolation + ACL

MONTH 3 — Scale:
  ☐ Multi-agent (specialized sub-agents)
  ☐ Tool versioning + deprecation handling
  ☐ Cost optimization (prompt caching, smaller models)
  ☐ A/B testing framework for agent versions
```

---

## 关键决策 / 框架

### Pattern selection

```
Simple, well-defined task → Plan-then-execute
Open-ended exploration → ReAct
Complex multi-step with branching → LangGraph state machine
Multi-agent collaboration → CrewAI or custom orchestrator
Long-running / durable → Plan + Temporal/Inngest
```

### Tool design checklist

```
For every tool:
  ☐ Clear description (LLM uses this to decide when to call)
  ☐ JSON schema for input
  ☐ Idempotency contract (idempotent? idempotency_key?)
  ☐ Side-effect declaration
  ☐ Retry policy
  ☐ Timeout (per-tool SLO)
  ☐ Auth scopes required
  ☐ Versioning
  ☐ Audit log emission
  ☐ Confirmation required? (for irreversible)
```

### Memory selection

```
Use working memory (context) when:
  - Single-task duration
  - < 200k tokens of relevant info
  - Cheap (no extra round-trip)

Use structured KV when:
  - Cross-session persistence
  - Lookup by key (user_id, order_id)
  - Structured (no semantic search needed)
  - Small payload

Use vector memory when:
  - Semantic search needed
  - Cross-session history
  - Examples / few-shot from past successes
  - Large unstructured corpus
```

---

## 完整代码 / 架构图

### Full agent skeleton

```python
# agent/main.py

from langgraph.graph import StateGraph
from typing import TypedDict, Optional
import asyncio

class AgentState(TypedDict):
    task: str
    user_id: str
    user_context: dict
    intent: Optional[str]
    plan: Optional[Plan]
    completed_steps: list
    failed_steps: list
    tool_results: dict
    needs_human: bool
    final_response: Optional[str]

class ProductionAgent:
    def __init__(self, config):
        self.config = config
        self.tools = ToolRegistry()
        self.memory = MemorySystem()
        self.planner = Planner()
        self.executor = ToolExecutor(self.tools)
        self.eval = AgentEvalSuite()
        
        self.graph = self._build_graph()
    
    def _build_graph(self):
        workflow = StateGraph(AgentState)
        
        workflow.add_node('load_context', self._load_context)
        workflow.add_node('classify_intent', self._classify_intent)
        workflow.add_node('plan', self._plan)
        workflow.add_node('execute_step', self._execute_step)
        workflow.add_node('synthesize', self._synthesize)
        workflow.add_node('escalate', self._escalate)
        
        workflow.set_entry_point('load_context')
        workflow.add_edge('load_context', 'classify_intent')
        workflow.add_edge('classify_intent', 'plan')
        workflow.add_edge('plan', 'execute_step')
        workflow.add_conditional_edges(
            'execute_step',
            self._route_after_execute,
            {
                'continue': 'execute_step',
                'synthesize': 'synthesize',
                'escalate': 'escalate',
            }
        )
        workflow.add_edge('synthesize', '__end__')
        workflow.add_edge('escalate', '__end__')
        
        return workflow.compile()
    
    async def _load_context(self, state):
        state['user_context'] = await self.memory.get_user_context(state['user_id'])
        return state
    
    async def _classify_intent(self, state):
        state['intent'] = await self.planner.classify_intent(
            state['task'], state['user_context']
        )
        return state
    
    async def _plan(self, state):
        applicable_tools = self.tools.filter_by_intent(state['intent'])
        state['plan'] = await self.planner.plan(
            state['task'], state['user_context'], applicable_tools
        )
        state['completed_steps'] = []
        state['failed_steps'] = []
        return state
    
    async def _execute_step(self, state):
        next_step = state['plan'].next_step(state['completed_steps'])
        if not next_step:
            return state
        
        try:
            # Idempotency key
            idempotency_key = generate_idempotency_key(
                state['user_id'], state['task'], next_step.id
            )
            
            result = await self.executor.execute(
                next_step.tool_name,
                next_step.args,
                idempotency_key=idempotency_key,
                timeout_ms=next_step.tool.timeout_ms,
            )
            
            state['tool_results'][next_step.id] = result
            state['completed_steps'].append(next_step.id)
        
        except Exception as e:
            state['failed_steps'].append({'step': next_step.id, 'error': str(e)})
            
            if len(state['failed_steps']) >= 3:
                state['needs_human'] = True
            elif isinstance(e, RetryableError):
                # Stay in execute_step, will retry
                pass
            else:
                # Try replanning
                state['plan'] = await self.planner.replan(
                    state['task'], state['tool_results'], e
                )
        
        return state
    
    def _route_after_execute(self, state):
        if state['needs_human']:
            return 'escalate'
        if state['plan'].is_complete(state['completed_steps']):
            return 'synthesize'
        return 'continue'
    
    async def _synthesize(self, state):
        state['final_response'] = await self.planner.synthesize(
            state['task'], state['tool_results']
        )
        
        # Persist learnings to memory
        await self.memory.remember('episodic', None, {
            'task': state['task'],
            'plan': state['plan'].to_dict(),
            'results': state['tool_results'],
            'response': state['final_response'],
            'summary': await summarize(state),
        })
        
        return state
    
    async def _escalate(self, state):
        state['final_response'] = "I need to escalate this to a human. Context preserved."
        await handoff_to_human(state)
        return state
    
    async def run(self, task, user_id):
        initial_state = AgentState(
            task=task,
            user_id=user_id,
            user_context={},
            intent=None,
            plan=None,
            completed_steps=[],
            failed_steps=[],
            tool_results={},
            needs_human=False,
            final_response=None,
        )
        
        final_state = await self.graph.ainvoke(initial_state)
        return final_state['final_response']
```

---

## Gao Xin 简历专属 reframe

### BNPL chatbot — 4-tool agent

**S**: BNPL chatbot needed to handle payment FAQ + refund + payment plan + escalation.

**T**: Design agent that handles 90%+ of inbound without human.

**A**: 4-tool agent:
1. `faq_retrieve` (RAG on FAQ corpus)
2. `check_eligibility` (rules engine call)
3. `request_refund` (idempotent payment system call)
4. `escalate_to_human` (creates ticket with context)

LangGraph state machine, plan-then-execute (deterministic for compliance).
Memory: working (in-context) + structured KV (user prefs, last interaction) + vector (FAQ + past success examples).

**R**:
- 88% tasks resolved without escalation
- p99 latency 3.2s
- Avg cost $0.04/task
- Pakistan ASR outage handled gracefully (circuit breaker)

### Internal Agent Platform — 12 internal teams

**S**: Internal Agent Platform serves 12 teams (engineering, ops, finance, HR, ...). Each team needs domain-specific agent but shared infrastructure.

**T**: Build platform that supports multi-tenant agent customization without forking codebase.

**A**: Platform:
- Shared base components: planner, executor, memory, eval
- Per-team customization: tool registry (their tools), prompts, memory namespace
- MCP standard for tool exposure
- Centralized observability (Phoenix + LangSmith)
- Per-team eval pipeline (their tasks, their metrics)

**R**:
- 12 teams onboarded
- Avg time to first agent: 2 weeks (vs 2 months bespoke)
- Shared learnings (successful patterns) accelerated newer teams

### Voice agent multi-step (debt collection workflow)

**S**: Voice agent handles multi-step debt collection — confirm identity → check balance → negotiate payment plan → process partial payment → schedule follow-up.

**T**: Robust multi-step with handoff to human on edge cases.

**A**:
- Plan-then-execute (compliance audit needs deterministic logic)
- Durable workflow (Temporal) — call may pause for human input, resume later
- Idempotent partial payment tool
- Hard escalation on certain triggers (customer hostile, hardship claim, large balance)

**R**:
- Multi-step success rate 78%
- 22% escalated, 0% wrong-action (compliance pass)
- 6-language support via FT (covered in Q41)

---

## 5 个 Follow-ups

**Q1**: "Tool selection — how do you make sure agent picks the right tool?"

**A**: Multiple layers:
1. **Tool description quality** — LLM uses this to decide. Write rich descriptions: "Use this when X. Don't use when Y. Examples: Z."
2. **Few-shot in system prompt** — 2-3 examples of correct tool selection
3. **Tool filtering by intent** — pre-classify intent, only expose relevant tools (smaller decision space)
4. **Validation step** — after LLM picks tool, validate (does this tool actually fit the intent?)
5. **Eval set** — measure tool selection accuracy on golden tasks, iterate on descriptions
6. **Fallback to LLM-confirmation** — for high-stakes tools, second LLM call confirms "is this the right tool given context"

BNPL chatbot lesson: I improved tool selection accuracy by rewriting descriptions, not changing model. 70→92% routing was 60% due to better descriptions.

**Q2**: "Agent goes into infinite loop. What do you do?"

**A**: Multi-layered defense:
1. **Hard max-step limit** (e.g., 20 steps) — kill after that
2. **Loop detector** — track recent (action, args) tuples, if same repeated 3x, raise InfiniteLoopError
3. **Cost limit** — kill if task cost exceeds threshold ($1/task default)
4. **Latency limit** — kill if task duration > SLO (e.g., 5 min)
5. **Repeat-call detection** — same tool with same args called consecutively → suspicious
6. **Escalation** — when loop detected, escalate to human with full trace

Lesson: don't trust max_steps alone. Loop detection on (action, args_hash) catches subtle loops where args differ trivially.

**Q3**: "How do you test an agent?"

**A**: Multi-level eval:
1. **Tool unit tests** — each tool's contract, idempotency, schema, error cases
2. **Plan generation eval** — given task + context, LLM generates correct plan? (LLM-as-judge)
3. **End-to-end task eval** — golden task set, measure completion rate
4. **Adversarial eval** — tools fail, network issues, malformed inputs — does agent recover?
5. **Memory eval** — agent recalls past interactions correctly? cross-session consistency?
6. **Safety eval** — refusal on disallowed, no PII leak, citation accuracy
7. **Cost / latency benchmark** — per-task budget, p99 latency

Tools: LangSmith, Phoenix, Langfuse for tracing. Custom Python for eval pipelines.

**Q4**: "Agent calls a tool that has side effects (e.g., processes refund). Tool times out. What now?"

**A**: This is the **non-idempotent partial completion** problem. Steps:
1. **Idempotency key** required for all side-effect tools. If timeout, retry with same key → tool returns same result without re-doing.
2. **Audit log query** — even if no idempotency key, query: "did this refund get processed in last 5 min for this user?" before retrying.
3. **Verification step** — after suspected partial completion, agent calls a read-only verification tool ("get refund status by idempotency_key").
4. **Conservative bias** — if uncertain, DON'T retry side-effect tools. Escalate to human with full context.
5. **Customer notification** — if agent uncertain, notify customer ("We've initiated a refund. You'll receive confirmation within 24h.") and let human confirm.

**Q5**: "How do you decide between single agent vs multi-agent (specialized sub-agents)?"

**A**: Decision factors:
- **Single agent** when: task fits in one context window, < 10 tools, single LLM can handle reasoning
- **Multi-agent** when: distinct expert domains (research + writing + reviewing), tool sets too large for single planner, parallel sub-tasks possible

**Patterns**:
- **Orchestrator + workers**: main agent delegates to specialized agents
- **Hierarchical**: high-level planner → mid-level executors → low-level tool callers
- **Peer**: equal agents collaborate via shared memory

**Trade-offs**: multi-agent adds 2-5x cost (more LLM calls), latency, coordination overhead. Don't multi-agent prematurely.

Voice agent example: single agent handled debt collection. We considered splitting (identity verification agent + payment negotiation agent), but single agent with good tools sufficed. Multi-agent only justified when single agent's context / tool list overflowed.

---

## ❌ 死路答法

1. **"Use LangChain agent"** — that's a framework not a design
2. **No tool schema discipline** — production agents need contracts
3. **No idempotency story** — non-idempotent tools without keys = disaster
4. **No memory layering** — vector store for everything = wasteful
5. **No failure handling** — happy path only = breaks in production
6. **No loop detection** — agent infinite loops are common
7. **No eval methodology** — "we test by trying it" = not production-grade
8. **No durable workflow** — multi-hour tasks need Temporal/Inngest
9. **No cost / latency budget** — "agent figures it out" = $$$
10. **Forget human-in-loop** — high-stakes tasks need confirmation

---

## ✅ 加分项

1. **5-component architecture** (tool registry / planner / executor / memory / eval)
2. **Tool registry contracts** (schema, idempotency, retry, SLO)
3. **3-layer memory** (working / structured / vector) with when to use which
4. **Failure mode taxonomy** + per-failure playbook
5. **Specific 2026 tools** (LangGraph, MCP, Temporal, OpenAI Agents SDK)
6. **Idempotency key pattern** for side-effect tools
7. **Loop detection** + circuit breaker
8. **Multi-layered eval** (per-step + end-to-end + cost + latency + safety)
9. **Quote BNPL 4-tool agent + Internal Platform 12-team + voice agent durable workflow**
10. **Plan-then-execute vs ReAct vs LangGraph** distinction with use case

---

## 一句话总结

> **Production agent = tool registry (with contracts) + planner (Plan-then-Execute by default, LangGraph for complex) + executor (retry + circuit breaker + idempotency) + 3-layer memory (working / structured / vector) + multi-layered eval. Failure handling is what separates demo from production. MCP as 2026 tool standard, Temporal for durable workflows.**

---

## Cheat Sheet

```
5 components:
  1. Tool registry (contracts + schemas + idempotency)
  2. Planner (LLM, generates plan or state machine)
  3. Executor (calls tools, retry, audit)
  4. Memory (working + structured + vector)
  5. Eval pipeline (per-step + e2e + cost + latency + safety)

3 planning patterns:
  Plan-then-Execute: deterministic, auditable, simple flows
  ReAct: flexible, open-ended exploration
  LangGraph state machine: complex multi-step with branching

3 memory layers:
  Working: in-context, single invocation
  Structured KV: cross-session, lookup by key
  Vector: cross-session, semantic search

Tool contracts:
  - Description (rich, LLM uses to decide)
  - Input schema (JSON / Pydantic)
  - Idempotent? (idempotency_key required if not)
  - Side effects?
  - Retry policy
  - Timeout (SLO)
  - Auth scopes
  - Versioning

10 failure modes:
  Timeout, error return, schema fail, partial completion,
  hallucinated tool call, infinite loop, plan fail mid-execution,
  rate limit, context exhaustion, user abort

Per-failure playbook:
  Timeout: retry with exponential backoff (max_retries)
  Schema fail: ReplanAction with feedback
  Rate limit: backoff 60s, retry
  Partial completion: idempotency key OR escalate
  Auth fail: hard escalate
  Loop: kill + escalate
  Unknown: escalate P2

Resilience patterns:
  - Idempotency key for side-effect tools
  - Circuit breaker per tool
  - Loop detector ((action, args_hash) repeat)
  - Max step / cost / latency limits
  - Durable workflow (Temporal) for long-running

2026 tool stack:
  Framework: LangGraph, OpenAI Agents SDK, Claude SDK
  Protocol: MCP (Anthropic standard)
  Durable: Temporal, Inngest, Restate
  Observability: LangSmith, Phoenix, Langfuse, Helicone
  Vector: Vertex AI Vector Search, Vertex AI Vector Search, Weaviate
  Memory: Mem0, custom

Eval pipeline:
  - Tool unit tests (contract verification)
  - Plan generation (LLM-as-judge)
  - End-to-end task completion
  - Adversarial (tool fails, network issues)
  - Memory consistency (cross-session)
  - Safety (refusal, PII, citation)
  - Cost / latency benchmarks

Production checklist:
  Week 1: registry + planner + happy path
  Week 2: retry, timeout, circuit breaker, loop detect, escalation
  Week 3: 3-layer memory
  Week 4: eval (per-step + e2e + cost + latency + safety)
  Month 2: durable workflow, cascade routing
  Month 3: multi-agent, tool versioning

Anti-patterns:
  - "Use LangChain" (framework not design)
  - No tool schemas
  - No idempotency
  - No memory layering
  - No failure handling (happy path only)
  - No loop detection
  - No durable workflow for long tasks
  - No cost / latency budget

Case studies:
  - BNPL: 4-tool agent, 88% resolved, LangGraph
  - Internal Platform: 12 teams, MCP standard, shared infra
  - Voice agent: Temporal durable workflow, multi-step debt collection

Quotes for interview:
  - "5 components — registry / planner / executor / memory / eval"
  - "Tool contracts > tool functions"
  - "Plan-then-Execute by default, LangGraph for complex, ReAct for exploration"
  - "Idempotency key is non-negotiable for side-effect tools"
  - "Loop detection on (action, args) hash catches subtle loops"
  - "Durable workflows (Temporal) for anything > 5 min"
  - "Failure handling separates demo from production"
```
