import sys
from pathlib import Path

from dotenv import load_dotenv

from paperweight.pipeline.decide import decide_parcel
from paperweight.policy.task import OperatorTask


def main() -> int:
    load_dotenv()
    frame = Path(sys.argv[1]).read_bytes()
    task = OperatorTask.model_validate_json(Path("tasks/sorting.json").read_text())
    decision = decide_parcel(frame, task)
    for o in decision.observations:
        print(f"  {o.id} {o.kind:<11} {o.field or '':<16} {o.text!r}")
    for j in decision.judged:
        params = {k: f"{v.value}<{v.cite}>" for k, v in j.action.params.items()}
        print(f"  action {j.action.kind} {params} -> {j.final_verdict.model_dump(exclude={'hits'})}")
    print(f"  review={decision.review} commands={decision.commands} lcd={decision.lcd!r} error={decision.error}")
    for s in decision.stages:
        print(f"  stage {s.stage} {s.latency_ms}ms in={s.tokens_in} out={s.tokens_out} replayed={s.replayed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
