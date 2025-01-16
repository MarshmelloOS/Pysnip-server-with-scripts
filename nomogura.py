"""
mogura kinsi by yuyasato 20180819

"""

from pyspades.constants import *
from random import randint
from twisted.internet import reactor
from math import sqrt,sin,asin, cos, acos, pi, tan,atan,degrees,radians,hypot,atan2,fabs,floor
from commands import admin, add, name, get_team, get_player,alias,add
import commands

BOX_RANGE=2 #syuui+- nanmasu tansaku


HALF_BOX_MASS_LIMIT = BOX_RANGE*((BOX_RANGE*2+1)**2)+((BOX_RANGE*2+1)**2)/2

def apply_script(protocol, connection, config):


	class NomoguraConnection(connection):

		def on_block_destroy(self, x, y, z, mode):
			xp,yp,zp = self.world_object.position.get()
			N = False #north
			S = False #south
			E = False #east
			W = False #west
			U = False #upper
			D = False #downner
			Ecount=0
			Wcount=0
			Ncount=0
			Scount=0
			Ucount=0
			Dcount=0
			destroy = True

			for a in range(BOX_RANGE*2+1):
				aa = a-BOX_RANGE
				if aa>=0:
					E=True
				else:
					E=False
				if aa<0:
					W=True
				else:
					W=False
				for b in range(BOX_RANGE*2+1):
					bb = b-BOX_RANGE
					if bb>=0:
						S=True
					else:
						S=False
					if aa<=0:
						N=True
					else:
						N=False
					for c in range(BOX_RANGE*2+1):
						cc = c-BOX_RANGE
						if cc>=0:
							D=True
						else:
							D=False
						if cc<=0:
							U=True
						else:
							U=False
						xx,yy,zz = x+aa,y+bb,z+cc
						if self.protocol.map.get_solid(xx, yy, zz):
							if E :Ecount+=1
							if W :Wcount+=1
							if N :Ncount+=1
							if S :Scount+=1
							if U :Ucount+=1
							if D :Dcount+=1
			if Ecount>HALF_BOX_MASS_LIMIT:destroy=False
			if Wcount>HALF_BOX_MASS_LIMIT:destroy=False
			if Ncount>HALF_BOX_MASS_LIMIT:destroy=False
			if Scount>HALF_BOX_MASS_LIMIT:destroy=False
			if Ucount>HALF_BOX_MASS_LIMIT:destroy=False
			if Dcount>HALF_BOX_MASS_LIMIT:destroy=False

			if destroy==False: #tokurei
				sixpath = 0
				if not self.protocol.map.get_solid(x+1,y,z) and not self.protocol.map.get_solid(x+2,y,z):sixpath+=1
				if not self.protocol.map.get_solid(x-1,y,z) and not self.protocol.map.get_solid(x-2,y,z):sixpath+=1
				if not self.protocol.map.get_solid(x,y+1,z) and not self.protocol.map.get_solid(x,y+2,z):sixpath+=1
				if not self.protocol.map.get_solid(x,y-1,z) and not self.protocol.map.get_solid(x,y-2,z):sixpath+=1
				if not self.protocol.map.get_solid(x,y,z+1) and not self.protocol.map.get_solid(x,y,z+2):sixpath+=1
				if not self.protocol.map.get_solid(x,y,z-1) and not self.protocol.map.get_solid(x,y,z-2):sixpath+=1

				if sixpath>=2:
					destroy=True
			if destroy:
				return connection.on_block_destroy(self, x, y, z, mode)
			else:
				self.send_chat("mogura damedesu !!!!!!")
				return False

	return protocol, NomoguraConnection