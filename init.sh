#!/usr/bin/env bash
# Arranca TaskFlow AI con un solo comando.
# Uso:  ./init.sh --api_key=TU_API_KEY
#       ./init.sh                      (sin IA: asignación manual)
set -euo pipefail
cd "$(dirname "$0")"

API_KEY=""
for arg in "$@"; do
  case "$arg" in
    --api_key=*|--api-key=*) API_KEY="${arg#*=}" ;;
  esac
done

# Crea el .env desde el ejemplo si no existe.
[ -f .env ] || cp .env.example .env

if [ -n "$API_KEY" ]; then
  # ponytail: '|' como delimitador de sed; las API keys de Gemini (AIza...) no lo usan.
  if grep -q '^GEMINI_API_KEY=' .env; then
    sed -i.bak "s|^GEMINI_API_KEY=.*|GEMINI_API_KEY=$API_KEY|" .env && rm -f .env.bak
  else
    echo "GEMINI_API_KEY=$API_KEY" >> .env
  fi
  echo "✓ GEMINI_API_KEY configurada en .env"
else
  echo "ℹ Sin --api_key: la IA queda deshabilitada (las tareas se asignan a mano)."
fi

echo "→ Levantando contenedores…"
docker compose up -d --build
echo "✓ Listo → http://localhost:5173"
