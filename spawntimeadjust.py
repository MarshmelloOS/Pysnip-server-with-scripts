from pyspades.server import *
from commands import *
import commands

@alias('st')
@admin
@name('spawntime')
def set_spawntime(self, target, time):
    if target == None or time == None: return 
    if target == 'blue' or target == 'b': 
        self.protocol.blue_spawn_time = int(time)
        return "Blue's respawn time set to %i seconds" % (self.protocol.blue_spawn_time)
    elif target == 'green' or target == 'g':
        self.protocol.green_spawn_time = int(time)
        return "Green's respawn time set to %i seconds" % (self.protocol.green_spawn_time)
    else: # unsupported for now
        # player = get_player(self.protocol, target)
        # player.respawn_time = int(time)
        # return "%s's respawm time set to %i seconds" % (player.name, player.respawn_time)
        return 'Enter some valid values, noob!'
commands.add(set_spawntime)


def apply_script(protocol, connection, config):

    class adjustspawnprotocol(protocol):

        blue_spawn_time = 10
        green_spawn_time = 10
    
    class adjustspawnconnection(connection):

        def get_respawn_time(self):
            if self.team == self.protocol.blue_team: spawn_time = self.protocol.blue_spawn_time
            elif self.team == self.protocol.green_team: spawn_time  = self.protocol.green_spawn_time
            else: 
                if self.admin: spawn_time = 0
                else: spawn_time = 15
            return spawn_time
        
    return adjustspawnprotocol, adjustspawnconnection
