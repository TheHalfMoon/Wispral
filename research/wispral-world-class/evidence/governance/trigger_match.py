"""Deterministic GitHub Actions pull_request/pull_request_target path-filter matcher (subset of glob syntax used in this repo: *, **)."""
import sys, os, re, subprocess, yaml, json

def glob_re(p):
    out = ''
    i = 0
    while i < len(p):
        if p.startswith('**', i):
            out += '.*'; i += 2
            if i < len(p) and p[i] == '/':
                out = out[:-2] + '(?:.*/)?'; i += 1
        elif p[i] == '*':
            out += '[^/]*'; i += 1
        else:
            out += re.escape(p[i]); i += 1
    return re.compile('^' + out + '$')

def triggered(filt, changed):
    if filt is None:
        return True, 'no filter'
    if 'paths' in filt:
        rs = [glob_re(p) for p in filt['paths']]
        hits = sorted({c for c in changed for r in rs if r.match(c)})
        return bool(hits), hits
    if 'paths-ignore' in filt:
        rs = [glob_re(p) for p in filt['paths-ignore']]
        rest = [c for c in changed if not any(r.match(c) for r in rs)]
        return bool(rest), rest
    return True, 'no path filter'

root, base, head = sys.argv[1:4]
changed = [l for l in subprocess.run(['git', '-C', root, 'diff', '--name-only', base, head], capture_output=True, text=True, check=True).stdout.splitlines() if l]
print('CHANGED', json.dumps(changed))
wfdir = os.path.join(root, '.github', 'workflows')
for fn in sorted(os.listdir(wfdir)):
    y = yaml.safe_load(open(os.path.join(wfdir, fn), encoding='utf-8'))
    on = y.get(True, y.get('on')) or {}
    for ev in ('pull_request', 'pull_request_target'):
        if ev not in on:
            continue
        ok, why = triggered(on[ev], changed)
        if not ok:
            continue
        for jn, j in y['jobs'].items():
            cond = j.get('if')
            print(f'TRIGGER {ev:20s} {fn:52s} job={jn:48s} if={cond!r} hits={why if isinstance(why,str) else len(why)}')
