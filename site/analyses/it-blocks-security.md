## 题目（verbatim）

> "Client's **IT team blocks your integration** citing **security concerns**. Navigate the politics, get unblocked, ship the deployment."

**出处**: fde.academy 客户模拟. Enterprise FDE 必经的政治情景. Palantir / OpenAI / Anthropic / 任何 enterprise SaaS 都问.

**Round**: Client Simulation (45 min)

---

## 这道题在考什么

考你**enterprise politics navigation + 多 stakeholder management + 真懂 security control**:

1. **理解 IT 真实诉求** — security 只是表面理由, 真问题可能是 NIH / 控制欲 / 担心 layoff / regulatory fear / vendor lock-in 担心
2. **Joint problem solving** — 跟 IT 站一边对外, 不是 vs IT
3. **Compliance language** — 你说「我们 secure」 = noise; 你说「SOC 2 + DPA + per-tenant DEK + BAA」 = checklist items IT 能拿给老板
4. **Phased approach** — restrictive first, expand on trust
5. **Sales vs IT 张力** — IT 是 risk function, sales 是 revenue function. 你 navigate 两边
6. **Compliance certifications** — 真懂 SOC 2 vs ISO 27001 vs HIPAA vs PCI 适用场景
7. **Knowing what NOT to promise** — 答应 customer-controlled key 是 OK, 答应 air-gapped on-prem 不能轻易 commit
8. **Reading the room** — IT 是 hard-block (政策) 还是 soft-block (流程慢)? 决策不同

这是一道**很被 underrate 的题** — 大部分 candidate 只会答「我们 secure, 我们 SOC 2」, 但 IT block 的真因 90% 不是 "you're insecure", 是其他东西.

---

# Part 1 · 教学讲解

## 1. 六个核心术语先解释

**SOC 2 Type II**: AICPA 制定的服务组织 security audit standard. **Type II** = 6 个月或 12 个月运营审计 (vs Type I 是一次性 design audit). Enterprise customer 99% 会问. 一份 SOC 2 报告通常 100+ 页, 覆盖 security / availability / processing integrity / confidentiality / privacy 五个 trust principles. **你的 deal 决定签否, 多数情况由这份报告决定**.

**ISO 27001**: 国际 information security management standard. 覆盖更全面的 ISMS (Information Security Management System), 包括 risk treatment / asset management / access control. 欧洲客户更 push. SOC 2 + ISO 27001 = enterprise 完整 baseline.

**HIPAA**: 美国医疗数据法. 涉及 PHI (Protected Health Information). 需要 BAA (Business Associate Agreement) 签字. **不签 BAA 不能碰 PHI**.

**PCI DSS**: 支付卡数据安全标准. 涉及信用卡号 / CVV 等. 需要 attest compliance level (1-4). Level 1 = 大型商户最严.

**BAA (Business Associate Agreement)**: HIPAA framework 下, vendor 跟 covered entity (医院 / 保险) 签的合同, 规定 vendor 处理 PHI 的责任 / 限制 / breach 通知义务.

**DPA (Data Processing Agreement)**: GDPR framework 下, controller (客户) 跟 processor (你) 签的合同, 规定 data 怎么处理 / 跨境 / 删除. 欧洲客户 mandatory.

**DEK / KEK / BYOK / HSM**:
- **DEK** (Data Encryption Key) = 实际加密数据的 key
- **KEK** (Key Encryption Key) = 加密 DEK 的 key (key wrapping)
- **BYOK** (Bring Your Own Key) = 客户提供 KEK, 你存 DEK
- **HYOK** (Hold Your Own Key) = 客户 hold KEK, 你每次解密都问客户
- **HSM** (Hardware Security Module) = 物理硬件保存 key, FIPS 140-2 Level 3+

**Data residency**: 数据物理上在哪个 region. EU customer 多数要 EU residency. 越南要 in-country. **你 multi-region 部署能力决定能不能接这些客户**.

**Zero Trust**: 不假设任何 network 默认可信. 每次访问 require explicit auth + audit. 现代 enterprise security 范式.

**Threat model**: 系统化分析 "谁可能攻击我? 怎么攻击? 我怎么 mitigate?" 框架. STRIDE (Spoofing / Tampering / Repudiation / Info disclosure / DoS / Elevation) 是经典 framework.

---

## 2. 这个场景的核心矛盾是什么

**矛盾 1: IT 表面理由 vs 真实理由**

IT 嘴上说 "security concerns". 真因可能是:
- 真的 security (e.g., 你不 SOC 2 → 真 block)
- 控制欲 (vendor 进来 = 我管不到)
- NIH (我们 in-house 也能做)
- 个人风险 (vendor 出事 = 我背锅)
- Regulator 担心 (上次审计 ding 过)
- Sales 跳过 IT 流程的怒气

→ 你的 first job 是 **识别真因**, 否则按错药.

**矛盾 2: IT vs Business 内部冲突**

客户内部, business 推产品, IT 卡 security. 你是 vendor, 你被 caught in middle. **站任何一边都错**.

**矛盾 3: 时间 vs 严谨**

Business sponsor push 你 "this week launch". IT 走 standard review 要 6 months. **你不能 skip IT 流程** (那是关系自杀), 但也不能 give up Business sponsor (那他失去 internal champion).

**矛盾 4: 承诺 vs 工程**

IT 想要 "data never leaves our network" / "you don't store our PII" / "on-prem deployment". 你想说 yes 但**有些技术上做不到**或**经济上不可行**.

**矛盾 5: 个人 IT contact vs IT 团队 vs CISO**

IT block 可能来自不同 level. 跟 security analyst (执行层) 谈 ≠ 跟 CISO (决策层) 谈. **找对人**.

**矛盾 6: 严格证明 vs 透明示弱**

IT 会问 "show me your pen-test results". 拿出来 = 信任. 拒绝 = "they're hiding something". 但 pen-test 总有 finding, 你 expose 的同时也在 expose vulnerability.

**矛盾 7: 销售压力 vs reputation**

AE 想 force escalation 越过 IT 到 CIO. 短期能赢. 长期 = IT 永久敌对, 续约时 explode.

---

## 3. 决策树 / 反应模板

| 时间 | 你的核心动作 |
|---|---|
| **接到 IT block 信号 (0-24h)** | 不 panic, 不 escalate. 先理解 |
| **24-48h** | Request 1:1 with IT lead. 不要 group call |
| **Week 1** | Listen-only call. Identify 真实 layer (L1/L2/L3/L4) |
| **Week 1-2** | Compliance checklist response + 3-tier rollout proposal |
| **Week 2-4** | 3-way working session (sales + IT + you) + joint plan |
| **Month 1-3** | Phased pilot + IT veto authority + governance setup |
| **Month 3+** | Quarterly security review + maturity |

---

## 4. 关键利益相关方对照表

| Stakeholder | 他们在意什么 | "Vendor 想集成" 时的内心 OS | 你对他们的关键动作 |
|---|---|---|---|
| **CISO** (顶层 IT 决策) | Org risk / 监管 / breach 可能性 | "Vendor 出事我背锅" | Compliance package + BAA/DPA + executive briefing |
| **Security architect** | Specific control gaps | "Their architecture passes my tech review?" | Architecture doc + threat model + pen-test summary |
| **Compliance officer** | SOC 2 / ISO / 行业法规 | "Are they audited? Recent?" | Send recent audit report (NDA-gated) |
| **IT director** (中层) | 团队 oversight | "Vendor 自己管 vs 我管?" | Joint governance + IT veto at stages |
| **Security analyst** (执行层) | Daily monitoring | "Vendor logs 我能看吗?" | Audit log access + monitoring integration |
| **Business sponsor** | 自己的 deal / KPI | "IT 卡我项目" | 1:1 align: 我帮你, 但要尊重 IT 流程 |
| **AE / Sales** | Close deal | "Escalate over IT" | Internal align: 不许 escalate, 走流程更快 |
| **客户 法务 / privacy** | Contractual liability | "Standard contract 改不改" | Fast-track contract review, 48h SLA |
| **你的 CISO** | 你公司 reputation | "Don't over-commit" | Pre-align: 我能承诺的 ceiling 在哪 |
| **你的 EM** | Engineering scope | "On-prem 不是免费" | Confirm what we can engineer |

---

## 5. 具体业务场景 (4 个变种带人物)

### 场景 A: TikTok PayLater Voice Agent 上线印尼, OJK + Bank IT 双 block (贴近 Gao Xin 工作)

**人物**:
- 你 (FDE) + 印尼区 GM Yuri + 你的 CISO Linda
- Bank IT 方: CISO Maria, security architect Andi, compliance director Budi
- OJK (监管): 3 examiner

**Setup**: Voice agent 接 Bank 系统做催收. Bank IT 担心:
- 客户 PII 流向 vendor cloud (data sovereignty)
- LLM 生成内容 unpredictable (auditability)
- TikTok 的 China 关联 (geopolitical, 印尼特别敏感)

**Maria 的 hard line**: "Without **in-country data residency + customer-controlled encryption + audited model**, we won't integrate."

**真因**: Maria 自己上次被 ex-vendor 烧了 (data 流出 + 监管罚款), 自己很 nervous. **不是 generic security paranoia**.

→ Part 2 全部以此为蓝本.

### 场景 B: Acme Bank Compliance Block CRM 集成

**Setup**: 你的 CRM 集成 chatbot 接 Acme 银行客服. Acme compliance 要 BAA-like terms.

**特殊性**: 不是 HIPAA, 但 Acme 把 financial data 当 PHI 级 protect. 你需要 sign customized agreement.

### 场景 C: 欧洲客户 GDPR Hard Block

**Setup**: 你的 SaaS 给欧洲 enterprise 用. GDPR 要求 data 不出 EU + 客户 right to be forgotten + DPA.

**特殊性**: GDPR fine 高 (up to 4% global revenue). 客户绝对不让一步.

### 场景 D: US Federal Government Customer

**Setup**: 你想卖给 US federal agency. 要 FedRAMP authorization.

**特殊性**: FedRAMP 是 1-2 年 process, **你可能根本拿不到**. 如果 customer hard-require, 你 deal 死了, 接受 reality.

---

## 6. 工程上 / 应对上要做什么 (Playbook)

按 **48h / 1 周 / 1 个月 / 3 个月** 4 阶段:

### 阶段 1 · 48 小时内 (识别 block 性质)

1. **不 panic, 不 escalate**. 第一反应不是 "go around IT"
2. **Request 1:1 with IT lead** (CISO / IT director / security architect — 看 block 来源)
3. **Listen-only meeting**: 30-min, 让对方说. 不 defend, 不 list mitigations
4. **Internal align with business sponsor**: 他知道这个 1:1 在发生, 不绕开他
5. **Internal align with your CISO + EM**: 提前知道 what we can and can't commit

### 阶段 2 · 1 周内

6. **Identify 4 layers** (L1/L2/L3/L4 — see Problem 1) 真实诉求
7. **Compliance checklist response**: 24h 内 deliver, 不让 IT 等
8. **Architecture diagram + threat model + pen-test summary**
9. **3-tier rollout proposal**: sandbox → restricted prod → broader
10. **3-way working session** (business + IT + you) — joint plan

### 阶段 3 · 1 个月内

11. **Sandbox pilot** running with IT full audit access
12. **Governance setup**: IT veto authority at each tier transition
13. **Quarterly security review cadence** established
14. **Customer-controlled encryption / BYOK** deployed
15. **Audit log integration** to customer's SIEM

### 阶段 4 · 3 个月内

16. **Tier 2 production rollout**, limited scope
17. **IT signoff on every expansion**
18. **3rd-party pen-test** (customer's choice, you pay)
19. **Real production monitoring** transparently shared

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **Escalate over IT to CIO** | IT 永久敌对, 续约时 block. 几乎从不该做 |
| 2 | **Skip IT review process** | 越过流程 = burning bridge |
| 3 | **Argue with IT in group call** | 公开 loss, IT 面子受损更狠 |
| 4 | **Promise "我们 secure"** without checklist | Hand-wave, IT 立刻 dismiss |
| 5 | **Blame sales VP to IT** | Internal disloyalty, IT 不 trust |
| 6 | **NIH 当 obstinacy 误判** | 错失 ally 机会 |
| 7 | **没 phased option** | All-or-nothing 死 |
| 8 | **Over-promise on-prem / air-gap** | 工程上做不到, 后续 explode |
| 9 | **没 read who blocked you** | CISO vs analyst vs architect, 反应完全不同 |
| 10 | **Send generic 50-page SOC 2 report** | IT 看 5 分钟, 跳到 "我们要 specific 答案" |
| 11 | **没 internal CISO align** before commit | 你公司 CISO 后续否决你的承诺 |
| 12 | **客户内 sponsor 落单不联络** | Business sponsor 失去信号, 自己内部斗争失败 |

---

## 一句话总结 (Part 1)

> **IT 不是你的敌人, 是你最稳定的盟友 — 如果你赢得他的信任**.
>
> 大部分 IT block 不是真 security concern, 是**控制感缺失 + 流程被跳过 + 个人 risk 担忧**. 你的 job 不是 "证明 we're secure", 是 **让 IT 感受到他在控制 process + 给他可量化的 checklist + 给他 veto 权**.
>
> 一旦 IT 站你这边, sales 进度反而比绕过他更快. 这是 enterprise selling 的反直觉真理.

---

# Part 2 · 5 个深度问题 (Client Sim 硬核细节)

## ⚙️ Problem 1: Understand What They Actually Fear — 4-Layer Concern Model

**90% 的 IT block 真因不在表面**.

### 1.1 IT 真实顾虑的 4 个 layer

| Layer | What they say | What they mean | Remedy class |
|---|---|---|---|
| **L1 Surface** | "Data leaves our network" | Standard infosec concern, addressable | Checklist (SOC 2 / ISO / DPA) |
| **L2 Control** | "We don't manage your access" | Want oversight, not necessarily veto | Governance access + audit log |
| **L3 NIH** | "We have internal alternative" | Built or own competing system | Make them ally + joint platform |
| **L4 Career** | "Vendor outage = my fault" | Personal risk if you fail | Legal SLAs + contract guarantees |
| **L5 Geopolitical** | "Don't trust [country]" | Political / regulatory anxiety | Data residency + corporate structure |
| **L6 Past trauma** | (Doesn't say it) | 上次被 vendor 烧了 | Trust building over time, not 1 doc |

**每层 different remedy. 错配 remedy = block 永不解**.

### 1.2 怎么 detect 真正 layer

不能直接问 "你真正怕什么". 通过 **listening + question** triangulate.

**Listen for**:

| Signal | Likely layer |
|---|---|
| Mentions "SOC 2 / encryption / data" | L1 Surface |
| Asks "who has access to our data" | L2 Control |
| Mentions "we tried building this" | L3 NIH |
| Mentions "last time we had a vendor outage" | L4 Career or L6 Past trauma |
| Mentions country / regulator name | L5 Geopolitical |
| Sigh / says "I've seen this before" | L6 Past trauma |

**Triangulating questions**:

| Question | What it reveals |
|---|---|
| "What would 'comfortable' look like for you?" | What they're optimizing for |
| "Have you done similar integrations recently? What worked / didn't?" | Past pattern, L3/L6 |
| "If something goes wrong, what's the worst case for your team?" | L4 Career anxiety |
| "Is there a specific framework or checklist you'd want us to align to?" | L1 surface (concrete) |
| "What does your normal vendor onboarding look like?" | L2 Control (process) |

### 1.3 1:1 with IT 的 sample script (50% listen, 50% speak)

> *(Maria 的 office, 30 分钟)*
>
> 你: "Maria, thanks for taking the time. **I want to start by understanding your concerns directly** rather than getting them filtered through David (business sponsor). I came without a deck. I just want to listen first.
>
> What concerns you most about this integration?"
>
> *(Maria talks for 8 minutes. You take notes, no interruption.)*
>
> Maria: "...basically, last year another vendor exfiltrated PII data through their integration. We got a regulator visit, my team was 90 days on remediation. **I'm not going to let that happen again**."
>
> 你 *(now you know real layer: L6 Past trauma + L4 Career)*:
>
> "I hear you. **Your concern is justified, and your reaction is reasonable**. I want to give you 3 things that would have caught that previous incident in our architecture:
>
> **(1) BYOK encryption** — even if our service were compromised, we cannot decrypt your data without your KMS authorization. Your team controls access at the cryptographic level.
>
> **(2) Audit log streaming to your SIEM** — every API call we make to your data lands in your monitoring system in real-time. **You'd see exfiltration attempts**, not learn from the regulator.
>
> **(3) Quarterly pen-test** by a firm of your choosing, paid by us — they break our defenses with your team observing. **You verify, you don't trust**.
>
> All 3 deployed at Tier 1 pilot, with your veto if anything looks off. **Would you walk me through which of these would have caught the previous incident?**"
>
> *(转 conversation to 'how would 这 architecture have prevented past incident'. Let Maria validate.)*

→ 这个 1:1 让 Maria **从 'block-er' 变 'co-designer'**. 信任 quickly 转.

### 1.4 不同 IT roles 的优先级差异

| Role | 看什么 | 你给什么 |
|---|---|---|
| **CISO** (decision) | Org-level risk + 监管 | Executive briefing + recent breach response history + insurance / liability |
| **Security architect** | Specific controls | Architecture diagram + threat model + control mapping |
| **Compliance officer** | Audit-grade evidence | SOC 2 report + ISO cert + recent renewal date |
| **Security analyst** | Daily ops | Log streaming + monitoring integration + on-call runbook |
| **IT director** | Team workload | Governance flow + IT signoff process + minimal overhead on their team |

→ **同一份 deck 给所有 5 个人 = wrong**. Customize per role.

### 1.5 当 IT 拒绝 1:1 (politics already broken)

**Scenario**: Maria's team refuses 1:1 meeting, says "go through formal review process".

这通常意味着 sales 之前 already burned bridge.

**Response**:

> "Of course. Could you point me to the formal review intake? I'd rather **go through your standard process** than create a one-off.
>
> *(After completing intake)*
>
> Once we're in the queue, could you tell me **where in the queue we are + what's the typical timeline**? I want to set realistic expectations with David's team about when we might be reviewable.
>
> One more ask: **if there are any pre-emptive documents I can prepare** (SOC 2 report, architecture diagram, threat model, BAA template), I'd love to attach them upfront so we don't have a doc-back-and-forth cycle."

→ Respect process. Even when you'd rather have 1:1, **complying with their process** is **trust currency**.

### 1.6 红线: 不要替 IT 答 IT 的问题

错的 move: 「I know what they really care about, let me address X.」

对的 move: **Let them tell you what they care about**. Make them define the problem. **Then you propose solutions to their problem**, not to your imagination of their problem.

---

## ⚙️ Problem 2: Security Control Inventory — 你能 Offer 的全套

**你应该 walk in with 这一整套 toolkit**.

### 2.1 完整 security control 清单 (按客户优先级)

**(a) Encryption**

| Item | Detail | 多数 customer demand |
|---|---|---|
| At rest | AES-256 | ✓ |
| In transit | TLS 1.3 | ✓ |
| Per-tenant DEK | Each customer has separate DEK | ✓ enterprise |
| Customer-controlled KEK (BYOK) | Customer's KMS holds the master key | Higher-security |
| HSM-backed | FIPS 140-2 Level 3+ | Banking / gov |
| Customer-hosted HSM (HYOK) | Customer's HSM holds the key, you call out | Rare, very high security |

**(b) Access controls**

| Item | Detail |
|---|---|
| RBAC | Role-based access control inside your service |
| SSO via SAML / OIDC | Customer's identity provider |
| MFA enforcement | Customer can enforce |
| Service account access | Auditable, time-bounded |
| Just-in-time access | Engineer access requires approval + 1h time-box |
| IP allowlist | Customer can restrict |

**(c) Audit + Monitoring**

| Item | Detail |
|---|---|
| Audit log every API call | Standard |
| Streamed to customer SIEM | Splunk / Datadog / customer chosen |
| Real-time anomaly detection | Outlier detection on access patterns |
| Tamper-evident log | Cryptographically signed |
| Retention 7+ years | Compliance |

**(d) Data handling**

| Item | Detail |
|---|---|
| Data residency | Per-region (US / EU / APAC / specific country) |
| No data leaves designated region | Enforced via deployment |
| Right to be forgotten | GDPR Article 17 compliant |
| Data deletion certificate | After contract end |
| No training on customer data | Explicit DPA clause |
| Tenant isolation | DB-level enforcement (RLS / separate schema) |

**(e) Deployment options**

| Option | What | When customer demands |
|---|---|---|
| Multi-tenant SaaS | Standard | Default |
| Single-tenant SaaS | Dedicated instance for them | Mid-tier |
| VPC peering | Your service in customer VPC | Enterprise |
| On-prem | Your software runs on their hardware | Rare, very enterprise |
| Air-gapped | Fully isolated, no internet | Government / defense |

**(f) Compliance certifications**

| Cert | Use case | Renewal |
|---|---|---|
| SOC 2 Type II | General enterprise | Annual |
| ISO 27001 | Global / European | 3-year cycle |
| HIPAA + BAA | Healthcare PHI | Per-engagement |
| PCI DSS Level 1 | Payment card data | Annual |
| FedRAMP | US Federal Gov | 1-2 year initial |
| GDPR DPA | EU customers | Per-engagement |
| ISO 27017 / 27018 | Cloud-specific | Annual |
| SOX (Sarbanes-Oxley) | Public company | Annual |

**(g) Incident response**

| Item | Detail |
|---|---|
| 24/7 on-call | Standard |
| Breach notification SLA | Within 24h |
| Forensics support | Free during incident |
| Customer-facing RCA | Within 5 days |
| Cyber insurance | $X million coverage, certificate available |

### 2.2 Tier-based offering (matched to customer tier)

| Tier | Customer profile | Standard offer |
|---|---|---|
| **Bronze** (SMB) | < $50K ARR | Multi-tenant, AES-256, TLS 1.3, SOC 2 |
| **Silver** (Mid) | $50K-$500K | + BYOK, audit log streaming, dedicated SE |
| **Gold** (Large enterprise) | $500K-$5M | + Single-tenant option, VPC peering, customer pen-test |
| **Platinum** (Strategic) | $5M+ | + On-prem option, HSM integration, custom DPA |

→ Pre-define offerings. **不要 every customer 当 Platinum 谈, 每个 customer 也别当 Bronze**.

### 2.3 Customer 问 "do you have X?" 的 default response

不要直接 "yes/no". 用 framework:

> "Yes, we have X. **Here's the detail**:
>
> - **Implementation**: [how we do it]
> - **Scope**: [what's covered, what's not]
> - **Verification**: [how you can verify — SOC 2 section / cert / doc]
> - **Tradeoffs / limitations**: [honest about边界]
>
> Want to deep dive on any of these?"

→ Concrete + honest about limitations = trust.

### 2.4 不要轻易承诺的事

| Customer asks | 你的默认反应 |
|---|---|
| "On-prem deployment" | 「Possible at Platinum tier with 6-12 month customization. Cost implications. Want to discuss?」(不轻易 commit) |
| "Air-gapped, no internet" | 「Possible but radically reduces functionality. What's driving this?」(probe真因) |
| "Customer-hosted HSM (HYOK)" | 「Possible with throughput impact. Discuss latency budget?」(reveal cost) |
| "FedRAMP" | 「We're at [stage]. Realistic timeline is [N] months」(不夸大) |
| "Custom contract terms" | 「Yes, with legal review. 48h response on each request」(commit process, not outcome) |
| "100% data sovereignty in [country]" | 「Yes if we have a region there. Confirm with you within 1 week.」(确认能力) |

### 2.5 Inventory presentation 的 format

不要 50-page PDF. Use:

**1-page security overview** (executive view):

```
SECURITY OVERVIEW — [Your company]
──────────────────────────────────

Certifications:
  ✓ SOC 2 Type II (last audit: 2025-Q4)
  ✓ ISO 27001 (renewed 2025-Q2)
  ✓ HIPAA + BAA available
  ✓ GDPR DPA available
  
Encryption:
  ✓ AES-256 at rest, TLS 1.3 in transit
  ✓ Per-tenant DEK
  ✓ BYOK option (BYOK with AWS KMS / Azure Key Vault / GCP KMS)
  ✓ FIPS 140-2 Level 3 HSM-backed

Access:
  ✓ SSO via SAML/OIDC
  ✓ RBAC with customer-defined roles
  ✓ Just-in-time engineer access (auditable, 1h time-box)
  
Audit:
  ✓ Every API call logged
  ✓ Real-time stream to Splunk/Datadog/customer-chosen
  ✓ 7-year retention, tamper-evident
  
Data handling:
  ✓ Residency: US / EU / APAC (specific country on request)
  ✓ No customer data used for training (explicit DPA clause)
  ✓ Right to be forgotten (GDPR Article 17)
  ✓ Tenant isolation at DB level

Deployment options:
  Bronze: Multi-tenant SaaS (most customers)
  Silver: + BYOK + audit streaming
  Gold: + Single-tenant + VPC peering
  Platinum: + On-prem option + HSM integration

Incident response:
  24/7 on-call
  Breach notification within 24h
  $50M cyber insurance
  
Documents available (NDA-gated):
  - Full SOC 2 Type II report (100+ pages)
  - ISO 27001 certificate
  - Recent pen-test summary
  - Threat model
  - Architecture diagrams
  - Custom DPA / BAA templates
```

→ This 1-pager **opens 90% of IT conversations**. They get what they want to know. They request the deeper docs as needed.

---

## ⚙️ Problem 3: Compliance / Certifications Proof Package

**这是 IT 评审里最 mechanical 的部分 — 你必须有 standard package**.

### 3.1 Proof package 完整结构

```
ENTERPRISE SECURITY PACKAGE — [Customer Name]
─────────────────────────────────────────────
Date: [date]
NDA: Signed [date]
Contents:

1. SECURITY OVERVIEW (1-pager) — see above

2. CERTIFICATIONS
   a. SOC 2 Type II Report (full, ~100 pages)
   b. ISO 27001 Certificate + Statement of Applicability
   c. HIPAA + BAA Template (if requested)
   d. PCI DSS AOC (if applicable)
   e. Vendor due diligence questionnaire (CAIQ-CCM filled)

3. ARCHITECTURE
   a. System architecture diagram (high-level)
   b. Data flow diagram (where data goes)
   c. Threat model (STRIDE)
   d. Trust boundary documentation

4. ENCRYPTION DETAIL
   a. KMS architecture
   b. BYOK integration guide
   c. Key rotation policy

5. ACCESS CONTROL
   a. RBAC model
   b. SSO integration guide (SAML/OIDC)
   c. Just-in-time access policy

6. AUDIT / MONITORING
   a. Audit log schema
   b. SIEM integration guide
   c. Sample log output

7. DATA HANDLING
   a. Data residency map
   b. Retention policy
   c. Deletion process

8. INCIDENT RESPONSE
   a. IR runbook
   b. Breach notification process
   c. Insurance certificate

9. THIRD-PARTY TESTING
   a. Last pen-test summary (NDA)
   b. Bug bounty program (if any)
   c. External audit history

10. CONTRACT TEMPLATES
    a. Standard MSA
    b. Standard DPA (GDPR)
    c. Standard BAA (HIPAA)
    d. Cyber insurance certificate
```

**Customer-IT 这 10 个 doc**, 你的 IT review 通过率 80%+. **没这 10 个 doc**, 通过率 30%.

### 3.2 SOC 2 报告的内部 navigation

客户 IT 不会读完 100 页. 他们会 jump to:

| Section | 重要度 |
|---|---|
| Auditor opinion (page 1-2) | ⭐⭐⭐⭐⭐ Pass / qualified |
| Description of system | ⭐⭐⭐⭐ Architecture |
| Trust services criteria | ⭐⭐⭐⭐ What's tested |
| Common controls | ⭐⭐⭐ |
| Exceptions / qualifications | ⭐⭐⭐⭐⭐ Any findings? |
| Sub-service organizations | ⭐⭐⭐ Who else handles data |
| User entity considerations | ⭐⭐ What customer must do |

**你的 job**: pre-highlight relevant pages for customer. "Page 12 covers your specific use case; pages 47-49 are encryption controls; pages 78-80 are sub-service orgs (we use AWS)".

### 3.3 Common qualifications / exceptions 怎么 handle

SOC 2 报告几乎都有 finding. 客户会问 "什么 finding?"

**Standard response format**:

> "Our last SOC 2 had **N findings**:
>
> - **Finding 1**: [描述]. Remediated [date]. **Validation**: [link to remediation evidence].
> - **Finding 2**: ...
>
> Our remediation cadence is **<30 days for high, <60 days for med, <90 days for low**. Standard industry practice.
>
> Want to discuss any specific finding?"

→ Honest, structured. **Never hide findings** — IT 立刻发现.

### 3.4 GDPR DPA 关键条款 (你应该 default offer)

```
DATA PROCESSING AGREEMENT — Key Clauses
─────────────────────────────────────────

1. SCOPE
   - Processing only for purposes specified by Controller
   - No further processing without Controller authorization

2. SECURITY MEASURES
   - Article 32 GDPR technical & organizational measures
   - Specific: encryption at rest + in transit, access controls,
     audit logging, employee training

3. SUB-PROCESSORS
   - List of authorized sub-processors maintained
   - 30-day notice before adding new sub-processor
   - Controller right to object

4. DATA SUBJECT RIGHTS
   - Cooperation on access / rectification / deletion / portability
   - Standard 30-day response

5. PERSONAL DATA BREACH
   - Notify Controller within 72h of becoming aware
   - Provide info on breach scope + remediation

6. DATA RETURN / DELETION
   - At end of contract: return or delete all personal data
   - Certificate of deletion provided

7. AUDIT RIGHTS
   - Annual audit right with reasonable notice
   - SOC 2 report sufficient for most audit needs

8. INTERNATIONAL TRANSFERS
   - Standard Contractual Clauses (SCCs) where applicable
   - Specific transfer mechanisms documented

9. LIABILITY & INDEMNIFICATION
   - Standard liability cap
   - Indemnification for processor's GDPR violations
```

### 3.5 HIPAA BAA 关键条款 (PHI 场景)

```
BUSINESS ASSOCIATE AGREEMENT — Key Clauses
──────────────────────────────────────────

1. PERMITTED USES & DISCLOSURES
   - Only as permitted by HIPAA + contract

2. SAFEGUARDS
   - Administrative, physical, technical safeguards
   - Meet HIPAA Security Rule

3. REPORTING
   - Report security incidents
   - Notify breach within 60 days (HIPAA strict)

4. SUB-BAs
   - Sub-contractors must sign sub-BAAs

5. ACCESS / AMENDMENT / ACCOUNTING
   - Cooperate with individual rights

6. TERM & TERMINATION
   - Return or destroy PHI upon termination
   - If infeasible: extend BAA protection

7. CIVIL PENALTIES
   - Acknowledge HIPAA penalties
   - Mutual indemnification
```

### 3.6 当 customer 要 custom amendments

**Frequency**: ~50% enterprise customers want some customization.

**Standard categories**:

| Category | 通常 acceptable | 通常 push back |
|---|---|---|
| Data residency clause | ✓ if region exists | ✗ if no region |
| Audit rights | ✓ annual right with notice | ✗ unlimited audit |
| Breach notification SLA | ✓ 24h (default) | ✗ 1h (impossible) |
| Liability cap | ✓ negotiate to 2-3x ACV | ✗ unlimited |
| Source code escrow | ✓ for Platinum tier | ✗ for SMB |
| Indemnification | ✓ for IP / GDPR | ✗ for general liability |
| Pen-test rights | ✓ annual, customer's auditor | ✗ continuous |
| Data sovereignty | ✓ if region exists | ✗ if not |

**SLA on contract review**: 48h response on each amendment. Customer-faces speed = trust.

### 3.7 客户 IT 让你填的 CAIQ / CCM (Cloud Controls Matrix)

CSA (Cloud Security Alliance) 的 standard questionnaire. 200+ questions. **Customer 自己不写这个, 拿 CAIQ 让你填**.

**Strategy**:
- Pre-fill 一份 standard CAIQ as company library
- Update quarterly
- Customer 来 ask: 你 24h 内 return filled CAIQ
- **比 customer 自己 design 100 个 question 快 10x**

---

## ⚙️ Problem 4: Pilot / Sandbox / POC Approach — Build Trust Incrementally

**这是 IT 反复 review 完后, 你 unblock 的实际 mechanism**.

### 4.1 为什么 phased approach 比 big-bang 好

| Big bang | Phased |
|---|---|
| Need IT to OK full scope in one go | IT signs off small first |
| IT 没经验 = high risk perception | Pilot generates trust data |
| If issue → entire deal at risk | If issue → pilot stops, deal preserved |
| Negotiation 1 次, all-or-nothing | Negotiation 多次, low-stakes each |
| 6-month wait | 2-week pilot start |

### 4.2 3-tier rollout 标准结构

**Tier 1 (Week 1-2): Sandbox Pilot**

| Aspect | Detail |
|---|---|
| Data | Non-production, synthetic / scrubbed |
| Users | 2-5 from customer's team |
| Use case | Single, simple |
| Access | Full audit access to customer |
| Veto | Customer can kill at any time |
| Cost | Free (vendor absorbs) |
| Duration | 2 weeks max |
| Exit criteria | Functionality validated, security observable |

**Tier 2 (Week 3-6): Production with Limits**

| Aspect | Detail |
|---|---|
| Data | Production, single use case |
| Users | One team (10-50 users) |
| Use case | Single, specific |
| Access | Customer-controlled keys (BYOK) |
| Veto | Daily review, customer veto |
| Cost | Partial billing or discounted |
| Duration | 4 weeks |
| Exit criteria | SLA met, no security events |

**Tier 3 (Week 7-12+): Broader Production**

| Aspect | Detail |
|---|---|
| Data | Production, broader use cases |
| Users | Multiple teams |
| Use case | Multi-use case |
| Access | Standard |
| Veto | Quarterly review |
| Cost | Standard contract billing |
| Duration | Ongoing |
| Exit criteria | Full deployment, BAU |

### 4.3 Pilot setup 的 detailed steps

**Week -1 (Before pilot starts)**

- BAA / DPA / NDA signed
- Customer IT issued credentials
- Pilot scope doc signed by both
- Customer SIEM integration tested
- Customer kill-switch tested (pull access in <1 min)

**Week 1 (Pilot start)**

- Daily 15-min sync (you + customer IT + customer business)
- Daily metrics dashboard (success rate, latency, audit log)
- Friday: week-1 review

**Week 2 (Pilot continue)**

- Reduce sync to 3x/week
- Customer's pen-tester can test (if scope allows)
- Friday: pilot completion review

**Pilot completion criteria** (decision point):

| Pass | Issue | Fail |
|---|---|---|
| All functional tests pass | Some functional issues | Functionality broken |
| 0 security events | 1-2 minor (logged + remediated) | 1+ major |
| SLA met or close | SLA close miss | SLA significant miss |
| Customer happy | Customer concerns addressed | Customer unhappy |
| → Tier 2 | → Tier 1 extended 1-2 weeks | → Pilot ends |

### 4.4 IT veto 机制设计

**IT-veto principle**: IT can stop the deployment at any time, no questions asked.

**Mechanism**:

- Single command kill-switch (feature flag)
- Customer has this credential in their dashboard
- Slack channel for emergency pause
- 24h on-call escalation for IT to reach you

**Why veto matters**: IT 知道 they have nuclear option = they relax during normal operation.

### 4.5 跟 IT propose phased rollout 的 script

> "Maria, I want to propose how we onboard, in a way that **gives your team maximum control at each step**.
>
> **3 tiers, you veto at each transition**.
>
> **Tier 1 — Sandbox pilot (2 weeks)**:
> - Non-production data only
> - 2-3 of your team using it
> - **Full audit access** for your security team — every action logged + streamed to your SIEM
> - **You can kill it at any time** with a single command (we'll give you the credentials)
> - Free, zero billing
>
> **What you'd learn in Tier 1**:
> - How our system actually behaves in your environment
> - Whether our audit log integration works for your SIEM
> - Real performance / latency data
> - Your security team's specific concerns surfacing
>
> **Tier 2 — Production with limits (4 weeks)**:
> - Single use case, production data
> - **Customer-controlled encryption keys (BYOK)** — your KMS
> - **Daily security review** with your team
> - Limited team (10-50 users)
> - Discounted billing
>
> **Tier 3 — Broader rollout (week 7+)**:
> - Only with your explicit signoff at each expansion stage
> - **You define** the criteria for expanding
> - Quarterly security review thereafter
>
> **Your veto authority at every transition**. If Tier 1 doesn't satisfy you, **we stop**. If Tier 2 has any security concern, **we pause** and address before continuing.
>
> What I'd ask: **let's pilot, not contract**. Once Tier 1 + 2 work, we sign full contract for Tier 3 with confidence on both sides. **2-week start commitment is much smaller than 12-month all-in contract**.
>
> Can we explore this shape?"

### 4.6 当 IT 想加 customizations 到 pilot scope

IT 经常 ask:

- "Add this specific control during Tier 1"
- "Run on different infrastructure than your standard"
- "Use our identity provider, not yours"

**Default response**: yes when reasonable.

> "Yes, **adding [their request] to Tier 1 scope is doable**. Adds [time] to setup but no further. **Want me to update the pilot scope doc?**"

→ Accommodate increases trust. **Don't fight unless engineering says it's truly impossible**.

### 4.7 当 IT vetoes Tier 2 (concerns 发现)

**Scenario**: Tier 1 went OK. Tier 2 IT says "there's a finding, we're not OK to proceed".

**Response**:

> "I respect that. **Let me understand the finding**, then we'll address it before considering Tier 2 again.
>
> *(Listen)*
>
> OK so the finding is X. **Three paths forward**:
>
> (1) **We engineer a fix**: timeline [N weeks], we re-pilot Tier 1.5 with the fix, then evaluate Tier 2.
>
> (2) **Tier 2 with the issue mitigated by additional control**: [propose mitigation], you accept the additional control as compensating.
>
> (3) **Pause indefinitely**: we go back to drawing board, no Tier 2.
>
> **Which path do you prefer?**
>
> Whatever you pick, **I respect your call**. The veto is real."

→ Veto being real = IT relaxes long-term.

### 4.8 Pilot succeed → Contract phase

**Critical**: Don't lose momentum after Tier 2 success. Move to:

- Standard MSA signature
- DPA / BAA / amendments finalized
- Tier 3 expansion plan
- Ongoing security review cadence

But **honor IT process at each step**. Don't suddenly skip review because pilot worked.

---

## ⚙️ Problem 5: When IT vs Business Buyer Conflict — Navigate Without Alienating

**这是这道题最考 craft 的部分: 客户内部冲突, 你 caught in middle**.

### 5.1 IT vs Business 冲突的几种 archetype

| Archetype | Business 说 | IT 说 | 真因 |
|---|---|---|---|
| **Speed war** | "Need this in 2 weeks for board" | "Standard review is 3 months" | Process pace mismatch |
| **NIH war** | "We need vendor for this capability" | "We could build it" | Internal team protecting territory |
| **Risk war** | "Risk of NOT doing this is large" | "Risk of doing this is large" | Risk appetite difference |
| **Spend war** | "Strategic investment" | "Better spend on internal" | Budget allocation |
| **Politics war** | (Business sponsor going around IT) | "Need formal review" | Org politics |

### 5.2 不要选边站

**Bad move 1**: Side with Business → IT becomes adversary forever
**Bad move 2**: Side with IT → Business sponsor loses face, may withdraw championship
**Right move**: **Side with the customer's organization, not with either internal faction**

### 5.3 3-way working session 设计

**Goal**: 让 Business 和 IT 在你面前 disagree, 你 facilitate 共识.

**Setup**:

- 30-60 min, in person if possible
- Attendees: Business sponsor + IT lead + you + (optionally) AE + customer's neutral party (e.g., COO)
- **You set agenda**: 不让 either side hijack

**Agenda**:

```
3-WAY WORKING SESSION — [Customer Org]
──────────────────────────────────────

1. RESTATE GOALS (5 min)
   - What does Business want? (sponsor states)
   - What does IT need? (IT lead states)
   - Both stated, both heard

2. IDENTIFY CONSTRAINTS (10 min)
   - Time constraints (Business)
   - Risk constraints (IT)
   - Acknowledge BOTH are legitimate

3. PROPOSE PHASED APPROACH (15 min)
   - 3-tier rollout
   - IT veto at each transition
   - Business sees progress on Tier 1 fast
   - IT controls risk via veto

4. DEFINE SUCCESS / EXIT CRITERIA (10 min)
   - What does pilot success look like to Business?
   - What does pilot success look like to IT?
   - Agree on specific exit criteria for each Tier

5. AGREE ON CADENCE (10 min)
   - Daily Tier-1 sync
   - Weekly Tier-2 review
   - Quarterly Tier-3 review

6. ACTION ITEMS (5 min)
   - Who does what by when
   - Both signoff on action items
```

### 5.4 在 working session 中你的 role

| Role | Tactic |
|---|---|
| **Facilitator** | Don't take sides. Restate both positions fairly |
| **Translator** | "I think what Business is saying is X; what IT is saying is Y. Are they actually compatible?" |
| **Solution proposer** | Offer phased / scoped / governance solutions |
| **Truth speaker** | When sides are aligned, say so. When they're not, surface the gap |
| **Time keeper** | Don't let session derail |

**绝不**:
- 替任何一方 advocate
- Promise 任何一方 over the other's head
- "Pre-align with one party before session"

### 5.5 经典 sticky scenarios

**Scenario A: Business sponsor pressures you to ship before IT signoff**

Business sponsor (David, VP Sales): "Just go ahead, IT will catch up. We need this live by board meeting."

**Response (to David, ideally 1:1)**:

> "David, I hear the pressure. **I want this to work for you. Here's my view**:
>
> If we ship before IT signoff, **3 things happen**:
>
> (1) IT permanently distrusts us. Next time you need integration, **they'll block harder**, and you'll lose more time net.
>
> (2) If anything goes wrong post-deploy, **IT will say 'I told you so'** + escalate to CIO + your name gets attached to the bypass.
>
> (3) **No working partner integration ever shipped this way**. The vendors who try are not around 12 months later.
>
> **What I'll do instead**: I'll work IT's process **aggressively**. I'll be available daily. I'll pre-empt every question. **2 weeks of process is faster net than 6 months of recovery from a bypass**.
>
> Will you trust me to do this within IT's process?"

→ 不答应 bypass. 但**重塑 bypass 为更慢的路径**.

**Scenario B: IT permanently slow-walking, Business losing patience**

You sense IT is dragging because of internal politics, not real concerns.

**Response (to IT lead, 1:1)**:

> "Maria, **I want to ask honestly**: is there something blocking the review that I can address?
>
> I'm seeing 3 weeks of process for what's typically a 1-week review. **Is there a specific question I haven't answered? Or a stakeholder I haven't met? Or is the timing just not right for your team right now?**
>
> I'm not pressuring. **I'd rather understand the real situation than push**. If it's bandwidth on your side, that's fine — I just want to know what to expect.
>
> What would help unblock?"

→ Question 真因 with respect. **没 accusing**.

**Scenario C: IT和 Business 直接 fight, 你 stuck in middle**

David: "Maria, you're killing this deal."
Maria: "David, you're bypassing security."

**Response (immediately step in, calm)**:

> "Both of you, **let me reset the conversation**.
>
> David, **Maria's concern is legitimate** — security review exists because past mistakes hurt this org. **She's right to insist on review**.
>
> Maria, **David's urgency is legitimate** — the business case requires Q3 board demonstration. **He's right to push timeline**.
>
> **The disagreement is on pace, not on whether to do this**. So let me propose a way forward:
>
> [Propose 3-tier phased approach]
>
> Maria, you get veto at every step. David, you see Tier 1 progress fast.
>
> **Both your concerns are honored**. Can we proceed?"

→ Validate both, then propose path. **Don't side with either**.

### 5.6 客户 sponsor 跟你 ghost 的应对

**Scenario**: Business sponsor (David) stops responding to your emails after IT block. He may be feeling defeated.

**Response**: 主动 outreach with **value, not pressure**.

```
Subject: Quick update on [Customer] engagement

Hi David,

Quick update. I've been working with Maria's team on the security
review. Two things to share:

1. We've completed the security questionnaire (CAIQ) and submitted.
   Maria has 48h to respond.

2. I'm proposing a 3-tier phased pilot. Tier 1 is sandbox-only with
   non-prod data, 2 weeks, fully under Maria's veto. This addresses
   her concerns while still letting us start in 2 weeks.

I'll send the full proposal by EOD tomorrow. If it's helpful,
happy to set up a 30-min sync to walk through it — you, me,
optionally Maria.

[Your name]
```

→ Keep him in loop. **Don't make him feel abandoned because IT blocked**.

### 5.7 你和你公司 leadership 的 alignment

跟客户冲突 navigate 前, 必须 internal align:

- **Your CISO**: 关于 customer ask 中的安全 commitment 上限
- **Your EM**: 关于 engineering commitment (on-prem 可行吗?)
- **Your AE**: 关于 sales narrative 一致
- **Your CEO** (大单时): 关于 strategic decision

**Internal escalation 红线**: 跟客户承诺前你 leadership 必须知道. **Never ship a customer commit your leadership hasn't seen**.

---

# Part 3 · 把 5 个问题串起来看

这 5 个问题其实是 **IT block 应对的 5 个 layer**:

1. **理解真因** (Problem 1) — 4-layer 模型, 错配 remedy 是徒劳
2. **Security control inventory** (Problem 2) — 你必须 walk in with 完整 toolkit
3. **Compliance package** (Problem 3) — SOC 2 / ISO / BAA / DPA 的 mechanical 部分
4. **Phased pilot** (Problem 4) — IT veto + 渐进信任建立
5. **IT vs Business navigation** (Problem 5) — 不选边, facilitate

每一层做对, **IT 从 block-er 变 ally**, 续约时反而是你最稳的支持者. 每一层错, **IT 永久敌对, 这单加未来都失去**.

---

## 必问 clarifying questions

**1. What specifically blocked**

> "Did they say which control they're worried about — data residency, encryption, identity, audit logging? Specifics tell us which layer (L1-L6)."

**2. Who specifically blocked**

> "Is it CISO, CISO's deputy, security architect, compliance team? Each has different motivations and needs different framing."

**3. Past pattern**

> "Have they blocked other vendor integrations recently? What got unblocked? What didn't? This reveals real org behavior."

**4. Business sponsor pressure**

> "Is our business sponsor pushing back internally? Are they aligned on 'work through IT' or 'go around IT'?"

**5. Timing**

> "Hard block (can't proceed) or soft block (delayed pending review)? What's their stated process / timeline?"

**6. Internal scope**

> "What can I commit on (BYOK / on-prem / data residency)? What's my internal CISO's ceiling?"

---

## 5 步框架 (45-min answer 节奏)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify which layer + who + past pattern |
| 5-15 min | 1:1 with IT lead — listen mode (no defending) |
| 15-25 min | Compliance checklist response + 3-tier phased proposal |
| 25-35 min | IT veto governance + customer-controlled keys + audit log streaming |
| 35-45 min | 3-way working session w/ business + IT + you, joint plan |

---

## 简历专属 reframe

| 题 | Gao Xin 的经验 |
|---|---|
| IT security block | **ByteDance 内部跨 org compliance** 多次经历 |
| OJK regulator engagement | 印尼 BNPL 监管, 你直接 navigate 过 |
| Multi-market regulatory | 7 markets 各自 CISO + 合规 + 监管 |
| BYOK / customer-controlled encryption | Voice agent for regulated banking 你做过 |
| SOC 2 / ISO 27001 navigation | ByteDance enterprise security stack |
| 3-tier rollout | Indonesia refund tier scoping (同 framework) |
| Geopolitical sensitivity (L5) | TikTok PayLater 在 Indonesia / India / Brazil, 政治极敏感 |

**主动 quote**:

> "I've done this exact dance for the voice agent in Indonesia.
>
> **Setup**: We wanted to deploy AI voice agent to Bank X for debt collection. Bank X's CISO Maria blocked the integration. Her stated concern: 'data sovereignty + LLM unpredictability + TikTok China-link geopolitical'.
>
> **The actual layer (L6 + L5)**: Maria had been burned by a previous vendor 12 months ago — data exfiltration, regulatory fine, 90-day remediation. Plus OJK (Indonesia's financial regulator) had been particularly aggressive on Chinese-linked tech. **Two trauma layers compounded**.
>
> **The move that unstuck us**:
>
> **(1) 1:1 with Maria, no deck, just listen.** 8 minutes she talked, I took notes. I learned about the previous incident, about OJK's specific concerns, about her personal accountability.
>
> **(2) Targeted package**:
> - In-Indonesia data residency (we had a Jakarta region)
> - BYOK with their KMS, customer-owned encryption
> - Audit log streaming to their SIEM (Splunk)
> - Quarterly OJK-friendly compliance review
> - **TikTok corporate structure transparency** — board structure, data flow diagram showing no China-routing
>
> **(3) 3-tier rollout with Maria's veto at each step**:
> - Tier 1: sandbox, non-prod, 2 weeks, free
> - Tier 2: prod with single team, BYOK, daily security review
> - Tier 3: broader, IT signoff each expansion
>
> **(4) 3-way working session** with Maria + her CTO + her business head + my GM. 90 min. Joint agreement on what's acceptable.
>
> **Took 2 months instead of 2 weeks** but we got production approval — and **they trusted us afterward**, which paid back 10x over the project lifecycle. They became reference customer for our other Indonesia engagements.
>
> The lesson: **IT isn't an obstacle to ignore. IT is your most loyal long-term ally if you earn their trust on day 1**. The trust they give you on day 100 is worth more than any sales escalation."

---

## 5 follow-ups

**Q1**: "Sales VP wants to escalate over IT to CIO. Should I support?"

**A**: Almost always **don't**:
- "Escalation wins the battle, loses the war. **IT will block harder next time + every time after**."
- "Better: I run the security process. If after 30 days I've addressed concerns and **still** blocked, then we talk escalation. Right now we haven't done the work to deserve escalation."
- Coach the sales VP to be patient. If they're impatient enough to demand escalation now, **the relationship is wrong** — they don't trust your process.

**Q2**: "IT requires 6-month security review. Customer needs deploy in 6 weeks."

**A**: Decompose:
- "Full security review for full feature: 6 months. **We respect that**."
- "**Sandbox pilot with non-prod data**: 2 weeks through a lighter review (no production data, no production access). Customer can test integration patterns."
- "**Limited production scope** with strict controls: 6 weeks (with your continued review of bigger scope in parallel)."
- Let IT come up with **the smallest reviewable unit**. They appreciate the respect; they're more flexible than you think when you respect process.

**Q3**: "IT really doesn't want any 3rd party vendor. NIH attitude."

**A**: Convert NIH to ally:
- "Maria, your team's expertise in [their domain] is something we'd **lose** if we just dropped a vendor solution. **What if we structured this as a joint platform** — your team owns the data layer, we own the AI layer, you have full visibility and control. **We're partners, not vendor-customer.**"
- This is **building IT's career** not threatening it. They become invested in success.

**Q4**: "Pen-test report from us — IT's pen-tester rejects it, wants their own."

**A**: 绝对 yes:
- "Of course. Recommend [reputable firm] or your preferred — we'll pay for the engagement (within reason) and grant whatever access you need."
- "**Their pen-test gives them confidence we can't fake**. It also catches things we'd miss. Win-win."
- Honor the principle: **customer-paid 3rd party verification > our self-report**.

**Q5**: "Legal team says our standard contract isn't acceptable. Customizations required."

**A**:
- "Legal customizations are normal at enterprise — we have a contract review process. **Walk me through what specifically needs to change**?"
- Top common: data ownership, liability cap, audit rights, indemnification, source code escrow
- Don't promise outcomes but commit to **fast-tracking review** — **48h response on each request**
- Have your legal team pre-trained on standard customizations so most are pre-approved patterns.

---

## ❌ 易错点 (top 12)

1. **Argue with IT in group call** — public loss, IT face damage worse
2. **Escalate over IT to CIO** — long-term lose, IT permanent enemy
3. **Promise "we're secure"** without checklist — hand-wave, IT dismisses
4. **Skip their process** — bypass = burning bridge
5. **Blame sales VP to IT** — internal disloyalty signal
6. **NIH 当 obstinacy 误判** — miss ally opportunity
7. **No phased option** — all-or-nothing fails
8. **Over-promise on-prem / air-gap** — engineering can't deliver
9. **Don't read who blocked** — CISO vs analyst, different reactions
10. **Generic 50-page SOC 2 dump** — IT looks for 5 min, gives up
11. **No internal CISO align before commit** — your CISO overrides你
12. **客户 sponsor 失去 visibility** during IT block — sponsor becomes inactive

---

## ✅ 加分项 (top 12)

1. **4-layer concern model** (Surface / Control / NIH / Career + Geopolitical + Past trauma)
2. **1:1 first** before group call (Maria 1:1 listen-only)
3. **Listen-mode 50/50 on 1:1**
4. **BYOK customer-controlled encryption** specifically
5. **Audit log streaming to customer SIEM**
6. **SOC 2 + ISO 27001 + DPA + BAA** package ready
7. **3-tier rollout with IT veto** at each stage
8. **3-way working session** w/ sales + IT + you
9. **Joint platform framing** for NIH cases
10. **Customer-paid 3rd party pen-test**
11. **Quote Indonesia OJK regulatory experience** (real Gao Xin work)
12. **Per-role tailored communication** (CISO vs architect vs analyst)

---

## 一句话总结

> **IT 不是你的敌人, 是你最稳定的盟友 — 如果你赢得他的信任**.
>
> 90% IT block 不是 generic security paranoia, 是 **控制感缺失 + 流程被跳过 + 个人 risk 担忧 + 过去 trauma**. 你的 job 不是 "证明 we're secure", 是 **让 IT 感受到他在控制 process + 给他可量化的 checklist + 给他 veto 权 + 给他 audit visibility**.
>
> 一旦 IT 站你这边, sales 进度反而比绕过他更快. 这是 enterprise selling 的反直觉真理.

---

## Cheat Sheet (印 1 页)

```
IT 4-6 layer real concern:
  L1 Surface: data leaving network → checklist (SOC 2 / ISO / DPA)
  L2 Control: oversight → governance access + audit log
  L3 NIH: internal alternative → make ally + joint platform
  L4 Career: vendor failure = my fault → legal SLAs + insurance
  L5 Geopolitical: don't trust [country] → data residency
  L6 Past trauma: previously burned → trust building over time

5 步 flow:
  1. 1:1 with IT lead first (no deck, listen 50%)
  2. Identify which layer (L1-L6) via question + listening
  3. Customize compliance package (don't dump generic SOC 2)
  4. Propose 3-tier rollout with IT veto each stage
  5. 3-way working session sales + IT + you

Standard security checklist:
  ✓ AES-256 at rest, TLS 1.3 in transit
  ✓ Per-tenant DEK + customer KEK option (BYOK)
  ✓ SOC 2 Type II + ISO 27001
  ✓ DPA + BAA + custom amendments
  ✓ Audit log streaming to customer SIEM
  ✓ Customer-paid pen-test
  ✓ Data residency (per region)
  ✓ Just-in-time engineer access
  ✓ 24/7 on-call + 24h breach notification
  ✓ Cyber insurance certificate

3-tier rollout:
  T1 (2 wk): sandbox, non-prod, FREE, full audit access, IT veto
  T2 (4 wk): prod single team, BYOK, daily review, discounted
  T3 (12 wk+): broader, IT signoff each expansion, standard

IT-veto principle:
  Single kill-switch command (feature flag)
  Customer holds credential
  24h on-call escalation
  No question asked when invoked

3-way working session agenda:
  1. Restate goals (Business + IT)
  2. Identify constraints (both legitimate)
  3. Propose phased approach
  4. Define exit criteria
  5. Agree on cadence
  6. Action items

Per-role tailoring:
  CISO: Executive briefing + risk + insurance
  Architect: Architecture + threat model + control mapping
  Compliance: SOC 2 + ISO + recent audit
  Analyst: Log streaming + monitoring integration
  IT director: Governance + minimal team overhead

Compliance package (10 docs):
  1. 1-pager security overview
  2. SOC 2 Type II + ISO 27001 + relevant cert
  3. Architecture + threat model
  4. Encryption + BYOK detail
  5. Access control model
  6. Audit log schema + SIEM integration
  7. Data handling + residency
  8. IR runbook + insurance
  9. Pen-test summary
  10. Contract templates (MSA / DPA / BAA)

CAIQ / CCM:
  Pre-fill standard CAIQ as company library
  Update quarterly
  Return filled within 24h of customer ask

Don't lightly commit:
  On-prem deployment (6-12 month custom)
  Air-gapped (radically reduces function)
  FedRAMP (1-2 year process)
  Unlimited liability (never)
  Continuous pen-test (annual is industry)
  Sub-hour breach notification (impossible)

IT vs Business conflict:
  Don't side with either
  Facilitate 3-way working session
  Restate both as legitimate
  Propose phased with IT veto

Phrases:
  "I want to understand directly, not filtered"
  "What's your normal process — let's go through it"
  "Joint platform, you own data, we own AI"
  "You can pull the plug any time"
  "Veto at every transition"
  "I respect that decision"

红线:
  - Escalate over IT to CIO
  - Skip review process / bypass
  - Public group argument
  - Promise without checklist
  - Over-commit on-prem/air-gap
  - Ship before IT signoff
  - Generic SOC 2 dump
  - Argue with IT in group call
```
