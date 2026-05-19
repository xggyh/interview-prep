## 题目（verbatim）

> "Integrate your AI platform with a **15-year-old on-premise ERP** system that **lacks an API layer**. What's your approach?"

**出处**：fde.academy 经典 deployment scenario。Salesforce / Palantir / Databricks 都问过。

**Round**：Case Study (45-60 min)

---

## 这道题在考什么

考你**真实企业部署经验**。Enterprise customer 90% 都有 legacy 系统。考点：

1. **You don't write your own ETL from scratch as plan A** —— 是不是真做过 enterprise deployment
2. **5 个 integration patterns 你知道几个** —— file drop, DB direct read, screen scraping, ESB, CDC
3. **Politics**：legacy ERP 通常 IT team 不让动. 怎么 navigate
4. **Risk staging**：read-only first, write much later

---

## 5 个 clarifying questions

**1. What ERP**

> "Which ERP — SAP R/3, Oracle EBS, JDE, custom Java? Each has different escape hatches."

**2. What data do we actually need**

> "Read-only or read-write? Real-time, hourly, or daily-fresh enough? Volumes — 1k records or 1M?"

**3. What can IT actually allow**

> "Has IT explicitly said no-API in writing? Or is it 'no one's built it'? Can they expose a **read-only DB replica**? VPN access? File drop on SFTP?"

**4. SLA / regulatory**

> "Is this regulated data (PII / financial / healthcare)? What's the data residency requirement?"

**5. Current pain**

> "How does the business currently get this data **for any other system**? There's almost always an existing CSV-export-to-shared-drive workflow we can piggyback on."

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-10 min | Clarify + understand current data flow inside customer |
| 10-25 min | 5 integration patterns, **rank by ETA-to-ship + risk** |
| 25-40 min | Recommend pattern + design data flow |
| 40-50 min | Failure modes + how to convince IT |
| 50-60 min | Phasing read-only → write |

---

## 5 个 integration patterns（必须知道）

| Pattern | 速度 | 风险 | 适用 |
|---|---|---|---|
| **1. Direct DB read (replica)** | Fast (real-time) | 低 if read-only replica | ERP 有 DB replica |
| **2. File drop (SFTP, CSV/XML)** | Slow (daily) | 极低 | IT 不让你直连任何东西 |
| **3. Change Data Capture (CDC)** | Real-time | 中 (需 DBA 配合) | DB binlog 能 expose |
| **4. ESB / message bus (TIBCO, MQ)** | Real-time | 中 (已有 bus) | 大企业有现成 ESB |
| **5. Screen scraping (RPA - UiPath/Automation Anywhere)** | Slow | 高 (脆弱 + 维护噩梦) | **绝对最后选项**，但有时 IT 只允许这个 |
| **6. Build a thin API wrapper** | Slow ramp-up | 中 | 你 own infra, 但需 IT signoff |

**STAFF/FDE 答**：永远**先试 pattern 1 + 2**（read-only DB + file drop），ramp 到 3 (CDC) for real-time，never 5 unless desperate。

---

## 我会这样答（sample monologue）

> "First, clarifying — *[问 5 questions]*. Assume **SAP R/3, read-only access needed, daily-fresh OK, IT says no direct API but open to discussion**.
>
> **My approach is 3-phase**:
>
> **Phase 1 (Week 1-2): File drop baseline + value demo**
> - SAP already exports nightly CSVs to a shared SFTP for the BI team — confirm this in week 1
> - We **piggyback on that existing export** — read CSV via batch ETL, ingest to our platform
> - Daily refresh, last-day-stale OK for v1
> - **Deliver visible value within 2 weeks**: dashboard / first AI insight that customer didn't have before
>
> **Phase 2 (Month 2-3): Pursue read-only DB replica**
> - With Phase 1 winning, **revisit IT conversation** with leverage: "you've seen the value, can we accelerate to near-real-time?"
> - Ask for **read-only replica of the SAP schema** — DBAs are usually willing to set up a 30-min-lag replica
> - We connect to replica directly, no impact on prod ERP
> - Latency drops from 24h to 30min
>
> **Phase 3 (Month 4-6): CDC for real-time use cases**
> - For specific use cases needing < 5min latency, set up CDC (e.g., Debezium reading SAP database log)
> - This requires deeper IT collaboration but **business case is now strong**
>
> **Pattern selection logic**:
> - File drop > API for politics: "we read what BI already reads" is unobjectionable
> - DB replica > API for capacity: APIs require IT to build; replica is "give us a connection string"
> - CDC > polling for real-time: scales to millions of records
> - **Never screen-scrape SAP** — UI changes break weekly, becomes unmaintainable
>
> **Failure modes**:
> - SAP schema undocumented — many tables, cryptic column names. **Get SAP analyst time** to map.
> - Soft-deletes vs hard-deletes — ERP has both, miss the wrong one and your data is stale.
> - Joins across modules — SAP HR + FI + MM modules don't link cleanly. Need domain-specific glue.
> - Timezone bugs — global ERP across regions, timestamps mixed.
>
> **Convincing IT** (the actual hard part):
> - **Start with they can already do** (read CSV they already produce)
> - **Show value before asking for more**
> - **Offer reciprocal value** to IT — e.g., we'll write back error reports that help their data quality
> - **Get their head-of-data on our side** before going to CIO
> - **Sign data processing agreement** (DPA) upfront — IT loves paperwork that protects them
>
> **Two scope risks**:
> - **Write-back to SAP is 10x harder than read** — promise read-only for v1, revisit write-back after 6mo
> - **Master data management problem** — if customer has 'who is a customer' inconsistent across SAP / Salesforce / Snowflake, **that's a 6-month MDM project before we can do anything useful**. Identify early."

---

## 简历专属 reframe

你的 **BNPL chatbot** + **voice agent** 都涉及 enterprise integration：

| Legacy ERP 题 | 你的经验 |
|---|---|
| Integrate without official API | BNPL chatbot 跨 ByteDance 内部多系统 |
| Read-only replica → CDC ramp | Voice agent 接 7 markets repayment system 你做过类似 |
| Politics with IT team | 你跨 product / ops / regional 7 markets, 政治经验丰富 |
| Phase 1 visible value | Refund tier scoping — "70% throughput at 0% risk" 同款 pattern |
| Don't screen-scrape | Voice agent ASR/TTS 真接生产 system, 不靠 UI hack |

**主动说**：

> "I've seen this exact shape at ByteDance Global Payment — we needed to integrate the voice agent with regional repayment systems that ranged from modern microservices in Singapore to **15-year-old monolith in one market**. We started with **CSV exports the BI team already had**, deployed v1 in 2 weeks, then later upgraded that one market to CDC via Debezium once we had political capital. The lesson I'd carry forward: **velocity-of-value beats elegance — ship the ugly thing first**."

→ 你有真做过 legacy integration 的 deployment 经验，比 90% candidate 强。

---

## 5 个 follow-ups

**Q1**: "IT 团队完全拒绝任何 DB access，只能 file drop。"
**A**: Fine. File drop scaling tactics:
- **Frequency**: negotiate from daily → hourly → 15-min. Each level needs different DB load justification.
- **Compression + diff**: only push changed rows (cdc-like behavior over files).
- **Acknowledgment loop**: SFTP file with `.lock` → `.ready` pattern so we don't read partial files.

15-min file drop covers 95% of "real-time" use cases.

**Q2**: "We need write-back to SAP. How risky?"
**A**: Very. SAP writes can corrupt ERP state, trigger downstream finance integrity issues, and CFO's career risk. Pattern:
- **Never direct DB write** — use SAP's official IDoc / RFC / BAPI interface, even if it's slower.
- **Stage in our system first, batch push** to ERP with reconciliation log.
- **Compensating transaction design** — every write has a known-rollback step.
- **Pilot with 1 specific transaction type** (e.g., purchase order status) for 60 days before expanding.

**Q3**: "SAP analyst time is unavailable to map schema. Stuck."
**A**: 3 options:
1. **Reverse-engineer from CSV exports** — what data shapes are already coming out? Use that as truth.
2. **Hire a 3rd-party SAP consultant** (3-day engagement, $5k) to map the 20 tables we care about.
3. **Pay client's BI vendor** (whoever maintains BI today) to give us their schema docs.

This is **a budget question, not a technical question**.

**Q4**: "Customer wants us to upgrade their ERP itself. Scope explosion?"
**A**: Hard no. 政治 + 技术 + 时间都不允许。Frame:
- "Upgrading SAP is a 2-year, $5M project that needs an SI partner. We're not that vendor. We can **make your old SAP look modern from the AI side** without touching SAP itself."
- Offer to **introduce them to an SI partner** for ERP modernization — get goodwill without owning that risk.

**Q5**: "How do you handle SAP schema changes mid-deployment?"
**A**:
- **Schema versioning**: tag each ingest with SAP schema version (e.g., date of last DDL change). Customer notifies us before changes.
- **Backward-compatible reads**: our ingestion code handles N and N-1 schemas, sunsets old after 90 days.
- **Schema diff alerts**: nightly cron diffs DB schema, alerts to FDE.

---

## ❌ 易错点

1. **直接说"build an API for them"** — 6 个月项目当 deployment 卖
2. **Screen-scraping 当主方案** — fragile + maintenance nightmare
3. **忽略 IT politics** — 技术方案再好，IT 不让也白搭
4. **Read 跟 write 不区分** — write-back 风险量级不同
5. **没 phasing** — 直接上 CDC，IT 直接 block
6. **MDM 问题忽略** — 客户内部数据不一致是部署 blocker
7. **没 quick win 概念** — 6 个月才 deliver value, 客户已经放弃

---

## ✅ 加分项

1. **Piggyback on existing BI export** — minimum IT effort, fast value
2. **5 patterns 排序 by velocity + risk** 主动 say out
3. **Phase 1 value before asking for more** — political capital strategy
4. **Compensating transaction for write-back** — show production safety mindset
5. **MDM identified as 6mo blocker** — surface real risk
6. **Refer SAP SI partner for upgrade** — politically savvy
7. **Quote your TikTok experience** — 15-year-old monolith integration

---

## Cheat Sheet

```
5 integration patterns ranked:
  1. File drop (existing BI export) - fastest, lowest risk
  2. Read-only DB replica - moderate
  3. CDC (Debezium / native log) - real-time read
  4. ESB (TIBCO/MQ) - if customer has bus
  5. Custom API wrapper - slow ramp-up
  X. Screen-scraping - NEVER unless desperate

3-phase rollout:
  Phase 1 (2 wk): File drop, daily, visible value
  Phase 2 (2 mo): Read-only replica, 30min lag
  Phase 3 (4 mo): CDC for real-time use cases

Politics tactics:
  - Piggyback on what IT already does
  - Show value before asking for more
  - Get DBA / data lead as ally first
  - Offer reciprocal value (data quality fix)
  - DPA / paperwork upfront

Write-back:
  - Never direct DB
  - IDoc / RFC / BAPI only
  - Stage + batch + reconciliation
  - Compensating transactions
  - Pilot 1 transaction type, 60 days

红线:
  - Don't screen-scrape
  - Don't promise ERP upgrade
  - Don't promise write-back v1
  - Don't ignore MDM if data inconsistent
```
