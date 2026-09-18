import markdown

class ContentRenderer:
    """
    Класс для обработки и преобразования контента из Markdown в HTML.
    Отвечает за парсинг инструкций, поддержку таблиц, списков и изображений.
    """

    def __init__(self):
        # Используем расширение 'extra', которое включает в себя:
        # - таблицы (table)
        # - атрибуты контента
        # - подсветку кода
        # - метаданные заголовков
        self.extensions = ['extra', 'codehilite', 'toc']

    def render_markdown(self, content: str) -> str:
        """
        Преобразует Markdown-строку в HTML.

        :param content: Сырой текст из .md файла инструкции.
        :return: Отформатированный HTML-код.
        """
        if not content:
            return ""

        try:
            # Основная конвертация. 
            # Мы не используем здесь фильтры обработки данных, так как данные
            # должны поступать уже очищенными из файлов.
            html = markdown.markdown(content, extensions=self.extensions)
            
            return html
        except Exception as e:
            # Если произошла ошибка парсинга, возвращаем пустую строку 
            # и логируем ошибку (логирование настроено глобально в loader/main).
            return f"<p>Ошибка отображения инструкции.</p>"
