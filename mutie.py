# secret mute script
# muted player can't know he is muted.
# mute without announcement
# thanks to idea from Mr.mutie

# script by yuyasato 20170315

from commands import add, admin, name, get_player, alias
from pyspades import contained as loaders
from pyspades.packet import load_client_packet
from pyspades.bytes import ByteReader, ByteWriter
from pyspades.common import *
from pyspades.constants import *

COMPLETE_MUTE= False  # don't show muted chat in the console window (True)  or  print the chat to console window (False)



@alias('mutie')
@name('secret_mute')
@admin
def secret_mute(connection, player):
	protocol = connection.protocol
	if player is not None:
		player = get_player(protocol, player)
	elif connection in protocol.players:
		player = connection
	else:
		raise ValueError()

	player.mutied = not player.mutied

	if not player.mutied:
		return '%s was unmuted'%player.name
	else:
		return '%s was muted. (secret muted)'%player.name
add(secret_mute)
  
@alias('compmutie')
@name('complete_mute')
@admin
def complete_mute(connection):
	global COMPLETE_MUTE
	COMPLETE_MUTE = not COMPLETE_MUTE
	if not COMPLETE_MUTE:
		return 'COMPLETE_MUTE disabled.'
	else:
		return 'COMPLETE_MUTE enabled.'
add(complete_mute)

def apply_script(protocol, connection, config):
  class MutekabeConnection(connection):
	mutied= False

	def loader_received(self, loader):
		if self.mutied:
			if self.player_id is not None:
				contained = load_client_packet(ByteReader(loader.data))
				if self.name:
					if contained.id == loaders.ChatMessage.id:
						if not self.name:
							return connection.loader_received(self, loader)
						value = contained.value
						if value.startswith('/'):
							return connection.loader_received(self, loader)
						else:
							global_message = contained.chat_type == CHAT_ALL
							if COMPLETE_MUTE:
								result = value
							else:
								print "<muted> --",
								result = self.on_chat(value, global_message)
							if result == False:
								return connection.loader_received(self, loader)
							elif result is not None:
								value = result
							contained.chat_type = [CHAT_TEAM, CHAT_ALL][int(global_message)]
							contained.value = value
							contained.player_id = self.player_id
							self.send_contained(contained)
							self.on_chat_sent(value, global_message)
					else:
						return connection.loader_received(self, loader)		
				else:
					return connection.loader_received(self, loader)		
			else:
				return connection.loader_received(self, loader)				
		else:
			return connection.loader_received(self, loader)	

	def on_command(self, command, parameters):
		if self.mutied:
			if command == "pm":
				if parameters:
					try:
						player = get_player(self.protocol, parameters.pop(0))
						self.send_chat("PM sent to %s"%player.name)
					except:
						self.send_chat("No such player")
						return False
				else:
					self.send_chat("Invalid number of arguments for pm")
					return False
				if not COMPLETE_MUTE:
					print "<muted>",self.name,"sent pm to",player.name,'"',
					if parameters:
						for word in parameters:
							print word,
						print '"'
					else:
						print "<- no message ->"
				return False

			if command == "admin":
				if not COMPLETE_MUTE:
					if parameters:
						print "<muted> -- <%s> /admin"%self.name,
						if parameters:
							for word in parameters:
								print word,
							print 
						else:
							print "<- no message ->"
				self.send_chat('Message sent to admins')
				return False
		return connection.on_command(self, command, parameters)
	
  return protocol, MutekabeConnection