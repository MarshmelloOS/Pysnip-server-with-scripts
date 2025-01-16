# fight.py

from commands import add, admin
from pyspades.common import coordinates
import random

@admin
def fight(connection, area_code=None):
    protocol = connection.protocol
    
    if area_code is None:
        protocol.fighting_players.discard(connection)
        protocol.send_chat('Fight mode canceled', irc=True)
    else:
        if not protocol.areas:
            protocol.send_chat('No fight areas defined on this map', irc=True)
            return
        
        area_code = area_code.upper()
        
        if area_code not in protocol.areas:
            protocol.send_chat('Invalid fight area code: {}'.format(area_code), irc=True)
            return
        
        protocol.fighting_players.add(connection)
        spawn_point = random.choice(protocol.areas[area_code])
        connection.set_location(*spawn_point)
        connection.send_chat('You have entered fight mode!')
        protocol.send_chat('{} has entered fight mode!'.format(connection.name), irc=True)

add(fight)

def apply_script(protocol, connection, config):
    class FightConnection(connection):
        def on_disconnect(self):
            self.protocol.fighting_players.discard(self)
            connection.on_disconnect(self)
    
    class FightProtocol(protocol):
        fighting_players = set()
        areas = {}
        
        def on_map_change(self, map):
            self.areas = self.load_fight_areas(map)
            protocol.on_map_change(self, map)
        
        def load_fight_areas(self, map):
            # Modify this function to load fight areas from the map
            # For example, parse a specific map file format or use predefined areas
            # For now, it's an example with hardcoded areas
            return {'A1': [(10, 10, 10), (20, 20, 20)],
                    'G2': [(30, 30, 30), (40, 40, 40)]}
        
        def is_in_fight_mode(self, connection):
            return connection in self.fighting_players
    
    return FightProtocol, FightConnection
