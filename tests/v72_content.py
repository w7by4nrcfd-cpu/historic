"""اختبارات V7.2: المرحلة الثانية، الدفعة الثانية (الدولة العباسية وعلماؤها): 40 صفحة جديدة.
التشغيل: python3 -m http.server 8080 --directory dist ثم python3 tests/v72_content.py"""
import json, os
from playwright.sync_api import sync_playwright
B = os.environ.get('ATLAS_URL', 'http://localhost:8080/')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist')
R = []
def ok(n, c, x=''):
    R.append(bool(c)); print(('PASS' if c else 'FAIL'), n, x)
d = json.load(open(os.path.join(ROOT, 'content.json'), encoding='utf-8'))
E = {x['id']: x for x in d['entries']}; C = {c['id']: c for c in d['civilizations']}
NEW = ['samarra', 'raqqa', 'bukhara', 'merv', 'nishapur', 'aleppo',
       'al-saffah', 'abu-muslim', 'yahya-barmaki', 'al-mutawakkil', 'ahmad-ibn-tulun', 'sayf-al-dawla', 'al-nasir',
       'abu-hanifa', 'malik-ibn-anas', 'al-shafii', 'ahmad-ibn-hanbal', 'al-bukhari', 'al-tabari',
       'sibawayh', 'ibn-al-muqaffa', 'al-jahiz', 'abu-nuwas', 'al-mutanabbi',
       'hunayn-ibn-ishaq', 'al-kindi', 'al-razi', 'al-farabi', 'ibn-sina', 'al-biruni', 'al-ghazali',
       'talas-751', 'barmakids-803', 'siege-baghdad-812', 'mihna-833', 'amorium-838', 'zanj-869', 'qarmatians-930', 'buyids-945', 'nizamiyya-1067']
ok('40 new pages, all present', len(set(NEW)) == 40 and all(i in E for i in NEW))
ok('content grew to at least 300 pages', len(d['entries']) >= 300, str(len(d['entries'])))
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
ok('older pages link back to the new ones', 'samarra' in E['al-mutasim']['relatedIds'] and 'talas-751' in E['paper-baghdad']['relatedIds'])
ok('batch 1 pages still present', all(i in E for i in ['badr-624', 'mecca', 'prophet-muhammad']))
ok('static pages exist for the new pages', all(os.path.exists(os.path.join(ROOT, 't', i, 'index.html')) for i in NEW))
ok('sitemap lists the new pages', all(f't/{i}/' in open(os.path.join(ROOT, 'sitemap.xml'), encoding='utf-8').read() for i in NEW))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 390, 'height': 844}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    for i in ['ibn-sina', 'mihna-833', 'samarra', 'al-mutanabbi']:
        pg.goto(B + f'#/topic/{i}'); pg.wait_for_timeout(1000)
        n = pg.locator('.article-text section').count()
        ok(f'{i}: page renders its sections', n >= 3, str(n))
        ok(f'{i}: no horizontal scroll', not pg.evaluate('document.documentElement.scrollWidth>innerWidth+1'))
    pg.goto(B + '#/search?q=' + 'المتنبي'); pg.wait_for_timeout(1500)
    ok('search finds a new page', 'المتنبي' in pg.inner_text('main') and 'لا نتائج' not in pg.inner_text('main'))
    ok('no page errors', not errs, str(errs)); b.close()
print(f'TOTAL {sum(R)} / {len(R)}'); raise SystemExit(0 if all(R) else 1)
