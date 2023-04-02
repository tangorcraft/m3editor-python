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
from OpenGL.GL import *
from struct import pack, unpack, pack_into, unpack_from
from typing import List
import math

M44I0_0 = 0
M44I0_1 = 1
M44I0_2 = 2
M44I0_3 = 3
M44I1_0 = 4
M44I1_1 = 5
M44I1_2 = 6
M44I1_3 = 7
M44I2_0 = 8
M44I2_1 = 9
M44I2_2 = 10
M44I2_3 = 11
M44I3_0 = 12
M44I3_1 = 13
M44I3_2 = 14
M44I3_3 = 15
M44_CNT = 16

matrix44_list = List[float]
'''List of floats, must hold exactly 16 values that define 4x4 matrix'''

def glmNormalizeVector(*vect):
    '''Return normalized vector as tuple with same number of values as input'''
    tmp = 0
    for v in vect:
        tmp += v*v
    if tmp == 0: return vect # zero vector, return as is
    tmp = 1.0 / math.sqrt(tmp)
    return tuple(v*tmp for v in vect)

def glmComputeNormalOfPlane(vec1_x, vec1_y, vec1_z, vec2_x, vec2_y, vec2_z):
    '''Return normal of plane defined by 2 vectors as tuple (x, y, z)'''
    return (
    vec1_y*vec2_z-vec1_z*vec2_y,
    vec1_z*vec2_x-vec1_x*vec2_z,
    vec1_x*vec2_y-vec1_y*vec2_x
    )

def _identRotateRad(angle: float, x: float, y: float, z: float) -> matrix44_list:
    x, y, z = glmNormalizeVector(x, y, z)

    CosAngle = math.cos(angle)
    OneMinusCosAngle = 1.0 - CosAngle
    SinAngle = math.sin(angle)
    X_OneMinusCosAngle = x * OneMinusCosAngle
    Z_OneMinusCosAngle = z * OneMinusCosAngle

    return [
        x * X_OneMinusCosAngle + CosAngle,
        y * X_OneMinusCosAngle + z * SinAngle,
        z * X_OneMinusCosAngle - y * SinAngle,
        0.0,
        y * X_OneMinusCosAngle - z * SinAngle,
        y * y * OneMinusCosAngle + CosAngle,
        y * Z_OneMinusCosAngle + x * SinAngle,
        0.0,
        x * Z_OneMinusCosAngle + y * SinAngle,
        y * Z_OneMinusCosAngle - x * SinAngle,
        z * Z_OneMinusCosAngle + CosAngle,
        0.0,
        0.0, 0.0, 0.0, 1.0
    ]

def _identTranRotateRad(tran_x: float, tran_y: float, tran_z: float,
    angle: float, rot_x: float, rot_y: float, rot_z: float) -> matrix44_list:
    '''Translate Then Rotate'''
    rot_x, rot_y, rot_z = glmNormalizeVector(rot_x, rot_y, rot_z)

    CosAngle = math.cos(angle)
    OneMinusCosAngle = 1.0 - CosAngle
    SinAngle = math.sin(angle)
    X_OneMinusCosAngle = rot_x * OneMinusCosAngle
    Z_OneMinusCosAngle = rot_z * OneMinusCosAngle

    return [
        rot_x * X_OneMinusCosAngle + CosAngle,
        rot_y * X_OneMinusCosAngle + rot_z * SinAngle,
        rot_z * X_OneMinusCosAngle - rot_y * SinAngle,
        0.0,
        rot_y * X_OneMinusCosAngle - rot_z * SinAngle,
        rot_y * rot_y * OneMinusCosAngle + CosAngle,
        rot_y * Z_OneMinusCosAngle + rot_x * SinAngle,
        0.0,
        rot_x * Z_OneMinusCosAngle + rot_y * SinAngle,
        rot_y * Z_OneMinusCosAngle - rot_x * SinAngle,
        rot_z * Z_OneMinusCosAngle + CosAngle,
        0.0,
        tran_x, tran_y, tran_z, 1.0
    ]

def _identRotateTranRad(tran_x: float, tran_y: float, tran_z: float,
    angle: float, rot_x: float, rot_y: float, rot_z: float) -> matrix44_list:
    '''Rotate Then Translate'''
    m = _identRotateRad(angle, rot_x, rot_y, rot_z)
    m[M44I3_0] = m[M44I0_0]*tran_x + m[M44I1_0]*tran_y + m[M44I2_0]*tran_z
    m[M44I3_1] = m[M44I0_1]*tran_x + m[M44I1_1]*tran_y + m[M44I2_1]*tran_z
    m[M44I3_2] = m[M44I0_2]*tran_x + m[M44I1_2]*tran_y + m[M44I2_2]*tran_z
    return m

def _identRotateQuat(x: float, y: float, z: float, w: float) -> matrix44_list:
    n = 2.0/(x*x + y*y + z*z + w*w)
    return [
        1.0 - n*y*y - n*z*z,
        n*x*y + n*w*z,
        n*x*z - n*w*y,
        0,
        n*x*y - n*w*z,
        1.0 - n*x*x - n*z*z,
        n*y*z + n*w*x,
        0,
        n*x*z + n*w*y,
        n*y*z - n*w*x,
        1.0 - n*x*x - n*y*y,
        0,
        0.0, 0.0, 0.0, 1.0
    ]

def _prepareLookAt(forw_x, forw_y, forw_z, up_x, up_y, up_z, side_x, side_y, side_z) -> matrix44_list:
    return [
        side_x, up_x, -forw_x, 0.0,
        side_y, up_y, -forw_y, 0.0,
        side_z, up_z, -forw_z, 0.0,
           0.0,  0.0,     0.0, 1.0
    ]

def _identOrtho(left, right, bottom, top, znear, zfar) -> matrix44_list:
    tmpRmL = right - left
    tmpTmB = top - bottom
    tmpFmN = zfar - znear
    return [
        2.0 / tmpRmL, 0.0, 0.0, 0.0,
        0.0, 2.0 / tmpTmB, 0.0, 0.0,
        0.0, 0.0, -2.0 / tmpFmN, 0.0,
        -(right + left) / tmpRmL,
        -(top + bottom) / tmpTmB,
        -(zfar + znear) / tmpFmN,
        1.0
    ]

def _identFrustum(left, right, bottom, top, znear, zfar) -> matrix44_list:
    tmp2N = 2.0 * znear
    tmpRmL = right - left
    tmpTmB = top - bottom
    tmpFmN = zfar - znear
    return [
        tmp2N / tmpRmL, 0.0, 0.0, 0.0,
        0.0, tmp2N / tmpTmB, 0.0, 0.0,
        (right + left) / tmpRmL,
        (top + bottom) / tmpTmB,
        (-zfar - znear) / tmpFmN,
        -1.0,
        0.0, 0.0, (-tmp2N * zfar) / tmpFmN, 0.0
    ]

class glmMatrix44():
    def __init__(self, *source: matrix44_list):
        if len(source)==1:
            self.mat = source[0].copy()
        else:
            self.identity()
            for m in source:
                self.mulMatrix44(m)

    def __enter__(self):
        return self.mat

    def __exit__(self, err_type, value, traceback):
        pass

    def data(self):
        '''Return matrix as binary data that contain 16 float32 values in little-endian byte order'''
        return pack('<'+'f'*M44_CNT, *self.mat)

    def dataTo(self, buffer, offset):
        '''Write matrix as binary data that contain 16 float32 values in little-endian byte order'''
        pack_into('<'+'f'*M44_CNT, buffer, offset, *self.mat)

    def loadData(self, data):
        '''Initialize matrix from binary data that contain 16 float32 values in little-endian byte order'''
        self.mat = list(unpack('<'+'f'*M44_CNT, data))

    def loadDataFrom(self, buffer, offset):
        '''Initialize matrix from binary data that contain 16 float32 values in little-endian byte order'''
        self.mat = list(unpack_from('<'+'f'*M44_CNT, buffer, offset))

    @classmethod
    def load(cls, data):
        '''Create glmMatrix44 from binary data that contain 16 float32 values in little-endian byte order'''
        return glmMatrix44(list(unpack('<'+'f'*M44_CNT, data)))

    @classmethod
    def loadFrom(cls, buffer, offset):
        '''Create glmMatrix44 from binary data that contain 16 float32 values in little-endian byte order'''
        return glmMatrix44(list(unpack_from('<'+'f'*M44_CNT, buffer, offset)))

    def side(self):
        '''Return unit x vector of transformation matrix as (x, y, z) tuple'''
        return (self.mat[M44I0_0], self.mat[M44I0_1], self.mat[M44I0_2])

    def forward(self):
        '''Return unit y vector of transformation matrix as (x, y, z) tuple'''
        return (self.mat[M44I1_0], self.mat[M44I1_1], self.mat[M44I1_2])

    def up(self):
        '''Return unit z vector of transformation matrix as (x, y, z) tuple'''
        return (self.mat[M44I2_0], self.mat[M44I2_1], self.mat[M44I2_2])

    def origin(self):
        '''Return origin point of transformation matrix as (x, y, z) tuple'''
        if self.mat[M44I3_3]==1.0:
            factor = 1.0
        else:
            factor = 1.0 / self.mat[M44I3_3]
        return (self.mat[M44I3_0]*factor, self.mat[M44I3_1]*factor, self.mat[M44I3_2]*factor)

    def mulMatrix44(self, matrix: matrix44_list):
        '''Multiply current matrix by given matrix'''
        m1 = self.mat.copy()
        with self as m_result:
            m_result[M44I0_0]=m1[M44I0_0]*matrix[M44I0_0]+ m1[M44I1_0]*matrix[M44I0_1]+ m1[M44I2_0]*matrix[M44I0_2]+ m1[M44I3_0]*matrix[M44I0_3]
            m_result[M44I1_0]=m1[M44I0_0]*matrix[M44I1_0]+ m1[M44I1_0]*matrix[M44I1_1]+ m1[M44I2_0]*matrix[M44I1_2]+ m1[M44I3_0]*matrix[M44I1_3]
            m_result[M44I2_0]=m1[M44I0_0]*matrix[M44I2_0]+ m1[M44I1_0]*matrix[M44I2_1]+ m1[M44I2_0]*matrix[M44I2_2]+ m1[M44I3_0]*matrix[M44I2_3]
            m_result[M44I3_0]=m1[M44I0_0]*matrix[M44I3_0]+ m1[M44I1_0]*matrix[M44I3_1]+ m1[M44I2_0]*matrix[M44I3_2]+ m1[M44I3_0]*matrix[M44I3_3]

            m_result[M44I0_1]=m1[M44I0_1]*matrix[M44I0_0]+ m1[M44I1_1]*matrix[M44I0_1]+ m1[M44I2_1]*matrix[M44I0_2]+ m1[M44I3_1]*matrix[M44I0_3]
            m_result[M44I1_1]=m1[M44I0_1]*matrix[M44I1_0]+ m1[M44I1_1]*matrix[M44I1_1]+ m1[M44I2_1]*matrix[M44I1_2]+ m1[M44I3_1]*matrix[M44I1_3]
            m_result[M44I2_1]=m1[M44I0_1]*matrix[M44I2_0]+ m1[M44I1_1]*matrix[M44I2_1]+ m1[M44I2_1]*matrix[M44I2_2]+ m1[M44I3_1]*matrix[M44I2_3]
            m_result[M44I3_1]=m1[M44I0_1]*matrix[M44I3_0]+ m1[M44I1_1]*matrix[M44I3_1]+ m1[M44I2_1]*matrix[M44I3_2]+ m1[M44I3_1]*matrix[M44I3_3]

            m_result[M44I0_2]=m1[M44I0_2]*matrix[M44I0_0]+ m1[M44I1_2]*matrix[M44I0_1]+ m1[M44I2_2]*matrix[M44I0_2]+ m1[M44I3_2]*matrix[M44I0_3]
            m_result[M44I1_2]=m1[M44I0_2]*matrix[M44I1_0]+ m1[M44I1_2]*matrix[M44I1_1]+ m1[M44I2_2]*matrix[M44I1_2]+ m1[M44I3_2]*matrix[M44I1_3]
            m_result[M44I2_2]=m1[M44I0_2]*matrix[M44I2_0]+ m1[M44I1_2]*matrix[M44I2_1]+ m1[M44I2_2]*matrix[M44I2_2]+ m1[M44I3_2]*matrix[M44I2_3]
            m_result[M44I3_2]=m1[M44I0_2]*matrix[M44I3_0]+ m1[M44I1_2]*matrix[M44I3_1]+ m1[M44I2_2]*matrix[M44I3_2]+ m1[M44I3_2]*matrix[M44I3_3]

            m_result[M44I0_3]=m1[M44I0_3]*matrix[M44I0_0]+ m1[M44I1_3]*matrix[M44I0_1]+ m1[M44I2_3]*matrix[M44I0_2]+ m1[M44I3_3]*matrix[M44I0_3]
            m_result[M44I1_3]=m1[M44I0_3]*matrix[M44I1_0]+ m1[M44I1_3]*matrix[M44I1_1]+ m1[M44I2_3]*matrix[M44I1_2]+ m1[M44I3_3]*matrix[M44I1_3]
            m_result[M44I2_3]=m1[M44I0_3]*matrix[M44I2_0]+ m1[M44I1_3]*matrix[M44I2_1]+ m1[M44I2_3]*matrix[M44I2_2]+ m1[M44I3_3]*matrix[M44I2_3]
            m_result[M44I3_3]=m1[M44I0_3]*matrix[M44I3_0]+ m1[M44I1_3]*matrix[M44I3_1]+ m1[M44I2_3]*matrix[M44I3_2]+ m1[M44I3_3]*matrix[M44I3_3]

    def _mulMatrix44optimized33(self, matrix: matrix44_list):
        ### Optimized in case where 'matrix' is like this:
        ###  x x x 0
        ###  x x x 0
        ###  x x x 0
        ###  0 0 0 1 
        m1 = self.mat.copy()
        with self as m_result:
            m_result[M44I0_0]=m1[M44I0_0]*matrix[M44I0_0]+ m1[M44I1_0]*matrix[M44I0_1]+ m1[M44I2_0]*matrix[M44I0_2]
            m_result[M44I1_0]=m1[M44I0_0]*matrix[M44I1_0]+ m1[M44I1_0]*matrix[M44I1_1]+ m1[M44I2_0]*matrix[M44I1_2]
            m_result[M44I2_0]=m1[M44I0_0]*matrix[M44I2_0]+ m1[M44I1_0]*matrix[M44I2_1]+ m1[M44I2_0]*matrix[M44I2_2]
            # m_result[M44I3_0]=m1[M44I3_0]

            m_result[M44I0_1]=m1[M44I0_1]*matrix[M44I0_0]+ m1[M44I1_1]*matrix[M44I0_1]+ m1[M44I2_1]*matrix[M44I0_2]
            m_result[M44I1_1]=m1[M44I0_1]*matrix[M44I1_0]+ m1[M44I1_1]*matrix[M44I1_1]+ m1[M44I2_1]*matrix[M44I1_2]
            m_result[M44I2_1]=m1[M44I0_1]*matrix[M44I2_0]+ m1[M44I1_1]*matrix[M44I2_1]+ m1[M44I2_1]*matrix[M44I2_2]
            # m_result[M44I3_1]=m1[M44I3_1]

            m_result[M44I0_2]=m1[M44I0_2]*matrix[M44I0_0]+ m1[M44I1_2]*matrix[M44I0_1]+ m1[M44I2_2]*matrix[M44I0_2]
            m_result[M44I1_2]=m1[M44I0_2]*matrix[M44I1_0]+ m1[M44I1_2]*matrix[M44I1_1]+ m1[M44I2_2]*matrix[M44I1_2]
            m_result[M44I2_2]=m1[M44I0_2]*matrix[M44I2_0]+ m1[M44I1_2]*matrix[M44I2_1]+ m1[M44I2_2]*matrix[M44I2_2]
            # m_result[M44I3_2]=m1[M44I3_2]

            m_result[M44I0_3]=m1[M44I0_3]*matrix[M44I0_0]+ m1[M44I1_3]*matrix[M44I0_1]+ m1[M44I2_3]*matrix[M44I0_2]
            m_result[M44I1_3]=m1[M44I0_3]*matrix[M44I1_0]+ m1[M44I1_3]*matrix[M44I1_1]+ m1[M44I2_3]*matrix[M44I1_2]
            m_result[M44I2_3]=m1[M44I0_3]*matrix[M44I2_0]+ m1[M44I1_3]*matrix[M44I2_1]+ m1[M44I2_3]*matrix[M44I2_2]
            #m_result[M44I3_3]=m1[M44I3_3]

    def identity(self):
        '''Initialize matrix as identity matrix'''
        self.mat = [0.0]*M44_CNT
        self.mat[M44I0_0] = 1.0
        self.mat[M44I1_1] = 1.0
        self.mat[M44I2_2] = 1.0
        self.mat[M44I3_3] = 1.0

    def determinant(self):
        '''Return determinant: det(M)'''
        with self as m:
            return m[M44I0_0]*(
                m[M44I1_1]*m[M44I2_2]*m[M44I3_3]-m[M44I1_1]*m[M44I3_2]*m[M44I2_3]
                -m[M44I2_1]*m[M44I1_2]*m[M44I3_3]+m[M44I2_1]*m[M44I3_2]*m[M44I1_3]
                +m[M44I3_1]*m[M44I1_2]*m[M44I2_3]-m[M44I3_1]*m[M44I2_2]*m[M44I1_3] )\
            -m[M44I1_0]*(
                m[M44I0_1]*m[M44I2_2]*m[M44I3_3]-m[M44I0_1]*m[M44I3_2]*m[M44I2_3]
                -m[M44I2_1]*m[M44I0_2]*m[M44I3_3]+m[M44I2_1]*m[M44I3_2]*m[M44I0_3]
                +m[M44I3_1]*m[M44I0_2]*m[M44I2_3]-m[M44I3_1]*m[M44I2_2]*m[M44I0_3] )\
            +m[M44I2_0]*(
                m[M44I0_1]*m[M44I1_2]*m[M44I3_3]-m[M44I0_1]*m[M44I3_2]*m[M44I1_3]
                -m[M44I1_1]*m[M44I0_2]*m[M44I3_3]+m[M44I1_1]*m[M44I3_2]*m[M44I0_3]
                +m[M44I3_1]*m[M44I0_2]*m[M44I1_3]-m[M44I3_1]*m[M44I1_2]*m[M44I0_3] )\
            -m[M44I3_0]*(
                m[M44I0_1]*m[M44I1_2]*m[M44I2_3]-m[M44I0_1]*m[M44I2_2]*m[M44I1_3]
                -m[M44I1_1]*m[M44I0_2]*m[M44I2_3]+m[M44I1_1]*m[M44I2_2]*m[M44I0_3]
                +m[M44I2_1]*m[M44I0_2]*m[M44I1_3]-m[M44I2_1]*m[M44I1_2]*m[M44I0_3] )

    def invert(self):
        '''Try inverting current matrix, return True on success, return False if determinant is 0'''
        oneDivDet = self.determinant()
        if oneDivDet == 0:
            return False
        oneDivDet = 1.0 / oneDivDet
        with self as m:
            mcopy = m.copy() # type: List[float]
            m[M44I0_0] = oneDivDet * (
            mcopy[M44I1_1]*mcopy[M44I2_2]*mcopy[M44I3_3] -mcopy[M44I1_1]*mcopy[M44I3_2]*mcopy[M44I2_3]
            -mcopy[M44I2_1]*mcopy[M44I1_2]*mcopy[M44I3_3] +mcopy[M44I2_1]*mcopy[M44I3_2]*mcopy[M44I1_3]
            +mcopy[M44I3_1]*mcopy[M44I1_2]*mcopy[M44I2_3] -mcopy[M44I3_1]*mcopy[M44I2_2]*mcopy[M44I1_3]
            )
            m[M44I0_1] = -oneDivDet * (
            mcopy[M44I0_1]*mcopy[M44I2_2]*mcopy[M44I3_3] -mcopy[M44I0_1]*mcopy[M44I3_2]*mcopy[M44I2_3]
            -mcopy[M44I2_1]*mcopy[M44I0_2]*mcopy[M44I3_3] +mcopy[M44I2_1]*mcopy[M44I3_2]*mcopy[M44I0_3]
            +mcopy[M44I3_1]*mcopy[M44I0_2]*mcopy[M44I2_3] -mcopy[M44I3_1]*mcopy[M44I2_2]*mcopy[M44I0_3]
            )
            m[M44I0_2] = oneDivDet * (
            mcopy[M44I0_1]*mcopy[M44I1_2]*mcopy[M44I3_3] -mcopy[M44I0_1]*mcopy[M44I3_2]*mcopy[M44I1_3]
            -mcopy[M44I1_1]*mcopy[M44I0_2]*mcopy[M44I3_3] +mcopy[M44I1_1]*mcopy[M44I3_2]*mcopy[M44I0_3]
            +mcopy[M44I3_1]*mcopy[M44I0_2]*mcopy[M44I1_3] -mcopy[M44I3_1]*mcopy[M44I1_2]*mcopy[M44I0_3]
            )
            m[M44I0_3] = -oneDivDet * (
            mcopy[M44I0_1]*mcopy[M44I1_2]*mcopy[M44I2_3] -mcopy[M44I0_1]*mcopy[M44I2_2]*mcopy[M44I1_3]
            -mcopy[M44I1_1]*mcopy[M44I0_2]*mcopy[M44I2_3] +mcopy[M44I1_1]*mcopy[M44I2_2]*mcopy[M44I0_3]
            +mcopy[M44I2_1]*mcopy[M44I0_2]*mcopy[M44I1_3] -mcopy[M44I2_1]*mcopy[M44I1_2]*mcopy[M44I0_3]
            )

            m[M44I1_0] = -oneDivDet * (
            mcopy[M44I1_0]*mcopy[M44I2_2]*mcopy[M44I3_3] -mcopy[M44I1_0]*mcopy[M44I3_2]*mcopy[M44I2_3]
            -mcopy[M44I2_0]*mcopy[M44I1_2]*mcopy[M44I3_3] +mcopy[M44I2_0]*mcopy[M44I3_2]*mcopy[M44I1_3]
            +mcopy[M44I3_0]*mcopy[M44I1_2]*mcopy[M44I2_3] -mcopy[M44I3_0]*mcopy[M44I2_2]*mcopy[M44I1_3]
            )
            m[M44I1_1] = oneDivDet * (
            mcopy[M44I0_0]*mcopy[M44I2_2]*mcopy[M44I3_3] -mcopy[M44I0_0]*mcopy[M44I3_2]*mcopy[M44I2_3]
            -mcopy[M44I2_0]*mcopy[M44I0_2]*mcopy[M44I3_3] +mcopy[M44I2_0]*mcopy[M44I3_2]*mcopy[M44I0_3]
            +mcopy[M44I3_0]*mcopy[M44I0_2]*mcopy[M44I2_3] -mcopy[M44I3_0]*mcopy[M44I2_2]*mcopy[M44I0_3]
            )
            m[M44I1_2] = -oneDivDet * (
            mcopy[M44I0_0]*mcopy[M44I1_2]*mcopy[M44I3_3] -mcopy[M44I0_0]*mcopy[M44I3_2]*mcopy[M44I1_3]
            -mcopy[M44I1_0]*mcopy[M44I0_2]*mcopy[M44I3_3] +mcopy[M44I1_0]*mcopy[M44I3_2]*mcopy[M44I0_3]
            +mcopy[M44I3_0]*mcopy[M44I0_2]*mcopy[M44I1_3] -mcopy[M44I3_0]*mcopy[M44I1_2]*mcopy[M44I0_3]
            )
            m[M44I1_3] = oneDivDet * (
            mcopy[M44I0_0]*mcopy[M44I1_2]*mcopy[M44I2_3] -mcopy[M44I0_0]*mcopy[M44I2_2]*mcopy[M44I1_3]
            -mcopy[M44I1_0]*mcopy[M44I0_2]*mcopy[M44I2_3] +mcopy[M44I1_0]*mcopy[M44I2_2]*mcopy[M44I0_3]
            +mcopy[M44I2_0]*mcopy[M44I0_2]*mcopy[M44I1_3] -mcopy[M44I2_0]*mcopy[M44I1_2]*mcopy[M44I0_3]
            )

            m[M44I2_0] = oneDivDet * (
            mcopy[M44I1_0]*mcopy[M44I2_1]*mcopy[M44I3_3] -mcopy[M44I1_0]*mcopy[M44I3_1]*mcopy[M44I2_3]
            -mcopy[M44I2_0]*mcopy[M44I1_1]*mcopy[M44I3_3] +mcopy[M44I2_0]*mcopy[M44I3_1]*mcopy[M44I1_3]
            +mcopy[M44I3_0]*mcopy[M44I1_1]*mcopy[M44I2_3] -mcopy[M44I3_0]*mcopy[M44I2_1]*mcopy[M44I1_3]
            )
            m[M44I2_1] = -oneDivDet * (
            mcopy[M44I0_0]*mcopy[M44I2_1]*mcopy[M44I3_3] -mcopy[M44I0_0]*mcopy[M44I3_1]*mcopy[M44I2_3]
            -mcopy[M44I2_0]*mcopy[M44I0_1]*mcopy[M44I3_3] +mcopy[M44I2_0]*mcopy[M44I3_1]*mcopy[M44I0_3]
            +mcopy[M44I3_0]*mcopy[M44I0_1]*mcopy[M44I2_3] -mcopy[M44I3_0]*mcopy[M44I2_1]*mcopy[M44I0_3]
            )
            m[M44I2_2] = oneDivDet * (
            mcopy[M44I0_0]*mcopy[M44I1_1]*mcopy[M44I3_3] -mcopy[M44I0_0]*mcopy[M44I3_1]*mcopy[M44I1_3]
            -mcopy[M44I1_0]*mcopy[M44I0_1]*mcopy[M44I3_3] +mcopy[M44I1_0]*mcopy[M44I3_1]*mcopy[M44I0_3]
            +mcopy[M44I3_0]*mcopy[M44I0_1]*mcopy[M44I1_3] -mcopy[M44I3_0]*mcopy[M44I1_1]*mcopy[M44I0_3]
            )
            m[M44I2_3] = -oneDivDet * (
            mcopy[M44I0_0]*mcopy[M44I1_1]*mcopy[M44I2_3] -mcopy[M44I0_0]*mcopy[M44I2_1]*mcopy[M44I1_3]
            -mcopy[M44I1_0]*mcopy[M44I0_1]*mcopy[M44I2_3] +mcopy[M44I1_0]*mcopy[M44I2_1]*mcopy[M44I0_3]
            +mcopy[M44I2_0]*mcopy[M44I0_1]*mcopy[M44I1_3] -mcopy[M44I2_0]*mcopy[M44I1_1]*mcopy[M44I0_3]
            )

            m[M44I3_0] = -oneDivDet * (
            mcopy[M44I1_0]*mcopy[M44I2_1]*mcopy[M44I3_2] -mcopy[M44I1_0]*mcopy[M44I3_1]*mcopy[M44I2_2]
            -mcopy[M44I2_0]*mcopy[M44I1_1]*mcopy[M44I3_2] +mcopy[M44I2_0]*mcopy[M44I3_1]*mcopy[M44I1_2]
            +mcopy[M44I3_0]*mcopy[M44I1_1]*mcopy[M44I2_2] -mcopy[M44I3_0]*mcopy[M44I2_1]*mcopy[M44I1_2]
            )
            m[M44I3_1] = oneDivDet * (
            mcopy[M44I0_0]*mcopy[M44I2_1]*mcopy[M44I3_2] -mcopy[M44I0_0]*mcopy[M44I3_1]*mcopy[M44I2_2]
            -mcopy[M44I2_0]*mcopy[M44I0_1]*mcopy[M44I3_2] +mcopy[M44I2_0]*mcopy[M44I3_1]*mcopy[M44I0_2]
            +mcopy[M44I3_0]*mcopy[M44I0_1]*mcopy[M44I2_2] -mcopy[M44I3_0]*mcopy[M44I2_1]*mcopy[M44I0_2]
            )
            m[M44I3_2] = -oneDivDet * (
            mcopy[M44I0_0]*mcopy[M44I1_1]*mcopy[M44I3_2] -mcopy[M44I0_0]*mcopy[M44I3_1]*mcopy[M44I1_2]
            -mcopy[M44I1_0]*mcopy[M44I0_1]*mcopy[M44I3_2] +mcopy[M44I1_0]*mcopy[M44I3_1]*mcopy[M44I0_2]
            +mcopy[M44I3_0]*mcopy[M44I0_1]*mcopy[M44I1_2] -mcopy[M44I3_0]*mcopy[M44I1_1]*mcopy[M44I0_2]
            )
            m[M44I3_3] = oneDivDet * (
            mcopy[M44I0_0]*mcopy[M44I1_1]*mcopy[M44I2_2] -mcopy[M44I0_0]*mcopy[M44I2_1]*mcopy[M44I1_2]
            -mcopy[M44I1_0]*mcopy[M44I0_1]*mcopy[M44I2_2] +mcopy[M44I1_0]*mcopy[M44I2_1]*mcopy[M44I0_2]
            +mcopy[M44I2_0]*mcopy[M44I0_1]*mcopy[M44I1_2] -mcopy[M44I2_0]*mcopy[M44I1_1]*mcopy[M44I0_2]
            )
        return True

    def identTranslate(self, x: float, y: float, z: float):
        '''Initialize as translation matrix'''
        self.mat = [
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
              x,   y,   z, 1.0
        ]

    def translate(self, x: float, y: float, z: float):
        '''Add translation to matrix'''
        with self as m:
            m[M44I3_0] = m[M44I0_0]*x + m[M44I1_0]*y + m[M44I2_0]*z + m[M44I3_0]
            m[M44I3_1] = m[M44I0_1]*x + m[M44I1_1]*y + m[M44I2_1]*z + m[M44I3_1]
            m[M44I3_2] = m[M44I0_2]*x + m[M44I1_2]*y + m[M44I2_2]*z + m[M44I3_2]
            m[M44I3_3] = m[M44I0_3]*x + m[M44I1_3]*y + m[M44I2_3]*z + m[M44I3_3]

    def identScale(self, x: float, y: float, z: float):
        '''Initialize as scale matrix'''
        self.mat = [
              x, 0.0, 0.0, 0.0,
            0.0,   y, 0.0, 0.0,
            0.0, 0.0,   z, 0.0,
            0.0, 0.0, 0.0, 1.0
        ]

    def scale(self, x: float, y: float, z: float):
        '''Add scale to matrix'''
        with self as m:
            m[M44I0_0] *= x
            m[M44I0_1] *= x
            m[M44I0_2] *= x
            m[M44I0_3] *= x

            m[M44I1_0] *= y
            m[M44I1_1] *= y
            m[M44I1_2] *= y
            m[M44I1_3] *= y

            m[M44I2_0] *= z
            m[M44I2_1] *= z
            m[M44I2_2] *= z
            m[M44I2_3] *= z

    def identRotateRad(self, angle: float, x: float, y: float, z: float):
        '''Initialize as rotation matrix with rotation around vector (x, y, z) by angle (in radians)'''
        self.mat = _identRotateRad(angle, x, y, z)

    def identRotateDeg(self, angle: float, x: float, y: float, z: float):
        '''Initialize as rotation matrix with rotation around vector (x, y, z) by angle (in degrees)'''
        self.mat = _identRotateRad(angle * math.pi / 180.0, x, y, z)

    def identRotateQuat(self, x: float, y: float, z: float, w: float):
        '''Initialize as rotation matrix with quaternion (x, y, z, w) rotation'''
        self.mat = _identRotateQuat(x, y, z, w)

    def rotateRad(self, angle: float, x: float, y: float, z: float):
        '''Add rotation around vector (x, y, z) by angle (in radians) to matrix'''
        self._mulMatrix44optimized33( _identRotateRad(angle, x, y, z) )

    def rotateDeg(self, angle: float, x: float, y: float, z: float):
        '''Add rotation around vector (x, y, z) by angle (in degrees) to matrix'''
        self._mulMatrix44optimized33( _identRotateRad(angle * math.pi / 180., x, y, z) )

    def rotateQuat(self, x: float, y: float, z: float, w: float):
        '''Add quaternion (x, y, z, w) rotation to matrix'''
        self._mulMatrix44optimized33( _identRotateQuat(x, y, z, w) )

    def identLookAt_ECU(self, eye_x: float, eye_y: float, eye_z: float,
    center_x: float, center_y: float, center_z: float,
    up_vec_x: float, up_vec_y: float, up_vec_z: float):
        '''Initialize as Look At matrix using Center and Eye positions and Up vector'''
        forw_x, forw_y, forw_z = glmNormalizeVector(
            center_x - eye_x,
            center_y - eye_y,
            center_z - eye_z
        ) # forw = eye -> center
        # side = forw x up
        side_x, side_y, side_z = glmNormalizeVector(
            *glmComputeNormalOfPlane(forw_x, forw_y, forw_z, up_vec_x, up_vec_y, up_vec_z)
        )
        # recompute up = side x forward
        up_vec_x, up_vec_y, up_vec_z = glmComputeNormalOfPlane(side_x, side_y, side_z, forw_x, forw_y, forw_z)
        self.mat = _prepareLookAt(
            forw_x, forw_y, forw_z,
            up_vec_x, up_vec_y, up_vec_z,
            side_x, side_y, side_z
        )
        self.translate(-eye_x, -eye_y, -eye_z)

    def lookAt_ECU(self, eye_x: float, eye_y: float, eye_z: float,
    center_x: float, center_y: float, center_z: float,
    up_vec_x: float, up_vec_y: float, up_vec_z: float):
        '''Apply Look At transformation to matrix using Center and Eye positions and Up vector'''
        forw_x, forw_y, forw_z = glmNormalizeVector(
            center_x - eye_x,
            center_y - eye_y,
            center_z - eye_z
        ) # forw = eye -> center
        # side = forw x up
        side_x, side_y, side_z = glmNormalizeVector(
            *glmComputeNormalOfPlane(forw_x, forw_y, forw_z, up_vec_x, up_vec_y, up_vec_z)
        )
        # recompute up = side x forward
        up_vec_x, up_vec_y, up_vec_z = glmComputeNormalOfPlane(side_x, side_y, side_z, forw_x, forw_y, forw_z)
        self._mulMatrix44optimized33( _prepareLookAt(
            forw_x, forw_y, forw_z,
            up_vec_x, up_vec_y, up_vec_z,
            side_x, side_y, side_z
        ))
        self.translate(-eye_x, -eye_y, -eye_z)

    def identFrustum(self, left: float, right: float, bottom: float, top: float, znear: float, zfar: float):
        '''Initialize as frustum matrix'''
        self.mat = _identFrustum(left, right, bottom, top, znear, zfar)

    def identPerspectiveDeg(self, fov_y: float, aspect: float, znear: float, zfar: float):
        '''Initialize as perspective matrix with FoV angle in degrees and aspect ratio'''
        ymax = znear * math.tan(fov_y * math.pi / 360.0)
        xmax = ymax * aspect
        self.mat = _identFrustum(-xmax, xmax, -ymax, ymax, znear, zfar)

    def identPerspectiveBox(self, H: int, W: int, scale: float, znear: float, zfar: float):
        '''Initialize as perspective matrix with Height and Width sizes'''
        ymax = H // 2 * scale
        xmax = W // 2 * scale
        self.mat = _identFrustum(-xmax, xmax, -ymax, ymax, znear, zfar)

    def frustum(self, left: float, right: float, bottom: float, top: float, znear: float, zfar: float):
        '''Apply frustum to matrix'''
        self.mulMatrix44( _identFrustum(left, right, bottom, top, znear, zfar) )

    def perspectiveDeg(self, fov_y: float, aspect: float, znear: float, zfar: float):
        '''Apply perspective with FoV angle in degrees and aspect ratio to matrix'''
        ymax = znear * math.tan(fov_y * math.pi / 360.0)
        xmax = ymax * aspect
        self.mulMatrix44( _identFrustum(-xmax, xmax, -ymax, ymax, znear, zfar) )

    def perspectiveBox(self, H: int, W: int, scale: float, znear: float, zfar: float):
        '''Apply perspective with Height and Width sizes to matrix'''
        ymax = H // 2 * scale
        xmax = W // 2 * scale
        self.mulMatrix44( _identFrustum(-xmax, xmax, -ymax, ymax, znear, zfar) )

    def transform(self, x: float, y: float, z: float, w: float):
        '''Transform given 4 component vector using current matrix. Return 4 component vector as tuple (x, y, z, w)'''
        with self as m:
            return (
                x * m[M44I0_0] + y * m[M44I0_1] + z * m[M44I0_2] + w * m[M44I0_3],
                x * m[M44I1_0] + y * m[M44I1_1] + z * m[M44I1_2] + w * m[M44I1_3],
                x * m[M44I2_0] + y * m[M44I2_1] + z * m[M44I2_2] + w * m[M44I2_3],
                x * m[M44I3_0] + y * m[M44I3_1] + z * m[M44I3_2] + w * m[M44I3_3]
            )

    def transformPoint(self, x: float, y: float, z: float):
        '''Transform given 3 component point position using current matrix. Return point as tuple (x, y, z)'''
        x, y, z, w = self.transform(x, y, z, 1.0)
        w = 1.0 / w
        return (x * w, y * w, z * w)

    def transfromVector(self, x: float, y: float, z: float):
        '''Transform given 3 component vector using current matrix. Return 3 component vector as tuple (x, y, z)'''
        x, y, z, w = self.transform(x, y, z, 0.0)
        return (x, y, z)

if __name__ == '__main__':
    test = glmMatrix44()
    test.translate(9,5,3)
    test.rotateDeg(53,2,3,4)
    mat = test.data()
    print(mat)
    print(test.mat, test.determinant())
    test2 = glmMatrix44(test.mat)
    test.invert()
    print(test.mat, test.determinant())
    test.mulMatrix44(test2.mat)
    print(test.mat, test.determinant())
    mat = test.data()
    print(mat)
    v = glmNormalizeVector(0,1,1)
    print(v)