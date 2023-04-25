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
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import *
from m3file import m3Tag, SIZE_TO_FORMAT
from m3struct import m3FieldInfo, m3Type
from editors.fieldHandlers import registerFieldHandlerClass, AbstractFieldHandler
from struct import pack_into, unpack_from
from common import options

YES_NO_CANCEL = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel

class flag_bits_handler(AbstractFieldHandler):
    def __init__(self, parent):
        self.parent = parent

    def editField(self, tag: m3Tag, item: int, field: m3FieldInfo):
        if field.size in SIZE_TO_FORMAT:
            fmt = SIZE_TO_FORMAT[field.size]
        else:
            return
        offset = field.getDataOffset(item)
        val = unpack_from(fmt, tag.data, offset)[0]
        if options.getOptionBool(options.OPT_CONFIRM_BIT_EDIT, True):
            ret = QMessageBox.question(self.parent, 'Edit flag bit', 'Yes = enable flag bit(s), No = disable flag bit(s)', YES_NO_CANCEL)
            if ret == QMessageBox.StandardButton.Cancel:
                return
            enable = (ret == QMessageBox.StandardButton.Yes)
        else:
            enable = not (val & field.bitMask == field.bitMask)
        if enable:
            val = val | field.bitMask
        else:
            max_bit = field.size * 8
            mask = 2**max_bit - 1 - field.bitMask
            val = val & mask
        pack_into(fmt, tag.data, offset, val)

    def fieldData(self, role: Qt.ItemDataRole, tag: m3Tag, item: int, field: m3FieldInfo):
        if role == Qt.ItemDataRole.CheckStateRole:
            return Qt.CheckState.Checked if tag.checkBitState(item, field) else Qt.CheckState.Unchecked
        elif role == Qt.ItemDataRole.DisplayRole:
            return tag.getFieldAsStr(item, field)

registerFieldHandlerClass(m3Type.FLAGS_BIT_NAME, flag_bits_handler)
