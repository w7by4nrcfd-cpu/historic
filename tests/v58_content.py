"""اختبارات V5.8: الدفعة الرابعة لتعميق المحتوى. التشغيل: python3 -m http.server 8080 --directory dist ثم python3 tests/v58_content.py"""
import json, os
from playwright.sync_api import sync_playwright
B = os.environ.get('ATLAS_URL', 'http://localhost:8080/')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist')
R = []
def ok(n, c, x=''):
    R.append(bool(c)); print(('PASS' if c else 'FAIL'), n, x)
d = json.load(open(os.path.join(ROOT, 'content.json'), encoding='utf-8'))
E = {x['id']: x for x in d['entries']}; C = {c['id']: c for c in d['civilizations']}
DEEP = ['translation-movement', 'khwarizmi-algebra', 'ibn-haytham-optics', 'zahrawi-surgery', 'paper-baghdad', 'zij-sultani', 'diriyah', 'riyadh',
        'istanbul', 'constantinople-city', 'petra', 'marrakesh', 'timbuktu', 'isfahan', 'alexander', 'augustus', 'ismail-i', 'abbas-i', 'babur',
        'akbar', 'kublai', 'sundiata', 'ulugh-beg', 'nebuchadnezzar', 'umayyad-end', 'ottoman-egypt', 'damascus-1401', 'taj-mahal',
        'hegra-tombs', 'sultan-hasan']
ok('30 pages in this batch', len(set(DEEP)) == 30)
for i in DEEP:
    s = E[i]['sections']
    ok(f'{i}: 3+ sections, each with text and sources', len(s) >= 3 and all(len(x['text']) > 30 and x['sourceIds'] for x in s), str(len(s)))
ok('batch 2 pages kept their depth', all(len(E[i]['sections']) >= 3 for i in ['hattin', 'jawhar', 'jeddah-1925']))
ids = set(E) | set(C); S = {s['id'] for s in d['sources']}
ok('no dangling related ids', not [r for x in d['entries'] for r in x.get('relatedIds', []) if r not in ids])
ok('no missing source ids', not [s for x in d['entries'] for s in x.get('sourceIds', []) if s not in S])
ok('no duplicate source ids', len(S) == len(d['sources']))
thin = sum(1 for x in d['entries'] if len(x.get('sections', [])) == 1)
ok('thin pages reduced to ≤ 100', thin <= 100, str(thin))
ok('static pages carry the new sections', all(s in open(os.path.join(ROOT, 't', i, 'index.html'), encoding='utf-8').read() for i, s in [('riyadh', 'عاصمة الدولة الثانية'), ('taj-mahal', 'البناء')]))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 390, 'height': 844}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    for i in ['diriyah', 'khwarizmi-algebra', 'akbar', 'sultan-hasan']:
        pg.goto(B + f'#/topic/{i}'); pg.wait_for_timeout(900)
        n = pg.locator('.article-text section').count()
        ok(f'{i}: page renders its sections', n >= 3, str(n))
        ok(f'{i}: no horizontal scroll', not pg.evaluate('document.documentElement.scrollWidth>innerWidth+1'))
    ok('no page errors', not errs, str(errs)); b.close()
print(f'TOTAL {sum(R)} / {len(R)}'); raise SystemExit(0 if all(R) else 1)
