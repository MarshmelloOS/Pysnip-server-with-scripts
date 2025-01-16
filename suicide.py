#Suicide script by Kuma

from commands import add, admin, alias, get_player
from pyspades.server import grenade_packet
from pyspades.world import Grenade
from pyspades.common import Vertex3
from math import floor

DEAD = "You are already dead."

@alias('su')
def suicide(connection):
    protocol = connection.protocol
    if connection in protocol.players:
        obj = connection.world_object
        position = obj.position
	if connection.hp <= 0:
            connection.send_chat(DEAD)
	else:
            grenade_spawn(connection, position.x, position.y, position.z, fuse = 0, z_block = 0)
			
add(suicide)

def grenade_spawn(connection, x, y, z, fuse = 1, z_block = 10): #This function was copied off from explode.py written by me
    protocol = connection.protocol
    x, y, z = floor(x), floor(y), floor(z) - z_block
    v_position = Vertex3(x, y, z)
    grenade = protocol.world.create_object(Grenade, fuse, v_position, None, Vertex3(0, 0, 0), connection.grenade_exploded)
    grenade_packet.player_id = connection.player_id
    grenade_packet.value = grenade.fuse
    grenade_packet.position = grenade.position.get()
    grenade_packet.velocity = grenade.velocity.get()
    protocol.send_contained(grenade_packet)

def apply_script(protocol, connection, config):
    return protocol, connection