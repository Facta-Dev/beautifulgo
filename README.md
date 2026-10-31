<!-- No banner yet. BeautifulRust has a painted banner in assets/; this repo has only
     the plugin icon for now. -->

# Beautiful Go

Three standard [Agent Skills](https://agentskills.io) and a lints config that teach coding
agents to write, review, port, and enforce idiomatic Go:

- **`go-best-practices`** loads whenever an agent writes or changes Go, and steers it
  toward idiomatic, robust, maintainable code — including the architecture contract when
  your repo follows the facta backend-go stack.
- **`go-review`** reviews existing Go code, a file, a package, a slice, or a diff, and
  writes a prioritized report where every finding cites the rule it breaks and shows the
  fix.
- **`go-port`** ports C, C++, Python, JavaScript, TypeScript, Java, or Rust to idiomatic
  Go with the same behavior, porting the original tests first so you can prove the two
  match.
- **`lints/`** is a drop-in golangci-lint v2 configuration whose depguard rules enforce
  the architecture in CI.

They work with Claude Code, OpenAI Codex, GitHub Copilot, Cursor, Gemini CLI, and any
other agent that reads the Agent Skills format. Every Go example in the skills is
syntax-checked in CI, and every depguard rule in the config is proven to fire against the
check module in [`lints/check/`](lints/check/).

The guidance is distilled from five sources, with a condensed digest of each bundled in
the skill so the agent can consult the original reasoning when it needs to:

- [Effective Go](https://go.dev/doc/effective_go)
- [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments) (the Go wiki checklist)
- [Google Go Style Guide](https://google.github.io/styleguide/go/)
- [Go Concurrency Patterns](https://go.dev/blog/concurrency-patterns) (Rob Pike)
- the facta backend-go handbook (the stack overlay digest, [backend-go-stack.md](skills/go-best-practices/references/backend-go-stack.md))

Where the sources disagree, the skill picks a side and says which.

*Status: first release in progress — see the [changelog](CHANGELOG.md).*

## What it changes

Asked to add an order to a Go backend, an agent without the skill put the pgx import
inside `domain.go`, wrapped the error with `%s`, and made every test that touches the
function depend on a live database. With the skill, the same agent kept the domain
I/O-free, declared the port where it is consumed, and pushed pgx into the adapter.
Condensed from those two runs:

```go
// Without the skill: domain.go reaches for the database driver, so no test
// can fake it and the use case cannot run without Postgres.
package store

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5"
)

type Order struct {
	ID         string
	TotalCents int64
	Status     string
}

// PlaceOrder wraps the driver error with %s and lives next to the model.
func PlaceOrder(ctx context.Context, conn *pgx.Conn, o Order) error {
	_, err := conn.Exec(ctx,
		"insert into orders (id, total_cents, status) values ($1, $2, $3)",
		o.ID, o.TotalCents, o.Status)
	if err != nil {
		return fmt.Errorf("order insert failed: %s", err)
	}
	return nil
}
```

```go
// With the skill: domain.go holds the order model and a sentinel, and
// nothing else — no net/http, no database/sql, no pgx, no platform.
package store

import "errors"

// ErrInvalidTotal is a sentinel the HTTP adapter can match with errors.Is.
var ErrInvalidTotal = errors.New("order: invalid total")

type Order struct {
	ID         string
	TotalCents int64
	Status     string
}
```

```go
// ports.go is written by the use case: the consumer defines the port it needs,
// and an interface with no consumer is not written in the first place.
package store

import "context"

// OrderStore is a port; postgres.go satisfies it, tests fake it.
type OrderStore interface {
	SaveOrder(ctx context.Context, o Order) error
}
```

```go
// usecase.go depends on the port interface, not on postgres.
package store

import (
	"context"
	"fmt"
)

func PlaceOrder(ctx context.Context, s OrderStore, o Order) error {
	if o.TotalCents <= 0 {
		return ErrInvalidTotal
	}
	if err := s.SaveOrder(ctx, o); err != nil {
		return fmt.Errorf("save order %s: %w", o.ID, err)
	}
	return nil
}
```

```go
// postgres.go is the only file in the slice that knows pgx exists. It calls
// the generated queries, maps rows to the domain type, and translates driver
// errors inward — never inline SQL, which lives in queries.sql.
package store

import (
	"context"
	"fmt"

	"github.com/acme/store-manager/internal/gen/db"
	"github.com/jackc/pgx/v5/pgxpool"
)

type PostgresStore struct {
	pool *pgxpool.Pool
	q    *db.Queries
}

func NewPostgresStore(pool *pgxpool.Pool) *PostgresStore {
	return &PostgresStore{pool: pool, q: db.New(pool)}
}

func (s *PostgresStore) SaveOrder(ctx context.Context, o Order) error {
	if err := s.q.InsertOrder(ctx, db.InsertOrderParams{
		ID:         o.ID,
		TotalCents: o.TotalCents,
		Status:     o.Status,
	}); err != nil {
		return fmt.Errorf("save order %s: %w", o.ID, err)
	}
	return nil
}
```

The depguard rules in the lints config make the broken shape fail `golangci-lint run`
before it is committed: `domain-pure` denies `github.com/jackc/pgx/v5` in
`**/internal/features/**/domain.go`, and the rest of the law is on the same file. See
[Enforcing the rules with golangci-lint](#enforcing-the-rules-with-golangci-lint).

## Install

Each skill is a folder under `skills/`: `go-best-practices/`, `go-review/`, and
`go-port/`. Every option below puts those folders where your agent looks for skills.
Install all three; the review and port skills lean on the best-practices skill for style.

### Any agent, one command

The [`skills`](https://github.com/vercel-labs/skills) installer supports most agents
(Node 22.20 or later):

```bash
npx skills add Facta-Dev/beautifulgo
```

Add `-g` to install for your user instead of the current project, or `-a <agent>` to pick
an agent, such as `-a codex` or `-a cursor`.

### Claude Code

Install it as a plugin so updates arrive with one command:

```bash
claude plugin install beautiful-go --marketplace Facta-Dev/beautifulgo
```

Inside a session, the same thing is:

```
/plugin marketplace add Facta-Dev/beautifulgo
/plugin install beautiful-go@beautiful-go
```

This installs all three skills. They appear as `/beautiful-go:go-best-practices`,
`/beautiful-go:go-review`, and `/beautiful-go:go-port`, though you rarely need to call
them, since they trigger on their own. To try it for one session without installing,
clone the repo and run `claude --plugin-dir ./beautifulgo`.

### OpenAI Codex

Install it as a plugin:

```bash
codex plugin marketplace add Facta-Dev/beautifulgo
codex plugin add beautiful-go@beautiful-go
```

This installs all three skills as `beautiful-go:go-best-practices`,
`beautiful-go:go-review`, and `beautiful-go:go-port`. The same package works in the
ChatGPT desktop app.

### GitHub Copilot

With GitHub CLI 2.90 or later:

```bash
gh skill install Facta-Dev/beautifulgo go-best-practices
gh skill install Facta-Dev/beautifulgo go-review
gh skill install Facta-Dev/beautifulgo go-port
```

This installs into the current project by default. Add `--scope user` to install for your
user, or `--agent <name>` to install for a different agent.

### Gemini CLI

```bash
gemini skills install https://github.com/Facta-Dev/beautifulgo --path skills/go-best-practices
gemini skills install https://github.com/Facta-Dev/beautifulgo --path skills/go-review
gemini skills install https://github.com/Facta-Dev/beautifulgo --path skills/go-port
```

### Cursor or anything else: copy the folder

Clone the repo and copy the three skill folders into your agent's skills directory.
Most agents now read the shared `.agents/skills/` location:

```bash
git clone https://github.com/Facta-Dev/beautifulgo
mkdir -p ~/.agents/skills
cp -R beautifulgo/skills/go-* ~/.agents/skills/
```

| Agent | User directory | Project directory |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| OpenAI Codex | `~/.agents/skills/` | `.agents/skills/` |
| GitHub Copilot | `~/.copilot/skills/` or `~/.agents/skills/` | `.github/skills/` or `.agents/skills/` |
| Cursor | `~/.cursor/skills/` or `~/.agents/skills/` | `.cursor/skills/` or `.agents/skills/` |
| Gemini CLI | `~/.gemini/skills/` or `~/.agents/skills/` | `.gemini/skills/` or `.agents/skills/` |

Claude Code does not read `.agents/skills/`, so use its own directory or the plugin.
Restart the agent if the skill doesn't show up right away.

### claude.ai

claude.ai takes one zip per skill, with the skill folder as the zip root:

```bash
cd skills
zip -r ../go-best-practices.zip go-best-practices -x '*.DS_Store' -x '*/evals/*'
zip -r ../go-review.zip go-review -x '*.DS_Store' -x '*/evals/*'
zip -r ../go-port.zip go-port -x '*.DS_Store' -x '*/evals/*'
```

Upload each under **Customize > Skills**. Code execution must be enabled first.

## Reviewing existing code

Ask your agent to review a file, package, slice, or diff, for example "review
internal/features/store" or "what would you change in this PR". The `go-review` skill
detects whether the repo is on the facta stack and states which mode it reviewed under,
runs `gofmt -l`, `go vet`, `golangci-lint run`, and `go test -race` when a toolchain is
available, then writes a report with three tiers: must fix, should fix, and consider.
Every finding gives a `file:line` location, the rule it breaks with its source (a depguard
rule name, a Google Go Style Guide section, a wiki entry, an Effective Go passage, a
golangci linter name, or the backend-go handbook), and the smallest code change that fixes
it. Each report ends with what the code already does well, so a review never flattens
valid idioms to make the report longer.

[`examples/review-inventory.md`](examples/review-inventory.md) is a real review the skill
produced for the deliberately messy module in the eval cases.

## Porting code to Go

Ask your agent to port a module, for example "port config.c to Go" or "rewrite this
Python service in Go". The `go-port` skill reads the original and its tests, ports the
tests first as table-driven Go tests, designs a Go API instead of transliterating the
original, and verifies with `go test` and `golangci-lint run`. It maps each language's
habits to their Go equivalents: `NULL` and `None` to `nil` plus the `v, ok :=` pattern,
error codes and exceptions to sentinel errors wrapped with `%w`, out-parameters to return
values, flag ints and magic strings to typed constants, fixed buffers to slices, and dict
insertion order to an ordered slice when order is observable, because a `map` would
silently reorder output. Each port comes with a `PORTING.md` that maps the old API and
tests to the new ones and lists every deliberate difference. When the destination is a
facta backend-go repo, a port that touches HTTP or storage lands as a vertical slice
under the architecture contract.

## The stack

The skills enforce the facta backend-go template's stack, restrictively — when a repo has
`go.mod`, `internal/features/`, and a `.golangci.yml` with these rules, the writing and
review skills read
[`references/backend-go-stack.md`](skills/go-best-practices/references/backend-go-stack.md)
first and hold the architecture contract at full strictness. On general Go repos, only
the general rules apply: the skills do not impose six-file slices on a CLI.

| Concern | The stack says |
|---|---|
| Language and module | Go 1.27, one `go.mod` per repo, no per-slice modules |
| Routing | stdlib `net/http` `ServeMux` with method + wildcard patterns — **no gin/echo/fiber/chi** |
| Database | `pgx/v5` through `pgxpool`, built once at the composition root |
| Queries | sqlc, per-slice `queries.sql` → committed `internal/gen/db`, never hand-edited |
| Migrations | goose with `+goose Up` and `+goose Down` sections, never applied at server startup |
| Logging | `slog` with the JSON handler, `request_id` from middleware, never inside `domain.go` |
| Linting | `golangci-lint run` with the depguard architecture law after `gofmt -l` and `go vet` |
| Auth | bcrypt + pepper and JWT through the `authx` platform adapter |
| Async work | an outbox worker pattern, not goroutines spawned in handlers |
| Cache and realtime | Dragonfly over the Redis protocol via go-redis, and pgvector, only where the template's realtime and persistence docs define them |

The template's topology is part of the contract, not a suggestion: hexagonal (ports and
adapters) plus vertical slicing, dependencies pointing inward (composition root → slices
→ ports → domain). Each slice is six files — `domain.go`, `ports.go`, `usecase.go`,
`http.go`, `postgres.go`, `module.go` — plus its `queries.sql`; `platform/` holds the
transversal adapters (config, httpx, pgx, email, realtime, authx); `internal/shared/`
holds the kernel (`apperr`, `rolex`, `clockx`, `idgen`). Routes are declared per slice in
`module.go: Register(mux, Deps)` and composed at `cmd/api`. Slices never import each
other, and the domain imports nothing that does I/O. The stack mandate is deliberately
narrow: leave the template's shape alone (a correct six-file slice is already lint-clean)
and spend judgment on the code inside it.

## Enforcing the rules with golangci-lint

The skills teach the rules; the lints keep them from slipping back in. Copy
[`lints/.golangci.yml`](lints/.golangci.yml) next to your `go.mod`, substitute
the module path once (internal-package rules must name the real module path,
because depguard's `pkg` patterns prefix-match import paths — pattern plus
every subpackage), then run:

```bash
sed -i '' 's|github.com/<scope>/<app>|github.com/your/module|g' .golangci.yml
golangci-lint run
```

On the facta `backend-go` template this substitution is a no-op before its
`rename.sh` runs: the template's module path is `github.com/<scope>/<app>`
verbatim. The `files:` globs already use `**/internal/...` forms, so they match
any module without substitution.

It enables the standard linters (errcheck, govet, ineffassign, staticcheck, unused) plus
contextcheck, depguard, errname, errorlint, and noctx, and carries the architecture law
in four depguard rules:

| Rule | Files | What it enforces |
|---|---|---|
| `domain-pure` | `**/domain.go` | an allow-list: the standard library plus `internal/shared` only — notably denying `net/http`, `database/sql`, `pgx/v5`, `internal/gen`, `internal/platform`, and other slices |
| `usecase-transport-free` | `**/usecase.go`, `**/ports.go` | `net/http`, `database/sql`, `pgx/v5`, `internal/gen`, `internal/platform` |
| `slice-isolation` | `**/internal/features/**` | any import from `internal/features` — slices stay sealed, composition happens in `cmd/api` |
| `platform-no-features` | `**/internal/platform/**` | any import from `internal/features` — platform serves features, never consumes them |

Internal-package rules must carry the real module path, because depguard's
`pkg` patterns prefix-match import paths (pattern plus every subpackage, `$`
for an exact match) — that is why the shipped file carries the
`github.com/<scope>/<app>` placeholder and every other project substitutes its
module path once (the one-line `sed` above). Test files are exempted from
errcheck only. `errorlint`'s comparison, assertion, and `errorf` checks are
all on, so `%s`-wrapped errors, `err == sentinel` comparisons, and
cast-asserted error types all fail the gate.

Every rule in the file is proven to fire. [`lints/check/`](lints/check/) is a throwaway
Go module with a clean six-file slice that must produce zero findings, next to one
deliberately violating file per rule, each marked `// want <linter>`; this script runs
the gate on it from the repo root:

```bash
bash scripts/check-lints.sh
```

It fails if a marked violation goes unreported, if something unexpected fires, if the
clean slice produces any finding, or if the check module's rule table drifts from
`lints/.golangci.yml`. Requires golangci-lint v2.x on `PATH`.
Stack repos run the full gate in CI: `gofmt -l` empty, `go vet ./...`, `golangci-lint run`,
then `go test ./...` with `-race`.

## What the writing skill covers

`skills/go-best-practices/SKILL.md` is about 500 lines, organized so an agent can scan it
while coding:

1. Mindset: Go-shaped code, not transliterated Python or Java; zero-I/O domain
2. Architecture contract: the facta stack's MUST/MUST NOT list, with the lints config as enforcement
3. Before you hand back code: `gofmt -l`, `go vet`, `golangci-lint run`, `go test`, gen-check; the nolint policy
4. Types and interfaces: accept interfaces, return concrete types; no interface pollution; no bool parameters
5. Errors and panics: sentinels, `%w`, `errors.Is`/`As`; panic only for programmer bugs
6. Context propagation: `ctx` first, never stored in structs, never dropped mid-chain
7. Concurrency: every goroutine has an owner and a shutdown path; channels for ownership, mutexes for state
8. Standard library first: stdlib `ServeMux`, no framework routers; dependencies cost supply-chain surface
9. Packages and file organization: the slice topology wins; no horizontal god-directories
10. Logging: slog only, JSON handler, structured attrs, never inside `domain.go`, never log-and-return
11. Tests: table-driven with named fields, fakes over mocks, `t.Parallel`, `-race`
12. Performance, in order: measure first, preallocate, stream, note deliberate ceilings
13. Final checklist
14. References: which digest to open when

`skills/go-best-practices/references/` holds one digest per source for deeper lookups.

## Layout

```
beautifulgo/
├── .claude-plugin/
│   ├── plugin.json         Claude Code plugin manifest
│   └── marketplace.json    lets this repo act as its own marketplace
├── .agents/plugins/
│   └── marketplace.json    the same, for Codex
├── plugin.json             Codex and ChatGPT plugin manifest
├── assets/icon.png         plugin icon for Codex and ChatGPT
├── skills/
│   ├── go-best-practices/  writing skill
│   │   ├── SKILL.md
│   │   ├── references/     one digest per source, plus backend-go-stack.md
│   │   └── evals/
│   ├── go-review/          review skill
│   │   ├── SKILL.md
│   │   └── evals/
│   └── go-port/            porting skill
│       ├── SKILL.md
│       └── evals/          a C module and a Python module to port
├── lints/
│   ├── .golangci.yml       the drop-in golangci-lint v2 config
│   ├── README.md           install copy and the rule table
│   └── check/              a Go module: one deliberate violation per rule
├── scripts/
│   ├── check-skill.py      validates skills, evals, and manifests
│   ├── check-lints.sh      proves every depguard rule in the config fires
│   ├── check-examples.py   syntax-checks every Go example in the docs
│   ├── examples.json       context that lets fragment examples parse
│   └── package-openai-plugin.py   builds the ChatGPT / Codex directory ZIP
├── tests/
│   └── test_*.py           unittest suites for the checkers
├── examples/
│   └── review-inventory.md a real review report
├── CHANGELOG.md
├── CONTRIBUTING.md
├── PRIVACY.md
└── README.md
```

## Testing the skills

`skills/go-best-practices/evals/` holds three test cases in the layout `claude plugin
eval` reads: a stdlib-only rate-limiter library task, a refactor-this-module task with an
input file, and a slice-regen task that adds a field and a query to a working six-file
slice — the stack-overlay case, which checks the agent upgrades the domain and pairs the
query with the migration without touching the six-file shape. Each case has the prompt, a
description of a good result, and one assertion per file under `graders/`, including
"does not rewrite existing code" graders. Run them with and without the skill from the
skill directory:

```bash
claude plugin eval . --allow-tools Write,Edit,Bash --scaffold
```

`skills/go-review/evals/` holds two review cases: one over a slice-shaped
module with planted architecture violations and valid shapes that must be left
alone, and one over a plain non-stack module (the general-rules mode), each
with its planted general-rule violations — and
`skills/go-port/evals/` holds a C config parser and a Python task graph to port, each
with its original test suite. Run them the same way from each skill's directory.

These are real model runs and are billed.

## Updating

Edit the skill, bump `version` in **both** `.claude-plugin/plugin.json` and
`plugin.json` (the checker fails if they differ), commit, and push. Claude Code plugin
users pick up the new version with:

```bash
claude plugin update beautiful-go
```

Codex users refresh the marketplace with:

```bash
codex plugin marketplace upgrade beautiful-go
```

Anyone who copied the folder or used an installer re-runs the install command. Record
each release in [CHANGELOG.md](CHANGELOG.md).

Validate before pushing. `python3 scripts/check-skill.py` checks skill frontmatter,
links, eval cases, and plugin manifests. Pass `--json` for machine-readable output.
`python3 scripts/check-examples.py` syntax-checks every Go block in the skills, reference
digests, README, and examples with `gofmt -e`. `python3 -m unittest discover tests` runs
the checker test suites.

```bash
python3 scripts/check-skill.py
python3 scripts/check-examples.py
python3 -m unittest discover tests
claude plugin validate .
```

To publish a release to the ChatGPT / Codex Plugins Directory, update `release_notes` in
`plugin.json`, then build the upload:

```bash
python3 scripts/package-openai-plugin.py
```

This writes `dist/beautiful-go-<version>.zip` with the manifest, the skills and their
references, the icon, the license, and the privacy policy, but not the eval cases. Upload
it at [platform.openai.com/plugins](https://platform.openai.com/plugins) from a verified
developer account, as described in OpenAI's
[submission guide](https://developers.openai.com/plugins/deploy/submission).

## Contributing

Issues and pull requests are welcome. Every rule needs a published source; see
[CONTRIBUTING.md](CONTRIBUTING.md) for how to propose a rule, report a review false
positive, or add an eval case.

## Sources and attribution

The guidance in this skill is a synthesis. The five digests in
`skills/go-best-practices/references/` are paraphrased summaries written for this
project; they restate each source's advice in condensed form and link back to the
original. Read the originals for the full reasoning.

| Source | Author | License |
|---|---|---|
| [Effective Go](https://go.dev/doc/effective_go) | The Go Project | CC BY 3.0 |
| [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments) | The Go Project (Go wiki) | CC BY 3.0 |
| [Google Go Style Guide](https://google.github.io/styleguide/go/) | Google | CC BY 3.0 |
| [Go Concurrency Patterns](https://go.dev/blog/concurrency-patterns) | Rob Pike | CC BY 3.0 |
| the facta backend-go handbook | Facta-Dev | template documentation (the digest in this repo is MIT) |

The skill text, the digests, and the config in this repository are MIT licensed (see
[LICENSE](LICENSE)). The icon gopher is our own art, not the official Go logo or mascot.

## License

MIT. See [LICENSE](LICENSE).