#!/usr/bin/env bash
# Kod Repo Asistanı: yalnız bu projenin Streamlit sunucusunu kapatır.
# Ollama'ya dokunmaz (başka projeler de kullanıyor olabilir).
ROOT="$(dirname "$(readlink -f "$0")")"
PIDFILE="$ROOT/data/streamlit.pid"
msg="Kod Repo Asistanı zaten kapalı."
if [ -f "$PIDFILE" ]; then
  read -r PID _ <"$PIDFILE"
  if [ -n "$PID" ] && [ -d "/proc/$PID" ] && [ "$(readlink -f "/proc/$PID/cwd" 2>/dev/null)" = "$ROOT" ] \
     && c="$(tr '\0' ' ' <"/proc/$PID/cmdline" 2>/dev/null)" && [[ "$c" == *streamlit* && "$c" == *app.py* ]]; then
    # çocukları (varsa) ve kendisini kapat
    kill $(pgrep -P "$PID") "$PID" 2>/dev/null
    msg="Kod Repo Asistanı kapatıldı."
  fi
  rm -f "$PIDFILE"
fi
command -v notify-send >/dev/null && notify-send "Kod Repo Asistanı" "$msg"
echo "$msg"
