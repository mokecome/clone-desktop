"""List visible top-level windows with their UIA FrameworkId.

Usage: python list_windows.py
Windows-only. Requires: pip install uiautomation

Prints one row per visible top-level window: index, FrameworkId, pid,
ClassName, and Name. Use it to identify the target window's exact title
before running detect_tech.py / dump_tree.py.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import uiautomation as auto


def main():
    root = auto.GetRootControl()
    rows = 0
    for i, w in enumerate(root.GetChildren()):
        if w.ControlTypeName == 'WindowControl' and w.Name:
            rows += 1
            print('{:2d} [{}] pid={} class={!r} name={!r}'.format(
                i, w.FrameworkId, w.ProcessId, w.ClassName, w.Name[:80]))
    if rows == 0:
        print('no named top-level windows found')


if __name__ == '__main__':
    main()
