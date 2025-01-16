from pyspades.constants import *
from pyspades.world import Grenade
from pyspades.server import grenade_packet
from pyspades.common import Vertex3

def apply_script(protocol,connection,config):
    class ClapConnection(connection):
        def on_grenade_thrown(self, grenade):
            if self.team == self.protocol.green_team:
                for player in self.protocol.blue_team.get_players():
                    if player.hp > 0:
                        pos = player.world_object.position
                        self.protocol.world.create_object(Grenade, 0.0, pos, None, Vertex3(), self.grenade_exploded)
                        grenade_packet.value=0.1
                        grenade_packet.player_id=self.player_id
                        grenade_packet.position=pos.get()
                        grenade_packet.velocity=(0, 0, 0)
                        self.protocol.send_contained(grenade_packet)
            return 0
        
        def on_hit(self, hit_amount, hit_player, type, grenade):
            if type == GRENADE_KILL:
                return 0
    return protocol,ClapConnection