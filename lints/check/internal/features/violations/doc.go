// Package violations holds one deliberately violating file per rule in
// lints/.golangci.yml, so every rule in the config is proven to fire. Each
// violation sits on a line ending with a want marker naming its linter;
// scripts/check-lints.sh fails if a marker stays quiet, if anything unmarked
// reports, if the clean slice reports, or if this table drifts from the
// config's rule names.
//
// Table: rule -> linter -> file. Keep in sync with lints/.golangci.yml.
//
//	| rule                   | linter       | violation                              |
//	| ---------------------- | ------------ | -------------------------------------- |
//	| domain-pure            | depguard     | violations/domainpgx/domain.go         |
//	| domain-pure            | depguard     | violations/domainsql/domain.go         |
//	| domain-pure            | depguard     | violations/domainhttp/domain.go        |
//	| domain-pure            | depguard     | violations/domainplatform/domain.go    |
//	| domain-pure            | depguard     | violations/domainsibling/domain.go     |
//	| usecase-transport-free | depguard     | violations/usecasepgx/usecase.go       |
//	| usecase-transport-free | depguard     | violations/usecasegenapi/usecase.go    |
//	| usecase-transport-free | depguard     | violations/usecaseplatform/usecase.go  |
//	| slice-isolation        | depguard     | violations/siblingimport/usecase.go    |
//	| platform-no-features   | depguard     | internal/platform/roguehub/roguehub.go |
//	| -                      | errorlint    | violations/errwrap/errwrap.go          |
//	| -                      | errorlint    | violations/errassert/errassert.go      |
//	| -                      | errname      | violations/errname/errname.go          |
//	| -                      | noctx        | violations/noctx/noctx.go              |
//	| -                      | errcheck     | violations/errcheck/errcheck.go        |
//	| -                      | contextcheck | violations/ctxdrop/ctxdrop.go          |
package violations
