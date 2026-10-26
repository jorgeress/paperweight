import os
import sys
import time
from pathlib import Path

import cv2
from dotenv import load_dotenv


def open_camera(source: str) -> cv2.VideoCapture:
    if source.isdigit():
        return cv2.VideoCapture(int(source))
    return cv2.VideoCapture(source, cv2.CAP_FFMPEG)


def main() -> int:
    load_dotenv()
    source = os.environ.get("CAMERA_SOURCE", "0")
    camera = open_camera(source)
    if not camera.isOpened():
        print("[camera] cannot open source, check CAMERA_SOURCE")
        return 1
    # note: rtsp streams lag 1-2 s, drop a few buffered frames before keeping one
    for _ in range(10):
        camera.read()
    ok, frame = camera.read()
    camera.release()
    if not ok:
        print("[camera] no frame")
        return 1
    out = Path("frames") / f"frame-{int(time.time())}.jpg"
    out.parent.mkdir(exist_ok=True)
    cv2.imwrite(str(out), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    height, width = frame.shape[:2]
    print(f"[camera] saved {out} size={width}x{height}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
