# Visual QA Reference

Use this before declaring a desktop clone complete. The desktop counterpart of clone-website's visual QA: coverage first, then operation-flow fidelity, then per-screen visual diffing.

## Screen coverage (check this first)

Catches silently-dropped windows/dialogs.

1. Open `docs/research/SCREENS.md`.
2. For each original screen, confirm a corresponding clone screen exists and renders (real or clearly-labeled placeholder) and is reachable **through the clone's own navigation**, not just by jumping to it directly.
3. Mark each row `done` / `placeholder` / **`missing`**. Any `missing` row is a blocker: build it, or get explicit user sign-off to drop it.
4. Verify the hierarchy matches: menus still open their submenus, hubs still show their panels, wizards keep their steps. A multi-step dialog flattened into one page is a coverage failure even if it looks right.
5. Record the tally (e.g. "38/40 done, 2 placeholder, 0 missing") in the completion report.

A clone where every built screen is pixel-perfect but whole dialogs are absent is NOT complete.

## Operation-flow fidelity (Faithful screens)

For every screen marked Faithful, open original and clone side by side and verify:

- **Menu bar / toolbar / ribbon** matches: same items, labels, order (including secondary/overflow items).
- **Panels / docking** matches: same panels, same placement, same splitters.
- **Tree / list / grid** matches: same columns in the same order, same headers, same row actions.
- **Dialog / wizard flow** matches: opens the same way (separate window vs in-place panel), same sections, same fields (incl. read-only/auto), same step sequence.
- **Drag interactions** match where they define the app (splitter drag, list reorder, timeline drag) — reproduce the behavior, or mark the gap.

Record mismatches in `QA_DIFFS.md` with `dimension: operation-flow`. A Faithful screen that merely "achieves the same outcome" with a different layout/fields/flow is a fidelity failure. (Functional-equivalent screens are exempt — verify only that they work.)

## Per-screen visual diffing

- Compare original vs clone screenshots per window at the app's real size(s). If the target has resize/responsive behavior, capture it at the sizes it changes.
- For custom-drawn regions (vision-only in extraction), compare the best-effort visual and record remaining gaps honestly — do not claim fidelity you could not measure.

## Screenshot naming

Save under `docs/design-references/qa/`:

```text
<appname>__<original|clone>__<window-or-state>.png
```

Examples:

```text
jianying__original__main-window.png
jianying__clone__main-window.png
jianying__clone__export-dialog.png
```

## Minimum checks

Do not complete until these pass or are recorded as known gaps:

- Every screen in `SCREENS.md` has a reachable clone counterpart (no `missing` rows); hierarchy preserved, not flattened.
- Each screen renders and is not blank.
- No local icon/image/font asset missing (proprietary assets shown as intentional placeholders, noted as such).
- No text overflow or clipped labels; no incoherent overlap; no broken interactive state.
- Menu/toolbar/panel/dialog/drag/hover states match `BEHAVIORS.md`.
- Layout matches `APP_TOPOLOGY.md`.
- Build/typecheck passes after QA fixes (real output in the same turn).

## QA diff log

Record in `docs/research/QA_DIFFS.md`:

```markdown
# QA Diffs

## <screen-or-state>
- Screen: SCREENS.md row #<n>
- Dimension: coverage | operation-flow | visual | behavior | asset
- Expected (original):
- Actual (clone):
- Evidence: docs/design-references/qa/<...>.png
- Likely cause: spec gap | implementation mismatch | asset placeholder | custom-drawn unmeasurable | tool/runtime difference | unknown
- Fix status: open | fixed | accepted gap
```

## Fix loop

1. Check the spec. If wrong/incomplete, re-extract the original (re-dump the tree / re-attach CDP), update the spec, then fix.
2. If the spec is right but implementation diverged, fix the implementation.
3. Re-run the relevant screen/interaction check.
4. Re-run build/typecheck after fixes.

Only report completion after QA has been performed and remaining gaps are documented. Every QA claim must trace to a real screenshot/tree dump from this session — never describe a screenshot you did not receive (see SKILL.md Grounding).
