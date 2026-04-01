from typing import Callable

LogFn = Callable[[str], None]
StopCheckFn = Callable[[], bool]


def fmt_elapsed(seconds: float) -> str:
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    m, s = divmod(s, 60)
    return f"{m}m {s}s"
