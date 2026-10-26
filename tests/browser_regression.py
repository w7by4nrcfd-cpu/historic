import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frames import FRAMES, fsel
import sys, json
from playwright.sync_api import sync_playwright
R=[]
def ok(name,cond,extra=''):
  R.append((name,bool(cond))); print(('PASS' if cond else 'FAIL'),name,extra)
import os
B=os.environ.get('ATLAS_URL','http://localhost:8080/')
with sync_playwright() as p:
  b=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
  ctx=b.new_context(viewport={'width':1280,'height':900}); pg=ctx.new_page(); errs=[]
  pg.on('pageerror',lambda e: errs.append(str(e)))
  pg.goto(B+'#/atlas'); pg.wait_for_timeout(2500)
  ok('webgl canvas', pg.locator('.maplibregl-canvas').count()==1)
  land=pg.evaluate("()=>{const m=document.querySelector('#map');return m&&m.querySelector('canvas').width>0}")
  ok('canvas sized',land)
  counts=[]
  for i in range(len(FRAMES)):
    pg.click(f'[data-frame="{i}"]'); pg.wait_for_timeout(300)
    counts.append(pg.locator('.map-point').count())
  ok('every frame has markers', all(c>0 for c in counts), str(counts))
  pg.evaluate("()=>{const p=document.getElementById('ax-panel');if(p)p.hidden=false}"); pg.check('#layer-event'); pg.wait_for_timeout(300)
  ev=pg.locator('.map-point.event').count(); ok('events layer at 1750', ev>0, str(ev))
  pg.click(fsel(850)); pg.wait_for_timeout(300); ok('events layer 850', pg.locator('.map-point.event').count()>0, str(pg.locator('.map-point.event').count()))
  
  pg.wait_for_timeout(1500)
  try:
    pg.locator('.map-point:not(.event)').first.click(timeout=6000); ok('city marker clickable with events on',True)
  except Exception: ok('city marker clickable with events on',False)
  pg.locator('.map-point').first.click(force=True); pg.wait_for_timeout(300)
  ok('marker click shows selection', 'اقرأ الموضوع' in pg.inner_text('#map-selection'))
  pg.fill('#map-query','بغداد'); pg.wait_for_timeout(300); ok('map query filters', pg.locator('#map-topic-list button').count()>=2 and 'بغداد' in pg.inner_text('#map-topic-list') and 'قرطبة' not in pg.inner_text('#map-topic-list'))  # بغداد ومعها أحداث العباسيين
  # zoom
  z0=pg.evaluate("()=>document.querySelector('.maplibregl-ctrl-zoom-in')?1:0"); pg.click('.maplibregl-ctrl-zoom-in'); ok('zoom ctrl', z0)
  # search
  pg.goto(B+'#/encyclopedia'); pg.wait_for_timeout(800)
  pg.fill('#search','الأندلس'); pg.wait_for_timeout(200); n1=pg.locator('.result-card').count()
  pg.fill('#search','الاندلس'); pg.wait_for_timeout(200); n2=pg.locator('.result-card').count()
  ok('hamza-insensitive search', n1==n2 and n1>0, f'{n1} {n2}')
  pg.fill('#search',''); pg.click('[data-type="person"]'); ok('filter person', pg.inner_text('#result-count').startswith(str(sum(e['type']=='person' for e in json.load(open('dist/content.json',encoding='utf-8'))['entries']))), pg.inner_text('#result-count'))
  pg.fill('#search','zzzz'); ok('empty state', pg.locator('.empty').count()==1)
  # header search link
  pg.goto(B+'#/'); pg.wait_for_timeout(800); pg.click('.search-link'); pg.wait_for_timeout(500); ok('header search route', pg.locator('#search').count()==1)
  # all topics render
  ids=pg.evaluate("()=>[...document.querySelectorAll('a')].length")
  pg.goto(B+'#/encyclopedia'); pg.wait_for_timeout(500)
  while pg.locator('#more-results').count(): pg.click('#more-results'); pg.wait_for_timeout(100)
  hrefs=pg.eval_on_selector_all('.result-card','els=>els.map(e=>e.getAttribute("href"))')
  bad=[]
  for h in hrefs:
    pg.goto(B+h); pg.wait_for_timeout(150)
    if 'غير موجود' in pg.inner_text('h1') or pg.locator('.article-text section').count()==0: bad.append(h)
    for a in pg.eval_on_selector_all('.article-text a[href^="#/topic/"]','els=>els.map(e=>[e.getAttribute("href"),e.textContent])'):
      if 'undefined' in a[1] or not a[1].strip().replace('←','').strip(): bad.append(('emptylink',h,a))
  ok('all topics render', len(hrefs)>=58 and not bad, f'{len(hrefs)} {bad[:5]}')
  # bookmark + reload
  pg.goto(B+'#/topic/abbasid'); pg.wait_for_timeout(500); pg.click('#bookmark'); pg.reload(); pg.wait_for_timeout(800)
  ok('bookmark persists', '✓' in pg.inner_text('#bookmark'))
  pg.goto(B+'#/saved'); pg.wait_for_timeout(500); ok('saved page lists', pg.locator('.result-card').count()==1)
  # journeys
  from re import escape
  JA={'caliphates':[1,2,0],'rome':[1,1,2],'saudi':[1, 0, 2, 1, 0, 0, 1],'constantinople':[2,0,1]}
  for jid,ans in JA.items():
    pg.goto(B+f'#/journey/{jid}'); pg.wait_for_timeout(500)
    for step,a in enumerate(ans):
      wrong=(a+1)%3
      pg.click(f'[data-journey-answer="{wrong}"]'); pg.wait_for_timeout(150)
      if step<len(ans)-1: ok(f'{jid} s{step} wrong blocks', pg.locator('[data-next]').is_disabled())
      pg.click(f'[data-journey-answer="{a}"]'); pg.wait_for_timeout(150)
      if step<len(ans)-1:
        ok(f'{jid} s{step} correct unlocks', not pg.locator('[data-next]').is_disabled())
        pg.click('[data-next]'); pg.wait_for_timeout(200)
    pg.reload(); pg.wait_for_timeout(700)
    st=pg.evaluate("()=>JSON.parse(localStorage.getItem('atlas-v1')).journeys")
    ok(f'{jid} done after reload', sorted(st[jid]['done'])==list(range(len(ans))), json.dumps(st[jid]))
  # city
  pg.goto(B+'#/city/baghdad'); pg.wait_for_timeout(500)
  for i,a in enumerate([0,1,1,2]):
    pg.click(f'.hotspot[data-landmark="{i}"]'); pg.wait_for_timeout(150)
    pg.click(f'[data-city-answer="{(a+1)%3}"]'); pg.click(f'[data-city-answer="{a}"]'); pg.wait_for_timeout(150)
  pg.reload(); pg.wait_for_timeout(700)
  ok('city 4/4 after reload', 'فهمت 4 من 4' in pg.inner_text('.city-workspace small'))
  # broken storage
  pg.evaluate("()=>localStorage.setItem('atlas-v1','{bad')"); pg.reload(); pg.wait_for_timeout(700); ok('corrupt storage survives', pg.locator('h1').count()>0)
  # 404
  pg.goto(B+'#/nothing'); pg.wait_for_timeout(300); ok('404 page', 'غير موجود' in pg.inner_text('h1'))
  # topic->atlas link
  pg.goto(B+'#/topic/baghdad-found'); pg.wait_for_timeout(500); pg.click('text=على الخريطة'); pg.wait_for_timeout(2500)
  ok('topic map link selects', 'اقرأ الموضوع' in pg.inner_text('#map-selection'), pg.inner_text('#map-selection')[:60])
  ok('no page errors', not errs, str(errs[:3]))
  # mobile menu
  m=b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True); mp=m.new_page(); mp.goto(B+'#/'); mp.wait_for_timeout(1200)
  mp.click('.menu-toggle'); mp.wait_for_timeout(300); ok('mobile menu opens', mp.locator('nav.open').count()==1 and mp.locator('nav a').first.is_visible())
  mp.click('nav a >> nth=1'); mp.wait_for_timeout(500); ok('mobile nav routes', mp.locator('#search').count()==1)
  # fallback without webgl
  f=b.new_context(viewport={'width':1280,'height':900}); fp=f.new_page()
  fp.add_init_script("HTMLCanvasElement.prototype.getContext=function(){return null}")
  fp.goto(B+'#/atlas'); fp.wait_for_timeout(2500)
  ok('fallback map', fp.locator('.map-fallback').count()==1 and fp.locator('.fallback-point').count()>0, str(fp.locator('.fallback-point').count()))
  fp.screenshot(path='/tmp/fallback.png')
  b.close()
print('TOTAL',sum(1 for r in R if r[1]),'/',len(R))
# mobile: all markers inside viewport after load, each frame
with sync_playwright() as p:
  b=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
  m=b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True); mp=m.new_page()
  mp.goto(B+'#/atlas'); mp.wait_for_timeout(2500)
  res=[]
  for i in range(len(FRAMES)):
    mp.click(f'[data-frame="{i}"]'); mp.wait_for_timeout(4500)
    res.append(mp.evaluate("""()=>{const r=document.querySelector('#map').getBoundingClientRect();return [...document.querySelectorAll('.map-point')].every(e=>{const q=e.getBoundingClientRect();return q.left>=r.left&&q.right<=r.right&&q.top>=r.top&&q.bottom<=r.bottom})}"""))
  wide=[i for i,y in enumerate(FRAMES) if y in (1492,1500,1530)]  # Americas + Asia cannot fit a 390px-wide map
  print(('PASS' if all(r for i,r in enumerate(res) if i not in wide) else 'FAIL'),'mobile markers inside map every frame (except world-wide 1492–1530)',res)
  mp.goto(B+'#/'); mp.wait_for_timeout(2500); mp.locator('#map').scroll_into_view_if_needed(); mp.wait_for_timeout(800)
  mp.locator('#map').screenshot(path='/tmp/after-mob-homemap.png')
  b.close()
# games
with sync_playwright() as p:
  b=p.chromium.launch(); pg=b.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(B+'#/play'); pg.wait_for_timeout(800); print(('PASS' if pg.locator('.game-card').count()==3 else 'FAIL'),'play hub')
  pg.goto(B+'#/play/order'); pg.wait_for_timeout(800)
  for k in range(4): pg.locator('[data-pick]').first.click(); pg.wait_for_timeout(100)
  print(('PASS' if pg.locator('.game-result').count()==1 and pg.locator('.slot.good,.slot.bad').count()==4 else 'FAIL'),'order game completes')
  pg.click('[data-again]'); pg.wait_for_timeout(200); print(('PASS' if pg.locator('[data-pick]').count()==4 else 'FAIL'),'order new round')
  pg.goto(B+'#/play/owner'); pg.wait_for_timeout(800)
  for k in range(10):
    pg.locator('[data-own]').first.click(); pg.wait_for_timeout(80); pg.click('[data-next]'); pg.wait_for_timeout(80)
  t=pg.inner_text('main'); print(('PASS' if 'من 10' in t and 'نتيجتك' in t else 'FAIL'),'owner game completes')
  g=pg.evaluate("localStorage.getItem('atlas-games')"); s=pg.evaluate("localStorage.getItem('atlas-v1')"); print(('PASS' if g else 'FAIL'),'scores saved separately',g)
  print(('PASS' if not errs else 'FAIL'),'game no errors',errs[:2])
  b.close()
# V2.4: new topics + share
with sync_playwright() as p:
  b=p.chromium.launch(); ctx=b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True); ctx.grant_permissions(['clipboard-read','clipboard-write'],origin=B.rstrip('/')); pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  for tid in ['rashidun','medina','abu-bakr','umar','uthman','ali','yarmuk','hijri-calendar','rashidun-start','khwarizmi-algebra','ibn-haytham-optics','zahrawi-surgery','paper-baghdad']:
    pg.goto(B+'#/topic/'+tid); pg.wait_for_timeout(250)
    print(('PASS' if pg.locator('h1').count()==1 and 'غير موجود' not in pg.inner_text('main') and pg.locator('#share-topic').count()==1 else 'FAIL'),'topic',tid)
  pg.goto(B+'#/topic/umar'); pg.wait_for_timeout(300); pg.evaluate("()=>{try{delete Navigator.prototype.share}catch(e){}}")
  pg.click('#share-topic'); pg.wait_for_timeout(400)
  clip=pg.evaluate("navigator.clipboard.readText()")
  print(('PASS' if clip.endswith('/t/umar/') else 'FAIL'),'share copies static url',clip)
  pg.goto(B+'#/atlas?frame=4'); pg.wait_for_timeout(2500)
  print(('PASS' if 'المدينة' in pg.inner_text('#map-topic-list') else 'FAIL'),'frame 650 shows Medina', pg.inner_text('#year-label'))
  pg.goto(B+'#/'); pg.wait_for_timeout(500)
  hrefs=pg.eval_on_selector_all('.era',"e=>e.map(a=>a.getAttribute('href'))"); print(('PASS' if hrefs==['#/atlas?year=-1750','#/atlas?year=-100','#/atlas?year=650','#/atlas?year=1300','#/atlas?year=1750'] else 'FAIL'),'era links',hrefs)
  pg.goto(B+'#/timeline'); pg.wait_for_timeout(500); print(('PASS' if 'الخلافة الراشدة' in pg.inner_text('main') else 'FAIL'),'timeline has rashidun')
  print(('PASS' if not errs else 'FAIL'),'v2.4 no errors',errs[:3])
  b.close()
# V2.5: borders, play, same-time, where game
with sync_playwright() as p:
  b=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
  pg=b.new_page(viewport={'width':1280,'height':900}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(B+'#/atlas?frame=6'); pg.wait_for_timeout(4000)
  n=pg.evaluate("()=>document.querySelectorAll('.border-label').length"); tag=pg.inner_text('#map-tag')
  print(('PASS' if n>5 and '800' in tag else 'FAIL'),'borders 850 labels',n,tag)
  feats=pg.evaluate("()=>{const m=document.querySelector('#map');return m.classList.contains('has-borders')}")
  print(('PASS' if feats else 'FAIL'),'borders class on')
  pg.evaluate("()=>{const p=document.getElementById('ax-panel');if(p)p.hidden=false}"); pg.click('label:has(#layer-borders)'); pg.wait_for_timeout(600)
  print(('PASS' if pg.locator('.border-label').count()==0 else 'FAIL'),'borders toggle off')
  pg.evaluate("()=>{const p=document.getElementById('ax-panel');if(p)p.hidden=false}"); pg.click('label:has(#layer-borders)'); pg.click(fsel(650)); pg.wait_for_timeout(1200)
  print(('PASS' if pg.locator('.border-label').count()==0 and 'لا تتوفر' in pg.inner_text('#map-tag') else 'FAIL'),'no borders at 650', pg.inner_text('#map-tag'))
  pg.click(fsel(-100)); pg.wait_for_timeout(300); pg.click('#map-play'); pg.wait_for_timeout(1500)
  lab=pg.inner_text('#year-label'); print(('PASS' if '117' in lab else 'FAIL'),'play advances',lab)
  pg.click('#map-play'); lab=pg.inner_text('#year-label'); pg.wait_for_timeout(3200); lab2=pg.inner_text('#year-label'); print(('PASS' if lab2==lab and pg.inner_text('#map-play')=='▶' else 'FAIL'),'play stops',lab2)
  pg.click(fsel(1914)); pg.wait_for_timeout(300); pg.click('#map-play'); pg.wait_for_timeout(1500); print(('PASS' if '1932' in pg.inner_text('#year-label') and pg.inner_text('#map-play')=='▶' else 'FAIL'),'play auto-stops at end')
  pg.goto(B+'#/topic/yarmuk'); pg.wait_for_timeout(500); t=pg.inner_text('main'); print(('PASS' if 'في الفترة نفسها' in t else 'FAIL'),'same-time event')
  pg.goto(B+'#/topic/abbasid'); pg.wait_for_timeout(500); t=pg.inner_text('main'); print(('PASS' if 'حضارات عاصرتها' in t else 'FAIL'),'same-time civ')
  pg.goto(B+'#/play/where'); pg.wait_for_timeout(4500)
  q=pg.inner_text('#where-q'); print(('PASS' if 'أين تقع' in q else 'FAIL'),'where question',q)
  for k in range(5):
    box=pg.locator('#map').bounding_box(); pg.mouse.click(box['x']+box['width']*0.5,box['y']+box['height']*0.5); pg.wait_for_timeout(900)
    pg.click('[data-next]'); pg.wait_for_timeout(900)
  t=pg.inner_text('main'); g=pg.evaluate("localStorage.getItem('atlas-games')")
  print(('PASS' if 'من 500' in t and '"where"' in (g or '') else 'FAIL'),'where game completes',g)
  pg.goto(B+'#/'); pg.wait_for_timeout(3500); pg.locator('#map').scroll_into_view_if_needed(); pg.wait_for_timeout(2500)
  print(('PASS' if not errs else 'FAIL'),'v2.5 no errors',errs[:3])
  b.close()
# V3.3: themes, relief, compare, polygon info, Saudi frames
with sync_playwright() as p:
  b=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
  pg=b.new_page(viewport={'width':1280,'height':820}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(B+'#/atlas?frame=6'); pg.wait_for_timeout(6000)
  print(('PASS' if pg.evaluate("()=>!!window.maplibregl&&document.querySelector('#map').classList.contains('theme-dark')") else 'FAIL'),'default dark theme')
  pg.evaluate("()=>{const p=document.getElementById('ax-panel');if(p)p.hidden=false}"); pg.click('[data-theme="parch"]'); pg.wait_for_timeout(800)
  ok1=pg.evaluate("()=>document.querySelector('#map').classList.contains('theme-parch')&&localStorage.getItem('atlas-map-theme')==='parch'")
  print(('PASS' if ok1 else 'FAIL'),'parchment theme applied and saved')
  pg.reload(); pg.wait_for_timeout(6000)
  print(('PASS' if pg.evaluate("()=>document.querySelector('#map').classList.contains('theme-parch')") else 'FAIL'),'theme persists after reload')
  pg.evaluate("()=>{const p=document.getElementById('ax-panel');if(p)p.hidden=false}"); pg.click('[data-theme="terrain"]'); pg.wait_for_timeout(2500)
  dem=pg.evaluate("()=>performance.getEntriesByType('resource').filter(r=>r.name.includes('/assets/dem/')).length")
  print(('PASS' if dem>0 else 'FAIL'),'relief tiles load',dem)
  pg.evaluate("()=>{const p=document.getElementById('ax-panel');if(p)p.hidden=false}"); pg.click('[data-theme="dark"]'); pg.wait_for_timeout(500)
  pg.select_option('#cmp-year','1000'); pg.wait_for_timeout(1500)
  print(('PASS' if '1000' in pg.inner_text('#cmp-note') else 'FAIL'),'compare overlay note')
  pg.select_option('#cmp-year',''); pg.wait_for_timeout(500)
  print(('PASS' if pg.locator('#cmp-note').count()==0 else 'FAIL'),'compare cleared')
  pt=pg.evaluate("()=>{const m=window.__atlasMap,q=m.project([42.5,31.5]),r=m.getContainer().getBoundingClientRect();return [r.left+q.x,r.top+q.y]}"); pg.mouse.click(pt[0],pt[1]); pg.wait_for_timeout(800)  # نقطة في العراق داخل حدود الدولة القائمة، لا موضع ثابت على الشاشة
  print(('PASS' if 'دولة على الخريطة' in pg.inner_text('#map-selection') else 'FAIL'),'polygon click shows info')
  pg.click(fsel(1932)); pg.wait_for_timeout(2500)
  t=pg.inner_text('#map-topic-list'); print(('PASS' if 'الرياض' in t and '1930' in pg.inner_text('#map-tag') else 'FAIL'),'1932 frame shows Riyadh, with 1930 borders')
  pg.goto(B+'#/topic/saudi-kingdom'); pg.wait_for_timeout(400); print(('PASS' if '1932' in pg.inner_text('main') else 'FAIL'),'kingdom page')
  print(('PASS' if not errs else 'FAIL'),'v3.3 no errors',errs[:3])
  b.close()
# V3.6: polish
with sync_playwright() as p:
  b=p.chromium.launch(); pg=b.new_page(viewport={'width':390,'height':844},is_mobile=True); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(B+'#/'); pg.wait_for_timeout(800)
  print(('PASS' if pg.locator('.civ-grid .civ-card').count()==8 and pg.locator('a[href="#/encyclopedia?type=civilization"]').count()>=1 else 'FAIL'),'home shows 8 featured civs')
  pg.goto(B+'#/encyclopedia'); pg.wait_for_timeout(600)
  n1=pg.locator('.result-card').count(); pg.click('#more-results'); pg.wait_for_timeout(300); n2=pg.locator('.result-card').count()
  print(('PASS' if n1==24 and n2==48 else 'FAIL'),'encyclopedia pagination',n1,n2)
  pg.fill('#search','بغداد'); pg.wait_for_timeout(300); print(('PASS' if 0<pg.locator('.result-card').count()<=24 else 'FAIL'),'search resets pagination',pg.locator('.result-card').count())
  pg.goto(B+'#/topic/saladin'); pg.wait_for_timeout(500)
  y1=pg.evaluate("document.querySelector('.article-aside').getBoundingClientRect().top"); y2=pg.evaluate("document.querySelector('.article-text').getBoundingClientRect().top")
  print(('PASS' if y1<y2 else 'FAIL'),'mobile facts box above article')
  print(('PASS' if not errs else 'FAIL'),'v3.6 no errors',errs[:2])
  b.close()
