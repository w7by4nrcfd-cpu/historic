"""اختبارات V7.9: المرحلة الثانية، الدفعة التاسعة (العرب في العصر الحديث وما قبل الإسلام والعلماء): 40 صفحة جديدة.
التشغيل: python3 -m http.server 8080 --directory dist ثم python3 tests/v79_content.py"""
import json, os
from playwright.sync_api import sync_playwright
B = os.environ.get('ATLAS_URL', 'http://localhost:8080/')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist')
R = []
def ok(n, c, x=''):
    R.append(bool(c)); print(('PASS' if c else 'FAIL'), n, x)
d = json.load(open(os.path.join(ROOT, 'content.json'), encoding='utf-8'))
E = {x['id']: x for x in d['entries']}; C = {c['id']: c for c in d['civilizations']}
NEW = ['napoleon-egypt-1798', 'muhammad-ali-pasha', 'bulaq-press-1820', 'rifaa-al-tahtawi', 'algiers-1830', 'emir-abdelkader', 'suez-canal-1869', 'jamal-al-din-afghani', 'muhammad-abduh', 'urabi-1882', 'omar-mukhtar', 'maysalun-1920', 'faisal-i-iraq', 'palmyra', 'zenobia', 'bosra', 'ugarit', 'ebla', 'hira', 'numan-iii', 'dhi-qar-609', 'harith-ibn-jabala', 'philip-the-arab', 'jabir-ibn-hayyan', 'banu-musa', 'thabit-ibn-qurra', 'al-battani', 'al-sufi', 'ibn-yunus', 'al-zarqali', 'ibn-zuhr', 'al-jazari', 'ibn-al-baytar', 'ibn-al-shatir', 'al-kashi', 'taqi-al-din', 'arabic-numerals', 'astrolabe', 'bimaristan', 'muqarnas']
ok('40 new pages, all present', len(set(NEW)) == 40 and all(i in E for i in NEW))
ok('content grew to at least 580 pages', len(d['entries']) >= 580, str(len(d['entries'])))
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
ok('older pages link back to the new ones', 'muhammad-ali-pasha' in E['ibrahim-pasha']['relatedIds'] and 'bimaristan' in E['qalawun']['relatedIds'])
ok('batch 1 pages still present', all(i in E for i in ['badr-624', 'mecca', 'ibn-sina', 'mihna-833']))
ok('static pages exist for the new pages', all(os.path.exists(os.path.join(ROOT, 't', i, 'index.html')) for i in NEW))
ok('sitemap lists the new pages', all(f't/{i}/' in open(os.path.join(ROOT, 'sitemap.xml'), encoding='utf-8').read() for i in NEW))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 390, 'height': 844}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    for i in ['emir-abdelkader', 'palmyra', 'al-battani', 'bimaristan']:
        pg.goto(B + f'#/topic/{i}'); pg.wait_for_timeout(1000)
        n = pg.locator('.article-text section').count()
        ok(f'{i}: page renders its sections', n >= 3, str(n))
        ok(f'{i}: no horizontal scroll', not pg.evaluate('document.documentElement.scrollWidth>innerWidth+1'))
    pg.goto(B + '#/search?q=' + 'ميسلون'); pg.wait_for_timeout(1500)
    ok('search finds a new page', 'معركة ميسلون' in pg.inner_text('main') and 'لا نتائج' not in pg.inner_text('main'))
    ok('no page errors', not errs, str(errs)); b.close()
print(f'TOTAL {sum(R)} / {len(R)}'); raise SystemExit(0 if all(R) else 1)
