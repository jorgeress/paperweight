from dataclasses import dataclass


@dataclass(frozen=True)
class Ok[T]:
    value: T
    ok: bool = True


@dataclass(frozen=True)
class Err:
    error: str
    ok: bool = False


type Outcome[T] = Ok[T] | Err
