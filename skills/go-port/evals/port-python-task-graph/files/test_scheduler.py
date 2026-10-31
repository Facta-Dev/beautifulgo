import threading
import time
import unittest

from scheduler import (
    CycleError,
    MissingDependency,
    ParseError,
    RunTimeout,
    SchedulerError,
    Task,
    execution_order,
    parse_schedule,
    run_all,
    wave_plan,
)

SAMPLE = """
# a small deploy schedule
compile: 2
lint: 1
unit: 3 [after=compile]
docs: 2
ship: 1 [after=unit, lint, docs]
"""


def _runner(records, lock):
    def runner(name, seconds):
        with lock:
            records.append((name, seconds))
        time.sleep(min(seconds, 0.05))
        return "ran " + name
    return runner


def _slow_runner():
    def runner(name, seconds):
        time.sleep(0.2)
        return "ran " + name
    return runner


class ParseTests(unittest.TestCase):
    def test_parses_fields(self):
        tasks = parse_schedule(SAMPLE)
        self.assertEqual(list(tasks), ["compile", "lint", "unit", "docs", "ship"])
        self.assertEqual(tasks["unit"].seconds, 3)
        self.assertEqual(tasks["unit"].deps, ["compile"])
        self.assertEqual(tasks["ship"].deps, ["unit", "lint", "docs"])

    def test_parse_errors_report_line(self):
        cases = {
            "a: 1\nnope": 2,
            "a: compile": 1,
            "a: 1\na: 2": 2,
            "a b: 1": 1,
            "a: 1 [after=x": 1,
            "a: -3": 1,
        }
        for text, line in cases.items():
            with self.subTest(text=text):
                with self.assertRaises(ParseError) as cm:
                    parse_schedule(text)
                self.assertEqual(cm.exception.line_no, line)

    def test_errors_share_a_base_class(self):
        self.assertTrue(issubclass(ParseError, SchedulerError))
        self.assertTrue(issubclass(CycleError, SchedulerError))
        self.assertTrue(issubclass(MissingDependency, SchedulerError))
        self.assertTrue(issubclass(RunTimeout, SchedulerError))


class OrderTests(unittest.TestCase):
    def test_order_respects_deps(self):
        self.assertEqual(
            execution_order(parse_schedule(SAMPLE)),
            ["compile", "docs", "lint", "unit", "ship"],
        )

    def test_missing_dependency(self):
        with self.assertRaises(MissingDependency) as cm:
            execution_order(parse_schedule("a: 1 [after=ghost]"))
        self.assertEqual((cm.exception.task, cm.exception.dep), ("a", "ghost"))

    def test_cycle_is_named(self):
        text = "a: 1 [after=c]\nb: 1 [after=a]\nc: 1 [after=b]\nd: 2"
        with self.assertRaises(CycleError) as cm:
            execution_order(parse_schedule(text))
        self.assertEqual(cm.exception.cycle, ["a", "c", "b", "a"])

    def test_empty(self):
        self.assertEqual(execution_order(parse_schedule("")), [])


class WaveTests(unittest.TestCase):
    def test_waves_group_and_sort_names(self):
        self.assertEqual(
            wave_plan(parse_schedule(SAMPLE)),
            [["compile", "docs", "lint"], ["unit"], ["ship"]],
        )


class RunTests(unittest.TestCase):
    def test_run_all_runs_every_task_once(self):
        tasks = parse_schedule(SAMPLE)
        records = []
        lock = threading.Lock()
        results = run_all(tasks, _runner(records, lock))
        self.assertEqual(sorted(results), sorted(tasks))
        self.assertEqual(len(records), len(tasks))
        self.assertEqual(results["ship"], "ran ship")

    def test_run_all_timeout_lists_pending(self):
        tasks = parse_schedule(SAMPLE)
        with self.assertRaises(RunTimeout) as cm:
            run_all(tasks, _slow_runner(), timeout=0.05)
        self.assertEqual(cm.exception.pending, ["compile", "docs", "lint"])

    def test_run_all_empty(self):
        self.assertEqual(run_all(parse_schedule(""), _runner([], threading.Lock())), {})


if __name__ == "__main__":
    unittest.main()
