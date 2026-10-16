"""اختبارات V5.2: الانتقال المتدرج بين اللقطات، المسارات التاريخية، تخفيف التزاحم على الجوال.
التشغيل: python3 -m http.server 8080 --directory dist ثم python3 tests/v52_routes.py"""
import json
import os
from playwright.sync_api import sync_playwright

B = os.environ.get('ATLAS_URL', 'http://localhost:8080/')
R = []
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist')


def ok(name, cond, extra=''):
    R.append(bool(cond))
    print(('PASS' if cond else 'FAIL'), name, extra)


# سلامة بيانات المسارات
routes = json.load(open(os.path.join(ROOT, 'assets', 'routes.json'), encoding='utf-8'))['routes']
ok('routes file has 3 routes', len(routes) == 3, str([r['id'] for r in routes]))
for r in routes:
    st = r['stations']
    ok(f"{r['id']}: every station has valid lon/lat", all(-180 <= s['p'][0] <= 180 and -90 <= s['p'][1] <= 90 for s in st))
    ok(f"{r['id']}: has a source", len(r.get('sources', [])) >= 1)
    ok(f"{r['id']}: show range covers its dates", r['show'][0] <= r['from'] and r['show'][1] >= r['from'])
    ys = [s['y'] for s in st if 'y' in s]
    ok(f"{r['id']}: station years in order", ys == sorted(ys), str(ys))
dz = next(r for r in routes if r['id'] == 'darb-zubaydah')
fayd = next(s for s in dz['stations'] if s['n'] == 'فيد')
ok('Darb Zubaydah: Fayd matches UNESCO coordinates (27°7′13″N 42°31′21″E)', abs(fayd['p'][1] - 27.1203) < .01 and abs(fayd['p'][0] - 42.5224) < .01)

ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS)
    for name, vp in [('desktop', {'width': 1440, 'height': 900}), ('mobile', {'width': 390, 'height': 844})]:
        ctx = b.new_context(viewport=vp)
        pg = ctx.new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(B + '#/atlas?year=850')
        pg.wait_for_timeout(4500)
        pg.click('.ax-coach-ok')

        # المسارات في 850 م: طريق الحرير ودرب زبيدة
        shown = pg.evaluate('window.__routesShown')
        ok(f'{name}: 850 shows silk road and Darb Zubaydah', sorted(shown or []) == ['darb-zubaydah', 'silk-road'], str(shown))
        n_lines = pg.evaluate("()=>window.__atlasMap.querySourceFeatures('routes').length")
        ok(f'{name}: route lines drawn', n_lines >= 2, str(n_lines))
        ok(f'{name}: summary counts routes', 'مسارات' in pg.inner_text('#map-selection'))

        # الانتقال المتدرج
        pg.click('[data-frame-move="1"]')
        pg.wait_for_timeout(120)
        mid = pg.evaluate("()=>{const m=window.__atlasMap;return [m.getPaintProperty('border-fill','fill-opacity')[1], m.getSource('borders-prev')._data?.features?.length||0]}")
        ok(f'{name}: borders fade in (opacity factor below 1 mid-transition)', mid[0] < 1, str(mid))
        ok(f'{name}: previous borders kept during the fade', mid[1] > 0, str(mid))
        pg.wait_for_timeout(1500)
        end = pg.evaluate("()=>{const m=window.__atlasMap;return [m.getPaintProperty('border-fill','fill-opacity')[1], m.getSource('borders-prev')._data?.features?.length||0]}")
        ok(f'{name}: fade completes and old borders cleared', end[0] == 1 and end[1] == 0, str(end))

        # فتح مسار من لوحة الطبقات: ينتقل إلى زمنه ويرسمه
        pg.click('#ax-layers-btn')
        pg.wait_for_timeout(300)
        ok(f'{name}: route list in layers panel', pg.locator('#route-list [data-route]').count() == 3)
        pg.click('[data-route="alexander-route"]')
        pg.wait_for_timeout(1500)
        ok(f'{name}: opening Alexander jumps to 300 BC', '300 ق.م' in pg.inner_text('#year-label'), pg.inner_text('#year-label'))
        sel = pg.inner_text('#map-selection')
        ok(f'{name}: route info panel', 'حملة الإسكندر' in sel and 'مسار تقريبي' in sel and 'غوغميلا' in sel)
        ok(f'{name}: approximate stations flagged', pg.locator('.route-stations b i').count() >= 3)
        pg.wait_for_timeout(10000)
        labels = pg.locator('.route-stop-label').count()
        ok(f'{name}: station labels appear as the route is drawn', labels >= 10, str(labels))
        ok(f'{name}: other map labels dimmed in route mode', pg.evaluate("()=>document.querySelector('.ax').classList.contains('route-mode')"))
        if name == 'mobile':
            ok('mobile: sheet stays down so the drawing is visible', 'open' not in (pg.get_attribute('#map-side', 'class') or ''))

        # الضغط على مدينة يخرج من وضع المسار
        pg.evaluate("()=>document.querySelector('.map-point:not(.stack-under)').click()")
        pg.wait_for_timeout(600)
        ok(f'{name}: selecting a place leaves route mode', not pg.evaluate("()=>document.querySelector('.ax').classList.contains('route-mode')") and pg.locator('.route-stop-label').count() == 0)

        # إطفاء طبقة المسارات
        pg.evaluate("()=>{document.getElementById('ax-panel').hidden=false;document.getElementById('layer-routes').click()}")
        pg.wait_for_timeout(800)
        ok(f'{name}: routes layer toggle', pg.evaluate("()=>window.__atlasMap.querySourceFeatures('routes').length") == 0)
        ok(f'{name}: no page errors', not errs, str(errs))
        ctx.close()

    # الجوال: عدد أسماء الدول الظاهرة عند التبعيد أقل
    ctx = b.new_context(viewport={'width': 390, 'height': 844})
    pg = ctx.new_page()
    pg.goto(B + '#/atlas?year=1300')
    pg.wait_for_timeout(4500)
    pg.evaluate("()=>window.__atlasMap.jumpTo({zoom:1.6,center:[50,35]})")
    pg.wait_for_timeout(1200)
    vis = pg.evaluate("()=>[...document.querySelectorAll('.border-label')].filter(e=>e.style.display!=='none'&&getComputedStyle(e).visibility!=='hidden').length")
    ok('mobile world view keeps only major state names (≤ 8)', vis <= 8, str(vis))
    ctx.close()
    b.close()

print(f'TOTAL {sum(R)} / {len(R)}')
raise SystemExit(0 if all(R) else 1)
