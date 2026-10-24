"""طبقة غطاء الأرض في الخريطة: صحارى وسهوب وغابات وتندرا وجليد، بدل لون أخضر واحد لكل اليابسة.
المصادر (في tools/base_src/cover/):
- biomes.geojson: المناطق الحيوية من RESOLVE Ecoregions 2017 (Dinerstein وآخرون 2017، رخصة CC BY 4.0)،
  مدموجة حسب المنطقة الحيوية ومبسطة في مشروع biome-atlas (github.com/jplaney/biome-atlas).
- ne_50m_glaciated_areas وne_50m_antarctic_ice_shelves_polys: Natural Earth (ملكية عامة).
- والقارة القطبية الجنوبية (جنوب خط 60° جنوبًا) كلها جليد، فـRESOLVE لا يغطيها.
الناتج dist/assets/cover.geojson: معلم لكل فئة، والخاصية c:
  d صحراء وشبه صحراء، s سهوب وسافانا وأعشاب، m شجيرات البحر المتوسط، f غابات معتدلة وجافة،
  r غابات مطيرة، b غابات شمالية (تايغا)، t تندرا، i جليد.
التشغيل: python3 tools/build_cover.py"""
import gzip
import json
import os
from shapely.geometry import shape, mapping, box
from shapely.ops import unary_union
from shapely.validation import make_valid

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'base_src', 'cover')
LAND = os.path.join(HERE, '..', 'dist', 'assets', 'land.geojson')
OUT = os.path.join(HERE, '..', 'dist', 'assets', 'cover.geojson')
EPS, IN, MIN_AREA, ND = float(os.environ.get('EPS', .15)), float(os.environ.get('IN', .1)), float(os.environ.get('MIN', .3)), 2

CLASS = {
    'Deserts & Xeric Shrublands': 'd',
    'Temperate Grasslands, Savannas & Shrublands': 's', 'Tropical & Subtropical Grasslands, Savannas & Shrublands': 's',
    'Montane Grasslands & Shrublands': 's', 'Flooded Grasslands & Savannas': 's',
    'Mediterranean Forests, Woodlands & Scrub': 'm',
    'Temperate Broadleaf & Mixed Forests': 'f', 'Temperate Conifer Forests': 'f', 'Tropical & Subtropical Coniferous Forests': 'f',
    'Tropical & Subtropical Dry Broadleaf Forests': 'f', 'Mangroves': 'r',
    'Tropical & Subtropical Moist Broadleaf Forests': 'r',
    'Boreal Forests/Taiga': 'b', 'Tundra': 't',
}
ORDER = ['s', 'm', 'f', 'r', 'b', 't', 'd', 'i']  # الجليد آخرًا فيغطي ما تحته


def geoms(path, pick=lambda p: True):
    for f in json.load(open(path, encoding='utf-8'))['features']:
        if f.get('geometry') and pick(f['properties']):
            yield make_valid(shape(f['geometry']))


def rnd(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], ND), round(c[1], ND)]
    return [rnd(x) for x in c]


land = unary_union(list(geoms(LAND))).buffer(0)
groups = {k: [] for k in ORDER}
for name, k in CLASS.items():
    groups[k] += list(geoms(os.path.join(SRC, 'biomes.geojson'), lambda p, n=name: p['biome'] == n))
groups['i'] += list(geoms(os.path.join(SRC, 'ne_50m_glaciated_areas.geojson')))
groups['i'] += list(geoms(os.path.join(SRC, 'ne_50m_antarctic_ice_shelves_polys.geojson')))
groups['i'].append(box(-180, -90, 180, -60))

# 1) كل فئة كما هي في المصدر، مقصوصة على اليابسة
raw = {k: unary_union(groups[k]).buffer(0).intersection(land) for k in ORDER}
# 2) ثغرات المصدر: مناطق يابسة سقطت من ملف المناطق الحيوية (منها وسط نجد والربع الخالي وأجزاء من الصحراء الكبرى والأمازون).
#    كل ثغرة تأخذ فئة المنطقة المحيطة بها (الفئة الأوسع حضورًا على حافتها)، ولا يُترك شيء من اليابسة بلا فئة.
gap = land.difference(unary_union(list(raw.values())))
fill = {k: [] for k in ORDER}
for p in getattr(gap, 'geoms', [gap]):
    if p.geom_type != 'Polygon' or p.area < 0.01:
        continue
    ring = p.buffer(0.3).difference(p)
    best = max(ORDER, key=lambda k: raw[k].intersection(ring).area)
    if raw[best].intersection(ring).area > 0:
        fill[best].append(p)
raw = {k: unary_union([raw[k]] + fill[k]).buffer(0) for k in ORDER}
# 3) قناع ساحلي داخل اليابسة بقليل: يُقص عليه كل شيء مرة واحدة فلا يخرج اللون إلى البحر
mask = land.buffer(-IN).simplify(IN * 0.6, preserve_topology=True).buffer(0)
feats, taken = [], None
for k in reversed(ORDER):  # الأعلى أولًا (الجليد ثم الصحراء...)، وكل فئة يُطرح منها ما أخذته التي قبلها فلا تتداخل
    # تبسيط ثم تمدد يسير، فتتلاقى الفئات المتجاورة بلا شقوق بينها، ثم القص على القناع الساحلي
    g = raw[k].simplify(EPS, preserve_topology=True).buffer(-EPS * 0.4, join_style=1, quad_segs=2).buffer(EPS, join_style=1, quad_segs=2).intersection(mask).simplify(0.03, preserve_topology=True)  # تدوير الزوايا
    if taken is not None:
        g = g.difference(taken)
    g = g.buffer(0)
    taken = g if taken is None else unary_union([taken, g])
    parts = [p for p in getattr(g, 'geoms', [g]) if p.geom_type == 'Polygon' and p.area >= MIN_AREA]
    if not parts:
        continue
    m = mapping(unary_union(parts))  # بلا تبسيط بعد الطرح، فلا تتداخل الفئات
    feats.append({'type': 'Feature', 'properties': {'c': k}, 'geometry': {'type': m['type'], 'coordinates': rnd(m['coordinates'])}})
feats.sort(key=lambda f: ORDER.index(f['properties']['c']))
j = json.dumps({'type': 'FeatureCollection', 'features': feats}, separators=(',', ':'), ensure_ascii=False)
open(OUT, 'w', encoding='utf-8').write(j)
print(' | '.join(f['properties']['c'] for f in feats), '|', len(j) // 1024, 'KB |', len(gzip.compress(j.encode())) // 1024, 'KB gz')
