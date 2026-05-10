from __future__ import annotations

import os


TRUTHY_VALUES = {"1", "true", "yes", "on"}


class ModelCallError(RuntimeError):
    """Raised when LLM mode is enabled but the provider call cannot run."""


def llm_mode_enabled() -> bool:
    return os.getenv("CAREERCOMPASS_USE_LLM", "").strip().lower() in TRUTHY_VALUES


def call_openai_json(prompt: str) -> str | None:
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

    model = os.getenv("CAREERCOMPASS_LLM_MODEL", "gpt-4o-mini")
    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a CareerCompass agent. Return only valid JSON matching the requested schema.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content or ""

