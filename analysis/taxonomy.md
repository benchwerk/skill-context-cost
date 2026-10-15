# Taxonomy of skills

Two independent axes, one label each per skill, plus a clarity score. Labels are given by reading the skill's own text
against these definitions; counted features (size, files, flags) are in `skill_features.json` and are not part of the labels.

## Domain: what the skill is about

| Code | Domain | Examples of the kind |
| :-- | :-- | :-- |
| D1 | software-process | planning, debugging, test-driven development, code review, refactoring, git workflow, hand-off between sessions |
| D2 | frontend-ui-design | interface and visual design guidance, design systems, animation, UI best practice |
| D3 | platform-reference | documentation-like knowledge of a cloud service, database, framework or SaaS (Azure, Firebase, Prisma, Supabase, Stripe) |
| D4 | tool-operation | operating one specific command-line tool, browser or application on the user's behalf |
| D5 | media-generation | image, video, audio or music generation through a model or service |
| D6 | business-marketing | SEO, copywriting, funnels, analytics, sales |
| D7 | office-documents | documents, slides, spreadsheets, notes, workplace suites |
| D8 | agent-meta | skills about skills, agent behaviour or style, orchestration of agents, memory |
| D9 | other | none of the above |

## Form: how the skill works

| Code | Form | Meaning |
| :-- | :-- | :-- |
| F1 | procedure | ordered steps or a workflow to follow |
| F2 | reference | facts, APIs or documentation to look up |
| F3 | rules-and-style | constraints, conventions, taste the agent must apply |
| F4 | tool-wrapper | teaches the commands and options of a tool |
| F5 | persona-or-mode | changes how the agent talks or behaves in general |
| F6 | stub-pointer | very short; the real content lives elsewhere (a command, a URL, other files) |

## Trigger clarity (from the description only)

3 = states concrete situations that should trigger it and where it stops; 2 = states what it does but triggers only
partly; 1 = vague, a title, or generic marketing text.

Rules: choose the single best label per axis; if two fit, choose the one that describes most of the body.
