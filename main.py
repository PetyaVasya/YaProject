import sys

from PyQt5.QtGui import QFontDatabase, QFont
from PyQt5.QtWidgets import QApplication
from MainWindow import MainWindow
import os


def main():
    setup()
    app = QApplication(sys.argv)
    font_db = QFontDatabase()
    font_id = font_db.addApplicationFont("Roboto-Regular.ttf")
    roboto = QFont("Roboto-Regular")
    app.setFont(roboto)
    ex = MainWindow("./parsers.db", "./results")
    ex.show()
    sys.exit(app.exec())


def setup():
    if not os.path.exists("./results"):
        os.mkdir('./results')
    if not os.path.exists("./sitemaps"):
        os.mkdir('./sitemaps')


if __name__ == "__main__":
    main()
