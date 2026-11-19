# Judgment Framework

> If your class used different wording for the three questions, replace the three column headings
> below with your exact wording. The content of each cell stays the same.

**Human checkpoint: the warden reads every comment in `output/urgent.csv`** and decides the action.
The tool never contacts anyone and never takes action on its own.

| Part of the tool | Q1. What could go wrong? | Q2. How do we catch it? | Q3. Who decides / is accountable? |
|---|---|---|---|
| **Urgent flag (most important)** | LLM misses a real health risk (false negative), or marks an angry taste complaint as urgent (false positive), or is tricked by a hidden instruction in the comment | Safety net raises urgency whenever a health-risk word is found, even if the LLM said false. The rubric says taste, quantity and timing are never urgent. Red-team test 1 checks the hidden-instruction case | **Warden** reads every urgent comment. A false positive costs a minute of reading; a false negative is the expensive mistake, so the design leans towards urgent when unsure |
| Safety net | A health word is missing from the list (for example hair written as "முடி" in Tamil script), or a word matches by accident | Whole-word matching for "mudi"; word list kept in one place and easy to extend; false alarms only add to the warden's list, they never hide anything. It can only raise urgency, never lower it | Student (me) maintains the list; warden reports misses so words get added |
| Category label | LLM picks a wrong category (for example hygiene vs taste for "smelly plates") | Allowed-value check on every reply; eval harness with known answers; 5 examples in the prompt | Mess committee reads the category counts as trends, not as exact figures |
| Sentiment label | Sarcasm or mixed comments ("sambar sour but tasty") are mislabelled | Allowed-value check; the sentiment never affects urgency | Mess committee; a wrong sentiment only slightly moves the % negative |
| Summary | Summary is too long or wrong | Validator rejects summaries over 12 words; the original comment is always saved next to it | Warden reads the original text in `urgent.csv`, not only the summary |
| Reply validator, retry, fallback | LLM returns text instead of JSON, wrong keys or an API error | `parse_reply()` and `is_valid()` check every reply. Retry once, then `needs_manual_review`. try/except means one bad reply never crashes the run | A committee member reads every `needs_manual_review` comment |
| Empty comments | An empty comment is sent to the API (wasted cost) or silently dropped | Checked before the API call; goes to `needs_manual_review`; red-team test 3 proves zero API calls | Committee member sees it listed in `summary.txt` |
| Counting and % negative | LLM does arithmetic wrongly | LLM never counts. Python counts with `Counter` | Mess committee reads `summary.txt` |
| API key | Key pushed to GitHub | Key only in `.env`, which `.gitignore` excludes; `.env.example` has no real key | Student checks `git status` before every commit |

## Where the AI is allowed to decide, and where it is not
- **AI may:** read a comment (English, Tamil or Tanglish) and suggest a category, sentiment, urgent flag and short summary.
- **Python decides:** whether the reply is accepted, whether the comment is urgent (it can overrule the LLM upwards), and every count.
- **A human decides:** every action. The warden for urgent comments, the committee for trends and manual-review items.
