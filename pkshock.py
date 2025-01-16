# Imports
from twisted.internet.reactor import callLater
from twisted.internet import reactor
from pyspades.server import fog_color
from pyspades.common import make_color
from pyspades.constants import *
from commands import add, admin, name, get_player, alias
from random import randint
from pyspades.server import *
from commands import admin, add, name, get_team, get_player,alias

R=(255,0,0)
B=(50,50,255)

def send_fog(player, color):
	fog_color.color = make_color(*color)
	player.send_contained(fog_color)


@admin
@name('pk')
def pk(connection, player = None):
	protocol = connection.protocol
	if player is not None:
		player = get_player(protocol, player)
	elif connection in protocol.players:
		player = connection
	else:
		raise ValueError()

	FC=R
	time=0
	for t in range(0,30):
		for FREQ in [12.0, 17.0]:
			for elapsed_time in range(0,int(FREQ*5)):	
				reactor.callLater(elapsed_time/FREQ+time, send_fog, player, FC)
				if FC==R:FC=B
				else:FC=R
			time+=5

	#send_fog(player, player.protocol.get_fog_color())
	message = 'Commencing seizure on  for  seconds.'
	return message
add(pk)

def apply_script(protocol, connection, config):
	return protocol, connection
