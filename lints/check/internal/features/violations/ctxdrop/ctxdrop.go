// Package ctxdrop violates contextcheck: a context-aware function drops the
// context on the way down, and the callee starts a fresh one.
package ctxdrop

import (
	"context"
	"net/http"
)

// Runner accepts a context but drops it on the way down.
func Runner(ctx context.Context) {
	_ = runHealth() // want contextcheck
}

func runHealth() error {
	req, err := http.NewRequestWithContext(context.TODO(), http.MethodGet, "https://example.internal/health", nil)
	if err != nil {
		return err
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return err
	}
	_ = resp.Body.Close()
	return nil
}
