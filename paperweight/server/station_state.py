import asyncio
import os
import threading
from pathlib import Path

from paperweight.camera.capture import capture_frame
from paperweight.ledger.log import append_decision, read_decisions
from paperweight.outcome import Err, Ok, Outcome
from paperweight.pipeline.decision import Decision
from paperweight.pipeline.modes import PipelineMode, decide_in_mode
from paperweight.policy.task import Grant, OperatorTask
from paperweight.station.execute import execute_decision
from paperweight.station.link import SerialLink, SimulatedLink, StationLink

FRAMES_DIR = Path("frames")


class StationState:
    def __init__(self, task: OperatorTask, ledger: Path, loop: asyncio.AbstractEventLoop) -> None:
        self.task = task
        self.ledger = ledger
        self.loop = loop
        self.camera_source = os.environ.get("CAMERA_SOURCE", "0")
        self.second_layer = os.environ.get("PAPERWEIGHT_SECOND_LAYER", "1") == "1"
        self.mode: PipelineMode = "paperweight"
        self.deciding = threading.Lock()
        self.subscribers: set[asyncio.Queue] = set()
        self.link: StationLink = self.open_link()

    def open_link(self) -> StationLink:
        port = os.environ.get("STATION_PORT", "")
        if port and Path(port).exists():
            print(f"[station] serial port={port}")
            return SerialLink(port, self.on_arrival)
        print("[station] no serial port, using the simulated station")
        return SimulatedLink(self.on_arrival)

    def on_arrival(self, distance_cm: int) -> None:
        print(f"[station] arrival distance_cm={distance_cm}")
        threading.Thread(target=self.decide_from_camera, daemon=True).start()

    def decide_from_camera(self) -> Outcome[Decision]:
        frame = capture_frame(self.camera_source)
        if not frame.ok:
            print(f"[camera] error={frame.error!r}")
            return frame
        return self.decide(frame.value)

    def decide(self, frame_jpeg: bytes) -> Outcome[Decision]:
        # note: one parcel at a time, the tray holds a single parcel
        if not self.deciding.acquire(blocking=False):
            return Err("a decision is already running")
        try:
            decision = decide_in_mode(frame_jpeg, self.task, self.mode, second_layer=self.second_layer)
            FRAMES_DIR.mkdir(exist_ok=True)
            (FRAMES_DIR / f"{decision.frame_sha}.jpg").write_bytes(frame_jpeg)
            sent = execute_decision(decision, self.link)
            if not sent.ok:
                print(f"[station] error={sent.error!r}")
            self.consume(decision.consumed_grants)
            append_decision(self.ledger, decision)
            self.publish(decision)
            return Ok(decision)
        finally:
            self.deciding.release()

    def consume(self, used: list[Grant]) -> None:
        if used:
            remaining = tuple(g for g in self.task.grants if g not in used)
            self.task = self.task.model_copy(update={"grants": remaining})

    def add_grant(self, grant: Grant) -> Outcome[OperatorTask]:
        if grant.kind not in self.task.privileged_actions:
            return Err(f"{grant.kind} is not a privileged action in this task")
        self.task = self.task.model_copy(update={"grants": (*self.task.grants, grant)})
        return Ok(self.task)

    def recent(self, limit: int = 50) -> list[Decision]:
        return read_decisions(self.ledger)[-limit:]

    def publish(self, decision: Decision) -> None:
        payload = decision.model_dump_json()
        for queue in list(self.subscribers):
            self.loop.call_soon_threadsafe(queue.put_nowait, payload)
