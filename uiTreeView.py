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
from PyQt5.QtCore import *
from m3file import m3File, m3Tag
from m3struct import m3StructFile, m3Type, m3FieldInfo, BINARY_DATA_ITEM_BYTES_COUNT
from editors.fieldHandlers import fieldHandlersCollection
from common import ceildiv, clampi

SHADOW_TAG, SHADOW_IT, SHADOW_GRP, SHADOW_DUP = range(4)
SHADOW_GRP_COUNT = 20

DEFAULT_SIMPLE_FIELDS_DISPLAY_COUNT = 50

class ShadowItem():
    def __init__(self, notifyParent: Callable[[int, int], int], index: int, type: int, parent: int, text: str, tag: m3Tag = None, tag_item = -1):
        #self.owner = owner
        self.index = index
        self.parent = parent
        if parent==None:
            self.row = 0
        else:
            self.row = notifyParent(parent, index)
        self.children = [] # type: List[int]

        self.type = type
        self.text = text
        self.tag = tag
        self.tag_item = tag_item
    
    def noticeChild(self, child):
        ret = len(self.children)
        self.children.append(child)
        return ret

class ShadowTree():
    def __init__(self, m3: m3File = None):
        self.processM3(m3)

    def processM3(self, m3: m3File):
        self.m3 = m3
        if m3:
            self.root = ShadowItem(self.notifyParent, 0, SHADOW_TAG, None, 'model', m3.modl)
        else:
            self.root = ShadowItem(self.notifyParent, 0, SHADOW_GRP, None, 'no model opened')
        self.orphan_root = ShadowItem(self.notifyParent, 1, SHADOW_GRP, None, 'orphan tags (not referenced from others)')
        self.orphan_root.row = 1
        self.items = [self.root, self.orphan_root] # type: List[ShadowItem]
        self.tags = [] # type: List[m3Tag]
        self.lastTagIdx = 0
        self.processTag(0, None)
        if m3:
            for orph in self.m3.orphans:
                tag = self.m3.tags[orph]
                if not tag in self.tags:
                    self.processTag(1, tag)

    def getShadowIndex(self, parent, row):
        if parent in range(0, len(self.items)):
            if row in range(0, len(self.items[parent].children)):
                return self.items[parent].children[row]

    def getShadow(self, index) -> ShadowItem:
        if index in range(0, len(self.items)):
            return self.items[index]

    def notifyParent(self, parent, child) -> int:
        if parent in range(0, len(self.items)):
            return self.items[parent].noticeChild(child)

    def isTagDuplicate(self, tag: m3Tag):
        if tag in self.tags:
            return True
        else:
            self.tags.append(tag)
            return False

    def newTagShadow(self, parent, tag: m3Tag, parent_field: m3FieldInfo = None):
        idx = len(self.items)
        prefix = f'{parent_field.name}->' if parent_field else ''
        if not tag:
            text = f'ERROR: Invalid m3Tag ({tag})'
        elif tag.info.type == m3Type.CHAR:
            text = f'{tag.info.name}#{tag.idx} {tag.getItemName()}'
        else:
            text = f'{tag.info.name}#{tag.idx} ({tag.count})'
        self.items.append( ShadowItem(
            self.notifyParent,
            idx,
            SHADOW_DUP if self.isTagDuplicate(tag) else SHADOW_TAG,
            parent,
            prefix + text,
            tag
        ) )
        return idx

    def newItemShadow(self, parent, tag: m3Tag, item_idx: int):
        idx = len(self.items)
        self.items.append( ShadowItem(
            self.notifyParent,
            idx,
            SHADOW_IT,
            parent,
            f'{tag.info.name}[{item_idx}]{tag.getItemName(item_idx)}',
            tag,
            item_idx
        ) )
        return idx

    def newGrpShadow(self, parent, start, max_count):
        idx = len(self.items)
        end = min(start + SHADOW_GRP_COUNT - 1, max_count - 1)
        if start==end: # do not create group for 1 item
            return parent
        self.items.append( ShadowItem(
            self.notifyParent,
            idx,
            SHADOW_GRP,
            parent,
            f'[{start:02d}-{end:02d}]'
        ) )
        return idx

    def processItem(self, tree_item, tag: m3Tag, item_idx):
        for f in tag.info.fields:
            if f.notSelfField and f.type in m3Type.REFS and tag.refIsValid(item_idx, f):
                self.processTag(tree_item, tag.getReff(item_idx, f), f)

    def processGroup(self, parent, tag: m3Tag, start):
        count = min(start + SHADOW_GRP_COUNT, tag.count)
        for it in range(start,count):
            self.processItem(
                self.newItemShadow(parent, tag, it),
                tag,
                it
            )

    def processTag(self, parent, tag: m3Tag, parent_field: m3FieldInfo = None):
        if not tag: # processing root
            shadow = 0
            tag = self.root.tag
        else:
            shadow = self.newTagShadow(parent, tag, parent_field)
        # do not display children of simple tags in the tree
        # also don't process thags with index less than last to prevent possible ref loops
        # and don't put vertices as children in the tree
        if not tag or tag.info.isSingleField() or tag.idx < self.lastTagIdx or tag.info.type == m3Type.VERTEX: return
        self.lastTagIdx = tag.idx
        if tag.count > SHADOW_GRP_COUNT:
            for start in range(0,tag.count,SHADOW_GRP_COUNT):
                grp = self.newGrpShadow(shadow, start, tag.count)
                self.processGroup(grp,tag,start)
        else:
            self.processGroup(shadow,tag,0)

class TagTreeModel(QAbstractItemModel):
    TagTreeShadowRole = Qt.ItemDataRole.UserRole # type: 'Qt.ItemDataRole'

    def __init__(self) -> None:
        self.shadows = ShadowTree()
        super().__init__(None)

    def changeM3(self, m3: m3File):
        self.beginResetModel()
        self.shadows.processM3(m3)
        self.endResetModel()
    
    def index(self, row: int, column: int, parent: QModelIndex = ...) -> QModelIndex:
        if not self.shadows or column>0:
            return QModelIndex()
        if parent.isValid():
            index = self.shadows.getShadowIndex(parent.internalId(), row)
            if index:
                return self.createIndex(row, column, index)
        else:
            return self.createIndex(row,0,row) # model and orphan roots
        return QModelIndex()
    
    def parent(self, child: QModelIndex) -> QModelIndex:
        if not self.shadows or not child.isValid():
            return QModelIndex()
        shadow = self.shadows.getShadow(child.internalId())
        if shadow and shadow.parent != None: # process both 0 and None as false? should we return invalid QModelIndex when parent is root?
            parent = self.shadows.getShadow(shadow.parent)
            if parent: return self.createIndex(parent.row, 0, parent.index)
        return QModelIndex()
    
    def rowCount(self, parent: QModelIndex) -> int:
        if not self.shadows: return 0
        if parent.isValid():
            shadow = self.shadows.getShadow(parent.internalId())
        else:
            return 2 if len(self.shadows.orphan_root.children)>0 else 1
        if shadow: return len(shadow.children)
        return 0
    
    def columnCount(self, parent: QModelIndex) -> int:
        if not self.shadows: return 0
        return 1
    
    def data(self, index: QModelIndex, role: int):
        if not self.shadows: return QVariant()
        shadow = self.shadows.getShadow(index.internalId())
        if not shadow: return QVariant()
        if role == Qt.ItemDataRole.DisplayRole:
            return shadow.text
        if role == Qt.ItemDataRole.StatusTipRole:
            return shadow.text
        if role == Qt.ItemDataRole.ToolTipRole and shadow.tag:
            return shadow.tag.info.descr
        if role == TagTreeModel.TagTreeShadowRole:
            return shadow
        return QVariant()

    def hasChildren(self, parent: QModelIndex) -> bool:
        if self.shadows:
            if parent.isValid():
                shadow = self.shadows.getShadow(parent.internalId())
            else:
                #shadow = self.shadows.root
                return True
            if shadow:
                return True if len(shadow.children)>0 else False
        return False

class fieldsTableModel(QAbstractItemModel):
    FieldRole = Qt.ItemDataRole.UserRole # type: 'Qt.ItemDataRole'
    SimpleFieldOffsetRole = Qt.ItemDataRole.UserRole + 1 # type: 'Qt.ItemDataRole'
    BinaryViewOffsetRole = Qt.ItemDataRole.UserRole + 2 # type: 'Qt.ItemDataRole'
    FullFieldHintRole = Qt.ItemDataRole.UserRole + 3 # type: 'Qt.ItemDataRole'

    def __init__(self, handlers: fieldHandlersCollection, tag: m3Tag = None) -> None:
        self.tag = tag
        self.handlers = handlers
        self.simpleFieldsDisplayCount = DEFAULT_SIMPLE_FIELDS_DISPLAY_COUNT
        self.binaryView = False
        self.isBaseTag = False # when selecting tag itself in tags tree, not one of its items
        super().__init__(None)

    def setM3Tag(self, tag: m3Tag, tag_item: int):
        if not tag: return
        self.beginResetModel()
        self.tag = tag
        self.isBaseTag = False if tag_item in range(0, tag.count) else True
        if self.isBaseTag:
            self.tag_item = 0
        else:
            self.tag_item = tag_item
        self._updateItemCount()
        self.item_offset = 0
        self.step = 0
        self.endResetModel()

    def _setSimpleItemOffset(self, offset: int):
        if self.item_offset != offset:
            self.beginResetModel()
            self.item_offset = offset
            self.endResetModel()

    def stepItemOffset(self, step: int):
        if self.tag and (self.tag.info.simple or self.binaryView):
            self.step = clampi(self.step + step, 0, self.step_max)
            self._setSimpleItemOffset(self.simpleFieldsDisplayCount * self.step)
        elif self.isBaseTag:
            tag_item = clampi(self.tag_item + step, 0, self.item_count - 1)
            if self.tag_item != tag_item:
                self.tag_item = tag_item
                self.dataChanged.emit(QModelIndex(), QModelIndex())

    def setSimpleFieldsDisplayCount(self, value: int):
        if self.tag and (self.tag.info.simple or self.binaryView):
            self.beginResetModel()
            self.simpleFieldsDisplayCount = value
            self.step_max = max(range(0, self.item_count, self.simpleFieldsDisplayCount)) // self.simpleFieldsDisplayCount
            self.step = clampi(self.step, 0, self.step_max)
            self.item_offset = self.simpleFieldsDisplayCount * self.step
            self.endResetModel()
        else:
            self.simpleFieldsDisplayCount = value

    def setBinaryView(self, value: bool):
        if self.binaryView != value:
            if self.tag:
                self.beginResetModel()
                self.binaryView = value
                self._updateItemCount()
                self._updateItemOffset()
                self.endResetModel()
            else:
                self.binaryView = value

    def _updateItemCount(self):
        if self.tag.info.type == m3Type.BINARY:
            self.item_count = ceildiv(len(self.tag.data), BINARY_DATA_ITEM_BYTES_COUNT)
        elif self.binaryView:
            if self.isBaseTag:
                self.item_count = ceildiv(len(self.tag.data), BINARY_DATA_ITEM_BYTES_COUNT)
            else:
                self.item_count = ceildiv(self.tag.info.item_size, BINARY_DATA_ITEM_BYTES_COUNT)
        else:
            self.item_count = self.tag.count
        self.step_max = max(range(0, self.item_count, self.simpleFieldsDisplayCount)) // self.simpleFieldsDisplayCount

    def _updateItemOffset(self):
        self.step = clampi(self.step, 0, self.step_max)
        self.item_offset = clampi(self.item_offset, 0, self.item_count - 1)

    def getTagItemIndexStr(self) -> str:
        if not self.tag: return '##'
        if self.binaryView:
            start = self.item_offset * BINARY_DATA_ITEM_BYTES_COUNT
            end = min(self.item_count, self.item_offset + self.simpleFieldsDisplayCount) * BINARY_DATA_ITEM_BYTES_COUNT - 1
            return f'0x{start:08x} - 0x{end:08x}'
        if self.tag.info.simple:
            end = min(self.item_count, self.item_offset + self.simpleFieldsDisplayCount) - 1
            return f'{self.item_offset} - {end}'
        return f'{self.tag_item}'

    def navigate(self, value) -> bool:
        if self.tag:
            if self.binaryView or self.tag.info.simple: # value is an offset to show
                if self.binaryView: value = value // BINARY_DATA_ITEM_BYTES_COUNT
                if value in range(0, self.item_count):
                    self.step = max(range(0, min(value+1, self.item_count), self.simpleFieldsDisplayCount)) // self.simpleFieldsDisplayCount
                    self._setSimpleItemOffset(self.simpleFieldsDisplayCount * self.step)
                    return True
            elif self.isBaseTag and value in range(0, self.item_count):
                if self.tag_item != value:
                    self.tag_item = value
                    self.dataChanged.emit(QModelIndex(), QModelIndex())
                return True
        return False

    ### Tree Implementation ###

    def index(self, row: int, column: int, parent: QModelIndex) -> QModelIndex:
        if self.tag.info.simple or self.binaryView:
            if parent.isValid(): return QModelIndex()
            return self.createIndex(row, column, row*10+column)
        elif parent.isValid():
            f = self.tag.info.getField(parent.internalId())
            if f and row in range(0, len(f.tree_children)):
                return self.createIndex(row, column, f.tree_children[row])
        elif row in range(0, len(self.tag.info.root_fields)):
            return self.createIndex(row, column, self.tag.info.root_fields[row])
        return QModelIndex()

    def parent(self, child: QModelIndex) -> QModelIndex:
        if self.tag.info.simple or self.binaryView:
            pass
        elif child.isValid():
            f = self.tag.info.getFieldParent(child.internalId())
            if f:
                return self.createIndex(f.tree_row, 0, f.getIndex())
        return QModelIndex()

    def rowCount(self, parent: QModelIndex) -> int:
        if self.tag:
            if self.tag.info.simple or self.binaryView:
                if parent.isValid(): return 0
                return min(self.item_count - self.item_offset, self.simpleFieldsDisplayCount)
            if parent.isValid() and parent.column()==0:
                f = self.tag.info.getField(parent.internalId())
                return len(f.tree_children) if f else 0
            return len(self.tag.info.root_fields)
        return 0

    def columnCount(self, parent: QModelIndex) -> int:
        return 4

    def dataDefault(self, role: int):
        if role == fieldsTableModel.FieldRole:
            return None
        if role == fieldsTableModel.SimpleFieldOffsetRole:
            return None
        if role == fieldsTableModel.BinaryViewOffsetRole:
            return None
        if role == fieldsTableModel.FullFieldHintRole:
            return ''
        return QVariant()

    def data(self, index: QModelIndex, role: int):
        if not (index.isValid() and self.tag):
            return self.dataDefault(role)
        col = index.column()
        f = None
        if self.binaryView:
            offset = (self.item_offset + index.row()) * BINARY_DATA_ITEM_BYTES_COUNT
            if self.isBaseTag:
                size = min(len(self.tag.data) - offset, BINARY_DATA_ITEM_BYTES_COUNT)
            else:
                size = min(self.tag.info.item_size - offset, BINARY_DATA_ITEM_BYTES_COUNT)
                offset += self.tag.info.item_size * self.tag_item
            if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.StatusTipRole):
                if col == 0:
                    return f'0x{offset:08x}'
                elif col == 1:
                    return 'HEX'
                elif col == 2:
                    return ''
                elif col == 3:
                    return self.tag.getBinaryAsStr(offset, size)
            if role == fieldsTableModel.BinaryViewOffsetRole:
                return offset
        elif self.tag.info.simple:
            f = self.tag.info.fields[0]
            item = self.item_offset + index.row()
            if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.StatusTipRole):
                if col == 0:
                    return f'{f.name} 0x{item*self.tag.info.item_size:08x}' if f.type == m3Type.BINARY else f'{f.name} {item:3d}'
                elif col == 1:
                    return f.type_name
                elif col == 2:
                    return self.tag.getFieldInfoStr(f)
                elif col == 3:
                    return self.tag.getFieldAsStr(item, f)
            if role == fieldsTableModel.SimpleFieldOffsetRole:
                return item * self.tag.info.item_size
        elif index.internalId() in range(0, len(self.tag.info.fields)):
            f = self.tag.info.fields[index.internalId()]
            if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.StatusTipRole):
                if col == 0:
                    return f.display_name if role == Qt.ItemDataRole.DisplayRole else f.name
                elif col == 1:
                    return f.type_name
                elif col == 2:
                    return self.tag.getFieldInfoStr(f)
                elif col == 3:
                    if self.handlers.hasHandler(f):
                        return self.handlers.fieldData(role, self.tag, self.tag_item, f)
                    return self.tag.getFieldAsStr(self.tag_item, f)
            elif role == Qt.ItemDataRole.ToolTipRole:
                tip = f.getHint()
                if tip: return tip
            elif col == 3 and role < Qt.ItemDataRole.UserRole:
                return self.handlers.fieldData(role, self.tag, self.tag_item, f)
        if role == fieldsTableModel.FieldRole and f:
            return f
        if role == fieldsTableModel.FullFieldHintRole and f:
            return f.getHint(True)
        return self.dataDefault(role)

    def hasChildren(self, parent: QModelIndex) -> bool:
        if not parent.isValid(): return True
        if self.tag and not self.binaryView and not self.tag.info.simple and parent.column()==0:
            f = self.tag.info.getField(parent.internalId())
            return len(f.tree_children) > 0
        return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section==0:
                return 'Field'
            elif section==1:
                return 'Type'
            elif section==2:
                return 'Info'
            elif section==3:
                return 'Value'
        return QVariant()
