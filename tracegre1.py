from pyspades.constants import *
from pyspades.world import Grenade
from pyspades.server import grenade_packet
from pyspades.common import Vertex3
from pyspades.constants import UPDATE_FREQUENCY
from twisted.internet.reactor import callLater
from twisted.internet import reactor
from pyspades.server import position_data
from commands import alias,add


def apply_script(protocol,connection,config):

	class GrainConnection(connection):


		def on_spawn(self, pos):
			self.grain(0)	
			connection.on_spawn(self, pos)


		def grain(self,kazu):
	                x, y, z = self.world_object.position.get()
	                pos = Vertex3(x, y, z+1.3)
	                gvector = Vertex3(0, 0, 0)
			kazu+=1
			if kazu==250:kazu=0
			print kazu
			time = 25
		#	self.protocol.world.create_object(Grenade, time, pos, None, gvector, self.grenade_exploded)
		        grenade_packet.value = time
	                grenade_packet.player_id = self.player_id
	                grenade_packet.position = pos.get()
	                grenade_packet.velocity = (0,0,0)
	                self.protocol.send_contained(grenade_packet)
			reactor.callLater(0.5,self.grain,kazu)
	return protocol, GrainConnection

