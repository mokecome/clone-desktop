# Window Discovery Reference (do this before building)

The desktop equivalent of route discovery. Enumerate every window, dialog, panel, menu, and context menu BEFORE extracting or building. Produce `docs/research/SCREENS.md` and `docs/research/APP_TOPOLOGY.md`.

## Required outputs

- `docs/research/SCREENS.md` — full recursive screen inventory (produce FIRST)
- `docs/research/APP_TOPOLOGY.md` — tree: module → window → panel/dialog → state
- `docs/research/BEHAVIORS.md` — interaction model per screen
- `docs/design-references/<appname>__original__<window-or-state>.png` — per discovered screen

## Why apps lose screens

Most missed-screen bugs come from treating the app as "the buttons in the main toolbar." Real surfaces hide behind: menu bars and submenus, ribbon tabs, dockable tool windows, right-click context menus, toolbar overflow menus, preference/settings dialogs (often a tree of pages), wizards (multi-step), and modal editors that open as separate top-level windows. Enumerate the whole tree first.

## Discovery loop

1. Launch the app in the correct state (logged in / a project open, if the target needs it).
2. Enumerate top-level windows from the **desktop root**, not just the main HWND (Electron and native apps both spawn extra windows):
   - Python-UIAutomation: `auto.GetRootControl()` then walk children; or
   - pywinauto: `Desktop(backend="uia").windows()`.
3. Maintain a queue of "screens to visit" and a set of "seen" (keyed by window title + `AutomationId` + control-tree signature — titles alone collide). Seed with the main window.
4. For each screen: record title/type, screenshot it, then find every way to open another surface ON it — menu items (walk the full menu tree), toolbar/ribbon buttons, every dockable panel toggle, tree/list "open/edit" actions, tabs, and **right-click context menus** on the main content. Add new surfaces to the queue.
5. **Trigger openers, don't just read labels.** A menu entry named "Export…" tells you a dialog exists, not what it contains. Click it, capture the dialog, then close it. Dialogs and wizards are screens.
6. Repeat until no new surfaces appear. Note permission/elevation-gated areas and anything you intentionally exclude (and why).
7. Write `SCREENS.md` as a checklist table.

## Driving the app

- **AI-driven walkthrough:** `microsoft/UFO` can navigate menus/dialogs autonomously — good for breadth (finding surfaces you'd miss). Verify each surface it reports with a real tree dump/screenshot; do not trust a narrated "opened X" without evidence.
- **From Claude directly:** `sbroenne/mcp-windows` exposes UI Automation over MCP — click by control name, read the tree back. Best when you want the driving loop inside this agent.
- **Scripted:** pywinauto / Python-UIAutomation for deterministic, repeatable enumeration.
- **Electron:** enumerate BrowserWindows via CDP (`/json` lists targets); each is a screen.

Watch for modal dialogs freezing the driver (see SKILL.md Environment Robustness) and dismiss them explicitly.

## `SCREENS.md` template

```markdown
# Screen Inventory

- Fidelity level: Faithful | Functional-equivalent | Mixed (per-screen overrides below)
- Target: <app> — see TECH.md

| # | screen title | type (window/dialog/panel/menu/wizard-step/context-menu) | opened from | fidelity | planned clone screen | status (done/placeholder/missing) | notes |
|---|---|---|---|---|---|---|---|
| 1 | Main window | window | launch | Faithful | / | | |
| 2 | Export dialog | dialog | File ▸ Export… | Faithful | /export | | separate modal window |
| 3 | Timeline panel | panel (custom-drawn) | main | Faithful | / (canvas) | | vision-only, UIA empty |
```

Mark custom-drawn / un-openable / permission-gated surfaces honestly. Do not begin specs or implementation until `SCREENS.md` covers the whole reachable tree — it is the contract QA checks coverage against.

## `APP_TOPOLOGY.md`

Write the topology as a **tree that mirrors the app's navigation**, not a flat list:

```
App
├─ Main window
│  ├─ Menu bar (File / Edit / View / …)
│  ├─ Toolbar
│  ├─ Left panel: <name>
│  ├─ Center: <content / canvas>  (custom-drawn → vision-only)
│  └─ Status bar
├─ Preferences (dialog)
│  ├─ General (page)
│  └─ Advanced (page)
└─ Export (wizard)
   ├─ Step 1: format
   └─ Step 2: output
```

Each node links to its `SCREENS.md` row. The tree and `SCREENS.md` must agree; a surface in one but not the other means the inventory is incomplete.

## Behavior sweep

Before writing specs, for each screen record in `BEHAVIORS.md`: hover/press/checked states, drag interactions (splitters, list reordering, timeline drags), keyboard shortcuts, enable/disable logic, resize/docking behavior, and any animation. Classify each region: static, click-driven, drag-driven, hover-driven, time-driven, or mixed.
