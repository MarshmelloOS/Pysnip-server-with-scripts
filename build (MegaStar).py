#script by MegaStar
#updated
 

from pyspades.constants import *
from commands import add, get_player, admin
from pyspades.server import grenade_packet
from pyspades.common import Vertex3
from pyspades.world import Grenade
from pyspades.server import block_action, set_color
from pyspades.common import make_color
import json

RANGE_CLAIM = 15 #size of the sector, remember that it is double the size, therefore it would be 20x20 blocks per claim.

#-------------------------------------------------------------#
#Quick functions to build and remove a block

def fastblock(connection, (x, y, z), color): #to place a block
	set_color.value = make_color(*color)
	set_color.player_id = 32
	connection.protocol.send_contained(set_color)
	block_action.player_id = 32
	block_action.value=BUILD_BLOCK
	block_action.x = x
	block_action.y = y
	block_action.z = z
	connection.protocol.send_contained(block_action)
	connection.protocol.map.set_point(x, y, z, color)

def removeblock(connection, (x, y, z)): #to remove a block
	block_action.player_id = connection.player_id
	block_action.value = DESTROY_BLOCK
	block_action.x = x
	block_action.y = y
	block_action.z = z
	connection.protocol.send_contained(block_action)
	connection.protocol.map.remove_point(x, y, z)

#-------------------------------------------------------------#

#-------------------------------------------------------------#
#Open, edit, check and save data

def open_data():
    with open("users.json", "r") as users:
        datos = json.load(users)
        return datos

def save_data(data):
    with open("users.json","w") as save_data:
        json.dump(data, save_data)

def edit_claims(connection, key, user, type):
    for claim_users in connection.protocol.claim_coords:
        if claim_users[0] == key:
            if type == "remove":
                claim_users[3].remove(user)
                return
            elif type == "add":
                claim_users[3].append(user)
                return
            elif type == "total":
                connection.protocol.claim_coords.remove(claim_users)

#-------------------------------------------------------------#


def buildregister(connection, username, password):
    datos = open_data()
    for key, value in datos.items():
        if username == key:
            return connection.send_chat("This username is already being used.")
        elif connection.address[0] == value["ip"]:
            return connection.send_chat("You currently already registered.")

    datos[username] = {"ip": connection.address[0], "password": password, "coordx": False, "coordy": False, "shared": []}
    save_data(datos)
    return connection.send_chat("%s you just registered succesfully, to login your account type /buildlogin <username> <password>" % connection.name)


def buildlogin(connection, username, password):
    if not connection.login:
        datos = open_data()
        for key, value in datos.items():
            if username == key:
                if password == value["password"]:
                    connection.login = True
                    connection.username = username
                    return connection.send_chat("You just logged in as %s." % username)
                else:
                    return connection.send_chat("La contrasenia es incorrecta.")
        return connection.send_chat("The account with the username %s does not exist." % username)
    return connection.send_chat("You are currently logged in as %s" % connection.username)


def buildlogout(connection):
    if connection.login:
        connection.login = False
        connection.username = None
        return connection.send_chat("you just logout succesfully.")
    return connection.send_chat("You are not currently logged in.")


def claim(connection):
    if connection.login:
        datos = open_data()
        posx = datos[connection.username]["coordx"]
        posy = datos[connection.username]["coordy"]
        if posx != False and posy != False:
            return connection.send_chat("You already claimed a sector.")
        connection.claimed = True
        return connection.send_chat("Claim activated, to choose your sector just destroy a block, make sure you choose a good place.")
    return connection.send_chat("You need to login before you can claim a sector.")


@admin
def removeclaim(connection, username):
    datos = open_data()
    for key in datos.keys():
        if username == key:
            if datos[username]["coordx"] != False and datos[username]["coordy"] != False:
                datos[username]["coordx"] = False
                datos[username]["coordy"] = False
                save_data(datos)
                edit_claims(connection, username, username, "total")
                print(connection.protocol.claim_coords)
                return connection.send_chat("The user %s has just been removed correctly." % username)
            return connection.send_chat("The user %s currently does not have a sector." % username)
    return connection.send_chat("%s does not exist or is not registered." % username)


def tpsector(connection):
    if connection.login:
        datos = open_data()
        for key in datos.keys():
            if connection.username == key:
                pos_x = datos[connection.username]["coordx"]
                pos_y = datos[connection.username]["coordy"]
                if pos_x != False and pos_y != False:
                    position = [ [x,y] for x in range(pos_x, pos_x + (RANGE_CLAIM * 2)) for y in range(pos_y - (RANGE_CLAIM * 2), pos_y)]
                    connection.set_location_safe((position[(len(position)-1)/2 + RANGE_CLAIM][0], position[(len(position)-1)/2 + RANGE_CLAIM][1] , int(connection.get_location()[2])))
                    return
                return connection.send_chat("You currently does not have a sector.")
    return connection.send_chat("You need to login before teleport to your sector.")



def share(connection, username):
    if connection.login:
        if username == connection.username:
            return connection.send_chat("Please enter a valid user.")
        datos = open_data()
        users = datos[connection.username]["shared"]
        for key, value in datos.items():
            if username == key:
                if username in users:
                    return connection.send_chat("%s is already on your list of users that can build and destroy in your sector." % username)
                else:
                    users.append(username)
                    save_data(datos)
                    edit_claims(connection, connection.username, username, "add")
                    return connection.send_chat("%s now can build and destroy in your sector." % username)

        return connection.send_chat("The user %s does not exist or is not registered." % username)
    return connection.send_chat("You need to login before sharing your sector.")


def unshare(connection, username):
    if connection.login:
        datos = open_data()
        users = datos[connection.username]["shared"]
        if len(users) <= 0:
            return connection.send_chat("Currently there are no users on your list.")
        elif username == connection.username:
            return connection.send_chat("Please enter a valid user.")
        for key, value in datos.items():
            if username == key:
                if username in users:
                    users.remove(username)
                    save_data(datos)

                    edit_claims(connection, connection.username, username, "remove")
                    return connection.send_chat("%s can no longer build or destroy in your sector." % username)
                else:
                    return connection.send_chat("%s currently is not on your list of users that can build or destroy in your sector." % username)
        return connection.send_chat("%s does not exist or is not registered." % username)
    return connection.send_chat("You need to login before sharing your sector.")



add(claim)
add(buildlogin)
add(buildregister)
add(share)
add(unshare)
add(buildlogout)
add(removeclaim)
add(tpsector)

def apply_script(protocol,connection,config):

    class BuildConnection(connection):
        claimed = False
        login = False
        username = None

        #--------this checks if the blocks are in the range of other claims-------#
        def is_in_range(self, x, y):
            if len(self.protocol.claim_coords) > 0:
                for values in self.protocol.claim_coords:
                    pos_x = values[1]
                    pos_y = values[2]
                    for xx in range(pos_x, pos_x + (RANGE_CLAIM * 2)):
                        for yy in range(pos_y - (RANGE_CLAIM * 2), pos_y):
                            for new_x in range(x-RANGE_CLAIM,x+RANGE_CLAIM):
                                for new_y in range(y-RANGE_CLAIM,y+RANGE_CLAIM):
                                    if xx == new_x and yy == new_y:
                                        return True
            return False



        #--------build-------#
        def on_block_build_attempt(self,x,y,z):

            if not self.admin:
                if not self.login:
                    self.send_chat("Before building you need login with /buildlogin <username> <password>")
                    return False

                check = self.protocol.is_claimed(x, y, z)
                if check == False:
                    self.send_chat("You can only build in your sector, if you have not chosen a sector yet use the /claim command")
                    return False
                if self.login and self.username != check[0] and self.username not in check[3]:
                    self.send_chat("This place was claimed by %s" % check[0])
                    return False

            return connection.on_block_build_attempt(self,x,y,z)


        #--------line build-------#
        def on_line_build_attempt(self, points):
            if not self.admin:
                if not self.login:
                    self.send_chat("Before building you need login with /buildlogin <username> <password>")
                    return False

                for xyz in points:
                    check = self.protocol.is_claimed(xyz[0], xyz[1], xyz[2])
                    if check == False:
                        self.send_chat("You can only build in your sector, if you have not chosen a sector yet use the /claim command")
                        return False

                    if self.login and self.username != check[0] and self.username not in check[3]:
                        self.send_chat("This place was claimed by %s" % check[0])
                        return False

            return connection.on_line_build_attempt(self, points)


        #--------destroy-------#
        def on_block_destroy(self,x,y,z,mode):
            if not self.admin and not self.login:
                self.send_chat("Before destroying you need login with /buildlogin <username> <password>")
                return False


            if self.claimed:
        	if self.is_in_range(x, y):
        	    self.send_chat("This place is close to other sectors, choose another place.")
        	    return False

        	for new_x in range(x-RANGE_CLAIM,x+RANGE_CLAIM):
        	    for new_y in range(y-RANGE_CLAIM,y+RANGE_CLAIM):
        	        if new_x < 0 or new_x >= 512 or new_y < 0 or new_y >= 512 or z < 0 or z >= 62:
        	            return self.send_chat("You can not claim a sector here.")

        	        removeblock(self, (new_x, new_y, z))
        	        fastblock(self,(new_x, new_y, z),self.color)

        	self.send_chat("Your sector has just been saved!")
        	self.claimed = False
        	datos = open_data()
                datos[self.username]["coordx"] = x - RANGE_CLAIM
        	datos[self.username]["coordy"] = y + RANGE_CLAIM
        	save_data(datos)
        	self.protocol.claim_coords.append([self.username, x - RANGE_CLAIM, y + RANGE_CLAIM, []])
        	return False

            check = self.protocol.is_claimed(x, y, z)
            if not self.admin and check == False:
                self.send_chat("You can only build in your sector, if you have not chosen a sector yet use the /claim command")
                return False
       	    if not self.admin and self.login and self.username != check[0] and self.username not in check[3]:
                self.send_chat("This place was claimed by %s" % check[0])
                return False

            return connection.on_block_destroy(self,x,y,z,mode)


        #--------kill-------#
        def on_kill(self,killer,type,grenade):
            if killer:
                self.send_chat("This is a build server, kills are disabled.")
                return False
            else:
                return connection.on_kill(self, killer, type, grenade)


        #--------hit-------#
        def on_hit(self, hit_amount, hit_player, type, grenade):
            self.send_chat("This is a build server, damage are disabled.")
            return False


        #--------flag-------#
        def on_flag_take(self):
            return False

    class BuildProtocol(protocol):
        claim_coords = []
        game_mode = CTF_MODE

        #--------this initialize the available claims-------#
        def on_map_change(self, map):
            datos = open_data()
            if len(datos) > 0:
                for key, value in datos.items():
                    if value["coordx"] != False and value["coordx"] != False:
                        self.claim_coords.append( [key, value["coordx"], value["coordy"], value["shared"]])

            protocol.on_map_change(self, map)


        #--------this check if the blocks are inside the claim of some other user-------#
        def is_claimed(self, x, y, z):
            for pr in self.claim_coords:
                for xx in range(pr[1], pr[1] + (RANGE_CLAIM * 2)):
                    for yy in range(pr[2] - (RANGE_CLAIM * 2), pr[2]):
                        if x == xx and y == yy:
                            return pr
            return False

        #--------this put the spawn in the corner of the map-------#
        def on_base_spawn(self, x, y, z, base, entity_id):
            return(0,0,63)


        #--------this put the flag in the corner of the map-------#
        def on_flag_spawn(self, x, y, z, flag, entity_id):
            return(0,0,63)


    return BuildProtocol, BuildConnection
