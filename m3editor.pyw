# This file is a part of "M3 Editor, python variant" project <https://github.com/tangorcraft/m3editor-python/>.
# Copyright (C) 2023  Ivan Markov (TangorCraft)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
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
        self.ui.fieldsTable.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.ui.fieldsTable.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.ui.fieldsTable.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.ui.fieldsTable.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)

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
                self.fieldsModel.setM3Tag(shadow.tag, tag_item)

    def openM3(self):
        fname, filter = QtWidgets.QFileDialog.getOpenFileName(self, 'Open m3 model',self.lastFile,"M3 Model (*.m3)")
        if os.path.exists(fname):
            self.lastFile =  fname
            self.m3 = m3File(fname, self.struct)
            self.tagsModel.changeM3(self.m3)

    def closeEvent(self, ev: QtGui.QCloseEvent) -> None:
        self.saveIni()
        ev.accept()

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    appWin = mainWin()
    app.installEventFilter(appWin)
    appWin.show()

    sys.exit(app.exec())
