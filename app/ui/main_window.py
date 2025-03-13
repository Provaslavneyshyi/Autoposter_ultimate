import sys, time, schedule
from PyQt5.QtWidgets import QMainWindow, QSplitter, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QGuiApplication
from data.data_manager import load_data, save_data
from ui.tabs import ContentTab, SettingsTab, AnalyticsTab, PromptsTab
from workers.mass_project_tab import MassProjectTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AutoPost Ultimate")
        # Определяем размеры окна: 80% от доступной области
        available_geometry = QGuiApplication.primaryScreen().availableGeometry()
        width = int(available_geometry.width() * 0.8)
        height = int(available_geometry.height() * 0.8)
        self.resize(width, height)
        self.setMinimumSize(800, 600)
        self.move((available_geometry.width() - width) // 2, (available_geometry.height() - height) // 2)

        self.data = load_data()

        # Создаем QSplitter для левой панели (sidebar) и вкладок
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Horizontal)

        # Левая панель (навигация)
        self.leftPanel = QWidget()
        left_layout = QVBoxLayout(self.leftPanel)
        label_sidebar = QLabel("Панель навигации")
        left_layout.addWidget(label_sidebar)
        btn_refresh = QPushButton("Обновить")
        btn_refresh.clicked.connect(self.some_left_panel_action)
        left_layout.addWidget(btn_refresh)
        left_layout.addStretch(1)

        # Создаем вкладки
        self.tabs = QTabWidget()
        self.analytics_tab = AnalyticsTab(self, self.log)
        self.content_tab = ContentTab(self, self.data, self.log, self.update_statistics)
        self.settings_tab = SettingsTab(self, self.data, self.log)
        self.prompts_tab = PromptsTab(self, self.data, self.log)
        self.mass_project_tab = MassProjectTab(self.data, self.log)  # Остается без изменений

        self.tabs.addTab(self.mass_project_tab, "Автопостинг")
        self.tabs.addTab(self.settings_tab, "Настройки")
        self.tabs.addTab(self.analytics_tab, "Аналитика")
        self.tabs.addTab(self.prompts_tab, "Промпты статей")


        splitter.addWidget(self.leftPanel)
        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        # Таймер для scheduled задач
        self.timer = QTimer()
        self.timer.timeout.connect(self.run_scheduled_jobs)
        self.timer.start(1000)

    def some_left_panel_action(self):
        self.log("Нажата кнопка обновления в sidebar.")

    def log(self, message):
        timestamp = time.strftime("[%H:%M:%S]")
        log_message = f"{timestamp} {message}"
        self.analytics_tab.add_log(log_message)

    def update_statistics(self):
        published = self.data.get("published_articles", [])
        total = len(published)
        auto_count = sum(1 for art in published if art.get("auto", False))
        self.analytics_tab.update_stats(total, auto_count)
        self.log("Статистика обновлена: Всего статей - " + str(total) + ", автопубликаций - " + str(auto_count))

    def run_scheduled_jobs(self):
        schedule.run_pending()