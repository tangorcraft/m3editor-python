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
def ceildiv(a: int, b: int) -> int:
    '''Ceil division, same as ceil(a/b)'''
    return -(a//-b)

def clampi(val: int, min: int, max: int) -> int:
    return min if val < min else max if val > max else val

TAG_SIZE_STEP = 0x10
def getTagStepNeededBytes(count):
    return max(1, ceildiv(count, TAG_SIZE_STEP))*TAG_SIZE_STEP - count
