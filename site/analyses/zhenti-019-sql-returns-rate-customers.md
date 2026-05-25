## Q19 · SQL 找上季度退货率 > 30% 的客户

> "Write SQL to find **all customers whose return rate exceeded 30% in the previous quarter**. Schema: `orders(order_id, customer_id, order_ts, total_amount, status)` and `returns(return_id, order_id, return_ts, return_amount)`. **Walk through edge cases** — what if customer had 0 orders? What if return is partial? Quarterly cut-off?"

**中文翻译**:

> "写一条 SQL 找出**上季度退货率 (return rate) 超过 30% 的所有客户**. Schema: `orders(order_id, customer_id, order_ts, total_amount, status)` 和 `returns(return_id, order_id, return_ts, return_amount)`. **把边界情况讲一遍** — 客户 0 个订单怎么办? 部分退货怎么办? 季度切换 (quarterly cut-off) 怎么处理?"

**Round**: Coding (60 min)
**出处**: Exponent 2026 FDE · 公司: **Palantir**, Scale AI, Anyscale
**难度**: Medium (但 edge cases 决定 differentiation)
**主要技能**: SQL aggregation, date functions, edge case awareness, business semantics

---

## 📖 术语速查 (本题用到的)

> SQL 题坑全在术语. 这堆词不熟 = edge case 漏一半, 面试官立刻 spot.

### SQL 核心语法

| 术语 | 解释 |
|---|---|
| **CTE (Common Table Expression)** ⭐ | `WITH name AS (SELECT ...)` 临时命名子查询. 让 query 像分步, 不写一团嵌套 subquery. |
| **`WITH RECURSIVE`** | 递归 CTE — 树 / 图遍历. 跟普通 CTE 不同. |
| **Window function** ⭐ | `OVER (PARTITION BY ... ORDER BY ...)` 在不 collapse rows 的前提下算聚合. 这题用 `RANK()`, `LAG`, `AVG OVER`. |
| **`PARTITION BY`** | window function 内分组. 跟 `GROUP BY` 不同: 不 collapse rows. |
| **`GROUP BY ... HAVING`** | aggregate 后再 filter. `WHERE` 在 aggregate 前, `HAVING` 在后. |
| **`UNION ALL` vs `UNION`** | ALL 保留重复, UNION 去重. ALL 快很多. |
| **`DISTINCT`** ⭐ | 去重. `COUNT(DISTINCT order_id)` 这题关键, 防 multi-return 导致 rate > 1. |

### JOIN 类型

| 术语 | 解释 |
|---|---|
| **INNER JOIN** ⭐ | 只保留两边都匹配的行. 默认 JOIN. |
| **LEFT JOIN** ⭐ | 左表全保, 右表没匹配则 NULL. 这题 denom 要 LEFT 否则丢"无退货客户". |
| **RIGHT JOIN** | 反过来. 不常用 (写 LEFT 反过来读). |
| **FULL OUTER JOIN** | 两边都全保. 罕用. |
| **CROSS JOIN** | 笛卡尔积. 这题 `FROM orders, quarter_bounds` 隐式 CROSS, 因为 quarter_bounds 只 1 行 OK. |
| **USING (col)** | `JOIN ... USING (customer_id)` 简写 `ON a.customer_id = b.customer_id`. |

### Date / 时间

| 术语 | 解释 |
|---|---|
| **`DATE_TRUNC('quarter', ts)`** ⭐ | 截断到本季度初. 这题计算 "上季度" 的核心. |
| **`INTERVAL '3 months'`** | 时间间隔. PostgreSQL `+ / -` interval. |
| **`NOW() / CURRENT_TIMESTAMP`** | 当前时间. PG `NOW()` 带 timezone. |
| **`TIMESTAMP` vs `TIMESTAMPTZ`** ⭐ | TS 不带 timezone (危险); TSTZ 自带. **Production 永远用 TIMESTAMPTZ**. |
| **`AT TIME ZONE 'UTC'`** | 转 timezone. `ts AT TIME ZONE 'Asia/Jakarta'`. |
| **Fiscal year vs Calendar year** | Calendar = Jan-Dec; Fiscal 公司定义 (e.g., Feb-Jan). 报表必区分. |
| **Quarter cutover** | 季度切换的边界 (e.g., 4 月 1 日 0:00). 这题: `q_end = DATE_TRUNC('quarter', NOW())` exclusive 让边界正确. |
| **`> q_start AND < q_end`** | 半开区间 `[start, end)`. 防双倍 count 边界. |

### NULL / 防错

| 术语 | 解释 |
|---|---|
| **`NULLIF(a, b)`** ⭐ | `a = b → NULL`, 否则 `a`. 防 divide by zero: `count / NULLIF(denom, 0)`. |
| **`COALESCE(a, b, c)`** | 第一个非 NULL. 默认值用. |
| **NULL semantics** | `NULL + 1 = NULL`, `NULL = NULL` 是 NULL (不是 TRUE!). 用 `IS NULL`. |
| **3-valued logic** | TRUE / FALSE / NULL. WHERE 只保留 TRUE 的行. |
| **`IS DISTINCT FROM`** | NULL-aware 不等. `a IS DISTINCT FROM b` 是 NULL 时也能比较. |

### Aggregation

| 术语 | 解释 |
|---|---|
| **`COUNT(*)` vs `COUNT(col)` vs `COUNT(DISTINCT col)`** ⭐ | * = 所有行; col = 非 NULL 行; DISTINCT col = 去重非 NULL 值. 这题 distinct 关键. |
| **`SUM` / `AVG` / `MIN` / `MAX`** | 标准 aggregate. NULL 自动跳过. |
| **`STRING_AGG / GROUP_CONCAT`** | 字符串聚合. |
| **`FILTER (WHERE ...)`** | aggregate 条件: `COUNT(*) FILTER (WHERE status='ok')`. PostgreSQL ≥9.4. |

### Performance / 索引

| 术语 | 解释 |
|---|---|
| **Composite index** ⭐ | 多列索引 `(order_ts, status)`. 列顺序重要: range 列放前. |
| **`INCLUDE (cols)`** | Covering index — 索引页带额外列, 走 Index Only Scan 不查 heap. PG 11+. |
| **`EXPLAIN ANALYZE`** ⭐ | 跑 query 看真实 plan + 时间. 详见 Q20. |
| **Partition pruning** | 分区表 query 只扫相关 partition. |
| **`PARTITION BY RANGE`** | DDL: 按 range (date) 分区. |
| **Materialized view** | 物化视图 — 预算好的 query 结果存表, `REFRESH MATERIALIZED VIEW CONCURRENTLY` 更新. 比普通 view 快, 但要 refresh. |
| **`CONCURRENTLY`** | 在线操作不锁表. `CREATE INDEX CONCURRENTLY`, `REFRESH MATERIALIZED VIEW CONCURRENTLY`. |

### Business semantics (这题特有)

| 术语 | 解释 |
|---|---|
| **Return rate** ⭐ | 退货率. 3 种定义: (a) order count 比, (b) item count 比, (c) dollar amount 比. 必须 clarify. |
| **Status whitelist vs blacklist** | Whitelist = `IN ('COMPLETED', 'SHIPPED')` 显式; Blacklist = `!= 'CANCELLED'` 漏未来新状态. **Whitelist > Blacklist**. |
| **Sample size guard** | `orders_total >= 5` — 防 1/1 = 100% 噪声. 业务标准. |
| **Chargeback** | 持卡人投诉发卡行强扣 + 罚款. 跟普通 refund 不同. |
| **Cohort analysis** | 按入会季度 / 人群分组看 metric 趋势. |

### 数据质量 / 工程

| 术语 | 解释 |
|---|---|
| **dbt model** | dbt = data build tool. `model.sql` + tests, lineage 自动 build. 现代 BI 标准. |
| **`pg_stat_statements`** | PG 扩展, 记录所有 query 统计. 找 top-N 慢查询. |
| **Read replica** | 主库 → 从库. BI 走 replica 不卡 master. |
| **Columnar OLAP store** | BigQuery / Snowflake / ClickHouse 列存数据库. aggregation 比 row-store (Postgres) 快百倍. |
| **`(1,234.56)` 负数表示** | 财务报告习惯, 括号 = 负数. Parse 时要识别. |
| **Currency / FX rates** | 多币种不能直接 SUM. 加 `fx_rates(date, ccy, rate)` JOIN. |

---

## 这道题在考什么

很多人写一个 `SELECT customer_id FROM orders JOIN returns ... GROUP BY ... HAVING count(*) > 0.3 * count(*)` 就交. 0 分. 真考的是:

1. **Date 边界处理** — "上季度" 是哪个? 跨年? Timezone? `Q1 = Jan 1 to Mar 31` 还是 fiscal quarter?
2. **Return rate 怎么算** — by order count? by dollar amount? 部分退货怎么算?
3. **Edge case enumeration** — 0 order 客户 (division by zero), 0 return 客户 (不报 false), order 完成但 status='cancelled' 算不算 denom
4. **JOIN 类型选对** — LEFT JOIN vs INNER JOIN: 默认 INNER 会丢"无退货客户" — bug
5. **NULL handling** — `count(returns.return_id) / count(orders.order_id)` 当 0 returns 时 NULL/0
6. **CTE / window function** 用法 — 现代 SQL 必备
7. **Index strategy** — `orders(customer_id, order_ts)` 这种 composite index
8. **Communication** — 边写边说 "I assume 'return rate' = orders refunded / total orders by count"; 找面试官确认

Palantir / Scale AI 真问题: 客户 BI dashboard 找不到为什么数字不对 — 80% 时间是 SQL 边界 bug.

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|------|--------|--------|
| 1 | Clarify | 0-5 min | "上季度" 定义, return rate 定义, threshold inclusive 不 | "5 things..." |
| 2 | Sketch logic | 5-10 min | high-level decompose | "Three steps: filter quarter, aggregate per customer, threshold." |
| 3 | Write query v1 | 10-25 min | basic CTE-based | "v1: simple counts." |
| 4 | Edge cases | 25-40 min | partial return, cancelled order, zero division | "Now let me harden..." |
| 5 | Performance | 40-50 min | indexes, EXPLAIN, partition | "How does this scale to 1B orders..." |
| 6 | Variants | 50-55 min | by dollar, by item, refund vs return | "Same query for dollar-based..." |
| 7 | Discuss | 55-60 min | timezone, fiscal year, ad-hoc | "Trade-offs..." |

---

## 必问 clarifying questions

**1. 时间窗口定义**

> "By 'last quarter' — do you mean (a) the calendar quarter immediately before today, (b) the most-recently-closed fiscal quarter, or (c) 90 days ago?"

Why: 今天 May 25, "last quarter" 可能是 Q1 (Jan-Mar) 或 Q4-2025 (Oct-Dec). Fiscal year 又不同 (e.g., 公司 fiscal Q1 = Feb-Apr).

**2. Return rate 定义**

> "Is return rate = (a) # orders with any return / # orders, (b) # returned items / # ordered items, (c) sum(return_amount) / sum(order_amount)?"

Why: 完全不同 query. (a) 最简单; (c) 财务上更准.

**3. Threshold inclusive/exclusive**

> "Greater than 30% (>0.3) or greater than or equal (>=0.3)?"

Why: 4 vs 5 returns out of 13 — strictly > 0.3 includes 5/13, excludes 4/13.

**4. Status filter**

> "Should I include cancelled orders in denominator? Pending orders? Failed payment?"

Why: 客户取消订单不算"购买", 不该算分母.

**5. Minimum order threshold**

> "1 order 100% returned counts as a 'high-return customer'? Or minimum N orders?"

Why: 客户买一次退一次 — 真高退货率, 但 sample size 太小; 业务通常要求 N ≥ 5.

**6. Multi-return per order**

> "Can one order have multiple return entries? Should I count distinct orders?"

Why: 一个 order 5 件商品分多次 return → 5 return rows, 但只 1 个被退的 order.

**7. Output**

> "Just customer_id list, or with return_count, order_count, return_rate?"

Why: 通常要 columns 让 analyst follow up.

---

## 详细解题流程

### Step 1: Sketch decomposition (分解思路, 5 min)

```
Goal: customers where in [last quarter] return_rate > 0.3

Steps:
  1. Define [last quarter] explicitly: [Q_start, Q_end]
  2. Get orders in that quarter (filter by status — exclude cancelled)
  3. Per customer count: orders_total, orders_with_return
  4. return_rate = orders_with_return / orders_total  
  5. Filter return_rate > 0.3 AND orders_total >= 5
```

### Step 2: SQL v1 (basic but solid) (第一版 SQL — 基础但靠谱) — 15-20 min

```sql
-- PostgreSQL (most common in interviews; ANSI-compatible)
-- Assumption clarified:
--   "Last quarter" = the most recently completed calendar quarter
--   "Return rate" = (orders with ≥1 return) / (orders not cancelled)
--   Threshold strictly > 0.30
--   Minimum 5 orders to qualify (avoid 1-of-1 noise)

WITH quarter_bounds AS (
    -- Compute the most-recently-completed calendar quarter
    SELECT
        DATE_TRUNC('quarter', NOW()) - INTERVAL '3 months' AS q_start,
        DATE_TRUNC('quarter', NOW())                       AS q_end
    -- result: e.g. ['2026-01-01', '2026-04-01') for today=2026-05-25
),
orders_in_q AS (
    SELECT
        o.customer_id,
        o.order_id,
        o.total_amount
    FROM orders o, quarter_bounds qb
    WHERE o.order_ts >= qb.q_start
      AND o.order_ts <  qb.q_end
      AND o.status   IN ('COMPLETED', 'SHIPPED', 'DELIVERED')  -- exclude CANCELLED, FAILED, PENDING
),
orders_with_return AS (
    SELECT DISTINCT
        oiq.customer_id,
        oiq.order_id
    FROM orders_in_q oiq
    INNER JOIN returns r ON r.order_id = oiq.order_id
    -- (Optional) restrict return_ts to same window if business requires.
    -- WHERE r.return_ts >= (SELECT q_start FROM quarter_bounds)
    --   AND r.return_ts <  (SELECT q_end   FROM quarter_bounds) + INTERVAL '30 days'  -- allow grace
),
per_customer AS (
    SELECT
        oiq.customer_id,
        COUNT(DISTINCT oiq.order_id)            AS orders_total,
        COUNT(DISTINCT owr.order_id)            AS orders_returned,
        COUNT(DISTINCT owr.order_id)::numeric
            / NULLIF(COUNT(DISTINCT oiq.order_id), 0) AS return_rate
    FROM orders_in_q oiq
    LEFT JOIN orders_with_return owr USING (customer_id, order_id)
    GROUP BY oiq.customer_id
)
SELECT
    customer_id,
    orders_total,
    orders_returned,
    ROUND(return_rate::numeric, 4) AS return_rate
FROM per_customer
WHERE orders_total >= 5
  AND return_rate > 0.30
ORDER BY return_rate DESC, orders_total DESC;
```

**讲给面试官每一步**:

- **`DATE_TRUNC('quarter', NOW()) - INTERVAL '3 months'`** — 截断到本季度初, 减 3 个月 = 上季度初. End = 本季度初 (exclusive).
- **`status IN (...)`** — explicit list of 算"购买"的 status; 反例: `status != 'CANCELLED'` 会漏未来出现的 status (e.g., 'REFUNDED').
- **`COUNT(DISTINCT oiq.order_id)`** — denominator is unique orders, not unique customers, not row count.
- **`LEFT JOIN ... USING`** — 无 return 的 customer 也保留, count = 0.
- **`NULLIF(..., 0)`** — divide by zero protection. `0 / 0 = NULL`, ratio = NULL, filtered out by `> 0.30`.
- **`orders_total >= 5`** — sample size guard.
- **`ROUND(..., 4)`** — output readable.
- **`ORDER BY`** — highest-risk customers first; BI dashboard friendly.

### Step 3: Edge case discussion (边界情况讨论, 10-15 min)

#### Edge case 1: Customer with 0 orders in quarter

```sql
-- They simply don't appear in orders_in_q, so they're not in the result.
-- We do NOT want to flag "0 orders → infinite return rate" (NULL handled by NULLIF).
```

#### Edge case 2: Customer with only cancelled orders

```sql
-- Filtered out by status IN (...). Won't appear in numerator or denominator.
```

#### Edge case 3: Order with multiple return rows

```sql
-- One order can have N return rows (e.g., 5 items returned separately).
-- Using DISTINCT on order_id collapses them to 1 returned order.
-- Without DISTINCT, return_rate could exceed 1.0 — semantic bug.

-- Verify:
SELECT order_id, COUNT(*) AS n_returns
FROM returns
GROUP BY order_id
ORDER BY n_returns DESC
LIMIT 5;
-- If you see n > 1, DISTINCT is required.
```

#### Edge case 4: Return outside the quarter window

```sql
-- An order in Q1 may be returned in Q2 (within 30-day return policy).
-- Decision:
--   Option A (default we used): count any return for an in-quarter order.
--   Option B: count only returns whose return_ts is also in quarter.
-- Clarify with interviewer. Business semantics:
--   - If "Q1 return rate" means "Q1 sales that get returned", Option A
--   - If "Q1 problem rate" (operational), Option B
```

#### Edge case 5: Partial return (return_amount < total_amount)

```sql
-- Our query counts an order as "returned" if any return row exists.
-- For dollar-weighted return rate:
WITH ...
returns_in_q AS (
    SELECT
        oiq.customer_id,
        oiq.order_id,
        oiq.total_amount,
        COALESCE(SUM(r.return_amount), 0) AS refunded_amount
    FROM orders_in_q oiq
    LEFT JOIN returns r ON r.order_id = oiq.order_id
    GROUP BY oiq.customer_id, oiq.order_id, oiq.total_amount
),
per_customer AS (
    SELECT
        customer_id,
        COUNT(*)                               AS orders_total,
        SUM(total_amount)                      AS order_dollars_total,
        SUM(refunded_amount)                   AS refunded_dollars_total,
        SUM(refunded_amount) / NULLIF(SUM(total_amount), 0) AS return_rate_dollar
    FROM returns_in_q
    GROUP BY customer_id
)
SELECT ... WHERE return_rate_dollar > 0.30 ...
```

#### Edge case 6: Customer who ordered in Q1 but returned in Q2 (next quarter)

```sql
-- Same as case 4. Default our query: includes if return is ANY time on Q1 order.
```

#### Edge case 7: Duplicate orders (same order_id appears twice)

```sql
-- Schema should prevent (primary key), but defensive:
WITH orders_in_q AS (
    SELECT DISTINCT customer_id, order_id, total_amount
    FROM orders
    WHERE ...
)
```

#### Edge case 8: Timezone

```sql
-- order_ts is TIMESTAMPTZ or TIMESTAMP?
-- If TIMESTAMP (no tz), check what tz it's stored in.
-- Default PostgreSQL: NOW() and DATE_TRUNC respect session timezone.
-- Production rule: store TIMESTAMPTZ everywhere; convert at presentation.

-- Explicit timezone:
SELECT
    DATE_TRUNC('quarter', NOW() AT TIME ZONE 'UTC') AS q_end,
    DATE_TRUNC('quarter', NOW() AT TIME ZONE 'UTC') - INTERVAL '3 months' AS q_start
```

#### Edge case 9: Quarter cutover

```sql
-- If today is exactly Apr 1 00:00:00:
--   DATE_TRUNC('quarter', NOW()) = 2026-04-01
--   q_end = 2026-04-01
--   q_start = 2026-01-01
-- Q1 results — correct.
-- If today is Mar 31 23:59:59:
--   DATE_TRUNC('quarter', NOW()) = 2026-01-01 (we're IN Q1)
--   q_end = 2026-01-01
--   q_start = 2025-10-01
-- → Q4 2025 results. Correct ("last completed quarter").
```

#### Edge case 10: Fiscal year ≠ calendar year

```sql
-- Some companies fiscal year starts Feb 1. "Q1" = Feb-Apr.
-- DATE_TRUNC('quarter', NOW()) gives calendar quarter, not fiscal.
-- Fix:
WITH quarter_bounds AS (
    SELECT
        DATE_TRUNC('quarter', NOW() - INTERVAL '1 month') + INTERVAL '1 month' - INTERVAL '3 months' AS q_start,
        DATE_TRUNC('quarter', NOW() - INTERVAL '1 month') + INTERVAL '1 month' AS q_end
)
-- Or maintain a fiscal_calendar table for clarity (recommended).
```

### Step 4: Performance + indexes (性能与索引, 10 min)

**Schema:**
```
orders   (order_id PK, customer_id FK, order_ts, total_amount, status)
returns  (return_id PK, order_id FK, return_ts, return_amount)
```

**Indexes needed**:

```sql
-- Hot path: filter by date range + status, group by customer_id
CREATE INDEX idx_orders_ts_status ON orders (order_ts, status);
-- Better for our query: composite on customer_id + order_ts (so per-customer aggregation streams)
CREATE INDEX idx_orders_cust_ts ON orders (customer_id, order_ts) INCLUDE (total_amount, status);

-- For JOIN to returns:
CREATE INDEX idx_returns_order_id ON returns (order_id);
-- If return_ts filter:
CREATE INDEX idx_returns_order_ts ON returns (order_id, return_ts);
```

**EXPLAIN ANALYZE expected**:

```
HashAggregate  (cost=XXX)
  Group Key: o.customer_id
  ->  Hash Right Join  (cost=XXX)
        Hash Cond: (r.order_id = o.order_id)
        ->  Bitmap Heap Scan on returns r (cost=XXX)
              Index Cond: (return_ts >= ...)
        ->  Hash
              ->  Bitmap Heap Scan on orders o
                    Index Cond: (order_ts >= ... AND order_ts < ...)
                    Filter: (status IN (...))
```

**Partitioning** (if 100M+ orders):

```sql
-- Partition orders by RANGE (order_ts) monthly or quarterly:
CREATE TABLE orders (...) PARTITION BY RANGE (order_ts);
CREATE TABLE orders_2026q1 PARTITION OF orders FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');
-- Query plan: partition pruning, only scan orders_2026q1 (massive speed up)
```

**Materialized view** (if this query runs daily):

```sql
CREATE MATERIALIZED VIEW customer_return_rate_quarterly AS
SELECT
    customer_id,
    DATE_TRUNC('quarter', order_ts) AS quarter,
    COUNT(DISTINCT order_id) AS orders_total,
    COUNT(DISTINCT returned_order_id) AS orders_returned,
    SUM(total_amount) AS dollar_total,
    SUM(refund_amount) AS dollar_refund
FROM ...
GROUP BY 1, 2;

CREATE UNIQUE INDEX ON customer_return_rate_quarterly (customer_id, quarter);

-- Refresh nightly:
REFRESH MATERIALIZED VIEW CONCURRENTLY customer_return_rate_quarterly;

-- Query becomes O(rows in MV):
SELECT customer_id, orders_returned::numeric / orders_total AS rate
FROM customer_return_rate_quarterly
WHERE quarter = DATE_TRUNC('quarter', NOW()) - INTERVAL '3 months'
  AND orders_total >= 5
  AND orders_returned::numeric / orders_total > 0.30;
```

### Step 5: Window function variant (window function 进阶版本)

For ranking / quarter-over-quarter trend:

```sql
-- Compare each customer's return rate over the past 4 quarters
WITH per_customer_quarter AS (
    SELECT
        o.customer_id,
        DATE_TRUNC('quarter', o.order_ts) AS quarter,
        COUNT(DISTINCT o.order_id) AS orders,
        COUNT(DISTINCT r.order_id) AS returns
    FROM orders o
    LEFT JOIN returns r ON r.order_id = o.order_id
    WHERE o.order_ts >= DATE_TRUNC('quarter', NOW()) - INTERVAL '12 months'
      AND o.status IN ('COMPLETED', 'SHIPPED', 'DELIVERED')
    GROUP BY o.customer_id, DATE_TRUNC('quarter', o.order_ts)
),
with_rate AS (
    SELECT
        customer_id,
        quarter,
        orders,
        returns,
        returns::numeric / NULLIF(orders, 0) AS rate,
        AVG(returns::numeric / NULLIF(orders, 0)) OVER (
            PARTITION BY customer_id
            ORDER BY quarter
            ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
        ) AS rate_4q_rolling
    FROM per_customer_quarter
)
SELECT
    customer_id,
    quarter,
    rate,
    rate_4q_rolling,
    RANK() OVER (PARTITION BY quarter ORDER BY rate DESC) AS rank_in_quarter
FROM with_rate
WHERE quarter = DATE_TRUNC('quarter', NOW()) - INTERVAL '3 months'
  AND orders >= 5
  AND rate > 0.30
ORDER BY rate DESC;
```

### Step 6: Sample data + test (样本数据与测试, 5-10 min)

```sql
-- Setup test data
CREATE TEMP TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    order_ts TIMESTAMPTZ,
    total_amount NUMERIC,
    status TEXT
);

CREATE TEMP TABLE returns (
    return_id INT PRIMARY KEY,
    order_id INT,
    return_ts TIMESTAMPTZ,
    return_amount NUMERIC
);

-- Assume today is 2026-05-25, so last quarter = Q1 2026 (Jan 1 - Apr 1)
INSERT INTO orders VALUES
    -- Customer 1: 10 orders, 4 returned → 40%, EXPECTED IN RESULT
    (1, 1, '2026-01-15', 100, 'COMPLETED'),
    (2, 1, '2026-01-20', 100, 'COMPLETED'),
    (3, 1, '2026-02-01', 100, 'COMPLETED'),
    (4, 1, '2026-02-10', 100, 'COMPLETED'),
    (5, 1, '2026-02-15', 100, 'COMPLETED'),
    (6, 1, '2026-03-01', 100, 'COMPLETED'),
    (7, 1, '2026-03-05', 100, 'COMPLETED'),
    (8, 1, '2026-03-10', 100, 'COMPLETED'),
    (9, 1, '2026-03-20', 100, 'COMPLETED'),
    (10, 1, '2026-03-25', 100, 'COMPLETED'),
    -- Customer 2: 6 orders, 1 returned → 16.6%, NOT in result
    (11, 2, '2026-01-15', 50, 'COMPLETED'),
    (12, 2, '2026-02-01', 50, 'COMPLETED'),
    (13, 2, '2026-02-15', 50, 'COMPLETED'),
    (14, 2, '2026-03-01', 50, 'COMPLETED'),
    (15, 2, '2026-03-15', 50, 'COMPLETED'),
    (16, 2, '2026-03-25', 50, 'COMPLETED'),
    -- Customer 3: 2 orders, 2 returned → 100%, BUT < 5 orders, NOT in result
    (17, 3, '2026-01-10', 200, 'COMPLETED'),
    (18, 3, '2026-02-01', 200, 'COMPLETED'),
    -- Customer 4: 5 orders, all in Q1, 2 returned → 40%, IN result
    (19, 4, '2026-01-05', 75, 'COMPLETED'),
    (20, 4, '2026-01-15', 75, 'COMPLETED'),
    (21, 4, '2026-02-10', 75, 'COMPLETED'),
    (22, 4, '2026-03-05', 75, 'COMPLETED'),
    (23, 4, '2026-03-25', 75, 'COMPLETED'),
    -- Customer 5: 5 cancelled orders in Q1, NOT in result
    (24, 5, '2026-01-15', 100, 'CANCELLED'),
    (25, 5, '2026-02-01', 100, 'CANCELLED'),
    (26, 5, '2026-02-15', 100, 'CANCELLED'),
    (27, 5, '2026-03-01', 100, 'CANCELLED'),
    (28, 5, '2026-03-15', 100, 'CANCELLED'),
    -- Customer 6: 8 orders in Q4 2025 (last year), should NOT be in result
    (29, 6, '2025-10-15', 100, 'COMPLETED'),
    (30, 6, '2025-10-20', 100, 'COMPLETED'),
    (31, 6, '2025-11-01', 100, 'COMPLETED'),
    (32, 6, '2025-11-10', 100, 'COMPLETED'),
    (33, 6, '2025-11-15', 100, 'COMPLETED'),
    (34, 6, '2025-12-01', 100, 'COMPLETED'),
    (35, 6, '2025-12-05', 100, 'COMPLETED'),
    (36, 6, '2025-12-10', 100, 'COMPLETED');

INSERT INTO returns VALUES
    -- Customer 1's returns
    (1, 1, '2026-01-20', 100),
    (2, 3, '2026-02-08', 100),
    (3, 5, '2026-02-25', 100),
    (4, 8, '2026-03-15', 100),
    -- Customer 2's return
    (5, 11, '2026-01-25', 50),
    -- Customer 3's returns (2 of 2 = 100% but < 5 orders)
    (6, 17, '2026-01-20', 200),
    (7, 18, '2026-02-10', 200),
    -- Customer 4's returns
    (8, 19, '2026-01-15', 75),
    (9, 22, '2026-03-15', 75),
    -- Customer 6's returns (last year, not in window)
    (10, 29, '2025-10-20', 100),
    (11, 32, '2025-11-15', 100),
    (12, 34, '2025-12-10', 100);

-- Run main query → expect:
-- customer_id=1, orders_total=10, orders_returned=4, return_rate=0.4
-- customer_id=4, orders_total=5,  orders_returned=2, return_rate=0.4
```

**Run + verify**:

```sql
WITH quarter_bounds AS (
    -- Hardcoded for test: "as of 2026-05-25"
    SELECT
        '2026-01-01'::timestamptz AS q_start,
        '2026-04-01'::timestamptz AS q_end
),
orders_in_q AS (
    SELECT o.customer_id, o.order_id, o.total_amount
    FROM orders o, quarter_bounds qb
    WHERE o.order_ts >= qb.q_start
      AND o.order_ts <  qb.q_end
      AND o.status   IN ('COMPLETED', 'SHIPPED', 'DELIVERED')
),
orders_with_return AS (
    SELECT DISTINCT oiq.customer_id, oiq.order_id
    FROM orders_in_q oiq
    INNER JOIN returns r ON r.order_id = oiq.order_id
),
per_customer AS (
    SELECT
        oiq.customer_id,
        COUNT(DISTINCT oiq.order_id) AS orders_total,
        COUNT(DISTINCT owr.order_id) AS orders_returned,
        COUNT(DISTINCT owr.order_id)::numeric
            / NULLIF(COUNT(DISTINCT oiq.order_id), 0) AS return_rate
    FROM orders_in_q oiq
    LEFT JOIN orders_with_return owr USING (customer_id, order_id)
    GROUP BY oiq.customer_id
)
SELECT customer_id, orders_total, orders_returned,
       ROUND(return_rate::numeric, 4) AS return_rate
FROM per_customer
WHERE orders_total >= 5
  AND return_rate > 0.30
ORDER BY return_rate DESC, orders_total DESC;

-- Expected:
-- customer_id | orders_total | orders_returned | return_rate
-- ------------+--------------+-----------------+-------------
--           1 |           10 |               4 |     0.4000
--           4 |            5 |               2 |     0.4000
```

---

## 完整代码 (Production-ready)

```sql
-- File: top_return_rate_customers.sql
-- PostgreSQL 13+. Adjust DATE_TRUNC, INTERVAL syntax for other dialects.
-- Parameterized: pass min_orders and threshold as CTE inputs.

WITH params AS (
    SELECT
        5::int       AS min_orders,
        0.30::numeric AS threshold,
        -- "Last completed calendar quarter" relative to today
        DATE_TRUNC('quarter', NOW()) - INTERVAL '3 months' AS q_start,
        DATE_TRUNC('quarter', NOW())                       AS q_end
),
orders_in_q AS (
    SELECT o.customer_id, o.order_id, o.total_amount
    FROM orders o, params p
    WHERE o.order_ts >= p.q_start
      AND o.order_ts <  p.q_end
      AND o.status   IN ('COMPLETED', 'SHIPPED', 'DELIVERED')
),
orders_with_return AS (
    SELECT DISTINCT oiq.customer_id, oiq.order_id
    FROM orders_in_q oiq
    INNER JOIN returns r ON r.order_id = oiq.order_id
),
per_customer AS (
    SELECT
        oiq.customer_id,
        COUNT(DISTINCT oiq.order_id)            AS orders_total,
        COUNT(DISTINCT owr.order_id)            AS orders_returned,
        COUNT(DISTINCT owr.order_id)::numeric
            / NULLIF(COUNT(DISTINCT oiq.order_id), 0) AS return_rate
    FROM orders_in_q oiq
    LEFT JOIN orders_with_return owr USING (customer_id, order_id)
    GROUP BY oiq.customer_id
)
SELECT
    customer_id,
    orders_total,
    orders_returned,
    ROUND(return_rate::numeric, 4) AS return_rate
FROM per_customer, params p
WHERE orders_total >= p.min_orders
  AND return_rate > p.threshold
ORDER BY return_rate DESC, orders_total DESC;
```

---

## 复杂度分析

| 操作 | Cost |
|------|------|
| Range scan on orders (date filter) | O(n_q) where n_q = orders in quarter |
| Hash join with returns | O(n_q + r_q) |
| GROUP BY customer_id | O(n_q) hash aggregate |
| Total | O(n_q + r_q) |

**Sample numbers**:
- 100M orders total, 25M in last quarter → ~5s on PostgreSQL with proper indexes
- With materialized view: 50ms

**Index plan**:
```
orders (order_ts, status)               — range scan on quarter
returns (order_id)                       — hash join probe
orders (customer_id) [for grouping]      — sort/hash aggregate
```

---

## Gao Xin 简历专属 reframe

- **Indonesia refund tier**: 我做的就是 refund / return 数据分析. 类似 query 跑过几十遍 — "上个月哪些 merchant refund rate > X%" 用于风控. 学到的: timezone (Jakarta vs UTC) 一不留神错位 7 小时.
- **TikTok PayLater**: refund rate cutoff 是 risk team 的核心指标 — 我们用 materialized view + airflow 每天 refresh.
- **BNPL chatbot**: 不直接相关, 但 metrics dashboard 类似 SQL 多.
- **Voice agent**: outbound call success rate / refund linkage SQL.
- **ConvFinQA**: 9-variant ablation 跑模型时, evaluation 也是 SQL aggregation over predictions vs ground truth.

**面试一句话**: "Wrote queries like this daily at TikTok PayLater. The two real-world traps I've hit: timezone-naive timestamps when ops uploaded a CSV (off by 7 hours), and double-counting orders that had multiple return rows."

---

## 5 个 Follow-ups

**Q1**: "如果 customer 在 Q1 买的 但 Q2 才退, 算 Q1 还是 Q2 的 return rate?"

A: 业务决定. 两种 view:
1. **Origination view** (我们 default): order date 决定, "Q1 的销售的退货率". 适合 sales / quality 评估.
2. **Activity view**: return date 决定, "Q2 处理了多少退货". 适合 operations.

通常 dual report — 两个都展示给 business. SQL 改 `WHERE r.return_ts BETWEEN ...`.

**Q2**: "1B orders / 100M customers, 你怎么 scale?"

A:
1. **Partition orders** by month (range): pruning to last 3 months only
2. **Materialized view** refresh nightly
3. **Sharding** by customer_id hash if even 1 quarter doesn't fit
4. **Columnar store** (BigQuery, Snowflake, ClickHouse) for OLAP workload
5. **Pre-aggregated table** maintained by streaming job (e.g., Flink consumes Kafka)
6. **Sample**: business doesn't always need exact — 1% sample give 99% confidence

**Q3**: "What if `returns.order_id` could be NULL (e.g., bulk return covering multiple orders)?"

A: Schema bug, 但 defensive:
```sql
INNER JOIN returns r ON r.order_id = oiq.order_id AND r.order_id IS NOT NULL
```
更好的: 扩展 schema `return_order_link(return_id, order_id, partial_amount)`, query 走 link table.

**Q4**: "我们 dashboard 跑得慢, 怎么 debug?"

A:
1. `EXPLAIN (ANALYZE, BUFFERS)` 看 plan
2. 检查 sequential scan vs index scan
3. 看 join 顺序 (PostgreSQL 选错 join order 时 hint)
4. `pg_stat_statements` 看 top slow queries
5. 检查 stats: `ANALYZE orders;`
6. Plan cardinality estimate 错就 force replan
7. 上 materialized view 短路
8. 考虑 partitioning

(详细见 Q20)

**Q5**: "If `total_amount` is in 7 currencies, 怎么 sum?"

A: Never sum mixed-currency directly. 选项:
1. Add `currency_code` column, group by it; report per-currency
2. Convert to USD using `fx_rates(date, from_ccy, to_ccy, rate)` table — JOIN on date
3. Pre-compute `total_amount_usd` at insert time (denormalized)

Production: 选 3, 静态 fx rate at-time-of-order, 不会因 fx 浮动改历史报告.

---

## 死路答法

1. **`SELECT customer_id FROM orders JOIN returns GROUP BY customer_id HAVING count(*)/count(*) > 0.3`** — divides numerator by itself = always 1.0. Wrong.
2. **`INNER JOIN returns`** — 丢无退货客户; 但其实我们要"在 numerator 用 INNER, denominator 用 ALL". 必 LEFT JOIN.
3. **没 NULLIF protection** — 0 orders divides → error.
4. **`WHERE return_ts BETWEEN`** without orders date filter — 把别期 order's return 算进来.
5. **No `DISTINCT order_id`** — multi-return per order → return_rate > 1.0
6. **`status != 'CANCELLED'`** — 漏未来出现的 'FAILED', 'PENDING' status
7. **Hardcoded quarter dates** — 下季度跑全错
8. **`>= 0.3` instead of `> 0.3`** — 题目说 "exceeded" = strictly greater
9. **No minimum order count** — 1/1 = 100% 误报
10. **`AVG(case when return ...)`** — 写 case 走 percentage 也能对, 但读起来不如 explicit count

---

## 加分项

**真 production 加分**:

- **`pg_stat_statements`** monitor query frequency, suggest mat view
- **`EXPLAIN ANALYZE`** before merging; flag plan regression in CI
- **`stats_target`** higher for date columns (better cardinality estimate)
- **Read replica**: BI 走 replica 不卡 write master
- **dbt model**: 把 query 写成 dbt model, 加 tests (`returns_rate >= 0 AND <= 1`)
- **Lineage**: dbt / Dataform 自动 build customer_metric_quarterly 依赖 orders + returns
- **Data quality**: 加 dq check — `orders_returned <= orders_total`, `return_rate IS NOT NULL`
- **Document semantics**: comment "return_rate counts orders, not items, not dollars" so future analyst doesn't redo
- **Notification**: customer 上榜 (high return rate) → 触发 review workflow (manual investigation)
- **Cohort comparison**: per-quarter trend chart in BI
- **Predictive**: ML model trained on "high return next quarter" — early flag

---

## 一句话总结

> **CTE: quarter window → orders_in_q (status filter) → orders_with_return (LEFT JOIN returns) → per_customer (count DISTINCT, NULLIF division) → filter rate > 0.3 AND orders >= 5. Edge cases: cancelled status, partial return, multi-return per order, timezone, fiscal vs calendar quarter.**

---

## Cheat Sheet

```sql
-- The query in 5 logical steps:
-- 1. quarter bounds (DATE_TRUNC + INTERVAL)
-- 2. orders_in_q: filter by date AND status whitelist
-- 3. orders_with_return: DISTINCT order_id from inner join to returns
-- 4. per_customer: LEFT JOIN, GROUP BY customer_id, NULLIF on denominator
-- 5. final filter: rate > threshold AND orders >= min

-- Edge cases to call out:
--   - 0 orders → not in result (NULLIF protects, then > 0.3 filters out NULL)
--   - cancelled / failed status → excluded by whitelist
--   - multi-return per order → DISTINCT order_id
--   - return outside quarter → business choice, default: include
--   - small sample (1/1 = 100%) → min_orders >= 5
--   - timezone → use TIMESTAMPTZ; or AT TIME ZONE 'UTC'
--   - fiscal vs calendar → use a fiscal_calendar table

-- Indexes:
--   orders(order_ts, status)
--   orders(customer_id, order_ts) INCLUDE (total_amount, status)
--   returns(order_id)
--   returns(order_id, return_ts) if filter

-- Performance levers:
--   - Partition orders by month (RANGE)
--   - Materialized view + nightly refresh CONCURRENTLY
--   - Read replica for BI
--   - Columnar OLAP (BigQuery / Snowflake) for ad-hoc

-- Variants:
--   - Dollar-weighted: SUM(return_amount) / SUM(total_amount)
--   - Item-weighted: needs items table
--   - Window function: 4-quarter rolling
--   - Q-over-Q trend: LAG over PARTITION BY customer_id

-- Don't:
--   - INNER JOIN (loses no-return customers)
--   - count(*) / count(*) (=1)
--   - skip DISTINCT order_id
--   - skip NULLIF (div by 0)
--   - hardcode dates
--   - status != 'CANCELLED' (whitelist > blacklist)
--   - sum mixed currency
```
