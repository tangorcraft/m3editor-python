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
from PyQt5.QtWidgets import QDialog, QColorDialog
from PyQt5.QtGui import QColor, QPixmap, QPainter
from PyQt5.QtCore import *
from .Ui_color_dialog import Ui_Dialog
from m3file import m3Tag
from m3struct import m3FieldInfo, m3Type
from editors.fieldHandlers import registerFieldHandlerClass, AbstractFieldHandler
from struct import pack_into
from common import clampf, clampi
import m3, colorsys

def convert_COL(b,g,r,a):
    return [r/255.0, g/255.0, b/255.0, a/255.0]

def convert_COL_back(r, g, b, a):
    return [
        clampi(round(b*255),0,255),
        clampi(round(g*255),0,255),
        clampi(round(r*255),0,255),
        clampi(round(a*255),0,255)
    ]

def convert_VEC3(r, g, b):
    return [
        clampf(r, 0.0, 1.0),
        clampf(g, 0.0, 1.0),
        clampf(b, 0.0, 1.0),
        1.0
    ]

IDX_R = 0
IDX_G = 1
IDX_B = 2
IDX_A = 3
IDX_H = 4
IDX_L = 5
IDX_S = 6
SLIDER_MAX = 0x7FFF
SPINEDIT_MAX = 255.0

class ColorFieldEdit(QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.px_init_val = QPixmap(100, 100)
        self.px_cur_val = QPixmap(100, 100)
        self.painter = QPainter()

        self.ui.btnOk.clicked.connect(self.okClick)
        self.ui.btnCancel.clicked.connect(self.cancelClick)
        self.ui.btnReset.clicked.connect(self.resetClick)
        self.ui.btnPickColor.clicked.connect(self.pickColorClick)

        self.spins = [
            self.ui.edtR, self.ui.edtG, self.ui.edtB, self.ui.edtA,
            self.ui.edtH, self.ui.edtL, self.ui.edtS
        ]
        self.sliders = [
            self.ui.sliderR, self.ui.sliderG, self.ui.sliderB, self.ui.sliderA,
            self.ui.sliderH, self.ui.sliderL, self.ui.sliderS
        ]
        self.ui.edtR.valueChanged.connect(lambda x: self.setRGB_spin(IDX_R, x))
        self.ui.edtG.valueChanged.connect(lambda x: self.setRGB_spin(IDX_G, x))
        self.ui.edtB.valueChanged.connect(lambda x: self.setRGB_spin(IDX_B, x))
        self.ui.edtA.valueChanged.connect(lambda x: self.setA_spin(IDX_A, x))

        self.ui.edtH.valueChanged.connect(lambda x: self.setHLS_spin(IDX_H, x))
        self.ui.edtL.valueChanged.connect(lambda x: self.setHLS_spin(IDX_L, x))
        self.ui.edtS.valueChanged.connect(lambda x: self.setHLS_spin(IDX_S, x))

        self.ui.sliderR.valueChanged.connect(lambda x: self.setRGB_slider(IDX_R, x))
        self.ui.sliderG.valueChanged.connect(lambda x: self.setRGB_slider(IDX_G, x))
        self.ui.sliderB.valueChanged.connect(lambda x: self.setRGB_slider(IDX_B, x))
        self.ui.sliderA.valueChanged.connect(lambda x: self.setA_slider(IDX_A, x))

        self.ui.sliderH.valueChanged.connect(lambda x: self.setHLS_slider(IDX_H, x))
        self.ui.sliderL.valueChanged.connect(lambda x: self.setHLS_slider(IDX_L, x))
        self.ui.sliderS.valueChanged.connect(lambda x: self.setHLS_slider(IDX_S, x))

        self.updating = False

    def showEditor(self):
        self.px_init_val.fill(QColor.fromRgbF(*self.init_value))
        if self.painter.begin(self.px_init_val):
            try:
                self.painter.fillRect(20,20,60,60,QColor.fromRgbF(*self.init_value[:3], 1.0))
            finally:
                self.painter.end()
        self.ui.lblInitVal.setPixmap(self.px_init_val)
        self.updateAll()
        return self.exec()

    def editValue(self, tag: m3Tag, item: int, field: m3FieldInfo):
        if field.type_name == m3.COL.self__:
            val = tag.getFieldUnpacked(item, field, '<BBBB') # BGRA
            self.init_value = convert_COL(*val)
            self.ui.frameA.setEnabled(True)
        elif field.type_name == m3.VEC3.self__:
            val = tag.getFieldUnpacked(item, field, '<fff') # RGB
            self.init_value = convert_VEC3(*val)
            self.ui.frameA.setEnabled(False)
        else:
            return
        self.value = self.init_value.copy()
        if self.showEditor():
            offset = tag.info.item_size * item + field.offset
            if field.type_name == m3.COL.self__:
                val = convert_COL_back(*self.value)
                pack_into('<BBBB', tag.data, offset, *val)
            elif field.type_name == m3.VEC3.self__:
                val = self.value[:3]
                pack_into('<fff', tag.data, offset, *val)

    def setRGB_spin(self, idx, val):
        if self.updating: return
        self.value[idx] = val / SPINEDIT_MAX
        self.sliders[idx].setValue(round(self.value[idx] * SLIDER_MAX))
        self.displayValue()
        self.updateHLS()

    def setRGB_slider(self, idx, val):
        if self.updating: return
        self.value[idx] = val / SLIDER_MAX
        self.spins[idx].setValue(self.value[idx] * SPINEDIT_MAX)
        self.displayValue()
        self.updateHLS()

    def setA_spin(self, idx, val):
        if self.updating: return
        self.value[idx] = val / SPINEDIT_MAX
        self.sliders[idx].setValue(round(self.value[idx] * SLIDER_MAX))
        self.displayValue()

    def setA_slider(self, idx, val):
        if self.updating: return
        self.value[idx] = val / SLIDER_MAX
        self.spins[idx].setValue(self.value[idx] * SPINEDIT_MAX)
        self.displayValue()

    def updateRGBfromHLS(self):
        h = self.sliders[IDX_H].value() / SLIDER_MAX
        l = self.sliders[IDX_L].value() / SLIDER_MAX
        s = self.sliders[IDX_S].value() / SLIDER_MAX
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        self.value[IDX_R] = r
        self.value[IDX_G] = g
        self.value[IDX_B] = b
        self.displayValue()
        self.updateRGB()

    def setHLS_spin(self, idx, val):
        if self.updating: return
        val = val / SPINEDIT_MAX
        self.sliders[idx].setValue(round(val * SLIDER_MAX))
        self.updateRGBfromHLS()

    def setHLS_slider(self, idx, val):
        if self.updating: return
        val = val / SLIDER_MAX
        self.spins[idx].setValue(val * SPINEDIT_MAX)
        self.updateRGBfromHLS()

    def updateRGB(self):
        self.updating = True
        self.ui.edtR.setValue(self.value[IDX_R] * SPINEDIT_MAX)
        self.ui.sliderR.setValue(round(self.value[IDX_R] * SLIDER_MAX))
        self.ui.edtG.setValue(self.value[IDX_G] * SPINEDIT_MAX)
        self.ui.sliderG.setValue(round(self.value[IDX_G] * SLIDER_MAX))
        self.ui.edtB.setValue(self.value[IDX_B] * SPINEDIT_MAX)
        self.ui.sliderB.setValue(round(self.value[IDX_B] * SLIDER_MAX))
        self.updating = False

    def updateHLS(self):
        h, l, s = colorsys.rgb_to_hls(*self.value[:3])
        self.updating = True
        self.ui.edtH.setValue(h * SPINEDIT_MAX)
        self.ui.sliderH.setValue(round(h * SLIDER_MAX))
        self.ui.edtL.setValue(l * SPINEDIT_MAX)
        self.ui.sliderL.setValue(round(l * SLIDER_MAX))
        self.ui.edtS.setValue(s * SPINEDIT_MAX)
        self.ui.sliderS.setValue(round(s * SLIDER_MAX))
        self.updating = False

    def displayValue(self):
        self.px_cur_val.fill(QColor.fromRgbF(*self.value))
        if self.painter.begin(self.px_cur_val):
            try:
                self.painter.fillRect(20,20,60,60,QColor.fromRgbF(*self.value[:3], 1.0))
            finally:
                self.painter.end()
        self.ui.lblCurVal.setPixmap(self.px_cur_val)

    def updateAll(self):
        self.updateRGB()
        self.updateHLS()
        self.displayValue()

    def okClick(self):
        self.done(QDialog.DialogCode.Accepted)

    def cancelClick(self):
        self.done(QDialog.DialogCode.Rejected)

    def resetClick(self):
        self.value = self.init_value.copy()
        self.updateAll()

    def pickColorClick(self):
        val = QColorDialog.getColor(QColor.fromRgbF(*self.value[:3]), self)
        if val.isValid():
            self.value[IDX_R] = val.redF()
            self.value[IDX_G] = val.greenF()
            self.value[IDX_B] = val.blueF()
            self.updateAll()

class color_handler(AbstractFieldHandler):
    def __init__(self, parent):
        self.dialog = ColorFieldEdit(parent)

    def editField(self, tag: m3Tag, item: int, field: m3FieldInfo):
        self.dialog.editValue(tag, item, field)

    def fieldData(self, role: Qt.ItemDataRole, tag: m3Tag, item: int, field: m3FieldInfo):
        if role == Qt.ItemDataRole.DecorationRole:
            if field.type_name == m3.COL.self__:
                val = convert_COL(*tag.getFieldUnpacked(item, field, '<BBBB')) # BGRA
            elif field.type_name == m3.VEC3.self__:
                val = convert_VEC3(*tag.getFieldUnpacked(item, field, '<fff')) # RGB
            else:
                return QVariant()
            px = QPixmap(10,10)
            px.fill(QColor.fromRgbF(*val[:3]))
            return px
        elif role == Qt.ItemDataRole.DisplayRole:
            if field.type_name == m3.COL.self__:
                val = tag.getFieldUnpacked(item, field, '<BBBB') # BGRA
                return f'RGBA: #{val[2]:02x}{val[1]:02x}{val[0]:02x}{val[3]:02x}'
            elif field.type_name == m3.VEC3.self__:
                val = convert_COL_back(*tag.getFieldUnpacked(item, field, '<fff'), 1.0) # RGB
                return f'RGB: #{val[2]:02x}{val[1]:02x}{val[0]:02x}'
            else:
                return QVariant()

registerFieldHandlerClass(m3.VEC3.self__, color_handler)
registerFieldHandlerClass(m3.COL.self__, color_handler)
