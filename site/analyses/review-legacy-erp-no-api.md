## Case #4 · Legacy ERP Integration — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/legacy-erp-no-api.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`legacy-erp-no-api.html`](questions/legacy-erp-no-api.html)

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 🧠 核心心智模型 (1 sentence)

> **Legacy ERP 集成 = 60% 政治 40% 技术**. Plan A: piggyback BI team 已有 CSV → 1 周 ship 70% value. Plan B: phase ramp file drop → replica → CDC → BAPI write-back. **Velocity-of-value beats elegance**. 永远不要 build 一个新 API for them, 永远不要 screen-scrape unless desperate.

### 📚 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| ERP | Enterprise Resource Planning, 整合财务/采购/HR/生产/销售 | 任何 enterprise 部署都遇到 |
| SAP R/3 | 1992 SAP 经典版, on-prem | 制造业 / 法国客户经典 |
| S/4HANA | SAP 现代版, HANA in-memory | 新客户 |
| BAPI | Business API, SAP 官方接口函数 | write-back 唯一安全方式 |
| RFC | Remote Function Call (SAP) | BAPI 的底层协议 |
| IDoc | Intermediate Document (SAP) | 异步消息交换 |
| KNA1 | SAP 客户主表 (cryptic table name) | reference example |
| MARA | SAP 物料主表 | reference example |
| Adapter / Shim | 把 legacy 接口包装成 modern REST | FDE 必造的轮子 |
| Anti-corruption layer | schema mapping 隔离 legacy 命名 | 让你的 internal API stable |
| CDC | Change Data Capture, binlog 流 | 真需要 real-time read |
| Debezium | 开源 CDC, MySQL/Oracle/PG | Pattern 3 实现 |
| Oracle GoldenGate | Oracle 商业 CDC | Pattern 3 商业方案 |
| ESB | Enterprise Service Bus (TIBCO/IBM MQ) | 客户已有就 piggyback |
| RPA | Robotic Process Automation (UiPath) | screen scraping, 最后选 |
| Idempotency key | hash(payload), 防 double-write | write-back 必须 |
| Compensating transaction | rollback 步骤已知 | 任何 write 都要有 |

### 🎯 5 个核心 framework

**Framework 1**: 6 Integration Pattern Ladder
- When: 拿到 customer ERP 后选 v1 方案
- Algorithm: File drop (1w, 70% value, IT politics 极低) → Read replica (3-4w, 90% value, DBA 配合) → CDC (4-6w, 95% value, ops 复杂) → ESB (already have it?) → BAPI/RFC (2-3mo, write-back) → RPA (最后)
- Trade-off: 政治成本 vs delivery speed vs data freshness
- Tools: paramiko SFTP, oracledb python, Debezium + Kafka, pyrfc, Selenium (avoid)

**Framework 2**: Adapter / Shim Architecture (Strategy + Cache + CB)
- When: 任何 ERP 集成
- Algorithm: Strategy pattern (FileDropAdapter / ReplicaAdapter / BAPIAdapter) + Cache (Redis tiered TTL: 30s high / 5min mid / 1hr low volatility) + Schema mapping (anti-corruption: KNA1.KUNNR → customer_id) + Retry (Tenacity exponential) + Circuit breaker (5 failure → open 60s → half-open)
- Trade-off: 适配层成本 vs 内部 API 稳定性
- Tools: Tenacity, Redis, abc.ABC abstract, OR Hystrix port

**Framework 3**: Sync Pattern Matrix (Batch / Incremental / CDC / Reconcile)
- When: 决定数据流模式
- Algorithm:
  - Master data (daily fresh, 100K): full reload nightly + atomic swap
  - Master delta (hourly): incremental timestamp-based (注意 hard-delete bug)
  - Transactions (real-time, 10K/day): CDC + Kafka, idempotent upsert
  - Aggregate (month close, 1M): full batch
  - Reconciliation: row_count_check + sample_diff (1%) + daily_aggregate_check (e.g., total AR)
- Trade-off: freshness vs ops complexity
- Tools: Kafka, Debezium, scheduled job (Airflow), backpressure semaphore

**Framework 4**: 5 Failure Modes + Mitigation
- When: 永远生效
- Algorithm:
  - Schema drift: daily describe_table, removed = critical pause, added = warn auto-add
  - Data quality: pre-ingest validator (dup / null / encoding / non-numeric / mixed tz)
  - Idempotency: sha256(customer_id + fields) key, write_log dedupe
  - Compensating: read old → try update → verify → rollback if mismatch
  - Reconciliation 3-tier: count (0.1% diff alert) + sample 1000 deep diff + daily aggregate (AR total)
- Trade-off: 复杂度 vs production safety
- Tools: Great Expectations, pandera schema validator, write_log table, alert pipeline

**Framework 5**: IT Politics Map + Piggyback Strategy
- When: 项目第 0 周
- Algorithm:
  - Players: CIO (strategic) / IT Director (审批) / DBA (DB access) / BI team (盟友) / SAP analyst (schema 业务知识) / Vendor (co-opetition) / Business sponsor (需求)
  - Anti-pattern: 上来找 CIO → ARB → 3 个月没动
  - 正确: BI team 先 → 同样 CSV → 1 周流数据 → ROI 上 CIO → CIO 主动加速
  - Reciprocal value: 报告 IT 的 0.3% dup customer_id, ghost record, SAP schema 变更
- Trade-off: 慢但稳, 急功必撞墙
- Tools: 每周 IT sync, fortnight check-in IT Director, 月度 CIO update

### 🌳 关键决策树

```
What's the integration phase?
├── Phase 1 (Week 1-2): BI team 已 export CSV? → File drop, 70% value
├── Phase 2 (Month 2-3): 需 fresher? → Read replica, 30min lag
├── Phase 3 (Month 4-6): 需 real-time? → CDC Debezium
├── Phase 4 (Month 6+): 需 write? → Single transaction BAPI pilot 60d
└── Customer 已有 ESB? → Pattern 4 piggyback (中间任何 phase)

Write-back risk?
├── Direct DB? → ABSOLUTELY NO (破坏 SAP 内部 consistency)
├── BAPI/RFC/IDoc → OK with idempotency + compensating + 60d pilot
└── 1 transaction type only → 扩展前 < 0.01% error 60 天

Schema mapping budget?
├── SAP analyst available? → 1-2w map 20 tables
├── No analyst → reverse-engineer from CSV exports
├── Hire 3rd party SAP consultant? → 3-day $5K
└── Pay BI vendor for docs? → budget question
```

### ⚙️ Part 2 五个深度问题速查

**Problem 1: Integration Option Ladder**
- 核心解法:
  ```python
  # Pattern 1 File drop
  paramiko.SFTPClient → check .ready marker → pull csv → pandas validate schema + row count anomaly
  # Pattern 2 Replica
  oracledb.create_pool → query KNA1 WHERE last_update > :since → detect_freshness lag check
  # Pattern 3 CDC
  Kafka Consumer subscribe sap.kna1 → event['payload']['op'] c/u/d → commit
  # Pattern 5 BAPI
  pyrfc Connection → call('BAPI_CUSTOMER_GETDETAIL', CUSTOMERNO=) → BAPI_TRANSACTION_COMMIT WAIT=X
  ```
- Top 3 gotchas: 直接 DB write 破坏 consistency / 不 check .ready 读到 partial / RPA 当主方案
- Tools: paramiko, oracledb, Debezium, pyrfc, Confluent Kafka

**Problem 2: Adapter Layer**
- 核心解法:
  ```python
  class ERPAdapter(ABC): get_customer / list_orders / get_inventory
  ADAPTER_MAP[os.environ['ERP_TYPE']]  # file_drop / replica / bapi
  AdapterCache: redis tiered TTL (30s / 5min / 1hr)
  SAP_FIELD_MAP = {'KNA1.KUNNR': 'customer_id', ...}  # anti-corruption
  @retry(stop_after_attempt(3), wait_exponential(2,10))
  CircuitBreaker: 5 failure → OPEN 60s → HALF_OPEN
  ```
- Top 3 gotchas: 没 schema mapping (legacy 命名泄漏) / 没 circuit breaker (ERP down 拖死 platform) / cache TTL 不分级
- Tools: Tenacity, Redis, abc.ABC, scoped strategy

**Problem 3: Data Sync Patterns**
- 核心解法:
  ```python
  # batch full reload atomic
  write_df(df, 'customers_staging') → ALTER RENAME swap → DROP old
  # incremental timestamp
  state = db.get('last_pull_ts') → query since=state → upsert → set new max
  # CDC
  for event: op='d' → delete; op='c'/'u' → upsert; partition by PK; idempotent
  # reconciliation 3-tier
  row_count_check (0.1% threshold) + sample_diff(1000) + aggregate (AR sum)
  ```
- Top 3 gotchas: timestamp incremental 漏 hard-delete (周对账补) / CDC at-least-once → 必 idempotent / CDC ordering 跨 partition 错
- Tools: Airflow scheduled, Kafka, semaphore backpressure, snapshot+log bootstrap

**Problem 4: Failure Modes + Reconciliation**
- 核心解法:
  ```python
  # schema drift
  daily describe_table → removed → critical pause ingest; added → warn auto-add nullable
  # data quality
  validate dup / null / non-numeric / encoding / tz before ingest
  # idempotent write
  key = sha256(json({customer_id, fields}))
  if write_log.exists(key): return cached_result
  # compensating
  old = adapter.get(); try update; verify; if mismatch → rollback to old
  ```
- Top 3 gotchas: schema 变 silent break / write retry double-write / 没 reconcile mirror 飘
- Tools: Great Expectations, pandera, write_log table, ghost record detector

**Problem 5: Vendor + IT Politics**
- 核心解法:
  ```
  Map: CIO / IT Director / DBA / BI team (盟友!) / SAP analyst / vendor (co-opetition)
  Anti-pattern: CIO 直接谈 → ARB → 3mo 不动
  正确: BI team → CSV → ROI → CIO 主动
  Reciprocal: 报 IT 的 0.3% dup / ghost record / schema 变更 heads-up
  Vendor: transparent "we're complementary" / BAPI 官方接口 / 不 trash SAP 在 customer 面前
  ```
- Top 3 gotchas: 上来找 CIO / 忽略 BI team 已有 pattern / vendor 当对手而非 co-opetition
- Tools: weekly IT sync, fortnight Director check-in, monthly CIO update, IT-facing dashboard

### 🔥 Production gotchas (top 15)

1. 直接 build API for them → 6 月项目当 deployment 卖
2. Screen scraping 当主方案 → UI 改 = 全部 selector 失效
3. 忽略 IT politics → 技术方案再好也白搭
4. Read vs write 不分 → write 风险量级不同
5. 没 phasing 直接 CDC → IT block
6. MDM 问题忽略 → 客户内部数据不一致 = blocker
7. 没 quick win 6 月才交付 → 客户放弃
8. 没 schema drift detection → 客户改 schema silent 死
9. 没 idempotency on write → retry double-write
10. 不 reconcile → mirror 飘了不知道
11. 直接 DB write → 破坏 SAP 内部 consistency (触发器/lock)
12. CDC bootstrap 没 snapshot → 起服务漏数据
13. timestamp incremental 漏 hard-delete → mirror 永有孤儿
14. SAP analyst 时间没预算 → schema mapping 卡死
15. 不 piggyback BI team → 自己造轮子, 6 月没数据流

### 💬 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Legacy 集成 no-API | TikTok 7 markets | Singapore microservice / Indonesia 15yo monolith |
| File drop → CDC ramp | Voice agent | CSV 2w → Debezium 后续 |
| Political navigation | 7 markets | 跨 product/ops/regional 政治经验丰富 |
| Phase 1 visible value | Refund tier scoping | 70% throughput 0% risk |
| Adapter pattern | Internal Agent Platform | 抽象 + cache + retry |
| Schema drift | Voice agent | 上游 schema 漂移处理过 |
| Compensating transaction | Indonesia refund tier 1/2/3 | tier 设计就有 |
| Reciprocal value to IT | 你做 bug fix 上游 | data quality 反馈 |
| MDM 跨 market | 7 markets repayment status | 不一致 blocker 处理 |

### 🎤 面试现场 quotables (top 8)

1. "I'd never start with build-an-API-for-them — that's a 6-month project sold as a deployment"
2. "Velocity-of-value beats elegance — ship the ugly CSV adapter first, upgrade later"
3. "Piggyback what IT already does — BI team CSV exports is 70% of value at 0% political cost"
4. "Never direct DB write to SAP — IDoc/BAPI/RFC only with idempotency + compensating + 60-day pilot of 1 transaction type"
5. "I'd never screen-scrape unless IT explicitly blocks every other path — UI change kills you"
6. "Reciprocal value to IT — report their 0.3% duplicate customer IDs, they start inviting you to architecture reviews"
7. "TikTok 7 markets had a 15-year-old monolith with no API. CSV → replica → Debezium ramp, took 8 weeks to v1"
8. "Reconciliation 3-tier: count check + sample diff + daily aggregate. Without this, your mirror silently drifts"

### 🚨 红线 (top 10 anti-patterns)

1. 直接说 "build an API for them"
2. Screen-scraping (RPA) 当主方案
3. 忽略 IT politics
4. Read 跟 write 不区分 risk
5. 没 phasing 直接 CDC
6. 直接 DB write 到 SAP
7. 没 quick win 6 月才 deliver
8. 没 idempotency on write-back
9. 不 reconcile, mirror 飘
10. 上来找 CIO, 跳过 BI team

### 📊 数字 anchors (面试必记)

| Metric | Value | Source |
|---|---|---|
| 6 pattern ramp time | File drop 1w / Replica 3-4w / CDC 4-6w / ESB 4w / Vendor 2-3mo / RPA 1-2w | preference order |
| File drop value | 70% value at 0% political cost | quick win |
| Replica lag | 30 min typical | acceptable for most |
| CDC lag | 秒级 (Debezium binlog) | real-time |
| BAPI/RFC call latency | 秒级 per call | slow but transaction-safe |
| Write-back pilot | 60 days single transaction type, error < 0.01% | careful ramp |
| Cache TTL tiered | High volatility 30s / Mid 5 min / Low 1 hour | per data type |
| Circuit breaker | 5 failure threshold, 60s recovery | resilience |
| Retry exponential | min=2, max=10, attempt=3, transient only | Tenacity |
| Schema validation | daily describe_table, removed=critical, added=warn | drift detection |
| Reconciliation 3-tier | count (0.1% diff) + sample 1000 deep + aggregate (AR sum) | data integrity |
| Idempotency key | sha256(customer_id + fields) | dedupe |
| Compensating transaction | rollback step pre-defined | write safety |
| SAP analyst time | 1-2 wk for 20 table mapping | budget item |
| 3rd-party SAP consultant | 3-day $5K, schema map 20 tables | alt option |
| Customer write capacity | 10/sec typical BAPI | rate limit aware |
| Politics IT cadence | weekly DBA sync / fortnight Director / monthly CIO | rhythm |
| Reciprocal data quality finds | 0.3% dup customer ID, ghost records | goodwill currency |
| FDE preference order | File drop ⭐⭐⭐⭐⭐ / Replica ⭐⭐⭐⭐ / CDC ⭐⭐⭐ / ESB ⭐⭐⭐ / BAPI ⭐⭐ / RPA ⭐ | velocity beats elegance |

### 💡 SAP-Specific cheat (背诵)

| 概念 | 详情 |
|---|---|
| KNA1 | 客户主表 (KUNNR customer_id, NAME1, NAME2, ORT01 city, PSTLZ postal, LAND1 country) |
| MARA | 物料主表 |
| MARC | 物料 plant 数据 |
| MARD | 物料库存 |
| MSEG | 物料移动文档 |
| BAPI_CUSTOMER_GETDETAIL | 查客户 |
| BAPI_CUSTOMER_UPDATE | 更新客户 |
| BAPI_TRANSACTION_COMMIT WAIT=X | 提交 (必须 wait) |
| IDoc | Intermediate Document, 异步消息 |
| RFC | Remote Function Call 底层协议 |
| pyrfc | Python RFC 库, finicky |
| Anti-corruption layer | KNA1.KUNNR → customer_id, internal API stable |
