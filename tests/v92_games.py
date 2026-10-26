"""اختبارات V9.2: تحدي اليوم و«من أنا؟».
التشغيل: python3 -m http.server 8080 --directory dist ثم python3 tests/v92_games.py"""
import json, os
from playwright.sync_api import sync_playwright
B = os.environ.get('ATLAS_URL', 'http://localhost:8080/')
R = []
def ok(n, c, x=''):
    R.append(bool(c)); print(('PASS' if c else 'FAIL'), n, x)

def answer_all(pg, n, right=True):
    for k in range(n):
        pg.wait_for_selector('[data-opt]')
        key = pg.evaluate("()=>{const t=[...document.querySelectorAll('[data-opt]')];return t.map(b=>b.dataset.opt)}")
        # الإجابة الصحيحة تُعرف بعد الضغط؛ نضغط الأول ثم نقرأ صحة الإجابة
        pg.click('[data-opt]'); pg.wait_for_timeout(80)
        pg.click('[data-next-q]'); pg.wait_for_timeout(80)

with sync_playwright() as p:
    br = p.chromium.launch()
    ctx = br.new_context(viewport={'width': 390, 'height': 844}); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(B + '#/play'); pg.wait_for_selector('.game-card', timeout=15000); pg.wait_for_timeout(600)
    ok('games page: daily challenge first, then «من أنا؟»', pg.locator('a.game-card').nth(0).get_attribute('href') == '#/play/daily' and pg.locator('a.game-card').nth(1).get_attribute('href') == '#/play/who')
    G = '__atlasGames'
    ok('«من أنا؟» has at least 120 people', pg.evaluate(f'{G}.whoPool().length') >= 120, str(pg.evaluate(f'{G}.whoPool().length')))
    leak = pg.evaluate(f"""{G}.whoPool().filter(x=>{{const t=x.title.split(' (')[0].trim(),c={G}.whoClue(x);return c.includes(t)||t.split(/\\s+/).filter(w=>w.length>=4&&w!=='الدين').some(w=>c.includes(w))}}).map(x=>x.id)""")
    ok('no clue reveals the name', not leak, str(leak[:5]))
    same = pg.evaluate(f"JSON.stringify({G}.dailyQuestions('2026-10-27'))===JSON.stringify({G}.dailyQuestions('2026-10-27'))")
    diff = pg.evaluate(f"JSON.stringify({G}.dailyQuestions('2026-10-27'))!==JSON.stringify({G}.dailyQuestions('2026-10-28'))")
    ok('daily questions are the same within a day and change the next day', same and diff)
    bad = pg.evaluate(f"""(()=>{{const b=[];for(let d=1;d<=90;d++){{const dt=new Date(2026,10,d),day=`${{dt.getFullYear()}}-${{String(dt.getMonth()+1).padStart(2,'0')}}-${{String(dt.getDate()).padStart(2,'0')}}`;for(const q of {G}.dailyQuestions(day)){{if(new Set(q.options.map(o=>o.label)).size!==3||!q.options.some(o=>o.key===q.answer))b.push(day+q.kind)}}}}return b}})()""")
    ok('90 days of daily questions: 3 distinct options with the answer among them', not bad, str(bad[:3]))
    kinds = pg.evaluate(f"{G}.dailyQuestions('2026-10-27').map(q=>q.kind).join(',')")
    ok('daily mixes when, who and owner questions', kinds == 'when,who,owner,when,who', kinds)
    give = pg.evaluate(f"""(()=>{{let n=0;for(let d=1;d<=60;d++){{const q={G}.dailyQuestions('2026-12-'+String(d%28+1).padStart(2,'0'))[2];if(q.prompt.includes(q.options.find(o=>o.key===q.answer).label.split(' ').pop()))n++}}return n}})()""")
    ok('owner questions do not name their civilization in the title', give == 0, str(give))

    pg.goto(B + '#/play/daily'); pg.wait_for_selector('[data-opt]', timeout=15000)
    ok('daily: 5 questions', 'السؤال 1 من 5' in pg.inner_text('main'))
    pg.click('[data-opt]'); pg.wait_for_timeout(100)
    ok('daily: feedback with a link to the topic', pg.locator('.feedback a.text-link').count() == 1)
    pg.click('[data-next-q]'); answer_all(pg, 4)
    pg.wait_for_selector('.daily-squares', timeout=5000)
    ok('daily: result shows 5 squares and a share button', pg.locator('.daily-squares i').count() == 5 and pg.locator('[data-share]').count() == 1)
    g = pg.evaluate("()=>JSON.parse(localStorage.getItem('atlas-games'))")
    ok('daily: result, streak and day saved', g['daily']['streak'] == 1 and len(g['daily']['res']) == 5 and g['daily']['played'] == 1, json.dumps(g['daily']))
    pg.goto(B + '#/play'); pg.wait_for_timeout(300); pg.goto(B + '#/play/daily'); pg.wait_for_timeout(600)
    ok('daily: playing again the same day shows the result, not new questions', pg.locator('.daily-squares').count() == 1 and pg.locator('[data-opt]').count() == 0)
    # سلسلة الأيام: لعب أمس يرفع السلسلة إلى 2
    pg.evaluate("""()=>{const g=JSON.parse(localStorage.getItem('atlas-games'));const y=new Date();y.setDate(y.getDate()-1);g.daily.last=`${y.getFullYear()}-${String(y.getMonth()+1).padStart(2,'0')}-${String(y.getDate()).padStart(2,'0')}`;localStorage.setItem('atlas-games',JSON.stringify(g))}""")
    pg.goto(B + '#/play'); pg.wait_for_timeout(300); pg.goto(B + '#/play/daily'); pg.wait_for_selector('[data-opt]', timeout=5000)
    answer_all(pg, 5); pg.wait_for_selector('.daily-squares', timeout=5000)
    g = pg.evaluate("()=>JSON.parse(localStorage.getItem('atlas-games'))")
    ok('daily: playing on consecutive days builds the streak', g['daily']['streak'] == 2 and g['daily']['best'] == 2, json.dumps(g['daily']))
    pg.evaluate("()=>{window.__shared=null;Object.defineProperty(navigator,'share',{value:undefined,configurable:true});Object.defineProperty(navigator,'clipboard',{value:{writeText:t=>{window.__shared=t;return Promise.resolve()}},configurable:true})}")
    pg.click('[data-share]'); pg.wait_for_timeout(200)
    t = pg.evaluate('window.__shared') or ''
    ok('daily: share text has the squares, the streak and the link', sum(t.count(c) for c in '🟩🟥') == 5 and 'أيام متتالية' in t and '#/play/daily' in t, t)

    pg.goto(B + '#/play/who'); pg.wait_for_selector('[data-opt]', timeout=15000)
    ok('«من أنا؟»: 10 questions with a clue', 'السؤال 1 من 10' in pg.inner_text('main') and pg.inner_text('h2.who-clue').startswith('…'))
    answer_all(pg, 10); pg.wait_for_timeout(300)
    ok('«من أنا؟»: result screen', 'من 10' in pg.inner_text('.game-result'))
    pg.goto(B + '#/'); pg.wait_for_selector('.hero'); pg.wait_for_timeout(500)
    ok('home: games section shows the daily challenge and «من أنا؟»', pg.locator('a[href="#/play/daily"]').count() >= 1 and pg.locator('a[href="#/play/who"]').count() >= 1)
    ok('no horizontal scroll', not pg.evaluate('document.documentElement.scrollWidth>innerWidth+1'))
    ok('no page errors', not errs, str(errs[:2]))
    br.close()
print(f'TOTAL {sum(R)} / {len(R)}'); raise SystemExit(0 if all(R) else 1)
