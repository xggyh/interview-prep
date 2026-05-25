## Q41 · When fine-tune vs RAG vs prompt engineering (decision framework)

> "A customer comes to you and says they want to 'inject their domain knowledge into the model.' They've heard about fine-tuning and want a quote. **Walk me through your decision framework — when do you fine-tune, when do you RAG, when do you prompt-engineer, and when do you combine?** Be specific about cost, latency, freshness, and governance tradeoffs."

**Round**: AI Specialty (45 min)
**出处**: Exponent 2026 FDE Guide · 公司: OpenAI / Anthropic / Cohere / Scale AI / Databricks — 100% 必问的「分水岭」decision-framework 题

---

## 这道题在考什么

表面是 "选哪个 technique", 底下藏着 **8 个 FDE evaluation signal**:

1. **3 个技术 distinct 区分** — 一半 candidate 把 RAG 当 "FT lite", 把 FT 当 "facts injection", 立刻露马脚
2. **客户教育能力** — 客户来 ask FT, 你能不能 **正面拒绝** 并讲清为什么 RAG 更合适
3. **6 维 cost / latency / freshness / governance / quality / staffing tradeoff** — 不是只讲 accuracy
4. **Combinations** — production reality 是 hybrid, 不是 either-or
5. **When NOT to use each** — 同等重要的 negative space
6. **Knowing limits** — FT 不能可靠 inject facts, PE 受 context window 限, RAG 不能教 reasoning
7. **Pragmatic ordering** — "都用最好" vs "按 ROI 顺序加"
8. **2026 long-context era awareness** — Gemini 3 Pro 2M / Claude Opus 4.7 1M 改变了一些 RAG 边界

不考概念定义, 考「客户来跟你描述需求, 60 秒内你给一个 defensible recommendation」.

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|---|---|---|
| 1 | **Clarify 5 dimensions** | 3 min | 数据 freshness / 体量 / quality bar / latency / cost / governance | "Before I prescribe, let me ask 5 things — what's the freshness rate of this knowledge?" |
| 2 | **3-tech anatomy** | 5 min | 一句话讲清 PE / RAG / FT 改的是什么 | "Three completely different surgical instruments — PE changes input format, RAG injects context, FT changes weights." |
| 3 | **Anti-pattern callout** | 3 min | 「FT to inject facts」 是 top antipattern | "The most common mistake — and I want to flag it now — is using FT to inject facts. Let me show you why with math." |
| 4 | **6-dim decision matrix** | 8 min | 每维给 concrete threshold | "On freshness: static → PE or FT; daily-updated → RAG. On knowledge size: <5k tokens → PE; 5k-100M → RAG; 100M+ → tiered RAG." |
| 5 | **Cost math at scale** | 5 min | 2026 pricing 算 break-even | "At 100k qps/day, Opus 4.7 PE-only = $150k/month. FT'd Sonnet 4.6 = $45k. FT payback in <1 month." |
| 6 | **Hybrid patterns** | 8 min | 6 production combinations | "Most production systems are PE+RAG±FT in some mix. Let me walk through 6 patterns I've shipped." |
| 7 | **Pragmatic ordering** | 4 min | Week 1 → Week 2-3 → Month 2+ migration | "Always PE-only baseline first with eval set. Add RAG only when knowledge gap is visible. FT only after PE+RAG plateau AND volume justifies." |
| 8 | **Quote BNPL / voice agent** | 5 min | 三个 case study | "I've literally shipped all three. BNPL chatbot uses PE+RAG (no FT because FAQ updates weekly). Voice agent uses FT for tone consistency across 6 languages. ConvFinQA uses RAG+tool for multi-hop math." |
| 9 | **Long-context 2026 caveat** | 2 min | Gemini 3 Pro 2M 改变某些边界 | "One 2026 nuance — long-context models are eating part of RAG's lunch for static <500k corpora. We're testing hybrid long-context + RAG narrowing." |
| 10 | **Close with 'how I'd run it'** | 2 min | Customer-facing engagement plan | "If you hire me Monday, week 1 I build eval set + PE baseline. Week 2-3 RAG. We re-decide on FT at week 4 with data." |

---

## 详细回答

### Step 1: 三技术 anatomy — 60 秒讲清本质

**Prompt Engineering (PE)** — 改 input format. System prompt, few-shot, structured output schema, chain-of-thought. **不改 model weight, 不改 retrieval pipeline**.

```
Bad PE:    "Answer this question: {query}"
Good PE:   "You are TikTok PayLater customer service agent.
            Customer query: {query}
            Think step by step. First identify intent.
            Then check eligibility. Then respond.
            Output JSON: {intent, response, escalate}"
```

**RAG (Retrieval-Augmented Generation)** — 在 prompt 里动态注入 retrieved context. 让 LLM「带着资料答」.

```
User query → Embed → Vector DB search → Top-K chunks
            → Prompt = "Based on: {chunks}\n\nAnswer: {query}"
            → LLM generates with citations
```

**Fine-Tuning (FT)** — 改 model weights. 用 (input, expected_output) 对训, 让 model 学新行为 / 风格 / output schema. 2026 主流 3 种:

- **SFT (Supervised Fine-Tuning)**: Standard next-token prediction on labeled data
- **DPO (Direct Preference Optimization)**: 用 (chosen, rejected) 对学偏好, 不需要 reward model
- **RLHF / RL alignment**: Reward model + PPO, 复杂但 quality 最高

```
       PE          RAG           FT
       │            │             │
   Input prompt  Input prompt  Model weights
       │         + retrieved    permanently
       │           chunks       changed
       │            │             │
    Same model   Same model    New model
```

### Step 2: Anti-pattern — FT to inject facts (top mistake)

客户走进来 ask FT, 第一反应应该是 **"很可能你想要的是 RAG"**. 教育客户为什么:

**场景: 客户说 "把我们 5000 页产品手册 baked into the model"**

```
工程师 (wrong): "好, 我 fine-tune"

结果:
  Week 1-3: 训练 + $50k 成本
  Week 4:   Model deploy
  Week 4 后:
    - "退款期限 14 天" 被记成 "退款 7-21 天" (probabilistic memory)
    - Hallucinate 不存在的 policy clause
    - Product doc 更新 → 必须 re-train ($25k 每次)
    - 没有 citation → 合规审计过不去
    - General capability 下降 (catastrophic forgetting)
```

**正确**: RAG. 因为:
- Facts 是**离散的**, 不是 pattern. LLM 学 pattern 强, 学 facts 弱
- Knowledge updates → 改 vector DB 5 分钟; FT 要 re-train
- Citation 可追溯 (legal/financial/medical 合规需要)
- Cost: RAG 一次性 $1-5k vs FT 每次 $25k+

**反过来 RAG 不能做 FT 的事**:
- 教 model 多语言一致的 tone (e.g., 印尼客服 firm-but-polite)
- 教 model output schema 严格遵守
- Cost reduction at 100k+ qps (distill 大 model → 小 FT model)

### Step 3: 6-Dimension Decision Matrix

```
                    Dimension                    │ PE  │ RAG │ FT
─────────────────────────────────────────────────┼─────┼─────┼─────
1. Freshness                                      │     │     │
   Static (rarely changes)                        │ ✓✓  │ ✓   │ ✓✓
   Dynamic (daily / weekly updates)               │  -  │ ✓✓  │  ✗
   Real-time (minute-level)                       │  ✗  │ ✓✓  │  ✗

2. Knowledge size                                 │     │     │
   < 5k tokens                                    │ ✓✓  │  -  │ ✓
   5k - 100M tokens                               │  -  │ ✓✓  │  -
   100M+ tokens                                   │  ✗  │ ✓   │  -
   (with long-context Gemini 3 Pro 2M)            │  ✓  │  ✓  │  -

3. Customization need                             │     │     │
   Per-tenant private data                        │  -  │ ✓✓  │  ✗
   Per-team prompts                               │ ✓✓  │  ✓  │  -
   Per-company style / tone                       │  -  │  -  │ ✓✓
   Global shared                                  │ ✓✓  │ ✓✓  │ ✓✓

4. Quality bar                                    │     │     │
   < 80% acceptable                               │ ✓✓  │ ✓   │  -
   80-90%                                         │  ✓  │ ✓✓  │ ✓
   > 90%                                          │  -  │ ✓   │ ✓✓
   > 95% (regulated / safety-critical)            │  ✗  │  ✓  │ ✓✓+HITL

5. Latency budget                                 │     │     │
   < 100ms                                        │ ✓✓  │  -  │ ✓✓
   100-500ms                                      │ ✓✓  │ ✓   │ ✓✓
   500ms-2s                                       │ ✓✓  │ ✓✓  │ ✓✓
   > 2s OK                                        │ ✓✓  │ ✓✓  │ ✓✓

6. Cost budget per query                          │     │     │
   < $0.001/query                                 │ ✓ small model │ - │ ✓✓ small FT
   $0.001-0.01                                    │ ✓✓  │ ✓   │ ✓✓
   $0.01-0.10                                     │ ✓✓  │ ✓✓  │ ✓✓
   > $0.10 OK                                     │ ✓✓  │ ✓✓  │ ✓✓
```

**Reading the matrix**: Find your row in each dimension. The technique with **most ✓✓ and fewest ✗** is your default.

### Step 4: Cost math at scale (2026 pricing)

**2026 reference pricing** (per million tokens):

| Model | Input | Output |
|---|---|---|
| Gemini 3 Pro | $2 | $12 |
| Gemini Flash | $0.50 | $3 |
| Claude Opus 4.7 | $5 | $25 |
| Claude Sonnet 4.6 | $3 | $15 |
| Claude Haiku 4.5 | $1 | $5 |
| GPT-5.5 | $5 | $30 |
| GPT-5.4 Lite | $2.50 | $15 |

**Scenario**: BNPL chatbot — 100k queries/day, 500 input tokens + 200 output tokens average.

```python
def monthly_cost(model_name, input_price, output_price, qpd=100_000):
    daily_input_cost = qpd * 500 / 1_000_000 * input_price
    daily_output_cost = qpd * 200 / 1_000_000 * output_price
    return (daily_input_cost + daily_output_cost) * 30

# 不同 strategy 月成本
print(monthly_cost("Opus 4.7 PE", 5, 25))      # $22,500 + $15,000 = $37,500
print(monthly_cost("Opus 4.7 PE+RAG", 5, 25))  # +800 tokens retrieval context
                                                # daily = (1300 in × $5/M + 200 out × $25/M) × 100k
                                                # = $65 + $50 = $115/day = $3,450/month + retrieval infra
print(monthly_cost("Sonnet 4.6 FT", 3, 15))    # $4,500 + $9,000 = $13,500/month + amortized FT
print(monthly_cost("Haiku 4.5 FT", 1, 5))      # $1,500 + $3,000 = $4,500/month + amortized FT
```

**FT economic break-even**:

```
SFT setup cost: ~$25k one-time (10k examples × $1.5 labeling + $80 compute + $10k engineering)

Quality vs Opus 4.7 PE: 
  If Sonnet 4.6 FT ≈ Opus 4.7 PE on this task →  
  Save: $37,500 - $13,500 = $24,000/month
  Payback: $25,000 / $24,000 = 1.04 months ✓✓

If Haiku 4.5 FT ≈ Opus 4.7 PE (more aggressive, possible if narrow task) →
  Save: $37,500 - $4,500 = $33,000/month
  Payback: < 1 month
```

**Rule of thumb**:
- < 10k queries/day: stick with PE+RAG on Sonnet 4.6 / Gemini 3 Pro (FT payback > 6 months)
- 10k-50k qpd: FT economic if quality plateau
- > 50k qpd: FT almost always pays back in < 3 months
- > 100k qpd: cascade (Haiku 90% + Sonnet 9% + Opus 1%) wins on cost AND quality

### Step 5: 6 Hybrid patterns (production reality)

**Pattern A: PE + RAG (most common, ~60% of FDE engagements)**

```
Use case: 客服 / 助理类
PE: response format, tone, escalation logic
RAG: FAQ, customer-specific data, policy
No FT: knowledge is dynamic

query → PE intent classify → RAG retrieve → PE+RAG generate
```

Example: TikTok BNPL chatbot. PE 教 escalation, RAG 抓 customer FAQ. **No FT** because FAQ updates weekly.

**Pattern B: PE + FT (style + query, no retrieve)**

```
Use case: 风格 / 格式严格要求, knowledge 静态
FT: tone, multilingual style, output format
PE: per-query specifics (which language, escalation flag)
No RAG: no external knowledge needed

query → FT model (with PE constraints) → response
```

Example: Voice agent 6 语言 collection tone. FT 教 style consistency, PE 控制 per-call escalation logic.

**Pattern C: RAG + FT (reasoning + knowledge)**

```
Use case: 需要 reasoning pattern + knowledge
FT: learn multi-step financial reasoning pattern
RAG: 抓 current financial data
PE: minimal, structure

query → FT model (with RAG context) → tool call → response
```

Example: ConvFinQA agent — FT 在 financial multi-hop reasoning data (你做过的 9-variant ablation), RAG 抓 10-K filings, calculator tool 做 math.

**Pattern D: All 3 (enterprise)**

```
Use case: 复杂 enterprise agent
FT: company-specific tone + reasoning
RAG: per-tenant knowledge
PE: query-time customization + structured output

query → FT classifier (intent + routing)
     → RAG retrieve (tenant filter + ACL)
     → FT generator (with retrieved + PE constraints)
     → PE post-process (JSON validate, redact PII)
```

Example: TikTok BNPL chatbot full stack.

**Pattern E: Cascade (cheap → expensive)**

```
99% queries → small FT model + PE
0.9%        → medium model + RAG
0.1%        → big model + multi-step agent

Routing logic:
  If intent classifier returns 'simple_greeting' → Haiku 4.5 FT
  If intent 'factual_query' → Sonnet 4.6 + RAG
  If 'complex_multi_hop' → Opus 4.7 + agent
```

**Cost**: 10x cheaper than always using big model. Quality: 同等 (right tool per query).

**Pattern F: Long-context + RAG (2026 trend)**

```
Knowledge 100k-1M tokens, dynamic:
  Option A: Pure RAG → 50k chunks
  Option B: Long-context (Gemini 3 Pro 2M) → entire corpus in context
  Option C: RAG narrows + long-context digests (BEST)

Pattern C:
  RAG retrieves top-100 chunks (50k tokens)
  Feed all 50k into Gemini 3 Pro 2M
  Gemini reasons over full retrieved set
  Output with citations from RAG

Pros: 
  - Better than pure RAG (model sees more context)
  - Cheaper than full long-context (only relevant chunks)
  - Citation possible (RAG provides sources)
```

### Step 6: Pragmatic ordering (FDE deployment script)

```
Week 0 — Discovery:
  - 5-dim clarification with customer
  - Sample 50 real queries from their workload
  - Map data sources (size, freshness, ACL)

Week 1 — PE baseline:
  - Build 100-200 sample eval set (stratified)
  - PE only on base model (Sonnet 4.6 default)
  - Measure baseline score per slice
  - "PE-only baseline is 72% accuracy. RAG candidate."

Week 2 — RAG iteration:
  - Build vector index (Qdrant / Pinecone)
  - Hybrid retrieval (dense + BM25)
  - Add reranker (bge-reranker / Cohere)
  - Measure lift: 72% → 88%

Week 3-4 — Production deploy:
  - PE+RAG to canary 5% traffic
  - A/B with business metric
  - Auto-rollback if SLO breach

Month 2 — Evaluate FT need:
  Check 3 conditions:
    ☐ PE+RAG quality plateau? (can't improve via prompts)
    ☐ Volume > 50k qpd? (FT economic)
    ☐ Style consistency or latency demands it?
  
  If all 3 yes → start SFT data collection
  Otherwise → keep iterating PE+RAG

Month 3-4 — FT deploy (if applicable):
  - SFT on 5k+ examples
  - Hold-out test set (20%)
  - Compare to PE+RAG honestly
  - Only deploy if +3pp on held-out AND cost reduction confirmed

Month 5+ — Production tuning:
  - Cascade routing (cheap → expensive)
  - Continuous golden set refresh
  - DPO refresh quarterly
  - Drift detection + alerts
```

---

## 关键决策 / 框架

### Decision Tree (when customer walks in)

```
Customer: "Inject our domain knowledge into the model"
            │
            ▼
Q: How often does this knowledge change?
   │
   ├── Daily / weekly → RAG (FT will stale)
   │
   ├── Yearly / static
   │   │
   │   ▼
   │   Q: How big is it?
   │   ├── < 5k tokens → PE (put in system prompt)
   │   ├── 5k - 500k → RAG OR long-context (compare cost)
   │   └── > 500k → RAG
   │
   └── Real-time → RAG with hot reload

Customer: "We want consistent tone in 6 languages"
            │
            ▼
Q: Have PE attempts failed?
   │
   ├── Not yet → Try PE first (system prompt + few-shot examples per language)
   │
   ├── Yes, inconsistent across languages → FT (SFT or DPO)
   │   │
   │   ▼
   │   Q: Have labeled preference data?
   │   ├── Yes → DPO
   │   └── No → SFT first, then DPO on production data

Customer: "Cost is too high at scale"
            │
            ▼
Q: What's the volume?
   │
   ├── < 10k qpd → Cache + prompt caching (Anthropic / OpenAI 90% input save)
   ├── 10k-50k qpd → Cascade routing (Haiku for easy, Sonnet for hard)
   └── > 50k qpd → FT smaller model (Sonnet → Haiku FT, often 5-10x cheaper)
```

### When NOT to use each (negative space)

```
❌ Don't PE when:
  - Knowledge gap is obvious (PE will hallucinate)
  - Style consistency needed across 6+ languages (PE inconsistent)
  - Prompt > 5k tokens at 100k qpd (cost prohibitive)
  - Multi-step reasoning beyond CoT (need FT)

❌ Don't RAG when:
  - Task is pure reasoning (RAG won't help)
  - Latency < 100ms (RAG adds 30-200ms)
  - Corpus < 5k tokens (just put in PE)
  - Corpus noisy / low quality (RAG amplifies bad data)

❌ Don't FT when:
  - Knowledge changes frequently (re-train cost prohibitive)
  - Data < 1k examples (overfits)
  - Time-to-deploy < 2 weeks
  - Base model is good enough + PE works
  - No eval discipline (FT regression invisible)
```

---

## 完整代码 / 架构图

### Production-ready decision function

```python
from dataclasses import dataclass
from typing import Literal, Optional

@dataclass
class Criteria:
    knowledge_size_tokens: int
    freshness: Literal['static', 'weekly', 'daily', 'realtime']
    quality_bar: float  # 0-1
    latency_budget_ms: int
    cost_budget_per_query: float
    queries_per_day: int
    multi_tenant: bool
    style_critical: bool
    languages: int
    fits_in_long_context: bool  # < 1M tokens
    labeled_data_available: int  # FT examples
    time_to_deploy_weeks: int
    governance_strict: bool  # citation required

def recommend(c: Criteria) -> dict:
    techniques = []
    rationale = []
    
    # === RAG decision ===
    if c.knowledge_size_tokens > 5_000:
        if c.freshness in ('daily', 'realtime'):
            techniques.append('RAG')
            rationale.append(f"Knowledge {c.knowledge_size_tokens} tokens + {c.freshness} → RAG essential")
        elif c.knowledge_size_tokens > 500_000:
            techniques.append('RAG')
            rationale.append(f"Knowledge {c.knowledge_size_tokens} too large for context window")
        elif c.fits_in_long_context and c.queries_per_day < 10_000:
            techniques.append('Long-context (consider RAG hybrid)')
            rationale.append("Fits long-context, low volume — try LC first, RAG if cost issue")
        else:
            techniques.append('RAG')
            rationale.append("Default knowledge handling")
    
    # === PE always included as base ===
    techniques.insert(0, 'PE')
    rationale.append("PE is always foundational (system prompt + structure)")
    
    # === FT decision ===
    ft_score = 0
    ft_reasons = []
    
    if c.style_critical and c.languages >= 4:
        ft_score += 3
        ft_reasons.append("multilingual style consistency needs FT")
    
    if c.queries_per_day > 50_000 and c.cost_budget_per_query < 0.01:
        ft_score += 3
        ft_reasons.append(f"{c.queries_per_day} qpd at <$0.01/query needs FT for cost")
    
    if c.quality_bar > 0.9 and 'RAG' in techniques:
        ft_score += 1
        ft_reasons.append("high quality bar may need FT layer")
    
    if c.labeled_data_available < 1_000:
        ft_score -= 5
        ft_reasons.append(f"only {c.labeled_data_available} examples — FT will overfit")
    
    if c.time_to_deploy_weeks < 2:
        ft_score -= 5
        ft_reasons.append("FT needs 2+ weeks minimum")
    
    if c.freshness in ('daily', 'realtime'):
        ft_score -= 3
        ft_reasons.append("dynamic knowledge — FT will stale")
    
    if ft_score >= 3:
        techniques.append('FT')
        rationale.extend(ft_reasons)
    
    # === Hybrid pattern naming ===
    pattern = '+'.join(techniques)
    
    # === Cost estimate ===
    if c.queries_per_day > 50_000 and 'FT' in techniques:
        monthly_cost = c.queries_per_day * 30 * 0.005  # FT'd smaller model
        recommendation_type = "FT-cascade"
    elif 'RAG' in techniques:
        monthly_cost = c.queries_per_day * 30 * 0.03  # PE+RAG on Sonnet 4.6
        recommendation_type = "PE+RAG"
    else:
        monthly_cost = c.queries_per_day * 30 * 0.02  # PE only
        recommendation_type = "PE-only"
    
    return {
        'techniques': techniques,
        'pattern': pattern,
        'rationale': rationale,
        'estimated_monthly_cost_usd': monthly_cost,
        'recommendation_type': recommendation_type,
        'next_steps': generate_next_steps(techniques, c),
    }

def generate_next_steps(techniques, c):
    steps = []
    steps.append("Week 1: Build 200-sample eval set + PE baseline")
    if 'RAG' in techniques:
        steps.append("Week 2-3: Build hybrid retrieval (dense + BM25) + reranker")
        steps.append("Week 3: Measure RAG lift vs PE baseline")
    if 'FT' in techniques:
        steps.append("Week 4+: Collect 5k labeled examples")
        steps.append("Week 6+: SFT training + held-out test eval")
        steps.append("Week 8+: Deploy with cascade routing")
    steps.append("Always: per-slice metric + drift detection + golden set refresh")
    return steps

# Example: BNPL chatbot
bnpl = Criteria(
    knowledge_size_tokens=2_000_000,  # FAQ + policy docs
    freshness='weekly',
    quality_bar=0.92,
    latency_budget_ms=800,
    cost_budget_per_query=0.05,
    queries_per_day=100_000,
    multi_tenant=True,
    style_critical=True,
    languages=6,
    fits_in_long_context=False,
    labeled_data_available=15_000,
    time_to_deploy_weeks=12,
    governance_strict=True,
)

result = recommend(bnpl)
print(result)
# {'techniques': ['PE', 'RAG', 'FT'],
#  'pattern': 'PE+RAG+FT',
#  'rationale': [...],
#  'estimated_monthly_cost_usd': 15000,
#  'recommendation_type': 'FT-cascade'}
```

### Architecture diagram (full PE+RAG+FT system)

```
                         ┌─────────────────────────┐
                         │     User Query          │
                         │  (with tenant context)  │
                         └───────────┬─────────────┘
                                     │
                                     ▼
                         ┌─────────────────────────┐
                         │  Intent Classifier      │
                         │  (Haiku 4.5 FT'd)       │
                         │  PE: structured output  │
                         └──────┬──────────┬───────┘
                                │          │
                       simple   │          │   complex
                                ▼          ▼
                  ┌─────────────────┐    ┌─────────────────────┐
                  │  Cached Reply   │    │  RAG Pipeline       │
                  │  (no LLM call)  │    │  ┌───────────────┐  │
                  └─────────────────┘    │  │ Query rewrite │  │
                                         │  └───────┬───────┘  │
                                         │          ▼          │
                                         │  ┌───────────────┐  │
                                         │  │  Dense + BM25 │  │
                                         │  │   (Qdrant)    │  │
                                         │  └───────┬───────┘  │
                                         │          ▼          │
                                         │  ┌───────────────┐  │
                                         │  │  Reranker     │  │
                                         │  │  (cross-enc)  │  │
                                         │  └───────┬───────┘  │
                                         │          ▼          │
                                         │     Top-10 chunks   │
                                         └──────────┬──────────┘
                                                    │
                                                    ▼
                                    ┌─────────────────────────────┐
                                    │  Generator                  │
                                    │  Sonnet 4.6 FT'd            │
                                    │  PE: system prompt + CoT    │
                                    │  + retrieved chunks         │
                                    │  + tool call schema         │
                                    └─────────────┬───────────────┘
                                                  │
                          ┌───────────────────────┼───────────────────┐
                          │                       │                   │
                          ▼                       ▼                   ▼
                   ┌─────────────┐         ┌────────────┐      ┌──────────────┐
                   │  JSON parse │         │ Tool call  │      │ Citation     │
                   │  + redact   │         │ (calc/api) │      │ extractor    │
                   └──────┬──────┘         └─────┬──────┘      └──────┬───────┘
                          │                      │                    │
                          └──────────────────────┴────────────────────┘
                                                 │
                                                 ▼
                                    ┌─────────────────────────┐
                                    │  Output validation      │
                                    │  - Schema valid?        │
                                    │  - Citations present?   │
                                    │  - Confidence > thresh? │
                                    └────────┬───┬────────────┘
                                             │   │
                                  high conf  │   │  low conf
                                             ▼   ▼
                              ┌──────────────┐  ┌──────────────────┐
                              │  Return to   │  │  Escalate human  │
                              │  user        │  │  (with context)  │
                              └──────────────┘  └──────────────────┘
```

---

## Gao Xin 简历专属 reframe

### Case A: BNPL chatbot — PE + RAG (70 → 92%)

**为什么不 FT**: FAQ + policy docs 每周更新, FT 会立刻 stale. Re-train 每周 $25k 不经济.

**架构**:
- PE: structured prompt, intent → routing → response template
- RAG: Qdrant + hybrid retrieval + cross-encoder rerank
- No FT (考虑过, ruled out because freshness)

**Quantified**:
- Routing accuracy 70% → 92% (+22pp) — 主要 lift 来自 tool description 改进 (PE) + chunk strategy (RAG), 不是模型升级
- 月成本 ~$15k (Sonnet 4.6 + Qdrant) vs $37k all-Opus PE-only
- 4-signal composite confidence allowed escalation policy (PE + calibration)

### Case B: Voice agent multi-market (FT + PE, no RAG)

**为什么 FT**: 6 语言 (印尼 / 越南 / 泰国 / 菲律宾 / 巴西 / 墨西哥) 一致的 firm-but-polite collection tone. PE 试过 system prompt + few-shot, 印尼 OK 但越南 / 葡语 inconsistent.

**为什么不 RAG**: Tone 是 style, 不是 facts. Collection policy 每市场静态.

**架构**:
- FT: SFT on 30k human-curated multilingual examples + DPO on 5k preference pairs (real customer outcomes where one response led to repayment, other didn't)
- PE: per-call escalation logic, structured state machine

**Quantified**:
- +25% collection success rate (vs PE on base model)
- 6 markets 一致 tone, regulator audit pass
- Pakistan ASR cascade 部署 (separate from text agent)

### Case C: ConvFinQA — RAG + tool (no FT)

**为什么 RAG**: 10-K 数据 retrievable, 不需要 inject into weights.
**为什么不 FT**: Financial knowledge 季度变, FT 会 stale. Base model reasoning 加 CoT 已够.

**架构**:
- RAG: 10-K filings indexed, hybrid retrieval + table-aware chunker
- PE: chain-of-thought reasoning prompt, query decomposition
- Tool: calculator (LLM bad at arithmetic)
- 9-variant ablation including critic agent (4/358 useful flags, negative result honestly reported)

### Case D: Indonesia refund tier (PE + structured output, tiered automation)

**Why tiered**: Tier 1+2 (simple refunds) PE-only 70% coverage with 0 wrong. Tier 3 (complex disputes) 6 months later with extensive eval.
**Lesson**: Don't FT until you know which tier is automatable.

### Case E: TikTok PayLater intent routing (cascade)

**Cascade**:
- 90% queries (greeting, balance check) → Haiku 4.5 FT'd ($1/$5)
- 9% (factual FAQ) → Sonnet 4.6 + RAG ($3/$15)
- 1% (multi-hop reasoning) → Opus 4.7 + agent ($5/$25)

**Cost**: 10x cheaper than always-Opus 4.7. Quality: 同 or 更好 (right tool per query).

---

## 5 个 Follow-ups

**Q1**: "Customer insists they want fine-tuning. How do you handle it?"

**A**: 3-step pushback:
1. **Validate concern first**: "Help me understand — what specifically do you want to achieve that you think FT will give?"
2. **Show the math**: "If your knowledge updates monthly, FT means $25k re-train × 12 = $300k/year. RAG means $5k setup + $0 updates. We can match quality with PE+RAG in 3 weeks vs FT's 3 months."
3. **Offer compromise**: "Let me build PE+RAG in 4 weeks. If we don't hit 88% accuracy, we add FT layer. Either way you get something shipped fast."

If customer still insists despite math: **document the disagreement in writing**, explain you'll proceed but flag the risks (cost, freshness, citation loss). FDE 是 trusted advisor, not order-taker — but ultimately customer decides.

**Q2**: "When does fine-tuning make economic sense at 100k queries/day?"

**A**: Cost math (2026 pricing):
- Opus 4.7 PE-only ($5/$25 per M) → ~$0.05/query → **$150k/month**
- Sonnet 4.6 FT'd, 3x cheaper if quality match → $0.015/query → **$45k/month**
- FT setup ~$25k one-time + $30k engineering → **payback in 1 month at this volume**

**Rule of thumb**: > 50k queries/day, FT a smaller model often pays back in < 3 months. Plus: FT smaller model has **lower latency** (Sonnet vs Opus ~40% faster), so dual benefit. Plus prompt caching (Anthropic / OpenAI 5-min cache) gives 90% input cost reduction on repeated system prompts — sometimes that alone closes the gap without FT.

**Q3**: "Long-context models (Gemini 3 Pro 2M, Claude Opus 4.7 1M) — does this kill RAG?"

**A**: **Not yet, but RAG's use case narrows**:
- **Long-context wins** when: corpus < 1M tokens, **static**, no privacy issues, latency tolerant. E.g., "analyze this 200-page contract."
- **RAG wins** when: corpus huge / dynamic / multi-tenant / per-user / cost-sensitive.
  - Cost math: Gemini 3 Pro 2M context at $2/M input → $4/query naively. RAG retrieves 5k → $0.01/query. **400x cheaper**.
- **Hybrid pattern (most common 2026)**: RAG retrieves top-K chunks (50k tokens), feeds into long-context Claude Opus 4.7 → best precision (RAG narrows) + best reasoning (long context model). This is what we're testing for BNPL complex queries.

**Q4**: "Our fine-tuned model performs worse than base + prompt. Why?"

**A**: Common causes (in priority order):
1. **Overfitting** to small training set (< 1k examples) — usual culprit. Need 5k+ for stable SFT.
2. **Catastrophic forgetting** — model loses general capability. Mix in 20% general data during FT.
3. **Bad eval** — measured on training data, not held-out test. 20% hold-out is non-negotiable.
4. **Wrong base model** — FT'ing Haiku for complex reasoning when Sonnet base would be better.
5. **Format inconsistency** in training data — model confused.
6. **Wrong hyperparams** — learning rate too high (overfit) or too low (no adaptation).

**Fix**:
- Use **LoRA not full fine-tune** (1-3% params, less forgetting)
- **Mix new + general data** (prevent catastrophic forgetting)
- **Bigger eval set** with diverse examples
- **Compare to base + best PE** as honest baseline

**Q5**: "What if RAG isn't returning relevant docs?"

**A**: Multi-pronged debugging (cheap first):
1. **Chunking strategy**: try structure-aware (heading-based) vs fixed-size 512 — often the issue for PDFs / docs with structure
2. **Retrieval method**: pure dense → hybrid (BM25 catches IDs / entities like product names / SKUs)
3. **Reranker**: add cross-encoder rerank top-50 → 10 (+10-15pp recall typical)
4. **Query rewriting**: LLM rewrites user query before retrieve (handles ambiguous queries)
5. **HyDE**: have LLM hypothesize an answer, embed that, retrieve similar docs (effective for short / vague queries)
6. **Don't fine-tune** to fix retrieval — that's a separate problem
7. **Eval first**: build 100-query golden set, ablation each change, keep what helps

---

## ❌ 死路答法

1. **"Just fine-tune everything"** — top antipattern, hallucinate variations of facts
2. **"PE is enough for production"** — works for prototype, fails at scale on multilingual / domain-specific
3. **Treating PE/RAG/FT as 3 alternatives** — production is hybrid
4. **No cost math** — "FT is cheaper at scale" without numbers
5. **No mention of `when NOT to use`** — only positive case shows shallow thinking
6. **Skip eval baseline** — adding RAG without measuring "did it help?"
7. **No long-context awareness** — 2026 reality, Gemini 3 Pro 2M / Claude 1M
8. **Confuse RAG with semantic search** — RAG = retrieve + generate, search is half
9. **"Use whatever's hot"** — pick based on technology not problem
10. **No customer education stance** — just execute what customer asks, no pushback on bad ideas

---

## ✅ 加分项

1. **3×10 dimension comparison table** — concrete thresholds, not vibes
2. **Concrete cost math** ($150k/month → FT payback in 1 month)
3. **PE → RAG → FT pragmatic order** with eval gate
4. **6 combination patterns** with named examples (BNPL / voice agent / ConvFinQA)
5. **Anti-pattern: FT for facts** named explicitly
6. **Long-context awareness** + RAG+LC hybrid (2026 reality)
7. **HyDE / query rewriting / self-RAG** beyond basic RAG
8. **DPO vs SFT vs RLHF** distinction (not just "fine-tune")
9. **Cascade routing** for production cost (10x reduction without quality loss)
10. **Quote specific shipped projects** (BNPL 70→92%, voice agent 6 languages, ConvFinQA negative result)

---

## 一句话总结

> **PE / RAG / FT 不是选择题, 是组合题. 起点永远是 PE-only baseline + eval set. 加 RAG 当 knowledge gap visible. 加 FT 只当 style consistency OR cost-at-scale OR latency 明确 demand. Never FT to inject facts — RAG is the right tool.**

---

## Cheat Sheet

```
3-tech anatomy:
              PE            RAG          FT
  Changes:    input         input+ctx    weights
  Setup:      $0            $1-5k        $25-100k
  Per query:  $$$$          $$$$         $$
  Latency:    fast          +30-200ms    same
  Updates:    edit (min)    re-embed     re-train
  Best for:   reasoning     facts        style
  Worst for:  knowledge     reasoning    facts
  Compliance: easy          easy (cite)  hard

6 decision dimensions:
  1. Freshness (static→PE/FT, dynamic→RAG)
  2. Knowledge size (<5k→PE, 5k-100M→RAG, 100M+→tiered)
  3. Customization (per-tenant→RAG, per-team→PE, per-company style→FT)
  4. Quality bar (>90%→all 3, <80%→PE only)
  5. Latency (<100ms→PE+cache, >500ms OK→all)
  6. Cost (cheap→small+PE, expensive OK→all)

6 hybrid patterns:
  A. PE+RAG (most common — chatbot, BNPL)
  B. PE+FT (style+query — voice agent)
  C. RAG+FT (reasoning+facts — financial advisor)
  D. All 3 (enterprise — TikTok BNPL full)
  E. Cascade (cheap→expensive based on intent)
  F. Long-context+RAG (2026 — Gemini 3 Pro 2M)

Pragmatic order:
  Week 1: PE-only + eval set + baseline
  Week 2-3: + RAG (measure recall lift)
  Month 2+: + FT only if (PE+RAG plateau AND volume justifies AND data available)

Cost @ 100k queries/day (2026):
  PE only Opus 4.7: $150k/month
  + RAG: $180k/month
  FT Sonnet 4.6: $45k/month + $25k FT (payback < 1 month)
  Cascade (Haiku 90% + Sonnet 9% + Opus 1%): ~$25k/month

2026 long-context:
  Gemini 3 Pro: 2M context, $2/$12
  Claude Opus 4.7: 1M context, $5/$25
  Long-context wins: small static, latency tolerant
  RAG still wins: large dynamic, cost-sensitive, multi-tenant
  Hybrid (RAG + LC): best of both

Anti-patterns:
  - FT for facts (use RAG)
  - PE only when knowledge gap (add RAG)
  - FT on <1k examples (overfits)
  - FT to fix retrieval (separate problem)
  - Same model judges itself (bias)
  - Skip eval baseline

3 case studies:
  - BNPL chatbot: PE+RAG (FAQ weekly, no FT)
  - Voice agent: PE+FT (6 languages tone, no RAG)
  - ConvFinQA: RAG+tool (10-K data + calculator, no FT)

Quotes for interview:
  - "Start PE-only, add RAG when knowledge gap visible, FT when style/cost demands"
  - "Never FT to inject facts — RAG is the right tool"
  - "PE+RAG covers 80% of production AI use cases"
  - "FT economic at >50k qpd, payback often <3 months"
  - "Cascade routing 10x cost reduction without quality loss"
```
