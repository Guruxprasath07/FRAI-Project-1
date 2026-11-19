# AI Decision Journal

> This is a STARTER. A decision journal only counts if it is yours. Go through each row, check that it
> matches what actually happened, and edit "My decision" and "Why" in your own words.
> You must be able to explain every line of the code in the Q&A.

| # | Decision | What AI suggested | My decision | Why |
|---|---|---|---|---|
| 1 | Which LLM API | Gemini free tier through plain `requests`, in one file (`llm_client.py`) | (confirm: use the API from Week 12, or keep Gemini) | Free key is allowed; one file means switching provider changes only `call_llm()` |
| 2 | Offline `--mock` mode | A fake keyword LLM so the Python code can be tested without a key | (keep / remove) | Lets me test the validator, retry and safety net any time. Mock results are NOT real accuracy figures |
| 3 | Run the safety net even when the LLM reply failed | Yes, apply it to `needs_manual_review` rows too | (agree / disagree) | An insect comment must reach the warden even if the LLM call failed |
| 4 | "mudi" matched as a whole word only | Avoids flagging Tanglish "mudinjidichu" (finished) | (agree / disagree) | Fewer false alarms for the warden |
| 5 | Prompt rule: "if unsure, choose urgent = true" | Lean towards urgent | (agree / disagree) | Missing a health risk costs more than one extra comment for the warden to read |
| 6 | % negative excludes `needs_manual_review` rows | Only count comments that have a valid sentiment | (agree / disagree) | An unlabelled comment has no sentiment to count |
| 7 | Where I rejected or changed AI output | (write at least one real example here) | | |

## Reflection (400 words): questions to answer in your own words
1. Which part of the tool did you trust least at the start, and what changed your mind (or didn't)?
2. Show one case where the safety net caught something the LLM missed. What does that tell you about trusting an LLM's urgent flag?
3. What did you find hard in Tamil and Tanglish comments?
4. What would go wrong if the warden stopped reading `urgent.csv`?
5. If you ran this on real data for a month, what would you improve first?
