# 🟡 G22 · Tell me about making tradeoffs between quality and cost.

> **信号**: 工程判断 · 商业意识 · **hellointerview 报告数**: 2
> ⚠️ 标 [✏️] 的数字是占位, 背诵前换成你的真实数据.

## 🧠 这题在测什么

测你是否把 quality-cost 当曲线工程问题而非道德问题. 你的素材: 模型分层 + 推理优化 (简历硬技能).

## 📋 English Answer (背诵稿, ~60-90 秒)

For the BNPL chatbot, serving every turn with our largest model gave the best conversation quality — and an unsustainable cost curve at payment-customer scale. The naive frames were both wrong: "always use the best model" burns money on requests that don't need it; "use the cheap model" quietly degrades money-touching flows where errors are expensive.
I treated it as a routing problem on the quality-cost curve. We profiled quality-per-cost by request type, then tiered: a small fine-tuned model handles intent classification and routine turns — that's most of the volume; the large model is reserved for generation in complex or sensitive flows; and on the serving side I drove vLLM and SGLang optimization with memory-efficiency tuning, which lowered the cost of *every* tier rather than trading anything away [✏️ 成本数字核实].
The key design decision was *where quality is non-negotiable*: anything touching money — refund confirmation, dispute handling — never gets downgraded, regardless of load. Cost flexibility lives only in the tiers where errors are cheap to recover.
My framing: quality-cost isn't one knob, it's a portfolio. Engineer the frontier outward with serving optimization, then spend your quality budget where errors are irreversible.

## 🇨🇳 中文速记 (结构记忆)

全量大模型质量好但成本曲线不可持续; 当成 quality-cost 曲线上的路由问题: 小 fine-tuned 模型扛意图分类+常规轮次, 大模型只用于复杂/敏感生成; vLLM/SGLang+显存优化把整条曲线外推. 关键: 动钱流永不降级, 成本弹性只放在错误可恢复的层. 金句: quality-cost 是组合不是单旋钮.

## 🔁 高概率追问

**Q: How did you validate the small model was good enough?**

Shadow evaluation against the large model on production traffic per intent — tiers were assigned from measured quality deltas, not assumptions, and re-checked after every model update.
