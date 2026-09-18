from typing import Dict, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Destination:
    """Объект, описывающий цель перехода пользователя."""
    type: str  # "question" или "article"
    id: str    # ID следующего вопроса или имя статьи


class QuizEngine:
    """Движок обработки дерева решений для анкеты."""

    def __init__(self, quiz_data: Dict[str, Any]):
        """
        Инициализация движка данными из JSON.
        :param quiz_data: Полный словарь данных из questions.json
        """
        self.quiz_data = quiz_data

    def get_next_destination(self, question_id: str, answer_choice: Dict[str, Any]) -> Optional[Destination]:
        """
        Определяет следующий шаг на основе выбранного ответа.
        
        Логика приоритетов:
        1. Если в ответе есть ключ 'article' — переход к статье (финал теста).
        2. Если в ответе есть ключ 'next' — переход к следующему вопросу.
        3. Если ключей нет — переход невозможен.

        :param question_id: ID текущего вопроса.
        :param answer_choice: Словарь данных выбранного варианта ответа (например, {"text": "Да", "next": "q2"}).
        :return: Объект Destination или None.
        """
        questions = self.quiz_data.get("questions", {})

        # Если узел не существует в анкете — выходим (не маскируем ошибку молча).
        if question_id not in questions:
            logger.info("Question not found in tree: %s", question_id)
            return None

        # Приоритет 1: Статья (Конечный результат теста)
        article_id = answer_choice.get("article")
        if article_id:
            logger.info("Routing %s -> article '%s'", question_id, article_id)
            return Destination(type="article", id=article_id)

        # Приоритет 2: Следующий вопрос
        next_id = answer_choice.get("next")
        if next_id:
            logger.info("Routing %s -> question '%s'", question_id, next_id)
            return Destination(type="question", id=next_id)

        logger.info("Question %s has no destination for choice %s", question_id, answer_choice)
        return None

    def validate_tree(self) -> bool:
        """
        Проверяет целостность дерева решений:
          - все 'next' ссылаются на существующие вопросы;
          - все 'article' ссылаются на существующие файлы инструкций.

        :return: True, если дерево целостно, иначе False.
        """
        questions = self._questions()
        valid = True

        for q_id, data in questions.items():
            answers = data.get("answers", []) if data else []
            for ans in answers:
                next_q = ans.get("next")
                art = ans.get("article")

                # Проверка: ссылка на следующий вопрос ведёт на существующий узел.
                if next_q is not None and next_q not in questions:
                    valid = False
                    logger.error("Question '%s' links to missing question '%s'", q_id, next_q)

                # Проверка: ссылка на статью ведёт на существующий файл инструкции.
                if art is not None and not self._article_exists(art):
                    valid = False
                    logger.error("Question '%s' links to missing article '%s'", q_id, art)

        return valid

    def _questions(self) -> Dict[str, Any]:
        """Возвращает словарь вопросов с дефолтными значениями при повреждённых данных."""
        return self.quiz_data.get("questions", {}) or {}

    def _article_exists(self, article_id: str) -> bool:
        """
        Проверяет существование файла инструкции data/articles/{article_id}.md.

        :param article_id: Идентификатор статьи (без расширения, напр. 'bleeding').
        :return: True, если файл существует; False, если загружен как пустой контент.
        """
        loader = self._data_loader()
        returned = loader.load_article(article_id) if loader else None
        if loader is None:
            # Без доступа к loaders (тест/юнит) — полагаемся на структуру JSON анкеты.
            return False

        logger.info("Article lookup: '%s' -> %s", article_id, None if returned is None else "found")
        return bool(returned)

    def _data_loader(self):
        """Пытается импортировать реальный DataLoader из проекта."""
        try:
            from app.loader import DataLoader
            return DataLoader()
        except Exception:
            return None
