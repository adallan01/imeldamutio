"""Real-ESRGAN (realesr-general-x4v3, SRVGG compact) photo restoration, CPU, tiled.

Weights (not committed; download once into scripts/.models/):
  https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth
  https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-wdn-x4v3.pth
Usage from python: restore(rgb_uint8, scale=2, denoise=.5) -> uint8 (H*scale, W*scale, 3)
"""
from pathlib import Path
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F

MODELS = Path(__file__).resolve().parent / '.models'

class SRVGG(nn.Module):
    def __init__(self, feat=64, conv=32, up=4):
        super().__init__()
        self.up = up
        body = [nn.Conv2d(3, feat, 3, 1, 1), nn.PReLU(feat)]
        for _ in range(conv): body += [nn.Conv2d(feat, feat, 3, 1, 1), nn.PReLU(feat)]
        body += [nn.Conv2d(feat, 3 * up * up, 3, 1, 1)]
        self.body = nn.ModuleList(body); self.ps = nn.PixelShuffle(up)
    def forward(self, x):
        y = x
        for m in self.body: y = m(y)
        return self.ps(y) + F.interpolate(x, scale_factor=self.up, mode='nearest')

_net = {}
def net(denoise):
    key = round(denoise, 2)
    if key not in _net:
        a = torch.load(MODELS / 'realesr-general-x4v3.pth', map_location='cpu')['params']
        b = torch.load(MODELS / 'realesr-general-wdn-x4v3.pth', map_location='cpu')['params']
        # denoise=1: full general model (strong clean-up); denoise=0: the weak-denoise model (keeps texture).
        sd = {k: denoise * a[k] + (1 - denoise) * b[k] for k in a}
        m = SRVGG(); m.load_state_dict(sd); m.eval(); _net[key] = m
    return _net[key]

@torch.no_grad()
def restore(rgb, scale=2, denoise=.5, tile=384, pad=16):
    torch.set_num_threads(4)
    m = net(denoise)
    x = torch.from_numpy(rgb.astype(np.float32) / 255).permute(2, 0, 1)[None]
    _, _, H, W = x.shape
    out = torch.zeros(1, 3, H * 4, W * 4)
    for y0 in range(0, H, tile):
        for x0 in range(0, W, tile):
            y1, x1 = min(H, y0 + tile), min(W, x0 + tile)
            py0, px0, py1, px1 = max(0, y0 - pad), max(0, x0 - pad), min(H, y1 + pad), min(W, x1 + pad)
            o = m(x[:, :, py0:py1, px0:px1])
            out[:, :, y0 * 4:y1 * 4, x0 * 4:x1 * 4] = o[:, :, (y0 - py0) * 4:(y0 - py0 + y1 - y0) * 4, (x0 - px0) * 4:(x0 - px0 + x1 - x0) * 4]
    if scale != 4:
        out = F.interpolate(out, size=(round(H * scale), round(W * scale)), mode='area')
    return (out[0].permute(1, 2, 0).clamp(0, 1).numpy() * 255 + .5).astype(np.uint8)
