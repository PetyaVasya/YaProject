from itertools import zip_longest
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLCDNumber, QLabel, QMainWindow, \
    QHBoxLayout, QVBoxLayout, QSizePolicy, QStatusBar, QTextEdit, QButtonGroup, QMessageBox, QErrorMessage
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from QParser import QParser, ParserEdit, ParsersList
from parser import Parser
from DataBase import DataBase
import re


class MainWindow(QMainWindow):

    def __init__(self, path):
        super(MainWindow, self).__init__()
        self.db = DataBase(path)
        self.initUI()

    def initUI(self):
        # self.setGeometry(500, 500, 500, 500)
        self.showFullScreen()
        self.actions_menu = QButtonGroup(self)

        self.ok_button = QPushButton("OK", self)
        # self.ok_button.setShortcut("Return")
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
            {row[0]: QParser(*row[0:-1], self.generate_attributes(row[-1])) for row in self.db.get_parsers()},
            self)
        self.setCentralWidget(self.parsers_list)
        self.parsers_list.createNewButton.clicked.connect(lambda: self.open_parser_edit(QParser()))
        for q_parser in self.parsers_list.q_parsers.values():
            # print(q_parser.name)
            q_parser.element.clicked.connect(lambda: self.open_parser_edit(q_parser))
            # q_parser.element.clicked.emit("")
            # break
        # list(self.parsers_list.q_parsers.values())[2].element.clicked.emit("")
        self.parsers_list.delete_buttons.buttonClicked.connect(self.delete_parser)

    def delete_parser(self, btn):
        reply = QMessageBox.question(self, "Delete parser", "Doо you want delete parser?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            id = self.parsers_list.delete_buttons.id(btn)
            self.parsers_list.delete_buttons.removeButton(btn)
            self.parsers_list.q_parsers[id].remove_element()
            del self.parsers_list.q_parsers[id]
            self.db.delete_parser(id)

    def open_parser_edit(self, q_parser):
        new = False

        if not q_parser.id:

            self.setWindowTitle("Create new parser")
            new = True

        else:

            self.setWindowTitle(q_parser.name)
        self.apply_button.setEnabled(False)

        self.statusBar().show()
        self.parser_edit = ParserEdit(q_parser, new, self)
        self.parser_edit.thing_changed.connect(self.dea_act_buttons)
        self.setCentralWidget(self.parser_edit)

    def finalEditAction(self, btn):
        if btn.text() == "Cancel":

            self.open_parsers_list()

        elif not any(self.parser_edit.errors.values()):

            if btn.text() == "OK":
                if self.parser_edit.q_parser and not self.parser_edit.new:

                    self.db.update_parser(self.parser_edit.q_parser.id, self.parser_edit.get_name(),
                                          self.parser_edit.get_url(), self.formated_attributes(self.parser_edit.get_attributes()))
                    # self.parser_edit.q_parser.name = self.parser_edit.get_name()

                else:

                    attrs = self.formated_attributes(self.parser_edit.get_attributes())
                    self.db.add_parser(self.parser_edit.get_name(), self.parser_edit.get_url(), attrs)
                    self.parsers_list.q_parsers[self.db.get_lastrowid()] = QParser(
                        self.db.get_lastrowid(),
                        self.parser_edit.get_name(), self.parser_edit.get_url(), attrs)
                    if self.parser_edit.new:
                        self.parser_edit.new = False
                self.open_parsers_list()

            elif btn.text() == "Apply":

                attrs = self.parser_edit.get_attributes()
                name = self.parser_edit.get_name()
                url = self.parser_edit.get_url()
                if self.parser_edit.new:
                    id = self.db.add_parser(name, url, attrs)
                    self.parser_edit.q_parser.id = id
                    self.parser_edit.new = False
                else:
                    self.db.update_parser(self.parser_edit.q_parser.id, name,
                                          url, self.formated_attributes(attrs))
                self.parser_edit.q_parser.name = name
                self.parser_edit.q_parser.url = url
                self.parser_edit.q_parser.attributes = attrs
                # self.q_parsers.append(QParser(self.parser_edit.name_edit.toPlainText()))
                self.setWindowTitle(self.parser_edit.get_name())
                self.apply_button.setEnabled(False)

            elif btn.text() == "Test":
                if not any(self.parser_edit.changed.values()) or (QMessageBox.question(self, "Test", "You need save changes for test",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes) == QMessageBox.Yes):
                    attrs = self.parser_edit.get_attributes()
                    if any(self.parser_edit.changed.values()):

                        name = self.parser_edit.get_name()
                        url = self.parser_edit.get_url()

                        if self.parser_edit.new:
                            id = self.db.add_parser(name, url, self.formated_attributes(attrs))
                            self.parser_edit.q_parser.id = id
                            self.parser_edit.new = False
                        else:
                            self.db.update_parser(self.parser_edit.q_parser.id, name,
                                                  url, self.formated_attributes(attrs))
                        self.parser_edit.q_parser.name = name
                        self.parser_edit.q_parser.url = url
                        self.parser_edit.q_parser.attributes = attrs
                        self.apply_button.setEnabled(False)
                    print(list(map(list, attrs.values())))
                    parser = Parser(self.parser_edit.get_url(), tuple(map(tuple, attrs.values())))
                    html = parser.get_html(self.parser_edit.get_url())

                    self.parser_edit.create_log_widget()
                    print(zip(attrs.keys(), parser.get_fields(html)))
                    self.parser_edit.add_logs("\n".join(map(lambda x: str(x[0]) + ": " + str(x[1]),
                                                            zip(attrs.keys(), parser.get_fields(html)))))
        else:
            print("error")
            QErrorMessage(self).showMessage('Fix errors(red fields)')
            if self.parser_edit.new:
                for i in self.parser_edit.errors.items():
                    if i[1]:
                        self.parser_edit.show_error(i[0])

    def generate_attributes(self, value):
        if value:
            print(dict(map(lambda x: (x[0], x[1:]), zip_longest(*(iter(re.findall('"(.*?)"', value)),) * 3))))
            return dict(map(lambda x: (x[0], x[1:]), zip_longest(*(iter(re.findall('"(.*?)"', value)),) * 3)))
        else:
            return {}

    def dea_act_buttons(self):
        if any(self.parser_edit.changed.values()):
            self.apply_button.setEnabled(True)
        else:
            self.apply_button.setEnabled(False)

    def formated_attributes(self, attrs):
        return "".join(
                        map(lambda x: '"{}""{}""{}"'.format(x[0], x[1][0], x[1][1]),
                            attrs.items()))
