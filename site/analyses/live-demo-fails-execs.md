## 题目（verbatim）

> "Your **live demo fails** in front of the client's executive team. What do you communicate, **in what order**, and how do you recover the deployment timeline?"

**出处**: fde.academy 客户模拟经典. Palantir / Salesforce / OpenAI / Databricks FDE 都问过.

**Round**: Client Simulation / Role-play (45 min)

---

## 这道题在考什么

**不**考你 "怎么 fix the bug". 考**沟通顺序 + 心态稳定 + business 思维 + 用失败做 leverage**:

1. **Acknowledge before explaining** — 不要立刻 jump to "let me explain why this happened"
2. **Buy time without sounding evasive** — 「2 分钟」是 magic number, 长了 awkward
3. **Reframe the meeting** — 把 demo-failure 转成 "live debugging value-demo"
4. **Save the deal, not your ego** — 你的脸面 ≪ 这份合同
5. **Follow-up commitment 实在** — 24h 内必须有 written artifact
6. **Postmortem 不要 sanitize** — 高管能闻出 sanitize 味道
7. **Hardening process** — 你怎么保证不再发生, 比 fix 本身更重要

这是一道 **soft-skill 题里最考 craft** 的, 因为它要你在压力下做 5 件事同时不出错: 听 + 想 + 说 + 操作电脑 + 观察房间情绪.

---

# Part 1 · 教学讲解

## 1. 四个核心术语先解释

**Live demo (现场演示)**: 区别于 "录屏 demo" 和 "deck demo". 风险最高 — 任何一行代码、任何一个 prompt、任何一个 API 调用挂了, 全房间能看到. 但成功的 live demo 比 100 页 deck 都管用, 所以高管 round 才会要求 live.

**Executive team (高管层)**: 通常是 C-level (CEO/CTO/CFO/CISO) + VP-level + 决策圈外围观察者. **关键 insight**: 他们不是来看你 demo 工作不工作的, 他们是来**判断"这个团队能不能把我们当客户处理好"** — demo 失败本身不致命, **应对方式**才决定签单.

**Stakeholders (利益相关方)**: 这场会议里同时坐着:
- 你的 **business sponsor** (推动签单的客户内部 champion) — 他比你还紧张, demo 挂了他在客户内部要被打脸
- **决策者** (CFO/CTO/CEO) — 看你的 craft 和心态
- **怀疑者** (通常是 IT / Security / Legal) — 在等你出错来印证他们的反对
- **你的 manager / 你的 AE** (Account Executive) — 你的盟友, 但也可能因为紧张说错话

**Postmortem (事故复盘 / RCA Root Cause Analysis)**: 失败发生后 24-48h 内写出的事件记录, 包含: 时间线 / 直接原因 / 根本原因 / 影响范围 / 已采取的缓解 / 长期防护. **高管比你想象的更懂技术**, 一份诚实有结构的 postmortem 反而是 sales 资产.

---

## 2. 这个场景的核心矛盾是什么

**矛盾 1: 时间压力 vs 思考时间**

房间里 8 个人, 每个人时薪 $500+, 现场 freeze 10 秒就是 $1000 烧掉. 但你又必须思考 — 思考太快说错话比沉默更糟.

**矛盾 2: 诚实 vs 自我保护**

承认 "this is a bug in our product" → 高管马上担心其他 bug. 但说 "this works in our env" 是把锅甩给客户环境, 立刻失信.

**矛盾 3: 修 bug vs 救会议**

工程脑子 (你的本能) 是马上打开 terminal 修. 但 demo round 不是修 bug round, 你的核心 KPI 是**让这场会议继续产生 business value**, 不是 demo 跑通.

**矛盾 4: 个人面子 vs 公司利益**

你被晾在投影屏前, 自尊心受打击. 本能想证明 "I'm competent". 但越证明越像 defensive, 越 defensive 越 lose trust. **放下个人面子是这一题的硬性要求**.

**矛盾 5: 应对当前 vs 防止下次**

如果你只把这次 demo 救回来, 但没人相信 "下次不会再挂", 这单一样签不下来. **你必须同时给出一个 "process change" 才算解决**.

---

## 3. 决策树 / 反应模板 (按时间窗划分)

| 时间窗 | 你的核心动作 | 你的核心句 |
|---|---|---|
| **0–10 秒** | 表情冷静下来, 不要 facial leak. 别说 "uh oh" / "that's weird" / "let me try again" | (无声, 控制呼吸) |
| **10–30 秒** | Acknowledge ownership. 把眼睛从屏幕移到房间里的人 | "OK, looks like the demo is hitting an issue. Let me handle that directly — give me 2 minutes." |
| **30 秒 – 2 分钟** | Diagnose 一次, 如果 obvious 就 fix, 不 obvious 别死磕 | (操作 + 简短旁白 "I'm checking if it's an auth issue") |
| **2–3 分钟** | Pivot. 不修了, 切到备选方案 | "Rather than burn your time debugging in front of you, let me [show recorded run / walk through the architecture / show yesterday's output]" |
| **3–15 分钟** | 把会议价值找回来 — 用 failure 当材料讲 observability / monitoring / 容错设计 | "This failure mode is exactly what we'd build monitoring for — let me show you how..." |
| **15 分钟末** | Recommit. 给具体日期 + 具体 deliverable | "I'll have a 1-page incident report by EOD tomorrow + re-demo Thursday 10am. Sound good?" |
| **会议后 30 分钟内** | Follow-up email, 写下 commitment | (邮件, 见 Part 2 Problem 4) |
| **Day 1 (会议次日)** | Postmortem 完成, 发出 | (含 RCA, 见 Problem 4) |
| **Day 2-7** | Demo hardening process 落地 + re-demo | (golden path test, frozen env, 见 Problem 5) |

---

## 4. 关键利益相关方对照表

| Stakeholder | 他们在意什么 | demo 挂了他们的内心 OS | 你对他们的关键动作 |
|---|---|---|---|
| **客户 CEO** | 战略风险 / "are these guys reliable" | "这是 5min 还是 6 month 的问题?" | 直视他, 用 business 语言 commit timeline |
| **客户 CTO** | 技术深度 / 架构合理性 | "他们到底懂不懂自己的产品?" | 用 RCA 的 hypothesis 让他参与诊断, 把他变盟友 |
| **客户 CFO** | ROI / 风险 / contract terms | "我能不能 walk away" | 提 "no-charge re-demo" + 「we own this incident」 |
| **客户 IT/Security** | 故障对生产影响 / blast radius | "他们 prod 也这样挂?" | 主动讲 staging vs prod isolation, feature flag |
| **客户 business sponsor** (你的内部 champion) | 自己的 face / political capital | "完蛋了, 我推这家厂商" | 私下 (会后) 给他 ammunition (postmortem + 时间线) 让他在公司内 spin |
| **你的 AE / Sales** | 这单能不能签 | "我的 quota..." | 会前对齐: 「如果 demo 挂, by me 处理, 你别插话」 |
| **你的 manager** | 你能不能处理 | "我要不要跳进来" | 会前对齐: signal "I've got this, 你支持但别接管" |
| **怀疑者** (IT/Legal) | 找 reason to say no | "AH-HA 我就知道" | 把诚实和 postmortem 直接给他 — 反而堵嘴 |

---

## 5. 具体业务场景 (4 个变种带人物)

### 场景 A: AI 外呼平台 demo 给 Acme Bank 高管 (债务催收用例, 贴近 Gao Xin 工作)

**人物**:
- 你 (FDE) + David (AE) + 你的 manager Linda
- Acme Bank 这边: CTO Raj (战略买家), VP Collections Maria (业务买家 + champion), CISO Priya (怀疑者)

**Demo 内容**: 给 Acme 的真实债务客户名单 (脱敏) 跑一遍 AI 外呼, 展示 LLM agent 在通话中识别客户意图、tool-call 查账单余额、回写承诺还款日期到 CRM.

**失败模式**: 你 click "Start Call", 系统返回 `502 Bad Gateway` — 后端 ASR 服务的 staging 环境刚好挂了 (你不知道, 因为你晚上没看告警).

**Raj 表情**: 看时钟, 准备 walk out.
**Maria 表情**: 自己在内部推这家厂商, 当场尴尬.
**Priya 表情**: 一脸 "I told you so".

→ 这是你这道题的 standard 场景, Part 2 全部以此为蓝本.

### 场景 B: BNPL chatbot demo 给印尼监管机构 (OJK)

**人物**:
- 你 + 印尼区 GM + 法务
- OJK 方: 3 个 examiner + 1 个合规 director

**Demo 内容**: 用户在 BNPL app 里跟 chatbot 提交还款延期申请, agent 走 RAG → intent routing → sub-agent → 回写决策.

**失败模式**: chatbot 一直在 "thinking..." 然后 timeout. 实际是 vLLM serving cluster 的 KV cache 满了, 排队队列爆了.

**特殊性**: 监管机构不光看你能不能 demo, 还要把这次 demo 写进**审批材料**. 任何失误都会变成审批 hold. 你的应对必须**用合规语言**, 不能仅技术语言.

### 场景 C: 内部 Agent Platform demo 给 ByteDance 跨部门评审

**人物**:
- 你 + Platform team + 你的 director
- 评审方: 多个部门 (TikTok PayLater / TikTok Shop / Lark) 的 staff eng

**Demo 内容**: 展示 shared workflow abstraction 让 PayLater 的 voice agent 流程能在 30 行代码内被 Lark 复用.

**失败模式**: 复用流程时一个 tool registry 配置错, agent 调到了一个 production tool 而不是 staging mock, 触发 alert.

**特殊性**: 内部评审, 没有合同, 但**有信任和 budget**. 失败带来的不是 "签不签单" 而是 "明年 headcount 给不给". 处理方式更 frank, 但同样需要 process change.

### 场景 D: ConvFinQA demo 给学术合作方

**人物**:
- 你 + Research lead
- 学术方: PhD students + 2 个 faculty

**Demo 内容**: 多跳金融 QA, 复杂 reasoning chain.

**失败模式**: prompt 里有个 typo 导致 reasoning chain 中间断了, agent 返回部分答案.

**特殊性**: 学术圈 demo 失败反而是**机会** — 学术人天天遇到 negative result, 你 honestly demo 失败 + 解释 hypothesis 反而被尊重. 这条策略不适用于商业客户.

---

## 6. 工程上 / 应对上要做什么 (Playbook)

按 **会议中 / 会议后 30 分钟 / 24 小时 / 一周** 4 个阶段:

### 阶段 1 · 会议中 (0–45 min)

1. **冷静呼吸 3 秒**, 然后 acknowledge + ownership (10 秒内)
2. **2 分钟硬上限** 给自己 diagnose, 超时立刻 pivot
3. **Pivot 到价值密度高的内容**: 备份录屏 / 架构讨论 / 类似客户案例 / 失败检测系统设计
4. **不允许的语言**: "works in our env" / "known issue" / "engineering will look" / "real quick"
5. **不允许的肢体**: 看屏不看人 / 频繁叹气 / 跟你的同事 huddle whisper
6. **结束前 5 分钟**: 三个明确 commitment + 具体日期 + 询问 "what else do you need"

### 阶段 2 · 会议后 30 分钟内

7. **Follow-up 邮件** 立刻发, 写明会议中的 commitment (event log purpose)
8. **私下找 business sponsor** (Maria) 通话 5 分钟: 「我搞砸了, 24h 内给你 ammunition 你在内部 spin」
9. **私下找 manager 同步**, 5 分钟: postmortem 计划 / 内部资源调度

### 阶段 3 · 24 小时内

10. **Postmortem 1-pager** 完成. 结构: 时间线 / 直接原因 / 根本原因 / 影响范围 / 缓解 / 长期防护
11. **发给客户** (CC: AE + manager). **不 sanitize** — 写实根因, 哪怕涉及自家流程问题
12. **预约 re-demo**: 给 2-3 个时间槽, 客户选

### 阶段 4 · 一周内

13. **Demo hardening process** 落地: golden path 测试 / frozen demo env / dry-run protocol
14. **Re-demo 执行**, 当 demo 中 mention 上次的 fix + 新增 monitoring
15. **「学到了什么」** — 主动跟客户 share 你们 internal 的 process improvement, 把 incident 变成 capability story

---

## 7. 几个容易踩的坑

| # | 坑 | 后果 / 应对 |
|---|---|---|
| 1 | **Long silence while debugging** | 房间气压暴跌, 高管开始看手机 → 注意力撤回 |
| 2 | **Blame environment / customer** | 听起来推卸, 信任立刻 -50 |
| 3 | **Punt to "engineering"** | 你听起来像中间商, 不像 owner |
| 4 | **Promise speedy fix without checking** | 第二次失败时信任归零 |
| 5 | **Don't write follow-up email** | 24h 后高管记忆模糊, commitment 漂移 |
| 6 | **Defensive body language** | pacing / 叹气 / 不看人 — 高管在读你的姿态 |
| 7 | **Re-demo too soon** | 同样的环境, 同样的风险, 同样的灾难 |
| 8 | **Postmortem 写得像 PR 稿** | 高管能闻出 spin 味, 反而失信 |
| 9 | **不告诉 business sponsor** | 他第二天还在公司里背锅, 失去内部 champion |
| 10 | **拿 demo 失败当 individual contributor 教训** | 这是 team / process 失败, 不是你一个人, 但责任你担 |

---

## 一句话总结 (Part 1)

> **Live demo 挂了不是技术事故, 是 trust event**. 你的 craft 不在于把 bug 修好, 而在于**在 5 分钟内把房间从 "他们能 deliver 吗?" 转向 "他们处理失败的方式让我更信任他们"**.
>
> 高管签合同看的是 **失败应对能力**, 不是 demo 完美度. 完美的 demo 只代表 demo 跑通, 灾难的应对代表你 prod 出事时也能这样.

---

# Part 2 · 5 个深度问题 (Client Sim 硬核细节)

## ⚙️ Problem 1: The 30-Second Recovery Script (literally what you say)

**这是这道题最被 underrate 的部分**. 大部分 candidate 只会说 "I'd acknowledge the issue" — 但 acknowledge 怎么说? 用什么词? 语速? 在哪一秒说? 这些是真正区分 senior 和 junior 的地方.

### 1.1 黄金 30 秒脚本 (verbatim)

**Demo 屏幕报错的瞬间**:

> *(深呼吸 2 秒. 不要立即开口. 不要"啊..." "诶..." "嗯...")*
>
> *(把视线从屏幕移开, 看向房间里坐得最远的人 — 通常是 CEO/CTO. 这个微动作传递「我没在 panic 看代码」)*
>
> **第 5 秒**: "OK, looks like the demo is hitting an issue."
>
> *(停 1 拍. 不要立刻接 "but" / "however")*
>
> **第 8 秒**: "Let me handle that directly — give me 2 minutes."
>
> *(看一眼屏幕, 但不要钻进 terminal)*
>
> **第 15 秒**: "If it's not obvious in 2 minutes, I'm going to pivot to [recorded run / architecture walkthrough] rather than burn your time. I'd rather you leave with substance than watch me debug."

**到 30 秒为止你已经做了 5 件事**:

1. Acknowledged 问题 (没有 deflect)
2. 拿 ownership ("I'll handle it" — 不是 "we'll" 也不是 "engineering will")
3. Bought 2 分钟 (set expectation)
4. Pre-committed pivot plan (告诉房间 "我不会让你们坐在这里看我 panic")
5. 表达对他们时间的尊重 ("rather than burn your time")

### 1.2 为什么 "2 分钟" 是 magic number

| 时长 | 房间感受 | 适用 |
|---|---|---|
| 30 秒 | 太快, 像在装样子 | 不适合 |
| **2 分钟** | 既显示尝试, 又不浪费时间 | ⭐ standard |
| 5 分钟 | 极限, 注意力开始撤 | 仅限你 90% 确定能修 |
| 10 分钟 | 灾难, 房间已经在 mental walk out | 绝不 |

**额外** tip: 说 "2 minutes" 而不是 "a few minutes" — 后者听起来 evasive, 前者 specific.

### 1.3 不允许说的话 (red line)

| Phrase | 为什么禁止 | Replace with |
|---|---|---|
| "Works fine in our env" | 暗示锅在客户环境 | "Let me check if it's an environment issue specific to this setup" |
| "This is a known issue we're fixing" | 暗示你们 prod 也有 | (不要在 demo 中提 known issue) |
| "Engineering will look at it" | 你是 middleman, 不是 owner | "I'll personally own this and get back to you by EOD tomorrow" |
| "Let me debug this real quick" | "real quick" 是 setup-for-failure 短语 | "Give me 2 minutes" |
| "I don't know what happened" | True 但不要在 demo 当下说, 给自己 hypothesis time | "Let me check 2-3 hypotheses, I'll know in a minute" |
| "Oh shit" / "Weird" / "Hmm" | facial / verbal leak | (沉默) |
| "Last time this didn't happen" | 暗示偶发, 不可控 | (略过, focus on 现在) |

### 1.4 允许 (鼓励) 说的话

| Phrase | 为什么有效 |
|---|---|
| "Let me handle that directly" | "directly" 传递 ownership |
| "Give me 2 minutes" | specific, time-bounded |
| "Rather than burn your time" | 表达 respect, 不是 desperate |
| "Here's what I'd rather show you" | pivot 不像 retreat, 像 redirect |
| "This is exactly what we'd build monitoring for" | 把 failure 转 feature talk |
| "By EOD tomorrow / Thursday 10am" | concrete deliverables |
| "Anything else you need from me in the next 24h" | open-ended ownership |

### 1.5 微表情 / 肢体语言 checklist

| Do | Don't |
|---|---|
| 把视线**离开屏幕**, 看人 | 一直盯屏 / 把脸埋进 laptop |
| 直立 / 把笔放下 | 频繁摸头 / 摸鼻子 / 双手抱胸 |
| 语速**降低** 20% (慢但清晰) | 加快语速 (panic 信号) |
| 单一手势 (打开手掌示意) | 多手势 / 指着屏幕 / 拍桌 |
| 跟 manager / AE 眼神示意 "我有这个" | 当众 whisper "what do we do" |

### 1.6 当你 manager 在场, 你怎么 signal "我 got this"

会前 5 分钟你应该和 manager 对齐:

> "If something breaks, I'll handle. **Signal me by tilting your head** if you want to jump in. Otherwise I'll run the recovery. After 5 minutes if I can't pivot, please jump in with 'let me share the architecture deck while [你的名字] gets us back on track'."

会议中你的眼神扫一下 manager + 微笑 + 继续讲 = "I got this, hold position". 这是 senior 沟通信号.

---

## ⚙️ Problem 2: Distinguish "Demo Bug" vs "Core Product Issue" — Which Do You Admit?

**这是道德 + 战术的双重题**.

### 2.1 两类失败的本质区别

| 类型 | 例子 | 客户该担心吗 | 你该承认吗 |
|---|---|---|---|
| **Demo-only 失败** | staging env 配错 / demo 数据过期 / WiFi 抖动 / 演示账号 credential 失效 | 不需要 | 部分承认 (是我们 demo 准备问题) |
| **Core product 失败** | 主推理链路 bug / 跨租户数据泄漏 / 核心 API 返回错误结果 | 应该担心 | 必须承认 (而且要主动 escalate) |

**问题在于: 当下你不知道是哪种**.

### 2.2 5 个 hypothesis 你应该在脑里排序

会议中你 demo 挂了, 你的脑子应该自动跑这 5 个 hypothesis:

1. **Demo env 配置问题** (60% 概率) — 最 likely. 比如 token 过期, 数据库刚 reset, demo 用户被 disable
2. **网络 / infra 偶发** (20%) — WiFi 抖, AWS 区域有事件
3. **演示 prompt / input 触发了边角 bug** (10%) — 客户 supply 的 input shape 没测过
4. **真 product bug** (8%) — 主路径 broken
5. **演示者本人操作错误** (2%) — 你点错了按钮

如果 1-3 是真因, 你可以说「demo 准备问题, 不是产品问题」. 如果 4-5, 老实承认.

### 2.3 当下的 admission 语言模板

**当你 90% 确定是 demo env 问题** (e.g., staging 服务挂了, 你看见 503):

> "Looks like our staging environment is down — this is the demo setup, not the core product. **The same code is running in production for other customers right now and is healthy** (我得有 dashboard 截图 backup). Let me show you the production dashboard so you can see system status, then we'll re-schedule the live walkthrough."

→ **关键**: 你得**有证据**. 不能空口说 "prod 是好的" — 高管会问 "how do you know". 准备 backup: 一个生产环境的 health dashboard 截图.

**当你不确定是 demo 还是 core**:

> "I don't want to speculate on root cause without checking. Two paths: **(a)** I take 1 minute to check our status dashboard, **or (b)** I commit to a full RCA by EOD tomorrow that tells you whether this was a demo-only issue or a product issue. **Both are honest answers, but (b) gives you the most reliable answer**. I'd recommend (b)."

→ 这句话牛逼在: 你**拒绝当场猜**, 但给客户选项, 还推荐了那个**更慢但更诚实**的选项. 这传递 "I value accuracy over face".

**当你怀疑是 core product issue**:

> "I want to be honest with you: this could be a real product issue, not just a demo glitch. I'd rather tell you that upfront than pretend it's nothing. **What I'll commit to**: full RCA by EOD tomorrow including whether other customers are affected. **In the meantime**, if you want me to share what monitoring/alerting we have to catch this kind of issue in production, I can walk through that now."

→ **承认 core bug 听起来反直觉, 但: (a) 你后来发现真是 core bug, 你 已经 framed, 信用保住. (b) 你后来发现不是, 你 looked more honest than you needed to be, **bonus trust**.

### 2.4 决策矩阵: 承认 vs 不承认

| 你的把握 | 承认是 demo 问题 | 承认是 core 问题 | 不承认任何 |
|---|---|---|---|
| 90% demo env | ✓ 承认 demo env, 给 backup 证据 | ✗ | ✗ (装糊涂失信) |
| 50/50 | ✗ (过早 commit) | ✗ (过早 commit) | ✓ 「等 RCA 再说」 |
| 90% core bug | ✗ (装无辜更糟) | ✓ frame 为「我们 catches this kind of issue 的 monitoring」 | ✗ |
| 完全不知道 | ✗ | ✗ | ✓ 「24h 内 RCA」 |

**唯一红线**: 永远不要明知是 core bug 还说是 demo env. 这是**业内 reputation 杀手**, 一旦客户后来发现, 信任永远修不回.

### 2.5 当高管追问 "is this happening in production right now"

这是高管经典连环问. 你的 3 种 reply:

**回复 1 (有 monitoring + dashboard)**:
> "Let me check our production status page in real time. *[打开 dashboard]* — production is showing healthy for the last 24h across all tenants. This issue is specific to our demo environment. **But I'll still do a full RCA tomorrow** to confirm there's no shared code path."

**回复 2 (没准备 dashboard)**:
> "I don't have our production dashboard pulled up — that's on me, I should have. **What I can commit to**: by EOD today, I'll send you a screenshot of last-24h production health metrics + tomorrow morning a full RCA. You'll have the answer before our next sync."

**回复 3 (你怀疑 prod 也受影响)**:
> "I don't want to commit to 'no production impact' without checking. **I'm going to step out for 90 seconds to call my SRE team** and get a yes/no. Can we take a 2-minute break and I'll come back with a clear answer?"

→ 回复 3 是**最 mature 的回答**, 即便它打断会议 — 因为它把诚实排在体面之前. 高管会注意.

---

## ⚙️ Problem 3: Pivot to Value Conversation — Use the Failure Productively

**这是把 demo 失败变成 sales 武器的核心**.

### 3.1 不要的 pivot

| 不要 | 为什么 |
|---|---|
| "Let me show our slide deck" | deck 永远是 sales 的最后救命稻草, demo round 拿出 deck = 投降 |
| "Let me explain the architecture" (干讲 1h) | 没人想听 1h 干讲架构 |
| "Let me reschedule" (5 分钟内说) | 太早, 你还没尝试救场 |
| "Here's a customer reference story" | 是好东西, 但应该是 backup, 不应该是主菜 |

### 3.2 推荐的 pivot 内容 (按 effectiveness 排序)

**Pivot Option 1: 录屏 + 现场解说 (⭐⭐⭐⭐⭐)**

> "I have a screen recording from yesterday's demo run on similar data. **Let me play it + narrate**, so you see what the workflow looks like end-to-end. Then we'll dig into your specific questions."

为什么有效:
- 仍然 visual, 不是干讲
- 你能控制节奏 + 暂停 + 解释
- 房间能跟着你的视线动
- **你需要 prep**: 任何重要 demo 前都要录一遍 backup, 30 分钟成本, 救命

**Pivot Option 2: 用 failure 当 monitoring / observability 的 talking point (⭐⭐⭐⭐⭐)**

> "Actually, **this kind of failure is exactly what we'd build production monitoring for**. Let me show you the observability layer we'd add to your deployment — and how you'd be notified before any of your customers see this. *(画一张图 / 拿出 dashboard 模板)*"

为什么有效:
- 把 negative 转 positive
- 直接展示**你不只 demo 工作场景, 你考虑过失败场景**
- 这是 staff-level signal: 「I think about prod, not just happy path」
- 关键: **你必须真的能讲出 monitoring 设计** — 见 Problem 5

**Pivot Option 3: 拿客户的数据 / 用例做 walkthrough (⭐⭐⭐⭐)**

> "While the live system is down, let me **walk through your specific use case end-to-end on a whiteboard**. You told us about X, Y, Z scenarios — let me show how each would flow through our system. We'll annotate with the questions you've been wanting to ask."

为什么有效:
- 切到客户**特定场景**, 显示你 done your homework
- 房间从「看你 demo」变「跟你一起设计」, 参与度更高
- 你能听到他们当下的实际担忧, 反而比 demo 更产生价值

**Pivot Option 4: 类似客户的真实案例 (⭐⭐⭐)**

> "Let me share what a comparable customer — same vertical, same scale — has done with us in the last 6 months. Here are 3 specific outcomes... (具体数字)"

为什么有效:
- Reference 是高管 trust 信号
- **必须**: 提前要 reference customer 的同意

为什么只 3 星: 这听起来还是 sales pitch, 不是真 substance.

### 3.3 串接 pivot 的语言模板

从 acknowledgment 转 pivot 的 transition 句:

> "Rather than debug this live in front of you — **and I really don't want to do that to your time** — let me show you something arguably more valuable: [pivot 内容]. We can come back to the live demo on a re-scheduled session if you want, but I think you'll get more out of [pivot] right now."

**关键词**:
- "rather than ... in front of you" — 强调对他们时间的尊重
- "arguably more valuable" — 不是 "as valuable", 是 **更** valuable
- "I think you'll get more out of" — 自信但不傲慢

### 3.4 用 failure 推 monitoring 讨论的 sample script (3 分钟)

> *(白板 / 屏幕一张系统图)*
>
> "OK so here's a useful side-conversation. **This kind of failure — a backend service returning 502 — is something we'd catch in 4 layers before your team ever sees a customer impact**:
>
> **Layer 1**: Real-time service health check, alerts on **success rate dropping below 99.5% over 5min window**.
>
> **Layer 2**: Per-tenant canary monitoring — we keep a synthetic transaction running every 30s simulating your users. If it fails 2x in a row, your on-call gets paged.
>
> **Layer 3**: Failure correlation — if 502s start spiking, we automatically check whether it correlates with deploys, dependency outages, or traffic spikes. RCA hypothesis comes in your inbox in 60s.
>
> **Layer 4**: Graceful degradation — for your specific use case (debt collection calls), if our LLM stack is down, we fall back to a scripted template. **Customer impact is muted, not propagated**.
>
> **What I want you to take away**: today you saw a single 502 in a demo. In production, you'd see **zero customer impact**, because layer 4 kicks in, layer 1-3 notifies my team, we'd fix it before your team even hears about it. **That's the reliability difference between demo and production**.
>
> Anyway — that's what I'd argue is more valuable than watching me click around to make demo work. Questions?"

→ 这个 3 分钟比你成功的 demo 都管用. 你刚把一场失败转成了**架构可信度展示**.

### 3.5 Reframe to 高管 language

| 工程师说 | 高管想听 |
|---|---|
| "502 from upstream" | "Service degraded gracefully, no customer impact" |
| "We'd add Prometheus alerts" | "Your on-call team would know in 60s; your customers would never see this" |
| "Circuit breaker pattern" | "If something's wrong, we **isolate** the failure to that single component" |
| "Canary monitoring" | "We continuously test the system as if a real customer were using it" |
| "Postmortem doc" | "You'd get a written explanation by tomorrow morning with timeline + fix" |

---

## ⚙️ Problem 4: Postmortem + 24-Hour Trust Repair Plan

**这是会议后 24-72 小时的具体动作**.

### 4.1 会议后 30 分钟内的 follow-up email

**模板** (你应该在车里 / 走廊就发出):

```
Subject: [Acme] Today's session - written follow-up

Hi Raj, Maria, Priya,

Quick written follow-up on today's session.

What happened:
- During the live demo, our system returned a 502 error preventing
  the AI agent from completing the workflow.
- I pivoted to a recorded walkthrough + architecture discussion to
  preserve your time.

What I committed to:
1. Full RCA by EOD tomorrow (Tuesday). I'll send a 1-page document
   with: timeline, direct cause, root cause, customer-impact analysis,
   mitigations applied, long-term fixes.
2. Re-demo Thursday 10am AEST. Same scenarios + your team can
   propose 2 additional scenarios for us to demo on. No charge for
   this session.
3. Monitoring/observability deep dive we discussed today — I'll
   include a written design as part of the Tuesday RCA.

What I'd appreciate from you:
- If you have any additional scenarios you want us to demo, please
  send them by Wednesday EOD so we can prepare.
- If Thursday doesn't work, please suggest 2 alternatives.

I appreciate your patience today. The way I handle this issue is the
way we'd handle any production issue with you as a customer — and
I want to demonstrate that.

[Your name]
[Title]
[Phone for direct reach]
```

**为什么这封邮件重要**:
- **Written record** of commitments — 防止高管次日记忆漂移
- **Phone for direct reach** — 传递 ownership ("you can reach me directly")
- **「the way I handle this is the way we'd handle prod issue」** — 把 incident 转成 capability message
- **Asks** — 让客户有 follow-up 动作, 减少他们 "should we cancel" 的负面 mental cycle

### 4.2 24 小时 RCA 1-pager 模板

```
PRODUCTION INCIDENT REPORT
─────────────────────────────
Incident: Live demo failure on 2026-05-20
Customer: Acme Bank
Severity: Sev 3 (customer-facing demo, no production impact)
Author: [you]
Distribution: Acme (Raj, Maria, Priya) + Internal (manager, AE)
Status: RESOLVED

TIMELINE (PST)
─────────────────────────────
14:00  Demo session starts, normal sequence
14:07  First demo workflow returns 502 from upstream ASR service
14:08  FDE (me) acknowledges, attempts 2-min diagnose
14:10  Pivot to recorded walkthrough + monitoring discussion
14:35  Session ends, follow-up email sent at 14:45
15:30  Internal SRE confirms ASR staging cluster OOM (out of memory)
       due to a load test left running overnight
16:00  Cluster restored, monitoring confirms healthy

DIRECT CAUSE
─────────────────────────────
ASR staging cluster ran out of memory due to a load test job
(scheduled by Engineering Team B) that did not properly terminate
overnight. Memory accumulated to OOM threshold during demo hours.

ROOT CAUSE (5-why)
─────────────────────────────
Q1: Why did the cluster OOM?
A: Load test job did not release memory.

Q2: Why did the load test run overnight?
A: It was scheduled by a different team for capacity planning, with
   no awareness of the demo time.

Q3: Why was there no coordination?
A: No shared calendar of "no-deploy / no-load-test" windows for
   customer-facing demos.

Q4: Why no shared calendar?
A: This is the first formal customer demo for the new region;
   processes hadn't been established.

Q5: Why hadn't processes been established?
A: Team grew faster than process formalization. This is a process
   gap, owned by me.

CUSTOMER IMPACT
─────────────────────────────
- Production customers: ZERO impact. Production runs on separate
  cluster with isolated resources. Verified via dashboard, attached.
- Acme demo: 30 min of session was redirected; 0 of 5 planned demo
  scenarios shown live.

MITIGATIONS APPLIED (within 24h)
─────────────────────────────
1. ASR staging cluster OOM rule set + auto-kill threshold
2. Load tests now require approval ticket; tickets reject
   overlapping with declared demo windows
3. Customer-demo calendar published across engineering teams
4. Pre-demo dry-run protocol formalized (see Section 5)

LONG-TERM PREVENTION
─────────────────────────────
1. Frozen demo environment, separate from staging (1 week to set up)
2. Automated 30-min-before-demo health check + abort criteria
3. Dual-environment fallback (primary + secondary demo cluster)
4. Internal demo certification (every demo must pass dry-run in
   prod-parity env)

WHAT THE CUSTOMER WOULD HAVE SEEN IN PRODUCTION
─────────────────────────────
If this were production: 0 customer impact. Layer-1 alerts would
have paged on-call within 60s, capacity would have been added, and
graceful degradation would have kept customer-facing service running
on a scripted fallback. Dashboard attached.

THIS WILL NOT HAPPEN AT THURSDAY'S RE-DEMO BECAUSE
─────────────────────────────
1. Re-demo runs on freshly-prepared demo env
2. 30-min pre-demo health check (we'll send you screenshot)
3. Two engineers on standby (one demo'ing, one watching system
   health real-time)
4. Backup recorded walkthrough ready if any layer fails

CONTACT
─────────────────────────────
[Your name], [phone], [email]
Available for any questions before Thursday 10am.
```

**这封 RCA 的设计哲学**:
- **Honest 5-why** (不是 "it was a one-off, won't happen again")
- **Customer impact section** 单独 — 高管最关心这个, 别让他们 hunt
- **What would have happened in production** — 把 demo failure 和 prod risk **明确分离**
- **Thursday won't fail because** — 给具体 reason 不是 vague promise

### 4.3 Re-demo 设计原则

**3 个不允许**:

1. 不允许同样的 setup (换 env / 换数据 / 换演示路径)
2. 不允许同一人 demo (换搭档, fresh eyes)
3. 不允许没有 backup (录屏 + 备份 demo 必须 ready)

**3 个必须**:

1. **Dry-run 至少 3 次** in production-parity env, 三次连续成功才允许 demo
2. **Pre-demo health check** 30 分钟前跑, screenshot 发给客户 (high-confidence signal)
3. **Standby engineer** in next room, 实时盯 system health

### 4.4 长期 trust 修复 timeline

| Phase | 期限 | 你做的事 |
|---|---|---|
| **Phase 0: 24h** | Day 1 | Postmortem 发出 |
| **Phase 1: 1 week** | Day 2-7 | Re-demo 成功 + 把 monitoring 设计发给他们 |
| **Phase 2: 1 month** | Week 2-4 | 主动给他们 weekly health 报告 (even without ask) |
| **Phase 3: 3 months** | Quarter 1 | Quarterly business review, demonstrate sustained stability |
| **Phase 4: 6 months** | Quarter 2 | 关系恢复正常, demo failure 变成 "remember when..." 笑谈 |

**重要**: 高管对 vendor 的 mental model 更新很慢. **30 天内绝不再失败一次**, 否则 trust 永远修不回.

---

## ⚙️ Problem 5: Demo Hardening Process — Prevent Next Time

**这是 staff-level signal. 个 FDE 知道怎么救场, 但 staff FDE 知道怎么让场不再挂**.

### 5.1 Demo 失败的 5 类根因 (帕累托)

| 类 | 占比 | 例子 | 解决方案 |
|---|---|---|---|
| **A. Demo env 配置 drift** | 35% | token 过期, demo 用户 disable, 数据库 reset | Frozen demo env + immutable |
| **B. Demo data 过期 / corrupted** | 25% | 演示 hardcode 的客户 ID 已删除, 演示 prompt 不再触发预期路径 | Demo data fixtures, version-pinned |
| **C. 上游 service / 依赖故障** | 20% | ASR / TTS / LLM provider / DB 短暂挂 | Dual-env + circuit breaker + fallback |
| **D. 网络 / 演示场地** | 10% | WiFi 抖, VPN 断 | 4G hotspot backup, ethernet 优先 |
| **E. 演示者操作 / prompt 错** | 10% | 点错按钮, prompt typo | Demo script + dry-run |

### 5.2 五层 Hardening Process

**Layer 1: Frozen Demo Environment** (防 A 类)

- 一个**独立**的 demo cluster, 跟 staging / prod 完全隔离
- **不允许任何人在 demo 前 24h push code 到这个 env**
- 所有 secret / config / data fixture **immutable** (lock & version)
- 单独的 demo 数据库, 每次 demo 后**完整 reset 到 known-good snapshot**

```yaml
# demo-env-policy.yml
demo_clusters:
  - name: demo-primary
    isolation: full
    code_freeze_before_demo: 24h
    data_snapshot: ./snapshots/demo-v2.3-blessed.tar.gz
    reset_after: true
    no_deploys_during_demo_window: true

  - name: demo-secondary
    purpose: hot-standby fallback
    isolation: full
    sync_with_primary: real-time
```

**Layer 2: Golden Path Test** (防 B + E 类)

每场 demo 之前, 把 demo 流程当 **automated end-to-end test** 跑一次:

```python
# golden_path_test.py
def test_acme_demo_path():
    """Run the exact demo script as an automated test."""
    # Step 1: Login as demo user
    session = login(DEMO_USER_ACME)

    # Step 2: Click "Start Call" workflow
    call = start_call(customer_id="DEMO_CUST_42")
    assert call.status == "in_progress"

    # Step 3: Verify ASR transcription
    transcription = wait_for_transcription(call.id, timeout=10)
    assert "expected_phrase" in transcription

    # Step 4: Verify agent tool call
    tool_calls = call.get_tool_calls()
    assert any(tc.name == "check_balance" for tc in tool_calls)

    # Step 5: Verify CRM writeback
    crm_record = crm.get_call(call.id, timeout=15)
    assert crm_record.outcome in ["promised", "refused", "unable_to_reach"]
```

**运行**: 自动每 30 分钟跑一次直到 demo 开始. 任何 step fail → 立即 page + 触发 hot-standby switch.

**Layer 3: Pre-Demo Health Check** (防 C 类)

Demo 开始前 30 分钟:

```bash
#!/bin/bash
# pre-demo-check.sh

echo "=== Acme Demo Pre-Flight ==="
echo "Time: $(date)"
echo ""

# Check core services
check_service "asr-staging"   || abort "ASR down"
check_service "tts-staging"   || abort "TTS down"
check_service "llm-vllm"      || abort "vLLM down"
check_service "crm-sandbox"   || abort "CRM sandbox down"

# Run golden path
python golden_path_test.py    || abort "Golden path failed"

# Check demo user / data
check_demo_data "DEMO_CUST_42" || abort "Demo data missing"

# Check network
ping -c 3 demo-cluster.example.com || abort "Network issue"

# Check hot-standby ready
check_hot_standby             || warn "Standby not ready (no fallback)"

echo "=== ALL CHECKS PASS ==="
echo "Demo is GO. Sending screenshot to customer."
```

**Output 截图**自动发给客户, signal "我们认真准备了".

**Layer 4: Dry-Run Protocol** (防 B + E 类)

- **3 次完整 dry-run** in demo env, 同一演示者, 同一 script
- 3 次全过才允许 customer demo
- 任何一次失败 → debug + 重置计数器 (回到 0/3)
- Dry-run 必须**录屏**, 录屏自动成为 backup

**Dry-run script 模板**:

```
Demo: Acme Bank - Voice Agent Workflow (v2.3)
Duration: 25 min content + 5 min Q&A buffer
Performer: [Your name]
Backup performer: [Colleague name]

[00:00-02:00] Open: 介绍 use case
  - Pull up CRM dashboard
  - Click "Customer list" → Filter "owed > $500"
  - Highlight DEMO_CUST_42

[02:00-08:00] Workflow 1: Outbound call
  - Click "AI Agent Call" on DEMO_CUST_42
  - Wait for live ASR transcript (typical 3-5s lag)
  - Show LLM agent reasoning panel
  - Verify tool call to balance_check
  - Verify customer response handling

[08:00-15:00] Workflow 2: Outcome writeback
  - Show CRM updated with call summary
  - Show recording URL accessible
  - Show transcript with timestamp

[15:00-22:00] Workflow 3: Compliance / Audit
  - Show audit log entry
  - Show consent recording flag
  - Show retention policy applied

[22:00-25:00] Wrap + transition to Q&A

Backup recording: ./recordings/acme-demo-v2.3-dryrun3.mp4
Hot-standby env: demo-secondary.example.com
On-call SRE: [name + phone]
```

**Layer 5: Standby Engineer** (防 fail-mid-demo)

- **一个工程师 in next room / remote**, 整场 demo 实时看 dashboard
- 配置 channel: 任何 alert 直接 Slack 你的 phone
- 如果 demo 中 system 出问题, standby 工程师**60 秒内**通过 Slack 告诉你 hypothesis
- **你不孤军作战**

### 5.3 Demo Hardening Checklist (印 1 页)

```
[ ] Demo env separate from staging/prod
[ ] Code freeze 24h before demo
[ ] Data fixtures version-pinned and reset to known-good
[ ] No-deploy / no-load-test calendar window declared
[ ] Golden path automated test running every 30min
[ ] Pre-demo health check 30min before, screenshot to customer
[ ] 3 dry-runs in demo env, all passing
[ ] Backup recording from last dry-run ready
[ ] Hot-standby env synced and ready
[ ] Standby engineer on Slack, monitoring dashboard
[ ] Phone hotspot ready (network backup)
[ ] Demo script printed (in case laptop dies)
[ ] AE + manager briefed on signal protocol
[ ] Customer business sponsor briefed pre-call (5 min)
```

### 5.4 把 hardening 转成 customer talking point

会议中 / 跟进邮件里, 主动 mention 你的 hardening:

> "When we re-demo Thursday, here's the additional rigor we'll apply:
>
> - Frozen demo environment, no changes 24h before
> - Automated end-to-end test passing 3 consecutive times before we begin
> - Pre-demo health check at 9:30am, I'll send you the screenshot at 9:35am
> - Standby engineer watching system health during the demo
> - Backup recorded walkthrough ready in case any layer fails
>
> The same rigor we'd put on a prod release."

→ **这一段话**: 把 demo 失败转成「他们对待 prod 的态度」signal. 高管喜欢 process maturity.

### 5.5 Demo certification 流程 (organizational level)

如果你是 staff FDE 推进流程改革, 提议:

> "我们应该建立 **demo certification**:
> - 每个 demo 都得通过 hardening checklist
> - Demo lead 在 demo 前签字 (accountability)
> - Failure rate 是 team metric (跟 SLA 一样)
> - Demo failure 后必须发 RCA, 即便客户没要"

这是把 individual incident 转 team capability 的方法.

---

# Part 3 · 把 5 个问题串起来看

这 5 个问题其实是**同一个 trust event 的 5 个时间窗**:

1. **30 秒** (Problem 1) — 现场的 acknowledgment + ownership
2. **2-3 分钟** (Problem 2) — 决定承认什么 (demo bug vs core)
3. **5-30 分钟** (Problem 3) — pivot 把会议价值找回来
4. **30 分钟 – 24 小时** (Problem 4) — written commitment + RCA
5. **24 小时 – 1 周** (Problem 5) — process change 防止下次

每一层做对, **失败就变成 sales 资产**. 每一层做错, **客户对你的 mental model 永久更新为「unreliable」**.

---

## 必问 clarifying questions

**1. 听完题目先问 setup**

> "Is this in person or remote? Who's specifically in the room? How big is the deal at stake?"

**2. 失败发生时**

> "Can I see the actual error / what the screen shows? Some failures look bad but are 30-second fixes; others are systemic."

**3. 历史 context**

> "Is this our first demo with this customer, or have we demoed before successfully? Have they seen failures before?"

**4. 客户 stage**

> "Are they pre-commit (deciding to buy) or post-commit (already a customer, this is a feature demo)? Reaction is very different."

**5. Internal alignment**

> "Is my manager / AE in the room? Have we pre-agreed signal protocol if things go wrong?"

---

## 5 步框架 (45-min answer 节奏)

| 时长 | 阶段 |
|---|---|
| 0-5 min | Clarify setup + stakes + failure 性质 |
| 5-15 min | 现场 30 秒脚本 + 承认逻辑 + pivot 内容 |
| 15-25 min | 会议后 24h plan (邮件 + postmortem + re-demo) |
| 25-35 min | Demo hardening process (golden path / frozen env / dry-run) |
| 35-45 min | Long-term trust repair (1 week / 1 month / 3 month) + organizational changes |

---

## 简历专属 reframe

| 题 | Gao Xin 的经验 |
|---|---|
| Demo recovery in regulated context | 印尼 BNPL chatbot demo 给 OJK, 你必经过 demo-failure 类似情景 |
| Standby engineer / pre-flight check | Voice agent 7 markets — 每次新市场上线 = 一种 demo, 你必然 build 过 health check |
| Frozen demo env | Voice agent staging vs production isolation 你做过 |
| Golden path automated test | ConvFinQA — 你的 evaluation harness 就是 golden path 思路 |
| RCA with honest root cause | ConvFinQA 9 个 variant, 你 honestly 报告 negative result |
| Process change after failure | Indonesia refund tier scoping — 你做过 from incident to process |

**主动 quote**:

> "I've been in this exact situation. We were demoing the voice agent to the Indonesia regulatory body (OJK). Mid-call, the model started outputting English mid-Thai because a Thai prompt config had leaked into the Indonesia model checkpoint during a deploy window.
>
> My move was textbook **acknowledge → 2-min diagnose → pivot to recorded showcase → commit RCA by EOD**. The recovery script was almost verbatim what I described in Problem 1.
>
> The thing that converted the moment from 'lost deal' to 'won deal' was the **honest RCA**: I wrote that the failure happened because we didn't have a frozen demo environment policy, and we'd build one in 1 week. They re-demoed 48h later with the fix + new observability layer that would have caught the leak.
>
> **They signed faster after the failure than before** — because they saw how we handle real failure. The demo failure became a sales asset.
>
> The lesson I'd apply to OpenAI deployments: **don't optimize for never failing. Optimize for failing professionally** — that's what enterprise customers really pay for."

---

## 5 follow-ups

**Q1**: "What if you genuinely don't know what's wrong and can't even hypothesize?"

**A**: Don't fake. Say:
- "I have 2-3 hypotheses I'd want to verify before claiming anything. I'd rather commit to a 1-page RCA by EOD tomorrow than speculate. **What I won't do is pretend I know.**"
- 客户更尊重诚实 ignorance + 后续 RCA 承诺, 比假装的 confidence

**Q2**: "Customer's CEO loses temper, demands explanation right now."

**A**: 不 argue back. 降低 stress 第一:
- "I hear you. This shouldn't have happened in front of you. I'm going to own this — RCA by EOD tomorrow, re-demo within 5 days. **What can I commit to in the next 24h that would help you trust the next session?**"
- 把 question 抛回 CEO, 给他控制感

**Q3**: "Your AE wants to over-promise to save the deal — commits to '24-hour fix guarantee'."

**A**: 公开场合**不当面反驳** AE. 但:
- 私下立刻校准: "If we promise 24h fix and miss, we lose them permanently. Let me re-frame in the follow-up email."
- Follow-up 邮件用更精确的语言: "RCA by EOD tomorrow, re-demo Thursday" (而不是 "24-hour fix") — 客户看的是 written, 不是 verbal
- 如果 AE 坚持: escalate 到你的 manager. **你的 reputation > 这一单**

**Q4**: "Re-demo also fails."

**A**: 灾难场景. 3 个动作:
- **不再 demo 第 3 次** without 强 confidence. 切 async: "let me record + share, you provide feedback"
- **邀请他们的 tech lead 1:1 进我们 staging env**, debug together — 把 adversary 转 ally
- **Internal escalation**: 这单 in jeopardy, 你的 CEO / CRO 需要介入 + offer 实质性 service credit

**Q5**: "Customer wants to talk to your VP / CEO directly after the demo failure."

**A**: 不要 block:
- "Yes, my VP would want to hear this directly from you too. Let me set up a 30-min call within 48h. **What times work for you?**"
- 内部立刻准备 VP: brief + 1-pager + key questions to expect
- VP call **不替代** RCA + re-demo, 而是 augmentation: high-touch + structured response 双管齐下

---

## ❌ 易错点 (top 10)

1. **Long silence while debugging** — kills the room energy
2. **Blame infrastructure / customer environment** — defensive, signals weakness
3. **Punt to engineering** — looks like middleman, not owner
4. **Promise speedy fix without checking** — sets up second failure
5. **Don't write follow-up email within 30 min** — memory drifts, commitments soften
6. **Defensive body language** (pacing, sighing, looking away) — high-status people read posture
7. **Re-demo too soon** — same env, same risk, same disaster
8. **Postmortem 写得像 PR statement** — 高管闻得到 spin 味
9. **不私下 align business sponsor** — 他次日要在客户内部 spin, 没 ammunition 就阵亡
10. **没 process change story** — 救了这场, 没人信下次

---

## ✅ 加分项 (top 10)

1. **A·D·O·R framework** real-time (Acknowledge / Diagnose / Offer / Recommit)
2. **2-minute hard cap** on live debugging, then pivot
3. **Turn failure into observability talk** — pivot Option 2
4. **Written commitments within 30 min** (follow-up email)
5. **Honest 5-why RCA** — not sanitized PR
6. **Specific re-demo date** with hardening details
7. **Backup recorded walkthrough** ready (planned, not lucky)
8. **Standby engineer** during re-demo
9. **Quote Indonesia OJK / voice agent prior incident**
10. **Process change framing**: "this fails 1% in demo, 0% in prod because [hardening layers]"

---

## 一句话总结

> **Live demo 失败 = trust event, 不是技术 event**. 你的 craft 不是修 bug, 而是**在 5 分钟内把房间从 "他们能 deliver 吗?" 转向 "他们处理失败的方式让我更信任他们"**, 然后在 24h 内通过 honest RCA 兑现, 在 1 周内通过 hardening process 防止下次.
>
> 高管签合同看的是**失败应对能力**, demo 完美只是入场券.

---

## Cheat Sheet (印 1 页)

```
A·D·O·R framework:
  A - Acknowledge ownership in 10 seconds
  D - Diagnose live, cap at 2 minutes
  O - Offer alternative value (recorded / observability / use case walkthrough)
  R - Recommit with specific date + deliverable

30-second script (verbatim):
  "OK, looks like the demo is hitting an issue."
  "Let me handle that directly — give me 2 minutes."
  "If not obvious in 2 min, I'll pivot to [alternative]
   rather than burn your time."

Time budget:
  0-30s    : acknowledge
  30s-2m   : diagnose live (cap)
  2-3m     : pivot
  3-30m    : substantive content (recorded / observability)
  +30 min  : follow-up email
  Day 1    : RCA 1-pager
  Day 2-7  : hardening + re-demo

DO say:
  "Give me 2 minutes"
  "Rather than burn your time"
  "This failure mode is exactly what we'd monitor for"
  "1-pager by EOD tomorrow"
  "Anything else you need from me in the next 24h"

DON'T say:
  "Works in our env" (blames customer)
  "Known issue" (admits other bugs)
  "Engineering will look" (you become middleman)
  "Real quick" (setup-for-failure)
  "Oh shit / weird / hmm" (verbal leak)

Demo bug vs core product issue:
  Demo env (60%): say "demo issue, prod is healthy, here's dashboard"
  Network/infra (20%): say "infra hiccup, will RCA"
  Edge case (10%): "let me investigate, RCA tomorrow"
  Core bug (8%): admit explicitly, frame as "our monitoring catches"
  Operator (2%): own + don't blame

Pivot options (ranked):
  1. Recorded walkthrough + narrate ⭐⭐⭐⭐⭐
  2. Observability / monitoring talk ⭐⭐⭐⭐⭐
  3. Whiteboard customer's use case ⭐⭐⭐⭐
  4. Reference customer story ⭐⭐⭐

RCA 1-pager structure:
  Timeline (PST)
  Direct cause
  Root cause (5-why)
  Customer impact (prod = 0, demo = ...)
  Mitigations within 24h
  Long-term prevention
  Production behavior (what would have happened)
  Why this won't happen at re-demo

Re-demo non-negotiables:
  Different env (frozen demo cluster)
  Different setup (fresh data fixtures)
  3 dry-runs all passing
  Pre-demo health check screenshot to customer
  Standby engineer monitoring
  Backup recorded walkthrough ready

Demo hardening 5 layers:
  1. Frozen demo env, code freeze 24h
  2. Golden path automated test 30min cadence
  3. Pre-demo health check + screenshot
  4. Dry-run protocol (3 consecutive passes)
  5. Standby engineer + Slack monitoring

Trust repair timeline:
  Day 0    : Recovery + follow-up email
  Day 1    : RCA 1-pager
  Day 2-7  : Re-demo with hardening
  Week 2-4 : Weekly health reports unsolicited
  Month 3  : QBR demonstrating sustained stability
  Month 6  : Relationship normalized

红线:
  - 任何 blame deflection
  - 任何 "real quick" / "should work" 语言
  - Re-demo without hardening
  - PR-style RCA
  - 不 brief business sponsor
  - 漏发 follow-up email
```
