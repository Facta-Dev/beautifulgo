// Package usecaseplatform violates usecase-transport-free with a platform
// adapter type: use case and ports files depend on their own ports, never on
// platform adapters.
package usecaseplatform

import "github.com/beautifulgo/check/internal/platform/stub" // want depguard

// Hub returns the platform hub type straight into the use case's signature.
func Hub() stub.Hub {
	return stub.Hub{}
}