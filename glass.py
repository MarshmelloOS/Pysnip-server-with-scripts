from pyspades.constants import *
from pyspades.contained import BlockAction

GLASS_COLOR = (159,255,255)

def apply_script(protocol, connection, config):
	class ColorProtectConnection(connection):
		glass_now=[]
		def on_block_destroy(self, x, y, z, value):
			self.glass_now = []
			self.glass_waku = []
			if value == SPADE_DESTROY:
				for zz in [z-1,z,z+1]:
					if self.protocol.map.get_color(x, y, zz) == GLASS_COLOR:
						self.glass_break(x, y, zz)

			elif value == GRENADE_DESTROY:
				for xx in [x-1,x,x+1]:
					for yy in [y-1,y,y+1]:
						for zz in [z-1,y,z+1]:
							if self.protocol.map.get_color(xx, yy, zz) == GLASS_COLOR:
								self.glass_break(xx, yy, zz)

			elif self.protocol.map.get_color(x, y, z) == GLASS_COLOR:
				self.glass_break(x, y, z)

			if self.glass_waku != []:
				for (xx,yy,zz) in self.glass_waku:
					block_action = BlockAction()
					block_action.player_id = 32
					block_action.value = DESTROY_BLOCK
					block_action.x = xx
					block_action.y = yy
					block_action.z = zz
					self.protocol.send_contained(block_action)
			if self.glass_now != []:
				for (xx,yy,zz) in self.glass_now:
					self.protocol.map.remove_point(xx, yy, zz)
			self.glass_now = []
			self.glass_waku = []
			return connection.on_block_destroy(self, x, y, z, value)

		def glass_break(self, x,y,z):
			if self.protocol.map.get_color(x, y, z) == GLASS_COLOR:
				self.glass_now.append((x,y,z))
				if not ((self.protocol.map.get_color(x+1, y, z) == GLASS_COLOR or self.protocol.map.get_color(x+1, y, z) == None)
					and (self.protocol.map.get_color(x-1, y, z) == GLASS_COLOR or self.protocol.map.get_color(x-1, y, z) == None)
					and (self.protocol.map.get_color(x, y+1, z) == GLASS_COLOR or self.protocol.map.get_color(x, y+1, z) == None)
					and (self.protocol.map.get_color(x, y-1, z) == GLASS_COLOR or self.protocol.map.get_color(x, y-1, z) == None)
					and (self.protocol.map.get_color(x, y, z+1) == GLASS_COLOR or self.protocol.map.get_color(x, y, z+1) == None)
					and (self.protocol.map.get_color(x, y, z-1) == GLASS_COLOR or self.protocol.map.get_color(x, y, z-1) == None)):
						self.glass_waku.append((x,y,z))

				self.next_glass(x+1,y,z)
				self.next_glass(x-1,y,z)
				self.next_glass(x,y+1,z)
				self.next_glass(x,y-1,z)
				self.next_glass(x,y,z+1)
				self.next_glass(x,y,z-1)

		def next_glass(self, x,y,z):
			if not (x,y,z) in self.glass_now:
				self.glass_break(x,y,z)

		def on_block_build_attempt(self, x, y, z):
			if self.color == GLASS_COLOR:
				return False
			return connection.on_block_build_attempt(self, x, y, z)

		def on_line_build_attempt(self, points):
			if self.color == GLASS_COLOR:
				return False
			return connection.on_line_build_attempt(self, points)

	return protocol,ColorProtectConnection