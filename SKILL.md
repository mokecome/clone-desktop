---
name: clone-desktop-app
description: >-
  Reverse-engineer and rebuild a Windows DESKTOP application as a local clone.
  Use when asked to clone, copy, replicate, duplicate, rebuild, or
  reverse-engineer a rendered desktop program — a native or Electron/Qt/WPF app,
  editor, dashboard, admin tool, internal line-of-business software, or SaaS
  desktop client — by driving the real app, reading its UI Automation tree, and
  rebuilding it as a local WEB APP by default (Next.js/React, same stack as
  clone-website; desktop shell only when native capabilities are required).
  Triggers on phrasings like "clone this
  desktop app", "replicate this Windows program", "rebuild 剪映/CapCut as my own
  project", "reverse-engineer this .exe UI into a local build", "make a copy of
  this desktop software". Requires a way to drive and inspect the running app
  (UI Automation via UFO / pywinauto / FlaUI, or CDP for Electron), and must
  avoid cracking licenses, bypassing paid features/DRM, copying proprietary
  assets without rights, or impersonating the original vendor.
triggers:
  - clone this desktop app
  - replicate this Windows program
  - rebuild this desktop software as a local copy
  - reverse-engineer this .exe into my own project
  - make a pixel-perfect clone of this desktop application
  - I want to replicate this desktop tool, every window and dialog
  - copy this native app so it looks and operates the same
non_triggers:
  - clone a website or web app (use clone-website)
  - automate a task inside a desktop app without rebuilding it
  - summarize what this program does
  - extract data from this app into a spreadsheet
  - crack, unlock, or bypass a paid/licensed feature
---

# Clone Desktop App

**Goal:** turn a running Windows desktop application into a faithful local clone — by default a web app — through tech detection, app driving, exact UI-structure extraction, screen/flow specs, implementation, build checks, and visual QA.

Use this skill to turn a running Windows desktop application into a local clone through app driving, exact UI-structure extraction, screen/flow specs, implementation, build checks, and visual QA.

**Default output is a local WEB APPLICATION** (browser-based Next.js/React + Tailwind + shadcn — the same stack as `clone-website`). The desktop app is only the *source* to reverse-engineer; the *clone* is a web app. Fall back to a desktop shell (Tauri/Electron) only when the clone genuinely needs native capabilities the browser cannot give — see `references/rebuild-stack.md`.

This is the desktop counterpart of the `clone-website` skill: the extraction half is desktop-specific, the rebuild half converges on the same web stack. The web version reads the DOM + `getComputedStyle`; here the **UI Automation tree is the "DOM" of the desktop** (control types, names, `AutomationId`, bounding rectangles, patterns). The workflow is deliberately parallel: detect the target's tech → walk every window/dialog → extract the control tree per screen → rebuild as a web app → QA against the inventory.

**Package-first is inherited.** Before implementing any mechanism (routing, data fetching, tables, forms, state, virtualization, media/timeline, drawing canvas), adopt a mature package rather than hand-rolling — see the `clone-website` package table and `references/rebuild-stack.md`. Hand-roll only after confirming no suitable package exists, and record the evaluation in the spec.

## Grounding and Verification (NON-NEGOTIABLE — read first)

A long clone is a long, repetitive tool loop (attach → walk → dump tree → write → build), and that is exactly where a model drifts from *doing* the step into *emitting text that looks like the step succeeded*. That drift produces fabricated screenshots, invented control trees/data, "File created" for files that never landed, and "build passed" for builds never run. It ships a broken clone and destroys trust. These rules prevent it:

- **Never author a tool result.** Every observation (screenshot, UIA tree dump, control property, screen text, process info) and every file write must come from a real tool call whose real result you actually received this turn. Never write the "output" of a tool yourself — not to summarize, not to "continue the pattern", not because you are confident what it would say.
- **Verify every write landed.** After writing a batch of files, confirm they exist with a real `Test-Path -LiteralPath` / directory read before treating them as done.
- **No unverified pass claims.** Never say build/typecheck/lint passed without running the real command and seeing its real output/exit code in the same turn. Re-run after every fix.
- **Un-observable ≠ inventable.** If a window, dialog, panel, or flow cannot actually be observed (it will not open, the account lacks permission, there is no data, the tool timed out, the control tree came back empty, the app is custom-drawn), record it in `SCREENS.md` / `QA_DIFFS.md` as **un-captured** with the reason, and build only a labeled placeholder. NEVER infer its internal fields/steps/columns from its label or from platform convention and present that as the original.
- **The UIA tree is truth; screenshots are secondary.** Use the UI Automation control tree (`ControlType`, `Name`, `AutomationId`, `BoundingRectangle`, supported patterns) as the source of truth for structure, labels, and values. Screenshots can render blank; when a screenshot is unusable, fall back to the tree, never to a guess. For custom-drawn apps where the tree is empty, screenshots + OCR become the only source — say so explicitly and mark the screen vision-only.
- **Distinguish claim from inference.** State what you verified (with evidence) separately from what you infer. If unsure a step really happened, re-check instead of asserting it.

## Environment Robustness (desktop-specific traps)

Deep clones of desktop apps hit predictable traps. Guard against them:

- **Custom-drawn apps expose little or nothing to UI Automation.** Timelines (e.g. 剪映's editing track), canvases, games, some Flutter/Skia and custom-GPU UIs render their own pixels; the UIA tree is a near-empty shell. Do not treat an empty tree as "no UI" — fall back to screenshot + OCR + vision for those regions and mark them vision-only in `SCREENS.md`. Never invent the control tree of a custom-drawn surface.
- **Electron/CEF apps are secretly web apps.** If tech detection shows `FrameworkId = Chrome` or you find `*.asar` / `resources.pak`, the app embeds Chromium. Attach via the Chrome DevTools Protocol (launch with `--remote-debugging-port`) and extract real DOM + `getComputedStyle` — this is the fast path, and you should reuse the `clone-website` extraction flow for those windows.
- **Elevation / integrity levels block automation (UIPI).** A non-elevated automation tool cannot drive an elevated (admin) target window, and vice versa. Match integrity levels; if the target runs elevated, run the driver elevated too, and note it.
- **Virtualized lists only expose realized items.** UIA (and the app itself) only materialize the visible rows of a long list/grid/tree; the tree shows a window of items, not all of them. Scroll to enumerate, or read the item count from the relevant pattern; never assume the visible slice is the whole set.
- **High-DPI scaling shifts every coordinate.** Bounding rectangles and click points depend on the monitor's scale factor and per-monitor DPI. Prefer name/`AutomationId`-based targeting (as `mcp-windows`/UFO do) over hard-coded coordinates.
- **In-app modal dialogs block the driver.** A native modal (message box, file picker) can freeze automation until dismissed. Prefer patterns/keyboard over blind clicks, and handle the dialog explicitly.
- **Multi-window / multi-process apps.** Splash, main window, tool windows, and OS dialogs are separate top-level elements (and Electron spawns many processes). Enumerate from the desktop root, not just the main window handle.

## Resources

**Scripts** (`scripts/`, run with `pip install uiautomation`; UTF-8-safe):

- `list_windows.py` — enumerate visible top-level windows with `FrameworkId` + pid; find the target's exact title.
- `detect_tech.py "<title>" [cdp_port]` — step-0 detection: FrameworkId, ClassName, process model, Chromium/Qt/.NET/Flutter fingerprints, CDP reachability, and a verdict.
- `dump_tree.py "<title>" [max_depth] [out_file]` — dump a window's control tree (the desktop "DOM") to a spec file.

**References** (load the one matching the current phase; do not preload all):

- `references/tech-detection.md` — FIRST. Detect tech, decide Electron (DOM shortcut) vs custom-drawn (vision fallback) vs native. Drives everything downstream.
- `references/window-discovery.md` — walk the whole window/dialog tree, map topology, drive the app.
- `references/ui-extraction.md` — dump the control tree per screen, capture properties, write specs.
- `references/rebuild-stack.md` — choose the output target (web/native/hybrid, two-axis judgment) and rebuild stack; package-first defaults.
- `references/visual-qa.md` — final QA, coverage checks, discrepancy reporting.
- `references/tooling-setup.md` — install/choose inspection & driving tools.

## Tooling (open-source, package-first)

Prefer mature, self-hostable tools over hand-rolled automation. Confirm availability before proceeding; if none is present, install one (see `references/tooling-setup.md`).

| Job | Tool |
|---|---|
| Detect app tech (`FrameworkId`) | FlaUInspect / built-in `Inspect.exe` / Accessibility Insights for Windows |
| AI-driven walkthrough of every screen | `microsoft/UFO` (UI Automation + vision agent) |
| Drive from Claude directly (by control name) | `sbroenne/mcp-windows` (MCP, UI Automation) |
| Dump the control tree programmatically | `yinkaisheng/Python-UIAutomation-for-Windows`, `pywinauto/pywinauto` |
| Electron/CEF windows | Chrome DevTools Protocol (reuse `clone-website`) |
| Low-level input/screen (last resort) | `go-vgo/robotgo`, `asweigart/pyautogui` |

## Decision Tree

Three branch points govern the whole clone. Resolve them in order:

1. **Extraction path** (from `scripts/detect_tech.py`):
   - Electron/CEF (Chromium class or asar/pak fingerprints) → **CDP DOM** (`--remote-debugging-port`); reuse clone-website extraction.
   - WPF / WinForms / WinUI / rich UIA tree → **UIA control tree** (`scripts/dump_tree.py`).
   - Qt / Direct UI / empty subtree (custom-drawn) → **screenshot + OCR**, mark vision-only. Never invent the tree.
2. **Output target** (two-axis, per function — you recommend, user decides; `references/rebuild-stack.md`):
   - required-fidelity Approximate, OR browser fully covers it → **web**.
   - required-fidelity Complete AND browser can't fully deliver (local FS / codecs / GPU / hardware / OS integration) → **native for that function**.
   - mix of both → **hybrid** (web UI now, native-only functions flagged as placeholders).
3. **Per-screen fidelity** (ask up front; record in `SCREENS.md`): **Faithful** (reproduce toolbar/panels/columns/fields/flow) vs **Functional-equivalent** vs **Mixed**.

## Coverage and Structural Fidelity

Multi-window apps silently lose screens, so these rules are non-negotiable:

- **Map the whole window/dialog tree before building.** An app is not "the buttons in the main toolbar." Screens live behind menus, ribbon tabs, tool windows, right-click context menus, wizards, preference dialogs, and modal editors — each a distinct surface. Enumerate them recursively (see `references/window-discovery.md`) and produce `docs/research/SCREENS.md` BEFORE writing any component.
- **Structure is mandatory; function is negotiable.** Every distinct original window/dialog/panel MUST exist as its own clone screen, even when the user says "functionality can be incomplete." Missing backend → render the real layout with mock data or a labeled placeholder. Missing the screen entirely is a defect.
- **Never flatten the hierarchy.** One distinct original surface = one distinct clone screen. Do not merge a menu-of-panels or a multi-tab dialog into one page.
- **No silent drops.** A placeholder/skipped screen must appear in `SCREENS.md` with that status. Coverage is verified in QA against `SCREENS.md`.

## Operation-Flow Fidelity (the layer below screen coverage)

Screen coverage answers "does the window EXIST." It does NOT answer "does it LOOK and OPERATE like the original." A clone can have every window and still be wrong inside each one: the original's toolbar, panels, menu items, tree columns, dialog fields, and multi-step flow get replaced by a plausible invention from the window's title. This is the most common deep-clone failure and it is invisible to a screen-count check.

Because faithfully reproducing every screen's internals costs far more than functional equivalents, **the depth is the user's call — ask it explicitly, up front, before building** (see First Checks). Record the choice in `SCREENS.md`:

- **Faithful (per-screen extraction):** open every window AND trigger its primary actions, then reproduce its actual menu bar / toolbar / ribbon, side panels, tree/list columns (labels + order), dialog sections & fields (label, control type, required, default), and inter-window flow. Highest effort; the only level that "looks the same when you click in."
- **Functional-equivalent:** build a working screen for the same purpose; layout/labels may differ. Cheaper; acceptable when the user only needs the capability.
- **Mixed:** faithful for a named set of key screens, functional-equivalent for the rest.

Rules when Faithful: do not infer a screen's internals from its title or menu entry; open the real window and its real dialogs (which may be separate windows, not in-place panels) and extract them. Capture the whole operation flow (toolbar → dialog → apply → result), not just the landing view. Match layout — panel docking, column order, where the toolbar sits — not just the fields.

## First Checks

1. Confirm the user named or can launch the target desktop app. If not, ask which app (path to the `.exe` or the running window).
2. Apply the Safety Boundary below before driving or copying the target.
3. Ensure an inspection path exists: `pip install uiautomation` is the minimum (the bundled `scripts/` drive it) — one package covers walking windows AND dumping the control tree, so UFO/`mcp-windows` are optional breadth add-ons, not required. For Electron targets you also need CDP. See `references/tooling-setup.md`. Do not proceed without a way to inspect the running app's tree and take screenshots.
4. **Run tech detection FIRST** (`references/tech-detection.md`): `python scripts/list_windows.py` to find the target, then `python scripts/detect_tech.py "<title>"` to read `FrameworkId`, process model, Chromium/Qt/.NET fingerprints, and CDP reachability. Write `docs/research/TECH.md` from the real output. If it is Electron/CEF, prefer the CDP/DOM path (relaunch with `--remote-debugging-port` if CDP is closed); if custom-drawn, plan the vision fallback. This result drives the rebuild-stack choice — do not pick a rebuild framework before this.
5. Inspect the workspace before writing. If it holds unrelated files, create a new project folder rather than overwriting.
6. **Ask the operation-flow fidelity level before building** (Faithful / Functional-equivalent / Mixed). Do not silently default to functional-equivalent. Record it at the top of `SCREENS.md`.
7. **Decide the output target by a two-axis judgment — you recommend, the user decides.** After tech detection, analyze each key function on TWO axes (see `references/rebuild-stack.md` → Output Target): (a) **required fidelity** — does it only need to be *Approximate* (近似, roughly right) or must it be *Complete* (完整, fully working)? and (b) **browser feasibility** — can the browser do it Fully / Partially / Not. Cross them: web is safe wherever the browser fully covers it OR the function only needs approximation; native is forced ONLY where a function must be Complete AND the browser cannot fully deliver it (local filesystem, real codecs/encode-export, GPU compute, hardware, deep OS integration). Present the full analysis (function → required fidelity → feasibility → recommended mode: web / native / hybrid) and let the user make the final call. **Never silently pick web and quietly downgrade the un-doable parts to fakes, and never silently jump to native.** Record the decision (and per-function overrides) in `TECH.md`.

### Confirmation gate (STOP here before long execution)

Steps 1–5 are cheap recon (detect tech, list windows, inspect one screen) — do them to gather evidence. But do NOT dive into the full multi-screen walk, extraction, or building until you have **presented the recommendations and gotten an explicit user decision** on:

- **Fidelity level** (step 6): Faithful / Functional-equivalent / Mixed.
- **Output target** (step 7): the per-function web / native / hybrid recommendation.

Show the tech-detection result plus these two recommendations in one message, then wait for the user's call. Extraction of an entire app and building a clone is long, largely irreversible work; starting it on an unconfirmed fidelity/target choice wastes that effort if the user wanted something different. A short confirmation now is cheaper than a re-clone later. (Recon that informs the recommendation is fine before the gate; the *commitment to build* is what waits.)

## Safety Boundary

Allowed:

- Rebuild the UI/UX of an app the user owns, operates, or has permission to reproduce, for study, migration, redesign, or local prototyping.
- Create educational or structural clones that reproduce layout and flow while omitting the real backend, license checks, and production integrations.

Refuse or redirect:

- Cracking, unlocking, or bypassing license checks, activation, DRM, trials, or paid/premium features.
- Copying proprietary assets (icons, fonts, art, bundled media, sounds) the user has no right to reproduce — use placeholders instead.
- Deceptive impersonation: passing the clone off as the original vendor's software, or reproducing brand identifiers to confuse users.
- Extracting private data, secrets, tokens, or another user's content from the app.
- Reproducing security-sensitive flows (auth, payment, wallet) as working paths rather than inert placeholders.

## Clone Workflow

Follow the phase references as needed. Clear the **Confirmation gate** in First Checks before the full walk/extraction/build begins. Keep these non-negotiable constraints:

- Detect tech FIRST (`scripts/detect_tech.py`) and write `docs/research/TECH.md` (FrameworkId, process model, Electron/custom-drawn verdict, chosen rebuild stack).
- Walk the full window/dialog tree (`scripts/list_windows.py` + driving) and write `docs/research/SCREENS.md` (every window, dialog, panel, menu, context menu, wizard step — recursively, including surfaces reached by clicking, not just the main toolbar). Do not start building until the inventory is complete.
- Capture a screenshot of every discovered screen before coding.
- Dump the UI Automation control tree per screen (`scripts/dump_tree.py "<title>" <depth> <out>`; see `references/ui-extraction.md`); for Electron windows use CDP DOM + `getComputedStyle`; for custom-drawn regions use screenshot + OCR and mark vision-only.
- Write `docs/research/APP_TOPOLOGY.md` (tree: module → window → panel/dialog → state) and `docs/research/BEHAVIORS.md`.
- Write one spec file per screen/component in `docs/research/components/*.spec.md` before implementing it.
- Build a screen for every entry in `SCREENS.md`. Preserve the hierarchy; never merge separate windows into one.
- Use exact extracted values (bounding rectangles, fonts, colors; or CDP `getComputedStyle` for Electron). Do not estimate.

## Implementation Rules

- Rebuild as a **web app by default** (Next.js/React + Tailwind + shadcn; see `references/rebuild-stack.md`). Electron sources are near-direct (reuse the CDP-extracted DOM); WPF/WinForms/Qt → translate the UIA control tree into React components. Only choose a desktop shell (Tauri/Electron) when the clone must have native filesystem/codec/GPU/OS access. Record the output-target decision in `TECH.md`.
- Recreate desktop UI paradigms with packages, not hand-rolled code: menu bar/toolbar/status bar via shadcn in the single app shell, dockable/resizable panels via `dockview`/`react-resizable-panels`, context menus via Radix, separate original windows → their own route + modal.
- **Package-first:** adopt mature packages for every mechanism; hand-roll only when none fits, and record why in the spec. The shared app shell (title bar, menu, docking panels, status bar) lives in exactly ONE layout level — do not render the chrome twice on nested screens.
- Build the foundation first: window chrome, theme tokens (colors, fonts, spacing extracted from the target), shared icons, and types.
- Implement from spec files in small batches. After each batch, verify files landed on disk (real directory read) before reporting them built.
- After component batches run `npm run typecheck` / `npx tsc --noEmit`; after assembly run `npm run build`. Report a check as passing only with its real output in the same turn.
- Preserve real labels and text. Use mock data only for session-specific or inaccessible dynamic content. Use placeholders for proprietary assets you may not copy.
- Keep secrets, license logic, and real backend behavior out of the clone unless the user owns and provides them.

## Visual QA

Do not call the clone complete until visual QA has been performed (see `references/visual-qa.md`):

1. **Screen coverage first:** every entry in `SCREENS.md` has a reachable clone counterpart (real or clearly-labeled placeholder), the hierarchy is preserved, no `missing` rows. Record the tally.
2. **Operation-flow fidelity** for Faithful screens: same menu/toolbar, same panels, same columns/order, same dialog sections & fields, same multi-step flow.
3. Compare original vs clone screenshots per window at the app's real size(s); capture the target's resize/responsive behavior if it has any.
4. Save QA screenshots under `docs/design-references/qa/` as `<appname>__<original|clone>__<window-or-state>.png`.
5. Check: nonblank render, no missing local assets, no text overflow/clipping, no incoherent overlap, no broken interactive state.
6. Record discrepancies in `docs/research/QA_DIFFS.md` (screen/state, expected, actual, evidence, likely cause, fix status).
7. Fix by checking whether the spec was wrong or the implementation diverged; re-run build checks after fixes.

## Completion Report

Report with:

- target app (name + `.exe` path/version) and detected tech (`FrameworkId`, Electron/native/custom-drawn)
- project folder and chosen rebuild stack (with reason)
- **screen coverage**: total screens in `SCREENS.md` vs clone screens built, listed done / placeholder / missing (there should be no missing)
- screens/components built, spec files written, assets reproduced (and which are placeholders for proprietary originals)
- build/typecheck status and visual QA status
- **un-captured screens**: any window/dialog/flow you could not actually observe (no permission, no data, would not open, custom-drawn, tool failure) listed honestly with the reason — never present inferred internals as if observed
- any legal, licensing, asset, elevation, or automation-access limitations

Every claim must trace to a real tool result from this session. Do not report a screen as "done", a check as "passed", or a screen as "captured" unless you verified it for real.
