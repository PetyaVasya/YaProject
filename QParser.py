import math

from PyQt5.QtGui import QIcon, QPainter, QFontDatabase, QFont, QPixmap, QFontMetrics, QPalette, \
    QPen, QBrush, QColor
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, \
    QHBoxLayout, QVBoxLayout, QSizePolicy, QLineEdit, QButtonGroup, QGridLayout, QTextBrowser, \
    QComboBox, QScrollArea, QFileDialog, QStyle, QProgressBar, QStyleOption, QRadioButton, \
    QStackedWidget, QMainWindow, QTextEdit, QTreeWidget, QDialog, QStatusBar
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QUrl, QEvent
import requests
import re
import os


class WebEnginePage(QWebEnginePage):

    def acceptNavigationRequest(self, url, navType, mainFrame):
        if navType == QWebEnginePage.NavigationTypeTyped:
            return True
        return False


class ParsersList(QWidget):

    def __init__(self, q_parsers, parent=None):
        super(ParsersList, self).__init__(parent)
        self.q_parsers = q_parsers
        self.initUI()

    def paintEvent(self, evt):
        super(ParsersList, self).paintEvent(evt)
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        s = self.style()
        s.drawPrimitive(QStyle.PE_Widget, opt, p, self)

    def move_buttons(self):
        ph = self.parent().height()
        pw = self.parent().width()
        px = self.parent().geometry().x()
        py = self.parent().geometry().y()
        dw = self.createNewButton.maximumWidth()
        dh = self.createNewButton.maximumHeight()
        self.createNewButton.setGeometry(px + pw - dw - 30, py + ph - dh - 21 - min(29, (ph / 8)), dw, dh)
        for i in self.get_elements():
            i.move_delete()

    def initUI(self):
        self.delete_buttons = QButtonGroup(self)
        self.parse_buttons = QButtonGroup(self)
        self.setStyleSheet("""
        ParsersList {
            background-color: #121212;
            border-radius: 20px;
            }
        """)
        self.layout_v = QVBoxLayout(self)
        for key, value in self.q_parsers.items():
            new = ParserElement(name=value[0], id=key, respath=value[1], parent=self)
            self.delete_buttons.addButton(new.delete, key)
            self.parse_buttons.addButton(new.run, key)
            self.layout_v.addWidget(new, alignment=Qt.AlignTop)

        self.createNewButton = QPushButton("+", self)
        # self.createNewButton.setFont(your_ttf_font)
        self.createNewButton.setStyleSheet("position:relative;top:100px;background-color: #03DAC5; border-radius:30px; color:black; font-size: 26px;")
        # self.createNewButton.move(300, 300)
        # self.createNewButton.setParent(self)
        self.createNewButton.setMaximumWidth(60)
        self.createNewButton.setMaximumHeight(60)
        self.createNewButton.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.move_buttons()
        # self.layout_v.addWidget(self.createNewButton, alignment=Qt.AlignTop)

    def get_element(self, id):
        return next((self.layout_v.itemAt(i).widget() for i in range(self.layout_v.count()) if
                     self.layout_v.itemAt(i).widget().id == id), None)

    def add_element(self, name, id, respath=None):
        new = ParserElement(name=name, id=id, respath=respath, parent=self)
        self.delete_buttons.addButton(new.delete, id)
        self.parse_buttons.addButton(new.run, id)
        self.layout_v.insertWidget(self.layout_v.count() - 1,new, alignment=Qt.AlignTop)
        return new

    def get_elements(self):
        return (self.layout_v.itemAt(i).widget() for i in range(self.layout_v.count()))


class ParserElement(QWidget):
    clicked = pyqtSignal([str], [str, int])
    progress_changed = pyqtSignal(int)

    def __init__(self, name, id=None, respath=None, execute=False, parent=None):
        super(ParserElement, self).__init__(parent)
        self.name = name
        self.id = id
        self.fpath = respath
        self.execute = execute
        self.run_vars = ["SP_MediaPlay", "SP_MediaPause"]
        self.initUI()

    def paintEvent(self, evt):
        super(ParserElement, self).paintEvent(evt)
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        s = self.style()
        s.drawPrimitive(QStyle.PE_Widget, opt, p, self)

    def initUI(self):
        btn_css = '''border-radius:5px;font-size:24px;background-color:#BB86FC;
        '''
        btn_css2 = '''border-radius:15px;font-size:16px;background-color:white;
                '''
        self.setMinimumHeight(200)
        self.setStyleSheet("""
        ParserElement {
            background-color: rgb(30, 30, 30);
            border-radius: 20px;
            }
        """)

        # self.setStyleSheet('''border-radius:50px; background-color:white;''')
        # self.setAutoFillBackground(True)
        # a = self.palette()
        # a.setColor(self.backgroundRole(), Qt.white)
        # self.setPalette(a)
        # self.st
        self.element = QHBoxLayout(self)
        self.pixmap = QPixmap("img.png")
        self.img = QLabel(self)
        self.img.setPixmap(self.pixmap)
        self.title = QLabel(self)
        self.title.setText(self.name)
        self.title.setStyleSheet('''color:white;font-size:32px''')
        self.element.addWidget(self.img)
        self.element.addWidget(self.title, stretch=60)
        self.result = QPushButton(self)
        self.result.setIcon(self.style().standardIcon(getattr(QStyle, "SP_FileIcon")))
        self.result.clicked.connect(self.open_result)
        self.result.setStyleSheet(btn_css)
        self.parse_bar = QProgressBar(self)
        self.parse_bar.setFormat("%v/%m")
        self.parse_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.progress_changed.connect(self.set_progress)
        if not self.execute:
            self.parse_bar.hide()
        if not self.fpath:
            self.result.hide()
        self.element.addWidget(self.parse_bar, stretch=20)
        self.element.addWidget(self.result, stretch=10)
        self.run = QPushButton(self)
        self.run.setStyleSheet(btn_css)
        # self.run.clicked.connect(self.run_stop)
        self.run.setIcon(self.style().standardIcon(getattr(QStyle, self.run_vars[self.execute])))
        self.element.addWidget(self.run, stretch=10)
        self.delete = QPushButton("X", self)
        print(self.width())
        self.setContentsMargins(0, 0, 0, 0)
        self.delete.setFixedWidth(30)
        self.delete.setFixedHeight(30)
        self.delete.setGeometry(self.width() - self.delete.width(), 0, self.delete.width(), self.delete.height())
        self.delete.setStyleSheet(btn_css2)
        # self.element.addWidget(self.delete, stretch=10)

    def move_delete(self):
        self.delete.setGeometry(self.width() - self.delete.width(), 0, self.delete.width(),
                                self.delete.height())

    def mousePressEvent(self, event):
        self.last = "Click"

    def mouseReleaseEvent(self, event):
        if self.last == "Click":
            QTimer.singleShot(QApplication.instance().doubleClickInterval(),
                              self.performSingleClickAction)
        else:
            if self.id:
                self.clicked[str, int].emit(self.last, self.id)
            else:
                self.clicked[str].emit(self.last)

    def mouseDoubleClickEvent(self, event):
        self.last = "Double Click"

    def performSingleClickAction(self):
        if self.last == "Click":
            if self.id:
                self.clicked[str, int].emit(self.last, self.id)
            else:
                self.clicked[str].emit(self.last)

    def run_stop(self):
        self.execute ^= 1
        self.run.setIcon(self.style().standardIcon(getattr(QStyle, self.run_vars[self.execute])))

    def set_result(self, path):
        self.fpath = path
        if self.fpath:
            self.result.show()
        else:
            self.result.show()

    def open_result(self):
        os.system("open " + self.fpath)

    def delete_self(self):
        self.setParent(None)

    def set_progress(self, value):
        if not self.parse_bar.isVisible():
            self.parse_bar.show()
        self.parse_bar.setValue(value)

    def set_links_count(self, count):
        self.parse_bar.setMaximum(count)

    def hide_progress(self):
        self.parse_bar.hide()

    def update_progress(self, value):
        self.progress_changed.emit(value)

    def set_name(self, name):
        self.title.setText(name)


class ParserEdit(QWidget):
    thing_changed = pyqtSignal([int], [int, int, QWidget])
    name_changed = 1
    url_changed = 2
    attributes_changed = 3
    links_changed = 4
    name_empty_error = 5
    attribute_error = 6
    incorrect_url_error = 7

    def __init__(self, q_parser, new, parent=None):
        super(ParserEdit, self).__init__(parent)
        self.q_parser = q_parser
        self.foc_attr_value = None
        self.changed = {self.name_changed: False, self.url_changed: False,
                        self.attributes_changed: False, self.links_changed: False}
        self.errors = {self.name_empty_error: new, self.attribute_error: False,
                       self.incorrect_url_error: new}
        self.new = new
        self.initUI()

    def initUI(self):
        self.thing_changed.connect(self.check_changes)
        self.layout_v = QVBoxLayout(self)
        # self.setLayout(self.layout_v)
        self.top_l = QGridLayout(self)
        # self.top_l.setColumnStretch(1, 20)
        # self.top_l.setColumnStretch(2, 80)
        # self.top_l.setRowStretch(1, 10)
        # self.top_l.setRowStretch(2, 10)
        self.name_edit = QLineEdit(self)
        # self.name_edit.setMaximumHeight(30)
        self.name_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.name_edit.editingFinished.connect(lambda: self.check_error(self.name_changed))
        self.name_edit.textChanged.connect(lambda: self.send_changed(self.name_changed))
        # self.url_layout = QHBoxLayout(self)
        # self.top_l.add
        self.url_load = QPushButton("Load", self)
        self.url_edit = QLineEdit(self)
        self.links_box = QComboBox(self)
        self.links_box.setLineEdit(self.url_edit)
        self.links_box.currentIndexChanged.connect(self.open_browser)
        self.url_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # self.url_edit.editingFinished.connect(self.open_browser)
        self.url_load.clicked.connect(self.open_browser)
        self.url_edit.textChanged.connect(lambda: self.send_changed(self.url_changed))
        # self.url_edit.setMaximumHeight(30)
        self.btn_upload = QPushButton("Upload", self)
        # self.upload_links.clicked.connect(self.get_file)
        self.btn_upload.clicked.connect(self.upload_links)
        self.top_l.addWidget(QLabel("Name:"), 0, 0)
        self.top_l.addWidget(self.name_edit, 0, 1)
        self.top_l.addWidget(QLabel("Url:"), 1, 0)
        self.top_l.addWidget(self.btn_upload, 0, 2)
        # self.top_l.addWidget(self.url_edit, 1, 1)
        self.top_l.addWidget(self.links_box, 1, 1)
        self.top_l.addWidget(self.url_load, 1, 2)
        self.body = QHBoxLayout(self)
        # self.attribute_fields = [FieldEdit(self)]
        self.fields_area = QScrollArea(self)
        self.fields_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.fields_area.setWidgetResizable(True)
        self.fields_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.fields_area.setContentsMargins(0, 0, 0, 0)
        self.fields = FieldsPull(attributes=self.q_parser.attributes, parent=self, e_filter=self)
        self.fields.field_changed.connect(lambda: print("changes"))
        self.fields.installEventFilter(self)
        self.fields.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.fields.field_changed.connect(lambda: self.send_changed(self.attributes_changed))
        self.fields.error_created.connect(
            lambda: self.errors.__setitem__(self.attribute_error, True))
        self.fields.errors_fixed.connect(
            lambda: self.errors.__setitem__(self.attribute_error, False))
        # self.fields.error_created[int, QWidget].connect(lambda x, y: self.errors.setdefault(y, set()).add(x))
        # self.fields.error_fixed[int, QWidget].connect(lambda x, y: self.errors[y].remove(x))
        self.fields_area.setWidget(self.fields)
        self.body.addWidget(self.fields_area, Qt.AlignTop)
        self.body.setStretch(1, 40)
        # self.body.addWidget(self.attribute_fields[0], 40, Qt.AlignTop)
        self.view = QWebEngineView(self)
        self._glwidget = self.view
        profile = QWebEngineProfile.defaultProfile()
        # profile.setHttpUserAgent("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36")
        page = WebEnginePage(profile, self.view)
        self.view.setPage(page)
        self.view.installEventFilter(self)
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.view.loadFinished.connect(lambda: self.view.grab().scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation).save("img.png", b'PNG'))
        self.body.addWidget(self.view, 60)
        self.layout_v.addLayout(self.top_l, 10)
        self.layout_v.addLayout(self.body, 90)
        self.links = []
        self.logs = None
        if self.q_parser:
            self.name_edit.setText(self.q_parser.name)
            self.url_edit.setText(self.q_parser.url)
            self.open_url(self.q_parser.url)
            self.res = self.q_parser.links
            self.links_type = self.q_parser.type
            if self.links_type == "File":
                self.links_from_file(self.q_parser.links)
            elif self.links_type == "Links":
                self.links = tuple(filter(lambda x: x, set(
                    self.res.strip().strip("\n").strip("\x00").split("\n"))))
                self.set_links(self.links)
            elif self.links_type == "Sitemap":
                pass
        else:
            self.res = ""
            self.links_type = ""
        print(self.links_type)

    def get_name(self):
        return self.name_edit.text()

    def get_url(self):
        return self.url_edit.text()

    def get_id(self):
        return self.q_parser.id

    def get_attributes(self):
        return self.fields.get_attributes()

    def open_url(self, url):
        self.view.setUrl(QUrl(url))
        QTimer.singleShot(1000, lambda: self.view.setZoomFactor(0.5))

    def check_url(self, url):
        try:
            requests.get(url)
            return True
        except Exception as e:
            return False

    def open_browser(self):
        if self.check_url(self.get_url()):
            normalize_widget(self.url_edit)
            self.errors[self.incorrect_url_error] = False
            self.open_url(self.get_url())
        else:
            self.show_error(self.incorrect_url_error)

    def eventFilter(self, source, event):
        if (event.type() == QEvent.Resize) and (source is self.fields):
            source.setMinimumWidth(10)
        elif (event.type() == QEvent.FocusIn) and (source.objectName() == "value"):
            self.foc_attr_value = source
        elif (event.type() == QEvent.FocusIn) and (type(source).__class__ == QLineEdit):
            self.foc_attr_value = None
        elif (event.type() == QEvent.ChildAdded and
              source is self.view and
              event.child().isWidgetType()):
            self._glwidget = event.child()
            self._glwidget.installEventFilter(self)
        elif (event.type() == QEvent.MouseButtonPress and
              source is self._glwidget):
            print(event.pos())
            func = '''
            function cssSelectorByPos(x, y){
                var element = document.elementFromPoint(x, y);
                var res = element.tagName;
                element.getAttributeNames().forEach(function(item, i, arr){
                    res += `[${item}='${element.getAttribute(item)}']`;
                });
                return res;
            };'''
            self.view.page().runJavaScript(
                func + 'cssSelectorByPos({}, {});'.format(event.pos().x() * 2,
                                                          event.pos().y() * 2),
                self.js_callback)
            # self.view.page().runJavaScript(
            #     "pageYOffset.toString() + ' ' + " + str(event.pos().y()),
            #     self.js_callback)
        return super().eventFilter(source, event)

    def js_callback(self, result):
        if self.foc_attr_value:
            self.foc_attr_value.setText(result)
            self.foc_attr_value.editingFinished.emit()
            self.foc_attr_value = None
        else:
            keys = set(
                map(int, filter(lambda x: x.isdigit() and int(x) > 0, self.fields.get_keys())))
            new_key = min(set(range(1, self.fields.children_count() + 1)) - keys)
            self.fields.create_field((str(new_key), (result, "Text")))
        print(result)

    def create_log_widget(self):
        if not self.logs:
            self.logs = QTextBrowser(self)
            self.logs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.layout_v.addWidget(self.logs, 20, Qt.AlignBottom)
            # sys.stdout.write = lambda x: self.logs.append(str(x))
        else:
            self.logs.clear()

    def add_logs(self, log):
        if self.logs:
            self.logs.append(log)

    def clear_log(self):
        if self.logs:
            self.logs.clear()

    def check_changes(self, *args):
        self.check_error(args[0])
        if args[0] == self.name_changed:
            self.changed[self.name_changed] = self.get_name() != self.q_parser.name
        elif args[0] == self.url_changed:
            self.changed[self.url_changed] = self.get_url() != self.q_parser.url
        elif args[0] == self.attributes_changed:
            self.changed[
                self.attributes_changed] = self.get_attributes() != self.q_parser.attributes
        elif args[0] == self.links_changed:
            self.changed[self.links_changed] = self.res != self.q_parser.links

    def check_error(self, type):
        if type == self.name_changed:
            if self.get_name():
                normalize_widget(self.name_edit)
                self.errors[self.name_empty_error] = False
            else:
                self.show_error(self.name_empty_error)

    def send_changed(self, type):
        self.thing_changed.emit(type)

    def show_error(self, type):
        if type == self.name_empty_error:
            errorize_widget(self.name_edit)
            self.errors[self.name_empty_error] = True
        elif type == self.incorrect_url_error:
            errorize_widget(self.url_edit)
            self.errors[self.incorrect_url_error] = True

    def upload_links(self):
        self.upload_window = UploadLinksWidget(self, self.links_type, self.res)
        if self.upload_window.exec_():
            self.links_type, self.res = self.upload_window.get_result()
            if self.links_type == "File":
                self.links_from_file(self.res)
            elif self.links_type == "Links":
                self.links = tuple(filter(lambda x: x, set(self.res.strip().strip("\n").strip("\x00").split("\n"))))
                self.set_links(self.links)

        # self.upload_window.show()

    def links_from_file(self, file):
        if file:
            with open(file, "r") as links:
                self.links = links.read().split("\n")
                self.set_links(self.links)
                # self.links_box.setEditable(False)
                # self.url_edit.setEnabled(False)

    def set_links(self, links):
        if links:
            self.url_edit.setText(links[0])
            self.links_box.clear()
            self.links_box.addItems(links)
            print(links)



class FieldsPull(QWidget):
    field_changed = pyqtSignal(int, QWidget)
    error_created = pyqtSignal(int, QWidget)
    errors_fixed = pyqtSignal()
    key_exists_error = 1
    value_empty_error = 2
    type_empty_error = 3

    def __init__(self, attributes=None, parent=None, e_filter=None):
        super(FieldsPull, self).__init__(parent)
        self.attributes = attributes
        if e_filter:
            self.e_filter = e_filter
        else:
            self.e_filter = self
        self.errors = {}
        self.initUI()

    def initUI(self):
        self.field_changed[int, QWidget].connect(self.check_error)
        self.error_created[int, QWidget].connect(
            lambda x, y: self.errors.setdefault(y, set()).add(x))
        # self.error_fixed[int, QWidget].connect(lambda x, y: self.errors[y].remove(x))
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(0, 0, 0, 0)
        attrs = tuple(self.attributes.items())
        self.create_field()
        for attribute in attrs:
            self.create_field(attribute)
            # self.get_last_widget().set_values(attribute[0], *attribute[1])
        #     self.create_field(attribute)
        # if attrs:
        #     self.create_field()

    def get_last_widget(self):
        if self.body.count():
            return self.body.itemAt(self.body.count() - 1).widget()
        return None

    def children_count(self):
        return self.body.count()

    def get_widget(self, id):
        if self.body.count():
            return self.body.itemAt(id).widget()
        return None

    def get_all_widgets(self):
        return tuple(self.body.itemAt(item).widget() for item in range(self.body.count()))

    def get_attributes(self):
        return dict(field.get_item() for field in self.get_all_widgets()[:-1])

    def get_keys(self):
        return tuple(field.get_item()[0] for field in self.get_all_widgets()[:-1])

    def create_field(self, attribute=None):
        if self.body.count() and attribute:
            last = self.get_last_widget()
            last.set_values(attribute[0], *attribute[1])
            return last
        else:
            new = FieldEdit(values=attribute, parent=self)
            self.body.addWidget(new, alignment=Qt.AlignTop)
            # new.key.textEdited.connect(self.thing_changed)
            new.edit_finished[QWidget].connect(self.create_space)
            new.edit_changed[int, QWidget].connect(self.field_change)
            new.key.installEventFilter(self.e_filter)
            # new.value.textEdited.connect(self.field_change)
            new.value.installEventFilter(self.e_filter)
            return new

    def create_space(self, last):
        last.edit_finished.disconnect(self.create_space)
        return self.create_field()

    def field_change(self, type, field):
        print("f_changed")
        self.field_changed.emit(type, field)

    def exists_key(self, key):
        if self.get_keys().count(key) > 1:
            return True
        return False

    def check_error(self, type, field):
        if type == FieldEdit.key_changed:
            if self.exists_key(field.get_key()):
                self.show_error(self.key_exists_error, field)
            else:
                normalize_widget(field.key)
                self.remove_error(type, field)
        elif type == FieldEdit.value_changed:
            if field.get_value():
                normalize_widget(field.value)
                self.remove_error(type, field)
            else:
                self.show_error(self.value_empty_error, field)
        elif type == FieldEdit.type_changed:
            if field.get_type():
                normalize_widget(field.value_type)
                self.remove_error(type, field)
            else:
                self.show_error(self.type_empty_error, field)
        elif type == FieldEdit.field_deleted:
            if self.errors.get(field):
                del self.errors[field]
                if not self.errors:
                    self.errors_fixed.emit()

    def show_error(self, type, field):
        if type == self.type_empty_error:
            errorize_widget(field.value_type)
        elif type == self.value_empty_error:
            errorize_widget(field.value)
        elif type == self.key_exists_error:
            errorize_widget(field.key)
        self.error_created[int, QWidget].emit(type, field)

    def remove_error(self, type, field):
        if self.errors.get(field):
            if len(self.errors[field]) > 1:
                self.errors[field].remove(type)
            else:
                self.errors.pop(field)
        if not self.errors:
            self.errors_fixed.emit()


class FieldEdit(QWidget):
    edit_finished = pyqtSignal(QWidget)
    edit_changed = pyqtSignal(int, QWidget)
    key_changed = 1
    value_changed = 2
    type_changed = 3
    field_deleted = 4

    def __init__(self, values=None, parent=None):
        super(FieldEdit, self).__init__(parent)
        self.initUI(values)

    def initUI(self, values=None):
        self.body = QHBoxLayout(self)
        self.key = QLineEdit(self)
        self.key.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.key.editingFinished.connect(self.check_full)
        self.key.setPlaceholderText("Name")
        self.key.setObjectName("key")
        self.value = QLineEdit(self)
        self.value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.value.editingFinished.connect(self.check_full)
        self.value.setPlaceholderText("Value")
        self.value.setObjectName("value")
        self.body.addWidget(self.key, 20)
        self.body.addWidget(self.value, 80)
        self.delete_btn = None
        self.value_type = None
        self.edit_finished.connect(self.init_after_edit)
        if values:
            self.init_after_edit()
            self.set_values(values[0], *values[1])

    def get_key(self):
        return self.key.text()

    def get_value(self):
        return self.value.text()

    def get_type(self):
        if self.value_type:
            return self.value_type.currentText()
        else:
            return ""

    def get_item(self):
        return self.get_key(), (self.get_value(), self.get_type())

    def set_values(self, key, value, type):
        self.send_finished()
        self.key.setText(key)
        self.value.setText(value)
        self.value_type.setCurrentText(type)

    def init_after_edit(self):
        self.add_select_type_box()
        self.add_delete_btn()
        self.edit_finished.disconnect(self.init_after_edit)
        self.key.textChanged.connect(lambda: self.send_changed(self.key_changed))
        self.value.textChanged.connect(lambda: self.send_changed(self.value_changed))

    def add_delete_btn(self):
        if not self.delete_btn:
            self.delete_btn = QPushButton("X", self)
            self.delete_btn.clicked.connect(self.delete)
            self.delete_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.body.addWidget(self.delete_btn, 10)
            return self.delete_btn

    def delete(self):
        self.setParent(None)
        self.send_changed(self.field_deleted)

    def add_select_type_box(self):
        if not self.value_type:
            self.value_type = QComboBox(self)
            self.value_type.setLineEdit(QLineEdit(self))
            self.set_value_types()
            self.value_type.activated.connect(lambda: self.send_changed(self.type_changed))
            self.body.addWidget(self.value_type, 20)
            return self.value_type

    def check_full(self):
        if self.get_key() or self.get_value():
            self.send_finished()

    def set_value_types(self):
        l_value = self.get_value().split()
        if l_value:
            l_value = l_value[-1]
            self.set_vars(["Text"] + re.findall(r"\[(.*?)=.*?\]", l_value))

    def set_vars(self, vars):
        self.value_type.clear()
        self.value_type.addItems(vars)

    def send_changed(self, type):
        self.edit_changed[int, QWidget].emit(type, self)
        if type == self.value_changed:
            self.set_value_types()

    def send_finished(self):
        self.edit_finished.emit(self)


class QParser:

    def __init__(self, id=None, name="", url="", attributes=dict(), type="", links="",
                 element=None):
        self.id = id
        self.name = name
        self.url = url
        self.attributes = attributes
        self.type = type
        self.links = links
        self.element = element

    def add_attribute(self, name, value):
        self.attributes[name] = value

    def remove_attribute(self, name):
        del self.attributes[name]

    def set_element(self, element):
        self.element = element

    def remove_element(self):
        self.element.setParent(None)
        self.element = None


class UploadLinksWidget(QDialog):

    def __init__(self, parent=None, *args):
        super(UploadLinksWidget, self).__init__(parent)
        self.initUI(*args)

    def initUI(self, type=None, data=None):
        self.setGeometry(300, 300, 300, 300)
        self.body = QVBoxLayout(self)
        self.main = QWidget()
        # self.setCentralWidget(self.main)
        self.links_type_layout = QHBoxLayout(self)
        self.btn_group = QButtonGroup(self)
        self.btn_links = QRadioButton("Links", self)
        self.btn_sitemap = QRadioButton("Sitemap", self)
        self.btn_group.addButton(self.btn_links, 0)
        self.btn_group.addButton(self.btn_sitemap, 1)

        self.links_type_layout.addWidget(self.btn_links)
        self.links_type_layout.addWidget(self.btn_sitemap)
        self.body.addLayout(self.links_type_layout, stretch=10)
        self.interface = QStackedWidget(self)
        self.links = QWidget()
        self.sitemap = QWidget()

        self.links_layout = QVBoxLayout(self)
        self.links.setLayout(self.links_layout)
        self.links_edit = QTextEdit(self)
        self.links_edit.setPlaceholderText("Each line on new line")
        self.file_layout = QHBoxLayout(self)
        file = None
        self.btn_links.setChecked(True)
        if type:
            if type == "Links":
                self.links_edit.setText(data)
            elif type == "File":
                file = data
            elif type == "Sitemap":
                self.btn_sitemap.setChecked(True)
            self.type = type
        else:
            self.type = ""
        self.opened_file = CutLabel()
        self.opened_file.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn_open_file = QPushButton("Open")
        self.btn_open_file.clicked.connect(self.get_file)
        self.file_layout.addWidget(self.opened_file, stretch=90)
        self.file_layout.addWidget(self.btn_open_file, stretch=10)
        self.links_layout.addWidget(self.links_edit, stretch=90)
        self.links_layout.addLayout(self.file_layout, stretch=10)
        self.opened_file.setText(file if file else "Choose file")

        self.sitemap_layout = QVBoxLayout(self)
        self.base_url = QLineEdit(self)
        self.base_url.setPlaceholderText("Index Url")
        self.sitemap_layout.addWidget(self.base_url)
        self.sitemap_tree = QTreeWidget(self)
        self.sitemap_layout.addWidget(self.sitemap_tree)
        self.sitemap.setLayout(self.sitemap_layout)

        self.interface.addWidget(self.links)
        self.interface.addWidget(self.sitemap)

        self.final = QButtonGroup()
        self.final.addButton(QPushButton("OK", self))
        self.final.addButton(QPushButton("Cancel", self))

        self.final.buttonClicked.connect(self.close_dialog)
        self.body.addWidget(self.interface, stretch=90)
        # self.main.setLayout(self.body)
        self.setLayout(self.body)
        self.btn_group.buttonClicked.connect(self.change_interface)
        self.bar = QHBoxLayout(self)
        for btn in self.final.buttons():
            self.bar.addWidget(btn)
        self.body.addLayout(self.bar)
        # self.statusBar().addWidget(QPushButton("OK", self))
        # self.statusBar().addWidget(QPushButton("Cancel", self))
        self.setFixedSize(300, 300)

    def change_interface(self, btn):
        print(self.btn_group.id(btn))
        self.interface.setCurrentIndex(self.btn_group.id(btn))

    def get_file(self):
        self.res = QFileDialog.getOpenFileName(self, 'Выберите файл с ссылками', '')[0]
        if self.res:
            self.accept()
            self.type = "File"

    def close_dialog(self, btn):
        if btn.text() == "OK":
            self.type = self.btn_group.checkedButton().text()
            if self.type == "Links":
                self.res = self.links_edit.toPlainText()
            else:
                pass
            self.accept()
        else:
            self.reject()

    def get_result(self):
        return self.type, self.res


class CutLabel(QLabel):

    def paintEvent(self, event):
        painter = QPainter(self)

        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), Qt.ElideLeft, self.width())

        painter.drawText(self.rect(), self.alignment(), elided)


class SitemapWindow(QWidget):

    def __init__(self, mpath=None):
        super().__init__()
        self.initUI(mpath)

    def initUI(self, mpath):
        self.body = QVBoxLayout(self)
        self.setLayout(self.body)
        self.tree = QTreeWidget(self)
        self.body.addWidget(self.tree)
        if mpath:
            self.unparse_tree(mpath)
        else:
            self.tree.hide()

    def unparse_tree(self, path):
        pass

    def grab_links(self, url):
        pass


def normalize_widget(widget):
    widget.setStyleSheet("border: None;")


def errorize_widget(widget):
    widget.setStyleSheet("border: 4px solid red;")
