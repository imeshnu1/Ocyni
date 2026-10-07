#!/bin/bash
# Ocyni hands-free setup — ONE paste on the Mac mini, then walk away.
# What it installs:
#   1. Backend auto-server: uvicorn restarts itself on crash AND on every reboot (LaunchAgent).
#   2. Build-watch loop: every 10 minutes it pulls GitHub; on any new commit it
#      rebuilds the iOS app, restarts the backend, and pops a macOS notification
#      with the result. So once a code fix lands on GitHub, the mini tests it alone.
#
# Paste this whole file into Termius as one command block, or save it and run:
#     bash ~/ocyni-handoff/setup-handsfree.sh
set -u

mkdir -p "$HOME/ocyni-handoff" "$HOME/ocyni-app/logs" "$HOME/Library/LaunchAgents"

# ---- 1. backend runner: pulls, finds python, serves on :8000 ----
cat > "$HOME/ocyni-handoff/ocyni-server.sh" <<'EOF'
#!/bin/bash
set -u
cd "$HOME/ocyni-app" || exit 1
git pull --ff-only origin main >/dev/null 2>&1 || true
for cand in "$HOME/ocyni-backend/bin/python" \
           "$HOME/ocyni-backend/venv/bin/python" \
           "$HOME/ocyni-app/venv/bin/python" \
           "$HOME/venv/bin/python"; do
  if [ -x "$cand" ]; then PY="$cand"; break; fi
done
PY="${PY:-$(command -v python3)}"
exec "$PY" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 \
  >>"$HOME/ocyni-app/logs/backend.log" 2>&1
EOF
chmod +x "$HOME/ocyni-handoff/ocyni-server.sh"

# ---- 2. LaunchAgent: keep the backend alive across crashes + reboots ----
cat > "$HOME/Library/LaunchAgents/com.ocyni.backend.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.ocyni.backend</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$HOME/ocyni-handoff/ocyni-server.sh</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>WorkingDirectory</key><string>$HOME/ocyni-app</string>
  <key>StandardOutPath</key><string>$HOME/ocyni-app/logs/launchd.out.log</string>
  <key>StandardErrorPath</key><string>$HOME/ocyni-app/logs/launchd.err.log</string>
</dict>
</plist>
EOF

# ---- 3. build-watch: rebuild iOS app on every new GitHub commit ----
cat > "$HOME/ocyni-handoff/build-watch.sh" <<'EOF'
#!/bin/bash
# Polls GitHub every 10 min. New commit -> pull, rebuild iOS app,
# restart backend, macOS notification with the result.
set -u
cd "$HOME/ocyni-app" || exit 1
mkdir -p "$HOME/ocyni-app/logs"
LOG="$HOME/ocyni-app/logs/build-watch.log"
LAST=""
while true; do
  git fetch origin main >/dev/null 2>&1 || true
  HEAD_NOW="$(git rev-parse origin/main 2>/dev/null || echo none)"
  if [ "$HEAD_NOW" != "none" ] && [ "$HEAD_NOW" != "$LAST" ]; then
    LAST="$HEAD_NOW"
    git pull --ff-only origin main >/dev/null 2>&1 || true
    OUT="$(mktemp)"
    if xcodebuild -project ios/Ocyni.xcodeproj -target Ocyni \
        -sdk iphonesimulator build >"$OUT" 2>&1; then
      STATUS="BUILD OK ✅"
      launchctl kickstart -k "gui/$(id -u)/com.ocyni.backend" >/dev/null 2>&1 || true
    else
      STATUS="BUILD FAILED ❌"
    fi
    {
      echo "=== $(date '+%F %T') — commit ${HEAD_NOW:0:7}: $STATUS ==="
      tail -6 "$OUT"
    } >>"$LOG" 2>&1
    rm -f "$OUT"
    osascript -e "display notification \"$STATUS — commit ${HEAD_NOW:0:7}\" with title \"Ocyni build-watch\"" >/dev/null 2>&1 || true
  fi
  sleep 600
done
EOF
chmod +x "$HOME/ocyni-handoff/build-watch.sh"

# ---- 4. (re)load the LaunchAgent ----
launchctl bootout "gui/$(id -u)/com.ocyni.backend" >/dev/null 2>&1 || true
launchctl load "$HOME/Library/LaunchAgents/com.ocyni.backend.plist"

# ---- 5. start build-watch in background (survives terminal close) ----
pkill -f "ocyni-handoff/build-watch.sh" >/dev/null 2>&1 || true
nohup "$HOME/ocyni-handoff/build-watch.sh" >/dev/null 2>&1 &

sleep 3
echo "---- hands-free status ----"
launchctl list | grep com.ocyni.backend || echo "backend agent: NOT LOADED (check logs)"
pgrep -f "ocyni-handoff/build-watch.sh" >/dev/null && echo "build-watch: RUNNING" || echo "build-watch: NOT RUNNING"
curl -s -o /dev/null -w "backend :8000 -> HTTP %{http_code}\n" --max-time 5 http://127.0.0.1:8000/docs || echo "backend :8000 -> not up yet (give it ~20s)"
echo ""
echo "Logs:  ~/ocyni-app/logs/backend.log   ~/ocyni-app/logs/build-watch.log"
echo "Stop everything:  launchctl bootout gui/\$(id -u)/com.ocyni.backend ; pkill -f ocyni-handoff/build-watch.sh"
