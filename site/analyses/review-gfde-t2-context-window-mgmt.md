## T2.3 · context window 管理 — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](gfde-t2-context-window-mgmt.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t2-context-window-mgmt.html`](gfde-t2-context-window-mgmt.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"Agent running 50 turns, 110K/128K context — manage so it doesn't degrade"** 或 **"Coding agent context fills up — keep / summarize / drop?"**, 我按这 8 层回答, 不跳序.

### 📐 Long-running Agent Context Management — 8 层结构

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 |
|---|---|---|---|---|
| 1 | Clarify + Token economy 灾难 | 0-5 min | Turn count + tool-call/turn 频率? Single agent vs multi-agent? File reads / test output 多吗? Cost target / latency budget? **然后 demo**: 50-turn coding agent context 110K, each turn cost = current × turn count, 总 cost $6/session, latency 20s/turn → 50 turn 蹲 16 min, agent 还忘了 turn 1 user 说 FastAPI 改成 Flask | "Before designing — 50-turn agent without management is $6/session and 16 min wall clock, and the agent forgets turn 1 decisions. Token economy is non-linear; let me ground in the disaster." |
| 2 | Lost-in-middle + effective context | 5-10 min | Context window ≠ effective context. Liu et al 2023 U 形 attention — 开头结尾 recall 好, 中间衰减. 2026 Gemini 3 Pro 2M / Claude 200K / GPT-5.5 256K, 但 effective 大概是 head 20K + tail 100K. 这决定哪段必须留 verbatim | "Context window ≠ effective context. Liu's lost-in-middle paper shows U-shaped attention even in 2M-context models. This shapes the strategy." |
| 3 | 4-strategy 组合骨架 | 10-18 min | (1) **Sliding window** 最近 10 turn verbatim (2) **Hierarchical summary** turn 1-30 heavy summary / 31-40 medium / 41-50 verbatim (3) **External memory** tool output >1K token offload to blob/Postgres/vector DB + ref (4) **Selective pruning + pinning** 关键决策 (user approval / file diff / preference) 永久保留 | "4 strategies in combination — sliding window, hierarchical summary, external memory offload, selective pruning + pinning. They're additive, not alternatives." |
| 4 | 7 种 memory type | 18-25 min | Working context (current turn) / Episodic (vector DB, "你之前说过 X") / Semantic (Postgres KV, user preferences) / Procedural (system prompt, tool usage) / External docs (user upload) / Scratchpad (local file, agent 自己工作笔记) / Decision log (structured Postgres, 永不丢) | "Production long-running agent uses 4-6 memory types simultaneously. Each serves a different access pattern — let me draw the taxonomy." |
| 5 | Compaction algorithm | 25-32 min | Pre-call manager: check size > soft cap (80% context) → trigger. Step A externalize big tool outputs. Step B selective prune low-importance reasoning. Step C hierarchical summarize. Step D **reinforce critical info** (re-state user preference / decisions at end of compacted context, 防 lost-in-middle) | "Compaction is a 4-step procedure triggered at 80% soft cap. The non-obvious step is D — restating critical decisions at the end so they don't fall into the lost-in-middle zone." |
| 6 | Tool output 处理 | 32-38 min | File reads → don't inline raw content, store as `file_ref` with `read_file(path)` tool. Diff 替代 full file (改完只展示 diff). Test output 摘要 (30KB pytest → "5 passed, 2 failed: test_foo line 42, test_bar timeout"). Image/PDF → blob ref + caption | "Big tool outputs are 70% of context bloat. The pattern is offload-and-reference, diff-not-full, summary-not-raw. Let me walk through file reads, test output, and image handling." |
| 7 | Recall test methodology | 38-44 min | Compaction 不能丢关键信息. Recall test: 给 compacted context, 问 "did we agree on FastAPI?" / "what file did we modify on turn 15?" — LLM 答对率必须 > 95%. Eval set: 50 long-running session × 10 recall question each. Slice by question type (decision / preference / file state) | "Compaction without measurement is hope. I run recall tests — 'did we agree on X?' across 500 evals, slice by question type. Target > 95% answer accuracy." |
| 8 | Connect + production hardening | 44-50 min | Voice agent multi-turn (5-10 turn 通话) context with user history. ConvFinQA multi-hop reasoning (intermediate calculation steps offload to scratchpad). Internal Agent Platform memory abstraction (4 memory tiers as 1st-class API). Cost target: $0.50/session vs $6 unbounded. Pinned decisions story | "Resume hook — voice agent + Internal Agent Platform built this exact 4-tier memory. Let me share metrics and one pinning bug story." |

### 🎯 为啥按这个序

**Cost economics 灾难 (Layer 1) 必须最先讲** — "$6/session × 1M users = $6M/month" 这个数字让面试官立刻明白 stake. Lost-in-middle (Layer 2) 必须在 strategy 之前讲, 这是设计 strategy 的物理基础. 4-strategy (3) 是骨架. Memory type taxonomy (4) 区分 production vs demo — demo 只有 context, production 有 4-6 tier memory. Compaction algorithm (5) 是具体执行. Tool output (6) 单列因为它占 context 70%, 单独优化 ROI 大. **Recall test (7) 是 staff-level scientific rigor** — compaction without measurement = hope. Resume close (8) 用 $0.50 vs $6 数字最有说服力.

### 🔥 哪一层最容易被追问 deeper

- **Layer 5 (compaction)**: "Summary 用什么 model?" → 准备 Gemini 3 Flash / Claude Haiku for summarization (cheap tier, 1/10 cost of generation model). "Summary lossy 怎么办?" → 准备 hierarchical (recent verbatim + old summary), pinning critical, recall test.
- **Layer 7 (recall test)**: "Specific eval framework?" → 准备 LongBench / Needle-in-a-haystack 类 benchmark + 自定义 session replay test.
- **Layer 4 (memory type)**: "Episodic vs Semantic 区别?" → episodic 时间序列 (turn N 发生了 X), semantic 抽象事实 (用户喜欢 X). 两种 query pattern.

### ⏱ 时间压缩版 (30 min round)

- Layer 1 (clarify + cost 灾难) 4 min — 必讲
- Layer 2 (lost-in-middle) 2 min
- Layer 3 (4-strategy) 5 min — 必讲, 骨架
- Layer 4 (memory type) 跳过 / 3 min, 只讲 working / episodic / decision log 三个
- Layer 5 (compaction algo) 5 min
- Layer 6 (tool output) 4 min — 必讲, 70% bloat 来源
- Layer 7 (recall test) 3 min — 必讲, 区分 staff
- Layer 8 (connect) 2 min

### 🆘 卡壳兜底 (针对这题)

- 忘了 lost-in-middle paper 名 → 退回讲「**Liu et al 2023 paper, 长 context U 形 attention. 关键 takeaway: 中间衰减, 重要 info 放头/尾**」
- 被追问 summary 怎么避免 lossy → 退回讲「**Hierarchical (recent verbatim + old summary) + pinning critical decisions + recall test 量化**」
- 忘了 4 memory tier 完整顺序 → 退回讲「**最核心 3 个: working context (in LLM) / episodic (vector DB) / decision log (structured DB, 永不丢)**」
- 被追问 compaction trigger → 退回讲「**Soft cap 80% context, hard cap 95%. 触发 hierarchical summarize + externalize big tool outputs**」
- 被追问 cost calculation → 退回讲「**Per-turn cost = current_context_tokens × input_price + output_tokens × output_price. 50 turn 无管理 = $6, with management = $0.50, 10x 省**」

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
| **External memory** | Blob (GCS) + Vector DB (Vertex AI Vector Search) + Structured (Postgres) | 数据 > 1K 不进 context |
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
- Algorithm: Blob (GCS, tool outputs > 1K) + Vector DB (Vertex AI Vector Search, episodic search) + Postgres (decisions/prefs/state)
- Trade-off: 1 extra hop, 但 context 不爆
- Tools: GCS / GCS, Vertex AI Vector Search / Vertex AI Vector Search, Postgres / Redis / Firestore / Bigtable

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
- 3 层 store: Blob (GCS) → tool outputs / files / artifacts; Vector DB (Vertex AI Vector Search) → episodic memory, embed 老 turn; Postgres → 结构化 (decisions, preferences, session_state)
- Blob usage: store(content) → ref_id, agent tool fetch(ref_id) on demand
- Vector DB: 老 turn segment → embed → upsert with metadata (turn#, ts, type)
- Postgres schema: session_id, key, value, type (decision/pref/state), created_at
- 一致性: write-through (decision 先 Postgres 后 context); read-back probe
- Top 3 gotchas: 不 externalize 大输出 / vector DB cross-session 混 / Postgres 没 session_id 隔离
- Tools: GCS / GCS / Azure Blob, Vertex AI Vector Search / Vertex AI Vector Search, Postgres / Redis / Firestore / Bigtable

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
| External memory | BNPL multi-turn agent | Postgres (decisions) + Vertex AI Vector Search (history embed) + GCS (tool blob) |
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
| Vector DB | Vertex AI Vector Search, Vertex AI Vector Search, Weaviate | Episodic memory |
| Blob | GCS, GCS, Azure Blob | Tool output > 1K |
| Structured | Postgres, Redis, Firestore / Bigtable | Decisions / state |
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
