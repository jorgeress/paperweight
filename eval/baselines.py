import io

from PIL import Image, ImageDraw

from paperweight.baseline.direct import decide_directly
from paperweight.provenance.observation import Observation

__all__ = ["decide_directly", "mask_text"]


def mask_text(frame_jpeg: bytes, observations: list[Observation]) -> bytes:
    # note: the literature's strongest defense, blank every text region the detector found
    image = Image.open(io.BytesIO(frame_jpeg)).convert("RGB")
    width, height = image.size
    pen = ImageDraw.Draw(image)
    for o in observations:
        if o.kind == "object":
            continue
        x0, y0, x1, y1 = o.bbox
        pad = 12
        pen.rectangle(
            [x0 * width / 1000 - pad, y0 * height / 1000 - pad, x1 * width / 1000 + pad, y1 * height / 1000 + pad],
            fill=(128, 128, 128),
        )
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()
