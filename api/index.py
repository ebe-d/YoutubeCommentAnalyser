# api/index.py — Vercel serverless entry point
# Vercel imports `app` from this file and routes all /api/* requests to it.
from main import app  # noqa: F401
