// HTTP adapter: chi route handlers, edge validation, {detail, code} envelope.
package widgets

import (
	"encoding/json"
	"errors"
	"net/http"

	"github.com/go-chi/chi/v5"

	"github.com/example/widgetsapp/internal/platform/httpx"
	"github.com/example/widgetsapp/internal/shared/apperr"
)

// Handler serves the widgets slice over HTTP.
type Handler struct {
	use *Creator
}

// NewHandler builds the slice's HTTP adapter.
func NewHandler(u *Creator) *Handler { return &Handler{use: u} }

// Create handles POST /api/v1/widgets.
func (h *Handler) Create(w http.ResponseWriter, r *http.Request) {
	var in CreateInput
	if err := json.NewDecoder(r.Body).Decode(&in); err != nil {
		httpx.WriteErr(w, http.StatusBadRequest, "invalid JSON body",
			apperr.WidgetInvalid)
		return
	}
	widget, err := h.use.Create(r.Context(), in)
	if err != nil {
		writeWidgetErr(w, err)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	_ = json.NewEncoder(w).Encode(widget)
}

// ByID handles GET /api/v1/widgets/{id}.
func (h *Handler) ByID(w http.ResponseWriter, r *http.Request) {
	widget, err := h.use.ByID(r.Context(), WidgetID(chi.URLParam(r, "id")))
	if err != nil {
		writeWidgetErr(w, err)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(widget)
}

// writeWidgetErr maps slice errors to the shared envelope.
func writeWidgetErr(w http.ResponseWriter, err error) {
	switch {
	case errors.Is(err, ErrWidgetMissing):
		httpx.WriteErr(w, http.StatusNotFound, "widget not found",
			apperr.WidgetMissing)
	case errors.Is(err, ErrInvalidSize):
		httpx.WriteErr(w, http.StatusBadRequest, "unknown size class",
			apperr.WidgetInvalid)
	default:
		httpx.WriteErr(w, http.StatusInternalServerError, "internal error",
			apperr.Internal)
	}
}