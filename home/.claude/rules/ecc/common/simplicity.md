# Simplicity and Anti-Over-Engineering

> Extends the KISS / DRY / YAGNI principles in [coding-style.md](./coding-style.md)
> with an enforceable procedure, and [code-review.md](./code-review.md) with a
> dedicated over-engineering review pass.

> **Language note**: the file-count guidance may be overridden by language-specific
> rules for languages whose idiom favors larger units (e.g. Go packages).

## The Ladder

Before writing code, stop at the first rung that holds:

1. **Does this need to exist at all?** Speculative need = skip it, say so in one line.
2. **Does the codebase already have it?** A helper, type, or pattern a few files over. Look before writing — re-implementing what already exists is the most common defect.
3. **Does the standard library do it?** Use it.
4. **Does a native platform feature cover it?** Platform primitive over application code, declarative constraint over imperative check.
5. **Does an already-installed dependency solve it?** Use it. Never add a new dependency for what a few lines cover.
6. **Can it be one line?** One line.
7. **Only then**: the minimum code that works.

The ladder runs *after* understanding the problem, never instead of it. Read the
task and trace the real flow first, then climb. A minimal diff in the wrong place
is not simplicity — it is a second defect.

## Mandatory Triggers

Apply this rule before:

- Adding any new dependency
- Creating an interface, abstract base, factory, builder, or wrapper
- Adding a new file or module
- Introducing a config option, feature flag, or extension point
- Any request phrased as "make it extensible", "future-proof", or "configurable"
- Any diff that grows well past the size the task implies

## The Floor: What Is Never Simplified Away

Simplicity governs *how much you build*, never *what you verify*. Never remove or
defer:

- Input validation at trust boundaries
- Error handling that prevents data loss
- Any control required by [security.md](./security.md)
- Accessibility basics
- Behavior the user explicitly requested

## Precedence

Per [README.md](../README.md), specific overrides general. This rule governs
solution shape only.

| Conflict | Winner |
|----------|--------|
| Test coverage, TDD cycle, required test types | [testing.md](./testing.md) — always |
| Security, validation, secret handling | [security.md](./security.md) — always |
| Abstractions, dependencies, scaffolding, layering | this rule |
| Process weight on trivial changes | this rule (see Proportionality) |

Never invoke simplicity to justify skipping a test, a validation, or a review.
"Lazy" describes the solution, never the verification.

## Files: Floor and Ceiling

[coding-style.md](./coding-style.md) sets a **ceiling** — 200-400 lines typical,
800 maximum. This rule sets a **floor**: do not create a file until it owns a
distinct responsibility. Both hold at once. The target is the fewest files that
each stay under the ceiling and each justify their own existence.

## Proportionality of Process

[development-workflow.md](./development-workflow.md) defines the full pipeline:
research and reuse, planner, TDD, code review. Run it in full for features,
refactors, and anything hitting a security trigger from
[code-review.md](./code-review.md).

For a one-line fix, a config value, or a change with no behavioral surface, the
pipeline itself is over-engineering: make the change, run the existing tests,
done. Scaling ceremony to risk is part of this rule, not an exception to it.

## Over-Engineering Review Pass

Run alongside the checklist in [code-review.md](./code-review.md):

- [ ] Any interface or abstract type with exactly one implementation?
- [ ] Any factory, builder, or wrapper around a single concrete type?
- [ ] Any config option, flag, or parameter that no caller ever varies?
- [ ] Any new dependency doing what the stdlib or an installed dependency does?
- [ ] Any hand-rolled utility duplicating something already in the repo?
- [ ] Any scaffolding, hook, or extension point with no current consumer?
- [ ] Any layer that only forwards calls without adding behavior?
- [ ] Any generality justified only by "we might need it later"?

## Severity Mapping

Uses the levels defined in [code-review.md](./code-review.md):

| Finding | Level |
|---------|-------|
| Reimplemented stdlib, or an existing repo helper | HIGH |
| Speculative subsystem or abstraction with no consumer | HIGH |
| New dependency replaceable by stdlib or an installed one | MEDIUM |
| Dead flexibility: unused options, flags, or parameters | MEDIUM |
| Pass-through layer adding no behavior | MEDIUM |
| Naming, minor duplication, cosmetic indirection | LOW |

Over-engineering is never CRITICAL — that level is reserved for security and data
loss. It blocks nothing on its own; it is fixed before the debt compounds.

## Deliberate Shortcuts

A simplification that cuts a real corner with a known ceiling (a global lock, an
O(n^2) scan, a naive heuristic) is legitimate, but must be marked in place with a
`ponytail:` comment naming the ceiling and the upgrade path.

The marker is greppable and the `ponytail-debt` skill harvests every occurrence
into a ledger, so deferrals stay tracked instead of rotting into "later means
never". An unmarked shortcut is not a simplification — it is an undocumented
defect.

## Skill and Agent Support

Rules define the standard; skills carry the procedure.

| Skill | Use |
|-------|-----|
| `ponytail` | Persistent simplicity mode while building. Levels: lite, full, ultra |
| `ponytail-review` | Over-engineering review of a diff |
| `ponytail-audit` | Over-engineering audit of a whole repository |
| `ponytail-debt` | Harvest `ponytail:` markers into a debt ledger |

Pair with the **code-reviewer** agent for correctness and the **refactor-cleaner**
agent for removing what this rule identifies.
