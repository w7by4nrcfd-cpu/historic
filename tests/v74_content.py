"""اختبارات V7.4: المرحلة الثانية، الدفعة الرابعة (الفاطميون والسلاجقة والأيوبيون والحروب الصليبية): 40 صفحة جديدة.
التشغيل: python3 -m http.server 8080 --directory dist ثم python3 tests/v74_content.py"""
import json, os
from playwright.sync_api import sync_playwright
B = os.environ.get('ATLAS_URL', 'http://localhost:8080/')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist')
R = []
def ok(n, c, x=''):
    R.append(bool(c)); print(('PASS' if c else 'FAIL'), n, x)
d = json.load(open(os.path.join(ROOT, 'content.json'), encoding='utf-8'))
E = {x['id']: x for x in d['entries']}; C = {c['id']: c for c in d['civilizations']}
NEW = ['antioch', 'edessa', 'acre', 'mosul', 'kerak', 'tripoli-levant', 'al-hakim', 'al-mustansir', 'badr-al-jamali',
       'imad-al-din-zengi', 'nur-al-din', 'shirkuh', 'al-adil', 'qadi-al-fadil', 'usama-ibn-munqidh', 'ibn-al-athir',
       'tughril-beg', 'malik-shah', 'sanjar', 'kilij-arslan-i', 'omar-khayyam', 'richard-i', 'ibn-jubayr', 'dar-al-ilm-1005',
       'shidda-1065', 'antioch-1098', 'jerusalem-1099', 'edessa-1144', 'damascus-1148', 'egypt-1169', 'fatimid-end-1171',
       'myriokephalon-1176', 'acre-1191', 'arsuf-1191', 'ramla-1192', 'damietta-1219', 'jerusalem-1229', 'kose-dag-1243',
       'mansurah-1250', 'acre-1291']
ok('40 new pages, all present', len(set(NEW)) == 40 and all(i in E for i in NEW))
ok('content grew to at least 380 pages', len(d['entries']) >= 380, str(len(d['entries'])))
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
ok('older pages link back to the new ones', 'nur-al-din' in E['saladin']['relatedIds'])
ok('batch 1 pages still present', all(i in E for i in ['badr-624', 'mecca', 'ibn-sina', 'mihna-833']))
ok('static pages exist for the new pages', all(os.path.exists(os.path.join(ROOT, 't', i, 'index.html')) for i in NEW))
ok('sitemap lists the new pages', all(f't/{i}/' in open(os.path.join(ROOT, 'sitemap.xml'), encoding='utf-8').read() for i in NEW))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 390, 'height': 844}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    for i in ['nur-al-din', 'acre-1191', 'omar-khayyam', 'mansurah-1250']:
        pg.goto(B + f'#/topic/{i}'); pg.wait_for_timeout(1000)
        n = pg.locator('.article-text section').count()
        ok(f'{i}: page renders its sections', n >= 3, str(n))
        ok(f'{i}: no horizontal scroll', not pg.evaluate('document.documentElement.scrollWidth>innerWidth+1'))
    pg.goto(B + '#/search?q=' + 'المنصورة'); pg.wait_for_timeout(1500)
    ok('search finds a new page', 'معركة المنصورة' in pg.inner_text('main') and 'لا نتائج' not in pg.inner_text('main'))
    ok('no page errors', not errs, str(errs)); b.close()
print(f'TOTAL {sum(R)} / {len(R)}'); raise SystemExit(0 if all(R) else 1)
