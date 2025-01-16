# nya
from commands import name, get_player, add, admin, alias, add
from pyspades.server import *


@alias('nick')  
def ingamenamechange(self, *args):
    if self.hp == None and self.team.id != -1: return 'You canot change your name while being dead.'
    dat_name = ''
    old_name = self.name
    for kitten in range(len(args)):
        if kitten == len(args)-1: dat_name += str(args[kitten])
        else: dat_name += (str(args[kitten]) + ' ')
    if len(dat_name) > 15 : return 'Your name must contain less than 15 characters!'
    if len(dat_name) <= 0: return 'Your name must consist of at least one character!'
    self.name = dat_name
    self.world_object.name = dat_name
    self.printable_name = dat_name
    player_left.player_id = self.player_id
    self.protocol.send_contained(player_left)
    
    del self.protocol.players[self.player_id]

    create_player.player_id = self.player_id
    create_player.weapon = self.weapon
    create_player.team = self.team.id
    create_player.name = dat_name
    self.protocol.send_contained(create_player)

    self.protocol.players[(self.name,self.player_id)]=self
    
    self.kill()
    self.protocol.irc_say(old_name + " has been renamed to " + dat_name)
    return old_name + " has been renamed to " + dat_name
add(ingamenamechange)


def apply_script(protocol, connection, config):
    return protocol, connection