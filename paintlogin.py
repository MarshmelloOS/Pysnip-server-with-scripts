"""
Lets you change the color of the block you are looking at.
/paint [player] enables painting mode for the player.

With block tool selected, pick a color, then hold down sneak key
(<V> by default) to paint.

Maintainer: hompy

MOD CRASIVE
/fill r=None g=None b=None
Must be loaded with "mapmakingtools.py".
"""

from pyspades.server import block_action
from pyspades.common import Vertex3
from pyspades.constants import *
from pyspades.contained import BlockAction, SetColor
from commands import add, admin, get_player, name, alias, join_arguments

PAINT_RAY_LENGTH = 120.0

@admin
def make_color(r, g, b, a):
    return b | (g << 8) | (r << 16) | (int((a / 255.0) * 128) << 24)

@admin
def make_color_tuple(color):
    return make_color(color[0], color[1], color[2], 255)

@admin
def set_color(prt, color):
    c = SetColor()
    c.player_id = 32
    c.value = color
    prt.send_contained(c)

@alias('@')
@name('paint')
@admin
def paint(connection, player = None):
    protocol = connection.protocol
    if player is not None:
        player = get_player(protocol, player)
    elif connection in protocol.players:
        player = connection
    else:
        raise ValueError()
    
    player.painting = not player.painting
    
    message = 'now painting' if player.painting else 'no longer painting'
    player.send_chat("You're %s" % message)
    if connection is not player and connection in protocol.players:
        connection.send_chat('%s is %s' % (player.name, message))
    protocol.irc_say('* %s is %s' % (player.name, message))

add(paint)


@admin
def paintlogin(connection):
    connection.painting = True
    connection.send_chat("You're now painting")

@admin
def paint_block(protocol, player, x, y, z, color, id):
    if x < 0 or y < 0 or z < 0 or x >= 512 or y >= 512 or z >= 63:
        return False
    if protocol.map.get_color(x, y, z) == color:
        return False
    protocol.map.set_point(x, y, z, color)
    block_action.x = x
    block_action.y = y
    block_action.z = z
    block_action.player_id = id
    block_action.value = DESTROY_BLOCK
    protocol.send_contained(block_action, save = True)
    block_action.value = BUILD_BLOCK
    protocol.send_contained(block_action, save = True)
    return True

@admin
def paint_ray(player):
    if player.tool != BLOCK_TOOL:
        return None
    location = player.world_object.cast_ray(PAINT_RAY_LENGTH)
    if location:
        x, y, z = location
        if player.on_block_build_attempt(x, y, z) == False:
            return None
        if paint_block(player.protocol, player, x, y, z, player.color, player.player_id):
            return location
        return None

@alias('fi')
@name('fill')
@admin
def fill(*arguments):
    connection = arguments[0]
    connection.reset_build()
    connection.callback = fill_r
    connection.arguments = arguments
    connection.select = True
    connection.points = 2
    connection.send_chat('Paint 2 blocks to determine the region to be painted.')

add(fill)

def fill_r(connection, r=None, g=None, b=None):
        x1 = min(connection.block1_x,connection.block2_x)
        y1 = min(connection.block1_y,connection.block2_y)
        z1 = min(connection.block1_z,connection.block2_z)
        x2 = max(connection.block1_x,connection.block2_x)
        y2 = max(connection.block1_y,connection.block2_y)
        z2 = max(connection.block1_z,connection.block2_z)
        if None in [r,g,b]:
            color = connection.color
            id = connection.player_id
        else:
            color = (int(r), int(g), int(b), 255)
            id = 32
            set_color(connection.protocol, make_color_tuple(color))
        for x in xrange(x1, x2 + 1):
            for y in xrange(y1, y2 + 1):
                for z in xrange(z1, z2 + 1):
                    if connection.protocol.map.get_solid(x, y, z):
                        paint_block(connection.protocol, connection, x, y, z, color, id)

@admin
def apply_script(protocol, connection, config):
    class PaintConnection(connection):
        painting = False
        
        def on_reset(self):
            self.painting = False
            connection.on_reset(self)
        
        def on_position_update(self):
            if self.painting and self.world_object.sneak:
                location = paint_ray(self)
                if location != None:
                    if self.select and self.callback == fill_r:
                        self.on_block_destroy(location[0],location[1],location[2],DESTROY_BLOCK)
            connection.on_position_update(self)
        
        def on_orientation_update(self, x, y, z):
            if self.painting and self.world_object.sneak:
                location = paint_ray(self)
                if location != None:
                    if self.select and self.callback == fill_r:
                        self.on_block_destroy(location[0],location[1],location[2],DESTROY_BLOCK)
            connection.on_orientation_update(self, x, y, z)
        
        def on_animation_update(self, jump, crouch, sneak, sprint):
            if self.painting and sneak:
                location = paint_ray(self)
                if location != None:
                    if self.select and self.callback == fill_r:
                        self.on_block_destroy(location[0],location[1],location[2],DESTROY_BLOCK)
            return connection.on_animation_update(self, jump, crouch, sneak, sprint)
    
    return protocol, PaintConnection