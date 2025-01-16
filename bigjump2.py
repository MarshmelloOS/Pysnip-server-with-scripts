from twisted.internet import reactor
from pyspades.constants import *
from pyspades.common import Vertex3
from pyspades.world import Grenade
from pyspades.server import grenade_packet
import commands


def apply_script(protocol,connection,config):
	class FlightConnection(connection):
		flying = False
		z_time=0


		def flight_reset(self):
			self.flying = False

		def flight(self, x, y, z, z_time):
			if self.flying:
				x2, y2, z2 = self.world_object.orientation.get()
				xy_rate = 0.4 
				x += x2 * xy_rate
				y += y2 * xy_rate
				z_v=-0.1+z_time
				z += z_v
				z_time += 0.001

				x = (x + 511) % 511
				y = (y + 511) % 511

				if self.protocol.map.get_solid(x, y, z) or self.protocol.map.get_solid(x, y, z+1):
				#	player_pos=self.world_object.position
				#	grenade_packet.value=0.0
				#	grenade_packet.player_id=self.player_id
				#	grenade_packet.position=player_pos.get()
				#	grenade_packet.velocity=(0,0,0)
				#	self.protocol.send_contained(grenade_packet)
					self.flight_reset()

				self.set_location((x, y, z))
				reactor.callLater(0.01, self.flight, x, y, z,z_time)

		def on_spawn(self,pos):
			self.send_chat("V & Space douji oside daijanpu ")
			return connection.on_spawn(self,pos)
		
		def on_animation_update(self,jump,crouch,sneak,sprint):
			if not self.flying and jump:
				self.flying=True
				z_time=0
				x, y, z = self.world_object.position.get()
				self.flight(x, y, z,z_time) 
				
			return connection.on_animation_update(self,jump,crouch,sneak,sprint)
		
		
		def on_kill(self,killer,type,grenade):
			if self.flying:
				self.flying=False
			return connection.on_kill(self,killer,type,grenade)
		
		def on_team_leave(self):
			self.flying=False
			return connection.on_team_leave(self)
		
		def on_fall(self, damage):
			return False

		def on_disconnect(self):
			self.flying = False
			return connection.on_disconnect(self)
		
	return protocol, FlightConnection