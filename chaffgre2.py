from pyspades.constants import *
from pyspades.world import Grenade
from pyspades.server import grenade_packet
from pyspades.common import Vertex3
from pyspades.constants import UPDATE_FREQUENCY
import random
import commands
from commands import alias,admin, add, name, get_team, get_player,where_from
from twisted.internet import reactor
from twisted.internet.reactor import callLater
from math import sqrt,sin,asin, cos, acos, pi, tan,atan,degrees,radians,hypot,atan2,floor
from easyaos import *
from collections import deque

@alias('chaff')			
@name('togglechaff')		
def togglechaff(connection):
	connection.chaff = not connection.chaff
	if connection.chaff:
		return "chaff on"		
	else:
		return "chaff off"
add(togglechaff)

def apply_script(protocol,connection,config):
	class ChaffConnection(connection):
		chaff = False

		def chaffing(self,time,x,y,z):
			if time<10:
				dt=0.01
				time+=dt
				if z>0 and 0<x<511 and 0<y<511 and 	not self.protocol.map.get_solid(x,y,z):
					xx=x+random.uniform(-5,5)
					yy=y+random.uniform(-5,5)
					zz=z+random.uniform(-4,4)
					self.blk_oku(xx,yy,zz-1)			
					self.blk_oku(xx,yy,zz)			
					reactor.callLater(0.005, self.blk_kesu,xx,yy,zz-1)	
					reactor.callLater(dt+0.005, self.blk_kesu,xx,yy,zz)	
					if random.uniform(0,1)>0.9:
						grenade_packet.value=0
						grenade_packet.player_id=self.player_id
						grenade_packet.position=(xx,yy,z+random.uniform(5.5,9.5))
						grenade_packet.velocity=(0,0,0)
						self.protocol.send_contained(grenade_packet)			
				
				reactor.callLater(dt, self.chaffing,time,x,y,z)

		def grenade_exploded(self, grenade):
			if self.chaff:
				position = grenade.position
				x = position.x
				y = position.y
				z = position.z
				self.chaffing(0,x,y,z-10)	
				return False

			return connection.grenade_exploded(self, grenade)


		def blk_oku(self, x,y,z):
			if z>0 and 0<x<511 and 0<y<511:
				easyblock(self, (x,y,z), (250,250,251))

		def blk_kesu(self, x,y,z):
			if self.protocol.map.get_solid(x,y,z):
				if z>0 and 0<x<511 and 0<y<511:
					easyremove(self,(x,y,z))

	return protocol,ChaffConnection