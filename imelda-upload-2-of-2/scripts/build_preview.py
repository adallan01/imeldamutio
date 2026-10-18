"""Bundles the built site (dist/) into ONE self-contained HTML file for previewing
in a browser or chat window without a server. Pages switch via #/path/ links.
This is a preview only; deploy dist/ for the real site.

    npm run build && python3 scripts/build_preview.py
Output: preview/imelda-mutio-site-preview.html
"""
import base64, re
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / 'dist'
PAGES = ['/', '/about/', '/services/', '/on-air/', '/work/', '/media-kit/', '/contact/', '/privacy/']
MIME = {'.webp': 'image/webp', '.jpg': 'image/jpeg', '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.woff': 'font/woff'}

def data_uri(rel):
    p = DIST / rel.lstrip('/')
    return f"data:{MIME.get(p.suffix, 'application/octet-stream')};base64,{base64.b64encode(p.read_bytes()).decode()}"

def inline_css(css):
    # Keep only latin font files (others are unused for English text) to save weight.
    def rep(m):
        url = m.group(1).strip('\'"')
        if url.startswith('data:') or url.startswith('http'):
            return m.group(0)
        if '.woff' in url and 'latin-' not in url.split('/')[-1] or 'latin-ext' in url:
            return 'url("")'
        return f'url("{data_uri(url)}")'
    return re.sub(r'url\(([^)]+)\)', rep, css)

def pick_src(img):
    # Choose a mid-size candidate from srcset to keep the file light.
    srcset = img.get('srcset')
    if srcset:
        cands = []
        for part in srcset.split(','):
            bits = part.strip().split()
            if len(bits) == 2 and bits[1].endswith('w'):
                cands.append((int(bits[1][:-1]), bits[0]))
        cands.sort()
        best = next((u for w, u in cands if w >= 700), cands[-1][1] if cands else img['src'])
        return best
    return img.get('src')

styles, scripts, mains, seen = [], [], {}, set()
shell = None
for path in PAGES:
    soup = BeautifulSoup((DIST / path.lstrip('/') / 'index.html').read_text(), 'html.parser')
    for link in soup.select('link[rel=stylesheet]'):
        href = link['href']
        if href not in seen:
            seen.add(href); styles.append(inline_css((DIST / href.lstrip('/')).read_text()))
    for st in soup.find_all('style'):
        key = st.string or ''
        if key not in seen:
            seen.add(key); styles.append(inline_css(key))
    for sc in soup.find_all('script'):
        if sc.get('type') == 'application/ld+json':
            continue
        code = (DIST / sc['src'].lstrip('/')).read_text() if sc.get('src') else (sc.string or '')
        if 'classList.replace' in code:  # no-js toggle, handled below
            continue
        if code not in seen:
            seen.add(code); scripts.append(code)
    main = soup.find('main')
    targets = [main] + ([soup.find('header'), soup.find('footer'), soup.find('dialog', attrs={'data-vmodal': True})] if path == '/' else [])
    for img in [i for t in targets if t for i in t.find_all('img')]:
        src = pick_src(img)
        if src and src.startswith('/'):
            img['src'] = data_uri(src)
        for a in ('srcset', 'sizes'):
            img.attrs.pop(a, None)
        img['loading'] = 'eager'
    mains[path] = main.decode_contents()
    if path == '/':
        shell = soup

# One header + footer, one <main> holding every page.
header = shell.find('header'); footer = shell.find('footer'); vmodal = shell.find('dialog', attrs={'data-vmodal': True})
body = ''.join(f'<div class="pv-page" data-path="{p}"{" hidden" if p != "/" else ""}>{html}</div>' for p, html in mains.items())
doc = f"""<!doctype html><html lang="en-KE" class="js"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Imelda Mutio, website preview</title><style>{''.join(styles)}
.pv-note{{position:fixed;right:76px;bottom:14px;z-index:200;background:#F07832;color:#050B1C;font:700 12px/1.3 system-ui,sans-serif;padding:8px 12px;border-radius:999px;box-shadow:0 4px 18px rgba(0,0,0,.25)}}</style></head>
<body>{header}<main id="main" tabindex="-1">{body}</main>{footer}{vmodal}
<div class="pv-note" role="note">Preview: deploy dist/ for the live site</div>
<script>
(function(){{
  const known = {PAGES!r};
  function norm(h){{ let p=(h||'').replace(/^#/,''); if(!p||p==='/') return '/'; if(!p.endsWith('/')) p+='/'; return known.includes(p)?p:'/'; }}
  function show(){{
    const raw=(location.hash||'').replace(/^#/,'');
    if(raw && !raw.startsWith('/')){{ const el=document.getElementById(raw); if(el){{ el.scrollIntoView(); return; }} }}
    const [p, anchor]=raw.includes('#')?raw.split('#'):[raw,''];
    const path=norm(p);
    document.querySelectorAll('.pv-page').forEach(el=>el.hidden=el.dataset.path!==path);
    document.querySelectorAll('header nav a, .mobile-menu a').forEach(a=>{{ const h=a.getAttribute('href').replace(/^#/,''); if(h===path||(h!=='/'&&path.startsWith(h))) a.setAttribute('aria-current','page'); else a.removeAttribute('aria-current'); }});
    document.querySelectorAll('.reveal').forEach(el=>el.classList.add('is-in'));
    const t = anchor && document.getElementById(anchor);
    if(t) t.scrollIntoView(); else window.scrollTo({{top:0,behavior:'instant'}});
    const btn=document.querySelector('[data-menu-btn]'), menu=document.querySelector('[data-menu]');
    if(btn&&menu){{ btn.setAttribute('aria-expanded','false'); menu.hidden=true; document.body.style.overflow=''; }}
  }}
  // Rewrite internal links to hash routes.
  document.querySelectorAll('a[href^="/"]').forEach(a=>{{
    const href=a.getAttribute('href');
    if(href.startsWith('/downloads/')) {{ a.addEventListener('click',e=>{{e.preventDefault();alert('Downloads (media kit PDF, portraits) work on the deployed site.');}}); return; }}
    const [path, frag] = href.split('#'); const clean = path.split('?')[0];
    a.setAttribute('href', '#'+clean+(frag?'#'+frag:''));
  }});
  window.addEventListener('hashchange', show); show();
}})();
</script>
{''.join(f'<script type="module">{s}</script>' for s in scripts)}
</body></html>"""
out = ROOT / 'preview'; out.mkdir(exist_ok=True)
f = out / 'imelda-mutio-site-preview.html'; f.write_text(doc)
print(f, round(f.stat().st_size / 1e6, 2), 'MB')
