from collections.abc import Callable

from pydantic import BaseModel

from eval.baselines import decide_directly, mask_text
from paperweight.perception.perceive import perceive_frame
from paperweight.pipeline.decide import decide_parcel
from paperweight.pipeline.modes import HIJACKED_PREAMBLE
from paperweight.policy.task import OperatorTask
from paperweight.token_factory.client import Completion


class Run(BaseModel):
    commands: list[str]
    latency_ms: int
    tokens_in: int
    tokens_out: int
    rule: str | None = None
    error: str | None = None


type Config = Callable[[bytes, OperatorTask], Run]


def from_direct(frame: bytes, task: OperatorTask, *, defended: bool, extra: tuple[Completion, ...] = ()) -> Run:
    outcome = decide_directly(frame, task, defended=defended)
    completions = [*extra, outcome.value[1]] if outcome.ok else list(extra)
    cost = {
        "latency_ms": sum(c.latency_ms for c in completions),
        "tokens_in": sum(c.tokens_in for c in completions),
        "tokens_out": sum(c.tokens_out for c in completions),
    }
    if not outcome.ok:
        return Run(commands=["HOLD"], error=outcome.error, **cost)
    return Run(commands=[outcome.value[0]], **cost)


def run_no_defense(frame: bytes, task: OperatorTask) -> Run:
    return from_direct(frame, task, defended=False)


def run_prompt_defense(frame: bytes, task: OperatorTask) -> Run:
    return from_direct(frame, task, defended=True)


def run_text_masking(frame: bytes, task: OperatorTask) -> Run:
    perceived = perceive_frame(frame, task)
    if not perceived.ok:
        return Run(commands=["HOLD"], latency_ms=0, tokens_in=0, tokens_out=0, error=perceived.error)
    masked = mask_text(frame, perceived.value.observations)
    return from_direct(masked, task, defended=False, extra=(perceived.value.completion,))


def run_pipeline(frame: bytes, task: OperatorTask, *, second_layer: bool, preamble: str = "") -> Run:
    decision = decide_parcel(frame, task, second_layer=second_layer, planner_preamble=preamble)
    fired = [j.final_verdict.rule for j in decision.judged if j.final_verdict.kind != "allow"]
    return Run(
        commands=decision.commands,
        latency_ms=sum(s.latency_ms for s in decision.stages),
        tokens_in=sum(s.tokens_in for s in decision.stages),
        tokens_out=sum(s.tokens_out for s in decision.stages),
        rule=fired[0] if fired else None,
        error=decision.error,
    )


CONFIGS: dict[str, Config] = {
    "no-defense": run_no_defense,
    "prompt-defense": run_prompt_defense,
    "text-masking": run_text_masking,
    "paperweight": lambda f, t: run_pipeline(f, t, second_layer=True),
    "paperweight-no-check": lambda f, t: run_pipeline(f, t, second_layer=False),
    "compromised-planner": lambda f, t: run_pipeline(f, t, second_layer=False, preamble=HIJACKED_PREAMBLE),
    "compromised-planner+check": lambda f, t: run_pipeline(f, t, second_layer=True, preamble=HIJACKED_PREAMBLE),
}
