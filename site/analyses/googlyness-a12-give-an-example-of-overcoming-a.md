# 🟡 G12 · Give an example of overcoming a significant setback or obstacle.

> **信号**: 韧性 · 系统性学习 · **hellointerview 报告数**: 2
> ⚠️ 标 [✏️] 的数字是占位, 背诵前换成你的真实数据.

## 🧠 这题在测什么

经典挫折题. 你的 canonical: 印尼 OTP. 重点放恢复机制与制度化, 不是事故细节.

## 📋 English Answer (背诵稿, ~60-90 秒)

We shipped a change to the BNPL refund flow in Indonesia that looked harmless — tightening an OTP confirmation timeout. Within a day, support calls spiked: a meaningful share of refunds were getting marked failed even though the money had actually gone back. Root cause: many Indonesian users switch to their SMS app to copy the OTP, and that round trip routinely beat our new timeout — a local usage pattern our review never considered.
I ran it in three phases. Stop the bleeding: confirmed the cause from transcripts and rolled back within the hour. Repair trust: worked with support on proactive outreach to affected users, and flagged it to the regional business lead myself the same day — better they hear it from me with a plan than discover it sideways. Make it structural: the blameless postmortem produced a hard rule — any timeout or retry parameter change runs in shadow against real traffic before enforcement — plus a replay harness simulating timing distributions from historical sessions.
Over the following weeks, with the guardrails and the retry redesign in place, the false-failure rate dropped about 47% versus baseline. That incident became the origin story of how we ship risky parameter changes now.

## 🇨🇳 中文速记 (结构记忆)

OTP 超时收紧→印尼用户切 SMS 复制验证码超时→退款误标失败. 三段: 止血(1h 回滚)/修信任(主动外呼+当天自己上报)/制度化(参数变更必 shadow + 回放 harness). 47% (canonical). 事故变发布纪律起源.

## 🔁 高概率追问

**Q: Whose fault was it?**

Mine to own — I approved the change. The postmortem stayed blameless by design: fixes live in process, not in naming whoever wrote the diff.
