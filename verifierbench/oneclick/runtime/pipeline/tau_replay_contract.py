"""Public scope of the banking DB/action-replay benchmark, without oracle details."""
VERSION = "banking-db-action-replay-20260919-v3"


def apply_banking_replay_contract(spec):
    result = dict(spec)
    result["judged_obligation"] = (
        "Judge the submitted actions and resulting database state against the task request. "
        "This benchmark evaluates DB/action replay, not a complete customer-service interaction. "
        "Use domain_policy to interpret the business request, action arguments, and state changes; "
        "do not impose a separate full-workflow compliance checklist on this abbreviated replay. "
        "There are no communicate_info or nl_assertions criteria."
    )
    result["trajectory_note"] = (
        "The payload is an abbreviated action-replay transcript, not a complete interaction log. "
        "It may omit read-only preparation such as identity lookup, clock reads, account or transaction "
        "lookup, and knowledge retrieval, as well as user dialogue. Their absence alone is not a failure "
        "and does not prove they never occurred. Do not require evidence of those omitted steps before "
        "accepting an otherwise correct recorded action. Still check the submitted actions, their "
        "arguments, ownership, effects, and required business outcomes; a claim that work was done "
        "does not substitute for a required action. requestor identifies action ownership, not message role. "
        "The user_scenario supplies context rather than an additional conversational checklist."
    )
    result["action_replay_contract_version"] = VERSION
    return result
