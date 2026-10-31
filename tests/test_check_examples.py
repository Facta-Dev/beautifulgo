#!/usr/bin/env python3
"""Tests for scripts/check-examples.py."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "check-examples.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_examples", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load %s" % SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


ce = load_checker()
GOFMT = ce._gofmt_exe()


def write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


README = """\
# Demo

```go
x := 1
y := x + 2
```

```bash
go test ./...
```

- A list item with an indented example:

  ```go
  z := y * 2
  ```

~~~markdown
```go
<a template placeholder, not real code>
```
~~~
"""


class RepoTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        write(self.root / "README.md", README)

    def tearDown(self):
        self._tmp.cleanup()

    def blocks(self):
        return ce.find_blocks(self.root, self.root / "README.md")

    def harness(self, data):
        write(self.root / "scripts" / "examples.json", json.dumps(data))


class FindBlocksTest(RepoTest):
    def test_finds_go_blocks_only(self):
        blocks = self.blocks()
        self.assertEqual([b.index for b in blocks], [1, 2])
        self.assertEqual(blocks[0].line, 4)
        self.assertIn("x := 1", blocks[0].code)

    def test_dedents_indented_blocks(self):
        self.assertEqual(self.blocks()[1].code, "z := y * 2")

    def test_ignores_go_fences_nested_in_other_blocks(self):
        codes = " ".join(b.code for b in self.blocks())
        self.assertNotIn("template placeholder", codes)

    def test_skips_eval_fixtures(self):
        write(self.root / "skills" / "demo" / "SKILL.md", "```go\nfn a() {}\n```\n")
        write(self.root / "skills" / "demo" / "evals" / "case" / "prompt.md",
              "```go\nbroken\n```\n")
        names = [p.relative_to(self.root).as_posix() for p in ce.doc_files(self.root)]
        self.assertIn("skills/demo/SKILL.md", names)
        self.assertNotIn("skills/demo/evals/case/prompt.md", names)

    def test_fence_tags_carry_domain_flag(self):
        write(self.root / "README.md",
              "```go domain\npackage domain\n```\n")
        blocks = self.blocks()
        self.assertEqual([b.is_domain for b in blocks], [True])


class WrapTest(RepoTest):
    def auto_blocks(self):
        self.harness({"files": {}})
        blocks = self.blocks()
        ce.apply_harness(self.root, blocks, {})
        return blocks

    def test_statement_fragments_get_the_statement_variant(self):
        block = self.auto_blocks()[0]
        suffixes = [s for s, _t in ce.variants_of(block)]
        self.assertEqual(suffixes, ["-decl", "-stmt"])

    def test_package_blocks_stay_unwrapped(self):
        write(self.root / "README.md", "```go\npackage demo\n\nvar A = 1\n```\n")
        for block in self.auto_blocks():
            self.assertEqual(ce.variants_of(block), [("", block.template)])


class DomainTest(RepoTest):
    def test_domain_comment_flag(self):
        block = ce.Block(path="x.md", line=1, index=1, code='// domain.go holds rules\n')
        self.assertTrue(ce.looks_like_domain(block.code))

    def test_forbidden_imports(self):
        for path in ("net/http", "net/http/httptest", "database/sql",
                     "github.com/jackc/pgx/v5", "github.com/jackc/pgx/v5/pgxpool",
                     "example.com/app/internal/platform/httpx",
                     "example.com/app/internal/gen/db",
                     "example.com/app/internal/features/other"):
            self.assertTrue(ce.is_forbidden_domain_import(path), path)
        for path in ("fmt", "errors", "context", "time", "log/slog",
                     "example.com/app/internal/shared/apperr", "encoding/json"):
            self.assertFalse(ce.is_forbidden_domain_import(path), path)

    def test_imports_of(self):
        code = 'import (\n\t"net/http"\n\t// fmt\n)\n\nimport "errors"\n'
        self.assertEqual(ce.imports_of(code),
                         [(1, "net/http"), (5, "errors")])


class HarnessTest(RepoTest):
    def apply(self, data):
        blocks = self.blocks()
        problems = ce.apply_harness(self.root, blocks, data)
        return blocks, problems

    def test_template_and_prelude_are_attached(self):
        blocks, problems = self.apply({"files": {"README.md": {
            "prelude": "package p",
            "blocks": {"2": {"first_line": "z := y * 2",
                             "template": ["func w() {", "{code}", "}"]}},
        }}})
        self.assertEqual(problems, [])
        self.assertEqual(blocks[0].prelude, "package p")
        self.assertEqual(ce.variants_of(blocks[1]), [("", "func w() {\n{code}\n}")])

    def test_first_line_mismatch_reports_drift_at_the_block(self):
        blocks, problems = self.apply({"files": {"README.md": {
            "blocks": {"2": {"first_line": "let z = 3;", "template": "{code}"}},
        }}})
        self.assertEqual(len(problems), 1)
        self.assertEqual((problems[0].path, problems[0].line), ("README.md", 15))
        self.assertIn("update the harness", problems[0].message)
        self.assertIsNotNone(blocks[1].skip)

    def test_skip_needs_a_reason(self):
        blocks, problems = self.apply({"files": {"README.md": {
            "blocks": {"2": {"first_line": "z := y * 2", "skip": ""}},
        }}})
        self.assertEqual(len(problems), 1)
        self.assertIn("skip needs a reason", problems[0].message)

    def test_skip_with_reason_is_not_an_error(self):
        blocks, problems = self.apply({"files": {"README.md": {
            "blocks": {"2": {"first_line": "z := y * 2", "skip": "a fragment"}},
        }}})
        self.assertEqual(problems, [])
        self.assertEqual(blocks[1].skip, "a fragment")

    def test_unknown_block_and_file_are_errors(self):
        _, problems = self.apply({"files": {
            "README.md": {"blocks": {"9": {"first_line": "x"}}},
            "missing.md": {"blocks": {}},
        }})
        messages = " ".join(p.message for p in problems)
        self.assertIn("no go block #9", messages)
        self.assertIn("missing.md", messages)

    def test_template_without_code_slot_is_an_error(self):
        _, problems = self.apply({"files": {"README.md": {
            "blocks": {"1": {"first_line": "x := 1",
                             "template": "fn f() {}"}},
        }}})
        self.assertIn("has no {code}", problems[0].message)


class CheckRepoTest(RepoTest):
    def setUp(self):
        super().setUp()
        self._previous_exe = ce._gofmt_exe

    def tearDown(self):
        ce._gofmt_exe = self._previous_exe
        super().tearDown()

    def use(self, exe):
        ce._gofmt_exe = lambda: exe

    def test_fallback_reports_unbalanced_block(self):
        write(self.root / "README.md", "# Demo\n\n```go\nfunc broken( {}\n```\n")
        self.use(None)
        problems, checked, wrapped, skipped, mode = ce.check_repo(self.root)
        self.assertEqual(checked, 1)
        self.assertTrue(problems, "no balance problem reported")
        self.assertIn("sanity pass", mode)

    def test_fallback_passes_clean_fragments(self):
        self.use(None)
        problems, checked, _wrapped, skipped, mode = ce.check_repo(self.root)
        self.assertEqual(problems, [])
        self.assertEqual((checked, skipped), (2, 0))
        self.assertIn("sanity pass", mode)

    def test_domain_snippet_imports_are_denied(self):
        write(self.root / "README.md",
              "```go\n// domain.go holds the rules.\npackage domain\n\n"
              'import "net/http"\n```\n')
        self.use(None)
        problems, _checked, _wrapped, _skipped, _mode = ce.check_repo(self.root)
        self.assertTrue(any("domain-pure" in p.message for p in problems))

    def test_adapter_snippet_may_import_http(self):
        write(self.root / "README.md",
              "```go\n// http.go is the edge.\npackage httpx\n\n"
              'import "net/http"\n```\n')
        self.use(None)
        problems, _checked, _wrapped, _skipped, _mode = ce.check_repo(self.root)
        self.assertEqual(problems, [])

    def test_skip_exempts_domain_and_syntax(self):
        write(self.root / "README.md",
              "```go\n// domain.go shows the wrong import.\npackage domain\n\n"
              'import "net/http"\n```\n')
        self.harness({"files": {"README.md": {"blocks": {"1": {
            "first_line": "// domain.go shows the wrong import.",
            "skip": "counterexample"}}}}})
        self.use(None)
        problems, _checked, _wrapped, skipped, _mode = ce.check_repo(self.root)
        self.assertEqual(problems, [])
        self.assertEqual(skipped, 1)



@unittest.skipUnless(GOFMT, "gofmt is not installed")
class GofmtModeTest(RepoTest):
    def setUp(self):
        super().setUp()
        self._previous = ce._gofmt_exe
        ce._gofmt_exe = lambda: GOFMT

    def tearDown(self):
        ce._gofmt_exe = self._previous
        super().tearDown()

    def test_gofmt_errors_map_to_the_markdown_line(self):
        write(self.root / "README.md", "# Demo\n\n```go\nfunc broken( {}\n```\n")
        problems, checked, _wrapped, _skipped, mode = ce.check_repo(self.root)
        self.assertEqual(checked, 1)
        self.assertEqual(mode, "gofmt -e")
        self.assertTrue(problems)
        self.assertEqual(problems[0].path, "README.md")
        self.assertEqual(problems[0].line, 4)

    def test_wrapped_fragment_parses(self):
        problems, checked, wrapped, _skipped, _mode = ce.check_repo(self.root)
        self.assertEqual((problems, checked, wrapped), ([], 2, 2))

    def test_declaration_snippet_parses_in_its_variant(self):
        write(self.root / "README.md",
              "```go\ntype Limiter interface {\n\tAllow() bool\n}\n```\n")
        problems, checked, _wrapped, _skipped, _mode = ce.check_repo(self.root)
        self.assertEqual(problems, [], [p.message for p in problems])

    def test_require_toolchain_exit_code_2(self):
        write(self.root / "README.md", "# Demo\n\n```go\nx := 1\n```\n")
        ce._gofmt_exe = lambda: None
        rc = ce.main(["--require-toolchain", str(self.root)])
        self.assertEqual(rc, 2)


class RealRepoTest(unittest.TestCase):
    def test_real_repo_passes(self):
        problems, checked, _wrapped, skipped, _mode = ce.check_repo(REPO_ROOT)
        self.assertEqual(problems, [], [ce.format_problem(p) for p in problems])
        self.assertGreater(checked, 0)
        self.assertGreater(skipped, 0)
        self.assertGreater(skipped, checked * 0 or 1)


if __name__ == "__main__":
    unittest.main()