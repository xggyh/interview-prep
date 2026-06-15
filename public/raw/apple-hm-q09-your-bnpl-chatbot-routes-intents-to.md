# 🍎 HM Q9 · Your BNPL chatbot routes intents to sub-agents with a FAQ RAG fallback — walk me through that design.

> **类别**: BNPL & Agent Platform · **考点**: router + dispatch + RAG 三层架构, 1:1 对应这个 Apple 团队的 agentic platform · ⚠️ [✏️] 数字背前替换成真实值

## 🧠 这题在测什么 / 面试官想看到

这是这个团队的题眼 —— 他们就在做 multi-turn、multi-agent 的 conversational LLM 应用，你的 BNPL chatbot 几乎是 1:1 的对照。面试官想看你能不能**清晰地分层**：哪一层做决策 (route)、哪一层做动作 (dispatch + tool calling)、哪一层做兜底 (RAG)。强答会把三层的**边界和失败处理**讲清楚 ("如果 router 错了会怎样"),弱答会把它讲成一个大 LLM prompt。陷阱:把它说成"一个 agent 干所有事",或者声称 router 100% 准 —— Apple 会立刻钻这个洞。

## 📋 English Answer (背诵稿, 主答 ~60-90 秒 + 可延伸)

"It's a three-layer design, and the key idea is separation of concerns: routing, doing, and falling back.

**Layer one — the router.**
- Every user turn first hits an intent classifier.
- It maps the message to one of a small set of *actionable* intents — order lookup, refund, dispute — or to a catch-all *general* bucket.
- The router only decides *where the turn goes*; it does not answer. That's deliberate — it's the thin, fast layer on every turn's critical path.

**Layer two — sub-agent dispatch.**
- If it's an actionable intent, I route to a dedicated workflow sub-agent.
- Each sub-agent owns one domain, has its own *scoped* tools — order API, refund API, dispute API — and its own guardrails.
- So the refund agent can call the refund endpoint, but it physically cannot touch anything else.
- It does tool calling, gets structured data back, and generates a *grounded* reply from that data.
- That containment is deliberate: in a money-touching flow you want the blast radius of any one agent to be small.

**Layer three — FAQ RAG fallback.**
- If the intent is general — 'how does BNPL work', 'when is my payment due in principle' — there's no API to call.
- So it goes to a retrieval-augmented path: retrieve from our policy and FAQ knowledge base, then generate an answer grounded in those passages, with citations.
- This catches the *informational* long tail, as opposed to the *transactional* intents the sub-agents handle.

The router is intentionally thin and fast; the sub-agents hold the business logic; RAG catches everything informational rather than transactional. And critically — the router is never assumed correct. There's a self-healing path when it misroutes, which I can walk through."

*(可延伸 1 — 编排与状态:)* "Holding it together is an orchestration layer. It owns the conversation state and decides who handles each turn — router, then a sub-agent, then back to the router if needed. The sub-agents themselves are stateless workers; the orchestrator owns memory and the control flow. That separation is what lets a multi-turn conversation move cleanly between an order-lookup turn and a refund turn without losing context."

*(可延伸 2 — eval:)* "On top of that, I owned the metrics and eval harness with product and ops — we defined what 'resolved' meant *per intent*, so each layer was measured separately rather than as one black box. The router was scored on routing accuracy, the sub-agents on correct-action and resolution, RAG on grounded-answer quality. When something regressed I could tell you *which layer* moved, which is the whole point of designing it as layers rather than one prompt."

*(一句话总纲, 如果时间紧只说这句:)* "So: a thin fast router decides, scoped sub-agents act with tool calling, RAG grounds the informational long tail, an orchestrator owns state, and every layer is independently measured — and none of it assumes the router is perfect."

## 🇨🇳 中文要点 (理解 + 记忆骨架)

记三个词:**route → dispatch → fallback**,外加一个底座 **orchestrator (state)**。

- **Router (薄、快)**: intent classifier 只决定"这一轮去哪",**不回答**。输出是 actionable intent (order/refund/dispute) 或 general。它便宜、低延迟,因为它在每一轮的关键路径上。
- **Sub-agent dispatch (业务逻辑)**: 每个 sub-agent 管一个域,自带 scoped tools + guardrails。refund agent 只能调 refund API —— 这是故意的 **blast radius 收敛**,money flow 里很关键。流程是 tool calling → 拿结构化数据 → grounded generation。每个 sub-agent 独立,可单独 eval、单独调 prompt。
- **RAG fallback (信息类兜底)**: general intent 没有 API 可调,走检索 —— 从 policy/FAQ 知识库 retrieve,再 grounded generation + citation。它接的是**信息类**长尾,不是交易类。
- **Orchestrator (底座, 拿状态)**: 持有 conversation state + 控制流,决定每一轮谁来处理。sub-agent 是无状态 worker,**orchestrator 持有 memory** —— 这是多轮对话能在 order 轮和 refund 轮之间干净切换的原因。
- **收尾钩子**: router 绝不假设 100% 准,有 misroute 自愈路径 (留给 Q10);指标和 eval harness 是我跟 product/ops 一起定的,**每层分开量** (router 看路由准确率、sub-agent 看 correct-action/resolution、RAG 看 grounded 质量) —— 出问题能定位到是哪一层动了。

为什么这么分 (面试官真正想听的判断):
- **关键路径要快** → router 薄。
- **money flow 要安全** → 权限按域 scope 死,blast radius 小。
- **交易 vs 信息是两类问题** → 一个用 tool calling 拿真实数据,一个用 RAG 拿知识;混在一起两边都做不好。

骨架一句话:**"分层是为了 separation of concerns —— 一层决策、一层动作 (含 tool + 收敛权限)、一层信息兜底、一个 orchestrator 持有状态;每层独立可测,且 router 永不假设 100% 准。"**

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: Why separate sub-agents per intent instead of one agent with all the tools?**
- Containment and reliability. One agent with every tool has a large blast radius — a wrong tool call in a refund context could trigger a dispute action.
- Scoping tools per sub-agent means the model literally can't take an out-of-domain action.
- It also makes each agent easier to eval, prompt-tune, and reason about independently.
- The cost is orchestration complexity — which is exactly what the platform layer absorbs.

**Q: How does a turn flow when the user mixes two intents — "where's my order and I want a refund"?**
- The router picks the dominant / first actionable intent and routes there; the sub-agent handles that, then control returns to the router for the second intent.
- I'd be honest that clean single-intent turns are the common case [✏️ 核实 实际多意图占比].
- Multi-intent was handled by re-routing on the *next* turn, not parallel sub-agent fan-out — I won't overclaim a DAG orchestrator I didn't build.

**Q: Where does the conversation state live across these layers?**
State is held at the orchestration layer, not inside any one sub-agent — so when control passes from router to a sub-agent to RAG, they share the same conversation context and any resolved slots. Sub-agents are stateless workers; the orchestrator owns memory. (That's one of the things we abstracted into the platform.)

**Q: What if RAG and a sub-agent both seem applicable?**
Actionable intent always wins over RAG. RAG is the fallback, not a peer — if there's a real transaction the user wants done, retrieving an FAQ passage is the wrong answer. The router's job is precisely to prefer action when an actionable intent fires with enough confidence.

**Q: How did you decide the intent taxonomy — why those three?**
Data-driven with ops. We looked at the actual ticket distribution; order lookup, refund, and dispute were the high-volume, automatable, money-touching flows worth a dedicated agent. Long-tail informational questions weren't worth a workflow each, so they collapse into the RAG bucket. [✏️ 核实 这三类占工单比例]

**Q: How would you add a new intent — say, "change payment date" — six months in?**
That's where the layering pays off. I register a new sub-agent with its own scoped tool and guardrails, add the intent to the router's label set, and the rest of the system is untouched. The orchestrator and RAG don't change. That's the difference between a layered design and a monolithic prompt — extending a monolith means re-validating the whole thing; extending this means validating one new agent against its own eval set. This is also exactly the argument for the platform: the *mechanics* of registering an agent are shared, so adding an intent is config plus one agent, not a project.

**Q: How does this map to what this Apple team is building?**
Pretty directly — it's the same shape. A conversational, multi-turn, multi-agent system where a controller routes user intent to specialized capabilities, falls back to retrieval for informational queries, and keeps state across turns. The domain differs — customer support across Apple's lines of business versus BNPL — but routing, scoped dispatch, grounded fallback, and an orchestrator owning state is the architecture either way. The thing I'd bring is having already hit the hard edges: misroute recovery, money-touching safety, and per-layer eval.

**Q: Walk me through one concrete turn, end to end.**
Take "I want a refund on order 12345." Router classifies it as `refund` with high confidence and passes the turn plus the order ID to the refund sub-agent. The sub-agent calls the order API to verify the order exists and is refund-eligible, calls the refund API if so, gets a structured result back — refund initiated, amount, ETA — and generates a grounded reply citing that result, not free-text. The orchestrator records the resolved state. If the order *isn't* refund-eligible, the sub-agent doesn't invent an answer — it explains why and offers the next step or a handoff. Every fact in the reply traces to a tool result.

## ⚠️ 边界 & 红线 (honest limits + what NOT to say)

- 如果被追到很细的 multi-intent 并行编排,**老实说**当时主要是单意图 + 下一轮 re-route,不是真正的并行 sub-agent fan-out。别吹成 full DAG orchestration。
- 不要声称 router 100% 准 —— 反而要主动说"它会错,我有自愈路径",这才是 senior 信号 (顺势引到 Q10)。
- 不要把 RAG 说成主路径。它是 fallback;actionable intent 优先。说反了会显得不懂 transactional vs informational 的区别。
- 任何具体的工单占比 / 自动化率数字没核实就别说成事实,用 [✏️ 核实] 占位。
- 如果被问"sub-agent 之间会不会互相调用 / 协作",诚实说当时是 **router 居中调度** (hub-and-spoke),不是 sub-agent 之间自由通信的 mesh —— 后者复杂且当时没必要。别为了显复杂硬说成 agent-to-agent。
- "automated case resolution" 这个词别理解成"全自动无人工" —— 它是高置信、低风险的自动闭环;敏感/低置信会转人工。把它说成 100% 无人工会和 Q10 的自愈、Q6 的合规兜底自相矛盾。

## ✅ 加分钩子 (主动抛, steer 到强项)

- 主动点出 **"blast radius 收敛"** 是有意的安全设计 —— money-touching flow 里把每个 agent 的权限 scope 死。这正好接 Apple 的 customer-facing、合规敏感场景。
- 提一句 **"这套 orchestration / tool integration / memory / eval 后来抽象成了内部 Agent Platform"** —— 把单项目自然升级成平台思维 (引到 Q13)。
- 强调 **eval harness 是跟 product/ops 一起定的**,每层分开量 —— 对上 JD 反复强调的 "LLM eval" + "partner with stakeholders"。
- 主动说 **"这跟你们团队在做的 multi-turn、multi-agent 系统是同一个 shape"** —— 让面试官看到 transfer 是直接的,不用脑补。然后补一句你已经踩过硬边界 (misroute 恢复、money 安全、分层 eval)。
- 如果对方对延迟感兴趣,顺势抛 **"router 故意做薄是因为它在每一轮的关键路径上"** —— 把架构选择和 latency 挂钩,接 JD 的 latency/cost 主线 (可引到 Q4/Q20)。
