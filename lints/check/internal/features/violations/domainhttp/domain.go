// Package domainhttp violates domain purity with the transport layer.
package domainhttp

import "net/http" // want depguard

// Status builds HTTP status text the domain has no business knowing.
func Status(code int) string {
	return http.StatusText(code)
}
