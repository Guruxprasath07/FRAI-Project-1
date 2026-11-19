"""sorter.py - Mess Feedback Sorter (console tool).

Reads feedback.csv, asks an LLM to label each comment, checks every reply in Python,
applies a health-risk safety net, and writes three files into output/.

Run:   python sorter.py              (live LLM, needs GEMINI_API_KEY)
       python sorter.py --mock       (offline fake LLM, no key needed)
       python sorter.py other.csv    (use a different input file)

The tool only labels and sorts. A person (the warden) decides what action to take.
"""
import csv
import json
import os
import re
import sys
import time
from collections import Counter

import llm_client

INPUT_FILE = "feedback.csv"
PROMPT_FILE = "system_prompt.txt"
OUTPUT_DIR = "output"

CATEGORIES = ["taste", "hygiene", "quantity", "timing", "other"]
SENTIMENTS = ["positive", "negative", "neutral"]
REQUIRED_KEYS = {"category", "sentiment", "urgent", "summary"}
MANUAL = "needs_manual_review"
MAX_SUMMARY_WORDS = 12
# Seconds to wait between calls. Set REQUEST_DELAY=6 in .env if the free tier says "429 too many requests".
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "0"))

# Health-risk words for the safety net. English, Tanglish and Tamil script.
HEALTH_WORDS = [
    "insect", "cockroach", "roach", "worm", "lizard", "bug", "hair", "mudi",
    "stone", "pebble", "plastic", "metal",
    "expired", "expiry", "stale", "spoiled", "spoilt", "rotten", "fungus", "mold", "mould",
    "fell sick", "fell ill", "got sick", "sick", "vomit", "food poisoning",
    "diarrhea", "diarrhoea", "stomach pain", "stomach ache",
    "poochi", "puzhu",
    "பூச்சி", "புழு", "பல்லி", "வாந்தி",
]
# "mudi" must match as a whole word, because Tanglish words like "mudinjidichu" (finished) start with it
WHOLE_WORD_ONLY = {"mudi"}


# ---------------------------------------------------------------- reading input

def load_comments(path):
    """Read the CSV file and return a list of dictionaries (one per comment)."""
    with open(path, newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def load_prompt(path):
    """Read the system prompt text file."""
    with open(path, encoding="utf-8") as file:
        return file.read()


# ---------------------------------------------------------------- checking the LLM reply

def parse_reply(reply_text):
    """Turn the LLM's text into a dictionary. Return None if it is not a JSON object."""
    text = str(reply_text).strip()
    if text.startswith("```"):            # some models wrap JSON in a code fence
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def is_valid(data):
    """True only if the reply has exactly the right keys and allowed values."""
    if not isinstance(data, dict):
        return False
    if set(data.keys()) != REQUIRED_KEYS:
        return False
    if data["category"] not in CATEGORIES:
        return False
    if data["sentiment"] not in SENTIMENTS:
        return False
    if not isinstance(data["urgent"], bool):      # "true" in quotes is not allowed
        return False
    if not isinstance(data["summary"], str):
        return False
    if len(data["summary"].split()) > MAX_SUMMARY_WORDS:
        return False
    return True


def manual_review_result(reason):
    """The label we use when the LLM cannot be trusted or was never asked."""
    return {"category": MANUAL, "sentiment": MANUAL, "urgent": False, "summary": reason}


# ---------------------------------------------------------------- labelling one comment

def classify(text, meal, system_prompt, call_llm=llm_client.call_llm):
    """Label one comment with the LLM. Try twice, then fall back to needs_manual_review."""
    if text.strip() == "":                        # empty comments never reach the API
        return manual_review_result("Empty comment")

    user_message = "Meal: " + meal + "\n<comment>" + text + "</comment>"

    for attempt in (1, 2):                        # first try + one retry
        try:
            reply = call_llm(system_prompt, user_message)
        except Exception as error:                # network error, timeout, 429, bad response...
            print("   (attempt " + str(attempt) + " failed: " + str(error)[:80] + ")")
            time.sleep(1)
            continue
        data = parse_reply(reply)
        if is_valid(data):
            data["urgent_source"] = "llm" if data["urgent"] else ""
            return data

    result = manual_review_result("LLM reply failed validation")
    result["urgent_source"] = ""
    return result


def find_health_word(text):
    """Return the first health-risk word found in the text, or None."""
    lowered = text.lower()
    for word in HEALTH_WORDS:
        if not word.isascii():                    # Tamil script: simple substring check
            if word in lowered:
                return word
            continue
        pattern = r"\b" + re.escape(word)
        if word in WHOLE_WORD_ONLY:
            pattern = pattern + r"\b"
        if re.search(pattern, lowered):
            return word
    return None


def apply_safety_net(text, result):
    """If a health-risk word is present, make the comment urgent. Never makes it less urgent."""
    word = find_health_word(text)
    if word is not None and result["urgent"] is False:
        result["urgent"] = True
        result["urgent_source"] = "safety_net (" + word + ")"
    return result


def label_comment(text, meal, system_prompt, call_llm=llm_client.call_llm):
    """Full pipeline for one comment: LLM label -> validation -> safety net."""
    result = classify(text, meal, system_prompt, call_llm)
    return apply_safety_net(text, result)


# ---------------------------------------------------------------- counting (Python only)

def count_categories(rows):
    """Count how many comments are in each category."""
    counts = Counter()
    for row in rows:
        counts[row["category"]] += 1
    return counts


def percent_negative(rows):
    """% negative among comments that got a valid label (manual review rows are left out)."""
    labelled = [row for row in rows if row["sentiment"] != MANUAL]
    if len(labelled) == 0:
        return 0.0
    negative = [row for row in labelled if row["sentiment"] == "negative"]
    return round(100 * len(negative) / len(labelled), 1)


# ---------------------------------------------------------------- writing the three reports

def write_reports(rows, output_dir=OUTPUT_DIR):
    """Write results.csv, urgent.csv and summary.txt. Returns the three file paths."""
    os.makedirs(output_dir, exist_ok=True)
    results_path = os.path.join(output_dir, "results.csv")
    urgent_path = os.path.join(output_dir, "urgent.csv")
    summary_path = os.path.join(output_dir, "summary.txt")

    urgent_rows = [row for row in rows if row["urgent"] is True]

    with open(results_path, "w", newline="", encoding="utf-8-sig") as file:
        fields = ["id", "date", "meal", "comment", "category", "sentiment",
                  "urgent", "summary", "urgent_source"]
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    with open(urgent_path, "w", newline="", encoding="utf-8-sig") as file:
        fields = ["id", "date", "meal", "comment", "category", "summary", "urgent_source"]
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(urgent_rows)

    counts = count_categories(rows)
    labelled = [row for row in rows if row["sentiment"] != MANUAL]
    negative = [row for row in labelled if row["sentiment"] == "negative"]
    manual_ids = [row["id"] for row in rows if row["category"] == MANUAL]

    with open(summary_path, "w", encoding="utf-8") as file:
        file.write("MESS FEEDBACK SUMMARY\n")
        file.write("=====================\n")
        file.write("Total comments: " + str(len(rows)) + "\n\n")
        file.write("Count per category:\n")
        for name in CATEGORIES + [MANUAL]:
            file.write("  " + name.ljust(20) + str(counts.get(name, 0)) + "\n")
        file.write("\nNegative comments: " + str(len(negative)) + " of " + str(len(labelled))
                   + " labelled = " + str(percent_negative(rows)) + "%\n")
        file.write("Needs manual review: " + (", ".join(manual_ids) if manual_ids else "none") + "\n\n")
        file.write("URGENT LIST FOR THE WARDEN (" + str(len(urgent_rows)) + " comments)\n")
        file.write("-----------------------------------\n")
        for row in urgent_rows:
            file.write(row["id"] + " | " + row["date"] + " | " + row["meal"] + " | "
                       + row["comment"].strip() + "  [" + row["urgent_source"] + "]\n")
        file.write("\nNote: these are labels only. The warden decides what action to take.\n")

    return results_path, urgent_path, summary_path


# ---------------------------------------------------------------- main program

def main():
    llm_client.use_mock_if_asked(sys.argv)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    input_file = args[0] if args else INPUT_FILE

    if not llm_client.is_ready():
        print("No API key found. Set GEMINI_API_KEY (see README) or run with --mock.")
        return 1

    try:
        comments = load_comments(input_file)
        system_prompt = load_prompt(PROMPT_FILE)
    except FileNotFoundError as error:
        print("Could not find file: " + str(error.filename))
        return 1

    stats = {"calls": 0, "seconds": 0.0}

    def counted_llm(prompt, message):             # wraps the real call so we can measure it
        start = time.time()
        try:
            return llm_client.call_llm(prompt, message)
        finally:
            stats["calls"] += 1
            stats["seconds"] += time.time() - start

    print("Mode: " + llm_client.mode_name())
    print("Reading " + str(len(comments)) + " comments from " + input_file + "\n")

    rows = []
    for item in comments:
        comment = item["comment"] or ""
        labels = label_comment(comment, item["meal"], system_prompt, counted_llm)
        row = {"id": item["id"], "date": item["date"], "meal": item["meal"], "comment": comment}
        row.update(labels)
        rows.append(row)
        flag = "URGENT" if row["urgent"] else "      "
        print(item["id"] + " " + flag + " " + row["category"].ljust(20) + row["sentiment"])
        if comment.strip() != "":
            time.sleep(REQUEST_DELAY)             # free-tier keys allow only a few calls per minute

    paths = write_reports(rows)

    print("\nWrote: " + ", ".join(paths))
    print("API calls made: " + str(stats["calls"]))
    if stats["calls"] > 0:
        print("Average latency per call: " + str(round(stats["seconds"] / stats["calls"], 2)) + " s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
