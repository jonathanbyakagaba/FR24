#!/usr/bin/env python3
"""Turn `work/ci_capture/capture_manifest.json` into workflow step outputs.

A here-doc in a `run: |` block cannot be written at column zero, so the six lines that read the
manifest live here instead. It never fails the build: a missing or unreadable manifest means "no
capture", which is a fact the notifier wants to say, not an error.
"""
import json
import os
import sys

ZERO = [('captured', 0), ('seen', 0), ('too_old', 0), ('held', 0),
        ('window', 'no fetch this run (a push-triggered run fetches nothing, by design)')]


def emit(pairs):
    fh = open(os.environ.get('GITHUB_OUTPUT', os.devnull), 'a')
    for k, v in pairs:
        fh.write('%s=%s\n' % (k, v))
    fh.close()
    for k, v in pairs:
        print('%-8s %s' % (k + ':', v))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'work/ci_capture/capture_manifest.json'
    try:
        d = json.load(open(path))
    except Exception as e:                                       # noqa: BLE001
        print(f'no capture summary ({type(e).__name__}: {e})')
        emit(ZERO)
        return 0
    emit([('captured', d.get('captured', 0)),
          ('seen', d.get('listings_seen', 0)),
          ('too_old', d.get('too_old_or_thin', 0)),
          ('held', d.get('already_held_or_scheduled', 0)),
          ('window', '%s to %s' % (d.get('since', '?'), d.get('until', '?')))])
    return 0


if __name__ == '__main__':
    sys.exit(main())
