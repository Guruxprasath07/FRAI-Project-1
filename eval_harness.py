"""eval_harness.py - checks the whole pipeline on 5 comments with known answers.

Run:  python eval_harness.py            (live LLM)
      python eval_harness.py --mock     (offline fake LLM)
A case passes only if BOTH the category and the urgent flag match what we expect.
Results are printed and saved to docs/eval_results.txt.
"""
import sys

import llm_client
import sorter

# (comment, meal, expected category, expected urgent)
EVAL_CASES = [
    ("Found a small insect in the sambar", "Dinner", "hygiene", True),
    ("Rice was undercooked again today", "Lunch", "taste", False),
    ("Dinner was served after 9 pm again", "Dinner", "timing", False),
    ("Not enough rice, we stayed hungry", "Dinner", "quantity", False),
    ("Chapati had a hair in it", "Dinner", "hygiene", True),
]


def run_eval():
    system_prompt = sorter.load_prompt(sorter.PROMPT_FILE)
    lines = []
    passed = 0

    for number, (comment, meal, want_category, want_urgent) in enumerate(EVAL_CASES, start=1):
        result = sorter.label_comment(comment, meal, system_prompt)
        ok = result["category"] == want_category and result["urgent"] == want_urgent
        if ok:
            passed += 1
        lines.append(
            str(number) + ". " + ("PASS" if ok else "FAIL") + " | " + comment + "\n"
            + "     expected: category=" + want_category + ", urgent=" + str(want_urgent) + "\n"
            + "     got:      category=" + result["category"] + ", urgent=" + str(result["urgent"])
            + (" (" + result["urgent_source"] + ")" if result["urgent_source"] else "")
        )

    report = ["EVAL HARNESS RESULTS", "Mode: " + llm_client.mode_name(), ""]
    report += lines
    report.append("")
    report.append("Score: " + str(passed) + " / " + str(len(EVAL_CASES)) + " passed")
    return "\n".join(report)


if __name__ == "__main__":
    llm_client.use_mock_if_asked(sys.argv)
    if not llm_client.is_ready():
        print("No API key found. Set GEMINI_API_KEY or run with --mock.")
        sys.exit(1)
    text = run_eval()
    print(text)
    with open("docs/eval_results.txt", "w", encoding="utf-8") as file:
        file.write(text + "\n")
