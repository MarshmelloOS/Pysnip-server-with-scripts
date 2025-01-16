from pyspades.constants import *
from pyspades.world import Grenade
from pyspades.server import grenade_packet
from pyspades.common import Vertex3
from pyspades.constants import UPDATE_FREQUENCY
import commands

SPEED = 2

def apply_script(protocol,connection,config):
    class GreLanConnection(connection):
        
        def on_shoot_set(self,fire):
            if self.tool == WEAPON_TOOL:
                if fire:
                    x, y, z = self.world_object.position.get()
                    pos = Vertex3(x, y, z+1)
                    fx, fy, fz = self.world_object.orientation.get()
                    fx *= SPEED
                    fy *= SPEED
                    fz *= SPEED
                    forward = Vertex3(fx, fy, fz)
                    grenade = self.protocol.world.create_object(Grenade, 0.0, pos, None, forward, None)
                    collision = grenade.get_next_collision(UPDATE_FREQUENCY)
                    if collision:
                        impact, x2, y2, z2 = collision
                    else:
                        impact = 1.0
                    self.protocol.world.create_object(Grenade, impact, pos, None, forward, self.grenade_exploded)
                    grenade_packet.value = impact
                    grenade_packet.player_id = self.player_id
                    grenade_packet.position = pos.get()
                    grenade_packet.velocity = (fx, fy, fz)
                    self.protocol.send_contained(grenade_packet)
                    fuse = 0.5
                    while fuse < impact:
                        self.protocol.world.create_object(Grenade, fuse, pos, None, forward, self.grenade_exploded)
                        grenade_packet.value = fuse
                        grenade_packet.player_id = self.player_id
                        grenade_packet.position = pos.get()
                        grenade_packet.velocity = (fx, fy, fz)
                        self.protocol.send_contained(grenade_packet)
                        fuse += 0.1
                else:
                    self.send_chat("Next Grenade stand by")
            return connection.on_shoot_set(self, fire)
    
    return protocol,GreLanConnection