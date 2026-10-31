"""Parse a small schedule format and run its tasks in waves.

Format, one task per line:

    name: seconds [after=dep1, dep2]

`seconds` is a positive integer (how long the task runs). `[after=...]` is an
optional comma-separated list of tasks that must finish first. Blank lines and
lines starting with '#' are ignored.
"""

import time
from concurrent.futures import ThreadPoolExecutor, wait


class SchedulerError(Exception):
    """Base class for every error this module raises."""


class ParseError(SchedulerError):
    def __init__(self, line_no, message):
        super().__init__(f"line {line_no}: {message}")
        self.line_no = line_no


class MissingDependency(SchedulerError):
    def __init__(self, task, dep):
        super().__init__(f"{task} depends on unknown task {dep}")
        self.task = task
        self.dep = dep


class CycleError(SchedulerError):
    def __init__(self, cycle):
        super().__init__("cycle: " + " -> ".join(cycle))
        self.cycle = cycle


class RunTimeout(SchedulerError):
    def __init__(self, pending):
        super().__init__("timed out; pending: " + ", ".join(pending))
        self.pending = pending


class Task:
    def __init__(self, name, seconds, deps=None):
        self.name = name
        self.seconds = seconds
        self.deps = deps or []

    def __repr__(self):
        return f"Task({self.name!r}, {self.seconds!r}, {self.deps!r})"


def parse_schedule(text):
    """Returns a dict of name -> Task, in the order tasks were defined."""
    tasks = {}
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ParseError(line_no, "expected 'name: seconds'")
        name, rest = line.split(":", 1)
        name = name.strip()
        if not name or not name.replace("-", "").replace("_", "").isalnum():
            raise ParseError(line_no, f"bad task name {name!r}")
        if name in tasks:
            raise ParseError(line_no, f"duplicate task {name}")
        deps = []
        if "[after=" in rest:
            rest, dep_text = rest.split("[after=", 1)
            if not dep_text.strip().endswith("]"):
                raise ParseError(line_no, "unclosed after list")
            deps = [d.strip() for d in dep_text.strip()[:-1].split(",") if d.strip()]
        seconds_text = rest.strip()
        try:
            seconds = int(seconds_text)
        except ValueError:
            raise ParseError(line_no, "seconds must be an integer")
        if seconds <= 0:
            raise ParseError(line_no, "seconds must be positive")
        tasks[name] = Task(name, seconds, deps)
    return tasks


def wave_plan(tasks):
    """Returns the task names grouped into sequential waves.

    A task appears in the first wave after all of its dependencies. Within a
    wave, names are sorted, so the plan is deterministic.
    """
    for t in tasks.values():
        for d in t.deps:
            if d not in tasks:
                raise MissingDependency(t.name, d)
    remaining = {name: set(t.deps) for name, t in tasks.items()}
    waves = []
    while remaining:
        ready = sorted(n for n, deps in remaining.items() if not deps)
        if not ready:
            raise CycleError(_find_cycle(tasks, remaining))
        waves.append(ready)
        for n in ready:
            del remaining[n]
            for deps in remaining.values():
                deps.discard(n)
    return waves


def execution_order(tasks):
    """Returns task names in a valid run order (waves flattened, sorted)."""
    order = []
    for wave in wave_plan(tasks):
        order.extend(wave)
    return order


def _find_cycle(tasks, remaining):
    start = min(remaining)
    path, seen = [], {}
    node = start
    while node not in seen:
        seen[node] = len(path)
        path.append(node)
        node = min(d for d in tasks[node].deps if d in remaining)
    return path[seen[node]:] + [node]


def run_all(tasks, runner, timeout=None):
    """Runs every task in wave order, each wave in parallel threads.

    `runner(name, seconds)` is called once per task and returns the task's
    result. Returns a dict of name -> result. If
    the whole run exceeds `timeout` seconds, remaining tasks are cancelled and
    a RunTimeout listing them by name is raised.
    """
    waves = wave_plan(tasks)
    results = {}
    deadline = None if timeout is None else time.monotonic() + timeout
    for wave in waves:
        with ThreadPoolExecutor(max_workers=len(wave)) as pool:
            futures = {
                pool.submit(runner, tasks[n].name, tasks[n].seconds): n
                for n in wave
            }
            budget = None if deadline is None else max(0.0, deadline - time.monotonic())
            done, not_done = wait(futures, timeout=budget)
            if not_done:
                pending = sorted(futures[f] for f in not_done)
                pool.shutdown(wait=False, cancel_futures=True)
                raise RunTimeout(pending)
            for future, name in futures.items():
                results[name] = future.result()
    return results