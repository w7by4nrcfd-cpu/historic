"""اختبارات V8: المرحلة الثالثة — تخفيف علامات الأحداث، والخريطة الصغيرة في صفحات المواضيع، وتعميق أهم 50 صفحة.
التشغيل: python3 -m http.server 8080 --directory dist ثم python3 tests/v80_phase3.py"""
import json, os
from playwright.sync_api import sync_playwright
B = os.environ.get('ATLAS_URL', 'http://localhost:8080/')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist')
R = []
def ok(n, c, x=''):
    R.append(bool(c)); print(('PASS' if c else 'FAIL'), n, x)

d = json.load(open(os.path.join(ROOT, 'content.json'), encoding='utf-8'))
E = {x['id']: x for x in d['entries']}
TOP = ('mecca medina jerusalem damascus baghdad cairo cordoba granada istanbul diriyah riyadh prophet-muhammad abu-bakr umar uthman ali '
       'khalid-ibn-walid muawiya abd-al-malik harun-al-rashid al-mamun saladin baybars mehmed-ii suleiman king-abdulaziz muhammad-saud '
       'muhammad-ibn-abd-al-wahhab turki-bin-abdullah ibn-sina ibn-khaldun ibn-battuta ibn-rushd hijra-622 badr-624 yarmuk qadisiyyah hattin '
       'ain-jalut constantinople-1453 baghdad-fall granada-1492 kingdom-1932 masmak-1902 saudi-found diriyah-pact-1744 andalus-start dome-rock '
       'umayyad-mosque translation-movement').split()
ok('50 key pages', len(set(TOP)) == 50)
thin = [i for i in TOP if len(E[i]['sections']) < 5]
ok('every key page has 5+ sections', not thin, str(thin))
ok('section titles unique within each page', all(len({s['title'] for s in E[i]['sections']}) == len(E[i]['sections']) for i in TOP))
mm = os.path.join(ROOT, 'assets', 'minimap.json')
ok('mini-map data exists and is small (< 150 KB)', os.path.exists(mm) and os.path.getsize(mm) < 150 * 1024, str(os.path.getsize(mm) // 1024 if os.path.exists(mm) else 0))
m = json.load(open(mm))
ok('mini-map has land, lakes and rivers', len(m['l']) > 100 and len(m['k']) > 10 and len(m['r']) > 50)
sw = open(os.path.join(ROOT, 'sw.js'), encoding='utf-8').read()
ok('service worker caches the mini-map and has a new cache version', 'minimap' in sw and "atlas-static-v1'" not in sw)

# الصور: من كومنز، بمصوّر ورخصة وصفحة ملف، بلا تكرار
withimg = [i for i in TOP if E[i].get('image')]
ok('at least 39 of the key pages have an image', len(withimg) >= 39, str(len(withimg)))
ims = [x['image'] for x in d['entries'] + d['civilizations'] if x.get('image')]
ok('every image has source, author, licence, caption and Commons page', all(im['src'].startswith('https://upload.wikimedia.org/') and im['author'] and im['license'] and im['caption'] and im['page'].startswith('https://commons.wikimedia.org/wiki/File:') for im in ims))
ok('no image file used twice', len({im['file'] for im in ims}) == len(ims))
ok('static page carries the image with its credit', 'Mark Ahsmann' in open(os.path.join(ROOT, 't', 'abu-bakr', 'index.html'), encoding='utf-8').read())
ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS)
    for name, vp, cap in [('desktop', {'width': 1280, 'height': 860}, 14), ('mobile', {'width': 390, 'height': 844}, 10)]:
        pg = b.new_page(viewport=vp); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        for y in [650, 850, 1200, 1300, 1600]:
            pg.goto(B + f'#/atlas?year={y}'); pg.wait_for_timeout(3500)
            n = pg.locator('.map-point.event').count()
            ok(f'{name}: {y} shows at most {cap} event markers', 0 < n <= cap, str(n))
        # الحدث المطلوب في الرابط يظهر حتى لو كان أقدم من غيره
        pg.goto(B + '#/atlas?topic=badr-624&year=650'); pg.wait_for_timeout(4000)
        ok(f'{name}: linked event stays on the map', pg.locator('.map-point[data-id="badr-624"]').count() == 1)
        # الخريطة الصغيرة
        pg.goto(B + '#/topic/hattin'); pg.wait_for_selector('#minimap svg', timeout=15000); pg.wait_for_timeout(300)
        ok(f'{name}: event page has a mini-map with its place and related places', pg.locator('#minimap svg .mm-main').count() == 1 and pg.locator('#minimap svg circle').count() >= 3)
        ok(f'{name}: mini-map draws land', len(pg.get_attribute('#minimap .mm-land', 'd') or '') > 200)
        ok(f'{name}: mini-map places link to their pages', pg.locator('#minimap a[href^="#/topic/"]').count() >= 3)
        pg.goto(B + '#/topic/ibn-battuta'); pg.wait_for_selector('#minimap svg', timeout=15000)
        ok(f'{name}: person page shows related places without a gold "main" point', pg.locator('#minimap svg circle').count() >= 2 and pg.locator('#minimap .mm-main').count() == 0 and 'أماكن مرتبطة' in pg.inner_text('.mini-sec h2'))
        pg.goto(B + '#/topic/granada'); pg.wait_for_timeout(1500)
        ok(f'{name}: deepened page shows its new sections', pg.locator('.article-text section h2', has_text='البيازين وجنة العريف').count() == 1)
        ok(f'{name}: no horizontal scroll on a topic page', not pg.evaluate('document.documentElement.scrollWidth>innerWidth+1'))
        pg.locator('#minimap a').first.click(); pg.wait_for_timeout(1200)
        ok(f'{name}: clicking a mini-map place opens its page', '#/topic/' in pg.url)
        ok(f'{name}: no page errors', not errs, str(errs))
        pg.close()
    b.close()
print(f'TOTAL {sum(R)} / {len(R)}'); raise SystemExit(0 if all(R) else 1)
