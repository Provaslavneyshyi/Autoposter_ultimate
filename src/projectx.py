# projectx.py

import time
import re
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QComboBox, QCheckBox, QSpinBox, QTextEdit, QGroupBox, QMessageBox
)
import Scripts
from Data import save_data

# Worker для ручной генерации статей для одного профиля
class ManualGenerationWorker(QThread):
    log_signal = pyqtSignal(str)
    article_generated = pyqtSignal(str, dict)  # отправляет (profile_url, article)

    def __init__(self, profile, prompt, image_prompt, count, image_enabled, api_key, parent=None):
        super().__init__(parent)
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
            article_text = Scripts.generate_article_text(
                self.api_key, self.prompt,
                lambda msg: self.log_signal.emit(f"На профиль {profile_url}: {msg}")
            )
            if not article_text:
                self.log_signal.emit(f"На профиль {profile_url}: Ошибка генерации статьи")
                continue
            html_text = Scripts.format_text_to_html(
                article_text,
                lambda msg: self.log_signal.emit(f"На профиль {profile_url}: {msg}")
            )
            pixmap = None
            if self.image_enabled:
                self.log_signal.emit(f"На профиль {profile_url}: Начало генерации изображения")
                pixmap = Scripts.generate_image(
                    self.api_key, self.image_prompt,
                    lambda msg: self.log_signal.emit(f"На профиль {profile_url}: {msg}")
                )
                if pixmap:
                    self.log_signal.emit(f"На профиль {profile_url}: Изображение сгенерировано")
                else:
                    self.log_signal.emit(f"На профиль {profile_url}: Ошибка генерации изображения")
            title = self.extract_title(html_text)
            article = {"title": title, "content": html_text, "image": pixmap}
            self.article_generated.emit(profile_url, article)
            self.log_signal.emit(f"На профиль {profile_url}: Сгенерированна статья")
            time.sleep(0.1)  # небольшая задержка

    def extract_title(self, html):
        pattern = re.compile(r'<h[1-6]>(.*?)</h[1-6]>', re.IGNORECASE)
        match = pattern.search(html)
        if match:
            title = match.group(1).strip()
            if title:
                return title
        return "Без заголовка"

# Worker для ручного постинга статей для одного профиля
class ManualPostingWorker(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, profile, article, category, api_key, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.article = article
        self.category = category
        self.api_key = api_key

    def run(self):
        profile_url = self.profile["url"]
        title = self.article.get("title", "Без заголовка")
        self.log_signal.emit(f"На профиль {profile_url}: Начало постинга статьи")
        result, error = Scripts.publish_article(
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
        else:
            self.log_signal.emit(f"На профиль {profile_url}: Ошибка публикации: {error}")

# Worker для автоматической генерации и постинга для одного профиля
class AutoGenerationPostingWorker(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, profile, prompt, image_prompt, count, interval, image_enabled, api_key, category, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.prompt = prompt
        self.image_prompt = image_prompt
        self.count = count
        self.interval = interval * 60  # переводим минуты в секунды
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
            article_text = Scripts.generate_article_text(
                self.api_key, self.prompt,
                lambda msg: self.log_signal.emit(f"На профиль {profile_url}: {msg}")
            )
            if not article_text:
                self.log_signal.emit(f"На профиль {profile_url}: Ошибка генерации статьи")
                continue
            html_text = Scripts.format_text_to_html(
                article_text,
                lambda msg: self.log_signal.emit(f"На профиль {profile_url}: {msg}")
            )
            pixmap = None
            if self.image_enabled:
                self.log_signal.emit(f"На профиль {profile_url}: Авто-генерация изображения начата")
                pixmap = Scripts.generate_image(
                    self.api_key, self.image_prompt,
                    lambda msg: self.log_signal.emit(f"На профиль {profile_url}: {msg}")
                )
                if pixmap:
                    self.log_signal.emit(f"На профиль {profile_url}: Изображение сгенерировано")
                else:
                    self.log_signal.emit(f"На профиль {profile_url}: Ошибка генерации изображения")
            title = self.extract_title(html_text)
            article = {"title": title, "content": html_text, "image": pixmap}
            self.log_signal.emit(f"На профиль {profile_url}: Статья сгенерирована, начало постинга")
            result, error = Scripts.publish_article(
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
            else:
                self.log_signal.emit(f"На профиль {profile_url}: Ошибка публикации: {error}")
            # Если это не последняя итерация, ждём указанный интервал
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

# Основной виджет вкладки "Mass Project"
class MassProjectTab(QWidget):
    def __init__(self, data, log_callback, parent=None):
        super().__init__(parent)
        self.data = data
        self.log_callback = log_callback
        self.generated_articles = {}
        self.auto_workers = {}
        # Добавляем списки для ручных потоков
        self.manual_workers = []
        self.manual_post_workers = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Блок выбора профилей сайтов
        profiles_group = QGroupBox("Выберите профили сайтов")
        profiles_layout = QVBoxLayout()
        self.profilesList = QListWidget()
        self.profilesList.setSelectionMode(QListWidget.NoSelection)  # Используем только чекбоксы для выбора
        for profile in self.data.get("profiles", []):
            item = QListWidgetItem(profile["url"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            # Если поле "selected" отсутствует, считаем его False
            if profile.get("selected", False):
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self.profilesList.addItem(item)
        # Обработчик изменения состояния элемента
        self.profilesList.itemChanged.connect(self.handle_profile_item_changed)
        profiles_layout.addWidget(self.profilesList)
        profiles_group.setLayout(profiles_layout)
        layout.addWidget(profiles_group)

        # Блок настроек генерации статей
        prompt_group = QGroupBox("Настройки генерации статей")
        prompt_layout = QVBoxLayout()

        hlayout1 = QHBoxLayout()
        hlayout1.addWidget(QLabel("Промпт статьи:"))
        self.promptCombo = QComboBox()
        for prompt in self.data.get("prompts", []):
            self.promptCombo.addItem(prompt)
        hlayout1.addWidget(self.promptCombo)
        prompt_layout.addLayout(hlayout1)

        hlayout2 = QHBoxLayout()
        hlayout2.addWidget(QLabel("Промпт изображения:"))
        self.imagePromptCombo = QComboBox()
        for prompt in self.data.get("image_prompts", []):
            self.imagePromptCombo.addItem(prompt)
        hlayout2.addWidget(self.imagePromptCombo)
        prompt_layout.addLayout(hlayout2)

        self.imageCheck = QCheckBox("Генерация изображений")
        self.imageCheck.setChecked(True)
        prompt_layout.addWidget(self.imageCheck)

        hlayout3 = QHBoxLayout()
        hlayout3.addWidget(QLabel("Кол-во статей:"))
        self.countSpin = QSpinBox()
        self.countSpin.setMinimum(1)
        self.countSpin.setValue(3)
        hlayout3.addWidget(self.countSpin)
        prompt_layout.addLayout(hlayout3)

        hlayout4 = QHBoxLayout()
        hlayout4.addWidget(QLabel("Интервал (мин):"))
        self.intervalSpin = QSpinBox()
        self.intervalSpin.setMinimum(1)
        self.intervalSpin.setValue(5)
        hlayout4.addWidget(self.intervalSpin)
        prompt_layout.addLayout(hlayout4)

        hlayout5 = QHBoxLayout()
        hlayout5.addWidget(QLabel("Категория:"))
        self.categoryCombo = QComboBox()
        for cat in self.data.get("categories", []):
            self.categoryCombo.addItem(cat)
        hlayout5.addWidget(self.categoryCombo)
        prompt_layout.addLayout(hlayout5)

        prompt_group.setLayout(prompt_layout)
        layout.addWidget(prompt_group)

        # Кнопки для ручных операций
        manual_buttons_layout = QHBoxLayout()
        self.manualGenBtn = QPushButton("Ручная генерация статей")
        self.manualGenBtn.clicked.connect(self.handle_manual_generation)
        manual_buttons_layout.addWidget(self.manualGenBtn)

        self.manualPostBtn = QPushButton("Ручной постинг статей")
        self.manualPostBtn.clicked.connect(self.handle_manual_posting)
        manual_buttons_layout.addWidget(self.manualPostBtn)
        layout.addLayout(manual_buttons_layout)

        # Кнопки для авто-режима
        auto_buttons_layout = QHBoxLayout()
        self.autoStartBtn = QPushButton("Старт авто генерации и постинга")
        self.autoStartBtn.clicked.connect(self.handle_auto_start)
        auto_buttons_layout.addWidget(self.autoStartBtn)
        self.autoStopBtn = QPushButton("Стоп авто генерации и постинга")
        self.autoStopBtn.clicked.connect(self.handle_auto_stop)
        auto_buttons_layout.addWidget(self.autoStopBtn)
        layout.addLayout(auto_buttons_layout)

        # Отображение лога действий
        self.logEdit = QTextEdit()
        self.logEdit.setReadOnly(True)
        layout.addWidget(QLabel("Лог действий:"))
        layout.addWidget(self.logEdit)

        self.setLayout(layout)

    def append_log(self, message):
        self.logEdit.append(message)
        self.log_callback(message)

    def get_selected_profiles(self):
        selected_profiles = []
        for index in range(self.profilesList.count()):
            item = self.profilesList.item(index)
            if item.checkState() == Qt.Checked:
                url = item.text()
                for profile in self.data.get("profiles", []):
                    if profile["url"] == url:
                        selected_profiles.append(profile)
                        break
        return selected_profiles

    def handle_manual_generation(self):
        selected_profiles = self.get_selected_profiles()
        if not selected_profiles:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы один профиль.")
            return
        count = self.countSpin.value()
        prompt = self.promptCombo.currentText()
        image_prompt = self.imagePromptCombo.currentText()
        image_enabled = self.imageCheck.isChecked()
        api_keys = self.data.get("api_keys", [])
        if not api_keys:
            QMessageBox.warning(self, "Ошибка", "Не добавлен ни один API-ключ.")
            return
        api_key = api_keys[0]
        for profile in selected_profiles:
            worker = ManualGenerationWorker(profile, prompt, image_prompt, count, image_enabled, api_key)
            worker.log_signal.connect(self.append_log)
            worker.article_generated.connect(self.store_generated_article)
            # Сохраняем ссылку на поток, чтобы он не был уничтожен сборщиком
            self.manual_workers.append(worker)
            # После завершения потока удаляем его из списка
            worker.finished.connect(lambda w=worker: self.manual_workers.remove(w))
            worker.start()

    def store_generated_article(self, profile_url, article):
        if profile_url not in self.generated_articles:
            self.generated_articles[profile_url] = []
        self.generated_articles[profile_url].append(article)

    def handle_manual_posting(self):
        selected_profiles = self.get_selected_profiles()
        if not selected_profiles:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы один профиль.")
            return
        category = self.categoryCombo.currentText()
        api_keys = self.data.get("api_keys", [])
        if not api_keys:
            QMessageBox.warning(self, "Ошибка", "Не добавлен ни один API-ключ.")
            return
        api_key = api_keys[0]
        for profile in selected_profiles:
            profile_url = profile["url"]
            articles = self.generated_articles.get(profile_url, [])
            if not articles:
                self.append_log(f"На профиль {profile_url}: Нет сгенерированных статей для постинга.")
                continue
            for article in articles:
                worker = ManualPostingWorker(profile, article, category, api_key)
                worker.log_signal.connect(self.append_log)
                self.manual_post_workers.append(worker)
                worker.finished.connect(lambda w=worker: self.manual_post_workers.remove(w))
                worker.start()
            self.generated_articles[profile_url] = []

    def handle_auto_start(self):
        selected_profiles = self.get_selected_profiles()
        if not selected_profiles:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы один профиль.")
            return
        count = self.countSpin.value()
        interval = self.intervalSpin.value()
        prompt = self.promptCombo.currentText()
        image_prompt = self.imagePromptCombo.currentText()
        image_enabled = self.imageCheck.isChecked()
        category = self.categoryCombo.currentText()
        api_keys = self.data.get("api_keys", [])
        if not api_keys:
            QMessageBox.warning(self, "Ошибка", "Не добавлен ни один API-ключ.")
            return
        api_key = api_keys[0]
        for profile in selected_profiles:
            worker = AutoGenerationPostingWorker(profile, prompt, image_prompt, count, interval, image_enabled, api_key, category)
            worker.log_signal.connect(self.append_log)
            worker.start()
            self.auto_workers[profile["url"]] = worker

    def handle_auto_stop(self):
        for url, worker in self.auto_workers.items():
            worker.stop()
            self.append_log(f"На профиль {url}: Авто-генерация и постинг остановлены.")
        self.auto_workers.clear()

    def handle_profile_item_changed(self, item):
        url = item.text()
        new_state = True if item.checkState() == Qt.Checked else False
        # Обновляем состояние выбранности в данных для соответствующего профиля
        for profile in self.data.get("profiles", []):
            if profile["url"] == url:
                profile["selected"] = new_state
                break
        save_data(self.data)

