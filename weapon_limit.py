# -*- coding: utf-8 -*-
"""

Enable or disable weapons

武器制限スクリプト
scripted by yuyasato 20170314

adminコマンド    admin commands 
/tsr    ライフルを規制/規制解除   enable or disable rifle
/tsmg   SMGを規制/規制解除      enable or disable SMG
/tsg    SGを規制/規制解除     enable or disable Shotgun
/tw     武器制限機能を停止/実行   weapon limit function disable or enable
"""

###### 設定項目 ###### default setting items ##########

 # 武器制限設定変更時、制限武器所持のプレイヤーを即死させて強制変更するか(True)、次死んだときに自動変更するようにするか(False)

TOGGLE_LIMIT_IMMEDIATE = False


# 各武器デフォルト制限設定(default setting enable or disable of weapons)
#  True ：武器の使用可能(can use)
#  False：武器の使用不能(can not use)

RIFLE_ENABLED    = True
SHOTGUN_ENABLED  = True
SMG_ENABLED      = True

######## 全部 False にするとエラー吐きます   ### all weapon turning False cause server error. ####


## 設定項目ここまで  ##  default setting items to here only


TOGGLE_LIMIT=True

from commands import add,admin,name
from pyspades.constants import *


@admin
@name("tw")
def toggle_weapon(connection):
	global TOGGLE_LIMIT
	TOGGLE_LIMIT = not TOGGLE_LIMIT
	if TOGGLE_LIMIT:
		if not (RIFLE_ENABLED and SMG_ENABLED and SHOTGUN_ENABLED):
			for player in connection.protocol.players.values():
				if player.team.id>=0:
					if connection.weapon == RIFLE_WEAPON and not RIFLE_ENABLED:
						player.set_weapon(connection.weapon,False,not TOGGLE_LIMIT_IMMEDIATE)
					elif connection.weapon == SMG_WEAPON and not SMG_ENABLED:
						player.set_weapon(connection.weapon,False,not TOGGLE_LIMIT_IMMEDIATE)
					elif connection.weapon == SHOTGUN_WEAPON and not SHOTGUN_ENABLED:
						player.set_weapon(connection.weapon,False,not TOGGLE_LIMIT_IMMEDIATE)
		return connection.protocol.send_chat("Now weapon limited. (rifle:%s, SMG:%s, SG:%s)"%(["NG","OK"][RIFLE_ENABLED],["NG","OK"][SMG_ENABLED],["NG","OK"][SHOTGUN_ENABLED]))
	else:
		return connection.protocol.send_chat("Now no weapon limited. all weapon is OK!")

@admin
@name("tsr")
def toggle_rifle(connection,boolean=None):
	if SMG_ENABLED or SHOTGUN_ENABLED:
		global RIFLE_ENABLED
		RIFLE_ENABLED = not RIFLE_ENABLED
		if not RIFLE_ENABLED and TOGGLE_LIMIT:
			for player in connection.protocol.players.values():
				if player.team.id>=0:
					if connection.weapon == RIFLE_WEAPON:
						player.set_weapon(connection.weapon,False,not TOGGLE_LIMIT_IMMEDIATE)
		return connection.protocol.send_chat("Rifle %sabled.  (rifle:%s, SMG:%s, SG:%s)" %(["dis","en"][RIFLE_ENABLED],["NG","OK"][RIFLE_ENABLED],["NG","OK"][SMG_ENABLED],["NG","OK"][SHOTGUN_ENABLED]))
	else:
		return "You can't disable all weapon."

@admin
@name("tsmg")
def toggle_smg(connection,boolean=None):
	if RIFLE_ENABLED or SHOTGUN_ENABLED:
		global SMG_ENABLED
		SMG_ENABLED = not SMG_ENABLED
		if not SMG_ENABLED and TOGGLE_LIMIT:
			for player in connection.protocol.players.values():
				if player.team.id>=0:
					if connection.weapon == SMG_WEAPON:
						player.set_weapon(connection.weapon,False,not TOGGLE_LIMIT_IMMEDIATE)
		return connection.protocol.send_chat("SMG %sabled.  (rifle:%s, SMG:%s, SG:%s)" %(["dis","en"][SMG_ENABLED],["NG","OK"][RIFLE_ENABLED],["NG","OK"][SMG_ENABLED],["NG","OK"][SHOTGUN_ENABLED]))
	else:
		return "You can't disable all weapon."

@admin
@name("tsg")
def toggle_shotgun(connection,boolean=None):
	if SMG_ENABLED or RIFLE_ENABLED:
		global SHOTGUN_ENABLED
		SHOTGUN_ENABLED = not SHOTGUN_ENABLED
		if not SHOTGUN_ENABLED and TOGGLE_LIMIT:
			for player in connection.protocol.players.values():
				if player.team.id>=0:
					if connection.weapon == SHOTGUN_WEAPON:
						player.set_weapon(connection.weapon,False,not TOGGLE_LIMIT_IMMEDIATE)
		return connection.protocol.send_chat("Shotgun %sabled.  (rifle:%s, SMG:%s, SG:%s)" %(["dis","en"][SHOTGUN_ENABLED],["NG","OK"][RIFLE_ENABLED],["NG","OK"][SMG_ENABLED],["NG","OK"][SHOTGUN_ENABLED]))
	else:
		return "You can't disable all weapon."



add(toggle_weapon)
add(toggle_rifle)
add(toggle_shotgun)
add(toggle_smg)

def check_allweapon(connection):
	if TOGGLE_LIMIT:
		if not (RIFLE_ENABLED and SMG_ENABLED and SHOTGUN_ENABLED):
			for player in connection.protocol.players.values():
				if player.team.id>=0:
					if connection.weapon == RIFLE_WEAPON and not RIFLE_ENABLED:
						player.set_weapon(connection.weapon)
					elif connection.weapon == SMG_WEAPON and not SMG_ENABLED:
						player.set_weapon(connection.weapon)
					elif connection.weapon == SHOTGUN_WEAPON and not SHOTGUN_ENABLED:
						player.set_weapon(connection.weapon)


def apply_script(protocol,connection,config):
	class WeaponlimitConnection(connection):

		def set_weapon(self, weapon, local = False, no_kill = False, *args, **kwargs):
			if TOGGLE_LIMIT:
				if weapon == RIFLE_WEAPON and not RIFLE_ENABLED:
					if SMG_ENABLED:
						self.send_chat("Rifle is disabled, SMG given instead")
						weapon = SMG_WEAPON
					else:
						self.send_chat("Rifle is disabled, Shotgun given instead")
						weapon = SHOTGUN_WEAPON

				elif weapon == SMG_WEAPON and not SMG_ENABLED:
					if SHOTGUN_ENABLED:
						self.send_chat("SMG is disabled, Shotgun given instead")
						weapon = SHOTGUN_WEAPON
					else:
						self.send_chat("SMG is disabled, Rifle given instead")
						weapon = RIFLE_WEAPON

				elif weapon == SHOTGUN_WEAPON and not SHOTGUN_ENABLED:
					if RIFLE_ENABLED:
						self.send_chat("Shotgun is disabled, Rifle given instead")
						weapon = RIFLE_WEAPON
					else:
						self.send_chat("Shotgun is disabled, SMG given instead")
						weapon = SMG_WEAPON
			return connection.set_weapon(self, weapon, local, no_kill, *args, **kwargs)

	return protocol,WeaponlimitConnection
