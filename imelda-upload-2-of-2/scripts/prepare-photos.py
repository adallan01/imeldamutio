"""Prepares every image the site uses. Originals stay in source-photos/; outputs go to src/assets/.

  python3 scripts/prepare-photos.py

- Photos (source-photos/originals/*.jpg): Imelda's own portfolio photos, lightly cleaned and sharpened, true colour.
- Cut-outs (source-photos/cutouts/*.png): background already removed (see HANDOVER.md).
- Stage backgrounds (source-photos/stage/*.jpg): enlarged, cleaned, then colour-graded onto the brand's
  navy-to-beam-blue ramp so every background sits in the same blue world.
- Duotones: brand-blue versions of every card photo; the true colour shows on hover."""
from pathlib import Path
from PIL import Image, ImageFilter, ImageOps
import numpy as np, cv2
ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / 'source-photos', ROOT / 'src/assets'
for d in ['photos', 'cutouts', 'stage', 'thumbs', 'events', 'duo']: (OUT / d).mkdir(parents=True, exist_ok=True)

def sharpen(im, r=1.2, p=60): return im.filter(ImageFilter.UnsharpMask(radius=r, percent=p, threshold=2))
def fit_max(im, w=2400):
    if im.width > w: im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    return im
def enlarge(im, s): return im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
def clean(im, h=4):
    arr = cv2.fastNlMeansDenoisingColored(cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR), None, h, h, 7, 21)
    return Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))

# 1. Photos. studio-guest.jpg is kept in originals but not used: the station logo is on screen behind it.
PHOTOS = ['portrait-green', 'studio-mic', 'speaking-orange', 'crowd-orange', 'room-orange', 'stage-trio', 'family-fest', 'timer-coat']
for n in PHOTOS:
    im = ImageOps.exif_transpose(Image.open(SRC / 'originals' / f'{n}.jpg')).convert('RGB')
    im = clean(im, 3)
    if im.width < 1800: im = enlarge(im, 1800 / im.width)
    sharpen(fit_max(im), 1.1, 55).save(OUT / 'photos' / f'{n}.jpg', quality=90, optimize=True, progressive=True); print('photo', n, im.size)

# Green-shirt portrait placed on brand navy with a soft beam-blue glow (for About and the media kit).
cut = Image.open(SRC / 'cutouts/green.png').convert('RGBA'); cut = enlarge(cut, 1.8)
pad = int(cut.width * .35); bg = Image.new('RGBA', (cut.width + pad * 2, cut.height + int(cut.height * .06)), (8, 22, 58, 255))
yy, xx = np.mgrid[0:bg.height, 0:bg.width]
r = np.sqrt(((xx - bg.width * .5) / bg.width) ** 2 + ((yy - bg.height * .22) / bg.height) ** 2)
g = np.zeros((bg.height, bg.width, 4), np.uint8); g[..., 0] = 61; g[..., 1] = 123; g[..., 2] = 255; g[..., 3] = (np.clip(1 - r * 1.7, 0, 1) * 170).astype(np.uint8)
bg.alpha_composite(Image.fromarray(g)); bg.alpha_composite(cut, (pad, bg.height - cut.height))
sharpen(bg.convert('RGB'), 1.2, 50).save(OUT / 'photos/portrait-navy.jpg', quality=90, optimize=True, progressive=True); print('photo portrait-navy')

# 2. Cut-outs
for f in sorted((SRC / 'cutouts').glob('*.png')):
    im = Image.open(f).convert('RGBA'); im = im.crop(im.getbbox())
    if im.height < 2200: im = enlarge(im, 2200 / im.height)
    a = im.getchannel('A'); rgb = sharpen(im.convert('RGB'), 1.4, 55); rgb.putalpha(a)
    rgb.save(OUT / 'cutouts' / f'imelda-{f.stem}.png', optimize=True); print('cutout', f.stem)

# 3. Stage backgrounds, graded onto one blue ramp
ramp_pts = [(0, (3, 7, 20)), (70, (8, 22, 60)), (150, (30, 80, 200)), (205, (90, 150, 255)), (255, (225, 236, 255))]
lut = np.zeros((256, 3), np.float32)
for (a0, c0), (a1, c1) in zip(ramp_pts, ramp_pts[1:]):
    for i in range(a0, a1 + 1):
        t = (i - a0) / max(1, a1 - a0); lut[i] = np.array(c0) * (1 - t) + np.array(c1) * t
for f in sorted((SRC / 'stage').glob('*.jpg')):
    im = enlarge(Image.open(f).convert('RGB'), 2.5)
    arr = cv2.fastNlMeansDenoisingColored(cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR), None, 5, 5, 7, 21)
    arr = cv2.GaussianBlur(arr, (0, 0), 1.1)
    rgb = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB).astype(np.float32)
    lum = np.clip(rgb @ np.array([.299, .587, .114]), 0, 255).astype(np.uint8)
    out = lut[lum] * .82 + rgb * .18
    out += np.random.default_rng(7).normal(0, 3.0, out.shape[:2])[..., None]
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(OUT / 'stage' / f.name, quality=86, optimize=True, progressive=True)
    print('stage', f.stem)

# 4. Brand duotone versions (navy to beam blue to ice) for cards. The full-colour originals show on hover/focus.
duo_pts = [(0, (4, 10, 28)), (90, (14, 38, 96)), (170, (52, 112, 240)), (225, (150, 190, 255)), (255, (240, 245, 255))]
duo = np.zeros((256, 3), np.float32)
for (a0, c0), (a1, c1) in zip(duo_pts, duo_pts[1:]):
    for i in range(a0, a1 + 1):
        t = (i - a0) / max(1, a1 - a0); duo[i] = np.array(c0) * (1 - t) + np.array(c1) * t
def duotone(src, name, maxw=1400):
    im = fit_max(Image.open(src).convert('RGB'), maxw)
    g = np.array(ImageOps.autocontrast(ImageOps.grayscale(im), cutoff=1))
    Image.fromarray(duo[g].astype(np.uint8)).save(OUT / 'duo' / f'{name}.jpg', quality=86, optimize=True, progressive=True)
for n in PHOTOS + ['portrait-navy']: duotone(OUT / 'photos' / f'{n}.jpg', n)
print('duotones done')
