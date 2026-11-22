#!/usr/bin/env bash
# Kod Repo Asistanı: Ollama + Streamlit'i başlatır, tarayıcıyı açar.
ROOT="$(dirname "$(readlink -f "$0")")"
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
mkdir -p data
PIDFILE=data/streamlit.pid

# PID dosyasındaki süreç canlı ve bu projeye ait mi?
bizim() { [ -n "$1" ] && [ -d "/proc/$1" ] && [ "$(readlink -f "/proc/$1/cwd" 2>/dev/null)" = "$ROOT" ]; }

# Ollama çalışmıyorsa başlat
if ! curl -s -o /dev/null http://localhost:11434; then
  setsid -f ollama serve >data/ollama.log 2>&1
fi

PORT=""
if [ -f "$PIDFILE" ]; then
  read -r PID PORT_KAYIT <"$PIDFILE"
  if bizim "$PID" && [ -n "$PORT_KAYIT" ] && curl -s -o /dev/null "http://localhost:$PORT_KAYIT"; then
    PORT=$PORT_KAYIT   # zaten çalışıyor
  fi
fi

if [ -z "$PORT" ]; then
  for p in 8501 8502 8503 8504 8505 8506 8507 8508 8509 8510; do
    curl -s -o /dev/null "http://localhost:$p" || { PORT=$p; break; }
  done
  [ -z "$PORT" ] && { echo "8501-8510 arası boş port yok." >&2; exit 1; }
  setsid -f bash -c 'echo "$$ '"$PORT"'" >"$0"; exec uv run streamlit run app.py --server.port '"$PORT"' --server.headless true --server.address localhost >data/streamlit.log 2>&1' "$PIDFILE"
  for _ in $(seq 1 60); do
    curl -s -o /dev/null "http://localhost:$PORT" && break
    sleep 0.5
  done
fi
URL="http://localhost:$PORT"

# Terminal kapansa bile tarayıcı açılsın diye ayrı oturumda başlat
setsid -f xdg-open "$URL" >/dev/null 2>&1
sleep 2
