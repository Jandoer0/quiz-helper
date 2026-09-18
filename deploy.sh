#!/usr/bin/env bash
#
# deploy.sh — деплой проекта «Стрижеспасатель» (Swift Help) на удалённый сервер.
#
# Запуск из корня проекта:  ./deploy.sh
#
# Настройка — через переменные окружения (или измените блок «Конфигурация» ниже):
#   DEPLOY_HOST  — адрес сервера (обязательно, например server.example.com)
#   DEPLOY_USER  — пользователь SSH (по умолчанию root)
#   DEPLOY_PORT  — порт SSH (по умолчанию 22)
#   DEPLOY_DIR   — каталог на сервере (по умолчанию /opt/swift-help)
#   SSH_KEY      — путь к приватному ключу SSH (опционально)
#
# Что делает скрипт:
#   1. Копирует актуальные исходники с вашего ПК на сервер (rsync, исключая мусор).
#   2. На сервере проверяет наличие podman, создаёт сеть и systemd-сервис.
#   3. Сервис стартует приложение (через podman compose) на порту
#      8001 (host) : 8000 (container) и автоматически запускается вместе с сервером.
#
set -euo pipefail

# ===== Конфигурация =====
SERVER_HOST="${DEPLOY_HOST:-}"
SERVER_USER="${DEPLOY_USER:-root}"
SERVER_PORT="${DEPLOY_PORT:-22}"
REMOTE_DIR="${DEPLOY_DIR:-/opt/swift-help}"
SSH_KEY="${SSH_KEY:-}"
SERVICE_NAME="swift-help"

if [[ -z "$SERVER_HOST" ]]; then
  echo "❌ Укажите адрес сервера: DEPLOY_HOST=server.example.com ./deploy.sh" >&2
  exit 1
fi

# Аргументы SSH
SSH_OPTS=(-p "$SERVER_PORT" -o StrictHostKeyChecking=accept-new -o BatchMode=yes)
if [[ -n "$SSH_KEY" ]]; then SSH_OPTS+=(-i "$SSH_KEY"); fi
SSH_TARGET="${SERVER_USER}@${SERVER_HOST}"

# Что НЕ копируем на сервер
EXCLUDES=(
  ".git" "__pycache__" "*.pyc" ".pytest_cache"
  ".build" "scratch" "*.bak*" "venv" ".venv" "swift-help_build"
  ".idea" ".vscode" "PROMT.md"
)
RSYNC_EXCLUDES=()
for e in "${EXCLUDES[@]}"; do RSYNC_EXCLUDES+=(--exclude="$e"); done

echo "🚀 Деплой Swift Help -> ${SSH_TARGET}:${REMOTE_DIR}"

# 1. Копируем исходники на сервер
echo "📦 Копирую исходники (rsync)..."
rsync -avz --delete "${RSYNC_EXCLUDES[@]}" ./ "${SSH_TARGET}:${REMOTE_DIR}/"

# 2. Готовим systemd-юнит локально (с подставленными путями) и копируем на сервер
UNIT_LOCAL="$(mktemp)"
cat > "$UNIT_LOCAL" <<UNIT_EOF
[Unit]
Description=Swift Help — Стрижеспасатель (podman compose)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${REMOTE_DIR}
ExecStartPre=-/usr/bin/podman compose -f ${REMOTE_DIR}/compose.yaml down
ExecStart=/usr/bin/podman compose -f ${REMOTE_DIR}/compose.yaml up
ExecStop=/usr/bin/podman compose -f ${REMOTE_DIR}/compose.yaml down -t 10
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT_EOF

echo "⚙️  Копирую systemd-юнит на сервер..."
scp "${SSH_OPTS[@]}" "$UNIT_LOCAL" "${SSH_TARGET}:/etc/systemd/system/${SERVICE_NAME}.service"
rm -f "$UNIT_LOCAL"

# 3. На сервере: проверяем podman, сеть, включаем и запускаем сервис
echo "🔧 Настраиваю и запускаю сервис на сервере..."
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" bash -s "$SERVICE_NAME" <<'EOF'
set -euo pipefail
SERVICE_NAME="$1"

if ! command -v podman >/dev/null 2>&1; then
  echo "❌ На сервере не найден podman. Установите podman и podman-compose, затем повторите." >&2
  exit 1
fi

# Создаём сеть, если её ещё нет (compose.yaml больше не требует external: true)
podman network exists services-net 2>/dev/null || podman network create services-net

systemctl daemon-reload
systemctl enable --now "${SERVICE_NAME}.service"

echo "✅ Сервис ${SERVICE_NAME} установлен, запущен и добавлен в автозагрузку."
echo "🌐 Приложение доступно на порту 8001 (container: 8000)."
EOF

echo "🎉 Деплой завершён."
