"""تنظيف طبقة الحدود بعد بنائها (tools/build_borders.py يستدعيها، ويمكن تشغيلها وحدها).
- التداخل بين دولتين: المنطقة المشتركة تبقى للدولة الأصغر مساحة، وتُطرح من الأكبر.
  (مثل الخزر سنة 900: كان مضلعهم في المصدر يغطي أجزاء من بلغار الفولغا وروس كييف.)
- القص على اليابسة: لا تمتد الدول فوق البحار (مع هامش صغير يلاقي خط الساحل المرسوم).
- إذا خرجت نقطة اسم الدولة من مضلعها بعد القص، تُحسب من جديد داخل أكبر أجزائها.
لا تُضاف حدود جديدة: كل ما يُفعل طرحٌ من المضلعات الموجودة في المصدر.
التشغيل: python3 tools/clean_borders.py [مجلد الحدود]"""
import glob
import json
import os
import sys
from shapely.geometry import shape, mapping, Point
from shapely.ops import unary_union, polylabel
from shapely.validation import make_valid

HERE = os.path.dirname(os.path.abspath(__file__))
LAND = os.path.join(HERE, '..', 'dist', 'assets', 'land.geojson')
COAST_PAD, LAND_EPS, MIN_PART, ND = 0.04, 0.03, 0.05, 2


def polys(g):
    g = make_valid(g)
    out = [p for p in getattr(g, 'geoms', [g]) if p.geom_type == 'Polygon']
    for p in getattr(g, 'geoms', []):
        if p.geom_type in ('MultiPolygon', 'GeometryCollection'):
            out += polys(p)
    return out


def rnd(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], ND), round(c[1], ND)]
    return [rnd(x) for x in c]


def landmask():
    land = unary_union([make_valid(shape(f['geometry'])) for f in json.load(open(LAND, encoding='utf-8'))['features']])
    return land.simplify(LAND_EPS).buffer(COAST_PAD).buffer(0)


def clean_frame(path, mask):
    d = json.load(open(path, encoding='utf-8'))
    F = d['features']
    G = [unary_union(polys(shape(f['geometry']))) for f in F]
    order = sorted(range(len(F)), key=lambda i: G[i].area)
    done, out = [], {}
    for i in order:  # الأصغر أولًا: كل دولة تُطرح منها مساحات الدول الأصغر التي تداخلها
        g = G[i].intersection(mask)
        hit = [h for h in done if h.intersects(g)]
        if hit:
            g = g.difference(unary_union(hit))
        parts = [p for p in polys(g) if p.area >= MIN_PART]
        g = unary_union(parts) if parts else None
        out[i] = g
        if g is not None:
            done.append(g)
    feats = []
    names = {}
    for i, f in enumerate(F):
        g = out[i]
        if g is None:
            continue
        m = mapping(g)
        feats.append({**f, 'geometry': {'type': m['type'], 'coordinates': rnd(m['coordinates'])}})
        names[f['properties']['n']] = g
    labels = []
    for l in d.get('labels', []):
        g = names.get(l['n'])
        if g is None:
            continue
        if not g.contains(Point(l['p'])):
            big = max(polys(g), key=lambda p: p.area)
            q = polylabel(big, 0.05)
            l = {**l, 'p': [round(q.x, 2), round(q.y, 2)]}
        labels.append(l)
    d['features'], d['labels'] = feats, labels
    json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    return len(F) - len(feats)


def clean_all(folder):
    mask = landmask()
    for p in sorted(glob.glob(os.path.join(folder, '*.json'))):
        if os.path.basename(p)[:-5].lstrip('-').isdigit():
            gone = clean_frame(p, mask)
            print('clean', os.path.basename(p), os.path.getsize(p) // 1024, 'KB', f'({gone} removed)' if gone else '')


if __name__ == '__main__':
    clean_all(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'dist', 'assets', 'borders'))
