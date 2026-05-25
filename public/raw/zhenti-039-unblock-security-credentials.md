## Q39 · 客户安全团队拒绝给生产凭证 (你必须解锁)

> "The customer's **security team is refusing to give your deployment team production credentials** to the systems you need to integrate with. You have a **30-min call with the head of their Security & IT team**. Your project is **stalled on this for 2 weeks already**. **Unblock it.**"

**Round**: Client Simulation (30 min)
**出处**: Exponent 2026 FDE · Palantir / OpenAI / Anthropic deployment 必踩
**场景**: Security blocks production credentials. Project stalled. You need to unblock without escalation war.

---

## 📖 术语速查 (本题用到的)

> 这题**安全 + 凭证管理术语最多**. 5 min 速查.

### 沟通 / 谈判核心

| 术语 | 解释 |
|---|---|
| **Respect their role** ⭐ | 尊重对方职责 — "Your team is doing what you're paid to do". Security 头一听就放下武器. 这题开场关键. |
| **Diagnose the fear, not the policy** ⭐ | 诊断恐惧, 不是政策 — 问 "what specific concern?" 不是 "why your policy is strict?". 政策是 surface, 恐惧是 root. |
| **Re-scope narrowly** ⭐ | 缩小范围 — 不要 full prod credentials, 要 read-only + 3 tables + 15 min + 特定 IP. Re-scope = unlock. |
| **Bring their tools** ⭐ | 用对方的工具 — Vault / Okta / Splunk 都他们已用. 不引入新工具 = 降低 adoption 阻力. |
| **Hand them defensible artifact** | 给可上推的文档 — "1-pager for your CISO". Security 头要拿去说服上级. |
| **Help them sell upward** | 帮对方向上推销 — 跟 Q38 同模式, 但这题对象是 CISO 不是 CEO. |
| **Pre-mortem the failure** | 预演失败 — "if breach happens, here's the 5 steps". 主动 walk through 减少对方焦虑. |
| **Kill switch** ⭐ | 一键禁用 — "revoke role in Vault, access dies in seconds". 给对方控制感. |
| **"Genuine appreciation, not grovel"** | 真诚感谢, 不卑微 — "you're the reason this is clean in 12 months". |
| **Don't lead with frustration** | 不以挫败开场 — "we've been blocked 2 weeks" = win the wrong battle. |
| **Escalation war** | 升级战 — 跳过对方找他 CEO = 永远树敌. 这题反面. |

### 安全 / 凭证管理 (core security 术语)

| 术语 | 解释 |
|---|---|
| **Production credentials (生产凭证)** ⭐ | 接到生产环境的密钥 / token / DB password. **vendor 拿到生产 = security 头最大恐惧**. |
| **Vault (HashiCorp Vault)** ⭐ | 业界最常用的 secrets management 工具 — 存 + 动态分发凭证, 支持 JIT, TTL, auto-rotate. 这题必用. |
| **JIT (Just-In-Time) credentials** ⭐ | 即时凭证 — 不预发, 用时才发, 15 min 后自动失效. **替代 static credentials 的金标准**. |
| **Static credentials** | 静态凭证 — 一次发, 永久有效. **安全反面教材**, 一泄露 = 永久泄露. |
| **TTL (Time-To-Live)** | 凭证存活时间 — Vault 配的 15-min TTL 是合理 default. |
| **Auto-rotate / Secret rotation** | 自动轮换 — 凭证定期换. |
| **Okta** ⭐ | 主流身份认证 SaaS — SSO + MFA + SCIM. 这题用来挂 vendor 团队的身份. |
| **SSO (Single Sign-On)** | 单点登录 — 一个 Okta 账号登所有系统. |
| **MFA (Multi-Factor Authentication)** | 多因素认证 — 密码 + 手机 token. |
| **SCIM (System for Cross-domain Identity Management)** | 跨系统身份同步标准 — vendor 员工离职, 自动 deprovision. |
| **RBAC (Role-Based Access Control)** | 角色访问控制 — "read-only on 3 tables" 是 role 定义. |
| **Least privilege** ⭐ | 最小权限原则 — 只给最少必需的访问. 安全基本盘. |
| **Allowlist (vs Blocklist)** | 允许列表 — 默认拒绝, 显式允许. 比 blocklist 安全. |
| **Column-level allowlist** | 列级允许列表 — 不是 `SELECT *`, 显式列出可访问列. 排除 PII. |
| **IP allowlist** | IP 允许列表 — 只允许特定网段连接. |
| **Dedicated subnet** | 专属网段 — vendor 走自己的 IP 范围, 不混在公网. |
| **Blast radius** ⭐ | 爆炸半径 — 一次 breach 的影响范围. Security 关键思考维度. |
| **Data exfiltration** | 数据外泄 — 攻击者把数据偷出去. Security 头第一恐惧. |
| **Breach surface** | 攻击面 — 系统暴露给攻击者的总范围. Vault + JIT + allowlist 都在缩 surface. |
| **Forensics** | 取证 — breach 后查证攻击者做了什么. SIEM log 是关键. |

### 审计 / 监控

| 术语 | 解释 |
|---|---|
| **SIEM (Security Information and Event Management)** ⭐ | 安全信息事件管理系统 — 聚合所有 log + 实时检测异常. **Splunk** 是最常见. |
| **Splunk** | 行业最大 SIEM 厂商. 客户已用 = vendor 用同一个. |
| **Audit log** | 审计日志 — 每个 query / access 记录. 这题 vendor 必 stream 到客户 SIEM. |
| **Anomaly detection** | 异常检测 — SIEM 上的规则, 比如 "full table scan in 非业务小时". |
| **Query logging** | 查询日志 — 每条 SQL / API call 留痕. |
| **Real-time stream** | 实时流 — log 实时进 SIEM, 不是 batch. |

### 合规 / 标准

| 术语 | 解释 |
|---|---|
| **NIST 800-53** ⭐ | 美国国家标准 — 联邦机构 + 大企业的安全控制标准. Access Control (AC) 系列是这题映射. |
| **ISO 27001** | 国际信息安全管理标准. |
| **SOC2 (Service Organization Control 2)** | 美国大企业用的 vendor 安全审计标准. |
| **CISO (Chief Information Security Officer)** ⭐ | 首席安全官 — 这题 James 的上级, 1-pager 给他看的人. |
| **Policy exception** | 政策例外 — CISO 给特定 vendor 一次性豁免, 通常需 documented controls + 季度 review. |
| **Compliance posture** | 合规姿态 — 客户当前满足哪些标准, vendor access 不能破坏这个. |

### 替代方案

| 术语 | 解释 |
|---|---|
| **Sanitized prod replica** | 脱敏的生产副本 — QA 用, 没 real PII. Vendor 开发可用. |
| **Synthetic data** | 合成数据 — 假数据匹配真 schema, 0 PII 风险. |
| **POC (Proof of Concept)** | 概念验证 — 用脱敏数据先证明价值, security 审查并行. |
| **Self-host vs Vendor-host** | 客户自托管 vs vendor 托管 — 如果 security 死活不给 vendor access, vendor code + model 部署到客户侧是终极选项. |
| **MLOps capacity** | 机器学习运维能力 — 客户自托管的前提条件, 不是所有客户都有. |

### 角色

| 术语 | 解释 |
|---|---|
| **Head of Security & IT** ⭐ | 这题对方 (James) — 既管 security 又管 IT, 中型企业常见组合. |
| **CISO** | James 上级 — 1-pager 给他看的人. |
| **24/7 security contact (on-call)** | vendor 侧的安全 on-call 名单 — breach 时客户 24h 内能找到人. |
| **AE / Director / EM** | 你公司的内部 align 对象 — 升级前必 align. |

### Gao Xin 简历相关

| 术语 | 解释 |
|---|---|
| **Indonesia InfoSec team** | Gao Xin 项目里 6-周 hold 的对方 — 类比 James. |
| **ByteDance global data sovereignty** | 字节全球数据主权 — Indonesia 数据不能出印尼是当时具体恐惧. |
| **OJK audit** | 印尼监管对 vendor access 的审计 — Indonesia InfoSec 的 upstream worry. |
| **NDA on prompts** | 提示词 NDA — Gao Xin 用过的具体 mitigation. |

---

## 这道题在考什么

**不是**: 考你能否 push security to give credentials.

**是**: 考你能否在 30 分钟内**理解 security 实际担心什么** + **propose scope they can approve** + **bring their preferred tools to the table** + **not turn this into a war**.

5 个 signal:

1. **Don't lead with frustration** — "we've been blocked 2 weeks" = win the wrong fight
2. **Diagnose THEIR actual fear** — data exfiltration, audit trail, breach surface, compliance exposure
3. **Offer narrow scope** — read-only, time-bounded, IP-allowlisted, vault-managed
4. **Use THEIR preferred tools** — HashiCorp Vault, Okta, AWS IAM Identity Center, their existing JIT pattern
5. **Give them the win** — they're protecting the company. You're enabling that, not bypassing

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 该说什么 | 开口句 (literal) |
|---|---|---|---|---|
| 1 | **Open: respect their role** | 0:00 - 0:30 | "You're the gate. I'm here to make it easy to say yes." | "James, before I make the ask — I want to acknowledge your team is doing exactly what you're paid to do." |
| 2 | **Diagnose the fear** | 0:30 - 6:00 | What's the actual blocker? | "What's the specific concern? Data exfiltration? Audit trail? Breach blast radius? Compliance posture?" |
| 3 | **Mirror back** | 6:00 - 7:00 | Show you got it | "OK so the 3 concerns are X, Y, Z." |
| 4 | **Reframe ask narrowly** | 7:00 - 12:00 | Read-only, time-bounded, scoped | "Let me re-scope the ask: not full production credentials. Specifically: read-only, X duration, Y IPs, Z roles." |
| 5 | **Bring their tools** | 12:00 - 17:00 | Vault, Okta, JIT, allowlist | "Can we use your existing Vault setup? Your Okta SSO? Your IP allowlist?" |
| 6 | **Audit + monitoring** | 17:00 - 22:00 | How they retain visibility | "Every query logged to your SIEM. Daily report. They monitor, we run." |
| 7 | **Pre-mortem the failure** | 22:00 - 25:00 | What if breach happens | "If breach, here's the blast radius. Here's the kill switch." |
| 8 | **Commit + close** | 25:00 - 30:00 | Specific next step | "By end of week: detailed scope doc. Can we get green light by next Friday?" |

**Total**: 6 min listening, 10 min reframe + tools, 5 min audit, 5 min commit.

---

## 30-second 开场脚本 (Verbatim)

> "James, before I make the ask — **I want to acknowledge your team is doing exactly what you're paid to do**.
>
> A vendor walking in asking for production credentials should get pushback. **I'd be skeptical too**.
>
> So I'm not here to argue around your concerns. I'm here to **understand them**, **re-scope what we're asking for**, **bring tools you already trust**, and **leave the audit trail you need**. Whatever the right answer turns out to be — read-only, time-bounded, JIT-issued, vault-managed — **that's the answer I want to land on with you, together**.
>
> So let me start with a question: **what's the specific concern that's blocked this for 2 weeks?**
>
> Walk me through what your team is worried about. I want to know the real reasons, not the polite-no version."

→ Open with **respect for their role** + **ask what they actually fear**. Don't lead with frustration.

---

## 完整对话流 (15-min back-and-forth)

> **James (Security Head)**: "Honestly, it's three things. **(1)** Your team is going to query our production DB and we don't know what queries you'll run. **(2)** Your credentials would be powerful enough to dump our entire customer table. **(3)** If your team has a breach, our customer data is part of the blast radius. None of those are acceptable."

> **You**: "Got it. Three real concerns: **(a)** scope of what we query, **(b)** power of the credential we'd hold, **(c)** blast radius if we're breached.
>
> Let me re-scope our ask **specifically against each concern**, because I think what we actually need is **much narrower than what we initially asked for**.
>
> **For concern (a) — query scope**:
>
> We need to query **3 specific tables**: `customers`, `transactions`, `support_tickets`. We **don't need** anything else. We don't need write access. We don't need to query customer-PII fields (just IDs).
>
> Proposal: **define a read-only DB role** that's restricted to just these 3 tables. Not `SELECT *` — explicitly allowlist columns. **No raw customer SSN / DL / email** in the role. Just enough for our deployment to work.
>
> **For concern (b) — credential power**:
>
> Instead of static credentials, **JIT-issued via your HashiCorp Vault setup**. Credential valid for **15-minute sessions**. Auto-rotated. No long-lived secrets stored anywhere on our side. **Even if our team leaks a credential, it's dead in 15 minutes.**
>
> **For concern (c) — blast radius**:
>
> All queries from us go through **a specific IP allowlist** (our dedicated subnet, not general internet). **Plus**: every query logged to **your SIEM** in real-time, so your team sees what we're doing. If you don't like a query pattern, **kill switch** — pull the role binding, we lose access in seconds.
>
> **Does this match your tooling**? You use Vault and Splunk, right?"

---

> **James**: "Yes Vault + Splunk. OK that's better. But what about non-prod testing? You're going to need to develop against something."

> **You**: "**Great question.** Two options:
>
> **Option A — Sanitized prod replica**: Your team's already producing a sanitized replica for your QA, right? We use that for development + staging. **Zero production credentials during development**. Production credentials only used during the actual production sync runs.
>
> **Option B — Synthetic data**: If sanitized replica isn't available, we generate synthetic data matching your schema. **Schema only — no real values, no PII.** Slower to set up, but fully isolated.
>
> **My preference**: Option A if your replica exists. Faster, more realistic. **Want to check with your team if your QA replica is suitable for our use case?**"

---

> **James**: "Replica exists. OK so JIT credentials, 15-min sessions, IP allowlist, SIEM logging. What's the audit story I'd take to my CISO?"

> **You**: "**Audit story for CISO**:
>
> 1. **Access scope**: read-only on 3 specific tables, allowlisted columns. **Cannot dump customer table.**
> 2. **Credential lifecycle**: JIT-issued via Vault, 15-min TTL, no static credentials anywhere on vendor side.
> 3. **Identity**: vendor team SSO via your Okta. Named individuals, MFA required. **Can attribute every query to a named person.**
> 4. **Network**: dedicated subnet IP allowlist. **Cannot connect from arbitrary internet.**
> 5. **Logging**: every query streamed to your Splunk + your SIEM. **You see what we query, in real-time.**
> 6. **Alerting**: anomalous query pattern (e.g., full table scan, query outside business hours) triggers your existing security incident response.
> 7. **Kill switch**: you can revoke our role binding in Vault, **our access dies in seconds**. No vendor coordination needed.
> 8. **Quarterly review**: audit log review with your team. **If anything's off, we adjust.**
>
> **The compliance frame**: **least privilege + JIT + audit + revocability**. Hits 4 of the 5 NIST 800-53 access control areas. **Your CISO will recognize this pattern.**
>
> **For your CISO meeting**, I'll send a 1-page diagram showing this. **Want me to draft it for you?**"

→ Help them sell to their CISO. **Hand them a defensible artifact.**

---

> **James**: "What if your team needs to add a 4th table later?"

> **You**: "**Two paths**:
>
> **Path A — Pre-define expansion criteria now**: We agree at signing that **read-only role can be expanded to additional tables with same scope rules** with **your approval per table**, **takes 1 business day** to add via Vault config. No re-negotiation of access pattern.
>
> **Path B — Treat each addition as new ask**: Each new table requires full security review. Slower, but you have more control.
>
> **My recommendation**: Path A with clear scope criteria — '**any additional table must be read-only, must be allowlisted at column level, must include identity + PII columns hashed, must update SIEM logging**'. Pre-defined criteria, so adding doesn't require re-review **as long as it fits**.
>
> **If we ever ask for write access or for PII columns, that's a separate conversation**, not in this scope."

---

> **James**: "OK. What's the rollback if your team has a breach 6 months from now?"

> **You**: "**Walking through the breach scenario**:
>
> **Step 1**: Your SIEM alerts (anomalous query pattern from our subnet OR a query attempted from outside our subnet)
>
> **Step 2**: Your team revokes our Vault role binding. **Access dies within seconds.**
>
> **Step 3**: We have a **24/7 security contact on our side** (I'll give you the name + on-call rotation). Your team can call them immediately.
>
> **Step 4**: **Forensics**: your SIEM has every query we made for the last 6 months. **You can reconstruct exactly what we accessed.** If a specific customer is impacted, you have the data to do customer-care direct contact.
>
> **Step 5**: **Re-issuing access**: only after your team's security review of the incident. No automatic re-grant.
>
> **What you DON'T have to worry about**:
>
> - Credentials sitting on a leaked laptop (no static creds)
> - Vendor team going rogue (revokable in seconds)
> - Mass data dump (column allowlist prevents)
> - Unknown queries (SIEM has every query)
>
> **What's still YOUR responsibility**: SIEM monitoring rules, incident response runbook, vendor security review cadence.
>
> Anything missing in this story?"

---

> **James**: "Looks comprehensive. Send me the 1-pager + the proposed Vault config + the dedicated subnet IP range by Friday. I'll review with my CISO next Monday. If she greenlights, we issue you JIT credentials by Wednesday."

> **You**: "**Done. Specifically**:
>
> **By Friday EOD**:
>
> 1. 1-page audit story for your CISO
> 2. Proposed Vault role config (will share Terraform if you use it)
> 3. Dedicated subnet IP range (our infra team is provisioning this week)
> 4. Splunk integration sample (the queries we plan to log)
>
> **Your action**:
>
> - Review with CISO Monday
> - If approved, issue first JIT credential Wednesday
>
> **Once we have first credential**, my team will run **a synthetic-data smoke test first** (verifying connectivity + logging works) **before any production query**. **Will let you know the timing**.
>
> James — **thank you for spending the 30 minutes here**. **Your team is the reason this rollout will be clean in 12 months**, not the reason it's slow this month. **I'd rather we get this right.**"

→ Close with **genuine appreciation for them protecting the company**. Don't grovel; acknowledge.

---

## Gao Xin 简历专属 reframe

> "I had this exact scenario at TikTok PayLater Indonesia. We needed access to **the production transaction database** for the voice agent to look up customer payment history. The Indonesia InfoSec team had a 6-week hold on issuing credentials.
>
> What worked (and what I'd apply directly here):
>
> 1. **I asked what they were afraid of, not what their policy was**. Turned out their three fears:
>    - **PII exfiltration to ByteDance global** (Indonesia data sovereignty concern)
>    - **Voice agent prompts becoming training data** (data leakage)
>    - **OJK auditing them for unauthorized data movement**
>
> Not 'we don't trust your team'. **Specific compliance + regulatory fears**.
>
> 2. **I re-scoped against each fear**:
>    - **PII fear**: only allowlisted columns, no national ID
>    - **Training data leak fear**: NDA on prompts + audit log showing no training pipeline access to data
>    - **OJK audit fear**: 1-pager methodology doc pre-shared with OJK
>
> 3. **I used their existing tools**: their HashiCorp Vault setup + Okta + Splunk. Didn't introduce any new tool.
>
> 4. **I gave them artifacts to take upward**: 1-page audit story they could share with their CISO + with OJK if asked.
>
> 5. **I respected their role explicitly**. **'You're the reason this is clean in 12 months'** — said in writing on our project kickoff doc.
>
> Outcome: credentials issued in 2 weeks (down from 6-week hold), zero security incidents in 18 months of operation, **security team became a champion for expanding our access to other markets** because we'd done it right.
>
> The pattern that transfers: **'unblock security' isn't about convincing security to give in. It's about understanding the specific fear, re-scoping to match, using their tools, and giving them defensible artifacts for their upward conversations.**"

**Other resume hooks**:

- **Indonesia voice agent partner negotiations** — direct analogy
- **BNPL chatbot data access scoping** — similar PII + audit conversation, different market

---

## 5 个 Follow-ups

**Q1**: "What if James actually has no specific concern, just 'no vendor production access'?"

**A**: Treat as policy that needs internal advocacy. Help him build the business case.

> "OK so it's policy-level, not a specific concern about us. **Let me ask — what would it take to update the policy**?
>
> Usually 3 paths:
>
> **(a) Policy exception**: ask CISO for a one-time exception with the scoped access we just discussed. Document the controls, set quarterly review.
>
> **(b) Policy update**: 'vendor access OK if [scoped + JIT + audited + revocable]'. **More work, but it sets precedent for future vendors**.
>
> **(c) Architecture change**: maybe vendor doesn't need direct access. We could **deploy on your side** — your team runs the inference, our IP is just the code + model. **This removes vendor access entirely**.
>
> Which path is feasible? **I'm flexible — I want to find the path that works for your team's frame, not impose mine.**"

**Q2**: "What if James demands you self-host everything (option (c) above)?"

**A**: Engage seriously. This is sometimes the right answer.

> "OK. Let me think through the tradeoffs:
>
> **Self-host benefits for you**:
> - No vendor production access (your top concern resolved)
> - Data never leaves your perimeter
> - Standard ops model (your team runs everything)
>
> **Self-host costs for you**:
> - You operate the GPU cluster (capacity + scaling)
> - You patch the model + dependencies
> - You handle model upgrades
> - **Your team needs MLOps capacity**
>
> **My honest assessment**: if your team has MLOps capacity (you've deployed ML before), self-host is a great answer. If not, the operational burden is real.
>
> **Want me to do a 1-week assessment of your team's readiness** for self-host? I'll come back with: 'self-host works for these 3 reasons, doesn't for these 2, here's the cost'. **Then you decide informed**."

**Q3**: "What if James says yes verbally but his CISO blocks?"

**A**: Anticipate. Pre-empt with CISO 1:1.

> "Smart to anticipate. **Two moves**:
>
> **(a) Brief CISO directly**: I'd offer a 30-min meeting with your CISO + you + me. **Not to bypass you — but to give CISO the audit story directly so she trusts your judgment when you bring it back**. CISO often blocks because she doesn't have full context.
>
> **(b) Pre-empt CISO's likely concerns**: what does she usually ask? 'Audit story', 'comparable vendor handling', 'compliance posture mapping to [NIST / ISO / SOC2]'? **I'll have all three in the 1-pager**.
>
> **Want me to schedule the 3-way for the week after the 1-pager?**"

**Q4**: "What if the project is genuinely blocked beyond 30 minutes' worth of conversation?"

**A**: Adjust scope realistically.

> "If we don't unblock today, **what's the minimum viable engagement we can run while security review continues**?
>
> Options:
>
> **(a) Demo / POC on sanitized data**: continue development on QA replica, no production data, no credentials needed. Show value, security review continues in parallel.
>
> **(b) Read-only batch export**: nightly batch dump (you control), our team consumes the export. Slower data refresh, but no live credentials.
>
> **(c) Move other workstreams forward**: while credential conversation continues, what else can we ship that doesn't depend on it?
>
> **My recommendation**: option (a) — POC on sanitized data, 2 weeks of work, demonstrates value, **gives security team more time without project being entirely stalled**."

**Q5**: "What if you find out James actually has authority but is being slow because he doesn't like your account team?"

**A**: Diagnose carefully. Don't accuse.

- **First**: ask directly but gently. "James, beyond the technical concerns, is there anything about working with us specifically that I should know about? I'd rather hear it than guess."
- **Possible reasons**: bad past experience with your company, AE personality conflict, internal politics where he's anti-vendor in general
- **If account-specific**: bring it to your director + AE. **Don't try to fix the relationship single-handedly without internal alignment.**
- **If personal**: align on different point of contact from his side. Sometimes change of personnel unblocks.

The goal isn't to "win" with James. It's to remove blockers — sometimes that means changing who interacts with him.

---

## ❌ 死路答法 (top 7)

1. **Lead with frustration** ("we've been blocked 2 weeks") — win the wrong battle
2. **Demand full production credentials** — same ask security already declined
3. **Push back on policy** without understanding why — fight the wrong thing
4. **Refuse to use their tools** — insist on your tooling stack
5. **Skip audit story** — no defensible artifact for CISO
6. **Escalate to CEO** as first move — burns bridges
7. **Refuse self-host as alternative** — show you're flexible, not just trying to extract data

---

## ✅ 加分项 (top 7)

1. **Lead with respect for their role**
2. **Diagnose specific fear** (not policy)
3. **Re-scope narrowly** (read-only, time-bounded, IP-allowlisted)
4. **Use their preferred tools** (Vault, Okta, Splunk)
5. **Hand them audit story for CISO** as 1-pager
6. **Pre-mortem breach scenario** with clear roles
7. **Quote your Indonesia InfoSec experience**

---

## 一句话总结

> **Unblock security on production credentials = "respect their role + diagnose specific fear + narrow re-scope + use their tools + hand them defensible artifact + pre-mortem breach"**.
>
> 真正的 win 不是说服 security to give in, 是**让 security 觉得「这个 vendor 帮我做了我的工作 + 给我审计 story 上 CISO + 给我 kill switch」**. 6 周 hold 变 2 周通过 + security 成 champion 不是反对者.

---

## Cheat Sheet

```
不要说:
  - "We've been blocked 2 weeks"
  - "We need full credentials"
  - "Your policy is too strict"
  - "Just trust us"
  - "Other vendors don't ask this"
  - "I'll escalate to your CEO"
  - "Self-host is too hard for us"

要说:
  - "Your team is doing what you're paid to do"
  - "What's the specific concern?"
  - "Let me re-scope to match your concerns"
  - "Can we use your Vault / Okta / Splunk?"
  - "Here's the audit story for your CISO"
  - "Kill switch: your team revokes in seconds"
  - "Your team is the reason this is clean in 12 months"

8-layer response:
  1. Open respect (0:00-0:30)
  2. Diagnose fear (0:30-6:00)
  3. Mirror back (6:00-7:00)
  4. Re-scope narrowly (7:00-12:00)
  5. Bring their tools (12:00-17:00)
  6. Audit story (17:00-22:00)
  7. Pre-mortem breach (22:00-25:00)
  8. Commit (25:00-30:00)

Their likely fears:
  1. Data exfiltration (PII leak)
  2. Credential power (can dump table)
  3. Blast radius (your breach → their data)
  4. Audit trail (regulator inquiry)
  5. Compliance posture (NIST / SOC2 / ISO mapping)

Re-scope against each:
  Exfiltration → read-only + column allowlist
  Power → JIT 15-min via Vault
  Blast radius → IP allowlist + SIEM
  Audit → every query logged
  Compliance → 1-pager NIST mapping

Their preferred tools (anticipate):
  - HashiCorp Vault (JIT credentials)
  - Okta (SSO + MFA)
  - Splunk / SIEM (audit logging)
  - AWS IAM Identity Center
  - CrowdStrike (endpoint)
  - Use what they already operate

The 8-point audit story:
  1. Access scope: read-only + allowlist
  2. Credential: JIT 15-min via Vault
  3. Identity: Okta SSO + MFA, named individuals
  4. Network: dedicated subnet IP allowlist
  5. Logging: real-time SIEM stream
  6. Alerting: anomaly detection
  7. Kill switch: Vault revoke, seconds
  8. Quarterly review

Pre-mortem breach scenario (5 steps):
  1. SIEM alerts on anomaly
  2. Vault revoke (seconds)
  3. Call our 24/7 security contact
  4. Forensics from SIEM (every query logged)
  5. Re-issue only after review

For development:
  Option A: sanitized QA replica
  Option B: synthetic data
  Never: production credentials for development

Alternative if self-host required:
  Honest tradeoff:
  - Pro: no vendor access
  - Con: operational burden on their team
  Offer: 1-week readiness assessment

When James verbally yes but CISO might block:
  Pre-empt with 3-way 30-min CISO + James + you
  Pre-load 1-pager with CISO-anticipated concerns

When asking adding 4th table later:
  Path A: pre-defined expansion criteria
  Path B: new ask each time
  Recommend A with clear scope rules

Specific commits:
  - 1-pager for CISO (date)
  - Vault config / Terraform
  - IP range
  - Splunk integration sample

Resume quote:
  "TikTok PayLater Indonesia: 6-week hold on
   production DB access. Diagnosed 3 specific fears
   (PII to ByteDance global, training-data leak, OJK
   audit). Re-scoped per fear, used their Vault +
   Splunk + Okta. 2 weeks to unblock. Security
   became champion for other markets. Pattern:
   respect role + diagnose fear + their tools + artifacts."

Close line:
  "James — thank you for spending these 30 minutes.
   Your team is the reason this rollout will be clean
   in 12 months, not the reason it's slow this month.
   I'd rather we get this right."
```
