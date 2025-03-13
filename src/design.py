# design.py

dark_style = """
QWidget {
    background-color: #2e2e2e;
    color: #ffffff;
    font-size: 14px;
}
QLineEdit, QTextEdit, QComboBox, QListWidget {
    background-color: #3c3c3c;
    border: 1px solid #555;
    color: #ffffff;
}
QPushButton {
    background-color: #444;
    border: 1px solid #666;
    padding: 6px 12px;
    color: #ffffff;
}
QPushButton:hover {
    background-color: #555;
}
QGroupBox {
    border: 1px solid #555;
    margin-top: 10px;
}
QGroupBox:title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 3px;
}
QSplitter::handle {
    background-color: #444;
}

QTabBar::tab { 
    color: #ffffff; /* обычное состояние */
    padding: 3px;
}
QTabBar::tab:selected { 
    color: #000000; /* выбранная вкладка */
    background: #ffffff
}
QTabBar::tab:hover { 
    color: #000000; /* при наведении */
    background: #B5B8B1;
}

"""
