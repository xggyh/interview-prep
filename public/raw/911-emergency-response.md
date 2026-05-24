## 题目（verbatim）

> "A major city wants to use our platform to **reduce 911 emergency response times**. They have **911 call data, traffic data, and ambulance GPS data**. You have **60 minutes**. Go."

**出处 / 公司**：Palantir FDE 经典原版（这个 round 的「始祖」）。后被 OpenAI / Google / Salesforce / Databricks 全部复用。多个候选人在 Glassdoor / Medium / fde.academy 公开 report.

**Round**: Case Study / Decomposition (60 min, single-question)

---

## 这道题在考什么

**不是**：考你「做出一个 911 系统的方案」.
**是**：考你**面对一个庞大、模糊、含多个数据源的真实客户问题, 能不能在 60 min 内做出 structured decomposition + propose tractable MVP + surface tradeoffs**.

4 个评分轴:

1. **Clarify before solving** — 一上来就画图、写代码 = 失分. FDE 圈一个共识: "Jumping to answers is an immediate red flag"
2. **Tractable MVP** — 你能从一个无边界问题里切出一个**3 周能交付 + 测得到 KPI** 的最小版本
3. **Surface tradeoffs proactively** — 在面试官追问前就主动说「这个方案的失败模式是 X / Y / Z」
4. **Safety-critical mindset** — 911 是生死线. 你要表现「我知道一条命就是一条命」, 不是把它当 normal SaaS

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**911 (Emergency Response System)**: 美国 / 加拿大的紧急求助电话号码 (中国是 110/120/119, 英国 999, 欧洲 112). 用户拨号 → 被路由到当地 PSAP (Public Safety Answering Point, 接警中心) → 接警员 (call-taker) 接通 → 派警员 / 救护车 / 消防车. 这是一个**典型的多阶段管道**, 每一段都有延迟.

**Response Time** (响应时间): 行业最常用的定义是 **call received → first responder on scene** 的总时长. 分解成:
- **Call processing time** (接警耗时): call connect → dispatcher 派出第一辆车
- **Travel time** (出动到到达): vehicle dispatched → arrived at scene

NFPA 1710 标准对火灾响应的目标是 **call-to-arrival 90 秒接警 + 60 秒 turnout + 240 秒 travel = 6.5 分钟 (90 percentile)**. 心脏骤停的 medical 黄金时间是 **4-6 分钟**, 超过 10 分钟生存率从 40% 跌到 < 10%.

**CAD** (Computer-Aided Dispatch): 接警中心的核心软件, 负责显示来电、定位、可用警力、推荐 / 派遣车辆. 主流厂商: Motorola, Tyler, Hexagon, RapidDeploy. 这是 911 体系的「中央神经」.

**Dispatcher** (调度员): 不等于 call-taker. Call-taker 接电话采集信息, dispatcher 看 CAD 屏决定派谁 / 怎么走. 大城市这两个角色分开, 中小城市可能同一个人兼任.

---

## 2. 这个问题的核心是什么

设想没有任何工程介入的灾难场景:

```
14:23:04  报警人: "我妈胸口剧痛"
14:23:11  call-taker 接通
14:24:18  call-taker 录完症状, 提交 incident
14:24:45  dispatcher 看屏幕: 4 辆救护车可用, 都距离 8-12 分钟
14:25:30  dispatcher 凭经验选最近一辆 (其实第三近的因不堵车更快)
14:25:32  paramedic 接到指令, 还在喝咖啡
14:26:14  上车出发
14:34:48  到达现场 (因第二街口大堵, 比预期晚 3 分钟)

Total: 11 min 44 sec. 心脏骤停脑细胞死了大半.
```

**问题**:

- **接警阶段**: call-taker 录入耗时不可控 (1-2 分钟), 没有 LLM 帮忙摘要
- **派警判断**: dispatcher 凭直觉, 不知道实时交通
- **路径选择**: 救护车 GPS 导航是 consumer-grade, 不知道哪里在修路
- **资源配置**: 4 辆车都集中在市北, 市南此刻是空白
- **数据孤岛**: 911 call DB / CAD / GPS / traffic 四套系统, 互不相通

**工程介入的解法**:

```
1. ASR + LLM 实时摘要 call-taker 对话 → 接警阶段省 30-60s
2. CAD 集成实时交通 → ETA 预测精确到秒, 选车不再靠直觉
3. 路径规划: 实时绕开拥堵 / 施工
4. 资源 pre-position: ML 预测下小时热点, 提前调整 idle 救护车站位
5. 全链 OpenTelemetry trace, 暴露真实瓶颈
6. Human-in-the-loop: 所有 ML 决策 dispatcher 可一键覆盖
```

---

## 3. 典型流程图 / 时间分解

```
┌───────────────── 完整 911 响应链路 ───────────────────────────┐
│                                                              │
│   报警人拨号                                                  │
│      ↓ (5-15s 接通延迟)                                       │
│   PSAP call-taker 接通                                       │
│      ↓ (60-120s 信息采集 + CAD 录入)         ← 优化点 A       │
│   incident 推送到 dispatcher                                  │
│      ↓ (10-30s dispatcher 选车)              ← 优化点 B       │
│   CAD 通知 responder (车 + 警员)                             │
│      ↓ (30-90s turnout: 警员上车启动)        ← 优化点 C       │
│   出动                                                       │
│      ↓ (3-15 分钟 travel, 取决于距离 + 路况)  ← 优化点 D       │
│   到达现场                                                   │
│      ↓                                                       │
│   on-scene treatment / containment                          │
│                                                              │
│ 总响应时间 = call connect → arrived 全程, 目标 < 6.5min P90    │
└──────────────────────────────────────────────────────────────┘

可优化点 4 个:
A. Call processing: ASR + LLM 实时摘要协助 call-taker
B. Dispatcher decision: ML ETA 估计 + 推荐选车
C. Turnout: 移动 push notification 替代无线电
D. Travel: 实时交通 + 优先信号 (信号灯 preempt)
```

---

## 4. 关键决策维度分类表

每段优化都有不同的复杂度 / 风险 / ROI:

| 阶段 | 单 case 平均时长 | 优化空间 | 工程难度 | 政治阻力 | 单 ms saved 价值 |
|---|---|---|---|---|---|
| Call processing | 60-120s | 20-40s | 中 (LLM 集成 CAD) | 中 (NENA 合规) | 高 (任何案件都享受) |
| Dispatcher decision | 10-30s | 5-15s | 高 (实时 ETA 模型) | 高 (替代经验) | 高 |
| Turnout | 30-90s | 10-30s | 低 (push notify) | 低 | 中 |
| Travel | 3-15 min | 30-90s | 中 (路径 + 信号灯) | 高 (signal preempt 需 city DOT) | 高 |

**FDE 实战策略**: **优先 attack call processing + turnout (低风险, 短期 win)**, 再 ramp 到 dispatcher decision + travel.

---

## 5. 具体业务场景

### 场景 A: 心脏骤停 EMS 调度 (黄金 4 分钟)

报警人: "我父亲晕倒了, 不呼吸了!"

- Call-taker 同时做 CPR 远程指导 (听口令) + 录入 CAD
- LLM 实时听: 抽取 "晕倒 / 不呼吸 / 男性 70" → 自动建议 dispatch code **CARDIAC ARREST PRIORITY 1**, 同时派出 AED-equipped first responder + 最近 ALS 救护车
- ML 模型给出每辆候选车的 ETA 95% confidence interval, dispatcher 看推荐 + 1 键 confirm
- 路径规划绕开下午高峰主干道
- 同时通知附近 Citizen App / PulsePoint 注册志愿者 (会 CPR 的市民) 携带 AED

**预期效果**: 黄金 4 分钟内 first responder 到场概率从 35% 提升到 55%, 心脏骤停存活率 +30%.

### 场景 B: 高层公寓火警

报警: "我们这栋楼着火了, 浓烟很大!"

- Address 识别: LLM 解析 "我们这栋楼" → cross-ref 来电号码 → 公寓地址自动填入
- 调度: 楼层 + 是否高层 → 决定派几辆云梯 + HazMat + EMS standby
- Travel: 实时交通 + 应急车道权限 (城市信号灯协议 RKE / OPTICOM 优先放行)
- 资源 pre-position: 模型预测下一小时火灾热点 (历史 + 天气干燥度 + 节假日) → 调整 idle 消防车站位

### 场景 C: 大规模 mass casualty event (枪击 / 踩踏 / 爆炸)

- 突发 50 个 911 calls 几秒内涌入 PSAP
- 系统识别 cluster (相同地点 / 相似描述) → 自动合并为 single incident, 防止重复派警
- 多部门协同 (police + EMS + fire + bomb squad) → CAD 推送 unified ops view
- LLM 摘要所有来电报告关键词 → 提供 incident commander 全局态势

### 场景 D: Non-emergency 误用分流 (噪音投诉、邻居纠纷)

- 美国 911 ~40% 是非紧急. 城市部署 **311 分流系统**
- LLM 判定来电意图: 紧急 / 非紧急 / 信息咨询 → 路由到 311 或自动 IVR 服务
- 紧急判误代价大: false negative (把紧急判为非紧急) 是不可接受的 → confidence threshold 偏保守, 不确定走人工

### 场景 E: 你的工作背景类比 — TikTok PayLater Voice Agent

你做的债务催收 voice agent 跨 7 markets 6 languages, 结构上**与 911 高度同构**:

| 911 | 你的 voice agent |
|---|---|
| Call-taker 录入信息 | ASR 实时转写 |
| LLM 摘要 call 内容 | LLM agent 做 intent + tool calling |
| Dispatcher 选车决策 | Agent 决策 (推送还款方案 / 转人工 / 标记纠纷) |
| Real-time 决策 < 800ms | 你的 streaming p99 < 800ms |
| Safety-critical, fallback to human | Trust-critical, fallback to human agent |
| 多数据源 (call / CAD / GPS / traffic) | 多数据源 (customer / 通话历史 / repay status / blacklist) |
| 跨 7 markets 部署 | 跨 7 markets 部署 (Indonesia, Brazil, Mexico, etc.) |

这个映射在面试时直接放出来, 立即把你从「FDE candidate」升级到「FDE who has shipped this in production」.

---

## 6. 工程上要做什么 / 诊断 checklist

**Phase 0 — Discovery (Week 1)**:

1. 跟接警中心运营负责人 (PSAP director) 跑一天班, 观察真实工作
2. 拉历史 6 个月数据: call → arrive 完整事件流, 含每段时间戳
3. 画 funnel: 每个阶段 P50 / P90 / P99 耗时, 找最大瓶颈
4. 跟 5 个 dispatcher 各 30 分钟访谈: 「你判断最难的时刻是什么」
5. 列出现有系统 (CAD 厂商、GPS 供应商、城市 traffic feed) 的集成可能性

**Phase 1 — 数据 instrumentation (Week 2-4)**:

6. OpenTelemetry trace 注入每段时间戳 (合规审计的 dispatcher action log)
7. 建立 baseline: 当前 call → arrive P50, P90, P99 by call category
8. 建立 control 对比组: 同期去年同月同 category 数据

**Phase 2 — Shadow mode (Week 4-12)**:

9. 上线 ETA estimator + dispatch recommender, 但**不暴露给 dispatcher**, 只 log 推荐
10. 计算 prediction error (MAE / RMSE) vs 实际 travel time
11. 如果 MAE < 60s 且 P90 error < 120s, 进入 Phase 3

**Phase 3 — Opt-in (Month 3-6)**:

12. 选 5 名 top-performing dispatcher 自愿试用, UI 加 "AI recommend" 提示
13. 跟踪 accept rate 和 override 后的 outcome
14. Weekly retro 跟 dispatcher 一起看 false positive / false negative

**Phase 4 — Default-on (Month 6+)**:

15. 默认开启, 但 dispatcher 永远可一键覆盖
16. 持续监控 override rate, 调整模型
17. 设立 kill switch: 任何 2 周窗口 outcome 退步 → 自动 fallback

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **一上来画 architecture** | 没 clarify, 方案脱离 stakeholder 真实需求. 先问 5 个 Q |
| 2 | **当 system design 题做** (算 QPS / shard) | 不是这道题考的. 考的是 problem decomposition |
| 3 | **把人类 cut out** | Safety-critical 系统的红旗. 永远 recommendation, 不 replace |
| 4 | **承诺 6 个月一次性 GA 上线** | FDE 红线. 没 phasing = 没部署过任何东西 |
| 5 | **假设 GPS / traffic 数据完美** | 真实世界 5-15% 救护车 GPS 是 stale / drift. Dead reckoning 兜底 |
| 6 | **忽略 dispatcher 拒接受** | Override rate 是 North Star. 模型再准 dispatcher 不信也白搭 |
| 7 | **A/B 测试做半个城市** | 伦理灾难: 不能 deny 另一半市民改进. 用 before/after 同期对照 |
| 8 | **承诺数字不留 buffer** | "30% 改进" 过于乐观. 现实通常 5-15% 已经 huge |
| 9 | **没考虑 PSAP 工会** | 美国 911 接警员是工会, 引入 AI 触动饭碗, 必须早期沟通 |
| 10 | **遗忘合规** (HIPAA / CJIS) | 911 涉及 PHI + 刑事数据, 加密 / 审计 / 数据驻留全要 |

---

## 一句话总结 (Part 1)

> **911 response time 优化 = "拆解 funnel 找到最大瓶颈 + ML 协助但人最终决策 + shadow → opt-in → default 渐进 + 全程 instrumentation 暴露真相"**.
>
> 真正的 win 不来自一个炫酷 ML 模型, 而是从「call connect → arrived」的每个阶段都挤出几十秒. 把 funnel 思维而非「我有个 idea」拿出来, 就是 FDE-level 答题.

---

# Part 2 · 5 个深度工程问题

## ⚙️ Problem 1: Diagnose Where Time Goes — Funnel 拆解 + Instrumentation

**核心**: 没量化, 一切都是猜测. FDE 第一周做的不是 model, 而是装 telemetry 看真实瓶颈在哪.

### 1.1 时间戳事件模型

每个 911 incident 需要 instrument 至少 12 个时间戳:

```python
# events_per_incident.py
@dataclass
class IncidentTimeline:
    incident_id: str
    # 来电阶段
    call_received_ts: datetime          # 0. 报警人按下拨号
    call_connected_ts: datetime         # 1. PSAP 接通 (运营商网络延迟)
    call_taker_pickup_ts: datetime      # 2. call-taker 接听
    location_confirmed_ts: datetime     # 3. 地址确认 (E911 / ALI)
    incident_classified_ts: datetime    # 4. 事件类型分类完毕
    cad_submitted_ts: datetime          # 5. CAD 录入完毕
    # 派警阶段
    dispatcher_received_ts: datetime    # 6. dispatcher 看到 incident
    unit_selected_ts: datetime          # 7. dispatcher 选定派单
    unit_notified_ts: datetime          # 8. responder 终端接到 alert
    unit_acknowledged_ts: datetime      # 9. responder 确认接单
    unit_enroute_ts: datetime           # 10. 车辆启动 (turnout 结束)
    unit_arrived_ts: datetime           # 11. 到达现场 (车 GPS 触发地理围栏)
```

每段时长 = 相邻两个时间戳的差. 然后聚合:

```sql
-- bottleneck.sql
SELECT
  category,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY t1_t2) AS p50_pickup,
  PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY t1_t2) AS p90_pickup,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY t5_t7) AS p50_dispatch_decide,
  PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY t5_t7) AS p90_dispatch_decide,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY t10_t11) AS p50_travel,
  PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY t10_t11) AS p90_travel
FROM incident_timeline
WHERE call_received_ts >= NOW() - INTERVAL '30 day'
GROUP BY category;
```

### 1.2 Funnel visualization

把每个阶段画成 stacked bar, 按 category 分:

```
Cardiac Arrest (P1):
  Pickup    Classify   Dispatch    Turnout       Travel        Total
  [25s]     [35s]      [12s]       [45s]         [220s]        337s ✓ goal

Fire (P1):
  Pickup    Classify   Dispatch    Turnout       Travel        Total
  [30s]     [60s]      [25s]       [85s]         [310s]        510s ✗ goal

Medical Non-emergency:
  Pickup    Classify   Dispatch    Turnout       Travel        Total
  [40s]     [180s]     [60s]       [120s]        [600s]        1000s
                ↑ outlier — LLM 摘要这里能砍一半
```

### 1.3 异常案件 root-cause

针对超时 outliers 自动归因:

```python
def root_cause_outliers(incident_id):
    t = fetch_timeline(incident_id)
    bucket = classify_bottleneck(t)

    if bucket == 'classify_slow':
        return {
            'reason': 'classification took > P90',
            'recommendation': 'check if LLM assist was used; replay audio'
        }
    elif bucket == 'dispatch_slow':
        return {
            'reason': 'dispatcher hesitated > 30s',
            'recommendation': 'check available units count; was there a recommend?'
        }
    elif bucket == 'travel_slow':
        return {
            'reason': 'travel exceeded ETA by > 60s',
            'recommendation': 'check traffic feed; was route stale?'
        }
```

### 1.4 实战建议: 第一周就做 dashboard

```
┌─────────────────────────────────────────────────────┐
│  PSAP Response Time Dashboard - last 7 days         │
├─────────────────────────────────────────────────────┤
│  Total calls: 12,847                                │
│  P50: 5:21  P90: 8:47  P99: 14:32   ← 关键 3 数字   │
│                                                     │
│  Worst bottleneck by volume × time:                 │
│    1. Classify (medical non-emergency): 180s P90   │
│    2. Travel (fire downtown): 310s P90              │
│    3. Turnout (night shift): 85s P90                │
│                                                     │
│  ROI estimate of fix:                               │
│    Classify LLM: save 60s × 8K calls/mo = 133 hours│
│    Travel routing: save 30s × 3K calls/mo = 25h    │
└─────────────────────────────────────────────────────┘
```

这个 dashboard 第一周拿给 PSAP director 看, **你立刻是「这个 vendor 懂我们」**.

---

## ⚙️ Problem 2: Real-Time Dispatch Agent — ETA + Recommendation

**核心**: dispatcher 看到 5 辆候选救护车, 怎么选? 凭直觉错 20% (尤其在交通复杂时). ML + 实时 traffic 能把这块的 P90 决策时间从 25s 降到 8s, 并选到更优的车.

### 2.1 ETA Estimator 设计

输入特征:

```python
features = {
    # Vehicle state
    'unit_lat': 40.7128,
    'unit_lng': -74.0060,
    'unit_heading_deg': 90,
    'unit_speed_kmh': 35,
    # Destination
    'incident_lat': 40.7589,
    'incident_lng': -73.9851,
    # Context
    'time_of_day': 14,       # 0-23 hour
    'day_of_week': 2,
    'is_holiday': 0,
    'weather_condition': 'rain',
    'distance_road_meters': 4250,
    'shortest_path_segments': [seg1, seg2, seg3],
    # Traffic
    'avg_speed_segment_1': 28,
    'avg_speed_segment_2': 15,    # ← 这里堵
    'incident_count_along_route': 1,
}
```

模型选型对比:

| 选型 | 优点 | 缺点 | 适用 |
|---|---|---|---|
| **Dijkstra / A* + 平均速度** | 简单, 可解释 | 不学时段 / 天气 modulation | v0 baseline |
| **GBDT (XGBoost / LightGBM)** | 准, 中等可解释, 训练快 | 不学路网结构 | v1 (recommend) |
| **GNN (Graph Neural Net)** | 学路网, 多步预测精 | 训练成本高, 不可解释 | v2 (advanced) |
| **LLM agent** | 灵活, 可整合非结构化 | 延迟高, 不擅长数值 | 不适合 |

**v1 推荐 GBDT**: 训练 3 个月历史数据, 目标 MAE < 60s on P90.

### 2.2 Recommendation 决策框架

简单看 ETA 不够, dispatcher 选车要考虑:

```python
def rank_units(incident, candidate_units):
    scored = []
    for unit in candidate_units:
        eta = predict_eta(unit, incident)
        confidence = predict_eta_confidence(unit, incident)

        score = (
            -eta                                          # 越快越好
            - confidence_penalty(confidence)              # 不确定打折
            + skill_match_bonus(unit.skill, incident)     # ALS for cardiac
            + equipment_bonus(unit.equipment, incident)   # AED, defib
            - workload_penalty(unit.shifts_today_hours)   # 别累垮
            - depot_imbalance_penalty(unit)               # 不要全市集中一处
            + redundancy_bonus(other_pending_incidents)   # 留一辆给热点
        )

        scored.append({
            'unit_id': unit.id,
            'score': score,
            'eta_seconds': eta,
            'confidence': confidence,
            'reasoning': explain(unit, incident, score)
        })

    return sorted(scored, key=lambda x: -x['score'])[:3]  # top 3
```

返回 top 3 给 dispatcher 看 + reasoning, dispatcher 一键 confirm.

### 2.3 LLM 在 dispatch 里的角色 — 协助但不决定

**LLM 不擅长数值优化** (ETA 模型那是 GBDT 的活), 但**擅长**:

1. **解析非结构化报警内容** — call-taker 还在记录时, LLM 已经从 ASR 流里抽出 "胸痛 / 男性 / 老年", 自动建议 dispatch code
2. **整合多源 context** — 把过去 30 天该地址的报警历史、附近 active incidents、天气、活动信息浓缩成一段给 dispatcher 看的 prompt
3. **多语言** — 报警人讲西语 / 中文, 实时翻译给 call-taker

**架构**:

```
ASR streaming → LLM agent (Gemini 3 Flash $0.50/$3) →
   {
     "suggested_code": "26-D-1 (Cardiac arrest)",
     "key_symptoms": ["chest pain", "shortness of breath", "70yo male"],
     "hazards": ["no allergies reported", "patient conscious"],
     "address_confidence": 0.92
   }
→ 显示在 call-taker UI 旁边, 加速他录入 (按 Tab 自动 fill)
```

每个 911 call 一次 LLM 调用. 假设城市每天 30K calls, 每 call 500 input + 200 output tokens:
- Daily cost = 30000 × (500 × 0.5 + 200 × 3) / 1M = 30000 × 0.85 / 1000 = $25.5/day = **$9300/year**

对一个市政府而言完全 negligible.

### 2.4 Confidence-aware 决策

```python
def dispatch_decision(top_3_units, incident):
    best = top_3_units[0]

    if best['confidence'] > 0.85 and incident.priority == 1:
        return {
            'mode': 'recommend_with_strong_hint',
            'auto_select_in_seconds': 3,    # dispatcher 不动 → 自动确认
            'reasoning': best['reasoning']
        }
    elif best['confidence'] > 0.7:
        return {
            'mode': 'recommend',
            'auto_select_in_seconds': None,
            'reasoning': best['reasoning']
        }
    else:
        return {
            'mode': 'show_all_with_no_strong_hint',
            'auto_select_in_seconds': None,
            'reasoning': 'multiple candidates have similar ETA'
        }
```

**关键设计**: confidence 高且 P1 → 加快 (默认确认), 但仍可 1 键 override.

---

## ⚙️ Problem 3: Failure Modes + Human-in-the-Loop for Life Safety

**核心**: 911 系统每一次错误可能死人. 你的 ML 系统必须设计**多层 fail-safe**, 永远不能让人完全离开决策环.

### 3.1 5 类典型 failure modes

```python
class FailureMode(Enum):
    DATA_STALE = "stale_data"        # GPS / traffic 上游断流
    MODEL_LOW_CONF = "low_conf"       # 模型自身不确定
    MODEL_OUT_OF_DIST = "ood"         # 输入异常 (mass casualty)
    INTEGRATION_DOWN = "integration"  # CAD 断连
    DISTRIBUTION_DRIFT = "drift"      # 模型行为漂移
```

每种都需要 **detector + fallback action**:

| Failure | Detector | Fallback |
|---|---|---|
| GPS stale > 60s | TS 监控每车上报间隔 | Dead reckoning (last pos + heading × elapsed) |
| Traffic feed > 5min lag | 心跳 metric | 退化到 `no-traffic shortest path` |
| Model confidence < 0.4 | inline check | 不 recommend, show raw distance list |
| Out-of-distribution input | embedding distance vs training set | escalate to dispatcher with reason flag |
| CAD API down | health probe | 全部回退手动 + alarm to ops |
| Override rate > 50% for 1 day | dashboard alert | auto-pause recommendations, page FDE |

### 3.2 Human-in-the-loop 三层架构

```
Layer 1: AI-assisted (recommendation, fast confirm)
  - dispatcher 1 键 confirm 或 1 键 override
  - 所有 override 行为 logged + 周复盘

Layer 2: AI-blind (recommendation hidden)
  - 用于 dispatcher 信号: 「这次我自己决定」
  - 仍记录 AI 的 shadow recommendation, 不显示

Layer 3: Manual override (emergency stop)
  - 重大 incident (mass casualty, active shooter): 自动切换 Layer 2
  - "Kill switch": ops 按钮全市停用 AI recommendation, 退回纯人工
```

dispatcher 在屏幕上**永远看到当前 Layer**:

```
┌─────────────────────────────────────────┐
│  AI Assist: ON  (Layer 1) [Switch]      │
│                                         │
│  Active Recommendations: 12 incidents   │
│  Override rate today: 18%               │
└─────────────────────────────────────────┘
```

### 3.3 Override 不是失败 — 是数据

```python
def log_override(incident_id, ai_recommendation, dispatcher_choice, reason):
    db.insert('overrides', {
        'incident_id': incident_id,
        'ai_unit': ai_recommendation['unit_id'],
        'ai_eta': ai_recommendation['eta_seconds'],
        'human_unit': dispatcher_choice['unit_id'],
        'human_reason': reason,
        'timestamp': now()
    })

# 一周后 outcome 出来:
def outcome_analysis():
    """对所有 override 计算: 人选的 vs AI 选的, 谁的实际 arrive time 更短"""
    overrides = db.query('overrides', age='last_7day')
    for o in overrides:
        actual = fetch_actual_arrival(o.incident_id)
        ai_predicted = o.ai_eta
        human_actual = actual.travel_seconds

        if human_actual < ai_predicted - 30:
            # 人对了, AI 错了 — 标为训练数据
            mark_as_training_signal(o)
        elif ai_predicted < human_actual - 30:
            # AI 实际会更快, 但人 override 了 — dispatcher 不信任?
            mark_for_trust_review(o)
```

**Override rate trend** 是组合健康度信号:

- 30% → 健康. dispatcher 在用脑, 不是 rubber stamp
- < 10% → 警惕. 可能 over-rely on AI, 关键 case 也不动脑
- > 60% → AI 模型有问题, 别人不信

### 3.4 「不信任 dispatcher」的反向问题

```
Scenario: 新来的 junior dispatcher, 看 AI recommend 都 accept
   → 没经验积累
   → AI 一旦犯错, junior 完全不会发现
   → 系统的 collective 决策质量下降

对策:
   - Junior 期强制 train mode: AI 推荐 hidden, 让他先决定
   - 决定后看 AI 的推荐, 学习反思
   - 通过 1 个月才解锁 Layer 1
```

---

## ⚙️ Problem 4: Resource Pre-Positioning — ML Predict + Static Optimization

**核心**: 大部分救护车 / 警车不是从 station 出发, 而是从巡逻位置. 哪里放 idle 车决定了未来 1 小时响应时间. 这是个有 ML + 优化空间的子问题.

### 4.1 Demand 预测模型

输入特征:

```python
demand_features = {
    'spatial': {
        'cell_id': '8x8 km^2 grid',
        'lat': 40.7128,
        'lng': -74.0060,
        'historical_avg_calls_per_hour': 12.3,
    },
    'temporal': {
        'hour_of_day': 14,
        'day_of_week': 2,
        'is_holiday': False,
        'is_event_day': False,
    },
    'contextual': {
        'weather_temp_f': 75,
        'weather_precip_in': 0,
        'major_event_within_5km': 'baseball_game',
        'recent_call_volume_last_30min': 8,
    }
}
```

预测目标: **下个 30 分钟内, 每个 cell 期望 911 calls 数量** (Poisson regression).

模型: GBDT, 训练 2 年数据. 性能目标 MAPE < 25% on cell-30min granularity.

### 4.2 Pre-position 优化

这是个**带容量约束的 multi-facility location problem**:

```python
# 决策变量: x[u, c] = 1 if unit u positioned at cell c
# 目标: 最小化 expected response time
# 约束: 每辆车一个位置, 每个区域容量上限, etc.

from scipy.optimize import linprog
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('CBC')

x = {}  # x[u][c] = binary
for u in units:
    for c in cells:
        x[u, c] = solver.IntVar(0, 1, f'x_{u}_{c}')

# 每个 unit 只能在一个 cell
for u in units:
    solver.Add(sum(x[u, c] for c in cells) == 1)

# 每个 cell 容量
for c in cells:
    solver.Add(sum(x[u, c] for u in units) <= c.capacity)

# 目标: 加权预期响应时间
objective = 0
for c in cells:
    expected_calls = demand_prediction[c]
    expected_resp = 0
    for u in units:
        # 如果 unit u 在 cell c', 服务 cell c 的预期 travel time
        for c2 in cells:
            travel = travel_time_matrix[c2][c]
            expected_resp += x[u, c2] * travel
    objective += expected_calls * expected_resp

solver.Minimize(objective)
solver.Solve()
```

这是个比较经典的 set cover / facility location 变种, 30 个救护车 × 100 cell 求解秒级.

### 4.3 实时 re-positioning trigger

```python
def should_reposition_now():
    # 1. 是否有明显偏离 baseline 的 demand 信号
    current_demand_vs_baseline = compute_demand_drift()
    if current_demand_vs_baseline > 1.3:
        return True

    # 2. 是否有突发活动 (sports event end, concert)
    if event_calendar.has_upcoming_dispersal(within_minutes=15):
        return True

    # 3. 是否当前覆盖空洞 (一个区域 30 min 内没有可达单位)
    coverage_gaps = compute_coverage_gaps()
    if any(g.severity > 0.8 for g in coverage_gaps):
        return True

    return False
```

### 4.4 部署阶段

| Phase | 范围 | 持续 |
|---|---|---|
| 0 | shadow: 算出 recommendations, 不下发, log only | 8 周 |
| 1 | one shift / one zone 测试 | 4 周 |
| 2 | one battalion (全市 1/3) | 4 周 |
| 3 | citywide 默认开启, 永远可 override | ∞ |

**实战教训**: 救护车司机 / 消防员对 "AI 让我去某个位置坐着" 强烈抗拒. 必须让他们参与设计 + 看到改进数据, 否则会 silent sabotage (假装去, 实际不到位置).

---

## ⚙️ Problem 5: Eval Methodology When Ground Truth Lags

**核心**: AI 的好坏要看 outcome (生存率 / 财产损失). 但这些数据有 weeks-months 的延迟. 怎么早期判断系统是不是工作?

### 5.1 三层 metric 架构

```
Layer 1: Leading indicators (实时可观察)
  - Response time P50/P90/P99
  - Override rate
  - System availability (CAD integration uptime)
  - Recommendation latency

Layer 2: Mid-term outcomes (1-7 天可观察)
  - On-scene assessment scores by responder
  - Resource utilization (车辆 idle %)
  - Dispatcher workload metrics

Layer 3: Lagging outcomes (weeks-months)
  - Cardiac arrest survival rate
  - Property damage from fires
  - Cost per incident
  - Public satisfaction
```

每层之间需要建立 **causal chain** (proxy metric):

```
Response time ↓ → On-scene assessment ↑ → Survival rate ↑

但: response time ↓ 不一定 → 总成本 ↓ (可能因为更多 over-dispatch)
```

### 5.2 设计可控对照实验

**A/B 测试在 911 不伦理** — 你不能 deny 一半市民的改进.

**替代方案**:

| 方法 | 描述 | 强 / 弱 |
|---|---|---|
| **Before/After 同期对照** | 与去年同月数据对比 | 弱 (季节性 / 趋势混淆) |
| **Difference-in-Differences (DiD)** | 跟没有 AI 的相邻城市相比 | 中 (邻市差异) |
| **Stepped wedge rollout** | 城市分区分阶段上线 | 中 (内部对照) |
| **Counterfactual simulation** | 用历史数据 replay AI 决策 | 强 (但只是 in-silico) |
| **Synthetic control** | ML 合成虚拟对照组 | 强 (统计假设多) |

**推荐组合**: Stepped wedge (分区分阶段) + Counterfactual simulation (历史 replay).

```python
# stepped_wedge.py
phases = [
    ('Phase 1', 'Zone A', month_1),
    ('Phase 2', 'Zone A + B', month_3),
    ('Phase 3', 'Zone A + B + C', month_5),
    ('Phase 4', 'Citywide', month_7),
]

# 每个 phase 比较: zone X 上线后 vs 上线前 vs 同时其他 zone
```

### 5.3 Counterfactual replay

对历史 incidents 用 AI replay:

```python
def counterfactual_eval(historical_incidents):
    """对每个历史 incident 让 AI 「做决定」, 比较实际 outcome"""
    results = []
    for incident in historical_incidents:
        # 重建当时的 state (可用车 / traffic / weather)
        state = reconstruct_state(incident.timestamp)

        # AI 在那个 state 下会怎么选
        ai_choice = ai_recommend(state, incident.context)

        # 人实际选了什么
        human_choice = incident.dispatched_unit_id

        # 用 ETA 模型估计 AI 选的会有多快到
        ai_predicted_arrival = predict_ETA(ai_choice, incident)

        # 人实际几点到的
        human_actual_arrival = incident.actual_arrival_seconds

        results.append({
            'incident_id': incident.id,
            'ai_better': ai_predicted_arrival < human_actual_arrival,
            'estimated_delta_sec': human_actual_arrival - ai_predicted_arrival,
        })

    return summarize(results)
```

**陷阱**: counterfactual 是估计, 不是真实. AI 可能在一些场景里**永远不会被实际验证** (比如 AI 选了不同的车, 那车实际可能不会按预测的速度跑). 把这当作 "directional signal", 不当 ground truth.

### 5.4 Trust-rebuilding 周期

```
Week 1-4: Daily standup with PSAP director
  - Show: P90 response time trend, override rate, any incidents
  - Discuss: what surprised us this week

Week 5-12: Weekly leadership review
  - Show: phase-by-phase rollout health
  - Discuss: should we accelerate / pause / pivot

Month 3-6: Monthly outcome review (with city's CMO / EMS director)
  - Show: lagging outcomes (cardiac, trauma)
  - Discuss: is leading metric → lagging metric translating

Month 6+: Quarterly with mayor's office
  - Show: ROI for budget defense
  - Discuss: scope expansion
```

每周 dashboard 必须有:

```
[Last 7 days]
  Total incidents: 84,231
  P90 response time: 6:42 (target 6:30, -12s vs last week ✓)
  Override rate: 22% (steady)
  AI uptime: 99.94%
  Lagging metric refresh: outcomes from Mar 2026 batch released
```

### 5.5 边界情况评估

```python
# 不能光看 aggregate, 要看 stratified
strata = ['cardiac', 'fire', 'trauma', 'violence', 'mental_health', ...]
for s in strata:
    p50 = response_time_p50(category=s)
    p90 = response_time_p90(category=s)
    # 主要 metric 是否在所有 strata 都改善, 或只是某几类拉高 aggregate?
```

如果只在 cardiac 改进 30% 但 mental health 退步 10%, **dashboard 必须红字标出**, 而不是被 aggregate 掩盖.

---

# Part 3 · 把 5 个问题串起来看

这 5 个 layer 拼起来就是一个完整的 911 deployment 工程视野:

1. **Funnel diagnose** (Problem 1) — 不量化就没真相
2. **Real-time dispatch** (Problem 2) — ML + LLM 各做擅长的事, 人最终决策
3. **Failure modes + HITL** (Problem 3) — safety-critical 的核心
4. **Resource pre-position** (Problem 4) — ML + 优化 + 渐进部署
5. **Eval methodology** (Problem 5) — ground truth 延迟的应对

面试场把这 5 个 layer 系统讲清楚, 就是 **FDE-staff level**. 单点深入展开任意 1 个时, **保持其他 4 个能在 30s 内串回来**, 让面试官看到你心里有完整框架.

---

## 必问 clarifying questions

**1. Stakeholders & success metric**

> "Who's the buyer — the mayor's office? Police? Fire department? And what's their **single KPI**? Average response time? P99 response time? Response time for a specific call category like cardiac arrest?"

**为什么问**: 每个 stakeholder 的 metric 不一样. Police 关心 violent crime 响应; fire 关心 structure fire 响应; mayor's PR 关心 average. **先锁 KPI**, 不然后面所有 design 都飘.

**2. Constraints**

> "What's the **integration constraint** — do we have read access to dispatch system, or just batch dumps overnight? Real-time GPS feed from ambulances, or 5-min sampled? Is the city willing to deploy on our cloud, or strict on-premise?"

**为什么问**: FDE 是 deployment 工程师, 不是 research scientist. Data freshness + integration mode 决定整个 architecture 是 batch ETL vs streaming.

**3. Baseline**

> "What's the **current** average response time? And what's the city's stated target — 10% improvement, or moonshot 50%?"

**为什么问**: No baseline = no eval. 10% 改进 (统计 noise above threshold) 跟 50% 改进 (要换 dispatch policy 那种级别) 是完全不同的项目 scope.

**4. Scope of platform**

> "When you say 'our platform' — are we **dispatch software** (operator picks an ambulance), or **predictive routing** (real-time traffic-aware route), or **resource pre-positioning** (where to park idle ambulances)?"

**为什么问**: 60 min 内做不完全部. **Force the interviewer to scope you down**.

**5. Failure mode tolerance**

> "What's the **cost of a wrong prediction**? If we route an ambulance through traffic that turns bad mid-route, what's the fallback?"

**为什么问**: Emergency response is **safety-critical**. 失败一次进新闻. **Risk appetite 决定 model 类型** (lookup-table baseline vs ML 模型 vs hybrid).

---

## 5 步框架 (60 min 时间分配)

| 时长 | 阶段 | 要做什么 |
|---|---|---|
| 0-10 min | Clarify + scope | 上面 5 个 Q, 把范围 narrow 到 1 个具体子问题 |
| 10-25 min | Architecture sketch | 3 components: data ingestion / decision engine / dispatcher integration |
| 25-40 min | Deep dive 1 component | 选最难的 1 个 (通常 decision engine + 实时 traffic) 展开 |
| 40-50 min | Failure modes + measurement | "这个 design 怎么挂"、KPI 怎么测、 dispatcher 怎么 trust |
| 50-60 min | Phasing + scope reduction | 90-day MVP 应该长什么样、phase 2/3 是什么 |

---

## 简历专属 reframe

你的 **debt collection voice agent** 项目跟这道题**结构上高度同构**:

| 911 题 | 你的 voice agent |
|---|---|
| Multi-source data (calls / traffic / GPS) | Multi-source data (customer profile / call history / repayment status) |
| Real-time decision under time pressure | Real-time conversation under latency pressure (p99 < 800ms streaming) |
| Stakeholder mismatch (mayor vs police vs fire) | Stakeholder mismatch (legal vs ops vs product across 7 markets) |
| Safety-critical, fallback to human | Trust-critical, fallback to human agent |
| Hard to A/B (ethics) | Cross-market A/B testing — 你做过 stepped wedge |
| Shadow-mode → opt-in → default-on phasing | RL alignment 你也是 phase-by-phase 上的 |
| LLM 协助 dispatcher 加速判断 | LLM agent 协助 collection rep 加速判断 |

**面试时主动 quote**:

> "Actually this problem structure mirrors something I just shipped — a voice AI agent for debt collection across 7 markets and 6 languages. Same shape: multi-source data, real-time decision under sub-second latency, safety-critical with human fallback, hard to A/B because the controlled-experiment is ethically tricky. I used a **shadow-mode → opt-in → default-on phasing** for that rollout with override rate as a North Star — same pattern would apply here.
>
> One specific lesson I'd carry: we instrumented every stage of the voice pipeline (ASR latency, LLM latency, TTS latency, tool-call latency) on day 1. When the system was 'slow', we didn't argue — we pointed at the dashboard. I'd do the same with 911: in week 1 build the funnel dashboard so the conversation with PSAP director moves from 'we feel slow' to 'classify takes 180s P90, that's the win'."

---

## 5 follow-ups

**Q1**: "What if the city has bad GPS data on ambulances — 30% of pings are stale?"

**A**: 先 measure stale rate per ambulance per time-of-day → identify if it's vehicle-specific (broken hardware) vs systematic (e.g., GPS dead in tunnels). For systematic gaps, layer in **dead reckoning** (last known position + heading × elapsed time). For broken hardware, flag to ops for fleet remediation. Model itself: degrade to "any nearby available ambulance" if stale rate > 50% in that region.

**Q2**: "Mayor wants results in 6 weeks not 12 months."

**A**: 时间压缩 → narrow scope. 6 周做不完 ML routing, 但能做 **dashboard + manual decision support**: 把「哪辆 ambulance 在哪 / 当前 traffic 怎样 / 推荐谁出动」实时给 dispatcher 看, **还是 dispatcher 决定**. 这是 deterministic + transparent, 6 周可行. Mayor 还是能 announce "AI-assisted dispatch saving lives". **逆向 scope 是 FDE 核心技能**.

**Q3**: "How do you avoid getting the city sued when an ambulance is misrouted?"

**A**: 3 个 legal-safe defaults:
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

1. **一上来就画 architecture** — 没 clarify, 方案脱离 stakeholder 实际需求
2. **把它当 system design 题做** — 算 QPS / DB shard. 不是这道题在考的
3. **忽略 dispatcher 这个角色** — 把人类完全 cut out 是 safety-critical 系统的红旗
4. **没说 phasing** — "6 个月一次性上线" 在 FDE 面试官眼里 = 没部署过任何东西
5. **忽略数据质量** — 假设 GPS / traffic 完美. **FDE 全职在跟脏数据死磕**
6. **不主动 surface failure modes** — 等面试官追问 = 失分
7. **答案太长, 没给面试官追问的空间** — 6-7 分钟讲完, 剩下 50 分钟 deep-dive, 是节奏目标
8. **直接 A/B test 切一半城市** — 伦理灾难, 用 stepped wedge / DiD
9. **过度依赖 lagging outcome** — 几个月才能反馈, 必须建 leading indicator
10. **忽略 PSAP 工会和政治** — 接警员是会议代表的工种

---

## ✅ 加分项

1. **Shadow-mode → opt-in → default-on phasing** 主动提
2. **Override rate as a North Star metric** — 把「用户信任」量化成 metric
3. **Side-car integration pattern** 应对 vendor 政治
4. **Legal-safe defaults** (recommendation not decision / audit log)
5. **Dead reckoning** 处理 GPS gap — 体现你处理过脏数据
6. **Stepped wedge rollout** 替代 A/B 因为 ethics
7. **OpenTelemetry trace 12 时间戳** 每个 incident
8. **Counterfactual replay 评估** + 承认它是 directional 不是 ground truth
9. **Cost math**: LLM assist per call $9300/year — negligible 对城市
10. **Quote your voice agent 7-market production experience**

---

## 一句话总结

> **911 response time 优化 = 在 funnel 每段挤秒 + ML 推荐但人最终决策 + 渐进 rollout + 全程 instrumentation 暴露真相**.
>
> 这道题考的不是 ML 模型本身, 而是「面对一个 unbounded、safety-critical、多 stakeholder 的真实部署你能不能 scope it down to a 90-day MVP without losing the long-term vision」.

---

## Cheat Sheet (面前 5 min 看)

```
不要做:
  - 上来画图 / 算 QPS
  - 假设你知道 stakeholder
  - 一次讲完整方案, 留空白

要做:
  1. 5 个 clarifying 问题先问
  2. Scope 到一个 sub-problem
  3. 3-layer architecture sketch (ingest / decision / integration)
  4. Deep dive 1 component
  5. Surface failure modes 主动
  6. Phasing: shadow → opt-in → default

Funnel timestamps (12 个):
  call_received → connected → pickup → location → classified
  → cad_submit → dispatcher → unit_select → notified → ack
  → enroute → arrived

ML + LLM 分工:
  LLM (Gemini 3 Flash $0.50/$3):
    - ASR 实时摘要 + symptom extract
    - 多语言翻译
    - dispatch code 建议
  GBDT:
    - ETA 预测 (target MAE < 60s P90)
    - Demand 预测 (Poisson, MAPE < 25%)
  优化:
    - 救护车 pre-positioning (facility location)

Failure modes 5 类 + fallback:
  GPS stale → dead reckoning
  Traffic stale → no-traffic shortest path
  Model low-conf → show raw list, no recommend
  CAD down → manual mode, alarm
  Override > 50% → auto-pause + page FDE

Eval (ground truth 延迟):
  Leading: response time, override, uptime
  Mid: assessment scores, utilization
  Lagging: survival, damage, cost
  方法: stepped wedge + counterfactual replay
  不用: A/B 因伦理

关键 phrases:
  - "Let me ask a few things before designing..."
  - "I'd narrow this to..."
  - "Before being asked, I want to flag..."
  - "This mirrors my voice agent at TikTok..."
  - "I'd phase this..."

数字 anchors:
  - 4 周 shadow mode
  - MAE < 60s P90 for ETA
  - 80% model confidence threshold
  - Override rate 20-30% target
  - LLM cost $9300/year/city
  - NFPA 1710: 6.5 min P90
  - Cardiac golden 4 min
```

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

> **911 不是「炫 ML 模型」, 是「把 funnel 每段 instrument + ML 推荐人决策 + shadow→opt-in→default 渐进 + ground truth lag 用 counterfactual + leading indicators 补位」**. FDE 拿到题目第一动作: 问 5 个 clarifying, 拒绝立刻画图.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| PSAP | Public Safety Answering Point, 接警中心 | 描述 911 入口节点 |
| CAD | Computer-Aided Dispatch, 接警调度中枢 | 集成对象 + 数据源 |
| Call-taker | 接电话录入 incident | 区分采集者 vs dispatcher |
| Dispatcher | 看 CAD 屏决定派谁 / 怎么走 | 决策环用户, override 的人 |
| ALI | Automatic Location Identification (E911) | 地址自动定位 |
| ALS | Advanced Life Support, 高级救护 | 高优先级 cardiac 派车 |
| NFPA 1710 | 火灾响应 P90 6.5 min 行业标准 | 当 baseline 引用 |
| Turnout | 接到通知 → 车启动的时间 | 4 优化点之一 (C) |
| Stepped wedge | 分区分阶段上线, 内部对照 | 替代 A/B 因 ethics |
| Counterfactual replay | 用历史 incident 让 AI 重新决策对比 | ground truth lag 时用 |
| Dead reckoning | 上次位置 + 朝向 × 时间, GPS stale 兜底 | GPS 数据 5-15% stale 时 |
| Override rate | dispatcher 推翻 AI 推荐的比例 | North Star: 20-30% 健康 |
| Stratified eval | 按 category (cardiac/fire/...) 分桶看指标 | 防止 aggregate 掩盖退步 |
| OPTICOM/RKE | 城市信号灯优先放行协议 | travel 优化, 需 city DOT |
| 26-D-1 | EMS 调度代码 (cardiac arrest) | 描述 dispatch code 时使用 |

### 🎯 5 个核心 framework

**Framework 1**: Funnel decomposition (12 时间戳)
- When: 任何 multi-stage 响应类问题
- Algorithm: call_received→connected→pickup→location→classified→cad_submit→dispatcher→unit_select→notified→ack→enroute→arrived
- Trade-off: 12 时间戳工程量大, 但没量化就没诊断
- Tools: OpenTelemetry trace, P50/P90/P99 Postgres percentile_cont, Grafana / Datadog dashboard

**Framework 2**: ML + LLM 分工
- When: 既有数值 (ETA) 又有非结构化 (call audio) 时
- Algorithm: GBDT 做 ETA + demand预测 (数值, MAE<60s) / LLM 做 ASR + symptom抽取 + 多语 + dispatch code 建议 (非结构化) / 优化器 (CBC / OR-Tools) 做 pre-position (NP-hard)
- Trade-off: LLM 慢且不擅数值, GBDT 不学非结构化
- Tools: Gemini 3 Flash $0.50/$3 (LLM), XGBoost / LightGBM (GBDT), Google OR-Tools / SciPy linprog

**Framework 3**: HITL 三层 + Override 数据化
- When: safety-critical 系统
- Algorithm: Layer 1 AI assist (1 键 confirm) / Layer 2 AI blind (junior train mode) / Layer 3 kill switch (全市退手动) / log every override + 一周后 outcome 对比
- Trade-off: junior 全 accept (over-rely) vs senior 全 ignore (信任不足)
- Tools: 强制 train mode 1 个月, override rate dashboard, "AI Assist: ON Layer X" UI 角标

**Framework 4**: 5-stage rollout (shadow→opt-in→default→kill)
- When: 任何 ML 系统部署 to safety-critical
- Algorithm: Phase 0 discovery 1w / Phase 1 instrument 2-4w / Phase 2 shadow 4-12w / Phase 3 opt-in 5 top dispatcher / Phase 4 default-on + kill switch
- Trade-off: 太慢, 但 911 一条命就是一条命, 不快
- Tools: feature flag (LaunchDarkly), shadow log table, weekly retro, 2w outcome regression auto-pause

**Framework 5**: Eval ladder (leading / mid / lagging)
- When: ground truth (生存率) 延迟 weeks-months
- Algorithm: Leading (response time, override rate, uptime 实时) → Mid (assessment scores 1-7d) → Lagging (survival, damage months) + stepped wedge + counterfactual replay
- Trade-off: counterfactual 是估计不是真相; A/B 不伦理
- Tools: stepped wedge by zone, synthetic control, DiD vs 邻市, replay simulator

### 🌳 关键决策树

```
Q: 60 min 内怎么 scope?
├─ Mayor's KPI? → P99 / category-specific / average → 锁 KPI
├─ Integration? → realtime stream / 5-min sampled / batch overnight → 锁架构
└─ Sub-problem? → routing / dispatch / pre-position → 选一个
   └─ Pick: 通常 funnel diagnose + dispatch recommend (最大 ROI)

Q: 决策时 confidence 多少 trigger 什么?
├─ conf > 0.85 + P1 → auto-confirm in 3s (但仍可 1 键 override)
├─ conf 0.7-0.85 → recommend, dispatcher 必须 confirm
├─ conf < 0.7 → show raw list, no recommend
└─ Override > 50% / 1 day → auto-pause + page FDE
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: Funnel 拆解 + Instrumentation**
- 核心解法:
  ```python
  # 12 时间戳 → SQL percentile_cont → stacked bar per category
  # outlier 自动归因: classify_slow / dispatch_slow / travel_slow
  # 第一周交付: PSAP dashboard "Worst bottleneck × volume = save 133h"
  ```
- Top 3 gotchas: 假设 timestamp 都有 (实际缺 30%) / 不分 category 看 aggregate / 没把 ROI 估出来
- Tools: OpenTelemetry, Datadog APM, Grafana, percentile_cont SQL, Mimir 长期存储

**Problem 2: Real-Time Dispatch Agent (ETA + Recommendation)**
- 核心解法:
  ```python
  rank = -eta - conf_penalty + skill_match + equipment - workload - depot_imbalance + redundancy
  return top_3 with reasoning  # dispatcher 一键 confirm
  # LLM (Gemini Flash) 解析 ASR → dispatch code 建议; GBDT MAE < 60s
  ```
- Top 3 gotchas: 只看 ETA 忽略 skill/equipment / 不给 reasoning (黑盒 dispatcher 不信) / LLM 跑数值
- Tools: Gemini 3 Flash $9300/yr/city, LightGBM, GraphQL UI, streaming ASR

**Problem 3: Failure Modes + HITL**
- 核心解法:
  ```
  GPS stale > 60s → dead reckoning
  Traffic > 5min lag → shortest path no-traffic
  conf < 0.4 → show raw list
  CAD down → manual mode + alarm
  Override > 50% → auto-pause + page FDE
  ```
- Top 3 gotchas: junior 全 accept (不动脑) / 没 kill switch / override 只算数不分析为什么
- Tools: 心跳 metric, OOD embedding distance, feature flag kill switch, weekly override retro

**Problem 4: Resource Pre-Positioning**
- 核心解法:
  ```python
  # demand: GBDT Poisson per 8x8km cell × 30min, MAPE < 25%
  # optim: CBC IntVar x[u,c], constraint 每车一位置, min Σ demand × travel
  # trigger: demand drift > 1.3 OR event dispersal in 15min OR coverage gap > 0.8
  ```
- Top 3 gotchas: 司机 silent sabotage (假装就位) / 没参与设计 / 没看到改进数据
- Tools: Google OR-Tools CBC, scipy.optimize, Poisson regression, event_calendar API

**Problem 5: Eval Methodology (ground truth lag)**
- 核心解法:
  ```
  Layer 1 leading (实时): response time, override, uptime, latency
  Layer 2 mid (1-7d): assessment scores, utilization
  Layer 3 lagging (weeks): survival, damage, cost
  Method: stepped wedge by zone + counterfactual replay (directional)
  Stratified: cardiac / fire / trauma / violence / mental_health 分桶看
  ```
- Top 3 gotchas: 直接 A/B 半个城市 (伦理) / 只看 aggregate 掩盖某 category 退步 / counterfactual 当 ground truth
- Tools: synthetic control, DiD vs 邻市, replay simulator, OpenTelemetry, Looker / Tableau

### 🔥 Production gotchas (top 15)

1. GPS 5-15% stale / drift → dead reckoning
2. Traffic feed > 5min lag → fallback no-traffic shortest path
3. CAD vendor (Motorola/Tyler/Hexagon/RapidDeploy) 拒绝集成 → side-car pattern
4. PSAP 工会触饭碗 → 早期 sponsor + 数据透明
5. Junior dispatcher rubber stamp → 1 个月 train mode
6. Senior dispatcher 全 override → 信任失败信号, retrain on their choices
7. Mass casualty (50 calls/秒) → 自动 cluster 合并防重复派警
8. Cluster mis-merge → 不同事件被合并 → 漏派, P1 必须 cluster + 单独 verify
9. Ambulance silent sabotage (假装就位) → GPS 校验 + 参与设计
10. Override rate noise → 30% 健康, < 10% 警惕, > 60% AI 模型差
11. A/B 切半个城市 → 伦理灾难, stepped wedge / DiD 替代
12. Counterfactual replay 当 ground truth → 只是 directional
13. 只看 aggregate → 某 strata (mental health) 退步被掩盖
14. Address 识别失败 ("我们这栋楼") → cross-ref 来电号码
15. HIPAA + CJIS 合规 → 911 涉及 PHI + 刑事数据, 加密 / 审计 / 数据驻留

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Funnel instrument | Voice agent 7 markets | ASR/LLM/TTS/tool-call latency day-1 instrument, dashboard 不吵架 |
| Multi-source data | Voice agent | customer / call history / repayment / blacklist 4 源 |
| Real-time decision | Voice agent | streaming p99 < 800ms |
| Safety-critical fallback | Voice agent | trust-critical, 转人工 fallback |
| Stepped wedge rollout | Voice agent | RL alignment 跨市分阶段 |
| LLM + ML 分工 | BNPL chatbot | agentic + RAG intent routing, sub-agent |
| Override / HITL | Indonesia refund tier 1/2/3 | tier 1 auto, tier 2 dual confirm, tier 3 manual |
| Override rate North Star | Voice agent | week-1 数据 |
| Counterfactual replay | ConvFinQA ablation | multi-hop reasoning ablation methodology |

### 🎤 面试现场 quotables (top 8)

1. "Let me ask 5 clarifying questions before I draw anything"
2. "I'd narrow this to dispatcher decision support — that's the highest leverage with lowest political risk"
3. "Before being asked, I want to flag 5 failure modes I'd plan for from day 1"
4. "This mirrors my voice agent at TikTok — multi-source, real-time, safety-critical, hard to A/B"
5. "I'd phase this shadow → opt-in → default-on, with override rate as the North Star"
6. "Override is not failure — it's training data. After 7 days of outcome we know if human or AI was right"
7. "A/B test on half the city is ethically off the table. Stepped wedge by zone + counterfactual replay"
8. "The first week deliverable is not a model — it's a funnel dashboard so we stop arguing about feelings"

### 🚨 红线 (top 10 anti-patterns)

1. 上来画 architecture / 算 QPS — 没 clarify = 失分
2. 当 system design 做 (DB shard / QPS) — 不是这题考的
3. 把人 cut out of decision loop — safety-critical 红旗
4. 承诺 6 个月一次性 GA — 没 phasing = 没部署过
5. 假设 GPS / traffic 完美 — 真实 5-15% stale
6. 忽略 dispatcher override — 模型再准, 不信任也白搭
7. A/B 切半个城市 — 伦理灾难
8. 承诺 "30% 改进" 没 buffer — 现实 5-15% 已 huge
9. 忽略 PSAP 工会和政治 — 接警员是工会代表的工种
10. 遗忘 HIPAA / CJIS 合规 — 涉 PHI + 刑事数据

### 📊 数字 anchors (面试必记)

| Metric | Value | Source / Rationale |
|---|---|---|
| NFPA 1710 fire response | 6.5 min P90 (90s pickup + 60s turnout + 240s travel) | 行业标准 |
| Cardiac arrest golden | 4 min, < 10% survival > 10 min | 医学共识 |
| Total response P50 / P90 / P99 (target) | 5:21 / 6:42 / 14:32 | dashboard 关键 3 数字 |
| ETA MAE target | < 60s P90 | GBDT 模型 KPI |
| Demand 预测 MAPE | < 25% on cell-30min granularity | Poisson regression |
| Confidence threshold | > 0.85 + P1 → auto-confirm in 3s | rank decision |
| Override rate healthy | 20-30% | < 10% over-rely warning, > 60% AI bad |
| LLM cost per city | $9300/year (30K calls/day × $0.85 / 1K) | Gemini 3 Flash $0.50/$3 |
| Shadow mode duration | 4-12 weeks | phase 2 |
| Phase 0/1/2/3 | 1w discovery / 2-4w instrument / 4-12w shadow / 5 dispatcher opt-in 3-6m | rollout schema |
| Outcome regression auto-pause | 2-week window | kill switch trigger |
| Mass casualty cluster | 50 calls/sec same location/similar desc | auto-merge logic |
| GPS stale threshold | > 60s | dead reckoning trigger |
| Traffic feed stale | > 5min | no-traffic fallback trigger |
| LLM model | Gemini 3 Flash $0.50/$3 | per 911 call ASR + symptom + code suggest |
| Pre-position model | GBDT 2yr training, MAPE < 25% | Poisson per 8km² cell |
| Optimization horizon | 30min next-period demand | facility location problem |

### 🎯 面试时机分配 (60-min budget)

| 阶段 | 时长 | 必做 |
|---|---|---|
| 0-10 min | Clarify + scope | 5 questions, narrow to 1 sub-problem |
| 10-25 min | Architecture | 3 components: ingest / decision / integration |
| 25-40 min | Deep dive 1 | 通常 decision engine + 实时 traffic |
| 40-50 min | Failure + measurement | 5 failure modes, KPI, dispatcher trust |
| 50-60 min | Phasing | 90-day MVP, phase 2/3

### ⚠️ 必避坑 (interview-specific)

| 坑 | 解法 | Quote |
|---|---|---|
| 一上来画 architecture | 先 5 clarify | "Let me ask 5 things before designing" |
| 当 system design 做 | 别算 QPS | "This isn't about QPS, it's about decomposition + tractable MVP" |
| 把 dispatcher cut out | HITL 3-layer | "Recommendation, not decision — dispatcher always has final call" |
| 承诺 6 个月 GA | phasing | "Shadow 4-12w → opt-in 5 dispatcher → default-on with kill switch" |
| 假设 GPS 完美 | dead reckoning | "Real-world 5-15% stale. Dead reckoning fallback" |
| A/B 切半个城市 | stepped wedge | "Ethically off the table. Stepped wedge by zone + counterfactual replay" |
| 承诺 30% 改进 | 5-15% 已 huge | "Realistic 5-15%, anything more 需要 buffer" |
| 忽略 PSAP 工会 | 早期 sponsor | "Union dispatcher is a real political constraint" |
| 遗忘 HIPAA / CJIS | 加密 + 审计 | "PHI + criminal data, need full compliance stack" |
| 单一 lagging outcome | leading + lagging | "Response time (leading) → assessment (mid) → survival (lagging months)" |

### 💡 ML + LLM 分工 cheat (背诵)

| Component | Tool | KPI |
|---|---|---|
| ASR streaming | Gemini 3 Flash $0.50/$3 | < 800ms p99 |
| Symptom抽取 + dispatch code | Gemini Flash w/ structured output | accuracy > 90% on 26-D-1 type codes |
| ETA estimator | GBDT (LightGBM) | MAE < 60s P90 |
| Demand 预测 | GBDT Poisson regression | MAPE < 25% per cell-30min |
| Pre-position optimization | Google OR-Tools CBC IntVar | facility location seconds-级 solve |
| Confidence calibration | self-consistency + logprob + probe | ECE < 0.05 |
| Override logging | structured table (incident, ai_unit, ai_eta, human_unit, reason, ts) | weekly outcome compare |
| Failure detector | TS heartbeat, OOD embedding distance | per-failure-mode runbook |

### 💡 5 Clarifying Questions cheat (背诵 verbatim)

| Q | 你问什么 | 为啥重要 |
|---|---|---|
| 1 | "Who's the buyer — mayor's office, police, fire? Single KPI?" | 不同 stakeholder metric 完全不同 |
| 2 | "Real-time GPS, or 5-min sampled? On-prem or cloud OK?" | data freshness + integration mode 决定 architecture |
| 3 | "Current baseline response time? Target — 10% or 50%?" | no baseline = no eval |
| 4 | "Dispatch software, predictive routing, or pre-positioning?" | 60min 做不完全部, force scope |
| 5 | "Cost of wrong prediction — fallback?" | safety-critical risk appetite 决定 model 类型 |
