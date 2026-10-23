"""اختبارات V5.5: الدفعة الأولى لتعميق المحتوى. التشغيل: python3 -m http.server 8080 --directory dist ثم python3 tests/v55_content.py"""
import json, os
from playwright.sync_api import sync_playwright
B = os.environ.get('ATLAS_URL', 'http://localhost:8080/')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist')
R = []
def ok(n, c, x=''):
    R.append(bool(c)); print(('PASS' if c else 'FAIL'), n, x)
d = json.load(open(os.path.join(ROOT, 'content.json'), encoding='utf-8'))
E = {x['id']: x for x in d['entries']}; C = {c['id']: c for c in d['civilizations']}
NEW = ['al-mansur', 'harun-al-rashid', 'al-mamun', 'zubaydah', 'khalid-ibn-walid', 'saad-ibn-abi-waqqas', 'amr-ibn-al-as', 'tariq-ibn-ziyad', 'hulagu', 'ibn-battuta']
DEEP = ['yarmuk', 'qadisiyyah', 'baghdad-found', 'baghdad-fall', 'ain-jalut', 'constantinople-1453', 'andalus-start', 'cordoba-caliphate', 'dome-rock', 'hijri-calendar',
        'mansa-musa-hajj', 'marib-dam', 'petra-312', 'alexander-death', 'baghdad', 'cordoba', 'damascus', 'medina', 'cairo', 'samarkand']
for i in NEW:
    ok(f'{i}: new person with 3 sections and sources', i in E and E[i]['type'] == 'person' and len(E[i]['sections']) >= 3 and E[i]['sourceIds'])
for i in DEEP:
    ok(f'{i}: deepened to 3+ sections', len(E[i]['sections']) >= 3, str(len(E[i]['sections'])))
ok('Abbasid notable people are the right caliphs', [p['id'] for p in C['abbasid']['people']][:3] == ['al-mansur', 'harun-al-rashid', 'al-mamun'])
ok('Rashidun page lists Khalid, Sa\'d and Amr', {'khalid-ibn-walid', 'saad-ibn-abi-waqqas', 'amr-ibn-al-as'} <= {p['id'] for p in C['rashidun']['people']})
ids = set(E) | set(C); S = {s['id'] for s in d['sources']}
ok('no dangling related ids', not [r for x in d['entries'] for r in x.get('relatedIds', []) if r not in ids])
ok('no missing source ids', not [s for x in d['entries'] for s in x.get('sourceIds', []) if s not in S])
ok('static pages generated for new people', all(os.path.exists(os.path.join(ROOT, 't', i, 'index.html')) for i in NEW))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 390, 'height': 844}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    for i in ['harun-al-rashid', 'baghdad-fall', 'tariq-ibn-ziyad']:
        pg.goto(B + f'#/topic/{i}'); pg.wait_for_timeout(900)
        n = pg.locator('.article-text section').count()
        ok(f'{i}: page renders its sections', n >= 3, str(n))
    pg.goto(B + '#/topic/abbasid'); pg.wait_for_timeout(900)
    ok('Abbasid infobox shows Harun al-Rashid', 'هارون الرشيد' in pg.inner_text('main'))
    pg.goto(B + '#/encyclopedia'); pg.wait_for_timeout(700); pg.fill('#search', 'هارون'); pg.wait_for_timeout(300)
    ok('search finds Harun', pg.locator('.result-card').count() >= 1)
    ok('no page errors', not errs, str(errs)); b.close()
print(f'TOTAL {sum(R)} / {len(R)}'); raise SystemExit(0 if all(R) else 1)
