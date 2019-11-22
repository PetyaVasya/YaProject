from itertools import zip_longest
from time import sleep
import xlsxwriter
import os

from PyQt5.QtGui import QPixmap
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QPushButton, QMainWindow, QSizePolicy, QButtonGroup, \
    QMessageBox, QErrorMessage, QTabWidget, QTabBar, QScrollArea, QDesktopWidget, QSplashScreen, \
    QWidget
from PyQt5.QtCore import Qt, QEvent, QMetaObject
from QParser import QParser, ParserEdit, ParsersList
from Tools import StoppableThread, CustomBar, CustomTabWidget
from parser import Parser
from DataBase import DataBase
import re


class MainWindow(QMainWindow):

    def __init__(self, path=None, res_path=None):
        super(MainWindow, self).__init__()
        self.db = DataBase(path)
        self.db_path = path
        self.res_path = res_path
        self.test = None
        self.parse = {}
        self.test = {}
        self.initUI()

    def closeEvent(self, event):
        print("close")
        for i in range(1, self.main.count()):
            reply = self.save_changes_dialog(self.main.widget(i), True)
            if reply == QMessageBox.Cancel:
                event.ignore()
                return
        event.accept()

    def initUI(self):
        start_screen = QPixmap("logo.png")
        splash_screen = QSplashScreen(start_screen, Qt.WindowStaysOnTopHint)
        splash_screen.show()
        self.main = CustomTabWidget(self)
        self.tb = CustomBar(self.main.width(), 30)
        self.main.setTabBar(self.tb)
        self.setWindowTitle("Parsers Creator")
        self.setCentralWidget(self.main)
        self.actions_menu = QButtonGroup(self)
        btn_css = "border-radius:5px;font-size:14px;background-color:#BB86FC;width:100px;height:30px"
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
            button.setStyleSheet(btn_css)
        self.init_parsers_list()
        self.setStyleSheet("QMainWindow{background-color: #121212;}")
        self.main.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main.setStyleSheet('''
                QTabWidget>QWidget>QWidget{
                background: #121212;
                }
                QTabWidget::tab-bar {
                    left: 0; 
                    background: rgb(35, 33, 41);
                }
                QTabBar::tab{
                    font-size:14px;
                    color:white;
                    height:30px;
                    border-bottom: 3px solid rgb(58, 53, 63);
                    border-left: 3px solid rgb(58, 53, 63);
                    text-align: center;
                }
                
                QTabBar::tab:first{
                    border-left:None;
                }
                QTabBar::tab::only-one{
                    border-left:None;
                }
                ''')
        # tb = CustomBar(self)
        # self.main.setTabBar(tb)
        #
        # self.main.tabBar().setExpanding(True)
        self.main.tabBar().setStyleSheet('''
                    background: rgb(35, 33, 41);
                    border-top-left-radius:20px;
                    border-top-right-radius:20px;
        ''')
        self.main.addTab(self.parsers_scroll, "List")
        self.main.setTabsClosable(True)
        self.main.setContentsMargins(0, 0, 0, 0)
        self.main.tabBar().tabButton(0, QTabBar.LeftSide).hide()
        self.main.currentChanged.connect(self.bar_opened)
        self.main.tabCloseRequested.connect(self.close_tab)
        self.statusBar().setStyleSheet('''
        background-color: rgb(30, 30, 30);
        ''')
        self.statusBar().hide()
        self.resize(QDesktopWidget().width(), QDesktopWidget().height())
        splash_screen.hide()

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
            if self.main.count() == ind:
                self.main.widget(ind - 1).setStyleSheet("QTabBar::tab{border-left:None;}")
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
        print("start")
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
            elif parser[4] == "Links":
                links = parser[5].split("\n")
                fields = self.generate_attributes(parser[3])
                self.parse[id_p] = StoppableThread(target=self.start_parsing,
                                                   args=(id_p, links, fields,))
                self.parse[id_p].start()
                self.parsers_list.get_element(id_p).run_stop()

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

                new = True
                q_parser = QParser()

            else:

                response = self.db.get_parser(id_p)
                q_parser = QParser(*response[:3], self.generate_attributes(response[3]),
                                   *response[4:])

            parser_edit = ParserEdit(q_parser, new, self)
            parser_edit.thing_changed.connect(self.dea_act_buttons)
            self.main.addTab(parser_edit, q_parser.name if q_parser.name else "New")
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
                    self.main.setTabText(self.main.currentIndex(), name)
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
                self.apply_button.setEnabled(False)

            elif btn.text() == "Test":
                if self.save_changes_dialog(parser_edit):
                    attrs = parser_edit.get_attributes()
                    id_p = parser_edit.get_id()
                    parser_edit.create_log_widget()
                    self.main.setTabText(self.main.currentIndex(), parser_edit.get_name())
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
                    self.parsers_list.get_element(id_p).run_stop()
                    self.main.removeTab(self.main.currentIndex())
                    self.open_parsers_list()

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
        element = self.parsers_list.get_element(id_p)
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
                worksheet.write(ind, 0, i)
                for c, j in enumerate(res, 1):
                    worksheet.write(ind, c, j)
                if ind % 10 == 0:
                    sleep(1)
            path = self.res_path + "/" + str(id_p) + ".xlsx"
            db = DataBase(self.db_path)
            db.update_parser(id_p, respath=path)
            db.close()
            element.set_result(path)
        finally:
            workbook.close()
            element.hide_progress()
            element.run_stop()
            del self.parse[id_p]
            print("end_parsing")
