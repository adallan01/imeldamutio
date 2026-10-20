"""Step 1 for the studio portraits: restore each photo with Real-ESRGAN (2x, light denoise).

  python3 scripts/restore-studio.py [names...]

Writes source-photos/restored/<name>.png (2x, cropped to the area above the show artwork).
The originals are Instagram-compressed phone frames: this removes JPEG blocking and noise and
crisps up glasses, eyes and fabric without changing her features. Cached: delete a file to redo it."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
from esrgan import restore

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / 'source-photos/studio', ROOT / 'source-photos/restored'
OUT.mkdir(exist_ok=True)
CUT = {'pink': 1830, 'cardigan': 1830, 'group': 1880}   # where the show artwork begins (default 1840)
names = sys.argv[1:] or ['pink', 'orange', 'trench', 'vest', 'stripes', 'cardigan', 'group', 'overhead']
for n in names:
    f = OUT / f'{n}.png'
    if f.exists(): print('cached', n); continue
    im = np.array(Image.open(SRC / f'{n}.jpg').convert('RGB'))
    im = im[:CUT.get(n, 1840)] if n != 'overhead' else im[330:1580]
    out = restore(im, scale=2, denoise=.3)
    Image.fromarray(out).save(f, compress_level=3); print('restored', n, out.shape)
