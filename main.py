import sys
from PyQt5.QtWidgets import QApplication
from MainWindow import MainWindow
import sqlite3

def main():
    app = QApplication(sys.argv)
    ex = MainWindow("./parsers.db")
    ex.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()