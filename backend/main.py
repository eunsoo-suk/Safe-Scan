"""DEPRECATED — the FastAPI service layer is no longer used.

SafeScan now runs as a single Streamlit application (`frontend/app.py`),
which imports the analyzer modules directly. This removes the need for a
separate HTTP service and allows the whole app to be deployed as one
process (e.g. Streamlit Community Cloud).

The analyzer modules in `backend/analyzers/` and the OCR module in
`backend/ocr.py` remain the canonical implementation; only this HTTP
entrypoint has been retired.
"""
raise ImportError(
    "backend.main is deprecated. The HTTP layer has been removed. "
    "Run `streamlit run frontend/app.py` instead — the analyzers and OCR "
    "are imported directly."
)
