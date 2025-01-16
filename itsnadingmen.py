from pyspades.server import *              # wow i realy beat myself
from commands import name, alias, admin    # with using imports
import commands                            # dang, that means i am
from twisted.internet import reactor       # a pussy who can not  
from pyspades.constants import *           # create anything
from pyspades.common import Vertex3        # independandly at all

@alias('twn')
@admin
@name('togglewetnades')                   # dont think bad of me, i just wanted to call them wet nades for no apparent reason
def toggle_wet_nades(self):
    if self.protocol.wet_potatoes == True:
        self.protocol.wet_potatoes = False
        self.protocol.send_chat('A rude admin made grenades harmless when they explode in water!')      # that would be just cruel of him
        return "Realism increased, grenades wont hurt anybody when they explode inside the water."      # i already regret writing this commnd
    else:
        self.protocol.wet_potatoes = True
        self.protocol.send_chat('A god made your grenades harmful when they explode in water!')         # that seriously takes some divine powers
        return "Are you stupid? Grenades are not supposed to kill when they explode inside the water."  # since the whole thing is so absurd
commands.add(toggle_wet_nades)

def check_potato_height(potato, man):
    if potato.position > 62 and man.protocol.wet_potatoes: 
        for drunkard in man.protocol.players.values():                                                                                                         # cant tell how many times i needed this line
            if (drunkard.team != man.team and drunkard.team != 2 and drunkard.hp != None)  or  (drunkard == man and drunkard.hp != None):                      # eleminating spectators and corpses to prevent errors
                potato.position.set(potato.position.x, potato.position.y, potato.position.z - 1)                                                               # that alone should be enough but NO pyspades does not work with common sense
                if potato.get_damage(drunkard.world_object.position) >= 1: drunkard.hit(potato.get_damage(drunkard.world_object.position), man, GRENADE_KILL)  # monster lines ftw


def apply_script(protocol, connection, config):

    class nadingprotocol(protocol):

        wet_potatoes = True                                                              # i can name my variables whatever i want!

    class nadingconnection(connection):
        
        potatotime = None                                                                # not much to say here

        def on_grenade(self, time_left):
            self.potatotime = time_left-0.1                                                  # i like hoe everything is linked here :3
            return connection.on_grenade(self, time_left)                                               

        def on_grenade_thrown(self, grenade):
            reactor.callLater(self.potatotime, check_potato_height, grenade, self) 
            return connection.on_grenade_thrown(self, grenade)


    return nadingprotocol, nadingconnection