"""DEPRECATED — replaced by backend/ocr.py + the modular analyzers.

This file is retained as an empty stub only because the MCP Filesystem
interface has no delete capability. Safe to remove manually.

Old responsibility: image upload → vision OCR → genotoxicity binary classification (single pass).
New equivalents:
  - Image → ingredient text:  backend/ocr.py
  - Safety classification:    backend/analyzers/{allergen,endocrine,pregnancy,environmental}.py
"""
raise ImportError(
    "backend.genotoxicity is deprecated. Use backend.ocr.extract_ingredients "
    "to convert an image to ingredient text, then route the text through the "
    "appropriate analyzer in backend.analyzers."
)
