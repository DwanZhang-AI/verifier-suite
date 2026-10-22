"""Fail closed when judging and generation expose different capability APIs."""
REVISION = 'public-observation-v2-rejudge-20261007'
EXPECTED_CONTRACT = 'task-serial-reset-shared-budget-20260917-v2+public-observation-pages-20260926-v1'

def validate_runtime_rows(rows, form, generation_contract):
    if form == 'ast':
        return
    assert generation_contract == EXPECTED_CONTRACT, 'Unexpected generation capability contract'
    assert rows, 'No candidate verdicts'
    for row in rows:
        assert row.get('runtime_contract') == generation_contract, 'Judging capability contract differs from generation'
        assert row.get('generation_environment_contract') == generation_contract, 'Verdict generation contract mismatch'
