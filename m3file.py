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
from struct import pack, pack_into, unpack_from, calcsize
from m3struct import m3FieldInfo, m3StructFile, m3StructInfo, m3Type,\
    TAG_HEADER_33, TAG_HEADER_34, TAG_HEADER_VER, TAG_CHAR, BINARY_DATA_ITEM_BYTES_COUNT
from common import ceildiv, getTagStepNeededBytes
import m3

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

FIELD_NOT_PART_OF_TAG = 'Field is not a part of tag structure'

REF_FROM_TAG = 0
REF_FROM_ITEM = 1
REF_FROM_FIELD = 2
REF_FROM_OFFSET = 3

SIZE_TO_FORMAT = {1: '<B', 2: '<H', 4: '<I'}

class m3FileError(Exception):
    pass

class m3Tag():
    def __init__(self, file: m3File, data: bytearray, index: int, tag: int, count: int, ver: int):
        self.file = file
        self.data = data
        self.idx = index
        self.tag = tag
        self.count = count
        # save original count, because vertices tag has U8__ type and is counted by bytes
        # the count property may change when parsing vflags and making vertex structure
        self.type_count = count
        self.ver = ver
        self.info = m3StructInfo(tag, ver, file.structs)
        self.refFrom = [] # type: List[Tuple]
        ''' RefFromTuple( tag_index, item_index, field_name, ref_data_absolute_offset) '''
        #if tag==m3struct.TAG_CHAR: pass
            # special case, 'data' contains a string of 'count-1' length + null-terminator (C string)
            # still, we should not decode it here, CHAR tag can contain binary data of unkown format (see MADD tag in structures.xml)
            # decoding should only happen after all references are resolved and it is certain 'data' content is a string

    def addRefFrom(self, tag_index, item_index, field: m3FieldInfo):
        if tag_index>0:
            self.refFrom.append((tag_index, item_index, field.name, field.getDataOffset(item_index)))
            if field.refToBinary:
                self.info.forceBinary()

    def getStr(self) -> str:
        if self.info.type == m3Type.CHAR:
            return self.data[:self.count-1].decode()
        else:
            return ''

    def isStr(self) -> bool:
        return True if self.info.type == m3Type.CHAR else False

    def setStr(self, value: str):
        if self.info.type == m3Type.CHAR:
            old_count = self.count
            self.data = bytearray(value, 'utf-8') + b'\x00'
            self.count = len(self.data)
            self.type_count = len(self.data)
            need = getTagStepNeededBytes(self.count)
            if need: self.data += b'\xaa'*need
            if old_count != self.count:
                for ref in self.refFrom: # update count in tags referencing this CHAR tag
                    tag = self.file.tags[ref[REF_FROM_TAG]]
                    pack_into('<I', tag.data, ref[REF_FROM_OFFSET], self.count) # count is first uint32 in Reference structure

    def getItemName(self, item_idx = 0, with_prefix = True):
        if self.info.type == m3Type.CHAR:
            return f'"{self.getStr()}"'
        elif self.info.item_name_field and self.refIsValid(item_idx, self.info.item_name_field):
            return (f' {self.info.item_name_field.name} -> ' if with_prefix else '') + self.getReff(item_idx, self.info.item_name_field).getItemName()
        return ''

    def getFieldInfoStr(self, field: m3FieldInfo):
        if not field in self.info.fields:
            raise m3FileError(FIELD_NOT_PART_OF_TAG)
        if field.type == m3Type.CHAR:
            return f'Size = {self.count}'
        if field.type == m3Type.BINARY:
            return f'Size = {field.size}'
        return field.getInfoStr()

    def getFieldAsStr(self, item_idx, field: m3FieldInfo) -> str:
        if not field in self.info.fields:
            raise m3FileError(FIELD_NOT_PART_OF_TAG)
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
            if field.type == m3Type.FIXED8:
                val = (val / 255.0) * 2 - 1
            if field.type == m3Type.FIXED16:
                val = val / 2048.0
            hex_size = m3Type.toSize(field.type) * 2
            return f'{val} (0x{hex:0{hex_size}x})'
        if field.type == m3Type.BIT:
            return f'0x{field.bitMask:0{field.size*2}x}'
        #if field.type == m3Type.BINARY:
        return self.getBinaryAsStr(offset, field.size)

    def getFieldAsUInt(self, item_idx, field: m3FieldInfo) -> int:
        if not field in self.info.fields:
            raise m3FileError(FIELD_NOT_PART_OF_TAG)
        if field.size in SIZE_TO_FORMAT:
            offset = self.info.item_size * item_idx + field.offset
            return unpack_from(SIZE_TO_FORMAT[field.size], self.data, offset)[0]

    def getFieldValue(self, item_idx, field: m3FieldInfo):
        if not field in self.info.fields:
            raise m3FileError(FIELD_NOT_PART_OF_TAG)
        fmt = m3Type.toFormat(field.type)
        if fmt:
            offset = self.info.item_size * item_idx + field.offset
            return unpack_from(fmt, self.data, offset)[0]

    def getFieldValueByName(self, item_idx, field_name: str):
        field = self.info.getFieldByName(field_name)
        if field:
            fmt = m3Type.toFormat(field.type)
            if fmt:
                offset = self.info.item_size * item_idx + field.offset
                return unpack_from(fmt, self.data, offset)[0]

    def getFieldUnpacked(self, item_idx, field: m3FieldInfo, unpack_format):
        if not field in self.info.fields:
            raise m3FileError(FIELD_NOT_PART_OF_TAG)
        offset = self.info.item_size * item_idx + field.offset
        return unpack_from(unpack_format, self.data, offset)

    def getFieldUnpackedByName(self, item_idx, field_name: str, unpack_format):
        field = self.info.getFieldByName(field_name)
        if field:
            offset = self.info.item_size * item_idx + field.offset
            return unpack_from(unpack_format, self.data, offset)

    def getBinaryAsStr(self, offset, size):
        end_offset = offset + min(size, BINARY_DATA_ITEM_BYTES_COUNT)
        data_list = [f'{x:02x}' for x in self.data[offset:end_offset]]
        for i in range(4, len(data_list), 4):
            data_list[i] = ' ' + data_list[i]
        if size > BINARY_DATA_ITEM_BYTES_COUNT:
            data_list.append('...')
        return ' '.join(data_list)

    def checkBitState(self, item_idx, field: m3FieldInfo) -> bool:
        if not field in self.info.fields:
            raise m3FileError(FIELD_NOT_PART_OF_TAG)
        if field.type == m3Type.BIT and field.size in SIZE_TO_FORMAT:
            offset = self.info.item_size * item_idx + field.offset
            val = unpack_from(SIZE_TO_FORMAT[field.size], self.data, offset)[0]
            if val & field.bitMask == field.bitMask: return True
        return False

    def getReff(self, item_idx, field: m3FieldInfo) -> m3Tag:
        if not field in self.info.fields:
            raise m3FileError(FIELD_NOT_PART_OF_TAG)
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
            raise m3FileError(FIELD_NOT_PART_OF_TAG)
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
        with open(fileName,'rb') as file:
            self.data = bytearray(file.read())
            file.close()
        if not self.reloadFromData():
            raise m3FileError('M3 file header not found in file: '+fileName)

    def reloadFromData(self) -> bool:
        self.tags = [] # type: List[m3Tag]
        self.orphans = []
        self.modl = None # type: m3Tag | None
        self.vert = None # type: m3Tag | None
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
            self.vflags = self.modl.getFieldAsUInt(0, self.modl.info.getFieldByName(m3.MODL.vFlags))
            self.rebildRefFrom()
            return True
        else:
            return False
    
    def rebildRefFrom(self):
        for tag in self.tags:
            tag.refFrom.clear()
        for tag in self.tags:
            for idx in range(0, tag.count):
                for f in tag.info.fields:
                    if f.notSelfField and f.isRef() and tag.refIsValid(idx, f):
                        ref_tag = tag.getReff(idx, f)
                        ref_tag.addRefFrom(tag.idx, idx, f)
                        if f.refToVertices and tag == self.modl:
                            ref_tag.info.forceVertices(self.structs, self.vflags)
                            ref_tag.count = ref_tag.type_count // ref_tag.info.item_size
                            self.vert = ref_tag
        self.orphans.clear()
        for tag in self.tags:
            if len(tag.refFrom)==0 and tag != self.modl and tag.idx != 0: # exclude MODL and header tags
                self.orphans.append(tag.idx)

    def repackIntoData(self):
        idx_size =  calcsize('IIII') # tag, dataOffset, dataCount, version
        index = bytearray(idx_size * self.tag_count)
        pack_into('<IIII', index, 0, TAG_HEADER_34, 0, 1, TAG_HEADER_VER) # tag, dataOffset, dataCount, version

        offset = calcsize('IIIIII') # file header == header tag at idx = 0
        extra = getTagStepNeededBytes(offset)
        self.data = bytearray(offset) + b'\xaa'*extra # file header is empty now, it will be filled last
        offset += extra

        for idx in range(1, self.tag_count): # skip tag at idx = 0 (header)
            t = self.tags[idx]
            pack_into('<IIII', index, idx_size * idx,
                t.tag, offset, t.type_count, t.ver
            ) # tag, dataOffset, dataCount, version
            offset += len(t.data)
            self.data += t.data
        # put index at the end of data
        self.data += index
        # last: fill header info
        pack_into('<IIIIII', self.data, 0,
            TAG_HEADER_34, offset, self.tag_count, 1, self.modl.idx, 0
        ) # header tag, tag index offset, tag index item count, MODL ref (count, index, flags)

if __name__ == '__main__':
    #test = 'cyclone.m3'
    test = 'BeaconAttackPing_AC.m3'
    strFile = m3StructFile()
    strFile.loadFromFile('structures.xml')
    m3f = m3File(test, strFile)
    print(m3f.tag_count)
    dds = []
    for t in m3f.tags:
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

    printTagsTree(m3f.modl,0,'model')
