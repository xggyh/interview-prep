## 题目

> "You're designing the API for an agent service. Should the **agent itself be stateless or stateful**? Walk through the trade-offs, and recommend for: (a) a customer-support chatbot, (b) a long-running coding agent, (c) a voice agent."

或追问形态:

> "OpenAI's API is stateless (you pass full history each call). Why? When would you choose differently?"

**Round**: System Design (45 min)

---

## 这道题在考什么

考你**production architecture trade-off** 理解:

1. **Stateless 优势** —— scale, failover, simplicity
2. **Stateful 优势** —— latency, cost (context cached), state proximity
3. **Per-use-case 选择** —— 同一个产品里可能 mix
4. **Hybrid pattern** —— server-side cache + client-passes-conversation-id

---

## 必问 clarifying

**1. Latency target**

> "Per-request — < 500ms (voice) or 5s (batch) OK? Stateless adds context reload overhead."

**2. State 大小**

> "Per-session state how big — 1KB (chat) or 1MB (coding agent file edits)?"

**3. Multi-tenant**

> "Same instance serves N users or partitioned?"

**4. Cost sensitivity**

> "Per-token cost matters? Stateless re-sends full context every call."

**5. Failover requirement**

> "Single-node failure should preserve session or OK to start fresh?"

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify latency / state size / cost / failover |
| 5-15 min | Definitions + 4 axes of comparison |
| 15-25 min | Per-use-case recommendation (a/b/c) |
| 25-35 min | Hybrid: server-cache + client-id |
| 35-45 min | Implementation details + observability |

---

## 我会这样答（sample）

> "Defining first:
>
> **Stateless**: Each request carries all state. Server has no per-session memory.
>
> **Stateful**: Server remembers per-session state across requests.
>
> **4 axes of comparison**:
>
> | Axis | Stateless | Stateful |
> |---|---|---|
> | **Latency** | + Context rebuild every call | Low (state cached) |
> | **Scalability** | Horizontal trivial | Sticky session / state replication |
> | **Cost (tokens)** | Re-send context every call | Send only delta |
> | **Failover** | Any node can serve next request | Need state replication or re-warm |
> | **Multi-tenant** | Easy (no per-tenant state on server) | Per-tenant memory mgmt |
> | **Debugging** | Reproducible (all in 1 request) | State must be snapshotted |
>
> **OpenAI / Anthropic / Google chose stateless** because:
> - Scale to 10M+ concurrent users
> - Horizontal scale without sticky session
> - Idempotent: same input → same output (debug-friendly)
> - Failover trivial
> - Cost: with KV-cache, partial state cached on server side anyway (hybrid in practice)
>
> **Recommendations per use case**:
>
> **(a) Customer-support chatbot**:
>
> ✅ **Stateless** (default)
>
> - Conversation 5-15 turns avg
> - Concurrent users 10K+
> - Per-request 200ms acceptable
> - User can resume from any device → state in DB not in-memory
>
> ```python
> # Client sends full history (or refers to conversation_id)
> POST /chat
> {
>   "conversation_id": "abc",
>   "user_message": "...",
> }
> 
> # Server (stateless):
> 1. Load conversation history from DB by conversation_id
> 2. Append user message
> 3. Call LLM with full context (with KV cache hit)
> 4. Save response to DB
> 5. Return response
> ```
>
> **(b) Long-running coding agent (Cursor-like)**:
>
> ⚠️ **Hybrid**:
>
> - Session lives hours, many edits
> - State (open files, working dir) large
> - Per-request latency sensitive (< 1s for autocomplete)
> - Failover OK to restart session on new node
>
> ```python
> # Stateful working memory + stateless API surface
> # Sticky session by conversation_id
> # State (open files, history) cached in-process, backed up to DB every 30s
> # On node failure, next request goes to any node, reloads from DB checkpoint
> ```
>
> **(c) Voice agent**:
>
> ✅ **Stateful with WebSocket / streaming**
>
> - Per-turn latency < 300ms hard
> - Audio + ASR + LLM + TTS pipeline shares state
> - Connection-bound (WebSocket)
> - Failover means dropped call (acceptable cost)
>
> ```python
> # WebSocket connection per call
> # Audio streamed in, response streamed out
> # State (transcript, user_id, conversation) lives in connection-handling actor
> # On disconnect: clean up; on reconnect: new session
> ```
>
> **Hybrid pattern (most common in production)**:
>
> Server is **logically stateless** (any node serves any request) but uses **caching layers**:
>
> ```
> 1. Client passes `conversation_id`
> 2. API gateway routes to any backend node
> 3. Node looks up state from:
>    a. In-process LRU cache (last 1000 active conversations)
>    b. Redis cache (last 10K, TTL 1h)
>    c. Postgres (source of truth)
> 4. Process request, update cache + persist
> 5. KV cache for LLM prefix: server-side cached, reused across requests
> ```
>
> **Benefits**:
> - Logically stateless: horizontal scale + failover
> - Practically fast: 95% in-process cache hit
> - KV-cache: LLM prefix reused
>
> **KV-cache critical**: with conversation history same prefix turns, LLM serving (vLLM / OpenAI internal) caches the KV computation. **Same conversation re-uses cache**, even if 'stateless' API.
>
> **Concrete implementation**:
>
> ```python
> async def chat_handler(request):
>     conv_id = request.conversation_id
>     
>     # Cache-tier lookup
>     state = await conv_cache.get(conv_id)  # in-process → Redis → DB
>     
>     # Append new turn
>     state.add_user_message(request.message)
>     
>     # LLM call (server-side KV cache by prefix)
>     response = await llm.generate(
>         messages=state.messages,
>         conversation_id=conv_id,  # hint to LLM serving for KV reuse
>     )
>     
>     state.add_assistant_message(response)
>     await conv_cache.set(conv_id, state)  # write-back
>     await db.persist_async(conv_id, state)  # async durable
>     
>     return response
> ```
>
> **Observability differs**:
>
> | Aspect | Stateless | Stateful |
> |---|---|---|
> | Trace | Per-request | Per-session + per-request |
> | Replay | Trivial (input → output) | Need state snapshot |
> | Cost track | Per-call tokens | Per-call delta tokens |
>
> **What NOT to do**:
> - Make stateless API but require sticky session (worst of both)
> - Make stateful but no failover plan
> - Skip KV cache opportunity (huge cost win)
> - Mix model semantics within product without explicit contract"

---

## 多场景变体 + 解法

### 变体 1: Customer service chatbot

> "电商 chatbot, 10K 并发用户, 每对话 15 turn。"

**解法**: **Stateless + DB-backed**
- REST API, client 传 `conversation_id`
- Server 每 turn 从 Postgres load 历史, 调 LLM, 写回
- KV-cache server-side 复用 prefix (vLLM 自动)
- 上 in-process LRU (1000 hot conversation) 减 DB hit
- Failover: any node 任意 request — Postgres 是 source of truth

### 变体 2: Code-completion agent (Copilot-like)

> "IDE 内 auto-complete, 每 keystroke 触发。<200ms latency budget。"

**解法**: **Stateful per IDE session (WebSocket)**
- 长连接 sticky session
- Per-session state: open files, recent edits, cursor position
- 高频小 request (auto-complete) 不能每次重传 100 个文件 context
- Failover: 断连 → 客户端重连, 短期 client-side state 也可重 init
- Cache: file content hash, 改动小时重用

### 变体 3: Voice agent

> "电话客服 voice agent, 全程 WebSocket, < 300ms latency"

**解法**: **Strict stateful**
- Per-call actor 持有: ASR transcript, LLM context, TTS queue
- Single-node, connection-bound
- Failover ≈ drop call (acceptable, retry call)
- 不写 DB on every turn (太慢) — checkpoint every 10s
- 通话结束 final transcript 落库

### 变体 4: Long-running data pipeline agent

> "Agent 跑数据 ETL, 每个 job 几小时 ~ 几天。"

**解法**: **Stateful via workflow engine (Temporal/DBOS)**
- Workflow_id 是 logical state
- Execution 可跨多 worker node (workflow engine 接管 state)
- Per-step durable checkpoint
- Failover: workflow 在新 worker 继续从最后 checkpoint
- 不需 sticky session — workflow engine routing

### 变体 5: Multi-user collaborative agent (Notion AI / Figma)

> "多用户同协作, agent 看所有人的 edit"

**解法**: **Hybrid, document-bound**
- Per-document agent 实例 (state = doc state)
- 多 user 看同一 agent (broadcast 决策)
- CRDT / OT 处理 user 编辑 race
- Agent 输出广播给所有在线 user (publish/subscribe)
- Persist: document state 持久, agent 'memory' 周期 snapshot
- 离开后归档, 重新打开 reload

---

## 简历专属 reframe

| 题 | 你做过 |
|---|---|
| Stateful voice agent | Voice agent over WebSocket — you've done this |
| Stateless chat | BNPL chatbot likely stateless or hybrid |
| KV cache opt | vLLM / SGLang infra — KV-cache is your area |
| Cache hierarchy | TikTok payment — in-process + Redis + DB pattern |
| Multi-tenant | Voice agent 7 markets — per-tenant isolation |

**Quote**:

> "Voice agent had hard stateful constraint — WebSocket-bound, audio streaming. State per call in connection-handling actor. Designed for **single-call failover acceptable** — if a call dropped, retry was OK UX-wise. But the BNPL chatbot we designed stateless: each REST call rebuilds context from DB. Latency overhead acceptable (~200ms) vs scale benefit (horizontal). Same team, two paradigms, by use-case shape."

---

## 5 follow-ups

**Q1**: "KV-cache — how big a win in real numbers?"
**A**:
- 1 conversation, 10 turns, avg 1K tokens history. Without KV cache: 10K tokens prefill compute × 10 turns.
- With cache: 1K (turn 1) + 1K each turn (just new content). 5-10x faster.
- Real cost: prefill is the expensive part of LLM serving. Cache hit means most cost saved.

**Q2**: "Conversation 100 turns, history 50K tokens. Stateless re-sends 50K every turn — wasteful?"
**A**:
- Yes wasteful **network-bandwidth**-wise
- BUT LLM cost-wise: KV cache on server hides this (server doesn't re-compute)
- Real waste: network bytes shipped
- Optimization: client sends conversation_id only, server reconstructs (server-side cache)

**Q3**: "Conversation across multiple devices. State sync?"
**A**: DB is source of truth:
- Conversation persisted on every turn
- Device A loads state on connect
- Device B reads from DB on connect → sees A's recent turns
- Real-time sync: WebSocket push from server when state updated

**Q4**: "Failover scenario — node serving session crashes mid-LLM-call. State?"
**A**:
- Pre-write user message to DB before LLM call → no loss
- LLM call in-flight: idempotency key allows retry (different node)
- Response: stream replays via durable queue (or just retry)
- Cost: 1 wasted partial LLM call, < 1s recovery

**Q5**: "Latency-sensitive (voice) but want failover. Possible?"
**A**: Hard but doable:
- Replicate state to 2-3 nodes (active-active or active-passive)
- Per-turn state sync (small delta)
- On failure: failover node has near-current state
- Some packets / utterances may be lost during failover (~200ms gap)
- Not zero-loss, but near-seamless

---

## ❌ 易错点

1. **Stateless = no state anywhere** — wrong, server cache fine
2. **Stateful = single-node** — wrong, can replicate
3. **Sticky session for stateless API** — worst of both
4. **No KV cache awareness** — leave money on table
5. **Mix paradigms in 1 product without contract**
6. **Stateful without failover plan**
7. **Re-send 50K tokens every call** — bandwidth waste

---

## ✅ 加分项

1. **4-axis comparison** (latency / scale / cost / failover)
2. **Hybrid pattern** (logically stateless + cache hierarchy)
3. **KV-cache** as cost-saving mechanism
4. **Per-use-case recommendations** with rationale
5. **DB as source of truth**, in-process + Redis cache
6. **Failover patterns** by use case
7. **Voice WebSocket** vs **chat REST** contrast
8. **Quote voice agent + BNPL contrast**

---

## Cheat Sheet

```
Stateless:
  + Horizontal scale trivial
  + Failover trivial
  + Reproducible debug
  - Context rebuild latency
  - More tokens sent

Stateful:
  + Low latency
  + Less tokens
  - Sticky session / replication
  - Per-tenant state mgmt
  - Debug needs snapshot

Decision matrix:
  Chat (10-15 turns, 10K users) → Stateless
  Long agent (hours, large state) → Hybrid sticky+failover
  Voice (< 300ms, WebSocket) → Stateful per-conn

Hybrid pattern (most prod):
  Stateless API surface
  In-process LRU (active 1K)
  Redis (active 10K, 1h TTL)
  Postgres (source of truth)
  KV-cache server-side

KV cache critical:
  Without: prefill cost × every turn
  With: 5-10x speedup
  Server-side, transparent to client

Failover plans:
  Stateless: any node serves next
  Stateful chat: state in DB, reload on new node
  Voice: drop call, accept lost session

Observability:
  Stateless: per-request trace
  Stateful: per-session + per-request

红线:
  - Sticky session for stateless API
  - Stateful without failover
  - No KV cache awareness
  - Mix paradigms no contract
```
