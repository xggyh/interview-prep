## T2.3 · context window 管理 — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/gfde-t2-context-window-mgmt.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t2-context-window-mgmt.html`](questions/gfde-t2-context-window-mgmt.html)

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

50-turn agent 不挂 = **compaction + external memory + tool externalization + lost-in-middle defense + cost budget**, 5 件套, 不是单 truncate; context 稳态 30K 而非随 turn 数线性涨, 成本从 $6/session 降到 $0.50.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| **Context window** | LLM 单次输入容量 (Gemini 3 Pro 2M / Claude 200K) | 物理限制 |
| **Effective context** | Attention 实际利用的部分 (常 < 1/3 of window) | Lost-in-middle 区域不算 |
| **Compaction** | Messages 转更短表示, 保关键弃冗余 | 软上限触发 |
| **Sliding window** | 仅保最近 N turn verbatim | 短会话 baseline |
| **Hierarchical summary** | 4-tier ancient/middle/recent/latest | Long agent ⭐ |
| **Selective pruning** | 按 importance score (LLM-judge) 砍低分 turn | Hybrid 配合 |
| **External memory** | Blob (S3) + Vector DB (Qdrant) + Structured (Postgres) | 数据 > 1K 不进 context |
| **Tool output externalization** | > 1K 存 blob, 留 short summary + ref_id | 防爆 |
| **Lost in middle** | Liu 2023, attention U 形, 中部 30-40% recall | Long ctx 通用问题 |
| **Pinned message** | 永不被 compact 的关键 turn | 系统决策 / 用户偏好 |
| **Decision log** | system prompt 内追加的 mini-summary | Anti-lost-middle |
| **Recall probe** | 随机抽事实验 summary 质量 | Weekly QA |
| **Periodic reinforcement** | 每 10 turn 注入 reminder | 防遗忘关键约束 |
| **Prefix cache** | Anthropic 5min / Gemini 1h, 90% off cached | 长 system prompt reuse |
| **Per-session budget** | $ / token 上限 hard cap | 成本可控 |

### 🎯 5 个核心 framework

**Framework 1**: Compaction Strategies (4 法)
- When: input > soft cap (70% 模型上限)
- Algorithm: combine sliding + summarize + hierarchical + selective
- Trade-off: aggressive 失细节, lazy 爆 budget
- Tools: LangChain ConversationSummaryBufferMemory, LlamaIndex memory, MemGPT

**Framework 2**: External Memory (3 层 store)
- When: 任何 long agent
- Algorithm: Blob (S3, tool outputs > 1K) + Vector DB (Qdrant, episodic search) + Postgres (decisions/prefs/state)
- Trade-off: 1 extra hop, 但 context 不爆
- Tools: S3 / GCS, Qdrant / Pinecone, Postgres / Redis / DynamoDB

**Framework 3**: Tool Output Externalization
- When: tool result > 1K token
- Algorithm: 阈值分层 (1K inline / 5K summarize+ref / 50K minimal+ref / >50K reject); per-tool summary
- Trade-off: 额外 retrieve hop, 但成本 $ / latency 都降
- Tools: blob ref_id, per-tool summarizer (Flash)

**Framework 4**: Lost-in-Middle Mitigation
- When: 任何 > 50K context
- Algorithm: critical info at start AND end; periodic recap every 10 turn; decision log in system; pinned messages
- Trade-off: 额外 prompt tokens, 但 recall +20-40%
- Tools: pinned_messages list, periodic recap function

**Framework 5**: Cost Economics + Budget Enforcement
- When: 始终
- Algorithm: 2026 pricing routing (Flash 简单 / Pro 推理 / Haiku batch); prefix cache 90% off; per-session $ alert; cost-quality slider
- Trade-off: 更复杂 router, 但 cost $6→$0.50
- Tools: Anthropic prompt cache, Gemini context cache, per-session cost tracker

### 🌳 关键决策树 (ASCII)

```
Q: 我应该几时 compact?
├── Input < 70% 限             → 不动 (lazy)
├── 70-90% (soft cap)          → Normal compaction (hierarchical)
├── > 90% (hard cap)           → Emergency aggressive compact
└── 新 turn 来了                → Pre-call check + 再 compact

Q: tool output 怎么处理?
├── ≤ 1K tok                   → Inline 全留
├── 1K-5K                      → Summarize (Flash) + blob ref
├── 5K-50K                     → Minimal summary + blob ref
└── > 50K                      → Reject / 强制 paginate

Q: 哪些 turn 该 pin (永不 compact)?
├── System prompt              → 永远
├── 用户明确 preference        → "use FastAPI" / dark mode
├── 已确认决策                 → "use Stripe API v3"
├── 错误教训                   → "Pyright detected X, switch to Y"
├── 文件修改记录               → path + hash + change summary
└── Open TODO                  → 未完成任务列表

Q: 用什么模型省钱?
├── Compaction / summary       → Gemini 3 Flash ($0.50/$3) ⭐
├── 推理 / 复杂决策            → Claude Opus 4.7 / Gemini 3 Pro
├── 批量 background            → Claude Haiku 4.5
└── 长 prefix reuse            → 加 prefix cache
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: Compaction Strategies (4 法)**
- Sliding window: 最近 N turn verbatim (baseline, 短会话)
- Summarize old + keep recent: 老 turn → 1 段 LLM summary, 近 N verbatim
- Hierarchical (4 tier): ancient (turn 1-30, 500 tok heavy) / middle (31-40, 1500 tok med) / recent (41-50, 5000 tok light) / latest (verbatim 5-10 turn) ⭐
- Selective pruning: 每 turn LLM-judge importance score, 低分砍
- 整合: hierarchical (主) + selective (辅), trigger at soft cap 70%, emergency at 90%
- Top 3 gotchas: blind truncate / single mega-summary 失结构 / 不 pin 关键
- Tools: LangChain ConversationSummaryBufferMemory, MemGPT, LlamaIndex memory

**Problem 2: External Memory Architecture**
- 3 层 store: Blob (S3) → tool outputs / files / artifacts; Vector DB (Qdrant) → episodic memory, embed 老 turn; Postgres → 结构化 (decisions, preferences, session_state)
- Blob usage: store(content) → ref_id, agent tool fetch(ref_id) on demand
- Vector DB: 老 turn segment → embed → upsert with metadata (turn#, ts, type)
- Postgres schema: session_id, key, value, type (decision/pref/state), created_at
- 一致性: write-through (decision 先 Postgres 后 context); read-back probe
- Top 3 gotchas: 不 externalize 大输出 / vector DB cross-session 混 / Postgres 没 session_id 隔离
- Tools: S3 / GCS / Azure Blob, Qdrant / Pinecone, Postgres / Redis / DynamoDB

**Problem 3: Tool Output Externalization**
- 阈值: ≤1K inline / 1K-5K summary+ref / 5K-50K minimal+ref / >50K reject
- Smart summary by type: SQL → stats + sample 5 rows; file read → first/last + lines; web search → title + snippet; image → caption + features
- Provenance: ref_id + tool + executed_at + original_query → 后续可 retrieve full
- Avoid dup: detect file re-read (path hash) → reference earlier ref_id, 不 re-store
- Top 3 gotchas: 阈值过松 / 没 ref_id / 重复 store same content
- Tools: 自实现 store layer + Redis dedup hash + presidio for PII before store

**Problem 4: Lost-in-Middle Mitigation**
- 现象: Liu 2023 U-shape; Gemini 3 Pro 2M 中部仍 30-40% recall gap
- Placement: system → history (compacted) → retrieved → query (critical 在 start 和 end)
- Periodic reinforcement: every 10 turn 注入 "## Reminder (turn N)" + 关键 decisions
- Decision log: system prompt 内追加 mini-summary ("- Use FastAPI - Stripe v3 - retry 3x")
- Pinned messages: list of (turn_id, content, importance), 不被 compact, 总放 prompt 末尾
- Recall probe: 每周抽样 100 session, 问 summary 涵盖 fact, 答对 < 80% → 调 compaction
- Top 3 gotchas: 没 reinforce / 没 pin / pin 太多反爆
- Tools: 自实现 pinned_messages list + periodic recap

**Problem 5: Cost Economics + Budget**
- 2026 pricing: Gemini 3 Pro $2 (≤200K) / $4 (>200K) / $12 out; Flash $0.50/$3; Opus 4.7 $5/$25; Sonnet 4.6 $3/$15; Haiku 4.5 $1/$5; GPT-5.5 $5/$30
- 公式: per-turn = (input_tok × in_price) + (out_tok × out_price); session = Σ per-turn
- Routing: 简单 query Flash, 推理 Pro/Opus, batch background Haiku, 长 prefix 加 cache
- Prefix cache: write surcharge 1.25-2x, hit 0.10x; Anthropic 5min / Gemini 1h; 50K project ctx hit 80%+ 节省 80% cost
- Per-session budget: hard cap $1, soft warn $0.50, dashboard p50/p95/p99
- Cost-quality trade-off: 80% Flash + 20% Opus 决策, 而非全 Opus
- Top 3 gotchas: 全 Opus / 不 cache / 没 budget alert
- Tools: 自实现 cost tracker, OTel attributes (model, tokens), prompt cache headers

### 🔥 Production gotchas (top 15)

1. Blind truncate (FIFO 砍最老) → 失关键决策
2. Single mega-summary one-shot → 失结构, 不能 update
3. Tool output 全 inline (50K+) → context 爆
4. 没 external memory → 一次性 in-context
5. 没 pin / pinned messages → 关键决策被 compact
6. 忽略 lost-in-middle → 中部 turn 答错率高
7. 没 cost monitoring → session $50 才发现
8. 没 recall probe → summary 质量盲飞
9. 没 prefix cache → 长 system prompt 每 turn 全价
10. Cross-session memory 混 → 跨用户泄漏
11. Compact 在每 turn (over-eager) → cost 反升
12. 没 emergency hard cap → 爆 context 全挂
13. 所有 turn 全 Opus → 4-5x cost
14. Decision log 没更新 → 旧决策仍在 prompt
15. Recall probe < 80% 不管 → silent quality drift

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Compaction | Voice agent 7 markets | 10-20 turn 20K+ tok, hierarchical 4-tier + recent 5 verbatim, token 减半 |
| External memory | BNPL multi-turn agent | Postgres (decisions) + Qdrant (history embed) + S3 (tool blob) |
| Tool externalization | ConvFinQA 5 calc tools | Tool result > 5K 走 blob ref, summary inline, context 稳态 30K |
| Lost-in-middle | Voice agent | Decision log + pinned + periodic recap 每 10 turn, 关键 recall 95%+ |
| Cost / routing | Internal Agent Plt | Flash 简单 + Opus 推理 + Haiku batch, session $ ↓ 60% |
| Prefix cache | BNPL chatbot | 30K system prompt, Anthropic 5min cache, hit 70%, $ 80% off |
| Per-session budget | Voice agent prod | Hard cap $1, soft warn $0.50, top 1% session 拦截 |
| Recall probe | Voice agent QA | Weekly 100 session abstract → fact probe, summary 质量阈值 |

### 🎤 面试现场 quotables (top 8)

> "Context management is what separates a 1-turn chatbot from a 50-turn agent. Without it, you hit lost-in-middle by turn 15 and bankruptcy by turn 50."

> "I run a 4-tier hierarchical summary: ancient 500 tok, middle 1500, recent 5000, latest verbatim. Steady-state context stays at 30K regardless of turn count."

> "Tool output > 1K goes to blob with a ref_id. Re-read same file? Reference earlier ref_id, don't re-store."

> "Lost-in-middle is real even at 2M Gemini 3 Pro — mid-position recall drops 30-40%. I put critical info at start AND end, with a decision log injected every 10 turns."

> "Prefix caching changed the economics: my 30K project context hits 70% cache rate on Anthropic 5-min cache, cutting 80% of the input cost."

> "Recall probe weekly: sample 100 sessions, ask if the summary still contains key facts. Below 80% means I retune compaction."

> "Per-session cost budget hard cap is non-negotiable — without it one session can rack up $50 silently."

> "Pinned messages are sacred — system prompt, user-stated preferences, confirmed decisions, error lessons, file mods, open TODOs. Never compact those."

### 🚨 红线 (top 10 anti-patterns)

1. Blind truncation (FIFO 砍最老 turn)
2. Single mega-summary (失结构, 不可 update)
3. All tool outputs verbatim (1KB OK, 50KB 自爆)
4. No external memory layer
5. No pinning of critical decisions
6. Ignoring lost-in-middle
7. No cost monitoring / no per-session budget
8. No recall probe (quality silent drift)
9. No prefix caching (烧钱)
10. All turns use Opus / GPT-5.5 (没 routing)

### 🛠️ Tool zoo (2026)

| 类别 | Tool | 一句话 |
|---|---|---|
| Memory libs | LangChain ConversationSummaryBufferMemory, LlamaIndex memory, MemGPT | 起步 |
| Vector DB | Qdrant, Pinecone, Weaviate | Episodic memory |
| Blob | S3, GCS, Azure Blob | Tool output > 1K |
| Structured | Postgres, Redis, DynamoDB | Decisions / state |
| Tracing | Phoenix (Arize), LangSmith, Langfuse, OpenTelemetry | Phoenix 开源 |
| Prompt cache | Anthropic 5min, Gemini context cache 1h | 90% off cached |
| Cost dashboard | OTel + Grafana / Phoenix | Per-session $ |
| LLM router | DSPy, Portkey, LiteLLM | Cost-aware routing |

### 📊 2026 pricing 速查

```
                  Input              Output
Gemini 3 Pro      $2 (≤200K)         $12 per 1M
                  $4 (>200K)
Gemini 3 Flash    $0.50              $3
Claude Opus 4.7   $5                 $25
Claude Sonnet 4.6 $3                 $15
Claude Haiku 4.5  $1                 $5
GPT-5.5           $5                 $30

Prefix cache:
  write surcharge 1.25-2x in
  hit 0.10x in
  Anthropic 5min, Gemini 1h
```

### 💻 一段最小 prod-ready compaction

```python
async def compact_if_needed(messages, model_limit):
    tok = count_tokens(messages)
    soft_cap = model_limit * 0.7
    hard_cap = model_limit * 0.9
    
    if tok < soft_cap: return messages  # lazy
    
    pinned = [m for m in messages if m.pinned]
    recent = messages[-10:]  # tier 4 verbatim
    middle = messages[-30:-10]  # tier 3 light summary
    older = messages[-50:-30]  # tier 2 medium summary
    ancient = messages[:-50]  # tier 1 heavy summary
    
    summary_ancient = await flash_summarize(ancient, max_tok=500)
    summary_older = await flash_summarize(older, max_tok=1500)
    summary_middle = await flash_summarize(middle, max_tok=5000)
    
    # Externalize big tool outputs in remaining
    recent = await externalize_big_outputs(recent, threshold=1000)
    
    return [
        *pinned,
        Msg("system", f"## Tier 1 ancient\n{summary_ancient}"),
        Msg("system", f"## Tier 2 older\n{summary_older}"),
        Msg("system", f"## Tier 3 middle\n{summary_middle}"),
        *recent,  # verbatim
        Msg("system", f"## Decision log\n{decision_log(pinned)}"),  # anti-lost-middle
    ]
```

### 🎬 45-min answer rhythm

```
0-5    Clarify: turn count / tool output sizes / multi-tenant? / cost budget?
5-10   Mental model: 50 turn doesn't scale linearly, need 5-piece engine
10-20  Compaction 4 法 + hierarchical 4-tier + selective pruning
20-30  External memory 3 层 (Blob / Vector DB / Postgres) + tool externalization
30-37  Lost-in-middle defense (placement / pinned / decision log / periodic recap)
37-42  Cost (pricing / routing / prefix cache / per-session budget) + recall probe
42-45  简历 quote (Voice agent 7 markets 20K+ tok hierarchical)
```

### 🔑 Compaction mnemonic

```
S  Sliding window         (last N verbatim)
H  Hierarchical (4-tier)  (ancient / middle / recent / latest) ⭐
P  Pruning by importance  (LLM judge score)
E  Externalize tool out   (> 1K → blob + ref)
L  Lost-in-middle defense (placement + pin + recap + decision log)
B  Budget enforcement     (per-session $ hard cap)
R  Recall probe           (weekly summary quality QA)
```
```
