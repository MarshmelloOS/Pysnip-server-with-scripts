from twisted.internet.reactor import callLater
from pyspades.constants import *

class SimpleBot:
    def __init__(self, *args, **kwargs):
        self.bot = None
        self.follow_player = None

    def on_map_change(self, map):
        self.bot = self.add_bot(self.blue_team)  # Change to green_team if you prefer

    def on_connect(self, name, protocol, ip, port, client_version):
        protocol.on_connect(name, protocol, ip, port, client_version)
        if self.bot and self.follow_player is None:
            self.follow_player = callLater(1, self.set_follow_target, self.bot, name)

    def set_follow_target(self, bot, player_name):
        player = self.get_player_by_name(player_name)
        if player:
            bot.follow_player(player)
    
class SimpleBotConnection:
    def on_map_change(self, map):
        protocol.on_map_change(self, map)
        self.follow_target = None

    def follow_player(self, player):
        self.follow_target = player

    def on_spawn(self, pos):
        if self.follow_target:
            self.send_chat('Following {}'.format(self.follow_target.name))
            self.set_position(self.follow_target.world_object.position.x, self.follow_target.world_object.position.y, self.follow_target.world_object.position.z)

# Usage: Replace your current apply_script function with the following
def apply_script(protocol, connection, config):
    class SimpleBotProtocol(SimpleBot, protocol):
        pass

    class SimpleBotConnectionClass(SimpleBotConnection, connection):
        pass

    return SimpleBotProtocol, SimpleBotConnectionClass
