"""Replace the baked MetaHuman bottom underwear with skin in an exported body texture set.

The MetaHuman Optimized build bakes grey briefs into T_Body_BC (show_top_underwear only removes the top).
Swim bodies wear small bikinis/trunks made in Blender, so the briefs would show around them: this finds the
grey, desaturated texels and fills them by normalized convolution of the surrounding skin (colour) plus a
little fine noise; the normal and specular/roughness (SRMF) maps are filled the same way so the brief seams
and the fabric's matte finish disappear.

python tools/ue58/mh_skin_underwear.py D:/CodexTemp/mh/Ada_Swim   -> writes *_Skin.tga next to the inputs
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None


def underwear_mask(rgb):
    a = rgb.astype(np.int16)
    spread = a.max(axis=2) - a.min(axis=2)
    value = a.max(axis=2)
    mask = (spread < 22) & (value > 70)
    # Drop isolated specks (nails/teeth-like highlights), keep the garment panels and the waistband.
    mask = ndimage.binary_opening(mask, iterations=2)
    labels, n = ndimage.label(mask)
    sizes = ndimage.sum(mask, labels, range(1, n + 1))
    keep = np.isin(labels, 1 + np.flatnonzero(sizes > mask.size * 2e-5))
    return ndimage.binary_dilation(keep, iterations=max(9, rgb.shape[0] // 200))


def fill(img, mask, sigma):
    """Normalized convolution: average of the unmasked neighbourhood, widening until every texel is reached."""
    out = img.astype(np.float32).copy()
    known = (~mask).astype(np.float32)
    todo = mask.copy()
    s = sigma
    while todo.any():
        w = ndimage.gaussian_filter(known, s)
        for ch in range(out.shape[2]):
            v = ndimage.gaussian_filter(out[..., ch] * known, s)
            out[..., ch] = np.where(todo & (w > 1e-3), v / np.maximum(w, 1e-6), out[..., ch])
        reached = todo & (w > 1e-3)
        known = np.maximum(known, reached.astype(np.float32))
        todo &= ~reached
        s *= 2
    return out


def grain(shape, strength=1.6):
    """Fine luminance noise so the filled skin is not perfectly flat (the briefs' own detail is fabric)."""
    rng = np.random.default_rng(7)
    n = ndimage.gaussian_filter(rng.standard_normal(shape[:2]).astype(np.float32), 1.2)
    return (n / (n.std() + 1e-6) * strength)[..., None]


def main(folder):
    bc = np.asarray(Image.open(f'{folder}/T_Body_BC.tga').convert('RGB'))
    small = np.asarray(Image.fromarray(bc).resize((2048, 2048), Image.BILINEAR))
    mask_small = underwear_mask(small)
    Image.fromarray((mask_small * 255).astype(np.uint8)).save(f'{folder}/underwear_mask.png')
    # Work at 2048 for the colour fill, then upsample the fill and blend into the 8k texture.
    filled_small = fill(small, mask_small, 6)
    k = bc.shape[0] // 2048
    mask = np.asarray(Image.fromarray((mask_small * 255).astype(np.uint8)).resize(bc.shape[:2][::-1], Image.BILINEAR)) / 255.
    filled = np.asarray(Image.fromarray(np.clip(filled_small, 0, 255).astype(np.uint8)).resize(bc.shape[:2][::-1], Image.BICUBIC)).astype(np.float32)
    out = bc.astype(np.float32) * (1 - mask[..., None]) + (filled + grain(bc.shape)) * mask[..., None]
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(f'{folder}/T_Body_BC_Skin.tga')
    n = np.asarray(Image.open(f'{folder}/T_Body_N.tga').convert('RGB'))
    nmask = np.asarray(Image.fromarray((mask_small * 255).astype(np.uint8)).resize(n.shape[:2][::-1], Image.BILINEAR)) > 127
    nfill = fill(n, nmask, 4)
    Image.fromarray(np.clip(nfill, 0, 255).astype(np.uint8)).save(f'{folder}/T_Body_N_Skin.tga')
    # Specular/roughness: the briefs keep fabric values (roughness 255, specular ~127 against ~160 on skin),
    # which read as a lighter, matte band in the game. Fill them from the surrounding skin as well.
    srmf = np.asarray(Image.open(f'{folder}/T_Body_SRMF.tga').convert('RGBA'))
    smask = np.asarray(Image.fromarray((mask_small * 255).astype(np.uint8)).resize(srmf.shape[:2][::-1], Image.BILINEAR)) > 127
    sfill = fill(srmf, smask, 4)
    Image.fromarray(np.clip(sfill, 0, 255).astype(np.uint8), 'RGBA').save(f'{folder}/T_Body_SRMF_Skin.tga')
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).resize((1024, 1024)).save(f'{folder}/bc_skin_small.jpg', quality=90)
    print('mask texels %.2f%%' % (100 * mask_small.mean()))


if __name__ == '__main__':
    main(sys.argv[1])
