from itertools import zip_longest
from time import sleep
import xlsxwriter
import os
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QPushButton, QMainWindow, QSizePolicy, QButtonGroup, \
    QMessageBox, QErrorMessage, QTabWidget, QTabBar, QScrollArea, QDesktopWidget
from PyQt5.QtCore import Qt
from QParser import QParser, ParserEdit, ParsersList
from Tools import StoppableThread
from parser import Parser
from DataBase import DataBase
import re


class MainWindow(QMainWindow):

    def __init__(self, path, res_path):
        super(MainWindow, self).__init__()
        self.db = DataBase(path)
        self.db_path = path
        self.res_path = res_path
        self.test = None
        self.parse = {}
        self.test = {}
        self.initUI()

    def initUI(self):
        self.resize(QDesktopWidget().width(), QDesktopWidget().height())
        self.main = QTabWidget(self)
        self.setCentralWidget(self.main)
        self.actions_menu = QButtonGroup(self)

        self.ok_button = QPushButton("OK", self)
        self.test_button = QPushButton("Test", self)
        self.run_button = QPushButton("Run", self)
        self.apply_button = QPushButton("Apply", self)
        self.cancel_button = QPushButton("Cancel", self)

        self.actions_menu.addButton(self.ok_button)
        self.actions_menu.addButton(self.run_button)
        self.actions_menu.addButton(self.test_button)
        self.actions_menu.addButton(self.apply_button)
        self.actions_menu.addButton(self.cancel_button)
        self.actions_menu.buttonClicked.connect(self.finalEditAction)

        for button in self.actions_menu.buttons():
            self.statusBar().addWidget(button)
        self.init_parsers_list()
        self.main.addTab(self.parsers_scroll, "list")
        self.main.setTabsClosable(True)
        self.main.setContentsMargins(0, 0, 0, 0)
        self.main.tabBar().tabButton(0, QTabBar.LeftSide).hide()
        self.main.currentChanged.connect(self.bar_opened)
        self.main.tabCloseRequested.connect(self.close_tab)
        self.statusBar().hide()

    def resizeEvent(self, event):
        try:
            self.parsers_list.move_buttons()
        except AttributeError as e:
            print(e)
        QMainWindow.resizeEvent(self, event)

    def close_tab(self, ind):
        parser_edit = self.main.widget(ind)
        self.main.setCurrentIndex(ind)
        res = self.save_changes_dialog(parser_edit, True)
        if res != QMessageBox.Cancel:
            self.main.removeTab(ind)
            self.open_parsers_list()

    def bar_opened(self, ind):
        if ind == 0:
            self.statusBar().hide()
        else:
            self.statusBar().show()
            self.apply_button.setEnabled(any(self.main.currentWidget().changed.values()))

    def init_parsers_list(self):
        self.parsers_scroll = QScrollArea(self)
        self.parsers_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.parsers_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.parsers_scroll.setWidgetResizable(True)
        res = self.db.execute("SELECT id, name, respath from parsers")
        self.parsers_list = ParsersList(q_parsers=dict(map(lambda x: (x[0], (x[1], x[2])), res)),
                                        parent=self)
        self.parsers_scroll.setWidget(self.parsers_list)
        for i in self.parse.keys():
            element = self.parsers_list.get_element(i)
            if element:
                element.run_stop()
        self.parsers_list.createNewButton.clicked.connect(self.open_parser_edit)
        self.parsers_list.createNewButton.setParent(self.parsers_scroll)
        for q_parser in map(lambda x: self.parsers_list.layout_v.itemAt(x).widget(),
                            range(self.parsers_list.layout_v.count())):
            # print(q_parser.name)
            q_parser.clicked[str, int].connect(self.open_parser_edit)
        self.parsers_list.delete_buttons.buttonClicked.connect(self.delete_parser)
        self.parsers_list.parse_buttons.buttonClicked.connect(self.run_stop_parser)

    def open_parsers_list(self):
        self.setWindowTitle("Parsers list")
        self.main.setCurrentIndex(0)

    def delete_parser(self, btn):
        reply = QMessageBox.question(self, "Delete parser", "Doо you want delete parser?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            id_p = self.parsers_list.delete_buttons.id(btn)
            dele = next((
                self.main.widget(i) for i in range(self.main.count()) if
                i and (self.main.widget(i).q_parser.id_p == id_p)), None)
            self.main.removeTab(self.main.indexOf(dele))
            self.parsers_list.delete_buttons.removeButton(btn)
            self.parsers_list.get_element(id_p).delete_self()
            if self.parse.get(id_p):
                self.parse[id_p].kill()
                self.parse[id_p].join()
            del self.parsers_list.q_parsers[id_p]
            self.db.delete_parser(id_p)

    def run_stop_parser(self, btn):
        """
        Запускает парсинг ленты с ParsersList. Добавляет progressbar и при успешном парсинге
        приклепляет файл с результатами.
        :param btn:
        :return:
        """
        id_p = self.parsers_list.parse_buttons.id(btn)
        if self.parse.get(id_p):
            reply = QMessageBox.question(self, "Stop parsing", "You lost your progress",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.parse[id_p].kill()
                self.parse[id_p].join()
            self.parsers_list.get_element(id_p).run_stop()
        else:
            parser = self.db.get_parser(id_p)
            if parser[4] == "File":
                if os.path.exists(parser[5]):
                    with open(parser[5], "r") as links:
                        links = links.read().split("\n")
                        fields = self.generate_attributes(parser[3])
                        self.parse[id_p] = StoppableThread(target=self.start_parsing,
                                                           args=(id_p, links, fields,))
                        self.parse[id_p].start()
                        self.parsers_list.get_element(id_p).run_stop()
                else:
                    QErrorMessage(self).showMessage('File path wrong')
        QApplication.processEvents()

    def open_parser_edit(self, name, id_p=None):
        has = next(
            (i for i in range(self.main.count()) if
             i and (self.main.widget(i).q_parser.id_p == id_p)),
            None)

        if has:
            self.main.setCurrentIndex(has)
        else:
            new = False
            if not id_p:

                self.setWindowTitle("Create new parser")
                new = True
                q_parser = QParser()

            else:

                response = self.db.get_parser(id_p)
                q_parser = QParser(*response[:3], self.generate_attributes(response[3]),
                                   *response[4:])
                self.setWindowTitle(q_parser.name)

            parser_edit = ParserEdit(q_parser, new, self)
            parser_edit.thing_changed.connect(self.dea_act_buttons)
            self.main.addTab(parser_edit, "test")
            self.main.setCurrentIndex(self.main.count() - 1)

    def save_changes_dialog(self, parser_edit, cancel=False):
        """
        Функция сохраняющая изменения в парсере(открытом окне ParserEdit)
        :param parser_edit:
        :param cancel:
        :return:
        """
        if not any(parser_edit.changed.values()):
            return True
        res = QMessageBox.question(self, "Saving changes", "Save changes?", (
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel) if cancel else (
                QMessageBox.Yes | QMessageBox.No), QMessageBox.Yes)
        if res == QMessageBox.Yes:
            attrs = parser_edit.get_attributes()

            name = parser_edit.get_name()
            url = parser_edit.get_url()
            if parser_edit.new:
                id_p = self.db.add_parser(name, url, self.formated_attributes(attrs),
                                          parser_edit.links_type,
                                          parser_edit.res)
                parser_edit.q_parser.id_p = id_p
                parser_edit.new = False
                new = self.parsers_list.add_element(name, id_p)
                new.clicked[str, int].connect(self.open_parser_edit)
            else:
                self.db.update_parser(parser_edit.q_parser.id_p, name,
                                      url, self.formated_attributes(attrs),
                                      parser_edit.links_type,
                                      parser_edit.res)
                id_p = parser_edit.q_parser.id_p
                self.parsers_list.get_element(id_p).set_name(name)
            parser_edit.q_parser.name = name
            parser_edit.q_parser.url = url
            parser_edit.q_parser.attributes = attrs
            parser_edit.q_parser.type_p = parser_edit.links_type
            parser_edit.q_parser.links = parser_edit.res
            for k in parser_edit.changed.keys():
                parser_edit.changed[k] = False
            self.apply_button.setEnabled(False)
            return QMessageBox.Yes if cancel else True
        else:
            if cancel:
                return QMessageBox.Cancel if res == QMessageBox.Cancel else QMessageBox.No
            else:
                return False

    def finalEditAction(self, btn):
        parser_edit = self.main.currentWidget()
        if btn.text() == "Cancel":

            id_p = parser_edit.get_id()
            if self.test.get(id_p) and self.test[id_p].isAlive():
                self.test[id_p].kill()
                self.test[id_p].join()
            if self.parse.get(id_p):
                self.parse[id_p].kill()
                self.parse[id_p].join()

            self.main.removeTab(self.main.currentIndex())
            self.open_parsers_list()

        elif not any(parser_edit.errors.values()):

            if btn.text() == "OK":
                if parser_edit.q_parser and not parser_edit.new:

                    self.db.update_parser(parser_edit.q_parser.id_p, parser_edit.get_name(),
                                          parser_edit.get_url(), self.formated_attributes(
                            parser_edit.get_attributes()),
                                          parser_edit.links_type,
                                          parser_edit.res)
                    id_p = parser_edit.get_id()
                    self.parsers_list.get_element(id_p).set_name(parser_edit.get_name())

                else:

                    attrs = self.formated_attributes(parser_edit.get_attributes())
                    id_p = self.db.add_parser(parser_edit.get_name(), parser_edit.get_url(),
                                              attrs, parser_edit.links_type,
                                              parser_edit.res)
                    new = self.parsers_list.add_element(parser_edit.get_name(), id_p)
                    new.clicked[str, int].connect(self.open_parser_edit)
                if self.test.get(id_p) and self.test[id_p].isAlive():
                    self.test[id_p].kill()
                    self.test[id_p].join()
                self.main.removeTab(self.main.currentIndex())
                self.open_parsers_list()

            elif btn.text() == "Apply":

                attrs = parser_edit.get_attributes()
                name = parser_edit.get_name()
                url = parser_edit.get_url()
                if parser_edit.new:
                    id_p = self.db.add_parser(name, url, attrs)
                    parser_edit.q_parser.id_p = id_p
                    parser_edit.new = False
                    new = self.parsers_list.add_element(name, id_p)
                    new.clicked[str, int].connect(self.open_parser_edit)
                else:
                    id_p = parser_edit.q_parser.id_p
                    self.db.update_parser(id_p, name,
                                          url, self.formated_attributes(attrs),
                                          parser_edit.links_type,
                                          parser_edit.res)
                    self.parsers_list.get_element(id_p).set_name(name)
                parser_edit.q_parser.name = name
                parser_edit.q_parser.url = url
                parser_edit.q_parser.attributes = attrs
                parser_edit.q_parser.type_p = parser_edit.links_type
                parser_edit.q_parser.links = parser_edit.res
                for k in parser_edit.changed.keys():
                    parser_edit.changed[k] = False
                self.setWindowTitle(parser_edit.get_name())
                self.apply_button.setEnabled(False)

            elif btn.text() == "Test":
                if self.save_changes_dialog(parser_edit):
                    attrs = parser_edit.get_attributes()
                    id_p = parser_edit.get_id()
                    parser_edit.create_log_widget()
                    self.test[id_p] = StoppableThread(target=self.start_test,
                                                      args=(self.main.currentIndex(), attrs,))
                    self.test[id_p].start()

            elif btn.text() == "Run":
                if self.save_changes_dialog(parser_edit):
                    id_p = parser_edit.get_id()
                    if self.test.get(id_p):
                        self.test[id_p].kill()
                        self.test[id_p].join()
                    new = StoppableThread(target=self.start_parsing, args=(
                        parser_edit.get_id(), parser_edit.links, parser_edit.get_attributes(),))
                    self.parse[parser_edit.get_id()] = new
                    self.parse[id_p].start()
                    self.open_parsers_list()
                    self.main.removeTab(self.main.currentIndex())

        else:
            print("error")
            QErrorMessage(self).showMessage('Fix errors(red fields)')
            if parser_edit.new:
                for i in parser_edit.errors.items():
                    if i[1]:
                        parser_edit.show_error(i[0])

    def generate_attributes(self, value):
        """
        Функция, превращающая сохранненые в DB атрибуты в dict
        :param value:
        :return:
        """
        if value:
            print(dict(map(lambda x: (x[0], x[1:]),
                           zip_longest(*(iter(re.findall('"(.*?)"', value)),) * 3))))
            return dict(map(lambda x: (x[0], x[1:]),
                            zip_longest(*(iter(re.findall('"(.*?)"', value)),) * 3)))
        else:
            return {}

    def dea_act_buttons(self):
        if any(self.main.currentWidget().changed.values()):
            self.apply_button.setEnabled(True)
        else:
            self.apply_button.setEnabled(False)

    def formated_attributes(self, attrs):
        """
        Функция, превращающая атрибуты в формат для сохранения в DB
        :param attrs:
        :return:
        """
        return "".join(
            map(lambda x: '"{}""{}""{}"'.format(x[0], x[1][0], x[1][1]),
                attrs.items()))

    def closeEvent(self, event):
        self.db.close()
        event.accept()

    def start_test(self, ind, attrs):
        parser_edit = self.main.widget(ind)
        id_p = parser_edit.get_id()
        # try:
        parser = Parser()
        fields = tuple(map(tuple, attrs.values()))
        print(fields)
        if parser_edit.links:

            for url in parser_edit.links[:5]:
                parser_edit.add_logs(url)
                parser_edit.add_logs(
                    "\n".join(map(lambda x: "\t" + str(x[0]) + ": " + str(x[1]),
                                  zip(attrs.keys(),
                                      parser.parse_url(url, fields)))))
                # Задержка, чтобы Log(QTextBrowser) успевал обновляться
                QTest.qWait(1)

        else:

            url = parser_edit.get_url()

            print(zip(attrs.keys(), parser.parse_url(url, fields)))
            parser_edit.add_logs("\n".join(map(lambda x: str(x[0]) + ": " + str(x[1]),
                                               zip(attrs.keys(),
                                                   parser.parse_url(url, fields)))))
        del self.test[id_p]

    def start_parsing(self, id_p, urls, fields):
        print(len(urls))
        try:
            workbook = xlsxwriter.Workbook(self.res_path + '/' + str(id_p) + '.xlsx')
            worksheet = workbook.add_worksheet()
            worksheet.write(0, 0, "url")
            for p, key in enumerate(fields.keys()):
                worksheet.write(0, p + 1, key)
            parser = Parser()
            self.parsers_list.get_element(id_p).set_links_count(len(urls))
            for ind, i in enumerate(urls, 1):
                res = parser.parse_url(i, fields.values())
                print(res)
                self.parsers_list.get_element(id_p).update_progress(ind)
                for c, j in enumerate(res):
                    worksheet.write(ind, c, j)
                if ind % 10 == 0:
                    sleep(1)
            db = DataBase(self.db_path)
            db.update_parser(id_p, respath=self.res_path + "/" + str(id_p) + ".xlsx")
            db.close()
        finally:
            workbook.close()
            self.parsers_list.get_element(id_p).hide_progress()
            del self.parse[id_p]
            print("end_parsing")
