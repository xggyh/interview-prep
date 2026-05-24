## T3.4 · observability stack — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](gfde-t3-observability.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`gfde-t3-observability.html`](gfde-t3-observability.html)

---
## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"LLM agent in production misbehaving — sometimes wrong, slow, expensive. Can't reproduce locally. Design observability"**, 我按这 8 层回答, 不跳序.

### 📐 LLM Observability — 8 层结构

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 |
|---|---|---|---|---|
| 1 | 传统 obs 为什么不够 | 90s | RED method (Rate / Error / Duration) 只看 HTTP 5xx. LLM 失败是 **200 OK 但内容差** — dashboard 一片绿用户在骂. 这是 LLM-specific obs 的根本 motivation | "Traditional RED misses LLM's signature failure — 200 OK with bad content. Dashboard green, users complain..." |
| 2 | 4-layer 框架 | 1 min | L1 OTel distributed trace / L2 LLM-specific prompt+completion log (LangSmith) / L3 cost track per (user, feature, model) / L4 eval-in-prod LLM-judge. 每层独立工具 | "4 layers stacked — trace, LLM log, cost, eval. Each layer has dedicated tooling..." |
| 3 | L1 OTel trace 设计 | 2 min | span hierarchy: http.request → auth → rate_limit → cache.lookup → retrieve → llm.gen → tool.call×N → audit. 关键 attr: `llm.model`, `llm.input_tokens`, `llm.cost_usd`, `prompt_template_version`, `tenant.id` | "L1 is OpenTelemetry — span tree from HTTP all the way down. Critical attrs: model, tokens, cost, prompt_template_version..." |
| 4 | L2 LLM-specific tracing | 3 min | OTel 不够细 — 需要 prompt 全文 + completion 全文 + tool call chain. LangSmith / Phoenix / Langfuse / Helicone 选型. **PII redact via Presidio at write-time**, 不能事后 | "L2 — OTel 看不到 prompt 内容. LangSmith logs full prompt + completion, PII redacted via Presidio before write..." |
| 5 | L3 cost tracking | 2 min | Per (user, feature, model, day) Redis hincrby int(cost*10000). Per-tenant daily/monthly aggregate. Budget alert 80% / hard stop 100%. **用 provider response.usage 不是 estimate** (cached input 算错是常见 bug) | "L3 cost — per (user, feature, model, day) hash. Critical gotcha: 用 provider response.usage, 不是 token estimate..." |
| 6 | L4 eval-in-prod | 3 min | 5% sample LLM-as-judge (faithfulness / relevance / safety / completeness). Calibrate to human eval weekly 100 条. Drift: 7-day MMD test on eval scores. **不做 = prompt-by-vibes** | "L4 — sampled LLM-judge 5%, calibrated to weekly 100 human-eval. MMD drift test daily. 没这层 = prompt-by-vibes..." |
| 7 | Tail-based sampling | 2 min | 100% sample = TB/day. 策略: 1% baseline + **100% error + 100% slow (> p95) + 100% expensive (> $0.05) + 100% jailbreak attempt + 100% VIP user**. Honeycomb / Datadog / Tempo 都支持 | "Sampling — 1% baseline + 100% on 5 anomaly classes. Tail-based, Honeycomb supports natively..." |
| 8 | 简历 resume hook | 90s | "Voice agent 7 markets weekly review: per-market p99, error by ASR/TTS/LLM segment, eval score (CER, intent acc), 用户 hangup rate. LangSmith **catch Indonesia prompt faithfulness drop 12% after LLM 升级 — pre-rollback alert**" | "On voice agent 7 markets, LangSmith caught Indonesian prompt faithfulness drop 12% pre-rollback — saved a regression..." |

### 🎯 为啥按这个序

传统 obs 不够 是 framing — 强制面试官接受 "LLM 需要新一层". 4 层框架是骨架. L1 OTel 必须先讲 (基础设施层), 关键 attribute list 显示你做过. L2 LangSmith 是 LLM-specific, PII redact at write-time 是 SOC2 要点. L3 cost 是 FDE 死穴, "用 provider.usage 不是 estimate" 是只有踩过坑才知道的细节. L4 eval-in-prod 是 staff signal — "prompt-by-vibes" 这句是 quotable. Tail-based sampling 显示你懂 100% log 的 TB/day economic. 简历 hook 用 Indonesia prompt drop 12% 是 concrete win.

### 🔥 哪一层最容易被追问 deeper

**Layer 6 (eval-in-prod)** — 追问 "LLM-judge 怎么知道判断准?". 回答: weekly 抽 100 条人工 label → 算 LLM-judge agreement (Cohen's kappa > 0.6 acceptable), drift 时 re-prompt judge or 换 model. **Layer 4 (LangSmith)** 追问 "100K QPS 全 log prompt 哪里存得下". 回答: tail-based + PII redact + tier storage (hot 7 day → cold S3 90 day → glacier), 加 prompt content hash dedup. **Layer 3 (cost)** 追问 "cached input 怎么算". 回答: Anthropic / OpenAI / Google response 里都返回 cached_tokens, 单价 90% off (Anthropic) / 50% off (OpenAI) / 75% off (Google), 用 provider 返回值不自己估.

### ⏱ 时间压缩版 (30 min round)

1. 传统 obs 不够 (1 min) + 4 layer 框架 (30s)
2. L1 OTel + L2 LangSmith + L3 cost + L4 eval, 各 90s (6 min)
3. Tail-based sampling + PII redact (2 min)
4. 3 个 gotcha (cost dashboard wrong, eval drift, log explosion, 2 min)
5. 简历: Indonesia prompt drop 12% (90s)

### 🆘 卡壳兜底 (针对这题)

1. **被问 "为什么不只用 Datadog APM"**: Datadog 看 latency / error / RPS 强, 看不到 prompt 内容 + 没 LLM-as-judge eval + cost tracking 维度不够. 通常 Datadog + LangSmith 双 stack, OTel 作为桥
2. **被问 "Helicone 还是 LangSmith 还是 Phoenix"**: Helicone 是 drop-in proxy, 无 code change, 快速接入但能力浅; LangSmith 强在 eval + LangChain 生态; Phoenix 开源自部署 + RAG-specific 强; Langfuse 开源 + prompt mgmt
3. **被问 "PII redaction 用 LLM 不行吗"**: 可以但贵 + 慢 + 容易漏. 标准做法是 Presidio (regex + NER 混合, < 5ms per doc), LLM 只在边界 case (sensitive enough that miss = fine) 用作 fallback
4. **被问 "eval-in-prod 100% sample 行不行"**: 不行. LLM-judge 自己一次调用 $0.001-0.01, 100K QPS × 全 eval = $100K/day, 而且 judge model 自己 latency 加 1-2s. 5% sample + 100% error 重保是平衡

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖 4 layer / sampling / PII / eval-in-prod / debug runbook 全量.

### 🧠 核心心智模型 (1 sentence)

LLM observability = **4 layer (trace / LLM-log / metric / eval)** + **tail-based sampling** + **PII redact at write** + **per-tenant SLA**, 没有 eval-in-prod 就是 "prompt-by-vibes", silent quality drop 是 LLM 系统专属灾难.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| OTel | OpenTelemetry, vendor-neutral trace/log/metric SDK | 全 layer 基础 |
| Span | Trace 中一个 operation (start/end/attr/status) | 每 LLM call / tool call |
| traceparent header | W3C standard, agent → gateway → MCP server | trace propagation |
| Tail-based sampling | 决策在 trace 完成后 (基于 error / latency / cost) | 高 QPS 必装 |
| Head-based sampling | 决策在 trace 开始时 (random %) | 简单, 但漏 error |
| LLM-as-judge | 用 LLM (Sonnet) 评估其他 LLM 输出 | eval-in-prod |
| Presidio | Microsoft 开源 PII detection / redaction | 写日志前 |
| MMD test | Maximum Mean Discrepancy, distribution shift | drift detection |
| RED method | Rate / Errors / Duration (传统 web) | L3 metric 基线 |
| USE method | Utilization / Saturation / Errors (GPU) | LLM serving GPU |
| Synthetic probe | 定期 fake request 验证可用性 | per-tenant SLA |
| Right to be Forgotten | GDPR/CCPA 用户要求删数据 | hash-based delete |
| Calibration | LLM judge vs human eval correlation | weekly |
| Cost attribution | Per-(feature, tenant, model) 维度归因 | dashboard |
| Drift detection | 7-day baseline vs recent shift | daily auto |

### 🎯 4-Layer Observability 框架

**Layer 1: Distributed Tracing (OTel)**
- When: 任何 production LLM system
- Algorithm: span-per-operation + W3C traceparent + LLM-specific attributes
- Trade-off: 100% sample $$$$$ vs missing key events
- Tools: OpenTelemetry SDK, Honeycomb, Datadog, Tempo, Jaeger

**Layer 2: LLM-Specific Logging**
- When: prompt 是 product code
- Algorithm: structured log {prompt_hash, completion_hash, model, version, tokens, cost, eval_score}
- Trade-off: PII redact overhead vs raw debug visibility
- Tools: LangSmith, Phoenix, Helicone, Langfuse, W&B Weave, Presidio (PII)

**Layer 3: Metrics (RED + LLM-specific)**
- When: real-time dashboard + alerting
- Algorithm: Prometheus / Mimir for time-series, LLM-specific (TTFT, TPOT, token cost, cache hit, eval pass)
- Trade-off: cardinality 爆炸 (per-user metric) vs aggregation
- Tools: Prometheus, Mimir, Datadog, NVIDIA DCGM (GPU)

**Layer 4: Quality Monitoring (Eval-in-Prod)**
- When: prompt / model 升级 / drift detection
- Algorithm: 5% sample + force-flagged 100%, LLM judge multi-dim (helpfulness / accuracy / tool / safety / refusal / conciseness), calibrate weekly
- Trade-off: judge cost vs quality blind
- Tools: Braintrust, LangSmith eval, custom LLM-judge with Sonnet 4.6

### 🌳 关键决策树 (ASCII)

```
Sampling strategy at 10K QPS?
  ├─ All? ── No (TB/day cost prohibit)
  ├─ Random 1%? ── 漏 errors
  └─ Tail-based: 1% baseline + 100% errors + 100% slow + 100% expensive + 100% VIP ⭐
      → ~30x cost reduction vs all

PII in prompt?
  ├─ Detect via Presidio NER
  ├─ Redact entities: PERSON / EMAIL / PHONE / CREDIT_CARD / SSN / LOCATION
  ├─ Hash for correlation (sha256 + per-type salt)
  └─ Right-to-be-Forgotten: hash deletion via user_id

Eval-in-prod method?
  ├─ Manual sample review weekly ── 不够 scale
  ├─ User signal (thumbs-up) ── biased
  ├─ Pure LLM judge ── calibrate vs human
  └─ Hybrid: 5% LLM judge + 0.1% human + force-flag ⭐
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: 4-Layer Instrumentation — Trace + Log + Metric + Eval**

```python
# OTel span with LLM attrs
with tracer.start_as_current_span("llm_call") as span:
    span.set_attribute("llm.model", "claude-sonnet-4.6")
    span.set_attribute("llm.prompt_template_version", "v2.3")
    span.set_attribute("llm.prompt_hash", sha256(prompt)[:16])
    span.set_attribute("llm.input_tokens", resp.usage.input_tokens)
    span.set_attribute("llm.cached_input_tokens", resp.usage.cache_read_tokens)
    span.set_attribute("llm.output_tokens", resp.usage.output_tokens)
    span.set_attribute("llm.cost_usd", calc_cost(resp))
    span.set_attribute("llm.ttft_ms", ttft)
    span.set_attribute("llm.finish_reason", resp.stop_reason)
    span.set_attribute("tenant.id", req.tenant_id)
    span.set_attribute("feature.id", req.feature_id)
```
- Top 3 gotchas: (1) 漏 prompt_template_version → 改了 prompt 不知 (2) raw prompt 入 log (PII) (3) cost_usd 用 estimate 不用 response.usage (provider 算的)
- Tools: OpenTelemetry SDK Python/TS, LangSmith integration, semantic conventions

**Problem 2: Sampling Strategy at Scale — Tail-based**

```yaml
# OTel Collector tail sampling config
processors:
  tail_sampling:
    decision_wait: 30s
    policies:
      - name: errors
        type: status_code
        status_code: { status_codes: [ERROR] }
      - name: slow
        type: latency
        latency: { threshold_ms: 5000 }
      - name: expensive
        type: numeric_attribute
        numeric_attribute: { key: llm.cost_usd, min_value: 0.5 }
      - name: vip_tenant
        type: string_attribute
        string_attribute: { key: tenant.tier, values: [gold] }
      - name: jailbreak
        type: boolean_attribute
        boolean_attribute: { key: security.jailbreak_flag, value: true }
      - name: random_1pct
        type: probabilistic
        probabilistic: { sampling_percentage: 1.0 }
```
- Cost: ~30x reduction vs 100% sampling
- Top 3 gotchas: (1) decision_wait 太短 → 完整 trace 没到决策时丢 (2) VIP tenant 100% 漏定义 (3) head sampling alone 漏 errors
- Tools: OpenTelemetry Collector, Honeycomb tail sampler, Datadog APM

**Problem 3: PII Redaction Pipeline — Presidio, Hash for Correlation**

```python
# Presidio integration
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

def redact_for_log(text, user_id):
    analyzer_results = analyzer.analyze(
        text=text,
        entities=["PERSON", "EMAIL", "PHONE_NUMBER", "CREDIT_CARD", "SSN", "LOCATION"],
        language="en"
    )
    # Replace with hash for correlation
    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=analyzer_results,
        operators={"DEFAULT": OperatorConfig("hash", {"hash_type": "sha256"})}
    )
    return anonymized.text

# Right-to-be-Forgotten: hash by user_id + type
def gdpr_delete(user_id):
    user_hashes = compute_user_hashes(user_id, salt=PER_TYPE_SALT)
    log_db.delete(where=user_hashes)
```
- Top 3 gotchas: (1) redact at log-write time, not at read (太晚) (2) hash 无 salt → rainbow table risk (3) GDPR delete 不 cover backup
- Tools: Microsoft Presidio (spaCy NER + custom), AWS Macie, AWS Comprehend PII

**Problem 4: Eval-in-Prod — LLM-as-Judge, Drift Detection**

```python
def sampled_eval(req, response):
    # 5% random + 100% flagged
    if random.random() > 0.05 and not req.force_eval:
        return
    
    judge_prompt = f"""
    Query: {req.query}
    Response: {response.text}
    Rate 1-5 on: helpfulness, accuracy, tool_use, safety, refusal_appropriateness, conciseness
    """
    scores = llm_judge_sonnet.complete(judge_prompt)  # cheaper than Opus for judge
    
    eval_db.insert({
        "ts": now(),
        "req": redact(req),
        "resp_hash": sha256(response.text)[:16],
        "model": response.model,
        "scores": scores,
        "prompt_template_version": PROMPT_VERSION,
    })
    
    # Drift detection daily job
    baseline = avg(eval_db.last_7d_excluding_today())
    today = avg(eval_db.today())
    if today < baseline - 0.05:
        alert("eval_drift", baseline, today)

# MMD test on prompt embeddings
def mmd_drift(today_embeddings, baseline_embeddings):
    return maximum_mean_discrepancy(today_embeddings, baseline_embeddings, kernel="rbf")
```
- Top 3 gotchas: (1) judge model 用 Opus too expensive ($25/M out) → 用 Sonnet 4.6 ($15/M) (2) judge not calibrated vs human → drift in judge (3) drift alert 阈值死板 (用 percentile not absolute)
- Tools: Braintrust, LangSmith, Phoenix evals, Sonnet 4.6 as judge, custom MMD

**Problem 5: Debug Workflow — Trace_ID → Slice → Re-run**

```
Standard runbook:
1. User reports: "agent gave wrong answer for X"
2. Find trace_id from user session or audit log
3. Read trace top-down in Honeycomb / Datadog
4. Identify failed span (error / high latency / bad eval)
5. Compare to good case (same template, similar query)
6. Re-run with replay tool (deterministic mocks)
7. Slice analysis: by tenant / model / template / time
8. Root cause: prompt / tool / model / RAG / input / cache stale
9. Hot fix: rollback prompt OR patch tool OR retrain
10. Post-mortem: add eval case to prevent regression
```
- Replay tool: store {prompt, model, version} → re-call with same input + mocked tool outputs
- Slice dashboards: per-tenant eval score, per-template error rate, per-model latency
- Top 3 gotchas: (1) trace 没 PII redact → 看 log 时再 redact 太晚 (2) replay 不 deterministic (tool 随机) (3) slice 维度太多 cardinality 爆
- Tools: Honeycomb (slice excellent), LangSmith replay, custom replay harness

### 🔥 Production gotchas (top 15)

1. **Raw PII in logs**: SOC2 / GDPR 违规, 必须 Presidio redact at write
2. **100% sample everything**: TB/day cost, 必须 tail-based
3. **No LLM eval-in-prod**: quality silent drop, "prompt-by-vibes"
4. **No tool spans**: agent debug 卡哪步不能
5. **Single pillar (only metric)**: log + trace + eval 都没 → 盲眼
6. **No alerting on eval drop**: 3 周后客户告才知
7. **Trace context not propagated**: agent → gateway → MCP 各自 trace
8. **No prompt_template_version tracking**: 改 prompt 不知道 perf delta
9. **No cost attribution per feature**: 1 bad prompt 100x token spike 不知
10. **No PII deletion workflow (GDPR)**: 用户要求删 → 找不到记录
11. **LLM judge 用 Opus**: cost $25/M out, 选 Sonnet $15
12. **Judge not calibrated vs human**: judge drift 自己
13. **High cardinality metric (per-user)**: Prometheus 爆
14. **Synthetic probe 不 per-tenant**: tenant-specific 漏 detect
15. **Eval drift detect 阈值死板**: 用 percentile (P25 baseline) 不 absolute

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Slice analysis | Voice agent ID market | "Eval drop 92→84%, 4h identify+fix via per-market slice + replay" |
| Prompt version track | BNPL chatbot | "prompt_template_version + model_version in span, A/B easy" |
| PII redact + SOC2 | Voice agent + payment | "Presidio redact at write, SOC2 audit pass, GDPR delete by hash" |
| Per-tenant SLA | Voice agent 7 markets | "Synthetic probe 1/min per market, SLO dashboard, monthly auto report" |
| Cost attribution | TikTok PayLater | "Per-(feature, tenant) cost dashboard caught 1 bad prompt 100x token spike" |
| Drift MMD | Internal Agent Platform | "Daily MMD on prompt embeddings, catch shift before user complains" |
| LLM-as-judge | BNPL eval pipeline | "Sonnet 4.6 judge 5% sample, calibrate weekly vs human 0.85 corr" |
| Debug runbook | Indonesia refund incident | "Trace_id → replay → slice 1 tenant → root cause 4h" |

### 🎤 面试现场 quotables (top 8)

1. "LLM obs needs 4 layers, not 3 — eval-in-prod is the LLM-specific one"
2. "Tail-based sampling: 1% baseline + 100% (errors / slow / expensive / VIP / jailbreak), 30x cost reduction"
3. "PII redact at write, not at read — at-read is already 数据泄"
4. "Cost from response.usage (provider authoritative), not your estimate"
5. "Prompt_template_version + model_version in every span, A/B 立刻能切"
6. "LLM judge calibrate vs human weekly, otherwise judge drift"
7. "Drift detection: 7-day baseline + MMD test on prompt embeddings, daily auto"
8. "Per-tenant synthetic probe 1/min + SLO dashboard, monthly auto credit policy"

### 🚨 红线 (top 10 anti-patterns)

1. Raw PII in logs (SOC2 / GDPR 违规)
2. 100% sample everything (TB/day)
3. No LLM eval-in-prod (prompt-by-vibes)
4. No tool spans (debug stuck)
5. Single pillar (盲)
6. No alerting on eval drop
7. Trace context not propagated
8. No version tracking
9. No cost attribution per feature
10. No PII deletion workflow

### 📊 Span attributes 全表 (LLM-specific, 背)

```
llm.model                        claude-sonnet-4.6
llm.prompt_template_version      v2.3
llm.prompt_hash                  sha256[:16]
llm.input_tokens                 1234
llm.cached_input_tokens          800   (Anthropic 90% off)
llm.output_tokens                567
llm.cost_usd                     0.012
llm.ttft_ms                      820
llm.total_ms                     3500
llm.finish_reason                stop / length / refusal
llm.refused                      bool
tools.used                       ["get_balance", "send_sms"]
cache.semantic_hit               bool
cache.prefix_hit_ratio           0.85
quality.eval_score               4.2 (async populated)
security.jailbreak_flag          false
tenant.id                        "tk_payL_001"
feature.id                       "refund_tier3"
user.tier                        gold
```

### 🧰 2026 工具栈 quick lookup

| 类别 | 默认 | Alt | 你用过 |
|---|---|---|---|
| Trace SDK | OpenTelemetry | — | OTel ✅ |
| Trace backend | Honeycomb (slice excellent) | Datadog APM, Tempo | Honeycomb |
| LLM-specific obs | LangSmith | Phoenix, Helicone, Langfuse, W&B Weave | LangSmith ✅ |
| Metric | Prometheus + Mimir | Datadog, Grafana Cloud | Prometheus |
| Eval suite | Braintrust | OpenAI Evals, Anthropic Evals | Braintrust |
| LLM judge | Claude Sonnet 4.6 | Gemini 3 Pro | Sonnet |
| PII | Presidio | AWS Macie, AWS Comprehend | Presidio ✅ |
| GPU monitor | NVIDIA DCGM | Datadog GPU | DCGM |
| Sampling | OTel Collector tail | Honeycomb Refinery | OTel |
| Drift | MMD / KS test custom | Evidently AI, Arize | MMD custom |

### 🎬 45-min 节奏 (T3.4 专属)

```
0-5    Clarify    "QPS? Multi-tenant? SLA? Compliance (SOC2 / GDPR)? Stack?"
5-10   Mental     "4 layer + tail sample + PII redact + per-tenant SLA"; 画 ASCII
10-25  4 layer    Trace / LLM-log / metric / eval-in-prod 逐层
25-35  Sampling+PII Tail-based + Presidio + GDPR delete
35-42  Eval+Debug LLM judge + drift + replay + slice runbook
42-45  Resume     "Voice agent ID 4h fix; SOC2 audit pass"
```

### 🔢 关键 production 数字

- Voice agent ID market: eval drop 92% → 84%, 4h identify + fix via slice + replay
- BNPL chatbot: prompt_template_version + model_version per span
- SOC2 audit: pass via Presidio redact at write
- Per-tenant SLA dashboard: 7 markets, synthetic probe 1/min, monthly auto report
- Tail-based sampling cost reduction: ~30x vs 100%
- LLM judge calibration corr: 0.85 (Sonnet 4.6 vs human, weekly recalibrate)
- Drift detection: 7-day MMD baseline, daily run, alert > 5pp drop
- Eval-in-prod sample rate: 5% random + 100% flagged
- Cost from response.usage: 100% accurate (vs estimate 80%)
