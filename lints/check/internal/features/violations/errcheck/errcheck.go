// Package errcheck violates errcheck: an error return value dropped on the
// floor is a lost failure.
package errcheck

// janitor stands in for any cleanup type whose method reports an error.
type janitor struct{}

// Sweep stands in for any cleanup call that reports an error.
func (janitor) Sweep() error { return nil }

// Tidy drops the error on the floor.
func Tidy() {
	janitor{}.Sweep() // want errcheck
}
