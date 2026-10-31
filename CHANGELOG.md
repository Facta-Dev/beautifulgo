# Changelog

All notable changes to this project are listed here. Versions follow
[Semantic Versioning](https://semver.org/), and the version lives in both manifests,
`.claude-plugin/plugin.json` and `plugin.json`, kept in step — `scripts/check-skill.py`
fails when the two differ.

## [Unreleased]

### Added

- Nothing yet; the first cut of the skills is drafted under [0.1.0].

## [0.1.0] - draft

First release, mirroring beautifulrust 1.0.0 in shape: three skills, packaging, license,
attribution.

### Added

- **The `go-best-practices` skill**, distilled from Effective Go, the Go Code Review
  Comments wiki, the Google Go Style Guide, Go Concurrency Patterns, and the facta
  backend-go handbook, with one reference digest per source. The stack overlay
  (`backend-go-stack.md`) holds the architecture contract: hexagonal ports and adapters
  plus vertical slicing, a zero-I/O `domain.go`, consumer-defined ports, sealed slices,
  per-slice `queries.sql` paired with the migration that created its tables, and the
  `{detail, code}` error envelope written only by `httpx`.
- **The `go-review` skill.** Reviews a file, package, slice, or diff and writes a
  prioritized report: must fix, should fix, and consider. Every finding cites a
  `file:line`, the rule it breaks and its source, and the smallest code change that
  fixes it. It runs `gofmt -l`, `go vet`, `golangci-lint run`, and `go test -race` when
  a toolchain is available, and ends with what the code already does well.
- **The `go-port` skill.** Ports C, C++, Python, JavaScript, TypeScript, Java, or Rust to
  idiomatic Go with the same behavior. It ports the original tests first, maps each
  language's habits to Go (`NULL` and `None` to `nil` plus the ok pattern, error codes
  and exceptions to sentinel errors wrapped with `%w`, out-params to return values, flag
  ints and magic strings to typed constants, dict insertion order to an ordered slice
  when order is observable), keeps the port proportionate instead of reimplementing the
  source language's runtime, and writes a `PORTING.md` with API and test mappings and
  every deliberate difference.
- **Drop-in lints in `lints/.golangci.yml`** — the standard linters plus contextcheck,
  depguard, errname, errorlint, noctx, and the four depguard rules (`domain-pure`,
  `usecase-transport-free`, `slice-isolation`, `platform-no-features`). `lints/check/` is
  a throwaway Go module whose clean files must produce zero findings and whose violating
  files prove every rule fires, verified by `scripts/check-lints.sh`.
- **Packaging.** `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` make
  the repo a Claude Code plugin that is its own marketplace;
  `.agents/plugins/marketplace.json` and root `plugin.json` package the same skills for
  Codex and the ChatGPT / Codex Plugins Directory, built by
  `scripts/package-openai-plugin.py` without the eval cases.
- **Checker scripts and test suites.** `scripts/check-skill.py`, `scripts/check-examples.py`,
  and `scripts/check-lints.sh` with unittest suites in `tests/` run in CI on every push
  and pull request. All validators are stdlib-Python-only.
- **MIT license, source attribution in the README, and a plugin icon.**

[Unreleased]: https://github.com/Facta-Dev/beautifulgo/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Facta-Dev/beautifulgo/releases/tag/v0.1.0