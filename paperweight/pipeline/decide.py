import hashlib
from datetime import UTC, datetime

from paperweight.perception.perceive import perceive_frame
from paperweight.pipeline.decision import Decision, JudgedAction, StageCost
from paperweight.pipeline.outcome_rules import choose_commands
from paperweight.planner.plan import plan_actions
from paperweight.policy.escalate import escalate_verdict
from paperweight.policy.judge import judge_action
from paperweight.policy.task import Grant, OperatorTask
from paperweight.reasoning_check.review import review_reasoning
from paperweight.station.command import command_for
from paperweight.token_factory.client import Completion


def decide_parcel(
    frame_jpeg: bytes, task: OperatorTask, *, second_layer: bool = True, planner_preamble: str = ""
) -> Decision:
    now = datetime.now(UTC)
    base = {
        "id": now.strftime("%Y%m%dT%H%M%S%f"),
        "at": now.isoformat(timespec="milliseconds"),
        "frame_sha": hashlib.sha256(frame_jpeg).hexdigest(),
        "task": task,
    }
    stages: list[StageCost] = []

    perceived = perceive_frame(frame_jpeg, task)
    if not perceived.ok:
        return fail_closed(base, stages, perceived.error)
    observations = perceived.value.observations
    stages.append(cost_of("perception", perceived.value.completion))

    planned = plan_actions(task, observations, planner_preamble)
    if not planned.ok:
        return fail_closed(base | {"observations": observations}, stages, planned.error)
    plan = planned.value
    stages.append(cost_of("planner", plan.completion))

    review = None
    if second_layer:
        reviewed = review_reasoning(plan.completion.reasoning, observations)
        if reviewed.ok:
            review = reviewed.value.review
            stages.append(cost_of("reasoning-check", reviewed.value.completion))
        else:
            print(f"[reasoning-check] unavailable error={reviewed.error!r}")

    judged = []
    for action in plan.actions:
        verdict = judge_action(action, task, observations)
        final = escalate_verdict(verdict, review) if second_layer else verdict
        judged.append(JudgedAction(action=action, policy_verdict=verdict, final_verdict=final))
        print(f"[policy] {action.kind} verdict={final.kind} rule={getattr(final, 'rule', '-')}")

    commands, lcd = choose_commands(judged)
    return Decision(
        **base,
        observations=observations,
        judged=judged,
        reasoning=plan.completion.reasoning,
        review=review,
        commands=commands,
        lcd=lcd,
        consumed_grants=consumed_grants(judged, task, commands),
        stages=stages,
    )


def fail_closed(base: dict, stages: list[StageCost], error: str) -> Decision:
    # threat: a stage that errors or times out must not let anything through
    print(f"[pipeline] fail-closed error={error!r}")
    return Decision(**base, commands=["HOLD"], lcd="HOLD stage error", stages=stages, error=error)


def consumed_grants(judged: list[JudgedAction], task: OperatorTask, commands: list[str]) -> list[Grant]:
    used = []
    for j in judged:
        if j.final_verdict.kind != "allow" or j.action.kind not in task.privileged_actions:
            continue
        # note: a plan that ends in HOLD never sends the privileged command, so the grant must survive it
        if command_for(j.action, j.final_verdict) not in commands:
            continue
        wanted = {k: v.value for k, v in j.action.params.items()}
        used += [g for g in task.grants if g.kind == j.action.kind and g.params == wanted]
    return used


def cost_of(stage: str, completion: Completion) -> StageCost:
    return StageCost(stage=stage, **completion.model_dump(include={"model", "latency_ms", "tokens_in", "tokens_out", "replayed"}))
