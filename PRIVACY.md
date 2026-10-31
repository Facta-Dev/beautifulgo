# Privacy policy

Beautiful Go is a set of agent skills: Markdown instructions and reference text that
your coding agent reads. It applies to the Claude Code plugin, the ChatGPT / Codex
plugin, and copies installed by hand.

- **It collects no data.** The skills contain no code that runs on install, no
  analytics, and no telemetry. The author receives nothing about you, your code, or how
  you use the skills.
- **It makes no network requests.** The skills do not contact any server, including the
  author's.
- **Your agent may run local tools.** When a Go toolchain is installed, the skills ask
  your agent to run `gofmt`, `go vet`, `golangci-lint run`, `go test`, and SQL tooling
  such as `sqlc` and `golang-migrate` in your project. These run on your computer under your
  agent's normal permissions. Go commands can download the modules your project depends
  on, as they always do.
- **Your agent's provider handles your conversations.** Whatever you share with Claude,
  ChatGPT, Codex, or another agent is covered by that provider's privacy policy, not
  this one.

Questions go to [GitHub issues](https://github.com/Facta-Dev/beautifulgo/issues).
This policy changes only through commits to this file, which keep its full history.