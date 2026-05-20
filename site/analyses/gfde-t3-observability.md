## 题目

> "An LLM agent in production is **misbehaving** — sometimes wrong answer, sometimes slow, sometimes expensive. **You can't reproduce it locally**. Design the **observability stack** so you can debug + improve."

或追问形态:

> "Walk through the difference between observability for traditional web service vs LLM agent. What's new / different?"

**Round**: Production Observability (45 min)

---

## 这道题在考什么

考你**3 pillars + LLM-specific**:

1. **Traces** —— per-request end-to-end (multi-LLM-call, multi-tool)
2. **Logs** —— prompt + response 必 capture
3. **Metrics** —— latency, error rate, tokens, cost
4. **LLM-specific** —— eval-in-prod, quality drift, jailbreak attempts
5. **PII handling** —— logging compliance

---

## 必问 clarifying

**1. Volume**

> "QPS — affects sampling strategy."

**2. Compliance**

> "PII in prompts — can log full or redact?"

**3. Cost concern**

> "Log every request fully or sample?"

**4. Latency budget**

> "Observability adds overhead — acceptable?"

**5. Existing infra**

> "Datadog / Honeycomb / custom? Reuse?"

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify volume / compliance / cost |
| 5-15 min | 3 pillars (trace / log / metric) |
| 15-25 min | LLM-specific (eval / quality / cost) |
| 25-35 min | Sampling + PII redaction strategy |
| 35-45 min | Alerting + debug workflow |

---

## 我会这样答（sample）

> "Clarify — *[假设: 10K QPS, PII present (must redact in logs), 1% cost budget for observability, Datadog + OpenTelemetry available]*.
>
> **4-layer observability**:
>
> **Layer 1: Distributed Tracing** (per-request)
>
> ```
> User request (trace_id=xxx)
> ├── span: API gateway (10ms)
> ├── span: Agent loop start (parent)
> │   ├── span: LLM call #1 (300ms, 1.2K tokens, $0.003)
> │   ├── span: Tool call #1 (search_inventory, 150ms)
> │   │   ├── span: DB query (100ms)
> │   │   └── span: Cache lookup (5ms, hit)
> │   ├── span: LLM call #2 (250ms, 800 tokens, $0.002)
> │   └── span: Tool call #2 (send_email, 200ms)
> └── span: Response stream (50ms TTFT, 800ms total)
> ```
>
> Implementation: **OpenTelemetry** auto-instrument + manual spans for tool calls + LLM calls.
>
> Each span captures:
> - duration
> - status (ok / error)
> - inputs (token count, not content unless authorized)
> - outputs (token count, citations, tool name)
> - errors with stack trace
>
> **Critical**: trace context propagates to MCP servers / tools via headers.
>
> **Layer 2: LLM-specific Logging**
>
> ```python
> log_entry = {
>     'trace_id': trace.id,
>     'span_id': span.id,
>     'timestamp': now(),
>     'model': 'gpt-4o',
>     'prompt_template_version': 'v3.2',
>     'prompt_hash': hash(prompt),  # for grouping
>     'input_tokens': 1234,
>     'output_tokens': 256,
>     'cost': 0.0034,
>     'latency_ttft': 0.18,
>     'latency_total': 1.2,
>     'finish_reason': 'stop',
>     'tools_used': ['search_inventory', 'send_email'],
>     # PII-redacted content
>     'prompt_redacted': redact_pii(prompt),
>     'response_redacted': redact_pii(response),
>     # Quality signals
>     'user_thumbs': None,  # filled later
>     'eval_sampled': False,  # 5% sampled for eval
> }
> ```
>
> Storage tiered:
> - **Hot (last 7 days)**: queryable, sampled at 100%
> - **Warm (90 days)**: full PII-redacted, S3/BQ
> - **Cold**: aggregated only, indefinite
>
> **Layer 3: Metrics (time series)**
>
> | Metric | Why |
> |---|---|
> | latency p50/p95/p99 (TTFT + total) | UX |
> | token in/out per request | Cost + capacity |
> | cost per session | Economics |
> | error rate (by type) | Reliability |
> | tool call count per turn | Behavior |
> | cache hit rate (semantic + result) | Optimization |
> | eval pass rate (sampled) | Quality |
> | user thumbs ratio | Quality |
> | jailbreak attempt count | Security |
>
> **Layer 4: LLM-specific Quality Monitoring**
>
> Eval-in-prod:
>
> ```python
> async def with_eval(prompt, response):
>     if random.random() < 0.05:  # 5% sample
>         eval_score = await evaluator.judge(prompt, response)
>         metrics.record('eval.quality', eval_score, tags=[model, version])
>         if eval_score < threshold:
>             alert('quality drop')
> ```
>
> Drift detection:
>
> ```python
> # Compare current week's prompt distribution to baseline
> # Embedding-based: are new queries semantically novel?
> # If drift > threshold → alert
> ```
>
> **Sampling strategy** (10K QPS, cost concern):
>
> - **Traces**: 1% baseline, **100% for errors**, **100% for high-cost calls** ($ > $0.10)
> - **Logs**: 100% structured metric, 10% full prompt-redacted, 1% with prompt content (for debug)
> - **Eval samples**: 5% random, force-eval all flagged (jailbreak detection / low confidence)
>
> **PII redaction pipeline**:
>
> ```python
> def redact(text):
>     # Use presidio / AWS Macie
>     text = re.sub(r'\b[\d-]{13,19}\b', '[CARD]', text)  # Luhn-validate
>     text = re.sub(EMAIL_REGEX, '[EMAIL]', text)
>     text = re.sub(PHONE_REGEX, '[PHONE]', text)
>     # Named entity recognition for names
>     text = ner_redact(text, types=['PERSON'])
>     return text
> ```
>
> Apply at log-write time. Never store raw PII in logs.
>
> **Alerting strategy**:
>
> | Alert | Threshold | Action |
> |---|---|---|
> | p99 latency > SLO | for 5 min | Page oncall |
> | Error rate > 2% | for 5 min | Page oncall |
> | Cost per session > $1 | sustained 10 min | Email cost team |
> | Eval pass rate < 90% | over 1 hour | Slack ML team |
> | Jailbreak attempts > 100/min | for 5 min | Page security |
> | Tool error rate > 10% | for 5 min | Page platform |
>
> **Debug workflow for the misbehaving agent**:
>
> 1. **Reproduce by trace**: get trace_id from user report → full trace + logs
> 2. **Compare to good cases**: find similar trace where it worked → diff
> 3. **Re-run with same input**: capture prompt/response, eval scored
> 4. **Check eval suite**: did regression land in recent deploy?
> 5. **Slice analysis**: which user / tenant / model / tool / time-of-day?
> 6. **Root cause**: usually one of: (a) bad prompt template change, (b) tool API drift, (c) model version change, (d) edge case in user input
>
> **Tools (2026)**:
>
> | Tool | What |
> |---|---|
> | **OpenTelemetry** | Standard trace / log / metric collection |
> | **Datadog / Honeycomb** | Trace storage + query |
> | **LangSmith** | LLM-specific trace, eval-in-prod |
> | **Phoenix (Arize)** | OSS LLM observability |
> | **Helicone** | LLM proxy logging |
> | **Langfuse** | Full eval + observability |
> | **Braintrust** | Eval framework |
>
> **What NOT to do**:
> - Log raw PII (compliance violation)
> - 100% sample everything (cost blow)
> - No correlation between trace and LLM call
> - Skip eval-in-prod (quality drift invisible)
> - No tool-specific spans (root cause hidden)
> - No alerting (waiting for users to complain)"

---

## 简历专属 reframe

| 题 | 你做过 |
|---|---|
| Distributed tracing | Voice agent — multi-region debugging 必 trace |
| LLM-specific logs | BNPL chatbot — prompt versioning + token tracking |
| Eval-in-prod | ConvFinQA — eval methodology you've done at scale |
| PII redaction | Compliance for debt collection — log redaction必 |
| Alerting | Voice agent SLA weekly review |

**Quote**:

> "Voice agent had weekly metric review. We instrumented per-market: ASR latency p99, LLM token cost per call, TTS latency, **end-to-end p99 < 800ms** budget. Eval-in-prod sampled 5% of calls → LLM-judge evaluated for hallucination / refusal. When Indonesia market's eval pass rate dropped 8% one week, we traced to a model version rollout, **rolled back in 2 hours** because the alert + trace + diff workflow was set up. Without observability, that'd have taken days."

---

## 5 follow-ups

**Q1**: "Trace volume — 10K QPS × full spans = expensive. Cost optim?"
**A**:
- **Smart sampling**: 1% baseline + 100% errors + 100% slow (> p95)
- **Span aggregation**: similar spans (DB query type) merged at storage
- **Retention tiers**: hot 7d full, warm 90d aggregated, cold metric-only
- **Vendor: Honeycomb tail-based sampling** (sample whole trace if ANY span anomalous)

**Q2**: "Can't reproduce user-reported issue. What's in your trace that helps?"
**A**:
- Full input + full response (PII-redacted)
- Model version + prompt template version
- All tool calls with inputs/outputs
- LLM-specific: top_p / temp / seed if available
- Re-run script: extract inputs from trace → replay

**Q3**: "Eval-in-prod — who decides ground truth?"
**A**:
- **LLM-as-judge**: GPT-4 evaluates response vs expected qualities. Calibrated against human eval set.
- **Self-eval**: LLM rates its own response (unreliable but cheap)
- **User signals**: thumbs / engagement / follow-up corrections
- **Heuristic checks**: response is on-topic, no refusal, no hallucination markers
- **Human sample**: 100 random per week, manual review by ML team

**Q4**: "Jailbreak detection — log everything for security?"
**A**:
- **Inline detection**: pattern + LLM-classifier on input → flag
- **Logged**: full input (in secure store, not main logs), trace, user_id
- **Alerting**: > 100 attempts/min from same user → block
- **Forensics**: incident-response can pull all flagged + nearby

**Q5**: "Cost observability — how attribute to features?"
**A**:
- Tag each span with `feature_id` (which product feature triggered)
- Per-feature cost dashboard: sum of all spans tagged with feature
- Time-series: cost per feature per day
- Identify expensive features for optimization or pricing decisions

---

## ❌ 易错点

1. **Log raw PII** — compliance
2. **No correlation** between user report and trace
3. **100% sample** — cost blow
4. **No LLM-specific eval** — quality silent regression
5. **No tool-level spans** — debug stuck at LLM boundary
6. **Single-pillar** (only logs, no traces / metrics)
7. **No alerting** — wait for user complaint

---

## ✅ 加分项

1. **4 layers**: trace / log / metric / quality
2. **OpenTelemetry standard**
3. **LLM-specific signals** (TTFT, token cost, eval, jailbreak)
4. **Smart sampling** (errors + slow always)
5. **PII redaction pipeline**
6. **Eval-in-prod with LLM-judge**
7. **Cost attribution by feature**
8. **Quote voice agent Indonesia rollback story**

---

## Cheat Sheet

```
4 observability layers:
  L1 Distributed Traces (OTel)
  L2 LLM-specific Logs (prompt/response/version)
  L3 Metrics (latency/cost/error)
  L4 Quality monitoring (eval-in-prod)

Trace must capture:
  Agent loop (parent span)
  Each LLM call (model/tokens/cost)
  Each tool call (name/duration/error)
  Each DB / cache / external call
  Context propagation to MCP servers

LLM-specific log fields:
  trace_id, span_id, timestamp
  model, prompt_template_version
  prompt_hash (group)
  tokens in/out, cost
  TTFT, total latency
  finish_reason
  tools_used
  prompt_redacted, response_redacted
  user_thumbs, eval_sampled

Key metrics:
  latency p50/95/99 (TTFT + total)
  tokens / cost per request
  error rate by type
  tool call count
  cache hit rate
  eval pass rate (sampled)
  user thumbs ratio
  jailbreak attempts

Sampling strategy:
  Traces: 1% + 100% errors + 100% slow
  Logs: 100% metric, 10% redacted, 1% with content
  Eval: 5% random + 100% flagged

PII redaction:
  Apply at log-write time
  presidio / Macie
  Card / email / phone / NRIC / API key
  NER for names

Alerting rules:
  p99 latency > SLO 5 min → page
  Error rate > 2% 5 min → page
  Cost / session > $1 sustained → email
  Eval < 90% 1 hour → slack ML
  Jailbreak > 100/min → page security

Tools:
  OTel + Datadog / Honeycomb
  LangSmith / Phoenix / Helicone / Langfuse
  Braintrust for eval

Debug workflow:
  Reproduce by trace_id
  Diff vs good case
  Re-run with same input
  Check eval suite
  Slice analysis (user / tenant / model / time)
  Root cause: prompt / tool / model / input

Cost attribution:
  Tag spans with feature_id
  Per-feature dashboard

红线:
  - Raw PII in logs
  - 100% sample
  - No LLM eval
  - No tool spans
  - Single pillar
  - No alerting
```
