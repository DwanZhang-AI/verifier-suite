"""Explicit AppWorld candidate entrypoint, separate from public probe code."""
import ast
import uuid


def execute_solution(world, source):
    """Invoke solution(apis, requester) once; completion is NOT a PASS label."""
    if not isinstance(source, str) or not source.strip():
        return {"execution_status": "error", "error": "solution must be nonempty Python source"}
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {"execution_status": "error", "error": "candidate_syntax_error"}
    if not any(isinstance(n, ast.FunctionDef) and n.name == "solution" for n in tree.body):
        return {"execution_status": "error", "error": "missing_solution_entrypoint"}
    # A fresh namespace prevents previous candidates/probes from supplying an
    # entrypoint. Only public runtime objects are passed to the candidate.
    marker = "VGB_ENTRYPOINT_COMPLETED_" + uuid.uuid4().hex
    program = (
        "def _vgb_invoke_candidate():\n"
        "    namespace = {'apis': apis, 'requester': requester}\n"
        "    exec(compile(" + repr(source) + ", '<candidate>', 'exec'), namespace)\n"
        "    namespace['solution'](apis, requester)\n"
        "_vgb_invoke_candidate()\n"
        "print(" + repr(marker) + ")\n"
    )
    try:
        output = str(world.execute(program))
    except Exception as exc:
        return {"execution_status": "error", "error": "candidate_execution_exception:" + type(exc).__name__}
    # AppWorld may return a traceback as text instead of raising. Never treat
    # that as successful execution just because execute() returned normally.
    lines = output.splitlines()
    completed = lines.count(marker) == 1 and lines[-1:] == [marker]
    clean = "\n".join(line for line in lines if line != marker)
    if not completed:
        return {"execution_status": "error", "error": "candidate_entrypoint_not_completed", "output": clean}
    return {"execution_status": "completed", "entrypoint": "solution(apis, requester)", "output": clean}
