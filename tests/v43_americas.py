"""V4.3: 1500 frame with borders; Aztecs + Inca."""
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
    ok('18 frames incl. 1500', len(FRAMES) == 18 and 1500 in FRAMES, str(FRAMES))
    pg.goto(B + '#/atlas?year=1500'); pg.wait_for_timeout(4500)
    t = pg.inner_text('#map-topic-list')
    ok('1500 shows Tenochtitlan, Cusco, Samarkand', all(k in t for k in ['تينوتشتيتلان', 'كوسكو', 'سمرقند']), t[:150])
    labels = pg.eval_on_selector_all('.border-label', 'e=>e.map(x=>x.textContent)')
    ok('1500 borders include Aztec and Inca', any('الأزتك' in l for l in labels) and any('الإنكا' in l for l in labels), str(len(labels)))
    pg.click(fsel(1600)); pg.wait_for_timeout(2500)
    labels = pg.eval_on_selector_all('.border-label', 'e=>e.map(x=>x.textContent)')
    ok('1600 borders exclude Inca and Songhai', not any(('الإنكا' in l) or ('سنغاي' in l) for l in labels))
    pg.goto(B + '#/atlas?frame=10'); pg.wait_for_timeout(1500)
    ok('legacy frame=10 still 1600', '1600' in pg.inner_text('#year-label'), pg.inner_text('#year-label'))
    pg.goto(B + '#/topic/aztecs'); pg.wait_for_timeout(800)
    m = pg.inner_text('main')
    ok('aztecs article', 'تينوتشتيتلان' in m and 'كورتيس' in m)
    ok('aztecs map link', pg.locator('a[href*="topic=aztecs&year=1500"]').count() >= 1)
    pg.goto(B + '#/topic/inca'); pg.wait_for_timeout(800)
    m = pg.inner_text('main')
    ok('inca article', 'ماتشو بيتشو' in m and 'الكيبو' in m)
    pg.goto(B + '#/atlas?topic=inca&year=1500'); pg.wait_for_timeout(4000)
    ok('inca topic on map', 'كوسكو' in pg.inner_text('#map-selection') or 'الإنكا' in pg.inner_text('#map-selection'), pg.inner_text('#map-selection')[:80])
    ok('no page errors', not errs, str(errs[:3]))
    b.close()
print('TOTAL', sum(R), '/', len(R))
