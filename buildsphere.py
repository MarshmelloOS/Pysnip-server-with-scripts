from pyspades.constants import *
from pyspades.server import Server
from commands import add, admin
from twisted.internet import reactor
import math

def build_sphere(connection, size):
    protocol = connection.protocol
    player_location = connection.world_object.position.get()
    center_x, center_y, center_z = int(player_location.x), int(player_location.y), int(player_location.z)

    for x in range(center_x - size, center_x + size + 1):
        for y in range(center_y - size, center_y + size + 1):
            for z in range(center_z - size, center_z + size + 1):
                if math.sqrt((x - center_x)**2 + (y - center_y)**2 + (z - center_z)**2) <= size:
                    protocol.map.set_point(x, y, z, BUILD_BLOCK)

@admin
def build_sphere_command(connection, size=5):
    try:
        size = int(size)
        if size < 1:
            connection.send_chat("Invalid size. Size must be a positive integer.")
            return
        build_sphere(connection, size)
        connection.send_chat("Sphere built with size {}".format(size))
    except ValueError:
        connection.send_chat("Invalid size. Size must be a positive integer.")

add(build_sphere_command)

def apply_script(protocol, connection, config):
    return protocol, connection
