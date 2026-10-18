"""Builds the downloadable media kit PDF, the social-sharing image and the touch icon.

Content comes from the same data files as the website (data/*.json), so the kit
never says more than the site does. Re-run after editing the data:

    python3 scripts/build_media_kit.py

Requires: pip install playwright && playwright install chromium
Outputs:  public/downloads/imelda-mutio-media-kit.pdf, public/og-image.jpg, public/apple-touch-icon.png
"""
import json, asyncio, html
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
site = json.loads((ROOT / 'data/site.json').read_text())
services = json.loads((ROOT / 'data/services.json').read_text())
bios = {b['label']: b['text'] for b in json.loads((ROOT / 'data/bios.json').read_text())}
lib = json.loads((ROOT / 'data/media-library.json').read_text())['entries']
pub = [e for e in lib if e.get('publish')]
sk = lambda e: e.get('eventDate') or e.get('publishedDate') or ''
credits = sorted([e for e in pub if e['section'] in ('engagement', 'award')], key=sk, reverse=True)
press = sorted([e for e in pub if e['section'] == 'media' and e.get('featured')], key=sk, reverse=True)
e = html.escape
F = lambda p: (ROOT / p).as_uri()
PH = lambda n: F(f'src/assets/photos/{n}.jpg')

shows_d = [x for x in pub if x['section'] == 'show']
SHOWS = [(x['title'], x['displayDate'], 'Music, stories, lifestyle conversations, guest interviews and the daily Dilemma of the Day.') for x in shows_d]
CUT = lambda n: F(f'src/assets/cutouts/imelda-{n}.png')
STG = lambda n: F(f'src/assets/stage/{n}.jpg')

CSS = f"""
@font-face {{ font-family: Sora; src: url('{F('node_modules/@fontsource-variable/sora/files/sora-latin-wght-normal.woff2')}') format('woff2'); font-weight: 100 800; }}
@font-face {{ font-family: Manrope; src: url('{F('node_modules/@fontsource-variable/manrope/files/manrope-latin-wght-normal.woff2')}') format('woff2'); font-weight: 200 800; }}
@font-face {{ font-family: 'Instrument Serif'; font-style: italic; src: url('{F('node_modules/@fontsource/instrument-serif/files/instrument-serif-latin-400-italic.woff2')}') format('woff2'); }}
@page {{ size: A4; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: Manrope, sans-serif; color: #071A33; font-size: 10.5pt; line-height: 1.5; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.page {{ width: 210mm; height: 297mm; position: relative; overflow: hidden; page-break-after: always; }}
.page:last-child {{ page-break-after: auto; }}
h1, h2, h3 {{ font-family: Sora, sans-serif; letter-spacing: -0.025em; line-height: 1.08; font-weight: 600; }}
.eyebrow {{ font-family: Sora; font-size: 7.5pt; letter-spacing: .2em; text-transform: uppercase; font-weight: 600; color: #A9480F; }}
.navy {{ background: #071A33; color: #F4F0E7; }} .navy .eyebrow {{ color: #C8A45D; }}
.ivory {{ background: #F4F0E7; }}
.pad {{ padding: 18mm 18mm; }}
.serif {{ font-family: 'Instrument Serif', serif; font-style: italic; font-weight: 400; }}
.muted {{ color: #4A5366; }} .navy .muted {{ color: #B9C1CF; }}
.foot {{ position: absolute; left: 18mm; right: 18mm; bottom: 10mm; display: flex; justify-content: space-between; font-size: 7.5pt; letter-spacing: .14em; text-transform: uppercase; font-family: Sora; color: #8C96A8; }}
/* cover */
.cover-bg {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: 50% 0; }}
.cover-img {{ position: absolute; right: -6mm; bottom: 0; height: 82%; width: auto; filter: drop-shadow(0 0 30px rgba(61,123,255,.45)); }}
.wm {{ font-family: Sora; font-weight: 650; font-size: 16pt; letter-spacing: -0.03em; }} .wm i {{ display: inline-block; width: 2.2mm; height: 2.2mm; border-radius: 50%; background: #F07832; margin-left: .6mm; box-shadow: 0 0 8px #F07832; }}
.cover-fade {{ position: absolute; inset: 0; background: linear-gradient(90deg, rgba(5,11,28,.92) 30%, rgba(5,11,28,.2) 65%, transparent), linear-gradient(0deg, rgba(5,11,28,.9), transparent 30%); }}
.cover-copy {{ position: absolute; left: 18mm; top: 0; bottom: 0; width: 105mm; display: flex; flex-direction: column; justify-content: center; gap: 7mm; }}
.cover h1 {{ font-size: 46pt; line-height: .98; }}
.cover h1 span {{ color: #F07832; display: block; }}
.mark {{ width: 15mm; height: 15mm; border: 1px solid #C8A45D; border-radius: 50%; display: grid; place-items: center; font-family: Sora; font-weight: 600; color: #C8A45D; font-size: 13pt; }}
.contact {{ font-family: Sora; font-size: 10pt; line-height: 1.7; }}
.contact b {{ color: #F07832; font-weight: 600; }}
/* grids */
.cols {{ display: grid; grid-template-columns: 1.25fr 1fr; gap: 12mm; }}
dl.facts div {{ display: grid; grid-template-columns: 30mm 1fr; gap: 4mm; padding: 2.6mm 0; border-bottom: .4pt solid rgba(7,26,51,.18); }}
dl.facts dt {{ font-size: 7.5pt; letter-spacing: .14em; text-transform: uppercase; font-weight: 700; color: #A9480F; padding-top: .6mm; }}
.box {{ background: #fff; border: .4pt solid rgba(7,26,51,.15); border-radius: 2mm; padding: 6mm; }}
.svc {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6mm 9mm; }}
.svc div {{ border-top: 1.2pt solid #F07832; padding-top: 3mm; }}
.svc h3 {{ font-size: 12.5pt; margin-bottom: 1.5mm; }}
.svc p {{ font-size: 9pt; }}
.svc .fm {{ font-size: 8pt; color: #B9C1CF; margin-top: 1.5mm; }}
.steps {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 4mm 7mm; counter-reset: s; }}
.steps div {{ border-top: .4pt solid rgba(244,240,231,.25); padding-top: 2.5mm; font-size: 8.5pt; }}
.steps b {{ display: block; font-family: Sora; font-weight: 600; font-size: 10pt; color: #F4F0E7; }}
table {{ width: 100%; border-collapse: collapse; font-size: 9pt; }}
th, td {{ text-align: left; padding: 2.2mm 2mm 2.2mm 0; border-bottom: .4pt solid rgba(7,26,51,.18); vertical-align: top; }}
thead th {{ font-family: Sora; font-size: 7pt; letter-spacing: .16em; text-transform: uppercase; color: #A9480F; }}
.credit {{ padding: 3.2mm 0; border-bottom: .4pt solid rgba(7,26,51,.18); display: grid; grid-template-columns: 24mm 1fr; gap: 4mm; }}
.credit .when {{ font-family: Sora; font-weight: 600; }}
.credit h3 {{ font-size: 10.5pt; letter-spacing: -0.01em; }}
.credit p {{ font-size: 8.5pt; }}
.tag {{ display: inline-block; font-family: Sora; font-size: 6.5pt; letter-spacing: .12em; text-transform: uppercase; padding: .5mm 1.6mm; background: #071A33; color: #F4F0E7; border-radius: .6mm; margin-bottom: 1mm; }}
.tag.award {{ background: #E9DFC6; color: #5E4718; }}
.src {{ font-size: 7.5pt; color: #4A5366; word-break: break-all; }}
"""

def page_cover():
    return f"""<section class="page navy cover" style="background:#040D1C">
  <img class="cover-bg" src="{STG('spotlight')}" alt="">
  <img class="cover-img" src="{CUT('green')}" alt="">
  <div class="cover-fade"></div>
  <div class="cover-copy">
    <div class="wm">Imelda Mutio<i></i></div>
    <p class="eyebrow">Media kit · {e(site['signature'])}</p>
    <h1>Imelda Mutio<span>Radio. MC. Events.</span></h1>
    <p class="muted" style="font-size:12.5pt;max-width:95mm">Good conversations. Great audiences. A radio presenter and MC who brings the warmth and quick thinking of live radio to corporate events, panels, galas, brand activations and workshops.</p>
    <div class="contact"><b>Bookings</b><br>{e(site['contact']['phoneDisplay'])}<br>{e(site['contact']['email'])}</div>
  </div>
  <div class="foot"><span>{e(site['location'])}</span><span>Media kit · October 2026</span></div>
</section>"""

def page_about():
    return f"""<section class="page ivory pad">
  <p class="eyebrow">About Imelda</p>
  <h2 style="font-size:24pt;margin:3mm 0 6mm;max-width:150mm">Warmth, energy and a real conversation.</h2>
  <div class="cols">
    <div>
      <p style="font-size:9.6pt">{e(bios['Full bio'])}</p>
      <p class="serif" style="font-size:14.5pt;line-height:1.2;margin-top:6mm;color:#071A33">“A strong host does more than hold a microphone. It is about reading the room, keeping the programme moving and making people feel included.”</p>
      <p class="eyebrow" style="margin-top:2mm">Imelda Mutio</p>
    </div>
    <div>
      <img src="{PH('studio-mic')}" style="width:100%;height:52mm;object-fit:cover;object-position:45% 30%;border-radius:2mm;margin-bottom:6mm" alt="">
      <dl class="facts">
        <div><dt>Known as</dt><dd>{e(site['signature'])}</dd></div>
        <div><dt>Based in</dt><dd>{e(site['location'])}; available across Kenya</dd></div>
        <div><dt>On air</dt><dd>{e(SHOWS[0][0] + ', ' + SHOWS[0][1].lower()) if SHOWS else ''}</dd></div>
        <div><dt>Brings</dt><dd>Clear communication, natural audience interaction, strong microphone presence, and the ability to read the room and adapt</dd></div>
      </dl>
    </div>
  </div>
  <div class="box" style="margin-top:6mm;font-size:9pt">
    <p class="eyebrow">Programme introduction for your MC script</p>
    <p style="margin-top:1.5mm;font-size:10pt">{e(bios['Programme introduction'])}</p>
    <p class="eyebrow" style="margin-top:4mm">Short bio</p>
    <p style="margin-top:2mm">{e(bios['Short bio'])}</p>
  </div>
  <div class="foot"><span>Imelda Mutio</span><span>02 / 04</span></div>
</section>"""

def page_services():
    svc = ''.join(f"<div><h3>{e(s['name'])}</h3><p>{e(s['short'])}</p><p class='fm'>{e(' · '.join(s['formats']))}</p></div>" for s in services)
    steps = [('Enquiry', 'Date, venue, format and audience. I confirm availability.'), ('Brief', 'Objectives, audience, speakers, sponsors and tone.'), ('Preparation', 'Programme, introductions, names, titles and guest questions.'), ('Sound check', 'A quick technical check and walk-through where the schedule allows.'), ('On the day', 'I arrive early, follow your cues and adjust live.'), ('Close', 'Sends people out on the right note, and on time.')]
    st = ''.join(f"<div><b>{i+1:02d} {e(t)}</b><span class='muted'>{e(d)}</span></div>" for i, (t, d) in enumerate(steps))
    return f"""<section class="page navy pad">
  <p class="eyebrow">Services</p>
  <h2 style="font-size:28pt;margin:3mm 0 9mm;max-width:160mm">Events I can host.</h2>
  <div class="svc">{svc}</div>
  <p class="muted" style="font-size:8pt;margin-top:5mm">Broadcast and interview hosting is subject to Imelda's broadcasting commitments and employer policy.</p>
  <p class="eyebrow" style="margin-top:10mm">Working with Imelda</p>
  <div class="steps" style="margin-top:4mm">{st}</div>
  <div class="foot"><span>Imelda Mutio</span><span>03 / 04</span></div>
</section>"""

def page_record():
    rows = ''.join(f"<div style='padding:3mm 0;border-bottom:.4pt solid rgba(7,26,51,.18)'><p class='eyebrow'>{e(w)}</p><h3 style='font-size:13pt;margin:1mm 0'>{e(n)}</h3><p class='muted' style='font-size:8.5pt'>{e(d)}</p></div>" for n, w, d in SHOWS)
    cr = ''.join(f"""<div class="credit"><span class="when">{e(c['displayDate'])}</span><div><span class="tag {'award' if c['section']=='award' else ''}">{'Award' if c['section']=='award' else 'Hosted'}</span><h3>{e(c.get('name') or c['title'])}</h3><p class="muted">{e(c.get('detail') or c['role'])}{(', ' + e(c['venue'])) if c.get('venue') else ''}</p><p class="src">Source: {e(c['url'])}</p></div></div>""" for c in credits)
    pr = ''.join(f"<li style='margin-bottom:1.6mm'><b>{e(p['title'])}</b> <span class='muted'>{e(p['publisher'])}, {e(p['displayDate'])}</span></li>" for p in press)
    socials = ' · '.join(f"{s['label']}: {s['url'].replace('https://www.', '')}" for s in site['social'])
    return f"""<section class="page ivory pad">
  <p class="eyebrow">The record</p>
  <h2 style="font-size:24pt;margin:3mm 0 6mm">On air, on stage, on record.</h2>
  <div class="cols" style="grid-template-columns:1fr 1fr">
    <div>
      <p class="eyebrow" style="margin-bottom:2mm">Selected live moments</p>
      <img src="{PH('speaking-orange')}" style="width:100%;height:44mm;object-fit:cover;object-position:48% 30%;border-radius:2mm;margin-bottom:3mm" alt="">
      <img src="{PH('family-fest')}" style="width:100%;height:44mm;object-fit:cover;object-position:50% 60%;border-radius:2mm" alt="">
      <p class="muted" style="font-size:8pt;margin-top:2mm">Corporate sessions, panels, workshops and festival stages.</p>
    </div>
    <div>
      <p class="eyebrow" style="margin-bottom:2mm">On air now</p>
      {rows}
      <p class="eyebrow" style="margin:6mm 0 2mm">Selected coverage</p>
      <ul style="list-style:none;font-size:8.5pt">{pr}</ul>
    </div>
  </div>
  <div class="box" style="position:absolute;left:18mm;right:18mm;bottom:20mm;background:#071A33;color:#F4F0E7;border:0">
    <div style="display:flex;justify-content:space-between;align-items:end;gap:8mm">
      <div><p class="eyebrow" style="color:#C8A45D">Bookings</p><p style="font-family:Sora;font-size:12.5pt;font-weight:600;margin-top:1mm">{e(site['contact']['phoneDisplay'])}<br>{e(site['contact']['email'])}</p><p style="font-size:8pt;color:#B9C1CF;margin-top:1.5mm">{e(socials)}</p></div>
      <p class="serif" style="font-size:15pt;color:#C8A45D;white-space:nowrap">{e(site['signOff'])}</p>
    </div>
    <p style="font-size:6.8pt;color:#B9C1CF;margin-top:3mm">{e(site['disclaimer'])}</p>
  </div>
  <div class="foot"><span>Imelda Mutio</span><span>04 / 04</span></div>
</section>"""

OG = f"""<html><head><meta charset="utf-8"><style>{CSS}
body {{ width:1200px; height:630px; background:#050B1C; color:#F4F0E7; position:relative; overflow:hidden; }}
img {{ position:absolute; right:0; top:0; width:600px; height:630px; object-fit:cover; object-position:50% 18%; }}
.f {{ position:absolute; inset:0; background:linear-gradient(90deg,#050B1C 44%,rgba(5,11,28,0) 60%); pointer-events:none; }}
.c {{ position:absolute; left:72px; top:0; bottom:0; display:flex; flex-direction:column; justify-content:center; gap:22px; width:700px; }}
h1 {{ font-size:84px; line-height:.98; }} h1 span {{ color:#F07832; display:block; }}
</style></head><body><img class="bg" src="{STG('spotlight')}" style="left:auto;right:0;width:640px;object-position:50% 0"><img src="{CUT('green')}" style="width:auto;height:600px;top:auto;bottom:0;right:40px;object-fit:contain;filter:drop-shadow(0 0 30px rgba(61,123,255,.5))"><div class="f"></div><div class="c">
<p class="eyebrow" style="font-size:18px;color:#C8A45D">Radio presenter · MC · Event host</p><h1>Imelda Mutio<span>Good conversations.</span></h1>
<p style="font-size:26px;color:#B9C1CF">Great audiences. Real impact.</p></div></body></html>"""

ICON = """<html><body style="margin:0;width:180px;height:180px;background:#071A33;display:grid;place-items:center">
<div style="width:110px;height:110px;border-radius:50%;background:radial-gradient(circle,#FFB27A 0,#F07832 35%,rgba(240,120,50,0) 70%)"></div></body></html>"""

async def main():
    doc = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{page_cover()}{page_about()}{page_services()}{page_record()}</body></html>"
    tmp = ROOT / 'scripts/.kit.html'; tmp.write_text(doc)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        await pg.goto(tmp.as_uri(), wait_until='networkidle')
        await pg.evaluate('document.fonts.ready')
        (ROOT / 'public/downloads').mkdir(parents=True, exist_ok=True)
        await pg.pdf(path=str(ROOT / 'public/downloads/imelda-mutio-media-kit.pdf'), format='A4', print_background=True, prefer_css_page_size=True)
        og = await b.new_page(viewport={'width': 1200, 'height': 630})
        (ROOT / 'scripts/.og.html').write_text(OG)
        await og.goto((ROOT / 'scripts/.og.html').as_uri(), wait_until='networkidle'); await og.evaluate('document.fonts.ready')
        await og.screenshot(path=str(ROOT / 'public/og-image.jpg'), type='jpeg', quality=88)
        ic = await b.new_page(viewport={'width': 180, 'height': 180})
        await ic.set_content(ICON); await ic.screenshot(path=str(ROOT / 'public/apple-touch-icon.png'))
        await b.close()
    for f in ['.kit.html', '.og.html']: (ROOT / 'scripts' / f).unlink()
    print('Built media kit PDF, og-image.jpg and apple-touch-icon.png')

asyncio.run(main())
