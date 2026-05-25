#!/usr/bin/env python3
"""Merge per-company question lists into a unified multi-company structure.

Reads:
  - openai-interview-questions.json
  - site/data/google-questions.json
Writes:
  - site/data/questions.json with structure:
    [
      {
        "slug": "/community/questions/.../<id>",
        "title": "...",
        "type": "Coding|System Design|...",
        "description": "...",
        "url": "https://...",
        "companies": {
          "OpenAI": {"level": "...", "reportedUsers": N, "lastAsked": "..."},
          "Google": {"level": "...", "reportedUsers": N, "lastAsked": "..."}
        }
      },
      ...
    ]
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_PATH = ROOT / "site" / "data" / "questions.json"

SOURCES = [
    # OpenAI sources disabled per user request (slimming down, focus on Google FDE prep)
    # ("OpenAI", ROOT / "openai-interview-questions.json"),
    # Google coding-only pages 1-3 (initial round)
    ("Google", ROOT / "site" / "data" / "google-questions.json"),
    # Google all-types pages 1-5 (expanded round) — overlapping with above is fine,
    # merge dedupes by slug. Both contribute the same "Google" badge.
    ("Google", ROOT / "site" / "data" / "google-all-questions.json"),
    # Google Coding extra — 77 more questions scraped from hellointerview.com 7 pages
    # (May 2026, complete coverage of Google Coding category for Google L5 tag)
    ("Google", ROOT / "site" / "data" / "google-coding-extra.json"),
    # Hand-written guides / longform articles (not scraped from hellointerview)
    # ("OpenAI", ROOT / "site" / "data" / "guides.json"),  # disabled (Tomoro/OpenAI-themed)
    # FDE (Forward Deployed Engineer) curated real interview questions
    # from Palantir / OpenAI / ElevenLabs / Google FDE reports
    ("FDE", ROOT / "site" / "data" / "fde-questions.json"),
    # Google FDE prep — HR-tipped topic areas (Tool calling / RAG / LLM eng / Delivery)
    ("Google FDE", ROOT / "site" / "data" / "google-fde-prep.json"),
    # Review / rapid-recall pages — extracted Extended Cheat Sheets from the 49 full pages
    ("Review", ROOT / "site" / "data" / "review-pages.json"),
    # 真题 — Exponent 2026 整理的 FDE 52 道高频真题 (Palantir/OpenAI/Anthropic/Databricks/Scale/ElevenLabs)
    ("真题", ROOT / "site" / "data" / "fde-real-questions.json"),
]

def main():
    merged: dict[str, dict] = {}
    for company, path in SOURCES:
        if not path.exists():
            print(f"  skip {company}: {path} not found")
            continue
        items = json.load(open(path))
        for q in items:
            slug = q["slug"]
            entry = merged.setdefault(slug, {
                "slug": slug,
                "title": q["title"],
                "type": q["type"],
                "description": q.get("description", ""),
                "url": q["url"],
                "companies": {},
            })
            # Update fields that may differ slightly (longer description wins)
            if len(q.get("description", "") or "") > len(entry["description"] or ""):
                entry["description"] = q["description"]
            entry["companies"][company] = {
                "level": q.get("level"),
                "reportedUsers": q.get("reportedUsers"),
                "lastAsked": q.get("lastAsked"),
            }
            # Carry top-level algorithm/data-structure tag if any source provides it
            if q.get("algoTag"):
                entry["algoTag"] = q["algoTag"]
            # Carry popularityRank (hellointerview's "Recent and Popular" position)
            if q.get("popularityRank"):
                # Keep the lowest rank (= most popular) if multiple sources contribute
                cur = entry.get("popularityRank")
                if cur is None or q["popularityRank"] < cur:
                    entry["popularityRank"] = q["popularityRank"]
        print(f"  merged {company}: {len(items)} questions")

    items = list(merged.values())
    print(f"\nTotal unique questions: {len(items)}")

    # Stats
    from collections import Counter
    by_company = Counter()
    by_type = Counter()
    for q in items:
        for c in q["companies"]:
            by_company[c] += 1
        by_type[q["type"]] += 1
    print("\nBy company:")
    for c, n in by_company.most_common():
        print(f"  {c}: {n}")
    print("\nBy type:")
    for t, n in by_type.most_common():
        print(f"  {t}: {n}")

    with open(OUT_PATH, "w") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {OUT_PATH}")

if __name__ == "__main__":
    main()
