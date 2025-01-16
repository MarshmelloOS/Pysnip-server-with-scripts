# version 1.1
# -*- coding: utf-8 -*-

from pyspades.world import Grenade
from pyspades.constants import *
from pyspades.contained import BlockAction, SetColor
from pyspades.server import grenade_packet
from pyspades.common import Vertex3
from twisted.internet import reactor

def get_color_tuple(color):
	"""
	0xAARRGGBB色から(r, g, b, a)色を作る
	"""
	b = color & 0xFF
	g = (color & 0xFF00) >> 8
	r = (color & 0xFF0000) >> 16
	a = int((((color & 0xFF000000) >> 24) / 128.0) * 255)
	return (r, g, b, a)

def make_color_tuple(color):
	"""
	(r, g, b)色から0xAARRGGBB色を作る
	"""
	r = color[0]
	g = color[1]
	b = color[2]
	return (128 << 24) | (r << 16) | (g << 8) | b

def set_color(prt, color, player_id = 32):
	c = SetColor()
	c.player_id = player_id
	c.value = color
	prt.send_contained(c)

def easygre(connection, (x, y, z), (vx, vy, vz), fuse):
	grenade = connection.protocol.world.create_object(Grenade, fuse, Vertex3(x, y, z), None, Vertex3(vx, vy, vz), connection.grenade_exploded)
	grenade_packet.value = fuse
	grenade_packet.player_id = connection.player_id
	grenade_packet.position = (x, y, z)
	grenade_packet.velocity = (vx, vy, vz)
	connection.protocol.send_contained(grenade_packet)
 
def easyblock(connection, (x, y, z), color):
	set_color(connection.protocol, make_color_tuple(color), 32)
	block_action = BlockAction()
	block_action.player_id = 32
	block_action.value = BUILD_BLOCK
	block_action.x = x
	block_action.y = y
	block_action.z = z
	connection.protocol.send_contained(block_action)
	connection.protocol.map.set_point(x, y, z, color)

def easyremove(connection, (x, y, z)):
	block_action = BlockAction()
	block_action.player_id = connection.player_id
	block_action.value = DESTROY_BLOCK
	block_action.x = x
	block_action.y = y
	block_action.z = z
	connection.protocol.send_contained(block_action)
	connection.protocol.map.remove_point(x, y, z)