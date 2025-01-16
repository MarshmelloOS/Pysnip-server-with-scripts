#Kick All script by Kuma
#Version 1.0

from commands import add, admin, alias

@admin
def kickall(connection):
    protocol = connection.protocol
    players_to_be_kicked = []
    for player in protocol.players.values():
        if not player.admin:
            players_to_be_kicked.append(player) #I need to do this as changing the size of the array between the execution = errors
    for player in players_to_be_kicked:
        player.kick(silent = True)
    protocol.send_chat("All players were kicked by {}".format(connection.name))

add(kickall)

def apply_script(protocol, connection, config):                    
    return protocol, connection
