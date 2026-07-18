"""Dump a target window's UI Automation control tree to a spec file.

Usage: python dump_tree.py "<window title substring>" [max_depth] [out_file]
Windows-only. Requires: pip install uiautomation

Writes the control tree (ControlType, Name, AutomationId, ClassName, bounding
rect, enabled/offscreen) as indented text — the desktop equivalent of a DOM
dump, used as the source of truth for a screen's component spec
(references/ui-extraction.md). UTF-8 safe. For Electron windows prefer CDP DOM
instead; for custom-drawn regions the tree is thin — mark those vision-only.
"""
import sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import uiautomation as auto


def walk(ctrl, depth, max_depth, out):
    if depth > max_depth:
        return
    for c in ctrl.GetChildren():
        r = c.BoundingRectangle
        out.append('{}[{}] {!r} id={!r} class={!r} rect=({},{},{},{}){}{}'.format(
            '  ' * depth, c.ControlTypeName, (c.Name or '')[:60], c.AutomationId,
            c.ClassName, r.left, r.top, r.width(), r.height(),
            '' if c.IsEnabled else ' DISABLED',
            ' OFFSCREEN' if c.IsOffscreen else ''))
        walk(c, depth + 1, max_depth, out)


def main():
    if len(sys.argv) < 2:
        print('usage: python dump_tree.py "<window title substring>" [max_depth] [out_file]')
        return 2
    needle = sys.argv[1]
    max_depth = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    out_file = sys.argv[3] if len(sys.argv) > 3 else None

    root = auto.GetRootControl()
    target = None
    for w in root.GetChildren():
        if w.ControlTypeName == 'WindowControl' and w.Name and needle in w.Name:
            target = w
            break
    if not target:
        print(f'no top-level window matching {needle!r} (run list_windows.py first)')
        return 1

    header = 'WINDOW {!r} class={!r} FrameworkId={}'.format(
        target.Name, target.ClassName, target.FrameworkId)
    out = [header]
    walk(target, 0, max_depth, out)
    out.append(f'\n[{len(out) - 2} descendant controls, depth<={max_depth}]')
    text = '\n'.join(out)

    if out_file:
        with io.open(out_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'wrote {len(out) - 2} controls to {out_file}')
    else:
        print(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
