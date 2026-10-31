# Google Go Style Guide (digest)

Source: the *Google Go Style Guide*
(https://google.github.io/styleguide/go/index), including the decisions from its
Best-practices and Decisions sections that reviewers cite most. Distilled from
the published guide; nothing quoted verbatim. Read this when the question is
judgment rather than syntax: when to abstract, how much to name, what makes a
package good, when errors deserve a wrapper type, when a function is too big.
~45 rules, paraphrased faithfully, with a link back.

## Core principles

1. **Readability is the point.** Go code is read and edited far more than it is
   written; optimize for the reader. When two rules conflict, the one producing
   clearer code wins.
2. **Clarity over cleverness.** Code that works but must be decoded is a style
   bug. If a reviewer asks "why", the answer should be in the code or a comment,
   not in the author's head.
3. **Let tools carry consistency.** gofmt and linters keep argument out of
   review so review can discuss design.
4. **The guide's triad: usable, idiomatic, efficient** — in that order.

## Naming

5. **Names carry context.** The package name is the first word of every
   declaration inside it, so a name never repeats it (`cache.Read`, not
   `cache.CacheRead`). Package name plus identifier should read as a sentence.
6. **A name's scope determines its length**: narrow scope, short name; wide
   scope (exported, package-level), descriptive name.
7. **One receiver name per type, for the type's life** — usually the type's
   first letter. Switching between `w` and `widget` for `(w Widget)` breaks
   scan-reading.
8. **Don't repeat obvious context**: `cfg.Server.Timeout`, not
   `cfg.Server.ServerTimeout`.
9. **Words in a name must be in the codebase's vocabulary**; don't invent
   jargon ahead of the domain.

## Package design

10. **A package solves one problem.** The guide's line: solve your problem with
    one package or with several — never with 1.5. Half-shared packages are the
    worst of both worlds.
11. **Name the package by what it provides, not what it contains** (`net/http`
    provides HTTP). Every exported identifier reads as `<pkg>.<Name>`, so names
    are chosen so that combination reads well.
12. **Refactor toward a real boundary when one blurs**: if a package needs
    internal-visibility tricks or "import this not that" doc notices, split it.
13. **A package is good when**: its parts change together, do similar jobs, stay
    out of each other's business, and form one logical thing to test.
14. **`internal/` is compiler-enforced privacy**; do not leak concretions from
    it into exported signatures — the consumers can't make the promise hold.
15. **No define-by-negation packages**: `util`, `common`, `base`, `misc` are
    named after what they are not. A helper is either a mechanism (a named
    package) or a domain concept (the owning package). Mirrors SKILL.md §9.
16. **Package-level mutable state is the main readability hazard**; dependencies
    flow through constructors and parameters, not globals.
17. **Dependency direction must be consistent and toward the stable.** In the
    hexagonal template this is law (SKILL.md §2); off-stack it is taste.

## Functions and design

18. **Functions do one thing at one level of abstraction.** A flag that switches
    modes is two functions — the bool-parameter rule from the clarity side.
19. **A function's size question**: can you find the core statement of what it
    does within the first few lines? If not, split or restructure.
20. **Flat is better than nested.** Early returns and guard clauses over
    arrow-shaped code; an `else` after a `return` is the classic signal.
21. **Handle errors in place**: wrap once with a verb phrase and return. Don't
    re-wrap identically, don't log-and-return, don't build a plumbing layer of
    nested wrappers.
22. **Wrapping vs sentinel is decided by the caller's needs**: does the caller
    need to *match* (sentinel or typed error), *display* (wrap chain), or just
    *report* (add context)? Choose per caller, not per taste.

## Error handling decisions

23. **Every error carries what its caller needs.** Add context with `%w` when
    the message must say where it happened, not to restate.
24. **`panic` only for programmer error and Must-style helpers on compile-time
    constants** (`regexp.MustCompile`). Never on runtime input. Matches SKILL.md
    §5 and the wiki digest.
25. **Never discard errors** (`_ = f()`); handle, wrap, or return — explicit is
    the contract. errcheck encodes this.
26. **Match errors structurally** (`errors.Is`/`errors.As`), never by string.
27. **No opaque central error plumbing** — no global handler that silently
    rewrites errors; wrap at the point where context is real.

## Types and interfaces

28. **Interfaces belong to the consumer.** Return concrete types; receive
    interfaces when a small interface or a test seam is genuinely needed. The
    implementer need not define or import the interface — Go satisfies
    structurally. This is the seed of the hexagonal ports rule (SKILL.md §2).
29. **One-implementation interfaces are a future lie.** The guide's question:
    does a second real implementation exist, or a consumer that declared the
    interface as a seam? If no, use the concrete type.
30. **Embedding is composition, not subtyping**: embed to reuse
    part-implementations; promoted fields are still state the type owns.
31. **Methods on the type that owns the data**; free functions when ownership is
    unclear. No `Manager`/`Service` god objects owning everything.
32. **No define-by-negation types** either — same taste as package names.

## Concurrency

33. **`ctx` is the first parameter, named `ctx`, and never stored in a
    struct.** The edge creates it, the middle passes it, the leaf observes
    cancellation.
34. **Every goroutine has an owner with a way to observe and stop it.** One of
    the guide's named concurrency hazards; the wiki says the same in stronger
    words.
35. **Channels for ownership transfer, mutexes for state** — the guide's
    heuristic, same as SKILL.md §7.
36. **`sync.Once` for shared one-time setup; `sync.OnceValue` (Go 1.21+) for the
    lazy-single-value case**, replacing the Once-plus-closure dance;
    `sync.OnceFunc` for the error-returning variant.
37. **No busy-wait and no `time.Sleep` coordination**; channels, WaitGroups, and
    context are the coordination primitives.

## Documentation

38. **Every exported symbol has a doc comment beginning with its name**:
    `// ParseCode converts ...` over `func ParseCode`. Complete sentence, third
    person ("Reports whether...").
39. **Doc comments describe the contract, not the implementation**: side
    effects, preconditions, thread-safety, failure modes in prose.
40. **Comments explain why, not what** — the code shows the what.
41. **Package comments live in one file** (doc.go when the package warrants
    it); deprecations use the exact `// Deprecated:` marker so tooling sees
    them.

## Application vs library code

42. **Application code favors simplicity**: concrete types, `string`/`int64`
    parameters, plain error values. Library-grade generality is for consumers
    you don't control.
43. **The strongest reason to abstract is a second implementation or a second
    consumer**; anything else is speculative generality. On the stack, the one
    sanctioned exception is the consumer-declared port in `ports.go`.
44. **No dead parameters or dead options** — a parameter added "for the future"
    is debt with no return; add it when the consumer exists.
45. **When this guide and the backend-go handbook disagree**, the handbook wins
    inside `internal/features/` (six files, ports in `ports.go`, the slice
    topology); this guide governs non-stack Go.

Full text: https://google.github.io/styleguide/go/index