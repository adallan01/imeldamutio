// Post-build checks. Run after `npm run build`:  npm run check
// 1. Every internal link and asset in dist/ resolves.
// 2. No unpublished register entry has leaked onto a page.
// 3. Every page has a title, description, canonical and one <h1>.
// 4. Lists external links so they can be spot-checked.
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const dist = new URL('../dist/', import.meta.url).pathname;
const lib = JSON.parse(readFileSync(new URL('../data/media-library.json', import.meta.url)));
const pages = [];
const walk = (d) => readdirSync(d).forEach((f) => { const p = join(d, f); statSync(p).isDirectory() ? walk(p) : p.endsWith('.html') && pages.push(p); });
walk(dist);

let problems = 0;
const external = new Set();
const fail = (m) => { problems++; console.log('✗', m); };

for (const file of pages) {
  const html = readFileSync(file, 'utf8');
  const rel = file.replace(dist, '/');
  if (!/<title>[^<]+<\/title>/.test(html)) fail(`${rel}: missing <title>`);
  if (!/<meta name="description" content="[^"]{50,}/.test(html)) fail(`${rel}: missing/short meta description`);
  if (!/<link rel="canonical"/.test(html)) fail(`${rel}: missing canonical`);
  const h1 = (html.match(/<h1[\s>]/g) || []).length;
  if (h1 !== 1) fail(`${rel}: ${h1} <h1> elements`);
  for (const [, url] of html.matchAll(/(?:href|src)="([^"#]+)/g)) {
    if (/^(mailto:|tel:|data:)/.test(url)) continue;
    if (/^https?:/.test(url)) { external.add(url); continue; }
    const clean = decodeURIComponent(url.split('?')[0]);
    const target = join(dist, clean);
    if (!(existsSync(target) && (statSync(target).isFile() || existsSync(join(target, 'index.html'))))) fail(`${rel}: broken internal link ${url}`);
  }
  for (const e of lib.entries.filter((x) => !x.publish)) {
    if (html.includes(e.title.replace(/&/g, '&amp;').replace(/'/g, '&#39;')) || html.includes(e.title)) fail(`${rel}: unpublished entry visible — "${e.title}"`);
  }
}
console.log(`\nChecked ${pages.length} pages. External links (${external.size}):`);
[...external].filter((u) => !u.includes('i.ytimg.com')).sort().forEach((u) => console.log('  ', u));
console.log(problems ? `\n${problems} problem(s) found.` : '\nAll checks passed.');
process.exit(problems ? 1 : 0);
