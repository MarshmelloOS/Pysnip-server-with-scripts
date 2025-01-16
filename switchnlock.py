#Switch n' Lock by Kuma
#Switches a complete team and locks it
#Also allows switching of multiple people at the same time

from commands import add, admin, alias, get_team, get_player

@alias('sl')
@admin
def switchlock(connection):
    protocol = connection.protocol
    switchandlock(connection)

@alias('ms')
@admin
def multiswitch(connection, *args):
    protocol = connection.protocol
    players = []
    if len(args) >= 2:
        teamname = args[0]
        team_ = get_team(connection, teamname)
        for player in args[1:]:
            players.append(get_player(protocol, player))
        for player in players:
            if player.team != team_:
                player.team = team_
                player.respawn()
        connection.send_chat('It will take some time to effect (respawn time)')
    else:
        raise ValueError()       

add(switchlock)
add(multiswitch)


def switchandlock(connection):
    protocol = connection.protocol
    players = protocol.players
    blue = get_team(connection, 'blue')
    green = get_team(connection, 'green')
    green.locked = True
    blue.locked = True
    for player in players.values():
        player.team = get_team(connection, 'spectator')
        player.kill()

def apply_script(protocol, connection, config):
    return protocol, connection
