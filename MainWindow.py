from itertools import zip_longest
from threading import Thread, Event
from time import sleep
import sys
import xlsxwriter
import os
from random import randrange
from multiprocessing import Pool
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLCDNumber, QLabel, QMainWindow, \
    QHBoxLayout, QVBoxLayout, QSizePolicy, QStatusBar, QTextEdit, QButtonGroup, QMessageBox, \
    QErrorMessage, QStackedWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from QParser import QParser, ParserEdit, ParsersList
from parser import Parser
from DataBase import DataBase
import re
import tqdm


class MainWindow(QMainWindow):

    def __init__(self, path):
        super(MainWindow, self).__init__()
        self.db = DataBase(path)
        self.db_path = path
        self.test = None
        self.parse = {}
        self.initUI()

    def initUI(self):
        # self.setGeometry(500, 500, 500, 500)
        self.showFullScreen()
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

        self.open_parsers_list()

    def open_parsers_list(self):
        self.statusBar().hide()
        self.setWindowTitle("Parsers list")
        self.parsers_list = ParsersList(q_parsers=dict(map(lambda x: (x[0], (x[1], x[2])),
                                                           self.db.execute(
                                                               "SELECT id, name, respath from parsers"))),
                                        parent=self)
        for i in self.parse.keys():
            element = self.parsers_list.get_element(i)
            if element:
                element.run_stop()
        self.setCentralWidget(self.parsers_list)
        self.parsers_list.createNewButton.clicked.connect(self.open_parser_edit)
        for q_parser in map(lambda x: self.parsers_list.layout_v.itemAt(x).widget(),
                            range(self.parsers_list.layout_v.count() - 1)):
            # print(q_parser.name)
            q_parser.clicked[str, int].connect(self.open_parser_edit)
            # q_parser.element.clicked.emit("")
            # break
        # list(self.parsers_list.q_parsers.values())[2].element.clicked.emit("")
        self.parsers_list.delete_buttons.buttonClicked.connect(self.delete_parser)
        self.parsers_list.parse_buttons.buttonClicked.connect(self.run_stop_parser)

    def delete_parser(self, btn):
        reply = QMessageBox.question(self, "Delete parser", "Doо you want delete parser?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            id = self.parsers_list.delete_buttons.id(btn)
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

        new = False
        self.statusBar().show()
        self.apply_button.setEnabled(False)

        if not id:

            self.setWindowTitle("Create new parser")
            new = True
            q_parser = QParser()

        else:

            response = self.db.get_parser(id)
            q_parser = QParser(*response[:3], self.generate_attributes(response[3]), *response[4:])
            self.setWindowTitle(q_parser.name)

        self.parser_edit = ParserEdit(q_parser, new, self)
        self.parser_edit.thing_changed.connect(self.dea_act_buttons)
        self.setCentralWidget(self.parser_edit)

    def finalEditAction(self, btn):
        if btn.text() == "Cancel":

            if self.test and self.test.isAlive():
                self.test.kill()
                self.test.join()
            id = self.parser_edit.get_id()
            if self.parse.get(id):
                self.parse[id].kill()
                self.parse[id].join()

            self.open_parsers_list()

        elif not any(self.parser_edit.errors.values()):

            if btn.text() == "OK":
                if self.parser_edit.q_parser and not self.parser_edit.new:

                    self.db.update_parser(self.parser_edit.q_parser.id, self.parser_edit.get_name(),
                                          self.parser_edit.get_url(), self.formated_attributes(
                            self.parser_edit.get_attributes()),
                                          "File" if self.parser_edit.fname else None,
                                          self.parser_edit.fname)
                    # self.parser_edit.q_parser.name = self.parser_edit.get_name()

                else:

                    attrs = self.formated_attributes(self.parser_edit.get_attributes())
                    self.db.add_parser(self.parser_edit.get_name(), self.parser_edit.get_url(),
                                       attrs, "File" if self.parser_edit.fname else None,
                                       self.parser_edit.fname)
                    # self.parsers_list.q_parsers[self.db.get_lastrowid()] = QParser(
                    #     self.db.get_lastrowid(),
                    #     self.parser_edit.get_name(), self.parser_edit.get_url(), attrs)
                    if self.parser_edit.new:
                        self.parser_edit.new = False
                if self.test and self.test.isAlive():
                    self.test.kill()
                    self.test.join()
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
                                          url, self.formated_attributes(attrs),
                                          "File" if self.parser_edit.fname else None,
                                          self.parser_edit.fname)
                self.parser_edit.q_parser.name = name
                self.parser_edit.q_parser.url = url
                self.parser_edit.q_parser.attributes = attrs
                if self.parser_edit.fname:
                    self.parser_edit.q_parser.type = "File"
                    self.parser_edit.q_parser.filepath = self.parser_edit.fname
                # self.q_parsers.append(QParser(self.parser_edit.name_edit.toPlainText()))
                self.setWindowTitle(self.parser_edit.get_name())
                self.apply_button.setEnabled(False)

            elif btn.text() == "Test":
                if not any(self.parser_edit.changed.values()) or (
                        QMessageBox.question(self, "Test", "You need save changes for test",
                                             QMessageBox.Yes | QMessageBox.No,
                                             QMessageBox.Yes) == QMessageBox.Yes):
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
                                                  url, self.formated_attributes(attrs),
                                                  "File" if self.parser_edit.fname else None,
                                                  self.parser_edit.fname)
                        self.parser_edit.q_parser.name = name
                        self.parser_edit.q_parser.url = url
                        self.parser_edit.q_parser.attributes = attrs
                        if self.parser_edit.fname:
                            self.parser_edit.q_parser.type = "File"
                            self.parser_edit.q_parser.filepath = self.parser_edit.fname
                        self.apply_button.setEnabled(False)
                    # print(list(map(list, attrs.values())))
                    self.parser_edit.create_log_widget()
                    # self.test = Thread(target=self.start_test, args=(attrs,))
                    self.test = StoppableThread(target=self.start_test, args=(attrs,))
                    self.test.start()
                # self.test.join()

            elif btn.text() == "Run":

                if self.test and self.test.isAlive():
                    self.test.kill()
                    self.test.join()
                self.parse[self.parser_edit.get_id()] = StoppableThread(target=self.start_parsing,
                                                                        args=(
                                                                        self.parser_edit.get_id(),
                                                                        self.parser_edit.links,
                                                                        self.parser_edit.get_attributes(),))
                self.parse[self.parser_edit.get_id()].start()

        else:
            print("error")
            QErrorMessage(self).showMessage('Fix errors(red fields)')
            if self.parser_edit.new:
                for i in self.parser_edit.errors.items():
                    if i[1]:
                        self.parser_edit.show_error(i[0])

    def generate_attributes(self, value):
        if value:
            print(dict(map(lambda x: (x[0], x[1:]),
                           zip_longest(*(iter(re.findall('"(.*?)"', value)),) * 3))))
            return dict(map(lambda x: (x[0], x[1:]),
                            zip_longest(*(iter(re.findall('"(.*?)"', value)),) * 3)))
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

    def closeEvent(self, event):
        self.db.close()
        event.accept()

    def start_test(self, attrs):
        # try:
        parser = Parser()
        fields = tuple(map(tuple, attrs.values()))
        print(fields)
        if self.parser_edit.links:

            for url in self.parser_edit.links[:5]:
                self.parser_edit.add_logs(url)
                self.parser_edit.add_logs(
                    "\n".join(map(lambda x: "\t" + str(x[0]) + ": " + str(x[1]),
                                  zip(attrs.keys(),
                                      parser.parse_url(url, fields)))))
                QTest.qWait(1)
            # res = parser.parse_urls(self.parser_edit.links[:5], fields)
            # print(res)
            # # print("\n".join(map(lambda x: x[0] + "\n" + "\n".join(map(lambda z: "\t" + str(z[0]) + ": " + str(z[1]), zip(attrs.keys(), x[1]))), zip(self.parser_edit.links[:5], res))))
            # self.parser_edit.add_logs("\n".join(map(lambda x: x[0] + "\n" + "\n".join(map(lambda x: "\t" + str(x[0]) + ": " + str(x[1]), zip(attrs.keys(), x[1]))), zip(self.parser_edit.links[:5], res))))

        else:

            url = self.parser_edit.get_url()
            # html = parser.get_html(self.parser_edit.get_url())

            print(zip(attrs.keys(), parser.parse_url(url, fields)))
            self.parser_edit.add_logs("\n".join(map(lambda x: str(x[0]) + ": " + str(x[1]),
                                                    zip(attrs.keys(),
                                                        parser.parse_url(url, fields)))))

    # except:
    #     pass

    def start_parsing(self, id, urls, fields):
        # parser = Parser()
        # print(list(zip(urls, [fields.items()] * len(urls))))
        print(len(urls))
        try:
            workbook = xlsxwriter.Workbook('./results/test.xlsx')
            worksheet = workbook.add_worksheet()
            worksheet.write(0, 0, "url")
            for p, key in enumerate(fields.keys()):
                worksheet.write(0, p + 1, key)
            with Pool(10) as p:
                row = 1
                for i in p.imap_unordered(parse, zip(urls, [tuple(fields.values())] * len(urls))):
                    print(i)
                    try:
                        self.parsers_list.get_element(id).set_links_count(len(urls))
                        self.parsers_list.get_element(id).update_progress(row)
                    except:
                        pass
                    for c, j in enumerate(i):
                        worksheet.write(row, c, j)
                    row += 1
            db = DataBase(self.db_path)
            db.update_parser(id, respath="./results/test.xlsx")
            db.close()
        finally:
            workbook.close()
            # if self.parsers_list:
            #     self.parsers_list.get_element(id).run_stop()
            self.parsers_list.get_element(id).hide_progress()
            del self.parse[id]
            print("end_parsing")


def parse(args):
    sleep(randrange(1, 3))
    parser = Parser()
    return [args[0]] + parser.parse_url(*args)


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
