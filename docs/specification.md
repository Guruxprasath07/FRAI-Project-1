# Specification: Mess Feedback Sorter

CIT AI-Native Engineering Programme · Assessment 5 · Written before any code
Author: Guru Prasath · Status: submit at Checkpoint 1 for faculty sign-off

## 1. Purpose
The mess committee gets dozens of comments a week in English, Tamil and Tanglish. A health risk
(for example an insect in the sambar) can get buried between comments about salt. This tool
labels and sorts every comment and puts health risks at the top for the warden.
**The tool only labels and sorts. A person decides what action to take.**

## 2. Input
`feedback.csv` with columns `id,date,meal,comment`. At least 20 comments (we use 26).
Includes English, Tamil script, Tanglish, a one-word comment ("ok"), an empty comment and a
whitespace-only comment.

## 3. LLM output rules (JSON)
One object per comment with exactly four keys:

| Field | Allowed values | Rule |
|---|---|---|
| category | taste, hygiene, quantity, timing, other | pick the one that fits |
| sentiment | positive, negative, neutral | |
| urgent | true or false (boolean) | true only for a health risk |
| summary | text | 12 words or fewer, in English |

Wrong key names, wrong values, a non-boolean `urgent`, or a summary over 12 words = invalid reply.

## 4. What counts as urgent
True only for a health risk: **(a)** a foreign object (insect, hair, stone, plastic, particles),
**(b)** stale, spoiled or expired food, **(c)** someone falling sick.
Taste, quantity and timing complaints are never urgent, however angry they sound.

## 5. Python rules
1. **Validate every reply.** If invalid, retry once. If still invalid, label the comment `needs_manual_review`.
2. **Empty or whitespace-only comments are never sent to the LLM.** They go straight to `needs_manual_review`.
3. **Safety net.** If the comment contains a health-risk word (insect, hair, expired, fell sick, poochi, mudi and others in the word list), it is urgent whatever the LLM said. The safety net can only raise urgency to true, never lower it. It also runs on comments that failed validation.
4. **Counting is Python.** The LLM never counts or calculates percentages.
5. A network or API error counts as a failed attempt, never a crash.

## 6. Outputs (written to `output/`)
- `results.csv`: every comment with its four labels (plus where the urgent flag came from).
- `urgent.csv`: only urgent comments, with the original text.
- `summary.txt`: count per category, % negative, and the urgent list.

"% negative" = negative comments ÷ comments that received a valid label (needs_manual_review excluded).

## 7. Who acts on the urgent list
**The warden** reads every comment in `urgent.csv` and decides the action (check the kitchen,
speak to the cook, contact a doctor). The mess committee reads `summary.txt` for trends.
Comments marked `needs_manual_review` are read by a committee member.

## 8. Out of scope
No automatic action or messages to students, no web interface, no database, no translation of the original comment.
