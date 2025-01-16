# -*- coding: utf-8 -*-
"""
by yuyasato

���̂Ƃ��냉�C�t����SMG�̂ݑΉ�
�}�K�W���T�C�Y���u���炷�v�X�N���v�g
�f�t�H���e�����₷�ƃo�O��
�}�K�W���̃T�C�Y�ƌg�s�����w�肷�邾���̂͂�
�}�K�W���t���ł������[�h�ł����Ⴄ�̂͂�����Ɖ���ł��Ȃ�����

ver3:���C�t����p

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
				weapon_reload.reserve_ammo = MAGAZINE_size * MAGAZINE_number		#(�\���E)�c�e��
				self.weapon_object.current_stock = weapon_reload.reserve_ammo	#���݂̎c�e���ɑ��(�\���E)�@���̓�̈Ⴂ�悭�킩��񂪂Ƃ肠����
				self.weapon_object.current_ammo = weapon_reload.clip_ammo		#���݂̏e�e���ɑ��		
				self.send_contained(weapon_reload)				#�������Ȃ��ƃ����[�h��e���ĂȂ��Ȃ�C������


			return connection.on_spawn(self,pos)


		def _on_reload(self):
			if self.team == self.protocol.blue_team and self.weapon == 0:
				callLater(0.01, self.reload_after)		#���K�̑��U�A�N�V�����I����Ƀ}�K�W���T�C�Y�𖳗����ύX
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
					weapon_reload.clip_ammo = MAGAZINE_size			#���U��̒e������
					weapon_reload.reserve_ammo += self.weapon_object.current_ammo-MAGAZINE_size		#(�\���E)�c�e�����������[�h���ꂽ���ゾ����A�c�e�������ݎc�e��(�f�t�H)�{�i���ݎc�e��(�f�t�H)-�}�K�W���j
				
				self.weapon_object.current_stock = weapon_reload.reserve_ammo	#���݂̎c�e���ɑ��(�\���E)�@���̓�̈Ⴂ�悭�킩��񂪂Ƃ肠����
				self.weapon_object.current_ammo = weapon_reload.clip_ammo		#���݂̏e�e���ɑ��		
				self.send_contained(weapon_reload)
	
	return protocol, BoltConnection