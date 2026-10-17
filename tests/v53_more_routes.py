"""اختبارات V5.4: المسارات السبعة الجديدة. كل مسار يفتح في لقطته ويُرسم وتظهر محطاته.
التشغيل: python3 -m http.server 8080 --directory dist ثم python3 tests/v53_more_routes.py"""
import json
import os
from playwright.sync_api import sync_playwright

B = os.environ.get('ATLAS_URL', 'http://localhost:8080/')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist')
OUT = os.environ.get('SHOTS')
R = []


def ok(name, cond, extra=''):
    R.append(bool(cond))
    print(('PASS' if cond else 'FAIL'), name, extra)


routes = {r['id']: r for r in json.load(open(os.path.join(ROOT, 'assets', 'routes.json'), encoding='utf-8'))['routes']}
content = json.load(open(os.path.join(ROOT, 'content.json'), encoding='utf-8'))
known = {x['id'] for x in content['civilizations'] + content['entries']}

EXPECT = {  # المسار ← اللقطة التي يُفتح فيها
    'hijra': '650 م', 'conquest-sham': '650 م', 'conquest-iraq': '650 م', 'tariq-andalus': '850 م',
    'hulagu': '1300 م', 'incense-route': '117 م', 'ibn-battuta': '1400 م',
}
for rid in EXPECT:
    r = routes[rid]
    ok(f'{rid}: has sources', len(r['sources']) >= 1)
    ok(f'{rid}: related topics exist in the encyclopedia', all(i in known for i in r.get('relatedIds', [])), str([i for i in r.get('relatedIds', []) if i not in known]))
    ok(f'{rid}: at least 4 stations', len(r['stations']) >= 4)

# محطات مشتركة يجب أن تطابق إحداثيات المدن في الموسوعة
city = {x['id']: x['coordinates'] for x in content['entries'] if x['type'] == 'city' and x.get('coordinates')}
pairs = [('hijra', 'المدينة المنورة', 'medina'), ('hulagu', 'بغداد', 'baghdad'), ('incense-route', 'البتراء', 'petra'), ('tariq-andalus', 'قرطبة', 'cordoba')]
for rid, name, cid in pairs:
    s = next(s for s in routes[rid]['stations'] if s['n'] == name)
    ok(f'{rid}: {cid} station matches encyclopedia coordinates', abs(s['p'][0] - city[cid][0]) < .05 and abs(s['p'][1] - city[cid][1]) < .05, f"{s['p']} vs {city[cid]}")

ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS)
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(B + '#/atlas?year=850')
    pg.wait_for_timeout(4500)
    pg.click('.ax-coach-ok')
    for rid, frame in EXPECT.items():
        pg.evaluate("()=>{document.getElementById('ax-panel').hidden=false}")
        pg.click(f'[data-route="{rid}"]')
        pg.wait_for_timeout(1800)
        ok(f'{rid}: opens at {frame}', pg.inner_text('#year-label') == frame, pg.inner_text('#year-label'))
        ok(f'{rid}: drawn on the map', rid in (pg.evaluate('window.__routesShown') or []))
        ok(f'{rid}: info panel shows its title', routes[rid]['title'] in pg.inner_text('#map-selection'))
        pg.wait_for_timeout(9500)
        n = pg.locator('.route-stop-label').count()
        ok(f'{rid}: station labels appear', n >= 3, str(n))
        if OUT:
            pg.screenshot(path=os.path.join(OUT, f'route_{rid}.png'))
    ok('no page errors', not errs, str(errs))
    b.close()

print(f'TOTAL {sum(R)} / {len(R)}')
raise SystemExit(0 if all(R) else 1)
