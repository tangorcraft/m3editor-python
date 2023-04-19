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
from PyQt5.QtWidgets import QMessageBox as mb, QFileDialog as fd
from Ui_editorWindow import Ui_m3ew
from configparser import ConfigParser
from m3file import m3File
from m3struct import m3StructFile, m3FieldInfo
from uiTreeView import TagTreeModel, fieldsTableModel, ShadowItem
from editors.simpleFieldEdit import SimpleFieldEdit
from editors.flagsFieldEdit import FlagsFieldEdit
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
        self.font().setStyleHint(QtGui.QFont.StyleHint.Monospace, QtGui.QFont.StyleStrategy.PreferDefault)

        ### Tree View ###

        self.tagsModel = TagTreeModel()
        self.ui.tagsTree.setModel(self.tagsModel)
        self.ui.tagsTree.selectionModel().currentChanged.connect(self.tagTreeClick)
        self.resetItemNaviText('##')

        self.simpleEditor = SimpleFieldEdit(self)
        self.flagEditor = FlagsFieldEdit(self)

        self.fieldsModel = fieldsTableModel()
        self.fieldsModel.modelReset.connect(self.fieldsModelReset)
        self.fieldsModel.dataChanged.connect(lambda a,b: self.fieldsDataChanged())
        self.fieldsFilterModel = QSortFilterProxyModel()
        self.fieldsFilterModel.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.fieldsFilterModel.setFilterRole(Qt.ItemDataRole.StatusTipRole)
        self.fieldsFilterModel.setRecursiveFilteringEnabled(True)
        self.fieldsFilterModel.setSourceModel(self.fieldsModel)
        self.ui.fieldsTable.setModel(self.fieldsFilterModel)
        #self.ui.fieldsTable.setModel(self.fieldsModel)

        self.ui.fieldsTable.clicked.connect(lambda x: self.ui.fieldsTable.expand(x))
        self.ui.fieldsTable.doubleClicked.connect(self.fieldDoubleClick)
        self.ui.fieldsTable.selectionModel().currentChanged.connect(lambda a,b: self.ui.textFieldHint.setText(a.data(fieldsTableModel.FullFieldHintRole)))
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

        ### 3d View ###

        self.ui.split3dViewH.setCollapsible(0, False)
        self.ui.tree3dView.setModel(self.ui.gl3dView.mtree)
        self.ui.gl3dView.mtree.modelReset.connect(self.ui.tree3dView.expandAll)
        self.glTimer = QTimer(self)
        self.glTimer.timeout.connect(self.ui.gl3dView.update)
        self.glTimer.start(1000)
        self.ui.slideLightMin.valueChanged.connect(lambda x: self.ui.gl3dView.setLightMin(x / 100))
        self.ui.slideLightPow.valueChanged.connect(lambda x: self.ui.gl3dView.setLightPow(x / 100))

        ### Menu ###

        self.ui.actionOpen.triggered.connect(self.openM3)
        self.ui.actionReopen.triggered.connect(self.reopenM3)
        self.ui.actionSave.triggered.connect(self.saveM3)
        self.ui.actionSave_as.triggered.connect(self.saveM3as)

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

    def fieldsDataChanged(self):
        self.resetItemNaviText(self.fieldsModel.getTagItemIndexStr())
        self.fieldsFilterModel.dataChanged.emit(QModelIndex(), QModelIndex())

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
                    mb.warning(self, 'Item not found', f'Item with index "{val}" is not found')
            except ValueError:
                self.resetItemNaviText()
                mb.critical(self, 'Ivalid input', f'"{text}" is not a valid integer value')

    def treeTagSelected(self, tag, item = -1):
        self.fieldsModel.setM3Tag(tag, item)

    def fieldsModelReset(self):
        self.resetItemNaviText(self.fieldsModel.getTagItemIndexStr())
        self.ui.edtItemNavi.setReadOnly(not self.fieldsModel.isBaseTag)
        self.ui.btnItemBack.setEnabled(self.fieldsModel.isBaseTag)
        self.ui.btnItemForw.setEnabled(self.fieldsModel.isBaseTag)

    def editSimpleValue(self, tag, item, f: m3FieldInfo):
        skip_to_flags = True if f.bits else False
        while True:
            if skip_to_flags:
                skip_to_flags = False
            else:
                if self.simpleEditor.editValue(tag, item, f): break
            if self.flagEditor.editValue(tag, item, f): break

    ## EVENTS ##

    def fieldDoubleClick(self, index: QModelIndex):
        tag = self.fieldsModel.tag
        if index.isValid() and tag:
            f = index.data(fieldsTableModel.FieldRole) # type: m3FieldInfo
            if self.fieldsModel.binaryView:
                pass
            elif tag.info.simple:
                item = self.fieldsModel.item_offset + index.row()
                self.editSimpleValue(tag, item, f)
            elif tag.isStr():
                val = tag.getStr()
                val, ok = QtWidgets.QInputDialog.getText(self, f'Edit CHAR#{tag.idx}', 'Input new CHAR value', text=val)
                if ok: tag.setStr(val)
            else:
                if f.simple():
                    self.editSimpleValue(self.fieldsModel.tag, self.fieldsModel.tag_item, f)
        self.fieldsModel.dataChanged.emit(QModelIndex(), QModelIndex())

    def tagTreeClick(self, item: QModelIndex, old_item: QModelIndex):
        if item.isValid():
            shadow = item.data(TagTreeModel.TagTreeShadowRole) # type: ShadowItem
            if shadow.tag:
                self.treeTagSelected(shadow.tag, shadow.tag_item)
                if self.ui.actionFields_Auto_Expand_All.isChecked():
                    self.ui.fieldsTable.expandAll()

    def openM3(self):
        fname, filter = fd.getOpenFileName(self, 'Open m3 model', self.lastFile, "M3 Model (*.m3 *.m3a)")
        if os.path.exists(fname):
            self.lastFile =  fname
            self.m3 = m3File(fname, self.struct)
            self.tagsModel.changeM3(self.m3)
            self.treeTagSelected(self.m3.modl)
            self.ui.gl3dView.setM3(self.m3)
            self.setWindowTitle(f'M3 Editor - {fname}')
            self.ui.actionReopen.setEnabled(True)
            self.ui.actionSave.setEnabled(True)
            self.ui.actionSave_as.setEnabled(True)
            self.confirmSave = True

    def reopenM3(self):
        self.m3.reloadFromData()

    def saveM3(self):
        if self.confirmSave and os.path.exists(self.lastFile):
            btns = mb.StandardButton.Yes | mb.StandardButton.No | mb.StandardButton.Cancel
            ret = mb.question(self, 'Save file', f'Replace file "{self.lastFile}"?', btns, mb.StandardButton.Yes)
            if ret == mb.StandardButton.Cancel:
                return
            if ret == mb.StandardButton.No:
                self.saveM3as()
                return
        self.m3.repackIntoData()
        with open(self.lastFile, 'wb') as file:
            file.write(self.m3.data)
            file.close()

    def saveM3as(self):
        fname, filter = fd.getSaveFileName(self, 'Save m3 model', self.lastFile, "M3 Model (*.m3);;M3 Model Animations (*.m3a)")
        if os.path.exists(fname):
            btns = mb.StandardButton.Yes | mb.StandardButton.No
            if mb.question(self, 'Save file', f'Replace file "{fname}"?', btns, mb.StandardButton.Yes) == mb.StandardButton.No:
                return
        self.confirmSave = False
        self.lastFile = fname
        self.setWindowTitle(f'M3 Editor - {fname}')
        self.saveM3()

    def closeEvent(self, ev: QtGui.QCloseEvent) -> None:
        self.saveIni()
        ev.accept()

if __name__ == '__main__':
    fmt = QtGui.QSurfaceFormat()
    fmt.setDepthBufferSize(24)
    fmt.setStencilBufferSize(8)
    fmt.setVersion(3,3)
    fmt.setProfile(QtGui.QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    QtGui.QSurfaceFormat.setDefaultFormat(fmt)
    app = QtWidgets.QApplication([])
    appWin = mainWin()
    #app.installEventFilter(appWin)
    appWin.show()

    sys.exit(app.exec())
