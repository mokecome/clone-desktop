# UI Extraction Reference

The desktop equivalent of DOM + `getComputedStyle` extraction. The **UI Automation control tree is the source of truth**; screenshots are secondary; for custom-drawn regions, vision + OCR is the only source (and must be marked as such). Every screen/component gets a spec file in `docs/research/components/*.spec.md` before implementation.

## What to extract per element

For each UIA element capture:

- `ControlType` (Button, Edit, DataItem, TreeItem, TabItem, MenuItem, Pane, Text, …)
- `Name`, `AutomationId`, `ClassName`
- `BoundingRectangle` (x, y, width, height) — for layout/order, but prefer name-based targeting in the rebuild
- supported **patterns** (Invoke, Value, Toggle, ExpandCollapse, Selection, Grid, Table, Scroll, RangeValue) — these reveal the control's real behavior
- state: `IsEnabled`, `IsOffscreen`, checked/selected/expanded
- for text/values: the actual `Value`/`Name` string (verbatim)

## Dump the tree

Fastest path: `python scripts/dump_tree.py "<window title>" <max_depth> <out_file>` (bundled, UTF-8-safe) writes the tree straight to a spec file. The equivalent inline code, when you need to customize the walk:

### Custom walk (Python-UIAutomation)

```python
import uiautomation as auto

def dump(ctrl, depth=0, max_depth=12):
    info = {
        "type": ctrl.ControlTypeName,
        "name": ctrl.Name,
        "autoId": ctrl.AutomationId,
        "class": ctrl.ClassName,
        "rect": (ctrl.BoundingRectangle.left, ctrl.BoundingRectangle.top,
                 ctrl.BoundingRectangle.width(), ctrl.BoundingRectangle.height()),
        "enabled": ctrl.IsEnabled,
        "offscreen": ctrl.IsOffscreen,
    }
    print("  " * depth + f"{info['type']} '{info['name']}' [{info['autoId']}] {info['rect']}")
    if depth < max_depth:
        for child in ctrl.GetChildren():
            dump(child, depth + 1, max_depth)

win = auto.WindowControl(searchDepth=1, Name='<app window title>')
dump(win)
```

pywinauto equivalent: `app.window(...).print_control_identifiers()` (also lists usable selectors).

Save each screen's raw dump under `docs/research/screens/<screen>.uia.txt`, then distill it into the spec. Never hand-write a tree you did not dump.

## Electron windows — use the DOM instead

If `TECH.md` says Electron and remote debugging is reachable, attach via CDP and extract real DOM + `getComputedStyle` exactly like `clone-website` (reuse its extraction script). This gives pixel-exact colors, spacing, fonts, and text — far better than UIA for these windows.

## Custom-drawn regions — vision fallback

When the tree under a region is empty (timeline, preview canvas, game view), you cannot read structure from UIA:

1. Screenshot the region at known DPI.
2. Use OCR for any text labels; measure layout from the image.
3. Record it in the spec as **vision-only** with the evidence screenshot.
4. Reproduce it as a best-effort visual with a labeled placeholder for interactive internals you could not observe. NEVER invent its internal widgets.

## Visual tokens

Extract the app's theme so the clone matches: dominant colors (sample from screenshots or, for Electron, `getComputedStyle`), title-bar/menu/toolbar colors, accent color, fonts (from Electron CSS, or best-effort from screenshots for native), corner radii, and spacing rhythm. Record in a `theme.spec.md`.

## Spec template

Create `docs/research/components/<screen-or-component>.spec.md`:

```markdown
# <Screen/Component> Specification

## Overview
- Target clone file: `src/.../<Name>.tsx` (or chosen stack)
- Source screen: SCREENS.md row #<n>
- Evidence: `docs/research/screens/<screen>.uia.txt`, `docs/design-references/<...>.png`
- Extraction source: UIA tree | Electron DOM | vision-only
- Interaction model: static | click-driven | drag-driven | hover-driven | time-driven | mixed
- Packages used: <package(s) adopted, or "hand-rolled — no suitable package found: <candidates & reason>">

## Structure
Element hierarchy from the UIA dump (or DOM): container → panels → controls, in order.

## Controls
For each: ControlType, Name/label (verbatim), AutomationId, patterns, state, position/order.

## Layout
Panel docking, split positions, toolbar placement, column order — measured, not guessed.

## Dialog / form fields (if any)
label | control type | required | default | read-only/auto | validation observed

## States & behaviors
Trigger → before → after → transition → implementation approach. Include hover/checked/disabled, drag (splitter/reorder/timeline), and multi-step sequences (open → edit → apply → result).

## Text content
Verbatim visible labels, menu items, tooltips.

## Assets
Icons/images (reproduce or placeholder if proprietary), fonts.

## Theme
Colors, fonts, radii, spacing relevant to this screen.
```

## Pre-implementation checklist

- Spec file exists and is filled from a real tree dump / DOM / labeled vision capture.
- Extraction source is stated (UIA / DOM / vision-only).
- Every control lists its ControlType, label, and patterns.
- Package-first decision recorded (adopted package, or why none fits).
- Layout/column/field order comes from observation, not the screen title.
- Custom-drawn regions are marked vision-only, not invented.
- Build/typecheck command is known.
