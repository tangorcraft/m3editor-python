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
import OpenGL.GL as gl
import OpenGL.GL.shaders as gls
from m3file import m3File, m3Tag
from m3struct import m3FieldInfo
import m3

class m3glWidget(QtWidgets.QOpenGLWidget):
    def __init__(self, parent) -> None:
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
        self.eye_forward = gl.glGetUniformLocation(self.prog, 'cam_forward')
        self.eye_pos = gl.glGetUniformLocation(self.prog, 'EyePos')
        self.light_pos = gl.glGetUniformLocation(self.prog, 'LightPos')
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
        return super().resizeGL(w, h)

    def paintGL(self) -> None:
        return super().paintGL()

    def setM3(self, m3: m3File):
        self.m3 = m3
