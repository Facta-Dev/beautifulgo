# Graph Report - .  (2026-11-22)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1081 nodes · 1488 edges · 190 communities (135 shown, 55 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 81 edges (avg confidence: 0.71)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e3f8ca96`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Checker
- CheckSkillTests
- write
- backend-go stack (digest)
- Order
- parse_schedule
- Creator
- check-examples.py
- interface
- Beautiful Go
- What You Must Do When Invoked
- config_parse
- Go best practices
- text_of
- Go review: <what was reviewed>
- UseCase
- Go port
- Google Go Style Guide (digest)
- Store
- graphify reference: extra exports and benchmark
- Effective Go (digest)
- Go Code Review Comments (digest)
- PackageTests
- Go Concurrency Patterns (digest)
- <app> API Designer
- <app> Migration Reviewer
- <app> Ownership Reviewer
- <app> Architect Agent
- <app> Build Resolver Agent
- <app> Code Explorer Agent
- <app> Code Reviewer Agent
- <app> Planner Agent
- <app> TDD Guide Agent
- <app> Depguard Reviewer
- <app> Go Test Author
- <app> Add Handler
- <app> Add Module
- <app> Claim Check skill
- <app> Clean-Room Rebuild skill
- <app> Corpus Retrieval skill
- <app> Depguard Guard
- <app> Diagnosing Bugs skill
- <app> Domain Modeling skill
- <app> Grilling skill
- <app> learn skill
- <app> Ownership Author
- <app> plan skill
- <app> Research skill
- <app> review skill
- <app> ship skill
- <app> spec skill
- <app> TDD skill
- <app> Verified Status skill
- graphify reference: query, path, explain
- build
- Hub
- BeautifulGo lints
- Error
- beautifulgo — agent instructions
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- janitor
- Runner
- guard-bash.sh
- /add-handler
- /add-module
- /claim-check
- /clean-room-rebuild
- /corpus-retrieval
- /depguard-guard
- /diagnosing-bugs
- /domain-modeling
- /grilling
- /learn
- /ownership-author
- /plan
- /research
- /review
- /ship
- /spec
- /tdd
- /verified-status
- Playbooks for `beautifulgo` — load on demand
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- Row
- Name
- Load
- Fetcher
- Widget
- Peek
- check-lints.sh
- CLAUDE.md
- README.md
- CREDITS.md
- CREDITS.md
- CREDITS.md
- CREDITS.md
- CREDITS.md
- extraction-spec.md
- CREDITS.md
- CREDITS.md
- CREDITS.md
- CREDITS.md
- kernel.go
- PRIVACY.md
- place-files.sh
- place-files.sh
- place-files.sh
- place-files.sh
- place-files.sh
- place-files.sh
- github.com/acme/inventory-cli
- github.com/acme/store-manager
- github.com/beautifulgo/check

## God Nodes (most connected - your core abstractions)
1. `CheckSkillTests` - 43 edges
2. `build_valid_repo()` - 40 edges
3. `write()` - 31 edges
4. `Checker` - 27 edges
5. `Beautiful Go` - 19 edges
6. `check_repo()` - 17 edges
7. `YamlParser` - 16 edges
8. `Go best practices` - 15 edges
9. `interface` - 14 edges
10. `config_parse()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `NewStore()` --calls--> `New()`  [INFERRED]
  skills/go-review/evals/review-messy-store/files/internal/features/store/postgres.go → skills/go-best-practices/evals/refactor-member-module/files/member.go
- `Register()` --calls--> `NewHandler()`  [INFERRED]
  skills/go-best-practices/evals/slice-regen/files/internal/features/widgets/module.go → skills/go-best-practices/evals/slice-regen/files/internal/features/widgets/http.go
- `Register()` --calls--> `NewCreator()`  [INFERRED]
  skills/go-best-practices/evals/slice-regen/files/internal/features/widgets/module.go → skills/go-best-practices/evals/slice-regen/files/internal/features/widgets/usecase.go
- `test_basic()` --calls--> `config_parse()`  [INFERRED]
  skills/go-port/evals/port-c-config-parser/files/test_config.c → skills/go-port/evals/port-c-config-parser/files/config.c
- `test_case_insensitive()` --calls--> `config_parse()`  [INFERRED]
  skills/go-port/evals/port-c-config-parser/files/test_config.c → skills/go-port/evals/port-c-config-parser/files/config.c

## Import Cycles
- None detected.

## Communities (190 total, 55 thin omitted)

### Community 0 - "Checker"
Cohesion: 0.10
Nodes (26): check_repo(), Checker, _fold_block(), format_problem(), _is_relative(), _json_key_line(), main(), _normalize_url() (+18 more)

### Community 1 - "CheckSkillTests"
Cohesion: 0.15
Nodes (10): add_portable_plugin(), build_valid_repo(), CheckSkillTests, error_messages(), formatted(), load_checker(), png_header(), portable_with() (+2 more)

### Community 2 - "write"
Cohesion: 0.08
Nodes (9): CheckRepoTest, DomainTest, FindBlocksTest, GofmtModeTest, HarnessTest, RealRepoTest, RepoTest, WrapTest (+1 more)

### Community 3 - "backend-go stack (digest)"
Cohesion: 0.05
Nodes (40): [0.1.0] - draft, Added, Added, Changelog, [Unreleased], Contributing, Good first contributions, License (+32 more)

### Community 4 - "Order"
Cohesion: 0.08
Nodes (27): Member, Membership, MemberStore, memoryStore, SyncOnce, Item, Mutex, Pool (+19 more)

### Community 5 - "parse_schedule"
Cohesion: 0.12
Nodes (24): CycleError, execution_order(), _find_cycle(), MissingDependency, parse_schedule(), ParseError, Exception, Parse a small schedule format and run its tasks in waves.  Format, one task per (+16 more)

### Community 6 - "Creator"
Cohesion: 0.09
Nodes (26): Request, ResponseWriter, Router, Time, Widget, NewHandler(), writeWidgetErr(), Time (+18 more)

### Community 7 - "check-examples.py"
Cohesion: 0.12
Nodes (31): apply_harness(), as_text(), balance_problems(), Block, check_repo(), doc_files(), find_blocks(), first_code_line() (+23 more)

### Community 8 - "interface"
Cohesion: 0.07
Nodes (29): author, name, url, interface, publication, description, extensions, com.openai (+21 more)

### Community 9 - "Beautiful Go"
Cohesion: 0.08
Nodes (26): Agent kit (Claude Code), Any agent, one command, Architecture diagrams, Beautiful Go, claude.ai, Claude Code, Contributing, Cursor or anything else: copy the folder (+18 more)

### Community 10 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 11 - "config_parse"
Cohesion: 0.28
Nodes (19): config_t, config_count(), config_free(), config_get(), config_get_int(), config_parse(), dup_range(), fail() (+11 more)

### Community 12 - "Go best practices"
Cohesion: 0.11
Nodes (18): 10. Logging, 11. Tests, 12. Performance, in order, 13. Final checklist, 14. References, 1. Mindset, 2. Architecture contract (the backend-go stack), 3. Before you hand back code (+10 more)

### Community 13 - "text_of"
Cohesion: 0.15
Nodes (11): chi_mentions(), ChiMandatePresent, ExactReadmePins, Lockstep, OldProhibitionRemoved, Contract pins on the backend-go stack wording in the repo's docs.  The chi manda, Word-boundary chi hits in one file (hyphen/slash count as boundaries)., The stack no longer bans chi; nothing may still say it does. (+3 more)

### Community 14 - "Go review: <what was reviewed>"
Cohesion: 0.13
Nodes (14): 1. Decide the scope, 1. <Short title> (`internal/features/store/domain.go:26`), 2. ..., 2. Run the tools first, if you can, 3. ..., 3. What to look for, in priority order, 4. Write the report, 5. Offer the lints (+6 more)

### Community 15 - "UseCase"
Cohesion: 0.22
Nodes (8): Fetch(), Store, Context, Store, Widget, New(), Now, UseCase

### Community 16 - "Go port"
Cohesion: 0.15
Nodes (12): 1. Understand the original before writing anything, 2. Port the tests first, 3. Design the Go API, then implement it, 4. Land it under the stack when the destination is a facta backend-go repo, 5. Keep the port proportionate, 6. Verify, 7. Write the porting notes, From C and C++ (+4 more)

### Community 17 - "Google Go Style Guide (digest)"
Cohesion: 0.18
Nodes (10): Application vs library code, Concurrency, Core principles, Documentation, Error handling decisions, Functions and design, Google Go Style Guide (digest), Naming (+2 more)

### Community 18 - "Store"
Cohesion: 0.38
Nodes (5): Item, Store, Context, mustQty(), ParseItem()

### Community 19 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 20 - "Effective Go (digest)"
Cohesion: 0.22
Nodes (8): Concurrency flavor, Control flow and declarations, Data: structs, slices, maps, Effective Go (digest), Formatting and naming, Functions and multiple returns, Methods, interfaces, and errors, Where this document is dated

### Community 21 - "Go Code Review Comments (digest)"
Cohesion: 0.22
Nodes (8): API shape, Concurrency, Error handling, Functions and parameters, Go Code Review Comments (digest), Naming and imports, Types and data, Where the wiki and other digests disagree

### Community 23 - "Go Concurrency Patterns (digest)"
Cohesion: 0.25
Nodes (7): Cancellation discipline, Correctness notes review looks for, Go Concurrency Patterns (digest), Patterns from the talk, The model, When NOT to reach for channels, Where this digest and SKILL.md differ

### Community 24 - "<app> API Designer"
Cohesion: 0.29
Nodes (6): <app> API Designer, Core Mission, Expertise Areas, Guiding Principles, Output Format, Quality Standards

### Community 25 - "<app> Migration Reviewer"
Cohesion: 0.29
Nodes (6): <app> Migration Reviewer, Core Mission, Expertise Areas, Guiding Principles, Output Format, Quality Standards

### Community 26 - "<app> Ownership Reviewer"
Cohesion: 0.29
Nodes (6): <app> Ownership Reviewer, Core Mission, Expertise Areas, Guiding Principles, Output Format, Quality Standards

### Community 27 - "<app> Architect Agent"
Cohesion: 0.29
Nodes (6): <app> Architect Agent, Core Mission, Expertise Areas, Guiding Principles, Output Format, Quality Standards

### Community 28 - "<app> Build Resolver Agent"
Cohesion: 0.29
Nodes (6): <app> Build Resolver Agent, Core Mission, Expertise Areas, Guiding Principles, Output Format, Quality Standards

### Community 29 - "<app> Code Explorer Agent"
Cohesion: 0.29
Nodes (6): <app> Code Explorer Agent, Core Mission, Expertise Areas, Guiding Principles, Output Format, Quality Standards

### Community 30 - "<app> Code Reviewer Agent"
Cohesion: 0.29
Nodes (6): <app> Code Reviewer Agent, Core Mission, Expertise Areas, Guiding Principles, Output Format, Quality Standards

### Community 31 - "<app> Planner Agent"
Cohesion: 0.29
Nodes (6): <app> Planner Agent, Core Mission, Expertise Areas, Guiding Principles, Output Format, Quality Standards

### Community 32 - "<app> TDD Guide Agent"
Cohesion: 0.29
Nodes (6): <app> TDD Guide Agent, Core Mission, Expertise Areas, Guiding Principles, Output Format, Quality Standards

### Community 33 - "<app> Depguard Reviewer"
Cohesion: 0.29
Nodes (6): <app> Depguard Reviewer, Core Mission, Expertise Areas, Guiding Principles, Output Format, Quality Standards

### Community 34 - "<app> Go Test Author"
Cohesion: 0.29
Nodes (6): <app> Go Test Author, Core Mission, Expertise Areas, Guiding Principles, Output Format, Quality Standards

### Community 35 - "<app> Add Handler"
Cohesion: 0.29
Nodes (6): <app> Add Handler, Core Principles, Output Format, Research References, Rules, When to Activate

### Community 36 - "<app> Add Module"
Cohesion: 0.29
Nodes (6): <app> Add Module, Core Principles, Output Format, Research References, Rules, When to Activate

### Community 37 - "<app> Claim Check skill"
Cohesion: 0.29
Nodes (6): <app> Claim Check skill, Core Principles, Output Format, Research References, Rules, When to Activate

### Community 38 - "<app> Clean-Room Rebuild skill"
Cohesion: 0.29
Nodes (6): <app> Clean-Room Rebuild skill, Core Principles, Output Format, Research References, Rules, When to Activate

### Community 39 - "<app> Corpus Retrieval skill"
Cohesion: 0.29
Nodes (6): <app> Corpus Retrieval skill, Core Principles, Output Format, Research References, Rules, When to Activate

### Community 40 - "<app> Depguard Guard"
Cohesion: 0.29
Nodes (6): <app> Depguard Guard, Core Principles, Output Format, Research References, Rules, When to Activate

### Community 41 - "<app> Diagnosing Bugs skill"
Cohesion: 0.29
Nodes (6): <app> Diagnosing Bugs skill, Core Principles, Output Format, Research References, Rules, When to Activate

### Community 42 - "<app> Domain Modeling skill"
Cohesion: 0.29
Nodes (6): <app> Domain Modeling skill, Core Principles, Output Format, Research References, Rules, When to Activate

### Community 43 - "<app> Grilling skill"
Cohesion: 0.29
Nodes (6): <app> Grilling skill, Core Principles, Output Format, Research References, Rules, When to Activate

### Community 44 - "<app> learn skill"
Cohesion: 0.29
Nodes (6): <app> learn skill, Core Principles, Output Format, Research References, Rules, When to Activate

### Community 45 - "<app> Ownership Author"
Cohesion: 0.29
Nodes (6): <app> Ownership Author, Core Principles, Output Format, Research References, Rules, When to Activate

### Community 46 - "<app> plan skill"
Cohesion: 0.29
Nodes (6): <app> plan skill, Core Principles, Output Format, Research References, Rules, When to Activate

### Community 47 - "<app> Research skill"
Cohesion: 0.29
Nodes (6): <app> Research skill, Core Principles, Output Format, Research References, Rules, When to Activate

### Community 48 - "<app> review skill"
Cohesion: 0.29
Nodes (6): <app> review skill, Core Principles, Output Format, Research References, Rules, When to Activate

### Community 49 - "<app> ship skill"
Cohesion: 0.29
Nodes (6): <app> ship skill, Core Principles, Output Format, Research References, Rules, When to Activate

### Community 50 - "<app> spec skill"
Cohesion: 0.29
Nodes (6): <app> spec skill, Core Principles, Output Format, Research References, Rules, When to Activate

### Community 51 - "<app> TDD skill"
Cohesion: 0.29
Nodes (6): <app> TDD skill, Core Principles, Output Format, Research References, Rules, When to Activate

### Community 52 - "<app> Verified Status skill"
Cohesion: 0.29
Nodes (6): <app> Verified Status skill, Core Principles, Output Format, Research References, Rules, When to Activate

### Community 53 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 54 - "build"
Cohesion: 0.53
Nodes (5): build(), main(), package_files(), Path, Files to package, relative to root, in a stable order.

### Community 56 - "BeautifulGo lints"
Cohesion: 0.40
Nodes (4): BeautifulGo lints, Copying it, The check directory, What each rule enforces

### Community 58 - "beautifulgo — agent instructions"
Cohesion: 0.50
Nodes (3): beautifulgo — agent instructions, graphify, Model routing (Claude Code + Ollama)

### Community 59 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 60 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 61 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 63 - "Runner"
Cohesion: 0.67
Nodes (3): Context, runHealth(), Runner()

### Community 64 - "guard-bash.sh"
Cohesion: 0.83
Nodes (3): has(), has_i(), guard-bash.sh script

## Knowledge Gaps
- **379 isolated node(s):** `github.com/beautifulgo/check`, `Store`, `Clock`, `$schema`, `name` (+374 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **55 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `render()` connect `check-examples.py` to `Checker`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._
- **What connects `github.com/beautifulgo/check`, `Store`, `Clock` to the rest of the system?**
  _403 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Checker` be split into smaller, more focused modules?**
  _Cohesion score 0.1020979020979021 - nodes in this community are weakly interconnected._
- **Should `CheckSkillTests` be split into smaller, more focused modules?**
  _Cohesion score 0.14675052410901468 - nodes in this community are weakly interconnected._
- **Should `write` be split into smaller, more focused modules?**
  _Cohesion score 0.07801418439716312 - nodes in this community are weakly interconnected._
- **Should `backend-go stack (digest)` be split into smaller, more focused modules?**
  _Cohesion score 0.04541062801932367 - nodes in this community are weakly interconnected._
- **Should `Order` be split into smaller, more focused modules?**
  _Cohesion score 0.08305647840531562 - nodes in this community are weakly interconnected._