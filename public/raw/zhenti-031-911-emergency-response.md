## Q31 · 911 急救响应时间优化

> "A major US city wants to **reduce 911 emergency response time**. You have access to **911 call data, real-time traffic data, and ambulance GPS data**. You have **60 minutes**. **Go**."

**中文翻译**:

> "美国某大城市想 **降低 911 急救响应时间**. 你能拿到 **911 通话数据、实时交通数据、救护车 GPS 数据**. 给你 **60 分钟**. **开始**."

**Round**: Decomposition Case (60 min)
**出处**: Exponent 2026 FDE · Palantir FDE 经典题, 后被 OpenAI / Google / Salesforce / Databricks 全部复用
**行业**: Public safety / municipal / healthcare

---

## 📖 术语速查 (本题用到的)

> 这题里的专业词如果不懂, 听都听不下去. 这张表 5 min 看完, 后面就跟得上.

### 911 / 公共安全行业

| 术语 | 解释 |
|---|---|
| **PSAP (Public Safety Answering Point)** ⭐ | 911 接警中心 — 接电话 + 派遣的物理设施 + 团队. 美国大城市通常 1-3 个 PSAP. **PSAP 接警员是工会**, 引入 AI 会触动饭碗, 是这题最高政治风险. |
| **CAD (Computer-Aided Dispatch)** ⭐ | 计算机辅助调度系统 — PSAP 用的核心软件, 记录 call → dispatch → arrival 全流程. 主流厂商: **Motorola, Tyler, Hexagon**. |
| **Dispatcher (调度员)** | 在 PSAP 工作的人, 接电话 + 决定派哪辆车 + 跟车上沟通. 跟 call-taker 有时分开 (call-taker 接电话, dispatcher 派车). |
| **Call-to-dispatch / Dispatch-to-arrival** | 911 response time 拆成 3 段: call processing (90s P90 标准) + turnout (60s) + travel (240s). 不同段 bottleneck 完全不同. |
| **NFPA 1710** | 美国消防协会标准 — 城市 EMS 必须在 6.5 min P90 内 call-to-arrival. 这题的 industry baseline. |
| **EMS (Emergency Medical Services)** | 急救服务 — 救护车 + paramedic. **EMS director** 是这题关键 stakeholder. |
| **Cardiac arrest "golden 4 minutes"** | 心脏骤停 4 分钟内 CPR / AED 生存率最高, 超过 10 min 几乎无法救活. 这题 P90 cardiac response 是 north-star metric. |
| **Mental health crisis call** | 911 接的精神危机电话 — 优化策略跟 cardiac 完全不同, 很多城市改派 civilian responder 而非警察. |
| **CJIS (Criminal Justice Information Services)** | FBI 的执法数据合规标准 — 911 数据涉及 CJIS, 类似 HIPAA 但更严. 数据加密 + access control 必做. |
| **HIPAA** | 美国医疗隐私法 — 911 涉及医疗数据 (cardiac arrest 是医疗) 必合规. |
| **Equity gap (公平性差距)** | 低收入 / 少数族裔街区的 911 response time 平均比富人区慢 50%+. 是这题 explicit 的 counter-metric, 不能 widen. |

### 数据 / 系统厂商

| 术语 | 解释 |
|---|---|
| **Motorola CAD / Tyler / Hexagon** | 3 大 CAD 厂商. 这题 likely Motorola. 集成必经 vendor. |
| **Zoll / ImageTrend** | EMS 行业的车载系统 + GPS 数据厂商. Zoll 是市占第一. |
| **INRIX** | 实时交通数据 SaaS, 美国城市常买. Google Maps API 是替代品. |
| **NMEA stream** | 标准 GPS 数据格式. Ambulance GPS feed 走 NMEA. |
| **HL7** | 美国医疗信息交换标准 — 医院 ED status 走 HL7. |
| **12 timestamps per incident** | 标准 CAD 一个 incident 记录 12 个时间戳 (call_received → connected → classified → cad_submit → dispatcher_received → unit_selected → notified → ack → enroute → arrived ...). 是 funnel diagnose 的核心数据. |

### 方法论 / 部署模式

| 术语 | 解释 |
|---|---|
| **Walking skeleton (走骨头)** ⭐ | 最薄端到端版本, 每个组件可以 mock 但流程全跑通. 跑稳后再换真组件. **Decomposition 题标准 MVP 方法论**. |
| **Shadow mode (影子模式)** | AI 跟人并跑, AI 决策**只记录不生效**, 收集真实数据但不影响线上. Safety-critical 必经. |
| **Opt-in / Default-on** | 渐进 rollout: shadow → 几个志愿者 opt-in → 全员 default-on (但可 override). |
| **Stepped wedge rollout** | 分批 rollout — 不是 A/B 切一半, 而是按时间窗 / 区域分批上, 每批观察后才上下一批. 适合 ethics 不能 A/B 的场景. |
| **Counterfactual replay** | 反事实回放 — 把 AI 跑在历史 incident 上, 比较 AI 预测的 ETA vs 实际 ETA. 不是真 ground truth, 但能给早期信号. |
| **Override rate (覆盖率)** | dispatcher 推翻 AI 推荐的比例. 是这题的 north-star process metric — 太低 (<10%) = rubber-stamp, 太高 (>50%) = 模型烂. **20-30% 是 sweet spot**. |
| **Recommendation, not decision** | AI 给推荐, 人做最终决定. Safety-critical 的红线, 否则 legal liability + 工会反对. |
| **Dead reckoning** | 当 GPS 信号断 (隧道 / 大楼里), 用 "last known position + heading × elapsed time" 估算当前位置. 5-15% 的 ambulance ping 要 fallback 这个. |
| **Kill switch** | 一键禁用 AI 回到 manual mode. < 60s 触发. Safety-critical 必备. |

### 数据 / ML 性能

| 术语 | 解释 |
|---|---|
| **P50 / P90 / P99** | Latency / response time 的百分位 — P90 = 90% 的 case 在这数以下. Mayor 关心平均, EMS director 关心 P99 (最坏情况救人). |
| **MAE (Mean Absolute Error)** | 平均绝对误差 — ETA 预测的标准指标. 这题 target MAE < 60s. |
| **GBDT (Gradient Boosted Decision Tree)** | 梯度提升决策树 — tabular 数据上的 baseline 选择, 比 deep learning 稳. ETA 预测首选. |
| **ASR (Automatic Speech Recognition)** | 自动语音识别 — 911 call audio → text. LLM 处理前的入口. |
| **LLM-assisted call processing** | 用 LLM (e.g. Gemini Flash) 边听 call 边提取 symptom, 自动填 CAD 字段, call-taker 只 confirm. 这题省 30-60s/call. |

### 角色 / 政治

| 术语 | 解释 |
|---|---|
| **PSAP union (接警员工会)** ⭐ | 911 dispatcher 工会 — **这题最高政治风险**, 能 kill 项目. 第一周必须 PSAP president 在 launch readme 上 co-sign. |
| **Mayor's office** | 市长办公室 — buyer, 要 PR / 选举 quick win. 在意 average response time (面向公众). |
| **EMS director** | 急救主任 — 在意 patient outcome + paramedic safety. |
| **City CTO** | 市政府首席技术官 — 管系统集成 + 安全. |
| **CJIS officer** | 城市的 CJIS 合规官 — 必 sign-off. |
| **Citizen advocacy group** | 公民倡导团体 — 关注 equity, 会公开盯着 dashboard. |

---

## 这道题在考什么

**不是**: 考你能不能 design 一个 911 系统的方案.

**是**: 考你**面对一个 unbounded、safety-critical、多 stakeholder、多 data source 的真实部署问题, 能不能在 60 min 内做出 structured decomposition**.

具体看 4 个 signal:

1. **Clarify before solving** (先 clarify 再 solve) — 一上来就画 architecture / 算 QPS = 失分. FDE 圈共识: "Jumping to answers is an immediate red flag" (直接跳到答案 = 立刻 red flag)
2. **Tractable MVP** (可交付的 MVP) — 你能从一个 unbounded 问题里切出一个 **2-3 周交付 + 测得到 KPI 的最薄 walking-skeleton** (走骨头)
3. **Surface tradeoffs proactively** (主动暴露 tradeoff) — 在面试官追问前主动说「这个方案的失败模式是 X / Y / Z」
4. **Safety-critical mindset** (安全关键思维) — 911 是生死线. 你必须表现「一条命就是一条命」, 不是把它当 normal SaaS

---

## ❌ 最常见的挂法 (top 3)

**挂法 #1: 一上来就冲 ML routing 算法** (上来就讲 ML routing 算法)

> 候选人 (5 秒内): "Sure, I'd train a graph neural network on historical traffic + GPS, predict ETA, build a recommendation system, deploy on Kubernetes..."

死. 你**没问**:
- 是 call-to-dispatch 慢, 还是 dispatch-to-arrival 慢? (你都不知道 bottleneck 在哪)
- "Response time" 是 P50 还是 P90? Mayor 关心 PR average, EMS director 关心 P99
- 哪个 call category? Cardiac 跟 mental health 的优化策略完全不同
- 已经有什么 system 在 production? (PSAP / CAD / Motorola / Tyler 等)
- Equity concern (低收入街区 vs 高收入街区响应时间差异) 是 explicit goal 吗?

**挂法 #2: 当 system design 题做** (把它当系统设计题答)

候选人开始算: 「30K calls/day → 350 calls/sec peak → 5 个 PSAP shards → Redis cache → Kafka topic...」

死. 这道题**不是 system design**. 60 min 全花在 capacity planning + sharding = miss the point.

**挂法 #3: 把 dispatcher 完全 cut out** (把调度员完全 cut 掉)

> "AI will replace dispatchers and pick the optimal unit autonomously."

死. Safety-critical 系统的红旗. PSAP 工会会立刻 kill 你的 project. **永远 recommendation, 不 replace**.

---

## 完美答案架构 (5 步拆解 + 本题具体应用)

下面就是 FDE 在这道题里**完整的 60 分钟脚本**, 严格按 5 步走.

---

### Step 1: 澄清问题 (10 min)

> "Before I start designing, I want to ask 8 questions. The reason: '911 response time' is **3 totally different problems** depending on what we mean."

**8 个 clarifying questions**:

> **Q1**: "When you say 'response time', do you mean **call-to-dispatch** (call connect → dispatcher sends unit) or **dispatch-to-arrival** (unit dispatched → on scene)? These are very different bottlenecks. Industry standard NFPA 1710 measures **call-to-arrival** with 90s call processing + 60s turnout + 240s travel = 6.5 min P90."

> **Q2**: "What's the **single KPI** you'd put in your annual report — average response time? P90? P99? Response time for cardiac specifically? Equity gap between richest and poorest zip code?"

> **Q3**: "Which **call category** matters most? Cardiac arrest (golden 4 minutes) vs structure fire (6.5 min P90 target) vs mental health crisis (different intervention, often 30+ min OK). The optimization is per-category."

> **Q4**: "What's the **current baseline**? P90 today? And what's the **target** — 10% improvement (statistical noise threshold) or moonshot 50% (would need new dispatch policy)?"

> **Q5**: "What's **already in production**? PSAP using Motorola / Tyler / Hexagon CAD? Are ambulances tracked via vendor (Zoll, ImageTrend) or city-owned GPS? Is there a real-time traffic feed (city DOT, INRIX, Google)?"

> **Q6**: "What's the **integration constraint** — read access to dispatch system, or just batch dumps overnight? Real-time GPS feed from ambulances, or 5-min sampled? On-premise required, or cloud OK?"

> **Q7**: "**Equity concern explicit?** Many cities have 50% longer response times in low-income / minority neighborhoods. If we just optimize 'average', we may **widen** the gap. Is **equity** an explicit success metric?"

> **Q8**: "What's the **stakeholder map** — mayor's office, PSAP director, EMS director, fire chief, police chief, PSAP union (接警员工会), city CTO, city legal (HIPAA / CJIS), citizen advocacy groups? Who has veto?"

**为什么这 8 个 Q 重要**: 不问 → 你的 architecture 全错. 问完, 你已经 narrow 到 1 个具体子问题, 而不是 unbounded.

**面试官 likely 回答** (Exponent guide 给的典型 setup):
- KPI: P90 cardiac response time
- Baseline: 8:42 currently, target 7:00
- Current systems: Motorola CAD + Zoll for EMS
- Integration: read-only API, real-time
- Equity: yes, secondary metric (gap between top-quartile and bottom-quartile zip codes)
- Stakeholder veto: PSAP director + PSAP union

→ 现在你 scope 清晰了. **不是「优化整个 911 系统」, 是「在 90 天内将 cardiac arrest P90 response time 从 8:42 降到 7:00, 同时不让 equity gap 扩大」**.

---

### Step 2: 找干系人 + 成功指标 (10 min)

> "Now let me map stakeholders, because **whose buy-in we need determines what we can ship**."

**Stakeholder map**:

| Stakeholder | 在意什么 | 对项目态度 | 我对他们的关键动作 |
|---|---|---|---|
| **Mayor's office** | PR / press release / 选举 | Enthusiastic, 要 quick win | Quarterly metric review + press kit |
| **PSAP director** | Daily operations, dispatcher morale | Cautiously supportive | Daily standup, ride-along |
| **EMS director** | Patient outcomes, paramedic safety | Supportive but skeptical | Show survival rate impact |
| **Fire chief** | Cross-jurisdiction coordination | Skeptical of "AI dispatch" | Side-car integration, no policy change |
| **Police chief** | Officer safety, 911 misuse | Tangential | Read-only, no police dispatch v1 |
| **PSAP union** | Job security, workload | **Highly skeptical, can veto** | Early engagement, training, "augment not replace" |
| **City CTO** | Integration, security | Need approval | Architecture review, CJIS compliance |
| **City legal** | HIPAA / CJIS / liability | Must approve | Audit log, recommendation-not-decision |
| **Citizen advocacy** | Equity, transparency | Watching | Public dashboard with equity metric |

**Key insight**: PSAP union 是 highest-risk stakeholder. 美国 911 接警员是工会, 引入 "AI" 触动饭碗会 kill the project. **第一周必须**: PSAP president 在 launch readme 上 co-sign.

**Success metrics (3 层)**:

**Layer 1 — North Star** (mayor will see):
- P90 cardiac arrest call-to-arrival time (target 7:00 from 8:42)

**Layer 2 — Operational** (PSAP director sees daily):
- Override rate of AI recommendations (target 20-30%, NOT < 10%)
- AI uptime (target 99.9%)
- Per-shift recommendation latency P99 (target < 500ms)

**Layer 3 — Outcome** (EMS director, monthly):
- Cardiac arrest survival rate (lags 30-60 days)
- Equity gap: P90 in bottom-quartile zip codes vs top-quartile (must NOT widen)
- Citizen satisfaction (survey)

**Counter-metrics** (must not move negatively):
- Mental health crisis response time (some cities use civilian responders, must not be deprioritized)
- Dispatcher reported workload survey
- Equity gap

---

### Step 3: 梳理输入数据 (10 min)

> "Let me inventory the data we have, who owns it, the format, freshness, and the gaps. Half of FDE work is fighting dirty data, so this matters more than the model."

**Data inventory**:

| Dataset | Owner | Format | Freshness | Quality / Gap |
|---|---|---|---|---|
| **911 call records** | PSAP (city) | CAD export, structured | Real-time | Some free-text fields (call notes) need NLP |
| **Call audio** | PSAP | mp3 / wav | Real-time stream | HIPAA / CJIS, encryption required |
| **CAD incident events** | Motorola CAD | API, structured | Real-time | 12 timestamps per incident (call_received → arrived) |
| **Ambulance GPS** | Zoll / city fleet | NMEA stream | 5-30s intervals | **5-15% stale or drift in tunnels / buildings** |
| **Real-time traffic** | City DOT / Google / INRIX | API | 30s-2min lag | Some sensors broken, gaps in coverage |
| **Historical incidents** | CAD archive | Daily batch | T+1 | 2-5 years available, schema changed 2x |
| **Weather** | NOAA | API | Hourly | Reliable |
| **Event calendar** | City permits + sports | CSV / API | Daily | Manual updates, incomplete |
| **Census / demographics** | US Census | Static | Annual | For equity analysis |
| **Hospital ED status** | Health system | HL7 | 15-min | Some hospitals don't share |

**Key gaps**:

1. **Stale GPS** is the #1 fight. Tunnels, garages, indoor incidents → 5-15% of pings stale > 60s. **Fallback**: dead reckoning (last known position + heading × elapsed time).
2. **Schema drift** in historical CAD. Have to write per-period parsers.
3. **Cross-jurisdiction**: 911 calls from city edge may belong to neighboring county. Boundary disputes 5% of cases.
4. **Free text in call notes**: dispatcher / call-taker shorthand ("PT C/O CP" = patient complains of chest pain). Need parser.

**Who I'd call in week 1**:
- PSAP IT lead — get me CAD API credentials
- Zoll account manager — confirm GPS data sharing agreement
- City DOT data engineer — traffic feed access
- HIPAA / CJIS officer — encryption + access controls

---

### Step 4: 拆成可解子问题 (15 min)

> "Now I have scope + stakeholders + data. Let me decompose the problem into subproblems, ranked by risk × value, so we attack highest-risk-highest-value first."

**Decomposition: 7 subproblems**:

| # | 子问题 | Risk | Value | Pri |
|---|---|---|---|---|
| **A** | Funnel diagnose: 12-timestamp dashboard, identify biggest bottleneck | Low | Very high | **1** |
| **B** | ETA prediction model (replace dispatcher's intuition for unit selection) | Med | High | **2** |
| **C** | Real-time traffic-aware routing for already-dispatched units | Low | Medium | 4 |
| **D** | LLM-assisted call processing (extract symptoms while call-taker types) | Med | High | **3** |
| **E** | Resource pre-positioning (where to park idle ambulances) | High | High | 5 |
| **F** | Cross-jurisdiction handoff optimization | Low | Low | 7 |
| **G** | Equity-aware dispatch policy (ensure dispatch doesn't widen gap) | High | Critical | **must run alongside everything** |

**Sequencing rationale**:

> **A first** because: without funnel diagnose, you don't know what to fix. PSAP director's first reaction when I show "Classify takes 180s P90 for non-emergency, that's the biggest leak" will be "**finally someone showed me this**". That builds trust.

> **B second** because: highest single-lever value (dispatcher decision time + selection quality), and tractable with 6 months of historical data. GBDT baseline, MAE target < 60s P90.

> **D third** because: LLM-assisted call processing is the fastest call-to-dispatch saver. ASR + Gemini Flash extract symptoms in real-time → auto-fill CAD fields → call-taker just confirms. Saves 30-60s per call.

> **G runs alongside** because: if I optimize "average" without watching equity, I may widen the gap (model learns "rich zip codes get faster response because there are more units there"). **Equity is a check on every other subproblem**, not a separate phase.

> **E and F deferred** to phase 2/3 because: pre-positioning is high-risk (paramedic union pushback), cross-jurisdiction is low value (5% of cases).

---

### Step 5: Walking-skeleton MVP (15 min)

> "Now the most important part: what's the **minimum end-to-end thing we can ship in 2 weeks** that proves the architecture, even with mocked logic?"

**Walking-skeleton (Week 1-2)**:

```
[CAD events stream]──┐
                     ├─→ [Telemetry collector] ──→ [Postgres + S3]
[Ambulance GPS]──────┘                                    │
                                                          ▼
                                              [Funnel Dashboard]
                                                          │
                                                          ▼
                                                 [PSAP director]
                                                  reviews daily
```

**Week 1**:
- Day 1-2: Get CAD API credentials, ingest last 30 days of incident events
- Day 3-4: Build 12-timestamp ETL → Postgres
- Day 5: Build first dashboard (P50 / P90 / P99 by call category)

**Week 2**:
- Day 6-7: Ride-along with 1 dispatcher per shift × 3 shifts (morning / evening / night)
- Day 8-9: Show dashboard to PSAP director, get feedback
- Day 10: Identify top 1 bottleneck → that's Phase 2 scope

**What's NOT in Week 1-2 MVP**:
- No ML model. Just descriptive analytics.
- No dispatcher UI change. Just internal dashboard.
- No real-time decisions. Just batch-refreshed metrics.

**Why this works**:
- **No risk** to dispatcher workflow (read-only)
- **Immediate value** (PSAP director never had this dashboard)
- **Foundation for everything** (without this, ML model has nothing to compare to)
- **Trust builder**: PSAP director sees you understand his domain in 2 weeks

**Phase 2 (Week 3-12) — ETA Prediction in Shadow Mode**:

After Funnel says "Dispatcher decision time is 25s P90, that's the biggest fixable bottleneck":

```
[Incident comes in]
      │
      ▼
[ETA model predicts arrive time for each candidate unit]  ← SHADOW
      │
      ▼
[Dispatcher selects unit manually (current process unchanged)]
      │
      ▼
[Log: AI recommended unit X (ETA Ys), human picked Y (actual ETA Zs)]
      │
      ▼
[Weekly retro: agreement rate, MAE, where AI was wrong]
```

**Success criteria for Phase 2**:
- ETA MAE < 60s on P90 ground truth
- AI recommendation matches dispatcher's pick > 70% of time
- For mismatches, AI's prediction is within 30s of actual on average

**Phase 3 (Month 4-6) — Opt-in Recommendation Mode**:

5 self-selected dispatchers see AI recommendation in UI sidebar (not blocking). Override rate tracked. Weekly retro.

**Phase 4 (Month 7-12) — Default-on with Override**:

All dispatchers see recommendation. Always can override with 1 click. Continuous monitoring.

**Kill switch**: ops can disable AI assist in < 60 seconds. Manual mode is the default fallback.

---

## 详细回答 (Sample 60-min monologue)

> "Let me make sure I understand what success looks like before I sketch a solution. I want to ask 8 quick questions.
>
> **First**: when you say 'response time', is that call-to-dispatch or dispatch-to-arrival? Industry breaks it into 90s call processing + 60s turnout + 240s travel = 6.5 min P90 standard. The bottlenecks for each are totally different problems — call processing is a UX + LLM problem, travel is a routing + traffic problem.
>
> **Second**: what's the single KPI in the mayor's annual report? Mean response time? P90? Or P90 specifically for cardiac arrest? Because the optimization is per-category.
>
> ... *(continues with 6 more clarifying questions)* ...
>
> *(After answers: P90 cardiac, 8:42 → 7:00 target, 90 days, Motorola CAD, Zoll EMS, equity is secondary metric, PSAP union has veto)*
>
> OK so the actual problem is: in 90 days, drop P90 cardiac call-to-arrival from 8:42 to 7:00, without widening the gap between top-quartile and bottom-quartile zip codes, with PSAP union buy-in.
>
> **Stakeholders**: mayor wants press release, PSAP director wants operational stability, PSAP union has veto, EMS director wants survival rate impact, city legal wants HIPAA/CJIS compliance. **Highest risk stakeholder is the PSAP union** — I'd schedule a meeting with their president in week 1 before any tech work.
>
> **Data**: 911 call records + CAD events + Zoll GPS + city traffic. I'd expect 5-15% GPS stale rate (tunnels, garages) — that's the dirty-data fight I'd plan for.
>
> **Decomposition**: 7 subproblems, ranked by risk × value:
>
> 1. **Funnel diagnose** — what's actually slow? Without this, everything else is guessing.
> 2. **ETA prediction** — replace dispatcher intuition for unit selection
> 3. **LLM-assisted call processing** — save 30-60s on call-taker info gathering
> 4. **Real-time routing** — already-dispatched units get traffic-aware route
> 5. **Resource pre-positioning** — where to park idle units (high political risk, defer to phase 3)
> 6. **Cross-jurisdiction handoff** — only 5% of cases, low value, defer
> 7. **Equity-aware dispatch** — runs **alongside** everything as a check, not a phase
>
> **Walking-skeleton MVP for Week 1-2**: just the funnel dashboard. No ML. Read-only. Ingest last 30 days of CAD events, build 12-timestamp ETL, show PSAP director where time is being lost. This is **immediately valuable** to him (he never had this view) and **risk-free** to dispatchers. It builds the credibility I need before I propose anything that touches their UI.
>
> **Phase 2 in Week 3-12** is the ETA model. Critical: **shadow mode**. AI predicts ETA for each candidate unit, dispatcher still picks manually, we log both. Weekly retro. We don't show AI's recommendation to dispatchers until MAE < 60s on real ground truth and agreement rate > 70%.
>
> **Phase 3 in Month 4-6**: 5 self-selected dispatchers see AI recommendation as sidebar, opt-in. Override rate becomes north-star — target 20-30% — not 5% (that means dispatchers rubber-stamp) and not 60% (that means model is wrong).
>
> **Phase 4 in Month 7-12**: default-on, always overridable, kill switch ops can pull in 60 seconds.
>
> **Three things I'd flag proactively before you ask**:
>
> **(a) PSAP union risk**. Project dies politically before it dies technically if I don't pre-engage. I'd want union president co-signing the launch readme.
>
> **(b) Equity is a check, not a phase**. If I optimize aggregate P90 without watching equity, the model learns 'rich zip codes have more idle units, recommend faster response there'. Equity metric on the dashboard from day 1, red-flagged if it widens.
>
> **(c) Eval methodology**. We can't A/B test 911 ethically (can't deny half the city the improvement). Instead, **stepped wedge rollout** by district + **counterfactual replay** (run the AI on historical incidents, compare predicted ETA to actual). Counterfactual is directional, not ground truth — but it gives us early signal before lagging outcomes catch up.
>
> Want me to deep-dive any of these layers?"

---

## Gao Xin 简历专属 reframe

这道题跟你**TikTok PayLater Indonesia voice agent** 项目**结构上高度同构**, 你直接 quote:

> "Actually this is very close to a problem I just shipped. The TikTok PayLater debt collection voice agent serves 7 markets, 6 languages, with strict regulatory constraints (especially OJK in Indonesia). The structure is the same:
>
> - **Multi-source data** under time pressure (customer profile + call history + repayment + blacklist + transaction context, just like 911's call + CAD + GPS + traffic)
> - **Real-time decisions** with sub-second latency requirement (p99 < 800ms for streaming, just like dispatch decision)
> - **Safety / trust critical** with regulatory exposure (OJK could revoke license, just like 911 union could kill project)
> - **Hard to A/B** because of fairness concerns (can't subject one market to worse service, same as can't deny half a city of 911 improvement)
> - **Multi-stakeholder** with veto holders (legal, ops, product, monitor) just like PSAP director + union + EMS + city legal
>
> The framework I used there was the same 5-step I just walked through:
>
> 1. **Clarified scope**: not 'replace all human collection', but 'first-line for non-disputed accounts where customer hasn't said the magic word "law" or "regulator"'.
> 2. **Stakeholders + KPI**: OJK monitor approval (north-star), customer NPS (counter-metric), repayment rate (operational), complaint rate (red line).
> 3. **Data inventory**: I spent week 1 listing what was clean vs dirty. The 'customer recent call attempts' field was missing for 8% of accounts and the team treated it as 0 — I caught that.
> 4. **Decomposed** into 6 subproblems, attacked highest-risk-highest-value first: **intent classifier first** (so I knew which calls to route to bot vs human), then dialog policy, then RL alignment, then multi-language.
> 5. **Walking-skeleton MVP**: I shipped a single-intent (payment reminder) version in 2 weeks with mocked LLM responses (literally `if intent == 'paid': return scripted_message`). That walked through the entire ASR → intent → dialog → TTS → escalation pipeline end-to-end. Once that was stable, I swapped in real LLM intent classifier, then real dialog policy. **Two weeks to end-to-end, four months to production at the same architecture I sketched in week 1**.
>
> The pattern that transfers to 911: **don't build the smartest piece first, build the dumbest end-to-end first, then upgrade in shadow mode**."

**Other transferable resume hooks**:

- **ConvFinQA ablation methodology** — for the "negative result that taught us something" angle when AI underperforms. In ConvFinQA work, I systematically ablated retrieval quality, prompt format, and CoT to find which knob actually mattered. Same systematic ablation would apply to "is ETA error from data freshness, model class, or feature set".
- **Internal Agent Platform onboarding multiple teams** — for the "multi-stakeholder ambiguous scope" angle. When 5 different teams want different things from the same platform, you have to do clarification + scope + walking-skeleton on each.

---

## 5 个 Follow-ups

**Q1**: "What if PSAP union refuses to participate at all?"

**A**: Don't proceed. The political risk to your company > one deal value. But before walking away, escalate: **what's the union's actual fear?** Usually it's "AI will replace my job" — and the union president is wrong to think that's the immediate risk. Real fear: more scrutiny on individual dispatcher decisions (every override now audited).
- **Counter-offer**: union gets to design the recommendation UI (they decide what AI shows / how prominent), union gets first 6 months of override data **redacted from individual dispatcher attribution** (only aggregate), union has a seat on the eval steering committee.
- If that fails — politely decline the project. Don't ship into political quicksand.

**Q2**: "What if the city's CAD vendor (Motorola) blocks integration?"

**A**: This is the **actual blocker**, not technical. 3 options:
- **Side-car**: read-only access via daily CAD log export → ingest into our system → recommendations shown in **separate dashboard** that dispatcher checks in parallel. Vendor doesn't have to change anything.
- **Vendor partnership**: bring Motorola in as joint go-to-market, give them rev share. Slow but durable.
- **City RFP leverage**: get city to mandate API access in vendor renewal. Slowest, most political.

Most FDE situations end up as #1 (side-car) — minimizes vendor politics and gets you shipping in weeks not quarters.

**Q3**: "What if the ETA model performs worse than dispatcher intuition?"

**A**: First — **don't take it personally**. Dispatchers have years of context (this driver is fast, this corner floods, this building's loading dock is on Main not Elm). The right framing is: "**the model is a 90th-percentile assistant for a 95th-percentile expert**" — useful for the 10% of cases where the expert is new / tired / stressed / overloaded, harmful if it overrides the expert in normal cases.

So: track **override rate vs outcome** carefully. If overrides have better outcomes than non-overrides, the model needs retraining on the dispatcher's decisions, not deployment. If overrides have similar outcomes, model is fine, dispatcher and model agree often. If model has better outcomes than overrides on average **but worse on specific categories** (e.g., model worse on mass casualty events because training data is sparse), gate the model to its strong categories.

**Q4**: "How do you avoid getting the city sued when an ambulance is misrouted?"

**A**: 3 legal-safe defaults:

1. **Recommendation, not decision** — dispatcher always has final call, audit log shows dispatcher acted.
2. **Conservative threshold** — recommend only when confidence > 80%, fall back to "show raw distance list, no preference" otherwise.
3. **Full audit log** — every recommendation + override + outcome logged immutable for legal review.

Plus: city legal should review the deployment, NOT just sign off on the contract. They need to see the actual recommendation UI and audit log before launch.

**Q5**: "Mayor wants results in 6 weeks for press release, not 90 days."

**A**: Time compression → narrow scope. 6 weeks doesn't do ML routing, but does:
- **Funnel dashboard** to PSAP director (week 1-2)
- **Manual decision support UI**: "current available units + their current location + current traffic-weighted distance" — no ML, just real-time deterministic display. Saves dispatcher 5-10 seconds per decision because they're not toggling tabs.
- **One press-friendly story**: "AI-assisted dispatch saving 8 seconds per cardiac call, saving X lives per year".

Mayor gets her announcement. PSAP gets a real improvement without rushed ML. **Reverse scoping is FDE's core skill** — anyone can add scope, FDE removes it.

---

## ❌ 死路答法 (top 7)

1. **一上来画 architecture** → 没 clarify, 方案脱离 stakeholder 实际需求
2. **当 system design 题做** (算 QPS / shard / Kafka topic) → 错位
3. **承诺 ML routing 6 个月一次性上线** → 没 phasing = 没部署过
4. **把 dispatcher 完全 cut out** → safety-critical 红旗
5. **假设 GPS / traffic 数据完美** → FDE 全职在跟脏数据死磕
6. **A/B test 半个城市** → 伦理灾难, 用 stepped wedge / counterfactual replay
7. **没考虑 PSAP 工会 / equity** → 政治盲点, 项目死于政治

---

## ✅ 加分项 (top 7)

1. **5 步框架显式讲出来** (clarify → stakeholder → data → decompose → MVP)
2. **8 个 clarifying questions 一次问完** 而不是 dribble
3. **Walking-skeleton MVP 2 周端到端**, 而不是 12 个月一次性
4. **Shadow → opt-in → default-on phasing** 主动提
5. **Override rate as a North Star metric** — 把「用户信任」量化
6. **Equity as a check, not a phase** — 显示你 think systemically
7. **Quote 你的 voice agent 7-market production experience** — 把 candidate 变 "shipped this before"

---

## 一句话总结

> **911 response time 优化 = "拆解 funnel 找最大瓶颈 + ML 协助但人最终决策 + shadow → opt-in → default 渐进 + 全程 instrumentation 暴露真相"**.
>
> 真正的 win 不来自一个炫酷 ML 模型, 而是「在 funnel 每段挤秒 + 让 dispatcher 信任 + 让 PSAP 工会同意 + 让 equity 不退步」.
>
> 60 分钟答题节奏: 10 min clarify → 10 min stakeholder + KPI → 10 min data → 15 min decompose → 15 min walking-skeleton MVP. 不省 step.

---

## Cheat Sheet (面前 5 min 看)

```
不要做:
  - 上来画图 / 算 QPS
  - 假设 stakeholder / KPI
  - 一口气讲完整方案
  - 把 dispatcher cut out
  - 假设数据 clean
  - A/B 切一半城市

要做 (5 step):
  1. Clarify (10min): 8 个 Q, 锁 KPI + 范围
  2. Stakeholder (10min): 9 角色表 + KPI 3 层
  3. Data (10min): inventory + gap 列表
  4. Decompose (15min): 7 subproblem 按 risk × value
  5. Walking-skeleton MVP (15min): 2 周 funnel dashboard

Step 1 必问 Q:
  - Call-to-dispatch vs dispatch-to-arrival?
  - P50 / P90 / P99?
  - 哪个 call category?
  - 当前 baseline + target?
  - 已有什么 system?
  - 集成约束?
  - Equity 是 explicit goal 吗?
  - Stakeholder veto 谁?

Stakeholder veto 候选人:
  - PSAP union (highest)
  - PSAP director
  - City legal
  - EMS director

Funnel 12 timestamps:
  call_received → connected → pickup → location
  → classified → cad_submit → dispatcher_received
  → unit_selected → notified → ack → enroute → arrived

7 subproblems (ranked):
  1. Funnel diagnose (risk 低, value 极高)
  2. ETA prediction (risk 中, value 高)
  3. LLM call processing (risk 中, value 高)
  4. Real-time routing (risk 低, value 中)
  5. Resource pre-position (risk 高, defer phase 2)
  6. Cross-jurisdiction (defer)
  7. Equity (alongside everything)

Walking-skeleton (Week 1-2):
  - 30 天 CAD events ingest
  - 12-timestamp ETL
  - Funnel dashboard
  - 3 dispatcher ride-along
  - 0 ML, 0 dispatcher UI change

Phasing:
  Phase 1 (W1-2): Funnel dashboard
  Phase 2 (W3-12): ETA shadow mode
  Phase 3 (M4-6): Opt-in for 5 dispatchers
  Phase 4 (M7-12): Default-on + kill switch

North-star metric: P90 cardiac call-to-arrival
North-star process metric: override rate 20-30% (NOT < 10%)

Failure modes:
  - GPS stale → dead reckoning
  - Traffic stale → no-traffic shortest path
  - Model low-conf → show raw list
  - CAD down → manual mode
  - Override > 50% → auto-pause

Eval:
  - Stepped wedge by district (NOT A/B half-city)
  - Counterfactual replay (directional, not ground truth)
  - Lagging metric: cardiac survival (30-60 day lag)
  - Equity check on every metric

Resume quote:
  "TikTok PayLater voice agent 7 markets — same structure:
   multi-source data, real-time, safety-critical, multi-stakeholder.
   I used same 5-step. Walking-skeleton in 2 weeks with mocked LLM."

Key phrases:
  - "Before I sketch, let me ask 8 things..."
  - "I'd narrow this to..."
  - "Before being asked, I want to flag..."
  - "Two-week walking-skeleton would look like..."
  - "Equity is a check, not a phase"
  - "Override rate is my north-star process metric"
```
