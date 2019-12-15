import glob
from itertools import zip_longest
from time import sleep
import xlsxwriter
import os

from PyQt5.QtGui import QPixmap
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QPushButton, QMainWindow, QSizePolicy, QButtonGroup, \
    QMessageBox, QErrorMessage, QTabWidget, QTabBar, QScrollArea, QDesktopWidget, QSplashScreen, \
    QWidget, QVBoxLayout, QTextEdit
from PyQt5.QtCore import Qt, QEvent, QMetaObject
from QParser import QParser, ParserEdit, ParsersList
from Tools import StoppableThread, CustomBar, CustomTabWidget, get_sitemaps_paths, \
    fetch_sitemaps_links, get_ranges_url
from Parser import Parser
from DataBase import DataBase
import re
import platform


class MainWindow(QMainWindow):

    def __init__(self, path=None, res_path=None, img_path=None):
        super(MainWindow, self).__init__()
        self.db = DataBase(path)
        self.db_path = path
        self.check_db()
        self.res_path = res_path
        self.img_path = img_path
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
        if os.path.exists("logo.png"):
            start_screen = QPixmap("logo.png")
            splash_screen = QSplashScreen(start_screen, Qt.WindowStaysOnTopHint)
            splash_screen.show()
        self.setMaximumSize(QDesktopWidget().width(), QDesktopWidget().height())
        self.setMinimumSize(800, 400)
        self.main = CustomTabWidget(self)
        self.tb = CustomBar(self.main.width(), 30)
        self.main.setTabBar(self.tb)
        self.setWindowTitle("Parsers Creator")
        self.setCentralWidget(self.main)
        self.actions_menu = QButtonGroup(self)
        btn_css = '''border-radius:5px;
                    font-size:14px;
                    background-color:#BB86FC;
                    width:100px;
                    height:30px;
                    border:0px;'''
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
        self.init_proxies_page()
        self.setStyleSheet('''QMainWindow{background-color: #121212;border:0px;}
                        QDialog{
                            background-color: #121212;
                        }
                        QDialog>QLabel{
                            color: white;
                            font-size:14px;
                        }
                        CustomTabWidget{background:#121212;border:0px;}
                        CustomTabWidget>QWidget{background:#121212;border:0px;}
                        CustomTabWidget>QWidget>QWidget{background:#121212;border:0px;}
                        QScrollBar:vertical, QScrollBar::handle:vertical,QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical, QScrollBar::left-arrow:vertical,
            QScrollBar::right-arrow:vertical{
                border: 1px solid white;
                background: #121212;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical{
                background: #303030;
                border:1px solid white;
            }
                            ''')
        self.main.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main.setStyleSheet('''
                QTabWidget{
                border:0px;
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
        self.main.addTab(self.proxies_page, "Proxies")
        self.main.setTabsClosable(True)
        self.main.setContentsMargins(0, 0, 0, 0)
        if platform.system() == 'Windows':
            self.main.tabBar().tabButton(0, QTabBar.RightSide).hide()
            self.main.tabBar().tabButton(1, QTabBar.RightSide).hide()
        else:
            self.main.tabBar().tabButton(0, QTabBar.LeftSide).hide()
            self.main.tabBar().tabButton(1, QTabBar.LeftSide).hide()
        self.main.currentChanged.connect(self.bar_opened)
        self.main.tabCloseRequested.connect(self.close_tab)
        self.statusBar().setStyleSheet('''
            QStatusBar{
                background-color: rgb(30, 30, 30);
                border:0px;
            }
            QStatusBar>QWidget, QStatusBar::item{
                border:0px;
            }
        ''')
        self.statusBar().hide()
        self.resize(QDesktopWidget().width(), QDesktopWidget().availableGeometry().height())
        if os.path.exists("logo.png"):
            splash_screen.hide()

    def resizeEvent(self, event):
        QMainWindow.resizeEvent(self, event)
        event.accept()
        try:
            self.parsers_list.move_buttons()
        except AttributeError as e:
            print(e)

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
            if ind == 1:
                self.apply_button.hide()
                self.run_button.hide()
                self.test_button.hide()
                self.cancel_button.hide()
            else:
                self.apply_button.show()
                self.run_button.show()
                self.test_button.show()
                self.cancel_button.show()
                self.apply_button.setEnabled(any(self.main.currentWidget().changed.values()))

    def init_parsers_list(self):
        self.parsers_scroll = QScrollArea(self)
        self.parsers_scroll.verticalScrollBar().setStyleSheet('''
            QScrollBar:vertical, QScrollBar::handle:vertical,QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical, QScrollBar::left-arrow:vertical,
            QScrollBar::right-arrow:vertical{
                border: 1px solid white;
                background: #121212;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical{
                background: #303030;
                border:1px solid white;
            }
        ''')
        self.parsers_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.parsers_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.parsers_scroll.setWidgetResizable(True)
        res = self.db.execute("SELECT id, name, url, respath from parsers")
        self.parsers_list = ParsersList(
            q_parsers=dict(map(lambda x: (x[0], (x[1], x[2], x[3])), res)),
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
            path = self.img_path + "/" + str(q_parser.id_p) + ".png"
            if os.path.exists(path):
                q_parser.set_image(path)
        self.parsers_list.delete_buttons.buttonClicked.connect(self.delete_parser)
        self.parsers_list.parse_buttons.buttonClicked.connect(self.run_stop_parser)
        self.parsers_list.result_buttons.buttonClicked.connect(self.check_path)

    def check_db(self):
        res = self.db.execute("SELECT id, linkstype, links, respath from parsers")
        for i in res:
            print(i)
            links_type = None
            links = None
            respath = None
            if i[1] != "Sitemap":
                if i[2] and not os.path.exists(i[2]):
                    links = ""
                    links_type = "Link"
                if i[3] and not os.path.exists(i[3]):
                    respath = ""
            else:
                paths = get_sitemaps_paths(i[2].split(';')[0], i[0], './sitemaps')
                print(paths)
                if i[2] and (not os.path.exists(paths[0]) or (not os.path.exists(paths[1]))):
                    links = ""
                    links_type = "Link"
            if links_type or links or respath:
                self.db.update_parser(i[0], type_p=links_type, links=links, respath=respath)

    def check_path(self, btn):
        id_p = self.parsers_list.result_buttons.id(btn)
        element = self.parsers_list.get_element(id_p)
        if not os.path.exists(element.fpath):
            self.db.update_parser(id_p, respath="")
            element.set_result("")

    def init_proxies_page(self):
        self.proxies_page = QWidget(self)
        body = QVBoxLayout()
        self.proxies_edit = QTextEdit()
        with open("proxies.txt", "r") as r:
            self.proxies_edit.setText(r.read())
        self.proxies_edit.setPlaceholderText("Each proxie on new line.\ntype://user:pass@host:port"
                                             "\ntype://host:port")
        body.addWidget(self.proxies_edit)
        self.proxies_page.setLayout(body)

    def open_parsers_list(self):
        self.main.setCurrentIndex(0)

    def delete_parser(self, btn):
        reply = QMessageBox.question(self, "Delete parser", "Doо you want delete parser?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            id_p = self.parsers_list.delete_buttons.id(btn)
            dele = next((
                self.main.widget(i) for i in range(2, self.main.count()) if
                i and (self.main.widget(i).q_parser.id_p == id_p)), None)
            self.main.removeTab(self.main.indexOf(dele))
            self.parsers_list.delete_buttons.removeButton(btn)
            self.parsers_list.get_element(id_p).delete_self()
            if self.parse.get(id_p):
                self.parse[id_p].kill()
                self.parse[id_p].join()
            del self.parsers_list.q_parsers[id_p]
            self.db.delete_parser(id_p)
            # res_path = self.res_path + '/' + str(id_p) + '.xlsx'
            # if os.path.exists(res_path):
            #     os.remove(res_path)
            for r in glob.glob("./sitemaps/*_" + str(id_p) + "_small.xml"):
                os.remove(r)

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
                if self.parse[id_p].isAlive():
                    self.parse[id_p].kill()
                    self.parse[id_p].join()
        else:
            self.parse[id_p] = StoppableThread(target=self.start_parsing,
                                               args=(id_p, self.db.get_parser(id_p)))
            self.parse[id_p].start()
            self.parsers_list.get_element(id_p).run_stop()

        QApplication.processEvents()

    def open_parser_edit(self, name, id_p=None):
        if id_p not in self.parse.keys():
            has = next(
                (i for i in range(2, self.main.count()) if
                 i and id_p and (self.main.widget(i).q_parser.id_p == id_p)),
                None)
            print(has)
            print(id_p)
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
                print(q_parser)

    def save_changes_dialog(self, parser_edit, cancel=False):
        """
        Функция сохраняющая изменения в парсере(открытом окне ParserEdit)
        :param parser_edit:
        :param cancel:
        :return:
        """
        path = self.img_path + "/" + str(parser_edit.get_id()) + ".png"
        if not any(parser_edit.changed.values()):
            if parser_edit.new:
                return True
            parser_edit.take_screenshot(path)
            self.parsers_list.get_element(parser_edit.get_id()).set_image(path)
            return True
        res = QMessageBox.question(self, "Saving changes", "Save changes?", (
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel) if cancel else (
                QMessageBox.Yes | QMessageBox.No), QMessageBox.Yes)
        if res == QMessageBox.Yes:
            attrs = parser_edit.get_attributes()

            name = parser_edit.get_name()
            url = parser_edit.get_url()
            if parser_edit.new:
                if not any(parser_edit.errors.values()):
                    id_p = self.db.add_parser(name, url, self.formated_attributes(attrs),
                                              parser_edit.links_type,
                                              parser_edit.res)
                    parser_edit.q_parser.id_p = id_p
                    parser_edit.new = False
                    new = self.parsers_list.add_element(name, id_p, url)
                    new.clicked[str, int].connect(self.open_parser_edit)
                    new.set_url(url)
                else:
                    print("error")
                    QErrorMessage(self).showMessage('Fix errors(red fields)')
                    if parser_edit.new:
                        for i in parser_edit.errors.items():
                            if i[1]:
                                parser_edit.show_error(i[0])
                    return QMessageBox.Cancel if cancel else False
            else:
                self.db.update_parser(parser_edit.q_parser.id_p, name,
                                      url, self.formated_attributes(attrs),
                                      parser_edit.links_type,
                                      parser_edit.res)
                id_p = parser_edit.q_parser.id_p
                element = self.parsers_list.get_element(id_p)
                element.set_name(name)
                element.set_url(url)
            parser_edit.q_parser.name = name
            parser_edit.q_parser.url = url
            parser_edit.q_parser.attributes = attrs
            parser_edit.q_parser.type_p = parser_edit.links_type
            parser_edit.q_parser.links = parser_edit.res
            path = self.img_path + "/" + str(parser_edit.get_id()) + ".png"
            parser_edit.take_screenshot(path)
            self.parsers_list.get_element(parser_edit.get_id()).set_image(path)
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
        if self.main.currentIndex() == 1:
            with open("proxies.txt", "w") as w:
                w.write(self.proxies_edit.toPlainText().replace("\x00", "\n"))
            return

        if btn.text() == "Cancel":

            id_p = parser_edit.get_id()
            if self.test.get(id_p) and self.test[id_p].isAlive():
                self.test[id_p].kill()
                self.test[id_p].join()
            if self.parse.get(id_p) and self.parse[id_p].isAlive():
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
                    element = self.parsers_list.get_element(id_p)
                    element.set_name(parser_edit.get_name())
                    element.set_url(parser_edit.get_url())

                else:
                    url = parser_edit.get_url()
                    attrs = self.formated_attributes(parser_edit.get_attributes())
                    id_p = self.db.add_parser(parser_edit.get_name(), url,
                                              attrs, parser_edit.links_type,
                                              parser_edit.res)
                    new = self.parsers_list.add_element(parser_edit.get_name(), id_p, url)
                    new.clicked[str, int].connect(self.open_parser_edit)
                if self.test.get(id_p) and self.test[id_p].isAlive():
                    self.test[id_p].kill()
                    self.test[id_p].join()
                path = self.img_path + "/" + str(parser_edit.get_id()) + ".png"
                parser_edit.take_screenshot(path)
                self.parsers_list.get_element(id_p).set_image(path)
                self.main.removeTab(self.main.currentIndex())
                self.open_parsers_list()

            elif btn.text() == "Apply":

                attrs = parser_edit.get_attributes()
                name = parser_edit.get_name()
                url = parser_edit.get_url()
                if parser_edit.new:
                    id_p = self.db.add_parser(name, url, self.formated_attributes(attrs), parser_edit.links_type,
                                          parser_edit.res)
                    parser_edit.q_parser.id_p = id_p
                    parser_edit.new = False
                    new = self.parsers_list.add_element(name, id_p, url)
                    new.set_url(url)
                    self.main.setTabText(self.main.currentIndex(), name)
                    new.clicked[str, int].connect(self.open_parser_edit)
                else:
                    id_p = parser_edit.q_parser.id_p
                    self.db.update_parser(id_p, name,
                                          url, self.formated_attributes(attrs),
                                          parser_edit.links_type,
                                          parser_edit.res)
                    element = self.parsers_list.get_element(id_p)
                    element.set_name(parser_edit.get_name())
                    element.set_url(parser_edit.get_url())
                parser_edit.q_parser.name = name
                parser_edit.q_parser.url = url
                parser_edit.q_parser.attributes = attrs
                parser_edit.q_parser.type_p = parser_edit.links_type
                parser_edit.q_parser.links = parser_edit.res
                path = self.img_path + "/" + str(parser_edit.get_id()) + ".png"
                parser_edit.take_screenshot(path)
                self.parsers_list.get_element(parser_edit.get_id()).set_image(path)
                for k in parser_edit.changed.keys():
                    parser_edit.changed[k] = False
                self.apply_button.setEnabled(False)

            elif btn.text() == "Test":
                if self.save_changes_dialog(parser_edit):
                    attrs = parser_edit.get_attributes()
                    id_p = parser_edit.get_id()
                    parser_edit.create_log_widget()
                    self.main.setTabText(self.main.currentIndex(), parser_edit.get_name())
                    if self.test.get(id_p) and self.test[id_p].isAlive():
                        self.test[id_p].kill()
                        self.test[id_p].join()
                    self.test[id_p] = StoppableThread(target=self.start_test,
                                                      args=(self.main.currentIndex(), attrs,))
                    self.test[id_p].start()

            elif btn.text() == "Run":
                if self.save_changes_dialog(parser_edit):
                    id_p = parser_edit.get_id()
                    new = StoppableThread(target=self.start_parsing, args=(
                        id_p, self.db.get_parser(id_p)))
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
            print(dict(map(lambda x: (x[0], tuple(x[1:-1] + (x[-1] == 'True',))),
                           zip_longest(*(iter(re.findall('"(.*?)"', value)),) * 4))))
            return dict(map(lambda x: (x[0], tuple(x[1:-1] + (x[-1] == 'True',))),
                            zip_longest(*(iter(re.findall('"(.*?)"', value)),) * 4)))
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
            map(lambda x: '"{}""{}""{}""{}"'.format(x[0], x[1][0], x[1][1], x[1][2]),
                attrs.items()))

    def closeEvent(self, event):
        self.db.close()
        event.accept()

    def start_test(self, ind, attrs):
        parser_edit = self.main.widget(ind)
        id_p = parser_edit.get_id()
        # try:
        with open("proxies.txt", "r") as r:
            proxies = r.read().split()
        parser = Parser(proxies)
        fields = tuple(map(tuple, attrs.values()))
        print(fields)
        urlm = parser_edit.get_url()
        if attrs:
            # if parser_edit.links:
            if parser_edit.links_type == 'Link':
                links = get_ranges_url(urlm)[:5]
            else:
                links = parser_edit.links[:5]
                if urlm not in links:
                    links[-1] = urlm
            for url in links:
                parser_edit.add_logs(url)
                parsed = parser.parse_url(url, fields)
                if parsed and parsed[0] not in Parser.ERRORS:
                    if filter(lambda x: len(x) > 1, parsed):
                        ma = len(max(parsed, key=lambda x: len(x)))
                        for d in range(ma):
                            data = []
                            for j in parsed:
                                if len(j) == 1:
                                    data.append(j[0])
                                elif len(j) < d:
                                    data.append('')
                                else:
                                    data.append(j[d])
                            parser_edit.add_logs(
                                "\n".join(map(lambda x: "\t" + str(x[0]) + ": " + str(x[1]),
                                              zip(attrs.keys(),
                                                  data))))
                    else:
                        parser_edit.add_logs(
                            "\n".join(map(lambda x: "\t" + str(x[0]) + ": " + str(x[1]),
                                          zip(attrs.keys(),
                                              parsed))))
                elif parsed:
                    parser_edit.add_logs("<pre style='color: red'>\t" + parsed[0] + "</pre>")
                # Задержка, чтобы Log(QTextBrowser) успевал обновляться
                QTest.qWait(1)

            # else:
            #
            #     parsed = parser.parse_url(urlm, fields)
            #     parser_edit.add_logs("\n".join(map(lambda x: str(x[0]) + ": " + str(x[1]),
            #                                        zip(attrs.keys(),
            #                                            parsed))))
        else:
            parser_edit.add_logs("Create attrs")
        del self.test[id_p]

    def start_parsing(self, id_p, request):

        fields = self.generate_attributes(request[3])
        if request[4] == "File":
            if os.path.exists(request[5]):
                with open(request[5], "r") as links:
                    urls = links.read().split("\n")
            else:
                QErrorMessage(self).showMessage('File path wrong')
                return
        elif request[4] == "Links":
            urls = request[5].split("\n")
        elif request[4] == "Link":
            urls = get_ranges_url(request[2])
        elif request[4] == "Sitemap":
            urls = fetch_sitemaps_links(request[5], request[0])

        element = self.parsers_list.get_element(id_p)
        try:
            workbook = xlsxwriter.Workbook(self.res_path + '/' + str(id_p) + '.xlsx')
            worksheet = workbook.add_worksheet()
            worksheet.write(0, 0, "url")
            for p, key in enumerate(fields.keys(), 1):
                worksheet.write(0, p, key)
            with open("proxies.txt", "r") as r:
                proxies = r.read().split()
            parser = Parser(proxies=proxies)
            self.parsers_list.get_element(id_p).set_links_count(len(urls))
            ind = 1
            for urln, i in enumerate(urls, 1):
                res = parser.parse_url(i, fields.values())
                print(res)
                self.parsers_list.get_element(id_p).update_progress(urln)
                if filter(lambda x: len(x) > 1, res):
                    ma = len(max(res, key=lambda x: len(x)))
                    for d in range(ma):
                        data = []
                        for j in res:
                            if len(j) == 1:
                                data.append(j[0])
                            elif len(j) < d:
                                data.append('')
                            else:
                                data.append(j[d])
                        worksheet.write(ind, 0, i)
                        for c, j in enumerate(data, 1):
                            worksheet.write(ind, c, j)
                        ind += 1
                        if ind % 10 == 0:
                            sleep(1)
                else:
                    worksheet.write(ind, 0, i)
                    for c, j in enumerate(res, 1):
                        worksheet.write(ind, c, j)
                    ind += 1
                    if ind % 10 == 0:
                        sleep(1)
            path = self.res_path + "/" + str(id_p) + ".xlsx"
            db = DataBase(self.db_path)
            db.update_parser(id_p, respath=path)
            db.close()
            element.set_result(path)
            workbook.close()
        finally:
            element.hide_progress()
            element.run_stop()
            for childQWidget in self.findChildren(QWidget):
                if childQWidget.__class__.__name__ == 'QMessageBox':
                    childQWidget.close()
            del self.parse[id_p]
            print("end_parsing")
