# Rebuild Stack Reference

**Preferred output target: a local WEB APPLICATION** (browser-based), rebuilt in the same stack as `clone-website` — Next.js/React + TypeScript + Tailwind + shadcn. The desktop app is the *source* to reverse-engineer; the *clone* is a web app **when the browser can faithfully restore its functions**. Choose the stack AFTER tech detection (`TECH.md`), and apply the package-first principle throughout.

Web is not an automatic default: judge it by function (see Output Target below), recommend web / native / hybrid to the user, and let them decide. For a UI/appearance/operation clone with mock or accessible data — the common case — web wins on effort and iteration and the whole mature toolchain is web-first anyway. Where a core function needs native access the browser cannot give, recommend a desktop shell rather than shipping a faked web version.

## Output target: decide by functional feasibility (you recommend, the user decides)

Do NOT auto-pick the target. Judge it by function, present a recommendation, and let the user make the final call. The rule:

> **Web is preferred when the browser can faithfully restore the function. Where it cannot, native/desktop-shell is the honest choice — recommend it rather than silently shipping a faked web version.**

The decision has TWO axes, not one. Browser-feasibility alone is not enough — weight it by how complete each function must be:

- **Axis 1 — required fidelity (a product judgment):** does this function only need to be **Approximate** (近似 — looks/behaves roughly right, enough to demo or use lightly) or must it be **Complete** (完整 — fully works at production fidelity)? You recommend a default per function based on what it is for; the user confirms.
- **Axis 2 — browser feasibility (a technical fact):** can the browser do it **Fully / Partially / Not at all** (from the rubric below)?

Procedure:

1. List the app's key functional areas (from `SCREENS.md` / `BEHAVIORS.md`), not just its screens.
2. For each, recommend the **required fidelity** (Approximate vs Complete) with a one-line reason — and flag it as the user's to confirm.
3. Score each against the **browser-feasibility rubric** (Fully / Partially / Not).
4. Cross the two axes with the matrix below → a per-function mode: **web / native / hybrid**, each with a one-line reason.
5. Present the whole analysis (function → required fidelity → feasibility → recommended mode) and let the user decide. Record the outcome (and per-function overrides) in `TECH.md`.

### Fidelity × feasibility → mode

| | Browser: Fully | Browser: Partially | Browser: Not at all |
|---|---|---|---|
| **Needs Approximate only** | web | **web** (partial is enough) | web placeholder + note, or small native shim |
| **Needs Complete** | web | **native** for this path (partial ≠ complete) | **native** for this path |

Read it as: *web is safe wherever the browser fully covers it, OR the function only needs to be approximate. Native is required only where a function must be Complete AND the browser can't fully deliver it.* That intersection — Complete + not-fully-doable — is the only thing that forces native. Everything else is web.

### Browser-feasibility rubric

| Functional need | Browser verdict | Implication |
|---|---|---|
| UI, layout, screens, navigation, dialogs, forms, tables, mock/accessible data | ✅ Web restores it well | Build web |
| Client-side interactivity, drag/drop, canvas drawing, in-page state | ✅ Web restores it well | Build web |
| Read/write arbitrary local files & folders | ⚠️ Partial (File System Access API, user-gated, Chromium-only) | Web if the gated flow is acceptable; else native |
| Real media encode/export, ffmpeg, many codecs | ⚠️ Approximate only (WebCodecs / WASM-ffmpeg) — format & performance limits | Recommend native if fidelity/performance matters |
| Heavy GPU compute, large-file/real-time processing | ⚠️ Capped (WebGPU/WASM, memory limits) | Recommend native for the heavy path |
| Cameras/USB/serial/Bluetooth, system tray, global shortcuts, native multi-window, background service, deep OS integration | ❌ Browser cannot | Native/desktop shell for those functions |

### Recommendation shapes

- **All-web** — every key function scores ✅/acceptable-⚠️. Lowest effort, best iteration; the common case for UI-focused clones.
- **All-native (desktop shell)** — a core function is ❌/hard-⚠️ and is central to the app (e.g. the whole point is real video export). Tauri + React or Electron; **the web UI code is identical, only the wrapper adds native access** — so you lose almost nothing by going native, you gain capability.
- **Hybrid** — build the UI/flows as web now (fast, demonstrable), and mark the native-only functions as placeholders with a note that they require the desktop shell. Good when the user wants the look-and-operate clone first and native capability later.

Because the UI layer is the same React code in all three, this decision is mostly about the *wrapper and which functions actually work*, not a rewrite — make that clear to the user so the choice is cheap to change later.

## How detected tech affects the web rebuild

Extraction differs by tech; the rebuild target stays web. Detection mainly changes how directly you can reuse the original's markup:

| Detected source | Effect on the web rebuild |
|---|---|
| **Electron/CEF** | Easiest — it is already web. Reuse the CDP-extracted DOM + `getComputedStyle` near-directly, exactly like clone-website. |
| **WPF / WinForms / WinUI** | Clean UIA tree maps to React components; translate control tree → JSX, computed layout → Tailwind. |
| **Qt** | UIA partial; translate what you can, treat custom-drawn regions as canvas/vision-only. |
| **Legacy Win32 / custom-drawn** | Highest effort; reproduce measured layout from screenshots; custom surfaces → canvas lib or labeled placeholder. |

## Package-first defaults (web rebuild)

Adopt mature packages for every mechanism; hand-roll only after confirming none fits, and record the evaluation in the spec. This mirrors the `clone-website` package table — reuse it.

| Mechanism | Package |
|---|---|
| Framework / routing between screens | Next.js App Router (or Vite + TanStack Router) |
| Server/data fetching + caching | TanStack Query (`@tanstack/react-query`) |
| Dockable / resizable panels (recreate desktop docking) | `react-resizable-panels`, `dockview`, or `rc-dock` |
| Data tables / grids | TanStack Table (`@tanstack/react-table`); AG Grid for spreadsheet-heavy |
| Trees | `react-arborist` or `@headless-tree/react` |
| Forms + validation | react-hook-form + zod |
| Client global state | Zustand |
| Long-list virtualization | TanStack Virtual (`@tanstack/react-virtual`) |
| Menus / menubar / context menus / dialogs | Radix / shadcn (menubar, context-menu, dialog, dropdown) |
| Drag & drop | `@dnd-kit/core` |
| Icons | Lucide (placeholders); reproduce originals only if the user owns them |
| Canvas / timeline (custom-drawn originals) | Konva (`react-konva`) or PixiJS |
| Media in-browser (only if editing is a goal) | WebCodecs / `@ffmpeg/ffmpeg` (WASM) — mind the limits |
| Date handling | date-fns or dayjs |

For any mechanism not listed, follow the rule: search for a mature package → adopt if found → hand-roll only when confirmed absent, recording candidates and reason in the spec.

## Recreating desktop UI paradigms in a web app

Desktop apps use patterns a plain web page does not — reproduce them with the packages above:

- **Menu bar / toolbar / status bar** → shadcn menubar + a toolbar component + a status-bar strip in the single app shell.
- **Dockable / resizable panels** → `dockview` / `react-resizable-panels` (do not hand-roll splitters).
- **Right-click context menus** → Radix context-menu.
- **Multi-window / dialogs** → routed modals or Radix dialog; a separate original window becomes its own route + modal.
- **Trees, grids, virtualized lists** → the mapped packages, not bespoke components.

## Foundation-first build order

1. App shell chrome (title bar area, menu bar, docking layout, status bar) + theme tokens (colors/fonts/spacing from extraction) + shared icons + types — the shell in ONE layout level.
2. Screens from `SCREENS.md`, in small verified batches, each from its spec.
3. Wire navigation per `APP_TOPOLOGY.md`. Preserve the hierarchy; never merge windows into one page.

After each batch verify files landed and run typecheck; after assembly run build — with real output in the same turn (see SKILL.md Grounding). Because the output is a web app, QA can reuse browser tooling (DevTools, screenshot diffing) as in clone-website.
