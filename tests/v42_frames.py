"""V4.2: 300 BC and 1400 frames with borders; Maurya + Timurids."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frames import FRAMES, fsel
from playwright.sync_api import sync_playwright
B = os.environ.get('ATLAS_URL', 'http://localhost:8080/')
R = []
def ok(n, c, x=''):
    R.append(bool(c)); print('PASS' if c else 'FAIL', n, x)

with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    pg = b.new_context(viewport={'width': 1280, 'height': 900}).new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    ok('frames include -300 and 1400', -300 in FRAMES and 1400 in FRAMES, str(FRAMES))
    pg.goto(B + '#/atlas?year=-300'); pg.wait_for_timeout(4000)
    ok('300 BC label', '300 ق.م' in pg.inner_text('#year-label'))
    ok('300 BC shows Pataliputra', 'باتاليبوترا' in pg.inner_text('#map-topic-list'))
    labels = pg.eval_on_selector_all('.border-label', 'e=>e.map(x=>x.textContent)')
    ok('300 BC borders include Maurya', any('الماورية' in l for l in labels), str(labels[:6]))
    ok('300 BC tag mentions approx borders', '300' in pg.inner_text('#map-tag'), pg.inner_text('#map-tag'))
    pg.click(fsel(1400)); pg.wait_for_timeout(3000)
    ok('1400 shows Samarkand', 'سمرقند' in pg.inner_text('#map-topic-list'))
    labels = pg.eval_on_selector_all('.border-label', 'e=>e.map(x=>x.textContent)')
    ok('1400 borders include Timurids', any('التيمورية' in l for l in labels), str(labels[:6]))
    ok('1400 borders exclude anachronistic Yuan', not any('يوان' in l for l in labels))
    pg.click(fsel(-100)); pg.wait_for_timeout(2500)
    labels = pg.eval_on_selector_all('.border-label', 'e=>e.map(x=>x.textContent)')
    ok('100 BC borders exclude Maurya', not any('الماورية' in l for l in labels))
    pg.goto(B + '#/atlas?frame=9'); pg.wait_for_timeout(1500)
    ok('legacy frame=9 still 1300', '1300' in pg.inner_text('#year-label'), pg.inner_text('#year-label'))
    pg.goto(B + '#/topic/timurids'); pg.wait_for_timeout(800)
    m = pg.inner_text('main')
    ok('timurids article', 'أولوغ بيك' in m and 'أنقرة' in m)
    ok('timurids map link', pg.locator('a[href*="topic=timurids&year=1400"]').count() >= 1)
    pg.goto(B + '#/topic/maurya'); pg.wait_for_timeout(800)
    ok('maurya article', 'كالينغا' in pg.inner_text('main'))
    ok('maurya map link', pg.locator('a[href*="topic=maurya&year=-300"]').count() >= 1)
    pg.goto(B + '#/topic/babur'); pg.wait_for_timeout(500)
    ok('babur links Timurids', pg.locator('a[href="#/topic/timurids"]').count() >= 1)
    ok('no page errors', not errs, str(errs[:3]))
    b.close()
print('TOTAL', sum(R), '/', len(R))
