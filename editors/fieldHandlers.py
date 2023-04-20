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
from typing import Dict, Type
from PyQt5.QtCore import *
from m3file import m3Tag
from m3struct import m3FieldInfo

class AbstractFieldHandler():
    def __init__(self, parent): pass
    def editField(self, tag: m3Tag, item: int, field: m3FieldInfo): pass
    def fieldData(self, role: Qt.ItemDataRole, tag: m3Tag, item: int, field: m3FieldInfo): return QVariant()

_handlers = {} # type: Dict[str, Type[AbstractFieldHandler]]

class fieldHandlersCollection():
    def __init__(self, parent) -> None:
        self.handlers = {} # type: Dict[str, AbstractFieldHandler]
        for field in _handlers:
            self.handlers[field] = _handlers[field](parent)

    def hasHandler(self, field: m3FieldInfo) -> bool:
        return True if field.type_name in self.handlers else False

    def editField(self, tag: m3Tag, item: int, field: m3FieldInfo):
        if field.type_name in self.handlers:
            return self.handlers[field.type_name].editField(tag, item, field)

    def fieldData(self, role: Qt.ItemDataRole, tag: m3Tag, item: int, field: m3FieldInfo):
        if field.type_name in self.handlers and role < Qt.ItemDataRole.UserRole:
            return self.handlers[field.type_name].fieldData(role, tag, item, field)
        else:
            return QVariant()

def registerFieldHandlerClass(field_type_name, handler_class: type):
    if issubclass(handler_class, AbstractFieldHandler):
        _handlers[field_type_name] = handler_class

from .handlers import *