"""llm_client.py - the only file that talks to the LLM API.

If your Week 12 class used a different provider, change only call_llm() in this file.
The API key is read from the environment (or a .env file). It is never written in the code.
"""
import os
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()  # reads GEMINI_API_KEY from a local .env file if it exists
except ImportError:
    pass  # python-dotenv is optional; you can also set the variable in your terminal

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-2.5-flash"


def use_mock_if_asked(argv):
    """If the user typed --mock, switch to the offline fake LLM (no key, no internet needed)."""
    if "--mock" in argv:
        os.environ["LLM_MODE"] = "mock"


def is_mock():
    return os.getenv("LLM_MODE", "").lower() == "mock"


def is_ready():
    """True if we can make a call: either mock mode, or an API key is set."""
    return is_mock() or bool(os.getenv("GEMINI_API_KEY"))


def mode_name():
    """Short text used in report headers so nobody confuses mock and live results."""
    if is_mock():
        return "MOCK (offline fake LLM, not a real model)"
    return "LIVE (" + os.getenv("GEMINI_MODEL", DEFAULT_MODEL) + ")"


def call_llm(system_prompt, user_message):
    """Send one comment to the LLM and return its reply as plain text."""
    if is_mock():
        import mock_llm
        return mock_llm.fake_llm(system_prompt, user_message)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    body = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_message}]}],
        "generationConfig": {
            "temperature": 0,                          # same comment -> same label
            "responseMimeType": "application/json",    # ask for JSON only
           
        },
    }
    response = requests.post(
        API_URL.format(model=model),
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        json=body,
        timeout=30,
    )
    response.raise_for_status()  # turns HTTP errors (like 429 too many requests) into exceptions
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]
