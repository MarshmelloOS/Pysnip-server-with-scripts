from commands import add, admin
from pyspades.contained import BlockAction, SetColor
from pyspades.constants import *
from commands import add, admin, name, alias, join_arguments
from math import *

EAST = 0
SOUTH = 1
WEST = 2
NORTH = 3

global_mmt_undo = []
global_mmt_is_undo = False

@admin
def make_color(r, g, b, a):
	return b | (g << 8) | (r << 16) | (int((a / 255.0) * 128) << 24)

@admin
def make_color_tuple(color):
	return make_color(color[0], color[1], color[2], 255)

@admin
def get_color_tuple(color):
	b = color & 0xFF
	g = (color & 0xFF00) >> 8
	r = (color & 0xFF0000) >> 16
	a = int((((color & 0xFF000000) >> 24) / 128.0) * 255)
	return (r, g, b, a)

@admin
def set_color(prt, color, player_id = 32):
	c = SetColor()
	c.player_id = player_id
	c.value = color
	prt.send_contained(c)


@admin
def add_block(prt, x, y, z, color, player_id = 32, mirror_x = False, mirror_y = False):
	global global_mmt_undo
	global global_mmt_is_undo
	if x >= 0 and x < 512 and y >= 0 and y < 512 and z >= 0 and z < 64:
		if mirror_x == True or mirror_y == True:
			x2 = x
			y2 = y
			if mirror_x == True:
				x2 = 511 - x
			if mirror_y == True:
				y2 = 511 - y
			add_block(prt, x2, y2, z, color, player_id, False, False)
		if not prt.map.get_solid(x, y, z):
			if not global_mmt_is_undo:
				global_mmt_undo.append( (x,y,z,-1) )
			block_action = BlockAction()
			block_action.player_id = player_id
			block_action.value = BUILD_BLOCK
			block_action.x = x
			block_action.y = y
			block_action.z = z
			prt.send_contained(block_action)
			prt.map.set_point(x, y, z, get_color_tuple(color))
			return True
	return False

@admin
def remove_block(prt, x, y, z, mirror_x = False, mirror_y = False):
	global global_mmt_undo
	global global_mmt_is_undo
	if x >= 0 and x < 512 and y >= 0 and y < 512 and z >= 0 and z < 64:
		if mirror_x == True or mirror_y == True:
			x2 = x
			y2 = y
			if mirror_x == True:
				x2 = 511 - x
			if mirror_y == True:
				y2 = 511 - y
			remove_block(prt, x2, y2, z, False, False)
		if prt.map.get_solid(x, y, z):
			if not global_mmt_is_undo:
				global_mmt_undo.append( (x,y,z,make_color_tuple(prt.map.get_point(x, y, z)[1])) )
			block_action = BlockAction()
			block_action.player_id = 32
			block_action.value = DESTROY_BLOCK
			block_action.x = x
			block_action.y = y
			block_action.z = z
			prt.map.remove_point(x, y, z)
			prt.send_contained(block_action)
			return True
	return False


@name('mirror')
@admin
def mirror(connection, xmode, ymode):
	if xmode:
		connection.mirror_x = not connection.mirror_x
	if ymode:
		connection.mirror_y = not connection.mirror_y
	connection.send_chat("mirror mode changed")

add(mirror)


@alias('tu')
@name('tunnel')
@admin
def tunnel(*arguments):
	connection = arguments[0]
	connection.reset_build()
	connection.callback = tunnel_r
	connection.arguments = arguments
	connection.select = True
	connection.points = 1
	connection.send_chat('Hit 1 blocks to determine the block to be entrance.')


add(tunnel)

def tunnel_r(connection, radius = 2, length = 10, zoffset = 0):
	radius = int(radius)
	length = int(length)
	zoffset = int(zoffset)
	facing = connection.get_direction()
	if facing == WEST or facing == NORTH:
		length = -length
	for rel_h in xrange(-radius, radius + 1):
		for rel_v in xrange(-radius, 1):
			if round(sqrt(rel_h**2 + rel_v**2)) <= radius:
				if facing == NORTH or facing == SOUTH:
					y1 = connection.block1_y
					y2 = connection.block1_y + length
					for y in xrange(min(y1, y2), max(y1, y2) + 1):
						remove_block(connection.protocol, connection.block1_x + rel_h, y, connection.block1_z + rel_v + zoffset, connection.mirror_x, connection.mirror_y)
				elif facing == WEST or facing == EAST:
					x1 = connection.block1_x
					x2 = connection.block1_x + length
					for x in xrange(min(x1, x2), max(x1, x2) + 1):
						remove_block(connection.protocol, x, connection.block1_y + rel_h, connection.block1_z + rel_v + zoffset, connection.mirror_x, connection.mirror_y)

@alias('in')
@name('insert')
@admin
def insert(*arguments):
	connection = arguments[0]
	connection.reset_build()
	connection.callback = insert_r
	connection.arguments = arguments
	connection.select = True
	connection.points = 2
	connection.send_chat('Hit 2 blocks to determine the region to be inserted.')


add(insert)

def insert_r(connection):
	x1 = min(connection.block1_x, connection.block2_x)
	x2 = max(connection.block1_x, connection.block2_x)
	y1 = min(connection.block1_y, connection.block2_y)
	y2 = max(connection.block1_y, connection.block2_y)
	z1 = min(connection.block1_z, connection.block2_z)
	z2 = max(connection.block1_z, connection.block2_z)
	color = make_color_tuple(connection.color)
	for xx in xrange(x1, x2 + 1):
		for yy in xrange(y1, y2 + 1):
			for zz in xrange(z1, z2 + 1):
				add_block(connection.protocol, xx, yy, zz, color, connection.player_id, connection.mirror_x, connection.mirror_y)

@alias('de')
@name('delete')
@admin
def delete(*arguments):
	connection = arguments[0]
	connection.reset_build()
	connection.callback = delete_r
	connection.arguments = arguments
	connection.select = True
	connection.points = 2
	connection.send_chat('Hit 2 blocks to determine the region to be deleted.')


add(delete)

def delete_r(connection):
	x1 = min(connection.block1_x, connection.block2_x)
	x2 = max(connection.block1_x, connection.block2_x)
	y1 = min(connection.block1_y, connection.block2_y)
	y2 = max(connection.block1_y, connection.block2_y)
	z1 = min(connection.block1_z, connection.block2_z)
	z2 = max(connection.block1_z, connection.block2_z)
	for xx in xrange(x1, x2 + 1):
		for yy in xrange(y1, y2 + 1):
			for zz in xrange(z1, z2 + 1):
				remove_block(connection.protocol, xx, yy, zz, connection.mirror_x, connection.mirror_y)

@alias('pa')
@name('pattern')
@admin
def pattern(*arguments):
	connection = arguments[0]
	connection.reset_build()
	connection.callback = pattern_r
	connection.arguments = arguments
	connection.select = True
	connection.points = 2
	connection.send_chat('Hit 2 blocks to determine the region to be patterned.')


add(pattern)

def pattern_r(connection, copies = 1):
	copies = int(copies)
	x1 = min(connection.block1_x, connection.block2_x)
	x2 = max(connection.block1_x, connection.block2_x)
	y1 = min(connection.block1_y, connection.block2_y)
	y2 = max(connection.block1_y, connection.block2_y)
	z1 = min(connection.block1_z, connection.block2_z)
	z2 = max(connection.block1_z, connection.block2_z)
	delta_z = (z2 - z1) + 1
	for xx in xrange(x1, x2 + 1):
		for yy in xrange(y1, y2 + 1):
			for zz in xrange(z1, z2 + 1):
				if connection.protocol.map.get_solid(xx, yy, zz):
					color = make_color_tuple(connection.protocol.map.get_point(xx, yy, zz)[1])
					set_color(connection.protocol, color, 32)
					for i in xrange(1, copies + 1):
						z_offset = delta_z * i
						add_block(connection.protocol, xx, yy, zz - z_offset, color, 32, connection.mirror_x, connection.mirror_y)

@alias('co')
@name('copy')
@admin
def copy(*arguments):
	connection = arguments[0]
	connection.reset_build()
	connection.callback = copy_r
	connection.arguments = arguments
	connection.select = True
	connection.points = 3
	connection.send_chat('Hit 2 blocks to determine the region to be copied.')


add(copy)

def copy_r(connection, copies = 1):
	copies = int(copies)
	x1 = min(connection.block1_x, connection.block2_x)
	x2 = max(connection.block1_x, connection.block2_x)
	y1 = min(connection.block1_y, connection.block2_y)
	y2 = max(connection.block1_y, connection.block2_y)
	z1 = min(connection.block1_z, connection.block2_z)
	z2 = max(connection.block1_z, connection.block2_z)
	delta_x = connection.block3_x-connection.block1_x
	delta_y = connection.block3_y-connection.block1_y
	delta_z = connection.block3_z-connection.block1_z
	for xx in xrange(x1, x2 + 1):
		for yy in xrange(y1, y2 + 1):
			for zz in xrange(z1, z2 + 1):
				if connection.protocol.map.get_solid(xx, yy, zz):
					color = make_color_tuple(connection.protocol.map.get_point(xx, yy, zz)[1])
					set_color(connection.protocol, color, 32)
					for i in xrange(1, copies + 1):
						x_offset = delta_x * i
						y_offset = delta_y * i
						z_offset = delta_z * i
						add_block(connection.protocol, xx + x_offset, yy + y_offset, zz + z_offset, color, 32, connection.mirror_x, connection.mirror_y)


@alias('cc')
@name('ctrlc')
@admin
def ctrlc(*arguments):
	connection = arguments[0]
	connection.reset_build()
	connection.callback = ctrlc_r
	connection.arguments = arguments
	connection.select = True
	connection.points = 2
	connection.send_chat('Hit 2 blocks to determine the region to be copied.(ver.y)')
add(ctrlc)

def ctrlc_r(connection):
	x1 = min(connection.block1_x, connection.block2_x)
	x2 = max(connection.block1_x, connection.block2_x)
	y1 = min(connection.block1_y, connection.block2_y)
	y2 = max(connection.block1_y, connection.block2_y)
	z1 = min(connection.block1_z, connection.block2_z)
	z2 = max(connection.block1_z, connection.block2_z)

	connection.ctrlc_zero_pos_x = connection.block1_x - x1
	connection.ctrlc_zero_pos_y = connection.block1_y - y1
	connection.ctrlc_zero_pos_z = connection.block1_z - z1
	connection.ctrlc_mem=[]

	for xx in xrange(0, x2 + 1 - x1):
		connection.ctrlc_mem.append([])
		for yy in xrange(0, y2 + 1 - y1):
			connection.ctrlc_mem[xx].append([])
			for zz in xrange(0, z2 + 1 - z1):
				if connection.protocol.map.get_solid(xx+x1, yy+y1, zz+z1):
					color = make_color_tuple(connection.protocol.map.get_point(xx+x1, yy+y1, zz+z1)[1])
					connection.ctrlc_mem[xx][yy].append(color)
				else:
					connection.ctrlc_mem[xx][yy].append(None)

@alias('cx')
@name('ctrlx')
@admin
def ctrlx(*arguments):
	connection = arguments[0]
	connection.reset_build()
	connection.callback = ctrlx_r
	connection.arguments = arguments
	connection.select = True
	connection.points = 2
	connection.send_chat('Hit 2 blocks to determine the region to be cut.(ver.y)')
add(ctrlx)

def ctrlx_r(connection):
	x1 = min(connection.block1_x, connection.block2_x)
	x2 = max(connection.block1_x, connection.block2_x)
	y1 = min(connection.block1_y, connection.block2_y)
	y2 = max(connection.block1_y, connection.block2_y)
	z1 = min(connection.block1_z, connection.block2_z)
	z2 = max(connection.block1_z, connection.block2_z)

	connection.ctrlx=True
	connection.ctrlx_x1 = x1
	connection.ctrlx_x2 = x2

	connection.ctrlx_y1 = y1
	connection.ctrlx_y2 = y2

	connection.ctrlx_z1 = z1
	connection.ctrlx_z2 = z2

	connection.ctrlc_zero_pos_x = connection.block1_x - x1
	connection.ctrlc_zero_pos_y = connection.block1_y - y1
	connection.ctrlc_zero_pos_z = connection.block1_z - z1
	connection.ctrlc_mem=[]

	for xx in xrange(0, x2 + 1 - x1):
		connection.ctrlc_mem.append([])
		for yy in xrange(0, y2 + 1 - y1):
			connection.ctrlc_mem[xx].append([])
			for zz in xrange(0, z2 + 1 - z1):
				if connection.protocol.map.get_solid(xx+x1, yy+y1, zz+z1):
					color = make_color_tuple(connection.protocol.map.get_point(xx+x1, yy+y1, zz+z1)[1])
					connection.ctrlc_mem[xx][yy].append(color)
				else:
					connection.ctrlc_mem[xx][yy].append(None)


@alias('cv')
@name('ctrlv')
@admin
def ctrlv(*arguments):
	connection = arguments[0]
	connection.reset_build()
	connection.callback = ctrlv_r
	connection.arguments = arguments
	connection.select = True
	connection.points = 1
	connection.send_chat('Hit 1 blocks to determine the region to be pasted.(ver.y)')
add(ctrlv)

def ctrlv_r(connection):
	if connection.ctrlx:
		connection.ctrlx=False
		x1 = connection.ctrlx_x1
		x2 = connection.ctrlx_x2
          
		y1 = connection.ctrlx_y1
		y2 = connection.ctrlx_y2
          
		z1 = connection.ctrlx_z1
		z2 = connection.ctrlx_z2

		for xx in xrange(x1, x2 + 1):
			for yy in xrange(y1, y2 + 1):
				for zz in xrange(z1, z2 + 1):
					remove_block(connection.protocol, xx, yy, zz, connection.mirror_x, connection.mirror_y)


	x1 = connection.block1_x
	y1 = connection.block1_y
	z1 = connection.block1_z

	x1-=connection.ctrlc_zero_pos_x
	y1-=connection.ctrlc_zero_pos_y
	z1-=connection.ctrlc_zero_pos_z
	


	counter_x=0
	counter_y=0
	counter_z=0

	for xx in connection.ctrlc_mem:
		counter_y=0
		for yy in xx:
			counter_z=0
			for zz in yy:
				if zz is not None:
					color = zz
					set_color(connection.protocol, color, 32)
					add_block(connection.protocol, x1+counter_x, y1+counter_y, z1+counter_z, color, 32, connection.mirror_x, connection.mirror_y)
				counter_z+=1
			counter_y+=1
		counter_x+=1




@alias('cu')
@name('cut')
@admin
def cut(*arguments):
	connection = arguments[0]
	connection.reset_build()
	connection.callback = cut_r
	connection.arguments = arguments
	connection.select = True
	connection.points = 3
	connection.send_chat('Hit 2 blocks to determine the region to be cut.')


add(cut)

def cut_r(connection, paste = 1):
	pastes = int(paste)
	x1 = min(connection.block1_x, connection.block2_x)
	x2 = max(connection.block1_x, connection.block2_x)
	y1 = min(connection.block1_y, connection.block2_y)
	y2 = max(connection.block1_y, connection.block2_y)
	z1 = min(connection.block1_z, connection.block2_z)
	z2 = max(connection.block1_z, connection.block2_z)
	delta_x = connection.block3_x-connection.block1_x
	delta_y = connection.block3_y-connection.block1_y
	delta_z = connection.block3_z-connection.block1_z
	for xx in xrange(x1, x2 + 1):
		for yy in xrange(y1, y2 + 1):
			for zz in xrange(z1, z2 + 1):
				if connection.protocol.map.get_solid(xx, yy, zz):
					color = make_color_tuple(connection.protocol.map.get_point(xx, yy, zz)[1])
					set_color(connection.protocol, color, 32)
					for i in xrange(1, pastes + 1):
						x_offset = delta_x * i
						y_offset = delta_y * i
						z_offset = delta_z * i
						add_block(connection.protocol, xx + x_offset, yy + y_offset, zz + z_offset, color, 32, connection.mirror_x, connection.mirror_y)
						remove_block(connection.protocol, xx, yy, zz, connection.mirror_x, connection.mirror_y)

@alias('mc')
@name('mirrorcopy')
@admin
def mirrorcopy(*arguments):
	connection = arguments[0]
	connection.reset_build()
	modes = len(arguments)
	if modes < 4:
		connection.send_chat('Enter Xmode, Ymode and Zmode')
		connection.send_chat('Ex /mirrorcopy 1 0 0')
		return False
	connection.callback = mirrorcopy_r
	connection.arguments = arguments
	connection.select = True
	connection.points = 3
	connection.send_chat('Hit 2 blocks to determine the region to be copied symmetric')


add(mirrorcopy)

def mirrorcopy_r(connection, x_mode, y_mode, z_mode):
	Xmode = int(x_mode)
	Ymode = int(y_mode)
	Zmode = int(z_mode)
	x1 = connection.block1_x
	x2 = connection.block2_x
	x3 = connection.block3_x
	min_x = min(connection.block1_x, connection.block2_x)
	max_x = max(connection.block1_x, connection.block2_x) + 1
	y1 = connection.block1_y
	y2 = connection.block2_y
	y3 = connection.block3_y
	min_y = min(connection.block1_y, connection.block2_y)
	max_y = max(connection.block1_y, connection.block2_y) + 1
	z1 = connection.block1_z
	z2 = connection.block2_z
	z3 = connection.block3_z
	min_z = min(connection.block1_z, connection.block2_z)
	max_z = max(connection.block1_z, connection.block2_z) + 1
	
	for zz in xrange(min_z, max_z):
		if Zmode:
			nz = z3 + z1 - zz
		else:
			nz = z3 - z1 + zz
			
		if nz < 0 or nz >= 63:
			return False
		for yy in xrange(min_y, max_y):
			if Ymode:
				ny = y3 + y1 - yy
			else:
				ny = y3 - y1 + yy
				
			if ny < 0 or ny >= 512:
				while ny < 0:
					ny += 512
				ny %= 512
			for xx in xrange(min_x, max_x):
				if Xmode:
					nx = x3 + x1 - xx
				else:
					nx = x3 - x1 + xx
				if nx < 0 or nx >= 512:
					while nx < 0:
						nx += 512
					nx %= 512
				if connection.protocol.map.get_solid(xx, yy, zz):
					color = make_color_tuple(connection.protocol.map.get_point(xx, yy, zz)[1])
					set_color(connection.protocol, color, 32)
					add_block(connection.protocol, nx, ny, nz, color, 32, connection.mirror_x, connection.mirror_y)

@alias('ro')
@name('rotate')
@admin
def rotate(*arguments):
	connection = arguments[0]
	connection.reset_build()
	if len(arguments) < 2:
		connection.send_chat('Enter angle')
		connection.send_chat('Ex /rotate 90')
		return False
	connection.callback = rotate_r
	connection.arguments = arguments
	connection.select = True
	connection.points = 3
	connection.send_chat('Hit 2 blocks to determine the region to be rotated')


add(rotate)

def rotate_r(connection, angle):
	ang = float(angle) * pi / 180
	x1 = connection.block1_x
	x2 = connection.block2_x
	x3 = connection.block3_x
	min_x = min(connection.block1_x, connection.block2_x)
	max_x = max(connection.block1_x, connection.block2_x) + 1
	y1 = connection.block1_y
	y2 = connection.block2_y
	y3 = connection.block3_y
	min_y = min(connection.block1_y, connection.block2_y)
	max_y = max(connection.block1_y, connection.block2_y) + 1
	z1 = connection.block1_z
	z2 = connection.block2_z
	z3 = connection.block3_z
	min_z = min(connection.block1_z, connection.block2_z)
	max_z = max(connection.block1_z, connection.block2_z) + 1
	
	for zz in xrange(min_z, max_z):
		nz = zz
		if nz < 0 or nz >= 63:
			return False
		for yy in xrange(min_y, max_y):
			dy = yy - y1
			for xx in xrange(min_x, max_x):
				dx = xx - x1
				nx = x3 + dx*cos(ang) - dy*sin(ang)
				ny = y3 + dx*sin(ang) + dy*cos(ang)
				
				if nx < 0 or nx >= 512:
					while nx < 0:
						nx += 512
					nx %= 512
				if ny < 0 or ny >= 512:
					while ny < 0:
						ny += 512
					ny %= 512
					
				if connection.protocol.map.get_solid(xx, yy, zz):
					color = make_color_tuple(connection.protocol.map.get_point(xx, yy, zz)[1])
					set_color(connection.protocol, color, 32)
					add_block(connection.protocol, nx, ny, nz, color, 32, connection.mirror_x, connection.mirror_y)


@alias('el')
@name('ellect')
@admin
def ellect(*arguments):
	connection = arguments[0]
	connection.reset_build()
	connection.callback = ellect_r
	connection.arguments = arguments
	connection.select = True
	connection.points = 3
	connection.send_chat('Hit 2 blocks to determine the region to be rotated')


add(ellect)

def ellect_r(connection):
	x1 = connection.block1_x
	x2 = connection.block2_x
	x3 = connection.block3_x
	y1 = connection.block1_y
	y2 = connection.block2_y
	y3 = connection.block3_y
	z1 = connection.block1_z
	z2 = connection.block2_z
	z3 = connection.block3_z
	
	if z1 != z2:
		connection.send_chat('Select a plane area')
		return
	elif x1 == x2:
		min_x = min(x1, x3)
		max_x = max(x1, x3) + 1
		min_y = min(y1, y2)
		max_y = max(y1, y2) + 1
		nx = x3
		for xx in xrange(min_x, max_x):
			dx = fabs(xx - x3)
			nz = z3 - dx
			for yy in xrange(min_y, max_y):
				ny = yy
				if connection.protocol.map.get_solid(xx, yy, z1):
					color = make_color_tuple(connection.protocol.map.get_point(xx, yy, z1)[1])
					set_color(connection.protocol, color, 32)
					add_block(connection.protocol, nx, ny, nz, color, 32, connection.mirror_x, connection.mirror_y)

	elif y1 == y2:
		min_y = min(y1, y3)
		max_y = max(y1, y3) + 1
		min_x = min(x1, x2)
		max_x = max(x1, x2) + 1
		ny = y3
		for yy in xrange(min_y, max_y):
			dy = fabs(yy - y3)
			nz = z3 - dy
			for xx in xrange(min_x, max_x):
				nx = xx
				if connection.protocol.map.get_solid(xx, yy, z1):
					color = make_color_tuple(connection.protocol.map.get_point(xx, yy, z1)[1])
					set_color(connection.protocol, color, 32)
					add_block(connection.protocol, nx, ny, nz, color, 32, connection.mirror_x, connection.mirror_y)
	
@alias('ho')
@name('hollow')
@admin
def hollow(*arguments):
	connection = arguments[0]
	connection.reset_build()
	connection.callback = hollow_r
	connection.arguments = arguments
	connection.select = True
	connection.points = 2
	connection.send_chat('Hit 2 blocks to determine the region to be hollowed.')



add(hollow)

def hollow_r(connection, thickness = 1):
	m = connection.protocol.map
	thickness = int(thickness) - 1
	x1 = min(connection.block1_x, connection.block2_x)
	x2 = max(connection.block1_x, connection.block2_x)
	y1 = min(connection.block1_y, connection.block2_y)
	y2 = max(connection.block1_y, connection.block2_y)
	z1 = min(connection.block1_z, connection.block2_z)
	z2 = max(connection.block1_z, connection.block2_z)
	blocks = []
	xr = x2 - x1 + 1
	yr = y2 - y1 + 1
	zr = z2 - z1 + 1
	for x in xrange(0, xr):
		blocks.append([])
		for y in xrange(0, yr):
			blocks[x].append([])
			for z in xrange(0, zr):
				blocks[x][y].append(False)
	def hollow_check(xc, yc, zc, thickness):
		if thickness > 0:
			for xx in xrange(xc - 1, xc + 2):
				if xx >= 0 and xx < xr:
					for yy in xrange(yc - 1, yc + 2):
						if yy >= 0 and yy < yr:
							for zz in xrange(zc - 1, zc + 2):
								if zz >= 0 and zz < zr:
									blocks[xx][yy][zz] = True
									if m.get_solid(x1 + xx, y1 + yy, z1 + zz):
										hollow_check(xx, yy, zz, thickness - 1)
	for x in xrange(0, xr):
		for y in xrange(0, yr):
			for z in xrange(0, zr):
				if m.get_solid(x1 + x, y1 + y, z1 + z):
					if m.is_surface(x1 + x, y1 + y, z1 + z):
						blocks[x][y][z] = True
						hollow_check(x, y, z, thickness)
				else:
					blocks[x][y][z] = True
	for x in xrange(0, xr):
		for y in xrange(0, yr):
			for z in xrange(0, zr):
				if not blocks[x][y][z]:
					remove_block(connection.protocol, x1 + x, y1 + y, z1 + z)


@name('undo_mmt')
@admin
def undo_mmt(connection):
	global global_mmt_is_undo
	global_mmt_is_undo = True
	if len(connection.undo)>0:
		if connection.undo[0][3]>=0:
			for tmp_undo in connection.undo:
				set_color(connection.protocol, tmp_undo[3], 32)
				add_block(connection.protocol, tmp_undo[0], tmp_undo[1], tmp_undo[2], tmp_undo[3], 32, connection.mirror_x, connection.mirror_y)
		else:
			for tmp_undo in connection.undo:
				remove_block(connection.protocol,tmp_undo[0], tmp_undo[1], tmp_undo[2], connection.mirror_x, connection.mirror_y)
		connection.send_chat("undo has been carried out.")
	global_mmt_is_undo = False
	connection.undo = []

add(undo_mmt)



def apply_script(protocol, connection, config):
	class MapMakingToolsConnection(connection):
		select = False
		mirror_x = False
		mirror_y = False
		undo = ["test"]
		ctrlc_mem=[]
		ctrlc_zero_pos_x=0
		ctrlc_zero_pos_y=0
		ctrlc_zero_pos_z=0
		ctrlx=False
		ctrlx_x1 = 0
		ctrlx_x2 = 0

		ctrlx_y1 = 0
		ctrlx_y2 = 0

		ctrlx_z1 = 0
		ctrlx_z2 = 0

		def on_reset(self):
			self.ctrlx=False
			connection.on_reset(self)

		def reset_build(self):
			self.block1_x = None
			self.block1_y = None
			self.block1_z = None
			self.block2_x = None
			self.block2_y = None
			self.block2_z = None
			self.block3_x = None
			self.block3_y = None
			self.block3_z = None
			self.callback = None
			self.arguments = None
			self.select = False
			self.points = None
		
		def get_direction(self):
			orientation = self.world_object.orientation
			angle = atan2(orientation.y, orientation.x)
			if angle < 0:
				angle += 6.283185307179586476925286766559
			# Convert to units of quadrents
			angle *= 0.63661977236758134307553505349006
			angle = round(angle)
			if angle == 4:
				angle = 0
			return angle

		def on_block_destroy(self, x, y, z, value):
			global global_mmt_undo
			global global_mmt_is_undo
			if not self.god:
				return False
			if self.select == True:
				if self.points == 1:
					self.block1_x = x
					self.block1_y = y
					self.block1_z = z
					global_mmt_undo = []
					self.callback(*self.arguments)
					self.undo = global_mmt_undo
					self.reset_build()
					return False
				elif self.points == 2:
					if self.block1_x == None:
						self.block1_x = x
						self.block1_y = y
						self.block1_z = z
						self.send_chat('First block selected')
						return False
					else:
						self.block2_x = x
						self.block2_y = y
						self.block2_z = z
						self.send_chat('Second block selected')
						global_mmt_undo = []
						self.callback(*self.arguments)
						self.undo = global_mmt_undo
						self.reset_build()
						return False
				elif self.points == 3:
					if self.block1_x == None:
						self.block1_x = x
						self.block1_y = y
						self.block1_z = z
						self.send_chat('First block selected')
						return False
					elif self.block2_x == None:
						self.block2_x = x
						self.block2_y = y
						self.block2_z = z
						self.send_chat('Second block selected')
						self.send_chat('Hit 1 more block to determine the place to be pasted.')
						return False
					else:
						self.block3_x = x
						self.block3_y = y
						self.block3_z = z
						self.send_chat('Third block selected')
						global_mmt_undo = []
						self.callback(*self.arguments)
						self.undo = global_mmt_undo
						self.reset_build()
						return False
			if self.mirror_x == True or self.mirror_y == True:
				x2 = x
				y2 = y
				if self.mirror_x == True:
					x2 = 511 - x
				if self.mirror_y == True:
					y2 = 511 - y
				remove_block(self.protocol, x2, y2, z)
				if value == SPADE_DESTROY:
					if z >= 1:
						remove_block(self.protocol, x2, y2, z-1)
					if z <= 61:
						remove_block(self.protocol, x2, y2, z+1)
			connection.on_block_destroy(self, x, y, z, value)
		
		def on_block_build(self, x, y, z):
			if self.mirror_x == True or self.mirror_y == True:
				x2 = x
				y2 = y
				if self.mirror_x == True:
					x2 = 511 - x
				if self.mirror_y == True:
					y2 = 511 - y
				add_block(self.protocol, x2, y2, z, make_color_tuple(self.color), self.player_id)
			connection.on_block_build(self, x, y, z)

		def on_line_build_attempt(self, points):
			if self.mirror_x or self.mirror_y:
				for point in points:
					x, y, z = point
					if self.mirror_x:
						x = 511 - x
					if self.mirror_y:
						y = 511 - y
					add_block(self.protocol, x, y, z, make_color_tuple(self.color), self.player_id)
			return connection.on_line_build_attempt(self, points)
			

	return protocol, MapMakingToolsConnection