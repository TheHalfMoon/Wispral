"""Extract the inline `python - <<'PY'` program of a named step from a workflow file at a fixed ref and run it against the current checkout (cwd)."""
import sys, os, subprocess, yaml, textwrap
repo, ref, wf, step_name = sys.argv[1:5]
src = subprocess.run(['git', '-C', repo, 'show', f'{ref}:{wf}'], capture_output=True, text=True, check=True).stdout
y = yaml.safe_load(src)
for j in y['jobs'].values():
    for s in j['steps']:
        if s.get('name') == step_name:
            run = s['run']
            body = run.split("<<'PY'\n", 1)[1].rsplit('\nPY', 1)[0]
            code = textwrap.dedent(body)
            r = subprocess.run([sys.executable, '-'], input=code, text=True, capture_output=True, env=os.environ)
            sys.stdout.write(r.stdout); sys.stderr.write(r.stderr)
            print(f'INLINE_EXIT={r.returncode}')
            sys.exit(0)
sys.exit('step not found')
