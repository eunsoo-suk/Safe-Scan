"""DEPRECATED — replaced by the modular analyzers in backend/analyzers/.

This file is retained as an empty stub only because the MCP Filesystem
interface has no delete capability. Safe to remove manually.

Old responsibility: single-endpoint carcinogenicity analysis.
New equivalents: backend/analyzers/{allergen,endocrine,pregnancy,environmental}.py
"""
raise ImportError(
    "backend.analyzer is deprecated. Use backend.analyzers.{allergen,endocrine,"
    "pregnancy,environmental} instead."
)
