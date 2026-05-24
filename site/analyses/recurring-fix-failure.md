## 题目（verbatim）

> "Deployed fix fails; the **same problem recurs**; client is **losing confidence** in your team. How do you communicate, what do you change in your process?"

**出处**: fde.academy 客户模拟. Palantir / OpenAI / Salesforce / Stripe FDE 都问过. 真实 deployment 最难的 moment 之一.

**Round**: Client Simulation (45 min)

---

## 这道题在考什么

你能不能 **professionally own a streak of failures** + 在客户失去信任的 brink 把关系拉回来:

1. **Stop digging the hole** — 别再 promise quick fix
2. **Process-level admission** — 不是"this bug specific", 是"我们的诊断方法有问题"
3. **Bring in fresh eyes** — 你已经 stuck in same hypothesis
4. **Compensation** — offer something they didn't ask for
5. **Plan to rebuild trust** — rebuild trust is **months**, not 1 fix
6. **Pattern recognition** — 知道「3 次失败」意味着什么 (root cause 没找到)
7. **Stop-the-line decision** — 何时 halt + 做正经 RCA

这道题考的不是 debug 技能, 是**职业成熟度**: 能不能在压力下做出反直觉但正确的决定 (halt > push more fixes).

---

# Part 1 · 教学讲解

## 1. 五个核心术语先解释

**RCA (Root Cause Analysis)**: 深度诊断, 找到「症状之下的真正原因」. 跟 "fix the bug" 不同 — fix 是 symptom, RCA 是 cause. 例如: 系统 OOM 多次, fix 是加内存, RCA 是「memory leak in module X due to unclosed connections in error path」.

**5-Why technique**: 连续问 5 次 "why" 直到 root cause. 例: 「Service A 慢」→ 「DB query 慢」→ 「Missing index」→ 「Schema migration 忘了 index」→ 「Code review 没 catch」→ 「我们没有 schema review checklist」. 真 root cause 是 process gap, 不是 missing index.

**Stop-the-line**: 来自 Toyota Production System. 任何工人发现质量问题, 都有权 stop the line. 应用到软件: 任何 engineer 发现严重 bug recurring, 都应该 halt feature work + 做 RCA, 而不是继续 patch.

**Blameless postmortem**: 事故复盘但**不归罪个人**, 归罪 process / system. Google SRE 经典实践. 目的: encourage honesty (大家敢说真因) 而不是 cover-up.

**Trust debt**: 类似 technical debt 但是社会维度. 每次失败 = 透支客户 trust account. **3 次连续失败 = trust account 接近 zero**. 修复需要数月「按时 + 透明」, 不是 1 次 perfect fix.

**Blast radius**: 一次 incident / bad fix 影响的范围. 0 影响 < 单租户影响 < 全产品影响. 修复优先级第一是**缩小 blast radius** (feature flag, kill switch), 然后才是修 root cause.

---

## 2. 这个场景的核心矛盾是什么

**矛盾 1: 紧迫感 vs 慢工出细活**

客户 push "fix it NOW". 你的本能也想 deliver fast. 但**3 次失败的 pattern 告诉你: fast fix 是 trap**. 需要 deliberately 慢下来.

**矛盾 2: 自我证明 vs 承认 process 失败**

你想证明「I'm competent, 这次 will work」. 但客户已经听过两次「this time」. 第三次说「this time」=信用归零. 必须**承认 process level fault**, 不是 individual.

**矛盾 3: 救火 vs 缩小 blast radius**

工程师 default 是 dive into code 修 bug. 但客户最痛的不是 bug 本身, 是 bug 在生产持续暴露. **第一步应该是 kill switch / feature flag**, 防止 bug 继续 hurt 客户, 然后才是修.

**矛盾 4: 给客户 visibility vs 不让 visibility 变成 micromanagement**

客户失去信任, 想要 visibility. 给 daily sync 显得过 needy. 不给 visibility 让他猜想最糟. 平衡: **structured cadence with clear deliverables**, 不是 unstructured chat.

**矛盾 5: 个人责任感 vs 团队 ownership**

你想自己 own 修复, 显示 dedication. 但**fresh eyes 才能 break stuck thinking**. 自尊心 vs 让别人来.

**矛盾 6: 短期客户挽回 vs 长期产品稳定**

如果架构有问题 (e.g., 6-month rewrite needed), 是该 transparent 还是 hide? **必须 transparent**, 即使客户 walks away. Lying 是更大长期损失.

---

## 3. 决策树 / 反应模板

| 时间 | 你的核心动作 | 关键句 |
|---|---|---|
| **客户表达失去信任时** (0-5 min) | Acknowledge + 不 defend | "You're right to be frustrated" |
| **5-15 分钟** | Process-level admission + commit fresh approach | "Our diagnostic was wrong, not just the code" |
| **15-30 分钟** | 4 commitments: fresh eyes / no-fix RCA week / blast radius reduction / pair-debug | (see Sample script) |
| **24 小时内** | RCA week start + feature flag deployed + daily 10-min sync set | (Process change visible) |
| **Week 1** | No new fix, only investigation. Customer sees us "thinking out loud" | Daily updates with hypothesis evolution |
| **Week 2-4** | Targeted fix based on RCA. Multi-layer review. Pair-debug with customer | New fix is qualitatively different (not patch) |
| **Month 1-3** | 30 / 60 / 90 day stability checkpoint | Trust rebuilding via consistent delivery |
| **Month 3-6** | Relationship normalization | Failure becomes "remember when..." story |

---

## 4. 关键利益相关方对照表

| Stakeholder | 他们在意什么 | "3 次失败" 时他们的内心 OS | 你对他们的关键动作 |
|---|---|---|---|
| **客户 CTO** (升到他这一级了) | 工程团队能不能可靠 | "Is this team competent or am I babysitting them?" | Process-level admission + fresh principal engineer + transparency |
| **客户 CFO** | Cost / risk / 是否 walk away | "We've sunk $500K, what's exit cost?" | Service credit + 30-day grace period + concrete metrics |
| **客户 工程师** (你的对接人) | 技术细节 / 共同 debug | "Vendor is hiding something" | Pair-debug + share internal logs + radical transparency |
| **客户 业务方** (sponsor) | 自己面子 + 项目 status | "I推 这家厂商, 现在被打脸" | Private ammunition: explanation she can use internally |
| **你的 EM** | Team morale + technical debt | "我的人 stuck in patches" | Stop-the-line authority + bring in principal eng |
| **你的 AE** | 这单是否丢 | "Is contract at risk?" | Real status, don't hide. Coordinate retention strategy |
| **你的 director** | 这单 + 你的 career | "Is FDE handling this OK?" | Brief regularly, ask for backing on 30-day grace plan |
| **你的 PE / Principal engineer** (你 bring in) | Help solve + 不被 dragged into 长期 ownership | "Why is FDE bringing me in" | Scoped engagement: 1 week RCA + bounded follow-on |

---

## 5. 具体业务场景 (4 个变种带人物)

### 场景 A: TikTok PayLater 客服 voice agent 「拒绝识别失败」反复 ship-break (贴近 Gao Xin 工作)

**人物**:
- 你 (FDE) + EM Linda + PE Marco
- 客户 (Indonesia ops): Maria (Ops Director), Andi (Tech Lead), Maria 的老板 Bambang (CTO)

**问题**: AI agent 在 5% 通话中错把客户 "no" 识别为 "yes I'll pay" (反讽 / sarcasm / Indonesian 双重否定). Fix 1: 加 prompt rule → 仍 4.8%. Fix 2: tune model → 仍 4.5%. Fix 3: 加 post-process classifier → 仍 4.6%. **3 次 fix, 错误率没降到 3% 以下**.

**Bambang 表情** (CTO 第一次出场): "I'm seriously considering canceling. What's your team doing?"

**真 root cause** (你后来 RCA 找到): 错误数据 distribution 集中在 Indonesian + Javanese 双语客户, 训练数据里 underrepresented. **不是 prompt / model / post-process 任何一个能 fix 的, 是 data coverage problem**.

→ Part 2 全部以此为蓝本.

### 场景 B: BNPL chatbot 状态丢失反复

**问题**: 客户在 chatbot 里完成 KYC verification, refresh 后 state 丢, 要 re-do. Fix 1: 加 session storage → 仍丢. Fix 2: 移到 server-side session → 部分修. Fix 3: 加 retry → 仍丢.

**真 RCA**: load balancer 不 sticky, 用户在不同 backend node 之间跳, server session 失败. 没人之前注意到 LB 配置.

### 场景 C: Acme Bank dashboard 数据 inconsistency

**问题**: Top-10 customer revenue 数字偶尔 mismatch source data. Fix 1: 加 cache invalidation → 仍 mismatch. Fix 2: 改 query → 仍. Fix 3: 加 reconciliation job → 仍.

**真 RCA**: ETL pipeline 跨 timezone, 某些 customer 数据用 UTC vs local time 混杂. **bug in business logic, 不是 caching/query**.

### 场景 D: 内部 platform 多租户 quota 偶发误算

**问题**: TikTok Shop / Lark / PayLater 共用 platform, quota 计算偶发错. Fix 1: lock fix → 仍. Fix 2: idempotency fix → 仍. Fix 3: retry fix → 仍.

**真 RCA**: distributed 计数器在跨 region failover 期间有 short window 双计数. **需要 redesign counter, 不是 patch**.

---

## 6. 工程上 / 应对上要做什么 (Playbook)

按 **会议中 / 24h / 1 周 / 1 月 / 3-6 月** 5 阶段:

### 阶段 1 · 会议中 (面对客户失信表达)

1. **不 defend, 不 list mitigations 第一句**
2. **「You're right to be frustrated」** — validate emotion
3. **Process-level admission**: "Our diagnostic approach was wrong, not just our code"
4. **3-4 个 specific commitments**:
   - Bring in fresh eyes (principal engineer)
   - **1 week of just RCA, no patches** (counterintuitive but key)
   - Feature flag / kill switch for blast radius
   - Pair-debug with customer's team
5. **Ask back**: "Would you give us 30 days under this plan before deciding cancel?"

### 阶段 2 · 24 小时内

6. **Stop-the-line**: 内部官方 halt feature work on this client
7. **Feature flag deployed**: 客户 prod 一行命令 kill switch
8. **Principal engineer briefed + start**: 不是 part-time, full 1 week
9. **Customer-facing daily sync set up**: 10 min, same time daily, written agenda
10. **Internal escalation**: brief director + AE manager, get backing on 30-day plan
11. **Service credit proposal** drafted (3 months free? scope reduction?)

### 阶段 3 · 1 周 (RCA week)

12. **No code changes** in this week (除非 critical safety)
13. **Daily customer update**: 「Today we tested hypothesis X, ruled out, next hypothesis Y」
14. **Hypothesis tracking**: 公开 board, all ruled-in / ruled-out hypotheses visible
15. **Pair session with customer eng**: 至少 2 次 in week, 让他们 see how we think
16. **RCA writeup**: end of week, share with customer 不 sanitized

### 阶段 4 · Week 2-4 (targeted fix)

17. **Multi-layer review** for new fix: PE review + EM review + customer eng review
18. **Staged rollout**: 1% traffic → 10% → 100%, monitor each
19. **Continued daily sync** through stabilization
20. **30-day stability tracker**: shared dashboard with metrics

### 阶段 5 · Month 1-6 (trust repair)

21. **30/60/90 day checkpoints** with formal metrics
22. **Weekly health reports** unsolicited
23. **Quarterly business review** (QBR), present sustained stability
24. **Don't promise faster trust rebuild** — 6 months is realistic
25. **Document organizational lessons**: stop-the-line policy / fresh eyes mandate

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **"This time we got it"** | 信用 burning. Replace: "This time we're approaching differently — here's how" |
| 2 | **Argue or defend** when customer frustrated | Reduce stress 第一. "You're right to be frustrated" |
| 3 | **No process-level admission** | 客户看出你 still treating as 1 bug. Stop-the-line 信号缺失 |
| 4 | **No blast radius reduction** | Fix 是 sole strategy → 客户继续 bleed |
| 5 | **Spin progress** ("we've made great strides") | 长期灾难, 客户 sees through |
| 6 | **Promise rapid trust rebuild** | 30-day trust = lie. 失信 |
| 7 | **Hide deeper architectural issue** if discovered | 第 4 次 fix 时 explodes, 永久 lost |
| 8 | **Same engineer keeps fixing** | Stuck in same hypothesis, repeat pattern |
| 9 | **No customer-facing visibility into fix process** | 客户感觉 "what are they doing", anxiety amplifies |
| 10 | **Internal misalignment** in front of customer | Confidence erosion in real time |
| 11 | **Skip service credit / compensation discussion** | 财务面 customer 没出口, churn 不可逆 |
| 12 | **Ship fix Friday afternoon** | Weekend monitoring 缺失, 灾难复发概率高 |

---

## 一句话总结 (Part 1)

> **3 次失败的 fix 不是 "需要第 4 次更努力", 是 "诊断方法本身有问题"**.
>
> 你的 craft 不是修这个 bug, 而是**敢于做反直觉的决定: stop-the-line, 花 1 周 just RCA 不写代码, bring in fresh eyes, 同时立即缩小 blast radius**. 然后**承诺 30/60/90 day stability**, 不是 next-sprint 又一次 "this will work".
>
> 客户失信不是 1 次 fix 能修的, 是数月 consistent professionalism 能修的.

---

# Part 2 · 5 个深度问题 (Client Sim 硬核细节)

## ⚙️ Problem 1: Pattern Recognition — 3 次 fix 没解决意味着什么

**这是这道题最 underrated 的部分: 知道何时承认 pattern, 而不是再 push 一次 fix**.

### 1.1 失败次数 vs hypothesis 信号

| 失败次数 | 信号 | 应对 |
|---|---|---|
| **1 次** | 单点 bug, 修 + 监控 | Standard fix flow |
| **2 次** | **可能 root cause 没找到**, 但还能 explain | Deeper RCA before fix 3 |
| **3 次** | **诊断方法 / hypothesis 本身错了** | **Stop-the-line, restart from scratch** |
| **4 次** | 你的客户已经在写 cancellation letter | Crisis mode, leadership escalate |

**Why 3 是 magic number**: 统计上, 如果 root cause 找到了, fix 应该 90%+ 概率成功. 连续 3 次 fail = 你的 hypothesis distribution **整体偏移**, 不是某一个 hypothesis 不对.

### 1.2 5-Why 重新走一遍 (案例: Indonesian voice agent 5% 误识别)

错误分析:

- **第一次诊断**: "Prompt 不够明确" → Fix: 加 prompt rule → 仍 4.8%
- **第二次诊断**: "模型不够 capable" → Fix: tune model → 仍 4.5%
- **第三次诊断**: "Post-processing 没 catch" → Fix: 加 classifier → 仍 4.6%

3 次都假设 **「模型 / prompt / 算法不够好」**. **共同 blind spot: 没 question 数据 distribution**.

第四次重新走 5-Why:

```
Why 5% error rate?
  → 5% calls are misclassified

Why these 5%?
  → Distributed how? *(画 distribution)*
  → 找出: 70% of errors 来自 Indonesian + Javanese 双语客户

Why this subgroup?
  → Training data 中此类客户 underrepresented (3% vs 实际 12%)

Why training data not representative?
  → 训练数据来自 Java 岛 call center, 一线客户实际更多 outer islands

Why this mismatch?
  → 数据收集 process 没 explicit 设计 demographic balance

Why no process?
  → ML team didn't have rep coverage check in eval gate
```

**Root cause**: Process gap in eval methodology. **Fix**: add demographic coverage check + collect rep data + retrain.

**第 4 个 fix 一次解决**, 因为终于 attacking root cause.

### 1.3 公开承认 pattern 的语言

第 3 次 fix 失败后, 你跟客户的开场:

> "I want to be direct with you about what I think is happening. **3 fixes haven't worked**. That's not 3 separate bugs — that's **a signal that we've been wrong about what the root cause is**.
>
> So instead of attempting fix #4 with the same diagnostic approach, **I'm going to do something different**:
>
> **1.** Stop all patching work this week
> **2.** Bring in [Principal Engineer Marco] who hasn't been touching this code
> **3.** Spend 1 week on **just root cause analysis, no fixes**
> **4.** Pair-debug with your tech lead so you see our thinking
> **5.** Deploy a feature flag immediately so we can disable the problem code path while we investigate
>
> Yes — this means **no fix this week**. **I know that's hard to hear**. But I'd rather take a week to find the right answer than continue to ship fixes that don't fix.
>
> Is that something you can accept?"

→ 这段话牛在: **explicitly 承认 hypothesis 错了**, 不是 "this time the fix is different". 客户尊重诚实.

### 1.4 Pattern recognition 的 5 个 trigger 你应该 internal 监控

每个 fix 走完, 检查这 5 个 indicators. 任何一个 trigger = stop-the-line.

| Trigger | Mean | Action |
|---|---|---|
| **Error rate 没下降** | Fix 没修 root cause | Stop |
| **Error rate 短暂下降然后回升** | Workaround 不 fundamental | Stop |
| **Error rate 下降但 customer satisfaction 没回来** | 你修了 symptom, 不 fundamental | Stop |
| **Fix 让 metric A 好, metric B 退化** | 你在 push 气球, 没 deflate | Stop |
| **新 fix 的 RCA hypothesis 跟上次 80% 相似** | 你 stuck in same thinking | Stop |

### 1.5 当客户也 push "just fix it again" 的应对

客户: "I don't care about your RCA week — just ship the fix. We need it working."

你的回应:

> "I hear you. But shipping fix #4 with the same hypothesis as fix #1-3 has a **very high probability of failing again** — based on the pattern of last 3 attempts.
>
> **What I'm proposing isn't slower, it's faster to actually working**:
>
> - Path A (your ask): Ship fix #4 this week. Based on pattern, 70%+ chance it fails. Then we're 4 weeks in with no fix.
> - Path B (my proposal): 1 week RCA, then 1 week targeted fix. 90%+ chance the fix works. **Total: 2 weeks to actually working**.
>
> **In actual time-to-stable, my path is faster.** Plus we deploy a feature flag immediately to disable the problem path during investigation, so you're not bleeding while we work.
>
> Can I get 1 week to do this right?"

→ Math + concrete time + immediate mitigation = customer harder to refuse.

---

## ⚙️ Problem 2: Stop-the-Line — 何时 Halt + 做正经 RCA

**这是 staff-level decision: 主动按下暂停键**.

### 2.1 Stop-the-line 的定义

借鉴 Toyota: **任何 engineer 发现严重 quality issue, 都有权 halt assembly line**, 即便会影响生产 metrics. **质量 > 速度** 是文化, 不是 slogan.

软件 deployment 应用:

- **Halt 标准**: 同一类 bug 3 次未解决 / 客户失去信任表达 / 修复带来新 bug
- **Halt action**: 停 feature work, 停 patch, 专心 RCA
- **Halt 期限**: 1-2 weeks 不超, 超了就是 architectural problem (不同 playbook)
- **Halt approval**: 应该 FDE 直接 call (don't ask permission), 不需要 EM sign-off

### 2.2 为什么 stop-the-line 反直觉但正确

| 工程师本能 | 实际 effective |
|---|---|
| 客户 push → ship more fixes | Stop-the-line → 1 week 找真因 |
| 不能让 team idle → 给个 task | Halt is the task — 让 team focus RCA |
| 每天 ship 让客户看到 progress | Each failed fix erodes trust faster than no progress |
| 修代码就有 sense of progress | 不修但 systematic ruling out hypothesis 是 real progress |

### 2.3 Stop-the-line 决策矩阵

| Scenario | Stop? | Reason |
|---|---|---|
| 1 次 fix 没解决, 客户耐心 | NO | Standard iterate |
| 2 次 fix 没解决, 客户有点烦 | MAYBE | Deeper RCA before fix 3 |
| 3 次 fix 没解决 | **YES** | Pattern signal |
| Fix 解决主问题但引入新 bug | YES (different fix) | 别 cascade |
| 客户 explicitly 失信 | YES regardless of fix count | Trust signal trumps tech signal |
| 监管 / 合规事件 | YES immediately | Regulatory > all |

### 2.4 跟客户公告 stop-the-line 的语言

**邮件 / 正式声明** template:

```
Subject: [Acme] Approach Change — Pause and Reset

Hi Bambang, Maria, Andi,

After internal review, I'm making a process decision I want to
share with you directly.

WHAT'S CHANGING
───────────────
We have shipped 3 fixes for the misclassification issue. Error rate
hasn't materially improved (4.6% vs 5% start). This pattern tells
me our diagnostic approach has been wrong — not just the code.

So: I'm halting fix attempts this week.

WHAT THIS MEANS THIS WEEK
─────────────────────────
- No new fix attempts (this is deliberate, not "we don't know")
- 1 week of structured root cause analysis with fresh engineer
  (Principal Engineer Marco joining)
- Pair-debug sessions with Andi (2 sessions this week)
- Feature flag deployed today: you can disable the problematic
  code path with a single command if error rate spikes

WHY THIS WILL BE FASTER OVERALL
───────────────────────────────
Continuing to patch without finding root cause has a high
probability of failing again. We've validated that pattern 3 times.
Spending 1 week to find the real root cause + 1 week to fix it is
likely faster than 4 more weeks of patches that don't work.

WHAT YOU'LL SEE FROM US
───────────────────────
- Daily 10-min sync at 9am AEST, structured agenda
- Daily hypothesis tracking board (shared link in this email)
- End-of-week RCA writeup, unsanitized
- Then 1 week targeted fix + staged rollout

WHAT I'M ASKING FROM YOU
────────────────────────
30 days under this plan before any contract decision. If we miss
any commitment milestone, the cancellation conversation is yours
without penalty discussions.

Marco and I are both available for any conversation.

[Your name]
[Phone]
```

### 2.5 RCA Week 的 daily structure

**Day 1**: Hypothesis explosion
- All engineers + PE + customer eng brainstorm 20+ hypothesis
- Categorize: data / model / infra / process / external
- Triage: prioritize top 5 by likelihood

**Day 2**: Top hypothesis investigation
- Each hypothesis assigned engineer + data analysis plan
- End-of-day: which still alive, which ruled out

**Day 3**: Deeper data analysis
- Pull production data, slice by demographic / time / use case
- 找 错误 pattern in raw data

**Day 4**: Hypothesis convergence
- Top 1-2 hypothesis tested with concrete experiment
- 95%+ confidence on root cause

**Day 5**: RCA writeup + customer review
- Send writeup to customer
- 30-min review call
- Approve fix plan for next week

**Daily 10-min customer sync** at fixed time. Agenda template:

```
Daily Sync — Day [N] of RCA Week
─────────────────────────────────
1. Hypothesis investigated yesterday:
   - [X]: result, action
2. Top hypothesis today:
   - [Y]: plan
3. Open risks / blockers:
   - [Z]
4. Anything we need from your team:
   - [list]
5. Q&A
```

### 2.6 RCA writeup 模板 (week-end deliverable)

```
ROOT CAUSE ANALYSIS — Misclassification Issue
─────────────────────────────────────────────
Author: Marco (PE) + Gao Xin (FDE)
Date: 2026-05-28
Status: COMPLETE
Distribution: Acme (Bambang, Maria, Andi) + Internal (EM, Director)

EXECUTIVE SUMMARY
─────────────────
We found root cause. It is NOT what our 3 previous fixes assumed.

Root cause: Training data underrepresents bilingual
Indonesian/Javanese speakers (3% of data, 12% of production
traffic). Model confidence in this subgroup is structurally low,
leading to misclassification.

3 previous fixes (prompt rules, model tune, post-processor) all
addressed the symptom (misclassification) but not the cause (data
distribution mismatch).

5-WHY ANALYSIS
──────────────
Why 5% error rate?
  → 5% calls misclassified

Why these 5%?
  → 70% of errors come from a specific subgroup: Indonesian +
    Javanese bilingual speakers (verified via demographic
    breakdown of error logs)

Why this subgroup?
  → Model confidence on bilingual sub-language switching is
    structurally low (verified via confidence score analysis)

Why low confidence?
  → Training data underrepresents this subgroup: 3% of training
    data, but 12% of production traffic (verified via data
    pipeline audit)

Why this representation mismatch?
  → Training data sourced from Java-region call center; production
    traffic comes from all regions including outer islands

Why no demographic check in eval?
  → ML team's eval methodology validates overall accuracy but not
    per-subgroup. Process gap, not code gap.

PROPOSED FIX (NEXT WEEK)
────────────────────────
1. Collect 5K additional bilingual examples (data team, 3 days)
2. Retrain model with rebalanced data (1 day)
3. Add per-subgroup accuracy check to eval gate (1 day)
4. Staged rollout 1% → 10% → 100% over 5 days
5. Monitor: error rate target <2% within 14 days

Total: 2 weeks to deploy + 2 weeks to stabilize.

QUALITY GATES
─────────────
- 80% accuracy on bilingual subgroup before promoting from 1% to 10%
- 90% accuracy before 100%
- If gates fail: stop-the-line again, escalate to architectural
  redesign discussion

WHAT WAS WRONG ABOUT PREVIOUS 3 FIXES
──────────────────────────────────────
Fix 1 (prompt rules): Treated as language understanding issue.
  Symptom not cause. No effect on training data coverage.

Fix 2 (model tuning): Tuned same underlying weights. Did not
  address underrepresentation.

Fix 3 (post-processor): Added classifier downstream. Did not
  address upstream coverage gap.

All 3 attacked "model is wrong" hypothesis. Correct hypothesis
is "data is unrepresentative".

LESSONS FOR OUR PROCESS
───────────────────────
- Per-subgroup eval should be standard before any model release
- Production traffic demographic should be reviewed quarterly
  vs training data
- 3-failed-fix trigger should automatically invoke RCA week

CONTACT
───────
[Your name + Marco's name]
Available for any questions before fix rollout.
```

---

## ⚙️ Problem 3: Communication During Repeated Failure — Transparency vs Damage Control

**这是讲什么 / 不讲什么 / 何时讲的细致 craft**.

### 3.1 错误的 default: 越失败越 hide

工程师本能: 失败时 minimize info sharing 以「避免引起恐慌」. 客户感受: vendor 在 hide, 信任更崩.

**正确 default**: **失败时 over-share, 成功时 understate**. Transparency 是 trust 的唯一货币.

### 3.2 Transparency 的 4 个 level

| Level | 内容 | 用法 |
|---|---|---|
| **L1 公开 fix attempt** | "We deployed a fix" | Standard, 每次都该 |
| **L2 公开 hypothesis** | "We think it's caused by X" | RCA 期间 daily |
| **L3 公开 thinking** | "We tested X, ruled out, now trying Y" | Pair-debug 风格 |
| **L4 公开 mistakes** | "Our diagnostic approach was wrong" | 转折点 admission, 1 次足够 |

**3 次 fix 失败后, 你应该全部 4 layer**. 之前可能只 L1.

### 3.3 Over-communicate 的语言模板

**Daily update 邮件** (RCA week, 5 天连发):

```
Subject: [Acme] RCA Day [N] — [概要]

Yesterday:
- Investigated hypothesis: [X]
- Method: [data analysis / test / experiment]
- Result: [ruled in / ruled out, why]
- Time spent: [N hours]

Today:
- Investigating hypothesis: [Y]
- Why this hypothesis: [reasoning]
- Method: [plan]
- Expected end-of-day result: [what we'll know]

Open hypotheses still alive:
- [list]

Hypotheses ruled out so far:
- [list with reasoning]

Risks / blockers:
- [list]

Anything we need from Acme:
- [list]
```

→ 客户看到 **process**, 不只 result. **Visibility into thinking = trust signal**.

### 3.4 不该 over-share 的事 (transparency 的边界)

| 不该 share | 原因 |
|---|---|
| 内部 disagreement (PE vs EM) 的 raw form | 让客户看到 internal political 没价值, 反 erode |
| 其他客户的 incident details | Confidentiality 违反 |
| 内部 finger-pointing | 「这是 X 的锅」公开说 = unprofessional |
| Speculation without evidence | "可能也许或许是 X" — 客户拿 hypothesis 当 commitment |
| Timeline 之前的进度 | "We've been working on this for 3 weeks" 听起来 inefficient |
| 团队 morale 问题 | "We're tired" — 客户立刻 worry about your team's competence |

### 3.5 客户 hostile / 失控时的 communication 策略

**Scene**: 客户 CTO (Bambang) 在视频会议中突然冷静地说: "I want to talk to your CEO. This is unacceptable."

**错误回应**:
- "Let me schedule that" (sounds like you're escalating yourself out of the room)
- "Why?" (defensive)
- "What did we do wrong?" (false humility)

**推荐回应**:

> "I understand. Your situation warrants leadership attention. **Two parallel things**:
>
> **(1)** I'll set up a call with our CRO this week — I'll have it on your calendar by EOD today. Their email + LinkedIn so you can prep questions.
>
> **(2)** **In parallel, I'm not stepping out of this.** I remain your primary contact. The CRO conversation is for strategic alignment + commitment level, but the day-to-day execution stays with me. **You shouldn't have to renegotiate the basics with a new contact every time things get hard.**
>
> What I'd ask: **let me brief our CRO so the conversation starts at the right level**. I'll send you my brief by EOD too, so you can correct any framing I get wrong.
>
> Is that OK?"

→ 这段语言**accept escalation 但 reaffirm continuity** + **proactively offer to brief leadership transparently**.

### 3.6 Internal team 沟通 (你的团队不要 panic)

跟客户 transparency 不能直接 mirror 给团队. 团队需要的不是 panic, 是 calm direction.

**Internal weekly all-hands** (你 host):

```
1. Customer status: [calm summary, no drama]
2. RCA progress: [where we are]
3. What I'm asking from each role:
   - Eng: focus on hypothesis X this week
   - PE: lead hypothesis ranking
   - SRE: deploy feature flag, monitor
   - Data: pull demographics analysis
4. What I'm shielding the team from:
   - Customer escalation noise (I handle)
   - Sales pressure (I handle)
5. Open questions / concerns from team
```

→ 团队需要 see **calm leadership**, 不是 fear-driven manager.

### 3.7 Damage control vs transparency 的真正区别

| Damage control (避免) | Transparency (推荐) |
|---|---|
| "We're making good progress" | "Day 3 of RCA. Top hypothesis ruled out. Investigating Y today" |
| "Don't worry, we got this" | "Here's what we got wrong about our diagnosis and what we're changing" |
| "Engineering is working on it" | "Marco (PE) is leading. Here's his thinking. He'll join Wednesday's call" |
| "We'll have it fixed soon" | "RCA complete by Friday. Fix deployed in stages over 2 weeks" |
| "This is a rare issue" | "This is 5% of calls — concentrated in bilingual subgroup. Here's the data" |

**Damage control 的 short-term comfort 换长期信任崩**. **Transparency 的 short-term discomfort 换长期信任增**.

---

## ⚙️ Problem 4: Bringing in Fresh Eyes — Rotate Engineer, Peer Review, Expert Escalation

**这是 stop-the-line 的实施工具**.

### 4.1 为什么 fresh eyes 是必要

**Cognitive lock-in**: 同一个 engineer 看同一个 bug 多次, **大脑形成 hypothesis 路径**, 之后所有 evidence 都 confirm 已有 hypothesis. 这是 confirmation bias 的工程版.

**Solution**: 切换观察者. **Fresh engineer 不带 prior**, 能 see what's missing.

### 4.2 Fresh eyes 的 3 个 level

| Level | 谁 | 何时 | 效果 |
|---|---|---|---|
| **L1 Peer rotation** | 同 team 不同 engineer | 1 次 fix fail | 30% 概率 break stuck |
| **L2 Principal engineer** | Cross-team senior, 没碰过 code | 2-3 次 fix fail | 60% 概率 break stuck |
| **L3 External expert** | 公司外 / 公司高 staff | 架构 redesign 需求 | 80%+ 概率 break stuck |

### 4.3 如何 onboard 一个 fresh engineer (不 leak 你的 hypothesis)

**反直觉**: 不要先讲你的 hypothesis. Let 他形成自己的.

**Day 1 brief (你给 PE Marco)**:

> "Marco, here's what I want from you this week.
>
> **Don't read my docs first.** I'll share when you ask. I want you to form your own hypothesis from raw data, not anchor on mine.
>
> **What I'll give you**:
> - Access to production logs
> - Production data sample
> - The 3 fixes we shipped + each fix's metric impact
> - Customer's environment access
>
> **What I won't tell you yet**:
> - My current hypothesis on root cause
> - Where I think the bug is
> - What I think the fix should be
>
> **Your job for first 2 days**: form independent hypothesis. Then compare with mine. **If we converge, we likely both wrong** (since I've been wrong 3 times). If we diverge, your hypothesis is the lead.
>
> Day 3: align + plan. Day 4-5: deep test + RCA writeup."

→ 这是**反 confirmation bias 的设计**. 反直觉但 critical.

### 4.4 Pair-debug with customer's team

**为什么**: customer 的 engineer 知道他们环境的 nuances 你不知道. 还有, **客户 watch your team think = trust 建立 fastest path**.

**Setup**:

- 2-hour session, screen share
- 客户 eng + 你 + PE
- 共同看 production logs / metrics
- **Out loud reasoning**: 你 narrate 你的思考 ("I'm looking at X because Y")
- 客户 eng 可以 challenge / suggest
- End: write down joint hypothesis + next experiment

**关键**: 客户 eng 不是 watcher, 是 collaborator. 给他 keyboard time.

**Sample dialog mid-session**:

> 你: "I'm filtering errors by hour of day. Looking for time-correlation..."
>
> 客户 eng (Andi): "Wait. Most of our outer-island customers call during evening — local time. UTC log might mask this."
>
> 你: "Good catch. Let me re-filter by local time. **This is exactly the kind of context I wouldn't have on my own**."
>
> *(运行 query)*
>
> "OK — evening hours show 8% error rate, daytime 3%. **That's a 5x spike**. And it correlates with outer island traffic. Andi, what's different about evening?"
>
> Andi: "Outer islands often have weaker network — Java DSL vs JKT 4G. Could be transmission quality?"
>
> 你: "Let's test that hypothesis Thursday. Marco, can you pull audio quality metrics by region?"

→ 客户 eng 反而 **identify 关键 insight**. 你的 job 是 facilitate.

### 4.5 Principal Engineer engagement 的 scoping

**Risk**: PE 进来 1 周, 然后 vanish, team 又 stuck.

**Solution**: bounded scope + structured handoff.

| Phase | PE 的 role |
|---|---|
| Week 1 (RCA week) | Lead investigation, write RCA |
| Week 2 (fix design) | Lead fix design, review code |
| Week 3-4 (staged rollout) | Available for consult, 不 daily |
| Month 2+ | Quarterly check-in only |

**Handoff doc** (PE write):

```
PE Handoff: Acme Misclassification Issue
─────────────────────────────────────────
RCA: [link]
Fix design: [link]
Quality gates: [link]
Open risks: [list]
What I'd watch for first 30 days post-rollout:
  - [specific metrics]
  - [specific behaviors]
Contact for questions: [PE name + 24h response SLA]
```

### 4.6 External expert escalation (rare but powerful)

**何时**: 架构层 redesign 需求 + 你公司没 in-house 那个深度.

**例**:
- 分布式 counter 设计 → bring in DSL author or systems consultant
- ML eval methodology 设计 → bring in ML Ph.D. researcher
- 合规审计 → bring in big-4 audit advisory

**客户 perception**: "Vendor 真在 invest 我们这个 problem" — 强 signal.

**Cost**: $20-50K for 1 week, **比 churn 一单 cheap**.

### 4.7 内部 politics: PE 不愿来 / EM 不放人

**典型 push back**:

| EM 说 | 你的 reply |
|---|---|
| "PE is busy on Project X" | "What's the priority — losing this $2M deal vs project X?" |
| "Can't spare 1 week" | "Spare 1 day. If PE confirms my hypothesis, we save 4 weeks of patches" |
| "Why don't you figure it out" | "Because I've been wrong 3 times. Statistical signal that fresh eyes is the right move" |
| "We don't usually do this" | "Right — and we don't usually have customers about to cancel. Process exception warranted" |

如果 EM 仍 block, escalate to director: "I need PE for 1 week. EM has blocked it. This is a $2M deal at risk. Can you intervene?"

---

## ⚙️ Problem 5: Trust Rebuilding Playbook — Over-Communicate, Scorecards, Weekly Review

**这是最长期 + 最 underrated 的部分. 救场不是 1 次 fix, 是 6 个月 craft**.

### 5.1 Trust loss vs trust rebuild 的 asymmetry

| | Trust 速度 |
|---|---|
| **Trust lose** | 1 个 incident, 几小时崩 |
| **Trust rebuild** | 几个月 consistent, 几周看到 trend |

数字: **Trust rebuild ≈ 5-10x time of trust loss**. 3 次 fix 失败 = 3-4 个月信任修复.

### 5.2 30 / 60 / 90 day milestones

**Day 1-30: Stabilization + visibility**

| Item | Cadence | 目的 |
|---|---|---|
| Daily 10-min sync | Daily | Visibility |
| Error rate dashboard | Real-time | Show trend |
| Service credit applied | Day 1 | Tangible good-faith |
| Weekly status email | Friday EOD | Written record |
| 30-day stability checkpoint | Day 30 | Formal review |

**Day 31-60: Process maturity**

| Item | Cadence | 目的 |
|---|---|---|
| Daily sync → 3x/week | Reduced | Trust signal (less hand-holding needed) |
| Quarterly business review prep | Day 60 | Forward-looking |
| Sub-incident postmortems | Per-incident | Process embedded |
| Roadmap discussion | Day 60 | Customer thinks ahead, not back |

**Day 61-90: Normalization**

| Item | Cadence | 目的 |
|---|---|---|
| Sync → weekly | Standard cadence | Normalcy |
| QBR happens | Day 90 | Demonstrate sustained delivery |
| Customer references our handling | Day 90+ | Real signal of recovery |

### 5.3 Scorecards (formal metrics 客户 trust 的可见证据)

| Metric | Pre-incident | Target post | Frequency |
|---|---|---|---|
| Error rate (the bug) | 5% | <2% | Real-time |
| MTTR (mean time to restore) | 4h | <1h | Per incident |
| Sev-1 frequency | 1/week | 0/month | Monthly |
| Roadmap delivery on time | 60% | 95% | Per release |
| Daily sync attended | N/A | 100% by us | Per day |
| RCA published timely | N/A | <24h | Per incident |
| Customer NPS | -20 (post-incident) | >0 at 90day | Quarterly |

**Shared dashboard** 客户 view. **No private metrics during recovery period**.

### 5.4 Weekly review 模板

**每周五 30 min, 客户 + 你 + EM**:

```
Weekly Review — Week [N] of Stabilization Period
────────────────────────────────────────────────
Date: [date]
Attendees: Acme (Bambang, Maria, Andi) + Us (Gao Xin, Linda)

1. METRICS THIS WEEK
   - Error rate: [number] vs target [number]
   - Incidents: [list]
   - MTTR: [number]
   - All metrics graphed: [link]

2. INCIDENTS REVIEWED
   - [Incident 1]: cause, mitigation, RCA status
   - [Incident 2]: ...

3. PROCESS CHANGES SHIPPED
   - [change 1]: deployed, monitored
   - [change 2]: ...

4. NEXT WEEK COMMITMENTS
   - [commitment 1]: date, owner
   - [commitment 2]: ...

5. RISKS / CONCERNS
   - From customer: [list]
   - From us: [list]

6. ACTION ITEMS
   - [list with owner + date]

7. OPEN Q&A
```

### 5.5 Service credit / compensation 的运用

**何时**:
- 3 次 fix 失败 = good time to offer
- 客户 SLA 已 breach = mandatory
- 客户 mention exit clause = preemptive

**Forms**:

| 形式 | Pros | Cons |
|---|---|---|
| **3 months free service** | Tangible $, easy understand | 可能 customer 觉得 cheap |
| **Free additional feature / scope** | 给客户 value 增加 | 你的 team work load 增加 |
| **Pro bono engineering** (你的 PE 帮 customer 做 ad-hoc work) | High signal, customer feels invested in | High cost |
| **Migration / contract amendment** | Strategic, long-term commitment | 法务介入 |

**经验**: 3-month service credit + 1 pro bono PE work = 通常 enough. 不需 over-offer.

### 5.6 不能承诺的 trust rebuild timeline

| Customer 期待 | 你应该说 |
|---|---|
| "When will trust be back?" | "Realistically 3-6 months of consistent stability. I won't promise faster — that's been the pattern with similar situations" |
| "Can you guarantee no more incidents?" | "No. **I can guarantee the response when they happen**: RCA in 24h, public sync, no spin. **That's what differentiates good vendors from bad ones**" |
| "When can we stop daily sync?" | "When you tell me. **You set the cadence**, I respond. My default is weekly after 60 day stability" |

### 5.7 Trust rebuild signals (你监控的, 客户不会告诉你)

| Signal | 含义 |
|---|---|
| 客户开始**主动** propose Tier 2 / new feature | Rebuilding |
| 客户 introducing 你给 their other teams | 重大 signal |
| 客户 reference 你给 prospective customers | Recovery 完成 |
| Customer NPS turns positive | Quantitative validation |
| 客户**减少** daily sync cadence by themselves | Confidence returning |
| 客户 mention incident **calmly** in QBR ("remember when we had...") | Normalized |

### 5.8 当 trust rebuild fail (客户仍 churn)

最坏 case. 这时:

- **Don't fight contract**. 让 legal 处理.
- **Preserve relationship for future**: ex-customers can become future customers
- **Internal postmortem honest**: 我们哪里没做对, 让 organization 学
- **Recovery 的 effort 不浪费**: Process changes are permanent organizational value

**邮件 to ex-customer (优雅 exit)**:

```
Subject: Wishing Acme well

Bambang, Maria, Andi —

I'm sorry we couldn't deliver to the level you needed.

Three things I want to leave with you:

1. The fix we deployed in Week 8 is stable and will continue to
   operate. We will support it through the end of your contract.

2. If you need to reference our work or technical details for your
   next vendor, I'll provide whatever you need.

3. Should you reconsider in the future — for any reason — I'd
   welcome the chance to demonstrate the lessons we've learned
   from this engagement.

Thank you for the trust you extended, even though we couldn't fully
honor it.

[Your name]
```

→ 即便 churn, **closing graceful** = future opportunity. Industry 小, customers talk.

---

# Part 3 · 把 5 个问题串起来看

这 5 个问题其实是**recurring fix 灾难的 5 个层次**:

1. **Pattern recognition** (Problem 1) — 知道 3 次失败意味着 hypothesis 错了
2. **Stop-the-line** (Problem 2) — 主动 halt, 反直觉但正确
3. **Communication** (Problem 3) — Over-communicate, transparency 是 trust 货币
4. **Fresh eyes** (Problem 4) — Break cognitive lock-in via outsider
5. **Trust rebuild** (Problem 5) — Months of craft, 不是 1 次 fix

每一层做对, **关系反而比 incident 前 stronger** (因为客户看到你 handle crisis 的能力). 每一层错, **客户永远走**.

---

## 必问 clarifying questions

**1. Failure pattern**

> "Same exact bug recurring, or related family? Same code path? Same customer trigger?"

**2. Customer state**

> "Has customer threatened cancellation? Mentioned legal? Or just expressed frustration?"

**3. Internal capacity**

> "Do I have authority to stop-the-line / bring in PE / commit service credit? Or do I need approval?"

**4. Time / contract**

> "Where is the customer in their contract — early, mid, renewal? Affects retention strategy."

**5. Wider impact**

> "Are other customers affected by same issue? If yes, this is a P0 for multiple — different playbook."

---

## 5 步框架 (45-min answer 节奏)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify pattern + customer state + capacity |
| 5-15 min | Process-level admission + 4 commitments dialog |
| 15-25 min | Stop-the-line + RCA week mechanics |
| 25-35 min | Communication: daily structure + 4 layer transparency |
| 35-45 min | Long-term: scorecards / 30-60-90 day / trust rebuild |

---

## 简历专属 reframe

| 题 | Gao Xin 的经验 |
|---|---|
| Recurring fix doesn't work | **ConvFinQA — 8 个 variant 都失败**, 你 honestly reported negative result |
| Process-level admission | ConvFinQA 你写了 "all 8 variants regressed" 不 hide |
| Fresh eyes | Voice agent 跨 7 markets — 每个市场带 fresh perspective |
| Feature flag for blast radius | Voice agent multi-market gradual rollout |
| Pair-debug with customer | Indonesia ops + you 共同 debug refund logic |
| Daily sync + RCA writeup | TikTok PayLater incident response 你做过 |
| Service credit | 内部 platform 团队对接 budget 重新协商 |

**主动 quote**:

> "This exact shape happened in my ConvFinQA work. I tried 9 variants of agent improvements. **The first 3 actually made the eval score worse**. I had a choice: keep patching (assume 'this variant just wasn't the right one'), or admit 'my hypothesis class is wrong, let me try something fundamentally different'.
>
> **I picked admission**. Documented the negative result openly in the ablation report. The team's first reaction was uncomfortable — 'why are you publishing failure?' But the writeup forced us to **regenerate hypothesis from scratch**. Variant 9 was qualitatively different (changed reasoning chain structure, not prompt). It worked.
>
> The lesson I'd apply to a customer in this situation: **3 fixes failing tells you the diagnostic class is wrong, not just one fix**. Customers in this situation prefer **honest reset over the 4th 'this time will work'**. So I'd offer them the equivalent: a fresh-eyes RCA week, no patches, and let them watch us think.
>
> **The hard skill isn't fix 4. The hard skill is 'pause + admit + restart'**, especially when customer pressure is at maximum."

---

## 5 follow-ups

**Q1**: "Client refuses 30-day grace. Wants exit clause activated NOW."

**A**: 别 fight contract. Move to relationship preservation:
- "I respect that decision. Before any contract action, **2-week reset proposal**: no charges during that period, you get full RCA + fix attempt. Day 14 you decide cancel or continue."
- This buys time + good faith. Most CTOs say yes to "free 2 weeks of best effort".
- If they still say no, accept gracefully, follow Section 5.8 (优雅 exit). 不要 desperate.

**Q2**: "Principal engineer finds it's a 6-month architectural issue."

**A**: This is where most FDE fail — they hide. Don't:
- "We've identified root cause. It's a **6-month architectural change** to truly fix. **Three paths**: (1) workaround that buys you 6 months at known limitations, (2) commit to architectural rewrite jointly with cost-sharing, (3) **de-scope the affected feature**."
- Let customer choose. They might pick (3) — **graceful degradation > 6 more months of denial**.

**Q3**: "Customer CFO talks about damages."

**A**: 上 lawyer 之前一定 try:
- Escalate to your CEO + AE manager + your CFO
- Joint call: their CFO + your CFO
- Offer **specific service credit / discount** (e.g., 6 months free) as good-faith
- Don't unilaterally promise damages — but **acknowledge real cost** to their business
- Document everything; legal at standby
- Most "damages" talk is **negotiation leverage**, not actual lawsuit. Respond to underlying business pain.

**Q4**: "Your EM wants you to spin the situation 'we've made great progress'."

**A**: Disagree internally:
- "If we tell them 'great progress' and the next fix fails, **we lose them permanently**. Honest reset is more likely to save the relationship than spin."
- "Spin is short-term comfortable, long-term lethal. I've seen this pattern."
- If EM insists, **escalate to senior leadership** — this is a **career-defining choice**. Spin → you become part of the failure pattern. Honesty → you're the FDE who saved the deal.

**Q5**: "How long does trust take to rebuild?"

**A**: Realistic: **3-6 months of stability** before trust returns. Specifically:
- 30 days zero incidents on previous bug class
- 60 days delivery of committed features on time
- 90 days no surprises — proactive comms on potential issues
- 6 months — relationship moves from "watching us fail" to "trusting by default"

**Don't promise faster recovery**. People rebuild trust slower than they lose it.

---

## ❌ 易错点 (top 12)

1. **"This time we got it"** — credibility-burning
2. **Argue or defend** when customer frustrated
3. **No process-level admission** — treating as bug-specific
4. **No blast radius reduction** (feature flag) — fix is sole strategy
5. **Spin progress** — short-term comfort, long-term disaster
6. **Promise rapid trust rebuild** — 30-day trust = lie
7. **Hide deeper architectural issue** if discovered
8. **Same engineer keeps fixing** — stuck in same hypothesis
9. **No customer visibility into fix process** — customer anxiety amplifies
10. **Internal misalignment in customer-facing** — confidence erosion real-time
11. **Skip service credit / compensation** — no financial out for customer
12. **Ship fix Friday afternoon** — weekend monitoring gap = relapse risk

---

## ✅ 加分项 (top 12)

1. **A·R·R·R framework** explicit (Admit / Reset / Reduce blast radius / Re-earn)
2. **Stop-the-line decision** at fix 3 (proactive, not reactive)
3. **1 week no-fix RCA** (counterintuitive but correct)
4. **Fresh PE without prior hypothesis leak** (anti-confirmation-bias)
5. **Pair-debug with customer's team** — radical transparency
6. **Feature flag for blast radius** — immediate mitigation
7. **30-day grace period offer** before contract action
8. **Daily 10-min sync** first 2-4 weeks
9. **Unsanitized RCA writeup** — honest 5-why
10. **Service credit** as tangible good-faith
11. **30/60/90 day formal milestones** + scorecards
12. **Quote ConvFinQA negative result honesty** (real Gao Xin work)

---

## 一句话总结

> **3 次 fix 失败不是「再 push 1 次」, 是「诊断方法本身错了」**.
>
> 你的 craft 是**敢于反直觉的决定**: stop-the-line + 1 周 just RCA + fresh eyes + 立即缩小 blast radius. 然后**承诺 30/60/90 day stability**, 不是 next-sprint 又一次 "this will work".
>
> 客户失信不是 1 次 fix 能修的, 是数月 consistent professionalism 能修的. **Honest reset > 4th promise**.

---

## Cheat Sheet (印 1 页)

```
A·R·R·R framework:
  Admit process-level fault (not just bug)
  Reset approach (fresh eyes, RCA week, pair-debug)
  Reduce blast radius (feature flag, kill switch)
  Re-earn over time (30/60/90 day stability)

3-fix-fail signal:
  Pattern: hypothesis class wrong, not individual fix
  Action: stop-the-line, not fix #4
  Math: 1 wk RCA + 1 wk fix > 4 wk patches that fail

Stop-the-line trigger:
  3 fixes same class fail OR
  Customer explicit trust loss OR
  Fix introduces new bug OR
  Regulatory event

Day-of script:
  "You're right to be frustrated"
  "Our diagnostic was wrong, not just our code"
  "I'm bringing in fresh eyes"
  "1 week of just RCA, no patches"
  "30-day grace before contract decision"

RCA week structure:
  Day 1: hypothesis explosion (20+)
  Day 2: triage to top 5
  Day 3: deep investigation
  Day 4: convergence to top 1-2
  Day 5: writeup + customer review

Daily sync:
  10 min, 9am, structured agenda
  Yesterday hypothesis + result
  Today hypothesis + plan
  Ruled-out list growing
  Open risks
  Asks of customer

Fresh eyes onboarding:
  Don't share your hypothesis first
  Let them form independent view
  Compare on day 3
  If converge: both possibly wrong (since you've been wrong 3x)
  If diverge: their view leads

Pair-debug with customer eng:
  Screen share 2h
  Out-loud reasoning
  Customer eng has keyboard time
  Joint hypothesis + next experiment

Transparency 4 layers:
  L1: We deployed fix (standard)
  L2: We think it's X (RCA daily)
  L3: We tested X, ruled out, trying Y (pair-debug style)
  L4: Our diagnostic was wrong (turning point admission, 1x)

Service credit defaults:
  3-month free service
  + 1 PE pro bono week
  + RCA published
  + 30-day grace before exit

30/60/90 day milestones:
  Day 1-30: stabilization, daily sync, dashboard, credit applied
  Day 31-60: process maturity, 3x/week sync, QBR prep
  Day 61-90: normalization, weekly sync, QBR, NPS check

Trust rebuild signals (you monitor):
  Customer proposes Tier 2 → rebuilding
  Customer introduces you to other teams → strong
  Customer references you → recovered
  NPS positive at 90 days → quantitative
  Daily sync reduced by customer → confidence

Architectural issue discovered:
  3 paths offered: workaround / rewrite / de-scope
  Customer chooses, you don't push

CFO mentions damages:
  Escalate to your CEO + CFO
  Service credit (6 months) before legal
  Acknowledge cost without promising damages
  Most "damages" = negotiation leverage

Trust rebuild timeline:
  3-6 months realistic
  Don't promise faster
  Lose trust in hours, rebuild in months

红线:
  - "This time we got it" (credibility-burning)
  - Defend / argue
  - Spin progress
  - Hide architectural issue
  - Same engineer keeps fixing
  - Friday afternoon fixes
  - Promise rapid trust rebuild
  - No blast radius reduction
```
