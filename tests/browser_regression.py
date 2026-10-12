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
  for i in range(7):
    pg.click(f'[data-frame="{i}"]'); pg.wait_for_timeout(300)
    counts.append(pg.locator('.map-point').count())
  ok('every frame has markers', all(c>0 for c in counts), str(counts))
  pg.check('#layer-event'); pg.wait_for_timeout(300)
  ev=pg.locator('.map-point.event').count(); ok('events layer at 1750', ev>0, str(ev))
  pg.click('[data-frame="4"]'); pg.wait_for_timeout(300); ok('events layer 850', pg.locator('.map-point.event').count()>0, str(pg.locator('.map-point.event').count()))
  
  try:
    pg.locator('.map-point:not(.event)').first.click(timeout=3000); ok('city marker clickable with events on',True)
  except Exception: ok('city marker clickable with events on',False)
  pg.locator('.map-point').first.click(force=True); pg.wait_for_timeout(300)
  ok('marker click shows selection', 'اقرأ الموضوع' in pg.inner_text('#map-selection'))
  pg.fill('#map-query','بغداد'); pg.wait_for_timeout(300); ok('map query filters', pg.locator('#map-topic-list button').count()==2 and 'قرطبة' not in pg.inner_text('#map-topic-list'))
  # zoom
  z0=pg.evaluate("()=>document.querySelector('.maplibregl-ctrl-zoom-in')?1:0"); pg.click('.maplibregl-ctrl-zoom-in'); ok('zoom ctrl', z0)
  # search
  pg.goto(B+'#/encyclopedia'); pg.wait_for_timeout(800)
  pg.fill('#search','الأندلس'); pg.wait_for_timeout(200); n1=pg.locator('.result-card').count()
  pg.fill('#search','الاندلس'); pg.wait_for_timeout(200); n2=pg.locator('.result-card').count()
  ok('hamza-insensitive search', n1==n2 and n1>0, f'{n1} {n2}')
  pg.fill('#search',''); pg.click('[data-type="person"]'); ok('filter person', pg.locator('.result-card').count()==20, str(pg.locator('.result-card').count()))
  pg.fill('#search','zzzz'); ok('empty state', pg.locator('.empty').count()==1)
  # header search link
  pg.goto(B+'#/'); pg.wait_for_timeout(800); pg.click('.search-link'); pg.wait_for_timeout(500); ok('header search route', pg.locator('#search').count()==1)
  # all topics render
  ids=pg.evaluate("()=>[...document.querySelectorAll('a')].length")
  pg.goto(B+'#/encyclopedia'); pg.wait_for_timeout(500)
  hrefs=pg.eval_on_selector_all('.result-card','els=>els.map(e=>e.getAttribute("href"))')
  bad=[]
  for h in hrefs:
    pg.goto(B+h); pg.wait_for_timeout(150)
    if 'غير موجود' in pg.inner_text('h1') or pg.locator('.source-list li').count()==0: bad.append(h)
    for a in pg.eval_on_selector_all('.article-text a[href^="#/topic/"]','els=>els.map(e=>[e.getAttribute("href"),e.textContent])'):
      if 'undefined' in a[1] or not a[1].strip().replace('←','').strip(): bad.append(('emptylink',h,a))
  ok('58 topics render with sources', len(hrefs)>=58 and not bad, f'{len(hrefs)} {bad[:5]}')
  # bookmark + reload
  pg.goto(B+'#/topic/abbasid'); pg.wait_for_timeout(500); pg.click('#bookmark'); pg.reload(); pg.wait_for_timeout(800)
  ok('bookmark persists', '✓' in pg.inner_text('#bookmark'))
  pg.goto(B+'#/saved'); pg.wait_for_timeout(500); ok('saved page lists', pg.locator('.result-card').count()==1)
  # journeys
  from re import escape
  JA={'caliphates':[1,2,0],'rome':[1,1,2],'arabia':[1,0,1]}
  for jid,ans in JA.items():
    pg.goto(B+f'#/journey/{jid}'); pg.wait_for_timeout(500)
    for step,a in enumerate(ans):
      wrong=(a+1)%3
      pg.click(f'[data-journey-answer="{wrong}"]'); pg.wait_for_timeout(150)
      if step<2: ok(f'{jid} s{step} wrong blocks', pg.locator('[data-next]').is_disabled())
      pg.click(f'[data-journey-answer="{a}"]'); pg.wait_for_timeout(150)
      if step<2:
        ok(f'{jid} s{step} correct unlocks', not pg.locator('[data-next]').is_disabled())
        pg.click('[data-next]'); pg.wait_for_timeout(200)
    pg.reload(); pg.wait_for_timeout(700)
    st=pg.evaluate("()=>JSON.parse(localStorage.getItem('atlas-v1')).journeys")
    ok(f'{jid} done after reload', sorted(st[jid]['done'])==[0,1,2], json.dumps(st[jid]))
  # city
  pg.goto(B+'#/city'); pg.wait_for_timeout(500)
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
  for i in range(7):
    mp.click(f'[data-frame="{i}"]'); mp.wait_for_timeout(3200)
    res.append(mp.evaluate("""()=>{const r=document.querySelector('#map').getBoundingClientRect();return [...document.querySelectorAll('.map-point')].every(e=>{const q=e.getBoundingClientRect();return q.left>=r.left&&q.right<=r.right&&q.top>=r.top&&q.bottom<=r.bottom})}"""))
  print(('PASS' if all(res) else 'FAIL'),'mobile markers inside map every frame',res)
  mp.goto(B+'#/'); mp.wait_for_timeout(2500); mp.locator('#map').scroll_into_view_if_needed(); mp.wait_for_timeout(800)
  mp.locator('#map').screenshot(path='/tmp/after-mob-homemap.png')
  b.close()
