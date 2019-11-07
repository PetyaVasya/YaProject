from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, \
    QHBoxLayout, QVBoxLayout, QSizePolicy, QTextEdit, QButtonGroup
from PyQt5.QtCore import Qt, pyqtSignal, QTimer


class ParsersList(QWidget):

    def __init__(self, parsers, parent=None):
        super(ParsersList, self).__init__(parent)
        self.parsers = parsers
        self.initUI()

    def initUI(self):
        self.setGeometry(500, 500, 500, 500)
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

    def __init__(self, parser, parent=None):
        super(ParserEdit, self).__init__(parent)
        self.parser = parser
        self.initUI()

    def initUI(self):
        self.layout_v = QVBoxLayout(self)
        self.name_edit = QTextEdit(self)
        self.layout_v.addWidget(self.name_edit)
        if self.parser:
            self.name_edit.setText(self.parser.name)

    def get_name(self):
        return self.name_edit.toPlainText()


class Parser:

    def __init__(self, id, name, attributes, element=None):
        self.id = id
        self.name = name
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
    # def eventFilter(self, source, event):
    #     if (event.type() == QEvent.ChildAdded and
    #             source is self.view and
    #             event.child().isWidgetType()):
    #         self._glwidget = event.child()
    #         self._glwidget.installEventFilter(self)
    #     elif (event.type() == QEvent.MouseButtonPress and
    #           source is self._glwidget):
    #         self.view.page().runJavaScript(
    #             'document.elementFromPoint({},{}).outerHTML'.format(event.pos().x(),
    #                                                                 event.pos().y()),
    #             self.js_callback)
    #     return super().eventFilter(source, event)
    #
    # def js_callback(self, result):
    #     print(result)
