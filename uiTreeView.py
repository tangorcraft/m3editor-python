from typing import List, Callable
from PyQt5.QtCore import *
from m3file import m3File, m3Tag
from m3struct import m3StructFile, m3Type, m3FieldInfo

SHADOW_TAG, SHADOW_IT, SHADOW_GRP, SHADOW_DUP = range(4)
SHADOW_GRP_COUNT = 20

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
            text = f'{tag.info.name}#{tag.idx} "{tag.getStr()}"'
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
            f'{tag.info.name}[{item_idx}]',
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
            if f.type in m3Type.REFS and tag.refIsValid(item_idx, f):
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
        if not tag or tag.info.simple or tag.idx < self.lastTagIdx: return
        self.lastTagIdx = tag.idx
        if tag.count > SHADOW_GRP_COUNT:
            for start in range(0,tag.count,SHADOW_GRP_COUNT):
                grp = self.newGrpShadow(shadow, start, tag.count)
                self.processGroup(grp,tag,start)
        else:
            self.processGroup(shadow,tag,0)

class TagTreeModel(QAbstractItemModel):
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
        if role == Qt.DisplayRole:
            return shadow.text
        if role == Qt.StatusTipRole:
            return shadow.text
        if role == Qt.UserRole:
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

class fieldsTableModel(QAbstractTableModel):
    def __init__(self, tag: m3Tag = None) -> None:
        self.tag = tag
        super().__init__(None)

    def setFields(self, tag: m3Tag, tag_item: int):
        self.beginResetModel()
        self.tag = tag
        self.tag_item = tag_item
        self.endResetModel()

    def rowCount(self, parent: QModelIndex) -> int:
        if self.tag: return len(self.tag.info.fields)
        return 0
    
    def columnCount(self, parent: QModelIndex) -> int:
        return 4

    def data(self, index: QModelIndex, role: int):
        if index.isValid() and self.tag and index.row() in range(0, len(self.tag.info.fields)):
            f = self.tag.info.fields[index.row()]
            col = index.column()
            if role in (Qt.DisplayRole, Qt.StatusTipRole):
                if col == 0:
                    return f.name
                elif col == 1:
                    return f.type_name
                elif col == 2:
                    return f.getInfoStr()
                elif col == 3:
                    return self.tag.getFieldAsStr(self.tag_item, f)
        return QVariant()
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section==0:
                return 'Field'
            elif section==1:
                return 'Type'
            elif section==2:
                return 'Info'
            elif section==3:
                return 'Value'
        return QVariant()
