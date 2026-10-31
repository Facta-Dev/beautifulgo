// Slice wiring: the composition root calls Register once.
package widgets

import (
	"net/http"
	"time"
)

// Deps carries the slice's collaborators; the root builds them from concrete
// adapters.
type Deps struct {
	Store WidgetStore
	Now   func() time.Time
}

// Register mounts the slice's routes on the root's mux.
func Register(mux *http.ServeMux, d Deps) {
    h := NewHandler(NewCreator(d.Store, d.Now))
    mux.HandleFunc("POST /api/v1/widgets", h.Create)
    mux.HandleFunc("GET /api/v1/widgets/{id}", h.ByID)
}