from __future__ import annotations

import os
from typing import Any


TRUTHY_VALUES = {"1", "true", "yes", "on"}
DISABLED_VALUES = {"0", "false", "no", "off"}
DEFAULT_OPENAI_MODEL = "gpt-5.4-mini"


class ModelCallError(RuntimeError):
    """Raised when LLM mode is enabled but the provider call cannot run."""


def llm_mode_enabled() -> bool:
    explicit_enabled = os.getenv("CAREERCOMPASS_LLM_ENABLED")
    if explicit_enabled and explicit_enabled.strip().lower() in DISABLED_VALUES:
        return False

    legacy_setting = os.getenv("CAREERCOMPASS_USE_LLM", "").strip().lower()
    if legacy_setting in DISABLED_VALUES:
        return False
    if legacy_setting in TRUTHY_VALUES:
        return True

    return bool(os.getenv("OPENAI_API_KEY"))


def call_openai_json(prompt: str, response_format: dict | None = None) -> str | None:
    """Return raw JSON text from OpenAI when LLM mode is enabled.

    The app deliberately defaults to deterministic fallbacks so demos do not
    require API keys, network access, or provider packages.
    """

    if not llm_mode_enabled():
        return None

    if not os.getenv("OPENAI_API_KEY"):
        raise ModelCallError("CAREERCOMPASS_USE_LLM is enabled, but OPENAI_API_KEY is missing.")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ModelCallError("Install the openai package to enable live LLM calls.") from exc

    model = _openai_model()
    client = _create_openai_client(OpenAI)
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": (
                    "You are a CareerCompass agent. Return only valid JSON "
                    "matching the requested schema."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        text={"format": response_format or {"type": "json_object"}},
    )

    return _extract_response_text(response)


def _openai_model() -> str:
    model = os.getenv("CAREERCOMPASS_OPENAI_MODEL") or os.getenv("CAREERCOMPASS_LLM_MODEL")
    return (model or DEFAULT_OPENAI_MODEL).strip() or DEFAULT_OPENAI_MODEL


def _create_openai_client(openai_class: Any) -> Any:
    return openai_class()


def _extract_response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    for item in getattr(response, "output", []) or []:
        for part in _get_value(item, "content") or []:
            refusal = _get_value(part, "refusal")
            if refusal:
                raise ModelCallError("OpenAI response included a refusal.")
            text = _get_value(part, "text")
            if isinstance(text, str) and text.strip():
                return text

    return ""


def _get_value(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, key, None)
