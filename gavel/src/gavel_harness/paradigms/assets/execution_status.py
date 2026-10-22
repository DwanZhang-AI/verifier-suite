"""Pure execution/semantic-result boundary, shared by generation probes and scoring.

This file is copied into old SWE images: stdlib only, Python 3.5 compatible.
Version 2 deliberately treats ambiguous execution as no verdict. It does not
retroactively reinterpret any historical predictions.
"""
import json
import re
import sys
import xml.etree.ElementTree as ET

MEASUREMENT_VERSION = "veritas-execution/2"


def _assertion_failure(node):
    kind = node.get("type", "").split(".")[-1]
    message = node.get("message", "")
    text = node.text or ""
    return (kind in ("AssertionError", "Failed")
            or message.startswith("assert ")
            or bool(re.search(r"(?m)^(?:E\s+)?(?:AssertionError|Failed)(?::|$)", text)))


def classify_execution(returncode, runner, junit_text=None, output=""):
    """Return explicit status; nonzero process exit alone is never semantic FAIL.

    pytest needs a consistent JUnit report and a real call-phase assertion
    failure, without collection/setup/runtime errors. The legacy shim merges
    failures/errors, so accept only when every failure has an AssertionError
    traceback. Standalone scripts retain exit-0 PASS; exit-1 is FAIL only with an
    explicit AssertionError traceback (arbitrary sys.exit(1) stays unknown).
    """
    result = {"measurement_version": MEASUREMENT_VERSION, "runner": runner,
              "returncode": returncode, "prediction": None,
              "reason": "unclassified_execution", "execution_status": "error",
              "n_tests": None, "n_failed": None, "n_errors": None,
              "n_skipped": None}

    def finish(prediction, reason, status="completed"):
        result.update(prediction=prediction, reason=reason, execution_status=status)
        return result

    if returncode == 124:
        return finish(None, "verifier_timeout", "timeout")
    if returncode not in (0, 1):
        return finish(None, "verifier_exit_{}".format(returncode), "error")
    if runner == "pytest":
        try:
            root = ET.fromstring(junit_text or "")
            cases = list(root.iter("testcase"))
        except (ET.ParseError, TypeError):
            return finish(None, "pytest_report_missing_or_invalid", "error")
        failures = [n for c in cases for n in c.findall("failure")]
        errors = [n for c in cases for n in c.findall("error")]
        skipped = sum(bool(c.findall("skipped")) for c in cases)
        runtime_errors = sum(not _assertion_failure(n) for n in failures)
        result.update(n_tests=len(cases), n_failed=len(failures) - runtime_errors,
                      n_errors=len(errors) + runtime_errors, n_skipped=skipped)
        if result["n_errors"]:
            return finish(None, "pytest_execution_error", "error")
        if not cases or len(cases) == skipped:
            return finish(None, "pytest_no_executed_tests", "unverified")
        if returncode == 1 and result["n_failed"] > 0:
            return finish(False, "assertion_failed")
        if returncode == 0 and not failures:
            return finish(True, "")
        return finish(None, "pytest_report_exit_mismatch", "error")
    if runner == "shim":
        matches = re.findall(r"(?m)^RAN=(\d+) FAILED=(\d+) SKIPPED=(\d+)\s*$", output)
        if len(matches) != 1:
            return finish(None, "shim_report_missing_or_invalid", "error")
        ran, failed, skipped = map(int, matches[0])
        assertions = len(re.findall(r"(?m)^AssertionError(?::[^\n]*)?$", output))
        result.update(n_tests=ran + skipped, n_failed=failed,
                      n_errors=max(0, failed - assertions), n_skipped=skipped)
        if ran < 1:
            return finish(None, "shim_no_executed_tests", "unverified")
        if returncode == 0 and failed == 0:
            return finish(True, "")
        if returncode == 1 and failed > 0 and assertions == failed:
            return finish(False, "assertion_failed")
        return finish(None, "shim_execution_error", "error")
    if runner == "standalone":
        if returncode == 0:
            return finish(True, "")
        lines = output.strip().splitlines()
        if ("Traceback (most recent call last):" in output and lines
                and re.match(r"^AssertionError(?::|$)", lines[-1])):
            result.update(n_failed=1, n_errors=0)
            return finish(False, "assertion_failed")
        return finish(None, "standalone_nonassertion_exit", "error")
    return finish(None, "unknown_runner", "error")


if __name__ == "__main__":
    def read_optional(path):
        try:
            with open(path, encoding="utf-8", errors="replace") as stream:
                return stream.read()
        except OSError:
            return ""
    status = classify_execution(int(sys.argv[1]), sys.argv[2],
                                read_optional(sys.argv[3]), read_optional(sys.argv[4]))
    print("PI_EXECUTION=" + json.dumps(status, sort_keys=True))
