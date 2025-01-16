#----------------SCRAMBLE GAMEMODE BY KUMA----------------
#In this gamemode, players start with no ammo and very critical health
#When they kill a enemy player,
#They get 5 healh and 1 bullet.
#Version 2
#I recommend turning fall damage on and setting melee damage to 10
#---------------------------------------------------------


from pyspades.server import weapon_reload
from commands import add, name, alias
from pyspades.constants import *

RIFLE_ONLY = "You can only use the rifle!"
NO_CP_HEAL = "Your team's cp/tent is out of munitions."

@name('saveammo')
@alias('sa')
def save_ammo(connection):
    if connection in connection.protocol.players and connection.weapon_object.current_ammo > 0:
        connection.saved_ammo += connection.weapon_object.current_ammo
        connection.weapon_object.current_ammo = 0
        weapon_reload.player_id = connection.player_id
        weapon_reload.clip_ammo = connection.weapon_object.current_ammo
        connection.protocol.send_contained(weapon_reload)
        return "All bullets were saved."
    else:
        return "You don't have enough bullets."

@name('ammosaved')
@alias('as')
def ammo_saved(connection):
    return "You have {} bullets saved in total".format(connection.saved_ammo)

@name('takeammo')
@alias('ta')
def take_ammo(connection):
    if connection.saved_ammo > 0:
        connection.weapon_object.current_ammo += connection.saved_ammo
        connection.saved_ammo = 0
        weapon_reload.player_id = connection.player_id
        weapon_reload.clip_ammo = connection.weapon_object.current_ammo
        connection.protocol.send_contained(weapon_reload)
        return "You took all the saved bullets"
    else:
        return "You don't have any saved bullets."
    
add(save_ammo)
add(ammo_saved)
add(take_ammo)

def apply_script(protocol, connection, config):

    class scrambleConnection(connection):
        saved_ammo = 0
        def spawn(self):
            self.set_weapon(RIFLE_WEAPON)
            return connection.spawn(self)
        
        def on_spawn(self, pos):
            self.set_hp(100 - (100-self.protocol.starting_hp), type = FALL_KILL)
            weapon_reload.player_id = self.player_id
            weapon_reload.clip_ammo = 0
            weapon_reload.reserve_ammo = 0
            self.weapon_object.current_ammo = 0
            self.grenades = 0
            
            self.weapon_object.clip_ammo = 0
            self.weapon_object.reserve_ammo = 0
            self.protocol.send_contained(weapon_reload)
            return connection.on_spawn(self, pos)

        #This disables weapon switching
        def on_weapon_set(self, weapon):
            self.send_chat(RIFLE_ONLY)
            return False

        def on_kill(self, killer, type, grenade):            
            if type == MELEE_KILL:
                killer.set_hp(killer.hp + self.protocol.add_hp_on_hit, type = FALL_KILL)
                killer.add_ammo(1)
                #hit_player.kill(by = self, type = MELEE_KILL)
            return connection.on_kill(self, killer, type, grenade)

        #This disables cp/tent healing
        def on_refill(self):
            self.send_chat(NO_CP_HEAL)
            return False

        def add_ammo(self, clip):
            self.weapon_object.current_ammo += clip
            weapon_reload.player_id = self.player_id
            weapon_reload.clip_ammo = self.weapon_object.current_ammo            
            self.protocol.send_contained(weapon_reload)

    class scrambleProtocol(protocol):
        game_mode = CTF_MODE
        starting_hp = config.get("start_hp", 5)
        add_hp_on_hit = config.get("add_hp_on_hit", 5)
        
    return scrambleProtocol, scrambleConnection
