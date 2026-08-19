#!/usr/bin/env python3
"""
MyTeacher blog generatori.

    content/blog/*.md  ->  blog/<slug>.html   (maqola sahifalari)
                           blog/index.html    (blog ro'yxati)
                           sitemap.xml        (qayta yoziladi)

Tashqi kutubxona talab qilmaydi — faqat Python 3.8+.

Ishga tushirish (repo ildizidan):

    python3 tools/build_blog.py

Har safar maqola qo'shganda yoki tahrirlaganda shu buyruqni ishga tushiring,
so'ng natijani commit qiling. Deploy o'zgarmaydi — chiqish statik HTML.
"""

import html
import os
import re
import sys
from datetime import date

# ---------------------------------------------------------------- sozlamalar

SITE = "https://myteacher.uz"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "content", "blog")
OUT_DIR = os.path.join(ROOT, "blog")

# sitemapga qo'shiladigan, blogdan tashqari sahifalar: (yo'l, lastmod)
STATIC_PAGES = [
    ("/", "2026-08-19"),
    ("/sharhlar.html", "2026-08-07"),
]

OYLAR = [
    "yanvar", "fevral", "mart", "aprel", "may", "iyun",
    "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr",
]

ICONS = {
    "arrow-left": '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
    "arrow-right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "calendar": '<path d="M8 2v3"/><path d="M16 2v3"/>'
                '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/>',
}


def icon(name, cls="w-4 h-4"):
    return (
        '<svg class="%s" xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
        'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg>'
        % (cls, ICONS[name])
    )


# ------------------------------------------------------------ markdown -> html

def _inline(text):
    """Satr ichidagi markdown: kod, havola, qalin, kursiv."""
    text = html.escape(text, quote=False)

    stash = []

    def keep(markup):
        stash.append(markup)
        return "\x00%d\x00" % (len(stash) - 1)

    # `kod` — birinchi bo'lib himoyalanadi
    text = re.sub(r"`([^`]+)`", lambda m: keep("<code>%s</code>" % m.group(1)), text)
    # [matn](url)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)\)",
        lambda m: keep('<a href="%s">%s</a>' % (html.escape(m.group(2), quote=True), m.group(1))),
        text,
    )
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)

    for i, markup in enumerate(stash):
        text = text.replace("\x00%d\x00" % i, markup)
    return text


def md_to_html(md):
    """Markdownning maqolalar uchun yetarli qismini HTMLga o'giradi."""
    lines = md.replace("\r\n", "\n").split("\n")
    out = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        if line.startswith("### "):
            out.append("<h3>%s</h3>" % _inline(line[4:].strip()))
            i += 1

        elif line.startswith("## "):
            out.append("<h2>%s</h2>" % _inline(line[3:].strip()))
            i += 1

        elif line.strip() in ("---", "***", "___"):
            out.append("<hr />")
            i += 1

        elif line.startswith("> "):
            buf = []
            while i < n and lines[i].startswith("> "):
                buf.append(lines[i][2:].strip())
                i += 1
            out.append("<blockquote><p>%s</p></blockquote>" % _inline(" ".join(buf)))

        elif line.lstrip().startswith("|") and i + 1 < n and set(lines[i + 1].replace("|", "").strip()) <= set("-: "):
            head = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            th = "".join("<th>%s</th>" % _inline(c) for c in head)
            tb = "".join(
                "<tr>%s</tr>" % "".join("<td>%s</td>" % _inline(c) for c in r) for r in rows
            )
            out.append(
                '<div class="table-wrap"><table><thead><tr>%s</tr></thead>'
                "<tbody>%s</tbody></table></div>" % (th, tb)
            )

        elif re.match(r"^\s*[-*]\s+", line):
            items = []
            while i < n and re.match(r"^\s*[-*]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*]\s+", "", lines[i]).strip())
                i += 1
            out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % _inline(x) for x in items))

        elif re.match(r"^\s*\d+\.\s+", line):
            items = []
            while i < n and re.match(r"^\s*\d+\.\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+\.\s+", "", lines[i]).strip())
                i += 1
            out.append("<ol>%s</ol>" % "".join("<li>%s</li>" % _inline(x) for x in items))

        else:
            buf = []
            while i < n and lines[i].strip() and not re.match(
                r"^(#{2,3} |> |---$|\*\*\*$|\s*[-*]\s+|\s*\d+\.\s+|\|)", lines[i]
            ):
                buf.append(lines[i].strip())
                i += 1
            if buf:
                out.append("<p>%s</p>" % _inline(" ".join(buf)))
            else:
                i += 1

    return "\n".join(out)


# ------------------------------------------------------------------ manbalar

def parse_post(path):
    raw = open(path, encoding="utf-8").read()
    if not raw.startswith("---"):
        sys.exit("XATO: %s — frontmatter (--- bloki) topilmadi" % path)

    _, fm, body = raw.split("---", 2)
    meta = {}
    for line in fm.strip().split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")

    slug = meta.get("slug") or os.path.splitext(os.path.basename(path))[0]
    for field in ("title", "description", "date"):
        if not meta.get(field):
            sys.exit("XATO: %s — '%s' maydoni yo'q" % (path, field))

    try:
        d = date.fromisoformat(meta["date"])
    except ValueError:
        sys.exit("XATO: %s — sana YYYY-MM-DD formatida bo'lishi kerak" % path)

    words = len(re.sub(r"[^\w\s]", "", body).split())
    return {
        "slug": slug,
        "title": meta["title"],
        "description": meta["description"],
        "date": d,
        "date_uz": "%d-%s %d" % (d.day, OYLAR[d.month - 1], d.year),
        "keywords": meta.get("keywords", ""),
        "author": meta.get("author", ""),
        "reviewed_by": meta.get("reviewed_by", ""),
        "read_min": max(1, round(words / 180)),
        "body_html": md_to_html(body.strip()),
        "url": "%s/blog/%s.html" % (SITE, slug),
    }


# ------------------------------------------------------------------- shablon

def tailwind_block():
    """Precompiled Tailwind blokini index.html dan oladi — shunda u doim sinxron."""
    src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    m = re.search(r'<style id="tailwind-precompiled">.*?</style>', src, re.S)
    if not m:
        sys.exit("XATO: index.html ichidan tailwind-precompiled bloki topilmadi")
    return m.group(0)


HEAD_COMMON = """<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<meta name="language" content="Uzbek" />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Sora:wght@400;500;600;700;800&display=swap" rel="stylesheet">"""

PAGE_CSS = """<style>
  body { font-family: 'Inter', sans-serif; background-color: #fbfaf9; }
  .font-display { font-family: 'Sora', sans-serif; }
  .text-gradient {
    background: linear-gradient(90deg, #0ea5e9, #06b6d4);
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }

  .article { font-size: 1.0625rem; line-height: 1.78; color: #334155; }
  .article > * + * { margin-top: 1.35rem; }
  .article h2 {
    font-family: 'Sora', sans-serif; font-weight: 700; font-size: 1.5rem;
    line-height: 1.3; color: #0f172a; margin-top: 3rem; letter-spacing: -0.01em;
  }
  .article h3 {
    font-family: 'Sora', sans-serif; font-weight: 600; font-size: 1.175rem;
    line-height: 1.4; color: #0f172a; margin-top: 2.25rem;
  }
  .article a { color: #0369a1; text-decoration: underline; text-underline-offset: 2px; }
  .article a:hover { color: #075985; }
  .article strong { color: #0f172a; font-weight: 650; }
  .article ul, .article ol { padding-left: 1.3rem; }
  .article li { margin-top: 0.5rem; }
  .article ul li::marker { color: #0ea5e9; }
  .article ol li::marker { color: #0ea5e9; font-weight: 600; }
  .article blockquote {
    border-left: 3px solid #0ea5e9; background: #f0f9ff;
    padding: 1rem 1.25rem; border-radius: 0 8px 8px 0; color: #0c4a6e;
  }
  .article blockquote p { margin: 0; }
  .article code {
    background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 4px;
    padding: 0.1em 0.35em; font-size: 0.9em;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  }
  .article hr { border: 0; border-top: 1px solid #e2e8f0; margin-top: 2.5rem; }
  .table-wrap { overflow-x: auto; }
  .article table { border-collapse: collapse; width: 100%; font-size: 0.95rem; min-width: 24rem; }
  .article th, .article td { text-align: left; padding: 0.6rem 0.9rem 0.6rem 0; border-bottom: 1px solid #e2e8f0; }
  .article th { font-weight: 650; color: #0f172a; }
</style>"""


def site_header():
    return """<header class="border-b border-slate-200 bg-white/90 backdrop-blur sticky top-0 z-40">
  <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
    <a href="/" class="font-display font-extrabold text-lg text-slate-900">MyTeacher</a>
    <a href="/blog/" class="inline-flex items-center gap-1.5 text-sm font-semibold text-sky-700 hover:text-sky-800">
      Blog
    </a>
  </div>
</header>"""


def site_footer():
    return """<footer class="border-t border-slate-200 py-8 text-center text-xs text-slate-500">
  &copy; 2026 MyTeacher. Barcha huquqlar himoyalangan.
</footer>"""


def render_page(title, description, canonical, body, extra_head="", og_type="article"):
    return """<!DOCTYPE html>
<html lang="uz">
<head>
%(head)s
<title>%(title_txt)s</title>
<meta name="description" content="%(desc)s" />
<link rel="canonical" href="%(canonical)s" />
<meta property="og:type" content="%(ogtype)s" />
<meta property="og:site_name" content="MyTeacher" />
<meta property="og:url" content="%(canonical)s" />
<meta property="og:title" content="%(title)s" />
<meta property="og:description" content="%(desc)s" />
<meta property="og:locale" content="uz_UZ" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="%(title)s" />
<meta name="twitter:description" content="%(desc)s" />
%(extra)s
%(tailwind)s
%(css)s
</head>
<body class="text-slate-800 antialiased">
%(header)s
%(body)s
%(footer)s
</body>
</html>
""" % {
        "head": HEAD_COMMON,
        "title_txt": html.escape(title, quote=False),
        "title": html.escape(title, quote=True),
        "desc": html.escape(description, quote=True),
        "canonical": canonical,
        "ogtype": og_type,
        "extra": extra_head,
        "tailwind": tailwind_block(),
        "css": PAGE_CSS,
        "header": site_header(),
        "body": body,
        "footer": site_footer(),
    }


def render_post(post):
    schema = """<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": %(title)s,
  "description": %(desc)s,
  "datePublished": "%(date)s",
  "dateModified": "%(date)s",
  "inLanguage": "uz",
  "author": %(author_ld)s,%(reviewed_ld)s
  "publisher": {
    "@type": "Organization",
    "name": "MyTeacher",
    "url": "%(site)s/"
  },
  "mainEntityOfPage": { "@type": "WebPage", "@id": "%(url)s" }
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Bosh sahifa", "item": "%(site)s/" },
    { "@type": "ListItem", "position": 2, "name": "Blog", "item": "%(site)s/blog/" },
    { "@type": "ListItem", "position": 3, "name": %(title)s, "item": "%(url)s" }
  ]
}
</script>""" % {
        "title": _json_str(post["title"]),
        "desc": _json_str(post["description"]),
        "date": post["date"].isoformat(),
        "url": post["url"],
        "site": SITE,
        "author_ld": (
            '{ "@type": "Person", "name": %s }' % _json_str(post["author"])
            if post["author"] else '{ "@type": "Organization", "name": "MyTeacher" }'
        ),
        "reviewed_ld": (
            '\n  "reviewedBy": { "@type": "Person", "name": %s },' % _json_str(post["reviewed_by"])
            if post["reviewed_by"] else ""
        ),
    }

    body = """<main class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
  <a href="/blog/" class="inline-flex items-center gap-1.5 text-sm font-semibold text-sky-700 hover:text-sky-800">
    %(back)s Barcha maqolalar
  </a>

  <h1 class="mt-6 font-display font-extrabold text-3xl sm:text-4xl text-slate-900 tracking-tight">%(title)s</h1>

  <div class="mt-4 flex flex-wrap items-center gap-4 text-sm text-slate-500">
    <span class="inline-flex items-center gap-1.5">%(cal)s <time datetime="%(iso)s">%(date_uz)s</time></span>
    <span class="inline-flex items-center gap-1.5">%(clock)s %(read)s daqiqa o'qish</span>
%(byline)s  </div>

  <p class="mt-6 text-lg text-slate-600">%(lede)s</p>

  <hr class="mt-8 border-slate-200" />

  <div class="article mt-8">
%(content)s
  </div>

  <div class="mt-14 rounded-2xl bg-white border border-slate-200 p-6 sm:p-8 shadow-sm text-center">
    <h2 class="font-display font-extrabold text-xl text-slate-900">Ingliz tilini mentor nazorati ostida o'rganing</h2>
    <p class="mt-3 text-slate-600">15,000+ o'quvchi MyTeacher bilan natijaga erishdi. Sinov darsiga yoziling.</p>
    <a href="/#tariflar" class="mt-5 inline-flex items-center gap-1.5 rounded-full bg-sky-600 hover:bg-sky-700 text-white px-6 py-3 text-sm font-semibold transition-colors">
      Sinab ko'rish %(fwd)s
    </a>
  </div>
</main>""" % {
        "back": icon("arrow-left"),
        "cal": icon("calendar"),
        "clock": icon("clock"),
        "fwd": icon("arrow-right"),
        "title": html.escape(post["title"]),
        "iso": post["date"].isoformat(),
        "date_uz": post["date_uz"],
        "read": post["read_min"],
        "byline": _byline(post),
        "lede": html.escape(post["description"]),
        "content": post["body_html"],
    }

    extra = schema
    if post["keywords"]:
        extra = '<meta name="keywords" content="%s" />\n%s' % (
            html.escape(post["keywords"], quote=True), schema)

    return render_page(post["title"], post["description"], post["url"], body, extra)


def _byline(post):
    parts = []
    if post["author"]:
        parts.append('<span>Muallif: <strong class="text-slate-700 font-semibold">%s</strong></span>'
                     % html.escape(post["author"]))
    if post["reviewed_by"]:
        parts.append('<span>Tekshirdi: <strong class="text-slate-700 font-semibold">%s</strong></span>'
                     % html.escape(post["reviewed_by"]))
    return "".join("    %s\n" % x for x in parts)


def _json_str(s):
    return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"')


def render_index(posts):
    cards = []
    for p in posts:
        cards.append("""    <article class="rounded-2xl bg-white border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
      <div class="flex flex-wrap items-center gap-3 text-xs text-slate-500">
        <time datetime="%(iso)s">%(date_uz)s</time>
        <span>&middot;</span>
        <span>%(read)s daqiqa o'qish</span>
      </div>
      <h2 class="mt-3 font-display font-bold text-xl text-slate-900 leading-snug">
        <a href="/blog/%(slug)s.html" class="hover:text-sky-700 transition-colors">%(title)s</a>
      </h2>
      <p class="mt-2.5 text-slate-600 text-sm leading-relaxed">%(desc)s</p>
      <a href="/blog/%(slug)s.html" class="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-sky-700 hover:text-sky-800">
        O'qish %(fwd)s
      </a>
    </article>""" % {
            "iso": p["date"].isoformat(),
            "date_uz": p["date_uz"],
            "read": p["read_min"],
            "slug": p["slug"],
            "title": html.escape(p["title"]),
            "desc": html.escape(p["description"]),
            "fwd": icon("arrow-right", "w-3.5 h-3.5"),
        })

    body = """<main class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
  <div class="text-center max-w-2xl mx-auto">
    <h1 class="font-display font-extrabold text-3xl sm:text-4xl text-slate-900 tracking-tight">
      Ingliz tili haqida <span class="text-gradient">foydali maqolalar</span>
    </h1>
    <p class="mt-4 text-slate-600">
      IELTS va CEFR tayyorgarligi, so'z boyligini oshirish, Speaking mashqlari va o'rganish metodikasi —
      MyTeacher mentorlari tajribasidan.
    </p>
  </div>

  <div class="mt-12 grid sm:grid-cols-2 gap-5">
%(cards)s
  </div>
</main>""" % {"cards": "\n".join(cards)}

    items = ",\n".join(
        '      { "@type": "ListItem", "position": %d, "url": "%s", "name": %s }'
        % (i + 1, p["url"], _json_str(p["title"]))
        for i, p in enumerate(posts)
    )
    schema = """<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Blog",
  "name": "MyTeacher blogi",
  "description": "Ingliz tilini samarali o'rganish bo'yicha amaliy maqolalar.",
  "inLanguage": "uz",
  "url": "%(site)s/blog/",
  "publisher": { "@type": "Organization", "name": "MyTeacher", "url": "%(site)s/" },
  "mainEntity": {
    "@type": "ItemList",
    "itemListElement": [
%(items)s
    ]
  }
}
</script>""" % {"site": SITE, "items": items}

    return render_page(
        "Blog — Ingliz tili bo'yicha foydali maqolalar | MyTeacher",
        "Ingliz tilini samarali o'rganish bo'yicha amaliy maqolalar: IELTS va CEFR tayyorgarligi, "
        "so'z boyligi, Speaking mashqlari va o'rganish metodikasi.",
        "%s/blog/" % SITE,
        body,
        schema,
        og_type="website",
    )


def write_sitemap(posts):
    urls = list(STATIC_PAGES)
    newest = max((p["date"] for p in posts), default=None)
    if posts:
        urls.append(("/blog/", newest.isoformat()))
        for p in posts:
            urls.append(("/blog/%s.html" % p["slug"], p["date"].isoformat()))

    entries = "\n".join(
        "  <url>\n    <loc>%s%s</loc>\n    <lastmod>%s</lastmod>\n  </url>" % (SITE, path, lastmod)
        for path, lastmod in urls
    )
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           "%s\n</urlset>\n" % entries)
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(xml)
    return len(urls)


def main():
    if not os.path.isdir(SRC_DIR):
        sys.exit("XATO: %s papkasi topilmadi" % SRC_DIR)

    # README.md va "_" bilan boshlanadigan fayllar maqola emas — chetlab o'tiladi
    files = sorted(
        f for f in os.listdir(SRC_DIR)
        if f.endswith(".md") and f.lower() != "readme.md" and not f.startswith("_")
    )
    if not files:
        sys.exit("XATO: %s ichida .md fayl yo'q" % SRC_DIR)

    posts = [parse_post(os.path.join(SRC_DIR, f)) for f in files]

    slugs = [p["slug"] for p in posts]
    dupes = {s for s in slugs if slugs.count(s) > 1}
    if dupes:
        sys.exit("XATO: takrorlangan slug: %s" % ", ".join(sorted(dupes)))

    posts.sort(key=lambda p: p["date"], reverse=True)

    os.makedirs(OUT_DIR, exist_ok=True)
    for p in posts:
        path = os.path.join(OUT_DIR, "%s.html" % p["slug"])
        open(path, "w", encoding="utf-8").write(render_post(p))
        print("  maqola  blog/%s.html  (%d daqiqa, %.0f KB)"
              % (p["slug"], p["read_min"], os.path.getsize(path) / 1024))

    idx = os.path.join(OUT_DIR, "index.html")
    open(idx, "w", encoding="utf-8").write(render_index(posts))
    print("  ro'yxat blog/index.html  (%.0f KB)" % (os.path.getsize(idx) / 1024))

    count = write_sitemap(posts)
    print("  sitemap.xml — %d ta URL" % count)
    print("\nTayyor: %d ta maqola." % len(posts))


if __name__ == "__main__":
    main()
