import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv

from eval.configs import CONFIGS, Run
from eval.metrics import render_table, summarize
from eval.synth.cases import Case
from paperweight.policy.task import OperatorTask

RESULTS_DIR = Path("eval/results")


def run_config(name: str, cases: list[Case], corpus: Path, task: OperatorTask, workers: int) -> list[Run]:
    config = CONFIGS[name]

    def run_case(case: Case) -> Run:
        run = config((corpus / f"{case.id}.jpg").read_bytes(), task)
        print(f"[eval] config={name} case={case.id} kind={case.kind} got={run.commands} expected={case.expected} goal={case.attacker_goal}")
        return run

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(run_case, cases))


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="eval/corpus/synth")
    parser.add_argument("--configs", default=",".join(CONFIGS))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    corpus = Path(args.corpus)
    cases = [Case.model_validate(c) for c in json.loads((corpus / "cases.json").read_text())]
    if args.limit:
        cases = cases[: args.limit // 2] + [c for c in cases if c.kind == "attack"][: args.limit - args.limit // 2]
    task = OperatorTask.model_validate_json(Path("tasks/sorting.json").read_text())
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    summaries = {}
    for name in args.configs.split(","):
        runs = run_config(name, cases, corpus, task, args.workers)
        rows = [{"case": c.model_dump(), "run": r.model_dump()} for c, r in zip(cases, runs, strict=True)]
        (RESULTS_DIR / f"{corpus.name}-{name}.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
        summaries[name] = summarize(cases, runs)
    table = render_table(summaries)
    (RESULTS_DIR / f"{corpus.name}-table.md").write_text(table + "\n")
    print(table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
