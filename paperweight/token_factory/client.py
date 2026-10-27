import json
import os
import time
from pathlib import Path
from typing import Literal

from openai import APIError, OpenAI
from pydantic import BaseModel

from paperweight.outcome import Err, Ok, Outcome
from paperweight.token_factory.budget import LIVE_BUDGET
from paperweight.token_factory.replay import key_request, load_recording, save_recording

BASE_URL = "https://api.tokenfactory.nebius.com/v1/"
VISION_MODEL = "nvidia/Nemotron-3.5-Super-VL"
FAST_MODEL = "nvidia/Nemotron-3_5-Lightning"
RECORDINGS_DIR = Path(os.environ.get("PAPERWEIGHT_RECORDINGS", "recordings"))
TRUNCATED = "hit max_tokens"

# note: live calls the api; record also saves responses; replay never touches the network
type CallMode = Literal["live", "record", "replay"]


class Completion(BaseModel):
    model: str
    content: str
    reasoning: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    replayed: bool


def read_call_mode() -> CallMode:
    mode = os.environ.get("PAPERWEIGHT_MODE", "record")
    if mode not in ("live", "record", "replay"):
        raise ValueError(f"PAPERWEIGHT_MODE={mode!r} must be live, record or replay")
    return mode


def complete_json(
    model: str,
    messages: list[dict],
    schema_name: str,
    schema: dict,
    *,
    thinking: bool,
    max_tokens: int = 4096,
    timeout_s: float = 60,
    retries: int = 2,
) -> Outcome[Completion]:
    request = {
        "model": model,
        "messages": messages,
        # note: token factory wants the openai shape {name, schema}; its docs example sends the bare schema and gets a 422
        "response_format": {"type": "json_schema", "json_schema": {"name": schema_name, "schema": schema, "strict": True}},
        "temperature": 0,
        "max_tokens": max_tokens,
        "extra_body": {"chat_template_kwargs": {"enable_thinking": thinking}},
    }
    key = key_request(request)
    mode = read_call_mode()
    if mode != "live":
        recorded = load_recording(RECORDINGS_DIR, key)
        if recorded is not None and "error" in recorded:
            return Err(recorded["error"])
        if recorded is not None:
            return Ok(Completion(**recorded, replayed=True))
        if mode == "replay":
            return Err(f"no recording for request {key}")
    taken = LIVE_BUDGET.take_call()
    if not taken.ok:
        print(f"[token_factory] refused model={model} reason=budget")
        return taken
    sent = send_request(request, timeout_s, retries)
    if mode == "record" and sent.ok:
        save_recording(RECORDINGS_DIR, key, sent.value.model_dump(exclude={"replayed"}))
    # note: a max_tokens cut is the model's answer to this request, so it replays; network errors do not
    if mode == "record" and not sent.ok and sent.error.endswith(TRUNCATED):
        save_recording(RECORDINGS_DIR, key, {"error": sent.error})
    return sent


def send_request(request: dict, timeout_s: float, retries: int) -> Outcome[Completion]:
    client = OpenAI(base_url=BASE_URL, api_key=os.environ["NEBIUS_API_KEY"], max_retries=retries, timeout=timeout_s)
    started = time.monotonic()
    try:
        response = client.chat.completions.create(**request)
    except APIError as error:
        return Err(f"token factory: {type(error).__name__}: {error.message}")
    latency_ms = int((time.monotonic() - started) * 1000)
    choice = response.choices[0]
    message = choice.message
    if choice.finish_reason == "length":
        return Err(f"token factory: {request['model']} {TRUNCATED}")
    reasoning = (message.model_extra or {}).get("reasoning_content") or ""
    return Ok(
        Completion(
            model=request["model"],
            content=message.content or "",
            reasoning=reasoning,
            latency_ms=latency_ms,
            tokens_in=response.usage.prompt_tokens,
            tokens_out=response.usage.completion_tokens,
            replayed=False,
        )
    )


def parse_json(completion: Completion) -> Outcome[dict]:
    try:
        return Ok(json.loads(completion.content))
    except json.JSONDecodeError as error:
        return Err(f"{completion.model} returned invalid json: {error}")
