"""يبني طبقة الحدود التقريبية من مشروع historical-basemaps (GPL-3.0).
التشغيل: python3 tools/build_borders.py <مسار مجلد geojson في historical-basemaps>
الناتج: dist/assets/borders/<سنة اللقطة>.json — دول ذات اسم عربي فقط، مبسطة ومقصوصة على منطقة الأطلس.
"""
import json, math, os, sys
sys.setrecursionlimit(100000)
SRC = sys.argv[1]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist', 'assets', 'borders')
# سنة اللقطة في أطلس -> ملف البيانات وسنته المعروضة
FRAMES = {-400: ('bc400', -400), -100: ('bc100', -100), 117: ('100', 100), 850: ('800', 800),
          1000: ('1000', 1000), 1300: ('1300', 1300), 1750: ('1715', 1715)}
TR = {
 'Achaemenid Empire': 'الإمبراطورية الأخمينية', 'Carthaginian Empire': 'قرطاج', 'Greek city-states': 'المدن اليونانية', 'Kush': 'مملكة كوش',
 'Seleucid Kingdom': 'المملكة السلوقية', 'Roman Republic': 'الجمهورية الرومانية', 'Ptolemaic Kingdom': 'مملكة البطالمة', 'Meroe': 'مملكة مروي',
 'Parthia': 'الفرثيون', 'Numidia': 'نوميديا', 'Mauretania': 'موريطنية', 'Qataban': 'قتبان', 'Maan': 'معين', 'Nabatean Kingdom': 'مملكة الأنباط',
 'Hadramaut': 'حضرموت', 'Saba': 'سبأ', 'Han Empire': 'إمبراطورية هان', 'Han': 'إمبراطورية هان',
 'Roman Empire': 'الإمبراطورية الرومانية', 'Parthian Empire': 'الإمبراطورية الفرثية', 'Himyarite Kingdom': 'مملكة حمير', 'Armenia': 'أرمينيا',
 'Axum': 'مملكة أكسوم', 'Kushan Empire': 'الإمبراطورية الكوشانية',
 'Abbasid Caliphate': 'الخلافة العباسية', 'Khazars': 'الخزر', 'Carolingian Empire': 'الإمبراطورية الكارولنجية', 'Byzantine Empire': 'الإمبراطورية البيزنطية',
 'Aghlabid Emirate': 'الأغالبة', 'Makkura': 'مملكة المقرة', 'Idrisid Caliphate': 'الأدارسة', 'Emirate of Córdoba': 'إمارة قرطبة', 'Alwa': 'مملكة علوة',
 'Tang Empire': 'إمبراطورية تانغ', 'Tibetan Empire': 'الإمبراطورية التبتية', 'Asturias': 'أستورياس',
 'Buwayhid Emirates': 'البويهيون', 'Buyid Emirate': 'البويهيون', 'Fatimid Caliphate': 'الخلافة الفاطمية', 'Ghaznavid Emirate': 'الغزنويون',
 'Holy Roman Empire': 'الإمبراطورية الرومانية المقدسة', 'Caliphate of Córdoba': 'خلافة قرطبة', 'Kingdom of France': 'فرنسا', 'France': 'فرنسا',
 'Song Empire': 'إمبراطورية سونغ', 'Yemen': 'اليمن', 'Muscat': 'عُمان', 'Oman': 'عُمان', 'Kingdom of Georgia': 'جورجيا', 'Georgia': 'جورجيا',
 'León': 'ليون', 'Ghana': 'مملكة غانا', 'Mali': 'مملكة مالي', 'Kyivan Rus': 'روس كييف',
 'Khanate of the Golden Horde': 'القبيلة الذهبية', 'Ilkhanate': 'الدولة الإلخانية', 'Mamluke Sultanate': 'سلطنة المماليك', 'Hafsid Caliphate': 'الدولة الحفصية',
 'Hungary': 'المجر', 'Seljuk Caliphate': 'سلاجقة الروم', 'Castile': 'قشتالة', 'Ethiopia': 'الحبشة', 'Morocco': 'المغرب', 'Aragón': 'أراغون',
 'Portugal': 'البرتغال', 'Granada': 'غرناطة', 'Mongol Empire': 'دولة المغول (يوان)', 'Great Khanate': 'الخانية الكبرى (يوان)', 'Chagatai Khanate': 'خانية جغطاي', 'Liao': 'دولة لياو', 'Xixia': 'شيا الغربية', 'Sultanate of Delhi': 'سلطنة دلهي',
 'Ottoman Empire': 'الدولة العثمانية', 'Safavid Empire': 'الدولة الصفوية', 'Quazaq Khanate': 'خانية القازاق', 'Khiva Khanate': 'خانية خيوة',
 'Egypt': 'مصر (إيالة عثمانية)', 'Austrian Empire': 'النمسا', 'Spain': 'إسبانيا', 'Algiers': 'إيالة الجزائر', 'Tunis': 'إيالة تونس',
 'Tripolitania': 'طرابلس الغرب', 'Mughal Empire': 'الدولة المغولية في الهند', 'Manchu Empire': 'إمبراطورية تشينغ', 'Tsardom of Muscovy': 'روسيا القيصرية',
 'Polish–Lithuanian Commonwealth': 'بولندا وليتوانيا', 'Venice': 'البندقية', 'Darfur': 'سلطنة دارفور',
}
# أسماء تخالف التسلسل التاريخي في نسخة معينة من البيانات، فنستبعدها
SKIP = {'bc100': {'Kushan Empire'}}
CIV = {'Achaemenid Empire': 'persia', 'Roman Republic': 'rome', 'Roman Empire': 'rome', 'Han Empire': 'china', 'Han': 'china',
       'Abbasid Caliphate': 'abbasid', 'Emirate of Córdoba': 'andalus', 'Caliphate of Córdoba': 'andalus', 'Nabatean Kingdom': 'nabataea',
       'Saba': 'saba', 'Mamluke Sultanate': 'mamluks', 'Ilkhanate': 'mongols', 'Khanate of the Golden Horde': 'mongols', 'Mongol Empire': 'mongols', 'Great Khanate': 'mongols', 'Chagatai Khanate': 'mongols',
       'Ottoman Empire': 'ottoman'}
PAL = ['#8c7a5b', '#6f8f8a', '#9a6f6f', '#7d7aa3', '#a08c5a', '#6c8f6a', '#9c7aa0', '#5f8aa3', '#a3866f', '#7a9a5f']


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    dmax, idx = 0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / L if L else math.hypot(x - x1, y - y1)
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        return rdp(pts[:idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]


def ring_area(r):
    return abs(sum(r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1] for i in range(len(r) - 1))) / 2


def inside(pt, ring):
    x, y = pt
    c = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def label_point(ring):
    A = cx = cy = 0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
        f = x0 * y1 - x1 * y0
        A += f; cx += (x0 + x1) * f; cy += (y0 + y1) * f
    if A:
        p = (cx / (3 * A), cy / (3 * A))
        if inside(p, ring):
            return p
    xs = [x for x, _ in ring]; ys = [y for _, y in ring]
    best, bd = None, -1
    for i in range(1, 12):
        for j in range(1, 12):
            p = (min(xs) + (max(xs) - min(xs)) * i / 12, min(ys) + (max(ys) - min(ys)) * j / 12)
            if inside(p, ring):
                d = min(math.hypot(p[0] - a, p[1] - b) for a, b in ring[::max(1, len(ring) // 60)])
                if d > bd:
                    best, bd = p, d
    return best or ring[0]


def in_region(ring):
    xs = [x for x, _ in ring]; ys = [y for _, y in ring]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    return -25 < cx < 140 and -10 < cy < 62


os.makedirs(OUT, exist_ok=True)
for frame, (fname, dyear) in FRAMES.items():
    d = json.load(open(os.path.join(SRC, f'world_{fname}.geojson'), encoding='utf-8'))
    groups = {}
    for ft in d['features']:
        g = ft['geometry']
        n = (ft['properties'] or {}).get('NAME')
        if not g or n not in TR or n in SKIP.get(fname, ()):
            continue
        polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        for poly in polys:
            outer = poly[0]
            if not in_region(outer):
                continue
            rings = []
            for k, r in enumerate(poly):
                s = [[round(x, 2), round(y, 2)] for x, y in rdp([tuple(p[:2]) for p in r], 0.12)]
                if len(s) >= 4 and ring_area(s) > 0.15:
                    rings.append(s)
                elif k == 0:
                    break
            if rings:
                groups.setdefault(TR[n], {'src': n, 'polys': []})['polys'].append(rings)
    feats, labels = [], []
    for i, (ar, gr) in enumerate(sorted(groups.items(), key=lambda kv: -sum(ring_area(p[0]) for p in kv[1]['polys']))):
        color = None
        civ = CIV.get(gr['src'])
        h = sum(map(ord, gr['src']))
        color = PAL[h % len(PAL)]
        polys = gr['polys']
        tot = sum(ring_area(p[0]) for p in polys)
        big = max(polys, key=lambda p: ring_area(p[0]))
        lp = label_point([tuple(x) for x in big[0]])
        feats.append({'type': 'Feature', 'properties': {'n': ar, 'c': color, **({'civ': civ} if civ else {})},
                      'geometry': {'type': 'MultiPolygon', 'coordinates': polys}})
        z = 0 if tot > 120 else 1 if tot > 20 else 2
        labels.append({'n': ar, 'p': [round(lp[0], 2), round(lp[1], 2)], 'z': z, **({'civ': civ} if civ else {})})
    out = {'year': dyear, 'type': 'FeatureCollection', 'features': feats, 'labels': labels}
    path = os.path.join(OUT, f'{frame}.json')
    json.dump(out, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(frame, fname, len(feats), os.path.getsize(path) // 1024, 'KB', [l['n'] for l in labels][:12])
open(os.path.join(OUT, 'LICENSE.txt'), 'w', encoding='utf-8').write(
    'Derived from historical-basemaps by André Ourednik and contributors\n'
    'https://github.com/aourednik/historical-basemaps\n'
    'License: GNU GPL v3.0 — https://www.gnu.org/licenses/gpl-3.0.html\n'
    'Changes: clipped to the ATLAS region, simplified (RDP 0.12°), filtered to named polities, Arabic names added.\n'
    'The source project is work in progress; borders are approximate.\n')
