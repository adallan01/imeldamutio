"""Turns Imelda's studio photos into studio-free portraits.

  python3 scripts/prepare-studio-photos.py

Sources: source-photos/studio/<name>.jpg (the station's promo frames, 1932 x 2576).
Masks:   source-photos/masks/edge-<name>.png   (isnet-general-use: crisp edges, but keeps chairs and mics)
         source-photos/masks/person-<name>.png (u2net_human_seg: person only, softer edges)
         Made with rembg: `rembg i -m isnet-general-use -om in.jpg out.png` (and -m u2net_human_seg).

What it does, per photo:
- keeps only Imelda: the edge mask, limited to where the person mask says there is a person;
  the chair, desk, screens, logos and the show artwork at the bottom of each frame are all removed;
- removes the white fringe from the old background around hair and shoulders;
- writes a transparent cut-out (src/assets/cutouts/imelda-<name>.png) for the hero and page heroes;
- writes a 4:5 portrait on an original, art-directed backdrop (src/assets/photos/<name>.jpg, 1600 x 2000):
  soft colour field, an arch, sound-wave rings and a few sparkles. No fake location: it reads as a
  coloured studio backdrop, which is what it is.
The overhead shot becomes a rose duotone crop instead (her arms rest on the desk, so a cut-out looks odd)."""
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw, ImageFont
import numpy as np, cv2, math

ROOT = Path(__file__).resolve().parent.parent
SRC, MASKS, OUT = ROOT / 'source-photos/studio', ROOT / 'source-photos/masks', ROOT / 'src/assets'
(OUT / 'cutouts').mkdir(parents=True, exist_ok=True); (OUT / 'photos').mkdir(parents=True, exist_ok=True)
W, H = 1600, 2000
rng = np.random.default_rng(11)

def hexc(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)

# Per photo: where the show artwork starts (crop above it), backdrop colours, and layout.
#   top/bottom: backdrop gradient; blobs: soft colour clouds (x, y, radius, colour, strength);
#   arch: colour of the arch behind her; ring: sound-wave ring colour; dark: light-on-dark styling.
LOOKS = {
  'pink':     dict(cut=1830, hx=.5, top='#FFE3EC', bottom='#FFB9CF', arch='#FFF4F7', ring='#FF5C93', blobs=[(.15, .2, .5, '#FF8FB6', .7), (.9, .75, .55, '#C9B6FF', .45)], fill=.9),
  'coral':    dict(cut=1840, top='#FFE9DC', bottom='#FFBE9E', arch='#FFF6EF', ring='#FF6F61', blobs=[(.85, .18, .5, '#FF9C7A', .6), (.1, .8, .55, '#FF8FB6', .45)], fill=.9),
  'trench':   dict(cut=1840, grow=11, hx=.52, top='#FBEDE4', bottom='#EBC6B8', arch='#FFF8F3', ring='#D9748C', blobs=[(.1, .15, .5, '#F4B6C2', .6), (.9, .85, .5, '#F2C7A5', .55)], fill=.86),
  'vest':     dict(cut=1840, grow=11, hx=.46, top='#F1E8FF', bottom='#F8CFE0', arch='#FFFFFF', ring='#B48CFF', blobs=[(.85, .2, .5, '#D9C6FF', .7), (.15, .85, .5, '#FFB3CC', .5)], fill=.86),
  'stripes':  dict(cut=1840, hx=.42, top='#FFEAF0', bottom='#FFC7D9', arch='#FFF7FA', ring='#FF5C93', blobs=[(.12, .22, .5, '#FFD1A8', .55), (.9, .7, .55, '#C9B6FF', .5)], fill=.84),
  'cardigan': dict(cut=1830, top='#2B1036', bottom='#5B1B4C', arch='#3C1648', ring='#FF7AA8', blobs=[(.5, .3, .55, '#FF5C93', .5), (.1, .9, .5, '#8E5BFF', .35)], fill=.92, dark=True),
  'group':    dict(cut=1880, top='#FFEDE6', bottom='#F9C9D6', arch='#FFF8F5', ring='#FF8FB6', blobs=[(.1, .15, .45, '#FFC9A8', .5), (.9, .2, .45, '#D9C6FF', .5)], fill=.9, wide=True, size=(2000, 1400)),
}

SRCNAME = {'coral': 'orange'}   # the orange pinstripe blazer

CUT = {n: v['cut'] for n, v in LOOKS.items()}
RESTORED = ROOT / 'source-photos/restored'

# Clean-up regions, in source pixels. 'dark': boxes where near-black, unsaturated pixels are the chair,
# a cable or the headphones (never her), so they are made transparent. 'head': traced outline of her head
# where the chair's headrest touches it; above 'above', nothing outside the outline is her.
FIX = {
  'pink': dict(head=[[(1000, 613), (1033, 618), (1067, 630), (1100, 650), (1127, 673), (1150, 703), (1167, 730), (1180, 763),
                      (1186, 797), (1186, 830), (1182, 863), (1176, 897), (1166, 923), (1152, 940), (1148, 1040), (748, 1040),
                      (712, 915), (716, 904), (745, 906), (768, 911), (772, 900), (775, 873), (782, 823), (788, 810), (791, 797),
                      (800, 763), (817, 730), (840, 700), (867, 670), (900, 643), (933, 627), (967, 617)],
                     [(714, 896), (720, 888), (786, 804), (792, 812), (722, 902)]],   # the arm of her glasses
              above=1012),
  'trench': dict(dark=[(180, 1590, 640, 1850), (430, 1000, 560, 1600), (1440, 1300, 1620, 1850)], firm=True, single=True),   # beige coat on a white wall
  'vest': dict(dark=[(300, 900, 720, 1850), (1080, 1100, 1420, 1700)], erase=[[(1110, 1560), (1190, 1562), (1230, 1570), (1265, 1586), (1300, 1590), (1340, 1582), (1372, 1564), (1395, 1546), (1460, 1546), (1460, 1840), (1110, 1840)]]),   # chair arm under her elbow
  'coral': dict(erase=[(380, 1340, 508, 1840)]),   # the chair's white post
  'stripes': dict(dark=[(0, 1000, 520, 1850), (1090, 1350, 1500, 1850)]),
}

def disk(r): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))

def load(name):
    src = SRCNAME.get(name, name); cut = CUT[name]
    r2 = np.array(Image.open(RESTORED / f'{src}.png').convert('RGB')).astype(np.float32) / 255
    r1 = cv2.resize(r2, (r2.shape[1] // 2, r2.shape[0] // 2), interpolation=cv2.INTER_AREA)
    y0 = LOOKS[name].get('y0', 0)
    edge = np.array(Image.open(MASKS / f'edge-{src}.png').convert('L')).astype(np.float64)[y0:cut] / 255
    person = np.array(Image.open(MASKS / f'person-{src}.png').convert('L')).astype(np.float64)[y0:cut] / 255
    h = min(r1.shape[0], cut - y0)
    return r1[:h], r2[:h * 2], edge[:h], person[:h]

def matte(name, rgb, edge, person):
    """Alpha matte: a trimap from the two segmentation masks, then closed-form matting (pymatting) in the
    uncertain band, solved in overlapping tiles and blended so there are no seams. Runs on the restored
    (de-blocked) image, so the edge follows her outline rather than JPEG blocks."""
    from pymatting import estimate_alpha_cf
    h, w = edge.shape; e, p = edge, person
    fg = cv2.erode((p > .5).astype(np.uint8), disk(16)).astype(bool) | cv2.erode(((e > .92) & (p > .4)).astype(np.uint8), disk(7)).astype(bool)
    near = cv2.dilate((p > .3).astype(np.uint8), disk(24)) > 0
    allowed = cv2.dilate(((p > .25) | ((e > .6) & near)).astype(np.uint8), disk(12)).astype(bool)
    tri = np.full((h, w), .5); tri[~allowed | (e < .03)] = 0; tri[fg] = 1
    fix = FIX.get(name, {})
    if 'head' in fix:
        # Above the shoulders, only her head (traced) can be her: outside the outline is background,
        # well inside it is her, and the matting decides the last few pixels.
        head = np.zeros((h, w), np.uint8); cv2.fillPoly(head, [np.array(q, np.int32) for q in fix['head']], 1)
        top = np.zeros((h, w), bool); top[:fix['above']] = True
        tri[top & (cv2.dilate(head, disk(3)) == 0)] = 0
        tri[top & (cv2.erode(head, disk(10)) > 0) & (tri == 0)] = .5
    for q in fix.get('erase', []):   # boxes or outlines that are never her
        if len(q) == 4 and not isinstance(q[0], tuple): x0, y0, x1, y1 = q; tri[y0:y1, x0:x1] = 0
        else: m = np.zeros((h, w), np.uint8); cv2.fillPoly(m, [np.array(q, np.int32)], 1); tri[m > 0] = 0
    unk = tri == .5
    acc = np.zeros((h, w)); wsum = np.zeros((h, w)); T, S = 448, 224
    ys = list(range(0, max(1, h - T), S)) + [max(0, h - T)]; xs = list(range(0, max(1, w - T), S)) + [max(0, w - T)]
    win = np.outer(np.hanning(T + 2)[1:-1], np.hanning(T + 2)[1:-1]) + 1e-3
    img = rgb.astype(np.float64)
    for y0 in ys:
        for x0 in xs:
            y1, x1 = min(h, y0 + T), min(w, x0 + T)
            if not unk[y0:y1, x0:x1].any(): continue
            t = tri[y0:y1, x0:x1]
            al = estimate_alpha_cf(img[y0:y1, x0:x1], t) if ((t == 1).any() and (t == 0).any()) else np.where(t == .5, e[y0:y1, x0:x1], t)
            ww = win[:y1 - y0, :x1 - x0]; acc[y0:y1, x0:x1] += al * ww; wsum[y0:y1, x0:x1] += ww
    a = np.where(unk, acc / np.maximum(wsum, 1e-9), tri).astype(np.float32)
    a = np.clip(a, 0, 1)
    if 'dark' in fix:
        hsv = cv2.cvtColor((rgb * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32) / 255
        v, sat = hsv[..., 2], hsv[..., 1]
        chair = np.clip((.26 - v) / .08, 0, 1) * np.clip((.3 - sat) / .1, 0, 1)
        chair = cv2.morphologyEx((chair > .5).astype(np.uint8), cv2.MORPH_OPEN, disk(2))
        chair = cv2.dilate(chair, disk(2)).astype(np.float32)
        box = np.zeros((h, w), np.float32)
        for x0, y0, x1, y1 in fix['dark']: box[y0:y1, x0:x1] = 1
        box = cv2.GaussianBlur(box, (0, 0), 6)
        a *= 1 - cv2.GaussianBlur(chair, (0, 0), 1.2) * box
        # Inside these boxes, faint leftovers are shadowed chair, not her: firm up the edge there.
        firm = np.clip((a - .42) / .26, 0, 1); firm = firm * firm * (3 - 2 * firm)
        a = a * (1 - box) + firm * box
    if fix.get('firm'):   # low-contrast edges (pale clothes on a pale wall): no see-through haze
        f = np.clip((a - .2) / .6, 0, 1); a = f * f * (3 - 2 * f)
    # Keep only the main figure(s): drop floating specks (or everything but her, for 'single').
    n, lab, stats, _ = cv2.connectedComponentsWithStats((a > .5).astype(np.uint8))
    if n > 1:
        keep = np.zeros(n, bool); big = stats[1:, cv2.CC_STAT_AREA].max()
        keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= (big if fix.get('single') else big * .03)
        solid = cv2.dilate(keep[lab].astype(np.uint8), disk(8)).astype(bool)
        a[~solid] = 0
    # Close pin-holes inside her (from the clean-up) without touching the outline.
    holes = cv2.morphologyEx((a > .5).astype(np.uint8), cv2.MORPH_CLOSE, disk(3)).astype(bool) & (a < .5) & (cv2.erode((a > .5).astype(np.uint8), disk(1)) == 0)
    return a

def foreground(r1, r2, a1):
    """Colour at the edges: estimate the true foreground colour (no white wall or black chair bleeding
    through), at 1x, then carry that correction onto the 2x restored image."""
    from pymatting import estimate_foreground_ml
    ys, xs = np.where(a1 > .01); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    F1 = r1.copy(); F1[y0:y1, x0:x1] = estimate_foreground_ml(r1[y0:y1, x0:x1].astype(np.float64), a1[y0:y1, x0:x1].astype(np.float64)).astype(np.float32)
    H2, W2 = r2.shape[:2]
    a2 = np.clip(cv2.resize(a1, (W2, H2), interpolation=cv2.INTER_CUBIC), 0, 1)
    d2 = cv2.resize(F1 - r1, (W2, H2), interpolation=cv2.INTER_LINEAR)
    t = np.clip((.985 - a2) / .3, 0, 1)[..., None]
    F2 = np.clip(r2 + d2 * t, 0, 1)
    return F2, a2

def grade(rgb):
    """A gentle, consistent finish: a touch of warmth and lift in the shadows. No smoothing of skin."""
    out = rgb * np.array([1.012, 1.0, .985], np.float32)
    out = out + (1 - out) * .015
    return np.clip(out, 0, 1)

def mic_sticker(canvas, pts, scale):
    """A playful sticker over the station's label on the microphone (stripes photo)."""
    (x0, y0), (x1, y1) = pts
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    L = math.hypot(x1 - x0, y1 - y0) * 1.08; T = 92 * scale
    s = Image.new('RGBA', (int(L + 40), int(T + 40)), (0, 0, 0, 0)); d = ImageDraw.Draw(s)
    d.rounded_rectangle([20, 20, 20 + L, 20 + T], radius=T / 2, fill=(255, 255, 255, 255))
    d.rounded_rectangle([28, 28, 12 + L, 12 + T], radius=T / 2 - 8, fill=(255, 92, 147, 255))
    try: f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', int(T * .44))
    except OSError: f = ImageFont.load_default()
    txt = 'ON AIR'
    tw = d.textlength(txt, font=f); d.text((20 + L / 2 - tw / 2, 20 + T / 2 - T * .27), txt, font=f, fill=(255, 255, 255, 255))
    for k, (sx, sy) in enumerate([(52, 20 + T / 2), (L - 12, 20 + T / 2)]):
        r = T * .16; d.polygon([(sx, sy - r), (sx + r * .3, sy - r * .3), (sx + r, sy), (sx + r * .3, sy + r * .3), (sx, sy + r), (sx - r * .3, sy + r * .3), (sx - r, sy), (sx - r * .3, sy - r * .3)], fill=(255, 255, 255, 255))
    s = s.rotate(-ang, expand=True, resample=Image.BICUBIC)
    sh = Image.new('RGBA', s.size, (60, 10, 40, 0)); sh.putalpha(s.getchannel('A').point(lambda v: v * .35).filter(ImageFilter.GaussianBlur(8)))
    canvas.alpha_composite(sh, (int(cx - s.width / 2 + 6), int(cy - s.height / 2 + 10)))
    canvas.alpha_composite(s, (int(cx - s.width / 2), int(cy - s.height / 2)))

def sparkle(d, x, y, r, col):
    d.polygon([(x, y - r), (x + r * .22, y - r * .22), (x + r, y), (x + r * .22, y + r * .22), (x, y + r), (x - r * .22, y + r * .22), (x - r, y), (x - r * .22, y - r * .22)], fill=col)

def backdrop(look, head_xy):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    t = (yy / H)[..., None]
    img = hexc(look['top']) * (1 - t) + hexc(look['bottom']) * t
    for bx, by, br, bc, st in look['blobs']:
        d = np.sqrt(((xx - bx * W) / W) ** 2 + ((yy - by * H) / W) ** 2) / br
        m = (np.exp(-d ** 2 * 2.2) * st)[..., None]
        img = img * (1 - m) + hexc(bc) * m
    base = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    hx, hy = head_xy
    # The arch: a tall rounded-top panel behind her.
    aw = W * (.78 if look.get('wide') else .62); ax0 = hx - aw / 2; atop = max(90, hy - W * .42)
    ac = tuple(int(v) for v in hexc(look['arch'])) + (150 if not look.get('dark') else 210,)
    d.rounded_rectangle([ax0, atop, ax0 + aw, H + 400], radius=aw / 2, fill=ac)
    # Sound-wave rings around her head.
    rc = tuple(int(v) for v in hexc(look['ring']))
    for k, rr in enumerate([W * .36, W * .45, W * .55]):
        d.ellipse([hx - rr, hy - rr, hx + rr, hy + rr], outline=rc + (int(120 - k * 30),), width=4)
    layer = layer.filter(ImageFilter.GaussianBlur(.6))
    base.alpha_composite(layer)
    # Sparkles and a few dots.
    sp = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(sp)
    white = (255, 255, 255, 235) if not look.get('dark') else (255, 214, 232, 235)
    for (x, y, r) in [(.13, .14, 42), (.86, .1, 30), (.9, .42, 22), (.08, .52, 18), (.78, .26, 14)]:
        sparkle(d, x * W, y * H, r, white)
    for _ in range(26):
        x, y = rng.uniform(0, W), rng.uniform(0, H * .7); r = rng.uniform(2, 5)
        d.ellipse([x - r, y - r, x + r, y + r], fill=white[:3] + (int(rng.uniform(90, 200)),))
    glow = sp.filter(ImageFilter.GaussianBlur(10)); base.alpha_composite(glow); base.alpha_composite(sp)
    return base

def grain(img, amt=4.0):
    a = np.array(img.convert('RGB')).astype(np.float32)
    a += rng.normal(0, amt, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def portrait(name):
    global W, H
    look = LOOKS[name]
    W, H = look.get('size', (1600, 2000))
    r1, r2, edge, person = load(name)
    a1 = matte(name, r1, edge, person)
    F2, a2 = foreground(r1, r2, a1)
    rgb = grade(F2); a = a2
    ys, xs = np.where(a > .5); x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), a.shape[0]
    pad = 40; x0, y0, x1 = max(0, x0 - pad), max(0, y0 - pad), min(a.shape[1], x1 + pad)
    cut = np.dstack([rgb[y0:y1, x0:x1], a[y0:y1, x0:x1]])
    cut_im = Image.fromarray((np.clip(cut, 0, 1) * 255 + .5).astype(np.uint8), 'RGBA')
    # Head position (for the rings and the arch): top of the figure, horizontally at the widest upper band.
    top_rows = a[y0:y0 + 760, x0:x1] > .5   # (2x pixels from here on)
    cols = np.where(top_rows.any(0))[0]; head_x_local = (cols.min() + cols.max()) / 2 if len(cols) else (x1 - x0) / 2
    # Place on the 4:5 canvas: as tall as the look asks, bottom on the bottom edge.
    # Scale by height; arms may run off the edge of the frame, like a real crop. Groups fit the width instead.
    if look.get('cover'): s = max(W / cut_im.width, H / cut_im.height)
    elif look.get('wide'): s = min(H * look['fill'] / cut_im.height, W * .98 / cut_im.width)
    else: s = H * look['fill'] / cut_im.height
    sub = cut_im.resize((round(cut_im.width * s), round(cut_im.height * s)), Image.LANCZOS)
    px = int((W - sub.width) / 2) if look.get('wide') else int(W * look.get('hx', .5) - head_x_local * s)
    py = (H - sub.height) // 2 if look.get('cover') else H - sub.height
    head = (px + head_x_local * s, py + 380 * s)
    bg = backdrop(look, head)
    # A wide, faint shadow straight below (no offset rim that would read as a halo), then her.
    al = sub.getchannel('A')
    sh = Image.new('RGBA', sub.size, (70, 10, 50, 0) if not look.get('dark') else (0, 0, 0, 0)); sh.putalpha(al.point(lambda v: v * (.16 if not look.get('dark') else .4)).filter(ImageFilter.GaussianBlur(44)))
    bg.alpha_composite(sh, (px, py + 26))
    if look.get('dark'):
        rim = Image.new('RGBA', sub.size, (255, 92, 147, 0)); rim.putalpha(al.filter(ImageFilter.GaussianBlur(26)).point(lambda v: v * .55))
        bg.alpha_composite(rim, (px, py))
    bg.alpha_composite(sub, (px, py))
    if name == 'stripes':
        # Label on the microphone, in source coordinates -> canvas coordinates.
        m = lambda X, Y: (px + (X - x0) * s, py + (Y - y0) * s)
        mic_sticker(bg, (m(2660, 2028), m(3156, 2228)), s * 2)
    grain(bg, 3.2).save(OUT / 'photos' / f'imelda-{name}.jpg', quality=90, optimize=True, progressive=True)
    # Transparent cut-out (sticker covers the mic label too).
    if name == 'stripes':
        tmp = Image.new('RGBA', cut_im.size, (0, 0, 0, 0)); tmp.alpha_composite(cut_im)
        mic_sticker(tmp, ((2660 - x0, 2028 - y0), (3156 - x0, 2228 - y0)), 2.0)
        tmp.putalpha(Image.fromarray(np.maximum(np.array(tmp.getchannel('A')), np.array(cut_im.getchannel('A')))))
        cut_im = tmp
    if not look.get('wide'):   # the group shot is used as a portrait only
        k = min(1, 2400 / cut_im.height, 2000 / cut_im.width)
        if k < 1: cut_im = cut_im.resize((round(cut_im.width * k), round(cut_im.height * k)), Image.LANCZOS)
        cut_im.save(OUT / 'cutouts' / f'imelda-{name}.png', optimize=True)
    print(name, 'portrait', bg.size, 'cut-out', cut_im.size)

def overhead():
    """Overhead shot: she leans in from above, peace sign up. The desk and studio behind her are melted
    into a soft rose blur (like a wide-open lens), so only she stays sharp."""
    r = np.array(Image.open(RESTORED / 'overhead.png').convert('RGB')).astype(np.float32) / 255
    h, w = r.shape[:2]
    p = np.array(Image.open(MASKS / 'person-overhead.png').convert('L').crop((0, 330, 1932, 1580)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255
    m = cv2.GaussianBlur(np.clip((p - .3) / .4, 0, 1), (0, 0), 6)[..., None]
    bg = cv2.GaussianBlur(r, (0, 0), 45)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    rose = np.dstack([np.ones((h, w)), .72 + .1 * xx / w, .84 + .08 * yy / h]).astype(np.float32)
    wash = rose * (.55 + .45 * (bg @ np.array([.3, .59, .11], np.float32)))[..., None]
    out = grade(r) * m + (bg * .25 + wash * .75) * (1 - m)
    img = Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype(np.uint8)).resize((2000, round(2000 * h / w)), Image.LANCZOS).convert('RGBA')
    sp = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(sp)
    for (x, y, rr) in [(.06, .1, 40), (.95, .14, 30), (.9, .84, 26), (.1, .86, 20)]:
        sparkle(d, x * img.width, y * img.height, rr, (255, 244, 248, 235))
    img.alpha_composite(sp.filter(ImageFilter.GaussianBlur(10))); img.alpha_composite(sp)
    grain(img, 2.6).save(OUT / 'photos' / 'imelda-overhead.jpg', quality=90, optimize=True, progressive=True)
    print('overhead', img.size)

def press():
    """Press portraits for the media kit page: full size downloads, and small previews."""
    dl = ROOT / 'public/downloads/portraits'; dl.mkdir(parents=True, exist_ok=True); (OUT / 'press').mkdir(exist_ok=True)
    for k, n in enumerate(['pink', 'coral', 'cardigan', 'trench'], 1):
        im = Image.open(OUT / 'photos' / f'imelda-{n}.jpg').convert('RGB')
        im.save(dl / f'imelda-mutio-portrait-{k}.jpg', quality=90, optimize=True, progressive=True)
        im.resize((800, 1000), Image.LANCZOS).save(OUT / 'press' / f'portrait-{k}.jpg', quality=86, optimize=True, progressive=True)
    print('press portraits')

if __name__ == '__main__':
    import sys
    for n in sys.argv[1:] or list(LOOKS) + ['overhead']:
        overhead() if n == 'overhead' else portrait(n)
    press()
