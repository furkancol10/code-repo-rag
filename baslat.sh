#!/usr/bin/env bash
# Kod Repo Asistanı: Ollama + Streamlit'i başlatır, tarayıcıyı açar.
cd "$(dirname "$(readlink -f "$0")")" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
PORT=8501
URL="http://localhost:$PORT"
mkdir -p data

# Ollama çalışmıyorsa başlat
if ! curl -s -o /dev/null http://localhost:11434; then
  setsid -f ollama serve >data/ollama.log 2>&1
fi

# Streamlit çalışmıyorsa başlat ve hazır olmasını bekle
if ! curl -s -o /dev/null "$URL"; then
  setsid -f uv run streamlit run app.py --server.port "$PORT" --server.headless true --server.address localhost \
    >data/streamlit.log 2>&1
  for _ in $(seq 1 60); do
    curl -s -o /dev/null "$URL" && break
    sleep 0.5
  done
fi

# Terminal kapansa bile tarayıcı açılsın diye ayrı oturumda başlat
setsid -f xdg-open "$URL" >/dev/null 2>&1
sleep 2
