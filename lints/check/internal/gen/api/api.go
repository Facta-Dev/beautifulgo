// Package api is the wire-model stub standing in for internal/gen/api: the
// {detail, code} envelope types the HTTP adapter encodes and decodes. Wire
// types stop at http.go — depguard's usecase-transport-free rule denies the
// import from use case and ports files.
package api

// Error is the wire error envelope.
type Error struct {
	Detail string `json:"detail"`
	Code   string `json:"code"`
}
