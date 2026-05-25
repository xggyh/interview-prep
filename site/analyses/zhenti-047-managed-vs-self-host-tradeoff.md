## Q47 · Managed (API) vs Self-Host — the tradeoff

> "Your customer is debating between using a managed AI provider (OpenAI / Anthropic / Cohere API) versus self-hosting open-weight models (Llama / Mistral / Qwen on their own GPUs). **Walk me through the tradeoff** — cost, data residency, vendor lock-in, latency, ops burden, quality lag. When do you recommend hybrid? Show me the math."

**Round**: AI Specialty (45 min)
**出处**: Exponent 2026 FDE Guide · 公司: Cohere / Anthropic / OpenAI / Databricks — enterprise sales / FDE 必问

---

## 这道题在考什么

表面是 build vs buy 题, 底下藏着 **8 个 FDE evaluation signal**:

1. **Real cost math** — 不只是 "self-host cheaper at scale", 是 actual break-even calculation
2. **Total Cost of Ownership** — GPU + ops + observability + drift + on-call, not just compute
3. **Data residency / governance** — knowing why finance / health / gov sometimes can't use managed
4. **Vendor lock-in awareness** — API change, deprecation, pricing volatility
5. **Latency profile** — egress + cold start + queue depth
6. **Model quality lag** — open weights typically 6-12 months behind frontier
7. **Hybrid patterns** — embedding self-host + LLM API, or open for stable + API for cutting-edge
8. **2026 reality** — Llama 4, Qwen 3, Mistral Large 3 closing quality gap

不考「self-host vs API」, 考「客户问你, 你怎么 quote 一个 defensible recommendation」.

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|---|---|---|
| 1 | **Clarify 6 dimensions** | 4 min | Volume / cost budget / latency / quality / governance / team capacity | "Before recommending, 6 things — volume, cost cap, latency SLO, quality requirement, governance, team capacity for ops." |
| 2 | **Decision matrix** | 5 min | Per-dim recommendation | "Each dimension has a recommendation. Volume > 50k qpd: self-host on table. Latency < 100ms: depends." |
| 3 | **Cost math at scale** | 8 min | 2026 pricing, GPU hour, ops cost, break-even calculator | "Let me show the real math. Self-host break-even at 100k qpd is ~$60k/month savings vs API, but $200k+ in setup + ops year 1." |
| 4 | **TCO factors beyond compute** | 5 min | GPU + storage + bandwidth + ops + observability + drift + on-call | "Beyond compute: storage, bandwidth, ops engineer, observability stack, model updates, on-call burden — often 2-3x compute cost." |
| 5 | **Data residency + governance** | 4 min | HIPAA, SOX, GDPR, regional, BAA | "Governance often forces self-host: healthcare BAA limits, EU data residency, financial regulators, on-prem only contracts." |
| 6 | **Quality lag reality** | 4 min | Open weights ~6mo behind frontier | "Open weights lag 6-12 months. Llama 4 ~ GPT-4o Mini quality. Qwen 3 strong on multilingual. Frontier (Opus 4.7, GPT-5.5) still managed-only." |
| 7 | **5 hybrid patterns** | 5 min | Embedding self-host + LLM API, etc. | "5 hybrid patterns — most customers end up here. Embedding self-host + LLM API is most common." |
| 8 | **Vendor lock-in mitigation** | 3 min | Multi-vendor, abstraction layer, eval portability | "Lock-in defense — abstraction layer over providers (LiteLLM), eval set portable across vendors, multi-vendor canary." |
| 9 | **Quote ConvFinQA / voice agent infra** | 4 min | Your real experience | "I deployed voice agent on self-hosted vLLM (open weights). BNPL on managed (Claude Sonnet 4.6 API). ConvFinQA on managed (GPT). Tradeoffs were different per project." |
| 10 | **Recommend + roadmap** | 3 min | Customer-specific recommendation with phased plan | "Recommendation depends on your stage — Year 1: managed (fast to value). Year 2+: hybrid with self-host on stable workload." |

---

## 详细回答

### Step 1: 6 dimensions for decision

```
1. Volume (queries per day)
   < 1k qpd:       managed (no break-even)
   1k - 50k qpd:   managed (cost difference < $5k/month, not worth ops)
   50k - 500k qpd: hybrid (self-host for stable, API for cutting-edge)
   > 500k qpd:     self-host primary (savings > $100k/month)

2. Cost budget per query
   > $0.10/query OK:   managed (frontier models)
   $0.01-0.10/query:   managed or hybrid
   $0.001-0.01:        hybrid (cascade)
   < $0.001:           self-host (small open model)

3. Latency budget
   < 50ms first token:  self-host (no egress)
   50-200ms:            managed OK (with prompt caching)
   > 200ms OK:          either

4. Quality requirement
   Frontier needed (long-context, complex reasoning):  managed
     (Opus 4.7, Gemini 3 Pro 2M, GPT-5.5)
   Strong but not frontier (Llama 4 70B quality OK):  self-host viable
   Domain-specific (FT'd small model):                self-host typically

5. Governance / data residency
   HIPAA + BAA available:           managed OK (Anthropic / OpenAI offer)
   HIPAA + zero-retention required: managed possible (verify DPA)
   On-prem mandated:                self-host only
   Sovereign cloud (China, EU):     self-host typically
   Air-gapped:                      self-host only

6. Team capacity
   No ML ops expertise:    managed
   1-2 ML eng available:   managed primary, self-host limited workload
   ML platform team:       self-host viable
   Dedicated MLOps:        any
```

### Step 2: Decision matrix

```
                    Managed   Self-Host   Hybrid
                    (API)     (GPU)       (Mix)
─────────────────────────────────────────────────
Setup cost          $0        $50k-500k   $20k-100k
Time to first ship  Days      Weeks-months Weeks
Per-query cost      $$$$      $$ (at scale) Varies
Latency             100-500ms 30-200ms     Mix
Ops burden          None      High         Medium
Quality (frontier)  Best      6-12mo lag   Mix
Data residency      Vendor's  Yours        Yours+
Vendor lock-in      High      None         Medium
Compliance burden   Vendor handles much  You handle  Split
Drift / model ver   Vendor controls (sometimes painful)  You control  Mix
Multi-tenancy       Vendor   You build    Split
On-call             Vendor   You          Both
```

### Step 3: Cost math at scale (concrete 2026 numbers)

**Scenario**: customer needs 100k queries/day, 500 input tokens + 200 output tokens average.

**Option A: Managed API (Claude Sonnet 4.6, $3 in / $15 out)**

```python
daily_input = 100_000 * 500 / 1_000_000 * 3   # $150/day input
daily_output = 100_000 * 200 / 1_000_000 * 15 # $300/day output
daily_cost = 450
monthly_cost = 450 * 30  # $13,500/month
annual_cost = monthly_cost * 12  # $162,000/year

# Plus prompt caching (Anthropic 5-min cache, 90% input discount on repeats):
# Realistic 50% cache hit → 50% of input at 10% cost
# Effective: $150 * 0.5 * 1.0 + $150 * 0.5 * 0.1 = $82.5/day for input
# Total: $82.5 + $300 = $382.5/day = $11,475/month = $137,700/year
```

**Option B: Self-host Llama 4 70B on H100 (assumption: quality matches Sonnet 4.6 for this workload)**

```python
# GPU cost
# H100 80GB SXM @ $2.50/hr on-demand (cheaper reserved $1.50/hr)
# For 100k qpd serving Llama 70B with vLLM:
#   - Throughput: ~50 tok/s output at batch 16
#   - Per query: 200 tokens / 50 tok/s = 4 sec serving time
#   - Throughput per GPU: ~3600/hr per query at full util
#   - But 100k qpd / 24h = ~70 qps continuous → 7-8 H100 for headroom

gpus = 8
gpu_hour = 1.50  # reserved 1yr
daily_gpu = gpus * 24 * gpu_hour  # $288/day = $8,640/month

# Plus:
storage = 500  # /month (model weights + logs)
bandwidth = 200  # /month (egress to clients)
observability = 1000  # /month (Datadog, monitoring)
on_call = 5000  # /month (engineer time amortized)

monthly_self_host = 8640 + 500 + 200 + 1000 + 5000  # $15,340/month
annual = monthly_self_host * 12  # $184,080/year

# Plus setup year 1:
gpu_reservation = 8 * 12 * 1.50 * 24 * 30  # already in monthly
ops_engineer_setup = 100_000  # 1 eng × 6 months × $200k/year prorated
infra_setup = 20_000  # observability, networking, k8s, etc.

year_1_self_host = annual + ops_engineer_setup + infra_setup
# = $184k + $100k + $20k = $304k year 1
```

**Comparison**:

```
           Managed       Self-Host    Delta
Year 1:    $137,700     $304,080     Self-host +$166k
Year 2+:   $137,700     $184,080     Self-host +$46k

Break-even: Year 3+ favors self-host marginally
```

**At higher volume (1M qpd)**:

```python
managed_1m = 137_700 * 10  # $1,377,000/year (linear)

self_host_1m_compute = 8640 * 10  # but throughput economies of scale
# Actually need 60 GPUs for 1M qpd (not 80, vLLM batching)
self_host_1m_compute = 60 * 24 * 1.50 * 30  # $64,800/month
self_host_1m_annual = (64800 + 6700) * 12  # $858,000/year
# Plus year 1 setup ~$150k

# Year 1 delta:
delta_y1_1m = 1_377_000 - 1_008_000  # Managed +$370k year 1
# Year 2+ delta:
delta_y2_1m = 1_377_000 - 858_000   # Managed +$520k

# At 1M qpd, self-host pays back year 1 + saves $500k/year after
```

**Break-even formula**:

```python
def break_even_analysis(queries_per_day, managed_cost_per_query, self_host_compute, ops_cost):
    annual_managed = queries_per_day * 365 * managed_cost_per_query
    annual_self_host = self_host_compute * 365 + ops_cost
    
    year_1_setup = 150_000  # avg
    
    payback_months = year_1_setup / (annual_managed - annual_self_host) * 12 if annual_managed > annual_self_host else float('inf')
    
    return {
        'annual_managed': annual_managed,
        'annual_self_host': annual_self_host,
        'savings_per_year_steady_state': annual_managed - annual_self_host,
        'payback_months': payback_months,
        'recommendation': 'self-host' if payback_months < 24 else 'managed'
    }
```

**Quick rules of thumb (2026)**:

```
< 50k qpd:    managed (savings don't justify ops)
50k-200k qpd: hybrid (specific workloads self-host)
> 200k qpd:   self-host primary, managed for cutting-edge / overflow
> 1M qpd:     self-host with multi-region GPU
```

### Step 4: TCO factors beyond compute

```
Often forgotten in "self-host is cheaper" calculation:

1. Compute (GPU)
   - On-demand: $2-4/H100 hour
   - Reserved 1yr: $1-2/H100 hour  
   - Spot: $0.80-1.50/H100 hour (interruptible)
   - Reality: mix of reserved + on-demand for burst

2. Storage
   - Model weights (70B model: 140GB FP16, 70GB INT8): ~$30/mo per copy
   - Inference logs: ~$500/mo at 100k qpd
   - Backups: 2-3x

3. Bandwidth
   - Egress to clients: variable, $0.05-0.10/GB AWS
   - Inter-region replication: $$$$

4. Observability stack
   - Datadog / Grafana cloud: $500-2000/mo
   - APM (request tracing): $300-1000/mo
   - GPU metrics (DCGM): self-hosted free
   - Alerting (PagerDuty): $100-500/mo

5. Ops engineering
   - 1 ML platform engineer: $200-300k/year fully loaded
   - Setup phase (6 months): $100-150k
   - Steady state (1 FTE for production-grade): $50k/quarter

6. On-call burden
   - On-call rotation: 2-3 engineers minimum
   - Incident response: ~5 hours/week steady state
   - Compensation: $5-10k/month for on-call differential

7. Drift / retraining
   - Quarterly model update / fine-tune: $20k each
   - A/B test new versions: ongoing
   - Eval regression cost: ongoing

8. Compliance / certifications
   - SOC2 audit: $30-50k/year
   - HIPAA assessment: $20-40k
   - Penetration testing: $10-30k/year
   - Documentation: $20k initial + ongoing

9. Multi-region (if needed)
   - 2-3x compute cost (replicas)
   - Cross-region sync infra

Total "hidden" TCO: often 2-3x raw compute cost
```

**Managed providers absorb most of this** — that's a real value, not just "lazy."

### Step 5: Data residency + governance

**When managed is impossible**:

```
1. On-prem mandated (gov / defense contracts)
   - Air-gapped, no cloud allowed
   - Self-host only

2. Sovereign cloud (China, India, UAE, Russia, EU strict)
   - Cross-border data prohibited
   - Self-host in compliant cloud (Alibaba Cloud China, Sovereign EU)
   - Some managed providers offer (Azure China, AWS GovCloud, but limited)

3. Air-gap (high-security)
   - No internet egress at all
   - Self-host only

4. Specific compliance with no BAA available
   - HIPAA: BAA available from Anthropic / OpenAI / AWS Bedrock — but verify
   - PCI: stricter, often self-host
   - FedRAMP High: limited managed options
```

**When managed works with care**:

```
HIPAA with BAA:
  - Anthropic offers BAA for Claude API
  - OpenAI offers BAA for Enterprise plans
  - AWS Bedrock HIPAA-eligible regions
  - Verify zero-retention (training opt-out)

GDPR / EU data:
  - Anthropic EU region (Frankfurt) for Claude
  - OpenAI Azure EU residency
  - DPA review with legal

SOC2:
  - All major providers have SOC2
  - Verify reports current

Multi-tenant SaaS:
  - Per-tenant key + audit log
  - Usually managed OK if BAA / DPA fits
```

**Customer-specific question** (FDE asks):

```
"Do you have any of:
  - Data residency restrictions (specific countries)?
  - Air-gapped requirement?
  - Compliance certifications mandated (HIPAA, SOX, FedRAMP)?
  - Contract clauses forbidding cloud / cross-border?

If yes → self-host or hybrid with self-host primary
If no  → managed is usually faster path"
```

### Step 6: Quality lag reality (2026)

```
Frontier models (managed only):
  - Claude Opus 4.7 ($5/$25)
  - GPT-5.5 ($5/$30)
  - Gemini 3 Pro ($2/$12) — 2M context

Strong tier (Strong managed + closing open):
  - Claude Sonnet 4.6 ($3/$15)
  - GPT-5.4 / GPT-5 Lite ($2.50/$15)
  - Gemini Flash ($0.50/$3)
  - Llama 4 70B (open) — approaches Sonnet 4.6 on many benchmarks
  - Qwen 3 (open) — strong on multilingual, Chinese
  - Mistral Large 3 (open with commercial)

Cheap tier:
  - Claude Haiku 4.5 ($1/$5)
  - GPT-5 Nano / 5.4 Lite
  - Llama 3.3 8B (open) — very cheap to host
  - Phi-4 / Gemma 3

Specialized:
  - Code: open weights catching up (Qwen-Coder, Llama 4 Code)
  - Vision: open closing (Llama 4 Vision)
  - Multilingual: Qwen / Llama 4 (some languages better than GPT)
```

**Quality lag**:
- Frontier (Opus 4.7, GPT-5.5): no open weights match yet (6-12 month lag typical)
- Strong tier: Llama 4 70B, Qwen 3 close gap with Sonnet 4.6 on most tasks
- Cheap tier: open weights matched or exceed managed for narrow tasks

**Reality**: for most enterprise use cases (chatbot, classification, RAG), open weights tier suffices. Frontier needed only for complex reasoning, long context, cutting-edge.

### Step 7: 5 Hybrid patterns (most production)

**Pattern A: Embedding self-host + LLM managed (most common)**

```
Customer embed text → in-house embedding model (BGE-M3 or open)
                   → in-house Qdrant / Pinecone (self-host)
                   → retrieve chunks
                   → Claude Sonnet 4.6 API for generation
                   
Why:
  - Embedding: lots of volume, simple model, easy to self-host
  - LLM: variable, complex, prefer managed quality
  - Cost: embedding is 80% of volume, 20% of cost when managed
  - Data: embeddings can leak training data, customer prefers self-host
```

**Pattern B: Open weights for stable workload + API for cutting-edge**

```
80% queries → Llama 4 70B (self-host) — FAQ, simple routing
20% queries → Claude Opus 4.7 (API) — complex reasoning, long context

Why:
  - Stable workload (FAQ) volume high, quality "good enough" sufficient
  - Cutting-edge volume low, quality needs frontier
  - Hybrid cost: 80% × self-host cost + 20% × managed cost = often 50% savings
```

**Pattern C: API for development, self-host for production**

```
Dev / staging: managed API (fast iteration, no GPU setup)
Production: self-host (cost + control)

Why:
  - Dev: experimentation needs frontier + speed
  - Prod: cost matters at scale, control matters
```

**Pattern D: Multi-vendor with abstraction layer**

```
Application → LiteLLM proxy → OpenAI / Anthropic / Self-host
                            ↓
                       Cost / latency routing

Why:
  - Avoid vendor lock-in
  - Cost arbitrage (cheapest provider for each request)
  - Resilience (failover if one vendor down)
```

**Pattern E: Self-host for sensitive data, API for non-sensitive**

```
Customer query classifier (cheap)
  ↓
  Is sensitive (PII / health / financial)?
    Yes → self-host (data stays in customer environment)
    No  → managed API (cheaper, faster, better quality)

Why:
  - Compliance allows sensitive subset only
  - Non-sensitive majority can use cheap managed
  - Hybrid cost: minority self-host + majority cheap managed
```

### Step 8: Vendor lock-in mitigation

```python
# LiteLLM as abstraction (2026 standard)

from litellm import completion

# Route to any provider with same API
response = completion(
    model="claude-sonnet-4-6",  # or "gpt-5.5", "ollama/llama4:70b", etc.
    messages=messages,
    fallbacks=[
        "claude-haiku-4-5",          # primary degrade
        "gemini-3-pro",              # secondary provider
        "ollama/llama4:70b",         # self-host fallback
    ],
    routing_strategy="cost-aware",  # or "latency-aware"
)

# Eval portability
async def cross_vendor_eval(eval_set, vendors):
    results = {}
    for vendor in vendors:
        vendor_scores = []
        for sample in eval_set:
            response = await get_completion(vendor, sample.query)
            score = await judge(sample, response)
            vendor_scores.append(score)
        results[vendor] = mean(vendor_scores)
    
    return results

# Run quarterly to detect vendor drift
results = cross_vendor_eval(
    eval_set,
    ['claude-opus-4-7', 'gpt-5.5', 'gemini-3-pro', 'llama-4-70b']
)
```

**Other lock-in defenses**:
- **Prompt portability**: avoid vendor-specific features (e.g., Anthropic's prompt caching syntax) — abstract
- **Schema portability**: use OpenAPI / JSON schema, not proprietary
- **Multi-vendor canary**: 95% one vendor, 5% second vendor — keeps both warm + comparative data
- **Annual eval refresh**: re-benchmark all vendors against eval set, switch if quality / cost shifts

### Step 9: Customer recommendation framework

```
"Based on your 6 dimensions, my recommendation is:"

Stage 1 (Year 1) — Managed primary
  - Faster time to value (days vs weeks)
  - Lower upfront commitment ($0 vs $200k)
  - Better quality on cutting-edge tasks
  - Easier to iterate / experiment

Stage 2 (Year 2, after PMF + scale clear) — Hybrid
  - Identify stable workloads (high volume, well-understood)
  - Self-host those on open weights
  - Keep managed for cutting-edge / variable workload
  - Build abstraction layer for vendor portability

Stage 3 (Year 3+, $1M+ annual spend) — Self-host primary
  - Self-host majority workload (60-80%)
  - Managed for frontier reasoning + spikes
  - Dedicated ML platform team
  - Multi-region GPU deployment

Inflection points:
  - $30k/month managed spend → start hybrid planning
  - $100k/month → self-host planning serious
  - $500k+/month → self-host primary
```

---

## 关键决策 / 框架

### Decision tree

```
Customer use case
   │
   ▼
Q1: Compliance / data residency constraints?
   │
   ├── On-prem / air-gap mandated → Self-host only
   ├── Specific country residency → Self-host or limited managed regions
   ├── HIPAA / SOC2 with BAA available → Managed OK with verification
   └── None → Continue

Q2: What volume per day?
   │
   ├── < 1k qpd → Managed
   ├── 1k - 50k qpd → Managed
   ├── 50k - 200k qpd → Hybrid (start managed, plan self-host)
   ├── 200k - 1M qpd → Self-host majority + managed for cutting-edge
   └── > 1M qpd → Self-host primary

Q3: What's the quality bar?
   │
   ├── Cutting-edge (complex reasoning, long context) → Managed (frontier)
   ├── Strong but not cutting-edge → Either (Llama 4 / Qwen 3 close gap)
   └── Narrow / specialized → Self-host (small model + FT)

Q4: Team capacity?
   │
   ├── No ML ops → Managed
   ├── 1-2 ML eng → Managed primary, self-host limited
   ├── ML platform team → Self-host viable
   └── Dedicated MLOps → Any
```

### Cost ranges (2026 reference)

```
Managed (per million tokens):
  Cheap (Haiku, Flash): $0.50-1 in / $3-5 out
  Mid (Sonnet, GPT-5.4): $2.50-3 in / $12-15 out  
  Frontier (Opus, GPT-5.5, Gemini 3 Pro): $2-5 in / $12-30 out

Self-host (per million tokens, amortized):
  Llama 4 70B on H100: ~$0.30 in / $0.30 out (compute only)
  Llama 4 13B on A100: ~$0.10 in / $0.10 out
  + Ops overhead: 50-100% on top
```

---

## 完整代码 / 架构图

### Full TCO calculator

```python
from dataclasses import dataclass

@dataclass
class WorkloadProfile:
    queries_per_day: int
    input_tokens_avg: int
    output_tokens_avg: int
    quality_tier: str  # 'frontier', 'strong', 'cheap'
    latency_p99_budget_ms: int
    data_residency: str  # 'none', 'us', 'eu', 'cn', 'on_prem'
    compliance: list[str]  # ['hipaa', 'sox', 'gdpr', 'pci']
    team_ops_capacity: int  # FTE
    expected_duration_years: int

@dataclass
class CostEstimate:
    monthly_cost: float
    annual_cost: float
    year_1_total: float
    setup_cost: float
    
def estimate_managed(workload):
    """API cost estimate."""
    # Pick model based on quality tier
    if workload.quality_tier == 'frontier':
        in_price, out_price = 5, 25  # Opus 4.7
    elif workload.quality_tier == 'strong':
        in_price, out_price = 3, 15  # Sonnet 4.6
    else:
        in_price, out_price = 1, 5   # Haiku 4.5
    
    qpd = workload.queries_per_day
    
    # With 50% prompt cache hit rate (conservative)
    input_cost_daily = qpd * workload.input_tokens_avg / 1_000_000 * (
        in_price * 0.5 +          # cache miss
        in_price * 0.1 * 0.5      # cache hit (90% discount)
    )
    output_cost_daily = qpd * workload.output_tokens_avg / 1_000_000 * out_price
    
    monthly = (input_cost_daily + output_cost_daily) * 30
    
    return CostEstimate(
        monthly_cost=monthly,
        annual_cost=monthly * 12,
        year_1_total=monthly * 12,
        setup_cost=0,
    )

def estimate_self_host(workload):
    """Self-host cost estimate."""
    qpd = workload.queries_per_day
    
    # Required GPUs based on throughput
    # Assumption: H100 80GB serves ~70B model at 50 tok/s output
    output_tokens_per_day = qpd * workload.output_tokens_avg
    output_tokens_per_second_avg = output_tokens_per_day / 86400
    
    # Peak factor (3x average)
    peak_throughput_needed = output_tokens_per_second_avg * 3
    
    tokens_per_gpu_per_sec = 50  # Llama 4 70B on H100, batch 16
    gpus_needed = max(2, ceil(peak_throughput_needed / tokens_per_gpu_per_sec))
    
    # Cost components
    gpu_hour = 1.50  # H100 reserved 1yr
    daily_compute = gpus_needed * 24 * gpu_hour
    monthly_compute = daily_compute * 30
    
    # Ops overhead
    storage = 500  # /month
    bandwidth = max(100, qpd / 100)  # scaled
    observability = 1000
    on_call = 5000 if workload.team_ops_capacity < 2 else 2000
    
    monthly = monthly_compute + storage + bandwidth + observability + on_call
    
    # Year 1 setup
    if workload.team_ops_capacity < 1:
        setup_ops = 200_000  # need to hire
    else:
        setup_ops = 100_000  # existing team
    
    setup_infra = 30_000
    
    return CostEstimate(
        monthly_cost=monthly,
        annual_cost=monthly * 12,
        year_1_total=monthly * 12 + setup_ops + setup_infra,
        setup_cost=setup_ops + setup_infra,
    )

def recommend(workload):
    # Compliance check first
    if 'on_prem' in workload.data_residency or workload.data_residency == 'cn':
        return {
            'recommendation': 'self-host',
            'reason': 'data residency mandates self-host',
            'estimate': estimate_self_host(workload),
        }
    
    managed = estimate_managed(workload)
    self_host = estimate_self_host(workload)
    
    # Multi-year comparison
    managed_years = managed.annual_cost * workload.expected_duration_years
    self_host_years = self_host.year_1_total + self_host.annual_cost * (workload.expected_duration_years - 1)
    
    # Find break-even
    if self_host_years < managed_years:
        savings = managed_years - self_host_years
        payback_years = self_host.setup_cost / (managed.annual_cost - self_host.annual_cost)
        
        if payback_years < 2:
            return {
                'recommendation': 'self-host',
                'reason': f'Payback {payback_years:.1f} years, saves ${savings:,.0f} over {workload.expected_duration_years} years',
                'managed_estimate': managed,
                'self_host_estimate': self_host,
            }
        elif workload.queries_per_day > 50_000:
            return {
                'recommendation': 'hybrid',
                'reason': 'High volume but ops capacity limited — start managed, plan self-host',
                'phase_1': managed,
                'phase_2': self_host,
            }
    
    return {
        'recommendation': 'managed',
        'reason': 'Volume / capacity / quality favor managed',
        'estimate': managed,
    }

# Example
bnpl_workload = WorkloadProfile(
    queries_per_day=100_000,
    input_tokens_avg=500,
    output_tokens_avg=200,
    quality_tier='strong',
    latency_p99_budget_ms=800,
    data_residency='none',
    compliance=['pci'],
    team_ops_capacity=2,
    expected_duration_years=3,
)

print(recommend(bnpl_workload))
```

### Hybrid architecture diagram

```
                      ┌────────────────────────────────────┐
                      │       Customer Request             │
                      └────────────────┬───────────────────┘
                                       │
                                       ▼
                      ┌────────────────────────────────────┐
                      │   ROUTER / CLASSIFIER              │
                      │   - Intent classification          │
                      │   - Sensitivity scoring            │
                      │   - Cost-aware routing             │
                      └─┬──────────┬──────────┬────────────┘
                        │          │          │
            ┌───────────┘          │          └────────────┐
            │                      │                       │
            ▼                      ▼                       ▼
   ┌────────────────┐    ┌────────────────┐     ┌────────────────┐
   │   Cheap path    │    │  Standard path  │     │   Frontier path │
   │                 │    │                 │     │                 │
   │ Llama 4 13B     │    │ Llama 4 70B     │     │ Claude Opus 4.7 │
   │ (self-host)     │    │ (self-host)     │     │ (managed API)   │
   │                 │    │                 │     │                 │
   │ Greetings, FAQ  │    │ Standard chat   │     │ Complex reasoning│
   │ 70% volume      │    │ 25% volume      │     │ 5% volume       │
   └────────────────┘    └────────────────┘     └────────────────┘
            │                      │                       │
            └──────────────────────┴───────────────────────┘
                                   │
                                   ▼
                       ┌────────────────────────┐
                       │  Common Embedding /    │
                       │  Vector store          │
                       │  (BGE-M3 + Qdrant      │
                       │   self-host)           │
                       └────────────────────────┘
                                   │
                                   ▼
                       ┌────────────────────────┐
                       │  Unified Observability │
                       │  LiteLLM proxy + tracer│
                       │  (vendor-agnostic)     │
                       └────────────────────────┘
```

---

## Gao Xin 简历专属 reframe

### Voice agent — Self-hosted vLLM (sensitive data + cost at scale)

**S**: 7-market voice agent for debt collection. Multi-tenant (different financial regulators per market). High volume (~500k calls/day across markets).

**T**: Choose deployment model that handles volume + compliance + cost.

**A**: Self-hosted on vLLM + SGLang:
- Llama 4 70B (FT'd for collection tone) on H100 clusters
- Per-market deployment (compliance + data residency)
- SGLang for prefix caching (system prompt + market policies cached)
- Multi-region GPU (Indonesia / Vietnam / Thailand / Brazil regional)

**R**:
- $200k/month TCO vs estimated $1.2M/month if all managed (5-6x savings)
- 80ms p99 first-token latency (vs 200ms managed)
- Full compliance per market regulator
- Quality matched managed Claude Sonnet 4.6 after FT

### BNPL chatbot — Managed API (faster iteration + variable workload)

**S**: BNPL chatbot serving multi-product line. Variable workload (peaks during sales). Need fast iteration.

**T**: Choose deployment.

**A**: Managed (Claude Sonnet 4.6 API):
- Volume ~100k qpd, savings from self-host would be ~$15k/month, not worth ops burden
- Variable workload — managed auto-scales
- Fast iteration — change prompts, test new versions in hours
- BAA in place (financial use case)
- Prompt caching (Anthropic 5-min cache) gave 50% input cost reduction

**R**:
- $15k/month cost (managed) vs estimated $20k/month self-host (with ops overhead)
- Iteration cycle 2x faster vs maintaining self-host infra
- Quality: Sonnet 4.6 strong enough, no need for self-host's open weights

### ConvFinQA — Managed (research project, quality bar)

**S**: ConvFinQA research project. Multi-hop financial reasoning needs strong reasoning model. Volume modest (~1k qpd dev / eval).

**T**: Choose for research vs production.

**A**: Managed (GPT-5 / Sonnet 4.6):
- Research stage — needed best quality reasoning
- Low volume — no cost case for self-host
- Multiple models for ablation (GPT vs Claude vs Gemini)

**R**:
- Cheap experimentation
- 9-variant ablation across models possible

### Internal Agent Platform — Hybrid

**S**: 12 internal teams. Different use cases. Some sensitive data (HR, legal).

**T**: Platform that supports both.

**A**: Hybrid platform:
- Default managed (OpenAI / Anthropic via LiteLLM)
- Self-host option for sensitive teams (HR, legal) — Llama 4 deployed
- Per-team policy enforced at LiteLLM layer

**R**:
- 10 teams managed (cost OK, no compliance issue)
- 2 teams self-host (HR / legal sensitive data stays in-house)
- Unified observability + eval across both

---

## 5 个 Follow-ups

**Q1**: "Customer says 'I want to self-host for control.' Volume is 5k qpd. What do you say?"

**A**: Push back with math:
- At 5k qpd, managed (Sonnet 4.6) ~$700/month
- Self-host setup ~$200k year 1, then $10-15k/month ops
- **Self-host costs 5-10x more for first 2 years at this volume**
- Ask: "What 'control' specifically? Data privacy (managed has BAA), latency (managed 200ms OK), customization (managed FT exists), cost (data shows opposite)"
- If still insists after math: **document disagreement, proceed with their choice**, but flag the cost overrun risk in writing

**Q2**: "When does self-host quality match managed?"

**A**: Depends on use case:
- **Narrow / domain-specific tasks**: open weights + FT often matches Sonnet 4.6 quality (e.g., voice agent collection tone post-FT)
- **General chat / Q&A**: Llama 4 70B ~95% of Sonnet 4.6 on most benchmarks
- **Complex reasoning / long context**: frontier (Opus 4.7, Gemini 3 Pro) still has 10-20% lead
- **Specialized (code, math)**: gap closing fast (Qwen-Coder, Llama 4 Code)

**Reality**: for production use cases, often "good enough" is the right bar, not "best."

**Q3**: "Customer is in healthcare. Can they use managed API?"

**A**: Depends:
- **Yes if**: BAA in place with provider (Anthropic, OpenAI Enterprise, AWS Bedrock HIPAA-eligible)
- **Verify**: zero-retention (no training on customer data), audit log access, data residency (HIPAA-eligible regions)
- **No if**: contract / regulator forbids cloud, or specific data must stay on-prem (e.g., DEA controlled substance data, certain VA contracts)
- **Hybrid common**: PHI redaction at client + managed for cleaned queries

Bottom line: HIPAA-compliant managed is achievable, but requires legal review of DPA + BAA + zero-retention + audit access. Not "no" by default in 2026.

**Q4**: "Self-host but want to use the latest models. How?"

**A**:
- **Llama series**: Meta releases every ~6 months (Llama 3 2024, Llama 4 2025, etc.)
- **Qwen, Mistral, others**: monthly releases of variants
- **Fine-tune yours**: SFT / DPO on your data (small models 1-week cycle)
- **Watch frontier-open gap**: subscribe to benchmarks, switch when open matches your bar

Reality: open weights ~6 months behind frontier. If your task needs frontier (Opus 4.7), you'll always need API for top tier. Self-host the bulk on Llama 4, API the cutting-edge 5% (hybrid pattern B).

**Q5**: "How do you avoid vendor lock-in with managed?"

**A**: 4-layer defense:
1. **Abstraction layer** — LiteLLM, Helicone proxy. Single client API, swap providers.
2. **Eval portability** — eval set works across vendors. Re-benchmark quarterly.
3. **Prompt portability** — avoid vendor-specific features (Anthropic cache control, OpenAI function calling specifics). Abstract.
4. **Multi-vendor canary** — 95% primary, 5% secondary always live. Switch capacity if needed.
5. **Annual eval refresh** — re-test all candidates against your eval set. Switch if cost / quality shifts.
6. **Open weight backup plan** — even if managed primary, have self-host plan + tested fallback. Pakistan ASR outage taught us — single vendor = single point of failure.

---

## ❌ 死路答法

1. **"Self-host is always cheaper at scale"** — without TCO math
2. **Forget ops cost** — compute is only 30-50% of TCO
3. **No break-even calculation** — gut feel, not numbers
4. **No data residency consideration** — sometimes managed impossible
5. **"Managed is always faster to ship"** — true short-term, but self-host can be fast if infrastructure exists
6. **No hybrid mention** — production is rarely 100% one side
7. **Ignore quality lag** — open weights 6-12 months behind frontier
8. **No vendor lock-in mitigation** — abstraction layer is essential
9. **No phased recommendation** — Year 1 vs Year 3 different answers
10. **Ignore team capacity** — no ML platform team, self-host is fantasy

---

## ✅ 加分项

1. **6-dimension decision matrix** — volume / cost / latency / quality / governance / capacity
2. **Concrete cost math** with 2026 pricing — break-even, TCO
3. **TCO beyond compute** — storage, bandwidth, ops, observability, on-call, drift, compliance
4. **5 hybrid patterns** — most production is hybrid
5. **Data residency + compliance specifics** — HIPAA BAA, EU residency, on-prem
6. **Quality lag honest** — Llama 4 close, frontier still lag
7. **LiteLLM abstraction layer** for vendor portability
8. **Phased recommendation** — Year 1 managed, Year 2 hybrid, Year 3+ self-host primary
9. **Quote voice agent self-host + BNPL managed + Internal Platform hybrid**
10. **Inflection points** — $30k/mo, $100k/mo, $500k/mo trigger different decisions

---

## 一句话总结

> **Managed vs self-host is a multi-year TCO + governance question, not "which is cheaper." Year 1 favors managed (fast value, $0 setup). Year 3+ favors self-host at scale (volume > 200k qpd). Production reality is usually hybrid — embedding self-host + LLM managed, or open for stable + API for cutting-edge. Frontier quality (Opus 4.7, GPT-5.5) still managed-only in 2026. Vendor lock-in mitigated by abstraction layer (LiteLLM), eval portability, multi-vendor canary.**

---

## Cheat Sheet

```
6 decision dimensions:
  1. Volume (<1k → managed, >200k → self-host)
  2. Cost budget (cheap → small open, premium → frontier managed)
  3. Latency (<50ms first-token → self-host, >200ms → either)
  4. Quality bar (frontier → managed, strong → either, narrow → self-host)
  5. Governance (on-prem mandated → self-host only)
  6. Team capacity (no ML ops → managed)

2026 pricing (per million tokens):
  Cheap managed: $0.50-1 in / $3-5 out (Haiku, Flash)
  Mid managed: $2.50-3 in / $12-15 out (Sonnet, GPT-5.4)
  Frontier: $2-5 in / $12-30 out (Opus, GPT-5.5, Gemini 3 Pro)
  Self-host (amortized): $0.30 in/out (Llama 4 70B on H100)
  + Ops overhead: 50-100% on top of compute

Cost at 100k qpd:
  Managed (Sonnet 4.6): $13.5k/month, $162k/year
  + Prompt caching: $11.5k/month, $137k/year
  Self-host (Llama 4 70B): $15k/month + $150k setup year 1 = $304k year 1
  Year 2+: $184k/year
  Break-even: Year 3+ at this volume

Cost at 1M qpd:
  Managed: $1.4M/year
  Self-host: $1M year 1, $858k/year after
  Saves $500k+/year at scale

TCO factors (beyond compute):
  1. Compute (GPU): $1-4/H100-hour
  2. Storage: $500/mo
  3. Bandwidth: $100-500/mo
  4. Observability: $1k-2k/mo
  5. Ops engineer: $200-300k/year fully loaded
  6. On-call: $5-10k/mo
  7. Drift / retraining: $20k/quarter
  8. Compliance: SOC2 $30-50k/year, HIPAA $20-40k
  9. Multi-region: 2-3x compute

Total hidden TCO: often 2-3x raw compute

Data residency:
  On-prem / air-gap: self-host only
  HIPAA: managed OK with BAA (Anthropic, OpenAI, AWS Bedrock)
  EU GDPR: managed OK with EU residency (Anthropic Frankfurt, OpenAI Azure EU)
  China: self-host or managed CN (Aliyun)
  Sovereign cloud: usually self-host

Quality lag (2026):
  Frontier (managed only): Opus 4.7, GPT-5.5, Gemini 3 Pro 2M context
  Strong (open closing): Llama 4 70B ~ Sonnet 4.6 on most
  Cheap (open often beats): Llama 4 13B, Phi-4

5 hybrid patterns:
  A. Embedding self-host + LLM managed (most common)
  B. Open stable + API cutting-edge
  C. API dev + self-host prod
  D. Multi-vendor abstraction (LiteLLM)
  E. Self-host sensitive + managed non-sensitive

Vendor lock-in defense:
  - LiteLLM proxy (abstraction)
  - Eval portability across vendors
  - Avoid vendor-specific prompts
  - Multi-vendor canary (5% second vendor)
  - Quarterly re-benchmark

Phased recommendation:
  Year 1: Managed (fast value, $0 setup)
  Year 2 (after PMF, $30k/mo): Hybrid planning
  Year 3+ ($100k+/mo): Self-host primary
  $500k+/mo: Self-host + dedicated platform team

Inflection points:
  $30k/mo: hybrid planning starts
  $100k/mo: self-host serious
  $500k/mo: self-host primary
  $1M+/mo: dedicated platform team

Case studies:
  - Voice agent: self-host (sensitive + 500k qpd), $200k/mo vs $1.2M managed
  - BNPL: managed (100k qpd + variable + iteration speed)
  - ConvFinQA: managed (research + low volume)
  - Internal Platform: hybrid (10 managed + 2 self-host)

Anti-patterns:
  - "Self-host always cheaper" without TCO
  - Forget ops cost (50-100% on top)
  - No data residency check
  - No hybrid consideration
  - No phased plan
  - No vendor lock-in defense

Quotes for interview:
  - "TCO ≠ compute cost — ops is 50-100% on top"
  - "Year 1 managed, Year 2 hybrid, Year 3+ self-host primary"
  - "Embedding self-host + LLM managed is most common hybrid"
  - "Frontier quality (Opus 4.7) still managed-only in 2026"
  - "LiteLLM abstraction mitigates vendor lock-in"
  - "Self-host break-even depends on volume + ops capacity"
  - "Hybrid is the reality of most production deployments"
```
