## 题目

> "Your agent has been running for **50 turns** with multiple tool calls per turn. Context window is **128K tokens, now at 110K**. How do you manage so the agent doesn't degrade / break?"

或追问形态:

> "Long-running coding agent (like Cursor) — context fills up with file reads / edits / outputs. How do you decide what to **keep, summarize, drop**?"

**Round**: Context Management / Long-running Agent (45-60 min)

---

## 这道题在考什么

**Context management** 是 agent 区别于 chatbot 的关键能力:

1. **Token economy** —— context = $$$
2. **Lost in middle** —— 长 context model attention 不均
3. **Compression strategy** —— summary / pruning / hierarchy
4. **External memory** —— offload to DB / vector store
5. **Tool output handling** —— huge data 不进 context

考你是否真的做过长跑 agent 而不是 1 turn demo.

---

## 必问 clarifying

**1. Agent 性质**

> "Conversational chat (turns sparse) or work-loop (50 tool calls/turn, like Cursor)? Different shape."

**2. State 重要性**

> "Earlier turns 信息 critical (recall to make decision) or just nice-to-have?"

**3. 用户期望**

> "User expects continuous coherent multi-day session, or each session resets OK?"

**4. Model context limit**

> "Current model 128K — moving to 1M would solve? Or always more demand?"

**5. Cost budget**

> "Per-call cost matters? 128K × $0.003 = $0.40 per call adds up."

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify agent shape + state importance |
| 5-15 min | 4 strategies overview |
| 15-25 min | Summary-based compression (hierarchical) |
| 25-35 min | External memory (vector DB / KV store) |
| 35-45 min | Tool output handling + observability |

---

## 我会这样答（sample）

> "Clarify — *[假设: work-loop agent (Cursor-like), state important (avoid re-reading files), user wants multi-hour session, current 128K Claude/GPT, cost matters]*.
>
> **4 strategies, used in combination**:
>
> **Strategy 1: Sliding window** (baseline)
>
> Keep most recent N turns verbatim, drop older.
>
> Pros: simple, predictable
> Cons: loses any earlier context (file structure decisions, user preferences set turn 1)
>
> **Strategy 2: Summarize old + keep recent**
>
> ```python
> def compact(messages):
>     if est_tokens(messages) < SOFT_CAP:
>         return messages
>     
>     # Identify split point: last 10 turns kept verbatim, older summarized
>     boundary = -10
>     to_summarize = messages[:boundary]
>     keep = messages[boundary:]
>     
>     summary = llm.summarize(
>         to_summarize,
>         instructions="Preserve: decisions made, files modified, user preferences, "
>                      "open todos. Compress: full tool outputs, intermediate thinking.",
>         max_tokens=2000,
>     )
>     
>     return [SystemMessage(f"[Conversation summary so far]\n{summary}")] + keep
> ```
>
> **Hierarchical summary** (better than flat):
>
> ```
> Turn 1-50:  Detailed summary in scratchpad
> Turn 51-80: Mid-level summary
> Turn 81-90: Recent summary
> Turn 91-100: Verbatim
> ```
>
> When compaction triggers, oldest layer summarized further.
>
> **Strategy 3: External memory (offload to DB)**
>
> Not everything belongs in context:
>
> ```python
> # Instead of full tool output in history:
> tool_output_ref = blob_store.put(tool_result)  # returns id
> history.append({
>     'role': 'tool',
>     'content': f'<tool_output id="{tool_output_ref}" tool="search_inventory">'
>                f'5 results found, top 3 in summary: ...</tool_output>',
> })
> # Agent can ask: 'show full content of tool_output xyz' → load from blob
> ```
>
> **What to externalize**:
> - Tool outputs > 1K tokens (replace with summary + ref)
> - File contents (replace with file path + content hash)
> - Long intermediate reasoning (mark as 'scratchpad' offloaded)
> - User-uploaded docs (vector-DB-indexed, retrieved on demand)
>
> **Strategy 4: Selective pruning** (smart, not just oldest-first)
>
> ```python
> def prune(messages, target_size):
>     scores = []
>     for i, msg in enumerate(messages):
>         score = importance_score(msg)
>         scores.append((i, score))
>     
>     # Keep top-N by score
>     # AND always keep last 10 turns (recency)
>     # AND always keep system messages
>     # AND always keep decisions ('user said yes', 'agent chose X')
> ```
>
> Importance signals:
> - Decisions made ('user said yes to X')
> - Errors that informed retry
> - Files modified
> - Tool outputs the agent referenced later
>
> **Putting it together — compaction pipeline**:
>
> ```python
> def manage_context(messages, model_limit=128_000, target_util=0.7):
>     current = est_tokens(messages)
>     if current < model_limit * target_util:
>         return messages  # No action
>     
>     # Step 1: Externalize big tool outputs
>     messages = externalize_large_outputs(messages, threshold=1000)
>     
>     # Step 2: Selective prune intermediate reasoning
>     messages = prune_low_importance(messages)
>     
>     # Step 3: Hierarchical summarize old turns
>     if still_too_big(messages, model_limit * target_util):
>         messages = hierarchical_summarize(messages)
>     
>     return messages
> ```
>
> **Tool output handling specifically**:
>
> ```python
> def add_tool_result(history, result, threshold=1000):
>     tokens = est_tokens(result)
>     if tokens > threshold:
>         # Summarize + store full
>         summary = llm.cheap_summarize(result, max_tokens=200)
>         full_id = blob_store.put(result, ttl=session.duration)
>         history.append({
>             'role': 'tool',
>             'content': summary,
>             '_full_ref': full_id,
>         })
>     else:
>         history.append({'role': 'tool', 'content': result})
> ```
>
> Agent has tool `get_full_tool_output(ref_id)` to fetch when needed.
>
> **Vector-DB-backed memory**:
>
> For very long sessions, every old turn becomes searchable:
>
> ```python
> def archive(turn):
>     vec = embed(turn.content)
>     memory_db.insert(turn_id, vec, turn.content, metadata=...)
>
> # Agent can search past:
> def recall(query):
>     results = memory_db.semantic_search(query, top_k=5)
>     return [r.content for r in results]
> ```
>
> 'Did we talk about X earlier?' triggers vector search instead of scanning entire history.
>
> **Lost-in-the-middle problem**:
>
> Long-context model attention is U-shaped — beginning and end better recall than middle. **Mitigation**:
> - Critical info at start (system prompt) or end (recent)
> - Avoid burying decisions in turn 25 of 50
> - **Position-sensitive prompts**: 'Key decisions made: [list]' at end every N turns
>
> **Observability**:
> - **Per-turn token count + cumulative**: trend
> - **Compaction events**: when, what dropped, what summarized
> - **Recall test**: occasional 'do you remember X from earlier' → verify summary preserved
> - **Cost**: per-session $ spent
>
> **What NOT to do**:
> - Just truncate oldest blindly (lose system / decisions)
> - Single mega-summary (loses detail)
> - Keep all tool outputs verbatim (10MB tool result in context)
> - Forget cost is per-turn × all-previous-context"

---

## 简历专属 reframe

| 题 | 你做过 |
|---|---|
| Multi-turn coherence | Voice agent — multi-turn conversation, state across calls |
| External memory | Internal Agent Platform — session memory abstraction |
| Tool output mgmt | BNPL chatbot — RAG output is selected top-k not dump everything |
| Cost optimization | TikTok payment — every cent counts at scale |

**Quote**:

> "Internal Agent Platform — we hit this on a multi-step agent that browsed 20+ files. Naive append-all blew context at turn 15. Built **hierarchical memory**: per file 'index card' (path, purpose, key symbols, last-modified) cached in context; full content offloaded to a blob store, fetched on agent's `read_file` tool call. Agent sees the index in summary, only loads full when needed. Context steady at 30K tokens even at turn 50."

---

## 5 follow-ups

**Q1**: "Summary quality is critical. How tune?"
**A**:
- **Structured summary** template: 'Decisions / Files modified / Open TODOs / User preferences'
- **Cheaper LLM for summary** (gpt-4o-mini): summary doesn't need top quality
- **Test recall**: occasional probe 'what did we decide about X' → if model misses, summary improved
- **Versioned summaries**: keep both old + new during transition, prefer new if no info lost

**Q2**: "1M context models exist now (Gemini 1.5, Claude 3.7). Just use them?"
**A**:
- **Cost still matters**: 1M tokens × $0.003 = $3 per call
- **Latency**: 1M context attention has higher per-call latency
- **Lost-in-middle still real**: even with 1M, middle gets worse attention
- **Use 1M for**: cold-start (load 1 huge doc), not for accumulating 50-turn agent state
- **Hybrid**: short-term active context fits 32K, archived in vector DB

**Q3**: "Cost per session — what's economic?"
**A**: Depends. Rule of thumb:
- $0.05-0.20 per chat turn: acceptable for consumer
- $1-5 per agent task: acceptable for B2B / dev tool
- Higher → must optimize via compaction + cheaper models on summarize

**Q4**: "User says 'pick up where we left off' from yesterday's session. Practical?"
**A**:
- Persist conversation state to DB on session-end
- On resume: load last summary + last 5 turns
- Optionally: snapshot before close, semantic-index everything
- **Practical**: usually 80% restore is enough; pixel-perfect restore not worth the cost

**Q5**: "Agent forgets recent decision because compaction summarized it. How avoid?"
**A**:
- **Explicit decision log**: separate from chat history, never summarized
- **Pinned messages**: user can pin a turn, never compacted
- **Decision-tagging**: LLM tags important turns with `<decision>` metadata, summarizer treats as must-keep

---

## ❌ 易错点

1. **Truncate oldest blindly** — lose system / first turn decisions
2. **Single mega-summary** — loses detail
3. **Keep all tool outputs verbatim** — 10MB output blows context
4. **No external memory** — everything in context
5. **Ignore lost-in-middle** — critical info buried
6. **No cost monitoring** — $$$ surprise
7. **No recall test** — summary quality drifts

---

## ✅ 加分项

1. **4-strategy combination** (window + summary + external + selective)
2. **Hierarchical summary** (not flat)
3. **Externalize large tool outputs** with reference
4. **Vector-DB-backed long memory**
5. **Lost-in-middle aware** placement
6. **Decision log separate** from chat
7. **Cost + recall observability**
8. **Quote Internal Agent Platform hierarchical memory**

---

## Cheat Sheet

```
4 strategies (combine):
  1. Sliding window (baseline)
  2. Summarize old + keep recent
  3. External memory (blob / vector DB)
  4. Selective pruning (importance-scored)

Hierarchical summary:
  Turn 1-50: heavily compressed
  Turn 51-80: mid-level
  Turn 81-90: light summary
  Turn 91-100: verbatim

What to externalize:
  Tool outputs > 1K tokens
  File contents (replace with path + hash)
  Long intermediate reasoning
  User-uploaded docs (vector indexed)

Importance signals to preserve:
  Decisions ('user said yes')
  Errors that informed retry
  Files modified
  Referenced tool outputs

Tool output handling:
  > 1K tokens → summarize + blob store
  Agent has get_full_tool_output(id) tool

Vector DB memory:
  Old turns embedded + indexed
  Agent can semantic_search past

Lost-in-middle mitigation:
  Critical info at start/end
  Periodic 'key decisions' bullet
  Avoid burying in middle

Cost economics:
  $0.05-0.20/turn: consumer chat
  $1-5/task: B2B agent
  Use cheaper LLM for summarization

Observability:
  Per-turn token count
  Compaction events
  Recall probe test
  Cost per session

红线:
  - Blind truncation
  - Single mega-summary
  - Tool outputs verbatim
  - No external memory
  - Ignore lost-in-middle
  - No cost monitoring
```
