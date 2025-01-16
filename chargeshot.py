# -*- coding: utf-8 -*-

from pyspades.constants import *
from easyaos import *
from pyspades.weapon import WEAPONS
from pyspades.world import Grenade
from pyspades.server import grenade_packet
from pyspades.common import Vertex3
from pyspades.constants import UPDATE_FREQUENCY
import commands


def blust(connection, pos, dir, pow, speed, color):
	x, y, z = pos
	vx, vy, vz = dir
	x += speed * vx
	y += speed * vy
	z += speed * vz
	if x < 0 or x >= 512:
		return
	if y < 0 or y >= 512:
		return
	if z < 0 or z >= 62:
		return
	pos = (x, y, z)
	easyblock(connection, pos, color)
	easygre(connection, pos, (0, 0, 0), 0)
	easyremove(connection, pos)
	if pow > 0:
		reactor.callLater(0.03, blust, connection, pos, dir, pow-0.25, speed, color)
	else:
		connection.blusting = False
	


def apply_script(protocol,connection,config):
	class ChargeShotConnection(connection):
		charging = False
		start_ammo = 0
		orb = None
		orb_r = 15
		orb_g = 255
		orb_b = 0
		blusting = False
		
		def on_shoot_set(self,fire):
			if self.tool == WEAPON_TOOL and self.weapon == SMG_WEAPON:
				if fire:
					self.charging = fire
					self.start_ammo = self.weapon_object.current_ammo
				elif self.charging:
					self.charging = fire
					x, y, z = self.world_object.position.get()
					pos = (x, y, z)
					vx, vy, vz = self.world_object.orientation.get()
					dir = (vx, vy, vz)
					pow = self.start_ammo - self.weapon_object.current_ammo
					speed = pow / 15.0
					color = (self.orb_r, self.orb_g, self.orb_b)
					self.blusting = True
					blust(self, pos, dir, pow, speed, color)
					self.start_ammo = 0
					self.orb_r = 15
					self.orb_g = 255
					self.orb_b = 0
					if self.orb is not None:
						easyremove(self, self.orb)
						self.orb = None
			return connection.on_shoot_set(self, fire)
		
		def on_orientation_update(self, vx, vy, vz):
			if self.charging:
				if self.orb is not None:
					easyremove(self, self.orb)
					if self.orb_r < 255:
						self.orb_r += 16
					elif self.orb_g > 0:
						self.orb_g -= 16
				x, y, z = self.world_object.position.get()
				dx = x + 2 * vx
				dy = y + 2 * vy
				dz = z + 2 * vz
				if dz < 0 or dz >= 62:
					return False
				if dx < 0 or dx >= 512:
					return False
				if dy < 0 or dy >= 512:
					return False
				self.orb = (dx, dy, dz)
				color = (self.orb_r, self.orb_g, self.orb_b)
				easyblock(self, self.orb, color)
			return connection.on_orientation_update(self, vx, vy, vz)
		
		def on_hit(self, damage, player, type, grenade):
			if type == GRENADE_KILL and self == player:
				if self.blusting:
					return False
			return connection.on_hit(self, damage, player, type, grenade)
		
		def on_tool_changed(self, tool):
			self.charging = False
			return connection.on_tool_changed(self, tool)
	return protocol,ChargeShotConnection