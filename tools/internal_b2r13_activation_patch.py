#!/usr/bin/env python3
from pathlib import Path

path = Path('research/000b2-public/verify_b2r13_activation.py')
text = path.read_text(encoding='utf-8')

policy_anchor = '    require(readiness.get("task_content_policies") == proof.expected_task_content_policies(), "successor task content policy drift")\n'
policy_replacement = policy_anchor + '    require(readiness.get("b2r14_non_primary_fixture_contract") == proof.B2R14_NON_PRIMARY_FIXTURE_CONTRACT, "B2R14 canonical non-primary fixture contract drift")\n'
if policy_anchor not in text:
    raise SystemExit('activation policy anchor drift')
text = text.replace(policy_anchor, policy_replacement, 1)

main_anchor = '''    proof.verify_invalidation_record()
    verify_activation_frontier()

    if args.sherpa_source is not None:
'''
main_replacement = '''    proof.verify_invalidation_record()
    verify_activation_frontier()
    proof.verify_b2r13_candidate_content(load(READINESS))

    if args.sherpa_source is not None:
'''
if main_anchor not in text:
    raise SystemExit('activation main anchor drift')
text = text.replace(main_anchor, main_replacement, 1)
path.write_text(text, encoding='utf-8')
