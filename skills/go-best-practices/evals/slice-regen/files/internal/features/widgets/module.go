// Slice wiring: the composition root calls Register once.
package widgets

import (
	"time"

	"github.com/go-chi/chi/v5"
)

// Deps carries the slice's collaborators; the root builds them from concrete
// adapters.
type Deps struct {
	Store WidgetStore
	Now   func() time.Time
}

// Register mounts the slice's routes on the root's chi router.
func Register(r chi.Router, d Deps) {
	h := NewHandler(NewCreator(d.Store, d.Now))
	r.Post("/api/v1/widgets", h.Create)
	r.Get("/api/v1/widgets/{id}", h.ByID)
}