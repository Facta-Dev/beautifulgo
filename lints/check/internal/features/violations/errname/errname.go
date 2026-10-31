// Package errname violates errname: sentinels are Err* and error types are
// *Error; ErrorFoo is neither.
package errname

import "errors"

// ErrorFoo is a sentinel with the wrong prefix.
var ErrorFoo = errors.New("bad thing") // want errname
