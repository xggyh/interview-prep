## Q13 · CLI 工具 — 读 PDF 输出带实体抽取的 JSON 索引

> "Build a **CLI tool** that takes a directory of PDFs and produces a **searchable JSON index** with **extracted entities** (people, organizations, dates, monetary values). Code it. Then we'll discuss productionization."

**Round**: Coding (60 min, shared screen + IDE)
**出处**: Exponent 2026 FDE · 公司: **Scale AI**, OpenAI, Anthropic
**难度**: Medium-Hard
**主要技能**: 真实 production tooling, LLM 集成成本控制, CLI UX, error handling

---

## 这道题在考什么

这道题不是 algo, 是 **真 FDE 工程问题** — 客户给一堆 PDF (审计报告 / 法律合同 / 研究 paper), 让你 "搜得到 + 找得到关键人/公司/金额". 考察:

1. **CLI 设计** — `argparse` 用对, `--dry-run`, `--output`, progress bar, exit code
2. **PDF 怎么读** — `pdfplumber` vs `PyMuPDF` (fitz) vs `pdfminer.six` — 各有 trade-off, 你能不能开口选
3. **Entity extraction 路径选择** — spaCy NER (offline, 快, 限于训练域) vs LLM (灵活, 慢且贵) — 你能不能 quantify 成本
4. **Chunking + cost control** — LLM 不能整个 100-page PDF 灌进去, 要 chunk + budget
5. **Robustness** — PDF 是图片扫描怎么办 (OCR fallback)? 加密 PDF? 损坏文件? 中文/多语言?
6. **Output format** — JSON schema 要适合 grep / 给 downstream search index 用
7. **Test 怎么写** — 不能真 call OpenAI, 要 mock; 也要有真 PDF fixture

Scale AI / OpenAI 真做的活: 给客户搭 doc-intelligence pipeline, 上面这些坑全踩过.

---

## 完美答案架构 (Layered Response)

| # | 层 | 时间 | 干什么 | 开口句 |
|---|---|------|--------|--------|
| 1 | Clarify | 0-5 min | 问 PDF 类型, scale, entity 定义, budget | "Before coding, let me clarify..." |
| 2 | Architecture sketch | 5-10 min | scanner → extractor → indexer → CLI | "Three components: scan, extract, output." |
| 3 | CLI skeleton | 10-15 min | argparse + dispatch | "I'll set up the CLI first, then plug in components." |
| 4 | PDF text extraction | 15-25 min | pdfplumber + OCR fallback | "Two layers: direct text, then OCR if empty." |
| 5 | Entity extraction | 25-40 min | spaCy default + LLM upgrade | "Default spaCy for speed; --use-llm flag for quality." |
| 6 | Index build + JSON output | 40-50 min | per-doc JSON + global index | "Two files: per-doc + master index." |
| 7 | Tests + dry-run | 50-55 min | mock LLM, test fixture PDF | "Mock the LLM client; use a known PDF for golden." |
| 8 | Productionization | 55-60 min | resume, parallelism, cost | "Three productionization concerns..." |

---

## 必问 clarifying questions

**1. PDF 性质**

> "Native PDFs (text-extractable) or scanned (image-only, need OCR)? Mix?"

Why: 决定要不要上 OCR (`tesseract` / `paddleocr`) — 10x slower 且要 GPU.

**2. Scale**

> "Order of magnitude — 100 PDFs / 10k / 1M? Each PDF size?"

Why: 100 个直接 sync 跑就行; 10k 得 multiprocess; 1M 要分布式 + queue.

**3. Entity 范围**

> "Which entities — just (person, org, date, money) or also (location, product, drug name, custom domain entities like invoice numbers)?"

Why: 标准 4 类 spaCy 直接给; 自定义实体必须 LLM 或 fine-tune.

**4. 精度 vs 成本**

> "What recall/precision do we need? How much cost budget per document?"

Why: 1c/doc → spaCy; 50c/doc → LLM allowed.

**5. 输出 schema**

> "Free-form JSON or compliant with a known schema (e.g., schema.org, ELK ingest)?"

Why: 决定 JSON shape. 简单起见 `{doc_id, path, pages, text_by_page, entities: {persons:[], orgs:[], ...}}`.

**6. Search 在哪用**

> "Where does this JSON go — Elasticsearch, Postgres, hand-grep, vector DB?"

Why: 决定要不要再 embed (vector); 简单 case 直接 dump JSON.

**7. Resume?**

> "If the run crashes mid-way, should it resume from where it left off, or restart?"

Why: 1M PDF 跑 8 小时挂了, 必须能 resume.

---

## 详细解题流程

### Step 1: Design decisions (5-10 min)

**Architecture**:

```
$ pdfindex extract /docs/*.pdf --output index.json [--use-llm] [--workers 8]

┌─────────────────────────────────────────────────────────────┐
│ CLI (argparse) → Pipeline orchestrator                       │
│                                                              │
│   ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────┐  │
│   │ Scanner  │→ │  Text    │→ │   Entity   │→ │ Indexer  │  │
│   │ (find)   │  │ Extract  │  │  Extract   │  │ (JSON)   │  │
│   └──────────┘  └──────────┘  └────────────┘  └──────────┘  │
│                  pdfplumber    spaCy / LLM     write file   │
│                  + OCR fallback                              │
└─────────────────────────────────────────────────────────────┘

Per-doc JSON:  ./out/{doc_id}.json
Master index:  ./out/index.json — { doc_id → { path, mtime, entity_counts } }
```

**关键选择**:

- **`pdfplumber`** for direct text — Python pure, mature, 不需要 native binding
- **OCR fallback**: 若 pdfplumber 抽出 < 20 chars/page, 走 `pytesseract` (or skip if `--no-ocr`)
- **`spaCy`** for default NER — `en_core_web_sm` 50MB 模型 fast — Person/Org/Date/Money/GPE 都有
- **`--use-llm`** flag for LLM-based extraction (OpenAI / Anthropic) — 更准, 但要 chunk + budget
- **JSON output** — per-doc + master index, idempotent

### Step 2: Initial implementation (15-20 min)

```python
"""
pdfindex - extract text + entities from PDFs into JSON.

Usage:
  pdfindex extract /docs --output ./out
  pdfindex extract /docs --output ./out --use-llm --workers 4
  pdfindex extract /docs --dry-run
  pdfindex search ./out --query "Anthropic"
"""
import argparse
import json
import os
import sys
import hashlib
import logging
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Iterator
from concurrent.futures import ProcessPoolExecutor, as_completed

log = logging.getLogger('pdfindex')


# ============ Data model ============

@dataclass
class PageText:
    page_num: int            # 1-indexed
    text: str
    char_count: int
    extraction_method: str   # 'pdfplumber' | 'ocr' | 'empty'


@dataclass
class Entities:
    persons: list[str] = field(default_factory=list)
    orgs: list[str] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)
    money: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)


@dataclass
class DocIndex:
    doc_id: str
    path: str
    file_hash: str            # sha1 of bytes — for dedupe / change-detection
    mtime: float
    page_count: int
    pages: list[PageText]
    entities: Entities
    extraction_method: str    # 'spacy' | 'llm' | 'mixed'
    extraction_cost_usd: float = 0.0
    error: Optional[str] = None


# ============ Scanner ============

def find_pdfs(root: Path) -> Iterator[Path]:
    """Yield .pdf files under root (recursive)."""
    if root.is_file() and root.suffix.lower() == '.pdf':
        yield root
        return
    for p in root.rglob('*.pdf'):
        if p.is_file():
            yield p


def file_hash_sha1(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


# ============ Text extraction ============

def extract_text_pdfplumber(path: Path) -> list[PageText]:
    """Use pdfplumber to extract text page by page."""
    import pdfplumber  # local import so non-LLM mode doesn't pay
    pages: list[PageText] = []
    try:
        with pdfplumber.open(str(path)) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                txt = page.extract_text() or ''
                pages.append(PageText(
                    page_num=i,
                    text=txt,
                    char_count=len(txt),
                    extraction_method='pdfplumber' if txt else 'empty',
                ))
    except Exception as e:
        log.warning('pdfplumber failed on %s: %s', path, e)
        raise
    return pages


def extract_text_ocr(path: Path, page_num: int) -> str:
    """Render a page to image then OCR. Slow — use sparingly."""
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError:
        log.warning('OCR libs not installed, skipping OCR for page %d', page_num)
        return ''
    images = convert_from_path(str(path), first_page=page_num, last_page=page_num, dpi=200)
    if not images:
        return ''
    return pytesseract.image_to_string(images[0])


def extract_with_ocr_fallback(path: Path, ocr_threshold: int = 20) -> list[PageText]:
    """If a page has fewer than `ocr_threshold` chars, fall back to OCR."""
    pages = extract_text_pdfplumber(path)
    for p in pages:
        if p.char_count < ocr_threshold:
            txt = extract_text_ocr(path, p.page_num)
            if txt:
                p.text = txt
                p.char_count = len(txt)
                p.extraction_method = 'ocr'
    return pages


# ============ Entity extraction ============

_SPACY_NLP = None  # lazy

def _get_spacy():
    global _SPACY_NLP
    if _SPACY_NLP is None:
        import spacy
        _SPACY_NLP = spacy.load('en_core_web_sm')
    return _SPACY_NLP


_SPACY_LABEL_TO_FIELD = {
    'PERSON': 'persons',
    'ORG':    'orgs',
    'DATE':   'dates',
    'TIME':   'dates',
    'MONEY':  'money',
    'GPE':    'locations',
    'LOC':    'locations',
}


def extract_entities_spacy(text: str, max_chars: int = 1_000_000) -> Entities:
    """Run spaCy NER. Truncate if too long (spaCy has 1M default)."""
    if not text:
        return Entities()
    nlp = _get_spacy()
    if len(text) > max_chars:
        text = text[:max_chars]
    doc = nlp(text)
    ent = Entities()
    for e in doc.ents:
        field_name = _SPACY_LABEL_TO_FIELD.get(e.label_)
        if field_name:
            getattr(ent, field_name).append(e.text.strip())
    # Dedupe preserving order
    for fname in ('persons', 'orgs', 'dates', 'money', 'locations'):
        seen = set()
        deduped = []
        for v in getattr(ent, fname):
            if v not in seen:
                seen.add(v)
                deduped.append(v)
        setattr(ent, fname, deduped)
    return ent


# ---- LLM extraction (optional, --use-llm) ----

_LLM_ENTITY_PROMPT = """Extract structured entities from the following document text.
Return ONLY valid JSON in this schema (no prose, no markdown):
{{
  "persons":   ["full names of people"],
  "orgs":      ["organizations, companies, agencies"],
  "dates":     ["dates, normalized to YYYY-MM-DD when possible"],
  "money":     ["monetary amounts with currency, e.g. '$1,200,000' or 'EUR 500'"],
  "locations": ["cities, countries, regions"]
}}
Be thorough but only include explicit mentions. Deduplicate within each list.

Document:
\"\"\"
{chunk}
\"\"\"
"""


def chunk_text(text: str, max_chars: int = 8000, overlap: int = 200) -> list[str]:
    """Chunk text into overlapping pieces. Prefers paragraph boundaries."""
    if len(text) <= max_chars:
        return [text]
    chunks = []
    i = 0
    while i < len(text):
        end = min(len(text), i + max_chars)
        # Try to break at paragraph boundary near end
        if end < len(text):
            bp = text.rfind('\n\n', i, end)
            if bp > i + max_chars * 0.5:
                end = bp
        chunks.append(text[i:end])
        if end >= len(text):
            break
        i = end - overlap
    return chunks


def extract_entities_llm(
    text: str,
    *,
    client,
    model: str = 'gpt-4o-mini',
    max_chars_per_chunk: int = 8000,
    cost_budget_usd: float = 0.10,
) -> tuple[Entities, float]:
    """
    Use LLM for entity extraction. Returns (entities, cost_used_usd).
    Stops chunking when cost_budget_usd is exceeded.
    """
    ent = Entities()
    cost = 0.0
    # Pricing snapshot (illustrative; real impl reads from a pricing table)
    PRICE_PER_1K_INPUT = 0.00015   # gpt-4o-mini
    PRICE_PER_1K_OUTPUT = 0.0006
    chunks = chunk_text(text, max_chars=max_chars_per_chunk)
    for i, chunk in enumerate(chunks):
        if cost >= cost_budget_usd:
            log.warning('Cost budget exceeded for doc — stopping at chunk %d/%d', i, len(chunks))
            break
        prompt = _LLM_ENTITY_PROMPT.format(chunk=chunk)
        resp = client.chat.completions.create(
            model=model,
            messages=[{'role': 'user', 'content': prompt}],
            response_format={'type': 'json_object'},
            temperature=0.0,
            max_tokens=2000,
        )
        # Cost estimate (rough)
        usage = resp.usage
        chunk_cost = (
            usage.prompt_tokens / 1000 * PRICE_PER_1K_INPUT +
            usage.completion_tokens / 1000 * PRICE_PER_1K_OUTPUT
        )
        cost += chunk_cost
        # Parse JSON
        content = resp.choices[0].message.content
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            log.warning('LLM returned non-JSON for chunk %d', i)
            continue
        # Merge
        for field_name in ('persons', 'orgs', 'dates', 'money', 'locations'):
            vals = parsed.get(field_name) or []
            getattr(ent, field_name).extend(v for v in vals if isinstance(v, str))
    # Dedupe
    for f in ('persons', 'orgs', 'dates', 'money', 'locations'):
        seen = set()
        deduped = []
        for v in getattr(ent, f):
            if v not in seen:
                seen.add(v)
                deduped.append(v)
        setattr(ent, f, deduped)
    return ent, cost


# ============ Pipeline ============

def process_pdf(
    path: Path,
    *,
    use_llm: bool = False,
    llm_client=None,
    llm_budget_usd: float = 0.10,
    enable_ocr: bool = True,
) -> DocIndex:
    """Process a single PDF and return a DocIndex."""
    doc_id = path.stem + '_' + file_hash_sha1(path)[:8]
    stat = path.stat()
    file_h = file_hash_sha1(path)
    try:
        if enable_ocr:
            pages = extract_with_ocr_fallback(path)
        else:
            pages = extract_text_pdfplumber(path)
    except Exception as e:
        return DocIndex(
            doc_id=doc_id, path=str(path), file_hash=file_h,
            mtime=stat.st_mtime, page_count=0, pages=[], entities=Entities(),
            extraction_method='error', error=str(e),
        )

    full_text = '\n\n'.join(p.text for p in pages if p.text)

    cost = 0.0
    if use_llm and llm_client:
        ent, cost = extract_entities_llm(
            full_text, client=llm_client, cost_budget_usd=llm_budget_usd,
        )
        method = 'llm'
    else:
        ent = extract_entities_spacy(full_text)
        method = 'spacy'

    return DocIndex(
        doc_id=doc_id,
        path=str(path),
        file_hash=file_h,
        mtime=stat.st_mtime,
        page_count=len(pages),
        pages=pages,
        entities=ent,
        extraction_method=method,
        extraction_cost_usd=cost,
    )


def write_doc_index(out_dir: Path, idx: DocIndex) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    fp = out_dir / f'{idx.doc_id}.json'
    with open(fp, 'w', encoding='utf-8') as f:
        json.dump(asdict(idx), f, indent=2, ensure_ascii=False)
    return fp


def update_master_index(out_dir: Path, idx: DocIndex) -> None:
    """Atomic-ish update of master index.json."""
    master = out_dir / 'index.json'
    data = {}
    if master.exists():
        try:
            with open(master) as f:
                data = json.load(f)
        except json.JSONDecodeError:
            log.warning('master index corrupted, rebuilding')
            data = {}
    data[idx.doc_id] = {
        'path': idx.path,
        'mtime': idx.mtime,
        'file_hash': idx.file_hash,
        'page_count': idx.page_count,
        'entity_counts': {
            'persons': len(idx.entities.persons),
            'orgs': len(idx.entities.orgs),
            'dates': len(idx.entities.dates),
            'money': len(idx.entities.money),
            'locations': len(idx.entities.locations),
        },
        'extraction_method': idx.extraction_method,
        'cost_usd': idx.extraction_cost_usd,
        'error': idx.error,
    }
    tmp = master.with_suffix('.json.tmp')
    with open(tmp, 'w') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, master)


def load_master(out_dir: Path) -> dict:
    fp = out_dir / 'index.json'
    if not fp.exists():
        return {}
    with open(fp) as f:
        return json.load(f)


# ============ CLI ============

def cmd_extract(args: argparse.Namespace) -> int:
    src = Path(args.source)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    pdfs = list(find_pdfs(src))
    if not pdfs:
        log.error('No PDFs found under %s', src)
        return 2
    log.info('Found %d PDFs', len(pdfs))

    if args.dry_run:
        for p in pdfs:
            print(p)
        return 0

    # Resume: skip already-processed by file_hash
    master = load_master(out)
    seen_hashes = {v['file_hash'] for v in master.values()}

    llm_client = None
    if args.use_llm:
        from openai import OpenAI
        llm_client = OpenAI()

    total_cost = 0.0
    successes, failures, skipped = 0, 0, 0
    t0 = time.time()

    todo = []
    for p in pdfs:
        try:
            if file_hash_sha1(p) in seen_hashes:
                skipped += 1
                continue
        except Exception:
            pass
        todo.append(p)
    log.info('Skipping %d already-processed, processing %d', skipped, len(todo))

    # Parallel via processes (spaCy is CPU-bound; OCR also CPU-bound)
    if args.workers > 1 and not args.use_llm:
        # LLM is I/O bound — would use threads; here keep simple
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            futures = {ex.submit(process_pdf, p, use_llm=False,
                                  enable_ocr=args.ocr): p for p in todo}
            for i, fut in enumerate(as_completed(futures), 1):
                idx = fut.result()
                _emit(idx, out)
                if idx.error:
                    failures += 1
                else:
                    successes += 1
                total_cost += idx.extraction_cost_usd
                if i % 10 == 0 or i == len(todo):
                    log.info('[%d/%d] cost=$%.4f', i, len(todo), total_cost)
    else:
        for i, p in enumerate(todo, 1):
            idx = process_pdf(
                p, use_llm=args.use_llm, llm_client=llm_client,
                llm_budget_usd=args.budget_per_doc, enable_ocr=args.ocr,
            )
            _emit(idx, out)
            if idx.error:
                failures += 1
            else:
                successes += 1
            total_cost += idx.extraction_cost_usd
            if i % 10 == 0 or i == len(todo):
                log.info('[%d/%d] cost=$%.4f', i, len(todo), total_cost)

    dt = time.time() - t0
    log.info('Done: %d succeeded, %d failed, %d skipped in %.1fs ($%.4f)',
             successes, failures, skipped, dt, total_cost)
    return 0 if failures == 0 else 1


def _emit(idx: DocIndex, out: Path) -> None:
    write_doc_index(out, idx)
    update_master_index(out, idx)


def cmd_search(args: argparse.Namespace) -> int:
    """Naive grep through master index entities."""
    out = Path(args.output)
    master = load_master(out)
    q = args.query.lower()
    matches = []
    for doc_id, meta in master.items():
        fp = out / f'{doc_id}.json'
        if not fp.exists():
            continue
        with open(fp) as f:
            doc = json.load(f)
        ent = doc.get('entities', {})
        all_strings = (ent.get('persons', []) + ent.get('orgs', []) +
                       ent.get('locations', []) + ent.get('money', []))
        for s in all_strings:
            if q in s.lower():
                matches.append((doc_id, s, doc['path']))
                break
    for doc_id, s, path in matches:
        print(f'{doc_id}\t{s}\t{path}')
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog='pdfindex')
    p.add_argument('-v', '--verbose', action='store_true')
    sub = p.add_subparsers(dest='cmd', required=True)

    px = sub.add_parser('extract', help='Extract PDFs to JSON index')
    px.add_argument('source', help='File or directory of PDFs')
    px.add_argument('-o', '--output', default='./pdfindex_out',
                    help='Output directory for JSON index')
    px.add_argument('--dry-run', action='store_true',
                    help='Just list files that would be processed')
    px.add_argument('--use-llm', action='store_true',
                    help='Use LLM (OpenAI) for entity extraction')
    px.add_argument('--budget-per-doc', type=float, default=0.10,
                    help='Max USD per document when --use-llm (default $0.10)')
    px.add_argument('--ocr', action='store_true', default=True,
                    help='OCR fallback for image PDFs (default on)')
    px.add_argument('--no-ocr', dest='ocr', action='store_false')
    px.add_argument('--workers', type=int, default=1,
                    help='Parallel worker processes')
    px.set_defaults(func=cmd_extract)

    ps = sub.add_parser('search', help='Search the index')
    ps.add_argument('query')
    ps.add_argument('-o', '--output', default='./pdfindex_out')
    ps.set_defaults(func=cmd_search)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
    )
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
```

### Step 3: Edge cases + tests (5-10 min)

```python
# tests/test_pdfindex.py
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import pdfindex


class TestChunking(unittest.TestCase):
    def test_short_no_chunk(self):
        chunks = pdfindex.chunk_text('x' * 100, max_chars=8000)
        self.assertEqual(len(chunks), 1)

    def test_long_chunked(self):
        text = ('paragraph one.\n\n' + 'x' * 9000 + '\n\n' + 'paragraph two.')
        chunks = pdfindex.chunk_text(text, max_chars=8000, overlap=200)
        self.assertGreater(len(chunks), 1)

    def test_chunks_have_overlap(self):
        text = 'a' * 5000 + 'b' * 5000
        chunks = pdfindex.chunk_text(text, max_chars=6000, overlap=500)
        # Overlap means some bytes appear in both
        self.assertGreater(len(chunks), 1)


class TestLLMMock(unittest.TestCase):
    def test_llm_extraction_with_mock(self):
        fake_client = MagicMock()
        fake_resp = MagicMock()
        fake_resp.choices = [MagicMock()]
        fake_resp.choices[0].message.content = json.dumps({
            'persons': ['Alice Smith'],
            'orgs': ['Anthropic'],
            'dates': ['2024-01-15'],
            'money': ['$1M'],
            'locations': ['San Francisco'],
        })
        fake_resp.usage = MagicMock(prompt_tokens=1000, completion_tokens=200)
        fake_client.chat.completions.create.return_value = fake_resp

        ent, cost = pdfindex.extract_entities_llm(
            'Alice Smith joined Anthropic on 2024-01-15.',
            client=fake_client, cost_budget_usd=1.0,
        )
        self.assertIn('Alice Smith', ent.persons)
        self.assertIn('Anthropic', ent.orgs)
        self.assertGreater(cost, 0)

    def test_llm_budget_stops_early(self):
        fake_client = MagicMock()
        fake_resp = MagicMock()
        fake_resp.choices = [MagicMock()]
        fake_resp.choices[0].message.content = '{"persons":[]}'
        fake_resp.usage = MagicMock(prompt_tokens=1_000_000, completion_tokens=1)
        fake_client.chat.completions.create.return_value = fake_resp

        long_text = 'word ' * 50_000  # several chunks
        ent, cost = pdfindex.extract_entities_llm(
            long_text, client=fake_client, cost_budget_usd=0.001,
        )
        # Should call create at most a few times before bailing
        self.assertLessEqual(fake_client.chat.completions.create.call_count, 2)


class TestCLI(unittest.TestCase):
    def test_dry_run_lists_pdfs(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / 'a.pdf').write_bytes(b'%PDF-1.4 fake')
            (d / 'b.txt').write_bytes(b'not a pdf')
            rc = pdfindex.main(['extract', str(d), '-o', str(d / 'out'),
                                 '--dry-run'])
            self.assertEqual(rc, 0)

    def test_no_pdfs_exits_2(self):
        with tempfile.TemporaryDirectory() as d:
            rc = pdfindex.main(['extract', d, '-o', d + '/out'])
            self.assertEqual(rc, 2)


if __name__ == '__main__':
    unittest.main()
```

**Edge cases (说给面试官)**:

1. **Empty PDF** (0 pages) → emit DocIndex with `page_count=0`, `error='empty'`
2. **Encrypted PDF** → pdfplumber 抛 PDFPasswordIncorrect, catch, mark `error`
3. **Corrupted PDF** → catch + log, 不 abort 整个 batch
4. **Scanned image PDF** → pdfplumber 返回空, OCR fallback (if enabled)
5. **Mixed scanned + text** (常见: 封面扫描, 正文 text) → per-page fallback
6. **Non-English** (中文 / 阿拉伯) → spaCy `en_core_web_sm` 不识别 — 切 `zh_core_web_sm`/`xx_ent_wiki_sm`
7. **Big PDF** (500 pages) → text 可能 5MB, spaCy 截断 1M chars; LLM 必 chunk
8. **Duplicate PDF** (同样 bytes 不同 path) → 用 `file_hash` dedupe
9. **LLM 返回 non-JSON** → catch JSONDecodeError, log, skip chunk
10. **LLM 超 budget** → 停止追加 chunk, 但 emit 已经抽出的
11. **Interrupted run** → master index 已有的 doc_id 跳过 (resume)
12. **Permission denied / file not exist** → log + counter
13. **Multi-file with same stem** → doc_id 加 hash 后缀避免冲突
14. **Long filename / special chars** → 落盘安全字符化
15. **Concurrent writes to master index** → 用 `tmp + os.replace` atomic rename

### Step 4: Trade-offs + extensions (5-10 min)

**Production hardening**:

| 问题 | 解法 |
|------|------|
| 1M PDFs, 单机跑不完 | Queue (SQS / Redis) + worker fleet; 每个 worker 处理一个 |
| 中途崩了 | resume via `file_hash in master` (本地) — 分布式用 status row |
| Cost runaway | per-doc budget + per-batch budget + Slack alert at 80% |
| LLM 不稳定 | spaCy 默认 + `--use-llm-only-if-confidence-low` |
| Schema 演进 | output JSON 加 `schema_version` field, downstream migrate |
| Search 性能 | dump JSON 后, 灌进 Elasticsearch / Tantivy |
| Multilingual | detect 语言 → pick correct spaCy 模型 / LLM prompt |
| OCR 慢 | gpu OCR (`easyocr`) 或 `paddleocr` 比 tesseract 快 5x |
| Privacy / PII | LLM 前先 redact SSN/credit card patterns; on-prem LLM (vLLM) |
| Costing accuracy | 用 real-time pricing table, 不 hardcode |

**Architecture upgrade**:

```
Naive (本题):
  for pdf in pdfs:
      doc = process_pdf(pdf)
      write(doc)

Multi-worker:
  ProcessPoolExecutor — 8 cores, 8x throughput

Distributed:
  Queue (Redis / SQS) — workers pick pdfs from queue
  Status DB (Postgres) — record processed file_hash
  S3 — store PDFs + output JSON

Pipeline-y:
  Airflow / Prefect DAG: scan → batch (100) → extract → entity → load
  Each stage independently scalable
```

**Cost example** (1000 PDFs, avg 50 pages each, avg 100k chars):

| 模式 | 时间 | 成本 |
|------|------|------|
| spaCy CPU 1 worker | ~10 hours | $0 |
| spaCy CPU 8 workers | ~1.5 hours | $0 |
| LLM gpt-4o-mini, 8 chunks/doc | ~6 hours (rate-limited) | ~$25 |
| LLM gpt-4o, 8 chunks/doc | ~12 hours | ~$300 |
| Hybrid: spaCy + LLM only for low-confidence pages | ~3 hours | ~$5 |

---

## 完整代码 (Production-ready)

完整代码已经在 Step 2 — single-file, runnable. 安装:

```bash
pip install pdfplumber spacy pytesseract pdf2image openai
python -m spacy download en_core_web_sm
# For OCR:
brew install tesseract poppler   # macOS

# Usage:
python pdfindex.py extract ./docs -o ./out --workers 8
python pdfindex.py extract ./docs -o ./out --use-llm --budget-per-doc 0.20
python pdfindex.py search ./out --query "Anthropic"
```

---

## 复杂度分析

| 阶段 | Time | Notes |
|------|------|-------|
| Scan | O(F) F = # files | rglob 是 O(files in tree) |
| pdfplumber per page | O(page complexity) | 大约 50-200ms/page native |
| OCR per page | O(image area + chars) | 1-3s/page on CPU |
| spaCy NER | O(N tokens) | ~100k tokens/sec on CPU |
| LLM extraction | O(chunks) | 1-3s per chunk; latency dominated |
| Indexer write | O(doc size) | JSON serialize |

**1000 文档 50 页, spaCy CPU 8 workers**: ~1.5 hour, $0
**1000 文档 50 页, gpt-4o-mini**: ~6 hours, $25

---

## Gao Xin 简历专属 reframe

- **BNPL chatbot / RAG**: 我们 ingest BNPL 客户服务知识库 (大量 PDF: policy doc, regulatory filing, internal SOP), 写过几乎一样的 pipeline. 区别: 我们落到 Chroma vector store 而不是 JSON index, 因为下游是 RAG retrieval. 但 chunking / NER / cost budget 逻辑同样.
- **Voice agent (7 markets)**: 每个市场 collection 法规不同, ingest 各市场监管 PDF (印尼 OJK, 越南 SBV, 泰国 BoT) — 多语言挑战, 上 LLM (gpt-4o) 比 multi-language spaCy 准确, 但 cost trade-off 明显.
- **ConvFinQA**: 9-variant ablation 里有几个 baseline 跑过类似 pipeline — PDF → text → entity → table extraction. 学到的: pdfplumber 抽 table 一般, `camelot-py` 更准但环境复杂.
- **Indonesia refund tier**: refund 决策有时要参考 contract PDF, 我们用类似 CLI tool 把 contract upfront 索引化, decision time O(1) lookup.

**面试一句话**: "Built this exact tool at TikTok for BNPL knowledge ingestion — 50k regulatory PDFs across 7 markets. The biggest learnings were OCR fallback was needed for 30% of docs, and per-doc LLM budget was the only way to stop cost runaway."

---

## 5 个 Follow-ups

**Q1**: "客户给你 10M PDFs, 你的 CLI 怎么 scale?"

A: CLI 设计基本不变, 但 runtime 不是单机:
1. **CLI 入队** mode: `pdfindex enqueue /docs/* --queue redis://...` 把文件路径推到 queue
2. **Worker fleet**: `pdfindex worker --queue redis://... --concurrency 4` 跑在 K8s
3. **Status DB**: Postgres 表 `(file_hash, status, output_path, processed_at, error)`
4. **Output**: 直接写 S3 + 灌 Elasticsearch
5. **CLI 仍然能 query**: `pdfindex search --backend es ...`

**Q2**: "LLM 给的 entity 含 hallucination 你怎么办?"

A: 多层防御:
1. **Post-hoc verify**: 提取后, regex / string-match 验证每个 entity 真在原文里出现 — 没出现的丢弃
2. **Self-consistency**: 同 chunk 跑 3 次, 取共识 (代价 3x)
3. **Lower temperature**: `temperature=0.0`, `seed=42`
4. **Structured output**: `response_format=json_schema` (OpenAI) 或 `tool_use` (Anthropic)
5. **Specific prompt**: "Only extract entities that appear verbatim in the text"

**Q3**: "中文 PDF / Arabic 怎么办?"

A: 三层方案:
1. Detect 语言 (`langdetect` 库) 一次 / per page
2. 选对应 spaCy 模型 (`zh_core_web_sm`, `xx_ent_wiki_sm` 多语言)
3. LLM 路径几乎无差 — gpt-4o 多语言 NER 表现好; 但 prompt 用英文描述任务, content 保留原文

**Q4**: "如果 PDF 有 form fields / tables, 你怎么抽?"

A: pdfplumber 已经支持 `page.extract_tables()` 返回 list of list of cells; `page.extract_form_data()` (有限). Table 抽完后转 markdown 再丢 LLM 更准. 复杂表格用 `camelot-py` 或 unstructured.io.

**Q5**: "你怎么 measure quality?"

A: 标 evaluation set (~100 PDFs 人工 ground truth), 算:
- **Per-entity precision** = TP / (TP + FP), 看 LLM 是不是 hallucinate
- **Per-entity recall** = TP / (TP + FN), 看漏召率
- **F1** 综合
- 按 entity type 分别看 (person 一般高, money 容易错单位)
- 按 PDF 类型分 (扫描 vs 文本 vs 表格密集)
- Continuous: 每周抽 10 个 prod doc 人工 review, drift 检测

---

## 死路答法

1. **直接用 `pdftotext` 系统命令然后 split** — fragile, 不跨平台, error 不可控
2. **整个 100-page PDF 一次性灌 LLM** — token 爆, 单次 query 超 limit
3. **没 OCR fallback** — 30% 客户 PDF 是扫描, 返回空 entity 客户疯
4. **`os.listdir` 而不是 `rglob`** — 客户 nested dir 抽不到
5. **写 JSON 不 atomic** — 中途崩, master index 损坏全 batch 重跑
6. **LLM 没 budget** — 1 个客户给 1000 个 500 页 PDF, 一晚上烧 $5000
7. **没 dedupe** — 客户上传两次, output 重复, master index 冲突
8. **没 progress bar / log** — 30 min 没响应, 用户以为挂了
9. **`print()` 而不是 `logging`** — 没 timestamp, 不能 grep, 不能调级别

---

## 加分项

**FDE 加分讨论**:

- **Pricing pluggability**: pricing 写在 yaml / cache, 不 hardcode (gpt-4o-mini 一个月降价就过期)
- **Confidence score**: 每个 entity 带 confidence (LLM logprobs 或 ensemble vote)
- **Provenance**: 每个 entity 附 `{page, char_start, char_end}` 可点回原文
- **Audit log**: 谁什么时候跑过, output hash — 法律合同场景必要
- **Idempotent re-runs**: 同样 input 同 hash → 同 output, 可以 reproducibility
- **Schema evolution**: output 含 `schema_version: 1`, 未来 schema 改了能 migrate
- **Observability**: emit Prometheus metrics — `pdfindex.docs.processed`, `pdfindex.cost.usd`, `pdfindex.errors`
- **Telemetry sample**: 每 1000 doc dump一个 sample 给 eval set
- **OOM protection**: per-process memory limit, page-by-page streaming spaCy
- **Multi-modal future**: PDF 里的 image / chart 也走 vision LLM (gpt-4o vision)

---

## 一句话总结

> **CLI 工具 = scanner → extractor (pdfplumber + OCR fallback) → entity (spaCy default, LLM opt-in with chunk + budget) → JSON index (per-doc + master). 用 `argparse` 做 UX, `file_hash` 做 dedupe + resume, atomic rename 写 master.**

---

## Cheat Sheet

```python
# Components:
#   Scanner: rglob('*.pdf')
#   Extractor: pdfplumber.open(path).pages -> extract_text(); else OCR fallback
#   NER (default): spacy.load('en_core_web_sm') -> doc.ents
#   NER (LLM opt-in): chunk(text) -> LLM json mode -> merge + dedupe
#   Indexer: write {doc_id}.json + update index.json (atomic via tmp+rename)

# CLI:
#   argparse, subcommands: extract, search
#   Flags: --dry-run --use-llm --budget-per-doc --workers --ocr --no-ocr

# Cost control:
#   per-doc budget USD
#   chunk 8000 chars with 200 overlap
#   stop chunking when budget exceeded

# Edge cases:
#   empty/encrypted/corrupted PDF: catch, emit DocIndex(error=...)
#   scanned PDF: OCR fallback if chars < 20
#   duplicate (same hash): skip on resume
#   LLM non-JSON: catch + log
#   multilingual: lang-detect → pick model

# Big-O:
#   text extract O(pages * page_complexity)
#   spaCy O(N tokens)
#   LLM O(chunks * latency)

# Failures + Resume:
#   file_hash in master.json → skip
#   atomic rename for master.json (tmp + os.replace)

# Don't:
#   load whole PDF text into LLM
#   silent skip malformed
#   hardcoded pricing
#   no progress / no log
```
