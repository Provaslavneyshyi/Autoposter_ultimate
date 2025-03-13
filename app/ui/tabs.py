import re, schedule
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTextEdit,
                             QCheckBox, QPushButton, QSpinBox, QListWidget, QGroupBox, QMessageBox)
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QSizePolicy
from data.data_manager import save_data
import Scripts  # Пока оставляем для вызова генерации и публикации через функции из сервиса
from utils.helpers import extract_title_from_html

class ContentTab(QWidget):
    def __init__(self, parent, data, log_callback, update_statistics_callback):
        super().__init__(parent)
        self.data = data
        self.log_callback = log_callback
        self.update_statistics_callback = update_statistics_callback
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        # Верхняя часть – настройки генерации
        top_layout = QHBoxLayout()
        # Промпт статьи
        prompt_box = QVBoxLayout()
        prompt_box.addWidget(QLabel("Промпт статьи:"))
        self.templateCombo = QComboBox()
        self.update_prompts()
        prompt_box.addWidget(self.templateCombo)
        top_layout.addLayout(prompt_box)
        # Промпт изображения
        image_prompt_box = QVBoxLayout()
        image_prompt_box.addWidget(QLabel("Промпт изображения:"))
        self.imagePromptCombo = QComboBox()
        self.update_image_prompts()
        image_prompt_box.addWidget(self.imagePromptCombo)
        top_layout.addLayout(image_prompt_box)
        # Чекбокс для генерации изображений
        self.imageCheck = QCheckBox("Генерация изображений")
        self.imageCheck.setChecked(True)
        top_layout.addWidget(self.imageCheck)
        # Кнопка "Сгенерировать"
        self.generateBtn = QPushButton("Сгенерировать статью")
        self.generateBtn.clicked.connect(self.generate_article)
        top_layout.addWidget(self.generateBtn)
        layout.addLayout(top_layout)
        # Предпросмотр статьи
        layout.addWidget(QLabel("Предпросмотр статьи (HTML):"))
        self.previewEdit = QTextEdit()
        self.previewEdit.setReadOnly(False)
        layout.addWidget(self.previewEdit)
        # Предпросмотр изображения
        self.imageLabel = QLabel("Предпросмотр изображения")
        self.imageLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.imageLabel)
        # Публикация
        pub_layout = QHBoxLayout()
        pub_layout.addWidget(QLabel("Категория (ID или имя):"))
        self.categoryCombo = QComboBox()
        self.update_categories()
        pub_layout.addWidget(self.categoryCombo)
        self.publishBtn = QPushButton("Опубликовать")
        self.publishBtn.clicked.connect(self.publish_article)
        pub_layout.addWidget(self.publishBtn)
        layout.addLayout(pub_layout)
        # Автопостинг
        auto_layout = QHBoxLayout()
        auto_layout.addWidget(QLabel("Интервал (мин):"))
        self.intervalSpin = QSpinBox()
        self.intervalSpin.setMinimum(1)
        self.intervalSpin.setValue(5)
        auto_layout.addWidget(self.intervalSpin)
        auto_layout.addWidget(QLabel("Кол-во статей:"))
        self.articleCountSpin = QSpinBox()
        self.articleCountSpin.setMinimum(1)
        self.articleCountSpin.setValue(5)
        auto_layout.addWidget(self.articleCountSpin)
        self.startAutoBtn = QPushButton("Старт (Авто)")
        self.startAutoBtn.clicked.connect(self.start_autopost)
        auto_layout.addWidget(self.startAutoBtn)
        self.pauseAutoBtn = QPushButton("Пауза (Авто)")
        self.pauseAutoBtn.clicked.connect(self.pause_autopost)
        auto_layout.addWidget(self.pauseAutoBtn)
        layout.addLayout(auto_layout)
        self.setLayout(layout)
        self.auto_post_running = False
        self.auto_articles_remaining = 0

    def update_prompts(self):
        self.templateCombo.clear()
        for prompt in self.data.get("prompts", []):
            self.templateCombo.addItem(prompt)

    def update_image_prompts(self):
        self.imagePromptCombo.clear()
        for prompt in self.data.get("image_prompts", []):
            self.imagePromptCombo.addItem(prompt)

    def update_categories(self):
        self.categoryCombo.clear()
        cats = self.data.get("categories", [])
        if not cats:
            cats = ["Uncategorized"]
            self.data["categories"] = cats
            save_data(self.data)
        for cat in cats:
            self.categoryCombo.addItem(cat)

    def generate_article(self):
        prompt = self.templateCombo.currentText()
        self.log_callback("Начало генерации статьи с промптом: " + prompt)
        api_keys = self.data.get("api_keys", [])
        if not api_keys:
            self.log_callback("Ошибка: не добавлен ни один API-ключ.")
            return
        api_key = api_keys[0]
        article_text = Scripts.generate_article_text(api_key, prompt, self.log_callback)
        if not article_text:
            return
        html_text = Scripts.format_text_to_html(article_text, self.log_callback)
        self.previewEdit.setHtml(html_text)
        self.log_callback("Статья сгенерирована.")
        if self.data.get("profiles"):
            profile_url = self.data["profiles"][0]["url"]
            self.increment_profile_counter(profile_url, "generated_count")
        if self.imageCheck.isChecked():
            img_prompt = self.imagePromptCombo.currentText()
            if not img_prompt:
                img_prompt = prompt
            self.log_callback("Генерация изображения с промптом: " + img_prompt)
            image = Scripts.generate_image(api_key, img_prompt, self.log_callback)
            if image:
                self.imageLabel.setPixmap(image.scaled(self.imageLabel.size()))
                self.log_callback("Изображение сгенерировано.")
            else:
                self.log_callback("Ошибка генерации изображения.")
        else:
            self.imageLabel.clear()
            self.log_callback("Генерация изображения отключена.")

    def extract_title(self, html):
        title = extract_title_from_html(html)
        if title == "Без заголовка":
            self.log_callback("Заголовок не найден, используется значение по умолчанию.")
        return title

    def add_interlinks(self, article_html):
        published = self.data.get("published_articles", [])
        if published:
            links_html = "<h3>Связанные статьи:</h3><ul>"
            for art in published:
                links_html += f'<li><a href="{art["link"]}">{art["title"]}</a></li>'
            links_html += "</ul>"
            return article_html + links_html
        else:
            return article_html

    def publish_article(self):
        article_html = self.previewEdit.toHtml()
        article_html = self.add_interlinks(article_html)
        title = self.extract_title(article_html)
        category = self.categoryCombo.currentText()
        profiles = self.data.get("profiles", [])
        if not profiles:
            self.log_callback("Ошибка: не добавлен ни один профиль сайта.")
            return
        profile = profiles[0]
        url = profile["url"]
        login = profile["login"]
        app_password = profile["app_password"]
        result, error = Scripts.publish_article(url, login, app_password, title, article_html, category, self.log_callback)
        if result:
            self.increment_profile_counter(url, "published_count")
            published = self.data.get("published_articles", [])
            pub_article = {"title": title, "link": result.get("link", url)}
            if self.auto_post_running:
                pub_article["auto"] = True
            published.append(pub_article)
            self.data["published_articles"] = published
            save_data(self.data)
            self.update_statistics_callback()
        else:
            if error is not None:
                self.log_callback("Ошибка публикации: " + error)
            else:
                self.log_callback("Ошибка публикации: неизвестная ошибка")

    def start_autopost(self):
        if self.auto_post_running:
            self.log_callback("Автопостинг уже запущен.")
            return
        interval = self.intervalSpin.value()
        count = self.articleCountSpin.value()
        self.auto_articles_remaining = count
        self.log_callback(f"Запуск автопостинга: {count} статей, интервал {interval} мин.")
        schedule.clear('autopost')
        schedule.every(interval).minutes.do(self.autopost_job_func).tag('autopost')
        self.auto_post_running = True

    def autopost_job_func(self):
        if self.auto_articles_remaining <= 0:
            self.log_callback("Заданное количество статей сгенерировано и опубликовано. Работа прекращена автоматически.")
            self.pause_autopost()
            return schedule.CancelJob
        self.log_callback(f"Автопостинг: публикация статьи. Осталось {self.auto_articles_remaining} статей.")
        self.generate_article()
        self.publish_article()
        self.auto_articles_remaining -= 1

    def pause_autopost(self):
        schedule.clear('autopost')
        self.auto_post_running = False
        self.log_callback("Автопостинг приостановлен.")

    def increment_profile_counter(self, profile_url, counter_key):
        for profile in self.data.get("profiles", []):
            if profile["url"] == profile_url:
                profile[counter_key] = profile.get(counter_key, 0) + 1
                break
        save_data(self.data)

class SettingsTab(QWidget):
    def __init__(self, parent, data, log_callback):
        super().__init__(parent)
        self.data = data
        self.log_callback = log_callback
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        profile_group = QGroupBox("Профили сайтов")
        profile_layout = QVBoxLayout()
        self.profileList = QListWidget()
        self.refresh_profile_list()
        profile_layout.addWidget(self.profileList)
        btn_layout = QHBoxLayout()
        self.addProfileBtn = QPushButton("Добавить")
        self.addProfileBtn.clicked.connect(self.handle_add_profile)
        btn_layout.addWidget(self.addProfileBtn)
        self.editProfileBtn = QPushButton("Редактировать")
        self.editProfileBtn.clicked.connect(self.handle_edit_profile)
        btn_layout.addWidget(self.editProfileBtn)
        self.deleteProfileBtn = QPushButton("Удалить")
        self.deleteProfileBtn.clicked.connect(self.handle_delete_profile)
        btn_layout.addWidget(self.deleteProfileBtn)
        profile_layout.addLayout(btn_layout)
        profile_group.setLayout(profile_layout)
        layout.addWidget(profile_group)
        api_group = QGroupBox("API-ключи OpenAI")
        api_layout = QVBoxLayout()
        self.apiList = QListWidget()
        self.refresh_api_list()
        api_layout.addWidget(self.apiList)
        btn_api_layout = QHBoxLayout()
        self.addApiBtn = QPushButton("Добавить")
        self.addApiBtn.clicked.connect(self.handle_add_api)
        btn_api_layout.addWidget(self.addApiBtn)
        self.editApiBtn = QPushButton("Редактировать")
        self.editApiBtn.clicked.connect(self.handle_edit_api)
        btn_api_layout.addWidget(self.editApiBtn)
        self.deleteApiBtn = QPushButton("Удалить")
        self.deleteApiBtn.clicked.connect(self.handle_delete_api)
        btn_api_layout.addWidget(self.deleteApiBtn)
        api_layout.addLayout(btn_api_layout)
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        cat_group = QGroupBox("Категории")
        cat_layout = QVBoxLayout()
        self.categoryList = QListWidget()
        self.refresh_category_list()
        cat_layout.addWidget(self.categoryList)
        btn_cat_layout = QHBoxLayout()
        self.addCategoryBtn = QPushButton("Добавить")
        self.addCategoryBtn.clicked.connect(self.handle_add_category)
        btn_cat_layout.addWidget(self.addCategoryBtn)
        self.editCategoryBtn = QPushButton("Редактировать")
        self.editCategoryBtn.clicked.connect(self.handle_edit_category)
        btn_cat_layout.addWidget(self.editCategoryBtn)
        self.deleteCategoryBtn = QPushButton("Удалить")
        self.deleteCategoryBtn.clicked.connect(self.handle_delete_category)
        btn_cat_layout.addWidget(self.deleteCategoryBtn)
        cat_layout.addLayout(btn_cat_layout)
        cat_group.setLayout(cat_layout)
        layout.addWidget(cat_group)
        prompt_group = QGroupBox("Промпты статей")
        prompt_layout = QVBoxLayout()
        self.promptList = QListWidget()
        self.refresh_prompt_list()
        prompt_layout.addWidget(self.promptList)
        btn_prompt_layout = QHBoxLayout()
        self.addPromptBtn = QPushButton("Добавить")
        self.addPromptBtn.clicked.connect(self.handle_add_prompt)
        btn_prompt_layout.addWidget(self.addPromptBtn)
        self.editPromptBtn = QPushButton("Редактировать")
        self.editPromptBtn.clicked.connect(self.handle_edit_prompt)
        btn_prompt_layout.addWidget(self.editPromptBtn)
        self.deletePromptBtn = QPushButton("Удалить")
        self.deletePromptBtn.clicked.connect(self.handle_delete_prompt)
        btn_prompt_layout.addWidget(self.deletePromptBtn)
        prompt_layout.addLayout(btn_prompt_layout)
        prompt_group.setLayout(prompt_layout)
        layout.addWidget(prompt_group)
        image_prompt_group = QGroupBox("Промпты изображений")
        image_prompt_layout = QVBoxLayout()
        self.imagePromptList = QListWidget()
        self.refresh_image_prompt_list()
        image_prompt_layout.addWidget(self.imagePromptList)
        btn_image_prompt_layout = QHBoxLayout()
        self.addImagePromptBtn = QPushButton("Добавить")
        self.addImagePromptBtn.clicked.connect(self.handle_add_image_prompt)
        btn_image_prompt_layout.addWidget(self.addImagePromptBtn)
        self.editImagePromptBtn = QPushButton("Редактировать")
        self.editImagePromptBtn.clicked.connect(self.handle_edit_image_prompt)
        btn_image_prompt_layout.addWidget(self.editImagePromptBtn)
        self.deleteImagePromptBtn = QPushButton("Удалить")
        self.deleteImagePromptBtn.clicked.connect(self.handle_delete_image_prompt)
        btn_image_prompt_layout.addWidget(self.deleteImagePromptBtn)
        image_prompt_layout.addLayout(btn_image_prompt_layout)
        image_prompt_group.setLayout(image_prompt_layout)
        layout.addWidget(image_prompt_group)
        self.setLayout(layout)

    def handle_add_profile(self):
        from ui.dialogs import AddProfileDialog
        dialog = AddProfileDialog(self)
        if dialog.exec_():
            new_profile = dialog.get_data()
            self.data["profiles"].append(new_profile)
            save_data(self.data)
            self.refresh_profile_list()
            self.log_callback("Профиль добавлен: " + new_profile["url"])

    def handle_add_api(self):
        from ui.dialogs import AddAPIKeyDialog
        dialog = AddAPIKeyDialog(self)
        if dialog.exec_():
            new_key = dialog.get_data()
            self.data["api_keys"].append(new_key)
            save_data(self.data)
            self.refresh_api_list()
            self.log_callback("API-ключ добавлен.")

    def handle_add_category(self):
        from ui.dialogs import AddCategoryDialog
        dialog = AddCategoryDialog(self)
        if dialog.exec_():
            new_cat = dialog.get_data()
            self.data["categories"].append(new_cat)
            save_data(self.data)
            self.refresh_category_list()
            self.log_callback("Категория добавлена: " + new_cat)

    def handle_add_prompt(self):
        from ui.dialogs import AddPromptDialog
        dialog = AddPromptDialog(self)
        if dialog.exec_():
            new_prompt = dialog.get_data()
            self.data["prompts"].append(new_prompt)
            save_data(self.data)
            self.refresh_prompt_list()
            self.log_callback("Промпт добавлен: " + new_prompt)

    def handle_add_image_prompt(self):
        from ui.dialogs import AddImagePromptDialog
        dialog = AddImagePromptDialog(self)
        if dialog.exec_():
            new_prompt = dialog.get_data()
            self.data["image_prompts"].append(new_prompt)
            save_data(self.data)
            self.refresh_image_prompt_list()
            self.log_callback("Промпт изображения добавлен: " + new_prompt)

    def refresh_profile_list(self):
        self.profileList.clear()
        for profile in self.data.get("profiles", []):
            self.profileList.addItem(profile["url"])

    def refresh_api_list(self):
        self.apiList.clear()
        for key in self.data.get("api_keys", []):
            self.apiList.addItem(key)

    def refresh_category_list(self):
        self.categoryList.clear()
        for cat in self.data.get("categories", []):
            self.categoryList.addItem(cat)

    def refresh_prompt_list(self):
        self.promptList.clear()
        for prompt in self.data.get("prompts", []):
            self.promptList.addItem(prompt)

    def refresh_image_prompt_list(self):
        self.imagePromptList.clear()
        for prompt in self.data.get("image_prompts", []):
            self.imagePromptList.addItem(prompt)

    def handle_edit_profile(self):
        current_item = self.profileList.currentRow()
        if current_item < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите профиль для редактирования.")
            return
        profile = self.data["profiles"][current_item]
        from ui.dialogs import EditProfileDialog
        dialog = EditProfileDialog(self, profile)
        if dialog.exec_():
            new_profile = dialog.get_data()
            self.data["profiles"][current_item] = new_profile
            save_data(self.data)
            self.refresh_profile_list()
            self.log_callback("Профиль обновлен: " + new_profile["url"])

    def handle_delete_profile(self):
        current_item = self.profileList.currentRow()
        if current_item < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите профиль для удаления.")
            return
        profile = self.data["profiles"].pop(current_item)
        save_data(self.data)
        self.refresh_profile_list()
        self.log_callback("Профиль удален: " + profile["url"])

    def handle_edit_api(self):
        current_item = self.apiList.currentRow()
        if current_item < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите API-ключ для редактирования.")
            return
        current_key = self.data["api_keys"][current_item]
        from ui.dialogs import EditAPIKeyDialog
        dialog = EditAPIKeyDialog(self, current_key)
        if dialog.exec_():
            new_key = dialog.get_data()
            self.data["api_keys"][current_item] = new_key
            save_data(self.data)
            self.refresh_api_list()
            self.log_callback("API-ключ обновлен.")

    def handle_delete_api(self):
        current_item = self.apiList.currentRow()
        if current_item < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите API-ключ для удаления.")
            return
        deleted_key = self.data["api_keys"].pop(current_item)
        save_data(self.data)
        self.refresh_api_list()
        self.log_callback("API-ключ удален.")

    def handle_edit_category(self):
        current_item = self.categoryList.currentRow()
        if current_item < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите категорию для редактирования.")
            return
        current_cat = self.data["categories"][current_item]
        from ui.dialogs import EditCategoryDialog
        dialog = EditCategoryDialog(self, current_cat)
        if dialog.exec_():
            new_cat = dialog.get_data()
            self.data["categories"][current_item] = new_cat
            save_data(self.data)
            self.refresh_category_list()
            self.log_callback("Категория обновлена: " + new_cat)

    def handle_delete_category(self):
        current_item = self.categoryList.currentRow()
        if current_item < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите категорию для удаления.")
            return
        deleted_cat = self.data["categories"].pop(current_item)
        save_data(self.data)
        self.refresh_category_list()
        self.log_callback("Категория удалена: " + deleted_cat)

    def handle_edit_prompt(self):
        current_item = self.promptList.currentRow()
        if current_item < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите промпт для редактирования.")
            return
        current_prompt = self.data["prompts"][current_item]
        from ui.dialogs import EditPromptDialog
        dialog = EditPromptDialog(self, current_prompt)
        if dialog.exec_():
            new_prompt = dialog.get_data()
            self.data["prompts"][current_item] = new_prompt
            save_data(self.data)
            self.refresh_prompt_list()
            self.log_callback("Промпт обновлен: " + new_prompt)

    def handle_delete_prompt(self):
        current_item = self.promptList.currentRow()
        if current_item < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите промпт для удаления.")
            return
        deleted_prompt = self.data["prompts"].pop(current_item)
        save_data(self.data)
        self.refresh_prompt_list()
        self.log_callback("Промпт удален: " + deleted_prompt)

    def handle_edit_image_prompt(self):
        current_item = self.imagePromptList.currentRow()
        if current_item < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите промпт изображения для редактирования.")
            return
        current_prompt = self.data["image_prompts"][current_item]
        from ui.dialogs import EditImagePromptDialog
        dialog = EditImagePromptDialog(self, current_prompt)
        if dialog.exec_():
            new_prompt = dialog.get_data()
            self.data["image_prompts"][current_item] = new_prompt
            save_data(self.data)
            self.refresh_image_prompt_list()
            self.log_callback("Промпт изображения обновлен: " + new_prompt)

    def handle_delete_image_prompt(self):
        current_item = self.imagePromptList.currentRow()
        if current_item < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите промпт изображения для удаления.")
            return
        deleted_prompt = self.data["image_prompts"].pop(current_item)
        save_data(self.data)
        self.refresh_image_prompt_list()
        self.log_callback("Промпт изображения удален: " + deleted_prompt)

class AnalyticsTab(QWidget):
    def __init__(self, parent, log_callback):
        super().__init__(parent)
        self.log_callback = log_callback
        self.init_ui()
        self.total_posts = 0
        self.auto_posts = 0

    def init_ui(self):
        layout = QVBoxLayout()
        self.statsLabel = QLabel("Статистика публикаций:")
        layout.addWidget(self.statsLabel)
        self.logTextEdit = QTextEdit()
        self.logTextEdit.setReadOnly(True)
        layout.addWidget(self.logTextEdit)
        self.clearLogBtn = QPushButton("Очистить лог")
        self.clearLogBtn.clicked.connect(self.clear_log)
        layout.addWidget(self.clearLogBtn)
        self.setLayout(layout)

    def add_log(self, message):
        self.logTextEdit.append(message)

    def update_stats(self, total, auto):
        self.total_posts = total
        self.auto_posts = auto
        self.statsLabel.setText(f"Общее число статей: {total}, Автопостинг: {auto}")

    def clear_log(self):
        self.logTextEdit.clear()
        self.add_log("Лог действий очищен.")

class PromptsTab(QWidget):
    def __init__(self, parent, data, log_callback):
        super().__init__(parent)
        self.data = data
        self.log_callback = log_callback
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Управление промптами статей:"))
        self.promptsEdit = QTextEdit()
        self.promptsEdit.setReadOnly(True)
        self.update_prompts_display()
        layout.addWidget(self.promptsEdit)
        self.setLayout(layout)

    def update_prompts_display(self):
        text = "\n".join(self.data.get("prompts", []))
        self.promptsEdit.setPlainText(text)
