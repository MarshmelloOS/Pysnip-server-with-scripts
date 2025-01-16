"""
this script enable config.txt setting change command in server

/adv 		: advance
/tfd        : toggle falldamage
/ttl [min]  : default timelimit set
/tcl [num]  : default capturelimit set
/taow       : toggle advance on win
/trt [sec]  : default respawn time set
/trw        : toggle respawn wave
/ttk        : toggle teamkill
/ttsi [min] : teamswitch interval set
/tmp [num]  : max player set
/tmd [dmg]  : melee damage set
/tbt [num]  : balanced teams set
/ttc [1 or 2] [r][g][b] : team color change
/ttn [1 or 2] [teamname] : team name change
/tgm        : toggle game mode ( CTF <--> TC )




"""
from pyspades.constants import *
from commands import alias, admin, add, name, get_team, get_player
from twisted.internet.reactor import callLater


@alias('adv')
@name('adv_advance')
def adv_advance(connection):
	connection.protocol.send_chat("advance forced.")
	callLater(0.1, connection.protocol.advance_rotation)
add(adv_advance)

@alias('ttc')
@name('toggleteamcolor')
def toggleteamcolor(connection, teamnum, r,g,b):
	protocol = connection.protocol
	teamnum=int(teamnum)
	if not(1<=teamnum<=2):
		return "team number should be written in 1 or 2"
	r=int(r)
	if not(0<=r<=255):
		return "color value is 0-255"
	g=int(g)
	if not(0<=g<=255):
		return "color value is 0-255"
	b=int(b)
	if not(0<=b<=255):
		return "color value is 0-255"
	if teamnum==1:
		protocol.team1_color = (r,g,b)
		protocol.blue_team.color = (r,g,b)
	elif teamnum==2:
		protocol.team2_color = (r,g,b)
		protocol.green_team.color = (r,g,b)

	message = "team%d color set (%d,%d,%d)"%(teamnum,r,g,b)
	print message
	return protocol.send_chat(message)	
add(toggleteamcolor)

@alias('ttn')
@name('toggleteamname')
def toggleteamname(connection, teamnum, teamname):
	protocol = connection.protocol
	teamnum=int(teamnum)
	if not(1<=teamnum<=2):
		return "team number should be written in 1 or 2"
	if len(teamname)>9:
		return "Too long! Teamname should be shorter than 9 letters."
	if teamnum==1:
		protocol.team1_name = teamname
		protocol.blue_team.name = teamname

	elif teamnum==2:
		protocol.team2_name = teamname
		protocol.green_team.name = teamname

	message = "team%d name set %s"%(teamnum,teamname)
	print message
	return protocol.send_chat(message)	
add(toggleteamname)

@alias('tfd')
@name('togglefalldamage')
def togglefalldamage(connection):
	protocol = connection.protocol
	protocol.fall_damage = not protocol.fall_damage
	if protocol.fall_damage:
		message = "fall damage turned ON"
	else:
		message = "fall damage turned OFF"
	print message
	return protocol.send_chat(message)	
add(togglefalldamage)

@alias('ttl')
@name('toggletimelimit')
def toggletimelimit(connection, value):
	protocol = connection.protocol
	protocol.default_time_limit  = float(value)
	message = "default time limit set %s"%protocol.default_time_limit
	print message
	return protocol.send_chat(message)	
add(toggletimelimit)

@alias('tcl')
@name('togglecapturelimit')
def togglecapturelimit(connection, value):
	protocol = connection.protocol
	protocol.default_cap_limit   = float(value)
	message = "default capture limit set %s"%protocol.default_cap_limit
	print message
	return protocol.send_chat(message)	
add(togglecapturelimit)

@alias('taow')
@name('toggleadvance_on_win ')
def toggleadvance_on_win(connection):
	protocol = connection.protocol
	protocol.advance_on_win  = not protocol.advance_on_win 
	if protocol.advance_on_win :
		message = "advance_on_win turned ON"
	else:
		message = "advance_on_win turned OFF"
	print message
	return protocol.send_chat(message)	
add(toggleadvance_on_win)


@alias('trt')
@name('togglerespawntime')
def togglerespawntime(connection, value):
	protocol = connection.protocol
	value = float(value)
	for player in protocol.players.values():
		if player.respawn_time == protocol.respawn_time:
			player.respawn_time = value
	protocol.respawn_time   = value
	message = "default respawn time set %s"%protocol.respawn_time
	print message
	return protocol.send_chat(message)	
add(togglerespawntime)

@alias('trw')
@name('togglerespawnwave')
def togglerespawnwave(connection):
	protocol = connection.protocol
	protocol.respawn_waves   = not protocol.respawn_waves  
	if protocol.respawn_waves:
		message = "respawn_waves turned ON"
	else:
		message = "respawn_waves turned OFF"
	print message
	return protocol.send_chat(message)	
add(togglerespawnwave)


@alias('ttk')
@name('toggleteamkill2')
def toggleteamkill2(connection):
	protocol = connection.protocol
	protocol.friendly_fire    = not protocol.friendly_fire   
	if protocol.friendly_fire :
		message = "friendly_fire turned OK"
	else:
		message = "friendly_fire turned NG"
	print message
	return protocol.send_chat(message)	
add(toggleteamkill2)

@alias('ttsi')
@name('toggleteamswitchinterval')
def toggleteamswitchinterval(connection, value):
	protocol = connection.protocol
	protocol.teamswitch_interval = float(value)
	message = "default teamswitch_interval set %s"%protocol.teamswitch_interval 
	print message
	return protocol.send_chat(message)	
add(toggleteamswitchinterval)

@alias('tmp')
@name('togglemax_players ')
def togglemax_players (connection, value):
	protocol = connection.protocol
	value=float(value)
	if value<=32:
		protocol.max_players  = value
		message = "default max_players set %s"%protocol.max_players 
		print message
		return protocol.send_chat(message)
	else:
		return "error"
add(togglemax_players)

@alias('tmd')
@name('togglemelee_damage')
def togglemelee_damage(connection, value):
	protocol = connection.protocol
	protocol.melee_damage  = float(value)
	message = "default melee_damage set %s"%protocol.melee_damage  
	print message
	return protocol.send_chat(message)	
add(togglemelee_damage)

@alias('tbt')
@name('togglebalanced_teams')
def togglebalanced_teams(connection, value):
	protocol = connection.protocol
	protocol.balanced_teams   = float(value)
	message = "default balanced_teams set %s"%protocol.balanced_teams   
	print message
	return protocol.send_chat(message)	
add(togglebalanced_teams)

@alias('tgm')
@name('togglegamemode')
def togglegamemode(connection):
	protocol = connection.protocol
	if protocol.game_mode == CTF_MODE:
		protocol.game_mode = TC_MODE
		message = "game_mode set TC"
	else:
		protocol.game_mode = CTF_MODE
		message = "game_mode set CTF"		 
	print message
	return protocol.send_chat(message)	
add(togglegamemode)

def apply_script(protocol, connection, config):
	return protocol, connection