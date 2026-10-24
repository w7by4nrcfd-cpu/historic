"""يولّد صفحة HTML ثابتة لكل موضوع (لمحركات البحث ومعاينة المشاركة) + فهرس + sitemap.
التشغيل: python3 tools/build_pages.py  (يُشغَّل تلقائيًا في GitHub Actions قبل النشر)
"""
import json, html, os, re, shutil, datetime

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist')
BASE_URL = 'https://w7by4nrcfd-cpu.github.io/historic/'
TODAY = datetime.date.today().isoformat()
TYPES = {'civilization': 'حضارة ودولة', 'city': 'مدينة', 'person': 'شخصية', 'event': 'حدث', 'science': 'علوم واكتشافات'}
esc = lambda s: html.escape(str(s or ''), quote=True)

d = json.load(open(os.path.join(ROOT, 'content.json'), encoding='utf-8'))
civs = d['civilizations']
items = civs + d['entries']
byid = {x['id']: x for x in items}
shell = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()


def civ_of(x):
    if x['type'] == 'civilization':
        return x
    for c in civs:
        if c['cityId'] == x['id'] or any(p['id'] == x['id'] for p in c['people']) or any(e['id'] == x['id'] for e in c['events']):
            return c
    for c in civs:
        if c['id'] in (x.get('relatedIds') or []):
            return c
    return None


def period(x):
    return x.get('period') or x.get('dateLabel') or ''


def page(x):
    c = civ_of(x)
    url = f"{BASE_URL}t/{x['id']}/"
    tag = ''
    if x['type'] == 'event' and x.get('year') is not None:
        y = x['year']; tag = f'{-y} ق.م' if y < 0 else f'{y} م'
    elif x['type'] in ('person', 'civilization', 'city') and period(x) and len(period(x)) <= 24:
        tag = period(x)
    title = f"{x['title']} ({tag}) | أطلس" if tag and tag not in x['title'] else f"{x['title']} | أطلس"
    desc = x['summary']
    if len(desc) < 70:
        extra = next((s['text'] for s in x.get('sections', []) if s['text'] != desc), '')
        desc = (desc + ' ' + extra).strip()
    if len(desc) > 160:
        cut = desc[:158]
        i = max(cut.rfind('. '), cut.rfind('، '))
        desc = cut[:i + 1] if i > 90 else cut[:cut.rfind(' ')] + '…'
        if desc.endswith('،'):
            desc = desc[:-1] + '…'
    img = (x.get('image') or (c or {}).get('image') or {}).get('src') or BASE_URL + 'assets/og.jpg'
    related = [byid[r] for r in (x.get('relatedIds') or ([x['cityId']] if x['type'] == 'civilization' else [])) if r in byid]
    if x['type'] == 'civilization':
        related += [byid[e['id']] for e in x['events'] if e['id'] in byid] + [byid[p['id']] for p in x['people'] if p['id'] in byid]
    if c and c['id'] != x['id']:
        related.insert(0, c)
    seen, rel = set(), []
    for r in related:
        if r['id'] not in seen and r['id'] != x['id']:
            seen.add(r['id']); rel.append(r)
    mid = f'<a href="t/{esc(c["id"])}/">{esc(c["title"])}</a> / ' if c and c['id'] != x['id'] else ''
    body = [f'<div class="container page-head"><div class="breadcrumb"><a href="#/">الرئيسية</a> / {mid}{esc(x["title"])}</div>',
            f'<div class="eyebrow">{esc(TYPES.get(x["type"], ""))}</div><h1>{esc(x["title"])}</h1><p>{esc(x["summary"])}</p></div>',
            '<div class="container section" style="padding-top:0"><article class="article-text">']
    if x.get('image'):
        body.append(f'<figure class="photo"><img src="{esc(x["image"]["src"])}" alt="{esc(x["image"]["caption"])}" loading="lazy"><figcaption>{esc(x["image"]["caption"])} · {esc(x["image"]["author"])} / {esc(x["image"]["license"])}</figcaption></figure>')
    for s in x.get('sections', []):
        if s['text'] != x['summary']:
            body.append(f'<section><h2>{esc(s["title"])}</h2><p>{esc(s["text"])}</p></section>')
    if period(x):
        body.append(f'<p class="note-small">الفترة: {esc(period(x))}</p>')
    if rel:
        body.append('<section><h2>اقرأ أيضًا</h2><ul>' + ''.join(f'<li><a href="t/{esc(r["id"])}/">{esc(r["title"])}</a></li>' for r in rel[:8]) + '</ul></section>')
    body.append('<p><a class="primary" href="#/topic/' + esc(x['id']) + '">افتح الموضوع في أطلس ←</a> <a class="text-link" href="t/">فهرس كل الموضوعات</a></p></article></div>')
    about = {'person': 'Person', 'city': 'Place', 'event': 'Event', 'civilization': 'Organization'}.get(x['type'], 'Thing')
    org = {'@type': 'Organization', 'name': 'أطلس', 'url': BASE_URL}
    ld = {'@context': 'https://schema.org', '@type': 'Article', 'headline': x['title'], 'description': desc, 'inLanguage': 'ar',
          'image': img, 'url': url, 'mainEntityOfPage': url, 'dateModified': TODAY, 'author': org, 'publisher': org,
          'isPartOf': {'@type': 'WebSite', 'name': 'أطلس', 'url': BASE_URL},
          'about': {'@type': about, 'name': x['title']}}
    crumbs = [('الرئيسية', BASE_URL)] + ([(c['title'], f"{BASE_URL}t/{c['id']}/")] if c and c['id'] != x['id'] else []) + [(x['title'], url)]
    bc = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u} for i, (n, u) in enumerate(crumbs)]}
    head = (f'<base href="../../"><link rel="canonical" href="{url}">'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
            f'<script type="application/ld+json">{json.dumps(bc, ensure_ascii=False)}</script>'
            '<meta property="og:type" content="article">'
            f'<script>window.__TOPIC={json.dumps(x["id"])}</script>')
    return render(title, desc, url, img, head, ''.join(body))


def render(title, desc, url, img, extra_head, main_html):
    h = re.sub(r'<link rel="canonical"[^>]*>', '', shell)
    h = re.sub(r'<title>.*?</title>', f'<title>{esc(title)}</title>', h, count=1)
    h = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{esc(desc)}">', h, count=1)
    h = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{esc(title)}">', h, count=1)
    h = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{esc(desc)}">', h, count=1)
    h = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{esc(url)}">', h, count=1)
    h = re.sub(r'<meta property="og:image" content="[^"]*">', f'<meta property="og:image" content="{esc(img)}">', h, count=1)
    if 'og:type" content="article"' in extra_head:
        h = h.replace('<meta property="og:type" content="website">', '', 1)
    h = h.replace('<meta charset="utf-8">', '<meta charset="utf-8">' + extra_head, 1)
    h = re.sub(r'<main id="main" tabindex="-1">.*?</main>', f'<main id="main" tabindex="-1">{main_html}</main>', h, count=1, flags=re.S)
    return h


out = os.path.join(ROOT, 't')
if os.path.isdir(out):
    shutil.rmtree(out)
os.makedirs(out)
for x in items:
    p = os.path.join(out, x['id'])
    os.makedirs(p)
    open(os.path.join(p, 'index.html'), 'w', encoding='utf-8').write(page(x))

# فهرس الموضوعات
groups = []
for c in civs:
    members = [c] + [e for e in d['entries'] if (civ_of(e) or {}).get('id') == c['id']]
    groups.append(f'<section><h2><a href="t/{esc(c["id"])}/">{esc(c["title"])}</a></h2><ul>' + ''.join(
        f'<li><a href="t/{esc(m["id"])}/">{esc(m["title"])}</a> <small>{esc(TYPES.get(m["type"], ""))}</small></li>' for m in members[1:]) + '</ul></section>')
others = [e for e in d['entries'] if not civ_of(e)]
if others:
    groups.append('<section><h2>موضوعات أخرى</h2><ul>' + ''.join(f'<li><a href="t/{esc(m["id"])}/">{esc(m["title"])}</a></li>' for m in others) + '</ul></section>')
idx_main = ('<div class="container page-head"><div class="breadcrumb"><a href="#/">الرئيسية</a> / الفهرس</div><h1>فهرس موضوعات أطلس</h1>'
            f'<p>{len(items)} موضوعًا عن {len(civs)} حضارة: مدن وشخصيات وأحداث.</p></div><div class="container section article-text" style="padding-top:0">' + ''.join(groups) + '</div>')
open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(
    render('فهرس الموضوعات | أطلس', 'فهرس كل موضوعات أطلس التاريخ التفاعلي.', BASE_URL + 't/', BASE_URL + 'assets/og.jpg',
           f'<base href="../"><link rel="canonical" href="{BASE_URL}t/"><script>window.__INDEX=true</script>', idx_main))

n_t = lambda t: sum(1 for x in d['entries'] if x['type'] == t)
method_main = ('<div class="container page-head"><div class="breadcrumb"><a href="#/">الرئيسية</a> / منهجنا</div><h1>منهجنا</h1>'
               '<p>كيف نكتب صفحات أطلس، ومن أين نأخذ المعلومات، وكيف نراجعها، وما حدود ما نعرضه.</p></div>'
               '<div class="container section article-text" style="padding-top:0">'
               f'<section><h2>ما أطلس؟</h2><p>مشروع تعليمي عربي مستقل يربط التاريخ بالمكان والزمن، فيه {len(items)} صفحة: {len(civs)} حضارة ودولة، و{n_t("city")} مدينة، و{n_t("person")} شخصية، و{n_t("event")} حدثًا.</p></section>'
               f'<section><h2>المصادر والمراجعة</h2><p>كل صفحة مكتوبة بالعربية خصيصًا لأطلس، ولكل قسم مصدر واحد على الأقل من {len(d["sources"])} مصدرًا، أكثرها بريتانيكا واليونسكو والمتاحف الكبرى. وتمر كل دفعة جديدة على مراجعة مستقلة قبل النشر تقارن التواريخ والأسماء والأرقام بالمصادر.</p></section>'
               '<section><h2>الخريطة والصور</h2><p>الحدود التاريخية تقريبية من مشروع Historical Basemaps المفتوح بعد تعريبها وتصحيحها، واليابسة من Natural Earth. والصور من ويكيميديا كومنز مع ذكر المصوّر والرخصة، ولا نعرض صورًا متخيلة للنبي ﷺ أو للصحابة.</p></section>'
               '<p><a class="primary" href="#/method">اقرأ المنهج كاملًا ←</a></p></div>')
os.makedirs(os.path.join(ROOT, 'method'), exist_ok=True)
open(os.path.join(ROOT, 'method', 'index.html'), 'w', encoding='utf-8').write(
    render('منهجنا: كيف نكتب أطلس ونراجعه | أطلس', 'مصادر أطلس، وطريقة مراجعة الصفحات، ودرجات اليقين، وحدود الخريطة التاريخية والصور.', BASE_URL + 'method/', BASE_URL + 'assets/og.jpg',
           f'<base href="../"><link rel="canonical" href="{BASE_URL}method/"><script>location.hash||(location.hash="#/method")</script>', method_main))

urls = [BASE_URL, BASE_URL + 't/', BASE_URL + 'method/'] + [f'{BASE_URL}t/{x["id"]}/' for x in items]
imgs = {f'{BASE_URL}t/{x["id"]}/': x['image'] for x in items if x.get('image')}
open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' +
    ''.join(f'  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod>' + (f'<image:image><image:loc>{esc(imgs[u]["src"])}</image:loc></image:image>' if u in imgs else '') + '</url>\n' for u in urls) + '</urlset>\n')
open(os.path.join(ROOT, 'robots.txt'), 'w', encoding='utf-8').write(f'User-agent: *\nAllow: /\nSitemap: {BASE_URL}sitemap.xml\n')
print('pages', len(items), '+ index; sitemap urls', len(urls))

# تقسيم المحتوى لتسريع أول تحميل: نص الأقسام (ثلثا الحجم) في ملف يُحمّل بعد ظهور الصفحة
def _words(x):
    return len(' '.join([x.get('summary', '')] + [s['text'] for s in x.get('sections', [])]).split())


core = json.loads(json.dumps(d))
core['stats'] = {'sources': len(d['sources'])}
core['sources'] = [{'id': s['id']} for s in d['sources']]
text = {}
for x in core['civilizations'] + core['entries']:
    x['mins'] = max(1, round(_words(x) / 180))
    text[x['id']] = x.pop('sections', [])
    x['sections'] = []
json.dump(core, open(os.path.join(ROOT, 'content-core.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump(text, open(os.path.join(ROOT, 'content-text.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('content-core', os.path.getsize(os.path.join(ROOT, 'content-core.json')) // 1024, 'KB; content-text', os.path.getsize(os.path.join(ROOT, 'content-text.json')) // 1024, 'KB')
