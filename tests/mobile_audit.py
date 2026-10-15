"""Mobile quality audit: performance (throttled), accessibility heuristics, SEO for static pages.
Run with local server on :8080 serving dist/.  python3 tests/mobile_audit.py [out.json]"""
import json, sys, os, re, glob
from playwright.sync_api import sync_playwright

BASE = 'http://localhost:8080/'
OUT = sys.argv[1] if len(sys.argv) > 1 else 'audit_mobile.json'
PAGES = [('home', ''), ('atlas', '#/atlas'), ('encyclopedia', '#/search'), ('article', '#/topic/abbasids'), ('static', 't/mali/')]

PERF_JS = """() => new Promise(res => {
  const out = {cls:0, lcp:0};
  new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) out.cls += e.value }).observe({type:'layout-shift', buffered:true});
  new PerformanceObserver(l => { const e = l.getEntries(); out.lcp = e[e.length-1].startTime; out.lcpEl = (e[e.length-1].element||{}).tagName }).observe({type:'largest-contentful-paint', buffered:true});
  setTimeout(() => { const p = performance.getEntriesByName('first-contentful-paint')[0]; out.fcp = p ? p.startTime : null;
    const r = performance.getEntriesByType('resource'); out.bytes = r.reduce((a,x)=>a+(x.transferSize||x.encodedBodySize||0),0);
    out.big = r.map(x=>[x.name.replace(location.origin,''), Math.round((x.encodedBodySize||0)/1024), Math.round(x.duration)]).sort((a,b)=>b[1]-a[1]).slice(0,6);
    out.n = r.length; res(out) }, 500);
})"""

A11Y_JS = r"""() => {
  const issues = [];
  const vis = e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width>0 && r.height>0 && s.visibility!=='hidden' && s.display!=='none' };
  const name = e => (e.getAttribute('aria-label')||e.getAttribute('title')||e.innerText||e.getAttribute('alt')||'').trim() || (e.querySelector('img[alt]')||{}).alt || (e.labels&&e.labels[0]&&e.labels[0].innerText) || '';
  document.querySelectorAll('img').forEach(i => { if (!i.hasAttribute('alt')) issues.push(['img-no-alt', i.src.slice(-60)]) });
  document.querySelectorAll('button,a[href],[role=button]').forEach(b => { if (vis(b) && !name(b).trim()) issues.push(['no-name', b.outerHTML.slice(0,90)]) });
  document.querySelectorAll('input,select,textarea').forEach(i => { if (i.type!=='hidden' && vis(i) && !name(i) && !i.getAttribute('placeholder')) issues.push(['input-no-label', i.outerHTML.slice(0,90)]) });
  document.querySelectorAll('button,a[href],input,select,[role=button]').forEach(b => { if (!vis(b)) return; const r = b.getBoundingClientRect();
    if ((r.height < 32 || r.width < 32) && b.closest('p,li.inline,.prose,article p') == null) issues.push(['small-target', Math.round(r.width)+'x'+Math.round(r.height)+' '+(name(b)||b.className).slice(0,40)]) });
  // contrast
  const lum = c => { const m = c.match(/[\d.]+/g); if (!m) return null; const [r,g,b] = m.slice(0,3).map(v => { v/=255; return v<=0.03928? v/12.92 : Math.pow((v+0.055)/1.055,2.4) }); return 0.2126*r+0.7152*g+0.0722*b };
  const bgOf = e => { while (e) { const s = getComputedStyle(e); const c = s.backgroundColor; const m = c.match(/[\d.]+/g); if (s.backgroundImage!=='none' && !s.backgroundImage.includes('gradient')) return null; if (m && (m.length<4 || +m[3]>0.9)) return c; e = e.parentElement } return 'rgb(11,18,32)' };
  const seen = new Set();
  document.querySelectorAll('body *').forEach(e => { if (!vis(e) || e.closest('#map,.maplibregl-map')) return; const t = [...e.childNodes].filter(n=>n.nodeType===3 && n.textContent.trim()).length; if (!t) return;
    const s = getComputedStyle(e); const bg = bgOf(e); if (!bg) return; const a = lum(s.color), b = lum(bg); if (a==null||b==null) return;
    const op = parseFloat(s.opacity); const ratio = (Math.max(a,b)+0.05)/(Math.min(a,b)+0.05); const fs = parseFloat(s.fontSize); const big = fs>=24 || (fs>=18.66 && +s.fontWeight>=700);
    if (ratio < (big?3:4.5) || op < 0.7) { const k = s.color+bg+e.tagName+e.className; if (!seen.has(k)) { seen.add(k); issues.push(['contrast', ratio.toFixed(2)+' '+s.color+' on '+bg+' '+e.tagName+'.'+String(e.className).slice(0,30)+' «'+e.innerText.trim().slice(0,25)+'»']) } } });
  const hs = [...document.querySelectorAll('h1,h2,h3,h4')].filter(vis).map(h=>+h.tagName[1]);
  if (hs.filter(x=>x===1).length !== 1) issues.push(['h1-count', hs.filter(x=>x===1).length]);
  for (let i=1;i<hs.length;i++) if (hs[i]-hs[i-1]>1) { issues.push(['heading-skip', hs[i-1]+'->'+hs[i]]); break }
  if (document.documentElement.scrollWidth > innerWidth+1) issues.push(['h-scroll', document.documentElement.scrollWidth]);
  return issues;
}"""

res = {}
with sync_playwright() as p:
    br = p.chromium.launch(args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
    dev = p.devices['iPhone 13']
    for key, path in PAGES:
        ctx = br.new_context(**dev)
        pg = ctx.new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        cdp = ctx.new_cdp_session(pg)
        cdp.send('Network.enable')
        cdp.send('Network.emulateNetworkConditions', {'offline': False, 'latency': 150, 'downloadThroughput': 1.6e6/8*1.0, 'uploadThroughput': 750e3/8})
        cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4})
        pg.goto(BASE + path, wait_until='load', timeout=120000)
        pg.wait_for_timeout(6000 if key == 'atlas' else 2500)
        perf = pg.evaluate(PERF_JS)
        cdp.send('Emulation.setCPUThrottlingRate', {'rate': 1})
        a11y = pg.evaluate(A11Y_JS)
        res[key] = {'perf': perf, 'a11y': a11y, 'errors': errs}
        ctx.close()
    br.close()

# SEO static pages
seo = []
for f in sorted(glob.glob('dist/t/*/index.html')):
    h = open(f, encoding='utf-8').read()
    pid = f.split('/')[-2]
    t = re.search(r'<title>(.*?)</title>', h)
    d = re.search(r'name="description" content="([^"]*)"', h)
    c = re.search(r'rel="canonical" href="([^"]*)"', h)
    h1 = len(re.findall(r'<h1[\s>]', h))
    prob = []
    if not t or len(t.group(1)) < 10: prob.append('title')
    if not d or len(d.group(1)) < 50: prob.append('desc-short')
    if d and len(d.group(1)) > 170: prob.append('desc-long %d' % len(d.group(1)))
    if not c: prob.append('no-canonical')
    if h1 != 1: prob.append('h1=%d' % h1)
    if 'application/ld+json' not in h: prob.append('no-jsonld')
    if 'lang="ar"' not in h: prob.append('lang')
    if prob: seo.append([pid] + prob)
sm = open('dist/sitemap.xml', encoding='utf-8').read()
locs = re.findall(r'<loc>(.*?)</loc>', sm)
missing = [l for l in locs if '/t/' in l and not os.path.exists('dist/' + l.split('/historic/')[1] + 'index.html')]
dupt = {}
for f in glob.glob('dist/t/*/index.html'):
    t = re.search(r'<title>(.*?)</title>', open(f, encoding='utf-8').read()).group(1)
    dupt.setdefault(t, []).append(f.split('/')[-2])
res['seo'] = {'pages': len(glob.glob('dist/t/*/index.html')), 'problems': seo[:60], 'n_problems': len(seo), 'sitemap_missing': missing, 'dup_titles': {k: v for k, v in dupt.items() if len(v) > 1}}
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in res.items():
    if k == 'seo':
        print('SEO', v['pages'], 'pages, problems', v['n_problems'], 'missing', len(v['sitemap_missing']), 'dups', len(v['dup_titles']))
    else:
        pf = v['perf']
        print(k, 'FCP %.0f LCP %.0f(%s) CLS %.3f KB %d n %d | a11y %d | err %d' % (pf['fcp'] or -1, pf['lcp'], pf.get('lcpEl'), pf['cls'], pf['bytes'] / 1024, pf['n'], len(v['a11y']), len(v['errors'])))
