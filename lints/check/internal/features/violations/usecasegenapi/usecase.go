// Package usecasegenapi violates usecase-transport-free with a wire type: gen/api
// models stop at http.go.
package usecasegenapi

import "github.com/beautifulgo/check/internal/gen/api" // want depguard

// Shape returns the wire envelope the HTTP adapter should own.
func Shape() api.Error {
	return api.Error{Code: "INTERNAL_ERROR"}
}
