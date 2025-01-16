#Change value of the damage (weapons)
#SCript by MegaStar 12/05/18

from pyspades.constants import *
from commands import add, admin

SMG_DAMAGE = [75,29,18] #default damage
RIFLE_DAMAGE = [100,49,33] #default damage
SHOTGUN_DAMAGE = [37,27,16] #default damage


@admin
def smgvalue(connection, head_value = "0" ,body_value = "0" ,arms_legs_value = "0"):
    if head_value == "0" and body_value == "0" and arms_legs_value == "0":
        connection.send_chat("You need to type /smgvalue <value head> <value body> <value arms/legs>")
        connection.send_chat("Current SMG damage: HEAD: {} BODY: {} ARMS/LEGS: {}".format(str(SMG_DAMAGE[0]),str(SMG_DAMAGE[1]),str(SMG_DAMAGE[2])))
    else:
        if head_value == "0":
            head_value = SMG_DAMAGE[0]
        if body_value == "0":
            body_value = SMG_DAMAGE[1]
        if arms_legs_value == "0":
            arms_legs_value = SMG_DAMAGE[2]            
        head = int(head_value)
        body = int(body_value)
        arms_legs = int(arms_legs_value)
    
        
        SMG_DAMAGE[0] = head
        SMG_DAMAGE[1] = body
        SMG_DAMAGE[2] = arms_legs        
        connection.send_chat("You changed the SMG damage by: HEAD: {} BODY: {} ARMS/LEGS: {}".format(str(SMG_DAMAGE[0]),str(SMG_DAMAGE[1]),str(SMG_DAMAGE[2])))

@admin
def riflevalue(connection, head_value = "0" ,body_value = "0",arms_legs_value = "0"):
    if head_value == "0" and body_value == "0" and arms_legs_value == "0":
        connection.send_chat("You need to type /riflevalue <value head> <value body> <value arms/legs>")
        connection.send_chat("Current RIFLE damage: HEAD: {} BODY: {} ARMS/LEGS: {}".format(str(RIFLE_DAMAGE[0]),str(RIFLE_DAMAGE[1]),str(RIFLE_DAMAGE[2])))
    else:
        if head_value == "0":
            head_value = RIFLE_DAMAGE[0]
        if body_value == "0":
            body_value = RIFLE_DAMAGE[1]
        if arms_legs_value == "0":
            arms_legs_value = RIFLE_DAMAGE[2]            
        head = int(head_value)
        body = int(body_value)
        arms_legs = int(arms_legs_value)
    
        
        RIFLE_DAMAGE[0] = head
        RIFLE_DAMAGE[1] = body
        RIFLE_DAMAGE[2] = arms_legs        
        connection.send_chat("You changed the RIFLE damage by: HEAD: {} BODY: {} ARMS/LEGS: {}".format(str(RIFLE_DAMAGE[0]),str(RIFLE_DAMAGE[1]),str(RIFLE_DAMAGE[2])))

@admin
def shotgunvalue(connection, head_value = "0" ,body_value = "0" ,arms_legs_value = "0"):
    if head_value == "0" and body_value == "0" and arms_legs_value == "0":
        connection.send_chat("You need to type /shotgunvalue <value head> <value body> <value arms/legs>")
        connection.send_chat("Current SHOTGUN damage: HEAD: {} BODY: {} ARMS/LEGS: {}".format(str(SHOTGUN_DAMAGE[0]),str(SHOTGUN_DAMAGE[1]),str(SHOTGUN_DAMAGE[2])))
    else:
        if head_value == "0":
            head_value = SHOTGUN_DAMAGE[0]
        if body_value == "0":
            body_value = SHOTGUN_DAMAGE[1]
        if arms_legs_value == "0":
            arms_legs_value = SHOTGUN_DAMAGE[2]            
        head = int(head_value)
        body = int(body_value)
        arms_legs = int(arms_legs_value)
    
        
        SHOTGUN_DAMAGE[0] = head
        SHOTGUN_DAMAGE[1] = body
        SHOTGUN_DAMAGE[2] = arms_legs         
        connection.send_chat("You changed the SHOTGUN damage by: HEAD: {} BODY: {} ARMS/LEGS: {}".format(str(SHOTGUN_DAMAGE[0]),str(SHOTGUN_DAMAGE[1]),str(SHOTGUN_DAMAGE[2])))
          
@admin
def debug(connection):
    global SMG_DAMAGE
    global RIFLE_DAMAGE
    global SHOTGUN_DAMAGE
        
    SMG_DAMAGE = [75,29,18] #default damage
    RIFLE_DAMAGE = [100,49,33] #default damage
    SHOTGUN_DAMAGE = [37,27,16] #default damage
    connection.send_chat("The damage of all the weapons have just been put in default")

    

    
add(smgvalue)
add(riflevalue)
add(shotgunvalue)
add(debug)


def apply_script(protocol,connection,config):
    class TestConnection(connection):

        def on_hit(self, hit_amount, hit_player, type, grenade):
            if type in (WEAPON_KILL,HEADSHOT_KILL):
                if hit_amount == 100:
                    return RIFLE_DAMAGE[0]
                elif hit_amount == 49:
                    return RIFLE_DAMAGE[1]
                elif hit_amount == 33:
                    return RIFLE_DAMAGE[2]
                elif hit_amount == 75:
                    return SMG_DAMAGE[0]
                elif hit_amount == 29:
                    return SMG_DAMAGE[1]
                elif hit_amount == 18:
                    return SMG_DAMAGE[2]
                elif hit_amount == 37:
                    return SHOTGUN_DAMAGE[0]
                elif hit_amount == 27:
                    return SHOTGUN_DAMAGE[1]
                elif hit_amount == 16:
                    return SHOTGUN_DAMAGE[2]
            return connection.on_hit(self, hit_amount, hit_player, type, grenade)

    return protocol, TestConnection
        







                
