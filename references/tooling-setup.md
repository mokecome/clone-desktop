# Tooling Setup Reference

Open-source, self-hostable tools for driving and inspecting a Windows desktop app. Prefer these mature packages over hand-rolled automation. Confirm what is already available before installing.

## Inspection (read the tree / detect tech)

- **FlaUInspect** — `FlaUI/FlaUInspect`. Download a release, run it, hover the target window to read `FrameworkId`, `ControlType`, `Name`, `AutomationId`, patterns. First tool for tech detection.
- **Inspect.exe** — ships with the Windows SDK (`C:\Program Files (x86)\Windows Kits\10\bin\<ver>\x64\inspect.exe`). Same purpose, no install if the SDK is present.
- **Accessibility Insights for Windows** — Microsoft, GUI live inspection.

## Programmatic driving / tree dump (Python)

```powershell
python -m pip install uiautomation
```

`uiautomation` alone covers walking windows AND dumping the tree — it is the only required install. The skill's bundled `scripts/` drive it directly:

- `scripts/list_windows.py` — enumerate top-level windows + FrameworkId.
- `scripts/detect_tech.py "<title>" [port]` — step-0 tech detection (see tech-detection.md).
- `scripts/dump_tree.py "<title>" [depth] [out]` — dump the control tree (see ui-extraction.md).

Underlying libraries, if you want to script beyond the bundled tools:

- **uiautomation** (`yinkaisheng/Python-UIAutomation-for-Windows`) — wraps MS UIAutomation; walk and dump the tree.
- **pywinauto** (`pywinauto/pywinauto`, optional) — `backend="uia"`; `print_control_identifiers()` lists usable selectors; drives clicks/typing. Redundant with uiautomation for extraction; add only if you prefer its driving API.

## AI-driven walkthrough

- **microsoft/UFO** (`microsoft/UFO`) — clone the repo and follow its README to configure a model backend; it navigates Windows apps (UI Automation + vision) to find surfaces you would miss. Verify every surface it reports with a real dump/screenshot.
- **sbroenne/mcp-windows** (`sbroenne/mcp-windows`) — an MCP server (C#/.NET) that exposes UI Automation over MCP so this agent can click by control name and read the tree back. Best when you want the driving loop inside Claude. Add it as an MCP server, then load its tools via ToolSearch.

## Electron / CEF targets

No extra install — launch the target with remote debugging and attach the Chrome DevTools Protocol:

```powershell
& "C:\path\to\App.exe" --remote-debugging-port=9222
# then check: http://localhost:9222/json  (lists BrowserWindow targets)
```

Reuse the `clone-website` DOM + `getComputedStyle` extraction against each target. Playwright/puppeteer-core can attach over CDP.

## Low-level input/screen (last resort)

- **go-vgo/robotgo** (Go), **asweigart/pyautogui** (Python) — raw mouse/keyboard/screen. Use only when UIA/CDP cannot reach a surface; prefer name-based targeting elsewhere (coordinates break under DPI scaling).

## Elevation note

If the target runs elevated (admin), the driver/inspector must also run elevated, or UIPI blocks automation (see SKILL.md Environment Robustness). Match integrity levels and record it in `TECH.md`.

## Minimum viable setup

For a first pass you only need: **FlaUInspect** (detect + inspect) + **Python-UIAutomation** (dump trees) + screenshots. Add UFO or `mcp-windows` when you want automated breadth across many screens. Add CDP only if detection says Electron.
