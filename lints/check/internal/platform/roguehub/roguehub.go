// Package roguehub violates platform-no-features: platform code reading a
// feature slice directly instead of serving it through a port.
package roguehub

import "github.com/beautifulgo/check/internal/features/widgets" // want depguard

// Peek reads the widgets slice's domain type from platform code.
func Peek() widgets.Widget {
	return widgets.Widget{Name: "rogue"}
}
