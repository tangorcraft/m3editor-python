from typing import List, Callable
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import *
from Ui_editorWindow import Ui_m3ew
from configparser import ConfigParser
from m3file import m3File
from m3struct import m3StructFile
from uiTreeView import TagTreeModel, fieldsTableModel, ShadowItem
import sys, os, requests

class mainWin(QtWidgets.QMainWindow):

    def __init__(self):
        super(mainWin, self).__init__()

        self.cfg = ConfigParser()
        self.cfg.read('options.ini')
        self.struct = m3StructFile()
        self.struct.loadFromFile('structures.xml')
        self.lastFile = ''

        self.ui = Ui_m3ew()
        self.ui.setupUi(self)

        self.tagsModel = TagTreeModel()
        self.ui.tagsTree.setModel(self.tagsModel)
        self.ui.tagsTree.clicked.connect(self.tagTreeClick)

        self.fieldsModel = fieldsTableModel()
        self.ui.fieldsTable.setModel(self.fieldsModel)

        self.ui.actionOpen.triggered.connect(self.openM3)

    def setIniOption(self, sect, opt, val, saveINI = False):
        if not sect in self.cfg:
            self.cfg[sect] = {}
        self.cfg[sect][opt] = str(val)
        if saveINI: self.saveIni()

    def saveIni(self):
        with open('options.ini','w') as cfgFile:
            self.cfg.write(cfgFile)

    def eventFilter(self, obj: 'QObject', ev: 'QEvent') -> bool:
        return super().eventFilter(obj, ev)

    ## EVENTS ##

    def tagTreeClick(self, item: QModelIndex):
        if item.isValid():
            shadow = item.data(Qt.UserRole) # type: ShadowItem
            if shadow.tag:
                tag_item = shadow.tag_item if shadow.tag_item in range(0, shadow.tag.count) else 0
                self.fieldsModel.setFields(shadow.tag, tag_item)

    def openM3(self):
        fname, filter = QtWidgets.QFileDialog.getOpenFileName(self, 'Open m3 model',self.lastFile,"M3 Model (*.m3)")
        if os.path.exists(fname):
            self.lastFile =  fname
            self.m3 = m3File(fname, self.struct)
            self.tagsModel.changeM3(self.m3)

    def closeEvent(self, ev: QtGui.QCloseEvent) -> None:
        self.saveIni()
        ev.accept()


app = QtWidgets.QApplication([])
appWin = mainWin()
app.installEventFilter(appWin)
appWin.show()

sys.exit(app.exec())
