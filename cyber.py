# -*- coding: utf-8 -*-
from itertools import product
from random import *
from math import floor
from pyspades.server import block_action
from pyspades.contained import BlockAction, SetColor
from commands import *
from commands import admin, add, name, get_team, get_player,alias
from pyspades.contained import *
from pyspades.server import *
from pyspades.common import *


MEN = (0,0,0)
KADO = (100,255,100)

def apply_script(protocol,connection,config):
	class LightProtocol(protocol):

		def on_map_change(self, map):
			for x in range(512):
				for y in range(512):
					z=0
					while(True):
						z = map.get_z(x,y,z)
						if map.is_surface(x,y,z):
							E = map.get_solid(x+1, y, z)
							S = map.get_solid(x, y+1, z)
							W = map.get_solid(x-1, y, z)
							N = map.get_solid(x, y-1, z)
							U = map.get_solid(x, y, z-1)
							D = map.get_solid(x, y, z+1)
							if (E and S and W and N) or (E and W and U and D) or (U and D and S and N):
								color = MEN
							else:
								color = KADO
							r,g,b  = color
								
							map.set_point(x, y, z, (r,g,b))
						z +=1
						if z>=63:
							break

			protocol.on_map_change(self, map)							
											
	return LightProtocol, connection