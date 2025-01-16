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

# /screen で　範囲指定すると元色に持ってるブロックの色が合成される（スクリーン）
# /jousan で　範囲指定すると元色に持ってるブロックの色が合成される（乗算）

DARK_RATIO = 1.0
light_R = 5
light_max = 6

def paint_block(protocol, player, x, y, z,id):
	r3,g3,b3 = protocol.map.get_color(x, y, z) 
	r2,g2,b2 = player.color
	
	if player.jousan:
		r = (r3 * r2) / 255
		g = (g3 * g2) / 255
		b = (b3 * b2) / 255
	
	if player.screen:
		r = (r3 + r2) - r3 * r2 / 255
		g = (g3 + g2) - g3 * g2 / 255
		b = (b3 + b2) - b3 * b2 / 255
		
	color = (r,g,b)
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


@alias('li')
@name('setlight')
def setlight(connection):
	connection.light_put = True
	return "you have light block now"
add(setlight)


def apply_script(protocol,connection,config):
	class LightProtocol(protocol):
		dark_next_map = True
		darked = False
		moto_blocks = None
		light_spot = []

		def on_map_change(self, map):
			self.darked = self.dark_next_map
			if self.darked:
				moto_blocks = self.moto_blocks = {}
				for x, y, z in product(xrange(512), xrange(512), xrange(64)):
					color= map.get_color(x, y, z)
					if color is not None:
						moto_blocks[(x, y, z)] = color
						if color!=(0,0,0):
							r,g,b  = color
							r= r//DARK_RATIO
							g= g//DARK_RATIO
							b= b//DARK_RATIO
							
							map.set_point(x, y, z, (r,g,b))
				print "ed"
			protocol.on_map_change(self, map)

	class LightConnection(connection):
		light_put = False
		nowput=[]

		def on_block_build_attempt(self, x, y, z):	
			if self.light_put:
				self.protocol.moto_blocks[(x, y, z)] = (255,255,255)
				self.light_put = False
				set_color = SetColor()
				set_color.value = make_color(255,255,255)
				set_color.player_id = 32
				self.protocol.send_contained(set_color)
				block_action.player_id = 32
				block_action.value=BUILD_BLOCK
				block_action.x = x
				block_action.y = y
				block_action.z = z
				self.protocol.send_contained(block_action)
				self.protocol.map.set_point(x, y, z, (255,255,255))
				self.protocol.light_spot.append((x,y,z))
				self.light_puted(x,y,z)
				return False
			else:
				self.protocol.moto_blocks[(x, y, z)] = self.color
				color = self.color
				r,g,b  = color
				r= int(r//DARK_RATIO)
				g= int(g//DARK_RATIO)
				b= int(b//DARK_RATIO)
				set_color = SetColor()
				set_color.value = make_color(r,g,b)
				set_color.player_id = 32
				self.protocol.send_contained(set_color)
				block_action.player_id = 32
				block_action.value=BUILD_BLOCK
				block_action.x = x
				block_action.y = y
				block_action.z = z
				self.protocol.send_contained(block_action)
				self.protocol.map.set_point(x, y, z, (r,g,b))
				self.normal_block_puted(x,y,z)
				return False				
			connection.on_block_build_attempt(self, x, y, z)

		def on_line_build_attempt(self, points):
			for point in points:
				x,y,z=point
				self.protocol.moto_blocks[(x, y, z)] = self.color
				color = self.color
				r,g,b  = color
				r= int(r//DARK_RATIO)
				g= int(g//DARK_RATIO)
				b= int(b//DARK_RATIO)
				set_color = SetColor()
				set_color.value = make_color(r,g,b)
				set_color.player_id = 32
				self.protocol.send_contained(set_color)
				block_action.player_id = 32
				block_action.value=BUILD_BLOCK
				block_action.x = x
				block_action.y = y
				block_action.z = z
				self.protocol.send_contained(block_action)
				self.protocol.map.set_point(x, y, z, (r,g,b))
			self.normal_line_puted(points)
			return False	
			return connection.on_line_build_attempt(self, points)

		def on_block_removed(self, xx, yy, zz):
			for spot in self.protocol.light_spot:
				x,y,z=spot
				if (xx,yy,zz)==(x,y,z):
					self.light_broken(x,y,z)
				else:
					dist = ( (x-xx)**2 + (y-yy)**2 + (z-zz)**2 )**0.5
					if dist<=light_R:
						if self.shade_shield(x,y,z,xx,yy,zz):
							self.light_puted(x,y,z)
			connection.on_block_removed(self, xx, yy, zz)

		def light_broken(self,x,y,z):
			self.protocol.light_spot.remove((x,y,z))
			near_light=[]
			for spot in self.protocol.light_spot:
				x2,y2,z2=spot			
				dist = ( (x-x2)**2 + (y-y2)**2 + (z-z2)**2 )**0.5
				if dist<=light_R*2:
					near_light.append((x2,y2,z2))


			for xx in range(x-light_R, x+light_R+1):
				for yy in range(y-light_R, y+light_R+1):
					for zz in range(z-light_R, z+light_R+1):
						if 0<=xx<=511 and 0<=yy<=511 and 0<=zz<=63:
							if self.protocol.map.get_solid(xx, yy, zz):
								dist = ( (x-xx)**2 + (y-yy)**2 + (z-zz)**2 )**0.5
								if dist<=light_R:
									only_light = True
									if near_light !=[]:
										for (x2,y2,z2) in near_light:
											distance = ( (xx-x2)**2 + (yy-y2)**2 + (zz-z2)**2 )**0.5
											if distance<=light_R:
												only_light = False
									if only_light:
										if (xx, yy, zz) in self.protocol.moto_blocks:
											if self.protocol.moto_blocks[(xx, yy, zz)]!=(0,0,0):
												color = self.protocol.moto_blocks[(xx, yy, zz)]
												r,g,b  = color
												r= int(r//DARK_RATIO)
												g= int(g//DARK_RATIO)
												b= int(b//DARK_RATIO)
												if self.protocol.map.get_color(xx, yy, zz) != (r,g,b):
													block_action = BlockAction()
													block_action.player_id = self.player_id
													block_action.value = DESTROY_BLOCK
													block_action.x = xx
													block_action.y = yy
													block_action.z = zz
													self.protocol.send_contained(block_action)
													self.protocol.map.remove_point(xx, yy, zz)
													block_action = BlockAction()
													set_color = SetColor()
													set_color.value = make_color(r,g,b)
													set_color.player_id = 32
													self.protocol.send_contained(set_color)
													block_action.player_id = 32
													block_action.value=BUILD_BLOCK
													block_action.x = xx
													block_action.y = yy
													block_action.z = zz
													self.protocol.send_contained(block_action)
													self.protocol.map.set_point(xx, yy, zz, (r,g,b))												
			if near_light !=[]:
				for (x2,y2,z2) in near_light:
					self.dark_light(x2,y2,z2,1)

		def dark_light(self,x,y,z,dark):
			self.light_puted(x,y,z,dark)
			self.nowput=[]
			near_light=[]
			for spot in self.protocol.light_spot:
				x2,y2,z2=spot			
				dist = ( (x-x2)**2 + (y-y2)**2 + (z-z2)**2 )**0.5
				if dist<=light_R*2:
					near_light.append((x2,y2,z2))
			if near_light !=[]:
				for (x2,y2,z2) in near_light:
					self.light_puted(x2,y2,z2)
	
		
		def normal_line_puted(self,points):
			upd_light=[]

			for (xx,yy,zz) in points:
				self.nowput.append((xx,yy,zz))		
				for spot in self.protocol.light_spot:
					x,y,z=spot
					dist = ( (x-xx)**2 + (y-yy)**2 + (z-zz)**2 )**0.5
					if dist<=light_R:
						if self.shade_shield(x,y,z,xx,yy,zz):
							if not (x,y,z) in upd_light:
								upd_light.append((x,y,z))
								self.dark_light(x,y,z,2)
			self.nowput=[]

		def normal_block_puted(self,xx,yy,zz):
			self.nowput.append((xx,yy,zz))	
			for spot in self.protocol.light_spot:
				x,y,z=spot
				dist = ( (x-xx)**2 + (y-yy)**2 + (z-zz)**2 )**0.5
				if dist<=light_R:
					if self.shade_shield(x,y,z,xx,yy,zz):
						self.dark_light(x,y,z,2)
			self.nowput=[]

		def shade_shield_now(self,x,y,z,xx,yy,zz):	# T:lightning  F:in shade
			blocked=False
			xb,yb,zb = x+0.5,y+0.5,z+0.5
			xs=min(x,xx)
			xd=max(x,xx)
			ys=min(y,yy)
			yd=max(y,yy)
			zs=min(z,zz)
			zd=max(z,zz)
			unblocked=0
			for xk in [xx+0.0000011,xx+0.9999995]:
				for yk in [yy+0.0000012,yy+0.9999994]:
					for zk in [zz+0.0000013,zz+0.9999996]:
						for xtt in range(xs+1, xd+1):
							for xt in [xtt-0.3,xtt-0.001,xtt+0.001,xtt+0.3]:
								if xs+1<=xt<=xd:
									xn=(xt*1.0-xb)/(xk*1.0-xb)
									yt = floor(xn*(yk-yb)+yb)
									zt = floor(xn*(zk-zb)+zb)
									if (xt, yt, zt)!=(x,y,z) and (xx, yy, zz)!=(xt, yt, zt):
										if (int(xt), int(yt), int(zt)) in self.nowput:
											blocked=True
											break
						if not blocked:
							for ytt in range(ys+1, yd+1):
								for yt in [ytt-0.3,ytt-0.001,ytt+0.001,ytt+0.3]:
									if ys+1<=yt<=yd:
										yn = (yt*1.0-yb)/(yk*1.0-yb)
										xt = floor(xb+(xk*1.0-xb)*yn)
										zt = floor(zb+(zk*1.0-zb)*yn)
										if (xt, yt, zt)!=(x,y,z) and (xx, yy, zz)!=(xt, yt, zt):
											if (int(xt), int(yt), int(zt)) in self.nowput:
												blocked=True
												break
						if not blocked:
							for ztt in range(zs+1, zd+1):
								for zt in [ztt-0.3,ztt-0.001,ztt+0.001,ztt+0.3]:
									if zs+1<=zt<=zd:
										zn = (zt*1.0-zb)/(zk*1.0-zb)
										yt = floor(yb+(yk*1.0-yb)*zn)
										xt = floor(xb+(xk*1.0-xb)*zn)
										if (xt, yt, zt)!=(x,y,z) and (xx, yy, zz)!=(xt, yt, zt):
											if (int(xt), int(yt), int(zt)) in self.nowput:
												blocked=True
												break
						if blocked==True:
							return True
			return False

		def shade_shield(self,x,y,z,xx,yy,zz):	# T:lightning  F:in shade
			if self.nowput!=[]:
				if not self.shade_shield_now(x,y,z,xx,yy,zz):return True
									
			blocked=False
			xb,yb,zb = x+0.5,y+0.5,z+0.5
			xs=min(x,xx)
			xd=max(x,xx)
			ys=min(y,yy)
			yd=max(y,yy)
			zs=min(z,zz)
			zd=max(z,zz)
			unblocked=0
			for xk in [xx+0.0000011,xx+0.9999995]:
				for yk in [yy+0.0000012,yy+0.9999994]:
					for zk in [zz+0.0000013,zz+0.9999996]:
						for xtt in range(xs+1, xd+1):
							if blocked:break
							for xt in [xtt-0.3,xtt-0.001,xtt+0.001,xtt+0.3]:
								if xs+1<=xt<=xd:
									xn=(xt*1.0-xb)/(xk*1.0-xb)
									yt = floor(xn*(yk-yb)+yb)
									zt = floor(xn*(zk-zb)+zb)
									if (xt, yt, zt)!=(x,y,z) and (xx, yy, zz)!=(xt, yt, zt):
										if self.protocol.map.get_solid(xt, yt, zt):	
											blocked=True
											break
						if not blocked:
							for ytt in range(ys+1, yd+1):
								for yt in [ytt-0.3,ytt-0.001,ytt+0.001,ytt+0.3]:
									if ys+1<=yt<=yd:
										yn = (yt*1.0-yb)/(yk*1.0-yb)
										xt = floor(xb+(xk*1.0-xb)*yn)
										zt = floor(zb+(zk*1.0-zb)*yn)
										if (xt, yt, zt)!=(x,y,z) and (xx, yy, zz)!=(xt, yt, zt):
											if self.protocol.map.get_solid(xt, yt, zt):	
												blocked=True
												break
						if not blocked:
							for ztt in range(zs+1, zd+1):
								for zt in [ztt-0.3,ztt-0.001,ztt+0.001,ztt+0.3]:
									if zs+1<=zt<=zd:
										zn = (zt*1.0-zb)/(zk*1.0-zb)
										yt = floor(yb+(yk*1.0-yb)*zn)
										xt = floor(xb+(xk*1.0-xb)*zn)
										if (xt, yt, zt)!=(x,y,z) and (xx, yy, zz)!=(xt, yt, zt):
											if self.protocol.map.get_solid(xt, yt, zt):	
												blocked=True
												break

						if blocked==False:
							unblocked+=1
							if unblocked>=2:
								return True
						blocked=False
			return False

		def light_puted(self,x,y,z,darken=0):
			for xx in range(x-light_R, x+light_R+1):
				for yy in range(y-light_R, y+light_R+1):
					for zz in range(z-light_R, z+light_R+1):
						if 0<=xx<=511 and 0<=yy<=511 and 0<=zz<=63:
							if self.protocol.map.get_solid(xx, yy, zz):
								dist = ( (x-xx)**2 + (y-yy)**2 + (z-zz)**2 )**0.5
								if dist<=light_R:
									if (xx,yy,zz)!=(x,y,z):
										if (xx, yy, zz) in self.protocol.moto_blocks:
											if self.protocol.moto_blocks[(xx, yy, zz)]!=(0,0,0):
												if darken==2:
													if not self.shade_shield(x,y,z,xx,yy,zz):
														color = self.protocol.moto_blocks[(xx, yy, zz)]
														r,g,b  = color
														r= int(r//DARK_RATIO)
														g= int(g//DARK_RATIO)
														b= int(b//DARK_RATIO)
														if self.protocol.map.get_color(xx, yy, zz) != (r,g,b):
															block_action = BlockAction()
															block_action.player_id = self.player_id
															block_action.value = DESTROY_BLOCK
															block_action.x = xx
															block_action.y = yy
															block_action.z = zz
															self.protocol.send_contained(block_action)
															self.protocol.map.remove_point(xx, yy, zz)
															block_action = BlockAction()
															set_color = SetColor()
															set_color.value = make_color(r,g,b)
															set_color.player_id = 32
															self.protocol.send_contained(set_color)
															block_action.player_id = 32
															block_action.value=BUILD_BLOCK
															block_action.x = xx
															block_action.y = yy
															block_action.z = zz
															self.protocol.send_contained(block_action)
															self.protocol.map.set_point(xx, yy, zz, (r,g,b))	

												elif darken==1:
													if self.shade_shield(x,y,z,xx,yy,zz):
														color = self.protocol.moto_blocks[(xx, yy, zz)]
														meido = max(self.protocol.map.get_color(xx, yy, zz))
														if dist<=light_max:
															r,g,b  = color
														else:
															light_power_ratio = (dist - light_max*1.0)/(light_R*1.0-light_max)
															light_power = light_power_ratio * (DARK_RATIO-1.0)+1
															r,g,b  = color
															r= int(r//light_power)
															g= int(g//light_power)
															b= int(b//light_power)
														if self.protocol.map.get_color(xx, yy, zz) != (r,g,b):
															block_action = BlockAction()
															block_action.player_id = self.player_id
															block_action.value = DESTROY_BLOCK
															block_action.x = xx
															block_action.y = yy
															block_action.z = zz
															self.protocol.send_contained(block_action)
															self.protocol.map.remove_point(xx, yy, zz)
															block_action = BlockAction()
															set_color = SetColor()
															set_color.value = make_color(r,g,b)
															set_color.player_id = 32
															self.protocol.send_contained(set_color)
															block_action.player_id = 32
															block_action.value=BUILD_BLOCK
															block_action.x = xx
															block_action.y = yy
															block_action.z = zz
															self.protocol.send_contained(block_action)
															self.protocol.map.set_point(xx, yy, zz, (r,g,b))	
													else:
														color = self.protocol.moto_blocks[(xx, yy, zz)]
														r,g,b  = color
														r= int(r//DARK_RATIO)
														g= int(g//DARK_RATIO)
														b= int(b//DARK_RATIO)
														if self.protocol.map.get_color(xx, yy, zz) != (r,g,b):
															block_action = BlockAction()
															block_action.player_id = self.player_id
															block_action.value = DESTROY_BLOCK
															block_action.x = xx
															block_action.y = yy
															block_action.z = zz
															self.protocol.send_contained(block_action)
															self.protocol.map.remove_point(xx, yy, zz)
															block_action = BlockAction()
															set_color = SetColor()
															set_color.value = make_color(r,g,b)
															set_color.player_id = 32
															self.protocol.send_contained(set_color)
															block_action.player_id = 32
															block_action.value=BUILD_BLOCK
															block_action.x = xx
															block_action.y = yy
															block_action.z = zz
															self.protocol.send_contained(block_action)
															self.protocol.map.set_point(xx, yy, zz, (r,g,b))														
												else:
													if self.shade_shield(x,y,z,xx,yy,zz):
														color = self.protocol.moto_blocks[(xx, yy, zz)]
														meido = max(self.protocol.map.get_color(xx, yy, zz))
														if dist<=light_max:
															r,g,b  = color
														else:
															light_power_ratio = (dist - light_max*1.0)/(light_R*1.0-light_max)
															light_power = light_power_ratio * (DARK_RATIO-1.0)+1
															r,g,b  = color
															r= int(r//light_power)
															g= int(g//light_power)
															b= int(b//light_power)
														if max(r,g,b)>meido:
															if self.protocol.map.get_color(xx, yy, zz) != (r,g,b):
																block_action = BlockAction()
																block_action.player_id = self.player_id
																block_action.value = DESTROY_BLOCK
																block_action.x = xx
																block_action.y = yy
																block_action.z = zz
																self.protocol.send_contained(block_action)
																self.protocol.map.remove_point(xx, yy, zz)
																block_action = BlockAction()
																set_color = SetColor()
																set_color.value = make_color(r,g,b)
																set_color.player_id = 32
																self.protocol.send_contained(set_color)
																block_action.player_id = 32
																block_action.value=BUILD_BLOCK
																block_action.x = xx
																block_action.y = yy
																block_action.z = zz
																self.protocol.send_contained(block_action)
																self.protocol.map.set_point(xx, yy, zz, (r,g,b))												
											
	return LightProtocol,LightConnection