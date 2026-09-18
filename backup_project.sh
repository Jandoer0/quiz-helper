#!/bin/bash

# --- Конфигурация ---
# Путь к исходному коду (укажите актуальный путь, если он отличается)
SOURCE_DIR="/home/jan/pod/swift-help"
# Папка, куда будут сохраняться бэкапы (можно указать внешний диск или облачную папку)
BACKUP_DIR="/mnt/raid/ivan/Home/Сайты/Сайт swift-help"
# Список исключений (папки, которые НЕ нужно копировать)
EXCLUDE_DIRS="venv|.git|__pycache__|.DS_Store"

# Создаем директорию для бэкапов, если она не существует
mkdir -p "$BACKUP_DIR"

# Формируем имя файла: backup_20231027_153000.tar.gz
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="backup_$TIMESTAMP.tar.gz"

echo "🚀 Начинаю создание резервной копии..."
echo "Источник: $SOURCE_DIR"
echo "Цель: $BACKUP_DIR/$FILENAME"

# Создаем архив
# --exclude убирает зависимости и системные файлы, чтобы бэкап был легким
tar -czf "$BACKUP_DIR/$FILENAME" \
    --exclude="$EXCLUDE_DIRS" \
    -C "$SOURCE_DIR" .

if [ $? -eq 0 ]; then
    echo "✅ Бэкап успешно создан: $BACKUP_DIR/$FILENAME"
else
    echo "❌ Ошибка при создании бэкапа!"
fi
