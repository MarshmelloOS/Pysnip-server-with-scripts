# -*- coding: utf-8 -*-
"""
飛行スクリプト改造型時限凍結スクリプト試作一号

"""

from twisted.internet import reactor
from twisted.internet.reactor import callLater, seconds
from pyspades.constants import *
from pyspades.common import Vertex3
from pyspades.world import Grenade
from pyspades.server import grenade_packet
import commands
from pyspades.constants import UPDATE_FREQUENCY
from easyaos import *
from math import sqrt, acos, degrees


FRIENDRY_FREEZE = True	#True→味方にも効く
BOTH_FLIGHT = True	#True→両方とも飛行／False→FLIGHT_TEAMで指定したチームのみ飛行

FREEZE_TIME = 2		#被弾時の凍結時間[秒]
init_rockets = 0	#初期ロケット所持数 ## 0で無限
COOLDOWN = 20		#凍結ロケットの連発規制時間[秒]
VTradius=2		#あたり判定の大きさ[block]




def apply_script(protocol,connection,config):
	class FlightConnection(connection):
		flying = False
		rocket=False
		rest_rockets=init_rockets
		flighttime=0
		fallfree=False
		last_rocketfire=0

		def flight_reset(self):
			self.flying = False
			self.fallfree = False
			self.rocket=True
			self.rest_rockets = init_rockets
			self.flighttime=0
			self.last_rocketfire=0

		def flight(self, x, y, z, flighttime, victim):
			if self.flying:
				victim.fallfree=True
				flighttime+=1
				if flighttime-1%500 == 0:
					victim.set_location((0, 0, 62))
				else:
					victim.set_location((x, y, z))
				if flighttime < FREEZE_TIME * 1000:
					reactor.callLater(0.001, self.flight, x, y, z, flighttime, victim)
				else:
					self.flying=False
					reactor.callLater(1.0,self.falldamage,victim)

		def on_spawn(self,pos):
			self.flight_reset()
			return connection.on_spawn(self,pos)

		def rockelan(self,connection,(x,y,z),(vx,vy,vz)):
			easyremove(connection,(x,y,z))
			x+=vx*1.5
			y+=vy*1.5
			z+=vz*1.5

			VTfuse = 0
			for player in connection.protocol.players.values():
				if FRIENDRY_FREEZE:
					if not (player==self or player.god or player.team.spectator):		#全プレイヤーの位置を取得
						xa,ya,za = player.get_location()
						xr,yr,zr=xa-x,ya-y,za-z
						radius= sqrt(xr**2 + yr**2 + zr**2)
						if radius<VTradius:						#ロケットとの距離が2より近いやつがいれば信管作動
							VTfuse=1
							victim=player
							break
				else:

					if not (player==self or player.god or player.team == connection.team or player.team.spectator):		#敵プレイヤーの位置を取得
						xa,ya,za = player.get_location()
						xr,yr,zr=xa-x,ya-y,za-z
						radius= sqrt(xr**2 + yr**2 + zr**2)
						if radius<VTradius:						#ロケットとの距離が2より近いやつがいれば信管作動
							VTfuse=1
							victim=player
							break

			if connection.protocol.map.get_solid(x,y,z) or x<2 or x>509 or y<2 or y>509 or z<2 or z>63 or VTfuse==1:
				if connection.protocol.map.get_solid(x,y,z)  or VTfuse==1:
					grenade_packet.value=0.0
					grenade_packet.player_id=connection.player_id
					grenade_packet.position=(x,y,z)
					grenade_packet.velocity=(0,0,0)
					self.protocol.send_contained(grenade_packet)
					if VTfuse == 1:
						self.flying=True
						self.flight(xa, ya, za, 0, victim)

			else:
				reactor.callLater(0.03,self.rockelan,connection,(x,y,z),(vx,vy,vz))
				easyblock(connection,(x,y,z),(70,90,40))

		def rocket_charge(self):
			self.rocket=True
			self.send_chat("Freeze rocket reloaded!")
		
		def on_animation_update(self,jump,crouch,sneak,sprint):
			if  sneak and not self.world_object.secondary_fire:	
            			remaining = COOLDOWN-(seconds() - self.last_rocketfire) +1
				if remaining > 0:
					self.send_chat("%s second WAIT! rocket reloading "% int(remaining))
				else:
					self.send_chat("Freeze rocket has been reloaded!")
			if  sneak and self.world_object.secondary_fire:		#ロケット発射
				if init_rockets==0:
					self.rest_rockets=100
				if self.rest_rockets>0:
					if not self.rocket:
            					remaining = COOLDOWN-(seconds() - self.last_rocketfire) +1
						self.send_chat("%s second WAIT! rocket reloading "% int(remaining))	
					else:
						self.rocket=False
						x,y,z=self.world_object.position.get()
						vx,vy,vz = self.world_object.orientation.get()
						self.rockelan(self,(x+vx,y+vy,z+vz),(vx*0.8,vy*0.8,vz*0.8))
						self.rest_rockets-=1
            					self.last_rocketfire = seconds()
						self.send_chat("The rest Rocket is  %s "% self.rest_rockets)
						reactor.callLater(COOLDOWN,self.rocket_charge)
				else:
					self.send_chat("You have used all Rocket.")

			
			return connection.on_animation_update(self,jump,crouch,sneak,sprint)

		def falldamage(self,victim):
			victim.fallfree=False
		
		def on_fall(self, damage):
			if self.fallfree:
				return False
			else:
				return connection.on_fall(self, damage)
		
		def on_kill(self,killer,type,grenade):
			self.flight_reset()
			return connection.on_kill(self,killer,type,grenade)
		
		def on_team_leave(self):
			self.flying=False
			self.flight_reset()
			return connection.on_team_leave(self)

		def on_disconnect(self):
			self.flying = False
			return connection.on_disconnect(self)

	    
	return protocol, FlightConnection