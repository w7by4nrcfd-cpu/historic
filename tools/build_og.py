"""بطاقة مشاركة لكل صفحة موضوع (1200×630): خريطة المكان من بلاطات غطاء الأرض في الموقع نفسه، وعليها العنوان والسنة أو الفترة ونوع الموضوع.
تظهر حين يُرسل رابط الصفحة (t/<المعرّف>/) في واتساب أو تويتر أو غيرهما بدل الصورة العامة للموقع.
- المكان: إحداثيات الموضوع، وإن لم تكن له (أغلب الشخصيات) فإحداثيات حضارته، بلا علامة.
- النص يُرسم في متصفح (Playwright) بخط الموقع، فيُشكَّل العربي تشكيلًا صحيحًا.
الناتج dist/og/<المعرّف>.jpg. التشغيل: python3 tools/build_og.py"""
import base64
import io
import json
import math
import os
import sys

from PIL import Image, ImageEnhance
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', 'dist')
OUT = os.path.join(ROOT, 'og')
W, H, T = 1200, 630, 256
OCEAN = (21, 52, 78)
sys.path.insert(0, HERE)
TYPES = {'civilization': 'حضارة ودولة', 'city': 'مدينة', 'person': 'شخصية', 'event': 'حدث', 'science': 'علوم واكتشافات'}

d = json.load(open(os.path.join(ROOT, 'content.json'), encoding='utf-8'))
civs = d['civilizations']
items = civs + d['entries']


def civ_of(x):  # كما في build_pages.py
    if x['type'] == 'civilization':
        return x
    for c in civs:
        if c['cityId'] == x['id'] or any(p['id'] == x['id'] for p in c['people']) or any(e['id'] == x['id'] for e in c['events']):
            return c
    for c in civs:
        if c['id'] in (x.get('relatedIds') or []):
            return c
    return None


def tag(x):  # السنة أو الفترة كما في عناوين الصفحات
    if x['type'] == 'event' and x.get('year') is not None:
        y = x['year']
        return f'{-y} ق.م' if y < 0 else f'{y} م'
    p = x.get('period') or x.get('dateLabel') or ''
    return p if len(p) <= 34 else ''


def world_px(lon, lat, z):
    lat = max(-85, min(85, lat))
    r = math.radians(lat)
    return (lon + 180) / 360 * T * 2 ** z, (1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * T * 2 ** z


def background(lon, lat, z, at=(390, 330)):
    """خريطة 1200×630 من بلاطات assets/cover، والمكان عند النقطة at (يسار البطاقة، فالنص على اليمين)."""
    cx, cy = world_px(lon, lat, z)
    x0, y0 = cx - at[0], cy - at[1]
    img = Image.new('RGB', (W, H), OCEAN)
    n = 2 ** z
    for tx in range(int(x0 // T), int((x0 + W) // T) + 1):
        for ty in range(int(y0 // T), int((y0 + H) // T) + 1):
            if not 0 <= ty < n:
                continue
            p = os.path.join(ROOT, 'assets', 'cover', str(z), str(tx % n), f'{ty}.webp')
            if not os.path.exists(p):
                continue
            t = Image.open(p).convert('RGBA')
            if t.size != (T, T):
                continue
            img.paste(t, (int(tx * T - x0), int(ty * T - y0)), t)
    img = ImageEnhance.Brightness(ImageEnhance.Color(img).enhance(.9)).enhance(.8)  # قريب من النمط الداكن
    b = io.BytesIO()
    img.save(b, 'JPEG', quality=90)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()


FONT = 'data:font/woff;base64,' + base64.b64encode(open(os.path.join(ROOT, 'assets', 'arabic.woff'), 'rb').read()).decode()
CSS = """@font-face{font-family:A;src:url(FONTURL)}*{margin:0;box-sizing:border-box}
body{width:1200px;height:630px;overflow:hidden;font-family:A,sans-serif;color:#f3ead8;background:#0b1220}
.bg{position:absolute;inset:0;background-size:cover}
.sh{position:absolute;inset:0;background:linear-gradient(270deg,rgba(8,13,22,.96) 0%,rgba(8,13,22,.88) 38%,rgba(8,13,22,.25) 70%,rgba(8,13,22,.05) 100%),
radial-gradient(ellipse at 30% 50%,transparent 40%,rgba(8,13,22,.55) 100%)}
.pin{position:absolute;left:372px;top:312px;width:36px;height:36px;border-radius:50%;background:#e2c27c;box-shadow:0 0 0 8px rgba(226,194,124,.28),0 0 34px 10px rgba(226,194,124,.5)}
.txt{position:absolute;right:64px;top:0;bottom:0;width:640px;display:flex;flex-direction:column;justify-content:center;direction:rtl;text-align:right}
.eb{font-size:27px;color:#cfb584;letter-spacing:.5px;margin-bottom:18px}
h1{font-size:72px;line-height:1.22;font-weight:700;margin-bottom:18px;text-wrap:balance}
h1.l{font-size:58px}h1.xl{font-size:48px}
.tag{display:inline-block;align-self:flex-start;font-size:32px;color:#0b1220;background:#d8bd8b;border-radius:10px;padding:4px 18px 8px;margin-bottom:22px}
.sum{font-size:27px;line-height:1.55;color:#c9cfd9;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.brand{position:absolute;left:44px;bottom:34px;direction:rtl;font-size:30px;color:#e9d6ac}
.brand small{display:block;font-size:19px;color:#9aa8ba;margin-top:2px}""".replace("FONTURL", FONT)


def card_html(x, bg, pin):
    c = civ_of(x)
    # اسم الحضارة إلا إذا كان الحدث قبل قيامها (غزوة بدر قبل الخلافة الراشدة مثلًا)
    before = x.get('year') is not None and c and c.get('startYear') is not None and x['year'] < c['startYear']
    eb = TYPES.get(x['type'], '') + (f' · {c["title"]}' if c and c is not x and not before else '')
    t = tag(x)
    cls = 'xl' if len(x['title']) > 34 else 'l' if len(x['title']) > 20 else ''
    e = lambda s: (s or '').replace('&', '&amp;').replace('<', '&lt;')
    return (f'<!doctype html><meta charset="utf-8"><style>{CSS}</style><div class="bg" style="background-image:url({bg})"></div><div class="sh"></div>'
            + ('<div class="pin"></div>' if pin else '')
            + f'<div class="txt"><div class="eb">{e(eb)}</div><h1 class="{cls}">{e(x["title"])}</h1>'
            + (f'<div class="tag">{e(t)}</div>' if t else '')
            + f'<div class="sum">{e(x.get("summary"))}</div></div><div class="brand">✧ أطلس<small>اكتشف العالم عبر الزمن</small></div>')


def main():
    os.makedirs(OUT, exist_ok=True)
    only = set(sys.argv[1:])
    total = 0
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={'width': W, 'height': H})
        for x in items:
            if only and x['id'] not in only:
                continue
            c = civ_of(x)
            co = x.get('coordinates') or (c or {}).get('coordinates') or [40, 28]
            z = 5 if x['type'] in ('city', 'event') else 4
            pg.set_content(card_html(x, background(co[0], co[1], z), bool(x.get('coordinates'))))
            pg.evaluate('document.fonts.ready')
            path = os.path.join(OUT, f'{x["id"]}.jpg')
            pg.screenshot(path=path, type='jpeg', quality=78)
            total += os.path.getsize(path)
        br.close()
    print('cards', len(os.listdir(OUT)), '| MB', round(total / 1e6, 1))


if __name__ == '__main__':
    main()
