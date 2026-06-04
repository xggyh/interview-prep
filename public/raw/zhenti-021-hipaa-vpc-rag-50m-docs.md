## Q21 · HIPAA + 5000 万文档医疗 RAG 系统

> "Design a RAG system over **50 million clinical documents** for a hospital network. Must be **HIPAA compliant**, deployed in customer VPC, integrate with their **Epic / Cerner EHR**. Doctor asks 'what's the latest on this patient's diabetes treatment plan'. Answer must cite sources. **No PHI can leak to public LLM APIs.**"

**中文翻译**:

> "为一个医院网络设计一套覆盖 **5000 万份临床文档**的 RAG (检索增强生成) 系统. 必须满足 **HIPAA 合规** (美国医疗数据隐私法), 部署在客户的 VPC (虚拟私有云) 内, 集成他们的 **Epic / Cerner EHR** (电子病历系统). 医生提问 '这个病人糖尿病治疗方案最新进展是什么'. 答案必须给出 citation (引用出处). **PHI (受保护医疗信息) 一丝都不能泄露到公网 LLM API.**"

**Round**: System Design (60 min)
**出处**: Exponent 2026 FDE · 公司: Anthropic / Palantir Foundry Health / Hippocratic AI · 行业: healthcare (provider network)
**约束**: HIPAA / BAA / PHI redaction / VPC-only deploy / encrypted at rest + in transit / immutable audit / RBAC tied to hospital IdP / no public LLM API egress

---

## 📖 术语速查 (本题用到的)

> 这题里的合规 + 架构词如果不懂, 后面架构图听不下去. 这张表 5 min 看完.

### 合规 / 行业 (HIPAA 体系)

| 术语 | 解释 |
|---|---|
| **HIPAA** ⭐ | Health Insurance Portability and Accountability Act — 美国医疗数据隐私法. 违反 = OCR (Office for Civil Rights) 罚款 + 客户走人. |
| **PHI (Protected Health Information)** ⭐ | 受保护医疗信息 — 任何能识别到病人 + 涉及健康的数据. 18 类直接标识符 (name, MRN, SSN, DOB...) + 准标识符组合. |
| **PII** | Personally Identifiable Information — 通用个人信息. PHI ⊂ 医疗领域的 PII. |
| **BAA (Business Associate Agreement)** ⭐ | 业务伙伴协议 — HIPAA 要求所有接触 PHI 的供应商 (你 / Anthropic / AWS) 必须签的法律合同. 没 BAA = 直接违规. |
| **OCR / HHS** | OCR = Office for Civil Rights, 隶属 HHS (卫生部) — 真的来查 HIPAA 违规的执法机构. |
| **HITRUST CSF** | 医疗行业的安全合规框架 — 比 SOC 2 更医疗-specific 的认证. |
| **PCI / GLBA** | PCI = 信用卡数据合规; GLBA = 金融数据隐私法. 医疗系统也常涉及. |
| **Joint Commission** | 美国医院认证组织 — 它的 audit retention 要求 10 年, 比 HIPAA 6 年更严. |
| **k-anonymity** | 数据去识别度量 — 准标识符组合 (rare diagnosis + zip + DOB) 在数据集中至少有 k 个一样的人. k < 5 = 仍可识别个体. |
| **Right to Erasure** | 病人有权要求删除自己的记录. HIPAA / GDPR / 州法都有不同版本. 删 metadata 不够, **embedding vector 也得删**. |
| **MRN** | Medical Record Number — 病历号. 每家医院给 patient 的内部 ID. PHI 第一类. |
| **SOAP note** | 临床笔记标准格式: Subjective (主诉) / Objective (体征) / Assessment (诊断) / Plan (治疗计划). |
| **ICD code** | International Classification of Diseases — 国际疾病分类码 (e.g. E11.9 = type 2 diabetes). 索引重要 keyword. |

### EHR / 医疗集成

| 术语 | 解释 |
|---|---|
| **EHR / EMR** | Electronic Health Record / Medical Record — 电子病历系统. Epic / Cerner 是两大头部供应商. |
| **Epic** | 美国市占率最高的 EHR 系统 (~40% 大医院). 私有协议 + SMART-on-FHIR + Hyperspace UI. |
| **Cerner** | 另一头部 EHR, 现属 Oracle. 主走 HL7v2 协议. |
| **Meditech / Allscripts / Athena** | 其他 EHR 供应商, 小医院常用. |
| **FHIR (Fast Healthcare Interoperability Resources)** ⭐ | 现代医疗数据标准, JSON-based, RESTful API. R4 / R5 是版本. |
| **HL7v2** | 老一代医疗消息标准, pipe-delimited 文本格式. 还在大量用. |
| **CCD / CCDA** | Continuity of Care Document — XML 格式的病人摘要交换标准. |
| **SMART-on-FHIR** | 在 FHIR 上的 OAuth + app 嵌入框架. 医生在 Epic 里直接打开第三方 app. |
| **DICOM** | 影像数据标准 (X 光 / CT / MRI). |
| **PACS** | Picture Archiving and Communication System — 医院影像存储系统. |
| **Mirth Connect** | 开源 HL7 集成引擎, 经常用于 Cerner 集成. |
| **ADT / ORU / MDM** | HL7 消息类型: ADT = 病人入院出院; ORU = 检验结果; MDM = 临床文档. |
| **CDC (Change Data Capture)** | 增量数据同步模式 — 只传变更, 不重传全量. |

### LLM / RAG 架构

| 术语 | 解释 |
|---|---|
| **RAG (Retrieval-Augmented Generation)** ⭐ | 检索增强生成 — 先从文档库里 retrieve 相关片段, 再让 LLM 基于片段生成答案. |
| **Embedding** | 把文本变成 1024 维向量, 语义近的向量距离近. |
| **BGE-M3** | 开源中英多语 embedding 模型, 自部署友好. M3 = multi-functionality + multi-linguality + multi-granularity. |
| **HNSW (Hierarchical Navigable Small World)** | 向量近似最近邻算法. M=32 是连接数, ef=128 是搜索宽度. |
| **K-NN search** | K 个最近邻搜索 — 向量库的核心 API. |
| **BM25** | 经典 keyword 检索算法 (TF-IDF 变种). 关键词精确匹配强. |
| **Hybrid retrieval** ⭐ | 向量 + BM25 双路并行召回, 用 RRF 融合. 医疗这种 keyword-heavy 场景必备. |
| **RRF (Reciprocal Rank Fusion)** | 排名倒数融合 — 不需要 score normalize, 按 rank 倒数求和. |
| **Cross-encoder rerank** | 用更贵的双向交叉模型对 top-100 重排出 top-10. 比 bi-encoder 准但慢. |
| **Bi-encoder** | query 和 doc 分别 encode 再求相似度. 快但不如 cross-encoder 准. |
| **nDCG@10** | normalized Discounted Cumulative Gain — top-10 检索质量指标, 越高越好. |
| **Citation faithfulness** | 引用忠实度 — LLM 答案里每个 claim 必须真的来自引用的 source span. |
| **NLI (Natural Language Inference)** | 蕴含判断模型 — 判断 premise 是否蕴含 hypothesis. 用于 citation 验证. |
| **Hallucination** | LLM 编造没有依据的内容. 在医疗 = patient harm. |
| **vLLM / TensorRT-LLM** | 高吞吐 LLM 推理引擎. PagedAttention + continuous batching. |
| **Med-PaLM 2 / Hippocratic 1.5** | 医疗领域专门 fine-tune 的 LLM. |
| **Vertex AI** | AWS 托管的 LLM 服务. 支持 in-VPC + BAA 部署 Claude. |

### 基础设施 / 部署

| 术语 | 解释 |
|---|---|
| **VPC (Virtual Private Cloud)** ⭐ | AWS 私有网络. "Deploy in customer VPC" = 装在客户自己的 AWS 账户里, 完全不出他们网络. |
| **VPC endpoint** | VPC 内调 AWS 服务的私网入口, 不走公网 IGW. |
| **IGW / NAT** | Internet Gateway / NAT — VPC 出公网的两种方式. HIPAA 部署里都禁用. |
| **KMS-CMK** | AWS Key Management Service - Customer Managed Key. 用户自管的加密主密钥. |
| **CloudHSM** | AWS 硬件安全模块 (FIPS 140-2 L3). 比 KMS 更高合规要求时用. |
| **Envelope encryption** | 信封加密 — data key 加密数据, master key 加密 data key. 应用层不持有 master key. |
| **GCS Object Lock / WORM** | Write Once Read Many — 写入后不可改不可删. HIPAA audit 必备. |
| **Vertex AI Vector Search** | AWS 托管的 ElasticSearch fork. 原生支持 K-NN + BM25 hybrid. |
| **Aurora Postgres + RLS** | Aurora = AWS 托管 Postgres; RLS = Row-Level Security 行级安全策略. |
| **Firestore / Bigtable** | AWS 托管 NoSQL kv 存储. |
| **MSK** | Managed Streaming for Kafka — AWS 托管 Kafka. |
| **Pub/Sub** | AWS 流处理服务, 类似 Kafka. |
| **Dagster** | 数据 pipeline 编排工具 (类似 Airflow). |
| **Cloud Audit Logs** | AWS 自带的 API 调用 audit 日志. 只 cover AWS API, 不 cover 应用层. |
| **ACM Private CA** | AWS 私有证书颁发机构, 用于内部 mTLS. |
| **Linkerd / Istio** | Service mesh — 服务间 mTLS + observability. |
| **Teleport** | 带审计录像的远程接入跳板机, 客户支持隧道用. |

### Auth / 访问控制

| 术语 | 解释 |
|---|---|
| **ACL (Access Control List)** ⭐ | 访问控制列表 — 哪个用户可访问哪些 doc. 这题 5K doctor × 1M patient. |
| **RBAC (Role-Based Access Control)** | 基于角色的访问控制 (department, specialty). Cardinality 低时用. |
| **ABAC (Attribute-Based)** | 基于属性的访问控制. 比 RBAC 更细. |
| **Pre-filter vs Post-filter** ⭐ | 检索前过滤 vs 检索后过滤. HIPAA "minimum necessary" 要求 pre-filter — 不该看见的连见都不能见到. |
| **Care team** | 病人的主治团队列表. ACL 主键来源. |
| **Break-glass access** | 紧急情况 (ED / ICU) 越权访问 + 强制事后审计. |
| **SAML / OIDC** | 企业级身份联合协议. SAML 老但广泛, OIDC 现代基于 OAuth. |
| **IdP (Identity Provider)** | 身份提供者 — 客户的 Active Directory / Okta. |
| **MFA / Step-up MFA** | 多因子认证 / 敏感操作时再要一次 MFA. |
| **JWT (JSON Web Token)** | 自包含的认证 token, 服务间常用. |

### 观测 / 运维

| 术语 | 解释 |
|---|---|
| **SLA / SLO** | Service Level Agreement (对外承诺) / Objective (内部目标). |
| **p50 / p99** | 50% / 99% 分位的延迟. p99 = 1% 慢请求的延迟. |
| **RPO / RTO** | Recovery Point Objective (能丢多少数据) / Recovery Time Objective (多久能恢复). |
| **Blue/green deploy** | 蓝绿部署 — v1 / v2 双跑, 切流量过去, 老版本兜底. |
| **Snyk / ECR scan** | 容器镜像漏洞扫描. |
| **CVE** | Common Vulnerabilities and Exposures — 公开的安全漏洞编号. |
| **Pen test** | 渗透测试 — 雇白帽子尝试攻破系统. |
| **DLQ (Dead Letter Queue)** | 处理失败的消息进的队列, 待人工处理. |

---

## 这道题在考什么

不是考你会不会做 RAG, 是考你**在合规约束 + 50M scale 下做 RAG**, 哪些地方会爆炸:

1. **PHI 不能出 VPC** — 90% 的候选人答出 "用 OpenAI embedding API" 直接挂. 必须 self-host (Voyage-3-medical or BGE-M3 in VPC).
2. **50M docs ≠ 1M docs** — 索引大小 / shard 策略 / 重建窗口 完全不同, 不能简单一句 "用 pgvector"
3. **PHI redaction at ingestion** — 不是 query 时, 是 ingestion 时. 用 Presidio + 自定义 medical NER (因为标准 PII detector 漏掉 ICD codes, lab values, drug names + dosage 这些隐式标识)
4. **Audit trail is the product** — HIPAA 要求每次 access PHI 都 immutable log, 这是 OCR audit 的命门
5. **Per-tenant RBAC** — 大型 hospital network = 50 hospitals + 5000 doctors + 100 departments, 每个 doctor 只能看自己 attending 过的 patient
6. **EHR integration** — Epic FHIR API vs Cerner HL7v2, 不是 file dump 而是 live sync (with CDC + deletion propagation under "right to erasure")
7. **Hallucination is patient harm** — citation must be exact span, "confidence" 是 board-level concern
8. **菜鸟答案失败点**: "I'd use OpenAI embeddings, Vertex AI Vector Search, GPT-5.5" — 三个全部违反 HIPAA. 即使 Vertex AI Vector Search 有 BAA, PHI 出 VPC 仍是问题. 即使 OpenAI 有企业 BAA, 大部分 hospital legal 团队不接受.

---

## 必问 clarifying questions

1. **PHI envelope**: 是 PHI 全文 (notes 含 patient name) 还是 de-identified analytics 库? 直接决定要不要 PHI redaction stage
2. **EHR vendor**: Epic / Cerner / Meditech / Athena? 决定 connector + sync protocol (Epic = FHIR R4, Cerner = HL7v2 + CCD)
3. **Latency SLA**: doctor 在 exam room 问 → 答案要 < 3s 还是 < 30s? 决定 model size + cascade
4. **Read or read+write**: agent 是只回答 还是可以 update problem list / order labs? 后者需要 dual-confirmation + write audit
5. **Cardinality of access control**: 5K doctor × 1M patient = 5B 行 ACL 还是 role-based (specialty × department)? 影响 retrieval filter strategy
6. **Volume growth**: 50M static 还是 +10K/day inflow? CDC pipeline 必要性
7. **Self-host LLM acceptable**: 用 Med-PaLM 2 / Hippocratic 1.5 self-host 还是 Anthropic BAA-covered Claude? 决定推理 stack
8. **Audit retention**: HIPAA 6 年 vs joint commission 10 年, 影响 audit storage 成本

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|------|------|------|
| 1 | Clarify | 5 min | 锁 PHI 范围 + EHR + RBAC + SLA | "Before architecture, three things I must lock — PHI envelope, EHR vendor, RBAC granularity" |
| 2 | Compliance frame | 4 min | HIPAA Tech Safeguards 5 条 → 映射组件 | "HIPAA Tech Safeguards: access control, audit, integrity, transmission security, encryption — let me map each to a component" |
| 3 | Ingestion architecture | 10 min | EHR connector → PHI redact → chunk → embed → store | "Ingestion is where compliance starts. PHI redaction at ingest, not at query." |
| 4 | Retrieval architecture | 10 min | Query → ACL filter → hybrid retrieval → rerank | "Retrieval has ACL as L1 filter, then HNSW + BM25 hybrid, then cross-encoder rerank." |
| 5 | Generation + grounding | 8 min | VPC-internal LLM + citation enforcement | "Self-host Claude or Med-PaLM via BAA. Citation token-span level." |
| 6 | Audit + observability | 8 min | Every PHI access logged, immutable | "Every read of PHI is an event in immutable audit. Cloud Audit Logs-equivalent." |
| 7 | Production hardening | 8 min | Key rotation / DR / patching / pen test | "BAA 是 contract, prod hardening 是 operationalization." |
| 8 | Trade-offs + close | 7 min | Self-host LLM vs BAA cloud / index strategy / cost | "If you give me 100K/month, I'd self-host. If 30K, I'd push Anthropic BAA." |

---

## 端到端架构图 (ASCII)

```
                      Hospital Network VPC (us-east-1, customer AWS account)
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                           │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────────────────┐   │
│   │ Epic FHIR    │    │ Cerner HL7v2 │    │ Department EMR exports (SFTP / Parquet)  │   │
│   │ Patient API  │    │ Mirth Connect│    │ Radiology PACS dump (DICOM metadata)     │   │
│   └──────┬───────┘    └──────┬───────┘    └────────────────────┬─────────────────────┘   │
│          │ FHIR R4 CDC       │ HL7 ADT/ORU/MDM stream          │ Daily 4am file drop      │
│          ▼                   ▼                                  ▼                         │
│   ┌─────────────────────────────────────────────────────────────────────────────┐         │
│   │   Ingestion Pipeline  (Dagster · runs in VPC, no public egress allowed)     │         │
│   │                                                                             │         │
│   │   [1] Normalize: FHIR → canonical clinical_note schema (Pydantic)           │         │
│   │   [2] PHI Redact: Presidio + medspaCy + custom medical NER                  │         │
│   │       - direct identifiers (name, MRN, SSN) → `<PHI_NAME_a3f2>`             │         │
│   │       - quasi-identifiers (rare diagnosis + zip5 + DOB) → flagged           │         │
│   │       - redaction map stored in encrypted key-value store (KMS-CMK)         │         │
│   │   [3] Chunk: 512 tokens, semantic boundary (section header aware)           │         │
│   │   [4] Embed: BGE-M3 medical fine-tune (self-host on g5.xlarge, batched)     │         │
│   │   [5] ACL extract: who can read this doc → ACL bitmap rows                  │         │
│   │   [6] Write: vectors → Vertex AI Vector Search K-NN | full text → Vertex AI Vector Search BM25        │         │
│   │             metadata → Postgres (with row-level security)                   │         │
│   │             ACL bitmap → Redis (per-patient)                                │         │
│   │   [7] Audit event: ingest.complete{doc_id, hash, ts, who}                   │         │
│   └─────────────────────────────────────────────────────────────────────────────┘         │
│                                                                                           │
│   ┌──────────────────────────────────────────────────────────────────────────────┐        │
│   │  Storage tier (all KMS-CMK + GCS Object Lock / immutable)                     │        │
│   │  ─ Vector store: Vertex AI Vector Search K-NN (HNSW, M=32, ef=128)  · 50M × 1024D ≈ 200GB │        │
│   │  ─ BM25 index : Vertex AI Vector Search full text                   · ≈ 250GB             │        │
│   │  ─ Metadata   : Aurora Postgres (RLS on)               · 50M rows ≈ 80GB     │        │
│   │  ─ PHI redact : Firestore / Bigtable encrypted (per-doc map)       · 50M rows ≈ 30GB     │        │
│   │  ─ Audit log  : GCS Object Lock + Cloud Audit Logs            · WORM 6 yrs          │        │
│   └──────────────────────────────────────────────────────────────────────────────┘        │
│                                                                                           │
│   ┌──────────────────────────────────────────────────────────────────────────────┐        │
│   │   Query Path  (doctor types in Epic side-panel / Hyperspace SMART-on-FHIR)   │        │
│   │                                                                              │        │
│   │   Hospital IdP (Active Directory) → SAML → API Gateway → Bearer token        │        │
│   │     ▼                                                                        │        │
│   │   [Q1] Query rewrite (Med-PaLM 2 self-host or Claude Sonnet 4.6 via BAA)     │        │
│   │   [Q2] ACL resolve: which patient/department doctor can read                 │        │
│   │   [Q3] Hybrid retrieval: HNSW top-100 ∪ BM25 top-100 (post-ACL filter)       │        │
│   │   [Q4] Cross-encoder rerank (BGE-reranker-v2-m3, self-host) → top-10         │        │
│   │   [Q5] Generation: VPC LLM with [retrieved_chunks] + citation enforcement    │        │
│   │   [Q6] Citation verify: every claim must point to chunk_id + token span      │        │
│   │   [Q7] Audit emit: query.complete{doctor, patient_ids, doc_ids, ts, latency} │        │
│   └──────────────────────────────────────────────────────────────────────────────┘        │
│                                                                                           │
│   ┌──────────────────────────────────────────────────────────────────────────────┐        │
│   │   LLM tier (none of these touch public internet)                             │        │
│   │   ─ Anthropic Claude Sonnet 4.6 via Vertex AI-in-VPC + BAA  (preferred)        │        │
│   │   ─ OR Med-PaLM 2 / Llama-3 medical fine-tune on vLLM (g5.12xlarge × 4)      │        │
│   │   ─ Embedding: BGE-M3-medical (self-host always)                             │        │
│   │   ─ Reranker : BGE-reranker-v2-m3 (self-host)                                │        │
│   └──────────────────────────────────────────────────────────────────────────────┘        │
│                                                                                           │
└──────────────────────────────────────────────────────────────────────────────────────────┘

         External (outside customer VPC) — control plane only, NO PHI ever
         ─ Terraform state (GCS, encrypted, our account, no data refs)
         ─ Eval golden set (synthetic, no real PHI)
         ─ Customer support tunnel (Teleport, audit-recorded sessions)
```

---

## 详细设计 (60-min walkthrough)

### Phase 1: Clarify + KPI (澄清 + 锁 KPI) (5 min)

开口先把红线说出来, 让面试官知道你不会闷头答:

"医疗 RAG 三件事必须先锁: **PHI 是不是会出 VPC** (90% 是 no), **EHR 是 Epic 还是 Cerner** (决定 connector), **doctor 问完到拿答案的 SLA** (3s 还是 30s 决定 model 选型). 我假设 PHI 不能出 VPC, EHR 是 Epic FHIR R4, p50 latency 3s, p99 8s."

KPI 给三条:
- **Retrieval quality**: nDCG@10 ≥ 0.75 on golden set (1000 clinical questions, annotated by attending physicians)
- **Citation faithfulness**: ≥ 95% claims have correct source span (LLM-as-judge + 5% human review)
- **Compliance**: 0 PHI in audit log, 0 LLM API external calls, 100% access logged

明确说不答的事情: **不是问 "doctor 应该开什么药"** (这是 clinical decision support, regulated as medical device, FDA Class II). 是问 "patient 历史里关于 diabetes 的相关记录是什么", 让 doctor 自己合成判断.

### Phase 2: HIPAA Tech Safeguards (技术保护措施) 5 条 → 组件映射 (4 min)

这一步是 staff-level 的标志. 不要先讲架构, 先讲合规如何 driving 架构:

| HIPAA 45 CFR § 164.312 | 我的组件 |
|---|---|
| (a) Access Control | Hospital IdP (SAML) + Aurora RLS + ACL bitmap in Redis |
| (b) Audit Controls | Cloud Audit Logs + 应用层 audit emitter → GCS Object Lock (WORM) |
| (c) Integrity | KMS-CMK encryption + GCS versioning + checksum on every chunk |
| (d) Person/Entity Auth | OIDC + step-up MFA on PHI-sensitive operations |
| (e) Transmission Security | TLS 1.3 everywhere, VPC endpoints (not public IGW), mTLS service-to-service |

加一条 Administrative Safeguard 必谈的: **BAA (Business Associate Agreement)** — 你和客户要签, 你和 Anthropic (如果用) 要签. 任何 sub-processor (vector DB / embedding API / monitoring tool) 都要在 BAA chain 里, 否则违规.

### Phase 3: Data path deep dive — Ingestion (数据通路深度剖析 - 摄取阶段) (10 min)

50M docs 不是一次性的, 是 backfill + ongoing. 拆 3 步讲.

**Step 3.1 EHR connector (Epic FHIR)**

```
Epic SMART-on-FHIR Backend Services
  ├─ JWT signed assertion (RS384) → access token
  ├─ Subscribe to:
  │    ├─ DocumentReference (clinical notes)
  │    ├─ Observation (labs)
  │    ├─ Condition (problem list)
  │    └─ MedicationRequest (orders)
  ├─ Bulk Export ($export) for backfill — NDJSON output, GCS sink
  └─ Subscription R5 for delta (CDC) — server pushes new resources
```

Backfill 50M docs 经过的时间:
- Epic bulk export rate limit: ~100 docs/sec
- 50M / 100/s = 500K sec = ~6 days continuous
- 实际加上 throttle / off-hours = 14 天 backfill window

Delta load: Epic Subscription R5 推送, 平均 30K events/day, 峰值 200K/day (查房后批量更新), 设计成 Kafka-like (用 MSK), Dagster 消费.

**Step 3.2 PHI redaction (核心)**

不能用 OpenAI Moderation API (违反 PHI 出 VPC). 必须 self-host. 三层 detector:

| Layer | 检测什么 | 工具 | False negative concern |
|---|---|---|---|
| L1 Rule | MRN, SSN, phone, email, DOB | regex + Stanford NER | 拼写错 / OCR 错 → 漏 |
| L2 ML | name, address, hospital name, provider name | Presidio + medspaCy `en_core_med7_lg` | 罕见姓氏 / 外国名漏检 |
| L3 Custom | implicit identifiers: rare ICD + zip + DOB combo | 自训练 BERT classifier 在 PhysioNet i2b2 数据上 fine-tune | 推理时延 + 误报率 |

Redaction map 设计:
```python
{
  "doc_id": "fhir-DocRef-7af2",
  "original_hash": "sha256:...",   # for integrity
  "tokens_redacted": [
    {"span": [42, 51], "type": "NAME", "key": "<PHI_NAME_a3f2>"},
    {"span": [108, 116], "type": "MRN", "key": "<PHI_MRN_b7d9>"},
  ],
  "redaction_key_kms_id": "arn:aws:kms:...:key/medical-redact"
}
```

Reversible: 只有 break-glass scenarios (e.g. court subpoena) 才解 PHI, 需要 2-person approval + audit event. 99.9% 的 retrieval / generation 都对 redacted 版本做.

Quasi-identifier 风险: rare diagnosis (基因病) + 5-digit zip + DOB 三件套, k-anonymity < 5 时直接拒绝索引该文档, 走人工审核队列.

**Step 3.3 Chunking + Embedding**

Chunk size: 512 token semantic chunks. 不要固定 512, 用 section-aware:
- SOAP note: 每个 Section (Subjective / Objective / Assessment / Plan) 单独 chunk
- Pathology report: 按 specimen 分
- Lab panel: 一组 lab values 一个 chunk

为什么不要 fixed 256 / 1024: 医疗文档语义边界强, 跨边界 chunk 会把 "Assessment" 和 "Plan" 撕开, 查 "treatment plan for diabetes" 时 retrieval miss.

Embedding model: **BGE-M3 medical fine-tune** (self-host on g5.xlarge GPU). 不是 OpenAI text-embedding-3-large (违反). 不是裸 BGE-M3 (医学领域适配不够).

Throughput: g5.xlarge × 8 (batch 64) → ~5K embeddings/sec → 50M docs ÷ 5K = 10K sec = 3 hours backfill embedding. 加上 chunking (CPU bound, Ray cluster) 总 ingest 时间 5-7 天 (含 PHI redact 的 GPU).

### Phase 4: Data path deep dive — Retrieval & Generation (检索 + 生成) (15 min)

**ACL 必须在 retrieval 之前**, 不能 post-filter.

为什么: post-filter 会让 LLM "看见过" 不能看的 doc, 这违反 HIPAA "minimum necessary" 原则. 实现:

```python
# Pre-filter: build doc_id whitelist BEFORE vector search
def resolve_acl(doctor_id, query_context):
    # query_context 可能包含 patient_id (从 Epic SMART context 拿)
    direct_patients = db.query("""
      SELECT patient_id FROM care_team WHERE provider_id = $1 AND active = true
    """, doctor_id)  
    
    department = db.query("SELECT department_id FROM providers WHERE id = $1", doctor_id)
    if department in ["ED", "ICU"]:
        # break-glass — emergency access to full record, with mandatory after-action audit
        return ALL_PATIENTS_FLAG
    
    return set(direct_patients)

allowed_patients = resolve_acl(doctor_id, ctx)
# Vertex AI Vector Search K-NN with pre-filter
results = opensearch.knn_search(
    query_vector=q_emb,
    k=100,
    filter={"terms": {"patient_id": list(allowed_patients)}}
)
```

**Hybrid retrieval**: HNSW + BM25 因为医疗 query 多 keyword (drug name, ICD code) 同时也 semantic (treatment plan 同义改写).

```
query "diabetes treatment plan latest"
  ├─ HNSW: 100 chunks (semantic)  → 25 unique docs
  ├─ BM25: 100 chunks (keyword "diabetes" "treatment" "plan") → 30 unique docs
  └─ RRF fusion (rank reciprocal): top 50 → cross-encoder rerank → top 10
```

为什么 RRF 不用 weighted sum: RRF 不需要 score normalization, score scale 在 BM25/HNSW 之间完全不同.

**Reranker**: BGE-reranker-v2-m3 cross-encoder, self-host on g5.xlarge.
- Pairwise score (query, chunk) → 0-1
- batch 32 → ~50ms / 10 candidates → 50ms latency

**Generation (VPC LLM)**:

两个可行 path, 给面试官 trade-off:

| Option | Pros | Cons | Cost |
|---|---|---|---|
| Anthropic Claude Sonnet 4.6 via Vertex AI + BAA | 质量最强, no infra to manage | 必须信 Vertex AI isolation | $3/$15 per 1M tokens |
| Med-PaLM 2 / Llama-3-medical self-host on vLLM | 完全 in-VPC, lower per-query cost | 维护 6 张 H100, eval lag | infra ~$80K/year |

我推荐: **Sonnet 4.6 via Vertex AI + BAA** 作为 Phase 1 (6 个月内上线), self-host 作为 Phase 2 (cost 优化). 因为 hospital legal 团队对 AWS BAA 接受度已经较高 (2025-2026 普及), 而维护 self-host LLM 是另一个 fulltime 团队的活.

**Citation enforcement**:

LLM 输出必须带 [chunk_id:token_span] 标记, post-process 验证:

```python
def verify_citations(answer_md, retrieved_chunks):
    citations = parse_citations(answer_md)  # [(claim_idx, chunk_id, span), ...]
    for claim_idx, chunk_id, span in citations:
        chunk = retrieved_chunks[chunk_id]
        cited_text = chunk.text[span[0]:span[1]]
        claim_text = extract_claim(answer_md, claim_idx)
        
        # NLI check: does cited_text entail claim_text?
        entailment = nli_model(premise=cited_text, hypothesis=claim_text)
        if entailment < 0.8:
            log_unfaithful_claim(claim_idx, chunk_id, claim_text, cited_text)
            answer_md = mark_low_confidence(answer_md, claim_idx)
    return answer_md
```

如果 unfaithful 率 > 10%, 整个回答 fall back 到 "I have these source documents — let me show them to you" + 显示 retrieval chunks 让 doctor 自己判断.

### Phase 5: Control / failure / consistency (控制面 / 故障 / 一致性) (15 min)

**5.1 EHR sync consistency**

Epic Subscription R5 不保证 exactly-once. 我们的接收处理:
- Idempotency key = `resource_type:fhir_id:version_id`
- Watermark in Postgres: 每个 resource type 一个 high-water mark
- Conflict resolution: last-writer-wins by `meta.lastUpdated`, 老版本进 history table
- Deletion propagation: 收到 `DocumentReference` resource 的 `status: superseded` 或者 `entered-in-error`, 在 vector store 标 deleted=true, 索引一周后物理 GC

**5.2 Index rebuild strategy**

50M docs 重建一次 HNSW 索引:
- BGE-M3 1024D × 50M = 200GB raw vectors
- HNSW with M=32: 内存约 1.5× raw = 300GB → 不能塞单机
- 拆 shard: 按 patient_id hash → 16 shards, 每 shard ~20GB → r6i.4xlarge × 16
- 重建窗口: 全量重建需 ~24h, 每 shard 并行, 在线服务用 blue/green

**5.3 PHI redaction errors**

False negative (漏掉 PHI) > false positive. 我们的 backstop:
- Daily sample 100 docs by random shard, human reviewer (HIPAA-trained) 走全文核查
- 任何漏检立刻进 detector retraining queue
- 同时在 LLM generation 后跑一层 **PHI scrubber**: 如果 generation 里出现像 MRN 格式的 token, 强制 redact (defense in depth)

**5.4 EHR vendor outage**

Epic outage 2-4 小时是常态 (尤其 Tuesday 升级窗口). 系统不能崩:
- Subscription 断线 → exponential backoff reconnect
- Backlog buffer in Kafka (MSK) 保 24h
- 我们的 query 仍能服务: 因为是 read-side cache, Epic 在线与否不影响 retrieval
- 但 patient data freshness 落后, UI 显示 "data current as of HH:MM, 5 min ago"

**5.5 Right to Erasure / Restriction Request (HIPAA + state law)**

Patient 请求 restrict某医生 access 或 撤回某条记录:
- 收到 restriction event → 更新 ACL bitmap (强制 cache 失效)
- 撤回某 doc: 软删除 + 30 天 grace (因为 audit 反查), 然后物理 GC
- 关键: **embedding vector 也要删** — 不能只删 metadata, vector 留着. 实际操作: 在 Vertex AI Vector Search 里 `_delete_by_query`, async confirm

### Phase 6: Production hardening (生产硬化) (10 min)

**6.1 Key management**:
- Per-tenant CMK (Customer Master Key) in KMS
- KMS automatic rotation every 365 days
- envelope encryption: data key 加密 doc, master key 加密 data key
- 应用层永不持有 master key plaintext, KMS Decrypt API call

**6.2 Networking**:
- VPC endpoints (Interface) for GCS / Firestore / Bigtable / KMS / Vertex AI — NO IGW, NO NAT
- 私网 only, even outbound update apt/yum 都要走 customer-approved mirror
- TLS 1.3 mandatory, certificate via ACM Private CA
- Service mesh: linkerd / istio for mTLS pod-to-pod

**6.3 Patching**:
- ECR scan + Snyk on every build
- Critical CVE → 24h patch SLA (HIPAA risk assessment 必备)
- AMI immutable, rebuild not patch-in-place

**6.4 Disaster Recovery**:
- RPO 15 min (GCS cross-region replication for audit + vector store)
- RTO 4 hour (warm standby in another AZ, cold in another region)
- Tabletop DR drill 每季度, audit log 验证 chain of custody not broken

**6.5 Pen testing + audit**:
- HITRUST CSF self-assessment ↔ SOC 2 Type II annual audit
- 外部 pen test (Bishop Fox / NCC Group) 半年一次
- HIPAA risk assessment by OCR/HHS-aligned consultant 年度

### Phase 7: Trade-offs + alternatives (权衡 + 备选方案) (7 min)

**Decision 7.1 — Self-host LLM vs BAA cloud LLM**

| 维度 | Self-host (vLLM + Llama-3-medical) | BAA cloud (Claude on Vertex AI) |
|---|---|---|
| Compliance | 最强 (零 egress) | 接受 (BAA + Vertex AI VPC endpoint) |
| Quality | Llama-3-medical < Claude 4.6 on Med-MCQA by ~8 pts | 最强 |
| Cost (1M queries/month, avg 4K tokens in / 500 out) | infra ~$8K/month | ~$15K/month |
| Operational | 维护 H100 cluster, ML on-call | none |
| Iteration | Fine-tune 自由 | 看 Anthropic / Google 发版 |

我推: Phase 1 BAA cloud (上线快, 质量保证), Phase 2 self-host (cost + sovereignty), Phase 3 dual-track (BAA cloud for complex, self-host for routine queries 70%).

**Decision 7.2 — pgvector vs Vertex AI Vector Search K-NN vs Vespa**

| 选项 | 50M docs 表现 | Pros | Cons |
|---|---|---|---|
| pgvector | 慢 (50M 时 query > 2s) | 同 PG, 简单 | scale 上限 ~5M docs |
| Vertex AI Vector Search K-NN (HNSW) | 100ms p99 | hybrid (BM25+HNSW) 原生, AWS native | 内存大 |
| Vespa | 50ms p99 | hybrid + reranker 一体, 最强 | 学习成本高, ops 复杂 |
| Vertex AI Vector Search Cloud | not applicable | — | Vertex AI Vector Search Cloud 不能 in-VPC (only QC enterprise on-prem) |

我选 **Vertex AI Vector Search K-NN** — VPC-native + hybrid 原生 + AWS BAA 已 cover, 50M scale ok.

**Decision 7.3 — Embedding model**

BGE-M3 medical > OpenAI text-embedding-3-large 的原因:
1. OpenAI 违反 PHI no-egress
2. BGE-M3 multilingual + multi-granularity (dense+sparse+colbert) 一个模型搞定
3. Medical fine-tune 比 base BGE 在 MedRAG benchmark 高 4-6 nDCG points

**Decision 7.4 — Citation strategy**

| Option | 实现 | 信任度 |
|---|---|---|
| Sentence-level | LLM output 每句话末尾带 `[chunk_id]` | 中等 |
| Token-span | LLM output 每个 claim 带 `[chunk_id:start-end]` + NLI verify | 高 (我选) |
| Document-level | 只显示 top-5 source doc, 不在 generation 内嵌 | 低 (LLM 可幻觉) |

---

## 关键决策点 (with rationale)

1. **PHI redaction at ingestion, not query** — 因为 redaction 是 CPU + GPU 昂贵 operation (medspaCy + custom NER 一次 doc ~200ms), 不能在 doctor query 时实时跑. 一次性付出, 50M docs × 200ms / 16 cores = ~7 天. 之后 query 不再需要.

2. **ACL pre-filter, not post-filter** — HIPAA "minimum necessary": doctor 不应"看见过"再被拒. 实现是把 patient_id whitelist 作为 Vertex AI Vector Search filter, K-NN 在 filtered subset 上跑.

3. **Cross-encoder rerank over more candidates** — Bi-encoder (HNSW) 召回 top-100, cross-encoder rerank 出 top-10 给 LLM. 因为医疗 query "diabetes treatment plan" 召回时同义改写多, rerank 排版 critical.

4. **Hybrid HNSW + BM25 over pure HNSW** — 医疗 query 大量 keyword (drug name, ICD code), pure HNSW 在精确 token match 上输给 BM25 30% recall. RRF fusion 给 nDCG@10 +0.08 在我们 golden set.

5. **Self-host embedding + reranker, BAA cloud generation** — 拆 trust boundary: embedding/reranker 是确定性算子可 audit, generation 是黑盒可 BAA-covered. cost 也 ok (embedding 模型小, gen 模型大).

6. **Audit log as event stream, not application log** — Cloud Audit Logs 不够 (它只 cover AWS API). 应用层每个 PHI access 都 emit 到 Pub/Sub → GCS Object Lock, schema 包含 (who, what doc_ids, when, why query, success). 6 年 WORM. 这是 OCR audit 必看的.

7. **Citation token-span + NLI verify** — claim 级别保真. NLI threshold 0.8 是经验值 (太严 false negative 多, 太松幻觉漏掉). 不达标的 claim 标灰 + 显示原文 chunk 让 doctor 自己看.

---

## 数字 (capacity sizing, cost math)

**Storage**:
- 50M docs × avg 4KB text = 200GB raw text
- + Embedding 50M × 1024D × 4B = 200GB
- + HNSW 内存 overhead 1.5× = 300GB
- + BM25 inverted index ≈ 200GB
- + Audit 6 年 × 1M queries/year × 2KB = 12GB (compressed GCS)
- Total: ~1TB hot + cold GCS Object Lock

**Throughput**:
- Doctor queries: 5000 doctors × 20 queries/day × 250 work days = 25M/year, peak QPS ~30
- Ingestion: 100K events/day average, 500K peak burst

**Latency budget (3s p50)**:
| Stage | Budget | 实际 |
|---|---|---|
| Auth + ACL resolve | 50ms | Redis ACL lookup + JWT verify |
| Query embed | 80ms | BGE-M3 GPU + network |
| Hybrid retrieve | 200ms | Vertex AI Vector Search parallel HNSW+BM25 |
| Rerank | 150ms | cross-encoder 100 candidates |
| LLM gen | 2000ms | Claude Sonnet 4.6, ~500 tokens out streaming |
| Citation verify | 300ms | NLI model on claims |
| Audit emit | 20ms | async to Pub/Sub |

**Cost**:
- Compute (g5/r6i mix): ~$80K/year
- Vertex AI Vector Search managed: ~$40K/year
- Aurora + Firestore / Bigtable + GCS: ~$30K/year
- Claude Sonnet 4.6 (1M queries × 4K in / 500 out @ BAA): $3/M in + $15/M out → 1M × ($0.012 + $0.0075) = $19.5K/month → $234K/year
- 总: ~$400K/year for 5000-doctor network — ~$80/doctor/year, very acceptable vs $200K/hospital saved chart-review time

---

## Gao Xin 简历专属 reframe

这道题映射到你简历多个项目:

- **TikTok PayLater BNPL chatbot (RAG + intent routing)** — 同样的 RAG architecture, 但你处理的是 PII (用户金融) 而不是 PHI. ACL 模型 (user 只能看自己 records) 你做过, intent routing 你做过. 跟面试官说: "我做 BNPL chatbot 时 ACL 设计是 user-level RLS, 这里换成 doctor-patient ACL bitmap, 同样思路, 但 patient cardinality 高 100×."
- **Indonesia refund tier (regulator audit pass)** — 你证明过能搭满足 OJK 监管的 audit pipeline (immutable + full chain). HIPAA 的 audit 跟 OJK 在结构上一样: who/what/when/why immutable log. 直接套.
- **Internal Agent Platform (50+ services)** — 你做的 MCP-like tool abstraction, EHR connector 模式可以直接套. Epic FHIR connector 就是一个 MCP server.
- **ConvFinQA (multi-hop)** — multi-step retrieval + reasoning 经验. 医疗多 hop: "latest treatment plan" → 先找最新 doc → 再找其中 plan section → 提取. 你做过.
- **Voice agent 7 markets, multi-tenant** — 你处理过 per-tenant 数据隔离 + 模型路由, 这里 multi-hospital tenant 隔离同样思路.

面试时这么 reframe: "我在字节做 PayLater chatbot 时 RAG 架构跟这道题 70% 重叠, 30% 增量是 HIPAA-specific safeguards (PHI redaction at ingest, BAA chain, OCR audit). 我去 hospital 之前会先做 4-week 合规吸收 (HIPAA training + 客户 IT security walkthrough), 然后基于已有 RAG 架构改造."

---

## 5 个 Follow-ups

1. **"假设客户 IT team 不允许装 KMS, 要用 HSM, 怎么改?"** — 答: AWS CloudHSM (FIPS 140-2 L3), 用 PKCS#11 接入应用. envelope encryption 仍然 sound. 性能损失 ~10ms per encrypt/decrypt 操作, in-memory cache data key 减少调用.

2. **"50M docs 重建一次索引太慢, 怎么 incremental?"** — 答: HNSW 支持 incremental insert, 但 delete + 重 insert 会让图劣化. 策略: 每 shard 累计 delete 比 > 5% 时 trigger reindex; 平时 insert in-place. 同时维护 v1 / v2 dual-index 做 blue/green.

3. **"Citation 99% faithful 不够, doctor 还是不放心. 怎么办?"** — 答: (a) 加 UI 强制 inline citation display + click-to-source-doc; (b) 加 confidence indicator (NLI score < 0.8 标灰); (c) 提供 "show me raw documents" 退出模式 — 不生成回答, 只显示 top-10 chunks; (d) 加 second-opinion 模式让 doctor 看到不同 model 的不同回答, 强调不替代 medical judgment.

4. **"如果 Epic 突然给我们一个 Field 包含 patient SSN 但我们没识别成 PHI, 出 audit 时怎么 trace?"** — 答: 这就是为什么 raw doc hash 留在 redaction map. OCR audit 时我们 reverse 看 v1 → v2 redaction diff. 同时这种漏检触发 retraining queue + customer notice. SLA: 通知客户 48 小时内.

5. **"另一个客户 hospital network 没有 Epic, 用 Allscripts/Meditech, 怎么 onboard?"** — 答: 每个 EHR 一个 connector module, 走标准化的 canonical `clinical_note` schema. 新 EHR = 4-6 周 onboard, 主要工作在 HL7v2 / proprietary API mapping. RAG / retrieval / generation 完全复用.

---

## ❌ 死路答法

1. **"用 OpenAI embedding API"** — 直接挂. PHI 出 VPC violation.
2. **"用 Vertex AI Vector Search vector DB"** — 即使有 BAA, customer legal 通常 reject, 因为 vector 本身可被 inverse 出 PHI.
3. **"用 OpenAI GPT-5.5"** — 同上, BAA 有但 hospital legal 不接受 default. 必须 BAA cloud BUT in customer's own VPC (Vertex AI).
4. **"裸 HNSW, 不要 BM25"** — 医疗 query keyword-heavy, miss 30% recall.
5. **"PHI 留着, query 时 redact"** — 性能爆炸 + 每次 query 都得 PHI scan + 失败 PHI 漏出风险.
6. **"chunk size 256 fixed"** — 切断 clinical section semantic boundary, retrieval 质量大跌.
7. **"audit 写应用日志 (Cloud Monitoring Logs)"** — 不 immutable, 不 WORM, OCR 不认.
8. **"用 RBAC role-based 不做 patient-level ACL"** — Cardinality 5K doctor × 1M patient ACL 不能用 role 解决, 必须 patient 粒度.
9. **"index 全量重建一次就好"** — 50M scale 不可行, 必须 incremental + blue/green.
10. **"citation 显示 doc title 就行"** — doctor 不信任, faithfulness 验证缺失.

---

## ✅ 加分项

1. **开口就讲 HIPAA Tech Safeguards 5 条 → 组件映射** — 立刻 signal staff-level 合规思维
2. **PHI redaction 三层 (rule + ML + custom)** + 解释 quasi-identifier k-anonymity 风险
3. **ACL pre-filter, 解释为什么不 post-filter** (minimum necessary 原则)
4. **Citation token-span + NLI verify** + 不达标的 fallback strategy
5. **Audit log 是 event stream 不是 application log** + 6 年 WORM + OCR audit ready
6. **Trade-off 主动给** (self-host vs BAA / 索引选型 / cost vs quality)
7. **Right to erasure 的 vector 删除 not just metadata** — 体现真懂 HIPAA + GDPR
8. **EHR vendor outage handling** (Epic Tuesday upgrade window 是真实运维痛点, 你知道说明你做过)
9. **Phased rollout 路线** (Phase 1 BAA cloud → Phase 2 self-host) 而不是一次性 over-engineer
10. **Numbers 给得出来** (200GB index, 300GB HNSW RAM, $80K self-host vs $234K BAA cloud)

---

## 一句话总结

医疗 RAG 不是 "RAG + 加密", 是 **从 EHR connector 到 audit log 全链路按 HIPAA 红线设计**, PHI redact 在 ingest, ACL pre-filter 在 retrieve, citation 在 generate, audit immutable 在 store, BAA 在 contract — 任何一环漏掉都是 OCR fine + 客户走人.

---

## Cheat Sheet

```
组件                   实现                              数字
─────────────────────────────────────────────────────────────────────
EHR connector          Epic FHIR R4 + Subscription R5    100 docs/sec backfill, 30K/day delta
PHI redactor           Presidio + medspaCy + custom NER  200ms/doc, 3 layers
Chunking               Section-aware, 512 tokens         50M chunks ≈ 50M docs
Embedding              BGE-M3 medical, self-host         g5.xlarge × 8, 5K embs/sec
Vector store           Vertex AI Vector Search K-NN HNSW M=32         200GB raw, 300GB RAM
BM25 + Hybrid          Vertex AI Vector Search native + RRF           BM25 250GB, +0.08 nDCG vs pure HNSW
Reranker               BGE-reranker-v2-m3 cross-encoder  50ms / 10 candidates
LLM (Phase 1)          Claude Sonnet 4.6 via Vertex AI+BAA $3/$15 per 1M tokens
LLM (Phase 2)          Llama-3-medical on vLLM           4× H100, $80K/yr
ACL                    Aurora RLS + Redis bitmap         pre-filter, not post
Audit                  Pub/Sub → GCS Object Lock          6yr WORM, immutable
Key mgmt               KMS-CMK per tenant + rotate 365d  envelope encryption
Network                VPC endpoints only, mTLS, no IGW  TLS 1.3 mandatory
DR                     RPO 15min, RTO 4h                 cross-region GCS, AZ standby
Cost (5K doctors)      ~$400K/year                       $80/doctor/yr
```
