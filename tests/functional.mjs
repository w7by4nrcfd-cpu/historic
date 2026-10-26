import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {JSDOM} from 'jsdom';
import {FRAMES,dateLabel,duration,normalize,search,readStore,saveStore} from '../dist/core.mjs';
const root=new URL('../dist/',import.meta.url).pathname,raw=JSON.parse(await fs.readFile(root+'content.json'));
const dom=new JSDOM(await fs.readFile(root+'index.html','utf8'),{url:'https://atlas.test/',pretendToBeVisual:true});
const errors=[];
global.window=dom.window;global.document=window.document;global.localStorage=window.localStorage;global.location=window.location;global.matchMedia=()=>({matches:true});global.fetch=async path=>({ok:true,json:async()=>JSON.parse(await fs.readFile(root+path,'utf8'))});window.scrollTo=()=>{};
window.addEventListener('error',e=>errors.push(e.error));
await import(root+'app.js');
const tick=()=>new Promise(r=>setTimeout(r,15));await tick();
let count=0;const check=(cond,name)=>{assert.ok(cond,name);count++};
async function route(s){window.location.hash='#'+s;await tick()}
check(document.querySelector('.hero')!==null,'Homepage mounts');
check(document.querySelectorAll('.civ-card').length===8,'8 civilization cards');
check(duration(-1,1)===1,'BCE CE no zero');
check(duration(-27,27)===53,'cross era elapsed years');
check(FRAMES.length===10&&FRAMES.every(y=>y!==0),'valid frames');
check(normalize('الأَنْدَلُس')===normalize('الاندلس'),'Arabic normalization');
for(const x of [...raw.civilizations,...raw.entries]){await route('/topic/'+x.id);check(document.querySelector('h1')?.textContent===x.title,'topic '+x.id);check(document.querySelector('.source-list a')!==null,'source '+x.id);check(!document.body.textContent.includes('undefined'),'no undefined '+x.id)}
await route('/topic/first-saudi');document.querySelector('#bookmark').click();check(JSON.parse(localStorage.getItem('atlas-v1')).saved.includes('first-saudi'),'bookmark persists');await route('/saved');check(document.querySelector('.result-card h3').textContent.includes('السعودية'),'saved route');
await route('/search');const searchInput=document.querySelector('#search');searchInput.value='الاندلس';searchInput.dispatchEvent(new window.Event('input'));check(document.querySelectorAll('.result-card').length>0,'Arabic search results');searchInput.value='zzzzzz';searchInput.dispatchEvent(new window.Event('input'));check(document.querySelector('.empty')!==null,'empty search');
for(const id of ['caliphates','rome','constantinople']){await route('/journey/'+id);for(let step=0;step<3;step++){check(document.querySelector('.badge').textContent.includes(String(step+1)),'step '+id+step);if(step<2)check(document.querySelector('[data-next]').disabled,'gated next');const {JOURNEYS}=await import(root+'journeys.mjs');const answer=JOURNEYS.find(j=>j.id===id).steps[step].answer;document.querySelector(`[data-journey-answer="${(answer+1)%3}"]`).click();check(!stateFor(id).done.includes(step),'wrong answer does not unlock');document.querySelector(`[data-journey-answer="${answer}"]`).click();check(stateFor(id).done.includes(step),'correct answer saved');if(step<2)document.querySelector('[data-next]').click()}await route('/journeys');check(stateFor(id).done.length===3,'full journey saved')}
function stateFor(id){return JSON.parse(localStorage.getItem('atlas-v1')).journeys[id]||{done:[]}}
await route('/city');for(let i=0;i<4;i++){document.querySelector(`[data-landmark="${i}"]`).click();const correct=[0,1,1,2][i];document.querySelector(`[data-city-answer="${correct}"]`).click()}check(JSON.parse(localStorage.getItem('atlas-v1')).city.length===4,'city progress persisted');
for(let frame=0;frame<FRAMES.length;frame++){await route('/atlas?frame='+frame);check(document.querySelector('#year-label').textContent===dateLabel(FRAMES[frame]),'map frame '+frame);check(document.querySelectorAll('[data-point]').length>0,'sites per frame '+frame)}
await route('/atlas?frame=4');document.querySelector('#layer-event').click();check(document.querySelectorAll('[data-point]').length>=2,'events layer adds points');document.querySelector('[data-point]').click();check(document.querySelector('#map-selection a')!==null,'map selection opens article');
await route('/atlas?frame=0');document.querySelector('[data-frame-move="-1"]').click();check(document.querySelector('#year-label').textContent===dateLabel(FRAMES[0]),'slider min clamps');
await route('/sources');check(document.querySelectorAll('.source-list a').length>=29,'sources registry');await route('/research');check(document.querySelectorAll('tbody tr').length===8,'8 competitors');await route('/missing');check(document.querySelector('h1').textContent==='الموضوع غير موجود','missing route');
check(readStore({getItem:()=>'{bad'}).saved.length===0,'corrupt storage recovery');check(saveStore({setItem:()=>{throw Error()}},{})===false,'blocked storage');
check(readStore(localStorage).journeys.constantinople.done.length===3,'persisted journey rehydration');
check(errors.length===0,'no DOM runtime errors '+errors.map(String).join(','));
console.log(JSON.stringify({checks:count,status:'passed',scope:'Node + jsdom DOM simulation, no visual browser/WebGL/Safari tests',routes:raw.civilizations.length+raw.entries.length,journeys:3,frames:FRAMES.length},null,2));

window.close();
