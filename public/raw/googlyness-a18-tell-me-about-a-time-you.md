# 🟡 G18 · Tell me about a time you proactively proposed a change.

> **信号**: Bias to action · 主人翁 · **hellointerview 报告数**: 2
> ⚠️ 标 [✏️] 的数字是占位, 背诵前换成你的真实数据.

## 🧠 这题在测什么

测主动性: 没人要求你做, 你发现→论证→推动落地的完整闭环.

## 📋 English Answer (背诵稿, ~60-90 秒)

Nobody asked me to rebuild the voice agent's streaming stack — the system was "working." But I kept seeing the same pattern in call reviews: users interrupting the bot mid-sentence and the bot talking over them, plus dead-air gaps at turn boundaries that made conversations feel mechanical. Individually they looked like tuning issues; together they pointed at an architectural ceiling in how we handled packetization and turn-taking.
I wrote a short proposal making the invisible visible: I quantified dead-air and overlap-talk from sampled production calls [✏️ 数字核实], tied them to drop-off at exactly those moments, and argued the fix was structural — streaming ASR partials, sentence-level TTS chunking, and proper barge-in interruption handling — not parameter tweaks.
To de-risk it, I scoped a two-week spike on one market before asking for the full migration. The spike's latency-quality numbers carried the decision for me; I then led the upgrade across markets.
The habit underneath: when the same symptom shows up three times in different costumes, I stop tuning and start questioning the architecture — and I bring leadership a measured spike, not an opinion.

## 🇨🇳 中文完整版 (口播稿, ~60-90 秒)

没有人要求我重构 voice agent 的 streaming 栈 — 系统「在正常工作」. 但我在 call review 里反复看到同一类现象: 用户打断 bot, bot 盖着用户继续说; 轮次边界出现死寂间隙, 让对话显得机械. 单看都像调参问题; 合起来看, 指向的是 packetization 和 turn-taking 的架构天花板.
我写了个短提案, 把不可见的东西变可见: 从抽样的生产通话里量化 dead-air 和盖话比例 [✏️ 数字核实], 关联到恰好发生在那些时刻的挂断流失, 然后论证解法是结构性的 — 流式 ASR partial、TTS 按句分块、真正的 barge-in 打断处理 — 不是调参.
为了去风险, 我先在一个市场做了两周 spike, 再申请全量迁移. spike 的延迟-质量数字替我说服了所有人; 之后我主导了跨市场的升级.
背后的习惯: 同一个症状第三次换着马甲出现时, 我就停止调参, 开始怀疑架构 — 并且带给 leadership 一个有测量数据的 spike, 而不是一个观点.

## 🇨🇳 中文速记 (结构记忆)

没人要求改 streaming; call review 反复出现打断被盖话+死寂间隙 → 指向 packetization/turn-taking 架构天花板; 写短提案量化 dead-air/overlap→流失; 先 1 市场 2 周 spike 去风险, 数字说话再全量. 习惯: 同症状三次换装出现就停止调参开始怀疑架构.

## 🔁 高概率追问

**Q: What if the spike had failed?**

Then it cost two weeks and bought certainty either way — the proposal explicitly framed the spike as buying information, not as a commitment.
