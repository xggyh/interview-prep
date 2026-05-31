# 🎯 T4.1 · Customer Scoping (模糊需求 → 3 周 MVP) — 冲刺版

> 完整版: [gfde-t4-customer-scoping.html](gfde-t4-customer-scoping.html). 200 行能背版.

---

## 📋 我会这样答 (Sample Monologue)

**Clarify (10 sec)**:
"假设: customer 说 'we want AI for X', 第 1 次会面下周, 我 3 周 ship MVP demo. 我假设 — 真 buyer 是 VP 级别, 客户已有 cloud account, 有 < $50K budget allocated, 有 5-7 stakeholder 可见."

**核心 framing**: 不要立即写代码. 客户的 vague request 是**起点不是终点**. Week 1 不写一行 production code, 全部 discovery + scoping.

### Layer 1: D·K·D·M·P framework (5 阶段)

```
D - Discovery     (day 1-3): 5-7 stakeholder interviews + shadow 1-2 user
K - KPI Lock      (day 3-4): ONE primary + baseline + target + sign-off doc
D - Decomposition (day 4-5): workflow 10 sub-step + 5-score matrix
M - MVP Design    (week 1-3): vertical slice, 1 happy path E2E, hardcoded OK
P - Pilot Rollout (week 4-12): 3 friendly rep → A/B → 10-20 expand
```

### Layer 2: 5-7 Stakeholder Roles (Mason Mirin-style)

| Role | 关心 | 你问 | 失败信号 |
|---|---|---|---|
| **Sponsor (VP)** | OKR + budget + decision | "如果完美 ship 3 月后, 你 quarterly review 哪个 number 涨?" | 答 "all metrics" → 不是真 buyer |
| **Process Owner (Ops)** | 流程 + 数据 + 工具 | "现在 workflow 每步是啥? 数据 in Salesforce or off-platform?" | 不知道 = 不是 owner |
| **End User × 2** | 自己 daily 爽不爽 | "Walk me through 昨天 — 30% 时间花哪? 最讨厌哪步?" | 没时间见你 = 项目不重要 |
| **IT / Security** | API + data + SSO | "Service live 哪? 数据出 cloud? PII 允 LLM 看?" | week 3 才知道 API 不开放 |
| **CFO / Finance** | ROI + payback | "ROI 阈值? Rep fully-loaded cost?" | 不关心 = 项目不是真投资 |
| **Champion** | 帮你穿针引线 | "谁是真决策者? 内部还有什么我没看到?" | 没 champion = 项目难推 |

**Async fallback**: 约不上 → 1-page 5-Q questionnaire / shadow 1 day / champion 转述 / 翻 public data (jobs page / 财报).

### Layer 3: KPI Lock — Mason Mirin's 5 Clarifying Qs → ONE Number

1. "If perfect in 3 months, what ONE number on YOUR quarterly review improves?"
2. "Baseline today? Verified how?"
3. "Winning delta — 10%? 50%?"
4. "Attribution measure (A/B vs before-after)?"
5. "Confounders that could fake-cause movement?"

**KPI Lock Doc** (sign-off required): Primary metric / Definition / Baseline / Target post-MVP (3wk) / Target post-pilot (12wk) / Measurement / Attribution / Confounders / Secondary KPIs (watch only) / Signed by VP + Ops + FDE.

### Layer 4: MVP Carve-out (IN vs OUT 硬列表)

**IN**: LLM-gen output + RAG grounding + Salesforce read API + Streamlit UI + 1 happy path E2E
**OUT (Phase 2+)**: write API + multi-rep + mobile + multi-language + multi-tenant + proper SSO + CI/CD + edge case + production observability

**Hardcoded OK**: 100 test data + 1 user + 1 prompt + 1 routing path + 3 templates
**Hardcoded 红线**: 不能假装 hardcoded 数据是 customer's real data (诚信)

### Edge cases (5 个最高频)

- **EC1 Scope creep (wk 2 客户加新 feature)**: Acknowledge + frame trade-off + park in roadmap doc + defer decision. 不当场说 yes/no.
- **EC2 客户改主意 (wk 3 要 pivot)**: 区分 — 真 pivot (新业务洞察) 延 demo 1 wk + re-lock KPI; shiny toy (老板看 LinkedIn 文章) push back 留 phase 2.
- **EC3 "Faster please" (1 周不是 3 周)**: Multi-choice — Option A (1-wk PoC hardcoded 5 lead) / B (3-wk MVP real CRM) / C (both — A as CEO demo + B as pilot). 让客户选.
- **EC4 "100% automation"**: Push back via trust ladder Phase 1-3. 算 ROI: 1-2-3 sequential = 5 months to full auto; direct-full = 8+ months (有 incident → rollback → restart).
- **EC5 Demo 后 underwhelmed**: 问 "what did you expect that you didn't see?" 通常 = KPI not visible. Recovery: 同周 ship revised demo with concrete delta number.

### Production hardening (3-week 节奏)

- **Wk1 Mon-Fri**: 5 interview / Tue-Wed / Thu KPI lock / Fri scope lock
- **Wk2 Mon-Fri**: Build vertical slice (input / process / output / edge / dry-run)
- **Wk3 Mon-Fri**: Demo prep + Demo Day 14 (10 min live + 5 min Q&A) + feedback triage + roadmap update
- **Demo Day storyboard**: 0-3 recap KPI / 3-15 live demo (with stopwatch vs baseline) / 15-22 数据 (extrapolate $$ saved) / 22-27 phase 2 roadmap / 27-30 Q&A

### 🪝 Resume hook

"TikTok voice agent expansion to Indonesia 就是这套 D·K·D·M·P. Wk 0 — 5 interview (ops head + compliance + finance + IT + local supervisor). KPI = CER (collection effectiveness rate), baseline 18%, target 25%, measured 8 wk. MVP = 1 intent (overdue reminder) + Bahasa voice + 100 hardcoded user, demo wk 3. Pilot wk 4-8 hit 23% CER statistically significant. 2 scope creep managed (multi-language fallback → phase 2, real-time cost dashboard → phase 3). 同 playbook 复用 Vietnam / Thailand / Philippines."

---

## 🔥 5 Follow-ups

**Q1: 客户非技术 (CMO 买 marketing tool), 怎么 present design?**
No architecture diagram in 1st meeting. Show storyboard (before/after workflow, 1 page). Show estimated $$ saved (rep cost × hours saved). Use customer vocab (AI assistant, not agent/embedding/vector). Diagrams reserved for IT/Eng meeting.

**Q2: 约不上 5 个 interview, 客户太忙?**
Async via 1-page 5-Q (10 min ask vs 30 min meeting). Shadow 1 day (信息量爆炸). Champion proxy (准确度打折但有). Public data (jobs / 财报 / news). Reduce to 3 critical + caveat ("based on incomplete discovery, assumptions: A B C").

**Q3: 客户要 "agentic" buzzword 但实际只需要 RAG Q&A?**
Build what's needed, not what's hyped. v1 = RAG Q&A, v2 = tool use, phase 3 = autonomy. They keep marketing language ("our new AI agent"), you build right thing. 不要 over-engineer 满足 buzzword.

**Q4: MVP demo 失败, 客户 underwhelmed. 怎么办?**
Diagnosis: "What did you expect that you didn't see?" Common: KPI not visible (showed features, not delta). Recovery same day — regroup + 当周 revised demo with concrete number. Postmortem: 为啥没 mid-week dry-run with champion.

**Q5: Scope creep — 客户每周加 "small" request?**
Roadmap doc (every request 进, dated, phase assigned). Trade-off framing ("加 X = 延 Y by 1 wk, which?"). Quarterly re-prioritize. Sponsor enforces scope (你不当 bad guy). Plot "items added vs shipped" chart, divergence → re-commit conversation.

---

## ❌ 易错点 (10 条红线)

1. **Write code week 1** — 没 scoping → wrong product
2. **No stakeholder interview** — design 基于 VP 单方面 view
3. **Multiple KPIs** — never know if MVP succeeded
4. **Try to automate all 10 workflow steps** — never ship MVP
5. **No demo until production-ready** — no early feedback
6. **Build for perfection week 1** — multi-tenant + observability 没必要
7. **Say yes to every scope add** — never ship
8. **Promise 100% automation** — first incident trust collapse
9. **Skip IT/Security align wk 1** — wk 3 blocked by API
10. **Demo without baseline number** — 客户问 "how much better?", 答不上

---

## ✅ 加分项 (12 条)

1. D·K·D·M·P framework 命名 + 5 阶段 walkthrough
2. 5-7 stakeholder roles + per-role 5-Q playbook
3. ONE primary KPI + baseline + target + measurement + attribution + confounders
4. Smallest vertical slice (1 step E2E, not 10 step surface)
5. 3-week timeline daily breakdown
6. Trust ladder (suggest → confirm → auto, 不 promise 100%)
7. Roadmap doc as scope-creep defense
8. Real-pivot vs shiny-toy distinction
9. Multi-choice negotiation ("3 options, you pick")
10. Demo Day 14 storyboard (KPI recap / live demo / data / phase 2)
11. Anti-perfection rules (hardcoded OK list + 红线)
12. Indonesia voice agent 18% → 25% concrete number

---

## 一句话总结

T4.1 = **用 D·K·D·M·P 框架把客户 vague request 收敛成 ONE KPI + ONE vertical slice + ONE E2E demo, 3 周内 ship**. 90% FDE 项目失败在第 1 周: 没 interview / 没 KPI / 没拆 workflow / 没说 no.

---

## 🃏 Cheat Sheet (印 1 页)

```
D·K·D·M·P framework:
  D Discovery     (d1-3):  5-7 stakeholder interview + shadow 1 user
  K KPI Lock      (d3-4):  ONE primary + baseline + target + sign-off
  D Decomposition (d4-5):  workflow N step + 5-score matrix
  M MVP Design    (w1-3):  vertical slice 1 happy path E2E
  P Pilot Rollout (w4-12): 3 friendly → A/B → 10-20 expand

5-7 stakeholder roles (30 min each, verbatim notes):
  Sponsor (VP)        OKR + budget + decision
  Process Owner (Ops) workflow + data + tools
  End User × 2        daily pain + time tracking
  IT / Security       API + data + SSO + auth
  CFO / Finance       ROI threshold + payback
  Champion            internal insider
  Your CS             historical context

Mason Mirin's 5 Q for KPI lock:
  1. "ONE number on your quarterly review improves?"
  2. "Baseline today? Verified how?"
  3. "Winning delta — 10%? 50%?"
  4. "Attribution (A/B vs before-after)?"
  5. "Confounders that fake-cause movement?"

KPI Lock Doc template:
  Primary metric / Definition / Baseline / Target post-MVP /
  Target post-pilot / Measurement / Attribution / Confounders /
  Secondary (watch only) / Signed by VP + Ops + FDE

Decomposition score (per step):
  耗时 + 痛感 + LLM-fit + data-ready + risk (1-5 each)
  Pick highest 1-2

MVP carve-out (IN vs OUT):
  IN:  LLM-gen + RAG + read API + Streamlit + 1 happy path
  OUT: write API + multi-rep + mobile + multi-lang + multi-tenant + SSO + CI/CD
Hardcoded OK: 100 test data / 1 user / 1 prompt / 1 routing
Hardcoded 红线: 不能假装 hardcoded 是 customer real data (诚信)

3-week timeline:
  Wk1: 5 interview / KPI lock / scope lock
  Wk2: vertical slice build (input/process/output/edge/dry-run)
  Wk3: demo prep + Demo Day 14 + feedback + roadmap

Demo Day 14 (30 min):
  0-3   Recap context + KPI
  3-15  Live demo (with stopwatch vs baseline)
  15-22 Data extrapolate $$ saved
  22-27 Phase 2+ roadmap (NOT in MVP)
  27-30 Q&A

Customer management tactics:
  Scope creep      → roadmap doc, defer next phase
  Change of mind   → real-pivot vs shiny-toy distinction
  "Faster please"  → multi-choice (PoC / MVP / both)
  "100% auto"      → trust ladder Phase 1-3
  Non-tech CMO     → storyboard, no architecture
  "Agentic" buzz   → build right, keep their language

Anti-patterns (红线):
  - Code week 1 / No interview / Multiple KPIs
  - Try automate all / No demo til ready / Build for perfection
  - Say yes to all / Promise 100% auto / Skip IT / No baseline

Resume hooks:
  - Voice agent 7 markets scoping
  - Indonesia CER 18% → 25%
  - BNPL chatbot phased ship
  - Refund tier 1/2/3 trust ladder
  - Internal Agent Platform roadmap discipline
```
