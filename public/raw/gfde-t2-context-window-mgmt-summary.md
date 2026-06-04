# 🧠 T2.3 · Context Window Management — 冲刺版

> 完整版: [gfde-t2-context-window-mgmt.html](gfde-t2-context-window-mgmt.html). 这页是 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: work-loop agent (Cursor-like), 50 turns multi-tool-call, state important (避免 re-read files), session 4-8h, Gemini 3 Pro main + Flash summary, model limit 1M (Pro), cost target $0.50/session, recall test 周度."

**4-strategy combined pipeline**:

### Layer 1: Trigger + 4 strategies

- **Trigger**: soft cap 70% of model limit (e.g., 700K of 1M Pro) → compact; hard cap 90% → emergency aggressive
- **Sliding window**: last 10 turn verbatim
- **Hierarchical summary**: 4 tier
- **External memory**: blob (>1K tool out) + Vertex AI Vector Search (episodic) + Postgres (decisions)
- **Selective pruning**: importance score + pinned messages

### Layer 2: Hierarchical 4 tier (核心)

```
Tier 1: ancient (turn 1-30, heavy compress, 500 tok target)
Tier 2: middle (turn 31-40, medium summary, 1500 tok)
Tier 3: recent (turn 41-50, light summary, 5000 tok)
Tier 4: latest (verbatim last 5-10 turns, 10K tok)

Cascade: tier 4 full → 移动 oldest 到 tier 3 (light summarize)
         tier 3 full → cascade to tier 2 (medium)
         tier 2 full → cascade to tier 1 (heavy)
```

**为何 hierarchical > flat single summary**: no re-summarize drift (tier 1 只压缩一次, 不反复磨), granular control, cost economy (大部分操作只动 tier 4→3 低成本).

### Layer 3: External memory 3 store

```
Blob (Cloud Storage / GCS):
  - Tool outputs > 1K tokens (full)
  - Uploaded files, agent artifacts
  - Key by content hash, 24h TTL, agent 用 get_full_tool_output(ref_id)

Vector DB (Vertex Vector Search / Vertex AI Vector Search):
  - Episodic memory: tier 2/3 summary 进 index
  - User-uploaded doc chunks
  - Agent recall_past_memory(query) tool

Structured (Postgres / Cloud SQL):
  - decisions table (turn, decision_text, rationale)
  - user_preferences (key, value, source_turn)
  - session_state
  - 永远不进 summary, 永远再注入 system prompt
```

### Layer 4: Lost-in-middle defense + cost

- **Placement**: critical info (system + decisions) 头**和**尾, 中间放 less critical
- **Periodic recap**: 每 10 turn 注入 "key decisions / preferences / open todos"
- **Decision log**: Postgres separate from chat, render_for_prompt() 每 turn re-inject
- **Prefix caching**: Anthropic 5min ephemeral / Gemini 1h, cache hit ~10% normal rate, 9 折省

### Edge cases (背 5 个)

- **EC1 Blind truncate oldest**: 丢 turn 1 user 要求 (FastAPI) → agent 改成 Flask → 用 hierarchical + pinned + decision_log Postgres 永久存.
- **EC2 Single mega-summary**: "前 50 turn 摘要" 失细节 + 反复 summarize drift → hierarchical 4 tier, tier 1 只 summarize 1 次, no drift.
- **EC3 Tool output 10MB pytest**: 直接 inline 爆 context → externalize threshold >1K tok 到 blob + summary (Flash) + ref_id, agent 调 get_full_tool_output(ref) 按需 fetch; > 50K reject + force pagination.
- **EC4 Lost in middle**: 关键 decision 埋中间 attention 弱 → decision_log Postgres separate, 永远 re-inject system prompt 末尾; periodic recap 每 10 turn.
- **EC5 Summary 静默坏掉**: agent 忘东忘西无 metric → recall probe 周度 ('what did we decide about X?' → 失败 alert), summarizer 调优.

### Production hardening (1 min)

- **Per-turn metrics**: input/output tokens, cost, compaction_event yes/no
- **Cumulative**: session_cost, session_turns, compaction_count
- **Recall probe**: random fact verify weekly
- **Cost alert**: session > $1 (target $0.20-0.50), $5 hard cap pause
- **Cost dashboard**: avg / p99 session cost, expensive sessions top-10
- **Async compaction**: 不 block user (background, 用旧 context 继续, 完后 swap)
- **Routing**: Gemini 3 Pro main loop + Flash for summary + Haiku for tool routing (cost-aware)

### 🪝 Resume hook

"Internal Agent Platform multi-step agent 浏览 20+ files: naive append-all blew context at turn 15. Built hierarchical memory: 每 file 'index card' (path, purpose, key symbols, last-modified hash) 留 context, full content offload Cloud Storage blob, agent `read_file` tool 按需 fetch. Decisions ('user confirmed FastAPI', 'Postgres not MySQL') Postgres decision_log re-inject system prompt 每 turn. Context steady 30K tokens 即便 turn 50. Cost $4 → $0.30 per session. 单点最大胜利是 prefix caching — 同 project 50K context, Anthropic ephemeral 90% off after first call."

---

## 🔥 5 Follow-ups (面试官会问)

**Q1: Summary quality 很关键, 怎么调?**
Structured template ('Decisions / Files modified / Open TODOs / User preferences / Errors'); cheap LLM (Gemini 3 Flash $0.50/$3 够, 不用 flagship); recall probe weekly (failure → alert summary regressed); versioned summary A/B; distilled summarizer if domain repeatable (SFT small model on (long turns, ideal summary) pair).

**Q2: 2M context 模型 (Gemini 3 Pro 2M) 就行了, 还要 compaction?**
要. Cost: 2M × $4/1M (>200K tier) = $8/call × 100 turn = $800/session 不可持续. Latency: 2M first-token 60-120s. Lost-in-middle: even 2M middle 30-40% gap. Use 2M for cold-start (load 1 huge doc), 不为 accumulate 50-turn state. Hybrid: short-term active context 32K + archived Vertex AI Vector Search.

**Q3: Cost / session 什么经济?**
按 segment: consumer chat $0.001-0.01/turn (Flash); B2B / pro $0.05-0.20/turn (Pro); dev tool / enterprise $0.50-3/agent task (mixed Pro + Opus); session $0.20-2 normal, $5+ problematic. Optimize via hierarchical compaction + cheaper Flash on summary + prefix caching.

**Q4: User 说 "接着昨天的", multi-day session 实际?**
Postgres 持久化 session_id / turns / decisions / preferences on session-end; resume 时 load last summary + last 5 turns + system prompt 注入 decisions; 可 snapshot 全 state + semantic-index Vertex AI Vector Search. **80% restore 够, pixel-perfect 不值**. User confirm: "上次我们 X, 接着 Y, 对吗?" explicit handshake.

**Q5: Agent 忘了最近 decision 因为 compaction 把它压没了?**
Explicit decision_log in Postgres, separate from chat, never compacted; pinned messages (user 可 pin, summarizer 跳过); decision-tagging — LLM 输出 schema 含 `decision_made` field, summarizer 必 keep; periodic recap 每 10 turn re-inject; recall probe 测 'do you remember X' fail trigger alert.

---

## ❌ 易错点 (10 条红线)

1. Truncate oldest blindly — 丢 system prompt / 第 1 turn 关键决策
2. Single mega-summary — "前 50 turn 摘要" 失细节 + re-summarize drift
3. Keep all tool outputs verbatim — 10MB pytest output 直接爆
4. No external memory — 一切塞 context, 注定爆
5. No pinning — summarizer 把 "user said yes to X" 压没
6. Ignore lost-in-middle — critical info 埋中间 attention 弱
7. No cost monitoring — Session 花 $20 老板才发现
8. Summary 用 flagship LLM — 浪费, Flash 足够
9. No recall test — summary 静默坏掉
10. No prefix caching — leave 90% savings on table

---

## ✅ 加分项 (10 条)

1. **4-strategy combination** (sliding + hierarchical + external + selective)
2. Hierarchical 4 tier (not flat), no re-summarize drift
3. Externalize large tool outputs (>1K) with ref + dedup cache
4. Vector-DB-backed episodic memory + agent `recall_past` tool
5. Structured Postgres for decisions / preferences (never compacted)
6. Lost-in-middle aware placement + periodic recap every 10 turn
7. Decision log separate from chat history
8. Pinned messages (user + auto-pin patterns)
9. **Prefix caching** (Anthropic 5min / Gemini 1h) 90% off
10. Quote Internal Agent Platform hierarchical memory $4 → $0.30

---

## 一句话总结

Context mgmt = **「Sliding 最近 + Hierarchical summary 4 tier + External memory (blob/vector/postgres) + Selective pruning + Pinning + Decision log + Lost-in-middle 觉知 + Prefix caching 省钱」**. 长跑 agent 稳定性的核心: **context size 不随 turn 数线性增长, cost/session 可控**.

---

## 🃏 Cheat Sheet (印 1 页随身)

```
4 compaction strategies (combine, NOT either-or):
  1. Sliding window      last N turn verbatim
  2. Hierarchical summary 4 tier (ancient/mid/recent/latest)
  3. External memory     blob + vector DB + Postgres
  4. Selective pruning   importance score + pinned

Trigger:
  Soft cap 70% of model limit → compact
  Hard cap 90% → emergency aggressive

Hierarchical 4 tier:
  Tier 1: ancient (turn 1-30, heavy, ~500 tok)
  Tier 2: middle (31-40, medium, ~1500 tok)
  Tier 3: recent (41-50, light, ~5000 tok)
  Tier 4: latest (verbatim, last 5-10 turn)
  Cascade: tier 4 满 → push old to tier 3 → ... → tier 1

External memory (3 store):
  Blob (Cloud Storage/GCS)  tool outputs >1K, files, artifacts
                            key by content hash, 24h TTL
  Vector DB (Vertex)        episodic (tier 2/3 summary), agent recall_past
  Postgres / Cloud SQL      structured (decisions, prefs, session_state)
                            NEVER compacted

Tool output thresholds:
  ≤ 1K tok:  inline
  1K-5K:     summarize (Flash) + blob ref
  5K-50K:    minimal summary + blob ref
  > 50K:     reject / force pagination (refine query)

Pin/preserve patterns:
  System prompt | user preferences | confirmed decisions
  Errors that informed strategy | files modified | open TODOs

Lost-in-middle defense:
  Critical info at start AND end of context
  Periodic recap every 10 turn (decisions + prefs + todos)
  Decision log Postgres → render_for_prompt() every turn
  Pinned messages

Cost (2026 per 1M):
  Pro $2 (≤200K) / $4 (>200K) / $12 out
  Flash $0.50 / $3 ← summary用这个
  Opus 4.7 $5/$25 (200K) | Sonnet $3/$15 | Haiku $1/$5 ← tool routing
  GPT-5.5 $5/$30 (256K)

Per-session cost (30-turn):
  No compaction Pro:           $3-6 (degrades turn 20+)
  Sliding only:                $0.50 (loses early)
  Hierarchical + Flash:        $0.45 ⭐
  + Prefix caching:            $0.20 ⭐⭐
  Aggressive cheap:            $0.05 (worst quality)

Prefix caching:
  Anthropic ephemeral: 5min TTL, cache_control on system block
  Gemini context cache: 1h TTL, $1/1M/h storage
  Cache hit ~10% of input (90% off)

GCP stack (2026):
  Cloud Storage (blob), Vertex Vector Search (episodic)
  Cloud SQL Postgres (decisions/prefs/state)
  Cloud Trace/Logging (per-turn cost), Pub/Sub (async compact)
  Memorystore Redis (hot cache, dedup tool out)
  AWS: GCS / Vertex AI Vector Search / RDS / Firestore / Bigtable

Observability:
  Per-turn: input/output tokens, cost, compaction event
  Cumulative: session_cost, turns, compactions
  Recall probe weekly | Cost dashboard avg/p99 (target <$1)
  Top-10 expensive session investigation

Recall probe:
  Random fact from compacted history
  Probe: 'what is user pref for X?' → expected vs LLM semantic match
  Fail → alert summarizer regressed → tune

红线:
  - Blind truncation
  - Single mega-summary (drift)
  - All tool outputs verbatim
  - No external memory
  - No pinning
  - Ignore lost-in-middle
  - No cost monitoring
  - Summary uses flagship (Flash 够)
  - No recall probe
  - No prefix caching
```
