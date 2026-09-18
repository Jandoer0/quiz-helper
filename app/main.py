from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import logging
from pathlib import Path

# Настройка логирования (используется в _safe_validate ниже)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Импорт внутренних модулей проекта
from .loader import DataLoader
from .renderer import ContentRenderer
from .quiz_engine import QuizEngine

# Абсолютный путь к каталогу app/ — чтобы шаблоны и статика находились
# независимо от рабочей директории, из которой запущено приложение.
APP_DIR = Path(__file__).resolve().parent

# Флаг для безопасного повторного вызова валидации.
# Он полезен в тестах: если импорты не завершены — блок проверки пропускается,
# а логирование при этом честно фиксирует факт пропуска (не молчит проблему).
_validation_done = False


def _safe_validate(quiz_data):
    """Запуск проверки целостности дерева решений с защитой от частичных импортов."""
    global _validation_done
    engine = None
    try:
        engine = QuizEngine(quiz_data)
        if not engine.validate_tree():
            logger.error("Validation failed for quiz data.")
    except ImportError as e:
        logger.error("Cannot import QuizEngine - offline test mode, validation skipped.")
        logger.error("Import error: %s", e)
    except Exception as e:
        logger.error("QuizEngine validation error.")
        logger.error("Exception: %s", e)
    else:
        _validation_done = True
    return engine


# 1. Инициализация компонентов данных
data_loader = DataLoader()
settings = data_loader.load_settings()       # Загрузка из settings.yaml
quiz_data = data_loader.load_questions()     # Загрузка из questions.json

# 1.1. Проверка целостности дерева решений с использованием QuizEngine.
# Логика: предупреждения не смертельны - приложение работает дальше,
# но в логах остается заметный след для быстрой диагностики.
_validator = _safe_validate(quiz_data)

# 2. Инициализация движка и рендерера
renderer = ContentRenderer()

# 3. Инициализация приложения FastAPI
app = FastAPI(title=settings.get("site_name", "Стрижеспасатель"))

# 4. Настройка шаблонов и статики (абсолютные пути — надёжнее относительных)
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

# Монтируем статичные файлы (CSS, изображения)
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Главная страница — сразу первый вопрос из JSON анкеты."""
    # Если валидация не вышла в продуктивную фазу (например, тест/юнит),
    # честно помечаем об этом в шапке, чтобы пользователь видел статус.
    _validate_flag = _validation_done

    start_node = settings.get("start_node", "q1")
    question = quiz_data.get(start_node)
    
    if not question:
        # Если начальный узел не найден, берем первый доступный в объекте questions
        questions = quiz_data.get("questions", {})
        nodes = list(questions.keys())
        if nodes:
            question = questions[nodes[0]]
        else:
            raise HTTPException(status_code=404, detail="Анкета пуста.")

    template_args = {
        "request": request,
        "question": question,
        "step": 1,
        "title": settings.get("site_name", "Стрижеспасатель"),
    }
    if not _validate_flag:
        template_args["validate_flag"] = False
    
    return templates.TemplateResponse("index.html", template_args)

@app.get("/question/{q_id}", response_class=HTMLResponse)
async def question_page(request: Request, q_id: str):
    """Страница конкретного вопроса из JSON анкеты."""
    questions = quiz_data.get("questions", {})
    question = questions.get(q_id)
    
    if not question:
        raise HTTPException(status_code=404, detail="Вопрос не найден.")

    # Указываем в шапке статус прохождения валидации quiz_engine.
    validate_flag = _validation_done
    return templates.TemplateResponse("question.html", {
        "request": request,
        "question": question,
        "title": settings.get("site_name", "Стрижеспасатель"),
        "validate_flag": validate_flag
    })

@app.get("/article/{article_id}", response_class=HTMLResponse)
async def article_page(request: Request, article_id: str):
    """Страница финальной инструкции (Markdown)."""
    content = data_loader.load_article(article_id)
    if not content:
        raise HTTPException(status_code=404, detail="Инструкция не найдена.")

    # Собираем все нужные данные из конфига
    html_content = renderer.render_markdown(content)
    contacts = settings.get("contacts")
    
    validate_flag = _validation_done
    return templates.TemplateResponse("article.html", {
        "request": request,
        "content": html_content,
        "contacts": contacts,
        "article_title": article_id,
        "title": article_id,
        "validate_flag": validate_flag
    })

@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """Страница 'О проекте' с юридической информацией и описанием целей."""
    # На статусе проверки целостности анкеты здесь мы уже ничего не меняем,
    # чтобы не задевать другие ветки кода (они вне зоны нашей правки).
    return templates.TemplateResponse("about.html", {
        "request": request,
        "title": "О проекте — Стрижеспасатель"
    })

if __name__ == "__main__":
    # Запуск сервера для локальной разработки (опционально)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
