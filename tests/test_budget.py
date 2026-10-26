from paperweight.token_factory.budget import CallBudget
from paperweight.token_factory.client import complete_json


def test_budget_refuses_after_limit(monkeypatch):
    monkeypatch.setenv("PAPERWEIGHT_MAX_LIVE_CALLS", "2")
    budget = CallBudget()
    assert budget.take_call().ok
    assert budget.take_call().ok
    assert not budget.take_call().ok


def test_spent_budget_never_reaches_the_network(monkeypatch, tmp_path):
    monkeypatch.setenv("PAPERWEIGHT_MODE", "live")
    monkeypatch.setenv("PAPERWEIGHT_MAX_LIVE_CALLS", "0")

    def fail_send(request):
        raise AssertionError("network call made with a spent budget")

    monkeypatch.setattr("paperweight.token_factory.client.send_request", fail_send)
    refused = complete_json("m", [{"role": "user", "content": "x"}], "s", {"type": "object"}, thinking=False)
    assert not refused.ok and "budget" in refused.error
