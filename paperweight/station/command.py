from paperweight.policy.action import ProposedAction
from paperweight.policy.verdict import Verdict


def command_for(action: ProposedAction, verdict: Verdict) -> str:
    if verdict.kind == "deny":
        return "DENY"
    if verdict.kind == "hold" or action.kind == "hold":
        return "HOLD"
    if action.kind == "route":
        return f"BIN {action.params['bin'].value}"
    return "PRIV OPEN"


def lcd_text(action: ProposedAction, verdict: Verdict) -> str:
    if verdict.kind == "allow":
        target = action.params["bin"].value if action.kind == "route" else action.kind
        return f"ALLOW {target}"[:32]
    return f"{verdict.kind.upper()} {verdict.rule}"[:32]
