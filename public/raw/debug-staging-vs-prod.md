## 题目（verbatim）

> "An **AI agent returns inconsistent results in production** compared to staging. Walk through your debugging approach end-to-end."

**出处**：fde.academy 列出的高频技术 round 题。OpenAI / Anthropic / Google FDE 都问过。

**Round**：Technical Integration / Debug (45-60 min)

---

## 这道题在考什么

考你**production deployment 的诊断套路**。AI deployment 大多数失败都是这个 shape：

1. **5 类典型 root cause** —— 你知道几个？
2. **诊断顺序** —— 先 cheap 后 expensive
3. **能不能 reproduce** —— production-only bug 是最难的
4. **Don't blame the model first** —— 9/10 root cause 不是 model

---

## 必问 clarifying questions

**1. Define "inconsistent"**

> "What kind of inconsistency — **wrong** answers, **different** answers each time (non-determinism), or **slower** answers?"

**2. Frequency**

> "All requests, or specific ones? Percentage? Same input always reproduces?"

**3. Same model artifact**

> "Are staging and prod running the **identical model checkpoint**? Same model version + system prompt + tokenizer?"

**4. Same input data**

> "Are users in prod sending the **same shape** of input? Could distribution have shifted?"

**5. Recent change**

> "Has anything changed recently — new release, new feature flag, upstream API changes, infrastructure migration?"

---

## 5 类典型 root cause

| Class | What | Diagnosis cost |
|---|---|---|
| **C1: Config drift** | model version / system prompt / temperature differ | 低 (1h diff configs) |
| **C2: Feature pipeline drift** | prod features are stale / missing / encoded differently | 中 (need trace) |
| **C3: Input distribution shift** | real users send things staging tests didn't cover | 中 (need distribution compare) |
| **C4: Non-determinism** | temperature > 0, batch size affects sampling, multi-replica state | 中 |
| **C5: Infrastructure** | timeout differences, GPU vs CPU, library version, region latency triggering shorter response | 中-高 |

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify + reproduce attempt |
| 5-15 min | C1 cheapest checks first (config diff) |
| 15-25 min | C2/C3 — feature + input distribution |
| 25-40 min | C4/C5 — non-determinism + infra |
| 40-50 min | Fix + add observability so it doesn't happen again |
| 50-60 min | Roll out fix safely |

---

## 我会这样答（sample monologue）

> "First clarify — *[假设：30% of requests, same input不一定 reproduce, configs claim identical, no recent release, infrastructure migrated last week from us-east to multi-region]*.
>
> Last clue is gold: **infrastructure migrated** → C5 candidate.
>
> But I'd still go systematic, cheapest first:
>
> **Step 1: Reproduce on prod with controlled input** (1 hour)
> - Capture **10 prod requests + responses** with full context
> - Replay each on staging with same request
> - See if outputs match. If yes → environmental. If no → input or pipeline.
>
> **Step 2: C1 config diff** (30 min)
> - `diff staging_config prod_config`: model ID, system prompt, temperature, top_p, max_tokens, stop sequences
> - Check **deployed model artifact hash** matches
> - Check **tokenizer version**
> - Check **feature flags** active on prod vs staging
>
> **Step 3: C2 feature pipeline trace** (2 hours)
> - For one failing request: trace every input feature value end-to-end
> - Are all features present? Same range / encoding as training?
> - Common bug: **missing feature defaults to wrong sentinel** (e.g., `-1` instead of `null` → model interprets as "very low score")
>
> **Step 4: C3 input distribution** (1 hour)
> - Compute distribution of input features over last 24h prod vs 24h staging
> - Look for **categories never seen in staging**
> - **Length distribution**: prod might have 99th percentile request 10x longer than staging
>
> **Step 5: C4 non-determinism** (1 hour)
> - If temperature > 0: same input should produce different output. Is that the inconsistency?
> - **Batching**: vLLM / SGLang batch size affects sampling. Compare batch size statistics.
> - Multi-replica: any state per-replica that varies?
>
> **Step 6: C5 infrastructure** (most likely given migration clue)
> - **Timeout**: prod may have shorter timeout → model truncates output mid-generation
> - **Concurrency**: prod under load → models may share KV cache improperly
> - **GPU vs CPU** (or different GPU types): rare but real, FP16 rounding differs
> - **Region latency**: client timeout causes early disconnection, model returns partial
> - **DNS / TLS handshake**: degraded prod path adds 200ms, but doesn't change output... unless triggers shorter max_tokens
> - **Library mismatch**: different transformers / torch version between staging and prod
>
> **Given the 'multi-region migration' clue, my top 2 hypotheses**:
> - **Region routing inconsistency**: 30% of traffic goes to a region with subtly different infra (e.g., older GPU type, library version, env variable)
> - **Timeout truncation**: cross-region call to LLM service has higher latency, downstream timeout truncates response
>
> **Immediate diagnostic**:
> - Tag every prod request with **region**, **GPU type**, **library hash**
> - Aggregate inconsistency rate by region
> - If 30% inconsistency clusters in 1 region, **prove the hypothesis**
>
> **Fix path**:
> - Short-term: **route 100% to known-good region**, accept higher latency from non-local users
> - Mid-term: align library versions / infra across regions (idempotent rebuild)
> - Long-term: **per-request artifact provenance log** so we always know which model+infra+config served each response
>
> **What I'd add to prevent recurrence**:
> - **Hash-versioned deployment artifacts**: every deploy logs SHA of model + tokenizer + system prompt + every dependency. `prod_hash == staging_hash` is invariant.
> - **Per-request observability**: log temperature, model_id, region, GPU type per request. **Without this, we'd never know.**
> - **Shadow eval pipeline**: 1% of prod traffic goes to staging-mirror, daily diff alerts on drift
> - **Canary on every deploy**: 1% → 10% → 100% with auto-rollback on error budget breach"

---

## 简历专属 reframe

你的 **voice agent multi-region** + **ConvFinQA RL alignment** 都涉及 production debug：

| 题 | 你的经验 |
|---|---|
| Multi-region inconsistency | Voice agent 跨 7 markets 不同 region |
| Library / artifact hash mismatch | vLLM / SGLang upgrade 你做过 |
| Per-request observability | Voice agent 端到端 latency tracing 你 own |
| Canary on every deploy | 7 markets phased rollout |
| Shadow eval | ConvFinQA stratified 300 eval 类似 |

**主动说**：

> "I've literally lived this. When we rolled out the voice agent from Singapore-only to multi-region, we got 25% inconsistency rate on Thai customers. We traced it to a **library mismatch** — the Thai region's vLLM was on an older version with different default sampling. We instituted **hash-versioned deploy artifacts** across all regions after that incident — every release we log SHA of model + tokenizer + library and assert equivalence pre-deploy. Saved us 3 more incidents in the year."

---

## 5 follow-ups

**Q1**: "We've checked configs identical, reproduces 30% of time, but staging doesn't show it. What now?"
**A**: Look at **load**: production has 100x traffic. Bug surfaces under **concurrency or batching**. Solutions:
- Simulate prod load on staging with synthetic traffic
- Profile vLLM batching: high concurrency triggers paged-attention re-use, can produce subtly different outputs
- Check **KV cache eviction** under memory pressure

**Q2**: "We can't reproduce even with same input on prod replay. Is it a ghost?"
**A**: Non-determinism likely. Audit:
- Is `temperature=0` enforced? Top-p > 0 still has limited non-det
- Is model **deterministic seed** set? OpenAI's `seed` parameter
- Tokenizer order: BPE merges might differ between versions
- GPU kernel non-det: cuBLAS GEMM has known reproducibility issues; force `torch.backends.cudnn.deterministic = True`

**Q3**: "Bug is intermittent and we can't catch it in staging. Just ship fix?"
**A**: 不行. Without root cause:
- High chance fix doesn't address actual bug
- High chance fix introduces new bug
**Workaround**: ship **observability first** (per-request logs + region tags), then wait 24h for **enough samples to find pattern**. Patience beats hasty patch.

**Q4**: "Customer demands immediate fix. We don't know root cause."
**A**: Negotiate:
- "We can **roll back to last-known-good infra** in 4 hours — restores consistency at cost of feature X. Acceptable?"
- "Or **disable agent for these specific input types** that fail — partial coverage but 100% consistent"
- "Or **A/B with 0% prod traffic for 2 days** while we get root cause from observability instrumented now"
The honest "we'll patch blindly" path almost always extends the incident.

**Q5**: "If it's prompt change ourselves silently made, how do we prevent next time?"
**A**:
- **System prompt as code**: stored in git with version + commit hash, deployed via CI
- **Prompt evals on PR**: every prompt change must pass eval suite before merge
- **Audit log + diff**: every prompt change emits diff to a team channel
- **Per-request prompt SHA** logged so we can reconstruct what was in effect

---

## ❌ 易错点

1. **立刻 blame model** — 90% root cause 不是 model
2. **没尝试 reproduce** — 直接 hypothesize
3. **跳过 C1 config diff** — 最 cheap, 最 common 原因
4. **忽略 infra migration clue** — recently-changed = recently-broken
5. **Ship fix without root cause** — 通常 reverberate
6. **没 observability instrumentation 先** — 没 tag region/GPU/lib version 啥都 trace 不到
7. **Customer 给 immediate pressure 就 cave** — negotiate workaround 时间换 quality

---

## ✅ 加分项

1. **5 root cause classes** 清晰列
2. **Cheapest-first 诊断顺序**
3. **Per-request artifact provenance log** as preventive
4. **Shadow eval at 1% traffic** 防 future drift
5. **Canary auto-rollback on error budget** standard SRE
6. **GPU non-determinism** awareness (cuBLAS GEMM)
7. **System prompt as code + eval-on-PR**
8. **Negotiate workaround for time** 不 cave under pressure

---

## Cheat Sheet

```
5 root cause classes (cheapest first):
  C1 Config drift (model / prompt / temp)
  C2 Feature pipeline drift
  C3 Input distribution shift
  C4 Non-determinism (temp, batch, multi-replica)
  C5 Infrastructure (region / GPU / lib)

Diagnostic flow:
  1. Reproduce on prod, replay on staging
  2. diff configs (model + prompt + dep versions)
  3. Trace 1 feature pipeline end-to-end
  4. Distribution compare (last 24h prod vs staging)
  5. Check non-determinism (seed, batch, replica)
  6. Tag region + GPU + lib hash, aggregate

Quick wins:
  - Per-request observability (region/gpu/lib SHA)
  - Hash-versioned deploy artifacts
  - Shadow 1% prod to staging-mirror
  - Canary + auto-rollback on every deploy

Workarounds while diagnosing:
  - Route 100% to known-good region
  - Disable agent for specific input types
  - Roll back infra (4-6h)
  - DO NOT patch blindly

红线:
  - Don't blame model first
  - Don't ship fix without RC
  - Don't ignore "recently changed"
```
