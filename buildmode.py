"""
Redefines god to build mode, and only allows changing other's build status if admin. Only blue team can be build mode
unless build mode set with /fg
"""

import commands


@commands.name('bm')
@commands.admin
def god(connection, name=None):
    if name is not None:
        if not connection.admin:
            return 'No administrator rights!'
        player = commands.get_player(connection.protocol, name)
    else:
        player = connection
    if player not in player.protocol.players:
        raise ValueError()
    player.infinite_blocks = False
    player.god = not player.god
    if player.god:
        message = '%s entered BUILD MODE!'
        player.set_team(player.protocol.blue_team)
        player.respawn_time = 0
    else:
        message = '%s returned to being a mere sightseer'
        player.set_team(player.protocol.green_team)
        player.respawn_time = player.protocol.respawn_time
    player.protocol.send_chat(message % connection.name, irc=True)
commands.add(god)


def setlocation(connection, x, y, z):
    connection.set_location((int(x), int(y), int(z)))
commands.add(setlocation)


@commands.admin
@commands.name('fg')
def forcegod(connection):
    if connection not in connection.protocol.players:
        raise ValueError()
    connection.infinite_blocks = False
    connection.god = not connection.god
    if connection.god:
        message = 'You entered build mode'
    else:
        message = 'You exited build mode'
    connection.send_chat(message)
commands.add(forcegod)


def apply_script(protocol, connection, config):

    class BuildModeConnection(connection):
        def on_hit(self, hit_amount, player, type, grenade):
            if player.god:
                self.send_chat("You can't hurt %s! That player is in *Build Mode*" % player.name)
                return False
            if self.god:
                self.send_chat("You can't hurt people while you are in *Build Mode*")
                return False
            return connection.on_hit(self, hit_amount, player, type, grenade)

        def on_team_join(self, team):
            connection.on_team_join(self, team)
            if self.team == self.protocol.green_team:
                if self.god:
                    self.god = False
                    message = '%s returned to being a mere sightseer'
                    self.protocol.send_chat(message % connection.name)

    return protocol, BuildModeConnection
