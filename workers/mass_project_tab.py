# workers/mass_project_tab.py

import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QListWidget, QLabel, QHBoxLayout,
    QPushButton, QMessageBox, QTextEdit, QComboBox, QSpinBox, QCheckBox
)
from PyQt5.QtCore import Qt
from data.data_manager import save_data
from workers.manual_workers import ManualGenerationWorker, ManualPostingWorker
from workers.auto_workers import AutoGenerationPostingWorker

class MassProjectTab(QWidget):
    def __init__(self, data, log_callback, parent=None):
        super().__init__(parent)
        self.data = data
        self.log_callback = log_callback
        self.generated_articles = {}  # локальное хранение сгенерированных в рамках сеанса
        self.auto_workers = {}
        self.manual_workers = []
        self.manual_post_workers = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        profiles_group = QGroupBox("Выберите профили сайтов")
        profiles_layout = QVBoxLayout()
        self.profilesList = QListWidget()
        self.profilesList.setSelectionMode(QListWidget.NoSelection)
        profiles_layout.addWidget(self.profilesList)
        profiles_group.setLayout(profiles_layout)
        layout.addWidget(profiles_group)

        # Кнопка "Обновить" для пересборки списка профилей
        refresh_btn = QPushButton("Обновить список профилей")
        refresh_btn.clicked.connect(self.refresh_profile_list)
        profiles_layout.addWidget(refresh_btn)

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
        self.imageCheck.setChecked(False)
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

        manual_buttons_layout = QHBoxLayout()
        self.manualGenBtn = QPushButton("Ручная генерация статей")
        self.manualGenBtn.clicked.connect(self.handle_manual_generation)
        manual_buttons_layout.addWidget(self.manualGenBtn)
        self.manualPostBtn = QPushButton("Ручной постинг статей")
        self.manualPostBtn.clicked.connect(self.handle_manual_posting)
        manual_buttons_layout.addWidget(self.manualPostBtn)
        layout.addLayout(manual_buttons_layout)

        auto_buttons_layout = QHBoxLayout()
        self.autoStartBtn = QPushButton("Старт авто генерации и постинга")
        self.autoStartBtn.clicked.connect(self.handle_auto_start)
        auto_buttons_layout.addWidget(self.autoStartBtn)
        self.autoStopBtn = QPushButton("Стоп авто генерации и постинга")
        self.autoStopBtn.clicked.connect(self.handle_auto_stop)
        auto_buttons_layout.addWidget(self.autoStopBtn)
        layout.addLayout(auto_buttons_layout)

        self.logEdit = QTextEdit()
        self.logEdit.setReadOnly(True)
        layout.addWidget(QLabel("Лог действий:"))
        layout.addWidget(self.logEdit)
        self.setLayout(layout)

        # В конце init_ui обновляем список
        self.refresh_profile_list()

    def append_log(self, message):
        self.logEdit.append(message)
        self.log_callback(message)

    def refresh_profile_list(self):
        """
        Пересобирает список профилей, отображая для каждого URL
        количество сгенерированных и опубликованных статей.
        """
        self.profilesList.clear()
        profiles = self.data.get("profiles", [])
        for profile in profiles:
            url = profile["url"]
            gen_count, pub_count = self.get_profile_counts(url)
            # Отображаем URL + статистику
            from PyQt5.QtWidgets import QListWidgetItem
            item_text = f"{url} (Сгенерировано: {gen_count}, Опубликовано: {pub_count})"
            item = QListWidgetItem(item_text)
            # Добавим флажок выбора (если нужно, как было ранее)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if profile.get("selected", False) else Qt.Unchecked)
            self.profilesList.addItem(item)

    def get_profile_counts(self, url):
        """
        Возвращает (количество_сгенерированных, количество_опубликованных)
        для заданного URL.
        """
        gen_list = self.data.get("generated_articles", [])
        pub_list = self.data.get("published_articles", [])

        gen_count = sum(1 for art in gen_list if art.get("profile_url") == url)
        pub_count = sum(1 for art in pub_list if art.get("profile_url") == url)
        return gen_count, pub_count

    def get_selected_profiles(self):
        selected_profiles = []
        for index in range(self.profilesList.count()):
            item = self.profilesList.item(index)
            if item.checkState() == Qt.Checked:
                # Ищем профиль в self.data["profiles"] по URL
                text = item.text()
                # Текст в формате: "https://site (Сгенерировано: X, Опубликовано: Y)"
                # Поэтому вырезаем URL до пробела или ищем скобку
                url_part = text.split(" (")[0]
                for profile in self.data.get("profiles", []):
                    if profile["url"] == url_part:
                        selected_profiles.append(profile)
                        break
        return selected_profiles

    def handle_profile_item_changed(self, item):
        # Обновляем флаг "selected" в data
        text = item.text()
        url_part = text.split(" (")[0]
        new_state = True if item.checkState() == Qt.Checked else False
        for profile in self.data.get("profiles", []):
            if profile["url"] == url_part:
                profile["selected"] = new_state
                break
        save_data(self.data)

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
            worker = ManualGenerationWorker(
                data=self.data,
                profile=profile,
                prompt=prompt,
                image_prompt=image_prompt,
                count=count,
                image_enabled=image_enabled,
                api_key=api_key
            )
            worker.log_signal.connect(self.append_log)
            worker.article_generated.connect(self.store_generated_article)
            self.manual_workers.append(worker)
            worker.finished.connect(lambda w=worker: self.manual_workers.remove(w))
            worker.start()

    def store_generated_article(self, profile_url, article):
        """
        Локально храним сгенерированные статьи в self.generated_articles
        (ключ = profile_url). Это не обязательно, так как мы уже
        сохранили статью в data['generated_articles'] внутри воркера,
        но можно дополнительно хранить для удобства.
        """
        if profile_url not in self.generated_articles:
            self.generated_articles[profile_url] = []
        self.generated_articles[profile_url].append(article)
        # Обновляем отображение счётчиков
        self.refresh_profile_list()

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
                worker = ManualPostingWorker(
                    data=self.data,
                    profile=profile,
                    article=article,
                    category=category,
                    api_key=api_key
                )
                worker.log_signal.connect(self.append_log)
                worker.finished.connect(lambda w=worker: self.manual_post_workers.remove(w))
                self.manual_post_workers.append(worker)
                worker.start()
            # Очистим локальный список, чтобы не постить одну и ту же статью повторно
            self.generated_articles[profile_url] = []

        # После запуска постинга обновим счётчики
        self.refresh_profile_list()

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
            worker = AutoGenerationPostingWorker(
                data=self.data,
                profile=profile,
                prompt=prompt,
                image_prompt=image_prompt,
                count=count,
                interval=interval,
                image_enabled=image_enabled,
                api_key=api_key,
                category=category
            )
            worker.log_signal.connect(self.append_log)
            worker.start()
            self.auto_workers[profile["url"]] = worker

        # Обновим список (изменения будут заметны по мере генерации/публикации)
        self.refresh_profile_list()

    def handle_auto_stop(self):
        for url, worker in self.auto_workers.items():
            worker.stop()
            worker.wait()  # Ждем, пока поток корректно завершится
            self.append_log(f"На профиль {url}: Авто-генерация и постинг остановлены.")
        self.auto_workers.clear()
        self.refresh_profile_list()
