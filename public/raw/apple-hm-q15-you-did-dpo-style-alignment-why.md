# 🍎 HM Q15 · You did DPO-style alignment — why DPO over PPO? Where did the preference data come from?

> **类别**: GenAI / ML Concepts · **考点**: DPO vs PPO 取舍 + preference data 来源 + 与 SFT 的边界 · ⚠️ 这是你较扎实的一端,但仍要诚实标注 data 来源 · [✏️] 数字背前替换成真实值

## 🧠 这题在测什么 / 面试官想看到

承接 Q14,落在你**较扎实的一端** (DPO/preference)。面试官想看三件事:(1) 你懂不懂 **DPO vs PPO 的真实取舍** (不是"DPO 更简单"这种表面话),(2) 你的 **preference data 从哪来** —— 这最容易暴露"到底是不是真做过",(3) 你分不分得清 **SFT 和 DPO 各干什么**。强答:DPO 去掉 reward model + online rollout,直接在 preference 上优化,更稳更省,适合合规场景;data 来源讲得具体且诚实。弱答:把 DPO 说成 PPO 的简化版还说不清差在哪,或 data 来源含糊。

## 📋 English Answer (背诵稿, 主答 ~60-90 秒 + 可延伸)

"Three parts: why DPO, where the data came from, and how it sits relative to SFT.

**Why DPO over PPO.**
- PPO is the classic RLHF recipe, but it has three moving parts: train a separate reward model, run online rollouts sampling from the policy, then do the PPO update with a value model.
- That's a lot of machinery — a reward model that can be gamed, online sampling that's expensive and unstable, careful tuning to avoid collapse.
- DPO collapses that: it skips the explicit reward model and the rollouts entirely, and optimizes the policy *directly* on preference pairs with a simple classification-style loss, while a KL term keeps it close to the reference model.
- For my setting — a compliance-sensitive, money-touching agent — that stability, and not having a reward model I'd have to defend, mattered more than the last bit of performance ceiling PPO might offer. Fewer things that can go wrong in production.

**Where the preference data came from.** Pairs — a preferred and a rejected response for the same context. Sources [✏️ 核实 — 据实填]:
- Model-generated candidate pairs ranked by human reviewers, including ops / domain experts who know what a compliant, effective collection turn looks like.
- Signals harvested from production — where one response led to resolution and another didn't.
- Some LLM-as-judge ranking for scale on the easier comparisons, with humans on the high-stakes ones.
- The point: the preference signal encoded *our* notion of a good turn — compliant, on-tone, effective — not a generic helpfulness score.

**Relative to SFT.**
- They do different jobs. SFT teaches *format and baseline behavior* — how to conduct the dialogue, call tools, stay in the multilingual register.
- DPO then *sharpens* it toward preferred behavior on axes SFT can't easily express — tone, compliance, picking the better of two plausible replies.
- You need SFT first — DPO on a model that can't do the task is polishing nothing."

*(可延伸:)* "And it's iterative — that's the eval-driven loop. Train DPO, evaluate, find the failure modes, collect new preference pairs targeting exactly those failures, retrain. The preference set grows toward the model's *current* weaknesses; static preference data goes stale as the model changes."

## 🇨🇳 中文完整版 (口播稿, 与英文对应)

"三块：为什么用 DPO、data 从哪来、以及它跟 SFT 是什么关系。

**为什么用 DPO 而不是 PPO。**
- PPO 是经典的 RLHF 配方，但它有三个活动部件：先单独训一个 reward model，再跑 online rollout、从 policy 采样，然后带一个 value model 做 PPO update。
- 这是一大堆机器 —— 一个会被 game 的 reward model、又贵又不稳的 online 采样、还要小心调参以免 collapse。
- DPO 把这一坨塌掉：它完全跳过显式的 reward model 和 rollout，用一个类似分类的 loss *直接*在 preference pair 上优化 policy，同时一个 KL 项把它拉住、别离 reference model 太远。
- 对我的场景 —— 一个合规敏感、碰钱的 agent —— 那种稳定性、以及不用去养一个我还得为它辩护的 reward model，比 PPO 可能多给的那一点点性能上限更重要。生产里能出错的东西更少。

**preference data 从哪来。** 是成对的 —— 同一个 context 下一个 preferred、一个 rejected 的回复。来源 [✏️ 核实 — 据实填]：
- 模型生成的候选对，由人工 reviewer 排序，包括懂什么叫一个合规、有效的催收回合的 ops / 领域专家。
- 从生产里 harvest 出来的信号 —— 一个回复促成了 resolution、另一个没有。
- 对那些较容易的比较用一些 LLM-as-judge 来上量，高风险的那些留给人工。
- 重点是：这个 preference 信号编码的是*我们*对一个好回合的定义 —— 合规、语气对、有效 —— 而不是一个泛泛的 helpfulness 分数。

**跟 SFT 的关系。**
- 它们干的是不同的活。SFT 教的是*格式和基线行为* —— 怎么把对话进行下去、怎么 call tool、怎么保持那个多语言的 register。
- DPO 再把它*磨*向那些 preferred 的行为，在一些 SFT 不容易表达的轴上 —— 语气、合规、在两个都说得通的回复里挑更好的那个。
- 你得先做 SFT —— 在一个还不会做这个任务的模型上做 DPO，是在抛光一个虚无。"

*(可延伸:)* "而且它是迭代的 —— 这就是那个 eval-driven loop。训一轮 DPO、评估、找出 failure mode、再收集一批专门针对那些 failure 的新 preference pair、重训。这个 preference 集是朝着模型*当前*的弱点长的；静态的 preference data 会随着模型变化而过期。"

## 🇨🇳 中文要点 (理解 + 记忆骨架)

三块:**为什么 DPO / data 哪来 / 和 SFT 的边界。**

**为什么 DPO over PPO (讲真取舍,不是"更简单"):**
- PPO = 三个活动部件:① 单独训 reward model → ② online rollout 从 policy 采样 → ③ 带 value model 做 PPO update。机器多:reward model 会被 hack、online 采样贵且不稳、调不好会 collapse。
- DPO 把这坨塌掉:**跳过显式 reward model 和 rollout,直接在 preference pair 上用类分类 loss 优化 policy**,KL 项把它拉住别离 reference 太远。
- 我的场景 (合规敏感、money-touching):**稳定性 + 不用养一个会被 hack 的 reward model** 比 PPO 那点性能上限更重要。生产里能出错的东西更少。

**Preference data 哪来 (最易暴露,要具体且诚实) [✏️ 核实]:** preference data = 同一 context 的 (preferred, rejected) 对。来源:
- 模型生成候选对 → 人工 (含 ops/领域专家,懂什么是合规有效的催收话术) 排序;
- 从生产 harvest 信号 (一个回复促成 resolution、另一个没有);
- 容易的比较用 LLM-as-judge 上量,高风险的留人工。
- **关键:这个 preference 编码的是"我们"对好回合的定义 (合规、语气对、有效),不是泛泛的 helpfulness。**

**和 SFT 的边界 (分清各干啥):**
- **SFT 教格式和基线行为** —— 怎么对话、怎么 call tool、多语言 register 怎么保持。
- **DPO 再把它往 preferred 行为磨** —— 语气、合规、两个都合理时选更好的那个 (SFT 难表达的轴)。
- **顺序:先 SFT 再 DPO** —— 在还不会做任务的模型上做 DPO 是在抛光虚无。

骨架一句话:**"DPO 砍掉 reward model + rollout,在 preference 上直接优化 + KL 拉住 —— 合规场景要的就是少出错;data 是人工+生产信号+LLM-judge 混合,编码我们的合规定义;SFT 教会做、DPO 教做得更好。"**

讲述节奏:
1. 三块结构先报:"why DPO / where data / vs SFT"。
2. why DPO:**先讲 PPO 三个部件,再讲 DPO 塌掉它** —— 对比才显出你懂取舍。
3. data 来源:**具体 + 诚实**,据实标 [✏️ 核实]。这是最易被钻的地方,讲扎实。
4. SFT vs DPO:一句话各自分工 + 顺序。
5. 收尾抛 iterative loop。

强答 vs 弱答对照 (面试官心里的评分表):
- 弱答:"DPO 比 PPO 简单,所以用 DPO" → "简单"不是工程理由,讲不出本质区别。
- 弱答 (data):"我们收集了 preference data 做 DPO" → 含糊。preference data 来源是最容易暴露真假的地方,含糊=没真做。
- 中等:能讲 DPO 跳过 reward model,但说不清 PPO 何时反而更优 → 只会一招。
- **强答 (你要给的):PPO 三部件 vs DPO 直接优化的本质对比 + 为合规场景选稳定性 + 具体且诚实的 data 来源 (人工/生产/LLM-judge 混合) + SFT 教会做 DPO 磨偏好的清晰边界 + 主动给出 PPO 何时更优** → 这是真做过 post-training 且懂取舍的人。
- 加分:把 preference 定义成"我们对好回合的定义 (合规/语气/有效)"而非泛 helpfulness —— 一句话证明你懂这是**领域对齐**不是套模板。

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: What's DPO actually optimizing — what's the loss doing?**
- Intuitively: it raises the policy's likelihood of the preferred response *relative to* the rejected one, measured against the reference model — so it can't just inflate both.
- The KL-to-reference is baked into the objective; that's what keeps it from drifting off the SFT policy.
- The clean insight: DPO shows the optimal RLHF policy has a closed form in terms of the reference and an implicit reward, so you optimize the policy directly and never materialize the reward model. I'd give that intuition, not derive the loss on the spot.

**Q: When would you actually prefer PPO then?**
- When I need an explicit, reusable reward model — to score arbitrary new outputs, or to do online exploration where the policy generates genuinely novel responses fixed pairs can't cover.
- PPO's online sampling can find behaviors *outside* the preference dataset; DPO is bounded by the pairs you collected.
- So if the data is narrow and I need exploration, PPO earns its complexity. For my case the data covered the space well enough that it didn't.

**Q: How do you ensure preference-data quality — bad pairs poison DPO directly?**
- Exactly — DPO has no reward model to average out noise, so pair quality is critical.
- Multiple reviewers with agreement checks on the high-stakes pairs, clear rubrics for what 'compliant' and 'better' mean, and I'd throw out low-agreement pairs rather than train on noise.
- For LLM-judge-generated pairs, I'd validate the judge against human labels before trusting it at scale. [✏️ 核实 实际质控做到哪一步]

**Q: Did you collect preferences once, or iterate?**
- Iteratively — the eval-driven loop. Train, evaluate, find failure modes, collect new pairs targeting those failures, retrain.
- The preference set grows toward the model's current weaknesses.
- Static preference data goes stale as the model changes. [✏️ 核实 迭代轮次]

**Q: How is "DPO-style" different from textbook DPO?**
- Honest answer: "-style" because [✏️ 核实 — 据实].
- If you used a DPO variant (e.g. IPO / KTO, or a length-normalized or modified loss), say which and why.
- If it was preference optimization with pipeline tweaks but the same core idea, say that. Don't claim a vanilla textbook implementation if it was adapted — the word "style" is doing honest work there.

**Q: How does DPO interact with the multilingual / 7-market setup?**
- Preference data has to cover each language and market — a "good, compliant turn" differs by locale, so I can't just collect English pairs and expect it to transfer.
- That's a data-construction cost, not an algorithm change: I need per-market preference signal, ideally from reviewers native to each market.
- This is exactly the kind of multilingual post-training judgment that maps to Apple's Greater China / Chinese-LLM need.

**Q: How much preference data did you need — is DPO data-hungry?**
- Less than full RLHF in the sense that you don't also train a separate reward model, but pair *quality and coverage* matter more because there's no reward model to smooth over noise.
- I'd rather have fewer, cleaner, well-targeted pairs covering the failure modes than a large noisy set. [✏️ 核实 实际数据量级]
- And because I collect iteratively toward current weaknesses, the data grows where it's actually needed rather than uniformly.

**Q: Does DPO risk over-optimizing and degrading the model's general ability?**
- Yes — push too hard on preferences and you can get reward-hacking-like degradation or reduced diversity, the model collapsing toward a narrow style.
- The KL-to-reference term is the main guard; I also watch *general* capability on a held-out set, not just the preference objective, so I catch alignment-tax regressions.
- It's the same discipline as any fine-tuning: optimize the target, but gate on the things you don't want to break.

## ⚠️ 边界 & 红线 (honest limits + what NOT to say)

- **Preference data 来源必须诚实且具体。** 这是最容易被抓的点。据实填 [✏️ 核实]:到底是人工标、生产信号、还是 LLM-judge,各占多少。**别把"想象中应该这么做"说成"我们就是这么做的"。** 不确定就说"主要是 X,辅以 Y"。
- **不要把 DPO 说成"PPO 的简化版"就完事** —— 要能讲出 closed-form / 跳过 reward model 这个**本质区别**,否则像只看过博客标题。
- **DPO loss 公式不要硬推**,除非你真能推。给直觉 (拉高 preferred 相对 rejected、KL 拉住 reference) 足够且更稳。被追公式细节,大方说"我讲直觉,精确推导我会查论文核对"。
- **"-style" 这个词要兑现** —— 如果用的是 IPO/KTO 或改过的 loss,说清;如果就是标准 DPO 加 pipeline 微调,也说清。别含糊带过让对方以为是别的。
- SFT vs DPO 的边界别说反:**SFT 教会做、DPO 磨偏好**;顺序是先 SFT。说反立刻露怯。
- 不要声称 DPO 比 PPO "全面更好" —— 它是**取舍**。被问 PPO 何时更优,要答得上 (探索 / 可复用 reward model),否则显得只会一招。

## ✅ 加分钩子 (主动抛, steer 到强项)

- 主动抛 **"在合规/money-touching 场景,'生产里能出错的东西更少'比性能上限更重要"** —— 把技术选型上升到生产责任感,正是 Apple customer-facing 想要的判断力。
- 主动提 **"preference 编码的是我们对好回合的定义 (合规/语气/有效),不是泛 helpfulness"** + **多语言 register** —— 把 7 市场、多语言 post-training 的真实经验变成差异化,直接对上 Apple 的 Chinese/Greater China LLM 需求。
- 用 **iterative preference collection = eval-driven loop** 收尾 —— 串起 SFT → DPO → eval → 补数据的闭环,呼应 JD 的 fine-tuning workflows + LLM eval,也把 Q14/Q15 收成一个连贯的 post-training 故事。
- 主动点 **PPO 何时更优 (探索 / 可复用 reward)** —— 不等对方问就给出反向场景,体现你是真懂取舍而非只背了 DPO 一招。
