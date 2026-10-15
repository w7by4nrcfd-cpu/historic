"""V4.1: 1750 BC frame, legacy frame links, Mesopotamia + Phoenicia content."""
import os, json
from playwright.sync_api import sync_playwright
B = os.environ.get('ATLAS_URL', 'http://localhost:8080/')
R = []
def ok(n, c, x=''):
    R.append(bool(c)); print('PASS' if c else 'FAIL', n, x)

with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    pg = b.new_context(viewport={'width': 1280, 'height': 900}).new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(B + '#/atlas?frame=1'); pg.wait_for_timeout(3000)
    ok('legacy frame=1 still opens 400 BC', '400 ق.م' in pg.inner_text('#year-label'), pg.inner_text('#year-label'))
    pg.goto(B + '#/atlas?frame=13'); pg.wait_for_timeout(1500)
    ok('legacy frame=13 still opens 1932', '1932' in pg.inner_text('#year-label'), pg.inner_text('#year-label'))
    pg.goto(B + '#/atlas?year=-1750'); pg.wait_for_timeout(3000)
    ok('1750 BC frame label', '1750 ق.م' in pg.inner_text('#year-label'))
    t = pg.inner_text('#map-topic-list')
    ok('1750 BC shows Babylon and Hammurabi', 'بابل' in t and 'حمورابي' in t, t[:120])
    pg.click('[data-frame="1"]'); pg.wait_for_timeout(1500)
    t = pg.inner_text('#map-topic-list'); ok('1400 BC shows Tyre and Babylon', 'صور' in t and 'بابل' in t, t[:120])
    ok('1750 BC markers', pg.locator('.map-point').count() >= 3, str(pg.locator('.map-point').count()))
    pg.click('[data-frame="2"]'); pg.wait_for_timeout(1500)
    ok('400 BC shows Carthage', 'قرطاج' in pg.inner_text('#map-topic-list'))
    pg.goto(B + '#/topic/mesopotamia'); pg.wait_for_timeout(800)
    m = pg.inner_text('main')
    ok('mesopotamia article', 'حمورابي' in m and 'ولادة الكتابة' in m and 'بلاد الرافدين' in m)
    ok('mesopotamia map link uses year', pg.locator('a[href*="topic=mesopotamia&year=-1750"]').count() >= 1)
    pg.goto(B + '#/topic/phoenicia'); pg.wait_for_timeout(800)
    m = pg.inner_text('main')
    ok('phoenicia article', 'الأبجدية' in m and 'حنبعل' in m)
    pg.goto(B + '#/topic/hannibal'); pg.wait_for_timeout(500)
    ok('hannibal page', 'كاناي' in pg.inner_text('main'))
    pg.goto(B + '#/encyclopedia'); pg.wait_for_timeout(800)
    pg.fill('#search', 'حمورابي'); pg.wait_for_timeout(500)
    ok('search finds Hammurabi', 'حمورابي' in pg.inner_text('#results'))
    pg.goto(B); pg.wait_for_timeout(1500)
    ok('home first era links to 1750 BC', pg.locator('.era').first.get_attribute('href') == '#/atlas?year=-1750')
    pg.goto(B + 't/mesopotamia/'); pg.wait_for_timeout(1500)
    ok('static page mesopotamia', 'بلاد الرافدين' in pg.title())
    ok('no page errors', not errs, str(errs[:3]))
    b.close()
print('TOTAL', sum(R), '/', len(R))
