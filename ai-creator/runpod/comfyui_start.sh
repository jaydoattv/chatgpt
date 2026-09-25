#!/usr/bin/env bash
# Startet ComfyUI im Hintergrund (übersteht eine SSH-Trennung) und wartet, bis es bereit ist.
# ComfyUI hört nur auf 127.0.0.1 → vom PC aus per SSH-Tunnel erreichbar, nicht öffentlich.
#
#   bash comfyui_start.sh          startet (oder meldet, dass es schon läuft)
#   bash comfyui_start.sh --stopp  beendet ComfyUI
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"
COMFY="$WORKSPACE/ComfyUI"
VENV="${VENV:-$WORKSPACE/venv_comfy}"
PORT="${PORT:-8188}"
LOG="$WORKSPACE/comfyui.log"
# zusätzliche ComfyUI-Argumente, z. B. COMFY_ARGS="--lowvram" (Standard: keine)
COMFY_ARGS="${COMFY_ARGS:-}"

laeuft() { curl -s -m 2 "http://127.0.0.1:$PORT/system_stats" >/dev/null; }

if [ "${1:-}" = "--stopp" ]; then
  pkill -f "[m]ain.py --listen 127.0.0.1 --port $PORT" && echo "ComfyUI beendet." || echo "ComfyUI lief nicht."
  exit 0
fi

if laeuft; then
  echo "ComfyUI läuft bereits auf Port $PORT."
  exit 0
fi

cd "$COMFY"
# shellcheck disable=SC2086  # COMFY_ARGS soll in einzelne Argumente zerfallen
setsid "$VENV/bin/python" main.py --listen 127.0.0.1 --port "$PORT" $COMFY_ARGS > "$LOG" 2>&1 < /dev/null &
PID=$!

for _ in $(seq 1 120); do
  if laeuft; then
    echo "ComfyUI bereit auf Port $PORT (PID $PID, Log: $LOG)."
    echo "Vom PC aus: ssh -N -L $PORT:127.0.0.1:$PORT root@<POD-IP> -p <SSH-PORT>  →  Browser: http://localhost:$PORT"
    exit 0
  fi
  if ! kill -0 "$PID" 2>/dev/null; then
    break  # Prozess ist abgestürzt – nicht weiter warten
  fi
  sleep 2
done
echo "ComfyUI startet nicht. Letzte Logzeilen:" >&2
tail -n 30 "$LOG" >&2
exit 1
