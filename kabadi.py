"""
kabadi-kabadi-kabadi-

script by vippei , modified by yuyasato 20190119

"""
from pyspades.contained import BlockAction, SetColor
from pyspades.contained import *
from pyspades.server import *
from pyspades.common import *
from pyspades.constants import *
from random import randint
from twisted.internet.reactor import callLater, seconds


LINE_COLOR_MAIN=(255,0,0)
LINE_COLOR_SUB=(255,255,0)
LINE_X = 96

def apply_script(protocol, connection, config):
	class kabadiConnection(connection):
		pass

	class kabadiProtocol(protocol):
		KBDTMR_running = False
		def __init__(self, *arg, **kw):
			self.KBDTMR_running=False
			callLater(3,self.KBDTMRstart)

			return protocol.__init__(self, *arg, **kw)

		def KBDTMRstart(self):
			if not self.KBDTMR_running:
				self.KBDTMR_running=True
				self.KBDTMR()

		def pos_check(self):
			if self.KBDTMR_running:
				for player in self.green_team.get_players():
					if player and player.world_object:
						if player.world_object.position.x <= LINE_X:
							player.take_flag()
							player.capture_flag()
							player.set_hp(0)

		def KBDTMR(self):
			if self.KBDTMR_running:
				self.pos_check()
				callLater(0.2,self.KBDTMR)

		def on_flag_spawn(self, x, y, z, flag, entity_id):
			return 0, 0, 63

		def on_map_change(self, map):
			protocol.on_map_change(self, map)
			self.line_draw()

		def line_draw(self):
			x = LINE_X
			for y in range(512):
				for z in range(self.map.get_z(x,y),64):
					if self.map.get_solid(x,y,z):
						if self.map.is_surface(x,y,z):
							self.map.remove_point(x,y,z)
							self.map.set_point(x, y, z, LINE_COLOR_MAIN)
			for y in range(512):
				for z in range(self.map.get_z(x+1,y),64):
					if self.map.get_solid(x+1,y,z):
						if self.map.is_surface(x+1,y,z):
							self.map.remove_point(x+1,y,z)
							self.map.set_point(x+1, y, z, LINE_COLOR_SUB)
			for y in range(512):
				for z in range(self.map.get_z(x-1,y),64):
					if self.map.get_solid(x-1,y,z):
						if self.map.is_surface(x-1,y,z):
							self.map.remove_point(x-1,y,z)
							self.map.set_point(x-1, y, z, LINE_COLOR_SUB)
	return kabadiProtocol,kabadiConnection