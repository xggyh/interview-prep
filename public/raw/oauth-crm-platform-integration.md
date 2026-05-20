## 题目（verbatim）

> "Design an **OAuth 1.0/2.0 integration** bridging between a client's **CRM** and your **platform API**. Cover token exchange, middleware placement, retry logic, and credential rotation."

**出处**：fde.academy 列出的 FDE 核心 integration 题。Palantir / Salesforce / Databricks / Google Cloud FDE 都问过。

**Round**：Technical Integration (45-60 min)

---

## 这道题在考什么

考你**enterprise integration 实战**。OAuth 在每家 customer 都不一样：

1. **OAuth 2.0 4 个 grant types 知不知道** —— authorization_code / client_credentials / refresh_token / device_code
2. **Token storage + rotation** —— 真生产 deployment 必须 handle
3. **Middleware placement** —— SDK / proxy / dedicated service？
4. **Failure modes** —— token expire mid-call, refresh race, revocation
5. **Multi-tenant secrets management**

不考"OAuth 是什么"，考"你 production 部署过 OAuth integration"。

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

## 5 步框架

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify direction + grant + version |
| 5-20 min | **End-to-end token exchange flow** (画 sequence diagram) |
| 20-35 min | **Middleware** placement (Token Service vs SDK vs proxy) |
| 35-45 min | **Retry + rotation + revocation** |
| 45-60 min | Failure modes + multi-tenant key mgmt |

---

## 我会这样答（sample monologue）

> "Clarify first — *[假设答：we're OAuth client, CRM is Salesforce, authorization_code grant with refresh_token, 2h access + 90d refresh, 100 QPS sustained]*.
>
> **End-to-end token exchange flow**:
>
> ```
> 1. User clicks 'Connect Salesforce' in our UI
> 2. We redirect to:
>    https://login.salesforce.com/services/oauth2/authorize
>      ?client_id=...&redirect_uri=...&response_type=code&scope=api+refresh_token
> 3. User authorizes, redirected to us with ?code=...
> 4. Our backend POST to /services/oauth2/token:
>    grant_type=authorization_code, code=, client_id=, client_secret=, redirect_uri=
> 5. SF returns {access_token, refresh_token, expires_in=7200, instance_url}
> 6. We persist {tenant_id, sf_org_id, encrypted(access_token), encrypted(refresh_token), expires_at}
> 7. Subsequent CRM calls: Authorization: Bearer <access_token>
> 8. On 401: refresh access_token via refresh grant, retry once
> ```
>
> **Middleware placement** — 3 options:
>
> | Pattern | Pros | Cons |
> |---|---|---|
> | SDK lib in every service | Latency-low | Auth logic duplicated, hard to rotate |
> | Sidecar proxy per service | Auth-isolated | Per-service ops |
> | **Central Token Service** | Auth single source of truth, easy rotation | +1 hop latency (~5ms) |
>
> **STAFF answer**: Central Token Service with **local cache in service**. Service queries Token Service every 30s for current valid token (or on 401 forced refresh). Token Service handles refresh, encryption, revocation.
>
> **Retry logic**:
> ```python
> def call_crm(endpoint, body, tenant_id):
>     token = token_service.get(tenant_id)
>     resp = http.post(endpoint, body, headers={'Authorization': f'Bearer {token}'})
>     if resp.status == 401:
>         # Token expired or revoked
>         token = token_service.refresh(tenant_id)  # acquires fresh
>         resp = http.post(...)  # ONE retry
>     if resp.status == 429:
>         # Rate limited; backoff per Salesforce's Retry-After header
>         sleep(int(resp.headers['Retry-After']))
>         resp = http.post(...)
>     if resp.status >= 500:
>         # Idempotent? retry with jittered exponential backoff up to 3x
>     return resp
> ```
>
> Single retry on 401, multiple on 5xx with backoff, never retry on 4xx (other than 401/429).
>
> **Credential rotation**:
> - **client_secret rotation**: Salesforce rotates on suspicion. Our system supports **2 active secrets** (old + new) for 30-day cutover.
> - **access_token expiry**: handled by refresh
> - **refresh_token revocation**: when user clicks "disconnect" in CRM, refresh fails — alert, re-prompt user
>
> **Failure modes**:
> - **Refresh race**: 10 concurrent requests all see 401 → 10 refreshes hit Salesforce. **Solution**: distributed lock per tenant (Redis SETNX) on refresh, first wins, others wait
> - **Clock skew**: server time off → premature expiry. Add 30s buffer
> - **PII in tokens** (JWT): never log tokens. Audit logs use token hash
> - **Multi-region**: Token Service per region with cross-region cache invalidation on revocation
>
> **Multi-tenant secrets**:
> - per-tenant client_id/client_secret stored in **HSM** (or Vault)
> - encryption at rest with per-tenant DEK + central KEK
> - **access_token + refresh_token** in DB encrypted with per-tenant DEK
> - audit log every token access (compliance)
>
> **What I'd add for production**:
> - **Monitoring**: track 401 / 429 / 5xx rates per tenant. Spike in 401 = upstream credential rotation
> - **Token lifecycle dashboard**: time-since-last-refresh, tokens nearing expiry
> - **Test harness**: mock OAuth server for integration tests"

---

## 简历专属 reframe

你的 **voice agent 7 markets** + **BNPL chatbot** 都有 enterprise auth：

| OAuth 题 | 你的经验 |
|---|---|
| Token exchange + refresh | 你的 voice agent 集成 7 个市场的 repayment 系统 — 各自不同 auth |
| Multi-tenant secrets in HSM | BNPL chatbot 跨 ByteDance internal 多 service |
| Distributed lock on refresh | Voice agent 你做过 thundering herd 类似问题 |
| ConvFinQA: secure API key handling | 你做过 `.env` + os.environ 模式, not hardcoded |
| Token Service central pattern | 你的 internal Agent Platform 应该有共享 service 设计 |

**主动说**：

> "I've implemented this pattern across 7 markets for the voice agent — each market's repayment system had different auth (some OAuth 2.0, some HMAC, some IP-allowlisted JWT). We centralized into a Token Service with per-tenant DEK encryption + distributed refresh lock. The trickiest failure mode I hit was **clock skew between our service and the customer's auth server** — a 30s buffer fixed 95% of premature-expiry incidents."

→ 显你真生产过 enterprise auth.

---

## 5 follow-ups

**Q1**: "Refresh race — 10 concurrent calls all 401. What happens?"
**A**: Without coordination, 10 parallel refresh requests hit Salesforce → 10 different refresh_tokens → 9 are now invalidated (Salesforce rotates refresh on use). 解：
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

## ❌ 易错点

1. **OAuth 2.0 当 single thing** — 4 个 grant types 区分不清
2. **每 service SDK** — auth 逻辑分散
3. **没 refresh race 处理** — production thunder
4. **明文存 token** — security violation
5. **不处理 clock skew** — 30s buffer 是经典 fix
6. **没 multi-tenant key isolation**
7. **没 monitor 401/429 rate** — 上游问题 silent

---

## ✅ 加分项

1. **Central Token Service + local cache** pattern
2. **Distributed lock on refresh** prevent stampede
3. **2 active client_secrets** for rotation cutover
4. **OBO flow** for compliance-strict customers
5. **30s clock skew buffer**
6. **Composite + Bulk API** for rate-limit avoidance
7. **HSM / Vault** for client_secret
8. **Tokenized DB column + per-tenant DEK**

---

## Cheat Sheet

```
OAuth grant types:
  authorization_code  - user delegation (most CRMs)
  refresh_token       - long-lived re-issue
  client_credentials  - service-to-service
  device_code         - IoT / TV

Architecture:
  Service → Token Service (central) → CRM
            ↓
        per-tenant secrets in HSM
        access/refresh in DB (encrypted DEK)

Retry rules:
  401 → refresh + 1 retry
  429 → respect Retry-After header
  5xx → exponential backoff up to 3
  Other 4xx → don't retry

Failure modes:
  - Refresh race → distributed lock per tenant
  - Clock skew → 30s buffer
  - Stampede on rotation → warm refresh 5min before expire
  - Token in logs → hash for correlation

Multi-tenant security:
  HSM/Vault for client_secret
  Per-tenant DEK + central KEK
  Audit log every access
  TLS 1.3 + AES-256

Rate-limit mitigation:
  Bulk API (10k/req)
  Composite REST (25 ops/req)
  CDC subscription not polling
  Backpressure queue
```
