## 📚 FDE 52 道真题总目录

> **来源**: Exponent《Forward Deployed Engineer Interview: The Definitive 2026 Guide》
> **范围**: Palantir / OpenAI / Anthropic / Databricks / ElevenLabs / Scale AI 真实候选人反馈
> **整理**: 按轮次分类, 共 52 题 + 各公司侧重表 + 高频提醒

---

## 📖 术语速查 (本题用到的)

> 这是全 52 题的总目录, 先把 FDE 相关角色 / 公司 / 题型术语过一遍. 后面具体题里再展开.

### FDE / 角色术语 ⭐ 必懂

| 术语 | 解释 |
|---|---|
| **FDE (Forward Deployed Engineer)** ⭐ | "前线部署工程师" — 在客户现场或者贴身服务客户的工程师. 不是普通 SWE, 60% 时间和客户 ops/product/compliance 对接, 把通用产品 deploy 到 customer 具体场景. Palantir 发明的角色, 现在 OpenAI / Anthropic / Databricks 都有. |
| **FDSE (Forward Deployed Software Engineer)** | Palantir 的正式叫法, 等同于 FDE. |
| **Deployment Strategist** | Palantir 的另一个 FDE-adjacent 角色, 偏 customer-facing strategy, 写代码少一点. |
| **Applied AI Engineer** | Anthropic 的 FDE-equivalent, 也叫 "Applied Solutions". 偏 enterprise 客户部署 + Claude 集成. |
| **SWE (Software Engineer)** ⭐ | 标准软件工程师. PM 给 PRD → ship feature → release notes. 信息流走 PM 中转, 不直接对接 customer. |
| **MLE (Machine Learning Engineer)** | ML 工程师. Happiness function 是 model quality metrics (accuracy / latency), 不是 customer outcome. |
| **SE (Sales Engineer / Solutions Engineer)** | 售前工程师. Deal close 之后就 hand off, 不 own deployment lifecycle. |
| **Research Scientist** | 研究员. Unit of progress 是 paper, distance to customer = max. |

### 公司 / 平台 ⭐ 必懂

| 术语 | 解释 |
|---|---|
| **Palantir** | 老牌数据 / ontology 平台公司. 客户 Airbus / JPMorgan / DoD. FDE 的发源地, 5+ 年 tenure 文化, 偏 regulated industry 长周期 deployment. |
| **Foundry** | Palantir 的 data + ontology 平台. 把客户混乱的 data model codify 成统一 ontology. |
| **AIP (Palantir AI Platform)** | Palantir 把 LLM 接到 Foundry 上的 layer. |
| **OpenAI** | GPT / Operator / Codex 的公司. FDE 偏 enterprise + agent stack. |
| **Anthropic** | Claude / Claude Code 的公司. FDE-equivalent 叫 Applied Solutions, 强调 safety + Constitutional AI. |
| **Databricks** | Lakehouse 数据 + ML 平台. 客户 Block / Mastercard. 收购 Mosaic ML 之后做 Mosaic AI 全套 LLM lifecycle. |
| **Scale AI** | 数据标注 + RLHF + evaluation 平台. 服务 OpenAI / Anthropic / Meta. Donovan 做 defense / federal sector. |
| **ElevenLabs** | Voice AI / TTS / 声音克隆 leader. 紧凑创业流程, 看速度和端到端 ownership. |
| **Exponent** | 面试题库 / mock interview 平台 (exponent.com). 这 52 道题的原始来源. |

### 7 大题型 ⭐ 必懂

| 术语 | 解释 |
|---|---|
| **Behavioral** | 行为题. STAR 框架讲故事, 测 mission fit / customer-handling / ownership. |
| **Coding** | 编程题. FDE 偏真实工程问题 (rate limiter / 脏 CSV / RAG pipeline), 不是 LeetCode hard. |
| **System Design** | 系统设计题. 带企业约束 (HIPAA / VPC / SSO), 不是设计 Twitter. |
| **Decomposition** ⭐ | 问题拆解题. **FDE 最关键的一轮**, 给你一个大模糊问题 (e.g., "90 天统一 3 套反欺诈系统"), 看你怎么拆. 常见挂法: 还没厘清问题就冲方案. |
| **Client Simulation** | 客户模拟题. 面试官扮客户 (有时刁难), 看你怎么沟通. |
| **AI Specialty** | AI lab 专属深度题 (fine-tune vs RAG / eval / guardrails / prompt injection). |
| **Production & Reliability** | 生产可靠性题. FDE 不只 ship 一次, 还要 keep it running (incident response / model drift). |

### 方法论 / 框架

| 术语 | 解释 |
|---|---|
| **STAR** | Situation / Task / Action / Result. Behavioral 题讲故事的标准框架. |
| **Walking-skeleton MVP** | 走骨头 — 最薄端到端版本, 每组件 mock 但流程全跑通. 跑稳后再换真组件. Decomposition 题标准 MVP 方法论. |
| **Take-home** | 带回家做的题, 通常 OpenAI 用 — 给你一个 dataset / API, 几天后 submit + 录视频讲解你的思路. |
| **Ontology** | 数据 / 概念的统一定义体系 — 不是数据库 schema, 是上层业务概念词典. Palantir 的核心方法论. |
| **RSP (Responsible Scaling Policy)** | Anthropic 的安全 scaling 政策, 模型能力到某个 threshold 才解锁部署. 面试 Anthropic 之前必读. |
| **Core Views** | Anthropic 的 "Core Views on AI Safety" 公开文档, mission alignment 的考点. |

### 高频公司侧重词

| 术语 | 解释 |
|---|---|
| **lakehouse** | Databricks 的核心概念 — 把 data lake (raw data) 跟 data warehouse (structured) 合一. |
| **MLflow** | Databricks 旗下 ML lifecycle 工具 (track / version / deploy model). |
| **Mosaic AI** | Databricks 收购 Mosaic ML ($1.3B) 之后的 LLM 训练 + serving stack. |
| **Operator** | OpenAI 的浏览器 / 计算机 use agent — agent 能在网页上点按钮 / 填表. |
| **Codex** | OpenAI 的 code agent. |
| **Claude Code** | Anthropic 的 code agent / CLI. |
| **Constitutional AI** | Anthropic 用 AI 反馈替代部分人类反馈做 alignment 的方法 (RLAIF). |

---

## 🎯 7 大类索引

### 一、行为 / 动机题 (Behavioral & Motivation) — 10 题

不是测情商, 是测**你为什么愿意做这个非典型 SWE 的活**, 以及**你能不能在客户面前讲清楚自己的工作**.

| # | 题 | 关键考察 |
|---|---|---|
| Q01 | 为什么选 FDE 而不是普通 SWE? | mission fit, FDE 定位理解 (几乎必问, 答不好直接卡) |
| Q02 | 讲一个你端到端负责过的、技术上最有挑战的项目 | end-to-end ownership |
| Q03 | 讲一次部署失败的经历, 你怎么处理的 | learn-from-failure |
| Q04 | 讲一次你不得不向客户传达坏消息 | hard conversation |
| Q05 | 讲一次你和客户意见不合并坚持了立场 | disagree without alienating |
| Q06 | 讲一次你发现多个客户的共性、并改变了团队做法 | product sense (考察 patternization) |
| Q07 | 讲一次你在一个并不完全理解的环境里工作 | ambiguity navigation |
| Q08 | 你推翻过的一个技术决策, 从中学到了什么 | intellectual humility |
| Q09 | 描述你入职新 FDE 岗位的前 30/60/90 天计划 | onboarding maturity |
| Q10 | 为什么是我们公司? | company-specific research (要引用真实客户/产品/研究) |

### 二、编程 / 工程深度题 (Coding) — 10 题

**FDE 编程轮偏真实工程问题, 不是 LeetCode hard**.

| # | 题 | 主要技能 |
|---|---|---|
| Q11 | 单用户限流 + 全局限流的 rate limiter | 分布式协调 (Anthropic 最爱) |
| Q12 | 解析引号格式混乱的脏 CSV | 边界情况 + 健壮性 |
| Q13 | PDF → 带实体抽取的 JSON 索引 CLI | 真实工程 + LLM 集成 |
| Q14 | 处理下游变慢的流式消费者 (backpressure) | 异步 + 流量控制 |
| Q15 | 把 200 行函数重构成可测试的 | 工程思路 + 解释能力 |
| Q16 | 不稳定 API 的带 jitter 指数退避 | 真实故障处理 |
| Q17 | 给定文档文件夹, 实现小型 RAG pipeline + 为 chunking 辩护 | AI 工程 + 设计辩护 |
| Q18 | 不用托管, 在 1000 万向量找 top-k 最相似 | ANN + 工程 |
| Q19 | SQL 找上季度退货率 > 30% 客户 | SQL + 业务理解 |
| Q20 | 诊断慢 SQL (查询计划 + 索引 + 分区) | DB 性能 |

### 三、系统设计 / 架构题 (System Design) — 10 题

**不是设计 Twitter, 是带企业约束的真实部署**.

| # | 题 | 行业 / 约束 |
|---|---|---|
| Q21 | HIPAA + 5000 万文档医疗 RAG 系统 | 医疗 + 合规 |
| Q22 | 12 个零散零售数据源汇入预测模型 | 数据工程 pipeline |
| Q23 | F500 在自己 AWS VPC + Okta SSO + BigQuery | 企业部署 |
| Q24 | 500 仓库经理 + 99% 送达率 AI agent 评估框架 | eval framework |
| Q25 | 诊断 LLM 推理 pipeline 高延迟 | OpenAI 最爱 (tokenization/网络/batch/KV cache) |
| Q26 | 支持优先级 + 重试 + 死信的分布式任务队列 | 真实工程 |
| Q27 | SAP + Salesforce + Postgres 统一给 AI agent | 异构数据集成 |
| Q28 | LLM 搜索从 1.5s 压到 100ms | 性能优化 |
| Q29 | 生产环境 prompt 版本 / A/B / 回滚 | prompt ops |
| Q30 | Agent 系统可观测性: 记录什么、告警什么、看板 | observability |

### 四、问题拆解 / 开放式案例题 (Decomposition) — 5 题 ★ **最关键的一轮**

**不是考你的答案, 是看你如何思考一个没见过的问题**. 最常见的挂法: **还没厘清问题就冲去给方案**.

| # | 题 | 题型特征 |
|---|---|---|
| Q31 | 大城市 911 急救响应时间 (60 min) | Palantir 风格 |
| Q32 | 银行 3 套并购反欺诈系统统一 (90 天计划) | M&A 数据整合 |
| Q33 | 药企 AI 助手 + 法务/IP/合规 | 高合规风险 |
| Q34 | 物流 + SAP + 天气 + 500 仓库经理 → 自动重路由 agent | 端到端 agent |
| Q35 | 保险 3000 万条理赔 LLM 摘要 + 各州监管 | 跨州合规 + 大数据量 |

**推荐 5 步拆解框架**:

1. **澄清问题** — 确认真正的目标是什么 (响应时间? 成本? 覆盖公平性?)
2. **找出干系人和成功指标** — 谁会认为这个项目成功? 哪个指标会动?
3. **梳理输入数据** — 有哪些数据、什么形态、谁拥有、新鲜度如何
4. **拆成可解子问题** — 按风险和价值排序, 先做最高风险的
5. **先给最薄的 walking-skeleton MVP, 再迭代** — 前两周用 mock 逻辑打通端到端, 跑稳后再换真模型

### 五、客户模拟 / 沟通题 (Client Simulation) — 5 题

**面试官会扮演客户, 有时友好、有时故意刁难或不懂技术**.

| # | 题 | 难点 |
|---|---|---|
| Q36 | 部署延期 3 周, 客户 CTO 在线上 | 传达坏消息 |
| Q37 | 客户想要破坏数据治理的功能, 在不破坏关系前提下拒绝 | 拒绝艺术 |
| Q38 | 向不懂技术的 VP 解释 RAG 无法保证 100% 准确 | 非技术沟通 |
| Q39 | 客户安全团队不给生产凭证 | 解除阻塞 (政治) |
| Q40 | 不认同客户选的架构, 怎么提出来 | push back |

**强答法套路**:
- 用 **ownership 语言** (「我周五前搞定」), 别推卸 (「团队在处理」)
- 给方案前**先问诊断性问题**
- **先承认客户对的地方**, 再 push back
- 给出**带明确取舍的选项**
- **绝不承诺做不到的事**

### 六、AI 专项技术题 (AI Lab FDE 岗位) — 7 题

OpenAI / Anthropic / 字节 / Cohere 等 AI 实验室专属深度题.

| # | 题 | 主题 |
|---|---|---|
| Q41 | 什么时候 fine-tune / RAG / prompt engineering | 决策框架 |
| Q42 | 除了「看起来对」, 怎么评估 LLM 系统 | eval methodology |
| Q43 | 生产 LLM 应用的 guardrails 设计 | safety + production |
| Q44 | 你的 RAG chunking 策略 + 向怀疑客户解释 | RAG defense |
| Q45 | 带工具调用、记忆、评估的端到端 agent 系统 | agent architecture |
| Q46 | 面向客户的 agent 怎么处理 prompt injection | security |
| Q47 | 企业客户: 托管 API vs 自托管开放权重 | enterprise tradeoff |

### 七、生产 / 可靠性题 (Production & Reliability) — 5 题

**FDE 不只 ship 一次, 还要 keep it running**.

| # | 题 | 场景 |
|---|---|---|
| Q48 | 第三方 API 间歇性超时排查 | 真实 production debug |
| Q49 | 凌晨 2 点部署宕机, 事故响应流程 | incident response |
| Q50 | 紧急 deadline + 关键功能上线, 哪些妥协 / 不妥协 | trade-off discipline |
| Q51 | P0 事故后在客户环境里怎么做复盘 | postmortem with customer |
| Q52 | 客户报「模型越来越差」, 排查模型漂移 | drift diagnosis |

---

## 🔥 贯穿全程的高频提醒 (十大被拒原因里最致命的 4 个)

| # | 提醒 | 后果 |
|---|---|---|
| 1 | **Decomposition 轮里别急着给方案** | 这是最常见的拒绝理由 |
| 2 | **讲项目用「我」而不是「我们」** | FDE 经理特别在意个人 ownership |
| 3 | **编程和设计时别沉默** | 面试官读不了你的心, 要持续讲思路 |
| 4 | **AI 岗位上别在「评估」问题上打太极** | "你怎么知道它真的работает" 是分水岭题 |
| 5 (bonus) | **「为什么是我们公司」别说空话** | 要引用对方真实的客户/产品/研究 |

---

## 🏢 各公司侧重点速查

| 公司 | 角色名 | 侧重 |
|---|---|---|
| **Palantir** | FDSE / Deployment Strategist | decomposition、数据工程、ontology 建模、mission fit (国防/公民自由话题) |
| **OpenAI** | Forward Deployed Engineer | take-home (带视频讲解)、评估、生产 AI 深度、客户沟通 |
| **Anthropic** | Applied AI Engineer | 实用编程 (rate limiter / 流式 / 分布式队列)、mission alignment (读 Core Views、RSP) |
| **Databricks** | AI Engineer / 客户向工程师 | Spark、SQL、数据建模、lakehouse、MLflow |
| **Scale AI** | FDE | 国防/政府、PySpark、脏数据清洗 |
| **ElevenLabs** | FDE | 紧凑创业流程、案例轮为核心、看速度和端到端 ownership |

---

## 🎯 推荐刷题顺序 (按 ROI)

**Week 1** (基础高 ROI):
1. **Behavioral Q1, Q2, Q10** (必答, 答不好直接卡)
2. **Decomposition Q31-35** (最关键的一轮, 整体看一遍)
3. **AI Q41, Q42, Q44** (LLM 必杀)

**Week 2** (深度):
- **System Design Q21, Q25, Q28** (跨行业代表性)
- **Coding Q11, Q14, Q17** (Anthropic / 通用)
- **Client Sim Q36, Q38, Q40** (高频沟通)

**Week 3** (覆盖):
- 剩下的 33 道, 按你 weakest 类型先补

**Week 4** (mock):
- 找朋友 mock 5-10 道, 录音回放
- 重点改 Decomposition 一题不要超 8 min 给方案

---

## 📋 每题页面结构

每道真题 deep-dive 页面包含:

1. **题目** (verbatim) + Round + 出处
2. **这题在考什么** (隐含信号)
3. **完美答案架构** (4-7 层 layered response)
4. **详细回答 (sample monologue)** 30-60 行可背诵
5. **Gao Xin 简历专属版** (你的项目映射 + STAR)
6. **5 follow-ups** (interviewer 追问 + 准备答案)
7. **❌ 死路答法** (碰了就挂)
8. **✅ 加分项**
9. **一句话总结**
10. **Cheat sheet** (1 页可印)

---

## 链接全表 (52 题 + 1 index)

> 直接点链接进入对应 deep-dive 页面

**Behavioral (10)**:
[Q01](zhenti-001-why-fde-not-swe.html) ·
[Q02](zhenti-002-end-to-end-technical-project.html) ·
[Q03](zhenti-003-deployment-failure.html) ·
[Q04](zhenti-004-deliver-bad-news.html) ·
[Q05](zhenti-005-disagreed-stood-firm.html) ·
[Q06](zhenti-006-common-pain-changed-team.html) ·
[Q07](zhenti-007-work-without-full-context.html) ·
[Q08](zhenti-008-overruled-technical-decision.html) ·
[Q09](zhenti-009-30-60-90-plan.html) ·
[Q10](zhenti-010-why-this-company.html)

**Coding (10)**:
[Q11](zhenti-011-rate-limiter-user-and-global.html) ·
[Q12](zhenti-012-parse-messy-csv.html) ·
[Q13](zhenti-013-cli-pdf-to-json-index.html) ·
[Q14](zhenti-014-streaming-consumer-backpressure.html) ·
[Q15](zhenti-015-refactor-200-line-function.html) ·
[Q16](zhenti-016-exp-backoff-with-jitter.html) ·
[Q17](zhenti-017-small-rag-pipeline-defend-chunking.html) ·
[Q18](zhenti-018-topk-similar-10m-vectors-no-host.html) ·
[Q19](zhenti-019-sql-returns-rate-customers.html) ·
[Q20](zhenti-020-diagnose-slow-sql.html)

**System Design (10)**:
[Q21](zhenti-021-hipaa-vpc-rag-50m-docs.html) ·
[Q22](zhenti-022-12-source-ingest-pipeline.html) ·
[Q23](zhenti-023-fortune-500-aws-vpc-okta-snowflake.html) ·
[Q24](zhenti-024-500-warehouses-routing-eval-framework.html) ·
[Q25](zhenti-025-llm-inference-latency-diagnosis.html) ·
[Q26](zhenti-026-task-queue-priority-retry-dlq.html) ·
[Q27](zhenti-027-unify-sap-salesforce-postgres-for-agent.html) ·
[Q28](zhenti-028-llm-search-1500ms-to-100ms.html) ·
[Q29](zhenti-029-prompt-version-ab-rollback.html) ·
[Q30](zhenti-030-agent-observability-design.html)

**Decomposition (5)**:
[Q31](zhenti-031-911-emergency-response.html) ·
[Q32](zhenti-032-bank-3-acquired-fraud-systems.html) ·
[Q33](zhenti-033-pharma-ai-with-ip-compliance.html) ·
[Q34](zhenti-034-logistics-sap-weather-500-managers.html) ·
[Q35](zhenti-035-insurance-3000-claims-llm-summary.html)

**Client Sim (5)**:
[Q36](zhenti-036-deployment-3-weeks-late-cto.html) ·
[Q37](zhenti-037-decline-feature-data-governance.html) ·
[Q38](zhenti-038-explain-rag-no-100-accuracy.html) ·
[Q39](zhenti-039-unblock-security-credentials.html) ·
[Q40](zhenti-040-disagree-with-customer-arch.html)

**AI Specialty (7)**:
[Q41](zhenti-041-when-fine-tune-vs-rag-vs-pe.html) ·
[Q42](zhenti-042-eval-llm-beyond-looks-right.html) ·
[Q43](zhenti-043-production-llm-guardrails.html) ·
[Q44](zhenti-044-rag-chunking-strategy-defense.html) ·
[Q45](zhenti-045-end-to-end-agent-with-tool-memory-eval.html) ·
[Q46](zhenti-046-customer-facing-prompt-injection.html) ·
[Q47](zhenti-047-managed-vs-self-host-tradeoff.html)

**Production (5)**:
[Q48](zhenti-048-third-party-api-intermittent-timeout.html) ·
[Q49](zhenti-049-2am-incident-response.html) ·
[Q50](zhenti-050-emergency-deadline-tradeoffs.html) ·
[Q51](zhenti-051-p0-postmortem-customer-env.html) ·
[Q52](zhenti-052-diagnose-model-getting-worse.html)

---

## 一句话总结

> **52 题不是用来全部背下来的, 是用来检验你思维空白点. 每周 mock 10 题, 8 周覆盖完整 spectrum**.

加油.
