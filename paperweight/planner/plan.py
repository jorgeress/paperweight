from pydantic import BaseModel, ValidationError

from paperweight.outcome import Err, Ok, Outcome
from paperweight.planner.prompt import build_planner_messages
from paperweight.planner.schema import PLAN_SCHEMA, RawAction, RawPlan
from paperweight.policy.action import ProposedAction
from paperweight.policy.task import OperatorTask
from paperweight.provenance.observation import CitedValue, Observation
from paperweight.token_factory.client import VISION_MODEL, Completion, complete_json, parse_json


class Plan(BaseModel):
    actions: list[ProposedAction]
    completion: Completion


def plan_actions(task: OperatorTask, observations: list[Observation], preamble: str = "") -> Outcome[Plan]:
    # note: preamble exists for the eval's compromised-planner run, production passes nothing
    messages = build_planner_messages(task, observations, preamble)
    # note: thinking stays on, the second layer reads this reasoning
    sent = complete_json(VISION_MODEL, messages, "plan", PLAN_SCHEMA, thinking=True, max_tokens=12000)
    if not sent.ok:
        return sent
    parsed = parse_json(sent.value)
    if not parsed.ok:
        return parsed
    try:
        raw = RawPlan.model_validate(parsed.value)
    except ValidationError as error:
        return Err(f"plan schema: {error.error_count()} errors, first: {error.errors()[0]['msg']}")
    return Ok(Plan(actions=[to_action(a) for a in raw.actions], completion=sent.value))


def to_action(raw: RawAction) -> ProposedAction:
    # note: a repeated param name keeps the last value; the policy then judges that one
    params = {p.name: CitedValue(value=p.value, cite=p.cite) for p in raw.params}
    return ProposedAction(kind=raw.kind, params=params)
