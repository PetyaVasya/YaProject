import math
import sys
from threading import Thread

from PyQt5 import QtXml
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPalette, QBrush, QColor, QPainter, QPen
from PyQt5.QtWidgets import QWidget, QTreeWidgetItem, QTabBar, QTabWidget


class LoadingWidget(QWidget):
    """
    After 21:00
    """

    def __init__(self, parent=None, text=""):

        QWidget.__init__(self, parent)
        palette = QPalette(self.palette())
        palette.setColor(palette.Background, Qt.transparent)
        self.setPalette(palette)
        self.text = text

    def paintEvent(self, event):

        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(), QBrush(QColor(255, 255, 255, 127)))
        painter.setPen(QPen(Qt.NoPen))

        for i in range(6):
            if (self.counter / 5) % 6 == i:
                painter.setBrush(QBrush(QColor(127 + (self.counter % 5) * 32, 127, 127)))
            else:
                painter.setBrush(QBrush(QColor(127, 127, 127)))
            painter.drawEllipse(
                self.width() / 2 + 30 * math.cos(2 * math.pi * i / 6.0) - 10,
                self.height() / 2 + 30 * math.sin(2 * math.pi * i / 6.0) - 10,
                20, 20)
        painter.drawText(self.width() / 2 + 5, self.height() / 2 + 20, self.text)
        painter.end()

    def showEvent(self, event):

        self.timer = self.startTimer(50)
        self.counter = 0

    def timerEvent(self, event):

        self.counter += 1
        self.update()
        if self.counter == 60:
            self.killTimer(self.timer)
            self.hide()


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


class XmlHandler(QtXml.QXmlDefaultHandler):
    """
        After 21:00
    """

    def __init__(self, root):
        QtXml.QXmlDefaultHandler.__init__(self)
        self._root = root
        self._item = None
        self._text = ''
        self._error = ''

    def startElement(self, namespace, name, qname, attributes):
        if qname == 'category' or qname == 'link' or qname == 'subcategory':
            if self._item is not None:
                self._item = QTreeWidgetItem(self._item)
            else:
                self._item = QTreeWidgetItem(self._root)
            self._item.setData(0, Qt.UserRole, qname)
            self._item.setText(0, 'Unknown Title')
            if qname == 'category' or qname == 'subcategory':
                self._item.setExpanded(True)
                self._item.setText(0, attributes.value('type'))

        self._text = ''
        return True

    def endElement(self, namespace, name, qname):
        if qname == 'title':
            if self._item is not None:
                self._item.setText(0, self._text)
        elif qname == 'folder' or qname == 'item':
            self._item = self._item.parent()
        return True

    def characters(self, text):
        self._text += text
        return True


class CustomBar(QTabBar):

    def __init__(self, width, height, parent=None):
        QTabBar.__init__(self, parent)
        self.setFixedSize(width, height)

    def tabSizeHint(self, i):
        t = int(self.width() / self.count()) - 20
        return QSize(t, self.height())


class CustomTabWidget(QTabWidget):

    def __init__(self, parent=None):
        QTabWidget.__init__(self, parent)

    def resizeEvent(self, event):
        self.tabBar().setMinimumWidth(self.width())
        QTabWidget.resizeEvent(self, event)
