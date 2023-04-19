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
from editors.Ui_simpleEditDialog import Ui_Dialog
from m3file import m3File, m3Tag
from m3struct import m3FieldInfo, m3Type
from struct import pack, pack_into, unpack, error as struct_error
from common import fixed8_to_float, fixed16_to_float, float_to_fixed8, float_to_fixed16

RESULT_CANCEL = QtWidgets.QDialog.DialogCode.Rejected
RESULT_OK = RESULT_CANCEL + 1
RESULT_CONTINUE = RESULT_CANCEL + 2

class SimpleFieldEdit(QtWidgets.QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.btnOK.clicked.connect(self.okClick)
        self.ui.btnCancel.clicked.connect(self.cancelClick)
        self.ui.btnReset.clicked.connect(self.resetClick)
        self.ui.btnFlags.clicked.connect(self.asFlagsClick)

        self.ui.edtSigned.textEdited.connect(lambda s: self.setValue(s, self.ui.edtSigned))
        self.ui.edtUnsigned.textEdited.connect(lambda s: self.setValue(s, self.ui.edtUnsigned))
        self.ui.edtHex.textEdited.connect(lambda s: self.setValue(s, self.ui.edtHex))

        self.floatDisplay = False

    def showEditor(self):
        self.ui.edtUnsigned.setReadOnly(self.floatDisplay)
        if self.floatDisplay:
            self.ui.lblSigned.setText('Value:')
            self.ui.lblUnsigned.setText('Scientific:')
        else:
            self.ui.lblSigned.setText('Signed:')
            self.ui.lblUnsigned.setText('Unsigned:')
        self.displayValue()
        return self.exec()

    def editValue(self, tag: m3Tag, item: int, field: m3FieldInfo) -> bool:
        if field.type in m3Type.SIMPLE:
            self.floatDisplay = field.type in m3Type.REAL
            if field.type == m3Type.FIXED8:
                self.float_convert = fixed8_to_float
                self.float_convert_back = float_to_fixed8
            elif field.type == m3Type.FIXED16:
                self.float_convert = fixed16_to_float
                self.float_convert_back = float_to_fixed16
            else:
                self.float_convert = lambda x: x
                self.float_convert_back = lambda x: x
            self.val_size = field.size
            self.init_value = tag.getFieldValue(item, field)
            self.value = self.init_value
            self.val_format = m3Type.toFormat(field.type)
            self.hex_format = m3Type.toHexFormat(field.type)
            self.sign_format = m3Type.toSignFormat(field.type)
            ret = self.showEditor()
            if ret == RESULT_OK:
                if self.value != self.init_value:
                    offset = tag.info.item_size * item + field.offset
                    pack_into(self.val_format, tag.data, offset, self.value)
                return True
            if ret == RESULT_CANCEL:
                return True # editing is finished even if it got canceled
            return False # "As Flags" clicked, editing should continue with different dialog

    def setValue(self, val, sender = None):
        try:
            if sender == self.ui.edtHex:
                val = int(val, 16)
                self.value = unpack(self.val_format, pack(self.hex_format, val))
            else:
                if self.floatDisplay:
                    val = self.float_convert_back(float(val))
                elif sender == self.ui.edtSigned:
                    val = int(val)
                elif sender == self.ui.edtUnsigned:
                    val = abs(int(val))
                pack(self.val_format, val) # test if value can be packed into right format
                self.value = val
        except (ValueError, struct_error) as e:
            self.ui.label.setText(e.args[0])
        else:
            self.ui.label.setText('')
        self.displayValue(sender)

    def displayValue(self, sender = None):
        if self.floatDisplay:
            val = self.float_convert(self.value)
            if sender != self.ui.edtSigned:
                self.ui.edtSigned.setText(f'{val}')
            if sender != self.ui.edtUnsigned:
                self.ui.edtUnsigned.setText(f'{val:e}')
        else:
            if sender != self.ui.edtSigned:
                self.ui.edtSigned.setText(f'{self.signValue()}')
            if sender != self.ui.edtUnsigned:
                self.ui.edtUnsigned.setText(f'{self.hexValue()}')
        if sender != self.ui.edtHex:
            self.ui.edtHex.setText(f'{self.hexValue():0{self.val_size*2}x}')

    def hexValue(self):
        if self.val_format==self.hex_format: return self.value
        return unpack(self.hex_format, pack(self.val_format, self.value))[0]

    def signValue(self):
        if self.val_format==self.sign_format: return self.value
        return unpack(self.sign_format, pack(self.val_format, self.value))[0]

    def okClick(self):
        self.done(RESULT_OK)

    def cancelClick(self):
        self.done(RESULT_CANCEL)

    def resetClick(self):
        self.value = self.init_value
        self.displayValue()

    def asFlagsClick(self):
        self.done(RESULT_CONTINUE)
