## Tech #1 · OAuth 2.0 CRM Integration — 复习速查

> 这是 **复习速查页**, 抽自 [原全量教学页](questions/oauth-crm-platform-integration.html). 10-15 min 通读, 含本主题的全量知识压缩版.

**原页面**: [`oauth-crm-platform-integration.html`](questions/oauth-crm-platform-integration.html)

---

## 🎤 答题逻辑 (Response Architecture)

> 被问到 **"你怎么让我们的 platform 集成 customer 的 CRM (Salesforce / HubSpot), 处理 OAuth, multi-tenant, token rotation, 故障?"** 我按这 7 层回答, 不跳序.

### 📐 OAuth 2.0 CRM Integration — 7 层 unpack + harden

| # | 层 | 时间 | 这层该说什么 (custom) | 开口句 |
|---|---|---|---|---|
| 1 | 3-term unpack | 30s | 先 unpack 3 confusable term: **access_token** (short-lived 1-24h, every API call), **refresh_token** (long-lived 30d-perpetual, only to /token endpoint, rotate per use), **authorization_code** (one-shot 10 min, exchanged 1x for tokens). 90% bug 是混淆这 3 个 | "Three terms first because they get confused — access vs refresh vs auth_code…" |
| 2 | Disaster scenario hook | 30s | "想象 user 把 Salesforce 密码贴 chat 给 agent. 1 incident, breach 全公司 CRM. OAuth 2.0 designed for this — never share password, delegate scoped token" | "The reason OAuth exists — never share passwords. Disaster scenario…" |
| 3 | authorization_code with PKCE end-to-end | 2.5 min | 6-step flow: (1) /authorize redirect with state + PKCE code_challenge S256, (2) user consent screen, (3) callback with code + state verify, (4) /token POST exchange code + code_verifier → access + refresh, (5) call API with Bearer, (6) on 401 → refresh flow with rotation. State CSRF, PKCE 防 code 拦截 | "I default to authorization_code with PKCE — 6 steps, state + PKCE prevent CSRF + code interception…" |
| 4 | 4 grant types 决策树 | 1.5 min | (a) authorization_code + PKCE → user-facing 3rd party (Salesforce); (b) client_credentials → service-to-service (your platform → vendor backend); (c) refresh_token rotation → keep alive long-lived; (d) device_code → CLI / TV / IoT no browser. Implicit grant deprecated, password grant 死掉 | "Four grants — code+PKCE / client_creds / refresh / device_code — implicit and password grants are dead…" |
| 5 | Multi-tenant secret + 4 storage 层 | 2 min | Per-tenant DEK wrap by KMS. 4 storage: (a) browser → httpOnly Secure SameSite cookie or window.sessionStorage; (b) mobile → iOS Keychain / Android Keystore; (c) server backend → KMS (AWS/GCP) + Vault for static client_secret; (d) hot cache → Redis encrypted at rest with TTL 5 min. Never localStorage for access tokens | "Storage is tiered — cookie / Keychain / KMS+Vault / Redis encrypted — per-tenant DEK…" |
| 6 | Refresh storm + clock skew + cache 兜底 | 2 min | Distributed lock (Redis SETNX) on refresh per tenant — 100 workers expire same token, 1 refresh, 99 wait + retry. 30s clock skew buffer (refresh at exp-60s not exp). On vendor 5xx fallback to cached token + retry with backoff. On vendor down 30 min, circuit breaker + customer notification. Bulk rate-limit mitigation: per-tenant token bucket, queue smoothing | "Three production hardening — distributed lock on refresh + 30s clock skew + cache fallback + circuit breaker…" |
| 7 | Middleware pattern + BNPL resume hook | 1.5 min | 3 pattern: (a) SDK in each service (low overhead, code duplication); (b) sidecar (Envoy / dedicated proxy, 1 hop latency); (c) dedicated Token Service (microservice, single source of truth, +1 hop). 我选 Token Service for multi-tenant SaaS — single audit point, easier rotation. "BNPL chatbot multi-tenant: each merchant 自己的 client_id + DEK + refresh rotation, Token Service centralized, 0 cross-tenant token leak in 18 months" | "Middleware — I pick Token Service for multi-tenant — single audit point…" |

### 🎯 为啥按这个序

3-term unpack 第一 because 面试官 5 秒判断你懂不懂 OAuth. Disaster scenario 提供 motivation (why exist). authorization_code + PKCE 是 most-used flow 必须 nail down. 4 grant decision tree 是 "你知道何时用哪个" 的 signal. Multi-tenant storage 是 enterprise gotcha — 90% startup 死在这. Hardening (refresh storm + clock skew + cache) 是 production-only knowledge. Token Service + BNPL hook 收尾.

### 🔥 哪一层最容易被追问 deeper

**Layer 3 (PKCE)** — 必被追 "Why PKCE if I'm a confidential client?" → 答: defense-in-depth. Even confidential clients (server-side with client_secret) benefit from PKCE because (a) it prevents auth code interception via redirect_uri hijack, (b) latest OAuth 2.1 draft recommends PKCE for all client types, (c) zero cost to add. code_challenge = SHA256(code_verifier), code_verifier 43-128 random char.

**Layer 6 (refresh storm)** — 追 "Why distributed lock not just retry?" → 答: 100 worker hit expired token simultaneously → 100 refresh requests → vendor rate-limit blocks ALL → cascade failure. Distributed lock (Redis SETNX with TTL 10s) means 1 worker refreshes, 99 wait 50ms then retry with new token. Single-flight refresh per tenant.

### ⏱ 时间压缩版 (30 min round)

- 0-3 min: Layer 1+2 (3-term + disaster scenario)
- 3-12 min: Layer 3+4 (PKCE 6-step + 4 grant tree)
- 12-20 min: Layer 5+6 (multi-tenant storage + hardening)
- 20-26 min: Layer 7 (Token Service + BNPL 18-month no-leak)
- 26-30 min: Q&A buffer

### 🆘 卡壳兜底 (针对这题)

- 忘 PKCE 步骤 → "code_verifier = 43-128 random char, code_challenge = base64url(SHA256(verifier)). 发 challenge, 后面用 verifier 验证. 标准 RFC 7636"
- 被问 token revocation → "RFC 7009 /revoke endpoint, vendor-specific support 不一致, fallback = blocklist token in our cache + wait expiry"
- 不熟 vendor 具体 (Salesforce / HubSpot 怎么实现) → "I follow RFC, vendor extension I look up in docs first 30 min; main risk is non-standard refresh rotation policy, e.g., Salesforce uses sticky refresh"

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
