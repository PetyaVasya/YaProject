import math
import re
import sys
from functools import reduce
from itertools import product
from threading import Thread

import requests
from PyQt5 import QtXml
from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtGui import QPalette, QBrush, QColor, QPainter, QPen, QFontMetrics
from PyQt5.QtWidgets import QWidget, QTreeWidgetItem, QTabBar, QTabWidget, QProgressBar, \
    QApplication, QLabel, QAbstractItemView, QTreeWidget
from lxml import etree
from usp.tree import sitemap_tree_for_homepage
import xml.etree.cElementTree as ET


class LoadingWidget(QWidget):
    """
    After 21:00
    """

    def __init__(self, parent=None, text=""):

        super(LoadingWidget, self).__init__(parent)
        palette = QPalette(self.palette())
        palette.setColor(palette.Background, Qt.transparent)
        # self.parent().resizeEvent.connect(self.re)
        self.setPalette(palette)

    def paintEvent(self, event):

        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.fillRect(QRect(0, 0, self.width() * 2, self.height()),
                         QBrush(QColor(17, 17, 17, 127)))
        painter.setPen(QPen(Qt.NoPen))

        for i in range(6):
            if (self.counter / 5) % 6 == i:
                painter.setBrush(QBrush(QColor(3, 218, 197)))
            else:
                painter.setBrush(QBrush(QColor(127, 127, 127)))
            painter.drawEllipse(
                self.width() / 2 + 30 * math.cos(2 * math.pi * i / 6.0) - 10,
                self.height() / 2 + 30 * math.sin(2 * math.pi * i / 6.0) - 10 + 30,
                20, 20)
        # painter.drawText(self.width() / 2 + 5, self.height() / 2 + 20, self.text)
        painter.end()

    def showEvent(self, event):

        self.timer = self.startTimer(50)
        self.counter = 0

    def timerEvent(self, event):

        self.counter += 1
        if (self.counter % 5) == 0:
            self.update()

    def resizeEvent(self, event):
        self.resize(self.parent().size())
        event.accept()


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


class CutLabel(QLabel):

    def __init__(self, align, parent=None):
        QLabel.__init__(self, parent)
        self.align = align

    def paintEvent(self, event):
        painter = QPainter(self)

        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), self.align, self.width())

        painter.drawText(self.rect(), self.alignment(), elided)


class XmlHandler(QtXml.QXmlDefaultHandler):
    def __init__(self, root):
        QtXml.QXmlDefaultHandler.__init__(self)
        self._root = root
        self._item = None
        self._text = ''
        self._error = ''

    def startElement(self, namespace, name, qname, attributes):
        if qname == 'category' or qname == 'link' or qname == 'links' or qname == 'subcategory':
            # if (qname == 'link') and self._item.childCount() > 4:
            #     return True
            if self._item is not None:
                self._item = QTreeWidgetItem(self._item)
            else:
                self._item = QTreeWidgetItem(self._root)
            self._item.setData(0, Qt.UserRole, qname)
            self._item.setText(0, 'Unknown Title')
            if qname == 'category' or qname == 'subcategory':
                # self._item.setExpanded(True)
                self._item.setText(0, attributes.value('name'))
                self._item.setFlags(self._item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
                self._item.setCheckState(0, Qt.Checked)
            elif qname == 'links':
                self._item.setText(0, 'Links')
                self._item.setFlags(self._item.flags() | Qt.ItemIsUserCheckable)
                self._item.setCheckState(0, Qt.Checked if attributes.value(
                    'checked') == "True" else Qt.Unchecked)
            elif qname == 'link':
                self._item.setText(0, 'Link')
        self._text = ''
        return True

    def endElement(self, namespace, name, qname):
        # if qname == 'title':
        #     if self._item is not None:
        #         self._item.setText(0, self._text)
        # if qname == 'link' and self._item.childCount() > 4:
        #     return True
        if qname == 'link' and self._item:
            self._item.setText(1, self._text)
        if qname == 'category' or qname == 'link' or qname == 'subcategory' or qname == 'links':
            self._item = self._item.parent()
        return True

    def characters(self, text):
        self._text += text
        return True

    def fatalError(self, exception):
        print('Parse Error: line %d, column %d:\n  %s' % (
            exception.lineNumber(),
            exception.columnNumber(),
            exception.message(),
        ))
        return False

    def errorString(self):
        return self._error


class CustomTreeWidget(QTreeWidget):

    def __init__(self, xml):
        QTreeWidget.__init__(self)
        self.initUI(xml)

    def initUI(self, xml):
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setHeaderLabels(['Title', 'Url'])
        self.set_xml(xml)
        self.itemChanged.connect(self.handleChanged)
        self.itemClicked.connect(self.findd)
        self.header().setStyleSheet('''
            QHeaderView::section:first{
                background:#121212;
                color:white;
                border-top:none;
                border-left:none;
                border-right:none;
                padding-left:10px;
            }
            QHeaderView::section{
                padding-left:10px;
                background:#121212;
                color:white;
                border-top:none;
                border-left:1px solid white;
                border-right:none;
            }
            QHeaderView:{
                border: none;
            }
        ''')

    def handleChanged(self, item, column):
        if len(self.selectedItems()) > 1:
            for sel_item in self.selectedItems():
                sel_item.setCheckState(0, item.checkState(column))

    def findd(self, item, column):
        self.all_checked_items()
        items = self.findItems(item.text(column), Qt.MatchContains | Qt.MatchRecursive)
        # print(item.text(column), [i.text(0) for i in items])
        # for i in items:
        #     i.setSelected(True)

    def all_checked_items(self):
        items = self.findItems('', Qt.MatchContains | Qt.MatchRecursive)
        checked = []
        uncheked = []
        for i in items:
            if (i.checkState(0) == Qt.Checked) or (i.checkState(0) == Qt.PartiallyChecked):
                checked.append(i)
            elif i.text(0) != 'Link':
                uncheked.append(i)
        if len(uncheked) < len(checked):
            return False, uncheked
        return True, checked

    def set_xml(self, xml):
        self.clear()
        source = QtXml.QXmlInputSource()
        source.setData(xml)
        handler = XmlHandler(self)
        reader = QtXml.QXmlSimpleReader()
        reader.setContentHandler(handler)
        reader.setErrorHandler(handler)
        reader.parse(source)


def check_url(url):
    try:
        url = get_ranges_url(url)[0]
        thread = ThreadWithReturnValue(target=requests.get, args=(url,))
        thread.daemon = True
        thread.start()
        r = thread.join(10)
        if r:
            return url
        else:
            return False
    except Exception as e:
        return False


def get_links(url, path):
    tree = sitemap_tree_for_homepage(url)
    with open(path, "w") as w:
        for i in tree.all_pages():
            w.write(i.url + '\n')


def make_tree(links_path, res_path):
    with open(links_path, "r") as r:
        links = list(set(filter(lambda x: x, r.read().split("\n"))))
    if links:
        base = re.findall(r".*?//(.*?)/", links[0])[0]
        http = links[0].split("//")[0]
        links = sorted(map(lambda x: x.lower().split("//")[-1].replace(base + "/", "")
                           .rstrip("/").split("/"), links), key=lambda y: len(y))
        root = ET.Element("site")
        root.set('url', http + "//" + base)
        elements = {}
        for link in links:
            for ind, i in enumerate(link):
                now = "/".join(link[:ind + 1])
                if (ind == 0) and (now not in elements.keys()):
                    elements[i] = ET.SubElement(root, "category")
                    elements[i + "_links"] = ET.SubElement(elements[i], "links")
                    elements[i].set('name', i)
                    elements[i].set('checked', 'True')
                    elements[i + "_links"].set('checked', 'True')
                elif (ind == (len(link) - 1)) and (now not in elements.keys()):
                    new = ET.SubElement(elements["/".join(link[:ind]) + "_links"], 'link')
                    url = http + "//" + "/".join([base] + link)
                    new.text = url
                    elements[url] = new
                elif now not in elements.keys():
                    p = "/".join(link[:ind])
                    elements[now] = ET.SubElement(elements[p], "subcategory")
                    elements[now + "_links"] = ET.SubElement(elements[now], "links")
                    elements[now].set('name', i)
                    elements[now].set('checked', 'True')
                    elements[now + "_links"].set('checked', 'True')
        tree = ET.ElementTree(root)
        tree.write(res_path)
        with open(res_path, mode="r") as r:
            res = r.read()
        with open(res_path, mode="w") as w:
            w.write(re.sub(
                r'<category checked="(True|False)" name="([-_\w\d]*)"><links checked="(True|False)"'
                r' /></category>',
                '', res))
    else:
        with open(res_path, mode="w") as w:
            w.write()


def make_small_tree(tree_path, res_path=None):
    import re
    t = open(tree_path, "r").read()
    tree_path = tree_path.rsplit('.', 1)
    if not res_path:
        res_path = tree_path[0] + "_small." + tree_path[1]
    open(res_path, "w").write(re.sub(
        r'<links checked="(.*?)">((<link>[^<]+<\/link>){1,5})((<link>[^<]+<\/link>)+)<\/links>',
        r'<links checked="\1">\2</links>', t))


def fetch_site(url, id, path):
    site_path = path + "/" + url.split("//")[1].split('/')[0]
    get_links(url, site_path + ".txt")
    make_tree(site_path + ".txt", site_path + ".xml")
    make_small_tree(site_path + ".xml", site_path + "_" + str(id) + "_small.xml")


def get_sitemaps_paths(url, id, start=""):
    if not url:
        return start + "/" + str(id) + ".xml", start + "/" + str(id) + "_small.xml"
    site_path = start + "/" + url.split("//")[1].split('/')[0]
    return site_path + ".xml", site_path + "_" + str(id) + "_small.xml"


def fetch_sitemaps_links(res, id_p):
    res = res.split(";")
    mask = res[1] if res[1] else ".*"
    paths = get_sitemaps_paths(res[0], id_p, "./sitemaps")
    all = etree.parse(paths[0])
    small = etree.parse(paths[1])
    find = './/links[@checked="True"]'
    not_find = './/links[@checked="False"]'
    between = small.findall(find)
    not_between = small.findall(not_find)
    print("find")
    if not between:
        return []
    if len(not_between) > len(between):
        return list(filter(lambda z: re.fullmatch(mask, z),
                           map(lambda x: x.text, reduce(lambda g, h: g + h,
                                                        map(lambda y: all.findall(
                                                            small.getpath(y).split('/', 2)[
                                                                2] + "/link"),
                                                            between))))
                    )
    else:
        with open("./sitemaps/avito.ru.txt", mode="r") as r:
            links = set(r.read().split("\n"))
        if not not_between:
            return list(links)
        return list(links - set(filter(lambda z: re.fullmatch(mask, z),
                       map(lambda x: x.text, reduce(lambda g, h: g + h,
                                                    map(lambda y: all.findall(
                                                        small.getpath(y).split('/', 2)[
                                                            2] + "/link"),
                                                        not_between))))
                ))

        return list(links)
    return []


def get_ranges_url(url, single=False):
    var = re.findall(r'{(?:.*?)*}', url, )
    ranges = [i[1:-1].split(';') for i in var]
    if ranges:
        for i in range(len(ranges)):
            if (len(ranges[i]) == 2) and ranges[i][0].isdigit() and ranges[i][1].isdigit():
                ranges[i] = tuple(map(str, range(int(ranges[i][0]), int(ranges[i][1]) + 1)))
            else:
                ranges[i] = tuple([j.strip() for j in ranges[i]])
        if single:
            return ultra_replace(var[0], ranges[0], url)
        else:
            return [ultra_replace(var, i, url) for i in product(*ranges)]
    return [url]


def ultra_replace(keys, attrs, replacement):
    for i in zip(keys, attrs):
        replacement = replacement.replace(*i)
    return replacement


class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,
                                        **self._kwargs)

    def join(self, *args):
        Thread.join(self, *args)
        return self._return
