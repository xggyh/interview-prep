# 🍎 HM Q20 · How would you cut latency and cost for an LLM serving system?

> **类别**: GenAI / ML Concepts (🟢 最强主场) · **考点**: streaming · KV-cache · prefix caching · speculative decoding · continuous batching · model cascade/routing · quantization — 全要落到取舍 + 真实 vLLM/SGLang 工作 · ⚠️ [✏️] 数字背前替换成真实值

## 🧠 这题在测什么 / 面试官想看到

这是 Gao **最强的题**，也是 JD 的核心（latency / cost / customer experience）——**要主动把面试往这里引**。面试官想看你不是背名词，而是**先建框架**（先分清是 TTFT 还是 throughput/cost 问题、prefill-bound 还是 decode-bound），再对症下药，每个手段都说清**取舍和代价**。强答案：一个分层菜单 + 知道每招治什么 + 真实做过 vLLM/SGLang。弱答案：报一串 buzzword 不讲取舍、不分场景。陷阱：把所有手段一股脑堆上而不区分「降首字延迟」vs「降单 token 成本」vs「提吞吐」——它们的招不一样，有的还互相打架（如激进量化省成本但可能掉质量、speculative decoding 降延迟但费算力）。

## 📋 English Answer (背诵稿, 主答 ~90 秒 + 可深挖)

"First I'd frame it, because 'latency and cost' are actually three different problems and they don't share the same fixes. **Time-to-first-token** is dominated by the **prefill** — processing the prompt. **Per-token latency after that** is the **decode** loop, which is memory-bandwidth bound. And **cost** is really about **throughput per GPU** — how many tokens per dollar. So I'd ask which one hurts, then pull the right levers.

**For perceived latency — the cheapest win first: streaming.** Stream tokens as they're generated so the user sees output in a few hundred milliseconds instead of waiting for the full response. It doesn't make the model faster, it makes it *feel* fast, and for a conversational agent that's huge.

**For repeated work — caching.** Two kinds. **KV-cache** is table stakes — you cache the attention keys/values so each new token doesn't recompute the whole sequence. Beyond that, **prefix caching**: if many requests share a prompt prefix — a long system prompt, a shared instruction, a common document — you compute that prefix's KV once and reuse it across requests. In a customer agent with a big fixed system prompt, that cuts a lot of redundant prefill. SGLang's RadixAttention is built exactly for this, and it's something I worked with directly.

**For throughput and cost — continuous batching.** Instead of static batches that wait for the slowest sequence, you batch at the *token* level — finished sequences leave, new ones join every step, so the GPU stays saturated. This is the single biggest cost lever in production serving, and it's core to how vLLM and SGLang get their throughput. vLLM's **PagedAttention** also stops you wasting memory on over-allocated KV, which lets you run bigger batches — more memory efficiency, more throughput, lower cost per token.

**For decode speed — speculative decoding.** A small draft model proposes several tokens, the big model verifies them in one pass; when the draft is right, you get multiple tokens per big-model step. Lower latency *and* the same quality — the trade is extra compute and a small draft model to maintain.

**For cost structurally — quantization and routing.** Quantize weights and KV-cache — 8-bit, 4-bit — to shrink memory and speed up the bandwidth-bound decode, watching quality on eval as you go down. And **model cascade / routing**: don't send every request to the biggest model. Route easy queries to a small cheap model, escalate only the hard ones to the large one. Most traffic is easy, so this is a large cost cut for little quality loss — if your router is good.

This is the work I actually did — inference acceleration on NVIDIA GPUs with **vLLM and SGLang**, plus memory-efficiency tuning. And on the voice agent latency was existential, so I drove the ASR/TTS streaming upgrades — packetization and interruption handling — to get time-to-first-audio down, which is the same streaming-and-pipelining discipline applied to the speech stack."

(可延伸 — 桥 Apple) "All of this maps to Apple on-device, just with a different constraint surface. On a GPU I'm optimizing HBM and dollars-per-token; on device I'm optimizing **unified memory, power, and model size**. The exact same levers reappear: aggressive **quantization** — Apple uses ~2-bit weights and 8-bit KV-cache — **KV-cache sharing** to cut prefill memory, and **small task-specific models/adapters** instead of one big model, which is the on-device version of model routing. Same engineering discipline, the cost function just changes from GPU spend to battery and RAM."

## 🇨🇳 中文要点 (理解 + 记忆骨架)

**先建框架（别直接报菜名）**：「latency + cost」其实是**三个问题**，招不通用：
- **TTFT（首字延迟）** ← 由 **prefill**（处理 prompt）主导。
- **后续单 token 延迟** ← **decode** 循环，**内存带宽 bound**。
- **成本** ← **每卡 throughput**（每块钱多少 token）。
先问「哪个疼」，再对症。

**分层菜单（每招配取舍）**：
1. **感知延迟最便宜的赢 → streaming**：边生成边吐，几百 ms 见字。不是更快，是「感觉快」，对话场景巨大收益。
2. **重复计算 → 缓存**：
   - **KV-cache**（基本盘）：缓存 attention k/v，每个新 token 不重算整序列。
   - **prefix caching**：多请求共享前缀（长 system prompt / 共享指令 / 公共文档）→ 前缀 KV 算一次复用。SGLang **RadixAttention** 专为此，我亲手用过。
3. **吞吐/成本 → continuous batching**：token 级批处理，完成的走、新的随时进，GPU 不空转。**生产最大成本杠杆**，vLLM/SGLang 核心。vLLM **PagedAttention** 还避免 KV 过度分配浪费显存 → 更大 batch → 更高吞吐 → 更低单 token 成本。
4. **decode 速度 → speculative decoding**：小 draft 模型提议多 token，大模型一次验证；猜对就一步多 token。降延迟 + 不掉质量，代价是额外算力 + 维护小 draft。
5. **结构性降本 → 量化 + 路由**：
   - 量化权重 + KV-cache（8/4-bit）缩内存、加速带宽 bound 的 decode，**边降边看 eval 质量**。
   - **model cascade/routing**：简单 query → 小便宜模型，只有难的升级到大模型。大多数流量简单 → 大幅降本、质量损失小（前提 router 好）。

**真做过**：NVIDIA GPU 上 vLLM + SGLang 推理加速 + 显存调优。voice agent 延迟是生死线 → 我主导 ASR/TTS streaming 升级（packetization + 打断处理）压低首字音频时间 = 同一套 streaming/pipelining 用在语音栈。

**桥 Apple**：同样的杠杆换约束面——GPU 上优化 HBM/每 token 成本；端侧优化 **unified memory / 功耗 / 模型大小**。激进量化（Apple ~2-bit 权重 + 8-bit KV）、KV-cache sharing 降 prefill、**小任务模型/adapter 替代大模型 = 端侧版 routing**。

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: Prefill-bound vs decode-bound — how do you tell, and does it change your fix?**
"Long prompt, short output → prefill-bound; the win is prefix caching and faster prompt processing. Short prompt, long generation → decode-bound, which is memory-bandwidth limited, so the wins are quantization, speculative decoding, and bigger batches. I'd profile actual TTFT and inter-token latency to know which regime I'm in before optimizing — optimizing the wrong half wastes effort."

**Q: How does continuous batching actually help latency, not just throughput — doesn't batching add latency?**
"It's a throughput-first technique, and naively bigger batches add queueing latency. The reason it still wins on latency in practice is that token-level scheduling means a request doesn't wait for a whole static batch to drain before joining — it joins on the next step. So you get high GPU utilization without the head-of-line blocking of static batching. There's still a batch-size knob that trades p99 latency against throughput, and I'd tune it to the SLA."

**Q: Speculative decoding — when does it *not* help?**
"When the draft model's acceptance rate is low — if the small model rarely agrees with the big one, you've paid for draft compute and verification and gained little. It shines on predictable text and a well-matched draft. On hard, high-entropy generation the speedup shrinks. So it's a measured bet per workload, not a free win."

**Q: How far can you quantize before it hurts? How do you decide?**
"Eval-driven, always. I take the model down — 8-bit is usually nearly free, 4-bit needs checking, lower needs care — and watch task metrics, not perplexity alone, because quality can fall off a cliff non-linearly on the tasks you care about. QAT (quantization-aware training) buys you more headroom than post-training quantization, which is exactly why Apple can run ~2-bit on device — they train for it rather than bolt it on after."

**Q: You have one big model serving mixed traffic. Walk me through cutting cost 50%.**
"First, profile the traffic mix. Then in order of leverage: turn on continuous batching and prefix caching if not already — usually the biggest, lowest-risk wins. Then route: classify easy vs hard and send the easy majority to a smaller model. Then quantize the serving model as far as eval allows. I'd land the cut from batching+caching+routing first because they don't touch quality, and only lean on quantization to the degree eval says is safe. I'd verify each step against latency *and* quality so I'm not trading a cost win for a customer-experience loss."

**Q: Which of these would you reach for first on Apple's on-device stack?**
"Quantization and small task-specific models, because the binding constraint on device is memory and power, not GPU dollars. Then KV-cache sharing to cut prefill memory — Apple reports meaningful memory and prefill savings from it. Streaming still matters for perceived latency. Continuous batching matters less on a single-user device — that's a server-side throughput lever — which is a good example of *matching the technique to the constraint* rather than applying all of them reflexively."

## ⚠️ 边界 & 红线 (honest limits + what NOT to say)

- 别一口气报 7 个 buzzword 不分场景——**先建「TTFT / 单 token 延迟 / 成本」框架**再对症，这是和初级答案的分水岭。
- 别把手段说成全是免费午餐——主动讲代价：量化掉质量风险、speculative decoding 费算力、batching 加排队延迟。
- continuous batching 别讲成「纯降延迟」——它是 throughput-first，要能解释它为什么也能帮延迟（无 head-of-line blocking）。
- 如果被钻进 PagedAttention / RadixAttention / 内核实现的逐行细节超出深度，老实说「我从 serving 行为和显存效果理解它们，用过但没逐行读 kernel」——诚实划边界在 Apple 加分。
- 端侧别硬套 server 手段——主动说 continuous batching 在单用户设备意义不大，体现「按约束选招」。

## ✅ 加分钩子 (主动抛, steer 到强项)

- **主动把面试引到这题**——这是 Gao 最强 + JD 最核心（latency/cost/CX）。开头就用「这其实是三个问题」的框架立刻拉开档次。
- 把 **vLLM + SGLang 亲手做推理加速/显存调优** 当锚反复落地，并点 **RadixAttention prefix caching / PagedAttention**。
- 用 **voice agent ASR/TTS streaming（packetization + 打断 + 首字音频）** 证明你把 serving 优化也用在语音栈——直接命中 JD「voice/STT/TTS a plus」。
- 收尾必抛 **on-device 同构桥**（2-bit QAT + 8-bit KV + KV-cache sharing + 小模型 = 端侧 routing），把最强项接到 Apple 的真实约束面，回应 Q26 那条反杀线。
