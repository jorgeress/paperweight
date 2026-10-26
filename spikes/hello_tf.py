import base64
import io
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

load_dotenv()
client = OpenAI(base_url="https://api.tokenfactory.nebius.com/v1/", api_key=os.environ["NEBIUS_API_KEY"])

VL = "nvidia/Nemotron-3.5-Super-VL"
FAST = "nvidia/Nemotron-3_5-Lightning"

ROUTE_TOOL = {
    "type": "function",
    "function": {
        "name": "route_parcel",
        "description": "Send the parcel on the tray to a bin.",
        "parameters": {
            "type": "object",
            "properties": {
                "bin": {"type": "string", "enum": ["A", "B", "C", "HOLD"]},
                "destination_read": {"type": "string", "description": "destination text read from the label"},
            },
            "required": ["bin", "destination_read"],
        },
    },
}

TASK = "Operator task: route parcels by destination city. Madrid -> A, Paris -> B, any other city -> C. Damaged or unreadable -> HOLD."


def list_models():
    ids = sorted(m.id for m in client.models.list().data)
    nvidia = [i for i in ids if "nvidia" in i.lower() or "nemotron" in i.lower()]
    print(f"[models] total={len(ids)} nvidia={len(nvidia)}")
    for i in nvidia:
        print("   ", i)
    return ids


def make_label() -> str:
    img = Image.new("RGB", (900, 600), (205, 170, 125))
    d = ImageDraw.Draw(img)
    d.rectangle([150, 120, 750, 480], fill="white", outline="black", width=4)
    try:
        font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 44)
        small = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", 30)
    except OSError:
        font = small = ImageFont.load_default()
    d.text((180, 150), "SHIP TO:", fill="black", font=small)
    d.text((180, 200), "Laura Gomez", fill="black", font=font)
    d.text((180, 260), "Calle Mayor 12", fill="black", font=small)
    d.text((180, 310), "28013 MADRID", fill="black", font=font)
    d.text((180, 400), "TRK 4471-0923", fill="black", font=small)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def call(model, messages, tools):
    t0 = time.time()
    r = client.chat.completions.create(model=model, messages=messages, tools=tools, temperature=0, max_tokens=2048)
    dt = time.time() - t0
    m = r.choices[0].message
    calls = [(c.function.name, c.function.arguments) for c in (m.tool_calls or [])]
    print(f"[{model}] {dt:.1f}s finish={r.choices[0].finish_reason} usage={r.usage.prompt_tokens}/{r.usage.completion_tokens}")
    print("   tool_calls:", calls or "none")
    if not calls:
        print("   content:", (m.content or "")[:400])
    reasoning = getattr(m, "reasoning_content", None) or (m.model_extra or {}).get("reasoning_content")
    if reasoning:
        print("   reasoning (first 300):", reasoning[:300].replace("\n", " "))


def main():
    ids = list_models()
    for want in (VL, FAST):
        print(f"[check] {want} listed={want in ids}")

    call(FAST, [{"role": "system", "content": TASK}, {"role": "user", "content": "The label reads: 75008 PARIS. Route it."}], [ROUTE_TOOL])

    b64 = base64.b64encode(Path(sys.argv[1]).read_bytes()).decode() if len(sys.argv) > 1 else make_label()
    call(
        VL,
        [
            {"role": "system", "content": TASK},
            {"role": "user", "content": [
                {"type": "text", "text": "Camera frame of the tray. Route the parcel."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            ]},
        ],
        [ROUTE_TOOL],
    )


if __name__ == "__main__":
    main()
