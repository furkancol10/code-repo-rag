#!/usr/bin/env bash
# Kod Repo Asistanı: Streamlit sunucusunu kapatır.
# Ollama'ya dokunmaz (başka projeler de kullanıyor olabilir).
pids=$(pgrep -f "bin/streamlit run app.py|uv run streamlit run app.py")
if [ -n "$pids" ]; then
  kill $pids
  msg="Kod Repo Asistanı kapatıldı."
else
  msg="Kod Repo Asistanı zaten kapalı."
fi
command -v notify-send >/dev/null && notify-send "Kod Repo Asistanı" "$msg"
echo "$msg"
