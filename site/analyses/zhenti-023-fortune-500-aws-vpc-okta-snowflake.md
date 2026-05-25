## Q23 · F500 在自己 AWS VPC 部署, 用 Okta SSO + Snowflake

> "A Fortune 500 customer wants us deployed **inside their AWS VPC** (no SaaS), using their **Okta SSO**, reading data from their **Snowflake** instance. They have a security review process that takes 6 weeks. **Design the deployment + ongoing operations**. How do you push code updates without re-running the security review?"

**Round**: System Design (60 min)
**出处**: Exponent 2026 FDE · 公司: Palantir / Databricks / Snowflake / Anthropic Enterprise · 行业: cross-industry F500 (bank, insurance, retail)
**约束**: customer VPC isolation / Okta SSO / Snowflake-as-source-of-truth / no public internet egress (or scoped allowlist) / 6-week security review process / customer compliance team gates every change / BYOK encryption

---

## 这道题在考什么

不是考你 K8s, 是考你**真正在客户 VPC 里跑过软件**, 知道这些坑:

1. **Single-tenant VPC deploy** — 区别 SaaS multi-tenant 和 customer-self-hosted, 后者每客户一份, version drift 是命门
2. **Okta SSO 集成** — OIDC vs SAML, JIT provisioning, group-to-role mapping, SCIM 用不用
3. **Snowflake connector** — Key-pair auth (preferred), External OAuth (Okta), Network Policy whitelist, role-based access via Okta groups
4. **6-week security review** — 你的 architecture 要把 "what re-triggers review" 降到最少. infra changes 重审, code changes (golden image upgrade) 不重审 是关键设计
5. **BYOK (Bring Your Own Key)** — customer-controlled KMS, envelope encryption, "we never have plaintext"
6. **No-egress posture** — VPC endpoints / Private Link, no NAT GW, scoped exceptions for software updates
7. **Telemetry back-haul** — 我们想看产品健康, 客户不让数据出, 怎么办 (脱敏 metrics-only via PrivateLink)
8. **菜鸟答案失败点**: "Terraform deploy + Okta OIDC + Snowflake JDBC" — 太浅. 没回答 update mechanism, BYOK, telemetry, 6-week 复审控制, multi-customer fleet management.

---

## 必问 clarifying questions

1. **Single customer or fleet?** 1 个 F500 还是 50 个 F500? 决定 fleet ops 投资
2. **What does "deployed in their VPC" mean?** Pure on-prem-style (无外部网络) 还是 our-account-peering 还是 dedicated VPC in their AWS organization?
3. **Update model**: 客户允许我们 SRE push updates 还是 customer ops team 自己 deploy?
4. **Telemetry**: 我们能看到什么? full traces? metrics-only? nothing (air-gap)?
5. **Snowflake reader role**: 是只读 还是 read+write? 决定 OAuth flow
6. **Okta source of truth**: Okta 管 user + group, 我们只是 RP, 还是要做自己的 RBAC?
7. **Compliance**: SOC 2 / FedRAMP / PCI? 决定额外控制
8. **Update SLA**: bug fix 客户接受 24h 还是 2 周? 决定 update path complexity

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|------|------|------|
| 1 | Clarify | 5 min | 锁部署模式 + 更新模式 + 客户网络姿态 | "三件事: deploy 是 our-account or customer-account, update 谁 push, customer 允不允许 egress" |
| 2 | Deployment model | 8 min | Customer AWS account + Terraform/CDK + Helm | "Terraform provision infra, Helm deploy app, 全在 customer account" |
| 3 | Okta SSO + Snowflake | 10 min | OIDC RP + External OAuth + group→role | "Okta 是 IdP, 我们是 RP, group-to-role via OIDC claims" |
| 4 | Update mechanism | 10 min | Golden image versioning + customer-controlled apply | "Image 是 versioned artifact, apply 是 customer ops 一键 helm upgrade" |
| 5 | Security review minimization | 8 min | Infra-stable vs app-update 区分 + signed images + SBOM | "把 infra 锁死, app 走 update channel, 只 infra change 才重审" |
| 6 | Telemetry / observability | 7 min | Customer-controlled egress 给 metrics-only OTLP | "Customer 给我们 PrivateLink to OTel collector, 只 metrics 没数据" |
| 7 | Multi-customer fleet | 7 min | Manage 50 customer 用 GitOps + per-customer Terraform state | "Per-customer git repo, Argo CD 或 Flux 拉版本, 我们 SRE 控版本 release channel" |
| 8 | Trade-offs + close | 5 min | EKS vs ECS, BYOK level, Air-gap posture | "EKS 我推荐 — 客户大部分已有, K8s 标准化 maintenance window" |

---

## 端到端架构图 (ASCII)

```
                Customer F500 AWS Account (us-east-1, their org)
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                          │
│   ┌──── VPC: customer-dedicated (10.50.0.0/16) ────────────────────────────────────┐    │
│   │                                                                                 │    │
│   │   ┌─Private subnet (app)─────────────────────────────────────────────────┐     │    │
│   │   │                                                                       │     │    │
│   │   │   EKS cluster (customer-account)                                      │     │    │
│   │   │   ├─ Namespace: agent-platform                                        │     │    │
│   │   │   │   ├─ Pod: api-gateway (OIDC RP, validates Okta JWT)               │     │    │
│   │   │   │   ├─ Pod: agent-orchestrator (LangGraph / state machine)         │     │    │
│   │   │   │   ├─ Pod: tool-server (MCP, talks to Snowflake)                  │     │    │
│   │   │   │   ├─ Pod: model-router (calls Bedrock-in-VPC via PrivateLink)    │     │    │
│   │   │   │   └─ Pod: ui-frontend                                            │     │    │
│   │   │   ├─ Namespace: ops                                                  │     │    │
│   │   │   │   ├─ Pod: otel-collector (forwards to customer Datadog only)     │     │    │
│   │   │   │   └─ Pod: argo-cd (GitOps controller, pulls from cust gitlab)    │     │    │
│   │   │   └─ Service mesh: Istio (mTLS, traffic policies)                    │     │    │
│   │   └─────────────────────────────────────────────────────────────────────┘     │    │
│   │                                                                                 │    │
│   │   ┌─Private subnet (data)────────────────────────────────────────────────┐    │    │
│   │   │  Aurora Postgres (state, audit) — KMS BYOK encryption                │    │    │
│   │   │  ElastiCache Redis (session, ACL cache) — encryption at rest         │    │    │
│   │   │  S3 (logs, snapshots, telemetry buffer) — KMS BYOK + Object Lock     │    │    │
│   │   └─────────────────────────────────────────────────────────────────────┘    │    │
│   │                                                                                 │    │
│   │   ┌─VPC endpoints (no IGW, no NAT)──────────────────────────────────────┐    │    │
│   │   │  com.amazonaws.us-east-1.s3                  (Gateway VPCe)         │    │    │
│   │   │  com.amazonaws.us-east-1.dynamodb            (Gateway VPCe)         │    │    │
│   │   │  com.amazonaws.us-east-1.bedrock-runtime     (Interface VPCe, $$)   │    │    │
│   │   │  com.amazonaws.us-east-1.kms                 (Interface)            │    │    │
│   │   │  com.amazonaws.us-east-1.secretsmanager      (Interface)            │    │    │
│   │   │  com.amazonaws.us-east-1.ecr.dkr             (Interface, image pull) │    │    │
│   │   │  com.amazonaws.us-east-1.ecr.api             (Interface)            │    │    │
│   │   │  snowflake-privatelink (Snowflake VPCe via AWS PrivateLink)         │    │    │
│   │   │  okta-privatelink (Okta VPCe optional)                              │    │    │
│   │   └─────────────────────────────────────────────────────────────────────┘    │    │
│   └─────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                          │
│   ┌─Customer IAM────────────────────────────────────────────────────────────────────┐  │
│   │   Cross-account role: arn:aws:iam::customer:role/AgentPlatform-Admin             │  │
│   │   (limited Trust to our SRE account, used only for incident response)           │  │
│   └────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                              │                                              │
                              │ Customer-controlled egress (whitelist)       │ Inbound (no public IP)
                              ▼                                              ▼
                  ┌───────────────────────────────┐               ┌─────────────────────┐
                  │ Customer's ECR (their account)│               │ Customer end users  │
                  │ Our golden images mirrored    │               │ (via Okta SSO)      │
                  │ via cross-account ECR replic │               │ → internal network  │
                  └───────────────────────────────┘               │   → ALB internal    │
                              ▲                                  │   → API GW          │
                              │ scoped allowlist                 └─────────────────────┘
                              │ ecr.us-east-1.amazonaws.com
                              │ (no general public internet)
                              │
                              │
                  ┌──── Outbound channels (read-only, low bandwidth) ──┐
                  │                                                    │
                  │  PrivateLink to customer's Datadog (metrics only)  │
                  │  or                                                │
                  │  Push to S3 bucket (customer reviews + forwards)   │
                  └────────────────────────────────────────────────────┘

   Our SRE side (separate AWS org):
   ┌─────────────────────────────────────────────────────────────────────────────┐
   │   Build pipeline (GitHub Actions / Buildkite):                              │
   │   - Source → multi-stage Dockerfile → ECR public/private                    │
   │   - Sign image with Cosign + Notary v2                                      │
   │   - Generate SBOM (Syft) + scan (Snyk, Trivy)                               │
   │   - Publish helm chart to OCI registry                                      │
   │                                                                             │
   │   Release channel:                                                          │
   │   - stable / beta / canary tagging                                          │
   │   - Customer Argo CD pulls from their ECR (replicated from ours)            │
   │   - Customer ops team approves PR in their GitOps repo                      │
   └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 详细设计 (60-min walkthrough)

### Phase 1: Clarify + KPI (5 min)

锁:
- "Customer 是 dedicated AWS account 在他们 org 下还是 our-account-peered? 大 F500 99% 是前者"
- "Update 是我们 SRE push 还是 customer ops team apply? 影响 RBAC / approval 设计"
- "Telemetry: 我们能拿 metrics? logs? nothing? F500 通常 metrics-only"
- "Snowflake 角色: 只读 vs 读写? 决定 OAuth scope"

我假设: 单一 F500 (能 generalize 到 fleet of 50), customer-account 部署, update 是 customer-apply (我们提供 PR), telemetry metrics-only.

KPI:
- **Deploy time** (greenfield): ≤ 8 weeks (含 6-week 安全审, 1 week infra, 1 week app)
- **Time to push critical bug fix**: ≤ 5 work days (含 customer ops review)
- **Time to push non-breaking minor**: ≤ 1 work day (auto-promote in stable channel after eval)
- **Telemetry coverage**: 100% production via OTel, 0% raw data egress
- **Compliance**: SOC 2 + customer-specific (FedRAMP / PCI / HITRUST depending)

### Phase 2: Deployment model (8 min)

**2.1 谁 owns the AWS account**

| 选项 | 谁 own | Pros | Cons |
|---|---|---|---|
| Our-account peering | 我们 own AWS account, VPC peer to customer | 我们 SRE 全控 | F500 99% 不允许 (data 出 customer network) |
| Customer-account, our access | Customer own account, 给我们 cross-account role | 数据 100% in customer | 我们 SRE access 受限 |
| Customer-account, no access | Customer own, 我们零 access | 最严 | 不能 incident response |

F500 几乎都是 #2 — customer 主账号, 我们通过 IAM cross-account role 在 break-glass 时进. 日常 SRE 不进 customer 账号.

**2.2 Infrastructure provisioning: Terraform + Helm**

Two-stage:
- **Stage 1 (Terraform)**: Greenfield infra. VPC, subnets, EKS, RDS, KMS, IAM, security groups, VPC endpoints. 这一步过 customer security review (6 周). 之后稳定.
- **Stage 2 (Helm)**: Application. 这一步通过 GitOps (Argo CD) 持续部署, 不需要 re-审.

我们提供:
- `terraform-aws-agent-platform-infra` — Terraform module, customer apply 一次
- `helm-chart-agent-platform` — Helm chart, Argo CD 持续 pull

为什么 Helm + Argo: customer ops team 习惯, 不强加新工具.

**2.3 Image management**

- 我们的 ECR (公网) → customer 的 ECR (他们 account) 通过 ECR cross-account replication (cron 或 EventBridge)
- 即使我们 SRE 失误, customer 仍能 rollback (image 在他们 ECR)
- 所有 image signed with Cosign, customer Argo 配 admission controller (Kyverno) 验签

### Phase 3: Okta SSO + Snowflake (10 min)

**3.1 Okta as IdP**

Two integration points:
- **Customer end-users → our app**: Authorization Code Flow with PKCE (OIDC). Okta 颁 JWT, 我们 RP 验签 + extract claims.
- **Our app → Snowflake**: External OAuth flow. Snowflake 信 Okta JWT, role 映射 Okta group.

OIDC config:
```yaml
oidc:
  issuer: "https://customer.okta.com"
  client_id: <our app ID in Okta>
  client_secret: <stored in customer Secrets Manager>
  scopes: [openid, profile, email, groups]
  jwks_uri: "https://customer.okta.com/.well-known/keys"
  group_claim: "groups"
  group_to_role_mapping:
    - okta_group: "agent-platform-admin"
      app_role: "admin"
    - okta_group: "agent-platform-user"
      app_role: "user"
    - okta_group: "snowflake-prod-reader"
      app_role: "snowflake-reader"
```

**JIT provisioning**: 用户首次 login, group claims 决定 role, 不需要 我们 RBAC 重复维护. SCIM 仅在大客户要求时启用 (Okta push user state).

**Step-up MFA**: 敏感操作 (admin) 触发 Okta Adaptive MFA, 通过 `acr_values` claim 强制.

**3.2 Snowflake connector**

3 种 auth 给客户选:

| Auth | 适合 | 安全性 |
|---|---|---|
| Key-pair (RSA) | 服务账号 (我们 app → Snowflake) | 高 (RSA key in Secrets Manager) |
| External OAuth (Okta) | 用户级 query, user identity preserved | 最高 (user audit clear) |
| Password / SCIM-managed | 不推荐 | 低 |

我们推 **Key-pair for service + External OAuth for user-scoped queries**.

Snowflake side setup (customer DBA 做):
```sql
-- Create our service role with read-only on relevant schemas
CREATE ROLE AGENT_PLATFORM_READER;
GRANT USAGE ON DATABASE PROD TO ROLE AGENT_PLATFORM_READER;
GRANT USAGE ON SCHEMA PROD.SALES TO ROLE AGENT_PLATFORM_READER;
GRANT SELECT ON ALL TABLES IN SCHEMA PROD.SALES TO ROLE AGENT_PLATFORM_READER;

-- Create user for our service, key-pair auth
CREATE USER AGENT_PLATFORM_SVC
  RSA_PUBLIC_KEY = '<our pub key>'
  DEFAULT_ROLE = AGENT_PLATFORM_READER;

-- Network policy: only customer VPC CIDR
CREATE NETWORK POLICY AGENT_PLATFORM_NP
  ALLOWED_IP_LIST = ('10.50.0.0/16');
ALTER USER AGENT_PLATFORM_SVC SET NETWORK_POLICY = AGENT_PLATFORM_NP;
```

**PrivateLink**: Snowflake 提供 AWS PrivateLink endpoint, customer 把 Snowflake URL 解析到 VPC endpoint, 数据完全私网. 无 internet hop.

**Query patterns**:
- Service queries (agent tool calling Snowflake): use key-pair, role = AGENT_PLATFORM_READER, scope by role grants
- User-attributed queries (audit who asked what): use External OAuth, Okta JWT 传递, Snowflake recognize user, query log 自带 user_id

### Phase 4: Update mechanism (10 min)

这是面试官最爱深挖的题. 6 周 security review 不能每 release 都过, 否则一年 release 8 次. 设计:

**4.1 Infra 锁死, App 通道更新**

定义 "infra change requires re-review" 的边界:
- 改 VPC / subnet / security group / IAM policy → **infra change, re-review**
- 改 EKS / RDS instance class → **infra change, re-review**
- 改 Helm chart container image tag → **app change, no re-review** (only image hash diff, no privilege escalation)
- 加新外部依赖 (Snowflake schema / 新 API endpoint) → **app change but customer notifies security**

把客户 ops 训练成: "infra-tagged change requires SecRev, app-tagged自助"

**4.2 Image signing + admission policy**

```yaml
# Kyverno policy on customer EKS
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-signed-images
spec:
  rules:
    - name: verify-cosign-sig
      match:
        any:
          - resources:
              kinds: [Pod]
              namespaces: [agent-platform]
      verifyImages:
        - imageReferences:
            - "*.ecr.amazonaws.com/agent-platform/*"
          attestors:
            - count: 1
              entries:
                - keys:
                    publicKeys: |
                      -----BEGIN PUBLIC KEY-----
                      <our pub key>
                      -----END PUBLIC KEY-----
```

Cosign 签名 + Kyverno 验签. 即使有人 push 假 image 到 customer ECR, 没有我们 SRE private key 签名, pod 起不来.

**4.3 Release channels**

| Channel | 谁 deploy | 何时 |
|---|---|---|
| `dev` | 我们 internal | 我们 SRE 测试 |
| `beta` | 1-2 friendly customer | Friday afternoon, our SRE 看一周 |
| `stable` | 90% customer | Beta + 2 weeks, no regression |
| `lts` | 大保守 F500 | Stable + 4 weeks, security 重审 quarterly |

Customer 在 Argo CD `Application` resource 里写 `channel: stable`. 我们 SRE update `stable → v1.4.5` 触发 customer Argo 拉新版本 (customer ops 审 PR + apply).

**4.4 Customer-controlled apply**

最大尊重: customer 决定何时 apply. Argo CD 设置 `syncPolicy: manual`, customer ops team 看 release notes + change diff + 一键 sync.

我们提供 release notes 模板:
- Summary (1 line)
- Affected components
- Privilege diff (是否新加 IAM permission)
- Public endpoint diff (是否暴露新端口)
- Backward compatibility (能 rollback 吗)
- Customer action required (auth update / config tweak)

**4.5 Emergency hotfix path**

Critical CVE (CVSS ≥ 9.0) — 标准 5-day flow 太慢. Pre-arranged emergency channel:
- 我们 SRE 跟客户 security team 直线 (PagerDuty integration)
- Hotfix branch + signed image within 4h
- Customer ops 跑 pre-approved `helm rollback` 或 `helm upgrade --version=hotfix-X`
- 24h SLA from CVE disclosure to deployed fix

### Phase 5: Minimizing security review surface (8 min)

**5.1 Architecture stability statement**

跟客户安全团队约定 "Architecture Stability Contract":
- VPC 拓扑不变
- Subnet 不变
- IAM role 不新增 (existing role 不放权)
- Security group ingress rules 不变
- External egress allowlist 不变
- KMS key usage 不变

只要这 6 条不变, code change = no re-review.

**5.2 SBOM (Software Bill of Materials)**

每个 image push, 生成 SBOM (Syft) + sign. Customer security team 自动 scan SBOM:
- New CVE in deps? alert
- New transitive dep? alert
- License change? alert

SBOM 自动化 customer security review 从 "看代码" 变成 "diff SBOM + diff IaC", 效率高 10×.

**5.3 Audit-ready evidence package**

每次 release 自动生成:
- Image digest + signature
- SBOM diff vs previous version
- Terraform plan diff (应该是空的, infra stable)
- Test report (我们的 eval suite passed)
- Threat model delta (是否引入新 threat)

Customer security 不需要 re-审, 因为证据齐.

**5.4 Pre-approved IaC patterns**

如果偶尔需要新 infra (e.g., 加个 EKS node group for GPU workload), 我们维护 "pre-approved patterns" library. Customer security 一次审 pattern, 之后类似 change 走 expedited review (1 week 而不是 6 周).

### Phase 6: Telemetry / observability (7 min)

**6.1 Customer 让看什么**

| 类别 | 默认 | F500 通常 |
|---|---|---|
| Raw user data | NO | NO |
| Raw query content | NO | NO |
| PII-redacted logs | maybe | usually NO |
| Aggregated metrics | yes | yes |
| Anonymized traces | maybe | sometimes |
| Health check ping | yes | yes |

设计成 **metrics-only by default**, opt-in for redacted logs.

**6.2 OTel collector pattern**

Customer-controlled collector in their VPC. 我们的应用 emit OTLP 到 cluster 内 collector. Customer ops 配 exporter:
- 默认: 仅 metrics → customer Datadog / Splunk / Dynatrace (customer 已经在用)
- 选项: PII-redacted logs → customer Splunk
- 我们 SRE 看: zero (除非 customer push 给我们 dashboard summary)

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols: {grpc: {}, http: {}}
processors:
  attributes/redact:
    actions:
      - key: user.id
        action: hash
      - key: query.text
        action: delete
      - key: snowflake.row_data
        action: delete
  batch: {}
exporters:
  prometheusremotewrite/customer:
    endpoint: "https://customer-prom.internal/api/v1/write"
  # NO exporter back to our SRE — telemetry stays in customer VPC
service:
  pipelines:
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheusremotewrite/customer]
```

**6.3 Our SRE visibility (degraded mode)**

我们 SRE 想看产品健康 → customer 同意:
- 每天 customer Argo 把 `daily-summary.json` push 到我们的 S3 (内含: tenant_id, deployment_version, request_count, error_rate, p99_latency, NO content)
- 我们 SRE dashboard 显示 fleet-wide health from this summary

Incident: customer 主动 page 我们, 我们 SRE 通过 break-glass cross-account role 进 customer EKS (限时 4h, 自动 revoke), 看 kubectl logs, audit-recorded session.

### Phase 7: Multi-customer fleet ops (7 min)

50 个 F500 怎么管?

**7.1 GitOps repository per customer**

每个客户一个 git repo:
```
github.com/our-org/customer-acme/
├── infra/        — Terraform state (customer-owned, we contribute via PR)
├── helm/         — Helm values + customizations
└── runbooks/     — incident runbooks
```

我们 SRE 提 PR, customer ops review + merge + Argo apply.

**7.2 Fleet config**

```
github.com/our-org/fleet-config/
├── customers.yaml      — list of all 50, channel assignment, version pinning
├── release-channels/
│   ├── stable.yaml     — current stable version, 测试矩阵
│   ├── beta.yaml
│   └── lts.yaml
└── golden-config/      — base configs all customers inherit
```

新 release: 我们 fleet-config 改 stable version, GitHub Actions 自动 update 各 customer repo PR, customer 自决 merge timing.

**7.3 Per-customer variability**

不是所有 F500 一样:
- Some 用 Datadog, others Splunk / Dynatrace
- Some 在 us-east-1, others eu-west-1 (GDPR)
- Some 接 Bedrock Claude, others self-host Llama

用 Helm values 配置, 不 fork code. Anti-pattern: per-customer code branch.

**7.4 Customer onboarding playbook**

T+0 to T+8 weeks:
- W1: kickoff, security questionnaire, IaC walkthrough
- W2-W6: customer security review (us answer questions)
- W7: Terraform apply (customer ops)
- W8: Helm deploy (Argo first run), smoke test

T+8+: ongoing updates per release channel.

### Phase 8: Trade-offs + alternatives (5 min)

**Decision 8.1 — EKS vs ECS vs Lambda**

| 选项 | 适用 | Cons |
|---|---|---|
| EKS | F500 通常已有 K8s, 标准化 | EKS 自己运维成本 |
| ECS | AWS-native, simple | F500 K8s 是 standard, ECS 边缘化 |
| Lambda + step functions | Serverless, low ops | 不适合 stateful agent orchestration |

我选 **EKS** — F500 99% 已有, 客户 ops team 习惯 K8s.

**Decision 8.2 — BYOK level**

| Level | 谁 own key |
|---|---|
| L1: AWS-managed | AWS |
| L2: Customer KMS-managed (CMK) | Customer | ← 我们 default |
| L3: HSM-backed | Customer (CloudHSM) |
| L4: Bring your own | Customer (external HSM 上传到 KMS) |

L2 是 sweet spot. L3-L4 仅 banking/defense 客户.

**Decision 8.3 — Air-gap level**

| Level | 描述 | 谁需要 |
|---|---|---|
| L1: scoped egress (allowlist) | ECR, KMS endpoints | Most F500 |
| L2: zero egress | 完全断网, manual update | Defense, classified |
| L3: read-only customer pull | 我们 push 不到, customer 主动拉 | Banks |

我们 default L1, 客户配 L2/L3 可选.

---

## 关键决策点 (with rationale)

1. **Customer 主账号 + cross-account role** 而不是 our-account peering — F500 99% 要求数据 in their account.

2. **Two-stage IaC (Terraform infra + Helm app)** — infra 锁定 = 不重审, app 通道 update = 快迭代.

3. **Cosign signed images + Kyverno admission** — 防 supply chain 攻击, 同时 signal 我们专业.

4. **GitOps (Argo CD) + customer-controlled apply** — 客户决定 apply 时机, 不强 push.

5. **External OAuth for user queries + Key-pair for service** — user 级 audit + service 级 性能, 两者结合.

6. **Architecture Stability Contract + SBOM diff** — 把 "什么算 infra change" 跟客户安全队约定死, 大幅减少 6-week SecRev 触发次数.

7. **OTel metrics-only egress, never raw data** — customer trust 第一, 自己 SRE 视野第二.

8. **PrivateLink to Snowflake + VPC endpoints for AWS services** — 0 internet egress, customer 安全队认可.

---

## 数字 (capacity sizing, cost math)

**Single F500 deploy**:
- EKS cluster: 3 nodes (m6i.2xlarge) baseline + autoscale = ~$500/month
- RDS Aurora: 2 instances db.r6g.large = $400/month
- ElastiCache Redis: 2 nodes cache.r6g.large = $200/month
- VPC endpoints: 8 interface endpoints × $7.5/month + data = $100/month
- KMS: $1/key × 5 keys = $5/month
- S3: ~$50/month
- Bedrock 推理 (1M agent queries/month × 4K tokens): ~$10K/month
- Snowflake compute (我们 query 占用): ~$2K/month customer credit
- **Total**: ~$13K/month infra ≈ $156K/year per F500

**Our SRE cost**:
- 4 SREs × $200K = $800K (fleet of 50)
- $16K/customer-year, 加上 infra ≈ $172K/customer-year

**Pricing**:
- Charge $300K/year per F500 → gross margin 43%
- Volume discount big F500 → $250K, margin 30%
- 50 customer × $275K = $13.75M ARR

**Update velocity**:
- Time to design feature: 1 week
- Time to test internally: 1 week
- Time to beta (1-2 friendly customer): 1 week
- Time to stable (broader): 2 weeks
- Time to F500 conservative (LTS): +4 weeks
- **Total**: ~9 weeks from idea to F500 production

**Security review numbers**:
- Initial deploy SecRev: 6 weeks (one-time)
- Subsequent app update SecRev: 0 weeks (Architecture Stability Contract)
- Subsequent infra change SecRev: 2 weeks (expedited)
- Emergency hotfix: 4h to ship, 24h to customer-deployed

---

## Gao Xin 简历专属 reframe

1. **TikTok PayLater Singapore deploy** — 你做过跨区域 regulator-compliant deploy (Singapore MAS), 类似 F500 customer-controlled deploy 思路.

2. **Indonesia OJK audit** — 你证明能跟客户 (regulator) 合作 6-month preparation, F500 6 weeks SecRev 是同一 ballpark.

3. **TikTok 内部 Agent Platform multi-tenant** — 你做过 multi-customer fleet management (虽然 internal tenant 多), GitOps + per-tenant config 思路套.

4. **跨 region 多 market 7 个** — 你处理过 fleet ops, per-customer/per-market variability with shared core code, 这道题直接迁移.

5. **BNPL chatbot 跟 Snowflake / BigQuery integration** — 你做过 enterprise data warehouse integration, key-pair auth + role-based access 思路.

reframe: "我在字节做 voice agent 跨 7 个市场, fleet ops 模型跟这道题 F500 fleet 一样: per-customer GitOps repo + 共享 core release channel + customer ops 决定 apply 时机. 我会迁移这套到 F500 deploy, 多加 Architecture Stability Contract 的设计来管 6-week SecRev."

---

## 5 个 Follow-ups

1. **"客户 ops team 自己 SRE 经验不够, 没法 review Argo PR. 怎么办?"** — 答: 我们提供 "白手套" 服务 — 我们 SRE 提 PR 并 do paired session with customer ops 一起 review, 重要 release 给 1-page summary + 风险评估. 短期: 我们 SRE 在 customer 监控下 apply. 长期: customer 招 SRE / 培训.

2. **"如果我们的 SRE 团队的某个人离职带走 Cosign 私钥, 怎么办?"** — 答: Cosign 配 keyless signing (Fulcio + OIDC), 不用 long-lived key. 我们 build pipeline 用 GitHub OIDC token → Fulcio 签发短 key, sig 写 transparent log (Rekor). 私钥永不持久化. 即使 SRE 离职, 也无法 forge signature.

3. **"客户安全队问'你们 SRE 看不到我们数据, 但 incident 时怎么 debug?'"** — 答: Break-glass cross-account role + Teleport 录屏 + customer 旁观. 流程: customer 主动开 ticket, 我们 SRE request access, customer DPO 批 (Slack approval), 限时 4h, 所有 session 录屏 + audit log 进 customer S3. 4h 后自动 revoke. 我们事后写 RCA 给 customer.

4. **"50 个客户里 1 个 stuck 在 v1.2, 不愿升级到 v2.x, 怎么办?"** — 答: LTS 通道为这类客户存在, v1.x.y backport critical security fix 18 个月. 之外 new feature 不 backport. 沟通: 跟 customer success 一起说服升级, 给 migration playbook + 我们 SRE 协助. 极端情况: 维护 v1 LTS 是 $50K/year extra contractual.

5. **"客户用 Okta 但他们 IT 不给我们 Okta 管理员权限, 怎么 setup app?"** — 答: 我们提供 Okta integration template (manifest YAML / IdP-side config doc), customer Okta admin 自己 setup. 我们 RP side 配 issuer/client_id/jwks 即可. 不要求我们直接管 Okta. 同时 SCIM 是 nice-to-have, 不强求.

---

## ❌ 死路答法

1. **"我们做 SaaS, customer 走 our endpoint"** — F500 拒绝, 直接挂.
2. **"用 Terraform 自动 push update"** — 客户不让, customer-controlled apply 是命门.
3. **"Okta + 我们自己 RBAC 系统"** — 重复, 维护爆炸. 直接用 Okta group claim.
4. **"Snowflake JDBC password auth"** — F500 拒绝, key-pair 或 External OAuth.
5. **"telemetry 直接 push 回我们 SRE"** — 数据出 customer network, 拒绝.
6. **"NAT GW + 公网 egress"** — F500 拒绝, 必须 VPC endpoint + PrivateLink.
7. **"每个 release 都过 6 周 SecRev"** — 一年 release 8 次, 不可行. 必须设计 update mechanism.
8. **"OpenAI API + 公网"** — 客户拒绝 (PHI / 数据). 用 Bedrock + PrivateLink.
9. **"50 customer 同一 git branch"** — variability 处理不了, Helm values per-customer 是正解.
10. **"customer 想 customize code 我们就 fork"** — 维护爆炸, 用 plugin / hook / values 解决.

---

## ✅ 加分项

1. **Customer 主账号 + cross-account role** — 立刻 signal 你做过真 F500 deploy
2. **Two-stage IaC (Terraform infra + Helm app)** + Architecture Stability Contract — 6-week SecRev 减压设计真厉害
3. **Cosign + Kyverno admission** — modern supply chain security
4. **GitOps + customer-controlled apply** — 客户 trust model 正确
5. **External OAuth + key-pair 混合** — user-attributed + service 都 cover
6. **OTel metrics-only egress** — 不贪 telemetry
7. **Release channels (dev/beta/stable/lts)** — 真懂 enterprise SaaS 节奏
8. **SBOM diff + audit-ready evidence package** — security review 减压创新
9. **Break-glass role + Teleport 录屏** — incident response 设计完整
10. **Fleet config GitOps + per-customer Helm values** — 50 客户 scale 思路

---

## 一句话总结

F500 VPC 部署不是 "把 SaaS 改 self-host", 是 **customer-owned AWS account + Terraform infra (锁定, 不重审) + Helm app (通过 Argo GitOps + Cosign 签名通道更新) + Okta OIDC + Snowflake PrivateLink + OTel metrics-only egress + per-customer git repo + LTS/stable/beta channel** 一整套 enterprise SaaS-as-self-host 模型.

---

## Cheat Sheet

```
Deploy: Customer AWS account, cross-account role (4h break-glass only)
Infra:  Terraform (锁定, SecRev 6w 一次), VPC + EKS + RDS + VPC endpoints
App:    Helm chart, Argo CD GitOps, customer ops apply
Image:  Cosign signed, Kyverno verify, customer ECR (replicated from ours)

Auth:
  User → app:        Okta OIDC (PKCE), JWT, group claim → role
  App → Snowflake:   Key-pair RSA (service) + External OAuth (user query)
  Snowflake link:    AWS PrivateLink, customer-VPC only

Update channels:
  dev:    我们 SRE 内部
  beta:   1-2 customer, 2 weeks observation
  stable: 90% customer, 4 weeks observation
  lts:    big保守 F500, 8 weeks observation

Architecture Stability Contract:
  - VPC topology 不变
  - IAM 不放权
  - Egress allowlist 不变
  - Image hash diff = no re-review
  - 6-week SecRev 只在 infra change 触发

Telemetry:
  Default:  OTel metrics only, exporter to customer Datadog/Splunk
  No raw:   user query / PII never egress
  Our view: daily summary JSON push to our S3, fleet dashboard

Cost (1 F500):
  Infra:    $13K/month
  SRE:      $16K/customer/yr (fleet of 50)
  Sell:     $300K/yr (gross margin 43%)

Fleet (50):
  ARR:      $13.75M
  GitOps:   per-customer repo + fleet-config repo
  Onboard:  8 weeks (6 SecRev + 2 install)

Emergency:
  CVE ≥ 9.0 → 4h hotfix image → 24h customer-deployed
```
