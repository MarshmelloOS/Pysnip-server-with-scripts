#	These commands are standard pyspades commands optimized for BUILD servers.
#	gt is goto that drops you from the top of build area. Must have no fall damage.
# 	gts is a silent goto command.  Remove "@admin" to make public.
#	letsfly is a public fly command that only works for the person using it.
#	 - Prevents annoying use of fly command on other players.

#	Customizations developed on SuperCool Build plus Platforms by JohnRambozo.
#	Stop by anytime or email johnrambozosc@gmail.com with questions or comments.

from pyspades.common import coordinates, to_coordinates
from pyspades.server import orientation_data
from commands import add, admin, get_player, alias, name
from map import Map
from pyspades.constants import *
import commands
from twisted.internet import reactor
import cuboid

def gt(connection, value):
    if connection not in connection.protocol.players:
        raise KeyError()
    move_helper(connection, connection.name, value, silent = connection.invisible)
add(gt)
	
@admin
def gts(connection, value):
    if connection not in connection.protocol.players:
        raise KeyError()
    move_helper(connection, connection.name, value, silent = True)
add(gts)
	
def move_helper(connection, player, value, silent = False):
    player = get_player(connection.protocol, player)
    x, y = coordinates(value)
    x += 32
    y += 32
    player.set_location((x, y, - 2))
    if connection is player:
        message = ('%s ' + ('silently ' if silent else '') + 'teleported to '
            'location %s')
        message = message % (player.name, value.upper())
    else:
        message = ('%s ' + ('silently ' if silent else '') + 'teleported %s '
            'to location %s')
        message = message % (connection.name, player.name, value.upper())
    if silent:
        connection.protocol.irc_say('* ' + message)
    else:
        connection.protocol.send_chat(message, irc = True)    

def fly(connection):
    if connection not in connection.protocol.players:
        raise ValueError()
    player = connection
    player.fly = not player.fly
    message = 'now flying' if player.fly else 'no longer flying'
    connection.protocol.irc_say('* %s is %s' % (player.name, message))
    if connection is player:
        return "You're %s." % message
    else:
        player.send_chat("You're %s." % message)
        if connection in connection.protocol.players:
            return '%s is %s.' % (player.name, message)
add(fly)

@alias('godme')
@admin
def build(connection):
    if connection not in connection.protocol.players:
        raise ValueError()
    connection.god = not connection.god
    if connection.protocol.set_god_build:
        connection.god_build = connection.god
    else:
        connection.god_build = False
    if connection.god:
        message = '%s entered BUILD MODE!' % connection.name
    else:
        message = '%s has become a mere tourist.' % connection.name
    connection.protocol.send_chat(message, irc = True)	
add(build)

@admin
def invis(connection):
	if connection in connection.protocol.players:
		player = connection
	else:
		raise ValueError()
	player.invisible = not player.invisible
	player.filter_visibility_data = player.invisible
	player.god = player.invisible
	player.god_build = False
	player.killing = not player.invisible
	if player.invisible:
		player.send_chat("You're now invisible.")
		connection.protocol.irc_say('* %s became invisible' % player.name)
		position_data.set((0, 0, 0), player.player_id)
		kill_action.kill_type = WEAPON_KILL
		kill_action.player_id = kill_action.killer_id = player.player_id
		player.protocol.send_contained(position_data, sender = player)
		player.protocol.send_contained(kill_action, sender = player,
			save = True)
	else:
		player.send_chat("You return to visibility.")
		connection.protocol.irc_say('* %s became visible' % player.name)
		pos = player.team.get_random_location()
		x, y, z = pos
		create_player.player_id = player.player_id
		create_player.name = player.name
		create_player.x = x
		create_player.y = y
		create_player.z = z
		create_player.weapon = player.weapon
		create_player.team = player.team.id
		world_object = player.world_object
		position_data.set(world_object.position.get(), player.player_id)
		orientation_data.set(world_object.orientation.get(), player.player_id)
		input_data.up = world_object.up
		input_data.down = world_object.down
		input_data.left = world_object.left
		input_data.right = world_object.right
		input_data.player_id = player.player_id
		input_data.fire = world_object.fire
		input_data.jump = world_object.jump
		input_data.crouch = world_object.crouch
		input_data.aim = world_object.aim
		input_data.player_id = player.player_id
		set_tool.player_id = player.player_id
		set_tool.value = player.tool
		set_color.player_id = player.player_id
		set_color.value = make_color(*player.color)
		player.protocol.send_contained(create_player, sender = player,
			save = True)
		player.protocol.send_contained(position_data, sender = player)
		player.protocol.send_contained(orientation_data, sender = player)
		player.protocol.send_contained(set_tool, sender = player)
		player.protocol.send_contained(set_color, sender = player,
			save = True)
		player.protocol.send_contained(input_data, sender = player)
	if connection is player or connection not in connection.protocol.players:
		return
	if player.invisible:
		return '%s is now invisible' % player.name
	else:
		return '%s is now visible' % player.name
add(invis)

@admin
def team(connection):
	if connection in connection.protocol.players:
		player = connection
	else:
		raise ValueError()
	connection.respawn_time = connection.protocol.respawn_time
	connection.set_team(connection.team.other)
	connection.protocol.send_chat('%s has switched teams' % connection.name,
		irc = True)
add(team)

def apply_script(protocol, connection, config):
	return protocol, connection

