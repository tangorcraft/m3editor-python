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
        self.font().setStyleHint(QtGui.QFont.Monospace, QtGui.QFont.PreferDefault)

        self.tagsModel = TagTreeModel()
        self.ui.tagsTree.setModel(self.tagsModel)
        self.ui.tagsTree.clicked.connect(self.tagTreeClick)
        self.resetItemNaviText('##')

        self.fieldsModel = fieldsTableModel()
        self.fieldsModel.modelReset.connect(self.fieldsModelReset)
        self.fieldsFilterModel = QSortFilterProxyModel()
        self.fieldsFilterModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.fieldsFilterModel.setFilterRole(Qt.StatusTipRole)
        self.fieldsFilterModel.setRecursiveFilteringEnabled(True)
        self.fieldsFilterModel.setSourceModel(self.fieldsModel)
        self.ui.fieldsTable.setModel(self.fieldsFilterModel)
        #self.ui.fieldsTable.setModel(self.fieldsModel)

        self.ui.fieldsTable.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.ui.fieldsTable.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.ui.fieldsTable.header().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.ui.fieldsTable.header().setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)

        self.acton_SimpleDisplayCountGroup = QtWidgets.QActionGroup(self)
        self.acton_SimpleDisplayCountGroup.addAction(self.ui.actionSimpleDisplayCount50)
        self.acton_SimpleDisplayCountGroup.addAction(self.ui.actionSimpleDisplayCount100)
        self.acton_SimpleDisplayCountGroup.addAction(self.ui.actionSimpleDisplayCount200)
        self.acton_SimpleDisplayCountGroup.addAction(self.ui.actionSimpleDisplayCount500)
        self.ui.actionSimpleDisplayCount50.triggered.connect(lambda x: self.setSDC(x, 50))
        self.ui.actionSimpleDisplayCount100.triggered.connect(lambda x: self.setSDC(x, 100))
        self.ui.actionSimpleDisplayCount200.triggered.connect(lambda x: self.setSDC(x, 200))
        self.ui.actionSimpleDisplayCount500.triggered.connect(lambda x: self.setSDC(x, 500))

        self.ui.btnShowBinary.clicked.connect(lambda x: self.fieldsModel.setBinaryView(x))
        self.ui.btnItemBack.clicked.connect(lambda x: self.fieldsModel.stepItemOffset(-1))
        self.ui.btnItemForw.clicked.connect(lambda x: self.fieldsModel.stepItemOffset(1))
        self.ui.edtItemNavi.editingFinished.connect(self.itemNaviEdited)
        self.ui.edtItemFilter.textEdited.connect(self.fieldsFilterModel.setFilterFixedString)

        self.ui.actionOpen.triggered.connect(self.openM3)

    def setIniOption(self, sect, opt, val, saveINI = False):
        if not sect in self.cfg:
            self.cfg[sect] = {}
        self.cfg[sect][opt] = str(val)
        if saveINI: self.saveIni()

    def saveIni(self):
        with open('options.ini','w') as cfgFile:
            self.cfg.write(cfgFile)

    def resetItemNaviText(self, new_text = None):
        if new_text:
            self.itemNaviText = new_text
        self.ui.edtItemNavi.setText(self.itemNaviText)

    ## SLOTS ##

    def setSDC(self, checked, value):
        if checked:
            self.fieldsModel.setSimpleFieldsDisplayCount(value)

    def itemNaviEdited(self):
        text = self.ui.edtItemNavi.text()
        if self.fieldsModel.tag and text != self.itemNaviText:
            try:
                val = int(text)
                if self.fieldsModel.navigate(val):
                    return
                else:
                    self.resetItemNaviText()
                    QtWidgets.QMessageBox.warning(self, 'Item not found', f'Item with index "{val}" is not found')
            except ValueError:
                self.resetItemNaviText()
                QtWidgets.QMessageBox.critical(self, 'Ivalid input', f'"{text}" is not a valid integer value')

    def treeTagSelected(self, tag, item = -1):
        self.fieldsModel.setM3Tag(tag, item)

    def fieldsModelReset(self):
        self.resetItemNaviText(self.fieldsModel.getTagItemIndexStr())
        self.ui.edtItemNavi.setReadOnly(not self.fieldsModel.isBaseTag)
        self.ui.btnItemBack.setEnabled(self.fieldsModel.isBaseTag)
        self.ui.btnItemForw.setEnabled(self.fieldsModel.isBaseTag)

    ## EVENTS ##

    def tagTreeClick(self, item: QModelIndex):
        if item.isValid():
            shadow = item.data(Qt.UserRole) # type: ShadowItem
            if shadow.tag:
                self.treeTagSelected(shadow.tag, shadow.tag_item)

    def openM3(self):
        fname, filter = QtWidgets.QFileDialog.getOpenFileName(self, 'Open m3 model', self.lastFile, "M3 Model (*.m3 *.m3a)")
        if os.path.exists(fname):
            self.lastFile =  fname
            self.m3 = m3File(fname, self.struct)
            self.tagsModel.changeM3(self.m3)
            self.treeTagSelected(self.m3.modl)

    def closeEvent(self, ev: QtGui.QCloseEvent) -> None:
        self.saveIni()
        ev.accept()

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    appWin = mainWin()
    #app.installEventFilter(appWin)
    appWin.show()

    sys.exit(app.exec())
