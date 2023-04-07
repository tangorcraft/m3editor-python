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
from gl.glMath import _prepareLookAt, glmMatrix44, glmComputeNormalOfPlane, glmNormalizeVector
from common import clampf
import math

class glmHorizontalCamera(glmMatrix44):
    def __init__(self, distance: float, h_angle: float, v_angle: float, center_x: float, center_y: float, center_z: float):
        super().__init__()
        self.setAll(distance, h_angle, v_angle, center_x, center_y, center_z)

    def setAll(self, distance: float, h_angle: float, v_angle: float, center_x: float, center_y: float, center_z: float):
        self.distance = clampf(distance, 1.0, 100.0)
        self.h_angle = h_angle
        self.v_angle = clampf(v_angle, -180.0, 180.0)
        self.center = (center_x, center_y, center_z)
        self._update_mat()

    def _update_mat(self):
        h_angle = self.h_angle * math.pi / 180.0
        v_angle = self.v_angle * math.pi / 180.0
        # make 2d forw vector
        forw_x = math.cos(h_angle)
        forw_y = math.sin(h_angle)
        # side = forw x up
        self.side_v = glmComputeNormalOfPlane(
            forw_x, forw_y, 0.0,
            0.0, 0.0, 1.0
        )
        # calc actual forw vector and eye position
        v_cos = math.cos(v_angle)*self.distance
        self.forw_v = (forw_x*v_cos, forw_y*v_cos, -math.sin(v_angle)*self.distance)
        self.eye_pos = (self.center[0] - self.forw_v[0], self.center[1] - self.forw_v[1], self.center[2] - self.forw_v[2])
        self.forw_v = glmNormalizeVector(*self.forw_v)
        # recompute up = side x forward
        self.up_v = glmComputeNormalOfPlane(*self.side_v, *self.forw_v)
        self.mat = _prepareLookAt(
            *self.forw_v,
            *self.up_v,
            *self.side_v
        )
        self.translate(-self.eye_pos[0], -self.eye_pos[1], -self.eye_pos[2])

    def modifyDistance(self, delta: float):
        self.distance = clampf(self.distance+delta, 1.0, 100.0)
        self._update_mat()

    def modifyAngles(self, delta_h: float, delta_v: float):
        self.h_angle += delta_h
        if self.h_angle > 360.0: self.h_angle -= 360.0
        elif self.h_angle < 0.0: self.h_angle += 360.0
        self.v_angle = clampf(self.v_angle+delta_v, -180.0, 180.0)
        self._update_mat()

    def modifyCenter(self, delta_x: float, delta_y: float, delta_z: float):
        self.center = (self.center[0]+delta_x, self.center[1]+delta_y, self.center[2]+delta_z)
        self._update_mat()

    def modifyCenterLocal(self, delta_side: float, delta_z: float):
        self.center = (
            self.center[0]+self.side_v[0]*delta_side,
            self.center[1]+self.side_v[1]*delta_side,
            self.center[2]+delta_z
        )
        self._update_mat()

    def data(self):
        self._update_mat()
        return super().data()

    def back_v(self):
        return (-self.forw_v[0], -self.forw_v[1], -self.forw_v[2])
