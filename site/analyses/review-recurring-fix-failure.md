## Client Sim #3 · Recurring Fix Failure — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/recurring-fix-failure.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`recurring-fix-failure.html`](questions/recurring-fix-failure.html)

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

> **3 次 fix 都失败不是「第 4 次更努力」, 是「诊断方法本身错了」**. craft 不在修 bug, 在敢做反直觉决定: stop-the-line + 1 周 just RCA 不写代码 + fresh eyes + 立即 feature flag 缩小 blast radius. 客户失信不是 1 次 fix 修的, 是数月 consistent professionalism 修的. Trust 失 1 小时, 重建 3-6 月.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| RCA | Root Cause Analysis, 5-why 找症状之下原因 | 永远 > fix-the-bug |
| 5-Why | 连续 5 个 why 到 process gap | 真 root cause 是 process 不是 code |
| Stop-the-line | Toyota TPS 任何人发现质量问题 halt | 3 次 fix 失败强制 trigger |
| Blameless postmortem | 不归罪个人归罪 process/system | Google SRE 经典实践 |
| Trust debt | 类 technical debt 但社会维度 | 3 次失败 = trust account ≈ 0 |
| Blast radius | 单 incident 影响范围 | 第一优先缩小 (feature flag/kill switch) |
| Pattern recognition | 失败次数 1/2/3/4 信号不同 | 知道何时承认 not push 第 4 次 |
| Fresh eyes | bring in 没碰过此 bug 的 PE | break stuck thinking |
| Pair debug | 客户 eng 同屏共同 reason | radical transparency |
| Hypothesis tracking | 公开 board, ruled-in/ruled-out | RCA week 必备 |
| 30/60/90 milestone | stabilization / maturity / normalization | trust rebuild timeline |
| Service credit | 3-month free + PE pro bono week | 财务面 customer 出口 |
| QBR | Quarterly Business Review | 90 day 后 sustained stability |
| Architectural issue | 不是 bug, 是 design 错 | 必 transparent, 给 3 path |
| Damages | 客户 legal 措辞 | 多数是 negotiation leverage |
| Sponsor ammunition | 私下给 Maria 内部 spin 材料 | 失去她 = 失去 internal 推进 |

### 🎯 5 个核心 framework

**Framework 1**: A·R·R·R Recovery (现场 + 24h 内)
- When: 客户表达失去信任
- Algorithm: 1. Admit process-level fault ("our diagnostic was wrong, not just code") 2. Reset approach (fresh PE, RCA week, pair-debug) 3. Reduce blast radius (feature flag/kill switch 一行命令) 4. Re-earn over time (30/60/90 day stability)
- Trade-off: 反直觉 (慢下来), 但快是 trap
- Tools: feature flag (LaunchDarkly), 30-day grace ask, structured daily 10-min sync

**Framework 2**: Pattern Recognition (3 是 magic number)
- When: fix 失败计数
- Algorithm:
  - 1 次: standard fix flow
  - 2 次: deeper RCA before fix 3
  - 3 次: **诊断方法 / hypothesis class 错了** → stop-the-line restart
  - 4 次: crisis mode, leadership escalate
- Trade-off: 数学上 root cause 找到 fix 90%+ 成功, 连续 3 次 fail = hypothesis distribution 整体偏移
- Tools: 5-Why 重走 (3 次共同 blind spot), hypothesis log, 假设类目

**Framework 3**: Stop-the-Line + RCA Week
- When: 3 次 fix fail OR 客户明确 trust loss OR fix 引新 bug OR 监管事件
- Algorithm:
  - Day 1: hypothesis explosion (20+, 别 self-censor)
  - Day 2: triage to top 5
  - Day 3: deep investigation
  - Day 4: convergence to top 1-2
  - Day 5: writeup + customer review
- Trade-off: 1 周不写代码 vs 客户焦虑, 必 daily sync 平衡
- Tools: hypothesis board, daily customer sync 10-min same time, ruled-out list 公开 growing

**Framework 4**: Fresh Eyes + Pair Debug
- When: 你 stuck in same hypothesis
- Algorithm:
  - PE onboarding: 不先 share 你的 hypothesis, 让他独立 form view, day 3 compare
  - Converge → both possibly wrong (你已经错 3 次); Diverge → their view leads
  - Pair with customer eng: screen share 2h, out-loud reasoning, 让他 keyboard time, joint hypothesis
- Trade-off: 自尊心 vs 让别人来, "我 dedicated" 反而是 ego trap
- Tools: PE scoped 1-week engagement, customer eng 同屏 (Zoom screen control)

**Framework 5**: Trust Rebuilding Playbook (30/60/90 + signals)
- When: post-RCA, 长期修复
- Algorithm:
  - Day 1-30 Stabilization: daily sync, dashboard, service credit applied
  - Day 31-60 Maturity: 3x/week sync, QBR prep
  - Day 61-90 Normalization: weekly sync, QBR, NPS check
  - Signals: customer proposes Tier 2 (rebuilding) / introduces other teams (strong) / references you (recovered) / NPS positive (quantitative) / daily sync reduced by customer (confidence)
- Trade-off: 3-6 月慢, 但 promise faster = lie
- Tools: stability tracker dashboard, weekly health report unsolicited, QBR template

### 🌳 关键决策树

```
Fix 失败计数?
├── 1 次 → standard fix flow
├── 2 次 → deeper RCA, deeper hypothesis
├── 3 次 → STOP-THE-LINE
│   ├── 1 week RCA no patches
│   ├── Fresh PE bring in
│   ├── Feature flag immediately (blast radius)
│   ├── Pair debug with customer eng
│   └── 30-day grace ask
└── 4 次 → crisis, leadership escalate, service credit, retention

客户表达失信
├── 第一句永远: "You're right to be frustrated"
├── 不 defend, 不 list mitigations
├── Process-level admission "diagnostic was wrong, not code"
└── 4 commitments: fresh eyes / 1 week RCA / blast radius / pair-debug

发现 architectural issue (6-month rewrite needed)?
├── 必 transparent 即使客户 walks away
├── 3 paths offered:
│   ├── Workaround (1-2 weeks, technical debt)
│   ├── Rewrite (6 months, clean)
│   └── De-scope (避免该 use case)
└── 客户选, 你不 push

CFO 提 damages?
├── 多数 = negotiation leverage 不是 legal
├── Escalate to your CEO + CFO
├── Service credit (6 months) before legal
└── Acknowledge cost without promising damages
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: Pattern Recognition (3 次失败信号)**
- 核心解法:
  ```
  3 次 fix 共同 blind spot:
    Fix 1: prompt rule
    Fix 2: model tune
    Fix 3: post-process classifier
    Common assumption: 模型/prompt/算法不够好
    Missing: 数据 distribution (Indonesian + Javanese 双语客户 underrepresented)
  
  5-Why 第 4 次重走:
    Why 5% error? → misclassified
    Why? → sarcasm + double negation
    Why misclassed? → training data 不含该 pattern
    Why not? → 数据收集 sample 不 cover bilingual
    Why? → 数据 spec 没要求 representative
  → 真 root cause: data spec process gap
  ```
- Top 3 gotchas: 同一 hypothesis class 反复 / "this time" 第 3 次说 / 不 question data distribution
- Tools/tactics: hypothesis 类目分类 (model/data/infra/UX), 5-Why 强制 5 层

**Problem 2: Stop-the-Line + RCA Week**
- 核心解法:
  ```
  Triggers: 3 fixes same class / explicit trust loss / fix 引新 bug / 监管
  Day 1: 20+ hypothesis explosion (别 self-censor)
  Day 2: triage to top 5
  Day 3: deep investigate
  Day 4: converge top 1-2
  Day 5: writeup + customer review
  
  No code changes 这一周 (除 critical safety)
  Daily customer update: "Today X, ruled out, next Y"
  Hypothesis tracking board: 公开 ruled-in/ruled-out
  Pair session with customer eng 2x/wk
  RCA writeup 不 sanitized end-of-week
  ```
- Top 3 gotchas: 1 周不写代码客户焦虑 (用 daily sync 平衡) / hypothesis self-censor / RCA sanitize
- Tools/tactics: shared hypothesis board (Miro/Notion), structured daily 10-min agenda

**Problem 3: Communication During Repeated Failure**
- 核心解法:
  ```
  4-Layer transparency:
    L1: We deployed fix (standard)
    L2: We think it's X (RCA daily)
    L3: We tested X, ruled out, trying Y (pair-debug style)
    L4: Our diagnostic was wrong (turning point admission, only 1x)
  
  Day-of script:
    "You're right to be frustrated"
    "Our diagnostic was wrong, not just our code"
    "I'm bringing in fresh eyes"
    "1 week of just RCA, no patches"
    "30-day grace before contract decision"
  
  Sponsor private ammunition:
    Maria 内部背锅, 给她 1-pager she can use internally
    explanation that doesn't sound like vendor spin
  ```
- Top 3 gotchas: "This time we got it" (3 次后 = credibility burn) / spin progress / 内部 misalignment 当面
- Tools/tactics: structured daily sync agenda, ruled-out list 公开 growing, sponsor 1:1 私下

**Problem 4: Fresh Eyes / Rotate Engineer**
- 核心解法:
  ```
  PE onboarding:
    Don't share your hypothesis first
    Let them form independent view
    Compare on day 3:
      Converge → both possibly wrong (你已经 wrong 3x)
      Diverge → their view leads
  
  Pair debug with customer eng:
    Screen share 2h
    Out-loud reasoning ("here I'm thinking it's X because Y")
    Customer eng keyboard time (joint experiment)
    Joint hypothesis + next test
  
  Scoped engagement:
    PE 1 week RCA + bounded follow-on
    Don't drag PE into long-term ownership
  ```
- Top 3 gotchas: 自尊心 (我 dedicated 自己 own) / share hypothesis 先 bias PE / PE 被 dragged into 长期 ownership
- Tools/tactics: Zoom screen control, PE engagement scope doc, customer eng joint invitation

**Problem 5: Trust Rebuilding Playbook**
- 核心解法:
  ```
  Service credit defaults:
    3-month free service
    + 1 PE pro bono week
    + RCA published
    + 30-day grace before exit
  
  30/60/90 milestones:
    Day 1-30: stabilization, daily sync, dashboard, credit applied
    Day 31-60: maturity, 3x/wk sync, QBR prep
    Day 61-90: normalization, weekly sync, QBR, NPS check
  
  Trust rebuild signals (you monitor):
    Customer proposes Tier 2 → rebuilding
    Customer introduces other teams → strong
    Customer references you → recovered
    NPS positive at 90 days → quantitative
    Customer reduces daily sync cadence → confidence
  
  Don't promise faster trust rebuild — 6 months realistic
  ```
- Top 3 gotchas: 30-day trust = lie / 没 service credit (财务 customer 没出口) / 不 unsolicited weekly health report
- Tools/tactics: dashboard 共享 read-only, weekly health PDF, NPS quarterly survey

### 🔥 Production gotchas (top 15)

1. "This time we got it" 第 3 次说 → 信用归零
2. Argue or defend → "You're right to be frustrated" 第一句
3. No process-level admission → 客户看出 still treating 1 bug
4. No blast radius reduction → 客户继续 bleed
5. Spin progress "we've made strides" → 长期灾难
6. Promise rapid trust rebuild → 失信
7. Hide architectural issue → 第 4 次 fix explode, 永久 lost
8. Same engineer keeps fixing → stuck in same hypothesis
9. No customer-facing visibility → anxiety amplifies
10. Internal misalignment in front of customer → confidence erosion real-time
11. Skip service credit → 财务 customer 没出口
12. Ship fix Friday afternoon → weekend 灾难复发
13. Architectural issue 没 3-path → 客户没选择权
14. CFO damages 直接 legal → 多数是 negotiation leverage, 先 credit
15. 不 brief sponsor → 失去内部 champion

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Pattern recognition 3 次 | Voice agent Indonesia | bilingual sarcasm 反复 fix 都没解 |
| Data coverage 真 root | Voice agent ASR | Javanese underrepresented |
| Stop-the-line RCA week | ConvFinQA ablation | 9 个 variant 都失败, 暂停 sprint 做 RCA |
| Fresh eyes | Refund tier 设计 | bring in cross-team review |
| Service credit | Internal Agent Platform | scoped re-engagement |
| Pair debug | 跨 ByteDance 内部多团队 | 同屏共同 reason |
| 30/60/90 milestone | Voice agent 7-market rollout | 渐进 stability check |
| Transparency 4-layer | ConvFinQA negative result | L4 admission 论文公开 |
| QBR sustained | Voice agent | quarterly market health review |

### 🎤 面试现场 quotables (top 8)

1. "You're right to be frustrated"
2. "Our diagnostic approach was wrong, not just our code"
3. "I'm bringing in fresh eyes — a principal engineer who hasn't touched this"
4. "1 week of just RCA, no patches. I know that sounds counterintuitive, but 3 failed fixes mean we're patching the wrong thing"
5. "Would you give us 30 days under this plan before deciding cancel? Service credit attached"
6. "I won't promise rapid trust rebuild — that's a lie. 3-6 months of consistent professionalism is realistic"
7. "Indonesia voice agent 5% error — we fixed prompt, model, post-process, all same hypothesis class. Real cause was bilingual data underrepresented. 3 fixes failed because 3 fixes were the wrong class"
8. "Trust is lost in hours, rebuilt in months"

### 🚨 红线 (top 10 anti-patterns)

1. "This time we got it" (credibility burning)
2. Defend / argue when customer frustrated
3. Spin progress ("we've made great strides")
4. Hide architectural issue if discovered
5. Same engineer keeps fixing
6. Friday afternoon fixes
7. Promise rapid trust rebuild (30-day = lie)
8. No blast radius reduction
9. No service credit discussion
10. Internal misalignment in front of customer
