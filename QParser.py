from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, \
    QHBoxLayout, QVBoxLayout, QSizePolicy, QLineEdit, QButtonGroup, QGridLayout, QTextBrowser, QComboBox
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QUrl, QEvent
import requests
import sys


class WebEnginePage(QWebEnginePage):

    def acceptNavigationRequest(self, url, navType, mainFrame):
        if navType == QWebEnginePage.NavigationTypeTyped:
            return True
        return False


class ParsersList(QWidget):

    def __init__(self, parsers, parent=None):
        super(ParsersList, self).__init__(parent)
        self.parsers = parsers
        self.initUI()

    def initUI(self):
        self.delete_buttons = QButtonGroup(self)
        self.layout_v = QVBoxLayout(self)
        for key, parser in self.parsers.items():
            parser.set_element(ParserElement(parser.name, self))
            self.delete_buttons.addButton(parser.element.delete, key)
            self.layout_v.addWidget(parser.element, alignment=Qt.AlignTop)
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
    changes = False

    def __init__(self, parser, parent=None):
        super(ParserEdit, self).__init__(parent)
        self.parser = parser
        self.foc_attr_value = None
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
        self.fields = FieldsPull(self, e_filter=self)
        self.fields.field_changed.connect(lambda: print("changes"))
        self.body.addWidget(self.fields, 40, Qt.AlignTop)
        # self.body.addWidget(self.attribute_fields[0], 40, Qt.AlignTop)
        self.view = QWebEngineView(self)
        self._glwidget = self.view
        profile = QWebEngineProfile.defaultProfile()
        # profile.setHttpUserAgent("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36")
        page = WebEnginePage(profile, self.view)
        self.view.setPage(page)
        self.view.installEventFilter(self)
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view.setZoomFactor(0.5)
        self.body.addWidget(self.view, 60)
        self.layout_v.addLayout(self.top_l, 10)
        self.layout_v.addLayout(self.body, 90)
        self.logs = None
        if self.parser:
            self.name_edit.setText(self.parser.name)
            self.url_edit.setText(self.parser.url)
            self.open_url(self.parser.url)

    def get_name(self):
        return self.name_edit.text()

    def get_url(self):
        return self.url_edit.text()

    def get_attributes(self):
        pass

    def open_url(self, url):
        self.view.setUrl(QUrl(url))

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
        if event.type() == QEvent.FocusIn:
            if source.objectName() == "value":
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
            self.fields.check_full()
        print(result)

    def create_log_widget(self):
        if not self.logs:
            self.logs = QTextBrowser(self)
            self.logs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.layout_v.addWidget(self.logs, 20, Qt.AlignBottom)
            sys.stdout.write = lambda x: self.logs.append(str(x))

    def __del__(self):
        sys.stdout.write = S_WRITE


class FieldsPull(QWidget):
    field_changed = pyqtSignal()

    def __init__(self, parent=None, del_func=None, e_filter=None):
        super(FieldsPull, self).__init__(parent)
        self.del_func = del_func
        if e_filter:
            self.e_filter = e_filter
        else:
            self.e_filter = self
        self.initUI()

    def initUI(self):
        self.body = QVBoxLayout(self)
        self.create_field()

    def get_last_widget(self):
        if self.body.count():
            return self.body.itemAt(self.body.count() - 1).widget()
        return None

    def get_all_widgets(self):
        return [item.widget() for item in self.body.children()]

    def create_field(self):
        new = FieldEdit(self, del_func=self.del_func)
        self.body.addWidget(new, alignment=Qt.AlignTop)
        # new.key.textEdited.connect(self.thing_changed)
        new.edit_finished.connect(self.create_place)
        new.edit_changed.connect(self.field_change)
        new.key.installEventFilter(self.e_filter)
        # new.value.textEdited.connect(self.field_change)
        new.value.installEventFilter(self.e_filter)
        return new

    def create_place(self):
        self.create_field()
        self.body.itemAt(self.body.count() - 2).widget().edit_finished.disconnect(self.create_place)

    def field_change(self):
        self.field_changed.emit()


class FieldEdit(QWidget):
    edit_finished = pyqtSignal()
    edit_changed = pyqtSignal()

    def __init__(self, parent=None, del_func=None):
        super(FieldEdit, self).__init__(parent)
        if del_func:
            self.del_func = del_func
        else:
            self.del_func = self.delete
        self.initUI()

    def initUI(self):
        self.body = QHBoxLayout(self)
        self.key = QLineEdit(self)
        self.key.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.key.editingFinished.connect(self.check_full)
        self.key.textEdited.connect(self.send_changed)
        self.key.setPlaceholderText("Name")
        self.key.setObjectName("key")
        self.value = QLineEdit(self)
        self.value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.value.editingFinished.connect(self.check_full)
        self.value.textEdited.connect(self.send_changed)
        self.value.setPlaceholderText("Value")
        self.value.setObjectName("value")
        self.body.addWidget(self.key, 20)
        self.body.addWidget(self.value, 80)
        self.delete_btn = None
        self.value_type = None
        self.edit_finished.connect(self.init_after_edit)

    def get_key(self):
        return self.key.text()

    def get_value(self):
        return self.value.text()

    def set_key(self, text):
        self.key.setText(text)

    def set_value(self, text):
        self.value.setText(text)

    def init_after_edit(self):
        self.add_select_type_box([])
        self.add_delete_btn()
        self.edit_finished.disconnect(self.init_after_edit)

    def add_delete_btn(self):
        if not self.delete_btn:
            self.delete_btn = QPushButton("X", self)
            self.delete_btn.clicked.connect(self.del_func)
            self.delete_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.body.addWidget(self.delete_btn, 10)
            return self.delete_btn

    def delete(self):
        self.setParent(None)

    def add_select_type_box(self, vars):
        if not self.value_type:
            self.value_type = QComboBox(self)
            self.value_type.addItems(vars)
            self.value_type.activated.connect(self.send_changed)
            self.body.addWidget(self.value_type, 20)
            return self.value_type

    def check_full(self):
        if self.get_key() or self.get_value():
            self.send_finished()

    def set_vars(self, vars):
        self.value_type.clear()
        self.value_type.addItems(vars)

    def send_changed(self):
        self.edit_changed.emit()

    def send_finished(self):
        self.edit_finished.emit()


class Parser:

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
    #     self.parsers.append(ParserElement(self))
    #     self.parsersLayout.addLayout(self.parsers[-1].element)
    #


S_WRITE = sys.stdout.write
