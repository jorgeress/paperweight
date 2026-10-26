import os
import sys
import time

import serial
from dotenv import load_dotenv

COMMANDS = ["PING", "BIN A", "BIN B", "BIN C", "HOLD", "DENY", "PRIV OPEN"]


def read_until(link: serial.Serial, prefix: str, timeout_s: float) -> str | None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        raw = link.readline().decode(errors="replace").strip()
        if raw:
            print(f"[station] <- {raw}")
        if raw.startswith(prefix):
            return raw
    return None


def main() -> int:
    load_dotenv()
    port = os.environ.get("STATION_PORT", "/dev/ttyACM0")
    with serial.Serial(port, 115200, timeout=0.5) as link:
        # note: opening the port resets the uno, wait for its banner
        if read_until(link, "READY", 5) is None:
            print(f"[station] no READY on {port}")
            return 1
        for command in COMMANDS:
            print(f"[station] -> {command}")
            link.write(f"{command}\n".encode())
            read_until(link, "OK" if command != "PING" else "PONG", 3)
            time.sleep(1.5)
        print("[station] watching arrivals for 15 s, put something in front of the sensor")
        read_until(link, "__never__", 15)
    return 0


if __name__ == "__main__":
    sys.exit(main())
