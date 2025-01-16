#script by MegaStar 5/05/18

from pyspades.constants import *
from commands import add

market_things = ("medkit","helmet","shield","refill")
cost_amount = ((3,100),4,(12,200),7)

def get(self,mobject = None):
    if mobject == None:
        self.send_chat("To choose: type /get [object]. Example: /get medkit")
        self.send_chat("#) shield (cost: 12 Dollars) -- #) refill (cost 7 Dollars)")
        self.send_chat("#) medkit (cost: 3 Dollars) -- #) helmet (cost 4 Dollars)")
    if mobject is not None:
        myobject = mobject.lower()
        if myobject in market_things:
            if myobject == "medkit":
                if self.coins >= cost_amount[0][0]:
                    self.medkit += 1
                    self.coins -= cost_amount[0][0]
                    self.send_chat("You bought a medkit, type /m to use it.")
                else:
                    self.send_chat("You need %s dollars more to buy the medkit." % (cost_amount[0][0] - self.coins))
            elif myobject == "helmet":
                if self.coins >= cost_amount[1]:
                    self.helmet += 1
                    self.coins -= cost_amount[1]
                    self.send_chat("You bought a helmet.")
                else:
                    self.send_chat("You need %s dollars more to buy the helmet." % (cost_amount[1] - self.coins))
            elif myobject == "shield":
                if self.coins >= cost_amount[2][0] and self.shield_protect < 401:
                    self.shield_protect += cost_amount[2][1]
                    self.coins -= cost_amount[2][0]
                    self.send_chat("You bought a bulletproof vest but you're still vulnerable in the head.")
                else:
                    self.send_chat("You do not have enough dollars or your shield is at 100%.")
            elif myobject == "refill":
                if self.coins >= cost_amount[3]:
                    self.refill()
                    self.send_chat("Your hp, ammo, grenades and blocks have been refill at 100%.")
                else:
                    self.send_chat("You need %s dollars more to buy the refill." % (cost_amount[3] - self.coins))
        

        else:
            self.send_chat("To choose: type /get [object]. Example: /get medkit")
            self.send_chat("#) shield (cost: 12 Dollars) -- #) refill (cost 7 Dollars)")
            self.send_chat("#) medkit (cost: 3 Dollars) -- #) helmet (cost 4 Dollars)")
            self.send_chat("%s was not found on the market." %mobject)
add(get)

def m(self):
    if self.hp < 100 and self.medkit > 0:
        self.set_hp(cost_amount[0][1],type = FALL_KILL)
    elif self.hp == 100:
        self.send_chat("Your hp is full.")
    elif self.medkit == 0:
        self.send_chat("You do not have any medkit.")
add(m)

def mystuff(self):
    self.send_chat("helmet's: %s" % self.helmet)
    self.send_chat("shield: (%s)" % self.shield_protect)
    self.send_chat("medkit's: %s" % self.medkit)
    self.send_chat("You have: %s dollars." % self.coins)
add(mystuff)                   

def apply_script(protocol, connection, config):
    class BuymarketConnection(connection):
        helmet = 0
        shield_protect = 0
        medkit = 0
        coins = 0

        def on_kill(self, killer, type, grenade):
            if killer is not None and self.team is not killer.team and self != killer:
                killer.coins += 1
                killer.send_chat("You now have %s dollars." % killer.coins)
            return connection.on_kill(self, killer, type, grenade)
            
        def on_hit(self,hit_amount,hit_player,type,grenade):
            if hit_player.helmet >= 1 and type == HEADSHOT_KILL:
                hit_player.helmet -= 1
                hit_player.send_chat("Your helmet has been broken, now you have %s helmet's"% hit_player.helmet)
                return False
            elif hit_player.shield_protect >= 1 and type == WEAPON_KILL:
                if self.weapon == SMG_WEAPON:
                    damage = hit_amount / 3
                elif self.weapon == RIFLE_WEAPON:
                    damage = hit_amount / 2
                elif self.weapon == SHOTGUN_WEAPON:
                    damage = hit_amount / 4
                hit_player.shield_protect -= damage
                if hit_player.shield_protect <= 0:
                    hit_player.shield_protect = 0
                    hit_player.send_chat("Your shield has been broken!")
                return damage
            else:
                return hit_amount

            return connection.on_hit(self, hit_amount, hit_player, type, grenade)

        def on_spawn(self,pos):
            self.send_chat("You have %s dollars, type /get to see the market." % self.coins)
            self.send_chat("Type /mystuff to see everything you bought.")
            if self.medkit > 0:
                self.send_chat("You have %s medkit's, type /m to use it."%self.medkit)
            return connection.on_spawn(self,pos)
                                               
    return protocol, BuymarketConnection
