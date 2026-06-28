#!/usr/bin/env bash
# Crea datos de demo: 1 Scrum Master + 5 Desarrolladores con perfiles distintos.
# El Líder Técnico ya existe por bootstrap (ver .env: BOOTSTRAP_ADMIN_*).
# Uso:  bash scripts/seed_demo.sh        (API en http://localhost:8000)
# Idempotente: si un usuario ya existe, lo informa y sigue.
set -euo pipefail

API="${API:-http://localhost:8000/api}"
TL_EMAIL="${TL_EMAIL:-lider@demo.com}"
TL_PASS="${TL_PASS:-Lider123!}"

jq_field() { python3 -c "import sys,json;print(json.load(sys.stdin).get('$1',''))"; }

echo "→ Login como Líder Técnico ($TL_EMAIL)"
TOKEN=$(curl -s -X POST "$API/auth/login" -H 'Content-Type: application/json' \
  -d "{\"email\":\"$TL_EMAIL\",\"password\":\"$TL_PASS\"}" | jq_field access_token)
if [ -z "$TOKEN" ]; then echo "✗ No se pudo autenticar al TL. ¿Está la API levantada?"; exit 1; fi

# Directorio id→nombre, para reubicar usuarios ya existentes y resetearles la contraseña.
DIRECTORIO=$(curl -s "$API/usuarios/directorio" -H "Authorization: Bearer $TOKEN")
id_por_nombre() {
  python3 -c "import sys,json;d=json.load(sys.stdin);print(next((k for k,v in d.items() if v==sys.argv[1]),''))" "$1" <<<"$DIRECTORIO"
}

crear_usuario() {
  local nombre="$1" email="$2" pass="$3" rol="$4" perfil="$5"
  local resp id
  resp=$(curl -s -X POST "$API/usuarios" -H "Authorization: Bearer $TOKEN" \
    -H 'Content-Type: application/json' \
    -d "{\"nombre\":\"$nombre\",\"email\":\"$email\",\"password\":\"$pass\",\"rol\":\"$rol\",\"perfil\":$perfil}")
  if echo "$resp" | grep -q '"id_usuario"'; then
    echo "  ✓ creado       $rol  $nombre  <$email>"
    return
  fi
  if echo "$resp" | grep -qi "ya existe"; then
    # Idempotente: si ya existía, le reseteo la contraseña a la documentada.
    id=$(id_por_nombre "$nombre")
    if [ -n "$id" ]; then
      curl -s -o /dev/null -X PUT "$API/usuarios/$id" -H "Authorization: Bearer $TOKEN" \
        -H 'Content-Type: application/json' \
        -d "{\"nombre\":\"$nombre\",\"password\":\"$pass\",\"perfil\":$perfil}"
      echo "  ↻ actualizado  $rol  $nombre  <$email>  (contraseña reseteada)"
    else
      echo "  • ya existía   $nombre <$email> con otro nombre; no pude resetear."
      echo "                 Para empezar limpio: docker compose down -v && docker compose up -d"
    fi
    return
  fi
  echo "  ✗ $nombre: $resp"
}

echo "→ Creando Scrum Master"
crear_usuario "Sofia Mendez" "sm@demo.com"   "ScrumM1!" "SCRUM_MASTER" '{}'

echo "→ Creando 5 Desarrolladores con perfiles distintos"
crear_usuario "Ana Lopez"   "ana@demo.com"   "DevAna1!"   "DESARROLLADOR" \
  '{"seniority":"Senior","lenguajes":["python","sql"],"frameworks":["fastapi"],"dominios":["backend","apis"]}'
crear_usuario "Bruno Diaz"  "bruno@demo.com" "DevBruno1!" "DESARROLLADOR" \
  '{"seniority":"Senior","lenguajes":["javascript","typescript"],"frameworks":["react"],"dominios":["frontend","ui"]}'
crear_usuario "Carla Ruiz"  "carla@demo.com" "DevCarla1!" "DESARROLLADOR" \
  '{"seniority":"Semi Senior","lenguajes":["python"],"frameworks":["django"],"dominios":["backend","datos"]}'
crear_usuario "Diego Sosa"  "diego@demo.com" "DevDiego1!" "DESARROLLADOR" \
  '{"seniority":"Junior","lenguajes":["javascript"],"frameworks":["node","express"],"dominios":["backend"]}'
crear_usuario "Elena Vega"  "elena@demo.com" "DevElena1!" "DESARROLLADOR" \
  '{"seniority":"Semi Senior","lenguajes":["java","kotlin"],"frameworks":["spring"],"dominios":["backend","mobile"]}'

login() {
  curl -s -X POST "$API/auth/login" -H 'Content-Type: application/json' \
    -d "{\"email\":\"$1\",\"password\":\"$2\"}" | jq_field access_token
}

# ─── Sprint activo + backlog de demo (todas las tareas con descripción) ───
SPRINTS=$(curl -s "$API/sprints" -H "Authorization: Bearer $TOKEN")
if [ "$SPRINTS" = "[]" ]; then
  echo "→ Creando sprint activo (Scrum Master)"
  SM_TOKEN=$(login "sm@demo.com" "ScrumM1!")
  HOY=$(python3 -c "import datetime;print(datetime.date.today())")
  FIN=$(python3 -c "import datetime;print(datetime.date.today()+datetime.timedelta(days=14))")
  SPRINT=$(curl -s -X POST "$API/sprints" -H "Authorization: Bearer $SM_TOKEN" \
    -H 'Content-Type: application/json' \
    -d "{\"objetivo\":\"Sprint 1 — MVP de TaskFlow AI\",\"fecha_inicio\":\"$HOY\",\"fecha_fin\":\"$FIN\"}")
  SPRINT_ID=$(echo "$SPRINT" | jq_field id_sprint)
  curl -s -o /dev/null -X PUT "$API/sprints/$SPRINT_ID" -H "Authorization: Bearer $SM_TOKEN" \
    -H 'Content-Type: application/json' -d '{"estado":"ACTIVO"}'
  echo "  ✓ sprint #$SPRINT_ID activo"

  echo "→ Creando backlog (Líder Técnico) — la IA asigna cada tarea si hay GEMINI_API_KEY"
  crear_tarea() {
    curl -s -o /dev/null -X POST "$API/sprints/$SPRINT_ID/tareas" \
      -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
      -d "{\"descripcion\":\"$1\",\"prioridad\":\"$2\"}"
    echo "  ✓ $2  $1"
  }
  crear_tarea "Implementar endpoint REST de autenticación con JWT en FastAPI" "ALTA"
  crear_tarea "Construir el tablero Kanban del sprint en React con TypeScript" "ALTA"
  crear_tarea "Modelar el esquema de perfiles de desarrollador en MongoDB" "MEDIA"
  crear_tarea "Diseñar la API de asignación automática de tareas con Gemini" "CRITICA"
  crear_tarea "Crear la pantalla de login responsive con validación de formularios" "MEDIA"
  crear_tarea "Configurar el microservicio de notificaciones en Spring Boot" "BAJA"
  crear_tarea "Optimizar las consultas SQL del dashboard de métricas" "MEDIA"
  crear_tarea "Documentar la API REST con OpenAPI y ejemplos de uso" "BAJA"
else
  echo "→ Ya existen sprints; omito sembrar el backlog."
fi

cat <<'TABLA'

╔═══════════════════════════════════════════════════════════════╗
║                 CREDENCIALES DE DEMO (TaskFlow AI)            ║
╠═══════════════╦══════════════════╦════════════════════════════╣
║ Rol           ║ Email            ║ Contraseña                 ║
╠═══════════════╬══════════════════╬════════════════════════════╣
║ Líder Técnico ║ lider@demo.com   ║ Lider123!                  ║
║ Scrum Master  ║ sm@demo.com      ║ ScrumM1!                   ║
║ Desarrollador ║ ana@demo.com     ║ DevAna1!     (Senior BE)   ║
║ Desarrollador ║ bruno@demo.com   ║ DevBruno1!   (Senior FE)   ║
║ Desarrollador ║ carla@demo.com   ║ DevCarla1!   (SSr datos)   ║
║ Desarrollador ║ diego@demo.com   ║ DevDiego1!   (Jr node)     ║
║ Desarrollador ║ elena@demo.com   ║ DevElena1!   (SSr java)    ║
╚═══════════════╩══════════════════╩════════════════════════════╝

Listo. Entrá en http://localhost:5173 con cualquiera de estas cuentas.
TABLA
