from twisted.internet import reactor
from pyspades.constants import *
from pyspades.common import Vertex3


def apply_script(protocol,connection,config):
	class FlightConnection(connection):
		flying = False
		speed = 1.00
		hover = False
		le = False
		ri = False
		
		def flight_reset(self):
			self.flying = False
			self.speed = 0.25
			self.hover = False
			self.le = False
			self.ri = False
		
		def flight(self, x, y, z):
			if self.flying:
				if not self.hover:
					x2, y2, z2 = self.world_object.orientation.get()
					spd = self.speed
					if self.world_object.secondary_fire:
						spd /= 2
					x += x2 * spd
					y += y2 * spd
					z += z2 * spd
					if self.le:
						x += y2 * spd
						y -= x2 * spd
					if self.ri:
						x -= y2 * spd
						y += x2 * spd
					x = (x + 511) % 511
					y = (y + 511) % 511
					if self.protocol.map.get_solid(x, y, z) or self.protocol.map.get_solid(x, y, z+1):
						self.flight_reset()
					elif z < 0 or z > 63:
						self.flight_reset()
					if z < 10:
						self.send_chat("Flight Altitude is too high")
						self.send_chat("!!WARNING!!")
				self.set_location((x, y, z))
				reactor.callLater(0.01, self.flight, x, y, z)
		
		def on_spawn(self,pos):
			self.send_chat("JUMP TO TAKE OFF!!")
			return connection.on_spawn(self,pos)
		
		def on_animation_update(self,jump,crouch,sneak,sprint):
			if not self.flying and jump:
				self.flying=True
				x, y, z = self.world_object.position.get()
				self.flight(x, y, z)
			if self.flying:
				if sprint and self.speed < 8:
					self.speed *= 2.0
				elif sneak and self.speed > 0.25:
					self.speed /= 2.0
				elif crouch:
					self.hover = True
				elif self.hover and not crouch:
					self.hover = False
			return connection.on_animation_update(self,jump,crouch,sneak,sprint)
		
		def on_walk_update(self, fw, bw, le, ri):
			if self.flying:
				if fw:
					self.speed *= 2.0
				if bw:
					self.speed /= 2.0
				if le:
					self.le = True
				else:
					self.le = False
				if ri:
					self.ri = True
				else:
					self.ri = False
			return connection.on_walk_update(self, fw, bw, le, ri)
		
		def on_kill(self,killer,type,grenade):
			self.flying=False
			return connection.on_kill(self,killer,type,grenade)
		
		def on_team_leave(self):
			self.flying=False
			return connection.on_team_leave(self)
		
		def on_fall(self, damage):
			if self.flying:
				self.flight_reset
				return False
			else:
				return connection.on_fall(self, damage)
		
		def on_disconnect(self):
			self.flying = False
			return connection.on_disconnect(self)
		
		def on_secondary_fire_set(self, bool):
			if bool:
				self.flying = True
				x, y, z = self.world_object.position.get()
				self.flight(x, y, z)
			return connection.on_secondary_fire_set(self, bool)
	
	return protocol, FlightConnection