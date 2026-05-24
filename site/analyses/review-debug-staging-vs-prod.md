## Tech #3 · Debug Agent Staging vs Prod — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/debug-staging-vs-prod.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`debug-staging-vs-prod.html`](questions/debug-staging-vs-prod.html)

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 核心心智模型 (1 sentence)

Staging vs prod inconsistency debug = "先 clarify 'wrong / different / slower' → stabilize (rollback if > 50% impact) → reproduce (trace_id + snapshot + replay) → cheap-first 7-diff source (config 35% / model 20% / time 15% / data 12% / state 10% / dep 5% / scale 3%) → fix + prevent (golden trace + canary + shadow)", 90% root cause 不是 model 本身是 D2/D3 (config / model hash).

### 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Staging vs Production | 两个环境, 理想一样实际 drift | 整体框架 |
| Inconsistency | wrong / different / slower 3 类 | 必先 clarify |
| Reproducibility | 给一个 prod failure 能在 staging 复现 | 80% 成功标志 |
| trace_id | OpenTelemetry span ID, 端到端 propagation | 找 specific request 必备 |
| D1-D7 | data / config / model / dep / scale / state / time | 7 类 diff source |
| Cheap-first | hash diff < config diff < dep diff < dist diff < load test | 诊断顺序 |
| Golden trace | 200-500 case CI gate eval | 防 regression |
| Shadow mode | 1-10% 流量 fork 到 staging, async compare | drift visibility |
| Canary deploy | 1% → 10% → 50% → 100% with auto-rollback | 防全量伤害 |
| Snapshot | failure 时存 full reproduce context (S3 30d) | 后续 replay 用 |
| PSI | Population Stability Index, 衡量 distribution drift | D1 数据 drift |
| KS test | Kolmogorov-Smirnov 累积分布最大差 | D1 detection |
| Singleflight | dlock + cache 防 thundering herd refresh | D7 token expire |
| Prefix cache | vLLM KV cache 复用前 prefix | D5/D6 scale + state |
| Replay tool | prod trace → staging run, compare output | parity verify |

### 5 个核心 framework / pattern

**Framework 1**: 7 diff sources cheap → expensive
- When: production-only bug
- Algorithm: D2 config (35% RC) → D3 model SHA (20%) → D4 deps (5%) → D1 data dist (12%) → D7 time (15%) → D6 state (10%) → D5 scale (3%); 按 occurrence × diagnostic cost 排序
- Trade-off: 跳过 cheap → 浪费 hours, 但深奥 bug 必到 D5/D6
- Tools: kubectl get cm diff, pip freeze diff, sha256sum 校验

**Framework 2**: Reproducibility 三件套 (trace + snapshot + replay)
- When: prod failure debugging
- Algorithm: 1) trace_id OpenTelemetry propagation 端到端 / 2) Per-request snapshot S3 30d (100% failure + 1% success) / 3) Replay tool — prod trace → staging run + override config + override seed + compare
- Trade-off: snapshot 存储 vs forensic 能力
- Tools: opentelemetry SDK, structlog with trace_id, S3 30d retention bucket

**Framework 3**: Environment parity (Golden + Shadow + Canary)
- When: 防 future drift
- Algorithm: Golden traces 200-500 case CI gate / Shadow mode 1-10% async fork / Canary 1→10→50→100% auto-rollback on error budget
- Trade-off: shadow $$, but catch drift before customer
- Tools: Argo Rollouts, Flagger, custom shadow proxy

**Framework 4**: Stateful diff (cache / in-mem / KV / replica)
- When: D6 state-driven bugs
- Algorithm: warm cache vs cold cache 都跑 / externalize in-memory singleton state to Redis / vLLM KV cache + batch_size 影响 FP16 rounding / per-replica state divergence dump
- Trade-off: stateless 更易 reason, 但 LLM inference 天然 stateful
- Tools: replica_consistency_check, kubectl describe pod, GPU memory dump

**Framework 5**: Time-dependent bugs (D7)
- When: 只某天 / 某小时复现
- Algorithm: 所有内部 UTC, 用户显示 local / preempt refresh 5min before expire + distributed lock / cache TTL parity assert / data freshness assert MAX(updated_at) recent / cron 依赖 signal 不依赖 clock
- Trade-off: timezone discipline 严格要求 + audit
- Tools: NTP chronyd, pytz, scheduled freshness check

### 关键决策树 (ASCII)

```
请求出现 inconsistency
   |
   v
Clarify: wrong / different / slower?
   |
   v
Stabilize: > 50% 受影响? → immediate rollback to LKG
                       → 否则收 sample 找 RCA
   |
   v
Reproduce: 拿 10 个 prod failing trace → replay staging
   |
   ├─> 复现 → input-driven (D1/D2 嫌疑)
   └─> 不复现 → env-driven (D3-D7 嫌疑)
   |
   v
Cheap first (< 4h):
   D2 config diff (kubectl get cm)
   D3 artifact SHA (sha256sum)
   D4 pip freeze diff
   |
   v
Medium (4-24h):
   D1 distribution (PSI / KS) on input
   D7 time audit (token expire / cache TTL / DST)
   |
   v
Hard (> 1d):
   D6 state introspect (replica divergence)
   D5 load test (mimic prod QPS)
   |
   v
Fix + Prevent:
   minimal repro test → regression suite
   postmortem (5 whys)
   canary 1% → 10% → 50% → 100%
   shadow eval add
   golden trace add
```

### Part 2 五个深度问题速查

**Problem 1: 7 类 diff source 系统排查**
- 核心解法: cheap → expensive 顺序 (D2 35% / D3 20% / D7 15% / D1 12% / D6 10% / D4 5% / D5 3%); 每类有专属诊断工具
- Top 3 gotchas: 不要立刻怀疑 model (90% RC 不在 model) / "recently changed" 永远先查 / 不跳到 GPU 非确定性 (配置 1 行不同的概率高 10x)
- Tools: PSI / KS test (D1), config diff (D2), sha256 (D3), pip freeze (D4), vegeta/wrk (D5), state dump (D6), time audit (D7)

**Problem 2: Reproducibility instrumentation (trace + snapshot + replay)**
- 核心解法: OpenTelemetry trace_id 端到端 (LLM metadata + response header + audit) / RequestSnapshot dataclass (trace_id, model_id, model_sha, image_sha, pod_id, seed, temperature, feature_flags, result) / ReplayTool prod-trace → staging-run + compare
- Top 3 gotchas: trace_id 进 LLM API metadata 字段 (OpenAI / Anthropic dashboard 才能查) / snapshot 必含 model_sha 不仅 model_id / replay 要 override seed 才 deterministic
- Tools: opentelemetry-sdk, structlog, S3 snapshots bucket 30d retention

**Problem 3: Environment parity (Golden / Shadow / Canary)**
- 核心解法: Golden 200-500 case CI gate (每 incident 加 1 防 regression) + Shadow 1-10% async fork + Canary Argo Rollouts 1→10→50→100% auto-rollback (error rate / latency / agent success rate)
- Top 3 gotchas: shadow 必 async 不阻塞 user / semantic similarity not exact match (LLM 有合理变化) / canary auto-rollback 阈值要 specific (error rate > 1% vs baseline 0.1%)
- Tools: Argo Rollouts / Flagger, semantic shadow diff using embedding cosine

**Problem 4: Stateful diff (cache / in-mem / vLLM KV / replica)**
- 核心解法: cache warm vs cold both test / externalize in-mem singleton → Redis / vLLM enable_prefix_caching=False for critical / per-replica state dump + outlier detection
- Top 3 gotchas: prod hot path 永远 cache hit, staging cold path 永远 cache miss → 测试覆盖两态 / batch_size 影响 FP16 rounding (paged attention) / 1 replica state stale → 25% 流量行为不一样
- Tools: replica_consistency_check, kubectl describe, vllm config dump

**Problem 5: Time-dependent (D7)**
- 核心解法: UTC everywhere / preempt 5min refresh + dlock / cache TTL parity assert / data freshness assert / cron depend on signal not clock
- Top 3 gotchas: DST 3月/11月切换日 system down / token 12h 同一刻全 expire thundering herd / agent 起动时拿 stale data (pipeline 没 ready)
- Tools: NTP chronyd 5s tolerance, pytz / ZoneInfo, max(updated_at) freshness check

### Production gotchas (top 15)

1. 立刻怀疑 model (90% RC 不在 model)
2. 没 trace_id 就 debug (在 high QPS 找 specific request 不可能)
3. 没 reproduce 就 fix (改一个引入另一个)
4. 跳过 cheap diffs 直接怀疑 GPU
5. Ship fix without RCA (mask 真因 1 周再爆)
6. 没 region/GPU/lib SHA tag (一切靠猜)
7. Customer 压力下盲 fix (通常延长事故)
8. 忽略 "recently changed" (recent change = recent break)
9. 盯个例不看 per-segment (aggregate 隐 5% 用户 100% 失败)
10. File 用 symlink 没更新 (文件名对内容不对)
11. 不验 cuBLAS / cuDNN version (silent inference bug)
12. Customer's TZ 处理错 (印尼 23:30 "明天" 解析成下下周)
13. Vault token 12h TTL 同时过期 (thundering herd refresh)
14. Cron 依赖时钟不依赖 signal (pipeline 没 ready 也跑)
15. Aggregate metric 看不到 per-region 5% 失败

### 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Multi-region inconsistency | Voice agent 7 markets | Bahasa drift on Indonesia release 25% 失败 |
| Library / artifact hash mismatch | vLLM / SGLang upgrade | 强制 sha256 校验 image |
| Per-request observability | Voice agent latency tracing | region + GPU + lib SHA tag |
| Canary on every deploy | 7 markets phased rollout | Argo Rollouts 1→10→50→100% |
| Shadow eval | ConvFinQA stratified 300 eval | per-length-bucket 类似分类 |
| Time-dependent bug | Vault token 12h 同时 expire | preempt 5min + dlock fix |
| Reproduce + replay tool | Voice agent failed call replay | prod trace → staging run |

### 面试现场 quotables (top 8)

1. "Production-only bug debug 顺序: clarify → stabilize → reproduce → cheap-first 7-diff source → fix + prevent."
2. "90% RC not model itself. 35% config drift / 20% model SHA / 15% time / 12% data dist / 10% state / 5% deps / 3% scale."
3. "trace_id + per-request snapshot + replay tool 三件套. 没 reproduce = 没 fix."
4. "Argo Rollouts canary 1→10→50→100% + auto-rollback on error budget. Plus shadow 1% to staging mirror."
5. "Indonesia Bahasa drift 25% — D2 config diff caught 'Respond only in English' system prompt addition, never in staging eval. Fix 10 min. Process change (mandatory eval-on-PR) the real fix."
6. "Hash-versioned deploy artifacts: assert pre-deploy that declared model_sha matches actual file SHA. Don't trust filenames."
7. "Time-dependent: UTC internal, user_tz display. Preempt 5min refresh + distributed lock prevents 12h expire thundering herd."
8. "Aggregate metric hides 90% drift signal. Stratified by per-market × per-customer-tier × per-day-of-week."

### 红线 (top 10 anti-patterns)

1. Blame model first (cheap diffs 一定先查)
2. Ship fix without RC (mask 真因)
3. No trace_id propagation
4. No artifact hash assertion
5. Trust filename (use SHA)
6. Aggregate metric only (per-segment 必须)
7. Customer 压力下盲 fix
8. Skip "recently changed" check
9. Stage QPS << Prod QPS (load test gap)
10. No canary on every deploy

### 7 diff source quick-reference (cheap → expensive)

| Class | What | Diagnostic | Typical cost |
|---|---|---|---|
| D2 Config | model_id / sys_prompt / temp / top_p / max_tokens / stop / tools | `diff <(prod get cm) <(staging get cm)` | 1h |
| D3 Model | checkpoint / LoRA / tokenizer hash | sha256sum compare | 1h |
| D4 Dependency | vLLM / torch / transformers / cuBLAS / cuDNN | `pip freeze` diff | 2h |
| D1 Data | input distribution (length / lang / topic) | PSI / KS test | 4h |
| D7 Time | DST / TZ / token expire / cache TTL / data freshness | time audit | 4h |
| D6 State | cache warm / in-mem / KV cache / replica divergence | state dump | 1d |
| D5 Scale | batch / concurrency / KV evict / paged attention | load test | 3d |

### Real-world distribution of root cause (voice agent 7 markets 复盘)

| Class | % occurrence | Example |
|---|---|---|
| D2 Config | 35% | "Respond only in English" 添加, 没在 staging eval |
| D3 Model | 20% | model_v2.bin vs model_v2_quantized.bin |
| D7 Time | 15% | Vault token 12h 同期 expire thundering herd |
| D1 Data | 12% | Long prompt (> 2K tokens) tool selection regress |
| D6 State | 10% | 1 replica stale flag, 25% 行为不一样 |
| D4 Dep | 5% | vLLM v0.5 vs v0.4.8 prefix caching default |
| D5 Scale | 3% | batch_size FP16 rounding 累积 |

### Canary deploy auto-rollback conditions (Argo Rollouts spec)

| Metric | Threshold | Action |
|---|---|---|
| Error rate | > 1% (vs baseline 0.1%) | rollback |
| p99 latency | > 2× baseline | rollback |
| agent_success_rate | < 95% | rollback |
| 5xx rate | > 0.5% | rollback |
| OOM kills | any in 10 min | rollback |
| GPU OOM | any | rollback |
| Restart rate | > 5/min | rollback |

### 工具栈 (real production)

| Stage | Tool |
|---|---|
| Trace | OpenTelemetry + Tempo/Jaeger |
| Log | structlog + Loki / Datadog |
| Metric | Prometheus + Grafana / Datadog |
| Snapshot store | S3 30d retention |
| Canary | Argo Rollouts / Flagger |
| Shadow proxy | Envoy / custom Lua filter |
| Replay tool | custom CLI on snapshots |
| Golden traces | YAML in repo, CI gate |
| Hash assertion | Cosign / Sigstore for image sig |

### RequestSnapshot dataclass fields

| Field | Purpose |
|---|---|
| trace_id | end-to-end identifier |
| timestamp | when failed |
| user_id | who hit it |
| region | geo dimension |
| request_body | replay input |
| request_headers | auth + meta |
| model_id | which model |
| model_sha | content-addressed |
| tokenizer_sha | content-addressed |
| image_sha | container ID |
| pod_id | replica ID |
| gpu_type | hardware |
| feature_flags | active flags snapshot |
| config_snapshot_sha | config ref |
| system_prompt_hash | which prompt version |
| temperature | LLM param |
| top_p | LLM param |
| max_tokens | LLM param |
| seed | reproducibility |
| response_body | what was returned |
| latency_ms | timing |
| error | if any |

### 5 业务场景变体 (anchor stories)

| Variant | Symptom | RC class | Fix |
|---|---|---|---|
| Voice agent Indonesia (Bahasa drift) | 25% English replies on Indonesia | D2 config | system_prompt diff + eval suite enforced |
| ConvFinQA quantized model | Staging 78% → Prod 71% accuracy | D3 model SHA | model_v2.bin vs model_v2_quantized.bin |
| Singapore vs India region | India 15% accuracy drop | D4 dep + D6 state | vLLM v0.5 vs v0.4.8 enable_prefix_caching default |
| BNPL chatbot tool calling | Prod 偶尔选错 tool | D1 data + D5 scale | long context tool selection regress |
| Indonesia refund tier flag | Confirmation 周二开始不弹 | D7 time + D6 state | feature_flag cache 24h TTL stale on prod |

### Cheap-first 诊断顺序 (recommended)

| Order | Class | Why |
|---|---|---|
| 1 | D2 Config | 35% RC, 1h cost — kubectl diff config |
| 2 | D3 Model SHA | 20% RC, 1h cost — sha256sum compare |
| 3 | D4 Dependency | 5% RC, 2h cost — pip freeze diff |
| 4 | D1 Data | 12% RC, 4h cost — PSI / KS test |
| 5 | D7 Time | 15% RC, 4h cost — token / cache / DST audit |
| 6 | D6 State | 10% RC, 1d cost — replica state dump |
| 7 | D5 Scale | 3% RC, 3d cost — load test mimic prod QPS |
