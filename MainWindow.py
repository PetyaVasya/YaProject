from itertools import zip_longest
from threading import Thread, Event
from time import sleep
import sys
import xlsxwriter
import os
from random import randrange
from multiprocessing import Pool

from PyQt5 import QtGui
from PyQt5.QtGui import QFontMetrics, QFontDatabase, QFont
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLCDNumber, QLabel, QMainWindow, \
    QHBoxLayout, QVBoxLayout, QSizePolicy, QStatusBar, QTextEdit, QButtonGroup, QMessageBox, \
    QErrorMessage, QTabWidget, QAction, QToolBar, QTabBar, QScrollArea, QDesktopWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QUrl, Qt
from QParser import QParser, ParserEdit, ParsersList
from parser import Parser
from DataBase import DataBase
import re
import tqdm


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
        # self.setGeometry(500, 500, 500, 500)
        # self.showFullScreen()
        self.resize(QDesktopWidget().width(), QDesktopWidget().height())
        self.main = QTabWidget(self)
        self.setCentralWidget(self.main)
        self.actions_menu = QButtonGroup(self)

        self.ok_button = QPushButton("OK", self)
        # self.ok_button.setShortcut("Return")
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
        # self.main.setStyleSheet('''QTabBar::tab{background:gray;}
        # QTabBar{background:black;}
        #
        #
        # ''')
        self.main.setContentsMargins(0, 0, 0, 0)
        self.main.tabBar().tabButton(0, QTabBar.LeftSide).hide()
        self.main.currentChanged.connect(self.bar_opened)
        self.main.tabCloseRequested.connect(self.close_tab)
        self.statusBar().hide()
        # self.resize()
        # self.open_parsers_list()

    def resizeEvent(self, event):
        try:
            self.parsers_list.move_buttons()
        except AttributeError as e:
            pass
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
        self.parsers_list = ParsersList(q_parsers=dict(map(lambda x: (x[0], (x[1], x[2])),
                                                           self.db.execute(
                                                               "SELECT id, name, respath from parsers"))),
                                        parent=self)
        self.parsers_scroll.setWidget(self.parsers_list)
        for i in self.parse.keys():
            element = self.parsers_list.get_element(i)
            if element:
                element.run_stop()
        self.parsers_list.createNewButton.clicked.connect(self.open_parser_edit)
        self.parsers_list.createNewButton.setParent(self.parsers_scroll)
        for q_parser in map(lambda x: self.parsers_list.layout_v.itemAt(x).widget(),
                            range(self.parsers_list.layout_v.count() - 1)):
            # print(q_parser.name)
            q_parser.clicked[str, int].connect(self.open_parser_edit)
            # q_parser.element.clicked.emit("")
            # break
        # list(self.parsers_list.q_parsers.values())[2].element.clicked.emit("")
        # self.parsers_list.setAutoFillBackground(True)
        # a = self.main.palette()
        # a.setColor(self.main.backgroundRole(), Qt.black)
        # self.parsers_list.setPalette(a)
        self.parsers_list.delete_buttons.buttonClicked.connect(self.delete_parser)
        self.parsers_list.parse_buttons.buttonClicked.connect(self.run_stop_parser)

    def open_parsers_list(self):
        self.setWindowTitle("Parsers list")
        self.main.setCurrentIndex(0)

    def delete_parser(self, btn):
        reply = QMessageBox.question(self, "Delete parser", "Doо you want delete parser?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            id = self.parsers_list.delete_buttons.id(btn)
            dele = next((
                self.main.widget(i) for i in range(self.main.count()) if i and (self.main.widget(i).q_parser.id == id)), None)
            self.main.removeTab(self.main.indexOf(dele))
            self.parsers_list.delete_buttons.removeButton(btn)
            self.parsers_list.get_element(id).delete_self()
            if self.parse.get(id):
                self.parse[id].kill()
                self.parse[id].join()
                # del self.parse[id]
            del self.parsers_list.q_parsers[id]
            self.db.delete_parser(id)

    def run_stop_parser(self, btn):
        id = self.parsers_list.parse_buttons.id(btn)
        if self.parse.get(id):
            reply = QMessageBox.question(self, "Stop parsing", "You lost your progress",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.parse[id].kill()
                self.parse[id].join()
                # del self.parse[id]
            self.parsers_list.get_element(id).run_stop()
        else:
            parser = self.db.get_parser(id)
            if parser[4] == "File":
                if os.path.exists(parser[5]):
                    with open(parser[5], "r") as links:
                        links = links.read().split("\n")
                        fields = self.generate_attributes(parser[3])
                        self.parse[id] = StoppableThread(target=self.start_parsing,
                                                         args=(id, links, fields,))
                        self.parse[id].start()
                        # self.parse[self.parser_edit.get_id()] = StoppableThread(
                        #     target=self.start_parsing, args=(
                        #         self.parser_edit.get_id(), self.parser_edit.links,
                        #         self.parser_edit.get_attributes(),))
                        # self.parse[self.parser_edit.get_id()].start()
                        self.parsers_list.get_element(id).run_stop()
                else:
                    QErrorMessage(self).showMessage('File path wrong')
            # self.parse[id] = Thread
        QApplication.processEvents()

    def open_parser_edit(self, name, id=None):
        has = next((i for i in range(self.main.count()) if i and (self.main.widget(i).q_parser.id == id)), None)

        if has:
            self.main.setCurrentIndex(has)
        else:
            new = False
            if not id:

                self.setWindowTitle("Create new parser")
                new = True
                q_parser = QParser()

            else:

                response = self.db.get_parser(id)
                q_parser = QParser(*response[:3], self.generate_attributes(response[3]), *response[4:])
                self.setWindowTitle(q_parser.name)

            parser_edit = ParserEdit(q_parser, new, self)
            parser_edit.thing_changed.connect(self.dea_act_buttons)
            self.main.addTab(parser_edit, "test")
            self.main.setCurrentIndex(self.main.count() - 1)
            # self.setCentralWidget(parser_edit)

    def save_changes_dialog(self, parser_edit, cancel = False):
        if not any(parser_edit.changed.values()):
            return True
        res = QMessageBox.question(self, "Saving changes", "Save changes?", (QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel) if cancel else (QMessageBox.Yes | QMessageBox.No), QMessageBox.Yes)
        if res == QMessageBox.Yes:
            attrs = parser_edit.get_attributes()

            name = parser_edit.get_name()
            url = parser_edit.get_url()
            if parser_edit.new:
                id = self.db.add_parser(name, url, self.formated_attributes(attrs))
                parser_edit.q_parser.id = id
                parser_edit.new = False
            else:
                self.db.update_parser(parser_edit.q_parser.id, name,
                                      url, self.formated_attributes(attrs),
                                      "File" if parser_edit.fname else None,
                                      parser_edit.fname)
                id = parser_edit.q_parser.id
            parser_edit.q_parser.name = name
            parser_edit.q_parser.url = url
            parser_edit.q_parser.attributes = attrs
            if parser_edit.fname:
                parser_edit.q_parser.type = "File"
                parser_edit.q_parser.filepath = parser_edit.fname
            self.apply_button.setEnabled(False)
            return QMessageBox.Yes if cancel else True
        else:
            return (QMessageBox.Cancel if res == QMessageBox.Cancel else QMessageBox.No) if cancel else QMessageBox.No

    def finalEditAction(self, btn):
        parser_edit = self.main.currentWidget()
        if btn.text() == "Cancel":

            id = parser_edit.get_id()
            if self.test.get(id) and self.test[id].isAlive():
                self.test[id].kill()
                self.test[id].join()
            if self.parse.get(id):
                self.parse[id].kill()
                self.parse[id].join()

            self.main.removeTab(self.main.currentIndex())
            self.open_parsers_list()

        elif not any(parser_edit.errors.values()):

            if btn.text() == "OK":
                if parser_edit.q_parser and not parser_edit.new:

                    self.db.update_parser(parser_edit.q_parser.id, parser_edit.get_name(),
                                          parser_edit.get_url(), self.formated_attributes(
                            parser_edit.get_attributes()),
                                          "File" if parser_edit.fname else None,
                                          parser_edit.fname)
                    # parser_edit.q_parser.name = parser_edit.get_name()
                    id = parser_edit.get_id()

                else:

                    attrs = self.formated_attributes(parser_edit.get_attributes())
                    id = self.db.add_parser(parser_edit.get_name(), parser_edit.get_url(),
                                       attrs, "File" if parser_edit.fname else None,
                                       parser_edit.fname)
                    # self.parsers_list.q_parsers[self.db.get_lastrowid()] = QParser(
                    #     self.db.get_lastrowid(),
                    #     parser_edit.get_name(), parser_edit.get_url(), attrs)
                    new = self.parsers_list.add_element(parser_edit.get_name(), id)
                    new.clicked[str, int].connect(self.open_parser_edit)
                if self.test.get(id) and self.test[id].isAlive():
                    self.test[id].kill()
                    self.test[id].join()
                self.main.removeTab(self.main.currentIndex())
                self.open_parsers_list()

            elif btn.text() == "Apply":

                attrs = parser_edit.get_attributes()
                name = parser_edit.get_name()
                url = parser_edit.get_url()
                if parser_edit.new:
                    id = self.db.add_parser(name, url, attrs)
                    parser_edit.q_parser.id = id
                    parser_edit.new = False
                else:
                    self.db.update_parser(parser_edit.q_parser.id, name,
                                          url, self.formated_attributes(attrs),
                                          "File" if parser_edit.fname else None,
                                          parser_edit.fname)
                parser_edit.q_parser.name = name
                parser_edit.q_parser.url = url
                parser_edit.q_parser.attributes = attrs
                if parser_edit.fname:
                    parser_edit.q_parser.type = "File"
                    parser_edit.q_parser.filepath = parser_edit.fname
                # self.q_parsers.append(QParser(parser_edit.name_edit.toPlainText()))
                self.setWindowTitle(parser_edit.get_name())
                self.apply_button.setEnabled(False)

            elif btn.text() == "Test":
                if self.save_changes_dialog(parser_edit):

                    id = parser_edit.get_id()
                    # print(list(map(list, attrs.values())))
                    parser_edit.create_log_widget()
                    # self.test = Thread(target=self.start_test, args=(attrs,))
                    self.test[id] = StoppableThread(target=self.start_test, args=(self.main.currentIndex(), attrs,))
                    self.test[id].start()
                # self.test.join()

            elif btn.text() == "Run":
                if self.save_changes_dialog(parser_edit):
                    id = parser_edit.get_id()
                    if self.test.get(id):
                        self.test[id].kill()
                        self.test[id].join()
                    self.parse[parser_edit.get_id()] = StoppableThread(target=self.start_parsing,
                                                                            args=(
                                                                            parser_edit.get_id(),
                                                                            parser_edit.links,
                                                                            parser_edit.get_attributes(),))
                    self.parse[id].start()
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
        return "".join(
            map(lambda x: '"{}""{}""{}"'.format(x[0], x[1][0], x[1][1]),
                attrs.items()))

    def closeEvent(self, event):
        self.db.close()
        event.accept()

    def start_test(self, ind, attrs):
        parser_edit = self.main.widget(ind)
        id = parser_edit.get_id()
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
                QTest.qWait(1)
            # res = parser.parse_urls(parser_edit.links[:5], fields)
            # print(res)
            # # print("\n".join(map(lambda x: x[0] + "\n" + "\n".join(map(lambda z: "\t" + str(z[0]) + ": " + str(z[1]), zip(attrs.keys(), x[1]))), zip(parser_edit.links[:5], res))))
            # parser_edit.add_logs("\n".join(map(lambda x: x[0] + "\n" + "\n".join(map(lambda x: "\t" + str(x[0]) + ": " + str(x[1]), zip(attrs.keys(), x[1]))), zip(parser_edit.links[:5], res))))

        else:

            url = parser_edit.get_url()
            # html = parser.get_html(parser_edit.get_url())

            print(zip(attrs.keys(), parser.parse_url(url, fields)))
            parser_edit.add_logs("\n".join(map(lambda x: str(x[0]) + ": " + str(x[1]),
                                                    zip(attrs.keys(),
                                                        parser.parse_url(url, fields)))))
        del self.test[id]
    # except:
    #     pass

    def start_parsing(self, id, urls, fields):
        # parser = Parser()
        # print(list(zip(urls, [fields.items()] * len(urls))))
        print(len(urls))
        try:
            workbook = xlsxwriter.Workbook(self.res_path + '/' + str(id) + '.xlsx')
            worksheet = workbook.add_worksheet()
            worksheet.write(0, 0, "url")
            for p, key in enumerate(fields.keys()):
                worksheet.write(0, p + 1, key)
            parser = Parser()
            # with Pool(10) as p:
            #     row = 1
            #     for i in p.imap_unordered(parse, zip(urls, [tuple(fields.values())] * len(urls)), [parser] * len(urls)):
            #         print(i)
            #         self.parsers_list.get_element(id).set_links_count(len(urls))
            #         self.parsers_list.get_element(id).update_progress(row)
            #         for c, j in enumerate(i):
            #             worksheet.write(row, c, j)
            #         row += 1
            self.parsers_list.get_element(id).set_links_count(len(urls))
            for ind, i in enumerate(urls, 1):
                res = parser.parse_url(i, fields.values())
                print(res)
                self.parsers_list.get_element(id).update_progress(ind)
                for c, j in enumerate(res):
                    worksheet.write(ind, c, j)
                if ind % 10 == 0:
                    sleep(1)
            db = DataBase(self.db_path)
            db.update_parser(id, respath=self.res_path + "/" + str(id) + ".xlsx")
            db.close()
        finally:
            workbook.close()
            # if self.parsers_list:
            #     self.parsers_list.get_element(id).run_stop()
            self.parsers_list.get_element(id).hide_progress()
            del self.parse[id]
            print("end_parsing")


# def parse(args):
#     sleep(randrange(1, 5))
#     parser = args[-1]
#     return [args[0]] + parser.parse_url(*args[:-1])


class StoppableThread(Thread):

    def __init__(self, *args, **keywords):
        Thread.__init__(self, *args, **keywords)
        self.killed = False

    def start(self):
        self.__run_backup = self.run
        self.run = self.__run
        Thread.start(self)

    def __run(self):
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def globaltrace(self, frame, event, arg):
        if event == 'call':
            return self.localtrace
        else:
            return None

    def localtrace(self, frame, event, arg):
        if self.killed:
            if event == 'line':
                raise SystemExit()
        return self.localtrace

    def kill(self):
        self.killed = True
