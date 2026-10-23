"""تخفيف بيانات الخلفية (اليابسة والمياه والتضاريس) لتسريع تحميل الخريطة.
المصدر الكامل في tools/base_src/ (Natural Earth)، والناتج في dist/assets/.
التشغيل: python3 tools/simplify_base.py"""
import gzip, json, math, os, sys
sys.setrecursionlimit(100000)
HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, 'base_src'), os.path.join(HERE, '..', 'dist', 'assets')
# درجة التبسيط بالدرجات الجغرافية، وأصغر مساحة تُبقى (درجة مربعة). 0.04° ≈ 4 كم، أدق مما يظهر حتى التكبير 6
EPS, MIN_AREA = 0.04, 0.015


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    dm, ix = 0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / L if L else math.hypot(x - x1, y - y1)
        if d > dm:
            dm, ix = d, i
    return rdp(pts[:ix + 1], eps)[:-1] + rdp(pts[ix:], eps) if dm > eps else [pts[0], pts[-1]]


def area(r):
    return abs(sum(r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1] for i in range(len(r) - 1))) / 2


def poly(coords):
    out = []
    for p in coords:
        rings = []
        for k, r in enumerate(p):
            s = [[round(x, 2), round(y, 2)] for x, y in rdp([tuple(q[:2]) for q in r], EPS)]
            if len(s) >= 4 and area(s) > MIN_AREA:
                rings.append(s)
            elif k == 0:
                break
        if rings:
            out.append(rings)
    return out


def line(coords):
    out = []
    for l in coords:
        s = [[round(x, 2), round(y, 2)] for x, y in rdp([tuple(q[:2]) for q in l], EPS)]
        if len(s) >= 2:
            out.append(s)
    return out


if __name__ == '__main__':
    for f in ['land.geojson', 'water.geojson', 'physical.geojson']:
        d = json.load(open(os.path.join(SRC, f), encoding='utf-8'))
        feats = []
        for ft in d['features']:
            g = ft['geometry']
            c = poly(g['coordinates']) if g['type'] == 'MultiPolygon' else line(g['coordinates'])
            if c:
                feats.append({'type': 'Feature', 'properties': ft['properties'], 'geometry': {'type': g['type'], 'coordinates': c}})
        j = json.dumps({'type': 'FeatureCollection', 'features': feats}, ensure_ascii=False, separators=(',', ':'))
        open(os.path.join(OUT, f), 'w', encoding='utf-8').write(j)
        print(f, len(d['features']), '→', len(feats), 'features |', len(j) // 1024, 'KB |', len(gzip.compress(j.encode())) // 1024, 'KB gz')
