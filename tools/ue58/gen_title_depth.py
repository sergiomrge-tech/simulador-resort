"""Depth map of the title painting for the 2.5D title screen (10/11, Sergio: "a tela em 2.5d faça você").
The painting (SourceArt/UI/Title/T_TitleArt.png, made in Canva on 08/11) keeps its look; a monocular depth model reads
how far each part is (palm in front, boat, kiosk, village, hill, sky) and the title material (M_Title25D, built by
mare_title_art.material25d) slides every pixel by its depth as the view sways: a continuous parallax, no cut-out layers.
Model: Depth Anything V2 Small (Apache-2.0), run locally on the CPU; only the resulting map goes into the game.
  uv run --no-project --with torch --with transformers --with pillow --with numpy --with scipy \
      --extra-index-url https://download.pytorch.org/whl/cpu python tools/ue58/gen_title_depth.py
Output: SourceArt/UI/Title/T_TitleDepth.png (8-bit, white = near), smoothed so the slide has no hard tears."""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from transformers import pipeline

DIR = Path(__file__).resolve().parents[2] / 'unreal' / 'MareAlta' / 'SourceArt' / 'UI' / 'Title'


def main():
    art = Image.open(DIR / 'T_TitleArt.png').convert('RGB')
    pipe = pipeline('depth-estimation', model='depth-anything/Depth-Anything-V2-Small-hf')
    d = np.asarray(pipe(art)['predicted_depth'], dtype=np.float32)   # larger = nearer
    d = np.asarray(Image.fromarray(d).resize(art.size, Image.BICUBIC), dtype=np.float32)
    lo, hi = np.percentile(d, 1), np.percentile(d, 99)
    d = np.clip((d - lo) / max(hi - lo, 1e-6), 0, 1)
    # Edges softened (a hard step tears the picture when it slides), fine detail kept by mixing a light and a wide blur.
    d = .6 * ndimage.gaussian_filter(d, 3) + .4 * ndimage.gaussian_filter(d, 10)
    Image.fromarray((d * 255).astype(np.uint8), 'L').save(DIR / 'T_TitleDepth.png')
    print('ok', art.size, 'near share %.2f' % float((d > .6).mean()))


if __name__ == '__main__':
    main()
