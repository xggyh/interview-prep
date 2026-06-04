## Q18 · 不用托管服务, 在 1000 万向量找 top-k

> "You have **10 million 768-dim vectors** and need to find the **top-k most similar** to a query vector in **under 50ms p99**. **No managed service** (no Vertex AI Vector Search, Weaviate). You can use libraries. **Walk through the algorithms, pick one, implement it, justify**."

**中文翻译**:

> "你有 **1000 万个 768 维向量**, 要在 **p99 50ms 之内**找到跟 query 向量**最相似的 top-k 个**. **不能用托管服务** (no Vertex AI Vector Search, Weaviate 这种). 可以用库. **过一遍算法, 选一个, 实现, 给出理由**."

**Round**: Coding (60 min)
**出处**: Exponent 2026 FDE · 公司: **Scale AI**, OpenAI, Anthropic
**难度**: Hard
**主要技能**: ANN algorithms (HNSW / IVF-PQ), recall vs latency, memory budget, library knowledge

---

## 📖 术语速查 (本题用到的)

> ANN 是向量检索硬骨头. 这堆术语必须张口就来, 否则面试官问哪个算法你蒙圈.

### ANN (Approximate Nearest Neighbor) 算法

| 术语 | 解释 |
|---|---|
| **ANN (Approximate Nearest Neighbor)** ⭐ | 近似最近邻搜索. 牺牲一点 recall 换巨大 speedup. 大规模向量检索必走. |
| **k-NN (exact)** | 精确 k 最近邻. Brute force O(N×d) per query. 10M × 768d → 770ms, 慢. |
| **HNSW (Hierarchical Navigable Small World)** ⭐ | 分层小世界图. 从顶层稀疏图 navigate 到底层密集图. SOTA recall × latency 在内存够时. |
| **IVF (Inverted File Index)** | k-means 把 N 向量聚成 K cluster, query 只搜 nprobe 个最近 cluster. |
| **IVF-PQ (IVF + Product Quantization)** ⭐ | IVF + 每向量切 M 段, 每段 8-bit 量化. 10M × 96 bytes = 1GB 总, 但 recall 损 5-10%. |
| **LSH (Locality Sensitive Hashing)** | 哈希让相似向量落同 bucket. 高维 recall 烂, 过时. |
| **ScaNN (Google)** | 学习的 quantization + asymmetric distance. SOTA 但 ops 复杂. |
| **DiskANN (Microsoft)** | SSD 上的 HNSW. 1B 向量单机, 96% recall, 1ms p99. 1B+ 场景关键. |
| **Annoy (Spotify)** | 老式随机树 ANN. Build 后 immutable. 简单但不 SOTA. |

### HNSW 参数

| 术语 | 解释 |
|---|---|
| **`M` (max edges per node)** ⭐ | 图节点度数上限. 高 M → 高 recall + 高内存. 32 是 sweet spot. |
| **`ef_construction`** | Build 时探索的候选数. 高 → 图质量好 + build 慢. 200 默认. |
| **`ef_search` (or `ef`)** ⭐ | Query 时探索的候选数. **可在线调!** 100 → recall 0.95 1ms; 500 → recall 0.995 5ms. |
| **`max_elements`** | 索引容量上限. 加 20% 余量给增长. |

### 量化 / 压缩

| 术语 | 解释 |
|---|---|
| **Product Quantization (PQ)** ⭐ | 把 d 维向量切 M 段, 每段独立 k-means 量化成 8-bit 码本 index. 768d × float32 = 3KB → 96 bytes. |
| **Scalar Quantization (SQ)** | 每维独立量化 (float32 → int8). 4x 压缩, recall 损小. |
| **Binary embedding** | 1-bit per dim. 4096 dim = 512 bytes/vec. recall ~80%. |
| **fp16 / bf16** | 半精度浮点. 2x 压缩, 几乎无损. |
| **Quantization-aware training** | 训练时就考虑量化, 比 post-hoc 准. |

### 距离 / Similarity

| 术语 | 解释 |
|---|---|
| **Cosine similarity** | `dot(a, b) / (|a| × |b|)`. L2 normalize 后等价 dot product. |
| **Inner product (IP / dot product)** | `Σ aᵢ × bᵢ`. 无 bound. |
| **L2 distance (Euclidean)** | `√Σ(aᵢ - bᵢ)²`. 跟 cosine 不等价但相关. |
| **Asymmetric distance (ScaNN)** | query 不量化, doc 量化 → 算 distance 时用 query 原始精度. 比 symmetric 准. |

### 性能 / 复杂度

| 术语 | 解释 |
|---|---|
| **Recall@k** ⭐ | top-k 里有多少正确. 0.98 = 100 query 中 98 个 top-10 含真 top-1. |
| **Latency p50 / p99** | 中位 / 99 分位延迟. p99 是 SLA 标准. |
| **Throughput / QPS** | Queries Per Second. 单机 HNSW 16-core ~1000 QPS. |
| **SIMD / AVX2 / AVX-512** | CPU 向量化指令. faiss 内部用. 决定 brute force 速度 (10 GFLOPS). |
| **GFLOPS / TFLOPS** | 每秒 10⁹ / 10¹² 浮点运算. CPU AVX2 ~10 GFLOPS, A100 ~30 TFLOPS. |
| **`hnswlib`** ⭐ | C++ HNSW 库 + Python binding. 不依赖 FAISS, 更轻. |
| **`faiss-cpu` / `faiss-gpu`** | Facebook FAISS, 包 HNSW/IVF/PQ 全家桶. |
| **`cuVS` (RAPIDS)** | NVIDIA 的 GPU vector search 库. |

### 工程 / Production

| 术语 | 解释 |
|---|---|
| **mmap (memory-mapped file)** ⭐ | OS 把文件映射到进程内存. 多 process 共享, OS page cache 友好. 大 index 必备. |
| **Tombstone** | 删除标记 (不真删, 留位). HNSW `mark_deleted` 是 tombstone. 累积过多触发 rebuild. |
| **Active/passive index swap** | 新 index 后台 build, 完成后原子切换 (atomic pointer swap). 旧 index drain 后回收. |
| **Incremental insert** | 不重 build 整 index, 增量加点. HNSW 支持, IVF / Annoy 不支持. |
| **Sharding** | N 个机器各 N 分之 1 向量, fan-out + top-k merge. 50M+ 必走. |
| **Filter (metadata filter)** | "similar to query AND created_at > 2024-01". HNSW 原生不支持, Vertex AI Vector Search 集成. |
| **Post-filter vs Pre-filter** | Post = 先 retrieve 后 filter (top-100 → top-10); Pre = 按 filter 分 index. |
| **Cold start / Pre-warm** | 进程启动后 OS page cache 没数据, 首查询慢. Pre-run 几个 query 把 page 拉进 RAM. |
| **`/healthz`** | K8s health endpoint. Known-answer query 验 index 装载正确. |

### 数据 / 实验

| 术语 | 解释 |
|---|---|
| **`.npz` (NumPy zip)** | NumPy 多 array 序列化格式. `np.load(allow_pickle=True)`. |
| **`np.linalg.norm(x, axis=1, keepdims=True)`** | 沿行算 L2 范数, 保 dim. Normalize 必备. |
| **Ground truth (brute force)** | 用 O(N) brute force 算真 top-k, 跟 ANN 结果比测 recall. |
| **A/B test (online recall)** | 两 ef 各 50% 流量, 看用户 KPI (点击 / 转化) 差别. |

### 比较 / 替代

| 术语 | 解释 |
|---|---|
| **`sklearn.NearestNeighbors`** | sklearn 实现. KD-tree / Ball-tree, 高维 (>~20d) 不工作. 这题不用. |
| **ColBERT / Multi-vector** | 每 token 一个向量, 检索时 query token × doc token max-pool. 准 + 慢. |
| **Vespa** | Yahoo 开源搜索引擎, 含向量 + 文本混合. |
| **Recsys 100M+ scale** | 推荐系统千万到亿向量. IVF-PQ 主流, 因 memory 受限. |

---

## 这道题在考什么

10M × 768d brute force =  10M × 768 × 4 bytes = **30 GB** floats + 10M × 768 multiplications per query = ~7.6B FLOPs ≈ 5-50s on CPU. 不能 brute force. 必上 ANN (Approximate Nearest Neighbor). 考的是:

1. **能不能算 memory + compute** — 30GB / 7.6B FLOPs 不是猜的, 现场算给面试官看
2. **ANN 算法选型** — HNSW vs IVF vs IVF-PQ vs LSH 各自原理 + 复杂度 + 调参
3. **Recall vs latency vs memory 三角** — 不可能全都要; 你选了哪两个牺牲哪个
4. **Library knowledge** — `faiss`, `hnswlib`, `scann`, `annoy` — 你能不能讲清楚每个 API 大致
5. **Build time + index size** — 加新 vector 怎么办 (re-build vs incremental)
6. **实测 protocol** — recall@10, latency p99, throughput, 怎么 measure
7. **Production wrap** — index serving (single-machine RAM-based), reload on update, query batching

Scale AI 真做的: ImageNet 12M, Recsys 100M+ — ANN 是日常.

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|------|--------|--------|
| 1 | Clarify | 0-5 min | 数据更新频率, recall 要求, query QPS, memory budget | "5 things..." |
| 2 | Numbers + brute force ruled out | 5-10 min | 现场算: 30GB / 7.6B FLOP / 5-50s — 不行 | "Let me size up brute force first..." |
| 3 | Algorithm survey | 10-20 min | LSH / IVF / IVF-PQ / HNSW / ScaNN 对比表 | "Five algorithms; here's the comparison." |
| 4 | Pick HNSW + 论证 | 20-25 min | M=32, ef=200, build 1h, query 1-5ms | "HNSW wins on recall × latency at this scale." |
| 5 | Implement | 25-45 min | hnswlib build + save + query | "I'll write build, then query." |
| 6 | Eval | 45-55 min | recall@10, p99 latency, throughput | "Three measurements that matter..." |
| 7 | Productionize | 55-60 min | shards, update, batch, GPU option | "Three production considerations..." |

---

## 必问 clarifying questions

**1. Update pattern**

> "Are vectors static or do they grow? Insertions per day? Deletions?"

Why: HNSW supports incremental insert; IVF needs full rebuild. Annoy is immutable after build.

**2. Recall requirement**

> "What recall@k do we need? 0.95? 0.99?"

Why: 0.95 lets us use heavily-quantized IVF-PQ; 0.99 forces HNSW or bigger ef.

**3. QPS + latency**

> "Avg/peak QPS? p50 / p99 latency budget?"

Why: 50ms p99 doable on single machine HNSW; 5ms p99 requires GPU or sharded.

**4. Memory budget**

> "How much RAM available? 64GB? 256GB?"

Why: 30GB raw vectors. HNSW adds ~50% for graph. IVF-PQ shrinks to ~1GB but lossy.

**5. Filter at query?**

> "Do we filter by metadata (e.g., 'similar to query AND created in 2024')?"

Why: Most ANN libs are weak at filter; needs hybrid.

**6. Single-machine OK?**

> "Can we host on one fat machine, or distributed?"

Why: 10M / 768d 单机 fine (~50GB total). 100M 必 shard.

**7. Hosted constraint**

> "No managed service — does that include cloud GPU? Or only no Vertex AI Vector Search-like?"

Why: 决定能不能用 cuVS / faiss-gpu.

---

## 详细解题流程

### Step 1: Numbers first (先算数, 5-10 min) — 现场算给面试官看

```
N = 10_000_000
d = 768
size per vector = 4 bytes (float32) * 768 = 3072 bytes ≈ 3KB
total raw = 10M × 3KB = 30 GB

Brute force per query:
  - dot product 10M times × 768 dims = 7.68 × 10^9 multiply-add
  - On CPU AVX2 ~10 GFLOPS = 0.77 s per query
  - On GPU A100 ~30 TFLOPS = 0.25 ms per query (but PCIe transfer + dispatch ~ 5-10ms)

→ Brute CPU = 770ms — way over 50ms budget. ANN required.

50ms budget breakdown:
  - Query embed: 5ms (small embedder)
  - Index lookup: 30ms (target)
  - Post-process (rerank/metadata): 10ms
  - Network overhead: 5ms
  → 30ms for index = HNSW with ef=200 typically 1-5ms in this scale, plenty of room.
```

**讲**: "Brute force ruled out. We need ANN. Let me compare 5 algorithms..."

### Step 2: Algorithm survey (算法对比, 8-10 min)

```
=== LSH (Locality Sensitive Hashing) ===
  Idea: hash similar vectors to same bucket
  Pros: dead simple, append-only, low memory
  Cons: recall poor at high dim; many hash tables needed
  Used by: Spotify (old), some recsys
  Recall@10 @ N=10M: ~70-85% with tuning
  Latency: 10-30ms
  Memory: 1-3x raw (hash tables)
  Build: O(N × T tables × hash_dim)
  Verdict: outdated for 768d

=== IVF (Inverted File Index, k-means partition) ===
  Idea: cluster N vectors into K centroids; query searches nearest M centroids' members
  Pros: fast build (~30 min on 10M); easy parallel
  Cons: high recall needs many probes; lossy near cluster boundaries
  Used by: FAISS (very common), Milvus
  Recall@10 @ N=10M, K=10000, nprobe=64: ~92-95%
  Latency: 5-20ms (CPU)
  Memory: ~30GB (still full vectors) + cluster info
  Build: 30 min - 2 hr
  Verdict: solid; main weakness is still 30GB RAM

=== IVF-PQ (IVF + Product Quantization) ===
  Idea: IVF + compress each vector into M sub-vectors, each sub quantized to 8 bits
  Pros: TINY memory (768d/M=8 = 96 codes × 1 byte = ~96 bytes/vec) → 10M × 96 = 1GB total
  Cons: significant recall loss (vector is approximate)
  Used by: FAISS, Vespa (most cost-optimized prod systems)
  Recall@10 @ N=10M, K=4096, nprobe=64, M=64 8-bit: ~85-90%
  Latency: 2-10ms (small footprint = cache friendly)
  Memory: ~1-3 GB
  Build: 1-3 hr (PQ training)
  Verdict: best when memory tight, can lose 5-10% recall

=== HNSW (Hierarchical Navigable Small World) ===
  Idea: layered graph; navigate from top sparse to bottom dense
  Pros: SOTA recall × latency; supports incremental insert
  Cons: 1.5-2x memory of raw (graph edges); slow to build (1-3 hr)
  Used by: hnswlib, FAISS, pgvector, Weaviate, Vertex AI Vector Search
  Recall@10 @ N=10M, M=32, ef=200: ~98-99%
  Latency: 1-5ms (CPU)
  Memory: ~50GB (raw + graph)
  Build: 1-3 hr (parallel)
  Verdict: BEST default for this size; weakness is RAM hungry

=== ScaNN (Google) ===
  Idea: learned quantization + asymmetric distance
  Pros: SOTA on some benchmarks
  Cons: less commodity tooling; harder ops
  Recall@10: ~95-99%
  Latency: 1-3ms
  Memory: depends on config
  Verdict: niche; HNSW is easier to ship.
```

| Algo | Recall@10 | Latency | Memory | Build | Incremental |
|------|-----------|---------|--------|-------|-------------|
| Brute force | 1.0 | 770ms | 30GB | 0 | yes |
| LSH | 0.75 | 20ms | 60GB | 30min | yes |
| IVF | 0.93 | 10ms | 30GB | 1hr | rebuild centroids |
| IVF-PQ | 0.87 | 5ms | 1-3GB | 2hr | rebuild PQ |
| **HNSW** | **0.98** | **2-5ms** | **50GB** | **2hr** | **yes** |
| ScaNN | 0.97 | 2ms | varies | 2hr | partial |

### Step 3: Pick HNSW + parameter rationale (选 HNSW 并讲参数理由, 5 min)

**Choice**: HNSW. Why:

1. **Recall@10 ≈ 0.98** — best in class without GPU
2. **Latency 1-5ms** — leaves headroom in 50ms budget
3. **Incremental insert** supported (Q's 5000 new vectors / day OK)
4. **Library mature**: `hnswlib` (pure C++ binding) or FAISS HNSW
5. **Memory 50GB**: fits on a 64GB box. Single machine.

**Trade-off acknowledged**: "If we had only 8GB RAM, I'd switch to IVF-PQ and accept ~0.87 recall. If we had 1 BILLION vectors, I'd shard HNSW or use GPU IVF."

**Parameter rationale**:

```
M = 32          (edges per node in graph at top layers)
  - Higher M → better recall, more memory
  - 16 is default-light, 32 is "high quality", 64 wastes memory
  - For 10M 768d: 32 sweet spot

ef_construction = 200
  - How many candidates to explore during build
  - Higher → better graph quality, slower build
  - 200 default; 400 for ultra-high recall

ef_search = 200 (tunable at query time!)
  - How many candidates to explore at query time
  - Higher → better recall, slower query
  - 100 → recall 0.95, latency 1ms
  - 200 → recall 0.98, latency 2ms
  - 500 → recall 0.995, latency 5ms

Distance metric: cosine (after L2 normalize, inner product = cosine)

Index size estimate:
  Raw vectors: 10M × 768 × 4 = 30 GB
  Graph (M=32, ~32 edges × 8 bytes per edge × 10M): ~5 GB
  Hierarchy + metadata: ~2 GB
  Total: ~37-50 GB depending on impl
```

### Step 4: Implementation (实现, 15-20 min)

```python
"""
HNSW-based ANN search for 10M × 768d vectors.
Uses hnswlib (C++ binding) for the core; numpy for I/O.
"""
import os
import time
import json
import logging
import numpy as np
from pathlib import Path
from typing import Optional

import hnswlib

log = logging.getLogger('ann')


class HNSWIndex:
    """
    HNSW ANN index for cosine similarity.
    - L2-normalizes input vectors before adding (so inner product == cosine).
    - Supports incremental add + delete (deletion is a tombstone, not free).
    - Persist + reload via index.save / load.
    """

    def __init__(
        self,
        dim: int = 768,
        max_elements: int = 10_000_000,
        m: int = 32,
        ef_construction: int = 200,
        ef_search: int = 200,
        space: str = 'ip',  # 'ip' for inner product (after normalize = cosine); 'cosine'; 'l2'
        n_threads: int = 0,  # 0 = auto = all cores
    ):
        self.dim = dim
        self.max_elements = max_elements
        self.m = m
        self.ef_construction = ef_construction
        self.ef_search = ef_search
        self.space = space
        # IDs we've added so we can map back to caller's ID space
        self.id_to_external: dict[int, str] = {}
        self.external_to_id: dict[str, int] = {}
        self.tombstones: set[int] = set()
        self._next_id = 0
        self.index = hnswlib.Index(space=space, dim=dim)
        self.index.init_index(
            max_elements=max_elements,
            ef_construction=ef_construction,
            M=m,
        )
        self.index.set_ef(ef_search)
        if n_threads > 0:
            self.index.set_num_threads(n_threads)

    @staticmethod
    def _normalize(vecs: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vecs / norms

    def add(self, vectors: np.ndarray, external_ids: list[str]):
        """Add vectors (will be L2-normalized) with given external IDs."""
        assert vectors.shape[1] == self.dim
        assert len(external_ids) == vectors.shape[0]
        # Normalize for cosine via inner-product space
        if self.space in ('ip', 'cosine'):
            vectors = self._normalize(vectors.astype(np.float32))
        internal_ids = np.empty(len(external_ids), dtype=np.int64)
        for i, eid in enumerate(external_ids):
            if eid in self.external_to_id:
                # Update: tombstone old, assign new id
                old_id = self.external_to_id[eid]
                self.tombstones.add(old_id)
            internal = self._next_id
            self._next_id += 1
            internal_ids[i] = internal
            self.id_to_external[internal] = eid
            self.external_to_id[eid] = internal
        self.index.add_items(vectors, internal_ids)

    def delete(self, external_id: str):
        if external_id not in self.external_to_id:
            return
        iid = self.external_to_id[external_id]
        self.tombstones.add(iid)
        # hnswlib has mark_deleted but it doesn't reclaim memory
        try:
            self.index.mark_deleted(iid)
        except RuntimeError:
            pass

    def search(self, query: np.ndarray, k: int = 10) -> list[tuple[str, float]]:
        """Return top-k as list of (external_id, distance_or_similarity)."""
        if self.space in ('ip', 'cosine'):
            q = self._normalize(query.reshape(1, -1).astype(np.float32))
        else:
            q = query.reshape(1, -1).astype(np.float32)
        # Over-fetch in case tombstones cull
        labels, distances = self.index.knn_query(q, k=k * 2)
        out = []
        for lid, d in zip(labels[0], distances[0]):
            if int(lid) in self.tombstones:
                continue
            eid = self.id_to_external.get(int(lid))
            if eid is None:
                continue
            out.append((eid, float(d)))
            if len(out) >= k:
                break
        return out

    def batch_search(self, queries: np.ndarray, k: int = 10) -> list[list[tuple[str, float]]]:
        """Batched search — uses internal multithreading."""
        if self.space in ('ip', 'cosine'):
            qs = self._normalize(queries.astype(np.float32))
        else:
            qs = queries.astype(np.float32)
        labels, distances = self.index.knn_query(qs, k=k * 2)
        results = []
        for row_labels, row_dists in zip(labels, distances):
            res = []
            for lid, d in zip(row_labels, row_dists):
                if int(lid) in self.tombstones:
                    continue
                eid = self.id_to_external.get(int(lid))
                if eid is None:
                    continue
                res.append((eid, float(d)))
                if len(res) >= k:
                    break
            results.append(res)
        return results

    def set_ef(self, ef: int):
        """Tune query-time recall/latency without rebuilding."""
        self.ef_search = ef
        self.index.set_ef(ef)

    def save(self, path: Path):
        path.mkdir(parents=True, exist_ok=True)
        self.index.save_index(str(path / 'hnsw.bin'))
        meta = {
            'dim': self.dim,
            'm': self.m,
            'ef_construction': self.ef_construction,
            'ef_search': self.ef_search,
            'space': self.space,
            'max_elements': self.max_elements,
            'id_to_external': self.id_to_external,
            'next_id': self._next_id,
            'tombstones': list(self.tombstones),
        }
        with open(path / 'meta.json', 'w') as f:
            json.dump(meta, f)

    @classmethod
    def load(cls, path: Path) -> 'HNSWIndex':
        with open(path / 'meta.json') as f:
            meta = json.load(f)
        inst = cls(
            dim=meta['dim'],
            max_elements=meta['max_elements'],
            m=meta['m'],
            ef_construction=meta['ef_construction'],
            ef_search=meta['ef_search'],
            space=meta['space'],
        )
        # NOTE: we re-init then load index data
        inst.index = hnswlib.Index(space=meta['space'], dim=meta['dim'])
        inst.index.load_index(str(path / 'hnsw.bin'), max_elements=meta['max_elements'])
        inst.index.set_ef(meta['ef_search'])
        inst.id_to_external = {int(k): v for k, v in meta['id_to_external'].items()}
        inst.external_to_id = {v: int(k) for k, v in meta['id_to_external'].items()}
        inst._next_id = meta['next_id']
        inst.tombstones = set(meta['tombstones'])
        return inst


# ============ Build script (one-time) ============

def build_index_from_npz(input_path: Path, output_dir: Path,
                          dim: int = 768) -> HNSWIndex:
    """
    input_path: .npz with arrays 'vectors' (N, dim) and 'ids' (N,) str.
    """
    data = np.load(input_path, allow_pickle=True)
    vectors = data['vectors']
    ids = list(data['ids'].tolist())
    assert vectors.shape[1] == dim

    log.info('Building HNSW index for %d vectors, dim=%d', vectors.shape[0], dim)
    idx = HNSWIndex(
        dim=dim,
        max_elements=int(vectors.shape[0] * 1.2),  # 20% growth headroom
        m=32, ef_construction=200, ef_search=200,
    )
    # Batch add — hnswlib uses internal threads
    batch = 100_000
    t0 = time.time()
    for i in range(0, vectors.shape[0], batch):
        idx.add(vectors[i:i+batch], ids[i:i+batch])
        if i % 1_000_000 == 0:
            log.info('  added %d in %.1fs', i + batch, time.time() - t0)
    log.info('Build done in %.1fs', time.time() - t0)
    idx.save(output_dir)
    return idx


# ============ Eval ============

def measure_recall_and_latency(
    idx: HNSWIndex,
    queries: np.ndarray,
    ground_truth: list[list[str]],  # ground-truth top-k external_ids per query
    k: int = 10,
    ef_values: Optional[list[int]] = None,
) -> list[dict]:
    """For each ef, compute mean recall@k and p99 latency."""
    ef_values = ef_values or [50, 100, 200, 500]
    rows = []
    for ef in ef_values:
        idx.set_ef(ef)
        latencies = []
        recalls = []
        for q, gt in zip(queries, ground_truth):
            t0 = time.perf_counter()
            results = idx.search(q, k=k)
            latencies.append((time.perf_counter() - t0) * 1000)
            retrieved = {r[0] for r in results}
            # recall = |retrieved ∩ ground_truth_topk| / k
            recalls.append(len(retrieved & set(gt[:k])) / k)
        rows.append({
            'ef': ef,
            'recall_mean': float(np.mean(recalls)),
            'latency_p50_ms': float(np.percentile(latencies, 50)),
            'latency_p99_ms': float(np.percentile(latencies, 99)),
            'throughput_qps': len(queries) / (sum(latencies) / 1000),
        })
    return rows


def compute_ground_truth_brute(vectors: np.ndarray, ids: list[str],
                                queries: np.ndarray, k: int = 10) -> list[list[str]]:
    """Slow brute-force for small eval set (typically queries ~ 100)."""
    # Normalize for cosine
    v = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    q = queries / np.linalg.norm(queries, axis=1, keepdims=True)
    sims = q @ v.T  # (Q, N)
    top_idx = np.argsort(-sims, axis=1)[:, :k]
    return [[ids[i] for i in row] for row in top_idx]
```

### Step 5: Tests (测试, 5 min)

```python
import unittest

class TestHNSWIndex(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(42)
        self.N = 5000
        self.dim = 64  # smaller for fast tests
        self.vecs = rng.standard_normal((self.N, self.dim)).astype(np.float32)
        self.ids = [f'v_{i}' for i in range(self.N)]
        self.idx = HNSWIndex(dim=self.dim, max_elements=self.N * 2,
                              m=16, ef_construction=100, ef_search=100)
        self.idx.add(self.vecs, self.ids)

    def test_self_search_returns_self(self):
        # Query with a vector that exists; should be top-1
        q = self.vecs[42]
        results = self.idx.search(q, k=5)
        self.assertEqual(results[0][0], 'v_42')

    def test_recall_against_brute(self):
        rng = np.random.default_rng(7)
        queries = rng.standard_normal((50, self.dim)).astype(np.float32)
        gt = compute_ground_truth_brute(self.vecs, self.ids, queries, k=10)
        recalls = []
        for q, g in zip(queries, gt):
            results = self.idx.search(q, k=10)
            ret = {r[0] for r in results}
            recalls.append(len(ret & set(g)) / 10)
        mean_recall = float(np.mean(recalls))
        self.assertGreater(mean_recall, 0.85)  # HNSW typically 0.9+

    def test_higher_ef_higher_recall(self):
        rng = np.random.default_rng(7)
        queries = rng.standard_normal((20, self.dim)).astype(np.float32)
        gt = compute_ground_truth_brute(self.vecs, self.ids, queries, k=10)
        def avg_recall(ef):
            self.idx.set_ef(ef)
            recalls = []
            for q, g in zip(queries, gt):
                r = self.idx.search(q, k=10)
                recalls.append(len(set(x[0] for x in r) & set(g)) / 10)
            return np.mean(recalls)
        r50 = avg_recall(50)
        r200 = avg_recall(200)
        self.assertGreaterEqual(r200, r50)

    def test_delete_excludes(self):
        before = self.idx.search(self.vecs[10], k=1)[0][0]
        self.assertEqual(before, 'v_10')
        self.idx.delete('v_10')
        after = self.idx.search(self.vecs[10], k=1)[0][0]
        self.assertNotEqual(after, 'v_10')

    def test_persist_and_reload(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            self.idx.save(d)
            loaded = HNSWIndex.load(d)
            results = loaded.search(self.vecs[100], k=1)
            self.assertEqual(results[0][0], 'v_100')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()
```

### Step 6: Production considerations (生产考虑, 5 min)

```
1. Sharding for >50M vectors:
   - Hash partition by external_id → N machines
   - Query: fan-out to all shards, top-k merge
   - Wins memory; loses some recall on boundary

2. GPU option:
   - FAISS GPU index (IndexIVFFlatGPU, IndexHNSWFlatGPU partial)
   - 10x throughput, similar latency
   - But: 30GB → A100 80GB (1 GPU), expensive

3. Update strategy:
   - HNSW: incremental insert OK; mark_deleted; periodic rebuild to reclaim
   - "Online" updates: write to delta index (small), merge to main index nightly

4. Memory ops:
   - mmap the index file: shared across processes, page-cache friendly
   - Pre-warm: read full index on boot → in RAM

5. Latency mitigations:
   - Batch queries (10 queries at once = ~5x throughput)
   - Cache popular query embeddings
   - "first-search" cold start warmup

6. Cost:
   - Single fat machine (256GB RAM): ~$1k/mo on cloud (m6i.32xlarge or similar)
   - vs Vertex AI Vector Search managed: ~$5k/mo for 10M × 768d
   - Self-host wins on cost; loses on ops effort

7. Filters at query time:
   - HNSW doesn't natively support; need 'post-filter' (top-100 → filter → top-10)
   - Or use Vertex AI Vector Search (HNSW + integrated metadata filter)
   - Or 'pre-cluster' by filter field → separate indices

8. Monitor:
   - recall (offline weekly sanity)
   - p50 / p99 latency
   - throughput (qps)
   - memory usage
   - tombstone count → trigger rebuild at 10%
```

---

## 完整代码 (Production-ready)

Self-contained — 已在 Step 4. Install + use:

```bash
pip install hnswlib numpy

# Build (one-time):
python -c "
from ann import build_index_from_npz
from pathlib import Path
build_index_from_npz(Path('vectors.npz'), Path('./index'))
"

# Query:
python -c "
from ann import HNSWIndex
from pathlib import Path
import numpy as np
idx = HNSWIndex.load(Path('./index'))
q = np.random.randn(768).astype(np.float32)
print(idx.search(q, k=10))
"
```

---

## 复杂度分析

| 操作 | Time | Space |
|------|------|-------|
| Brute force search | O(N × d) = 30 GB read = 770ms CPU | 30 GB |
| HNSW build | O(N × M × log N × d) — ~2hr | 50 GB |
| HNSW search | O(M × ef × log N × d) — 1-5ms | — |
| IVF-PQ build | O(N × d + Kmeans) — ~1hr | 1-3 GB |
| IVF-PQ search | O(nprobe × N/K × d_compressed) — 5ms | — |
| LSH build | O(N × T × d) — ~30min | 60 GB |
| LSH search | O(T × bucket_size × d) — 20ms | — |

**Sample numbers for 10M × 768d, HNSW M=32, ef=200**:
- Build: ~2 hours on 16-core CPU
- Memory: ~50 GB
- Query latency: 1-2ms p50, 3-5ms p99
- Recall@10: ~0.98
- Throughput: ~1000 QPS on 16-core

---

## Gao Xin 简历专属 reframe

- **BNPL chatbot (RAG)**: ~500k vectors 768d, 用 Chroma 自带 HNSW. 当时 thinking 简单调用现成. 这道题考的是 SAME pipeline 但 10M scale, 必须自己写.
- **Voice agent**: similarity search for FAQ 检索 ~50k 条, 用 in-mem FAISS Flat — 因为太小没必要 HNSW. 但同样需要 normalize cosine + reranker.
- **Internal Agent Platform**: tool selection 用 embedding similarity from manifest 描述 ~10k tool, FAISS Flat 也够.
- **ConvFinQA**: 9-variant ablation 里 retrieval variant 用过 BM25 vs HNSW vs hybrid — 我熟悉 hnswlib API.
- **TikTok PayLater**: 不直接相关, 但 fraud team 用 embeddings 找 similar user (5M+ user vectors), 我做过 reviewer, 知道他们用 FAISS IVF-PQ 因为 memory budget.

**面试一句话**: "I've used hnswlib in production at TikTok for RAG (500k scale) and reviewed our fraud team's setup at 5M scale with IVF-PQ for memory constraints. At 10M I'd default HNSW unless RAM is tight, then IVF-PQ."

---

## 5 个 Follow-ups

**Q1**: "如果 vectors 涨到 1B 怎么办?"

A: 单机 1B × 768 × 4 = 3 TB raw — 不可能 in-mem. 选项:
1. **Shard HNSW across N machines**: 30 个机器, 每个 30M vectors. Fan-out + merge. 每个 shard 50GB RAM.
2. **IVF-PQ on 1 GPU**: 1B × 64 bytes = 64GB, A100 80GB 装得下. Recall ~85%.
3. **DiskANN** (Microsoft): SSD-based HNSW, 1ms p99 from disk, 96% recall, OOM-proof. 1B 在单机.
4. **GraphANN / SPANN**: hybrid memory + disk.
5. **Cloud spilled**: hot 10% in-mem, cold 90% on disk + cache.

**Q2**: "如果向量 dim 改成 4096 (e.g., GPT embedding 大模型)?"

A: 内存 30GB → 160GB. HNSW 不行了 (graph + raw)/. 选项:
1. **MRL / Matryoshka embeddings**: 截断到 768d, recall 只丢 2-3%
2. **PQ 压缩** 到 256 codes × 1byte = 256 bytes/vec → 2.5GB
3. **Binary embeddings**: 1 bit per dim — 4096 bits = 512 bytes/vec → 5GB. Recall 还行 ~80%.
4. **Distillation to smaller embedder**

**Q3**: "Index 怎么 update? 客户每天加 5000 个新 vector."

A: HNSW 支持 incremental insert. Strategy:
1. **In-place insert**: `idx.add()` 直接加. 多个 connection 不要并发 (lib 不 thread-safe write).
2. **Append-only journal**: 新 vector 写一个 delta index (小), 主 index nightly merge.
3. **Mark-deleted for updates**: 旧 ID tombstone, 新 ID 加. tombstone 比例 > 10% 触发 rebuild.

我做过的: 用 active/passive index swap — build 新 index 完成后 atomic 切换, 老 index drain.

**Q4**: "Recall 不够你怎么办?"

A: 几个 lever:
1. **Increase ef_search** at query time (no rebuild) — recall up, latency up
2. **Re-rank with cross-encoder** on top-100 → top-10 — precision up dramatically
3. **Hybrid**: BM25 union HNSW, ranking fusion
4. **Bigger M** (rebuild required)
5. **Better embedder**: e.g., bge-large 比 bge-base recall@10 +3-5%
6. **Query expansion / HyDE** (Q17)

**Q5**: "怎么 measure recall in production (没 ground truth)?"

A: 几个 proxy:
1. **Offline weekly**: 抽 1000 query, run brute force ground truth, 比 HNSW result, 报 recall@10
2. **Surrogate**: top-1 score 的分布 — drift 即 alarm
3. **Click-through / Implicit feedback**: 用户点了 top-1 vs 没点 — proxy quality signal
4. **A/B**: 切两个 ef (200 vs 500) 各 50% 流量, 看用户 KPI 差别
5. **Synthetic**: 已知相似 pair (e.g., title vs body) 看 retrieval 能否找回 known pair

---

## 死路答法

1. **`for v in vectors: dot(q, v)`** — brute force 770ms 超 budget
2. **`np.argsort(q @ V.T)[:k]`** — same brute force, 同样慢
3. **`sklearn.NearestNeighbors`** — 没 HNSW, 限于小数据集
4. **没考虑 normalize** — cosine 跟 inner product 不等价时 score 不对
5. **没 incremental insert plan** — 客户加新 vector 你说 "重 build" 失分
6. **过度复杂**: 上来就讲 ScaNN + DiskANN — 不知道 HNSW 是 baseline
7. **dont' size first** — 没算 30GB 内存就说"用 HNSW", 面试官不知你懂不懂
8. **memory 不算** — 50GB 不在 8GB RAM 机子上跑
9. **`ef_construction == ef_search`** — 这两个独立, 前者 build-time, 后者 query-time
10. **没 recall eval** — defend 不出 ANN 选择

---

## 加分项

**Production discussion 加分**:

- **Memory-mapped index**: `mmap` HNSW binary, multi-process share, OS page cache friendly. Recovery from crash fast (no reload).
- **Cold start**: 启动后 prefetch / warm-up by running a few synthetic queries to bring pages into RAM
- **Health check**: `/healthz` runs known-answer query, expect specific top-1 — verifies index loaded and not corrupted
- **Schema versioning**: index 的 embedder model version 写在 metadata; serving 时 check 客户端 expectation 一致
- **Backup**: index 文件 nightly to GCS
- **Crash recovery**: 重启从 backup GCS download (5min for 50GB), or from raw vectors rebuild (2hr)
- **Replication**: 2 instances on separate AZ, LB
- **Capacity planning**: monitor `len(tombstones) / N`, alert > 5%; monitor `ef_search` distribution
- **Filter strategy**: post-filter top-100 after retrieval (sufficient for sparse filter); pre-shard by category for dense filter
- **Hybrid search**: BM25 + vector union with RRF (reciprocal rank fusion)
- **Reranker hook**: separate process for cross-encoder rerank (different latency budget)
- **Cost monitor**: $$ per query, $$ per QPS, $$ per million docs indexed — show CFO

---

## 一句话总结

> **10M × 768d 单机 → HNSW (hnswlib) M=32 ef_construction=200 ef_search=200. ~50GB RAM, 2hr build, 2ms p50 query, 0.98 recall@10. IVF-PQ if RAM tight (sacrifice recall); shard if N > 50M; GPU IVF if 1B+.**

---

## Cheat Sheet

```python
# 现场算 brute force:
#   10M × 768 × 4B = 30GB
#   10M × 768 mul-add per q = 7.6 GFLOP
#   CPU AVX2 ~10 GFLOPS → 770ms per query → too slow

# Algorithm pick: HNSW
#   Recall@10 = 0.98, latency 2-5ms, memory 50GB
#   Fits single fat machine (64GB RAM)
#   Supports incremental insert
#   Library: hnswlib (C++ + Python binding)

# Parameters:
#   M = 32                  (graph edges per node)
#   ef_construction = 200   (build quality)
#   ef_search = 200         (query quality — tunable at query time!)
#   space = 'ip'            (inner product; normalize first for cosine)

# Eval:
#   recall@10 vs brute force ground truth on 100 query sample
#   latency p50 / p99 from prod traces
#   throughput QPS under batch

# Update strategy:
#   incremental add() OK (HNSW)
#   delete via mark_deleted (tombstone)
#   periodic rebuild when tombstones > 10%

# Production:
#   mmap index file
#   pre-warm on startup
#   batch queries (5x throughput)
#   filter: post-filter top-100 → top-10
#   shard if >50M
#   GPU if you have it

# Alternatives:
#   IVF-PQ:  recall 0.87, memory 1-3GB, latency 5ms      → use if RAM tight
#   IVF:     recall 0.93, memory 30GB, latency 10ms      → middle ground
#   LSH:     recall 0.75, memory 60GB, latency 20ms      → outdated
#   ScaNN:   recall 0.97, faster but harder ops
#   DiskANN: recall 0.96, on disk, 1B+ scale

# Don't:
#   - brute force at 10M scale
#   - forget normalize for cosine
#   - bottom-up: explain numbers first
#   - over-claim incremental on IVF (needs rebuild centroids)
#   - hardcode ef_search (it's per-query tunable!)
```
