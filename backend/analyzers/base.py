"""Common Claude API utilities shared across all analyzers.

All analyzers use the same JSON output schema so the frontend can render
them with a single component. Prompt caching is applied to the system
prompt for cost efficiency when the same analyzer is called repeatedly.

The API key is passed in by the caller (typically from a user-supplied
input field) rather than read from the environment, so this module is
safe to use in a BYOK (Bring Your Own Key) deployment.
"""
import json
import re
import anthropic

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 4096


def run_text_analysis(
    api_key: str,
    system_prompt: str,
    ingredients_text: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> dict:
    """Run a text-only ingredient analysis with Claude."""
    if not api_key:
        raise ValueError("Anthropic API key is required.")

    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Analyze these consumer product ingredients. "
                    f"Respond ONLY with valid JSON matching the schema.\n\n"
                    f"Ingredients:\n{ingredients_text}"
                ),
            }
        ],
    )

    result = _parse_json_response(response.content[0].text)
    result["_cache_stats"] = _extract_cache_stats(response)
    return result


def run_image_analysis(
    api_key: str,
    system_prompt: str,
    user_query: str,
    image_bytes: bytes,
    media_type: str = "image/jpeg",
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> dict:
    """Run an image-based analysis with Claude (used by the OCR module)."""
    if not api_key:
        raise ValueError("Anthropic API key is required.")

    import base64

    client = anthropic.Anthropic(api_key=api_key)
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": user_query},
                ],
            }
        ],
    )

    result = _parse_json_response(response.content[0].text)
    result["_cache_stats"] = _extract_cache_stats(response)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_json_response(raw: str) -> dict:
    """Strip markdown code fences if present, then parse JSON."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def _extract_cache_stats(response) -> dict:
    return {
        "cache_creation_tokens": response.usage.cache_creation_input_tokens or 0,
        "cache_read_tokens": response.usage.cache_read_input_tokens or 0,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Unified output schema (documentation only — not enforced at runtime)
# ─────────────────────────────────────────────────────────────────────────────

UNIFIED_SCHEMA_DOC = """
All analyzers MUST return JSON in this shape so the frontend can render them
with a single component:

{
  "ingredients_analyzed": [...],
  "overall_risk": "HIGH|MEDIUM|LOW|MINIMAL",
  "flagged_count": <int>,
  "total_count": <int>,
  "summary": "2-3 sentence overall assessment",
  "key_concerns": [...],
  "recommendation": "..."
}
"""
