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

## 🇨🇳 中文速记 (结构记忆)

没人要求改 streaming; call review 反复出现打断被盖话+死寂间隙 → 指向 packetization/turn-taking 架构天花板; 写短提案量化 dead-air/overlap→流失; 先 1 市场 2 周 spike 去风险, 数字说话再全量. 习惯: 同症状三次换装出现就停止调参开始怀疑架构.

## 🔁 高概率追问

**Q: What if the spike had failed?**

Then it cost two weeks and bought certainty either way — the proposal explicitly framed the spike as buying information, not as a commitment.
