"""ينزّل بلاطات الارتفاعات المفتوحة (Terrain Tiles من AWS Open Data، صيغة terrarium) لمنطقة الأطلس،
ويقلل دقتها قليلًا لتصغير الحجم، ويحفظها في dist/assets/dem/{z}/{x}/{y}.png لتُقرأ محليًا دون خدمة خارجية.
المصدر: https://registry.opendata.aws/terrain-tiles/ (يتطلب ذكر المصادر: Mapzen وUSGS وغيرها).
التشغيل: python3 tools/build_dem.py [المجلد]
"""
import io, math, os, sys, urllib.request
import numpy as np
from PIL import Image

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist', 'assets', 'dem')
W, S, E, N = -25, -12, 145, 64
MAXZ = 5
URL = 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'


def tx(lon, z):
    return int((lon + 180) / 360 * 2 ** z)


def ty(lat, z):
    r = math.radians(lat)
    return int((1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * 2 ** z)


n = size = 0
for z in range(0, MAXZ + 1):
    for x in range(tx(W, z), tx(E, z) + 1):
        for y in range(ty(N, z), ty(S, z) + 1):
            raw = urllib.request.urlopen(URL.format(z=z, x=x, y=y), timeout=60).read()
            a = np.asarray(Image.open(io.BytesIO(raw)).convert('RGB')).astype(np.float64)
            h = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
            h = np.where(h < 0, 0, h)                      # البحر مستوٍ: نحتاج تضاريس اليابسة فقط
            q = np.round(h / 8) * 8 + 32768                 # دقة 8 أمتار تكفي للظلال وتصغّر الملف
            r = np.floor(q / 256)
            g = q - r * 256
            img = np.stack([r, g, np.zeros_like(r)], -1).astype(np.uint8)
            d = os.path.join(OUT, str(z), str(x))
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, f'{y}.png')
            Image.fromarray(img, 'RGB').save(p, optimize=True)
            n += 1; size += os.path.getsize(p)
print('tiles', n, 'MB', round(size / 1e6, 1))
