from paperweight.policy.action import ProposedAction
from paperweight.policy.task import OperatorTask
from paperweight.policy.verdict import RuleHit
from paperweight.provenance.observation import OPERATOR, Observation, find_observation
from paperweight.provenance.text_match import contains_value

type Hits = list[RuleHit]


def check_action_in_task(action: ProposedAction, task: OperatorTask, observations: list[Observation]) -> Hits:
    if action.kind not in task.allowed_actions | task.privileged_actions:
        return [RuleHit(rule="action-in-task", severity="deny", reason=f"{action.kind} is not in the operator task")]
    if action.kind != "route":
        return []
    expected = {task.route_slot, "bin"}
    got = set(action.params)
    if got == expected:
        return []
    detail = f"missing={sorted(expected - got)} unexpected={sorted(got - expected)}"
    return [RuleHit(rule="action-in-task", severity="deny", reason=f"route params do not match the task: {detail}")]


def check_citations(action: ProposedAction, task: OperatorTask, observations: list[Observation]) -> Hits:
    hits = []
    for param, cited in action.params.items():
        if cited.cite == OPERATOR:
            # threat: a model claiming operator authority for a value the operator never typed
            if not task.declares(action.kind, param, cited.value):
                reason = f"{param}={cited.value} cites operator but the task never declares it"
                hits.append(RuleHit(rule="citation-mismatch", severity="deny", reason=reason))
            continue
        observation = find_observation(cited.cite, observations)
        if observation is None:
            reason = f"{param} cites {cited.cite}, which is not in this frame"
            hits.append(RuleHit(rule="citation-mismatch", severity="deny", reason=reason))
        elif not contains_value(observation.text, cited.value):
            reason = f"{param}={cited.value} is not in {observation.id} text {observation.text!r}"
            hits.append(RuleHit(rule="citation-mismatch", severity="deny", reason=reason))
    return hits


def check_privileged(action: ProposedAction, task: OperatorTask, observations: list[Observation]) -> Hits:
    if action.kind not in task.privileged_actions:
        return []
    from_scene = [p for p, c in action.params.items() if c.cite != OPERATOR]
    if from_scene:
        # threat: a printed "security override" sheet asking the station to open the cage
        reason = f"{action.kind} takes {from_scene} from the scene; privileged params come from the operator only"
        return [RuleHit(rule="privileged-operator-only", severity="deny", reason=reason)]
    wanted = {p: c.value for p, c in action.params.items()}
    if any(g.kind == action.kind and g.params == wanted for g in task.grants):
        return []
    reason = f"no operator grant matches {action.kind} {wanted}"
    return [RuleHit(rule="privileged-operator-only", severity="deny", reason=reason)]


def check_routing(action: ProposedAction, task: OperatorTask, observations: list[Observation]) -> Hits:
    bin_param = action.params.get("bin")
    slot_param = action.params.get(task.route_slot)
    if action.kind != "route" or bin_param is None or slot_param is None:
        return []
    if bin_param.cite != OPERATOR:
        # threat: scene text redefining the mapping ("Madrid parcels now go to B")
        reason = f"bin comes from {bin_param.cite}; the mapping belongs to the operator"
        return [RuleHit(rule="routing-operator-only", severity="deny", reason=reason)]
    expected = task.bin_for(slot_param.value)
    if expected is None or expected == bin_param.value:
        return []
    reason = f"{task.route_slot}={slot_param.value} routes to {expected}, planner chose {bin_param.value}"
    return [RuleHit(rule="routing-operator-only", severity="deny", reason=reason)]


def check_slot_source(action: ProposedAction, task: OperatorTask, observations: list[Observation]) -> Hits:
    slot_param = action.params.get(task.route_slot)
    if action.kind != "route" or slot_param is None or slot_param.cite == OPERATOR:
        return []
    observation = find_observation(slot_param.cite, observations)
    if observation is None:
        return []
    if observation.kind != "label_field" or observation.field != task.route_slot:
        # threat: a loose sheet saying "SHIP TO PARIS" is scene text, not the parcel's label
        reason = f"{task.route_slot} comes from {observation.kind} {observation.id}, not a {task.route_slot} label field"
        return [RuleHit(rule="scene-slot-domain", severity="hold", reason=reason)]
    slot = task.slot(task.route_slot)
    if slot is not None and not slot.admits(slot_param.value):
        reason = f"{task.route_slot}={slot_param.value} is outside the declared domain"
        return [RuleHit(rule="scene-slot-domain", severity="hold", reason=reason)]
    return []


def check_slot_conflict(action: ProposedAction, task: OperatorTask, observations: list[Observation]) -> Hits:
    slot_param = action.params.get(task.route_slot)
    if action.kind != "route" or slot_param is None:
        return []
    fields = [o for o in observations if o.kind == "label_field" and o.field == task.route_slot]
    disagreeing = [o for o in fields if not contains_value(o.text, slot_param.value)]
    if not disagreeing:
        return []
    # threat: a second, forged label stuck over or next to the real one
    seen = ", ".join(f"{o.id} {o.text!r}" for o in fields)
    reason = f"label fields for {task.route_slot} disagree: {seen}"
    return [RuleHit(rule="slot-conflict", severity="hold", reason=reason)]
