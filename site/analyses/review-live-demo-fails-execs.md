## Client Sim #1 · Demo Fails Before Execs — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](live-demo-fails-execs.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`live-demo-fails-execs.html`](live-demo-fails-execs.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"Your live demo fails in front of customer execs. What do you do?"**, 我按这 7 层回答, 不跳序. 这题考的不是 "你能不能 fix bug", 是 **trust event 的处理 + dialog literally**.

### 📐 Demo Fails Before Execs — 7 层结构

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 (literal) |
|---|---|---|---|---|
| 1 | 30-second recovery script (verbatim) | 1 min | **不沉默不甩锅不假装**. 立刻说出 verbatim: *"OK, that's not the result we expected — let me pause the demo and acknowledge what just happened. I'd rather walk you through what went wrong than fake my way through the rest."* 然后停 2 秒 让 acknowledge sink in | "First thing out of my mouth, literally, within 30 seconds: 'OK that's not what we expected...'" |
| 2 | Demo-vs-core distinction | 2 min | 区分 **"demo environment broke"** vs **"core capability broken"**. 90% 是 demo env (数据脏 / VPN / config), 10% 是 core. **在房间里 explicitly classify** 这两种是不同对话. Demo env 失败 → 我们 5 min 修 + show alternative; core 失败 → admit + reschedule | "Here's the critical question I'd answer for the room first: is this a demo environment issue or a core capability issue? Different conversations..." |
| 3 | Pivot to value conversation | 3 min | 不要硬修 demo. **Pivot to**: (i) what we were trying to show, (ii) why that matters to your business, (iii) **"let me show you data from production not from this demo"**. 把房间从 "demo work?" 转向 "do I trust these people". 开口: > *"Rather than try to brute-force this, let me show you what this looks like in production. I have 3 anonymized customer logs that demonstrate the same capability..."* | "I'd pivot the room within 3 minutes. Not to fix the demo. To re-anchor on value..." |
| 4 | In-room stakeholder map | 2 min | 房间里通常 4 类: **(a) CEO/sponsor (wants confidence)**, **(b) CIO/builder (wants honesty)**, **(c) CFO (wants risk)**, **(d) skeptic (wants you to fail)**. **每类不同 line**: > to CEO: *"this doesn't change our timeline"* > to CIO: *"happy to do a full RCA with your team"* > to CFO: *"our SLA terms cover this scenario"* > to skeptic: *"good question, what specifically concerned you?"* | "Different execs in the room need different sentences. Four archetypes, four lines..." |
| 5 | 24h trust repair playbook | 3 min | 24h 内 deliver: (i) **honest RCA email** (1 page, what happened + why + fix), (ii) **followup call with CIO** 30-min, (iii) **revised timeline** if scope changed, (iv) **demo redo offer** 不是 ask. 7 day 内: hardening + rehearsal + new demo. **Honest RCA 比 silent fix 更建 trust** | "24-hour trust repair has a specific playbook. Four deliverables. Each one before the next..." |
| 6 | Demo hardening for next time | 2 min | 5 hardening rules: (1) **demo env = prod-like data + canned fallback**, (2) **2 rehearsals at exact time-of-day** (network conditions), (3) **2-person tech rehearsal** (1 demo-er + 1 silent debugger), (4) **3 demo paths** (happy, edge, "if everything breaks" canned video), (5) **pre-call 15 min before** | "I'd never demo without 5 hardening checks. Here's my checklist..." |
| 7 | Resume reframe | 1 min | "我做过 voice agent live demo 给 Indonesia partner, 30 秒内 ASR 卡了. 我说: *'Let me show you what this actually looks like in production'*, 切到 anonymized prod log. **3 个月后 partner 签了**. 他们后来跟我说: 那场 demo 卡是 deal-deciding moment because 我们没装" | "I lived this — Indonesia partner demo. ASR stalled. Switched to production logs. Three months later we signed. The CIO later told me the stall was the deal-decider..." |

### 🎯 为啥按这个序

**先 acknowledge (Layer 1), 再 classify (Layer 2), 再 pivot (Layer 3), 再 stakeholder-tailor (Layer 4)** — 因为 90% candidates 沉默后开始 frantically debug, 这是 trust killer. **房间观察的是你怎么处理失败, 不是你能不能修 bug**.

Stakeholder map (Layer 4) 是这题的 **Client Sim 区分项** — ML researcher 给 room 一句话, FDE 知道房间有 4 类人, 4 句话.

### 🔥 哪一层最容易被追问 deeper

- **Layer 1 (30-sec script)**: 面试官会问 "如果 CEO 直接 cut you off 说 'just fix it', 你怎么办?" → 答: > *"Of course, Sir/Ma'am. To be transparent: forcing a fix risks giving you a misleading result. I have 5 minutes of value-content I can show in parallel — would you prefer I do that while my colleague investigates, or pause entirely?"*
- **Layer 5 (trust repair)**: 面试官会问 "RCA 里如果发现是 customer-side 问题 (e.g. VPN), 怎么写?" → 答: never blame the customer in writing. Phrase as *"the demo environment depends on connectivity we don't fully control — we'll add an offline fallback for next session"*

### ⏱ 时间压缩版 (30 min round)

- 5 min: 30-sec script verbatim + classify (Layer 1-2)
- 10 min: pivot + stakeholder map (Layer 3-4, 重点)
- 8 min: 24h trust repair (Layer 5)
- 3 min: hardening playbook (Layer 6)
- 2 min: resume hook — Indonesia demo (Layer 7)

### 🆘 卡壳兜底 (针对这题)

- 卡 verbatim → fall back to **"OK that's not what we expected — let me pause"** 这一句最 universal
- 卡 stakeholder → pivot to **"4 archetypes in the room, 4 different lines"**
- 卡 vulnerability → tell **Indonesia ASR stall — partner signed 3 months later** 故事

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

> **Live demo 失败 = trust event, 不是技术 event**. craft 不在修 bug, 在于**5 分钟内把房间从「他们能 deliver?」转向「他们处理失败的方式让我更信任他们」**, 24h honest RCA, 1 周 hardening 防下次. 高管签合同看的是失败应对能力, 不是 demo 完美度.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| A·D·O·R | Acknowledge / Diagnose / Offer / Recommit | 现场恢复 4 步 framework |
| RCA | Root Cause Analysis, 5-why | 24h 内 honest 1-pager |
| Golden path test | demo 流程的 automated end-to-end test | 每 30min 自动跑 |
| Frozen demo env | 独立 cluster, 24h code freeze | Layer 1 hardening |
| Hot standby | 同步 secondary demo env | 失败立刻切 |
| Pre-flight check | demo 前 30min health screenshot | 给客户高 confidence |
| Standby engineer | next room 看 dashboard 的人 | 60s slack 给 hypothesis |
| Demo certification | demo lead 签字 + checklist + failure metric | organizational level |
| Business sponsor | 客户内部 champion (Maria 等) | 必须私下 brief + ammunition |
| Pivot Option 1-4 | 录屏 / observability / whiteboard / reference | ranked by effectiveness |
| 5-why | 连问 5 次 why | RCA 根因方法 |
| Demo bug | env/data/network/operator | 60+20+10+2 = 92% case |
| Core product bug | 主路径真错 | 8% case, 必须诚实承认 |
| Frozen artifact | data fixture / config 不变 | 防 drift |
| facial leak | "uh / weird / hmm" 表情/语言 | 红线, 绝不允许 |
| Service credit | 财务补偿 | re-demo 再失败时备用 |

### 🎯 5 个核心 framework

**Framework 1**: A·D·O·R Recovery (0-30 min)
- When: demo 屏报错的瞬间
- Algorithm: A 第 5-10s acknowledge + ownership (不 deflect) → D 2min 硬上限 diagnose (超时 pivot) → O 录屏/observability/use case 三选一 → R EOD tomorrow + Thursday 10am 具体 commit
- Trade-off: 时间压力 vs 思考时间, 慢说 > 快错
- Tools: 30s verbatim script, 微表情 / 肢体 checklist, manager signal protocol (head tilt)

**Framework 2**: Demo Bug vs Core Bug Admission (3 min)
- When: 当下不知道根因, 但客户问 "is this happening in prod"
- Algorithm: 5 hypothesis 排序 (60% demo env / 20% infra / 10% edge prompt / 8% core bug / 2% operator) → 90% demo: 承认 demo + 给 dashboard 证据 / 50/50: 拒绝当场猜 + EOD RCA / 90% core: 主动承认 + frame 为 monitoring 价值
- Trade-off: 诚实 vs 自我保护
- Tools: production health dashboard 截图 backup, real-time status page, 90s call-out 给 SRE team

**Framework 3**: Pivot to Value (5-30 min)
- When: 2min 没修好
- Algorithm: 4 选项 ranked: 录屏 narrate ⭐⭐⭐⭐⭐ / observability talk (4-layer) ⭐⭐⭐⭐⭐ / whiteboard customer's use case ⭐⭐⭐⭐ / reference customer ⭐⭐⭐
- Trade-off: 录屏需提前准备, observability 需真懂架构
- Tools: backup 录屏 (任何重要 demo 前 30min 录, 救命), 4-layer monitoring sample script

**Framework 4**: 24h Trust Repair (Email + RCA)
- When: 会议结束后立刻
- Algorithm:
  - 30min 内: follow-up email (what happened / commitments / asks / phone)
  - 24h 内: RCA 1-pager (timeline PST / direct / 5-why / customer impact / mitigations / long-term / prod behavior / why re-demo won't fail / contact)
  - 私下: brief business sponsor + give ammunition
- Trade-off: honest RCA 暴露内部问题 vs sanitize PR-style 失信
- Tools: phone in email signature, 1-pager template, video call backup

**Framework 5**: 5-Layer Demo Hardening (1 week)
- When: re-demo 前
- Algorithm:
  - Layer 1 Frozen env (code freeze 24h, data fixture v-pinned, no-deploy calendar)
  - Layer 2 Golden path automated test (每 30min, fail → page + hot-standby)
  - Layer 3 Pre-demo health check 30min before + screenshot to customer
  - Layer 4 Dry-run protocol (3 consecutive pass, 失败重置计数器)
  - Layer 5 Standby engineer in next room, Slack alert 60s hypothesis
- Trade-off: 工程量大, 但 staff-level signal
- Tools: demo-env-policy.yml, golden_path_test.py, pre-demo-check.sh, demo certification

### 🌳 关键决策树

```
Demo 屏报错的 30 秒
├── 0-3s: 深呼吸, 不要 facial leak, 视线离屏看人
├── 5-10s: "OK, looks like the demo is hitting an issue. Let me handle that directly — give me 2 minutes"
├── 15s: pre-commit pivot plan
└── 30s: 已做 5 件事 (acknowledge / ownership / 2min / pre-pivot / time respect)

2 分钟到了还没修?
├── 90% 把握 obvious fix? → 继续 30s
├── < 90%? → 立刻 pivot, 不死磕
└── Pivot 选项:
   ├── 录屏 backup 有? → Option 1 ⭐⭐⭐⭐⭐
   ├── observability/monitoring 能讲? → Option 2 ⭐⭐⭐⭐⭐
   ├── 客户 use case 准备过? → Option 3 ⭐⭐⭐⭐
   └── 都没有? → Option 4 reference customer ⭐⭐⭐ (最后)

被问 "is this in prod now"?
├── 90% demo env, 有 dashboard? → 看实时, "prod healthy 24h, still full RCA tomorrow"
├── 没准备 dashboard? → "screenshot by EOD + RCA tomorrow"
└── 怀疑 prod 也受影响? → "step out 90s call SRE, take 2-min break"
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: 30-Second Recovery Script**
- 核心解法:
  > "OK, looks like the demo is hitting an issue."
  > (1 拍停顿)
  > "Let me handle that directly — give me 2 minutes."
  > "If it's not obvious in 2 minutes, I'm going to pivot to [recorded run / architecture walkthrough] rather than burn your time."
- Top 3 gotchas: "uh / weird / hmm" facial leak / 看屏不看人 / "real quick" setup-for-failure
- Tools/tactics: 视线扫到最远 CEO, 降速 20%, 单一手势 open palm, manager head tilt signal

**Problem 2: Demo Bug vs Core Bug Admission**
- 核心解法:
  ```
  if 90% demo env + dashboard:
    "demo issue, prod healthy, here's dashboard, still full RCA tomorrow"
  if 50/50:
    "don't speculate, EOD tomorrow RCA, recommend (b) over guessing"
  if 90% core:
    "honest: could be product issue, RCA tomorrow + monitoring walkthrough now"
  if don't know:
    "step out 90s call SRE for yes/no on prod impact"
  ```
- Top 3 gotchas: 明知 core 还说 demo (reputation 杀手) / 空口说 prod 好没证据 / 当场猜根因
- Tools/tactics: prod dashboard screenshot ready, status page bookmark, SRE phone

**Problem 3: Pivot to Value (用 failure 当 sales 武器)**
- 核心解法:
  ```
  Transition: "Rather than debug this live in front of you — and I really don't want to do that to your time —
              let me show you something arguably more valuable: [pivot]. I think you'll get more out of [pivot] right now."
  
  Option 2 (4-layer monitoring talk):
  Layer 1: success rate < 99.5% over 5min → alert
  Layer 2: per-tenant synthetic txn every 30s, 2x fail → page on-call
  Layer 3: failure correlation (deploys/deps/traffic), RCA hypothesis 60s
  Layer 4: graceful degradation (scripted fallback for debt collection)
  Takeaway: demo 1x 502, prod 0 customer impact
  ```
- Top 3 gotchas: pull out slide deck (= 投降) / 干讲架构 1h / reschedule 5min 内说 (太早)
- Tools/tactics: backup 录屏 prep cost 30min, observability talk sample script, whiteboard

**Problem 4: Postmortem + Trust Repair (Day 0-30)**
- 核心解法:
  ```
  30min: follow-up email (subject "[Acme] Today's session - written follow-up")
    - What happened (2 bullets)
    - Committed (RCA EOD tomorrow / Thursday 10am re-demo / monitoring deep-dive)
    - Asks (additional scenarios / alt times)
    - Phone for direct reach
  
  24h: RCA 1-pager
    Timeline PST / Direct cause / 5-why root / Customer impact (prod=0, demo=...) /
    Mitigations 24h / Long-term prevention / Production behavior /
    Why re-demo won't fail / Contact
  
  Private: brief business sponsor + give ammunition for internal spin
  ```
- Top 3 gotchas: PR-style sanitized RCA (高管闻得到 spin 味) / 漏发 follow-up email / 不 brief sponsor (他次日背锅)
- Tools/tactics: RCA 1-pager template, phone in signature, "the way I handle this is the way we'd handle prod"

**Problem 5: Demo Hardening Process (5 layers)**
- 核心解法:
  ```
  Layer 1: demo-env-policy.yml frozen, code freeze 24h, data fixture v-pinned, no-deploy/no-load-test calendar
  Layer 2: golden_path_test.py per 30min cadence (login → click → ASR → tool call → CRM writeback)
  Layer 3: pre-demo-check.sh @ T-30min, screenshot 发给客户
  Layer 4: 3 consecutive dry-run pass, failure 重置计数 → 0/3
  Layer 5: standby engineer next room + Slack alert + 60s hypothesis
  Talking point: "same rigor we'd put on a prod release"
  ```
- Top 3 gotchas: re-demo same env (同灾难) / 没 backup 录屏 (= 没 plan B) / failure rate 不是 team metric
- Tools/tactics: demo certification (lead 签字 + checklist + SLA), Slack channel monitoring, ethernet > WiFi

### 🔥 Production gotchas (top 15)

1. Long silence while debugging → 房间气压暴跌
2. Blame env / customer → 信任 -50
3. Punt to "engineering" → 你是 middleman 不是 owner
4. Promise speedy fix 不检查 → 2 次失败 trust 归零
5. Don't write follow-up email 30min → 高管记忆漂移
6. Defensive body (pacing/sigh/looking away) → 高管读姿态
7. Re-demo too soon (同 env 同 risk) → 同灾难
8. Postmortem 写成 PR 稿 → 失信
9. 不私下 brief business sponsor → 失去内部 champion
10. 没 process change story → 救场不救信任
11. 明知 core bug 装 demo issue → reputation 杀手
12. AE 当面 over-promise "24h fix guarantee" → follow-up email 校准
13. Re-demo also fails → 不 demo 第 3 次 + 邀客户 tech lead 进 staging
14. 客户 CEO 发脾气 → 不 argue, "What can I commit in 24h to help trust"
15. 客户要求 talk to VP → 不 block, 48h 内 set up + brief VP

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Demo recovery 监管场景 | 印尼 BNPL chatbot OJK demo | Thai prompt 泄漏到 Indonesia model, 你 handle 过 |
| Standby + pre-flight | Voice agent 7 markets 上线 | 每市场上线 = demo, build health check |
| Frozen demo env | Voice agent staging vs prod | isolation 你做过 |
| Golden path test | ConvFinQA eval harness | 你的 9-variant ablation harness 思路 |
| Honest RCA | ConvFinQA negative result | 9 个 variant 都没超 baseline, 公开报告 |
| Process change from incident | Indonesia refund tier scoping | from incident to process |
| 跨 stakeholder 政治 | 跨 7 markets | regional GM / 法务 / 客户 |
| Sales asset 转化 | OJK demo failure 后签更快 | "they signed faster after the failure than before" |

### 🎤 面试现场 quotables (top 8)

1. "OK, looks like the demo is hitting an issue. Let me handle that directly — give me 2 minutes"
2. "Rather than debug live in front of you — and I really don't want to do that to your time — let me show something arguably more valuable"
3. "This failure mode is exactly what we'd build production monitoring for — let me show you the 4 layers"
4. "I want to be honest with you: this could be a real product issue. RCA by EOD tomorrow with whether other customers are affected"
5. "I'd rather commit to a 1-page RCA by EOD tomorrow than speculate. What I won't do is pretend I know"
6. "The way I handle this issue is the way we'd handle any production issue with you as a customer"
7. "Indonesia OJK demo failed mid-call. We signed faster after the failure than before — they saw how we handle real failure"
8. "Don't optimize for never failing. Optimize for failing professionally — that's what enterprise customers really pay for"

### 🚨 红线 (top 10 anti-patterns)

1. "Works fine in our env" (blame customer)
2. "Known issue" (admits other bugs)
3. "Engineering will look" (middleman)
4. "Real quick" (setup-for-failure)
5. "Oh shit / weird / hmm" (verbal leak)
6. Long silence > 10 秒 no acknowledgment
7. Defensive body language (pacing / sigh)
8. Re-demo without hardening
9. PR-style sanitized RCA
10. 漏 brief business sponsor (他次日背锅)

### 📊 数字 anchors (面试必记)

| Metric | Value | Source |
|---|---|---|
| Acknowledge response time | 5-10 seconds, no facial leak | 第一动作 |
| Diagnose hard cap | 2 min, then pivot | magic number |
| Manager signal | head tilt = jump in / nothing = hold | pre-aligned |
| Demo failure root cause % | Demo env config 35% / data 25% / upstream 20% / network 10% / operator 10% | hardening focus |
| Code freeze before demo | 24h | Layer 1 hardening |
| Golden path test cadence | every 30 min until demo start | Layer 2 |
| Pre-demo health check | T-30 min, screenshot to customer | Layer 3 |
| Dry-run protocol | 3 consecutive pass, reset counter on fail | Layer 4 |
| Standby engineer | 60s Slack hypothesis SLA | Layer 5 |
| Follow-up email | 30 min after meeting | written record |
| RCA 1-pager | 24h after incident | trust repair |
| Re-demo | minimum 48-72h after first failure | not too soon |
| Backup recording | 30 min cost to record, save the deal | proactive |
| Production health dashboard | screenshot ready, "prod healthy 24h" | demo bug vs core admission |
| Phone in email signature | direct reach signal | ownership |
| Trust repair timeline | Day 0 recovery → Day 1 RCA → Day 2-7 hardening + re-demo → Wk 2-4 unsolicited reports → Q1 QBR → Mo 6 normalized | 6 month |
| Outage probability if Path B (full scope, 3d) | 15-20% | hardening incentive |
| Service credit consideration | offered if re-demo also fails | retention |
| 4-layer monitoring talking point | Layer 1 success rate < 99.5% / Layer 2 30s synthetic / Layer 3 60s RCA / Layer 4 graceful degrade | pivot Option 2

### 💡 30-Second Recovery Script cheat (背诵 verbatim)

| 第几秒 | 你的动作 + 句子 |
|---|---|
| 0-3s | 深呼吸 2s, 不 "啊" / "诶" / "嗯", 视线从屏幕移开看远处 CEO |
| 第 5 秒 | "OK, looks like the demo is hitting an issue." |
| 第 7 秒 | (停 1 拍, 不 "but" / "however") |
| 第 8 秒 | "Let me handle that directly — give me 2 minutes." |
| 第 15 秒 | "If it's not obvious in 2 minutes, I'm going to pivot to [recorded run / architecture walkthrough] rather than burn your time. I'd rather you leave with substance than watch me debug." |
| 第 30 秒 | ✓ 5 件事: acknowledged 问题 / ownership / 2min limit / pre-pivot / time respect
