#!/usr/bin/env bash
# Prove that lints/.golangci.yml fires. Every want marker inside lints/check
# must report on its marked line, nothing unmarked may report, the clean slice
# must stay silent, and the violation table in lints/check must match the
# config's rule names. The proof module substitutes the config's
# github.com/<scope>/<app> placeholder with its own module path -- exactly what
# a project does -- so the shipped file is proven as a project would use it.
#
# Exit 1 on any failure, 2 when the toolchain is missing (go with a matching
# stdlib, golangci-lint v2, python3).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$ROOT/lints/.golangci.yml"
CHECK="$ROOT/lints/check"

die() { echo "check-lints: $*" >&2; exit "${2:-1}"; }

command -v python3 >/dev/null 2>&1 || die "python3 not found on PATH" 2
command -v go >/dev/null 2>&1 || die "go not found on PATH" 2
command -v golangci-lint >/dev/null 2>&1 || die "golangci-lint not found on PATH" 2
V="$(golangci-lint version 2>/dev/null || true)"
echo "$V" | grep -Eq 'version [0-9]+\.' || die "cannot read the golangci-lint version ($V)" 2
echo "$V" | grep -Eq 'version 2\.' || die "golangci-lint v2.x is required, found: $V" 2

PROOF="$CHECK/.golangci.proof.yml"
LOG="$(mktemp "${TMPDIR:-/tmp}/lints-log.XXXXXX")"
JSON="$(mktemp "${TMPDIR:-/tmp}/lints-json.XXXXXX")"
trap 'rm -f "$PROOF" "$LOG" "$JSON"' EXIT

sed 's|github.com/<scope>/<app>|github.com/beautifulgo/check|g' "$CONFIG" > "$PROOF"
grep -q 'github.com/beautifulgo/check' "$PROOF" \
  || die "the placeholder substitution produced no check-module paths"

set +e
(cd "$CHECK" && golangci-lint run -c .golangci.proof.yml --output.json.path "$JSON" --show-stats=false ./...) >"$LOG" 2>&1
STATUS=$?
set -e

if [ ! -s "$JSON" ] && [ "$STATUS" -ne 0 ]; then
  die "golangci-lint run failed without findings (exit $STATUS): $(tail -3 "$LOG")"
fi
[ -s "$JSON" ] || die "golangci-lint produced no findings file"

python3 - "$CONFIG" "$CHECK" "$JSON" "$STATUS" <<'PYEOF'
import json, re, sys
from pathlib import Path

config_path, check_path, json_path, status_s = sys.argv[1:]
status = int(status_s)
check = Path(check_path)
config = Path(config_path).read_text(encoding="utf-8")

DEFAULT_STANDARD = {"errcheck", "govet", "ineffassign", "staticcheck", "unused"}

def parse_config(text):
    lines = text.splitlines()
    enabled = set(DEFAULT_STANDARD)
    rules = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if line == "  enable:":
            i += 1
            while i < len(lines) and lines[i].startswith("    - "):
                enabled.add(lines[i][6:].split()[0])
                i += 1
            continue
        if line == "      rules:":
            i += 1
            while i < len(lines) and lines[i].startswith("        "):
                m = re.match(r"^        ([a-z-]+):$", lines[i])
                if not m:
                    i += 1
                    continue
                name = m.group(1)
                rules[name] = []
                i += 1
                while i < len(lines) and lines[i].startswith("          "):
                    dm = re.match(r"^            - pkg: (.+)$", lines[i])
                    if dm:
                        rules[name].append(dm.group(1).strip())
                    i += 1
            continue
        i += 1
    return enabled, rules

def read_markers():
    """(file_rel, line, {linters}) for every // want marker in the check module."""
    out = []
    for path in sorted(check.rglob("*.go")):
        rel = path.relative_to(check).as_posix()
        if rel.startswith("."):
            continue
        for n, text in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            m = re.search(r"//\s*want\s+((?:[A-Za-z-]+)(?:\s+[A-Za-z-]+)*)\s*$", text)
            if m:
                out.append((rel, n, set(m.group(1).lower().split())))
    return out

def read_findings():
    """(file_rel, line, linter, text) from the golangci-lint JSON report."""
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    out = []
    for issue in data.get("Issues") or []:
        pos = issue.get("Pos") or {}
        rel = (pos.get("Filename") or "").replace("\\", "/").lstrip("./")
        line_no = int(pos.get("Line") or 0)
        out.append((rel, line_no, issue.get("FromLinter") or "?", issue.get("Text") or ""))
    return out

def read_table():
    """(rule, linter, file) rows parsed from the violations package doc.go."""
    rows = []
    doc = check / "internal" / "features" / "violations" / "doc.go"
    for text in doc.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*//\s*\|\s*([a-z-]+)\s*\|\s*([a-z-]+)\s*\|\s*(\S+)\s*\|\s*$", text)
        if not m or m.group(1) == "rule" or set(m.group(1)) == {"-"}:
            continue
        rows.append((m.group(1), m.group(2), m.group(3)))
    return rows

markers = read_markers()
findings = read_findings()
rows = read_table()
enabled, rules = parse_config(config)

failed = False
if not markers:
    print("no want markers found in the check module")
    failed = True

by_pos = {}
for rel, line_no, linter, text in findings:
    by_pos.setdefault((rel, line_no), []).append((linter, text))

consumed = set()
report = []
for rel, line_no, want in markers:
    hits = sorted(f for f in findings if (f[0], f[1]) == (rel, line_no) and f[2] in want)
    if not hits:
        report.append((rel, line_no, ", ".join(sorted(want)), "MISSING"))
        failed = True
        continue
    for f in hits:
        consumed.add((f[0], f[1], f[2]))
    rule = next((r for r, l, _f in rows if _f == rel and l in want), "-")
    report.append((rel, line_no, ", ".join(sorted(want)), "fired"))

for rel, line_no, linter, text in findings:
    if (rel, line_no, linter) in consumed:
        continue
    marked = (rel, line_no) in {(m[0], m[1]) for m in markers}
    if marked:
        print(f"unexpected linter on a marked line: {rel}:{line_no}: {linter}: {text}")
    else:
        print(f"finding on an unmarked line: {rel}:{line_no}: {linter}: {text}")
    failed = True

row_by_file = {}
for rule, linter, rel in rows:
    row_by_file.setdefault(rel, []).append((rule, linter))
    if linter not in enabled:
        print(f"table drift: linter '{linter}' is not enabled by lints/.golangci.yml")
        failed = True
    if rule != "-" and rule not in rules:
        print(f"table drift: rule '{rule}' is not a depguard rule in lints/.golangci.yml")
        failed = True

covered = {rule for rule, _l, _f in rows if rule != "-"}
for name in rules:
    if name not in covered:
        print(f"table drift: depguard rule '{name}' has no violation row in doc.go")
        failed = True

width_l = max((len(r[2]) for r in report), default=4)
width_l = max(width_l, 4)
print(f"{'file:line'.ljust(56)}  {'want'.ljust(width_l)}  status")
print(f"{'-' * 56}  {'-' * width_l}  ------")
for rel, line_no, want, state in report:
    print(f"{f'{rel}:{line_no}'.ljust(56)}  {want.ljust(width_l)}  {state}")

if failed:
    print()
    print("check-lints: FAIL")
    if status not in (0, 1):
        print(f"golangci-lint exited {status}; see the run log for load errors")
    sys.exit(1)

print()
print(f"{len(report)} expected lints fired; table matches {config_path}")
PYEOF