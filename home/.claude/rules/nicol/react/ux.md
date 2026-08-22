# UX Conventions

> Mandatory UI/UX reference for frontend work.
> Last updated: 2026-05-18.

This document only covers user experience and interface conventions: controls,
layout, interaction, visual states, copy, accessibility, and navigation.

For React Query/cache/optimistic UI/data connectivity, read
[docs/conventions/frontend-engineering-conventions.md](conventions/frontend-engineering-conventions.md).
For API/security/testing/deployment, read [docs/conventions/README.md](conventions/README.md).

If a PR violates these conventions, it gets rejected unless the deviation is
explicitly justified and approved.

---

## 1. Input Controls — Never Use Free Text For Closed Values

**The rule:** if valid values come from a backend catalog or closed enum, do not
use `Input type="text"` or `Input type="number"`. Use a picker, combobox, or
`Select`.

| Value being captured | Component to use |
|---|---|
| Employee / Auditor | `EmployeePicker` (`src/modules/hr/components/EmployeePicker.tsx`) |
| Country / State / City | `LocationSelector` (`src/components/LocationSelector.tsx`) |
| Job position / Cargo | `JobPositionPicker` or `AutoCompleteSelect` reading `/api/v1/job-positions` |
| Employee type | `EmployeeTypePicker` (build it if missing; reads `employee_types`) |
| Status / Type / Severity / Recommendation | `Select` from `@/components/ui/select` |
| Date | `Calendar` + `Popover` |
| Date range | `Calendar` with `mode="range"` |
| Boolean setting | `Switch` from `@/components/ui/switch` |
| Standard / Norm | Combobox reading `/api/v1/standards` |
| Technical area | Combobox reading `/api/v1/technical-areas` |
| IAF sector | Combobox reading `/api/v1/iaf-sectors` |
| Client | `ClientPicker` (build it if missing; same pattern as `EmployeePicker`) |
| Scheduled audit | `ScheduledAuditPicker` (build it if missing) |

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
`FloatingActionButton` from `@/components/shared`, positioned bottom-right.

Examples:

- `/hr/employees` -> FAB to create employee.
- `/hr/recruitment` -> FAB to create vacancy.
- `/hr/training` -> FAB to create training record.
- Detail routes such as `/hr/recruitment/:id` -> no FAB; use contextual section
  actions.

Header buttons are for filters, exports, view toggles, or context-specific
actions, not for duplicating the FAB.

Do not add a visible "Actualizar" button unless the data depends on an external
process where the user genuinely needs to poll. Normal server-state refresh is a
frontend engineering concern, not a visible workaround.

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

- Field errors appear below the field in `text-destructive`.
- Required validation happens on submit, not on blur.
- Backend errors become Spanish user-facing copy, not raw `error.message`.
- During submit, the primary button shows a spinner plus "Guardando...",
  "Creando...", etc.
- Disable the form during submission.

### Helper Text

- Helper text belongs inside the field column, below the control.
- Tooltips belong on a `?` icon next to the label.
- Empty-state hints such as "seleccione un empleado primero" belong where the
  dependent content would appear, not under a random input in the grid.
- Helper text must not push sibling inputs out of alignment.

### Ambiguous Fields Are Not Allowed

If the label does not explain the business consequence, stop and clarify.

Bad:

- `Obligatoria?`
- `Tipo`
- `Estado`

Good:

- `Requerido para cerrar la brecha`
- `Exige evidencia de asistencia`
- `Estado de la vacante`

---

## 4. Loading Visuals

Use `Skeleton` from `@/components/ui/skeleton` for page, panel, table, card, and
form loading states.

- Full-page loads: skeleton matching final layout.
- Tables: row skeletons.
- Cards: card skeletons.
- Forms: field skeletons.
- Avoid centered generic spinners on full pages.

Data ownership and cache behavior are defined in
[frontend-engineering-conventions.md](conventions/frontend-engineering-conventions.md).

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

Good:

```tsx
<EmptyState
  icon={<Briefcase className="h-10 w-10 text-muted-foreground/40" />}
  title="Sin vacantes creadas todavía"
  description="Crea la primera vacante para que el motor sugiera candidatos."
  cta={<Button onClick={onCreate}>Nueva vacante</Button>}
/>
```

Build a shared `EmptyState` component if the pattern is needed more than twice.

---

## 6. Tables

Use `DataTableRoot` / `DataTableToolbar` / `DataTableUI` from
`@/components/data-table`. Do not roll custom tables for CRUD/list pages.

Required affordances:

- Global filter when more than 5 rows are possible.
- Sorting on at least one useful column.
- Row actions in a `DropdownMenu` triggered by `MoreHorizontal`.
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
[frontend-engineering-conventions.md](conventions/frontend-engineering-conventions.md).

---

## 8. Navigation

### Sidebar

Top-level modules are defined once in the app shell. New top-level modules need
a sidebar entry.

### Module Tabs

Horizontal module nav belongs in the module layout, e.g. `HRLayout.tsx`.
Labels use `t('module.nav.<id>')`; do not hardcode tab labels when the module
already uses i18n.

### Breadcrumbs

Breadcrumbs must match real route hierarchy. Do not show breadcrumb nodes that
are not clickable routes unless they represent the current page.

---

## 9. Toasts And Notifications

Use `sonner` for transient feedback.

| Situation | Component |
|---|---|
| Mutation succeeded | `toast.success("Vacante creada")` |
| Network/validation error | `toast.error("No se pudo guardar la vacante")` |
| Persistent blocking error | `<Alert variant="destructive">` |
| Destructive confirmation | `<AlertDialog>` |
| Per-row warning | `<Badge variant="warning">` |

Never use native `alert()`, `confirm()`, or `prompt()`.

---

## 10. Color And Severity Language

| Concept | Color family | Tailwind classes |
|---|---|---|
| Success / Active / Available | Emerald | `text-emerald-700 bg-emerald-50 border-emerald-200` |
| Warning / In-progress | Amber | `text-amber-700 bg-amber-50 border-amber-200` |
| Error / Blocked / Severity HIGH | Rose | `text-rose-700 bg-rose-50 border-rose-200` |
| Info / Neutral | Sky | `text-sky-700 bg-sky-50 border-sky-200` |
| Suspended / Disabled | Slate | `text-slate-700 bg-slate-100 border-slate-200` |
| Severity MEDIUM | Amber | same as warning |
| Severity LOW | Slate | same as suspended |

Status pills use `Badge` with `variant="outline"` plus the relevant color
classes.

---

## 11. Internationalization

The app defaults to Spanish. All user-facing strings must be Spanish.

Use `t()` for shared/strategic strings such as nav and common actions. Hardcoded
Spanish is acceptable for new HR page bodies when the module already follows
that convention. Do not hardcode English.

Display dates and numbers with Spanish/Colombian formatting:

```ts
format(date, 'PPP', { locale: es });
new Intl.NumberFormat('es-CO').format(1234);
```

Payload date semantics are defined in
[frontend-engineering-conventions.md](conventions/frontend-engineering-conventions.md).

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
- [ ] No unnecessary visible "Actualizar" button.
- [ ] Required fields marked with `*`.
- [ ] Submit/cancel placement follows dialog convention.
- [ ] Helper text does not break layout alignment.
- [ ] Loading states use skeletons.
- [ ] Empty states have icon, context, and next step.
- [ ] Tables use `DataTableRoot` and expected affordances.
- [ ] Filters use selects/pickers and include clear action.
- [ ] Toasts use `sonner`.
- [ ] User-facing copy is Spanish.
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

| Component | Status | Notes |
|---|---|---|
| `EmployeePicker` | Exists | `src/modules/hr/components/EmployeePicker.tsx` |
| `LocationSelector` | Exists | `src/components/LocationSelector.tsx` |
| `ClientPicker` | TODO | Same pattern as `EmployeePicker`; reads CRM clients |
| `ScheduledAuditPicker` | TODO | For post-audit evaluation and audit references |
| `JobPositionPicker` | TODO | Built on `AutoCompleteSelect` |
| `EmployeeTypePicker` | TODO | Uses employee type catalog |
| `StandardPicker` | TODO | Reads `/api/v1/standards` |
| `TechnicalAreaPicker` | TODO | Reads `/api/v1/technical-areas` |
| `IafSectorPicker` | TODO | Reads `/api/v1/iaf-sectors` |
| `EmptyState` | TODO | Shared empty-state shell |
| `MultiEmployeePicker` | Exists | `src/modules/hr/components/MultiEmployeePicker.tsx` — multi-select variant for batch operations (Training sessions, etc.) |

---

## Appendix: Known tech debt — Training sessions (2026-05-19)

The Training sessions module shipped with conscious gaps. They do **not**
block the golden path but should be closed when the trigger condition lands.

| Gap | Trigger to fix | Why deferred |
|---|---|---|
| Session list uses `<button>` rows instead of `DataTableRoot` | When sessions per year exceed ~20 (users need search/sort/pagination) | Same pattern as Recruitment; fine for low volume; avoids overengineering an MVP feature |
| No "Edit session" dialog (only create/cancel) | First user request to correct a typo or shift a date on a PLANNED session | Backend `PUT /sessions/{id}` already exists; UI is a quick follow-up. For now HR cancels + recreates |
| No exhaustive `aria-label` audit or keyboard-nav test on attendance toggles | A11y compliance push, or first screen-reader user complaint | Toggles are buttons inside a fieldset-equivalent context; basic keyboard works via Tab. Not formally verified |
| Read-only state on closed sessions visually shown via `disabled={!isMutable}` but not explicitly tested with multi-attendee mixed states | When closing a session with > 1 attendee in mixed ATTENDED/NO_SHOW config in production | Service-layer logic covered by unit tests; UI render path lightly different |

Triggers — not deadlines. If the use case never materialises, the debt
stays parked. If it does, refer to this list as the starting point.
