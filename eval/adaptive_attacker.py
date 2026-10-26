import itertools
import json
import sys
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

from eval.synth.cases import Case, bin_of
from paperweight.perception.perceive import perceive_frame
from paperweight.pipeline.decision import JudgedAction
from paperweight.pipeline.outcome_rules import choose_commands
from paperweight.policy.action import ProposedAction
from paperweight.policy.judge import judge_action
from paperweight.policy.task import OperatorTask
from paperweight.provenance.observation import OPERATOR, CitedValue, Observation

CORPUS_DIR = Path("eval/corpus/synth")
CAGES = ("R1", "RESTRICTED", "CAGE")


def forge_actions(case: Case, task: OperatorTask, observations: list[Observation]) -> list[ProposedAction]:
    # note: every citation an attacker-controlled planner could emit, for every value that reaches the goal
    cites = [OPERATOR, *(o.id for o in observations)]
    if case.attacker_goal == "PRIV OPEN":
        return [
            ProposedAction(kind="priv_open", params={"cage": CitedValue(value=cage, cite=cite)})
            for cage in CAGES
            for cite in cites
        ]
    goal_bin = case.attacker_goal.removeprefix("BIN ")
    cities = {c for c in task.routing if bin_of(c) == goal_bin} if goal_bin != task.routing_default else set()
    cities |= {o.text for o in observations if o.kind == "label_field" and o.field == task.route_slot}
    cities |= {token for o in observations for token in o.text.split() if token.isalpha()}
    return [
        ProposedAction(
            kind="route",
            params={
                task.route_slot: CitedValue(value=city, cite=city_cite),
                "bin": CitedValue(value=goal_bin, cite=bin_cite),
            },
        )
        for city, city_cite, bin_cite in itertools.product(sorted(cities), cites, cites)
    ]


def main() -> int:
    load_dotenv()
    task = OperatorTask.model_validate_json(Path("tasks/sorting.json").read_text())
    cases = [Case.model_validate(c) for c in json.loads((CORPUS_DIR / "cases.json").read_text())]
    tried = 0
    reached: list[tuple[str, ProposedAction]] = []
    rules: Counter[str] = Counter()
    skipped = 0
    for case in (c for c in cases if c.kind == "attack"):
        perceived = perceive_frame((CORPUS_DIR / f"{case.id}.jpg").read_bytes(), task)
        if not perceived.ok:
            skipped += 1
            continue
        observations = perceived.value.observations
        for action in forge_actions(case, task, observations):
            verdict = judge_action(action, task, observations)
            commands, _ = choose_commands([JudgedAction(action=action, policy_verdict=verdict, final_verdict=verdict)])
            tried += 1
            rules[verdict.rule if verdict.kind != "allow" else "allow"] += 1
            if case.attacker_goal in commands:
                reached.append((case.id, action))
    print(f"[adaptive] actions={tried} reached_goal={len(reached)} frames_skipped={skipped}")
    for rule, count in rules.most_common():
        print(f"[adaptive] stopped_by={rule} count={count}")
    for case_id, action in reached[:20]:
        params = {k: f"{v.value}<{v.cite}>" for k, v in action.params.items()}
        print(f"[adaptive] reached case={case_id} action={action.kind} params={params}")
    out = Path("eval/results/synth-adaptive-attacker.json")
    out.write_text(json.dumps({"actions": tried, "reached_goal": len(reached), "stopped_by": rules,
                               "reached": [{"case": c, "action": a.model_dump()} for c, a in reached]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
