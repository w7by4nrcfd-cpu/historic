"""V8.2 — صور لأهم الصفحات من ويكيميديا كومنز، بعد التحقق من رخصة كل صورة ومصوّرها من صفحة الملف.
البيانات في reports/images/images_v82.json. لا صور متخيلة للنبي ﷺ ولا للصحابة: لوحات أسمائهم بالخط في آيا صوفيا، ومساجد ونقود ومخطوطات.
التشغيل مرة واحدة: python3 tools/content_v82.py"""
import json, os
H = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(H, '..', 'dist', 'content.json')
IMG = json.load(open(os.path.join(H, '..', 'reports', 'images', 'images_v82.json'), encoding='utf-8'))
d = json.load(open(P, encoding='utf-8'))
E = {x['id']: x for x in d['entries']}
used = {x['image']['file'] for x in d['entries'] + d['civilizations'] if x.get('image')}
n = 0
for k, im in IMG.items():
    x = E[k]
    assert not x.get('image'), k
    assert im['file'] not in used, (k, im['file'])
    assert im['src'].startswith('https://upload.wikimedia.org/wikipedia/commons/') and im['page'].startswith('https://commons.wikimedia.org/wiki/File:')
    assert im['license'] and im['author'] and im['caption'], k
    x['image'] = {kk: im[kk] for kk in ('src', 'file', 'author', 'license', 'caption', 'page')}
    used.add(im['file']); n += 1
json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('images added:', n, '| pages with images:', sum(1 for x in d['entries'] if x.get('image')))
