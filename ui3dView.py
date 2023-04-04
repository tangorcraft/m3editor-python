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
from struct import pack
import OpenGL.GL as gl
import OpenGL.GL.shaders as gls
from m3file import m3File, m3Tag
from m3struct import m3FieldInfo
from gl.glMath import glmMatrix44
from gl.glmHorCam import glmHorizontalCamera
import m3

def vec3_data(v1, v2, v3):
    return pack('<fff', v1, v2, v3)

class m3glWidget(QtWidgets.QOpenGLWidget):
    def __init__(self, parent) -> None:
        self.cam = glmHorizontalCamera(5.0, 0.0, 45.0, 0.0, 0.0, 0.0)
        self.perspective = glmMatrix44()
        self.wireframe = False
        self.m3 = None
        self.mouse_cap = Qt.MouseButton.NoButton
        self.mouse_X = 0
        self.mouse_Y = 0
        super().__init__(parent)

    def initializeGL(self) -> None:
        super().initializeGL()
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
        self.eye_pos = gl.glGetUniformLocation(self.prog, 'EyePos')
        gl.glEnable(gl.GL_DEPTH_TEST)
        self.vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self.vao)
        self.buff_vert = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.buff_vert)
        self.buff_face = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.buff_face)
        gl.glBindVertexArray(0)

    def resizeGL(self, w: int, h: int) -> None:
        gl.glClearColor(0.0, 0.0, 0.4, 0.0)
        self.perspective.identPerspectiveDeg(45.0, w/h, 1.0, 500.0)
        #self.mvp_mat.mulMatrix44(self.cam.mat)
        gl.glViewport(0,0,w,h)
        return super().resizeGL(w, h)

    def paintGL(self) -> None:
        self._camStatUpdate()
        gl.glClear(gl.GL_DEPTH_BUFFER_BIT | gl.GL_COLOR_BUFFER_BIT)
        if not self.prog: return
        if not self.m3: return
        final = glmMatrix44(self.perspective.mat, self.cam.mat)
        gl.glUseProgram(self.prog)
        # set uniform data
        gl.glUniformMatrix4fv(self.mvp, 1, gl.GL_FALSE, final.data())
        gl.glUniform3fv(self.light_back_vec, 1, vec3_data(*self.cam.back_v()))
        gl.glUniform3fv(self.eye_pos, 1, vec3_data(*self.cam.eye_pos))
        # set vertex data
        gl.glBindVertexArray(self.vao)
        gl.glEnableVertexAttribArray(0)
        gl.glEnableVertexAttribArray(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.buff_vert)
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, self.vert_stride, None) # position
        gl.glVertexAttribPointer(1, 4, gl.GL_UNSIGNED_BYTE, gl.GL_FALSE, self.vert_stride, gl.GLvoidp(self.vert_offset_normal)) # normal
        gl.glVertexAttribPointer(2, 2, gl.GL_SHORT, gl.GL_FALSE, self.vert_stride, None)#self.vert_offset_uv) # uv0
        # set faces data
        if self.wireframe:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
        else:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.buff_face)
        # draw
        for idx in range(0, self.m3regn.count):
            vi = self.m3regn.getFieldUnpackedByName(idx, m3.REGN.firstVertexIndex, '<I')
            if not vi: continue
            fi = self.m3regn.getFieldUnpackedByName(idx, m3.REGN.firstFaceVertexIndexIndex, '<I')
            if not fi: continue
            fn = self.m3regn.getFieldUnpackedByName(idx, m3.REGN.numberOfFaceVertexIndices, '<I')
            if not fn: continue
            gl.glDrawElementsBaseVertex(gl.GL_TRIANGLES, fn[0], gl.GL_UNSIGNED_SHORT, gl.GLvoidp(fi[0]*2), vi[0])
        gl.glDisableVertexAttribArray(0)
        gl.glDisableVertexAttribArray(1)

    def setM3(self, m3file: m3File):
        self.m3div = m3file.modl.getRefn(0, m3.MODL.divisions)
        if not self.m3div: return
        self.m3faces = self.m3div.getRefn(0, m3.DIV_.faces)
        if not self.m3faces: return
        self.m3regn = self.m3div.getRefn(0, m3.DIV_.regions)
        if not self.m3regn: return
        self.m3 = m3file
        self.vert_offset_normal = self.m3.vert.info.getFieldOffsetByName(m3.VertexFormat.normal)
        self.vert_offset_uv = self.m3.vert.info.getFieldOffsetByName(m3.VertexFormat.uv0)
        self.vert_stride = self.m3.vert.info.item_size
        self.vert_mem = bytes(self.m3.vert.data)
        self.face_mem = bytes(self.m3faces.data)
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
        d = a0.angleDelta().y() * -0.005
        if d:
            self.cam.modifyDistance(d)
            self.update()
            a0.accept()
        return super().wheelEvent(a0)
