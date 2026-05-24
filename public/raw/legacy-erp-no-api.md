## 题目（verbatim）

> "Integrate your AI platform with a **15-year-old on-premise ERP** system that **lacks an API layer**. What's your approach?"

**出处**: fde.academy 经典 deployment scenario. Salesforce / Palantir / Databricks 都问过.

**Round**: Case Study (45-60 min)

---

## 这道题在考什么

考你**真实企业部署经验**. Enterprise customer 90% 都有 legacy 系统. 考点:

1. **You don't write your own ETL from scratch as plan A** — 是不是真做过 enterprise deployment
2. **6 个 integration patterns 你知道几个** — file drop, DB direct read, screen scraping, ESB, CDC, RPA
3. **Politics**: legacy ERP 通常 IT team 不让动. 怎么 navigate
4. **Risk staging**: read-only first, write much later
5. **Velocity-of-value beats elegance** — ship 丑的 file drop 比 build 完美的 API 快

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**ERP** (Enterprise Resource Planning): 企业资源规划. 整合公司**所有**核心业务流程的系统 — 财务、采购、库存、HR、生产、销售. 典型代表: **SAP** (R/3, ECC, S/4HANA), **Oracle EBS / NetSuite / JD Edwards**, **Microsoft Dynamics**, **Infor**, **Sage**.

为什么 enterprise 离不开: 一个订单从下单 → 库存扣减 → 财务记账 → 生产排程 → 出货 → 应收账款, 全部在一个系统里跑. 拔掉这个系统公司停摆.

**Legacy ERP**: 15 年前的 ERP, 典型特征:
- 在 customer 数据中心 on-premise (不是 cloud)
- 没有现代 REST API (那时还没成熟)
- 有些有 SOAP / RFC / IDoc 接口, 但难用
- 经过 N 次定制, schema 偏离原厂
- DBA 是 mid-50s 的老 SAP 顾问, 用过 SAP NetWeaver 7.0

**API layer**: 现代系统都有的 HTTP/REST/gRPC 接口. Legacy ERP 没有这一层, 但通常有几个 escape hatches:
- 数据库直连 (危险)
- 批量文件导出 (SFTP CSV)
- 厂商 RFC / SOAP 接口 (难用)
- BAPIs (SAP 内部函数模块)
- IDoc (SAP 文档交换)

**Adapter / Shim Service**: 你自己写的「胶水层」. 把 legacy ERP 的所有古怪接口包装成现代 REST / GraphQL, 让 customer 其他系统能用「正常」方式调用. **这是 FDE 部署后最常造的轮子**.

---

## 2. 这个问题的核心是什么

设想直接说「我们给你 build 个 API 然后接」的灾难:

```
Day 1:   你: "我们帮你给 SAP 加 API."
Day 7:   IT: "你不能动 SAP. 那是核心系统."
Day 14:  你: "那我们用 Python 直连数据库读."
Day 21:  DBA: "你不能直连 prod DB. 走 read replica."
Day 28:  你: "读 replica 也行, 给个连接串."
Day 35:  DBA: "需要 CTO 审批."
Day 60:  CTO 审批中.
Day 90:  你已经燃尽 1/4 项目预算, 还没读到 1 行数据.
```

**问题**:
- 一上来选了**最大变更路径** (build API), 撞 IT 红线
- 没找现有的「合法路径」 (BI team 已经在用 CSV)
- 没区分 read vs write — read 简单 100x
- 没意识到 ERP 集成 80% 是政治, 20% 是技术

**FDE 思维**:

```
Week 1: 找 customer 内部「已经在做的事」 — BI team 用什么读 SAP 的?
Week 2: piggyback 那个路径, 1 周给客户看到 value
Week 3+: 用 phase 1 的 political capital 谈下个 phase
Month 3+: 真正需要 real-time 时再上 CDC

核心: velocity-of-value beats elegance.
      Ship the ugly version first.
```

---

## 3. 6 个 Integration Pattern 决策树

```
                ┌────────────────────────────────────────┐
                │  Customer 内部 BI 已经在 read SAP?      │
                └────┬─────────────────────────────┬─────┘
                     │ YES                         │ NO
                     ↓                             ↓
              ┌──────────────┐              ┌──────────────────┐
              │ Pattern 1:   │              │  Need real-time? │
              │  File drop   │              └────┬─────────────┘
              │ (CSV/XML)    │                   │
              └──────┬───────┘                   │
                     │                          ↙ ↘
                     │              NO (hourly OK) YES (sub-min)
                     │                  ↓             ↓
                     │           ┌──────────────┐  ┌────────────────┐
                     │           │ Pattern 2:    │  │ Pattern 3:     │
                     │           │ DB read-only  │  │ CDC (Debezium  │
                     │           │ replica       │  │  binlog)       │
                     │           └───────────────┘  └────────────────┘
                     │
              Customer 已有 ESB / MQ?
                     │ YES
                     ↓
              ┌──────────────────┐
              │ Pattern 4:       │
              │ ESB (TIBCO/MQ)   │
              │ already running  │
              └──────────────────┘

兜底 (最后才选):
                ┌─────────────────────────────────────────┐
                │ Pattern 5: Vendor API (SOAP/RFC/BAPI)   │
                │   - SAP: BAPI, IDoc, RFC                │
                │   - Oracle: APEX, OIC                   │
                │   - 难用但官方支持                       │
                └─────────────────────────────────────────┘

绝对最后:
                ┌─────────────────────────────────────────┐
                │ Pattern 6: Screen scraping (RPA)        │
                │   - UiPath, Automation Anywhere         │
                │   - Brittle, maintenance nightmare      │
                │   - 仅当 IT 100% block 其他时           │
                └─────────────────────────────────────────┘
```

---

## 4. 6 Integration Pattern 详细分类表

| Pattern | 速度 | 数据延迟 | 风险 | 维护成本 | 适用 |
|---|---|---|---|---|---|
| **1. File drop (SFTP CSV/XML)** | 设置极快 (1 wk) | 高 (daily) | 极低 | 低 | IT 不让任何 live access; BI 已在用 |
| **2. Read-only DB replica** | 中 (3-4 wk) | 低 (30 min lag) | 低 (replica isolate) | 低 | DBA 配合 OK; 大表 OK |
| **3. CDC (Debezium / native log)** | 中 (4-6 wk) | 极低 (秒级) | 中 (需 DBA + ops) | 中 | Real-time 业务 case |
| **4. ESB / Message Bus** | 中 (4 wk) | 低-中 | 中 | 中 | 客户已有 TIBCO / IBM MQ |
| **5. Vendor API (BAPI/RFC/SOAP)** | 慢 (2-3 mo ramp) | 中 | 中 (vendor lock) | 高 | 官方支持的唯一方式 |
| **6. Screen scraping (RPA)** | 中 (1-2 wk) | 高 | 高 (UI 改就死) | 极高 | 没别选时的最后办法 |

**FDE 实战首选顺序**:
1. **File drop** — 最快 ship value
2. **DB read replica** — 后续升级
3. **CDC** — 真需要 real-time 才上

---

## 5. 具体业务场景

### 场景 A: Customer's SAP R/3 — 你最常遇到

**Setup**: 法国制造业客户, SAP R/3 用了 15 年. 你 deploy AI 库存预测.

**Reality check**:
- SAP 数据在 Oracle DB 后端, 几千张表 (MARA, MARC, MARD, MSEG...)
- IT 不让你碰 prod DB
- 但 BI team 每天凌晨从 SAP 导出 CSV 到 Snowflake

**Phase 1 (Week 1-2)**: 
- 你和 BI team 谈, 同样的 CSV 给你 read
- 你接 Snowflake, 你的 AI model 训练 + 推理用日级数据
- 部署 1 个 demo dashboard 给客户看

**Phase 2 (Month 2-3)**:
- 用 phase 1 ROI ($X saved by AI prediction) 谈 IT
- 申请 SAP 的 read-only Oracle replica (30 min lag)
- 你的 model 升级到 hourly

**Phase 3 (Month 4-6)**:
- 对真需要 real-time 的 use case (e.g., 关键品类的库存警报)
- 上 CDC (Oracle GoldenGate or Debezium)
- 延迟降到秒级

### 场景 B: Customer's NetSuite Cloud ERP — 看起来 modern 但…

**Setup**: SaaS NetSuite, 看似有 SuiteTalk REST API.

**Reality check**:
- 有 API 但**每天 5000 calls 限额**
- Schema 是 cryptic 业务 ID (script id 1234 = unknown)
- 客户 customize 太多, native API 返回 null

**Pattern**: SuiteAnalytics CSV export hourly + REST API 补充关键字段.

### 场景 C: Customer's Mainframe (COBOL 50 年)

**Setup**: 银行 / 保险公司, 主机 COBOL.

**Reality**:
- 数据在 IMS / DB2 大型机
- 没有任何「现代」接口
- 但有**夜间批量 ETL** 到一个 staging Oracle

**Pattern**: 接 staging Oracle. 永远不碰主机. 这是行业标准.

### 场景 D: 你的 TikTok PayLater 跨 7 markets — 直接对应这道题

类比:

```
TikTok PayLater Voice Agent 跨 7 markets repayment system:

Singapore (HQ): modern microservice ↔ REST API 直接接
Indonesia:      legacy monolith Java (15 yo) ↔ no API, only DB
Brazil:         vendor SaaS ↔ webhook + polling
Mexico:         legacy + new mix ↔ ESB

每个 market 用不同 pattern. 这就是这道题的真实生产版本.
```

你已经做过! 面试时直接 quote.

### 场景 E: Read-only 升级到 write-back (后续 phase)

写回 SAP 比 read 难 10x:

- **Never direct DB write** — 直接写 Oracle 会破坏 SAP 内部 consistency (触发器 / lock)
- **必须走 IDoc / RFC / BAPI** — SAP 官方文档接口, 有 transaction 保护
- **Compensating transaction** — 任何 write 都有 known rollback
- **Pilot single transaction type 60 days** — 不要一次开多种 write

---

## 6. 工程上要做什么 (实现 checklist)

**Phase 0 — Discovery (Week 1)**:

1. 跟 customer IT 谈: "你们 BI team 怎么读 SAP / ERP 的?"
2. 跟 BI / data engineering team 直接接触, 看现有 ETL
3. 调查 ERP 厂商 (是 SAP? Oracle? JDE? 各有不同 escape hatch)
4. 列出你的 use case 需要的具体数据 (哪些表 / 哪些字段)
5. 找出 customer 已有的 staging Snowflake / Redshift / on-prem warehouse

**Phase 1 — File drop baseline (Week 2-4)**:

6. 跟 BI 协调: 现有 CSV export 加 1 个 dump for AI use case
7. 你的服务接 SFTP / shared S3, 增量读取
8. Schema validation (上游变了就 alert)
9. 在你的平台跑 first AI model 用 day-1 数据
10. **部署 visible value** — 至少 1 个 dashboard / 1 个 insight 给客户看

**Phase 2 — DB replica (Month 2-3)**:

11. 用 phase 1 的 ROI 数据跟 IT 重谈
12. 申请 SAP DB 的 read-only replica
13. 你的 adapter 直读 replica
14. Schema mapping document (你要看的 20 张表 是哪些)
15. SAP analyst 时间 (mapping 20 张表通常 1-2 周)

**Phase 3 — CDC (Month 4-6)**:

16. 对真需要 real-time 的子集开 CDC
17. Debezium 监听 Oracle / SAP HANA log
18. Schema evolution handling
19. Backpressure (CDC stream 不能压垮你)
20. Recovery from gap (重新跑历史时)

**Phase 4 — Write-back (Month 6+)**:

21. 选一个 single transaction type
22. IDoc / BAPI 编码
23. Compensating transaction
24. 60 天 pilot, 错误率 < 0.01% 才扩展

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **直接说「build an API for them」** | 6 个月项目当 deployment 卖 |
| 2 | **Screen-scraping 当主方案** | Fragile + maintenance nightmare |
| 3 | **忽略 IT politics** | 技术方案再好, IT 不让也白搭 |
| 4 | **Read 跟 write 不区分** | Write-back 风险量级不同 |
| 5 | **没 phasing** | 直接上 CDC, IT 直接 block |
| 6 | **MDM 问题忽略** | 客户内部数据不一致是部署 blocker |
| 7 | **没 quick win 概念** | 6 个月才 deliver value, 客户已经放弃 |
| 8 | **忽略 schema drift** | SAP 升级 / 客户定制变更 break 集成 |
| 9 | **没 reconciliation** | Write-back 后没对账, 数据漂移不自知 |
| 10 | **没 SAP / Oracle analyst budget** | Schema mapping 卡死, 项目 stall |

---

## 一句话总结 (Part 1)

> **Legacy ERP integration = 「先 piggyback BI team 已有 CSV export 1 周 ship value, 再用 political capital 升级 DB replica, 真需要 real-time 才上 CDC, write-back 永远走 vendor API + compensating transaction」**.
>
> 这道题考的不是技术, 是**部署经验**: 你是不是真的进过一个 customer 数据中心, 跟 50 岁 DBA 谈过判过.

---

# Part 2 · 5 个深度工程问题

## ⚙️ Problem 1: Integration Option Ladder — 6 Pattern 详细比较 + 决策

**核心**: 不是单选, 是按 phase 升级. 不同 phase 适合不同 pattern.

### 1.1 Pattern 1: File Drop (CSV/XML over SFTP)

```
SAP → 每日凌晨 batch job → CSV 导出到 /export/customers.csv
       → SFTP 推到 BI 的 shared 服务器
       → 你的 adapter 拉去消费
```

**Code 示例**:

```python
# file_drop_adapter.py
import paramiko
import pandas as pd
from datetime import datetime, timedelta

class SFTPFileDropAdapter:
    def __init__(self, host, user, key_path):
        self.transport = paramiko.Transport((host, 22))
        self.transport.connect(username=user, pkey=paramiko.RSAKey(filename=key_path))
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)

    def pull_daily(self, date):
        """Pull yesterday's file, validate schema, parse"""
        filename = f'/export/customers_{date.strftime("%Y%m%d")}.csv'

        # Check .ready marker (don't read partial)
        marker = f'{filename}.ready'
        if not self.exists(marker):
            raise FileNotReady(f'{filename} not ready')

        # Pull
        local_path = f'/tmp/customers_{date}.csv'
        self.sftp.get(filename, local_path)

        # Validate schema
        df = pd.read_csv(local_path, dtype={'customer_id': str, 'balance': float})
        self.validate_schema(df)

        # Validate row count vs baseline
        if abs(len(df) - self.expected_rows_for(date)) > 0.05 * self.expected_rows_for(date):
            alert(f'Row count anomaly for {date}: {len(df)}')

        return df

    def validate_schema(self, df):
        expected_columns = {'customer_id', 'balance', 'last_update', 'status'}
        actual_columns = set(df.columns)
        if expected_columns - actual_columns:
            raise SchemaDriftError(f'Missing: {expected_columns - actual_columns}')

# usage
adapter = SFTPFileDropAdapter('bi.acme.com', 'ai_user', '/keys/ai.pem')
yesterday = datetime.now() - timedelta(days=1)
df = adapter.pull_daily(yesterday)
```

**Pros**: 政治成本最低, IT 已经在用; ramp-up 1 周; 无运维负担
**Cons**: T+1 延迟; 一旦上游 schema 变更没人通知; 大表 (1B 行) 不友好

### 1.2 Pattern 2: Read-only DB Replica

```
SAP Oracle DB → Active Data Guard / replication → Read replica (30 min lag)
                                                      ↓
                                              Your adapter connects
```

**Code 示例**:

```python
# replica_adapter.py
import oracledb
from contextlib import contextmanager

class OracleReplicaAdapter:
    def __init__(self, conn_string, user, pwd):
        self.pool = oracledb.create_pool(
            user=user, password=pwd, dsn=conn_string,
            min=2, max=10
        )

    @contextmanager
    def cursor(self):
        with self.pool.acquire() as conn:
            with conn.cursor() as cur:
                yield cur

    def query_customers(self, last_modified_after):
        """Incremental pull based on last_modified_ts"""
        sql = """
            SELECT customer_id, balance, status, last_update
            FROM SAP_OWNER.KNA1
            WHERE last_update > :since
            ORDER BY last_update
        """
        with self.cursor() as cur:
            cur.execute(sql, since=last_modified_after)
            return cur.fetchall()

    def detect_freshness(self):
        """Replica lag check"""
        sql = "SELECT (SYSDATE - MAX(last_update)) * 24 * 60 FROM KNA1"
        with self.cursor() as cur:
            cur.execute(sql)
            lag_minutes = cur.fetchone()[0]
            if lag_minutes > 60:
                alert(f'Replica lag {lag_minutes}min')
            return lag_minutes
```

**Pros**: 30-min 实时, 无 SAP server 影响; 可全 schema 查询
**Cons**: 需要 DBA 配合; schema 复杂 (SAP 几千张表); 跨模块 join 难

### 1.3 Pattern 3: CDC (Change Data Capture)

```
SAP Oracle DB
   ↓
Oracle GoldenGate / Debezium 监听 binlog (redo log)
   ↓
Kafka topic (per table)
   ↓
Your stream consumer
```

**Code 示例**:

```python
# cdc_consumer.py
from confluent_kafka import Consumer
import json

class CDCConsumer:
    def __init__(self, brokers, topics):
        self.consumer = Consumer({
            'bootstrap.servers': brokers,
            'group.id': 'ai_platform',
            'auto.offset.reset': 'earliest',
        })
        self.consumer.subscribe(topics)

    def consume(self):
        while True:
            msg = self.consumer.poll(timeout=1.0)
            if not msg:
                continue
            event = json.loads(msg.value())
            # Debezium format
            op = event['payload']['op']     # 'c' create, 'u' update, 'd' delete
            after = event['payload']['after']
            before = event['payload'].get('before')

            self.handle(op, before, after)
            self.consumer.commit(msg)

    def handle(self, op, before, after):
        if op == 'c' or op == 'u':
            self.upsert(after)
        elif op == 'd':
            self.delete(before)
```

**Pros**: 秒级延迟; 完整 change history; 无轮询
**Cons**: 运维复杂 (Kafka + Connector); DBA 需配合 enable binlog; 历史回放需 snapshot + log

### 1.4 Pattern 4: ESB / Message Bus

```
SAP → IDoc → TIBCO Bus / IBM MQ → Your subscribed listener
```

**适用**: 客户已经有 ESB. 不要 introduce 一个新 ESB just for you.

### 1.5 Pattern 5: Vendor API (SAP RFC/BAPI/IDoc, Oracle OIC)

**SAP-specific**:

```python
# sap_bapi_adapter.py
from pyrfc import Connection

class SAPBAPIAdapter:
    def __init__(self, ashost, sysnr, client, user, passwd):
        self.conn = Connection(
            ashost=ashost, sysnr=sysnr,
            client=client, user=user, passwd=passwd
        )

    def get_customer(self, customer_id):
        result = self.conn.call('BAPI_CUSTOMER_GETDETAIL', CUSTOMERNO=customer_id)
        if result['RETURN']['TYPE'] == 'E':
            raise SAPError(result['RETURN']['MESSAGE'])
        return result['CUSTOMERDATA']

    def update_customer(self, customer_id, fields):
        result = self.conn.call(
            'BAPI_CUSTOMER_UPDATE',
            CUSTOMERNO=customer_id,
            CUSTOMERDATA=fields
        )
        if result['RETURN']['TYPE'] == 'E':
            raise SAPError(result['RETURN']['MESSAGE'])
        # Commit
        self.conn.call('BAPI_TRANSACTION_COMMIT', WAIT='X')
```

**Pros**: SAP 官方支持; transaction 安全; 适合 write-back
**Cons**: 接口慢 (秒级 per call); 文档晦涩; pyrfc 库 finicky

### 1.6 Pattern 6: Screen Scraping (RPA) — 最后的选择

```python
# screen_scraping_adapter.py — ONLY IF DESPERATE
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

class SAPGUIScrapeAdapter:
    """绝对最后选择. 维护噩梦."""

    def __init__(self, sap_gui_path):
        # Selenium 操作 SAP GUI 或 Web client
        self.driver = webdriver.Chrome()

    def get_customer(self, customer_id):
        self.driver.get('https://sap.acme.com/customers')
        # 模拟用户点击
        self.driver.find_element(By.ID, 'customer_search').send_keys(customer_id)
        self.driver.find_element(By.ID, 'submit_btn').click()
        time.sleep(2)  # wait for load
        balance = self.driver.find_element(By.ID, 'balance').text
        return {'customer_id': customer_id, 'balance': float(balance.replace(',', ''))}
        # UI 改一个 class name 这代码就死
```

**为什么避免**:
- UI 升级 → 全部 selector 失效
- 难 parallelize (UI 是 sequential)
- 慢 (人类速度)
- 不稳定 (timing 问题)
- 看起来像被攻击 (anti-bot 触发)

仅当 IT **明确禁止**其他所有 pattern 时考虑.

---

## ⚙️ Problem 2: Adapter Layer / Shim Service Design

**核心**: 你要造一个 service, 把 legacy ERP 的多种古怪接口包装成现代 REST/GraphQL.

### 2.1 Adapter Architecture

```
┌────────────────────────────────────────────────┐
│       Your AI Platform / Other Services         │
└────────────────────┬───────────────────────────┘
                     │ REST/GraphQL API
                     ↓
┌────────────────────────────────────────────────┐
│            ERP Adapter Service                  │
│  ┌──────────┬───────────┬─────────┬─────────┐  │
│  │ Schema   │ Caching   │ Retry / │ Rate    │  │
│  │ Mapping  │ Layer     │ Backoff │ Limit   │  │
│  └──────────┴───────────┴─────────┴─────────┘  │
│  ┌──────────────────────────────────────────┐  │
│  │  Strategy Pattern: 不同 ERP 用不同 driver│  │
│  └──────────────────────────────────────────┘  │
└────┬───────────┬──────────┬────────┬───────────┘
     │           │          │        │
     ↓           ↓          ↓        ↓
  SFTP CSV    Oracle    Debezium   BAPI
  (Pattern 1) Replica    Kafka     RFC
              (Pattern 2)(Pattern 3)(Pattern 5)
```

### 2.2 Strategy Pattern 实现

```python
# adapter_strategy.py
from abc import ABC, abstractmethod

class ERPAdapter(ABC):
    @abstractmethod
    def get_customer(self, customer_id): pass
    @abstractmethod
    def list_orders(self, since): pass
    @abstractmethod
    def get_inventory(self, sku): pass

class FileDropAdapter(ERPAdapter):
    """从 CSV 读"""
    def get_customer(self, customer_id):
        # Cached file loaded
        df = self.cache.get('customers')
        if df is None:
            df = self.load_latest_csv('customers')
            self.cache.set('customers', df, ttl=3600)
        return df[df.customer_id == customer_id].to_dict('records')[0]

class ReplicaAdapter(ERPAdapter):
    """从 read replica 读"""
    def get_customer(self, customer_id):
        with self.cursor() as cur:
            cur.execute("SELECT * FROM KNA1 WHERE CUSTOMER = :id", id=customer_id)
            return self.row_to_dict(cur.fetchone())

class BAPIAdapter(ERPAdapter):
    """RFC call"""
    def get_customer(self, customer_id):
        return self.conn.call('BAPI_CUSTOMER_GETDETAIL', CUSTOMERNO=customer_id)

# 客户配置选择 strategy
ERP_TYPE = os.environ['ERP_TYPE']
ADAPTER_MAP = {
    'file_drop': FileDropAdapter,
    'replica': ReplicaAdapter,
    'bapi': BAPIAdapter,
}
adapter = ADAPTER_MAP[ERP_TYPE](config)
```

### 2.3 Caching Layer

```python
# cache.py
import redis
import json
import hashlib

class AdapterCache:
    def __init__(self):
        self.redis = redis.Redis()

    def get_or_fetch(self, key, fetch_fn, ttl=300):
        cached = self.redis.get(key)
        if cached:
            return json.loads(cached)
        value = fetch_fn()
        self.redis.set(key, json.dumps(value), ex=ttl)
        return value

# 用法
def get_customer_cached(customer_id):
    return cache.get_or_fetch(
        f'customer:{customer_id}',
        lambda: adapter.get_customer(customer_id),
        ttl=300
    )
```

**Cache TTL 设计**:
- High-volatility (库存): 30s
- Mid-volatility (客户 balance): 5 min
- Low-volatility (客户 master data): 1 hour

### 2.4 Schema Mapping (anti-corruption layer)

ERP 内部 schema 是 cryptic:

```
SAP KNA1 table:
  MANDT, KUNNR, NAME1, NAME2, ORT01, PSTLZ, ...

你的 API 应该返回:
  client_code, customer_id, name_line_1, name_line_2, city, postal_code
```

```python
# schema_mapping.py
SAP_FIELD_MAP = {
    'MANDT': 'client_code',
    'KUNNR': 'customer_id',
    'NAME1': 'name_line_1',
    'NAME2': 'name_line_2',
    'ORT01': 'city',
    'PSTLZ': 'postal_code',
    'LAND1': 'country_code',
}

def normalize_sap_customer(sap_row):
    return {our_name: sap_row[sap_name] for sap_name, our_name in SAP_FIELD_MAP.items()}

# 这样你 API 是 stable 的, SAP schema 变 (e.g., 字段重命名) 只在 mapping 改
```

### 2.5 Retry + Circuit Breaker

```python
# resilience.py
from tenacity import retry, stop_after_attempt, wait_exponential

class ResilientAdapter:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(SAPTransientError)
    )
    def get_customer(self, customer_id):
        return self.adapter.get_customer(customer_id)

# Circuit breaker
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_time=60):
        self.failures = 0
        self.threshold = failure_threshold
        self.recovery = recovery_time
        self.state = 'CLOSED'
        self.opened_at = None

    def call(self, fn, *args):
        if self.state == 'OPEN':
            if now() - self.opened_at > self.recovery:
                self.state = 'HALF_OPEN'
            else:
                raise CircuitOpen('ERP unavailable')

        try:
            result = fn(*args)
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
            self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            if self.failures >= self.threshold:
                self.state = 'OPEN'
                self.opened_at = now()
            raise
```

---

## ⚙️ Problem 3: Data Sync Patterns — Batch vs Streaming, CDC, MQ

**核心**: 不同数据有不同 sync 模式. 一个项目可能同时跑 4 种 sync.

### 3.1 Pattern matrix

| Data type | Freshness need | Volume | Sync pattern |
|---|---|---|---|
| Customer master | Daily | 100K rows | Full reload nightly batch |
| Customer master delta | Hourly | < 1K updates | Incremental (timestamp-based) |
| Orders / transactions | Real-time | 10K/day | CDC + Kafka |
| Inventory | Sub-minute | 10K SKU | CDC + Kafka |
| GL / accounting | Monthly close | 1M rows | Full batch, month-end |
| Master data (rare changes) | Weekly | < 1K | Full reload weekly |

### 3.2 Batch reload pattern

```python
def nightly_full_reload():
    """Atomic full reload to avoid partial state"""
    # 1. Stage new data
    df = adapter.pull_full('customers')

    # 2. Write to staging table
    staging_table = 'customers_staging'
    write_df(df, staging_table)

    # 3. Atomic swap
    db.execute("""
        BEGIN;
        ALTER TABLE customers RENAME TO customers_old;
        ALTER TABLE customers_staging RENAME TO customers;
        DROP TABLE customers_old;
        COMMIT;
    """)
```

### 3.3 Incremental (timestamp-based)

```python
def incremental_pull():
    """每小时只拉 last_modified > previous_pull_ts 的数据"""
    state = db.get('last_pull_ts', table='customers') or '1970-01-01'

    new_rows = adapter.query_customers(since=state)

    for row in new_rows:
        db.upsert('customers', row, key='customer_id')

    # 更新 state
    new_state = max(row['last_modified'] for row in new_rows) if new_rows else state
    db.set('last_pull_ts', new_state, table='customers')
```

**陷阱**: timestamp-based 不能处理 hard-delete. 如果 SAP 删了一个客户, 你这边永远存在.

**Mitigation**: 周期性 full reconcile (e.g., weekly), 对账后清理孤儿记录.

### 3.4 CDC pattern

```python
def cdc_handler():
    """从 Kafka 消费 change events"""
    consumer = create_consumer('sap.kna1')
    for event in consumer:
        op = event.op   # c / u / d
        if op == 'd':
            db.delete('customers', key=event.before['KUNNR'])
        else:  # c / u
            db.upsert('customers', normalize(event.after), key='customer_id')

        # Commit offset
        consumer.commit()
```

**陷阱**:
- **At-least-once delivery**: 同一 event 可能消费两次 → idempotent upsert
- **Ordering**: 同一行的 update 必须按顺序 — partition by primary key
- **Schema evolution**: SAP 加字段, Debezium event 加字段, 你的 parser 要兼容
- **Bootstrap**: 起服务时已有数据怎么 sync? Snapshot + 从 snapshot point 开始 CDC

### 3.5 Reconciliation (对账)

**永远要做**: 定期 reconcile 你的 mirror 跟 ERP 真实数据.

```python
def daily_reconciliation():
    """对账"""
    # 抽样 1% 客户 hard compare
    sample_customers = db.sample('customers', n=1000)

    discrepancies = []
    for c in sample_customers:
        truth = adapter.get_customer(c.customer_id)
        if truth.balance != c.balance or truth.status != c.status:
            discrepancies.append({
                'customer_id': c.customer_id,
                'our_value': c.balance,
                'erp_value': truth.balance,
            })

    if len(discrepancies) > 5:
        alert(f'reconciliation found {len(discrepancies)} discrepancies')

    # Auto-fix
    for d in discrepancies:
        db.update('customers', key=d.customer_id, balance=d.erp_value)
```

### 3.6 Backpressure

CDC stream 大量更新时 (e.g., month-end 批处理):

```python
class BackpressureConsumer:
    def __init__(self, max_inflight=1000):
        self.semaphore = asyncio.Semaphore(max_inflight)

    async def consume(self, msg):
        async with self.semaphore:
            await self.handle(msg)
            self.commit(msg)

    # 如果下游 (你的 DB) 写慢, semaphore 会限制上游消费速度
    # 而不是 OOM
```

---

## ⚙️ Problem 4: Failure Modes + Reconciliation

**核心**: ERP 集成 production 后会遇到的 5 类问题, 每类需要 detection + auto-fix.

### 4.1 Schema drift

**问题**: SAP 升级 / 客户定制 → 列名变了 / 新列加了 / 列类型变了 → 你 parser 死.

```python
class SchemaDriftDetector:
    def __init__(self, expected_schema):
        self.expected = expected_schema

    def check(self, actual_schema):
        added = set(actual_schema) - set(self.expected)
        removed = set(self.expected) - set(actual_schema)

        if removed:
            return {'severity': 'critical', 'reason': f'removed: {removed}'}
        if added:
            return {'severity': 'warning', 'reason': f'new fields: {added}'}
        return {'severity': 'ok'}

# Daily check
def daily_schema_check():
    actual = adapter.describe_table('KNA1')
    result = drift_detector.check(actual)
    if result['severity'] == 'critical':
        alert(result['reason'])
        pause_ingest('KNA1')
    elif result['severity'] == 'warning':
        log(result['reason'])
        # 自动加新 nullable 列
        auto_add_columns(actual)
```

**Best practice**: customer 改 ERP schema 前必须 notify 你 (合同条款).

### 4.2 Data quality issues

**典型**:
- NULL 在 not-null 字段
- 重复 customer_id
- Encoding issue (latin-1 客户名出现在 UTF-8 期望)
- 数字字段含字符 ("N/A")
- 时区 mixed (有 UTC, 有 local)

```python
def data_quality_validator(df):
    issues = []
    if df['customer_id'].duplicated().any():
        issues.append('duplicate customer_id')
    if df['customer_id'].isna().any():
        issues.append('null customer_id')
    if not df['balance'].apply(lambda x: isinstance(x, (int, float))).all():
        issues.append('non-numeric balance')
    return issues
```

### 4.3 Reconciliation patterns

```python
class Reconciler:
    """3 层 reconciliation"""

    def row_count_check(self):
        """快速 sanity: ERP 总行数 vs 我们的"""
        erp_count = adapter.count('KNA1')
        our_count = db.count('customers')
        if abs(erp_count - our_count) > erp_count * 0.001:
            alert(f'count mismatch: ERP {erp_count}, ours {our_count}')

    def sample_diff(self, sample_size=1000):
        """抽样深度对比"""
        sample = db.sample('customers', n=sample_size)
        for c in sample:
            truth = adapter.get_customer(c.customer_id)
            if not deep_equal(truth, c.to_dict()):
                yield diff(truth, c)

    def daily_aggregate_check(self):
        """聚合 metric 对账 (e.g., total open AR)"""
        erp_total_ar = adapter.query("SELECT SUM(BALANCE) FROM KNA1 WHERE STATUS='OPEN'")
        our_total_ar = db.query("SELECT SUM(balance) FROM customers WHERE status='open'")
        if abs(erp_total_ar - our_total_ar) > 0.001 * erp_total_ar:
            alert(f'AR mismatch: ERP ${erp_total_ar}, ours ${our_total_ar}')
```

### 4.4 Idempotent write-back

Write-back to ERP 必须 idempotent:

```python
def update_customer_idempotent(customer_id, fields):
    # 1. Generate idempotency key
    idempotency_key = hashlib.sha256(
        json.dumps({'customer_id': customer_id, 'fields': fields}, sort_keys=True).encode()
    ).hexdigest()

    # 2. Check if we already wrote this
    if write_log.exists(idempotency_key):
        return write_log.get_result(idempotency_key)

    # 3. Write
    try:
        result = adapter.update_customer(customer_id, fields)
        write_log.record_success(idempotency_key, result)
        return result
    except Exception as e:
        write_log.record_failure(idempotency_key, str(e))
        raise
```

### 4.5 Compensating transactions

```python
def compensating_pattern(customer_id, new_balance):
    """If write fails midway, undo it"""
    # 1. Read current state
    old_balance = adapter.get_customer(customer_id).balance

    # 2. Try update
    try:
        adapter.update_customer(customer_id, balance=new_balance)
    except WriteFailedError:
        # 没写成功, 不需要补偿
        raise

    # 3. Verify
    actual = adapter.get_customer(customer_id).balance
    if actual != new_balance:
        # 写了但状态不对? Try rollback
        try:
            adapter.update_customer(customer_id, balance=old_balance)
        except:
            alert(f'failed to rollback customer {customer_id}, manual intervention')
        raise WriteVerificationFailed
```

---

## ⚙️ Problem 5: Vendor Relationship + IT Politics

**核心**: 60% of ERP integration battles are political, not technical.

### 5.1 IT politics map

```
Players in customer:
  CIO         — strategic decision, 你不需要每天见
  IT Director — 实际审批人, 你需要 fortnight check-in
  DBA / Data Lead — 决定 DB access yes/no, 你需要每周 sync
  BI / Data Eng team — 已有 ERP read pattern, 你的最佳盟友
  SAP Functional 顾问 — 知道 schema 业务含义, 你需要 5 小时/周
  Vendor (SAP / Oracle) — 决定 license / support, 谨慎
  Business sponsor — 你的需求来源, 但他们不懂 IT
```

### 5.2 Anti-pattern: 上来直接找 CIO

```
You: "Hi CIO, we want to add API to your SAP"
CIO: "Why? Submit to architecture review board."
   ↓
ARB: "Why? Show ROI. SLA. Risk assessment."
   ↓
3 months later: 项目还没启动.
```

### 5.3 正确 pattern: BI team 先盟友化

```
You: "Hey BI team, what data do you read from SAP today?"
BI:  "We get nightly CSV dumps for our Tableau dashboards"
You: "Can we get the same CSV? Same security model, same access."
BI:  "Sure, no problem."
   ↓ 1 week later: you have data flowing
   ↓ ROI 在跑
   ↓ CIO 看到 dashboard 上的 ROI
   ↓ CIO 主动问 "你们想加快吗?"
```

**Key insight**: piggyback existing approved patterns. 不要请求新东西.

### 5.4 政治成本 vs 技术升级 决策表

| Phase | 政治成本 | 技术 effort | Value Delivery |
|---|---|---|---|
| Piggyback CSV | 极低 (已 approved) | 1 wk | 70% value |
| Read replica | 中 (需 DBA approve) | 3-4 wk | 90% value |
| CDC | 高 (需 ops capacity) | 4-6 wk | 95% value |
| Vendor API write | 极高 (需 finance signoff) | 2-3 mo | 100% value (write-back) |

**FDE 战略**: 永远只升级到「下一级别足够 unlock value」, 不要 over-engineer.

### 5.5 Reciprocal value to IT

IT 团队**不喜欢被卖方使唤**. 给他们一些反向 value:

```
你给 IT 的反馈:
  "我们发现你们 KNA1 表里 0.3% 数据有重复 customer_id, 
   这是 list 给你们 fix."

  "我们的 schema validation 跑了 30 天, 
   发现你们 SAP last upgrade 把 NAME2 默认值改了. Heads up."

  "我们的 reconciliation 找到 14 个 ghost 客户 
   (KNA1 有但 KNVV 没有), 你们想看吗?"
```

IT 突然觉得你是「来帮我们 fix 数据」的, 不是「来加负担」的. 这是 long-term 关系.

### 5.6 跟你 TikTok 7-markets 经验对应

你跨 7 markets 处理本地 IT 团队, 直接 reframe:

| Healthcare/Logistics ERP politics | Your TikTok 7-market |
|---|---|
| CIO / IT Director hierarchy | Country head / regional ops director |
| BI team as ally | Local data team |
| DBA approval | Local compliance officer |
| Reciprocal value (data quality) | Bug fix / monitoring contribution |
| Cultural difference (US vs SEA) | Indonesia vs Brazil vs Mexico |
| Slow approval cycle | Government regulator review |

### 5.7 处理 vendor (SAP / Oracle)

```
Vendor 跟你的关系是 "co-opetition":
  - 他们 sell SAP license, 你 sell AI on top
  - 你 read SAP 数据 → 他们 OK
  - 你 write SAP 数据 → 他们想自己卖 module
  - 你帮 customer 减 SAP usage → 他们不爽

策略:
  - 早期 transparent — 告诉 SAP "we're complementary"
  - 用 BAPI / IDoc (官方接口) 不用 hack
  - SAP rep 在 customer 现场时, 你态度 collaborative
  - 不要在 customer 面前 trash SAP — 客户依赖 SAP 比依赖你深
```

---

# Part 3 · 把 5 个问题串起来看

这 5 个 layer 拼起来就是 legacy ERP integration 的全栈:

1. **Pattern ladder** (Problem 1) — 6 个 pattern, 选最匹配 phase 的
2. **Adapter design** (Problem 2) — Strategy + Cache + Schema map + Retry + CB
3. **Sync patterns** (Problem 3) — Batch / Incremental / CDC / Reconcile 各有用途
4. **Failure modes** (Problem 4) — Schema drift / DQ / Idempotency / Compensating
5. **Politics** (Problem 5) — BI ally → Reciprocal → Reciprocal capital → Upgrade

面试场全栈讲明 + quote 你 7-market voice agent 经验 = 真 FDE-staff level.

---

## 必问 clarifying questions

**1. What ERP**

> "Which ERP — SAP R/3, S/4HANA, Oracle EBS, JDE, NetSuite, custom Java? Each has different escape hatches."

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
| 10-25 min | 6 integration patterns, rank by velocity + risk |
| 25-40 min | Recommend pattern + design adapter |
| 40-50 min | Failure modes + how to convince IT |
| 50-60 min | Phasing read-only → write |

---

## 简历专属 reframe

你的 **BNPL chatbot** + **voice agent** 都涉及 enterprise integration:

| Legacy ERP 题 | 你的经验 |
|---|---|
| Integrate without official API | BNPL chatbot 跨 ByteDance 内部多系统, 同款痛点 |
| Read-only replica → CDC ramp | Voice agent 接 7 markets repayment system 真做过 |
| Politics with IT team | 跨 product / ops / regional 7 markets, 政治经验丰富 |
| Phase 1 visible value | Refund tier scoping "70% throughput at 0% risk" 同款 pattern |
| Don't screen-scrape | Voice agent ASR/TTS 真接生产 system, 不靠 UI hack |
| Adapter pattern | Internal Agent Platform 应该有 abstraction |
| Schema drift | Voice agent 上游 schema 漂移你处理过 |
| Compensating transaction | Indonesia refund tier 设计就有 |

**主动说**:

> "I've seen this exact shape at ByteDance Global Payment — we needed to integrate the voice agent with regional repayment systems that ranged from modern microservices in Singapore to **15-year-old monolith in one market**. We started with **CSV exports the BI team already had**, deployed v1 in 2 weeks, then later upgraded that one market to CDC via Debezium once we had political capital from the v1 ROI.
>
> The lesson I'd carry forward: **velocity-of-value beats elegance — ship the ugly thing first**. The CSV adapter took 1 week and was good enough for daily prediction. The CDC took 2 months and unlocked the last 5% of value. If we'd started with CDC, we'd have been stuck in IT approvals for 2 months with zero data flowing.
>
> The other thing I learned: **be the data quality champion to IT**. When we found 0.3% duplicate customer IDs in their SAP, we reported it instead of working around it. That gave us long-term goodwill — they started inviting us to architecture reviews."

---

## 5 个 follow-ups

**Q1**: "IT 团队完全拒绝任何 DB access, 只能 file drop."

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
- **Idempotency key** — every write tagged so retry doesn't double-write.

**Q3**: "SAP analyst time is unavailable to map schema. Stuck."

**A**: 3 options:
1. **Reverse-engineer from CSV exports** — what data shapes are already coming out? Use that as truth.
2. **Hire a 3rd-party SAP consultant** (3-day engagement, $5k) to map the 20 tables we care about.
3. **Pay client's BI vendor** (whoever maintains BI today) to give us their schema docs.

This is **a budget question, not a technical question**.

**Q4**: "Customer wants us to upgrade their ERP itself. Scope explosion?"

**A**: Hard no. 政治 + 技术 + 时间都不允许. Frame:
- "Upgrading SAP is a 2-year, $5M project that needs an SI partner. We're not that vendor. We can **make your old SAP look modern from the AI side** without touching SAP itself."
- Offer to **introduce them to an SI partner** for ERP modernization — get goodwill without owning that risk.

**Q5**: "How do you handle SAP schema changes mid-deployment?"

**A**:
- **Schema versioning**: tag each ingest with SAP schema version (e.g., date of last DDL change). Customer notifies us before changes.
- **Backward-compatible reads**: our ingestion code handles N and N-1 schemas, sunsets old after 90 days.
- **Schema diff alerts**: nightly cron diffs DB schema, alerts to FDE.
- **Adapter layer absorbs change**: our internal API stable, adapter changes when SAP schema does.

---

## ❌ 易错点

1. **直接说「build an API for them」** — 6 个月项目当 deployment 卖
2. **Screen-scraping 当主方案** — Fragile + maintenance nightmare
3. **忽略 IT politics** — 技术方案再好, IT 不让也白搭
4. **Read 跟 write 不区分** — Write-back 风险量级不同
5. **没 phasing** — 直接上 CDC, IT 直接 block
6. **MDM 问题忽略** — 客户内部数据不一致是部署 blocker
7. **没 quick win 概念** — 6 个月才 deliver value, 客户已经放弃
8. **没 schema drift detection** — 客户改 schema 后你 silently 死掉
9. **没 idempotency on write** — Retry 导致 double-write
10. **不 reconcile** — Mirror 跟 ERP 飘了不知道

---

## ✅ 加分项

1. **Piggyback on existing BI export** — minimum IT effort, fast value
2. **6 patterns 排序 by velocity + risk** 主动说
3. **Phase 1 value before asking for more** — political capital strategy
4. **Compensating transaction for write-back** — show production safety mindset
5. **MDM identified as 6mo blocker** — surface real risk
6. **Refer SAP SI partner for upgrade** — politically savvy
7. **Adapter Strategy pattern + Schema map + CB** 技术深度
8. **Reciprocal value to IT (data quality reports)** 关系建立
9. **Reconciliation 3-tier** (count + sample + aggregate)
10. **Quote your TikTok 7-market experience** — 15-year-old monolith integration

---

## 一句话总结

> **Legacy ERP integration = 「先 piggyback BI team CSV 1 周 ship value, adapter layer 抽象 + cache + retry + schema map, 再用 political capital 升级 DB replica → CDC, write-back 永远 vendor API + compensating + idempotent + 60 天单 transaction type pilot」**.
>
> 60% 是政治, 40% 是技术. 没在 customer 数据中心跟 DBA 谈判过的人答不出这道题.

---

## Cheat Sheet

```
6 integration patterns ranked by FDE preference:
  1. File drop (existing BI export) — fastest, lowest risk
  2. Read-only DB replica — moderate
  3. CDC (Debezium / native log) — real-time read
  4. ESB (TIBCO/MQ) — if customer already has
  5. Vendor API (BAPI/RFC/IDoc/SOAP) — for write
  6. Screen-scraping — NEVER unless desperate

3-phase rollout:
  Phase 1 (2 wk): File drop, daily, visible value
  Phase 2 (2 mo): Read-only replica, 30min lag
  Phase 3 (4 mo): CDC for real-time use cases
  Phase 4 (6mo+): Single transaction type write-back

Adapter design (4 layer):
  Strategy: per-ERP driver (file_drop / replica / bapi)
  Cache: Redis with tiered TTL
  Resilience: Tenacity retry + Circuit breaker
  Schema map: anti-corruption layer (KNA1 → customer)

Sync patterns matrix:
  Master data: daily full reload
  Master delta: hourly incremental (timestamp)
  Transactions: CDC + Kafka
  Aggregate: month-end batch
  + Weekly reconciliation (3-tier)

Politics tactics:
  - Piggyback what IT already does
  - Show value before asking for more
  - Get DBA / data lead as ally first
  - Offer reciprocal value (data quality fix)
  - DPA / paperwork upfront

Write-back patterns:
  - Never direct DB
  - IDoc / RFC / BAPI only (SAP)
  - Stage + batch + reconciliation
  - Compensating transactions
  - Idempotency key
  - Pilot 1 transaction type, 60 days

Failure modes 5 类:
  Schema drift: auto-detect daily, alert critical
  Data quality: validator pre-ingest
  Idempotency: hash key on write
  Compensating: rollback on partial failure
  Reconciliation: count + sample + aggregate

红线:
  - Don't screen-scrape unless desperate
  - Don't promise ERP upgrade
  - Don't promise write-back v1
  - Don't ignore MDM if data inconsistent
  - Don't go to CIO before BI team

Quote opportunity:
  "TikTok PayLater 7 markets — Singapore microservice,
   Indonesia 15yo monolith no API. CSV → replica → CDC ramp."
```

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

