## Q29 · 生产环境 prompt 版本管理 / A/B / 回滚

> "Your team manages **200+ prompts** in production across 30 LLM features. PM wants to A/B test a new system prompt for the customer support bot. Eng wants to **safely roll it out**, and ops wants to **rollback in 5 minutes** if metrics regress. **Design the prompt lifecycle system** — versioning, eval, A/B, rollout, rollback, audit."

**中文翻译**:

> "你的团队在 production 跑 **200+ 个 prompt**, 跨 30 个 LLM 功能. PM 想给客服 bot 的 system prompt (系统提示词) 跑一个 A/B test. Eng 想**安全上线**, ops 想在指标回归时 **5 分钟内回滚**. **设计 prompt 生命周期系统** — 版本管理, 评估 (eval), A/B, 灰度上线, 回滚, 审计 (audit)."

**Round**: System Design (60 min)
**出处**: Exponent 2026 FDE · 公司: Anthropic / OpenAI / Cohere / Vertex AI · 行业: AI infra / LLM ops
**约束**: 200+ prompts / 30 features / per-tenant variants / non-eng (PM) authors / pre-deploy eval / canary rollout / auto-rollback / audit trail

---

## 📖 术语速查 (本题用到的)

> 这题是 LLM ops + 产品 ops + ML ops 三层混合. 名词不懂答不清 lifecycle. 5 min 看完.

### 概念框架

| 术语 | 解释 |
|---|---|
| **Prompt** ⭐ | LLM 的系统输入文本, 决定 LLM 行为. 这题 200+ 个 prompt 在跑. |
| **Prompt as data, not code** ⭐ | 本题核心思维 — prompt 是产品 config (DB 管), 不是源码 (git 管). |
| **Prompt lifecycle** | 创建 → eval → canary → A/B → prod → 回滚 / deprecate. |
| **System prompt** | 定义 LLM 角色的指令文本. |
| **Variables / Jinja templating** | 模板变量 — `{{ user_name }}` 这种占位符. |
| **Jinja2** | Python 模板引擎, 业界 prompt 标准. |
| **Tier-1 / Tier-2 / Tier-3** | 重要度分级 — tier-1 关键 (支付 / 合规), tier-3 实验. |

### 版本 / 注册中心

| 术语 | 解释 |
|---|---|
| **Prompt registry** ⭐ | 集中存 prompt 的服务 — 这题主架构. |
| **Version tag (semver)** | 语义化版本 1.2.3 — MAJOR.MINOR.PATCH. |
| **Parent version** | 派生自哪个版本 (forking). |
| **State machine (draft/eval-passed/canary/prod/deprecated/rolled-back)** | prompt 版本的状态. |
| **Variables schema** | 模板变量的 JSON Schema. |
| **PromptLayer / LangSmith / Helicone** | 3 个商业 prompt 管理工具. |

### Eval (评估)

| 术语 | 解释 |
|---|---|
| **Eval gate** ⭐ | 评估卡口 — 必须过才能 promote. |
| **Golden set** ⭐ | 黄金集 — 50-200 (input, expected) 对, 回归测试用. |
| **LLM-as-judge** ⭐ | 用 LLM 当 judge 比较两个回复. |
| **Pairwise comparison** | 配对比较 A vs B. |
| **Rubric-based scoring** | 评分细则 — helpfulness/accuracy/tone 各打分. |
| **Human review** | 人工审核 — tier-1 必须. |
| **Active learning queue** | 低 confidence 样本进入人工标注队列. |
| **Lint** | 语法检查 — Jinja syntax / PII / 长度 / model 兼容. |
| **Regression budget** | 允许 quality 下降的预算 (e.g., 3%). |
| **BLEU / Exact match / nDCG** | 不同任务的 scoring 指标. |

### A/B 测试 / Rollout

| 术语 | 解释 |
|---|---|
| **A/B test** ⭐ | A 和 B 两组随机比较, 测效应大小. |
| **Canary rollout** ⭐ | 灰度发布 — 1% → 10% → 50% → 100% 分阶段. |
| **Feature flag** ⭐ | 功能开关 — runtime 控制 traffic 走哪个版本. |
| **LaunchDarkly / Statsig / Optimizely** | 3 个商业 feature flag 平台. |
| **Sticky assignment** ⭐ | 粘性分配 — 同 user 总走同 version, hash(user_id) % 100. |
| **Traffic split / Traffic percentage** | 流量切分百分比. |
| **Multi-armed bandit (MAB)** | 多臂老虎机 — 边 explore 边 exploit 找最优 arm. |
| **Thompson sampling** | MAB 的一种贝叶斯算法. |
| **Power calculation** | A/B 需要多少 sample 才能检测出 X% 效应. |
| **Holdout / Control group** | 对照组. |
| **Cohort** | 同质用户群. |

### Rollback / 自动回滚

| 术语 | 解释 |
|---|---|
| **Auto-rollback** ⭐ | 自动回滚 — metric 超阈值时无需人工. |
| **Rollback trigger** | 触发回滚的 metric 阈值. |
| **Baseline metric** | 过去 7 天的基准. |
| **Sliding window** | 滑动窗口比较. |
| **Flap loop** | 反复回滚 + 重发的循环, 必须防. |
| **Freeze window** | 回滚后冻结时间 (24h), 防 flap. |
| **Cache invalidation** ⭐ | 缓存失效 — Redis cache 必须 < 30s 失效让 rollback 生效. |
| **TTL (Time To Live)** | 缓存过期时间. |
| **Fix forward** | 不回滚, 直接发布修复版. |

### 多租户 / 变体

| 术语 | 解释 |
|---|---|
| **Per-tenant variant** ⭐ | 每客户的定制版本. |
| **Inheritance / extends** | Jinja extends 让 variant 继承 base 并覆盖部分块. |
| **Variant pool** | 命名变体池 (formal / casual / multilingual). |
| **Tenant override** | 租户级覆盖. |

### 监控 / 业务指标

| 术语 | 解释 |
|---|---|
| **CSAT** | Customer Satisfaction Score — 客户满意度. |
| **NPS (Net Promoter Score)** | 净推荐值. |
| **Refund rate** | 退款率. |
| **Conversion rate** | 转化率. |
| **Acceptance rate** | 用户对 LLM 答案的接受率 (thumbs up). |
| **Quality score** | LLM-judge 跑 1% 样本评的分. |
| **Token usage** | LLM 调用的 token 量, 直接关系 cost. |
| **Runaway cost** ⭐ | 失控成本 — 新 prompt 长 50% → 月成本翻倍. |

### 合规 / 审计

| 术语 | 解释 |
|---|---|
| **Audit log** ⭐ | 审计日志 — 每次 prompt 变更的 who/what/when/why. |
| **Immutable log** | 不可变日志 — WORM 写入. |
| **SOX (Sarbanes-Oxley)** | 美国上市公司财务合规, 要求审计保留 7 年. |
| **SOC 2** | 企业服务安全审计标准. |
| **Retention period** | 保留期 (这题 7 年). |
| **Reason / change reason** | 变更原因 — audit 必填. |

### Auth / 部署

| 术语 | 解释 |
|---|---|
| **SDK fetch** | 应用通过 SDK runtime 拿当前 prompt 版本. |
| **Retool** | 内部工具 UI 平台 — 适合搭 PM 友好编辑器. |
| **PagerDuty** | on-call + 告警. |
| **Slack notify** | Slack 通知. |
| **Anthropic prompt cache** | Anthropic 自己的 server-side prompt cache. |

### 模型 / Provider

| 术语 | 解释 |
|---|---|
| **Claude Sonnet 4.6 / Opus 4.7** | Anthropic 模型 — Sonnet 主用, Opus judge. |
| **GPT-5.5** | OpenAI 旗舰. |
| **Gemini 3 Pro** | Google 旗舰. |
| **Model-agnostic prompt** | 不绑死特定 model 的 prompt 设计. |
| **Cross-model eval** | 同 prompt 跑多 model 对比. |

---

## 这道题在考什么

不是考你 git, 是考你 **prompt 不是普通 code, 需要 ML ops 加 web ops 加产品 ops 三层混合的 lifecycle 系统**:

1. **Prompt 不是 source code** — PM/non-eng author, can't require Pull Request review for every typo
2. **Eval gate** — LLM-as-judge + human review before production
3. **Per-tenant variants** — customer A 想 customize wording, multi-tenant prompt
4. **Feature flag for prompt** — LaunchDarkly / Statsig pattern, but prompt-specific
5. **Auto-rollback** — metric regression → revert without human
6. **Audit + immutable history** — who changed what when, why
7. **Cost/latency monitoring** — new prompt 长 50% token → cost +50%, need watch
8. **菜鸟答案失败点**: "git 提交 prompt + feature flag" — too shallow. 没说 eval gate / canary / auto-rollback / per-tenant.

---

## 必问 clarifying questions

1. **Who authors prompts?**: PM 直接 edit 还是 eng 翻译? 影响 UI / approval
2. **Prompt count**: 200 多少 active? 多少 archived?
3. **Per-tenant variants needed?**: customer-specific wording vs single prompt for all
4. **Auto-rollback metric**: latency / error rate / refund rate / NPS, 哪些用作 trigger?
5. **A/B traffic split**: 1% / 50% / 100% 步骤? 决定 ramp-up time
6. **Time budget**: 1 week iteration vs 1 hour hotfix?
7. **Compliance**: 需要 audit who changed when (SOX / SOC 2)?
8. **Existing infra**: 用 Git? Postgres? LaunchDarkly?

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|------|------|------|
| 1 | Clarify + framing | 5 min | Prompt 是 product config, 不是 code | "Prompt 既不是 code 也不是 doc, 是 product config, 需要 ML ops + product ops" |
| 2 | Prompt as data | 8 min | Schema + registry + version | "Prompt registry 是 DB, 不是 git, 因为 PM author + per-tenant + run-time fetch" |
| 3 | Eval pipeline | 10 min | Pre-deploy + golden + LLM-judge | "Eval gate 4 层: lint, golden, LLM-judge, human review" |
| 4 | A/B + canary rollout | 10 min | Feature flag + traffic split + cohort | "LaunchDarkly-style flag, 1% → 10% → 50% → 100%" |
| 5 | Auto-rollback | 8 min | Metric trigger + diff + revert | "Rollback < 5min = pre-promote shadow + auto trigger" |
| 6 | Per-tenant variants | 6 min | Inheritance + override + governance | "Base prompt + per-tenant override, customer 自定义但 governance 在我们" |
| 7 | Audit + observability | 7 min | Immutable history + dashboard | "Every prompt change is event in audit log, dashboard per prompt" |
| 8 | Trade-offs + close | 6 min | DB vs Git, build vs buy (PromptLayer/LangSmith) | "DB-based registry + LangSmith eval, 不全自建" |

---

## 端到端架构图 (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          Prompt Lifecycle System                                        │
│                                                                                         │
│  ┌─AUTHORING (PM-friendly UI)──────────────────────────────────────┐                    │
│  │   Web UI (Retool / custom):                                     │                    │
│  │   - Edit prompt content (markdown editor)                       │                    │
│  │   - Sidebar: variables, model, temperature                      │                    │
│  │   - Inline test: try sample input                               │                    │
│  │   - Version history                                             │                    │
│  │   - Save as draft / propose for review                          │                    │
│  └─────────────────────────────────┬───────────────────────────────┘                    │
│                                    │                                                    │
│                                    ▼                                                    │
│  ┌─PROMPT REGISTRY (Postgres + Redis cache)────────────────────────┐                    │
│  │   Table: prompts                                                │                    │
│  │     id, name (unique), domain, owner, current_version           │                    │
│  │   Table: prompt_versions                                        │                    │
│  │     id, prompt_id, version_tag (semver), content,               │                    │
│  │     model, temperature, max_tokens, variables_schema,           │                    │
│  │     state (draft, eval-passed, canary, prod, deprecated),       │                    │
│  │     created_by, created_at, eval_results, parent_version        │                    │
│  │   Table: prompt_assignments                                     │                    │
│  │     prompt_id, tenant_id, version_id, traffic_pct, started_at   │                    │
│  │   Table: prompt_audit_log                                       │                    │
│  │     prompt_id, action, actor, ts, before, after, reason         │                    │
│  └─────────────────────────────────┬───────────────────────────────┘                    │
│                                    │                                                    │
│                                    ▼                                                    │
│  ┌─EVAL PIPELINE (gate before promote)─────────────────────────────┐                    │
│  │   1. Lint: variable schema match, no PII leak, length, model    │                    │
│  │      compatibility check                                        │                    │
│  │   2. Golden set: 50-200 (input, expected) per prompt            │                    │
│  │      Run new version, compare to current. nDCG / accuracy /     │                    │
│  │      exact match etc. depending on task                         │                    │
│  │   3. LLM-as-judge: Claude Opus 4.7 evaluates quality on         │                    │
│  │      sampled outputs (rubric-based)                             │                    │
│  │   4. Human review: 1-5% sample queue to human evaluator         │                    │
│  │      (mandatory for prompts above tier-2 importance)            │                    │
│  │   5. Cost / latency check: new version's token usage,           │                    │
│  │      compare. > 10% increase → flag                             │                    │
│  │                                                                 │                    │
│  │   Pass → state: 'eval-passed', eligible for canary              │                    │
│  │   Fail → reject with detailed report                            │                    │
│  └─────────────────────────────────┬───────────────────────────────┘                    │
│                                    │                                                    │
│                                    ▼                                                    │
│  ┌─FEATURE FLAG / TRAFFIC SPLIT (LaunchDarkly-style)───────────────┐                    │
│  │   Resolution at request time:                                   │                    │
│  │     SDK: get_prompt("customer_support_v2", user, tenant)        │                    │
│  │     1. Lookup tenant override (if tenant has custom variant)    │                    │
│  │     2. Lookup A/B assignment (sticky by user_id hash)           │                    │
│  │     3. Return prompt version + content                          │                    │
│  │                                                                 │                    │
│  │   Ramp-up: 1% canary → 10% → 50% → 100% (per-stage observation) │                    │
│  │   Sticky: user_id hash mod 100 < pct → treat                    │                    │
│  │   Override: specific user/tenant force into bucket              │                    │
│  └─────────────────────────────────┬───────────────────────────────┘                    │
│                                    │                                                    │
│                                    ▼                                                    │
│  ┌─PRODUCTION INFERENCE (with prompt SDK)──────────────────────────┐                    │
│  │   def chat(user, message):                                      │                    │
│  │     prompt_v = prompt_sdk.get(                                  │                    │
│  │         name="customer_support",                                │                    │
│  │         user_id=user.id,                                        │                    │
│  │         tenant=user.tenant                                      │                    │
│  │     )                                                           │                    │
│  │     # SDK returns version_tag + content                         │                    │
│  │     resp = llm.chat(prompt_v.content, message)                  │                    │
│  │     # Log version_tag with response                             │                    │
│  │     observability.emit(prompt_version=prompt_v.tag, ...)        │                    │
│  └─────────────────────────────────┬───────────────────────────────┘                    │
│                                    │                                                    │
│                                    ▼                                                    │
│  ┌─MONITORING + AUTO-ROLLBACK───────────────────────────────────────┐                   │
│  │   Per-prompt-version dashboard:                                 │                    │
│  │     - p50/p99 latency                                           │                    │
│  │     - token usage in/out (cost)                                 │                    │
│  │     - error rate (LLM refuses, timeouts)                        │                    │
│  │     - quality score (LLM-judge sample 1%)                       │                    │
│  │     - business metric (refund rate, CSAT, conversion)           │                    │
│  │     - acceptance rate (e.g., user clicked thumb-up)             │                    │
│  │                                                                 │                    │
│  │   Auto-rollback triggers:                                       │                    │
│  │     - error rate > 2× baseline for 5 min                        │                    │
│  │     - p99 latency > 1.5× baseline for 10 min                    │                    │
│  │     - business metric regression > 5% in 1h                     │                    │
│  │     - cost > 2× baseline for 30 min                             │                    │
│  │                                                                 │                    │
│  │   On rollback:                                                  │                    │
│  │     1. Flip traffic 100% back to last 'prod' version             │                    │
│  │     2. Mark new version as 'rolled-back' with reason             │                    │
│  │     3. PagerDuty alert to prompt owner                          │                    │
│  │     4. Slack notification to team                               │                    │
│  │     5. Time to rollback < 30 sec (Redis cache invalidate)       │                    │
│  └─────────────────────────────────────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 详细设计 (60-min walkthrough)

### Phase 1: Clarify + framing (澄清 + 框架) (5 min)

开口:
- "Prompt 200+ 中, active production 大约多少? Tier-1 重要 vs tier-3 实验性 mix"
- "Per-tenant variants 需要吗? customer A 想 'be more formal' 类 customization?"
- "Auto-rollback metric: latency / error / refund rate / NPS, 哪个主?"

假设: 150 production active + 50 dev/archive, 30 feature, 60% tier-2+, per-tenant customization 给 paid only (10 tenants), auto-rollback 主用 error rate + 业务 metric.

KPI:
- **Time to promote (new version → 100% prod)**: 1 day for tier-3, 1 week for tier-1
- **Time to rollback**: < 5 min
- **Eval coverage**: 100% prod prompts have golden set
- **Audit**: 100% changes logged with actor + reason

Framing: prompt 不是 code. Treat as **product config managed via versioned data store**.
- Code: PR review, CI, deploy
- Prompt: edit in UI, eval gate, traffic split, runtime fetch
- 共同: version control, audit, rollback. But mechanism different.

### Phase 2: Prompt as data (Prompt 当数据来管) (8 min)

**2.1 Schema design**

```sql
CREATE TABLE prompts (
    id UUID PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,  -- 'customer_support', 'order_classifier'
    domain TEXT,                -- 'support', 'sales', 'analytics'
    description TEXT,
    owner_team TEXT,
    tier SMALLINT DEFAULT 2,    -- 1 = critical, 3 = experimental
    current_version_id UUID,    -- pointer to current prod
    archived BOOLEAN DEFAULT FALSE
);

CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY,
    prompt_id UUID REFERENCES prompts(id),
    version_tag TEXT NOT NULL,    -- semver: '1.2.3'
    content TEXT NOT NULL,
    model TEXT,                   -- 'claude-sonnet-4.6', 'gpt-5.5'
    temperature FLOAT,
    max_tokens INT,
    variables_schema JSONB,       -- e.g., {"user_name": "string", "order_id": "string"}
    state TEXT DEFAULT 'draft',   -- draft, eval-passed, canary, prod, deprecated, rolled-back
    eval_results JSONB,
    parent_version_id UUID,       -- forking
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    promoted_at TIMESTAMPTZ,
    deprecated_at TIMESTAMPTZ,
    UNIQUE (prompt_id, version_tag)
);

CREATE TABLE prompt_assignments (
    id UUID PRIMARY KEY,
    prompt_id UUID,
    tenant_id TEXT,              -- NULL = global default
    version_id UUID,
    traffic_pct INT,             -- 0-100, what % of (tenant) traffic gets this version
    started_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ       -- for A/B time-bound
);

CREATE TABLE prompt_audit_log (
    id UUID PRIMARY KEY,
    prompt_id UUID,
    version_id UUID,
    action TEXT,                 -- 'created', 'promoted', 'rolled_back', 'edited'
    actor TEXT,
    ts TIMESTAMPTZ DEFAULT NOW(),
    before JSONB,
    after JSONB,
    reason TEXT
);
```

Postgres for source of truth. Redis cache for fast read (10ms target).

**2.2 Versioning convention**

semver: MAJOR.MINOR.PATCH
- MAJOR: breaking change (variable schema change, output format change)
- MINOR: new capability (e.g., handle new query type)
- PATCH: bug fix / wording tweak

Tag examples:
- `customer_support@1.0.0`: initial
- `customer_support@1.1.0`: added "handle refund" capability
- `customer_support@1.1.1`: typo fix
- `customer_support@2.0.0`: changed output to JSON

**2.3 Variable schema (Jinja templating)**

Prompts use Jinja templates:
```
You are a helpful customer support agent for {{ company_name }}.
The customer is {{ user.name }} with order #{{ order_id }}.
Their issue: {{ issue }}
```

Variables declared in schema:
```json
{
  "company_name": {"type": "string", "required": true},
  "user": {"type": "object", "properties": {"name": "string"}},
  "order_id": {"type": "string"},
  "issue": {"type": "string"}
}
```

Renderer (Jinja2) validates at compile time. Missing variable → error fast, not runtime.

### Phase 3: Eval pipeline (评估流水线) (10 min)

**Multi-layer gate** before promote to prod:

**Layer 1: Lint (1 sec)**

```python
def lint(prompt_version):
    issues = []
    # Schema validation
    if not prompt_version.variables_schema:
        issues.append("missing variables_schema")
    
    # Template syntax
    try:
        jinja_env.parse(prompt_version.content)
    except TemplateSyntaxError as e:
        issues.append(f"jinja syntax: {e}")
    
    # PII / secret leak check
    if re.search(r'\bsk-[a-zA-Z0-9]{40}', prompt_version.content):
        issues.append("API key in prompt")
    
    # Length warning
    if len(prompt_version.content) > 10000:
        issues.append("prompt > 10k chars, cost concern")
    
    # Model compatibility
    if prompt_version.model not in supported_models:
        issues.append(f"unsupported model: {prompt_version.model}")
    
    return issues
```

**Layer 2: Golden set (5-30 min)**

50-200 (input, expected) pairs per prompt. Run new version on golden, compare to current:

```python
async def golden_eval(prompt_id, new_version):
    golden = await db.fetch_golden(prompt_id)  # list of (input, expected)
    
    results = []
    for ex in golden:
        new_output = await llm.run(new_version, ex.input)
        score = scoring_fn(new_output, ex.expected)  # exact, BLEU, etc.
        results.append({
            'input': ex.input,
            'expected': ex.expected,
            'actual': new_output,
            'score': score
        })
    
    new_avg = mean([r['score'] for r in results])
    # Compare to current version's golden eval (stored at promote time)
    current_avg = await db.fetch_current_avg(prompt_id)
    
    return {
        'pass': new_avg >= current_avg * 0.97,  # 3% regression budget
        'new_avg': new_avg,
        'baseline': current_avg,
        'regressions': [r for r in results if r['score'] < threshold]
    }
```

**Layer 3: LLM-as-judge (10-20 min)**

Sample 50-100 production-realistic inputs. Use Claude Opus 4.7 to judge new vs current:

```python
JUDGE_PROMPT = """
You are evaluating two responses to a customer query.
Rate each on: helpfulness (1-5), accuracy (1-5), tone (1-5).

Query: {query}
Response A: {a}
Response B: {b}

Output JSON: {{"a": {{"helpfulness": 4, ...}}, "b": ..., "winner": "a" | "b" | "tie"}}
"""

results = []
for sample in samples:
    new_resp = await llm.run(new_version, sample.input)
    cur_resp = await llm.run(current_version, sample.input)
    judgment = await judge_llm.run(JUDGE_PROMPT, query=sample.input, a=new_resp, b=cur_resp)
    results.append(judgment)

new_win_rate = sum(j['winner'] == 'a' for j in results) / len(results)
# Pass if new wins or ties >= 50%
```

**Layer 4: Human review (1-3 day async)**

Tier-1 prompts MUST have human review. Sampled 10-30 outputs queued to human reviewer (subject matter expert, e.g., support manager):

```
Reviewer dashboard:
  - Side-by-side: current vs new output
  - Score: 1-5 (better, same, worse)
  - Comment box
  - Reject button
```

Required for tier-1, optional for tier-2, skip for tier-3.

**Layer 5: Cost + latency check (1 min)**

```python
def cost_latency_check(new_version, samples):
    # Run on samples, measure
    measurements = []
    for s in samples[:20]:  # 20 sample is enough
        with timer() as t:
            resp = await llm.run(new_version, s.input)
        measurements.append({
            'latency_ms': t.duration,
            'tokens_in': count_tokens(s.input + new_version.content),
            'tokens_out': count_tokens(resp)
        })
    
    new_p95_latency = percentile([m['latency_ms'] for m in measurements], 95)
    new_avg_cost = mean([m['tokens_in'] * price_in + m['tokens_out'] * price_out for m in measurements])
    
    baseline = await db.fetch_current_cost_latency(prompt_id)
    
    return {
        'latency_change_pct': (new_p95_latency - baseline['p95']) / baseline['p95'],
        'cost_change_pct': (new_avg_cost - baseline['cost']) / baseline['cost'],
        'flag': new_avg_cost > baseline['cost'] * 1.1  # >10% increase
    }
```

Flag for review if cost +10% or latency +20%.

### Phase 4: A/B + canary rollout (A/B + 灰度上线) (10 min)

**4.1 Traffic split implementation**

```python
class PromptSDK:
    def get_prompt(self, name, user_id, tenant_id) -> PromptVersion:
        # 1. Lookup assignments for this prompt
        assignments = self.cache.get(f"assign:{name}:{tenant_id or 'global'}")
        if not assignments:
            assignments = self.db.fetch_assignments(name, tenant_id)
            self.cache.set(..., ttl=60)
        
        # 2. Resolve which version (sticky hash)
        bucket = hash(f"{user_id}:{name}") % 100
        cumulative = 0
        for a in assignments:
            cumulative += a.traffic_pct
            if bucket < cumulative:
                return self.cache.get_version(a.version_id)
        
        # Fallback to default
        return self.cache.get_version_default(name)
```

User-sticky: same user always gets same version (consistent UX, avoid flapping).

**4.2 Rollout stages**

Tier-1 critical prompt rollout:
```
Stage 1: 1% (canary) — 24h observation
Stage 2: 10%         — 48h observation
Stage 3: 50%         — 48h observation
Stage 4: 100%        — promote, deprecate old
```

Tier-3 experimental: 50% → 100% in 1 day.

**4.3 A/B vs canary**

A/B test: compare A and B with statistical rigor
- Hypothesis: new prompt improves CSAT
- Sample size: power calc (e.g., 5000 users for 2pp lift detect)
- 50/50 split for fast convergence
- Duration: until n_samples reached

Canary: roll out gradually, monitor for regression
- Goal: deploy safely, not measure effect
- 1% → 10% → ... ramp
- Halt at any metric breach

These are different. PM 想 A/B = measure effect. Eng 想 canary = safe deploy. 一般 sequence: canary first (no regression), then A/B (measure benefit).

**4.4 Per-tenant override**

```sql
-- Default for all
INSERT INTO prompt_assignments (prompt_id, tenant_id, version_id, traffic_pct)
VALUES ('customer_support', NULL, 'v1.2.0', 100);

-- Custom for tenant ACME
INSERT INTO prompt_assignments (prompt_id, tenant_id, version_id, traffic_pct)
VALUES ('customer_support', 'acme', 'v1.2.0-acme-formal', 100);
```

Tenant ACME 总 hit `v1.2.0-acme-formal`, 其他 tenant hit `v1.2.0`.

### Phase 5: Auto-rollback (自动回滚) (8 min)

**5.1 Trigger metrics**

| Metric | Trigger | Notes |
|---|---|---|
| Error rate | > 2× baseline 5 min | LLM refuse / timeout / 5xx |
| p99 latency | > 1.5× baseline 10 min | UX degradation |
| Quality score | < baseline -5% 1 hour | LLM-judge sample |
| Refund rate | > 1.2× baseline 1 hour | Business signal |
| Cost | > 2× baseline 30 min | runaway token usage |
| CSAT | < baseline -5pp 24 hour | slow signal |

Per-prompt baseline computed from last 7 days. Sliding window comparison.

**5.2 Rollback action**

```python
async def rollback(prompt_id, new_version_id, reason):
    # 1. Find previous prod version
    prev = await db.fetch_one("""
        SELECT * FROM prompt_versions
        WHERE prompt_id = $1 AND state = 'prod' AND id != $2
        ORDER BY promoted_at DESC LIMIT 1
    """, prompt_id, new_version_id)
    
    # 2. Atomically flip traffic
    async with db.transaction():
        await db.execute("""
            UPDATE prompt_assignments SET traffic_pct = 0, expires_at = NOW()
            WHERE prompt_id = $1 AND version_id = $2
        """, prompt_id, new_version_id)
        
        await db.execute("""
            INSERT INTO prompt_assignments (prompt_id, version_id, traffic_pct)
            VALUES ($1, $2, 100)
        """, prompt_id, prev.id)
        
        await db.execute("""
            UPDATE prompt_versions SET state = 'rolled-back', rollback_reason = $1
            WHERE id = $2
        """, reason, new_version_id)
    
    # 3. Invalidate cache (must be < 30 sec to take effect)
    await redis.delete(f"assign:{prompt_id}:*")  # all tenants
    
    # 4. Audit log
    await db.execute("""
        INSERT INTO prompt_audit_log (prompt_id, version_id, action, actor, reason)
        VALUES ($1, $2, 'rolled_back', 'auto-rollback', $3)
    """, prompt_id, new_version_id, reason)
    
    # 5. Alerts
    await pagerduty.alert(prompt_id, reason)
    await slack.notify(f"Auto-rollback of {prompt_id}: {reason}")
```

**5.3 Cache invalidation < 30s**

Redis cache TTL 60s + active invalidation on rollback. SDK in-process LRU cache TTL 30s.

Total time from trigger to effect: detection (5 min metric window) + invalidation (30 sec) ≈ 6 min. Tight, but within 5 min hard requirement IF detection window shortened.

Tight rollback (< 5 min): use shorter detection window for tier-1 (e.g., 1 min). But more false positive risk.

**5.4 Manual rollback button**

PM / on-call can rollback via UI:
- Click "rollback" → confirm → 30s effect
- Same flow as auto, just human-triggered

**5.5 Avoid rollback loop**

After rollback, freeze new version 24h (can't re-promote without team review). Avoid: rollback → re-promote → rollback flap.

### Phase 6: Per-tenant variants (按租户的变体) (6 min)

**6.1 Inheritance model**

```
Base prompt: customer_support@1.2.0 (default for all)
  └─ Variant: customer_support@1.2.0-acme-formal (ACME inherits + override sections)
      Content:
        {% extends "customer_support_v1.2.0" %}
        {% block tone %}Use formal language. Always say "Mr/Ms. <surname>".{% endblock %}
```

Jinja extends/block: variant inherits base, overrides specific sections.

**6.2 Governance**

Customer wants custom prompt → can be:
- (a) Self-serve UI within constraints (variables only, no content edit)
- (b) Submit request → our team author + eval → deploy

99% case use (b). Self-serve (a) risky (compliance, brand violation).

Approval flow:
- Customer requests in support portal
- Customer success team validates business reason
- Eng team authors variant
- Eval gate same as base
- Customer approves output sample
- Deploy as tenant override

**6.3 Variant explosion**

10 tenants × 200 prompts = potentially 2000 variants. Reality:
- 80% of customer requests are minor (tone, language)
- 90% can be handled by parametrized base prompt (variables: tone="formal", language="es")
- Hard custom = 1-2 per tier-1 prompt per top customer = ~50 actual variants

Manage via "variant pool": each tier-1 prompt has 3-5 named variants (default, formal, casual, multilingual), tenant picks one.

### Phase 7: Audit + observability (审计 + 可观测性) (7 min)

**7.1 Audit trail**

Every change → immutable log:
```json
{
  "prompt_id": "customer_support",
  "version_id": "v1.2.0",
  "action": "promoted",
  "actor": "alice@company.com",
  "ts": "2026-05-25T10:30:00Z",
  "before": {"state": "canary", "traffic_pct": 50},
  "after": {"state": "prod", "traffic_pct": 100},
  "reason": "All KPIs green after 48h canary at 50%",
  "eval_results": {...}
}
```

Stored 7 years (SOX retention).

**7.2 Per-prompt dashboard**

Datadog / Grafana dashboard per prompt:
- Traffic split (which versions running)
- Latency p50/p99
- Cost ($ per call)
- Error rate
- Quality score (LLM-judge)
- Business metric (CSAT, refund, NPS)
- Refund rate (if applicable)

Color: green / yellow / red against baseline.

**7.3 Prompt lineage**

UI shows version tree:
```
customer_support
├── 1.0.0 (deprecated 2026-01)
├── 1.1.0 (deprecated 2026-03)
│   └── 1.1.1 (deprecated 2026-04)
├── 1.2.0 (prod, 100%)
│   ├── 1.2.0-acme-formal (tenant variant)
│   └── 1.2.0-globex-casual (tenant variant)
└── 1.3.0-rc1 (canary, 10%)
```

**7.4 Alerts**

| Alert | Channel | Severity |
|---|---|---|
| Auto-rollback triggered | PagerDuty | P1 |
| Quality drop > 5% on canary | Slack | P3 |
| Eval gate failing | Slack to prompt owner | P3 |
| Cost spike > 50% per prompt | Slack | P2 |
| Manual rollback by team | Slack (no page) | Info |

### Phase 8: Trade-offs + alternatives (权衡 + 备选方案) (6 min)

**Decision 8.1 — DB vs Git for prompt storage**

| 选项 | Pros | Cons |
|---|---|---|
| Git repo | Familiar to eng, code review pattern | PM can't edit, slow, conflict-prone |
| DB (我推) | Fast read, runtime lookup, per-tenant, audit native | Need build UI, not just `git log` |
| Hybrid (DB + git sync) | Versioned audit | Complex sync |

我推 DB. Add git backup nightly for DR.

**Decision 8.2 — Build vs buy**

Tools to consider:
- **LangSmith** (LangChain) — prompt registry + eval + tracing
- **Helicone** — LLM observability + experiments
- **Promptlayer** — prompt versioning + comparison
- **Statsig / LaunchDarkly** — feature flag generic, can do prompts

| 决策 | Pros | Cons |
|---|---|---|
| Build all | Customize, no vendor lock | 6 month build, ongoing maintain |
| Buy all (LangSmith) | Fast | Lock-in, may not fit |
| Hybrid (我推) | Best of both | Some integration |

我推: LangSmith for eval + tracing (mature), LaunchDarkly for traffic split (mature), Postgres DB for registry (custom, simple), custom UI in Retool.

**Decision 8.3 — A/B vs multi-armed bandit**

| 选项 | Pros | Cons |
|---|---|---|
| A/B (50/50, time-bound) | Clean stats | Slow to find winner, wastes traffic |
| Multi-armed bandit (Thompson sampling) | Learn fast, exploit | Less clean stats |

I推 A/B for tier-1 (cleaner), MAB for tier-3 experimental.

**Decision 8.4 — When to roll back vs when to fix forward**

Roll back if:
- Quick regression (5 min)
- Unknown root cause
- Tier-1 critical

Fix forward if:
- Known issue with quick fix
- Tier-3 / low risk
- Rolling back loses too much value (e.g., new feature)

---

## 关键决策点 (with rationale)

1. **Prompt as data (DB), not code (Git)** — PM author + runtime fetch + per-tenant.

2. **Eval 4-layer gate (lint + golden + LLM-judge + human)** — quality before promote.

3. **Cost/latency check in eval** — runaway token cost是真实事故.

4. **Sticky user_id hash for A/B** — consistent UX, no flapping.

5. **Per-tenant variants via Jinja inheritance** — DRY but customizable.

6. **5-layer auto-rollback triggers** — multiple signals, robust.

7. **Cache TTL 60s + active invalidation** — < 30s rollback effect.

8. **24h freeze post-rollback** — avoid flap loop.

9. **Audit log immutable + 7yr retention** — SOX compliance.

10. **Buy LangSmith for eval + LaunchDarkly for traffic + build registry** — hybrid pragmatism.

---

## 数字 (capacity sizing, cost math)

**Volumes**:
- 200 prompts × 1M calls/day = 200M LLM calls/day
- SDK fetch (cached): 200M × 95% cache hit = ~10M DB reads/day = 120 QPS
- Audit log: ~100 entries/day (changes), 7yr retention = ~250K rows

**Storage**:
- prompts: 200 rows
- prompt_versions: ~2000 (10 versions per prompt avg)
- prompt_assignments: 200 × 10 tenant variants = ~2K rows
- prompt_audit_log: 250K rows over 7 years
- Total: ~5MB ≈ nothing

**Cache**:
- Redis: 200 prompt × 5 active version × 1KB content = 1MB hot
- 60s TTL, ~10K reads/min hit

**Eval cost**:
- Per new version: lint (free) + golden 100 samples × $0.01 each = $1 + LLM-judge 50 samples × $0.10 = $5 = **$6 per eval**
- Tier-1 human review: ~$50 reviewer time
- 200 prompts × 1 update/month × $6 = $1200/month eval cost (auto)

**Cost monitoring**:
- New prompt longer 50% → 200M × 50% × $0.005/k token avg = $5M/month overrun if undetected
- Our cost-gate catches at canary 1%

**Infra cost**:
- Postgres: ~$200/month (overkill for size)
- Redis: ~$100/month
- LangSmith: ~$2K/month (1M trace/day plan)
- LaunchDarkly: $1K/month (100K MAU plan)
- Custom UI (Retool): $500/month
- Total: ~$4K/month

**Time to detect + rollback**:
- Detection window: 1-5 min (tier dependent)
- Decision (auto rule): < 1 sec
- Cache invalidate + propagate: 30 sec
- Total: ≤ 6 min worst case, ≤ 1 min if tier-1 with 30s window

---

## Gao Xin 简历专属 reframe

1. **TikTok PayLater BNPL prompt management** — 你做过 prompt 多版本管理, A/B for default rate optimization.

2. **TikTok Voice agent 7 markets** — 你做过 per-market prompt variants (语言 + tone + 合规), 直接套.

3. **Indonesia OJK 合规 prompt audit** — 监管要求 immutable audit, 你做过.

4. **Internal Agent Platform prompt registry** — 你做过内部 prompt 中央仓库, 给 30+ 团队用.

5. **ConvFinQA / financial agent eval** — golden set + LLM-judge, 你跑过 production eval.

reframe: "我在字节做 voice agent 时 prompt 跨 7 market × 5 intent = 35 个 + tier-1 critical (compliance disclosure) 需要 audit, 直接做过这道题. 我的 stack 是 自建 Postgres registry + 自建 UI + 自建 A/B + LangSmith 集成. 这道题如果重做我会加 LaunchDarkly 替代自建 flag, 更稳."

---

## 5 个 Follow-ups

1. **"如果同一 user 不同 session, hash 同会得到同 version, 但用户感觉跟昨天不一样. 怎么 align?"** — 答: User-sticky 已用 user_id 不是 session. 但 user 跨 device 可能不同 cookie. 解决: hash on permanent user_id (DB id, not cookie). 同时记录 (user, prompt, version) 在 user profile, 跨 device 一致.

2. **"如果一个 prompt 同时 100 个 customer 用, 1 个 customer 用自己 variant. 我们怎么 do A/B 不污染 base?"** — 答: 这 customer 的 variant 自己 stream, 不参与 base A/B. Base A/B 拿剩 99 customer 数据. Variant 自己有 baseline + eval, customer 自己愿意 A/B 也可 (但 stat power 弱).

3. **"PM 想直接 prod edit prompt, 不走 eval gate, 怎么 govern?"** — 答: (a) UI-level role: PM 不能 edit tier-1, 只能 propose; (b) Tier-3 (experimental) 给 PM 直接 edit + auto-canary 1%; (c) Manager approval for tier-1 promote; (d) After-incident review: 如果 bypass 导致问题, 加 friction (force review). 平衡 friction vs speed.

4. **"prompts 在 LLM provider 端 cache (Anthropic prompt cache), 我们 rollback 后 cache 仍 stale, 怎么办?"** — 答: Anthropic prompt cache 是 server-side semantic cache. Rollback 改 prompt content → cache hash 变 → automatic miss + recompute. 5 min 内自然 propagate. 强制 invalidate: client SDK 加 cache_breaker hash on prompt change.

5. **"我们 prompt 用 Claude, 想 cross-test 同 prompt 在 GPT 上表现, 怎么 design?"** — 答: (a) prompt model-agnostic 设计 (无 Claude-specific 句法); (b) Eval golden 跑多 model 并存; (c) UI shows side-by-side: GPT-5.5 vs Claude Sonnet 4.6 vs Gemini 3 Pro on same prompt; (d) Per-prompt model recommendation (有些 prompt 在 Claude 强, 有些 GPT 强); (e) Allow per-tenant model choice if quality tied.

---

## ❌ 死路答法

1. **"git + PR review"** — PM 不会用, 慢, 不支持 runtime fetch.
2. **"YAML config in deploy"** — change 要 deploy, 不是 minute 改.
3. **"prompt in code"** — change = code release, 慢.
4. **"无 eval gate, deploy 直接 A/B"** — 1% canary 可能就 5% user 受害.
5. **"全 manual rollback"** — < 5 min 不可能 manual.
6. **"无 per-tenant"** — 失去 customization 价值.
7. **"无 audit"** — SOX 合规挂.
8. **"无 cost monitor"** — 新 prompt 长 50% 月费爆炸不知道.
9. **"binary on/off feature flag"** — 没 gradual rollout.
10. **"prompt 写 Jinja 太复杂"** — Jinja 是 industry standard, PM 学 30min 会用.

---

## ✅ 加分项

1. **Prompt as data, not code** — framework correctness
2. **4-layer eval gate (lint + golden + LLM-judge + human)** — production-grade
3. **Sticky user_id hash for A/B** — 真懂 UX
4. **Per-tenant variants via Jinja inheritance** — DRY + customizable
5. **5 auto-rollback triggers** — multiple signals
6. **Cache TTL 60s + active invalidation = < 30s rollback effect** — fast
7. **24h freeze post-rollback** — avoid flap
8. **Cost / latency in eval gate** — token cost runaway prevention
9. **Buy LangSmith + LaunchDarkly + Retool, build registry** — pragmatic build/buy
10. **Numbers 给得出来** (200M calls/day, $4K/month infra, $6 per eval, $5M/month cost runaway risk)

---

## 一句话总结

Prompt 生命周期不是 git, 是 **DB registry + Jinja templating + 4-layer eval gate + LangSmith eval + LaunchDarkly traffic split + sticky user A/B + 5-signal auto-rollback + per-tenant Jinja inheritance + immutable audit + per-prompt cost/quality dashboard** 的 ML ops + 产品 ops 混合系统.

---

## Cheat Sheet

```
Registry: Postgres + Redis (60s TTL)
  Tables: prompts, prompt_versions, prompt_assignments, prompt_audit_log
  Versioning: semver (MAJOR.MINOR.PATCH)
  Templating: Jinja2

Eval Gate (before promote):
  1. Lint:        schema, syntax, PII, length, model compat (1 sec)
  2. Golden:      50-200 (input, expected) regression check (5-30 min)
  3. LLM-judge:   Claude Opus 4.7 pairwise vs current (10-20 min)
  4. Human:       tier-1 mandatory, sampled (1-3 day async)
  5. Cost/latency: token usage + p95 latency (1 min)
  Pass criteria: ≥ 97% of baseline quality + < 10% cost overrun

Rollout Stages (tier-1):
  Canary 1% → 10% → 50% → 100% (24h+48h+48h observation)
Tier-3: 50% → 100% in 1 day

Traffic Split:
  Sticky: hash(user_id + prompt_name) % 100 vs cumulative pct
  Per-tenant override possible

Auto-Rollback Triggers:
  Error rate > 2× baseline 5 min
  p99 latency > 1.5× baseline 10 min
  Quality < baseline -5% 1h
  Refund > 1.2× baseline 1h
  Cost > 2× baseline 30 min
  CSAT < -5pp 24h

Rollback Action:
  1. Flip traffic 100% → prev version
  2. Invalidate Redis cache (active)
  3. Mark new as 'rolled-back'
  4. Audit + PagerDuty + Slack
  5. Effect within 30s, total < 5 min from trigger

Per-Tenant Variants:
  Jinja inheritance: variant extends base, overrides blocks
  Variant pool: 3-5 named variants (formal, casual, multilingual)
  Customer self-serve: parametrized only (variables)
  Hard custom: submit-request flow

Stack (build / buy):
  Registry:        Postgres + Redis (build, simple)
  Eval:            LangSmith (buy, ~$2K/m)
  Traffic split:   LaunchDarkly (buy, ~$1K/m)
  UI:              Retool (buy, ~$500/m)
  Observability:   Datadog + LangSmith traces

Cost (200 prompts, 200M calls/day):
  Infra: ~$4K/m
  Eval auto: $1200/m
  Per-prompt update eval: $6 each (auto), +$50 human review

Audit: 7yr retention, immutable, $0 storage (logs)

SLO:
  Time to promote new (tier-1): 1 week
  Time to rollback: < 5 min (target < 1 min for tier-1)
  Eval coverage: 100% prod prompts
```
