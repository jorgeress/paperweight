from paperweight.pipeline.decision import JudgedAction
from paperweight.station.command import command_for, lcd_text


def choose_commands(judged: list[JudgedAction]) -> tuple[list[str], str]:
    # note: one denied action means the plan is compromised, so nothing else in it runs
    denied = [j for j in judged if j.final_verdict.kind == "deny"]
    if denied:
        return ["DENY"], lcd_text(denied[0].action, denied[0].final_verdict)
    held = [j for j in judged if j.final_verdict.kind == "hold"]
    if held:
        return ["HOLD"], lcd_text(held[0].action, held[0].final_verdict)
    routes = [j for j in judged if j.action.kind == "route"]
    if not judged or len(routes) > 1 or any(j.action.kind == "hold" for j in judged):
        return ["HOLD"], "HOLD" if judged else "HOLD empty plan"
    ordered = sorted(judged, key=lambda j: j.action.kind != "priv_open")
    commands = [command_for(j.action, j.final_verdict) for j in ordered]
    return commands, lcd_text(ordered[-1].action, ordered[-1].final_verdict)
