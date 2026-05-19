## 题目（verbatim）

> "A major city wants to use our platform to **reduce 911 emergency response times**. They have **911 call data, traffic data, and ambulance GPS data**. You have **60 minutes**. Go."

**出处 / 公司**：**Palantir 经典原版**（FDE 这个 round 的"始祖"）。后被 OpenAI / Google / Salesforce / Databricks 全部复用。多个候选人在 Glassdoor / Medium / fde.academy 公开 report。

**Round**：Case Study / Decomposition（30-60 min，single-question）

---

## 这道题在考什么

**不是**：考你"做出一个 911 系统的方案"。  
**是**：考你**面对一个庞大、模糊、含多个数据源的真实客户问题，能不能在 60 min 内做出 structured decomposition + propose tractable MVP + surface tradeoffs**。

3 个评分轴：

1. **Clarify before solving** —— 一上来就画图、写代码 = 失分。FDE 圈一个共识："Jumping to answers is an immediate red flag"
2. **Tractable MVP** —— 你能从一个无边界问题里切出一个**3 周能交付 + 测得到 KPI**的最小版本
3. **Surface tradeoffs proactively** —— 在面试官追问前就主动说"这个方案的失败模式是 X / Y / Z"

---

## 一上来必问的 5 个 clarifying questions

**1. Stakeholders & success metric**

> "Who's the buyer — the mayor's office? Police? Fire department? And what's their **single KPI**? Average response time? P99 response time? Response time for a specific call category like cardiac arrest?"

**为什么问**：每个 stakeholder 的 metric 不一样。Police 关心 violent crime 响应；fire 关心 structure fire 响应；mayor's PR 关心 average。**先锁 KPI**，不然后面所有 design 都飘。

**2. Constraints**

> "What's the **integration constraint** — do we have read access to dispatch system, or just batch dumps overnight? Real-time GPS feed from ambulances, or 5-min sampled? Is the city willing to deploy on our cloud, or strict on-premise?"

**为什么问**：FDE 是 deployment 工程师，不是 research scientist。data freshness + integration mode 决定整个 architecture 是 batch ETL vs streaming。

**3. Baseline**

> "What's the **current** average response time? And what's the city's stated target — 10% improvement, or moonshot 50%?"

**为什么问**：no baseline = no eval。10% 改进 (统计 noise above threshold) 跟 50% 改进 (要换 dispatch policy 那种级别) 是完全不同的项目 scope。

**4. Scope of platform**

> "When you say 'our platform' — are we **dispatch software** (operator picks an ambulance), or **predictive routing** (real-time traffic-aware route), or **resource pre-positioning** (where to park idle ambulances)?"

**为什么问**：60 min 内做不完全部。**Force the interviewer to scope you down**。

**5. Failure mode tolerance**

> "What's the **cost of a wrong prediction**? If we route an ambulance through traffic that turns bad mid-route, what's the fallback?"

**为什么问**：emergency response is **safety-critical**。失败一次进新闻。**Risk appetite 决定 model 类型**（lookup-table baseline vs ML 模型 vs hybrid）。

---

## 5 步框架（60 min 时间分配）

| 时长 | 阶段 | 要做什么 |
|---|---|---|
| 0-10 min | **Clarify + scope** | 上面 5 个问题，把范围 narrow 到 1 个具体子问题（e.g. "real-time predictive routing for ambulance dispatch"） |
| 10-25 min | **Architecture sketch** | 3 个 components：data ingestion / decision engine / dispatcher integration |
| 25-40 min | **Deep dive 1 component** | 选最难的 1 个（通常是 decision engine + 实时 traffic）展开讲 |
| 40-50 min | **Failure modes + measurement** | "这个 design 怎么挂"、KPI 怎么测、 dispatcher 怎么 trust |
| 50-60 min | **Phasing + scope reduction** | 90-day MVP 应该长什么样、phase 2/3 是什么 |

---

## 我会这样答（sample 完整 monologue）

> "Before diving in, let me ask 5 things — *[问 5 clarifying questions, 假设面试官回应：mayor's KPI = average response time, target = 15% reduction in 12 months, real-time GPS + 5-min traffic, scope = predictive routing not pre-positioning]*.
>
> OK so the problem is **real-time predictive routing**: given an incoming 911 call with location + category, route the optimal ambulance with optimal path, factoring current traffic.
>
> **Architecture is 3 layers**:
>
> 1. **Ingest** — 3 streams: 911 calls (sub-second, push), ambulance GPS (1Hz pull), traffic feed (5-min batch).
> 2. **Decision engine** — for each new call: (a) candidate ambulances = those within 5km radius + not currently transporting; (b) ETA estimator per (ambulance, call) pair using current traffic graph; (c) pick min-ETA dispatch.
> 3. **Dispatcher integration** — push recommendation to existing CAD (computer-aided dispatch) system, **suggest don't replace**. Human dispatcher confirms or overrides.
>
> **The hard part is the ETA estimator under traffic uncertainty**. I'd start with a **simple shortest-path on the road graph weighted by current avg speed** as v0 baseline. Run it for 4 weeks shadow-mode — predictions logged but not surfaced to dispatchers — and measure prediction error against actual transit times. If MAE is acceptable (say <90 seconds), graduate to live recommend. If not, layer in an ML model that learns time-of-day / weather / event corrections.
>
> **Failure modes I'd preemptively address**:
> - Model recommends ambulance A but A is unavailable for human reason (radio down, crew swap) — fallback to dispatcher's manual pick within 5 seconds.
> - Traffic feed stale → degrade gracefully to no-traffic shortest path (don't fail closed).
> - Edge case: cardiac arrest call where time matters in absolute terms — bypass ML, use deterministic nearest-available.
> - 'Distrust dispatcher' problem: if dispatchers don't trust the rec, they ignore it. Track override rate as a North Star metric.
>
> **Measurement**: in-flight A/B isn't ethical (denying half the city the improvement), so we'd do **before/after with comparable-period control** (last year's response times for same months/categories), measuring p50 and p99 response time, plus override rate.
>
> **Phasing**:
> - Phase 1 (0-3 mo): shadow-mode predictions, no dispatcher impact, baseline data
> - Phase 2 (3-6 mo): opt-in recommend to top-quartile dispatchers (volunteer)
> - Phase 3 (6-12 mo): default-on, dispatchers override if needed
>
> I'd want to flag **two scope risks**: (1) data quality on ambulance GPS — if it's unreliable we're cooked; (2) political — the city's existing dispatch vendor will resist us replacing them. I'd want a pre-engagement with their CTO before we commit to a timeline."

⏱️ ~5 minutes spoken。剩下 55 分钟交给面试官 deep-dive 任何 component。

---

## 简历专属 reframe（Gao Xin 简历专用）

你的 **debt collection voice agent** 项目跟这道题**结构上高度同构**：

| 911 题 | 你的 voice agent |
|---|---|
| Multi-source data (calls / traffic / GPS) | Multi-source data (customer profile / call history / repayment status) |
| Real-time decision under time pressure | Real-time conversation under latency pressure (p99 < 800ms streaming) |
| Stakeholder mismatch (mayor vs police vs fire) | Stakeholder mismatch (legal vs ops vs product across 7 markets) |
| Safety-critical, fallback to human | Trust-critical, fallback to human agent |
| Hard to A/B (ethics) | Cross-market A/B testing — 你做过 |
| Shadow-mode → opt-in → default-on phasing | RL alignment 你也是 phase-by-phase 上的 |

**面试时可以主动说**：

> "Actually this problem structure mirrors something I just shipped — a voice AI agent for debt collection across 7 markets. Same shape: multi-source data, real-time decision, safety-critical with human fallback, hard to A/B because the controlled-experiment is ethically tricky. I used a **shadow-mode → opt-in → default-on phasing** for that rollout, which I'd reuse here."

→ 这一招立刻把你从"FDE candidate"升级到"FDE who has already done this in production"。

---

## 5 个常见 follow-ups

**Q1**: "What if the city has bad GPS data on ambulances — 30% of pings are stale?"
**A**: 先 measure stale rate per ambulance per time-of-day → identify if it's vehicle-specific (broken hardware) vs systematic (e.g., GPS dead in tunnels). For systematic gaps, layer in **dead reckoning** (last known position + heading × elapsed time). For broken hardware, flag to ops for fleet remediation. Model itself: degrade to "any nearby available ambulance" if stale rate > 50% in that region.

**Q2**: "Mayor wants results in 6 weeks not 12 months."
**A**: 时间压缩 → narrow scope。6 周做不完 ML routing，但能做**dashboard + manual decision support**：把"哪辆 ambulance 在哪 / 当前 traffic 怎样 / 推荐谁出动"实时给 dispatcher 看，**还是 dispatcher 决定**。这是 deterministic + transparent，6 周可行。Mayor 还是能 announce "AI-assisted dispatch saving lives"。**逆向 scope 是 FDE 核心技能**。

**Q3**: "How do you avoid getting the city sued when an ambulance is misrouted?"
**A**: 3 个 legal-safe defaults：
1. **Recommendation, not decision** — dispatcher always has final call, audited.
2. **Conservative threshold** — recommend only when model confidence > 80%, fall back to traditional dispatch otherwise.
3. **Full audit log** — every recommendation + override + outcome logged immutable for legal review.

**Q4**: "City's dispatch vendor (e.g., RapidDeploy) doesn't want to integrate. What do you do?"
**A**: This is **the actual blocker**, not technical. 3 options:
1. **Side-car**: read-only access to dispatch logs, recommendations shown in separate UI to dispatcher. Vendor doesn't have to change anything.
2. **Vendor partnership**: bring vendor in as joint go-to-market partner, give them rev share.
3. **City RFP**: get city to mandate API access in vendor renewal. Slow but durable.

Most FDE situations end up as #1 (side-car) — minimizes vendor politics.

**Q5**: "If the model performs worse than dispatchers' intuition, what do you do?"
**A**: First — **don't take it personally**. Dispatchers have years of context. The right framing is "the model is a 90th-percentile assistant for a 95th-percentile expert" — useful for the 10% of cases where the expert is new / tired / stressed, harmful if it overrides the expert in normal cases. So: track **override rate vs outcome** carefully. If overrides have better outcomes than non-overrides, **the model needs retraining on the dispatcher's decisions**, not deployment.

---

## ❌ 易错点

1. **一上来就画 architecture** — 没 clarify，方案脱离 stakeholder 实际需求。
2. **把它当 system design 题做** — 算 QPS / DB shard。不是这道题在考的。
3. **忽略 dispatcher 这个角色** — 把人类完全 cut out 是 safety-critical 系统的红旗。
4. **没说 phasing** — "6 个月一次性上线"在 FDE 面试官眼里 = 没部署过任何东西。
5. **忽略数据质量** — 假设 GPS / traffic 完美。**FDE 全职在跟脏数据死磕**。
6. **不主动 surface failure modes** — 等面试官追问 = 失分。
7. **答案太长，没给面试官追问的空间** — 6-7 分钟讲完，剩下 50 分钟 deep-dive，是节奏目标。

---

## ✅ 加分项

1. **Shadow-mode → opt-in → default-on phasing** 主动提
2. **Override rate as a North Star metric** ——把"用户信任"量化成 metric
3. **Side-car integration pattern** 应对 vendor 政治
4. **Legal-safe defaults**（recommendation not decision / audit log）
5. **Dead reckoning** 处理 GPS gap — 体现你处理过脏数据
6. **Before/after with same-period control** 替代 A/B 因为 ethics
7. **Quote a real number from your past work** — 用 voice agent 的具体经验加权重

---

## 11. Cheat sheet (面前 5 min 看)

```
不要做:
  - 上来画图 / 算 QPS
  - 假设你知道 stakeholder
  - 一次讲完整方案，留空白

要做:
  1. 5 个 clarifying 问题先问
  2. Scope 到一个 sub-problem
  3. 3-layer architecture sketch
  4. Deep dive 1 component
  5. Surface failure modes 主动
  6. Phasing: shadow → opt-in → default

关键 phrases:
  - "Let me ask a few things before designing..."
  - "I'd narrow this to..."
  - "Before being asked, I want to flag..."
  - "This mirrors something I shipped at TikTok..." (用 voice agent)
  - "I'd phase this..."

数字 anchors (随机选 2-3 个引用):
  - 4 周 shadow mode
  - MAE < 90s for ETA
  - 80% model confidence threshold
  - Override rate < 30% target
```
