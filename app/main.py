import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from styles.design import dark_style  # Файл стилей из папки styles

def main():
    try:
        app = QApplication(sys.argv)
        app.setStyleSheet(dark_style)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Ошибка при запуске приложения: {e}")

if __name__ == "__main__":
    main()