"""اختبارات V7.6: المرحلة الثانية، الدفعة السادسة (الدولة العثمانية): 40 صفحة جديدة.
التشغيل: python3 -m http.server 8080 --directory dist ثم python3 tests/v76_content.py"""
import json, os
from playwright.sync_api import sync_playwright
B = os.environ.get('ATLAS_URL', 'http://localhost:8080/')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist')
R = []
def ok(n, c, x=''):
    R.append(bool(c)); print(('PASS' if c else 'FAIL'), n, x)
d = json.load(open(os.path.join(ROOT, 'content.json'), encoding='utf-8'))
E = {x['id']: x for x in d['entries']}; C = {c['id']: c for c in d['civilizations']}
NEW = ['bursa', 'edirne', 'algiers', 'sarajevo', 'tripoli-libya', 'iznik', 'osman-i', 'orhan', 'murad-i', 'bayezid-i',
       'murad-ii', 'selim-i', 'abdulmejid-i', 'selim-iii', 'mahmud-ii', 'abdulhamid-ii', 'mimar-sinan', 'hurrem-sultan',
       'kosem-sultan', 'sokollu-mehmed', 'piri-reis', 'hayreddin-barbarossa', 'evliya-celebi', 'katip-celebi', 'osman-1299',
       'bursa-1326', 'kosovo-1389', 'nicopolis-1396', 'varna-1444', 'mohacs-1526', 'vienna-1529', 'baghdad-1534', 'preveza-1538',
       'lepanto-1571', 'vienna-1683', 'karlowitz-1699', 'janissaries-1826', 'tanzimat-1839', 'hejaz-railway-1908',
       'sultanate-abolition-1922']
ok('40 new pages, all present', len(set(NEW)) == 40 and all(i in E for i in NEW))
ok('content grew to at least 460 pages', len(d['entries']) >= 460, str(len(d['entries'])))
for i in NEW:
    x = E[i]; s = x['sections']
    good = len(s) >= 3 and all(len(t['text']) > 40 and t['sourceIds'] for t in s) and x['summary'] and x['sourceIds']
    if x['type'] == 'event':
        good = good and isinstance(x.get('year'), int) and x.get('dateLabel') and x.get('kind') and len(x.get('coordinates', [])) == 2
    if x['type'] == 'city':
        good = good and x.get('startYear') and x.get('endYear') and len(x.get('coordinates', [])) == 2
    ok(f'{i}: complete page ({x["type"]}, {len(s)} sections)', good)
    ok(f'{i}: linked to a civilization', any(r in C for r in x['relatedIds']))
ids = set(E) | set(C); S = {s['id'] for s in d['sources']}
ok('no dangling related ids', not [r for x in d['entries'] for r in x.get('relatedIds', []) if r not in ids])
ok('no missing source ids', not [s for x in d['entries'] for s in x.get('sourceIds', []) if s not in S])
ok('no duplicate ids', len(E) == len(d['entries']) and not set(E) & set(C))
ok('older pages link back to the new ones', 'mohacs-1526' in E['suleiman']['relatedIds'])
ok('batch 1 pages still present', all(i in E for i in ['badr-624', 'mecca', 'ibn-sina', 'mihna-833']))
ok('static pages exist for the new pages', all(os.path.exists(os.path.join(ROOT, 't', i, 'index.html')) for i in NEW))
ok('sitemap lists the new pages', all(f't/{i}/' in open(os.path.join(ROOT, 'sitemap.xml'), encoding='utf-8').read() for i in NEW))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 390, 'height': 844}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    for i in ['mimar-sinan', 'mohacs-1526', 'hejaz-railway-1908', 'algiers']:
        pg.goto(B + f'#/topic/{i}'); pg.wait_for_timeout(1000)
        n = pg.locator('.article-text section').count()
        ok(f'{i}: page renders its sections', n >= 3, str(n))
        ok(f'{i}: no horizontal scroll', not pg.evaluate('document.documentElement.scrollWidth>innerWidth+1'))
    pg.goto(B + '#/search?q=' + 'موهاج'); pg.wait_for_timeout(1500)
    ok('search finds a new page', 'معركة موهاج' in pg.inner_text('main') and 'لا نتائج' not in pg.inner_text('main'))
    ok('no page errors', not errs, str(errs)); b.close()
print(f'TOTAL {sum(R)} / {len(R)}'); raise SystemExit(0 if all(R) else 1)
