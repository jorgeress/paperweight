from paperweight.policy.action import ProposedAction
from paperweight.policy.rules import (
    check_action_in_task,
    check_citations,
    check_parcel_condition,
    check_privileged,
    check_routing,
    check_slot_conflict,
    check_slot_source,
)
from paperweight.policy.task import OperatorTask
from paperweight.policy.verdict import Allow, Deny, Hold, Verdict
from paperweight.provenance.observation import Observation

RULES = (
    check_action_in_task,
    check_citations,
    check_privileged,
    check_routing,
    check_slot_source,
    check_slot_conflict,
    check_parcel_condition,
)


def judge_action(action: ProposedAction, task: OperatorTask, observations: list[Observation]) -> Verdict:
    # note: hold parks the parcel; no parameter can make it less safe than doing nothing
    if action.kind == "hold" and "hold" in task.allowed_actions:
        return Allow()
    hits = tuple(hit for rule in RULES for hit in rule(action, task, observations))
    denies = [h for h in hits if h.severity == "deny"]
    if denies:
        return Deny(rule=denies[0].rule, reason=denies[0].reason, hits=hits)
    if hits:
        return Hold(rule=hits[0].rule, reason=hits[0].reason, hits=hits)
    return Allow()
