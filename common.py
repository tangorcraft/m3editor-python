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
from struct import pack
from configparser import ConfigParser
from PyQt5.QtWidgets import QAction

class Options():
    SECT_MAIN = 'main'
    SECT_TREE_VIEW = 'tree_view'

    OPT_CONFIRM_BIT_EDIT = (SECT_TREE_VIEW, 'confirm_bit_edit')
    OPT_FIELDS_AUTO_EXPAND = (SECT_TREE_VIEW, 'field_auto_expand')

    def __init__(self):
        self.ini = ConfigParser()
        self.ini.read('options.ini')

    def setIniOption(self, sect, opt, val, saveINI = False):
        if not sect in self.ini:
            self.ini[sect] = {}
        self.ini[sect][opt] = str(val)
        if saveINI: self.saveIni()

    def setOption(self, opt, val, saveINI = False):
        self.setIniOption(opt[0], opt[1], val, saveINI)

    def setOptionBool(self, opt, val: bool, saveINI = False):
        v = '1' if val else '0'
        self.setIniOption(opt[0], opt[1], v, saveINI)

    def getOption(self, opt, fallback) -> str:
        return self.ini.get(opt[0], opt[1], fallback=fallback)

    def getOptionBool(self, opt, fallback: bool) -> bool:
        fb = '1' if fallback else '0'
        return (self.ini.get(opt[0], opt[1], fallback=fb) != '0')

    def connectWithActionCheckState(self, action: QAction, opt, opt_fallback):
        action.setChecked(self.getOptionBool(opt, opt_fallback))
        action.triggered.connect(lambda: self.setOptionBool(opt, action.isChecked()))

    def saveIni(self):
        with open('options.ini','w') as cfgFile:
            self.ini.write(cfgFile)

options = Options()

def ceildiv(a: int, b: int) -> int:
    '''Ceil division, same as ceil(a/b)'''
    return -(a//-b)

def clampi(val: int, min: int, max: int) -> int:
    return min if val < min else max if val > max else val

def clampf(val: float, min: float, max: float) -> float:
    return min if val < min else max if val > max else val

def fixed8_to_float(val):
    return (val / 255.0) * 2 - 1

def float_to_fixed8(val):
    if val < -1.0 or val > 1.0:
        raise ValueError('fixed8 value must be in range from -1.0 to 1.0')
    return clampi(round((val + 1) * 255 / 2), 0, 255)

def fixed16_to_float(val):
    return val / 2048.0

def float_to_fixed16(val):
    if val < 0.0 or val > 32.0:
        raise ValueError('fixed16 value must be in range from 0.0 to 32.0')
    return clampi(val * 2048, 0, 0xFFFF)

TAG_SIZE_STEP = 0x10
def getTagStepNeededBytes(count):
    return max(1, ceildiv(count, TAG_SIZE_STEP))*TAG_SIZE_STEP - count

def pack_all(base_format, *v):
    res = bytes()
    for i in v:
        res += pack(base_format, i)
    return res
