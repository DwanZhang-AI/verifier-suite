
# usage harvest (metering channel)
python3 - <<'PYUSAGE' > "$V/usage.json" 2>/dev/null || echo '{}' > "$V/usage.json"
import json, os, glob
tin = tout = calls = 0
for f in (glob.glob('/logs/agent/opencode/xdg-data/opencode/**/*.json', recursive=True)
          or glob.glob(os.path.expanduser('~/.local/share/opencode/**/*.json'), recursive=True)):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    stack = [d]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            t = o.get('tokens')
            if isinstance(t, dict):
                tin += int(t.get('input') or 0)
                tout += int(t.get('output') or 0)
            if o.get('type') == 'tool':
                calls += 1
            stack.extend(o.values())
        elif isinstance(o, list):
            stack.extend(o)
print(json.dumps({'tokens_in': tin, 'tokens_out': tout, 'tool_calls': calls}))
PYUSAGE
