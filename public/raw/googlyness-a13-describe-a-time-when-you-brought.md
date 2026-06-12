# 🟡 G13 · Describe a time when you brought different perspectives together to solve a problem.

> **信号**: 视角汇聚 · 跨市场协调 · **hellointerview 报告数**: 1
> ⚠️ 标 [✏️] 的数字是占位, 背诵前换成你的真实数据.

## 🧠 这题在测什么

与 Q6 区分: Q6 是化解对立; 这题是主动汇聚多视角产出更好的方案.

## 📋 English Answer (背诵稿, ~60-90 秒)

Rolling the voice agent out across markets, I coordinated UAT with regional ops teams in multiple countries — none reported to me, and each heard the product completely differently. The Japanese team flagged that our polite-form phrasing was grammatically right but felt scripted. The Indonesian team cared most about mixed-language utterances and local number formats. The Thai team surfaced tone issues no metric of ours would ever have caught.
The default would be triaging these as local bug reports. Instead I built a structure to *combine* them: a shared UAT framework where every market ran the same scenario matrix plus market-specific cases, and a weekly review where each ops lead presented their top finding to the whole group — not just to me.
The cross-pollination changed the architecture. Japan's phrasing feedback became a per-market style layer in prompt config; Indonesia's number-format cases became validation logic that then caught defects in other markets too [✏️ 核实].
The lesson: regional perspectives routed through one engineer get averaged away. Put them in one room with structure, and they turn into architecture.

## 🇨🇳 中文速记 (结构记忆)

7 市场 UAT 各看见不同问题 (JP 语气/ID 混语数字/TH tone); 建共享 UAT 框架+每周各 ops lead 向全组讲 top finding; JP→per-market style 层, ID→通用校验. 金句: 视角经一人中转被平均, 同处一室才变架构.

## 🔁 高概率追问

**Q: How did you resolve conflicting market feedback?**

Per-market config absorbed real differences; shared-layer conflicts were settled by eval data — and because the forum was transparent, no market felt silently overridden.
