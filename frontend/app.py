"""SafeScan — single-file Streamlit application (BYOK + Demo mode).

Five tabs:
  1. Label Scan           — OCR utility (vision)
  2. Allergens & Irritants
  3. Endocrine Disruptors
  4. Pregnancy & Pediatric
  5. Environmental Impact

The analyzer and OCR modules are imported directly from `backend/`; there
is no separate HTTP service. The user supplies their own Anthropic API
key in the sidebar (Bring Your Own Key).

Demo mode loads pre-computed sample results from `examples/*.json` so
visitors without an API key can still see what the app produces.
"""
import json
import os
import sys
from pathlib import Path

import streamlit as st

# Make `backend.*` importable when Streamlit runs from any directory.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_EXAMPLES_DIR = _PROJECT_ROOT / "examples"

from backend.analyzers import allergen, endocrine, pregnancy, environmental
from backend.ocr import extract_ingredients

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ─────────────────────────────────────────────────────────────────────────────
# Visual constants
# ─────────────────────────────────────────────────────────────────────────────
RISK_COLORS = {
    "HIGH":    "#B91C1C",
    "MEDIUM":  "#B45309",
    "LOW":     "#A16207",
    "MINIMAL": "#15803D",
}
RISK_BG = {
    "HIGH":    "#FEF2F2",
    "MEDIUM":  "#FFFBEB",
    "LOW":     "#FEFCE8",
    "MINIMAL": "#F0FDF4",
}
RISK_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "MINIMAL": 3}

ANALYZERS = {
    "allergen": {
        "tab_label":   "Allergens & Irritants",
        "fn":          allergen.analyze,
        "accent":      "#7F1D1D",
        "title":       "Allergens & Irritation",
        "description": (
            "Identifies contact allergens, sensitizers, irritants, and food allergens. "
            "References EU Cosmetics Regulation 1223/2009 Annex III, FDA Top 9 food "
            "allergens (FALCPA + FASTER Act), EU Food Information Regulation 1169/2011 "
            "Annex II, NACDG patch-test series, and ACDS Allergen of the Year designations."
        ),
        "example": (
            "Water, Sodium Laureth Sulfate, Cocamidopropyl Betaine, "
            "Methylisothiazolinone, Linalool, Limonene, Citronellol, "
            "DMDM Hydantoin, Fragrance, Citric Acid"
        ),
    },
    "endocrine": {
        "tab_label":   "Endocrine Disruptors",
        "fn":          endocrine.analyze,
        "accent":      "#581C87",
        "title":       "Endocrine-Disrupting Activity",
        "description": (
            "Screens for ingredients with established or suspected endocrine activity "
            "(estrogenic, anti-androgenic, thyroid). References EU Regulation 2018/605 "
            "EDC criteria, EPA EDSP, the Endocrine Society Scientific Statement, EFSA "
            "food-contact opinions, and pesticide residue monitoring."
        ),
        "example": (
            "Water, Oxybenzone, Octinoxate, Homosalate, Propylparaben, "
            "Butylparaben, Diethyl Phthalate, Cyclopentasiloxane, Glycerin"
        ),
    },
    "pregnancy": {
        "tab_label":   "Pregnancy & Pediatric",
        "fn":          pregnancy.analyze,
        "accent":      "#92400E",
        "title":       "Pregnancy, Breastfeeding & Pediatric Safety",
        "description": (
            "Flags ingredients of concern during pregnancy, lactation, infancy, and "
            "early childhood across cosmetic AND dietary exposures. References FDA "
            "PLLR, ACOG and AAP guidance, FDA/EPA fish consumption advisory, and CDC "
            "listeriosis/toxoplasmosis prevention."
        ),
        "example": (
            "Water, Retinol, Salicylic Acid, Hydroquinone, Niacinamide, "
            "Hyaluronic Acid, Lavender Oil, Phenoxyethanol, Glycerin"
        ),
    },
    "environmental": {
        "tab_label":   "Environmental Impact",
        "fn":          environmental.analyze,
        "accent":      "#134E4A",
        "title":       "Environmental & Climate Impact",
        "description": (
            "Evaluates aquatic toxicity, coral reef impact, persistence, "
            "bioaccumulation, microplastic content, deforestation, overfishing, and "
            "carbon footprint. References NOAA reef-safe guidance, Hawaii Act 104, EU "
            "REACH PBT/vPvB criteria, EU 2023/2055 microplastic restriction, RSPO, and "
            "Monterey Bay Aquarium Seafood Watch."
        ),
        "example": (
            "Water, Oxybenzone, Octinoxate, Polyethylene, Cyclopentasiloxane, "
            "Triclosan, Galaxolide, BHT, Sodium Laureth Sulfate, Glycerin"
        ),
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Sample-data loading (Demo mode)
# ─────────────────────────────────────────────────────────────────────────────
def _load_sample_json(filename: str) -> dict | None:
    """Read examples/<filename> and return parsed JSON, or None if missing."""
    path = _EXAMPLES_DIR / filename
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_demo_into_session():
    """Populate every input and result slot with pre-computed sample data."""
    ocr_data = _load_sample_json("ocr.json")
    if ocr_data:
        st.session_state["extracted_text"] = ocr_data.get("comma_separated", "")
        st.session_state["extracted_meta"] = ocr_data
        # Pre-fill every analyzer input with the same extracted text.
        for name in ANALYZERS:
            st.session_state[f"input_{name}"] = ocr_data.get("comma_separated", "")
    for name in ANALYZERS:
        result = _load_sample_json(f"{name}.json")
        if result is not None:
            st.session_state[f"result_{name}"] = result


def _clear_demo_from_session():
    """Reset all demo-populated fields without touching the user-supplied API key."""
    st.session_state["extracted_text"] = ""
    st.session_state["extracted_meta"] = None
    for name in ANALYZERS:
        st.session_state[f"input_{name}"] = ""
        st.session_state[f"result_{name}"] = None


# ─────────────────────────────────────────────────────────────────────────────
# Page setup
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="SafeScan", page_icon=None, layout="wide")

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1200px; }

    .hero {
        background: #111827;
        color: #F9FAFB;
        padding: 1.6rem 1.8rem;
        border-radius: 4px;
        margin-bottom: 1.25rem;
        border-left: 3px solid #6B7280;
    }
    .hero .brand {
        font-size: 0.72rem; font-weight: 600; letter-spacing: 0.18em;
        text-transform: uppercase; color: #9CA3AF; margin-bottom: 0.35rem;
    }
    .hero h1 {
        margin: 0; font-size: 1.85rem; font-weight: 700;
        letter-spacing: -0.015em; color: #F9FAFB;
    }
    .hero p {
        margin: 0.5rem 0 0; font-size: 0.92rem; color: #D1D5DB;
        max-width: 720px; line-height: 1.5;
    }

    .tab-header {
        padding: 1rem 1.2rem; border-radius: 4px;
        margin-bottom: 1.1rem; color: white;
    }
    .tab-header .module {
        font-size: 0.7rem; font-weight: 600; letter-spacing: 0.16em;
        text-transform: uppercase; opacity: 0.78; margin-bottom: 0.3rem;
    }
    .tab-header h2 {
        margin: 0; font-size: 1.2rem; font-weight: 700; letter-spacing: -0.01em;
    }
    .tab-header p {
        margin: 0.45rem 0 0; font-size: 0.88rem; line-height: 1.5;
        opacity: 0.95; max-width: 880px;
    }

    .assessment {
        padding: 1.1rem 1.3rem; border-radius: 4px;
        margin-bottom: 1.2rem; border-left: 4px solid;
    }
    .assessment .label {
        font-size: 0.7rem; font-weight: 600; letter-spacing: 0.18em;
        text-transform: uppercase; color: #6B7280;
    }
    .assessment .verdict {
        font-size: 1.35rem; font-weight: 700;
        margin-top: 0.2rem; letter-spacing: -0.01em;
    }
    .assessment .summary {
        margin-top: 0.6rem; font-size: 0.93rem; color: #1F2937; line-height: 1.55;
    }
    .assessment .meta {
        margin-top: 0.7rem; font-size: 0.78rem; color: #6B7280; letter-spacing: 0.02em;
    }

    .chip {
        display: inline-block; padding: 0.22rem 0.65rem;
        margin: 0.15rem 0.2rem 0.15rem 0; border-radius: 3px;
        background: #F3F4F6; color: #374151;
        font-size: 0.8rem; font-weight: 500; border: 1px solid #E5E7EB;
    }
    .chip.warn { background: #FEF3C7; color: #92400E; border-color: #FCD34D; }

    .section-h {
        font-size: 0.78rem; font-weight: 700; letter-spacing: 0.14em;
        text-transform: uppercase; color: #4B5563;
        margin: 1.1rem 0 0.5rem;
    }

    .key-status-ok {
        background: #ECFDF5; color: #065F46; border-left: 3px solid #10B981;
        padding: 0.5rem 0.7rem; border-radius: 3px; font-size: 0.85rem;
    }
    .key-status-missing {
        background: #FEF2F2; color: #991B1B; border-left: 3px solid #EF4444;
        padding: 0.5rem 0.7rem; border-radius: 3px; font-size: 0.85rem;
    }
    .key-status-demo {
        background: #EFF6FF; color: #1E3A8A; border-left: 3px solid #3B82F6;
        padding: 0.5rem 0.7rem; border-radius: 3px; font-size: 0.85rem;
    }

    .demo-badge {
        display: inline-block;
        background: #DBEAFE;
        color: #1E3A8A;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        padding: 0.18rem 0.55rem;
        border-radius: 3px;
        margin-left: 0.6rem;
        vertical-align: middle;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Session state init
# ─────────────────────────────────────────────────────────────────────────────
# Sidebar key starts empty by default. Each visitor (and the developer
# running locally) supplies their own key per session. A local .env is no
# longer read, so deploying or sharing the app cannot leak any key.
st.session_state.setdefault("anthropic_api_key", "")
st.session_state.setdefault("extracted_text", "")
st.session_state.setdefault("extracted_meta", None)
st.session_state.setdefault("demo_mode", False)
st.session_state.setdefault("_demo_mode_prev", False)
for key in ANALYZERS:
    st.session_state.setdefault(f"input_{key}", "")
    st.session_state.setdefault(f"result_{key}", None)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — API key (BYOK) + Demo mode
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Setup")

    api_key_input = st.text_input(
        "Anthropic API key",
        value=st.session_state["anthropic_api_key"],
        type="password",
        placeholder="sk-ant-api03-...",
        help=(
            "Your key stays in this browser session only. It is not logged or "
            "stored on any server. Refresh the page and it is gone."
        ),
    )
    st.session_state["anthropic_api_key"] = api_key_input.strip()

    if st.session_state["anthropic_api_key"]:
        st.markdown(
            '<div class="key-status-ok">Key loaded for this session.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="key-status-missing">No key. Enter one or enable Demo mode.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    demo_mode = st.toggle(
        "Demo mode",
        value=st.session_state["demo_mode"],
        help=(
            "Show pre-computed sample analyses for a labeled product. "
            "No API key needed; no Anthropic API calls are made."
        ),
    )
    # Detect a transition into demo mode and populate session state once.
    if demo_mode and not st.session_state["_demo_mode_prev"]:
        _load_demo_into_session()
    elif (not demo_mode) and st.session_state["_demo_mode_prev"]:
        _clear_demo_from_session()
    st.session_state["demo_mode"] = demo_mode
    st.session_state["_demo_mode_prev"] = demo_mode

    if demo_mode:
        st.markdown(
            '<div class="key-status-demo">'
            'Demo mode active. All results are pre-computed samples '
            'for the bundled product label.'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### How to get a key")
    st.markdown(
        "1. Sign up at [console.anthropic.com](https://console.anthropic.com)\n"
        "2. **Settings → API Keys → Create Key**\n"
        "3. Add a small amount of credit (most analyses cost a few cents)\n"
        "4. Paste the key above"
    )

    st.markdown("---")
    st.markdown("### Privacy")
    st.markdown(
        "- The key is held only in your browser session.\n"
        "- Ingredient lists and uploaded photos are sent to the Anthropic API "
        "for analysis and are not stored by this app.\n"
        "- Refreshing the page clears everything."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Hero
# ─────────────────────────────────────────────────────────────────────────────
hero_demo_badge = (
    '<span class="demo-badge">Demo</span>' if st.session_state["demo_mode"] else ""
)
st.markdown(
    f"""
    <div class="hero">
        <div class="brand">SafeScan &middot; v2.1{hero_demo_badge}</div>
        <h1>Consumer Product Ingredient Safety Analyzer</h1>
        <p>Four independent analyzers across cosmetics, personal care, household, and
        food &mdash; grounded in regulatory and clinical literature. Bring your own
        Anthropic API key to run live analyses, or enable Demo mode in the sidebar
        to see sample output without a key.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state["anthropic_api_key"] and not st.session_state["demo_mode"]:
    st.warning(
        "Enter your Anthropic API key in the sidebar to run live analyses, "
        "or enable **Demo mode** to view sample output."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Shared rendering helpers
# ─────────────────────────────────────────────────────────────────────────────
def render_assessment_banner(data: dict):
    overall = data.get("overall_risk", "UNKNOWN")
    color   = RISK_COLORS.get(overall, "#6B7280")
    bg      = RISK_BG.get(overall, "#F9FAFB")
    flagged = data.get("flagged_count", 0)
    total   = data.get("total_count", 0)
    badge = (
        '<span class="demo-badge">Sample</span>'
        if st.session_state["demo_mode"]
        else ""
    )

    st.markdown(
        f"""
        <div class="assessment" style="background:{bg}; border-left-color:{color}">
            <div class="label">Overall Assessment {badge}</div>
            <div class="verdict" style="color:{color}">{overall}</div>
            <div class="summary">{data.get("summary", "")}</div>
            <div class="meta">{flagged} of {total} ingredients flagged for concern</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ingredient_list(data: dict):
    ingredients = data.get("ingredients_analyzed", [])
    ingredients_sorted = sorted(
        ingredients,
        key=lambda x: RISK_ORDER.get(x.get("risk_level", "MINIMAL"), 3),
    )

    for ing in ingredients_sorted:
        risk = ing.get("risk_level", "MINIMAL")
        expanded = risk in ("HIGH", "MEDIUM")
        name = ing.get("name", "Unknown")

        with st.expander(f"{name}   —   {risk}", expanded=expanded):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Classification**  \n{ing.get('classification', 'N/A')}")
                st.markdown(f"**Concern**  \n{ing.get('concern', 'None identified')}")
            with c2:
                alt = ing.get("alternative") or ing.get("safer_alternative") or "N/A"
                if alt and alt != "N/A":
                    st.markdown(f"**Suggested alternative**  \n{alt}")
                else:
                    st.markdown("**Suggested alternative**  \nNot applicable")


def render_concerns_and_recommendation(data: dict):
    concerns = data.get("key_concerns", [])
    if concerns:
        st.markdown('<div class="section-h">Key Concerns</div>', unsafe_allow_html=True)
        for c in concerns:
            st.warning(c)

    rec = data.get("recommendation", "")
    if rec:
        st.info(f"**Recommendation.** {rec}")


def render_cache_stats(data: dict):
    stats = data.get("_cache_stats", {})
    if not stats:
        return
    with st.expander("API usage statistics"):
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Input tokens",   stats.get("input_tokens", 0))
        s2.metric("Output tokens",  stats.get("output_tokens", 0))
        s3.metric("Cache created",  stats.get("cache_creation_tokens", 0))
        s4.metric("Cache read",     stats.get("cache_read_tokens", 0))
        if stats.get("cache_read_tokens", 0) > 0:
            st.caption("Prompt cache hit — reduced cost and latency.")


def run_analysis(name: str, ingredients_text: str) -> dict | None:
    """Call the analyzer directly with the user's API key, or return a sample in demo mode."""
    if st.session_state["demo_mode"]:
        sample = _load_sample_json(f"{name}.json")
        if sample is None:
            st.error(f"Demo sample for '{name}' not found. Check examples/{name}.json.")
        return sample

    cfg = ANALYZERS[name]
    api_key = st.session_state.get("anthropic_api_key", "")
    try:
        return cfg["fn"](ingredients_text, api_key)
    except Exception as exc:
        st.error(f"Analysis failed: {exc}")
        return None


def run_ocr(image_bytes: bytes, media_type: str) -> dict | None:
    if st.session_state["demo_mode"]:
        return _load_sample_json("ocr.json")

    api_key = st.session_state.get("anthropic_api_key", "")
    try:
        return extract_ingredients(image_bytes, api_key, media_type=media_type)
    except Exception as exc:
        st.error(f"OCR failed: {exc}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab_ocr, tab_allergen, tab_endocrine, tab_pregnancy, tab_env = st.tabs(
    [
        "Label Scan",
        ANALYZERS["allergen"]["tab_label"],
        ANALYZERS["endocrine"]["tab_label"],
        ANALYZERS["pregnancy"]["tab_label"],
        ANALYZERS["environmental"]["tab_label"],
    ]
)

# ═════════════════════════════════════════════════════════════════════════════
# TAB 0 — OCR
# ═════════════════════════════════════════════════════════════════════════════
with tab_ocr:
    st.markdown(
        """
        <div class="tab-header" style="background:#374151">
            <div class="module">Utility</div>
            <h2>Label Scan — Photo to Ingredient List</h2>
            <p>Upload a product label and extract a normalized ingredient list. The
            extracted text is held in session and can be loaded into any of the
            four analyzers with one click, avoiding redundant vision API calls.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    is_demo = st.session_state["demo_mode"]
    has_key = bool(st.session_state["anthropic_api_key"])

    col_up, col_help = st.columns([3, 1])

    with col_up:
        sample_image_path = _PROJECT_ROOT / "sample image.jpg"
        if is_demo and sample_image_path.exists():
            # In demo mode, render a static "file attached" card in place of the
            # file_uploader so the visual state matches a real upload.
            st.markdown("**Product label image**")
            file_size_mb = sample_image_path.stat().st_size / (1024 * 1024)
            st.markdown(
                f"""
                <div style='
                    background: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 6px;
                    padding: 10px 14px;
                    display: flex;
                    align-items: center;
                    gap: 0.7rem;
                    margin-bottom: 0.9rem;
                '>
                    <div style='flex: 1;'>
                        <div style='font-weight: 500; color: #1F2937; font-size: 0.9rem;'>sample image.jpg</div>
                        <div style='color: #6B7280; font-size: 0.78rem;'>{file_size_mb:.1f} MB</div>
                    </div>
                    <span style='background: #DBEAFE; color: #1E3A8A; padding: 3px 9px; border-radius: 3px; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em;'>SAMPLE</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.image(
                str(sample_image_path),
                caption="Uploaded image",
                use_container_width=True,
            )
            uploaded = None
        else:
            uploaded = st.file_uploader(
                "Product label image",
                type=["jpg", "jpeg", "png", "webp", "gif"],
                help="A clear, well-lit photo of the ingredient panel yields the best results.",
            )
            if uploaded is not None:
                st.image(uploaded, caption="Uploaded image", use_container_width=True)

        extract_disabled = (
            (uploaded is None and not is_demo) or
            (not has_key and not is_demo)
        )
        extract_help = None
        if extract_disabled:
            if not is_demo and not has_key:
                extract_help = "Enter your API key in the sidebar, or enable Demo mode."
            elif uploaded is None:
                extract_help = "Upload a label image first."

        extract_clicked = st.button(
            "Extract ingredients",
            type="primary",
            disabled=extract_disabled,
            help=extract_help,
        )

    with col_help:
        st.markdown('<div class="section-h">Workflow</div>', unsafe_allow_html=True)
        st.markdown(
            """
1. Upload a label image
2. Click **Extract ingredients**
3. Review and edit the result
4. Open any analyzer tab and click **Load from label scan**
            """
        )

    st.divider()

    if extract_clicked:
        with st.spinner("Extracting ingredient list from image…"):
            if is_demo:
                ocr_data = _load_sample_json("ocr.json")
            else:
                uploaded.seek(0)
                ocr_data = run_ocr(uploaded.read(), uploaded.type or "image/jpeg")

        if ocr_data is None:
            st.stop()
        if "error" in ocr_data:
            st.error(ocr_data["error"])
        else:
            st.session_state["extracted_text"] = ocr_data.get("comma_separated", "")
            st.session_state["extracted_meta"] = ocr_data

    meta = st.session_state["extracted_meta"]
    if meta:
        conf    = meta.get("confidence", "LOW")
        lang    = meta.get("language_detected", "—")
        count   = meta.get("ingredient_count", 0)
        ptype   = meta.get("product_type", "unknown")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Ingredients", count)
        m2.metric("Confidence",  conf)
        m3.metric("Language",    lang)
        m4.metric("Product type", ptype)

        notes = meta.get("notes", "")
        if notes:
            st.caption(f"Notes: {notes}")

        st.markdown(
            '<div class="section-h">Extracted Text (editable)</div>',
            unsafe_allow_html=True,
        )
        edited = st.text_area(
            "Correct any OCR errors before sending to an analyzer.",
            value=st.session_state["extracted_text"],
            height=140,
            key="ocr_editable",
            label_visibility="collapsed",
        )
        st.session_state["extracted_text"] = edited

        chips = [i.strip() for i in edited.split(",") if i.strip()]
        if chips:
            chips_html = "".join(
                f'<span class="chip{" warn" if i.endswith("?") else ""}">{i}</span>'
                for i in chips
            )
            st.markdown(chips_html, unsafe_allow_html=True)

        st.caption(
            "Extraction complete. Use **Load from label scan** in any analyzer tab to import."
        )


# ═════════════════════════════════════════════════════════════════════════════
# Analyzer tab builder (reused 4 times)
# ═════════════════════════════════════════════════════════════════════════════
def build_analyzer_tab(name: str):
    cfg = ANALYZERS[name]
    accent = cfg["accent"]
    input_key = f"input_{name}"

    def _load_from_scan():
        st.session_state[input_key] = st.session_state["extracted_text"]

    def _load_sample():
        st.session_state[input_key] = cfg["example"]

    def _clear_input():
        st.session_state[input_key] = ""

    st.markdown(
        f"""
        <div class="tab-header" style="background:{accent}">
            <div class="module">Analyzer</div>
            <h2>{cfg['title']}</h2>
            <p>{cfg['description']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_input, col_actions = st.columns([3, 1])

    with col_input:
        st.text_area(
            "Ingredient list (comma- or newline-separated)",
            height=160,
            key=input_key,
            placeholder="Water, Sodium Laureth Sulfate, ...",
        )

    with col_actions:
        st.markdown('<div class="section-h">Tools</div>', unsafe_allow_html=True)

        has_ocr = bool(st.session_state["extracted_text"].strip())
        st.button(
            "Load from label scan",
            key=f"load_ocr_{name}",
            on_click=_load_from_scan,
            disabled=not has_ocr,
            use_container_width=True,
            help=(
                "Import the ingredient text extracted in the Label Scan tab."
                if has_ocr
                else "Run a label scan first to enable this."
            ),
        )

        st.button(
            "Load sample",
            key=f"load_ex_{name}",
            on_click=_load_sample,
            use_container_width=True,
        )

        st.button(
            "Clear",
            key=f"clear_{name}",
            on_click=_clear_input,
            use_container_width=True,
        )

    is_demo = st.session_state["demo_mode"]
    has_key = bool(st.session_state["anthropic_api_key"])
    has_input = bool(st.session_state[input_key].strip())

    analyze_disabled = (not has_input) or ((not has_key) and (not is_demo))
    analyze_help = None
    if analyze_disabled:
        if not has_input:
            analyze_help = "Enter or load an ingredient list first."
        elif (not has_key) and (not is_demo):
            analyze_help = "Enter your API key in the sidebar, or enable Demo mode."

    analyze_clicked = st.button(
        "Run analysis",
        key=f"run_{name}",
        type="primary",
        disabled=analyze_disabled,
        help=analyze_help,
    )

    if analyze_clicked:
        with st.spinner("Running analysis…"):
            data = run_analysis(name, st.session_state[input_key])
        if data is not None:
            st.session_state[f"result_{name}"] = data

    # Render the last analysis result if one exists. Persists across tab switches
    # and across runs of other analyzers; only refreshes when the user clicks
    # Run analysis again on this tab.
    result = st.session_state.get(f"result_{name}")
    if result is not None:
        st.divider()
        render_assessment_banner(result)
        render_concerns_and_recommendation(result)
        st.markdown(
            '<div class="section-h">Per-Ingredient Findings</div>',
            unsafe_allow_html=True,
        )
        render_ingredient_list(result)
        render_cache_stats(result)


# ═════════════════════════════════════════════════════════════════════════════
# TABS 1–4 — Analyzers
# ═════════════════════════════════════════════════════════════════════════════
with tab_allergen:
    build_analyzer_tab("allergen")

with tab_endocrine:
    build_analyzer_tab("endocrine")

with tab_pregnancy:
    build_analyzer_tab("pregnancy")

with tab_env:
    build_analyzer_tab("environmental")

# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "SafeScan is provided for informational purposes only and does not constitute "
    "medical, legal, or regulatory advice. Risk assessments are derived from publicly "
    "available scientific literature and regulatory classifications including, but not "
    "limited to, EU Regulation 1223/2009, EU Regulation 1169/2011, EU Regulation "
    "2018/605, FDA FALCPA + FASTER Act, EPA EDSP, NOAA reef guidance, ACOG, AAP, and "
    "the FDA Pregnancy and Lactation Labeling Rule."
)
