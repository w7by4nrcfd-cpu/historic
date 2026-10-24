"""اختبارات V8.4: المرحلة الرابعة — صفحة «منهجنا»، وتحسين الظهور في محركات البحث، وتخفيف ملف المحتوى الأساسي.
التشغيل: python3 -m http.server 8080 --directory dist ثم python3 tests/v84_phase4.py"""
import json, os, re
from playwright.sync_api import sync_playwright
B = os.environ.get('ATLAS_URL', 'http://localhost:8080/')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist')
R = []
def ok(n, c, x=''):
    R.append(bool(c)); print(('PASS' if c else 'FAIL'), n, x)
rd = lambda *p: open(os.path.join(ROOT, *p), encoding='utf-8').read()

full = json.load(open(os.path.join(ROOT, 'content.json'), encoding='utf-8'))
core = json.load(open(os.path.join(ROOT, 'content-core.json'), encoding='utf-8'))
ok('core file keeps only source ids', all(set(s) == {'id'} for s in core['sources']) and len(core['sources']) == len(full['sources']))
ok('core file carries the source count for the method page', core.get('stats', {}).get('sources') == len(full['sources']))
ok('core file smaller than before (< 480 KB)', os.path.getsize(os.path.join(ROOT, 'content-core.json')) < 480 * 1024, str(os.path.getsize(os.path.join(ROOT, 'content-core.json')) // 1024))

idx = rd('index.html')
ok('site description no longer says 34 civilizations', 'أربع وثلاثين' not in idx and '600 صفحة' in idx)
ok('footer links to the method page', 'href="method/">منهجنا<' in idx)
m = rd('method', 'index.html')
ok('static method page: title, canonical and content', 'منهجنا' in m and 'rel="canonical" href="https://w7by4nrcfd-cpu.github.io/historic/method/"' in m and 'Historical Basemaps' in m)
sm = rd('sitemap.xml')
ok('sitemap lists the method page', '/historic/method/' in sm)
ok('sitemap carries images for pages that have them', sm.count('<image:image>') >= 50, str(sm.count('<image:image>')))
b = rd('t', 'badr-624', 'index.html')
ok('event page title carries its year', '<title>غزوة بدر (624 م) | أطلس</title>' in b)
ok('topic page has breadcrumb structured data', '"BreadcrumbList"' in b and '"position": 2' in b)
ok('topic page is marked as an article for sharing', 'og:type" content="article"' in b and 'og:type" content="website"' not in b)
ok('person page structured data says Person', '"@type": "Person"' in rd('t', 'saladin', 'index.html'))
ok('visible breadcrumb links to the civilization', 'href="t/rashidun/"' in b)

with sync_playwright() as p:
    br = p.chromium.launch()
    for name, vp in [('desktop', {'width': 1280, 'height': 860}), ('mobile', {'width': 390, 'height': 844})]:
        pg = br.new_page(viewport=vp); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(B + '#/method'); pg.wait_for_selector('h1', timeout=15000); pg.wait_for_timeout(800)
        t = pg.inner_text('main')
        ok(f'{name}: method page renders', pg.inner_text('h1') == 'منهجنا')
        ok(f'{name}: method page shows live counts', f'{len(full["entries"]) + len(full["civilizations"])} صفحة' in t and f'{len(full["sources"])} مصدرًا' in t, t[:120])
        ok(f'{name}: method page lists frames without borders', '650 م' in t and '1200 م' in t)
        ok(f'{name}: method page does not dump the source list', pg.locator('main a[href*="wikipedia.org"]').count() == 0)
        ok(f'{name}: image credits are listed', pg.locator('main details li').count() >= 50)
        ok(f'{name}: old address still opens the method page', (pg.goto(B + '#/sources'), pg.wait_for_timeout(600), pg.inner_text('h1'))[2] == 'منهجنا')
        ok(f'{name}: no horizontal scroll', not pg.evaluate('document.documentElement.scrollWidth>innerWidth+1'))
        pg.goto(B + 'method/'); pg.wait_for_timeout(2500)
        ok(f'{name}: static method address opens the full page', pg.inner_text('h1') == 'منهجنا' and pg.locator('main details').count() == 1)
        ok(f'{name}: no page errors', not errs, str(errs))
        pg.close()
    br.close()
print(f'TOTAL {sum(R)} / {len(R)}'); raise SystemExit(0 if all(R) else 1)
