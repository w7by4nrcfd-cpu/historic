"""اختبارات V3 للخريطة الرئيسية. التشغيل: python3 -m http.server 8080 --directory dist ثم python3 tests/v3_atlas.py"""
import os
from playwright.sync_api import sync_playwright

B = os.environ.get('ATLAS_URL', 'http://localhost:8080/')
R = []


def ok(name, cond, extra=''):
    R.append(bool(cond))
    print(('PASS' if cond else 'FAIL'), name, extra)


with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    for name, vp in [('mobile', {'width': 390, 'height': 844}), ('desktop', {'width': 1366, 'height': 860})]:
        pg = b.new_page(viewport=vp)
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(B + '#/atlas')
        pg.wait_for_timeout(3000)
        box = pg.locator('.ax').bounding_box()
        ok(f'{name}: map fills first screen', box and box['y'] < 100 and box['y'] + box['height'] >= vp['height'] - 2, str(box))
        ok(f'{name}: no horizontal scroll', not pg.evaluate('document.documentElement.scrollWidth>innerWidth+1'))
        ok(f'{name}: era name shown', pg.inner_text('#ax-era-name') == 'العصور الإسلامية', pg.inner_text('#ax-era-name'))
        # slider and chips agree: oldest frame on the right in RTL
        pg.click('[data-frame="0"]')
        pg.wait_for_timeout(600)
        thumb_right = pg.evaluate("(()=>{const s=document.getElementById('year-slider');return getComputedStyle(s).direction})()")
        ok(f'{name}: slider runs right-to-left like the chips', thumb_right == 'rtl')
        ok(f'{name}: era updates with frame', pg.inner_text('#ax-era-name') == 'العالم القديم')
        pg.click('[data-frame="8"]')
        pg.wait_for_timeout(1200)
        ok(f'{name}: battle marker kind', pg.locator('.map-point.kind-battle').count() >= 1)
        pg.locator('.map-point.kind-battle').first.click(force=True)
        pg.wait_for_timeout(800)
        sel = pg.inner_text('#map-selection')
        ok(f'{name}: selection shows kind and certainty', 'معركة أو حصار' in sel and 'موثق بالمصادر' in sel, sel[:60])
        ok(f'{name}: selection links to encyclopedia', pg.locator('#map-selection a[href^="#/topic/"]').count() >= 1)
        if name == 'mobile':
            ok('mobile: sheet opens on selection', 'open' in pg.get_attribute('#map-side', 'class'))
            pg.click('.ax-handle')
            pg.wait_for_timeout(500)
            ok('mobile: handle collapses sheet', 'open' not in pg.get_attribute('#map-side', 'class'))
        pg.click('.ax-layers label:has(#layer-event)')
        pg.wait_for_timeout(500)
        ok(f'{name}: events layer toggle', pg.locator('.map-point.event').count() == 0)
        ok(f'{name}: no page errors', not errs, str(errs))
        pg.close()
    b.close()

print(f'TOTAL {sum(R)} / {len(R)}')
raise SystemExit(0 if all(R) else 1)
