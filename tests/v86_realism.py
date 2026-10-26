"""اختبارات V8.6: خريطة أوقع — غطاء الأرض (صحارى وجليد...)، وحدود بلا تداخل ولا امتداد فوق البحر، وتضاريس بلا مستطيل.
التشغيل: python3 -m http.server 8080 --directory dist ثم python3 tests/v86_realism.py"""
import glob, io, json, os
from playwright.sync_api import sync_playwright
from PIL import Image
from shapely.geometry import shape, Point
from shapely.ops import unary_union
from shapely.validation import make_valid
B = os.environ.get('ATLAS_URL', 'http://localhost:8080/')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist')
R = []
def ok(n, c, x=''):
    R.append(bool(c)); print(('PASS' if c else 'FAIL'), n, x)

land0 = unary_union([make_valid(shape(f['geometry'])) for f in json.load(open(os.path.join(ROOT, 'assets', 'land.geojson')))['features']])
TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools')
cover = json.load(open(os.path.join(TOOLS, 'base_src', 'cover', 'cover_classes.geojson'), encoding='utf-8'))
C = {f['properties']['c']: make_valid(shape(f['geometry'])) for f in cover['features']}
_g = land0.buffer(-0.3).difference(unary_union(list(C.values())))  # داخل اليابسة، بعيدًا عن هامش الساحل
land_gap = max([p.area for p in getattr(_g, 'geoms', [_g])] or [0])
ok('no inland area left without a class (largest gap under 1.5 sq deg)', land_gap < 1.5, f'{land_gap:.2f}')
ok('cover has desert, steppe, forest, rainforest, taiga, tundra and ice', set('dsfrbti') <= set(C), str(sorted(C)))
at = lambda lon, lat: next((k for k, g in C.items() if g.contains(Point(lon, lat))), None)
ok('central Arabia (Najd) is desert', at(45, 24) == 'd', str(at(45, 24)))
ok('Rub al Khali is desert', at(50, 20) == 'd', str(at(50, 20)))
ok('Sahara is desert', at(10, 23) == 'd' and at(25, 25) == 'd')
ok('Antarctica is ice', at(0, -80) == 'i' and at(100, -75) == 'i')
ok('Greenland interior is ice', at(-40, 75) == 'i', str(at(-40, 75)))
ok('Amazon is rainforest', at(-62, -4) == 'r', str(at(-62, -4)))
ok('Siberia is taiga', at(100, 60) == 'b', str(at(100, 60)))
ok('cover classes do not overlap', all(C[a].intersection(C[b]).area < 0.05 for a in C for b in C if a < b))
import math
def tile(lon, lat, z):
    r = math.radians(lat); return z, int((lon + 180) / 360 * 2 ** z), int((1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * 2 ** z)
def peak(lon, lat, z=5):
    import numpy as np
    zz, x, y = tile(lon, lat, z); a = np.asarray(Image.open(os.path.join(ROOT, 'assets', 'dem', str(zz), str(x), f'{y}.png')).convert('RGB')).astype(float)
    return (a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768).max()
CT = glob.glob(os.path.join(ROOT, 'assets', 'cover', '*', '*', '*.webp'))
ok('cover raster tiles for zoom 0-5 (1365) present', len(CT) == 1365, str(len(CT)))
def px(lon, lat, z=4):
    zz, x, y = tile(lon, lat, z); im = Image.open(os.path.join(ROOT, 'assets', 'cover', str(zz), str(x), f'{y}.webp')).convert('RGBA')
    import math as _m; n = 2 ** zz; r = _m.radians(lat)
    u = int(((lon + 180) / 360 * n - x) * im.width); v = int(((1 - _m.log(_m.tan(r) + 1 / _m.cos(r)) / _m.pi) / 2 * n - y) * im.height)
    return im.getpixel((min(u, im.width - 1), min(v, im.height - 1)))
sand, forest, ice, sea = px(45, 23), px(10, 50), px(0, -78, 3), px(-35, 30)
ok('raster: Najd is sand-coloured, Germany green, Antarctica white, the Atlantic transparent', sand[0] > sand[2] + 40 and sand[3] == 255 and forest[1] > forest[0] and forest[1] > forest[2] and min(ice[:3]) > 220 and sea[3] == 0, str([sand, forest, ice, sea]))
ok('raster tiles are light (under 12 MB in total)', sum(os.path.getsize(p) for p in CT) < 12e6, str(round(sum(os.path.getsize(p) for p in CT) / 1e6, 1)))
ok('the old vector cover file is gone from the site', not os.path.exists(os.path.join(ROOT, 'assets', 'cover.geojson')))

ok('terrain covers the whole world: Andes, Rockies, Australia and the Himalaya have relief', peak(-70, -15) > 4000 and peak(-110, 40) > 2500 and peak(140, -30) > 300 and peak(87, 28) > 6000, str([round(peak(*q)) for q in [(-70, -15), (-110, 40), (140, -30), (87, 28)]]))
ok('all 1365 terrain tiles (zoom 0-5) present', len(glob.glob(os.path.join(ROOT, 'assets', 'dem', '*', '*', '*.png'))) == 1365)
land = unary_union([make_valid(shape(f['geometry'])) for f in json.load(open(os.path.join(ROOT, 'assets', 'land.geojson')))['features']])
worst_ov = worst_sea = 0; frames = 0
for p in glob.glob(os.path.join(ROOT, 'assets', 'borders', '*.json')):
    if not os.path.basename(p)[:-5].lstrip('-').isdigit(): continue
    d = json.load(open(p, encoding='utf-8')); G = [make_valid(shape(f['geometry'])) for f in d['features']]; frames += 1
    worst_ov = max(worst_ov, sum(a.intersection(b).area for i, a in enumerate(G) for b in G[i + 1:]))
    U = unary_union(G); worst_sea = max(worst_sea, U.difference(land).area / U.area)
    names = {f['properties']['n']: g for f, g in zip(d['features'], G)}
    bad = [l['n'] for l in d['labels'] if l['n'] in names and not names[l['n']].buffer(0.01).contains(Point(l['p']))]
    if bad: ok(f'labels inside their state in {os.path.basename(p)}', False, str(bad))
ok(f'no overlapping states in any of {frames} border frames', worst_ov < 0.1, f'{worst_ov:.2f}')
ok('borders stay on land (sea part under 1%)', worst_sea < 0.01, f'{worst_sea:.4f}')
b1932 = json.load(open(os.path.join(ROOT, 'assets', 'borders', '1932.json'), encoding='utf-8'))
ks = [f for f in b1932['features'] if f['properties']['n'] == 'المملكة العربية السعودية']
ok('1932: one Saudi kingdom (Hejaz, Najd, Hail and al-Jawf merged, no inner lines)', len(ks) == 1 and shape(ks[0]['geometry']).geom_type == 'Polygon' and ks[0]['properties'].get('civ') == 'saudi-kingdom')
k = make_valid(shape(ks[0]['geometry']))
ok('1932: kingdom covers Riyadh, Makkah, Hail, al-Jawf and Abha but not Kuwait or Amman', all(k.contains(Point(q)) for q in [(46.7, 24.6), (39.8, 21.4), (41.7, 27.5), (39.9, 29.8), (42.5, 18.2)]) and not k.contains(Point(47.98, 29.37)) and not k.contains(Point(35.9, 31.95)))
n1932 = {f['properties']['n'] for f in b1932['features']}
ok('1932: no out-of-time names (Ottoman Egypt, medieval Ghana, Hail emirate)', not n1932 & {'مصر (إيالة عثمانية)', 'مملكة غانا', 'الحجاز', 'إمارة حائل'} and 'مملكة مصر' in n1932, str(sorted(n1932)[:8]))
b900 = {f['properties']['n']: make_valid(shape(f['geometry'])) for f in json.load(open(os.path.join(ROOT, 'assets', 'borders', '900.json')))['features']}
ok('900: Khazars no longer cover Volga Bulgaria', b900['الخزر'].intersection(b900['بلغار الفولغا']).area < 0.01)

with sync_playwright() as p:
    br = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    for theme in ['terrain', 'dark']:
        ctx = br.new_context(viewport={'width': 1100, 'height': 800})
        ctx.add_init_script(f"localStorage.setItem('atlas-map-theme','{theme}');localStorage.setItem('atlas-coach-v1','1')")
        pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(B + '#/atlas?year=850')
        pg.wait_for_function("()=>window.__atlasMap&&__atlasMap.isSourceLoaded('land')", timeout=90000)
        pg.wait_for_timeout(5000); pg.evaluate("__atlasMap.stop();__atlasMap.jumpTo({center:[0,10],zoom:1.4})"); pg.wait_for_timeout(5000)
        ok(f'{theme}: cover layer shown and its tiles loaded', pg.evaluate("__atlasMap.getLayoutProperty('cover','visibility')==='visible'&&__atlasMap.isSourceLoaded('cover')"))
        q = pg.evaluate("()=>[[-20,35],[-31,35],[-20,5],[-31,5]].map(c=>{const a=__atlasMap.project(c);return [a.x,a.y]})")
        im = Image.open(io.BytesIO(pg.locator('#map').screenshot())).convert('RGB')
        px = [im.getpixel((int(x), int(y))) for x, y in q]
        ok(f'{theme}: sea has the same tone inside and outside the terrain area', max(abs(a - b) for a, b in zip(px[0], px[1])) <= 3 and max(abs(a - b) for a, b in zip(px[2], px[3])) <= 3, str(px))
        ok(f'{theme}: no page errors', not errs, str(errs[:2]))
        ctx.close()
    br.close()
print(f'TOTAL {sum(R)} / {len(R)}'); raise SystemExit(0 if all(R) else 1)
