// Package domainplatform violates domain purity with a platform adapter type.
package domainplatform

import "github.com/beautifulgo/check/internal/platform/stub" // want depguard

// Hub is the repo stub hub, straight into the domain.
type Hub = stub.Hub
