// Regenerates research/source-register.csv from data/media-library.json.
// Run: npm run register
import { readFileSync, writeFileSync } from 'node:fs';
const lib = JSON.parse(readFileSync(new URL('../data/media-library.json', import.meta.url)));
const cols = ['id','title','type','category','platform','publisher','url','originalPublisher','publishedDate','eventDate','role','summary','demonstrates','evidence','verification','publish','format','rights'];
const esc = v => { const s = v === undefined || v === null ? '' : String(v); return /[",\n]/.test(s) ? `"${s.replace(/"/g,'""')}"` : s; };
const rows = [cols.join(','), ...lib.entries.map(e => cols.map(c => esc(e[c])).join(','))];
writeFileSync(new URL('../research/source-register.csv', import.meta.url), rows.join('\n') + '\n');
const count = (k) => lib.entries.reduce((m,e)=>(m[e[k]]=(m[e[k]]||0)+1,m),{});
console.log('entries', lib.entries.length, count('verification'), 'published', lib.entries.filter(e=>e.publish).length);
