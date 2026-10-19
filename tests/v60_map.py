"""اختبارات V6: لقطات الحدود الجديدة وبطاقات الدول.
التشغيل: python3 -m http.server 8080 --directory dist ثم python3 tests/v60_map.py"""
import glob, json, os, re
from playwright.sync_api import sync_playwright
B = os.environ.get('ATLAS_URL', 'http://localhost:8080/')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist')
R = []
def ok(n, c, x=''):
    R.append(bool(c)); print(('PASS' if c else 'FAIL'), n, x)

core = open(os.path.join(ROOT, 'core.mjs'), encoding='utf-8').read()
FRAMES = [int(x) for x in re.search(r'export const FRAMES=\[([^\]]*)\]', core).group(1).split(',')]
app = open(os.path.join(ROOT, 'app.js'), encoding='utf-8').read()
BY = [int(x) for x in re.search(r'BORDER_YEARS=\[([^\]]*)\]', app).group(1).split(',')]
ok('36 frames, sorted', len(FRAMES) == 36 and FRAMES == sorted(FRAMES), str(len(FRAMES)))
ok('30 border snapshots, each a frame with a file', len(BY) == 30 and all(y in FRAMES and os.path.exists(os.path.join(ROOT, 'assets', 'borders', f'{y}.json')) for y in BY))
ok('frames without trustworthy data stay without borders', not {-1750, -1400, 650, 1200, 1850, 1932} & set(BY))

P = json.load(open(os.path.join(ROOT, 'assets', 'polities.json'), encoding='utf-8'))
labels = {}
for f in [f for f in glob.glob(os.path.join(ROOT, 'assets', 'borders', '*.json')) if not f.endswith('index.json')]:
    d = json.load(open(f, encoding='utf-8'))
    ok(f'{os.path.basename(f)}: every polygon has a name and colour', all(ft['properties'].get('n') and ft['properties'].get('c') for ft in d['features']))
    for l in d['labels']:
        labels.setdefault(l['n'], set()).add(d['year'])
missing = [n for n in labels if 't' not in P.get(n, {}) and not any(l.get('civ') for f in [f for f in glob.glob(os.path.join(ROOT, 'assets', 'borders', '*.json')) if not f.endswith('index.json')] for l in json.load(open(f, encoding='utf-8'))['labels'] if l['n'] == n)]
ok('every state without an encyclopedia page has a card', not missing, str(missing))
ok('every card has period, capital and text', all(p['d'] and p['cap'] and len(p['t']) > 30 for p in P.values() if 't' in p) and sum('t' in p for p in P.values()) == 138)
# أخطاء زمنية استُبعدت عمدًا
y = lambda n: labels.get(n, set())
ok('no Sasanians after 651', not [v for v in y('الدولة الساسانية') if v > 651])
ok('no Fatimids after 1171', not [v for v in y('الخلافة الفاطمية') if v > 1171])
ok('no Songhai after 1591', not [v for v in y('إمبراطورية سنغاي') if v > 1591])
ok('Umayyads drawn in 700', 700 in y('الدولة الأموية'))
ok('First Saudi state drawn in 1800', 1800 in y('الدولة السعودية الأولى'))

ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS)
    for name, vp in [('desktop', {'width': 1280, 'height': 860}), ('mobile', {'width': 390, 'height': 844})]:
        pg = b.new_page(viewport=vp); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(B + '#/atlas?year=1279'); pg.wait_for_timeout(5000)
        if pg.locator('.ax-coach-ok').is_visible(): pg.click('.ax-coach-ok')
        ok(f'{name}: 1279 frame shows its own borders', 'حدود تقريبية لعام 1279' in pg.inner_text('#map-tag'), pg.inner_text('#map-tag'))
        # الضغط على دولة لا صفحة لها: الحفصيون (تونس)
        pt = pg.evaluate("()=>{const m=window.__atlasMap;m.jumpTo({center:[9.5,35.5],zoom:5});return null}")
        pg.wait_for_timeout(1500)
        pos = pg.evaluate("()=>{const m=window.__atlasMap,q=m.project([9.0,34.6]),r=m.getContainer().getBoundingClientRect();return [r.left+q.x,r.top+q.y]}")
        pg.mouse.click(pos[0], pos[1]); pg.wait_for_timeout(1500)
        sel = pg.inner_text('#map-selection')
        ok(f'{name}: clicking a state without a page shows its card', 'الدولة الحفصية' in sel and 'العاصمة' in sel and 'تونس' in sel, sel[:120])
        # التنقل بين اللقطات الجديدة يعمل
        pg.evaluate("()=>document.querySelector('[data-frame-move=\"1\"]').click()"); pg.wait_for_timeout(2500)  # على الجوال تغطي اللوحة المفتوحة الشريط
        ok(f'{name}: next frame after 1279 is 1300', pg.inner_text('#year-label') == '1300 م', pg.inner_text('#year-label'))
        # ما الذي تغيّر: من 600 إلى 700 (بينهما 650 بلا حدود)
        pg.goto(B + '#/atlas?year=600'); pg.wait_for_timeout(4500)
        for _ in range(2):
            pg.evaluate("()=>document.querySelector('[data-frame-move=\"1\"]').click()"); pg.wait_for_timeout(1500)
        chg = pg.inner_text('.sum-chg') if pg.locator('.sum-chg').count() else ''
        ok(f'{name}: change box compares 700 with 600', 'منذ 600' in chg, chg[:80])
        ok(f'{name}: Umayyads listed first among new states', chg.split('ظهرت')[-1].strip().startswith('الدولة الأموية'), chg)
        ok(f'{name}: Sasanians listed as gone', 'الدولة الساسانية' in chg.split('اختفت')[-1])
        ok(f'{name}: new states glow on the map', pg.evaluate("()=>{const m=window.__atlasMap;return JSON.stringify(m.getFilter('border-new')).includes('الدولة الأموية')}"))
        if name == 'mobile':
            ok('mobile: change pill shown above the map', pg.locator('#ax-chg-pill:visible').count() == 1 and 'ظهرت' in pg.inner_text('#ax-chg-pill'))
        # 900 ← 1000: العباسيون لم يسقطوا سنة 1000 رغم غيابهم عن بيانات تلك السنة
        pg.goto(B + '#/atlas?year=900'); pg.wait_for_timeout(4500)
        pg.evaluate("()=>document.querySelector('[data-frame-move=\"1\"]').click()")
        for _ in range(20):  # البيئة بطيئة الرسم: ننتظر حتى 5 ثوانٍ
            pg.wait_for_timeout(250)
            if pg.locator('.sum-chg').count(): break
        chg = pg.inner_text('.sum-chg') if pg.locator('.sum-chg').count() else ''
        ok(f'{name}: data gaps are not reported as falls (Abbasids in 1000)', 'الخلافة العباسية' not in chg and 'الخلافة الفاطمية' in chg, chg[:120])
        ok(f'{name}: no page errors', not errs, str(errs))
        pg.close()
    b.close()
print(f'TOTAL {sum(R)} / {len(R)}'); raise SystemExit(0 if all(R) else 1)
