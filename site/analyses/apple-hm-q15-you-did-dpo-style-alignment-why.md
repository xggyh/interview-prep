# 🍎 HM Q15 · You did DPO-style alignment — why DPO over PPO? Where did the preference data come from?

> **类别**: GenAI / ML Concepts · **考点**: DPO vs PPO 取舍 + preference data 来源 + 与 SFT 的边界 · ⚠️ 这是你较扎实的一端,但仍要诚实标注 data 来源 · [✏️] 数字背前替换成真实值

## 🧠 这题在测什么 / 面试官想看到

承接 Q14,这题落在你**较扎实的一端** (DPO/preference)。面试官想看三件事:(1) 你懂不懂 **DPO vs PPO 的真实取舍** (不是"DPO 更简单"这种表面话),(2) 你的 **preference data 从哪来** —— 这最容易暴露"到底是不是真做过",(3) 你分不分得清 **SFT 和 DPO 各干什么**。强答:DPO 去掉 reward model + online rollout,直接在 preference 上优化,更稳更省,适合合规场景;data 来源讲得具体且诚实。弱答:把 DPO 说成 PPO 的简化版还说不清差在哪,或者 data 来源含糊。

## 📋 English Answer (背诵稿, 主答 ~60-90 秒 + 可延伸)

"Three parts: why DPO, where the data came from, and how it sits relative to SFT.

**Why DPO over PPO.** PPO is the classic RLHF recipe, but it has three moving parts: you train a separate reward model, then you run online rollouts sampling from the policy, then you do the PPO update with a value model. That's a lot of machinery — a reward model that can be gamed, online sampling that's expensive and unstable, careful tuning to keep it from collapsing. DPO collapses that: it skips the explicit reward model and the rollouts entirely, and optimizes the policy *directly* on preference pairs with a simple classification-style loss, while a KL term keeps it close to the reference model. For my setting — a compliance-sensitive, money-touching agent — that stability and the absence of a reward model I'd have to defend mattered more than the last bit of performance ceiling PPO might offer. Fewer things that can go wrong in production.

**Where the preference data came from.** Preference data is pairs — a preferred and a rejected response for the same context. In my case the sources were [✏️ 核实 — 据实填]: model-generated candidate pairs ranked by human reviewers including ops/domain experts who know what a compliant, effective collection turn looks like; signals harvested from production — where one response led to resolution and another didn't; and some LLM-as-judge ranking for scale on the easier comparisons, with humans on the high-stakes ones. The point is the preference signal encoded *our* notion of a good turn — compliant, on-tone, effective — not a generic helpfulness score.

**Relative to SFT.** They do different jobs. SFT teaches the model the *format and baseline behavior* — how to conduct the dialogue, call tools, stay in the multilingual register. DPO then *sharpens* it toward preferred behavior on the axes SFT can't easily express — tone, compliance, picking the better of two plausible replies. SFT gets you a capable agent; DPO aligns it to preference. You need SFT first — DPO on a model that can't do the task is polishing nothing."

## 🇨🇳 中文要点 (理解 + 记忆骨架)

三块:**为什么 DPO / data 哪来 / 和 SFT 的边界。**

**为什么 DPO over PPO (讲真取舍,不是"更简单"):**
- PPO = 三个活动部件:① 单独训 reward model → ② online rollout 从 policy 采样 → ③ 带 value model 做 PPO update。机器多:reward model 会被 hack、online 采样贵且不稳、调不好会 collapse。
- DPO 把这一坨塌掉:**跳过显式 reward model 和 rollout,直接在 preference pair 上用类分类 loss 优化 policy**,KL 项把它拉住别离 reference 太远。
- 我的场景 (合规敏感、money-touching):**稳定性 + 不用养一个会被 hack 的 reward model** 比 PPO 那点性能上限更重要。生产里能出错的东西更少。

**Preference data 哪来 (最易暴露,要具体且诚实) [✏️ 核实]:** preference data = 同一 context 的 (preferred, rejected) 对。来源:① 模型生成候选对 → 人工 (含 ops/领域专家,懂什么是合规有效的催收话术) 排序;② 从生产 harvest 信号 (一个回复促成 resolution、另一个没有);③ 容易的比较用 LLM-as-judge 上量,高风险的留人工。**关键:这个 preference 编码的是"我们"对好回合的定义 (合规、语气对、有效),不是泛泛的 helpfulness。**

**和 SFT 的边界 (分清各干啥):**
- **SFT 教格式和基线行为** —— 怎么对话、怎么 call tool、多语言 register 怎么保持。
- **DPO 再把它往 preferred 行为磨** —— 语气、合规、两个都合理时选更好的那个 (SFT 难表达的轴)。
- **顺序:先 SFT 再 DPO** —— 在一个还不会做任务的模型上做 DPO 是在抛光虚无。

骨架一句话:**"DPO 砍掉 reward model + rollout,在 preference 上直接优化 + KL 拉住 —— 合规场景要的就是少出错;data 是人工+生产信号+LLM-judge 混合,编码我们的合规定义;SFT 教会做、DPO 教做得更好。"**

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: What's DPO actually optimizing — what's the loss doing?**
Intuitively: it raises the policy's likelihood of the preferred response relative to the rejected one, *measured against the reference model*, so it can't just inflate both. The KL-to-reference is baked into the objective — that's what keeps it from drifting off the SFT policy. The clean insight is that DPO shows the optimal RLHF policy has a closed form in terms of the reference and the implicit reward, so you can optimize the policy directly and skip ever materializing the reward model. I'd give that intuition, not derive the loss on the spot.

**Q: When would you actually prefer PPO then?**
When I need an explicit, reusable reward model — e.g. to score arbitrary new outputs, or to do online exploration where the policy generates genuinely novel responses DPO's fixed pairs can't cover. PPO's online sampling can find behaviors outside the preference dataset; DPO is bounded by the pairs you collected. So if the preference data is narrow and I need exploration, PPO earns its complexity. For my case the data covered the space well enough that it didn't.

**Q: How do you ensure preference-data quality — bad pairs poison DPO directly?**
Exactly — DPO has no reward model to average out noise, so pair quality is critical. Multiple reviewers with agreement checks on the high-stakes pairs, clear rubrics for what 'compliant' and 'better' mean, and I'd throw out low-agreement pairs rather than train on noise. For the LLM-judge-generated pairs, I'd validate the judge against human labels before trusting it at scale. [✏️ 核实 实际质控做到哪一步]

**Q: Did you collect preferences once, or iterate?**
Iteratively — that's the eval-driven loop. Train DPO, evaluate, find the failure modes, collect *new* preference pairs targeting exactly those failures, retrain. The preference set grows toward the model's current weaknesses. Static preference data goes stale as the model changes. [✏️ 核实 迭代轮次]

**Q: How is "DPO-style" different from textbook DPO?**
Honest answer: "-style" because [✏️ 核实 — 据实]. If you used a DPO variant (e.g. IPO/KTO, or a length-normalized or modified loss) say which and why; if it was preference optimization with some pipeline tweaks but the same core idea, say that. Don't claim a vanilla textbook implementation if it was adapted — the word "style" is doing honest work there.

## ⚠️ 边界 & 红线 (honest limits + what NOT to say)

- **Preference data 来源必须诚实且具体。** 这是最容易被抓的点。据实填 [✏️ 核实]:到底是人工标、生产信号、还是 LLM-judge,各占多少。**别把"想象中应该这么做"说成"我们就是这么做的"。** 不确定就说"主要是 X,辅以 Y"。
- **不要把 DPO 说成"PPO 的简化版"就完事** —— 要能讲出 closed-form / 跳过 reward model 这个**本质区别**,否则像只看过博客标题。
- **DPO loss 公式不要硬推**,除非你真能推。给直觉 (拉高 preferred 相对 rejected、KL 拉住 reference) 足够且更稳。被追公式细节,大方说"我讲直觉,精确推导我会查论文核对"。
- **"-style" 这个词要兑现** —— 如果你用的是 IPO/KTO 或改过的 loss,说清;如果就是标准 DPO 加 pipeline 微调,也说清。别含糊带过让对方以为是别的。
- SFT vs DPO 的边界别说反:**SFT 教会做、DPO 磨偏好**;顺序是先 SFT。说反立刻露怯。

## ✅ 加分钩子 (主动抛, steer 到强项)

- 主动抛 **"在合规/money-touching 场景,'生产里能出错的东西更少'比性能上限更重要"** —— 把技术选型上升到生产责任感,正是 Apple customer-facing 想要的判断力。
- 主动提 **"preference 编码的是我们对好回合的定义 (合规/语气/有效),不是泛 helpfulness"** + **多语言 register** —— 把你 7 市场、多语言 post-training 的真实经验变成差异化,直接对上 Apple 的 Chinese/Greater China LLM 需求。
- 用 **iterative preference collection = eval-driven loop** 收尾 —— 串起 SFT → DPO → eval → 补数据的闭环,呼应 JD 的 fine-tuning workflows + LLM eval,也把 Q14/Q15 收成一个连贯的 post-training 故事。
