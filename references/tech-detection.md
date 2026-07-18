# Tech Detection Reference (run this FIRST)

Detect what the target app is built with BEFORE anything else. The result decides how you extract (structured tree vs DOM vs vision) and which stack you rebuild in. Write `docs/research/TECH.md` from this step.

## Why it is step 0

Cloning strategy branches entirely on the answer:

- **Electron/CEF** → the app is a web app in disguise; attach the Chrome DevTools Protocol, get real DOM + `getComputedStyle`, and reuse the `clone-website` flow. Fastest, highest-fidelity path.
- **WPF / WinForms / native UIA-friendly** → the UI Automation tree is rich; dump it as your "DOM".
- **Custom-drawn (Qt with custom paint, Skia/Flutter, games, canvas timelines like 剪映)** → UIA is nearly empty; you fall back to screenshots + OCR + vision and mark regions vision-only.

Guessing wrong wastes the whole clone. Never pick a rebuild framework before this file exists.

## How to read `FrameworkId`

Every UIA element carries a `FrameworkId`. Read it on the target's main window with any of:

- **FlaUInspect** (`FlaUI/FlaUInspect`) — hover the window, read the properties panel.
- **Inspect.exe** — ships with the Windows SDK; same idea.
- **Accessibility Insights for Windows** — Microsoft, live inspection.
- **Programmatically** with Python-UIAutomation:

```python
import uiautomation as auto
win = auto.WindowControl(searchDepth=1, ClassName='')  # or Name='...'
print(win.Name, win.ClassName, win.FrameworkId)
```

or pywinauto:

```python
from pywinauto import Desktop
w = Desktop(backend="uia").window(title_re=".*<app title>.*")
print(w.element_info.framework_id, w.element_info.class_name)
```

## FrameworkId → verdict → rebuild stack

| FrameworkId / signal | Target tech | Extraction path | Default rebuild stack |
|---|---|---|---|
| `Chrome`, or `*.asar` / `resources.pak` / `ffmpeg.dll`+`libEGL.dll` in install dir | **Electron/CEF** | CDP DOM + `getComputedStyle` (reuse clone-website) | Electron or Tauri + the same web tech (often near-direct) |
| `WPF` | WPF (XAML) | UIA tree (rich) | Tauri/Electron + React, or same-tech WPF if user wants native |
| `WinForm` | WinForms | UIA tree (rich) | Tauri/Electron + React, or same-tech WinForms |
| `XAML` | WinUI 3 / UWP | UIA tree (rich) | WinUI same-tech, or Tauri/Electron + React |
| `Win32` + `Qt*.dll` present | Qt | UIA partial; expect custom-drawn regions | Tauri/Electron + React, or same-tech Qt |
| `Win32` only, sparse tree | Legacy native / custom | UIA thin → screenshot + OCR fallback | pick by user goal; expect high effort |
| `Direct UI` / `DirectUIHWND`, empty subtree | Custom-drawn (Skia/Flutter/game/canvas) | Vision + OCR only | choose by goal; mark heavy vision-only |

## Confirm the process model

Beyond `FrameworkId`, record:

1. **Process tree** — one process or many? (Electron spawns a main + several renderer/GPU processes.) `Get-Process`, or Task Manager's process group.
2. **Install-dir fingerprints** — list the app folder. `*.asar`, `resources.pak`, `chrome_*.dll` → Electron/CEF. `Qt6*.dll` → Qt. `*.exe` alone with `PresentationFramework` in loaded modules → WPF (.NET).
3. **Loaded modules** (optional) — `(Get-Process <name>).Modules | Select ModuleName` reveals `coreclr.dll` (.NET), `Qt6Core.dll` (Qt), `libcef.dll` (CEF), `flutter_windows.dll` (Flutter).
4. **Remote-debugging support (Electron)** — try launching the target with `--remote-debugging-port=9222`; if `http://localhost:9222/json` lists pages, you have full DOM access.

## `docs/research/TECH.md` template

```markdown
# Target Tech Detection

- App: <name> — <path\to.exe> — version <x.y.z>
- Main window FrameworkId: <value> (evidence: FlaUInspect | Inspect.exe | script output)
- Process model: single | multi-process (<n> processes: main/renderer/gpu/...)
- Install-dir fingerprints: <asar / Qt6 / coreclr / libcef / flutter ...>
- Verdict: Electron | WPF | WinForms | WinUI | Qt | legacy-native | custom-drawn
- Extraction path: CDP DOM | UIA tree | UIA + vision fallback | vision-only
- Electron remote-debugging reachable: yes (port ____) | no | n/a
- Output target: web app (default) | desktop shell (Tauri/Electron) — reason if desktop: <needs local FS/codec/GPU/OS access>
- Chosen rebuild stack: <stack, default Next.js/React+Tailwind+shadcn> — reason: <why> (see rebuild-stack.md)
- Custom-drawn regions to expect: <e.g. timeline, preview canvas> → vision-only
```

Every value here must come from a real inspection/tool result — see SKILL.md Grounding. If you cannot read the `FrameworkId` (won't attach, elevated, etc.), record that and proceed with the vision fallback rather than guessing the tech.
