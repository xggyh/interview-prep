## 题目（verbatim）

> "Build a **detection system for data pipeline quality degradation** on specific days. Cover metrics, thresholds, alerting, and root-cause routing."

**出处**: fde.academy 技术 round 经典. Databricks / Salesforce / Snowflake FDE 都问过.

**Round**: Technical Integration (45-60 min)

---

## 这道题在考什么

考你 **production data ops** — 数据 pipeline 半挂掉是 enterprise 最常见 silent failure. ML / agent 都依赖数据, 数据 silently 坏了, 模型给出错误答案, 业务直接被烫.

1. **Drift 类型分得清吗** — covariate / concept / label / schema, 各自检测方法不一样
2. **Detection 灵敏度 vs 噪声 trade-off** — 太 sensitive 警报疲劳, 太 loose 漏 bug
3. **架构怎么搭** — input monitor + output monitor + feedback loop
4. **告警怎么不疲劳** — per-segment baseline, dynamic threshold, dedup, P0/P1/P2
5. **remediation pipeline** — alert 之后呢? retrain / data fix / rollback / hotfix
6. **熟不熟工具栈** — Great Expectations / Evidently / Whylogs / Monte Carlo

考的不是「z-score 是啥」, 是「你 own 过一个 ML pipeline, 解决过 silent data quality 事故」.

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**Data pipeline**: 一条**数据流**, 从源头 (DB / API / CDC stream / 用户事件) 到下游消费者 (warehouse / dashboard / ML training / agent inference). 典型 hop: 5-15 个 service / job, 每一跳都可能引入质量问题.

**Data drift** (数据漂移): 数据**分布**随时间变化. 注意, 这是个**统计学**概念, 不是「数据有 bug」. Drift 本身**中性** — 真实世界本来就在变 (用户行为变、业务变、季节变). 问题是, 你的下游模型 / 业务逻辑没跟上.

**Concept drift** (概念漂移): 不是数据变, 是「**输入和输出的映射关系**变了」. 例如: 同一个用户特征 (年龄 30 + 月入 1 万), 2020 年的还款概率是 90%, 2024 年同样特征还款概率掉到 70% (因为通胀 / 经济环境). 模型本身没坏, 但**学到的关系不再成立**.

**Drift detection**: 一套**量化对比 "现在 vs 历史"** 的工具. 不是「我感觉数据怪」, 是「KS test p < 0.001, PSI = 0.31, 报警」.

---

## 2. 这个问题的核心是什么

**设想一个没 drift detection 的 ML / agent pipeline 灾难**:

```
2024-12-01:  上游 CRM 改了一个字段, "phone_country_code" 从 "+62" 变成 "62"
2024-12-01:  你的 voice agent feature pipeline 没人通知, 照旧 join 字段
2024-12-02:  Join 95% 失败, agent 拿不到客户 phone 信息, 输出垃圾
2024-12-02:  没监控, 没人发现
2024-12-15:  PM 发现 NPS 掉了 20 个点, 才开始查
2024-12-20:  Root cause 找到, fix
            → 15 天数据污染, 70% 客户体验崩坏
```

**问题**:

- **Silent failure**: pipeline 没报错, 数据正常入库, 只是质量低
- **下游放大**: ML 模型用脏数据训练 → 永久污染 model
- **追溯困难**: 15 天后才查, 哪天开始坏的? 几条 record 受影响?
- **修复昂贵**: 回退数据、retrain、重新部署, 几周工作

**Production-grade drift detection 解法**:

```
1. Schema check (字段名 / 类型) — 改了立刻 alert (covers 30% RC)
2. Volume check (row count) — 多少掉了 / 涨了多少 (covers 20% RC)
3. Null rate check (空值率) — 跳了 5% 立刻 alert (covers 15% RC)
4. Distribution check (KS / PSI) — 分布偏了 (covers 20% RC)
5. Concept drift check (model accuracy) — 模型表现掉了 (covers 10% RC)
6. Referential check (FK 完整性) — orphan rows (covers 5% RC)
+ 加上: per-segment baseline + dynamic threshold + dedup + routing
+ 加上: 自动 remediation (retrain / rollback / data fix / hotfix)
```

---

## 3. 典型架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Data Sources                            │
│  CRM API / DB CDC / User Events / 3rd-party Files / Streams │
└─────────────┬───────────────────────────────────────────────┘
              ▼
   ┌──────────────────────┐
   │ INPUT MONITOR        │ ← 检测进 pipeline 的数据
   │  - Schema diff       │
   │  - Volume z-score    │
   │  - Null rate         │
   │  - Freshness SLA     │
   │  - Distribution (KS) │
   └─────────┬────────────┘
             ▼
   ┌──────────────────────┐
   │ Pipeline (Airflow /  │
   │ Spark / dbt / Flink) │
   └─────────┬────────────┘
             ▼
   ┌──────────────────────┐
   │ OUTPUT MONITOR       │ ← 检测出 pipeline 的数据
   │  - Same checks as    │
   │    input             │
   │  - Plus: business    │
   │    invariants        │
   │    (sum, ratio, ...) │
   │  - Plus: cross-table │
   │    referential       │
   └─────────┬────────────┘
             ▼
   ┌──────────────────────┐
   │ Downstream Consumers │
   │  - ML training       │
   │  - Agent inference   │
   │  - Dashboard         │
   │  - BI reports        │
   └─────────┬────────────┘
             ▼
   ┌──────────────────────┐
   │ FEEDBACK LOOP        │ ← 从下游回采 model perf
   │  - Online accuracy   │
   │    on labeled data   │
   │  - User feedback     │
   │  - A/B holdout       │
   │  - Concept drift     │
   └─────────┬────────────┘
             │
             │ (signals → alerts)
             ▼
   ┌─────────────────────────────────────────┐
   │ ALERT / ROUTING SYSTEM                  │
   │  Slack / PagerDuty / Auto-remediation   │
   └─────────────────────────────────────────┘
```

**3 层 monitor 缺一不可**: 只查 input 看不到 pipeline 内部 bug; 只查 output 不知道是输入坏还是逻辑坏; 没 feedback loop 看不到 concept drift.

---

## 4. 4 类 drift 分类表

| 类型 | 含义 | 例子 | 主要检测方法 | 修复方式 |
|---|---|---|---|---|
| **Covariate shift** (特征漂移) | P(X) 变了, P(Y\|X) 不变 | 用户 demographic 变了 (年轻化) | KS test / PSI on features | 通常不需 retrain (模型还成立) |
| **Concept drift** (概念漂移) | P(Y\|X) 变了 | 通胀, 同样特征还款率掉 | Online accuracy monitor | **必须 retrain** |
| **Label drift** (标签漂移) | P(Y) 变了 | 欺诈率本来 1%, 突然 5% | Label histogram | 调整 threshold / retrain |
| **Schema drift** (结构漂移) | 字段名 / 类型 / 顺序变 | "phone_country" → "phone_country_code" | Schema diff at ingest | 修 join / mapping |

**4 类的关联**:

```
Schema drift → 暴力错 (job 直接 crash, 容易发现)
Covariate shift → 模型 degrade 但仍能跑 (silent)
Concept drift → 模型完全跟不上现实 (most insidious)
Label drift → 业务环境变了 (alert business team)
```

**真实分布** (我个人 voice agent + ConvFinQA 复盘):

- Schema drift 40% (上游瞎改, 没沟通)
- Covariate shift 30% (用户群体变化)
- Concept drift 20% (世界变化)
- Label drift 10% (业务变化)

---

## 5. 具体业务场景

### 场景 A: 你的 TikTok Voice Agent — 7 markets debt collection

**Pipeline 长这样**:

```
CRM (per-market) → Daily extract → Feature store → Voice agent inference
                                      ↑
                                      └── Phone, language, debt amount, last_call_outcome
```

**真实 drift 事故**:

- 2026 春节, 印尼客户大量主动 dispute 还款条件 (经济压力)
- "promised_to_pay" outcome 占比从历史 35% 掉到 12%
- Voice agent 学的 prompt 是按 35% 训练的, 现在不适用 → 客户体验差
- **检测**: outcome distribution shift, P(Y) 变了 → label drift
- **解法**: 调整 prompt 策略 + retrain agent classifier

### 场景 B: ConvFinQA Multi-hop Reasoning

**Pipeline**:

```
Financial reports (per quarter) → Parser → Q/A generator → Eval set
                                       ↑
                                       └── 不同公司的报告格式
```

**真实 drift 事故**:

- 上游解析的报告里, 某个公司从 Q3 开始换了 PDF 模板
- 数字 column 偏移, parser 把 "Revenue" 拉成了 "Cost"
- ConvFinQA eval 准确率掉 5%, 但没人怀疑数据
- **检测**: 输入 column header 的 hash diff → schema drift
- **解法**: parser 加 schema 自适应; 加 schema diff alert

### 场景 C: BNPL Chatbot 推荐系统

**Pipeline**:

```
User events → Aggregation (1h windows) → Feature store → Recommender model
```

**真实 drift 事故**:

- 营销团队跑了一个 "新用户首单 0 利息" campaign
- 新用户占比从 5% 飙到 30%
- 模型推荐策略学的是 "成熟用户" 行为, 对新用户不准
- **检测**: P(X) 变了 — `user_tenure_days` 分布左移 → covariate shift
- **解法**: retrain with recent 7d data; segment model by tenure

### 场景 D: Indonesia Refund Tier (你做过)

**Pipeline**:

```
Refund request → Tier classifier → Confirmation rule → Auto/Manual approve
```

**真实 drift 事故**:

- Indonesia 经济波动, 平均 refund amount 上涨 40%
- Tier threshold 还是历史的, 大量原本 "auto-approve" 的进入 "manual-confirm"
- Manual queue 爆炸, customer 等 24h
- **检测**: amount distribution 右移; tier 分布偏离基线
- **解法**: dynamic threshold (滚动 30d 中位数); per-market baseline

### 场景 E: 经典 model accuracy degradation

**Pipeline**:

```
Loan application → Risk model → Approve/Deny
```

**真实 drift 事故**:

- 通胀 + 失业率上涨
- 同样特征的人, 实际违约率从 3% 涨到 7%
- 模型预测的违约率还是历史的, 大量 "低风险" 客户最后违约
- **检测**: Online accuracy on labeled data, 看 prediction vs realized
- **解法**: 持续 retrain (每周); concept drift detector ADWIN / DDM

---

## 6. 工程上要做什么 — 实现 checklist

**Stage 0: Foundation (Week 1-2)**

1. **数据 contract**: 每个 source ↔ pipeline 之间签 schema contract (JSON Schema / Avro / Protobuf)
2. 接入工具: **Great Expectations** for assertions, **Evidently** for drift dashboards, **Whylogs** for profiling
3. 定义 monitoring scope: 不可能监控所有 column, 选 top 20 重要的

**Stage 1: Input Monitor (Week 2-4)**

4. **Schema diff**: 每次 ingest 计算 schema hash, 改变就 alert
5. **Volume**: row count 7d trailing mean ± 3 SD, alert if drop > 20% or surge > 50%
6. **Freshness**: SLA on `MAX(updated_at)`, alert if older than expected + 1h grace
7. **Null rate**: per-column null %, alert if Δ > 5pp from 7d mean
8. 关键 column (customer_id, order_id) **零容忍**: 任何 null 立刻 alert

**Stage 2: Distribution Monitor (Week 4-6)**

9. **Numeric column**: today's mean / std / quantiles vs 7d baseline, KS test
10. **Categorical column**: PSI > 0.25 alert, > 0.1 watch
11. **Embedding shift** (for text / images): centroid distance from baseline embedding
12. Per-segment baseline (per-market, per-customer-tier), not just global

**Stage 3: Output + Feedback (Week 6-8)**

13. **Business invariants**: e.g., `sum(line_items) == order.total`, `count(orders today) ≥ count(orders yesterday) * 0.5` (sanity)
14. **Referential integrity**: orphan row count, constraint violation count
15. **Model accuracy monitor**: 抽样标注 + 模型预测对比
16. **Online feedback**: user complaints, manual escalation rate, A/B holdout group

**Stage 4: Alert + Routing + Remediation (Week 8-10)**

17. **Alert routing** by detected dimension (see Problem 5 below)
18. **Auto-remediation playbook**:
    - Schema drift → block downstream + page integration team
    - Volume drop → fail open, alert source team
    - Concept drift → trigger retrain job
    - Distribution shift → notify model owner, watch + decide
19. **Audit log**: every alert + resolution kept 1y for SOC 2 / compliance

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **ML-based anomaly detection day 1** | Black-box, no one can RCA. **Start statistical**, layer ML after 3 months stable |
| 2 | **Single threshold for all tables** | Important table needs tighter; toy table tolerant |
| 3 | **没 per-segment baseline** | Global mean hides per-segment failure (e.g., 1 market down, aggregate looks fine) |
| 4 | **没 dedup** | Single root cause fires 50 alerts → alert storm |
| 5 | **没 P0/P1/P2 stratification** | Page on everything = page on nothing |
| 6 | **没 routing** | Alert lands in `#general`, nobody owns |
| 7 | **没 dashboard** | Only alerts = no daily situational awareness |
| 8 | **过 aggregate** | Aggregate metric hides 90% of drift signal |
| 9 | **没 calendar suppression** | Black Friday / public holiday = false positive flood |
| 10 | **没 audit log** | Customer disputes "你说 drift 了, 证据呢" — 无据可查 |

---

## 一句话总结 (Part 1)

> **Data pipeline drift detection = "区分 4 类 drift (covariate / concept / label / schema), 用合适的检测方法 (KS / PSI / schema diff / accuracy monitor), 按 dim routing 给 owner, 并配套 remediation playbook"**.
>
> 这道题考的不是 "你知道 z-score 公式", 是 "你 own 过 production ML pipeline, 看着它 silently 坏过, 之后修出来一套监控体系".

---

# Part 2 · 5 个深度工程问题

## ⚙️ Problem 1: 4 类 Drift — 各自检测方法

### 1.1 Schema Drift

**最简单, 最常见, 也最容易抓**.

```python
import hashlib, json
from typing import Dict, List

def compute_schema_fingerprint(df) -> str:
    """字段名 + 类型 + 顺序的 hash."""
    schema = [(col, str(df[col].dtype)) for col in df.columns]
    return hashlib.sha256(json.dumps(schema, sort_keys=False).encode()).hexdigest()

class SchemaMonitor:
    def __init__(self, db):
        self.db = db

    def check(self, table_name, current_df):
        current_fp = compute_schema_fingerprint(current_df)
        baseline_fp = self.db.get_baseline_schema(table_name)

        if current_fp != baseline_fp:
            diff = self._compute_diff(table_name, current_df)
            self._alert(table_name, diff)
            return False
        return True

    def _compute_diff(self, table_name, current_df):
        baseline = self.db.get_baseline_columns(table_name)
        current = {col: str(current_df[col].dtype) for col in current_df.columns}

        added = set(current.keys()) - set(baseline.keys())
        removed = set(baseline.keys()) - set(current.keys())
        type_changed = {
            col: (baseline[col], current[col])
            for col in set(current.keys()) & set(baseline.keys())
            if current[col] != baseline[col]
        }
        return {'added': added, 'removed': removed, 'type_changed': type_changed}
```

**Severity 分级**:

- **Critical**: required column 消失 / type 变 (`int` → `str`) → block downstream
- **Warning**: nullable column 增加 / order 变 → log only

**工具**: `pandera`, `Great Expectations`, `dbt schema tests`.

### 1.2 Covariate Shift (Feature Distribution)

**Population Stability Index (PSI)** 是工业界最常用的:

```python
import numpy as np

def compute_psi(baseline: np.ndarray, current: np.ndarray, bins=10) -> float:
    """PSI: 数值越大说明分布越偏离 baseline.
    
    PSI < 0.1: 没显著偏移
    PSI 0.1-0.25: 小幅偏移, watch
    PSI > 0.25: 显著偏移, alert
    """
    # 用 baseline 的分位数定义 bin 边界
    breakpoints = np.percentile(baseline, np.linspace(0, 100, bins + 1))
    breakpoints[0] = -np.inf
    breakpoints[-1] = np.inf

    base_counts, _ = np.histogram(baseline, bins=breakpoints)
    cur_counts, _ = np.histogram(current, bins=breakpoints)

    # 转 percentage, 避免除零用 epsilon
    base_pct = (base_counts / base_counts.sum()) + 1e-6
    cur_pct = (cur_counts / cur_counts.sum()) + 1e-6

    psi = np.sum((cur_pct - base_pct) * np.log(cur_pct / base_pct))
    return float(psi)

# Usage
baseline = df_7d['debt_amount'].values
current = df_today['debt_amount'].values
psi = compute_psi(baseline, current)
if psi > 0.25:
    alert(f"PSI={psi:.3f} on debt_amount — significant covariate shift")
```

**配合 KS test (Kolmogorov-Smirnov)** 做连续分布的 hypothesis test:

```python
from scipy.stats import ks_2samp

stat, p_value = ks_2samp(baseline, current)
if p_value < 0.001:
    alert(f"KS test rejects null at p={p_value} — distribution differs")
```

**Categorical 用 chi-square**:

```python
from scipy.stats import chi2_contingency

def chi2_drift(baseline_counter, current_counter):
    keys = sorted(set(baseline_counter) | set(current_counter))
    table = [
        [baseline_counter.get(k, 0) for k in keys],
        [current_counter.get(k, 0) for k in keys],
    ]
    chi2, p, _, _ = chi2_contingency(table)
    return chi2, p
```

### 1.3 Concept Drift — 最难检测

P(Y|X) 变了, 不能只看输入分布, **必须看模型表现**:

```python
# Online accuracy monitor
class ConceptDriftDetector:
    """
    用 ADWIN (Adaptive Windowing) 或 DDM (Drift Detection Method) 实时检测.
    简化版用滚动窗口看 accuracy trend.
    """
    def __init__(self, window_size=1000):
        self.window = []  # (prediction, actual) tuples
        self.window_size = window_size
        self.baseline_acc = None

    def observe(self, prediction, actual):
        self.window.append((prediction, actual))
        if len(self.window) > self.window_size:
            self.window.pop(0)

        if len(self.window) < self.window_size:
            return

        current_acc = sum(p == a for p, a in self.window) / len(self.window)
        if self.baseline_acc is None:
            self.baseline_acc = current_acc
            return

        # 5% 绝对下降 alert
        if self.baseline_acc - current_acc > 0.05:
            alert(f"Concept drift: baseline_acc={self.baseline_acc:.3f}, "
                  f"current={current_acc:.3f}")
            self.baseline_acc = current_acc  # 重置 baseline
```

**问题**: 需要 label, 实时 label 难拿. 解决:

- **Delayed feedback**: e.g., 还款 30 天后才知道实际违约
- **A/B holdout**: 10% 流量保留 manual label
- **Surrogate signal**: 用户行为变化 (复购率 / 投诉率) 作为 proxy

### 1.4 Label Drift

P(Y) 变了, 在没有 X 的情况下看 label distribution:

```python
def label_drift_check(baseline_labels, current_labels):
    """简单 histogram 对比."""
    from collections import Counter
    base_dist = Counter(baseline_labels)
    cur_dist = Counter(current_labels)

    total_base = sum(base_dist.values())
    total_cur = sum(cur_dist.values())

    for label in set(base_dist) | set(cur_dist):
        base_pct = base_dist[label] / total_base
        cur_pct = cur_dist[label] / total_cur
        delta = cur_pct - base_pct
        if abs(delta) > 0.05:  # 5pp shift
            alert(f"Label drift on {label}: {base_pct:.2%} → {cur_pct:.2%}")
```

**响应**:

- 不一定 retrain (label 变可能是真实业务变化)
- 但需要 **alert business** + **update threshold** + **consider re-balance**

---

## ⚙️ Problem 2: Detection Methods — KS / PSI / Chi-square / Embedding / Model-based

### 2.1 Statistical Test 选型

| 数据类型 | 推荐方法 | 公式直觉 | Tool |
|---|---|---|---|
| 连续 numeric | **KS test** | 累积分布最大差 | `scipy.stats.ks_2samp` |
| 连续 numeric (业务化) | **PSI** | 加权 log-ratio | 自实现 |
| Categorical | **Chi-square** | 期望 vs 实际频次 | `scipy.stats.chi2_contingency` |
| Text / embedding | **Centroid distance** | embedding mean 距离 | sentence-transformers |
| 模型表现 | **Accuracy / F1 滚动窗口** | 直接看 model output | 自实现 |
| 通用 | **Wasserstein distance** | 把一个分布"运到"另一个的最小代价 | `scipy.stats.wasserstein_distance` |

### 2.2 Embedding Distance for Text / Image

**场景**: agent input 是自然语言, 没法直接 KS test. 转 embedding:

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

class TextDriftDetector:
    def __init__(self):
        self.baseline_centroid = None
        self.baseline_radius = None

    def fit(self, baseline_texts):
        embs = model.encode(baseline_texts)
        self.baseline_centroid = embs.mean(axis=0)
        # 75th percentile distance as "normal radius"
        distances = np.linalg.norm(embs - self.baseline_centroid, axis=1)
        self.baseline_radius = np.percentile(distances, 75)

    def check(self, current_texts):
        embs = model.encode(current_texts)
        cur_centroid = embs.mean(axis=0)
        centroid_shift = np.linalg.norm(cur_centroid - self.baseline_centroid)

        if centroid_shift > 2 * self.baseline_radius:
            alert(f"Embedding centroid shift: {centroid_shift:.3f} "
                  f"(baseline radius: {self.baseline_radius:.3f})")
```

**用在哪**:

- ConvFinQA: 监控 incoming question 的 embedding 是否偏离训练分布
- Voice agent: 监控用户 utterance embedding 是否飘出语义边界

### 2.3 Model-based Drift Detection

**思想**: 训练一个 binary classifier 区分 "baseline 数据" vs "current 数据". 如果它能轻松分开 → 两个分布有显著差异.

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

def model_based_drift(baseline_df, current_df, threshold=0.7):
    """如果 AUC > 0.7, 说明两个分布显著不同."""
    X_base = baseline_df.values
    X_cur = current_df.values
    X = np.vstack([X_base, X_cur])
    y = np.concatenate([np.zeros(len(X_base)), np.ones(len(X_cur))])

    clf = RandomForestClassifier(n_estimators=100, max_depth=5)
    auc = cross_val_score(clf, X, y, cv=5, scoring='roc_auc').mean()

    # feature importance 还能告诉你哪个 feature drift 最严重
    clf.fit(X, y)
    importances = dict(zip(baseline_df.columns, clf.feature_importances_))
    top_drifting = sorted(importances.items(), key=lambda x: -x[1])[:5]

    return {'auc': auc, 'is_drifting': auc > threshold, 'top_features': top_drifting}
```

**优点**: 多维联合分布、能指出**哪个 feature drift 最严重**.

**缺点**: 算得慢, 不适合实时.

---

## ⚙️ Problem 3: 架构 — Input + Output + Feedback 三层 Monitor

### 3.1 Input Monitor (Pipeline 入口)

**贴近数据源, 抓上游问题**:

```python
# 用 Great Expectations 做声明式 contract
import great_expectations as gx

context = gx.get_context()
suite = context.create_expectation_suite("orders_input_contract")

batch = context.get_batch({...}, "orders_table")

batch.expect_column_to_exist("customer_id")
batch.expect_column_values_to_not_be_null("customer_id")
batch.expect_column_values_to_be_unique("order_id")
batch.expect_column_values_to_be_between("amount", min_value=0, max_value=1e7)
batch.expect_column_value_lengths_to_equal("country_code", value=2)
batch.expect_table_row_count_to_be_between(min_value=1000, max_value=100000)
batch.expect_column_values_to_match_regex("email", r".+@.+\.[a-z]{2,}")

result = batch.validate()
if not result.success:
    block_pipeline(reason=result.statistics)
    alert_team(result.results)
```

**部署**: Airflow operator `GreatExpectationsOperator` 跑在 ingest task 之前.

### 3.2 Output Monitor (Pipeline 出口)

**业务 invariant 校验**:

```python
class OutputMonitor:
    """Pipeline 出口检查, 多了 business logic 校验."""

    def __init__(self, db):
        self.db = db

    def check_invariants(self, today):
        violations = []

        # Invariant 1: orders today >= 50% of yesterday (sanity)
        today_count = self.db.count('orders', date=today)
        yesterday_count = self.db.count('orders', date=today - 1)
        if today_count < 0.5 * yesterday_count:
            violations.append(f"Order volume dropped {today_count}/{yesterday_count}")

        # Invariant 2: sum(line_items) == orders.total
        mismatch = self.db.query("""
            SELECT order_id FROM orders o
            JOIN (SELECT order_id, SUM(amount) as li_sum
                  FROM line_items GROUP BY order_id) l
            ON o.order_id = l.order_id
            WHERE ABS(o.total - l.li_sum) > 0.01
        """).count()
        if mismatch > 0:
            violations.append(f"{mismatch} orders with mismatched line items")

        # Invariant 3: no orphan line_items
        orphans = self.db.query("""
            SELECT COUNT(*) FROM line_items l
            LEFT JOIN orders o ON l.order_id = o.order_id
            WHERE o.order_id IS NULL
        """).scalar()
        if orphans > 0:
            violations.append(f"{orphans} orphan line items")

        return violations
```

### 3.3 Feedback Loop (从下游回采)

**关键**: 没有 feedback loop, **concept drift 不可见**.

```python
class FeedbackCollector:
    def __init__(self, db):
        self.db = db

    def collect_voice_agent_feedback(self):
        """从下游收集 voice agent 的实际效果."""
        return self.db.query("""
            SELECT
              market,
              DATE(call_started_at) as date,
              COUNT(*) as total_calls,
              SUM(CASE WHEN outcome = 'promised_to_pay' THEN 1 ELSE 0 END) as promises,
              SUM(CASE WHEN actually_paid_within_30d = TRUE THEN 1 ELSE 0 END) as fulfilled,
              AVG(user_satisfaction_score) as avg_sat
            FROM voice_agent_calls
            WHERE call_started_at >= CURRENT_DATE - 30
            GROUP BY market, DATE(call_started_at)
        """).all()

    def detect_concept_drift(self):
        history = self.collect_voice_agent_feedback()
        # 30d 前的 fulfillment rate vs 最近 7d
        old = [r for r in history if r.date < today - 7]
        new = [r for r in history if r.date >= today - 7]

        old_fulfill = sum(r.fulfilled for r in old) / sum(r.promises for r in old)
        new_fulfill = sum(r.fulfilled for r in new) / sum(r.promises for r in new)

        if old_fulfill - new_fulfill > 0.05:
            alert(f"Concept drift: promise→fulfill rate "
                  f"{old_fulfill:.2%} → {new_fulfill:.2%}")
```

**实战 quote**:

> 在 voice agent 上, **input + output monitor 抓 80% 的 schema / volume / null 问题, feedback loop 抓另外 20% 的 concept drift**. 没 feedback loop, 你永远不知道 "模型还活着但效果掉了".

---

## ⚙️ Problem 4: 告警 — 阈值调优 + Per-segment + 减少疲劳

### 4.1 Dynamic Threshold (动态阈值)

```python
class DynamicThreshold:
    """
    用滚动 30d 的 mean + k * std 作为阈值, 而不是硬编码.
    业务量变了, threshold 自动跟着变.
    """

    def __init__(self, metric_name, k=3, window_days=30):
        self.metric = metric_name
        self.k = k
        self.window = window_days

    def is_anomaly(self, today_value, history):
        recent = history[-self.window:]
        if len(recent) < 7:
            return False  # 数据不足, 不报警

        mean = np.mean(recent)
        std = np.std(recent)
        z = (today_value - mean) / (std + 1e-6)
        return abs(z) > self.k
```

**为什么 dynamic 比静态好**:

- 业务季节性 (黑五 / 春节) 自动适应
- 业务增长期 (新功能上线后流量翻倍) 自动校准
- 减少 false positive (固定阈值在业务变化时大量误报)

### 4.2 Per-segment Baseline

```python
# 全局: 1 个 baseline
# Per-segment: per (market, customer_tier, day_of_week) 各 1 个 baseline

class SegmentedBaseline:
    """每个 segment 单独存 baseline."""

    def __init__(self):
        self.baselines = {}  # key: (market, tier, dow), value: stats

    def fit(self, df):
        for (market, tier, dow), grp in df.groupby(['market', 'tier', 'dow']):
            self.baselines[(market, tier, dow)] = {
                'mean': grp['volume'].mean(),
                'std': grp['volume'].std(),
                'p05': grp['volume'].quantile(0.05),
                'p95': grp['volume'].quantile(0.95),
            }

    def is_anomaly(self, row):
        key = (row['market'], row['tier'], row['dow'])
        b = self.baselines.get(key)
        if not b:
            return False
        return row['volume'] < b['p05'] or row['volume'] > b['p95']
```

**为什么**: aggregate 看不到 "Indonesia 周一掉 50%, 但 Singapore 周一涨 60%, 加起来正常" 这种场景.

### 4.3 Alert Fatigue Reduction

**4 个手段**:

#### (a) Stratification (P0/P1/P2)

```python
def severity(check_name, magnitude):
    if check_name in ['schema_critical', 'required_field_null']:
        return 'P0'  # page immediately
    if check_name in ['volume_drop_50pct', 'concept_drift_acc_drop_10pct']:
        return 'P1'  # page in business hours
    return 'P2'  # slack only

# P0/P1 → PagerDuty
# P2 → Slack channel
```

#### (b) Dedup (Group Alerts by Root Cause)

```python
class AlertDedup:
    """同一 source × dim × 1h 窗口内的 alert 聚合."""

    def __init__(self, window_sec=3600):
        self.window = window_sec
        self.recent = {}  # key: (source, dim), value: last_fire_ts

    def should_fire(self, alert):
        key = (alert.source, alert.dim)
        last = self.recent.get(key, 0)
        if time.time() - last < self.window:
            # 不发, 但累计 count
            self._increment_count(key)
            return False
        self.recent[key] = time.time()
        return True
```

#### (c) Auto-resolve

```python
def auto_resolve(alert_id, stable_period_sec=1800):
    """alert 触发后, 如果 metric 连续 30 min 回到正常, 自动 close."""
    alert = db.get_alert(alert_id)
    metric_history = metric_store.fetch(
        alert.metric_name,
        start=time.time() - stable_period_sec,
    )
    if all(not is_anomaly(v) for v in metric_history):
        db.close_alert(alert_id, reason='auto_resolved')
```

#### (d) Calendar Suppression

```python
# 已知大流量日子, 自动 suppress volume 类 alert
KNOWN_SURGE_DAYS = ['2026-02-12', '2026-11-29', '2026-12-25']  # Black Friday, etc.

def should_alert(check, today):
    if check in ['volume_surge', 'volume_drop'] and today in KNOWN_SURGE_DAYS:
        return False
    return True
```

### 4.4 Alert 评价 — Quarterly Review

```python
# 每季度跑一次, tune 阈值
def alert_quality_review(quarter):
    alerts = db.get_alerts(quarter)

    for alert_type in set(a.type for a in alerts):
        ats = [a for a in alerts if a.type == alert_type]
        true_positive = sum(1 for a in ats if a.resolution == 'real_issue')
        false_positive = sum(1 for a in ats if a.resolution == 'auto_resolved')

        precision = true_positive / (true_positive + false_positive + 1e-6)
        print(f"{alert_type}: precision={precision:.2%}, total={len(ats)}")

        if precision < 0.3:
            print(f"  → Suggestion: tighten threshold or remove")
        if len(ats) == 0:
            print(f"  → Suggestion: this alert never fired, dead code?")
```

---

## ⚙️ Problem 5: Remediation Pipeline — Alert 之后呢

**Alert ≠ Fix**. 系统化的 remediation playbook:

### 5.1 Routing by Detected Dimension

```python
ROUTING_TABLE = {
    'schema_drift': {
        'owner': 'data-integration-team',
        'playbook': 'block_pipeline_then_fix_mapping',
        'severity': 'P0',
    },
    'volume_drop': {
        'owner': 'source-system-team',  # 上游 own 数据来源
        'playbook': 'check_source_health_then_alert_partner',
        'severity': 'P1',
    },
    'volume_surge': {
        'owner': 'data-engineering',
        'playbook': 'check_for_duplicate_then_scale_pipeline',
        'severity': 'P2',
    },
    'null_spike': {
        'owner': 'data-engineering',
        'playbook': 'check_upstream_for_nullable_change',
        'severity': 'P1',
    },
    'psi_drift': {
        'owner': 'product-analytics',  # business shift, not engineering
        'playbook': 'investigate_business_event',
        'severity': 'P2',
    },
    'concept_drift': {
        'owner': 'ml-team',
        'playbook': 'trigger_retrain_job',
        'severity': 'P1',
    },
    'constraint_violation': {
        'owner': 'data-engineering',
        'playbook': 'investigate_data_quality_bug',
        'severity': 'P0',
    },
}
```

### 5.2 Remediation Playbooks

#### Playbook A: Schema Drift

```
1. BLOCK downstream (stop dependent jobs)
2. Capture old schema + new schema diff
3. Page data-integration-team
4. If upstream-driven: contact upstream owner, agree on fix vs. accept
5. Update mapping / parser
6. Unblock downstream
7. Backfill 漏过的几个小时
8. Add new schema to baseline
```

#### Playbook B: Concept Drift

```
1. CONFIRM via second signal (e.g., user complaints, manual review sample)
2. Quantify: 多大下降, 哪个 segment 受影响
3. Decision tree:
   ├─ If < 5% drop: monitor, schedule retrain in normal cadence
   ├─ If 5-10% drop: trigger retrain on recent 30d data
   └─ If > 10% drop: consider model rollback to previous version OR emergency retrain
4. Validate retrained model on holdout
5. Canary deploy (1% → 10% → 100%)
6. Update concept drift baseline
```

#### Playbook C: Volume Drop

```
1. Check source system health (is it down?)
2. Check ingestion job (did it fail silently?)
3. Check business event (holiday? policy change?)
4. If source-side: alert partner team
5. If ingestion-side: rerun job
6. If business-side: update baseline (no fix needed, it's "real")
```

### 5.3 Auto vs Manual Remediation

```python
class RemediationOrchestrator:
    """部分 remediation 可以自动跑, 部分必须人审."""

    AUTO_OK = {
        'volume_surge': 'scale_pipeline',  # 自动扩容
        'concept_drift_small': 'trigger_retrain',  # 自动 retrain
        'null_spike_known_field': 'apply_default_value',  # 自动 fillna
    }

    MANUAL_ONLY = {
        'schema_drift': 'requires_human_to_update_mapping',
        'concept_drift_large': 'requires_decision_on_rollback',
        'constraint_violation': 'requires_data_quality_investigation',
    }

    def handle(self, alert):
        if alert.type in self.AUTO_OK:
            return self._execute_auto(alert)
        if alert.type in self.MANUAL_ONLY:
            return self._create_ticket(alert)
        return self._page_oncall(alert)
```

### 5.4 Audit Trail

每个 alert + remediation 记 1y, 用于 SOC 2 / 合规:

```json
{
  "alert_id": "alrt_2026_05_21_001",
  "fired_at": "2026-05-21T14:30:00Z",
  "type": "schema_drift",
  "source": "salesforce_crm",
  "severity": "P0",
  "diff": {"removed_columns": ["phone_country"]},
  "remediation": {
    "playbook": "block_pipeline_then_fix_mapping",
    "actions": [
      {"ts": "2026-05-21T14:32:00Z", "actor": "auto", "action": "blocked_downstream"},
      {"ts": "2026-05-21T14:45:00Z", "actor": "alice@", "action": "contacted_upstream"},
      {"ts": "2026-05-21T15:30:00Z", "actor": "bob@", "action": "deployed_mapping_fix"},
      {"ts": "2026-05-21T15:35:00Z", "actor": "auto", "action": "unblocked_downstream"},
      {"ts": "2026-05-21T16:00:00Z", "actor": "alice@", "action": "backfilled_2h"}
    ],
    "resolved_at": "2026-05-21T16:00:00Z",
    "mttr_minutes": 90
  }
}
```

---

# Part 3 · 把 5 个问题串起来看

这 5 个问题是**同一件事的 5 个 viewpoint**:

1. **4 类 drift** 是「**根本现象**」 — 你要监控的实质
2. **Detection methods** 是「**量化工具**」 — KS / PSI / chi-square / accuracy
3. **3 层架构 (input / output / feedback)** 是「**部署位置**」 — 在哪监控
4. **Alerting** 是「**信号过滤**」 — 怎么把 signal 推给对的人, 不疲劳
5. **Remediation** 是「**闭环动作**」 — alert 之后怎么修

面试场或事故复盘上, 能把这 5 个 layer 系统性讲清楚 + 配套具体工具 (Great Expectations / Evidently / Whylogs / Monte Carlo), 就是 staff-level data engineering. 只会答 "z-score 大于 3 就 alert" 是初级.

---

## 必问 clarifying questions

**1. Pipeline 结构**

> "Single pipeline or many? Batch (daily) or streaming (sub-minute)? Source → sink 几跳? Existing orchestrator (Airflow / dbt / Spark)?"

**2. Downstream consumers**

> "What breaks downstream if pipeline goes bad — model training? dashboard? customer-facing feature? Different consumer = different sensitivity tolerance."

**3. Existing monitoring**

> "Any current monitoring (Datadog / Great Expectations / Monte Carlo / Evidently)? Or greenfield?"

**4. Acceptable false positive rate**

> "Pager fatigue cost: how many false alerts per week are we willing to tolerate? 1? 5? 20? Determines threshold tuning aggressiveness."

**5. Drift types prioritized**

> "Which drift type matters most — schema, distribution, or concept? Different business stage prioritizes different."

**6. Recent incident**

> "Was there a specific incident that drove this ask? Customer usually wants to detect 'the next time X happens'."

---

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify pipeline + downstream + existing tools + recent incident |
| 5-15 min | 4 类 drift + detection methods 系统讲 |
| 15-25 min | Input + Output + Feedback 三层架构 |
| 25-35 min | Alerting (threshold / segment / dedup / stratification) |
| 35-50 min | Remediation playbook + routing by dim |
| 50-60 min | Failure modes + onboarding + cost optimization |

---

## 简历专属 reframe

你的 **voice agent monitoring** + **ConvFinQA eval pipeline** + **BNPL chatbot** 直接 map:

| 题 | 你做过 |
|---|---|
| Schema drift detection | Voice agent CRM extraction 7 markets, schema 各家不一样 |
| Volume / freshness monitor | ConvFinQA eval pipeline 你 own data freshness SLA |
| Distribution PSI | ConvFinQA stratified eval 4 length buckets 类似分类思路 |
| Concept drift | Voice agent — Indonesia 经济波动 outcome 分布变 |
| Alert fatigue tuning | Voice agent 监控 7 markets, 你必经过 alert tuning |
| Per-segment baseline | Voice agent per-market latency / accuracy, 不能 aggregate |
| Routing by dim | Voice agent failure routing to LLM / ASR / TTS team |
| Auto remediation | Voice agent failed call replay tool |

**主动 quote**:

> "When I built the eval pipeline for ConvFinQA, I learned aggregate metric **hides 90% of drift**. Stratified by **4 length buckets** caught one cascade where T0 errors compound through later turns — but I had to add **per-turn-index breakdown** to see it. For voice agent monitoring across 7 markets, I applied the same lesson: **always per-segment baseline** (per market × per customer tier × per day-of-week). Without it, Indonesia's 50% volume drop got hidden by other markets' growth, and I'd have missed a 2-week silent data corruption incident. Building 6 dim of monitor (volume / freshness / schema / null / distribution / referential) gave us **MTTR < 1h on data quality issues**, vs the 15-day MTTR we had before the system."

---

## 5 follow-ups

**Q1**: "Customer wants ML-based anomaly detection. Auto-magic."

**A**: 推回去:
- "Day 1 ML detection is a trap — black-box alerts, no engineer can RCA, trust collapses fast"
- "Start statistical (z-score / quantile / KS / PSI). Once stable for 3 months, layer ML on top of statistical, with **explainable output** (which feature drifted, by how much)"
- Use **Prophet** for seasonality (interpretable, weekly+monthly+yearly decomposition), not deep models
- Industry pattern: Monte Carlo, Evidently 都是 statistical-first, ML 是补充

**Q2**: "Volume drops 50% on a Sunday — false positive (weekend)?"

**A**: Seasonality 是 alert fatigue 大头:
- **Prophet** decomposes weekly seasonality automatically
- Or **per-day-of-week baselines** (Sunday 跟 last 4 Sundays 比, 不跟 weekday 比)
- Or **calendar-aware suppression** (holidays, regional events, payday)
- 7 markets 都有不同的 holiday calendar, 每个市场单独 calendar

**Q3**: "How fast can you detect a corruption that affects 0.1% of rows?"

**A**: Hard. 0.1% 在自然 noise 之下. Mitigations:
- **Sampling row-level checks**: stratified 10k random rows / day, run referential / constraint checks
- **Domain rules**: if customer has business rules (e.g., "order_total = sum(line_items)"), assert these
- **Downstream catch**: model accuracy or dashboard ratio drift detects 0.1% if it accumulates
- Honest answer: < 0.5% corruption 通常需要 **几天到几周** 才能可靠 detect, 这是 statistical limit

**Q4**: "Customer's source system makes schema changes daily. How not to alert every time?"

**A**:
- **Schema-change allow-list**: customer maintains list of "expected upcoming changes" (PR-style)
- **Non-breaking auto-accept**: 加 nullable column = info-only
- **Breaking changes still alert**: column drop / type change / required field rename
- **Schema contract negotiation**: 跟 source team 签 SLA, e.g., "breaking schema change must give 7-day notice"

**Q5**: "We need to be auditable for SOC 2 / SOX. How does monitoring help?"

**A**:
- Every alert + resolution logged immutable for 1 year
- Compliance dashboard: % SLOs met, MTTR, alert backlog
- **Pipeline health** 越来越多被列为 SOC 2 / SOX item
- Auditor 来了能给出: "show me last 12 months of data quality incidents and their MTTR"
- **Audit chain of custody**: 每个修改有 actor + ts + reason

---

## ❌ 易错点

1. **ML anomaly day 1** — black-box, untrustable
2. **Single threshold for all tables** — important tables need tighter
3. **没 dedup** — alert storm on single root cause
4. **没 P0/P1/P2 stratification** — page on everything = page on nothing
5. **没 routing** — alert lands in #general, nobody owns
6. **没 dashboard** — only alerting = no daily situational awareness
7. **过 aggregate** — miss per-segment drift
8. **没 feedback loop** — concept drift 完全看不见
9. **没 calendar suppression** — Black Friday 报警一片
10. **没区分 4 类 drift** — schema 和 concept 用同套阈值

---

## ✅ 加分项

1. **4 类 drift 分得清** + 各自检测方法
2. **PSI for categorical drift** specific metric
3. **Prophet for seasonality** (interpretable)
4. **Alert routing by detected dim** + lineage info in alert
5. **Auto-resolve + suppression** for fatigue
6. **Phasing 60 days** from foundational to advanced
7. **Statistical first, ML later** (反 hype)
8. **Feedback loop for concept drift** explicit
9. **Per-segment baseline** (not aggregate)
10. **Tool 知道得多** (Great Expectations / Evidently / Whylogs / Monte Carlo / Prophet)
11. **Remediation playbook** per drift type
12. **Audit log for compliance**

---

## 一句话总结

> **Data pipeline drift detection = "区分 4 类 drift (covariate / concept / label / schema), 各用合适的统计 / model-based 方法检测, 在 input / output / feedback 三层架构上部署, 按 dim 路由 alert 给对的 owner, 配套 remediation playbook 闭环"**.
>
> 这道题考的不是 "你知道 z-score", 是 "你 own 过 production ML / agent pipeline, 看着它 silently 坏过, 之后修出来一套监控体系".

---

## Cheat Sheet (印 1 页)

```
4 类 drift:
  Covariate shift (P(X) 变)  → PSI, KS test
  Concept drift  (P(Y|X) 变) → accuracy monitor + ADWIN
  Label drift    (P(Y) 变)   → label histogram
  Schema drift   (字段 / 类型) → schema hash diff

Distribution stats:
  PSI > 0.25 alert, > 0.1 watch (业务化)
  KS test p < 0.001 alert (hypothesis test)
  Chi-square for categorical
  Wasserstein for general distribution
  Embedding centroid distance for text/image

3 层 monitor 架构:
  Input  monitor: schema / volume / freshness / null
  Output monitor: + business invariants
  Feedback loop: + model accuracy on labels

6 dims (实战 checklist):
  Volume    z-score + Prophet (seasonality)
  Freshness SLA on MAX(updated_at)
  Schema    snapshot + diff (Great Expectations)
  Null rate per-column %, Δ>5pp alert
  Distribution PSI > 0.25 alert
  Referential FK constraint check

Alerting:
  P0/P1/P2 stratification (page only P0/P1)
  Dynamic threshold (滚动 30d + 3 SD)
  Per-segment baseline (market × tier × dow)
  Dedup within 1h
  Auto-resolve when stable 30min
  Calendar suppression (holidays, payday)
  Quarterly review (tune low-precision alerts)

Routing by detected dim:
  Schema drift     → data-integration team (P0)
  Volume drop      → source-system team (P1)
  Null spike       → data-engineering (P1)
  PSI drift        → product-analytics (P2, business event)
  Concept drift    → ml-team (P1, trigger retrain)
  Constraint break → data-engineering (P0)

Remediation playbooks:
  Schema drift  → block + fix mapping + backfill
  Concept drift → quantify + retrain (5-10% small, >10% rollback)
  Volume drop   → check source + ingestion + business
  Auto OK: scale, retrain-small, fillna-known
  Manual: schema-change, large concept-drift, constraint-violation

Tool 栈:
  Great Expectations - declarative assertions
  Evidently AI       - drift dashboards
  Whylogs            - profiling
  Monte Carlo        - data observability platform
  Prophet            - seasonality decomposition
  Alibi-Detect       - concept drift algorithms

Phasing 60 days:
  Wk 1-2: Volume / Freshness / Schema (foundational)
  Wk 3-4: Null rate
  Wk 5-6: Distribution drift (PSI / KS)
  Wk 7-8: Concept drift + feedback loop
  Wk 9-10: Routing + remediation playbooks

红线:
  - ML day 1
  - Single threshold
  - 没 dedup
  - 没 feedback loop (concept drift 不可见)
  - 没 per-segment
  - 没 routing
```

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 核心心智模型 (1 sentence)

Data pipeline drift detection = "区分 4 类 drift (covariate P(X) / concept P(Y|X) / label P(Y) / schema 字段类型) → 用合适统计 / model-based 方法 (PSI > 0.25 alert / KS test p<0.001 / chi-square categorical / embedding centroid / accuracy monitor with ADWIN) → 在 input / output / feedback 3 层架构部署 → per-dim routing 给 owner (schema → integration team P0 / concept → ml team P1 / volume → source team P1) → remediation playbook 闭环 (block + fix mapping / quantify + retrain / check source + alert)", 90% 失败是 silent failure 没监控.

### 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| Covariate shift | P(X) 变, 模型仍成立 | 通常不 retrain |
| Concept drift | P(Y\|X) 变, 模型跟不上现实 | **必须 retrain** |
| Label drift | P(Y) 变, 业务环境变化 | alert business + threshold |
| Schema drift | 字段名 / 类型 / 顺序变 | block downstream + fix mapping |
| PSI | Population Stability Index, 0.25+ alert | 业务化 distribution metric |
| KS test | Kolmogorov-Smirnov 累积分布最大差 | hypothesis test |
| Chi-square | 期望 vs 实际频次, categorical | category drift |
| ADWIN | Adaptive Windowing, concept drift detector | online accuracy 跟踪 |
| Embedding centroid | text/image drift, mean distance from baseline | non-numeric drift |
| 3 层 monitor | Input + Output + Feedback | 架构必备 |
| Feedback loop | 从下游 label 回采, 见 concept drift | 否则不可见 |
| Per-segment baseline | per (market, tier, dow) 单独 baseline | aggregate 隐 |
| Dynamic threshold | 滚动 30d mean ± 3 SD | 业务变化时自动校准 |
| Alert dedup | (source × dim × 1h) 同窗口聚合 | 防 storm |
| Calendar suppression | 黑五 / 春节 已知大流量日 不报 | 防节假 false positive |
| Remediation playbook | per-drift-type 闭环动作 | block / retrain / fix mapping |

### 5 个核心 framework / pattern

**Framework 1**: 4 类 drift 分类
- When: 出现 quality 问题前
- Algorithm: covariate (P(X)) / concept (P(Y|X)) / label (P(Y)) / schema (字段/类型); 真实分布 schema 40% / covariate 30% / concept 20% / label 10%
- Trade-off: 每类不同检测方法, 不能一刀切
- Tools: PSI for covariate, accuracy monitor for concept, label histogram, schema hash diff

**Framework 2**: Detection methods 矩阵
- When: 量化 drift
- Algorithm: 连续 numeric → KS test + PSI / categorical → chi-square / text-image → embedding centroid / 模型表现 → accuracy 滚动窗口 + ADWIN/DDM
- Trade-off: statistical first, ML-based 3 months 后 layer
- Tools: scipy.stats.ks_2samp, sklearn.metrics, sentence-transformers, alibi-detect ADWIN

**Framework 3**: 3 层 monitor 架构
- When: pipeline design
- Algorithm: Input monitor (schema / volume / null / freshness / KS) + Output monitor (+ business invariants + referential) + Feedback loop (online accuracy + 用户 complaints + A/B holdout)
- Trade-off: 3 层缺一不可, feedback loop 是 concept drift 唯一可见途径
- Tools: Great Expectations input, dbt tests output, custom feedback collector

**Framework 4**: Alert 减少疲劳 4 手段
- When: 监控部署
- Algorithm: stratification (P0/P1/P2) + dedup (1h window source × dim) + auto-resolve (30min stable) + calendar suppression (already-known surge days)
- Trade-off: 每加一层减疲劳, 加 1 false negative 风险
- Tools: Alertmanager dedup, PagerDuty / Slack tier, calendar JSON list

**Framework 5**: Remediation routing per dim
- When: alert fires
- Algorithm: schema → data-integration team P0 / volume → source team P1 / null spike → data-eng P1 / PSI → product-analytics P2 / concept → ml team P1 / constraint → data-eng P0
- Trade-off: routing 表 maintain 成本 vs 找对人 cost
- Tools: ROUTING_TABLE dict + alert manager rule

### 关键决策树 (ASCII)

```
出现 ML / agent quality 问题
   |
   v
Symptom 分类:
   - 上游字段变 → Schema drift
   - 模型输入分布变 → Covariate shift
   - 同 X 出 Y 概率变 → Concept drift (最难)
   - Y 分布变 → Label drift

Detection method:
   Numeric continuous → KS test (p<0.001) + PSI (>0.25)
   Categorical → chi-square
   Text/image → embedding centroid distance > 2× baseline radius
   Model performance → accuracy + ADWIN/DDM
   Schema → hash diff + Great Expectations

3 层部署:
   Input monitor (schema/volume/null/freshness/KS) — 80% RC catch
   Output monitor (+ business invariants + referential) — 15% RC
   Feedback loop (online accuracy + complaints + A/B) — 5% RC concept drift

Alert routing:
   Schema drift → integration team P0 (block + fix mapping)
   Volume drop → source team P1 (check upstream)
   Null spike → data-eng P1 (check nullable change)
   PSI drift → product-analytics P2 (business event)
   Concept drift → ml team P1 (trigger retrain)
   Constraint break → data-eng P0 (investigate)

Remediation playbook:
   Schema → 1.block 2.compare schema 3.contact upstream 4.update mapping 5.unblock 6.backfill
   Concept → 1.confirm 2.quantify per segment 3.decide (< 5% monitor / 5-10% retrain / > 10% rollback) 4.canary
   Volume → check source / ingestion / business event
```

### Part 2 五个深度问题速查

**Problem 1: 4 类 drift 各自检测**
- 核心解法: schema (hash diff Great Expectations) / covariate (PSI > 0.25 + KS) / concept (accuracy monitor + ADWIN) / label (histogram per class)
- Top 3 gotchas: PSI > 0.1 watch, > 0.25 alert / concept drift 需 label (delayed feedback / A/B holdout / surrogate signal) / 同 ts grant + revoke tie-break
- Tools: scipy KS test, sklearn isotonic, alibi-detect ADWIN, sentence-transformers embedding

**Problem 2: Detection methods 选型**
- 核心解法: numeric → PSI + KS / categorical → chi-square / text → embedding centroid distance > 2× baseline radius / 多 feature → model-based (binary classifier baseline vs current, AUC > 0.7 = drift)
- Top 3 gotchas: PSI / KS 单 feature, model-based 联合分布 / Wasserstein distance for general / embedding 75th percentile = normal radius
- Tools: scipy.stats, sklearn RandomForestClassifier, fastdtw

**Problem 3: 3 层 monitor 架构**
- 核心解法: Input (schema / volume / null / freshness / dist) + Output (business invariants / referential) + Feedback (accuracy / complaints / A/B); 80% catch from input, 15% output, 5% feedback (concept drift 唯一可见)
- Top 3 gotchas: 没 feedback loop concept drift 完全不见 / output 必含 cross-table 业务 invariants 不只 sum / freshness assert MAX(updated_at)
- Tools: Great Expectations input, dbt tests output, custom feedback ETL

**Problem 4: Alerting 阈值 + per-segment + 减疲劳**
- 核心解法: dynamic threshold (滚动 30d mean ± 3 SD) + per-segment baseline (market × tier × dow) + dedup (source × dim × 1h) + P0/P1/P2 stratification + calendar suppression
- Top 3 gotchas: 全局 mean 隐 per-segment 失败 / dedup 同窗口聚合不消失 / quarterly review tune low-precision alerts
- Tools: SegmentedBaseline class, AlertDedup, Prophet for seasonality

**Problem 5: Remediation pipeline (routing + playbook + audit)**
- 核心解法: routing per dim (schema → integration / volume → source / concept → ml / etc.) + per-playbook (schema = block + fix mapping + backfill / concept = quantify + retrain / volume = check 3 layers) + audit log 1y
- Top 3 gotchas: auto OK (scale / retrain-small / fillna-known) vs manual (schema / large concept / constraint) / dispute window 60d / SOC 2 audit chain of custody
- Tools: ROUTING_TABLE dict, RemediationOrchestrator, audit immutable log

### Production gotchas (top 15)

1. ML-based anomaly day 1 (black-box, no RCA)
2. Single threshold for all tables
3. 没 per-segment baseline (aggregate 隐)
4. 没 dedup (alert storm on single RC)
5. 没 P0/P1/P2 stratification (page on everything)
6. 没 routing (alert → #general, no owner)
7. 没 dashboard (only alerting, no situational awareness)
8. 过 aggregate (miss per-segment drift)
9. 没 calendar suppression (Black Friday 误报)
10. 没 audit log (customer dispute 无据可查)
11. 没 feedback loop (concept drift 完全不见)
12. 没分 4 类 drift, 同套阈值 cover schema + concept
13. Embedding centroid 没 baseline radius
14. Schema drift 没 severity (added column 不该 P0)
15. ML model retrain on biased label (human override 直接 fine-tune)

### 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Schema drift detection | Voice agent CRM 7 markets | phone_country_code 类型变, 没监控 → 95% join fail |
| Volume / freshness monitor | ConvFinQA eval pipeline | per quarter report freshness SLA |
| PSI for covariate | ConvFinQA stratified eval | 4 length buckets 类似分类思路 |
| Concept drift detected | Voice agent Indonesia | 春节经济压力 promise→fulfill rate 35% → 12% |
| Alert fatigue tuning | Voice agent 7 markets | per-market threshold, quarterly review precision < 30% remove |
| Per-segment baseline | Voice agent per-market | aggregate 隐 Indonesia 50% drop |
| Routing by dim | Voice agent failure | ASR team / LLM team / TTS team |
| Statistical first ML later | ConvFinQA RL alignment | z-score → PSI → Prophet seasonality, 3 mo 后才 ML detector |
| Audit log compliance | TikTok payment 7y retention | SOC2 / SOX immutable + hash-chained |

### 面试现场 quotables (top 8)

1. "4 类 drift: covariate P(X) / concept P(Y|X) / label P(Y) / schema. 真实分布 schema 40% / covariate 30% / concept 20% / label 10%."
2. "Statistical first, ML-based after 3 months stable. ML day 1 is a trap — black-box alerts no engineer can RCA."
3. "Concept drift 没 feedback loop 完全看不见. Input + Output monitor 抓 80%, feedback loop 抓 20% concept drift."
4. "PSI > 0.25 alert, > 0.1 watch. KS test p < 0.001 reject null. Chi-square for categorical."
5. "Per-segment baseline (market × tier × dow). Aggregate hides Indonesia 50% drop when Singapore +60% offsets it."
6. "ConvFinQA: aggregate metric hides 90% drift. Stratified per-length-bucket caught cascade where T0 errors compound."
7. "Voice agent monitoring: 6 dims (volume / freshness / schema / null / distribution / referential) → MTTR < 1h from 15-day silent corruption."
8. "Remediation per dim: schema → integration team block + fix mapping. Concept → ml team retrain. Volume drop → source team check upstream."

### 红线 (top 10 anti-patterns)

1. ML anomaly day 1 (black-box)
2. Single threshold for all tables
3. No dedup (alert storm)
4. No feedback loop (concept drift invisible)
5. No per-segment baseline
6. No routing (alert → #general)
7. Aggregate metric only
8. No calendar suppression
9. Mutable audit log (compliance fail)
10. Retrain on biased human label (amplify bias)

### 4 drift types vs detection method

| Drift type | Definition | Detection | Action |
|---|---|---|---|
| Covariate | P(X) 变, P(Y\|X) 不变 | PSI > 0.25 / KS p < 0.001 / chi-square cat | 通常不 retrain, watch |
| Concept | P(Y\|X) 变, model 跟不上 | Online accuracy + ADWIN / DDM | **必须 retrain** |
| Label | P(Y) 变 | Label histogram Δ > 5pp | Alert business + threshold |
| Schema | Field name / type 变 | Hash diff (Great Expectations) | Block downstream + fix mapping |

### Statistical test 选型表

| Data type | Method | Threshold | Tool |
|---|---|---|---|
| 连续 numeric | PSI | > 0.25 alert, > 0.1 watch | numpy + percentile bins |
| 连续 numeric | KS test | p < 0.001 reject null | scipy.stats.ks_2samp |
| Categorical | Chi-square | p < 0.001 reject null | scipy.stats.chi2_contingency |
| Text / image | Embedding centroid distance | > 2× baseline radius | sentence-transformers |
| Multi-feature | Model-based (binary classifier) | AUC > 0.7 | sklearn RandomForestClassifier |
| Universal | Wasserstein distance | application-specific | scipy.stats.wasserstein_distance |

### Routing per detected dim → owner

| Dim | Owner | Severity | Playbook |
|---|---|---|---|
| Schema drift | data-integration | P0 | block + diff + contact upstream + fix mapping + unblock + backfill |
| Volume drop | source-system team | P1 | check source / ingestion / business event |
| Volume surge | data-eng | P2 | check duplicate / scale pipeline |
| Null spike | data-eng | P1 | check upstream nullable change |
| PSI drift | product-analytics | P2 | investigate business event |
| Concept drift | ml-team | P1 | quantify + decide retrain / rollback |
| Constraint violation | data-eng | P0 | investigate data quality bug |

### 工具栈 (production)

| Tool | Use |
|---|---|
| Great Expectations | declarative assertions on ingest |
| Evidently AI | drift dashboards |
| Whylogs | profiling |
| Monte Carlo | data observability platform (SaaS) |
| Prophet | seasonality decomposition (interpretable) |
| Alibi-Detect | concept drift algorithms (ADWIN / DDM) |
| dbt tests | downstream output invariants |
| Pandera | schema enforcement Python |
| Soda Core | open-source data quality |

### 60-day phasing

| Week | Stage | Deliverable |
|---|---|---|
| 1-2 | Foundation: Volume / Freshness / Schema | Great Expectations setup |
| 3-4 | Null rate | per-column null % alert |
| 5-6 | Distribution drift | PSI / KS test on top 20 columns |
| 7-8 | Concept drift + feedback loop | accuracy monitor + A/B holdout |
| 9-10 | Routing + remediation playbooks | per-dim playbook + auto-remediation |

### 5 业务场景变体 (anchor stories)

| Variant | Drift type | Detection signal | Remediation |
|---|---|---|---|
| Voice agent Indonesia 春节 | Label drift (P(Y)) | promise_to_pay 35% → 12% | adjust prompt strategy + retrain classifier |
| ConvFinQA Q3 PDF template | Schema drift | column header hash diff | parser schema 自适应 + alert |
| BNPL chatbot recommender | Covariate (P(X)) | user_tenure_days 分布左移 (new user 5% → 30%) | retrain on recent 7d + segment model |
| Indonesia refund tier | Covariate (amount distribution shift) | mean refund +40% | dynamic threshold (滚动 30d 中位数) per-market |
| Risk model 通胀 | Concept (P(Y\|X)) | prediction vs realized 违约率差 | continuous weekly retrain |

### Alert fatigue reduction 4 mechanisms

| Mechanism | Effect | Implementation |
|---|---|---|
| Stratification P0/P1/P2 | page only critical | severity = (check_name, magnitude) → pager / slack / email |
| Dedup 1h | single RC → 1 alert not 50 | (source × dim) → 1 fire per hour, count累计 |
| Auto-resolve 30min stable | close auto when metric back | metric_history(last 30min) all OK → close |
| Calendar suppression | Black Friday / 春节 不报 | KNOWN_SURGE_DAYS list, volume alert suppressed |

### Audit log fields (data quality)

| Field | Type | Purpose |
|---|---|---|
| alert_id | uuid | unique identifier |
| fired_at | datetime | when |
| type | str | "schema_drift" / "volume_drop" / etc. |
| source | str | which pipeline / table |
| severity | "P0/P1/P2/P3" | priority |
| diff | dict | what changed |
| remediation | dict | playbook + actions + actors |
| resolved_at | datetime | when closed |
| mttr_minutes | int | mean time to resolution |
| owner | str | team responsible |
| audit_chain | list | each action with actor + ts + reason |

### Per-table baseline storage strategy

| Table importance | Threshold tightness | Sample rate | Retention |
|---|---|---|---|
| Critical (billing, regulatory) | strict (z > 2) | 100% | 1y |
| Important (model training) | medium (z > 3) | 100% | 90d |
| General (analytics) | lax (z > 5) | 10% | 30d |
| Toy / experiment | none | 1% | 7d |

