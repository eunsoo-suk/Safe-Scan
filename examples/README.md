# Sample analysis data

This folder powers the **Demo mode** toggle in the sidebar of the SafeScan app. When demo mode is enabled, the app loads these JSON files instead of calling the Anthropic API, so visitors can see the four analyzer outputs without supplying their own API key.

## Contents

| File                 | Purpose                                                 |
|----------------------|---------------------------------------------------------|
| `sample_image.jpg`   | The product label that the demo run was performed on.   |
| `ocr.json`           | OCR / extraction output for the sample image.           |
| `allergen.json`      | Allergens & Irritants analyzer output.                  |
| `endocrine.json`     | Endocrine Disruptors analyzer output.                   |
| `pregnancy.json`     | Pregnancy & Pediatric analyzer output.                  |
| `environmental.json` | Environmental Impact analyzer output.                   |

## Replacing the sample with your own analysis

The JSON shipped here is a hand-written illustration based on the product's label, not a captured run of the live API. If you want the demo to reflect a real analysis you've performed:

1. Run the app with your own Anthropic API key in the sidebar.
2. Disable Demo mode (or leave it off).
3. For each of the four analyzers, paste the ingredient list and click **Run analysis**.
4. The full response (including `_cache_stats`) is what you want — copy it from the **API usage statistics** expander or capture it from `st.session_state["result_<name>"]`.
5. Replace the corresponding file in this folder, keeping the same filename.
6. For the OCR sample, upload your label image, click **Extract ingredients**, and replace `ocr.json` and `sample_image.jpg` together.

The schema each file follows is documented in `backend/analyzers/base.py` (`UNIFIED_SCHEMA_DOC`). The `_sample_meta` field at the top of each analyzer JSON is ignored by the renderer; you can keep it, edit it, or remove it.
