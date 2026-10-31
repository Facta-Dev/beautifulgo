// Package errwrap violates errorlint: %s flattens the error into a string and
// breaks errors.Is/As on the wrapped sentinel.
package errwrap

import (
	"errors"
	"fmt"
)

// ErrLoad is the sentinel this file flattens.
var ErrLoad = errors.New("load failed")

// Wrap flattens with %s, losing the chain.
func Wrap(err error) error {
	return fmt.Errorf("load config: %s", err) // want errorlint
}

// WithChain wraps correctly, and stays quiet.
func WithChain(err error) error {
	return fmt.Errorf("load config: %w", err)
}
