import sys, os, yaml, json, re
root = sys.argv[1]
d = os.path.join(root, '.github', 'workflows')
for fn in sorted(os.listdir(d)):
    p = os.path.join(d, fn)
    txt = open(p, encoding='utf-8').read()
    y = yaml.safe_load(txt)
    on = y.get(True, y.get('on'))
    print('=' * 80)
    print(fn, '| name:', y.get('name'))
    print('ON:', json.dumps(on, default=str))
    if 'permissions' in y: print('PERMS:', json.dumps(y['permissions']))
    if 'concurrency' in y: print('CONC:', json.dumps(y['concurrency']))
    for jn, j in (y.get('jobs') or {}).items():
        print(f'  JOB {jn} name={j.get("name")!r} if={j.get("if")!r} needs={j.get("needs")!r} runs-on={j.get("runs-on")!r}')
        for s in j.get('steps', []) or []:
            r = s.get('run'); u = s.get('uses')
            nm = s.get('name')
            sif = s.get('if')
            line = f'     - {nm!r}'
            if sif: line += f' if={sif!r}'
            if u: line += f' uses={u}'
            if s.get('with'): line += f' with={json.dumps(s.get("with"))[:200]}'
            print(line)
            if r:
                for rl in r.strip().splitlines():
                    if re.search(r'python|verify|\.py|trusted|git |pytest|bash|sh ', rl):
                        print('         $', rl.strip()[:220])
