from pathlib import Path

SOURCE = Path('.github/workflows/internal-b2e02-reconciliation-apply.yml')
OUT = Path('/tmp/reconcile-v3.sh')

source = SOURCE.read_text(encoding='utf-8')
marker = '        run: |\n'
if source.count(marker) != 1:
    raise SystemExit(f'apply run block drift: {source.count(marker)}')

block = source.split(marker, 1)[1]
lines = block.splitlines()
extracted: list[str] = []
for line in lines:
    if line.startswith('          '):
        extracted.append(line[10:])
    elif not line.strip():
        extracted.append('')
    else:
        raise SystemExit(f'unexpected YAML indentation in apply block: {line!r}')
script = '\n'.join(extracted) + '\n'

insertion_anchor = '# Canonical CURRENT: update frontier and record the exact B2E02 merge/post-merge proof.\n'
if script.count(insertion_anchor) != 1:
    raise SystemExit(f'methodology insertion anchor drift: {script.count(insertion_anchor)}')

extension = """# Exact methodology frontier extension for post-B2E02 reconciliation.
p = Path("research/000b2-public/verify_methodology.py")
text = read(p)
text = once(
    text,
    '    require(readiness.get("completed_through") == "B2E01", "readiness completed_through must be B2E01")\\n',
    '    require(readiness.get("completed_through") == "B2E02", "readiness completed_through must be B2E02")\\n',
    "methodology exact completed_through",
)
old_next = '''    expected_next_action = (\\n        'Execute B2E02 only: decode the identical frozen P0 public-human subset with candidate cell 2 (`moonshine-balanced`) under unchanged frozen C0, preserve raw transcript/failure/run evidence, keep repository/test-specific context and candidate-specific audio transforms OFF, and preserve DIAGNOSTIC timing semantics. Do not begin B2E03 or any later candidate cell until B2E02 is canonical.'\\n    )\\n    require(readiness.get("next_action") == expected_next_action, "next action must be exact post-B2E01 B2E02-only instruction")\\n'''
new_next = '''    expected_next_action = (\\n        'Execute B2E03 only: decode the identical frozen P0 public-human subset with candidate cell 3 (`whispercpp-compact`) under unchanged frozen C0, preserve raw transcript/failure/run evidence, keep repository/test-specific context and candidate-specific audio transforms OFF, and preserve DIAGNOSTIC timing semantics. Do not begin B2E04 or any later candidate cell until B2E03 is canonical.'\\n    )\\n    require(readiness.get("next_action") == expected_next_action, "next action must be exact post-B2E02 B2E03-only instruction")\\n'''
text = once(text, old_next, new_next, "methodology exact next action")
write(p, text)

"""

script = script.replace(insertion_anchor, extension + insertion_anchor)
OUT.write_text(script, encoding='utf-8')
print(f'WROTE={OUT}')
