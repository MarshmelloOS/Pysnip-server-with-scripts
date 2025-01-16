#*-* coding: utf-8

# Coded by ImChris
# imchris.tk
# ubge.org

from pyspades.server import *
from pyspades import world
from pyspades.constants import *

def apply_script(protocol, connection, config):
	class AIDSConnection(connection):
		crouch_count = 0
				
		def on_animation_update(self, jump, crouch, sneak, sprint):
			player_pos = self.world_object.position.get()
			if crouch:
				pl = self.world_object
				if pl is not None:
					for player in self.team.get_players():
						if player is not None and player.world_object.dead:
							mate = player.world_object
							if mate is not None:
								mate_pos = player.world_object.position.get()
								if collision_3d(pl.position.x,pl.position.y,pl.position.z,mate.position.x,mate.position.y, mate.position.z, 2):
									self.crouch_count += 1							
								if (self.crouch_count >= 3):
									player.spawn_call.cancel()
									player.spawn((pl.position.x,pl.position.y,pl.position.z))
									player.send_chat ('Voce foi ressuscitado por (%s).' % self.name)
									self.send_chat ('Voce ressuscitou (%s).' % player.name)
									self.crouch_count = 0
			return connection.on_animation_update(self,jump,crouch,sneak,sprint)	
								
	return protocol,AIDSConnection