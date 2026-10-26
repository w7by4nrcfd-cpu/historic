"""اختبارات V9.3: دليل المدن (108 مدن في 9 مناطق) ومخطط بغداد في رابط خاص.
التشغيل: python3 -m http.server 8080 --directory dist ثم python3 tests/v93_cities.py"""
import os
from playwright.sync_api import sync_playwright
B = os.environ.get('ATLAS_URL', 'http://localhost:8080/')
R = []
def ok(n, c, x=''):
    R.append(bool(c)); print(('PASS' if c else 'FAIL'), n, x)

with sync_playwright() as p:
    br = p.chromium.launch()
    for name, vp in [('mobile', {'width': 390, 'height': 844}), ('desktop', {'width': 1280, 'height': 900})]:
        pg = br.new_page(viewport=vp); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(B + '#/city'); pg.wait_for_selector('.city-card-main', timeout=15000); pg.wait_for_timeout(500)
        ok(f'{name}: all 108 cities listed', pg.locator('.city-card-main').count() == 108, str(pg.locator('.city-card-main').count()))
        ok(f'{name}: 9 region sections', pg.locator('.city-region').count() == 9)
        pg.click('[data-region="arabia"]'); pg.wait_for_timeout(300)
        t = pg.inner_text('#city-body')
        ok(f'{name}: Arabia filter shows 23 cities incl. Mecca, Diriyah, Riyadh, al-Ula', pg.locator('.city-card-main').count() == 23 and all(c in t for c in ['مكة المكرمة', 'الدرعية', 'الرياض', 'العُلا']))
        pg.click('[data-csort="time"]'); pg.wait_for_timeout(300)
        first = pg.locator('.city-card-main b').first.inner_text()
        ok(f'{name}: time sort puts the oldest first', first == 'دلمون (قلعة البحرين)', first)
        pg.click('[data-region="all"]'); pg.click('[data-csort="region"]'); pg.wait_for_timeout(300)
        ok(f'{name}: Baghdad plan card in the Iraq section', pg.locator('.city-region:has-text("العراق") a[href="#/city/baghdad"]').count() == 1)
        href = pg.locator('.city-card:has-text("مكة المكرمة") a.city-onmap').get_attribute('href')
        ok(f'{name}: map button opens the city on the map', href.startswith('#/atlas?topic=mecca&year='), href)
        ok(f'{name}: no horizontal scroll', not pg.evaluate('document.documentElement.scrollWidth>innerWidth+1'))
        pg.goto(B + '#/city/baghdad'); pg.wait_for_selector('.hotspot', timeout=10000)
        ok(f'{name}: Baghdad round-city plan still works', pg.locator('.hotspot').count() == 4)
        pg.goto(B + '#/'); pg.wait_for_selector('.hero'); pg.wait_for_timeout(500)
        ok(f'{name}: home shows 4 cities and a link to the guide', pg.locator('main .city-card-main').count() == 4 and pg.locator('a[href="#/city"]').count() >= 1)
        ok(f'{name}: no page errors', not errs, str(errs[:2]))
        pg.close()
    br.close()
print(f'TOTAL {sum(R)} / {len(R)}'); raise SystemExit(0 if all(R) else 1)
