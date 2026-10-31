// Package errassert violates errorlint: a type assertion on an error fails on
// wrapped chains; use errors.As.
package errassert

import "io/fs"

// IsMissing type-asserts the error, which fails on wrapped errors.
func IsMissing(err error) bool {
	_, ok := err.(*fs.PathError) // want errorlint
	return ok
}
