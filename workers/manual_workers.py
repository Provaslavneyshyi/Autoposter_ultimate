# workers/manual_workers.py

import time
import re
from PyQt5.QtCore import QThread, pyqtSignal
from services.openai_service import generate_article_text, generate_image
from services.markdown_converter import format_text_to_html
from services.wordpress import publish_article
from data.data_manager import save_data
from utils.helpers import extract_title_from_html

class ManualGenerationWorker(QThread):
    log_signal = pyqtSignal(str)
    article_generated = pyqtSignal(str, dict)  # отправляет (profile_url, article)

    def __init__(self, data, profile, prompt, image_prompt, count, image_enabled, api_key, parent=None):
        """
        Args:
            data (dict): Ссылка на общий словарь данных.
            profile (dict): Профиль сайта (url, login, app_password).
            prompt (str): Промпт для статьи.
            image_prompt (str): Промпт для изображения.
            count (int): Количество статей для генерации.
            image_enabled (bool): Флаг генерации изображений.
            api_key (str): API-ключ OpenAI.
        """
        super().__init__(parent)
        self.data = data
        self.profile = profile
        self.prompt = prompt
        self.image_prompt = image_prompt
        self.count = count
        self.image_enabled = image_enabled
        self.api_key = api_key

    def run(self):
        profile_url = self.profile["url"]
        for i in range(self.count):
            self.log_signal.emit(f"На профиль {profile_url}: Начало генерации статьи")
            article_text = generate_article_text(
                self.api_key, self.prompt,
                lambda msg: self.log_signal.emit(f"На профиль {profile_url}: {msg}")
            )
            if not article_text:
                self.log_signal.emit(f"На профиль {profile_url}: Ошибка генерации статьи")
                continue

            html_text = format_text_to_html(
                article_text,
                lambda msg: self.log_signal.emit(f"На профиль {profile_url}: {msg}")
            )

            pixmap = None
            if self.image_enabled:
                self.log_signal.emit(f"На профиль {profile_url}: Начало генерации изображения")
                pixmap = generate_image(
                    self.api_key, self.image_prompt,
                    lambda msg: self.log_signal.emit(f"На профиль {profile_url}: {msg}")
                )
                if pixmap:
                    self.log_signal.emit(f"На профиль {profile_url}: Изображение сгенерировано")
                else:
                    self.log_signal.emit(f"На профиль {profile_url}: Ошибка генерации изображения")

            title = self.extract_title(html_text)
            article = {"title": title, "content": html_text, "image": pixmap}

            # Сохраняем факт генерации статьи в data["generated_articles"]
            gen_list = self.data.get("generated_articles", [])
            gen_list.append({
                "title": title,
                "profile_url": profile_url,
                "timestamp": time.time()
            })
            self.data["generated_articles"] = gen_list
            save_data(self.data)

            self.article_generated.emit(profile_url, article)
            self.log_signal.emit(f"На профиль {profile_url}: Сгенерирована статья")
            time.sleep(0.1)

    def extract_title(self, html):
        return extract_title_from_html(html)


class ManualPostingWorker(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, data, profile, article, category, api_key, parent=None):
        """
        Args:
            data (dict): Ссылка на общий словарь данных.
            profile (dict): Профиль сайта (url, login, app_password).
            article (dict): Словарь со статьёй ("title", "content", "image").
            category (str): Категория (ID или имя).
            api_key (str): API-ключ OpenAI.
        """
        super().__init__(parent)
        self.data = data
        self.profile = profile
        self.article = article
        self.category = category
        self.api_key = api_key

    def run(self):
        profile_url = self.profile["url"]
        title = self.article.get("title", "Без заголовка")
        self.log_signal.emit(f"На профиль {profile_url}: Начало постинга статьи")

        result, error = publish_article(
            self.profile["url"],
            self.profile["login"],
            self.profile["app_password"],
            title,
            self.article["content"],
            self.category,
            lambda msg: self.log_signal.emit(f"На профиль {profile_url}: {msg}")
        )
        if result:
            self.log_signal.emit(f"На профиль {profile_url}: Загружена статья")

            # Сохраняем факт публикации в data["published_articles"]
            pub_list = self.data.get("published_articles", [])
            pub_list.append({
                "title": title,
                "link": result.get("link", profile_url),
                "profile_url": profile_url,
                "timestamp": time.time()
            })
            self.data["published_articles"] = pub_list
            save_data(self.data)
        else:
            self.log_signal.emit(f"На профиль {profile_url}: Ошибка публикации: {error}")
