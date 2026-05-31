# ⚡ T1.2 · Tool Retry / Timeout / Fallback — 冲刺版

> 完整版: [gfde-t1-retry-fallback.html](gfde-t1-retry-fallback.html). 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: 客户面 agent, latency budget = 2s p99 端到端, tool 不一定 idempotent, vendor SLA 99.9%, retry 不能放大 cost, agent runtime owns retry policy (不是 LLM 决定)."

**4-layer 策略**:

### Layer 1: 失败分类 (决定 retry vs fail-fast)

```
4xx (除 408/429) → fail-fast, 不重试 (永久性错误)
408 timeout      → 可重试 (transient)
429 rate-limit   → 按 Retry-After 重试
5xx              → 可重试 (server transient)
Network reset    → 可重试
DNS / TLS error  → 可重试 (但小心 — 可能是 outage)
```

LLM-generated tool error (parse fail) → **不 retry**, 让 agent 看到 error 改 args.

### Layer 2: Retry 算法 (exponential backoff + jitter)

```python
delay = random.uniform(0, min(cap, base * 2**n))   # AWS full jitter
base=0.5s, cap=30s, max_attempts=5
```

**为啥 jitter**: 没 jitter, N 个 client 同步重试 → thundering herd 把刚恢复的 server 又打挂.

**Per-tool retry budget**: 给每个 tool 设 `max_total_time` (e.g., 3s), 不只 max_attempts. 一个 tool 烧光整个 2s p99 latency 不行.

### Layer 3: Circuit breaker (防雪崩)

```
状态机:
  closed   (正常): 失败计数, ≥5 连续失败 → open
  open     (短路): 60s 直接返 fallback, 不打 vendor
  half-open: 60s 后试 1 个 request, 成功 → closed; 失败 → open
```

每个 tool 独立 breaker, 不要 global (一个 vendor 挂不能拖全部).

### Layer 4: Fallback tier (降级而非崩溃)

```
Primary tool fail → Fallback strategy:
  T1: Cached result (Redis, TTL 60s, mark "stale data" to user)
  T2: Alternative vendor (Stripe down → Adyen; OpenAI → Anthropic)
  T3: Degraded answer ("I can't access live data, here's what I knew last")
  T4: Graceful refusal ("Service temporarily unavailable, your request is queued")
```

不要 silent fail. LLM 必须看到 "fallback engaged" 标记, 不能假装一切正常.

### Edge cases

- **EC1 Retry budget exhausted mid-conversation**: 返 error to LLM, prompt 让它 ask user "retry later or accept partial?"
- **EC2 Timeout but server commit**: 见 idempotency Q (T1.1) — query-by-ref 确认.
- **EC3 Circuit breaker 误判** (transient blip 触发了 open): half-open 是关键. 也加 manual override (oncall 可以强制 close).
- **EC4 Vendor 维护窗口**: status page poll, calendar-aware, 不在维护期 retry.
- **EC5 Latency budget 倒计时**: 每跳记录 `remaining_budget`, 没钱了直接 fail (不 retry).

### Production hardening

- **Metrics**: retry_count{tool, attempt, outcome}, circuit_breaker_state{tool}, fallback_engaged_rate
- **Alert**: retry_rate > 30% (5min sustain) = upstream 问题早期信号
- **Chaos test**: 月度 inject vendor 504, 验证 fallback 链工作
- **Budget cap**: per-conversation `max_total_retry_cost` (防 LLM 失控重试烧钱)

### 🪝 Resume hook

"PayLater agent 接 OTP vendor 间歇 5xx, 我加了 circuit breaker + Adyen 作 fallback. Before: 0.8% conversation 因为 OTP fail user drop. After: 0.04%, 20x 改善."

---

## 🔥 5 Follow-ups

**Q1: Fixed vs exponential backoff 怎么选?**
固定 interval 在 server 高压时持续打压. 指数让重试越来越稀, 给 server 喘息. **永远 exp + jitter**.

**Q2: Max retry 怎么选?**
看 SLA. p99 = 2s 的 agent, 3 次 retry 总 budget 不能 >1.5s. 用 `total_time_budget` 而非 `max_attempts` 更准.

**Q3: Circuit breaker 误判误伤怎么办?**
3 件: (a) half-open 是设计内自动恢复 (b) failure threshold 用 % 而非绝对数 (e.g., 5xx rate >50% 持续 30s, 不是 5 个失败) (c) oncall manual override slack command.

**Q4: Non-idempotent tool 怎么 retry?**
不要直接 retry. 流程: 第 1 次失败 → idempotency key 已设 → in_flight 状态 → 走 idempotency 系统 wait + status check (T1.1). 不到这层就直接 fail 给 LLM.

**Q5: Fallback 链怎么不级联崩溃 (primary 挂 fallback 也挂)?**
(a) Fallback 必须比 primary 独立 (不同 vendor / region) (b) Fallback 有自己 breaker (c) 终极 fallback = static degraded response 不依赖任何 vendor (d) 每月 chaos test 主备都挂的场景.

---

## ❌ 易错点

1. 没分类 fail (4xx 也 retry → 浪费)
2. 没 jitter → thundering herd
3. Retry 无 budget → 单 tool 吃光 latency
4. Global circuit breaker (一挂全挂)
5. Silent fallback (LLM 不知道 degraded)
6. 没 half-open → breaker 永远 open
7. Non-idempotent tool 直接 retry → 双扣
8. Fallback 和 primary 同 vendor (一起挂)
9. 没监控 retry rate (上游异常不知道)
10. 没 chaos test (生产第一次见 = 翻车)

---

## ✅ 加分项

1. AWS full jitter 算法 (`random.uniform(0, min(cap, base*2**n))`)
2. Per-tool 独立 circuit breaker
3. Half-open state + manual override
4. 4-tier fallback (cache / alt vendor / degraded / refusal)
5. LLM 看到 fallback marker (不假装正常)
6. Per-conversation cost cap
7. Retry rate metric + 30% alert (早于 error_rate 30-60s)
8. Vendor calendar-aware (维护期不 retry)
9. Failure type classifier (4xx vs 5xx vs network)
10. Chaos test monthly drill
11. Latency budget propagation (`remaining_budget` per hop)
12. Tenacity / resilience4j library mention (vs hand-roll)
13. Resume hook (PayLater OTP 20x 改善)

---

## 一句话总结

Retry/fallback = **classify error + exp jitter + per-tool circuit breaker + 4-tier fallback + budget propagation + chaos test**. LLM 永远不应该自己决定 retry, runtime owns 整个 policy.

---

## 🃏 Cheat Sheet

```
Failure classification:
  4xx (除 408/429): fail-fast
  408 / 429 / 5xx / network: retry
  TLS / DNS: retry-cautious (could be outage)
  LLM-tool parse error: fail-fast (let agent fix)

Retry formula (AWS full jitter):
  delay = random.uniform(0, min(cap, base * 2**n))
  base=0.5s, cap=30s, max_attempts=5
  per-tool budget: max_total_time=3s

Circuit breaker (per-tool):
  closed → 5 consec fail / 50% rate 30s → open
  open: 60s short-circuit to fallback
  half-open: 1 req test, ok→closed, fail→open

Fallback tier:
  T1: cached result (60s TTL, mark "stale")
  T2: alternative vendor
  T3: degraded answer (LLM aware)
  T4: graceful refusal + queue

Latency budget:
  端到端 2s p99
   ├─ tool retry budget: 3s max
   ├─ per-attempt budget: cap delay 30s
   └─ remaining_budget propagated each hop

Monitor:
  - retry_rate per tool (alert >30%)
  - circuit_breaker_state changes
  - fallback_engaged_rate
  - p99 of retry path

Test:
  - chaos: inject 504 monthly
  - circuit breaker tripping unit test
  - fallback chain integration test

红线:
  - 同步 retry (no jitter)
  - global breaker
  - silent fallback
  - non-idem tool naive retry
  - no chaos drill
```
