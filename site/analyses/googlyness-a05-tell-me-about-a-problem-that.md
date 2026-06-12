# 🟡 G5 · Tell me about a problem that required in-depth thought and analysis.

> **信号**: 技术深度 · 严谨 · **hellointerview 报告数**: 1
> ⚠️ 标 [✏️] 的数字是占位, 背诵前换成你的真实数据.

## 🧠 这题在测什么

要一次真正的深挖: 重构问题→实验→反直觉发现. 别讲日常 debug.

## 📋 English Answer (背诵稿, ~60-90 秒)

At Shopee I owned MYKAD — Malaysian ID — tamper detection for banking onboarding. The deep problem: real tampered samples were extremely rare and attack techniques kept evolving, so a standard classifier just memorized the few known fraud patterns — great offline metrics, useless against novel attacks.
The analysis that cracked it was reframing the problem itself: stop classifying "tampered vs genuine," and instead learn the manifold of *genuine* documents so tightly that anything off-manifold flags. I implemented that with contrastive learning — pulling genuine-document representations together while pushing apart synthetically perturbed variants: font swaps, region splices, reprint artifacts — approximating the attack space without needing real fraud at scale.
Second-order analysis mattered just as much: failure-mode clustering showed lighting and camera quality dominated false rejects, so the fix was capture-condition augmentation, not a bigger model.
It shipped at 95% TAR at 1% FAR in production. The transferable lesson I use in LLM work now: when labels are scarce and adversarial, model normality and engineer augmentations against the threat model — not against the test set.

## 🇨🇳 中文速记 (结构记忆)

MYKAD 防篡改: 真样本稀缺+攻击演化 → 反转问题学'真'流形; contrastive + 合成篡改增广; 失败聚类发现光照主导误拒→采集条件增广而非大模型. 95% TAR@1%FAR (简历真实).

## 🔁 高概率追问

**Q: How does this transfer to LLMs?**

Hallucination detection has the same shape — scarce labeled failures, shifting distribution. So anchor on grounded behavior, generate adversarial probes synthetically, and build the failure taxonomy before scaling the model.
