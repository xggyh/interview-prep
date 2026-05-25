## Q22 · 12 个零散零售数据源汇入预测模型的「摄取+转换」pipeline

> "Retail customer has **12 data sources** — POS systems (Oracle Retail + NCR), e-commerce (Shopify + Magento), inventory (SAP S/4HANA), warehouse (Manhattan WMS), supplier feeds (EDI 850/856/810), weather API, promo calendar (Smartsheet), foot traffic (Placer.ai), social signals (Brandwatch). They want to feed a demand forecasting model. **Design the ingest + transform pipeline.**"

**Round**: System Design (60 min)
**出处**: Exponent 2026 FDE · 公司: Palantir / Databricks / o9 Solutions · 行业: retail / CPG
**约束**: 12 heterogeneous sources / multiple SLAs (real-time POS vs daily EDI) / schema drift / data quality / late-arriving data / forecasting freshness (daily forecast horizon 90 days)

---

## 这道题在考什么

不是考你会不会写 Airflow DAG, 是考你**在 12 个 schema 完全不同的来源面前怎么不崩**:

1. **Per-source connector pattern** — 不能写一个 generic ingester, 每个 source 都需要专属的 connector + auth + error handling
2. **Schema registry 是命门** — 12 个 source 各自演化, 没有 registry + contract test 一周就乱
3. **DLQ 在 ingestion 必须有** — bad row 不能 block 整 batch, 要 isolation
4. **Idempotency + dedupe** — POS 偶尔会重复发送一笔交易, 要做 exactly-once 语义
5. **Late-arriving data** — supplier EDI 856 可能 3 天后到, watermark + reprocessing 必须支持
6. **Transform 在哪做** — ELT (dbt in warehouse) vs ETL (Spark) — 这道题考你的 modern-stack 直觉
7. **数据质量验证** — Great Expectations / Soda / dbt tests 必备, 否则 garbage in → forecasting model 崩
8. **菜鸟答案失败点**: "我会用 Airflow + Spark, 写 12 个 DAG, 跑出来塞 Snowflake" — 太浅. 没回答 schema drift / DLQ / late arrival / 端到端可观察性 / forecasting model 关心 freshness 这些问题.

---

## 必问 clarifying questions

1. **Forecasting freshness需求**: 每日跑一次 forecast 用 T-1 数据 还是 hourly intraday refresh? 决定 batch vs streaming
2. **Data volume per source**: POS 一天 5M 交易 vs Smartsheet promo 100 entries — 决定 connector strategy
3. **Failure tolerance**: 一个 source 挂了能跑 forecast 吗? 还是 hard dependency?
4. **Historical backfill**: 只跑增量还是要 3 年历史? 决定 backfill 投资
5. **Owner per source**: 谁的 SLA / oncall? 影响 contract test 谁来维护
6. **Data residency**: 数据要在哪 region 落? GDPR / state law constraints?
7. **Existing warehouse**: 已经有 Snowflake / Databricks / BigQuery 吗? 决定 transform layer 选型
8. **Schema change 频率**: 哪些 source 季度 schema 变更 (Shopify API 频繁), 哪些不变 (EDI 30 年没改过)? 决定 registry 投入

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|------|------|------|
| 1 | Clarify | 5 min | freshness / volume / owner / 现有 stack | "三件事先锁: forecast 是 daily 还是 hourly, 12 source 各自 SLA, 现成是不是 Snowflake" |
| 2 | Source matrix | 5 min | 把 12 source 按 (volume × freshness × stability) 分类 | "我把 12 个 source 画个 2x2, 决定 connector pattern" |
| 3 | Architecture (medallion) | 10 min | Bronze → Silver → Gold + orchestration + registry | "我用 medallion: 原始入 Bronze, 清洗入 Silver, 业务模型入 Gold" |
| 4 | Ingestion deep dive | 10 min | Per-source pattern (CDC/SFTP/API/EDI/streaming) | "每 source 一个 connector module, 走标准化 contract" |
| 5 | Transform layer (dbt) | 10 min | Models + tests + lineage | "dbt 在 warehouse 跑 SQL transform + tests, 不在 Spark" |
| 6 | Data quality + DLQ | 8 min | Great Expectations + DLQ + alerting | "每 source 出 Bronze 前过 expectations, 失败进 DLQ" |
| 7 | Late + idempotent | 6 min | Watermark + reprocess + dedupe | "Watermark 4 天 grace, 之后 reprocess. Idempotent 用 merge key" |
| 8 | Trade-offs + close | 6 min | Airflow vs Dagster vs Prefect / Spark vs dbt / 监控 | "Dagster 我推荐 — asset-based + 12 source 异构最适合" |

---

## 端到端架构图 (ASCII)

```
┌────────────────────────── 12 Data Sources (heterogeneous) ─────────────────────────────────┐
│                                                                                            │
│  ┌─POS────────────┐  ┌─E-com──────┐  ┌─ERP──────────┐  ┌─WMS─────────┐  ┌─Supplier────┐    │
│  │ Oracle Retail  │  │ Shopify    │  │ SAP S/4HANA  │  │ Manhattan   │  │ EDI 850/856 │    │
│  │ NCR Aloha      │  │ Magento    │  │ (HANA tables)│  │ WMS         │  │ /810 (AS2)  │    │
│  │ ~5M txn/day    │  │ webhook    │  │ CDC          │  │ DB extract  │  │ daily 3am   │    │
│  └────┬───────────┘  └─────┬──────┘  └──────┬───────┘  └──────┬──────┘  └──────┬──────┘    │
│       │                    │                │                  │                │           │
│  ┌─External APIs────────────────────┐  ┌─Spreadsheets──┐  ┌─Behavioral──────────────┐      │
│  │ Weather (NOAA / OpenWeather)     │  │ Smartsheet    │  │ Placer.ai foot traffic  │      │
│  │ Brandwatch social signals        │  │ promo cal     │  │ daily report files      │      │
│  └──────────────┬───────────────────┘  └────┬──────────┘  └─────┬────────────────────┘     │
│                 │                            │                    │                          │
└─────────────────┼────────────────────────────┼────────────────────┼──────────────────────────┘
                  ▼                            ▼                    ▼
   ┌────────────────────────────────────────────────────────────────────────────────────┐
   │                  Per-source Connector Layer (Dagster assets)                       │
   │                                                                                    │
   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐  │
   │   │POS connector│  │Shopify webhk│  │SAP CDC      │  │EDI/AS2 parse│  │Weather  │  │
   │   │(JDBC + CDC) │  │Lambda → SQS │  │(Qlik / Fivt)│  │             │  │API poll │  │
   │   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────┬────┘  │
   │          │                │                │                │              │       │
   │   each emits raw event to its own S3 bronze partition  (no schema enforced yet)    │
   └──────────┼────────────────┼────────────────┼────────────────┼──────────────┼───────┘
              ▼                ▼                ▼                ▼              ▼
   ┌────────────────────────────────────────────────────────────────────────────────────┐
   │  Schema Registry (Confluent Schema Registry or AWS Glue Registry)                  │
   │  - Avro / Parquet schemas per source, versioned                                    │
   │  - Producer registers, consumer validates on read                                  │
   │  - PR-based schema review w/ contract test                                         │
   └────────────────────────────────────────────────────────────────────────────────────┘
              │
              ▼
   ┌────────────────────────────────────────────────────────────────────────────────────┐
   │             Bronze Layer — Raw Append (S3 + Iceberg / Delta)                       │
   │  - schema-on-read, partitioned by source/dt/hr                                     │
   │  - WORM 90d, then S3 Glacier 7 yr                                                  │
   │  - Great Expectations basic checks (not-null PK, type assert)                      │
   │  - Failures → DLQ (S3 bucket + alert)                                              │
   └────────────────────────────────────────────────────────────────────────────────────┘
              │
              ▼
   ┌────────────────────────────────────────────────────────────────────────────────────┐
   │             Silver Layer — Cleaned + Conformed (Snowflake or Databricks)           │
   │  - dbt models: dedup, type cast, conform business keys                             │
   │  - dbt tests: unique, not_null, accepted_values, relationships                     │
   │  - SCD2 for dimension tables (store, sku, customer)                                │
   │  - Late-arriving handling via merge + watermark                                    │
   └────────────────────────────────────────────────────────────────────────────────────┘
              │
              ▼
   ┌────────────────────────────────────────────────────────────────────────────────────┐
   │             Gold Layer — Forecasting-ready (Snowflake materialized)                │
   │  - Daily aggregates: sales by sku × store × dt                                     │
   │  - Feature tables: weather joined, promo joined, foot traffic joined               │
   │  - Train view (history) + Predict view (incremental, last 90d)                    │
   │  - Surfaced via Feature Store (Tecton / Feast) for model serving                   │
   └────────────────────────────────────────────────────────────────────────────────────┘
              │
              ▼
   ┌────────────────────────────────────────────────────────────────────────────────────┐
   │     Forecasting Model Trainer / Server (Databricks ML / Vertex AI / SageMaker)     │
   │     - daily retrain on Gold features → forecast 90-day horizon per sku × store     │
   │     - feedback loop: actual vs forecast → drift dashboard                          │
   └────────────────────────────────────────────────────────────────────────────────────┘

  Cross-cutting:
  ├─ Orchestration: Dagster (asset-based, 12 source = 12 software-defined assets)
  ├─ Observability: Dagster UI + OpenLineage → Marquez + Datadog
  ├─ Lineage: OpenLineage emit on every asset materialization
  ├─ Secrets: HashiCorp Vault per source (Oracle JDBC creds, Shopify token, EDI AS2 keys)
  └─ DLQ: separate S3 bucket per source, daily review by data team on-call
```

---

## 详细设计 (60-min walkthrough)

### Phase 1: Clarify + KPI (5 min)

开口锁:
- "Forecasting model retrain 频率: daily? hourly? 不同答案设计差别巨大"
- "12 source 哪些是 hard dependency (没它 forecast 跑不了), 哪些是 nice-to-have (weather)"
- "Snowflake / Databricks / BigQuery 哪个是 ground truth warehouse"

我假设: daily retrain (drone 大客户多数 nightly batch forecast), POS + SAP 是 hard dependency, Snowflake on AWS 是 warehouse.

KPI:
- **Freshness**: T-1 data available by 6am for 8am business hour
- **Completeness**: 99.5% rows landed (some sources flaky)
- **Quality**: 0 critical test failures (dbt test, severity = error), < 5 warnings per day
- **DLQ size**: < 0.1% of daily volume
- **Lineage coverage**: 100% production assets in OpenLineage graph

### Phase 2: Source matrix (5 min)

不要 12 个 source 一个一个讲, 画个矩阵让面试官看到你的分类思维:

| Source | Volume | Freshness need | Stability | Mode | Connector |
|---|---|---|---|---|---|
| Oracle Retail POS | High (5M/d) | Hourly | Stable | CDC | Oracle GoldenGate / Qlik Replicate |
| NCR Aloha POS | High (2M/d) | Hourly | Legacy | DB Extract | JDBC nightly + delta |
| Shopify | Med (500K/d) | Real-time | API stable | Webhook + REST poll | Lambda → SQS |
| Magento | Med (200K/d) | Real-time | Self-hosted | DB read replica | Read replica + CDC |
| SAP S/4HANA | High (1M/d) | Daily | Stable, ABAP | CDS Views or Qlik | Fivetran or Qlik Replicate |
| Manhattan WMS | Med (50K/d) | Hourly | Stable | DB extract | Custom ODBC |
| EDI 850/856/810 | Low (5K/d) | Daily | Standardized | AS2 + EDI parse | EDI parser library (Edifecs / SPS) |
| Weather API | Low (1K calls/d) | Hourly | Public API | REST poll | Lambda + scheduled |
| Smartsheet promo | Tiny (100/wk) | Daily | Manual entry | API poll | Daily Lambda |
| Placer.ai foot traffic | Low (1K files/wk) | Daily | File drop | SFTP | SFTP pickup |
| Brandwatch | Low (10K/d) | Daily | API | REST poll | Daily Lambda |
| Internal promo (Smartsheet alternative) | Tiny | Weekly | Manual | Excel upload | Manual + dbt seed |

矩阵教你 4 个 connector pattern:
- **CDC/streaming**: Oracle Retail, SAP, Magento (有 transactional log)
- **Webhook + DLQ**: Shopify, NCR (event push)
- **API poll**: Weather, Smartsheet, Brandwatch (REST, rate-limited)
- **File drop**: EDI (AS2), Placer.ai (SFTP)

### Phase 3: Medallion Architecture (10 min)

为什么 medallion (Bronze/Silver/Gold) 是工业标准:

**Bronze (raw)**:
- 任何 source 进来不动 schema, 只加 metadata (`_ingested_at`, `_source`, `_batch_id`)
- 用 Apache Iceberg 或 Delta Lake on S3 (而不是 Snowflake) 因为 schema-on-read 灵活, 失败也能 reprocess
- 保留 90 天 hot + 7 年 Glacier (合规 + ML 训练历史)

**Silver (cleaned + conformed)**:
- dbt models on Snowflake/Databricks 跑 SQL transform
- 标准化业务键 (sku, store_id, customer_id 跨 source 对齐)
- SCD2 维表 (store 信息每天可能变, 保历史)
- 跑 dbt tests, 失败 fail loud

**Gold (business-ready)**:
- Forecasting-specific aggregates: 一天一行 per sku × store, 含 sales / inventory / promo flag / weather
- Materialized + clustered (Snowflake clustering on sku, store, dt)
- 给 Feature Store / 直接给 model trainer

为什么不是 EL 直接到 Gold: bronze 让你 reprocess 不用回 source (source 可能没历史保留), silver 让 dbt test 早 fail 而不是 forecast 时才挂.

为什么不是 ETL (用 Spark transform): 现代 stack 趋势 ELT — load raw to warehouse, transform with SQL. Snowflake compute 比 EMR Spark 更便宜 + 不用维护集群. Spark 留给 ML training / large file processing (parquet conversion).

### Phase 4: Per-source ingestion deep dive (10 min)

选 3 个最难的讲, 不要 12 个都讲完.

**4.1 Oracle Retail POS (high volume CDC)**

```
Oracle Retail Production DB
  └─ Oracle GoldenGate or Qlik Replicate
      └─ Reads redo logs (no impact on source DB)
      └─ Streams CDC events to Kinesis
          └─ Lambda consumer
              ├─ Validate against Avro schema (Confluent Schema Registry)
              ├─ Enrich with metadata (_ingested_at, _source=oracle-pos)
              └─ Write to S3 Bronze (Iceberg table, partitioned by dt/hr)
```

关键考虑:
- **Redo log read**: 不能 SELECT * on POS DB (会拖死收银台). GoldenGate / Qlik 读 transaction log, 透明.
- **Backpressure**: Kinesis 限流 1MB/shard/sec, 5M txn/day = ~60 TPS avg, peak 500 TPS (12 noon / 6pm), 我用 32 shards
- **Schema drift**: Oracle DBA 加新列时 schema registry 检测, schema review PR 触发, 默认 backward-compatible (新列必须 nullable + default)
- **CDC ordering**: 同一行的更新必须有序. partition key = `${table}:${primary_key}`, 保证 same key 同一 shard.

**4.2 EDI 856 Advance Ship Notice (AS2 file drop)**

EDI 是 retail 最 legacy 也最稳的协议:

```
Supplier sends 856 via AS2 (HTTPS POST with S/MIME signing)
  └─ Our AS2 gateway (Cleo Harmony / OpenAS2) receives
      └─ Verify signature + decompress
      └─ Write raw .edi file to S3 Bronze (no parse yet)
      └─ Trigger Lambda
          └─ Parse with python-edi-835 library or Edifecs
          └─ Transform to canonical JSON: { po_number, asn_date, ship_lines: [...] }
          └─ Write to Bronze Iceberg table
          └─ Send AS2 acknowledgement (997 functional ack) back to supplier
```

关键:
- **AS2 ack 是 SLA**: 没回 997 supplier 会重发 / 客服来电. 60-second 内必须 ack
- **EDI is fragile**: supplier 偶尔发坏文件 (encoding 错, segment 顺序错), 进 DLQ + 24h SLA 让 ops 手动修
- **PO matching**: 856 关联 850 (purchase order), 需要 join. silver 层做.

**4.3 Shopify webhook**

```
Shopify Order Created webhook
  └─ API Gateway → Lambda
      ├─ Verify HMAC signature (X-Shopify-Hmac-Sha256)
      ├─ Idempotency check (X-Shopify-Webhook-Id stored in DynamoDB 7 days)
      ├─ Schema validate (Shopify changes minor API every quarter, schema registry catches)
      └─ Push to SQS (DLQ enabled after 3 retries)
          └─ Bronze writer Lambda
              └─ Write to S3 Bronze partition
```

关键:
- **Webhook 重试**: Shopify retry 19 次跨 48h. Idempotency 必须做.
- **Webhook 不保证顺序**: order_updated 可能先于 order_created 到. 写时不依赖 ordering, silver 层用 max(updated_at) merge.
- **Webhook 丢失**: 1% 概率丢 webhook. backup: 每天跑一次 Shopify REST API reconcile, diff webhook 来的 vs API 查到的.

### Phase 5: Transform layer (dbt) (10 min)

为什么 dbt > Spark / Airflow PythonOperator:
- 团队 SQL 比 Python 普及
- dbt tests + docs + lineage 一个 framework 给齐
- Version control + PR review for SQL 跟 code 一样

dbt project 结构:
```
models/
  staging/                    -- 1:1 with bronze
    stg_pos__oracle_orders.sql
    stg_ecom__shopify_orders.sql
    stg_erp__sap_inventory.sql
    ...
  intermediate/               -- joins, conformed
    int_orders_unified.sql    -- POS + ecom unioned, with source tag
    int_inventory_current.sql -- WMS + ERP reconciled
  marts/                      -- gold
    fct_daily_sales_by_sku_store.sql
    dim_store_scd2.sql
    dim_sku.sql
    forecast_features.sql     -- 给 ML model
tests/
  generic/                    -- custom assertions
    test_revenue_reconciliation.sql  -- POS revenue ≈ Shopify revenue, with tolerance
  singular/
    test_no_orphan_orders.sql
```

dbt test 必备 5 类:
1. `unique` on primary key
2. `not_null` on required columns
3. `accepted_values` on enums (e.g., order_status in ['paid', 'refunded', 'pending'])
4. `relationships` (every order references a valid store)
5. Custom reconciliation tests (POS total ≈ SAP revenue posting, within 1% threshold)

dbt run cadence:
- Staging: 每小时 (incremental)
- Intermediate: 每 4 小时
- Marts: nightly 1am
- Forecasting features: 1am (依赖 marts), 4am cutoff for 6am SLA

### Phase 6: Data quality + DLQ + alerting (8 min)

**Great Expectations checkpoints**:

每个 bronze 写入前过 expectations:

```python
# expectations/oracle_pos_orders.json
{
  "expectations": [
    {"type": "expect_column_to_exist", "column": "order_id"},
    {"type": "expect_column_values_to_not_be_null", "column": "order_id"},
    {"type": "expect_column_values_to_be_unique", "column": "order_id"},
    {"type": "expect_column_values_to_be_between", "column": "total_amount", "min_value": 0, "max_value": 100000},
    {"type": "expect_column_value_lengths_to_be_between", "column": "store_id", "min_value": 4, "max_value": 4},
    {"type": "expect_table_row_count_to_be_between", "min_value": 1000, "max_value": 1000000}
  ]
}
```

失败处理:
- **Soft failures** (warning level): single row 失败 → 该 row 进 DLQ S3 bucket, 其余 batch 继续
- **Hard failures** (error level): 整 batch 失败率 > 5% → 整 batch 进 DLQ + PagerDuty alert
- **Schema failures**: schema 不匹配 → block ingestion, PagerDuty + Slack 给 data eng oncall

DLQ structure:
```
s3://retail-dlq/
  ├─ oracle-pos/dt=2026-05-25/
  │   ├─ schema_violation/      -- bad schema
  │   ├─ quality_violation/     -- ge expectation failed
  │   └─ ingest_error/          -- connector exception
  └─ shopify/dt=2026-05-25/...
```

Daily DLQ review at 9am: data engineer on-call 看每个 source 的 DLQ size, decide reprocess / skip / escalate to source owner.

**Anomaly detection**:
- Volume anomaly: row count today vs yesterday |Δ| > 30% → alert (POS 周末高峰 / 节日 全部要在白名单里)
- Quality anomaly: dbt test failure rate 上升

### Phase 7: Late-arriving + idempotency (6 min)

**Watermark + reprocess**:

Forecasting 跑在 t = today 6am, 用 t - 1 day 数据. 但 EDI 856 可能 t+3 才到 (supplier 慢). 怎么办?

```python
# forecast_features.sql (dbt incremental model)
{{ config(materialized='incremental', unique_key=['sku', 'store_id', 'dt']) }}

WITH source_data AS (
  SELECT ... FROM {{ ref('int_orders_unified') }}
  WHERE dt >= DATEADD('day', -7, CURRENT_DATE)  -- 7 day late window
)
SELECT ... FROM source_data
{% if is_incremental() %}
  -- Re-merge last 7 days to catch late arrivals
{% endif %}
```

策略: 每天 reprocess 过去 7 天的 gold features. Forecasting model 设计上要接受 features 会更新 (用 unique key merge).

Watermark 监控: 每 source 维护 `data_freshness` 表, 每次 ingest 更新 `latest_event_ts`. Dashboard 显示哪个 source 已 N 小时无新数据.

**Idempotency**:
- 每条 event 必有 source-side ID (Shopify order_id, Oracle txn_id, EDI 856 控制号)
- Bronze 写入用 Iceberg merge / Delta merge with `_source_id` unique key
- Webhook 层用 7 天 DynamoDB idempotency cache (防止 source 重发)

**Dedup at silver**:
- POS POS 跨 Oracle / NCR 偶尔会同一笔 ring 两次 (人为操作错误). dbt model `int_orders_dedup` 按 (store_id, terminal_id, ring_ts ±5 sec, total_amount) 模糊去重, 取 last_modified 最新一笔.

### Phase 8: Trade-offs + alternatives (6 min)

**Decision 8.1 — Orchestrator: Airflow vs Dagster vs Prefect**

| 维度 | Airflow | Dagster | Prefect |
|---|---|---|---|
| Asset-based | No (task-based) | Yes (asset-based) | Yes (since v2) |
| Schema/types | 弱 | 强 (pydantic) | 中 |
| UI | 较老 | 模块化 | 现代 |
| 12 source 异构 | DAG 各写各的 | 12 个 source = 12 assets, 自动 lineage | 类似 Dagster |
| 生态 | 最大 | 在追 | 较小 |
| 我选 | — | **Dagster** | — |

理由: 12 异构 source asset-based 比 task-based 自然. Dagster 的 asset 描述把 "这条数据来自 source X, 在 Bronze Iceberg 表 Y" 写在代码里, lineage 自动. Airflow 你得自己拼 lineage.

**Decision 8.2 — Warehouse: Snowflake vs Databricks vs BigQuery**

| 选项 | Pros | Cons |
|---|---|---|
| Snowflake | 12 source 接 connector 多, SQL UX 好, dbt-native | 贵 (compute credit), Iceberg 支持后来 |
| Databricks | Lakehouse, ML 好, Iceberg/Delta 强 | 学习成本 |
| BigQuery | 便宜 (按扫描), ML 好 | AWS 客户少用 |

我选 **Snowflake** (assuming 客户已经有). Databricks 若客户做大量 ML training 我推. BigQuery 仅 GCP 客户.

**Decision 8.3 — Iceberg vs Delta vs Hudi for Bronze**

| Format | Pros | Cons |
|---|---|---|
| Iceberg | Open, vendor-neutral, 多 engine 读 | 较新, 工具较少 |
| Delta | Databricks-blessed, 性能好 | Lock-in Databricks 生态 |
| Hudi | Streaming-first | 复杂 |

我选 **Iceberg** — Snowflake / Databricks / Trino / Spark 都读, 客户未来换 warehouse 不绑死.

**Decision 8.4 — CDC: GoldenGate vs Qlik vs Fivetran vs Debezium**

| 选项 | 适用 | 价格 |
|---|---|---|
| Oracle GoldenGate | Oracle source | 贵 ($100K+/year) |
| Qlik Replicate | 多 source, enterprise | 中 |
| Fivetran | SaaS, easy, but cost 按行 | 量大很贵 |
| Debezium | OSS, Kafka Connect | 免费, 但运维成本 |

混合: Oracle 用 GoldenGate (客户可能已经有 license), Magento Postgres 用 Debezium (自己跑), SAP 用 Fivetran connector (SAP 接入复杂, SaaS 省事).

---

## 关键决策点 (with rationale)

1. **Medallion (Bronze/Silver/Gold)** 而不是 Lambda / Kappa — retail 主要 batch 不是 stream, medallion 更对路. Lambda 给 ML real-time scoring 留, 不在 ingest pipeline.

2. **Iceberg on S3 for Bronze** 而不是 Snowflake direct ingest — schema-on-read 灵活, 失败可 reprocess from raw, 不绑死 warehouse.

3. **dbt + Snowflake 跑 transform** 而不是 Spark/EMR — 团队 SQL 普及, dbt test + lineage 一站式, Spark 维护成本不值.

4. **Per-source connector module** 而不是 generic ingest framework — 12 source schema 差异太大, 强 abstraction 会泄露. 每 source 一个 module, 共享只共享 (schema validate, DLQ, observability) 这些 cross-cutting.

5. **Schema registry + PR-based schema review** — schema 变更不能产线接到再处理, 必须 source owner / data consumer 在 PR 阶段达成共识.

6. **Dagster asset-based 而不是 Airflow task-based** — 12 source 异构 + 强 lineage 需求 + 现代 dev experience, Dagster 更对路.

7. **7-day re-process window for late arrivals** — EDI / supplier delay 常见 3-4 天, 7 天 give margin. forecasting feature 用 merge 接受 update.

8. **DLQ per source, not central** — 每 source 一个桶, owner 清晰, 不混淆. 每天 9am review.

---

## 数字 (capacity sizing, cost math)

**Volumes**:
- POS: 7M txn/day combined (Oracle 5M + NCR 2M) × avg 1KB = 7GB/day
- E-commerce: 700K orders/day × 2KB = 1.4GB/day
- SAP: 1M inventory updates/day × 0.5KB = 500MB/day
- WMS: 50K events/day × 1KB = 50MB/day
- EDI: 5K files/day × 50KB = 250MB/day
- Weather/social: < 100MB/day
- **Total**: ~10GB/day = 3.6TB/year for Bronze (compressed Iceberg ≈ 1.5TB/yr)

**Compute**:
- Lambdas for ingest: ~$2K/month (5M invocations/day pooled)
- Kinesis: 32 shards × $0.015/h × 24 × 30 = $350/month
- Snowflake compute for dbt: 3 warehouses × 8h/day = ~$8K/month (mid-size XL)
- Total infra: ~$12K/month

**Storage** (5-year cumulative):
- Bronze hot (90d): 135GB → $3/month
- Bronze Glacier (5 yr): 7.5TB → $40/month
- Silver / Gold (active): 5TB → $115/month (Snowflake)
- Total: < $500/month storage

**SaaS connectors**:
- Fivetran SAP: ~$1500/month (5K MAR)
- GoldenGate license: amortized $5K/month (often customer has)
- Qlik Replicate: $30K/year ≈ $2500/month

**Total run cost**: ~$20K/month (~$240K/year) — acceptable for a $500M revenue retailer doing weekly demand planning.

**Latency / freshness**:
- POS → Bronze: 5 min (CDC)
- Bronze → Silver: hourly batch
- Silver → Gold (forecast features): nightly 1am
- Gold available by: 6am
- Forecast generated by: 7am
- Buyer dashboards refresh: 8am ← business SLA ✓

---

## Gao Xin 简历专属 reframe

1. **TikTok PayLater BNPL 多 source 集成** — 你做过对接信用 bureau (CTOS / Experian) + risk system + KYC vendor 的 ingest pipeline, 跟这道题模式高度一致, 不同之处是 retail volume 大 100×.

2. **Indonesia refund tier (regulator audit)** — 那个项目你建过 SCD2 维表 + audit trail + DLQ, 这里全套思路复用.

3. **BytePay 数据中台经验** — 你做的内部数据 product 包括 schema registry / contract test, 这道题直接套.

4. **Internal Agent Platform** — 异构 service 集成 mindset, 跟异构 source 集成 mindset 同源.

5. **ConvFinQA multi-source** — 处理 SEC 文件 + Bloomberg + 内部 ledger 多 source 经验.

reframe: "我在字节做 BNPL 的 risk + credit 数据 pipeline, 6 个 source 用 Airflow + dbt 接, 这道题 12 source 是 scale up 不是新 paradigm. 我会切换到 Dagster 因为 asset-based 在 12 source 比 task-based 干净, 其他思路一致."

---

## 5 个 Follow-ups

1. **"如果客户突然加第 13 个 source (TikTok Shop), 你的架构改多少?"** — 答: 新 Dagster asset module (3-5 天), schema registry 加新 schema, dbt 加 staging model. 不需要改 Bronze/Silver/Gold 框架. 这是 modular 架构的好处.

2. **"周末某个 source (Shopify) webhook 全挂 6 小时, 我们怎么知道?"** — 答: data freshness watchdog Dagster sensor 每 30 分钟检查每 source `latest_event_ts`, > 90 min 无新数据触发 Slack alert + PagerDuty (P3, owner = data eng on-call). 同时每天有 reconcile job 跑 Shopify REST API 对比 webhook 接收量, 缺失 > 1% 告警.

3. **"Snowflake 跑 dbt 的 cost 在月底突然翻倍, 怎么定位?"** — 答: 用 Snowflake `QUERY_HISTORY` view + dbt-snowflake-monitoring tool. 看 (a) 哪个 model warehouse credit 涨; (b) 是 data volume 涨 vs model SQL 改差. 工具: Select Star / SDF Labs / 自建 dashboard.

4. **"两个 source (POS Oracle, SAP) 关于同一 SKU 的 inventory 数字不一致, forecasting 用谁?"** — 答: SAP 是 system of record for inventory (ERP 定义). POS 数据只用来算 sold quantity. silver 层 join 时显式 source 优先级, 同时建 reconciliation test alert 不一致 > 5%.

5. **"forecast 跑出来不准, 责任是 ingest pipeline 还是 model 团队?"** — 答: lineage 摆出来. (a) 看 data quality dashboard (dbt test pass rate, GE expectations); (b) feature 端 distribution drift 是否在 SLA 内; (c) feature → model 输入 schema 是否变. 用 OpenLineage + Marquez 显示血缘, 直接定位是上游 vs model.

---

## ❌ 死路答法

1. **"写 12 个 Airflow DAG, Spark 跑 transform"** — 太浅, 没回答 schema drift / DLQ / lineage.
2. **"用一个 generic ingester"** — 12 source 太异构, generic 漏 detail.
3. **"实时流处理 12 source (Flink)"** — 大部分 source 不需要实时, over-engineering.
4. **"raw 直接进 Snowflake, 不要 S3 lake"** — 失去 reprocess 灵活性 + 失去 Iceberg vendor 中立.
5. **"用 Excel/CSV middle ground"** — 笑.
6. **"不要 schema registry, 让 dbt 处理 schema"** — schema 变更影响 ingest, dbt 在下游, 太晚.
7. **"DLQ = warning 日志"** — DLQ 是 S3 持久化 bad rows + 有 review SLA, 不是日志.
8. **"forecasting 跟 ingestion 同一团队"** — ownership 区分, ingestion 团队对 freshness/quality SLA 负责, forecast 团队 owns model accuracy.
9. **"不做 idempotency, source 不会 dup"** — Shopify 重试是常态, POS 偶尔 dup, 必须 dedupe.
10. **"用 OpenAI 来 fuzzy match SKU"** — 数据量 7M/day, LLM 不 economic, 用 fuzzy match library (rapidfuzz) + 维表 join.

---

## ✅ 加分项

1. **画 12 source 的 (volume × freshness × stability) 矩阵** — 立刻看出你能分类思考
2. **Medallion + Iceberg + dbt + Dagster 现代 stack 主张** — signal 你不是 5 年前的 hadoop 思维
3. **Schema registry + PR-based contract test** — 真正运过 production 才会想到这层
4. **DLQ per source 而不是 central** — operational 经验
5. **7-day re-process window** — 知道 EDI 856 等真实 retail 数据延迟
6. **Dagster asset-based 论证** — 不是 just Airflow, 知道 modern orchestrator 差异
7. **Trade-off 表 (Snowflake/Databricks/BQ, Iceberg/Delta, GoldenGate/Qlik/Fivetran/Debezium)** — 完整 modern data engineering 知识
8. **Numbers 具体** (10GB/day, $20K/month run cost, 32 Kinesis shards)
9. **Reconciliation tests** (POS revenue ≈ SAP revenue ±1%) — 体现真懂 retail finance reconcile
10. **OpenLineage + Marquez** — modern lineage tool, not just "drawing arrows"

---

## 一句话总结

12 source ingest 不是 "写 12 个 ETL job", 是 **Bronze/Silver/Gold medallion + per-source connector + schema registry + DLQ + dbt tests + watermark reprocess + lineage** 一套现代 data engineering stack 同时跑 — Dagster 编, Iceberg 存, dbt 转, GE 验, OpenLineage 追.

---

## Cheat Sheet

```
12 source → 4 patterns:
  CDC (Oracle GG / Qlik / Debezium): Oracle POS, SAP, Magento
  Webhook + SQS:                     Shopify, NCR
  API poll:                          Weather, Smartsheet, Brandwatch
  File drop (SFTP/AS2):              EDI 850/856/810, Placer.ai

Medallion:
  Bronze: S3 + Iceberg, schema-on-read, 90d hot + 7yr Glacier
  Silver: Snowflake + dbt models, conformed business keys, SCD2 dims
  Gold:   Snowflake materialized, forecasting features + Feature Store

Orchestration: Dagster (asset-based) > Airflow / Prefect
Transform:     dbt on Snowflake (SQL, version-controlled, tested)
Schema:        Confluent Schema Registry, PR-reviewed
Quality:       Great Expectations checkpoints at Bronze write
DLQ:           Per-source S3 bucket, 9am daily review by data eng oncall
Idempotency:   Source-side ID + Iceberg merge + 7d webhook cache
Late data:     7-day reprocess window for forecast features
Lineage:       OpenLineage → Marquez (auto from Dagster)
Secrets:       Vault per source

Numbers:
  Volume:   ~10GB/day Bronze, 7M POS txn/day, 700K orders/day
  Compute:  $12K/month infra, $8K/month Snowflake credits
  Storage:  < $500/month
  SaaS:     ~$5K/month connectors (Fivetran SAP + Qlik)
  Total:    ~$20K/month ($240K/yr) for $500M-revenue retailer
  Freshness: T-1 by 6am, forecast by 7am, business 8am SLA ✓
```
