"""Open-source line icons (Lucide, ISC licence, npm lucide-static) rendered to PIL sprites in any colour."""
import io, os, re, functools
import cairosvg
from PIL import Image
ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
@functools.lru_cache(maxsize=256)
def icon(name, size=160, col=(206, 244, 30), stroke=2.0):
    s = open(os.path.join(ICON_DIR, name + ".svg")).read()
    s = s.replace("currentColor", "#%02x%02x%02x" % col[:3])
    s = re.sub(r'stroke-width="[\d.]+"', f'stroke-width="{stroke}"', s)
    png = cairosvg.svg2png(bytestring=s.encode(), output_width=size, output_height=size)
    return Image.open(io.BytesIO(png)).convert("RGBA")
