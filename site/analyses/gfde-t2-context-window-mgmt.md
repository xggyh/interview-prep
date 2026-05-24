## 题目

> "Your agent has been running for **50 turns** with multiple tool calls per turn. Context window is **128K tokens, now at 110K**. How do you manage so the agent doesn't degrade / break?"

或追问形态:

> "Long-running coding agent (like Cursor / Devin) — context fills up with file reads / edits / outputs. How do you decide what to **keep, summarize, drop**?"

**出处**: Google FDE T2 / Anthropic Forward Deployed / Cursor / Cognition / 任何做 long-running agent 的公司都会问.

**Round**: Context Management / Long-running Agent (45-60 min)

---

## 这道题在考什么

**Context management** 是 agent 区别于 single-turn chatbot 的关键能力:

1. **Token economy** —— context = $$$ + latency (input 越长越慢)
2. **Lost in middle** —— 长 context 模型 attention U 形, 中间 recall 弱
3. **Compression strategy** —— summary / pruning / hierarchy
4. **External memory** —— offload to DB / vector store
5. **Tool output handling** —— huge data 不进 context
6. **Cost economics** —— Gemini 3 Pro 1M token = $2-12, 不能盲乘
7. **Recall test** —— summary 后能不能回答 "did we agree on X"

考你是否真做过长跑 agent 而不是 1 turn demo. 真做过会知道 turn 15 就开始烂, turn 50 已经接近瘫.

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**Context window**: LLM 单次输入能容纳的 token 数. 2026 主流: Gemini 3 Pro 2M, Claude Opus 4.7 200K, GPT-5.5 256K, Gemini 3 Flash 1M. **不等于 effective context** — 模型在 2M 里只有最近 100K 和最早 20K 的 attention 是好的.

**Compaction (压缩)**: 把已有 messages 转成更短的表示, 保留关键信息, 丢掉冗余. 主流做法: hierarchical summary + 保留最近 N turn verbatim + 关键决策单独存.

**External memory**: 不放进 context 的内容存在外部 (Postgres / vector DB / blob store), 需要时再 fetch. 关键区别: **passive storage** (LLM 不主动找) vs **active retrieval** (agent 有 tool 主动查).

**Lost in the middle**: Liu et al. (2023) 发现长 context 模型 attention 呈 U 形 — 开头和结尾 recall 好, 中间显著衰减. 2026 即使 1M context 模型仍部分有此问题.

---

## 2. 这个问题的核心是什么

设想没有 context management 的 50-turn coding agent 灾难:

```
Turn 1:  user: "build a payment API in Python with Stripe integration, use FastAPI"
Turn 2:  agent reads pyproject.toml (2KB)
Turn 3:  agent reads README.md (5KB)
Turn 4:  agent reads app/main.py (8KB)
...
Turn 12: agent reads stripe_handler.py (15KB)
Turn 18: agent runs pytest → output 30KB (test trace)
Turn 25: agent reads webhooks/handler.py (10KB)
Turn 28: agent reads webhooks/test_handler.py (8KB)
Turn 33: agent runs full test suite → 80KB output
Turn 40: agent debugs, runs python REPL → 20KB
Turn 45: agent reads stripe_handler.py AGAIN (15KB, didn't remember)
...

Turn 50:
  Total context: 280KB raw tokens ≈ 110K tokens after dedup compression
  Lost in middle: agent 忘了 turn 1 user 说 "FastAPI"
  Cost: 50 turns × avg 60K context × $2/1M Gemini 3 Pro = $6 per session
  Latency: 110K input × Gemini 3 Pro first-token ~20s per turn
```

**问题**:

- **Token cost 指数增长**: each turn cost = current context × turn count
- **Lost-in-middle**: turn 1 的 user 要求 (FastAPI) 埋在中间, agent 改成 Flask 了
- **Tool output 重复**: agent reads same file twice 因为忘了
- **Long latency**: 每 turn 20s, 50 turn 蹲 16 分钟
- **Agent 越来越笨**: context 长 → attention 稀, 出错率升

**好 context management 的解法**:

```
4 个 strategy 组合:
  1. Sliding window: 最近 10 turn verbatim
  2. Hierarchical summary: turn 1-30 (heavy summary) / 31-40 (med) / 41-50 (verbatim)
  3. External memory: tool output > 1K token 外置, 留 reference
  4. Selective pruning: 重要决策 / 文件改动 / 用户 preference 标记永久保留

成果:
  Context steady at 30K throughout, regardless of turn count
  Cost per session: $0.50 instead of $6
  Latency p99 8s per turn instead of 20s
  Agent remembers turn 1 decision because pinned
```

---

## 3. 典型流程图

```
┌─────────────────────────────────────────────────────────────────┐
│              Agent Loop with Context Management                  │
└─────────────────────────────────────────────────────────────────┘

  User input
    │
    ▼
  ┌────────────────────────┐
  │  Pre-call context      │
  │  manager:              │
  │  1. Check size         │
  │  2. If > soft cap →    │
  │     compact            │
  └────────┬───────────────┘
           │
           ▼
  ┌────────────────────────────────────────────────┐
  │                 Compaction                       │
  │                                                  │
  │  Step A: Externalize big tool outputs            │
  │    tool_output > 1K token → blob store + ref     │
  │                                                  │
  │  Step B: Selective prune                         │
  │    Drop low-importance intermediate reasoning    │
  │    Keep pinned (decisions / preferences)         │
  │                                                  │
  │  Step C: Hierarchical summarize                  │
  │    Oldest turns → heavy summary                  │
  │    Middle → medium summary                       │
  │    Recent 10 → verbatim                          │
  │                                                  │
  │  Step D: Reinforce critical info                 │
  │    Re-state user preference / decisions at end   │
  └────────┬───────────────────────────────────────┘
           │
           ▼
  ┌────────────────────────┐
  │  LLM call              │
  │  (Gemini 3 Pro / Flash)│
  └────────┬───────────────┘
           │
           ▼
  Tool calls / response
           │
           ▼
  ┌────────────────────────┐
  │  Post-call:            │
  │  - Tag importance      │
  │  - Update external mem │
  │  - Log token count     │
  │  - Cost tracking       │
  └────────────────────────┘

External components:
  ├── Blob store (S3): full tool outputs
  ├── Vector DB (Qdrant): semantic memory of old turns
  ├── Structured memory (Postgres): facts, preferences, decisions
  └── File system: working files agent reads/writes
```

---

## 4. 关键 memory 类型分类表

| Memory type | 存哪 | 何时用 | 例 |
|---|---|---|---|
| **Working context** | LLM context window | 当前 turn 需要的所有信息 | Recent 10 turns + summary + system prompt |
| **Episodic memory** | Vector DB | "你之前说过 X" 类查询 | 旧 turn 摘要, embed 后 search |
| **Semantic memory** | Postgres / KV | 用户 preferences / facts | "用户喜欢 dark mode" / "项目用 FastAPI" |
| **Procedural memory** | LLM weights + system prompt | How to use tools | Tool 使用说明, examples |
| **External docs** | Vector DB / S3 | User-uploaded reference material | 用户上传的 PDF |
| **Scratchpad** | Local file / blob | Agent 自己的工作笔记 | research_notes.md |
| **Decision log** | Structured Postgres | 永远不能丢的决策 | "user approved spec on turn 12" |

production 的 long-running agent **必同时用 4-6 种**, 各司其职.

---

## 5. 具体业务场景 (5 个高频)

### 场景 A: Coding agent (你 BNPL 工作的 voice agent 类比)

Cursor / Devin / Claude Code 长跑 50+ turn:
- 读多个文件 (10-100 个)
- 跑测试 / lint output 巨大
- 反复编辑同一文件
- 用户中途 inject 新需求

**重点**:
- **File 内容**: 不 inline, 用 `read_file` tool 按需 load
- **Diff 替代 full file**: 改完只展示 diff
- **Test output 摘要**: 30KB pytest output → "5 passed, 2 failed: test_foo (assertion error line 42), test_bar (timeout)"
- **TODO list**: 不靠 LLM 记, 显式 todo file

### 场景 B: 客服 support agent 接历史 ticket

用户来咨询, agent 接手 50 个历史 ticket:
- 全 inline 爆 context
- 但需要 cross-ticket 模式 ("这 user 反复抱怨 billing")

**重点**:
- **Per-ticket gist**: cheap LLM summarize each → 50 × 100 tokens = 5K
- **Hot context**: 最近 5 ticket full
- **On-demand fetch**: `get_ticket_full(id)` 工具
- **Pattern aggregation**: "user_profile.frequent_complaint = 'billing'" 显式 surfacing

### 场景 C: Research / browsing agent (deep research)

Agent 浏览 100 个 web page 做研究:
- Raw HTML 完全没用 (噪声多)
- 但 citation 不能丢

**重点**:
- **Web page → notes**: 每访问 1 页, LLM 抽 key findings (500 tok)
- **Discard raw page** 立即 drop
- **Notes 累积** + 阶段性 compress notes
- **Citation 保留**: URL + 引用 quote
- **Working memory file**: research_notes.md 持久化

### 场景 D: Legal agent — 500-page 合同 + 多 turn Q&A

律师问 50 个 question on 同一合同:
- 一次性 load → long-context, 但贵
- Per-question 重 load → 浪费

**重点**:
- **Hybrid**: load 一次 (prefix caching), 后续 RAG 取相关 clause
- **Question router**: 'overview' 类 → long context; 'specific clause' → RAG
- **Prefix cache** (Anthropic / Gemini 都支持): 合同 prefix 5min cache, 同 session 复用

### 场景 E: Real-time dashboard / monitoring agent

Agent 监控 metric, 每 30s data update:
- 旧 data 立刻过时
- Anomaly 需保留

**重点**:
- **Drop stale aggressively**: 30s 前 data drop
- **Per-turn delta only**: 不重发全状态
- **Aggregation 替代 raw**: "last hour: p99 250ms, p50 80ms" 替代 10K data point
- **Anomaly memory**: 仅 retain 异常事件 + 5-min 后冷静期

---

## 6. 工程上要做什么 (实现 checklist)

**离线设计**:

1. **设定 soft cap / hard cap**: e.g., model_limit = 128K, soft = 70% = 90K, hard = 90% = 115K
2. **设计 message tagging**: 每 message 加 metadata `{type, importance, source, ts, pinned}`
3. **设计 external memory schema**: 哪些进 vector DB, 哪些进 KV, 哪些进 S3
4. **设计 tool 列表**: `read_file`, `get_full_tool_output`, `recall_past`, `write_note` 等

**在线运行时**:

5. **Pre-call check**: `est_tokens(messages) > soft_cap` → trigger compact
6. **Compaction pipeline** (4 步, 见上图)
7. **Tool output handler**: > 1K token 自动 externalize
8. **Post-call tagging**: LLM 自标 importance (or heuristic)

**Observability**:

9. **Per-turn metrics**: input_tokens, output_tokens, cost, compaction_event_yes_no
10. **Cumulative**: session_cost, session_turns, compaction_count
11. **Recall test**: 周期性 probe "do you remember turn 1 instruction" → 失败上报
12. **Cost alert**: session > $5 → alert
13. **Trajectory tracing** (Phoenix / LangSmith): 每 turn input/output 可回放

**Tuning**:

14. **Summary template**: 'Decisions / Files modified / Open TODOs / User preferences' structured
15. **Summary model**: 用 Gemini 3 Flash ($0.50/$3) 而不是 Pro
16. **Eval set**: 几个长跑场景, 比较不同 compaction policy
17. **A/B** new compaction strategy vs old

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **Truncate oldest blindly** | 丢 system prompt / 第 1 turn 关键决策 |
| 2 | **Single mega-summary** | "前 50 turn 摘要" 失细节, agent 忘细节 |
| 3 | **Keep all tool outputs verbatim** | 10MB pytest output 直接爆 |
| 4 | **没 external memory** | 一切塞 context, 注定爆 |
| 5 | **No pinning** | summarizer 把 "user said yes to X" 压没了 |
| 6 | **Ignore lost-in-middle** | 关键 info 埋在中间 attention 弱 |
| 7 | **No cost monitoring** | Session 花 $20 老板才发现 |
| 8 | **Summary 用 flagship LLM** | 浪费, Flash 足够好 |
| 9 | **每 turn 全量 compact** | Compact 本身就贵, 应该 threshold trigger |
| 10 | **No recall test** | Summary 静默坏掉, agent 忘东忘西无 metric |
| 11 | **Block on compaction** | User 等 5s 才回应, 应 async |
| 12 | **External memory 不归一** | Vector DB / Postgres / S3 状态不一致 |

---

## 一句话总结 (Part 1)

> **Context management = 「Sliding window 最近 + Hierarchical summary 中间 + External memory 大数据 + Selective pruning 不重要 + Pinning 关键决策 + Lost-in-middle 觉知」 6 件套**.
>
> Long-running agent 的稳定性 = context size 不随 turn 数线性增长.

---

# Part 2 · 5 个深度工程问题

## ⚙️ Problem 1: Compaction Strategies — Sliding / Summarize / Hierarchical

### 1.1 Sliding window (baseline)

```python
def sliding_window(messages, keep_last_n=10):
    """最简单: 保留最近 N turn, 丢老的"""
    return messages[-keep_last_n:]
```

**问题**:
- 丢 turn 1 user 要求 ("用 FastAPI") → agent 改成 Flask
- 丢 mid-session 关键决策 ("user approved API spec turn 12")
- 适合**完全 stateless** 场景, 不适合 stateful agent

### 1.2 Summarize old + keep recent

```python
def summarize_and_keep(messages, recent_n=10, summary_model='gemini-3-flash'):
    if len(messages) <= recent_n:
        return messages

    to_summarize = messages[:-recent_n]
    recent = messages[-recent_n:]

    summary_prompt = """Summarize the following conversation history.
Preserve:
  - Decisions made (e.g., "agreed to use FastAPI", "user said yes to schema")
  - Files modified (path + brief change description)
  - User preferences and constraints
  - Open TODOs
  - Errors encountered and how they were handled
Compress:
  - Full tool outputs (replace with "ran X, got Y outcome")
  - Intermediate reasoning
  - Repeated information

Conversation:
{history}

Summary:"""

    summary = llm.generate(
        prompt=summary_prompt.format(history=format_messages(to_summarize)),
        model=summary_model,
        max_tokens=2000,
    )

    return [
        Message(role='system', content=f'[Conversation summary so far]\n\n{summary}\n\n[End summary]'),
        *recent,
    ]
```

**Trade-off**:
- ✓ 大幅压缩 (20K → 2K typical)
- ✗ Single summary 失细节
- ✗ Re-summarize 多次会 drift (信息逐渐磨损)

### 1.3 Hierarchical summary (推荐)

```python
class HierarchicalCompactor:
    """
    分层 summary:
      tier 1: 最老 turn 1-30 → heavy compress (200 tok)
      tier 2: turn 31-40 → medium (500 tok)
      tier 3: turn 41-50 → light or verbatim
      tier 4: turn 51-60 (recent) → verbatim

    每次 compaction trigger, 把 tier 4 → tier 3, tier 3 → tier 2, tier 2 → tier 1 (re-summarize)
    """

    def __init__(self, model='gemini-3-flash'):
        self.tiers = {1: [], 2: [], 3: [], 4: []}  # tier_id → messages
        self.tier_max_tokens = {1: 500, 2: 1500, 3: 5000, 4: 10000}
        self.summary_model = model

    def add_turn(self, msg):
        self.tiers[4].append(msg)
        if self._tier_size(4) > self.tier_max_tokens[4]:
            self._cascade_down()

    def _cascade_down(self):
        """Move oldest tier-4 turns into tier-3, summarize when needed"""
        # tier 4 满了 → 移动 oldest 部分到 tier 3
        overflow = []
        while self._tier_size(4) > self.tier_max_tokens[4] * 0.8:
            overflow.append(self.tiers[4].pop(0))

        if overflow:
            # tier 3 incoming: summarize overflow lightly
            light_summary = self._summarize(overflow, target_tokens=500)
            self.tiers[3].append(light_summary)

        # 递归 cascade
        if self._tier_size(3) > self.tier_max_tokens[3]:
            old_t3 = self.tiers[3][:len(self.tiers[3])//2]
            self.tiers[3] = self.tiers[3][len(self.tiers[3])//2:]
            medium_summary = self._summarize(old_t3, target_tokens=1500, level='medium')
            self.tiers[2].append(medium_summary)

        if self._tier_size(2) > self.tier_max_tokens[2]:
            old_t2 = self.tiers[2][:len(self.tiers[2])//2]
            self.tiers[2] = self.tiers[2][len(self.tiers[2])//2:]
            heavy_summary = self._summarize(old_t2, target_tokens=500, level='heavy')
            self.tiers[1].append(heavy_summary)

    def build_context(self):
        """构造最终给 LLM 的 context"""
        tier1_concat = '\n\n'.join(m.content for m in self.tiers[1])
        tier2_concat = '\n\n'.join(m.content for m in self.tiers[2])
        tier3_concat = '\n\n'.join(m.content for m in self.tiers[3])

        return [
            Message(role='system', content=(
                '## Ancient history (turns long ago, heavily compressed)\n\n' + tier1_concat
            )),
            Message(role='system', content=(
                '## Recent past (medium-compressed)\n\n' + tier2_concat
            )),
            Message(role='system', content=(
                '## Last few turns (light summary)\n\n' + tier3_concat
            )),
            *self.tiers[4],  # verbatim recent
        ]
```

**为什么 hierarchical 优于 flat**:
- **No re-summarize drift**: tier 1 信息只 summarize 一次, 不会反复磨
- **Granular control**: 可调每 tier 大小, 不同场景不同 budget
- **Cost economy**: 大部分 compaction 操作只动 tier 4 → tier 3 (低成本), 偶尔 cascade 才贵

### 1.4 Selective pruning by importance

```python
def importance_score(msg) -> float:
    """启发式打分"""
    score = 0.0

    # Type-based
    if msg.role == 'user':
        score += 2.0  # 用户输入永远重要
    if msg.role == 'system':
        score += 3.0  # 必保

    # Content-based
    if any(kw in msg.content.lower() for kw in
           ['decided', 'approved', 'agreed', 'rejected', 'changed', 'preference']):
        score += 2.0
    if 'error' in msg.content.lower() or 'failed' in msg.content.lower():
        score += 1.5

    # Length penalty (大 message 倾向 drop or summarize)
    if msg.tokens > 2000:
        score -= 1.0

    # Recency bonus
    age_turns = current_turn - msg.turn
    score += max(0, 5 - age_turns) * 0.5

    # Pin override
    if msg.metadata.get('pinned'):
        score = float('inf')

    return score

def prune_low_importance(messages, target_token_count):
    scored = [(m, importance_score(m)) for m in messages]
    scored.sort(key=lambda x: -x[1])

    kept, total = [], 0
    for msg, score in scored:
        if total + msg.tokens > target_token_count:
            continue
        kept.append(msg)
        total += msg.tokens

    # Restore original order
    kept.sort(key=lambda m: m.turn)
    return kept
```

### 1.5 整合 compaction pipeline

```python
def manage_context(
    messages,
    model_limit=128_000,
    target_util=0.7,
    config=CompactionConfig(),
):
    current = est_tokens(messages)
    if current < model_limit * target_util:
        return messages  # no action

    # Step 1: Externalize big tool outputs (-30% typical)
    messages = externalize_large_outputs(messages, threshold=1000)

    # Step 2: Selective prune low-importance intermediate
    if est_tokens(messages) > model_limit * target_util:
        messages = prune_low_importance(messages, target_token_count=int(model_limit * 0.5))

    # Step 3: Hierarchical summarize
    if est_tokens(messages) > model_limit * target_util:
        compactor = HierarchicalCompactor()
        for m in messages:
            compactor.add_turn(m)
        messages = compactor.build_context()

    # Step 4: Reinforce critical info (lost-in-middle defense)
    messages = append_decision_recap(messages)

    return messages
```

每一步 stop-condition 是「token 数足够小」, 不必每次跑全部.

---

## ⚙️ Problem 2: External Memory Architecture — Blob + Vector DB + Structured

### 2.1 三层 external memory

```
┌─────────────────────────────────────────────────────────┐
│                  Blob store (S3 / GCS)                   │
│    - Full tool outputs (>1K tokens)                      │
│    - Uploaded files (PDFs, CSVs)                         │
│    - Long agent-generated artifacts                      │
│    - Key by content hash, immutable, cheap               │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              Vector DB (Qdrant / Pinecone)               │
│    - Episodic memory: old turn summaries indexed         │
│    - User-uploaded doc chunks                            │
│    - Project knowledge (Confluence / Slack archive)      │
│    - Searchable by semantic similarity                   │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│        Structured memory (Postgres / KV)                 │
│    - User preferences ('user_prefers_FastAPI': true)    │
│    - Decision log (turn, decision_text, ts)              │
│    - Session state (current_file, current_task)          │
│    - Strongly typed, key-value lookup                    │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Blob store usage

```python
class BlobMemory:
    def __init__(self, bucket='agent-blobs'):
        self.s3 = boto3.client('s3')
        self.bucket = bucket

    def put(self, content: str, ttl_hours=24) -> str:
        """存 large output, 返回引用 ID"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        key = f'blob/{content_hash}.txt'
        self.s3.put_object(
            Bucket=self.bucket, Key=key, Body=content,
            Metadata={'ttl_until': str(int(time.time()) + ttl_hours * 3600)},
        )
        return content_hash

    def get(self, ref_id: str) -> str:
        key = f'blob/{ref_id}.txt'
        resp = self.s3.get_object(Bucket=self.bucket, Key=key)
        return resp['Body'].read().decode()

# Tool wrapper
def execute_tool_with_externalization(tool_name, args, blob_mem):
    result = call_tool(tool_name, args)
    if len(result) > 1000 * 4:  # > ~1K tokens
        ref = blob_mem.put(result)
        summary = summarize(result, max_tokens=200)
        return {
            'role': 'tool',
            'content': f'<tool_output tool="{tool_name}" ref="{ref}">\n{summary}\n</tool_output>',
            '_full_ref': ref,
        }
    return {'role': 'tool', 'content': result}
```

Agent 用 `get_full_tool_output(ref_id)` 拿全文 — 自助按需 fetch.

### 2.3 Vector DB for episodic memory

```python
class EpisodicMemory:
    def __init__(self):
        self.qdrant = QdrantClient()
        self.qdrant.create_collection(
            collection_name='agent_memory',
            vectors_config={'size': 768, 'distance': 'Cosine'},
        )

    def archive(self, turn: int, content: str, metadata: dict):
        """旧 turn 归档"""
        vec = embed(content)
        self.qdrant.upsert(
            collection_name='agent_memory',
            points=[{
                'id': f'turn_{turn}',
                'vector': vec,
                'payload': {'turn': turn, 'content': content, **metadata},
            }],
        )

    def recall(self, query: str, top_k=5) -> List[Memory]:
        """Agent 主动 search 过去"""
        q_vec = embed(query)
        hits = self.qdrant.search(
            collection_name='agent_memory',
            query_vector=q_vec, limit=top_k,
        )
        return [h.payload for h in hits]

# Agent tool
def recall_past_memory(query: str):
    """Agent 调用: 'did we talk about Stripe webhook earlier?'"""
    memories = episodic_mem.recall(query, top_k=5)
    return format_for_llm(memories)
```

**注意**: 不是每 turn 都 dump 进 vector DB. 通常 compaction 时 tier 2/3 摘要进 vector DB 索引 (信息密度更高).

### 2.4 Structured memory (Postgres)

```sql
CREATE TABLE session_memory (
    session_id UUID,
    key TEXT,
    value JSONB,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (session_id, key)
);

CREATE TABLE decisions (
    session_id UUID,
    decision_id SERIAL,
    turn INT,
    decision_text TEXT,
    rationale TEXT,
    made_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (session_id, decision_id)
);

CREATE TABLE user_preferences (
    user_id UUID,
    pref_key TEXT,
    pref_value TEXT,
    source_turn INT,
    PRIMARY KEY (user_id, pref_key)
);
```

**用法**:

```python
# Agent 检测到决策 → 显式记录
def record_decision(session_id, turn, decision: str, rationale: str):
    db.execute("INSERT INTO decisions ... VALUES (?, ?, ?, ?)",
               session_id, turn, decision, rationale)

# Agent 检测到 user preference → 持久化
def record_preference(user_id, key: str, value: str, source_turn: int):
    db.execute("""INSERT INTO user_preferences VALUES (?, ?, ?, ?)
                  ON CONFLICT (user_id, pref_key) DO UPDATE SET ...""", ...)

# 构造 context 时, 显式注入
def build_system_prompt(session_id, user_id):
    prefs = db.query("SELECT pref_key, pref_value FROM user_preferences WHERE user_id = ?", user_id)
    decisions = db.query("SELECT decision_text FROM decisions WHERE session_id = ? ORDER BY turn", session_id)
    return f"""You are an agent. User preferences:
{format_prefs(prefs)}

Decisions made this session (must respect):
{format_decisions(decisions)}
"""
```

**这是 lost-in-middle 的最强解药** — 决策不靠 LLM 记, 强制注入 system prompt 末尾.

### 2.5 Memory consistency

三个 store 不一致是经典坑:

```python
class MemoryWrite:
    def __init__(self, session_id):
        self.session_id = session_id
        self.pending = []  # 收集 changes

    def record(self, store: str, op: str, **kwargs):
        self.pending.append((store, op, kwargs))

    def commit(self):
        """All-or-nothing 写三 store"""
        with db.transaction():
            for store, op, kwargs in self.pending:
                if store == 'blob':
                    ref = blob_mem.put(**kwargs)
                    db.execute("INSERT INTO blob_refs ...", ref)
                elif store == 'vector':
                    qdrant.upsert(**kwargs)
                elif store == 'postgres':
                    db.execute(op, **kwargs)
            # 全成功才 commit, postgres tx 保证原子性
```

实际 production 里 vector DB 和 blob store 不在 RDBMS tx 里, 用**最终一致** + cleanup job 处理 orphan.

---

## ⚙️ Problem 3: Tool Output Externalization — > 1K Token 拿走

### 3.1 阈值与策略

```python
class ToolOutputRouter:
    INLINE_LIMIT = 1000          # tokens, 直接 inline
    SUMMARIZE_LIMIT = 5000       # 1K-5K, summarize + reference
    BLOB_ONLY_LIMIT = 50000      # 5K-50K, summarize 极简 + blob
    REJECT_LIMIT = 50000         # > 50K, reject 或 force pagination

    def route(self, tool_name, output):
        tokens = est_tokens(output)
        if tokens <= self.INLINE_LIMIT:
            return self._inline(output)
        elif tokens <= self.SUMMARIZE_LIMIT:
            return self._summarize_and_blob(tool_name, output, summary_len=300)
        elif tokens <= self.BLOB_ONLY_LIMIT:
            return self._summarize_and_blob(tool_name, output, summary_len=100)
        else:
            return self._reject_or_paginate(tool_name, output)

    def _inline(self, output):
        return output

    def _summarize_and_blob(self, tool_name, output, summary_len):
        ref = blob_mem.put(output)
        summary = llm.summarize(output, max_tokens=summary_len, model='gemini-3-flash')
        return f'''<tool_output tool="{tool_name}" ref="{ref}" full_tokens="{est_tokens(output)}">
{summary}

(Full output stored at ref {ref}. Use get_full_tool_output("{ref}") to retrieve.)
</tool_output>'''

    def _reject_or_paginate(self, tool_name, output):
        # 50KB+ 必须 force agent 用 query refinement
        return f'''<tool_output tool="{tool_name}" status="too_large" tokens="{est_tokens(output)}">
Output too large ({est_tokens(output)} tokens). Refine your query:
- Add filters / WHERE clause
- Request specific column / page range
- Use a different tool that returns aggregates
</tool_output>'''
```

### 3.2 Smart summary by tool type

不同 tool output 有不同 schema, 不同 summary 模板:

```python
SUMMARIZE_TEMPLATES = {
    'execute_sql': """The query returned {row_count} rows with columns {columns}.
Sample first 3 rows:
{sample}
Aggregate stats:
{stats}
""",
    'read_file': """File {path} ({line_count} lines, {byte_count} bytes).
First 20 lines:
{head}
Outline (classes/functions):
{outline}
""",
    'web_search': """{result_count} search results. Top 5 by relevance:
{top_snippets}
""",
    'pytest_run': """{passed}/{total} tests passed, {failed} failed, {skipped} skipped.
Failures:
{failure_summary}
Duration: {duration}s
""",
}
```

预定义 schema 比 LLM free-form summarize 更可靠. 出 schema-conforming summary 给 LLM, 易解析.

### 3.3 Provenance / reference resolution

Agent 想看全文:

```python
# Tool definition exposed to agent
{
    "name": "get_full_tool_output",
    "description": "Retrieve the full content of a previously executed tool call by its reference ID. Use when summary is insufficient.",
    "parameters": {
        "ref_id": {"type": "string", "description": "Reference ID from a previous tool_output tag"}
    }
}

def get_full_tool_output(ref_id):
    try:
        full = blob_mem.get(ref_id)
        if est_tokens(full) > 20000:
            return f"Full content is {est_tokens(full)} tokens (too large to return inline). Consider using a different filter approach."
        return full
    except KeyError:
        return f"Ref {ref_id} expired or not found."
```

Agent 实战 trace:

```
Turn 5: agent: execute_sql("SELECT * FROM orders WHERE Q4")
        tool: <tool_output ref="abc123">10K rows, aggregates: total $500K, top: ...
              get_full_tool_output("abc123") for details</tool_output>
        agent: I see total Q4 spend. User asked top-5 customers.

Turn 6: agent: get_full_tool_output("abc123")
        tool: (full 10K rows)
        agent: sees full → identifies top-5

Better:
Turn 6: agent: execute_sql("SELECT customer_id, name, SUM(amount) FROM orders
                            WHERE Q4 GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 5")
        tool: (small precise result)
        agent: 高效得出 top-5
```

第二种更省 token, 但 LLM 不一定每次都 refine, 所以两条路都得有.

### 3.4 Avoid duplication

```python
class DedupCache:
    """同一 tool + 同 args 短时间内不重复执行"""
    def __init__(self, ttl=300):
        self.cache = {}
        self.ttl = ttl

    def get(self, tool, args):
        key = (tool, json.dumps(args, sort_keys=True))
        entry = self.cache.get(key)
        if entry and time.time() - entry['ts'] < self.ttl:
            return entry['result']
        return None

    def set(self, tool, args, result):
        key = (tool, json.dumps(args, sort_keys=True))
        self.cache[key] = {'result': result, 'ts': time.time()}

# Agent loop
def call_tool_cached(tool, args):
    cached = dedup.get(tool, args)
    if cached:
        return f"<cached_result note='Same as {ref_id} from earlier'>\n{cached}\n</cached_result>"
    result = actual_call_tool(tool, args)
    dedup.set(tool, args, result)
    return result
```

避免 turn 45 重读同一文件这种事.

---

## ⚙️ Problem 4: Lost-in-the-Middle Mitigation — Placement + Reinforcement

### 4.1 Lost-in-middle 是什么

Liu et al. (2023) 实验: 把 ground-truth 信息埋在不同位置, 测模型 recall.

```
信息位置:    开头  四分之一  中间  四分之三  结尾
Claude 3:    95%   78%      52%   76%      94%
GPT-4:       92%   71%      48%   72%      91%
Gemini 1.5:  93%   75%      55%   77%      92%
```

明显 U 形, 中间最低. **2026 即使 1M context model 仍有 30-40% gap 中间 vs 端点**.

### 4.2 Placement strategy

```python
def build_context_with_placement(messages, system_prompt, key_facts):
    """构造 LLM context, 把关键 info 放头尾"""

    # 头: system prompt + 最关键 fact
    head = [
        Message(role='system', content=system_prompt),
        Message(role='system', content=(
            '## Critical context (MUST follow)\n\n' +
            format_key_facts(key_facts['critical'])
        )),
    ]

    # 中: 历史 / summary (low attention 区, 放 less critical)
    middle = build_summarized_history(messages, key_facts['historical'])

    # 尾: 最近 turns + 当前 task + recap
    tail = [
        *messages[-5:],  # 最近 verbatim
        Message(role='system', content=(
            '## Recap of decisions / preferences\n\n' +
            format_key_facts(key_facts['decisions'])  # ← 关键 info 再写一遍
        )),
    ]

    return head + middle + tail
```

### 4.3 Periodic reinforcement

每 N turn 自动注入一段 recap:

```python
def maybe_inject_recap(messages, current_turn, last_recap_turn, key_facts):
    if current_turn - last_recap_turn >= 10:
        recap_msg = Message(role='system', content=f"""
## Reminder (turn {current_turn})

Key decisions so far:
{format_key_facts(key_facts['decisions'])}

User preferences (must follow):
{format_key_facts(key_facts['preferences'])}

Open todos:
{format_key_facts(key_facts['todos'])}
""")
        messages.append(recap_msg)
        return current_turn  # update last_recap_turn
    return last_recap_turn
```

### 4.4 Decision log (anti-lost-in-middle)

```python
class DecisionLog:
    """关键决策永远不进 summary, 永远在 system prompt"""
    def __init__(self, session_id):
        self.session_id = session_id
        self.decisions = []

    def record(self, decision: str, rationale: str = None):
        self.decisions.append({
            'turn': current_turn(),
            'decision': decision,
            'rationale': rationale,
            'ts': now(),
        })
        # 同时持久化到 Postgres
        db.execute("INSERT INTO decisions ...", ...)

    def render_for_prompt(self):
        if not self.decisions:
            return ''
        return '## Decisions (binding, must follow)\n\n' + '\n'.join(
            f"- Turn {d['turn']}: {d['decision']}" + (f" (because {d['rationale']})" if d['rationale'] else '')
            for d in self.decisions
        )

# Inject 进 system prompt 每个 turn
def build_system_prompt(session, decision_log):
    base = "You are an agent..."
    return base + '\n\n' + decision_log.render_for_prompt()
```

LLM 自标 decision:

```python
# 加入 LLM 输出 schema
{
    "thought": "...",
    "action": {"tool": "...", "args": {...}},
    "decision_made": {  # optional, when LLM decides something
        "decision": "Use FastAPI for the web framework",
        "rationale": "User confirmed FastAPI in turn 3",
    } or None,
}

# Agent loop parser
if response.get('decision_made'):
    decision_log.record(**response['decision_made'])
```

### 4.5 Pinned messages

User 可以 pin / agent 自动 pin:

```python
class Message:
    role: str
    content: str
    pinned: bool = False
    pin_reason: str = None
    ...

# Compaction 跳过 pinned
def compact(messages):
    pinned = [m for m in messages if m.pinned]
    unpinned = [m for m in messages if not m.pinned]
    compressed_unpinned = compress_strategy(unpinned)
    return pinned + compressed_unpinned

# User 显式 pin
@app.post('/pin')
def pin_message(message_id):
    db.execute("UPDATE messages SET pinned = TRUE WHERE id = ?", message_id)

# Agent 自动 pin 类型
AUTO_PIN_PATTERNS = [
    r'(decided|agreed|approved|use)',  # 决策类
    r'(prefer|like|want|need)',         # 偏好
    r'I should remember',
]
def should_auto_pin(msg) -> bool:
    return any(re.search(p, msg.content, re.IGNORECASE) for p in AUTO_PIN_PATTERNS)
```

### 4.6 Recall probe (验 summary 质量)

每 N turn 测一次:

```python
def recall_probe(messages, key_facts):
    """从已 compact 的 messages 中随机抽 fact 测 LLM 能否记起"""
    fact = random.choice(key_facts)
    probe_msg = Message(role='system', content=(
        f'Internal check: what is the user preference for {fact["key"]}? '
        f'Answer in 1 short sentence or "I do not know".'
    ))
    response = llm.generate(messages + [probe_msg], max_tokens=50)

    if fact['expected_answer'].lower() in response.lower():
        metrics.incr('recall_probe.pass')
    else:
        metrics.incr('recall_probe.fail')
        alert('Summary degraded — recall probe failed', detail={'fact': fact, 'response': response})
```

Probe failure → summarizer 出问题, 需调.

---

## ⚙️ Problem 5: Cost Economics + Per-session Budget

### 5.1 2026 模型定价

| Model | Input / 1M | Output / 1M | Effective context | Best for |
|---|---|---|---|---|
| **Gemini 3 Pro** | $2 (≤200K), $4 (>200K) | $12 | 2M | Flagship agent, complex reasoning |
| **Gemini 3 Flash** | $0.50 | $3 | 1M | Compaction summary, cheap iterations |
| **Claude Opus 4.7** | $5 | $25 | 200K | Highest quality reasoning |
| **Claude Sonnet 4.6** | $3 | $15 | 200K | Balanced flagship |
| **Claude Haiku 4.5** | $1 | $5 | 200K | Tool routing, cheap pass |
| **GPT-5.5** | $5 | $30 | 256K | Reasoning-heavy |

**Google FDE 默认用 Gemini 3 Pro / Flash 量化**.

### 5.2 Cost 公式

```
per_turn_cost = (input_tokens × input_price + output_tokens × output_price) / 1M

session_cost = Σ per_turn_cost over all turns
```

**关键洞察**: input_tokens 每 turn 包括前面所有 messages. 如果不 compact:

```
Turn 1: input 1K → cost 1K × $2/1M = $0.002
Turn 2: input 2K → cost 2K × $2/1M = $0.004
Turn 3: input 3K → cost 3K × $2/1M = $0.006
...
Turn 50: input 50K → cost 50K × $2/1M = $0.10
Total: ~$3 per session (quadratic-ish)

如果 turn 50 时 context 已 110K:
  per turn ≈ $0.22, session total $6+

Compact 后 steady 30K:
  per turn $0.06, session total $3
```

### 5.3 Routing strategy (cost-aware)

```python
class CostAwareRouter:
    """根据任务复杂度选 model"""

    def route(self, task_type: str, complexity: str, latency_target: float):
        # Compaction / summary: 用 Flash
        if task_type == 'summarize':
            return 'gemini-3-flash'

        # Tool calling / routing: Haiku 够
        if task_type == 'tool_decision':
            return 'claude-haiku-4.5'

        # 复杂推理: Pro 或 Opus
        if complexity == 'high':
            return 'gemini-3-pro' if latency_target < 5 else 'claude-opus-4.7'

        # 默认: Sonnet 平衡
        return 'claude-sonnet-4.6'

# 用法
summarizer = router.route('summarize', 'low', 10.0)        # → flash
main_loop = router.route('reasoning', 'high', 5.0)         # → Gemini 3 Pro
```

### 5.4 Prefix caching (大节省)

Gemini / Anthropic 都支持 prompt caching:

```python
# Anthropic 例
response = anthropic.messages.create(
    model='claude-opus-4.7',
    system=[{
        'type': 'text',
        'text': long_system_prompt + project_context,  # 50K tokens
        'cache_control': {'type': 'ephemeral'}  # cache 5 min
    }],
    messages=conversation,
)
# 第 2-N 次 call 同 prefix 内: cached input cost ~10% normal price
```

**收益**: 多 turn 同 session, 50K prefix 第 1 次 full price, 之后 90% off.

```
Turn 1: input 60K (50K cached prefix + 10K conv) = $0.30
Turn 2: input 65K (50K cache hit + 15K) = $0.030 (大省!)
Turn 10: ~$0.10/turn instead of $0.13
```

### 5.5 Per-session budget enforcement

```python
class SessionBudget:
    def __init__(self, max_dollars: float = 5.0):
        self.max = max_dollars
        self.spent = 0.0
        self.alerts_sent = set()

    def can_spend(self, projected: float) -> bool:
        return self.spent + projected <= self.max

    def record(self, cost: float):
        self.spent += cost
        # 阶段性 alert
        for pct in [0.5, 0.8, 0.95]:
            if self.spent >= self.max * pct and pct not in self.alerts_sent:
                alert(f'Session budget {pct*100}% reached: ${self.spent:.2f}')
                self.alerts_sent.add(pct)

# Agent loop
def agent_step(messages, budget: SessionBudget):
    projected = estimate_cost(messages, model)
    if not budget.can_spend(projected):
        return Message(role='system', content=(
            'Session budget reached. Pausing. Ask user to confirm continuation.'
        ))

    response = llm.call(messages, model)
    actual = compute_cost(response.usage, model)
    budget.record(actual)
    return response
```

### 5.6 Cost-quality trade-off

| Setting | Strategy | Per-session cost (typical 30-turn) | Quality |
|---|---|---|---|
| **No compaction** | 全 verbatim, Gemini 3 Pro | $3-6 | Degrades at turn 20+ |
| **Sliding window only** | 保留 10 turn, Pro | $0.50 | Loses early context |
| **Hierarchical + Flash summary** | 4 tier, Flash summarize | $0.40 (Pro) + $0.05 (Flash) = $0.45 | Best |
| **+ Prefix caching** | 同 + 5 min cache | $0.20 | Best |
| **Aggressive cheap** | Sliding + Flash all | $0.05 | Worst |

production sweet spot: **hierarchical + Flash summary + prefix caching ≈ $0.20-0.50/session**.

### 5.7 Cost monitoring dashboard

```
┌─────────────────────────────────────────────────────────┐
│  Cost Dashboard                          (last 24h)      │
├─────────────────────────────────────────────────────────┤
│  Total spend:           $1,234.56                        │
│  Total sessions:        4,567                            │
│  Avg cost / session:    $0.27                            │
│  p99 cost / session:    $2.10  ⚠ (target < $1)          │
│                                                          │
│  Top expensive sessions:                                 │
│   session_abc  $4.50  120 turns  no compaction triggered │
│   session_def  $3.20  85 turns   compaction failed       │
│                                                          │
│  Compaction stats:                                       │
│   Triggered:       8,432 events                          │
│   Failed:          12 (alert if >50/h)                   │
│   Avg compression: 4.2x                                  │
│                                                          │
│  Model breakdown:                                        │
│   Gemini 3 Pro:    $980  (main reasoning)                │
│   Gemini 3 Flash:  $180  (summary)                       │
│   Claude Haiku:    $74   (tool routing)                  │
└─────────────────────────────────────────────────────────┘
```

---

# Part 3 · 把 5 个问题串起来看

5 个问题 = 同一个工程问题 5 层:

1. **Compaction strategies** 决定「context 怎么压」
2. **External memory** 决定「不进 context 的去哪」
3. **Tool output externalization** 决定「大 tool result 怎么处理」
4. **Lost-in-middle mitigation** 决定「关键 info 不被压没」
5. **Cost economics** 决定「production 经济可行」

面试场把这 5 层都讲清楚, + 「Internal Agent Platform hierarchical memory 案例」, 就是 staff-level long-running agent 设计.

---

## 必问 clarifying questions

**1. Agent 性质**

> "Conversational chat (turns sparse, user-driven) or work-loop agent (50 tool calls/turn, like Cursor/Devin)? Different shape."

**2. State 重要性**

> "Earlier turns 信息 critical (recall to make decision) or just nice-to-have? Decision log needed?"

**3. 用户期望**

> "User expects continuous coherent multi-day session, or each session reset OK? Cross-session memory needed?"

**4. Model context limit**

> "Current model 128K — moving to 1M (Gemini 3 Pro) would solve? Or always more demand?"

**5. Cost budget**

> "Per-session $ budget? $0.10 consumer / $1 B2B / $5 dev tool? Affects compaction aggressiveness."

---

## 5 步框架 (sample 45-60 min answer)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify agent shape + state importance + cost target |
| 5-15 min | 4 strategies overview (sliding / summary / hierarchical / selective) |
| 15-25 min | External memory (blob / vector DB / structured Postgres) |
| 25-35 min | Tool output externalization + lost-in-middle |
| 35-45 min | Cost math (Gemini 3 Pro / Flash routing + prefix caching) |
| 45-60 min | Observability + recall probe + production hardening |

---

## 我会这样答 (sample)

> "Clarify — *[假设: work-loop agent (Cursor-like), 50 turns multi-tool-call, state important (avoid re-read files), session 可达 4-8h, Gemini 3 Pro main + Flash summary, cost target $0.50/session]*.
>
> **4 strategies, used in combination**:
>
> 1. **Sliding window**: last 10 turns verbatim
> 2. **Hierarchical summary**: tier 1 (ancient, 500 tok) → tier 2 (500 tok) → tier 3 (5K) → tier 4 (verbatim recent)
> 3. **External memory**: blob (tool outputs > 1K), vector DB (episodic), Postgres (decisions / preferences)
> 4. **Selective pruning**: importance scoring, pinned messages never dropped
>
> **Compaction trigger**: soft cap 70% (90K of 128K) → run pipeline
>
> **Pipeline**:
> - Step A: externalize big tool outputs (> 1K → blob + summary + ref)
> - Step B: prune low-importance intermediate
> - Step C: hierarchical re-summarize tiers
> - Step D: reinforce decisions / preferences at end (lost-in-middle defense)
>
> **External memory**: 3 store
> - Blob (S3): full tool outputs, key by content hash, 24h TTL
> - Vector DB (Qdrant): episodic, search past turns by semantic
> - Postgres: structured (decisions, user_preferences, session_state)
>
> **Tool output handling**: >1K → externalize, replace with `<tool_output ref="...">{summary}</tool_output>`; agent has `get_full_tool_output(ref)` to fetch on demand
>
> **Lost-in-middle**: critical info (system prompt, decisions, preferences) always at start AND end; periodic recap every 10 turn; decision_log in Postgres always re-injected to system prompt
>
> **Cost**: Gemini 3 Pro main loop + Flash for summary, with prefix caching (50K project prefix cache 5min) — typical session $0.20-0.40
>
> **Observability**: per-turn token count, compaction events, recall probe weekly, session_cost dashboard with p99 alert if > $1
>
> **What I would NOT do**: truncate blindly oldest, single mega-summary, keep all tool outputs verbatim, no external memory, no pinning, no cost monitoring."

---

## 简历专属 reframe

| 题 | 你的经验 |
|---|---|
| Multi-turn coherence | **Voice agent** — multi-turn conversation, state across calls in 7 markets |
| External memory | **Internal Agent Platform** — shared session memory abstraction |
| Tool output mgmt | **BNPL chatbot** — RAG output selected top-k, not dump |
| Hierarchical summary | **Voice agent** — multi-call session, per-call summary + cross-call agg |
| Cost optimization | **TikTok payment infra** — every cent counts |
| Decision log | **BNPL** — payment / refund 决策必持久化合规 |

**主动 quote**:

> "Internal Agent Platform — we hit this on a multi-step agent that browsed 20+ files. Naive append-all blew context at turn 15. Built **hierarchical memory**: per file 'index card' (path, purpose, key symbols, last-modified hash) cached in context; full content offloaded to a blob store, fetched on agent's `read_file` tool call. Decisions ('user confirmed FastAPI', 'use Postgres not MySQL') persisted to a Postgres decision_log and re-injected to system prompt every turn. Context steady at 30K tokens even at turn 50. Cost dropped from $4 to $0.30 per session. The biggest single win was **prefix caching** — same project context 50K, Anthropic ephemeral cache gave us 90% off after first call."

---

## 5 follow-ups

**Q1**: "Summary quality is critical. How tune?"

**A**:
- **Structured summary** template: 'Decisions / Files modified / Open TODOs / User preferences / Errors'
- **Cheaper LLM** (Gemini 3 Flash $0.50/$3): summary doesn't need flagship
- **Recall test**: probe 'what did we decide about X' weekly → if model misses, summary improved
- **Versioned summaries**: keep old + new during transition, A/B
- **Distilled summarizer** if domain repeatable: fine-tune small model on (long turns, ideal summary) pairs

**Q2**: "1M / 2M context models exist (Gemini 3 Pro 2M). Just use them?"

**A**:
- **Cost still matters**: 2M tokens × $4/1M (Pro >200K) = $8/call; 100 turns × $8 = $800/session. Prohibitive.
- **Latency**: 2M context first-token 60-120s
- **Lost-in-middle still real**: even 2M, middle 50% range has 30-40% lower recall
- **Use 2M for**: cold-start (load 1 huge doc), not for accumulating 50-turn agent state
- **Hybrid**: short-term active context 32K, archived in vector DB

**Q3**: "Cost per session — what's economic?"

**A**: Depends on segment:
- $0.001-0.01/turn (Gemini 3 Flash): consumer chat acceptable
- $0.05-0.20/turn (Gemini 3 Pro): B2B / pro
- $0.50-3/agent task (mixed Pro + Opus): dev tool / enterprise
- Total session $0.20-2 normal, $5+ problematic
- Higher → must optimize via compaction + cheaper models on summarize + prefix caching

**Q4**: "User says 'pick up where we left off' from yesterday's session. Practical?"

**A**:
- Persist conversation state to Postgres (session_id, turns, decisions, preferences) on session-end
- On resume: load last summary + last 5 turns from DB + system prompt with decisions injected
- Optionally: snapshot full state before close, semantic-index all turns to Qdrant
- **Practical**: 80% restore is enough; pixel-perfect not worth the cost
- **User confirms continuity**: agent says "last time we agreed X — continuing on Y. Sound right?" — explicit handshake

**Q5**: "Agent forgets recent decision because compaction summarized it."

**A**:
- **Explicit decision log** in Postgres, separate from chat history, never compacted
- **Pinned messages**: user can pin a turn, never compacted
- **Decision-tagging**: LLM tags important turns with `decision_made` field in output schema, summarizer treats as must-keep
- **Periodic recap**: every 10 turn re-inject "key decisions so far" at end of context
- **Recall probe**: test "do you remember X" → fail trigger alert

---

## ❌ 易错点 (top 10)

1. **Truncate oldest blindly** — lose system / first-turn decisions
2. **Single mega-summary** — loses detail
3. **Keep all tool outputs verbatim** — 10MB output blows context
4. **No external memory** — everything in context
5. **No pinning** — summarizer flattens critical info
6. **Ignore lost-in-middle** — critical info buried
7. **No cost monitoring** — $20 session shock
8. **Summary uses flagship LLM** — wasteful, Flash 够
9. **No recall test** — summary degrades silently
10. **No prefix caching** — leave 90% savings on table

---

## ✅ 加分项 (top 10)

1. **4-strategy combination** (window + hierarchical summary + external + selective)
2. **Hierarchical summary** (4 tier, not flat)
3. **Externalize large tool outputs** with reference + dedup cache
4. **Vector-DB-backed episodic memory**
5. **Structured Postgres** for decisions / preferences
6. **Lost-in-middle aware** placement + periodic recap
7. **Decision log separate** from chat
8. **Pinned messages** for user control
9. **Prefix caching** (Gemini / Anthropic) for cost
10. **Quote Internal Agent Platform hierarchical memory $4 → $0.30**

---

## 一句话总结

> **Context management = 「Sliding 最近 + Hierarchical summary 中间 + External memory 大数据 + Selective pruning 不重要 + Pinning + Decision log + Lost-in-middle 觉知 + Prefix caching 省钱」**.
>
> 长跑 agent 稳定性的核心: context size 不随 turn 数线性增长, cost / session 可控.

---

## Cheat Sheet

```
4 compaction strategies (combine):
  1. Sliding window (last N turn verbatim)
  2. Summarize old + keep recent
  3. Hierarchical summary (4 tier)
  4. Selective pruning by importance

Trigger:
  soft cap 70% of model limit → compact
  hard cap 90% → emergency aggressive compact

Hierarchical 4 tier:
  Tier 1: ancient (turn 1-30, heavy compress, 500 tok)
  Tier 2: middle (turn 31-40, medium, 1500 tok)
  Tier 3: recent (turn 41-50, light, 5000 tok)
  Tier 4: latest (verbatim, last 5-10 turns)

External memory (3 store):
  Blob (S3): tool outputs >1K, files, artifacts
  Vector DB (Qdrant): episodic memory, semantic search past
  Postgres: structured (decisions, preferences, session_state)

Tool output thresholds:
  ≤ 1K tok: inline
  1K-5K: summarize + blob ref
  5K-50K: minimal summary + blob ref
  > 50K: reject / force pagination

Pin / preserve patterns:
  System prompt (always)
  User-stated preferences
  Confirmed decisions
  Errors that informed strategy
  Files modified (path + hash)
  Open TODOs

Lost-in-middle defense:
  Critical info at start AND end
  Periodic recap every 10 turn
  Decision log in system prompt
  Pinned messages

Cost (2026 pricing):
  Gemini 3 Pro:    $2 (≤200K) / $4 (>200K) / $12 out per 1M
  Gemini 3 Flash:  $0.50 / $3
  Claude Opus 4.7: $5 / $25
  Sonnet 4.6:      $3 / $15
  Haiku 4.5:       $1 / $5

Cost optimization:
  Hierarchical summary (4x compress)
  Flash for summary (Pro for reasoning)
  Prefix caching (50K project ctx, 5min, 90% off cache hit)
  Compact at soft cap, not every turn
  Per-session budget alert

Observability:
  per-turn input/output tokens, cost
  compaction events (count, before/after, latency)
  recall probe weekly (random fact verify)
  session_cost dashboard (avg, p99)

Tool zoo (2026):
  Tracing: Phoenix (Arize), LangSmith, Langfuse
  Vector DB: Qdrant, Pinecone, Weaviate
  Blob: S3, GCS, Azure Blob
  Structured: Postgres, Redis, DynamoDB
  Compaction libs: LangChain ConversationSummaryBufferMemory, LlamaIndex memory

红线:
  - Blind truncation
  - Single mega-summary
  - All tool outputs verbatim
  - No external memory
  - No pinning
  - Ignore lost-in-middle
  - No cost monitoring
  - No recall probe
  - No prefix caching
```
