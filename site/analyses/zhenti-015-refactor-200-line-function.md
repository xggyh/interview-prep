## Q15 · 把 200 行函数重构成可测试的, 讲清思路

> "Here's a 200-line function from our codebase. **Refactor it** so it's testable, readable, and maintainable. **Walk us through your reasoning** as you go. We care more about your process than the final code."

**Round**: Coding (60 min, shared screen)
**出处**: Exponent 2026 FDE · 公司: **Palantir** (经典), Anthropic, Anyscale
**难度**: Medium (但 process 是关键, 不是 algo)
**主要技能**: 工程素养, 单一职责, 依赖反转, communication

---

## 📖 术语速查 (本题用到的)

> 重构题的术语都是 "工程素养" 词. 知道这些, 跟面试官同频. 不知道 = 听不懂面试官在 reference 哪个 pattern.

### 设计原则 / SOLID

| 术语 | 解释 |
|---|---|
| **Single Responsibility Principle (SRP)** ⭐ | "一个 class/function 只有一个变更理由". 这题 before 有 6 个 (validate, query, fee, fraud, persist, notify) → 必须拆. |
| **Dependency Injection (DI)** ⭐ | 依赖通过构造函数/参数传入, 而不是全局 import. 让 test 可注入 fake. |
| **Dependency Inversion** | 高层模块不依赖低层模块, 都依赖抽象 (Protocol / Interface). 这题: handler 不依赖 `psycopg`, 只依赖 `UserRepo` Protocol. |
| **SOLID** | S (SRP), O (Open-Closed), L (Liskov), I (Interface Segregation), D (Dependency Inversion). OO 设计经典 5 原则. |
| **Functional core, imperative shell** ⭐ | 内核 pure function, 外壳负责 I/O. 这题: validators / fees / tier 是 pure; adapters / handler 是 imperative. |
| **Pure function** | 同 input 同 output, 无 side effect, 无 mutation. 测试 trivial. |
| **Side effect** | DB 写, 文件写, 网络调用, 全局变量改. 必须 inject 才好测. |

### Python 语言特性

| 术语 | 解释 |
|---|---|
| **`@dataclass`** | 自动生成 `__init__/__eq__/__repr__`. 替代手写 boilerplate class. |
| **`Protocol` (PEP 544)** ⭐ | Python 的 structural subtyping. "duck typing 加类型注解" — 不需 inherit, 只要符合接口就行. 这题用来定义 `UserRepo / TxRepo` 等 ports. |
| **`@dataclass(frozen=True)`** | immutable dataclass. 防意外 mutation. |
| **Walrus operator `:=`** | Python 3.8+ 赋值表达式. `if err := validate(...)` 一行赋值 + 判断. |
| **Type hint `User \| None`** | Python 3.10+ union 类型. 等价 `Optional[User]`. |
| **`mypy --strict`** | 静态类型 checker. CI 强制就抓 90% 类型 bug. |

### 重构 patterns

| 术语 | 解释 |
|---|---|
| **Characterization test** ⭐ | "锁住现行行为" 的 test. 在改之前写, 改之后必须仍 pass. **Refactor 必备**. |
| **Extract function** | 把一段 inline 代码抽成函数. Refactor 最基本动作. |
| **Adapter pattern** | 包外部 lib (e.g. `psycopg`, `requests`) 进自己的接口. 让 lib 可替换. |
| **Repository pattern** | 数据访问抽象 (`UserRepo.get_user`). 隐藏 SQL / DB 细节. |
| **Strangler pattern** ⭐ | 老系统不删, 新系统逐步替换调用方, 最终老系统空了再删. 大 refactor 安全姿势. |
| **Strategy pattern** | 把行为 plug-in 化 (e.g., 多 region 各自 rule 实现). |
| **Branch by abstraction** | 不开 feature branch, 而是在 trunk 加抽象层, 灰度切流量. |
| **Shadow traffic** | 旧/新 handler 同时跑, 比较输出, 0 diff 后切流. |
| **Feature flag** | `if FEATURE_X: new_path else: old_path`. 灰度上线, 出错回滚. |

### Code smells (代码坏味道)

| 术语 | 解释 |
|---|---|
| **Magic number** | 没名字的常量 (`100000`, `0.78`). 改一处要全局搜. |
| **Tuple positional access** | `user[1]` 看不出意思. 改 dataclass: `user.status`. |
| **Nested if 3+ levels** | 嵌套太深, 难读. 用 early return / 提 helper. |
| **Long parameter list** | 7+ 参数. 改 dataclass / config object. |
| **God function** | 一个函数干所有事 (这题 before). 必拆. |
| **Global state** | 模块级 `db_conn = ...`. 不能 mock, 测试痛苦. |
| **Implicit error** | `except: pass` 静默吞错. 看不到失败原因. |

### 测试 / CI

| 术语 | 解释 |
|---|---|
| **Unit test vs integration test** | Unit = 单组件 with fakes; integration = 真 DB / 真 HTTP. Unit 快 (ms); integration 慢 (s). |
| **Fake vs Mock vs Stub** ⭐ | Fake = in-memory 真实现 (`FakeUserRepo`); Mock = 验证 call 的对象; Stub = 返预设值. 这题用 fake 比 mock 干净. |
| **`unittest.mock.patch`** | Python mock 用 monkey-patch 替换模块属性. characterization test 用. |
| **Frozen clock** | test 时 inject 固定时间, 避免 flaky. `FrozenClock` 是 fake. |
| **Cyclomatic complexity** | 函数分支数衡量. 这题 before 25 (高), refactor 后每个 ≤ 10. |
| **Coverage %** | 测试覆盖的代码行比例. 0% → 95% 是重构成功标志. |
| **CODEOWNERS** | GitHub 文件: 谁要 review 改某文件. |
| **`git mv`** | Git 重命名 + move, 保留 blame history. |
| **CI / Pre-commit hook** | 提交前自动跑 lint / test. `ruff`, `mypy`, `pytest`. |
| **`ruff`** | Rust 写的 Python linter, 比 `flake8` 快 100x. |

### 业务术语 (BNPL refund 上下文)

| 术语 | 解释 |
|---|---|
| **BNPL (Buy Now Pay Later)** | 先享后付 — Klarna / Afterpay / TikTok PayLater. 用户分期付款. |
| **Refund** | 退款. 这题 handler 处理 refund 决策 (auto vs manual). |
| **Tier (AUTO / MANUAL)** | 自动放行 vs 走人工 review. 业务规则决定. |
| **VIP user / Pro tier** | 高价值用户. 通常 fee 减免 + 阈值放宽. |
| **Chargeback vs Refund** | Chargeback 是持卡人投诉发卡行 + 银行强扣 (有罚款); Refund 是商户主动退. |

---

## 这道题在考什么

这道题最容易低估. 大多数候选人觉得"重构就是切几个函数嘛", 然后 30 分钟切完, 面试官说"你的过程比结果重要" → 跪. 真正考的是:

1. **能不能边写边讲思路** — silent 重构 = 0 分
2. **能不能识别 code smell 并 verbalize** — "这里 nested if 太深", "这个名字 vague", "I/O 和 logic 混了" — 说出来
3. **重构 step 是不是 incremental** — 每一步改完跑测试, 不要 big-bang rewrite
4. **测试 first 还是 last** — production refactor 标准: 先 characterization tests 锁住现有行为, 再改
5. **能不能识别 pure vs side-effect** — 纯函数 / I/O / side effect 怎么分层
6. **抽象 layer 是不是合理** — 不要过度 OOP, 也不要 100% 函数式
7. **Trade-off 表达** — "我可以再抽一层, 但 cost 大于 benefit, 暂时不动"
8. **Customer empathy** — 这是 production code 不是 toy; 改坏 = 客户受伤

Palantir 真问题: 客户 codebase 一个 audit_invoice() 函数 500 行, 是 6 个 engineer 5 年加起来的, 测不动. 把它弄能测的是日常.

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|------|--------|--------|
| 1 | Read + comment | 0-10 min | 通读, 出声标注 smell | "Let me read this first. As I do I'll call out code smells." |
| 2 | Clarify | 10-12 min | 问 callers, side effects, hot path | "Before refactoring: who calls this?" |
| 3 | Characterization tests | 12-22 min | 写 3-5 个 black-box tests 锁现行行为 | "Don't refactor without a safety net — let me write tests first." |
| 4 | Refactor step-by-step | 22-50 min | extract → rename → inject → simplify, 每步跑 test | "Step 1: extract validate_..." |
| 5 | Review | 50-55 min | diff before/after, what's testable now | "Before: 200 LoC, 0 unit tests. After: 6 small funcs, 14 tests." |
| 6 | Trade-offs | 55-60 min | what I didn't do, why | "I left X coupled because Y..." |

---

## 必问 clarifying questions

**1. Who calls this function?**

> "What's the call site? Is it a hot path (1000 QPS) or once-a-day cron?"

Why: 决定能不能 introduce overhead (e.g., DI 多一层 dispatch).

**2. Side effects?**

> "DB writes, file writes, network calls, logging — what does this touch?"

Why: 纯逻辑可以直接 extract; side effect 要 inject.

**3. Existing tests?**

> "Are there integration tests / golden files / customer-facing assertions I shouldn't break?"

Why: 决定 characterization test 跑哪个 spec.

**4. Performance SLA?**

> "Any latency / memory budget?"

Why: 抽函数有 call overhead; 热路径慎用过深嵌套.

**5. Allowed dependencies**

> "Can I introduce a new library (e.g., pydantic)?"

Why: 客户 ban 第三方时不能装.

**6. Scope of refactor**

> "Only this function, or also its callers? Can I change the signature?"

Why: 不能改 signature 限制大很多; 能改的话可以彻底 redesign.

**7. Timeline / branch strategy**

> "PR review pressure — small incremental PRs or one big refactor?"

Why: production refactor 多次小 PR > 一个大 PR (review 友好, easy revert).

---

## 详细解题流程

### Step 1: Sample "bad" 200-line function

为了 concrete, 我们假设面试官 paste 进来这么个函数 (real-feel BNPL refund handler):

```python
# refund_handler.py (BEFORE — 200 LoC, 0 tests)
import datetime
import requests
import json
import logging
from db import db_conn

logger = logging.getLogger(__name__)

def process_refund(refund_id, user_id, amount, currency, reason, region):
    """Process a refund request."""
    logger.info(f"Processing refund {refund_id}")
    # Validate amount
    if amount is None or amount <= 0:
        return {"status": "error", "code": "INVALID_AMOUNT"}
    if amount > 100000:
        if region == "ID":
            if amount > 5000000:
                return {"status": "error", "code": "AMOUNT_TOO_LARGE"}
        elif region == "VN":
            if amount > 50000000:
                return {"status": "error", "code": "AMOUNT_TOO_LARGE"}
        elif region == "TH":
            if amount > 1000000:
                return {"status": "error", "code": "AMOUNT_TOO_LARGE"}
        else:
            return {"status": "error", "code": "AMOUNT_TOO_LARGE"}
    # Validate currency
    if currency not in ["IDR", "VND", "THB", "USD"]:
        return {"status": "error", "code": "INVALID_CURRENCY"}
    if region == "ID" and currency != "IDR":
        return {"status": "error", "code": "CURRENCY_MISMATCH"}
    if region == "VN" and currency != "VND":
        return {"status": "error", "code": "CURRENCY_MISMATCH"}
    if region == "TH" and currency != "THB":
        return {"status": "error", "code": "CURRENCY_MISMATCH"}
    # Fetch user
    cursor = db_conn.cursor()
    cursor.execute("SELECT id, status, tier, country FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        return {"status": "error", "code": "USER_NOT_FOUND"}
    if user[1] == "SUSPENDED":
        return {"status": "error", "code": "USER_SUSPENDED"}
    if user[3] != region:
        return {"status": "error", "code": "REGION_MISMATCH"}
    # Fetch original transaction
    cursor.execute("SELECT id, amount, status, created_at FROM transactions WHERE id = (SELECT tx_id FROM refunds WHERE id = %s)", (refund_id,))
    tx = cursor.fetchone()
    if not tx:
        return {"status": "error", "code": "TX_NOT_FOUND"}
    if tx[2] != "SUCCESS":
        return {"status": "error", "code": "TX_NOT_REFUNDABLE"}
    # Check age
    tx_age_days = (datetime.datetime.now() - tx[3]).days
    if tx_age_days > 90:
        if user[2] != "VIP":
            return {"status": "error", "code": "TX_TOO_OLD"}
    # Check amount vs tx amount
    if amount > tx[1]:
        return {"status": "error", "code": "AMOUNT_EXCEEDS_TX"}
    # Compute fee
    fee = 0
    if amount < 100:
        fee = 5
    elif amount < 1000:
        fee = 10
    else:
        fee = amount * 0.01
    if user[2] == "VIP":
        fee = 0
    # Determine tier — manual confirm if amount > threshold or first refund or VIP large
    tier = "AUTO"
    if amount > 1000:
        tier = "MANUAL"
    cursor.execute("SELECT COUNT(*) FROM refunds WHERE user_id = %s AND status = 'COMPLETED'", (user_id,))
    refund_count = cursor.fetchone()[0]
    if refund_count == 0:
        tier = "MANUAL"
    if user[2] == "VIP" and amount > 500:
        tier = "MANUAL"
    # Fraud check via HTTP
    try:
        r = requests.post("https://fraud-svc/check", json={
            "user_id": user_id, "amount": amount, "tx_id": tx[0]
        }, timeout=5)
        if r.status_code == 200:
            fraud_score = r.json()["score"]
            if fraud_score > 0.8:
                tier = "MANUAL"
            if fraud_score > 0.95:
                return {"status": "error", "code": "BLOCKED_FRAUD"}
        else:
            logger.warning("fraud check failed")
    except Exception as e:
        logger.error(f"fraud check error: {e}")
    # Persist refund
    cursor.execute(
        "INSERT INTO refunds_processed (id, user_id, amount, fee, tier, status, created_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (refund_id, user_id, amount, fee, tier,
         "PENDING" if tier == "MANUAL" else "COMPLETED",
         datetime.datetime.now())
    )
    db_conn.commit()
    # Notify
    if tier == "MANUAL":
        try:
            requests.post("https://notify-svc/send", json={
                "user_id": user_id,
                "msg": f"Your refund {refund_id} is under review"
            }, timeout=5)
        except Exception as e:
            logger.error(f"notify failed: {e}")
    # Return
    return {
        "status": "ok",
        "refund_id": refund_id,
        "amount": amount,
        "fee": fee,
        "tier": tier,
        "net_amount": amount - fee
    }
```

### Step 2: Read + verbalize smells (10 min)

**Smells to call out (out loud)**:

1. **One function, multiple responsibilities** — validates + queries DB + computes fee + calls fraud svc + writes DB + sends notification. 6 个 reason to change.
2. **Region-specific limits hardcoded** — `if region == "ID": ...` 重复 3 次, 改一个限额要改 3 处.
3. **Magic numbers** — `100000`, `5000000`, `1000`, `0.8`, `0.95`, `90` 全无名字.
4. **Tuple positional access** — `user[1]`, `tx[3]` — 看不出意思.
5. **DB / HTTP 硬编码全局** — `db_conn`, `requests.post(...)` 不能 mock, 不能注入.
6. **Mixed return shapes** — error returns vs success returns不同 dict shape.
7. **Side effects 散落** — INSERT, requests.post, notify 全在 control flow 里.
8. **Error swallow** — fraud svc 挂 silently log + 继续, behavior 隐藏.
9. **Nested if** — region check 3 层嵌套, hard to test corner.
10. **No tests** — 函数 200 行 0 unit test.

### Step 3: Characterization tests (10 min)

**Before touching code, lock current behavior**:

```python
# tests/test_refund_handler_characterization.py
"""
Characterization tests: snapshot what current behavior is BEFORE refactor.
Goal — these MUST pass before and after refactor unchanged.
"""
import pytest
from unittest.mock import patch, MagicMock
import datetime

from refund_handler import process_refund


@pytest.fixture
def fake_db():
    with patch('refund_handler.db_conn') as db:
        cursor = MagicMock()
        db.cursor.return_value = cursor
        yield db, cursor


@pytest.fixture
def fake_requests():
    with patch('refund_handler.requests') as r:
        # default: fraud svc returns 200 with score 0.1
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {'score': 0.1}
        r.post.return_value = resp
        yield r


def test_negative_amount(fake_db, fake_requests):
    result = process_refund('r1', 'u1', -5, 'IDR', 'reason', 'ID')
    assert result == {'status': 'error', 'code': 'INVALID_AMOUNT'}


def test_zero_amount(fake_db, fake_requests):
    result = process_refund('r1', 'u1', 0, 'IDR', 'reason', 'ID')
    assert result == {'status': 'error', 'code': 'INVALID_AMOUNT'}


def test_invalid_currency(fake_db, fake_requests):
    result = process_refund('r1', 'u1', 100, 'JPY', 'reason', 'ID')
    assert result == {'status': 'error', 'code': 'INVALID_CURRENCY'}


def test_currency_mismatch(fake_db, fake_requests):
    result = process_refund('r1', 'u1', 100, 'USD', 'reason', 'ID')
    assert result == {'status': 'error', 'code': 'CURRENCY_MISMATCH'}


def test_amount_over_region_limit(fake_db, fake_requests):
    result = process_refund('r1', 'u1', 6_000_000, 'IDR', 'reason', 'ID')
    assert result == {'status': 'error', 'code': 'AMOUNT_TOO_LARGE'}


def test_happy_path_auto(fake_db, fake_requests):
    db, cursor = fake_db
    # User row
    cursor.fetchone.side_effect = [
        ('u1', 'ACTIVE', 'REGULAR', 'ID'),   # user
        ('tx1', 500.0, 'SUCCESS', datetime.datetime.now()),  # tx
        (3,),  # refund_count
    ]
    result = process_refund('r1', 'u1', 50.0, 'IDR', 'reason', 'ID')
    assert result['status'] == 'ok'
    assert result['tier'] == 'AUTO'
    assert result['fee'] == 5  # < 100
    assert result['net_amount'] == 45.0


def test_fraud_high_blocks(fake_db, fake_requests):
    db, cursor = fake_db
    cursor.fetchone.side_effect = [
        ('u1', 'ACTIVE', 'REGULAR', 'ID'),
        ('tx1', 500.0, 'SUCCESS', datetime.datetime.now()),
        (3,),
    ]
    fake_requests.post.return_value.json.return_value = {'score': 0.99}
    result = process_refund('r1', 'u1', 50.0, 'IDR', 'reason', 'ID')
    assert result['code'] == 'BLOCKED_FRAUD'


def test_fraud_medium_promotes_manual(fake_db, fake_requests):
    db, cursor = fake_db
    cursor.fetchone.side_effect = [
        ('u1', 'ACTIVE', 'REGULAR', 'ID'),
        ('tx1', 500.0, 'SUCCESS', datetime.datetime.now()),
        (3,),
    ]
    fake_requests.post.return_value.json.return_value = {'score': 0.85}
    result = process_refund('r1', 'u1', 50.0, 'IDR', 'reason', 'ID')
    assert result['tier'] == 'MANUAL'


def test_first_refund_is_manual(fake_db, fake_requests):
    db, cursor = fake_db
    cursor.fetchone.side_effect = [
        ('u1', 'ACTIVE', 'REGULAR', 'ID'),
        ('tx1', 500.0, 'SUCCESS', datetime.datetime.now()),
        (0,),  # refund_count = 0 → manual
    ]
    result = process_refund('r1', 'u1', 50.0, 'IDR', 'reason', 'ID')
    assert result['tier'] == 'MANUAL'
```

**讲给面试官**:

- "Characterization tests — locking current behavior. **If a test would fail with a known existing bug, I lock the bug** (write the test asserting the bug, refactor without changing behavior, then fix bug in a SEPARATE PR)."
- "I'm intentionally using mocks for `db_conn` and `requests` — even before refactor — so I can run these in 0.1s, not flake on network."
- "Coverage isn't 100%, but I have one test per branch + happy path. That's the safety net."

### Step 4: Refactor step by step (25 min)

**Each step: change → run tests → commit (mental commit)**.

#### Step 4a: Extract pure validation functions

```python
# refund/validators.py
from dataclasses import dataclass

REGION_AMOUNT_LIMITS = {
    'ID': 5_000_000,
    'VN': 50_000_000,
    'TH': 1_000_000,
}

REGION_CURRENCIES = {
    'ID': 'IDR',
    'VN': 'VND',
    'TH': 'THB',
}

ALLOWED_CURRENCIES = frozenset({'IDR', 'VND', 'THB', 'USD'})


@dataclass
class ValidationError:
    code: str


def validate_amount(amount: float, region: str) -> ValidationError | None:
    if amount is None or amount <= 0:
        return ValidationError('INVALID_AMOUNT')
    limit = REGION_AMOUNT_LIMITS.get(region)
    if limit is None or amount > limit:
        return ValidationError('AMOUNT_TOO_LARGE')
    return None


def validate_currency(currency: str, region: str) -> ValidationError | None:
    if currency not in ALLOWED_CURRENCIES:
        return ValidationError('INVALID_CURRENCY')
    expected = REGION_CURRENCIES.get(region)
    if expected and currency != expected:
        return ValidationError('CURRENCY_MISMATCH')
    return None
```

**Tests新增 (per-function unit test)**:

```python
def test_validate_amount_negative():
    assert validate_amount(-1, 'ID').code == 'INVALID_AMOUNT'

def test_validate_amount_over_limit_id():
    assert validate_amount(6_000_000, 'ID').code == 'AMOUNT_TOO_LARGE'

def test_validate_amount_under_limit():
    assert validate_amount(50, 'ID') is None
```

**讲**: "现在 validate_amount 是 **pure function** — 没 I/O, 没 mutation, 输入到输出. 测试 trivial, 一行 assert."

#### Step 4b: Define domain types

```python
# refund/types.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    id: str
    status: str
    tier: str
    country: str

@dataclass
class Transaction:
    id: str
    amount: float
    status: str
    created_at: datetime

@dataclass
class RefundRequest:
    refund_id: str
    user_id: str
    amount: float
    currency: str
    reason: str
    region: str

@dataclass
class RefundDecision:
    status: str  # 'ok' | 'error'
    code: str | None = None
    refund_id: str | None = None
    amount: float | None = None
    fee: float | None = None
    tier: str | None = None
    net_amount: float | None = None
```

**讲**: "Tuple positional access `user[1]` 改成 `user.status` — 自文档, 编辑器有 autocomplete, mypy 可 check."

#### Step 4c: Extract fee computation (pure)

```python
# refund/fees.py
def compute_fee(amount: float, user_tier: str) -> float:
    if user_tier == 'VIP':
        return 0.0
    if amount < 100:
        return 5.0
    if amount < 1000:
        return 10.0
    return amount * 0.01
```

**Tests**: `assert compute_fee(50, 'REGULAR') == 5`, etc. 4 行 test.

#### Step 4d: Extract tier classification (pure, but with fraud_score injected)

```python
# refund/tier.py
def classify_tier(
    amount: float,
    user_tier: str,
    refund_count: int,
    fraud_score: float | None,
    manual_threshold: float = 1000.0,
    vip_manual_threshold: float = 500.0,
    fraud_manual_threshold: float = 0.8,
) -> str:
    if amount > manual_threshold:
        return 'MANUAL'
    if refund_count == 0:
        return 'MANUAL'
    if user_tier == 'VIP' and amount > vip_manual_threshold:
        return 'MANUAL'
    if fraud_score is not None and fraud_score > fraud_manual_threshold:
        return 'MANUAL'
    return 'AUTO'
```

**讲**: "Tier 决策完全 pure — 不 call DB, 不 call HTTP. 测试 trivial."

#### Step 4e: Define I/O ports (dependency injection)

```python
# refund/ports.py
from typing import Protocol

class UserRepo(Protocol):
    def get_user(self, user_id: str) -> User | None: ...

class TxRepo(Protocol):
    def get_tx_by_refund(self, refund_id: str) -> Transaction | None: ...
    def get_refund_count(self, user_id: str) -> int: ...

class RefundStore(Protocol):
    def save_refund(self, *, refund_id, user_id, amount, fee, tier, status) -> None: ...

class FraudCheck(Protocol):
    def score(self, user_id: str, amount: float, tx_id: str) -> float | None: ...

class Notifier(Protocol):
    def notify_review(self, user_id: str, refund_id: str) -> None: ...

class Clock(Protocol):
    def now(self) -> datetime: ...
```

**讲**: "Define ports — abstract interfaces. 测试时 inject in-memory fake; prod inject real DB / HTTP. **不依赖具体 lib (psycopg, requests), 只依赖 protocol.**"

#### Step 4f: Implementations (adapters)

```python
# refund/adapters.py
import requests
import psycopg

class PostgresUserRepo:
    def __init__(self, conn):
        self.conn = conn

    def get_user(self, user_id):
        cur = self.conn.cursor()
        cur.execute("SELECT id, status, tier, country FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        if not row: return None
        return User(*row)


class PostgresTxRepo:
    def __init__(self, conn):
        self.conn = conn
    def get_tx_by_refund(self, refund_id):
        cur = self.conn.cursor()
        cur.execute("""SELECT id, amount, status, created_at FROM transactions
                        WHERE id = (SELECT tx_id FROM refunds WHERE id = %s)""", (refund_id,))
        row = cur.fetchone()
        if not row: return None
        return Transaction(*row)
    def get_refund_count(self, user_id):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM refunds WHERE user_id=%s AND status='COMPLETED'",
                     (user_id,))
        return cur.fetchone()[0]


class HttpFraudCheck:
    def __init__(self, url='https://fraud-svc/check', timeout=5):
        self.url = url
        self.timeout = timeout
    def score(self, user_id, amount, tx_id):
        try:
            r = requests.post(self.url, json={
                'user_id': user_id, 'amount': amount, 'tx_id': tx_id,
            }, timeout=self.timeout)
            if r.status_code == 200:
                return r.json()['score']
            return None
        except Exception:
            return None


class HttpNotifier:
    def notify_review(self, user_id, refund_id):
        try:
            requests.post('https://notify-svc/send', json={
                'user_id': user_id,
                'msg': f'Your refund {refund_id} is under review',
            }, timeout=5)
        except Exception:
            pass  # fire-and-forget
```

#### Step 4g: Compose orchestrator (thin)

```python
# refund/handler.py
from .validators import validate_amount, validate_currency
from .fees import compute_fee
from .tier import classify_tier
from .types import RefundRequest, RefundDecision
from .ports import UserRepo, TxRepo, RefundStore, FraudCheck, Notifier, Clock

REFUND_AGE_LIMIT_DAYS = 90
FRAUD_BLOCK_THRESHOLD = 0.95


class RefundHandler:
    def __init__(
        self,
        users: UserRepo,
        txs: TxRepo,
        store: RefundStore,
        fraud: FraudCheck,
        notifier: Notifier,
        clock: Clock,
    ):
        self.users = users
        self.txs = txs
        self.store = store
        self.fraud = fraud
        self.notifier = notifier
        self.clock = clock

    def process(self, req: RefundRequest) -> RefundDecision:
        # Validate inputs (pure)
        if err := validate_amount(req.amount, req.region):
            return RefundDecision(status='error', code=err.code)
        if err := validate_currency(req.currency, req.region):
            return RefundDecision(status='error', code=err.code)

        # Fetch user (I/O)
        user = self.users.get_user(req.user_id)
        if user is None:
            return RefundDecision(status='error', code='USER_NOT_FOUND')
        if user.status == 'SUSPENDED':
            return RefundDecision(status='error', code='USER_SUSPENDED')
        if user.country != req.region:
            return RefundDecision(status='error', code='REGION_MISMATCH')

        # Fetch tx (I/O)
        tx = self.txs.get_tx_by_refund(req.refund_id)
        if tx is None:
            return RefundDecision(status='error', code='TX_NOT_FOUND')
        if tx.status != 'SUCCESS':
            return RefundDecision(status='error', code='TX_NOT_REFUNDABLE')

        # Age check (pure)
        age_days = (self.clock.now() - tx.created_at).days
        if age_days > REFUND_AGE_LIMIT_DAYS and user.tier != 'VIP':
            return RefundDecision(status='error', code='TX_TOO_OLD')

        # Amount vs tx check
        if req.amount > tx.amount:
            return RefundDecision(status='error', code='AMOUNT_EXCEEDS_TX')

        # Compute fee (pure)
        fee = compute_fee(req.amount, user.tier)

        # Fraud check (I/O, optional fail)
        fraud_score = self.fraud.score(req.user_id, req.amount, tx.id)
        if fraud_score is not None and fraud_score > FRAUD_BLOCK_THRESHOLD:
            return RefundDecision(status='error', code='BLOCKED_FRAUD')

        # Refund count (I/O)
        refund_count = self.txs.get_refund_count(req.user_id)

        # Tier classification (pure)
        tier = classify_tier(req.amount, user.tier, refund_count, fraud_score)

        # Persist (I/O)
        self.store.save_refund(
            refund_id=req.refund_id, user_id=req.user_id,
            amount=req.amount, fee=fee, tier=tier,
            status='PENDING' if tier == 'MANUAL' else 'COMPLETED',
        )

        # Notify (I/O, fire-and-forget)
        if tier == 'MANUAL':
            self.notifier.notify_review(req.user_id, req.refund_id)

        return RefundDecision(
            status='ok',
            refund_id=req.refund_id,
            amount=req.amount,
            fee=fee,
            tier=tier,
            net_amount=req.amount - fee,
        )
```

### Step 5: Now write unit tests trivially (5 min)

```python
# tests/test_handler.py
import pytest
import datetime
from refund.handler import RefundHandler
from refund.types import User, Transaction, RefundRequest

class FakeUserRepo:
    def __init__(self, users): self.users = users
    def get_user(self, uid): return self.users.get(uid)

class FakeTxRepo:
    def __init__(self, txs, counts):
        self.txs = txs
        self.counts = counts
    def get_tx_by_refund(self, rid): return self.txs.get(rid)
    def get_refund_count(self, uid): return self.counts.get(uid, 0)

class FakeStore:
    def __init__(self): self.saved = []
    def save_refund(self, **kw): self.saved.append(kw)

class FakeFraud:
    def __init__(self, score): self.s = score
    def score(self, uid, amt, txid): return self.s

class FakeNotifier:
    def __init__(self): self.sent = []
    def notify_review(self, uid, rid): self.sent.append((uid, rid))

class FrozenClock:
    def __init__(self, t): self.t = t
    def now(self): return self.t


def make_handler(*, user=None, tx=None, count=3, fraud=0.1, now=None):
    now = now or datetime.datetime(2026, 1, 1)
    user = user or User('u1', 'ACTIVE', 'REGULAR', 'ID')
    tx = tx or Transaction('tx1', 500.0, 'SUCCESS', now - datetime.timedelta(days=1))
    return RefundHandler(
        users=FakeUserRepo({'u1': user}),
        txs=FakeTxRepo({'r1': tx}, {'u1': count}),
        store=FakeStore(),
        fraud=FakeFraud(fraud),
        notifier=FakeNotifier(),
        clock=FrozenClock(now),
    )


def make_req(**kw):
    base = dict(refund_id='r1', user_id='u1', amount=50.0,
                currency='IDR', reason='r', region='ID')
    base.update(kw)
    return RefundRequest(**base)


def test_happy_auto():
    h = make_handler()
    res = h.process(make_req())
    assert res.status == 'ok' and res.tier == 'AUTO'

def test_fraud_score_blocks():
    h = make_handler(fraud=0.99)
    res = h.process(make_req())
    assert res.code == 'BLOCKED_FRAUD'

def test_first_refund_manual():
    h = make_handler(count=0)
    res = h.process(make_req())
    assert res.tier == 'MANUAL'

def test_vip_high_amount_manual():
    h = make_handler(user=User('u1','ACTIVE','VIP','ID'))
    res = h.process(make_req(amount=700.0))
    assert res.tier == 'MANUAL'

def test_old_tx_blocked():
    old = datetime.datetime(2026,1,1) - datetime.timedelta(days=120)
    tx = Transaction('tx1', 500.0, 'SUCCESS', old)
    h = make_handler(tx=tx)
    res = h.process(make_req())
    assert res.code == 'TX_TOO_OLD'

def test_old_tx_vip_passes():
    old = datetime.datetime(2026,1,1) - datetime.timedelta(days=120)
    tx = Transaction('tx1', 500.0, 'SUCCESS', old)
    h = make_handler(tx=tx, user=User('u1','ACTIVE','VIP','ID'))
    res = h.process(make_req())
    assert res.status == 'ok'

def test_amount_too_large():
    res = make_handler().process(make_req(amount=6_000_000))
    assert res.code == 'AMOUNT_TOO_LARGE'

def test_notify_called_on_manual():
    h = make_handler(count=0)
    h.process(make_req())
    assert len(h.notifier.sent) == 1

def test_notify_not_called_on_auto():
    h = make_handler()
    h.process(make_req())
    assert len(h.notifier.sent) == 0
```

**讲**: "现在 9 个 unit test, no mocks (only fake adapters), 全部 in-memory, 跑 <0.05s. 之前要 mock requests + db_conn 一堆 patch, 现在 zero patch."

### Step 6: Diff before/after (5 min)

| Metric | Before | After |
|--------|--------|-------|
| Lines (1 file) | 200 | 6 files × ~30-60 lines each |
| Functions | 1 | 1 orchestrator + 4 pure + 6 adapters |
| Imports | `db_conn` global, `requests` direct | None at top-level handler — DI only |
| Unit tests | 0 | 9 unit + 5 pure-function tests |
| Test runtime | ~30s (real DB) | ~0.05s (all in-memory) |
| Cyclomatic complexity (handler) | ~25 | ~10 (orchestrator) + 1-3 each |
| Coverage | est. 15% | 95%+ |

**讲**: "Single Responsibility per file: validators / fees / tier / ports / adapters / handler. **Pure / I/O 分离**. **DI via Protocol**. **In-memory tests**."

---

## 完整代码 (after refactor)

整个 refund package, ~400 行 across 6 files. Tests ~250 lines. Production-ready. (Already shown above in steps 4a-4g and Step 5.)

---

## 复杂度分析

**重构 doesn't change time complexity** — 还是 O(1) DB queries per refund. 重要 metric 是 **maintainability**:

- Cognitive complexity (handler): 25 → 10
- Test runtime: 30s integration → 50ms unit
- Time to add new validation rule: 1h with manual test → 10 min with unit test
- Bug repro: 整 integration env → 1 行 fake

---

## Gao Xin 简历专属 reframe

- **Indonesia refund tier**: 我的真实工作. 我接手的 refund decision 是 ~300 行 Java function, 我重构成 strategy pattern + dependency injection, 把 6 个 region-specific rule 抽成 plugin. Unit test 从 0 到 40+.
- **BNPL chatbot**: intent routing 一个文件 500 行 if/else, 我重构成 plug-in handler pattern + central dispatcher. 后来加新 intent 不再 touch dispatcher, 只 register new handler.
- **Voice agent**: phone bot 大状态机 800 行 swich case, 我重构成 explicit state class + transition table. 之前 add 一个 state 改 5 处, 之后 1 处.
- **Internal Agent Platform**: tool dispatcher 重构, 抽 ToolProtocol, plug-in 注册.
- **ConvFinQA**: experiment runner 重构成 declarative config + injectable models, 9-variant ablation 跑通的关键就是 model 是 inject 进来的不是 hardcode.

**面试一句话**: "I shipped this pattern at TikTok for the refund tier system. The before was untestable — 6 dev hours for a 1-line policy change because there were no unit tests. After refactor with DI + pure functions, same change is 30 minutes including tests."

---

## 5 个 Follow-ups

**Q1**: "如果 PR 太大, reviewer 看不过来, 怎么 split?"

A: **Strangler pattern**. 一系列小 PR:
1. PR1: Add types.py + tests (no behavior change)
2. PR2: Add validators.py + unit tests, keep handler using new validators internally (still 200 lines)
3. PR3: Add fees.py
4. PR4: Add tier.py
5. PR5: Add ports.py + adapters.py
6. PR6: Replace orchestrator wiring (only at this PR is "before" function deleted)
每个 PR 都跑 characterization test, 失败 = 不 merge.

**Q2**: "有没有时候不应该 refactor?"

A: 是的:
- 函数 stable 5 年没改, 也不打算改 → 改它价值低, 风险高
- Test coverage 0 + 重要 prod 路径 + 没 time 写 characterization tests → 拆了一定 bug, 拒 refactor
- 公司即将弃用这模块 (3 个月后下线) → 不重构
- 自己一周后离职 → 不要留个半改不彻底的烂摊子

**Q3**: "你会用 OOP 还是 functional?"

A: Hybrid — **functional core, imperative shell**:
- Validators / fees / tier 是 pure functions
- Repository / adapter 是 class (有 state — connection)
- Orchestrator 是 class (持有 dependencies, 多个 method 可共享 ctor injected deps)
- 不 over-OOP — 简单 validator 就是 function, 不 wrap class

**Q4**: "性能开销?"

A: Negligible:
- 6 个函数 call 比 1 个 inline 多 ~600ns
- Protocol dispatch 用 duck typing 没 vtable 开销
- DI 多一层 attribute access
- 总开销远小于 1 个 DB query (1-5ms)
当然 hot path (1M QPS in-mem cache) 我会考虑 inline, 但 refund handler 100 RPS 完全不是 issue.

**Q5**: "如果有 50 个 region 而不是 3 个, 你的 abstraction 还成立吗?"

A: Yes — `REGION_AMOUNT_LIMITS` dict 加新行就行, 不动 code. 这才是 refactor 真价值: **change isolation**. 反例: 之前 200 行 hardcode if/elif, 加 50 个 region 改 200 处.

进一步: 把 region config 移到 YAML / DB, runtime 改不 deploy. → `PolicyRepo.get_limits(region)`.

---

## 死路答法

1. **沉默重构** — 30 分钟一句不说, 面试官不知你在想什么
2. **Big-bang rewrite** — 全删了从零写, 没 characterization test 保底, 没法验证等价
3. **过度抽象** — 5 行函数 wrap 一个 class with factory, "为了 SOLID" — 客户看不懂
4. **没问 caller** — 改了 signature, callers 编译挂
5. **没测 before refactor** — 改完跑不起来, 不知道 break 了什么
6. **改完没 commit 历史** — 一个 commit 改 6 个文件, 出 bug 不能 bisect
7. **重命名 + 重构 同 commit** — diff 看不清, review 痛苦; 拆分: 先 rename PR, 再 refactor PR
8. **忽略 region/currency 重复** — leaving lookup tables hardcoded 不 abstract
9. **`requests.post` 直接用** — 没法 mock without monkey-patch
10. **silent error swallow** — fraud svc 挂了 silent log, 客户看到神秘 tier 决策

---

## 加分项

**Process 加分**:

- **`git mv` 然后 refactor** — preserve blame history
- **每个 PR 命名 prefix**: `[refactor-1/6] add types module` — reviewer 一眼看到 batch
- **CI check**: char tests + new unit tests 都过, coverage 上升才能 merge
- **Branch protection** — 这种 PR 要求 2 个 reviewer
- **CODEOWNERS** for the file — 改它要 originating team approve
- **Feature flag**: 灰度 — `if FEATURE_REFUND_REFACTOR: new_handler else: old_handler`. 灰度 1% → 10% → 100%, 出错回滚
- **Shadow traffic**: 旧 handler 还跑, 新 handler 也跑, diff log — 0 diff 数日后切流
- **Burn-down**: 一开始多文件不 delete 老函数; deprecation period 后再删
- **Lint**: `ruff`, `mypy --strict` on new modules
- **Documentation**: README 说明分层 (functional core + imperative shell), how to test, how to add new validator
- **Customer empathy**: refund handler 决定客户钱, 错了 = 财务损失 + PR. Refactor 必须 zero behavior change.

---

## 一句话总结

> **重构 = (1) 写 characterization tests 锁定 behavior, (2) 抽 pure function 出来 → 易测, (3) 注入 dependencies 取代全局, (4) 每改一步跑 test, (5) 边做边讲 — 不 silent. Process > result.**

---

## Cheat Sheet

```
Process (out loud the whole time):
  1. Read + verbalize smells (5-10 min)
  2. Ask clarifying Qs (callers, side effects, perf, deps)
  3. Write characterization tests — lock current behavior
  4. Refactor incrementally:
     a. Extract pure functions (validators, fees, tier)
     b. Define domain types (replace tuple indexing)
     c. Define ports (Protocol-based DI)
     d. Implement adapters (DB, HTTP wrappers)
     e. Compose thin orchestrator
     f. Write unit tests (no mocks — use fakes)
  5. Diff before/after, talk trade-offs

Smells to call out:
  - Multiple responsibilities in one function
  - Magic numbers
  - Nested if 3+ levels
  - Tuple positional access
  - Global state (db_conn, requests)
  - Mixed I/O + logic
  - Region/business-rule hardcoded duplicated
  - 0 unit tests

Refactor patterns:
  - Extract function (pure first)
  - Replace magic with constant / dict
  - Dataclass instead of tuple
  - Protocol-based DI for I/O
  - Adapter pattern for external libs
  - Strangler pattern for big PRs

Test strategy:
  - Characterization tests first (snapshot existing)
  - Pure-function unit tests (no setup)
  - Fake adapters (in-memory)
  - Frozen clock
  - Goal: zero patch/mock

Things NOT to do:
  - Refactor without tests
  - Rewrite from scratch
  - Big-bang single PR
  - Silent — speak the whole way
  - Over-abstract (5-line fn wrap in class)
  - Rename + refactor in same commit
```
