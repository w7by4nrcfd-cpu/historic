"""اختبارات V6.3 للسرعة. التشغيل: python3 tools/build_pages.py ثم python3 -m http.server 8080 --directory dist ثم python3 tests/v62_speed.py"""
import json, os
from playwright.sync_api import sync_playwright
B = os.environ.get('ATLAS_URL', 'http://localhost:8080/')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist')
R = []
def ok(n, c, x=''):
    R.append(bool(c)); print(('PASS' if c else 'FAIL'), n, x)

core = json.load(open(os.path.join(ROOT, 'content-core.json'), encoding='utf-8'))
text = json.load(open(os.path.join(ROOT, 'content-text.json'), encoding='utf-8'))
full = json.load(open(os.path.join(ROOT, 'content.json'), encoding='utf-8'))
ok('core file has no section text', all(not x['sections'] for x in core['civilizations'] + core['entries']))
ok('text file has every page', len(text) == len(full['civilizations']) + len(full['entries']))
ok('core file is less than half the full size', os.path.getsize(os.path.join(ROOT, 'content-core.json')) < os.path.getsize(os.path.join(ROOT, 'content.json')) / 2)
ok('service worker present', os.path.exists(os.path.join(ROOT, 'sw.js')))
ok('land data simplified (< 450 KB)', os.path.getsize(os.path.join(ROOT, 'assets', 'land.geojson')) < 450 * 1024)

ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS)
    pg = b.new_page(viewport={'width': 390, 'height': 844}); errs, reqs = [], []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('request', lambda r: reqs.append(r.url.split('/')[-1]))
    pg.goto(B + '#/atlas'); pg.wait_for_function("()=>document.querySelectorAll('.border-label').length>0", timeout=60000)
    ok('map loads with the core file, not the full one', 'content-core.json' in reqs and 'content.json' not in reqs, str([r for r in reqs if 'content' in r]))
    ok('section text not requested while the map loads', 'content-text.json' not in reqs)
    pg.evaluate("()=>{window.__r=0;window.__atlasMap.on('render',()=>window.__r++)}")
    pg.wait_for_timeout(7000); pg.evaluate("window.__r=0"); pg.wait_for_timeout(3000)
    ok('map stops redrawing when idle', pg.evaluate("window.__r") == 0, str(pg.evaluate("window.__r")))
    pg.wait_for_timeout(1000)
    ok('section text arrives in the background', 'content-text.json' in reqs)
    # فتح موضوع مباشرة: النص يصل ويظهر
    pg2 = b.new_page(); pg2.goto(B + '#/topic/hattin'); pg2.wait_for_timeout(2500)
    ok('topic opened directly shows its sections', pg2.locator('.article-text section').count() >= 3 and 'معركة حطين' in pg2.title())
    pg3 = b.new_page(); pg3.goto(B + 't/saladin/'); pg3.wait_for_timeout(2500)
    ok('static page keeps its title and sections', 'صلاح الدين' in pg3.title() and pg3.locator('.article-text section').count() >= 3, pg3.title())
    # الضغط على مسار يعيد الحركة
    pg.evaluate("()=>{document.getElementById('ax-panel').hidden=false}"); pg.click('[data-route="silk-road"]'); pg.wait_for_timeout(1500)
    pg.evaluate("window.__r=0"); pg.wait_for_timeout(2000)  # ثانيتان: الرسم البرمجي في بيئة الاختبار بطيء الإطارات
    ok('selected route still animates', pg.evaluate("window.__r") > 3, str(pg.evaluate("window.__r")))
    ok('no page errors', not errs, str(errs))
    b.close()
print(f'TOTAL {sum(R)} / {len(R)}'); raise SystemExit(0 if all(R) else 1)
