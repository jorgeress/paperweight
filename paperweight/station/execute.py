from paperweight.outcome import Err, Ok, Outcome
from paperweight.pipeline.decision import Decision
from paperweight.station.link import ALLOWED_COMMANDS, StationLink


def execute_decision(decision: Decision, link: StationLink) -> Outcome[list[str]]:
    # threat: this is the only path to the actuator, and it only accepts a judged decision
    unknown = [c for c in decision.commands if c not in ALLOWED_COMMANDS]
    if unknown:
        return Err(f"refusing unknown station commands {unknown}")
    replies = []
    for command in decision.commands:
        sent = link.write_line(command)
        if not sent.ok:
            return sent
        replies.append(sent.value)
    if decision.lcd:
        link.write_line(f"LCD {decision.lcd}")
    return Ok(replies)
