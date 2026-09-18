import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Настройка логирования согласно стандартам Senior разработки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLoader:
    """
    Класс для загрузки и управления конфигурационными данными приложения.
    Отвечает за чтение JSON (анкета), YAML (настройки) и Markdown (статьи).
    """

    def __init__(self):
        # Определяем пути относительно файла текущего модуля.
        # Это обеспечивает корректную работу в Docker-контейнере и разных ОС.
        self.base_path = Path(__file__).resolve().parent.parent
        self.data_dir = self.base_path / "data"
        self.articles_dir = self.data_dir / "articles"

        # Проверка наличия структуры данных при инициализации
        self._validate_structure()

    def _validate_structure(self) -> None:
        """Проверяет наличие обязательных папок для работы приложения."""
        required_dirs = [self.data_dir, self.articles_dir]
        for directory in required_dirs:
            if not directory.exists():
                logger.warning(f"Directory missing: {directory}. Creating it...")
                directory.mkdir(parents=True, exist_ok=True)

    def load_settings(self) -> Dict[str, Any]:
        """
        Загружает общие настройки сайта из файла data/settings.yaml.
        
        :return: Словарь с настройками или дефолтные значения.
        """
        path = self.data_dir / "settings.yaml"
        try:
            with open(path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config if config else {}
        except FileNotFoundError:
            logger.error(f"Settings file not found at {path}")
            return {"site_name": "Стрижеспасатель", "footer": ""}
        except Exception as e:
            logger.error(f"Unexpected error loading settings: {e}")
            return {}

    def load_questions(self) -> Dict[str, Any]:
        """
        Загружает дерево вопросов из файла data/questions.json.
        
        :return: Словарь с данными анкеты (включая ключи 'start_node' и 'questions').
        """
        path = self.data_dir / "questions.json"
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Questions file not found at {path}")
            return {"start_node": "q1", "questions": {}}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode questions JSON: {e}")
            return {"start_node": "q1", "questions": {}}

    def load_article(self, article_id: str) -> Optional[str]:
        """
        Загружает содержимое Markdown-файла инструкции по идентификатору.
        Принимает ID без расширения .md.

        :param article_id: Идентификатор статьи (например, 'bleeding')
        :return: Строка с контентом или None, если статья не найдена.
        """
        # Формируем путь к файлу: data/articles/{article_id}.md
        path = self.articles_dir / f"{article_id}.md"
        
        if not path.exists():
            logger.warning(f"Article file not found: {path}")
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading article content for {article_id}: {e}")
            return None

# Пример использования в других модулях:
# loader = DataLoader()
# settings = loader.load_settings()
# questions = loader.load_questions()