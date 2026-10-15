"""V4.0: remove duplicated sections, merge overlaps, reorder sections chronologically (ending last)."""
import json, sys
p = sys.argv[1]
d = json.load(open(p, encoding='utf-8'))
C = {c['id']: c for c in d['civilizations']}

def sec(cid, i): return C[cid]['sections'][i]

def edit(cid, i, old, new):
    s = sec(cid, i)
    assert s['text'].count(old) == 1, (cid, i, old)
    s['text'] = s['text'].replace(old, new)

def settext(cid, i, text, title=None):
    s = sec(cid, i); s['text'] = text
    if title: s['title'] = title

def merge_src(cid, keep, drop):
    a, b = sec(cid, keep), sec(cid, drop)
    for x in b.get('sourceIds', []):
        if x not in a['sourceIds']: a['sourceIds'].append(x)

DROP = {}

# --- persia: merge wars (2+5), dedupe provinces (0 vs 4)
edit('persia', 0, 'لم تقم الإمبراطورية على شعب واحد؛ فقد قسّمها الملوك إلى ولايات (مرازبات) لكل منها حاكم، وبقيت لغات وديانات محلية كثيرة قائمة.', 'لم تقم الإمبراطورية على شعب واحد، بل جمعت شعوبًا ولغات وديانات كثيرة.')
edit('persia', 4, 'قُسمت الإمبراطورية إلى ولايات يحكم', 'قُسمت الإمبراطورية إلى ولايات (مرازبات) يحكم')
settext('persia', 2, 'حاول دارا الأول ثم ابنه خشايارشا إخضاع المدن اليونانية في أوائل القرن الخامس ق.م، فهُزمت حملة دارا في ماراثون سنة 490 ق.م، وانكسرت حملة خشايارشا في معركة سلاميس البحرية سنة 480 ق.م، ثم هُزم جيشه البري في بلاتيا سنة 479 ق.م. وبعد نحو قرن ونصف أسقط الإسكندر المقدوني الدولة الأخمينية، وأُحرقت برسيبوليس سنة 330 ق.م. وقراءة المصادر اليونانية عن فارس تحتاج حذرًا، لأنها كُتبت غالبًا من وجهة نظر الخصم.', 'الحروب مع اليونان والنهاية')
merge_src('persia', 2, 5); DROP['persia'] = [5]

# --- mongols: Baghdad/Ain Jalut only in section 4
edit('mongols', 1, ' وفي سنة 1258 م اجتاح هولاكو بغداد، ثم هُزم المغول أمام المماليك في عين جالوت سنة 1260 م.', '')

# --- mamluks: system details only in 3; end moved to last section
edit('mamluks', 0, 'كان المماليك جنودًا يُشترون صغارًا ويُربّون على الفروسية والقتال في خدمة السلاطين الأيوبيين.', 'كان المماليك فرسانًا من أصل رقيق في خدمة السلاطين الأيوبيين.')
edit('mamluks', 2, ' وانتهت دولة المماليك حين دخل العثمانيون القاهرة سنة 1517 م.', '')
sec('mamluks', 2)['title'] = 'القاهرة: مساجد ومدارس'
edit('mamluks', 5, 'والمقريزي مؤرخ مصر.', 'والمقريزي مؤرخ مصر. وانتهت دولة المماليك حين هزمهم العثمانيون في مرج دابق سنة 1516 م، ثم دخلوا القاهرة سنة 1517 م.')
sec('mamluks', 5)['title'] = 'العلم والتجارة والنهاية'

# --- second-saudi: merge Faisal (1+3), merge end (2+5)
settext('second-saudi', 1, 'بعد مقتل الإمام تركي سنة 1834 م حكم ابنه الإمام فيصل بن تركي، ثم أُخذ أسيرًا إلى مصر، وعاد فاستعاد الرياض وحكم مرة ثانية (1843–1865 م). وفي عهده الثاني استقرت أوضاع الدولة، وامتد نفوذها إلى الأحساء والقصيم وجبل شمر، وكانت الرياض مركزًا للحكم والعلم.')
merge_src('second-saudi', 1, 3)
settext('second-saudi', 5, 'في هذه الأثناء قوي حكام حائل من آل رشيد، وبخاصة الأمير محمد بن عبدالله بن رشيد، فبسطوا نفوذهم على نجد والرياض. وفي سنة 1891 م انتصروا في معركة المليداء، فانتهت الدولة السعودية الثانية، وخرج الإمام عبدالرحمن بن فيصل مع أسرته، ومنهم ابنه عبدالعزيز، فتنقلوا في البادية والبحرين ثم استقروا في الكويت.', 'صعود آل رشيد والنهاية')
merge_src('second-saudi', 5, 2); DROP['second-saudi'] = [2, 3]

# --- china: standardisation only in 3
edit('china', 0, ' وحّد الكتابة والأوزان والمقاييس والنقود في أنحاء دولته، فصار التاجر والموظف يتعاملان بنظام واحد.', '')

# --- nabataea: caravans only in 5
edit('nabataea', 0, ' ومن تجارة القوافل جاءت ثروتهم.', '')

# --- ayyubids: merge 0+3
settext('ayyubids', 0, 'جاء صلاح الدين إلى مصر قائدًا في جيش نور الدين زنكي، حاكم حلب ودمشق، الذي سعى إلى توحيد الشام ومصر في مواجهة الصليبيين، ثم صار وزيرًا للخليفة الفاطمي. وفي سنة 1171 م أنهى الخلافة الفاطمية، وأعاد الخطبة للخليفة العباسي في بغداد. وبعد وفاة نور الدين سنة 1174 م ضم دمشق، ثم حلب سنة 1183 م، فجمع مصر والشام تحت حكمه.')
merge_src('ayyubids', 0, 3); DROP['ayyubids'] = [3]

# --- seljuks: madrasas only in 4; split explained before crusades
edit('seljuks', 1, 'ونظّم الوزير نظام الملك الدولة، وأسس في بغداد المدرسة النظامية، وتُنسب إليه مدارس مماثلة في مدن أخرى.', 'ونظّم الوزير نظام الملك شؤون الدولة في عهد ألب أرسلان ثم ابنه ملكشاه.')
edit('seljuks', 5, 'بعد تفكك الدولة الكبرى لم تستطع', 'بعد وفاة ملكشاه سنة 1092 م تفككت الدولة الكبرى، فلم تستطع')
edit('seljuks', 2, 'انقسمت الدولة الكبرى بعد وفاة السلطان ملكشاه سنة 1092 م، وانتهى حكم السلاجقة', 'انتهى حكم السلاجقة')
sec('seljuks', 2)['title'] = 'سلاجقة الروم والنهاية'

# --- andalus: post-1031 continuation moved to the ending section
edit('andalus', 2, ' وبعد تفكك الخلافة سنة 1031 م استمر الحكم الإسلامي في الأندلس قرونًا أخرى، في ممالك الطوائف ثم في غرناطة حتى 1492 م.', '')
edit('andalus', 5, 'وتفرقت الأندلس إلى ممالك الطوائف.', 'وتفرقت الأندلس إلى ممالك الطوائف. واستمر الحكم الإسلامي فيها قرونًا أخرى، حتى سقطت غرناطة سنة 1492 م.')

# --- safavids: end moved to last section
edit('safavids', 2, ' وضعفت الدولة بعده، حتى انتهت سنة 1736 م بتتويج نادر شاه.', '')
edit('safavids', 5, 'من روائع العمارة الإسلامية.', 'من روائع العمارة الإسلامية. وضعفت الدولة بعد الشاه عباس، حتى انتهت سنة 1736 م بتتويج نادر شاه.')
sec('safavids', 5)['title'] = 'الفنون والنهاية'
sec('safavids', 2)['title'] = 'أصفهان «نصف العالم»'

# --- mughals: Shah Jahan in one section, Aurangzeb + end in another
settext('mughals', 2, 'في عهد شاه جهان (1628–1658 م) بلغت العمارة المغولية ذروتها، فبُني تاج محل في أغرا ضريحًا لزوجته ممتاز محل بين 1632 و1653 م، وبنى في دلهي مدينة شاه جهان آباد، وفيها القلعة الحمراء والمسجد الجامع.', 'شاه جهان وتاج محل')
settext('mughals', 4, 'حكم أورنكزيب، ابن شاه جهان، بين 1658 و1707 م، فبلغت الدولة في عهده أقصى اتساعها جنوبًا، لكن حروبه الطويلة أنهكتها. ثم ضعفت الدولة في القرن الثامن عشر، حتى أنهاها البريطانيون بعد ثورة 1857 م.', 'أورنكزيب والنهاية')
for x in sec('mughals', 2)['sourceIds']:
    if x not in sec('mughals', 4)['sourceIds']: sec('mughals', 4)['sourceIds'].append(x)
for x in sec('mughals', 4)['sourceIds']:
    if x not in sec('mughals', 2)['sourceIds']: sec('mughals', 2)['sourceIds'].append(x)

# --- saudi-kingdom: Najd conquests only in 3; section 1 = Hejaz
settext('saudi-kingdom', 1, 'ثم اتجه الملك عبدالعزيز إلى الحجاز، فانتهت حملته بسقوط جدة في ديسمبر 1925 م، وبويع ملكًا على الحجاز سنة 1926 م. وظلت نجد والحجاز تُداران منفصلتين حتى سنة 1932 م.', 'الحجاز')

# --- new order per civ (original indices; dropped ones omitted)
ORDER = {
 'egypt': [0, 3, 1, 2, 4, 5], 'rome': [0, 1, 3, 4, 5, 2], 'greece': [0, 3, 1, 4, 5, 2],
 'umayyad': [0, 1, 3, 4, 2, 5], 'abbasid': [0, 3, 4, 1, 5, 2], 'andalus': [0, 1, 3, 4, 2, 5],
 'first-saudi': [0, 3, 4, 1, 5, 2], 'china': [0, 3, 1, 4, 5, 2], 'persia': [0, 4, 1, 3, 2],
 'ottoman': [0, 1, 2, 3, 4, 5], 'saba': [0, 1, 3, 4, 2, 5], 'nabataea': [0, 5, 3, 1, 4, 2],
 'mamluks': [0, 3, 1, 4, 2, 5], 'mongols': [0, 3, 1, 4, 2, 5], 'rashidun': [0, 1, 4, 2, 3, 5],
 'byzantine': [0, 1, 3, 4, 2, 5], 'sasanian': [0, 3, 1, 4, 5, 2], 'fatimids': [0, 3, 1, 4, 5, 2],
 'ayyubids': [0, 1, 4, 5, 2], 'seljuks': [0, 1, 3, 4, 5, 2], 'safavids': [0, 1, 3, 2, 4, 5],
 'mughals': [0, 1, 3, 5, 2, 4], 'second-saudi': [0, 1, 4, 5], 'saudi-kingdom': [0, 3, 4, 1, 2, 5],
 'parthians': [0, 3, 4, 1, 5, 2], 'almohads': [0, 3, 1, 5, 4, 2], 'mali': [0, 3, 1, 4, 2, 5],
 'ming': [0, 4, 1, 3, 5, 2],
}
for cid, c in C.items():
    o = ORDER[cid]; n = len(c['sections'])
    assert sorted(o + DROP.get(cid, [])) == list(range(n)), cid
    c['sections'] = [c['sections'][i] for i in o]
    titles = [s['title'] for s in c['sections']]
    assert len(set(titles)) == len(titles), cid

json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('ok', sum(len(c['sections']) for c in d['civilizations']))
