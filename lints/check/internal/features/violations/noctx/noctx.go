// Package noctx violates noctx: an adapter making an outgoing HTTP call
// without a context loses cancellation and deadlines.
package noctx

import "net/http"

// Fetch does an outgoing call with no context, from an adapter.
func Fetch(url string) (int, error) {
	resp, err := http.Get(url) // want noctx
	if err != nil {
		return 0, err
	}
	return resp.StatusCode, nil
}
