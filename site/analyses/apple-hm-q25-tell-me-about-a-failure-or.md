# 🍎 HM Q25 · "Tell me about a failure or setback, and what you changed afterward."

> **类别**: Behavioral / Failure & growth (STAR) · **考点**: 出事后是甩锅还是 own; 是临时补丁还是把问题变成结构性改进; blameless 文化 · ⚠️ [✏️] 数字背前替换成真实值

## 🧠 这题在测什么 / 面试官想看到

Apple 不怕你犯错, 怕你**犯错后的反应**。他们想看到三件事: (1) 你真的 own 了它 ("I", 不甩团队/平台/供应商); (2) 事故响应里有 quality bar — 快速止血 + 主动披露, 而不是藏; (3) 最关键 — 你把一次性事故**变成结构性防御**, 让同类问题再也不会发生。强答案 = 一个真实有后果的 failure + 一个具体的根因 + 一个永久性的机制改进 + 一个改进后的数字。弱答案 = 假 failure ("我太追求完美了"), 或者只讲止血没讲结构性改进, 或者甩锅。陷阱: 选一个无关痛痒的 "失败", 或者把 blame 推给别人 → 直接判死。

## 📋 English Answer (背诵稿, 主答 ~80 秒 + 可延伸)

"A real one. In an earlier system handling OTP delivery for the Indonesia market, I shipped a change to the retry logic — when a one-time-passcode send didn't get a confirmation fast enough, we'd retry. My change made the retry more aggressive to improve delivery. What I missed was that a slow confirmation isn't the same as a failed send. So we started counting successful sends as failures and retrying them — a false-fail spike. Real customers were getting duplicate codes, and our failure metrics looked alarming when delivery was actually fine.

**My response had two parts.** First, contain it. I caught it within the hour, rolled back the change, and confirmed the metrics recovered before I did anything else [✏️ 核实 rollback 时间]. Second — and this is the part I care about — I disclosed it proactively. I didn't wait for someone to ask why the numbers looked weird. I wrote up exactly what happened, the blast radius, and the root cause, and sent it to the stakeholders myself. Owning the disclosure mattered more to me than looking clean.

But a rollback isn't a fix — it just removes the bad change. The real failure was that my change reached production where a flawed assumption could hit real customers at all. So I made it **structural**. I added a shadow-mode rule: changes like that now run in shadow first, observing real traffic and emitting what they *would* have done, without acting — so a bad assumption shows up as a divergence in the data, not as duplicate codes on a customer's phone. And I built a replay harness so I could run a candidate change against recorded real traffic before it ever went live. After those two changes, our false-fail and false-retry rate dropped by about 47% [✏️ 核实 47%].

The lesson I actually internalized: a slow signal is not a failed signal, and more broadly — never let an untested assumption reach a customer. Test it against real traffic in the dark first."

延伸: "That shadow-mode-then-replay discipline is exactly what I carried into the voice agent — I now ship nothing customer-facing without a shadow rollout, because of this incident."

## 🇨🇳 中文完整版 (口播稿, 与英文对应)

"说一个真的。在更早的一个系统里, 我们负责印尼市场的 OTP 发送 — 就是一次性验证码。我上线了一个改 retry 逻辑的改动: 当一条验证码发出去之后, 没有在足够快的时间内拿到确认, 我们就重试。我这个改动让 retry 变得更激进, 想提升送达率。我漏掉的一点是: **一个慢的确认, 和一个失败的发送, 不是一回事**。所以我们开始把那些其实成功了的发送当成失败、然后重试 — 出现了一个 false-fail 的尖峰。真实的客户开始收到重复的验证码, 而我们的失败指标看起来很吓人, 但实际上送达根本是正常的。

**我的应对分两部分。** 第一, 先止血。我在一小时之内就发现了, 把改动 rollback 掉, 而且在做任何别的事情之前, 先确认指标恢复了 [✏️ 核实 rollback 时间]。第二 — 这才是我真正在意的部分 — 我主动把这件事披露了出去。我没有等别人来问 '这数字怎么这么奇怪'。我自己写清楚了到底发生了什么、影响范围 (blast radius) 有多大、根因是什么, 然后亲自发给了相关的 stakeholders。对我来说, **own 这个披露这件事, 比让自己看起来干净更重要**。

但是 rollback 不是 fix — 它只是把那个坏的改动撤掉而已。真正的 failure 在于: 我的改动里有一个有缺陷的假设, 而它居然能一路触达到真实客户。所以我把它变成了**结构性的改进**。我加了一条 shadow-mode 的规则: 这一类的改动, 现在都先在 shadow 里跑, 观察真实流量、并且输出它 '本来会做什么', 但不真的执行 — 这样一个坏的假设, 会以数据里的 divergence 的形式暴露出来, 而不是变成客户手机上的重复验证码。我还搭了一个 replay harness, 让我能把一个候选改动先拿录制下来的真实流量回放一遍, 再让它上线。做完这两个改动之后, 我们的 false-fail 和 false-retry 率降了大概 47% [✏️ 核实 47%]。

我真正内化下来的教训是: **一个慢的信号不等于一个失败的信号**; 更广义地说 — **永远不要让一个没被测过的假设触达到客户。先在暗处, 拿真实流量去测它**。"

延伸: "这套 'shadow-mode 然后 replay' 的纪律, 正是我后来带进 voice agent 的东西 — 我现在任何面向客户的东西, 不做 shadow 上线就绝不 ship, 就是因为这次事故。"

## 🇨🇳 中文要点 (理解 + 记忆骨架)

- **选真事**: 印尼市场 OTP retry 事故。改了 retry 逻辑想提升送达, 漏掉一点: **慢确认 ≠ 发送失败** → 把成功的发送当失败重试 → false-fail spike → 真实用户收到重复验证码, 指标看着吓人但其实送达正常。(这是真有后果的 failure, 不是假谦虚)
- **响应两段** (背熟):
  1. **止血**: 1 小时内发现 → rollback → 确认指标恢复 [✏️ 核实时间]
  2. **主动披露**: 不等别人问, 自己写清楚 what happened / blast radius / 根因, 主动发给 stakeholders。**"own 披露这件事比看起来干净更重要"**
- **关键转折 — rollback ≠ fix**: 真正的 failure 是 "有缺陷的假设居然能触达真实用户"。所以做**结构性改进**:
  1. **shadow-mode 规则**: 这类改动先 shadow 跑真实流量, 只输出 "本来会做什么" 不实际动作 → 坏假设变成数据里的 divergence, 而不是用户手机上的重复短信
  2. **replay harness**: 候选改动先对录制的真实流量回放, 再上线
  - 改进后 false-fail/false-retry 率降 ~47% [✏️ 核实]
- **内化的教训**: "慢信号 ≠ 失败信号"; 更广义 — **永远别让未测试的假设触达用户, 先在暗处对真实流量测**。
- 记忆钩子: **"慢≠失败 / 1小时止血+主动披露 / shadow+replay 变结构性 / -47%"**。

## 🔬 深挖追问 + 答法 (面试官会顺着钻, Apple 钻到边界)

**Q: Why did this get through review/testing in the first place?**
**中**: 这个问题一开始为什么能通过 review / 测试漏出去?
"Because our tests covered the happy path and clean failures, but not the ambiguous middle — a send that's slow but ultimately succeeds. The assumption 'no fast confirmation means failure' was baked in so quietly that no test challenged it. That's precisely why I didn't just add one test case afterward — a point fix would've left the next hidden assumption exposed. Shadow mode against real traffic catches the class of problem, not just this instance."
> 🇨🇳 因为我们的测试覆盖了 happy path 和那种干净的失败, 但没覆盖那个模糊的中间地带 — 一个发送很慢、但最终成功了的情况。'没有快速确认就等于失败' 这个假设被悄无声息地埋了进去, 没有任何一个测试去挑战它。这正是为什么我后来没有只加一个 test case — 一个点修复 (point fix) 会把下一个隐藏的假设继续暴露在那里。拿真实流量跑的 shadow mode 抓的是这一整类的问题, 而不只是这一个个例。

**Q: How do you make sure shadow mode doesn't just become a step people skip under deadline pressure?**
**中**: 你怎么确保 shadow mode 不会在 deadline 压力下变成一个大家都跳过的步骤?
"I made it a rule, not a suggestion — for customer-facing changes of that risk class, shadow-then-replay is the default path, and skipping it is the exception that needs a reason. Process that depends on goodwill erodes; process that's the default path survives deadlines. And because the replay harness is fast, it's cheaper to use it than to argue about skipping it."
> 🇨🇳 我把它做成了一条规则, 而不是一个建议 — 对那个风险等级、面向客户的改动来说, shadow-then-replay 是默认路径, 跳过它反而是一个需要给理由的例外。靠 goodwill (自觉) 撑着的流程会被磨损掉; 而作为默认路径的流程, 能扛过 deadline。而且因为这个 replay harness 很快, 用它比起去争论要不要跳过它, 成本还更低。

**Q: That 47% — how did you measure it, and are you confident in it?**
**中**: 那个 47% — 你是怎么量的, 你有多大把握?
"It's the false-fail-and-retry rate before versus after, measured on the same Indonesia traffic over comparable windows [✏️ 核实 — 背前确认口径和数字]. I want to be honest that it's a before/after on production metrics, not a controlled experiment, so I'd frame it as a strong directional improvement rather than a clean causal number."
> 🇨🇳 它是 false-fail-and-retry 率的前后对比, 在同一个印尼市场的流量上、可比的时间窗口里量出来的 [✏️ 核实 — 背前确认口径和数字]。我想诚实地说: 这是 production 指标上的一个 before/after, 不是一个对照实验, 所以我会把它框成一个很强的方向性改进, 而不是一个干净的因果数字。

## ⚠️ 边界 & 红线 (honest limits + what NOT to say)

- **绝不甩锅**。不能说 "供应商的确认延迟害的 / 团队没测出来"。根因落在 **"我的改动里有个没被挑战的假设"**, 是 I 不是 they。Apple 对甩锅零容忍。
- **47% 必须 [✏️ 核实]**, 且被钻时主动降级为 "before/after 方向性改进, 非对照实验" — 诚实地承认口径, 比硬撑一个数字强得多 (这本身就是 Apple 看重的 humility)。
- 不要选假失败 ("我太 push 团队 / 我太追求完美")。Apple 一眼识破, 视为不真诚。
- 不要只讲止血就停。这题的分全在**结构性改进**那段 — 没有 shadow+replay 这段, 这题就废了。
- 全程 blameless: 描述事故不带情绪、不抱怨, 像写 postmortem 一样冷静。

## ✅ 加分钩子 (主动抛, steer 到强项)

- **主动披露** — 这是最强的 ownership 信号, 重点强调 "不等别人问, 自己先写 postmortem 发出去"。Apple 极度欣赏这种 own-the-bad-news 的成熟度。
- **从点修复升级到 class 修复** — 主动点出 "我没只加一个 test case, 而是防住整类问题"。这是 senior judgment, 区别于 junior 的补丁思维。
- **教训被带进下一个项目** — 主动说 voice agent 的 shadow rollout 就是这次事故的遗产, 证明这是真正内化的成长, 不是嘴上说说。同时呼应 Q23 里提到的 shadow-mode, 前后一致。
- **"never let an untested assumption reach a customer"** — 这句一句话级别的原则, 直接对齐 Apple 的 "上线前不让真实用户踩坑" 质量观, 也天然带出 privacy/用户体验意识。
