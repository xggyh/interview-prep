# 🎯 T4 · FDE Scenario Delivery 全景 — 冲刺版

> 完整版: [gfde-t4-overview.html](gfde-t4-overview.html). 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: customer 给 vague request (e.g., '用 AI 帮忙'), 我有 3 周 MVP timeline, 客户限 GCP + Vertex AI, 多 stakeholder (sponsor + IT + legal + end user), 单 tenant pilot 然后 multi-tenant scale."

**核心心智模型**: FDE ≠ SWE. Input 是混乱客户需求不是 PRD, success 是客户 KPI 不是 LOC, timeline 是 3-week MVP → 12-week pilot, skills = 30% code + 30% customer + 20% scoping + 20% selling.

**3 种 ambiguity 必须 navigate**: 需求 (问 5+ clarifying Q) / 技术栈 (在客户约束内 design) / 政治 (sponsor + IT + legal 三角).

### Layer 1: D·K·D·M·P framework (Customer Scoping)

```
D - Discovery     (wk 0):   5-7 stakeholder interviews + system landscape
K - KPI Lock      (wk 0-1): ONE measurable + baseline + target + attribution
D - Decomposition (wk 1):   workflow 10 sub-step, score 耗时×痛×LLM-fit×data×风险
M - MVP Demo      (wk 1-3): smallest vertical slice E2E (hardcoded OK)
P - Pilot Rollout (wk 4-12): 10 → 50 → 200 user gradual
```

### Layer 2: 3-Question Workflow Abstraction (per step)

Q1 Deterministic? Q2 Reversible? Q3 Latency? → 5 outcome: agent auto / agent+confirm / agent draft + human review / human+assist / human only. 90% real workflow = hybrid, 不是全自动也不是全人.

### Layer 3: 4 Human-Agent Patterns (coexist, 不是选一个)

```
A. Confidence threshold escalation  (< 0.7 → human)
B. Confirm-required destructive     (send / charge / delete = UI checkpoint)
C. Scheduled human review           (5% sample weekly batch)
D. User-initiated takeover          (/handoff any time, no friction)
```

### Layer 4: 4-Layer Permissions / Safety / Recovery

```
L1 IAM           OBO delegation, agent ≤ user, per-action scope, multi-tenant DEK
L2 Injection     trust marking + system reminder + pattern + confirm UI
L3 Audit         immutable hash-chained, 90d hot + 7y cold (compliance)
L4 Recovery      outbox + compensating handler + bulk rollback
```

### Edge cases (5 个最高频)

- **EC1 客户改主意 (week 3)**: 区分真 pivot vs shiny toy. 真 pivot → 延 demo 1 周 + 重新 KPI lock. Shiny toy → push back, 留 Phase 2 roadmap.
- **EC2 客户要 1 周交付**: multi-choice — Option A (1-week PoC) / Option B (3-week MVP) / Option C (both). 让客户自己选 trade-off.
- **EC3 客户要 100% 自动**: 不接受. 用 trust ladder (Phase 1 suggest → 2 auto deterministic → 3 escalate outlier → 4 autonomous routine).
- **EC4 IT week 3 才说 API 不开放**: 强制 day 1 IT interview, constraint 当 input 不是 obstacle.
- **EC5 Demo 后客户 underwhelmed**: 直接问 "What did you expect that you didn't see?". 通常 = KPI not visible. Recovery: 当周 ship revised demo with concrete delta number.

### Production hardening

- **Stakeholder map** (谁是 sponsor / blocker / champion) day 1
- **Anti-goals doc** (写下 not building 哪些, 跟 goals 一样重要)
- **Weekly metric review** with sponsor (live dashboard, 不是黑盒)
- **Phase tracker** customer-visible (Phase 1 / 2 / 3 / 4 进度 + 当前指标)
- **Roadmap doc** (每个客户加的 request 进 phase queue, 不当场拒)

### 🪝 Resume hook

"TikTok PayLater voice agent 7 markets — 每市场跑同套 D·K·D·M·P scoping (Indonesia / Vietnam / Thailand / Philippines / Malaysia / Brazil / Mexico). 每市场 KPI 是 collection effectiveness rate (Indonesia 18% → 25%), 3 周 MVP (1 intent 'overdue reminder' + Bahasa voice + 100 hardcoded user), 然后 8 周 pilot, 然后 parallel 6 markets. 同套 playbook 复用 — 这就是 FDE 工作: 1 套 framework, N customer, 边际成本 ↓."

---

## 🔥 5 Follow-ups

**Q1: FDE 和 SWE 的真正区别是什么?**
Input (混乱需求 vs PRD), Success (客户 KPI vs LOC), Timeline (3-week MVP vs 季度 sprint), Stack (客户限定 vs 团队选), Failure mode (客户不用 vs bug), Skills (60% non-code vs 80% code). FDE 是 customer-site product engineer + solution architect + PM + sales engineer 四合一.

**Q2: 怎么决定 MVP 范围? 客户想要 5 features.**
锁 ONE primary KPI. Decompose workflow 成 N sub-step. 给每步打分 (耗时×痛×LLM-fit×data×risk). Pick **highest single sub-step**, 做端到端. 其他 4 feature 进 phase 2-3 roadmap. 红线: 5 features at 50% < 1 feature at 100%.

**Q3: Sponsor 不在 demo 现场怎么办?**
不 demo. 重新 schedule. Demo 给非决策者 = 浪费 (反馈无法 act). Workaround: pre-demo dry-run 给 champion + 录 demo video + 用 1-on-1 sponsor schedule 30 min on different day.

**Q4: 怎么和 customer 谈 "phase 2 你可能不会做" 的话?**
Honest framing: "MVP success criteria 我们一起定的, phase 2 我们 commitment 是 conditional on phase 1 hit target. 如果 phase 1 missed, 我们会和你一起 decide pivot / iterate / stop." 不要假承诺. Trust > 短期 sales win.

**Q5: 客户的 IT 团队完全不想配合 (deploy 阻力大)?**
Day 1 见 IT lead, 把 constraints 当 input. 找 IT 的 champion (通常是想做新东西的 engineer). 用 IT-friendly 方案 (Cloud Run vs custom K8s, managed Pinecone vs self-host). 让 IT 自己 demo 给他们 boss — 把功劳让出去.

---

## ❌ 易错点 (10 条红线)

1. **Spec before demo** — 6 周 perfect design, 客户看 demo 说 "不是这个"
2. **Promise 100% automation** — 第 1 个 incident 失信
3. **Skip clarifying questions** — design wrong thing perfectly
4. **Vendor-style narrative** — 讲 "我们 platform 怎么 work" 而非客户 KPI 语言
5. **Ignore IT / Security** — week 3 demo 才发现 API 不开放
6. **No observability** — 上线 silent fail
7. **Multiple KPIs** — 同时优化 win rate + cycle time + cost → 都 mediocre
8. **Write code week 1** — 没 scoping
9. **Heroics culture** — 周末烧人, 12 周 sustained 离职
10. **No anti-goals** — 没写 "we are NOT building X", scope creep 无底洞

---

## ✅ 加分项 (12 条)

1. D·K·D·M·P framework 命名 + 5 阶段 walkthrough
2. 3-Question workflow abstraction (Det / Rev / Latency)
3. 4 human-agent patterns coexist (A/B/C/D)
4. 4-layer security (IAM OBO + Injection + Audit + Recovery)
5. Stakeholder map (sponsor / blocker / champion 三角)
6. ONE KPI lock with baseline + target + attribution + confounders
7. Anti-goals doc (negative scope)
8. 3-week MVP 红线 + daily breakdown
9. Trust ladder 4 phase 渐进 autonomy
10. Customer-visible phase tracker (transparent, 不是黑盒)
11. Multi-choice negotiation ("3 options, you pick") instead of saying no
12. Voice agent 7-market story + Indonesia KPI 18% → 25% 数字

---

## 一句话总结

FDE delivery = **customer KPI 北极星 + D·K·D·M·P scoping + 3-question workflow abstraction + 4 human-agent pattern coexist + 4-layer security + 3-week MVP 红线**. 90% 失败不是 code 写错, 是第 1 周没 scope 清楚或没 align stakeholder.

---

## 🃏 Cheat Sheet (印 1 页)

```
FDE ≠ SWE:
  Input: 客户混乱需求 (not PRD)
  Success: 客户 KPI (not LOC)
  Timeline: 3-wk MVP → 12-wk pilot
  Skills: 30% code + 30% customer + 20% scoping + 20% selling

3 ambiguity 必 navigate:
  需求 / 技术栈 / 政治

D·K·D·M·P framework (Customer Scoping):
  D Discovery     (wk 0):   5-7 stakeholder interview
  K KPI Lock      (wk 0-1): ONE primary + baseline + target
  D Decomposition (wk 1):   workflow N step, score each
  M MVP Demo      (wk 1-3): vertical slice 1 path E2E
  P Pilot Rollout (wk 4-12): 10 → 50 → 200 gradual

3-Question Workflow Abstraction (per step):
  Q1 Deterministic? Q2 Reversible? Q3 Latency-sensitive?
  → 5 outcomes:
    Agent auto / Agent+confirm / Agent draft+review / Human+assist / Human only

4 Human-Agent Patterns (coexist):
  A. Confidence threshold escalation
  B. Confirm-required destructive
  C. Scheduled human review (5% sample)
  D. User-initiated takeover (/handoff)

4-Layer Permissions / Safety / Recovery:
  L1 IAM         OBO delegation, agent ≤ user, multi-tenant DEK
  L2 Injection   trust mark + reminder + pattern + confirm UI
  L3 Audit       immutable hash-chained, 90d hot + 7y cold
  L4 Recovery    outbox + compensating handler + bulk rollback

3-Week MVP Playbook:
  Wk1: Discovery (5 interview) + 1-page design + scope lock
  Wk2: Vertical slice build (hardcoded OK, 1 path E2E)
  Wk3: Demo + 5-10 feedback + top 3 prioritized

Trust Ladder (autonomy 渐进):
  Phase 1 suggest mode (human approves all)
  Phase 2 auto deterministic + reversible
  Phase 3 auto + escalate outlier
  Phase 4 autonomous on routine (criteria-defined)

7 FDE Anti-patterns (红线):
  1. Spec before demo
  2. Promise 100% automation
  3. Skip clarifying Q
  4. Vendor-style narrative
  5. Ignore IT / Security
  6. No observability
  7. Heroics culture

45-min Answer Rhythm:
  0-5    Clarify (KPI, users, stack, stakeholders)
  5-10   Mental model (FDE ≠ SWE, 3 ambiguity)
  10-25  D·K·D·M·P walkthrough (your case)
  25-35  Workflow abstraction + 4 pattern
  35-42  Permissions / Recovery 4-layer
  42-45  Resume quote

Resume Hooks:
  Voice agent 7 markets   → T4.1 scoping
  BNPL chatbot            → T4.2 workflow tiering
  Indonesia refund tier   → T4.3 4-pattern in production
  Voice agent + payment   → T4.4 IAM + audit + recovery
  Internal Agent Platform → T4 general framework reuse

Key Phrases (FDE-flavor):
  "Customer-first, KPI-locked, MVP-driven"
  "Automation is not the goal, customer outcome is"
  "Resist scope creep, ship phase 1 first"
  "Anti-goals are as important as goals"
  "Make IT and Legal your ally on day 1"
```
