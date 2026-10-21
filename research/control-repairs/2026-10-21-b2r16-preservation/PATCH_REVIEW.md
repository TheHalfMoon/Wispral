# Fresh-context patch review

Scope: repair diff against `origin/main`, including the preservation checker, mutation fixtures, workflow and bounded repair evidence. This is a fail-closed applicability correction, with no Constitution XVI authority. Original `verify_b2r16.py` and historical evidence remain unchanged.

## Findings and resolutions

- **Resolved — mutable checker/fixture bypass.** The workflow previously executed candidate-controlled Python without authenticating it. It now verifies both source SHA-256 identities inline before execution. Exit-zero replacements for either source are rejected.
- **Resolved — preflight import shadowing.** The initial inline preflight lacked isolation, allowing candidate-root `hashlib.py` to exit successfully before the digest checks. The current workflow invokes `python -I -`. The regression extracts the actual invocation flags and heredoc, executes them as stdin with a hostile candidate-root `hashlib.py`, and rejects both modified source files. I independently ran this focused regression against the current files: PASS.
- **Resolved — mode/type fixture masking.** Executable-mode and symlink fixtures now preserve the original blob bytes. Their failures therefore exercise Git mode/type rejection rather than a coincident byte difference.

No remaining implementation must-fix was identified in this pass. Correctness: exact full-SHA input prevents option/ref injection; frozen paths require exact regular-file mode and blob identity; missing history fails closed. Historical proof executes the unchanged verifier from the pinned qualified commit, with its original authority context. The workflow requests full history; partial-clone historical tree materialization is explicit. Parsimony: no additional dependency or general-purpose policy framework. Product: the bounded workflow migration is declared honestly instead of claiming all four original task paths remain unchanged. Its normalized digest slot is constrained to the exact executing checker bytes; the fixture digest and remaining workflow bytes stay bound.

The parent reports its final seven-group suite PASS, including all 16 byte mutations, 48 deletion/mode/symlink cases, preserved original main/#124 failures and exact qualified historical PASS. That full-suite result is parent-supplied evidence, separate from my directly executed focused regression. The final committed revision still requires the parent's planned exact-head verification.

## Approval boundary

This review supplies **no external merge or security approval** and authorizes no merge, successor execution, scoring or production claim. A candidate-controlled workflow cannot authenticate arbitrary changes to its own entry code. Trusted canonical workflow/bootstrap enforcement, required governance checks and fresh independent final-range review remain mandatory; their satisfaction is not established here. Keep the repair draft while those prerequisites remain unsatisfied.

panel: fresh-context combined correctness/parsimony/product/security review; external merge/security gate unsatisfied.
