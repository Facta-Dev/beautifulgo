#!/usr/bin/env python3
"""Check every Go fenced block in the skills and docs is syntactically valid Go.

Most examples are fragments: a few statements, a method without its receiver,
a type that refers to another type elsewhere. scripts/examples.json gives each
fragment the context it needs (a per-file prelude and a per-block template) or
a reason to skip it with. Blocks keyed by (file, order, first non-blank line);
a first-line mismatch between a doc and examples.json is an error, so edits
fail the check until the harness is updated: examples never rot silently.

The blocks are syntax-checked, not compiled, in two modes:

- gofmt on PATH: each block is assembled (prelude + template + block) into its
  own file in one temp directory and parsed with `gofmt -e`; errors report at
  the markdown line. This is the authoritative mode; CI runs it.
- gofmt missing: a pure-Python sanity pass over the same assembled text --
  brace/bracket/paren parity outside strings, comments, and raw strings, plus
  stray-fence detection. Weaker than gofmt but never silent.

Blocks never silently skip: a skip needs an entry in examples.json with a
reason, and skipped blocks are counted and listed in the summary. Skipped
blocks are also exempt from the domain check, because a deliberate
counterexample violates it by design.

Exemption to know about: find_blocks only sees top-level ```go fences. A ```go
fence nested inside another fence — today the ~~~markdown report template in
skills/go-review/SKILL.md, whose ```go block holds a template placeholder — is
intentionally not a block, is not checked, and is not counted. Keep any real
Go example out of nested fences, or extend this script.

Domain snippets keep the architecture law: a ```go domain fence, a block whose
first comment names domain.go, or a `package domain` clause must not import
net/http, database/sql, pgx, chi, internal/gen, internal/platform, or sibling
slices -- the domain-pure rule from lints/.golangci.yml, enforced in the docs.

Fragments with no harness entry are auto-wrapped as `package p` / `func _()` /
{...} when the block has no package clause and no top-level import/func/type
line, which keeps ordinary statement snippets out of the harness. Anything
else without an entry is checked as a file and fails like one, so the harness
stays the single place context is declared.

Stdlib only, Python 3.9+. Exit 0 clean, 1 on any error, 2 if the Go toolchain
is missing and --require-toolchain is set.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

HARNESS = Path("scripts") / "examples.json"
DOC_GLOBS = (
    "README.md",
    "CONTRIBUTING.md",
    "examples/*.md",
    "skills/*/SKILL.md",
    "skills/*/references/*.md",
)
FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*(.*)$")
CODE = "{code}"

DOMAIN_FORBIDDEN_PREFIXES = ("net/http", "database/sql", "github.com/jackc/pgx/", "github.com/go-chi/chi/")
DOMAIN_FORBIDDEN_PARTS = ("/internal/gen", "/internal/platform", "/internal/features")
DOMAIN_COMMENT_RE = re.compile(r"^\s*//\s*.*\bdomain\.go\b")
PACKAGE_RE = re.compile(r"^\s*package\s+[A-Za-z_]\w*\s*$", re.M)
PACKAGE_DOMAIN_RE = re.compile(r"^\s*package\s+domain\s*$", re.M)
TOP_LEVEL_RE = re.compile(r"^(import|func|type)\b", re.M)
SINGLE_IMPORT_RE = re.compile(r'''^\s*import\s+"([^"]+)"''')
IMPORT_BLOCK_RE = re.compile(r"^\s*import\s*\(\s*$")
IMPORT_PATH_RE = re.compile(r'"([^"]+)"')
WRAP_TEMPLATE = "package p\n\nfunc _() {\n" + CODE + "\n}"


@dataclass(frozen=True)
class Problem:
    path: str
    line: int
    level: str
    message: str


@dataclass
class Block:
    path: str
    line: int  # markdown line of the first code line
    index: int  # 1-based position among the file's go blocks
    code: str
    is_domain: bool = False
    skip = None
    prelude = ""
    template = "{code}"
    wrapped = False
    lines = None
    variants = None


def rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def format_problem(problem: Problem) -> str:
    prefix = "warning: " if problem.level == "warning" else ""
    return "%s:%d: %s%s" % (problem.path, problem.line, prefix, problem.message)


def summary_line(problems: Sequence[Problem], checked: int, wrapped: int, skipped: int, mode: str) -> str:
    errors = sum(1 for p in problems if p.level == "error")
    err_word = "error" if errors == 1 else "errors"
    return "%d %s, %d blocks checked (%d wrapped, %d skipped), %s" % (
        errors, err_word, checked, wrapped, skipped, mode)


def doc_files(root: Path) -> List[Path]:
    found = set()
    for pattern in DOC_GLOBS:
        for path in root.glob(pattern):
            if path.is_file() and "evals" not in path.parts:
                found.add(path)
    return sorted(found)


def find_blocks(root: Path, path: Path) -> List[Block]:
    """Return the ```go blocks in one markdown file."""
    blocks: List[Block] = []
    lines = path.read_text(encoding="utf-8").split("\n")
    fence: Optional[str] = None
    is_go = False
    is_domain = False
    start = 0
    body: List[str] = []
    for number, text in enumerate(lines, 1):
        match = FENCE_RE.match(text)
        if fence is None:
            if match:
                fence = match.group(2)
                info = (match.group(3) or "").strip()
                tokens = info.split()
                lang = tokens[0].split(",")[0] if tokens else ""
                is_go = lang == "go"
                is_domain = "domain" in (tokens[1:] or [])
                start = number + 1
                body = []
            continue
        if match and match.group(2).startswith(fence[0]) and len(match.group(2)) >= len(fence) and not (match.group(3) or "").strip():
            if is_go and body:
                blocks.append(
                    Block(
                        path=rel(root, path),
                        line=start,
                        index=len(blocks) + 1,
                        code=textwrap.dedent("\n".join(body)),
                        is_domain=is_domain,
                    )
                )
                is_domain = False
            fence = None
            continue
        body.append(text)
    return blocks


def as_text(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    return str(value or "")


def first_code_line(code: str) -> str:
    for text in code.split("\n"):
        if text.strip():
            return text.strip()
    return ""


def looks_like_domain(code: str) -> bool:
    """A snippet that presents itself as a domain file."""
    if any(PACKAGE_DOMAIN_RE.match(line) for line in code.split("\n")):
        return True
    for line in code.split("\n"):
        if line.strip():
            return bool(DOMAIN_COMMENT_RE.match(line))
    return False


def imports_of(code: str) -> List[Tuple[int, str]]:
    """(offset within code, import path) pairs for a snippet's imports."""
    out: List[Tuple[int, str]] = []
    in_block = False
    for offset, line in enumerate(code.split("\n")):
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        single = SINGLE_IMPORT_RE.match(line)
        if single:
            out.append((offset, single.group(1)))
            continue
        if IMPORT_BLOCK_RE.match(line):
            in_block = True
            continue
        if in_block:
            if stripped == ")":
                in_block = False
            else:
                paths = IMPORT_PATH_RE.findall(line)
                if paths:
                    out.append((offset, paths[-1]))
    return out
def apply_harness(root, blocks, harness):
    """Attach preludes, templates, and skips. Report harness drift."""
    problems = []
    files = harness.get("files", {})
    by_path = {}
    for block in blocks:
        by_path.setdefault(block.path, []).append(block)
    harness_path = HARNESS.as_posix()
    referenced = set()
    for path, entry in files.items():
        if path not in by_path:
            problems.append(Problem(HARNESS.as_posix(), 1, "error",
                "%s: file has no go blocks or does not exist" % path))
            continue
        for key, spec in (entry.get("blocks") or {}).items():
            try:
                index = int(key)
            except ValueError:
                problems.append(Problem(HARNESS.as_posix(), 1, "error",
                    "%s: block key %r is not a number" % (path, key)))
                continue
            if index < 1 or index > len(by_path[path]):
                problems.append(Problem(HARNESS.as_posix(), 1, "error",
                    "%s: no go block #%d (file has %d)" % (path, index, len(by_path[path]))))
                continue
            block = by_path[path][index - 1]
            referenced.add(id(block))
            expected = (spec.get("first_line") or "").strip()
            actual = first_code_line(block.code)
            if expected != actual:
                problems.append(Problem(block.path, block.line, "error",
                    "go block #%d does not match %s (expected first line %r, found %r); "
                    "update the harness" % (index, HARNESS.as_posix(), expected, actual)))
                block.skip = "harness out of date"
                continue
            if "skip" in spec:
                reason = str(spec.get("skip") or "").strip()
                if not reason:
                    problems.append(Problem(block.path, block.line, "error", "skip needs a reason"))
                block.skip = reason or "no reason"
                continue
            template = as_text(spec.get("template")) or CODE
            if CODE not in template:
                problems.append(Problem(HARNESS.as_posix(), 1, "error",
                    "%s block #%d: template has no {code}" % (path, index)))
                template = CODE
            block.template = template
        prelude = as_text(entry.get("prelude"))
        for block in by_path[path]:
            block.prelude = prelude
    for block in blocks:
        if id(block) in referenced or block.skip is not None:
            continue
        if PACKAGE_RE.search(block.code):
            continue
        block.variants = [
            ("-decl", "package p\n" + CODE),
            ("-stmt", "package p\n\nfunc _() {\n" + CODE + "\n}"),
        ]
        block.wrapped = True
    return problems


def render(block, label, template):
    out = []
    origin = []

    def add(text, where):
        for piece in text.split("\n"):
            out.append(piece)
            origin.append(where)

    if block.prelude:
        add(block.prelude, (HARNESS.as_posix(), 1))
    before, _, after = template.partition(CODE)
    if before:
        add(before.rstrip("\n"), (HARNESS.as_posix(), 1))
    for offset, piece in enumerate(block.code.split("\n")):
        out.append(piece)
        origin.append((block.path, block.line + offset))
    if after:
        add(after.lstrip("\n"), (HARNESS.as_posix(), 1))
    lines = {n: w for n, w in enumerate(origin, 1)}
    return "\n".join(out) + "\n", lines
CODE_TOKEN_RE = re.compile(
    r"//[^\n]*"
    r"|/\*.*?\*/"
    r'|"(?:[^"\\\n]|\\.)*"'
    r"|`[^`]*`"
    r"|'[^'\n]*'"
    r"|([({[])"
    r"|([)}\]])",
    re.S,
)
PARENS = {")": "(", "]": "[", "}": "{"}


def balance_problems(text):
    """Pure-Python sanity pass: [(line, message)] for unbalanced Go-ish text."""
    problems = []
    stack = []
    line = 1
    pos = 0
    for match in CODE_TOKEN_RE.finditer(text):
        start, end = match.span()
        line += text.count("\n", pos, start)
        pos = end
        opener = match.group(1)
        closer = match.group(2)
        if opener:
            stack.append((opener, line))
        elif closer:
            if stack and PARENS[closer] == stack[-1][0]:
                stack.pop()
            else:
                problems.append((line, "unbalanced %s" % closer))
        line += text.count("\n", start, end)
    line += text.count("\n", pos, len(text))
    if stack:
        problems.append((line, "unclosed %s (opened at line %d)" % (stack[-1][0], stack[-1][1])))
    for n, text_line in enumerate(text.split("\n"), 1):
        s = text_line.lstrip()
        if s.startswith("```") or s.startswith("~~~"):
            problems.append((n, "stray fence line"))
    return problems


def run_gofmt(directory: Path, exe: str) -> List[Tuple[str, int, str]]:
    """gofmt -e over one directory; [(file, line, message)] from stderr."""
    result = subprocess.run(
        [exe, "-e", directory.name],
        cwd=str(directory.parent),
        capture_output=True,
        text=True,
        env=None,
    )
    found = []
    for raw in result.stderr.splitlines():
        m = re.match(r"^(.*\.go):(\d+):(\d+): (.*)$", raw)
        if m:
            found.append((Path(m.group(1)).name, int(m.group(2)), m.group(4)))
    return found
def variants_of(block):
    """[(suffix, template)] for one block: harness form or the canned pair."""
    if block.variants is None:
        return [("", block.template)]
    return block.variants


def check_repo(root):
    """Return (problems, checked, wrapped, skipped, mode)."""
    root = Path(root)
    harness, problems = load_harness(root)
    blocks = []
    for path in doc_files(root):
        blocks.extend(find_blocks(root, path))
    for block in blocks:
        if not block.is_domain and looks_like_domain(block.code):
            block.is_domain = True
    problems.extend(apply_harness(root, blocks, harness))
    to_check = [b for b in blocks if b.skip is None]
    skipped = len(blocks) - len(to_check)
    for block in to_check:
        if not block.is_domain:
            continue
        for offset, imported in imports_of(block.code):
            if is_forbidden_domain_import(imported):
                problems.append(Problem(block.path, block.line + offset, "error",
                    "domain snippet imports %s, denied by the domain-pure rule "
                    "(lints/.golangci.yml)" % imported))
                break
    if not to_check:
        return problems, 0, 0, skipped, "no go blocks found"
    exe = _gofmt_exe()
    mode = "pure-Python sanity pass (gofmt not on PATH)" if exe is None else "gofmt -e"
    rendered = []
    for number, block in enumerate(to_check, 1):
        for suffix, template in variants_of(block):
            name = "ex_%03d%s.go" % (number, suffix)
            text, lines = render(block, HARNESS.as_posix(), template)
            rendered.append((block, name, text, lines))
    errs_by_file = {}
    if exe is None:
        for block, name, text, lines in rendered:
            errs_by_file[name] = balance_problems(text)
    else:
        with tempfile.TemporaryDirectory(prefix="examples-check.") as tmp:
            blocks_dir = Path(tmp) / "blocks"
            blocks_dir.mkdir()
            for block, name, text, lines in rendered:
                (blocks_dir / name).write_text(text, encoding="utf-8")
            for file_name, line_no, msg in run_gofmt(blocks_dir, exe):
                errs_by_file.setdefault(file_name, []).append((line_no, msg))
    per_block = {}
    for block, name, text, lines in rendered:
        errs = errs_by_file.get(name, [])
        per_block.setdefault(id(block), (block, []))[1].append((name, errs))
    for _key, (block, attempts) in per_block.items():
        clean = [name for name, errs in attempts if not errs]
        if clean:
            continue
        name, errs = min(attempts, key=lambda a: len(a[1]))
        lines = next(lines for b, n, _t, lines in rendered if n == name)
        for line_no, msg in errs:
            where = lines.get(line_no, (block.path, block.line))
            note = "" if where[0] == block.path else " (in the harness code for this block)"
            problems.append(Problem(where[0], where[1], "error", msg + note))
    wrapped = sum(1 for b in to_check if b.wrapped)
    return problems, len(to_check), wrapped, skipped, mode


def load_harness(root):
    path = root / HARNESS
    if not path.exists():
        return {}, []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return {}, [Problem(HARNESS.as_posix(), 1, "error", "invalid JSON: %s" % exc)]
    if not isinstance(data, dict):
        return {}, [Problem(HARNESS.as_posix(), 1, "format error: top level must be an object")]
    return data, []


def is_forbidden_domain_import(imported):
    return (
        imported.startswith(DOMAIN_FORBIDDEN_PREFIXES)
        or any(part in imported for part in DOMAIN_FORBIDDEN_PARTS)
    )


def _gofmt_exe():
    return shutil.which("gofmt")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Check that every Go block in the skills and docs is valid Go.")
    parser.add_argument("root", nargs="?", default=".",
        help="repository root (default: current directory)")
    parser.add_argument("--json", dest="as_json", action="store_true",
        help="print findings as JSON")
    parser.add_argument("--require-toolchain", dest="require_toolchain", action="store_true",
        help="exit 2 instead of the fallback when gofmt is missing")
    args = parser.parse_args(argv)
    root = Path(args.root)
    if not root.exists():
        payload = {
            "ok": False, "error_count": 1, "checked": 0, "wrapped": 0, "skipped": 0,
            "mode": "root missing", "summary": "1 error, nothing checked",
            "problems": [{"path": args.root, "line": 1, "level": "error",
                "message": "path does not exist"}]}
        if args.as_json:
            json.dump(payload, sys.stdout, indent=2)
            sys.stdout.write("\n")
        else:
            sys.stdout.write("%s:1: path does not exist\n1 error, nothing checked\n" % args.root)
        return 1
    problems, checked, wrapped, skipped, mode = check_repo(root)
    errors = sum(1 for p in problems if p.level == "error")
    payload = {
        "ok": errors == 0, "error_count": errors,
        "checked": checked, "wrapped": wrapped, "skipped": skipped, "mode": mode,
        "summary": summary_line(problems, checked, wrapped, skipped, mode),
        "problems": [asdict(p) for p in problems]}
    if args.as_json:
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        for problem in problems:
            sys.stdout.write(format_problem(problem) + "\n")
        sys.stdout.write(summary_line(problems, checked, wrapped, skipped, mode) + "\n")
    if args.require_toolchain and _gofmt_exe() is None:
        return 2
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
