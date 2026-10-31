// Package siblingimport violates slice isolation: route composition happens in
// cmd/api, not use case to use case.
package siblingimport

import "github.com/beautifulgo/check/internal/features/widgets" // want depguard

// Load reaches sideways into the widgets slice instead of through a port.
func Load() widgets.Widget {
	return widgets.Widget{Name: "borrowed"}
}
