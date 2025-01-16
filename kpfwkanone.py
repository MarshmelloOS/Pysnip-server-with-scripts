from pyspades.constants import *
from pyspades.world import Grenade
from pyspades.server import grenade_packet
from pyspades.common import Vertex3
from pyspades.constants import UPDATE_FREQUENCY

SPEED = 5

def apply_script(protocol,connection,config):
    class GrenadeConnection(connection):
        def on_animation_update(self,jump,crouch,sneak,sprint):
            if sneak and self.world_object.secondary_fire:
                x, y, z = self.world_object.position.get()
                pos = Vertex3(x, y, z)
                a,b,c = self.world_object.orientation.get()
                a = a * SPEED
                b = b * SPEED
                c = c * SPEED
                forward = Vertex3(a, b, c)
		exp_pos = Vertex3(x-0.5*a, y-0.5*b, z-0.5*c)
  	 	grenade_packet.value=0.0
  		grenade_packet.player_id=self.player_id
  		grenade_packet.position=exp_pos.get()
  		grenade_packet.velocity=(0,0,0)
 	        self.protocol.send_contained(grenade_packet)
                grenade = self.protocol.world.create_object(Grenade, 0.0, pos, None, forward, None)
                collision = grenade.get_next_collision(UPDATE_FREQUENCY)
                if collision:
                    impact, x, y, z = collision
                self.protocol.world.create_object(Grenade, impact, pos, None, forward, self.grenade_exploded)
                grenade_packet.value = impact
                grenade_packet.player_id = self.player_id
                grenade_packet.position = pos.get()
                grenade_packet.velocity = (a,b,c)
                self.protocol.send_contained(grenade_packet)
            return connection.on_animation_update(self,jump,crouch,sneak,sprint)
    
    return protocol,GrenadeConnection