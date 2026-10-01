# UX Conventions

> Mandatory UI/UX reference for frontend work.
> Last updated: 2026-09-08.

This document only covers user experience and interface conventions: controls,
layout, interaction, visual states, copy, accessibility, and navigation.

For React Query/cache/optimistic UI/data connectivity, read
[engineering.md](./engineering.md).
For API/security/testing/deployment, read [../README.md](../README.md).

If a PR violates these conventions, it gets rejected unless the deviation is
explicitly justified and approved.

**On the vocabulary used here.** Examples name components and classes from a
Tailwind + shadcn/ui vocabulary, because that is the usual starting stack. They
are illustrations, not requirements: a project built on plain CSS, its own token
system, or another component library satisfies these rules with its own
equivalents, and declares the mapping in its `AGENTS.md` (`## Conventions`). What
is mandatory is the behaviour each rule describes — the affordance, the state,
the feedback — never the import path.

---

## 1. Input Controls — Never Use Free Text For Closed Values

**The rule:** if valid values come from a backend catalog or closed enum, do not
use `Input type="text"` or `Input type="number"`. Use a picker, combobox, or
`Select`.

| Value category | Control to use |
|---|---|
| Entity from a backend catalog or list (single) | Search-driven picker/combobox, not free text or a raw id |
| Entity from a backend catalog or list (multiple) | Multi-select picker/combobox |
| Closed enum: status, type, severity, classification | `Select` |
| Boolean setting | `Switch` |
| Single date | `Calendar` + `Popover` |
| Date range | `Calendar` with `mode="range"` |
| Dependent/cascading catalog value (one selection narrows the next) | Cascading picker/combobox, each level reading its own catalog |

The concrete component for each category — which picker, which combobox, which
endpoint it reads — is the project's to declare, in its `AGENTS.md` (section
`## Conventions`) or in the README that serves that role. If the project has
not declared this mapping, that is the first finding: surface it before
building more closed-value inputs ad hoc.

`Input` is acceptable only for genuinely free values: names, descriptions,
notes, street address, email, phone, open numeric quantities such as hours or
amounts.

### Picker Contract

Every picker must provide:

- Search by human text, not only by raw id.
- Human primary label (`fullName`, `name`, `code + name`), never id as label.
- Optional secondary metadata for disambiguation.
- Loading, empty, error, disabled, and clearable states where applicable.
- Keyboard navigation and `aria-label`.
- Internal id value returned to the parent without making the user type it.

---

## 2. Primary Create Actions — Use FAB Consistently

The action that creates the page's primary collection resource lives in a
floating action button, positioned bottom-right. Which component provides it is
the project's to declare.

Examples (illustrative pattern, not specific routes):

- A collection list route (e.g. a list of records) -> FAB creates the primary
  resource.
- A detail route for one item in that collection -> no FAB; use contextual
  section actions instead.

Header buttons are for filters, exports, view toggles, or context-specific
actions, not for duplicating the FAB.

Do not add a visible "Actualizar"/"Refresh" button unless the data depends on
an external process where the user genuinely needs to poll. Normal
server-state refresh is a frontend engineering concern, not a visible
workaround.

---

## 3. Forms And Dialogs

### Layout

- Forms with 5 fields or fewer use one column.
- Forms with 6 or more fields use two columns from `md:` upward.
- Required fields show a red `*` next to the label.
- Submit button sits bottom-right; Cancel sits to its left.
- Primary action is filled; secondary action is `variant="outline"`.
- Do not place an input and button in the same `flex items-end` row unless the
  input has its own label and reserved helper/error space.

### Validation And Feedback

- Field errors appear below the field, in the project's error text style.
- Required validation happens on submit, not on blur.
- Backend errors become user-facing copy in the project's default language,
  not raw `error.message`.
- During submit, the primary button shows a spinner plus a state label
  ("Guardando...", "Creando...", or the project's equivalent).
- Disable the form during submission.

### Helper Text

- Helper text belongs inside the field column, below the control.
- Tooltips belong on a `?` icon next to the label.
- Empty-state hints such as "select the parent record first" belong where the
  dependent content would appear, not under a random input in the grid.
- Helper text must not push sibling inputs out of alignment.

### Ambiguous Fields Are Not Allowed

If the label does not explain the business consequence, stop and clarify.

Bad:

- `Obligatorio?`
- `Tipo`
- `Estado`

Good:

- `Requerido para completar el registro`
- `Determina qué plantilla de notificación se usa`
- `Estado de la solicitud`

---

## 4. Loading Visuals

Use the project's skeleton component for page, panel, table, card, and form
loading states.

- Full-page loads: skeleton matching final layout.
- Tables: row skeletons.
- Cards: card skeletons.
- Forms: field skeletons.
- Avoid centered generic spinners on full pages.

Data ownership and cache behavior are defined in
[engineering.md](./engineering.md).

---

## 5. Empty States

Every empty list, table, or panel must explain what's missing and what to do.

Required ingredients:

1. Icon from `lucide-react`, usually `text-muted-foreground/40`.
2. One contextual sentence, not just "Sin resultados".
3. One next step: CTA, hint pointing to FAB, or clear-filters action.

Bad:

```tsx
<p>No results found.</p>
```

Good (illustrative content — swap the noun and copy for the real resource):

```tsx
<EmptyState
  icon={<FolderOpen className="h-10 w-10 text-muted-foreground/40" />}
  title="Sin proyectos creados todavía"
  description="Crea el primer proyecto para empezar a trabajar."
  cta={<Button onClick={onCreate}>Nuevo proyecto</Button>}
/>
```

Build a shared `EmptyState` component if the pattern is needed more than twice.

---

## 6. Tables

Use the project's table component for CRUD/list pages; do not roll custom
tables. The project declares its table component (and any separate
toolbar/filter pieces) in its `AGENTS.md` (`## Conventions`) or equivalent
README; if it hasn't, that's the first finding.

Required affordances:

- Global filter when more than 5 rows are possible.
- Sorting on at least one useful column.
- Row actions behind an overflow menu, not a row of naked icons.
- Pagination with rows-per-page selector.
- Table empty state following section 5.

---

## 7. Filters And Search

- Use selects/pickers for enum, catalog, and entity filters.
- Never ask users to type raw ids as filters.
- Add "Limpiar filtros" when multiple filters can be active.
- Use debounced search for free-text search.
- Empty results caused by filters should offer to clear filters.
- Filter controls must not erase unrelated in-progress form work.

URL persistence and query keys are defined in
[engineering.md](./engineering.md).

---

## 8. Navigation

### Sidebar

Top-level modules are defined once in the app shell. New top-level modules need
a sidebar entry.

### Module Tabs

Horizontal module nav belongs in the module's own layout component (e.g. a
`<Module>Layout.tsx` file), not scattered across pages. Labels use
`t('module.nav.<id>')`; do not hardcode tab labels when the module already
uses i18n.

### Breadcrumbs

Breadcrumbs must match real route hierarchy. Do not show breadcrumb nodes that
are not clickable routes unless they represent the current page.

---

## 9. Toasts And Notifications

Use the project's toast mechanism for transient feedback.

| Situation | Component |
|---|---|
| Mutation succeeded | `toast.success("Registro creado")` (illustrative copy) |
| Network/validation error | `toast.error("No se pudo guardar el registro")` (illustrative copy) |
| Persistent blocking error | `<Alert variant="destructive">` |
| Destructive confirmation | `<AlertDialog>` |
| Per-row warning | `<Badge variant="warning">` |

Never use native `alert()`, `confirm()`, or `prompt()`.

---

## 10. Color And Severity Language

| Concept | Semantic role |
|---|---|
| Success / Active / Available | positive |
| Warning / In-progress | warning |
| Error / Blocked / Severity HIGH | danger / destructive |
| Info / Neutral | informational |
| Suspended / Disabled | muted / inactive |
| Severity MEDIUM | same family as warning |
| Severity LOW | same family as suspended/disabled |

The concrete values for each semantic role — Tailwind classes, CSS variables,
or design tokens — are defined by the project's design system, declared in its
`AGENTS.md` (`## Conventions`), its README, or its theme/token file. A
dark-themed product with its own token system uses its tokens here, not a
light-mode Tailwind palette borrowed from elsewhere. If the project hasn't
declared this mapping, that's the first finding.

Status pills use `Badge` with `variant="outline"` plus the project's styling
for the matching semantic role. Color is never the only signal; pair it with
text or an icon (see section 12).

---

## 11. Internationalization

The default language is declared by the project — in its `AGENTS.md`
(`## Conventions`) or README. Do not hardcode a different language than the
project's declared default (e.g. do not hardcode English copy into a
Spanish-first product).

If the project supports more than one language, every user-facing string must
go through `t()`, and the dictionaries must not diverge — no key missing in
one locale that exists in another. Enforce this with a test if the project
doesn't already have one.

Use `t()` for shared/strategic strings such as nav and common actions.
Hardcoded strings in the project's default language are acceptable for page
bodies only when the module already follows that convention consistently.

Display dates and numbers with the project's locale formatting. Example
(Spanish/Colombian shown only as illustration — use the project's actual
locale):

```ts
format(date, 'PPP', { locale: es });
new Intl.NumberFormat('es-CO').format(1234);
```

Payload date semantics are defined in [engineering.md](./engineering.md).

---

## 12. Accessibility

- `aria-label` on icon-only buttons.
- Visible focus rings.
- Tab order matches visual order.
- Escape closes dialogs.
- Enter submits forms when appropriate.
- Empty states announce meaningful text.
- Color is never the only signal; pair color with text or icon.

---

## 13. UX Pre-Merge Checklist

Before requesting review on frontend UI changes:

- [ ] No raw id or enum text inputs.
- [ ] Dates use `Calendar` + `Popover`, not text/date inputs.
- [ ] Primary create action uses FAB where the page is a collection.
- [ ] No unnecessary visible "Actualizar"/"Refresh" button.
- [ ] Required fields marked with `*`.
- [ ] Submit/cancel placement follows dialog convention.
- [ ] Helper text does not break layout alignment.
- [ ] Loading states use skeletons.
- [ ] Empty states have icon, context, and next step.
- [ ] Tables use the project's table component and expected affordances.
- [ ] Filters use selects/pickers and include clear action.
- [ ] Transient feedback uses the project's toast mechanism, not an ad-hoc one.
- [ ] User-facing copy matches the project's declared default language, and
      i18n dictionaries (if any) don't diverge.
- [ ] Color/severity follows section 10.
- [ ] Icon-only buttons have `aria-label`.
- [ ] Desktop and mobile/narrow layouts were visually checked.

---

## 14. When In Doubt

1. Search for an existing component or pattern before building a new one.
2. If you must deviate, document why in the PR.
3. If the convention is wrong, update the convention first.

---

## Appendix: Component Gaps

Each project maintains its own list of UI component gaps (missing pickers,
missing shared components) where it declares its conventions — typically its
`AGENTS.md` or a project-local doc. This file does not track per-project
component inventories.
