from pyspades.constants import *
from pyspades.world import Grenade
from pyspades.server import grenade_packet
from pyspades.common import Vertex3
from pyspades.constants import UPDATE_FREQUENCY
import random

from twisted.internet import reactor
from twisted.internet.reactor import callLater

SPEED = 3

def apply_script(protocol,connection,config):
	class ArtilleryConnection(connection):
		def on_animation_update(self,jump,crouch,sneak,sprint):
			if sneak and self.world_object.secondary_fire:
				x, y, z = self.world_object.position.get()
				pos = Vertex3(x, y, z)
				a,b,c = self.world_object.orientation.get()
				exp_pos = Vertex3(x-a, y-b, z-c)
				a = a * SPEED
				b = b * SPEED
				c = c * SPEED
				forward = Vertex3(a, b, c)


		  	 	grenade_packet.value=0.0
		  		grenade_packet.player_id=self.player_id
		  		grenade_packet.position=exp_pos.get()
		  		grenade_packet.velocity=(0,0,0)
 				self.protocol.send_contained(grenade_packet)

				grenade = self.protocol.world.create_object(Grenade, 0.0, pos, None, forward, None)
				collision = grenade.get_next_collision(UPDATE_FREQUENCY)
				if collision:
					impact, x, y, z = collision

				self.protocol.world.create_object(Grenade, impact, pos, None, forward, None )
				grenade_packet.value = impact
				grenade_packet.player_id = self.player_id
				grenade_packet.position = pos.get()
				grenade_packet.velocity = (a,b,c)
				self.protocol.send_contained(grenade_packet)
				reactor.callLater(impact, self.high_explosive, x, y, z)
			return connection.on_animation_update(self,jump,crouch,sneak,sprint)

		def high_explosive(self,x,y,z):
			count = 0
			self.protocol.world.create_object(Grenade,count,Vertex3(x,y,z),None,Vertex3(0,0,0.001),self.grenade_exploded)
			grenade_packet.value=count
			grenade_packet.player_id=self.player_id
			grenade_packet.position=(x,y,z)
			grenade_packet.velocity=(0,0,0.001)
			self.protocol.send_contained(grenade_packet)
			self.explode=True

			while count<15: 
				reactor.callLater(count/100.0, self.makegre,x,y,z)				
				count+=1

			while count<0.15:						
				(xg,yg,zg)=(random.uniform(-0.5,0.5),random.uniform(-0.5,0.5),random.uniform(-0.5,0.5))
				dt=random.uniform(0,0.25)
				self.protocol.world.create_object(Grenade,count+dt,Vertex3(x,y,z),None,Vertex3(xg,yg,zg),self.grenade_exploded)
				grenade_packet.value=count+dt
				grenade_packet.player_id=self.player_id
				grenade_packet.position=(x,y,z)
				grenade_packet.velocity=(xg,yg,zg)
				self.protocol.send_contained(grenade_packet)
				count+=0.01

		def makegre(self,x,y,z):
				sigma=1.5
				(xg,yg,zg)=(random.gauss(0, sigma),random.gauss(0, sigma),random.gauss(0, sigma))
				xp, yp, zp = x+xg, y+yg, z+zg
				self.protocol.world.create_object(Grenade,0,Vertex3(xp,yp,zp),None,Vertex3(0,0,0),self.grenade_exploded)
				if random.uniform(-0.2,1.2)<0:
					grenade_packet.value=0
					grenade_packet.player_id=self.player_id
					grenade_packet.position=(xp,yp,zp)
					grenade_packet.velocity=(0,0,0)
					self.protocol.send_contained(grenade_packet)
	return protocol,ArtilleryConnection