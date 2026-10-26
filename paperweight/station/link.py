import threading
import time
from collections.abc import Callable

import serial

from paperweight.outcome import Err, Ok, Outcome

BAUD = 115200
ALLOWED_COMMANDS = ("BIN A", "BIN B", "BIN C", "HOLD", "DENY", "PRIV OPEN", "PING")

type ArrivalListener = Callable[[int], None]


class SerialLink:
    def __init__(self, port: str, on_arrival: ArrivalListener) -> None:
        self.port = serial.Serial(port, BAUD, timeout=0.5)
        self.on_arrival = on_arrival
        self.lock = threading.Lock()
        self.last_reply = ""
        self.reader = threading.Thread(target=self.read_forever, daemon=True)
        self.reader.start()

    def read_forever(self) -> None:
        while self.port.is_open:
            line = self.port.readline().decode(errors="replace").strip()
            if not line:
                continue
            print(f"[station] <- {line}")
            if line.startswith("ARRIVAL "):
                self.on_arrival(int(line.split()[1]))
            else:
                self.last_reply = line

    def write_line(self, line: str) -> Outcome[str]:
        with self.lock:
            self.last_reply = ""
            self.port.write(f"{line}\n".encode())
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline and not self.last_reply:
                time.sleep(0.02)
        if self.last_reply.startswith("OK") or self.last_reply == "PONG":
            return Ok(self.last_reply)
        return Err(f"station replied {self.last_reply or 'nothing'} to {line}")


class SimulatedLink:
    def __init__(self, on_arrival: ArrivalListener) -> None:
        self.on_arrival = on_arrival
        self.sent: list[str] = []

    def write_line(self, line: str) -> Outcome[str]:
        self.sent.append(line)
        print(f"[station] sim -> {line}")
        return Ok(f"OK {line}")

    def simulate_arrival(self, distance_cm: int = 8) -> None:
        self.on_arrival(distance_cm)


type StationLink = SerialLink | SimulatedLink
