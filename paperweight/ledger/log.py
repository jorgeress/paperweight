from pathlib import Path

from paperweight.pipeline.decision import Decision


def append_decision(path: Path, decision: Decision) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as ledger:
        ledger.write(decision.model_dump_json() + "\n")


def read_decisions(path: Path) -> list[Decision]:
    if not path.exists():
        return []
    return [Decision.model_validate_json(line) for line in path.read_text().splitlines() if line.strip()]
