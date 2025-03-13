import time
import re
from PyQt5.QtCore import QThread, pyqtSignal
from services.openai_service import generate_article_text, generate_image
from services.markdown_converter import format_text_to_html
from services.wordpress import publish_article
from data.data_manager import save_data

class AutoGenerationPostingWorker(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, data, profile, prompt, image_prompt, count, interval, image_enabled, api_key, category, parent=None):
        """
        Args:
            data (dict): Ссылка на общий словарь данных.
            profile (dict): Профиль сайта (url, login, app_password).
            prompt (str): Промпт для статьи.
            image_prompt (str): Промпт для изображения.
            count (int): Количество статей для генерации.
            interval (int): Интервал в минутах.
            image_enabled (bool): Флаг генерации изображений.
            api_key (str): API-ключ OpenAI.
            category (str): Категория (ID или имя).
        """
        super().__init__(parent)
        self.data = data
        self.profile = profile
        self.prompt = prompt
        self.image_prompt = image_prompt
        self.count = count
        self.interval = interval * 60  # минуты -> секунды
        self.image_enabled = image_enabled
        self.api_key = api_key
        self.category = category
        self._stopped = False

    def run(self):
        profile_url = self.profile["url"]
        for i in range(self.count):
            if self._stopped:
                break
            self.log_signal.emit(f"На профиль {profile_url}: Авто-генерация статьи начата")

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
                self.log_signal.emit(f"На профиль {profile_url}: Авто-генерация изображения начата")
                pixmap = generate_image(
                    self.api_key, self.image_prompt,
                    lambda msg: self.log_signal.emit(f"На профиль {profile_url}: {msg}")
                )
                if pixmap:
                    self.log_signal.emit(f"На профиль {profile_url}: Изображение сгенерировано")
                else:
                    self.log_signal.emit(f"На профиль {profile_url}: Ошибка генерации изображения")

            title = self.extract_title(html_text)
            self.log_signal.emit(f"На профиль {profile_url}: Статья сгенерирована, начало постинга")

            # Сохраняем факт генерации
            gen_list = self.data.get("generated_articles", [])
            gen_list.append({
                "title": title,
                "profile_url": profile_url,
                "timestamp": time.time()
            })
            self.data["generated_articles"] = gen_list
            save_data(self.data)

            result, error = publish_article(
                self.profile["url"],
                self.profile["login"],
                self.profile["app_password"],
                title,
                html_text,
                self.category,
                lambda msg: self.log_signal.emit(f"На профиль {profile_url}: {msg}")
            )
            if result:
                self.log_signal.emit(f"На профиль {profile_url}: Загружена статья")

                # Сохраняем факт публикации
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

            if i < self.count - 1:
                for _ in range(int(self.interval)):
                    if self._stopped:
                        break
                    time.sleep(1)
                if self._stopped:
                    break

    def stop(self):
        self._stopped = True

    def extract_title(self, html):
        pattern = re.compile(r'<h[1-6]>(.*?)</h[1-6]>', re.IGNORECASE)
        match = pattern.search(html)
        if match:
            title = match.group(1).strip()
            if title:
                return title
        return "Без заголовка"
