
# --- evidence capture (T1): final state + materials -> the verifier channel ---
# Behaviour streams are NOT parsed here any more (2026-09-04 ruling): harbor
# natively converts each agent's event stream into an ATIF trajectory.json which
# now rides home with the trial — that is the process-lane record. Only a raw
# tail is kept in-container as a crash-forensics fallback.
EV="${V:-/logs/verifier}/evidence"; mkdir -p "$EV"
WROOT=/app; [ -d /testbed ] && WROOT=/testbed
[ -f /logs/agent/opencode.txt ] && timeout 30 tail -c 131072 /logs/agent/opencode.txt \
    > "$EV/opencode_tail.txt" 2>/dev/null || true
# final.manifest: end-state fingerprint of the workroot (listing + digests, capped)
timeout 120 sh -c "find '$WROOT' -type f -not -path '*/.git/*' 2>/dev/null | head -5000 \
    | xargs -r sha256sum 2>/dev/null" > "$EV/final_manifest.tsv" 2>/dev/null || true
# final.diff: change set when the workroot is a git repo (SWE-style testbeds)
if [ -d "$WROOT/.git" ]; then
  timeout 120 sh -c "cd '$WROOT' && git diff HEAD 2>/dev/null | head -c 262144" \
      > "$EV/diff.patch" 2>/dev/null || true
fi
# final.deps: dependency state (small, best-effort)
{ command -v python3 >/dev/null 2>&1 && timeout 60 python3 -m pip freeze 2>/dev/null | head -300;
  command -v node >/dev/null 2>&1 && node --version 2>/dev/null; } > "$EV/deps.txt" 2>/dev/null || true
# storage diagnosis: where do opencode sessions actually live? (usage.json has been
# silently all-zero since genesis — same wrong-path root cause; listing settles it)
{ for H in "$HOME" /root /home/*; do
    [ -d "$H/.local/share/opencode" ] && find "$H/.local/share/opencode" -type f 2>/dev/null | head -60;
  done
  ls -d /root/.opencode /app/.opencode 2>/dev/null
  env | grep -iE "^HOME=|XDG" ; } > "$EV/storage_listing.txt" 2>/dev/null || true
# T5 declaration + task-material export (host-side certificate needs both)
for MF in /app/declaration.json "$WROOT/declaration.json"; do
  [ -f "$MF" ] && cp -f "$MF" "$EV/gen_declaration.json" 2>/dev/null && break
done
for MAT in /app/task_info.json /testbed/ISSUE.md /app/TASK.md /app/CLAIMS.txt; do
  [ -f "$MAT" ] && cp -f "$MAT" "$EV/material_$(basename "$MAT")" 2>/dev/null || true
done
# --- end evidence capture ---
