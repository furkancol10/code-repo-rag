#!/usr/bin/env bash
# Kod Repo Asistanı: Ollama + Streamlit'i başlatır, tarayıcıyı açar.
ROOT="$(dirname "$(readlink -f "$0")")"
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
mkdir -p data
PIDFILE=data/streamlit.pid

# PID dosyasındaki süreç canlı ve bu projeye ait mi? (cwd + cmdline doğrulaması)
bizim() {
  [ -n "$1" ] && [ -d "/proc/$1" ] || return 1
  [ "$(readlink -f "/proc/$1/cwd" 2>/dev/null)" = "$ROOT" ] || return 1
  local c; c="$(tr '\0' ' ' <"/proc/$1/cmdline" 2>/dev/null)"
  [[ "$c" == *streamlit* && "$c" == *app.py* ]]
}

# Port dinleniyor mu? (HTTP'den bağımsız)
dinleniyor() {
  if command -v ss >/dev/null; then
    [ -n "$(ss -ltnH "sport = :$1" 2>/dev/null)" ]
  else
    timeout 1 bash -c ">/dev/tcp/127.0.0.1/$1" 2>/dev/null
  fi
}

# Ollama çalışmıyorsa başlat
if ! curl -s --max-time 2 -o /dev/null http://localhost:11434; then
  setsid -f ollama serve >data/ollama.log 2>&1
fi

# Eşzamanlı başlatmalara karşı kilit
exec 9>data/baslat.lock
flock 9

PORT=""
if [ -f "$PIDFILE" ]; then
  read -r PID PORT_KAYIT <"$PIDFILE"
  if bizim "$PID" && [ -n "$PORT_KAYIT" ]; then
    # canlı ve bizim: yanıt verene kadar bekle, yeni sunucu başlatma
    for _ in $(seq 1 60); do
      curl -s --max-time 2 -o /dev/null "http://localhost:$PORT_KAYIT" && { PORT=$PORT_KAYIT; break; }
      bizim "$PID" || break
      sleep 0.5
    done
  fi
fi

if [ -z "$PORT" ]; then
  for p in 8501 8502 8503 8504 8505 8506 8507 8508 8509 8510; do
    dinleniyor "$p" || { PORT=$p; break; }
  done
  [ -z "$PORT" ] && { echo "8501-8510 arası boş port yok." >&2; exit 1; }
  setsid -f bash -c 'echo "$$ '"$PORT"'" >"$0"; exec uv run streamlit run app.py --server.port '"$PORT"' --server.headless true --server.address localhost >data/streamlit.log 2>&1' "$PIDFILE" 9>&-
  for _ in $(seq 1 60); do
    curl -s --max-time 2 -o /dev/null "http://localhost:$PORT" && break
    sleep 0.5
  done
fi
flock -u 9
URL="http://localhost:$PORT"

# Terminal kapansa bile tarayıcı açılsın diye ayrı oturumda başlat
setsid -f xdg-open "$URL" >/dev/null 2>&1
sleep 2
