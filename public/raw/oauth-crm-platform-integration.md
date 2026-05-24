## 题目（verbatim）

> "Design an **OAuth 1.0/2.0 integration** bridging between a client's **CRM** and your **platform API**. Cover token exchange, middleware placement, retry logic, and credential rotation."

**出处**: fde.academy 列出的 FDE 核心 integration 题. Palantir / Salesforce / Databricks / Google Cloud FDE 都问过.

**Round**: Technical Integration (45-60 min)

---

## 这道题在考什么

考你 **enterprise integration 实战**. OAuth 在每家 customer 都不一样:

1. **OAuth 2.0 4 个 grant types 知不知道** — authorization_code / client_credentials / refresh_token / device_code
2. **Token storage + rotation** — 真生产 deployment 必须 handle
3. **Middleware placement** — SDK / proxy / dedicated service?
4. **Failure modes** — token expire mid-call, refresh race, revocation
5. **Multi-tenant secrets management**

不考 "OAuth 是什么", 考 "你 production 部署过 OAuth integration".

---

# Part 1 · 教学讲解 — 先把概念讲透

## 1. 三个术语先解释

**OAuth 2.0**: 一个**授权协议** (不是认证), 解决的问题是「让 A 应用代表用户去访问 B 应用的数据, 但不需要把用户的密码告诉 A」. 这是现代 SaaS 互联互通的事实标准.

**CRM**: Customer Relationship Management, 客户关系管理系统. 存储客户、销售线索、订单、跟进记录的系统. 代表产品: Salesforce, HubSpot, Zoho, Pipedrive, 字节内部的 Lark CRM, Microsoft Dynamics.

**Platform API**: 「平台」的 API. 这里的「平台」是个泛指, 具体是什么取决于上下文, 可能是:

- 你自己公司的 SaaS 平台 (比如你做了个 AI 外呼平台)
- 一个第三方平台 (比如 Slack, Stripe, 抖音开放平台)
- 一个聚合层 API

`CRM ↔ Platform API` 这个箭头是**双向**的, 意味着两边都能调用对方、读写数据.

---

## 2. OAuth 2.0 解决的核心问题

设想没有 OAuth 时的灾难场景:

```
用户:    "请把通话录音和总结自动写回我的 Salesforce"
平台:    "好的, 请把你的 Salesforce 用户名密码给我"
用户:    😨
```

**问题**:

- 用户得交出密码 (信任风险)
- 平台得存用户密码 (合规炸弹)
- 用户改密码后平台就废了
- 没办法限制平台只能访问某些数据
- 用户没法随时撤销授权

**OAuth 2.0 的解法**:

```
用户 → 跳转到 Salesforce 登录页 (在 Salesforce 域名, 平台看不到密码)
     → Salesforce 弹窗: "AI 外呼平台 想要: 读取联系人、写入通话记录. 同意?"
     → 用户点"同意"
     → Salesforce 给平台发一个 access_token (一串短期凭证)
     → 平台用 access_token 调 Salesforce API

任何时候用户可以在 Salesforce 后台撤销这个授权 → token 失效
```

---

## 3. 典型流程图 (Authorization Code Flow, 最常用)

```
┌────────┐      ┌──────────────┐      ┌────────────┐
│  用户   │      │ Platform/CRM │      │   CRM      │
│ Browser │      │  (你的应用)  │      │ (Salesforce)│
└───┬────┘      └──────┬───────┘      └─────┬──────┘
    │  1. 点 "连接 Salesforce"               │
    │ ──────────────────────► │              │
    │                          │              │
    │  2. 重定向到 Salesforce 授权页          │
    │ ◄────────────────────────              │
    │                                        │
    │  3. 登录 + 同意权限                    │
    │ ──────────────────────────────────────►│
    │                                        │
    │  4. 重定向回平台 + 携带 auth_code      │
    │ ◄──────────────────────────────────────│
    │                                        │
    │  5. 平台把 auth_code 发给 Salesforce    │
    │                          │ ───────────►│
    │                          │              │
    │  6. Salesforce 返回 access_token + refresh_token
    │                          │ ◄───────────│
    │                          │              │
    │  7. 平台存储 token, 以后用它调 Salesforce API
    │                          │ ───────────►│
    │                          │              │
    │  8. token 过期后用 refresh_token 换新的 │
    │                          │ ◄──────────►│
```

**几个关键 token**:

| Token | 寿命 | 用途 |
|---|---|---|
| **access_token** | 短 (1h–24h) | 每次 API 调用带上 |
| **refresh_token** | 长 (30天–永久) | access_token 过期时换新的, 不需要用户重新登录 |
| **auth_code** | 极短 (10 分钟) | 一次性, 换 access_token 用 |

**Scope** (权限范围): 授权时声明「我要读 contacts、写 calls」, 用户能看到这个清单再决定同不同意.

---

## 4. 具体业务场景 (CRM ↔ Platform API 双向)

### 场景 A: AI 外呼 / 客服平台 ↔ Salesforce (最贴你工作背景)

你做的债务催收 / 客服语音 agent, 要和客户的 Salesforce 双向打通:

**平台 → CRM (写入)**:
- 通话结束后, 把通话录音 URL、ASR 转写文本、AI 生成的对话摘要写回 Salesforce 的「Call Activity」记录
- 把客户在通话中表达的「下次回访意向时间」更新到 CRM 的 follow-up 字段
- 把客户标签 (如「拒绝沟通」「承诺还款」) 回写到 Lead/Contact 上

**CRM → 平台 (拉取)**:
- 启动外呼任务时, 从 Salesforce 拉取今日待催收名单 (contact + phone + 欠款金额 + 历史记录)
- 拉取客户偏好语言、过往沟通记录给 LLM 当 context
- 监听 CRM 的 webhook: 当销售在 CRM 里把一个 lead 标记为「热」, 自动触发 AI 外呼

**OAuth 在这里的角色**: 每个企业客户 (比如 TikTok PayLater 团队) 在他们自己的 Salesforce 里授权一次, 你的平台拿到他们租户的 token, 之后所有 API 调用都用这个 token.

### 场景 B: HubSpot ↔ 邮件营销平台

- 营销平台从 HubSpot 拉客户名单做邮件 campaign
- 邮件打开 / 点击事件回写 HubSpot 作为 engagement signal

### 场景 C: Stripe ↔ 你的 SaaS

- Stripe 是支付 platform API
- 你的 SaaS 让用户「连接 Stripe」做收款
- 通过 OAuth 用户授权后, 你能代表他们创建订阅、查询交易

### 场景 D: Slack ↔ Jira (双向集成)

- Jira 里 ticket 状态变化 → 推送到 Slack 频道
- Slack 里 `/jira create` 命令 → 在 Jira 里建 ticket

---

## 5. 工程上要做什么 (实现 checklist)

**作为平台方** (被集成方角度 — 你的 AI 外呼平台想被装进客户的 Salesforce):

1. 在 Salesforce Connected App 注册, 拿到 `client_id` 和 `client_secret`
2. 实现一个「连接 Salesforce」按钮, 跳转到 Salesforce 授权 URL
3. 实现 callback endpoint 接收 `auth_code`
4. 后端用 `auth_code + client_secret` 换 `access_token`
5. **加密存储 token** (数据库或专门的 secrets manager)
6. 每次调 Salesforce API 时带上 token
7. 处理 token 过期: 用 `refresh_token` 自动续期
8. 提供「断开连接」按钮, 调用 revoke endpoint

**作为调用方** (你想去消费别家 platform API): 逻辑对称, 你是 OAuth client, 对方是 OAuth server.

---

## 6. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **token 存储**: 必须加密 | token 泄漏 = 数据泄漏. 用 KMS / HashiCorp Vault / AWS Secrets Manager |
| 2 | **scope 最小化** | 只申请你真正需要的权限. 不要图省事申请 `*`, 会让客户审批阶段过不了 |
| 3 | **多租户隔离** | 每个企业客户的 token 必须严格按 `tenant_id` 隔离. 跨租户调用是经典安全事故 |
| 4 | **rate limit 处理** | Salesforce 这类 API 有严格限流 (per app per org), 需要做 backoff + queue |
| 5 | **PKCE** | 移动端 / SPA 不能存 `client_secret`, 要用 OAuth 2.0 的 PKCE 扩展 |
| 6 | **refresh_token 旋转** | 高安全场景下每次 refresh 都换新 refresh_token, 旧的失效 |
| 7 | **webhook 验签** | CRM 推 webhook 给你时要校验签名, 否则任何人都能伪造事件 |

---

# Part 2 · 5 个深度工程问题 (面试 / 架构评审硬核细节)

## ⚙️ Problem 1: 4 个 Grant Types

**Grant type** = 「你用什么方式拿到 token」. OAuth 2.0 规范里其实有 5–6 种, 但生产里 90% 场景就是这 4 个.

### 1.1 authorization_code (授权码模式) — 最常用、最安全

**场景**: 用户在浏览器里授权第三方应用访问自己的数据.

**流程**:

```
用户 → 第三方应用「登录 Salesforce」按钮
    → 跳到 Salesforce → 登录 + 同意
    → Salesforce 重定向回应用, URL 里带 ?code=xxx
    → 应用后端用 code + client_secret 调 token endpoint
    → 拿到 access_token + refresh_token
```

**关键点**:

- **两步换 token**: 先拿 code (短期、一次性), 再用 code 换 token
- **为什么两步**? 因为 code 走的是浏览器 URL (可能被日志记录、被引荐者头泄漏), 而 token 走的是后端到后端的 HTTPS, 更安全
- `client_secret` 永远只在后端用, 不能放前端

**变种 PKCE** (Proof Key for Code Exchange): 移动 App / SPA 没法存 `client_secret`, 用 PKCE 替代 — 客户端生成一个随机 `code_verifier`, 先发 `code_challenge`, 换 token 时再发 `code_verifier`, 服务端验证匹配. 现在的最佳实践是**所有 authorization_code 流程都加 PKCE**, 包括有后端的 Web 应用.

**用在哪**: 你前面问的 CRM ↔ Platform API 场景, 99% 用这个.

### 1.2 client_credentials (客户端凭证模式) — 机器对机器

**场景**: 没有用户, 是两个服务之间互调.

**流程**:

```
你的服务 → 直接拿 client_id + client_secret 调 token endpoint
       → 拿到 access_token (注意: 没有 refresh_token)
       → 用 token 调 API
```

**关键点**:

- 没有用户参与, 没有授权页面
- 没有 refresh_token — 因为反正服务自己持有 secret, 过期了直接重新申请就行
- token 代表的是「这个应用本身」的身份, 不是某个用户

**用在哪**:

- 你的后台定时任务调第三方 API (比如每天凌晨同步汇率)
- 微服务之间的 service-to-service 调用 (虽然内部场景一般用 mTLS 或 JWT 更轻)
- B2B 集成里没有最终用户的纯系统对接

### 1.3 refresh_token (刷新令牌模式) — 续命

**场景**: `access_token` 快过期了, 不想让用户重新登录一次, 用 `refresh_token` 换一个新的 `access_token`.

**流程**:

```
应用 → 检测到 access_token 过期 (或预过期)
    → 用 refresh_token 调 token endpoint
    → 拿到新的 access_token (可能也拿到新的 refresh_token)
```

**关键点**:

- `refresh_token` 寿命长 (几天 – 几个月), `access_token` 寿命短 (几小时)
- 这个设计的安全意义: 即使 `access_token` 泄漏, 攻击者最多用几小时; `refresh_token` 只在后端流动, 泄漏概率低
- **refresh token rotation** (旋转): 每次用 `refresh_token`, 服务端会发一个新的 `refresh_token`, 旧的立刻失效. 这样如果攻击者偷了 `refresh_token` 用了一次, 真用户再用就会失败 → 服务端检测到「同一个 refresh_token 被用了两次」立刻撤销整条链, 强迫用户重新授权.

### 1.4 device_code (设备码模式) — 没浏览器的设备

**场景**: 你要在一个没有键盘 / 浏览器的设备上授权, 比如智能电视、CLI 工具、IoT 设备.

**流程**:

```
设备 → 调 device endpoint, 拿到 device_code + user_code + verification_url
设备 → 显示「请在手机上访问 https://..., 输入码: ABCD-1234」
用户 → 在手机 / 电脑上访问该 URL, 登录 + 输入码 + 同意
设备 → 后台轮询 token endpoint
     → 用户同意后, 拿到 access_token
```

**用在哪**:

- AWS CLI / GitHub CLI 的 `gh auth login`
- Apple TV 上登 Netflix
- Claude Code / Anthropic CLI 类工具

### 已废弃的旧 grant type

- **implicit** (隐式模式): token 直接走 URL 返回, 不安全, 已被 PKCE 取代
- **password** (密码模式): 用户把账号密码给应用, 应用换 token — OAuth 反模式, 禁止使用

---

## ⚙️ Problem 2: Token Storage + Rotation

**这块是生产事故重灾区.**

### 2.1 存哪里

按场景:

| 场景 | 推荐存储 | 不能用 |
|---|---|---|
| 浏览器 Web 应用 | `httpOnly + Secure + SameSite Cookie` | localStorage (XSS 一锅端) |
| 移动 App | iOS Keychain / Android Keystore | SharedPreferences 明文 |
| 后端服务 (B2B 集成) | **加密数据库 + KMS / Vault / Secrets Manager** | 明文数据库、配置文件 |
| 短期临时 | Redis (加密 + TTL) | 普通日志、监控 metric label |

**核心原则**:

- **必须加密** (at-rest encryption), 用 KMS 管密钥
- 永远**不要进日志**, error message、APM 追踪、Sentry 报错都要 redact
- **不要进 URL**, 只能进 Header (`Authorization: Bearer xxx`) 或 POST body

### 2.2 Rotation (轮换 / 旋转)

两个层面:

**(a) Refresh Token Rotation** (前面讲过的):

- 旧设计: 用 refresh_token 换 access_token, refresh_token 不变
- 新设计: 每次换都返回新 refresh_token, 旧的立刻作废

实现要点:

```python
def refresh(old_refresh_token):
    record = db.get_token(old_refresh_token)
    if not record or record.used:
        # 被用过一次又来用? 说明被偷了
        revoke_all_tokens_for_user(record.user_id)  # 一刀切
        raise SecurityError("Token reuse detected")

    new_access = generate_access_token()
    new_refresh = generate_refresh_token()

    with db.transaction():
        record.used = True
        db.save_token(new_refresh, user_id=record.user_id)

    return new_access, new_refresh
```

**(b) 凭证轮换** (你应用自己的 `client_secret`):

- 每 90 天换一次 `client_secret`
- 支持「双 secret 共存」机制: 新旧 secret 都能用一段时间, 平滑过渡
- 自动化: cron job + Vault 自动生成新 secret + 通知依赖方

---

## ⚙️ Problem 3: Middleware Placement (SDK / Proxy / Dedicated Service)

这是个架构选型问题: OAuth 的 token 管理逻辑 (拿 token、续 token、塞到请求 Header) 这堆事, 放在系统的哪一层?

### 3.1 SDK / Library 模式 (最常见)

每个微服务自己引入一个 OAuth client 库 (比如 Java 的 Spring Security OAuth、Python 的 authlib、Go 的 oauth2).

```
[Service A] ←有 OAuth SDK→ [External API]
[Service B] ←有 OAuth SDK→ [External API]
[Service C] ←有 OAuth SDK→ [External API]
```

**优点**: 简单、零网络跳数

**缺点**:

- 每个服务重复实现 token 刷新、缓存
- token 散落在多个进程内存里
- 升级 SDK 要同步推所有服务
- 多语言栈下要维护多套 SDK

### 3.2 Proxy / Sidecar 模式

放一个 sidecar (比如 Envoy、Istio、Kong) 在每个服务旁边, 所有出站请求经过它, sidecar 负责注入 token.

```
[Service A] → [Envoy Sidecar] ←OAuth→ [External API]
                   ↑
              从中央配置拉 token
```

**优点**:

- 服务代码完全不感知 OAuth
- 一处升级, 全员受益
- 统一观测、统一限流

**缺点**:

- 运维复杂度上升 (Service Mesh)
- 网络跳数增加
- 调试 token 问题要看 sidecar 日志

### 3.3 Dedicated Auth Service (专用认证服务)

抽一个独立服务, 专门管所有外部集成的 token. 其他服务调它要 token.

```
[Service A] → [Token Service] ←OAuth→ [External API]
[Service B] →      ↑
[Service C] →  缓存 + 刷新 + 撤销
```

**优点**:

- 单一职责, 集中管理
- token 不暴露给业务服务
- 容易做审计、轮换、撤销
- 多租户隔离最干净

**缺点**:

- 单点故障, 要做 HA
- 多一次内部网络调用
- 跨网络的延迟

### 怎么选

| 团队规模 | 选什么 |
|---|---|
| 小 (< 5 服务) | SDK 模式 |
| 中 (已经在跑 Service Mesh) | Sidecar 模式 |
| 大 (多租户 SaaS, 强合规) | Dedicated Service |

**字节 / 阿里这种规模**一般是 **Dedicated Service + SDK 混合**: 核心租户态在专用服务, 业务侧用统一 SDK 调它.

---

## ⚙️ Problem 4: Failure Modes (Token Expire / Refresh Race / Revocation)

这是「面试题里你能不能展现实战经验」的地方, 没踩过坑的人答不出.

### 4.1 Token Expire Mid-Call (调用中途 token 过期)

**问题**: 你 `14:59:59` 检查 token 还有 1 秒, `14:59:59.5` 发出请求, 服务端 `15:00:00` 收到, 判定过期, 返回 401.

**解法**:

```python
# 方案 1: 预过期 (preemptive refresh)
# 不等到真过期, 提前 5 分钟就刷新
def is_token_valid(token):
    return token.expires_at - now() > 5 * 60  # 留 5 分钟 buffer

# 方案 2: 自动重试
def call_api(request):
    try:
        return http.send(request, token=current_token())
    except Unauthorized as e:
        new_token = refresh_token()
        return http.send(request, token=new_token)  # 重试一次
```

**生产里两个都要做**: 预过期减少 401 概率, 自动重试兜底.

### 4.2 Refresh Race (刷新竞态)

**问题**: 服务有 10 个并发请求, token 同时过期了, 10 个请求各自看到 token 过期, 各自去 refresh — 后果:

- 调 10 次 token endpoint, 被对方限流
- 如果开了 refresh token rotation: 第 1 个 refresh 成功, 旧 refresh_token 作废, 后 9 个全部失败 → 触发安全告警 → 整条 token 链被撤销 ← **灾难**

**解法**: 分布式锁 + 单飞模式 (singleflight)

```python
def get_valid_token(tenant_id):
    token = cache.get(tenant_id)
    if is_valid(token):
        return token

    # 分布式锁: 只有一个请求能进入 refresh
    with distributed_lock(f"refresh:{tenant_id}", timeout=10):
        # 再查一次缓存, 可能其他实例刚刷完
        token = cache.get(tenant_id)
        if is_valid(token):
            return token

        # 真的要刷
        new_token = oauth.refresh(token.refresh_token)
        cache.set(tenant_id, new_token, ttl=new_token.expires_in - 300)
        return new_token
```

**实现工具**:

- Go 标准库里有 `singleflight.Group` 专门干这个
- Java 用 Caffeine 的 `LoadingCache`
- Python 用 `asyncio.Lock` + Redis

### 4.3 Revocation (撤销)

**问题**: 用户在 Salesforce 后台点了「撤销 AI 外呼平台的访问」, 但你这边 token cache 里还有有效 token, 照样发请求, 全部 401.

**两类撤销**:

- **被动发现**: API 返回 401 / invalid_token, 你才知道
- **主动通知**: OAuth 服务端发 webhook / token_revocation_event

**应对**:

```python
def handle_401(tenant_id):
    # 1. 立即从 cache 删除 token
    cache.delete(tenant_id)
    # 2. 标记 tenant 为「需要重新授权」
    db.update_tenant(tenant_id, status="reauth_required")
    # 3. 通知用户: 「请重新连接 Salesforce」
    notify_user(tenant_id, "Connection lost, please re-authorize")
    # 4. 暂停该 tenant 的所有定时任务
    scheduler.pause_jobs(tenant_id)
```

**还有一类**: `refresh_token` 也失效了 (用户改了 Salesforce 密码、超过 90 天没用、管理员强制 revoke). 这时连 refresh 都救不回来, **必须重新走完整 OAuth 流程**.

### 4.4 其他常见失败

- **Clock skew**: 你服务器时间和对方差 30 秒, JWT 校验失败. 用 NTP, 并在校验时留 60s 容差
- **Rate limit on token endpoint**: token endpoint 本身也有限流, 刷太频繁会被封
- **Token endpoint 挂了**: 你的服务依赖 Salesforce token endpoint, 对方故障你也跟着挂. **缓存有效 token, 故障期间继续用**

---

## ⚙️ Problem 5: Multi-Tenant Secrets Management

**场景**: 你做的是 SaaS 平台, 有 1000 个企业客户, 每个客户都接了他们自己的 Salesforce. 意味着你手里有 1000 套 `(refresh_token, access_token, client_secret)`.

### 5.1 为什么这是个难题

```
租户 A 的 Salesforce token  ┐
租户 B 的 Salesforce token  │
租户 C 的 Salesforce token  ├─ 你的平台数据库
...                         │
租户 ZZZ 的 Salesforce token┘

如果数据库被脱库 → 1000 家公司的 CRM 数据全暴露 → 你公司倒闭
```

### 5.2 关键设计原则

**(a) Per-tenant encryption (每租户独立加密)**

每个 tenant 用不同的加密 key:

```
encrypted_token = AES_encrypt(plaintext_token, tenant_specific_key)
tenant_specific_key = KMS_derive(master_key, tenant_id)
```

哪怕一个 tenant 的 key 泄漏, 影响范围只是那一家.

**(b) 严格隔离 (Tenant Isolation)**

数据库层强制 `WHERE tenant_id = ?`, 绝不允许跨租户查询. 生产事故里**跨租户数据泄漏是 SaaS 公司最致命的事故**, 没有之一.

实现方式:

- Row Level Security (PostgreSQL RLS)
- 每个租户独立 schema 或独立 DB
- ORM 层强制注入 `tenant_id` 过滤

**(c) Secrets Manager 集中存储**

不要把 token 写到自己服务的数据库里, 用专门的 secrets manager:

| 工具 | 适用 |
|---|---|
| HashiCorp Vault | 自建首选, 功能最全 |
| AWS Secrets Manager / Parameter Store | AWS 上 |
| GCP Secret Manager | GCP 上 |
| Azure Key Vault | Azure 上 |

它们提供: 自动轮换、审计日志、细粒度 IAM、HSM 加持

**(d) Audit Log (审计日志)**

每次 token 被读 / 写 / 刷新都记日志 (只记元数据, 不记 token 本身):

```json
{
  "ts": "2026-05-21T14:30:00Z",
  "actor": "service:tts-handler",
  "action": "token.read",
  "tenant_id": "tenant_abc",
  "purpose": "salesforce_api_call",
  "outcome": "success"
}
```

合规审计 (SOC2、ISO27001) 必备.

**(e) Least Privilege (最小权限)**

不是所有服务都该能读所有 tenant 的 token. 设计 IAM:

- TTS handler 只能读「它正在处理的 tenant」的 token
- Admin 服务能读全部, 但要 break-glass approval

**(f) Rotation 自动化**

cron job 定期检查:

- `access_token` 离过期 < 10min → 提前刷
- `refresh_token` 离过期 < 7day → 提醒用户重新授权
- `client_secret` 用了 > 90day → 触发轮换流程

### 5.3 典型架构

```
┌─────────────────────────────────────────────────┐
│              Tenant Onboarding                  │
│  用户在你平台点 "连接 Salesforce" → OAuth flow    │
└─────────────────────┬───────────────────────────┘
                      │ (refresh_token, access_token)
                      ▼
            ┌─────────────────────┐
            │   Token Service     │
            │  - 加密              │
            │  - 多租户隔离        │
            │  - 自动刷新          │
            │  - 审计日志          │
            └─────────┬───────────┘
                      │
              ┌───────┴───────┐
              ▼               ▼
        ┌─────────┐     ┌──────────┐
        │  Vault  │     │  Audit   │
        │ (KMS)   │     │  Log DB  │
        └─────────┘     └──────────┘
              ▲
              │ token request
        ┌─────┴────────────────┐
        │   TTS Handler        │  ← 业务服务
        │   Outbound Caller    │    需要调 Salesforce 时
        │   Webhook Receiver   │    向 Token Service 要 token
        └──────────────────────┘
```

---

# Part 3 · 把 5 个问题串起来看

这 5 个问题其实是**同一件事的不同维度**:

1. **Grant types** 决定「怎么拿到 token」
2. **Storage + Rotation** 决定「token 怎么安全存活」
3. **Middleware placement** 决定「token 在系统里怎么流动」
4. **Failure modes** 决定「token 出问题时系统怎么活」
5. **Multi-tenant secrets** 决定「token 在多客户场景下怎么隔离」

面试或架构评审里, 能从这 5 个角度系统讲一遍, 基本就是**资深后端 / 平台工程的水准**. 如果只会答「OAuth 就是 authorization_code 流程那张图」, 那是初级.

---

## 必问 clarifying questions

**1. Which direction**

> "Are **we** acting on behalf of client's CRM users (we're OAuth client) or is CRM calling our API on behalf of users (we're OAuth server)? Often both, but design is different."

**2. Which OAuth version**

> "OAuth 1.0a is HMAC-signed and deprecated. Most modern CRMs (Salesforce, HubSpot, Dynamics) use 2.0. Is the client on an older version requiring 1.0?"

**3. Grant type**

> "Are we acting **as a user** (authorization_code + refresh_token) or **as the application** (client_credentials)?"

**4. Token lifetime**

> "What's the client's access token TTL? (Salesforce default is 2h, HubSpot 30min). Refresh token TTL? Revocation policy?"

**5. Volume / SLA**

> "QPS to CRM and from CRM? Rate limits on their side? Bursty or sustained?"

---

## 5 步框架 (sample 45-min answer 节奏)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify direction + grant + version + volume |
| 5-20 min | Token exchange flow (画 sequence diagram) + grant type 选择 |
| 20-30 min | Middleware placement (Token Service + SDK 混合) |
| 30-40 min | Failure modes (refresh race / expire mid-call / revocation) |
| 40-55 min | Multi-tenant secrets (per-tenant DEK + Vault + audit) |
| 55-60 min | Production hardening (monitor 401/429, dashboard, test harness) |

---

## 简历专属 reframe

你的 **voice agent 7 markets** + **BNPL chatbot** 都有 enterprise auth:

| OAuth 题 | 你的经验 |
|---|---|
| Token exchange + refresh | 你的 voice agent 集成 7 个市场的 repayment 系统 — 各自不同 auth |
| Multi-tenant secrets in HSM | BNPL chatbot 跨 ByteDance internal 多 service |
| Distributed lock on refresh | Voice agent 你做过 thundering herd 类似问题 |
| ConvFinQA: secure API key handling | 你做过 `.env` + os.environ 模式, not hardcoded |
| Token Service central pattern | 你的 internal Agent Platform 应该有共享 service 设计 |

**主动 quote**:

> "I've implemented this pattern across 7 markets for the voice agent — each market's repayment system had different auth (some OAuth 2.0, some HMAC, some IP-allowlisted JWT). We centralized into a Token Service with per-tenant DEK encryption + distributed refresh lock. The trickiest failure mode I hit was **clock skew between our service and the customer's auth server** — a 30s buffer fixed 95% of premature-expiry incidents."

---

## 5 follow-ups

**Q1**: "Refresh race — 10 concurrent calls all 401. What happens?"

**A**: 没有 coordination, 10 个并行 refresh 请求打到 Salesforce → 10 个不同的 refresh_token → 9 个立刻被作废 (Salesforce 旋转 refresh on use). 解:
- **Distributed lock per tenant on refresh** (Redis `SETNX` with TTL)
- Holder refreshes, writes new tokens, releases lock
- Others wait up to 5s, then re-read tokens

**Q2**: "Token Service is single point of failure. 100k QPS impact if it goes down."

**A**:
- **Stateless multi-instance** behind LB
- **Local cache in service** (30s TTL) — if Token Service is unreachable, use cached token until expiry
- **Read replica** for token DB (writes are rare)
- **Async refresh path** — refresh tokens 5 min before expire (warm), don't wait until 401

**Q3**: "Customer says we can't store their refresh_token. What now?"

**A**: 3 patterns:
1. **Token broker on customer side** — customer hosts a service that holds tokens, we call that service. Customer-owns-keys model.
2. **HSM with customer-controlled KEK** — we store but encrypted by their KMS, customer can revoke decryption
3. **OAuth on-behalf-of (OBO) flow** — Microsoft / Google support; we get short-lived tokens per request, no refresh storage

**Q4**: "PCI / HIPAA compliance — tokens are sensitive data?"

**A**:
- Tokens themselves aren't typically classified PII, but **tokens can be exchanged for PII**, so treat as sensitive
- **Never log tokens** (use hash for correlation)
- **TLS 1.3** in transit, AES-256 at rest
- **Access audit** every read with actor + reason
- **Tokenized DB column** with field-level encryption

**Q5**: "Salesforce rate-limits us at 100 req/min/org. How do we serve a customer with 1M API calls/day?"

**A**:
- **Batch operations** — use Bulk API (1 request = 10k records)
- **CDC subscription** instead of polling — receive change events, no polling needed
- **Composite REST** — pack 25 operations per request
- **Queue + backpressure** — our system caches, batches, retries
- If still hitting limits, work with Salesforce account team for higher quota tier

---

## ❌ 易错点 (top 7)

1. **OAuth 2.0 当 single thing** — 4 个 grant types 区分不清
2. **每 service 内嵌 SDK** — auth 逻辑分散, rotate 困难
3. **没 refresh race 处理** — production thundering herd
4. **明文存 token** — security violation
5. **不处理 clock skew** — 30s buffer 是经典 fix
6. **没 multi-tenant key isolation**
7. **没 monitor 401/429 rate** — 上游问题 silent

---

## ✅ 加分项 (top 10)

1. **Central Token Service + local cache** pattern
2. **Distributed lock on refresh** prevent stampede
3. **2 active `client_secrets`** for rotation cutover
4. **PKCE on all authorization_code flows** (best practice 2026)
5. **OBO flow** for compliance-strict customers
6. **30s clock skew buffer**
7. **Composite + Bulk API** for rate-limit avoidance
8. **HSM / Vault** for client_secret
9. **Tokenized DB column + per-tenant DEK**
10. **Refresh token reuse detection** → revoke whole chain

---

## 一句话总结

> **OAuth 2.0 Integration (CRM ↔ Platform API) = 「用 OAuth 2.0 把你的应用和客户的 CRM 系统安全地打通, 让两边的数据 / 事件能双向流动, 而不需要客户交出账号密码」**.
>
> 这个能力是 **B2B SaaS 的生死线** — 客户的数据都在 CRM 里, 你的产品如果不能接入 CRM 就只是个孤岛工具, 接了就是他们工作流的一部分.

---

## Cheat Sheet (印 1 页随身)

```
OAuth grant types:
  authorization_code  - user delegation (most CRMs) ⭐ 99% 场景
  client_credentials  - service-to-service (后台任务)
  refresh_token       - 续命 (rotate per use!)
  device_code         - IoT / TV / CLI
  [废弃] implicit / password — 不要碰

PKCE: 所有 authorization_code 都该加 (不只 mobile)

Token lifetimes:
  access_token: 1-24h (短)
  refresh_token: 30d-永久 (rotate)
  auth_code: 10min (一次性)

Architecture:
  Service → Token Service (central) → CRM
            ↓
       per-tenant DEK + Vault
       audit log every access

Storage:
  Browser: httpOnly + Secure + SameSite Cookie
  Mobile: Keychain / Keystore
  Backend: KMS + encrypted DB
  红线: 不进 URL, 不进 log, 不进 localStorage

Rotation:
  refresh_token 旋转 (rotate on use)
  client_secret 90d (双 secret 共存过渡)
  Refresh reuse detect → revoke chain

Middleware (选一):
  SDK lib: 小团队
  Sidecar proxy: 中等, Service Mesh 已在跑
  Dedicated Token Service: 大型 / 多租户 / 强合规 ⭐

Failure modes:
  Token expire mid-call → preempt 5min + auto retry once
  Refresh race → distributed lock per tenant (SETNX)
  Revocation → cache invalidate + reauth_required flag
  Clock skew → 60s buffer
  Token endpoint down → cache 兜底

Multi-tenant secrets (6 原则):
  1. Per-tenant DEK (KMS derive)
  2. 严格隔离 (RLS / 强制 WHERE tenant_id)
  3. Vault / Secrets Manager (不放 app DB)
  4. Audit log (元数据, 不记 token)
  5. Least privilege IAM
  6. Rotation 自动化

Rate-limit mitigation (Salesforce style):
  Bulk API (10k records/req)
  Composite REST (25 ops/req)
  CDC subscription, not polling
  Backpressure queue
  Quota tier 升级谈

Retry rules:
  401 → refresh + 1 retry
  429 → respect Retry-After header
  5xx → exponential backoff up to 3
  Other 4xx → 别 retry
```

---

## Extended Cheat Sheet (能背诵·含全量知识)

> 10-15 min 通读, 覆盖本页所有 framework / decision / production gotcha.

### 核心心智模型 (1 sentence)

OAuth 2.0 CRM ↔ Platform integration = "4 grant types (authorization_code with PKCE / client_credentials / refresh_token rotation / device_code) × 4 storage 层 (httpOnly cookie / Keychain / KMS+vault / Redis encrypted) × 3 middleware pattern (SDK / sidecar / dedicated Token Service) + per-tenant DEK + distributed lock on refresh + 30s clock skew buffer + cache 兜底 + composite + Bulk rate-limit mitigation", token lifetime: access 1-24h short / refresh 30d-perm rotate / auth_code 10min one-shot.

### 术语全表

| 术语 | 一句话定义 | 何时用 |
|---|---|---|
| OAuth 2.0 | 授权协议 (非认证), 让 A 应用代表 user 访问 B 数据 | SaaS 互联标配 |
| Grant type | 怎么拿到 token (4 种生产场景) | 流程选型 |
| Access token | 短期 (1-24h), 每次 API 调用 Header | 工作 token |
| Refresh token | 长期 (30d-perm), 换新 access token | 续命 |
| Auth code | 一次性 10min, 换 access token | authorization_code 流程 |
| PKCE | Proof Key for Code Exchange, 移动+SPA 防 code 截获 | 2026 best practice for ALL auth_code |
| Scope | 权限范围声明, 用户授权时看到 | 最小权限 |
| Token rotation | refresh 每用换新, 旧的失效 | 安全升级 |
| Reuse detection | 同 refresh_token 用 2 次 → revoke 全链 | 防偷 |
| Distributed lock | Redis SETNX per-tenant 防 thundering herd refresh | 高并发 |
| Singleflight | 多并发 refresh 收敛为 1 个 | Go std lib / Caffeine |
| Clock skew buffer | NTP + 60s 容差 | JWT exp check |
| OBO (On-Behalf-Of) | 短期 narrow token, 不存 refresh | 高合规 customer |
| Composite REST | 25 ops/请求 | Salesforce rate limit |
| Bulk API | 10k records/请求 | Salesforce 大量数据 |
| CDC subscription | Change Data Capture push 替 polling | 不踩限流 |
| HSM | Hardware Security Module 加 client_secret | enterprise compliance |

### 5 个核心 framework / pattern

**Framework 1**: 4 grant types selection
- When: 流程开始
- Algorithm: authorization_code (user delegation, 99% CRM) + PKCE / client_credentials (service-to-service, no user) / refresh_token (续命, rotate on use) / device_code (IoT/TV/CLI)
- Trade-off: implicit / password 已废弃 — 绝不要用
- Tools: authlib (Python), Spring Security OAuth (Java), golang.org/x/oauth2

**Framework 2**: Token storage 4 场景
- When: 持久化 token
- Algorithm: Browser → httpOnly+Secure+SameSite Cookie / Mobile → iOS Keychain or Android Keystore / Backend B2B → KMS-encrypted DB or Vault / Short-term temp → Redis encrypted + TTL
- Trade-off: 红线 — 永远不进 URL, log, localStorage
- Tools: HashiCorp Vault (自建首选), AWS Secrets Manager, GCP Secret Manager, Azure Key Vault

**Framework 3**: Middleware placement 3 options
- When: token 管理放哪
- Algorithm: SDK lib (小团队 < 5 services) / Sidecar proxy Envoy (Service Mesh 已跑) / Dedicated Token Service (multi-tenant 强合规, ⭐ enterprise default)
- Trade-off: SDK 简单但散乱, Sidecar 运维 vs 透明, Dedicated 单点 vs 集中
- Tools: 字节 / 阿里规模 — Dedicated Service + SDK 混合, Envoy/Istio for sidecar pattern

**Framework 4**: Failure mode 5 套路
- When: production deployment
- Algorithm: 1) Token expire mid-call → preempt 5 min + auto retry once / 2) Refresh race → distributed lock per tenant (Redis SETNX) / 3) Revocation → cache invalidate + reauth_required flag / 4) Clock skew → 60s buffer + NTP / 5) Token endpoint down → cache 兜底 continue
- Trade-off: lock 增 latency, 但 thundering herd 灾难大
- Tools: Go singleflight.Group / Caffeine LoadingCache / asyncio.Lock + Redis

**Framework 5**: Multi-tenant secrets 6 原则
- When: 1000 customer 各自接 Salesforce
- Algorithm: 1) Per-tenant DEK (KMS derive) / 2) 严格隔离 (RLS / 强制 WHERE tenant_id) / 3) Vault / Secrets Manager 不放 app DB / 4) Audit log 元数据 / 5) Least privilege IAM / 6) Rotation 自动化
- Trade-off: per-tenant DEK 贵, 但跨 tenant leak 致命
- Tools: HashiCorp Vault context-bound key derivation, Postgres RLS, Audit + SOC2 dashboard

### 关键决策树 (ASCII)

```
Choose grant type:
有 user 参与? → YES → authorization_code + PKCE (99% case)
              → NO  → client_credentials (service-to-service)
IoT/TV/CLI? → device_code
[废弃] implicit / password — 不要碰

Storage decision:
Browser app  → httpOnly + Secure + SameSite Cookie
Mobile app   → Keychain / Keystore
Backend B2B  → KMS-encrypted DB or Vault
Short temp   → Redis encrypted + TTL

Middleware:
< 5 services            → SDK lib
Service Mesh 已跑       → Sidecar proxy
Multi-tenant 强合规     → Dedicated Token Service ⭐

Refresh race?
Yes  → distributed lock per tenant (Redis SETNX)
       singleflight on holder, others wait/re-read

Customer 不许 store refresh_token?
Option 1: Token broker on customer side
Option 2: HSM with customer-controlled KEK (BYOK)
Option 3: OAuth OBO (short-lived per-request)
```

### Part 2 五个深度问题速查

**Problem 1: 4 Grant Types**
- 核心解法: authorization_code with PKCE (99% case) / client_credentials (no user) / refresh_token (rotate) / device_code (IoT/CLI); implicit + password 已废弃
- Top 3 gotchas: client_secret 永远后端 / PKCE 所有 auth_code 都加 (不仅 mobile) / refresh rotation on use (旧立刻失效)
- Tools: authlib, Spring Security OAuth, oauth2-proxy

**Problem 2: Token Storage + Rotation**
- 核心解法: storage 按场景 (Cookie/Keychain/Vault/Redis), refresh token rotation (旧立刻作废), client_secret rotation 90d 双 secret 共存
- Top 3 gotchas: 不进 URL / log / localStorage / refresh reuse detection 偷探测 → revoke 全链 / KMS + Vault for client_secret 不放 DB
- Tools: Vault auto-rotation, KMS DEK derive, HSM for high-stakes

**Problem 3: Middleware placement**
- 核心解法: SDK (小团队) / Sidecar Envoy (Service Mesh) / Dedicated Token Service (multi-tenant 强合规, ⭐ enterprise)
- Top 3 gotchas: Token Service 是 SPOF, 必 HA + local cache 兜底 / Read replica for token DB / async refresh 5min 之前 warm
- Tools: Envoy/Istio sidecar, gRPC Token Service, Redis local cache 30s TTL

**Problem 4: Failure modes (5 套路)**
- 核心解法: preempt 5min + auto retry once (mid-call), distributed lock per-tenant (refresh race), cache invalidate + reauth flag (revocation), 60s NTP buffer (clock skew), cache 兜底 (endpoint down)
- Top 3 gotchas: 没 lock → thundering herd refresh / 没 preempt → 边界 401 / 没 cache fallback → 上游故障跟着挂
- Tools: Redis SETNX, Go singleflight, NTP chronyd

**Problem 5: Multi-tenant secrets**
- 核心解法: per-tenant DEK / RLS or 强制 WHERE / Vault central / audit log 元数据 / least priv IAM / rotation cron 自动
- Top 3 gotchas: cross-tenant SQL injection / token 进 log / no audit on read (合规 fail)
- Tools: HashiCorp Vault per-tenant transit engine, Postgres RLS, audit immutable log

### Production gotchas (top 15)

1. OAuth 2.0 当 single thing (4 grant 不分)
2. 每 service 内嵌 SDK (auth 散乱, rotate 难)
3. 没 refresh race 处理 (thundering herd)
4. 明文存 token (security violation)
5. 不处理 clock skew (经典 30-60s buffer fix)
6. 没 multi-tenant key isolation
7. 没 monitor 401/429 rate (silent 上游问题)
8. PKCE 只给 mobile (现在 2026 ALL auth_code 必加)
9. 客户改密码后 refresh_token 失效 silent (必须 reauth_required flag)
10. Token endpoint down 跟着挂 (cache 兜底 missing)
11. Cross-tenant token leak via shared cache key
12. Log redact 漏掉 token (Sentry / APM trace 也要 redact)
13. No tokenized DB column field-level encryption
14. No OBO for compliance-strict customer
15. 大客户 rate limit 不谈 quota tier upgrade

### 简历 reframe 索引

| 题考点 | 你的项目 | 1-line story |
|---|---|---|
| Token exchange + refresh | Voice agent 7 markets | 每市场 repayment 系统 — OAuth 2.0 / HMAC / IP-allowlisted JWT 混合 |
| Multi-tenant secrets in HSM | BNPL chatbot | TikTok internal multi-service per-market DEK |
| Distributed lock on refresh | Voice agent thundering herd | per-tenant Redis SETNX + 5s wait |
| ConvFinQA: secure API key | `.env` + os.environ pattern, never hardcoded |
| Token Service central pattern | Internal Agent Platform shared service | 共享 token middleware for cross-team |
| Clock skew 30s buffer | Voice agent international | NTP 同步 + 30-60s tolerance |
| Composite + Bulk API | TikTok Salesforce integration | 10k records / req + 25 ops / req mitigate rate limit |

### 面试现场 quotables (top 8)

1. "OAuth 2.0 是授权协议不是认证协议. Authorization_code with PKCE 是 2026 best practice, 不仅 mobile, 所有 auth_code 都加."
2. "Refresh token rotation on use — 旧的立刻作废 + reuse detection → revoke 整链. 偷一次就被发现."
3. "Distributed lock per tenant on refresh prevents thundering herd. Without it, 10 concurrent 401 → 10 refresh → 9 失败 → 整链被 revoke = 灾难."
4. "Token endpoint down 不能跟着挂. Cache 30s TTL + 故障期间 serve stale token until expire."
5. "Per-tenant DEK (KMS derive) + 严格 WHERE tenant_id + Vault central + audit log + least priv. 6 原则缺一不可."
6. "Voice agent 7 markets — multi-tenant token mgmt. Trickiest was clock skew between our service + customer's auth server. 30s NTP buffer fixed 95% premature expiry."
7. "Customer 不许 store refresh_token: token broker on customer side / HSM with customer KEK / OAuth OBO short-lived per request."
8. "Rate limit mitigation: Bulk API 10k records/req + Composite 25 ops/req + CDC subscription not polling + backpressure queue + tier upgrade negotiate."

### 红线 (top 10 anti-patterns)

1. implicit / password grant (已废弃)
2. 明文 / 进 URL / 进 log token
3. Service account super-perms 跨 tenant
4. PKCE 只给 mobile (现在 ALL auth_code 必加)
5. 不处理 refresh race
6. 没 client_secret rotation
7. 不验 webhook signature
8. Customer 改密码 / revoke 不发现 (no reauth flag)
9. Token endpoint down 跟着挂 (no cache fallback)
10. No tokenized DB column field-level encryption

### Token lifetime cheat (主流 CRM)

| CRM | Access TTL | Refresh TTL | Rotation? | Rate limit / org |
|---|---|---|---|---|
| Salesforce | 2h (默认 15min-24h 可配) | 永久 (revoke 才失效) | 可选 enable | 5 req/sec/app/org (Bulk API 不算) |
| HubSpot | 30min | 6 months idle | 是 | 100 req/10s/app |
| Microsoft Dynamics 365 | 1h | 90d idle | 可选 | varies by license |
| Pipedrive | 1h | 永久 | no | 100 req/10s |
| Zoho CRM | 1h | 永久 (no rotation) | no | 10K calls/day |

### Storage matrix detail

| 场景 | 推荐 | 不能用 |
|---|---|---|
| Browser web app | httpOnly + Secure + SameSite=Lax Cookie | localStorage (XSS 一锅端) |
| Mobile iOS | iOS Keychain (kSecAttrAccessibleAfterFirstUnlock) | UserDefaults |
| Mobile Android | Android Keystore (hardware-backed) | SharedPreferences (明文) |
| Backend (B2B SaaS) | KMS-encrypted DB + Vault Transit | App config file, 明文 DB column |
| Short-term temp | Redis encrypted + TTL | 普通 log, APM trace, Sentry |

### Failure modes 5 套路 + remediation

| Failure | Symptom | Remediation |
|---|---|---|
| Token expire mid-call | 14:59:59.5 valid → 15:00:00 server side 过期 → 401 | preempt refresh 5min before exp + auto retry once on 401 |
| Refresh race | 10 并发 401 → 10 refresh → 9 失败 (旋转 rotation) | dlock per-tenant (Redis SETNX 10s timeout), singleflight |
| Revocation | Customer revoke 后 cache 还有, 全 401 | cache.delete + db.status='reauth_required' + notify + pause scheduled jobs |
| Clock skew | server 时间差 30s, JWT exp check fail | NTP + 60s buffer in JWT validation |
| Token endpoint down | Salesforce token endpoint 5xx | cache 兜底 serve stale valid token until expire |
| refresh_token expire (90d idle) | refresh 也失效 | reauth flow, customer 必须 re-OAuth |

### 4 grant types selection table

| Grant type | Use case | Has user? | Has refresh_token? | Browser involved? | Best practice |
|---|---|---|---|---|---|
| authorization_code | User delegation (CRM, SaaS) | YES | YES | YES | + PKCE (all flows, not just mobile) |
| client_credentials | Service-to-service, no user | NO | NO | NO | mTLS for internal as alternative |
| refresh_token | Continue session without re-login | YES (cached) | input | NO | Rotate on use (旋转) |
| device_code | IoT / CLI / TV (no browser) | YES | YES | YES (separate device) | Used by gh CLI, AWS CLI |
| [废弃] implicit | Mobile (old) | YES | NO | YES | Replaced by PKCE |
| [废弃] password (ROPC) | Migration only | YES | YES | NO | OAuth anti-pattern |

### Multi-tenant secrets 6 原则

| Principle | Implementation |
|---|---|
| 1. Per-tenant DEK | KMS derive (master_key, context=tenant_id) |
| 2. 严格隔离 | Postgres RLS + ORM 强制 WHERE tenant_id |
| 3. Vault / Secrets Manager central | Not in app DB |
| 4. Audit log 元数据 | actor + on_behalf_of + tool + ts, no raw token |
| 5. Least privilege IAM | TTS handler only reads its tenant token |
| 6. Rotation 自动化 | cron: access < 10min → refresh; refresh < 7day → notify customer; client_secret > 90d → rotate |

### Rate limit mitigation tactics (Salesforce-style)

| Tactic | Reduction | Example |
|---|---|---|
| Bulk API | 10k records / req | Salesforce Bulk 2.0 |
| Composite REST | 25 ops / req | Salesforce Composite |
| CDC subscription | event-driven (push) replace polling | Salesforce CDC |
| Backpressure queue | dampening burst | rabbitmq / Kafka |
| Quota tier upgrade | + Salesforce account team | enterprise tier |
| Cache + dedup | duplicate read collapse | Redis read-through |

### Middleware placement decision

| Team size | Pattern | Pros | Cons |
|---|---|---|---|
| < 5 services | SDK lib | 简单, 零网络跳数 | token 散落多进程内存, multi-lang 多套 SDK |
| Service Mesh 已跑 | Sidecar (Envoy) | 服务不感知 OAuth, 一处升级 | Service Mesh 运维复杂 |
| Multi-tenant 强合规 ⭐ | Dedicated Token Service | 单一职责, 集中管理, audit clean | SPOF, +1 跨网络调用 |
| Hybrid (字节 / 阿里规模) | Dedicated Service + local SDK cache | Both | 复杂 |

### Audit log fields (OAuth specific)

| Field | Example |
|---|---|
| ts | 2026-05-21T14:30:00Z |
| actor | service:tts-handler |
| action | token.read / token.refresh / token.revoke |
| tenant_id | tenant_abc |
| purpose | salesforce_api_call |
| outcome | success / failure |
| scope_used | ["read:contacts", "write:calls"] |
| token_id_hash | sha256 (not raw token) |
| api_endpoint | /services/data/v58.0/sobjects/Account |

### 4 customer auth scenarios (你的实际经验)

| Customer scenario | Auth pattern |
|---|---|
| Standard SaaS (most) | OAuth 2.0 authorization_code + PKCE |
| Compliance-strict (cannot store refresh) | OAuth OBO (on-behalf-of), short-lived per request |
| Enterprise BYOK | HSM with customer-controlled KEK |
| Behind firewall | Token broker on customer side, we call their service |
| Legacy partner (rare) | OAuth 1.0a HMAC-signed (deprecated but still seen) |
| Internal service-to-service | mTLS preferred over OAuth |

### Common error reasons + retry decision

| Error | Retry? | Action |
|---|---|---|
| 401 invalid_token | YES once after refresh | refresh + retry |
| 401 invalid_grant | NO | reauth flow |
| 403 insufficient_scope | NO | upgrade scope through customer flow |
| 429 rate_limit | YES with Retry-After | respect header |
| 500-504 transient | YES exponential backoff up to 3 | jittered |
| Other 4xx | NO | log + alert |
| Network timeout | YES with backoff | + cache fallback |
| Clock skew rejection | NO | NTP sync + 60s buffer |

