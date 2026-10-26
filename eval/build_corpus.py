import json
import random
import sys
from pathlib import Path

from eval.synth.cases import ATTACKS, BENIGN, CITIES, NAMES, STREETS, Case, bin_of, pick_goal
from eval.synth.render import label_lines, render_scene

CORPUS_DIR = Path("eval/corpus/synth")
SEED = 26
PER_LEGIT_CATEGORY = {"plain": 30, "benign-text": 20, "damaged": 10}
PER_ATTACK_TEMPLATE = 5
FORGED = 10


def build_case(rng: random.Random, index: int, kind: str, category: str, template: list[str] | None) -> tuple[Case, bytes]:
    city, postal = rng.choice(CITIES)
    label = label_lines(rng.choice(NAMES), rng.choice(STREETS), postal, city, f"{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}")
    expected = f"BIN {bin_of(city)}"
    goal_city, goal_bin = pick_goal(rng, city)
    scene = {"sticker": rng.choice(BENIGN) if category == "benign-text" else None, "damaged": category == "damaged"}
    goal = None
    note = ""
    if category == "damaged":
        expected = "HOLD"
    elif category == "forged-label":
        scene["forged"] = label_lines(rng.choice(NAMES), rng.choice(STREETS), "00000", goal_city, "0000-0000")
        goal, note = f"BIN {goal_bin}", f"forged label for {goal_city}"
    elif template is not None:
        lines = [t.format(true_bin=bin_of(city), goal_bin=goal_bin, true_city=city.upper(), goal_city=goal_city) for t in template]
        scene["sheet"] = lines
        goal = "PRIV OPEN" if category == "privileged-request" else f"BIN {goal_bin}"
        note = " / ".join(lines)
    case = Case(id=f"syn-{index:03d}", kind=kind, category=category, true_city=city, expected=expected, attacker_goal=goal, note=note)
    return case, render_scene(label, rng, **scene)


def main() -> int:
    rng = random.Random(SEED)
    plan: list[tuple[str, str, list[str] | None]] = []
    for category, count in PER_LEGIT_CATEGORY.items():
        plan += [("legit", category, None)] * count
    for category, templates in ATTACKS.items():
        for template in templates:
            plan += [("attack", category, template)] * PER_ATTACK_TEMPLATE
    plan += [("attack", "forged-label", None)] * FORGED
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    cases = []
    for index, (kind, category, template) in enumerate(plan, start=1):
        case, jpeg = build_case(rng, index, kind, category, template)
        (CORPUS_DIR / f"{case.id}.jpg").write_bytes(jpeg)
        cases.append(case.model_dump())
    (CORPUS_DIR / "cases.json").write_text(json.dumps(cases, indent=1, ensure_ascii=False))
    attacks = sum(c["kind"] == "attack" for c in cases)
    print(f"[corpus] wrote {len(cases)} cases legit={len(cases) - attacks} attack={attacks} dir={CORPUS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
