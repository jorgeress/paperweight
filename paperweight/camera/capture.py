import cv2

from paperweight.outcome import Err, Ok, Outcome

MAX_WIDTH = 1280


def capture_frame(source: str) -> Outcome[bytes]:
    camera = cv2.VideoCapture(int(source)) if source.isdigit() else cv2.VideoCapture(source, cv2.CAP_FFMPEG)
    if not camera.isOpened():
        return Err(f"cannot open camera source {redact_source(source)}")
    # note: rtsp streams lag 1-2 s, drop a few buffered frames before keeping one
    for _ in range(8):
        camera.read()
    grabbed, frame = camera.read()
    camera.release()
    if not grabbed:
        return Err("camera returned no frame")
    height, width = frame.shape[:2]
    if width > MAX_WIDTH:
        frame = cv2.resize(frame, (MAX_WIDTH, int(height * MAX_WIDTH / width)))
    encoded, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not encoded:
        return Err("jpeg encoding failed")
    return Ok(jpeg.tobytes())


def redact_source(source: str) -> str:
    # threat: rtsp urls carry the camera password, keep it out of logs and the console
    if "@" not in source:
        return source
    scheme, rest = source.split("://", 1)
    return f"{scheme}://***@{rest.split('@', 1)[1]}"
