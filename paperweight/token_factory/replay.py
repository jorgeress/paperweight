import hashlib
import json
from pathlib import Path


def key_request(request: dict) -> str:
    canonical = json.dumps(request, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:24]


def load_recording(directory: Path, key: str) -> dict | None:
    path = directory / f"{key}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def save_recording(directory: Path, key: str, response: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{key}.json").write_text(json.dumps(response, indent=1))
