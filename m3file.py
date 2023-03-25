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
from typing import List, Tuple
from struct import pack, unpack_from, calcsize
from m3struct import m3FieldInfo, m3StructFile, m3StructInfo, m3Type, TAG_HEADER_33, TAG_HEADER_34, TAG_CHAR, BINARY_DATA_ITEM_BYTES_COUNT

INDEX_REF_SIZE = calcsize('<IIII') # tag, dataOffset, dataCount, version
# index item fields, first 3 also match header fields
IDX_TAG = 0
IDX_OFFSET = 1
IDX_COUNT = 2
IDX_VER = 3
# header fields at index 3,4,5 are MODL ref (count, index, flags)
#IDX_REF_MODL_COUNT = 3
IDX_REF_MODL_INDEX = 4
#IDX_REF_MODL_FLAGS = 5

RefFromTuple = Tuple[int, int, int]
''' Tuple( tag_index, item_index, field_index) '''

class m3FileError(Exception):
    pass

class m3Tag():
    def __init__(self, file: m3File, data: bytes, index: int, tag: int, count: int, ver: int):
        self.file = file
        self.data = data
        self.idx = index
        self.tag = tag
        self.count = count
        self.ver = ver
        self.info = m3StructInfo(tag, ver, file.structs)
        self.refFrom = [] # type: List[RefFromTuple]
        #if tag==m3struct.TAG_CHAR: pass
            # special case, 'data' contains a string of 'count-1' length + null-terminator (C string)
            # still, we should not decode it here, CHAR tag can contain binary data of unkown format (see MADD tag in structures.xml)
            # decoding should only happen after all references are resolved and it is certain 'data' content is a string

    def addRefFrom(self, tag_index, item_index, field: m3FieldInfo):
        if tag_index>0:
            self.refFrom.append((tag_index, item_index, field.getIndex()))
            if field.refToBinary:
                self.info.forceBinary()

    def getStr(self) -> str:
        if self.info.type == m3Type.CHAR:
            return self.data[:self.count-1].decode()
        else:
            return ''

    def getFieldInfoStr(self, field: m3FieldInfo):
        if not field in self.info.fields:
            raise m3FileError('Field not part of tag structure')
        if field.type == m3Type.CHAR:
            return f'Size = {self.count}'
        if field.type == m3Type.BINARY:
            return f'Size = {field.size}'
        return field.getInfoStr()

    def getFieldAsStr(self, item_idx, field: m3FieldInfo) -> str:
        if not field in self.info.fields:
            raise m3FileError('Field not part of tag structure')
        if field.type == m3Type.CHAR:
            return self.getStr()
        offset = field.getDataOffset(item_idx)
        if field.isRef():
            if field.type == m3Type.REF:
                ref = unpack_from('<III', self.data, offset) # count, index, flags(not used)
                s = f'idx={ref[1]}, cnt={ref[0]}, flag={ref[2]:x}'
            elif field.type == m3Type.REF_SMALL:
                ref = unpack_from('<II', self.data, offset) # count, index
                s = f'idx={ref[1]}, cnt={ref[0]}'
            if self.refIsValid(item_idx, field):
                refTag = self.getReff(item_idx, field)
                s += f' -> {refTag.info.name}#{refTag.idx}'
                if refTag.info.type == m3Type.CHAR:
                    s += f' "{refTag.getStr()}"'
            return s
        val = None
        if field.type in m3Type.SIMPLE:
            val = unpack_from(m3Type.toFormat(field.type), self.data, offset)[0]
            hex = unpack_from(m3Type.toHexFormat(field.type), self.data, offset)[0]
            hex_size = m3Type.toSize(field.type) * 2
            return f'{val} (0x{hex:0{hex_size}x})'
        #if field.type == m3Type.BINARY:
        return self.getBinaryAsStr(offset, field.size)

    def getBinaryAsStr(self, offset, size):
        end_offset = offset + min(size, BINARY_DATA_ITEM_BYTES_COUNT)
        data_list = [f'{x:02x}' for x in self.data[offset:end_offset]]
        for i in range(4, len(data_list), 4):
            data_list[i] = ' ' + data_list[i]
        if size > BINARY_DATA_ITEM_BYTES_COUNT:
            data_list.append('...')
        return ' '.join(data_list)

    def getReff(self, item_idx, field: m3FieldInfo) -> m3Tag:
        if not field in self.info.fields:
            raise m3FileError('Field is not a part of tag structure')
        if not field.isRef():
            raise m3FileError(f'Field is not a reference ({field.type_name})')
        offset = field.getDataOffset(item_idx)
        ref = unpack_from('<II', self.data, offset) # count, index, flags(not used)
        if ref[0]>0 and ref[1] in range(1, self.file.tag_count):
            try:
                return self.file.tags[ref[1]]
            except IndexError:
                raise m3FileError(f'Ref Index out of bounds: {self.info.name}#{self.idx}[{item_idx}] - {field.name} = {ref[1]}')
        raise m3FileError(f'Trying to get tag from null reference: {self.info.name}#{self.idx}[{item_idx}] - {field.name}')

    def getRefn(self, item_idx, field_name) -> m3Tag:
        for f in self.info.fields:
            if f.name == field_name:
                return self.getReff(item_idx,f)
        raise m3FileError(f'Field name {field_name} not found in {self.info.name}#{self.idx}')

    def getRefi(self, item_idx, field_idx) -> m3Tag:
        if field_idx >= len(self.info.fields):
            raise m3FileError('Field index out of bounds')
        return self.getReff(item_idx, self.info.fields[field_idx])

    def refIsValid(self, item_idx, field: m3FieldInfo) -> bool:
        if not field in self.info.fields:
            raise m3FileError('Field not part of tag structure')
        if not field.isRef():
            raise m3FileError(f'Field is not a reference ({field.type_name})')
        offset = field.getDataOffset(item_idx)
        ref = unpack_from('<II', self.data, offset) # count, index, flags(not used)
        if ref[0]>0 and ref[1] in range(1, self.file.tag_count):
            return True
        else:
            return False

class m3File():
    def __init__(self, fileName, structFile: m3StructFile):
        self.structs = structFile
        self.tags = [] # type: List[m3Tag]
        self.orphans = []
        self.modl = None # type: m3Tag | None
        with open(fileName,'rb') as file:
            self.data = file.read()
            file.close()
        # reading header
        h = unpack_from('<IIIIII',self.data) # header tag, tag index offset, tag index item count, MODL ref (count, index, flags)
        if h[IDX_TAG]==TAG_HEADER_33 or h[IDX_TAG]==TAG_HEADER_34:
            self.tag_count = h[IDX_COUNT]
            index = self.data[h[IDX_OFFSET]:]
            items = []
            for i in range(0,self.tag_count):
                items.append(unpack_from('<IIII',index,INDEX_REF_SIZE*i)) # tag, dataOffset, dataCount, version
            for i in range(0,self.tag_count):
                offset = items[i][IDX_OFFSET]
                if i==(self.tag_count-1):
                    endOffset = h[IDX_OFFSET]
                else:
                    endOffset = items[i+1][IDX_OFFSET]
                self.tags.append(m3Tag(self, self.data[offset:endOffset], i, items[i][IDX_TAG], items[i][IDX_COUNT], items[i][IDX_VER]))
            self.modl = self.tags[h[IDX_REF_MODL_INDEX]]
            self.rebildRefFrom()
        else:
            raise m3FileError('M3 file header not found in file: '+fileName)
    
    def rebildRefFrom(self):
        for tag in self.tags:
            tag.refFrom.clear()
        for tag in self.tags:
            for idx in range(0, tag.count):
                for f in tag.info.fields:
                    if f.notSelfField and f.isRef() and tag.refIsValid(idx, f):
                        tag.getReff(idx, f).addRefFrom(tag.idx, idx, f)
        self.orphans.clear()
        for tag in self.tags:
            if len(tag.refFrom)==0 and tag != self.modl and tag.idx != 0: # exclude MODL and header tags
                self.orphans.append(tag.idx)

if __name__ == '__main__':
    #test = 'cyclone.m3'
    test = 'BeaconAttackPing_AC.m3'
    strFile = m3StructFile()
    strFile.loadFromFile('structures.xml')
    m3 = m3File(test, strFile)
    print(m3.tag_count)
    dds = []
    for t in m3.tags:
        if t.tag == TAG_CHAR:
            s = t.data[:t.count-1].decode()
            if s[-4:]=='.dds' and not s in dds: dds.append(s)
    for s in dds:
        print(s)

    def printTagsTree(first: m3Tag, ident, prefix):
        print('  '*ident + prefix, first.info.name, first.ver, first.count, first.getStr())
        for i in range(0,first.count):
            for f in first.info.fields:
                if f.type == m3Type.REF and first.refIsValid(i,f):
                    printTagsTree(first.getReff(i,f),ident+1,f.name)

    printTagsTree(m3.modl,0,'model')
