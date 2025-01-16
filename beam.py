"""
godzilla
naikaku soujisyoku BEEEEEEAM
"""

from pyspades.server import block_action
from pyspades.common import Vertex3
from pyspades.constants import *
from pyspades.contained import BlockAction, SetColor
from commands import add, admin, get_player, name, alias, join_arguments
from pyspades.world import Grenade
from pyspades.server import grenade_packet
from pyspades.common import Vertex3
from pyspades.constants import UPDATE_FREQUENCY
from twisted.internet.reactor import callLater
from twisted.internet import reactor
from pyspades.server import position_data



def apply_script(protocol, connection, config):
	class BeamConnection(connection):
		
		def on_position_update(self):
			if self.world_object.sneak:
				self.beamfire()
			connection.on_position_update(self)
		
		def on_orientation_update(self, x, y, z):
			if self.world_object.sneak:
				self.beamfire()
			connection.on_orientation_update(self, x, y, z)
		
		def on_animation_update(self, jump, crouch, sneak, sprint):
			if sneak:
				self.beamfire()
				callLater(0.1, self.vroop)
			return connection.on_animation_update(self, jump, crouch, sneak, sprint)

		def vroop(self):
			if self.world_object.sneak:
				self.beamfire()
				callLater(0.0005, self.vroop)

		def beamfire(self):
			px=self.world_object.position.x
			py=self.world_object.position.y
			pz=self.world_object.position.z
			ox=self.world_object.orientation.x
			oy=self.world_object.orientation.y
			oz=self.world_object.orientation.z
			d=1
			for n in range(140):
				self.protocol.world.create_object(Grenade, 0, Vertex3(px+ox*d*n, py+oy*d*n, pz+oz*d*n), None, Vertex3(0,0,0), self.grenade_exploded)
		
	
	return protocol, BeamConnection