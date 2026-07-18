"""Step-0 tech detection for a target desktop window.

Usage: python detect_tech.py "<window title substring>" [cdp_port]
Windows-only. Requires: pip install uiautomation  (stdlib for the rest)

Reports the signals SKILL.md First Checks / references/tech-detection.md need:
FrameworkId, ClassName, process model, install-dir Chromium/Qt/.NET/Flutter
fingerprints, and whether a Chrome DevTools Protocol port is reachable.
Prints a draft TECH.md verdict block. Every line comes from a real probe;
fill un-probeable fields honestly rather than guessing (see SKILL.md Grounding).
"""
import sys, io, os, ctypes, subprocess, json
from ctypes import wintypes
from urllib.request import urlopen

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import uiautomation as auto

FINGERPRINTS = {
    'Electron/CEF (Chromium)': ('chrome_elf.dll', 'libcef.dll', 'resources.pak',
                                'libEGL.dll', 'chrome_wer.dll'),
    'Electron (asar bundle)': ('app.asar', 'electron.asar'),
    'Qt': ('Qt5Core.dll', 'Qt6Core.dll'),
    '.NET (WPF/WinForms)': ('coreclr.dll', 'PresentationFramework.dll'),
    'Flutter': ('flutter_windows.dll',),
}


def exe_path(pid):
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return None
    try:
        buf = ctypes.create_unicode_buffer(4096)
        size = wintypes.DWORD(4096)
        ok = ctypes.windll.kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size))
        return buf.value if ok else None
    finally:
        ctypes.windll.kernel32.CloseHandle(h)


def same_name_count(exe):
    if not exe:
        return None
    name = os.path.basename(exe)
    try:
        out = subprocess.run(['tasklist', '/fi', f'imagename eq {name}', '/fo', 'csv', '/nh'],
                             capture_output=True, text=True, timeout=15).stdout
        return sum(1 for line in out.splitlines() if name.lower() in line.lower())
    except Exception:
        return None


def scan_fingerprints(exe):
    hits = {}
    if not exe:
        return hits
    root = os.path.dirname(exe)
    found = set()
    for base, _dirs, files in os.walk(root):
        if base.count(os.sep) - root.count(os.sep) > 2:
            _dirs[:] = []
            continue
        for f in files:
            found.add(f.lower())
    for tech, names in FINGERPRINTS.items():
        matched = [n for n in names if n.lower() in found]
        if matched:
            hits[tech] = matched
    return hits


def cdp_reachable(port):
    try:
        with urlopen(f'http://127.0.0.1:{port}/json/version', timeout=3) as r:
            data = json.loads(r.read().decode('utf-8', 'replace'))
            return data.get('Browser', 'reachable')
    except Exception as e:
        return f'no ({type(e).__name__})'


def main():
    if len(sys.argv) < 2:
        print('usage: python detect_tech.py "<window title substring>" [cdp_port]')
        return 2
    needle = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9222

    root = auto.GetRootControl()
    target = None
    for w in root.GetChildren():
        if w.ControlTypeName == 'WindowControl' and w.Name and needle in w.Name:
            target = w
            break
    if not target:
        print(f'no top-level window matching {needle!r} (run list_windows.py first)')
        return 1

    pid = target.ProcessId
    exe = exe_path(pid)
    procs = same_name_count(exe)
    hits = scan_fingerprints(exe)
    chromium_class = target.ClassName in ('Chrome_WidgetWin_1', 'Chrome_WidgetWin_0')

    verdict = 'custom/native (inspect UIA tree depth)'
    if hits.get('Electron/CEF (Chromium)') or hits.get('Electron (asar bundle)') or chromium_class:
        verdict = 'Electron/CEF (Chromium) -> prefer CDP DOM extraction'
    elif hits.get('Qt'):
        verdict = 'Qt -> UIA tree, expect custom-drawn regions'
    elif hits.get('.NET (WPF/WinForms)'):
        verdict = 'WPF/WinForms (.NET) -> UIA tree (rich)'
    elif hits.get('Flutter'):
        verdict = 'Flutter -> custom-drawn, vision fallback'

    print('=== Tech detection ===')
    print('window        :', repr(target.Name))
    print('FrameworkId   :', target.FrameworkId)
    print('ClassName     :', target.ClassName, '(Chromium widget)' if chromium_class else '')
    print('pid / exe     :', pid, '/', exe)
    print('same-name proc:', procs, '(multi-process => Chromium/Electron likely)' if (procs or 0) > 3 else '')
    print('fingerprints  :', hits or 'none matched')
    print(f'CDP :{port}    :', cdp_reachable(port))
    print()
    print('VERDICT       :', verdict)
    print()
    print('If Electron/CEF and CDP is "no": relaunch the app with '
          f'--remote-debugging-port={port} to unlock full DOM extraction.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
