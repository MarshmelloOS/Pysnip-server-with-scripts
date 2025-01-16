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
from pyspades import contained as loaders

grenade_packet = loaders.GrenadePacket()

@alias('sm')			
@name('togglesmoke')		
def togglesmoke(connection):
	connection.chaff = not connection.chaff
	if connection.chaff:
		return "next grenade set smoke grenade"		
	else:
		return "next grenade set normal grenade"
add(togglesmoke)

def apply_script(protocol,connection,config):
	class ChaffConnection(connection):
		chaff = False

		def chaffing(self,time,x,y,z,grenade):
			if time<10:
				dt=0.01
				time+=dt
				if z>0 and 0<x<511 and 0<y<511 and 	not self.protocol.map.get_solid(x,y,z):
					xx=x+random.uniform(-5,5)
					yy=y+random.uniform(-5,5)
					zz=z+random.uniform(-14,-6)
					stopper = 0
					while not(not self.protocol.map.get_solid(xx,yy,zz) and not self.protocol.map.get_solid(xx,yy,zz-1) and grenade.get_damage(Vertex3(xx,yy,zz))>0):
						xx=x+random.uniform(-5,5)
						yy=y+random.uniform(-5,5)
						zz=z+random.uniform(-14,-3)
						stopper+=1
						if stopper>30:
							break
					if stopper>30:
						while not(not self.protocol.map.get_solid(xx,yy,zz) and not self.protocol.map.get_solid(xx,yy,zz-1) and grenade.get_damage(Vertex3(xx,yy,zz))>0):
							xx=x+random.uniform(-5,5)
							yy=y+random.uniform(-5,5)
							zz=z+random.uniform(-10,-3)
							stopper+=1
							if stopper>60:
								break
					if stopper>60:
						while not(not self.protocol.map.get_solid(xx,yy,zz) and not self.protocol.map.get_solid(xx,yy,zz-1) and grenade.get_damage(Vertex3(xx,yy,zz))>0):
							xx=x+random.uniform(-5,5)
							yy=y+random.uniform(-5,5)
							zz=z+random.uniform(-5,0)
							stopper+=1
							if stopper>100:
								break
					if stopper<=100:
						self.blk_oku(xx,yy,zz-1)			
						self.blk_oku(xx,yy,zz)			
						reactor.callLater(0.005, self.blk_kesu,xx,yy,zz-1)	
						reactor.callLater(dt+0.005, self.blk_kesu,xx,yy,zz)	
						if random.uniform(0,1)>0.95:
							grenade_packet.value=0
							grenade_packet.player_id=self.player_id
							grenade_packet.position=(xx,yy,zz)
							grenade_packet.velocity=(0,0,0)
							self.protocol.send_contained(grenade_packet)			
				
				reactor.callLater(dt, self.chaffing,time,x,y,z,grenade)

		def smokegrenade_exploded(self, grenade):
			if self.chaff:
				self.chaff = False
				position = grenade.position
				x = position.x
				y = position.y
				z = position.z
				self.chaffing(0,x,y,z,grenade)

		def loader_received(self, loader):
			ret = True
			if self.player_id is not None:
				contained = load_client_packet(ByteReader(loader.data))
				if self.hp:
					world_object = self.world_object
					if contained.id == loaders.GrenadePacket.id:
						if self.chaff:
							ret = False
							
							if not self.grenades:
								return
							self.grenades -= 1
							if not self.is_valid_position(*contained.position):
								contained.position = self.world_object.position.get()
							if self.on_grenade(contained.value) == False:
								return
							grenade = self.protocol.world.create_object(
								world.Grenade, contained.value,
								Vertex3(*contained.position), None,
								Vertex3(*contained.velocity), self.smokegrenade_exploded)
							grenade.team = self.team
							self.on_grenade_thrown(grenade)
							if self.filter_visibility_data:
								return
							contained.player_id = self.player_id
							self.protocol.send_contained(contained, 
								sender = self)
			if ret:
				return connection.loader_received(self, loader)


		def blk_oku(self, x,y,z):
			if z>0 and 0<x<511 and 0<y<511:
				easyblock(self, (x,y,z), (250,250,251))

		def blk_kesu(self, x,y,z):
			if self.protocol.map.get_solid(x,y,z):
				if z>0 and 0<x<511 and 0<y<511:
					easyremove(self,(x,y,z))

	return protocol,ChaffConnection