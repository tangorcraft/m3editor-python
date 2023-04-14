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
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import *
from struct import pack, calcsize
from typing import List
import OpenGL.GL as gl
import OpenGL.GL.shaders as gls
from common import pack_all
from m3file import m3File, m3Tag
from m3struct import m3FieldInfo
from gl.glMath import glmMatrix44
from gl.glmHorCam import glmHorizontalCamera
import m3

def vec3_data(v1, v2, v3):
    return pack('<fff', v1, v2, v3)

class mainShader():
    def __init__(self) -> None:
        with open('modelEdit.frag','r') as file:
            frag = file.read()
            file.close()
        with open('modelEdit.vert','r') as file:
            vert = file.read()
            file.close()
        self.prog = gls.compileProgram(
            gls.compileShader(frag, gl.GL_FRAGMENT_SHADER),
            gls.compileShader(vert, gl.GL_VERTEX_SHADER)
        )
        self.mvp = gl.glGetUniformLocation(self.prog, 'MVP')
        self.light_back_vec = gl.glGetUniformLocation(self.prog, 'LightRay_reverse')
        self.light_pow = gl.glGetUniformLocation(self.prog, 'LightPower')
        self.light_min = gl.glGetUniformLocation(self.prog, 'LightMinimal')
        self.eye_pos = gl.glGetUniformLocation(self.prog, 'EyePos')

class helperShader():
    BONE_VS = pack_all('<f',
        # x,   y,   z,   r,   g,   b,
        0.00, 0.00, 0.00, 1.0, 1.0, 1.0, #0#
        0.01, 0.00, 0.00, 0.2, 0.2, 1.0, #1# x 0.2
        0.10, 0.00, 0.00, 0.2, 0.2, 1.0, #2# x 1.0
        0.01, 0.02, 0.00, 1.0, 0.2, 0.2, #3# y 0.2
        0.01, 0.00, 0.02, 0.2, 1.0, 0.2, #4# z 0.2
        0.01,-0.02, 0.00, 1.0, 1.0, 1.0, #5#-y 0.2
        0.01, 0.00,-0.02, 1.0, 1.0, 1.0, #6#-z 0.2
    )
    ''' packed vertices data (floats)'''
    BONE_STRIDE = calcsize('<f')*6
    BONE_COL_OFFSET = calcsize('<f')*3
    BONE_ELS = pack_all('<B',
        0, 1, 1, 2,
        0, 3, 3, 1, 3, 2,
        0, 4, 4, 1, 4, 2,
        0, 5, 5, 1, 5, 2,
        0, 6, 6, 1, 6, 2,
        3, 4, 4, 5, 5, 6, 6, 3,
    )
    ''' packed elements data (uint8, gl_lines)'''

    def __init__(self) -> None:
        with open('helper.frag','r') as file:
            frag = file.read()
            file.close()
        with open('helper.vert','r') as file:
            vert = file.read()
            file.close()
        self.prog = gls.compileProgram(
            gls.compileShader(frag, gl.GL_FRAGMENT_SHADER),
            gls.compileShader(vert, gl.GL_VERTEX_SHADER)
        )
        self.mvp = gl.glGetUniformLocation(self.prog, 'MVP')
        self.light_pow = gl.glGetUniformLocation(self.prog, 'LightPower')
        self.light_min = gl.glGetUniformLocation(self.prog, 'LightMinimal')
        self.eye_pos = gl.glGetUniformLocation(self.prog, 'EyePos')
        self.bone_vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self.bone_vao)
        self.bone_vert = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.bone_vert)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, self.BONE_VS, gl.GL_STATIC_DRAW)
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, self.BONE_STRIDE, None) # position
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, self.BONE_STRIDE, gl.GLvoidp(self.BONE_COL_OFFSET)) # color
        self.bone_lines = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.bone_lines)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, self.BONE_ELS, gl.GL_STATIC_DRAW)
        gl.glBindVertexArray(0)

    def drawBoneBegin(self, cam: glmHorizontalCamera, light_pow: float, light_min: float):
        gl.glUseProgram(self.prog)
        # set uniform data
        gl.glUniform3fv(self.eye_pos, 1, vec3_data(*cam.eye_pos))
        gl.glUniform1f(self.light_pow, light_pow)
        gl.glUniform1f(self.light_min, light_min)
        # set vertex data
        gl.glBindVertexArray(self.bone_vao)
        gl.glEnableVertexAttribArray(0)
        gl.glEnableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.bone_vert)
        # draw
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.bone_lines)

    def drawBone(self, mvp: glmMatrix44):
        gl.glUniformMatrix4fv(self.mvp, 1, gl.GL_FALSE, mvp.data())
        gl.glDrawElements(gl.GL_LINES, len(self.BONE_ELS), gl.GL_UNSIGNED_BYTE, None)

    def drawBoneEnd(self):
        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)

def listCheckState(l: List[Qt.CheckState]):
    ret = Qt.CheckState.Unchecked
    for i in l:
        if i == Qt.CheckState.Checked:
            return Qt.CheckState.Checked
        elif i == Qt.CheckState.PartiallyChecked:
            ret = Qt.CheckState.PartiallyChecked
    return ret

class glTreeItem():
    TYPE_ROOT = 0
    TYPE_BATCH = 1
    TYPE_BONE = 2
    def __init__(self, tree_idx, text, gl_item_type, type_item_idx = 0, parent = -1) -> None:
        self.tree_idx = tree_idx
        self.tree_row = 0
        self.text = text
        self.type = gl_item_type
        self.type_idx = type_item_idx
        self.parent = parent
        self.children = []

    def noticeChild(self, child):
        if child in self.children:
            return self.children.index(child)
        else:
            idx = len(self.children)
            self.children.append(child)
            return idx

    def dropChildren(self):
        self.children = []

class glViewTreeModel(QAbstractItemModel):
    def __init__(self, m3file: m3File = None) -> None:
        super().__init__(None)
        self.bat_root = glTreeItem(0, 'Mesh batches', glTreeItem.TYPE_ROOT)
        self.bone_root = glTreeItem(1, 'Bones', glTreeItem.TYPE_ROOT)
        self.root_list = [0, 1]
        self.setM3(m3file)

    def addNode(self, node_type, node_type_idx, text, parent = -1):
        idx = len(self.node_list)
        it = glTreeItem(idx, text, node_type, node_type_idx, parent)
        self.node_list.append(it)
        return it

    def getNode(self, idx):
        if idx in range(0, len(self.node_list)):
            return self.node_list[idx]

    def setM3(self, m3file: m3File = None):
        self.beginResetModel()
        try:
            # reset model vars
            self.bat_root.dropChildren()
            self.bone_root.dropChildren()
            self.node_list = [self.bat_root, self.bone_root]
            self.bat_list = [] # type: List[Qt.CheckState]
            self.bone_list = [] # type: List[Qt.CheckState]
            self.div = None
            self.bats = None
            self.bones = None
            self.regns = None
            self.m3 = None
            # get info from m3 file
            if not m3file: return
            # DIV_
            self.div = m3file.modl.getRefn(0, m3.MODL.divisions)
            if not self.div: return
            # BAT_
            self.bats = self.div.getRefn(0, m3.DIV_.batches)
            if not self.bats: return
            self.bat_list = [Qt.CheckState.Checked] * self.bats.count
            for idx in range(0, self.bats.count):
                it = self.addNode(glTreeItem.TYPE_BATCH, idx, f'BAT_#{self.bats.idx}[{idx}]', self.bat_root.tree_idx)
                it.tree_row = self.bat_root.noticeChild(it.tree_idx)
            # REGN
            self.regns = self.div.getRefn(0, m3.DIV_.regions)
            if not self.regns: return
            # BONE
            self.bones = m3file.modl.getRefn(0, m3.MODL.bones)
            if not self.bones: return
            self.bone_list = [Qt.CheckState.Checked] * self.bones.count
            bone_item_map = [None] * self.bones.count # type: List[glTreeItem]
            for idx in range(0, self.bones.count):
                it = self.addNode(glTreeItem.TYPE_BONE, idx, f'BONE#{self.bones.idx}[{idx}]', self.bone_root.tree_idx)
                bone_item_map[idx] = it
                parent = self.bones.getFieldValueByName(idx, m3.BONE.parent)
                if parent and parent in range(0, self.bones.count) and parent < idx: # don't allow parent index >= child index to avoid possible loops
                    it.parent = bone_item_map[parent].tree_idx
                    it.tree_row = bone_item_map[parent].noticeChild(it.tree_idx)
                else:
                    it.tree_row = self.bone_root.noticeChild(it.tree_idx)
            # Set m3
            self.m3 = m3file
        finally:
            self.endResetModel()

    def index(self, row: int, column: int, parent: QModelIndex) -> QModelIndex:
        if parent.isValid():
            it = self.getNode(parent.internalId())
            if it and row in range(0, len(it.children)):
                return self.createIndex(row, column, it.children[row])
        elif row in range(0, len(self.root_list)):
            return self.createIndex(row, column, self.root_list[row])
        return QModelIndex()

    def parent(self, child: QModelIndex) -> QModelIndex:
        if child.isValid():
            it = self.getNode(child.internalId())
            if it:
                parent = self.getNode(it.parent)
                if parent:
                    return self.createIndex(parent.tree_row, 0, it.parent)
        return QModelIndex()

    def rowCount(self, parent: QModelIndex) -> int:
        if parent.isValid():
            it = self.getNode(parent.internalId())
            if it:
                return len(it.children)
        else: return len(self.root_list)
        return 0

    def columnCount(self, parent: QModelIndex) -> int:
        return 1

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if index.isValid():
            it = self.getNode(index.internalId())
            if it.type==glTreeItem.TYPE_BATCH or it==self.bat_root: # only batches use tristate
                return super().flags(index) | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsUserTristate
        return super().flags(index) | Qt.ItemFlag.ItemIsUserCheckable

    def data(self, index: QModelIndex, role: int):
        if index.isValid():
            it = self.getNode(index.internalId())
            if it:
                if role == Qt.ItemDataRole.DisplayRole:
                    return it.text
                elif role == Qt.ItemDataRole.CheckStateRole:
                    if it == self.bat_root:
                        return listCheckState(self.bat_list)
                    elif it == self.bone_root:
                        return listCheckState(self.bone_list)
                    elif it.type == glTreeItem.TYPE_BATCH:
                        return self.bat_list[it.type_idx]
                    elif it.type == glTreeItem.TYPE_BONE:
                        return self.bone_list[it.type_idx]
        return QVariant()

    def setData(self, index: QModelIndex, value, role: int) -> bool:
        if index.isValid() and role == Qt.ItemDataRole.CheckStateRole:
            it = self.getNode(index.internalId())
            if it:
                if it == self.bat_root:
                    for i in range(0, len(self.bat_list)):
                        self.bat_list[i] = value
                        self.dataChanged.emit(QModelIndex(), QModelIndex(), [role])
                elif it == self.bone_root:
                    for i in range(0, len(self.bone_list)):
                        self.bone_list[i] = value
                        self.dataChanged.emit(QModelIndex(), QModelIndex(), [role])
                elif it.type == glTreeItem.TYPE_BATCH:
                    self.bat_list[it.type_idx] = value
                    # root check state can change, so update whole model data
                    self.dataChanged.emit(QModelIndex(), QModelIndex(), [role])
                elif it.type == glTreeItem.TYPE_BONE:
                    self.bone_list[it.type_idx] = value
                    self.dataChanged.emit(QModelIndex(), QModelIndex(), [role])
        return False

    def hasChildren(self, parent: QModelIndex) -> bool:
        if not parent.isValid(): return True
        it = self.getNode(parent.internalId())
        if it and len(it.children) > 0:
            return True
        return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole and section == 0:
            return 'Objects visibility'
        return QVariant()

class m3glWidget(QtWidgets.QOpenGLWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.mtree = glViewTreeModel()
        self.mtree.dataChanged.connect(lambda a0,a1,a2: self.update())
        self.cam = glmHorizontalCamera(5.0, 0.0, 45.0, 0.0, 0.0, 0.0)
        self.perspective = glmMatrix44()
        self.wireframe = False
        self.m3 = None
        self.mouse_cap = Qt.MouseButton.NoButton
        self.mouse_X = 0
        self.mouse_Y = 0
        self.light_pow = 10.0
        self.light_min = 0.3
        self.gl_init_done = False

    def initializeGL(self) -> None:
        super().initializeGL()
        self.main = mainShader()
        self.helper = helperShader()
        gl.glEnable(gl.GL_DEPTH_TEST)
        self.vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self.vao)
        self.buff_vert = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.buff_vert)
        self.buff_face = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.buff_face)
        gl.glBindVertexArray(0)
        self.gl_init_done = True
        if self.m3: self.updateM3Data()

    def resizeGL(self, w: int, h: int) -> None:
        gl.glClearColor(0.2, 0.2, 0.3, 0.0)
        self.perspective.identPerspectiveDeg(45.0, w/h, 1.0, 500.0)
        #self.mvp_mat.mulMatrix44(self.cam.mat)
        gl.glViewport(0,0,w,h)
        return super().resizeGL(w, h)

    def paintGL(self) -> None:
        self._camStatUpdate()
        gl.glClear(gl.GL_DEPTH_BUFFER_BIT | gl.GL_COLOR_BUFFER_BIT)
        if not self.main.prog: return
        if not self.m3: return
        final = glmMatrix44(self.perspective.mat, self.cam.mat)
        gl.glUseProgram(self.main.prog)
        # set uniform data
        gl.glUniformMatrix4fv(self.main.mvp, 1, gl.GL_FALSE, final.data())
        gl.glUniform3fv(self.main.light_back_vec, 1, vec3_data(*self.cam.back_v()))
        gl.glUniform3fv(self.main.eye_pos, 1, vec3_data(*self.cam.eye_pos))
        gl.glUniform1f(self.main.light_pow, self.light_pow)
        gl.glUniform1f(self.main.light_min, self.light_min)
        # set vertex data
        gl.glBindVertexArray(self.vao)
        gl.glEnableVertexAttribArray(0)
        gl.glEnableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.buff_vert)
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, self.vert_stride, None) # position
        gl.glVertexAttribPointer(1, 4, gl.GL_UNSIGNED_BYTE, gl.GL_FALSE, self.vert_stride, gl.GLvoidp(self.vert_offset_normal)) # normal
        gl.glVertexAttribPointer(2, 2, gl.GL_SHORT, gl.GL_FALSE, self.vert_stride, gl.GLvoidp(self.vert_offset_uv0)) # uv0
        # set faces data
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.buff_face)
        # draw mesh
        for idx in range(0, self.mtree.bats.count):
            state = self.mtree.bat_list[idx]
            if state == Qt.CheckState.Unchecked: continue
            regn_idx = self.mtree.bats.getFieldUnpackedByName(idx, m3.BAT_.regionIndex, '<H')
            if not regn_idx: continue
            regn_idx = regn_idx[0]
            vi = self.mtree.regns.getFieldUnpackedByName(regn_idx, m3.REGN.firstVertexIndex, '<I')
            if not vi: continue
            fi = self.mtree.regns.getFieldUnpackedByName(regn_idx, m3.REGN.faceArrayFirstVertexIndex, '<I')
            if not fi: continue
            fn = self.mtree.regns.getFieldUnpackedByName(regn_idx, m3.REGN.faceArrayNumberOfIndices, '<I')
            if not fn: continue
            if state == Qt.CheckState.Checked:
                gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
            else:
                gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
            gl.glDrawElementsBaseVertex(gl.GL_TRIANGLES, fn[0], gl.GL_UNSIGNED_SHORT, gl.GLvoidp(fi[0]*2), vi[0])
        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)
        # draw bones
        self.helper.drawBoneBegin(self.cam, self.light_pow, self.light_min)
        for idx in range(0, self.mtree.bones.count):
            if self.mtree.bone_list[idx] == Qt.CheckState.Unchecked: continue
            mat = glmMatrix44().loadFrom(self.m3iref.data, self.m3iref.info.item_size * idx)
            if not mat.invert(): continue
            self.helper.drawBone(glmMatrix44(self.perspective.mat, self.cam.mat, mat.mat))
        self.helper.drawBoneEnd()

    def setM3(self, m3file: m3File):
        self.mtree.setM3(m3file)
        self.m3 = None
        if not self.mtree.m3: return
        self.m3faces = self.mtree.div.getRefn(0, m3.DIV_.faces)
        if not self.m3faces: return
        self.m3iref = m3file.modl.getRefn(0, m3.MODL.absoluteInverseBoneRestPositions)
        if not self.m3iref: return
        self.m3 = m3file
        self.vert_offset_normal = self.m3.vert.info.getFieldOffsetByName(m3.VertexFormat.normal)
        self.vert_offset_uv0 = self.m3.vert.info.getFieldOffsetByName(m3.VertexFormat.uv0)
        self.vert_stride = self.m3.vert.info.item_size
        self.vert_mem = bytes(self.m3.vert.data)
        self.face_mem = bytes(self.m3faces.data)
        if self.gl_init_done: self.updateM3Data()

    def updateM3Data(self):
        self.makeCurrent()
        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.buff_vert)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, self.vert_mem, gl.GL_STATIC_DRAW)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.buff_face)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, self.face_mem, gl.GL_STATIC_DRAW)
        self.doneCurrent()
        self.resetCamera() # this will also call update()

    def _camStatUpdate(self):
        s = 'forw'
        for x in self.cam.forw_v:
            s += f' {x:f}'
        s += '; up'
        for x in self.cam.up_v:
            s += f' {x:f}'
        s += '; side'
        for x in self.cam.side_v:
            s += f' {x:f}'
        s += '; eye'
        for x in self.cam.eye_pos:
            s += f' {x:f}'
        self.setStatusTip(s)

    def resetCamera(self):
        self.cam.setAll(5.0, 0.0, 45.0, 0.0, 0.0, 0.0)
        self.update()

    def setLightPow(self, value):
        self.light_pow = value
        self.update()

    def setLightMin(self, value):
        self.light_min = value
        self.update()

    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.resetCamera()
        a0.accept()
        return super().mouseDoubleClickEvent(a0)

    def mouseMoveEvent(self, a0: QtGui.QMouseEvent) -> None:
        if a0.buttons() & self.mouse_cap:
            x = a0.globalX()
            y = a0.globalY()
            dX = 0.0
            dY = 0.0
            if self.mouse_X != x:
                dX = self.mouse_X - x
                self.mouse_X = x
            if self.mouse_Y != y:
                dY = y - self.mouse_Y
                self.mouse_Y = y
            if dX or dY:
                if self.mouse_cap == Qt.MouseButton.LeftButton:
                    self.cam.modifyAngles(dX * 0.5, dY * 0.5)
                elif self.mouse_cap == Qt.MouseButton.RightButton:
                    self.cam.modifyCenterLocal(dX * 0.01, dY * 0.01)
                self.update()
        return super().mouseMoveEvent(a0)

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.mouse_cap = a0.button()
        self.mouse_X = a0.globalX()
        self.mouse_Y = a0.globalY()
        a0.accept()
        return super().mousePressEvent(a0)

    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.mouse_cap = Qt.MouseButton.NoButton
        a0.accept()
        return super().mouseReleaseEvent(a0)

    def wheelEvent(self, a0: QtGui.QWheelEvent) -> None:
        d = a0.angleDelta().y() * -0.002
        if d:
            self.cam.modifyDistance(d)
            self.update()
            a0.accept()
        return super().wheelEvent(a0)
