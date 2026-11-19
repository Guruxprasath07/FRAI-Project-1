# Cost and Latency Note

## 1. API calls for one day of input
- Feedback arrives as "dozens a week", so a normal day is about 5 to 10 comments.
- **Worst-case day used for planning: 50 comments.**
- One non-empty comment = one API call. Empty comments = 0 calls.
- A failed or invalid reply is retried once, so allow about 10% extra.
- **50 comments x 1.1 = about 55 API calls per day** (about 10 calls on a normal day).
- The sample file has 26 comments, 2 of them empty, so a full run makes **24 calls** (confirmed by the program's own counter).

## 2. Time per call
- Typical for a small, fast model with no extra "thinking": **about 1 to 3 seconds per call**.
- The program prints its real average ("Average latency per call") after every live run.
  **Replace this estimate with your own measured number after your live run: ______ s.**
- Calls run one after another, so 55 calls is about 1 to 3 minutes. This is fine because the tool is run once a day, not live.
- On the free tier, rate limits (a few calls per minute) can slow the run. Set `REQUEST_DELAY=6` in `.env` if you see "429 too many requests".

## 3. Cost per day
Token estimate per call (system prompt is 550 words, about 800 tokens):

| Item | Tokens per call | 55 calls per day |
|---|---|---|
| Input (system prompt + comment) | about 830 | about 46,000 |
| Output (small JSON) | about 45 | about 2,500 |

Illustrative prices for a Flash-class model: **$0.30 per 1M input tokens, $2.50 per 1M output tokens**.
These prices are an assumption. Check the provider's current pricing page and replace them.

- Input: 46,000 / 1,000,000 x $0.30 = about $0.014
- Output: 2,500 / 1,000,000 x $2.50 = about $0.006
- **Total: about $0.02 per day (roughly 2 US cents, under Rs 2).**
- On the **free tier the cost is $0**, limited only by the rate limits above.

## 4. Why it stays cheap
- One short call per comment, with no chat history.
- Python does all counting, so the LLM never gets long inputs.
- Empty comments are skipped before the API call.
- Thinking is switched off and the reply is a small JSON object.
