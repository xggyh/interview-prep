# 🔍 T3.4 · Observability for Agent System (Trace / Log / Metric / Quality) — 冲刺版

> 完整版: [gfde-t3-observability.html](gfde-t3-observability.html). 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: 10K QPS, PII present (must redact in logs), <1% observability cost budget, GCP Cloud Trace + Cloud Logging + OpenTelemetry available, LangSmith for LLM-specific, multi-tenant SaaS, SOC2 compliance."

**核心 framing**: 传统 web observability (RED method) 不够. LLM 有独特维度: TTFT/TPOT, token cost, prompt template version, model version, RAG corpus version, jailbreak attempts, hallucination. **4-layer stack**.

### Layer 1: Distributed Tracing (OpenTelemetry standard)

```
1 user request → N spans:
  http.request
    auth.verify
    rate_limit.check
    cache.lookup (miss)
    llm.query_rewrite       attr: llm.model, llm.input_tokens
    retrieval.vector_search attr: retrieval.docs_count
    llm.generation          attr: llm.cost_usd, llm.ttft_ms
    tool.send_email         attr: tool.duration_ms, tool.outcome
    audit.log
```

trace_id 全局唯一 + span_id 每段 + parent_span_id 父子关系. Export → Cloud Trace / Honeycomb / Tempo (hot 7d) + GCS cold 90d.

### Layer 2: LLM-specific Logging (PII-redacted)

```python
@trace_span("llm_call")
def llm_call(req):
    log.info({
        "trace_id": ...,
        "model": "gemini-3-pro",
        "prompt_template_version": "agent_v3.2",
        "prompt_hash": sha256(prompt),         # for grouping
        "input_tokens": resp.usage.input,
        "output_tokens": resp.usage.output,
        "cached_input_tokens": resp.usage.cached,
        "cost_usd": calc_cost(resp),
        "ttft_ms": ..., "total_ms": ...,
        "tools_used": [...],
        "prompt_redacted": presidio.redact(prompt),  # NOT raw
        "response_redacted": presidio.redact(resp),
    })
```

PII redact **at write time** (Microsoft Presidio / Cloud DLP), 不能 post-hoc. Hash for correlation (SHA-256 + per-type salt) → Right-to-be-Forgotten via hash deletion.

### Layer 3: Metrics (Prometheus + Cloud Monitoring)

Traditional latency/error + LLM-specific:

```
TTFT / TPOT p50 / p95 / p99       (per model, per tenant)
input_output_tokens (cached vs not, per tenant, per feature)
cost_per_tenant / cost_per_feature
cache_hit_rate (per tier L1/L2/L3/L4-prefix)
tool_call_success_rate / tool_latency_p99
eval_pass_rate (sampled 5%)
jailbreak_attempts_per_min
user_thumbs_ratio
```

### Layer 4: Quality monitoring (eval-in-prod)

```python
def sampled_eval(req, response):
    if random.random() > 0.05 and not flagged:
        return
    
    # LLM-as-judge (Sonnet 4.6)
    scores = {
        "faithfulness": llm_judge(req, resp, "faithfulness"),
        "relevance": ..., "tool_selection": ...,
        "safety": ..., "refusal": ..., "conciseness": ...,
    }
    eval_db.insert({...})
    
    if scores["faithfulness"] < 0.6:
        alert("low_faithfulness", req, resp)
```

5% random sample + 100% flagged (low thumbs / new prompt version / VIP tenant / jailbreak detected) → LLM-as-judge. Calibrate weekly vs human labelers 200-500 golden set.

### Edge cases

- **EC1 10K QPS, 100% trace 太贵**: **tail-based sampling** — 1% random + 100% errors + 100% slow (>5s) + 100% high-cost (>$0.5) + 100% VIP. OTel collector tail_sampling processor. 30x cost saving.
- **EC2 PII 写 raw log**: SOC2/GDPR fail. Presidio middleware on EVERY log call (NER spaCy + custom recognizer for account#/SSN). Apply at log-write time. Hash for correlation. RTBF via hash deletion.
- **EC3 Silent quality drop (metric 全绿)**: 传统 latency/error OK 但用户感受变差 = invisible. 必须 eval-in-prod 5% sample. Real case ID market 92% → 84% via slice analysis (by market/model/prompt/RAG), revert RAG 4h to recovery.
- **EC4 Cost spike unknown**: 7d trend by tenant → 某 tenant spike → by feature → identify expensive feature → by prompt → too-long context. Solution: per-feature cost guard alarm + 5x baseline detector.
- **EC5 Jailbreak detection**: pattern match (keywords "ignore previous", DAN, 中文 "忽略之前的指令") + LLM-classifier (Haiku $1/$5 cheap) + honeypot (inject fake secrets, detect leak) + response pattern ("I cannot" 异常增多) + user freq throttle (>10/min temp ban).

### Production hardening

- **Alert tiers**: P0 PagerDuty (p99>SLO 5min, error>2%, jailbreak>100/min, eval drop>5pp). P1 Slack ML (eval <90% 1h, cost trend up 50%, drift). P2 Email weekly review.
- **Drift detection daily**: MMD test on prompt embeddings, mean eval score baseline vs recent, cost mean baseline.
- **Per-tenant SLA dashboard**: availability + p99 + eval pass rate, synthetic probes 1/min, SLO error budget tracking, monthly auto-report.

### 🪝 Resume hook

"On TikTok Global Payment voice agent we built 4-layer observability: OTel for ASR → LLM → TTS → DB → CRM tracing. Structured log with prompt_template_version + model_version + RAG_corpus_version per call. Prometheus for TTFT/TPOT/cost/cache hit. LangSmith for LLM-specific trace inspection + 5% LLM-judge eval-in-prod. **Key win**: Indonesia market eval 92% → 84% in 1 week. Slice analysis (by market/model/prompt/RAG) pinpointed RAG corpus update as cause. Revert, back to 92% — **4 hour from alert to recovery**. Hard lesson: PII redaction must be at log-write time, not post-hoc — Presidio middleware on every log call. SOC2 audit passed."

---

## 🔥 5 Follow-ups

**Q1: 10K QPS × full span 太贵, cost 优化?**
**Tail-based sampling**: 1% baseline + 100% errors + 100% slow + 100% high-cost + 100% VIP + 100% jailbreak. Span aggregation (similar merged at storage). Retention tier: hot 7d full / warm 90d aggregated / cold 1y metric-only. Adaptive per-route (high-traffic low-value 0.1%, low-traffic high-value 100%). 30x reduction vs 100%.

**Q2: 用户报问题 can't reproduce, trace 里有啥能 debug?**
Full input + response (PII-redacted) sampled 10%. Model version + prompt template version + RAG corpus version. All tool calls in/out (full). LLM params (temp, top_p, seed). Conversation state at request time (Redis snapshot). **Re-run replay tool**: extract inputs → deterministic replay with mocked tool results. Compare to good case (diff inputs/outputs).

**Q3: Eval-in-prod - 谁定 ground truth?**
LLM-as-judge (Sonnet 4.6 / Opus 4.7) multi-dim score (helpfulness, accuracy, safety, etc.) calibrated weekly vs human eval set 200-500 examples gold standard. User signals (thumbs, copy, regenerate, follow-up correction). Heuristic checks (on-topic, no refusal markers, no hallucination markers). **Triangulation** = LLM judge + user signal + heuristic. Disagreement → human review.

**Q4: Jailbreak detection - log everything for security?**
**Inline detection**: pattern matching keywords + LLM-classifier on input → flag. **Logged**: full input separate secure store (not main logs), trace, user_id, severity. **Alerting**: >10 attempts/min temp ban / >50/day security review. **Forensics**: 7d hot 90d cold separate index (RTBF deletable). **Honeypot**: inject fake secrets, detect leak. **Pattern library**: maintain known jailbreak, update weekly.

**Q5: Cost observability - 怎么 attribute to features?**
**Tag each span feature_id** + tenant_id + user_id + model. **Cost per span**: input_tokens × input_price + output_tokens × output_price. **Per-feature dashboard**: sum by feature_id time-series. **Per-tenant report**: sum by tenant_id. **Daily report**: top 10 expensive features, week-over-week trend. **Use case**: identify expensive features for optimization / pricing decision / deprecation. 抓 100x token spike feature (your real case).

---

## ❌ 易错点 (10 条红线)

1. **Log raw PII** — SOC2/GDPR/CCPA 直接 fail
2. **No correlation between user report and trace** — debug 不可能
3. **100% sample everything** — cost blow up
4. **No LLM-specific eval** — quality drift invisible (灾难)
5. **No tool-level spans** — debug 卡在 LLM boundary
6. **Single-pillar (only logs)** — limited visibility
7. **No alerting** — wait for user complaint
8. **Trace context not propagated cross-service** — broken trace chain
9. **No version tracking** (prompt / model / RAG corpus) — "something changed" 不知 what
10. **No cost attribution by feature** — cost spike 找不到 root cause

---

## ✅ 加分项 (12 条)

1. **4 layers**: trace / log / metric / quality
2. **OpenTelemetry standard** (vendor-neutral 2026, GCP Cloud Trace compatible)
3. **LLM-specific signals** (TTFT/TPOT, token cost, eval, jailbreak)
4. **Smart sampling** (tail-based, errors + slow always)
5. **PII redaction pipeline** at write time (Presidio + Cloud DLP + hash)
6. **Eval-in-prod** with LLM-judge + calibration vs human
7. **Drift detection** (MMD test, eval drop alert)
8. **Cost attribution** by tenant + feature (per-span tag)
9. **Right-to-be-Forgotten** workflow (hash-based deletion)
10. **Replay tool** for deterministic debug
11. **Per-tenant SLA dashboard** with synthetic probes
12. **Quote voice agent Indonesia 4-hour debug story** (92→84% → revert RAG)

---

## 一句话总结

**LLM agent observability = 4 layers (OTel trace + LLM-specific log PII-redacted + Prometheus metric + quality eval-in-prod) + smart sampling (tail-based) + drift detection + debug workflow (trace_id → slice → re-run → root cause)**. 传统 web observability 不够 — LLM-specific signals (TTFT, token cost, prompt/model/RAG version, jailbreak, hallucination) 必须专门 instrument. 5% LLM-judge eval-in-prod 是 2026 LLM platform 标配, 不做就是盲飞.

---

## 🃏 Cheat Sheet (印 1 页随身)

```
4 observability layers:
  L1 Distributed Traces (OTel + GCP Cloud Trace / Honeycomb)
  L2 LLM-specific Logs  (prompt/resp PII-redacted, tokens, cost, version)
  L3 Metrics            (Prometheus / Mimir, latency/cost/error/cache)
  L4 Quality monitor    (LangSmith / Phoenix, eval-in-prod 5%, drift)

Span attributes (LLM-specific):
  llm.model / prompt_template_version / prompt_hash
  llm.input_tokens (+ cached) / output_tokens / cost_usd
  llm.ttft_ms / total_ms / finish_reason / refused
  tools.used / cache.prefix_hit_ratio
  quality.eval_score (async) / security.jailbreak_flag

Key LLM metrics:
  TTFT / TPOT p50/p95/p99
  In/out tokens (cached vs not), cost per (tenant,feature,model)
  Cache hit per tier / tool success rate
  Eval pass rate / jailbreak/min / thumbs ratio

Sampling 10K QPS (tail-based):
  1% random + 100% errors + 100% slow >5s
  + 100% high cost >$0.5 + 100% VIP + 100% jailbreak
  → 30x cost reduction vs 100%

PII redaction:
  Presidio (spaCy NER + custom) or Cloud DLP
  Apply at log-write time
  Entities: PERSON/EMAIL/PHONE/CC/SSN/LOCATION
  Hash sha256 + per-type salt for correlation, RTBF via deletion

Eval-in-prod:
  5% random + 100% flagged → LLM-judge (Sonnet 4.6)
  Multi-dim: helpful/accurate/tool/safety/refusal/concise
  Calibrate vs human weekly (200-500 golden), alert drop >5pp

Drift detect daily: MMD prompt embeddings + eval baseline + cost mean + tool error baseline

Alert tiers:
  P0 PagerDuty p99>SLO 5min, err>2%, jailbreak>100/min, eval drop>5pp
  P1 Slack ML  eval<90% 1h, cost up 50%, drift detected
  P2 Email week model mix shift, usage trend

Debug workflow: trace_id → trace top-down → identify failed span → compare good case → replay tool (deterministic mocks) → slice (tenant/model/template/time) → root cause

Tools 2026: OpenTelemetry + GCP Cloud Trace/Logging/Monitoring + Datadog/Honeycomb + LangSmith/Phoenix/Langfuse + Braintrust + Presidio/Cloud DLP

Cost attribution: per-span tag feature_id/tenant_id/model → per-feature dashboard + per-tenant report → catch 100x token spike feature

Per-tenant SLA: dashboard avail+p99+eval + synthetic probes 1/min + SLO error budget + monthly auto-report + credit policy

红线:
  - Raw PII in logs
  - 100% sample everything
  - No LLM eval (quality blind)
  - No tool spans
  - Single pillar
  - No alerting
  - Trace context not propagated
  - No version tracking
  - No cost attribution
  - No PII deletion workflow

Resume quotes:
  "Voice agent ID market 92→84% eval, 4h identify+fix via slice"
  "BNPL chatbot prompt_template_version + model_version + RAG_corpus_version tracking"
  "SOC2 audit passed via Presidio redact at write time"
  "Per-tenant SLA + synthetic probes 7 markets"
```
