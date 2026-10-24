"""يبني طبقة الحدود التقريبية من مشروع historical-basemaps (GPL-3.0).
التشغيل: python3 tools/build_borders.py <مسار مجلد geojson في historical-basemaps>
الناتج: dist/assets/borders/<سنة اللقطة>.json — دول ذات اسم عربي فقط، مبسطة ومقصوصة على منطقة الأطلس.
"""
import json, math, os, sys
sys.setrecursionlimit(100000)
SRC = sys.argv[1]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist', 'assets', 'borders')
# سنة اللقطة في أطلس -> ملف البيانات وسنته المعروضة
FRAMES = {-500: ('bc500', -500), -400: ('bc400', -400), -323: ('bc323', -323), -300: ('bc300', -300), -200: ('bc200', -200), -100: ('bc100', -100),
          117: ('100', 100), 200: ('200', 200), 300: ('300', 300), 400: ('400', 400), 500: ('500', 500), 600: ('600', 600), 700: ('700', 700),
          850: ('800', 800), 900: ('900', 900), 1000: ('1000', 1000), 1100: ('1100', 1100), 1279: ('1279', 1279), 1300: ('1300', 1300),
          1400: ('1400', 1400), 1492: ('1492', 1492), 1500: ('1500', 1500), 1530: ('1530', 1530), 1600: ('1600', 1600), 1650: ('1650', 1650),
          1700: ('1700', 1700), 1750: ('1715', 1715), 1800: ('1800', 1800), 1880: ('1880', 1880), 1914: ('1914', 1914), 1932: ('1930', 1930)}
# لم نستعمل ملفات قبل 500 ق.م ولا ملف 1200: فيها دول في غير زمنها (الحيثيون ومملكة داود سنة 700 ق.م، والفاطميون والبويهيون والمغول سنة 1200،
# ووسط الأناضول بيزنطي فيه وكان للسلاجقة). وملف 1930 أخطاؤه في الأسماء فقط، فصُحّحت في ـ1930 أدناه (لقطة 1932).
TR = {
 'Aztec Empire': 'إمبراطورية الأزتك', 'Inca Empire': 'إمبراطورية الإنكا', 'Timurid Emirates': 'الإمارات التيمورية', 'Emirate of the White Sheep Turks': 'آق قويونلو',
 'Songhai': 'إمبراطورية سنغاي', 'Wattasid Caliphate': 'الدولة الوطاسية', 'Zayyanid Caliphate': 'الدولة الزيانية', 'Vijayanagara': 'إمبراطورية فيجاياناغارا', 'Bahmani Kingdom': 'السلطنة البهمنية', 'Grand Duchy of Moscow': 'دوقية موسكو الكبرى', 'Castille': 'قشتالة',
 'Mauryan Empire': 'الإمبراطورية الماورية', 'Qin': 'دولة تشين', 'Timurid Empire': 'الدولة التيمورية', 'Bactria': 'باختريا',
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
 'Polish–Lithuanian Commonwealth': 'بولندا وليتوانيا', 'Poland-Lithuania': 'بولندا وليتوانيا', 'Ming Chinese Empire': 'الصين (أسرة مينغ)', 'Watassid Morocco': 'المغرب', 'Crimean Khanate': 'خانية القرم', 'Adal': 'سلطنة عدل', 'England and Ireland': 'إنجلترا', 'Sweden': 'السويد', 'Vijayanagara': 'فيجاياناغارا', 'Venice': 'البندقية', 'Darfur': 'سلطنة دارفور',
}
# أسماء تخالف التسلسل التاريخي في نسخة معينة من البيانات، فنستبعدها
SKIP = {'bc100': {'Kushan Empire', 'Mauryan Empire'}, '1400': {'Great Khanate', 'Seljuk Caliphate', 'Chola Empire'},
        '1300': {'Grand Duchy of Moscow'}, '1600': {'Inca Empire', 'Songhai'}, '1715': {'Songhai'}}
CIV = {'Aztec Empire': 'aztecs', 'Inca Empire': 'inca', 'Timurid Emirates': 'timurids', 'Mauryan Empire': 'maurya', 'Timurid Empire': 'timurids', 'Achaemenid Empire': 'persia', 'Roman Republic': 'rome', 'Roman Empire': 'rome', 'Han Empire': 'china', 'Han': 'china',
       'Abbasid Caliphate': 'abbasid', 'Emirate of Córdoba': 'andalus', 'Caliphate of Córdoba': 'andalus', 'Nabatean Kingdom': 'nabataea',
       'Saba': 'saba', 'Mamluke Sultanate': 'mamluks', 'Ilkhanate': 'mongols', 'Khanate of the Golden Horde': 'mongols', 'Mongol Empire': 'mongols', 'Great Khanate': 'mongols', 'Chagatai Khanate': 'mongols',
       'Ottoman Empire': 'ottoman', 'Byzantine Empire': 'byzantine', 'Fatimid Caliphate': 'fatimids', 'Seljuk Caliphate': 'seljuks', 'Safavid Empire': 'safavids', 'Mughal Empire': 'mughals', 'Parthia': 'parthians', 'Parthian Empire': 'parthians', 'Mali': 'mali', 'Ming Chinese Empire': 'ming'}

TR.update({
 'Empire of Alexander': 'إمبراطورية الإسكندر', 'Magadha': 'مملكة مگدها', 'Zhou states': 'ممالك تشو', 'Cappadocia': 'قبادوقيا', 'Atropatene': 'أتروباتين',
 'Bosporan Kingdom': 'مملكة البوسفور', 'Rome': 'الجمهورية الرومانية', 'Carthage': 'قرطاج', 'Xiongnu': 'الشيونغنو', 'Macedon and Hellenic League': 'مقدونيا',
 'Kingdom of Syphax': 'مملكة سيفاكس', 'Saka Kingdom': 'مملكة الساكا', 'Satavahanihara': 'دولة الساتافاهانا', 'Jin': 'إمبراطورية جين',
 'Rome (Maximian)': 'الإمبراطورية الرومانية', 'Rome (Diocletianus)': 'الإمبراطورية الرومانية', 'Rome (Constantinus)': 'الإمبراطورية الرومانية',
 'Rome (Galerius)': 'الإمبراطورية الرومانية', 'Western Roman Empire': 'الإمبراطورية الرومانية الغربية', 'Eastern Roman Empire': 'الإمبراطورية الرومانية الشرقية',
 'Persia': 'الدولة الساسانية', 'Sasanian Empire': 'الدولة الساسانية', 'Gupta Empire': 'إمبراطورية غوبتا', 'Hunnic Empire': 'إمبراطورية الهون',
 'Ruanruan': 'خانية الروران', 'Ostrogoths': 'القوط الشرقيون', 'Visigoths': 'القوط الغربيون', 'Visigothic Kingdom': 'مملكة القوط الغربيين',
 'Vandals': 'الوندال', 'Franks': 'الفرنجة', 'Frankish Kingdom': 'مملكة الفرنجة', 'Toba Wei': 'دولة وي الشمالية',
 'Göktürks': 'الخاقانية التركية', 'Sui Empire': 'إمبراطورية سوي', 'Avars': 'الآفار', 'Hejaz': 'الحجاز', 'Lombard principalities': 'إمارات اللومبارديين',
 'Umayyad Caliphate': 'الدولة الأموية', 'Tufan Empire': 'الإمبراطورية التبتية', 'Kingdom of Sind': 'مملكة السند', 'Bulgars': 'البلغار',
 'Samanid Empire': 'الدولة السامانية', 'Saffarids': 'الصفاريون', 'East Francia': 'فرنجة الشرقية', 'West Francia': 'فرنجة الغربية', 'Volga Bulgars': 'بلغار الفولغا',
 'Seljuk Empire': 'الدولة السلجوقية', 'Almoravid dynasty': 'دولة المرابطين', 'Kievan Rus': 'روس كييف', 'Karkhanids': 'القراخانيون',
 'Merinides': 'الدولة المرينية', 'Abdelouadides': 'الدولة الزيانية', 'Kanem-Bornu': 'سلطنة كانم وبرنو',
 'Ming Empire': 'الصين (أسرة مينغ)', 'Golden Horde': 'القبيلة الذهبية', 'White Horde': 'القبيلة البيضاء', 'Bengal': 'سلطنة البنغال', 'Gujarat': 'سلطنة كجرات',
 'Funj': 'سلطنة الفونج', 'Nogai Horde': 'قبيلة النوغاي', 'Kazan Khanate': 'خانية قازان', 'Bukara Khanate': 'خانية بخارى', 'Astrakhan Khanate': 'خانية أستراخان',
 'Mahra': 'سلطنة المهرة', 'Russian Empire': 'الإمبراطورية الروسية', 'Qing Empire': 'إمبراطورية تشينغ', 'Afghanistan': 'أفغانستان',
 'Maratha Confederacy': 'اتحاد المراثا', 'Nejd': 'الدولة السعودية الأولى', 'Prussia': 'بروسيا', 'British Raj': 'الهند البريطانية',
 'Austria Hungary': 'النمسا والمجر', 'Austro-Hungarian Empire': 'النمسا والمجر', 'Germany': 'ألمانيا', 'German Empire': 'ألمانيا',
 'Algeria (FR)': 'الجزائر (فرنسية)', 'Algeria': 'الجزائر (فرنسية)', 'Italy': 'إيطاليا', 'Kingdom of Italy': 'إيطاليا', 'Sultanate of Zanzibar': 'سلطنة زنجبار',
 'Bokhara Khanate': 'إمارة بخارى', 'Greece': 'اليونان', 'Romania': 'رومانيا', 'Sokoto Caliphate': 'خلافة سوكوتو', 'Arabia (Nejd)': 'إمارة نجد (آل سعود)',
 'Anglo-Egyptian Sudan': 'السودان الإنجليزي المصري', 'Libya': 'ليبيا (إيطالية)', 'Abyssinia': 'الحبشة', 'Tunisia': 'تونس (فرنسية)', 'Bulgaria': 'بلغاريا',
 'Serbia': 'صربيا', 'Mongolia': 'منغوليا',
})
# أسماء تختلف بحسب السنة
YTR = {'300': {'Parthian Empire': 'الدولة الساسانية'}, '1300': {'Morocco': 'الدولة المرينية'}, '1400': {'Morocco': 'الدولة المرينية'}, '1530': {'Watassid Morocco': 'الدولة الوطاسية'}, '1800': {'Persia': 'إيران (القاجاريون)'}, '1880': {'Persia': 'إيران (القاجاريون)', 'Egypt': 'مصر (الخديوية)'},
       '1914': {'Persia': 'إيران (القاجاريون)', 'Egypt': 'مصر', 'Eastern Roman Empire': 'الإمبراطورية البيزنطية'},
       '700': {'Eastern Roman Empire': 'الإمبراطورية البيزنطية'}, '600': {'Eastern Roman Empire': 'الإمبراطورية البيزنطية'}}
SKIP.update({
 'bc500': {'Hindu kingdoms'}, '300': {'Gupta Empire', 'Satavahanihara', 'Suren Kingdom', 'Hadramaut'},
 '400': {'Meroe', 'Hadramaut', 'Jin'}, '500': {'Meroe', 'Hadramaut', 'Western Roman Empire', 'Jin Empire'},
 '700': {'Sasanian Empire', 'Sui Empire', 'Hejaz', 'Western Gokturk Khaganate'}, '900': {'Carolingian Empire', 'Tibetan Empire'},
 '1914': {'Manchu Empire'},
})
CIV.update({'Rome': 'rome', 'Rome (Maximian)': 'rome', 'Rome (Diocletianus)': 'rome', 'Rome (Constantinus)': 'rome', 'Rome (Galerius)': 'rome', 'Umayyad Caliphate': 'umayyad', 'Sasanian Empire': 'sasanian', 'Persia': 'sasanian', 'Seljuk Empire': 'seljuks', 'Eastern Roman Empire': 'byzantine',
            'Nejd': 'first-saudi', 'Arabia (Nejd)': 'saudi-kingdom', 'Empire of Alexander': 'greece', 'Ming Empire': 'ming', 'Golden Horde': 'mongols'})
for k, v in {'bc400': {'Xiongnu'}, 'bc200': {'Kingdom of Syphax'}, '400': {'Satavahanihara'}, '600': {'Ostrogoths'}, '800': {'Avars'},
             '900': {'Avars'}, '1650': {'Vijayanagara', 'Songhai'}, '1700': {'Vijayanagara', 'Songhai'}, '1800': {'Songhai'}, '1914': {'Georgia', 'Armenia'}}.items():
    SKIP[k] = set(SKIP.get(k, set())) | v
YCIV = {'300': {'Parthian Empire': 'sasanian'}, '1800': {'Persia': None}, '1880': {'Persia': None}, '1914': {'Persia': None}}
# لقطة 1932 من ملف 1930: تصحيح الأسماء، وتوحيد أجزاء المملكة (الحجاز وحائل ونجد والجوف) كما كانت سنة 1932
YTR['1930'] = {
    'Hejaz': 'المملكة العربية السعودية', 'Hail': 'المملكة العربية السعودية', "Emirate of Bin Shal'an": 'المملكة العربية السعودية',
    'Egypt': 'مملكة مصر', 'Iran': 'إيران (البهلوية)', 'Republic of Turkey': 'الجمهورية التركية',
    'Mesopotamia (GB)': 'العراق وشرق الأردن (انتداب بريطاني)', 'Syria (France)': 'سوريا ولبنان (انتداب فرنسي)', 'Mandatory Palestine (GB)': 'فلسطين (انتداب بريطاني)',
    'Yemen': 'المملكة المتوكلية اليمنية', 'Muscat and Oman': 'سلطنة مسقط وعمان', 'Trucial Oman': 'الإمارات المتصالحة', 'Qatar': 'قطر',
    'Sudan': 'السودان الإنجليزي المصري', 'Libya (IT)': 'ليبيا (إيطالية)', 'Eritrea': 'إريتريا (إيطالية)', 'Morocco': 'المغرب (حماية فرنسية)',
    'White Russia': 'الاتحاد السوفيتي', 'Armenia': 'أرمينيا السوفيتية', 'Georgia': 'جورجيا السوفيتية', 'Azerbaijan': 'أذربيجان السوفيتية',
    'Yugoslavia': 'يوغوسلافيا', 'Poland': 'بولندا', 'Austria': 'النمسا', 'Czechoslovakia': 'تشيكوسلوفاكيا', 'Albania': 'ألبانيا',
    'United Kingdom of Great Britain and Ireland': 'المملكة المتحدة', 'Chinese Warlords': 'الصين (الجمهورية)', 'Tibet': 'التبت',
    'Empire of Japan': 'اليابان', 'Rattanakosin Kingdom': 'سيام', 'French Indo-China': 'الهند الصينية الفرنسية',
}
SKIP['1930'] = set(SKIP.get('1930', set())) | {'Ghana', 'Xinjiang', 'Manchuria', 'Far Eastern SSR'}  # غانا القديمة في غير زمنها، ومناطق بلا دولة واضحة
YCIV['1930'] = {'Hejaz': 'saudi-kingdom', 'Hail': 'saudi-kingdom', "Emirate of Bin Shal'an": 'saudi-kingdom', 'Egypt': None, 'Iran': None}
UNNAMED_1930_SAUDI = (36, 27, 44, 33)  # المنطقة الشمالية بلا اسم في الملف (الجوف ووادي السرحان)، وكانت تحت حكم الملك عبدالعزيز منذ 1922–1925
RDP_EPS = float(os.environ.get('RDP_EPS', 0.05))  # دقة تبسيط الحدود بالدرجات
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


AMERICAS = {'Aztec Empire', 'Inca Empire'}


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
        if fname == '1930' and n is None and g:
            from shapely.geometry import shape as _sh
            _c = _sh(g).representative_point(); W_, S_, E_, N_ = UNNAMED_1930_SAUDI
            if W_ < _c.x < E_ and S_ < _c.y < N_:
                n = 'Hail'
        if not g or (n not in TR and n not in YTR.get(fname, {})) or n in SKIP.get(fname, ()):  # أسماء ـYTR خاصة بسنتها
            continue
        ar_name = YTR.get(fname, {}).get(n, TR.get(n))
        polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        for poly in polys:
            outer = poly[0]
            if not in_region(outer) and n not in AMERICAS:
                continue
            rings = []
            for k, r in enumerate(poly):
                s = [[round(x, 2), round(y, 2)] for x, y in rdp([tuple(p[:2]) for p in r], RDP_EPS)]
                if len(s) >= 4 and ring_area(s) > 0.15:
                    rings.append(s)
                elif k == 0:
                    break
            if rings:
                gr = groups.setdefault(ar_name, {'src': n, 'polys': [], 'bp': 1})
                gr['polys'].append(rings)
                gr['bp'] = max(gr['bp'], int((ft['properties'] or {}).get('BORDERPRECISION') or 1))
    feats, labels = [], []
    for i, (ar, gr) in enumerate(sorted(groups.items(), key=lambda kv: -sum(ring_area(p[0]) for p in kv[1]['polys']))):
        color = None
        civ = YCIV.get(fname, {}).get(gr['src'], CIV.get(gr['src']))
        h = sum(map(ord, gr['src']))
        color = PAL[h % len(PAL)]
        polys = gr['polys']
        tot = sum(ring_area(p[0]) for p in polys)
        big = max(polys, key=lambda p: ring_area(p[0]))
        lp = label_point([tuple(x) for x in big[0]])
        feats.append({'type': 'Feature', 'properties': {'n': ar, 'c': color, 'bp': gr['bp'], **({'civ': civ} if civ else {})},
                      'geometry': {'type': 'MultiPolygon', 'coordinates': polys}})
        z = 0 if tot > 120 else 1 if tot > 20 else 2
        labels.append({'n': ar, 'p': [round(lp[0], 2), round(lp[1], 2)], 'z': z, **({'civ': civ} if civ else {})})
    out = {'year': dyear, 'type': 'FeatureCollection', 'features': feats, 'labels': labels}
    path = os.path.join(OUT, f'{frame}.json')
    json.dump(out, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(frame, fname, len(feats), os.path.getsize(path) // 1024, 'KB', [l['n'] for l in labels][:12])
from clean_borders import clean_all  # إزالة التداخل والقص على اليابسة (tools/clean_borders.py)
clean_all(OUT)
index = {}
for frame in sorted(FRAMES):
    dd = json.load(open(os.path.join(OUT, f'{frame}.json'), encoding='utf-8'))
    index[str(frame)] = [l['n'] for l in dd['labels']]
civmap = {}
for frame in sorted(FRAMES):
    for l in json.load(open(os.path.join(OUT, f'{frame}.json'), encoding='utf-8'))['labels']:
        if l.get('civ'):
            civmap[l['n']] = l['civ']
json.dump({'frames': sorted(FRAMES), 'names': index, 'civ': civmap}, open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
open(os.path.join(OUT, 'LICENSE.txt'), 'w', encoding='utf-8').write(
    'Derived from historical-basemaps by André Ourednik and contributors\n'
    'https://github.com/aourednik/historical-basemaps\n'
    'License: GNU GPL v3.0 — https://www.gnu.org/licenses/gpl-3.0.html\n'
    'Changes: clipped to the ATLAS region, simplified (RDP 0.12°), filtered to named polities, Arabic names added.\n'
    'The source project is work in progress; borders are approximate.\n')
