"""اختبارات V5 للخريطة: التعليمات، لوحة الطبقات، شريط العصور، هرمية الوسوم، تحديد الدول.
التشغيل: python3 -m http.server 8080 --directory dist ثم python3 tests/v5_map.py"""
import os
from playwright.sync_api import sync_playwright

B = os.environ.get('ATLAS_URL', 'http://localhost:8080/')
R = []


def ok(name, cond, extra=''):
    R.append(bool(cond))
    print(('PASS' if cond else 'FAIL'), name, extra)


ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']

with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS)
    for name, vp in [('mobile', {'width': 390, 'height': 844}), ('desktop', {'width': 1440, 'height': 900})]:
        ctx = b.new_context(viewport=vp)
        pg = ctx.new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(B + '#/atlas?year=1300')
        pg.wait_for_timeout(4500)

        # التعليمات: تظهر في الزيارة الأولى وتختفي بعد «فهمت» ولا تعود بعد التحديث
        ok(f'{name}: coach shown on first visit', pg.locator('#ax-coach').is_visible())
        pg.click('.ax-coach-ok')
        ok(f'{name}: coach dismissed', not pg.locator('#ax-coach').is_visible())
        pg.reload()
        pg.wait_for_timeout(3500)
        ok(f'{name}: coach stays dismissed after reload', not pg.locator('#ax-coach').is_visible())
        pg.click('#ax-help-btn')
        ok(f'{name}: help button reopens coach', pg.locator('#ax-coach').is_visible())
        pg.keyboard.press('Escape')
        ok(f'{name}: Escape closes coach', not pg.locator('#ax-coach').is_visible())

        # لوحة الطبقات
        ok(f'{name}: layers panel closed by default', not pg.locator('#ax-panel').is_visible())
        pg.click('#ax-layers-btn')
        ok(f'{name}: layers panel opens', pg.locator('#ax-panel').is_visible() and pg.get_attribute('#ax-layers-btn', 'aria-expanded') == 'true')
        ok(f'{name}: legend lists civilizations of the frame', pg.locator('#map-legend a').count() >= 3, str(pg.locator('#map-legend a').count()))
        ok(f'{name}: symbol key present', pg.locator('.ax-key span').count() == 6)
        pg.keyboard.press('Escape')
        ok(f'{name}: Escape closes panel', not pg.locator('#ax-panel').is_visible())

        # ملخص اللقطة
        side = pg.inner_text('#map-selection')
        ok(f'{name}: side summary shows frame and counts', 'العالم في 1300' in side and 'دولة' in side, side[:40])

        # شريط العصور
        ok(f'{name}: active era segment highlighted', pg.locator('.era-seg.active').count() == 1)
        if name == 'desktop':  # على الجوال الشريط إشارة لونية فقط، والتنقل بالمنزلق
            pg.locator('.era-seg').first.click()
            pg.wait_for_timeout(1500)
            ok('desktop: era strip jumps to first era', pg.inner_text('#ax-era-name') == 'العالم القديم', pg.inner_text('#ax-era-name'))
        pg.goto(B + '#/')
        pg.wait_for_timeout(500)
        pg.goto(B + '#/atlas?year=1300')
        pg.wait_for_timeout(4000)

        # هرمية الوسوم
        ev_hidden = pg.evaluate("()=>[...document.querySelectorAll('.map-point.event span')].every(s=>getComputedStyle(s).display==='none')")
        ok(f'{name}: event titles hidden until hover/select', ev_hidden)
        pg.locator('.map-point.kind-battle').first.click(force=True)
        pg.wait_for_timeout(900)
        ok(f'{name}: selected event shows its title', pg.evaluate("()=>{const s=document.querySelector('.map-point.is-sel span');return !!s&&getComputedStyle(s).display!=='none'}"))
        ok(f'{name}: event timing sentence', 'قبل هذه اللقطة بنحو' in pg.inner_text('#map-selection'))
        ls = pg.evaluate("()=>[...document.querySelectorAll('.border-label,.geo-label')].map(e=>getComputedStyle(e).letterSpacing)")
        ok(f'{name}: no letter-spacing on Arabic map labels', all(x in ('normal', '0px') for x in ls), str(set(ls)))
        ok(f'{name}: kashida on sea labels', pg.evaluate("()=>[...document.querySelectorAll('.geo-w')].some(e=>e.textContent.includes('ـ'))"))

        # تحديد دولة بالضغط
        pg.keyboard.press('Escape')
        box = pg.locator('#map').bounding_box()
        clicked = False
        if name == 'mobile':
            pg.click('.ax-handle')
            pg.wait_for_timeout(500)
        pg.wait_for_timeout(800)
        pts = pg.evaluate("""()=>{const top=document.querySelector('.ax-era').getBoundingClientRect().bottom+10,dock=document.querySelector('.ax-dock').getBoundingClientRect().top-10;return [...document.querySelectorAll('.border-label')].filter(e=>getComputedStyle(e).display!=='none'&&getComputedStyle(e).visibility!=='hidden').map(e=>{const r=e.getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]}).filter(p=>p[1]>top&&p[1]<dock&&document.elementFromPoint(p[0],p[1])?.tagName==='CANVAS')}""")
        for x, y in pts[:4]:
            pg.mouse.click(x, y)
            pg.wait_for_timeout(700)
            if 'دولة على الخريطة' in pg.inner_text('#map-selection'):
                clicked = True
                break
        ok(f'{name}: clicking a state opens its info', clicked)
        if name == 'mobile':
            ok('mobile: zoom buttons hidden (pinch instead)', not pg.locator('.maplibregl-ctrl-zoom-in').is_visible())
        ok(f'{name}: no horizontal scroll', not pg.evaluate('document.documentElement.scrollWidth>innerWidth+1'))
        ok(f'{name}: no page errors', not errs, str(errs))
        ctx.close()

    # النمط الورقي يغيّر ألوان اللوحات العائمة
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    pg = ctx.new_page()
    pg.goto(B + '#/atlas?year=850')
    pg.wait_for_timeout(4000)
    pg.click('.ax-coach-ok')
    dark_bg = pg.evaluate("()=>getComputedStyle(document.querySelector('.ax-era')).backgroundColor")
    pg.click('#ax-layers-btn')
    pg.click('[data-theme="parch"]')
    pg.wait_for_timeout(800)
    parch_bg = pg.evaluate("()=>getComputedStyle(document.querySelector('.ax-era')).backgroundColor")
    ok('parchment theme switches panel colors', dark_bg != parch_bg, f'{dark_bg} -> {parch_bg}')
    pg.click('[data-theme="dark"]')
    ctx.close()
    b.close()

print(f'TOTAL {sum(R)} / {len(R)}')
raise SystemExit(0 if all(R) else 1)
