# Mess Feedback Sorter

A console tool for the CIT hostel mess. It reads student feedback (English, Tamil and Tanglish),
asks an LLM to label each comment, checks every reply in Python, and writes a summary for the mess
committee and an urgent list for the warden.

**The tool only labels and sorts. A person decides what action to take.**
The warden reads every comment in `output/urgent.csv`.

CIT AI-Native Engineering Programme · Semester 1 · Assessment 5 · Author: Guru Prasath

## How it works

```
feedback.csv -> skip empty comments -> LLM labels comment -> Python checks reply
             -> retry once -> else needs_manual_review -> safety net (health words)
             -> results.csv + urgent.csv + summary.txt
```

For each comment the LLM returns:
`{"category": "hygiene", "sentiment": "negative", "urgent": true, "summary": "Insect found in sambar"}`

| Field | Allowed values |
|---|---|
| category | taste, hygiene, quantity, timing, other |
| sentiment | positive, negative, neutral |
| urgent | true or false (health risk only) |
| summary | 12 words or fewer |

Python rules: validate every reply, retry once, empty comments never reach the API, the safety net
can only raise urgency, and Python (not the LLM) does all counting.

## Project files

| File | Purpose |
|---|---|
| `sorter.py` | Main program: `classify()`, `parse_reply()`, `is_valid()`, `apply_safety_net()`, `write_reports()` |
| `llm_client.py` | The only file that calls the LLM API (key read from the environment) |
| `mock_llm.py` | Fake LLM for offline testing with `--mock` |
| `system_prompt.txt` | System prompt (Authority, Exemplar, Constraint, Rubric, Metadata) |
| `feedback.csv` | Input: 26 comments |
| `eval_harness.py` | 5 comments with expected answers |
| `red_team.py` | 3 tricky inputs: hidden instruction, Tanglish, empty |
| `docs/` | Specification, Judgment Framework, cost and latency note, decision journal, test results |
| `output/` | `results.csv`, `urgent.csv`, `summary.txt` |

## Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac / Linux
pip install -r requirements.txt
```

Get a free API key from Google AI Studio, then:

```bash
copy .env.example .env         # Windows   (Mac / Linux: cp .env.example .env)
```

Open `.env` and replace `your-key-here` with your key. **Never commit `.env`.** The `.gitignore` already excludes it.

## Run

```bash
python sorter.py               # live LLM, writes the three files into output/
python eval_harness.py         # eval harness, saves docs/eval_results.txt
python red_team.py             # red-team tests, saves docs/red_team_results.txt
```

No key yet? Add `--mock` to any command to use the offline fake LLM. Mock results only prove the
Python code works. **Run once without `--mock` and commit those results before you submit.**

## Push to GitHub

Create an empty repository on github.com first (no README, no .gitignore), then:

```bash
git init
git status                     # check that .env is NOT listed

git add .gitignore .env.example requirements.txt feedback.csv system_prompt.txt docs/specification.md
git commit -m "Add specification, input data, system prompt and gitignore"

git add llm_client.py mock_llm.py sorter.py
git commit -m "Add classifier with LLM client, validator, retry and safety net"

git add eval_harness.py red_team.py
git commit -m "Add eval harness and red-team tests"

git add docs README.md output
git commit -m "Add judgment framework, cost note, decision journal, README and outputs"

git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/mess-feedback-sorter.git
git push -u origin main
```

If you ever commit the key by mistake, delete that key in the provider's console and create a new one.
Removing the file in a later commit does not remove it from history.

## Known limits
- The safety net uses a word list. A health word it does not know (for example hair written in Tamil script) depends on the LLM to catch it.
- Mock mode is not a real model. Accuracy figures must come from a live run.
- Sarcasm and mixed-sentiment comments may get the wrong sentiment. This never affects the urgent flag.
