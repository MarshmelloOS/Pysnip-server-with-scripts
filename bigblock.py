"""
bigblock.py
written by Nick Christensen AKA a_girl

bigblock.py is a simple script that makes building faster and much less expensive.  Instead of placing just one block
you now place a 2x2x2 block for a total of 8 blocks.  This is ideal for servers where map development is fundamental
to the game play.

Known issues:
	***Fixed - Compatibility with OpenSpades. OpenSpades would have all 8 blocks deducted from player's block count.
	***Fixed - Compatibility with painty.py
	***Fixed - Compatibility with blockinfo.py
	***Fixed - Floating Blocks are no longer a problem with BIG_BLOCK_DESTROY OPTION
	***Added - Big Block Uniform Color. Gives option for the big blocks to have their sub-color blocks match.
		Helps see the 8 normal blocks as 1 giant block
	***Added - Option for bullets to take out bigblocks instead of just sub-blocks
	***Added - Option for grenades to take out a sphere of radius 4.5 sub-blocks (it's sweet!)
	***To do: If possible, fix the line build so it doesn't cost on average twice as many blocks
"""
from pyspades.contained import BlockAction, SetColor
from math import sqrt
from pyspades.server import block_action
from pyspades.constants import *
from pyspades.common import make_color
from twisted.internet.reactor import callLater, seconds
from random import randint

BIG_BLOCK_DESTROY = True		#Allows digging to break on the same scale as the build.
								#left click dig would take out 8 blocks, right click dig takes out 24 blocks
WEAPON_BIG_BLOCK_DESTROY = True	#Blocks destroyed by bullets destroy the entire BigBlock, instead of 1 sub-block
GRENADE_BIG_BLOCK_DESTROY = True#Blocks destroyed by grenades destroys all sub-blocks in a sphere of radius 4.5!		
RANDOM_COLOR_OFFSET = 8			#controls the randomization factor of individual generated blocks
BLOCK_INFO_SCRIPT = True		#Set to False if you are not using blockinfo.py
PAINT_SCRIPT = True				#Set to True if you are using paint.py
UNIFORM_COLOR = True			#Enable if you want all 8 sub-blocks to have the same randomized color, false to randomize each sub-bblock
BABEL_MODE = True				#Enables Babel compatibility

	
def apply_script(protocol, connection, config):
	class bigblockConnection(connection):
		count = 0
		
		def on_block_build_attempt(self, x, y, z):		
			other = connection.on_block_build_attempt(self, x, y, z)
			if other == False:
				return other
			if PAINT_SCRIPT == True:
				try:
					if self.painting == True:
						return other
				except AttributeError:
					print "If you are not using paint.py, you need to disable that option in bigblock.py"
			coord = (x, y, z)
			coord = upsize(coord)
			points = []
			points.append(coord)
			self.build_big_block(points)
			return other
			
		def on_line_build_attempt(self, points):
			other = connection.on_line_build_attempt(self, points)	#Do any other scripts prevent this from happening?										
			if other == False:										#Stored Function call in a variable to avoid calling
				return other										#the function twice. We don't want to run all scripts twice.
			if PAINT_SCRIPT == True:
				try:
					if self.painting == True:
						return other
				except AttributeError:
					print "If you are not using paint.py, you need to disable that option in bigblock.py"
			point_list = []
			for point in points:
				coord = upsize(point)
				if coord not in point_list:
					point_list.append(coord)
			self.build_big_block(point_list)
			return other										
																	
		def on_block_destroy(self, x, y, z, value):
			other = connection.on_block_destroy(self, x, y, z, value)
			if BIG_BLOCK_DESTROY == False:
				return other
			if other == False:
				return other
			center = (x, y, z)
			point = upsize(center)
			points = find_sub_blocks(point)
			point_list = []
			if (self.tool == 0 or (self.tool == 2 and WEAPON_BIG_BLOCK_DESTROY == True)) and value == 1:		
				#self.tool == 0 : Spade, self.tool == 2 : Weapon
				#value 1 : not right click dig or grenade destroy				
				self.destroy_sub_blocks(points)
			elif value == 2:						#value 2 refers to blocks destroyed by right click dig
				point_above = (point[0], point[1], point[2] - 1)
				point_below = (point[0], point[1], point[2] + 1)
				point_list.extend(find_sub_blocks(point_above))
				point_list.extend(find_sub_blocks(point_below))
				point_list.extend(points)
				callLater(.03, self.destroy_sub_blocks, point_list)
			elif value == 3 and GRENADE_BIG_BLOCK_DESTROY == True:
				for i in xrange(-2, 3):
					for j in xrange(-2, 3):
						for k in xrange(-2,3):
							tempBlock = (point[0] + i, point[1] + j, point[2] + k)
							tempList = find_sub_blocks(tempBlock)
							for block in tempList:
								if distance(block, center) <= 4.5:
									point_list.append(block)									
				callLater(.03, self.destroy_sub_blocks, point_list)
				return False
			return other
																	
		def build_big_block(self, points):										#accepts a list of modified points to place blocks
			count = 1
			for x in points:
				point_list = find_sub_blocks(x)
				count = count + 1
				callLater(.03 * count, self.build_sub_blocks, point_list)		#build in 2x2x2 sections at a time... allows use of call Later to
				point_list = []													#prevent massive simultaneous builds, then clear the list
				
		def destroy_sub_blocks(self, points):
			for point in points:
				x, y, z = point[0], point[1], point[2]
				if x < 0 or x > 511:
					continue
				if y < 0 or y > 511:
					continue
				if z < 0 or z > 61:
					continue
				if BABEL_MODE == True:
					if connection.on_block_destroy(self, x, y, z, 1) == False:
						continue
				if self.protocol.map.get_solid(x, y, z):
					self.protocol.map.destroy_point(x, y, z)		#destroy_point() checks for any floating blocks, remove_point() does not
					block_action.player_id = 101					#ID value that is outside of the player range to prevent interference
					block_action.value = DESTROY_BLOCK				
					block_action.x = x
					block_action.y = y
					block_action.z = z
					self.protocol.send_contained(block_action, save = True)
					self.protocol.update_entities()
					try:
						if BLOCK_INFO_SCRIPT == True:					#copied from blockinfo.py for script compatibility
							if self.protocol.block_info is None:		#May need to adjust this section depending on which
								self.protocol.block_info = {}			#version of blockinfo you are using.
							if self.blocks_removed is None:
								self.blocks_removed = []
							pos = (x, y, z)
							if pos[0] >= 256:
								side = 1
							else:
								side = 0                
							info = (seconds(), self.protocol.block_info.pop(pos, None),side)
							self.blocks_removed.append(info)
					except AttributeError:
						print "If you are not using blockinfo.py, then you need to disable that setting in bigblock.py"
			
		def build_sub_blocks(self, points):
			count = 0
			color = self.color
			for point in points:
				x, y, z = point[0], point[1], point[2]
				if x < 0 or x > 511:
					continue
				if y < 0 or y > 511:
					continue
				if z < 0 or z > 61:
					continue
				if BABEL_MODE == True:
					if connection.on_block_build_attempt(self, x, y, z) == False:
						continue
				R, G, B = color[0], color[1], color[2]
				if UNIFORM_COLOR == True:
					if count % 8 == 0:
						color = randomize_color(R, G, B)
				else:
					color = randomize_color(R, G, B)
				set_color = SetColor()
				set_color.value = make_color(*color)
				set_color.player_id = 101
				self.send_contained(set_color)
				block_action.player_id = 101
				block_action.x = x
				block_action.y = y
				block_action.z = z
				if self.protocol.map.get_solid(x, y, z):
					block_action.value = DESTROY_BLOCK
					self.protocol.map.remove_point(x, y, z)
					self.protocol.send_contained(block_action, save = True)
				block_action.value = BUILD_BLOCK
				self.protocol.map.set_point(x, y, z, color)
				self.protocol.send_contained(block_action, save = True)
				count += 1
				try:
					if BLOCK_INFO_SCRIPT == True:			#copied from blockinfo.py for script compatibility. May need to adjust for version												
						if self.protocol.block_info is None:
							self.protocol.block_info = {}
						self.protocol.block_info[(x, y, z)] = (self.name, self.team.id)
				except AttributeError:
					print "If you are not using blockinfo.py, then you need to disable that setting in bigblock.py"
				
	return protocol, bigblockConnection

def randomize_color(R, G, B):
	R = R + random_integer()
	G = G + random_integer()
	B = B + random_integer()
	R = inside(R, 0, 255)			#ensures each color value can not be outside of the 0-255 range.
	G = inside(G, 0, 255)
	B = inside(B, 0, 255)
	color = (R, G, B)
	return color
	
def upsize(point):
	x = point[0] // 2				#floor division. Divides each coordinate by two, rounded down to nearest integer
	y = point[1] // 2
	z = point[2] // 2
	newPoint = (x, y, z)
	return newPoint

def inside(x, a, b):
	if x < a:
		x = a
	elif x > b:
		x = b
	return x
	
def find_sub_blocks(point): 		#returns a list of all blocks contained in the big block coordinate
	point_list = []
	for i in xrange(2):
		for j in xrange(2):
			for k in xrange(2):				
				x = (point[0] * 2) + i					
				y = (point[1] * 2) + j
				z = (point[2] * 2) + k
				coord = (x, y, z)
				point_list.append(coord)
	return point_list
	
def random_integer():											#random integer within +\- offset of original value
	x = randint(-RANDOM_COLOR_OFFSET,RANDOM_COLOR_OFFSET)
	return x
	
def distance(a, b):
	return sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 +(a[2] - b[2]) ** 2)