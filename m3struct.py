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
from __future__ import annotations
import xml.sax, re
from struct import pack, unpack_from, calcsize
from xml.sax.xmlreader import AttributesImpl
from typing import Dict, List

def m3TagFromName(name: str) -> int:
    if name and len(name)<=4:
        b = bytes([ord(x) for x in name])[::-1]+b'\x00'*4
        return unpack_from('<I',b)[0]
    else:
        return 0

def m3TagToStr(tag: int) -> str:
    b = pack('>I',tag)
    while len(b)>0 and b[0]==0:
        b = b[1:]
    return b.decode()

def addToList(base, name, obj):
    if not name in base:
        base[name] = []
    base[name].append(obj)

def convertFieldToInt(obj, field):
    if field in obj:
        num = int(obj[field], 0)
        obj[field] = num

def checkMask(value: int, mask: int) -> bool:
    return True if value & mask == mask else False

TAG_HEADER_33 = m3TagFromName('MD33')
TAG_HEADER_34 = m3TagFromName('MD34')
TAG_CHAR = m3TagFromName('CHAR')
TAG_LAYR = m3TagFromName('LAYR')
TAG_SEQS = m3TagFromName('SEQS')

IDX_TAG = 1
IDX_TYPE = 2
IDX_NAME = 3
IDX_DESC = 4
IDX_VERS = 5
IDX_FIELDS = 6
IDX_HINT = 7
IDX_BITS = 8
IDX_SIMPLE = 9

SUB_STRUCT_DELIM = '.'

BINARY_DATA_ITEM_BYTES_COUNT = 16

VERTICES_STRUCT_UNIVERSAL = 'VertexFormat'

class Tag:
    STRUCT = 'structure'
    DESC = 'description'
    VERS = 'versions'
    VER = 'version'
    FIELDS = 'fields'
    FIELD = 'field'
    BIT = 'bit'
    HINT = 'hint'

    HAS_ATTR = (STRUCT, VER, FIELD, BIT)

class Attr:
    NUM = 'number'
    SIZE = 'size'
    NAME = 'name'
    TYPE = 'type'
    HINT = 'hint'
    REF_TO = 'refTo'
    MASK = 'mask'
    DEFAULT = 'default-value'
    EXPECTED = 'expected-value'
    SINCE_VER = 'since-version'
    TILL_VER = 'till-version' # inclusive
    BINARY = 'char-binary'
    VERTICES = 'ref-vertices'

class m3Type():
    BINARY = 1
    UINT8 = 2
    UINT16 = 3
    UINT32 = 4
    INT8 = 5
    INT16 = 6
    INT32 = 7
    FLOAT = 8
    REF = 9
    REF_SMALL = 10
    STRUCT = 11
    CHAR = 12
    BIT = 13
    VERTEX = 14

    NAME_TO_TYPE = {
        'uint8': UINT8,
        'fixed8': UINT8,
        'uint16': UINT16,
        'uint32': UINT32,
        'tag': UINT32,
        'int8': INT8,
        'int16': INT16,
        'int32': INT32,
        'float': FLOAT,
        'Reference': REF,
        'SmallReference': REF_SMALL,
    }

    TYPE_TO_SIZE = {
        UINT8: 1,
        UINT16: 2,
        UINT32: 4,
        INT8: 1,
        INT16: 2,
        INT32: 4,
        FLOAT: 4,
        REF: calcsize('<III'),
        REF_SMALL: calcsize('<II'),
    }

    TYPE_TO_STR = {
        BINARY: 'Binary',
        UINT8: 'uInt8',
        UINT16: 'uInt16',
        UINT32: 'uInt32',
        INT8: 'Int8',
        INT16: 'Int16',
        INT32: 'Int32',
        FLOAT: 'Float',
        REF: 'Reference',
        REF_SMALL: 'Reference (small)',
        STRUCT: 'Structure',
        CHAR: 'String',
        BIT: 'Flag Bit'
    }

    TYPE_TO_FORMAT = {
        UINT8: '<B',
        UINT16: '<H',
        UINT32: '<I',
        INT8: '<b',
        INT16: '<h',
        INT32: '<i',
        FLOAT: '<f',
    }

    TYPE_TO_HEX_FORMAT = {
        UINT8: '<B',
        UINT16: '<H',
        UINT32: '<I',
        INT8: '<B',
        INT16: '<H',
        INT32: '<I',
        FLOAT: '<I',
    }

    SIMPLE = (UINT8, UINT16, UINT32, INT8, INT16, INT32, FLOAT)
    REFS = (REF, REF_SMALL)

    @classmethod
    def fromName(cls, name) -> int:
        if name=='':
            return cls.BINARY
        elif name in cls.NAME_TO_TYPE:
            return cls.NAME_TO_TYPE[name]
        else:
            return cls.STRUCT

    @classmethod
    def toSize(cls, type) -> int:
        if type in cls.TYPE_TO_SIZE:
            return cls.TYPE_TO_SIZE[type]
        else:
            return 0

    @classmethod
    def toStr(cls, type) -> str:
        if type in cls.TYPE_TO_STR:
            return cls.TYPE_TO_STR[type]
        else:
            return f'Unknown {type}'

    @classmethod
    def toFormat(cls, type) -> int:
        if type in cls.TYPE_TO_FORMAT:
            return cls.TYPE_TO_FORMAT[type]

    @classmethod
    def toHexFormat(cls, type) -> int:
        if type in cls.TYPE_TO_HEX_FORMAT:
            return cls.TYPE_TO_HEX_FORMAT[type]

class m3FieldInfo():
    def __init__(self, owner: m3StructInfo, type_name, prefix, name, offset, Type = None, size = 0, bitMask = 0) -> None:
        self.owner = owner
        self.tree_parent = 0
        self.tree_row = 0
        self.tree_children = [] # type: List[int]
        if Type==None:
            self.type = m3Type.fromName(type_name)
        else:
            self.type = Type
        self.type_name = type_name
        self.name = prefix + name # type: str
        self.display_name = name
        self.offset = offset
        self.default = None
        self.expected = None
        self.refTo = None
        self.refToBinary = False
        self.refToVertices = False
        self.size = size
        self.bitMask = bitMask
        self.notSelfField = True

    def noticeChild(self, child) -> int:
        idx = len(self.tree_children)
        self.tree_children.append(child)
        return idx

    def setParent(self, parent: int):
        self.tree_parent = parent
        self.tree_row = self.owner.notifyParent(parent, self.getIndex())

    def getInfoStr(self) -> str:
        if self.type == m3Type.BIT:
            parent = self.owner.getField(self.tree_parent)
            if parent.default:
                try:
                    default = int(parent.default, 0)
                except TypeError:
                    return ''
                return 'Default' if default & self.bitMask == self.bitMask else ''
        s = ''
        delim = ''
        if self.default:
            s += f'Default = {self.default}'
            delim = ', '
        if self.expected:
            s += delim + f'Expected = {self.expected}'
            delim = ', '
        if self.refTo:
            s += delim + f'Ref to {self.refTo}'
        return s

    def getDataOffset(self, item_idx) -> int:
        return self.owner.item_size * item_idx + self.offset
    
    def isRef(self) -> bool:
        return True if self.type in m3Type.REFS else False

    def getIndex(self) -> int:
        return self.owner.fields.index(self)

class m3StructInfo():
    def __init__(self, tag: int, ver: int, structFile: m3StructFile):
        struct = structFile.ByTag(tag)
        self.name = m3TagToStr(tag)
        self.hasRefs = False
        self.fields = [] # type: List[m3FieldInfo]
        self.root_fields = [0] # we will add at least one field
        if tag == TAG_CHAR:
            self.type = m3Type.CHAR
            self.simple = False
            self.item_size = 0
            self.fields.append( m3FieldInfo(self, 'CHAR', '', 'String', 0, m3Type.CHAR) )
        elif not struct:
            self.type = m3Type.BINARY
            self.simple = True
            self.item_size = BINARY_DATA_ITEM_BYTES_COUNT
            self.fields.append( m3FieldInfo(self, 'Binary', '', 'bytes', 0, m3Type.BINARY, BINARY_DATA_ITEM_BYTES_COUNT) )
        else:
            self.type = struct[IDX_TYPE]
            self.simple = struct[IDX_SIMPLE]
            if self.simple:
                self.item_size = m3Type.toSize(self.type)
                self.fields.append( m3FieldInfo(self, struct[IDX_FIELDS][0][Attr.TYPE], '', 'value', 0, self.type) )
            else:
                field = m3FieldInfo(self, self.name, '', '*** Self ***', 0, self.type)
                field.notSelfField = False
                self.fields.append( field )
                self.item_size = self.putSubStructureFields(structFile, struct, 0, '', ver)

    def putSubStructureFields(self, structFile: m3StructFile, struct, offset, prefix, ver, parent = 0, flags = 0):
        if struct:
            for f in struct[IDX_FIELDS]:
                if Attr.SINCE_VER in f and f[Attr.SINCE_VER] > ver: continue
                if Attr.TILL_VER in f and f[Attr.TILL_VER] < ver: continue
                if flags and Attr.MASK in f and not checkMask(flags, f[Attr.MASK]): continue
                field = m3FieldInfo( self, f[Attr.TYPE], prefix, f[Attr.NAME], offset )
                if Attr.DEFAULT in f:
                    field.default = f[Attr.DEFAULT]
                if Attr.EXPECTED in f:
                    field.expected = f[Attr.EXPECTED]
                if Attr.REF_TO in f:
                    field.refTo = f[Attr.REF_TO]
                if Attr.BINARY in f:
                    field.refToBinary = True
                if Attr.VERTICES in f:
                    field.refToVertices = True
                if Attr.SIZE in f:
                    size = f[Attr.SIZE]
                else:
                    size = m3Type.toSize(field.type)
                field.size = size
                if not self.hasRefs and field.type in (m3Type.REF, m3Type.REF_SMALL):
                    self.hasRefs = True
                idx = len(self.fields)
                self.fields.append(field)
                field.setParent(parent)

                if IDX_BITS in f:
                    self.putSubBitsFields(field, idx, f[IDX_BITS])

                if size==0: # sub structure
                    match = re.search('(.*)V([0-9]+)$',f[Attr.TYPE])
                    if match:
                        n = match.group(1)
                        v = int(match.group(2))
                        field.type_name = n
                    else:
                        n = f[Attr.TYPE]
                        v = 0
                    offset = self.putSubStructureFields(structFile, structFile.ByName(n), offset, field.name+SUB_STRUCT_DELIM, v, idx)
                else:
                    if field.type == m3Type.BINARY and size > BINARY_DATA_ITEM_BYTES_COUNT:
                        self.putSubBinaryFields(field, idx, offset)
                    offset += size
        return offset

    def putSubBinaryFields(self, parent: m3FieldInfo, parent_idx, offset):
        if parent.type == m3Type.BINARY:
            for step in range(0, parent.size, BINARY_DATA_ITEM_BYTES_COUNT):
                field = m3FieldInfo(
                    self,
                    'Binary',
                    parent.name + SUB_STRUCT_DELIM,
                    f'bytes_0x{offset+step:08x}',
                    offset + step,
                    m3Type.BINARY,
                    min(BINARY_DATA_ITEM_BYTES_COUNT, parent.size - step)
                )
                self.fields.append(field)
                field.setParent(parent_idx)

    def putSubBitsFields(self, parent: m3FieldInfo, parent_idx, bits: List[Dict]):
        for b in bits:
            field = m3FieldInfo(
                self,
                'Flags Bit',
                parent.name + SUB_STRUCT_DELIM,
                b[Attr.NAME],
                parent.offset,
                m3Type.BIT,
                parent.size,
                b[Attr.MASK]
            )
            self.fields.append(field)
            field.setParent(parent_idx)

    def getField(self, index) -> m3FieldInfo:
        if index in range(0, len(self.fields)):
            return self.fields[index]

    def getFieldByName(self, name) -> m3FieldInfo:
        for f in self.fields:
            if f.name == name:
                return f

    def getFieldParent(self, index) -> m3FieldInfo:
        if index in range(0, len(self.fields)):
            parent = self.fields[index].tree_parent
            if parent in range(1, len(self.fields)):
                return self.fields[parent]

    def forceBinary(self):
        self.hasRefs = False
        self.fields = [] # type: List[m3FieldInfo]
        self.root_fields = [0]
        self.type = m3Type.BINARY
        self.simple = True
        self.item_size = BINARY_DATA_ITEM_BYTES_COUNT
        self.fields.append( m3FieldInfo(self, 'Binary', '', 'bytes', 0, m3Type.BINARY, BINARY_DATA_ITEM_BYTES_COUNT) )

    def forceVertices(self, structFile: m3StructFile, vflags: int):
        struct = structFile.ByName(VERTICES_STRUCT_UNIVERSAL)
        if not struct: return
        self.name = f'VERTEX ({self.name})'
        self.hasRefs = False
        self.fields = [] # type: List[m3FieldInfo]
        self.root_fields = [0]
        self.type = m3Type.VERTEX
        self.simple = False
        field = m3FieldInfo(self, 'Vertex', '', '*** Self ***', 0, self.type)
        field.notSelfField = False
        self.fields.append( field )
        self.item_size = self.putSubStructureFields(structFile, struct, 0, '', 0, flags=vflags)

    def notifyParent(self, parent, child: int):
        if parent in range(1, len(self.fields)):
            return self.fields[parent].noticeChild(child)
        idx = len(self.root_fields)
        self.root_fields.append(child)
        return idx

    def isSingleField(self) -> bool:
        return True if len(self.fields)<2 else False

class m3StructFile():
    def __init__(self):
        self.structByName = {}
        self.structByTag = {}
    
    def ByTag(self, tag: int):
        if tag in self.structByTag:
            return self.structByTag[tag]

    def ByName(self, name: str):
        if name in self.structByName:
            return self.structByName[name]

    def loadFromFile(self, fileName):
        parser = xml.sax.make_parser()
        # turn off namepsaces
        parser.setFeature(xml.sax.handler.feature_namespaces, 0)

        # override the default ContextHandler
        Handler = m3StructHandler(self)
        parser.setContentHandler( Handler )

        parser.parse(fileName)

class m3StructHandler( xml.sax.ContentHandler ):
    def __init__(self, file: m3StructFile):
        self.tag = ''
        self.file = file
        self.structs = {}

    def newEntry(self):
        self.entry = {
            IDX_DESC:'',
            IDX_VERS:[],
            IDX_FIELDS:[],
        } # type: Dict[int, List]
        tag = m3TagFromName(self.copyAttrIfExists(self.entry,Attr.NAME,IDX_NAME))
        if tag != 0:
            self.entry[IDX_TAG] = tag

    def finalizeEntry(self):
        if IDX_NAME in self.entry:
            self.entry_counter += 1
            copy = self.entry.copy()
            # here we need to process collected struct info and add it to StructFile

            copy[IDX_SIMPLE] = False
            if len(copy[IDX_FIELDS])==1: # check for simple types
                copy[IDX_TYPE] = m3Type.fromName(copy[IDX_FIELDS][0][Attr.TYPE])
                if copy[IDX_TYPE] in m3Type.SIMPLE:
                    copy[IDX_SIMPLE] = True
            else:
                copy[IDX_TYPE] = m3Type.STRUCT

            vers = copy[IDX_VERS]
            copy[IDX_VERS] = {}
            for v in vers:
                copy[IDX_VERS][v[Attr.NUM]] = v[Attr.SIZE]
            
            self.file.structByName[self.entry[IDX_NAME]] = copy
            if IDX_TAG in self.entry:
                self.file.structByTag[self.entry[IDX_TAG]] = copy

    def getAttr(self, attr) -> str:
        if attr in self.attr:
            return self.attr[attr]

    def copyAttrIfExists(self, dest, attr, key) -> str:
        if attr in self.attr:
            dest[key] = self.attr[attr]
            return self.attr[attr]
        else:
            return None

    def fieldAddHint(self, hint):
        if IDX_HINT in self.field:
            self.field[IDX_HINT] += '\n' + hint
        else:
            self.field[IDX_HINT] = hint

    def startDocument(self):
        self.entry_counter = 0

    def endDocument(self):
        #print('Entries processed:',self.entry_counter)
        pass

    # Call when an element starts
    def startElement(self, tag, attrs: AttributesImpl):
        if tag in Tag.HAS_ATTR:
            self.attr = {}
            for k,v in attrs.items():
                self.attr[k]=v
        if tag==Tag.STRUCT:
            self.newEntry()
        elif tag==Tag.FIELD:
            self.field = self.attr.copy()
            convertFieldToInt(self.field,Attr.SINCE_VER)
            convertFieldToInt(self.field,Attr.TILL_VER)
            convertFieldToInt(self.field,Attr.SIZE)
            convertFieldToInt(self.field,Attr.MASK)
            if not Attr.TYPE in self.field: self.field[Attr.TYPE] = ''
        elif tag==Tag.BIT:
            convertFieldToInt(self.attr,Attr.MASK)
            addToList(self.field,IDX_BITS,self.attr.copy())
        elif tag==Tag.VER:
            convertFieldToInt(self.attr,Attr.NUM)
            convertFieldToInt(self.attr,Attr.SIZE)
            addToList(self.entry,IDX_VERS,self.attr.copy())
        self.tag = tag

    # Call when an elements ends
    def endElement(self, tag):
        if tag == Tag.STRUCT:
            self.finalizeEntry()
        elif tag==Tag.FIELD:
            addToList(self.entry,IDX_FIELDS,self.field.copy())

    # Call when a character is read
    def characters(self, content: str):
        s = content.strip()
        if s:
            if self.tag==Tag.DESC:
                self.entry[IDX_DESC] = s
            elif self.tag==Tag.HINT:
                self.fieldAddHint(s)

if __name__ == '__main__':
    # create an XMLReader
    parser = xml.sax.make_parser()
    # turn off namepsaces
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)

    sfile = m3StructFile()
    sfile_name = 'structures.xml'
    # override the default ContextHandler
    Handler = m3StructHandler(sfile)
    parser.setContentHandler( Handler )

    print('Processing Structures.xml')
    parser.parse(sfile_name)

    out_file = open('m3.py', 'w')
    out_file.write('''
### ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ###
## This file was generated from structures.xml by m3struct.py          ##
## Any changes to this file will be lost when m3struct.py is run again ##
### ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ###
''')

    def parseSubField(struct, prefix_k, prefix_v, typ):
        for f in sfile.structByName[typ][IDX_FIELDS]:
            struct[prefix_k + f[Attr.NAME]] = prefix_v + f[Attr.NAME]
            size = m3Type.toSize(m3Type.fromName(f[Attr.TYPE]))
            if not Attr.SIZE in f and size==0:
                match = re.search('(.*)V([0-9]+)$',f[Attr.TYPE])
                if match:
                    n = match.group(1)
                else:
                    n = f[Attr.TYPE]
                if n in sfile.structByName:
                    parseSubField(struct, prefix_k + f[Attr.NAME] + '_', prefix_v + f[Attr.NAME] + SUB_STRUCT_DELIM, n)

    for s in sfile.structByName:
        struct = {}
        parseSubField(struct, '', '', s)
        out_file.write(f'class {s}:\n')
        for f in struct:
            out_file.write(f"    {f} = '{struct[f]}'\n")
