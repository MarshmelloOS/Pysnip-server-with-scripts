"""
sniper rifle

by yuyasato 20180108
"""


import commands
from pyspades.server import set_tool, weapon_reload, create_player, set_hp
from twisted.internet.reactor import callLater
from pyspades.server import position_data, orientation_data
from twisted.internet import reactor
from pyspades.constants import *
from pyspades.common import Vertex3
from pyspades.world import Grenade
from pyspades.server import grenade_packet
from collections import deque
import random
from commands import  alias,admin, add, name, get_team, get_player,where_from,invisible


def apply_script(protocol,connection,config):
	class StalkingConnection(connection):

		d=100

		def scope(self):
			if self.world_object:
				if self.tool == WEAPON_TOOL and self.world_object.secondary_fire:
					self.world_object.up=self.world_object.down=self.world_object.left=self.world_object.right=False
					self.freeze_animation = True
					xo,yo,zo=self.world_object.orientation.get()
					xp,yp,zp=self.world_object.position.get()

					magn=self.d

					xb,yb,zb = xp,yp,zp
					sol = None
					isol=magn
					for i in range(int(magn*3)):
						xb+=xo/3.0
						yb+=yo/3.0
						zb+=zo/3.0
						if self.protocol.map.get_solid(xb, yb, zb) or xb>511 or xb<0 or yb>511 or yb<0 or zb>63 or zb<-40:
							sol = (xb, yb, zb)
							isol=i
							break
					bk = self.world_object.cast_ray(magn)
					bki = self.world_object.cast_ray(i)

					if bk == None and sol==None:
						xo*=magn
						yo*=magn
						zo*=magn

						x,y,z=xp+xo,yp+yo,zp+zo	
					else:
						xo*=2
						yo*=2
						zo*=2

						if bki==None:
							x,y,z=sol[0]-xo, sol[1]-yo, sol[2]-zo
						else:
							x,y,z=bki[0]-xo, bki[1]-yo, bki[2]-zo
					position_data.x = x
					position_data.y = y
					position_data.z = z
					self.send_contained(position_data)
					reactor.callLater(0.001, self.scope)
				else:
					xp,yp,zp=self.world_object.position.get()
					position_data.x = xp
					position_data.y = yp
					position_data.z = zp
					self.send_contained(position_data)	
					self.freeze_animation = False
					

		def on_secondary_fire_set(self, secondary):
			if self.tool == WEAPON_TOOL and secondary:
				self.freeze_animation = True
				reactor.callLater(0.001, self.scope)
			return connection.on_secondary_fire_set(self, secondary)

	return protocol, StalkingConnection