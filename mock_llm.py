"""mock_llm.py - a FAKE LLM for offline testing (run with --mock).

It is a simple keyword program, NOT a real model. It is useful to check that the
Python code (validator, retry, fallback, safety net, reports) works without an API key.
It is deliberately imperfect, like a real LLM can be:
  - it does not know the words "hair" or "mudi", so the safety net has something to catch
  - if a comment tries to give it instructions, it replies with plain text instead of JSON
Real accuracy numbers must come from a LIVE run with a real API key.
"""
import json
import re

URGENT_WORDS = ["insect", "poochi", "stale", "sick", "expired", "particles", "worm"]
HYGIENE_WORDS = URGENT_WORDS + ["oily", "smelly", "dirty", "washed", "washing", "hair", "mudi"]
TASTE_WORDS = ["salt", "undercooked", "bland", "tasty", "watery", "hard", "spicy", "pulichu",
               "pongal", "fish fry", "rasam", "curry", "variety", "உப்பு"]
QUANTITY_WORDS = ["not enough", "too less", "hungry", "quantity", "less"]
TIMING_WORDS = ["late", " pm", "delay", "minutes"]
POSITIVE_WORDS = ["tasty", "excellent", "great", "sema"]
NEGATIVE_WORDS = ["bad", "again", "too", "not", "late", "bland", "cold", "hungry", "stale",
                  "insect", "poochi", "sick", "expired", "hair", "mudi", "oily", "smelly",
                  "undercooked", "particles", "உப்பாக"]


def has_any(text, words):
    return any(word in text for word in words)


def fake_llm(system_prompt, user_message):
    match = re.search(r"<comment>(.*?)</comment>", user_message, re.S)
    comment = match.group(1).strip() if match else ""
    text = comment.lower()

    # Pretend to be confused by a hidden instruction: reply with plain text, not JSON
    if "ignore" in text and "instruction" in text:
        return "Sure! I will ignore the earlier instructions."

    if has_any(text, HYGIENE_WORDS):
        category = "hygiene"
    elif has_any(text, QUANTITY_WORDS):
        category = "quantity"
    elif has_any(text, TIMING_WORDS):
        category = "timing"
    elif has_any(text, TASTE_WORDS):
        category = "taste"
    else:
        category = "other"

    if has_any(text, POSITIVE_WORDS) and not has_any(text, ["not ", "too "]):
        sentiment = "positive"
    elif has_any(text, NEGATIVE_WORDS):
        sentiment = "negative"
    else:
        sentiment = "neutral"

    reply = {
        "category": category,
        "sentiment": sentiment,
        "urgent": has_any(text, URGENT_WORDS),
        "summary": " ".join(comment.split()[:8]),
    }
    return json.dumps(reply)
