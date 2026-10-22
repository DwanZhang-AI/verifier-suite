#!/usr/bin/env bash
# veritas-bridge/1: runs the generated verifier tests/veritas/verifier.sh and turns
# its exit status into the Harbor reward. Written by gavel-harness; do not edit.
#
# /logs/verifier/veritas_verdict.json records the raw exit status; reward.txt is 1
# for exit 0 and 0 for any other exit. Rewards and verdicts already present
# (/logs/verifier is writable during the agent phase) are removed before the
# verifier runs, and rewards again after it. When the verifier cannot be staged,
# or the verdict or reward cannot be written, the bridge exits without a reward.
set -u
R=/logs/verifier
W=@WORKDIR@
V=@VERIFIER@
mkdir -p "$R" || exit 90
rm -f "$R/reward.json" "$R/reward.txt" "$R/veritas_verdict.json" || exit 90
mkdir -p "$(dirname "$V")" || exit 91
cp /tests/veritas/verifier.sh "$V" || exit 91
cd "$W" || exit 92
bash "$V" >"$R/verifier.log" 2>&1 </dev/null
rc=$?
rm -f "$R/reward.json" "$R/reward.txt" || exit 93
printf '{"bridge":"veritas-bridge/1","exit_code":%d}\n' "$rc" >"$R/veritas_verdict.json" || exit 93
if [ "$rc" -eq 0 ]; then
  echo 1 >"$R/reward.txt" || exit 94
else
  echo 0 >"$R/reward.txt" || exit 94
fi
