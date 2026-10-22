#!/bin/bash
# Artifact presence + bash syntax probe for the generated verifier.
set -u
V=/app/verifier.sh
REWARD_DIR=/logs/verifier
mkdir -p "$REWARD_DIR"
if [ ! -s "$V" ]; then
  echo "0.0" > "$REWARD_DIR/reward.txt"
  echo "verifier.sh missing or empty"
  exit 0
fi
cp -f "$V" "$REWARD_DIR/verifier.sh" 2>/dev/null || true
if bash -n "$V" 2> "$REWARD_DIR/syntax.err"; then
  echo "1.0" > "$REWARD_DIR/reward.txt"
  echo "verifier.sh present ($(wc -c < "$V") bytes), syntax OK"
else
  echo "0.0" > "$REWARD_DIR/reward.txt"
  echo "PROBE=NODIRECTION verifier.sh syntax error: $(head -c 200 "$REWARD_DIR/syntax.err")"
fi
