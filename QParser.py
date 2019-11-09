from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, \
    QHBoxLayout, QVBoxLayout, QSizePolicy, QLineEdit, QButtonGroup, QGridLayout, QTextBrowser, \
    QComboBox, QScrollArea
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QUrl, QEvent
import requests
import sys
import re


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

    def initUI(self):
        self.delete_buttons = QButtonGroup(self)
        self.layout_v = QVBoxLayout(self)
        for key, q_parser in self.q_parsers.items():
            q_parser.set_element(ParserElement(q_parser.name, self))
            self.delete_buttons.addButton(q_parser.element.delete, key)
            self.layout_v.addWidget(q_parser.element, alignment=Qt.AlignTop)
        self.createNewButton = QPushButton("+", self)
        self.createNewButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layout_v.addWidget(self.createNewButton, alignment=Qt.AlignTop)


class ParserElement(QWidget):
    clicked = pyqtSignal(str)

    def __init__(self, name, parent=None):
        super(ParserElement, self).__init__(parent)
        self.name = name
        self.initUI()

    def initUI(self):
        self.element = QHBoxLayout(self)
        self.title = QLabel(self)
        self.title.setText(self.name)
        self.element.addWidget(self.title, stretch=90)
        self.delete = QPushButton("X", self)
        self.element.addWidget(self.delete, stretch=10)

    def mousePressEvent(self, event):
        self.last = "Click"

    def mouseReleaseEvent(self, event):
        if self.last == "Click":
            QTimer.singleShot(QApplication.instance().doubleClickInterval(),
                              self.performSingleClickAction)
        else:
            self.clicked.emit(self.last)

    def mouseDoubleClickEvent(self, event):
        self.last = "Double Click"

    def performSingleClickAction(self):
        if self.last == "Click":
            self.clicked.emit(self.last)


class ParserEdit(QWidget):
    name_changed = 1
    url_changed = 2

    def __init__(self, q_parser, parent=None):
        super(ParserEdit, self).__init__(parent)
        self.q_parser = q_parser
        self.foc_attr_value = None
        self.changed = False
        self.initUI()

    def initUI(self):
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
        self.url_edit = QLineEdit(self)
        self.url_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.url_edit.editingFinished.connect(self.open_browser)
        # self.url_edit.setMaximumHeight(30)
        self.top_l.addWidget(QLabel("Name:"), 0, 0)
        self.top_l.addWidget(self.name_edit, 0, 1)
        self.top_l.addWidget(QLabel("Url:"), 1, 0)
        self.top_l.addWidget(self.url_edit, 1, 1)
        self.body = QHBoxLayout(self)
        # self.attribute_fields = [FieldEdit(self)]
        self.fields_area = QScrollArea(self)
        self.fields_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.fields_area.setWidgetResizable(True)
        self.fields_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.fields = FieldsPull(attributes=self.q_parser.attributes, parent=self, e_filter=self)
        self.fields.field_changed.connect(lambda: print("changes"))
        self.fields.installEventFilter(self)
        self.fields.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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
        self.body.addWidget(self.view, 60)
        self.layout_v.addLayout(self.top_l, 10)
        self.layout_v.addLayout(self.body, 90)
        self.logs = None
        if self.q_parser:
            self.name_edit.setText(self.q_parser.name)
            self.url_edit.setText(self.q_parser.url)
            self.open_url(self.q_parser.url)

    def get_name(self):
        return self.name_edit.text()

    def get_url(self):
        return self.url_edit.text()

    def get_attributes(self):
        return self.fields.get_attributes()

    def open_url(self, url):
        self.view.setUrl(QUrl(url))
        self.view.setZoomFactor(0.5)

    def check_url(self, url):
        try:
            requests.get(url)
            return True
        except Exception as e:
            return False

    def open_browser(self):
        if self.check_url(self.get_url()):
            self.open_url(self.get_url())

    def eventFilter(self, source, event):
        if (event.type() == QEvent.Resize) and (source is self.fields):
            source.setMinimumWidth(10)
        elif (event.type() == QEvent.FocusIn) and (source.objectName() == "value"):
            self.foc_attr_value = source
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
            print(1)
            self.foc_attr_value.setText(result)
            self.foc_attr_value.editingFinished.emit()
            self.foc_attr_value = None
        print(result)

    def create_log_widget(self):
        if not self.logs:
            self.logs = QTextBrowser(self)
            self.logs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.layout_v.addWidget(self.logs, 20, Qt.AlignBottom)
            # sys.stdout.write = lambda x: self.logs.append(str(x))

    def add_logs(self, log):
        self.logs.append(log)

    def check_changes(self, *args):


class FieldsPull(QWidget):
    field_changed = pyqtSignal(int, QWidget)
    key_exists_error = 1
    value_empty_error = 2
    type_empty_error = 3

    def __init__(self, attributes=None, parent=None, del_func=None, e_filter=None):
        super(FieldsPull, self).__init__(parent)
        self.attributes = attributes
        self.del_func = del_func
        if e_filter:
            self.e_filter = e_filter
        else:
            self.e_filter = self
        self.initUI()

    def initUI(self):
        self.body = QVBoxLayout(self)
        if self.attributes:
            for attribute in self.attributes:
                self.create_field(attribute)
            self.create_space(self.get_last_widget())
        else:
            self.create_field()

    def get_last_widget(self):
        if self.body.count():
            return self.body.itemAt(self.body.count() - 1).widget()
        return None

    def get_widget(self, id):
        if self.body.count():
            return self.body.itemAt(id).widget()
        return None

    def get_all_widgets(self):
        return tuple(self.body.itemAt(item).widget() for item in range(self.body.count()))

    def get_attributes(self):
        return dict(field.get_item() for field in self.get_all_widgets()[:-1])

    def get_keys(self):
        return tuple(field.get_item()[0] for field in self.get_all_widgets())

    def create_field(self, attribute=None):
        new = FieldEdit(values=attribute, parent=self, del_func=self.del_func)
        self.body.addWidget(new, alignment=Qt.AlignTop)
        # new.key.textEdited.connect(self.thing_changed)
        new.edit_finished[QWidget].connect(self.create_space)
        new.edit_finished[QWidget].connect(lambda x: self.show_error(x, self.name_exists_error) if self.exists_name(x) else None)
        new.edit_changed.connect(self.field_change)
        new.key.installEventFilter(self.e_filter)
        # new.value.textEdited.connect(self.field_change)
        new.value.installEventFilter(self.e_filter)
        return new

    def create_space(self, last):
        self.create_field()
        last.edit_finished.disconnect(self.create_space)

    def field_change(self, *args):
        print("f_changed")
        # if
        self.field_changed.emit(args[1], args[0])

    def exists_name(self, field):
        if self.get_keys().count(field.get_key()) > 1:
            return True
        return False

    def show_error(self, field, type):
        if type == self.type_empty_error:
            field.value_type.setStyleSheet("border: 4px solid red;")
        elif type == self.value_empty_error:
            field.value.setStyleSheet("border: 4px solid red;")
        elif type == self.key_exists_error:
            field.key.setStyleSheet("border: 4px solid red;")


class FieldEdit(QWidget):
    edit_finished = pyqtSignal(QWidget)
    edit_changed = pyqtSignal([QWidget, int], [QWidget, int, str])
    key_changed = 3
    value_changed = 4
    type_changed = 5

    def __init__(self, values=None, parent=None, del_func=None):
        super(FieldEdit, self).__init__(parent)
        if del_func:
            self.del_func = del_func
        else:
            self.del_func = self.delete
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
            self.delete_btn.clicked.connect(self.del_func)
            self.delete_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.body.addWidget(self.delete_btn, 10)
            return self.delete_btn

    def delete(self):
        self.setParent(None)

    def add_select_type_box(self):
        if not self.value_type:
            self.value_type = QComboBox(self)
            self.value_type.addItems([])
            self.value_type.activated[str].connect(
                lambda x: self.send_changed(self.type_changed, x))
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

    def send_changed(self, *args):
        self.edit_changed[(QWidget, int) if len(args) == 1 else (QWidget, int, str)].emit(self,
                                                                                          *args)
        if args[0] == self.value_changed:
            self.set_value_types()

    def send_finished(self):
        self.edit_finished.emit(self)


class QParser:

    def __init__(self, id, name, url, attributes, element=None):
        self.id = id
        self.name = name
        self.url = url
        self.attributes = attributes
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

        # self.HL = QHBoxLayout(self)
        # self.view = QWebEngineView(self)
        # page = WebEnginePage(self.view)
        # self.view.setPage(page)
        # self.view.installEventFilter(self)
        # self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        #
        # self.left = QVBoxLayout(self)
        # self.parsersLayout = QVBoxLayout(self)
        # self.left.addLayout(self.parsersLayout)
        #
        # self.button = QPushButton("+", self)
        # self.button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # self.button.clicked.connect(self.add_parser)
        # self.left.addWidget(self.button)
        #
        # self.HL.addLayout(self.left, 50)
        # self.HL.addWidget(self.view, 50)
        # self.HL.setStretch(50, 50)
        # # self.statusBar = QStatusBar(self)
        # # self.statusBar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # # self.button1 = QPushButton("<-", self)
        # # self.statusBar.addWidget(self.button1)

    # def add_parser(self):
    #     self.q_parsers.append(ParserElement(self))
    #     self.parsersLayout.addLayout(self.q_parsers[-1].element)
    #


S_WRITE = sys.stdout.write
