from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, QLineEdit, QTextEdit, \
    QPushButton




class ConcatenatePromptsDialog(QDialog):
    def __init__(self, prompts, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Склеить промпты")
        self.prompts = prompts
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Выберите промпты для склейки:"))
        self.listWidget = QListWidget()
        self.listWidget.setSelectionMode(QListWidget.MultiSelection)
        for prompt in self.prompts:
            item = QListWidgetItem(prompt)
            self.listWidget.addItem(item)
        layout.addWidget(self.listWidget)

        layout.addWidget(QLabel("Разделитель:"))
        self.delimiterEdit = QLineEdit("\n")
        layout.addWidget(self.delimiterEdit)

        self.resultEdit = QTextEdit()
        self.resultEdit.setPlaceholderText("Результат склейки...")
        layout.addWidget(self.resultEdit)

        self.concatButton = QPushButton("Склеить")
        self.concatButton.clicked.connect(self.concatenate_prompts)
        layout.addWidget(self.concatButton)

        self.setLayout(layout)

    def concatenate_prompts(self):
        selected_items = self.listWidget.selectedItems()
        delimiter = self.delimiterEdit.text()
        result = delimiter.join(item.text() for item in selected_items)
        self.resultEdit.setPlainText(result)

    def get_result(self):
        return self.resultEdit.toPlainText()
