## 💵 2026 年 LLM API 价格速查 (Google FDE 必背)

**为什么这页存在**: Google FDE 面试 cost math 是必考。你脱口而出 "1M tokens 大概多少钱" + 知道选哪个模型 routing, 加分明显。**面试场默认用 Gemini 3 Pro / Flash 量化** (Google FDE, 主场优势)。

**Last updated**: 2026-05-21

---

## 📊 主流 LLM 价格表 (per 1M tokens, USD)

| Model | Input | Output | 备注 |
|---|---:|---:|---|
| **Gemini 3 Pro** ⭐ | $2.00 | $12.00 | ≤200K context; 上 200K 翻倍 $4 / $18 |
| **Gemini 3 Flash** ⭐ | $0.50 | $3.00 | Pro 1/4 input 价 |
| **Gemini 3 Flash-Lite** | $0.10 | $0.40 | super cheap, batch |
| **Claude Opus 4.7** | $5.00 | $25.00 | Apr 2026; 新 tokenizer 多出 ~35% token |
| **Claude Sonnet 4.6** | $3.00 | $15.00 | mid-tier mainstream |
| **Claude Haiku 4.5** | $1.00 | $5.00 | cheap Claude |
| **GPT-5.5** | $5.00 | $30.00 | Apr 2026 涨价: 比 GPT-5 翻 2x |
| **GPT-5.5 mini** | $1.25 | $7.50 | |
| **GPT-5.4** | $2.50 | $15.00 | 仍 available 作 backup |
| **GPT-5.4 mini** | $0.75 | $4.50 | |
| **GPT-5.4 nano** | $0.10 | $0.40 | super cheap |
| **o-series (reasoning)** | $15+ | $60+ | high-reasoning, 高价 |

⭐ = Google FDE 面试**首选 quantization 基准**

---

## 🎯 5x output:input 是普遍规律

> Anthropic / Google 都保持 output 是 input 5x 价格。OpenAI GPT-5.5 是 6x。
> 心算公式: input price × 5 ≈ output price (Claude / Gemini)

---

## 💰 常用 cost 心算 (Gemini 3 Pro 基准)

### 单次 call 大概多少钱

| Context size | Input cost (Gemini 3 Pro) | Output cost (假设 500 token output) |
|---|---|---|
| 1K tokens | $0.002 | $0.006 |
| 10K tokens | $0.02 | $0.006 |
| 100K tokens | $0.20 | $0.006 |
| 128K tokens | $0.26 | $0.006 |
| 200K tokens | $0.40 | $0.006 |
| **500K tokens** (above 200K threshold!) | $2.00 (at $4/1M) | $0.009 (at $18/1M) |
| **1M tokens** (full Gemini Pro context) | $4.00 (at $4/1M) | $0.009 |

### Per-用户成本估算

| 用户行为 | 估算 cost |
|---|---|
| Chat 用户 1 turn (~2K context + 500 output) | ~$0.01 (Gemini Pro) / ~$0.003 (Flash) |
| 用户 1 个 session (~10 turn, 50K accumulated) | ~$0.10 (Pro) / ~$0.03 (Flash) |
| 用户 1 天 (~20 sessions) | ~$2 (Pro) / ~$0.60 (Flash) |
| 用户 1 月 (active) | ~$60 (Pro) / ~$18 (Flash) |
| Agent task (50 LLM calls + 10 tool calls) | ~$0.50-2 |

### Per-feature daily cost (10K QPS workload)

| Setup | Daily cost |
|---|---|
| 100% Gemini 3 Flash, 2K context avg | ~$8,000 / day |
| 100% Gemini 3 Pro, 2K context avg | ~$32,000 / day |
| **Hybrid: 80% Flash + 20% Pro** | ~**$12,500 / day** |
| 100% Claude Opus 4.7 | ~$80,000 / day |
| Hybrid with cache (50% hit) | ~$6,000 / day |

---

## 🎚 Cost-aware routing 3-tier 模板

面试场默认这个 template:

```python
async def route_model(query, complexity_score):
    if complexity_score < 0.3:
        # 简单 query (FAQ / lookup / 短答) — 90% 流量
        return 'gemini-3-flash'        # $0.50/$3 per 1M
    elif complexity_score < 0.7:
        # 中等 query (reasoning / multi-step) — 8% 流量
        return 'gemini-3-pro'          # $2/$12 per 1M
    else:
        # 复杂 query (long context / hard reasoning) — 2% 流量
        return 'claude-opus-4.7'       # $5/$25 per 1M
        # or 'gpt-5.5' for OpenAI-strong tasks
```

**Cost weighted average** (80/15/5 split):
- Flash: 0.8 × $0.50 = $0.40
- Pro: 0.15 × $2 = $0.30
- Opus: 0.05 × $5 = $0.25
- **Blended input cost: ~$0.95 per 1M** (vs $5 if 100% Opus)
- **Savings: ~80% 的成本 reduction**, quality on average 接近 Pro

---

## 🧊 Caching / batch / prefix 降本

不同 provider 有不同 discount:

| Provider | Mechanism | Discount |
|---|---|---|
| **Anthropic** | Prompt caching | Cached input **90% off** (e.g., Opus cached input $0.50/1M) |
| **Anthropic** | Batch API | **50% off** standard rates |
| **Google** | Implicit cache (auto) | up to **75% off** input |
| **Google** | Batch | **50% off** |
| **OpenAI** | Cached input | **50% off** typically |
| **OpenAI** | Batch | **50% off** |
| **OpenAI** | Flex (slower) | **50% off** standard |
| **OpenAI** | Priority (faster) | **2.5x** standard ($$$) |

**面试用法**:
> "For repeated agent loop with shared system prompt, Anthropic prompt caching gives 90% off cached input — so a 50K-token system prompt costs $2.50 first call but $0.25 every subsequent call. Combined with batch discount, sustained workload runs ~10-20% of peak rates."

---

## 🏷 vs 自托管 (vLLM / SGLang)

| Approach | Effective $/1M tokens | Setup cost |
|---|---|---|
| Gemini 3 Flash (API) | $0.50 / $3 | $0 |
| Self-host Llama 4 70B (vLLM, H100) | ~$0.20-0.50 | GPU + ops time |
| Self-host Mistral / Mixtral | ~$0.10-0.30 | GPU + ops time |

**心算 break-even**:
- 自托管 1 个 H100 ($3/hr) × 5K tokens/sec = ~$0.0002/1K = $0.20/1M raw compute
- 加 ops overhead (model 维护 / monitoring / quality eval): ~$0.30-0.50/1M
- **Crossover**: 月消耗 > $30K LLM cost 才值得自托管

---

## 📏 Context window 上限 (2026)

| Model | Standard context | Max context |
|---|---|---|
| Gemini 3 Pro | 1M tokens | 2M experimental |
| Gemini 3 Flash | 1M tokens | 1M |
| Claude Opus 4.7 | 200K | 1M (beta) |
| Claude Sonnet 4.6 | 200K | 1M (beta) |
| GPT-5.5 | 400K | 1M (with cache) |
| GPT-5.4 | 200K | 400K |

**Trend**: 1M context 成主流, 但 cost 线性增长, 不能滥用. **Hybrid (RAG + long-context) 仍是 production 默认.**

---

## 🎤 面试常用 quotable 句子

把以下背下来, 面试现场直接说:

> **On cost-aware routing**: "我们 default to Gemini 3 Flash at $0.50/1M input — 90% query 走它. Complex query escalate to Gemini 3 Pro at $2/1M. 真正难的少量 query 升 Claude Opus 4.7 at $5/$25. Blended cost 大概在 $0.7-1 per 1M token, 比纯 flagship 省 80%."

> **On context size**: "128K context call cost about $0.26 with Gemini 3 Pro — not nothing, but 100 turn 累积也才 $26. Long-context viable for high-value workload."

> **On caching**: "With Anthropic prompt caching, agent loop sharing 50K system prompt — first call costs $2.50, every subsequent only $0.25 — 10x reduction on repeated prefix."

> **On break-even self-host**: "Self-host break-even 月 LLM 消耗 $30K+. Below that, API cheaper than GPU ops overhead. Above that, vLLM / SGLang 自托管 ROI 明显, 加上 latency / privacy 收益."

---

## 🚨 价格变动 watch list

| 模型 | 变化方向 | 警觉点 |
|---|---|---|
| GPT-5.5 | 比 GPT-5 涨 2x (Apr 2026) | OpenAI 走高端 / 高 margin 路线 |
| Claude Opus 4.7 | 单价没变 | 但 tokenizer 改, 同样文本多 35% token, **隐性涨价** |
| Gemini 3 Pro | 没变 | 维持 $2/$12 价格优势 |
| Gemini 3 Flash | 没变 | $0.50/$3 — 大部分 production 主力 |

**Trend**: API 价不再单边降. 不同厂商 differentiate by **price tier / context / caching / batch**.

---

## Cheat Sheet (1 张图)

```
💵 2026 LLM 价 (Input / Output per 1M tokens)

Cheap tier:
  Gemini 3 Flash      $0.50 / $3
  Claude Haiku 4.5    $1 / $5
  GPT-5.4 mini        $0.75 / $4.50

Mid tier:
  Gemini 3 Pro        $2 / $12        ← Google FDE 默认基准
  Claude Sonnet 4.6   $3 / $15
  GPT-5.4             $2.50 / $15

Flagship:
  Claude Opus 4.7     $5 / $25
  GPT-5.5             $5 / $30
  Gemini 3 Pro (>200K)$4 / $18

Routing template (Google FDE):
  90% → Gemini 3 Flash
  9% → Gemini 3 Pro
  1% → Claude Opus 4.7

Cost levers:
  Prompt cache: Anthropic 90% off
  Batch: 50% off (all)
  Self-host break-even: $30K+/month

Cost math 心算:
  128K context @ Gemini 3 Pro = $0.26 in
  1M context @ Gemini 3 Pro (>200K) = $4 in
  Chat turn (2K) = ~$0.01
  Session (10 turn) = ~$0.10
```
