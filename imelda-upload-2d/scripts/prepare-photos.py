"""Prepares every image the site uses. Originals stay in source-photos/; outputs go to src/assets/.

  python3 scripts/prepare-photos.py

- Photos (source-photos/originals/*.jpg): Imelda's own event photos, restored with Real-ESRGAN (scripts/esrgan.py:
  removes JPEG blocking and noise, doubles the resolution), true colour.
- Stage backgrounds (source-photos/stage/*.jpg): restored and enlarged the same way, then colour-graded onto the
  brand's plum-to-rose ramp so every background sits in the same rose-lit world.
The studio portraits are made by scripts/restore-studio.py + scripts/prepare-studio-photos.py."""
from pathlib import Path
from PIL import Image, ImageFilter, ImageOps
import numpy as np, cv2, sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from esrgan import restore
ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / 'source-photos', ROOT / 'src/assets'
for d in ['photos', 'stage', 'thumbs', 'events']: (OUT / d).mkdir(parents=True, exist_ok=True)

def sharpen(im, r=1.2, p=60): return im.filter(ImageFilter.UnsharpMask(radius=r, percent=p, threshold=2))
def fit_max(im, w=2400):
    if im.width > w: im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    return im
def enlarge(im, s): return im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
def clean(im, h=4):
    arr = cv2.fastNlMeansDenoisingColored(cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR), None, h, h, 7, 21)
    return Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))

# 1. Photos. studio-guest.jpg and studio-mic.jpg stay in originals but are not used: they show the station's studio.
PHOTOS = ['portrait-green', 'speaking-orange', 'crowd-orange', 'room-orange', 'stage-trio', 'family-fest', 'timer-coat']
for n in PHOTOS:
    im = np.array(ImageOps.exif_transpose(Image.open(SRC / 'originals' / f'{n}.jpg')).convert('RGB'))
    scale = min(2, 2400 / max(im.shape[:2]))
    out = Image.fromarray(restore(im, scale=scale, denoise=.4))
    fit_max(out).save(OUT / 'photos' / f'{n}.jpg', quality=90, optimize=True, progressive=True); print('photo', n, out.size)

# 2. Stage backgrounds, graded onto one plum-to-rose ramp
ramp_pts = [(0, (14, 6, 24)), (70, (44, 14, 58)), (150, (150, 40, 110)), (205, (255, 120, 170)), (255, (255, 230, 240))]
lut = np.zeros((256, 3), np.float32)
for (a0, c0), (a1, c1) in zip(ramp_pts, ramp_pts[1:]):
    for i in range(a0, a1 + 1):
        t = (i - a0) / max(1, a1 - a0); lut[i] = np.array(c0) * (1 - t) + np.array(c1) * t
for f in sorted((SRC / 'stage').glob('*.jpg')):
    rgb = restore(np.array(Image.open(f).convert('RGB')), scale=2.5, denoise=.7).astype(np.float32)
    lum = np.clip(rgb @ np.array([.299, .587, .114]), 0, 255).astype(np.uint8)
    out = lut[lum] * .82 + rgb * .18
    out += np.random.default_rng(7).normal(0, 3.0, out.shape[:2])[..., None]
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(OUT / 'stage' / f.name, quality=86, optimize=True, progressive=True)
    print('stage', f.stem)

