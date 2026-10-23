/* أطلس: يحفظ الملفات الكبيرة التي لا تتغير تقريبًا (مكتبة الخريطة، اليابسة والمياه، الخط، الحدود، التضاريس)
   في ذاكرة الجهاز، فتفتح الخريطة في الزيارة الثانية دون تنزيلها من جديد.
   باقي الملفات (الصفحة، الكود، المحتوى) تُطلب من الشبكة دائمًا، فيصل كل تحديث فور نشره. */
// غيّر الرقم عند تحديث مكتبة الخريطة أو بيانات اليابسة والمياه والخط، ليحذف المتصفح النسخة القديمة
const CACHE = 'atlas-static-v2';
const STATIC = /\/assets\/(maplibre-gl\.(js|css)|land\.geojson|water\.geojson|physical\.geojson|arabic\.woff|minimap\.json|dem\/|borders\/)/;

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(
  caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith('atlas-') && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())
));
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET' || !STATIC.test(new URL(req.url).pathname)) return;
  // ملفات الحدود قد تتغير مع تحديث البيانات: نعرض المحفوظ فورًا ونحدّثه في الخلفية
  const revalidate = /\/borders\//.test(req.url);
  e.respondWith(caches.open(CACHE).then(c => c.match(req).then(hit => {
    const net = fetch(req).then(r => { if (r.ok) c.put(req, r.clone()); return r; });
    if (hit) { if (revalidate) net.catch(() => {}); return hit; }
    return net;
  })));
});
