#!/usr/bin/env python3
"""
CAVE Clinic static site builder.

Run:  python3 build.py
Then: python3 -m http.server 8000 --directory site   (open http://localhost:8000)

Edit the words and prices in /data. Drop photos into /images (see images/README.md)
and run the build again: placeholders are swapped for real images automatically.
"""
import html, json, os, re, shutil, glob
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "site")
D = lambda f: json.load(open(os.path.join(ROOT, "data", f), encoding="utf-8"))
SITE, LOCS, TEAM, REVIEWS = D("site.json"), D("locations.json"), D("team.json"), D("reviews.json")
RESULTS, TREATS, EVENTS, PARIS = D("results.json"), D("treatments.json"), D("events.json"), D("paris.json")
BOOK = SITE["book"]
URL = SITE["url"].rstrip("/")
esc = lambda s: html.escape(str(s), quote=True)
BANNED = re.compile(r"botox|botulinum|azzalure|bocouture|dysport|xeomin|letybo|relfydess", re.I)

# ---------------------------------------------------------------- images
IMG_DIR = os.path.join(ROOT, "images")
def find_media(name, exts):
    for e in exts:
        p = os.path.join(IMG_DIR, name + e)
        if os.path.exists(p):
            return name + e
    return None

def img(name, alt, label=None, cls="", eager=False, dark=False, attrs=""):
    """A .media box with a real photo if images/<name>.webp|jpg exists, else a labelled placeholder."""
    f = find_media(name, [".webp", ".jpg", ".jpeg", ".png"])
    if f:
        inner = (f'<img src="/assets/img/{f}" alt="{esc(alt)}" '
                 f'{"fetchpriority=\"high\"" if eager else "loading=\"lazy\""} decoding="async">')
    else:
        inner = ph_html(alt, label, dark)
    return f'<div class="media {cls}" {attrs}>{inner}</div>'

def ph_html(alt, label, dark=False):
    role = f'role="img" aria-label="{esc(alt)}"' if alt else 'aria-hidden="true"'
    span = f'<span>{esc(label)}</span>' if label != "" else ""
    if label is None:
        span = "<span>Clinic photo to add</span>"
    return f'<div class="ph{" ph--dark" if dark else ""}" {role}>{span}</div>'

def img_inner(name, alt, label=None, dark=False, eager=False):
    f = find_media(name, [".webp", ".jpg", ".jpeg", ".png"])
    if f:
        return f'<img src="/assets/img/{f}" alt="{esc(alt)}" {"fetchpriority=\"high\"" if eager else "loading=\"lazy\""} decoding="async">'
    return ph_html(alt, label, dark)

def video(name, poster, alt, label, dark=True):
    v = find_media(name, [".mp4", ".webm"])
    p = find_media(poster, [".webp", ".jpg", ".jpeg"])
    ph = img_inner(poster, alt, label, dark=dark, eager=True)
    if not v:
        return ph
    return (ph + f'<video data-autoplay autoplay muted loop playsinline preload="metadata" '
            f'{f"poster=/assets/img/{p}" if p else ""} aria-label="{esc(alt)}"><source src="/assets/img/{v}"></video>')

def video_src(name):
    v = find_media(name, [".mp4", ".webm"])
    return f"/assets/img/{v}" if v else ""

STAR = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2l2.9 6.9 7.1.6-5.4 4.7 1.6 7-6.2-3.8-6.2 3.8 1.6-7L2 9.5l7.1-.6z"/></svg>'
STARS = f'<div class="stars" role="img" aria-label="5 out of 5 stars">{STAR * 5}</div>'

def book(label="Book a consultation", cls="btn"):
    return f'<a class="{cls}" href="{BOOK}" target="_blank" rel="noopener">{label}<span class="sr-only"> (opens in a new tab)</span></a>'

# ---------------------------------------------------------------- shell
NAV_L = [("/treatments/", "Treatments"), ("/the-cave-secret/", "The CAVE Secret"), ("/the-clinic/", "The clinic")]
NAV_R = [("/paris/", "Paris"), ("/results/", "Results")]
MENU = NAV_L + NAV_R + [("/team/", "The team"), ("/events/", "Events"), ("/academy/", "Academy"), ("/journal/", "Journal"), ("/contact/", "Contact")]

def wordmark():
    return '<span class="wordmark"><span class="wm-cave">Cave</span><span class="wm-clinic">CLINIC</span></span>'

def header(path):
    cur = lambda href: ' aria-current="page"' if path.startswith(href) else ""
    l = "".join(f'<a href="{h}"{cur(h)}>{t}</a>' for h, t in NAV_L)
    r = "".join(f'<a href="{h}"{cur(h)}>{t}</a>' for h, t in NAV_R)
    strip = "".join(img(f"menu-{i}", a, "Photo") for i, a in enumerate(
        ["Sheer curtains and bouclé chairs at the clinic entrance", "The chocolate bouclé sofa in the lounge",
         "The sculptural lounger in the treatment suite", "Brass wall lights and plaster artwork"], 1))
    links = "".join(f'<li><a href="{h}">{t}</a></li>' for h, t in MENU)
    return f'''
<a class="skip" href="#main">Skip to content</a>
<header class="header" role="banner">
  <div class="container header-inner">
    <nav class="nav" aria-label="Primary">{l}</nav>
    <a class="header-mobile-book link" href="{BOOK}" target="_blank" rel="noopener">Book<span class="sr-only"> (opens in a new tab)</span></a>
    <a href="/" aria-label="CAVE Clinic home">{wordmark()}</a>
    <nav class="nav nav--right" aria-label="Secondary">{r}{book("Book", "btn btn--sm")}</nav>
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="menu" aria-label="Open menu"><span></span><span></span></button>
  </div>
</header>
<div class="menu" id="menu" role="dialog" aria-modal="true" aria-label="Menu" hidden>
  <div class="menu-top"><span></span>{wordmark()}<button class="menu-close" type="button" aria-label="Close menu"></button></div>
  <ul class="menu-links">{links}</ul>
  <div class="menu-strip">{strip}</div>
  <div class="menu-meta"><a class="link" href="tel:{SITE["phoneIntl"]}">{SITE["phone"]}</a>{book("Book", "link")}</div>
</div>'''

def footer():
    addr = "".join(f'<address>{esc(l["name"])}<br>{esc(l["street"])}<br>{esc(l["locality"])} {esc(l["postcode"])}</address>' for l in LOCS)
    explore = [("/treatments/", "Treatments"), ("/the-cave-secret/", "The CAVE Secret"), ("/the-clinic/", "The clinic"), ("/paris/", "Paris"),
               ("/results/", "Results"), ("/events/", "Events"), ("/academy/", "Academy"), ("/journal/", "Journal")]
    ex = "".join(f'<li><a href="{h}">{t}</a></li>' for h, t in explore)
    email = f'<li><a href="mailto:{SITE["email"]}">{SITE["email"]}</a></li>' if SITE["email"] else ""
    return f'''
<footer class="footer" role="contentinfo">
  <svg class="footer-giant" viewBox="0 0 1000 250" aria-hidden="true" focusable="false"><text x="500" y="235" text-anchor="middle" font-family="Boska, Times New Roman, serif" font-size="320" letter-spacing="24" fill="currentColor">CAVE</text></svg>
  <div class="container">
    <div class="footer-cols">
      <div><h2>Visit</h2>{addr}</div>
      <div><h2>Contact</h2><ul><li><a href="tel:{SITE["phoneIntl"]}">{SITE["phone"]}</a></li>{email}<li><a href="{SITE["instagram"]}" target="_blank" rel="noopener">Instagram {SITE["instagramHandle"]}</a></li><li><a href="/contact/">Contact form</a></li></ul></div>
      <div><h2>Explore</h2><ul>{ex}</ul></div>
      <div><h2>Book</h2><p style="font-size:15px">Video consultation from £15.<br>In person £30.</p>{book("Book a consultation")}</div>
    </div>
    <div class="footer-bottom">
      <span>© 2026 CAVE Clinic</span>
      <nav aria-label="Legal"><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a></nav>
      <span>All treatments are subject to consultation. Results vary.</span>
    </div>
  </div>
</footer>
<div class="sticky-bar"><span>Consultations from £15</span>{book("Book", "btn btn--sm")}</div>
<div class="cursor-preview" aria-hidden="true"><div class="inner"></div></div>
<div class="dialog" id="video-dialog" role="dialog" aria-modal="true" aria-labelledby="video-dialog-title" hidden>
  <h2 class="sr-only" id="video-dialog-title">Clinic film</h2>
  <div class="dialog-inner"><video controls playsinline hidden></video><div class="ph ph--dark"><span>Film to add</span></div></div>
  <button class="dialog-close" type="button" aria-label="Close video"></button>
</div>
<div class="veil" aria-hidden="true"></div>'''

def crumbs(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": URL + p} for i, (n, p) in enumerate([("Home", "/")] + items)]}

def business():
    def loc(l, typ="MedicalBusiness"):
        return {"@type": typ, "name": "CAVE Clinic" if l["id"] == "ivy-mill" else f'CAVE Clinic at {l["name"]}',
                "telephone": SITE["phoneIntl"],
                "address": {"@type": "PostalAddress", "streetAddress": l["street"], "addressLocality": l["locality"].split(",")[-1].strip(),
                            "postalCode": l["postcode"], "addressCountry": "GB"},
                "openingHoursSpecification": [{"@type": "OpeningHoursSpecification", "dayOfWeek": f"https://schema.org/{d}"} for d in l["schemaDays"]]}
    main = loc(LOCS[0])
    main.update({"@context": "https://schema.org", "@id": URL + "/#clinic", "url": URL + "/", "email": SITE["email"],
                 "image": URL + "/assets/og/og-default.jpg", "priceRange": "£15–£700",
                 "description": "Natural-results aesthetics clinic in Manchester, founded by Paris Tyrell.",
                 "sameAs": [SITE["instagram"]], "founder": {"@id": URL + "/paris/#paris"},
                 "areaServed": ["Manchester", "London"],
                 "department": [loc(l) for l in LOCS[1:]],
                 "potentialAction": {"@type": "ReserveAction", "target": BOOK}})
    return main

def person():
    return {"@context": "https://schema.org", "@type": "Person", "@id": URL + "/paris/#paris", "name": "Paris Tyrell",
            "jobTitle": "Founder & aesthetic practitioner", "worksFor": {"@id": URL + "/#clinic"},
            "url": URL + "/paris/", "sameAs": [SITE["instagram"]],
            "description": "Natural-results specialist and founder of CAVE Clinic in Manchester."}

PAGES = []  # (path, title) for sitemap

def page(path, title, desc, body, schema=(), hero=False, intro=False, og="og-default", out=None):
    assert len(title) <= 60, f"Title too long ({len(title)}): {title}"
    assert body.count("<h1") == 1, f"{path} must have exactly one H1"
    full = body + str(schema)
    assert not BANNED.search(full + title + desc), f"Prescription-only medicine name found on {path}"
    PAGES.append((path, title))
    lds = "".join(f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>' for s in schema)
    canon = URL + path
    intro_html = ""
    if intro:
        letters = "".join(f'<span class="l">{c}</span>' for c in "CAVE")
        clinic = "".join(f'<span class="l">{c}</span>' for c in "CLINIC")
        intro_html = f'<div class="intro" hidden aria-hidden="true"><span class="wordmark"><span class="wm-cave">{letters}</span><span class="wm-clinic">{clinic}</span></span></div>'
    doc = f'''<!doctype html>
<html lang="en-GB" class="veil-start">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="website"><meta property="og:site_name" content="CAVE Clinic">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canon}"><meta property="og:image" content="{URL}/assets/og/{og}.jpg">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="The lounge at CAVE Clinic, Manchester">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#FFFFFF">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://api.fontshare.com" crossorigin>
<link rel="preconnect" href="https://cdn.fontshare.com" crossorigin>
<link href="https://api.fontshare.com/v2/css?f[]=boska@400,401,500&f[]=general-sans@400,500,600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/styles.css">
<script>document.documentElement.classList.add("js");</script>
{lds}
</head>
<body class="{"" if hero else "no-hero"}">
{intro_html}
{header(path)}
<main id="main">
{body}
</main>
{footer()}
<script src="/assets/data.js"></script>
<script src="/assets/main.js" defer></script>
</body>
</html>'''
    dest = os.path.join(OUT, out or path.strip("/"), "" if out else "index.html") if not out else os.path.join(OUT, out)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w", encoding="utf-8").write(doc)

# ---------------------------------------------------------------- components
def hero(label, h1, line="", actions="", media="", full=True, cls=""):
    return f'''
<section class="hero {"" if full else "hero--page"} {cls} grain" aria-label="Introduction">
  <div class="hero-media"><div class="settle">{media}</div></div>
  <div class="hero-content"><div class="container">
    <div><span class="label">{label}</span>{h1}{f'<p class="hero-line">{line}</p>' if line else ""}</div>
    <div class="hero-actions">{actions}</div>
  </div></div>
</section>'''

def page_hero(label, h1, line="", extra=""):
    return f'''<section class="page-hero"><div class="container" data-stagger>
<span class="label reveal">{label}</span><h1 class="h1 reveal">{h1}</h1>{f'<p class="reveal">{line}</p>' if line else ""}{extra}</div></section>'''

def result_pair(r, i):
    rev = ""
    if r.get("review"):
        rev = f'''<div class="review">{STARS}<blockquote>“{esc(r["review"])}”</blockquote>
<footer><span class="label">{esc(r["name"])}</span><span class="label">Google review</span></footer></div>'''
    return f'''
<article class="rr reveal" data-cat="{r["cat"]}">
  <div class="ba">
    <div class="ba-layer ba-before">{img_inner(r["before"], f'Before: {r["treatment"]}, consented client image', "Consented result to add · Before")}</div>
    <div class="ba-layer ba-after">{img_inner(r["after"], f'After: {r["treatment"]}, consented client image', "Consented result to add · After")}</div>
    <span class="ba-tag ba-tag--b label">Before</span><span class="ba-tag ba-tag--a label">After</span>
    <span class="ba-line"></span>
    <span class="ba-handle" role="slider" tabindex="0" aria-label="Before and after comparison, {esc(r["treatment"])}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="50"></span>
  </div>
  <div class="rr-cap"><span class="label" style="color:var(--ink)">{esc(r["treatment"])}</span><span class="label">Results vary</span></div>
  {rev}
</article>'''

def results_row(items):
    return f'<div class="results" data-stagger>{"".join(result_pair(r, i) for i, r in enumerate(items))}</div>'

AREAS = [("Lips", "Shape and symmetry, in proportion with the face.", 74, 60.4),
         ("Nose", "A smoother profile, without surgery.", 73, 47),
         ("Cheeks", "Mid-face lift and gentle structure.", 56, 50),
         ("Chin", "Projection that grounds the profile.", 69, 75),
         ("Jaw", "A defined line from ear to chin.", 46, 74)]
PACKS = [("Tweak", "2ml", "£350", False), ("Refine", "3ml", "£450", True), ("Enhance", "4ml", "£550", False), ("Modify", "5ml", "£700", False)]
PROFILE_SVG = '''<svg viewBox="0 0 400 500" aria-hidden="true" focusable="false">
<path d="M212 40 C252 50 270 110 263 165 C261 180 257 189 262 200 C276 225 292 245 300 258 C303 266 296 272 283 272 C277 272 274 278 276 284 C280 292 287 296 283 302 C278 306 272 306 274 311 C280 317 283 325 273 332 C265 338 262 345 268 353 C281 369 279 389 258 397 C236 405 206 404 186 398"/>
<path d="M212 40 C150 28 92 66 84 148 C78 208 98 258 122 292"/>
<path d="M186 398 C176 372 162 340 152 300"/>
<path d="M186 398 C182 426 184 452 190 486"/>
<path d="M122 292 C120 350 114 420 104 486"/>
<path d="M146 214 C136 222 136 246 146 258 C152 264 158 258 156 248"/>
<path d="M232 190 C240 186 250 187 256 192"/>
<path d="M226 176 C236 170 250 170 262 176"/>
<path d="M276 300 L262 302"/>
</svg>'''

def explorer():
    spots = "".join(
        f'<button class="hotspot" type="button" style="left:{x}%;top:{y}%" aria-pressed="false" '
        f'aria-label="{n}: {d}" data-name="{n}" data-desc="{d}"></button>' for n, d, x, y in AREAS)
    stops = "".join(
        f'<button class="scale-stop" type="button" role="radio" aria-checked="{"true" if p else "false"}" tabindex="{0 if p else -1}" data-name="{n} {ml}">'
        f'<span class="nm">{n}</span><span class="ml">{ml} · {pr}</span>{"<span class=pop>Most popular</span>" if p else ""}</button>' for n, ml, pr, p in PACKS)
    return f'''
<div class="explorer reveal">
  <div class="explorer-stage">
    <div class="explorer-figure">{PROFILE_SVG}{spots}</div>
    <div>
      <div class="explorer-info" aria-live="polite"><span class="label">Facial harmony explorer</span><h3 class="h3">Choose your areas</h3><p>Hover or tap a point on the profile.</p></div>
      <div class="areas"><span class="label">Your areas</span><ul aria-live="polite"></ul><p class="note" aria-live="polite"></p></div>
    </div>
  </div>
  <div class="scale">
    <span class="label" id="scale-label">Package</span>
    <div class="scale-track" role="radiogroup" aria-labelledby="scale-label">{stops}</div>
    <p class="scale-msg" aria-live="polite">Refine 3ml: up to 3 areas from lips, nose, cheeks, chin and jaw.</p>
  </div>
  <div class="explorer-cta">{book("Book a consultation", "btn btn--ivory")}<small>Your plan is confirmed at consultation.</small></div>
</div>'''

SECRET_COPY = '''<p>We look at your natural structure, symmetry and proportions. Instead of isolating one feature, we consider how each area works together.</p>
<p>So no one can tell what's been done, only that you look refreshed.</p>'''

def secret_section(h="h2", extra_copy="", title="The CAVE Secret™", label="Signature method"):
    return f'''
<section class="section bg-cocoa grain" id="the-cave-secret" aria-labelledby="secret-h">
  <div class="container secret">
    <div data-stagger>
      <span class="label reveal">{label}</span>
      <{h} class="h2 reveal" id="secret-h">{title}</{h}>
      <div class="reveal" style="margin-top:32px">{SECRET_COPY}{extra_copy}</div>
    </div>
    {explorer()}
  </div>
</section>'''

WALK = [("01", "The arrival", "Sheer curtains, bouclé chairs and a marble table.", "walk-arrival", "Sheer curtains, cream bouclé chairs and a round marble table at the clinic entrance", None),
        ("02", "The lounge", "A chocolate bouclé sofa, candles and quiet.", "walk-lounge", "The lounge with a chocolate bouclé sofa and lit candles", None),
        ("03", "The treatment suite", "A sculptural lounger beneath an arched mirror.", "walk-suite", "The treatment suite with a sculptural cream lounger and an arched mirror", "walk-suite"),
        ("04", "The details", "Brass wall lights, plaster art and the CAVE menu.", "walk-details", "Brass wall lights, plaster artwork and the printed CAVE menu", None)]

def walkthrough():
    frames = ""
    for n, name, line, im, alt, vid in WALK:
        media = video(vid, im, alt, f"Clinic film to add · {name}", dark=False) if vid else img_inner(im, alt, f"Clinic photo to add · {name}")
        play = ""
        if vid:
            play = f'<button class="btn btn--ivory btn--sm walk-play" type="button" data-play="{video_src(vid + "-full") or video_src(vid)}" data-title="The treatment suite">Play with sound</button>'
        frames += f'''
<figure class="walk-frame" tabindex="0" aria-roledescription="slide" aria-label="{n} of 04, {name}" style="margin:0">
  <div class="walk-media"><div class="settle">{media}</div>{play}</div>
  <figcaption class="walk-cap"><span class="label">{n} · {name}</span><p>{line}</p></figcaption>
</figure>'''
    dots = "".join(f'<button type="button" aria-label="Go to frame {i + 1}" aria-current="{"true" if i == 0 else "false"}"></button>' for i in range(4))
    return f'''
<section class="walk" id="step-inside" aria-labelledby="walk-h">
  <div class="container walk-head" data-stagger><span class="label reveal">Step inside</span><h2 class="h2 reveal" id="walk-h">The clinic</h2>
  <p class="reveal" style="margin-top:20px">Use the arrow keys to move between rooms.</p></div>
  <div class="walk-pin"><div class="walk-sticky">
    <div class="walk-track">{frames}</div>
    <div class="walk-progress"><div class="walk-bar"><i></i></div><span class="walk-count" aria-hidden="true">01 / 04</span></div>
    <div class="walk-dots">{dots}</div>
  </div></div>
  <div class="walk-end"></div>
</section>'''

def treatment_rows():
    rows = ""
    for c in TREATS:
        if not c.get("home"):
            continue
        rows += f'''
<a class="row reveal" href="/treatments/#{c["id"]}" data-preview="{("/assets/img/" + find_media(c["image"], [".webp", ".jpg"])) if find_media(c["image"], [".webp", ".jpg"]) else ""}" data-preview-label="{esc(c["home"])}">
  <span class="row-name">{esc(c["home"])}</span><p class="row-desc">{esc(c["homeDesc"])}</p>
  <span class="row-price">{esc(c["from"])}</span><span class="row-arrow" aria-hidden="true"></span>
  <span class="row-thumb">{img(c["image"], "", "")}</span>
</a>'''
    return f'<div class="rows" data-stagger>{rows}</div>'

def team_cards(join_href="", join_title="Joining soon", join_line="A new practitioner joins CAVE soon.", grid=False):
    cards = ""
    for t in TEAM:
        cards += f'''
<article class="team-card reveal">
  {img(t["image"], t["alt"], "Portrait to add · " + t["name"].split()[0], cls="clip")}
  <h3>{esc(t["name"])}</h3><span class="label">{esc(t["role"])}</span>
  <a class="link" href="{t["link"]}">View treatments<span class="sr-only"> by {esc(t["name"])}</span></a>
</article>'''
    link = f'<a class="link" href="{join_href}">Get in touch</a>' if join_href else ""
    cards += f'''
<article class="team-card reveal">
  <div class="media" style="background:var(--boucle)"><div class="ph" aria-hidden="true"><span></span></div></div>
  <h3>{join_title}</h3><span class="label">{join_line}</span>{link}
</article>'''
    return f'<div class="team{" team--grid" if grid else ""}" data-stagger>{cards}</div>'

def quotes():
    items = "".join(f'''<figure class="quote{" is-active" if i == 0 else ""}" style="margin:0" aria-hidden="{"false" if i == 0 else "true"}">
<blockquote>“{esc(r["text"])}”</blockquote>{STARS}<figcaption class="label">{esc(r["name"])}</figcaption></figure>''' for i, r in enumerate(REVIEWS))
    dots = "".join(f'<button type="button" aria-label="Show review {i + 1}" aria-current="{"true" if i == 0 else "false"}">{i + 1:02d}</button>' for i in range(len(REVIEWS)))
    return f'''
<section class="section bg-ivory quotes" aria-labelledby="q-h">
  <div class="container">
    <span class="label reveal">In their words</span><h2 class="sr-only" id="q-h">Client reviews</h2>
    <div class="quote-stage" aria-live="polite">{items}</div>
    <div class="quote-dots">{dots}</div>
  </div>
</section>'''

def event_cards(events):
    return '<div class="cards-3" data-stagger>' + "".join(f'''
<article class="card reveal">
  {img(e["image"], e["alt"], "Event photo to add", cls="clip")}
  <span class="label">{esc(e["date"])}</span><h3>{esc(e["title"])}</h3><p>{esc(e["line"])}</p>
</article>''' for e in events) + "</div>"

def locations_block():
    out = '<p class="today" data-today aria-live="polite"></p>'
    for l in LOCS:
        days = esc(l["daysText"]) + (' <span class="tbc">(days to confirm)</span>' if l["toConfirm"] else "")
        out += f'''
<div class="loc">
  <span class="label">{esc(l["label"])}</span><h3>{esc(l["name"])}</h3>
  <address>{esc(l["street"])}<br>{esc(l["locality"])} {esc(l["postcode"])}</address>
  <p class="days">{days}</p>
  <a class="link" href="{l["maps"]}" target="_blank" rel="noopener">Directions<span class="sr-only"> to {esc(l["name"])} (opens in a new tab)</span></a>
</div>'''
    out += '<p class="find-note">Exclusive dates in London, Bradford, Liverpool and Ireland, announced on Instagram.</p>'
    return out

def findus(h="Find us"):
    return f'''
<section class="section bg-ivory" aria-labelledby="find-h">
  <div class="container findus">
    {img("find-lounge", "The lounge at CAVE Clinic, Ivy Mill, with the chocolate bouclé sofa", "Clinic photo to add · The lounge", cls="clip")}
    <div class="reveal"><span class="label">Visit</span><h2 class="h2" id="find-h" style="margin:20px 0 40px">{h}</h2>{locations_block()}</div>
  </div>
</section>'''

def final_cta(h="Your face isn't the place to find a bargain."):
    return f'''
<section class="section bg-cocoa grain final" aria-labelledby="final-h">
  <div class="final-bg">{img_inner("final-table", "", "", dark=True)}</div>
  <div class="container" data-stagger>
    <h2 class="h2 reveal" id="final-h">{h}</h2>
    <div class="actions reveal">{book("Book a consultation", "btn btn--ivory")}</div>
    <p class="label reveal" style="max-width:none">Video consultation from £15 · In-person £30</p>
  </div>
</section>'''

def founder_split(h_tag="h2"):
    return f'''
<section class="section bg-ivory" aria-labelledby="paris-h">
  <div class="container founder">
    <div class="founder-media">
      {img("paris-portrait", "Portrait of Paris Tyrell, founder of CAVE Clinic, in soft daylight", "Portrait to add · Paris", cls="arch clip")}
      {img("paris-at-work", "Paris Tyrell assessing a client's profile in the treatment suite", "Photo to add · Paris at work", cls="founder-inset clip", attrs='style="--d:300ms"')}
    </div>
    <div data-stagger>
      <span class="label reveal">Founder</span>
      <{h_tag} class="h1 reveal" id="paris-h">Paris Tyrell</{h_tag}>
      <p class="reveal" style="margin-top:32px">{esc(PARIS["excerpt"])}</p>
      <hr class="brass-rule reveal">
      <span class="label reveal">Natural-results specialist</span>
      <div class="actions reveal" style="margin-top:28px"><a class="link" href="/paris/">Meet Paris</a></div>
    </div>
  </div>
</section>'''

# ---------------------------------------------------------------- pages
def home():
    media = video("hero", "hero-poster", "A slow walk past sheer curtains, bouclé chairs and a marble table into the treatment room", "Hero film to add · A slow walk through the clinic")
    body = hero("Manchester · London",
                '<h1 class="display" style="margin-top:20px">Natural results,<br><em>beautifully</em> made.</h1>',
                actions=book("Book a consultation", "btn btn--ivory") + '<a class="link link--light" href="#step-inside">Step inside ↓</a>',
                media=media)
    body += f'''
<section class="section" aria-labelledby="intro-h">
  <div class="container cols">
    <div><span class="label reveal">Est. by Paris Tyrell</span></div>
    <div data-stagger>
      <h2 class="h2 reveal" id="intro-h">Aesthetics isn't about changing yourself. It's about looking your best and preserving what you have.</h2>
      <p class="reveal">Every plan starts with your natural structure, symmetry and proportions.</p>
      <a class="link reveal" href="/paris/">Meet Paris</a>
    </div>
  </div>
</section>'''
    body += walkthrough() + founder_split() + secret_section()
    body += f'''
<section class="section" aria-labelledby="res-h">
  <div class="container">
    <div class="section-head split-head" data-stagger><div><span class="label reveal">Results</span><h2 class="h2 reveal" id="res-h">Subtle, by design.</h2></div><a class="link reveal" href="/results/">All results</a></div>
    {results_row(RESULTS[:3])}
    <p class="note-line">Results vary from person to person.</p>
  </div>
</section>
<section class="section bg-ivory" aria-labelledby="tr-h">
  <div class="container">
    <div class="section-head split-head" data-stagger><div><span class="label reveal">Treatments</span><h2 class="h2 reveal" id="tr-h">Considered, never <em>overdone</em>.</h2></div><a class="link reveal" href="/treatments/">The full menu</a></div>
    {treatment_rows()}
  </div>
</section>
<section class="section" aria-labelledby="team-h">
  <div class="container">
    <div class="section-head" data-stagger><span class="label reveal">The team</span><h2 class="h2 reveal" id="team-h">Hands you can trust.</h2></div>
    {team_cards()}
  </div>
</section>
{quotes()}
<section class="section" aria-labelledby="ev-h">
  <div class="container">
    <div class="section-head" data-stagger><span class="label reveal">Events</span><h2 class="h2 reveal" id="ev-h">More than appointments.</h2></div>
    {event_cards(EVENTS)}
    <div class="actions"><a class="link" href="{SITE["instagram"]}" target="_blank" rel="noopener">Follow {SITE["instagramHandle"]} for the next date</a></div>
  </div>
</section>
{findus()}
{final_cta()}'''
    page("/", "CAVE Clinic | Natural-Looking Aesthetics in Manchester",
         "Natural-results aesthetics in Manchester by Paris Tyrell. Facial balancing, lips, skin boosters and facials. Consultations from £15.",
         body, [business(), person()], hero=True, intro=True)

def treatments():
    cats_nav = [c for c in TREATS if c["id"] != "consultations"]
    bar = "".join(f'<a href="#{c["id"]}">{esc(c["name"])}</a>' for c in cats_nav)
    filt = "".join(f'<button class="filter-btn" type="button" data-value="{v}" aria-pressed="{"true" if v == "all" else "false"}">{t}</button>' for v, t in [("all", "All"), ("paris", "Paris"), ("alix", "Alix")])
    sections = ""
    for c in TREATS:
        if c["id"] == "anti-wrinkle":
            sections += f'''
<section class="menu-cat" id="anti-wrinkle" aria-labelledby="h-anti-wrinkle" data-who="paris">
  <div class="panel reveal" data-who="paris">
    <div><span class="label">Anti-wrinkle injections</span><h2 class="h2" id="h-anti-wrinkle" style="margin:16px 0 16px">Consultation-led.</h2>
    <p style="margin:0">A prescriber consultation is needed before your first treatment.</p></div>
    {book("Book a consultation")}
  </div>
</section>'''
            continue
        rows = ""
        for r in c["rows"]:
            who = r["practitioner"]
            who_txt = " & ".join(w.capitalize() for w in who.split())
            meta = " · ".join(x for x in [r["duration"], f"With {who_txt}"] if x)
            pop = '<span class="tag-pop">Most popular</span>' if r["popular"] else ""
            note = f'<small>{esc(r["note"])}</small>' if r["note"] else ""
            rows += f'''
<div class="mrow reveal" data-who="{who}">
  <div><h3 class="mrow-name" style="font-weight:400">{esc(r["name"])}{pop}</h3><span class="label mrow-meta">{esc(meta)}</span></div>
  <p>{esc(r["desc"])}</p>
  <span class="mrow-price">{esc(r["price"])}{note}</span>
  {book("Book", "link")}
</div>'''
        sections += f'''
<section class="menu-cat" id="{c["id"]}" aria-labelledby="h-{c["id"]}">
  <div class="menu-cat-head reveal"><h2 class="h2" id="h-{c["id"]}">{esc(c["name"])}{" with Alix" if c["id"] == "skin-facials" else ""}</h2><p>{esc(c["intro"])}</p></div>
  <div class="rows" style="border-top:1px solid var(--hair)">{rows}</div>
</section>'''
    body = page_hero("Treatments", "The menu", "Every treatment starts with a consultation, by video or in person.")
    body += f'''
<div class="catbar"><div class="container catbar-inner">
  <nav class="catbar-cats" aria-label="Treatment categories">{bar}</nav>
  <div class="filters" role="group" aria-label="Filter by practitioner" data-filter-group="menu-list" data-filter-attr="data-who" data-param="practitioner"><span class="label" aria-hidden="true">With</span>{filt}</div>
</div></div>
<p class="sr-only" aria-live="polite" data-filter-live></p>
<div class="section" style="padding-top:clamp(72px,8vw,120px)"><div class="container" id="menu-list">{sections}
<p class="note-line">All treatments are subject to consultation. Results vary.</p></div></div>
{final_cta()}'''
    services = []
    for c in TREATS:
        offers = [{"@type": "Offer", "name": r["name"], "price": r["value"], "priceCurrency": "GBP", "url": BOOK}
                  for r in c["rows"] if r["value"]]
        if offers:
            services.append({"@context": "https://schema.org", "@type": "Service", "name": c["name"], "serviceType": c["name"],
                             "provider": {"@id": URL + "/#clinic"}, "areaServed": "Manchester",
                             "offers": offers})
    page("/treatments/", "Treatments & Prices | CAVE Clinic Manchester",
         "The CAVE Clinic menu: facial balancing from £350, lips from £130, skin boosters, facials with Alix and body contouring.",
         body, services + [crumbs([("Treatments", "/treatments/")])])

FAQ = [("Who is facial balancing for?",
        "It's for anyone who wants a refreshed, balanced look without obvious change. We assess your face as a whole first. [Answer to confirm with Paris]"),
       ("How many ml do I need?",
        "Most clients choose Refine, 3ml. Your plan and amount are confirmed at consultation, never before. [Answer to confirm with Paris]"),
       ("How long do results last?",
        "It depends on the treatment and the area. Generally, results last between 6 and 18 months. [Answer to confirm with Paris]"),
       ("What happens at the consultation?",
        "We talk about what's bothering you and why. Then we map your face and agree a plan together. [Answer to confirm with Paris]")]

def cave_secret():
    media = img_inner("secret-hero", "Close-up of a client's side profile in soft daylight, showing balanced proportions", "Photo to add · Profile close-up", dark=True, eager=True)
    body = hero("Signature method", '<h1 class="h1" style="margin-top:20px">The CAVE Secret™</h1>', "Our signature facial balancing method.",
                actions=book("Book a consultation", "btn btn--ivory"), media=media, full=False)
    body += f'''
<section class="section" aria-labelledby="short-h">
  <div class="container cols">
    <div><span class="label reveal">In short</span></div>
    <div data-stagger>
      <h2 class="h2 reveal" id="short-h">One face, planned as a whole.</h2>
      <p class="reveal lead">We look at your natural structure, symmetry and proportions. We use the golden ratio as a guide, not a rule. Instead of isolating one feature, we consider how each area works together. So no one can tell what's been done, only that you look refreshed.</p>
    </div>
  </div>
</section>
{secret_section(title="Explore your plan.", label="Facial harmony explorer")}
<section class="section" aria-labelledby="how-h">
  <div class="container">
    <div class="section-head" data-stagger><span class="label reveal">How it works</span><h2 class="h2 reveal" id="how-h">Four quiet steps.</h2></div>
    <ol class="steps" data-stagger>
      <li class="reveal"><h3>Consultation</h3><p>By video or in person. We start with what's bothering you, and why.</p></li>
      <li class="reveal"><h3>Your facial map</h3><p>We assess structure, symmetry and proportion, and agree up to 3 areas.</p></li>
      <li class="reveal"><h3>Treatment</h3><p>Paris treats each area as part of one plan, never in isolation.</p></li>
      <li class="reveal"><h3>Review</h3><p>We check in once everything has settled, and fine-tune if needed.</p></li>
    </ol>
  </div>
</section>
<section class="section bg-ivory" aria-labelledby="res-h">
  <div class="container">
    <div class="section-head" data-stagger><span class="label reveal">Results</span><h2 class="h2 reveal" id="res-h">Refreshed, not changed.</h2></div>
    {results_row([r for r in RESULTS if r["cat"] in ("facial-balancing", "profile", "lips")][:3])}
    <p class="note-line">Results vary from person to person.</p>
  </div>
</section>
<section class="section" aria-labelledby="faq-h">
  <div class="container cols">
    <div><span class="label reveal">Questions</span><h2 class="h2 reveal" id="faq-h" style="margin-top:20px">Good to know.</h2></div>
    <div class="faq reveal">{"".join(f'<details><summary>{q}</summary><div class="ans"><p>{a}</p></div></details>' for q, a in FAQ)}</div>
  </div>
</section>
{final_cta()}'''
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"\s*\[.*?\]", "", a)}} for q, a in FAQ]}
    fb = next(c for c in TREATS if c["id"] == "facial-balancing")
    svc = {"@context": "https://schema.org", "@type": "Service", "name": "The CAVE Secret™ facial balancing", "serviceType": "Facial balancing",
           "provider": {"@id": URL + "/#clinic"}, "areaServed": "Manchester",
           "offers": [{"@type": "Offer", "name": r["name"], "price": r["value"], "priceCurrency": "GBP", "url": BOOK} for r in fb["rows"] if r["value"]]}
    page("/the-cave-secret/", "Facial Balancing in Manchester | The CAVE Secret™",
         "The CAVE Secret™ is our signature facial balancing method. A whole-face plan from £350, built on structure, symmetry and proportion.",
         body, [svc, faq, crumbs([("The CAVE Secret", "/the-cave-secret/")])], hero=True)

def clinic():
    media = video("tour", "tour-poster", "A slow walkthrough of CAVE Clinic, from the entrance to the treatment suite", "Clinic tour film to add")
    body = hero("The clinic", '<h1 class="h1" style="margin-top:20px">Step inside.</h1>', "A quiet, light-filled space at Ivy Mill, Failsworth.",
                actions=f'<button class="btn btn--ivory" type="button" data-play="{video_src("tour-full") or video_src("tour")}" data-title="The clinic tour">Play the tour</button>' + book("Book", "link link--light"),
                media=media, full=False)
    rooms = ""
    for n, name, line, im, alt, vid in WALK:
        rooms += f'''
<div class="room">
  {img(im, alt, "Clinic photo to add · " + name, cls="clip")}
  <div class="reveal"><span class="label">{n}</span><h2 class="h2">{name}</h2><p>{line}</p></div>
</div>'''
    body += f'''
<section class="section" aria-label="Room by room">
  <div class="container"><div class="section-head reveal"><span class="label">Room by room</span></div>{rooms}</div>
</section>
<section class="section bg-ivory" aria-labelledby="care-h">
  <div class="container cols">
    <div><span class="label reveal">Care and hygiene</span></div>
    <div data-stagger><h2 class="h2 reveal" id="care-h">Spotless, always.</h2>
    <p class="reveal">Every room is cleaned and reset between clients. Single-use items are used once and safely disposed of. [Paragraph to confirm with Paris]</p></div>
  </div>
</section>
<section class="section" aria-labelledby="find-h">
  <div class="container findus">
    {img("clinic-entrance", "The entrance to CAVE Clinic on the second floor of Ivy Mill", "Clinic photo to add · The entrance", cls="clip")}
    <div class="reveal"><span class="label">Visit</span><h2 class="h2" id="find-h" style="margin:20px 0 40px">Two places in Manchester.</h2>{locations_block()}</div>
  </div>
</section>
{final_cta()}'''
    page("/the-clinic/", "The Clinic | CAVE Clinic, Ivy Mill, Manchester",
         "Step inside CAVE Clinic at Ivy Mill, Failsworth: the arrival, the lounge, the treatment suite and the details. Plus our city centre room.",
         body, [business(), crumbs([("The clinic", "/the-clinic/")])], hero=True)

def paris_page():
    story = "".join(f'<p class="reveal">{esc(p)}</p>' for p in PARIS["story"])
    creds = "".join(f'<li><span>{esc(a)}</span><span>{esc(b)}</span></li>' for a, b in PARIS["credentials"])
    strip = "".join(img(f"paris-work-{i}", a, "Photo to add · Paris at work", cls="clip") for i, a in enumerate(
        ["Paris Tyrell mapping a client's profile", "Paris preparing the treatment suite", "Paris in consultation at the marble table"], 1))
    body = f'''
<section class="page-hero" style="padding-bottom:0"><div class="container founder" style="align-items:end">
  <div class="founder-media" style="padding:0">{img("paris-portrait", "Portrait of Paris Tyrell, founder of CAVE Clinic, in soft daylight", "Portrait to add · Paris", cls="arch clip", eager=True)}</div>
  <div data-stagger><span class="label reveal">Founder · Natural-results specialist</span><h1 class="display reveal">Paris<br>Tyrell</h1></div>
</div></section>
<section class="section" aria-labelledby="story-h">
  <div class="container cols">
    <div><span class="label reveal" id="story-h">In her own words</span></div>
    <div class="story" data-stagger>{story}</div>
  </div>
</section>
<section class="section bg-ivory" aria-label="Pull quote">
  <div class="container cols"><div></div><blockquote class="pull reveal">“Aesthetics isn't about changing <em>yourself</em>.”</blockquote></div>
</section>
<section class="section" aria-labelledby="cred-h">
  <div class="container cols">
    <div><span class="label reveal">Credentials</span><h2 class="h2 reveal" id="cred-h" style="margin-top:20px">Training and awards.</h2></div>
    <ul class="list reveal">{creds}</ul>
  </div>
</section>
<section class="section" style="padding-top:0" aria-label="Paris at work">
  <div class="container"><div class="strip-3" data-stagger>{strip}</div>
  <div class="actions"><a class="link" href="/academy/">Learn with Paris at the Academy</a><a class="link" href="/the-cave-secret/">The CAVE Secret™</a></div></div>
</section>
{final_cta()}'''
    page("/paris/", "Paris Tyrell | Founder of CAVE Clinic Manchester",
         "Meet Paris Tyrell, natural-results specialist and founder of CAVE Clinic in Manchester. Her story, her method and her training.",
         body, [person(), crumbs([("Paris", "/paris/")])])

def team_page():
    body = page_hero("The team", "Hands you can trust.", "A small team, trained to treat your face as a whole.")
    body += f'''<section class="section" style="padding-top:0"><div class="container"><h2 class="sr-only">Our practitioners</h2>{team_cards("/contact/", "Interested in joining CAVE?", "Practitioners and skin specialists")}</div></section>{final_cta()}'''
    page("/team/", "Our Team | CAVE Clinic Manchester",
         "Meet the CAVE Clinic team: Paris Tyrell, founder and aesthetic practitioner, and Alix, skin specialist for facials and peels.",
         body, [crumbs([("The team", "/team/")])])

def results_page():
    filt = "".join(f'<button class="filter-btn" type="button" data-value="{v}" aria-pressed="{"true" if v == "all" else "false"}">{t}</button>'
                   for v, t in [("all", "All"), ("facial-balancing", "Facial balancing"), ("lips", "Lips"), ("profile", "Profile"), ("skin", "Skin")])
    body = page_hero("Results", "Subtle, by design.", "Consented client results only. Every face is different, and results vary.")
    body += f'''
<section class="section" style="padding-top:0"><div class="container">
  <div class="filters" role="group" aria-label="Filter results" data-filter-group="gallery" style="margin-bottom:56px">{filt}</div>
  <p class="sr-only" aria-live="polite" data-filter-live></p>
  <div id="gallery">{results_row(RESULTS)}</div>
  <p class="note-line">Results vary from person to person. Images shared with client consent.</p>
</div></section>
{quotes()}
{final_cta()}'''
    page("/results/", "Results | Natural Aesthetics, CAVE Clinic Manchester",
         "Consented before and after results from CAVE Clinic: facial balancing, lips, profile and skin. Paired with our clients' own reviews.",
         body, [crumbs([("Results", "/results/")])])

def events_page():
    up = [e for e in EVENTS if not e["past"]]
    past = [e for e in EVENTS if e["past"]]
    past_html = f'''<section class="section bg-ivory"><div class="container"><div class="section-head"><span class="label">Past events</span><h2 class="h2" style="margin-top:20px">Moments we've shared.</h2></div>{event_cards(past)}</div></section>''' if past else ""
    body = page_hero("Events", "More than appointments.", "Evenings, mornings and treatment days, announced on Instagram first.")
    body += f'''<section class="section" style="padding-top:0"><div class="container"><div class="section-head"><h2 class="label">Upcoming</h2></div>{event_cards(up)}
<div class="actions"><a class="link" href="{SITE["instagram"]}" target="_blank" rel="noopener">Follow {SITE["instagramHandle"]} for dates</a></div></div></section>{past_html}{final_cta()}'''
    page("/events/", "Events | CAVE Clinic Manchester",
         "Galentine's evenings, wellness mornings and exclusive treatment days from CAVE Clinic. Follow @caveclinic for dates.",
         body, [crumbs([("Events", "/events/")])])

def consent_box(text):
    return f'<label class="check"><input type="checkbox" name="consent" required> <span>{text}</span></label>'

def academy_page():
    body = page_hero("Learn with CAVE", "CAVE Academy", "Learn the natural-results approach, from the ebook to 1-1 training with Paris.")
    body += f'''
<section class="section" style="padding-top:0"><div class="container">
  <div class="offer reveal"><div><span class="label">The ebook</span><h2 class="h3" style="font-size:32px;font-weight:400;margin:10px 0">The viral CAVE ebook</h2><p>The guide clients and practitioners keep asking for. [Price and summary to confirm]</p></div>
  <a class="btn" href="https://learn.caveclinic.uk/" target="_blank" rel="noopener">Buy the ebook<span class="sr-only"> (opens in a new tab)</span></a></div>
  <div class="offer reveal" style="border-bottom:1px solid var(--hair)"><div><span class="label">1-1 training</span><h2 class="h3" style="font-size:32px;font-weight:400;margin:10px 0">One student a month.</h2><p>Only one student a month joins the CAVE Training Academy. Join the waitlist below.</p></div>
  <a class="link" href="#waitlist">Join the waitlist</a></div>
</div></section>
<section class="section bg-ivory" id="waitlist" aria-labelledby="wl-h" style="scroll-margin-top:72px">
  <div class="container split">
    <div class="reveal"><span class="label">Waitlist</span><h2 class="h2" id="wl-h" style="margin-top:20px">Join the waitlist.</h2><p style="margin-top:24px">We'll be in touch when a place opens.</p></div>
    <form class="form reveal" data-form action="{SITE["formAction"]}" method="post" novalidate data-success="Thank you. You're on the waitlist, and we'll be in touch.">
      <input type="hidden" name="form" value="Academy waitlist">
      <div class="two"><div class="field"><label class="label" for="wl-name">Name</label><input id="wl-name" name="name" autocomplete="name" required></div>
      <div class="field"><label class="label" for="wl-email">Email</label><input id="wl-email" name="email" type="email" autocomplete="email" required></div></div>
      <div class="field"><label class="label" for="wl-exp">Experience</label><select id="wl-exp" name="experience" required><option value="">Choose one</option><option>New to aesthetics</option><option>Qualified, under 1 year</option><option>Qualified, 1 to 3 years</option><option>Qualified, 3 years or more</option></select></div>
      {consent_box('I agree to CAVE Clinic storing my details to contact me about the Academy, in line with UK GDPR and the <a href="/privacy/" style="text-decoration:underline">privacy policy</a>.')}
      <div><button class="btn" type="submit">Join the waitlist</button></div>
      <p class="form-msg" role="status" aria-live="polite"></p>
    </form>
  </div>
</section>'''
    page("/academy/", "CAVE Academy | Aesthetics Training in Manchester",
         "Learn with Paris Tyrell. The CAVE ebook and 1-1 aesthetics training, with one student accepted each month. Join the waitlist.",
         body, [crumbs([("Academy", "/academy/")])])

def contact_page():
    body = page_hero("Contact", "Get in touch.", "Call, message or send the form. For treatment advice, a video consultation is best.")
    body += f'''
<section class="section" style="padding-top:0"><div class="container split">
  <div class="reveal">
    <h2 class="sr-only">Ways to reach us</h2><ul class="contact-list">
      <li><span class="label">Phone</span><br><a href="tel:{SITE["phoneIntl"]}">{SITE["phone"]}</a></li>
      <li><span class="label">WhatsApp</span><br><a href="{SITE["whatsapp"]}" target="_blank" rel="noopener">Message us</a></li>
      <li><span class="label">Email</span><br><a href="mailto:{SITE["email"]}" style="font-size:22px">{SITE["email"]}</a></li>
      <li><span class="label">Instagram</span><br><a href="{SITE["instagram"]}" target="_blank" rel="noopener">{SITE["instagramHandle"]}</a></li>
    </ul>
    <div style="margin-top:48px">{locations_block()}</div>
  </div>
  <form class="form reveal" data-form action="{SITE["formAction"]}" method="post" novalidate data-success="Thank you. We'll reply as soon as we can.">
    <input type="hidden" name="form" value="Contact">
    <div class="two"><div class="field"><label class="label" for="c-name">Name</label><input id="c-name" name="name" autocomplete="name" required></div>
    <div class="field"><label class="label" for="c-email">Email</label><input id="c-email" name="email" type="email" autocomplete="email" required></div></div>
    <div class="two"><div class="field"><label class="label" for="c-phone">Phone</label><input id="c-phone" name="phone" type="tel" autocomplete="tel"></div>
    <div class="field"><label class="label" for="c-t">Treatment of interest</label><select id="c-t" name="treatment"><option value="">Choose one</option>{"".join(f"<option>{esc(c['name'])}</option>" for c in TREATS)}<option>Academy</option><option>Joining the team</option><option>Something else</option></select></div></div>
    <div class="field"><label class="label" for="c-msg">Message</label><textarea id="c-msg" name="message" required></textarea></div>
    {consent_box('I agree to CAVE Clinic storing my details to reply to my enquiry, in line with UK GDPR and the <a href="/privacy/" style="text-decoration:underline">privacy policy</a>.')}
    <div><button class="btn" type="submit">Send message</button></div>
    <p class="form-msg" role="status" aria-live="polite"></p>
  </form>
</div></section>'''
    page("/contact/", "Contact | CAVE Clinic Manchester",
         "Contact CAVE Clinic by phone, WhatsApp, email or form. Clinics at Ivy Mill, Failsworth and John Dalton Street, Manchester.",
         body, [business(), crumbs([("Contact", "/contact/")])])

# ---------------------------------------------------------------- journal
def md(text):
    def inline(s):
        s = esc(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
        return s
    out, items = [], []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.strip().split("\n")
        if all(l.startswith("- ") for l in lines):
            out.append("<ul>" + "".join(f"<li>{inline(l[2:])}</li>" for l in lines) + "</ul>")
        elif block.startswith("## "):
            out.append(f"<h2>{inline(block[3:])}</h2>")
        else:
            out.append(f"<p>{inline(' '.join(lines))}</p>")
    return "\n".join(out)

def load_posts():
    posts = []
    for f in glob.glob(os.path.join(ROOT, "data", "journal", "*.md")):
        raw = open(f, encoding="utf-8").read()
        head, body = raw.split("\n---\n", 1)
        meta = dict(l.split(": ", 1) for l in head.strip().split("\n"))
        meta["slug"] = os.path.basename(f)[:-3]
        meta["body"] = body
        posts.append(meta)
    return sorted(posts, key=lambda p: p["date"], reverse=True)

def nice_date(d):
    return date.fromisoformat(d).strftime("%-d %B %Y")

def post_card(p, h="h3"):
    return f'''<a class="card reveal" href="/journal/{p["slug"]}/">{img(p["image"], p["alt"], "Journal photo to add", cls="clip")}
<span class="label">{esc(p["category"])} · {nice_date(p["date"])}</span><{h}>{esc(p["title"])}</{h}><p>{esc(p["summary"])}</p></a>'''

def journal():
    posts = load_posts()
    lead, rest = posts[0], posts[1:]
    body = page_hero("Journal", "Notes from CAVE", "Honest thoughts on aesthetics, skin and running a clinic, from Paris.")
    body += f'''
<section class="section" style="padding-top:0"><div class="container">
  <a class="lead-post reveal" href="/journal/{lead["slug"]}/">{img(lead["image"], lead["alt"], "Journal photo to add", cls="clip")}
  <div><span class="label">Latest · {esc(lead["category"])} · {nice_date(lead["date"])}</span><h2>{esc(lead["title"])}</h2><p>{esc(lead["summary"])}</p><span class="link">Read</span></div></a>
  <div class="cards-2" data-stagger>{"".join(post_card(p) for p in rest)}</div>
</div></section>'''
    page("/journal/", "Journal | CAVE Clinic Manchester",
         "The CAVE Clinic journal by Paris Tyrell: facial balancing, skin, ethics in aesthetics and life behind the scenes.",
         body, [crumbs([("Journal", "/journal/")])])
    for p in posts:
        related = [x for x in posts if x["slug"] != p["slug"]][:2]
        title = p["title"] if len(p["title"]) <= 46 else p["title"].split(":")[0]
        title = f"{title} | CAVE Clinic" if len(title) <= 46 else title[:60]
        body = f'''
<article>
  <header class="page-hero" style="padding-bottom:0"><div class="article" data-stagger>
    <span class="label reveal">{esc(p["category"])} · {nice_date(p["date"])} · Paris Tyrell</span>
    <h1 class="h2 reveal" style="margin-top:20px">{esc(p["title"])}</h1>
  </div></header>
  <div class="container"><div class="article-wide">{img(p["image"], p["alt"], "Journal photo to add", cls="clip ratio-32")}</div></div>
  <div class="container"><div class="article reveal">{md(p["body"])}
    <div class="actions">{book("Book a consultation")}<a class="link" href="{SITE["instagram"]}" target="_blank" rel="noopener">DM {SITE["instagramHandle"]}</a></div>
  </div></div>
</article>
<section class="section bg-ivory" aria-labelledby="rel-h"><div class="container">
  <div class="section-head"><span class="label">Keep reading</span><h2 class="h2" id="rel-h" style="margin-top:20px">Related notes.</h2></div>
  <div class="cards-2" data-stagger>{"".join(post_card(x) for x in related)}</div>
</div></section>'''
        art = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"], "datePublished": p["date"],
               "author": {"@id": URL + "/paris/#paris", "@type": "Person", "name": "Paris Tyrell"},
               "publisher": {"@id": URL + "/#clinic"}, "mainEntityOfPage": URL + f"/journal/{p['slug']}/",
               "image": URL + "/assets/og/og-default.jpg", "description": p["summary"]}
        page(f"/journal/{p['slug']}/", title, p["summary"], body,
             [art, crumbs([("Journal", "/journal/"), (p["title"], f"/journal/{p['slug']}/")])])

def simple(path, label, h1, text, title, desc):
    body = page_hero(label, h1, text) + '<section class="section" style="padding-top:0"><div class="container"><p>[Full text to add, reviewed by your legal adviser.]</p></div></section>'
    page(path, title, desc, body, [crumbs([(h1, path)])])

def notfound():
    media = img_inner("find-lounge", "The lounge at CAVE Clinic", "Clinic photo to add · The lounge", dark=True, eager=True)
    body = hero("404", '<h1 class="h1" style="margin-top:20px">This room doesn\'t exist.</h1>', "The page may have moved, or the link may be old.",
                actions='<a class="btn btn--ivory" href="/">Back to the clinic</a>', media=media, full=True, cls="notfound")
    PAGES_BEFORE = len(PAGES)
    page("/404.html", "Page not found | CAVE Clinic", "This page doesn't exist. Head back to CAVE Clinic.", body, [], hero=True, out="404.html")
    PAGES.pop()  # keep 404 out of the sitemap

# ---------------------------------------------------------------- assets & SEO files
def assets():
    a = os.path.join(OUT, "assets")
    os.makedirs(os.path.join(a, "img"), exist_ok=True)
    os.makedirs(os.path.join(a, "og"), exist_ok=True)
    shutil.copy(os.path.join(ROOT, "src", "styles.css"), a)
    shutil.copy(os.path.join(ROOT, "src", "main.js"), a)
    for f in glob.glob(os.path.join(IMG_DIR, "*")):
        if not f.endswith(".md"):
            shutil.copy(f, os.path.join(a, "img"))
    for f in glob.glob(os.path.join(ROOT, "src", "og", "*")):
        shutil.copy(f, os.path.join(a, "og"))
    open(os.path.join(a, "data.js"), "w").write("window.CAVE_LOCATIONS = " + json.dumps(
        [{"id": l["id"], "days": l["days"], "today": l["today"]} for l in LOCS]) + ";\n")
    open(os.path.join(a, "favicon.svg"), "w").write(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="#F6F3EE"/>'
        '<text x="32" y="44" text-anchor="middle" font-family="Georgia,serif" font-size="36" fill="#161412">C</text></svg>')

def seo_files():
    today = date.today().isoformat()
    urls = "".join(f"<url><loc>{URL}{p}</loc><lastmod>{today}</lastmod></url>" for p, _ in PAGES if p not in ("/privacy/", "/terms/"))
    open(os.path.join(OUT, "sitemap.xml"), "w").write(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    open(os.path.join(OUT, "robots.txt"), "w").write(f"""User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

Sitemap: {URL}/sitemap.xml
""")
    t_lines = []
    for c in TREATS:
        if c["id"] == "anti-wrinkle":
            t_lines.append("- Anti-wrinkle injections: consultation-led. A prescriber consultation is needed before your first treatment.")
            continue
        t_lines.append(f"- {c['name']}: " + "; ".join(f"{r['name']} {r['price']}" for r in c["rows"]))
    locs = "\n".join(f"- {l['label']}: {l['name']}, {l['street']}, {l['locality']} {l['postcode']}. Open {l['daysText']}." for l in LOCS)
    posts = "\n".join(f"- [{p['title']}]({URL}/journal/{p['slug']}/): {p['summary']}" for p in load_posts())
    open(os.path.join(OUT, "llms.txt"), "w").write(f"""# CAVE Clinic

> Natural-results aesthetics clinic in Manchester, UK, founded by Paris Tyrell. Known for The CAVE Secret™, a whole-face facial balancing method. Every treatment starts with a consultation (video £15, in person £30).

## Key facts
- Founder: Paris Tyrell, natural-results specialist.
- Team: Paris Tyrell (founder & aesthetic practitioner); Alix (skin specialist, facials and peels).
- Phone: {SITE['phone']}. Email: {SITE['email']}. Instagram: {SITE['instagramHandle']}.
- Booking: {BOOK}
- Exclusive dates in London, Bradford, Liverpool and Ireland, announced on Instagram.

## Locations
{locs}

## Treatments and prices
{chr(10).join(t_lines)}
All treatments are subject to consultation. Results vary.

## Pages
- [Treatments]({URL}/treatments/): full menu and prices
- [The CAVE Secret™]({URL}/the-cave-secret/): signature facial balancing method, packages and FAQs
- [The clinic]({URL}/the-clinic/): rooms, hygiene and locations
- [Paris Tyrell]({URL}/paris/): founder story
- [Results]({URL}/results/): consented before and after results
- [Academy]({URL}/academy/): ebook and 1-1 training
- [Contact]({URL}/contact/)

## Journal
{posts}
""")

def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    assets()
    home(); treatments(); cave_secret(); clinic(); paris_page(); team_page(); results_page()
    events_page(); academy_page(); contact_page(); journal()
    simple("/privacy/", "Privacy", "Privacy policy", "How we look after your personal data under UK GDPR.", "Privacy Policy | CAVE Clinic", "How CAVE Clinic collects, uses and protects your personal data under UK GDPR.")
    simple("/terms/", "Terms", "Terms", "Booking, deposits, cancellations and aftercare.", "Terms | CAVE Clinic", "CAVE Clinic booking terms, cancellations and treatment conditions.")
    notfound()
    seo_files()
    print(f"Built {len(PAGES) + 1} pages into {OUT}")
    for p, t in PAGES:
        print(f"  {len(t):>2}  {p:<55} {t}")

if __name__ == "__main__":
    main()
