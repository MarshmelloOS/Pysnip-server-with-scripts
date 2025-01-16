# -*- coding: utf-8 -*-
"""
kankeri2017/7/15

佐藤裕也

"""
#ここからスクリプト
from pyspades.server import create_player, player_left, intel_capture
from twisted.internet import reactor
from commands import admin, add, name, get_team, get_player,alias
from pyspades.common import Vertex3
from pyspades.world import Grenade
from pyspades.server import grenade_packet
import random
import math
from pyspades.contained import *
from pyspades.server import *
from pyspades.common import *
from twisted.internet.reactor import callLater,seconds

move_object = loaders.MoveObject()

AREA_R = 128

@alias('cp')
@name('canpos')
def canpos(connection, area=64):
	if connection.protocol.kankeri_started:
		return "already started"
	global AREA_R
	AREA_R = int(area)
	returned = connection.kankeri_start()
	return returned
add(canpos)

def apply_script(protocol,connection,config):

	class TentmoveConnection(connection):
		resp=False


		def invalid_build_position(self, x, y, z):
			kx,ky,kz = self.protocol.canpos_centar
			if (x-kx)**2+(y-ky)**2<100:
				return True
			return False

		def on_block_build_attempt(self, x, y, z):
			if self.invalid_build_position(x, y, z):
				return False
			return connection.on_block_build_attempt(self, x, y, z)

		def on_line_build_attempt(self, points):
			for point in points:
				if self.invalid_build_position(*point):
					return False
			return connection.on_line_build_attempt(self, points)

		def on_block_destroy(self, x, y, z, mode):
			if self.invalid_build_position(x, y, z):
				return False
			return connection.on_block_destroy(self, x, y, z, mode)

		def paint_ground(self,x,y,z,color):
			if 0<=x<=511 and 0<=y<=511 and 0<=z<=62:
				block_action = BlockAction()
				block_action.player_id = self.player_id
				block_action.value = DESTROY_BLOCK
				block_action.x = x
				block_action.y = y
				block_action.z = z
				self.protocol.send_contained(block_action)
				self.protocol.map.remove_point(x, y, z)
				set_color = SetColor()
				set_color.value = make_color(*color)
				set_color.player_id = 32
				self.protocol.send_contained(set_color)
				block_action.player_id = 32
				block_action.value=BUILD_BLOCK
				block_action.x = x
				block_action.y = y
				block_action.z = z
				self.protocol.send_contained(block_action)
				self.protocol.map.set_point(x, y, z, color)


		def kankeri_start(self):
					#kan start pos check
			x,y,z=self.world_object.position.get()
			point_clear=0
			for xx in [-4,-3,-2,-1,0,1,2,3,4]:
				for yy in [-4,-3,-2,-1,0,1,2,3,4]:
						point_clear += self.protocol.map.get_solid(x+xx,y+yy,z+2)
						point_clear += not self.protocol.map.get_solid(x+xx,y+yy,z+3)
						if point_clear>0:break
			if point_clear!=0:
				return "here is bad pos"
			else:  #good pos
					#paint ground
				for xx in [-4,-3,-2,-1,0,1,2,3,4]:
					for yy in [-4,4]:
						xxx = x+xx
						yyy = y+yy
						zzz = z+3	
						color = (255,0,0)		
						self.paint_ground(xxx,yyy,zzz,color)

				for xx in [-4,4]:
					for yy in [-3,-2,-1,0,1,2,3]:
						xxx = x+xx
						yyy = y+yy
						zzz = z+3	
						color = (255,0,0)		
						self.paint_ground(xxx,yyy,zzz,color)

				xxx = x
				yyy = y
				zzz = z+3	
				color = (255,0,0)		
				self.paint_ground(xxx,yyy,zzz,color)

				for xc in range(-11, 11):
					for yc in range(-11, 11):
						if 90<xc**2+yc**2<115:
							xe,ye,ze = x+xc,y+yc,self.protocol.map.get_z(x+xc, y+yc)
							color = (255,128,0)
							self.paint_ground(xe,ye,ze,color)

				for xc in range(-1*AREA_R-1,AREA_R+1):
					for yc in range(-1*AREA_R-1,AREA_R+1):
						if (AREA_R-0.5)**2<xc**2+yc**2<(AREA_R+0.5)**2:
							xe,ye,ze = x+xc,y+yc,self.protocol.map.get_z(x+xc, y+yc)
							color = (255,0,0)
							self.paint_ground(xe,ye,ze,color)

						#can start pos set
				move_object.object_type = 0
				b_intel = self.protocol.blue_team.flag
				kx,ky,kz = x,y,self.protocol.map.get_z(x, y, z)
				self.protocol.canpos_centar=kx,ky,kz
				self.protocol.canpos_now=kx,ky,kz
				location = [kx,ky,kz]
				b_intel.set(*location)
				move_object.x = kx
				move_object.y = ky
				move_object.z = kz
				self.protocol.send_contained(move_object)
				self.protocol.kankeri_started=True
				return "pos set"	

		def on_position_update(self):
			if self.hp or self.hp>0:	
				if self.team == self.protocol.blue_team:
					kx,ky,kz = self.protocol.canpos_centar
					xb,yb,zb = self.world_object.position.get()
					if (kx-xb)**2 + (ky-yb)**2 >(AREA_R + 1)**2 and self.protocol.kankeri_started:
						self.set_hp(self.hp - 24)
					if not self.protocol.cankicked:		
						if self.protocol.blue_team.flag.player is None and vector_collision(self.world_object.position, self.protocol.blue_team.flag):
							self.cankicked()	

		def cankicked(self):
			vx,vy,vz = self.world_object.velocity.get()
			self.protocol.cankicked=True

				#player respawn
			kx,ky,kz = self.protocol.canpos_centar
			sx,sy,sz = kx,ky,kz-2
			for player in self.protocol.blue_team.get_players():
				if player.hp is None or player.hp<=0 or player.world_object.dead:
					player.spawn((sx,sy,sz))	
					pos = sx,sy,sz 
					player.set_location(pos)

				#fly can
			kx,ky,kz = self.protocol.canpos_now
			self.protocol.kan_gre = self.protocol.world.create_object(Grenade, 45, Vertex3(kx,ky,kz-1), None, Vertex3(vx*2, vy*2, -1), None)
			self.protocol.can_fly()

		def respawn(self):
			if self.team.spectator or self.resp:
				self.spawn_call = callLater(0.01, self.spawn)
				self.resp=False
			else:
				if self.spawn_call is None:
					self.spawn_call = callLater(114514,None)
				return False
			return connection.respawn(self)	
		
		def on_kill(self, killer, type, grenade):
			self.set_location(self.protocol.canpos_centar)
			living = 0
			for player in self.protocol.blue_team.get_players():
				living += player.hp>0 and not self.world_object.dead
			if living >0:
				self.protocol.send_chat("%s attacker alive."%living)
			else:
				self.protocol.send_chat("All attacker were killed. Defence team win.")
				if killer is None:
					for killer in self.protocol.green_team.get_players():	
						break
				else:
					if killer.team != self.protocol.green_team:
						for killer in self.protocol.green_team.get_players():	
							break
				self.protocol.reset_game(killer)		
				self.protocol.on_game_end()	
			if type<5:
				self.respawn_time = -1
			else:
				self.resp=True
			connection.on_kill(self, killer, type, grenade)	

		def on_flag_take(self):
			if not self.protocol.cankicked:
				return False
			return connection.on_flag_take(self)

			
		def on_hit(self, hit_amount, hit_player, type, grenade):
			if self.protocol.cankicked or hit_player.team == self.protocol.green_team:
				return False
			connection.on_hit(self, hit_amount, hit_player, type, grenade)

		def on_animation_update(self, jump, crouch, sneak, sprint):
			if self == self.team.other.flag.player:
				xp,yp,zp = self.world_object.position.get()
				kx,ky,kz = self.protocol.canpos_centar
				if kx-3<xp<kx+3 and ky-3<yp<ky+3:
					if crouch and not self.world_object.crouch:
						for player in self.protocol.blue_team.get_players():
							xb,yb,zb = player.world_object.position.get()
							if (kx-xb)**2 + (ky-yb)**2 <10:
								player.kill()
						self.drop_flag()
						self.protocol.cankicked = False
						kan = self.protocol.blue_team.flag
						self.protocol.canpos_now = kan.x, kan.y, kan.z
			return connection.on_animation_update(self, jump, crouch, sneak, sprint)

		def on_reset(self):
			self.resp=False
			return connection.on_reset(self)

	class TentmoveProtocol(protocol,TentmoveConnection):
		cankicked=False
		canpos_centar = 0,0,0
		canpos_now = 0,0,0
		kan_gre = None
		kankeri_started=False

		def on_map_leave(self):
			self.cankicked=False
			self.canpos_centar = 0,0,0
			self.canpos_now = 0,0,0
			self.kan_gre = None
			self.kankeri_started=False
			protocol.on_map_leave(self)

		def can_fly(self,x=-100,y=-100,z=-100,d1=100,d2=100,d3=100,d4=100,d5=100):
			xg,yg,zg =self.kan_gre.position.get()
			d5=d4
			d4=d3
			d3=d2
			d2=d1
			d1= (x-xg)**2 + (y-yg)**2 + (z-zg)**2
			if 0<=xg<=511 and 0<=yg<=511:
				if d1+d2+d3+d4+d5!=0 and  self.blue_team.flag.player is None:
					move_object.object_type = 0
					b_intel = self.blue_team.flag
					location = [xg,yg,zg]
					b_intel.set(*location)
					move_object.x = xg
					move_object.y = yg
					move_object.z = zg
					self.send_contained(move_object)
					callLater(0.01, self.can_fly,xg,yg,zg,d1,d2,d3,d4,d5)
			else:
				xg,yg,zg = xg,yg,self.map.get_z(xg, yg)
				move_object.object_type = 0
				b_intel = self.blue_team.flag
				location = [xg,yg,zg]
				b_intel.set(*location)
				move_object.x = xg
				move_object.y = yg
				move_object.z = zg
				self.send_contained(move_object)

		def on_world_update(self):
			for player in self.blue_team.get_players():
				if (player.hp or player.hp>0) and not player.world_object.dead:	
					if not self.cankicked:		
						if self.blue_team.flag.player is None and vector_collision(player.world_object.position, self.blue_team.flag):
							player.cankicked()	
			if self.advance_call is not None and player is not None:
				advance_call = self.advance_call
				timeleft = advance_call.getTime() - seconds()
				if timeleft<=0:
					self.reset_game(player)

			protocol.on_world_update(self)

	return  TentmoveProtocol, TentmoveConnection

