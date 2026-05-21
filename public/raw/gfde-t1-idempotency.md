## 题目

> "Design an **idempotent tool interface** for an agent that may retry. The tool transfers money between two accounts."

或更开放版本:

> "Your agent's `transfer_funds` tool can be called multiple times due to network retry, model re-issuing, parallel execution. How do you ensure **at-most-once** semantics from the agent's perspective without sacrificing **at-least-once** delivery guarantees from the system?"

**出处**: Google FDE T1 (Tool Calling) 经典题. Anthropic / OpenAI / Stripe agent infra interview 也都问过类似 framing.

**Round**: Tool Calling System Design (45-60 min)

---

## 这道题在考什么

**Idempotency** 是 production agent 的必修课, 不是「会不会写代码」, 是「在 LLM + 分布式 + 真钱场景下你想没想清楚」:

1. **Agent retry semantics** —— LLM 可能 re-issue tool call, runtime 可能 retry on timeout, network 也可能重发
2. **Idempotency key 设计** —— 谁生成、用什么字段、hash 还是 UUID、长度多少
3. **State machine** —— `in_flight / completed / failed` 三态 + race condition 处理
4. **TTL design** —— 几分钟还是几天, 跟存储 tier 的关系
5. **Failure modes** —— Redis 挂、key collision、agent 改 args 后 retry、跨 vendor 不支持 idem
6. **Cross-vendor reality** —— 50% 的下游 API 没有原生 idempotency 支持, 你得自己 wrap

不只是知道 "用 idempotency_key", 而是知道**所有 corner case + 真生产怎么部署**.

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 四个术语先解释

**Idempotency (幂等性)**: 一个操作执行 1 次 vs N 次, **结果一样**. 数学定义: `f(f(x)) = f(x)`. 工程定义: 多次调用产生**相同 side effect** (不是相同 return value — return 可以变, 但 state change 不会重复).

- 幂等的例子: `set_email(user, 'a@b.com')` (设几次都是这个 email)
- **非**幂等的例子: `transfer($100)` (调 3 次扣 3 次), `append_log(msg)` (调 3 次有 3 条)
- **被改造成幂等的** 例子: `transfer($100, idem_key='abc-123')` (key 相同时第 2-3 次 noop)

**At-most-once vs at-least-once vs exactly-once**: 投递语义.

- **At-most-once**: 最多 1 次, 可能 0 次 (会丢)
- **At-least-once**: 至少 1 次, 可能多次 (默认你能拿到的网络层保证)
- **Exactly-once**: 恰好 1 次. **网络环境下严格不可达** (Two Generals 问题), 但「**at-least-once + idempotent consumer = 业务层 exactly-once**」是工程实现.

**Idempotency Key**: 一个**唯一标识 1 次业务意图**的字符串. 同 key 多次请求 → server 识别为同一意图, 只执行一次. 关键: key 要由**意图来源方** (一般是 client / agent runtime) 生成, 不能 server 生成.

**Dedup window (去重窗口)**: server 记住 idempotency_key 的时间. 同 key 在窗口内重发 → dedup. 窗口外重发 → 当成新意图. 典型: Stripe 24h, 银行账本永久.

---

## 2. 这个问题的核心是什么

设想 agent 没做 idempotency 的灾难场景:

```
T=0    agent: "I'll transfer $100 from A to B"
T=0.1  runtime: call transfer_funds(A, B, 100)
T=0.5  bank API: 收到, 处理中 ...
T=5.0  network glitch: agent 端 timeout, 没收到 response
T=5.0  runtime: 重试 → call transfer_funds(A, B, 100) 第二次
T=5.5  bank API: 第一次正在 commit, 第二次也开始 ...
T=6.0  bank: A 扣了 2 次 100, B 收到 2 次 100, 总账平
T=6.0  用户: "我账上少了 200!" → 客诉, compliance event, 公司新闻
```

**问题来源 (多种)**:

| 来源 | 原因 | 例子 |
|---|---|---|
| **网络层重试** | TCP retransmit / load balancer retry | 30% 5xx rate 的服务 |
| **HTTP client retry** | requests / aiohttp 自带 retry | tenacity 默认 3 次 |
| **Runtime retry** | Agent framework wrapper retry | LangGraph node retry config |
| **LLM re-issue** | LLM 等不到 result 自己生成新 tool_call | 流式响应中 timeout |
| **User refresh** | 用户在 UI 上手动重试 | "上次没成功吧?" 再点一次 |
| **Parallel agents** | 2 个 worker pick 同 task | 没 dedup 的 queue |
| **Backup restore** | DR 演练放回了已 process 的 event | Kafka offset rewind |

**没 idempotency 的后果**:

- **金钱**: 双花 / 重复扣款 / 重复发货 (TikTok PayLater 业务里这是直接 P0)
- **通知**: 同一封邮件发 3 次 (UX 难受 + 反垃圾算法判你 spam)
- **状态**: order 状态机 `created → paid → created` 倒退
- **资源泄漏**: create_resource 重复 N 次, quota 涨爆

**Idempotency 的解法 (1 句话)**:

```
client/agent: 我给每个意图分配一个 unique key
server: 我记住每个 key 的 result, 同 key 再来直接返回上次的 result, 不重新执行
```

---

## 3. 典型流程图 (state machine)

```
              client/agent 生成 idempotency_key
                            ↓
                     [tool wrapper 收到请求]
                            ↓
              ┌──────────────────────────┐
              │ Redis: GET idem:{key}    │
              └──────────────┬───────────┘
                             ↓
            ┌────────────────┼────────────────┐
            ↓                ↓                ↓
       (not found)      in_flight         completed
            ↓                ↓                ↓
      ┌──────────┐    ┌──────────┐     ┌──────────┐
      │ SETNX    │    │ poll 200ms│    │ return    │
      │ in_flight│    │ wait up to│    │ cached    │
      │ TTL 24h  │    │  10s     │    │ result    │
      └─────┬────┘    └────┬─────┘     └──────────┘
            ↓              ↓
       (got lock?)      (finished?)
            ↓              ↓
       ┌────┴────┐    ┌────┴────┐
       ↓         ↓    ↓         ↓
      yes       no   yes       no
       ↓         ↓    ↓         ↓
   execute  poll again return  return
   bank API           cached  409 Conflict
       ↓
   ┌──────────────┐
   │ SUCCESS      │
   │   ↓          │
   │ SET completed│
   │ TTL 24h     │
   └──────────────┘
       OR
   ┌──────────────┐
   │ FAIL         │
   │   ↓          │
   │ DEL key     │  ← 让 retry 可以再试
   │ (or set     │
   │  retryable) │
   └──────────────┘
```

**3 个状态语义**:

| 状态 | 含义 | 同 key 再来 |
|---|---|---|
| `in_flight` | 上一次还在执行 | 等 / 409 / 返回 (等结果) |
| `completed` | 成功了, 有结果 | 直接返回 cached result |
| `failed` (或删 key) | 失败了, 允许重试 | 当新请求处理 |

---

## 4. 关键 key 生成策略分类表

谁生成 key、怎么生成, 是这道题最容易答错的地方:

| 谁生成 | 怎么生成 | 优点 | 缺点 | 适用 |
|---|---|---|---|---|
| **LLM** | 让模型自己 emit `idempotency_key` 字段 | 简单 | 模型不确定性, 同意图可能 emit 不同 key | ❌ 避免 |
| **Client app** | 用户点按钮时 UUID v4 | 处理 user double-click | retry 内部 layer 不知道 | 用户 UI 层 |
| **Agent runtime** ⭐ | `sha256(session_id + tool_name + sorted_args)` | 确定性, 跨 retry 一致 | args 微变就失效 | 推荐 |
| **Tool wrapper** | 直接收 LLM 或 runtime 的 key | 把责任推给上层 | 上层错就传错 | 默认行为 |
| **Server (tool side)** | server 自己生成 + 返回 | 不可能 (生成时就执行了) | — | ❌ 不可行 |

**Agent runtime 生成 key 的标准模板**:

```python
import hashlib
import json

def make_idempotency_key(session_id: str, tool_name: str, args: dict) -> str:
    """
    Deterministic key from intent.

    Why include each field:
      - session_id: 跨 session 不同 user 不能撞 (user A 转 100 vs user B 转 100)
      - tool_name: 同 session 内不同 tool 不能撞
      - args: 同 tool 不同参数不能撞

    Why NOT include:
      - timestamp: retry 时 timestamp 变, key 就变, 等于没 dedup
      - request_id: LLM 每次重新 emit 会变, 同上
      - random nonce: 同上
    """
    content = json.dumps({
        'session': session_id,
        'tool': tool_name,
        'args': args,
    }, sort_keys=True, separators=(',', ':'))
    # SHA-256 → 64 hex chars; truncate to 32 enough
    return hashlib.sha256(content.encode()).hexdigest()[:32]
```

**Hash vs UUID 选择**:

- **Hash (deterministic)**: 相同意图自动相同 key, 不需要 client 记 key. ⭐ 推荐 agent 场景
- **UUID (random)**: client 必须**记住自己用过的 UUID**, 否则 retry 时生成新 UUID = 新意图. 适合 UI 场景 (按钮点击时 generate, 存 React state)

---

## 5. 具体业务场景

### 场景 A: TikTok PayLater debt collection voice agent (你最贴的业务背景)

Voice agent 跟欠款客户通话, 谈到「你同意现在还 100 块?」, 客户说同意, agent 触发 tool:

```python
@tool(idempotent=True, dedup_window_hours=24)
def collect_payment(loan_id, amount, payment_method):
    """Trigger payment collection from customer's bound card."""
    ...
```

**Idempotency 在这里的重要性**:

- **网络抖动**: voice agent 跨 Indonesia / Brazil / Mexico 7 markets, 第三方支付 channel 经常 timeout → runtime auto retry → 不带 idem 就双扣
- **LLM re-issue**: LLM 等 200ms 没收到 result, 觉得「网络问题, 我再试一次」, emit 第二次 tool call → 必须 dedup
- **客户挂断重拨**: 客户挂了再拨, 新 session, 但 loan_id 不变 — **这种应该是新意图** (用户重新同意一次), 不该被 dedup
- **Resume across crash**: voice agent process 崩了, restart 后 resume session, 不能把 commitment 漏掉也不能重发

**Key 设计要点**:

```python
# 包含 session_id 区分: 客户两次通话各自独立
key = sha256(f"{session_id}:{loan_id}:collect_payment:{amount}")
# 不含 timestamp / call_attempt_id
```

### 场景 B: BNPL chatbot — order modification

Chatbot 帮用户改订单:

```python
@tool(idempotent=True)
def cancel_order(order_id): ...

@tool(idempotent=True)
def request_refund(order_id, amount, reason): ...
```

- `cancel_order` 天然幂等 (取消已取消的还是已取消)
- `request_refund` **不天然幂等** — 没 idem 时同 args 调 2 次会发起 2 个退款请求

**真实 bug 故事**: 用户点 "退款" 按钮, 网络慢, 用户再点一次, chatbot 调了 2 次 `request_refund` → 退了 2 倍金额. 加 idempotency key (基于 `user_id + order_id + amount`) 后修复.

### 场景 C: Internal Agent Platform — workflow step idempotency

你做的 internal Agent Platform 给其他 ByteDance 团队提供 workflow / tool / memory abstractions. Workflow 编排里:

```python
workflow:
  - step: create_invoice (idempotent)
  - step: charge_card (idempotent, MUST)
  - step: send_confirmation_email (idempotent)
  - step: update_ledger (idempotent, MUST)
```

任一 step crash → workflow runtime 从最后 committed step resume → 每个 step 必须幂等才能正确 resume.

**框架做法**: workflow_id × step_name 作为 idempotency key 自动注入:

```python
@step
def charge_card(amount):
    # framework injects _idem_key = sha256(workflow_id + step_name)
    return stripe.charge(amount, idempotency_key=_idem_key)
```

### 场景 D: ConvFinQA agent — read tools

ConvFinQA 是 multi-hop financial Q&A. 看似全是 read tool (`get_revenue`, `calculate_ratio`), 没有 destructive op, **是不是不需要 idempotency**?

答: read tool 也需要, 但场景不同:

- **Cost dedup**: 同 prompt 同 args 调 5 次 LLM, 浪费 token cost. 即使 idempotent (无 side effect), 加 cache 用 key dedup 省钱
- **Result stability**: ablation methodology 要求**相同实验配置得到相同 result**, idem key + cached result 保证可复现

### 场景 E: Multi-tenant SaaS — agent 帮多个 customer 各自操作

```
Customer A: agent → transfer_funds(from=A_acc1, to=A_acc2, $100)
Customer B: agent → transfer_funds(from=B_acc1, to=B_acc2, $100)
```

Args 完全一样? 不, 因为 acc 编号不同. **但要确保 key 不跨 tenant 撞**:

```python
key = sha256(f"{tenant_id}:{session_id}:{tool}:{args}")
# tenant_id 必须显式入 key, 不能信任 args 里有
```

跨租户 key collision 是 SaaS 最致命事故 (用户 A 看到用户 B 的 result, 一锤定音公司倒闭).

---

## 6. 工程上要做什么 (实施 checklist)

**作为 agent runtime / tool wrapper 实现方**:

1. **声明 tool 是否 idempotent** — 在 tool registration 加 metadata
2. **Key generation function** — runtime 中央实现, 确定性 hash
3. **Pre-execute lookup** — Redis GET 看是否已知 key
4. **State machine 3 态** — `in_flight / completed / failed`
5. **In-flight 处理** — poll 等待 / 返 409 / async wait
6. **TTL 配置** — 短 (5min for transient) + 长 (24h for cross-session) 双 tier
7. **持久化** — Redis 不够, 加 DB 兜底 (cold tier)
8. **Pass-through 下游** — 如果下游 (e.g., Stripe) 支持 idem header, 直接传
9. **Fallback when 下游 不支持** — wrapper 全权负责 dedup
10. **Audit log** — 每次 hit / miss / collision 都记
11. **Monitoring** — dedup hit rate, in-flight wait time p99, key cardinality
12. **Failure policy** — Redis 挂时 fail closed (destructive) or fail open (read)
13. **Reconciliation job** — 跟下游账本定时对账, 修 unknown 状态
14. **Test harness** — concurrent invocation property test
15. **Documentation** — 给 tool author + LLM prompt 一份 idempotency 行为说明

**作为 LLM prompt 设计者**:

- 提示模型: "If a tool call times out, **retry with EXACT same args first**. Only adjust args after confirming original didn't execute (use `get_status` tool)."
- 不要让模型生成 `idempotency_key` 字段 (modeling 不确定)

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **让 LLM 生成 idempotency_key** | LLM 输出有随机性, 同意图可能不同 key. Runtime 生成 |
| 2 | **Key 不含 tenant_id / session_id** | 跨用户撞车, 安全事故 |
| 3 | **Key 含 timestamp / random** | 每次都新 key, 等于没 dedup |
| 4 | **TTL 太短** (< 1min) | 跨 session retry 失效 |
| 5 | **TTL 太长** (> 30d) | 用户合法 retry (e.g., 1 月后再转同样金额) 被当 dup |
| 6 | **没 in_flight 状态** | 第一次还在跑, 第二次又跑了, race |
| 7 | **Fail-open 在 Redis 挂时** | 全部 retry 都过, 双花风险 |
| 8 | **不记 audit** | dedup hit 不可观察, 出 bug 查不到 |
| 9 | **TTL 跨 layer 不一致** | wrapper 5 min, 下游 24h, 两者 race |
| 10 | **没 reconciliation** | wrapper 状态和下游账本最终不一致 |
| 11 | **Idem key 进 URL** | 日志泄漏 → 攻击者可用 key 重放 (用 header) |
| 12 | **同 key 不同 result** | 第一次返 success result_X, 第二次因下游 mutate 返 result_Y → 矛盾 |

---

## 一句话总结 (Part 1)

> **Idempotent tool = "runtime 生成确定性 key + 3 态机 (in_flight/completed/failed) + 短长 TTL 双 tier + 跨 vendor wrapper 兜底 + 持续对账"**.
>
> 没做 idempotency 的 destructive tool, 早晚在 production 上演双花 / 重复扣款 / 客诉 P0. Agent 时代这一层只会更重要 — LLM 比 human 更容易触发 retry.

---

# Part 2 · 5 个深度工程问题

## ⚙️ Problem 1: Idempotency Key Generation — 谁生成, 怎么 hash, 包含什么

Key generation 决定了 idempotency 的**整个语义边界**: key 一样 = 同意图, key 不同 = 新意图. 设计错了, 整个机制崩.

### 1.1 谁生成 — Layer 决策

```
┌────────────────────────────────────────────────────┐
│  User clicks button (UI)                            │
│      ↓ generate client_request_id (UUID)            │  ← UI 层 key
│  POST /agent/chat                                   │
│      ↓                                              │
│  Agent runtime receives, plans tool call            │
│      ↓ generate idem_key = hash(session, tool, args)│  ← Runtime 层 key ⭐
│  Tool wrapper                                       │
│      ↓ pass-through key to downstream               │
│  Downstream API (Stripe / bank)                     │
│      ↓ if supports idem header: use ours            │  ← Vendor 层 key
│      ↓ else: wrapper's Redis is source of truth     │
└────────────────────────────────────────────────────┘
```

**为什么 runtime 而不是 LLM**:

```python
# 反面教材: 让 LLM emit idem_key
tool_call = {
    "name": "transfer_funds",
    "arguments": {
        "from": "A", "to": "B", "amount": 100,
        "idempotency_key": "abc-123"  # ← LLM 生成的
    }
}

# 问题:
# 1. Sampling 不确定: 同 prompt 调 2 次, model 可能生成 "abc-124"
# 2. LLM 可能 reason 错: 觉得「上次失败了, 我用新 key 重试」→ 重复执行
# 3. Token cost: idem_key 进 / 出 token 浪费
# 4. Hallucinate: 复制其他 conversation 的 key, 跨 session 撞
```

**Runtime 生成的好处**: 确定性、跨 retry 一致、不消耗 LLM token、可控.

### 1.2 包含哪些字段

这是设计重点. 包多了 = 误判新意图 (失效); 包少了 = 跨 user 撞车.

| 字段 | 必须? | 为什么 |
|---|---|---|
| `tenant_id` | ✅ MUST | SaaS 多租户必备 |
| `session_id` | ⭐ 推荐 | 区分用户的不同 conversation |
| `tool_name` | ✅ MUST | 同 args 不同 tool 不能撞 |
| `args` (canonical) | ✅ MUST | 同 tool 不同 args 必须不同 key |
| `timestamp` / `nonce` | ❌ 不要 | 加了等于没 dedup |
| `attempt_id` / `retry_count` | ❌ 不要 | 同上 |
| `model_name` / `prompt_version` | 🤔 视情况 | 实验场景需要, 生产慎重 |
| `user_id` | 🤔 通常已含在 session | 显式加更安全 |

**Args canonical 化** (经典坑):

```python
# 同意图但 dict 顺序不同:
args1 = {"from": "A", "to": "B", "amount": 100}
args2 = {"to": "B", "from": "A", "amount": 100}

# 不 canonical 化 → 不同 hash → 不同 key → 双花
key1 = hash(json.dumps(args1))  # 算出 X
key2 = hash(json.dumps(args2))  # 算出 Y, X != Y

# 解法: sort keys
key1 = hash(json.dumps(args1, sort_keys=True))
key2 = hash(json.dumps(args2, sort_keys=True))
# 现在 X == Y ✓
```

**还要注意**:
- Float precision: `100.00 != 100.000` 在某些 JSON encode 下产生不同 string → 强制 `Decimal` + 固定精度
- 字符串大小写: `"a@b.com" vs "A@b.com"` 看业务上是否同 user
- 数组顺序: `["a","b"] vs ["b","a"]` 看语义是否 set 还是 list

### 1.3 Hash 算法选择

```python
# Option A: SHA-256 truncated 32 chars
key = hashlib.sha256(content.encode()).hexdigest()[:32]
# Collision prob: ~2^-128 (negligible for any realistic cardinality)

# Option B: SHA-256 full 64 chars
key = hashlib.sha256(content.encode()).hexdigest()
# Same collision prob, more storage

# Option C: BLAKE2b (faster, same security)
key = hashlib.blake2b(content.encode(), digest_size=16).hexdigest()
# 30% faster than SHA-256

# Option D: xxHash (NOT for security, just fast hash)
import xxhash
key = xxhash.xxh64(content.encode()).hexdigest()
# 10x faster but NOT cryptographically safe → collision prob much higher
# 对于 idempotency 通常 OK (反正不是 adversarial), 但 production 还是 BLAKE/SHA
```

**实战推荐**: BLAKE2b-128, 16 字节 / 32 hex char. SHA 也行, 别用 MD5.

### 1.4 完整实现

```python
import hashlib
import json
from decimal import Decimal

def canonicalize(obj):
    """Make any obj deterministic-serializable."""
    if isinstance(obj, dict):
        return {k: canonicalize(v) for k, v in sorted(obj.items())}
    if isinstance(obj, (list, tuple)):
        return [canonicalize(x) for x in obj]
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, float):
        # 强制 6 位小数, 避免 1.0000001 vs 1.0
        return f"{obj:.6f}"
    return obj

def make_idempotency_key(
    tenant_id: str,
    session_id: str,
    tool_name: str,
    args: dict,
) -> str:
    canonical = {
        'tenant': tenant_id,
        'session': session_id,
        'tool': tool_name,
        'args': canonicalize(args),
    }
    content = json.dumps(canonical, sort_keys=True, separators=(',', ':'))
    return hashlib.blake2b(content.encode(), digest_size=16).hexdigest()
    # 32 hex chars, ~10^-19 collision prob for 1 billion keys
```

### 1.5 工具

- **Python**: `hashlib` (stdlib), `xxhash` (PyPI for non-crypto fast hash)
- **Go**: `crypto/sha256`, `golang.org/x/crypto/blake2b`
- **Validation**: 用 `pydantic.BaseModel` 当 args schema, 然后 `.json()` 自动 canonical
- **Storage**: Redis Hash 存 key → metadata; 或 KV (key = idem_key prefix)

---

## ⚙️ Problem 2: Dedup State Machine — in_flight / completed / failed + race

3 态比单态 ("seen yes/no") 多承载了**并发场景**.

### 2.1 为什么需要 in_flight 态

考虑无 in_flight 的简化版:

```python
def transfer(args, idem_key):
    if redis.get(f'idem:{idem_key}'):
        return cached_result  # 已有
    result = bank.transfer(args)  # 第一次
    redis.set(f'idem:{idem_key}', result, ex=86400)
    return result
```

**Bug**: 两个并发 request 同时到, 都看到 `redis.get` 为空, 都去 `bank.transfer` → 双花.

加 in_flight:

```python
def transfer(args, idem_key):
    # Atomic: SETNX 拿锁
    ok = redis.set(f'idem:{idem_key}', json.dumps({
        'state': 'in_flight',
        'started_at': time.time()
    }), ex=86400, nx=True)

    if not ok:
        # Key 已存在, 看是 in_flight 还是 completed
        existing = json.loads(redis.get(f'idem:{idem_key}'))
        if existing['state'] == 'completed':
            return existing['result']
        elif existing['state'] == 'in_flight':
            return wait_or_409(idem_key)
        elif existing['state'] == 'failed':
            # 删除 key, 重试 (落到下面 execute)
            redis.delete(f'idem:{idem_key}')
            return transfer(args, idem_key)  # recurse once

    # 第一次进来, 真正执行
    try:
        result = bank.transfer(args)
        redis.set(f'idem:{idem_key}', json.dumps({
            'state': 'completed',
            'result': result,
            'completed_at': time.time(),
        }), ex=86400)
        return result
    except RetryableError as e:
        redis.set(f'idem:{idem_key}', json.dumps({
            'state': 'failed',
            'error': str(e),
        }), ex=300)  # 短 TTL, 让 retry 可以快回来
        raise
    except FatalError as e:
        # Tombstone: 不可重试
        redis.set(f'idem:{idem_key}', json.dumps({
            'state': 'failed_permanent',
            'error': str(e),
        }), ex=86400)
        raise
```

### 2.2 in_flight 等待策略

第二个 request 撞到 in_flight, 怎么办?

**Option A: Poll wait**

```python
def wait_or_409(idem_key, max_wait_sec=10, poll_interval_sec=0.2):
    deadline = time.time() + max_wait_sec
    while time.time() < deadline:
        existing = json.loads(redis.get(f'idem:{idem_key}') or '{}')
        if existing.get('state') == 'completed':
            return existing['result']
        if existing.get('state', '').startswith('failed'):
            return retry_or_error(idem_key)
        time.sleep(poll_interval_sec)

    # 等超时
    return {
        'error': 'in_flight_timeout',
        'idem_key': idem_key,
        'message': 'Original call still running, poll later with get_status'
    }, 409
```

**Option B: Async wait** (better)

```python
# Redis Pub/Sub 通知
async def wait_async(idem_key, timeout=10):
    pubsub = redis.pubsub()
    await pubsub.subscribe(f'idem_done:{idem_key}')
    try:
        msg = await asyncio.wait_for(pubsub.get_message(), timeout=timeout)
        return msg['data']
    except asyncio.TimeoutError:
        return {'error': 'in_flight_timeout'}, 409

# 完成时
async def mark_completed(idem_key, result):
    await redis.set(...)
    await redis.publish(f'idem_done:{idem_key}', json.dumps(result))
```

Pub/Sub 比 poll 快, latency 低, 但要求 Redis Pub/Sub 可用.

**Option C: Return 409 immediately** (simplest)

```python
if existing['state'] == 'in_flight':
    return {'error': 'concurrent', 'retry_after': 1}, 409
# Agent / client 自己决定是否 wait + retry
```

适合下游 client 已经有 retry 机制的场景.

### 2.3 race 极端 case — TOCTOU (Time-of-check-to-time-of-use)

```python
# Bad
if redis.get(key) is None:  # check
    redis.set(key, 'in_flight')  # use
    execute()
# 两个 request 都过 check, 都执行 set, 都执行 — race
```

**Fix**: 用 atomic SETNX:

```python
ok = redis.set(key, value, nx=True, ex=ttl)
if not ok:
    # Lost the race
    handle_existing(key)
else:
    # Won the race
    execute()
```

Redis `SET NX` 是 atomic, 保证只有一个 setter 成功.

### 2.4 Distributed lock pattern (Redlock)

如果有多 Redis instance / cluster:

```python
# Redlock (Redis 官方推荐 distributed lock 算法)
from redlock import Redlock

dlm = Redlock([
    {"host": "redis-1", "port": 6379},
    {"host": "redis-2", "port": 6379},
    {"host": "redis-3", "port": 6379},
])

lock = dlm.lock(f'idem:{idem_key}', ttl=30000)  # 30s
if lock:
    try:
        execute()
    finally:
        dlm.unlock(lock)
else:
    handle_in_flight()
```

**注意**: Martin Kleppmann 对 Redlock 有质疑 (clock drift / GC pause 下不安全). 高安全场景用 **fencing token** 或 **ZooKeeper / etcd**.

### 2.5 Tools

- **Redis**: `SET NX EX`, `SCAN`, Pub/Sub for wait notification
- **Redlock**: distributed lock across Redis cluster
- **ZooKeeper / etcd**: 强一致性锁 (CP > Redis 的 AP)
- **DB unique constraint**: `INSERT ... ON CONFLICT DO NOTHING` 作为最后兜底
- **Temporal / Cadence**: workflow-level dedup (自动 idempotency per workflow_id)

---

## ⚙️ Problem 3: TTL Design + Storage Tier — Redis hot + DB cold + bank ledger long-term

TTL 决定 dedup window. 怎么平衡「越长越安全」vs「越长越可能误判合法重试为 dup」.

### 3.1 多 tier 存储设计

```
┌────────────────────────────────────────────────────┐
│  Tier 1: Redis (hot, in-memory)                    │
│  - TTL: 24h                                        │
│  - Latency: < 1ms                                  │
│  - Capacity: 1M keys easily                        │
│  - 用途: 实时 dedup, 大部分 retry 在此命中            │
└────────────────────────────────────────────────────┘
                       ↓ TTL 到期 or cache miss
┌────────────────────────────────────────────────────┐
│  Tier 2: DB (warm, persistent)                     │
│  - TTL: 30 days                                    │
│  - Latency: < 50ms                                 │
│  - 表: idempotency_log (idem_key UNIQUE)          │
│  - 用途: 长尾 retry, Redis cold start 恢复          │
└────────────────────────────────────────────────────┘
                       ↓ archive
┌────────────────────────────────────────────────────┐
│  Tier 3: Cold storage / Ledger (permanent)         │
│  - 银行 / 第三方对账系统的 transaction_id           │
│  - 用途: 真正长期 dedup 兜底 (业务无限期)            │
└────────────────────────────────────────────────────┘
```

### 3.2 TTL 数值经验值

| 场景 | TTL | 理由 |
|---|---|---|
| HTTP transport retry | 60 sec | 最长 retry window 一般几十秒 |
| LLM re-issue tool call | 5 min | LLM session 内 retry |
| 同 session 多 turn | 1 hour | 用户在一次对话里 |
| 跨 session 但同 user | 24 hours | Stripe 默认 |
| 长尾 reconciliation | 30 days | 月底对账 |
| Banking ledger | Permanent | 法律要求 |

**注意**: TTL 太长会有**误判合法 retry 为 dup** 的风险:

```
T=0:    用户转账 100 (key=K1)
T=2h:   用户又想转 100 (合法新意图, 但 args 相同 → key=K1)
        → 24h TTL 内, 被当作 dup, 第二次没执行
```

**解法**: 用户合法重复操作时, **客户端要主动加 nonce 区分新意图**:

```python
# UI 给用户一个明确选择
# "Transfer $100 to John" → 第一次
# "I already sent it; this is a new transfer" → 第二次, UI 生成新 client_request_id
```

或 short TTL + 下游 ledger 兜底 (下面 3.3).

### 3.3 Bank ledger 作为永久兜底

```python
@tool(idempotent=True)
def transfer_funds(from_acc, to_acc, amount, _idem_key):
    # Layer 1: Redis 24h
    cached = redis_dedup(_idem_key)
    if cached: return cached

    # Layer 2: DB 30d
    db_record = db.idempotency_log.find(idem_key=_idem_key)
    if db_record and db_record.state == 'completed':
        return db_record.result

    # Layer 3: Bank ledger - 用 our_reference 在 bank 那边查
    # Bank API 接受 external_ref 字段, bank 自己 dedup
    bank_result = bank.transfer(
        from_acc, to_acc, amount,
        external_ref=_idem_key,  # bank 自己也认这个
        idempotency_key=_idem_key  # Stripe-style header
    )

    # Bank 看到重复 external_ref, 返回原 transaction 信息
    return bank_result
```

**关键**: 我方 wrapper 24h TTL 是 fast path; bank 那边永久 transaction record 是终极 truth.

### 3.4 Reconciliation job

```python
# 每天跑, 检查 our DB vs bank ledger 一致性
def reconcile():
    yesterday = datetime.now() - timedelta(days=1)
    our_records = db.idempotency_log.filter(
        completed_at__gte=yesterday,
        state='completed'
    )

    for r in our_records:
        bank_record = bank.lookup(external_ref=r.idem_key)
        if not bank_record:
            # 我方说成功了, 但 bank 没记录 → 异常, 告警
            alert(f'Missing in bank: {r.idem_key}')
        elif bank_record.amount != r.amount:
            # Amount mismatch → severe
            alert(f'Amount mismatch: {r.idem_key}, ours={r.amount}, bank={bank_record.amount}')

    # 反向: bank 有, 我方没
    bank_records = bank.list(date=yesterday)
    for b in bank_records:
        our = db.idempotency_log.find(idem_key=b.external_ref)
        if not our:
            alert(f'Untracked bank transaction: {b.external_ref}')
```

### 3.5 Cardinality math

1M users × 50 tool calls / day = 50M keys/day.

- Redis: 50M × 100 bytes = 5 GB. 单 Redis instance OK. Cluster 更稳.
- DB: 50M × 500 bytes = 25 GB/day, archive 后 manageable.
- Cost: Redis $50/month for 8GB, Postgres $200/month for 100GB. 完全 affordable.

### 3.6 Tools

- **Redis**: 标准, AWS ElastiCache 托管
- **DragonflyDB / KeyDB**: Redis 兼容, 更快
- **Postgres**: 长期存储, `idempotency_log` 表带 `UNIQUE(idem_key)`
- **DynamoDB / Spanner**: serverless 替代
- **Apache Iceberg / Parquet on S3**: cold archive
- **Datafold / dbt**: reconciliation job 编排

---

## ⚙️ Problem 4: Failure Modes — Redis down, key collision, agent retries with different args

每个 failure mode 都要有明确 policy.

### 4.1 Redis down

```python
def get_dedup_state(idem_key):
    try:
        return redis.get(f'idem:{idem_key}')
    except RedisConnectionError as e:
        log.error("Redis down, failing closed")
        # Policy depends on tool safety
        if tool.safety == 'destructive':
            raise SystemUnavailable("Idempotency layer unavailable for destructive tool")
        elif tool.safety == 'write':
            # Fall back to DB
            return db.idempotency_log.find(idem_key=idem_key)
        else:  # read
            # Skip dedup, allow call (will retry idempotently)
            return None
```

**Policy table**:

| Tool safety | Redis down | DB also down |
|---|---|---|
| `read` | Skip dedup, allow | Skip dedup, allow |
| `write` (idempotent) | Use DB | Local in-memory dedup (5 min window) |
| `destructive` | **Fail closed**, refuse | **Fail closed** |

**Fail closed for destructive** = 宁可不可用, 不可双花.

### 4.2 Key collision (theoretically impossible but...)

SHA-256 truncated to 32 hex = 128 bit. Birthday collision at sqrt(2^128) = 2^64 keys. **Practically 0** for any real cardinality (50M keys → collision prob ~10^-25).

但**逻辑 collision** (same args 同, 不同意图) 真实发生:

```
User: 上午 9 点转 100 给 John
User: 下午 3 点又想转 100 给 John (合法新意图)
→ args 完全相同, hash 相同, 24h TTL 还在 → 被 dedup, 没转出去
```

**Mitigations**:

1. **Document behavior**: 客户知道「同 args 24h 内只执行一次」
2. **Short TTL on user-facing tools**: 5 min, 长尾依赖 bank ledger
3. **UI 加 explicit confirm**: "You already transferred $100 to John today. New transfer or duplicate?"
4. **`force_new_intent` flag**: tool 接受 `force=True` 跳过 dedup
5. **Time bucket in key**: `key = hash(args + day(now))` — 但破坏 cross-day retry

### 4.3 Agent retries with different args after partial failure

最经典的灾难场景:

```
T=0: agent → transfer_funds(100), idem_key=K1
T=1: bank API timeout (但 actually 已 commit)
T=2: agent thinks: "失败了, 重试"
T=2: agent → transfer_funds(100), idem_key=K1 (same args)
     → wrapper dedup, 返回 cached result (没 cache, 因为没 commit)
     → 但 wrapper 不知道 bank actually 已 commit
T=3: bank 又被调一次, 双花

或者更糟:
T=2: agent → "上次失败了, 我换 110 块试试"
T=2: agent → transfer_funds(110), idem_key=K2 (different!)
     → wrapper 看到 new key, 执行
     → bank 收到第二次, 100 + 110 都扣
```

**解法层**:

**Layer 1 — Tool design**: 提供 status query tool

```python
@tool
def get_transfer_status(transfer_ref):
    """Query if a previous transfer succeeded, by external_ref."""
    return bank.lookup_by_external_ref(transfer_ref)

# Prompt 提示 LLM:
# "If a transfer call times out, FIRST call get_transfer_status to confirm.
#  Do NOT retry with adjusted args until you've confirmed the original failed."
```

**Layer 2 — Wrapper state**: 把 in_flight + "unknown if downstream committed" 显式标记

```python
class TransferResult:
    state: str  # 'committed' | 'failed' | 'unknown'

# Wrapper 在 timeout 时:
if timeout:
    return TransferResult(state='unknown', idem_key=K1)
    # Agent 看到 'unknown', 知道得 get_status 查
```

**Layer 3 — Bank-side dedup**: bank 自己接受 `external_ref` 并 dedup

```python
bank.transfer(amount, external_ref=idem_key, idempotency_key=idem_key)
# 即使 wrapper 没 cache, bank 看到 external_ref 已存在 → 返回原 transaction
```

**Layer 4 — Reconciliation**: 定时对账, 修 'unknown' 状态

### 4.4 LLM 生成相似但不一样的 args

```python
# 第一次
agent: transfer_funds(from='Account 12345', to='John Smith', amount=100.00)

# Retry, LLM 微调
agent: transfer_funds(from='Account 12345', to='John Smith', amount=100)  # int vs float
agent: transfer_funds(from='account 12345', to='John Smith', amount=100.00)  # case
agent: transfer_funds(from='Account 12345', to='John  Smith', amount=100.00)  # extra space
```

**Args canonical 化** + **strict schema**:

```python
class TransferArgs(BaseModel):
    from_account: str  # 强制 regex 验证, 'Account ' prefix 自动 strip
    to_account: str  # 同上
    amount: Decimal  # 强制 Decimal, 不收 float/int 混
    currency: str = 'USD'

    @validator('to_account', 'from_account')
    def normalize(cls, v):
        return ' '.join(v.strip().lower().split())  # 多空格压缩 + lowercase
```

经过 schema → canonical → hash 后, 上述变体全部 hash 到同 key.

### 4.5 Worker crash mid-execution

```
T=0: worker_1 picks task, marks in_flight in Redis
T=1: worker_1 calls bank, bank starts processing
T=2: worker_1 CRASHES (k8s pod killed)
T=2: in_flight Redis entry 还在 (TTL 24h), 没人 mark completed
T=10: worker_2 picks task, sees in_flight → wait
T=20: worker_2 wait timeout → 409
T=300: in_flight TTL still alive, no one resumes
T=86400 (24h): TTL 到期, 但 bank 早就 commit 了 → 这时 retry 会双花
```

**解法**: in_flight 加 worker heartbeat:

```python
class InFlightRecord:
    state = 'in_flight'
    worker_id: str
    started_at: float
    last_heartbeat: float  # worker 每 5s 更新

def check_stale_in_flight(idem_key):
    rec = redis.get(f'idem:{idem_key}')
    if rec.state == 'in_flight':
        if time.time() - rec.last_heartbeat > 30:
            # Worker dead, take over
            # 但要 query bank: did it commit?
            bank_state = bank.lookup_by_ref(idem_key)
            if bank_state.committed:
                # Bank commit 成功了, 标记 completed
                redis.set(idem_key, completed_state)
                return bank_state.result
            else:
                # Bank 也没收到, 重新执行
                redis.delete(idem_key)
                return execute_again()
```

### 4.6 Tools

- **Redis Sentinel / Cluster**: Redis HA
- **OpenTelemetry**: trace 整条 idempotency 决策路径
- **Sentry / Datadog**: alert on idem hit anomalies
- **Property-based testing**: Hypothesis (Python), QuickCheck patterns

---

## ⚙️ Problem 5: Cross-Vendor Idempotency — when downstream doesn't support idem_key

50% 的下游 API 不原生支持 idempotency header. 怎么办?

### 5.1 Vendor 支持矩阵

| Vendor | 支持 | Header / Field |
|---|---|---|
| **Stripe** | ✅ | `Idempotency-Key` header, 24h |
| **Square** | ✅ | `idempotency_key` body field |
| **PayPal** | ✅ | `PayPal-Request-Id` header, 30d |
| **AWS SQS** | ✅ partial | `MessageDeduplicationId` (FIFO queue) |
| **Twilio** | ❌ no native | 但 messageSid 可 query |
| **SendGrid** | ❌ | 自己 dedup |
| **传统银行 API** (e.g., SWIFT) | ⚠️ varies | `EndToEndId` 或 custom ref |
| **Internal microservice** | ⚠️ depends | 看自己怎么写的 |

### 5.2 Pattern A: Vendor 原生支持 — pass-through

```python
def transfer_via_stripe(args, idem_key):
    return stripe.transfers.create(
        amount=args['amount'],
        destination=args['destination'],
        idempotency_key=idem_key  # ⭐ pass-through
    )
    # Stripe 看到同 idem_key 重复请求, 返回原始 result
    # 我方 wrapper 24h + Stripe 24h, 双层兜底
```

**注意**: vendor 的 TTL 可能短 (Stripe 24h). 跨 24h 还想 dedup 得靠 wrapper.

### 5.3 Pattern B: Vendor 不支持 — wrapper 全权

```python
def transfer_via_legacy_bank(args, idem_key):
    # Wrapper 必须保证 bank 只被调一次
    with distributed_lock(f'transfer:{idem_key}', ttl=30):
        # 再 check cache (double-check pattern)
        cached = redis.get(f'idem:{idem_key}')
        if cached and cached['state'] == 'completed':
            return cached['result']

        # Mark in_flight
        redis.set(f'idem:{idem_key}', {'state': 'in_flight'}, ex=86400)

        try:
            # Bank API 没 idem 支持, 直接调
            result = bank_legacy.wire_transfer(
                amount=args['amount'],
                to=args['to'],
                from_=args['from'],
                ref=idem_key  # 当 reference 传, bank 可能记 record 但不 dedup
            )
            redis.set(f'idem:{idem_key}', {
                'state': 'completed',
                'result': result,
            }, ex=86400)
            return result
        except TimeoutError:
            # 危险: bank 可能 commit 了也可能没
            redis.set(f'idem:{idem_key}', {
                'state': 'unknown',
                'requires_reconciliation': True,
            }, ex=86400)
            raise IdempotencyUnknown(idem_key)
```

### 5.4 Pattern C: Vendor 有 query API 但无 idem

最常见的中间地带 — vendor 没 idem header, 但有「按 external_ref 查 transaction」API.

```python
def transfer_via_bank_with_query(args, idem_key):
    # 1. 先查 vendor 是否已 commit
    existing = bank.search(external_ref=idem_key)
    if existing:
        return existing  # 已 commit, 不再调

    # 2. 没 commit 才调
    result = bank.create_transfer(
        amount=args['amount'],
        external_ref=idem_key,  # bank 存这个 ref
    )

    # 3. 调成功后 cache
    redis.set(f'idem:{idem_key}', result, ex=86400)
    return result
```

**Race condition**:

```
T=0: thread_1: search(ref=K1) → not found
T=1: thread_2: search(ref=K1) → not found
T=2: thread_1: create(ref=K1) → success
T=3: thread_2: create(ref=K1) → success again (vendor 不 dedup) → 双花
```

**Fix**: 加 wrapper-side distributed lock 串行化:

```python
def transfer_safe(args, idem_key):
    with distributed_lock(f'idem:{idem_key}', ttl=30):
        # 串行 → 安全
        return transfer_via_bank_with_query(args, idem_key)
```

### 5.5 Pattern D: Vendor 完全裸 — 自己加 reconciliation

最差情况, vendor 既不 dedup 也不 query, 只是 fire-and-forget:

```python
def send_via_legacy_sms(args, idem_key):
    # 这种 vendor 我们没法 100% safe
    # 只能 best-effort: wrapper 串行 + 业务上接受小概率重复

    with distributed_lock(f'idem:{idem_key}', ttl=30):
        cached = redis.get(f'idem:{idem_key}')
        if cached:
            return cached  # 但不保证 vendor 那边没重复

        result = legacy_sms.send(args)  # vendor 返个 message_id
        redis.set(f'idem:{idem_key}', result, ex=86400)
        return result

# 配合 reconciliation:
def reconcile_sms():
    sent_today = db.find(sent_at__gte=yesterday)
    grouped = group_by(sent_today, key=['phone', 'content_hash'])
    for phone_content, msgs in grouped.items():
        if len(msgs) > 1:
            alert(f'Duplicate SMS: {phone_content}, {len(msgs)} times')
```

### 5.6 Decision tree

```
Vendor 支持 idempotency-key header?
  ├─ YES → Pattern A: pass-through (最干净)
  └─ NO
      ├─ Vendor 提供 query-by-ref API?
      │   ├─ YES → Pattern C: check-then-execute + wrapper lock
      │   └─ NO
      │       ├─ Vendor 是 idempotent at storage (设置类操作)?
      │       │   └─ YES → 直接调, repeat OK
      │       └─ NO → Pattern D: best-effort + reconciliation
      └─ Vendor 是我们自己 service?
          └─ 改造 vendor 支持 idem-key (从上游解决)
```

### 5.7 Voice agent 实战

你的 voice agent 跨 7 markets, 每个 market 的 repayment channel 都不同:

```
Indonesia: GoPay (no native idem) → Pattern C with query
Brazil: Mercado Pago (idem support) → Pattern A
Mexico: SPEI (legacy bank API) → Pattern D + 严格 reconcile
Philippines: GCash (idem support, 24h) → Pattern A
...
```

**统一抽象**: payment-gateway wrapper 层暴露统一 `transfer(args, idem_key)` 接口, 内部按 market 选 pattern. Agent / LLM 不感知差异.

### 5.8 Tools

- **Stripe SDK**: `idempotency_key` parameter
- **MessageDeduplicationId** (AWS SQS FIFO)
- **Temporal**: workflow_id 自动 idempotency
- **Kafka with exactly-once semantics** (transactional producer)
- **Outbox pattern**: DB 写 + 消息队列发统一 transaction
- **Sage / Saga**: cross-service compensating transaction framework

---

# Part 3 · 把 5 个问题串起来看

这 5 个 deep problem 其实是**同一根线的 5 个 layer**, 从抽象到具体:

1. **Key generation** 决定「同意图怎么识别」— 这是语义边界
2. **State machine** 决定「并发场景下怎么协调」— 这是 race 防御
3. **TTL + storage tier** 决定「这个保护持续多久 + 怎么存」— 这是空间换时间的工程
4. **Failure modes** 决定「infra 出问题时系统怎么活」— 这是 reliability 兜底
5. **Cross-vendor** 决定「下游不配合时怎么自己撑」— 这是 real production 现实

面试场把这 5 个 layer 都讲清楚 + 至少 1 个 "我自己 production 踩过 X 坑" 的故事, 就是 staff-level tool calling 系统设计.

**反过来看 5 个 layer 互相依赖**:

```
Key generation (1) 不严谨 → State machine (2) 没法工作
State machine (2) 不严谨 → TTL (3) 长短都救不了
TTL (3) 设得激进 → Failure mode (4) 出问题概率大
Failure mode (4) 没 policy → Cross-vendor (5) 没法兜底
```

5 层缺 1 都是坑.

---

## 必问 clarifying questions

**1. Idempotency source**

> "Is the idempotency key generated by the LLM, the agent runtime, or the tool server? Each has tradeoffs."

**2. Dedup window**

> "How long do we remember keys — minutes (transient retry) or hours (full session)? Multi-tier (Redis hot + DB cold)?"

**3. Failure modes to cover**

> "Network timeout (don't know if executed), LLM re-issue (clear duplicate), parallel agents on same user (race), Redis down (fail-closed?)"

**4. Underlying API**

> "Does the bank API already accept idempotency_key (Stripe-style)? Or do we need to wrap an idem-unaware vendor?"

**5. Cost of double-execute**

> "Worst case if we double-charge — UX issue (refundable) or compliance event (audited / customer harm / regulator)?"

---

## 5 步框架 (sample 45-min answer 节奏)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify + define at-most-once vs at-least-once vs exactly-once |
| 5-15 min | Key generation (agent-side, sha256, canonical args) |
| 15-25 min | State machine (in_flight / completed / failed) + race handling |
| 25-35 min | TTL + storage tier (Redis 24h + DB 30d + bank ledger permanent) |
| 35-45 min | Failure modes + cross-vendor patterns |
| 45-55 min | Production hardening (audit, reconciliation, monitoring) |
| 55-60 min | Q&A |

---

## 我会这样答（sample monologue）

> "Clarify — *[假设: bank API 不原生支持 idempotency_key, dedup window 24h, worst-case double charge = compliance event, agent runtime owns the key, multi-tenant SaaS]*.
>
> **3-layer design**:
>
> **Layer 1: Idempotency key generation (at agent runtime)**
>
> Runtime, not LLM, generates `idem_key = blake2b(tenant + session + tool + canonical(args))`. Why runtime: LLM sampling means same intent might emit different key. Why include `tenant`: cross-tenant collision is SaaS death.
>
> **Layer 2: 3-state dedup (Redis hot + DB warm)**
>
> ```
> GET idem:{key}
>   in_flight → poll 10s OR 409 with Retry-After
>   completed → return cached result
>   not exist / failed → SETNX with TTL 24h, execute
> ```
>
> Pub/Sub for fast wake-up on in_flight wait. DB tier for >24h reach.
>
> **Layer 3: Cross-vendor wrapper**
>
> Bank not idem-aware. Pattern: distributed lock per key + `external_ref` pass-through + reconciliation job. If bank query-by-ref API exists, check-then-execute. Otherwise best-effort + daily reconcile.
>
> **Edge cases**:
>
> **EC1: Network timeout — bank may or may not have committed**
> → Return state='unknown' to agent. Agent calls `get_transfer_status(ref)` to confirm. Don't blindly retry.
>
> **EC2: Agent retries with adjusted args (LLM thinks need to fix)**
> → New args → new key → new transaction. **This is LLM's responsibility**. Prompt-level guidance: "Always retry SAME args first. Only adjust after status query."
>
> **EC3: Redis down**
> → Fail closed for destructive tools. Fall back to DB lookup. If DB also down → tombstone error to caller. **Never fail-open on transfer_funds**.
>
> **EC4: Logical key collision (same args 24h later, legitimate new intent)**
> → User UI provides explicit "this is new" affordance. Tool accepts `force_new=True` to bypass dedup.
>
> **EC5: Worker crash mid-execution**
> → In_flight has worker heartbeat. Stale > 30s → re-query bank via `external_ref`, if committed mark completed, else re-execute.
>
> **Production hardening (1 min wrap)**:
> - Monitor: dedup hit rate (~2% expected), p99 in_flight wait, key cardinality
> - Audit log: every hit with reason (retry / dup / collision suspicion)
> - Reconciliation: nightly compare our log vs bank ledger
> - Property-based test: concurrent invocation invariant (never > 1 commit per key)
> - Failure isolation: Redis cluster + DB read replica, no SPOF
>
> **Resume from PayLater context**: I built this exact pattern on the voice agent for 7 markets. 5 of those markets had idem-supporting payment channels, 2 didn't (legacy banks in MX and ID). For the legacy 2 we used Pattern C — check-then-execute via vendor's transaction lookup API + distributed lock. After deployment, double-charge incidents dropped from ~3/month to 0 in 6 months."

---

## 简历专属 reframe

| 题角度 | 你的项目 |
|---|---|
| Idempotency key in tool layer | Voice agent (TikTok Global Payment) — multi-tenant retry handling |
| In-flight wait / race | BNPL chatbot intent fanout to sub-agents |
| Underlying API dedup | TikTok payment — Stripe-style transaction.external_ref |
| Cross-vendor pattern | 7 markets each different payment channel, some idem-aware some not |
| Audit trail | Compliance for debt collection: every tool call audit-logged |
| Reconciliation | Daily reconcile between our payment_log and bank ledger |

**主动 quote**:

> "On the voice agent, we hit this exact issue early on. Network retry to GoPay (Indonesia) caused one customer to receive 2 collection SMS. We added Redis-based dedup keyed on `tenant_id + session_id + tool_name + sha256(canonical_args)`, 24h window. Hit rate ~2% (real retries). Zero duplicate SMS in subsequent 6 months. Bigger learning was **state='unknown' for timeouts** — initially we'd auto-retry on timeout, but that risked double-commit when bank actually succeeded. Switched to returning 'unknown' to agent + companion `get_status` tool. LLM learned to query before retrying."

---

## 5 follow-ups

**Q1**: "If Redis goes down, what's the policy — fail open or closed?"

**A**: Tool-class dependent.
- **Destructive (transfer / charge / delete)**: fail closed — refuse to execute. Worse to over-execute than under-respond.
- **Write idempotent (update_profile)**: fall back to DB tier; if DB also down, local in-memory dedup with stricter 5-min window
- **Read (search / lookup)**: fail open, skip dedup, allow call (read is naturally idempotent)

**Q2**: "Bank API does have idempotency_key support but expires after 5 min. Yours wants 24h."

**A**: 2-layer:
- Bank's 5 min handles transient transport retry
- Our 24h handles cross-session legitimate retry (user closes laptop, comes back later)
- Beyond 24h: bank's permanent transaction record + `external_ref` lookup
- Document the 3 windows clearly to clients

**Q3**: "Agent decides to retry with adjusted args (e.g., +$10) after error. New idem_key. But original might still execute."

**A**: This is **the LLM's error**, runtime can't catch it directly. Defenses:
- Prompt-level: "On error, retry SAME args first. Only adjust after confirming original didn't execute via `get_transaction_status`."
- Tool always returns a `transaction_ref` on success/unknown. LLM can `get_transaction(ref)` to verify before retrying.
- Compensating action: explicit `cancel_transfer(ref)` available if double execution detected.
- Audit: tag 'LLM-initiated retry with adjusted args' for review.

**Q4**: "How would you test idempotency?"

**A**: Multi-layer testing:
- **Unit**: 2 concurrent calls with same key → 1 execution, both get same result
- **Integration**: Inject network failure mid-call, verify retry idempotent
- **Property-based**: `hypothesis` generates random arg sequences, invariant: `count(distinct execution) <= count(distinct key)`
- **Chaos**: Kill Redis mid-flight, verify graceful degradation
- **Production shadow**: replay real traffic with idem turned off, count would-be-doubles

**Q5**: "What if the tool is a 3rd-party API we don't control and they don't support idempotency?"

**A**: Cross-vendor pattern (Problem 5 details):
- **Wrapper layer** owned by us — single point of dedup
- **Distributed lock** per key (Redis Redlock or ZooKeeper) serializes concurrent calls
- **Vendor query API** (if exists): check `external_ref` before execute
- **Reconciliation job**: nightly compare our log vs vendor's authoritative record
- **Worst case** (vendor neither dedup nor queryable): best-effort + business-level acceptance of small dup rate + manual compensation flow

---

## ❌ 易错点

1. **让 LLM 生成 idempotency_key** — non-deterministic, 不可靠
2. **Key 不含 tenant_id** — 跨租户撞车, 安全事故
3. **没考虑 in-flight race** — `SET NX` 是关键
4. **TTL 太长** — collision risk + memory cost
5. **TTL 太短** — 跨 session 重试漏 dedup
6. **Fail-open on Redis down** — destructive tool 默认越界, 可能双花
7. **没 audit log** — dedup hit 应该可观察
8. **Args 不 canonical 化** — 同意图不同 hash, 等于没 dedup
9. **跨 vendor 无 wrapper** — 下游不支持就裸奔
10. **没 reconciliation** — wrapper 状态和 vendor 账本最终不一致

---

## ✅ 加分项

1. **Agent-side key gen + sha256/blake2b hashing**
2. **3-state state machine** (in_flight / completed / failed)
3. **`SET NX` + 短 poll** 处理 race
4. **Pub/Sub 通知 in_flight done** (vs 单纯 poll)
5. **Stripe-style key passthrough** to underlying API
6. **Multi-tier storage** (Redis 24h + DB 30d + bank ledger permanent)
7. **Fail-closed on destructive tools** + fail-open on read
8. **Reconciliation job** nightly
9. **Cardinality math** (50M keys/day, Redis cluster handles fine)
10. **Audit hit logging** with reason
11. **Cross-vendor pattern decision tree**
12. **Property test mention** (hypothesis / concurrent invocation)
13. **Quote voice agent SMS dedup story** + 7-market vendor variance

---

## 一句话总结

> **Idempotent tool = "runtime 生成确定性 key + 3 态机协调并发 + 短长 TTL 双 tier + Redis 挂时 fail-closed + 跨 vendor wrapper 兜底 + 持续对账"**.
>
> Agent 时代这一层只会越来越关键. LLM 比 human 更容易触发 retry, 而 idempotency 是阻止灾难的最后防线. 这道题答得好 = 你真在 production 跑过 destructive tools.

---

## Cheat Sheet (印 1 页随身)

```
Idempotency key:
  Source: agent runtime (not LLM, not server)
  Composition: tenant_id + session_id + tool_name + canonical(args)
  Hash: BLAKE2b-128 (16 bytes / 32 hex)
  Canonical: sort_keys + Decimal precision + str normalize

State machine:
  none → in_flight → completed
              ↓
            failed (retryable) → none
              ↓
        failed_permanent (tombstone)

In-flight race:
  redis.set(key, in_flight, nx=True, ex=ttl)  # atomic
  If exists in_flight: poll 200ms or Pub/Sub wait, max 10s, else 409

TTL multi-tier:
  Redis (hot):  24h
  DB (warm):    30d
  Bank ledger:  permanent
  + Reconciliation nightly

Failure policy:
  Tool safety  | Redis down  | DB down
  read         | skip dedup  | skip dedup
  write idem   | use DB      | local 5m
  destructive  | FAIL CLOSED | FAIL CLOSED

Key collision:
  Cryptographic: 2^-128 negligible
  Logical: same args 24h later legitimate
    → short TTL + bank ledger
    → force_new flag in UI

Agent-retry-with-adjusted-args:
  → tool returns state='unknown' on timeout
  → companion get_status tool
  → prompt: retry SAME args first

Cross-vendor patterns:
  A. Native idem header (Stripe) → pass-through ⭐
  B. Wrapper full ownership (no support)
  C. Check-then-execute via query API + lock
  D. Best-effort + reconciliation (legacy)

Worker crash:
  in_flight entry: worker_id + last_heartbeat
  Stale > 30s → re-query vendor by external_ref
              → if committed: mark completed
              → if not: re-execute

Cost / cardinality:
  1M users × 50 calls/day = 50M keys
  Redis: 5GB, single cluster OK
  Hit rate: ~2% (real retry), monitor anomaly > 5%

Monitoring:
  - dedup hit rate (alert if > 10%, sign of bad upstream)
  - in_flight wait p99 (alert > 1s)
  - key cardinality growth
  - reconciliation mismatch count

Test:
  - Concurrent same-key invocation property
  - Chaos: Redis kill mid-flight
  - Replay real traffic with idem disabled, count doubles

红线:
  - LLM-generated key
  - Fail-open on infra failure for destructive
  - TTL too long (logical collision)
  - Tool inner not idempotent
  - No reconciliation
  - No audit
```
