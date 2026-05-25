## Q20 · 诊断慢 SQL — 查询计划, 索引, 分区

> "A customer dashboard query is **taking 45 seconds** to run, was previously sub-second. They blame us. **Walk through how you'd diagnose it** — query plan, indexes, partitioning, statistics. They send you the query and `EXPLAIN ANALYZE` output. Find the bottleneck."

**Round**: Coding (60 min, may be partly diagnostic-style)
**出处**: Exponent 2026 FDE · 公司: **Palantir**, Anyscale, Scale AI
**难度**: Medium-Hard
**主要技能**: DB internals, query plan reading, index strategy, customer empathy

---

## 这道题在考什么

不会写 SQL 也能装 1 年 — DB perf debugging 是真硬功夫:

1. **能读 query plan** — 不只是看"是不是 seq scan", 要看 cardinality estimate vs actual, buffer hits, sort/hash spill
2. **索引心智模型** — composite index 列顺序, INCLUDE columns, partial index, covering index
3. **统计信息 + planner** — `ANALYZE`, `pg_stat_statements`, `auto_vacuum`, `pg_stat_user_indexes`
4. **Partition strategy** — RANGE/LIST/HASH 何时上, pruning
5. **真实场景 awareness** — 周一全表 ANALYZE 跑了 stats refresh, plan flip — production-y 故事
6. **Customer empathy** — 客户着急, 你能不能不慌. 系统化排查, 不靠 vibes
7. **End-to-end 思维** — 不只 SQL, 还看 lock contention, IO 饱和, connection pool

Palantir 真问题: 客户 Foundry workbook query 突然慢. 你 30 分钟内不告诉他原因 + 修复就有事.

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|------|--------|--------|
| 1 | Clarify | 0-5 min | 问 baseline, when started, dataset growth, recent changes | "5 things..." |
| 2 | Triage 三层 | 5-12 min | 区分 query / data / infra issue | "Three suspects: query, data, infra." |
| 3 | EXPLAIN ANALYZE | 12-25 min | 读 plan, 找 cardinality + 大 cost step | "Let me read the plan..." |
| 4 | Hypothesis | 25-35 min | 5 个 hypothesis 排序按可能性 | "I think it's #2 — let me verify." |
| 5 | Fix + verify | 35-50 min | 加 index / refactor query / ANALYZE | "Add this index, re-run plan..." |
| 6 | Prevent | 50-58 min | monitoring, regression test | "To prevent recurrence..." |
| 7 | Communicate | 58-60 min | tell customer what + ETA + impact | "Summary for customer..." |

---

## 必问 clarifying questions

**1. Baseline + when started**

> "How long was it before? Sub-second? When did it start being slow — gradual or sudden?"

Why: Sudden = plan flip / stats / recent change; gradual = data growth.

**2. Recent deploys / data load**

> "Any deploy, schema change, big data load, vacuum/analyze in last 24h?"

Why: 80% of "suddenly slow" = a known change.

**3. Tables grown?**

> "How big is the table now vs a month ago? 10x growth?"

Why: 10x → plan switches from index scan to seq scan if planner decides.

**4. Query frequency + concurrency**

> "Is this 1 query at a time or 100 concurrent? Lock waits?"

Why: Lock blocking can disguise as slow query.

**5. Cache state**

> "Is the buffer pool warm or cold? First run vs repeated?"

Why: Cold cache 10x slower normal; not real perf issue.

**6. Other queries**

> "Is everything else slow too or just this one?"

Why: All slow = infra (disk, CPU); one slow = query/index.

**7. Resource pressure**

> "DB host CPU / memory / disk IOPS / connection count?"

Why: Saturation = throw money at problem first, then optimize.

---

## 详细解题流程

### Step 1: Triage — three suspects

```
SUSPECT 1: Query / Plan
  - Plan changed (no longer using index)
  - Bad cardinality estimate → wrong join order / wrong join type
  - Implicit type cast disabling index use
  - Function on indexed column (WHERE upper(email) = ... → seq scan)
  - Predicate not selective enough for index

SUSPECT 2: Data
  - Table grew 100x → seq scan now expensive
  - Skewed distribution (one value dominant, planner mis-estimates)
  - Stale statistics → planner guesses wrong
  - Bloat (many dead tuples after UPDATE/DELETE without VACUUM)
  - Index bloat (delete + insert without REINDEX)

SUSPECT 3: Infra / Concurrency
  - Lock contention (ALTER TABLE in flight, vacuum blocking)
  - IO saturated (autovacuum + dump + this query competing)
  - Buffer pool too small → cache miss
  - Disk failing / EBS slowing
  - Connection pool exhausted, query queued
```

### Step 2: EXPLAIN ANALYZE — what to read

```sql
EXPLAIN (ANALYZE, BUFFERS, COSTS, VERBOSE) <your query>;
```

**Sample output** (with annotated read):

```
HashAggregate  (cost=5012345.45..5012345.67 rows=22 width=24)
  (actual time=45000.123..45000.456 rows=18 loops=1)            ← actual rows / time
  Group Key: o.customer_id
  Buffers: shared hit=12345 read=987654                          ← read = disk; hit = cache
  ->  Hash Right Join  (cost=4567890.12..4987654.32 rows=1000000 width=12)
        (actual time=12000.000..40000.000 rows=15000000 loops=1) ← ROWS HUGE MISMATCH
        Hash Cond: (r.order_id = o.order_id)
        Buffers: shared hit=20 read=987000
        ->  Seq Scan on returns r  (cost=0..123456 rows=10000000)
              (actual time=0.020..1500.000 rows=10000000 loops=1)
              Buffers: shared read=560000
        ->  Hash  (cost=4444444 rows=100000)
              (actual time=10000..10000 rows=100000 loops=1)
              ->  Index Scan using idx_orders_ts on orders o
                    (actual time=0.02..8500 rows=100000 loops=1)
                    Index Cond: (order_ts >= '...' AND order_ts < '...')
                    Filter: status = 'COMPLETED'
                    Rows Removed by Filter: 90000               ← post-filter wasteful
```

**Key reading skills**:

1. **`(cost=A..B rows=N)` vs `(actual time=C..D rows=M)`**:
   - If `N` (estimate) << `M` (actual) by 10x → **stale stats** or correlated columns; planner picked wrong join type
   - If `N` >> `M` by 10x → planner overly pessimistic; might use seq scan when index would help

2. **`Buffers: shared hit=X read=Y`**:
   - `read=Y` is disk reads (8KB pages); large `read` = cold cache or first run
   - `hit=X` = page cache; high `hit / (hit + read)` = warm

3. **Plan node types** (left to right ordered by cost):
   - `Seq Scan` — full table; ok if filter selective AFTER but usually bad
   - `Index Scan` — uses index; preferred for selective predicate
   - `Bitmap Heap Scan` — index gives row pointers, then heap fetched; mid ground
   - `Index Only Scan` — covering index, no heap visit; fastest
   - `Hash Join` — build hash on smaller side; good for non-skewed joins
   - `Merge Join` — both sides sorted; good for sorted joins
   - `Nested Loop` — outer x inner; good for small outer; **disastrous** if planner mis-estimates outer

4. **`Rows Removed by Filter: N`** = filter applied AFTER index lookup → not really used; consider index on filter column

5. **`Sort` with `external merge Disk: N kB`** = sort spilled to disk; bump `work_mem`

6. **`-> Hash` with high mem and `Buckets: 1024 Batches: 8`** = hash join spilled; bump `work_mem`

7. **`loops=N`** with `N > 1` on nested loop inner = repeated execution; multiply costs

### Step 3: 5 hypotheses (in order of likelihood)

#### H1: Stats are stale (very common after large load)

```sql
-- Check last analyze
SELECT relname, n_live_tup, n_dead_tup, last_analyze, last_autoanalyze
FROM pg_stat_user_tables
WHERE relname IN ('orders', 'returns');

-- If last_analyze is days ago + data has changed → ANALYZE
ANALYZE orders;
ANALYZE returns;

-- Then re-run EXPLAIN ANALYZE and compare.
```

**Why often correct**: autovacuum thresholds = 50 + 20% of rows changed. A 100M-row table changing 5M rows is < 20%, so autoanalyze doesn't trigger, and stats become stale.

#### H2: Missing or wrong-shape index

```sql
-- Look at indexes on the tables
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('orders', 'returns');

-- Common findings:
--   - Only PK (order_id) and PK (return_id) — no help for our WHERE order_ts BETWEEN
--   - Index on (order_ts) but not (order_ts, status) — filter on status still happens after scan
--   - Index on (status) only — low cardinality, not useful alone

-- Fix:
CREATE INDEX CONCURRENTLY idx_orders_ts_status
ON orders (order_ts, status) INCLUDE (customer_id, total_amount);

-- Why composite (order_ts, status):
--   - order_ts is range filter → leading column
--   - status is equality → next
--   - INCLUDE pulls referenced columns onto index page → Index Only Scan

CREATE INDEX CONCURRENTLY idx_returns_order_id
ON returns (order_id);
```

#### H3: Bad join order from cardinality misestimate

```sql
-- If planner picks 'Nested Loop' on huge outer + small inner —
-- it estimated outer is small; reality is huge.

-- Fix 1: better stats
ALTER TABLE orders ALTER COLUMN order_ts SET STATISTICS 1000;
ANALYZE orders;

-- Fix 2: extended statistics on correlated columns
CREATE STATISTICS s_orders_ts_status (dependencies, ndistinct)
ON order_ts, status FROM orders;
ANALYZE orders;

-- Fix 3 (hammer): JOIN order hint via pg_hint_plan extension
/*+ Leading(o r) HashJoin(o r) */
SELECT ...

-- Fix 4: rewrite to force order
WITH o AS MATERIALIZED (
    SELECT order_id, customer_id FROM orders WHERE ... 
)
SELECT ... FROM o JOIN returns r ON r.order_id = o.order_id
```

#### H4: Function on indexed column

```sql
-- Bad:
WHERE DATE(order_ts) = '2026-05-25'    -- DATE() prevents index use
WHERE UPPER(email) = 'X@Y.COM'         -- UPPER() prevents
WHERE order_id::text = '123'           -- cast prevents

-- Fix: use sargable forms
WHERE order_ts >= '2026-05-25' AND order_ts < '2026-05-26'
-- Or build expression index:
CREATE INDEX idx_orders_email_upper ON orders (UPPER(email));
```

#### H5: Bloat / dead tuples

```sql
-- Check bloat
SELECT relname,
       n_live_tup, n_dead_tup,
       round(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS pct_dead
FROM pg_stat_user_tables
WHERE n_live_tup > 1000
ORDER BY pct_dead DESC;

-- If pct_dead > 20%:
VACUUM ANALYZE orders;   -- normal vacuum (online)
VACUUM FULL orders;       -- aggressive (locks table — only off-hours)
-- Better: pg_repack (online compaction, no lock)
```

#### Additional candidates

- **Lock wait**: `pg_stat_activity` show queries waiting on lock
- **Connection pool exhausted**: app log shows queue
- **Backfill job running**: `pg_stat_activity` 看 long-running other queries
- **Disk IOPS saturated**: `iostat -x 1` on host
- **Wrong work_mem**: sort/hash spilled

### Step 4: Working example walkthrough

**Customer query** (typical dashboard):

```sql
SELECT
    c.region,
    SUM(o.total_amount) AS revenue,
    COUNT(DISTINCT o.customer_id) AS customers
FROM orders o
JOIN customers c USING (customer_id)
WHERE o.order_ts >= NOW() - INTERVAL '30 days'
  AND o.status = 'COMPLETED'
GROUP BY c.region;
```

**EXPLAIN ANALYZE before**:

```
HashAggregate  (cost=2500000 rows=10)
  (actual time=45000 rows=10)
  ->  Hash Join  (cost=... rows=15000000)
        (actual rows=15000000)
        Hash Cond: o.customer_id = c.customer_id
        ->  Seq Scan on orders o                       ← BAD: full scan of 1B rows
              Filter: (order_ts >= NOW() - '30 days' AND status='COMPLETED')
              Rows Removed by Filter: 985000000
              Buffers: shared read=8000000
        ->  Hash
              ->  Seq Scan on customers c              ← OK for 10K rows

Planning Time: 0.5 ms
Execution Time: 45123 ms
```

**Diagnosis**: Seq scan on 1B orders, removing 985M rows by filter. Missing index on `(order_ts, status)`.

**Fix**:

```sql
CREATE INDEX CONCURRENTLY idx_orders_ts_status
ON orders (order_ts, status)
INCLUDE (customer_id, total_amount);

ANALYZE orders;
```

**EXPLAIN ANALYZE after**:

```
HashAggregate  (actual time=850 rows=10)
  ->  Hash Join  (actual rows=15000000)
        Hash Cond: o.customer_id = c.customer_id
        ->  Index Only Scan using idx_orders_ts_status on orders o
              Index Cond: (order_ts >= NOW() - '30 days' AND status='COMPLETED')
              Heap Fetches: 0                          ← visible-map satisfied!
              Buffers: shared hit=300000 read=20000    ← 100x less I/O
        ->  Hash
              ->  Seq Scan on customers c

Planning Time: 0.7 ms
Execution Time: 870 ms                                 ← 50x faster
```

Done — 45s → 0.87s.

### Step 5: Diagnostic script

```sql
-- Step 0: confirm slow
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) <query>;

-- Step 1: any locks/blockers?
SELECT pid, usename, state, wait_event_type, wait_event, query, age(NOW(), state_change) AS waiting_for
FROM pg_stat_activity
WHERE state != 'idle' AND pid != pg_backend_pid()
ORDER BY waiting_for DESC NULLS LAST;

-- Step 2: stats fresh?
SELECT schemaname, relname, n_live_tup, n_dead_tup, last_analyze, last_autoanalyze
FROM pg_stat_user_tables
WHERE relname IN (...);  -- tables in your query

-- Step 3: bloat?
SELECT relname,
       round(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS pct_dead
FROM pg_stat_user_tables;

-- Step 4: indexes available?
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE tablename IN (...);

-- Step 5: index usage?
SELECT indexrelname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE relname IN (...)
ORDER BY idx_scan ASC;
-- idx_scan = 0 → unused index, drop candidate

-- Step 6: slow queries by total time
SELECT query, total_exec_time, mean_exec_time, calls, rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- Step 7: cache hit ratio?
SELECT relname,
       round(100.0 * heap_blks_hit / NULLIF(heap_blks_hit + heap_blks_read, 0), 2) AS hit_ratio
FROM pg_statio_user_tables;
-- <95% might mean buffer pool too small
```

### Step 6: Partitioning when appropriate

**When**: tables > 100M rows, queries filtered by a clear range column (date).

```sql
-- Partitioned by month
CREATE TABLE orders (
    order_id    BIGSERIAL,
    customer_id BIGINT,
    order_ts    TIMESTAMPTZ NOT NULL,
    total_amount NUMERIC,
    status      TEXT
) PARTITION BY RANGE (order_ts);

CREATE TABLE orders_2026_05 PARTITION OF orders
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');

CREATE TABLE orders_2026_04 PARTITION OF orders
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

-- ... etc, monthly partitions

CREATE INDEX idx_orders_2026_05_cust ON orders_2026_05 (customer_id);
```

**Query plan with partition pruning**:

```
Append
  ->  Index Scan on orders_2026_05    ← only this partition scanned
        Index Cond: customer_id = ...
```

**Benefits**:
- Query touches only relevant partition (smaller index → less I/O)
- Drop old partitions in O(1): `DROP TABLE orders_2024_01;` instant
- VACUUM per partition independently
- Different storage class possible (hot partitions on SSD, cold on HDD)

**Pitfalls**:
- All queries must include partition key in WHERE (else scans all)
- More indexes to manage
- ALTER TABLE complex

### Step 7: Communication to customer (the FDE part!)

```
Dear customer,

I diagnosed the slow dashboard query — it was running 45s.

Root cause: the `orders` table grew 8x in the past month due to your
seasonal traffic spike. The existing query plan was a sequential scan
on the now-1.2 billion-row table.

Fix: I added a composite index on (order_ts, status) including
customer_id and total_amount. Query now runs in 0.87s.

ETA: the index build took 25 minutes (online, no downtime). Already
deployed. Dashboard should be back to sub-second on next load.

Prevention: I've added monitoring for queries with >5s p99 latency
and >1M Rows-Removed-by-Filter. We'll catch the next one earlier.

— Gao
```

---

## 完整代码 (Diagnostic Runbook)

```sql
-- =========================================================
-- Slow-SQL Diagnostic Runbook for PostgreSQL
-- Use top-to-bottom. Stop when you find the cause.
-- =========================================================

-- STEP A: Get the slow query's plan
EXPLAIN (ANALYZE, BUFFERS, VERBOSE) <your_query>;

-- STEP B: Find currently long-running / blocked queries
SELECT pid, state, wait_event, query, age(NOW(), query_start) AS runtime
FROM pg_stat_activity
WHERE state IN ('active', 'idle in transaction')
ORDER BY runtime DESC LIMIT 20;

-- STEP C: Check table sizes + stats freshness
SELECT relname,
       pg_size_pretty(pg_total_relation_size(relid)) AS size,
       n_live_tup, n_dead_tup,
       last_analyze, last_autoanalyze
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 20;

-- STEP D: Index usage (is the index even being used?)
SELECT t.relname AS table, i.indexrelname AS index,
       idx_scan, idx_tup_read, idx_tup_fetch,
       pg_size_pretty(pg_relation_size(i.indexrelid)) AS size
FROM pg_stat_user_indexes i JOIN pg_stat_user_tables t USING (relid)
ORDER BY idx_scan ASC LIMIT 20;
-- idx_scan = 0 → unused; drop if no recent need

-- STEP E: Top slow queries (need pg_stat_statements ext)
SELECT round(mean_exec_time::numeric, 2) AS mean_ms,
       calls, round(total_exec_time::numeric, 2) AS total_ms,
       LEFT(query, 100) AS query
FROM pg_stat_statements
ORDER BY total_exec_time DESC LIMIT 20;

-- STEP F: Bloat estimate
SELECT relname,
       round(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS pct_dead
FROM pg_stat_user_tables ORDER BY pct_dead DESC LIMIT 20;

-- STEP G: Cache hit ratio (target > 99%)
SELECT round(100.0 * sum(heap_blks_hit)
              / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0), 2) AS hit_pct
FROM pg_statio_user_tables;

-- STEP H: Active settings
SHOW work_mem;
SHOW shared_buffers;
SHOW effective_cache_size;
SHOW random_page_cost;
SHOW max_parallel_workers_per_gather;

-- STEP I: Fix actions (run as needed)
--   1. Refresh stats: ANALYZE table_name;
--   2. Add index:     CREATE INDEX CONCURRENTLY ...;
--   3. Rewrite query: avoid functions on indexed col, replace OR with UNION ALL, etc.
--   4. Bump work_mem for session: SET work_mem = '128MB';
--   5. Vacuum:        VACUUM ANALYZE;  (or VACUUM FULL if needed off-hours)
--   6. Partition:     for tables > 100M rows with range column
```

---

## 复杂度分析

Not algorithmic — domain knowledge.

**Typical fix latencies**:

| Action | Time | Impact |
|--------|------|--------|
| `ANALYZE table` | seconds | Fix stale stats (very common quick win) |
| `CREATE INDEX CONCURRENTLY` | minutes to hours | Most direct, low risk |
| Rewrite query | minutes | If query is clearly bad |
| `VACUUM FULL` | minutes | Reclaim bloat but locks |
| `pg_repack` | longer | Bloat without lock |
| Partition | days (data migration) | Long-term for big tables |
| Replication / read replica | days | Scale read load |

---

## Gao Xin 简历专属 reframe

- **Indonesia refund tier / TikTok PayLater**: 我们 BI 团队 ad-hoc query 经常 timeout. 我做过 DBA-light 工作: 加 composite index, run ANALYZE after big load, set up `pg_stat_statements` 报 top-N 慢查询给 Slack.
- **BNPL chatbot**: 用 ClickHouse 跑 conversation analytics (不是 Postgres 但同样 query plan 概念). 也用 partition by date.
- **Voice agent**: outbound call CDR 数据每天 1B 行, partition by date 必备.
- **ConvFinQA**: 不直接相关.

**面试一句话**: "Triaged exactly this at TikTok PayLater — a dashboard that went from 2s to 60s overnight after a large data backfill. Root cause: stats were stale, planner chose Nested Loop with bad cardinality estimate. ANALYZE + a composite index fixed it in 10 minutes."

---

## 5 个 Follow-ups

**Q1**: "如果加 index 没用呢?"

A: 几种可能:
1. **Planner 没用**: 检查 plan, 看是不是 `Seq Scan` 还在. 用 `SET enable_seqscan = OFF; EXPLAIN ...` force, 若 cost 高就 index 真没帮; 若 cost 低就 stats 错, ANALYZE.
2. **Index 列顺序**: composite index `(A, B)` only helps if WHERE 有 `A` (and optionally `B`). 没有 `A` 没用. 用 `(B, A)` 反过来.
3. **Filter selectivity 低**: index 帮不了 — 比如 `status = 'COMPLETED'` 占 95% rows, 索引不如 seq scan. 这时考虑 partial index `WHERE status != 'COMPLETED'`.
4. **Cardinality estimate 错**: planner 以为 selective, 实际不是 → wrong join order. 更细 stats / extended stats / hint.

**Q2**: "如果 dashboard 有 30 个 query, 你怎么知道哪个慢?"

A: `pg_stat_statements` 是 gold:
```sql
SELECT mean_exec_time, calls, total_exec_time, query
FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 20;
```
- `mean_exec_time` 高 = 每次慢
- `calls` 高 + `mean` 低 = 频繁但快 (总 cost 高也优化)
- `total_exec_time` 排序 = 优化收益最大的

**Q3**: "如果是 read replica 慢, master 快, 怎么办?"

A: 检查 replication lag (`pg_stat_replication`). 几种可能:
1. **Replica IO 弱**: instance class 不一样
2. **Vacuum 没跑** on replica (replica 不自动 vacuum)
3. **Long-running query** on replica 阻 apply
4. **Plan 不同** (stats 不一致) — 罕见但发生
5. **Different connection pool / work_mem 配置**

**Q4**: "如果 customer 不让 ALTER TABLE 加 index, 怎么办?"

A:
1. **Materialized view** 跑 ad-hoc 不动 schema, refresh nightly
2. **Read replica** + index 只加 replica
3. **Rewrite query** 用现有 index
4. **`CREATE INDEX CONCURRENTLY`** — online, no lock, customer 应该接受 (vs `CREATE INDEX` 阻塞 write)
5. **Communication**: 解释 risk, ETA, 跟客户走 change management

**Q5**: "Postgres 看完, 同样问题 MySQL / Snowflake / BigQuery 怎么看?"

A:
- **MySQL**: `EXPLAIN FORMAT=JSON`, `SHOW PROFILE`, `SHOW STATUS` for cache hits. Stats via `ANALYZE TABLE`. Composite index 列顺序同 PG.
- **Snowflake**: query profile UI; data spillage 看 "Bytes Spilled to Remote Storage"; cluster key (sort) 替代 index; warehouse size 主要 lever
- **BigQuery**: execution graph in console; `bytes_billed` 决定 cost; partition pruning + cluster columns; no index (BQ doesn't index, sorts/scans)
- **Trino / Presto**: EXPLAIN; partition pruning + bucketed tables

---

## 死路答法

1. **"加 index 就行"** without EXPLAIN — 可能 index 错列, 没用
2. **加 index on `status`** — low cardinality, often useless alone
3. **`SELECT *`** in dashboard — 抓全列, 没 covering index 帮不了
4. **`ORDER BY ... LIMIT 1000` 没 index on sort column** — sort spill
5. **`WHERE col LIKE '%text%'`** — leading wildcard, no index
6. **`OR` between two indexed columns** — planner 多见 seq scan; rewrite UNION ALL
7. **没 ANALYZE** — stats 错 planner 全错
8. **`VACUUM FULL` in business hours** — locks table, customer 怒
9. **Blame customer** — "你 query 烂" → tone 错, 不解决问题
10. **加索引不 CONCURRENTLY** — `CREATE INDEX` 默认 acquires Share-Exclusive lock, 阻 writes 全程

---

## 加分项

**Production 加分**:

- **`auto_explain`**: 自动 log slow query plan, post-incident 分析
- **`pg_stat_statements`** + dashboard (Grafana / pgAdmin / Datadog)
- **`pg_hint_plan` extension**: 强行干预 planner (use sparingly)
- **Connection pool**: PgBouncer / RDS Proxy 防 connection 爆
- **Read replica routing**: read query → replica 减 master 压力
- **Vacuum tuning**: `autovacuum_vacuum_scale_factor`, `analyze_threshold` 调低让 stats 跟上
- **`work_mem` per session**: 大 ad-hoc query set high (`SET work_mem = '256MB'`), 主交易 keep low
- **Index hygiene**: `pg_stat_user_indexes` 每周 review, idx_scan = 0 的 drop
- **Migration testing**: 大 ALTER TABLE 用 `pg_squeeze` / `pg_repack` 不锁
- **Backup test**: 定期 restore 验, 否则 DR 时 panic
- **Document slow-query playbook**: 团队 wiki 写 "若 X 慢 → 看 Y → 跑 Z"
- **Monitor**:
  - p99 query latency
  - n queries > 5s
  - lock wait > 1s count
  - cache hit ratio < 99%
  - bloat > 20%
  - replication lag > 10s

---

## 一句话总结

> **EXPLAIN ANALYZE first → cardinality mismatch (stale stats?) or wrong access path (missing index?) or wrong join (planner bad estimate?) → ANALYZE + CREATE INDEX CONCURRENTLY + verify with re-EXPLAIN. Customer empathy: explain root cause, ETA, prevention.**

---

## Cheat Sheet

```sql
-- The 7-step triage:
-- 1. EXPLAIN (ANALYZE, BUFFERS) <query>
-- 2. pg_stat_activity → currently blocked?
-- 3. pg_stat_user_tables → stats fresh? bloat?
-- 4. pg_indexes → exists? right columns?
-- 5. pg_stat_user_indexes → being used?
-- 6. pg_stat_statements → top N slow
-- 7. system: CPU / IOPS / connection / cache

-- Read EXPLAIN ANALYZE:
--   estimated rows vs actual: 10x off = stale stats
--   Seq Scan on big table + Filter removing >90%: missing index
--   Nested Loop with high outer + inner index miss: bad join order
--   Sort: external merge Disk: spilled work_mem
--   Hash: Batches > 1: spilled work_mem
--   Rows Removed by Filter: high = post-index filter expensive

-- 5 hypotheses ranked:
-- H1 stale stats          → ANALYZE
-- H2 missing index        → CREATE INDEX CONCURRENTLY (composite, INCLUDE)
-- H3 bad join order       → extended statistics, hint, rewrite
-- H4 function-on-column   → expression index OR rewrite sargable
-- H5 bloat                → VACUUM, pg_repack
-- (+) infra: locks, IO sat, connection pool, cold cache

-- Composite index rules:
--   leading column = range/equality predicate
--   following columns = additional equality
--   INCLUDE(...)  = for Index Only Scan (avoid heap)

-- Partitioning:
--   tables > 100M rows
--   range by date column
--   query MUST include partition key
--   drop old partition = instant

-- Comms to customer:
--   1. root cause (1 sentence)
--   2. fix + ETA
--   3. impact (downtime? data change?)
--   4. prevention monitor

-- Don't:
--   - guess at index
--   - VACUUM FULL in prod hours
--   - blame
--   - CREATE INDEX without CONCURRENTLY in prod
--   - keep stats stale
--   - SELECT *
--   - functions on indexed column
```
