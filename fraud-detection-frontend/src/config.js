// Central place for the backend URL.
// Vite exposes any variable prefixed with VITE_ from your .env files
// via import.meta.env. If it's not set (e.g. local dev with no .env),
// we fall back to your local FastAPI server.

export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";