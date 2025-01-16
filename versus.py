#script by MegaStar 10/06/18
#versus (1 vs 1)
#commands:
# /versUs <player> <amounts of kills>
# /accept >player>
# /deny <playet> optional


from commands import add, get_player
from pyspades.constants import *
from twisted.internet.reactor import callLater
from twisted.internet.task import LoopingCall

DEFAULT_VERSUS_KILLS = 20

def versus(connection,player,k_amount = None):
    if not connection.protocol.start_game:
        global DEFAULT_VERSUS_KILLS
        if k_amount == None:
            k_amount = DEFAULT_VERSUS_KILLS
        k_amount = int(k_amount)
        DEFAULT_VERSUS_KILLS = k_amount
        player = get_player(connection.protocol, player)
        if player == connection:
            connection.send_chat("You must choose a different player.")
            return
        player.send_chat("Type /accept #%s to accept the versus!" % connection.player_id)
        player.send_chat("1 vs 1 to %s kills." % DEFAULT_VERSUS_KILLS)
        player.send_chat("The player %s has challenged you to a versus:" % connection.name)
        connection.send_chat("The request for the versus has been sent correctly.")
        player.versus = True
    else:
        connection.send_chat("Currently a versus is already in progress, wait for it to end!")

add(versus)

def accept(connection,player):
        if connection.versus == True:
            player = get_player(connection.protocol, player)
            if player == connection:
                connection.send_chat("You must choose a different player.")
                return
            player.send_chat("The player %s has accepted your challenge!" % connection.name)
            connection.protocol.start_game = True
            connection.protocol.players_versus = [connection,player]
            connection.protocol.countdown_round()
            return
        connection.send_chat("Currently you do not have any request for a versus.")
add(accept)



def apply_script(protocol,connection,config):
    class VersusConnection(connection):
        versus = False
        my_kills = 0


        def on_block_build_attempt(self,x,y,z):
            if not self.protocol.start_game:
                return False
            return connection.on_block_build_attempt(self,x,y,z)


        def on_block_destroy(self,x,y,z, mode):
            if not self.protocol.start_game:
                return False
            return connection.on_block_destroy(self,x,y,z, mode)


        def on_line_build_attempt(self,points):
            if not self.protocol.start_game:
                return False
            return connection.on_line_build_attempt(self,points)


        def on_hit(self,damage,victim,icon,grenade):
            if not self.protocol.start_game:
                return False
            return connection.on_hit(self,damage,victim,icon,grenade)

        def on_kill(self, killer, type, grenade):
            if self.protocol.start_game:
                if killer is not None and self.team is not killer.team and self != killer:
                    killer.my_kills += 1
                    self.protocol.check_winner(killer)
            return connection.on_kill(self,killer,type,grenade)


        def on_disconnect(self):
            if self.protocol.players_versus:
                if self in self.protocol.players_versus:
                    self.protocol.send_chat("the player %s has retired while the versus did not finish." % self.name)
                    self.protocol.send_chat("The versus has not concluded, for the following reason:")
                    self.protocol.restart_game()
            return connection.on_disconnect(self)


    class VersusProtocol(protocol):
        game_mode = CTF_MODE
        start_game = False
        players_versus = None


        def remove_other_players(self):
            for player in self.players.values():
                if player not in self.players_versus:
                    player.set_team(self.spectator_team)
            self.green_team.locked = True
            self.blue_team.locked = True
            self.players_versus[0].set_team(self.green_team)
            self.players_versus[0].spawn()
            self.players_versus[1].set_team(self.blue_team)
            self.players_versus[1].spawn()


        def countdown_round(self):
            self.remove_other_players()
            count = 0
            for remain_count in [5,4,3,2,1]:
                count += 1
                msg = "The round will begin in {}..".format(str(remain_count))
                callLater(count,self.send_chat,msg)
            callLater(6,self.start_round)


        def start_round(self):
            self.send_chat("The versus between %s and %s has started!" % (self.players_versus[0].name,self.players_versus[1].name))
            self.send_chat("The player who reaches %s kills is the winner!" % DEFAULT_VERSUS_KILLS)
            self.notice = LoopingCall(self.counting_of_kills)
            self.notice.start(30)


        def counting_of_kills(self):
                self.send_chat("(Player %s: kills:%s) --- (Player %s: kills: %s)" % (self.players_versus[0].name,self.players_versus[0].my_kills,self.players_versus[1].name,self.players_versus[1].my_kills))
                self.send_chat("Goal of versus: %s kills!" % DEFAULT_VERSUS_KILLS)

        def check_winner(self,player):
            if player.my_kills >= DEFAULT_VERSUS_KILLS:
                self.send_chat("###")
                self.send_chat("######")
                self.send_chat("#########")
                self.send_chat("%s is the winner!" % player.name)
                self.restart_game()


        def restart_game(self):
                global DEFAULT_VERSUS_KILLS
                DEFAULT_VERSUS_KILLS = 20
                self.players_versus[0].my_kills = 0
                self.players_versus[0].versus = False
                self.players_versus[1].my_kills = 0
                self.players_versus[1].versus = False
                self.green_team.locked = False
                self.blue_team.locked = False
                self.start_game = False
                self.players_versus = None
                self.notice.stop()


        def on_map_change(self, map):
            if self.start_game:
                self.restart_game()
            protocol.on_map_change(self, map)


    return VersusProtocol,VersusConnection
