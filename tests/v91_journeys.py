"""اختبارات V9.1: الرحلات التعليمية (13 رحلة، أغلبها 7 محطات).
التشغيل: python3 -m http.server 8080 --directory dist ثم python3 tests/v91_journeys.py"""
import json, os, subprocess
from playwright.sync_api import sync_playwright
B = os.environ.get('ATLAS_URL', 'http://localhost:8080/')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist')
R = []
def ok(n, c, x=''):
    R.append(bool(c)); print(('PASS' if c else 'FAIL'), n, x)

J = json.loads(subprocess.run(['node', '-e', f"import('{ROOT}/journeys.mjs').then(m=>console.log(JSON.stringify(m.JOURNEYS)))"], capture_output=True, text=True).stdout)
d = json.load(open(os.path.join(ROOT, 'content.json'), encoding='utf-8'))
by = {x['id']: x for x in d['civilizations'] + d['entries']}
ok('13 journeys', len(J) == 13, str(len(J)))
ok('10 journeys have 7 stops', sum(len(j['steps']) == 7 for j in J) == 10)
ok('every stop links to a real page and civilization', all((s.get('topic') or s['civ']) in by and s['civ'] in by for j in J for s in j['steps']))
ok('every stop has a question with 3 options and a valid answer', all(len(s['options']) == 3 and 0 <= s['answer'] < 3 and s['explanation'] for j in J for s in j['steps']))
ok('correct answers are spread over the three positions', min([a for j in J for a in [s['answer'] for s in j['steps']]].count(k) for k in range(3)) >= 15)
ok('no stop repeats a topic within its journey', all(len({s.get('topic') or s['title'] for s in j['steps']}) == len(j['steps']) for j in J))
ok('four featured journeys, the Saudi one first', [j['id'] for j in J if j.get('featured')] == ['saudi', 'prophet', 'andalus', 'crusades'])

with sync_playwright() as p:
    br = p.chromium.launch()
    for name, vp in [('mobile', {'width': 390, 'height': 844}), ('desktop', {'width': 1280, 'height': 860})]:
        ctx = br.new_context(viewport=vp); pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(B + '#/journeys'); pg.wait_for_selector('.journey-card', timeout=15000)
        ok(f'{name}: journeys page lists all 13', pg.locator('a.journey-card[href^="#/journey/"]').count() == 13)
        ok(f'{name}: cards show their stop count', '7 محطات' in pg.inner_text('main') and '3 محطات' in pg.inner_text('main'))
        pg.goto(B + '#/'); pg.wait_for_selector('.hero', timeout=15000); pg.wait_for_timeout(500)
        ok(f'{name}: home shows the 4 featured journeys only', pg.locator('a.journey-card[href^="#/journey/"]').count() == 4 and 'قصة الدولة السعودية' in pg.inner_text('main'))
        j = next(x for x in J if x['id'] == 'prophet'); n = len(j['steps'])
        pg.goto(B + '#/journey/prophet'); pg.wait_for_selector('.lesson-card', timeout=15000)
        ok(f'{name}: badge counts 7 stops', f'1 / {n}' in pg.inner_text('.badge'))
        link = pg.locator('a:has-text("استكشف موقعه")').get_attribute('href')
        ok(f'{name}: map link goes to the stop place and year', link == '#/atlas?topic=hijra-622&year=622', link)
        for k, s in enumerate(j['steps']):
            pg.click(f'[data-journey-answer="{(s["answer"] + 1) % 3}"]'); pg.wait_for_timeout(120)
            if k < n - 1 and k in (0, 3):
                ok(f'{name}: stop {k + 1} wrong answer keeps next locked', pg.locator('[data-next]').is_disabled())
            pg.click(f'[data-journey-answer="{s["answer"]}"]'); pg.wait_for_timeout(120)
            if k < n - 1:
                pg.click('[data-next]'); pg.wait_for_timeout(150)
        ok(f'{name}: last stop shows journey complete', 'أتممت الرحلة' in pg.inner_text('.journey-actions'))
        pg.reload(); pg.wait_for_timeout(800)
        st = pg.evaluate("()=>JSON.parse(localStorage.getItem('atlas-v1')).journeys.prophet")
        ok(f'{name}: all 7 stops saved after reload', sorted(st['done']) == list(range(n)), json.dumps(st))
        pg.goto(B + '#/journeys'); pg.wait_for_timeout(600)
        ok(f'{name}: card shows 7/7 progress', '7/7' in pg.locator('.journey-card', has_text='من مكة إلى المدينة').inner_text())
        ok(f'{name}: no horizontal scroll', not pg.evaluate('document.documentElement.scrollWidth>innerWidth+1'))
        ok(f'{name}: no page errors', not errs, str(errs[:2]))
        ctx.close()
    br.close()
print(f'TOTAL {sum(R)} / {len(R)}'); raise SystemExit(0 if all(R) else 1)
