# 🍎 HM Q27 · "The team serves Greater China and needs Chinese LLM work. What's different about training/evaluating LLMs in Chinese?"

> **类别**: Fit / Technical depth (🟢 差异化强项) · **考点**: 是否真懂中文 LLM 的技术特殊性 (不是 "我会说中文" 而已); 能否把 native 中文 + 7 市场多语 post-training 经验变成不可替代的优势 · ⚠️ [✏️] 数字背前替换成真实值

## 🧠 这题在测什么 / 面试官想看到

这是 Gao 的**主场题**, 也是他相对其他候选人最难被替代的差异点 — JD 明确要 "LLM in Chinese for Greater China + fluent Chinese"。面试官想验证两件事: (1) 你是否真懂中文 LLM 在**技术层面**的特殊性 (tokenization / benchmark / 数据 / code-switching), 而不是只会 "我母语中文"; (2) 你有没有**真做过**多语 post-training, 能把经验落到具体决策。强答案 = 4-5 个具体技术差异, 每个都带 "所以训练/评估时要怎么做", 再用他 7 市场 (含 CN) 的真实经验背书。弱答案 = "中文是另一种语言, 数据少一点" 这种泛泛。陷阱: 把文化/语言常识当技术答案 → 要落到 tokenization、eval、数据这些工程层。

## 📋 English Answer (背诵稿, 主答 ~90 秒 + 可延伸)

"This is the part of the role I'm probably most differentiated on — Chinese is my native language, and on the voice agent I owned multilingual post-training across seven markets including Mainland Chinese, so I've hit these issues in production, not in theory. Let me give the concrete technical differences, because 'it's a different language' isn't the real answer.

**First, tokenization.** Chinese has no spaces and no word boundaries, and a single character can be a word or part of one. Tokenizers built English-first fragment Chinese badly — you burn far more tokens per unit of meaning, which hurts both latency and the effective context window. So a model's tokenizer vocabulary coverage for Chinese is something I'd check before anything else; it silently caps your quality and cost ceiling.

**Second, evaluation.** You can't trust English benchmarks translated into Chinese — translation artifacts leak and you end up measuring the wrong thing. Chinese needs native benchmarks like C-Eval and CMMLU that test Chinese knowledge and reasoning directly. And for a customer-facing agent, generic benchmarks aren't enough anyway — I'd build domain-specific Chinese eval sets from real interactions, the same eval-harness approach I used on the voice agent, just grounded in Chinese transcripts.

**Third, data characteristics.** Chinese has Simplified versus Traditional — which matters enormously for Greater China, since the mainland is Simplified and Taiwan and Hong Kong are Traditional, and they're not interchangeable. There's also a huge register gap between formal written Chinese and how people actually talk, which matters a lot for a conversational agent. So data curation isn't just 'get Chinese text' — it's getting the *right* variety and register for the target users.

**Fourth, code-switching.** Real Chinese users mix in English constantly — product names, technical terms, English loanwords mid-sentence. The model has to handle that gracefully, and the eval has to include it, or you ship something that breaks the moment a user says an English brand name in a Chinese sentence. I dealt with exactly this across my markets.

So my honest claim is: I don't just speak Chinese — I've run the post-training and eval loop where these issues are the difference between a model that feels native and one that feels translated."

延伸: "And it's not only Chinese — doing this across Japanese and Korean too taught me a transferable lesson: never assume an English-first pipeline generalizes. You re-examine tokenization, benchmarks, and register for each language, every time."

## 🇨🇳 中文完整版 (口播稿, 与英文对应)

"这大概是整个岗位里我最有差异化的一块 — 中文是我的母语, 而且在 voice agent 上, 我 own 了跨七个市场的多语 post-training, 其中就包括大陆中文, 所以这些问题我是在 production 里真撞过的, 不是纸上谈兵。我直接讲具体的技术差异, 因为 '中文是另一种语言' 并不是真正的答案。

**第一, tokenization。** 中文没有空格、没有词的边界, 而且一个字可以是一个词, 也可以只是一个词的一部分。那些 English-first 设计的 tokenizer 会把中文切得很碎 — 你为每一个单位的语义烧掉多得多的 token, 这同时伤 latency 和有效的 context window。所以一个模型的 tokenizer 对中文的词表覆盖, 是我会在做任何别的事情之前先去查的东西; 它会悄无声息地锁死你质量和成本的天花板。

**第二, evaluation。** 你不能相信把英文 benchmark 翻译成中文的那种东西 — 翻译的痕迹会泄漏进来, 你最后测的是错的东西。中文需要原生的 benchmark, 比如 C-Eval 和 CMMLU, 它们直接考中文的知识和推理。而且对一个面向客户的 agent 来说, 光有通用 benchmark 本来也不够 — 我会从真实的交互里, 构建领域专属的中文 eval set, 就是我在 voice agent 上用的那套 eval-harness 方法, 只不过这次扎根在中文的 transcript 上。

**第三, 数据特性。** 中文有简体和繁体的区别 — 这对 Greater China 极其重要, 因为大陆是简体, 而台湾和香港是繁体, 它们不是可以互换的。另外, 正式的书面中文, 和人们实际说话的方式之间, 还有一个巨大的 register (语域) 落差, 这对一个对话式的 agent 影响很大。所以数据策展不只是 '搞到中文文本' 而已 — 是要拿到对目标用户来说**对的那个变体和语域**。

**第四, code-switching (混码)。** 真实的中文用户会不停地往里掺英文 — 产品名、技术术语、句子中间冒出来的英文外来词。模型必须能优雅地处理这个, 而且 eval 里必须包含这种情况, 否则你 ship 出去的东西, 用户一在中文句子里说一个英文品牌名就崩了。这个我在我那几个市场里正好处理过。

所以我诚实的说法是: 我不只是会说中文 — 我跑过那个 post-training 加 eval 的 loop, 而在那里, 这些问题正是 '一个感觉像母语的模型' 和 '一个感觉像翻译腔的模型' 之间的差别。"

延伸: "而且不只是中文 — 在日文和韩文上也做过这一套, 教会了我一个可迁移的教训: 永远不要假设一个 English-first 的 pipeline 能自动泛化。每一种语言, 你每次都得重新审视它的 tokenization、benchmark 和 register。"

## 🇨🇳 中文要点 (理解 + 记忆骨架)

- **开场锁定差异化**: native 中文 + voice agent 7 市场 (含 CN) **真做过** multilingual post-training → production 里踩过, 不是理论。
- **四个技术差异** (背熟, 每个都要带 "所以怎么做"):
  1. **Tokenization**: 中文无空格无词界, 一字可成词。English-first tokenizer 把中文切碎 → 每单位语义烧更多 token → 伤 latency + 有效 context。**上手先查 tokenizer 对中文的词表覆盖**, 它悄悄锁死质量和成本天花板。
  2. **Evaluation**: 别信英文 benchmark 翻译版 (翻译痕迹泄漏, 测错东西)。用 native benchmark **C-Eval / CMMLU**。面向客户的 agent 还要从**真实中文 transcript** 建 domain eval set (复用 voice agent 的 eval-harness 方法)。
  3. **Data characteristics**: **简体 vs 繁体** — 对 Greater China 极重要 (大陆简体 / 台港繁体, 不可互换)。还有**书面语 vs 口语 register 鸿沟**, 对话 agent 尤其重要。数据策展不是 "搞到中文", 是搞到**对的变体和语域**。
  4. **Code-switching**: 真实中文用户狂混英文 (产品名/技术词/外来词)。模型要优雅处理, eval 必须包含 code-switching, 否则用户一说英文品牌名就崩。我在多市场里正好处理过。
- **收尾**: **"我不只是会说中文 — 我跑过那个让模型从'翻译腔'变'母语感'的 post-training + eval loop"**。
- 延伸: 不止中文 — JP/KR 也做过, 学到可迁移原则: **永远别假设 English-first pipeline 能泛化, 每种语言都要重新审视 tokenization/benchmark/register**。
- 记忆钩子: **"分词 / 评估(C-Eval CMMLU) / 数据(简繁+口语) / 混码 — 母语感 vs 翻译腔"**。

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: If you found a base model's tokenizer handled Chinese poorly, what would you actually do?**
**中**: 如果你发现一个 base model 的 tokenizer 处理中文很糟, 你实际会怎么做?
"It depends on how locked-in the tokenizer is. If I control pre-training, vocabulary expansion for Chinese is the clean fix. If I'm post-training on a fixed base — which is the realistic case — I can't change the tokenizer, so I'd quantify the damage first: measure tokens-per-character on real Chinese traffic and see how much context and latency it's actually costing. If it's severe, that becomes an argument for choosing a different base model, ideally one trained Chinese-inclusive from the start. The judgment is knowing when it's a tuning problem versus a base-model-selection problem."
> 🇨🇳 这取决于这个 tokenizer 被锁死到什么程度。如果我能控制 pre-training, 那对中文做 vocabulary expansion (词表扩展) 就是那个干净的修法。如果我是在一个固定的 base 上做 post-training — 这才是现实里的情况 — 我没法改 tokenizer, 那我会先把损害量化出来: 在真实的中文流量上量 tokens-per-character, 看它实际上吃掉了多少 context 和 latency。如果很严重, 那这就成了一个 '换一个 base model' 的论据, 最好是一个从一开始就把中文包含进去训练的模型。这里的判断力, 在于知道什么时候它是一个 tuning 的问题, 什么时候它是一个 base-model-selection 的问题。

**Q: How would you build a Chinese eval set you actually trust for a customer agent?**
**中**: 你会怎么给一个面向客户的 agent 建一个你真正信得过的中文 eval set?
"Three layers. Public native benchmarks like C-Eval and CMMLU for general capability — a sanity floor. Then a domain set built from real Chinese customer interactions, labeled with the outcomes we care about. Then a targeted adversarial slice: Simplified and Traditional, heavy code-switching, and colloquial register, because those are exactly the cases generic benchmarks miss. I'd weight the domain and adversarial layers highest, because that's what actually predicts production behavior — that's the lesson from building the voice-agent harness."
> 🇨🇳 三层。公开的原生 benchmark, 像 C-Eval 和 CMMLU, 用来看通用能力 — 这是一个 sanity 的底线。然后是一个从真实中文客户交互里建出来的 domain set, 用我们在乎的那些结果去打标。再然后是一个有针对性的 adversarial 切片: 简体和繁体、大量的 code-switching、还有口语的 register, 因为这些恰恰是通用 benchmark 会漏掉的情况。我会给 domain 层和 adversarial 层最高的权重, 因为那才是真正能预测 production 行为的东西 — 这是我搭 voice-agent harness 时学到的教训。

**Q: Simplified vs Traditional — is that really a model problem or just a conversion step?**
**中**: 简体 vs 繁体 — 这真的是一个模型问题, 还是只是一个转换的步骤?
"It's more than conversion. Script conversion handles the characters, but Traditional-using regions — Taiwan, Hong Kong — also differ in vocabulary, phrasing, and which English terms get borrowed. A naive Simplified-to-Traditional conversion produces text that's technically Traditional but reads as mainland-flavored and slightly off to a Taiwan user. For a customer-facing agent where trust matters, I'd treat the Traditional variants as their own register in both data and eval, not a post-processing afterthought."
> 🇨🇳 它不止是转换。字形转换处理的是字, 但用繁体的地区 — 台湾、香港 — 在词汇、说法、以及借用哪些英文词上也都不一样。一个 naive 的简转繁会产出一种技术上是繁体、但读起来带着大陆味、对一个台湾用户来说有点 '不对劲' 的文本。对一个信任很重要的、面向客户的 agent 来说, 我会把繁体的变体当成它们自己的一个 register, 在数据和 eval 里都这么对待, 而不是当成一个事后的 post-processing。

**Q: Did you measurably improve Chinese performance on your agent, or are these general principles?**
**中**: 你在你的 agent 上有可度量地提升过中文的表现吗, 还是说这些都是一般性的原则?
"Both — but let me be precise about what I can claim. I ran the multilingual post-training and eval loop across seven markets including Mainland Chinese, and Chinese was one of the markets where we moved the automation and conversion metrics [✏️ 核实 中文市场具体指标]. I'd rather state it as 'Chinese was an in-scope production market I owned end to end' than quote a per-language number I can't back precisely on the spot."
> 🇨🇳 两者都有 — 但让我把我能 claim 的东西讲精确。我跑了那个跨七个市场、包括大陆中文的多语 post-training 和 eval loop, 而中文正是我们把 automation 和 conversion 指标推动起来的市场之一 [✏️ 核实 中文市场具体指标]。比起去引一个我当场没法精确背书的 per-language 数字, 我更愿意把它说成 '中文是一个我端到端 own 的、in-scope 的 production 市场'。

## ⚠️ 边界 & 红线 (honest limits + what NOT to say)

- **别把 "我母语中文" 当答案的全部**。这题考技术深度, 语言能力只是背书。必须落到 tokenization/eval/data/code-switching 这些工程层。
- **简繁问题对 Greater China 是政治敏感区** — 只讲技术事实 (大陆简体、台港繁体、词汇/用法有别), 客观中性, 不评论政治。框成 "用户信任 + 工程正确性" 问题。
- 中文市场的具体指标用 [✏️ 核实], 被钻时诚实降级为 **"中文是我端到端 own 的 in-scope 市场"**, 别硬编 per-language 数字。
- benchmark 名字 (C-Eval / CMMLU) 要说得准; 如果记不牢就说 "native Chinese benchmarks that test Chinese knowledge directly", 别说错名字露怯。
- 别夸张成 "中文 LLM 我全懂"。框成 "我在 production 里 own 过中文 post-training+eval, 知道坑在哪"。

## ✅ 加分钩子 (主动抛, steer 到强项)

- **"production 里 own 过, 不是理论"** — 这是这题最强的底气, 反复用真实的 7 市场 (含 CN) 经验背书每一个技术点。这是其他候选人 (尤其非母语/没做过多语 post-training 的) 给不出的。
- **eval-harness 方法可直接复用** — 主动点出 "我给 voice agent 建 eval harness 的那套方法, 换成中文 transcript 就能用", 把过往经验变成对这个岗位的即插即用能力, 直击 JD 的 "LLM eval"。
- **多语泛化的元能力** — 主动抛 JP/KR 经验和 "永不假设 English-first pipeline 泛化" 这条原则, 展示你不止会中文, 而是有一套**系统性处理任意语言**的方法论, 这对一个多市场团队价值极高。
- **code-switching + 口语 register** — 主动提这两个细节, 体现 attention to detail (Apple 看重), 也暗示你懂 conversational/voice 场景的真实难点 (呼应 voice agent 背景)。
