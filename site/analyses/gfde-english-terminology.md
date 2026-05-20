## 📣 Google FDE 英语面试术语 + 音标发音

**目的**: 让你在面试现场说出这些 term 时**发音正确**, 不被打断 "sorry, what's that?" 干扰节奏。

**怎么用**:
1. 先扫 **🔥 高频高错** section — 中国工程师最常发错的 12 个词
2. 然后按 T1/T2/T3/T4 主题过一遍
3. **每个 term 跟读 3 次** (强制肌肉记忆)
4. **打开 forvo.com 或 dictionary.com 听母语者发音** (IPA 只能近似)

**Legend**: `/IPA/` = 国际音标 · **重音** = 加粗音节 · 🇺🇸 = 美音 · 🇬🇧 = 英音 (有差异时标注)

---

## 🔥 高频高错 (top 12 — 中国工程师最常翻车)

| Term | IPA | 拼读 | 常错读法 | 含义 |
|---|---|---|---|---|
| **idempotent** | /aɪˈdɛm.pə.tənt/ | "eye-**DEM**-puh-tunt" | "eye-dem-PO-tent" ❌ | 幂等 |
| **idempotency** | /ˌaɪ.dɛmˈpoʊ.tən.si/ | "eye-dem-**POH**-tun-see" | 同上 | 幂等性 |
| **niche** | /niːʃ/ 🇺🇸 也念 /nɪtʃ/ | "neesh" | "nitch" 在英国常见 | 细分领域 |
| **cache** | /kæʃ/ | "cash" | "cay-shay" ❌ "kah-chey" ❌ | 缓存 |
| **queue** | /kjuː/ | "kyoo" | 整 5 letters 别都念出来 | 队列 |
| **schema** | /ˈskiː.mə/ | "**SKEE**-mah" | "shee-ma" ❌ | 数据结构 |
| **API** | /eɪ piː aɪ/ | "A-P-I" letter-by-letter | "AY-pie" ❌ | API |
| **JSON** | /ˈdʒeɪ.sɑːn/ | "**JAY**-son" | "jay-ess-oh-en" ❌ | JSON |
| **SQL** | /ˈsiː.kwəl/ or /ˌɛs kjuː ˈɛl/ | "SEE-quel" or "S-Q-L" | 两个都对 | SQL |
| **kubernetes** | /ˌkuː.bərˈnɛ.tiːz/ | "koo-ber-**NET**-eez" | "koo-ber-nets" ❌ | k8s |
| **regex** | /ˈrɛ.dʒɛks/ | "**REJ**-eks" | "ree-jeks" 也可 | 正则 |
| **YAML** | /ˈjæ.məl/ | "**YAM**-el" | "Y-A-M-L" ❌ "ya-mel" | YAML |

---

## 🛠 通用 / 面试场常用动作词

| Term | IPA | 拼读 | 含义 |
|---|---|---|---|
| **clarify** | /ˈklær.ə.faɪ/ | "**KLAIR**-uh-fye" | 澄清 |
| **assumption** | /əˈsʌmp.ʃən/ | "uh-**SUMP**-shun" | 假设 |
| **trade-off** | /ˈtreɪd ɔːf/ | "**TRADE**-off" | 权衡 |
| **prioritize** | /praɪˈɔːr.ə.taɪz/ | "pry-**OR**-uh-tize" | 排优先级 |
| **escalate** | /ˈɛs.kə.leɪt/ | "**ES**-kuh-late" | 上报 / 升级 |
| **mitigate** | /ˈmɪ.tə.ɡeɪt/ | "**MIT**-uh-gate" | 缓解 |
| **caveat** | /ˈkæ.vi.æt/ | "**KA**-vee-at" | 注意点 / 前提 |
| **nuance** | /ˈnuː.ɑːns/ | "**NOO**-ahns" | 细微差别 |
| **granular** | /ˈɡræn.jə.lər/ | "**GRAN**-yuh-ler" | 粒度细 |
| **holistic** | /hoʊˈlɪs.tɪk/ | "ho-**LIS**-tik" | 整体的 |
| **pragmatic** | /præɡˈmæ.tɪk/ | "prag-**MAT**-ik" | 务实的 |
| **robust** | /roʊˈbʌst/ | "ro-**BUST**" | 健壮 |
| **naive** | /nɑːˈiːv/ | "nah-**EEV**" | 朴素的 / 简单的 |
| **elegant** | /ˈɛl.ə.ɡənt/ | "**EL**-uh-gunt" | 优雅的 |
| **canonical** | /kəˈnɑː.nɪ.kəl/ | "kuh-**NON**-i-kul" | 标准的 |
| **decompose** | /ˌdiː.kəmˈpoʊz/ | "dee-kum-**POZE**" | 拆解 |
| **orthogonal** | /ɔːrˈθɑː.ɡə.nəl/ | "or-**THOG**-uh-nul" | 正交 / 不相关 |
| **tractable** | /ˈtræk.tə.bəl/ | "**TRAK**-tuh-bul" | 可解的 |

---

## 1️⃣ T1 — Tool Calling 术语

| Term | IPA | 拼读 | 含义 |
|---|---|---|---|
| **idempotent** | /aɪˈdɛm.pə.tənt/ | "eye-**DEM**-puh-tunt" | 幂等 |
| **idempotency key** | /ˌaɪ.dɛmˈpoʊ.tən.si kiː/ | "eye-dem-**POH**-tun-see key" | 幂等 key |
| **semantics** | /sɪˈmæn.tɪks/ | "si-**MAN**-tiks" | 语义 |
| **at-most-once** | /æt moʊst wʌns/ | "at-most-wons" | 最多 1 次 |
| **at-least-once** | /æt liːst wʌns/ | "at-least-wons" | 至少 1 次 |
| **exactly-once** | /ɪɡˈzækt.li wʌns/ | "ig-**ZAKT**-lee wons" | 恰好 1 次 |
| **retry** | /ˌriːˈtraɪ/ | "ree-**TRY**" | 重试 |
| **backoff** | /ˈbæk.ɔːf/ | "**BACK**-off" | 退避 |
| **exponential backoff** | /ˌɛk.spoʊˈnɛn.ʃəl ˈbæk.ɔːf/ | "ek-spo-**NEN**-shul back-off" | 指数退避 |
| **jitter** | /ˈdʒɪ.tər/ | "**JIT**-er" | 抖动 |
| **circuit breaker** | /ˈsɜːr.kɪt ˈbreɪ.kər/ | "**SIR**-kit **BRAY**-ker" | 熔断器 |
| **fallback** | /ˈfɔːl.bæk/ | "**FALL**-bak" | 降级 |
| **timeout** | /ˈtaɪm.aʊt/ | "**TIME**-out" | 超时 |
| **transient** | /ˈtræn.ʒənt/ 🇺🇸 /ˈtræn.zi.ənt/ 🇬🇧 | "**TRAN**-zhunt" | 短暂的 |
| **deterministic** | /dɪˌtɜːr.məˈnɪs.tɪk/ | "di-tur-min-**IS**-tik" | 确定性的 |
| **race condition** | /ˈreɪs kənˈdɪ.ʃən/ | "race kun-**DISH**-un" | 竞态条件 |
| **mutex** | /ˈmjuː.tɛks/ | "**MEW**-teks" | 互斥锁 |
| **semaphore** | /ˈsɛ.mə.fɔːr/ | "**SEM**-uh-for" | 信号量 |
| **deadlock** | /ˈdɛd.lɑːk/ | "**DED**-lok" | 死锁 |
| **compensating action** | /ˈkɑːm.pən.seɪ.tɪŋ ˈæk.ʃən/ | "**KOM**-pun-say-ting **AK**-shun" | 补偿动作 |
| **rollback** | /ˈroʊl.bæk/ | "**ROLL**-bak" | 回滚 |
| **destructive** | /dɪˈstrʌk.tɪv/ | "di-**STRUK**-tiv" | 破坏性的 |
| **reversible** | /rɪˈvɜːr.sə.bəl/ | "ri-**VUR**-suh-bul" | 可逆的 |
| **atomic** | /əˈtɑː.mɪk/ | "uh-**TOM**-ik" | 原子的 |
| **CAS (compare-and-swap)** | /siː eɪ ɛs/ | "C-A-S" | CAS |
| **audit trail** | /ˈɔː.dɪt treɪl/ | "**AW**-dit trail" | 审计日志 |
| **schema validation** | /ˈskiː.mə ˌvæl.əˈdeɪ.ʃən/ | "**SKEE**-mah val-uh-**DAY**-shun" | schema 验证 |
| **sanitize** | /ˈsæ.nə.taɪz/ | "**SAN**-uh-tize" | 净化 |
| **redact** | /rɪˈdækt/ | "ri-**DAKT**" | 脱敏 |
| **PII** | /piː aɪ aɪ/ | "P-I-I" | 个人身份信息 |
| **prompt injection** | /prɑːmpt ɪnˈdʒɛk.ʃən/ | "prompt in-**JEK**-shun" | 提示注入 |

**面试示例 sentence**:
> "I would make the tool **idempotent** by using an **idempotency key** — that way, if a **retry** happens, we get **exactly-once semantics** at the agent level, even though the underlying delivery is **at-least-once**."

---

## 2️⃣ T2 — RAG / Search 术语

| Term | IPA | 拼读 | 含义 |
|---|---|---|---|
| **embedding** | /ɪmˈbɛd.ɪŋ/ | "im-**BED**-ing" | 向量化 |
| **embed** (v) | /ɪmˈbɛd/ | "im-**BED**" | 向量化 (动) |
| **semantic search** | /sɪˈmæn.tɪk sɜːrtʃ/ | "si-**MAN**-tik search" | 语义搜索 |
| **cosine similarity** | /ˈkoʊ.saɪn ˌsɪ.məˈlær.ə.ti/ | "**KO**-syne sim-uh-**LAR**-uh-tee" | 余弦相似度 |
| **dense vector** | /dɛns ˈvɛk.tər/ | "dense **VEK**-ter" | 稠密向量 |
| **sparse vector** | /spɑːrs ˈvɛk.tər/ | "sparse **VEK**-ter" | 稀疏向量 |
| **hybrid search** | /ˈhaɪ.brɪd sɜːrtʃ/ | "**HY**-brid search" | 混合搜索 |
| **chunk** | /tʃʌŋk/ | "chunk" | 切块 |
| **chunking** | /ˈtʃʌŋ.kɪŋ/ | "**CHUNG**-king" | 切块策略 |
| **overlap** | /ˈoʊ.vər.læp/ | "**OH**-ver-lap" | 重叠 |
| **corpus** | /ˈkɔːr.pəs/ | "**KOR**-pus" | 语料库 |
| **retrieval** | /rɪˈtriː.vəl/ | "ri-**TREE**-vul" | 检索 |
| **retriever** | /rɪˈtriː.vər/ | "ri-**TREE**-ver" | 检索器 |
| **recall** | /ˈriː.kɔːl/ (n) /rɪˈkɔːl/ (v) | "**REE**-kawl" | 召回率 |
| **precision** | /prɪˈsɪ.ʒən/ | "pri-**SIZH**-un" | 精确率 |
| **NDCG** | /ɛn diː siː dʒiː/ | "N-D-C-G" | 归一化折损累计增益 |
| **MRR** | /ɛm ɑːr ɑːr/ | "M-R-R" | 平均倒数排名 |
| **reranker** | /ˌriːˈræŋ.kər/ | "ree-**RANK**-er" | 重排器 |
| **rerank** (v) | /ˌriːˈræŋk/ | "ree-**RANK**" | 重排 |
| **cross-encoder** | /krɔːs ɪnˈkoʊ.dər/ | "cross in-**KO**-der" | 交叉编码器 |
| **bi-encoder** | /baɪ ɪnˈkoʊ.dər/ | "bye in-**KO**-der" | 双塔编码器 |
| **ANN** | /eɪ ɛn ɛn/ | "A-N-N" | 近似最近邻 |
| **HNSW** | /eɪtʃ ɛn ɛs ˈdʌ.bəl juː/ | "H-N-S-W" | 一种 ANN 算法 |
| **BM25** | /biː ɛm ˈtwɛn.ti faɪv/ | "B-M-twenty-five" | BM25 |
| **RRF** | /ɑːr ɑːr ɛf/ | "R-R-F" | 倒数排名融合 |
| **HyDE** | /haɪd/ | "hide" | 假设文档嵌入 |
| **truncate** | /ˈtrʌŋ.keɪt/ | "**TRUNG**-kate" | 截断 |
| **aggregate** | /ˈæ.ɡrə.ɡət/ (n) /ˈæ.ɡrə.ɡeɪt/ (v) | "**AG**-ruh-gut" 名 / "**AG**-ruh-gate" 动 | 聚合 |
| **provenance** | /ˈprɑː.və.nəns/ | "**PROV**-uh-nuns" | 来源 / 出处 |
| **citation** | /saɪˈteɪ.ʃən/ | "sy-**TAY**-shun" | 引用 |
| **hallucination** | /həˌluː.səˈneɪ.ʃən/ | "huh-loo-suh-**NAY**-shun" | 幻觉 |
| **grounding** | /ˈɡraʊn.dɪŋ/ | "**GROUN**-ding" | 信息扎根 |
| **context window** | /ˈkɑːn.tɛkst ˈwɪn.doʊ/ | "**KON**-tekst **WIN**-doh" | 上下文窗口 |

**面试示例 sentence**:
> "For this **corpus**, I'd use **hybrid retrieval** — **BM25** captures rare keywords like product **SKUs**, while **dense embedding** handles **semantic** paraphrasing. Then a **cross-encoder reranker** takes top-50 to top-10, giving us ~15% **NDCG** lift over pure **dense**."

---

## 3️⃣ T3 — LLM Engineering 术语

| Term | IPA | 拼读 | 含义 |
|---|---|---|---|
| **stateless** | /ˈsteɪt.ləs/ | "**STATE**-less" | 无状态 |
| **stateful** | /ˈsteɪt.fəl/ | "**STATE**-ful" | 有状态 |
| **latency** | /ˈleɪ.tən.si/ | "**LAY**-tun-see" | 延迟 |
| **throughput** | /ˈθruː.pʊt/ | "**THROO**-put" (注意 th 音) | 吞吐量 |
| **concurrency** | /kənˈkɜːr.ən.si/ | "kun-**KUR**-un-see" | 并发 |
| **parallelism** | /ˈpær.ə.lə.lɪ.zəm/ | "**PAIR**-uh-lel-iz-em" | 并行 |
| **horizontal scale** | /ˌhɔːr.əˈzɑːn.təl skeɪl/ | "hor-uh-**ZON**-tul scale" | 水平扩展 |
| **vertical scale** | /ˈvɜːr.tə.kəl skeɪl/ | "**VUR**-ti-kul scale" | 垂直扩展 |
| **multi-tenant** | /ˌmʌl.ti ˈtɛ.nənt/ | "**MUL**-tee **TEN**-unt" | 多租户 |
| **isolation** | /ˌaɪ.səˈleɪ.ʃən/ | "eye-suh-**LAY**-shun" | 隔离 |
| **saga** (pattern) | /ˈsɑː.ɡə/ | "**SAH**-gah" | saga 模式 |
| **outbox** | /ˈaʊt.bɑːks/ | "**OUT**-boks" | outbox 模式 |
| **eventual consistency** | /ɪˈvɛn.tʃu.əl kənˈsɪs.tən.si/ | "i-**VEN**-choo-ul kun-**SIS**-tun-see" | 最终一致性 |
| **queue** | /kjuː/ | "**KYU**" | 队列 |
| **backpressure** | /ˈbæk.prɛ.ʃər/ | "**BAK**-presh-er" | 背压 |
| **quantization** | /ˌkwɑːn.tə.ˈzeɪ.ʃən/ | "kwon-tuh-**ZAY**-shun" | 量化 |
| **distillation** | /ˌdɪs.təˈleɪ.ʃən/ | "dis-tuh-**LAY**-shun" | 蒸馏 |
| **inference** | /ˈɪn.fər.əns/ | "**IN**-fer-uns" | 推理 |
| **serving** | /ˈsɜːr.vɪŋ/ | "**SUR**-ving" | 服务化 |
| **batching** | /ˈbæ.tʃɪŋ/ | "**BACH**-ing" | 批处理 |
| **continuous batching** | /kənˈtɪ.nju.əs ˈbæ.tʃɪŋ/ | "kun-**TIN**-yu-us batching" | 连续批处理 |
| **prefix** | /ˈpriː.fɪks/ | "**PREE**-fiks" | 前缀 |
| **KV cache** | /keɪ viː kæʃ/ | "K-V cash" | KV 缓存 |
| **attention** | /əˈtɛn.ʃən/ | "uh-**TEN**-shun" | 注意力 |
| **transformer** | /trænsˈfɔːr.mər/ | "trans-**FOR**-mer" | transformer |
| **speculative decoding** | /ˈspɛ.kjə.lə.tɪv ˌdiːˈkoʊ.dɪŋ/ | "**SPEK**-yuh-luh-tiv dee-**KO**-ding" | 推测解码 |
| **pipeline parallel** | /ˈpaɪp.laɪn ˈpær.ə.lɛl/ | "**PIPE**-line **PAIR**-uh-lel" | 流水线并行 |
| **tensor parallel** | /ˈtɛn.sər ˈpær.ə.lɛl/ | "**TEN**-ser **PAIR**-uh-lel" | 张量并行 |
| **TTFT** | /tiː tiː ɛf tiː/ | "T-T-F-T" | 首 token 延迟 |
| **TPOT** | /tiː piː oʊ tiː/ | "T-P-O-T" | per token 延迟 |
| **vLLM** | /viː ɛl ɛl ɛm/ | "V-L-L-M" 或 "vee-LLM" | vLLM |
| **PagedAttention** | /peɪdʒd əˈtɛn.ʃən/ | "**PAGED** uh-tenshun" | PagedAttention |
| **observability** | /əbˌzɜːr.vəˈbɪ.lə.ti/ | "ob-zer-vuh-**BIL**-uh-tee" | 可观测性 |
| **tracing** | /ˈtreɪ.sɪŋ/ | "**TRAY**-sing" | 追踪 |
| **telemetry** | /təˈlɛ.mə.tri/ | "tuh-**LEM**-uh-tree" | 遥测 |
| **MCP** | /ɛm siː piː/ | "M-C-P" | Model Context Protocol |
| **proxy** | /ˈprɑːk.si/ | "**PROK**-see" | 代理 |
| **gateway** | /ˈɡeɪt.weɪ/ | "**GATE**-way" | 网关 |
| **idempotent** | /aɪˈdɛm.pə.tənt/ | (见 T1) | 幂等 |

**面试示例 sentence**:
> "Default to **stateless** — client passes **conversation ID**, server reconstructs context using **KV cache** and **prefix caching**. For **voice agents** that need < 300ms **TTFT**, we use **WebSocket** with per-call **stateful** actor."

---

## 4️⃣ T4 — FDE Delivery 术语

| Term | IPA | 拼读 | 含义 |
|---|---|---|---|
| **scoping** | /ˈskoʊ.pɪŋ/ | "**SKO**-ping" | 范围界定 |
| **stakeholder** | /ˈsteɪk.hoʊl.dər/ | "**STAKE**-hol-der" | 利益相关人 |
| **discovery** | /dɪˈskʌ.və.ri/ | "di-**SKUH**-ver-ee" | 调研 |
| **KPI** | /keɪ piː aɪ/ | "K-P-I" | 关键绩效指标 |
| **baseline** | /ˈbeɪs.laɪn/ | "**BASE**-line" | 基线 |
| **decomposition** | /ˌdiː.kɑːm.pəˈzɪ.ʃən/ | "dee-kom-puh-**ZISH**-un" | 拆解 |
| **prototype** | /ˈproʊ.tə.taɪp/ | "**PRO**-toh-type" | 原型 |
| **MVP** | /ɛm viː piː/ | "M-V-P" | 最小可行产品 |
| **pilot** | /ˈpaɪ.lət/ | "**PY**-lut" | 试点 |
| **iterate** | /ˈɪ.tə.reɪt/ | "**IT**-uh-rate" | 迭代 |
| **iteration** | /ˌɪ.təˈreɪ.ʃən/ | "it-uh-**RAY**-shun" | 迭代 (名) |
| **ambiguity** | /ˌæm.bəˈɡjuː.ə.ti/ | "am-buh-**GYU**-uh-tee" | 模糊性 |
| **workflow** | /ˈwɜːrk.floʊ/ | "**WURK**-flo" | 工作流 |
| **abstraction** | /æbˈstræk.ʃən/ | "ab-**STRAK**-shun" | 抽象 |
| **abstract** | /ˈæb.strækt/ (n/adj) /æbˈstrækt/ (v) | "**AB**-strakt" 名 / "ab-**STRAKT**" 动 | 抽象 |
| **escalation** | /ˌɛs.kəˈleɪ.ʃən/ | "es-kuh-**LAY**-shun" | 升级 / 上报 |
| **handoff** | /ˈhænd.ɔːf/ | "**HAND**-off" | 移交 |
| **confidence** | /ˈkɑːn.fə.dəns/ | "**KON**-fuh-duns" | 置信度 |
| **calibration** | /ˌkæ.ləˈbreɪ.ʃən/ | "kal-uh-**BRAY**-shun" | 校准 |
| **autonomy** | /ɔːˈtɑː.nə.mi/ | "aw-**TON**-uh-mee" | 自主性 |
| **autonomous** | /ɔːˈtɑː.nə.məs/ | "aw-**TON**-uh-mus" | 自主的 |
| **permission** | /pərˈmɪ.ʃən/ | "per-**MISH**-un" | 权限 |
| **least privilege** | /liːst ˈprɪ.və.lɪdʒ/ | "least **PRIV**-uh-lij" | 最小权限 |
| **IAM** | /aɪ eɪ ɛm/ | "I-A-M" | 身份访问管理 |
| **OAuth** | /ˈoʊ.ɔːθ/ | "**OH**-awth" | OAuth |
| **OBO (on-behalf-of)** | /oʊ biː oʊ/ | "O-B-O" or "on-buh-**HAF**-of" | 代表用户 |
| **audit** | /ˈɔː.dɪt/ | "**AW**-dit" | 审计 |
| **compliance** | /kəmˈplaɪ.əns/ | "kum-**PLY**-uns" | 合规 |
| **SOC 2** | /sɒk tuː/ | "sock two" | SOC 2 认证 |
| **HIPAA** | /ˈhɪ.pə/ | "**HIP**-uh" | 美国医疗隐私法 |
| **GDPR** | /dʒiː diː piː ɑːr/ | "G-D-P-R" | 欧盟数据保护 |
| **PII** | /piː aɪ aɪ/ | "P-I-I" | 个人身份信息 |
| **PHI** | /piː eɪtʃ aɪ/ | "P-H-I" | 个人健康信息 |
| **adversarial** | /ˌæd.vərˈsɛr.i.əl/ | "ad-ver-**SAIR**-ee-ul" | 对抗的 |
| **mitigation** | /ˌmɪ.təˈɡeɪ.ʃən/ | "mit-uh-**GAY**-shun" | 缓解措施 |
| **graceful degradation** | /ˈɡreɪs.fəl ˌdɛɡ.rəˈdeɪ.ʃən/ | "**GRACE**-ful deg-ruh-**DAY**-shun" | 优雅降级 |

**面试示例 sentence**:
> "My first week is **discovery** — 5 **stakeholder** interviews, **baseline** the **KPI**, and produce a 1-page design. By week 3 the customer sees a working **MVP**. The **trust ladder** starts with agent-suggest + human-approve, then graduates to **autonomous** within bounds once we have **calibration** data."

---

## 5️⃣ 面试常用 sentence starter (背下来用)

### 🟢 Clarifying (clarifying question 开场)

| English | 中文 |
|---|---|
| "Before I dive in, let me ask a few clarifying questions." | 深入之前我问几个澄清问题 |
| "I'd like to make sure I understand the scope correctly." | 我想确认理解准确 |
| "What's the **primary KPI** we're optimizing for?" | 主要 KPI 是什么 |
| "Could you walk me through a typical user journey?" | 走一遍用户路径 |
| "What's the **latency budget** end-to-end?" | 端到端延迟预算 |
| "Are we optimizing for **latency**, **throughput**, or **cost**?" | 优化哪个 |
| "What's the **failure mode** if this goes wrong?" | 出错时的失败模式 |
| "Is this **read-heavy** or **write-heavy**?" | 读多还是写多 |

### 🟢 Stating assumptions

| English | 中文 |
|---|---|
| "Let me state my assumptions explicitly..." | 我明确说一下假设 |
| "Assuming X is the case, I would..." | 假设 X 的话, 我会... |
| "For the sake of this discussion, let's assume..." | 为讨论方便, 假设... |
| "I'm going to make a simplifying assumption that..." | 做一个简化假设 |

### 🟢 Trade-off framing

| English | 中文 |
|---|---|
| "There's a clear **trade-off** here between X and Y." | 这里 X 和 Y 有明显权衡 |
| "On one hand... on the other hand..." | 一方面... 另一方面... |
| "The **tension** is between..." | 矛盾在于... |
| "Given the constraints, I'd lean towards..." | 给定约束, 我倾向于... |
| "**Pragmatically speaking**..." | 务实地说... |

### 🟢 Hedging (不确定时的话术)

| English | 中文 |
|---|---|
| "I'm not 100% sure, but I think..." | 不完全确定, 但我认为... |
| "**It depends on**..." | 看情况 / 取决于... |
| "My initial intuition is X, but I'd want to validate by..." | 直觉 X, 但我想通过 Y 验证 |
| "This is a bit outside my direct experience, but based on first principles..." | 这超出我直接经验, 但基于第一性原理... |
| "I'd want to dig deeper before committing to..." | 在 commit 前我想深入了解 |

### 🟢 Pushing back / 礼貌反驳

| English | 中文 |
|---|---|
| "I see where you're coming from, but I'd push back on..." | 理解你的角度, 但我会质疑... |
| "That works for the happy path, but **what about** ...?" | 正常路径可以, 但 X 怎么办 |
| "I'd be cautious about that — here's why..." | 我会谨慎 — 原因是... |
| "**Devil's advocate**: what if..." | 唱反调: 如果... |
| "Have we considered the alternative of...?" | 我们考虑过... 替代方案吗 |

### 🟢 Showing experience (引出简历故事)

| English | 中文 |
|---|---|
| "I've seen this exact pattern at TikTok where..." | 我在 TikTok 见过同样的模式... |
| "**In production**, what I've found is..." | 生产环境我发现... |
| "Drawing from my voice agent work..." | 根据我做 voice agent 的经验... |
| "I learned this the hard way when..." | 我吃过亏: ... |
| "A **real-world gotcha** is..." | 实际坑是... |

### 🟢 Closing / 总结

| English | 中文 |
|---|---|
| "To summarize my approach..." | 总结一下方案 |
| "The **key insight** is..." | 关键 insight 是 |
| "If we have more time, I'd also want to discuss..." | 时间允许的话, 我还想讨论 |
| "**Open questions** I'd flag for follow-up..." | 我会标记的 open question |
| "Does this approach align with what you had in mind?" | 跟你想的一致吗 |

---

## 6️⃣ 数字 / 单位的英语 (容易卡)

| 写法 | 英语读法 |
|---|---|
| **10K QPS** | "ten K Q-P-S" or "ten thousand queries per second" |
| **1M users** | "one million users" 或 "a million users" |
| **1B parameters** | "one billion parameters" |
| **3x speedup** | "three-X speedup" or "three times faster" |
| **p99 latency** | "P-ninety-nine latency" |
| **99.99%** | "four nines" |
| **5ms** | "five milliseconds" |
| **2.5 GB** | "two-point-five gigabytes" |
| **128K tokens** | "128 K tokens" |
| **$0.001/1K tokens** | "point-zero-zero-one dollars per thousand tokens" |
| **24/7** | "twenty-four-seven" |
| **A/B test** | "A-B test" |
| **k=10** | "K equals ten" |
| **O(n log n)** | "Big O of n log n" |
| **q1 2026** | "Q-one twenty-twenty-six" |

---

## 7️⃣ 训练建议

**Day 1** (今天):
- 通读全表, 标记 **不会读** 和 **没听过** 的 ~20 个
- 这 20 个去 **forvo.com** 听 3 遍

**Day 2-3**:
- 跟读所有 **🔥 高频高错** 词 (idempotent, niche, cache, queue, schema, kubernetes 这些一定不能错)
- 每天通读 1 个 section (T1/T2/T3/T4)

**Day 4-5**:
- 把 sentence starter (第 5 节) **背下来**
- 模拟面试: 录音自己讲, 听回放找发音错的

**Day 6** (前 1 天):
- 只过 🔥 高频 + sentence starter
- 不要塞新内容
- 早睡

**面试当天**:
- 提前 30 min 出门 (网络面试也要)
- 暖嗓: 朗读 sentence starter 5 遍
- 紧张时 **慢说**, 比快错好

---

## 8️⃣ 易错对比 (中国工程师高频混淆)

| ❌ 常错 | ✅ 正确 |
|---|---|
| /ˈɪmpɔtənt/ "impotent" 😅 | /aɪˈdɛmpətənt/ "eye-DEMP-tent" (idempotent) |
| /ˈʃiː.mə/ "shee-ma" | /ˈskiː.mə/ "SKEE-ma" (schema) |
| /eɪ pi/ "AY-pee" | /eɪ piː aɪ/ "A-P-I" (API) |
| /ˈkaʊ.bər.nɛts/ | /ˌkuː.bərˈnɛ.tiːz/ "koo-ber-NET-eez" (kubernetes) |
| /ˈθru pʊt/ "throo put" 太轻 | /ˈθruː.pʊt/ "THROO-put" — 注意 'th' 咬舌 |
| /ˈkæʃ.eɪ/ "cash-AY" | /kæʃ/ "cash" (cache) |
| /ˈnaɪv/ "knive" | /nɑːˈiːv/ "nah-EEV" (naive) |
| /ˈkjuː ɛ ʌ ɛ/ 字母都念 | /kjuː/ "kyoo" 一个音 (queue) |
| /ˈsɛkʊəl/ "se-kyu-el" | /ˈsiː.kwəl/ "SEE-quel" (SQL) |
| /ˈsoʊsi tuː/ | /sɒk tuː/ "sock two" (SOC 2) |
| /haɪ pə/ "hai-pa" | /ˈhɪ.pə/ "HIP-ah" (HIPAA) |
| /ˈmɪ.tɪ.geɪt/ 重音错 | /ˈmɪ.tə.ɡeɪt/ "**MIT**-uh-gate" |

---

## Cheat Sheet (印 1 页随身)

```
🔥 别读错:
  idempotent: eye-DEM-puh-tunt
  schema: SKEE-ma
  cache: cash
  queue: kyoo
  niche: neesh
  kubernetes: koo-ber-NET-eez
  YAML: YAM-el
  HIPAA: HIP-uh
  SOC 2: sock two
  JSON: JAY-son
  regex: REJ-eks
  naive: nah-EEV

🟢 开场万能:
  "Before I dive in, let me ask a few clarifying questions."
  "What's the primary KPI here?"
  "What's the latency budget?"

🟢 假设:
  "Assuming X, I would..."
  "Let me state my assumptions..."

🟢 权衡:
  "There's a clear trade-off between..."
  "On one hand... on the other..."

🟢 不确定:
  "It depends on..."
  "My intuition is X, but I'd validate by..."

🟢 经验背书:
  "I've seen this at TikTok where..."
  "In production, what I found is..."
  "I learned this the hard way when..."

🟢 总结:
  "To summarize my approach..."
  "Key insight is..."
  "Does this align with what you had in mind?"
```
