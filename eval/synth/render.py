import io
import random

from PIL import Image, ImageDraw, ImageFont

FONT_DIR = "/usr/share/fonts/TTF"
SIZE = (1024, 768)


def load_font(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"{FONT_DIR}/{name}", size)


def draw_card(lines: list[tuple[str, bool, int]], width: int, fill: str, rng: random.Random) -> Image.Image:
    height = 40 + sum(size + 14 for _, _, size in lines)
    card = Image.new("RGBA", (width, height), fill)
    pen = ImageDraw.Draw(card)
    pen.rectangle([0, 0, width - 1, height - 1], outline="black", width=3)
    y = 20
    for text, bold, size in lines:
        pen.text((24, y), text, fill="black", font=load_font(bold, size))
        y += size + 14
    return card.rotate(rng.uniform(-6, 6), expand=True, resample=Image.BICUBIC)


def label_lines(recipient: str, street: str, postal: str, city: str, tracking: str) -> list[tuple[str, bool, int]]:
    return [
        ("SHIP TO:", False, 22),
        (recipient, True, 34),
        (street, False, 26),
        (f"{postal} {city}", True, 40),
        (f"TRK {tracking}", False, 22),
    ]


def render_scene(
    label: list[tuple[str, bool, int]],
    rng: random.Random,
    *,
    sheet: list[str] | None = None,
    forged: list[tuple[str, bool, int]] | None = None,
    sticker: str | None = None,
    damaged: bool = False,
) -> bytes:
    scene = Image.new("RGB", SIZE, (88, 92, 96))
    pen = ImageDraw.Draw(scene)
    box = [rng.randint(40, 90), rng.randint(40, 80), rng.randint(900, 980), rng.randint(680, 730)]
    pen.rectangle(box, fill=(196, 160, 112), outline=(120, 90, 60), width=4)
    if damaged:
        for _ in range(6):
            x, y = rng.randint(box[0], box[2]), rng.randint(box[1], box[3])
            pen.line([x, y, x + rng.randint(-160, 160), y + rng.randint(-120, 120)], fill=(60, 40, 25), width=9)
        pen.ellipse([box[2] - 260, box[3] - 220, box[2] - 60, box[3] - 60], fill=(140, 110, 80))
    card = draw_card(label, 520, "white", rng)
    scene.paste(card, (rng.randint(100, 180), rng.randint(90, 150)), card)
    if forged:
        fake = draw_card(forged, 440, (255, 250, 235), rng)
        scene.paste(fake, (rng.randint(470, 540), rng.randint(330, 400)), fake)
    if sticker:
        tag = draw_card([(sticker, True, 30)], 320, (250, 220, 60), rng)
        scene.paste(tag, (rng.randint(560, 640), rng.randint(110, 170)), tag)
    if sheet:
        note = draw_card([(line, True, 26) for line in sheet], 500, (248, 248, 244), rng)
        scene.paste(note, (rng.randint(420, 500), rng.randint(380, 440)), note)
    buffer = io.BytesIO()
    scene.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()
