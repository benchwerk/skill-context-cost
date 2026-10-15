---
name: meeting-notes-summary
description: Turn raw meeting notes or a transcript into a concise summary (under 200 words) listing decisions, action items with owner and due date when stated, and open questions. Use when the user pastes or points to meeting notes, a transcript, or asks to summarize a meeting or extract action items.
---

# Meeting Notes Summary

Convert raw notes or a transcript into a short, scannable summary.

## Process

1. Read the full input (pasted text or a referenced file).
2. Extract only what the source supports:
   - **Decisions**: things agreed or settled, not merely discussed.
   - **Action items**: commitments to do something. Record the owner and due date only if stated; otherwise write "owner not stated" or "no date". Never guess names or dates.
   - **Open questions**: unresolved issues, items deferred, or points needing follow-up.
3. Drop small talk, repeated points, and discussion that led nowhere.
4. Resolve relative dates ("next Friday") only if the meeting date is known; otherwise keep the original wording.

## Output format

Keep the whole output **under 200 words**. Use this structure and omit nothing; write "None" for an empty section.

```
**Meeting:** <title/topic, date if known>
**Summary:** <1-2 sentences>

**Decisions**
- ...

**Action items**
- <Task>: <Owner>, due <date>

**Open questions**
- ...
```

## Rules

- Be terse: one line per item, no filler.
- If the content would exceed 200 words, merge minor items and keep the most consequential ones.
- If attribution is ambiguous (unclear speaker, unclear assignee), say so rather than infer.
- Do not add information that is not in the source.
