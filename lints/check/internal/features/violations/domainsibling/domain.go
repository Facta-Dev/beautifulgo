// Package domainsibling violates domain purity and slice isolation together: a
// domain file reaching sideways into another slice's package.
package domainsibling

import "github.com/beautifulgo/check/internal/features/widgets" // want depguard

// Name reads another slice's domain type directly.
func Name(w widgets.Widget) string {
	return w.Name
}
