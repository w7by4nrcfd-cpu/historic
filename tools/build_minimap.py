"""بيانات الخريطة الصغيرة في صفحات المواضيع: يابسة وبحيرات وأنهار مبسطة جدًا (Natural Earth من tools/base_src/).
الناتج dist/assets/minimap.json: كل شكل = [حدوده xmin,ymin,xmax,ymax، ثم الإحداثيات ×10 بفروق متتالية].
التشغيل: python3 tools/build_minimap.py"""
import gzip
import json
import os
from simplify_base import rdp, area  # noqa: E402  (الدوال نفسها)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, 'base_src'), os.path.join(HERE, '..', 'dist', 'assets', 'minimap.json')
EPS, MIN_AREA, RIVER_MIN = 0.06, 0.12, 3


def enc(pts):
    q = [(round(x * 10), round(y * 10)) for x, y in pts]
    out, px, py = [], 0, 0
    for x, y in q:
        if (x, y) == (px, py) and out:
            continue
        out += [x - px, y - py]
        px, py = x, y
    xs, ys = [p[0] for p in q], [p[1] for p in q]
    return [min(xs), min(ys), max(xs), max(ys)] + out


def rings(geom, closed):
    for part in geom['coordinates']:
        for k, r in enumerate(part if geom['type'] == 'MultiPolygon' else [part]):
            s = rdp([tuple(p[:2]) for p in r], EPS)
            if closed:
                if len(s) < 4 or area(s) < MIN_AREA:
                    if k == 0:
                        break
                    continue
            elif len(s) < 2 or sum(abs(s[i + 1][0] - s[i][0]) + abs(s[i + 1][1] - s[i][1]) for i in range(len(s) - 1)) < RIVER_MIN:
                continue
            yield enc(s)


land = json.load(open(os.path.join(SRC, 'land.geojson'), encoding='utf-8'))
water = json.load(open(os.path.join(SRC, 'water.geojson'), encoding='utf-8'))
L = [r for f in land['features'] for r in rings(f['geometry'], True)]
Lk = [r for f in water['features'] if f['geometry']['type'] == 'MultiPolygon' for r in rings(f['geometry'], True)]
R = [r for f in water['features'] if f['geometry']['type'] == 'MultiLineString' for r in rings(f['geometry'], False)]
j = json.dumps({'l': L, 'k': Lk, 'r': R}, separators=(',', ':'))
open(OUT, 'w').write(j)
print('land', len(L), '| lakes', len(Lk), '| rivers', len(R), '|', len(j) // 1024, 'KB |', len(gzip.compress(j.encode())) // 1024, 'KB gz')
