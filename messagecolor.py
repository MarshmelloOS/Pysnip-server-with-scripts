from pyspades.server import *
from twisted.internet import reactor

def check_count(self):
    self.msgcount = 0
    self.msgtimeset = False


def apply_script(protocol, connection, config):

    class msgcolorprotocol(protocol):
        col = None

    class msgcolorconnection(connection):
        msgcount = 0
        msgtimeset = False

        def on_chat(self, value, global_message):
            chat_message.player_id = self.player_id
            chat_message.value = value
            if global_message: 
                chat_message.chat_type = 1
                self.protocol.send_contained(chat_message)
            else: 
                chat_message.chat_type = 0
                for player in self.protocol.players.values():
                    if player.team == self.team: player.send_contained(chat_message)
            self.protocol.irc_say(self.name + ': ' + value)        
            print (self.name + ': ' + value) # str(datetime.now())[:20] + '>> ' + 
            self.msgcount +=1
            if self.msgcount > 10: self.kick('spaming faggot')
            if not self.msgtimeset: 
                reactor.callLater(60, check_count, self)
                self.msgtimeset = True
            return False

    return msgcolorprotocol, msgcolorconnection