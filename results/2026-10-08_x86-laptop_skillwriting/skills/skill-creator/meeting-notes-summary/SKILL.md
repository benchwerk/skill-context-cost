---
name: meeting-notes-summary
description: Turn raw meeting notes or a transcript into a concise summary listing decisions, action items (with owner and due date when stated) and open questions, in under 200 words. Use this skill whenever the user pastes or points to meeting notes, a call transcript, a standup log, or a recording summary and asks to summarize it, extract action items, recap decisions, or write up "what happened" in a meeting, even if they don't say "summary".
---

# Meeting notes summary

Readers of a meeting summary want to know three things: what was decided, who must do what, and what is still unresolved. Everything else is noise, so cut it.

## Process

1. Read the full notes or transcript. If given a file path, read the file.
2. Separate decisions (things agreed) from discussion (things only talked about). Do not promote a suggestion to a decision unless the group clearly agreed.
3. Capture action items: the task, the owner, and the due date only if one was stated. Write "owner not stated" or omit the date rather than guessing; an invented owner or deadline is worse than a gap.
4. Capture open questions: issues raised but left unresolved, or items needing follow-up information.
5. Write the summary using the format below.

## Output format

Use exactly this structure, omitting a section's bullets with "None noted" if empty:

**Meeting:** <topic/date if known>

**Decisions**
- ...

**Action items**
- <Task> — <Owner>, due <date>

**Open questions**
- ...

## Constraints

- Keep the whole summary under 200 words. Count before replying; trim the least consequential bullets first, and merge related items.
- One line per bullet, plain wording, no filler or attendee-by-attendee recap.
- Use names exactly as they appear in the notes. Keep relative dates ("next Friday") as stated unless the meeting date is known, in which case add the resolved date.
- Do not add information that is not in the source.
