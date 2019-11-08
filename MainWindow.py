import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLCDNumber, QLabel, QMainWindow, \
    QHBoxLayout, QVBoxLayout, QSizePolicy, QStatusBar, QTextEdit, QButtonGroup, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from QParser import Parser, ParserEdit, ParsersList
from DataBase import DataBase


class MainWindow(QMainWindow):

    def __init__(self, path):
        super(MainWindow, self).__init__()
        self.db = DataBase(path)
        self.initUI()

    def initUI(self):
        self.setGeometry(500, 500, 500, 500)

        self.actions_menu = QButtonGroup(self)

        self.ok_button = QPushButton("OK", self)
        self.ok_button.setShortcut("Return")
        self.test_button = QPushButton("Test", self)
        self.apply_button = QPushButton("Apply", self)
        self.cancel_button = QPushButton("Cancel", self)

        self.actions_menu.addButton(self.ok_button)
        self.actions_menu.addButton(self.test_button)
        self.actions_menu.addButton(self.apply_button)
        self.actions_menu.addButton(self.cancel_button)
        self.actions_menu.buttonClicked.connect(self.finalEditAction)

        for button in self.actions_menu.buttons():
            self.statusBar().addWidget(button)

        self.open_parsers_list()

    def open_parsers_list(self):
        self.statusBar().hide()
        self.setWindowTitle("Parsers list")
        self.parsers_list = ParsersList(
            {row[0]: Parser(*row[0:]) for row in self.db.get_parsers()},
            self)
        self.setCentralWidget(self.parsers_list)
        self.parsers_list.createNewButton.clicked.connect(self.open_parser_edit)
        for parser in self.parsers_list.parsers.values():
            parser.element.clicked.connect(lambda: self.open_parser_edit(parser))
        self.parsers_list.delete_buttons.buttonClicked.connect(self.delete_parser)

    def delete_parser(self, btn):
        reply = QMessageBox.question(self, "Delete parser", "Doо you want delete parser?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            id = self.parsers_list.delete_buttons.id(btn)
            self.parsers_list.delete_buttons.removeButton(btn)
            self.parsers_list.parsers[id].remove_element()
            del self.parsers_list.parsers[id]
            self.db.delete_parser(id)

    def open_parser_edit(self, parser=None):
        if not parser:

            self.setWindowTitle("Create new parser")
            self.apply_button.hide()

        else:

            self.setWindowTitle(parser.name)
            self.apply_button.show()

        self.statusBar().show()
        self.parser_edit = ParserEdit(parser, self)
        self.setCentralWidget(self.parser_edit)

    def finalEditAction(self, btn):
        if btn.text() == "OK":
            if self.parser_edit.parser:

                self.db.update_parser(self.parser_edit.parser.id, self.parser_edit.get_name())
                self.parser_edit.parser.name = self.parser_edit.get_name()

            else:

                self.db.add_parser(self.parser_edit.get_name(), self.parser_edit.get_url())
                self.parsers_list.parsers[self.db.get_lastrowid()] = Parser(self.db.get_lastrowid(),
                                                                            self.parser_edit.get_name(),self.parser_edit.get_url(), None)
            self.open_parsers_list()

        elif btn.text() == "Apply":

            self.db.update_parser(self.parser_edit.parser.id, self.parser_edit.get_name())
            self.parser_edit.parser.name = self.parser_edit.get_name()
            # self.parsers.append(Parser(self.parser_edit.name_edit.toPlainText()))
            self.setWindowTitle(self.parser_edit.get_name())

        else:

            self.open_parsers_list()
