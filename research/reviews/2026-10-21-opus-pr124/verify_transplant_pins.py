import json, sys, hashlib, subprocess, base64, re, concurrent.futures as cf
rows = json.load(open(sys.argv[1]))['rows']
jobs = []
for r in rows:
    for s in (r.get('sources') or [r['source']]):
        u = s.get('url','')
        m = re.match(r'https://github.com/([^/]+/[^/]+)/blob/([0-9a-f]{40})/([^#]+)', u)
        if m: jobs.append((r['id'], m.group(1), m.group(2), m.group(3), s))
        else: jobs.append((r['id'], None, None, None, s))
def check(j):
    rid, repo, sha, path, s = j
    if not repo: return (rid, s.get('path'), 'NON_GITHUB', s.get('url','')[:70])
    p = subprocess.run(['gh','api','-H','Accept: application/vnd.github.raw',f'repos/{repo}/contents/{path}?ref={sha}'],capture_output=True)
    if p.returncode: return (rid, path, 'FETCH_FAIL', p.stderr.decode()[:80])
    b = p.stdout
    h = hashlib.sha256(b).hexdigest()
    blob = hashlib.sha1(b'blob %d\0' % len(b) + b).hexdigest()
    ok_h = h == s.get('sha256'); ok_b = blob == s.get('git_blob', blob)
    sym = (s.get('symbol') or '').split('(')[0].strip()
    line = s.get('line')
    lines = b.decode('utf-8','replace').splitlines()
    sym_ok = 'n/a'
    if line and sym:
        sym_ok = sym.split()[-1] in lines[line-1] if line <= len(lines) else False
    return (rid, path, 'HASH_OK' if ok_h else 'HASH_MISMATCH', f'blob_ok={ok_b} line_sym_ok={sym_ok}')
with cf.ThreadPoolExecutor(8) as ex:
    res = list(ex.map(check, jobs))
for x in res: print(*x, sep=' | ')
from collections import Counter; print(Counter(x[2] for x in res))
