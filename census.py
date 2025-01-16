#Census by Kuma
#Inspired by server lists developed by many people (Moose)

from commands import add, admin, alias
from json import loads
from urllib2 import urlopen

NUMBER_OF_PLAYERS = "The current number of players on the server: {} ({})"
WORLD_POPULATION_IS = "server list population: {} players out of {} available slots (Servers: {})"
NOT_CONNECTED_TO_MASTER = "The server is isn't connected to the master server"
REFRESH_DONE = "Refreshed!"

version = '0.75' #change this to '0.76 for 0.76 server list'
url = 'http://services.buildandshoot.com/serverlist.php?version=075' if version == '0.75' else 'http://services.buildandshoot.com/serverlist.php?version=076'
server_list = loads(urlopen(url).read())

@alias('sp')
@admin
def serverpopulation(connection):
    protocol = connection.protocol
    current_players = len(protocol.players)
    if protocol.master:
        if connection in protocol.players:
            connection.send_chat(NUMBER_OF_PLAYERS.format(current_players, percent(current_players, number_of_players_playing(connection, server_list))))
        else:
            protocol.irc_say(NUMBER_OF_PLAYERS.format(current_players, percent(current_players, number_of_players_playing(connection, server_list))))
    else:
        connection.send_chat(NOT_CONNECTED_TO_MASTER) if connection in protocol.players else protocol.irc_say(NOT_CONNECTED_TO_MASTER)

@alias('wp')
def worldpopulation(connection):
    protocol = connection.protocol
    if connection in protocol.players:
        connection.send_chat(WORLD_POPULATION_IS.format(number_of_players_playing(connection, server_list, c = False), slots(connection, server_list), number_of_servers(connection, url)))
    else:
        protocol.irc_say(WORLD_POPULATION_IS.format(number_of_players_playing(connection, server_list, c = False),slots(connection, server_list),number_of_servers(connection, url)))
   

@admin
def refresh(connection): #It causes lag, don't use it often
    server_list = p_url(url)
    protocol = connection.protocol
    if connection in protocol.players:
        connection.send_chat(REFRESH_DONE)
    else:
        protocol.irc_say(REFRESH_DONE)

add(serverpopulation)
add(worldpopulation)
add(refresh)


#JSON functions-------------------------------
def number_of_players_playing(connection, url, c = True):
    numbers, total_players, protocol = [], 0, connection.protocol
    get_value(url, numbers, "players_current")
    for number in numbers:
        total_players += int(number)
    return total_players - len(protocol.players) if c else total_players

def slots(connection, url):
    numbers, total_slots, protocol = [], 0, connection.protocol
    get_value(url, numbers, "players_max")
    for number in numbers:
        total_slots += int(number)
    return total_slots

def number_of_servers(connection, url):
    return len(server_list)
    

def get_value(list, var, value = "name"):
    for line in list:
        dict_obj = line
        var.append(dict_obj.get(value))

#Returns a percentage
def percent(num1, num2):
    return str(100 * float(num1)/float(num2)) + "%"

#Prepares a string url to json
def p_url(url):
    return loads(urlopen(url).read())

def apply_script(protocol, connection, config):
    return protocol, connection
