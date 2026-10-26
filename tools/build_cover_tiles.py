"""بلاطات صور لغطاء الأرض (صحراء، سهوب، غابات، تندرا، جليد) بانتقالات ناعمة وملمس خفيف، بدل المضلعات الملوّنة ذات الحواف الحادة.
المدخلات: فئات الغطاء من tools/build_cover.py (tools/base_src/cover/cover_classes.geojson) واليابسة dist/assets/land.geojson.
الخطوات لكل بلاطة (مركاتور، المستويات 0–5):
  1) ترسم كل فئة في قناع، وما بقي من اليابسة بلا فئة (هامش الساحل) يأخذ أقرب فئة إليه.
  2) حدود غير منتظمة بين الفئات (إزاحة بضجيج)، ولون كل فئة مع تفاوت واسع وحبيبات دقيقة من ضجيج متصل بين البلاطات،
     والصحراء بين رمل فاتح ورمل محمر.
  3) تنعيم الألوان (Gaussian) بقدر نحو 30 كم على الأرض، فتتدرج الصحراء إلى السهوب ثم الغابات.
  4) الشفافية من قناع اليابسة نفسه (بلا تنعيم)، فيبقى خط الساحل حادًّا.
الناتج dist/assets/cover/{z}/{x}/{y}.webp، وبلاطات البحر الخالص صورة شفافة 1×1.
التشغيل: python3 tools/build_cover_tiles.py"""
import json
import math
import os
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
CLASSES = os.path.join(HERE, 'base_src', 'cover', 'cover_classes.geojson')
LAND = os.path.join(HERE, '..', 'dist', 'assets', 'land.geojson')
OUT = os.path.join(HERE, '..', 'dist', 'assets', 'cover')
MAXZ, T, SS = 5, 256, 2
ORDER = ['s', 'm', 'f', 'r', 'b', 't', 'd', 'i']
PAL = np.array([[0, 0, 0],            # 0: بلا فئة (لا يبقى بعد الملء)
                [186, 178, 122],      # s سهوب وسافانا
                [166, 163, 112],      # m شجيرات المتوسط
                [106, 133, 84],       # f غابات معتدلة وجافة
                [80, 116, 66],        # r غابات مطيرة
                [100, 125, 98],       # b تايغا
                [170, 175, 154],      # t تندرا
                [216, 191, 140],      # d صحراء
                [241, 244, 247]], float)  # i جليد
WORLD_KM = 40075.0


def merc(lon, lat):
    lat = np.clip(lat, -85.0511, 85.0511)
    x = (lon + 180) / 360
    r = np.radians(lat)
    y = (1 - np.log(np.tan(r) + 1 / np.cos(r)) / math.pi) / 2
    return x, y


def rings_of(geom):
    polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    out = []
    for poly in polys:
        rs = []
        for r in poly:
            a = np.asarray(r, float)
            x, y = merc(a[:, 0], a[:, 1])
            rs.append(np.stack([x, y], 1))
        out.append((rs, (rs[0][:, 0].min(), rs[0][:, 1].min(), rs[0][:, 0].max(), rs[0][:, 1].max())))
    return out


C = {f['properties']['c']: rings_of(f['geometry']) for f in json.load(open(CLASSES, encoding='utf-8'))['features']}
L = [p for f in json.load(open(LAND, encoding='utf-8'))['features'] for p in rings_of(f['geometry'])]


def draw(polys, z, x, y, pad, size):
    im = Image.new('L', (size, size), 0)
    d = ImageDraw.Draw(im)
    n = 2 ** z
    x0, y0, x1, y1 = (x - pad / T) / n, (y - pad / T) / n, (x + 1 + pad / T) / n, (y + 1 + pad / T) / n
    hit = False
    for rs, (bx0, by0, bx1, by1) in polys:
        if bx1 < x0 or bx0 > x1 or by1 < y0 or by0 > y1:
            continue
        for k, r in enumerate(rs):
            px = ((r[:, 0] * n - x) * T + pad) * SS
            py = ((r[:, 1] * n - y) * T + pad) * SS
            if len(px) >= 3:
                d.polygon(list(zip(px.tolist(), py.tolist())), fill=0 if k else 255)
                hit = True
    return np.asarray(im) > 127 if hit else None


def vnoise(gx, gy, cell, seed):
    """ضجيج قيمي متصل بين البلاطات: شبكة عالمية من قيم عشوائية ثابتة (من تجزئة الإحداثيات) مع استيفاء ناعم."""
    fx, fy = gx / cell, gy / cell
    ix, iy = np.floor(fx).astype(np.int64), np.floor(fy).astype(np.int64)
    tx, ty = fx - ix, fy - iy
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    def h(i, j):
        v = (i * 374761393 + j * 668265263 + seed * 2147483647) & 0xFFFFFFFF
        v = ((v ^ (v >> 13)) * 1274126177) & 0xFFFFFFFF
        return (v & 0xFFFF) / 32767.5 - 1
    a, b, c, d = h(ix, iy), h(ix + 1, iy), h(ix, iy + 1), h(ix + 1, iy + 1)
    return (a + (b - a) * tx) + ((c + (d - c) * tx) - (a + (b - a) * tx)) * ty


def fbm(gx, gy, seed, cells=(96, 48, 24, 12, 6), amps=(.42, .26, .16, .1, .06)):
    return sum(a * vnoise(gx, gy, c, seed + i) for i, (c, a) in enumerate(zip(cells, amps)))


def texture(z, x, y, pad, size):
    g = (np.arange(size) / SS - pad)
    gx = (x * T + g[None, :]) * np.ones((size, 1))
    gy = (y * T + g[:, None]) * np.ones((1, size))
    return gx, gy


def tile(job):
    z, x, y = job
    path = os.path.join(OUT, str(z), str(x), f'{y}.webp')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sigma = max(1.0, 30.0 / (WORLD_KM / (T * 2 ** z)))  # نحو 30 كم بالبكسل
    pad = int(math.ceil(3 * sigma)) + 2
    size = (T + 2 * pad) * SS
    land = draw(L, z, x, y, pad, size)
    inner = slice(pad * SS, (pad + T) * SS)
    if land is None or not land[inner, inner].any():
        Image.new('RGBA', (1, 1), (0, 0, 0, 0)).save(path, 'WEBP', lossless=True)
        return 0
    cls = np.zeros((size, size), np.uint8)
    for i, k in enumerate(ORDER, 1):
        m = draw(C.get(k, []), z, x, y, pad, size)
        if m is not None:
            cls[m] = i
    if (cls == 0).any() and (cls > 0).any():  # هامش الساحل وما لا فئة له: أقرب فئة
        idx = ndimage.distance_transform_edt(cls == 0, return_distances=False, return_indices=True)
        cls = cls[idx[0], idx[1]]
    elif not (cls > 0).any():
        cls[:] = ORDER.index('t' if (y / 2 ** z) < .2 else 's') + 1
    gx, gy = texture(z, x, y, pad, size)
    # حدود غير منتظمة بين الفئات: إزاحة نقاط القراءة بضجيج (بقدر التنعيم تقريبًا) قبل التلوين
    w = 2.2 * sigma * SS
    rr, cc = np.mgrid[0:size, 0:size].astype(float)
    cls = ndimage.map_coordinates(cls, [np.clip(rr + w * fbm(gx, gy, 11), 0, size - 1), np.clip(cc + w * fbm(gx, gy, 23), 0, size - 1)], order=0)
    rgb = PAL[cls]
    lo = fbm(gx, gy, 5, cells=(160, 80), amps=(.65, .35))      # تفاوت واسع في درجة اللون داخل المنطقة الواحدة
    fine = fbm(gx, gy, 41, cells=(12, 6, 3), amps=(.5, .3, .2))  # حبيبات دقيقة
    desert = cls == ORDER.index('d') + 1
    sand_hi, sand_lo = np.array([231, 207, 158.]), np.array([196, 160, 112.])
    mix = np.clip(.5 + .55 * lo, 0, 1)[..., None]
    rgb = np.where(desert[..., None], sand_lo + (sand_hi - sand_lo) * mix, rgb)
    rgb = rgb * (1 + 0.05 * lo + 0.03 * fine)[..., None]
    s = sigma * SS
    rgb = np.stack([ndimage.gaussian_filter(rgb[..., c], s) for c in range(3)], -1)
    a = land.astype(float) * 255
    img = np.dstack([np.clip(rgb, 0, 255), a])[inner, inner].astype(np.uint8)
    Image.fromarray(img, 'RGBA').resize((T, T), Image.LANCZOS).save(path, 'WEBP', quality=82, alpha_quality=90, method=6)
    return os.path.getsize(path)


if __name__ == '__main__':
    jobs = [(z, x, y) for z in range(MAXZ + 1) for x in range(2 ** z) for y in range(2 ** z)]
    with Pool(os.cpu_count() or 2) as p:
        sizes = p.map(tile, jobs, chunksize=8)
    print('tiles', len(sizes), '| with land', sum(1 for s in sizes if s), '| MB', round(sum(sizes) / 1e6, 1))
