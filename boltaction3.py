# -*- coding: utf-8 -*-
"""
by yuyasato

今のところライフルとSMGのみ対応
マガジンサイズを「減らす」スクリプト
デフォより弾数増やすとバグる
マガジンのサイズと携行数を指定するだけのはず
マガジンフルでもリロードできちゃうのはちょっと回避できなかった

ver3:ライフル専用

"""
from twisted.internet.task import LoopingCall
from twisted.internet.reactor import callLater
from pyspades.server import weapon_reload
import math
from pyspades.constants import *
from pyspades.server import weapon_reload
from commands import add, admin, name, get_player, alias
import commands


Rifle_MAGAZINE_size	= 1
Rifle_MAGAZINE_number	= 30




def apply_script(protocol, connection, config):
	class BoltConnection(connection):


		def on_spawn(self,pos):
			if self.team == self.protocol.blue_team and self.weapon == 0:
				MAGAZINE_size=Rifle_MAGAZINE_size
				MAGAZINE_number=Rifle_MAGAZINE_number	
			   	weapon_reload.clip_ammo = MAGAZINE_size			
				weapon_reload.reserve_ammo = MAGAZINE_size * MAGAZINE_number		#(表示右)残弾数
				self.weapon_object.current_stock = weapon_reload.reserve_ammo	#現在の残弾数に代入(表示右)　この二つの違いよくわからんがとりあえず
				self.weapon_object.current_ammo = weapon_reload.clip_ammo		#現在の銃弾数に代入		
				self.send_contained(weapon_reload)				#これ入れないとリロード後弾撃てなくなる気がする


			return connection.on_spawn(self,pos)


		def _on_reload(self):
			if self.team == self.protocol.blue_team and self.weapon == 0:
				callLater(0.01, self.reload_after)		#正規の装填アクション終了後にマガジンサイズを無理やり変更
				weapon_reload.player_id = self.player_id
				weapon_reload.clip_ammo = self.weapon_object.current_ammo
				weapon_reload.reserve_ammo = self.weapon_object.current_stock
				self.send_contained(weapon_reload)
			return connection._on_reload(self)
		   
		def reload_after(self):
			if self.team == self.protocol.blue_team and self.weapon == 0:
				weapon_reload.player_id = self.player_id
				MAGAZINE_size=Rifle_MAGAZINE_size

				if self.weapon_object.current_ammo >MAGAZINE_size:
					weapon_reload.clip_ammo = MAGAZINE_size			#装填後の弾数を代入
					weapon_reload.reserve_ammo += self.weapon_object.current_ammo-MAGAZINE_size		#(表示右)残弾数＝今リロードされた直後だから、残弾数＝現在残弾数(デフォ)＋（現在残弾数(デフォ)-マガジン）
				
				self.weapon_object.current_stock = weapon_reload.reserve_ammo	#現在の残弾数に代入(表示右)　この二つの違いよくわからんがとりあえず
				self.weapon_object.current_ammo = weapon_reload.clip_ammo		#現在の銃弾数に代入		
				self.send_contained(weapon_reload)
	
	return protocol, BoltConnection