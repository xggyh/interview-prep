"""Bundle each deep-dive HTML into a single self-contained file.

iOS Files app Quick Look doesn't run JavaScript and only loosely resolves
relative paths. By inlining CSS + Prism into each HTML, the files preview
correctly with just a tap — no third-party app required.

Output: public_offline/<slug>.html — one per deep-dive page.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PUBLIC = ROOT / "public"
OUT_DIR = ROOT / "public_offline"
ASSETS = PUBLIC / "assets"
PRISM = ASSETS / "prism"


def read(p: Path) -> str:
    return p.read_text()


def inline_assets(html: str) -> str:
    style_css = read(ASSETS / "style.css")
    prism_css = read(PRISM / "prism-tomorrow.css")
    prism_core = read(PRISM / "prism-core.min.js")
    prism_autoloader = read(PRISM / "prism-autoloader.min.js")
    # Inline a curated set of language components so the page never needs to
    # fetch anything at runtime.
    langs = ["markup", "clike", "python", "javascript", "java", "bash",
             "sql", "json", "yaml", "typescript", "go", "rust"]
    lang_js_parts = []
    for lang in langs:
        p = PRISM / "components" / f"prism-{lang}.min.js"
        if p.exists():
            lang_js_parts.append(read(p))
    lang_js = "\n".join(lang_js_parts)

    # Use lambda-based replacement so the (CSS/JS) content isn't interpreted as regex.
    style_block = f"<style>\n{style_css}\n</style>"
    prism_css_block = f"<style>\n{prism_css}\n</style>"
    prism_core_block = f"<script>\n{prism_core}\n</script>"
    autoloader_replacement = (
        f"<script>\n{lang_js}\n</script>\n"
        "<script>/* autoloader skipped — languages inlined above */</script>"
    )

    html = re.sub(r'<link rel="stylesheet" href="\.\./assets/style\.css[^"]*">',
                  lambda _m: style_block, html)
    html = re.sub(r'<link rel="stylesheet" href="\.\./assets/prism/prism-tomorrow\.css">',
                  lambda _m: prism_css_block, html)
    html = re.sub(r'<script src="\.\./assets/prism/prism-core\.min\.js"></script>',
                  lambda _m: prism_core_block, html)
    html = re.sub(r'<script src="\.\./assets/prism/prism-autoloader\.min\.js"></script>',
                  lambda _m: autoloader_replacement, html)
    html = re.sub(r'<script>if\(window\.Prism\).*?</script>', "", html)
    # 6) Rewrite navigation links so they degrade to a friendly hint instead
    # of trying to load a sibling HTML that may not exist in the offline bundle.
    html = re.sub(
        r'<a href="\.\./index\.html">',
        '<a href="#" onclick="alert(\'返回列表在完整离线包里；本文件是独立单页\');return false;">',
        html,
    )
    # Prev/next links inside the page — keep them as hash-disabled anchors
    html = re.sub(
        r'<a href="(?!https?:|#)[^"]+\.html"([^>]*)>',
        r'<a href="#" onclick="alert(\'此链接需要完整离线包\');return false;"\1>',
        html,
    )
    return html


def main():
    deep_slugs = []
    for p in (PUBLIC / "questions").glob("*.html"):
        body = read(p)
        if "deep-banner" in body or 'class="q-card is-deep' in body:
            deep_slugs.append(p)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    titles = []
    for p in sorted(deep_slugs):
        html = read(p)
        inlined = inline_assets(html)
        out = OUT_DIR / p.name
        out.write_text(inlined)

        # extract title for the index
        m = re.search(r"<title>([^<]+)</title>", inlined)
        title = m.group(1) if m else p.stem
        titles.append((p.name, title))
        print(f"  wrote {out.name}  ({len(inlined) // 1024} KB)")

    # Write a tiny index.html listing the bundled pages (so user can browse
    # from one place if their iOS Files view is cluttered).
    items = "\n".join(
        f'  <li><a href="{name}">{title.split("·")[0].strip()}</a></li>'
        for name, title in titles
    )
    index_html = f"""<!doctype html>
<html lang="zh-CN"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>教学版离线包</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif;
       max-width: 720px; margin: 24px auto; padding: 0 16px; line-height: 1.6; }}
h1 {{ font-size: 18px; }}
ul {{ padding-left: 20px; }}
li {{ margin: 8px 0; font-size: 15px; }}
a {{ color: #0969da; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
.note {{ color: #57606a; font-size: 13px; }}
</style></head>
<body>
<h1>📚 教学版深度讲解（离线，{len(titles)} 篇）</h1>
<p class="note">每篇都是单 HTML 文件，可直接在 iOS Files / Safari 打开。</p>
<ul>
{items}
</ul>
</body></html>
"""
    (OUT_DIR / "index.html").write_text(index_html)
    print(f"\nwrote {OUT_DIR}/index.html with {len(titles)} entries")


if __name__ == "__main__":
    main()
