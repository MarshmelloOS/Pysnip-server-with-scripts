"""
Sends messages in chat (messages can be edited to your liking)

Author: Marshmello
Maintainer: mat^2
"""

import commands
from pyspades.constants import *

@commands.alias('f1')
def fact1(connection):
    if connection.medkits and connection.hp < 100:
        connection.set_hp(connection.hp + connection.protocol.heal_amount,
            type = FALL_KILL)
        connection.medkits -= 1
        connection.send_chat('fact_number_1')
    else:
        connection.send_chat("Some turtles can breathe through their butts")
commands.add(fact1)

def apply_script(protocol, connection, config):
    default_medkits = config.get('fact1', 0)
    medkit_heal_amount = config.get('medkit_heal_amount', 0)

@commands.alias('f2')
def fact2(connection):
    if connection.medkits and connection.hp < 100:
        connection.set_hp(connection.hp + connection.protocol.heal_amount,
            type = FALL_KILL)
        connection.medkits -= 1
        connection.send_chat('fact_number_2')
    else:
        connection.send_chat("Cats have a sixth sense: they can sense earthquakes before they happen")
commands.add(fact2)

def apply_script(protocol, connection, config):
    default_medkits = config.get('fact2', 0)
    medkit_heal_amount = config.get('medkit_heal_amount', 0)

@commands.alias('f3')
def fact3(connection):
    if connection.medkits and connection.hp < 100:
        connection.set_hp(connection.hp + connection.protocol.heal_amount,
            type = FALL_KILL)
        connection.medkits -= 1
        connection.send_chat('fact_number_3')
    else:
        connection.send_chat("Penguins propose to their lifemates with pebbles")
commands.add(fact3)

def apply_script(protocol, connection, config):
    default_medkits = config.get('fact3', 0)
    medkit_heal_amount = config.get('medkit_heal_amount', 0)

@commands.alias('f4')
def fact4(connection):
    if connection.medkits and connection.hp < 100:
        connection.set_hp(connection.hp + connection.protocol.heal_amount,
            type = FALL_KILL)
        connection.medkits -= 1
        connection.send_chat('fact_number_4')
    else:
        connection.send_chat("Some species of fungi can infect insects turning them into zombies before bursting out of their bodies")
commands.add(fact4)

def apply_script(protocol, connection, config):
    default_medkits = config.get('fact4', 0)
    medkit_heal_amount = config.get('medkit_heal_amount', 0)

@commands.alias('f5')
def fact5(connection):
    if connection.medkits and connection.hp < 100:
        connection.set_hp(connection.hp + connection.protocol.heal_amount,
            type = FALL_KILL)
        connection.medkits -= 1
        connection.send_chat('fact_number_5')
    else:
        connection.send_chat("Holly shit the script works! If NASA not calling me, I am coming")
commands.add(fact5)

def apply_script(protocol, connection, config):
    default_medkits = config.get('fact5', 0)
    medkit_heal_amount = config.get('medkit_heal_amount', 0)

@commands.alias('dis')
def discord(connection):
    if connection.medkits and connection.hp < 100:
        connection.set_hp(connection.hp + connection.protocol.heal_amount,
            type = FALL_KILL)
        connection.medkits -= 1
        connection.send_chat('discord')
    else:
        connection.send_chat("https://discord.gg/qEz5qdK9NC")
commands.add(discord)

def apply_script(protocol, connection, config):
    default_medkits = config.get('discord', 0)  
    medkit_heal_amount = config.get('medkit_heal_amount', 0)
    
    class MedkitConnection(connection):
        medkits = 0
        def on_spawn(self, pos):
            self.medkits = default_medkits
            self.send_chat('You have %s medkit!' % self.medkits)
            return connection.on_spawn(self, pos)
    
    class MedkitProtocol(protocol):
        heal_amount = medkit_heal_amount

    return MedkitProtocol, MedkitConnection
