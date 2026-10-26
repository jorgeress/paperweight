import os
import threading

from paperweight.outcome import Err, Ok, Outcome

DEFAULT_MAX_LIVE_CALLS = 200


class CallBudget:
    # threat: a flapping sonar or a stuck loop firing paid calls until the credits run out
    def __init__(self) -> None:
        self.spent = 0
        self.lock = threading.Lock()

    def take_call(self) -> Outcome[int]:
        # note: read on every call because .env is loaded after this module is imported
        limit = int(os.environ.get("PAPERWEIGHT_MAX_LIVE_CALLS", DEFAULT_MAX_LIVE_CALLS))
        with self.lock:
            if self.spent >= limit:
                return Err(f"live call budget spent ({limit} calls this process), restart to reset")
            self.spent += 1
            return Ok(self.spent)


LIVE_BUDGET = CallBudget()
