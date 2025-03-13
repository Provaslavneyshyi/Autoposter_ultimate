from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QMessageBox

class AddProfileDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить профиль сайта")
        self.layout = QFormLayout(self)
        self.urlEdit = QLineEdit()
        self.loginEdit = QLineEdit()
        self.appPasswordEdit = QLineEdit()
        self.appPasswordEdit.setEchoMode(QLineEdit.Password)
        self.layout.addRow("URL сайта:", self.urlEdit)
        self.layout.addRow("Логин:", self.loginEdit)
        self.layout.addRow("Application Password:", self.appPasswordEdit)
        self.saveButton = QPushButton("Сохранить")
        self.saveButton.clicked.connect(self.accept)
        self.layout.addRow(self.saveButton)

    def get_data(self):
        return {"url": self.urlEdit.text(), "login": self.loginEdit.text(), "app_password": self.appPasswordEdit.text()}

class EditProfileDialog(QDialog):
    def __init__(self, parent=None, profile=None):
        super().__init__(parent)
        self.setWindowTitle("Редактировать профиль сайта")
        self.layout = QFormLayout(self)
        self.urlEdit = QLineEdit()
        self.loginEdit = QLineEdit()
        self.appPasswordEdit = QLineEdit()
        self.appPasswordEdit.setEchoMode(QLineEdit.Password)
        if profile:
            self.urlEdit.setText(profile.get("url", ""))
            self.loginEdit.setText(profile.get("login", ""))
            self.appPasswordEdit.setText(profile.get("app_password", ""))
        self.layout.addRow("URL сайта:", self.urlEdit)
        self.layout.addRow("Логин:", self.loginEdit)
        self.layout.addRow("Application Password:", self.appPasswordEdit)
        self.saveButton = QPushButton("Сохранить")
        self.saveButton.clicked.connect(self.accept)
        self.layout.addRow(self.saveButton)

    def get_data(self):
        return {"url": self.urlEdit.text(), "login": self.loginEdit.text(), "app_password": self.appPasswordEdit.text()}

class AddAPIKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить API-ключ OpenAI")
        self.layout = QFormLayout(self)
        self.apiKeyEdit = QLineEdit()
        self.layout.addRow("API-ключ:", self.apiKeyEdit)
        self.saveButton = QPushButton("Сохранить")
        self.saveButton.clicked.connect(self.accept)
        self.layout.addRow(self.saveButton)

    def get_data(self):
        return self.apiKeyEdit.text()

class EditAPIKeyDialog(QDialog):
    def __init__(self, parent=None, api_key=""):
        super().__init__(parent)
        self.setWindowTitle("Редактировать API-ключ OpenAI")
        self.layout = QFormLayout(self)
        self.apiKeyEdit = QLineEdit()
        self.apiKeyEdit.setText(api_key)
        self.layout.addRow("API-ключ:", self.apiKeyEdit)
        self.saveButton = QPushButton("Сохранить")
        self.saveButton.clicked.connect(self.accept)
        self.layout.addRow(self.saveButton)

    def get_data(self):
        return self.apiKeyEdit.text()

class AddCategoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить категорию")
        self.layout = QFormLayout(self)
        self.categoryEdit = QLineEdit()
        self.layout.addRow("Название категории (ID или имя):", self.categoryEdit)
        self.saveButton = QPushButton("Сохранить")
        self.saveButton.clicked.connect(self.accept)
        self.layout.addRow(self.saveButton)

    def get_data(self):
        return self.categoryEdit.text()

class EditCategoryDialog(QDialog):
    def __init__(self, parent=None, category=""):
        super().__init__(parent)
        self.setWindowTitle("Редактировать категорию")
        self.layout = QFormLayout(self)
        self.categoryEdit = QLineEdit()
        self.categoryEdit.setText(category)
        self.layout.addRow("Название категории (ID или имя):", self.categoryEdit)
        self.saveButton = QPushButton("Сохранить")
        self.saveButton.clicked.connect(self.accept)
        self.layout.addRow(self.saveButton)

    def get_data(self):
        return self.categoryEdit.text()

class AddPromptDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить промпт статьи")
        self.layout = QFormLayout(self)
        self.promptEdit = QLineEdit()
        self.layout.addRow("Промпт статьи:", self.promptEdit)
        self.saveButton = QPushButton("Сохранить")
        self.saveButton.clicked.connect(self.accept)
        self.layout.addRow(self.saveButton)

    def get_data(self):
        return self.promptEdit.text()

class EditPromptDialog(QDialog):
    def __init__(self, parent=None, prompt=""):
        super().__init__(parent)
        self.setWindowTitle("Редактировать промпт статьи")
        self.layout = QFormLayout(self)
        self.promptEdit = QLineEdit()
        self.promptEdit.setText(prompt)
        self.layout.addRow("Промпт статьи:", self.promptEdit)
        self.saveButton = QPushButton("Сохранить")
        self.saveButton.clicked.connect(self.accept)
        self.layout.addRow(self.saveButton)

    def get_data(self):
        return self.promptEdit.text()

class AddImagePromptDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить промпт изображения")
        self.layout = QFormLayout(self)
        self.promptEdit = QLineEdit()
        self.layout.addRow("Промпт изображения:", self.promptEdit)
        self.saveButton = QPushButton("Сохранить")
        self.saveButton.clicked.connect(self.accept)
        self.layout.addRow(self.saveButton)

    def get_data(self):
        return self.promptEdit.text()

class EditImagePromptDialog(QDialog):
    def __init__(self, parent=None, prompt=""):
        super().__init__(parent)
        self.setWindowTitle("Редактировать промпт изображения")
        self.layout = QFormLayout(self)
        self.promptEdit = QLineEdit()
        self.promptEdit.setText(prompt)
        self.layout.addRow("Промпт изображения:", self.promptEdit)
        self.saveButton = QPushButton("Сохранить")
        self.saveButton.clicked.connect(self.accept)
        self.layout.addRow(self.saveButton)

    def get_data(self):
        return self.promptEdit.text()