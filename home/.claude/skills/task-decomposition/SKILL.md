---
name: task-decomposition
description: "Take a feature, plan or design doc and break it into a sequenced list of small, mergeable tickets. Use when a plan spans multiple layers, multiple weeks, or when the user asks to 'break this down' / 'split into tickets' / 'subdivide tasks'."
---

# Task Decomposition

## Overview

Convert a high-level plan into an ordered backlog of small tickets. Each ticket is a complete unit of value (no partial PRs that only make sense once a later one merges) with explicit scope, testable acceptance, and dependencies. Output is a markdown doc engineers can execute one ticket at a time.

This skill produces docs, not code. After running it, hand off the resulting tickets file to the implementing skill (TDD, refactor, etc.) one ticket at a time.

## When to use

- A plan / design doc spans multiple layers (backend + frontend + infra) or multiple weeks.
- The user says "break this down", "split into smaller tickets", "subdivide", or asks for a backlog.
- A milestone bundle has more than ~6 atomic changes.
- After `brainstorming` produces a design doc and you need to schedule the work.

## When NOT to use

- A single-file, sub-1-hour change. Just do it.
- Pure exploration / research with no concrete deliverables yet — run `brainstorming` first.
- The plan is already presented in ticket form. Read it as is.
- The plan is one ticket. Skip the skill.

## Process

You MUST execute these steps in order.

### 1. Read the source plan completely
Don't skim. If the source is a design doc, read every section. If it's a verbal description, restate it back to the user before decomposing.

### 2. Identify slices of value
List capabilities a user, operator, or developer gains when each ticket merges. A ticket whose merge changes nothing observable is a smell — either it's a refactor that should ride along with a feature, or it's pure scaffolding (combine with the first feature it enables).

### 3. Map dependencies
Note which tickets prerequisite which. Surface at most one critical path. If you find a tangled DAG, you probably have phases that should be done sequentially — group those into milestones.

### 4. Size each ticket
Target: 1-4 hours of focused engineering. If bigger, decompose further. If smaller, merge with the next related one. Reject tickets that smell like "wire everything up" — those almost always hide complexity.

### 5. Write each ticket with these fields

```markdown
### T<n> — <imperative-verb outcome>
**Why**: 1-2 sentences pointing to the design doc / risk mitigated / user pain.
**Scope**:
- In: <bullet list>
- Out: <explicit exclusions to prevent scope creep>
**Acceptance**:
- <testable criterion 1>
- <testable criterion 2>
**Depends on**: <T<m>, T<k> | none>
**Risks / notes**: <known unknowns, edge cases, follow-ups>
**Estimate**: ~Xh
```

Imperative title: "Add scheduling type to Tareas model" not "Scheduling type". Acceptance must be observable — not "looks good", "is clean", "works well". Estimates are budgets, not promises.

### 6. Sequence into milestones

Group adjacent tickets that ship together as user-visible value. Each milestone gets a one-line outcome ("Provider can start a service only when at the location and inside the scheduled window"). Milestones make planning conversations possible without re-reading every ticket.

### 7. Apply sanity gates before declaring done

Run each gate over the ticket list:

- **Solo-executable**: could a new engineer execute each ticket given the doc + design doc, without needing a conversation? If no, add detail.
- **Single concern**: would each ticket require >1 reviewer with different expertise to merge? If yes, split.
- **Testable acceptance**: each criterion written so a human can mark pass/fail by inspection or by running a command? If not, refine.
- **Vertical slices preferred**: when possible, each ticket touches the layers needed to ship one capability end-to-end. Resort to horizontal slicing (one ticket = one layer) only when a layer truly is a hard prerequisite for everything else (e.g., a schema migration before any feature consumes it).
- **Optional tickets flagged**: any "we'd skip this if pressed" tickets marked `(optional)` so MVP cuts are obvious.

## Output format

Write to `docs/plans/YYYY-MM-DD-<topic>-tickets.md`:

```markdown
# <Topic> — ticket breakdown

Source plan: [<doc>](<relative-path>)
Date: YYYY-MM-DD
Status: ready for execution

## Milestones

- **M1** (<outcome>): T1, T2, T3
- **M2** (<outcome>): T4, T5
- ...

## Tickets

### T1 — <imperative title>
...

### T2 — ...
```

Commit the file. The implementer picks tickets in order.

## Anti-patterns

| Smell | Fix |
|---|---|
| `T1: backend; T2: frontend; T3: tests` | Vertical slices, not horizontal layers. Each ticket should ship a thin user-visible capability *with* its tests. |
| `T1: scaffold the module; T2: actually build it` | Scaffolding alone is not a unit of value. Combine. |
| Acceptance reads "looks reasonable" | Replace with observable behavior + commands to verify. |
| Ticket > 4 hours | Decompose further. |
| Milestone > 12 tickets | Subdivide the milestone — it's really two. |
| No "Out:" section | Scope creeps in review. Always state what's NOT included. |
| Every ticket depends on every other | Re-read; usually means tickets are fragments of one work item. |
| Mixing "must" tickets with "would be nice" tickets without flagging | Mark optional ones explicitly so cuts are easy. |

## Hand-off rule

When done, **stop**. Do not start implementing. Hand the doc back to the user with a short summary (count of tickets per milestone, total estimate, critical path, optional cuts). Implementation belongs to TDD / refactor / frontend-design / etc., one ticket at a time.
