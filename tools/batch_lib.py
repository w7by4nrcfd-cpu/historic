"""أدوات مشتركة لدفعات توسيع المحتوى (V7.3 وما بعدها).
كل دفعة تعرّف SOURCES وNEW وBACK ثم تستدعي apply()."""
import json
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dist', 'content.json')
W = 'موسوعة مفتوحة (للتحقق المبدئي)'
U = 'متحف أو مرجع رسمي'
B = 'موسوعة مرجعية'
ALLOWED = {'id', 'type', 'title', 'summary', 'sections', 'coordinates', 'startYear', 'endYear', 'period', 'year', 'dateLabel',
           'kind', 'sourceIds', 'relatedIds', 'certainty', 'caveat'}


def apply(SOURCES, NEW, BACK, expected, accessed='2026-10-23', label='23 أكتوبر 2026'):
    d = json.load(open(P, encoding='utf-8'))
    E = {x['id']: x for x in d['entries']}
    C = {c['id']: c for c in d['civilizations']}
    S = {s['id'] for s in d['sources']}
    for i, title, url, kind in SOURCES:
        if i in S:
            continue
        d['sources'].append({'id': i, 'title': title, 'url': url, 'accessed': accessed, 'type': kind,
                             'verification': f'روجعت الصفحة في {label}؛ لا يعني ذلك تدقيقًا أكاديميًا شاملًا'})
        S.add(i)
    assert not set(NEW) & set(E), set(NEW) & set(E)
    assert not set(NEW) & set(C), set(NEW) & set(C)
    for eid, (typ, title, summ, extra, secs, sids, rel) in NEW.items():
        x = {'id': eid, 'type': typ, 'title': title, 'summary': summ}
        x.update(extra)
        x['sections'] = [{'title': t, 'text': tx, 'sourceIds': sids} for t, tx in secs]
        x['sourceIds'] = sids
        x['relatedIds'] = rel
        assert set(x) <= ALLOWED, (eid, set(x) - ALLOWED)
        assert len(secs) >= 3, eid
        assert any(r in C for r in rel), (eid, 'no civilization link')
        if typ == 'event':
            assert isinstance(x.get('year'), int) and x.get('dateLabel') and x.get('kind') and x.get('coordinates'), eid
        if typ == 'city':
            assert x.get('startYear') and x.get('endYear') and x.get('coordinates'), eid
        d['entries'].append(x)
        E[eid] = x
    for k, v in BACK.items():
        x = E[k]
        x['relatedIds'] = list(dict.fromkeys((x.get('relatedIds') or []) + v))
    ids = set(E) | set(C)
    bad = [(x['id'], r) for x in d['entries'] for r in (x.get('relatedIds') or []) if r not in ids]
    miss = [(x['id'], s) for x in d['entries'] for s in (x.get('sourceIds') or []) if s not in S]
    titles = {}
    for x in d['entries']:
        titles.setdefault(x['title'], []).append(x['id'])
    dup = {t: v for t, v in titles.items() if len(v) > 1}
    assert not bad, bad
    assert not miss, miss
    assert not dup, dup
    assert len(NEW) == expected, len(NEW)
    json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('new pages:', len(NEW), '| total entries:', len(d['entries']), '| sources:', len(d['sources']))
