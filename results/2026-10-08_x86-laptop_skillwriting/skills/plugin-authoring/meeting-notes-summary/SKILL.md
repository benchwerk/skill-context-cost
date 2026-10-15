---
name: meeting-notes-summary
description: Turn raw meeting notes or a transcript into a short summary of decisions, action items (owner and due date when stated) and open questions, under 200 words. Use when the user pastes or points to meeting notes, a transcript, or asks to summarize a meeting.
---

# Meeting Notes Summary

Condense raw meeting notes or a transcript into a summary of **under 200 words**.

## Steps

1. Read the full input (pasted text or the file the user names).
2. Extract only what was concluded, assigned, or left unresolved. Drop small talk, tangents, and play-by-play.
3. Write the summary in the format below.

## Output format

```
**Decisions**
- <decision, one line>

**Action items**
- <task> — <owner>, due <date>

**Open questions**
- <question or unresolved issue>
```

## Rules

- Keep the total under 200 words. Cut the least important items first.
- Give an owner and due date only when the notes state them. Never invent either. Use "owner unassigned" or omit the due date when missing.
- Keep dates as written in the notes; do not convert relative dates unless the meeting date is given.
- Put an item under Decisions only if the group actually agreed. Proposals without agreement go under Open questions.
- If a section has nothing, write "None stated".
- Do not add a title, preamble, or closing remarks. Do not ask follow-up questions; summarize what is there.
