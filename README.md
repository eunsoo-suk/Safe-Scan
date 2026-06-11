<div align="center">

# SafeScan

**Consumer Product Ingredient Safety Analyzer**

Four independent risk lenses across cosmetics, personal care, household, and food, powered by Claude Sonnet 4.6 and grounded in regulatory and clinical literature.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Claude](https://img.shields.io/badge/Claude-Sonnet%204.6-D97757?logo=anthropic&logoColor=white)](https://anthropic.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## Overview

SafeScan reads an ingredient list from any consumer product — cosmetic, personal care, household, or food — and returns four independent safety assessments grounded in published regulatory and clinical references. A label-scan utility extracts ingredients from a photo once, so vision OCR runs a single time per product before driving multiple analyses against the same text.

Consumer product labels list ingredients in INCI names and food-additive codes that most people cannot interpret. Existing apps (Yuka, Think Dirty, EWG Skin Deep) rely on opaque scoring rubrics. SafeScan instead exposes which regulatory or clinical reference drives each flag, gives per-ingredient transparency, and provides four orthogonal lenses so users see context-dependent risk — an ingredient that is environmentally problematic but pediatrically safe is not collapsed into a single score.

---

## Modules

| Module | Focus | Key references |
|---|---|---|
| Label Scan | Vision-based ingredient extraction (one call, four analyses) | Claude Sonnet 4.6 vision |
| Allergens & Irritants | Contact allergens, sensitizers, irritants, food allergens | EU 1223/2009 Annex III, FDA FALCPA + FASTER Act, EU 1169/2011 Annex II, NACDG, ACDS Allergen of the Year |
| Endocrine Disruptors | Estrogenic, anti-androgenic, thyroid-active substances | EU 2018/605, EPA EDSP, Endocrine Society Scientific Statement, EFSA, pesticide residue data |
| Pregnancy & Pediatric | Teratogens, lactation, infant/child restrictions, dietary risks | FDA PLLR, ACOG, AAP, FDA/EPA fish advisory, CDC listeriosis prevention |
| Environmental Impact | Aquatic toxicity, reefs, persistence, microplastics, deforestation, carbon | NOAA reef guidance, Hawaii Act 104, EU REACH PBT/vPvB, EU 2023/2055, RSPO, Monterey Bay Seafood Watch |

All analyzers return the same unified JSON schema, so the frontend renders all four with a single component.

---

## Workflow

### 1. Upload a label and extract the ingredient list

The Label Scan tab accepts any photo of a packaging panel. A single Claude vision call returns a normalized, INCI-compliant ingredient list along with metadata (confidence, language, product type). Allergen disclosure statements (`CONTAINS: ...`) are surfaced separately. The extracted text is editable before being passed to any analyzer.

<p align="center">
  <img src="docs/images/label_scan.png" alt="Label Scan and extracted ingredients" width="900"/>
</p>

### 2. Run any of the four analyzers

Each analyzer reads the same text and produces a structured assessment with an overall verdict, key concerns, per-ingredient findings, and (where relevant) safer alternatives.

**Allergens & Irritants**

<p align="center">
  <img src="docs/images/allergen_result.png" alt="Allergens result" width="900"/>
</p>

**Endocrine Disruptors**

<p align="center">
  <img src="docs/images/endocrine_result.png" alt="Endocrine result" width="900"/>
</p>

**Pregnancy & Pediatric**

<p align="center">
  <img src="docs/images/pregnancy_result.png" alt="Pregnancy result" width="900"/>
</p>

**Environmental Impact**

<p align="center">
  <img src="docs/images/environmental_result.png" alt="Environmental result" width="900"/>
</p>

---

## Architecture

```
                ┌──────────────────────────────────────┐
                │  Streamlit app (frontend/app.py)     │
                │   - Sidebar: BYOK + Demo toggle      │
                │   - 5 tabs (Label Scan + 4 analyzers)│
                └─────────────────┬────────────────────┘
                                  │  direct function call
                ┌─────────────────▼────────────────────┐
                │  backend/                            │
                │   analyzers/                         │
                │    base.py        (Claude client)    │
                │    allergen.py    endocrine.py       │
                │    pregnancy.py   environmental.py   │
                │   ocr.py          (vision extract)   │
                └─────────────────┬────────────────────┘
                                  │
                          ┌───────▼────────┐
                          │ Anthropic API  │
                          │ Claude Sonnet  │
                          └────────────────┘
```

### Design decisions

- **Single-process Streamlit.** Earlier iterations had a separate FastAPI service. It was removed because Streamlit Community Cloud deploys in one click, there is no CORS overhead, and the analyzers can be imported as plain Python modules.
- **One OCR call, four analyses.** The user reviews and edits the extracted text once, then runs any subset of analyzers against it. This reduces vision API calls by 75% versus re-extracting per analyzer.
- **Unified JSON schema across analyzers.** The frontend renders all four with a single component; adding a new analyzer is one file plus one tab.
- **Prompt caching.** Each analyzer's domain-expert system prompt is well above the 1024-token caching threshold. Repeated analyses in the same session hit the ephemeral prompt cache for lower cost and latency.
- **Bring Your Own Key (BYOK).** Hosting a free public demo would mean the operator pays for every visitor's API calls. BYOK shifts the few-cents cost to the user and removes rate limits.
- **Demo mode.** Visitors without a key still see exactly what the app produces, populated from `examples/*.json` and a bundled product photo.

---

## Usage modes

### Live mode (BYOK)
1. Sign up at [console.anthropic.com](https://console.anthropic.com)
2. Settings → API Keys → Create Key
3. Add a small amount of credit (most analyses cost a few cents)
4. Paste the key into the sidebar when the app loads

The key lives only in `st.session_state` for the current browser tab. Refreshing clears it. It is never logged or stored server-side.

### Demo mode
Toggle Demo mode in the sidebar. The app loads a bundled product label photo, a pre-computed OCR extraction (`examples/ocr.json`), and pre-computed assessments for all four analyzers (`examples/*.json`). No API key required, no Anthropic API calls are made.

---

## Local setup

**Requirements:** Python 3.11+, an Anthropic API key (entered at runtime).

```powershell
python -m venv venv
.\venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
streamlit run frontend/app.py
```

The app opens at `http://localhost:8501`. Paste your API key into the sidebar or enable Demo mode.

If you put `ANTHROPIC_API_KEY=sk-ant-...` in a local `.env`, the sidebar will be pre-filled. The `.env` file is gitignored. Do not use this pattern when deploying to Streamlit Community Cloud — the deployed app is BYOK by design.

---

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub.
2. Sign in at [share.streamlit.io](https://share.streamlit.io).
3. New app → select `eunsoo-suk/Safe-Scan`.
4. Main file path: `frontend/app.py`.
5. Python version: 3.11+.
6. Do not add any secret named `ANTHROPIC_API_KEY`. Leaving it empty is what makes the demo BYOK.
7. Deploy.

Streamlit Cloud installs from `requirements.txt`, runs `streamlit run frontend/app.py`, and serves the app at `https://<your-app-name>.streamlit.app`. Visitors enter their own key in the sidebar.

---

## Project layout

```
Safe Scan/
├── frontend/
│   └── app.py                     Single-file Streamlit application
├── backend/
│   ├── analyzers/
│   │   ├── base.py                Shared Claude client, JSON parsing, prompt caching
│   │   ├── allergen.py            Allergens & irritants (topical + food)
│   │   ├── endocrine.py           Endocrine disruptors (cosmetic + dietary)
│   │   ├── pregnancy.py           Pregnancy & pediatric (topical + dietary)
│   │   └── environmental.py       Environmental impact (aquatic + climate)
│   ├── ocr.py                     Vision-based ingredient extraction
│   └── main.py                    Deprecated, kept as stub
├── examples/                      Pre-computed JSON samples for Demo mode
├── docs/images/                   README screenshots
├── sample image.jpg               Bundled product label for Demo mode
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Tech stack

| Layer | Choice |
|---|---|
| LLM | Claude Sonnet 4.6 (Anthropic API) |
| App framework | Streamlit (single-process, BYOK) |
| Vision OCR | Claude Sonnet 4.6 vision capability |
| Caching | Anthropic ephemeral prompt cache |
| Language | Python 3.11+ |

---

## Development history

The project went through three iterations:

1. **v1.** Single-purpose carcinogenicity analyzer with a FastAPI backend and a separate React-style frontend. Removed because the surface area was too narrow for a single safety lens, and CORS and deployment friction made the demo unfriendly.
2. **v2.** Two analyzers (carcinogenicity + genotoxicity), still split across FastAPI and frontend. Removed because the two lenses overlapped heavily and operating two services for a hackathon-scale app was overkill.
3. **v2.1 (current).** Restructured to four orthogonal analyzers (allergens, endocrine, pregnancy, environmental) covering both topical and dietary exposures. Frontend and backend merged into a single Streamlit process. Vision OCR factored into its own utility tab so one extraction drives multiple analyses.

Throughout, the goal was to keep regulatory provenance visible: every finding lets the user audit which standard or clinical reference drove the flag. The system prompts in `backend/analyzers/*.py` encode those references explicitly.

---

## Responsible-use notes

SafeScan is informational. It is not a medical, legal, or regulatory product. The UI footer states this.

The analyzers reason from the LLM's training data and the regulatory references encoded in each system prompt. They do not query live regulatory databases at inference time, so assessments reflect the state of the literature up to the model's knowledge cutoff. The model can be wrong. Two safeguards are in place: ingredient-level transparency (each finding shows its claimed classification and concern, so the user can audit it), and an explicit disclaimer in the UI.

No ingredient list or image is persisted by this application. All inputs live only in process memory while the session is active. API keys are read from the sidebar `st.session_state` and never logged or stored.

---

## License

MIT.

---

<div align="center">

Built by [Eunsoo Suk](https://github.com/eunsoo-suk) · MS Applied Machine Learning, University of Maryland

</div>
