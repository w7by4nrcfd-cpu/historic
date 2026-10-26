"""اختبارات V9.0: بطاقة مشاركة لكل صفحة موضوع (tools/build_og.py).
التشغيل: python3 tools/build_pages.py ثم python3 tests/v90_share.py"""
import glob, json, os, re
from PIL import Image
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist')
BASE = 'https://w7by4nrcfd-cpu.github.io/historic/'
R = []
def ok(n, c, x=''):
    R.append(bool(c)); print(('PASS' if c else 'FAIL'), n, x)

d = json.load(open(os.path.join(ROOT, 'content.json'), encoding='utf-8'))
ids = [x['id'] for x in d['civilizations'] + d['entries']]
cards = {os.path.basename(p)[:-4] for p in glob.glob(os.path.join(ROOT, 'og', '*.jpg'))}
ok(f'a card for every one of the {len(ids)} topic pages', set(ids) <= cards, str(sorted(set(ids) - cards)[:5]))
ok('no stray cards for removed pages', cards <= set(ids), str(sorted(cards - set(ids))[:5]))
bad = []
for i in ids[::7]:
    im = Image.open(os.path.join(ROOT, 'og', f'{i}.jpg'))
    if im.size != (1200, 630) or im.format != 'JPEG' or os.path.getsize(os.path.join(ROOT, 'og', f'{i}.jpg')) > 120 * 1024:
        bad.append(i)
ok('cards are 1200×630 JPEG under 120 KB (sample of every 7th)', not bad, str(bad[:5]))
miss = []
for i in ids:
    h = open(os.path.join(ROOT, 't', i, 'index.html'), encoding='utf-8').read()
    m = re.search(r'<meta property="og:image" content="([^"]*)">', h)
    if not m or m.group(1) != f'{BASE}og/{i}.jpg' or f'<meta name="twitter:image" content="{BASE}og/{i}.jpg">' not in h or 'og:image:alt' not in h:
        miss.append(i)
ok('every static page shares its own card (og:image, twitter:image, alt)', not miss, str(miss[:5]))
h = open(os.path.join(ROOT, 't', 'saladin', 'index.html'), encoding='utf-8').read()
ok('static page photo caption uses the small © link, not the full credit line', 'class="cr"' in h and ' / CC' not in h.split('<figcaption>')[1].split('</figcaption>')[0] if '<figcaption>' in h else True)
ok('home page keeps the general site image', 'assets/og.jpg' in open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read())
print(f'TOTAL {sum(R)} / {len(R)}'); raise SystemExit(0 if all(R) else 1)
