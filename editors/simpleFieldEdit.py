from typing import List, Callable
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import *
from editors.Ui_simpleEditDialog import Ui_Dialog
from m3file import m3File, m3Tag
from m3struct import m3FieldInfo, m3Type
from struct import pack, pack_into, unpack, error as struct_error

RESULT_CANCEL = QtWidgets.QDialog.Rejected
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
        self.setValue(self.init_value)
        return self.exec()

    def editValue(self, tag: m3Tag, item: int, field: m3FieldInfo) -> bool:
        if field.type in m3Type.SIMPLE:
            self.floatDisplay = field.type in m3Type.REAL
            self.val_size = field.size
            self.init_value = tag.getFieldValue(item, field)
            self.val_format = m3Type.toFormat(field.type)
            self.hex_format = m3Type.toHexFormat(field.type)
            self.sign_format = m3Type.toSignFormat(field.type)
            ret = self.showEditor()
            if ret == RESULT_OK and self.value != self.init_value:
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
                    val = float(val)
                elif sender == self.ui.edtSigned:
                    val = int(self.ui.edtSigned.text())
                elif sender == self.ui.edtUnsigned:
                    val = abs(int(self.ui.edtUnsigned.text()))
                pack(self.val_format, val) # test if value can be packed into right format
                self.value = val
        except (ValueError, struct_error) as e:
            self.ui.label.setText(e.args[0])
        else:
            self.ui.label.setText('')
        self.displayValue(sender)

    def displayValue(self, sender = None):
        if self.floatDisplay:
            if sender != self.ui.edtSigned:
                self.ui.edtSigned.setText(f'{self.value}')
            if sender != self.ui.edtUnsigned:
                self.ui.edtUnsigned.setText(f'{self.value:e}')
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
