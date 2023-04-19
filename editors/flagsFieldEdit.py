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
from PyQt5 import QtWidgets
from PyQt5.QtCore import *
from editors.Ui_flagsEditDialog import Ui_Dialog
from m3file import m3Tag
from m3struct import m3FieldInfo, m3Type
from struct import pack_into

RESULT_CANCEL = QtWidgets.QDialog.DialogCode.Rejected
RESULT_OK = RESULT_CANCEL + 1
RESULT_CONTINUE = RESULT_CANCEL + 2

class FlagsFieldEdit(QtWidgets.QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.btnOk.clicked.connect(self.okClick)
        self.ui.btnCancel.clicked.connect(self.cancelClick)
        self.ui.btnReset.clicked.connect(self.resetClick)
        self.ui.btnAsInteger.clicked.connect(self.asIntClick)

        self.bit_update = False
        self.bits = [
            self.ui.cbBit_1, self.ui.cbBit_2, self.ui.cbBit_3, self.ui.cbBit_4,
            self.ui.cbBit_5, self.ui.cbBit_6, self.ui.cbBit_7, self.ui.cbBit_8,
            self.ui.cbBit_9, self.ui.cbBit_10, self.ui.cbBit_11, self.ui.cbBit_12,
            self.ui.cbBit_13, self.ui.cbBit_14, self.ui.cbBit_15, self.ui.cbBit_16,
            self.ui.cbBit_17, self.ui.cbBit_18, self.ui.cbBit_19, self.ui.cbBit_20,
            self.ui.cbBit_21, self.ui.cbBit_22, self.ui.cbBit_23, self.ui.cbBit_24,
            self.ui.cbBit_25, self.ui.cbBit_26, self.ui.cbBit_27, self.ui.cbBit_28,
            self.ui.cbBit_29, self.ui.cbBit_30, self.ui.cbBit_31, self.ui.cbBit_32,
        ]
        for idx in range(0,32):
            self.bits[idx].stateChanged.connect((lambda i: lambda x: self.setBit(x, i))(idx))

    def showEditor(self, bits):
        self.bit_update = True
        for idx in range(0,32):
            if idx < self.max_bit:
                self.bits[idx].setEnabled(True)
                self.bits[idx].setCheckState(self.getBitState(idx))
                bit = 1 << idx
                text = f'0x{bit:{self.str_format}}'
                for name in bits:
                    if bits[name] & bit == bit:
                        text += f' ({name})'
                self.bits[idx].setText(text)
            else:
                self.bits[idx].setEnabled(False)
                self.bits[idx].setCheckState(Qt.CheckState.Unchecked)
                self.bits[idx].setText('None')
        self.bit_update = False
        self.ui.lblInitVal.setText(f'Initial value: 0x{self.init_value:{self.str_format}}')
        self.ui.lblCurVal.setText(f'Current value: 0x{self.value:{self.str_format}}')
        return self.exec()

    def editValue(self, tag: m3Tag, item: int, field: m3FieldInfo) -> bool:
        if field.type in m3Type.SIMPLE:
            self.max_bit = field.size * 8
            self.val_size = field.size
            self.str_format = f'0{self.val_size*2}x'
            self.hex_format = m3Type.toHexFormat(field.type)
            self.init_value = tag.getFieldUnpacked(item, field, self.hex_format)[0]
            self.value = self.init_value
            ret = self.showEditor(field.bits)
            if ret == RESULT_OK:
                if self.value != self.init_value:
                    offset = tag.info.item_size * item + field.offset
                    pack_into(self.hex_format, tag.data, offset, self.value)
                return True
            if ret == RESULT_CANCEL:
                return True # editing is finished even if it got canceled
            return False # "As Int" clicked, editing should continue with different dialog

    def getBitState(self, idx: int):
        bit = 1 << idx
        return Qt.CheckState.Checked if self.value & bit == bit else Qt.CheckState.Unchecked

    def setBit(self, val, idx = None):
        if self.bit_update: return
        bit = 1 << idx
        if val == Qt.CheckState.Checked:
            self.value = self.value | bit
        elif val == Qt.CheckState.Unchecked:
            mask = 2**self.max_bit - 1 - bit
            self.value = self.value & mask
        self.displayValue(idx)

    def displayValue(self, idx = None):
        self.bit_update = True
        if idx == None:
            for idx in range(0, self.max_bit):
                self.bits[idx].setCheckState(self.getBitState(idx))
        self.bit_update = False
        self.ui.lblCurVal.setText(f'Current value: 0x{self.value:{self.str_format}}')

    def okClick(self):
        self.done(RESULT_OK)

    def cancelClick(self):
        self.done(RESULT_CANCEL)

    def resetClick(self):
        self.value = self.init_value
        self.displayValue()

    def asIntClick(self):
        self.done(RESULT_CONTINUE)
