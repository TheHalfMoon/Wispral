#!/usr/bin/env bash
# usage: content_verifiers.sh <label>   (run from repo checkout root)
export PYTHONDONTWRITEBYTECODE=1 AUTHORITY_BASE_REVISION=edacdf7504302cc91ff7138bc6ac2d391e4df1f4 EXACT_REVISION=$(git rev-parse HEAD)
run() { local wf="$1"; shift; local out; out=$(timeout 180 python -I "$@" 2>&1); local rc=$?; printf '%s | %-45s | rc=%s | %s\n' "$LABEL" "$wf: $(basename "$1") ${*:2}" "$rc" "$(printf '%s' "$out" | grep -v '^\s*$' | tail -1 | cut -c1-160)"; }
LABEL="$1"
run methodology research/000b2-public/verify_workflow_contracts.py
run methodology research/000b2-public/verify_methodology.py
for s in verify_preregistration verify_frozen_contracts verify_b2_registry_gate verify_entity_annotation_gate verify_documents verify_closeout verify_closeout_regressions verify_parent_reconciliation; do run preregistration research/000b1/$s.py; done
run entry-contracts research/000b2-entry/verify_closeout.py
run entry-contracts research/000b2-entry/verify_readiness.py
run entry-contracts research/000b2-entry/verify_scorer.py
run recovery/trusted-pr research/000b2-public/verify_attempt_002_invalidation.py --static-only
run legacy-recovery research/000b2-public/verify_attempt_001_invalidation.py --static-only --canonical-main-ref refs/remotes/origin/main
run b2e01 research/000b2-public/verify_b2e01.py
run b2e02 research/000b2-public/verify_b2e02.py
run attempt-freeze research/000b2-public/verify_public_wer.py
run attempt-freeze research/000b2-public/verify_attempt_manifest.py
run subset-selection research/000b2-public/verify_subset_selection.py
run subset-freeze research/000b2-public/verify_subset_freeze.py
run subset-freeze research/000b2-public/verify_subset_freeze_root_metadata.py
run trusted-human .github/trusted/verify_000b2_human_authority.py --base-root . --candidate-root .
run trusted-materials .github/trusted/verify_000b2_participant_materials.py --base-root . --candidate-root .
run trusted-policy .github/trusted/verify_000b2_participant_policy.py --base-root . --candidate-root .
