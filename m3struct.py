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
        num = int(obj[field])
        obj[field] = num

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
        CHAR: 'String'
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

class m3FieldInfo():
    def __init__(self, owner: m3StructInfo, type_name, name, offset) -> None:
        self.owner = owner
        self.type = m3Type.fromName(type_name)
        self.type_name = type_name
        self.name = name
        self.offset = offset
        self.default = None
        self.expected = None
        self.refTo = None
        self.size = 0

    def getInfoStr(self) -> str:
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
        if tag == TAG_CHAR:
            self.type = m3Type.CHAR
            self.simple = True
            self.item_size = 0
        elif not struct:
            self.type = m3Type.BINARY
            self.simple = True
            self.item_size = 0
        else:
            self.type = struct[IDX_TYPE]
            self.simple = struct[IDX_SIMPLE]
            if not self.simple:
                self.item_size = self.putSubStructureFields(structFile, struct, 0, '', ver)
            else:
                self.item_size = m3Type.toSize(self.type)

    def putSubStructureFields(self, structFile: m3StructFile, struct, offset, prefix, ver):
        if struct:
            for f in struct[IDX_FIELDS]:
                if Attr.SINCE_VER in f and f[Attr.SINCE_VER] > ver: continue
                if Attr.TILL_VER in f and f[Attr.TILL_VER] < ver: continue
                field = m3FieldInfo( self, f[Attr.TYPE], prefix + f[Attr.NAME], offset )
                if Attr.DEFAULT in f:
                    field.default = f[Attr.DEFAULT]
                if Attr.EXPECTED in f:
                    field.expected = f[Attr.EXPECTED]
                if Attr.REF_TO in f:
                    field.refTo = f[Attr.REF_TO]
                if Attr.SIZE in f:
                    size = f[Attr.SIZE]
                else:
                    size = m3Type.toSize(field.type)
                field.size = size
                if not self.hasRefs and field.type in (m3Type.REF, m3Type.REF_SMALL):
                    self.hasRefs = True
                self.fields.append(field)

                if size==0: # sub structure
                    match = re.search('(.*)V([0-9]+)$',f[Attr.TYPE])
                    if match:
                        n = match.group(1)
                        v = int(match.group(2))
                        field.type_name = n
                    else:
                        n = f[Attr.TYPE]
                        v = 0
                    offset = self.putSubStructureFields(structFile, structFile.ByName(n), offset, field.name+SUB_STRUCT_DELIM, v)
                else:
                    offset += size
        return offset

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
            if not Attr.TYPE in self.field: self.field[Attr.TYPE] = ''
        elif tag==Tag.BIT:
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

    for s in sfile.structByName:
        pass
