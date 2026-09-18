# Стрижеспасатель (Swift Help)

Волонтёрский сайт-помощник для людей, нашедших стрижа. Пользователь проходит
короткий опрос о состоянии птицы, и в конце получает подходящую инструкцию
по первичным действиям и уходу.

> Информационный проект, не заменяет консультацию ветеринара.

## Технологии
- Python 3.13 + FastAPI (uvicorn)
- Jinja2-шаблоны, инструкции в Markdown

## Структура
- `app/` — FastAPI-приложение (`main`, `loader`, `quiz_engine`, `renderer`) + шаблоны и статика
- `data/` — настройки (`settings.yaml`), дерево вопросов (`questions.json`), статьи (`articles/*.md`)
- `requirements.txt` — зависимости Python

## Запуск
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
# Откройте http://localhost:8000
```

## Лицензия
MIT — см. файл `LICENSE`.
