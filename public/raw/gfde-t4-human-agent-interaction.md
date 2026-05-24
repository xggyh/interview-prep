## 题目

> "Design **human-agent interaction patterns** for a customer support chatbot. When should the agent: (a) act autonomously, (b) ask the user to confirm, (c) ask a human agent to take over? Walk through the **escalation logic** end-to-end."

或追问形态:

> "Agent confidence is hard to calibrate. How do you decide 'agent confident enough to act' vs 'needs human'?"

**出处**: Google FDE T4 (Forward Deployed Engineer Scenario Delivery), HR-tipped. 测试 **human-in-the-loop product design** 能力 — 不是技术 (agent 怎么写), 而是**用户体验 + 信任 + 失败模式**.

**Round**: Human-Agent UX / Interaction Design (45-60 min)

---

## 这道题在考什么

考你 **human-in-the-loop product design** 功底:

1. **4 interaction patterns** — 不是 1 个 pattern, 必须 coexist
2. **Confidence calibration** — raw LLM score 不可信
3. **Escalation paths** — smooth handoff, 不让用户重复
4. **State preservation** — human 接 agent 的活, 不能 reset
5. **Trust building** — UX 教用户什么时候信 agent

**不考**: "你 LLM 用什么 model". 考 **"用户和 agent / human 三方怎么 dance"**.

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**Human-Agent Interaction (HAI)**: 用户、agent (LLM-driven 自动化)、human agent (人工客服) 三方之间的交互. 不是简单的 "user ↔ agent" 二元, 而是**三角**: user, agent, human.

**Confidence Calibration**: agent **自评对自己答案的把握**, 必须和**真实正确率**相符. Raw LLM log-prob 通常 **overconfident** (说 0.9 的实际只对 60%), 必须用 calibration 技术 (Platt scaling / isotonic regression) 把概率拉直.

**Escalation**: agent 把 conversation 交给 human. 分 **主动** (agent confidence 低自己 escalate) 和 **被动** (user 要求 human). 关键是 **smooth handoff** — human 看到 agent 已经做的, 不让 user 重复.

**Confirmation Pattern**: agent 不直接执行, 先 draft, 让 user (或 human reviewer) 确认. 适用于 **irreversible** action.

---

## 2. 核心问题 / 矛盾

**设想没有 4-pattern + calibration 的灾难场景**:

```
Customer support chatbot:
  - 所有 query 都 LLM 直答 (no human)
  - LLM 自评 confidence 0.9, 直接 reply
  - 实际 60% 答案错 (但 LLM 不知道自己错)
  - User 不满, 跳过 agent 喊 "I want human"
  - chatbot 不让转 (没 fallback)
  - User 取消订阅 / 投诉 / 上社媒抱怨

或反过来:
  - 所有 query 都转 human
  - Human 30-min wait 平均
  - User 焦躁, 离开
  - Human 团队加班, 流失
  - 没人用 chatbot (没 value)
```

**问题根源**:

- **单 pattern** (只 auto 或只 human) → 都失败
- **Trust raw LLM confidence** → overconfident, 错都不知道
- **No threshold tuning** → 一刀切, 不能 query-type 区分
- **Sudden escalation** → user 重复 5 分钟的 context
- **No takeover option** → user 被困

**4-pattern + calibration 解法**:

```
4 patterns coexist:
A: Confidence threshold — agent confident 就 auto, 低就 escalate
B: Confirm-required — destructive action 必 user 确认
C: Scheduled review — agent auto, human 抽样 post-hoc 看
D: User-initiated takeover — user 任何时候可 /human

Calibration: 5+ signals 合成 composite score, 用 isotonic 校准.
Threshold: 0.85 auto / 0.5-0.85 offer human / < 0.5 preempt escalate
Smooth handoff: human 看 transcript + intent + draft + concerns
Observability: per-type escalation, override, satisfaction
```

---

## 3. 决策树 — Per-Query Pattern 选择

```
                  ┌─────────────────────────────────────┐
                  │  User message arrives               │
                  └─────────────────┬───────────────────┘
                                    │
            ┌───────────────────────┴─────────────────────────┐
            │                                                 │
            ▼                                                 ▼
   User explicitly asks                              Auto-route by signals
   "/human" or "speak to human"                                │
            │                                                 │
            ▼                                                 │
        ┌────────────────┐                                    │
        │ Pattern D:     │                                    │
        │ Immediate human│                                    │
        │ (no fight)     │                                    │
        └────────────────┘                                    │
                                                              │
       ┌──────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│  Action destructive / irreversible?           │
│  (refund $, password reset, account delete)  │
└──────────────────────┬───────────────────────┘
                       │
                ┌──────┴──────┐
            YES │             │ NO
                ▼             │
        ┌─────────────┐       │
        │ Pattern B:  │       │
        │ Confirm-    │       │
        │ required    │       │
        │ (draft +    │       │
        │  user OK)   │       │
        └─────────────┘       │
                              ▼
                  ┌────────────────────────────┐
                  │ Compute composite confidence│
                  │ (5+ signals)                │
                  └─────────────┬───────────────┘
                                │
                  ┌─────────────┴───────────────────────────┐
                  │                                         │
              > 0.85                                    < 0.5
                  ▼                                         ▼
            ┌──────────┐                            ┌──────────────┐
            │ Pattern A│                            │ Pattern A     │
            │ Auto     │                            │ Preempt human │
            │ respond  │                            │ "let me get a │
            │          │                            │  human"       │
            └──────────┘                            └──────────────┘
                  
                            0.5-0.85
                                ▼
                        ┌──────────────────┐
                        │ Respond + offer  │
                        │ "Not sure?       │
                        │  Talk to human?" │
                        └──────────────────┘

For all auto-responded: 5% sample → Pattern C
(human review post-hoc, signal for improvement)
```

---

## 4. 4 Interaction Patterns 分类表

| Pattern | When | Agent acts | Human role |
|---|---|---|---|
| **A. Confidence threshold** | High confidence | Auto-respond | Reviews escalations |
| **B. Confirm-required** | Destructive action | Draft only | 1-click approve |
| **C. Scheduled review** | All auto actions | Auto-act | Post-hoc 5% sample audit |
| **D. User-initiated** | User asks for human | Hands off | Take over |

**All 4 coexist** in same product. Most products start with A + B + D, add C after.

**Decision matrix per query type** (前面 Part 1 决策树的 reference):

| Query type | Primary Pattern | Why |
|---|---|---|
| "What's my balance?" | A (auto) | Low stakes, deterministic |
| "Reset my password" | B (confirm) | Action with consequence, identity-protective |
| "Refund $500" | B (confirm) + D offer | High stakes, complex |
| "I'm angry, you suck" | D (auto human) | Sentiment, human relationship |
| "How do I file a tax form for my country?" | A with low conf → D | Specialized, agent uncertain |
| New / weird question | A + D fallback | Unknown territory |
| "Change my email address" | B (confirm) + verify identity | Identity-sensitive |
| "Cancel my subscription" | B (confirm + retention attempt) | Reversal pattern |
| "Show me my last order" | A (auto) | Read-only |
| "I need to dispute a charge" | D (human, but agent prep summary) | Complex, requires investigation |

---

## 5. 具体业务场景 (5 个变体)

### 场景 A: 你工作背景 — BNPL Chatbot 客服 (Anchor case)

**背景**: TikTok PayLater 客服 chatbot, 处理还款、退款、账单、合同问题.

**4 patterns 落地**:

- **Pattern A** (confidence threshold):
  - "我还款日是哪天?" — confidence 0.95, auto-respond
  - "为什么这单 BNPL 没批?" — confidence 0.7, respond with reason + offer human
  - "为什么我有 fraud flag?" — confidence 0.3, preempt human

- **Pattern B** (confirm-required):
  - "退款这单 $200" → agent drafts: "I'll initiate $200 refund to your card ending 4242. Confirm?"
  - User confirms → agent executes

- **Pattern C** (scheduled review):
  - 5% of agent's auto-responses sampled
  - Human reviewer marks: 正确 / 错 / 不完整
  - Aggregated 数据用于 retrain / prompt 调整

- **Pattern D** (user-initiated):
  - User 说 "I want a human" → 立即转 (no gating, no friction)

**Calibration story**:

- 初版 agent: raw LLM confidence
- Eval: 1000 known-answer queries, plot confidence bucket vs accuracy
- 发现 0.8 confidence = 65% 实际对 (overconfident)
- 用 isotonic regression 校准
- Re-deploy: 0.8 confidence = 80% 实际对 (calibrated)
- 业务效果: false-escalation 从 18% → 7%, missed-escalation 从 5% → 2%

### 场景 B: Coding Agent (Cursor / Copilot 风格)

- **A**: small / non-destructive auto-apply (单文件 < 20 行 + 在 git working tree)
- **B**: 多文件 / > 100 行 / delete file / 改 config → confirm
- **D**: dev 改 file 直接 override agent, no fight
- **特殊**: test gate — agent 跑 test, fail 时不能 auto apply

### 场景 C: 医疗 Triage 助手

- **A**: 简单症状归类 (e.g., 普通感冒) auto
- **B**: 不常见症状, agent 建议 + 让 user 确认
- **保守 default**: 不确定 → 上调到更严重 tier (false positive 优于 false negative)
- **红 flag 永远 D**: 胸痛 / 呼吸困难 → 不 triage, 直转 ER
- **人 takeover trivial**: 任何时候 nurse 可 override

### 场景 D: Sales Agent

- **A**: routine info (产品价格 / 试用流程) auto
- **B**: 给客户发 demo 邀请前 — confirm with rep
- **D**: high-value signal (deal > $100K) — 直转真 sales
- **特殊**: emotion / sentiment → 立即 human

### 场景 E: Trading / Financial Agent

- **A**: 报价、查询 — auto
- **B**: 下单买卖 — 必 confirm (small auto, large human)
- **C**: 每周抽样 agent decision, risk team review
- **D**: kill switch — 风控团队可一键 pause all
- **特殊**: 大宗 / cross-border / 监管要求人审 — hard rule

---

## 6. 实施 Playbook (4-phase rollout)

**Phase 1: Pattern D + Manual Routing (Week 1-2)**

- 只上 chatbot 接入 + "I want human" 按钮
- 所有非简单 query 都转 human
- 目的: 数据收集 (typical query 长啥样)

**Phase 2: Pattern A + B (Week 3-8)**

- 高 confidence + low stakes → A auto
- Destructive action → B confirm
- 中 confidence → A respond + offer human
- 低 confidence → preempt to human

**Phase 3: Calibration + Tuning (Week 8-12)**

- Eval set (500+ known-answer queries)
- Plot calibration curve
- Apply Platt / isotonic
- Tune threshold (0.85 / 0.5 may not be right for your domain)

**Phase 4: Pattern C + Observability (Week 12+)**

- 5% sampled auto-actions to human review
- Build dashboards (calibration plot, escalation rate, override rate, satisfaction)
- Weekly review meeting (improve based on signal)

---

## 7. 易错坑表

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **Single pattern** (only auto or only human) | 体验差或没 value |
| 2 | **Trust raw LLM confidence** | Overconfident, 错都不知道 |
| 3 | **Sudden escalation** (user 重新解释) | User 体验崩 |
| 4 | **No threshold tuning per query type** | 一刀切, 不灵活 |
| 5 | **No calibration eval** | Confidence number 没意义 |
| 6 | **No takeover option** | User 被困 |
| 7 | **No observability** | Escalation pattern 看不见 |
| 8 | **Gate the human path** ("Let me try again, please") | User 烦, 体验崩 |
| 9 | **No queue / off-hours handling** | 无 human 时 silent drop |
| 10 | **No false / missed escalation track** | Quality 不可量化 |

---

## 一句话总结 (Part 1)

> **Human-Agent Interaction = "4 pattern coexist (auto + confirm + sample-review + user-takeover) + calibrated confidence (5+ signals) + smooth handoff (no re-explain) + observability"**.
>
> 90% chatbot 失败不是 LLM 不行, 是 **没设计好这 4 个 pattern 怎么 coexist**.

---

# Part 2 · 5 个深度问题

## ⚙️ Problem 1: 4 Patterns Coexisting — 不是选一个, 必须四个一起

**最常见的错**: 把 4 个 pattern 当 "选一个". 实际**必须 coexist**.

### 1.1 Pattern A — Confidence Threshold Escalation

**用途**: 大部分 informational query.

**逻辑**:

```python
async def handle(user_msg, conv_history):
    response, confidence = await agent.respond(user_msg, conv_history)
    
    if confidence > 0.85:
        return response  # Pattern A: auto
    elif confidence > 0.5:
        return f"{response}\n\nNot sure this is what you need? [Talk to human]"
        # Pattern A: respond + offer
    else:
        return await escalate_to_human(conv_history, agent_draft=response)
        # Pattern A: preempt
```

**关键点**:

- Threshold (0.85 / 0.5) 不是拍脑袋, 是 calibrated + tuned
- 不同 query type 可不同 threshold (sensitive query 阈值更高)

### 1.2 Pattern B — Confirm-Required for Destructive Action

**用途**: irreversible action (refund, password reset, send email).

**逻辑**:

```python
async def execute_action(action, args):
    if action.is_destructive:
        # Agent drafts the intended action
        draft = await agent.draft(action, args)
        
        # Show draft to user, get confirmation
        confirmed = await ui.confirm({
            'description': draft.human_readable,
            'args': draft.args,
            'side_effects': draft.side_effects,  # "Will send email to..." / "Will charge..."
        })
        
        if confirmed:
            return await execute(action, args)
        else:
            return await agent.respond_to_cancellation(args)
    else:
        return await execute(action, args)  # Reversible, no confirm
```

**Confirmation UI 设计**:

```
[Agent suggests: Refund $200 to card ending 4242]

This will:
✓ Refund $200 USD
✓ Take 3-5 business days to appear
✓ Send email confirmation to john@example.com

[Confirm Refund]   [Modify amount]   [Cancel]
```

**关键点**:

- Confirm 不是 "yes / no", 是**显示 side effects + 让 user 完整 understand**
- 大额 confirm 应该有更高 friction (type 'confirm' / 2FA)
- 小额 confirm 1-click

### 1.3 Pattern C — Scheduled Human Review (Post-Hoc Audit)

**用途**: agent 已 auto 做了, 但人需要 sample 检查 quality.

**逻辑**:

```python
async def handle_with_post_hoc_review(query, ...):
    response = await handle(query)
    
    # 5% sample to human review queue
    if random.random() < 0.05:
        await queue_for_human_review({
            'conversation': conv,
            'agent_response': response,
            'sample_timestamp': now(),
        })
    
    return response

# Daily batch
async def reviewer_dashboard():
    items = await fetch_pending_reviews()
    for item in items:
        # Reviewer sees agent's response + can mark:
        # - Correct (no action)
        # - Incomplete (improve prompt)
        # - Wrong (training signal + alert)
        # - Customer harmed (incident response)
        pass
```

**关键点**:

- 5% sample 是平衡: 太少 (1%) 看不出 pattern, 太多 (20%) 人累
- Sample stratified by query type (各类都看一些)
- Reviewer 反馈 → 直接进 prompt iteration / fine-tuning queue

### 1.4 Pattern D — User-Initiated Takeover

**用途**: user 明确表达 "I want human".

**逻辑**:

```python
async def handle_user_msg(user_msg, conv):
    # First, check for explicit user-takeover signal
    if matches_human_request(user_msg):
        return await escalate_to_human(conv, reason='user_request')
    
    # Otherwise normal flow (Pattern A / B / C)
    return await normal_handle(user_msg, conv)

def matches_human_request(msg):
    patterns = [
        'speak to human', 'talk to human', 'real person',
        'human agent', 'human please', 'i want a human',
        '/human', 'transfer me', '人工', '转人工',
    ]
    return any(p in msg.lower() for p in patterns)
```

**关键点**:

- **No gating** — 不要 "Let me try again, please". 直接 OK.
- **Track**: 高 bypass rate (大量 user 喊 human) = agent 质量信号
- Off-hours: 'No agents available, callback form?'
- High volume: queue with ETA shown
- **Never silently drop**

### 1.5 4 Patterns 协同 Logic

```python
async def main_handler(user_msg, conv):
    # 1. Pattern D first: user explicit takeover
    if matches_human_request(user_msg):
        return await escalate_to_human(conv, reason='user_request')
    
    # 2. Pattern B: destructive action gate
    intent = await classify_intent(user_msg)
    if intent.requires_confirm:
        draft = await agent.draft_action(intent)
        return await present_confirm_ui(draft)
    
    # 3. Pattern A: confidence-based routing
    response, confidence = await agent.respond(user_msg, conv)
    
    if confidence > 0.85:
        # Auto-respond
        # 4. Pattern C: 5% sample to review
        if random.random() < 0.05:
            await schedule_review(conv, response)
        return response
    elif confidence > 0.5:
        return f"{response}\n\n[Connect to human if not helpful]"
    else:
        return await escalate_to_human(conv, agent_draft=response)
```

**所有 4 pattern 在 same handler 里跑**.

---

## ⚙️ Problem 2: Composite Confidence Calibration

**Raw LLM log-prob 不可信**. 必须 **composite from 5+ signals + calibrate with eval data**.

### 2.1 为什么 raw LLM confidence 不可信

**事实**:

- Same answer different prompt → 不同 score
- Models often **overconfident** (说 0.9 → 实际 60%)
- LLM "I don't know" 时可能依然给高 score 的答案 (hallucination)
- Log-prob 是 token-level, 不是 answer-level

**Eval 实验** (你需要做的):

```python
# Build eval set: 500-1000 questions with known correct answer
eval_set = load_known_answer_questions()

results = []
for q in eval_set:
    response, confidence = await agent.respond(q.question)
    is_correct = check_correctness(response, q.expected)
    results.append({'confidence': confidence, 'correct': is_correct})

# Plot: 横轴 confidence bucket (0.1, 0.2, ..., 0.9), 纵轴 % correct in that bucket
# Perfect calibration: y = x (diagonal)
# Overconfident: y < x (curve below diagonal)
# Underconfident: y > x (curve above)

import matplotlib.pyplot as plt
buckets = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
accuracy = [bucket_accuracy(results, b, b+0.1) for b in buckets]
plt.plot(buckets, accuracy, 'o-', label='actual')
plt.plot([0,1], [0,1], '--', label='perfect calibration')
```

**典型结果**: LLM 在 0.9 confidence 上, 实际 ~60% correct. **Overconfident**.

### 2.2 5+ Signals for Composite Score

不仅靠 LLM log-prob, 综合**多个独立信号**:

**Signal 1: LLM token log-prob** (raw)
- Anthropic / OpenAI API 都返回 log-prob
- 弱信号, 但 free

**Signal 2: Self-consistency**

```python
async def self_consistency_check(query):
    answers = await asyncio.gather(*[
        agent.respond(query) for _ in range(3)
    ])
    # If all 3 responses same → high consistency
    return len(set(a.canonical_form() for a in answers)) == 1
```

**逻辑**: 同一 query 跑 3 次, 答案一致 → 信号 strong. 不一致 → 信号 weak.

**Signal 3: Tool grounding (citations)**

```python
def has_citations(response):
    return response.contains_source_links() and response.cites_retrieved_docs
```

**逻辑**: agent 如果引用了 RAG retrieved doc → hallucination 风险低. 没引用 → 可能编造.

**Signal 4: Schema validation**

```python
def schema_valid(response, expected_schema):
    try:
        validate(response, expected_schema)
        return True
    except ValidationError:
        return False
```

**逻辑**: 结构化 output 通过 schema → high confidence. Schema 失败 → 模型乱写.

**Signal 5: OOD detection (out-of-distribution)**

```python
def ood_distance(query):
    # Embed query, find nearest in known-successful query DB
    embed = embeddings.encode(query)
    nearest = vector_db.search(embed, top_k=1)[0]
    return 1.0 - nearest.similarity  # 0 = exact match, 1 = totally novel
```

**逻辑**: 见过类似 query → high confidence. 全新 query → low confidence.

**Signal 6: Sentiment / complexity**

```python
def query_complexity(query):
    # Length + clauses + entities
    return (
        word_count(query) / 100 +  # length
        clause_count(query) / 5 +   # multi-part
        entity_count(query) / 5     # entities
    )
```

**逻辑**: 长 / 多 part / 多实体 query → 难答 → low confidence.

**Signal 7: Explicit refusal detected**

```python
def contains_refusal(response):
    patterns = [
        "i don't know", "i'm not sure", "i cannot",
        "consult a professional", "i recommend you contact",
        "i don't have information", "as an ai",
    ]
    return any(p in response.lower() for p in patterns)
```

**逻辑**: agent 自己说 "I don't know" → 显然不 confident.

### 2.3 Composite Score 合成

```python
def composite_confidence(query, response, agent_state):
    score = 1.0
    
    # Signal 1: LLM log-prob (continuous)
    score *= max(0.1, agent_state.logprob_normalized)
    
    # Signal 2: Self-consistency (boolean penalty)
    if not agent_state.self_consistency_passed:
        score *= 0.5
    
    # Signal 3: Tool grounding (boolean penalty)
    if not response.has_citations:
        score *= 0.7
    
    # Signal 4: Schema validation (boolean penalty)
    if not response.schema_valid:
        score *= 0.5
    
    # Signal 5: OOD (continuous)
    if agent_state.ood_distance > 0.4:
        score *= max(0.3, 1 - agent_state.ood_distance)
    
    # Signal 6: Complexity (continuous)
    if agent_state.query_complexity > 2.0:
        score *= max(0.5, 1 / agent_state.query_complexity)
    
    # Signal 7: Refusal (boolean override)
    if response.contains_refusal:
        score = 0.0
    
    return clamp(score, 0, 1)
```

**调权重**: 用 eval set 跑出最优组合.

### 2.4 Calibration via Platt / Isotonic Regression

**Platt scaling** (sigmoid):

```python
from sklearn.linear_model import LogisticRegression

# Train calibrator on eval data
X = [[r.raw_confidence] for r in eval_results]  # 输入: raw
y = [r.is_correct for r in eval_results]         # target: 是否对

calibrator = LogisticRegression()
calibrator.fit(X, y)

def calibrated_score(raw):
    return calibrator.predict_proba([[raw]])[0][1]
```

**Isotonic regression** (more flexible, non-monotonic-can-handle):

```python
from sklearn.isotonic import IsotonicRegression

calibrator = IsotonicRegression(out_of_bounds='clip')
calibrator.fit(raw_scores, is_correct_flags)

def calibrated_score(raw):
    return calibrator.predict([raw])[0]
```

**Choose**:
- Platt: 数据少, 简单 monotonic
- Isotonic: 数据多 (500+), 更精确

### 2.5 Calibration Maintenance

**Drift detection**:

```python
# Weekly job: re-eval on recent labeled data
def check_calibration_drift():
    recent_results = load_last_week_labeled_results()
    for bucket in [0.1, 0.2, ..., 0.9]:
        actual_accuracy = compute_accuracy(recent_results, bucket)
        expected_accuracy = bucket  # post-calibration
        if abs(actual_accuracy - expected_accuracy) > 0.1:
            alert(f'Calibration drift at confidence {bucket}')
            trigger_recalibration()
```

**Recalibration trigger**:
- Drift > 10% on any bucket
- Model version change
- Major prompt change
- Quarterly scheduled

---

## ⚙️ Problem 3: Threshold Tuning + Tiered Response

**Threshold 不是拍脑袋**, 必须基于业务 cost.

### 3.1 Cost-Sensitive Threshold Optimization

**4 outcomes** of agent decision:

| Outcome | Cost |
|---|---|
| Auto-respond + correct | $0 (best) |
| Auto-respond + wrong | $$$ (customer harm + reputation) |
| Escalate + correct | $$ (human time wasted) |
| Escalate + wrong | $$ (human time + still wrong) |

**Threshold 优化**: 选 confidence threshold τ 使 **total cost** 最小:

```python
def total_cost(threshold, results, cost_matrix):
    cost = 0
    for r in results:
        if r.confidence > threshold:
            if r.correct: cost += cost_matrix['auto_correct']  # 0
            else: cost += cost_matrix['auto_wrong']           # 100
        else:
            if r.correct: cost += cost_matrix['esc_correct']  # 10
            else: cost += cost_matrix['esc_wrong']            # 30
    return cost

# Try different thresholds, pick min cost
best = min(
    [t for t in np.arange(0, 1, 0.05)],
    key=lambda t: total_cost(t, eval_results, cost_matrix)
)
```

### 3.2 Tiered Threshold (Not Just Binary)

**三 tier** 比 binary 更好:

| Confidence range | Action |
|---|---|
| > 0.85 | **Pattern A auto** (just respond) |
| 0.5 - 0.85 | **Pattern A + offer** (respond + "talk to human?") |
| < 0.5 | **Preempt** ("let me get a human for this") |

**好处**:

- 中等 confidence 不浪费 human (auto-respond) 但保险 (offer)
- Low confidence 不让 user 等失败 (preempt)

### 3.3 Per-Query-Type Threshold

不同 query type 风险不同, threshold 应不同:

| Query type | Auto threshold | Why |
|---|---|---|
| Account balance | 0.7 | Low risk, can recover |
| Refund processing | 0.95 + B confirm | High stakes |
| Account password reset | 0.95 + B confirm + 2FA | Identity-sensitive |
| Product info | 0.6 | Marketing, low harm if wrong |
| Medical advice | 1.0 (never auto) | Liability |
| Legal advice | 1.0 (never auto) | Liability |
| Personal data lookup | 0.95 + B confirm | Privacy |

**Implementation**:

```python
THRESHOLDS = {
    'balance_inquiry': 0.7,
    'refund_request': 0.95,
    'password_reset': 0.95,
    'product_info': 0.6,
    'medical': 1.0,  # always escalate
    'legal': 1.0,
}

def threshold_for(intent):
    return THRESHOLDS.get(intent, 0.85)  # default
```

### 3.4 Threshold A/B Testing

不是设了就完, 持续 A/B test:

```python
# A: threshold 0.85
# B: threshold 0.80 (more auto)
# Compare:
#   - False-escalation rate
#   - Missed-escalation rate
#   - Customer satisfaction
#   - Time to resolution
#   - Cost
```

每月 review, 调整 threshold 趋向最优.

---

## ⚙️ Problem 4: Smooth Handoff — No Re-Explain

**用户最讨厌的事**: 跟 agent 聊了 5 分钟, 转 human, human 问 "How can I help?", **从头说一遍**.

**优秀 handoff = 0 重复**.

### 4.1 What Human Sees on Takeover

**Bad** (常见):

```
[Human agent dashboard]
New conversation #4283 from user@example.com
Subject: General inquiry
```

Human 点进去, 看 transcript 5 分钟, 才知道问题.

**Good**:

```
[Human agent dashboard]
New escalation: #4283 from user@example.com

[Quick summary]
User asking for refund on order #ABC-12. Says product arrived damaged.
Sent photos. Agent verified order in system, photo metadata 
suggests legitimate. Agent confidence 0.4 — couldn't confirm 
damage extent, escalated.

[Agent's attempted response] (not yet sent)
"I see the damage. Let me process a refund of $X..."

[Agent flags]
- Photo verification: passed
- Order history: legitimate customer, 3rd order
- Refund amount: matches order
- Concern: damage extent unclear from photos

[Suggested action]
Approve refund, offer 10% discount on next order

[Quick actions]
[Approve agent draft] [Modify] [Investigate further] [Decline] [Take over conversation]

[User sentiment]
Frustrated (negative score: -0.6)

[Conversation context]
Last 10 messages (collapsed) [+]
Full transcript [+]
```

Human glances 30 seconds, makes decision, types brief reply. 5x faster.

### 4.2 Handoff Data Structure

```python
class EscalationContext:
    conversation_id: str
    user_id: str
    user_sentiment: float  # -1 to 1
    
    # Conversation
    full_transcript: List[Message]
    summary: str  # Agent-generated 1-paragraph summary
    
    # Agent's work
    agent_intent_classification: str  # 'refund_request'
    agent_attempted_response: Optional[str]
    agent_confidence: float
    agent_concerns: List[str]
    agent_actions_taken: List[Action]  # 已 executed
    agent_actions_pending: List[Action]  # draft, not executed
    
    # User context
    user_account_info: Dict
    user_history: List[Interaction]
    user_lifetime_value: float
    user_vip_status: bool
    
    # Suggested
    suggested_next_action: str
    suggested_response_template: str
    
    # Operational
    sla_target: datetime
    priority: int  # 1 (urgent) to 5 (low)
    queue_assigned: str
```

### 4.3 Human UI Components

```
┌────────────────────────────────────────────────────────────┐
│ Escalation #4283 — Pri 2 — SLA: 10 min                    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ [Summary]                                                  │
│ User refund request, damaged product. Agent 0.4 confidence │
│ — couldn't verify damage. 3rd-time customer, frustrated.   │
│                                                            │
│ [User sentiment]   ●●●●○ (Frustrated)                     │
│                                                            │
│ [Agent's draft response] (not sent)                        │
│ ┌───────────────────────────────────────────────────┐    │
│ │ "I see the damage. Let me process a refund..."   │    │
│ │ [Send as-is]  [Edit]  [Reject and respond fresh]│    │
│ └───────────────────────────────────────────────────┘    │
│                                                            │
│ [Suggested next action]                                    │
│ Approve refund $X. Offer 10% discount.                    │
│ [Apply suggestion]                                         │
│                                                            │
│ [Quick actions]                                            │
│ [Approve refund] [Investigate] [Decline] [Take over]      │
│                                                            │
│ [Full transcript] [+]                                      │
│ [Customer history] [+]                                     │
│ [Account info] [+]                                         │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 4.4 User Experience on Handoff

**Smooth**:

```
[Agent]: I'm connecting you with a specialist who can help with 
your refund request. They'll have all the context of our 
conversation — you won't need to repeat anything.

[5-second wait]

[Human Sarah]: Hi! I see you're asking about a refund on order 
#ABC-12 for a damaged product. I have your photos and details — 
let me get this resolved for you in just a moment.
```

**Bad** (avoid):

```
[Agent]: Let me transfer you.

[2-min wait]

[Human]: Hello! How can I help you today?
```

**Critical**: human 的第一句话**必须 reference 之前 context**, 证明 transfer 不 fake.

### 4.5 Bi-directional Handoff (Agent ← Human ← Agent)

Sometimes human deals with hard part, hands back:

```python
async def hand_back_to_agent(conv, human_summary):
    # Human writes 1-line summary of what was resolved
    # Agent picks up rest
    conv.add_human_note(human_summary)
    await agent.continue_conversation(conv)
```

例:

```
[Human Sarah]: I've approved the refund of $200. It'll arrive in 3-5 days.
              [Hands back to agent for follow-up]
[Agent]: Glad that's resolved! Is there anything else I can help with?
```

---

## ⚙️ Problem 5: Observability — Calibration, Override, False / Missed Escalation

**Without observability, 你不知道 agent 是好是坏**.

### 5.1 4 Critical Metrics

**Metric 1: Calibration plot**

```
横轴: confidence bucket (0.1, 0.2, ..., 0.9)
纵轴: actual accuracy in that bucket
Goal: y = x (diagonal)

例:
  0.9 bucket → 0.88 actual (close to 0.9 = good)
  0.7 bucket → 0.55 actual (overconfident at 0.7)
```

**Alert**: any bucket deviates > 10% from diagonal.

**Metric 2: Override rate (Pattern A → Human)**

```
% of agent's auto-responses that human-reviewer later marks as wrong
Or
% of agent's draft (Pattern B) that user edits before confirming
```

**Target**: < 10% for high-confidence (> 0.85), < 30% for mid (0.5-0.85)

**Alert**: trend up over week.

**Metric 3: False escalation rate**

```
% of escalations that human resolves trivially (e.g., < 30 sec)
= agent too conservative
```

**Target**: < 15%

**High false escalation** = agent's confidence too low, threshold too strict.

**Metric 4: Missed escalation rate**

```
% of auto-responses that turn out wrong (post-hoc review or customer complaint)
= agent too aggressive
```

**Target**: < 2%

**High missed escalation** = agent's confidence too high (overconfident).

### 5.2 Per-Type Breakdown

不要看总指标, 要 per-query-type:

```
Refund queries:
  Calibration: good
  Override: 8%
  False escalation: 12%
  Missed: 1%
  → 健康

Password reset:
  Calibration: drift (0.9 → 0.7 actual)
  Override: 25%
  False escalation: 5%
  Missed: 3%
  → 不健康, 紧急 recalibrate
```

### 5.3 Dashboard Design

```
┌──────────────────────────────────────────────────────┐
│ Agent Health Dashboard — Last 7 days                │
├──────────────────────────────────────────────────────┤
│                                                      │
│ [Calibration plot]                                   │
│ [chart showing confidence vs accuracy]              │
│                                                      │
│ [Top 5 query types by volume]                       │
│ - Refund (32%) — health: ✓                          │
│ - Balance (22%) — health: ✓                         │
│ - Password reset (10%) — health: ⚠ drift            │
│ - Order status (8%) — health: ✓                     │
│ - Cancellation (5%) — health: ✓                     │
│                                                      │
│ [Escalation rate over time]                          │
│ [time series showing % escalated]                   │
│                                                      │
│ [Override rate]                                      │
│ [time series]                                       │
│                                                      │
│ [Customer satisfaction by path]                      │
│ - Pattern A (auto): 4.3 / 5                         │
│ - Pattern B (confirm): 4.5 / 5                      │
│ - Pattern D (human): 4.7 / 5                        │
│                                                      │
│ [Recent alerts]                                      │
│ - Password reset calibration drift (2h ago)         │
│ - Override spike on refund (yesterday)              │
└──────────────────────────────────────────────────────┘
```

### 5.4 Iteration Loop

**Weekly review**:

1. Dashboard 看 last 7 days
2. 识别 worst-performing query type
3. Pull 50 examples (sample)
4. Manual review — what went wrong?
5. Fix: prompt iteration / RAG addition / threshold adjust
6. Deploy + monitor next week

**Quarterly**:

- Full re-calibration with new eval set
- Threshold A/B test
- Re-benchmark vs baseline

### 5.5 User Satisfaction by Path

不仅指标, 还要看 **CSAT 分 path**:

| Path | CSAT | NPS |
|---|---|---|
| Pattern A (auto) | 4.3 | 30 |
| Pattern B (confirm) | 4.5 | 40 |
| Pattern A + offer human | 4.4 | 35 |
| Pattern D (human) | 4.7 | 50 |
| Failed (no resolution) | 1.8 | -60 |

**洞察**: 
- Pattern A 满意度低于 D → 提升 agent 质量
- Failed path 拉低整体, 重点 fix

---

# Part 3 · 把 5 个问题串起来看

这 5 个 problem 是 **chatbot product design 的完整闭环**:

1. **4 patterns coexisting** = 整体架构
2. **Composite confidence calibration** = signal layer
3. **Threshold tuning** = decision layer
4. **Smooth handoff** = handoff layer
5. **Observability** = feedback loop

**FDE T4 面试场**, 这 5 个讲下来 + BNPL chatbot calibration story, 是 senior FDE 水准.

---

## 必问 clarifying questions

**1. Use case**

> "Customer support — chat / email / voice? Each has different UX patterns."

**2. Operating hours**

> "Human agents 24/7 or only daytime? Affects fallback design + off-hours queueing."

**3. Stakes**

> "Common queries (FAQ) or money/account changes? Different friction + threshold."

**4. Volume**

> "Queries / day, queries / second peak? Affects how many humans needed in backup."

**5. Customer demographic**

> "Tech-savvy or not? Affects how to communicate confidence / escalation."

**6. Brand voice**

> "Formal (bank) or casual (B2C)? Affects agent tone."

---

## 5 步框架 (sample 45-min answer)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify use case / hours / stakes / volume |
| 5-15 min | 4 interaction patterns overview |
| 15-25 min | Confidence calibration (5+ signals + Platt / isotonic) |
| 25-35 min | Escalation paths + state transfer (smooth handoff) |
| 35-45 min | Observability + iteration loop |

---

## 我会这样答 (sample 完整应答)

> "Clarify — *[假设: chat support 24/7, common = FAQ, some = account changes, 10K Q/day, mainstream consumer]*.
>
> **4 interaction patterns — must coexist in same product**:
>
> - **A. Confidence threshold escalation**: high confidence → auto, mid → offer human, low → preempt
> - **B. Confirm-required**: destructive action (refund, password, etc.) → draft + user confirm
> - **C. Scheduled review**: 5% of auto-actions sampled to human review post-hoc
> - **D. User-initiated takeover**: user says 'human' → immediate transfer, no friction
>
> Most products start A + B + D, add C after basic operations stable.
>
> **Confidence is the hard part**:
>
> Raw LLM log-prob is unreliable — overconfident. I'd build **composite from 5+ signals**: LLM log-prob, self-consistency (3 runs agree), citations (RAG-grounded), schema validation, OOD distance, query complexity, explicit-refusal detected.
>
> **Calibration with eval**: 500-1000 known-answer queries, plot confidence bucket vs accuracy, apply Platt or isotonic regression. Re-calibrate weekly on drift.
>
> **Threshold tuning**:
> - 0.85+ → auto
> - 0.5-0.85 → respond + offer human
> - < 0.5 → preempt to human
> Per-query-type thresholds (medical / legal → 1.0 = never auto, balance check → 0.7)
>
> **Smooth handoff** — human sees:
> - Conversation summary (agent-generated)
> - Agent's attempted response (draft, not sent)
> - Agent's concerns (where it's unsure)
> - Customer history + sentiment
> - Suggested next action
> - 1-click quick actions
>
> Critical: human's first line **references prior context** ('I see you're asking about refund on order #X...') to prove transfer is real.
>
> **Observability** — 4 metrics:
> - Calibration plot (confidence vs accuracy diagonal)
> - Override rate (agent wrong, human corrects)
> - False escalation (agent too conservative)
> - Missed escalation (agent too aggressive)
>
> Per-query-type dashboard. Weekly review + quarterly recalibration.
>
> **What I'd avoid**: single pattern, trust raw confidence, sudden escalation without context, gate the human path, no observability.
>
> **My resume anchor**: BNPL chatbot at TikTok PayLater. Initial agent was overconfident — 0.8 confidence = 65% actual accuracy. Built composite from 4 signals (log-prob + retrieval citations + OOD + refusal detection). Applied isotonic regression calibration. Threshold tiered (0.85 / 0.5). **After deployment**: false-escalation rate dropped 18% → 7%, missed-escalation dropped 5% → 2%. Tool selection accuracy in subsequent product went 70% → 92% by adding RAG-based discovery to compose more signals."

---

## 多场景变体 + 解法

### 变体 1: Coding agent (Cursor / Copilot)

前面 Section 5 场景 B 已展开. 关键: branch isolation, test gate, dev override.

### 变体 2: 医疗 triage

前面 Section 5 场景 C 已展开. 关键: 保守 default, red flag = D, nurse 永远可 override.

### 变体 3: Sales agent

前面 Section 5 场景 D 已展开. 关键: high-value signal → D, emotion → D.

### 变体 4: 内部 IT helpdesk

类似 customer support 但内部用户:
- L1 (密码 / Wi-Fi) — auto/self-serve
- L2/L3 (硬件 / 网络) — 人
- VIP user (CEO/VP) — 优先 + 人
- Repeat ticket (前次没解决) → 直人

### 变体 5: Trading agent

前面 Section 5 场景 E 已展开. 关键: per-trade dollar limit, kill switch, independent review.

---

## 简历专属 reframe

| 题点 | 你做过的具体动作 |
|---|---|
| Confidence threshold | BNPL chatbot — 4-signal composite + isotonic calibration |
| Confirm-required | Indonesia refund tier 2 — agent draft + ops 1-click approve |
| Scheduled review | Voice agent — weekly 5% sample 人工 review |
| User takeover | Voice agent — "speak to human" any time, no friction |
| State handoff | Voice agent escalation — transcript + agent prep + sentiment transferred to human |
| Calibration drift detection | Voice agent — weekly metric review of confidence buckets |
| Per-query-type threshold | BNPL chatbot — different thresholds for refund vs balance |

**主动 quote** (面试 30-sec):

> "BNPL chatbot at TikTok PayLater did exactly this. **Composite confidence** combined 4 signals: LLM log-prob, retrieval citations (must have for factual claim), OOD distance (novel query → low confidence), explicit refusal detection. **Threshold 0.85 for auto, 0.5-0.85 for 'agent + offer human', < 0.5 for preemptive escalate**. **Calibration eval**: 800 known-answer queries showed initial agent overconfident (0.8 confidence = 65% actual accuracy). Applied isotonic regression — re-calibrated. **After deployment**: false-escalation rate dropped 18% → 7%, missed-escalation dropped 5% → 2%. Then tool selection accuracy in subsequent product 70% → 92% after adding RAG-based discovery as another signal. **Iteration loop**: weekly dashboard review (calibration plot per query type), quarterly recalibration with fresh eval set."

---

## 5 follow-ups

**Q1**: "Calibration drifts as model / data shifts. How maintain?"

**A**:
- **Continuous eval**: 5% sampled, ground-truth labeled by human (Pattern C)
- **Weekly review**: recalibrate if any bucket drifts > 10%
- **Re-train calibrator** on recent 30-day data
- **Alert**: per-bucket accuracy drops below tolerance
- **Model version trigger**: any model change → mandatory recalibration before deploy
- **Prompt version trigger**: same as model

**Q2**: "User keeps trying to bypass agent ('I want human, you're useless'). Handle?"

**A**:
- **Respect user choice**: route to human immediately (Pattern D)
- **Don't gate the human path**: avoid making user prove they need human
- **Track**: high bypass-rate signals agent quality issue
- **Don't 'fight'**: 'OK, connecting you' beats 'let me try again'
- **Friendly message**: "I'll connect you with a specialist — they'll have the context."
- **Post-hoc analyze**: what query types have high bypass? Improve those

**Q3**: "Escalation queue is full, no human available. What happens?"

**A**:
- **Queue with ETA**: 'You're #4 in line, ~5 min wait'
- **Async option**: 'Want us to email you instead?'
- **Self-serve docs**: 'While you wait, here's our help center'
- **Off-hours**: 'No agents available, here's a callback form for tomorrow'
- **Never silently drop**: always communicate
- **Priority queue**: VIP / urgent / high-sentiment-loss → fast lane

**Q4**: "Human agent disagrees with what AI did. Surface to user?"

**A**:
- **No, internally only**: don't undermine AI trust in front of user
- **Log + train signal**: feed back to model improvement
- **If correction needed**: human takes over, fixes, doesn't blame agent verbally
- **Postmortem internally**: why didn't agent escalate? Calibration issue?
- **Customer messaging**: "I've looked into this and want to update the resolution..."

**Q5**: "Agent confidence high but wrong (hallucination). Detect?"

**A**: Hardest case. Defense layers:
- **Citation enforcement**: factual claim → must cite RAG source, agent's response validates
- **Fact-check second pass**: cheap LLM (Gemini Flash) verifies factual claims against KB
- **Anomaly detection**: response semantically very different from similar past queries → flag
- **Outcome telemetry**: did action have expected effect (refund went through? customer happy?)
- **User feedback loop**: thumbs up/down on response, corrections feed training
- **Pattern C sample review**: 5% caught here
- **Customer complaint route**: customer says "agent told me wrong" → instant investigation

---

## ❌ 易错点 (top 10)

1. **Single pattern** (only auto or only human)
2. **Trust raw LLM confidence** — overconfident, errors invisible
3. **Sudden escalation** — user re-explains everything
4. **No threshold tuning per query type** — one-size-fits-all
5. **No calibration eval** — confidence numbers don't mean correctness
6. **No takeover option** — user trapped with bad agent
7. **No observability** — escalation patterns invisible
8. **Gate the human path** — user frustration spikes
9. **No queue / off-hours fallback** — silent drop
10. **No false / missed escalation track** — can't iterate

---

## ✅ 加分项 (top 10)

1. **4 patterns coexist** explicitly
2. **Composite confidence** (5+ signals)
3. **Calibration eval + isotonic / Platt regression**
4. **Per-query-type threshold**
5. **Smooth handoff** with full state context
6. **Tiered threshold** (auto / offer / preempt)
7. **Off-hours / queue full handling**
8. **False / missed escalation observability**
9. **Per-path CSAT tracking**
10. **Quote BNPL calibration story + measurable improvement**

---

## 一句话总结

> **Human-Agent Interaction = "4 pattern coexist (auto + confirm + sample-review + user-takeover) + calibrated composite confidence + smooth handoff (no re-explain) + per-type observability + weekly iteration"**.
>
> 90% chatbot 失败不是 LLM 不行, 是**没设计 4 个 pattern 怎么 coexist, 没校准 confidence, handoff 不顺**.

---

## Cheat Sheet (印 1 页)

```
4 interaction patterns (coexist):
  A: Confidence threshold escalation
  B: Confirm-required for destructive
  C: Scheduled human review (post-hoc, 5% sample)
  D: User-initiated takeover (/human)

Order in handler:
  1. Pattern D first (explicit user intent)
  2. Pattern B (destructive action gate)
  3. Pattern A (confidence-based routing)
  4. Pattern C (5% sample to review queue)

Composite confidence signals (5+):
  1. LLM log-prob (continuous)
  2. Self-consistency (3 runs agree)
  3. Tool-grounding (citations present)
  4. Schema validation
  5. OOD detection (vector distance)
  6. Sentiment / complexity (long / multi-part)
  7. Explicit refusal detected (override → 0)

Calibration:
  Eval set of 500-1000 known-answer queries
  Plot confidence bucket vs % correct
  Apply Platt scaling (small data) or Isotonic regression (large)
  Recalibrate weekly / on drift
  Drift alert: any bucket > 10% off diagonal

Threshold tiers (default):
  > 0.85: auto-respond
  0.5-0.85: respond + offer human
  < 0.5: preempt escalate
  Per-query-type override:
    medical / legal: 1.0 (never auto)
    balance / read-only: 0.7
    refund / sensitive: 0.95 + B

Escalation handoff data:
  Conversation summary (agent-gen)
  Agent draft response (unsent)
  Agent confidence + concerns
  Customer history + sentiment
  Suggested next action
  Quick actions (1-click)
  SLA + priority

Human UI:
  Summary first (30-sec read)
  Quick actions visible
  Full transcript collapsed (expand on demand)
  Sentiment indicator
  Confidence score (transparent)
  Disagree path (training signal)

Smooth handoff UX:
  Agent: "I'm connecting you with a specialist who 
          has the context of our conversation."
  Human: "Hi! I see you're asking about [SPECIFIC] —
          let me get this resolved."
  Never: "How can I help you today?"

Off-hours / queue full:
  Queue with ETA
  Async option (email back)
  Self-serve docs
  Callback form
  Priority lane (VIP)
  Never silent drop

Observability (4 metrics):
  Calibration plot (per query type)
  Escalation rate
  Override rate
  False escalation (human resolves trivially)
  Missed escalation (low conf agent wrong)
  Per-path CSAT
  Time-to-resolution

User-initiated takeover:
  Don't gate (immediate)
  Respect choice
  Track bypass rate (agent quality signal)
  Don't fight ("Let me try again" = bad)

Anti-patterns:
  - Single pattern
  - Raw LLM confidence
  - Sudden escalation
  - No threshold tuning
  - No calibration
  - No takeover option
  - No observability
  - Gate human path
  - Silent drop on queue full

Resume hooks:
  - BNPL chatbot 4-signal composite + isotonic + measurable
  - Indonesia refund tier 2 confirm-required
  - Voice agent 7 markets escalation + transcript transfer
  - Per-type calibration drift detection
```

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 核心心智模型 (1 sentence)

Human-Agent Interaction = "4 pattern coexist (A confidence threshold + B confirm-required + C scheduled review + D user-takeover) + calibrated composite confidence (5+ signal + Platt/isotonic regression) + smooth handoff (agent prep visible, human first line refs context) + per-type observability (calibration plot, false/missed escalation, per-path CSAT) + weekly iteration", 90% chatbot 失败不是 LLM 不行而是 4 pattern coexist 没设计 / confidence 没校准 / handoff 不顺.

### 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| HAI | user × agent × human 三角交互 | 整体框架 |
| Pattern A | confidence threshold escalation (auto / offer / preempt) | 大部分 info query |
| Pattern B | confirm-required for destructive (refund / pwd reset) | irreversible action |
| Pattern C | scheduled human review (post-hoc 5% sample audit) | 持续 quality monitor |
| Pattern D | user-initiated takeover (/human, no friction) | 用户明确表达 |
| Composite confidence | 5+ signal 合成 (logprob + self-consist + citation + schema + OOD + complexity + refusal) | 不信 raw LLM logprob |
| Platt scaling | sigmoid logistic regression 校准, 数据少时用 | 500 sample 以下 |
| Isotonic regression | non-monotonic 校准, 数据多时用 | 500+ sample |
| Calibration drift | 任意 bucket > 10% off diagonal | 周 alert |
| False escalation | human resolves trivially (< 30 sec) | agent 太保守 |
| Missed escalation | auto-respond turn out wrong | agent 太激进 (overconfident) |
| Self-consistency | 同 query 跑 3 次答案一致 | composite signal 2 |
| OOD distance | embed query 找最近已 known query, 1-similarity | composite signal 5 |
| Tool grounding | response 引用 RAG retrieved doc | hallucination 防线 |
| Tiered threshold | > 0.85 auto / 0.5-0.85 offer / < 0.5 preempt | 不 binary |

### 5 个核心 framework / pattern

**Framework 1**: 4 pattern coexist (顺序 D > B > A > C)
- When: 每个 user message 进 handler
- Algorithm: 1) D 先检测 /human 明确意图 → escalate / 2) B 检测 destructive action → 起草 + confirm UI / 3) A composite confidence routing (auto / offer / preempt) / 4) C 5% sample to review queue
- Trade-off: 多 pattern coexist 复杂, 但单 pattern 必失败
- Tools: matches_human_request regex, ui.confirm out-of-band, schedule_review async queue

**Framework 2**: Composite confidence (5+ signal)
- When: agent 决定是否 auto-respond 前
- Algorithm: score = logprob_norm × (0.5 if !self_consistent) × (0.7 if !cited) × (0.5 if !schema) × (0.3-1 if OOD > 0.4) × (0.5-1 if complex) × (0 if refusal)
- Trade-off: 多 signal 慢, 但 raw logprob 不可信
- Tools: self-consistency 3-run / citation grounding / schema validation / vector OOD / regex refusal detect

**Framework 3**: Platt / Isotonic calibration with eval set
- When: 部署前 + 每周 drift check + model/prompt 升级时
- Algorithm: 500-1000 known-answer eval → plot confidence bucket vs accuracy → fit Platt (small data) or Isotonic (large) → re-deploy
- Trade-off: eval 数据贵, 但不校准 = confidence 没意义
- Tools: sklearn IsotonicRegression / LogisticRegression, weekly cron drift check

**Framework 4**: Tiered + per-query-type threshold
- When: routing decision
- Algorithm: > 0.85 auto / 0.5-0.85 respond + offer / < 0.5 preempt; per-type override (medical=1.0 never auto, balance=0.7, refund=0.95+B confirm)
- Trade-off: 三 tier 比 binary 复杂, 但中段 confidence 不浪费 human
- Tools: THRESHOLDS dict per intent, cost-sensitive optimization

**Framework 5**: Smooth handoff (no re-explain)
- When: agent → human takeover
- Algorithm: human dashboard 显 summary + draft + concerns + sentiment + history + 1-click actions; human 第一句必 reference 之前 context ("I see you're asking about refund on order #X...")
- Trade-off: 准备 dashboard 工程量, 但 20-min 变 2-min
- Tools: EscalationContext data structure, sentiment indicator, priority queue

### 关键决策树 (ASCII)

```
User msg → handler entry
   |
   v
matches_human_request? → YES → Pattern D escalate (no gate)
   |
   NO
   v
intent.requires_confirm? → YES → Pattern B (draft + confirm UI)
   |
   NO
   v
composite_confidence(query, response, agent_state)
   |
   ├─> 0.85 → Pattern A auto-respond
   |          └─> 5% sample → Pattern C review queue
   |
   ├─> 0.5-0.85 → Pattern A respond + offer "talk to human?"
   |
   └─> < 0.5 → Pattern A preempt "let me get a human"
```

```
Per-query-type threshold:
medical / legal → 1.0 (never auto)
account password reset → 0.95 + B confirm + 2FA
refund processing → 0.95 + B confirm
account balance → 0.7 (low risk, recoverable)
product info → 0.6 (marketing, low harm)
new / weird → A + D fallback
```

### Part 2 五个深度问题速查

**Problem 1: 4 pattern coexisting**
- 核心解法: 顺序 D > B > A > C 在 same handler, 不是选一个 必须四个 coexist
- Top 3 gotchas: D 别 gate ("let me try again" = bad UX) / B 大额必 type 'confirm' or 2FA / C 5% sample stratified per query type
- Tools: matches_human_request regex incl. 中文 "人工/转人工", confirm UI out-of-band

**Problem 2: Composite confidence calibration**
- 核心解法: 7 signal (logprob + self-consistency 3run + citation + schema + OOD + complexity + refusal); weights 用 eval set 跑
- Top 3 gotchas: raw LLM logprob 通常 overconfident (0.8 报为 60% 实际) / OOD distance 用 embedding nearest neighbor / refusal detected → override score 0
- Tools: sentence-transformers OOD, BPE token logprob, Pinecone vector OOD

**Problem 3: Threshold tuning + tiered response**
- 核心解法: cost-sensitive optimization (auto_correct 0 / auto_wrong 100 / esc_correct 10 / esc_wrong 30 → min cost), 三 tier > binary, per-query-type override
- Top 3 gotchas: 不同 query type 不同 threshold / monthly A/B test (0.85 vs 0.80) / vanity threshold "low p99" 不 reflect true cost
- Tools: per-intent THRESHOLDS dict, cost_matrix grid search

**Problem 4: Smooth handoff no re-explain**
- 核心解法: EscalationContext 包含 (conv summary / agent draft / concerns / sentiment / history / suggested action / quick actions / SLA); human 第一句必 ref context
- Top 3 gotchas: bad handoff "How can I help today?" = trust 崩 / good handoff "I see you're asking about refund on order #X" / bi-directional handback (human resolved → back to agent)
- Tools: priority queue, sentiment indicator, full transcript collapsed default

**Problem 5: Observability — 4 metrics**
- 核心解法: calibration plot (per-type) + override rate (< 10% high-conf, < 30% mid) + false escalation (< 15%) + missed escalation (< 2%); per-query-type breakdown + per-path CSAT
- Top 3 gotchas: aggregate 看不到 per-type drift / weekly review + quarterly recalibration / 不只指标看 CSAT path 分解
- Tools: dashboard 4 quadrant + per-type table, alerts on drift > 10%

### Production gotchas (top 15)

1. Single pattern (only auto or only human)
2. Trust raw LLM logprob (overconfident invisible)
3. Sudden escalation (user 重复 5 分钟 context)
4. No threshold tuning per query type
5. No calibration eval (confidence 数没意义)
6. No takeover option (user trapped)
7. No observability (escalation pattern invisible)
8. Gate the human path ("Let me try again, please")
9. No queue / off-hours handling (silent drop)
10. No false / missed escalation tracking
11. Auto-respond mindless confirm B (1-click 100% within 1s = fatigue)
12. Hallucination at high confidence (citation enforcement)
13. Model version change without recalibrate
14. Per-path CSAT 不看 (auto vs confirm vs human 差异)
15. Bypass rate 不 track (高 bypass = agent quality 信号)

### 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Composite confidence 4-signal | BNPL chatbot | logprob + citation + OOD + refusal 合成 |
| Isotonic calibration | BNPL chatbot | 800 eval, 0.8 conf → 65% 实际 → 校准后 80% |
| False / missed escalation drop | BNPL chatbot | false 18% → 7%, missed 5% → 2% |
| Tool selection accuracy gain | BNPL agent platform | 70% → 92% 加 RAG discovery signal |
| Pattern B confirm-required | Indonesia refund tier 2 | agent draft + ops 1-click 确认 |
| Pattern C scheduled review | Voice agent | weekly 5% sample 人工 review |
| Pattern D user takeover | Voice agent | "speak to human" any time no friction |
| Smooth handoff state transfer | Voice agent escalation | transcript + agent prep + sentiment 全 transfer |
| Per-type calibration drift | Voice agent 7 markets | weekly buckets review per market |

### 面试现场 quotables (top 8)

1. "4 patterns coexist in same product — A confidence threshold + B confirm-required for destructive + C scheduled human review + D user-initiated takeover. Most start A+B+D, add C after."
2. "Raw LLM logprob is unreliable — at 0.8 confidence we saw 65% actual accuracy. Composite from 5+ signals + isotonic regression."
3. "BNPL chatbot: false-escalation 18% → 7%, missed 5% → 2% after composite + isotonic."
4. "Human's first line must reference context: 'I see you're asking about refund on order #X' — never 'How can I help you today?'"
5. "Per-query-type threshold: medical/legal = 1.0 (never auto), balance = 0.7 (low risk), refund = 0.95 + B confirm."
6. "Tiered response not binary: > 0.85 auto, 0.5-0.85 respond + offer human, < 0.5 preempt."
7. "Don't gate the human path — 'Let me try again, please' is the worst UX. Respect user choice, track bypass rate as quality signal."
8. "Weekly dashboard per-query-type calibration plot. Quarterly recalibration with fresh eval set. Drift alert > 10% off diagonal."

### 红线 (top 10 anti-patterns)

1. Single pattern (only auto or only human)
2. Trust raw LLM logprob without calibration
3. Sudden escalation (user re-explains everything)
4. No threshold tuning per query type
5. No calibration eval (eval set < 500)
6. No takeover option (user trapped)
7. Gate the human path (friction = trust崩)
8. Silent drop on off-hours / queue full
9. No false/missed escalation tracking
10. Auto-respond at high conf without citation grounding (hallucination)

### Per-query-type threshold reference

| Query type | Auto threshold | Pattern | Why |
|---|---|---|---|
| Account balance / read-only | 0.7 | A | Low risk, recoverable |
| Order status lookup | 0.7 | A | Read-only |
| Product info / FAQ | 0.6 | A | Marketing, low harm |
| Refund < $X | 0.95 | A+B confirm | High stakes |
| Refund > $X | 1.0 | B+D | Human required |
| Password reset | 0.95 | B+2FA | Identity sensitive |
| Account delete | 1.0 | B+D | Irreversible |
| Personal data lookup | 0.95 | B confirm | Privacy |
| Subscription cancel | 0.85 | B (retention attempt) | Reversal pattern |
| Medical advice | 1.0 (never auto) | D | Liability |
| Legal advice | 1.0 (never auto) | D | Liability |
| Emotional / "I'm angry" | n/a | D | Human relationship |
| New / weird question | n/a | A + D fallback | Unknown territory |

### Composite confidence 7 signal weights (BNPL chatbot 真实)

| Signal | Weight | Implementation |
|---|---|---|
| LLM logprob (norm) | continuous multiplier | from OpenAI / Anthropic logprobs response |
| Self-consistency 3-run | × 0.5 if disagree | 3 parallel runs, canonical_form() compare |
| Tool grounding (citations) | × 0.7 if no citation | retrieved doc cite check |
| Schema validation | × 0.5 if invalid | JSON schema for structured |
| OOD distance | × max(0.3, 1-ood) if > 0.4 | embedding nearest-neighbor in known-good DB |
| Query complexity | × max(0.5, 1/complexity) if > 2.0 | word + clause + entity count |
| Explicit refusal | override → 0 | regex "I don't know" / "consult professional" |

### Calibration drift detection

| Bucket | Expected accuracy | Actual (drift example) | Action |
|---|---|---|---|
| 0.9 | ~ 0.88 | 0.65 | drift > 10% → recalibrate |
| 0.7 | ~ 0.7 | 0.55 | drift > 10% → recalibrate |
| 0.5 | ~ 0.5 | 0.48 | OK |
| 0.3 | ~ 0.3 | 0.32 | OK |

### Per-path CSAT tracking

| Path | CSAT | NPS | 启示 |
|---|---|---|---|
| Pattern A auto | 4.3 / 5 | 30 | 提升 agent 质量 |
| Pattern B confirm | 4.5 / 5 | 40 | 中等 |
| Pattern A + offer | 4.4 / 5 | 35 | 中段 conf OK |
| Pattern D human | 4.7 / 5 | 50 | 最高 (human win) |
| Failed (no resolution) | 1.8 / 5 | -60 | 主拉低, fix |

### Confirm UI design pattern

| Component | Example |
|---|---|
| Title | "Agent suggests: Refund $200 to card ending 4242" |
| Side effects list | ✓ Refund $200 USD ✓ Take 3-5 business days ✓ Send email confirmation |
| Detail toggle | Full args expandable |
| 1-click actions | [Confirm Refund] [Modify amount] [Cancel] |
| High-stakes friction | type 'CONFIRM' / 2FA for > $X |
| Time tracking | start → user confirm time (analytics) |

### Escalation handoff data structure

| Field | Type | Purpose |
|---|---|---|
| conversation_id | str | unique session |
| user_sentiment | float -1 to 1 | human knows tone before opening |
| full_transcript | List[Message] | Collapsed expand on demand |
| summary | str | agent-generated 1-paragraph |
| agent_intent_classification | str | "refund_request" |
| agent_attempted_response | str (unsent) | human sees draft |
| agent_confidence | float | transparent to human |
| agent_concerns | List[str] | flagged concerns |
| agent_actions_taken | List | already executed (e.g., verified order) |
| agent_actions_pending | List | drafts not executed |
| user_account_info | Dict | account context |
| user_history | List | past interactions |
| user_lifetime_value | float | VIP signal |
| user_vip_status | bool | priority queue flag |
| suggested_next_action | str | agent's recommended |
| suggested_response_template | str | starter for human reply |
| sla_target | datetime | response deadline |
| priority | int 1-5 | queue priority |
| queue_assigned | str | which team / agent |

### Phase rollout 4-stage

| Phase | Week | What | Advance |
|---|---|---|---|
| 1 | 1-2 | Pattern D + manual routing only | data collection ("typical query 长啥样") |
| 2 | 3-8 | Pattern A + B | threshold roughly tuned |
| 3 | 8-12 | Calibration + tuning | eval set + Platt/isotonic + per-type threshold |
| 4 | 12+ | Pattern C + observability | 5% sample review + dashboard + iteration |

