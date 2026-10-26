import asyncio
import json
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from paperweight.camera.capture import redact_source
from paperweight.pipeline.decision import PipelineMode
from paperweight.policy.task import Grant, OperatorTask
from paperweight.server.station_state import FRAMES_DIR, StationState
from paperweight.station.link import SimulatedLink
from paperweight.token_factory.client import read_call_mode

load_dotenv()

TASK_FILE = Path(os.environ.get("PAPERWEIGHT_TASK", "tasks/sorting.json"))
LEDGER_FILE = Path(os.environ.get("PAPERWEIGHT_LEDGER", "ledger/decisions.jsonl"))
CONSOLE_DIST = Path("console/dist")
SAMPLES_DIR = Path(os.environ.get("PAPERWEIGHT_SAMPLES", "eval/corpus/synth"))
# note: public mode is the hosted demo, read-only and replaying recorded model calls
IS_PUBLIC = os.environ.get("PAPERWEIGHT_PUBLIC") == "1"
MAX_FRAME_BYTES = 4 * 1024 * 1024


@asynccontextmanager
async def lifespan(app: FastAPI):
    if IS_PUBLIC and read_call_mode() != "replay":
        raise RuntimeError("PAPERWEIGHT_PUBLIC=1 requires PAPERWEIGHT_MODE=replay, a public demo must not spend credits")
    task = OperatorTask.model_validate_json(TASK_FILE.read_text())
    app.state.station = StationState(task, LEDGER_FILE, asyncio.get_running_loop())
    yield


app = FastAPI(lifespan=lifespan)


class PipelineChoice(BaseModel):
    mode: PipelineMode


def station(request: Request) -> StationState:
    return request.app.state.station


@app.get("/api/state")
def read_state(request: Request) -> dict:
    s = station(request)
    return {
        "task": s.task.model_dump(mode="json"),
        "mode": read_call_mode(),
        "station": "simulated" if isinstance(s.link, SimulatedLink) else "serial",
        "camera": redact_source(s.camera_source),
        "second_layer": s.second_layer,
        "public": IS_PUBLIC,
        "pipeline": s.mode,
        "decisions": [d.model_dump(mode="json") for d in s.recent()],
    }


@app.put("/api/task")
def replace_task(request: Request, task: OperatorTask) -> dict:
    refuse_in_public()
    station(request).task = task
    print(f"[console] task replaced routing={task.routing}")
    return task.model_dump(mode="json")


@app.put("/api/pipeline")
def set_pipeline(request: Request, choice: PipelineChoice) -> dict:
    refuse_in_public()
    station(request).mode = choice.mode
    print(f"[console] pipeline mode={choice.mode}")
    return {"pipeline": choice.mode}


@app.post("/api/grants")
def add_grant(request: Request, grant: Grant) -> dict:
    refuse_in_public()
    added = station(request).add_grant(grant)
    if not added.ok:
        raise HTTPException(status_code=422, detail=added.error)
    print(f"[console] grant kind={grant.kind} params={grant.params}")
    return added.value.model_dump(mode="json")


@app.post("/api/decide")
async def decide(request: Request) -> dict:
    refuse_in_public()
    s = station(request)
    body = await request.body()
    if len(body) > MAX_FRAME_BYTES:
        raise HTTPException(status_code=413, detail="frame too large")
    if body and not body.startswith(b"\xff\xd8"):
        raise HTTPException(status_code=415, detail="send a jpeg body, or no body to use the camera")
    decided = await run_in_threadpool(s.decide, body) if body else await run_in_threadpool(s.decide_from_camera)
    if not decided.ok:
        raise HTTPException(status_code=409, detail=decided.error)
    return decided.value.model_dump(mode="json")


@app.post("/api/arrival")
def simulate_arrival(request: Request) -> dict:
    refuse_in_public()
    s = station(request)
    if not isinstance(s.link, SimulatedLink):
        raise HTTPException(status_code=409, detail="a real station is connected, use the sensor")
    s.link.simulate_arrival()
    return {"ok": True}


@app.get("/api/samples")
def list_samples() -> list[dict]:
    cases = json.loads((SAMPLES_DIR / "cases.json").read_text())
    return [{k: c[k] for k in ("id", "kind", "category", "note")} for c in cases]


@app.post("/api/samples/{sample_id}/decide")
async def decide_sample(request: Request, sample_id: str, mode: PipelineMode | None = None) -> dict:
    # threat: path traversal through the sample id
    if not re.fullmatch(r"[a-z]+-\d{3}", sample_id):
        raise HTTPException(status_code=404)
    path = SAMPLES_DIR / f"{sample_id}.jpg"
    if not path.exists():
        raise HTTPException(status_code=404)
    # note: the mode travels with the request so visitors of the public demo do not switch it for each other
    decided = await run_in_threadpool(station(request).decide, path.read_bytes(), mode)
    if not decided.ok:
        raise HTTPException(status_code=409, detail=decided.error)
    return decided.value.model_dump(mode="json")


def refuse_in_public() -> None:
    if IS_PUBLIC:
        raise HTTPException(status_code=403, detail="read-only demo: run Paperweight locally to change the task or use a camera")


@app.get("/api/events")
async def stream_events(request: Request) -> StreamingResponse:
    s = station(request)
    queue: asyncio.Queue = asyncio.Queue()
    s.subscribers.add(queue)

    async def events():
        try:
            while not await request.is_disconnected():
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15)
                    yield f"event: decision\ndata: {payload}\n\n"
                except TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            s.subscribers.discard(queue)

    return StreamingResponse(events(), media_type="text/event-stream")


@app.get("/api/frames/{sha}.jpg")
def read_frame(sha: str) -> FileResponse:
    # threat: path traversal through the frame id
    if len(sha) != 64 or not all(c in "0123456789abcdef" for c in sha):
        raise HTTPException(status_code=404)
    path = FRAMES_DIR / f"{sha}.jpg"
    if not path.exists():
        raise HTTPException(status_code=404)
    return FileResponse(path, media_type="image/jpeg")


if CONSOLE_DIST.exists():
    app.mount("/", StaticFiles(directory=CONSOLE_DIST, html=True), name="console")
